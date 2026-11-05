import re

import pytest

from arua_companion.apply import save_all
from arua_companion.settings import Settings
from arua_companion.themes import can_write, find_arua_themes, replace_block
from conftest import LISTS, PROFILES, lua_parses


def test_save_writes_every_arua_theme(fake_game):
    r = save_all(fake_game, Settings(marker='green', group_rows=2), LISTS, PROFILES)
    assert r.error is None and r.themes == ['arua_dark', 'arua_ice'] and r.skipped == []
    for t in ('arua_dark', 'arua_ice'):
        th = fake_game / 'data/ui/themes' / t
        assert 'world-target-marker: 38px 910px' in (th / 'styles/spritesheet_world_ui.css').read_text()
        assert 'group_rows = 2' in (th / 'game/arena_group.html').read_text(encoding='utf-8')
        assert "active = 'Profile A'" in (th / 'game/options_bgfx.html').read_text(encoding='utf-8')
    assert (fake_game / 'arua_companion_backup/arua_ice/game/arena_group.html').exists()


def test_save_writes_loot_files_and_rules(fake_game):
    r = save_all(fake_game, Settings(), LISTS, PROFILES)
    assert r.error is None
    assert (fake_game / 'loot_filter.txt').read_text(encoding='utf-8').startswith('yellow=Pink Powder')
    assert '[Farm B]' in (fake_game / 'loot_filter_profiles.txt').read_text(encoding='utf-8')
    rules = (fake_game / 'data/ui/themes/arua_dark/styles/lf_rules.css').read_text(encoding='utf-8')
    assert 'lf-name="Golden Feather"' in rules
    labels = (fake_game / 'data/ui/themes/arua_dark/game/dropped_item_labels.html').read_text(encoding='utf-8')
    assert "name = 'Farm B'" in labels and 'local LF_DATA = nil' not in labels
    assert (fake_game / 'arua_companion.json').exists()


def test_save_leaves_rose_alone(fake_game):
    rose = fake_game / 'data/ui/themes/rose'
    before = sorted(str(p.relative_to(rose)) for p in rose.rglob('*'))
    save_all(fake_game, Settings(), LISTS, PROFILES)
    assert sorted(str(p.relative_to(rose)) for p in rose.rglob('*')) == before
    assert not (fake_game / 'arua_companion_backup/rose').exists()


def test_no_arua_theme(tmp_path):
    (tmp_path / 'data/ui/themes/rose').mkdir(parents=True)
    r = save_all(tmp_path, Settings(), LISTS, PROFILES)
    assert r.error == 'No Arua theme found in data\\ui\\themes'
    assert not (tmp_path / 'loot_filter.txt').exists()


def test_old_build_without_markers_is_skipped(fake_game):
    f = fake_game / 'data/ui/themes/arua_ice/game/minimap.html'
    f.write_text(f.read_text(encoding='utf-8').replace('ARUA-SETTINGS', 'X'), encoding='utf-8')
    before = f.read_bytes()
    r = save_all(fake_game, Settings(), LISTS, PROFILES)
    assert 'arua_ice/game/minimap.html: no settings block (old Arua build)' in r.skipped
    assert f.read_bytes() == before


def test_saved_themes_still_validate(fake_game):
    save_all(fake_game, Settings(drop_box=True), LISTS, PROFILES)
    for html in (fake_game / 'data/ui/themes/arua_ice/game').glob('*.html'):
        for script in re.findall(r'<script>(.*?)</script>', html.read_text(encoding='utf-8'), re.S):
            if html.name != 'speech_bubbles.html':
                assert '<' not in script and '&' not in script, html.name
            assert lua_parses(script), html.name


def test_find_arua_themes(fake_game):
    assert [p.name for p in find_arua_themes(fake_game)] == ['arua_dark', 'arua_ice']


def test_replace_block_keeps_crlf():
    text = 'a\r\n-- B-BEGIN x\r\nold\r\n-- B-END\r\nz\r\n-- B-BEGIN\r\nold2\r\n-- B-END\r\n'
    out, n = replace_block(text, '-- B-BEGIN', '-- B-END', '-- B-BEGIN\nnew\n-- B-END')
    assert n == 2
    assert out == 'a\r\n-- B-BEGIN\r\nnew\r\n-- B-END\r\nz\r\n-- B-BEGIN\r\nnew\r\n-- B-END\r\n'


def test_can_write(tmp_path):
    f = tmp_path / 'a.txt'
    f.write_text('x')
    assert can_write([f]) is True
