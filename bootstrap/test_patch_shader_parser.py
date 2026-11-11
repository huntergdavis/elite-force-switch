#!/usr/bin/env python3
"""Check the shader parser rewrite is guarded and rejects reapplication."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
source = root / 'references/VoyagerSP-Android/EFAndroid-SP/app/jni/efcode/renderervk/tr_shader.c'
patch = root / 'bootstrap/patch_shader_parser.py'
(root / 'bootstrap/build').mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(dir=root / 'bootstrap/build', prefix='shader-test-') as tmp:
    target = Path(tmp) / 'tr_shader.c'
    target.write_text(source.read_text())
    subprocess.run(['python3', str(patch), str(target)], check=True)
    changed = target.read_text()
    assert changed.count('Switch_ParseExt(') == 76
    assert changed.count('Switch_SkipRestOfLine(') == 7
    assert changed.count('Switch_SkipBracedSection(') == 4
    again = subprocess.run(['python3', str(patch), str(target)], capture_output=True)
    assert again.returncode != 0 and target.read_text() == changed
print('Shader parser rewrite matches pinned call sites and rejects reapplication')
