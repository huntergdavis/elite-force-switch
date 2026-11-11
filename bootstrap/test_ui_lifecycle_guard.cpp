#include <cassert>
#include "ui_lifecycle_guard.h"
#include "ui_state_snapshot.h"
int main() {
    UILifecycleGuard guard = {};
    UIStateSnapshot snapshot = {};
    int data=17, bss=0, buffer=0;
    assert(UIState_Capture(&snapshot, &data, (char*)&data+sizeof(data), &bss, (char*)&bss+sizeof(bss)));
    data=4; bss=9;
    assert(UITrack_Enter(&guard)); assert(UITrack_Enter(&guard));
    assert(!UIState_Restore(&snapshot, &guard, sizeof(guard), UITrack_CanReset(&guard), true));
    UITrack_Leave(&guard); UITrack_Leave(&guard);
    UITrack_FileOpen(&guard, 7); UITrack_BufferOpen(&guard, &buffer);
    assert(!UITrack_CanReset(&guard));
    UITrack_FileClose(&guard, 7); assert(!UITrack_CanReset(&guard));
    UITrack_BufferClose(&guard, &buffer); assert(UITrack_CanReset(&guard));
    assert(UIState_Restore(&snapshot, &guard, sizeof(guard), UITrack_CanReset(&guard), true));
    assert(data==17 && bss==0);
    UITrack_FileClose(&guard, 7); assert(!UITrack_CanReset(&guard));
    UIState_Release(&snapshot);
    UILifecycleGuard duplicate={}; UITrack_FileOpen(&duplicate, 1); UITrack_FileOpen(&duplicate, 1);
    assert(!UITrack_CanReset(&duplicate));
    UILifecycleGuard full={}; for (int i=1;i<=65;++i) UITrack_FileOpen(&full,i);
    assert(full.poisoned && !UITrack_CanReset(&full));
    UILifecycleGuard bad={}; UITrack_Leave(&bad); assert(!UITrack_CanReset(&bad));
}
