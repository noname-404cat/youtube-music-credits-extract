"""実データに対する回帰テスト。

レビューで洗い出した破綻ポイントが再発しないよう、実際の概要欄で固定する。
    python3 test_extract.py
"""

import extract
import fixtures


def row_of(video, category="original"):
    return extract.build_row(video, category)


def test_lyrics_section_does_not_leak_into_credit():
    """◆Lyrics は敬称略の後に歌詞見出しとして再登場する。1回目だけを採る。"""
    row = row_of(fixtures.ORIGINAL_SIX_NATION)
    assert row["作詞"] == "ケンカイヨシ", row["作詞"]
    assert "ジョーカー" not in row["作詞"]
    assert "\n" not in row["作詞"]


def test_misspelled_illustration_label_is_matched():
    """◆Main Animation ＆ IIlustration (綴り揺れ + 全角＆) を取りこぼさない。"""
    row = row_of(fixtures.ORIGINAL_APRIL_FOOL)
    assert row["絵"] == "緒文 / 成田無限 / 重光亮摩 / 稗苗 一糸", row["絵"]


def test_zero_width_characters_are_stripped_from_song():
    """タイトルの U+200D を除去する。ただし意匠(キリル文字Я)は残す。"""
    row = row_of(fixtures.ORIGINAL_T4XI)
    assert row["曲名"] == "T4xi DЯiver", repr(row["曲名"])
    assert "‍" not in row["曲名"]


def test_multiple_lyricists_are_split():
    row = row_of(fixtures.ORIGINAL_T4XI)
    assert row["作詞"] == "ふぁるすてぃ / 暇72", row["作詞"]
    assert row["作曲"] == "ふぁるすてぃ", row["作曲"]


def test_original_playlist_without_music_label_is_flagged():
    """オリジナル再生リスト所属でも ◆Music が無い動画がある。埋めずに要確認にする。"""
    row = row_of(fixtures.ORIGINAL_MEDLEY)
    assert row["作曲"] == ""
    assert row["作詞"] == ""
    assert row["要確認"] == "要確認"
    assert "作曲: 該当ラベルが概要欄に無い" in row["要確認理由"]


def test_trailing_space_in_label_is_tolerated():
    """「◆Illustration 」の末尾スペースで一致に失敗しない。"""
    row = row_of(fixtures.ORIGINAL_MEDLEY)
    assert row["絵"] == "こよせ", row["絵"]


def test_cover_title_splits_song_and_original_artist():
    row = row_of(fixtures.COVER_SHOUJO_REI, "cover")
    assert row["曲名"] == "少女レイ"
    assert row["原曲アーティスト"] == "みきとP"


def test_cover_song_name_keeps_inner_spaces():
    """曲名自体に半角スペースと記号が入る。末尾ブラケット内の「 / 」に引っ張られない。"""
    row = row_of(fixtures.COVER_KYOURAN, "cover")
    assert row["曲名"] == "狂乱 Hey Kids!!", row["曲名"]
    assert row["原曲アーティスト"] == "THE ORAL CIGARETTES"


def test_singers_are_parsed_from_trailing_bracket():
    """【暇72×すち / シクフォニ】からメンバー2名を取り、グループ名は落とす。"""
    row = row_of(fixtures.COVER_KYOURAN, "cover")
    assert row["歌ってる人"] == "暇72 / すち", row["歌ってる人"]
    assert "タイトルに歌唱者の表記が無く" not in row["要確認理由"]


def test_default_singers_are_always_flagged():
    """表記が無いときの「全員」は推定であり、黙って確定させない。"""
    row = row_of(fixtures.COVER_SHOUJO_REI, "cover")
    assert row["歌ってる人"] == "暇72 / 雨乃こさめ / いるま / LAN / すち / みこと"
    assert row["歌唱者は推定"] == "推定"
    assert "タイトルに歌唱者の表記が無く" not in row["要確認理由"]


def test_cover_never_guesses_lyricist_from_original_artist():
    """THE ORAL CIGARETTES はバンド名であり作詞作曲者ではない。原曲名で埋めてはいけない。"""
    row = row_of(fixtures.COVER_KYOURAN, "cover")
    assert row["作詞"] == ""
    assert row["作曲"] == ""


def test_name_with_inner_space_survives_fullwidth_separator():
    """`藤浪 潤一郎　( url )` を空白で切ると姓だけになる。全角スペースで切る。"""
    credits = extract.credits_by_column(fixtures.ORIGINAL_SIX_NATION["snippet"]["description"])
    assert extract._clean_name("藤浪 潤一郎　( https://x.com/2273xxx )") == "藤浪 潤一郎"
    assert credits["絵"]["names"] == ["すわだ"]


def test_affiliation_in_parentheses_is_dropped():
    assert extract._clean_name("呉井辰吉(SUPA LOVE) ") == "呉井辰吉"
    assert extract._clean_name("ソノイ(In Fleur Inc.) 　( https://x.com/_Sonoi )") == "ソノイ"


def test_published_at_converts_to_jst():
    assert extract.to_jst_date("2026-08-31T10:00:06Z") == "2026-08-31"
    assert extract.to_jst_date("2026-08-31T15:30:00Z") == "2026-09-01"


def test_cover_without_lyricist_label_is_not_flagged():
    """カバーは作詞作曲が原曲側にあり、概要欄に無いのが通常。要確認にしない。"""
    row = row_of(fixtures.COVER_SHOUJO_REI, "cover")
    assert "作詞: 該当ラベルが概要欄に無い" not in row["要確認理由"]
    assert "作曲: 該当ラベルが概要欄に無い" not in row["要確認理由"]


def test_medley_lists_songs_from_honke_section():
    """曲名が1つに決まらないメドレーは、▼本家様 欄の曲を表記のまま順に出す。"""
    row = row_of(fixtures.COVER_ANISON_MEDLEY, "cover")
    songs = row["メドレー収録曲"].split(" | ")
    assert len(songs) == 6, songs
    assert songs[0] == "TVアニメ「ONE PIECE」1000話記念：ウィーアー！"
    assert songs[-1].startswith("「残酷な天使のテーゼ」")
    assert "DAN DAN 心魅かれてく" in songs
    assert all(not s.startswith(("http", "※")) for s in songs), songs
    assert row["曲名"] == ""
    assert "曲名が取れない" not in row["要確認理由"]


def test_single_cover_is_not_treated_as_medley():
    row = row_of(fixtures.COVER_SHOUJO_REI, "cover")
    assert row["メドレー収録曲"] == ""


def test_music_and_lyrics_label_fills_both_columns():
    """◆Music&Lyrics は作詞と作曲を兼ねる。歌詞見出しの◆Lyricsに引っ張られない。"""
    row = row_of(fixtures.ORIGINAL_MUSIC_AND_LYRICS)
    assert row["作詞"] == "ケンカイヨシ", row["作詞"]
    assert row["作曲"] == "ケンカイヨシ", row["作曲"]
    assert "作詞" not in row["要確認理由"] and "作曲" not in row["要確認理由"]


def test_rap_lyrics_is_added_to_lyricist_with_marker():
    """RAP Lyrics はラップ部分の作詞者。作詞に足すが (RAP) で曲全体の作詞者と区別する。"""
    row = row_of(fixtures.ORIGINAL_LYRICS_AND_RAP)
    assert row["作詞"] == "ふぁるすてぃ / いるま(RAP)", row["作詞"]
    row = row_of(fixtures.ORIGINAL_MUSIC_LYRICS_AND_RAP)
    assert row["作詞"] == "ふぁるすてぃ / いるま(RAP)", row["作詞"]
    assert row["作曲"] == "ふぁるすてぃ", row["作曲"]


def test_cover_rap_lyricist_is_marked_as_rap_only():
    """カバーの作詞にラップ担当が入っても、原曲の作詞者と誤読されない。"""
    row = row_of(fixtures.COVER_RAP_ONLY, "cover")
    assert row["作詞"] == "いるま(RAP)", row["作詞"]
    assert row["作曲"] == ""


def test_illusration_typo_is_matched_as_illustration():
    row = row_of(fixtures.COVER_ILLUSRATION_TYPO, "cover")
    assert row["絵"] == "トウカ", row["絵"]
    assert "絵" not in row["要確認理由"]


def test_thumbnail_illustrator_is_not_the_illustrator():
    """◆サムネイラスト はサムネイル担当。絵に入れず、絵が無いものとして要確認にする。"""
    row = row_of(fixtures.COVER_THUMBNAIL_ILLUST_ONLY, "cover")
    assert row["絵"] == "", row["絵"]
    assert "絵: 該当ラベルが概要欄に無い" in row["要確認理由"]


def test_cover_with_two_honke_entries_is_not_a_medley():
    """本家様欄が2曲でも、タイトルに「メドレー」が無ければ通常のカバー。"""
    row = row_of(fixtures.COVER_TWO_HONKE_NOT_MEDLEY, "cover")
    assert row["メドレー収録曲"] == ""
    assert row["曲名"] == "夏祭り", row["曲名"]


def test_every_sample_produces_a_song_name():
    for video, category in fixtures.ALL_SAMPLES:
        row = extract.build_row(video, category)
        assert row["曲名"], f"曲名が空: {row['video_id']}"
        assert row["raw_description"], f"raw が空: {row['video_id']}"


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
