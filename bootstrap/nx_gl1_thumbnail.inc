/* Experimental SP save-thumbnail support for single-threaded NX GL1. */
#define NX_THUMB_SIZE 256
#define NX_THUMB_MAX_DIM 16384
#define NX_THUMB_MAX_BYTES (64u * 1024u * 1024u)
static byte nx_save_thumb[NX_THUMB_SIZE * NX_THUMB_SIZE * 4];
static qboolean nx_thumb_pending, nx_thumb_valid;

static void NX_RequestSaveThumb(void) { nx_thumb_pending = qtrue; }
static qboolean NX_GetSaveThumb(byte *dst) {
    if (!dst || !nx_thumb_valid) return qfalse;
    Com_Memcpy(dst, nx_save_thumb, sizeof(nx_save_thumb));
    return qtrue;
}
void NX_ResetSaveThumb(void) { nx_thumb_pending = nx_thumb_valid = qfalse; }
void NX_CaptureSaveThumb(void) {
    byte *pixels;
    size_t stride, bytes;
    GLint alignment = 0, row_length = 0, skip_rows = 0, skip_pixels = 0;
#ifdef GL_PIXEL_PACK_BUFFER_BINDING
    GLint pack_buffer = 0;
#endif
    int x, y, width = glConfig.vidWidth, height = glConfig.vidHeight;
    if (!nx_thumb_pending) return;
    nx_thumb_pending = qfalse;
    nx_thumb_valid = qfalse;
    /* Bounded dimensions make multiplication and the allocator's int size safe. */
    if (width <= 0 || height <= 0 || width > NX_THUMB_MAX_DIM || height > NX_THUMB_MAX_DIM) return;
    /* A pre-existing GL error makes this capture inconclusive. Consume one and fail. */
    if (qglGetError() != GL_NO_ERROR) return;
    qglGetIntegerv(GL_PACK_ALIGNMENT, &alignment);
    qglGetIntegerv(GL_PACK_ROW_LENGTH, &row_length);
    qglGetIntegerv(GL_PACK_SKIP_ROWS, &skip_rows);
    qglGetIntegerv(GL_PACK_SKIP_PIXELS, &skip_pixels);
#ifdef GL_PIXEL_PACK_BUFFER_BINDING
    qglGetIntegerv(GL_PIXEL_PACK_BUFFER_BINDING, &pack_buffer);

#endif
    if (qglGetError() != GL_NO_ERROR || row_length != 0 || skip_rows != 0 || skip_pixels != 0 ||
        (alignment != 1 && alignment != 2 && alignment != 4 && alignment != 8)
#ifdef GL_PIXEL_PACK_BUFFER_BINDING
        || pack_buffer != 0
#endif
    ) return;
    stride = ((size_t)width * 3 + (size_t)alignment - 1) & ~((size_t)alignment - 1);
    bytes = stride * (size_t)height;
    if (bytes == 0 || bytes > NX_THUMB_MAX_BYTES) return;
    pixels = ri.Hunk_AllocateTempMemory((int)bytes);
    if (!pixels) return;
    Com_Memset(pixels, 0, bytes);
    qglReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, pixels);
    if (qglGetError() != GL_NO_ERROR) {
        ri.Hunk_FreeTempMemory(pixels);
        return;
    }
    for (y = 0; y < NX_THUMB_SIZE; ++y) {
        for (x = 0; x < NX_THUMB_SIZE; ++x) {
            const byte *src = pixels + ((size_t)y * height / NX_THUMB_SIZE) * stride
                                     + ((size_t)x * width / NX_THUMB_SIZE) * 3;
            byte *dst = nx_save_thumb + (y * NX_THUMB_SIZE + x) * 4;
            dst[0] = src[0]; dst[1] = src[1]; dst[2] = src[2]; dst[3] = 255;
        }
    }
    ri.Hunk_FreeTempMemory(pixels);
    nx_thumb_valid = qtrue;
}

/* Called between the game and menu draw on the single-threaded NX GL1 path.
 * Complete the queued game rendering and capture the back buffer without
 * swapping it. The menu can then be drawn into the same presented frame. */
int NX_CapturePendingBeforeMenu(void) {
    if (!nx_thumb_pending || !tr.registered || !r_skipBackEnd || r_skipBackEnd->integer)
        return 0;
    R_IssuePendingRenderCommands();
    if (tess.numIndexes) {
        RB_EndSurface();
        /* If the backend could not finish its surface, keep the existing
         * one-frame suppression and capture-at-swap behavior. */
        if (tess.numIndexes) return 0;
    }
    /* Force the next 2D draw to begin a fresh surface after our mid-frame
     * flush, even if it happens to use the previous HUD shader. */
    tess.shader = NULL;
    NX_CaptureSaveThumb();
    if (nx_thumb_valid) return 1;
    /* Capture clears the pending flag even on failure. Retry at swap, while
     * the caller retains its original one-frame menu suppression. */
    nx_thumb_pending = qtrue;
    return 0;
}
