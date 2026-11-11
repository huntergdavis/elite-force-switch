#!/bin/sh
set -eu
if [ "$#" -ne 2 ]; then
  echo "usage: $0 <game-archive-experiment-dir> <collision-experiment-dir>" >&2
  exit 2
fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
game=$(realpath "$1")
collision=$(realpath "$2")
[ -f "$game/build/libefgame.a" ] && [ -f "$game/efgame/android/ef_android_compat.h" ] && [ -f "$collision/ui-renamed.a" ]
mkdir -p "$root/sp-probe/build"
out=$(mktemp -d "$root/sp-probe/build/combined-api.XXXXXXXX")
echo "Combined API experiment directory: $out"
image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
docker run --rm -u "$(id -u):$(id -g)" -v "$game:/game:ro" -v "$collision/ui-renamed.a:/input/ui.a:ro" \
  -v "$root/sp-probe:/probe:ro" -v "$out:/out" -w /out "$image" sh -c '
  set -eu
  CXX=/opt/devkitpro/devkitA64/bin/aarch64-none-elf-g++
  FLAGS="-std=gnu++17 -O2 -ffunction-sections -fdata-sections -march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft -fPIE"
  $CXX $FLAGS -I/opt/devkitpro/libnx/include -I/game/efgame/android \
    -I/game/efgame/src/game -I/game/efgame/src/cgame -I/game/efgame/src/ui \
    -I/game/efgame/src/icarus -I/game/efgame/src/qcommon -I/game/efgame/src/client \
    -I/game/efgame/src/renderer -I/game/efgame/src/speedrun \
    -include /game/efgame/android/ef_android_compat.h -c /probe/combined-api-main.cpp -o main.o
  $CXX $FLAGS -specs=/opt/devkitpro/libnx/switch.specs -Wl,--gc-sections \
    main.o /game/build/libefgame.a /input/ui.a -L/opt/devkitpro/libnx/lib -lnx -o combined-api.elf
  /opt/devkitpro/tools/bin/elf2nro combined-api.elf combined-api.nro'
