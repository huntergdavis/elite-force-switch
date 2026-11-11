#!/bin/sh
# Syntax-check the NX GL1 source set against SP's non-Vulkan headers.
set -eu
if [ "$#" -ne 1 ] || [ ! -f "$1/EFAndroid-SP/app/jni/efcode/qcommon/q_shared.h" ]; then
  echo "usage: $0 <SP-engine-experiment-directory>" >&2
  exit 2
fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
sp=$(realpath "$1")
mkdir -p "$root/bootstrap/build"
out=$(mktemp -d "$root/bootstrap/build/nx-gl1.XXXXXXXX")
git -C "$root/references/VoyagerNX" archive 649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f code/renderergl1 | tar -x -C "$out"
python3 - "$out/code/renderergl1" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
header = root / 'tr_local.h'
s = header.read_text()
if s.count('color4ub_t') != 4:
    raise SystemExit('unexpected NX renderer color type')
for p in [header, *root.glob('*.c')]:
    s = p.read_text()
    p.write_text(s.replace('color4ub_t', 'nx_color4ub_t'))
PY
image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
echo "GL1 check directory: $out"
docker run --rm -u "$(id -u):$(id -g)" -v "$out:/check" -v "$sp:/work:ro" "$image" sh -c '
  set -eu
  for dir in renderercommon qcommon client server; do ln -s /work/EFAndroid-SP/app/jni/efcode/$dir /check/code/$dir; done
  result=0
  for src in /check/code/renderergl1/*.c; do
    name=${src##*/}
    if /opt/devkitpro/devkitA64/bin/aarch64-none-elf-gcc -fsyntax-only -D__SWITCH__ -DELITEFORCE -DNO_VM_COMPILED -DUSE_LOCAL_HEADERS=1 -DARCH_STRING=\"arm64\" -I/opt/devkitpro/portlibs/switch/include/SDL2 -I/opt/devkitpro/portlibs/switch/include -I/opt/devkitpro/libnx/include "$src" > "/check/$name.log" 2>&1; then
      echo "PASS $name"
    else
      echo "FAIL $name (see $name.log)"
      result=1
    fi
  done
  exit "$result"
'
