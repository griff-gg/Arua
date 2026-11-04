import pytest

from arua_companion.generators import (MARKERS, drops_css, nameplate_bars_css, settings_lua, world_ui_css)
from arua_companion.settings import Settings, load_settings, save_settings
from conftest import THEME


@pytest.mark.xfail(strict=True, reason='theme defaults land in Task 6')
def test_defaults_reproduce_current_theme_files():
    s = Settings()
    assert world_ui_css(s) == (THEME / 'styles/spritesheet_world_ui.css').read_text(encoding='utf-8')
    assert nameplate_bars_css(s) == (THEME / 'styles/ice_nameplate_gauges.css').read_text(encoding='utf-8')


def test_marker_blue():
    assert 'world-target-marker: 2px 910px 32px 28px;' in world_ui_css(Settings(marker='blue'))
    assert set(MARKERS) == {'red', 'blue', 'green'}


def test_party_bars_faded_uses_np_bars():
    css = nameplate_bars_css(Settings(party_bars='faded'))
    assert 'src: ../imgs/ice_np_bars.dds;' in css and 'gauge-red-sm-md: 2px 32px 200px 26px;' in css
    assert 'gauge-purple-sm-sm: 1px 52px 99px 4px;' in css


def test_drops_defaults_are_empty_look():
    css = drops_css(Settings(), [])
    assert 'background-color' not in css and 'font-effect: none' not in css and 'opacity: 0.' not in css
    assert '.arua-drops-ok { display: block; }' in css


def test_drops_box_no_outline_half():
    css = drops_css(Settings(drop_box=True, drop_outline=False, drop_opacity=50), ['Pink Powder'])
    assert 'opacity: 0.5' in css and 'font-effect: none' in css and 'background-color: rgba(10, 18, 32, 200)' in css
    assert '.dropped-item[lf-name="Pink Powder"] { opacity: 1; }' in css


def test_drops_names_are_cleaned():
    css = drops_css(Settings(drop_opacity=75), ['Say "hi"\\'])
    assert '[lf-name="Say hi"]' in css


def test_settings_lua_has_no_forbidden_chars():
    lua = settings_lua(Settings(group_rows=1, group_columns=2, class_icons=False, minimap_size=260))
    assert '<' not in lua and '&' not in lua
    assert 'group_rows = 1, group_columns = 2, class_icons = false, minimap_size = 260' in lua
    assert lua.splitlines()[0].startswith('-- ARUA-SETTINGS-BEGIN') and lua.splitlines()[-1] == '-- ARUA-SETTINGS-END'


def test_load_settings_clamps(tmp_path):
    p = tmp_path / 's.json'
    p.write_text('{"group_rows": 9, "drop_opacity": 33, "minimap_size": 999, "marker": "pink"}')
    s = load_settings(p)
    assert (s.group_rows, s.drop_opacity, s.minimap_size, s.marker) == (3, 100, 300, 'red')


def test_load_settings_missing_or_broken(tmp_path):
    assert load_settings(tmp_path / 'nope.json') == Settings()
    (tmp_path / 'bad.json').write_text('{not json')
    assert load_settings(tmp_path / 'bad.json') == Settings()


def test_settings_roundtrip(tmp_path):
    s = Settings(marker='green', drop_box=True, group_rows=2, party_bars='faded')
    save_settings(tmp_path / 's.json', s)
    assert load_settings(tmp_path / 's.json') == s
