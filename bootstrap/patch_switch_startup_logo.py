#!/usr/bin/env python3
"""Test-only: omit automatic SP startup logo on Switch, preserving explicit movies."""
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
old = '#ifdef CINEMATICS_LOGO\n\t\t\tCbuf_AddText ("cinematic " CINEMATICS_LOGO "\\n");\n#endif'
new = '#if defined(CINEMATICS_LOGO) && !defined(__SWITCH__)\n\t\t\tCbuf_AddText ("cinematic " CINEMATICS_LOGO "\\n");\n#endif'
if s.count(old) != 1:
    raise SystemExit('unexpected automatic startup cinematic block')
p.write_text(s.replace(old, new))
