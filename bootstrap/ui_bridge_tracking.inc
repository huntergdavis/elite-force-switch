/* Experimental tracking only. No loader reset is enabled by this file.
 * Deliberately no C++ destructor: a nonlocal exit skips the leave and blocks reset. */
#include "ui_lifecycle_guard.h"
static UILifecycleGuard switch_ui_tracking = {};
#define UI_TRACK_CALL(expression) do { \
    bool uiTrackEntered = UITrack_Enter(&switch_ui_tracking); \
    expression; \
    if (uiTrackEntered) UITrack_Leave(&switch_ui_tracking); \
} while (0)
static int UII_TrackedOpen(const char *name, fileHandle_t *handle, fsMode_t mode) {
    if (handle) *handle = 0;
    int result = FS_FOpenFileByMode(name, handle, mode);
    if (handle && *handle) UITrack_FileOpen(&switch_ui_tracking, *handle);
    return result;
}
static void UII_TrackedClose(fileHandle_t handle) {
    FS_FCloseFile(handle);
    UITrack_FileClose(&switch_ui_tracking, handle);
}
static int UII_TrackedReadFile(const char *name, void **buffer) {
    if (buffer) *buffer = 0;
    int result = (int)FS_ReadFile(name, buffer);
    if (buffer && *buffer) UITrack_BufferOpen(&switch_ui_tracking, *buffer);
    return result;
}
static void UII_TrackedFreeFile(void *buffer) {
    FS_FreeFile(buffer);
    UITrack_BufferClose(&switch_ui_tracking, buffer);
}
