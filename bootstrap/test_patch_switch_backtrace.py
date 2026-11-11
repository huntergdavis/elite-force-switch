#!/usr/bin/env python3
"""Check the Switch backtrace patch preserves the non-Switch symbolizer."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
source = root / 'references/VoyagerSP-Android/EFAndroid-SP/app/jni/sp/sp_integration.c'
patch = root / 'bootstrap/patch_switch_backtrace.py'
(root / 'bootstrap/build').mkdir(parents=True, exist_ok=True)
original = source.read_text()
start = '        Dl_info info;\n'
end = '            SP_LogE("crash", "  #%02d  %p  ?", i, buf[i]);\n'
block = original[original.index(start):original.index(end, original.index(start)) + len(end)]
with tempfile.TemporaryDirectory(dir=root / 'bootstrap/build', prefix='backtrace-test-') as tmp:
    target = Path(tmp) / 'sp_integration.c'
    target.write_text(original)
    subprocess.run(['python3', str(patch), str(target)], check=True)
    changed = target.read_text()
    assert '#ifndef __SWITCH__\n#include <dlfcn.h>\n#endif' in changed
    assert '#else\n' + block + '#endif' in changed
    assert '/* Switch has no dladdr; log raw frame addresses. */' in changed
    second = subprocess.run(['python3', str(patch), str(target)], capture_output=True)
    assert second.returncode != 0 and target.read_text() == changed
print('Switch raw-address patch and unchanged non-Switch symbolizer verified')
