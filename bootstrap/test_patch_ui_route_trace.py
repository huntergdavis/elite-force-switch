#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import tempfile
root = Path(__file__).resolve().parent
repo = root.parent / 'references/VoyagerSP-Android'
rev = 'c73750361cfc22c1afb3a2c160fa9c5df57214db:'
with tempfile.TemporaryDirectory(prefix='ui-route.', dir=root / 'build') as tmp:
    paths = [Path(tmp) / 'cl_ui.c', Path(tmp) / 'sp_ui_bridge.cpp']
    for path, src in zip(paths, ['EFAndroid-SP/app/jni/efcode/client/cl_ui.c', 'EFAndroid-SP/app/jni/sp/sp_ui_bridge.cpp']):
        path.write_bytes(subprocess.check_output(['git', '-C', str(repo), 'show', rev + src]))
    cmd = [sys.executable, str(root / 'patch_ui_route_trace.py'), *map(str, paths)]
    subprocess.run(cmd, check=True)
    c, b = [p.read_text() for p in paths]
    for event in ('sp_ui enabled', 'sp_ui disabled', 'SP active', 'VM fallback'):
        assert event in c
    for event in ('load requested', 'already active', 'dlopen failed', 'symbol missing', 'invalid API', 'entering UI_Init', 'UI_Init returned', 'shutdown requested', 'closed'):
        assert event in b
    assert subprocess.run(cmd, capture_output=True).returncode != 0
    assert [p.read_text() for p in paths] == [c, b]
print('pinned route tracing patch verified')
