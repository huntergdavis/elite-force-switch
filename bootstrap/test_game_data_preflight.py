#!/usr/bin/env python3
"""Exercise file-presence preflight with synthetic files in workspace scratch."""
import ctypes
import errno
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
scratch = root / 'build'
scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='data-preflight.', dir=scratch) as tmp:
    tmp = Path(tmp)
    lib = tmp / 'preflight.so'
    subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                    str(root / 'game_data_preflight.c'), '-o', str(lib)], check=True)
    check = ctypes.CDLL(str(lib)).GameData_Check
    check.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
    result = (ctypes.c_int * 3)()
    def run():
        check(str(tmp).encode(), result)
        return list(result)
    assert run() == [errno.ENOENT] * 3
    (tmp / 'pak0.pk3').write_bytes(b'')
    (tmp / 'pak1.pk3').mkdir()
    assert run() == [0, errno.EINVAL, errno.ENOENT]
    (tmp / 'pak1.pk3').rmdir()
    (tmp / 'pak1.pk3').write_bytes(b'')
    (tmp / 'pak2.pk3').write_bytes(b'')
    assert run() == [0, 0, 0]  # Presence only, these are not real archives.
    check(b'x' * 1024, result)
    assert list(result) == [errno.ENAMETOOLONG] * 3
print('missing, non-file, present and overlong paths checked; archives not validated')
