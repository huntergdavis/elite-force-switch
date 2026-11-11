# Public source preparation: review required

No release or push has been approved by this document. The owner requires a
public fork without retail game data, keys, device logs, or unlicensed binary
artifacts. Users must supply their own original game files; see
[DATA_REQUIREMENTS.md](DATA_REQUIREMENTS.md). Do not publish until the owner
verifies gameplay and the complete proposed history and license review have
been independently accepted.

## Source provenance requiring review

The build scripts consume these separate, locally ignored reference checkouts:

- [VoyagerSP-Android](https://github.com/imjustadudegamer/VoyagerSP-Android),
  pinned commit `c73750361cfc22c1afb3a2c160fa9c5df57214db`.
- [VoyagerNX](https://github.com/faithvoid/VoyagerNX), pinned commit
  `649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f`.

VoyagerSP-Android's README describes its engine/port as GPLv2 and its `efgame`
module as subject to the STEF Game Source License, and points to its LICENSE,
license document and credits. VoyagerNX identifies its engine as GPLv2 or
later and states that game, cgame and UI code is not included due to non-free
terms. These statements do not settle the terms for this repository: scripts,
patches, fixtures and generated artifacts may contain or derive from either
source and require file-by-file provenance and license review. Check all
third-party notices and binary distribution obligations separately. No
repository-wide license is asserted here pending that review.

## Initial history screen

At commit `2ed6797`, `git rev-list --objects --all` identified 495 reachable
objects, including 245 blobs totaling 1,366,172 bytes. A binary screen found no
NUL-containing blobs. A filename screen for common archive, executable,
media, configuration, log and key extensions found no matches. These are
heuristics, not proof that every blob is free of private material or that all
source is redistributable. Repeat against the exact proposed refs immediately
before any push; examine content and origin, not just filenames or sizes.

The local `references/`, `bootstrap/build/`, `evidence/`, and Dunking Sheep
state are not intended for publication. The diagnostic history contains paths,
hashes and descriptions of local experiments, so review those text blobs for
private details too. No remote is configured in this repository as of this
screen; identify the owner's actual fork before preparing a destination.

## Independent audit findings

Two independent screens of `c8afcbb` reported 248 reachable blob versions and
no matches for the binary and sensitive-content heuristics they applied. Neither
review establishes privacy or licensing clearance. Both identified embedded SP
UI fragments in `patch_ui_file_cleanup.py` and `patch_ui_narrowing.py`, copied
SP/NX input code in `patch_nx_input.py`, and an unresolved template provenance
for `first-light/Makefile`. `patch_ui_readfile_cleanup.py` also reproduces SP
UI fragments. Review the actual upstream notices and STEF terms, copied source,
dependencies and the distribution obligations for resulting binaries. The
repository currently has no tracked LICENSE or NOTICE; do not infer a license
from these notes.

The history also contains author/committer email addresses, which would become
public if those commits are pushed. The owner should review that disclosure.
The ignored evidence directory contains retail archives and local logs; never
stage it. Repeat all checks for the exact proposed refs, including this update,
before any publication.

## Upstream game-source terms examined

The pinned SP reference includes `efgame/STEF Game Source License.doc`.
Section 3(a) describes conditions for free, noncommercial electronic copies of
the Software, including that the agreement accompany each copy, and limits New
Creations to operation with the full game. Section 3(b) sets conditions for
distributing New Creations. Section 2(l) prohibits altering, disabling or
reducing game anti-piracy components including the CD-key system. These are
source-document observations, not a conclusion about the rights or obligations
of a particular distribution. In particular, the Switch code modifies CD-key
persistence and UI routing, and the candidate statically links the SP module
with a GPL-derived engine. The applicability and compatibility of these terms,
including the CD-key restriction, must be resolved by a qualified reviewer or
rights holder before publishing either source or binary. Adding notices alone
does not resolve those questions.

The owner has now reported that the controls build works. That test does not
establish licensing or establish that a clean, reproducible release build
matches the incrementally linked candidate. Independent license/provenance
review and exact-source/artifact review remain prerequisites to publication.

An independent reviewer inspected the candidate link command and identified
isolated game/UI and SP bridge libraries, SDL2, EGL, glapi, drm_nouveau, glad,
libnx, FFmpeg libraries, dav1d, bz2, z and toolchain runtime as link inputs.
A link command alone does not prove which archive members are present in the
final NRO. A release audit must use the link map and pinned toolchain package
metadata to identify incorporated components, FFmpeg configuration, licenses,
notices and corresponding-source obligations. The reviewer also identified
potential conflict between the GPL engine's redistribution terms and Raven's
noncommercial/full-game restrictions on a statically combined work. Qualified
review or a compatible rights grant is needed; this is not a legal conclusion.
