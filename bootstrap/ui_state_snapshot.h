#ifndef ELITE_UI_STATE_SNAPSHOT_H
#define ELITE_UI_STATE_SNAPSHOT_H

/* Experimental byte-state primitive. It does not own or clean external resources.
 * Caller must establish archive isolation, initial-state timing and quiescence. */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#ifndef UI_SNAPSHOT_ALLOC
#define UI_SNAPSHOT_ALLOC malloc
#endif
#ifndef UI_SNAPSHOT_FREE
#define UI_SNAPSHOT_FREE free
#endif

struct UIStateSnapshot {
    unsigned char *data, *bss, *image;
    size_t data_size, bss_size;
};

static inline void UIState_Release(UIStateSnapshot *state) {
    if (!state) return;
    UI_SNAPSHOT_FREE(state->image);
    memset(state, 0, sizeof(*state));
}

static inline bool UIState_Capture(UIStateSnapshot *state,
                                   void *data_begin, void *data_end,
                                   void *bss_begin, void *bss_end) {
    const uintptr_t db = (uintptr_t)data_begin, de = (uintptr_t)data_end;
    const uintptr_t bb = (uintptr_t)bss_begin, be = (uintptr_t)bss_end;
    const uintptr_t sb = (uintptr_t)state;
    if (!state || sb > UINTPTR_MAX - sizeof(*state)) return false;
    const uintptr_t se = sb + sizeof(*state);
    const size_t max_bytes = 16u * 1024u * 1024u;
    if (state->image || !db || !bb || de <= db || be <= bb ||
        !(de <= bb || be <= db) || !(se <= db || de <= sb) ||
        !(se <= bb || be <= sb) || de-db > max_bytes || be-bb > max_bytes ||
        de-db > max_bytes-(be-bb)) return false;
    const size_t data_size = (size_t)(de-db), bss_size = (size_t)(be-bb);
    unsigned char *image = (unsigned char *)UI_SNAPSHOT_ALLOC(data_size+bss_size);
    if (!image) return false;
    const uintptr_t ib = (uintptr_t)image;
    const size_t image_size = data_size + bss_size;
    if (ib > UINTPTR_MAX - image_size ||
        !(ib + image_size <= db || de <= ib) ||
        !(ib + image_size <= bb || be <= ib) ||
        !(ib + image_size <= sb || se <= ib)) { UI_SNAPSHOT_FREE(image); return false; }
    memcpy(image, data_begin, data_size);
    memcpy(image+data_size, bss_begin, bss_size);
    state->data = (unsigned char *)data_begin; state->bss = (unsigned char *)bss_begin;
    state->data_size = data_size; state->bss_size = bss_size; state->image = image;
    return true;
}

/* The exact guard controlling quiescence must be passed here; checking an
 * unrelated object does not establish that the real guard is disjoint. */
static inline bool UIState_Restore(UIStateSnapshot *state, const void *guard, size_t guard_size,
                                   bool quiescent, bool resources_released) {
    if (!state || !state->image || !guard || !guard_size || !quiescent || !resources_released) return false;
    const uintptr_t gb = (uintptr_t)guard, db = (uintptr_t)state->data, bb = (uintptr_t)state->bss;
    const uintptr_t ib = (uintptr_t)state->image, sb = (uintptr_t)state;
    if (gb > UINTPTR_MAX - guard_size || db > UINTPTR_MAX - state->data_size ||
        bb > UINTPTR_MAX - state->bss_size || state->data_size > SIZE_MAX - state->bss_size ||
        ib > UINTPTR_MAX - (state->data_size + state->bss_size) || sb > UINTPTR_MAX - sizeof(*state)) return false;
    const uintptr_t ge = gb + guard_size, de = db + state->data_size, be = bb + state->bss_size;
    const uintptr_t ie = ib + state->data_size + state->bss_size, se = sb + sizeof(*state);
    if (!(ge <= db || de <= gb) || !(ge <= bb || be <= gb) ||
        !(ge <= ib || ie <= gb) || !(ge <= sb || se <= gb)) return false;
    memcpy(state->data, state->image, state->data_size);
    memcpy(state->bss, state->image+state->data_size, state->bss_size);
    return true;
}
#endif
