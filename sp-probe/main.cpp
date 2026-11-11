#include <switch.h>
#include <stdio.h>
extern signed char ClampChar(int);
int main() {
    consoleInit(NULL);
    volatile int value = 200;
    printf("SP q_math ClampChar(200): %d (expected 127)\n", (int)ClampChar(value));
    printf("Compile/link probe only; press Plus to exit.\n");
    PadState pad; padConfigureInput(1, HidNpadStyleSet_NpadStandard); padInitializeDefault(&pad);
    while (appletMainLoop()) { padUpdate(&pad); if (padGetButtonsDown(&pad) & HidNpadButton_Plus) break; consoleUpdate(NULL); }
    consoleExit(NULL); return 0;
}
