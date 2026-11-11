#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_dir="$root/references/VoyagerSP-Android"
revision=c73750361cfc22c1afb3a2c160fa9c5df57214db
if [ "$(git -C "$source_dir" rev-parse HEAD)" != "$revision" ] || [ -n "$(git -C "$source_dir" status --porcelain --untracked-files=all)" ] || [ -n "$(git -C "$source_dir" clean -ndx)" ]; then
    echo 'VoyagerSP reference must be clean and at the pinned revision.' >&2
    exit 1
fi
mkdir -p "$root/sp-probe/build"
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$source_dir/efgame:/sp:ro" -v "$root/sp-probe:/probe:ro" \
  -v "$root/sp-probe/build:/out" -w /out \
  devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282 \
  sh -c 'set -eu
    CXX=/opt/devkitpro/devkitA64/bin/aarch64-none-elf-g++
    FLAGS="-std=gnu++17 -O2 -ffunction-sections -fdata-sections -march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft -fPIE"
    $CXX $FLAGS -fno-strict-aliasing -fno-threadsafe-statics -fcommon \
      -I/sp/android -I/sp/src/game -I/sp/src/cgame -I/sp/src/ui \
      -I/sp/src/icarus -I/sp/src/qcommon -I/sp/src/client -I/sp/src/renderer \
      -I/sp/src/speedrun -include /sp/android/ef_android_compat.h \
      -c /sp/src/game/q_math.cpp -o q_math.o
    $CXX $FLAGS -fno-strict-aliasing -fno-threadsafe-statics -fcommon -DNDEBUG \
      -I/sp/android -I/sp/src/game -I/sp/src/cgame -I/sp/src/ui \
      -I/sp/src/icarus -I/sp/src/qcommon -I/sp/src/client -I/sp/src/renderer \
      -I/sp/src/speedrun -I/sp/src/speedrun/strafe_helper \
      -I/sp/src/speedrun/overbounce_prediction -include /sp/android/ef_android_compat.h \
      -c /sp/src/game/g_main.cpp -o g_main.o
    /opt/devkitpro/devkitA64/bin/aarch64-none-elf-nm -C g_main.o > g_main-symbols.txt
    grep " T GetGameAPI(game_import_t\*)$" g_main-symbols.txt
    $CXX $FLAGS -I/opt/devkitpro/libnx/include -c /probe/main.cpp -o main.o
    $CXX $FLAGS -specs=/opt/devkitpro/libnx/switch.specs -Wl,--gc-sections \
      main.o q_math.o -L/opt/devkitpro/libnx/lib -lnx -o sp-probe.elf
    /opt/devkitpro/tools/bin/elf2nro sp-probe.elf sp-probe.nro
    /opt/devkitpro/devkitA64/bin/aarch64-none-elf-nm -C sp-probe.elf | grep " T ClampChar(int)$"'
