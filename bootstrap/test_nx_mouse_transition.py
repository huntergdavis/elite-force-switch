#!/usr/bin/env python3
"""Test actual injected mouse-deactivation function with host SDL stubs."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

source = Path(sys.argv[1]).read_text()
match = re.search(r'static void IN_DeactivateMouse\( qboolean isFullscreen, qboolean showSystemCursor \)\n\{.*?\n\}', source, re.S)
if not match:
    raise SystemExit('mouse deactivation function not found')
harness = r'''
#include <assert.h>
#define USE_FLEXIBLE_DISPLAY 1
#define SDL_INIT_VIDEO 1
#define SDL_TRUE 1
#define SDL_FALSE 0
#define SDL_WINDOW_MOUSE_FOCUS 2
#define qfalse 0
typedef int qboolean;
typedef struct { int integer; } cvar_t;
static cvar_t flexible = {1}, *cl_flexibleDisplay = &flexible;
static int mouseLastX=80, mouseLastY=40, mouseActive=1, mouseAvailable=1;
static int visibility=-1, warpx=-1, warpy=-1, focused=1, video=1, ungrab, relative;
static void *SDL_window;
static struct { struct { int vidWidth, vidHeight; } glconfig; } cls = {{640,480}};
static int SDL_WasInit(int x) { (void)x; return video; }
static void SDL_ShowCursor(int x) { visibility=x; }
static void IN_GobbleMotionEvents(void) { }
static void SDL_SetWindowGrab(void *w,int x) { (void)w; ungrab=x; }
static void SDL_SetRelativeMouseMode(int x) { relative=x; }
static int SDL_GetWindowFlags(void *w) { (void)w; return focused ? SDL_WINDOW_MOUSE_FOCUS : 0; }
static void SDL_WarpMouseInWindow(void *w,int x,int y) { (void)w; warpx=x; warpy=y; }
''' + match.group(0) + r'''
int main(void) {
 IN_DeactivateMouse(0, 0); assert(!visibility && !mouseActive && warpx==80 && warpy==40 && !ungrab && !relative);
 mouseActive=1; flexible.integer=0; IN_DeactivateMouse(0,1); assert(visibility && warpx==320 && warpy==240);
 mouseActive=1; focused=0; warpx=-1; IN_DeactivateMouse(1,1); assert(!visibility && warpx==-1);
 mouseActive=1; video=0; visibility=-1; IN_DeactivateMouse(0,1); assert(visibility==-1 && mouseActive);
 return 0;
}
'''
scratch=Path(__file__).resolve().parent / 'build'; scratch.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='nx-transition.',dir=scratch) as tmp:
    c=Path(tmp)/'test.c'; exe=Path(tmp)/'test'; c.write_text(harness)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('mouse release, visibility, focus and saved-position checks passed')
