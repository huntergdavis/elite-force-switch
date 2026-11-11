/* Minimal Switch platform functions needed by the SP engine build. */
#include <stdio.h>
#include "qcommon/q_shared.h"
#include "qcommon/qcommon.h"

void Sys_Remove(const char *path)
{
    remove(path);
}

char *Sys_MicrosoftStorePath(void)
{
    static char empty[] = "";
    return empty;
}

dialogResult_t Sys_Dialog(dialogType_t type, const char *message, const char *title)
{
    fprintf(stderr, "%s: %s\n", title ? title : "Message", message ? message : "");
    if (type == DT_YES_NO) return DR_NO;
    if (type == DT_OK_CANCEL) return DR_CANCEL;
    return DR_OK;
}
