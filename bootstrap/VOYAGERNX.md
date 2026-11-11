# VoyagerNX integration assessment

Baseline: VoyagerNX `649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f`, SP
`c73750361cfc22c1afb3a2c160fa9c5df57214db`. The owner wants the existing
Switch port used for platform and build decisions, with adaptations focused on
single-player differences. Source observations below are not runtime evidence.

- `Makefile.nx` selects `sys_main_nx.c`, `sys_nx.c`, `sdl_input_nx.c`, SDL2,
  EGL, glapi and drm_nouveau, with GL1/GL2 renderer source lists. The current
  SP experiment already takes `sys_nx.c` from this revision (with documented SP
  path adaptations), and the build now selects adapted NX input, but retains a custom main and static
  SP Vulkan renderer. The previously packaged NRO predates the input change
  and does not test the NX graphics/input path.
- NX's `sys_main_nx.c:676` performs platform and time setup, path setup,
  `CON_Init`, `Com_Init`, network init and the applet loop. Its `Com_Init`
  returns `qboolean` (`code/qcommon/qcommon.h:1013`); the SP version returns
  `void` (`efcode/qcommon/qcommon.h:1025`). A direct main replacement cannot
  preserve NX's return-value branch without an SP-specific decision. SP's own
  desktop main calls `Com_Init` followed by `NET_Init`.
- NX's `sdl_input_nx.c` implements controller/menu events, Switch software
  keyboard and motion sensors. A syntax-only compile of the pinned file against
  the SP headers and pinned Switch toolchain succeeded; that does not verify
  linking or behavior. SP `client/cl_keys.c` calls `IN_Rumble`, declared in
  `client/client.h` and implemented in SP `sdl_input.c`; NX input has no such
  definition. NX also lacks SP's `IN_SyncMousePosition`: the first incremental link
  failed on that symbol. The current adapter copies SP cursor sync and absolute
  motion conversion and adapts the mouse-mode transition and visibility; the
  event loop, controller interaction and hardware behavior remain unverified.
  NX menu mapping also differs from SP's `IN_GamepadMenuKey`, so
  an input replacement needs an explicit rumble bridge and a review of menu,
  keyboard, state-release and gamepad behavior. SP damage rumble is also in its
  input implementation. A whole build was started and stopped before completion
  after identifying this difference; no resulting link is claimed.
- NX `renderercommon/tr_public.h` declares API version 8. SP's version is 9
  with `USE_FLEXIBLE_DISPLAY` (8 otherwise); `USE_VULKAN` separately adds
  Vulkan imports including `VKimp_Init`. The GL build uses SP headers and
  flexible-display version 9, not NX's unmodified version-8 interface.
  NX's `sdl_glimp.c` provides the OpenGL path. Matching an API number alone
  would not prove structure, renderer feature or data compatibility. Inventory
  the SP renderer imports, exports and features before deciding how to connect
  NX's graphics stack; do not assume an unmodified renderer is interchangeable.
- NX's own README documents sleep-mode crashes and a controller softlock in
  Solo Match; its platform is a useful baseline, not proof all lifecycle paths
  are solved. Keep SP module reload, cinematics and symbol isolation open.

## Hardware test recommendation

Hold the already transferred SP bootstrap NRO as an exploratory artifact while
preparing a reviewed NX-based integration artifact; it cannot establish NX
renderer or input behavior. If there is already an identified, installed
VoyagerNX multiplayer release, a separate baseline launch using its documented
HBMenu application launch and the owner's own Holomatch `baseEF` can record the
release hash/version, whether its menu appears, and controller response. That
only tests that release and multiplayer platform path, not this SP build. Do not
request a new owner hardware run until the coordinator selects an artifact and
test; there is currently no reviewed NX-based SP NRO to launch.

Next integration work: verify the adapted NX input, preserve needed SP input
behavior, and complete a full link and independent review. In parallel compare the GL renderer API and
SP-required rendering features before choosing a viable backend. Avoid treating
syntax compilation or successful linking as hardware validation.
