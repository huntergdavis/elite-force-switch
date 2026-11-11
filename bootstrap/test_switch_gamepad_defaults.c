#include <assert.h>
#include <stdio.h>
#include <string.h>
#define __SWITCH__ 1
#define CVAR_ARCHIVE 1
#define CVAR_LATCH 2
typedef struct { int integer; } cvar_t;
static cvar_t stamp;
static const char *names[32];
static char bindings[32][32];
static int keys, writes;
static cvar_t *Cvar_Get(const char *name, const char *value, int flags) {
    (void)value; (void)flags; (void)name; return &stamp;
}
static void Cvar_Set(const char *name, const char *value) {
    assert(!strcmp(name,"in_switchDefaults") && !strcmp(value,"1")); stamp.integer=1;
}
int Key_StringToKeynum(char *name) {
    for (int i=0;i<keys;i++) if (!strcmp(names[i],name)) return i;
    names[keys]=name; return keys++;
}
char *Key_GetBinding(int key) { return bindings[key]; }
void Key_SetBinding(int key, const char *binding) {
    snprintf(bindings[key],sizeof(bindings[key]),"%s",binding); ++writes;
}
#include "switch_gamepad_defaults.inc"
int main(void) {
    int key=Key_StringToKeynum("PAD0_A");
    strcpy(bindings[key],"+custom");
    Switch_InstallGamepadDefaults();
    assert(!strcmp(bindings[key],"+custom"));
    assert(!strcmp(bindings[Key_StringToKeynum("PAD0_LEFTSTICK_UP")],"+forward"));
    assert(stamp.integer==1 && writes==22);
    strcpy(bindings[Key_StringToKeynum("PAD0_LEFTSTICK_UP")], "");
    Switch_InstallGamepadDefaults();
    assert(!*bindings[Key_StringToKeynum("PAD0_LEFTSTICK_UP")] && writes==22);
}
