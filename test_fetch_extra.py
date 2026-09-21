"""fetch_extra.py のテスト。APIは疑似関数に差し替え、ネットワークには触らない。

    python3 test_fetch_extra.py
"""

import io
from contextlib import redirect_stdout

import fetch_and_build as fb
import fetch_extra
import fixtures

OTHER_CHANNEL = "UCother"


def make_video(video_id, title, description, channel_id=None, published="2026-01-02T03:00:00Z", **extra):
    snippet = {
        "title": title,
        "description": description,
        "publishedAt": published,
        "channelId": channel_id or fb.CHANNEL_ID,
        "channelTitle": "シクフォニ【SIXFONIA】",
    }
    snippet.update(extra)
    return {"id": video_id, "snippet": snippet, "contentDetails": {"duration": "PT45S"}}


HONKE_DESCRIPTION = """歌ってみた

▼本家様
Ado「新時代」
https://youtu.be/xxxx

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆Mix
誰か

※敬称略
"""


def fake_api(playlists, videos):
    """playlists: {playlistId: [videoId]}, videos: {videoId: video}"""

    def api_get(api_key, path, **params):
        if path == "playlistItems":
            ids = playlists[params["playlistId"]]
            return {"items": [{"contentDetails": {"videoId": v}} for v in ids]}
        if path == "videos":
            return {"items": [videos[v] for v in params["id"].split(",") if v in videos]}
        raise AssertionError(path)

    return api_get


def test_has_honke_detects_the_mark():
    assert fetch_extra.has_honke(make_video("a", "t", HONKE_DESCRIPTION))
    assert not fetch_extra.has_honke(make_video("b", "t", "歌ってみた\n※敬称略"))


def test_honke_row_collects_song_title_video_title_and_date():
    row = fetch_extra.honke_row(make_video("a", "【歌ってみた】新時代", HONKE_DESCRIPTION), "歌チャレンジ")
    assert row["曲タイトル"] == "Ado「新時代」", row["曲タイトル"]
    assert row["曲数"] == 1
    assert row["動画タイトル"] == "【歌ってみた】新時代"
    assert row["投稿日"] == "2026-01-02"
    assert row["再生リスト"] == "歌チャレンジ"
    assert row["動画URL"] == "https://youtu.be/a"


def test_honke_row_lists_every_song_of_a_medley():
    row = fetch_extra.honke_row(fixtures.COVER_ANISON_MEDLEY, "日常")
    assert row["曲数"] == 6
    assert row["曲タイトル"].split(" | ")[0] == "TVアニメ「ONE PIECE」1000話記念：ウィーアー！"


def test_honke_song_rows_are_one_song_per_row_in_order():
    rows = fetch_extra.honke_song_rows(fixtures.COVER_ANISON_MEDLEY, "日常")
    assert len(rows) == 6
    assert [r["曲順"] for r in rows] == [1, 2, 3, 4, 5, 6]
    assert {r["曲数"] for r in rows} == {6}
    assert rows[0]["曲タイトル"] == "TVアニメ「ONE PIECE」1000話記念：ウィーアー！"
    assert {r["video_id"] for r in rows} == {"JaFgv0Ovz8A"}
    assert list(rows[0]) == fetch_extra.SONG_FIELDS


def test_honke_song_rows_keep_song_titles_that_contain_the_joiner():
    """曲タイトルに ` | ` があっても、行を分けたあとなので壊れない（結合して再分割しない）。"""
    video = make_video("a", "t", "▼本家様\nA | B\nhttps://youtu.be/x\n\n" + "┄" * 10)
    rows = fetch_extra.honke_song_rows(video, "日常")
    assert [r["曲タイトル"] for r in rows] == ["A | B"]


def test_run_honke_writes_one_row_per_song_newest_first():
    import csv
    import os
    import sys
    import tempfile

    ids = fetch_extra.HONKE_PLAYLISTS
    old = make_video("old", "古い", HONKE_DESCRIPTION, published="2025-01-01T00:00:00Z")
    new_description = "▼本家様\nX\nhttps://youtu.be/1\n\nY\nhttps://youtu.be/2\n\n" + "┄" * 10
    new = make_video("new", "新しい", new_description, published="2026-01-01T00:00:00Z")
    original_api, original_key, original_argv = fb.api_get, fb.get_api_key, sys.argv
    fb.api_get = fake_api({ids["日常"]: ["old", "new"], ids["歌チャレンジ"]: []}, {"old": old, "new": new})
    fb.get_api_key = lambda: "key"
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "honke.csv")
        sys.argv = ["fetch_extra.py", "honke", "--out", out, "--no-audit"]
        try:
            with redirect_stdout(io.StringIO()):
                fetch_extra.main()
        finally:
            fb.api_get, fb.get_api_key, sys.argv = original_api, original_key, original_argv
        with open(out, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
    assert [(r["video_id"], r["曲順"], r["曲タイトル"]) for r in rows] == [
        ("new", "1", "X"),
        ("new", "2", "Y"),
        ("old", "1", "Ado「新時代」"),
    ], rows


def test_collect_honke_skips_other_channels_and_keeps_first_playlist_on_duplicates():
    ids = fetch_extra.HONKE_PLAYLISTS
    videos = {
        "mine": make_video("mine", "自分", HONKE_DESCRIPTION),
        "dup": make_video("dup", "重複", HONKE_DESCRIPTION),
        "other": make_video("other", "他", HONKE_DESCRIPTION, channel_id=OTHER_CHANNEL),
    }
    playlists = {ids["日常"]: ["mine", "dup"], ids["歌チャレンジ"]: ["dup", "other", "gone"]}
    original = fb.api_get
    fb.api_get = fake_api(playlists, videos)
    try:
        playlist_of, per_playlist, mine, foreign, missing = fetch_extra.collect_honke("key")
    finally:
        fb.api_get = original
    assert playlist_of["dup"] == "日常"
    assert sorted(v["id"] for v in mine) == ["dup", "mine"]
    assert [v["id"] for v in foreign] == ["other"]
    assert missing == ["gone"]


def test_audit_honke_runs_and_reports_unresolved_marks():
    marked_but_empty = make_video("empty", "曲名なし", "本家様は以下\n※敬称略")
    rows = [fetch_extra.honke_row(marked_but_empty, "日常")]
    out = io.StringIO()
    with redirect_stdout(out):
        fetch_extra.audit_honke(
            {"日常": ["empty"]}, {"empty": "日常"}, [marked_but_empty], [], [], rows
        )
    text = out.getvalue()
    assert "曲タイトルが取れなかった動画: 1 本" in text, text
    assert "empty" in text


def test_parse_duration():
    assert fetch_extra.parse_duration("PT45S") == 45
    assert fetch_extra.parse_duration("PT1M30S") == 90
    assert fetch_extra.parse_duration("PT1H2M3S") == 3723
    assert fetch_extra.parse_duration("P0D") is None
    assert fetch_extra.parse_duration(None) is None


def test_shorts_song_takes_the_title_bracket():
    """実データの例。曲名は末尾の【】に入る。"""
    assert fetch_extra.shorts_song("夏の終わりにノスタルジックな曲を貴方へ【少女レイ】") == ("少女レイ", None)
    assert fetch_extra.shorts_song("出すとこ出して歌ってみた【HOT LIMIT】") == ("HOT LIMIT", None)
    assert fetch_extra.shorts_song("ジョーカーじゃ足りない!【SiX N4TioN】") == ("SiX N4TioN", None)


def test_shorts_song_ignores_brackets_that_are_not_songs():
    """【3D】【アニメ】【シクフォニ×…】は曲名ではない。"""
    song, note = fetch_extra.shorts_song("ルールを守って剣と盾チャレンジ【3D】")
    assert song is None and "曲名が無い" in note
    song, note = fetch_extra.shorts_song("ラストが神すぎる絵しりとり【シクフォニ×ハンドレッドノート】")
    assert song is None, song
    song, note = fetch_extra.shorts_song("【アニメ】オタクくん～見てる？電話に...【漫画】")
    assert song is None, song


def test_shorts_song_flags_a_title_with_two_candidates():
    song, note = fetch_extra.shorts_song("【青と夏】を歌ったあとに【夏祭り】")
    assert song == "夏祭り"
    assert "【】が複数" in note


def test_shorts_row_has_song_and_basics():
    video = make_video("s1", "この夏の主役は貴方だ【青と夏】", "#shorts", tags=["a", "b"])
    video["statistics"] = {"viewCount": "12345"}
    row = fetch_extra.shorts_row(video)
    assert list(row) == fetch_extra.SHORTS_FIELDS
    assert row["曲名"] == "青と夏"
    assert row["秒数"] == 45
    assert row["再生数"] == "12345"
    assert row["タグ"] == "a | b"
    assert row["要確認"] == ""


def test_run_shorts_uses_only_the_shorts_playlist_and_skips_other_channels():
    import csv
    import os
    import sys
    import tempfile

    mine = make_video("s1", "歌ってみた【青と夏】", "#shorts", published="2026-07-31T10:00:00Z")
    newer = make_video("s2", "歌ってみた【少女レイ】", "#shorts", published="2026-08-31T10:00:00Z")
    other = make_video("s3", "他人の動画【曲】", "#shorts", channel_id=OTHER_CHANNEL)
    playlists = {fetch_extra.SHORTS_PLAYLIST: ["s1", "s2", "s3", "gone"]}
    original_api, original_key, original_argv = fb.api_get, fb.get_api_key, sys.argv
    fb.api_get = fake_api(playlists, {"s1": mine, "s2": newer, "s3": other})
    fb.get_api_key = lambda: "key"
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "shorts.csv")
        sys.argv = ["fetch_extra.py", "shorts", "--out", out]
        try:
            printed = io.StringIO()
            with redirect_stdout(printed):
                fetch_extra.main()
        finally:
            fb.api_get, fb.get_api_key, sys.argv = original_api, original_key, original_argv
        with open(out, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
    assert [(r["video_id"], r["曲名"]) for r in rows] == [("s2", "少女レイ"), ("s1", "青と夏")]
    assert "取得できず" in printed.getvalue()


def test_member_channel_ids_come_from_the_members_own_videos_in_the_playlists():
    """メンバーのチャンネルIDは、シクフォニの再生リストに混ざる本人の動画から引く。"""
    videos = {
        "a": make_video("a", "シクフォニの曲", "x"),
        "b": make_video("b", "いるまのオリ曲", "x", channel_id="UCillma"),
        "c": make_video("c", "こさめのオリ曲", "x", channel_id="UCkosame"),
    }
    videos["b"]["snippet"]["channelTitle"] = "いるま"
    videos["c"]["snippet"]["channelTitle"] = "雨乃こさめ【シクフォニ】"
    playlists = {fb.PLAYLISTS["cover"]: ["a", "b"], fb.PLAYLISTS["original"]: ["c"]}
    original = fb.api_get
    fb.api_get = fake_api(playlists, videos)
    try:
        found = fetch_extra.member_channel_ids("key")
    finally:
        fb.api_get = original
    assert found["いるま"]["channelId"] == "UCillma"
    assert found["雨乃こさめ"]["channelId"] == "UCkosame"
    assert "暇72" not in found


def test_match_playlists_prefers_an_exact_title():
    playlists = [
        {"snippet": {"title": "歌ってみた"}},
        {"snippet": {"title": "歌ってみた（コラボ）"}},
        {"snippet": {"title": "雑談"}},
    ]
    matched = fetch_extra.match_playlists(playlists, ["歌ってみた"])
    assert [p["snippet"]["title"] for p in matched["歌ってみた"]] == ["歌ってみた"]


def test_match_playlists_falls_back_to_a_partial_title():
    playlists = [{"snippet": {"title": "LAN歌ってみた リスト"}}]
    matched = fetch_extra.match_playlists(playlists, ["LAN歌ってみた", "無い名前"])
    assert [p["snippet"]["title"] for p in matched["LAN歌ってみた"]] == ["LAN歌ってみた リスト"]
    assert matched["無い名前"] == []


def test_match_playlists_skips_the_all_uploads_marker():
    assert fetch_extra.match_playlists([], [fetch_extra.ALL_UPLOADS]) == {}


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
