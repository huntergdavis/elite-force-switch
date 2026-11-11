#!/bin/sh
# Relink a copied prepared tree for state-layout inspection only.
set -eu
if [ "$#" -ne 1 ] || [ ! -f "$1/build/src/CMakeFiles/voyagersp.dir/link.txt" ] || [ ! -f "$1/efui-isolated.a" ]; then
  echo "usage: $0 <prepared-engine-experiment>" >&2
  exit 2
fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source=$(realpath "$1")
mkdir -p "$root/bootstrap/build"
out=$(mktemp -d "$root/bootstrap/build/ui-state-layout.XXXXXXXX")
echo "UI state layout experiment directory: $out"
cp -a --reflink=auto "$source/." "$out/"
image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
docker run --rm -u "$(id -u):$(id -g)" -v "$out:/work" -v "$root/bootstrap/generate_ui_state_linker.py:/generator.py:ro" "$image" \
  python3 /generator.py /opt/devkitpro/libnx/switch.ld /opt/devkitpro/libnx/switch.specs /work
docker run --rm -u "$(id -u):$(id -g)" -v "$out:/work" -w /work/build/src "$image" python3 -c '
import shlex, subprocess
args = shlex.split(open("CMakeFiles/voyagersp.dir/link.txt").read())
assert args.count("-specs=/opt/devkitpro/libnx/switch.specs") == 1
args = ["-specs=/work/switch-ui.specs" if a == "-specs=/opt/devkitpro/libnx/switch.specs" else a for a in args]
i = args.index("-o")
args[i+1] = "/work/ui-state-layout.elf"
args.append("-Wl,-Map,/work/ui-state-layout.map")
subprocess.run(args, check=True)
'
docker run --rm -v "$out:/work:ro" "$image" sh -c '/opt/devkitpro/devkitA64/bin/aarch64-none-elf-nm -n /work/ui-state-layout.elf | grep -E "efui_(data|bss)_(start|end)|__bss_(start|end)__"'
