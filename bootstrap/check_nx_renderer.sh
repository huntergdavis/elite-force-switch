#!/bin/sh
# Compile one NX GL1 source against the extracted SP headers; failure is evidence, not an integration.
set -eu
if [ "$#" -ne 1 ] || [ ! -f "$1/EFAndroid-SP/app/jni/efcode/qcommon/q_shared.h" ]; then
  echo "usage: $0 <SP-engine-experiment-directory>" >&2
  exit 2
fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
sp=$(realpath "$1")
mkdir -p "$root/bootstrap/build"
out=$(mktemp -d "$root/bootstrap/build/nx-renderer.XXXXXXXX")
mkdir "$out/renderergl1"
for file in tr_init.c tr_local.h; do
  git -C "$root/references/VoyagerNX" show "649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f:code/renderergl1/$file" > "$out/renderergl1/$file"
done
image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
echo "Renderer check directory: $out"
docker run --rm -u "$(id -u):$(id -g)" -v "$out:/check" -v "$sp:/work:ro" "$image" sh -c '
  set -eu
  for dir in renderercommon qcommon client server; do ln -s /work/EFAndroid-SP/app/jni/efcode/$dir /check/$dir; done
  /opt/devkitpro/devkitA64/bin/aarch64-none-elf-gcc -fsyntax-only -D__SWITCH__ -DELITEFORCE -DNO_VM_COMPILED -DUSE_LOCAL_HEADERS=1 -DUSE_VULKAN -DUSE_VULKAN_API -DARCH_STRING=\"arm64\" -I/opt/devkitpro/portlibs/switch/include/SDL2 -I/opt/devkitpro/portlibs/switch/include -I/opt/devkitpro/libnx/include /check/renderergl1/tr_init.c
'
