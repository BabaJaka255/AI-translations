"""The English script: string id -> text (ids as in out/script_dump.txt).
\\n = line break. {CD} etc. = the game's insert codes (see UMI_NOTES.md).
Width limits are checked by build_patch.py (see limits())."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from tr_system import EN_SYS
from tr_story import EN_STORY
from tr_town import EN_TOWN
from tr_notes import EN_NOTES, NAMES
from tr_misc import EN_MISC
EN={}
for d in (EN_SYS,EN_STORY,EN_TOWN,EN_NOTES,EN_MISC): EN.update(d)
try:
    from user_edits import EN_USER
    EN.update(EN_USER)
except ImportError: pass
FIXED={63,66,69,505,579,609}      # letters/certificates: fixed 5-line windows
TIPS=set(range(102,181,2))                        # fishing paper tips: 3 lines of 30 (checked in the emulator)
WIDE={81,83,85,87,88,90}                          # tournament news: 3 lines of 32
HEAD=set(range(98,102))                           # fishing paper headlines: 2 lines of 14
def limits(sid,jpw,jpl):
    """(max columns, max lines or None). Dialogue windows are 24 columns; the page-end arrow
    covers column 23, so lines stop at 22."""
    if sid in FIXED: return jpw,jpl
    if sid in TIPS: return 30,3
    if sid in WIDE: return 32,3
    if sid in HEAD: return 14,2
    return 22,None
