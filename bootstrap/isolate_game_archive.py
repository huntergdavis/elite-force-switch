#!/usr/bin/env python3
"""Rename five observed game-owned globals; not a complete isolation mechanism."""
from pathlib import Path
import subprocess
import sys

source, output = map(Path, sys.argv[1:])
binpath = '/opt/devkitpro/devkitA64/bin/aarch64-none-elf-'
names = ('com_buildScript', 'bytedirs', 'vec3_origin', 'g_color_table', 'axisDefault')
def symbols(path, defined_only=False):
    args = [binpath + 'nm', '-g']
    if defined_only:
        args.append('--defined-only')
    lines = subprocess.check_output(args + [str(path)], text=True).splitlines()
    return {parts[-1] for line in lines if len(parts := line.split()) >= 2 and len(parts[-2]) == 1}
before = symbols(source, True)
if not set(names) <= before:
    raise SystemExit('Expected game-owned definitions are absent')
if any('efgame_isolated_' + name in before for name in names):
    raise SystemExit('Game isolation target name already exists')
renames = output.with_suffix('.renames')
renames.write_text(''.join(f'{name} efgame_isolated_{name}\n' for name in names))
subprocess.run([binpath + 'objcopy', '--redefine-syms=' + str(renames), str(source), str(output)], check=True)
after_all = symbols(output)
after_defined = symbols(output, True)
if set(names) & after_all or not {'efgame_isolated_' + name for name in names} <= after_defined:
    raise SystemExit('Game symbol remapping check failed')
print('Renamed five observed game globals; complete isolation remains unverified')
