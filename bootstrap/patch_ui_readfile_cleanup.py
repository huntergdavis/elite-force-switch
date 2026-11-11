#!/usr/bin/env python3
"""Free engine FS_ReadFile buffers before fatal oversized UI-data errors."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
pattern = re.compile(r'(if\s*\(\s*len\s*>\s*MAX[A-Z_]+\s*\)\s*\{\s*)(?=(?:ui\.Error|Com_Error)\s*\()')
updated = {}
for name, expected in [('ui_atoms.cpp', 2), ('ui_turbolift.cpp', 6)]:
    path = root / name
    source = path.read_text()
    matches = list(pattern.finditer(source))
    if len(matches) != expected:
        raise SystemExit(f'unexpected oversized UI-data branches in {name}: {len(matches)}')
    # These pinned branches all follow successful ui.FS_ReadFile into buffer.
    for match in matches:
        before = source[max(0, match.start()-600):match.start()]
        if not re.search(r'ui\.FS_ReadFile\s*\([^;]*&buffer\s*\)', before):
            raise SystemExit(f'oversized branch lacks expected FS_ReadFile context in {name}')
    updated[path] = pattern.sub(r'\1ui.FS_FreeFile( buffer );\n\t\t', source)
for path, source in updated.items():
    path.write_text(source)
