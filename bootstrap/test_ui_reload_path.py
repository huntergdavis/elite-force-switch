#!/usr/bin/env python3
"""Exercise pinned CL_InitUI/CL_ShutdownUI with the actual static-loader adapter.

UI/VM and engine services are stubs; no actual UI resources or renderer run.
"""
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
source = root.parent / 'references/VoyagerSP-Android'
text = subprocess.check_output([
    'git', '-C', str(source), 'show',
    'c73750361cfc22c1afb3a2c160fa9c5df57214db:EFAndroid-SP/app/jni/efcode/client/cl_ui.c',
], text=True)
start = text.index('void CL_ShutdownUI( void ) {')
end = text.index('\n#ifndef STANDALONE', start)
functions = text[start:end]
harness = r'''
#include <cassert>
#include <cstdarg>
#include "switch_static_loader.h"
extern "C" void static_game_api(void) {}
extern "C" void static_game_dll_entry(void) {}
extern "C" void static_game_vm_main(void) {}
extern "C" void static_ui_api(void) {}
typedef int vmInterpret_t;
struct Cvar { int integer; };
static Cvar enabled = {1};
static struct { int uiStarted; } cls;
static struct { int state; } clc;
static int cl_connectedToPureServer, keycatcher, vm_creates, ui_inits;
static void *uivm, *handle;
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
#define UI_API_VERSION 6
#define CA_AUTHORIZING 2
#define CA_ACTIVE 4
static int Key_GetCatcher() { return keycatcher; }
static void Key_SetCatcher(int value) { keycatcher=value; }
static int SPUI_IsActive() { return handle != nullptr; }
static void SPUI_Shutdown() { assert(dlclose(handle)==0); handle=nullptr; }
static Cvar *Cvar_Get(const char*, const char*, int) { return &enabled; }
static void Cvar_SetValue(const char*, int) {}
static int SPUI_Load() {
 handle=dlopen("libefui.so",RTLD_NOW|RTLD_GLOBAL);
 if (!handle) return 0;
 assert(dlsym(handle,"GetUIAPI")); ++ui_inits; return 1;
}
static float Cvar_VariableValue(const char*) { return VMI_COMPILED; }
static int CL_UISystemCalls(int*) { return 0; }
static void *VM_Create(const char*, int (*)(int*), int) { ++vm_creates; return &vm_creates; }
static int VM_Call(void*, int command, ...) { return command == UI_GETAPIVERSION ? UI_API_VERSION : 0; }
static void VM_Free(void*) {}
static void Com_Error(int, const char*, ...) { assert(false); }
''' + functions + r'''
int main() {
 cls.uiStarted=1; CL_InitUI(); assert(ui_inits==1 && vm_creates==0 && SPUI_IsActive());
 CL_ShutdownUI(); assert(!SPUI_IsActive() && !cls.uiStarted);
 cls.uiStarted=1; CL_InitUI();
 assert(ui_inits==1 && vm_creates==1 && uivm != nullptr);
 assert(strstr(dlerror(),"reload") != nullptr);
 return 0;
}
'''
scratch = root / 'build'
scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ui-reload-path.', dir=scratch) as tmp:
    cpp = Path(tmp) / 'fixture.cpp'
    exe = Path(tmp) / 'fixture'
    cpp.write_text(harness)
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-I', str(root),
                    str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('actual client UI init/shutdown path falls back to VM after static reload refusal; services stubbed')
