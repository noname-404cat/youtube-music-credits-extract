"""楽曲の再生リスト以外の調査用スクリプト。

    # 1. 「日常」「歌チャレンジ」再生リストから、▼本家様 がある動画の曲タイトル・動画タイトル・投稿日を集める
    python3 fetch_extra.py honke --out honke.csv

    # 2. ショート動画に、長尺と同じ項目（タグ・クレジット・本家様など）があるかを調べる
    python3 fetch_extra.py shorts --limit 30 --out shorts.csv --dump shorts_sample.json

APIキーは fetch_and_build.py と同じ（環境変数 YOUTUBE_API_KEY か Colab の Secrets）。
"""

import argparse
import collections
import csv
import json
import re
import sys
import urllib.error
import urllib.request

import extract
import fetch_and_build as fb

HONKE_PLAYLISTS = {
    "日常": "PLppXIlUC-oPyaxRSpRoy-KjULmacUGsiF",
    "歌チャレンジ": "PLppXIlUC-oPwyVf-u8bnH_LROH8W2xd0L",
}
HONKE_MARK = "本家様"

# 動画の詳細を広めに取る。ショートに何が付いているかを調べるため。
SHORTS_PARTS = "snippet,contentDetails,statistics,status,topicDetails,recordingDetails,localizations"
# ショートは現在3分まで。長尺との境目として使う。
SHORTS_MAX_SECONDS = 180

_HEADING = re.compile(r"^\s*[▼◆■●▶▷◇]\s*(?P<text>.+?)\s*$")
_DURATION = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")
_COLLAB_KEY = re.compile(r"collab|contribut|partner|co-?creator", re.IGNORECASE)


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
# 2. ショート動画の調査
# --------------------------------------------------------------------------


def parse_duration(iso):
    """PT1M30S 形式を秒にする。ライブ等で形式に合わなければ None。"""
    m = _DURATION.match(iso or "")
    if not m or not any(m.groups()):
        return None
    hours, minutes, seconds = (int(g or 0) for g in m.groups())
    return hours * 3600 + minutes * 60 + seconds


def flatten_keys(obj, prefix=""):
    """JSON に出てくるキーの経路（snippet.tags など）を集める。リストの中は [] で表す。"""
    keys = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            keys.add(path)
            keys |= flatten_keys(value, path)
    elif isinstance(obj, list):
        for value in obj:
            keys |= flatten_keys(value, prefix + "[]")
    return keys


def shorts_playlist_id(channel_id):
    """チャンネルのショート一覧（UC→UUSH）。公式に文書化された仕組みではない。"""
    return "UUSH" + channel_id[2:]


def uploads_playlist_id(channel_id):
    return "UU" + channel_id[2:]


def fetch_recent_playlist_ids(api_key, playlist_id, limit):
    """再生リストの先頭（新しい順）から limit 件まで。全件は取らない。"""
    ids = []
    page_token = None
    while len(ids) < limit:
        params = {"part": "contentDetails", "playlistId": playlist_id, "maxResults": 50}
        if page_token:
            params["pageToken"] = page_token
        page = fb.api_get(api_key, "playlistItems", **params)
        ids.extend(item["contentDetails"]["videoId"] for item in page.get("items", []))
        page_token = page.get("nextPageToken")
        if not page_token:
            break
    return ids[:limit]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def is_short_by_url(video_id):
    """youtube.com/shorts/ID はショートなら 200、長尺なら watch へ 30x で飛ばされる。"""
    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(
        f"https://www.youtube.com/shorts/{video_id}", method="HEAD"
    )
    try:
        with opener.open(request, timeout=15) as resp:
            return resp.status == 200
    except urllib.error.HTTPError:
        return False


def find_shorts_by_scan(api_key, limit, scan_max):
    """UUSH が使えないときの代替。アップロード一覧を新しい順に見て、3分以下かつ shorts URL が通るものを拾う。"""
    ids = fetch_recent_playlist_ids(api_key, uploads_playlist_id(fb.CHANNEL_ID), scan_max)
    videos = []
    for video in fb.fetch_videos(api_key, ids, part=SHORTS_PARTS):
        seconds = parse_duration(video["contentDetails"].get("duration"))
        if seconds is not None and seconds <= SHORTS_MAX_SECONDS and is_short_by_url(video["id"]):
            videos.append(video)
            if len(videos) >= limit:
                break
    return videos


def collect_shorts(api_key, limit, force_scan=False, scan_max=300):
    """(動画のリスト, 取得方法の説明) を返す。"""
    if not force_scan:
        try:
            ids = fetch_recent_playlist_ids(api_key, shorts_playlist_id(fb.CHANNEL_ID), limit)
        except urllib.error.HTTPError as exc:
            print(f"  ショート一覧(UUSH)が取れなかった: HTTP {exc.code}。アップロード一覧を走査する")
        else:
            if ids:
                videos = fb.fetch_videos(api_key, ids, part=SHORTS_PARTS)
                return videos, "ショート一覧(UUSH)の新しい順"
            print("  ショート一覧(UUSH)が空だった。アップロード一覧を走査する")
    videos = find_shorts_by_scan(api_key, limit, scan_max)
    return videos, f"アップロード一覧の新しい{scan_max}本から、3分以下かつ shorts URL が通るもの"


def analyze_shorts(videos):
    """ショートに何が付いているかを数える。表示は print_shorts_report に任せる。"""
    result = {"n": len(videos)}

    key_counts = collections.Counter()
    for video in videos:
        key_counts.update(flatten_keys(video))
    result["key_counts"] = key_counts
    result["collab_keys"] = sorted(k for k in key_counts if _COLLAB_KEY.search(k))

    tag_lists = [v["snippet"].get("tags", []) for v in videos]
    result["with_tags"] = sum(1 for t in tag_lists if t)
    result["top_tags"] = collections.Counter(t for tags in tag_lists for t in tags).most_common(15)

    result["durations"] = sorted(
        d for d in (parse_duration(v["contentDetails"].get("duration")) for v in videos if "contentDetails" in v) if d is not None
    )

    found = collections.Counter()
    honke = title_song = singer_marked = credit_labels = 0
    for video in videos:
        title = video["snippet"]["title"]
        description = video["snippet"].get("description", "")
        credits = extract.credits_by_column(description)
        for column in credits:
            found[column] += 1
        if extract.parse_credit_blocks(description):
            credit_labels += 1
        if extract.extract_medley_songs(description):
            honke += 1
        song, _, _ = extract.extract_song(title, description)
        if song:
            title_song += 1
        if extract.extract_singers(title)[1] is None:
            singer_marked += 1
    result["credit_columns"] = found
    result["with_credit_labels"] = credit_labels
    result["with_honke"] = honke
    result["song_extracted"] = title_song
    result["singers_in_title"] = singer_marked

    # 概要欄の末尾に「××× 毎日更新 ×××」の装飾があり、×は概要欄では数えられない。概要欄は「コラボ」だけを見る。
    result["collab_text"] = sum(
        1
        for v in videos
        if re.search(r"コラボ|feat\.?|×", v["snippet"]["title"], re.IGNORECASE)
        or "コラボ" in v["snippet"].get("description", "")
    )
    result["with_mention"] = sum(1 for v in videos if "@" in v["snippet"].get("description", ""))
    return result


def print_shorts_report(result, source):
    n = result["n"]
    print()
    print("=" * 78)
    print("調査: ショート動画")
    print("=" * 78)
    print(f"  対象: {n} 本（{source}）")
    if not n:
        return

    durations = result["durations"]
    if durations:
        print(f"  長さ(秒): 最短 {durations[0]} / 中央 {durations[len(durations) // 2]} / 最長 {durations[-1]}")

    print()
    print("  【タグ】")
    print(f"    snippet.tags がある動画: {result['with_tags']} / {n} 本")
    for tag, count in result["top_tags"]:
        print(f"    {count:4d}  {tag}")

    print()
    print("  【コラボレーター】")
    if result["collab_keys"]:
        print(f"    collab/contributor 等を含むキー: {result['collab_keys']}")
    else:
        print("    APIの応答に collab/contributor/partner を含むキーは無かった")
    print(f"    タイトルに「コラボ」「feat」「×」、または概要欄に「コラボ」がある動画: {result['collab_text']} / {n} 本")
    print(f"    概要欄に @ がある動画: {result['with_mention']} / {n} 本")

    print()
    print("  【長尺と同じ項目が概要欄・タイトルから取れるか】")
    print(f"    ◆ラベルのクレジットがある動画: {result['with_credit_labels']} / {n} 本")
    for column in ("作詞", "作曲", "絵", "動画"):
        print(f"      {column}: {result['credit_columns'].get(column, 0)} / {n} 本")
    print(f"    ▼本家様の曲が取れた動画: {result['with_honke']} / {n} 本")
    print(f"    曲名が取れた動画: {result['song_extracted']} / {n} 本")
    print(f"    タイトルに歌唱者の表記がある動画: {result['singers_in_title']} / {n} 本")

    print()
    print("  【videos.list の応答に含まれていたキー（何本中何本に出たか）】")
    for key, count in sorted(result["key_counts"].items()):
        print(f"    {count:4d}/{n}  {key}")


SHORTS_FIELDS = [
    "動画タイトル",
    "投稿日",
    "秒数",
    "タグ",
    "曲名",
    "歌ってる人",
    "歌唱者は推定",
    "作詞",
    "作曲",
    "絵",
    "動画",
    "本家様の曲",
    "video_id",
    "動画URL",
    "概要欄の先頭",
]


def shorts_row(video):
    row = extract.build_row(video, "short")
    snippet = video["snippet"]
    return {
        "動画タイトル": row["タイトル"],
        "投稿日": row["投稿日"],
        "秒数": parse_duration(video.get("contentDetails", {}).get("duration")) or "",
        "タグ": " | ".join(snippet.get("tags", [])),
        "曲名": row["曲名"],
        "歌ってる人": row["歌ってる人"],
        "歌唱者は推定": row["歌唱者は推定"],
        "作詞": row["作詞"],
        "作曲": row["作曲"],
        "絵": row["絵"],
        "動画": row["動画"],
        "本家様の曲": " | ".join(extract.extract_medley_songs(snippet.get("description", ""))),
        "video_id": row["video_id"],
        "動画URL": row["動画URL"],
        "概要欄の先頭": snippet.get("description", "")[:200].replace("\n", " ⏎ "),
    }


def run_shorts(args):
    api_key = fb.get_api_key()
    videos, source = collect_shorts(api_key, args.limit, args.scan, args.scan_max)
    rows = [shorts_row(v) for v in videos]
    write_csv(args.out, SHORTS_FIELDS, rows)
    print(f"{len(rows)} 行を {args.out} に書き出した")
    if args.dump:
        with open(args.dump, "w", encoding="utf-8") as fh:
            json.dump(videos, fh, ensure_ascii=False, indent=2)
        print(f"応答の生データを {args.dump} に書き出した")
    print_shorts_report(analyze_shorts(videos), source)


# --------------------------------------------------------------------------


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

    shorts = sub.add_parser("shorts", help="ショート動画に付いている情報の調査")
    shorts.add_argument("--limit", type=int, default=30, help="調べるショートの本数（新しい順）")
    shorts.add_argument("--out", default="shorts.csv")
    shorts.add_argument("--dump", help="APIの応答の生データを書き出すJSON")
    shorts.add_argument("--scan", action="store_true", help="UUSHを使わずアップロード一覧から探す")
    shorts.add_argument("--scan-max", type=int, default=300, help="--scan で見る動画の本数")
    shorts.set_defaults(run=run_shorts)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
