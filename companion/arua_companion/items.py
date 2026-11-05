"""The shipped item-name list (plain text, extracted locally per game patch) and search over it."""
import json
import os
import urllib.request
from pathlib import Path

ITEMS_URL = 'https://raw.githubusercontent.com/griff-gg/Arua/main/companion/data/items.json'
MIN_ITEMS = 1000


def load_items(path: Path) -> list[dict]:
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        return [i for i in data.get('items', []) if isinstance(i, dict) and i.get('name')]
    except (OSError, ValueError, AttributeError):
        return []


def list_patch(path: Path) -> str:
    try:
        return str(json.loads(Path(path).read_text(encoding='utf-8')).get('patch', ''))
    except (OSError, ValueError, AttributeError):
        return ''


def filter_can_match(name: str) -> bool:
    """Loot lists are comma separated and the rules drop quotes / backslashes: such names can never glow."""
    return not any(ch in name for ch in (',', '"', chr(92)))


def search(items: list[dict], query: str, limit: int = 20) -> list[dict]:
    q = (query or '').strip().lower()
    if len(q.replace(' ', '')) < 2:
        return []
    first, rest = [], []
    for i in items:
        if not filter_can_match(i['name']):
            continue
        n = i['name'].lower()
        if n.startswith(q):
            first.append(i)
        elif q in n:
            rest.append(i)
    key = lambda i: (i['name'].lower(), i.get('cat', ''))
    return (sorted(first, key=key) + sorted(rest, key=key))[:limit]


def urllib_fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=15) as r:
        return r.read()


def update_items(dest: Path, fetch=urllib_fetch) -> tuple[bool, str]:
    dest = Path(dest)
    tmp = dest.with_suffix('.tmp')
    try:
        raw = fetch(ITEMS_URL)
        data = json.loads(raw.decode('utf-8'))
        items = data.get('items') if isinstance(data, dict) else None
        if not isinstance(items, list) or len(items) < MIN_ITEMS:
            raise ValueError('the downloaded list looks incomplete')
        tmp.write_bytes(raw)
        os.replace(tmp, dest)
    except Exception as e:  # network, JSON, disk: keep the current list in every case
        if tmp.exists():
            tmp.unlink()
        reason = str(e) or e.__class__.__name__
        return False, f'Could not update the item list: {reason}. The current list is kept.'
    return True, f'Item list updated: {len(items)} items (patch {data.get("patch", "?")}).'
