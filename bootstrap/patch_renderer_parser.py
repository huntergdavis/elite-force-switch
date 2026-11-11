#!/usr/bin/env python3
"""Align the renderer's mutable entity parse cursors with the engine parser."""
from pathlib import Path
import sys

renderer = Path(sys.argv[1])
bsp = renderer / 'tr_bsp.c'
header = renderer / 'tr_local.h'
bsp_text = bsp.read_text()
header_text = header.read_text()
old_bsp = '\tconst char *p, *token, *s;\n\tchar keyname[MAX_TOKEN_CHARS];'
new_bsp = '\tchar *p;\n\tconst char *token, *s;\n\tchar keyname[MAX_TOKEN_CHARS];'
old_header = '\tconst char\t*entityParsePoint;'
new_header = '\tchar\t\t*entityParsePoint;'
if bsp_text.count(old_bsp) != 1 or header_text.count(old_header) != 1:
    raise SystemExit('unexpected entity parser declarations')
bsp.write_text(bsp_text.replace(old_bsp, new_bsp, 1))
header.write_text(header_text.replace(old_header, new_header, 1))
