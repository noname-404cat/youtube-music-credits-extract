"""members.py と、fetch_extra.py の member-songs のテスト。

タイトルは、メンバーのチャンネルを実際に調べたとき（2026-09-21）の出力に出ていたものを使う。
APIは疑似関数に差し替え、ネットワークには触らない。

    python3 test_members.py
"""

import csv
import io
import os
import sys
import tempfile
from contextlib import redirect_stdout

import extract
import fetch_and_build as fb
import fetch_extra
import members
from test_fetch_extra import fake_api, make_video


def song_of(title):
    return members.parse_title(title)["song"]


# --- 曲名（タイトル） ------------------------------------------------------


def test_song_before_the_slash_for_hima72_covers():
    assert song_of("丸の内サディスティック／暇72 【Cover】") == "丸の内サディスティック"
    assert song_of("AIZO／暇72 【Cover】") == "AIZO"
    assert song_of("不可幸力／暇72 【Cover】") == "不可幸力"


def test_hima72_original_uses_the_official_format():
    assert song_of("暇72 - 希死遠慮 [Official Music Video]") == "希死遠慮"
    assert members.title_category("暇72 - 希死遠慮 [Official Music Video]") == "original"


def test_leading_bracket_and_trailing_bracket_are_dropped_for_kosame():
    assert song_of("【誕生日に】恥ずかしいか青春は / 雨乃こさめ【歌ってみた / シクフォニ】") == "恥ずかしいか青春は"
    assert song_of("とても素敵な六月でした / 歌ってみた【雨乃こさめ / シクフォニ】") == "とても素敵な六月でした"
    assert song_of("点.mp4 / 歌ってみた【雨乃こさめ / シクフォニ】") == "点.mp4"
    assert song_of("【6周年】シルエット / 雨乃こさめ【歌ってみた / シクフォニ】") == "シルエット"


def test_kosame_original_mv_is_original():
    assert song_of("【MV】ジグザグ / 雨乃こさめ") == "ジグザグ"
    assert members.title_category("【MV】ジグザグ / 雨乃こさめ") == "original"
    assert song_of("雨乃こさめ - ありきたり [Official Music Video]") == "ありきたり"


def test_old_kosame_titles_drop_the_uta_tte_mita_tail():
    assert song_of("【オリジナル音源で】YELLOW 歌ってみた / 雨乃こさめ(cover)") == "YELLOW"
    assert song_of("ビターチョコデコレーション　歌ってみた / 雨乃こさめ(cover)") == "ビターチョコデコレーション"


def test_lan_puts_the_original_artist_after_the_slash():
    assert song_of("【元プロ声優が】きゅうくらりん / いよわ Covered by LAN") == "きゅうくらりん"
    assert song_of("【最大の感謝を込めて】BEAUTIFUL DAYS / SPYAIR Covered by LAN") == "BEAUTIFUL DAYS"
    assert song_of("【4オクターブで】'ヤラララ' (YARARARA) / AnythingBecomeMoe Cover") == "ヤラララ (YARARARA)"


def test_such_titles_after_the_leading_bracket():
    assert song_of("【矯正中の絵師が】Tot Musica／歌ってみた【すち】【シクフォニ】") == "Tot Musica"
    assert song_of("【絵師が】踊／歌ってみた【すち】【シクフォニ】") == "踊"


def test_voice_imitation_series_takes_the_quoted_song():
    assert song_of("【鬼滅の刃】伊黒小芭内で『グッバイ宣言』歌ってみた【声真似】") == "グッバイ宣言"
    assert song_of("【鬼滅の刃】おばみつで『アイドル／YOASOBI』歌ってみた【声真似】") == "アイドル"
    assert song_of("【銀魂】ドS検定組で”虎視眈々”歌ってみた【声真似】") == "虎視眈々"
    assert song_of('【銀魂】沖神兄で"一騎当千"歌ってみた【声真似】') == "一騎当千"


def test_a_title_with_no_song_shape_is_not_song_like():
    """みこと・いるまのアップロードにはショートの企画動画が混ざる。曲の形が見えなければ採らない。"""
    for title in ("【アニメ】俺のリア友が天然すぎる件", "誰に似てますか？", "検診をおすすめします。"):
        assert members.parse_title(title)["song_like"] is False, title


# --- ハッシュタグ（ショート） ----------------------------------------------


def test_short_song_comes_from_the_first_non_generic_hashtag():
    assert members.song_from_hashtags("はい登録しましょうね。#デビットビット　#歌ってみた", "") == "デビットビット"
    assert members.song_from_hashtags("あんま無責任なこと言うな？#未完成婚姻論", "") == "未完成婚姻論"


def test_short_song_uses_the_description_when_the_title_has_only_generic_tags():
    assert members.song_from_hashtags(
        "4オクターブで歌ってみた”ヤラララ”【#多声類】", "#歌ってみた #ヤラララ #ABM #AnythingBecomeMoe #vtuber"
    ) == "ヤラララ"
    assert members.song_from_hashtags("#高音厨 全員イケボ説【メルト】", "#歌ってみた #メルト #ryo #supercell") == "メルト"


def test_hashtag_in_brackets_does_not_keep_the_closing_bracket():
    tags = members._HASHTAG.findall("【検証】#両声類 結局最後はイケボ説【#多声類】")
    assert tags == ["両声類", "多声類"], tags


def test_hashtags_that_are_not_songs_give_none():
    assert members.song_from_hashtags("【アニメ】俺のリア友が天然すぎる件 #vtuber #anime", "") is None
    assert members.song_from_hashtags("ドパガキ用メドレー", "#歌ってみた #tiktokメドレー #tiktokbest #バズ曲 #トレンド") is None


# --- 歌唱者 ----------------------------------------------------------------


def test_singers_come_from_the_title_when_it_names_members():
    assert members.singers_in_title("【絵師が】踊／歌ってみた【すち】【シクフォニ】") == ["すち"]
    assert members.singers_in_title("丸の内サディスティック／暇72 【Cover】") == ["暇72"]
    assert members.singers_in_title("【元プロ声優が】セレナーデ / なとり Covered by LAN") == ["LAN"]
    assert members.singers_in_title("【暇72×いるま】曲名／原曲【Cover】") == ["暇72", "いるま"]


def test_singer_falls_back_to_the_channel_owner():
    video = make_video("a", "【鬼滅の刃】伊黒小芭内で『グッバイ宣言』歌ってみた【声真似】", "x")
    row = members.member_row(video, "暇72", "声真似歌ってみた。")
    assert (row["歌ってる人"], row["歌唱者の出所"]) == ("暇72", "チャンネル")
    video = make_video("b", "AIZO／暇72 【Cover】", "x")
    row = members.member_row(video, "暇72", "Covered by 暇72")
    assert (row["歌ってる人"], row["歌唱者の出所"]) == ("暇72", "タイトル")


def test_a_non_member_next_to_a_member_is_flagged_as_a_possible_guest():
    """「キルシュトルテ × 暇72」は二人で歌っている可能性がある。確定できないので要確認にする。"""
    assert members.guest_candidates("爆笑／キルシュトルテ × 暇72【Cover】") == ["キルシュトルテ"]
    row = members.member_row(make_video("a", "爆笑／キルシュトルテ × 暇72【Cover】", "x"), "暇72", "Covered by 暇72")
    assert row["要確認"] == "要確認"
    assert "共演者の可能性: キルシュトルテ" in row["要確認理由"]
    assert row["歌ってる人"] == "暇72"


def test_original_artist_after_the_slash_is_not_a_guest():
    assert members.guest_candidates("【元プロ声優が】きゅうくらりん / いよわ Covered by LAN") == []
    assert members.guest_candidates("【誕生日に】恥ずかしいか青春は / 雨乃こさめ【歌ってみた / シクフォニ】") == []


# --- 1動画→1行 -------------------------------------------------------------


def test_playlist_video_without_a_slash_takes_the_whole_title_and_is_flagged():
    video = make_video("a", "ドパガキ用メドレー作って歌ってみたｗｗｗｗｗ", "#歌ってみた #tiktokメドレー")
    row = members.member_row(video, "LAN", "おうたのshort")
    assert row["曲名"] == "ドパガキ用メドレー作って歌ってみたｗｗｗｗｗ"
    assert row["要確認"] == "要確認"
    assert "区切りの「／」が無く" in row["要確認理由"]


def test_upload_only_video_without_a_song_shape_is_skipped():
    video = make_video("a", "【アニメ】俺のリア友が天然すぎる件 #vtuber #anime", "")
    row = members.member_row(video, "みこと", None)
    assert row["曲名"] == ""
    assert "曲名を判定できない" in row["要確認理由"]


def test_short_takes_the_song_from_the_hashtag_and_marks_it():
    video = make_video("a", "4オクターブで歌ってみた”ヤラララ”【#多声類】", "#歌ってみた #ヤラララ #ABM")
    row = members.member_row(video, "LAN", "おうたのshort")
    assert (row["曲名"], row["曲名の出所"], row["ショート"]) == ("ヤラララ", "ハッシュタグ", "はい")


def test_long_video_ignores_hashtags_and_uses_the_title():
    """ハッシュタグから曲名を採るのはショートだけ。長尺は付いていても使わない。"""
    video = make_video("a", "【絵師が】踊／歌ってみた【すち】【シクフォニ】", "#歌ってみた #ノイズ")
    video["contentDetails"] = {"duration": "PT4M12S"}
    assert members.is_short(video) is False
    row = members.member_row(video, "すち", "歌ってみた")
    assert (row["曲名"], row["曲名の出所"], row["ショート"]) == ("踊", "タイトル", "")


def test_is_short_boundary():
    video = make_video("a", "t", "x")
    video["contentDetails"] = {"duration": "PT3M"}
    assert members.is_short(video) is True
    video["contentDetails"] = {"duration": "PT3M1S"}
    assert members.is_short(video) is False
    video["contentDetails"] = {}
    assert members.is_short(video) is False


def test_category_prefers_the_title_and_falls_back_to_the_playlist():
    row = members.member_row(make_video("a", "暇72 - 希死遠慮 [Official Music Video]", "x"), "暇72", "Covered by 暇72")
    assert row["category"] == "original"
    row = members.member_row(make_video("b", "点.mp4 / 歌ってみた【雨乃こさめ / シクフォニ】", "x"), "雨乃こさめ", "歌ってみた！")
    assert row["category"] == "cover"
    row = members.member_row(make_video("c", "曲名／だれか", "x"), "いるま", "Original (Solo)")
    assert row["category"] == "original"


def test_playlist_category_names():
    assert members.playlist_category("Original (Group)") == "original"
    assert members.playlist_category("LANオリジナル曲") == "original"
    assert members.playlist_category("Cover (Solo)") == "cover"
    assert members.playlist_category("Rap arrange (Group)") == "cover"
    assert members.playlist_category("Rap Collaboration") is None


def test_unknown_category_is_flagged():
    row = members.member_row(make_video("a", "曲名／だれか", "x"), "いるま", "Rap Collaboration")
    assert row["category"] == ""
    assert "カバーかオリジナルか判定できない" in row["要確認理由"]


# --- 絵・動画（概要欄） ----------------------------------------------------


def test_credit_label_followed_by_a_name_on_the_same_line():
    """暇72の声真似シリーズにある書き方（◆Illustration　どろ　https://…）。"""
    description = (
        "◆Vocal　暇72　https://twitter.com/hima72_25\n\n"
        "◆Mix　よしか⁂　https://twitter.com/yosi_k14\n\n"
        "◆Illustration　どろ　https://twitter.com/doro_desu2\n\n"
        "◆Movie　あさこ　https://twitter.com/OO1O83\n\n※敬称略\n"
    )
    row = members.member_row(make_video("a", "【銀魂】沖田総悟で『うっせぇわ』歌ってみた【声真似】", description), "暇72", "声真似歌ってみた。")
    assert (row["絵"], row["動画"]) == ("どろ", "あさこ")


def test_compound_label_fills_both_illustration_and_movie():
    """◆Vocal & Movie & Illust は、動画も絵も本人。"""
    row = members.member_row(make_video("a", "曲／歌ってみた【暇72】", "◆Vocal & Movie & Illust\n暇72\n\n※敬称略\n"), "暇72", "歌ってみた")
    assert (row["絵"], row["動画"]) == ("暇72", "暇72")


def test_missing_credit_labels_are_left_blank_without_a_flag():
    row = members.member_row(make_video("a", "点.mp4 / 歌ってみた【雨乃こさめ / シクフォニ】", "眩しい日には見えないものを"), "雨乃こさめ", "歌ってみた！")
    assert (row["絵"], row["動画"]) == ("", "")
    assert row["要確認"] == ""


# --- 絵・動画（◆ が無い書き方） ---------------------------------------------


def test_loose_credit_formats_without_the_diamond():
    """メンバーのチャンネルには ◆ の無い書き方がある。ラベル名は暇72の声真似シリーズの実例から。"""
    assert members.loose_credits("Movie：LAN\nサムネ：暇72\nOP / ED\n") == {"動画": ["LAN"]}
    assert members.loose_credits("動画：みこと\n絵：すち / こさめ\n") == {"動画": ["みこと"], "絵": ["すち", "こさめ"]}
    assert members.loose_credits("Illustration by どろ\nMovie by あさこ\n") == {"絵": ["どろ"], "動画": ["あさこ"]}
    assert members.loose_credits("【Movie】あさこ\n[Illustration] どろ\n") == {"動画": ["あさこ"], "絵": ["どろ"]}
    assert members.loose_credits("サムネイラスト：ねぽ\n") == {"絵": ["ねぽ"]}


def test_loose_credit_with_a_url_after_the_name():
    """区切りは全角スペース。URLの「https:」の「:」で切らない。"""
    description = "Illustration　どろ　https://twitter.com/doro_desu2\nMovie　あさこ　https://twitter.com/OO1O83\n"
    assert members.loose_credits(description) == {"絵": ["どろ"], "動画": ["あさこ"]}
    assert members.loose_credits("Illust どろ https://twitter.com/x\n") == {"絵": ["どろ"]}


def test_loose_credit_label_on_its_own_line_takes_the_next_lines():
    description = "Illustration\nどろ\nhttps://twitter.com/doro_desu2\n\nMovie\nあさこ\n\nMix\nよしか\n"
    assert members.loose_credits(description) == {"絵": ["どろ"], "動画": ["あさこ"]}


def test_loose_credit_compound_label():
    assert members.loose_credits("Vocal & Movie & Illust　暇72\n") == {"絵": ["暇72"], "動画": ["暇72"]}


def test_loose_credit_does_not_pick_up_ordinary_sentences():
    for text in (
        "新作Movieが公開されます！\nmovie is coming soon\nMovie star 好きだった\n",
        "次のMovie：楽しみ、です\n今日の絵：かわいい！\n",
        "Illustrationの意味を知りたくて\n動画を見て、絵を描いた。\n",
        "動画はこちら\nhttps://youtu.be/abc\n",
    ):
        assert members.loose_credits(text) == {}, text


def test_member_row_uses_the_loose_credits_when_there_is_no_diamond():
    row = members.member_row(make_video("a", "点.mp4 / 歌ってみた【雨乃こさめ / シクフォニ】", "Movie：LAN\n絵：すち"), "雨乃こさめ", "歌ってみた！")
    assert (row["絵"], row["動画"]) == ("すち", "LAN")


def test_diamond_credits_win_over_loose_ones():
    description = "◆Illustration\nどろ\n\n※敬称略\n\n絵：だれか\n"
    row = members.member_row(make_video("a", "曲／歌ってみた【すち】", description), "すち", "歌ってみた")
    assert row["絵"] == "どろ"


# --- ショート（再生リストに入っていないもの） --------------------------------


def _http_error(code):
    import urllib.error

    return urllib.error.HTTPError("http://x", code, "err", {}, None)


def test_every_member_has_a_way_to_reach_shorts():
    """再生リストに入っていないショートも対象。いるま・みことはアップロード全体、他は UUSH のショート一覧。"""
    for member, spec in fetch_extra.MEMBER_SOURCES.items():
        assert spec.get("uploads") or spec.get("shorts"), member


def test_fetch_member_shorts_uses_the_shorts_playlist_and_skips_known_and_live():
    channel = "UCsuchi0000000000000000"
    short = make_video("sh1", "曲名【歌ってみた】 #未完成", "", channel_id=channel)
    known = make_video("sh2", "既に再生リストにある", "", channel_id=channel)
    live = make_video("sh3", "配信", "", channel_id=channel)
    live["liveStreamingDetails"] = {}
    long_video = make_video("sh4", "長い動画", "", channel_id=channel)
    long_video["contentDetails"] = {"duration": "PT9M"}
    videos = {v["id"]: v for v in (short, known, live, long_video)}
    original = fb.api_get
    fb.api_get = fake_api({"UUSH" + channel[2:]: ["sh1", "sh2", "sh3", "sh4"]}, videos)
    try:
        found = fetch_extra.fetch_member_shorts("key", channel, 10, "snippet", {"sh2"})
    finally:
        fb.api_get = original
    assert [v["id"] for v in found] == ["sh1"]


def test_fetch_member_shorts_falls_back_to_uploads_when_the_shorts_playlist_is_missing():
    channel = "UCsuchi0000000000000000"
    short = make_video("sh1", "曲名【歌ってみた】", "", channel_id=channel)
    long_video = make_video("sh4", "長い動画", "", channel_id=channel)
    long_video["contentDetails"] = {"duration": "PT9M"}
    base = fake_api({"UU" + channel[2:]: ["sh1", "sh4"]}, {"sh1": short, "sh4": long_video})

    def api_get(api_key, path, **params):
        if params.get("playlistId", "").startswith("UUSH"):
            raise _http_error(404)
        return base(api_key, path, **params)

    original = fb.api_get
    fb.api_get = api_get
    try:
        found = fetch_extra.fetch_member_shorts("key", channel, 10, "snippet", set())
    finally:
        fb.api_get = original
    assert [v["id"] for v in found] == ["sh1"]


def test_collect_member_videos_adds_shorts_outside_the_playlists():
    channel = "UCsuchi0000000000000000"
    in_playlist = make_video("p1", "【絵師が】踊／歌ってみた【すち】", "x", channel_id=channel)
    in_playlist["contentDetails"] = {"duration": "PT4M"}
    short = make_video("sh1", "夜に駆ける歌ってみた #夜に駆ける", "", channel_id=channel)
    videos = {"p1": in_playlist, "sh1": short}
    playlists = {"PLsuchi": ["p1"], "UUSH" + channel[2:]: ["p1", "sh1"]}
    base = fake_api(playlists, videos)

    def api_get(api_key, path, **params):
        if path == "playlists":
            return {"items": [{"id": "PLsuchi", "snippet": {"title": "歌ってみた"}, "contentDetails": {"itemCount": 1}}]}
        return base(api_key, path, **params)

    original = fb.api_get
    fb.api_get = api_get
    try:
        collected, stats = fetch_extra.collect_member_videos("key", channel, fetch_extra.MEMBER_SOURCES["すち"], 300, 500)
    finally:
        fb.api_get = original
    assert [(v["id"], p) for v, p in collected] == [("p1", "歌ってみた"), ("sh1", None)]
    rows = [members.member_row(v, "すち", p) for v, p in collected]
    assert rows[1]["曲名"] == "夜に駆ける" and rows[1]["ショート"] == "はい"


# --- 実行結果（1363本）で見つかった誤りの再発防止 ---------------------------


def test_member_and_group_names_are_never_a_song_name():
    """#暇72 #雨乃こさめ などのメンバー名タグが曲名になっていた（暇72が185本）。全角・半角の揺れも同じ。"""
    for name in ("暇72", "暇７２", "雨乃こさめ", "いるま", "ＬＡＮ", "LAN", "すち", "みこと", "シクフォニ", "SIXFONIA"):
        assert members.is_member_name(name), name
    assert members.song_from_hashtags("無人島生活してみたくない？ #shorts", "#shorts #暇72 #シクフォニ #vtuber") is None
    assert members.song_from_hashtags("逆やろって言わせる #雨乃こさめ #シクフォニ #いるま #マイクラ", "") is None
    song, source, _ = members.resolve_song("暇72", "", False, True)
    assert song is None, "どの経路でも、メンバー名は曲名にしない"


def test_topic_tags_are_not_songs_but_the_songs_named_by_the_user_are():
    for tag in ("shortsvideo", "shortsfeed", "イラスト", "マイクラ", "pokemon", "鬼滅の刃", "銀魂", "ado", "dance", "シクフォニ3D"):
        assert members._is_generic(tag), tag
    for song in ("irisout", "人マニア", "テトリス", "可愛くてごめん", "モエチャッカファイア"):
        assert not members._is_generic(song), song
    assert members.song_from_hashtags("【TikTokでバズ】君たち、ほんと最高だよ。#人マニア #shorts", "") == "人マニア"
    assert members.song_from_hashtags("今推せば君も新規です！！！#テトリス #歌ってみた #vtuber", "") == "テトリス"


def test_illustration_making_of_shorts_do_not_take_a_hashtag_song():
    """すちの「サムネ描いてみた」は、#歌ってみた が付いていても曲ではない。"""
    video = make_video("a", "【サムネ描いてみた】 #歌ってみた #イラスト #描いてみた #メイキング #偽物人間40号", "")
    row = members.member_row(video, "すち", None)
    assert row["曲名"] == "", row["曲名"]


def test_short_title_with_a_slash_beats_the_hashtags():
    """タイトルに「曲名 / 誰か」とあれば、ハッシュタグ（曲名以外の語が先に来ることがある）より確か。"""
    cases = [
        ("【Rap arrange】モエチャッカファイア / いるま", "#zenlesszonezero #歌ってみた", "モエチャッカファイア"),
        ("【歌い手歴2週間の俺が】ウタカタララバイ/Ado 激ムズラップパート歌った結果wwwwwww", "#Ado #歌ってみた", "ウタカタララバイ"),
        ("【Remix】p.h. / いるま【シクフォニ】【SEVENTHLINKS】", "#ph #歌ってみた", "p.h."),
        ("残酷な夜に輝け / LiSA #歌ってみた #LiSA #shorts", "", "残酷な夜に輝け"),
    ]
    for title, description, expected in cases:
        song, source, _ = members.resolve_song(title, description, True, False)
        assert (song, source) == (expected, "タイトル"), (title, song, source)


def test_slash_without_spaces_next_to_japanese_splits_but_digits_do_not():
    assert members.parse_title("ファタール/キタニタツヤ様 #歌ってみた")["song"] == "ファタール"
    assert members.parse_title("【圧倒的王子が】妄想アステルパーム/picco様【歌ってみた】#shorts")["song"] == "妄想アステルパーム"
    assert members.parse_title("2024/09/21 の雑談")["split"] is False


def test_new_song_with_quotes_is_an_original():
    """すちの「新曲⚾️ 『1HOLE』 【すち】」。"""
    parsed = members.parse_title("新曲⚾️ 『1HOLE』 【すち】 #shorts #vtuber")
    assert parsed["song"] == "1HOLE"
    assert members.title_category("新曲⚾️ 『1HOLE』 【すち】") == "original"


def test_song_at_the_end_of_the_title_in_brackets():
    """ハッシュタグから取れないときの予備。「…【曲名】」、「…【曲名】【原曲アーティスト】」。"""
    assert members.bracket_song("【歌い手が】ちゅ！と言うたびキャラが変わる声真似チャレンジｗｗｗｗ 【可愛くてごめん】#shorts") == "可愛くてごめん"
    assert members.bracket_song("何が何でも天然水になりたかった成人男性の【とても素敵な六月でした】【Eight】　#shorts") == "とても素敵な六月でした"
    assert members.bracket_song("声真似オールバックしたら喉終わったわwwwwww 【強風オールバック】#shorts") == "強風オールバック"
    for title in ("【アニメ】オタクくん～見てる？電話に...【漫画】", "ルールを守って剣と盾チャレンジ【3D】", "曲名／歌ってみた【すち】【シクフォニ】"):
        assert members.bracket_song(title) is None, title


def test_a_lone_hiragana_particle_is_not_a_song():
    song, _, _ = members.resolve_song("【#多声類】 #新人vtuber の【Bunny Girl / バニーガール】【AKASHI】", "", False, True)
    assert song != "の"


def test_guest_needs_a_member_in_the_line_and_ignores_hashtags():
    # 原曲側の名義（LAN）: メンバーが並びに居ないので共演者ではない
    assert members.guest_candidates("【最大の感謝を込めて】セカイ / DECO*27×堀江晶太(kemu) Covered by LAN") == []
    # 実データの誤検出: ハッシュタグの中の名前を共演者にしていた
    assert members.guest_candidates("T氏の話を信じるな／暇72×雨乃こさめ #歌ってみた #ピノキオピー #cover") == []
    # 本物の共演者
    assert members.guest_candidates("HOWL／すち×超学生【Cover】") == ["超学生"]
    assert members.guest_candidates("【Cover】Rambling Beast / いるま×しゃけみー×渚トラウト") == ["しゃけみー", "渚トラウト"]


def test_category_from_hashtags_and_no_flag_for_a_hashtag_song():
    video = make_video("a", "今推せば君も新規です！！！#テトリス #歌ってみた #vtuber", "")
    row = members.member_row(video, "いるま", None)
    assert (row["曲名"], row["category"], row["要確認"]) == ("テトリス", "cover", "")
    # 企画動画のように区別が付かないものも、ハッシュタグ由来の曲名なら要確認にしない（大量に立つため）
    video = make_video("b", "【TikTokでバズ】君たち、ほんと最高だよ。#人マニア #shorts", "")
    row = members.member_row(video, "暇72", None)
    assert (row["曲名"], row["category"], row["要確認"]) == ("人マニア", "", "")
    assert members.hashtag_category("", "#オリジナル曲 #新曲") == "original"


# --- 2回目の実行（ハッシュタグ由来の曲名 765本）で見つけた曲名でないタグ ------


def test_people_topics_and_artists_are_not_song_names():
    not_songs = [
        "しろせんせー", "キルシュトルテ", "ゲーム実況", "ニキ", "みぃ太軍", "18号", "弐十",
        "マリカ", "おみくじ", "呪術廻戦", "沖田総悟", "おじさん構文", "合唱", "アカペラ", "方言", "女声",
        "なとり", "ピノキオピー", "キタニタツヤ", "オリジナル曲", "シクフォ二",
    ]
    for tag in not_songs:
        assert members._is_generic(tag), tag


def test_songs_that_look_like_topics_stay_songs():
    """繰り返し出るが、曲名のもの。ご指定の5つに加え、実データで曲と判断したもの。"""
    songs = [
        "irisout", "人マニア", "テトリス", "可愛くてごめん", "モエチャッカファイア",
        "ドレミの歌", "唱", "ライラック", "はいよろこんで", "混沌ブギ", "ヤラララ", "爆裂愛してる", "ウワサのあの子",
        "プロポーズ", "なぁぜなぁぜ", "リードコントロール", "モニタリング", "アイドル", "最酊",
        # 判断を確認して曲名と決めたもの
        "カラスの目", "トンツカタンタン", "真的没喝多",
    ]
    for tag in songs:
        assert not members._is_generic(tag), tag


def test_tags_confirmed_as_not_songs():
    for tag in ("ありナ", "bbbbダンス", "爆弾", "ナガレ", "ズズ", "エジソン", "100万ドルの五稜星"):
        assert members._is_generic(tag), tag


def test_a_short_with_only_person_and_topic_tags_has_no_song():
    """暇72のショートで最も多かった誤り（しろせんせー56本、キルシュトルテ40本、ゲーム実況30本）。"""
    for title, description in (
        ("みんなは流石に履くよね？ #shorts", "#shorts #しろせんせー #暇72 #シクフォニ"),
        ("VTuberの裏の姿がヤバイ。 #shorts", "#shorts #キルシュトルテ #暇72"),
        ("なんの話してるの？ #shorts", "#shorts #ゲーム実況 #暇72"),
    ):
        row = members.member_row(make_video("a", title, description), "暇72", None)
        assert row["曲名"] == "", (title, row["曲名"])


def test_bracket_naming_a_member_or_the_group_is_not_a_song():
    assert members.bracket_song("ラストが神すぎる絵しりとり【シクフォニ×ハンドレッドノート】") is None
    assert members.bracket_song("曲名／歌ってみた【暇72×すち】") is None
    assert members.bracket_song("夏！花火！【夏恋センセイション】【マカロニえんぴつ】") == "夏恋センセイション"


# --- fetch_extra member-songs ---------------------------------------------


def test_member_sources_cover_all_six_members():
    assert list(fetch_extra.MEMBER_SOURCES) == ["暇72", "雨乃こさめ", "いるま", "LAN", "すち", "みこと"]
    assert "LANオリジナル曲" in fetch_extra.MEMBER_SOURCES["LAN"]["playlists"]
    assert fetch_extra.MEMBER_SOURCES["みこと"] == {"uploads": True}


def test_run_member_songs_reads_playlists_and_non_live_uploads():
    ids = {"channel": "UCsuchi0000000000000000", "illma": "UCillma00000000000000000"}
    suchi_song = make_video("s1", "【絵師が】踊／歌ってみた【すち】【シクフォニ】", "x", channel_id=ids["channel"])
    illma_playlist = make_video("i1", "曲名／だれか", "x", channel_id=ids["illma"])
    illma_short = make_video("i2", "あんま無責任なこと言うな？#未完成婚姻論", "", channel_id=ids["illma"])
    illma_live = make_video("i3", "配信アーカイブ #歌ってみた", "", channel_id=ids["illma"])
    illma_live["liveStreamingDetails"] = {"actualStartTime": "2026-01-01T00:00:00Z"}
    illma_talk = make_video("i4", "誰に似てますか？", "", channel_id=ids["illma"])
    entry_suchi = make_video("e1", "すちの動画", "x", channel_id=ids["channel"])
    entry_suchi["snippet"]["channelTitle"] = "すち"
    entry_illma = make_video("e2", "いるまの動画", "x", channel_id=ids["illma"])
    entry_illma["snippet"]["channelTitle"] = "いるま"

    videos = {v["id"]: v for v in (suchi_song, illma_playlist, illma_short, illma_live, illma_talk, entry_suchi, entry_illma)}
    playlists = {
        fb.PLAYLISTS["cover"]: ["e1", "e2"],
        fb.PLAYLISTS["original"]: [],
        "PLsuchi": ["s1"],
        "PLillma": ["i1"],
        "UU" + ids["illma"][2:]: ["i1", "i2", "i3", "i4"],
        "UUSH" + ids["channel"][2:]: ["sh1"],
    }
    # すちの再生リスト外のショート。長さは疑似動画の既定（45秒）でショート扱い。
    suchi_short = make_video("sh1", "夜に駆ける歌ってみた #夜に駆ける", "", channel_id=ids["channel"])
    videos["sh1"] = suchi_short
    listing = {
        ids["channel"]: [{"id": "PLsuchi", "snippet": {"title": "歌ってみた"}, "contentDetails": {"itemCount": 1}}],
        ids["illma"]: [{"id": "PLillma", "snippet": {"title": "Original (Solo)"}, "contentDetails": {"itemCount": 1}}],
    }
    base = fake_api(playlists, videos)

    def api_get(api_key, path, **params):
        if path == "playlists":
            return {"items": listing.get(params["channelId"], [])}
        return base(api_key, path, **params)

    original_api, original_key, original_argv = fb.api_get, fb.get_api_key, sys.argv
    fb.api_get, fb.get_api_key = api_get, lambda: "key"
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "member_songs.csv")
        sys.argv = ["fetch_extra.py", "member-songs", "--out", out]
        printed = io.StringIO()
        try:
            with redirect_stdout(printed):
                fetch_extra.main()
        finally:
            fb.api_get, fb.get_api_key, sys.argv = original_api, original_key, original_argv
        with open(out, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
    by_id = {r["video_id"]: r for r in rows}
    assert list(rows[0]) == members.MEMBER_FIELDS
    assert by_id["s1"]["曲名"] == "踊" and by_id["s1"]["メンバー"] == "すち"
    assert by_id["sh1"]["曲名"] == "夜に駆ける" and by_id["sh1"]["再生リスト"] == "", "再生リスト外のショートも拾う"
    assert by_id["i1"]["再生リスト"] == "Original (Solo)" and by_id["i1"]["category"] == "original"
    assert by_id["i2"]["曲名"] == "未完成婚姻論" and by_id["i2"]["曲名の出所"] == "ハッシュタグ"
    assert by_id["i2"]["再生リスト"] == ""
    assert "i3" not in by_id, "配信は含めない"
    assert by_id["i4"]["曲名"] == "" and "曲名を判定できない" in by_id["i4"]["要確認理由"]
    text = printed.getvalue()
    assert "配信 1 本" in text and "曲名が取れなかった動画" in text


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
