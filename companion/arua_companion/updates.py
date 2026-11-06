"""Arua updates and theme install: newest release on GitHub, downloads, theme folders.

Only files from the Arua repo's own GitHub releases are used, and a download is checked against the
sha256 GitHub lists for it."""
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from .items import urllib_fetch

LATEST_URL = 'https://api.github.com/repos/griff-gg/Arua/releases/latest'
TAG_URL = 'https://api.github.com/repos/griff-gg/Arua/releases/tags/v{version}'
DOWNLOAD_PREFIX = 'https://github.com/griff-gg/Arua/releases/download/'
# folder name -> (setup component, label)
THEMES = {'arua_ice': ('ice', 'Arua Ice'), 'arua_dark': ('dark', 'Arua Dark'),
          'arua_midnight': ('midnight', 'Arua Midnight')}


class UpdateError(Exception):
    pass


@dataclass
class Asset:
    name: str
    url: str
    size: int
    sha256: str | None


@dataclass
class Release:
    version: str
    page: str
    setup: Asset | None = None
    themes: dict = field(default_factory=dict)   # theme folder -> Asset


def parse_version(s: str) -> tuple:
    m = re.fullmatch(r'v?(\d+(?:\.\d+)*)', str(s or '').strip())
    return tuple(int(x) for x in m.group(1).split('.')) if m else ()


def is_newer(candidate: str, current: str) -> bool:
    c, cur = parse_version(candidate), parse_version(current)
    return bool(c) and c > cur


def app_version() -> str:
    """VERSION bundled with the app (frozen) or at the repo root (source)."""
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[2]))
    try:
        return (base / 'VERSION').read_text(encoding='utf-8').strip()
    except OSError:
        return '0'


def read_release(raw: bytes) -> Release | None:
    try:
        data = json.loads(raw.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict) or not parse_version(data.get('tag_name')):
        return None
    rel = Release(version='.'.join(map(str, parse_version(data['tag_name']))), page=str(data.get('html_url') or ''))
    for a in data.get('assets') or []:
        if not isinstance(a, dict):
            continue
        name, url = str(a.get('name') or ''), str(a.get('browser_download_url') or '')
        if not url.startswith(DOWNLOAD_PREFIX) or '/' in name or '\\' in name:
            continue
        digest = str(a.get('digest') or '')
        asset = Asset(name, url, int(a.get('size') or 0),
                      digest[7:].lower() if re.fullmatch(r'sha256:[0-9a-fA-F]{64}', digest) else None)
        if name.endswith('-Setup.exe'):
            rel.setup = asset
        else:
            m = re.search(r'-(arua_[a-z]+)\.zip$', name)
            if m and m.group(1) in THEMES:
                rel.themes[m.group(1)] = asset
    return rel


def latest_release(fetch=urllib_fetch) -> Release | None:
    try:
        return read_release(fetch(LATEST_URL))
    except Exception:   # offline, rate limited, ...: simply no update shown
        return None


def download(asset: Asset, dest: Path, fetch=urllib_fetch) -> Path:
    dest = Path(dest)
    data = fetch(asset.url)
    if asset.size and len(data) != asset.size:
        raise UpdateError(f'{asset.name} did not download completely.')
    if asset.sha256 and hashlib.sha256(data).hexdigest() != asset.sha256:
        raise UpdateError(f'{asset.name} does not match the release (checksum). Nothing was changed.')
    tmp = dest.with_name(dest.name + '.part')
    tmp.write_bytes(data)
    os.replace(tmp, dest)
    return dest


def themes_root(game: Path) -> Path:
    return Path(game) / 'data' / 'ui' / 'themes'


def installed_themes(game: Path) -> list[str]:
    root = themes_root(game)
    return [n for n in THEMES if (root / n / 'theme.toml').is_file()]


def install_theme_zip(zip_path: Path, game: Path, name: str) -> None:
    """Unpack <name>/... from the zip into the themes folder, replacing the old folder only when the
    whole new one is in place."""
    if name not in THEMES:
        raise UpdateError(f'{name} is not an Arua theme.')
    root = themes_root(game)
    root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        for n in names:
            parts = n.replace('\\', '/').split('/')
            if parts[0] != name or '..' in parts or n.startswith('/') or ':' in n:
                raise UpdateError(f'The download for {name} contains unexpected files. Nothing was changed.')
        if f'{name}/theme.toml' not in names:
            raise UpdateError(f'The download for {name} is not a theme. Nothing was changed.')
        work = Path(tempfile.mkdtemp(prefix='.arua_new_', dir=root))
        try:
            z.extractall(work)
            old = root / name
            trash = root / f'.arua_old_{name}'
            if trash.exists():
                shutil.rmtree(trash)
            if old.exists():
                os.replace(old, trash)
            os.replace(work / name, old)
            shutil.rmtree(trash, ignore_errors=True)
        finally:
            shutil.rmtree(work, ignore_errors=True)


def remove_theme(game: Path, name: str) -> None:
    if name not in THEMES:
        raise UpdateError(f'{name} is not an Arua theme.')
    path = themes_root(game) / name
    if path.exists():
        shutil.rmtree(path)


def setup_args(game: Path) -> list[str]:
    """Arguments for a quiet update: same folder, the Companion plus the themes that are installed now."""
    comps = ['companion'] + [THEMES[n][0] for n in installed_themes(game)]
    return ['/SILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/RELAUNCH',
            f'/DIR={Path(game)}', '/COMPONENTS=' + ','.join(comps)]
