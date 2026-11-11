# Static SP UI reload blocker

This assessment is for pinned SP revision
`c73750361cfc22c1afb3a2c160fa9c5df57214db` and the current static-loader
adapter. It is a source and host-fixture assessment, not Switch runtime evidence.

`Com_Init` calls `CL_StartHunkUsers(qfalse)`, which sets `cls.uiStarted` and
calls `CL_InitUI`. With `sp_ui` enabled, `CL_InitUI` tries `SPUI_Load` first.
`CL_FlushMemory` later calls `CL_ClearMemory`, whose `CL_ShutdownAll` calls
`CL_ShutdownUI` before renderer shutdown; it clears `uiStarted` and shuts down
the active SP UI. The flush then calls `CL_StartHunkUsers` again. The SP
Route-b `SP_ReinitUI` path can also call `CL_InitUI` after a shutdown. These
are source paths, not a claim that every device launch has reached them.

The original bridge closes the dynamic UI module after `UI_Shutdown` so the
next load gets freshly initialized module state. The pinned `UI_Shutdown` is
empty. Its `UI_Init` registers renderer resources through `Menu_Cache`; other
menus use lazy `initialized` flags, for example `s_newgame_menu.initialized`
in `ui_game.cpp` and `s_menuframe.initialized` in `ui_atoms.cpp`. The bridge
comments document stale shader handles across renderer teardown. Calling
`UI_Init` again without restoring module state can retain those flags and
handles, even though `Menu_Cache` itself runs again.

The Switch adapter only marks the module inactive at close and refuses a
second load. Importantly, `CL_InitUI` treats failed `SPUI_Load` as a reason to
try the Holomatch `ui` VM; it does not guarantee a safe failure or an SP menu.
`python3 bootstrap/test_ui_reload_path.py` compiles the pinned actual
`CL_InitUI` and `CL_ShutdownUI` functions together with the real static-loader
header and stubbed UI/VM/engine services. It confirms first SP load, shutdown,
then static-load refusal and VM fallback. The test does not run actual UI
initialization, renderer teardown, real VM loading, resources, or hardware.
`bootstrap/test_static_loader.cpp` separately tests loader handle/name behavior.

A targeted resource audit found three concrete early-return leaks: oversized
`UI_LoadFonts` and `UI_LoadGenericMenu` inputs, and empty/oversized
`UI_ParseAnimationFile` inputs can leave a successfully opened engine file
handle unclosed. `patch_ui_file_cleanup.py` initializes those handles and
closes them on the relevant early returns. `test_ui_file_cleanup.py` compiles
the patched pinned font/menu functions and the animation early-return prefix
with stub filesystem services and checks both failure and selected normal
paths. This does not cover every UI resource, asynchronous callback, nonlocal
error or full reload. An incremental archive and engine link succeeded in
`ui-cleanup-build.CzeYNGlU`; log `bootstrap/build/ui-cleanup-link.log`, ELF
SHA-256 `69f012e0d84f30694c6bd8180838f0d567949f45c75216c1c58d69497285ff11`.
That tree was cloned from the earlier mouse-transition experiment and does not
include all later startup/preflight fixes; it is not a release build or NRO.

The bridge also copied the `Sys_GetClipboardData` result without releasing it.
The pinned engine allocates a nonempty clipboard result with `Z_Malloc`, and its
own console paste path calls `Z_Free`. `patch_ui_clipboard.py` adds the matching
free after copying; a host fixture covers null, truncation and zero-length output
cases with stubbed ownership. The cloned incremental bridge/engine build linked
in `ui-clipboard-build.3U5f78Oc` (log `ui-clipboard-build.log`, ELF SHA-256
`cc7aea8894ec855c7b5669467469ae742fc2e048a86def19a947f6e58a4c0bae`). Like its
input tree, it predates later preflight fixes; it is not a release artifact. This
fix does not demonstrate that every external resource is balanced across UI
shutdown or that reload is safe.

A further audit found eight oversized UI-text branches that call a fatal error
after successful `FS_ReadFile` without releasing its buffer. The engine's
`FS_ReadFile` allocates hunk temporary memory and increments `fs_loadStack`;
`FS_FreeFile` decrements it. `patch_ui_readfile_cleanup.py` releases the buffer
before those existing fatal calls, without changing their severity. A host
fixture executes each patched branch with stubbed services and checks free
occurs before the error; it does not execute the real error machinery. The
incremental cloned GL link succeeded in `ui-readfile-build.IEBIeJZg`
(`ui-readfile-build.log`, ELF SHA-256
`38ceb5c4c35c2fab59679f7851c109d98ec0149f5fc063dd0383a08c0610ded0`); it also
predates the later preflight fixes. No actual data, UI reload or runtime was
exercised.

`audit_ui_sections.py` inventories writable allocated, TLS and init/fini
sections from an archive using the pinned toolchain's `readelf`. For the
older `engine.El40Oylv/efui-isolated.a`, it reported 599 section records:
443 `.bss`, 145 other `.data`, and 11 `.data.rel.ro` records, including
zero-sized sections. The inventory is in `bootstrap/build/ui-sections.tsv`;
it is not a complete ownership or resource proof. A scratch linker experiment
using a copy of the pinned Switch linker script grouped that archive's selected
`.data` and `.bss` inputs inside the existing output sections
(`ui-layout.XMk7gzqS/ui-layout2.map`), while keeping `.data.rel.ro` separate.
This is layout feasibility only: it does not establish startup initialization,
constructor/destructor, relocation, actual module reset, or runtime safety.
The earlier variant placed UI BSS outside the normal `.bss` bounds and was not
used. No snapshot or reload behavior from either experiment is enabled.

A safe replacement requires evidence for all UI-owned writable state and
external resources: reset to the initial post-load state after shutdown,
re-register media after renderer teardown, and avoid resetting shared engine or
game state. The current archive transformation renames selected UI/game symbol
collisions; it has not established complete state ownership or final bindings.
A local inspection of the old unrenamed `libefui.a` found 553 defined writable
symbol records (`nm -A -C --defined-only`, types B/b/D/d); that count includes
local and global records and is not a complete state or resource inventory.
Resetting only the obvious flags, blindly copying arbitrary sections, or merely
allowing a second `dlopen` is not justified by this evidence. Constructor,
destructor, allocation, open-handle, callback, and renderer-resource behavior
also need an explicit audit before a snapshot/reset can be accepted.

## Experimental reset primitives

`ui_state_snapshot.h` provides a bounded byte snapshot of separate initialized
data and BSS ranges. It refuses invalid or overlapping ranges and restores only
when its caller asserts both quiescence and resource release. The separate
`ui_lifecycle_guard.h` can track nested entries, file handles, and buffers;
unknown, duplicate, overflow, or unmatched operations poison the guard. Neither
header discovers ownership, observes every callback, frees engine resources, or
proves the caller's assertions. Both require zero-initialized state and are not
thread-safe. Capture rejects overlap between the snapshot control object, its
allocated image and either reset range. Restore checks that the caller-supplied
lifecycle guard storage is disjoint from those ranges and snapshot storage; the
caller must pass the actual controlling guard and keep all other live control
storage outside those ranges. The experimental
loader rejects recursive reset-hook entry and poisons later attempts; hook
failure must leave UI state unmodified. A nonlocal exit that bypasses a leave
must prevent reset rather than be silently cleared.

The static-loader header has an opt-in `SWITCH_UI_SNAPSHOT_EXPERIMENT` hook.
The production build does not define it and provides no live hook
implementation. The default behavior therefore still refuses reload and can
fall back to the VM. The host-only `test_ui_snapshot_loader.cpp` supplies a
synthetic hook and proves that the real adapter refuses reset with a simulated
active callback or outstanding buffer, then restores synthetic state only after
both clear. Other host fixtures exercise bounds and a synthetic archive; none
loads the actual SP UI or validates real resource cleanup.

`probe_ui_state_layout.sh` relinks a copied, caller-selected prepared engine
using a generated copy of the pinned Switch linker script. For the older
`engine.El40Oylv` input, `ui-state-layout.bkqshbaE` linked an ELF with UI data
and BSS ranges of 138848 and 1162304 bytes inside the normal `.data` and `.bss`
outputs. Its UI BSS start matches the normal `__bss_start__`; relocated
`.data.rel.ro` remains outside the writable snapshot range. The map and ELF
are a layout experiment only: archive provenance, all live state, TLS,
constructors, engine-owned resources, real reentrancy and renderer teardown
remain unaudited. An earlier host attempt that placed a separate data section
before `.data` put it in RELRO and faulted; the accepted synthetic host fixture
instead brackets the archive inside the normal data and BSS outputs.

Until actual bridge callbacks and every relevant external resource are audited
and wired into a reviewed reset, the one-load restriction is a build-stage
boundary, not a safe or playable reload implementation. No device artifact in
this repository enables the experimental hook.

A separate, manually applied `SWITCH_UI_TRACK_EXPERIMENT` bridge patch tracks
entry and exit around the pinned SP UI exports and records file handles and
`FS_ReadFile` buffers passed through the UI imports. It is instrumentation
only: it is not wired to the snapshot hook or enabled by the normal build.
Tracking is bounded and fails closed on bookkeeping errors; it is not
thread-safe. Explicit enter/leave avoids relying on a C++ destructor for a
nonlocal exit, which leaves the entry outstanding in the host fixture; this
does not establish that nonlocal exits through other C++ frames are valid.
Renderer resources, commands, cvars, other allocations, concurrency, and the
actual UI lifecycle remain unaudited. The tracker does not prove cleanup or
that its control storage is outside every prospective reset range.

The patched scratch clone `ui-track-build.PLLhQP0q` linked with the tracking
flag and without the snapshot flag (log `ui-track-macro.log`); its ELF SHA-256
is `c3d6efca6216bbd9023310e35c70595f5a404dba1968907f8df18ab6fcad01ad`.
This incremental experimental build is not hardware or gameplay evidence.
Host fixtures cover nested entries, a synthetic nonlocal exit, resource
bookkeeping, and pinned source patching; they do not exercise the real UI.

Further source audit of the prepared `ui-readfile-build.IEBIeJZg` tree:
`efgame/src/ui/ui_atoms.cpp` calls `Menu_Cache` from `UI_Init`, creates
engine cvars through `Cvar_Create`, and defines an empty `UI_Shutdown`.
`ui_qmenu.cpp:Menu_Cache` stores registered shader and sound handles in UI
state. The bridge forwards registration through `sp_integration.c` to the
renderer and sound system. Thus clearing UI state alone does not establish
what happens to those engine resources or whether their handles remain valid;
registration reuse and renderer/sound restart ordering still need inspection.
The bridge also exposes `Cmd_ExecuteText`: in the prepared engine's
`efcode/qcommon/cmd.c`, append/insert copy command bytes into the engine
command buffer, while immediate execution calls `Cmd_ExecuteString` (or drains
the buffer). Copying text avoids retaining that particular input pointer but
does not prove queued commands have finished or cannot reenter UI. Existing
filesystem tracking measures none of these effects. These are source findings,
not a complete ownership audit or a runtime observation.

## First-menu diagnostic candidate

Owner testing of the earlier advisory package reached `Com_Init` and showed a
key prompt described as multiplayer. That observation does not establish why
SP UI was not shown. `CL_InitUI` defaults `sp_ui` to 1 but can select the
Holomatch VM if it is disabled or `SPUI_Load` fails; the one-load static
adapter can reject a later UI load. The pinned SP bridge describes a boot-logo
renderer teardown and reload, but the actual device sequence is unknown.

A manually patched clone of `engine-preflight.TKTRkp9W`,
`first-menu.tQN54jcZ`, omits only automatic startup logo scheduling on Switch
and adds bounded fixed-label UI routing events. Explicit cinematics remain
available; this does not implement UI reload. To reproduce these particular
patches on that copied prepared tree, apply `patch_switch_startup_logo.py` to
`efcode/qcommon/common.c` and `patch_ui_route_trace.py` to `efcode/client/cl_ui.c`
and `sp/sp_ui_bridge.cpp`, then compile `bootstrap/switch_main.c` with
`SWITCH_UI_ROUTE_TRACE` defined. The normal builders do not apply these
experimental patches. The trace appends at most 64 fixed labels per run to
`sdmc:/switch/elite-force-switch/ui-route.log`; each run begins with `run:
begin`, and no key or config values are logged. Preserve any previous log
before testing; storage failures can leave it absent or incomplete.

The incremental link log is `bootstrap/build/first-menu-trace-build.log` and
ELF SHA-256 is `214286d34d79acdcb31054debc89ac0cb6b4b6d031b0a09c1c3deb58022d7ff9`.
Package `bootstrap/build/package.hT8iGv0R/elite-force-engine.nro` has SHA-256
`53ab39ab8ca895996135f2c35f145ad0a51804b6f1680bffa009e99d4365102f`.
This candidate has not been run on hardware and must be independently reviewed
before selecting a device test. It does not establish campaign or reload
behavior; archives and configuration must be preserved.

The `first-menu.tQN54jcZ` scratch tree was subsequently modified and rebuilt for
the controller-defaults candidate, so it no longer preserves the first-menu
source/object state described above. The previously packaged NRO and copied ELF
in `package.hT8iGv0R` remain intact at the hashes above.
