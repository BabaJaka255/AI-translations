# English script, keyed by the Japanese text as dumped (out/script.json).
# Dialogue windows are 24 letters wide (12 kanji cells, 2 letters per cell), 2 lines per page.
# '\n' forces a new line. Control codes: {A0} {B0} {B1} {B2} {B3} {V0}..{V6} {NUM} (one cell each).
# Glossary (follows Super Legend of the River King): ぬし = the River King, 寄せえ = chum, びく = creel,
# たらい = tub, ぬしえさ = King bait, ぬし針 = King hook, ぬし竿 = King rod, 体力 = HP, 経験値 = EXP,
# 磁石 = compass, めがね = glasses, 洞穴 = cave, 京子 = Kyoko (the hero's little sister).
# Baits: 川虫 = caddis, ねりえ = paste bait (menu "Paste"), 赤虫 = midge (larva), さし = maggot, みみず = worm.
# Items (menu names): めがね specs, 磁石 magnet, 花火 sparks, 斧 axe, 鍵 key, たらい tub, ぱん bun,
# もち cake, いも spud, 牛乳 milk, あめ mint, りんご apple.

DIALOGUE = {
# --- intro (main program) ---
"山奥の　せせらぎから　　端を発した流れは　渓谷を下り　しだいに川幅を　　増していく。　　　　　　やがて　ゆるやかになった流れは　数多くの沼や　　湿地帯の間を通って　　　蛇行しながら流れ下る。":
"From a babbling brook high in the mountains, a river runs down through the gorges, growing wider as it goes. Then, slowing, it winds its way on past countless ponds and wetlands.",
"一方　川の中では数多くの種類の魚が　元気よく　　泳ぎ回っていた。　　　　なかでも　ぬしと呼ばれている魚は　強すぎて　まだ誰も　釣りあげる事が出来なかった。":
"In the river, fish of all kinds swam about. One of them, called the River King, was so strong that nobody had ever managed to land it.",
"そして　村では毎日　平穏な日々が　続いていた。　ところが　ある日のこと　釣り好きの　少年の妹が　突然　高熱を出して倒れてしまいました・・・。":
"Life in the village went on peacefully, day after day. Then one day, the sister of a boy who loved to fish fell ill with a high fever...",
# old copy of the intro (unused program, sector 4)
"一方　川の中では数多くの種類の魚が　元気よく　　泳ぎ回っていた。　　　　なかでも　ぬしと呼ばれている魚は　強くてまだ誰も釣る事が出来なかった。":
"In the river, fish of all kinds swam about. One of them, called the River King, was so strong no one had ever caught it.",
"ところが　ある日　少年の妹が　急に高熱を出して　寝込んでしまいました。　釣り好きの少年は　　　　心配で　心配で　　　　　たまりませんでした。":
"Then one day a boy's little sister fell ill with a high fever. The boy, who loved to fish, was worried sick.",

# --- field messages ---
"今は　釣りをしていない。": "You aren't fishing now.",
"何も　見つからない。": "Found nothing.",
"針が無いので　エサを　　つけられない。": "No hook to put bait on.",
"ハリが無いので　エサを　つけられない。": "No hook to put bait on.",
"ハリがないので　エサを　つけられない。": "No hook to put bait on.",
"たらいを　水に浮かべた。": "You launched the tub.",
"川虫を　[A0:A0]匹見つけた。": "Found {A0} caddis.",
"ねりえを　[A0:A0]コ見つけた。": "Found {A0} paste bait.",
"赤虫を　[A0:A0]匹見つけた。": "Found {A0} midges.",
"さしを　[A0:A0]匹見つけた。": "Found {A0} maggots.",
"みみずを　[A0:A0]匹見つけた。": "Found {A0} worms.",
"寄せえを　まかなくても　釣れる。": "They bite here without\nchum.",
"ハリをつけた。": "Tied a hook.",
"ハリはついている。": "Hook's on already.",
"ハリは　残っていない。": "No hooks left.",
"寄せえを　まいた。　　　魚が　集まって来た。": "You scattered chum.\nThe fish are coming!",
"寄せえは　残っていない。": "No chum left.",
"ここでは　使えない。": "Can't use that here.",
"今は　使えない。": "Not usable now.",
"たらいは　今使っている。": "You're in the tub now.",
"磁石の針が　右を指した。": "The needle points right.",
"磁石の針が　左を指した。": "The needle points left.",
"磁石の針が　上を指した。": "The needle points up.",
"磁石の針が　下を指した。": "The needle points down.",
"針が　動かなくなった。": "The needle won't move.",
"エサを　ぬしえさにした。": "Switched to King bait.",
"リール竿が　入っていた。": "Inside was a reel rod!",
"ぬしえさは　ついている。": "King bait is on already.",
"ぬしえさは　ない。": "No King bait.",
"何も　入っていなかった。": "There was nothing in it.",
"何も　入っていない。": "It's empty.",
"りんごが　入っていた。": "Inside was an apple!",
"タヌキが　驚いて　姿を　見せた。": "A tanuki jumped out in\nfright!",
"斧で　扉を壊した。": "Axed it open!",
"俺の大好きな　りんごを　ありがとう　ブーブー。　流れの速い　うずの中に　きっといると思う　ブー。":
"Thanks for the apple, my favorite! Oink! Look in the whirlpool where the water's fast. Oink!",
"ぬしばりを　つけた。": "Tied the King hook.",
"ぬしばりは　ついている。": "King hook's on already.",
"ぬしばりは残っていない。": "No King hooks left.",
"[B1:B1]が　現れた！": "{B1} appears!",
"食べ物は　残っていない。": "You have no food left.",
"道具はまだ持っていない。": "You have no tools yet.",
"どうする？": "Action?",
"宝箱に　ぶつかった。": "Hit a treasure box!",
"いらっしゃいませ！": "Welcome!",
"どれに　しましょうか？": "What would you like?",
"この度は　ありがとう　　ございました。": "Thank you very much!",
"うーん　うーん。": "Ugh... ugh...",
"お泊まりには　お金を　　[B0:B0]０円　いただきますが　よろしいですか？":
"A night's stay will be {B0}0 yen. Is that all right?",
"よくやったね！　　　　　おめでとう。": "Well done! Congrats!",
"お金が　足らないけれど": "You're short of money.",
"体力は　最大体力まで　　回復してらっしゃいます。": "Your HP has been fully\nrestored.",
"この井戸の中に　カジカを入れとったが　いなくなってしもうてのう！　　　　お願いじゃが　釣ってきてもらえんじゃろうか？":
"I kept a sculpin in this well, but it's gone! Would you be a dear and catch me another one?",
"おおっ！　カジカじゃな。よく　やったぞ。　　　　いい事を　教えてやろう。洞穴の中に入ったら　磁石の指す方向へ進みなされ。":
"Oh! A sculpin! Well done! Here's a tip for you: inside the caves, go the way the magnet points.",
"あんたのおかげで　毎日　カジカの姿を見られるよ。": "Thanks to you I can see\nmy sculpin every day.",
"村の中や　家の中を　　　めがねかけて　探し回ればエサなんか　いくらでも　めっかるぞ。":
"Put on specs and search the village and the houses. You'll find bait galore!",
"あんたの妹さんの　病気が一日も早く　良くなりますように　こうして　毎日　祈っているんじゃよ。　　ところで　わしのめがねを差しあげよう。":
"Every day I pray your sister gets well soon. Oh, and here, you can have my old specs.",
"魚が　釣れなくなったら　宿に　泊まってみてね。　また　すぐに釣れだすよ。":
"If the fish stop biting, stay at the inn. They'll bite again soon.",
"あー忙しか　忙しか。　　魚が　釣れない時には　　寄せえを　まかなきゃあ　ダメじゃろうが！　　　　それから　魚の集まる　　ポイントを　見つけろよ。エサも　よく選ぶんだぞ。":
"Busy, busy! If the fish won't bite, you've got to scatter chum, see! And find a spot where the fish gather. Choose your bait well too!",
"確かに　記憶しました。": "Saved successfully.",
"記憶に失敗しました。": "Save failed.",
"京子が　急に熱を出して。ごらんのとおりだよ。　　うちの村の　やぶ医者は　どこに　いるのかしらね？早く見つけて来て頂だい。":
"Kyoko suddenly got a fever. Look at her! Where is that quack of a village doctor? Hurry, go find him!",
"何を　ぼんやりしてるの！早く探さないと大変だよ。": "Don't just stand there!\nHurry and find him!",
"ご苦労だったね。": "Thank you, dear.",
"ウキが　ピクピク動いてもエサが合ってないと　魚は絶対に食べないからね。":
"Even if the float bobs, fish won't eat the wrong bait.",
"私が　この村の医者だが。何っ！　京子ちゃんが口をパクパクして倒れたんか？ウーン・・・。　そうだっこの病気を直すには今すぐ川のぬしを　釣って来て　食べさせてやらねばっ。":
"I'm the village doctor. What! Little Kyoko collapsed, gasping? Hmm... I know! To cure her, you must catch the River King and feed it to her!",
"洞穴は　村への近道だからじょうずに　利用してね。": "The caves are shortcuts\nto villages. Use them!",
"洞穴に入ったら　めがねをかけてみろや。　ええことあるぞー。": "Wear specs in the caves. Good things await!",
"ほらみてみな　おばばでもこんなに　釣れるがや。": "Look! Even an old gal\nlike me caught lots!",
"カラスに　魚を盗られないように　注意してね。": "Don't let the crows\nsteal your fish!",
"じゃまするなっ！": "Out of my way!",
"ナムアミダブツ！": "Namu Amida!",
"散らかさないでーっ！": "Don't make a mess!",
"りっぱな　リール竿を　　お持ちですなあ。": "What a splendid reel\nrod you have!",
"宝箱を見つけてないんか？立派な竿が　入っとるぞ。": "Found the treasure yet?\nIt holds a fine rod.",
"立派な　ぬし竿ですなあ。": "That's a fine King rod!",
"何っ！　大きな魚を探しているって？　そりゃあ　　ハクレンや　コクレンが　でかいね。":
"What? You want big fish? Silver carp and bighead carp are big ones.",
"川のぬしを釣りたけりゃあ河口の村で　ぬしばりを　手に入れるんだなっ。":
"To catch the River King, get a King hook at the river mouth.",
"ほら　ほらっ　ムギツクが入れぐいだぞっ！": "The striped minnows are\nbiting like mad!",
"カエルは　ぬしのエサに　なるからたくさん釣れよ。": "Frogs make King bait, so\ncatch a lot of them.",
"たらい作りの　じいとは　わしのことじゃ！　　　　じつは　メダカの魚拓を　作りたいが　釣って来て　もらえんじゃろうか？":
"I'm the old tub maker! Say, I want to make a print of a ricefish. Would you catch one for me?",
"おうっ！　やりおったな。わしにも釣れんかった魚をとうとう　釣りあげたか！わしが　たんねんに作ったたらいじゃが持っていけ。":
"Oh! You did it! You caught a fish even I couldn't! Here, take this tub. I made it with care.",
"たらいに　乗っているか！": "Riding in a tub, eh!",
"ハリヨを　釣ったことが　あるかい？　釣って来たら名人と　言ってやるぜっ！":
"Caught a stickleback? Bring one, and I'll call you a master!",
"やったじゃないかっ！　　わしの畑でとれた芋だけど持っていっていいよ。":
"You did it! Here, have some spuds from my field.",
"いよっ！ハリヨ釣り名人。": "Hey! Stickleback master!",
"最近は　わたしの姿も　　少なくなりました。": "There are fewer of us\nthese days.",
"背の高い　草の中に入ると釣りが　出来ませんぜっ。": "You can't fish from in\nthe tall grass.",
"あんた　カエルがぬしえさになるちゅうことを　まだ知らんのか？　もっと　　釣らなきゃあ！　":
"Don't you know frogs make King bait? You need to catch more!",
"ほうっ。カエルをいっぱい釣ったじゃないかっ！": "Oho! You caught lots of\nfrogs!",
"洞穴の前に　変な木を　　見ませんでした？　時々　タヌキが　化けてるから　せんこう花火で　驚かして見たら　おもしろいよっ。":
"Seen an odd tree by the cave? Sometimes it's a tanuki in disguise. Scare it with sparks. It's a riot!",
"ハリヨは　もっと上の方で見かけたけどなあ！": "I saw sticklebacks\nfurther upstream!",
"たらいを　こぐ時にゃ用心せいよ。　体力をいっぱい使うからなっ。":
"Careful rowing a tub. It takes lots of HP!",
"ポンポコリンのポンッ！": "Pom-pokorin-pom!",
"ぼちぼち　休もうかなっ。": "Time for a rest, maybe.",
"草むしりしてるんです。": "I'm pulling weeds.",
"あーん　腰が痛いよーっ。": "Oww, my aching back!",
"田植えを手伝って下さい。": "Help me plant the rice!",
"カメ釣り名人とは俺様よ。カメの経験値は　とびきり高いからな。　ウッヒヒ！":
"I'm the turtle master! Turtles give heaps of EXP. Hee hee!",
"ずっと下の方で行き止まりになると思うけどその時は斧で　扉をこわしてね。":
"Far downstream it's a dead end. Break the door with an axe.",
"牛のむれの中に　ブタを　見なかったかい？　　　　そのブタが　川のぬしの　居場所を知っているらしいんだが・・。":
"Seen a pig among the cows? They say that pig knows where the River King lives...",
"ブヒーッ　ブヒーッ。　　何だっ！　手ぶらかっ。　俺の好物を　持ってこい。":
"Oink! Oink! What, empty handed? Bring my favorite food!",
"この扉は　斧でこわれる。": "An axe can break this.",
"気持ちがいーよーっ。": "Feels so good!",
"ポチには話しかけないで。今　腹をすかしているの。": "Don't talk to Pochi.\nHe's hungry right now.",
"ウーッ　ワンッ！": "Grrr! Woof!",
"ごちそうさんでしたっ！": "That was delicious!",
"ゴロ　ゴロ　ニャーン。": "Purr purr... meow.",
"あんたの竿じゃあ　ぬしに逃げられちゃうねぇ。　　釣り具屋さんで　売ってるよ。":
"The King will escape that rod. The tackle shop has better.",
"いい竿　持ってるねぇ！": "That's a nice rod!",
"頑張れよーっ！": "Go for it!",
"チクショー！　１ｍもあるソウギョに逃げられたっ。": "Dang! A 1m grass carp\ngot away from me!",
"わたしの　かわいい子ブタさん。　どこに行って　　しまったの？　とっても　りんごが　好きだったの。":
"My cute little piggy, where did you go? He just loved apples.",
"村にいる　犬と猫は　僕が飼っているんです。": "The dog and cat in the\nvillage are mine.",
"ここでは　釣れない。": "Can't fish here.",
"寄せえを　まかないと　　釣れない。": "Nothing bites without\nchum.",
"全部で[V3:C3]円になるけど売ってくれるかい？": "{V3} yen in all.\nSell?",
"ありがとうございました。": "Thank you very much!",
"お金が　足らないけれど。": "You're short of money.",
"それは　残念ですね。": "That's too bad.",
"このびくは　今持っているじゃないですか！": "You already have this\ncreel!",
"このびくは　今持っているのよりも　小さいですよ。": "This creel is smaller\nthan the one you have.",
"これ以上　持つことは　　出来ません。": "You can't carry any\nmore.",
"磁石は持っているはずだ！": "You've got a magnet!",
"鍵は持っているはずだ！": "You've got a key!",
"花火は持っているはずだ！": "You've got sparks!",
"斧は持っているはずだ！": "You've got an axe!",
"釣れているじゃないか！びくの中の　魚一匹につき大きさ別に　お金を払うと":
"Nice catch! I pay for each fish in your creel by size.",
"釣れているじゃないか！びくの中の　魚ー匹につき大きさ別に　お金を払うと":
"Nice catch! I pay for each fish in your creel by size.",
"魚が　びくに入っていないようですけれど！": "Your creel doesn't have\nany fish in it!",
"それは　残念だなあ！": "Too bad!",
"針はそれ以上持てません。": "Can't carry more hooks.",
"寄せえは　それ以上　　　持てません。": "You can't carry any\nmore chum.",
"ぬし針は　それ以上　　　持てません。": "Can't carry any more\nKing hooks.",
"ぬし竿は　持っている。": "You have the King rod.",
"お金がないのか！　　　　しょうがねえなあ！": "No money, huh?\nOh, all right!",
"１本だけだぞ！　　　　　大事に使えよ。": "Only one! Take good\ncare of it.",
"びくの中に　魚が残って　いると　パスワードを　　お伝えできません。":
"I can't give a password while fish are in your creel.",
"ほかに　ございませんか？": "Anything else?",
"びくが　いっぱいに　　　なっている。": "Your creel is full.",
"エサが　ついていない。": "There's no bait on.",
"ハリが　ついていない。": "There's no hook on.",
"かわされて　しまった。": "It dodged!",
"エサを　ミミズにした。": "Switched to worms.",
"エサを　サシにした。": "Switched to maggots.",
"エサを　アカムシにした。": "Switched to midges.",
"エサを　ねりえにした。": "Baited with paste.",
"エサを　カワムシにした。": "Switched to caddis.",
"これ以上　食べきれない。": "You can't eat any more.",
"ミミズは　ない。": "No worms.",
"サシは　ない。": "No maggots.",
"アカムシは　ない。": "No midges.",
"ねりえは　ない。": "No paste bait.",
"カワムシは　ない。": "No caddis.",
"　　力一杯ぶんなぐった！": "You hit it hard!",
"　　力ー杯ぶんなぐった！": "You hit it hard!",
"体力が　[V0:C0]回復した。": "{V0} HP restored.",
"　　必死に　逃げた！": "You ran for it!",
"[B1:B1]の反撃！": "{B1} hits!",
"[B1:B1]の攻撃！": "{B1} lunges!",
"[B1:B1]を　倒した。": "{B1} is beaten.",
"体力が　全部　回復した。": "HP fully restored.",
"[B1:B1]に　捕まった。": "{B1} has you!",
"[B1:B1]は　追って来なかった。": "{B1} didn't follow.",
"[B1:B1]に　やられてしまった。": "{B1} beat you...",
"ミミズは　ついている。": "Worms are on already.",
"サシは　ついている。": "Maggots are on now.",
"アカムシは　ついている。": "Midges are on already.",
"ねりえは　ついている。": "Paste is on already.",
"カワムシは　ついている。": "Caddis is on already.",
"寄せえを１つ持っていた。": "It was carrying chum.",
"はりを１本　持っていた。": "It was carrying a hook.",
"ぱんを　食べた。": "Ate a bun.",
"もちを　食べた。": "Ate a cake.",
"いもを　食べた。": "Ate a spud.",
"牛乳を　飲んだ。": "Drank some milk.",
"あめを　食べた。": "Ate a mint.",
"最大体力まで　　　　　　あと　[V5:C5]です。": "To max HP:\n{V5} more.",
"魚を　１匹　盗まれた。": "A fish was stolen!",
"[V1:C1]ポイントの　ダメージを受けた。": "You took {V1} damage.",
"[V2:C2]ポイントの　ダメージを与えた。": "You dealt {V2} damage.",
"新しい力が　身についた。": "You grew stronger!",
"最大体力が　一つふえて　[B2:B2]になった。": "Max HP went up by one,\nto {B2}.",
"経験値　[B3:B3]　獲得。": "Got {B3} EXP.",
"力を　使い果たした。": "You're worn out.",
"ハリが　取れてしまった。": "The hook came off.",
"ハリが盗られてしまった。": "The hook was stolen.",
"魚が　いなくなった。": "The fish are gone.",
"びくが　いっぱいに　　　なってしまった。": "Your creel is now full.",
"大きさは　[NUM:F0]Ｃｍ。": "Size: {NUM}cm.",
"やったーっ！　ついに　　川のぬしを　釣り上げた。大きさは　２ｍ。　　　　さあ！　すぐに家へ帰って病気で寝ている妹にぬしを食べさせてあげて下さい。":
"You did it! At last you landed the River King! It's 2m long! Now hurry home and feed it to your sick little sister.",
"どうぞ　ごゆっくり。": "Enjoy your stay.",
# fish caught / lost: the fish name is printed before these
"０１２３４５６７８９に　逃げられた。": None,   # digit table + "...got away"; handled in tr_fixed
"を　釣りあげた。": " landed!",
"を　逃がした。": " escaped.",
# --- ending ---
"川のぬしから　作った薬を妹に　飲ませてあげた。　": "The boy gave his sister\nmedicine from the King.",
"すると　すぐに妹は元気になり　立ち上がりました。": "At once she felt better\nand got up out of bed.",
"　　　バンザーイ。　　　": "        Hooray!",
"村人の間から　よろこびの歓声がわき上がりました。　　　　　　　　　　　　": "A cheer of joy went up\nfrom all the villagers.",
"　　　　おわり　　　　　": "        THE END",
}

# Strings placed by offset (copy 1 data offset: (slot bytes incl. terminator, text)).
# Backup memory messages (sector 34): two fixed 22-character lines per message
for _jp, _en in (('データがありません。　', 'No saved game found.'),
                 ('データが正常に読み　　', 'The saved data could'),
                 ('込めませんでした。　　', 'not be loaded.'),
                 ('全体を初期化して　　　', 'Please format the'),
                 ('下さい。　　　　　　　', 'backup memory.'),
                 ('バックアップメモリーが', 'Not enough free space'),
                 ('足りません。　　　　　', 'in backup memory.')):
    DIALOGUE[_jp] = _en.ljust(22)

FIXED = {
    0x01F852: (16, " got away."),   # after the digit table ０-９ at $C83E: "[fish] got away."
    0x003592: (16, " got away."),   # same, unused old program
}

# Animals for {B1} (resident table: offsets at $C886, names at $C89F). Odd-length names get a leading space
# so the cell after the name always starts with the message's own space. Keep names <= 9 letters.
ANIMALS = ["Mouse", "Hare", "Mole", "Mt. Bat", "Owl", "Marten", "Crow", "Fox", "Squirrel", "Tanuki", "Weasel",
           "Eagle", "Rat Snake", "Snake", "Serow", "Viper", "Deer", "Macaque", "Wildcat", "Badger", "Boar",
           "Grizzly", "Scorpion", "Moon Bear", "Spider"]
