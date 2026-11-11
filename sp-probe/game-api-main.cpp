#include <switch.h>
#include <stdio.h>
#include <string.h>
#include "q_shared.h"
#include "g_public.h"

extern game_export_t *GetGameAPI(game_import_t *);
static char empty_data[] = "";
static int reads;
static int releases;
static int read_file(const char *name, void **buffer) {
    ++reads;
    if (strcmp(name, "ext_data/weapons.dat") != 0) { *buffer = NULL; return -1; }
    *buffer = empty_data;
    return 0;
}
static void free_file(void *buffer) {
    if (buffer == empty_data) ++releases;
}

int main() {
    consoleInit(NULL);
    game_import_t imports = {};
    imports.FS_ReadFile = read_file;
    imports.FS_FreeFile = free_file;
    game_export_t *api = GetGameAPI(&imports);
    int ok = api && api->apiversion == GAME_API_VERSION && api->Init && api->Shutdown &&
             api->RunFrame && reads == 1 && releases == 1;
    printf("Synthetic GetGameAPI probe: %s\n", ok ? "PASS" : "FAIL");
    printf("Weapon data: empty synthetic buffer; reads %d, releases %d\n", reads, releases);
    printf("No engine, real data or gameplay initialized.\nPress Plus to exit.\n");
    PadState pad;
    padConfigureInput(1, HidNpadStyleSet_NpadStandard);
    padInitializeDefault(&pad);
    while (appletMainLoop()) {
        padUpdate(&pad);
        if (padGetButtonsDown(&pad) & HidNpadButton_Plus) break;
        consoleUpdate(NULL);
    }
    consoleExit(NULL);
    return 0;
}
