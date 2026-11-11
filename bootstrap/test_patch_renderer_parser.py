#!/usr/bin/env python3
"""Check the parser patch is narrow and rejects reapplication."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
source = root / 'references/VoyagerSP-Android/EFAndroid-SP/app/jni/efcode/renderervk'
patch = root / 'bootstrap/patch_renderer_parser.py'
(root / 'bootstrap/build').mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(dir=root / 'bootstrap/build', prefix='parser-test-') as tmp:
    target = Path(tmp)
    names = ('tr_bsp.c', 'tr_local.h')
    originals = {name: (source / name).read_text() for name in names}
    for name in names:
        (target / name).write_text(originals[name])
    subprocess.run(['python3', str(patch), str(target)], check=True)
    bsp = (target / 'tr_bsp.c').read_text()
    header = (target / 'tr_local.h').read_text()
    assert bsp.replace('\tchar *p;\n\tconst char *token, *s;\n\tchar keyname[MAX_TOKEN_CHARS];',
                       '\tconst char *p, *token, *s;\n\tchar keyname[MAX_TOKEN_CHARS];', 1) == originals['tr_bsp.c']
    assert header.replace('\tchar\t\t*entityParsePoint;', '\tconst char\t*entityParsePoint;', 1) == originals['tr_local.h']
    second = subprocess.run(['python3', str(patch), str(target)], capture_output=True)
    assert second.returncode != 0 and (target / 'tr_bsp.c').read_text() == bsp and (target / 'tr_local.h').read_text() == header
print('Parser cursor patch is limited to two declarations and rejects reapplication')
