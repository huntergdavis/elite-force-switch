#!/bin/sh
set -eu
if [ "$#" -ne 2 ]; then
  echo "usage: $0 <libefgame.a> <libefui.a>" >&2
  exit 2
fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
game=$(realpath "$1")
ui=$(realpath "$2")
[ -f "$game" ] && [ -f "$ui" ]
mkdir -p "$root/sp-probe/build"
out=$(mktemp -d "$root/sp-probe/build/collisions.XXXXXXXX")
echo "Collision experiment directory: $out"
image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
docker run --rm -u "$(id -u):$(id -g)" -v "$game:/input/game.a:ro" -v "$ui:/input/ui.a:ro" \
  -v "$out:/out" -w /out "$image" sh -c '
  set -eu
  NM=/opt/devkitpro/devkitA64/bin/aarch64-none-elf-nm
  $NM -g --defined-only /input/game.a > game-defined.txt
  $NM -g --undefined-only /input/game.a > game-undefined.txt
  $NM -g --defined-only /input/ui.a > ui-defined.txt
  $NM -g --undefined-only /input/ui.a > ui-undefined.txt'
python3 - "$out" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
def definitions(name):
    return {parts[-1] for line in (p / name).read_text().splitlines()
            if len(parts := line.split()) >= 3 and parts[-2] in 'TDBRSVWCG'}
game = definitions('game-defined.txt')
ui = definitions('ui-defined.txt')
def undefined(name):
    return {parts[-1] for line in (p / name).read_text().splitlines()
            if len(parts := line.split()) == 2 and parts[0] in ('U', 'w', 'v')}
for consumer, names, other_only in (
    ('ui', undefined('ui-undefined.txt'), game - ui),
    ('game', undefined('game-undefined.txt'), ui - game),
):
    matches = sorted(names & other_only)
    report = f'{consumer}-undefined-other-only.txt'
    (p / report).write_text(''.join(name + '\n' for name in matches))
    if matches:
        raise SystemExit(f'{consumer} U/w/v undefined names defined only by other archive: {len(matches)}; inspect {report}')
    print(f'{consumer} U/w/v undefined names defined only by other archive (selected types): 0')
names = sorted(game & ui)
if not names:
    raise SystemExit('No colliding global definitions found')
(p / 'renames.txt').write_text(''.join(f'{name} efui_isolated_{name}\n' for name in names))
print(f'Collision names mapped: {len(names)}')
PY
docker run --rm -u "$(id -u):$(id -g)" -v "$game:/input/game.a:ro" -v "$ui:/input/ui.a:ro" \
  -v "$root/sp-probe:/probe:ro" -v "$out:/out" -w /out "$image" sh -c '
  set -eu
  BIN=/opt/devkitpro/devkitA64/bin/aarch64-none-elf
  FLAGS="-std=gnu++17 -O2 -ffunction-sections -fdata-sections -march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft -fPIE"
  $BIN-objcopy --redefine-syms=renames.txt /input/ui.a ui-renamed.a
  $BIN-g++ $FLAGS -I/opt/devkitpro/libnx/include -c /probe/game-link-main.cpp -o main.o
  $BIN-g++ $FLAGS -specs=/opt/devkitpro/libnx/switch.specs -Wl,--gc-sections \
    -Wl,-u,_Z10GetGameAPIP13game_import_t -Wl,-u,_Z8GetUIAPIv \
    main.o /input/game.a ui-renamed.a -L/opt/devkitpro/libnx/lib -lnx -o both.elf
  $BIN-nm -C both.elf > linked-symbols.txt
  grep " T GetGameAPI(game_import_t\\*)$" linked-symbols.txt
  grep " T GetUIAPI()$" linked-symbols.txt
  $BIN-nm -A /input/ui.a > ui-before.txt
  $BIN-nm -A ui-renamed.a > ui-after.txt
  grep -E ":gameinfo\.o:.*[[:space:]]B gi$" ui-before.txt
  grep -E ":g_weaponLoad\.o:.*[[:space:]]U gi$" ui-before.txt
  grep -E ":gameinfo\.o:.*[[:space:]]B efui_isolated_gi$" ui-after.txt
  grep -E ":g_weaponLoad\.o:.*[[:space:]]U efui_isolated_gi$" ui-after.txt
  $BIN-nm both.elf > linked-raw.txt
  grep -E "[[:space:]]B gi$" linked-raw.txt
  grep -E "[[:space:]]B efui_isolated_gi$" linked-raw.txt
  $BIN-ar p ui-renamed.a g_weaponLoad.o > ui-weapon.o
  $BIN-objdump -r ui-weapon.o > ui-weapon-relocs.txt
  grep -Eq "[[:space:]]efui_isolated_gi([+-]0x[0-9a-fA-F]+)?$" ui-weapon-relocs.txt
  if grep -Eq "[[:space:]]gi([+-]0x[0-9a-fA-F]+)?$" ui-weapon-relocs.txt; then
    echo "UI weapon object still relocates against unrenamed gi" >&2
    exit 1
  fi
  echo "UI weapon object relocations target efui_isolated_gi"'
