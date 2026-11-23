"""Every piece of text in the game (all of it lives in bank $C1, ROM 0x15EE8-0x17E05).

STRINGS: '/'-terminated strings reached through a 16-bit pointer in bank $80 code. English versions are
         written to free space in bank $E0 and the pointer operands are repointed.
TABLES:  fixed-width records (base + index * stride) drawn as a fixed number of columns.
"""
# id: (address in $C1, [pointer operand ROM offsets], notes)
STRINGS = {
    'records_erased': (0x5EE8, [0x8520], 'Shown when the save records fail their check.'),
    'menu_by_island': (0x5F0E, [0x8658], 'Records menu, pick an island. ^ = cursor stop.'),
    'menu_by_fish':   (0x603C, [0x89D9], 'Records menu, pick a fish (2 columns). ^ = cursor stop.'),
    'record_header':  (0x62C4, [0x8A56], 'Column header above the record list.'),
    'name_entry':     (0x66F7, [0x8D96, 0x8F53], 'Name entry prompt and keyboard (built by script_en).'),
    'todays_catch':   (0x686E, [0x955F], 'Catch result screen title.'),
    'new_record':     (0x6879, [0x9665, 0x9693], 'Catch result screen, record broken.'),
    'top_menu':       (0x723F, [0x8DB6], 'Main menu and angler list frame.'),
    'intro':          (0x72B3, [0xDDF7], 'Opening story crawl. FFFC/FFFD change the scene.'),
    'ending':         (0x7C4F, [0xDE13], 'Ending crawl.'),
}

# id: (base, count, stride, columns, notes)
TABLES = {
    'island_title':  (0x5FCC, 7, 16, 16, 'Island name, big heading on the island records page. Centered.'),
    'fish_title':    (0x6170, 20, 17, 16, 'Fish name, big heading on the fish records page. Centered.'),
    'record_spot':   (0x62E1, 64, 16, 13, 'Spot + island column of a record line (relocated, 18 columns).'),
    'method':        (0x6880, 5, 12, 12, 'Fishing method label (fishing view). Box width = first word.'),
    'method2':       (0x68BC, 5, 12, 12, 'Fishing method (catch result screen). Centered.'),
    'bait':          (0x68F8, 18, 20, 20, 'Lure / bait name. Centered.'),
    'fish':          (0x6A60, 20, 12, 12, 'Fish name on the catch result screen (relocated, 14 columns).'),
    'sub_spot':      (0x6B50, 64, 16, 16, 'Sub-spot label on the spot map. Right-aligned.'),
    'spot':          (0x6F50, 32, 18, 18, 'Spot label on the island map. Right-aligned.'),
    'island':        (0x7190, 7, 8, 8, 'Island label (map HUD). Right-aligned.'),
    'place':         (0x72A7, 2, 6, 6, 'Angler list, where the angler is (relocated, 8 columns).'),
}
