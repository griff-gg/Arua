import os

from arua_companion.unblock import unblock_tree


def _mark(p):
    with open(str(p) + ':Zone.Identifier', 'w') as f:
        f.write('[ZoneTransfer]\nZoneId=3\n')


def _marked(p):
    return os.path.exists(str(p) + ':Zone.Identifier')


def test_unblock_removes_download_mark(tmp_path):
    sub = tmp_path / '_internal' / 'pythonnet'
    sub.mkdir(parents=True)
    dll, exe, plain = sub / 'Python.Runtime.dll', tmp_path / 'app.exe', tmp_path / 'items.json'
    for p in (dll, exe, plain):
        p.write_bytes(b'x')
    _mark(dll)
    _mark(exe)
    assert _marked(dll) and _marked(exe)

    assert unblock_tree(tmp_path) == 2
    assert not _marked(dll) and not _marked(exe) and not _marked(plain)
    assert dll.read_bytes() == b'x'


def test_unblock_missing_folder_is_harmless(tmp_path):
    assert unblock_tree(tmp_path / 'nope') == 0
