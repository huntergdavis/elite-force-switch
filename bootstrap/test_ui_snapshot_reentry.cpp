#include <cassert>
#define SWITCH_UI_SNAPSHOT_EXPERIMENT 1
#include "switch_static_loader.h"
extern "C" void static_game_api(void) {}
extern "C" void static_game_dll_entry(void) {}
extern "C" void static_game_vm_main(void) {}
extern "C" void static_ui_api(void) {}
static int calls;
bool UIStateExperiment_BeginLoad(bool first) {
    assert(first); ++calls;
    assert(!dlopen("libefui.so",RTLD_NOW));
    return true;  // the outer operation must still fail closed
}
int main() {
    assert(!dlopen("libefui.so",RTLD_NOW));
    assert(calls==1 && strstr(dlerror(),"unavailable"));
    assert(!dlopen("libefui.so",RTLD_NOW));
    assert(calls==1 && strstr(dlerror(),"poisoned"));
    assert(!dlsym(nullptr,"GetUIAPI") && dlclose(nullptr)!=0);
}
