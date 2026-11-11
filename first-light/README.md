# First-light diagnostic

This is a standalone libnx diagnostic, not the game engine. It reports whether
`pak0.pk3` through `pak3.pk3` are regular files in
`sdmc:/switch/elite-force-switch/baseEF/`. It does not inspect archive contents,
verify retail ownership, or establish that data is usable. The upstream SP port
also requires `efgamex86.dll` for its ownership check; this diagnostic does not
implement that check.

Build with devkitPro's Switch toolchain (`make` in this directory). The following pins the Docker repository digest used for the local build. It
contains devkitA64 r29.2-1 (GCC 15.2.0), libnx 4.12.0-1 and switch-tools
1.13.1-1:

```
docker run --rm -u "$(id -u):$(id -g)" -v "$PWD:/work" -w /work devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282 make
```

Copy `EliteForceFirstLight.nro` into `switch/elite-force-switch/` on the SD card,
put your own retail and patch files in the `baseEF` subdirectory, and launch via
the homebrew menu. The display gives per-file results; a log is written to
`switch/elite-force-switch/first-light.log` if possible. Press Plus to exit.
No retail data is included. The application has not been run on Switch hardware.

Acceptance still requires a hardware launch, missing-file and present-file
checks, and checking the log on the SD card. Do not interpret a successful
cross-compile as a launch or gameplay result.
