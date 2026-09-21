"""各チャンネル × 動画/ショートのCSVを、1つのフォルダにまとめて出す。

    python3 export_all.py --out-dir /content/drive/MyDrive/sixfonia_export

出力（チャンネル7 × 種別）:

    シクフォニ_動画_楽曲.csv           カバー・オリジナル曲の再生リスト（◆クレジット付き。メドレーは1曲1行）
    シクフォニ_動画_日常歌チャレンジ.csv   日常・歌チャレンジ再生リストの ▼本家様（1曲1行）
    シクフォニ_shorts.csv              シクフォニ歌ってみた Shorts（曲名のみ）
    暇72_動画.csv / 暇72_shorts.csv     （雨乃こさめ・いるま・LAN・すち・みこと も同じ）
    メンバー全員_まとめ.csv             メンバー6人の動画とショートをまとめたもの（分割前）
    _index.csv                        ファイルごとの内容・行数・動画数

APIキーは fetch_and_build.py と同じ（環境変数 YOUTUBE_API_KEY か Colab の Secrets）。
"""

import argparse
import csv
import os
import sys

import fetch_and_build as fb
import fetch_extra
import members

SIXFONIA = "シクフォニ"
COMBINED_NAME = "メンバー全員_まとめ.csv"
INDEX_NAME = "_index.csv"
INDEX_FIELDS = ["ファイル", "チャンネル", "種別", "内容", "行数", "動画数"]


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def count_rows(path):
    """(行数, 動画数)。メドレー等で1動画が複数行になるため、動画数は video_id の種類で数える。"""
    rows = read_csv(path)
    return len(rows), len({r["video_id"] for r in rows})


def split_member_rows(rows, member):
    """メンバー1人の行を (動画, ショート) に分ける。ショート列が「はい」のものがショート。"""
    mine = [r for r in rows if r["メンバー"] == member]
    return [r for r in mine if r["ショート"] != "はい"], [r for r in mine if r["ショート"] == "はい"]


def export_sixfonia(out_dir, no_audit):
    """シクフォニ本体。3ファイルを書き、(パス, チャンネル, 種別, 内容) を返す。"""
    entries = []

    songs = os.path.join(out_dir, "シクフォニ_動画_楽曲.csv")
    # fetch_and_build は argv を読む。前回の CSV があれば統合される。
    original_argv = sys.argv
    sys.argv = ["fetch_and_build.py", "--out", songs] + (["--no-audit"] if no_audit else [])
    try:
        fb.main()
    finally:
        sys.argv = original_argv
    entries.append((songs, SIXFONIA, "動画", "カバー・オリジナル曲の再生リスト（メドレーは1曲1行）"))

    honke = os.path.join(out_dir, "シクフォニ_動画_日常歌チャレンジ.csv")
    fetch_extra.run_honke(argparse.Namespace(out=honke, videos_out=None, no_audit=no_audit))
    entries.append((honke, SIXFONIA, "動画", "日常・歌チャレンジ再生リストの ▼本家様（1曲1行）"))

    shorts = os.path.join(out_dir, "シクフォニ_shorts.csv")
    fetch_extra.run_shorts(argparse.Namespace(out=shorts, no_audit=no_audit))
    entries.append((shorts, SIXFONIA, "shorts", "シクフォニ歌ってみた Shorts（曲名のみ）"))
    return entries


def export_members(out_dir, no_audit, uploads_limit, shorts_limit):
    """メンバー6人。まとめの CSV を書き、人ごと・動画/ショートごとに分けて返す。"""
    combined = os.path.join(out_dir, COMBINED_NAME)
    fetch_extra.run_member_songs(
        argparse.Namespace(out=combined, uploads_limit=uploads_limit, shorts_limit=shorts_limit, no_audit=no_audit)
    )
    rows = read_csv(combined)

    entries = []
    for member in fetch_extra.MEMBER_SOURCES:
        videos, shorts = split_member_rows(rows, member)
        for label, subset, note in (
            ("動画", videos, "再生リストの動画（いるま・みことは配信以外のアップロード全体）"),
            ("shorts", shorts, "ショート（再生リスト内と、再生リストに入っていないもの）"),
        ):
            path = os.path.join(out_dir, f"{member}_{label}.csv")
            fetch_extra.write_csv(path, members.MEMBER_FIELDS, subset)
            entries.append((path, member, label, note))
    return entries, combined


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


def print_index(index, out_dir):
    print()
    print("=" * 78)
    print(f"出力: {out_dir}")
    print("=" * 78)
    for row in index:
        print(f"  {row['ファイル']:<32s} {row['行数']:>6} 行 / {row['動画数']:>5} 本   {row['内容']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True, help="出力先のフォルダ（無ければ作る）")
    parser.add_argument("--only", choices=["sixfonia", "members"], help="片方だけ出す")
    parser.add_argument("--no-audit", action="store_true", help="監査統計を出さない")
    parser.add_argument("--uploads-limit", type=int, default=300, help="いるま・みことのアップロードを新しい順に見る本数")
    parser.add_argument("--shorts-limit", type=int, default=500, help="再生リスト外のショートを新しい順に見る本数")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    entries = []
    if args.only != "members":
        entries += export_sixfonia(args.out_dir, args.no_audit)
    if args.only != "sixfonia":
        member_entries, _ = export_members(args.out_dir, args.no_audit, args.uploads_limit, args.shorts_limit)
        entries += member_entries

    print_index(write_index(args.out_dir, entries), args.out_dir)


if __name__ == "__main__":
    main()
