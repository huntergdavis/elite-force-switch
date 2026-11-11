# Elite Force single-player on Nintendo Switch

An experimental Nintendo Switch port of *Star Trek: Voyager – Elite Force*
single-player, built on the VoyagerSP and VoyagerNX projects. The 0.1 beta
candidate has been tested on Switch: campaign gameplay, controller input,
and the single-player pause menu and saving work according to the device
tester. The whole campaign, cinematics, and every game edition have not been
tested.

## 0.1 beta

The 0.1 beta candidate restores the original single-player pause menu and fixes
a brief menu flash caused by capturing save thumbnails. The tested local build
also carries a locally sourced game icon; retail artwork is not included in
the source repository. Publication of a downloadable build is pending review
of the bundled source terms and release contents.

## What you need

- A Nintendo Switch set up to run homebrew.
- Your own legitimately obtained copy of Elite Force and its original game data.
- A Switch build of this port, made using the recipe below. No prebuilt release
  is included here.

This repository does not supply retail game data. Copy your own `pak0.pk3`,
`pak1.pk3`, `pak2.pk3`, and `pak3.pk3` from the game's `BaseEF` directory to:

```text
sdmc:/switch/elite-force-switch/baseEF/
```

Place the port's NRO in `sdmc:/switch/elite-force-switch/`, then launch it from
the Homebrew Menu. The exact files required may vary by game edition and patch
level; see [data requirements](bootstrap/DATA_REQUIREMENTS.md). Keep your game
files, keys, saves, and personal logs out of public uploads.

## Building

The build recipe needs Git, Python 3, a POSIX shell, and Docker. Docker must be
able to download and run the pinned devkitPro image. It also needs separate
local checkouts of [VoyagerSP-Android](https://github.com/imjustadudegamer/VoyagerSP-Android)
and [VoyagerNX](https://github.com/faithvoid/VoyagerNX). From this repository's
root, obtain the exact source revisions used by the recipe:

```sh
mkdir -p references
git clone https://github.com/imjustadudegamer/VoyagerSP-Android.git references/VoyagerSP-Android
git -C references/VoyagerSP-Android checkout --detach c73750361cfc22c1afb3a2c160fa9c5df57214db
git clone https://github.com/faithvoid/VoyagerNX.git references/VoyagerNX
git -C references/VoyagerNX checkout --detach 649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f
```

Build the GL1 renderer used by the tested Switch build:

```sh
./bootstrap/build.sh nx-gl1
```

The script prints an `Engine bootstrap experiment directory`. When the build
finishes, its ELF is at `build/Release/voyagersp.elf` inside that directory.
Pass that exact file to [`bootstrap/package.sh`](bootstrap/package.sh):

```sh
# Replace engine.REPLACE_ME with the directory printed by the build.
./bootstrap/package.sh bootstrap/build/engine.REPLACE_ME/build/Release/voyagersp.elf
```

The packaging script prints the new package directory. Copy its
`elite-force-engine.nro` to the Switch directory above. The script packages no
retail icon or game data. The upstream checkouts and build outputs are ignored
by Git and must not be uploaded with the release.

The tested Switch recipe does not save entered CD keys: its Switch-specific
patch disables key-file writes. It does not change the upstream key-reading or
validation functions; the pinned upstream's Elite Force validation branch
accepts any key. Consult the upstream license terms before using or
redistributing the resulting build.

The tested NRO was built incrementally from a prepared tree with the startup
logo suppression and UI-route tracing patches enabled. The build script now
applies the same patches: the prepared engine and game source directories and
the principal build inputs have been compared to the tested tree. A fresh
binary has not yet been compared byte for byte with the tested NRO; build
metadata and a locally supplied icon can differ.

## Source and licensing

This project builds on third-party engine and game-module code; it is not
solely newly generated code. The upstream engine and single-player game module
have different licenses. Their terms, including the conditions for distributing
the linked Switch build, remain under review. See
[the source review](bootstrap/PUBLIC_SOURCE_REVIEW.md) for provenance and the
specific unresolved questions, and [third-party notices](THIRD_PARTY_NOTICES.md)
for the pinned upstream license texts and component information. Do not assume
a single license applies to the whole repository or to a compiled binary.

This is an unofficial fan project, unaffiliated with the game's rights holders.
