"""Save: write the player's choices into the loot files and every installed Arua theme."""
from dataclasses import dataclass, field
from pathlib import Path

from .generators import drops_css, nameplate_bars_css, settings_lua, world_ui_css
from .lootfilter import Lists, Profiles, all_names, build_lf_data, build_rules_css, write_lists, write_profiles
from .settings import Settings, save_settings
from .themes import backup, can_write, find_arua_themes, read_text, replace_block, write_text

NO_THEME = 'No Arua theme found in data\\ui\\themes'
NO_WRITE = 'Windows did not allow writing to the game folder. Nothing was changed.'
LF_FILES = ('game/dropped_item_labels.html', 'game/options_bgfx.html')
SETTINGS_FILES = ('game/arena_group.html', 'game/minimap.html')


@dataclass
class SaveReport:
    themes: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    error: str | None = None


def save_all(game: Path, settings: Settings, lists: Lists, profiles: Profiles) -> SaveReport:
    game = Path(game)
    themes = find_arua_themes(game)
    if not themes:
        return SaveReport(error=NO_THEME)
    whole = {
        'styles/lf_rules.css': build_rules_css(lists, profiles),
        'styles/spritesheet_world_ui.css': world_ui_css(settings),
        'styles/ice_nameplate_gauges.css': nameplate_bars_css(settings),
        'styles/arua_drops.css': drops_css(settings, all_names(lists, profiles)),
    }
    blocks = [(f, '-- ARUA-LF-DATA-BEGIN', '-- ARUA-LF-DATA-END', build_lf_data(lists, profiles)) for f in LF_FILES]
    blocks += [(f, '-- ARUA-SETTINGS-BEGIN', '-- ARUA-SETTINGS-END', settings_lua(settings)) for f in SETTINGS_FILES]

    targets = [game] + [t / f for t in themes for f in whole] + [t / f for t in themes for f, *_ in blocks]
    if not can_write([p for p in targets if p.exists()]):
        return SaveReport(error=NO_WRITE)

    report = SaveReport()
    for name, write in (('loot_filter.txt', lambda p: write_lists(p, lists)),
                        ('loot_filter_profiles.txt', lambda p: write_profiles(p, profiles)),
                        ('arua_companion.json', lambda p: save_settings(p, settings))):
        backup(game / name, game, None)
        write(game / name)

    for theme in themes:
        for rel, text in whole.items():
            path = theme / rel
            backup(path, game, theme.name)
            write_text(path, text)
        for rel, begin, end, block in blocks:
            path = theme / rel
            if not path.is_file():
                report.skipped.append(f'{theme.name}/{rel}: file missing')
                continue
            new, count = replace_block(read_text(path), begin, end, block)
            if count == 0:
                what = 'settings block' if 'SETTINGS' in begin else 'loot filter block'
                report.skipped.append(f'{theme.name}/{rel}: no {what} (old Arua build)')
                continue
            backup(path, game, theme.name)
            write_text(path, new)
        report.themes.append(theme.name)
    return report
