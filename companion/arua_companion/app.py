"""Arua Companion: the window (pywebview) and the API its page calls."""
import ctypes
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

from . import updates
from .apply import save_all
from .items import list_patch, load_items, search, update_items, urllib_fetch
from .lootfilter import COLORS, Lists, Profile, Profiles, read_lists, read_profiles
from .settings import _clean, load_settings
from .themes import can_write, find_arua_themes

WIDTH, HEIGHT = 940, 684
OUTLINE = '#265b97'   # the frame art's outer outline colour
SAVED = 'Saved. Restart the game, or press Ctrl+F5 in game to reload the UI.'
VERSION_FILE = 'arua_companion_version.txt'   # Arua version the saved settings were last written into
CLOSE_GAME = 'Close ROSE Online first, then try again.'


def app_dir() -> Path:
    """Folder of the exe (frozen) or of the companion source."""
    return Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]


def ui_dir() -> Path:
    return Path(getattr(sys, '_MEIPASS', app_dir())) / 'ui'


def default_items() -> Path:
    p = app_dir() / 'items.json'
    return p if p.is_file() else app_dir() / 'data' / 'items.json'


def game_running() -> bool:
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq trose.exe', '/NH'], capture_output=True, text=True,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return 'trose.exe' in out.lower()


def launch(exe: Path, args: list[str]) -> None:
    """Start the setup; Windows asks for permission (the setup needs admin)."""
    os.startfile(str(exe), arguments=subprocess.list2cmdline(args))


class Api:
    def __init__(self, game: Path, items_path: Path | None = None, fetch=urllib_fetch, version: str | None = None,
                 game_running=game_running, launch=launch):
        self._game = Path(game)
        self._items_path = Path(items_path) if items_path else default_items()
        self._fetch = fetch
        self._items = load_items(self._items_path)
        self._window = None
        self._version = version or updates.app_version()
        self._running = game_running
        self._launch = launch
        self._release = None

    def attach(self, window) -> None:
        self._window = window

    def close(self) -> None:
        if self._window:
            self._window.destroy()

    def minimize(self) -> None:
        if self._window:
            self._window.minimize()

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
            'theme_list': self._theme_list(),
            'version': self._version,
        }

    def _theme_list(self) -> list[dict]:
        have = set(updates.installed_themes(self._game))
        return [{'name': n, 'label': label, 'installed': n in have} for n, (_, label) in updates.THEMES.items()]

    def _apply_saved(self) -> dict:
        """Write the saved lists and settings into every installed Arua theme (as pressing Save would)."""
        return self.save(self.get_state())

    def startup(self) -> dict:
        """After an install or update the theme files are fresh: put the player's settings back in, once."""
        mark = self._game / VERSION_FILE
        try:
            done = mark.read_text(encoding='utf-8').strip()
        except OSError:
            done = ''
        if not find_arua_themes(self._game) or done == self._version:
            return {'applied': False, 'message': ''}
        r = self._apply_saved()
        if not r['ok']:
            return {'applied': False, 'message': r['message']}
        mark.write_text(self._version + '\n', encoding='utf-8')
        return {'applied': True, 'message': f'Arua {self._version}: your lists and settings are applied to the themes.'}

    def check_update(self) -> dict:
        rel = updates.latest_release(self._fetch)
        ok = bool(rel and rel.setup and updates.is_newer(rel.version, self._version))
        self._release = rel if ok else None
        return {'available': ok, 'version': rel.version if ok else '', 'page': rel.page if ok else ''}

    def start_update(self) -> dict:
        if self._running():
            return {'ok': False, 'message': CLOSE_GAME}
        if not self._release:
            self.check_update()
        if not self._release:
            return {'ok': False, 'message': 'No newer Arua version found.'}
        rel, asset = self._release, self._release.setup
        try:
            exe = updates.download(asset, Path(tempfile.mkdtemp(prefix='arua_update_')) / asset.name, self._fetch)
            self._launch(exe, updates.setup_args(self._game))
        except Exception as e:
            return {'ok': False, 'message': f'Update failed: {e}'}
        self.close()   # the setup replaces this app and opens the Companion again when it is done
        return {'ok': True, 'message': f'Installing Arua {rel.version}…'}

    def install_theme(self, name: str) -> dict:
        if name not in updates.THEMES:
            return {'ok': False, 'message': 'Unknown theme.', 'theme_list': self._theme_list()}
        label = updates.THEMES[name][1]
        try:
            rel = updates.read_release(self._fetch(updates.TAG_URL.format(version=self._version)))
            asset = rel.themes.get(name) if rel else None
            if not asset:
                raise updates.UpdateError(f'{label} {self._version} is not available for download')
            with tempfile.TemporaryDirectory(prefix='arua_theme_') as tmp:
                updates.install_theme_zip(updates.download(asset, Path(tmp) / asset.name, self._fetch), self._game, name)
        except Exception as e:
            return {'ok': False, 'message': f'Could not install {label}: {e}', 'theme_list': self._theme_list()}
        r = self._apply_saved()
        extra = '' if r['ok'] else f' (settings not applied: {r["message"]})'
        return {'ok': True, 'message': f'{label} installed{extra}. Pick it in game: Options > Interface > Theme.',
                'theme_list': self._theme_list()}

    def remove_theme(self, name: str) -> dict:
        if self._running():
            return {'ok': False, 'message': CLOSE_GAME, 'theme_list': self._theme_list()}
        try:
            updates.remove_theme(self._game, name)
        except Exception as e:
            return {'ok': False, 'message': f'Could not remove it: {e}', 'theme_list': self._theme_list()}
        return {'ok': True, 'message': f'{updates.THEMES[name][1]} removed.', 'theme_list': self._theme_list()}

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
    targets = [game, updates.themes_root(game)] + [p for t in find_arua_themes(game) for p in (t / 'styles', t / 'game')]
    if not can_write(targets) and '--elevated' not in argv:
        if _relaunch_elevated([a for a in argv if a != '--elevated']):
            return
    api = Api(game)
    # no Windows title bar: the page draws the Arua frame (title band drags, X closes). The window is cut
    # to the frame + flourish shape, so nothing shows around it (edge pixels blend into the frame outline).
    window = webview.create_window('Arua Companion', str(ui_dir() / 'index.html'), js_api=api,
                                   width=WIDTH, height=HEIGHT, resizable=False, frameless=True,
                                   easy_drag=False, shadow=False, background_color=OUTLINE)
    api.attach(window)
    window.events.shown += lambda: _shape(window)
    webview.start()


def _shape(window) -> None:
    """Cut the shown window to the Arua frame shape; on any failure it simply stays a rectangle."""
    try:
        import ctypes
        from ctypes import wintypes
        from .shape import apply_shape, window_mask
        hwnd = int(window.native.Handle.ToInt64())
        rect = wintypes.RECT()
        ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
        scale = ctypes.windll.user32.GetDpiForWindow(hwnd) / 96 or 1.0
        apply_shape(hwnd, window_mask(round(rect.right / scale), round(rect.bottom / scale), scale))
    except Exception:
        pass


if __name__ == '__main__':
    main()
