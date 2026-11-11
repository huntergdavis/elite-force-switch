#include "game_data_preflight.h"
#include <errno.h>
#include <stdio.h>
#include <sys/stat.h>

void GameData_Check(const char *base_dir, int status[GAME_DATA_REQUIRED_PAKS])
{
    for (int i = 0; i < GAME_DATA_REQUIRED_PAKS; ++i) {
        char path[1024];
        struct stat st;
        int n = snprintf(path, sizeof(path), "%s/pak%d.pk3", base_dir, i);
        if (n < 0 || (size_t)n >= sizeof(path)) { status[i] = ENAMETOOLONG; continue; }
        if (stat(path, &st) != 0) { status[i] = errno ? errno : EIO; continue; }
        if (!S_ISREG(st.st_mode)) { status[i] = EINVAL; continue; }
        FILE *file = fopen(path, "rb");
        if (!file) { status[i] = errno ? errno : EIO; continue; }
        if (fclose(file) != 0) { status[i] = errno ? errno : EIO; continue; }
        status[i] = 0;
    }
}
