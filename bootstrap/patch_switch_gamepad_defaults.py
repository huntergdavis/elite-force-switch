#!/usr/bin/env python3
from pathlib import Path
import sys
p = Path(sys.argv[1]); s = p.read_text()
marker = 'void Com_ExecuteCfg(void)\n{'
call = '\t\tCbuf_ExecuteText(EXEC_NOW, "exec autoexec.cfg\\n");\n\t\tCbuf_Execute();'
if s.count(marker) != 1 or s.count(call) != 1 or 'Switch_InstallGamepadDefaults' in s:
    raise SystemExit('unexpected config startup')
s = s.replace(marker, '#include "switch_gamepad_defaults.inc"\n\n' + marker)
s = s.replace(call, call + '\n#ifdef __SWITCH__\n\t\tSwitch_InstallGamepadDefaults();\n#endif')
p.write_text(s)
