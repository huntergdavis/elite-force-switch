#!/usr/bin/env python3
"""Exercise actual patched UI file-return paths with stub filesystem imports."""
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
source = root.parent / 'references/VoyagerSP-Android'
scratch = root / 'build'
scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ui-file-cleanup.', dir=scratch) as tmp:
    tmp = Path(tmp)
    for name in ('ui_atoms.cpp', 'ui_players.cpp', 'ui_turbolift.cpp'):
        data = subprocess.check_output(['git', '-C', str(source), 'show',
            f'c73750361cfc22c1afb3a2c160fa9c5df57214db:efgame/src/ui/{name}'])
        (tmp / name).write_bytes(data)
    subprocess.run([sys.executable, str(root / 'patch_ui_file_cleanup.py'), str(tmp)], check=True)
    atoms = (tmp / 'ui_atoms.cpp').read_text()
    players = (tmp / 'ui_players.cpp').read_text()
    repeated = subprocess.run([sys.executable, str(root / 'patch_ui_file_cleanup.py'), str(tmp)], capture_output=True)
    assert repeated.returncode != 0
    assert (tmp / 'ui_atoms.cpp').read_text() == atoms
    assert (tmp / 'ui_players.cpp').read_text() == players
    def function(text, signature):
        start = text.index(signature)
        return text[start:text.index('\n}', start) + 2]
    fonts = function(atoms, ' void UI_LoadFonts( void )')
    generic = function(atoms, 'void UI_LoadGenericMenu(char *fileName)')
    start = players.index('static qboolean UI_ParseAnimationFile(')
    end = players.index('\n\tui.FS_Read( text, len, f );', start)
    # The actual function prefix covers its early exits; parsing is deliberately stubbed.
    animation_prefix = players[start:end] + '\n return qtrue;\n}'
    harness = r'''
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#define FONT_BUFF_LENGTH 16
#define MENULAYOUTLENGTH 16
#define MAX_QPATH 128
#define MAX_ANIMATIONS 1
#define FS_READ 0
#define S_COLOR_RED ""
#define qfalse 0
#define qtrue 1
typedef int fileHandle_t;
typedef int qboolean;
typedef struct { int unused; } animation_t;
static int fake_len, fake_handle, closes, reads;
static int propMapTiny[1][3], propMap[1][3], propMapBig[1][3];
static char menuLayoutBuffer[MENULAYOUTLENGTH];
static int Open(const char*, fileHandle_t *f, int) { *f=fake_handle; return fake_len; }
static void Close(fileHandle_t f) { assert(f==fake_handle && f!=0); ++closes; }
static void Read(void *buf, int len, fileHandle_t f) { assert(f==fake_handle); memset(buf,0,(size_t)len); ++reads; }
static struct { int (*FS_FOpenFile)(const char*,fileHandle_t*,int); void (*FS_FCloseFile)(fileHandle_t); void (*FS_Read)(void*,int,fileHandle_t); } ui = { Open, Close, Read };
static void Com_Printf(const char*, ...) {}
static void Com_sprintf(char *p, int n, const char *fmt, ...) { va_list a; va_start(a,fmt); vsnprintf(p,n,fmt,a); va_end(a); }
static void COM_BeginParseSession() {}
static char *UI_ParseFontParms(char *p, int (*)[3]) { return p; }
static void UI_MenuLayoutSetup(char*) {}
static void UI_ParseMenuLayoutParms(char*) {}
''' + fonts + '\n' + generic + '\n' + animation_prefix + r'''
int main() {
 fake_handle=0; fake_len=-1; UI_LoadFonts(); assert(closes==0);
 fake_handle=7; fake_len=17; UI_LoadFonts(); assert(closes==1 && reads==0);
 fake_len=4; UI_LoadFonts(); assert(closes==2 && reads==1);
 char name[]="menu"; fake_len=17; UI_LoadGenericMenu(name); assert(closes==3);
 fake_len=-1; UI_LoadGenericMenu(name); assert(closes==4);
 fake_handle=0; UI_LoadGenericMenu(name); assert(closes==4);
 animation_t anim; fake_handle=7; fake_len=0; assert(!UI_ParseAnimationFile("x",&anim) && closes==5);
 fake_len=20000; assert(!UI_ParseAnimationFile("x",&anim) && closes==6);
 fake_handle=0; fake_len=-1; assert(!UI_ParseAnimationFile("x",&anim) && closes==6);
 return 0;
}
'''
    cpp = tmp / 'test.cpp'
    exe = tmp / 'test'
    cpp.write_text(harness)
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-Wno-conversion-null',
                    '-Wno-unused-variable', '-Wno-sign-compare', '-Wno-pointer-arith', str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('actual UI font, menu and animation early-return handle cleanup passed with stub filesystem')
