import hashlib
import io
import json
import zipfile

import pytest

from arua_companion import updates as up

REL = 'https://github.com/griff-gg/Arua/releases/download/v0.3.0/'


def release_json(**over):
    data = {'tag_name': 'v0.3.0', 'html_url': 'https://github.com/griff-gg/Arua/releases/tag/v0.3.0',
            'assets': [{'name': 'Arua-0.3.0-Setup.exe', 'browser_download_url': REL + 'Arua-0.3.0-Setup.exe',
                        'size': 10, 'digest': 'sha256:' + 'a' * 64},
                       {'name': 'Arua-0.3.0-arua_ice.zip', 'browser_download_url': REL + 'Arua-0.3.0-arua_ice.zip',
                        'size': 5, 'digest': None}]}
    data.update(over)
    return json.dumps(data).encode()


def test_versions():
    assert up.parse_version('v0.2.1') == (0, 2, 1)
    assert up.parse_version('0.10.0') > up.parse_version('0.9.9')
    assert up.parse_version('nonsense') == ()
    assert up.is_newer('v0.3.0', '0.2.1') and not up.is_newer('v0.2.1', '0.2.1') and not up.is_newer('bad', '0.2.1')


def test_read_release_picks_setup_and_theme_zips():
    r = up.read_release(release_json())
    assert r.version == '0.3.0'
    assert r.setup.url == REL + 'Arua-0.3.0-Setup.exe' and r.setup.sha256 == 'a' * 64
    assert set(r.themes) == {'arua_ice'} and r.themes['arua_ice'].sha256 is None


def test_read_release_ignores_files_from_elsewhere():
    bad = json.loads(release_json())
    for a in bad['assets']:
        a['browser_download_url'] = 'https://evil.example/' + a['name']
    r = up.read_release(json.dumps(bad).encode())
    assert r is None or (r.setup is None and not r.themes)


def test_read_release_handles_garbage():
    assert up.read_release(b'not json') is None
    assert up.read_release(json.dumps({'tag_name': 'v1.0.0'}).encode()).setup is None


def test_download_checks_sha256(tmp_path):
    data = b'setup bytes'
    good = up.Asset('x.exe', REL + 'x.exe', len(data), hashlib.sha256(data).hexdigest())
    out = up.download(good, tmp_path / 'x.exe', fetch=lambda url: data)
    assert out.read_bytes() == data
    bad = up.Asset('y.exe', REL + 'y.exe', len(data), '0' * 64)
    with pytest.raises(up.UpdateError):
        up.download(bad, tmp_path / 'y.exe', fetch=lambda url: data)
    assert not (tmp_path / 'y.exe').exists()


def make_zip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, data in entries.items():
            z.writestr(name, data)
    return buf.getvalue()


def test_install_theme_zip_replaces_folder(tmp_path):
    themes = tmp_path / 'data' / 'ui' / 'themes'
    (themes / 'arua_ice').mkdir(parents=True)
    (themes / 'arua_ice' / 'stale.css').write_text('old')
    zp = tmp_path / 't.zip'
    zp.write_bytes(make_zip({'arua_ice/theme.toml': 'name = "Arua Ice"', 'arua_ice/styles/a.css': 'x'}))
    up.install_theme_zip(zp, tmp_path, 'arua_ice')
    assert (themes / 'arua_ice' / 'styles' / 'a.css').read_text() == 'x'
    assert not (themes / 'arua_ice' / 'stale.css').exists()
    assert sorted(p.name for p in themes.iterdir()) == ['arua_ice']


@pytest.mark.parametrize('entries', [
    {'arua_ice/theme.toml': 'x', 'arua_ice/../../evil.txt': 'x'},
    {'arua_ice/theme.toml': 'x', 'arua_dark/other.css': 'x'},
    {'arua_ice/styles/a.css': 'no theme.toml'},
])
def test_install_theme_zip_refuses_bad_zips_and_keeps_old(tmp_path, entries):
    themes = tmp_path / 'data' / 'ui' / 'themes'
    (themes / 'arua_ice').mkdir(parents=True)
    (themes / 'arua_ice' / 'theme.toml').write_text('old')
    zp = tmp_path / 't.zip'
    zp.write_bytes(make_zip(entries))
    with pytest.raises(up.UpdateError):
        up.install_theme_zip(zp, tmp_path, 'arua_ice')
    assert (themes / 'arua_ice' / 'theme.toml').read_text() == 'old'
    assert not (tmp_path / 'evil.txt').exists() and not (themes.parent / 'evil.txt').exists()
    assert sorted(p.name for p in themes.iterdir()) == ['arua_ice']


def test_remove_theme_only_known_arua_themes(tmp_path):
    themes = tmp_path / 'data' / 'ui' / 'themes'
    for n in ('arua_ice', 'rose'):
        (themes / n).mkdir(parents=True)
    up.remove_theme(tmp_path, 'arua_ice')
    assert not (themes / 'arua_ice').exists()
    with pytest.raises(up.UpdateError):
        up.remove_theme(tmp_path, 'rose')
    assert (themes / 'rose').exists()


def test_setup_args_keep_installed_themes(tmp_path):
    themes = tmp_path / 'data' / 'ui' / 'themes'
    for n in ('arua_ice', 'arua_midnight'):
        (themes / n).mkdir(parents=True)
        (themes / n / 'theme.toml').write_text('x')
    args = up.setup_args(tmp_path)
    assert '/SILENT' in args and '/RELAUNCH' in args
    assert f'/DIR={tmp_path}' in args
    assert '/COMPONENTS=companion,ice,midnight' in args
