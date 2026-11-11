#include <assert.h>
#include <string.h>
#include "switch_static_loader.h"

extern "C" void static_game_api(void) {}
extern "C" void static_game_dll_entry(void) {}
extern "C" void static_game_vm_main(void) {}
extern "C" void static_ui_api(void) {}

int main() {
    assert(!dlopen("unknown.so", RTLD_NOW));
    void *game = dlopen("libefgame.so", RTLD_NOW);
    void *ui = dlopen("libefui.so", RTLD_NOW | RTLD_GLOBAL);
    assert(game && ui && game != ui);
    assert(dlsym(game, "_Z10GetGameAPIP13game_import_t") == (void *)&static_game_api);
    assert(dlsym(game, "_Z8dllEntryPFiizE") == (void *)&static_game_dll_entry);
    assert(dlsym(game, "_Z6vmMainiiiiiiiii") == (void *)&static_game_vm_main);
    assert(dlsym(ui, "GetUIAPI") == (void *)&static_ui_api);
    assert(dlsym(ui, "_Z8GetUIAPIv") == (void *)&static_ui_api);
    assert(!dlsym(game, "GetUIAPI"));
    assert(dlclose(game) == 0 && dlclose(ui) == 0);
    assert(!dlsym(game, "_Z10GetGameAPIP13game_import_t"));
    assert(dlclose(game) != 0);
    assert(!dlopen("libefgame.so", RTLD_NOW));
    assert(strstr(dlerror(), "reload") != NULL);
    assert(!dlopen("libefui.so", RTLD_NOW));
    return 0;
}
