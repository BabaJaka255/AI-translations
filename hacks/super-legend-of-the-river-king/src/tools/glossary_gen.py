"""Step 1 of the glossary: collect every name and term with its Japanese source (writes out/glossary_rows.json).
Then run glossary_build.py to write docs/glossary.{csv,xlsx,html}."""
import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import pickle,struct,sys,json
from knt2lib import *
from zones_en import Z
import user_edits, fishery, map_labels, translations, tr_batch2, tr_batch3
Z=dict(Z); Z.update(user_edits.Z_USER)
FSH=dict(fishery.SHORT); FSH.update(user_edits.FISHERY_SHORT_USER)
MSH=dict(map_labels.SHORT); MSH.update(user_edits.MAP_SHORT_USER)
EN=dict(translations.EN);EN.update(tr_batch2.EN2);EN.update(tr_batch3.EN3);EN.update(user_edits.EN_USER)
S={x['id']:x for x in json.load(open(P.b('script.json'),encoding='utf-8'))}
rom=open(ROMPATH,'rb').read(); single=load_single(); kanji=load_kanji()
zones=pickle.load(open(P.data('zones.pkl'),'rb'))
FIX=[('貝虫','昆虫'),('塋','型'),('ブドウ涌煮','ブドウ酒煮'),('忖露煮','甘露煮'),('忖煮つけ','甘煮つけ'),('実験忖料','実験材料'),
     ('蓙狎','産卵'),('狎柬','卵巣'),('艦賞','観賞'),('胙','酢'),('強壮劑','強壮剤'),('トップウ<B7>ータ','トップウォータ')]
UNSURE={'つけやき・煉白'}
def fix(j):
    for a,b in FIX: j=j.replace(a,b)
    return j
# --- kana -> Hepburn
H="あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
R="a i u e o ka ki ku ke ko sa shi su se so ta chi tsu te to na ni nu ne no ha hi fu he ho ma mi mu me mo ya yu yo ra ri ru re ro wa o n ga gi gu ge go za ji zu ze zo da ji zu de do ba bi bu be bo pa pi pu pe po".split()
K={h:r for h,r in zip(H,R)}
SM={'ゃ':'ya','ゅ':'yu','ょ':'yo'}; SV={'ぁ':'a','ぃ':'i','ぅ':'u','ぇ':'e','ぉ':'o'}
def kata2hira(s): return ''.join(chr(ord(c)-0x60) if 'ァ'<=c<='ヶ' else c for c in s)
def romaji(s):
    t=kata2hira(s); out=''; i=0
    if any(not(c in K or c in SM or c in SV or c in 'っー・ ') for c in t): return ''
    while i<len(t):
        c=t[i]
        if c=='っ':
            nx=K.get(t[i+1],'') if i+1<len(t) else ''; out+=('t' if nx.startswith('ch') else nx[:1]); i+=1; continue
        if c=='ー':
            M={'a':'ā','i':'ī','u':'ū','e':'ē','o':'ō'}
            if out and out[-1] in M: out=out[:-1]+M[out[-1]]
            i+=1; continue
        if c=='・': out+=' / '; i+=1; continue
        if c==' ': out+=' '; i+=1; continue
        if c in SM:
            b=out[-1:] ; 
            if out.endswith('i'): out=out[:-1]; 
            out+=('' if out.endswith(('sh','ch','j')) else '')+(SM[c] if not out.endswith(('sh','ch','j')) else SM[c][1:]); i+=1; continue
        if c in SV:
            if out.endswith('u') and c in 'ぃぇぉ' and out[-2:-1] in ('f','w','') : out=out[:-1]
            elif out.endswith('i') and c=='ぇ': out=out[:-1]
            elif out.endswith(('e','o','u','a','i')) and c=='ぃ': out=out[:-1]
            out+=SV[c]; i+=1; continue
        out+=K[c]; i+=1
    return out.capitalize()
SCI={'イワナ':'Salvelinus leucomaenis','アメマス':'Salvelinus leucomaenis (sea-run form)','ヤマメ':'Oncorhynchus masou masou (river form)',
'アマゴ':'Oncorhynchus masou ishikawae (river form)','カジカ':'Cottus pollux','ニジマス':'Oncorhynchus mykiss','ヒメマス':'Oncorhynchus nerka (landlocked)',
'ブラウントラウト':'Salmo trutta','カワマス':'Salvelinus fontinalis','ワカサギ':'Hypomesus nipponensis','ブラックバス':'Micropterus salmoides',
'ウグイ':'Pseudaspius hakonensis','コイ':'Cyprinus carpio','ドンコ':'Odontobutis obscura','オイカワ':'Opsariichthys platypus','モツゴ':'Pseudorasbora parva',
'イトモロコ':'Squalidus gracilis','ギギ':'Tachysurus nudiceps','サクラマス':'Oncorhynchus masou masou (sea-run form)','コクレン':'Hypophthalmichthys nobilis',
'ハクレン':'Hypophthalmichthys molitrix','ムギツク':'Pungtungia herzi','ホンモロコ':'Gnathopogon caerulescens','ヤマノカミ':'Trachidermus fasciatus',
'ドジョウ':'Misgurnus anguillicaudatus','タモロコ':'Gnathopogon elongatus','カワムツ':'Candidia temminckii','キンブナ':'Carassius buergeri subsp.',
'マブナ':'Carassius spp. (wild crucian carp)','アカザ':'Liobagrus reinii','メダカ':'Oryzias latipes','ブルーギル':'Lepomis macrochirus',
'オヤニラミ':'Coreoperca kawamebari','ハリヨ':'Gasterosteus aculeatus subsp.','トミヨ':'Pungitius sinensis','ライギョ':'Channa spp.',
'ヘラブナ':'Carassius cuvieri','ナマズ':'Silurus asotus','サヨリ':'Hyporhamphus sajori','ハス':'Opsariichthys uncirostris','ワタカ':'Ischikauia steenackeri',
'カマツカ':'Pseudogobio esocinus','ツチフキ':'Abbottina rivularis','シマドジョウ':'Cobitis biwae','カムルチー':'Channa argus',
'ヒガイ':'Sarcocheilichthys variegatus','ソウギョ':'Ctenopharyngodon idella','アオウオ':'Mylopharyngodon piceus','ニゴイ':'Hemibarbus barbus',
'マルタ':'Pseudaspius brandtii','ハゼ':'Gobiidae (e.g. Acanthogobius flavimanus)','ボラ':'Mugil cephalus','スズキ':'Lateolabrax japonicus',
'アカメ':'Lates japonicus','アユ':'Plecoglossus altivelis','タナゴ':'Acheilognathus melanogaster','ウナギ':'Anguilla japonica',
'オオウナギ':'Anguilla marmorata','アブラハヤ':'Rhynchocypris lagowskii','クロダイ':'Acanthopagrus schlegelii','ヌマガレイ':'Platichthys stellatus',
'クサフグ':'Takifugu alboplumbeus','テナガエビ':'Macrobrachium nipponense','サツキマス':'Oncorhynchus masou ishikawae (sea-run form)',
'イモリ':'Cynops pyrrhogaster','ザリガニ':'Procambarus clarkii','スッポン':'Pelodiscus sinensis'}
FNOTE={'ヤマメ':'River form of the masu salmon. The sea-run form (サクラマス) is "Masu Salmon".',
'サクラマス':'Sea-run form of ヤマメ ("Masu Trout").','アマゴ':'River form; the sea-run form (サツキマス) is "Redspot Salmon".',
'サツキマス':'Sea-run form of アマゴ ("Redspot Trout").','アメマス':'Sea-run form of イワナ ("Char").',
'ヘラブナ':'Abbreviated "W.Crucian" in tight spaces (hooks, floats, rods, map).','マブナ':'General term for wild crucian carp.',
'イトモロコ':'Japanese name kept: no common English name.','ムギツク':'Japanese name kept: no common English name.',
'タモロコ':'Japanese name kept: no common English name.','ワタカ':'Japanese name kept: no common English name.',
'ヒガイ':'Japanese name kept: no common English name.','ライギョ':'Generic snakehead; カムルチー is the species "Amur Snakehead".',
'ヒメマス':'Landlocked sockeye salmon.','メゴチ':'In Japanese this name covers several small flatheads and dragonets.',
'アブラハヤ':'Translated generically as "Minnow".','トウギョ':'"Fighting fish"; translated as Paradise Fish (Macropodus).'}
READ={'ぬし釣り':'Nushi-tsuri','川のぬし釣り2':'Kawa no Nushi Tsuri 2','釣りノート':'Tsuri nōto','釣り方':'Tsurikata','投げづり':'Nagezuri',
'毛バリ':'Kebari','無し':'Nashi','寄せエサ':'Yose-esa','道具':'Dōgu','体力':'Tairyoku','お金':'Okane','円':'En','経験値':'Keikenchi','命令':'Meirei',
'尾 / 匹':'O / hiki','年齢':'Nenrei','釣果':'Chōka','最長':'Saichō','生活':'Seikatsu','利用':'Riyō','順位':'Jun\'i','名前':'Namae','記録':'Kiroku',
'大会':'Taikai','釣り大会':'Tsuri taikai','絵はがき':'Ehagaki','届いた絵はがき':'Todoita ehagaki','記録を消す':'Kiroku o kesu',
'最初から始める':'Saisho kara hajimeru','東 / 西 / 南 / 北':'Higashi / nishi / minami / kita','宿':'Yado','魚':'Sakana','釣':'Tsuri','様':'Sama','才':'Sai',
'渓流':'Keiryū','山上湖':'Sanjōko','清流':'Seiryū','湖':'Mizuumi','下流':'Karyū','河口':'Kakō','ステレオ / モノラル':'Sutereo / monoraru',
'紅ザシ':'Benizashi','ハチの子':'Hachi no ko','小魚':'Kozakana','貝のむきみ':'Kai no mukimi','おとりアユ':'Otori ayu','袖ヒガイ':'Sode higai',
'目印':'Mejirushi','丸型シモリ':'Marugata shimori','流線シモリ':'Ryūsen shimori','玉ウキ':'Tama uki','棒ウキ':'Bō uki','小判型おもり':'Koban-gata omori',
'ナツメ型おもり':'Natsume-gata omori','日の丸弁当':'Hinomaru bentō','釣った魚':'Tsutta sakana','虫メガネ':'Mushi megane','金アミ':'Kin ami',
'磁石':'Jishaku','牛乳ビン':'Gyūnyū bin','牛乳':'Gyūnyū','富くじ':'Tomikuji','花火':'Hanabi','昆虫':'Konchū','ソフト・赤ガエル':'Sofuto / aka gaeru','ウェット':'Wetto','トップウォータ':'Toppu wōta','月の輪熊':'Tsukinowaguma','大岩魚':'Ō-iwana','作者':'Sakusha',
'イワナの記録':'Iwana no kiroku','ブラックバス大会':'Burakkubasu taikai','アユ釣りの記録':'Ayu-tsuri no kiroku','ヘラブナ大会':'Herabuna taikai',
'ドジョウの記録':'Dojou no kiroku','スズキ大会':'Suzuki taikai','びく 容量10':'Biku yōryō 10','びく 容量20':'Biku yōryō 20','びく 容量30':'Biku yōryō 30'}
rows=[]
def add(cat,jp,en,**kw):
    jp=fix(jp); d=dict(cat=cat,jp=jp,romaji=kw.pop('romaji',None) or READ.get(fix(jp)) or romaji(fix(jp)),en=en); d.update(kw)
    if jp in UNSURE: d['note']=(d.get('note','')+' Japanese partly unverified (font-matched kanji).').strip()
    rows.append(d)
# Fish & catchables
for i in range(73):
    o=0x28018+i*23; p=struct.unpack('<H',rom[o+0x11:o+0x13])[0]
    e=rom.index(b'\0',0x28000+p-0x8000); jp=decode(rom,0x28000+p-0x8000,e,single,kanji)
    en=Z.get(jp)
    if not en: continue
    cat='Fish' if jp not in ('イモリ','カエル','ザリガニ','カメ','スッポン','カニ','テナガエビ') else 'Other catch'
    add(cat,jp,en,map=MSH.get(en,'') if len(en)>9 else '',fishery=FSH.get(en,'') if len(en)>13 else '',sci=SCI.get(jp,''),note=FNOTE.get(jp,''))
CATS={'bait':'Bait','hook':'Hooks','float':'Floats & sinkers','lure':'Lures','rod':'Rods','fly':'Flies','food':'Food','item':'Items','animal':'Creatures'}
for zn,cat in CATS.items():
    seen=[]
    for s,e in zones[zn]:
        jp=decode(rom,s,e,single,kanji)
        if jp.strip() and jp not in seen and Z.get(jp): seen.append(jp); add(cat,jp,Z[jp])
fz=[]
fishjp={r['jp'] for r in rows}
for s,e in zones['fish']:
    jp=decode(rom,s,e,single,kanji)
    if len(jp)<30 and jp not in fz and Z.get(jp) and fix(jp) not in fishjp: fz.append(jp); add('Fishing Note: how to eat',jp,Z[jp])
# script-based terms
def sid(cat,i,en=None,jp=None,note=''):
    add(cat,(jp or S[i]['jp']).strip(),(en or EN[i]).strip(),note=note,src='string %d'%i)
for i,rel,r in ((6,'Brother (兄)','Taro'),(7,'Sister (妹)','Kyoko'),(8,'Father (父)','Yuzo'),(9,'Mother (母)','Noriko')):
    add('Characters',S[i]['jp'].strip(),EN[i].strip(),romaji=EN[i].strip(),src='string %d'%i,note='Default name for the '+rel.split()[0].lower()+' '+rel.split()[1]+'.')
add('Characters','つり太郎','FishTaro',romaji='Tsuri Tarō',note='Secret name for the brother; unlocks a stocked tackle box.')
for i,n in ((424,''),(425,'')): sid('Characters',i,en=EN[i].rstrip('!.').strip(),jp=S[i]['jp'].replace('さーん!','').replace('さん。',''),note='Named in the ending.')
for i in range(497,527):
    if i==526: continue
    add('Characters',S[i]['jp'].strip(),EN[i],romaji=EN[i],note='Villager name.',src='string %d'%i)
sid('Characters',533,note='Creature named in the endings.'); sid('Characters',536); sid('Characters',530)
for i,v in ((54,'渓流'),(55,'山上湖'),(56,'清流'),(57,'湖'),(58,'下流'),(59,'河口')):
    sid('Places',i,jp=v,note='Area name (Fishing Note, map).')
for i in (290,291,292,293,294,295):
    jp=S[i]['jp']; place,town=jp.split()
    add('Places',jp.replace('  ',' '),EN[i],note='Village. The game shows the river/lake name ('+place+') and the village name together; the English keeps only the village.')
for i in (535,532,529): sid('Places',i,jp=S[i]['jp'].replace('  ',' '))
T=[('ぬし','River King','The legendary fish of each area. Follows the Game Boy "Legend of the River King" series.'),
('ぬし釣り','River King fishing','Used in "Kawa no Nushi Tsuri" (title) and dialogue.'),
('川のぬし釣り2','Super Legend of the River King','Title of this patch.'),
('釣りノート','Fishing Note',''),('釣り方','fishing style',''),('ウキづり','Float fishing','Fishing style (Select switches styles in the gear window).'),
('投げづり','Casting','Fishing style.'),('ルアー','Lure','Fishing style and gear.'),('フライ','Fly','Fishing style. Flies themselves are 毛バリ.'),('毛バリ','fly (artificial)',''),
('サオ','Rod','Gear slot; empty slot shows ROD.'),('ウキ','Float','Gear slot; empty slot shows FLOAT.'),('オモリ','Sinker','Gear slot; empty slot shows SINKER.'),
('ハリ','Hook','Gear slot; empty slot shows HOOK.'),('無し','None','Empty-slot label; shows NONE.'),('エサ','bait',''),('寄せエサ','chum',''),('びく','creel','The fish basket; menu label "Creel".'),
('道具','tools / gear',''),('体力','HP','Status window.'),('お金','Yen','Status window. Money is shown in yen.'),('円','yen','Currency counter.'),('経験値','EXP','Status window and battle.'),
('命令','Cmd','Battle command window title.'),('尾 / 匹','(fish counter, dropped)','Counters are omitted in English.'),('年齢','Age','Character select.'),
('釣果','Got','Fishing Note column: fish caught.'),('最長','Best','Fishing Note column: longest catch.'),('生活','Info','Fishing Note column: habitat notes.'),
('利用','Use','Fishing Note column: how to eat.'),('順位','Rank','Contest records.'),('名前','Name','Contest records.'),('記録','Best / Records','Contest records.'),
('大会','Contest','e.g. ブラックバス大会 = Bass Contest.'),('釣り大会','fishing tournament',''),('絵はがき','postcard',''),('届いた絵はがき','Received postcard',''),
('記録を消す','Erase Data','Title menu.'),('はじめる','Start','Title screen sprite now reads START.'),('最初から始める','New Game','Title menu.'),
('ステレオ / モノラル','Stereo / Mono','Sound option item.'),('メイフライ','Mayfly','Fly category.'),('カディス','Caddis','Fly category.'),('ディプテラ','Diptera','Fly category.'),
('ストーンフライ','Stonefly','Fly category.'),('テレストリアル','Terrestrial','Fly category; menu label "Terrestr.".'),('東 / 西 / 南 / 北','East / West / South / North','Compass.'),
('宿','INN','Town plaque.'),('魚','(fish icon)','Fish-shop plaque, now a picture.'),('釣','(hook icon)','Tackle-shop plaque, now a picture.'),('だんご','Dumpling / (dango icon)','Food item; the shop banner is now a dango picture.'),
('様','(honorific dropped)','Postcard address line.'),('才','(age suffix dropped)','Character select.')]
for jp,en,n in T: add('Terms',jp,en,note=n)
for i in (282,283,284,285,286,287): sid('Terms',i,note='Contest / records board title.')
json.dump(rows,open(P.out('glossary_rows.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=0)
from collections import Counter; print(Counter(r['cat'] for r in rows)); print(len(rows))
for r in rows[:12]+rows[-60:-40]: print(r)
