"""実際に YouTube Data API から取得した概要欄を、そのままテスト用に保持する。

歌詞セクションは長いため冒頭数行だけに切り詰めてあるが、
◆Lyrics が2回出てくるという構造はそのまま残している。
全角スペース・綴り揺れ(IIlustration)・ゼロ幅文字は原文どおり。
"""

COVER_SHOUJO_REI = {
    "id": "Y2MOUQY48_s",
    "snippet": {
        "title": "【とり憑かれた6人で】少女レイ / みきとP【Cover】【シクフォニ】",
        "publishedAt": "2026-08-31T10:00:06Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿愛し合えたら

××× 毎日更新＿＿＿現在464日目！ ×××

▼Cover Song Playlist
https://www.youtube.com/playlist?list=PLppXIlUC-oPw8uCDchVYal9ibApaYP-4R

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

▼本家様
みきとP 『 少女レイ 』 MV
https://youtu.be/JW3N-HvU0MA

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

運命を掴み取る最強の6人による2.5次元タレントグループ

Color：赤
暇72
https://x.com/hima72_25

Color：緑
すち
https://x.com/suchi_paint


◆Mix
ソノイ(In Fleur Inc.) 　( https://x.com/_Sonoi )

◆Instrumental
Studio Rabbits　( https://x.com/studio_rabbits )

◆Illustration
麺　( https://x.com/mendayooo )

◆Movie
MERO　( https://x.com/M3ro_pv )

※敬称略

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆スケジュール
長尺動画投稿 ▶ 週2　基本毎週火・金曜日
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄


#歌ってみた #少女レイ #みきとP #シクフォニ""",
    },
}

# ◆の並び順が上と逆。Instrumental は URL ではなく所属会社名が括弧に入る。
COVER_KYOURAN = {
    "id": "G7uwWGXB11s",
    "snippet": {
        "title": "【狂乱な共犯者で】狂乱 Hey Kids!! / THE ORAL CIGARETTES【Cover】【暇72×すち / シクフォニ】",
        "publishedAt": "2026-08-21T10:00:06Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿Tonight We honor the hero!!”

××× 毎日更新＿＿＿現在454日目！ ×××

▼本家様
＜ノラガミARAGOTO＞OPテーマ THE ORAL CIGARETTES「狂乱 Hey Kids!!」MusicVideo
https://youtu.be/C-o8pTi6vd8

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

運命を掴み取る最強の6人による2.5次元タレントグループ

Color：赤
暇72
https://x.com/hima72_25

◆Instrumental
呉井辰吉(SUPA LOVE)

◆Mix
kokoro no yami　( https://x.com/kny_mix )

◆Illustration
JIGENN　( https://x.com/JIGENN_x_ )

◆Movie
らる　( https://x.com/rc2lx )

※敬称略

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄


#歌ってみた #狂乱HeyKids #THEORALCIGARETTES #ノラガミ #シクフォニ""",
    },
}

# タイトルに U+200D が2つ入る。◆Lyrics が「クレジット」と「歌詞見出し」で2回出る。
ORIGINAL_SIX_NATION = {
    "id": "U-hMQG9kcqs",
    "snippet": {
        "title": "シクフォニ - SiX N4TioN ‍‍[Official Music Video]",
        "publishedAt": "2026-08-12T11:00:06Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿It all depends on you.

××× 毎日更新＿＿＿現在445日目！ ×××

▼Streaming & Download
https://nex-tone.link/A00224492

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

運命を掴み取る最強の6人による2.5次元タレントグループ

Color：赤
暇72
https://x.com/hima72_25


◆Music
ケンカイヨシ

◆Lyrics
ケンカイヨシ

◆Arrange
小木岳司

◆Basic Instruments Programming
ケンカイヨシ

◆Mix
藤浪 潤一郎　( https://x.com/2273xxx )

◆Edit
Satori

◆Illustration
すわだ　( https://x.com/suwada_yo )

◆Movie
スンセア　( https://x.com/sunsea2019 )


※敬称略
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆Lyrics

ジョーカーじゃ足りない!
エースじゃ、まだ満ちない!
その先には......。
(SiX N4TioN)

鼓動の先に観えるパノラマ
決意を知らぬバイアス

(以下、歌詞が100行以上続く)

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆スケジュール
長尺動画投稿 ▶ 週2　基本毎週火・金曜日
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄


#SiXN4TioN #シクフォニ #オリジナル曲""",
    },
}

# Original Song Playlist 所属だが ◆Music も ◆Lyrics も無い(メドレー)。
ORIGINAL_MEDLEY = {
    "id": "2wUgZh7B7fc",
    "snippet": {
        "title": "シクフォニ - SIXFONIA \"J to 3rd\" Archive Medley ‍‍[Official Music Video]",
        "publishedAt": "2026-08-10T10:00:06Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿どこまでも走れよ 朝も夜も超えて

××× 毎日更新＿＿＿現在443日目！ ×××

運命を掴み取る最強の6人による2.5次元タレントグループ

Color：赤
暇72
https://x.com/hima72_25

◆Instrumental
呉井辰吉(SUPA LOVE)

◆Arrange
呉井辰吉(SUPA LOVE)

◆Mix
赤ティン　( https://twitter.com/akatibitintin )

◆Edit
Satori

◆Illustration
こよせ　( https://x.com/koyose_ )

◆Movie
POhL　( https://x.com/BlurPohl )

※敬称略

#SIXFONIAJto3rdArchiveMedley #歌ってみた #メドレー #シクフォニ #オリジナル曲""",
    },
}

# ◆Lyrics に2人が「 / 」で併記される。◆Movie には URL が無い。
ORIGINAL_T4XI = {
    "id": "sZUSjWvxWXs",
    "snippet": {
        "title": "シクフォニ - T4xi DЯiver ‍‍[Official Music Video]",
        "publishedAt": "2026-06-06T10:00:06Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿海で洗浄

××× 毎日更新＿＿＿現在378日目！ ×××

運命を掴み取る最強の6人による2.5次元タレントグループ

Color：赤
暇72
https://x.com/hima72_25


◆Music
ふぁるすてぃ

◆Lyrics
ふぁるすてぃ / 暇72

◆Original Story
暇72

◆Arrange
ふぁるすてぃ

◆Mix
赤ティン　( https://x.com/akatibitintin )

◆Edit
安部良太

◆Illustration
鮫　( https://x.com/aa_832 )

◆Movie
やさね。


※敬称略
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆Lyrics

とある日の雑談
「──今日変なお客さん乗ってきてね」

(以下、歌詞が続く)

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄


 #T4xiDЯiver #シクフォニ #オリジナル曲""",
    },
}

# ラベルが「◆Main Animation ＆ IIlustration」(綴り揺れ + 全角＆)で、値が4行にわたる。
ORIGINAL_APRIL_FOOL = {
    "id": "eTWukuLut7c",
    "snippet": {
        "title": "シクフォニ - 今日もボクらは歩いてく ‍‍[Official Music Video]",
        "publishedAt": "2026-04-01T09:00:06Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿生きてるだけでOKじゃん

××× 毎日更新＿＿＿現在312日目！ ×××

運命を掴み取る最強の6人による2.5次元タレントグループ

Color：赤
暇72
https://x.com/hima72_25

◆Music
クレハリュウイチ

◆Lyrics
クレハリュウイチ

◆Arrange
クレハリュウイチ

◆Mix
赤ティン　( https://x.com/akatibitintin )

◆Edit
安部良太

◆Main Animation ＆ IIlustration
緒文　( https://x.com/shobo_n023 )
成田無限
重光亮摩 (mico.animation)　( https://mico-animation.co.jp/ )
稗苗 一糸

◆Dance Animation
斜め　( https://x.com/4nanome )

◆Movie
骨付きくぁるび　( https://x.com/SAN_Q_SAN )

◆Cast
27丸(つなまる)　 暇72
ここサメ　　雨乃こさめ

※エイプリルフール企画です。
※敬称略
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆Lyrics

バタバタバタ uh バタバタバタ yeah
ギリギリギリ oh ギリギリギリ hey

(以下、歌詞が続く)

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄


#今日もボクらは歩いてく #シクフォニ #オリジナル曲 #エイプリルフール""",
    },
}

COVERS = [COVER_SHOUJO_REI, COVER_KYOURAN]
ORIGINALS = [ORIGINAL_SIX_NATION, ORIGINAL_MEDLEY, ORIGINAL_T4XI, ORIGINAL_APRIL_FOOL]
ALL_SAMPLES = [(v, "cover") for v in COVERS] + [(v, "original") for v in ORIGINALS]


# メドレー動画。曲名は1つに決まらず、▼本家様 欄に曲が並ぶ（実物は26曲。ここでは表記の型が違う6曲だけ残した）。
# publishedAt は取得していないためダミー（テストは日付を見ない）。ALL_SAMPLES には入れない。
COVER_ANISON_MEDLEY = {
    "id": "JaFgv0Ovz8A",
    "snippet": {
        "title": "【アニソン組曲】超有名アニソン勝手に選んでメドレーにしたら神過ぎた件ｗｗｗｗｗｗ【アニソンメドレー】【Cover】【シクフォニ】",
        "publishedAt": "2000-01-01T00:00:00Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿少年よ 神話になれ

▼TikTokメドレー　2022Ver.
https://youtu.be/qobAdZm39Rc

▼Cover Song Playlist
https://www.youtube.com/playlist?list=PLppXIlUC-oPw8uCDchVYal9ibApaYP-4R 
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

▼本家様

TVアニメ「ONE PIECE」1000話記念：ウィーアー！
https://youtu.be/dM7x1PNZDo0

デジモンアドベンチャー オープニング映像 / 和田光司「Butter-Fly」
https://youtu.be/32JTFI0alPk

めざせポケモンマスター
https://youtu.be/E_BsL8_cFnE

LiSA『紅蓮華』-MUSiC CLiP-（アニメ「鬼滅の刃」竈門炭治郎 立志編 オープニングテーマ）
https://youtu.be/x1FV6IrjZCY

DAN DAN 心魅かれてく
https://field-of-view.jp/
※正式なYoutubeリンクが見つからなかったため、公式HPを記載させていただきます。

「残酷な天使のテーゼ」MUSIC VIDEO（HDver.）/Zankoku na Tenshi no Te-ze“The Cruel Angel's Thesis”
https://youtu.be/o6wtDPVkKqI

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

運命を掴み取る最強の6人による2.5次元タレントグループ

◆Arrange
show　( https://x.com/boogie_d_box )

◆Illustration
灰色ルト　( https://x.com/luto_gray000 )

◆Movie
骨付きくぁるび　( https://x.com/SAN_Q_SAN )

※敬称略
""",
    },
}


# 実データ(2026-09-20 取得)から取ったサンプル。歌詞は◆Lyrics 見出しの直後で切ってある。
# publishedAt は投稿日(JST)だけ復元した値で、時刻は実物と違う。テストは日付を見ない。
ORIGINAL_MUSIC_AND_LYRICS = {
    "id": "veWr0v_EFL8",
    "snippet": {
        "title": "シクフォニ - Desperate Track [Official Music Video]",
        "publishedAt": "2024-01-20T00:00:00Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿死に物狂いで勝ち取れ!!!!!

▼Streaming & Download
https://nex-tone.link/A00178760

▼Original Song Playlist
https://youtube.com/playlist?list=PLppXIlUC-oPw5Giv-JPWi_5DjstLk3ML2&si=cGRNiCOP6KBTMRX5

▼Inst音源＆ガイドライン
https://www.dropbox.com/scl/fo/kiel7w6tnuov1e5vvry3m/h?rlkey=5wb2u9ngtjlaj6n9413360udn&dl=0

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

運命を掴み取る最強の6人による歌い手グループ

▼2022.08.12.Start.
公式X(旧:Twitter)
https://twitter.com/sixfonia_info

Color：赤
暇72
https://twitter.com/hima72_25
https://www.youtube.com/c/hima72
https://twitcasting.tv/hima72_25

Color：水色
雨乃こさめ
https://twitter.com/amam_frfr_
https://www.youtube.com/c/amenokosame
https://twitcasting.tv/c:amam_frfr_

Color：紫
いるま
https://twitter.com/illmaill
https://www.youtube.com/c/illma
https://twitcasting.tv/illmaill

Color：ピンク
LAN
https://twitter.com/lanlanutau
https://www.youtube.com/c/LANlanutau
https://twitcasting.tv/lanlanutau

Color：緑
すち
https://twitter.com/suchi_paint
https://www.youtube.com/c/suchi_paint
https://twitcasting.tv/suchi_paint

Color：黄色
みこと
https://mobile.twitter.com/mikoto_miko11
https://www.youtube.com/c/mikoto11
https://twitcasting.tv/mikoto_miko11


◆Music&Lyrics
ケンカイヨシ

◆Arrange
ケンカイヨシ

◆Mix
赤ティン　( https://twitter.com/akatibitintin )

◆Illustration
すわだ　( https://twitter.com/suwada_yo )

◆Movie
スンセア　( https://twitter.com/sunsea2019 )

◆サムネデザイン
すち


※敬称略
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆Lyrics

【1A】
挑戦しなきゃ意味ないじゃん 一度きりの命なら
回り道も 高笑いで 乗り越えるさ
瞬間に賭けたいじゃん 一度きりの人生だし
トップギアで 限界なんて意味ないから

【1B】
We go!!!
一か八か ハンかチョウか の 勝負
そりゃないな! なんて展開も全部 糧にgoin go
最底辺の屈辱 we're gonna 勝利も苦労
何も知らない奴らには言わせとけ!

自分の霊感に従え!
脅威に負けるな 喰らい
""",
    },
}

ORIGINAL_MUSIC_LYRICS_AND_RAP = {
    "id": "wyairCK8JtI",
    "snippet": {
        "title": "シクフォニ - アンダーリズムサーカス [Official Music Video]",
        "publishedAt": "2023-10-28T00:00:00Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿俺達が王道

▼Streaming & Download
https://nex-tone.link/A00178756

▼Original Song Playlist
https://youtube.com/playlist?list=PLppXIlUC-oPw5Giv-JPWi_5DjstLk3ML2&si=cGRNiCOP6KBTMRX5

▼Inst音源＆ガイドライン
https://www.dropbox.com/scl/fo/tk7c470as3kxgywi3swja/h?rlkey=89pjemfjeh8wqlkb0yv352i9c&dl=0

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

運命を掴み取る最強の6人による歌い手グループ

▼2022.08.12.Start.
公式Twitter ( https://twitter.com/sixfonia_info )

Color：赤
暇72
https://twitter.com/hima72_25
https://www.youtube.com/c/hima72
https://twitcasting.tv/hima72_25

Color：水色
雨乃こさめ
https://twitter.com/amam_frfr_
https://www.youtube.com/c/amenokosame
https://twitcasting.tv/c:amam_frfr_

Color：紫
いるま
https://twitter.com/illmaill
https://www.youtube.com/c/illma
https://twitcasting.tv/illmaill

Color：ピンク
LAN
https://twitter.com/lanlanutau
https://www.youtube.com/c/LANlanutau
https://twitcasting.tv/lanlanutau

Color：緑
すち
https://twitter.com/suchi_paint
https://www.youtube.com/c/suchi_paint
https://twitcasting.tv/suchi_paint

Color：黄色
みこと
https://mobile.twitter.com/mikoto_miko11
https://www.youtube.com/c/mikoto11
https://twitcasting.tv/mikoto_miko11


◆Music&Lyrics
ふぁるすてぃ

◆Arrange
ふぁるすてぃ

◆Rap Lyrics
いるま

◆Mix
赤ティン　( https://twitter.com/akatibitintin )

◆Illustration
こよせ　( https://twitter.com/koyose_/media )

◆Movie
スンセア　( https://twitter.com/sunsea2019 )

◆サムネデザイン
すち


※敬称略
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆Lyrics

1
静粛に傾聴　万物は掌　嗚呼
冴えないその面を拝んで
人生ただGエンドです
簡単な謎解き　潜在的傀儡をなして
地獄のような現世に堕ちて
ハッピーエンド　退屈なララバイ

ラップ
傍観してりゃ My turn
悦んで道化と化す
条件問わず
タブー常套大胆なスタンスで
根底から覆す森羅万象

悪態にも似たブラフか妄言
輪廻さえも捨てて課した証明
巧妙なTrapには気づけない
悦にイッた Audience

サビ
踊れ
""",
    },
}

ORIGINAL_LYRICS_AND_RAP = {
    "id": "vOliM2VtKDc",
    "snippet": {
        "title": "シクフォニ - シンギュロイド [Official Music Video]",
        "publishedAt": "2025-07-26T00:00:00Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿嘘じゃない感情


▼Streaming & Download
https://nex-tone.link/A00198237

▼Original Song Playlist
https://www.youtube.com/playlist?list=PLppXIlUC-oPw5Giv-JPWi_5DjstLk3ML2

▼Inst音源＆ガイドライン
https://www.dropbox.com/scl/fo/rq4n5x5hkjf90i98lpudo/AHsos6NlwamhjMgRBIxLgtI?rlkey=j9xmy9zdmjopzoeyxtt07rwza&st=b77wppd7&dl=0

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

運命を掴み取る最強の6人による2.5次元タレントグループ

▼2022.08.12.Start.
公式X(旧:Twitter)
https://x.com/sixfonia_info 

Color：赤
暇72
https://x.com/hima72_25
https://www.youtube.com/c/hima72
https://twitcasting.tv/hima72_25

Color：水色
雨乃こさめ
https://x.com/amam_frfr_
https://www.youtube.com/c/amenokosame
https://twitcasting.tv/c:amam_frfr_

Color：紫
いるま
https://x.com/illmaill
https://www.youtube.com/c/illma
https://twitcasting.tv/illmaill

Color：ピンク
LAN
https://x.com/lanlanutau
https://www.youtube.com/c/LANlanutau
https://twitcasting.tv/lanlanutau

Color：緑
すち
https://x.com/suchi_paint
https://www.youtube.com/c/suchi_paint
https://twitcasting.tv/suchi_paint

Color：黄色
みこと
https://x.com/mikoto_miko11
https://www.youtube.com/c/mikoto11
https://twitcasting.tv/mikoto_miko11


◆Music
ふぁるすてぃ

◆Lyrics
ふぁるすてぃ

◆Rap Lyrics
いるま

◆Arrange
ふぁるすてぃ

◆Mix
赤ティン　( https://x.com/akatibitintin )

◆Edit
安部良太

◆Illustration
めつぶしあんこ　( https://x.com/YUDEAZUKING_ )

◆Movie
ねびる　( https://x.com/n_prol )


※敬称略

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆Lyrics

『What are emotions?』

1
混がらがった感傷を歌う
ブリキ照らす部屋
無人の輪 御手を拝借
我ら主となるヒトの為
青い肌の僕等が声を鳴らす

戦争 貧困 残酷なsugar yummyとなって
刈り剃りたい やめたい ブリキの僕等を裂いた
逆らっても脳浸透 シグナルバグって
プログラムか？ 偽って合唱！

サビ.
これが僕等の活きるサクシード
我ら電子で哭くシンギュロイド
青いヒカリに揺られて
""",
    },
}

COVER_RAP_ONLY = {
    "id": "LhH_6IP8CVU",
    "snippet": {
        "title": "【腐り絶えた3人で】ラブカ？ / 柊キライ【Cover】【暇72×いるま×すち / シクフォニ】",
        "publishedAt": "2025-08-01T00:00:00Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿腐る愛 愛 愛か？

▼Cover Song Playlist
https://www.youtube.com/playlist?list=PLppXIlUC-oPw8uCDchVYal9ibApaYP-4R

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

▼本家様
ラブカ？ / 柊キライ feat.flower
https://youtu.be/1Esz9ONM9X8

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

運命を掴み取る最強の6人による2.5次元タレントグループ

▼2022.08.12.Start.
公式X(旧:Twitter)
https://x.com/sixfonia_info 

Color：赤
暇72
https://x.com/hima72_25
https://www.youtube.com/c/hima72
https://twitcasting.tv/hima72_25

Color：水色
雨乃こさめ
https://x.com/amam_frfr_
https://www.youtube.com/c/amenokosame
https://twitcasting.tv/c:amam_frfr_

Color：紫
いるま
https://x.com/illmaill
https://www.youtube.com/c/illma
https://twitcasting.tv/illmaill

Color：ピンク
LAN
https://x.com/lanlanutau
https://www.youtube.com/c/LANlanutau
https://twitcasting.tv/lanlanutau

Color：緑
すち
https://x.com/suchi_paint
https://www.youtube.com/c/suchi_paint
https://twitcasting.tv/suchi_paint

Color：黄色
みこと
https://x.com/mikoto_miko11
https://www.youtube.com/c/mikoto11
https://twitcasting.tv/mikoto_miko11


◆Mix
よしけん　( https://x.com/yoshi_kennn )

◆Edit
安部良太

◆Illustration
麻呂田まろ　( https://x.com/Maaroso_09 )

◆Movie
くすみ　( https://x.com/qusmi_ )

◆RAP  Lyrics
いるま

※敬称略

【RAP  Lyrics】
香り立つ方に強引
超ディープなルール
Tick tock多分解明できぬラブイズム
魅惑の罠フリル
単なるワナビー
じゃあ、どっちが正しい？
知りたいこと何？
love love love
けど知らない方がマシ？
blah blah blah
また血肉剥がれた石ころがfloat
次のラブは逃がせない

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆スケジュール
動画投稿 ▶ 毎週火・金曜日
ツイキャス生放送 ▶ 月曜日～土曜日 20時~
公式You
""",
    },
}

COVER_ILLUSRATION_TYPO = {
    "id": "FFvgmsWle3U",
    "snippet": {
        "title": "【立ち向かう6人で】プライド革命 / CHiCO with HoneyWorks【Cover】【シクフォニ】",
        "publishedAt": "2026-05-16T00:00:00Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿理由なら君にもらった

××× 毎日更新＿＿＿現在357日目！ ×××

▼Cover Song Playlist
https://www.youtube.com/playlist?list=PLppXIlUC-oPw8uCDchVYal9ibApaYP-4R

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
▼本家様
プライド革命 ／ CHiCO with HoneyWorks
https://youtu.be/EYiNo2kLAHw
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

運命を掴み取る最強の6人による2.5次元タレントグループ

▼2022.08.12.Start.
公式X(旧:Twitter)
https://x.com/sixfonia_info 

Color：赤
暇72
https://x.com/hima72_25
https://www.youtube.com/c/hima72
https://twitcasting.tv/hima72_25

Color：水色
雨乃こさめ
https://x.com/amam_frfr_
https://www.youtube.com/c/amenokosame
https://twitcasting.tv/c:amam_frfr_

Color：紫
いるま
https://x.com/illmaill
https://www.youtube.com/c/illma
https://twitcasting.tv/illmaill

Color：ピンク
LAN
https://x.com/lanlanutau
https://www.youtube.com/c/LANlanutau
https://twitcasting.tv/lanlanutau

Color：緑
すち
https://x.com/suchi_paint
https://www.youtube.com/c/suchi_paint
https://twitcasting.tv/suchi_paint

Color：黄色
みこと
https://x.com/mikoto_miko11
https://www.youtube.com/c/mikoto11
https://twitcasting.tv/mikoto_miko11


◆Mix
ソノイ(In Fleur Inc.) ( https://x.com/_Sonoi )

◆Illusration
トウカ　( https://x.com/Touka_moru04 )

◆Movie
NEFTED　( https://x.com/nefted_info )

※敬称略

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆スケジュール
動画投稿 ▶ 毎週火・金曜日
ツイキャス生放送 ▶ 月曜日～土曜日 20時~
公式YouTube LIVE ▶ 日曜日 20時~
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄


#歌ってみた #プライド革命 #honeyworks #シクフォニ
""",
    },
}

COVER_THUMBNAIL_ILLUST_ONLY = {
    "id": "peL6oPKimIQ",
    "snippet": {
        "title": "【圧倒的王子二人で】ロウワー / ぬゆり【Cover】【すち×みこと / シクフォニ】",
        "publishedAt": "2022-09-25T00:00:00Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿僕の生きているすべてを確かめて

▼Cover Song Playlist
https://youtube.com/playlist?list=PLppXIlUC-oPw8uCDchVYal9ibApaYP-4R&si=AQwvQIBn1zMH2ibU

×××チャンネル登録3万人企画挑戦中×××

9/29(木) 23:59までに

▼達成の場合
記 念 グ ッ ズ 発 売

▼未達成の場合
販 売 数 3 個

▼詳細はこちら
https://twitter.com/sixfonia_info/status/1568933179289124865

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

▼本家様
ロウワー / Flower - Lower one's eyes
https://youtu.be/3sEptl-psU0

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

超大型オーディションを潜り抜けた6人による最強の新人歌い手グループ

▼2022.08.12.Start.
公式Twitter ( https://twitter.com/sixfonia_info )

Color：赤
暇72
https://twitter.com/hima72_25
https://www.youtube.com/c/hima72
https://twitcasting.tv/hima72_25

Color：水色
雨乃こさめ
https://twitter.com/amam_frfr_
https://www.youtube.com/c/amenokosame
https://twitcasting.tv/c:amam_frfr_

Color：紫
いるま
https://twitter.com/illmaill
https://www.youtube.com/c/illma
https://twitcasting.tv/illmaill

Color：ピンク
LAN
https://twitter.com/lanlanutau
https://www.youtube.com/c/LANlanutau
https://twitcasting.tv/lanlanutau

Color：緑
すち
https://twitter.com/suchi_paint
https://www.youtube.com/c/suchi_paint
https://twitcasting.tv/suchi_paint

Color：黄色
みこと
https://mobile.twitter.com/mikoto_miko11
https://www.youtube.com/c/mikoto11
https://twitcasting.tv/mikoto_miko11


◆Vocal
すち
みこと

◆Mix
赤ティン　( https://twitter.com/akatibitintin )

◆サムネイラスト
ねぽ　( https://twitter.com/neponepo216 )


※敬称略
  

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆スケジュール
動画投稿 ▶ 毎週火・金・土曜日
ツイキャス生放送 ▶ 月曜日～土曜日 20時~
公式Youtube LIVE ▶ 日曜日 20時~
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄


#プロセカ #ロウワー #ぬゆり #シクフォニ #歌ってみた
""",
    },
}

COVER_TWO_HONKE_NOT_MEDLEY = {
    "id": "8qmSgqZok5E",
    "snippet": {
        "title": "【今夏も6人で】夏祭り / JITTERIN'JINN, Whiteberry【Cover】【シクフォニ】",
        "publishedAt": "2025-08-30T00:00:00Z",
        "channelTitle": "シクフォニ【SIXFONIA】",
        "description": """＿＿＿遠い夢の中

▼Cover Song Playlist
https://www.youtube.com/playlist?list=PLppXIlUC-oPw8uCDchVYal9ibApaYP-4R

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

▼本家様
ジッタリン・ジン / 夏祭り ( Jitterin’ Jinn / Natsumatsuri )【MV】
https://youtu.be/BFvdvIFsvPg

Whiteberry「夏祭り」MUSIC VIDEO
https://youtu.be/AZRR01YOKcM

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

運命を掴み取る最強の6人による2.5次元タレントグループ

▼2022.08.12.Start.
公式X(旧:Twitter)
https://x.com/sixfonia_info 

Color：赤
暇72
https://x.com/hima72_25
https://www.youtube.com/c/hima72
https://twitcasting.tv/hima72_25

Color：水色
雨乃こさめ
https://x.com/amam_frfr_
https://www.youtube.com/c/amenokosame
https://twitcasting.tv/c:amam_frfr_

Color：紫
いるま
https://x.com/illmaill
https://www.youtube.com/c/illma
https://twitcasting.tv/illmaill

Color：ピンク
LAN
https://x.com/lanlanutau
https://www.youtube.com/c/LANlanutau
https://twitcasting.tv/lanlanutau

Color：緑
すち
https://x.com/suchi_paint
https://www.youtube.com/c/suchi_paint
https://twitcasting.tv/suchi_paint

Color：黄色
みこと
https://x.com/mikoto_miko11
https://www.youtube.com/c/mikoto11
https://twitcasting.tv/mikoto_miko11


◆Mix
赤ティン　( https://x.com/akatibitintin )

◆Edit
kokoro no yami

◆Instrumental    
ハイカラサウンド　( https://x.com/highkarasound )

◆Illustration
Lumino　( https://x.com/mskmmti )

◆Movie
ナデコ　( https://x.com/natadecoco_cas )

※敬称略


┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
◆スケジュール
動画投稿 ▶ 毎週火・金曜日
ツイキャス生放送 ▶ 月曜日～土曜日 20時~
公式YouTube LIVE ▶ 日曜日 20時~
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄


#歌ってみた #夏祭り #jitterinjinn #whiteberry #シクフォニ
""",
    },
}

