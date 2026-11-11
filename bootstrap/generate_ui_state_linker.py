#!/usr/bin/env python3
"""Build a scratch Switch linker script that brackets UI archive data and bss.

This does not install a loader reset or prove ownership or runtime safety.
"""
from pathlib import Path
import sys

ld_source, specs_source, out_dir = map(Path, sys.argv[1:])
s = ld_source.read_text()
data = '\t.data :\n\t{'
bss = '\t.bss :\n\t{'
relro = '\t.data.rel.ro :'
if s.count(data) != 1 or s.count(bss) != 1 or s.count(relro) != 1:
    raise SystemExit('unexpected Switch linker script')
if not s.index(relro) < s.index(data) < s.index(bss) or '__bss_start__ = ADDR(.bss)' not in s:
    raise SystemExit('unexpected Switch data/bss layout')
s = s.replace(data, data + '''
        efui_data_start = .;
        *efui-isolated.a:*(.data .data.* .gnu.linkonce.d.*)
        efui_data_end = .;''')
s = s.replace(bss, bss + '''
        efui_bss_start = .;
        *efui-isolated.a:*(.bss .bss.* .gnu.linkonce.b.* COMMON)
        efui_bss_end = .;''')
old = '-T %:getenv(DEVKITPRO /libnx/switch.ld)'
specs = specs_source.read_text()
if specs.count(old) != 1:
    raise SystemExit('unexpected Switch specs')
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / 'switch-ui.ld').write_text(s)
(out_dir / 'switch-ui.specs').write_text(specs.replace(old, '-T /work/switch-ui.ld'))
