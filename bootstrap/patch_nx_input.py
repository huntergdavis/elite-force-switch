#!/usr/bin/env python3
"""Adapt pinned VoyagerNX input to the SP engine's rumble entry point."""
import re
import sys
from pathlib import Path

nx, sp = map(Path, sys.argv[1:])
t = nx.read_text()
s = sp.read_text()
match = re.search(r'void IN_Rumble\( float low, float high, int ms \)\n\{.*?\n\}', s, re.S)
if not match:
    raise SystemExit('SP rumble implementation missing')
marker = 'static SDL_GameController *gamepad = NULL;'
if t.count(marker) != 1 or 'void IN_Rumble(' in t:
    raise SystemExit('unexpected NX gamepad declarations')
t = t.replace(marker, marker + '\nstatic cvar_t *in_rumble = NULL;\nstatic cvar_t *in_rumbleStrength = NULL;')
marker = '\tin_keyboardDebug = Cvar_Get( "in_keyboardDebug", "0", CVAR_ARCHIVE );'
if t.count(marker) != 1:
    raise SystemExit('unexpected NX input initialization')
t = t.replace(marker, marker + '\n\tin_rumble = Cvar_Get( "in_rumble", "1", CVAR_ARCHIVE );\n\tin_rumbleStrength = Cvar_Get( "in_rumbleStrength", "1.0", CVAR_ARCHIVE );')
marker = '\t\tSDL_GameControllerClose(gamepad);'
if t.count(marker) != 2:
    raise SystemExit('unexpected NX controller close sites')
t = t.replace(marker, '#if SDL_VERSION_ATLEAST(2, 0, 9)\n\t\tSDL_GameControllerRumble(gamepad, 0, 0, 0);\n#endif\n' + marker)
# Reuse SP's flexible-display cursor math and sync against the native SP UI.
start = s.index('void IN_UpdateMouseMenuPosition(')
end = s.index('\n#endif', start)
mouse_functions = s[start:end]
marker = '#include "../client/client.h"'
if t.count(marker) != 1:
    raise SystemExit('unexpected NX client include')
t = t.replace(marker, marker + '\n#include "../../sp/sp_ui.h"')
marker = 'static qboolean mouseActive = qfalse;'
if t.count(marker) != 1 or 'IN_SyncMousePosition' in t:
    raise SystemExit('unexpected NX mouse declarations')
t = t.replace(marker, marker + '\n#ifdef USE_FLEXIBLE_DISPLAY\nstatic int mouseLastX, mouseLastY;\nstatic float mouse640X, mouse640Y;\nstatic qboolean in_showUICursor;\n#endif')
marker = '\tSDL_window = (SDL_Window *)windowData;'
if t.count(marker) != 1:
    raise SystemExit('unexpected NX input window setup')
t = t.replace(marker, marker + '\n#ifdef USE_FLEXIBLE_DISPLAY\n\tSDL_GetMouseState(&mouseLastX, &mouseLastY);\n#endif')
# Match SP's relative-to-absolute transition for flexible-display menus.
old = 'static void IN_DeactivateMouse( qboolean isFullscreen )'
if t.count(old) != 1:
    raise SystemExit('unexpected NX mouse deactivation signature')
t = t.replace(old, 'static void IN_DeactivateMouse( qboolean isFullscreen, qboolean showSystemCursor )')
old = '\t// Always show the cursor when the mouse is disabled,\n\t// but not when fullscreen\n\tif( !isFullscreen )\n\t\tSDL_ShowCursor( SDL_TRUE );'
new = ('#ifdef USE_FLEXIBLE_DISPLAY\n\tSDL_ShowCursor(isFullscreen ? SDL_FALSE : showSystemCursor);\n'
       '#else\n\t(void)showSystemCursor;\n\tif (!isFullscreen) SDL_ShowCursor(SDL_TRUE);\n#endif')
if t.count(old) != 1:
    raise SystemExit('unexpected NX cursor visibility')
t = t.replace(old, new)
old = ('\t\tif( SDL_GetWindowFlags( SDL_window ) & SDL_WINDOW_MOUSE_FOCUS )\n'
       '\t\t\tSDL_WarpMouseInWindow( SDL_window, cls.glconfig.vidWidth / 2, cls.glconfig.vidHeight / 2 );')
new = ("""\t\tif( SDL_GetWindowFlags( SDL_window ) & SDL_WINDOW_MOUSE_FOCUS ) {
#ifdef USE_FLEXIBLE_DISPLAY
\t\t\tif (cl_flexibleDisplay->integer)
\t\t\t\tSDL_WarpMouseInWindow(SDL_window, mouseLastX, mouseLastY);
\t\t\telse
#endif
\t\t\t\tSDL_WarpMouseInWindow(SDL_window, cls.glconfig.vidWidth / 2, cls.glconfig.vidHeight / 2);
\t\t}""")
if t.count(old) != 1:
    raise SystemExit('unexpected NX mouse warp')
t = t.replace(old, new)
old = 'IN_DeactivateMouse( cls.glconfig.isFullscreen );'
if t.count(old) != 3:
    raise SystemExit('unexpected NX frame deactivation calls')
t = t.replace(old, 'IN_DeactivateMouse( cls.glconfig.isFullscreen, qtrue );')
old = 'IN_DeactivateMouse( Cvar_VariableIntegerValue( "r_fullscreen" ) != 0 );'
if t.count(old) != 2:
    raise SystemExit('unexpected NX lifecycle deactivation calls')
t = t.replace(old, 'IN_DeactivateMouse( Cvar_VariableIntegerValue( "r_fullscreen" ) != 0, qtrue );')
old = '\telse\n\t\tIN_ActivateMouse( cls.glconfig.isFullscreen );'
new = ('#ifdef USE_FLEXIBLE_DISPLAY\n\telse if (cl_flexibleDisplay->integer && (Key_GetCatcher() & KEYCATCH_UI))\n'
       '\t\tIN_DeactivateMouse(cls.glconfig.isFullscreen, in_showUICursor);\n#endif\n' + old)
if t.count(old) != 1:
    raise SystemExit('unexpected NX frame mouse mode')
t = t.replace(old, new)
marker = 'static int joy_keys[16] = {'
if t.count(marker) != 1:
    raise SystemExit('unexpected NX mouse function insertion point')
t = t.replace(marker, '#ifdef USE_FLEXIBLE_DISPLAY\n' + mouse_functions + '\n#endif\n\n' + marker)
old = '\t\t\t\t\tCom_QueueEvent( in_eventTime, SE_MOUSE, e.motion.xrel, e.motion.yrel, 0, NULL );\n\t\t\t\t}\n\t\t\t\tbreak;'
new = old.replace('\n\t\t\t\tbreak;', '\n#ifdef USE_FLEXIBLE_DISPLAY\n\t\t\t\telse if ( cl_flexibleDisplay->integer ) {\n\t\t\t\t\tint xrel, yrel;\n\t\t\t\t\tIN_UpdateMouseMenuPosition(e.motion.x, e.motion.y, &xrel, &yrel);\n\t\t\t\t\tif ((xrel || yrel) && (Key_GetCatcher() & KEYCATCH_UI))\n\t\t\t\t\t\tCom_QueueEvent(in_eventTime, SE_MOUSE, xrel, yrel, 0, NULL);\n\t\t\t\t}\n#endif\n\t\t\t\tbreak;')
if t.count(old) != 1:
    raise SystemExit('unexpected NX mouse motion path')
t = t.replace(old, new)
t += '\n/* SP client entry point; implementation from pinned SP input. */\n' + match.group(0) + '\n'
nx.write_text(t)
