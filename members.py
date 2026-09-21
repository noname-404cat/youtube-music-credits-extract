"""各メンバーのチャンネルの動画から、曲名・歌唱者・カバー/オリジナルを取る。

メンバーのチャンネルにはシクフォニ本体のような ◆ラベル も ▼本家様 もほぼ無いため、
タイトルとハッシュタグから取る。ネットワークには触らない。

  - 曲名: タイトルから。ショートはハッシュタグから（ショートは再生リストに入っていないものがある）。
  - 歌唱者: タイトルに出るメンバー名。二人以上で歌う動画があるため。無ければチャンネルの持ち主。
  - 絵・動画: 概要欄の ◆ラベル、無ければ ◆ が付いていない書き方（「Movie：LAN」「Illust　どろ」
    「Illustration by どろ」、ラベルだけの行の次の行）からも拾う。無ければ空。
"""

import re

import extract

# タイトルに出るメンバーの表記。値は正式名。
ALIASES = {
    "暇72": "暇72",
    "ひまなつ": "暇72",
    "雨乃こさめ": "雨乃こさめ",
    "雨野こさめ": "雨乃こさめ",
    "こさめ": "雨乃こさめ",
    "いるま": "いるま",
    "LAN": "LAN",
    "らん": "LAN",
    "すち": "すち",
    "みこと": "みこと",
}

# ショートは現在3分まで。ハッシュタグから曲名を採る対象の境目。
SHORTS_MAX_SECONDS = 180

_DURATION = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")
_TOKEN_SPLIT = re.compile(r"[／/×＆&,、・･\s【】\[\]()（）『』「」“”\"'‘’#＃]+")
_LEAD = re.compile(r"^(?:\s*【[^【】]*】)+\s*")
_TRAIL = re.compile(r"(?:\s*【[^【】]*】)+\s*$")
_SPLIT = re.compile(r"\s*／\s*|\s+/\s+")
_COVER_TAIL = re.compile(r"\s*(?:歌ってみた|Covered? by\s*\S+|Cover\b.*|[(（]cover[)）])\s*$", re.IGNORECASE)
_SEGMENT_END = re.compile(r"\s*【|\s*\[|\s+Covered? by|\s+Cover\b|\s*[(（]cover[)）]", re.IGNORECASE)
_OFFICIAL = re.compile(r"^\s*(?P<artist>.+?)\s*[-‐－ー–—]\s*(?P<song>.+?)\s*\[Official", re.IGNORECASE)
_QUOTED = re.compile(r'[『“”"]([^『』“”"]+)[』“”"]')
_PAIR_QUOTE = re.compile(r"^['\"‘’“”](.+?)['\"‘’“”](?=\s|$)")
_ORIGINAL_MARK = re.compile(r"\[Official|【MV】|【Official", re.IGNORECASE)
_COVER_MARK = re.compile(r"【Cover】|Covered? by|Cover\b|[(（]cover[)）]|歌ってみた|声真似", re.IGNORECASE)
# 【#多声類】のように括弧に入ったタグの、閉じ括弧を含めない
_HASHTAG = re.compile(r"[#＃]([^\s#＃　】\]）)」』]+)")

# ハッシュタグのうち、曲名ではないもの（小文字で比べる）。実データで見つけたら足す。
GENERIC_TAGS = {
    "歌ってみた", "歌ってみた合唱", "歌い手", "歌", "カバー", "cover", "歌ってみたshorts",
    "shorts", "short", "ショート", "shortvideo", "fyp", "おすすめ", "バズ", "バズ曲", "トレンド",
    "vtuber", "vsinger", "新人vtuber", "男性vtuber", "vチューバー",
    "両声類", "多声類", "高音厨", "低音厨", "声真似", "tiktok", "tiktokbest",
    "anime", "アニメ", "漫画", "シクフォニ", "しくふぉに", "ボカロ", "ボカロ曲",
}


# --------------------------------------------------------------------------
# 絵・動画の担当（◆ が無い書き方も含める）
# --------------------------------------------------------------------------

_BULLETS = "◆◇■□●○◎▽▷・-*＊ 　"
_URL = re.compile(r"https?://\S+")
# ラベルと値の区切り。URLの「https:」の「:」は区切りにしない。
_LABEL_SEPARATOR = re.compile(r"[：　]|:(?!//)")
_SENTENCE = re.compile(r"[。！？!?、]")
# 行頭の語がこの語だけでできているとき、その行はラベル。文章の途中の「movie」を拾わないため。
_LABEL_VOCAB = re.compile(
    r"(?:vocal|mix|movie|video|illust[a-z]*|i{1,3}l{1,3}ust[a-z]*|illustrator|animation|art|design|character|main|sub|and|by|mv"
    r"|動画|絵|イラスト|イラストレーター|作画|アニメ(?:ション)?|映像|サムネイラスト)+"
)
_SINGLE_WORD_LABELS = {"movie", "video", "illust", "illustration", "illustrator", "animation", "art", "mv", "動画", "絵", "イラスト", "映像", "作画"}


def _split_label(line):
    """行を (ラベル, 値) に分ける。区切りは「：」「:」全角スペース、「by」、または単語1つのラベルのあとの半角スペース。"""
    s = line.strip().lstrip(_BULLETS).strip()
    m = re.match(r"^[【\[(（]([^】\])）]{1,30})[】\])）]\s*(.*)$", s)
    if m:
        return m.group(1), m.group(2)
    sep = _LABEL_SEPARATOR.search(s)
    if sep and 0 < len(s[: sep.start()].strip()) <= 30:
        return s[: sep.start()].strip(), s[sep.end():].strip()
    m = re.match(r"^(\S+)\s+by\s+(.+)$", s, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2)
    head, _, tail = s.partition(" ")
    if head.lower() in _SINGLE_WORD_LABELS and _URL.search(tail):
        return head, tail
    return s, ""


def _label_columns(head):
    """head がラベルなら、入る列（絵・動画）を返す。文章の一部なら空。"""
    if not head or len(head) > 30 or _SENTENCE.search(head):
        return ()
    normalized = extract._normalize_label(head)
    if not _LABEL_VOCAB.fullmatch(normalized):
        return ()
    if normalized == "絵":  # 本体の◆ラベルには「絵」単体は無いが、メンバーのチャンネルにはある
        return ("絵",)
    return tuple(c for c in extract._match_columns(head) if c in ("絵", "動画"))


def _people(text):
    """値の文字列から人名を取り出す。URLは捨て、全角スペース・括弧の手前までを名前とする。"""
    names = []
    for line in text.split("\n"):
        name = extract._clean_name(_URL.sub("", line))
        for part in re.split(r"\s*[/／]\s*", name):
            if part.strip() and part.strip() not in names:
                names.append(part.strip())
    return names


def loose_credits(description):
    """概要欄から絵・動画の担当を拾う。{列: [名前]}。◆ の有無を問わない。

    ラベルと名前が同じ行にあるもの（Movie：LAN）と、ラベルだけの行の次の行に名前があるものを見る。
    """
    lines = extract.strip_invisible(description).split("\n")
    found = {}
    i = 0
    while i < len(lines):
        head, value = _split_label(lines[i])
        columns = _label_columns(head)
        if not columns:
            i += 1
            continue
        values = [value] if value else []
        j = i + 1
        if not value:
            # ラベルだけの行: 次の空行・区切り線・別のラベルまでの数行が名前
            while j < len(lines) and len(values) < 4:
                nxt = lines[j].strip()
                if not nxt or extract._DIVIDER.match(nxt) or _label_columns(_split_label(nxt)[0]):
                    break
                values.append(nxt)
                j += 1
        names = _people("\n".join(values))
        if 0 < len(names) <= extract._MAX_VALUE_LINES and all(len(n) <= extract._MAX_NAME_LEN for n in names):
            for column in columns:
                found.setdefault(column, names)
        i = max(j, i + 1)
    return found


def parse_duration(iso):
    """PT1M30S 形式を秒にする。ライブ等で形式に合わなければ None。"""
    m = _DURATION.match(iso or "")
    if not m or not any(m.groups()):
        return None
    hours, minutes, seconds = (int(g or 0) for g in m.groups())
    return hours * 3600 + minutes * 60 + seconds


def is_short(video):
    seconds = parse_duration(video.get("contentDetails", {}).get("duration"))
    return seconds is not None and seconds <= SHORTS_MAX_SECONDS


# --------------------------------------------------------------------------
# 分類・曲名
# --------------------------------------------------------------------------


def playlist_category(name):
    """再生リスト名からカバー/オリジナルの見当を付ける。タイトルの表記があればそちらを優先する。"""
    lowered = (name or "").lower()
    if "オリジナル" in (name or "") or "original" in lowered:
        return "original"
    if any(k in (name or "") for k in ("歌ってみた", "ワンコーラス", "おうたの")) or "cover" in lowered or "rap arrange" in lowered:
        return "cover"
    return None


def title_category(title):
    title = extract.strip_invisible(title)
    if _ORIGINAL_MARK.search(title):
        return "original"
    if _COVER_MARK.search(title):
        return "cover"
    return None


def song_from_hashtags(*texts):
    """最初の、曲名ではないハッシュタグ。ショートは曲名がここに入る。"""
    for text in texts:
        for tag in _HASHTAG.findall(extract.strip_invisible(text)):
            if tag.lower() not in GENERIC_TAGS and "メドレー" not in tag:
                return tag
    return None


def parse_title(title):
    """タイトルから曲名を取る。song が None なら取れなかった。

    song_like は「曲のタイトルらしい」形（区切りの／・カバーの表記・Official 等）が見えたかどうか。
    """
    title = extract.strip_invisible(title).strip()
    result = {"song": None, "song_like": False, "note": None}

    official = _OFFICIAL.match(title)
    if official:
        result.update(song=official.group("song").strip(), song_like=True)
        return result

    body = title
    # 「『曲名』歌ってみた」「”曲名”歌ってみた」の形（声真似シリーズ）
    quoted = _QUOTED.search(title)
    if quoted and "歌ってみた" in title:
        body = quoted.group(1).strip()
        result["song_like"] = True
    else:
        lead = _LEAD.match(title)
        stripped = _TRAIL.sub("", _LEAD.sub("", title, count=1)).strip()
        # 先頭の【】だけで中身が無いタイトルは、先頭の【】を曲名の候補に戻す
        body = stripped or (lead.group(0).strip("【】 ") if lead else title)

    parts = _SPLIT.split(body, maxsplit=1)
    left = parts[0]
    if len(parts) > 1:
        result["song_like"] = True
    left = _COVER_TAIL.sub("", left).strip()
    left = _PAIR_QUOTE.sub(r"\1", left).strip()
    if title_category(title):
        result["song_like"] = True
    if not left:
        return result
    result["song"] = left
    if len(parts) == 1 and not quoted:
        result["note"] = "区切りの「／」が無く、タイトル全体を曲名とした"
    return result


# --------------------------------------------------------------------------
# 歌唱者
# --------------------------------------------------------------------------


def _alias(token):
    return ALIASES.get(token) or ALIASES.get(token.upper())


def singers_in_title(title):
    """タイトルに出るメンバー名を、出た順に。"""
    found = []
    for token in _TOKEN_SPLIT.split(extract.strip_invisible(title)):
        name = _alias(token) if token else None
        if name and name not in found:
            found.append(name)
    return found


def guest_candidates(title):
    """「曲名／キルシュトルテ × 暇72」のように、メンバー以外の名前が × や ＆ で並ぶもの。

    共演者か、原曲側の名義か区別が付かないので、要確認の材料として返す。
    """
    text = _LEAD.sub("", extract.strip_invisible(title), count=1)
    m = _SPLIT.search(text)
    if not m:
        return []
    segment = _SEGMENT_END.split(text[m.end():], maxsplit=1)[0]
    parts = [p.strip() for p in re.split(r"\s*[×＆&]\s*", segment) if p.strip()]
    if len(parts) < 2:
        return []
    return [p for p in parts if not _alias(p)]


# --------------------------------------------------------------------------
# 1動画 → 1行
# --------------------------------------------------------------------------

MEMBER_FIELDS = [
    "メンバー",
    "曲名",
    "曲名の出所",
    "category",
    "歌ってる人",
    "歌唱者の出所",
    "絵",
    "動画",
    "投稿日",
    "動画タイトル",
    "再生リスト",
    "ショート",
    "video_id",
    "動画URL",
    "要確認",
    "要確認理由",
]


def resolve_song(title, description, short, from_playlist):
    """(曲名, 出所, 注記) を返す。曲名が None なら取れなかった。

    再生リスト経由の動画は運営が選んだ曲なので、区切りが無くてもタイトル全体を曲名として採る。
    アップロード一覧だけから来た動画は、曲のタイトルらしい形のものだけを採る。
    """
    if short:
        tag = song_from_hashtags(title, description)
        if tag:
            return tag, "ハッシュタグ", None
    parsed = parse_title(title)
    if parsed["song"] and (parsed["song_like"] or from_playlist):
        return parsed["song"], "タイトル", parsed["note"]
    return None, None, "曲名を判定できない"


def member_row(video, member, playlist=None):
    snippet = video["snippet"]
    title = snippet["title"]
    description = snippet.get("description", "")
    short = is_short(video)

    song, source, song_note = resolve_song(title, description, short, playlist is not None)

    category = title_category(title) or playlist_category(playlist)
    notes = []
    if song_note:
        notes.append(song_note)
    if song and not category:
        notes.append("カバーかオリジナルか判定できない")

    singers = singers_in_title(title)
    singer_source = "タイトル"
    if not singers:
        singers, singer_source = [member], "チャンネル"
    guests = guest_candidates(title)
    if guests:
        notes.append(f"共演者の可能性: {' / '.join(guests)}")

    credits = extract.credits_by_column(description)
    loose = loose_credits(description)
    values = {}
    for column in ("絵", "動画"):
        entry = credits.get(column)
        if entry and not entry["suspect"]:
            values[column] = " / ".join(entry["names"])
        else:
            values[column] = " / ".join(loose.get(column, []))

    return {
        "メンバー": member,
        "曲名": song or "",
        "曲名の出所": source or "",
        "category": category or "",
        "歌ってる人": " / ".join(singers),
        "歌唱者の出所": singer_source,
        "絵": values["絵"],
        "動画": values["動画"],
        "投稿日": extract.to_jst_date(snippet["publishedAt"]),
        "動画タイトル": extract.strip_invisible(title),
        "再生リスト": playlist or "",
        "ショート": "はい" if short else "",
        "video_id": video["id"],
        "動画URL": f"https://youtu.be/{video['id']}",
        "要確認": "要確認" if notes else "",
        "要確認理由": " / ".join(notes),
    }
