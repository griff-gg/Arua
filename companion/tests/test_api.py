from pathlib import Path

from arua_companion.app import Api
from arua_companion.apply import NO_THEME

DATA = Path(__file__).resolve().parents[1] / 'data' / 'items.json'
SAVED = 'Saved. Restart the game, or press Ctrl+F5 in game to reload the UI.'


def test_get_state_roundtrip(fake_game):
    api = Api(fake_game, items_path=DATA)
    st = api.get_state()
    assert 'arua_ice' in st['themes'] and st['items_patch'] == '2026-11-03'
    st['settings']['marker'] = 'blue'
    st['lists']['green'] = 'Golden Feather'
    st['profiles'] = {'items': [{'name': 'Farm', 'lists': {'purple': 'Blue Stone'}}], 'active': 'Farm'}
    assert api.save(st) == {'ok': True, 'message': SAVED, 'skipped': []}
    again = Api(fake_game, items_path=DATA).get_state()
    assert again['settings']['marker'] == 'blue'
    assert again['lists']['green'] == 'Golden Feather'
    assert again['profiles']['active'] == 'Farm' and again['profiles']['items'][0]['lists']['purple'] == 'Blue Stone'


def test_save_without_theme(tmp_path):
    (tmp_path / 'data/ui/themes').mkdir(parents=True)
    api = Api(tmp_path, items_path=DATA)
    assert api.save(api.get_state()) == {'ok': False, 'message': NO_THEME, 'skipped': []}


def test_save_bad_settings_are_cleaned(fake_game):
    api = Api(fake_game, items_path=DATA)
    st = api.get_state()
    st['settings']['group_rows'] = 'lots'
    st['settings']['minimap_size'] = 5000
    assert api.save(st)['ok']
    assert Api(fake_game, items_path=DATA).get_state()['settings']['minimap_size'] == 190


def test_search_through_api(fake_game):
    assert any(i['name'] == 'Pink Powder' for i in Api(fake_game, items_path=DATA).search('pink pow'))


def test_update_item_list_offline_keeps_list(fake_game, tmp_path):
    items = tmp_path / 'items.json'
    items.write_bytes(DATA.read_bytes())
    api = Api(fake_game, items_path=items, fetch=lambda url: (_ for _ in ()).throw(OSError('offline')))
    r = api.update_item_list()
    assert r['ok'] is False and 'offline' in r['message']
    assert api.search('hime')
