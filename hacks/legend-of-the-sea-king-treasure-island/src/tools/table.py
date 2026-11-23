"""Glyph index <-> character for Umi no Nushi Tsuri (COMM.TIM pages 1-5)."""
import json, os
_h = os.path.dirname(os.path.abspath(__file__))
SYM = '　、。．・：？！０１２３４５６７８９（）「」ヶー～＋＜°″○Ａｍ'
HIRA = [chr(c) for c in range(ord('ぁ'), ord('ん') + 1) if chr(c) not in 'ゎゐゑ']
KATA = [chr(c) for c in range(ord('ァ'), ord('ン') + 1) if chr(c) not in 'ゥヮヰヱ']
T = {}
for i, c in enumerate(SYM + ''.join(HIRA) + ''.join(KATA)): T[i] = c
assert len(T) == 191, len(T)
T.update({191: '磯?', 192: 'アミ', 193: 'ルア', 194: 'ー', 195: 'cm'})
for k, v in json.load(open(os.path.join(_h, 'kanji_dp.json'))).items():
    T[int(k)] = v[0]
EXTRA = ('裂恋練連路老郎録和話椀湾腕[989][990]遊聴[993][994]'
         '\x01ギジ\x01バリ\x01ワー\x01ラー杯偏半棲茶油牛乳印電率％神影販機旅賊届貴堀普万'
         '存各説泣払労限憶遠[1031]ヶ奇跡術稼善諸国浸功[1042]急緒頃格闘件[1049]恐池井稿飢殿'
         '[1056][1057][1058][1059][1060]版支呂迷養殖[1067]')
import re
toks = re.findall(r'\[\d+\]|\x01..|.', EXTRA)
for i, t in enumerate(toks): T[976 + i] = t.lstrip('\x01')
assert max(T) == 1067, max(T)
R = {}
for k, v in sorted(T.items()):
    R.setdefault(v, k)
# hand corrections from visual check (2026-11-22)
FIX = {205: '意', 208: '違', 220: '鵜', 227: '鋭', 249: '佳', 262: '怪', 279: '活', 282: '蒲', 283: '鎌', 285: '寒',
       287: '感', 289: '漢', 297: '関', 303: '頑', 342: '協', 353: '禁', 361: '屈', 375: '経', 378: '軽', 384: '健',
       385: '堅', 391: '険', 404: '湖', 425: '考', 432: '黒', 437: '根', 438: '混', 449: '菜', 487: '治', 488: '磁',
       523: '集', 537: '順', 539: '所', 543: '傷', 548: '彰', 558: '蕉', 577: '深', 579: '親', 590: '錐', 593: '瀬',
       619: '線', 625: '然', 626: '全', 627: '噌', 628: '狙', 630: '組', 631: '層', 663: '態', 677: '濁', 680: '棚',
       684: '淡', 732: '転', 736: '電', 737: '塗', 783: '熱', 784: '年', 810: '般', 822: '尾', 823: '美', 893: '慢',
       894: '満', 935: '揚', 941: '要', 945: '翼', 952: '理', 967: '鱗'}
T.update(FIX)
R = {}
for k, v in sorted(T.items()):
    R.setdefault(v, k)
# context fixes (2026-11-22, from reading the script)
FIX2 = {861: '変', 717: '漬', 666: '胎', 953: '離', 954: '陸', 786: '撚', 386: '嫌', 837: '富', 635: '槍',
        993: '茹', 994: '貪', 990: '棘', 989: '孵', 1008: '籠', 1055: '殴'}
FIX2.update({1067: '風', 1031: '慮', 1042: '費', 1056: '｜'})
T.update(FIX2)
R = {}
for k, v in sorted(T.items()):
    R.setdefault(v, k)
