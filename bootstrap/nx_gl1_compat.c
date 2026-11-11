/* NX GL1 has no Vulkan device-loss source. Do not claim GL loss detection. */
#include "qcommon/q_shared.h"
qboolean vk_device_lost(void) { return qfalse; }
void vk_clear_device_lost(void) { }
int vk_device_lost_report(char *out, int size) { (void)out; (void)size; return 0; }
