#include <switch.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <sys/stat.h>

#define DATA_DIR "sdmc:/switch/elite-force-switch/baseEF"
#define LOG_PATH "sdmc:/switch/elite-force-switch/first-light.log"

int main(void) {
    consoleInit(NULL);
    padConfigureInput(1, HidNpadStyleSet_NpadStandard);
    PadState pad;
    padInitializeDefault(&pad);
    FILE *log = fopen(LOG_PATH, "w");
    printf("Elite Force first-light diagnostic\n\n");
    printf("Checking %s\n\n", DATA_DIR);
    if (log) fprintf(log, "Elite Force first-light diagnostic\nData directory: %s\n", DATA_DIR);
    else printf("Could not open log: %s\n\n", LOG_PATH);
    int found = 0;
    for (int i = 0; i < 4; ++i) {
        char path[256];
        struct stat st;
        snprintf(path, sizeof path, DATA_DIR "/pak%d.pk3", i);
        int result = stat(path, &st);
        int error = result == 0 ? 0 : errno;
        const char *status = result == 0 ? (S_ISREG(st.st_mode) ? "found" : "not a regular file") :
            (error == ENOENT || error == ENOTDIR ? "missing" : strerror(error));
        printf("pak%d.pk3: %s\n", i, status);
        if (log) fprintf(log, "pak%d.pk3: %s\n", i, status);
        found += result == 0 && S_ISREG(st.st_mode);
    }
    printf("\n%d/4 files found. Presence only; contents not checked.\n", found);
    printf("This diagnostic does not launch the game.\nPress Plus to exit.\n");
    if (log) {
        int failed = ferror(log);
        if (fclose(log) != 0) failed = 1;
        if (failed) printf("Failed to write complete log.\n");
    }
    while (appletMainLoop()) {
        padUpdate(&pad);
        if (padGetButtonsDown(&pad) & HidNpadButton_Plus) break;
        consoleUpdate(NULL);
    }
    consoleExit(NULL);
    return 0;
}
