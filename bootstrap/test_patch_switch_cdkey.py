#!/usr/bin/env python3
"""Verify the Switch key-write exclusion and preserve the non-Switch writer."""
from pathlib import Path
import subprocess
import tempfile
root = Path(__file__).resolve().parent.parent
source = root / 'references/VoyagerSP-Android/EFAndroid-SP/app/jni/efcode/qcommon/common.c'
patch = root / 'bootstrap/patch_switch_cdkey.py'
(root / 'bootstrap/build').mkdir(parents=True, exist_ok=True)
original = source.read_text()
start = 'static void Com_WriteCDKey( const char *filename, const char *ikey ) {'
end = '\n#endif // STANDALONE'
old_fn = original[original.index(start):original.index(end, original.index(start))]
with tempfile.TemporaryDirectory(dir=root / 'bootstrap/build', prefix='key-test-') as tmp:
    path = Path(tmp) / 'common.c'
    path.write_text(original)
    subprocess.run(['python3', str(patch), str(path)], check=True)
    changed = path.read_text()
    new_fn = changed[changed.index(start):changed.index(end, changed.index(start))]
    switch_body, rest = new_fn.split('#else', 1)
    assert 'return;' in switch_body and 'FS_SV_FOpenFileWrite' not in switch_body and 'umask(' not in switch_body
    assert rest.replace('#endif /* !__SWITCH__ */\n}', '}', 1) == old_fn[len(start):]
    again = subprocess.run(['python3', str(patch), str(path)], capture_output=True)
    assert again.returncode != 0 and path.read_text() == changed
print('Switch CD-key write blocked; original non-Switch writer preserved')
