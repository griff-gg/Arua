import shutil
from pathlib import Path

import pytest
from lupa import LuaRuntime

from arua_companion.lootfilter import read_lists, read_profiles

REPO = Path(__file__).resolve().parents[2]
THEME = REPO / 'themes' / 'arua_ice'
FIX = Path(__file__).resolve().parent / 'fixtures'
LISTS = read_lists(FIX / 'lf_basic' / 'loot_filter.txt')
PROFILES = read_profiles(FIX / 'lf_basic' / 'loot_filter_profiles.txt')

_lua = LuaRuntime()
_check = _lua.eval('function(s) local f = load(s) return f ~= nil end')


def lua_parses(source: str) -> bool:
    return bool(_check(source))


@pytest.fixture
def fake_game(tmp_path):
    """A game folder with two Arua themes (copies of the repo's arua_ice) and a plain 'rose' folder."""
    themes = tmp_path / 'data' / 'ui' / 'themes'
    for name in ('arua_ice', 'arua_dark'):
        shutil.copytree(THEME, themes / name)
    (themes / 'rose' / 'game').mkdir(parents=True)
    (themes / 'rose' / 'game' / 'hud.html').write_text('<rml></rml>', encoding='utf-8')
    return tmp_path
