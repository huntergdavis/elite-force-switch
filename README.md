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
- A Switch build of this port; a public release has not yet been published.

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

The current build is experimental and requires Docker, the pinned devkitPro
image, and local reference checkouts of
[VoyagerSP-Android](https://github.com/imjustadudegamer/VoyagerSP-Android) and
[VoyagerNX](https://github.com/faithvoid/VoyagerNX). The scripts expect them in
`references/VoyagerSP-Android` and `references/VoyagerNX`, at the revisions
listed in [the source review](bootstrap/PUBLIC_SOURCE_REVIEW.md). See
[`bootstrap/build.sh`](bootstrap/build.sh) and
[`bootstrap/package.sh`](bootstrap/package.sh) for the current build and
packaging steps. For the experimental NX GL1 build, run
`./bootstrap/build.sh nx-gl1`, then pass the resulting ELF to
`./bootstrap/package.sh <path-to-elf>`. The build prints its experiment
directory; the ELF is under its `build/Release/` directory. The scripts use
local pinned reference checkouts.

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
