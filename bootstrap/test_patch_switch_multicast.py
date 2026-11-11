#!/usr/bin/env python3
"""Check patch application is guarded and preserves non-Switch multicast source."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
source = root / 'references/VoyagerSP-Android/EFAndroid-SP/app/jni/efcode/qcommon/net_ip.c'
patch = root / 'bootstrap/patch_switch_multicast.py'
(root / 'bootstrap/build').mkdir(parents=True, exist_ok=True)
original = source.read_text()
start = 'void NET_SetMulticast6(void)\n{'
end = '\n/*\n====================\nNET_OpenSocks'
original_multicast = original[original.index(start):original.index(end, original.index(start))]
with tempfile.TemporaryDirectory(dir=root / 'bootstrap/build', prefix='multicast-test-') as tmp:
    target = Path(tmp) / 'net_ip.c'
    target.write_text(original)
    subprocess.run(['python3', str(patch), str(target)], check=True)
    changed = target.read_text()
    assert '#else\n' + original_multicast + '\n#endif' in changed
    send = changed[changed.index('void Sys_SendPacket('):]
    assert send.index('if (to.type == NA_MULTICAST6) return;') < send.index('NetadrToSockadr( &to')
    second = subprocess.run(['python3', str(patch), str(target)], capture_output=True)
    assert second.returncode != 0 and target.read_text() == changed
print('Switch multicast patch guards and non-Switch functions verified')
