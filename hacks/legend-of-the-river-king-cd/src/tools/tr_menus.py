# Menu labels drawn from window templates (tools/templates.py). Each kanji cell is 2 tiles = 2 letters,
# so an English label has exactly the template's width in tiles (n); '_' cells in the key are blank tiles.
# Values are padded with spaces to n.
LABELS = {
    '命令': 'Menu',
    'えさ_弁当': 'Bait Food',
    '釣具_びく': 'Gear Fish',
    '道具': 'Item',
    'はい': 'Yes',
    'いいえ': 'No',
    '体力': 'HP',
    'お金': 'Yen',
    '経験': 'EXP',
    '渓流': 'Glen', '上流': 'High', '中流': 'Mid', '下流': 'Low', '河口': 'Bay',
    '川__虫': 'Caddis', 'ねりえ': 'Paste', '赤__虫': 'Midge', 'さ__し': 'Maggot', 'みみず': 'Worms',
    '針': 'Hook', '寄せえ': 'Chum', 'ぬし針': 'K.Hook', 'ぬしえ': 'K.Bait',
    '容量': 'Size',
    'びく': 'Bag', '磁__石': 'Magnet', 'ぱ__ん': 'Bun', '鍵': 'Key', 'も__ち': 'Cake', '花__火': 'Sparks',
    'い__も': 'Spud', '斧': 'Axe', '牛__乳': 'Milk', 'ぬし竿': 'K.Rod', 'あ__め': 'Mint',
    '竹__竿': 'Bamboo', 'リール竿': 'Reel rod',
    'ぱん': 'Bun', 'もち': 'Cake', 'いも': 'Spud', '牛乳': 'Milk', 'あめ': 'Mint',
    'めがね': 'Specs', '磁石': 'Magnet', 'たらい': 'Tub', '花火': 'Sparks', 'リんご': 'Apple',
    # battle menu: glyph slots 56-63 are reloaded in battle with 戦う弁当する逃げ
    '花__が': 'Fight', 'ね__斧': 'Eat', 'ね斧たら': 'Eat', '竹ルら': 'Run',
}
