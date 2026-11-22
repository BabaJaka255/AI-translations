# File select prompts, place names, tournament titles, region captions and NPC names (ids below 189).
from tr_notes import NAMES
EN_MISC={
0:"Who's going\nfishing?",
8:"  Start     Erase Data",
1:"Whose record\nwill you erase?",
2:"Erase {CD}'s\nrecord?",
15:"Jetty",16:"Beach",17:"Rocks",18:"Coast",19:"Islet",20:"Ocean",21:" Isle",   # map captions: 6 letters (3 glyph cells)
182:"Breakwater",183:"Beach",184:"Rocks",185:"Coast",186:"Islet",187:"Open Sea",188:"Far Isle",
23:"Black Porgy Cup",24:"Whiting Cup",25:"Opaleye Record",26:"Squid Record",27:"Sea Bass Cup",
28:"Marlin Cup",29:"Grouper Record",373:"Grouper Record",
# envelope addresses (see letters.py): one 16-letter line each
62:"Namino Port",580:"Namino Port",64:"Dragon Palace",67:"Love Beach",70:"Sea Floor",503:"Far South Isle",
74:"Family Board",        # 12 letters fit the title line
78:"Done",79:"Line",      # board keyboard: the last key on the last line / other lines (4 letters)
}
# NPC names are ordinary strings. The player names (4-7) are copied into the name buffer and handled
# with name entry, so they stay out of this table.
EN_MISC.update({k:v for k,v in NAMES.items() if k not in (4,5,6,7)})
