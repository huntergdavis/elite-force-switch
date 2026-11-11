#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import tempfile
root = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='gamepad-patch.', dir=root / 'build') as tmp:
    path = Path(tmp) / 'common.c'
    path.write_bytes(subprocess.check_output(['git', '-C', str(root.parent / 'references/VoyagerSP-Android'), 'show', 'c73750361cfc22c1afb3a2c160fa9c5df57214db:EFAndroid-SP/app/jni/efcode/qcommon/common.c']))
    cmd = [sys.executable, str(root / 'patch_switch_gamepad_defaults.py'), str(path)]
    subprocess.run(cmd, check=True)
    text = path.read_text()
    assert text.index('exec autoexec.cfg') < text.index('Switch_InstallGamepadDefaults();')
    assert '#ifdef __SWITCH__\n\t\tSwitch_InstallGamepadDefaults();\n#endif' in text
    assert subprocess.run(cmd, capture_output=True).returncode != 0
    assert path.read_text() == text
print('pinned gamepad config patch verified')
