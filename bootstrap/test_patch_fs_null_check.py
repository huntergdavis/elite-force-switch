#!/usr/bin/env python3
"""Check the pinned FS search-path guard transformation."""
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
source = root.parent / 'references/VoyagerSP-Android/EFAndroid-SP/app/jni/efcode/qcommon/files.c'
scratch = root / 'build'
scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='fs-null.', dir=scratch) as tmp:
    path = Path(tmp) / 'files.c'
    before = source.read_text()
    path.write_text(before)
    command = [sys.executable, str(root / 'patch_fs_null_check.py'), str(path)]
    subprocess.run(command, check=True)
    after = path.read_text()
    section = after[after.index('static void FS_CheckPak0( void )'):]
    assert section.index('if(!path->pack)') < section.index('pakBasename = curpack->pakBasename;')
    assert before.count('const char* pakBasename = path->pack->pakBasename;') == 1
    assert 'const char* pakBasename = path->pack->pakBasename;' not in after
    result = subprocess.run(command, capture_output=True)
    assert result.returncode != 0 and path.read_text() == after
print('null guard precedes member access; unexpected repeat is rejected')
