# Glossary: Hamster Club

Approved by the project lead on 2026-10-30 ("Everything looks good!"): every former ASK item
stands as drafted. Use these terms everywhere.

Script-specific choices made while translating the event script (2026-10-30):
- Rival boy's silences are "……"; ellipses inside lines are the one-tile "…".
- Shop main menu: Shop / Show off / Heal (was Treat; changed 2026-11-02 at the project lead's request so it doesn't clash with the food "Treats").
- Food menus: Pellets+ / Fruit+ / Veggies+ for the premium tier (a "+" glyph was
  added to the font), Corn; amounts Normal / A little / Plenty.
- Bean menus: GutsBean / HopBean / DashBean (Stamina / Jump / Speed) and
  SilkBean / CuteBean / LookBean (Coat / Cuteness / Looks). This replaces the
  ShinyBn / Sparkle / Bouncy forms below.
- Buy menus in a single column: Buy / Don't buy.
- The player's insult option ムカツクね〜ちゃん is "You're a pest!", and the rival
  girl's reply turns the word "pest" back on the player's hamster.
- Lost-hamster search spots: Dresser / Rack / Curtains / Desk.

Space limits that shape these choices:
- Dialogue boxes are 18 characters × 2 lines (fixed-width 8 px font, like the
  Game Boy Pokémon games).
- Menu options in dialogue are **8 characters max** (two columns per line).
- Names the player types are 8 characters max.
- Item, food and trick tables outside the script have their own fixed widths
  (to be measured when they're dumped). Where the dialogue name doesn't fit a
  menu, the "Menu form" column gives the short form.

## Titles, places, events

| Japanese | Reading | English | Menu form | Kind | Notes |
|---|---|---|---|---|---|
| ハムスター倶楽部 / ハムスターくらぶ | Hamusutā Kurabu | Hamster Club | | title, shop | The shop shares the game's name. "Welcome to the Hamster Club!" |
| HAM'Sカップ | Hamuzu Kappu | HAM'S Cup | HAM'S Cup | event | Romanized like this in the ROM itself. Hamster-only competitions, ranked. |
| ブリーダーズカップ | Burīdāzu Kappu | Breeders' Cup | Breeders' | event | Owner takes part too. Generic phrase, no conflict with the horse race in context. |
| ブリーダーマスター | Burīdā Masutā | Breeder Master | | title | Top rank of the Breeders' Cup, "the most respected". |
| スぺシャルカップ | Supesharu Kappu | Special Cup | | event | Final showdown with the rival girl. |
| プリティーカップ | Puritī Kappu | Pretty Cup | | event | Cuteness contest (announcer script). |
| ラブリーコンテスト | Raburī Kontesuto | Lovely Contest | Lovely | event | The announcer calls it あいきょうたいしょう, "the Charm Awards". |
| かえるとびコンテスト | kaerutobi kontesuto | Leapfrog Contest | | event | Jumping contest. Approved: "Leapfrog". |
| 100Mそう / ひろいぐいレース / 30Mうんてい / タネキャッチ / まわしぐるまレース | | 100m Dash / Snack Race / Monkey Bars / Seed Catch / Wheel Race | 100m Dash / Snack / Bars / Seeds / Wheel | event | The athletics events. Banners and help titles use the full names; the 9-column contest list uses the menu forms (2026-11-02; before that the list said Snack Run / Bar Hang / Seed Grab / Wheel Run, which didn't match the banners). Lovely Contest / Pretty Cup are "Lovely" / "Pretty" in the list. |
| あいきょうしょうぶ / うんどうしょうぶ | aikyō/undō shōbu | Charm match / Athletics match | | event type | The two contest categories. |
| ランク / ランクアップ | ranku | Rank / Rank up! | | system | Rank 1-5 ("さいしょはランク2まで"). |
| ランクポイント | ranku pointo | Rank Points | | system | |
| しょうきん | shōkin | Prize money | | UI | |
| おこづかい | okozukai | allowance | | system | Pocket money from the player's parents. Keep the kid-life flavor. |
| G | | G | | currency | The game's own unit (e.g. 5000G). Not yen, so leave as G. |

## People (unnamed in the game)

None of the humans have names in the text. Refer to them by role in notes, never
invent names on screen.

| Japanese | English (notes only) | Notes |
|---|---|---|
| ショップのおねえさん | Shop owner | Runs the Hamster Club. |
| (rich girl) | Rival girl | Ojou-sama rival with Josephine. |
| (stoic boy) | Rival boy | The cool, quiet one. |

## Hamsters with names

| Japanese | English | Notes |
|---|---|---|
| しげっち | Shigechi | Starter. っち is a cutesy nickname suffix (cf. Tamagotchi). "Shigetchi" is 9 letters and names hold 8, so drop one letter. |
| ぷーちゃん | Pū-chan → **Pu-chan** | Starter. Macron dropped: no ū in the font. |
| えんどーくん | Endō-kun → **Endo-kun** | Starter. Named like a classmate; the joke works as-is. |
| ジョセフィーヌ | Josephine | Rival girl's champion. French-style name in JP, so the English spelling. |
| オスカーくん | Oscar-kun | Rival girl's gift hamster. Check the name fits the stored-name limit. |
| マロン, グリ, モカ, ... | Marron, Guri, Mocha, ... | NPC hamsters in contests. Full list when that table is dumped. |

## Honorifics and nicknames (see characters.md for policy)

| Japanese | English | Notes |
|---|---|---|
| さん / クン / ちゃん / よびすて | -san / -kun / -chan / No title | The player picks how the shop owner addresses them. The menu stays. Options: " -san", " -kun", " -chan", " None". |
| <name>っち | <name>-chi | What the rival girl calls the player. Same suffix as Shigechi, so it's consistent. |
| せつめいくん | Mr. Explainer | Rival girl's "せつめいくん、スイッチオン！" gag: "Mr. Explainer, switch on!" |

## Hamster breeds

| Japanese | English | Menu form (≤8) | Notes |
|---|---|---|---|
| ジャンガリアン | Djungarian | Djungar. | Japanese pet-trade name. English pet trade also says Winter White. Keep Djungarian (what the game says). Menu form approved. |
| ゴールデン | Golden | Golden | Syrian. |
| ロボロフスキー | Roborovski | Robo | "Robo" is the usual hobbyist nickname. |
| キャンべル | Campbell's | Campbell | |
| チャイニーズ | Chinese | Chinese | |
| クロハラ(ハムスター) | Black-bellied (hamster) | B-Belly | The European/common hamster. Can't breed in game. |
| 〜けいのハムスター | a ...-type hamster | | |
| うまれたてのオス/メス | newborn male/female | Baby ♂ / Baby ♀ | Font has ♂♀. |
| そだっているオス/メス | grown male/female | Adult ♂ / Adult ♀ | |

## Care and stats

| Japanese | Reading | English | Notes |
|---|---|---|---|
| いくせい | ikusei | raising | "raising tips" for いくせいのコツ. |
| ちょうきょう | chōkyō | training | The weekly training menu. |
| しつけ / しつける | shitsuke | (house-)training / train | Toilet and nest-building training. |
| すづくり | suzukuri | nest-building | |
| さんぽ | sanpo | walk | |
| おていれ | oteire | grooming | |
| きげん | kigen | mood | |
| たいちょう | taichō | health | |
| なつく | natsuku | be attached / friendly | "よくなついている" = "really attached to you". |
| うんどう(のうりょく) | undō | Athletics | Stat group. |
| あいきょう(のうりょく) | aikyō | Charm | Stat group. |
| たいりょく | tairyoku | Stamina | |
| すばやさ | subayasa | Speed | |
| ジャンプ | janpu | Jump | |
| けヅヤ | kezuya | Coat | Fur gloss. |
| かわいさ | kawaisa | Cuteness | |
| ようし | yōshi | Looks | |
| かしこさ | kashikosa | Smarts | |
| VCM / ビタミン カロリー ミネラル | | VCM / Vitamins, Calories, Minerals | The letters stay; luckily they work in English. |
| わざ | waza | trick | Contest tricks (おすわり = Sit, あくび = Yawn, ...). |
| はんしょく | hanshoku | breeding | |
| あいしょうチェック | aishō chekku | Compatibility check | |
| ひきとる | hikitoru | take in (shop takes a hamster back) | "Give up" from the player's side. |
| ちりょう | chiryō | treatment | Shop menu "Heal": heal a sick hamster. |

## Shop

| Japanese | English | Menu form (≤8) | Notes |
|---|---|---|---|
| かいもの / みてみて / ちりょう | Shop / Show her / Heal | Shop, Show, Heal | Shop owner's main menu. みてみて = "look, look!" (show her a hamster). |
| アイテム / エサ / ケージ / ハムスター | Items / Food / Cages / Hamsters | Items, Food, Cages, Hamsters | "Hamsters" is exactly 8. |
| きほんアイテム / とくしゅアイテム | Basic items / Special items | Basic, Special | |
| かう / かわない | Buy / Don't buy | Buy, Pass | |
| ほかのケージ | Other cages | Others | |
| つぎへ / まえへ | Next / Back | Next, Back | |
| すばこ | nest box | Nest box | |
| みずいれ / みずのみ | water bottle | Water | |
| まわしぐるま | wheel | Wheel | |
| トイレ | toilet | Toilet | Hamster litter corner. "Toilet" is what English hamster guides say too. |
| すべりだい / シーソー | slide / seesaw | Slide, Seesaw | Level 2/3 toys. |
| レべル1-3 | Level 1-3 | Lv.1 | |
| ハムスターボール | Hamster Ball | HamBall | 8-character menu problem. |
| ブラシ | Brush | Brush | |

## Food

| Japanese | English | Menu form (≤8) | Notes |
|---|---|---|---|
| エサ | food | Food | |
| やすいエサ / たかいエサ / こうきゅうフード / ごちそう | Cheap food / Pricey food / Gourmet food / Treats | Cheap, Pricey, Gourmet, Treats | Shop food tiers. |
| それなりに / すこしだけ / たっぷりと | a normal amount / just a little / plenty | Normal, A little, Plenty | Purchase sizes. |
| ぺレット / スーパーぺレット | Pellets / Super Pellets | Pellets, SuperPel | |
| くだもの / ぜいたくくだもの | Fruit / Luxury Fruit | Fruit, LuxFruit | |
| ヤサイ / たかいヤサイ | Veggies / Fancy Veggies | Veggies, FancyVeg | |
| ひまわりのタネ | Sunflower Seeds | Seeds | |
| と〜もろこし | Corn | Corn | The 〜 is a playful drawl in the source ("cooorn"). Plain "Corn" fits better. |
| へルシーとうふ | Healthy Tofu | Tofu | Keep tofu (Japanese staple). |
| チーズ | Cheese | Cheese | |
| ガッツ/ダッシュ/ぴょっこんマメ | Guts / Dash / Hop Bean | GutsBean, DashBean, HopBean | Stat beans (Stamina / Speed / Jump). |
| つやつや/ぴかぴか/ぷりぷりマメ | Shiny / Sparkle / Bouncy Bean | ShinyBn, Sparkle, Bouncy | Coat / Cuteness / Looks. |
| カップアイス | Ice Cream Cup | Ice Cup | |
| にぼし / ニボシ | niboshi (dried sardines) | Niboshi | Keep the Japanese snack. Shop line adds the context: "Dried sardines, full of nutrients." |

## Cages

| Japanese | English |
|---|---|
| ケージ / カゴ | cage |
| ノーマルケージ1-3 | Normal Cage 1-3 |
| ラージケージ | Large Cage |
| へビーケージ | Heavy Cage |
| アイテムケージ | Item Cage |
| ハムスターケージ | Hamster Cage |
| プラスチックケージ | Plastic Cage |
| プラスチック2だんケージ | Two-Story Plastic Cage |
| はんしょくケージ | Breeding Cage |
| うんどうケージ | Exercise Cage |
| あいきょうケージ | Charm Cage |
| ピラミッドケージ | Pyramid Cage ("ピラミッドパワー" = pyramid power, keep the 90s fad) |
| きんみらいスーパーケージ | Future Super Cage |

## Recurring phrases

| Japanese | English | Notes |
|---|---|---|
| いらっしゃいませ | Welcome! | Shop greeting. |
| ありがとうございました | Thank you! Come again! | |
| ごきげんよう | Good day! / Ta-ta! | Rival girl's sign-off. See characters.md. |
| お〜ほっほっほっほっほっほっ！ | Oh-ho-ho-ho-ho-ho! | Ojou-sama laugh. Keep the full length. |
| また、あおう。 | We'll meet again. | Rival boy's catchphrase. Always the same English. |
| ・・・・・・・・・・・・・・・。 | ...... | Rival boy's silences. Use one consistent "......" |
| ムカッ / ムカツク | (annoyed) "Grr!" / "jerk" | Player's reaction and insult option. |
