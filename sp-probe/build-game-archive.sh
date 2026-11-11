#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_dir="$root/references/VoyagerSP-Android"
revision=c73750361cfc22c1afb3a2c160fa9c5df57214db
mkdir -p "$root/sp-probe/build"
scratch=$(mktemp -d "$root/sp-probe/build/game-archive.XXXXXXXX")
echo "Archive experiment directory: $scratch"
git -C "$source_dir" archive --output="$scratch/source.tar" "$revision" efgame
tar -xf "$scratch/source.tar" -C "$scratch"
python3 - "$scratch/efgame/CMakeLists.txt" <<'PY'
import pathlib, sys
path = pathlib.Path(sys.argv[1])
text = path.read_text()
for target in ('efgame', 'efui'):
    old = f'add_library({target} SHARED'
    if text.count(old) != 1:
        raise SystemExit(f'Unexpected upstream CMake declaration: {old}')
    text = text.replace(old, f'add_library({target} STATIC')
path.write_text(text)
PY
image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
docker run --rm -u "$(id -u):$(id -g)" -v "$scratch:/work" -w /work "$image" \
  cmake -S efgame -B build -DCMAKE_TOOLCHAIN_FILE=/opt/devkitpro/cmake/Switch.cmake \
  -DEF_PLATFORM=linux -DCMAKE_BUILD_TYPE=Release
docker run --rm -u "$(id -u):$(id -g)" -v "$scratch:/work" -w /work "$image" \
  cmake --build build --target efgame -j2
docker run --rm -u "$(id -u):$(id -g)" -v "$scratch:/work" \
  -v "$root/sp-probe:/probe:ro" -w /work "$image" sh -c '
    set -eu
    CXX=/opt/devkitpro/devkitA64/bin/aarch64-none-elf-g++
    FLAGS="-std=gnu++17 -O2 -ffunction-sections -fdata-sections -march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft -fPIE"
    $CXX $FLAGS -I/opt/devkitpro/libnx/include -c /probe/game-link-main.cpp -o game-link-main.o
    $CXX $FLAGS -specs=/opt/devkitpro/libnx/switch.specs -Wl,--gc-sections \
      -Wl,-u,_Z10GetGameAPIP13game_import_t game-link-main.o build/libefgame.a \
      -L/opt/devkitpro/libnx/lib -lnx -o game-link.elf
    /opt/devkitpro/devkitA64/bin/aarch64-none-elf-nm -C game-link.elf > game-link-symbols.txt
    grep " T GetGameAPI(game_import_t\\*)$" game-link-symbols.txt
    /opt/devkitpro/tools/bin/elf2nro game-link.elf game-link.nro'
docker run --rm -u "$(id -u):$(id -g)" -v "$scratch:/work" \
  -v "$root/sp-probe:/probe:ro" -w /work "$image" sh -c '
    set -eu
    CXX=/opt/devkitpro/devkitA64/bin/aarch64-none-elf-g++
    FLAGS="-std=gnu++17 -O2 -ffunction-sections -fdata-sections -march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft -fPIE"
    $CXX $FLAGS -I/opt/devkitpro/libnx/include -I/work/efgame/android \
      -I/work/efgame/src/game -I/work/efgame/src/cgame -I/work/efgame/src/ui \
      -I/work/efgame/src/icarus -I/work/efgame/src/qcommon -I/work/efgame/src/client \
      -I/work/efgame/src/renderer -I/work/efgame/src/speedrun \
      -include /work/efgame/android/ef_android_compat.h -c /probe/game-api-main.cpp -o game-api-main.o
    $CXX $FLAGS -specs=/opt/devkitpro/libnx/switch.specs -Wl,--gc-sections \
      game-api-main.o build/libefgame.a -L/opt/devkitpro/libnx/lib -lnx -o game-api.elf
    /opt/devkitpro/tools/bin/elf2nro game-api.elf game-api.nro'
