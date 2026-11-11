#ifndef ELITE_SWITCH_STATIC_LOADER_H
#define ELITE_SWITCH_STATIC_LOADER_H

/* Compile-time bridge adapter, not a general dlopen implementation.
   By default each module may be loaded once; unloading cannot reset its globals. */
#include <string.h>

#define RTLD_NOW 0
#define RTLD_GLOBAL 0

extern "C" void static_game_api(void) __asm__("_Z10GetGameAPIP13game_import_t");
extern "C" void static_game_dll_entry(void) __asm__("_Z8dllEntryPFiizE");
extern "C" void static_game_vm_main(void) __asm__("_Z6vmMainiiiiiiiii");
extern "C" void static_ui_api(void) __asm__("_Z8GetUIAPIv");

struct SwitchStaticModule { bool used; bool live; };
static SwitchStaticModule switch_game_module = {false, false};
static SwitchStaticModule switch_ui_module = {false, false};
static const char *switch_loader_error = "static module operation failed";
#ifdef SWITCH_UI_SNAPSHOT_EXPERIMENT
/* A test/experimental caller must capture or restore owned state and fail
   closed when callbacks/resources are active; failure must not mutate UI state.
   Not enabled by build.sh. */
extern bool UIStateExperiment_BeginLoad(bool first_load);
static bool switch_ui_reset_in_progress = false;
static bool switch_ui_reset_poisoned = false;
#endif

static void *dlopen(const char *name, int flags) {
    (void)flags;
    SwitchStaticModule *module = NULL;
    if (name && strcmp(name, "libefgame.so") == 0) module = &switch_game_module;
    if (name && strcmp(name, "libefui.so") == 0) module = &switch_ui_module;
    if (!module) { switch_loader_error = "unknown static module"; return NULL; }
#ifdef SWITCH_UI_SNAPSHOT_EXPERIMENT
    if (module == &switch_ui_module) {
        if (module->live) { switch_loader_error = "static module is already active"; return NULL; }
        if (switch_ui_reset_in_progress) {
            switch_ui_reset_poisoned = true;
            switch_loader_error = "recursive static UI state reset"; return NULL;
        }
        if (switch_ui_reset_poisoned) {
            switch_loader_error = "static UI state reset poisoned"; return NULL;
        }
        switch_ui_reset_in_progress = true;
        bool ready = UIStateExperiment_BeginLoad(!module->used);
        switch_ui_reset_in_progress = false;
        if (!ready || switch_ui_reset_poisoned) {
            switch_loader_error = "static UI state reset unavailable"; return NULL;
        }
    } else
#endif
    if (module->used) { switch_loader_error = "static module reload is unsupported"; return NULL; }
    module->used = true;
    module->live = true;
    return module;
}

static void *dlsym(void *handle, const char *name) {
    if (handle == &switch_game_module && switch_game_module.live && name) {
        if (strcmp(name, "_Z10GetGameAPIP13game_import_t") == 0) return (void *)&static_game_api;
        if (strcmp(name, "_Z8dllEntryPFiizE") == 0) return (void *)&static_game_dll_entry;
        if (strcmp(name, "_Z6vmMainiiiiiiiii") == 0) return (void *)&static_game_vm_main;
    }
    if (handle == &switch_ui_module && switch_ui_module.live && name &&
        (strcmp(name, "GetUIAPI") == 0 || strcmp(name, "_Z8GetUIAPIv") == 0))
        return (void *)&static_ui_api;
    switch_loader_error = "unknown static symbol or inactive module";
    return NULL;
}

static int dlclose(void *handle) {
    SwitchStaticModule *module = NULL;
    if (handle == &switch_game_module) module = &switch_game_module;
    if (handle == &switch_ui_module) module = &switch_ui_module;
    if (!module || !module->live) { switch_loader_error = "static module is not active"; return -1; }
    module->live = false;
    return 0;
}

static const char *dlerror(void) { return switch_loader_error; }
#endif
