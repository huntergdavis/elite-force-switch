/* Experimental entry into VoyagerSP's real engine initialization. */
#include <switch.h>
#include <stdio.h>
#include <string.h>
#include "game_data_preflight.h"
#include "sys/sys_local.h"

#define DATA_ROOT "sdmc:/switch/elite-force-switch"
#define TRACE_PATH DATA_ROOT "/engine-bootstrap.log"

/* Defined in the upstream sys_main.c, retained for its path and system APIs. */
void Sys_SetBinaryPath(const char *path);

/* Diagnostic build only: fixed event strings, bounded per process, no key data. */
#ifdef SWITCH_UI_ROUTE_TRACE
void Switch_UIRouteTrace(const char *event)
{
    static unsigned count;
    if (count++ >= 64) return;
    FILE *out = fopen(DATA_ROOT "/ui-route.log", "a");
    if (out) { fputs(event, out); fputc('\n', out); fclose(out); }
}
#endif

int main(void)
{
#ifdef SWITCH_UI_ROUTE_TRACE
    Switch_UIRouteTrace("run: begin");
#endif
    FILE *trace = fopen(TRACE_PATH, "w");
    char command_line[] = "+set logfile 2";
    if (trace) { fputs("Switch engine bootstrap: checking game data\n", trace); fflush(trace); }

    int pak_status[GAME_DATA_REQUIRED_PAKS];
    GameData_Check(DATA_ROOT "/baseEF", pak_status);
    if (pak_status[0] || pak_status[1] || pak_status[2]) {
        consoleInit(NULL);
        padConfigureInput(1, HidNpadStyleSet_NpadStandard);
        PadState pad;
        padInitializeDefault(&pad);
        printf("Elite Force game data unavailable\n\n%s/baseEF\n\n", DATA_ROOT);
        for (int i = 0; i < GAME_DATA_REQUIRED_PAKS; ++i)
            printf("pak%d.pk3: %s\n", i, pak_status[i] ? strerror(pak_status[i]) : "readable");
        printf("\nCopy your own retail and patch files.\nPresence check only; content not verified.\nA: continue anyway   Plus: exit\n");
        if (trace) { fputs("Switch engine bootstrap: data preflight warning\n", trace); fflush(trace); }
        int proceed = 0;
        while (appletMainLoop()) {
            padUpdate(&pad);
            u64 buttons = padGetButtonsDown(&pad);
            if (buttons & HidNpadButton_Plus) break;
            if (buttons & HidNpadButton_A) { proceed = 1; break; }
            consoleUpdate(NULL);
        }
        consoleExit(NULL);
        if (!proceed) { if (trace) fclose(trace); return 1; }
    }
    if (trace) { fputs("Switch engine bootstrap: starting platform init\n", trace); fflush(trace); }
    Sys_PlatformInit();
    Sys_Milliseconds();
    Sys_SetBinaryPath(DATA_ROOT);
    Sys_SetDefaultInstallPath(DATA_ROOT);
    Sys_SetDefaultHomePath(DATA_ROOT);
    CON_Init();
    if (trace) { fputs("Switch engine bootstrap: entering Com_Init\n", trace); fflush(trace); }
    Com_Init(command_line);
    if (trace) { fputs("Switch engine bootstrap: Com_Init returned\n", trace); fflush(trace); }
    NET_Init();
    while (appletMainLoop()) {
        Com_Frame();
    }
    if (trace) fclose(trace);
    Sys_Quit();
    return 0;
}
