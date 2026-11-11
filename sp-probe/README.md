# Single-player source compile/link probe

Run `./sp-probe/build.sh` from the project root. It requires Docker and a clean
`references/VoyagerSP-Android` checkout at the pinned commit stated in the script.
It compiles the upstream campaign module's `src/game/q_math.cpp` with devkitA64,
links its `ClampChar` function into a minimal libnx NRO, and checks the linked
ELF symbol. The source is consumed from the reference checkout, not copied here.
The compatibility header produces a `__fastcall` redefinition warning with this
toolchain; its consequences beyond this compile probe have not been assessed.

The script also compiles `src/game/g_main.cpp` to `build/g_main.o`, checks that
it defines `GetGameAPI(game_import_t*)`, and writes `build/g_main-symbols.txt`.
That object is not linked into the NRO and has many unresolved symbols; its
successful compilation does not establish the game-module ABI, a loadable module,
or reset behavior. Its upstream source emits additional compiler warnings.

The reference checkout must be trusted: `git clean -ndx` skips nested Git
repositories and is not an exhaustive source-integrity check.

The NRO displays the result of `ClampChar(200)` and exits on Plus. It has not
been run on hardware. This is a single utility function, not the game module,
its import API, its reload lifecycle, the engine, graphics, or gameplay. Linker
section garbage collection discards unused functions. A successful build is not
evidence of a playable port.

The separate first-light NRO only reports the presence or access status of four
PK3 filenames and attempts a log; it does not validate archives, check ownership,
or start the game. The next playable milestone is the campaign menu and first
mission with controller and audio. Before that,
the full SP engine, renderer, native module linking and reset, assets, and
platform services require integration and on-device validation.

## Campaign archive experiment

`./sp-probe/build-game-archive.sh` extracts the pinned upstream revision into a
new directory under `build/`, changes its game and UI CMake targets from shared
to static in that extracted copy, and cross-builds only `efgame` with the pinned
devkitPro image. It uses upstream's `EF_PLATFORM=linux` CMake branch to obtain
its existing source list and options; this is an experiment, not a supported
Switch platform setting. The extracted copy and build outputs remain in the
printed directory for inspection. Upstream disables many compiler warnings for
this target, so a successful build does not mean the code is warning-free.

A successful `libefgame.a` only proves that this particular source list compiled
and archived. Static archives can contain unresolved symbols. It does not link
the archive into an engine, build the UI target, prove symbol isolation or reset
module globals on reload. Those remain open before an executable campaign.

After building the archive, the same script links a separate minimal
`game-link.nro`, forcing the linker to retain the archive's `GetGameAPI`
entry point and checking the ELF symbol table. The program does not call that
entry point. This tests link closure for the sections the linker retains, not
all functions in the archive, and it supplies neither the engine import table
nor UI, renderer, asset loading or module reset. It is not a game and has not
been run on Switch hardware.

The script also builds a distinct `game-api.nro` intended to call `GetGameAPI`
with a zeroed import table and synthetic read/free callbacks returning empty
weapon data. It checks the API version, selected non-null exports and callback
counts, displaying PASS or FAIL. This is a deliberately narrow synthetic test:
it does not call `Init`, validate retail data, provide an engine or exercise
reload. It has compiled and linked, but has not been executed; its behavior and
safety on Switch remain unverified.

## UI archive experiment

`./sp-probe/build-ui-archive.sh` extracts the same pinned source and builds only
`efui` as a static archive. GCC rejected three list initializers that convert
floating-point menu coordinates to integers. The script applies explicit
`static_cast<int>` conversions to those expressions in the extracted copy;
C++ conversion truncates toward zero. This is a compile experiment, not a
visual verification of the resulting menu coordinates. As in the game archive
experiment, the Linux CMake branch supplies upstream options; it is not a
supported Switch platform setting and upstream suppresses many warnings.

A separate exploratory link forcing both `GetGameAPI` and `GetUIAPI` failed
with duplicate definitions, including `Com_Error`, `Com_Printf`, `animTable`,
and `G_ParseString`/`G_ParseInt`/`G_ParseFloat`. Upstream builds separate shared libraries with per-target export version
scripts; actual symbol isolation also depends on loader flags and visibility.
A combined static build needs a validated isolation strategy. No combined module, UI behavior, graphics or hardware is established.

## Static collision experiment

After building both archives with the scripts above,
`./sp-probe/test-static-collisions.sh <path-to-libefgame.a> <path-to-libefui.a>`
intersects selected `nm` global definition types (`TDBRSVWCG`) from the two
archives, renames those names
throughout a copy of the UI archive with `objcopy --redefine-syms`, and attempts
a combined ELF link with both entry points retained. Other symbol types are excluded, so this is not an exhaustive collision census.
Inputs are caller-selected; the script does not verify their provenance. It writes the name list, renamed
archive, and linked-symbol inventory to a fresh directory under `build/`.

This is a link experiment, not a validated isolation mechanism: matching symbol
names alone cannot determine intended ownership, internal versus external
references, weak-symbol behavior, ABI compatibility, or state reset. A successful
link does not show that either entry point works, and the ELF is not packaged
or run. The UI coordinate casts and all existing runtime limitations apply.

For the pinned source configuration, the script also checks one specific
ownership case. The game declares `game_import_t gi` in `src/game/g_main.cpp`;
the UI build declares `gameinfo_import_t gi` in `src/ui/gameinfo.cpp`, and its
`g_weaponLoad.o` references that name. The script checks that the transformed
UI archive contains a renamed UI definition and reference, and that the linked
ELF contains both the original and renamed definitions. These symbol-table
checks do not prove every relocation binds as intended or that either table
works at runtime. They are specific to the expected object names and do not
validate all other mapped symbols.

`./sp-probe/build-combined-experiment.sh` runs both pinned-source archive builds
and then supplies their freshly produced archives to the collision experiment.
It builds the combined synthetic API probe from that game archive and renamed
UI output. It preserves each command's log in the printed run directory. It does not
change the collision experiment's behavioral, isolation, or runtime limits.

The collision script additionally inspects relocations in the renamed UI
`g_weaponLoad.o`: at least one must name `efui_isolated_gi`, and none may name
unrenamed `gi`. This is an object-file check before final linking. It does not
validate other UI objects, the linker's final relocation targets, or runtime
behavior.

The script also compares each archive’s undefined names with `nm` types `U`,
`w`, and `v` against definitions found only in the other archive in the selected
types, and fails if either intersection is nonempty. Other undefined types are excluded. This is an
archive-wide name check, not proof of link bindings: it excludes other symbol
types, does not identify which objects are retained, and cannot detect semantic
aliasing, external library resolution, or runtime behavior.

## Combined synthetic API probe

`./sp-probe/build-combined-api.sh <game-archive-experiment-dir>
<collision-experiment-dir>` builds a separate NRO that intends to call both
`GetGameAPI` with the same synthetic empty weapon data as `game-api.nro` and
`GetUIAPI`, then inspect selected non-null entries. It calls neither module's
`Init` function. Input paths are caller-selected and are not provenance-checked;
the UI archive must be the renamed output of the collision experiment. The NRO
has not been executed or reviewed for hardware distribution. A build does not
establish callback safety, symbol-isolation correctness, UI behavior, reload,
engine integration, or gameplay.
