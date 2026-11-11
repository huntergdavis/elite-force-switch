# Experimental SP engine bootstrap

These are historical development notes. The current GL1 build has since been
tested on Switch with campaign gameplay, controller input and the pause/save
menu; see the [project README](../README.md) for current build instructions
and their limitations. Statements below about missing gameplay, old lifecycle
behavior and absent hardware tests describe earlier experiments.

The earlier integration attempt was not yet playable. The Switch
entry point in `switch_main.c` calls the pinned VoyagerSP engine's actual
platform/time setup, sets the binary, install and home paths to
`sdmc:/switch/elite-force-switch`, then calls `CON_Init`, `Com_Init`,
`NET_Init`, and `Com_Frame` within the libnx applet loop. The startup sequence
is based on `EFAndroid-SP/app/jni/efcode/sys/sys_main.c:832-939` in the pinned
reference; the applet loop follows `references/VoyagerNX/code/sys/sys_main_nx.c`.
It attempts a small phase trace at `engine-bootstrap.log` and asks the engine
for `logfile 2`; neither logging path has been tested on Switch. It does not
implement the upstream desktop data importer or verify retail ownership.

`./bootstrap/build.sh` extracts VoyagerSP revision
`c73750361cfc22c1afb3a2c160fa9c5df57214db`, injects the Switch main into its
real `voyagersp` target, renames the original main while retaining its other
system functions, and uses the pinned devkitPro container. It adds a minimal
Switch `q_platform.h` branch and sets the target architecture string to arm64;
`.so` there is a build placeholder and is not a claim of dynamic loading.
It selects the upstream Linux CMake branch and static Vulkan renderer solely as
a build experiment; neither is an established Switch implementation.

The Switch toolchain lacks `dlfcn.h`, used by both SP bridges. The build
substitutes `switch_static_loader.h` only in those two bridge files. It maps the
exact pinned game/UI entry-point symbol names to static linker symbols, permits
one load of each module per process, and refuses all later loads after close.
Close does **not** reset globals. This is a fail-closed lifecycle boundary, not
an implementation of module reload: upstream reloads UI during startup, so this
restriction prevents a normal menu path. The game and renamed UI archives are linked into the experimental engine ELF;
proving their isolation remains work to do. The adapter is not a general dynamic loader.

A host-only adapter test can be run with `g++ -std=c++17 -Wall -Wextra -Werror
bootstrap/test_static_loader.cpp -o bootstrap/build/test-static-loader` followed
by `bootstrap/build/test-static-loader`. It checks names, handles and refusal to
reload, not execution of the actual modules or behavior on Switch.

The renderer import expects `const char *` while the engine function returns
`char *`. `renderer_cvar_adapter.c` provides a matching function type and
returns the engine pointer as read-only; it does not change the string. The
host fixture in `test_renderer_cvar_adapter.c` checks the forwarded argument
and pointer. The bootstrap object and SP bridge library compile, and the engine
build gets past `cl_main.c`. The Switch build now excludes the unavailable
`ifaddrs.h`, following the pinned VoyagerNX `code/qcommon/net_ip.c:80`; the
SP source's non-BSD path attempts hostname-based discovery with assumed masks.
That fallback and networking have not been tested on Switch. The Switch-only
multicast patch excludes unavailable IPv6 multicast structures and operations,
reports multicast as unsupported, and drops multicast sends before address
conversion. It retains the original multicast functions for non-Switch builds.
This is an explicit loss of IPv6 multicast, not evidence that other network
behavior works. `net_ip.c` now compiles. The build uses `sys_nx.c` from pinned VoyagerNX
`649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f` rather than SP's `sys_unix.c`,
which requires unavailable `sys/mman.h`. It adds the SP home-path setter and
uses the pinned SP `Sys_Basename` and `Sys_Dirname` implementations to match
its const signatures and slash-based paths; VoyagerNX's versions use backslash
separators. The Switch platform object compiles, but its runtime behavior and
compatibility with SP have not been verified. For `sp_integration.c`, the Switch build excludes unavailable `dlfcn.h` and
retains the unwinder while logging raw frame addresses in place of `dladdr`
symbol names. The original symbolizer remains in the non-Switch branch. This
entry point does not install the upstream signal handlers, so even invocation of
that diagnostic is not established; crash handling, unwinding, output, and
async-signal safety are not validated. `sp_integration.c` compiles.
The renderer's entity parse cursor declarations are adapted to `char *` to
match the engine parser: `R_LoadEntities` allocates the underlying entity string
as writable memory, and `COM_ParseExt` advances the cursor. The host patch test
checks the two declaration changes, not parser behavior. `tr_bsp.c` compiles.
The renderer export table has incompatible internal signatures. Experimental
typed adapters preserve the existing numeric 0/1 shutdown mapping to
`REF_KEEP_CONTEXT`/`REF_KEEP_WINDOW`, supply `qfalse` for the renderer's extra
entity argument, and reject both Vulkan cinematic exports with `ERR_DROP` before any
allocation or renderer call. This is a deliberate loss of cinematic support:
the earlier copy-and-free approach leaked on renderer `ERR_DROP` nonlocal
exits, and downstream resource creation has further error paths. A host fixture
exercises the rejection and shutdown/entity mappings; it does not establish
renderer semantics, engine error recovery or performance. In particular, upstream call-site comments disagree about what a
true shutdown value means; the mapping preserves the observed numeric convention,
not a verified shutdown contract. The build compiles `tr_init.c`.

The shader parser uses `const char **` cursors, while the pinned engine helpers
accept `char **`. The shader-only adapter copies the pointer to a local mutable-
typed cursor, calls the existing helper, and copies the advanced cursor back;
it never aliases a `const char **` as `char **`. This relies on the pinned
`q_shared.c` helpers reading, not writing, input bytes; a future parser change
must be audited. A host fixture exercises the actual pinned parser with literal
and mutable input, token, line, null-cursor and nested-brace cases. The patch
check covers the 76 active parse calls and 11 skip calls. This does not establish
all shader behavior or Switch runtime safety.

The extracted Switch-only build removes the desktop target's explicit `-ldl`
link item because the toolchain has no such library and this experiment selects
a static renderer and bridge adapter. This does not remove all dynamic-loading
assumptions or prove that they are resolved. The Switch platform adapter now
implements `Sys_Remove` using the upstream `remove` behavior, returns an empty
Microsoft Store path, and writes dialog text to stderr while choosing no/cancel
for prompts. There is no tested on-device dialog UI. Since `umask` is absent,
the Switch branch explicitly refuses CD-key persistence instead of writing a
key without the upstream protection; this is a functional limitation.

The build compiles the actual SP game and UI static archives. The UI archive
renames selected definitions shared with the game archive. The game archive
renames five observed engine collisions: `com_buildScript`, `bytedirs`,
`vec3_origin`, `g_color_table`, and `axisDefault`. Both engine and game source
define these globals separately; game initializes its own `com_buildScript`
through its import table. The remaps preserve the observed archive symbol
records, but do not establish complete semantic isolation or correct bindings.
A fresh `bootstrap/build/attempt17.log` build linked an AArch64 engine ELF
(`engine.cx6Tiw83/build/Release/voyagersp.elf`); it did not execute the engine. The ELF SHA-256 is
`594c1bea1e8c3fc2059e30d353b1a72b6748f3fee20dbd6273d57aa30520ef43`.

There is also an unresolved renderer constant mismatch: public
`renderercommon/tr_types.h` defines `REFENTITYNUM_BITS` as 10, while
`renderervk/tr_local.h` redefines it as 12. The renderer's sort layout uses
one dlight bit, five fog bits, 12 entity bits and 14 shader bits (32 total),
and its internal world sentinel is consequently 4095 rather than the public
header's 1023. The code references internal masks and sentinel in renderer
sorting and scene handling. We have not established whether any value crosses
the engine/renderer boundary with a conflicting interpretation; do not treat
renderer ABI or draw behavior as validated. The build also emits
`USE_FLEXIBLE_DISPLAY` redefinition warnings. The host source-transformation test
is `python3 bootstrap/test_patch_switch_multicast.py`; it does not execute the
network stack.
Platform services, renderer, module lifecycle, audio, input, data validation,
logging, shutdown, linked symbol behavior and hardware behavior remain unverified.
The packaged NRO has not been run on hardware.

## VoyagerNX input integration experiment

The current build selects `code/sdl/sdl_input_nx.c` from pinned VoyagerNX,
with `patch_nx_input.py` adding the pinned SP `IN_Rumble` implementation and
its cvars. It uses the NX controller, on-screen keyboard and motion sensor code;
it stops active controller rumble before both NX close paths. The SP input's
separate damage-rumble trigger and menu mapping are not carried over. This
choice and the NX controller, sensor and rumble behavior have not been tested
on hardware. A separately compiled AArch64 input object exported `IN_Rumble`;
this does not validate its behavior. The first incremental engine link failed on
SP's `IN_SyncMousePosition`, absent from NX input. The current input adaptation
copies SP's cursor conversion and sync functions, initializes the last mouse
position, and routes absolute menu motion through that conversion. A host
fixture checks clamping, SP UI sync and the disabled path; it does not test the
SDL event loop, controller interactions or hardware. The NX frame path now
releases relative mouse mode for a flexible-display UI and restores SP's saved
mouse position and cursor visibility rules on deactivation. A stubbed host
fixture checks the deactivation function; the frame branch, controller
interaction and actual SDL behavior remain unverified. An incremental GL link
with this transition produced ELF SHA-256
`8593d34f1ca574521f7f13ee53aa9c08a663da8d3f9862ec08405e33ff960e48`
(log `bootstrap/build/nx-gl-menu-mouse.log`); it was not run on hardware.
An earlier incremental GL link with cursor sync, before the mouse-mode
transition, produced ELF SHA-256
`f2964c731c49bc88dc3270d25b70c525ab87d892f16515a2154f64bb0ca45aad`
(log `bootstrap/build/nx-gl-cursor-attempt2.log`). This is not a fresh build or
runtime test. A prepared-tree replay using the current guards completed with
exit 0 and produced the same hash (log `bootstrap/build/gl-current-replay2.log`,
output `nx-gl-engine.CukIbX00`). Its input was an updated copy of the earlier
prepared tree, so this is not a clean build or provenance proof. That tree was
subsequently rebuilt for thumbnail integration; the same cursor ELF remains
in `engine.UzdPMgMY/build/Release/voyagersp.elf`. A prior replay
linked the same hash but its wrapper exited 127 after the script was edited while
running; it is not counted as a successful script run.

`check_nx_renderer.sh` compiles pinned NX GL1 `tr_init.c` and `tr_local.h`
against the extracted SP headers in a specified existing engine experiment.
It is an incompatibility check, not a renderer build. With the SP Vulkan
preprocessor settings it failed on NX's array `color4ub_t` versus SP's union,
and NX calls passing numeric bounds to SP's string-based `Cvar_CheckRange`.
Other incompatibilities and any GL integration remain untested; switching API
versions or adapting those two failures alone would not establish correctness.
`check_nx_gl1.sh` exercises the alternative non-Vulkan SP interface: it
extracts the pinned NX GL1 sources, renames their local array color type to
avoid SP's union type, and syntax-checks all 24 GL1 `.c` files. The pinned
container check passed without compiler diagnostics using the extracted SP
headers in `engine.5SAsswO1`. The check accepts a caller-selected SP experiment
directory and does not verify its provenance or cleanliness. This only checks each
translation unit against those headers: it does not link a renderer, validate the
import/export layout or SP rendering features, or establish Switch behavior.
The existing engine target still uses Vulkan.
See [VOYAGERNX.md](VOYAGERNX.md) for the platform comparison.

## VoyagerNX GL1 engine experiment

To build from a fresh extraction of the pinned SP and VoyagerNX revisions, run
`./bootstrap/build.sh nx-gl1`. With no argument (or `vulkan`) the original
Vulkan experiment remains selected. The GL build uses the same input and
lifecycle boundaries described above; a successful cross-build would not
establish runtime behavior.

`./bootstrap/build_nx_gl1.sh <prepared-SP-engine-experiment>` clones the
caller-selected prepared tree, selects the pinned NX GL1 renderer and its SDL
window implementation, disables the SP Vulkan configuration, and links NX's
EGL/glapi/drm_nouveau/glad dependencies. The script does not verify the input
tree's revision or cleanliness; it is an incremental experiment, not a clean
reproducible build. It rejects a tree containing the old cursor no-op, one lacking the expected
literal NX input fragment in its CMake source list, or an NX input file that
differs from the current adapter applied to the tree's SP input. It also
compares the three UI cleanup source files with patched pinned versions and
checks for the clipboard cleanup adapter. The text check does not prove effective CMake selection or full tree provenance. It removes the copied ELF before building so an old Vulkan
artifact cannot be mistaken for the result.

The first GL engine link failed on SP's Vulkan device-loss functions and five
render-thread imports absent from NX SDL. The experiment supplies a boundary
that always reports no Vulkan device loss, and initializes those thread
imports to NULL; the inspected NX GL1 source does not reference them. This does
not provide GL device-loss handling or render-thread support. The incremental
follow-up linked an AArch64 ELF in `nx-gl-engine.Pu8SWmbH` (log
`bootstrap/build/nx-gl-engine-attempt3.log`, SHA-256
`2c6e27091e401680a646aca051bd2262810090cf7037227ad394e6fb4c54a5b0`).
Its caller-selected input was `engine.5SAsswO1`; the build reused its prior
objects and was manually continued after the first failure. No clean rebuild,
NRO conversion, ABI or gameplay validation, or hardware execution is claimed.

A subsequent fresh pinned-source `./bootstrap/build.sh nx-gl1` run in
`engine.UzdPMgMY` was interrupted during compilation and resumed in that same
tree with `cmake --build /work/build --target voyagersp -j4` in the pinned
container. It completed with exit 0; the two logs are `nx-gl-clean.log` and
`nx-gl-clean-resumed.log` under `bootstrap/build`. No earlier build objects
were copied into this tree. At that point the linked ELF had the same SHA-256 as the
incremental ELF above; the tree was subsequently modified and incrementally
rebuilt for cursor integration. The original ELF is preserved in
`bootstrap/build/package.H0JN5e6f/engine.elf`. The build emitted `USE_FLEXIBLE_DISPLAY` redefinition
warnings. This is a fresh-source build, not an uninterrupted full-script run
or proof of runtime behavior.

The input, UI lifecycle, cursor-sync, cinematics and symbol-isolation
limitations remain open. In this GL build, NX `GetRefAPI` is compiled against
SP's public header with `USE_FLEXIBLE_DISPLAY`, so it reports API version 9.
The earlier GL artifact zeroed its export table and left SP's save-thumbnail
and `ResizeWindow` callbacks unset. The current GL build experiment installs
thumbnail callbacks using a checked GL readback immediately before buffer swap,
downscaling bottom-up RGB into opaque 256x256 RGBA. It rejects a pre-existing
GL error (consuming one error), non-default row/skip/pack-buffer state,
unsupported alignment, oversized dimensions or allocation, allocation failure,
and reported readback errors. Its temporary buffer is initialized. A host
fixture exercises success and those failure branches; it does not execute GL.
An incremental link produced ELF SHA-256
`2c128f6f37998ab0dc24b952b12c196c88d3645f6b256fa953665c84457b8a51`
(log `bootstrap/build/nx-gl-thumb-checked.log`). A fresh pinned-source GL build
in `engine.El40Oylv`, started with `build.sh nx-gl1` and interrupted then resumed
in the same tree with `cmake --build /work/build --target voyagersp -j4`,
completed with exit 0 and produced the same hash. Logs are
`nx-gl-thumb-fresh.log` and `nx-gl-thumb-fresh-resumed.log`; no earlier build
objects were copied. That tree was subsequently changed for the mouse-mode
transition; the prior checked-thumbnail ELF remains in
`nx-gl-engine.CukIbX00/build/Release/voyagersp.elf`. This was not an uninterrupted script run. The previous unreviewed
thumbnail ELF `1564664742ee9531739067dc1a31eb7f6a93d59f9206bcdb8fa9e73f8f2d3788`
had an unsafe unchecked readback and must not be used. GL readback, frame timing,
error handling, save behavior and hardware are unverified. The earlier startup
NRO does not include this change. `ResizeWindow` remains unset. The NX input path does not implement SP's flexible-display resize; its cursor synchronization adaptation remains
untested on hardware. Renderer ABI and other export behavior remain unverified. NX GL1 has its own cinematic exports; their behavior
has not been verified, and the Vulkan-specific rejection above does not establish
their outcome.

## Missing-data startup screen

The installed older GL startup NRO produced `evidence/startup-crash/crashlog.txt`:
filesystem startup found zero files in PK3 archives under
`sdmc:/switch/elite-force-switch/baseEF` and entered the engine's missing-data
fatal path. The trace reached `Com_Init` but does not establish whether files
were absent, misplaced, unreadable, invalid, or why the reported crash
presentation occurred. The engine's fatal path writes its console log through
`Sys_ErrorDialog`; it is not the separate `Sys_Dialog` stub.

The current entry point performs a shallow check for readable regular files
`pak0.pk3`, `pak1.pk3`, and `pak2.pk3` in that directory before engine init.
Those three correspond to the `FS_CheckPak0` bitmask gate in the pinned source;
the engine's message also requests patch 1.2 files, and passing this check does
not establish a complete or valid data set. If any check fails, the program
attempts to show each status on a libnx console, offers A to continue to the
engine (which evaluates its own search paths) and Plus to exit. This is a
usability boundary for the observed missing-data case, not a game-data importer,
archive validator, or fix for unavailable data. The new screen, continue and exit behavior
have not been tested on hardware. A host fixture checks missing, non-file,
synthetic-present and overlong paths; it does not validate PK3s.

The current preflight change has an incremental GL link in
`engine-preflight.TKTRkp9W` (log `nx-gl-preflight-nullguard.log`, ELF SHA-256
`d710150a3cef4b759948c934a26bc0e0f6ffbf7bd23fd880b43df8fc2cd4d3b0`). It
also moves the SP `FS_CheckPak0` pack member access after its existing null check;
forming a member address from a null directory search-path pointer is undefined
behavior in C. This source fix is not established as the cause of the observed
failure. The earlier advisory ELF (`708436657dc780c849040da667068f4cf526193a4109ed9768739630c1fc85dc`)
was superseded in that build tree. The current ELF has been packaged as noted
below; no hardware test of it is claimed. The earlier installed NRO lacks this screen.

## Advisory-screen package

The incremental advisory/null-guard ELF above was packaged with
`./bootstrap/package.sh bootstrap/build/engine-preflight.TKTRkp9W/build/Release/voyagersp.elf`.
The resulting `bootstrap/build/package.UuVgxGe9/elite-force-engine.nro` has
SHA-256 `26073d1088b53ae542f82aec7b56eab492a3f23f56110ed2cdbdb77aadb8b771`;
its copied `engine.elf` has SHA-256
`d710150a3cef4b759948c934a26bc0e0f6ffbf7bd23fd880b43df8fc2cd4d3b0`.
This package has not been launched on Switch.

For a selected hardware test, keep this artifact distinct from the older GL
NRO. Before each run, preserve and rename any previous `engine-bootstrap.log`
and `crashlog.txt` so stale evidence cannot be attributed to the new run. With
the data directory unavailable, launch it from the homebrew menu and
record whether the advisory lists the three file statuses and whether Plus
returns to the menu. If testing A separately, record that it proceeds to the
engine, which may still report its own missing-data fatal error. Preserve the
new `engine-bootstrap.log` and any `crashlog.txt` separately for each run,
along with the package hash and screen/exit observations. The trace is overwritten
on each launch, and exiting with Plus does not itself create a crash log. A passing presence check does not validate PK3
contents, retail ownership, complete patch data, or gameplay. The existing
logs establish a missing-data fatal path, not that the separate null-member
source fix caused or resolved the observed crash presentation.

## Experimental packaging and startup test

Package a specific previously linked ELF with the pinned devkitPro image:

```sh
./bootstrap/package.sh bootstrap/build/package.H0JN5e6f/engine.elf
```

The script creates a fresh package directory and prints both hashes. For the
fresh-source GL ELF (`2c6e27091e401680a646aca051bd2262810090cf7037227ad394e6fb4c54a5b0`),
the NRO at `bootstrap/build/package.H0JN5e6f/elite-force-engine.nro` has
SHA-256 `ee47caa12c652abb3f935dcf21688e41d5c70abb1e093a2090c3d8b3d8d6ca5d`.
The older Vulkan NRO has SHA-256
`2875aa7515e226a0107d090040e68aa68f5351bc6bb82f6fa3853f346af2f242`.
This is an `elf2nro` conversion, not evidence of successful launch. Rebuilds
may produce different hashes; use the printed directory and hashes to identify
the exact artifact tested. No retail data is included.

For an authorized hardware startup test:

1. Copy that NRO to `switch/elite-force-switch/` on the SD card. Place your own
   retail and patch data in `switch/elite-force-switch/baseEF/`; see the
   [first-light diagnostic](../first-light/README.md) for its limited file check.
   The engine's data and ownership requirements have not been validated here.
2. Preserve and rename any previous `engine-bootstrap.log` in that directory so
   it cannot be mistaken for a new run. Launch the NRO from the homebrew menu.
   Observe the screen and any error or return to the menu; there is no proven
   on-screen diagnostic or exit control for this experimental engine.
3. After the run, save `engine-bootstrap.log` if present and any engine log
   created under the data directory, along with the NRO hash and observations.
   The trace attempts to record entry, entry to `Com_Init`, and its return. A
   missing log is inconclusive because opening the trace file can fail; the last
   line only identifies the last successfully flushed phase, not a root cause.

Do not infer menu, gameplay, renderer, cinematics, or module reload success from
packaging or from reaching a startup trace. The unresolved lifecycle and
renderer restrictions above still apply.

## UI lifecycle boundary

The source makes a reset necessary: `sp_ui_bridge.cpp:231-244` documents an
unload/reload around renderer teardown and stale cached handles. In
`efgame/src/ui/ui_atoms.cpp:1366-1411`, `UI_Shutdown` is empty, while `UI_Init`
sets up imports, data and `Menu_Cache`; the latter registers renderer handles
in `ui_qmenu.cpp:3061`. Merely calling shutdown and init again does not establish
fresh module globals. `CL_InitUI` falls back to the Holomatch VM if SPUI_Load
fails, so a rejected reload does not itself prove a safe engine outcome.

A real static solution needs a reviewed way to restore *all* UI-owned writable
module state to its initialized state, isolate it from engine/game state, and
handle resources and any C++ initialization safely. It must be tested against
actual renderer teardown and reload; the current one-load adapter does none of
that and must not be treated as the solution. Its reload refusal is a temporary
build-stage boundary only.

To run the parser checks on a host with a C compiler and the pinned reference:

```sh
python3 bootstrap/test_patch_shader_parser.py
cc -std=gnu11 -O2 -ffunction-sections -fdata-sections -DARCH_STRING='"x86_64"' -Ireferences/VoyagerSP-Android/EFAndroid-SP/app/jni/efcode -Ibootstrap -c references/VoyagerSP-Android/EFAndroid-SP/app/jni/efcode/qcommon/q_shared.c -o bootstrap/build/host-q-shared.o
cc -std=gnu11 -O2 -ffunction-sections -fdata-sections -DARCH_STRING='"x86_64"' -Ireferences/VoyagerSP-Android/EFAndroid-SP/app/jni/efcode -Ibootstrap -Wl,--gc-sections bootstrap/test_renderer_const_parser.c bootstrap/build/host-q-shared.o -lm -o bootstrap/build/test-const-parser
bootstrap/build/test-const-parser
```

These commands use the local reference checkout; they do not verify its revision
or cleanliness. `bootstrap/build` must exist before the compiler commands.

## Switch controller defaults candidate

The owner reports the traced SP package reaches a responsive main menu and
campaign visuals, but gameplay controller inputs do not register. In the pinned
NX input, menu navigation has its own translation; gameplay buttons emit PAD0
keys and stick translation depends on their bindings. The inspected retail
`default.cfg` files contain no PAD0/JOY bindings, while the SP engine's desktop
gamepad defaults are gated on `__linux__`, which this Switch toolchain does not
define. This is a source-backed configuration gap; the actual device bindings,
input state and user commands are not yet observed.

The Switch build now installs the SP desktop PAD0 mapping once after user config
and autoexec, leaving existing nonempty bindings and cvar values intact. The
archived `in_switchDefaults` stamp prevents reapplying it on later startups.
On this first migration an empty binding is filled: this engine's saved
`unbindall` format cannot distinguish an intentionally unbound key from an
unspecified key. Mappings can be changed afterward. The helper creates sensible
analog scale defaults only when cvars do not already exist; it does not force
joystick enablement over an existing value. A host fixture checks the mapping,
nonempty preservation, and the one-time stamp; it does not emulate SDL or a
running game.

The candidate was incrementally built on the traced first-menu scratch tree
(log `bootstrap/build/gamepad-defaults-build.log`), then packaged as
`bootstrap/build/package.kBE83qxH/elite-force-engine.nro` (SHA-256
`f1ed7b5fb29ed8c3a4420e98c1ef68ef46d11a9870ead0a1876d6e018c90b50a`;
ELF `7a2c76cf29e8046a48557f6f5624af61ab06b18e08e3707812a8ebb04786e4f4`).
This candidate has not been independently reviewed or tested on hardware; it
is not proof of gameplay input. The previous working NRO remains in
`package.hT8iGv0R`.
