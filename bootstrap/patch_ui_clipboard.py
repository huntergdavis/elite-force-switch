#!/usr/bin/env python3
"""Release the engine-owned clipboard allocation after copying it to the UI."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
old_decl = '    char *Sys_GetClipboardData( void );'
old_fn = 'static void UII_GetClipboardData(char* buf,int bufsize){ char* c=Sys_GetClipboardData(); sp_strncpyz(buf, c?c:"", bufsize); }'
new_fn = 'static void UII_GetClipboardData(char* buf,int bufsize){ char* c=Sys_GetClipboardData(); sp_strncpyz(buf, c?c:"", bufsize); if(c) Z_Free(c); }'
if s.count(old_decl) != 1 or s.count(old_fn) != 1:
    raise SystemExit('unexpected UI clipboard bridge')
s = s.replace(old_decl, old_decl + '\n    void  Z_Free( void *ptr );').replace(old_fn, new_fn)
path.write_text(s)
