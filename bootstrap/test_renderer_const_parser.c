#include <assert.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include "qcommon/q_shared.h"
void QDECL Com_Error(int level, const char *fmt, ...) { (void)level; (void)fmt; abort(); }
void QDECL Com_Printf(const char *fmt, ...) { (void)fmt; }
#include "renderer_const_parser.h"
int main(void) {
    const char *input = "alpha \"two words\"\n{ inner { nested } } tail\nnext";
    char mutable_input[] = "alpha \"two words\"\n{ inner { nested } } tail\nnext";
    const char *a = input;
    char *b = mutable_input;
    char first[64], second[64];
    int line_a;
    COM_BeginParseSession("fixture");
    strcpy(first, Switch_ParseExt(&a, qtrue));
    strcpy(second, Switch_ParseExt(&a, qtrue));
    assert(!strcmp(first, "alpha") && !strcmp(second, "two words"));
    assert(Switch_SkipBracedSection(&a, 0));
    assert(!strcmp(Switch_ParseExt(&a, qtrue), "tail"));
    Switch_SkipRestOfLine(&a);
    line_a = COM_GetCurrentParseLine();
    COM_BeginParseSession("fixture");
    assert(!strcmp(COM_ParseExt(&b, qtrue), first));
    assert(!strcmp(COM_ParseExt(&b, qtrue), second));
    assert(SkipBracedSection(&b, 0));
    assert(!strcmp(COM_ParseExt(&b, qtrue), "tail"));
    SkipRestOfLine(&b);
    assert((a - input) == (b - mutable_input));
    assert(COM_GetCurrentParseLine() == line_a);
    assert(!strcmp(Switch_ParseExt(&a, qtrue), "next"));
    a = NULL;
    assert(!strcmp(Switch_ParseExt(&a, qtrue), "") && a == NULL);
    return 0;
}
