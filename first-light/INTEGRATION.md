# Integration decision and next experiments

The candidate campaign base is VoyagerSP-Android, retaining its SP engine and
bridges while adapting the platform to Switch. This is a working hypothesis,
not an established build strategy: VoyagerNX supplies a Switch platform and GL
reference, but its stated target is Holomatch and its README says the Elite
Force game, cgame and UI source is absent (`references/VoyagerNX/README.md`).
VoyagerSP includes the SP modules, but only its Vulkan renderer is supported
(`references/VoyagerSP-Android/README.md:20-22`); neither source establishes a
working Switch campaign. Mac is another SP reference, not hardware evidence.

Renderer choice remains open. VoyagerNX selects its GL1 sources and links EGL
and graphics libraries (`references/VoyagerNX/Makefile.nx:255,320`), while SP
uses a modified renderer interface and Vulkan. Compare the actual import/export
structures and dependencies before attempting a GL transplant; do not assume
matching names imply ABI compatibility. A Vulkan route also needs a demonstrated
Switch graphics stack and working surface support. The console diagnostic makes
no renderer decision.

Module lifecycle is a critical risk. SP loads its game and UI via `dlopen` and
explicitly unloads them to reset module globals on map and UI reloads
(`references/VoyagerSP-Android/EFAndroid-SP/app/jni/sp/sp_bridge.cpp:530`,
`sp_ui_bridge.cpp:216`). Static linkage cannot simply replace the loader calls:
it needs a tested equivalent reset or supported reload mechanism, plus proof
that symbol and ABI boundaries work. No Switch module-loading capability is
claimed by this diagnostic.

The immediate hardware milestone is the accompanying NRO launching, showing
missing and present-file results, and producing a readable log. The next engine
experiment should compile a small SP module lifecycle probe and check repeated
initialization before integrating it into the engine; in parallel, compare the
renderer interfaces and demonstrate a graphics path. Retail data detection in
this NRO checks names only; upstream documents four PK3s and an ownership-check
DLL (`references/VoyagerSP-Android/README.md:48-51`).
