#!/usr/bin/env python3
"""Use typed cursor bridges for the pinned shader parser call sites."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
marker = '#include "tr_local.h"'
if text.count(marker) != 1:
    raise SystemExit('unexpected shader include marker')
text = text.replace(marker, marker + '\n#include "/work/renderer_const_parser.h"', 1)
counts = {'COM_ParseExt(': 0, 'SkipRestOfLine(': 0, 'SkipBracedSection(': 0}
replacements = {'COM_ParseExt(': 'Switch_ParseExt(',
                'SkipRestOfLine(': 'Switch_SkipRestOfLine(',
                'SkipBracedSection(': 'Switch_SkipBracedSection('}
lines = []
for line in text.splitlines(keepends=True):
    if not line.lstrip().startswith('//'):
        for old, new in replacements.items():
            counts[old] += line.count(old)
            line = line.replace(old, new)
    lines.append(line)
if counts != {'COM_ParseExt(': 76, 'SkipRestOfLine(': 7, 'SkipBracedSection(': 4}:
    raise SystemExit(f'unexpected shader parser call sites: {counts}')
path.write_text(''.join(lines))
