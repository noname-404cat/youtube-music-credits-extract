"""export_all.py のテスト。取得は疑似関数に差し替え、ネットワークには触らない。

変換元の行は、実際の関数（extract.build_rows / members.member_row など）が作る行を使う。
列名が食い違ったら、ここで KeyError になって分かる。

    python3 test_export_all.py
"""

import csv
import io
import os
import sys
import tempfile
from contextlib import redirect_stdout

import export_all
import extract
import fetch_and_build as fb
import fetch_extra
import fixtures
import members
from test_fetch_extra import make_video


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


# --- 実際の関数が作る行 ------------------------------------------------------


def real_song_rows():
    return extract.build_rows(fixtures.COVER_ANISON_MEDLEY, "cover") + extract.build_rows(fixtures.ORIGINAL_SIX_NATION, "original")


def real_honke_rows():
    return fetch_extra.honke_song_rows(fixtures.COVER_ANISON_MEDLEY, "日常")


def real_shorts_row():
    video = make_video("sh1", "夏の終わりにノスタルジックな曲を貴方へ【少女レイ】", "#shorts #歌ってみた #少女レイ", published="2026-08-31T10:00:00Z")
    video["statistics"] = {"viewCount": "1"}
    return fetch_extra.shorts_row(video)


def real_member_rows():
    long_video = make_video("l1", "AIZO／暇72 【Cover】", "Movie：LAN", published="2026-03-21T10:00:00Z")
    long_video["contentDetails"] = {"duration": "PT4M"}
    short_video = make_video("s1", "ヤラララを歌ってみた #ヤラララ #歌ってみた", "", published="2026-08-11T10:00:00Z")
    return [
        members.member_row(long_video, "暇72", "Covered by 暇72"),
        members.member_row(short_video, "LAN", None),
    ]


# --- 共通の列への変換 --------------------------------------------------------


def test_every_conversion_produces_exactly_the_single_columns():
    converted = (
        [export_all.from_song_row(r) for r in real_song_rows()]
        + [export_all.from_honke_row(r) for r in real_honke_rows()]
        + [export_all.from_shorts_row(real_shorts_row())]
        + [export_all.from_member_row(r) for r in real_member_rows()]
    )
    for row in converted:
        assert list(row) == export_all.SINGLE_FIELDS, list(row)


def test_song_rows_keep_credits_and_get_the_playlist_from_the_category():
    rows = [export_all.from_song_row(r) for r in extract.build_rows(fixtures.ORIGINAL_SIX_NATION, "original")]
    row = rows[0]
    assert (row["チャンネル"], row["形式"], row["データ元"]) == ("シクフォニ", "動画", "楽曲")
    assert row["作詞"] == "ケンカイヨシ" and row["再生リスト"] == "Original Song Playlist"
    assert row["動画タイトル"] == fixtures.ORIGINAL_SIX_NATION["snippet"]["title"].replace("‍", "")
    assert row["歌唱者は推定"] == "推定" and row["歌唱者の出所"] == "推定（全員）"


def test_medley_becomes_one_row_per_song_in_the_single_csv():
    rows = [export_all.from_song_row(r) for r in extract.build_rows(fixtures.COVER_ANISON_MEDLEY, "cover")]
    assert len(rows) == 6
    assert [r["曲順"] for r in rows] == [1, 2, 3, 4, 5, 6]
    assert {r["曲数"] for r in rows} == {6}


def test_honke_rows_use_the_honke_text_as_the_song_name():
    row = export_all.from_honke_row(real_honke_rows()[0])
    assert row["曲名"] == "TVアニメ「ONE PIECE」1000話記念：ウィーアー！"
    assert (row["曲名の出所"], row["データ元"], row["再生リスト"]) == ("本家様", "本家様", "日常")
    assert row["歌ってる人"] == "", "本家様の行では歌唱者を判定しない"


def test_shorts_rows_have_the_shorts_kind_and_no_singer():
    row = export_all.from_shorts_row(real_shorts_row())
    assert (row["チャンネル"], row["形式"], row["曲名"]) == ("シクフォニ", "shorts", "少女レイ")
    assert row["歌ってる人"] == ""


def test_member_rows_are_split_into_video_and_shorts_by_the_short_column():
    long_row, short_row = [export_all.from_member_row(r) for r in real_member_rows()]
    assert (long_row["チャンネル"], long_row["形式"], long_row["曲名"], long_row["動画"]) == ("暇72", "動画", "AIZO", "LAN")
    assert (short_row["チャンネル"], short_row["形式"], short_row["曲名"]) == ("LAN", "shorts", "ヤラララ")


# --- 並び --------------------------------------------------------------------


def _row(channel, kind, date, video_id, order=1):
    row = export_all._blank()
    row.update(チャンネル=channel, 形式=kind, 投稿日=date, video_id=video_id, 曲順=order, 曲数=1)
    return row


def test_rows_are_ordered_by_channel_kind_newest_first_and_song_order():
    rows = [
        _row("LAN", "shorts", "2026-01-01", "a"),
        _row("シクフォニ", "shorts", "2026-01-01", "b"),
        _row("シクフォニ", "動画", "2026-01-01", "old"),
        _row("シクフォニ", "動画", "2026-02-01", "new", 2),
        _row("シクフォニ", "動画", "2026-02-01", "new", 1),
        _row("暇72", "動画", "2026-01-01", "c"),
    ]
    ordered = export_all.sort_rows(rows)
    assert [(r["チャンネル"], r["形式"], r["video_id"], r["曲順"]) for r in ordered] == [
        ("シクフォニ", "動画", "new", 1),
        ("シクフォニ", "動画", "new", 2),
        ("シクフォニ", "動画", "old", 1),
        ("シクフォニ", "shorts", "b", 1),
        ("暇72", "動画", "c", 1),
        ("LAN", "shorts", "a", 1),
    ]


# --- 実行 --------------------------------------------------------------------


def run_export(argv_extra=()):
    """取得の入り口を、実際の関数が作る行を書くだけの関数に差し替えて export_all.main を動かす。"""
    calls = []

    def fake_credits():
        out = sys.argv[sys.argv.index("--out") + 1]
        calls.append(("credits", out, "--no-audit" in sys.argv))
        fetch_extra.write_csv(out, extract.ROW_FIELDS, real_song_rows())

    def fake_honke(args):
        calls.append(("honke", args.out, args.no_audit))
        fetch_extra.write_csv(args.out, fetch_extra.SONG_FIELDS, real_honke_rows())

    def fake_shorts(args):
        calls.append(("shorts", args.out, args.no_audit))
        fetch_extra.write_csv(args.out, fetch_extra.SHORTS_FIELDS, [real_shorts_row()])

    def fake_members(args):
        calls.append(("members", args.out, args.uploads_limit, args.shorts_limit, args.no_audit))
        fetch_extra.write_csv(args.out, members.MEMBER_FIELDS, real_member_rows())

    originals = (fb.main, fetch_extra.run_honke, fetch_extra.run_shorts, fetch_extra.run_member_songs, sys.argv)
    fb.main, fetch_extra.run_honke, fetch_extra.run_shorts, fetch_extra.run_member_songs = (
        fake_credits,
        fake_honke,
        fake_shorts,
        fake_members,
    )
    tmp = tempfile.TemporaryDirectory()
    out = os.path.join(tmp.name, "nested", "sixfonia_all.csv")
    sys.argv = ["export_all.py", "--out", out, *argv_extra]
    printed = io.StringIO()
    try:
        with redirect_stdout(printed):
            export_all.main()
    finally:
        fb.main, fetch_extra.run_honke, fetch_extra.run_shorts, fetch_extra.run_member_songs, sys.argv = originals
    return tmp, out, calls, printed.getvalue()


def test_export_writes_one_csv_with_every_channel_and_kind():
    tmp, out, calls, text = run_export()
    with tmp:
        assert os.listdir(os.path.dirname(out)) == ["sixfonia_all.csv"], "元のCSVは残さない"
        with open(out, encoding="utf-8-sig", newline="") as fh:
            assert next(csv.reader(fh)) == export_all.SINGLE_FIELDS
        rows = read(out)
        kinds = {(r["チャンネル"], r["形式"], r["データ元"]) for r in rows}
        assert kinds == {
            ("シクフォニ", "動画", "楽曲"),
            ("シクフォニ", "動画", "本家様"),
            ("シクフォニ", "shorts", "ショート"),
            ("暇72", "動画", "メンバー"),
            ("LAN", "shorts", "メンバー"),
        }, kinds
        expected = len(real_song_rows()) + len(real_honke_rows()) + 1 + len(real_member_rows())
        assert len(rows) == expected
        assert "出力:" in text and "シクフォニ" in text


def test_split_dir_also_writes_per_channel_files_and_the_index():
    with tempfile.TemporaryDirectory() as split:
        tmp, out, _, _ = run_export(["--split-dir", split])
        with tmp:
            names = set(os.listdir(split))
            expected = {export_all.SONGS_NAME, export_all.HONKE_NAME, export_all.SHORTS_NAME, export_all.COMBINED_NAME, export_all.INDEX_NAME}
            expected |= {f"{m}_{k}.csv" for m in fetch_extra.MEMBER_SOURCES for k in ("動画", "shorts")}
            assert names == expected, names ^ expected
            index = {r["ファイル"]: r for r in read(os.path.join(split, export_all.INDEX_NAME))}
            assert index["暇72_動画.csv"]["行数"] == "1" and index["LAN_shorts.csv"]["行数"] == "1"
            assert index["みこと_shorts.csv"]["行数"] == "0"
            assert len(read(out)) > 0


def test_options_reach_every_step():
    tmp, out, calls, _ = run_export(["--no-audit", "--uploads-limit", "50", "--shorts-limit", "70"])
    with tmp:
        by_name = {c[0]: c for c in calls}
        assert by_name["credits"][2] is True and by_name["honke"][2] is True and by_name["shorts"][2] is True
        assert by_name["members"][2:] == (50, 70, True)


def test_only_sixfonia_or_only_members():
    tmp, out, calls, _ = run_export(["--only", "sixfonia"])
    with tmp:
        assert [c[0] for c in calls] == ["credits", "honke", "shorts"]
        assert {r["データ元"] for r in read(out)} == {"楽曲", "本家様", "ショート"}
    tmp, out, calls, _ = run_export(["--only", "members"])
    with tmp:
        assert [c[0] for c in calls] == ["members"]
        assert {r["データ元"] for r in read(out)} == {"メンバー"}


def test_argv_is_restored_after_the_credits_step():
    """fetch_and_build.main は argv を読むので差し替える。あとで元に戻さないと次の処理が壊れる。"""
    before = list(sys.argv)
    run_export()[0].cleanup()
    assert sys.argv == before


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  ok   {name}")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL {name}: {exc}")
    print()
    print("失敗なし" if not failures else f"{failures} 件失敗")
    raise SystemExit(1 if failures else 0)
