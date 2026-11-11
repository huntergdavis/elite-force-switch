#!/usr/bin/env python3
"""Capture the clean game frame before drawing the NX GL1 pause menu."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_nx_gl1_menu_flash.py <cl_scrn.c>')
screen = Path(sys.argv[1])
text = screen.read_text()
marker = '\tint spSuppressMenu = SP_TakeMenuSuppress();'
if text.count(marker) != 1 or 'NX_CapturePendingBeforeMenu' in text:
    raise SystemExit('unexpected SP menu suppression')
text = text.replace(marker, marker + '''
\tif (spSuppressMenu) {
\t\textern int NX_CapturePendingBeforeMenu(void);
\t\tif (NX_CapturePendingBeforeMenu()) spSuppressMenu = 0;
\t}''', 1)
screen.write_text(text)
