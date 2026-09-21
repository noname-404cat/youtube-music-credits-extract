"""再生リストから楽曲動画を集め、クレジットを抽出して CSV にする。

Colab で動かす前提。APIキーは Colab の Secrets から読むか、環境変数 YOUTUBE_API_KEY で渡す。

    python3 fetch_and_build.py --out credits.csv

抽出結果と同時に、書式のばらつきを潰すための監査統計も出力する。
どのラベルが何本に出たか、どのタイトルが形式に当てはまらなかったかが分かる。
"""

import argparse
import collections
import csv
import json
import os
import sys
import urllib.parse
import urllib.request

import extract

API_BASE = "https://www.googleapis.com/youtube/v3"
CHANNEL_ID = "UCGMG8BNfA8gsH9Rn_d_yW2A"

PLAYLISTS = {
    "cover": "PLppXIlUC-oPw8uCDchVYal9ibApaYP-4R",
    "original": "PLppXIlUC-oPw5Giv-JPWi_5DjstLk3ML2",
}


def get_api_key():
    key = os.environ.get("YOUTUBE_API_KEY")
    if key:
        return key
    try:
        from google.colab import userdata

        return userdata.get("YOUTUBE_API_KEY")
    except Exception:
        sys.exit("YOUTUBE_API_KEY が見つからない。環境変数か Colab の Secrets に設定する。")


def api_get(api_key, path, **params):
    params["key"] = api_key
    url = f"{API_BASE}/{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url) as resp:
        return json.load(resp)


def fetch_playlist_video_ids(api_key, playlist_id):
    """再生リストの全 videoId を順に返す。1ページ50件。"""
    video_ids = []
    page_token = None
    while True:
        params = {"part": "contentDetails", "playlistId": playlist_id, "maxResults": 50}
        if page_token:
            params["pageToken"] = page_token
        page = api_get(api_key, "playlistItems", **params)
        for item in page.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])
        page_token = page.get("nextPageToken")
        if not page_token:
            break
    return video_ids


def fetch_videos(api_key, video_ids, part="snippet"):
    """videos.list を50IDずつ束ねて叩く。削除・非公開の動画は返ってこない。"""
    videos = []
    for start in range(0, len(video_ids), 50):
        chunk = video_ids[start : start + 50]
        page = api_get(api_key, "videos", part=part, id=",".join(chunk))
        videos.extend(page.get("items", []))
    return videos


def collect(api_key):
    """再生リストごとに videoId を集め、重複は先に見つかった方のカテゴリを採用する。"""
    category_of = {}
    order = []
    per_playlist = {}
    for category, playlist_id in PLAYLISTS.items():
        ids = fetch_playlist_video_ids(api_key, playlist_id)
        per_playlist[category] = ids
        for video_id in ids:
            if video_id in category_of:
                continue
            category_of[video_id] = category
            order.append(video_id)

    fetched = fetch_videos(api_key, order)
    found = {v["id"] for v in fetched}
    missing = [v for v in order if v not in found]
    # 再生リストにはメンバー個人チャンネルの動画も入る。シクフォニのチャンネルに上がった動画に限る
    videos = [v for v in fetched if v["snippet"].get("channelId") == CHANNEL_ID]
    foreign = [v for v in fetched if v["snippet"].get("channelId") != CHANNEL_ID]
    return videos, category_of, per_playlist, missing, foreign


def audit(videos, category_of, per_playlist, missing, rows, foreign=()):
    """抽出はせず「どういう書式が何本あるか」だけを数える。ここを見て正規表現を直す。"""
    print()
    print("=" * 78)
    print("監査: 書式のばらつき")
    print("=" * 78)

    for category, ids in per_playlist.items():
        print(f"  {category:9s}: {len(ids)} 本")
    overlap = set(per_playlist["cover"]) & set(per_playlist["original"])
    print(f"  両方に登録: {len(overlap)} 本  {sorted(overlap) if overlap else ''}")
    if missing:
        print(f"  取得できず(削除/非公開): {len(missing)} 本  {missing}")
    print(f"  他チャンネルのため除外: {len(foreign)} 本 / 採用: {len(videos)} 本")
    for channel, count in collections.Counter(
        v["snippet"].get("channelTitle", "") for v in foreign
    ).most_common():
        print(f"    {count:4d}  {channel}")
    years = collections.Counter(r["投稿日"][:4] for r in rows)
    print("  投稿年: " + "  ".join(f"{y}={n}" for y, n in sorted(years.items())))

    labels = collections.Counter()
    honorific = collections.Counter()
    for video in videos:
        description = video["snippet"].get("description", "")
        for block in extract.parse_credit_blocks(description):
            labels[block["label"]] += 1
        for marker in ("※敬称略", "（敬称略）", "(敬称略)"):
            if marker in description:
                honorific[marker] += 1
        if "敬称略" not in description:
            honorific["なし"] += 1

    print()
    print("  ◆ラベルの出現数（上位40件・ここに綴り揺れが出る）")
    for label, count in labels.most_common(40):
        print(f"    {count:4d}  {label!r}")

    print()
    print("  「敬称略」の表記")
    for marker, count in honorific.most_common():
        print(f"    {count:4d}  {marker}")

    medleys = {r["video_id"] for r in rows if int(r["曲数"]) > 1}
    print()
    print(f"  メドレー（1曲1行に展開）: {len(medleys)} 本")
    unresolved = [r for r in rows if not r["曲名"]]
    print(f"  曲名が取れなかった動画: {len(unresolved)} 本")
    for row in unresolved:
        print(f"    {row['video_id']}  {row['タイトル']}")

    reasons = collections.Counter()
    for row in rows:
        for reason in filter(None, row["要確認理由"].split(" / ")):
            reasons[reason.split(":")[0]] += 1
    print()
    print(f"  要確認の行: {sum(1 for r in rows if r['要確認'])} / {len(rows)} 本")
    for reason, count in reasons.most_common():
        print(f"    {count:4d}  {reason}")


def row_key(row):
    """メドレーは1動画が複数行になるため、video_id だけでは行を区別できない。"""
    return (row["video_id"], str(row["曲順"]))


def load_existing(path):
    """前回のCSVがあれば読み込む。再実行しても行が重複しない。"""
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = [row for row in csv.DictReader(fh) if set(extract.ROW_FIELDS) <= set(row)]
    return {row_key(row): row for row in rows}


def write_csv(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=extract.ROW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="credits.csv", help="出力先CSV")
    parser.add_argument("--no-audit", action="store_true", help="監査統計を出さない")
    args = parser.parse_args()

    api_key = get_api_key()
    videos, category_of, per_playlist, missing, foreign = collect(api_key)

    merged = load_existing(args.out)
    # 以前の実行で入れた他チャンネルの行と、今回作り直す動画の古い行を消す
    stale = {v["id"] for v in foreign} | {v["id"] for v in videos}
    merged = {key: row for key, row in merged.items() if key[0] not in stale}
    for video in videos:
        for row in extract.build_rows(video, category_of[video["id"]]):
            merged[row_key(row)] = row

    # 新しい動画が上、同じ動画の中は曲順どおり（-曲順 と reverse で昇順にする）
    rows = sorted(merged.values(), key=lambda r: (r["投稿日"], r["video_id"], -int(r["曲順"])), reverse=True)
    write_csv(args.out, rows)
    print(f"{len(rows)} 行を {args.out} に書き出した（今回の取得: {len(videos)} 本）")

    if not args.no_audit:
        audit(videos, category_of, per_playlist, missing, rows, foreign)


if __name__ == "__main__":
    main()
