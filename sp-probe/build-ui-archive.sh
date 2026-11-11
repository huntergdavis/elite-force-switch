#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_dir="$root/references/VoyagerSP-Android"
revision=c73750361cfc22c1afb3a2c160fa9c5df57214db
mkdir -p "$root/sp-probe/build"
scratch=$(mktemp -d "$root/sp-probe/build/ui-archive.XXXXXXXX")
echo "UI experiment directory: $scratch"
git -C "$source_dir" archive --output="$scratch/source.tar" "$revision" efgame
tar -xf "$scratch/source.tar" -C "$scratch"
python3 - "$scratch/efgame" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
def replace_once(path, old, new):
    text = path.read_text()
    if text.count(old) != 1:
        raise SystemExit(f'Unexpected upstream source in {path}: {old}')
    path.write_text(text.replace(old, new))
cmake = root / 'CMakeLists.txt'
for target in ('efgame', 'efui'):
    replace_once(cmake, f'add_library({target} SHARED', f'add_library({target} STATIC')
replace_once(root / 'src/ui/ui_game.cpp',
             'SGBLIP_MIN_X,\tSGPIC_Y-4-SGPIC_H-4-4,',
             'SGBLIP_MIN_X,\tstatic_cast<int>(SGPIC_Y-4-SGPIC_H-4-4),')
video = root / 'src/ui/ui_video.cpp'
replace_once(video, '30, 250 + 6 + (MENU_BUTTON_MED_HEIGHT * 1.5),',
             '30, static_cast<int>(250 + 6 + (MENU_BUTTON_MED_HEIGHT * 1.5)),')
replace_once(video, '30, 250 + (2 * (6 + (MENU_BUTTON_MED_HEIGHT * 1.5))),',
             '30, static_cast<int>(250 + (2 * (6 + (MENU_BUTTON_MED_HEIGHT * 1.5)))),')
PY
image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
docker run --rm -u "$(id -u):$(id -g)" -v "$scratch:/work" -w /work "$image" \
  cmake -S efgame -B build -DCMAKE_TOOLCHAIN_FILE=/opt/devkitpro/cmake/Switch.cmake \
  -DEF_PLATFORM=linux -DCMAKE_BUILD_TYPE=Release
docker run --rm -u "$(id -u):$(id -g)" -v "$scratch:/work" -w /work "$image" \
  cmake --build build --target efui -j2
