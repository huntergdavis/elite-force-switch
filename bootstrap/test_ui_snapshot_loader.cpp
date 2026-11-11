#include <cassert>
#define SWITCH_UI_SNAPSHOT_EXPERIMENT 1
#include "switch_static_loader.h"
#include "ui_state_snapshot.h"
#include "ui_lifecycle_guard.h"
extern "C" void static_game_api(void) {}
extern "C" void static_game_dll_entry(void) {}
extern "C" void static_game_vm_main(void) {}
extern "C" void static_ui_api(void) {}
static int ui_data=17, ui_bss=0, engine_state=4, buffer;
static UIStateSnapshot state={};
static UILifecycleGuard guard={};
bool UIStateExperiment_BeginLoad(bool first_load) {
    if (!UITrack_CanReset(&guard)) return false;
    if (first_load) return UIState_Capture(&state,&ui_data,(char*)&ui_data+sizeof(ui_data),
                                          &ui_bss,(char*)&ui_bss+sizeof(ui_bss));
    return UIState_Restore(&state,&guard,sizeof(guard),true,true);
}
int main() {
    void *ui=dlopen("libefui.so",RTLD_NOW); assert(ui);
    assert(!dlopen("libefui.so",RTLD_NOW));
    ui_data=2; ui_bss=9; engine_state=8;
    UITrack_Enter(&guard); assert(dlclose(ui)==0);
    assert(!dlopen("libefui.so",RTLD_NOW) && ui_data==2 && ui_bss==9);
    UITrack_Leave(&guard); UITrack_BufferOpen(&guard,&buffer);
    assert(!dlopen("libefui.so",RTLD_NOW) && ui_data==2 && ui_bss==9);
    UITrack_BufferClose(&guard,&buffer);
    ui=dlopen("libefui.so",RTLD_NOW); assert(ui && ui_data==17 && ui_bss==0 && engine_state==8);
    assert(dlsym(ui,"GetUIAPI") == (void *)&static_ui_api);
    assert(dlclose(ui)==0);
    UITrack_FileOpen(&guard,5); UITrack_FileClose(&guard,5); UITrack_FileClose(&guard,5);
    assert(!dlopen("libefui.so",RTLD_NOW));
    assert(strstr(dlerror(), "reset") != nullptr);
    UIState_Release(&state);
}
