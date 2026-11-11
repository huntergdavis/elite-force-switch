#!/usr/bin/env python3
"""Exercise the patched SP menu-suppression decision using the pinned client."""
from pathlib import Path
import os
import subprocess
import tempfile

root = Path(__file__).resolve().parent
upstream = Path(os.environ.get('ELITE_SP_REFERENCE', root.parent / 'references/VoyagerSP-Android'))
rev = 'c73750361cfc22c1afb3a2c160fa9c5df57214db'
screen = subprocess.check_output([
    'git', '-C', str(upstream), 'show', f'{rev}:EFAndroid-SP/app/jni/efcode/client/cl_scrn.c'
], text=True)
scratch = root / 'build'
scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='nx-menu-flash.', dir=scratch) as tmp:
    tmp = Path(tmp)
    patched = tmp / 'cl_scrn.c'
    patched.write_text(screen)
    subprocess.run(['python3', str(root / 'patch_nx_gl1_menu_flash.py'), str(patched)], check=True)
    text = patched.read_text()
    start = text.index('int spSuppressMenu = SP_TakeMenuSuppress();')
    end = text.index('// the menu draws next', start)
    decision = text[start:end]
    fixture = r'''
#include <assert.h>
static int armed, captured, calls;
int SP_TakeMenuSuppress(void) { int v=armed; armed=0; return v; }
int NX_CapturePendingBeforeMenu(void) { ++calls; return captured; }
static int suppression(void) {
''' + decision + r'''
return spSuppressMenu;
}
int main(void) {
  armed=0; captured=1; calls=0; assert(suppression()==0 && calls==0);
  armed=1; captured=1; calls=0; assert(suppression()==0 && calls==1);
  armed=1; captured=0; calls=0; assert(suppression()==1 && calls==1);
  return 0;
}
'''
    source, binary = tmp / 'fixture.c', tmp / 'fixture'
    source.write_text(fixture)
    subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)

print('NX GL1 preserves the menu on successful pre-capture and falls back on failure (renderer stubbed).')
