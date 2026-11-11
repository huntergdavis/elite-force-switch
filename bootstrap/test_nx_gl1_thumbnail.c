#include <assert.h>
#include <stddef.h>
#include <string.h>
typedef unsigned char byte;
typedef int qboolean;
typedef int GLint;
#define qtrue 1
#define qfalse 0
#define GL_NO_ERROR 0
#define GL_PACK_ALIGNMENT 1
#define GL_PACK_ROW_LENGTH 4
#define GL_PACK_SKIP_ROWS 5
#define GL_PACK_SKIP_PIXELS 6
#define GL_PIXEL_PACK_BUFFER_BINDING 7
#define GL_RGB 2
#define GL_UNSIGNED_BYTE 3
#define Com_Memcpy memcpy
#define Com_Memset memset
static struct { int vidWidth, vidHeight; } glConfig;
static byte pixels[16];
static const byte rgb[] = { 1,2,3, 4,5,6, 0,0, 7,8,9, 10,11,12, 0,0 };
static int frees, allocs, pending_error, read_failure, query_failure, alignment=4, row_length, skip_rows, skip_pixels, pack_buffer, allocation_failure;
static int qglGetError(void) { int e=pending_error; pending_error=0; return e; }
static void qglGetIntegerv(int name, int *v) { *v = name==GL_PACK_ALIGNMENT ? alignment : name==GL_PACK_ROW_LENGTH ? row_length : name==GL_PACK_SKIP_ROWS ? skip_rows : name==GL_PACK_SKIP_PIXELS ? skip_pixels : name==GL_PIXEL_PACK_BUFFER_BINDING ? pack_buffer : 0; if(query_failure) pending_error=7; }
static void qglReadPixels(int x,int y,int w,int h,int fmt,int type,void *dst) {
    assert(!x && !y && w==2 && h==2 && fmt==GL_RGB && type==GL_UNSIGNED_BYTE);
    if (read_failure) { pending_error=9; return; }
    memcpy(dst,rgb,sizeof(rgb));
}
static void *allocate(int n) { assert(n==16); ++allocs; if (allocation_failure) return NULL; memset(pixels,0xaa,sizeof(pixels)); return pixels; }
static void release(void *p) { assert(p == pixels); ++frees; }
static struct { void *(*Hunk_AllocateTempMemory)(int); void (*Hunk_FreeTempMemory)(void *); } ri = { allocate, release };
#include "nx_gl1_thumbnail.inc"
int main(void) {
    static byte result[256 * 256 * 4];
    assert(!NX_GetSaveThumb(result)); glConfig.vidWidth=2; glConfig.vidHeight=2;
    NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(frees==1 && NX_GetSaveThumb(result));
    assert(result[0]==1 && result[1]==2 && result[2]==3 && result[3]==255);
    assert(result[128*4]==4 && result[128*256*4]==7 && result[(255*256+255)*4]==10);
    read_failure=1; NX_RequestSaveThumb(); NX_CaptureSaveThumb();
    assert(frees==2 && !NX_GetSaveThumb(result)); read_failure=0;
    pending_error=3; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==2 && !NX_GetSaveThumb(result));
    query_failure=1; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==2 && !NX_GetSaveThumb(result)); query_failure=0;
    alignment=3; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==2 && !NX_GetSaveThumb(result)); alignment=4;
    row_length=1; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==2 && !NX_GetSaveThumb(result)); row_length=0;
    pack_buffer=1; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==2 && !NX_GetSaveThumb(result)); pack_buffer=0;
    skip_rows=1; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==2 && !NX_GetSaveThumb(result)); skip_rows=0;
    skip_pixels=1; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==2 && !NX_GetSaveThumb(result)); skip_pixels=0;
    allocation_failure=1; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==3 && frees==2 && !NX_GetSaveThumb(result)); allocation_failure=0;
    glConfig.vidWidth=0; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==3 && !NX_GetSaveThumb(result));
    glConfig.vidWidth=-1; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==3 && !NX_GetSaveThumb(result));
    glConfig.vidWidth=2; glConfig.vidHeight=0; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==3 && !NX_GetSaveThumb(result));
    glConfig.vidHeight=-1; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==3 && !NX_GetSaveThumb(result));
    glConfig.vidHeight=2;
    glConfig.vidWidth=16385; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==3 && !NX_GetSaveThumb(result));
    glConfig.vidWidth=16384; glConfig.vidHeight=16384; NX_RequestSaveThumb(); NX_CaptureSaveThumb(); assert(allocs==3 && !NX_GetSaveThumb(result));
    NX_ResetSaveThumb(); assert(!NX_GetSaveThumb(result)); return 0;
}
