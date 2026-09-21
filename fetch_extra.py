"""楽曲の再生リスト以外の調査用スクリプト。

    # 1. 「日常」「歌チャレンジ」再生リストから、▼本家様 がある動画の曲タイトル・動画タイトル・投稿日を集める
    python3 fetch_extra.py honke --out honke.csv

    # 2. 「シクフォニ歌ってみた Shorts」再生リストから曲名を集める
    python3 fetch_extra.py shorts --out shorts.csv

    # 3. 各メンバーのチャンネルの再生リストと概要欄の書式を調べる
    python3 fetch_extra.py members

    # 4. 各メンバーの曲名・歌唱者・カバー/オリジナルを1動画1行のCSVにする
    python3 fetch_extra.py member-songs --out member_songs.csv

APIキーは fetch_and_build.py と同じ（環境変数 YOUTUBE_API_KEY か Colab の Secrets）。
"""

import argparse
import collections
import csv
import re
import urllib.error

import extract
import fetch_and_build as fb
import members

HONKE_PLAYLISTS = {
    "日常": "PLppXIlUC-oPyaxRSpRoy-KjULmacUGsiF",
    "歌チャレンジ": "PLppXIlUC-oPwyVf-u8bnH_LROH8W2xd0L",
}
HONKE_MARK = "本家様"

_HEADING = re.compile(r"^\s*[▼◆■●▶▷◇]\s*(?P<text>.+?)\s*$")


# --------------------------------------------------------------------------
# 1. 本家様つきの動画
# --------------------------------------------------------------------------


def has_honke(video):
    return HONKE_MARK in extract.strip_invisible(video["snippet"].get("description", ""))


def honke_row(video, playlist):
    """曲タイトルは ▼本家様 欄の表記のまま ` | ` 区切り。メドレーは複数入る。"""
    snippet = video["snippet"]
    songs = extract.extract_medley_songs(snippet.get("description", ""))
    return {
        "再生リスト": playlist,
        "曲タイトル": " | ".join(songs),
        "曲数": len(songs),
        "動画タイトル": extract.strip_invisible(snippet["title"]),
        "投稿日": extract.to_jst_date(snippet["publishedAt"]),
        "video_id": video["id"],
        "動画URL": f"https://youtu.be/{video['id']}",
    }


HONKE_FIELDS = ["再生リスト", "曲タイトル", "曲数", "動画タイトル", "投稿日", "video_id", "動画URL"]
SONG_FIELDS = ["再生リスト", "曲タイトル", "動画タイトル", "投稿日", "曲順", "曲数", "video_id", "動画URL"]


def honke_song_rows(video, playlist):
    """1曲1行。曲順は本家様欄に書かれた順、曲数はその動画の曲の総数。"""
    snippet = video["snippet"]
    songs = extract.extract_medley_songs(snippet.get("description", ""))
    return [
        {
            "再生リスト": playlist,
            "曲タイトル": song,
            "動画タイトル": extract.strip_invisible(snippet["title"]),
            "投稿日": extract.to_jst_date(snippet["publishedAt"]),
            "曲順": order,
            "曲数": len(songs),
            "video_id": video["id"],
            "動画URL": f"https://youtu.be/{video['id']}",
        }
        for order, song in enumerate(songs, start=1)
    ]


def collect_honke(api_key):
    """再生リストごとに videoId を集める。重複は先に見つかった再生リストを採る。"""
    playlist_of = {}
    per_playlist = {}
    for name, playlist_id in HONKE_PLAYLISTS.items():
        ids = fb.fetch_playlist_video_ids(api_key, playlist_id)
        per_playlist[name] = ids
        for video_id in ids:
            playlist_of.setdefault(video_id, name)

    fetched = fb.fetch_videos(api_key, list(playlist_of))
    found = {v["id"] for v in fetched}
    missing = [v for v in playlist_of if v not in found]
    mine = [v for v in fetched if v["snippet"].get("channelId") == fb.CHANNEL_ID]
    foreign = [v for v in fetched if v["snippet"].get("channelId") != fb.CHANNEL_ID]
    return playlist_of, per_playlist, mine, foreign, missing


def audit_honke(per_playlist, playlist_of, mine, foreign, missing, rows):
    print()
    print("=" * 78)
    print("監査: 本家様つきの動画")
    print("=" * 78)
    for name, ids in per_playlist.items():
        in_playlist = [v for v in mine if playlist_of[v["id"]] == name]
        with_honke = [v for v in in_playlist if has_honke(v)]
        print(f"  {name}: 再生リスト {len(ids)} 本 / シクフォニのチャンネル {len(in_playlist)} 本 / 本家様あり {len(with_honke)} 本")
    if missing:
        print(f"  取得できず(削除/非公開): {len(missing)} 本  {missing}")
    print(f"  他チャンネルのため除外: {len(foreign)} 本")
    for channel, count in collections.Counter(
        v["snippet"].get("channelTitle", "") for v in foreign
    ).most_common():
        print(f"    {count:4d}  {channel}")

    # 本家様の見出しの表記ゆれを見つけるため、概要欄の見出し行を数える
    headings = collections.Counter()
    for video in mine:
        description = extract.strip_invisible(video["snippet"].get("description", ""))
        for line in description.split("\n"):
            m = _HEADING.match(line)
            if m:
                headings[m.group("text")[:30]] += 1
    print()
    print("  概要欄の見出し行（▼◆など）の出現数（上位30件・本家様の表記ゆれを見る）")
    for text, count in headings.most_common(30):
        print(f"    {count:4d}  {text!r}")

    unresolved = [r for r in rows if not r["曲数"]]
    print()
    print(f"  「本家様」はあるが曲タイトルが取れなかった動画: {len(unresolved)} 本")
    for row in unresolved:
        print(f"    {row['video_id']}  {row['動画タイトル']}")

    counts = collections.Counter(r["曲数"] for r in rows)
    print()
    print("  曲数の分布（曲数: 動画本数）  " + "  ".join(f"{k}曲={v}" for k, v in sorted(counts.items())))

    without = [v for v in mine if not has_honke(v)]
    print()
    print(f"  本家様が無い動画: {len(without)} 本（先頭10件）")
    for video in without[:10]:
        print(f"    {video['id']}  {extract.strip_invisible(video['snippet']['title'])}")


def run_honke(args):
    api_key = fb.get_api_key()
    playlist_of, per_playlist, mine, foreign, missing = collect_honke(api_key)
    with_honke = sorted(
        (v for v in mine if has_honke(v)),
        key=lambda v: v["snippet"]["publishedAt"],
        reverse=True,
    )
    rows = [honke_row(v, playlist_of[v["id"]]) for v in with_honke]
    song_rows = [r for v in with_honke for r in honke_song_rows(v, playlist_of[v["id"]])]
    write_csv(args.out, SONG_FIELDS, song_rows)
    print(
        f"{len(song_rows)} 曲（{len(rows)} 本の動画）を {args.out} に書き出した"
        f"（再生リスト合計 {len(playlist_of)} 本）"
    )
    if args.videos_out:
        write_csv(args.videos_out, HONKE_FIELDS, rows)
        print(f"動画ごとの1行版を {args.videos_out} に書き出した")
    if not args.no_audit:
        audit_honke(per_playlist, playlist_of, mine, foreign, missing, rows)


# --------------------------------------------------------------------------
# 2. ショート動画（シクフォニ歌ってみた Shorts）
# --------------------------------------------------------------------------

SHORTS_PLAYLIST = "PLppXIlUC-oPwMYxLewbvGWpVJGzjXVR8P"
# ショートは概要欄がハッシュタグだけで、クレジットも歌唱者も書かれていない。曲名だけを採る。
SHORTS_PARTS = "snippet,contentDetails,statistics"
parse_duration = members.parse_duration


def shorts_song(title, description=""):
    """(曲名, 注記)。メンバーのショートと同じ規則（members.resolve_song）。

    タイトルの「曲名 / 誰か」→ タイトルと概要欄のハッシュタグ → タイトル末尾の【曲名】の順。
    シクフォニ歌ってみた Shorts は歌のショートだけの再生リストなので、曲名が取れなければ空にする。
    """
    song, _, note = members.resolve_song(title, description, True, False)
    return song, note


def shorts_song_source(title, description=""):
    return members.resolve_song(title, description, True, False)[1] or ""


SHORTS_FIELDS = [
    "曲名",
    "曲名の出所",
    "投稿日",
    "動画タイトル",
    "秒数",
    "再生数",
    "タグ",
    "video_id",
    "動画URL",
    "要確認",
    "要確認理由",
]


def shorts_row(video):
    snippet = video["snippet"]
    description = snippet.get("description", "")
    song, source, note = members.resolve_song(snippet["title"], description, True, False)
    return {
        "曲名": song or "",
        "曲名の出所": source or "",
        "投稿日": extract.to_jst_date(snippet["publishedAt"]),
        "動画タイトル": extract.strip_invisible(snippet["title"]),
        "秒数": parse_duration(video.get("contentDetails", {}).get("duration")) or "",
        "再生数": video.get("statistics", {}).get("viewCount", ""),
        "タグ": " | ".join(snippet.get("tags", [])),
        "video_id": video["id"],
        "動画URL": f"https://youtu.be/{video['id']}",
        "要確認": "要確認" if note else "",
        "要確認理由": note or "",
    }


def audit_shorts(videos, foreign, missing, rows):
    print()
    print("=" * 78)
    print("監査: ショート（シクフォニ歌ってみた Shorts）")
    print("=" * 78)
    print(f"  再生リスト {len(videos) + len(foreign) + len(missing)} 本 / シクフォニのチャンネル {len(videos)} 本")
    if foreign:
        print(f"  他チャンネルのため除外: {len(foreign)} 本")
    if missing:
        print(f"  取得できず(削除/非公開): {len(missing)} 本  {missing}")
    durations = sorted(d for d in (r["秒数"] for r in rows) if d)
    if durations:
        print(f"  長さ(秒): 最短 {durations[0]} / 中央 {durations[len(durations) // 2]} / 最長 {durations[-1]}")

    unresolved = [r for r in rows if not r["曲名"]]
    print()
    print(f"  曲名が取れなかった動画: {len(unresolved)} / {len(rows)} 本")
    for row in unresolved:
        print(f"    {row['video_id']}  {row['動画タイトル']}")
    sources = collections.Counter(r["曲名の出所"] or "(取れず)" for r in rows)
    print("  曲名の出所: " + "  ".join(f"{k}={v}" for k, v in sources.most_common()))


def run_shorts(args):
    api_key = fb.get_api_key()
    ids = fb.fetch_playlist_video_ids(api_key, SHORTS_PLAYLIST)
    fetched = fb.fetch_videos(api_key, ids, part=SHORTS_PARTS)
    found = {v["id"] for v in fetched}
    missing = [v for v in ids if v not in found]
    videos = [v for v in fetched if v["snippet"].get("channelId") == fb.CHANNEL_ID]
    foreign = [v for v in fetched if v["snippet"].get("channelId") != fb.CHANNEL_ID]
    videos.sort(key=lambda v: v["snippet"]["publishedAt"], reverse=True)

    rows = [shorts_row(v) for v in videos]
    write_csv(args.out, SHORTS_FIELDS, rows)
    print(f"{len(rows)} 行を {args.out} に書き出した")
    if not args.no_audit:
        audit_shorts(videos, foreign, missing, rows)


# --------------------------------------------------------------------------
# 3. 各メンバーのチャンネルの調査
# --------------------------------------------------------------------------

# 対象の再生リスト名と、再生リストに入っていない動画も拾うか。
#   uploads: 配信以外のアップロードをすべて新しい順に見る（いるま・みこと）
#   shorts : 再生リストに入っていないショートだけを足す（ショートは再生リストに入っていないことが多い）
MEMBER_SOURCES = {
    "暇72": {"playlists": ["Covered by 暇72", "声真似歌ってみた。", "銀魂×四字熟語"], "shorts": True},
    "雨乃こさめ": {"playlists": ["オリジナル曲", "歌ってみた！", "ワンコーラス"], "shorts": True},
    "いるま": {
        "playlists": [
            "Original (Solo)",
            "Original (Group)",
            "Cover (Solo)",
            "Rap arrange (Group)",
            "Rap Collaboration",
            "Rapppp",
        ],
        "uploads": True,
    },
    "LAN": {"playlists": ["LAN歌ってみた", "LANオリジナル曲", "おうたのshort"], "shorts": True},
    "すち": {"playlists": ["歌ってみた"], "shorts": True},
    "みこと": {"uploads": True},
}
# 調査コマンド用。ALL_UPLOADS は「再生リスト問わず、配信以外すべて」の意味。
ALL_UPLOADS = "＊配信以外すべて"
MEMBER_TARGETS = {
    member: spec.get("playlists", []) + ([ALL_UPLOADS] if spec.get("uploads") else [])
    for member, spec in MEMBER_SOURCES.items()
}


def member_channel_ids(api_key):
    """メンバーのチャンネルIDを、シクフォニの再生リストに混ざる本人の動画から引く。

    再生リストには各メンバーのオリジナル曲が入っており、その channelId が本人のチャンネル。
    ハンドル名を当て推量せずに済む。
    """
    ids = []
    for playlist_id in fb.PLAYLISTS.values():
        ids.extend(fb.fetch_playlist_video_ids(api_key, playlist_id))
    found = {}
    for video in fb.fetch_videos(api_key, list(dict.fromkeys(ids))):
        snippet = video["snippet"]
        if snippet.get("channelId") == fb.CHANNEL_ID:
            continue
        title = snippet.get("channelTitle", "")
        for member in MEMBER_TARGETS:
            if member in title:
                found.setdefault(member, {"channelId": snippet["channelId"], "channelTitle": title})
    return found


def fetch_channel_playlists(api_key, channel_id):
    playlists = []
    page_token = None
    while True:
        params = {"part": "snippet,contentDetails", "channelId": channel_id, "maxResults": 50}
        if page_token:
            params["pageToken"] = page_token
        page = fb.api_get(api_key, "playlists", **params)
        playlists.extend(page.get("items", []))
        page_token = page.get("nextPageToken")
        if not page_token:
            break
    return playlists


def match_playlists(playlists, targets):
    """再生リスト名の完全一致を優先し、無ければ部分一致で拾う。"""
    matched = {}
    for target in targets:
        if target == ALL_UPLOADS:
            continue
        exact = [p for p in playlists if p["snippet"]["title"].strip() == target]
        partial = [p for p in playlists if target in p["snippet"]["title"]]
        matched[target] = exact or partial
    return matched


def describe_videos(videos, label, sample):
    """その集まりの書式の規則性を出す。概要欄のラベルとタイトルの形を見る。"""
    labels = collections.Counter()
    honke = live = 0
    for video in videos:
        description = video["snippet"].get("description", "")
        for block in extract.parse_credit_blocks(description):
            if block["before_cutoff"]:
                labels[block["label"].strip()] += 1
        if "本家様" in description:
            honke += 1
        if video["snippet"].get("liveBroadcastContent") not in (None, "none"):
            live += 1
    print(f"    {label}: 調べた {len(videos)} 本 / 本家様あり {honke} 本")
    if labels:
        print("      ◆ラベル: " + "  ".join(f"{k}={v}" for k, v in labels.most_common(12)))
    else:
        print("      ◆ラベル: 無し")
    for video in videos[:sample]:
        snippet = video["snippet"]
        head = snippet.get("description", "").strip().split("\n")[0][:40]
        print(f"      - {extract.to_jst_date(snippet['publishedAt'])} {extract.strip_invisible(snippet['title'])[:52]} | {head}")


def run_members(args):
    api_key = fb.get_api_key()
    channels = member_channel_ids(api_key)
    print()
    print("=" * 78)
    print("調査: 各メンバーのチャンネル")
    print("=" * 78)
    for member in MEMBER_TARGETS:
        info = channels.get(member)
        print(f"  {member}: {info['channelTitle']} ({info['channelId']})" if info else f"  {member}: チャンネルIDが引けなかった")

    for member, targets in MEMBER_TARGETS.items():
        info = channels.get(member)
        print()
        print("-" * 78)
        print(f"■ {member}")
        if not info:
            print("  チャンネルIDが引けなかったので飛ばす")
            continue
        playlists = fetch_channel_playlists(api_key, info["channelId"])
        print(f"  公開再生リスト {len(playlists)} 本")
        for playlist in playlists:
            print(f"    {playlist['contentDetails']['itemCount']:4d} 本  {playlist['snippet']['title']}")

        if ALL_UPLOADS in targets:
            uploads = "UU" + info["channelId"][2:]
            ids = fb.fetch_playlist_video_ids(api_key, uploads)[: args.limit]
            videos = fb.fetch_videos(api_key, ids, part="snippet,contentDetails,liveStreamingDetails")
            streams = [v for v in videos if "liveStreamingDetails" in v]
            others = [v for v in videos if "liveStreamingDetails" not in v]
            print(f"  アップロードの新しい {len(videos)} 本: 配信 {len(streams)} 本 / 配信以外 {len(others)} 本")
            describe_videos(others, "配信以外", args.sample)

        for target, found in match_playlists(playlists, targets).items():
            if not found:
                print(f"  「{target}」: 見つからなかった")
                continue
            for playlist in found:
                ids = fb.fetch_playlist_video_ids(api_key, playlist["id"])[: args.limit]
                videos = fb.fetch_videos(api_key, ids)
                describe_videos(videos, f"「{playlist['snippet']['title']}」", args.sample)


# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# 4. 各メンバーの曲名リスト
# --------------------------------------------------------------------------


def fetch_member_shorts(api_key, channel_id, limit, parts, skip):
    """再生リストに入っていないショートを新しい順に limit 本まで。

    チャンネルのショート一覧（チャンネルIDの UC を UUSH に替えた再生リスト。公式に文書化された方法ではない）から取り、
    使えなければアップロード一覧を3分以下で絞る。
    """
    try:
        ids = fb.fetch_playlist_video_ids(api_key, "UUSH" + channel_id[2:])[:limit]
    except urllib.error.HTTPError:
        ids = []
    if not ids:
        ids = fb.fetch_playlist_video_ids(api_key, "UU" + channel_id[2:])[:limit]
    videos = fb.fetch_videos(api_key, [v for v in ids if v not in skip], part=parts)
    return [v for v in videos if members.is_short(v) and "liveStreamingDetails" not in v]


def collect_member_videos(api_key, channel_id, spec, uploads_limit, shorts_limit=500):
    """(動画, 再生リスト名 または None) のリストと、集計用の情報を返す。

    再生リスト経由の動画は運営が選んだ曲として扱う（再生リスト名は None にならない）。
    uploads が指定されたメンバーは、再生リストに入っていない動画も配信以外に限って足す。
    shorts が指定されたメンバーは、再生リストに入っていないショートだけを足す。
    """
    parts = "snippet,contentDetails,liveStreamingDetails"
    stats = {"missing_playlists": [], "foreign": 0, "live_skipped": 0}
    playlists = fetch_channel_playlists(api_key, channel_id)

    playlist_of = {}
    for target, found in match_playlists(playlists, spec.get("playlists", [])).items():
        if not found:
            stats["missing_playlists"].append(target)
            continue
        for playlist in found:
            for video_id in fb.fetch_playlist_video_ids(api_key, playlist["id"]):
                playlist_of.setdefault(video_id, playlist["snippet"]["title"])

    fetched = {v["id"]: v for v in fb.fetch_videos(api_key, list(playlist_of), part=parts)}
    result = [(fetched[v], name) for v, name in playlist_of.items() if v in fetched]

    if spec.get("uploads"):
        uploads = "UU" + channel_id[2:]
        ids = [v for v in fb.fetch_playlist_video_ids(api_key, uploads)[:uploads_limit] if v not in playlist_of]
        for video in fb.fetch_videos(api_key, ids, part=parts):
            if "liveStreamingDetails" in video:
                stats["live_skipped"] += 1
                continue
            result.append((video, None))
    elif spec.get("shorts"):
        for video in fetch_member_shorts(api_key, channel_id, shorts_limit, parts, set(playlist_of)):
            result.append((video, None))

    own = [(v, p) for v, p in result if v["snippet"].get("channelId") == channel_id]
    stats["foreign"] = len(result) - len(own)
    return own, stats


def audit_member_songs(stats_of, rows):
    print()
    print("=" * 78)
    print("監査: 各メンバーの曲名リスト")
    print("=" * 78)
    for member, stats in stats_of.items():
        mine = [r for r in rows if r["メンバー"] == member]
        print()
        print(f"■ {member}: {len(mine)} 本")
        if stats is None:
            print("  チャンネルIDが引けなかった")
            continue
        songs = [r for r in mine if r["曲名"]]
        print(f"  曲名が取れた {len(songs)} 本 / 要確認 {sum(1 for r in mine if r['要確認'])} 本")
        for name, counter in (
            ("曲名の出所", collections.Counter(r["曲名の出所"] or "(取れず)" for r in mine)),
            ("category", collections.Counter(r["category"] or "(不明)" for r in mine)),
            ("歌唱者の出所", collections.Counter(r["歌唱者の出所"] for r in mine)),
        ):
            print(f"  {name}: " + "  ".join(f"{k}={v}" for k, v in counter.most_common()))
        shorts = [r for r in mine if r["ショート"]]
        print(
            f"  ショート {len(shorts)} 本（曲名が取れた {sum(1 for r in shorts if r['曲名'])} 本）"
            f" / 絵あり {sum(1 for r in mine if r['絵'])} 本 / 動画あり {sum(1 for r in mine if r['動画'])} 本"
        )
        if stats["missing_playlists"]:
            print(f"  見つからなかった再生リスト: {stats['missing_playlists']}")
        if stats["foreign"] or stats["live_skipped"]:
            print(f"  除外: 他チャンネルの動画 {stats['foreign']} 本 / 配信 {stats['live_skipped']} 本")

        unresolved = [r for r in mine if not r["曲名"]]
        if unresolved:
            print(f"  曲名が取れなかった動画 {len(unresolved)} 本（先頭10件）")
            for row in unresolved[:10]:
                print(f"    {row['video_id']}  {row['動画タイトル'][:60]}")
        guests = [r for r in mine if "共演者の可能性" in r["要確認理由"]]
        for row in guests[:10]:
            print(f"  共演者の可能性: {row['動画タイトル'][:40]} -> {row['要確認理由']}")

    tags = collections.Counter(r["曲名"] for r in rows if r["曲名の出所"] == "ハッシュタグ")
    if tags:
        print()
        print("  ハッシュタグ由来の曲名（2回以上出るものは曲名ではない可能性。GENERIC_TAGS に足す候補）")
        for tag, count in tags.most_common(15):
            if count >= 2:
                print(f"    {count:3d}  {tag}")


def run_member_songs(args):
    api_key = fb.get_api_key()
    channels = member_channel_ids(api_key)
    rows = []
    stats_of = {}
    for member, spec in MEMBER_SOURCES.items():
        info = channels.get(member)
        if not info:
            stats_of[member] = None
            continue
        collected, stats_of[member] = collect_member_videos(
            api_key, info["channelId"], spec, args.uploads_limit, args.shorts_limit
        )
        collected.sort(key=lambda item: item[0]["snippet"]["publishedAt"], reverse=True)
        rows.extend(members.member_row(video, member, playlist) for video, playlist in collected)
    write_csv(args.out, members.MEMBER_FIELDS, rows)
    print(f"{len(rows)} 本を {args.out} に書き出した")
    if not args.no_audit:
        audit_member_songs(stats_of, rows)


def write_csv(path, fields, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    honke = sub.add_parser("honke", help="日常・歌チャレンジ再生リストの本家様つき動画")
    honke.add_argument("--out", default="honke.csv", help="1曲1行のCSV")
    honke.add_argument("--videos-out", help="動画ごとの1行版のCSV（任意）")
    honke.add_argument("--no-audit", action="store_true")
    honke.set_defaults(run=run_honke)

    shorts = sub.add_parser("shorts", help="シクフォニ歌ってみた Shorts の曲名")
    shorts.add_argument("--out", default="shorts.csv")
    shorts.add_argument("--no-audit", action="store_true")
    shorts.set_defaults(run=run_shorts)

    members_cmd = sub.add_parser("members", help="各メンバーのチャンネルの再生リストと書式の調査")
    members_cmd.add_argument("--limit", type=int, default=30, help="再生リストごとに調べる本数")
    members_cmd.add_argument("--sample", type=int, default=5, help="画面に出すタイトルの本数")

    member_songs = sub.add_parser("member-songs", help="各メンバーの曲名・歌唱者・カバー/オリジナルのCSV")
    member_songs.add_argument("--out", default="member_songs.csv")
    member_songs.add_argument("--uploads-limit", type=int, default=300, help="再生リスト外も拾うメンバーで、アップロードを新しい順に見る本数")
    member_songs.add_argument("--shorts-limit", type=int, default=500, help="再生リスト外のショートを新しい順に見る本数")
    member_songs.add_argument("--no-audit", action="store_true")
    member_songs.set_defaults(run=run_member_songs)
    members_cmd.set_defaults(run=run_members)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
