#!/usr/bin/env python3
"""Convert selected pinned UI aggregate coordinates to integral values."""
from pathlib import Path
import re
import sys
root = Path(sys.argv[1])
items = [
    ('ui_game.cpp', r'(SGBLIP_MIN_X,\s*)(SGPIC_Y\s*-\s*4\s*-\s*SGPIC_H\s*-\s*4\s*-\s*4)(\s*,)', 1),
    ('ui_video.cpp', r'(30,\s*)(250\s*\+\s*6\s*\+\s*\(MENU_BUTTON_MED_HEIGHT\s*\*\s*1\.5\))(\s*,)', 1),
    ('ui_video.cpp', r'(30,\s*)(250\s*\+\s*\(2\s*\*\s*\(6\s*\+\s*\(MENU_BUTTON_MED_HEIGHT\s*\*\s*1\.5\)\)\))(\s*,)', 1),
]
updates = {}
for name, expression, expected in items:
    path = root / name
    source = updates.get(path, path.read_text())
    source, count = re.subn(expression, r'\1static_cast<int>(\2)\3', source)
    if count != expected: raise SystemExit('unexpected UI coordinate: ' + name)
    updates[path] = source
for path, source in updates.items(): path.write_text(source)
