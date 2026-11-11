#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "qcommon/q_shared.h"
#include "qcommon/qcommon.h"

int main(int argc, char **argv)
{
    FILE *f;
    assert(argc == 2);
    assert(!Sys_MicrosoftStorePath()[0]);
    assert(Sys_Dialog(DT_YES_NO, "test", "fixture") == DR_NO);
    assert(Sys_Dialog(DT_OK_CANCEL, "test", "fixture") == DR_CANCEL);
    assert(Sys_Dialog(DT_ERROR, "test", "fixture") == DR_OK);
    f = fopen(argv[1], "wx");
    assert(f && fclose(f) == 0);
    Sys_Remove(argv[1]);
    f = fopen(argv[1], "r");
    assert(!f);
    return 0;
}
