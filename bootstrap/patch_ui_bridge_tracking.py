#!/usr/bin/env python3
"""Instrument pinned SP UI bridge under an explicit test-only flag.

No snapshot or reload hook is enabled by this patch.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
marker = '// ================= uiimport_t adapters ================='
if s.count(marker) != 1:
    raise SystemExit('unexpected UI bridge imports')
s = s.replace(marker, '''#ifdef SWITCH_UI_TRACK_EXPERIMENT
#include "ui_bridge_tracking.inc"
#else
#define UI_TRACK_CALL(expression) do { expression; } while (0)
#endif

''' + marker)
for old, new in [
    ('g_ux = getapi();', 'UI_TRACK_CALL(g_ux = getapi());'),
    ('g_ux->UI_Init(UI_API_VERSION, &g_uii);', 'UI_TRACK_CALL(g_ux->UI_Init(UI_API_VERSION, &g_uii));'),
    ('if(g_uiActive && g_ux && g_ux->UI_Shutdown) g_ux->UI_Shutdown();',
     'if(g_uiActive && g_ux && g_ux->UI_Shutdown) UI_TRACK_CALL(g_ux->UI_Shutdown());'),
    ('if(g_uiActive && g_ux->UI_Refresh) g_ux->UI_Refresh(t);',
     'if(g_uiActive && g_ux->UI_Refresh) UI_TRACK_CALL(g_ux->UI_Refresh(t));'),
    ('if(g_uiActive && down && g_ux->UI_KeyEvent) g_ux->UI_KeyEvent(key);',
     'if(g_uiActive && down && g_ux->UI_KeyEvent) UI_TRACK_CALL(g_ux->UI_KeyEvent(key));'),
    ('if(g_uiActive && g_ux->UI_MouseEvent) g_ux->UI_MouseEvent(dx,dy);',
     'if(g_uiActive && g_ux->UI_MouseEvent) UI_TRACK_CALL(g_ux->UI_MouseEvent(dx,dy));'),
    ('qboolean fs=qfalse; g_ux->UI_GetActiveMenu(NULL,&fs); return fs?1:0;',
     'qboolean fs=qfalse; UI_TRACK_CALL(g_ux->UI_GetActiveMenu(NULL,&fs)); return fs?1:0;'),
    ('g_ux->UI_SetActiveMenu(name, "");', 'UI_TRACK_CALL(g_ux->UI_SetActiveMenu(name, ""));'),
    ('return (g_uiActive && g_ux->UI_ConsoleCommand) ? g_ux->UI_ConsoleCommand() : 0;',
     'if(!g_uiActive || !g_ux->UI_ConsoleCommand) return 0; int result; UI_TRACK_CALL(result=g_ux->UI_ConsoleCommand()); return result;'),
    ('if(g_uiActive && g_ux->UI_DrawConnect) g_ux->UI_DrawConnect(sv,upd);',
     'if(g_uiActive && g_ux->UI_DrawConnect) UI_TRACK_CALL(g_ux->UI_DrawConnect(sv,upd));'),
]:
    if s.count(old) != 1:
        raise SystemExit(f'unexpected UI lifecycle call: {old}')
    s = s.replace(old, new)
old = '''    g_uii.FS_FOpenFile=FS_FOpenFileByMode; g_uii.FS_Read=FS_Read; g_uii.FS_Write=FS_Write; g_uii.FS_FCloseFile=FS_FCloseFile;
    g_uii.FS_GetFileList=FS_GetFileList; g_uii.FS_ReadFile=UII_FS_ReadFile; g_uii.FS_FreeFile=FS_FreeFile;'''
new = '''#ifdef SWITCH_UI_TRACK_EXPERIMENT
    g_uii.FS_FOpenFile=UII_TrackedOpen; g_uii.FS_Read=FS_Read; g_uii.FS_Write=FS_Write; g_uii.FS_FCloseFile=UII_TrackedClose;
    g_uii.FS_GetFileList=FS_GetFileList; g_uii.FS_ReadFile=UII_TrackedReadFile; g_uii.FS_FreeFile=UII_TrackedFreeFile;
#else
''' + old + '''
#endif'''
if s.count(old) != 1:
    raise SystemExit('unexpected UI filesystem imports')
s = s.replace(old, new)
path.write_text(s)
