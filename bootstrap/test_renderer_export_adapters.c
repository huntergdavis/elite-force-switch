#include <assert.h>
#include <setjmp.h>
#include <stdarg.h>

typedef unsigned char byte;
typedef int qboolean;
typedef struct { int value; } refEntity_t;
enum { qfalse = 0, qtrue = 1, ERR_DROP = 1, REF_KEEP_CONTEXT = 0, REF_KEEP_WINDOW = 1 };
static jmp_buf error_target;
static int shutdown_code = -1, entity_flag = -1, errors;
static void error_stub(int level, const char *format, ...) {
    assert(level == ERR_DROP && format); ++errors; longjmp(error_target, 1);
}
static struct { void (*Error)(int, const char *, ...); } ri = { error_stub };
static void RE_Shutdown(int value) { shutdown_code = value; }
static void RE_AddRefEntityToScene(const refEntity_t *entity, qboolean flag) { assert(entity); entity_flag = flag; }
#include "renderer_export_adapters.inc"
int main(void) {
    const byte input[4] = { 7, 0, 0, 0 };
    refEntity_t entity = { 0 };
    Switch_RE_Shutdown(qfalse); assert(shutdown_code == REF_KEEP_CONTEXT);
    Switch_RE_Shutdown(qtrue); assert(shutdown_code == REF_KEEP_WINDOW);
    Switch_RE_AddRefEntityToScene(&entity); assert(entity_flag == qfalse);
    if (!setjmp(error_target)) { Switch_RE_StretchRaw(0,0,1,1,1,1,input,0,qtrue); assert(0); }
    if (!setjmp(error_target)) { Switch_RE_UploadCinematic(1,1,1,1,input,0,qtrue); assert(0); }
    assert(errors == 2 && input[0] == 7);
    return 0;
}
