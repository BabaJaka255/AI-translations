"""Export the translation to an editable workbook, and import an edited workbook back.

    python3 script_io.py export out.xlsx
    python3 script_io.py import edited.xlsx      -> writes user_edits.py (picked up by build_patch2.py)
"""
import paths as P
import sys, re, json, pickle, importlib
sys.path.insert(0,P.BUILD)
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation

ORIG=P.ROM
WIDE={289:32,297:32,53:48,527:28,528:28,531:28,534:28}
POSTCARD={527,528,531,534}
FIXED={4,5,12,52,53,281,297,299}           # spacing/column-sensitive strings
NOTES={4:'Status label; keep the trailing space.',5:'Title menu; keep the trailing spaces.',
 12:'Two menu options at fixed columns; keep the spacing.',52:'Four column headers, each padded to its column width.',
 53:'Eight labels run together; the contents page maps each column. Change only if lengths stay the same.',
 281:'Three column headers run together.',297:'Prompt plus Yes/No at fixed columns; keep the spacing.',
 299:'Two keys, one per 16px slot; keep the space between them.',
 6:'Default name. Max 8 letters.',7:'Default name. Max 8 letters.',8:'Default name. Max 8 letters.',9:'Default name. Max 8 letters.'}
CODES={'CD':'player name (up to 8 letters)','D8':'fish name','D9':'creature name','DA':'a number','D4':'a second number/place',
 'D1':'lure name','D2':'fly name','D3':'rod name','D5':'food name','D6':'tool/boat name','D7':'compass direction',
 'CE':'bait name','CF':'float/hook name','D0':'fly name'}
ZONE_LABEL={'fish':'Fish','bait':'Bait','hook':'Hook','float':'Float','lure':'Lure','rod':'Rod','fly':'Fly','food':'Food',
 'item':'Item','animal':'Creature'}
ZONE_LIMIT={'fish':15,'bait':16,'hook':16,'float':16,'lure':16,'rod':18,'fly':16,'food':16,'item':16,'animal':16}

def current():
    for m in ('translations','tr_batch2','tr_batch3','zones_en','fish_desc_en','fishery','map_labels'):
        if m in sys.modules: importlib.reload(sys.modules[m])
    import translations,tr_batch2,tr_batch3,zones_en,fish_desc_en,fishery,map_labels
    EN=dict(translations.EN); EN.update(tr_batch2.EN2); EN.update(tr_batch3.EN3)
    Z=dict(zones_en.Z); FD=dict(fish_desc_en.D); FS=dict(fishery.SHORT); MS=dict(map_labels.SHORT)
    try:
        import user_edits; importlib.reload(user_edits)
        EN.update(user_edits.EN_USER); Z.update(user_edits.Z_USER); FD.update(user_edits.FD_USER)
        FS.update(user_edits.FISHERY_SHORT_USER); MS.update(user_edits.MAP_SHORT_USER)
    except ImportError: pass
    return EN,Z,FD,FS,MS

def fish_record_names():
    import struct
    from knt2lib import load_single,load_kanji,decode
    rom=open(ORIG,'rb').read(); s=load_single(); k=load_kanji(); out=set()
    for i in range(73):
        o=0x28018+i*23; p=struct.unpack('<H',rom[o+0x11:o+0x13])[0]; po=0x28000+p-0x8000
        out.add(decode(rom,po,rom.index(b'\0',po),s,k))
    return out
def used_names():
    """(zone, jp) pairs actually present in the ROM name zones, in ROM order."""
    from knt2lib import load_single,load_kanji,decode
    rom=open(ORIG,'rb').read(); s=load_single(); k=load_kanji()
    zones=pickle.load(open(P.data('zones.pkl'),'rb'))
    zones['bait']=list(zones['bait'])+[(0x29FE7,0x29FEA)]
    zones['lure']=list(zones['lure'])+[(0x2A5EC+8*i,0x2A5EC+8*i+7) for i in range(13)]
    out=[];seen=set()
    for zn,L in zones.items():
        for a,b in L:
            jp=decode(rom,a,b,s,k)
            if (zn,jp) in seen or not jp.strip(): continue
            seen.add((zn,jp)); out.append((zn,jp))
    return out

FONT='Arial'
HDR=Font(name=FONT,bold=True,color='FFFFFF'); HFILL=PatternFill('solid',fgColor='1F4E78')
EDIT=PatternFill('solid',fgColor='FFF2CC'); LOCK=PatternFill('solid',fgColor='F2F2F2'); WARN=PatternFill('solid',fgColor='FCE4D6')
THIN=Side(style='thin',color='BFBFBF'); BOX=Border(left=THIN,right=THIN,top=THIN,bottom=THIN)
def table(ws,headers,widths,rows,edit_cols,wrap_cols=()):
    ws.append(headers)
    for c,w in enumerate(widths,1):
        ws.column_dimensions[ws.cell(1,c).column_letter].width=w
        cell=ws.cell(1,c); cell.font=HDR; cell.fill=HFILL; cell.alignment=Alignment(vertical='center',wrap_text=True)
    for r in rows: ws.append(list(r))
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font=Font(name=FONT,size=10); c.border=BOX
            c.alignment=Alignment(vertical='top',wrap_text=(c.column in wrap_cols))
            c.fill=EDIT if c.column in edit_cols else LOCK
    ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions

def export(path):
    EN,Z,FD,FS,MS=current()
    script={x['id']:x for x in json.load(open(P.b('script.json')))}
    wb=Workbook()
    # --- instructions
    ws=wb.active; ws.title='How to edit'
    lines=[
     ('Super Legend of the River King - script workbook',True),
     ('',False),
     ('Edit only the yellow cells (the English columns). Grey cells are reference and are ignored when imported.',False),
     ('Keep every row: do not add, delete or re-sort rows. IDs tell the patch builder where each line goes.',False),
     ('',False),
     ('LINE BREAKS',True),
     ('Each line of a cell is one line in the game. Start a new line with Alt+Enter (Excel/LibreOffice) or Ctrl+Enter (Google Sheets).',False),
     ('Dialogue lines can be at most 23 characters (a few special strings allow more; see the Limit column).',False),
     ('A dialogue box shows 4 lines at a time and scrolls, so a message can have more than 4 lines.',False),
     ('The "Longest line" column counts characters as you type; it turns red when a line is too long. Codes like {CD} count as 8.',False),
     ('',False),
     ('CODES - copy them exactly, including braces',True)]
    lines+=[('  {%s}  =  %s'%(k,v),False) for k,v in CODES.items()]
    lines+=[('A code that inserts a name should usually sit on its own line or near the start of one, because names can be long.',False),
     ('',False),
     ('ALLOWED CHARACTERS',True),
     ('Plain ASCII only: letters, digits, space and  ! " # $ % & \' ( ) * + , - . / : ; < = > ? @ [ \\ ] ^ _ ` { | } ~',False),
     ('No curly quotes, accented letters, em dashes or Japanese. Excel and Word love to turn \' and " into curly quotes; the importer converts them back, but check.',False),
     ('',False),
     ('THE SHEETS',True),
     ('Dialogue  - every message, menu and sign text (511 strings).',False),
     ('Names     - fish, bait, gear, items and creature names, used everywhere the game inserts a name.',False),
     ('Fish Notes - the description on each fish page (wrapped automatically; about 100 characters fit).',False),
     ('Short Names - shorter forms used only where space is tight: the fishery price window (max 13) and Fishing Note map labels (max 9).',False),
     ('',False),
     ('Example (Dialogue sheet): ID 27, English  "Hearing this, {CD}" + Alt+Enter + "decided to go fishing" + Alt+Enter + "for the River King."',False),
     ('When you are done, save as .xlsx and send the file back.',False)]
    for i,(t,b) in enumerate(lines,1):
        c=ws.cell(i,1,t); c.font=Font(name=FONT,bold=b,size=12 if i==1 else 10)
    ws.column_dimensions['A'].width=140
    # --- dialogue
    ws=wb.create_sheet('Dialogue')
    rows=[]
    for i in sorted(EN):
        jp=script[i]['jp']; lim=WIDE.get(i,23)
        note=NOTES.get(i,'Fixed layout - edit with care.' if i in FIXED else '')
        if i in POSTCARD: note='Shown on a postcard: max 5 lines of 28 characters.'
        rows.append((i,jp,EN[i],lim,None,note))
    table(ws,['ID','Japanese (reference)','English (edit)','Limit','Longest line','Notes'],[7,38,40,7,9,40],rows,{3},{2,3,6})
    for r in range(2,ws.max_row+1):
        # longest line: codes {XX} count as 8 (approximation of name width), via SUBSTITUTE on the common codes
        e='C%d'%r
        sub=e
        for code in ('CD','D8','D9','D1','D2','D3','D5','D6','CE','CF','D0','D7'):
            sub='SUBSTITUTE(%s,"{%s}","########")'%(sub,code)
        sub='SUBSTITUTE(SUBSTITUTE(%s,"{DA}","######"),"{D4}","######")'%sub
        # longest of up to 12 lines: MID/FIND on CHAR(10)
        f=('=SUMPRODUCT(MAX(LEN(TRIM(MID(SUBSTITUTE(SUBSTITUTE(%s," ","~"),CHAR(10),REPT(" ",200)),(ROW($1:$12)-1)*200+1,200)))))'%sub)
        ws['E%d'%r]=f
        ws['E%d'%r].font=Font(name=FONT,size=10); ws['E%d'%r].border=BOX; ws['E%d'%r].fill=LOCK
    from openpyxl.formatting.rule import FormulaRule
    ws.conditional_formatting.add('E2:E%d'%ws.max_row,FormulaRule(formula=['E2>D2'],fill=PatternFill('solid',fgColor='FF9999'),font=Font(name=FONT,bold=True,color='9C0006')))
    # --- names
    ws=wb.create_sheet('Names')
    rows=[]
    fishnames=fish_record_names()
    items=[]
    for zn,jp in used_names():
        if jp not in Z: continue
        kind=ZONE_LABEL[zn]
        if zn=='fish' and jp not in fishnames: kind='How to eat'
        items.append((kind,jp,Z[jp]))
    lim={}
    for kind,jp,en in items: lim[kind]=max(lim.get(kind,0),len(en))
    rows=[(kind,jp,en,lim[kind]) for kind,jp,en in items]
    table(ws,['Kind','Japanese (reference)','English (edit)','Max length'],[11,30,30,11],rows,{3})
    ws.conditional_formatting.add('C2:C%d'%ws.max_row,FormulaRule(formula=['LEN(C2)>D2'],fill=PatternFill('solid',fgColor='FF9999')))
    # --- fish notes
    ws=wb.create_sheet('Fish Notes')
    from knt2lib import load_single,load_kanji,decode
    import struct
    rom=open(ORIG,'rb').read(); s=load_single(); k=load_kanji()
    rows=[]
    for i in sorted(FD):
        o=0x28018+i*23; p=struct.unpack('<H',rom[o+0x11:o+0x13])[0]; po=0x28000+p-0x8000
        jp=decode(rom,po,rom.index(b'\0',po),s,k)
        dp=struct.unpack('<H',rom[o+0x13:o+0x15])[0]; dpo=0x28000+dp-0x8000
        jpd=decode(rom,dpo,rom.index(b'\0',dpo),s,k)
        rows.append((i,Z.get(jp,jp),jpd,FD[i]))
    table(ws,['#','Fish','Japanese (reference)','English description (edit)'],[5,18,50,60],rows,{4},{3,4})
    # --- short names
    ws=wb.create_sheet('Short Names')
    rows=[('Fishery window (max 13)',k_,v,13) for k_,v in sorted(FS.items())]+[('Map label (max 9)',k_,v,9) for k_,v in sorted(MS.items())]
    table(ws,['Used in','Full name (reference)','Short form (edit)','Max length'],[24,22,22,11],rows,{3})
    ws.conditional_formatting.add('C2:C%d'%ws.max_row,FormulaRule(formula=['LEN(C2)>D2'],fill=PatternFill('solid',fgColor='FF9999')))
    wb.save(path)

FIX={'‘':"'",'’':"'",'“':'"','”':'"','–':'-','—':'-','…':'...',' ':' ','\r':''}
def clean(t):
    t='' if t is None else str(t)
    for a,b in FIX.items(): t=t.replace(a,b)
    return t
def check_text(t,lim,where,errs):
    bad=[ch for ch in t if not (ch=='\n' or 0x20<=ord(ch)<0x7F)]
    if bad: errs.append('%s: characters the game cannot show: %s'%(where,''.join(sorted(set(bad)))))
    for code in re.findall(r'\{([^}]*)\}',t):
        if not re.fullmatch(r'[0-9A-Fa-f]{2}',code): errs.append('%s: unknown code {%s}'%(where,code))
    if lim:
        for ln in t.split('\n'):
            w=len(re.sub(r'\{(CD|D8|D9|D1|D2|D3|D5|D6|CE|CF|D0|D7)\}','#'*8,re.sub(r'\{(DA|D4)\}','#'*6,ln)))
            if w>lim: errs.append('%s: line too long (%d > %d): %r'%(where,w,lim,ln))

def import_(path,out=P.b('user_edits.py')):
    EN,Z,FD,FS,MS=current()
    wb=load_workbook(path)
    errs=[]; en={}; z={}; fd={}; fs={}; ms={}; changed=[]
    ws=wb['Dialogue']
    for row in ws.iter_rows(min_row=2,values_only=True):
        if row[0] is None: continue
        i=int(row[0]); t=clean(row[2]); lim=WIDE.get(i,23)
        check_text(t,lim,'Dialogue ID %d'%i,errs); en[i]=t
        if i in POSTCARD and (t.count('\n')>4 or len(t)>158):
            errs.append('Dialogue ID %d: shown on a postcard - max 5 lines and about 155 characters'%i)
        if t!=EN.get(i): changed.append(('Dialogue',i,EN.get(i),t))
    ws=wb['Names']
    for row in ws.iter_rows(min_row=2,values_only=True):
        if row[1] is None: continue
        jp=row[1]; t=clean(row[2]); lim=row[3]
        check_text(t,None,'Name %s'%jp,errs)
        if len(t)>int(lim): errs.append('Name %s: %r is longer than %s'%(jp,t,lim))
        if '\n' in t: errs.append('Name %s: names cannot have line breaks'%jp)
        z[jp]=t
        if t!=Z.get(jp): changed.append(('Names',jp,Z.get(jp),t))
    ws=wb['Fish Notes']
    for row in ws.iter_rows(min_row=2,values_only=True):
        if row[0] is None: continue
        i=int(row[0]); t=' '.join(clean(row[3]).split()); check_text(t,None,'Fish note %d'%i,errs); fd[i]=t
        lines=[];cur='';w=22
        for wd in t.split():
            if len(cur)+len(wd)+(1 if cur else 0)<=w: cur=(cur+' '+wd) if cur else wd
            else: lines.append(cur); cur=wd; w=27
        lines.append(cur)
        if len(lines)>4: errs.append('Fish note %d: too long - it wraps to %d lines (max 4)'%(i,len(lines)))
        if t!=FD.get(i): changed.append(('Fish Notes',i,FD.get(i),t))
    ws=wb['Short Names']
    for row in ws.iter_rows(min_row=2,values_only=True):
        if row[1] is None: continue
        kind,full,t,lim=row[0],row[1],clean(row[2]),int(row[3])
        check_text(t,None,'Short name %s'%full,errs)
        if len(t)>lim: errs.append('Short name %s: %r is longer than %d'%(full,t,lim))
        (fs if kind.startswith('Fishery') else ms)[full]=t
        old=(FS if kind.startswith('Fishery') else MS).get(full)
        if t!=old: changed.append(('Short Names',full,old,t))
    with open(out,'w') as f:
        f.write('# Generated by script_io.py import from %s - edits made in the script workbook.\n'%path.split('/')[-1])
        for name,d in (('EN_USER',en),('Z_USER',z),('FD_USER',fd),('FISHERY_SHORT_USER',fs),('MAP_SHORT_USER',ms)):
            f.write('%s=%r\n'%(name,d))
    return changed,errs

if __name__=='__main__':
    if sys.argv[1]=='export': export(sys.argv[2])
    else:
        ch,er=import_(sys.argv[2])
        print('changed',len(ch)); [print(' ',c) for c in ch[:50]]
        print('problems',len(er)); [print(' ',e) for e in er[:50]]
