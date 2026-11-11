#!/usr/bin/env python3
"""Exercise the eight actual patched oversized-data branches with stubs."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
source = root.parent / 'references/VoyagerSP-Android'
scratch = root / 'build'
scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ui-readfile-cleanup.', dir=scratch) as tmp:
    tmp = Path(tmp)
    for name in ('ui_atoms.cpp', 'ui_turbolift.cpp'):
        (tmp / name).write_bytes(subprocess.check_output(['git', '-C', str(source), 'show',
            f'c73750361cfc22c1afb3a2c160fa9c5df57214db:efgame/src/ui/{name}']))
    command = [sys.executable, str(root / 'patch_ui_readfile_cleanup.py'), str(tmp)]
    subprocess.run(command, check=True)
    results = [(tmp / n).read_text() for n in ('ui_atoms.cpp', 'ui_turbolift.cpp')]
    assert subprocess.run(command, capture_output=True).returncode != 0
    assert results == [(tmp / n).read_text() for n in ('ui_atoms.cpp', 'ui_turbolift.cpp')]
    pattern = re.compile(r'if\s*\(\s*len\s*>\s*MAX[A-Z_]+\s*\)\s*\{\s*ui\.FS_FreeFile\( buffer \);.*?\n\s*\}', re.S)
    blocks = [m.group() for text in results for m in pattern.finditer(text)]
    assert len(blocks) == 8
    names = set(re.findall(r'\bMAX[A-Z_]+\b', '\n'.join(blocks)))
    # Pinning the count and names makes unexpected upstream edits fail closed.
    assert names == {'MAXBUTTONTEXT', 'MAXMENUTEXT', 'MAXTURBOLIFTTEXT', 'MAXHOLODECKTEXT',
                     'MAXLOGSTEXT', 'MAXPADDSTEXT', 'MAXTRANSPORTERTEXT', 'MAXLIBRARYTEXT'}
    harness = r'''
#include <cassert>
#define ERR_FATAL 1
static int frees, errors;
static char data;
static void Free(void *p) { assert(p==&data); ++frees; }
static void Error(int, const char*, ...) { assert(frees==errors+1); ++errors; throw 1; }
static void Com_Error(int level,const char *fmt,...) { Error(level,fmt); }
static const char *va(const char*,...) { return "formatted"; }
static struct { void (*FS_FreeFile)(void*); void (*Error)(int,const char*,...); } ui = {Free,Error};
''' + ''.join(f'#define {name} 1\n' for name in sorted(names))
    for i, block in enumerate(blocks):
        harness += f'\nstatic void branch{i}(int len) {{ char *buffer=&data; const char *filePtr="x"; (void)filePtr; {block} }}\n'
    harness += '\nint main() {\n'
    for i in range(len(blocks)):
        harness += f' branch{i}(0); assert(frees=={i}); try {{ branch{i}(2); assert(false); }} catch(int) {{ assert(frees=={i+1} && errors=={i+1}); }}\n'
    harness += '}\n'
    cpp = tmp / 'test.cpp'; exe = tmp / 'test'; cpp.write_text(harness)
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('eight oversized UI-data branches free buffers before fatal error; stubs used')
