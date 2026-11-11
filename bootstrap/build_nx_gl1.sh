#!/bin/sh
# Start from a disposable prepared SP engine experiment; this is not a clean build.
set -eu
if [ "$#" -ne 1 ] || [ ! -f "$1/EFAndroid-SP/app/jni/src/CMakeLists.txt" ]; then
  echo "usage: $0 <prepared-SP-engine-experiment>" >&2
  exit 2
fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source=$(realpath "$1")
mkdir -p "$root/bootstrap/build"
# Reject stale prepared trees instead of silently retaining the old cursor no-op.
python3 - "$root" "$source" <<'PY_CHECK'
from pathlib import Path
import subprocess
import sys
import tempfile
root, source = map(Path, sys.argv[1:])
cmake = source / 'EFAndroid-SP/app/jni/src/CMakeLists.txt'
input_dir = source / 'EFAndroid-SP/app/jni/efcode/sdl'
bridge = source / 'EFAndroid-SP/app/jni/sp/sp_ui_bridge.cpp'
clipboard = 'static void UII_GetClipboardData(char* buf,int bufsize){ char* c=Sys_GetClipboardData(); sp_strncpyz(buf, c?c:"", bufsize); if(c) Z_Free(c); }'
if bridge.read_text().count(clipboard) != 1:
    raise SystemExit('prepared UI clipboard bridge lacks current cleanup; use a fresh build.sh nx-gl1')
cmake_text = cmake.read_text()
if '/work/switch_input_compat.c' in cmake_text:
    raise SystemExit('obsolete cursor no-op in prepared tree; use a fresh build.sh nx-gl1')
if cmake_text.count('${EF}/sdl/sdl_input_nx.c ${EF}/sdl/sdl_snd.c') != 1:
    raise SystemExit('prepared tree does not select current NX input; use a fresh build.sh nx-gl1')
with tempfile.TemporaryDirectory(prefix='nx-input-check.', dir=root / 'bootstrap/build') as tmp:
    expected = Path(tmp) / 'sdl_input_nx.c'
    with expected.open('wb') as out:
        subprocess.run(['git', '-C', str(root / 'references/VoyagerNX'), 'show',
                        '649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f:code/sdl/sdl_input_nx.c'],
                       stdout=out, check=True)
    subprocess.run([sys.executable, str(root / 'bootstrap/patch_nx_input.py'), str(expected),
                    str(input_dir / 'sdl_input.c')], check=True)
    if expected.read_bytes() != (input_dir / 'sdl_input_nx.c').read_bytes():
        raise SystemExit('prepared NX input differs from current adapter; use a fresh build.sh nx-gl1')
    ui = Path(tmp) / 'ui'
    ui.mkdir()
    for name in ('ui_atoms.cpp', 'ui_players.cpp', 'ui_turbolift.cpp'):
        with (ui / name).open('wb') as out:
            subprocess.run(['git', '-C', str(root / 'references/VoyagerSP-Android'), 'show',
                            'c73750361cfc22c1afb3a2c160fa9c5df57214db:efgame/src/ui/' + name],
                           stdout=out, check=True)
    subprocess.run([sys.executable, str(root / 'bootstrap/patch_ui_file_cleanup.py'), str(ui)], check=True)
    subprocess.run([sys.executable, str(root / 'bootstrap/patch_ui_readfile_cleanup.py'), str(ui)], check=True)
    for name in ('ui_atoms.cpp', 'ui_players.cpp', 'ui_turbolift.cpp'):
        if (ui / name).read_bytes() != (source / 'efgame/src/ui' / name).read_bytes():
            raise SystemExit('prepared UI sources differ from current cleanup; use a fresh build.sh nx-gl1')
PY_CHECK
out=$(mktemp -d "$root/bootstrap/build/nx-gl-engine.XXXXXXXX")
echo "NX GL1 engine experiment directory: $out"
cp -a --reflink=auto "$source/." "$out/"
git -C "$root/references/VoyagerNX" archive 649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f code/renderergl1 | tar -x -C "$out"
rm -rf "$out/EFAndroid-SP/app/jni/efcode/renderergl1"
mv "$out/code/renderergl1" "$out/EFAndroid-SP/app/jni/efcode/renderergl1"
git -C "$root/references/VoyagerNX" show 649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f:code/sdl/sdl_glimp.c > "$out/EFAndroid-SP/app/jni/efcode/sdl/sdl_glimp_nx.c"
cp "$root/bootstrap/nx_gl1_compat.c" "$out/nx_gl1_compat.c"
cp "$root/bootstrap/nx_gl1_thumbnail.inc" "$out/nx_gl1_thumbnail.inc"
python3 "$root/bootstrap/prepare_nx_gl1.py" "$out"
# Do not confuse a copied Vulkan ELF with a GL build result.
python3 -c 'import pathlib, sys; pathlib.Path(sys.argv[1]).unlink(missing_ok=True)' "$out/build/Release/voyagersp.elf"
image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
docker run --rm -u "$(id -u):$(id -g)" -v "$out:/work" "$image" cmake --build /work/build --target voyagersp -j2
