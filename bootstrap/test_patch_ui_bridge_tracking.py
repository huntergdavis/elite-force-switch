#!/usr/bin/env python3
"""Check pinned UI bridge tracking transformation and fail-closed repeat."""
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
source = root.parent / 'references/VoyagerSP-Android'
scratch = root / 'build'; scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ui-track-patch.', dir=scratch) as tmp:
    path = Path(tmp) / 'sp_ui_bridge.cpp'
    path.write_bytes(subprocess.check_output(['git', '-C', str(source), 'show',
        'c73750361cfc22c1afb3a2c160fa9c5df57214db:EFAndroid-SP/app/jni/sp/sp_ui_bridge.cpp']))
    cmd = [sys.executable, str(root / 'patch_ui_bridge_tracking.py'), str(path)]
    subprocess.run(cmd, check=True)
    text = path.read_text()
    for call in ('g_ux = getapi()', 'g_ux->UI_Init(UI_API_VERSION, &g_uii)',
                 'g_ux->UI_Shutdown()', 'g_ux->UI_Refresh(t)', 'g_ux->UI_KeyEvent(key)',
                 'g_ux->UI_MouseEvent(dx,dy)', 'g_ux->UI_GetActiveMenu(NULL,&fs)',
                 'g_ux->UI_SetActiveMenu(name, "")', 'result=g_ux->UI_ConsoleCommand()',
                 'g_ux->UI_DrawConnect(sv,upd)'):
        assert 'UI_TRACK_CALL(' + call + ')' in text
    assert text.count('UI_TRACK_CALL(') == 11 # definition plus ten call sites
    assert 'g_uii.FS_FOpenFile=UII_TrackedOpen' in text
    assert 'g_uii.FS_FCloseFile=UII_TrackedClose' in text
    assert 'g_uii.FS_ReadFile=UII_TrackedReadFile' in text
    assert 'g_uii.FS_FreeFile=UII_TrackedFreeFile' in text
    assert subprocess.run(cmd, capture_output=True).returncode != 0
    assert path.read_text() == text
print('pinned bridge entry and file-import instrumentation verified; repeat rejected')
