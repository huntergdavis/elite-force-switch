#!/usr/bin/env python3
"""Retain raw backtrace addresses on Switch without requiring dladdr."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
marker = '/* Switch has no dladdr; log raw frame addresses. */'
if marker in text:
    raise SystemExit('Switch backtrace patch already applied')
old_include = '#include <dlfcn.h>'
if text.count(old_include) != 1:
    raise SystemExit('unexpected dladdr include')
text = text.replace(old_include, '#ifndef __SWITCH__\n' + old_include + '\n#endif', 1)
start = '        Dl_info info;\n'
end = '            SP_LogE("crash", "  #%02d  %p  ?", i, buf[i]);\n'
if text.count(start) != 1 or text.count(end) != 1:
    raise SystemExit('unexpected backtrace symbolization block')
begin = text.index(start)
finish = text.index(end, begin) + len(end)
original = text[begin:finish]
replacement = '''#ifdef __SWITCH__
        /* Switch has no dladdr; log raw frame addresses. */
        SP_LogE("crash", "  #%02d  %p  ?", i, buf[i]);
#else
''' + original + '#endif\n'
path.write_text(text[:begin] + replacement + text[finish:])
