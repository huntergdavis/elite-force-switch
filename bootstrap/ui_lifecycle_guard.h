#ifndef ELITE_UI_LIFECYCLE_GUARD_H
#define ELITE_UI_LIFECYCLE_GUARD_H

/* Experimental bookkeeping only: callers must route every UI entry, handle,
 * and owned buffer through it. Unknown ownership poisons reset permanently. */
#include <limits.h>
#include <stddef.h>

struct UILifecycleGuard {
    unsigned int active;
    int files[64];
    const void *buffers[64];
    bool poisoned;
};

static inline bool UITrack_Enter(UILifecycleGuard *g) {
    if (g->active == UINT_MAX) { g->poisoned = true; return false; }
    ++g->active;
    return true;
}
static inline void UITrack_Leave(UILifecycleGuard *g) {
    if (!g->active) { g->poisoned = true; return; }
    --g->active;
}
static inline void UITrack_FileOpen(UILifecycleGuard *g, int file) {
    if (!file) return;
    if (file < 0) { g->poisoned = true; return; }
    size_t empty = 64;
    for (size_t i=0; i<64; ++i) {
        if (g->files[i] == file) { g->poisoned = true; return; }
        if (!g->files[i] && empty == 64) empty=i;
    }
    if (empty == 64) { g->poisoned = true; return; }
    g->files[empty]=file;
}
static inline void UITrack_FileClose(UILifecycleGuard *g, int file) {
    if (!file) { g->poisoned = true; return; }
    for (size_t i=0; i<64; ++i) if (g->files[i] == file) { g->files[i]=0; return; }
    g->poisoned = true;
}
static inline void UITrack_BufferOpen(UILifecycleGuard *g, const void *buffer) {
    if (!buffer) return;
    size_t empty = 64;
    for (size_t i=0; i<64; ++i) {
        if (g->buffers[i] == buffer) { g->poisoned = true; return; }
        if (!g->buffers[i] && empty == 64) empty=i;
    }
    if (empty == 64) { g->poisoned = true; return; }
    g->buffers[empty]=buffer;
}
static inline void UITrack_BufferClose(UILifecycleGuard *g, const void *buffer) {
    if (!buffer) { g->poisoned = true; return; }
    for (size_t i=0; i<64; ++i) if (g->buffers[i] == buffer) { g->buffers[i]=NULL; return; }
    g->poisoned = true;
}
static inline bool UITrack_CanReset(const UILifecycleGuard *g) {
    if (g->active || g->poisoned) return false;
    for (size_t i=0; i<64; ++i) if (g->files[i] || g->buffers[i]) return false;
    return true;
}
#endif
