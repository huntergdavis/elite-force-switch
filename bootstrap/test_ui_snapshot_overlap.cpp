#include <cassert>
#include <cstdlib>
#include <cstring>
#include <cstdint>
static unsigned char data[128], bss[32];
static int freed;
static void *overlap_malloc(size_t) { return data+8; }
static void overlap_free(void *p) { assert(p==data+8); ++freed; }
#define UI_SNAPSHOT_ALLOC overlap_malloc
#define UI_SNAPSHOT_FREE overlap_free
#include "ui_state_snapshot.h"
#undef UI_SNAPSHOT_ALLOC
#undef UI_SNAPSHOT_FREE
int main() {
    UIStateSnapshot state = {};
    assert(!UIState_Capture(&state,data,data+sizeof(data),bss,bss+sizeof(bss)));
    assert(freed==1 && state.image==nullptr);
}
