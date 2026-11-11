#!/usr/bin/env python3
"""Inventory allocated writable/TLS/initializer sections in a UI archive.

Run inside the pinned devkitPro image; output is a section inventory, not proof
of state ownership, live linker inclusion, or resource cleanup.
"""
import collections
import re
import subprocess
import sys

archive = sys.argv[1]
tool = '/opt/devkitpro/devkitA64/bin/aarch64-none-elf-readelf'
result = subprocess.check_output([tool, '-SW', archive], text=True)
member = None
rows = []
for line in result.splitlines():
    if line.startswith('File: '):
        member = line.rsplit('(', 1)[-1].rstrip(')')
        continue
    match = re.match(r'\s*\[\s*\d+\]\s+(\S+)\s+(\S+)\s+[0-9a-f]+\s+[0-9a-f]+\s+([0-9a-f]+)\s+\S+\s+(\S+)', line)
    if not match:
        continue
    name, typ, size, flags = match.groups()
    if ('A' in flags and ('W' in flags or 'T' in flags)) or name.startswith(('.init_array', '.fini_array')):
        rows.append((member, name, typ, flags, int(size, 16)))
counts = collections.Counter(('relro' if name.startswith('.data.rel.ro') else
                              'data' if name.startswith('.data') else
                              'bss' if name.startswith('.bss') else 'other')
                             for _, name, _, _, _ in rows)
print('member\tsection\ttype\tflags\tbytes')
for member, name, typ, flags, size in rows:
    print(f'{member}\t{name}\t{typ}\t{flags}\t{size}')
print('# section records:', len(rows), 'classes:', dict(counts), file=sys.stderr)
