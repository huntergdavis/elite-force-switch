#!/usr/bin/env python3
"""Experimental symbol renaming; this does not establish semantic isolation."""
from pathlib import Path
import subprocess
import sys

game, ui, output = map(Path, sys.argv[1:])
binpath = '/opt/devkitpro/devkitA64/bin/aarch64-none-elf-'
def defined(path):
    result = subprocess.check_output([binpath + 'nm', '-g', '--defined-only', str(path)], text=True)
    return {parts[-1] for line in result.splitlines()
            if len(parts := line.split()) >= 3 and parts[-2] in 'TDBRSVWCG'}
names = sorted(defined(game) & defined(ui))
if not names:
    raise SystemExit('No selected shared game/UI definitions found')
renames = output.with_suffix('.renames')
renames.write_text(''.join(f'{name} efui_isolated_{name}\n' for name in names))
subprocess.run([binpath + 'objcopy', '--redefine-syms=' + str(renames), str(ui), str(output)], check=True)
print(f'Renamed {len(names)} selected overlapping game/UI symbols; semantic isolation unverified')
