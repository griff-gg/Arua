import json
from pathlib import Path

from arua_companion.items import ITEMS_URL, load_items, search, update_items

DATA = Path(__file__).resolve().parents[1] / 'data' / 'items.json'


def test_search_orders_prefix_first():
    items = [{'name': 'Purple Powder', 'cat': 'material'}, {'name': 'Pink Powder', 'cat': 'material'},
             {'name': 'Powder Keg', 'cat': 'consumable'}]
    assert [i['name'] for i in search(items, 'powder')] == ['Powder Keg', 'Pink Powder', 'Purple Powder']


def test_search_needs_two_chars():
    assert search([{'name': 'Hime', 'cat': 'material'}], 'h') == []
    assert search([{'name': 'Hime', 'cat': 'material'}], ' h ') == []


def test_search_limit():
    items = [{'name': f'Sword {i:02d}', 'cat': 'weapon'} for i in range(50)]
    assert len(search(items, 'sword')) == 20 and len(search(items, 'sword', limit=5)) == 5


def test_shipped_list_has_known_names():
    names = {i['name'] for i in load_items(DATA)}
    assert {'Hime', 'Ice Key Fragment', 'Astarot Feather', 'Wooden Sword'} <= names


def test_items_url_is_the_repo():
    assert ITEMS_URL == 'https://raw.githubusercontent.com/griff-gg/Arua/main/companion/data/items.json'


def _list(n):
    return json.dumps({'patch': '2026-12-01', 'items': [{'name': f'Item {i}', 'cat': 'material'} for i in range(n)]}).encode()


def test_update_items_replaces_file(tmp_path):
    dest = tmp_path / 'items.json'
    dest.write_text('{"patch": "old", "items": []}')
    ok, msg = update_items(dest, fetch=lambda url: _list(1500))
    assert ok and msg == 'Item list updated: 1500 items (patch 2026-12-01).'
    assert len(load_items(dest)) == 1500


def test_update_items_keeps_old_on_error(tmp_path):
    dest = tmp_path / 'items.json'
    dest.write_text('{"patch": "old", "items": []}')
    before = dest.read_bytes()

    def offline(url):
        raise OSError('offline')

    for fetch in (offline, lambda url: b'{}', lambda url: b'not json', lambda url: _list(10)):
        ok, msg = update_items(dest, fetch=fetch)
        assert not ok and msg.startswith('Could not update the item list: ') and msg.endswith('. The current list is kept.')
        assert dest.read_bytes() == before
    assert not (tmp_path / 'items.tmp').exists()


def test_search_hides_names_the_filter_cannot_match():
    items = [{'name': 'Kurara "Hey, Girl!" Backpack', 'cat': 'back'}, {'name': 'Atk Power, Accuracy Up (All)', 'cat': 'consumable'},
             {'name': 'Hey Hat', 'cat': 'cap'}, {'name': 'Back' + chr(92) + 'slash', 'cat': 'cap'}]
    assert [i['name'] for i in search(items, 'hey')] == ['Hey Hat']
    assert search(items, 'atk power') == [] and search(items, 'slash') == []


def test_shipped_list_search_never_returns_commas_or_quotes():
    items = load_items(DATA)
    for q in ('hey', 'atk power', 'shirt', 'feet'):
        assert all(',' not in i['name'] and '"' not in i['name'] for i in search(items, q, limit=500))
