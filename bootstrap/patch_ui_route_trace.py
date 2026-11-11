#!/usr/bin/env python3
"""Instrument pinned SP UI selection for a Switch diagnostic build."""
from pathlib import Path
import sys
client, bridge = map(Path, sys.argv[1:])
c, b = client.read_text(), bridge.read_text()
old = 'if ( Cvar_Get("sp_ui", "1", CVAR_ARCHIVE)->integer && SPUI_Load() ) {'
new = '''int switch_sp_ui_enabled = Cvar_Get("sp_ui", "1", CVAR_ARCHIVE)->integer;
#ifdef __SWITCH__
\textern void Switch_UIRouteTrace(const char *event);
\tSwitch_UIRouteTrace(switch_sp_ui_enabled ? "selection: sp_ui enabled" : "selection: sp_ui disabled");
#endif
\tif ( switch_sp_ui_enabled && SPUI_Load() ) {
#ifdef __SWITCH__
\t\tSwitch_UIRouteTrace("selection: SP active");
#endif'''
if c.count(old) != 1: raise SystemExit('unexpected UI selection')
c = c.replace(old, new)
old = '\t// load the dll or bytecode\n\tinterpret = Cvar_VariableValue("vm_ui");'
new = '''#ifdef __SWITCH__
\tSwitch_UIRouteTrace("selection: VM fallback");
#endif
''' + old
if c.count(old) != 1: raise SystemExit('unexpected VM fallback')
c = c.replace(old, new)
marker = 'extern "C" int SPUI_Load(void){'
if b.count(marker) != 1: raise SystemExit('unexpected bridge entry')
b = b.replace(marker, '''#ifdef __SWITCH__
extern "C" void Switch_UIRouteTrace(const char *event);
#define UI_ROUTE(event) Switch_UIRouteTrace(event)
#else
#define UI_ROUTE(event) ((void)0)
#endif

''' + marker + '\n    UI_ROUTE("bridge: load requested");')
for old, new in [
 ('if(g_uiActive) return 1;', 'if(g_uiActive){ UI_ROUTE("bridge: already active"); return 1; }'),
 ('if(!g_uilib){ ulog(', 'if(!g_uilib){ UI_ROUTE("bridge: dlopen failed"); ulog('),
 ('if(!getapi){ ulog(', 'if(!getapi){ UI_ROUTE("bridge: symbol missing"); ulog('),
 ('if(!g_ux || !g_ux->UI_Init){ ulog(', 'if(!g_ux || !g_ux->UI_Init){ UI_ROUTE("bridge: invalid API"); ulog('),
 ('g_ux->UI_Init(UI_API_VERSION, &g_uii);', 'UI_ROUTE("bridge: entering UI_Init");\n    g_ux->UI_Init(UI_API_VERSION, &g_uii);\n    UI_ROUTE("bridge: UI_Init returned");'),
 ('extern "C" void SPUI_Shutdown(void){', 'extern "C" void SPUI_Shutdown(void){\n    UI_ROUTE("bridge: shutdown requested");'),
 ('if(g_uilib){ dlclose(g_uilib); g_uilib=0; g_ux=0; }', 'if(g_uilib){ dlclose(g_uilib); UI_ROUTE("bridge: closed"); g_uilib=0; g_ux=0; }'),
]:
 if b.count(old) != 1: raise SystemExit('unexpected bridge site: ' + old)
 b = b.replace(old, new)
client.write_text(c); bridge.write_text(b)
