/* The renderer import exposes a read-only string; the engine returns char *. */
#include "qcommon/q_shared.h"
#include "qcommon/qcommon.h"

const char *Switch_RendererCvarString(const char *name)
{
    return Cvar_VariableString(name);
}
