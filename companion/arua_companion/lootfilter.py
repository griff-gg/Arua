"""Loot filter files and generated theme parts. A port of game-folder/arua_loot_filter.ps1:
same input files, byte-identical lf_rules.css and ARUA-LF-DATA block."""
import re
from dataclasses import dataclass, field
from pathlib import Path

COLORS = ('yellow', 'blue', 'purple', 'red', 'green', 'rainbow')
GLOW = {'yellow': 'rgb(255, 226, 84)', 'blue': 'rgb(150, 230, 255)', 'purple': 'rgb(205, 140, 255)',
        'red': 'rgb(255, 96, 96)', 'green': 'rgb(120, 235, 120)', 'rainbow': 'animated'}
LINE = re.compile(r'^\s*([A-Za-z_]+)\s*=(.*)$')
SECTION = re.compile(r'^\s*\[(.*?)\]\s*$')


@dataclass
class Lists:
    yellow: str = ''
    blue: str = ''
    purple: str = ''
    red: str = ''
    green: str = ''
    rainbow: str = ''
    only_filtered: bool = False
    dim_others: bool = False
    name_size: int | None = None

    def colors(self) -> dict[str, str]:
        return {k: getattr(self, k) for k in COLORS}


@dataclass
class Profile:
    name: str
    lists: dict[str, str]


@dataclass
class Profiles:
    items: list[Profile] = field(default_factory=list)
    active: str | None = None

    def get(self, name):
        return next((p for p in self.items if p.name == name), None)


def _lines(path: Path):
    if not Path(path).exists():
        return []
    return re.split(r'\r?\n', Path(path).read_text(encoding='utf-8-sig'))


def read_lists(path: Path) -> Lists:
    out = Lists()
    for line in _lines(path):
        m = LINE.match(line)
        if not m:
            continue
        key, value = m.group(1).lower(), m.group(2)
        if key in COLORS:
            setattr(out, key, value)
        elif key == 'only_filtered':
            out.only_filtered = re.match(r'^\s*1', value) is not None
        elif key == 'dim_others':
            out.dim_others = re.match(r'^\s*1', value) is not None
        elif key == 'name_size':
            d = re.search(r'\d', value)
            if d:
                out.name_size = int(d.group(0))
    return out


def write_lists(path: Path, lists: Lists) -> None:
    rows = [f'{k}={getattr(lists, k)}' for k in COLORS]
    rows += [f'only_filtered={int(lists.only_filtered)}', f'dim_others={int(lists.dim_others)}',
             f'name_size={2 if lists.name_size is None else lists.name_size}']
    Path(path).write_bytes(('\r\n'.join(rows) + '\r\n').encode('utf-8'))


def read_profiles(path: Path) -> Profiles:
    out, cur = Profiles(), None
    for line in _lines(path):
        s = SECTION.match(line)
        if s:
            cur = {k: '' for k in COLORS}
            old = out.get(s.group(1))
            if old:
                old.lists = cur
            else:
                out.items.append(Profile(s.group(1), cur))
            continue
        m = LINE.match(line)
        if not m:
            continue
        key = m.group(1).lower()
        if key == 'active' and cur is None:
            out.active = m.group(2).strip()
        elif cur is not None and key in COLORS:
            cur[key] = m.group(2)
    return out


def write_profiles(path: Path, profiles: Profiles) -> None:
    rows = []
    if profiles.active and profiles.get(profiles.active):
        rows.append(f'active={profiles.active}')
    for p in profiles.items:
        rows.append(f'[{p.name}]')
        rows += [f'{k}={p.lists.get(k, "")}' for k in COLORS]
    Path(path).write_bytes(('\r\n'.join(rows) + '\r\n').encode('utf-8'))


def lf_hash(text: str) -> str:
    h = 5381
    for b in text.encode('utf-8'):
        h = (h * 33 + b) % 1000000007
    return str(h)


def _split(text: str) -> list[str]:
    return [p.strip() for p in (text or '').split(',') if p.strip()]


def _sig(colors: dict[str, str]) -> str:
    return lf_hash('|'.join(colors.get(k) or '' for k in COLORS))


def _block(lines: list[str], colors: dict[str, str], tag: str) -> list[str]:
    root = '#dropped-item-labels-root.' + tag
    lines.append(f'/* set {tag} {_sig(colors)} */')
    every, per = [], {}
    for key in COLORS:
        names = []
        for n in _split(colors.get(key, '')):
            n = re.sub(r'["\\]', '', n)
            if n:
                names.append(n)
                every.append(n)
        per[key] = names

    def rule(names, pre, suf, body):
        if names:
            lines.append(',\n'.join(f'{root}{pre} .dropped-item[lf-name="{n}"]{suf}' for n in names) + ' { ' + body + ' }')

    pulse = 'animation: 1.3s sine-in-out infinite alternate lf-pulse;'
    rule(every, '', '', 'overflow: visible; font-size: 22dp;')
    rule(every, '.lf-sz1', '', 'font-size: 18dp;')
    rule(every, '.lf-sz0', '', 'font-size: 15dp;')
    rule(every, '', ' .lf-beam-wrap', 'display: block;')
    rule(every, '', ' .lf-text', 'color: rgb(255, 255, 255);')
    rule(every, '', ' .lf-beam', pulse)
    rule(every, '', ' .lf-base', pulse)
    rule(every, '', ' .lf-core', 'animation: 1.3s sine-in-out infinite alternate lf-pulse-core;')
    rule(every, '', ' .lf-shine', 'animation: 1.9s linear infinite lf-shine;')
    rule(every, '.lf-only', '', 'display: inline-block;')
    rule(every, '.lf-dim', '', 'opacity: 1;')
    for key in COLORS:
        names = per[key]
        if key == 'rainbow':
            rb = 'animation: 1.3s sine-in-out infinite alternate lf-pulse, 3s linear infinite lf-rainbow-beam;'
            rule(names, '', '', 'font-effect: outline(1dp rgb(36, 24, 60)), glow(2dp rgb(255, 255, 255));')
            rule(names, '', ' .lf-text', 'animation: 3s linear infinite lf-rainbow-text;')
            rule(names, '', ' .lf-beam', rb)
            rule(names, '', ' .lf-base', rb)
        else:
            c = GLOW[key]
            rule(names, '', ' .lf-beam', f'image-color: {c};')
            rule(names, '', ' .lf-base', f'image-color: {c};')
            rule(names, '', '', f'font-effect: outline(1dp {c}), glow(3dp {c});')
    return every


def build_rules_css(lists: Lists, profiles: Profiles, modes: bool = True) -> str:
    lines = ['/* generated by the Loot Filter (Options > Loot Filter > Save). Do not edit. */',
             '.lf-rules-ok { display: block; }']
    every = _block(lines, lists.colors(), 'lfp-none')
    for p in profiles.items:
        _block(lines, p.lists, 'lfp-' + lf_hash(p.name))
    if modes and every:
        base = '#dropped-item-labels-root.lfp-none:not(.lf-live)'
        sel = ',\n'.join(f'{base} .dropped-item[lf-name="{n}"]' for n in every)
        size = '' if lists.name_size is None else str(lists.name_size)
        lines.append(f'/* saved modes: only_filtered={int(lists.only_filtered)} dim_others={int(lists.dim_others)} name_size={size} */')
        if lists.only_filtered:
            lines.append(base + ' .dropped-item { display: none; }')
            lines.append(sel + ' { display: inline-block; }')
        elif lists.dim_others:
            lines.append(base + ' .dropped-item { opacity: 0.5; }')
            lines.append(sel + ' { opacity: 1; }')
        if lists.name_size == 1:
            lines.append(sel + ' { font-size: 18dp; }')
        if lists.name_size == 0:
            lines.append(sel + ' { font-size: 15dp; }')
    return '\n'.join(lines) + '\n'


def lua_string(s: str) -> str:
    out = ["'"]
    for ch in s:
        if ch == '\\':
            out.append('\\092')
        elif ch == "'":
            out.append('\\039')
        elif ch == '<':
            out.append('\\060')
        elif ch == '&':
            out.append('\\038')
        elif ord(ch) < 32:
            continue
        elif ord(ch) > 127:
            out.extend('\\%03d' % b for b in ch.encode('utf-8'))
        else:
            out.append(ch)
    out.append("'")
    return ''.join(out)


def _lua_lists(colors: dict[str, str], extra: str = '') -> str:
    return '{ ' + extra + ', '.join(f'{k} = {lua_string(colors.get(k, ""))}' for k in COLORS) + ' }'


def build_lf_data(lists: Lists, profiles: Profiles) -> str:
    modes = (f'only_filtered = {str(lists.only_filtered).lower()}, '
             f'dim_others = {str(lists.dim_others).lower()}, ')
    if lists.name_size is not None:
        modes += f'name_size = {lists.name_size}, '
    active = lua_string(profiles.active) if profiles.active and profiles.get(profiles.active) else 'nil'
    rows = ['-- ARUA-LF-DATA-BEGIN (written by "Arua Loot Filter.bat" from loot_filter.txt; do not edit by hand)',
            'local LF_DATA = {',
            '    lists = ' + _lua_lists(lists.colors(), modes) + ',',
            '    profiles = {']
    rows += ['        ' + _lua_lists(p.lists, 'name = ' + lua_string(p.name) + ', ') + ',' for p in profiles.items]
    rows += ['    },', f'    active = {active},', '}', '-- ARUA-LF-DATA-END']
    return '\n'.join(rows)


def all_names(lists: Lists, profiles: Profiles) -> list[str]:
    seen, out = set(), []
    for colors in [lists.colors()] + [p.lists for p in profiles.items]:
        for key in COLORS:
            for n in _split(colors.get(key, '')):
                if n not in seen:
                    seen.add(n)
                    out.append(n)
    return out
