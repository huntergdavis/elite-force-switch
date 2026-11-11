#!/usr/bin/env python3
"""Test the pinned patched clipboard adapter with stubbed engine ownership."""
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
source = root.parent / 'references/VoyagerSP-Android'
scratch = root / 'build'
scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ui-clipboard.', dir=scratch) as tmp:
    tmp = Path(tmp)
    bridge = tmp / 'sp_ui_bridge.cpp'
    bridge.write_bytes(subprocess.check_output(['git', '-C', str(source), 'show',
        'c73750361cfc22c1afb3a2c160fa9c5df57214db:EFAndroid-SP/app/jni/sp/sp_ui_bridge.cpp']))
    cmd = [sys.executable, str(root / 'patch_ui_clipboard.py'), str(bridge)]
    subprocess.run(cmd, check=True)
    text = bridge.read_text()
    before = text
    assert subprocess.run(cmd, capture_output=True).returncode != 0 and bridge.read_text() == before
    def line(prefix):
        matches = [line for line in text.splitlines() if line.startswith(prefix)]
        assert len(matches) == 1
        return matches[0]
    harness = r'''
#include <cassert>
#include <cstring>
static char text[]="abcdef";
static bool present=true;
static int freed;
static char *Sys_GetClipboardData() { return present ? text : nullptr; }
static void Z_Free(void *p) { assert(p==text); ++freed; }
''' + line('static void sp_strncpyz(') + '\n' + line('static void UII_GetClipboardData(') + r'''
int main() {
 char out[8] = {};
 UII_GetClipboardData(out,sizeof(out)); assert(!strcmp(out,"abcdef") && freed==1);
 UII_GetClipboardData(out,4); assert(!strcmp(out,"abc") && freed==2);
 UII_GetClipboardData(out,0); assert(freed==3);
 present=false; UII_GetClipboardData(out,sizeof(out)); assert(!strcmp(out,"") && freed==3);
 return 0;
}
'''
    cpp = tmp / 'test.cpp'; exe = tmp / 'test'; cpp.write_text(harness)
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('clipboard copied, truncated, null and zero-length cases release owned allocations')
