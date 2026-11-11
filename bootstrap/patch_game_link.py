#!/usr/bin/env python3
"""Use a narrowly renamed game archive for the experimental engine link."""
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
old = 'target_link_libraries(voyagersp PRIVATE efgame switch_ui)'
new = '''add_custom_command(OUTPUT /work/efgame-isolated.a
  COMMAND python3 /work/isolate_game_archive.py $<TARGET_FILE:efgame> /work/efgame-isolated.a
  DEPENDS efgame /work/isolate_game_archive.py VERBATIM)
add_custom_target(switch_game_isolation DEPENDS /work/efgame-isolated.a)
add_library(switch_game STATIC IMPORTED GLOBAL)
set_target_properties(switch_game PROPERTIES IMPORTED_LOCATION /work/efgame-isolated.a)
add_dependencies(voyagersp switch_game_isolation)
target_link_libraries(voyagersp PRIVATE switch_game switch_ui)'''
if s.count(old) != 1:
    raise SystemExit('unexpected game archive linkage')
p.write_text(s.replace(old, new, 1))
