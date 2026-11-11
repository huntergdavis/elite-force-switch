#!/bin/sh
# Package the explicitly selected ELF; this does not build or validate it.
set -eu
if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
  echo "usage: $0 <engine-elf>" >&2
  exit 2
fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$root/bootstrap/build"
out=$(mktemp -d "$root/bootstrap/build/package.XXXXXXXX")
cp "$1" "$out/engine.elf"
image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
docker run --rm -u "$(id -u):$(id -g)" -v "$out:/work" "$image" \
  /opt/devkitpro/tools/bin/elf2nro /work/engine.elf /work/elite-force-engine.nro
sha256sum "$out/engine.elf" "$out/elite-force-engine.nro"
echo "Package directory: $out"
