#!/usr/bin/env python3
"""Compare object-level symbol records before/after the five-name remap."""
from collections import Counter
import re
import subprocess
import sys

nm = '/opt/devkitpro/devkitA64/bin/aarch64-none-elf-nm'
source, renamed = sys.argv[1:]
names = ('com_buildScript', 'bytedirs', 'vec3_origin', 'g_color_table', 'axisDefault')
def records(path):
    output = subprocess.check_output([nm, '-A', '-g', path], text=True)
    result = {}
    for line in output.splitlines():
        match = re.search(r':([^:]+):\s*(?:[0-9a-fA-F]+\s+)?([A-Za-z])\s+(\S+)$', line)
        if match:
            member, kind, name = match.groups()
            result.setdefault(name, Counter())[(member, kind)] += 1
    return result
before, after = records(source), records(renamed)
for name in names:
    target = 'efgame_isolated_' + name
    if name not in before or name in after or before[name] != after.get(target):
        raise SystemExit(f'game archive record mismatch: {name}')
    print(f'{name}: {sum(before[name].values())} definition/reference records preserved under {target}')
