"""Theme files the Companion generates from its settings."""
import re

from .settings import Settings

# selected-player marker sprites in imgs/iceinv2.dds (32x28)
MARKERS = {'red': '211px 878px', 'blue': '2px 910px', 'green': '38px 910px'}

_BARS = {
    'normal': ('../imgs/iceinv.dds', ('160px 394px', '2px 532px', '160px 394px', '206px 532px')),
    'faded': ('../imgs/ice_np_bars.dds', ('2px 2px', '2px 32px', '2px 2px', '2px 62px')),
}


def world_ui_css(s: Settings) -> str:
    return ('@spritesheet world-ui-0 {\n'
            f'    /* ice theme: selected-player marker ({s.marker}), chosen in Arua Companion. Atlas2. */\n'
            '    src: ../imgs/iceinv2.dds;\n'
            f'    world-target-marker: {MARKERS[s.marker]} 32px 28px;\n'
            '}\n'
            '@spritesheet world-ui-1 {\n'
            '    src: /3ddata/control/res/glassui_00.dds;\n'
            '    world-quest-1: 1px 301px 43px 43px;\n'
            '    world-quest-2: 45px 301px 43px 43px;\n'
            '    world-quest-3: 89px 301px 43px 43px;\n'
            '    world-quest-4: 133px 301px 43px 43px;\n'
            '}\n')


def nameplate_bars_css(s: Settings) -> str:
    src, (bg, red, bg_sm, blue) = _BARS[s.party_bars]
    return ('/* Nameplate bars: the native nameplate layer draws these sprite NAMES directly,\n'
            ' * so they are remapped onto the ice art (only linked from character_nameplates.html).\n'
            f' * Party Bars: {s.party_bars} (Arua Companion). */\n'
            '@spritesheet ice-nameplate\n{\n'
            f'    src: {src};\n'
            f'    gauge-bg-sm-md: {bg} 200px 26px;\n'
            f'    gauge-red-sm-md: {red} 200px 26px;\n'
            f'    gauge-bg-sm-sm: {bg_sm} 200px 26px;\n'
            f'    gauge-blue-sm-sm: {blue} 200px 26px;\n'
            '}\n'
            '@spritesheet ice-nameplate-keep\n{\n'
            '    src: ../imgs/gauge.dds;\n'
            '    gauge-purple-sm-sm: 1px 52px 99px 4px;\n'
            '}\n')


def drops_css(s: Settings, names: list[str]) -> str:
    root = '#dropped-item-labels-root .dropped-item'
    rows = ['/* Drop names (Arua Companion): box, outline and opacity of drops that are not in a list. */',
            '.arua-drops-ok { display: block; }']
    body = []
    if s.drop_box:
        body.append('background-color: rgba(10, 18, 32, 200); border-radius: 3dp;')
    if not s.drop_outline:
        body.append('font-effect: none;')
    if s.drop_opacity < 100:
        body.append('opacity: %s;' % ('0.75' if s.drop_opacity == 75 else '0.5'))
    if body:
        rows.append(root + ' { ' + ' '.join(body) + ' }')
    # listed (glowing) names keep their own look: no box, full opacity
    reset = (['background-color: rgba(0, 0, 0, 0);'] if s.drop_box else []) + (['opacity: 1;'] if s.drop_opacity < 100 else [])
    if reset:
        for n in names:
            n = re.sub(r'["\\]', '', n)
            if n:
                rows.append(f'{root}[lf-name="{n}"] {{ ' + ' '.join(reset) + ' }')
    return '\n'.join(rows) + '\n'


def settings_lua(s: Settings) -> str:
    return ('-- ARUA-SETTINGS-BEGIN (written by Arua Companion; do not edit by hand)\n'
            f'local ARUA_SETTINGS = {{ group_rows = {s.group_rows}, group_columns = {s.group_columns}, '
            f'class_icons = {str(s.class_icons).lower()}, minimap_size = {s.minimap_size} }}\n'
            '-- ARUA-SETTINGS-END')
