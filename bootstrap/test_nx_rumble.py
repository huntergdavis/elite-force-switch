#!/usr/bin/env python3
"""Host exercise of the SP rumble function injected into NX input."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

source = Path(sys.argv[1]).read_text()
match = re.search(r'void IN_Rumble\( float low, float high, int ms \)\n\{.*?\n\}', source, re.S)
if not match:
    raise SystemExit('missing rumble implementation')
harness = r'''
#include <assert.h>
typedef unsigned short Uint16;
typedef unsigned int Uint32;
typedef struct { int integer; float value; } cvar_t;
#define SDL_VERSION_ATLEAST(a,b,c) 1
static int controller, motors = 1, calls, lo_value, hi_value, ms_value;
static int *gamepad;
static cvar_t on = { 1, 1 }, strength = { 1, 0.5f };
static cvar_t *in_rumble = &on, *in_rumbleStrength = &strength;
static int SDL_GameControllerHasRumble(int *p) { (void)p; return motors; }
static void SDL_GameControllerRumble(int *p, Uint16 lo, Uint16 hi, Uint32 ms) {
 (void)p; calls++; lo_value = lo; hi_value = hi; ms_value = ms;
}
''' + match.group(0) + r'''
int main(void) {
 IN_Rumble(1, 1, 90); assert(calls == 0);
 gamepad = &controller; on.integer = 0; IN_Rumble(1, 1, 90); assert(calls == 0);
 on.integer = 1; motors = 0; IN_Rumble(1, 1, 90); assert(calls == 0);
 motors = 1; IN_Rumble(2, -1, 90);
 assert(calls == 1 && lo_value == 32767 && hi_value == 0 && ms_value == 90);
 return 0;
}
'''
scratch = Path(__file__).resolve().parent / 'build'
scratch.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='nx-rumble.', dir=scratch) as tmp:
    c = Path(tmp) / 'test.c'
    exe = Path(tmp) / 'test'
    c.write_text(harness)
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('SP rumble no-pad, disabled, unavailable, clamp and scaling checks passed')
