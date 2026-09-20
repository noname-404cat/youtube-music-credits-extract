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


def test_flatten_keys_walks_lists_and_nesting():
    keys = fetch_extra.flatten_keys({"snippet": {"tags": ["a"], "thumbnails": {"default": {"url": "u"}}}, "x": [{"y": 1}]})
    assert "snippet.tags" in keys
    assert "snippet.thumbnails.default.url" in keys
    assert "x[].y" in keys


def test_shorts_playlist_id_swaps_the_uc_prefix():
    assert fetch_extra.shorts_playlist_id("UCGMG8BNfA8gsH9Rn_d_yW2A") == "UUSHGMG8BNfA8gsH9Rn_d_yW2A"
    assert fetch_extra.uploads_playlist_id("UCGMG8BNfA8gsH9Rn_d_yW2A") == "UUGMG8BNfA8gsH9Rn_d_yW2A"


def test_analyze_shorts_counts_tags_credits_and_collab_keys():
    with_everything = make_video(
        "s1",
        "歌ってみた【Cover】【暇72×すち / シクフォニ】",
        HONKE_DESCRIPTION + "\nコラボ企画",
        tags=["シクフォニ", "歌ってみた"],
    )
    with_everything["snippet"]["contributors"] = [{"channelId": "UCx"}]
    plain = make_video("s2", "ただのショート", "説明なし")
    result = fetch_extra.analyze_shorts([with_everything, plain])
    assert result["n"] == 2
    assert result["with_tags"] == 1
    assert result["top_tags"][0][0] in ("シクフォニ", "歌ってみた")
    assert result["with_honke"] == 1
    assert result["with_credit_labels"] == 1
    assert result["collab_keys"] == ["snippet.contributors", "snippet.contributors[].channelId"]
    assert result["collab_text"] == 1
    assert result["singers_in_title"] == 1


def test_analyze_shorts_reports_no_collab_keys_when_absent():
    result = fetch_extra.analyze_shorts([make_video("s2", "ただのショート", "説明なし")])
    assert result["collab_keys"] == []
    out = io.StringIO()
    with redirect_stdout(out):
        fetch_extra.print_shorts_report(result, "テスト")
    assert "collab/contributor/partner を含むキーは無かった" in out.getvalue()


def test_shorts_row_has_tags_and_honke_songs():
    video = make_video("s1", "歌ってみた", HONKE_DESCRIPTION, tags=["a", "b"])
    row = fetch_extra.shorts_row(video)
    assert row["タグ"] == "a | b"
    assert row["本家様の曲"] == "Ado「新時代」"
    assert row["秒数"] == 45
    assert row["投稿日"] == "2026-01-02"


def test_collect_shorts_falls_back_when_the_shorts_playlist_is_empty():
    calls = []
    original_api, original_scan = fb.api_get, fetch_extra.find_shorts_by_scan
    fb.api_get = fake_api({fetch_extra.shorts_playlist_id(fb.CHANNEL_ID): []}, {})
    fetch_extra.find_shorts_by_scan = lambda api_key, limit, scan_max: calls.append(limit) or []
    try:
        with redirect_stdout(io.StringIO()):
            videos, source = fetch_extra.collect_shorts("key", 5)
    finally:
        fb.api_get, fetch_extra.find_shorts_by_scan = original_api, original_scan
    assert calls == [5]
    assert "アップロード一覧" in source


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
