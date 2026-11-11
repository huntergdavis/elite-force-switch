#!/usr/bin/env python3
"""Install typed experimental renderervk adapters into pinned tr_init.c."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
marker = '#ifdef USE_RENDERER_DLOPEN\nQ_EXPORT refexport_t* QDECL GetRefAPI'
if text.count(marker) != 1:
    raise SystemExit('unexpected GetRefAPI marker')
text = text.replace(marker, '#include "/work/renderer_export_adapters.inc"\n\n' + marker, 1)
for field, target in (
    ('Shutdown', 'RE_Shutdown'),
    ('AddRefEntityToScene', 'RE_AddRefEntityToScene'),
    ('DrawStretchRaw', 'RE_StretchRaw'),
    ('UploadCinematic', 'RE_UploadCinematic'),
):
    old = f're.{field} = {target};'
    if text.count(old) != 1:
        raise SystemExit(f'unexpected export assignment {field}')
    text = text.replace(old, f're.{field} = Switch_{target};', 1)
path.write_text(text)
