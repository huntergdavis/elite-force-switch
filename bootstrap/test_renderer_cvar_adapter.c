#include <assert.h>
#include <string.h>

static char value[] = "value";
static const char *received;
char *Cvar_VariableString(const char *name) { received = name; return value; }
const char *Switch_RendererCvarString(const char *name);

int main(void)
{
    const char *result = Switch_RendererCvarString("test_cvar");
    assert(result == value);
    assert(strcmp(received, "test_cvar") == 0);
    return 0;
}
