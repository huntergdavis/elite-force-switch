#include <switch.h>
#include <stdio.h>

int main() {
    consoleInit(NULL);
    printf("Campaign game archive link probe.\n");
    printf("GetGameAPI is linked but is not called.\n");
    printf("No engine or game is initialized.\nPress Plus to exit.\n");
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
