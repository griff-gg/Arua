"""Arua Companion: the window (pywebview) and the API its page calls."""
import ctypes
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from .apply import save_all
from .items import list_patch, load_items, search, update_items, urllib_fetch
from .lootfilter import COLORS, Lists, Profile, Profiles, read_lists, read_profiles
from .settings import _clean, load_settings
from .themes import can_write, find_arua_themes

SAVED = 'Saved. Restart the game, or press Ctrl+F5 in game to reload the UI.'


def app_dir() -> Path:
    """Folder of the exe (frozen) or of the companion source."""
    return Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]


def ui_dir() -> Path:
    return Path(getattr(sys, '_MEIPASS', app_dir())) / 'ui'


def default_items() -> Path:
    p = app_dir() / 'items.json'
    return p if p.is_file() else app_dir() / 'data' / 'items.json'


class Api:
    def __init__(self, game: Path, items_path: Path | None = None, fetch=urllib_fetch):
        self._game = Path(game)
        self._items_path = Path(items_path) if items_path else default_items()
        self._fetch = fetch
        self._items = load_items(self._items_path)

    def get_state(self) -> dict:
        lists = read_lists(self._game / 'loot_filter.txt')
        profiles = read_profiles(self._game / 'loot_filter_profiles.txt')
        return {
            'settings': asdict(load_settings(self._game / 'arua_companion.json')),
            'lists': {**lists.colors(), 'only_filtered': lists.only_filtered, 'dim_others': lists.dim_others,
                      'name_size': 2 if lists.name_size is None else lists.name_size},
            'profiles': {'items': [{'name': p.name, 'lists': dict(p.lists)} for p in profiles.items],
                         'active': profiles.active},
            'themes': [t.name for t in find_arua_themes(self._game)],
            'game': str(self._game),
            'items_patch': list_patch(self._items_path),
        }

    def search(self, query: str) -> list[dict]:
        return search(self._items, query)

    def save(self, state: dict) -> dict:
        settings = _clean(state.get('settings') or {})
        raw = state.get('lists') or {}
        size = raw.get('name_size', 2)
        lists = Lists(**{k: str(raw.get(k) or '') for k in COLORS},
                      only_filtered=bool(raw.get('only_filtered')), dim_others=bool(raw.get('dim_others')),
                      name_size=size if size in (0, 1, 2) else 2)
        prof = state.get('profiles') or {}
        profiles = Profiles(items=[Profile(str(p['name']), {k: str((p.get('lists') or {}).get(k) or '') for k in COLORS})
                                   for p in prof.get('items', []) if str(p.get('name', '')).strip()],
                            active=prof.get('active'))
        report = save_all(self._game, settings, lists, profiles)
        if report.error:
            return {'ok': False, 'message': report.error, 'skipped': []}
        return {'ok': True, 'message': SAVED, 'skipped': report.skipped}

    def update_item_list(self) -> dict:
        ok, msg = update_items(self._items_path, fetch=self._fetch)
        if ok:
            self._items = load_items(self._items_path)
        return {'ok': ok, 'message': msg, 'items_patch': list_patch(self._items_path)}


def _relaunch_elevated(args: list[str]) -> bool:
    """Ask Windows (UAC) to start this program again with permission to write the game folder."""
    params = subprocess.list2cmdline(args + ['--elevated'])
    exe = sys.executable
    if not getattr(sys, 'frozen', False):
        params = subprocess.list2cmdline(['-m', 'arua_companion.app']) + ' ' + params
    return ctypes.windll.shell32.ShellExecuteW(None, 'runas', exe, params, str(app_dir()), 1) > 32


def main(argv: list[str] | None = None) -> None:
    import webview

    argv = list(sys.argv[1:] if argv is None else argv)
    game = app_dir().parent if getattr(sys, 'frozen', False) else Path(r'C:\Program Files\ROSE Online')
    if '--game' in argv:
        game = Path(argv[argv.index('--game') + 1])
    targets = [game] + [p for t in find_arua_themes(game) for p in (t / 'styles', t / 'game')]
    if not can_write(targets) and '--elevated' not in argv:
        if _relaunch_elevated([a for a in argv if a != '--elevated']):
            return
    api = Api(game)
    webview.create_window('Arua Companion', str(ui_dir() / 'index.html'), js_api=api,
                                   width=900, height=640, min_size=(760, 560), background_color='#0e203e')
    webview.start()


if __name__ == '__main__':
    main()
