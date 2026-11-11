#!/usr/bin/env python3
"""Avoid forming a member address from a null directory search path."""
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()
old = '''\t\tconst char* pakBasename = path->pack->pakBasename;

\t\tif(!path->pack)
\t\t\tcontinue;
\t\t
\t\tcurpack = path->pack;'''
new = '''\t\tconst char *pakBasename;

\t\tif(!path->pack)
\t\t\tcontinue;

\t\tcurpack = path->pack;
\t\tpakBasename = curpack->pakBasename;'''
if s.count(old) != 1:
    raise SystemExit('unexpected FS_CheckPak0 search-path code')
p.write_text(s.replace(old, new))
