#!/usr/bin/env python3
"""Apply a narrow Switch-only IPv6 multicast exclusion to pinned SP net_ip.c."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
if '/* The current Switch toolchain lacks the IPv6 multicast interfaces used here. */' in text:
    raise SystemExit('Switch multicast patch already applied')

def replace_once(old, new):
    global text
    if text.count(old) != 1:
        raise SystemExit(f'unexpected network source around {old[:80]!r}')
    text = text.replace(old, new, 1)

replace_once('static struct ipv6_mreq curgroup;',
             '#ifndef __SWITCH__\nstatic struct ipv6_mreq curgroup;\n#endif')
old = '''\telse if(a->type == NA_MULTICAST6)
\t{
\t\t((struct sockaddr_in6 *)s)->sin6_family = AF_INET6;
\t\t((struct sockaddr_in6 *)s)->sin6_addr = curgroup.ipv6mr_multiaddr;
\t\t((struct sockaddr_in6 *)s)->sin6_port = a->port;
\t}'''
replace_once(old, '#ifndef __SWITCH__\n' + old + '\n#endif')
old = '''void Sys_SendPacket( int length, const void *data, netadr_t to ) {
\tint\t\t\t\tret = SOCKET_ERROR;
\tstruct sockaddr_storage\taddr;
'''
new = old + '''#ifdef __SWITCH__
\t/* Do not convert or send an unsupported multicast destination. */
\tif (to.type == NA_MULTICAST6) return;
#endif
'''
replace_once(old, new)
start = 'void NET_SetMulticast6(void)\n{'
end = '\n/*\n====================\nNET_OpenSocks'
if text.count(start) != 1 or text.count(end) != 1:
    raise SystemExit('unexpected multicast function boundaries')
pos = text.index(start)
finish = text.index(end, pos)
original = text[pos:finish]
replacement = '''#ifdef __SWITCH__
/* The current Switch toolchain lacks the IPv6 multicast interfaces used here. */
void NET_SetMulticast6(void) {
    Com_Printf("IPv6 multicast is not supported in this Switch build.\\n");
}
void NET_JoinMulticast6(void) { }
void NET_LeaveMulticast6(void) { }
#else
''' + original + '\n#endif\n'
text = text[:pos] + replacement + text[finish:]
path.write_text(text)
