#!/usr/bin/env python3
"""Test archive-specific state grouping and snapshot restore on host GNU ld.

Synthetic fixture only; no actual UI archive, relocations on Switch, or GPU.
"""
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
scratch = root / 'build'
scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ui-state-linker.', dir=scratch) as tmp:
    tmp = Path(tmp)
    (tmp / 'ui.cpp').write_text('''
static int value = 17;
static int count;
int *ui_pointer = &value;
int ui_get() { return value + count; }
void ui_mutate() { value=4; count=9; }
''')
    (tmp / 'main.cpp').write_text('''
#include <cassert>
#include "ui_state_snapshot.h"
extern char ui_data_start[], ui_data_end[], ui_bss_start[], ui_bss_end[];
extern int ui_get(), *ui_pointer;
extern void ui_mutate();
static int engine_state = 19;
int main() {
 UIStateSnapshot s={};
 assert(UIState_Capture(&s,ui_data_start,ui_data_end,ui_bss_start,ui_bss_end));
 assert(ui_get()==17 && *ui_pointer==17);
 ui_mutate(); engine_state=21; assert(ui_get()==13);
 assert(UIState_Restore(&s,&engine_state,sizeof(engine_state),true,true));
 assert(ui_get()==17 && *ui_pointer==17 && engine_state==21);
 UIState_Release(&s);
}
''')
    verbose = subprocess.check_output(['ld', '-pie', '--verbose'], text=True)
    script = verbose.split('=' * 50)[1]
    import re
    for section, label in [('data', 'data'), ('bss', 'bss')]:
        pattern = r'(\n  \.' + section + r'\s*:\s*\n  \{)'
        selector = '.data .data.* .gnu.linkonce.d.*' if section == 'data' else '.bss .bss.* .gnu.linkonce.b.* COMMON'
        replacement = r'\1\n    ui_' + label + '_start = .;\n    *libui.a:*(' + selector + ')\n    ui_' + label + '_end = .;'
        script, count = re.subn(pattern, replacement, script, count=1)
        assert count == 1
    (tmp / 'sections.ld').write_text(script)
    subprocess.run(['g++','-std=c++17','-fdata-sections','-c',str(tmp/'ui.cpp'),'-o',str(tmp/'ui.o')],check=True)
    subprocess.run(['ar','rcs',str(tmp/'libui.a'),str(tmp/'ui.o')],check=True)
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-I',str(root),str(tmp/'main.cpp'),
                    str(tmp/'libui.a'),'-Wl,-T,'+str(tmp/'sections.ld'),'-o',str(tmp/'test')],check=True)
    subprocess.run([str(tmp/'test')],check=True)
print('synthetic archive state reset preserves pointer and excludes engine state')
