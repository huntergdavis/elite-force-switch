#!/usr/bin/env python3
"""Apply guarded early-return cleanup to the pinned UI input."""
from pathlib import Path
import re
import sys
root = Path(sys.argv[1])
updated = {}
def edit(name, start, end, handle, count):
    path = root / name
    text = updated.get(path, path.read_text())
    a = text.index(start); b = text.index(end, a) + (2 if end == '\n}' else 0)
    part = text[a:b]
    part, n = re.subn(r'(fileHandle_t\s+' + handle + r')\s*;', r'\1 = 0;', part, count=1)
    if n != 1: raise SystemExit('unexpected handle declaration')
    pattern = r'(?m)^([ \t]*)return(?:\s+qfalse)?;'
    matches = list(re.finditer(pattern, part))
    # Only the specified early exits, before the first file read, own this handle.
    first_read = part.index('ui.FS_Read(')
    targets = [m for m in matches if m.start() < first_read]
    if len(targets) != count: raise SystemExit('unexpected early returns')
    for m in reversed(targets):
        part = part[:m.start()] + m.group(1) + 'if (' + handle + ') ui.FS_FCloseFile( ' + handle + ' );\n' + part[m.start():]
    updated[path] = text[:a] + part + text[b:]
edit('ui_atoms.cpp', ' void UI_LoadFonts( void )', '\nvoid UI_LoadGenericMenu', 'f', 2)
edit('ui_atoms.cpp', 'void UI_LoadGenericMenu(char *fileName)', '\nint UI_FindMenuID', 'fileHandle', 2)
edit('ui_players.cpp', 'static qboolean UI_ParseAnimationFile(', '\n}', 'f', 2)
for p, text in updated.items(): p.write_text(text)
