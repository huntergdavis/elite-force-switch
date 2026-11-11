#!/usr/bin/env python3
"""Keep the Switch SP UI module resident while renderer resources restart.

Apply to the pinned, otherwise unmodified upstream bridge and UI files. The
separate media-handle adapter must be installed before this is used: cached
renderer handles are invalid across renderer teardown.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_switch_ui_lifetime.py <sp_ui_bridge.cpp> <ui_atoms.cpp>")

bridge_path, atoms_path = map(Path, sys.argv[1:])
bridge, atoms = bridge_path.read_text(), atoms_path.read_text()


def replace_once(text, old, new, label):
    if text.count(old) != 1:
        raise SystemExit(f"unexpected {label}")
    return text.replace(old, new, 1)


marker = '// ================= uiimport_t adapters ================='
bridge = replace_once(
    bridge, marker,
    '''#ifdef __SWITCH__
#include "switch_ui_media.h"
static int Switch_RegisterUiMedia(void *, ResidentMediaKind kind, const char *name) {
    switch (kind) {
    case ResidentMediaKind::Model: return SPR_RegisterModel(name);
    case ResidentMediaKind::Skin: return SPR_RegisterSkin(name);
    case ResidentMediaKind::Shader: return SPR_RegisterShader(name);
    case ResidentMediaKind::ShaderNoMip: return SPR_RegisterShaderNoMip(name);
    case ResidentMediaKind::Sound: return SPR_S_RegisterSound(name);
    }
    return 0;
}
static ResidentUiMedia<> switch_ui_media(nullptr, Switch_RegisterUiMedia);
#endif

''' + marker,
    "UI media insertion",
)
adapters = [
    ('static void      UII_R_AddRefEntity(const refEntity_t* re){ SPR_AddRefEntity(re, sizeof(*re)); }',
     'static void UII_R_AddRefEntity(const refEntity_t* re){ if (!re) return; refEntity_t translated = switch_ui_media.TranslateEntity(*re); SPR_AddRefEntity(&translated, sizeof(translated)); }'),
    ('static void      UII_R_AddPoly(qhandle_t hShader,int n,const polyVert_t* v){ SPR_AddPoly((int)hShader,n,v); }',
     'static void UII_R_AddPoly(qhandle_t s,int n,const polyVert_t* v){ SPR_AddPoly(switch_ui_media.Resolve(ResidentMediaUse::Shader,s),n,v); }'),
    ('static qhandle_t UII_R_RegisterModel(const char* n){ return (qhandle_t)SPR_RegisterModel(n); }',
     'static qhandle_t UII_R_RegisterModel(const char* n){ return switch_ui_media.Register(ResidentMediaKind::Model,n); }'),
    ('static qhandle_t UII_R_RegisterSkin(const char* n){ return (qhandle_t)SPR_RegisterSkin(n); }',
     'static qhandle_t UII_R_RegisterSkin(const char* n){ return switch_ui_media.Register(ResidentMediaKind::Skin,n); }'),
    ('static qhandle_t UII_R_RegisterShader(const char* n){ return (qhandle_t)SPR_RegisterShader(n); }',
     'static qhandle_t UII_R_RegisterShader(const char* n){ return switch_ui_media.Register(ResidentMediaKind::Shader,n); }'),
    ('static qhandle_t UII_R_RegisterShaderNoMip(const char* n){ return (qhandle_t)SPR_RegisterShaderNoMip(n); }',
     'static qhandle_t UII_R_RegisterShaderNoMip(const char* n){ return switch_ui_media.Register(ResidentMediaKind::ShaderNoMip,n); }'),
    ('static void      UII_R_DrawStretchPic(float x,float y,float w,float h,float s1,float t1,float s2,float t2,qhandle_t s){ SPR_DrawStretchPic(x,y,w,h,s1,t1,s2,t2,(int)s); }',
     'static void UII_R_DrawStretchPic(float x,float y,float w,float h,float s1,float t1,float s2,float t2,qhandle_t s){ SPR_DrawStretchPic(x,y,w,h,s1,t1,s2,t2,switch_ui_media.Resolve(ResidentMediaUse::Shader,s)); }'),
    ('static void      UII_R_ScissorPic(float x,float y,float w,float h,float s1,float t1,float s2,float t2,qhandle_t s){ SPR_ScissorPic(x,y,w,h,s1,t1,s2,t2,(int)s); }',
     'static void UII_R_ScissorPic(float x,float y,float w,float h,float s1,float t1,float s2,float t2,qhandle_t s){ SPR_ScissorPic(x,y,w,h,s1,t1,s2,t2,switch_ui_media.Resolve(ResidentMediaUse::Shader,s)); }'),
    ('static void      UII_R_LerpTag(orientation_t* tag,clipHandle_t mod,int sf,int ef,float frac,const char* name){ SPR_LerpTag(tag,(int)mod,sf,ef,frac,name); }',
     'static void UII_R_LerpTag(orientation_t* tag,clipHandle_t mod,int sf,int ef,float frac,const char* name){ SPR_LerpTag(tag,switch_ui_media.Resolve(ResidentMediaUse::Model,mod),sf,ef,frac,name); }'),
    ('static void        UII_S_StartLocalSound(sfxHandle_t sfx,int chan){ SPR_S_StartLocalSound((int)sfx,chan); }',
     'static void UII_S_StartLocalSound(sfxHandle_t sfx,int chan){ SPR_S_StartLocalSound(switch_ui_media.Resolve(ResidentMediaUse::Sound,sfx),chan); }'),
    ('static sfxHandle_t UII_S_RegisterSound(const char* name){ return (sfxHandle_t)SPR_S_RegisterSound(name); }',
     'static sfxHandle_t UII_S_RegisterSound(const char* name){ return switch_ui_media.Register(ResidentMediaKind::Sound,name); }'),
]
for old, new in adapters:
    bridge = replace_once(bridge, old, '#ifdef __SWITCH__\n' + new + '\n#else\n' + old + '\n#endif', old)

marker = 'extern "C" int SPUI_Load(void){'
bridge = replace_once(
    bridge, marker,
    '#ifdef __SWITCH__\nextern "C" void Switch_UIResume(uiimport_t *imports);\n#endif\n\n' + marker,
    "UI load entry",
)
marker = '    if(g_uiActive) return 1;\n'
if marker not in bridge:
    marker = '    if(g_uiActive){ UI_ROUTE("bridge: already active"); return 1; }\n'
bridge = replace_once(
    bridge, marker,
    marker + '''#ifdef __SWITCH__
    // The linked UI cannot be unloaded. Resume it after engine teardown with
    // current imports and media, retaining its original menu implementation.
    if(g_uilib && g_ux){
        SPUI_FillImport();
        Switch_UIResume(&g_uii);
        g_uiActive = 1;
        return 1;
    }
#endif
''',
    "UI load active guard",
)
marker = '    if(g_uilib){ dlclose(g_uilib); g_uilib=0; g_ux=0; }'
if marker not in bridge:
    marker = '    if(g_uilib){ dlclose(g_uilib); UI_ROUTE("bridge: closed"); g_uilib=0; g_ux=0; }'
bridge = replace_once(
    bridge, marker,
    '#ifndef __SWITCH__\n' + marker + '\n#endif',
    "UI unload",
)

marker = 'static void UI_Shutdown( void ) {\n}'
atoms = replace_once(
    atoms, marker,
    '''static void UI_Shutdown( void ) {
#ifdef __SWITCH__
    // A freshly loaded UI starts with an empty menu stack. Clear only the
    // retained UI's stack; CL_ShutdownUI clears the UI catcher. Do not reset
    // the shared pause cvar or clear keys owned by the rest of the engine.
    uis.menusp = 0;
    uis.activemenu = NULL;
#endif
}''',
    "UI shutdown",
)
marker = '\nuiexport_t *GetUIAPI( void ) {'
atoms = replace_once(
    atoms, marker,
    '''
#ifdef __SWITCH__
// Unlike a newly loaded dynamic library, our UI retains its globals. Do not
// reload the parsed text that existing menus may still reference.
extern "C" void Switch_UIResume(uiimport_t *imports) {
    ui = *imports;
    ui.GetGlconfig(&uis.glconfig);
    UI_RecalcAspect();
    Menu_Cache();
}
#endif
''' + marker,
    "UI resume insertion",
)

bridge_path.write_text(bridge)
atoms_path.write_text(atoms)
