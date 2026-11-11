#include <cassert>
#include <csetjmp>
typedef int fileHandle_t;
typedef int fsMode_t;
static int next_file=7, opened, closed, reads, frees, data;
static int FS_FOpenFileByMode(const char*, fileHandle_t *f, fsMode_t) { ++opened; if (f) *f=next_file; return next_file ? 5 : -1; }
static void FS_FCloseFile(fileHandle_t f) { assert(f==next_file); ++closed; }
static long FS_ReadFile(const char*, void **p) { ++reads; if (p) *p=&data; return 4; }
static void FS_FreeFile(void *p) { assert(p==&data); ++frees; }
#include "ui_bridge_tracking.inc"
static std::jmp_buf jump_target;
static void jump_out() { std::longjmp(jump_target, 1); }
int main() {
    assert(UITrack_CanReset(&switch_ui_tracking));
    UI_TRACK_CALL(assert(switch_ui_tracking.active == 1);
        UI_TRACK_CALL(assert(switch_ui_tracking.active == 2));
        assert(switch_ui_tracking.active == 1));
    assert(UITrack_CanReset(&switch_ui_tracking));
    if (setjmp(jump_target) == 0) { UI_TRACK_CALL(jump_out()); assert(false); }
    assert(switch_ui_tracking.active == 1 && !UITrack_CanReset(&switch_ui_tracking));
    switch_ui_tracking = {}; // Isolate the remaining host fixture cases.
    fileHandle_t file=0;
    assert(UII_TrackedOpen("x",&file,0)==5 && file==7 && opened==1);
    void *buffer=nullptr; assert(UII_TrackedReadFile("x",&buffer)==4 && buffer==&data && reads==1);
    assert(!UITrack_CanReset(&switch_ui_tracking));
    UII_TrackedClose(file); assert(closed==1 && !UITrack_CanReset(&switch_ui_tracking));
    UII_TrackedFreeFile(buffer); assert(frees==1 && UITrack_CanReset(&switch_ui_tracking));
    next_file=0; assert(UII_TrackedOpen("missing",&file,0)<0 && !file && UITrack_CanReset(&switch_ui_tracking));
    UITrack_FileClose(&switch_ui_tracking,7); assert(!UITrack_CanReset(&switch_ui_tracking));
}
