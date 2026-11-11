#!/usr/bin/env python3
"""Exercise the injected SP cursor math and UI sync with host stubs."""
import subprocess
import sys
import tempfile
from pathlib import Path

source = Path(sys.argv[1]).read_text()
start = source.index('void IN_UpdateMouseMenuPosition(')
end = source.index('\n#endif', start)
functions = source[start:end]
harness = r'''
#include <assert.h>
#include <math.h>
#include <stddef.h>
#define qtrue 1
#define qfalse 0
#define SCREEN_WIDTH 640
#define SCREEN_HEIGHT 480
#define UI_MOUSE_EVENT 1
typedef struct { int integer; } cvar_t;
static cvar_t enabled = {1}, *cl_flexibleDisplay = &enabled;
static int mouseLastX, mouseLastY, mouseActive, in_showUICursor, seen, dx, dy;
static float mouse640X, mouse640Y;
static void *uivm;
static void CL_AdjustToUI(float *x, float *y, void *a, void *b) { (void)x; (void)y; (void)a; (void)b; }
static int SPUI_IsActive(void) { return 1; }
static void SPUI_MouseEvent(int x, int y) { ++seen; dx=x; dy=y; }
static void VM_Call(void *vm, int event, int x, int y) { (void)vm; (void)event; (void)x; (void)y; }
static unsigned SDL_GetMouseState(int *x, int *y) { *x=123; *y=45; return 0; }
''' + functions + r'''
int main(void) {
 int x,y;
 IN_UpdateMouseMenuPosition(900, -3, &x, &y);
 assert(x == 639 && y == 0 && in_showUICursor);
 IN_SyncMousePosition();
 assert(seen == 2 && dx == 123 && dy == 45);
 enabled.integer=0; IN_SyncMousePosition(); assert(seen == 2);
 return 0;
}
'''
scratch = Path(__file__).resolve().parent / 'build'
scratch.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='nx-cursor.', dir=scratch) as tmp:
    c = Path(tmp) / 'test.c'
    exe = Path(tmp) / 'test'
    c.write_text(harness)
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(c), '-lm', '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('cursor clamping, SP UI sync and disabled-path checks passed')
