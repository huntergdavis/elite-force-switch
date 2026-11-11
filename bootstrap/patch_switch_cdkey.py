#!/usr/bin/env python3
"""Disable CD-key writes on Switch until secure storage semantics exist."""
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
if 'CD-key persistence is unavailable in this Switch build.' in s:
    raise SystemExit('Switch CD-key patch already applied')
start = 'static void Com_WriteCDKey( const char *filename, const char *ikey ) {'
end = '''out:
#ifndef _WIN32
\tumask(savedumask);
#else
\t;
#endif
}'''
if s.count(start) != 1 or s.count(end) != 1:
    raise SystemExit('unexpected CD-key writer')
s = s.replace(start, start + '''
#ifdef __SWITCH__
    (void)filename;
    (void)ikey;
    Com_Printf("CD-key persistence is unavailable in this Switch build.\\n");
    return;
#else''', 1)
s = s.replace(end, end[:-1] + '#endif /* !__SWITCH__ */\n}', 1)
p.write_text(s)
