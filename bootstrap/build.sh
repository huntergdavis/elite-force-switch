#!/bin/sh
set -eu
renderer=${1:-vulkan}
if [ "$#" -gt 1 ] || { [ "$renderer" != vulkan ] && [ "$renderer" != nx-gl1 ]; }; then
  echo "usage: $0 [vulkan|nx-gl1]" >&2
  exit 2
fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_dir="$root/references/VoyagerSP-Android"
revision=c73750361cfc22c1afb3a2c160fa9c5df57214db
mkdir -p "$root/bootstrap/build"
work=$(mktemp -d "$root/bootstrap/build/engine.XXXXXXXX")
echo "Engine bootstrap experiment directory: $work"
git -C "$source_dir" archive --output="$work/source.tar" "$revision"
tar -xf "$work/source.tar" -C "$work"
git -C "$root/references/VoyagerNX" show 649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f:code/sys/sys_nx.c > "$work/EFAndroid-SP/app/jni/efcode/sys/sys_nx.c"
git -C "$root/references/VoyagerNX" show 649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f:code/sdl/sdl_input_nx.c > "$work/EFAndroid-SP/app/jni/efcode/sdl/sdl_input_nx.c"
python3 "$root/bootstrap/patch_nx_input.py" "$work/EFAndroid-SP/app/jni/efcode/sdl/sdl_input_nx.c" "$work/EFAndroid-SP/app/jni/efcode/sdl/sdl_input.c"
# The owner-tested 0.1 build enabled the bounded UI route trace.  Its
# implementation is guarded in switch_main.c and is required by the trace
# hooks applied below.
{ printf '#define SWITCH_UI_ROUTE_TRACE 1\n'; cat "$root/bootstrap/switch_main.c"; } > "$work/switch_main.c"
cp "$root/bootstrap/game_data_preflight.c" "$root/bootstrap/game_data_preflight.h" "$work/"
cp "$root/bootstrap/renderer_cvar_adapter.c" "$work/renderer_cvar_adapter.c"
cp "$root/bootstrap/switch_platform.c" "$work/switch_platform.c"
cp "$root/bootstrap/renderer_export_adapters.inc" "$work/renderer_export_adapters.inc"
cp "$root/bootstrap/renderer_const_parser.h" "$work/renderer_const_parser.h"
cp "$root/bootstrap/switch_static_loader.h" "$work/switch_static_loader.h"
cp "$root/bootstrap/isolate_ui_archive.py" "$work/isolate_ui_archive.py"
cp "$root/bootstrap/isolate_game_archive.py" "$work/isolate_game_archive.py"
python3 - "$work/EFAndroid-SP/app/jni/src/CMakeLists.txt" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
old = '${EF}/sdl/sdl_input.c ${EF}/sdl/sdl_snd.c'
if s.count(old) != 1: raise SystemExit('unexpected SDL input source')
s = s.replace(old, '${EF}/sdl/sdl_input_nx.c ${EF}/sdl/sdl_snd.c')
old = 'set(SYS_MAIN ${EF}/sys/sys_main.c)'
new = old + '\nset_source_files_properties(${SYS_MAIN} PROPERTIES COMPILE_DEFINITIONS "main=SP_DesktopMain")'
if s.count(old) != 1: raise SystemExit('unexpected upstream SYS_MAIN')
s = s.replace(old, new)
old = '${EF}/sys/sys_unix.c'
if s.count(old) != 1: raise SystemExit('unexpected upstream system source')
s = s.replace(old, '${EF}/sys/sys_nx.c')
old = 'set(EF_ARCH_STRING "x86_64")'
if s.count(old) != 1: raise SystemExit('unexpected upstream architecture setting')
s = s.replace(old, 'set(EF_ARCH_STRING "arm64")')
old = 'target_include_directories(sp_game_bridge PRIVATE\n'
if s.count(old) != 1: raise SystemExit('unexpected bridge include configuration')
s = s.replace(old, old + '  /work\n')
old = '    dl m pthread)'
if s.count(old) != 1: raise SystemExit('unexpected desktop library list')
s = s.replace(old, '    m pthread)')
old = 'set(EF_TARGET_SRC\n'
new = old + '  /work/switch_main.c\n  /work/game_data_preflight.c\n  /work/renderer_cvar_adapter.c\n  /work/switch_platform.c\n'
if s.count(old) != 1: raise SystemExit('unexpected upstream EF_TARGET_SRC')
s = s.replace(old, new)
old = '  add_executable(voyagersp ${EF_TARGET_SRC})'
new = old + '\n  target_link_libraries(voyagersp PRIVATE nx)'
if s.count(old) != 1: raise SystemExit('unexpected upstream target')
s = s.replace(old, new)
marker = '# ---------------------------------------------------------------------------\n# Renderer modules'
if s.count(marker) != 1: raise SystemExit('unexpected renderer modules marker')
linkage = '''add_custom_command(OUTPUT /work/efui-isolated.a
  COMMAND python3 /work/isolate_ui_archive.py $<TARGET_FILE:efgame> $<TARGET_FILE:efui> /work/efui-isolated.a
  DEPENDS efgame efui /work/isolate_ui_archive.py VERBATIM)
add_custom_target(switch_ui_isolation DEPENDS /work/efui-isolated.a)
add_library(switch_ui STATIC IMPORTED GLOBAL)
set_target_properties(switch_ui PROPERTIES IMPORTED_LOCATION /work/efui-isolated.a)
add_dependencies(voyagersp switch_ui_isolation)
target_link_libraries(voyagersp PRIVATE efgame switch_ui)

'''
p.write_text(s.replace(marker, linkage + marker, 1))
platform = p.parent.parent / 'efcode/qcommon/q_platform.h'
t = platform.read_text()
marker = '//catch missing defines in above blocks'
if t.count(marker) != 1: raise SystemExit('unexpected upstream platform checks')
block = '''#ifdef __SWITCH__
#define OS_STRING "switch"
#define ID_INLINE inline
#define PATH_SEP '/'
#define Q3_LITTLE_ENDIAN
#define DLL_EXT ".so"
#endif

'''
platform.write_text(t.replace(marker, block + marker))
client = p.parent.parent / 'efcode/client/cl_main.c'
t = client.read_text()
marker = 'void CL_InitRef( void ) {'
assignment = 'ri.Cvar_VariableString = Cvar_VariableString;'
if t.count(marker) != 1 or t.count(assignment) != 1:
    raise SystemExit('unexpected renderer cvar import site')
t = t.replace(marker, 'extern const char *Switch_RendererCvarString(const char *name);\n\n' + marker)
t = t.replace(assignment, 'ri.Cvar_VariableString = Switch_RendererCvarString;')
client.write_text(t)
network = p.parent.parent / 'efcode/qcommon/net_ip.c'
t = network.read_text()
old = '#\tif !defined(__sun) && !defined(__sgi)\n#\t\tinclude <ifaddrs.h>'
new = '#\tif !defined(__sun) && !defined(__sgi) && !defined(__SWITCH__)\n#\t\tinclude <ifaddrs.h>'
if t.count(old) != 1: raise SystemExit('unexpected network interface include')
network.write_text(t.replace(old, new))
switch_sys = p.parent.parent / 'efcode/sys/sys_nx.c'
t = switch_sys.read_text()
marker = 'static char homePath[ MAX_OSPATH ] = { 0 };'
if t.count(marker) != 1: raise SystemExit('unexpected Switch home path')
t = t.replace(marker, marker + '\n\nvoid Sys_SetDefaultHomePath(const char *path) {\n    Q_strncpyz(homePath, path ? path : "", sizeof(homePath));\n}')
unix_sys = p.parent.parent / 'efcode/sys/sys_unix.c'
import re
original = unix_sys.read_text()
for function in ('Sys_Basename', 'Sys_Dirname'):
    pattern = r'const char \*' + function + r'\(.*?\n\}'
    old = re.findall(pattern, t, flags=re.DOTALL)
    replacement = re.findall(pattern, original, flags=re.DOTALL)
    if len(old) != 1 or len(replacement) != 1:
        raise SystemExit(f'unexpected path function {function}')
    t = t.replace(old[0], replacement[0], 1)
switch_sys.write_text(t)
for bridge in ('sp_bridge.cpp', 'sp_ui_bridge.cpp'):
    path = p.parent.parent / 'sp' / bridge
    text = path.read_text()
    old = '#include <dlfcn.h>'
    if text.count(old) != 1: raise SystemExit(f'unexpected loader include in {bridge}')
    path.write_text(text.replace(old, '#include "switch_static_loader.h"'))
PY
# The 0.1 hardware-tested tree predates the optional clipboard and UI file
# cleanup patches. Keep the build aligned with that tested behavior.
python3 "$root/bootstrap/patch_ui_route_trace.py" "$work/EFAndroid-SP/app/jni/efcode/client/cl_ui.c" "$work/EFAndroid-SP/app/jni/sp/sp_ui_bridge.cpp"
python3 "$root/bootstrap/patch_game_link.py" "$work/EFAndroid-SP/app/jni/src/CMakeLists.txt"
python3 "$root/bootstrap/patch_ui_narrowing.py" "$work/efgame/src/ui"
cp "$root/bootstrap/switch_ui_media.h" "$work/EFAndroid-SP/app/jni/sp/"
python3 "$root/bootstrap/patch_switch_ui_lifetime.py" "$work/EFAndroid-SP/app/jni/sp/sp_ui_bridge.cpp" "$work/efgame/src/ui/ui_atoms.cpp"
python3 "$root/bootstrap/patch_fs_null_check.py" "$work/EFAndroid-SP/app/jni/efcode/qcommon/files.c"
python3 "$root/bootstrap/patch_switch_cdkey.py" "$work/EFAndroid-SP/app/jni/efcode/qcommon/common.c"
python3 "$root/bootstrap/patch_switch_startup_logo.py" "$work/EFAndroid-SP/app/jni/efcode/qcommon/common.c"
cp "$root/bootstrap/switch_gamepad_defaults.inc" "$work/EFAndroid-SP/app/jni/efcode/qcommon/"
python3 "$root/bootstrap/patch_switch_gamepad_defaults.py" "$work/EFAndroid-SP/app/jni/efcode/qcommon/common.c"
python3 "$root/bootstrap/patch_switch_multicast.py" "$work/EFAndroid-SP/app/jni/efcode/qcommon/net_ip.c"
python3 "$root/bootstrap/patch_switch_backtrace.py" "$work/EFAndroid-SP/app/jni/sp/sp_integration.c"
python3 "$root/bootstrap/patch_renderer_parser.py" "$work/EFAndroid-SP/app/jni/efcode/renderervk"
python3 "$root/bootstrap/patch_renderer_exports.py" "$work/EFAndroid-SP/app/jni/efcode/renderervk/tr_init.c"
python3 "$root/bootstrap/patch_shader_parser.py" "$work/EFAndroid-SP/app/jni/efcode/renderervk/tr_shader.c"
if [ "$renderer" = nx-gl1 ]; then
  git -C "$root/references/VoyagerNX" archive 649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f code/renderergl1 | tar -x -C "$work"
  mv "$work/code/renderergl1" "$work/EFAndroid-SP/app/jni/efcode/renderergl1"
  git -C "$root/references/VoyagerNX" show 649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f:code/sdl/sdl_glimp.c > "$work/EFAndroid-SP/app/jni/efcode/sdl/sdl_glimp_nx.c"
  cp "$root/bootstrap/nx_gl1_compat.c" "$work/nx_gl1_compat.c"
  cp "$root/bootstrap/nx_gl1_thumbnail.inc" "$work/nx_gl1_thumbnail.inc"
  python3 "$root/bootstrap/prepare_nx_gl1.py" "$work"
fi
image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
docker run --rm -u "$(id -u):$(id -g)" -v "$work:/work" "$image" \
  cmake -S /work/EFAndroid-SP/app/jni -B /work/build \
  -DCMAKE_TOOLCHAIN_FILE=/opt/devkitpro/cmake/Switch.cmake -DEF_PLATFORM=linux -DEF_STATIC_RENDERER=ON
docker run --rm -u "$(id -u):$(id -g)" -v "$work:/work" -w /work/build "$image" \
  make -f src/CMakeFiles/voyagersp.dir/build.make src/CMakeFiles/voyagersp.dir/work/switch_main.o
docker run --rm -u "$(id -u):$(id -g)" -v "$work:/work" "$image" \
  cmake --build /work/build --target voyagersp -j2
