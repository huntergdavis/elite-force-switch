# SP data requirements in this Switch experiment

Use your own legitimately obtained Elite Force retail and patch data. No game
data is supplied by this project. The default entry point sets both install and
home roots to `sdmc:/switch/elite-force-switch`; its advisory checks files in
`baseEF` under that root. The advisory can be bypassed with A and only checks
whether three names are readable regular files, not whether they are archives or
whether the engine can mount them.

The pinned SP engine's `FS_InitFilesystem` starts filesystem search and calls
`FS_CheckPak0` (`efcode/qcommon/files.c:4239`). For the non-standalone Elite
Force branch, that function's initial gate requires the bits for mounted
`baseEF` archives named `pak0`, `pak1`, and `pak2` (`foundPak & 0x07`); its
message also requests the 1.2 patch files. The search uses engine search paths
and case-insensitive basename comparisons, not just the advisory's literal
file tests. A checksum mismatch emits a warning in this function; these checks
are not proof of usable or complete game data. The next startup check requires
`default.cfg` to be nonempty and readable through the engine filesystem.
Requirements for all editions and later campaign content have not been validated.

The upstream desktop importer's documented intended retail set is
`pak0.pk3` through `pak3.pk3` plus `efgamex86.dll`
(`sp/data_import.h`, `sp/data_import.c`). Its file checks require each PK3 to
be at least 1024 bytes and the DLL to be at least 4096 bytes with an `MZ`
header; it treats the DLL as a token and does not load or execute it. These
checks do not independently prove ownership or archive validity. The custom
Switch `main` in this repository does **not** call `DataImport_PreInit`, so the
current Switch build neither performs that importer's token check nor
establishes that the DLL is a runtime requirement. Do not interpret that as a
license to use data you do not own.

An early missing-data diagnostic reached `Com_Init` but could not mount the
game archives. The later 0.1 candidate reached single-player gameplay with
the four files described below; this is not validation of every retail edition.

## Supplying game data on Switch

Provide your own original, legitimately obtained game files. Create
`sdmc:/switch/elite-force-switch/baseEF/` and place your own `pak0.pk3`,
`pak1.pk3`, `pak2.pk3`, and `pak3.pk3` there. Preserve your original files and
existing configuration; do not upload them, keys, or diagnostic logs to the
public source repository. The preflight checks readability of `pak0` through
`pak2` only, and the owner has reported reaching the SP campaign with these
four candidate archives. This does not establish that every retail edition or
patch combination is compatible, or that all content has been tested.
