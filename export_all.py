"""シクフォニ本体とメンバー6人の楽曲を、1つのCSVにまとめて出す。

    python3 export_all.py --out /content/drive/MyDrive/sixfonia_all.csv

1行 = 1曲（メドレー・企画は動画の曲ごとに1行）。どのチャンネルのどの形式（動画/shorts）かは
`チャンネル` `形式` 列で分かる。元のデータ（列が違う4種類）は共通の列に揃える:

    シクフォニ  動画   カバー・オリジナル曲の再生リスト（◆クレジット付き）        データ元=楽曲
    シクフォニ  動画   日常・歌チャレンジ再生リストの ▼本家様                     データ元=本家様
    シクフォニ  shorts シクフォニ歌ってみた Shorts（曲名のみ）                    データ元=ショート
    暇72 雨乃こさめ いるま LAN すち みこと  動画 / shorts                          データ元=メンバー

`--split-dir DIR` を付けると、チャンネルごと・動画/ショートごとのCSV（と `_index.csv`）も DIR に出す。
APIキーは fetch_and_build.py と同じ（環境変数 YOUTUBE_API_KEY か Colab の Secrets）。
"""

import argparse
import csv
import os
import sys
import tempfile

import fetch_and_build as fb
import fetch_extra
import members

SIXFONIA = "シクフォニ"
COMBINED_NAME = "メンバー全員_まとめ.csv"
INDEX_NAME = "_index.csv"
INDEX_FIELDS = ["ファイル", "チャンネル", "種別", "内容", "行数", "動画数"]

SONGS_NAME = "シクフォニ_動画_楽曲.csv"
HONKE_NAME = "シクフォニ_動画_日常歌チャレンジ.csv"
SHORTS_NAME = "シクフォニ_shorts.csv"

# 形式
VIDEO = "動画"
SHORTS = "shorts"

# データ元
SOURCE_SONGS = "楽曲"
SOURCE_HONKE = "本家様"
SOURCE_SHORTS = "ショート"
SOURCE_MEMBER = "メンバー"

PLAYLIST_OF_CATEGORY = {"cover": "Cover Song Playlist", "original": "Original Song Playlist"}

# 1つのCSVの列。元データで列が違うものは、無い列を空にして揃える。
SINGLE_FIELDS = [
    "チャンネル",
    "形式",
    "曲名",
    "曲名の出所",
    "category",
    "歌ってる人",
    "歌唱者の出所",
    "歌唱者は推定",
    "作詞",
    "作曲",
    "絵",
    "動画",
    "原曲アーティスト",
    "投稿日",
    "動画タイトル",
    "再生リスト",
    "曲順",
    "曲数",
    "video_id",
    "動画URL",
    "データ元",
    "要確認",
    "要確認理由",
]


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def count_rows(path):
    """(行数, 動画数)。メドレー等で1動画が複数行になるため、動画数は video_id の種類で数える。"""
    rows = read_csv(path)
    return len(rows), len({r["video_id"] for r in rows})


def _blank():
    return dict.fromkeys(SINGLE_FIELDS, "")


# --------------------------------------------------------------------------
# 元データ → 共通の列
# --------------------------------------------------------------------------


def from_song_row(row):
    """シクフォニ本体の楽曲（fetch_and_build の行）。曲名はタイトルから取ったもの。"""
    out = _blank()
    out.update(
        チャンネル=SIXFONIA,
        形式=VIDEO,
        曲名=row["曲名"],
        曲名の出所="タイトル",
        category=row["category"],
        歌ってる人=row["歌ってる人"],
        歌唱者の出所="推定（全員）" if row["歌唱者は推定"] else "タイトル",
        歌唱者は推定=row["歌唱者は推定"],
        作詞=row["作詞"],
        作曲=row["作曲"],
        絵=row["絵"],
        動画=row["動画"],
        原曲アーティスト=row["原曲アーティスト"],
        投稿日=row["投稿日"],
        動画タイトル=row["タイトル"],
        再生リスト=PLAYLIST_OF_CATEGORY.get(row["category"], ""),
        曲順=row["曲順"],
        曲数=row["曲数"],
        video_id=row["video_id"],
        動画URL=row["動画URL"],
        データ元=SOURCE_SONGS,
        要確認=row["要確認"],
        要確認理由=row["要確認理由"],
    )
    return out


def from_honke_row(row):
    """日常・歌チャレンジの ▼本家様（fetch_extra.honke_song_rows の行）。曲名は本家様欄の表記のまま。"""
    out = _blank()
    out.update(
        チャンネル=SIXFONIA,
        形式=VIDEO,
        曲名=row["曲タイトル"],
        曲名の出所="本家様",
        投稿日=row["投稿日"],
        動画タイトル=row["動画タイトル"],
        再生リスト=row["再生リスト"],
        曲順=row["曲順"],
        曲数=row["曲数"],
        video_id=row["video_id"],
        動画URL=row["動画URL"],
        データ元=SOURCE_HONKE,
    )
    return out


def from_shorts_row(row):
    """シクフォニ歌ってみた Shorts（fetch_extra.shorts_row の行）。歌唱者は判定しない。"""
    out = _blank()
    out.update(
        チャンネル=SIXFONIA,
        形式=SHORTS,
        曲名=row["曲名"],
        曲名の出所=row["曲名の出所"],
        投稿日=row["投稿日"],
        動画タイトル=row["動画タイトル"],
        再生リスト="シクフォニ歌ってみた Shorts",
        曲順=1,
        曲数=1,
        video_id=row["video_id"],
        動画URL=row["動画URL"],
        データ元=SOURCE_SHORTS,
        要確認=row["要確認"],
        要確認理由=row["要確認理由"],
    )
    return out


def from_member_row(row):
    """メンバーのチャンネル（members.member_row の行）。ショート列が「はい」なら shorts。"""
    out = _blank()
    out.update(
        チャンネル=row["メンバー"],
        形式=SHORTS if row["ショート"] == "はい" else VIDEO,
        曲名=row["曲名"],
        曲名の出所=row["曲名の出所"],
        category=row["category"],
        歌ってる人=row["歌ってる人"],
        歌唱者の出所=row["歌唱者の出所"],
        絵=row["絵"],
        動画=row["動画"],
        投稿日=row["投稿日"],
        動画タイトル=row["動画タイトル"],
        再生リスト=row["再生リスト"],
        曲順=1,
        曲数=1,
        video_id=row["video_id"],
        動画URL=row["動画URL"],
        データ元=SOURCE_MEMBER,
        要確認=row["要確認"],
        要確認理由=row["要確認理由"],
    )
    return out


def sort_rows(rows):
    """シクフォニ→メンバー（MEMBER_SOURCES の順）、動画→shorts、新しい投稿日が上、同じ動画は曲順どおり。"""
    channels = [SIXFONIA] + list(fetch_extra.MEMBER_SOURCES)
    kinds = [VIDEO, SHORTS]
    rows = sorted(rows, key=lambda r: int(r["曲順"] or 0))
    rows.sort(key=lambda r: r["video_id"])
    rows.sort(key=lambda r: r["投稿日"], reverse=True)  # 安定ソートなので、上の並びは同じ日付の中で残る
    rows.sort(
        key=lambda r: (
            channels.index(r["チャンネル"]) if r["チャンネル"] in channels else len(channels),
            kinds.index(r["形式"]) if r["形式"] in kinds else len(kinds),
        )
    )
    return rows


# --------------------------------------------------------------------------
# 取得（既存のコマンドを、作業フォルダに書かせる）
# --------------------------------------------------------------------------


def export_sixfonia(work_dir, no_audit):
    """シクフォニ本体。3ファイルを書き、(パス, チャンネル, 種別, 内容) を返す。"""
    entries = []

    songs = os.path.join(work_dir, SONGS_NAME)
    # fetch_and_build は argv を読む。前回の CSV があれば統合される。
    original_argv = sys.argv
    sys.argv = ["fetch_and_build.py", "--out", songs] + (["--no-audit"] if no_audit else [])
    try:
        fb.main()
    finally:
        sys.argv = original_argv
    entries.append((songs, SIXFONIA, VIDEO, "カバー・オリジナル曲の再生リスト（メドレーは1曲1行）"))

    honke = os.path.join(work_dir, HONKE_NAME)
    fetch_extra.run_honke(argparse.Namespace(out=honke, videos_out=None, no_audit=no_audit))
    entries.append((honke, SIXFONIA, VIDEO, "日常・歌チャレンジ再生リストの ▼本家様（1曲1行）"))

    shorts = os.path.join(work_dir, SHORTS_NAME)
    fetch_extra.run_shorts(argparse.Namespace(out=shorts, no_audit=no_audit))
    entries.append((shorts, SIXFONIA, SHORTS, "シクフォニ歌ってみた Shorts（曲名のみ）"))
    return entries


def split_member_rows(rows, member):
    """メンバー1人の行を (動画, ショート) に分ける。ショート列が「はい」のものがショート。"""
    mine = [r for r in rows if r["メンバー"] == member]
    return [r for r in mine if r["ショート"] != "はい"], [r for r in mine if r["ショート"] == "はい"]


def export_members(work_dir, no_audit, uploads_limit, shorts_limit):
    """メンバー6人。まとめの CSV を書き、人ごと・動画/ショートごとに分けて返す。"""
    combined = os.path.join(work_dir, COMBINED_NAME)
    fetch_extra.run_member_songs(
        argparse.Namespace(out=combined, uploads_limit=uploads_limit, shorts_limit=shorts_limit, no_audit=no_audit)
    )
    rows = read_csv(combined)

    entries = []
    for member in fetch_extra.MEMBER_SOURCES:
        videos, shorts = split_member_rows(rows, member)
        for label, subset, note in (
            (VIDEO, videos, "再生リストの動画（いるま・みことは配信以外のアップロード全体）"),
            (SHORTS, shorts, "ショート（再生リスト内と、再生リストに入っていないもの）"),
        ):
            path = os.path.join(work_dir, f"{member}_{label}.csv")
            fetch_extra.write_csv(path, members.MEMBER_FIELDS, subset)
            entries.append((path, member, label, note))
    return entries, combined


# --------------------------------------------------------------------------
# 1つのCSV・分割・一覧
# --------------------------------------------------------------------------


def build_single_rows(work_dir, only=None):
    """作業フォルダに書かれた元のCSVを読み、共通の列に揃えた行を返す。"""
    rows = []
    if only != "members":
        rows += [from_song_row(r) for r in read_csv(os.path.join(work_dir, SONGS_NAME))]
        rows += [from_honke_row(r) for r in read_csv(os.path.join(work_dir, HONKE_NAME))]
        rows += [from_shorts_row(r) for r in read_csv(os.path.join(work_dir, SHORTS_NAME))]
    if only != "sixfonia":
        rows += [from_member_row(r) for r in read_csv(os.path.join(work_dir, COMBINED_NAME))]
    return sort_rows(rows)


def write_index(out_dir, entries):
    """ファイルごとの行数・動画数を、書き出したCSVを読み直して数える。"""
    index = []
    for path, channel, kind, note in entries:
        rows, videos = count_rows(path)
        index.append(
            {
                "ファイル": os.path.basename(path),
                "チャンネル": channel,
                "種別": kind,
                "内容": note,
                "行数": rows,
                "動画数": videos,
            }
        )
    fetch_extra.write_csv(os.path.join(out_dir, INDEX_NAME), INDEX_FIELDS, index)
    return index


def print_summary(rows, out_path):
    """チャンネル × 形式ごとの行数と動画数。"""
    print()
    print("=" * 78)
    print(f"出力: {out_path}   {len(rows)} 行 / {len({r['video_id'] for r in rows})} 本")
    print("=" * 78)
    groups = {}
    for row in rows:
        groups.setdefault((row["チャンネル"], row["形式"], row["データ元"]), []).append(row)
    for (channel, kind, source), subset in groups.items():
        videos = len({r["video_id"] for r in subset})
        flagged = sum(1 for r in subset if r["要確認"])
        print(f"  {channel:<8s} {kind:<7s} {source:<6s} {len(subset):>5} 行 / {videos:>4} 本   要確認 {flagged}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="出力する1つのCSV")
    parser.add_argument("--split-dir", help="チャンネルごと・動画/ショートごとのCSVと _index.csv も出すフォルダ（任意）")
    parser.add_argument("--only", choices=["sixfonia", "members"], help="片方だけ出す")
    parser.add_argument("--no-audit", action="store_true", help="監査統計を出さない")
    parser.add_argument("--uploads-limit", type=int, default=300, help="いるま・みことのアップロードを新しい順に見る本数")
    parser.add_argument("--shorts-limit", type=int, default=500, help="再生リスト外のショートを新しい順に見る本数")
    args = parser.parse_args()

    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)

    # 分割を頼まれなければ、元のCSVは一時フォルダに置いて消す
    temp = None if args.split_dir else tempfile.TemporaryDirectory()
    work_dir = args.split_dir or temp.name
    os.makedirs(work_dir, exist_ok=True)
    try:
        entries = []
        if args.only != "members":
            entries += export_sixfonia(work_dir, args.no_audit)
        if args.only != "sixfonia":
            member_entries, _ = export_members(work_dir, args.no_audit, args.uploads_limit, args.shorts_limit)
            entries += member_entries

        rows = build_single_rows(work_dir, args.only)
        fetch_extra.write_csv(args.out, SINGLE_FIELDS, rows)
        print_summary(rows, args.out)
        if args.split_dir:
            write_index(args.split_dir, entries)
            print(f"チャンネルごとのCSVと {INDEX_NAME} を {args.split_dir} に出した")
    finally:
        if temp:
            temp.cleanup()


if __name__ == "__main__":
    main()
