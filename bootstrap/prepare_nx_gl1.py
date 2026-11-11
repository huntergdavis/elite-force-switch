#!/usr/bin/env python3
"""Select NX GL1 in an already-prepared disposable SP engine tree."""
from pathlib import Path
import sys

work = Path(sys.argv[1])
cmake = work / 'EFAndroid-SP/app/jni/src/CMakeLists.txt'
s = cmake.read_text()
changes = {
    'set(EF_USE_VULKAN TRUE)': 'set(EF_USE_VULKAN FALSE)',
    '  /work/switch_main.c': '  /work/switch_main.c\n  /work/nx_gl1_compat.c',
    '${EF}/sdl/sdl_gamma.c ${EF}/sdl/sdl_glimp.c':
        '${EF}/sdl/sdl_gamma.c ${EF}/sdl/sdl_glimp_nx.c',
    'list(APPEND EF_TARGET_SRC ${RENDERER_VK_SRC} ${RENDERCOMMON_SRC})':
        'file(GLOB NX_GL1_SRC ${EF}/renderergl1/*.c)\n  list(REMOVE_ITEM NX_GL1_SRC ${EF}/renderergl1/tr_subs.c)\n  list(APPEND EF_TARGET_SRC ${NX_GL1_SRC} ${RENDERCOMMON_SRC})',
    'target_link_libraries(voyagersp PRIVATE nx)':
        'target_link_libraries(voyagersp PRIVATE EGL glapi drm_nouveau glad nx)',
}
for old, new in changes.items():
    if s.count(old) != 1:
        raise SystemExit(f'unexpected CMake fragment: {old}')
    s = s.replace(old, new)
cmake.write_text(s)
root = work / 'EFAndroid-SP/app/jni/efcode/renderergl1'
header = root / 'tr_local.h'
if header.read_text().count('color4ub_t') != 4:
    raise SystemExit('unexpected NX renderer color type')
for path in [header, *root.glob('*.c')]:
    text = path.read_text()
    path.write_text(text.replace('color4ub_t', 'nx_color4ub_t'))
# Reuse the GL1 screenshot readback immediately before buffer swap.
init = root / 'tr_init.c'
text = init.read_text()
marker = 'void RE_Shutdown( qboolean destroyWindow ) {'
# Upstream includes a trailing tab after the brace; the prefix remains unique.
if text.count(marker) != 1:
    raise SystemExit('unexpected GL1 shutdown')
text = text.replace(marker, marker + '\n\tNX_ResetSaveThumb();')
marker = 'void RE_Shutdown( qboolean destroyWindow )'
text = text.replace(marker, '#include "/work/nx_gl1_thumbnail.inc"\n\n' + marker, 1)
marker = '\tre.EndFrame = RE_EndFrame;'
if text.count(marker) != 1:
    raise SystemExit('unexpected GL1 export table')
text = text.replace(marker, marker + '\n\tre.RequestSaveThumb = NX_RequestSaveThumb;\n\tre.GetSaveThumb = NX_GetSaveThumb;')
init.write_text(text)
backend = root / 'tr_backend.c'
text = backend.read_text()
marker = '\tGLimp_EndFrame();'
if text.count(marker) != 1:
    raise SystemExit('unexpected GL1 buffer swap')
text = text.replace(marker, '\tNX_CaptureSaveThumb();\n' + marker)
backend.write_text(text)
header = root / 'tr_local.h'
text = header.read_text()
marker = '#include "../qcommon/q_shared.h"'
if text.count(marker) != 1:
    raise SystemExit('unexpected GL1 header')
text = text.replace(marker, marker + '\nvoid NX_CaptureSaveThumb(void);')
header.write_text(text)
client = work / 'EFAndroid-SP/app/jni/efcode/client/cl_main.c'
s = client.read_text()
for old, new in [('Cvar_Get( "cl_rendererModules", "vulkan", CVAR_ROM );', 'Cvar_Get( "cl_rendererModules", "opengl1", CVAR_ROM );'),
                 ('Cvar_Get( "cl_rendererLoaded", "vulkan", CVAR_ROM );', 'Cvar_Get( "cl_rendererLoaded", "opengl1", CVAR_ROM );'),
                 ('Cvar_Get( "cl_renderer", "vulkan", CVAR_ARCHIVE );', 'Cvar_Get( "cl_renderer", "opengl1", CVAR_ARCHIVE );')]:
    if s.count(old) != 1:
        raise SystemExit('unexpected static renderer label')
    s = s.replace(old, new)
# VoyagerNX GL1 does not reference the SP renderer-thread imports.
# Set them to NULL rather than pretending that a threading implementation exists.
for name in ('GLimp_SpawnRenderThread', 'GLimp_RendererSleep', 'GLimp_FrontEndSleep',
             'GLimp_WakeRenderer', 'GLimp_ShutdownRenderThread'):
    old = f'ri.{name} = {name};'
    if s.count(old) != 1:
        raise SystemExit(f'unexpected renderer thread import: {name}')
    s = s.replace(old, f'ri.{name} = NULL;')
client.write_text(s)
