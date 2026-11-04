from pathlib import Path

from arua_companion.lootfilter import (Lists, build_lf_data, build_rules_css, lf_hash, lua_string,
                                       read_lists, read_profiles, write_lists, write_profiles, all_names)

FIX = Path(__file__).resolve().parent / 'fixtures'
D = FIX / 'lf_basic'


def load():
    return read_lists(D / 'loot_filter.txt'), read_profiles(D / 'loot_filter_profiles.txt')


def test_rules_css_matches_helper():
    css = build_rules_css(*load())
    assert css == (D / 'expected_lf_rules.css').read_text(encoding='utf-8')


def test_lf_data_matches_helper():
    block = build_lf_data(*load())
    assert block == (D / 'expected_lf_data.lua').read_text(encoding='utf-8').rstrip('\n')


def test_hash_matches_helper():
    # tags the PowerShell helper wrote for the fixture profiles (lfp-<hash>)
    assert lf_hash('Profile A') == '483132409'
    assert lf_hash('Farm B') == '247821013'


def test_lua_string_escapes():
    s = lua_string("Knight's Sword, Salt & Pepper <Rare>, Épée")
    assert '<' not in s and '&' not in s
    assert s == "'Knight\\039s Sword, Salt \\038 Pepper \\060Rare>, \\195\\137p\\195\\169e'"


def test_read_lists_bom_crlf_comments(tmp_path):
    p = tmp_path / 'loot_filter.txt'
    p.write_bytes('﻿yellow=A, B\r\n# note\r\nfoo=bar\r\ndim_others=1\r\nname_size=0\r\n'.encode('utf-8'))
    lists = read_lists(p)
    assert (lists.yellow, lists.dim_others, lists.name_size) == ('A, B', True, 0)


def test_write_read_roundtrip(tmp_path):
    lists = Lists(yellow='A', blue='', purple='', red='B', green='', rainbow='',
                  only_filtered=False, dim_others=True, name_size=1)
    write_lists(tmp_path / 'f.txt', lists)
    assert read_lists(tmp_path / 'f.txt') == lists


def test_profiles_roundtrip(tmp_path):
    _, profiles = load()
    write_profiles(tmp_path / 'p.txt', profiles)
    assert read_profiles(tmp_path / 'p.txt') == profiles


def test_all_names_dedup_in_order():
    names = all_names(*load())
    assert names[:2] == ['Pink Powder', "Knight's Sword"]
    assert names.count('Pink Powder') == 1 and 'Rainbow Gem' in names
