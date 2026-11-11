#include <cassert>
#include <cstring>
#include "ui_state_snapshot.h"
struct UIData { int initial; int *self; };
struct UIBss { int count; char buffer[16]; };
int main() {
    UIData data = {17, nullptr}; data.self = &data.initial;
    UIBss bss = {};
    int engine_state = 41;
    struct Embedded { UIStateSnapshot state; char bytes[8]; } embedded = {};
    assert(!UIState_Capture(&embedded.state, &embedded, (char*)&embedded+sizeof(embedded),
                            &bss, (char*)&bss+sizeof(bss)));
    UIStateSnapshot snapshot = {};
    assert(!UIState_Restore(&snapshot, &engine_state, sizeof(engine_state), true, true));
    assert(!UIState_Capture(&snapshot, &data, &data, &bss, (char*)&bss+sizeof(bss)));
    assert(!UIState_Capture(&snapshot, &data, (char*)&data+sizeof(data), &data, (char*)&data+sizeof(data)));
    assert(UIState_Capture(&snapshot, &data, (char*)&data+sizeof(data), &bss, (char*)&bss+sizeof(bss)));
    assert(!UIState_Capture(&snapshot, &data, (char*)&data+sizeof(data), &bss, (char*)&bss+sizeof(bss)));
    data.initial=3; data.self=nullptr; bss.count=10; strcpy(bss.buffer,"changed"); engine_state=42;
    assert(!UIState_Restore(&snapshot, &engine_state, sizeof(engine_state), false, true));
    assert(!UIState_Restore(&snapshot, &engine_state, sizeof(engine_state), true, false));
    assert(!UIState_Restore(&snapshot, &data, sizeof(data), true, true));
    assert(!UIState_Restore(&snapshot, &bss, sizeof(bss), true, true));
    assert(!UIState_Restore(&snapshot, snapshot.image, 1, true, true));
    assert(!UIState_Restore(&snapshot, &snapshot, sizeof(snapshot), true, true));
    assert(!UIState_Restore(&snapshot, nullptr, 1, true, true));
    assert(data.initial==3 && bss.count==10);
    assert(UIState_Restore(&snapshot, &engine_state, sizeof(engine_state), true, true));
    assert(data.initial==17 && data.self==&data.initial && *data.self==17 && bss.count==0 && !bss.buffer[0]);
    assert(engine_state==42);
    UIState_Release(&snapshot); assert(!UIState_Restore(&snapshot, &engine_state, sizeof(engine_state), true, true));
    UIState_Release(&snapshot);
}
