#!/usr/bin/env python3
"""Check the resident bridge through real pinned client UI dispatch.

UI, engine services and media are stubs. This does not test a Switch, real UI
resource lifetime, renderer restarts or saving.
"""
from pathlib import Path
import os
import subprocess
import tempfile

root = Path(__file__).resolve().parent
upstream = Path(os.environ.get(
    "ELITE_SP_REFERENCE", root.parent / "references/VoyagerSP-Android"
))
rev = "c73750361cfc22c1afb3a2c160fa9c5df57214db"


def pinned(path):
    return subprocess.check_output(
        ["git", "-C", str(upstream), "show", f"{rev}:{path}"], text=True
    )


client = pinned("EFAndroid-SP/app/jni/efcode/client/cl_ui.c")
client = client[client.index("void CL_ShutdownUI( void ) {"):client.index("\n#ifndef STANDALONE", client.index("void CL_ShutdownUI( void ) {"))]
bridge = pinned("EFAndroid-SP/app/jni/sp/sp_ui_bridge.cpp")
atoms = pinned("efgame/src/ui/ui_atoms.cpp")
scratch = root / "build"
scratch.mkdir(exist_ok=True)

with tempfile.TemporaryDirectory(prefix="resident-ui-lifetime.", dir=scratch) as tmp:
    tmp = Path(tmp)
    bridge_path, atoms_path = tmp / "bridge.cpp", tmp / "atoms.cpp"
    bridge_path.write_text(bridge)
    atoms_path.write_text(atoms)
    subprocess.run(["python3", str(root / "patch_switch_ui_lifetime.py"),
                    str(bridge_path), str(atoms_path)], check=True)
    patched_bridge = bridge_path.read_text()
    start = patched_bridge.index('extern "C" int SPUI_Load(void){')
    end = patched_bridge.index('extern "C" int  SPUI_IsActive(void)', start)
    functions = patched_bridge[start:end]
    patched_atoms = atoms_path.read_text()
    shutdown = patched_atoms[patched_atoms.index("static void UI_Shutdown( void ) {"):]
    shutdown = shutdown[:shutdown.index("\n}")]
    assert "uis.menusp = 0;" in shutdown and "uis.activemenu = NULL;" in shutdown
    assert "UI_ForceMenuOff" not in shutdown and "ui.Cvar_Set" not in shutdown
    assert "ui.Key_ClearStates" not in shutdown
    assert 'extern "C" void Switch_UIResume(uiimport_t *imports)' in patched_atoms
    harness = r'''
#include <cassert>
#include <cstring>
#include <cstdarg>
struct uiimport_t {};
struct uiexport_t { void (*UI_Init)(int,uiimport_t*); void (*UI_Shutdown)(); };
static int inits, resumes, shutdowns, opens, closes;
static struct { int menusp; void *activemenu; } uis;
''' + shutdown + r'''
}
static void Init(int,uiimport_t*) { ++inits; }
static void Shutdown() { ++shutdowns; UI_Shutdown(); }
static uiexport_t api={Init,Shutdown};
static uiexport_t* GetApi() { return &api; }
static void* dlopen(const char*,int) { ++opens; return opens==1 ? &api : nullptr; }
static void* dlsym(void*,const char*) { return reinterpret_cast<void*>(&GetApi); }
static int dlclose(void*) { ++closes; return 0; }
static const char* dlerror() { return "fake"; }
#define RTLD_NOW 0
#define RTLD_GLOBAL 0
#define UI_API_VERSION 6
static void ulog(const char*,...) {}
typedef uiexport_t* (*GetUIAPI_t)(void);
static void* g_uilib=0;
static uiexport_t* g_ux=0;
static int g_uiActive=0;
static uiimport_t g_uii;
static void SPUI_FillImport() {}
extern "C" void Switch_UIResume(uiimport_t*) { ++resumes; }
''' + functions + r'''
typedef int vmInterpret_t;
struct Cvar { int integer; };
static Cvar enabled={1};
static struct { int uiStarted; } cls;
static struct { int state; } clc;
static int cl_connectedToPureServer, keycatcher, vm_creates;
static void* uivm;
#define qfalse 0
#define KEYCATCH_UI 1
#define CVAR_ARCHIVE 1
#define VMI_COMPILED 1
#define VMI_BYTECODE 2
#define ERR_FATAL 1
#define ERR_DROP 2
#define UI_GETAPIVERSION 10
#define UI_INIT 11
#define UI_SHUTDOWN 12
#define CA_AUTHORIZING 2
#define CA_ACTIVE 4
static int Key_GetCatcher() { return keycatcher; }
static void Key_SetCatcher(int value) { keycatcher=value; }
static int SPUI_IsActive() { return g_uiActive; }
static Cvar* Cvar_Get(const char*,const char*,int) { return &enabled; }
static void Cvar_SetValue(const char*,int) {}
static float Cvar_VariableValue(const char*) { return VMI_COMPILED; }
static int CL_UISystemCalls(int*) { return 0; }
static void* VM_Create(const char*,int (*)(int*),int) { ++vm_creates; return &vm_creates; }
static int VM_Call(void*,int cmd,...) { return cmd==UI_GETAPIVERSION ? UI_API_VERSION : 0; }
static void VM_Free(void*) {}
static void Com_Error(int,const char*,...) { assert(false); }
''' + client + r'''
int main() {
 cls.uiStarted=1; CL_InitUI();
 assert(SPUI_IsActive() && inits==1 && resumes==0 && opens==1 && vm_creates==0);
 for(int i=0;i<3;++i) {
   uis.menusp=1; uis.activemenu=&api;
   CL_ShutdownUI(); assert(!SPUI_IsActive() && !cls.uiStarted);
   assert(uis.menusp==0 && uis.activemenu==nullptr);
   cls.uiStarted=1; CL_InitUI();
   assert(SPUI_IsActive() && inits==1 && resumes==i+1 && opens==1 && vm_creates==0);
 }
 assert(shutdowns==3 && closes==0);
 return 0;
}
'''
    cpp, exe = tmp / "fixture.cpp", tmp / "fixture"
    cpp.write_text(harness)
    subprocess.run(["g++", "-std=c++17", "-D__SWITCH__", "-Wall", "-Wextra",
                    "-Werror", "-Wno-unused-function", str(cpp), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)

print("Resident bridge and pinned client retain SP UI over three resumes (UI/renderer stubbed).")
