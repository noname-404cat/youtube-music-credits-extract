"""export_all.py のテスト。取得は疑似関数に差し替え、ネットワークには触らない。

    python3 test_export_all.py
"""

import csv
import io
import os
import sys
import tempfile
from contextlib import redirect_stdout

import export_all
import fetch_and_build as fb
import fetch_extra
import members


def member_row(member, video_id, short, song="曲"):
    row = dict.fromkeys(members.MEMBER_FIELDS, "")
    row.update(メンバー=member, 曲名=song, video_id=video_id, ショート="はい" if short else "")
    return row


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def run_export(rows_by_member, argv_extra=()):
    """取得の3つの入り口を、決まった内容を書くだけの関数に差し替えて export_all.main を動かす。"""
    calls = []

    def fake_credits():
        out = sys.argv[sys.argv.index("--out") + 1]
        calls.append(("credits", out, "--no-audit" in sys.argv))
        rows = [dict.fromkeys(["曲名", "video_id"], "x")]
        rows[0]["video_id"] = "c1"
        fetch_extra.write_csv(out, ["曲名", "video_id"], rows)

    def fake_honke(args):
        calls.append(("honke", args.out, args.no_audit))
        fetch_extra.write_csv(args.out, ["曲タイトル", "video_id"], [{"曲タイトル": "a", "video_id": "h1"}, {"曲タイトル": "b", "video_id": "h1"}])

    def fake_shorts(args):
        calls.append(("shorts", args.out, args.no_audit))
        fetch_extra.write_csv(args.out, ["曲名", "video_id"], [{"曲名": "s", "video_id": "sh1"}])

    def fake_members(args):
        calls.append(("members", args.out, args.uploads_limit, args.shorts_limit, args.no_audit))
        rows = [r for rs in rows_by_member.values() for r in rs]
        fetch_extra.write_csv(args.out, members.MEMBER_FIELDS, rows)

    originals = (fb.main, fetch_extra.run_honke, fetch_extra.run_shorts, fetch_extra.run_member_songs, sys.argv)
    fb.main, fetch_extra.run_honke, fetch_extra.run_shorts, fetch_extra.run_member_songs = (
        fake_credits,
        fake_honke,
        fake_shorts,
        fake_members,
    )
    tmp = tempfile.TemporaryDirectory()
    out_dir = os.path.join(tmp.name, "nested", "out")
    sys.argv = ["export_all.py", "--out-dir", out_dir, *argv_extra]
    printed = io.StringIO()
    try:
        with redirect_stdout(printed):
            export_all.main()
    finally:
        fb.main, fetch_extra.run_honke, fetch_extra.run_shorts, fetch_extra.run_member_songs, sys.argv = originals
    return tmp, out_dir, calls, printed.getvalue()


def test_split_member_rows_separates_videos_and_shorts():
    rows = [member_row("すち", "v1", False), member_row("すち", "s1", True), member_row("LAN", "v2", False)]
    videos, shorts = export_all.split_member_rows(rows, "すち")
    assert [r["video_id"] for r in videos] == ["v1"]
    assert [r["video_id"] for r in shorts] == ["s1"]


def test_export_writes_a_file_per_channel_and_kind():
    rows = {
        "暇72": [member_row("暇72", "a1", False), member_row("暇72", "a2", True), member_row("暇72", "a3", True)],
        "すち": [member_row("すち", "b1", False)],
    }
    tmp, out_dir, calls, text = run_export(rows)
    with tmp:
        names = sorted(os.listdir(out_dir))
        expected = {"シクフォニ_動画_楽曲.csv", "シクフォニ_動画_日常歌チャレンジ.csv", "シクフォニ_shorts.csv", "メンバー全員_まとめ.csv", "_index.csv"}
        expected |= {f"{m}_{k}.csv" for m in fetch_extra.MEMBER_SOURCES for k in ("動画", "shorts")}
        assert set(names) == expected, set(names) ^ expected
        assert [r["video_id"] for r in read(os.path.join(out_dir, "暇72_動画.csv"))] == ["a1"]
        assert [r["video_id"] for r in read(os.path.join(out_dir, "暇72_shorts.csv"))] == ["a2", "a3"]
        assert [r["video_id"] for r in read(os.path.join(out_dir, "すち_shorts.csv"))] == []
        assert "暇72_動画.csv" in text and "出力:" in text


def test_files_with_no_rows_still_have_the_header():
    """メンバーの動画が0本でも、ファイルは作り、列名は残す（後段の取り込みが壊れない）。"""
    tmp, out_dir, _, _ = run_export({})
    with tmp:
        with open(os.path.join(out_dir, "みこと_shorts.csv"), encoding="utf-8-sig", newline="") as fh:
            assert next(csv.reader(fh)) == members.MEMBER_FIELDS


def test_index_counts_rows_and_distinct_videos():
    tmp, out_dir, _, _ = run_export({"暇72": [member_row("暇72", "a1", False)]})
    with tmp:
        index = {r["ファイル"]: r for r in read(os.path.join(out_dir, "_index.csv"))}
        honke = index["シクフォニ_動画_日常歌チャレンジ.csv"]
        assert (honke["行数"], honke["動画数"]) == ("2", "1"), "1動画が複数行になるので、行数と動画数は別に数える"
        assert index["暇72_動画.csv"]["行数"] == "1"
        assert index["暇72_shorts.csv"]["行数"] == "0"
        assert index["シクフォニ_shorts.csv"]["種別"] == "shorts"
        assert len(index) == 3 + 6 * 2


def test_options_reach_every_step():
    tmp, out_dir, calls, _ = run_export({}, ["--no-audit", "--uploads-limit", "50", "--shorts-limit", "70"])
    with tmp:
        by_name = {c[0]: c for c in calls}
        assert by_name["credits"][2] is True and by_name["honke"][2] is True and by_name["shorts"][2] is True
        assert by_name["members"][2:] == (50, 70, True)


def test_only_sixfonia_or_only_members():
    tmp, out_dir, calls, _ = run_export({}, ["--only", "sixfonia"])
    with tmp:
        assert [c[0] for c in calls] == ["credits", "honke", "shorts"]
        assert not os.path.exists(os.path.join(out_dir, "暇72_動画.csv"))
    tmp, out_dir, calls, _ = run_export({}, ["--only", "members"])
    with tmp:
        assert [c[0] for c in calls] == ["members"]
        assert not os.path.exists(os.path.join(out_dir, "シクフォニ_shorts.csv"))


def test_argv_is_restored_after_the_credits_step():
    """fetch_and_build.main は argv を読むので差し替える。あとで元に戻さないと次の処理が壊れる。"""
    before = list(sys.argv)
    run_export({})[0].cleanup()
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
