import json
from pathlib import Path

from arua_companion.app import Api
from arua_companion.updates import THEMES
from test_updates import REL, make_zip

DATA = Path(__file__).resolve().parents[1] / 'data' / 'items.json'


def fake_release(version='0.9.0', zips=None):
    assets = [{'name': f'Arua-{version}-Setup.exe', 'browser_download_url': REL + 'setup.exe', 'size': 5, 'digest': None}]
    for name, data in (zips or {}).items():
        assets.append({'name': f'Arua-{version}-{name}.zip', 'browser_download_url': REL + name + '.zip',
                       'size': len(data), 'digest': None})
    return json.dumps({'tag_name': 'v' + version, 'html_url': 'x', 'assets': assets}).encode()


def fetcher(release, files=None):
    def fetch(url):
        if 'api.github.com' in url:
            return release
        for name, data in (files or {}).items():
            if url.endswith(name + '.zip'):
                return data
        if url.endswith('setup.exe'):
            return b'12345'
        raise OSError('offline')
    return fetch


def make_api(game, version='0.2.1', fetch=None, running=False, launched=None):
    return Api(game, items_path=DATA, fetch=fetch or fetcher(fake_release()), version=version,
               game_running=lambda: running, launch=lambda exe, args: launched.append((exe, args)) if launched is not None else None)


def test_startup_applies_saved_settings_once_per_version(fake_game):
    (fake_game / 'arua_companion.json').write_text(json.dumps({'marker': 'blue'}), encoding='utf-8')
    api = make_api(fake_game)
    first = api.startup()
    assert first['applied'] is True
    css = (fake_game / 'data/ui/themes/arua_ice/styles/spritesheet_world_ui.css').read_text(encoding='utf-8')
    assert 'blue' in css.lower()
    assert (fake_game / 'arua_companion_version.txt').read_text().strip() == '0.2.1'
    assert make_api(fake_game).startup()['applied'] is False
    assert make_api(fake_game, version='0.3.0').startup()['applied'] is True


def test_startup_without_themes_does_nothing(tmp_path):
    assert make_api(tmp_path).startup()['applied'] is False


def test_theme_list_in_state(fake_game):
    st = make_api(fake_game).get_state()
    rows = {t['name']: t['installed'] for t in st['theme_list']}
    assert rows == {'arua_ice': True, 'arua_dark': True, 'arua_midnight': False}
    assert st['version'] == '0.2.1'


def test_check_update(fake_game):
    assert make_api(fake_game).check_update()['available'] is True
    same = make_api(fake_game, fetch=fetcher(fake_release('0.2.1')))
    assert same.check_update()['available'] is False
    offline = make_api(fake_game, fetch=fetcher(b'{}'))
    assert offline.check_update()['available'] is False


def test_install_theme_from_release_for_this_version(fake_game):
    z = make_zip({'arua_midnight/theme.toml': 'name = "Arua Midnight"',
                  'arua_midnight/styles/spritesheet_world_ui.css': 'old'})
    api = make_api(fake_game, fetch=fetcher(fake_release('0.2.1', {'arua_midnight': z}), {'arua_midnight': z}))
    r = api.install_theme('arua_midnight')
    assert r['ok'], r['message']
    assert (fake_game / 'data/ui/themes/arua_midnight/theme.toml').is_file()
    assert {t['name'] for t in r['theme_list'] if t['installed']} == set(THEMES)


def test_remove_theme_refused_while_game_runs(fake_game):
    r = make_api(fake_game, running=True).remove_theme('arua_dark')
    assert not r['ok'] and 'close' in r['message'].lower()
    assert (fake_game / 'data/ui/themes/arua_dark').is_dir()
    r = make_api(fake_game).remove_theme('arua_dark')
    assert r['ok'] and not (fake_game / 'data/ui/themes/arua_dark').exists()


def test_start_update_downloads_and_launches_setup(fake_game):
    launched = []
    blocked = make_api(fake_game, running=True, launched=launched).start_update()
    assert not blocked['ok'] and launched == []
    r = make_api(fake_game, launched=launched).start_update()
    assert r['ok'], r['message']
    exe, args = launched[0]
    assert Path(exe).read_bytes() == b'12345'
    assert '/COMPONENTS=companion,ice,dark' in args
