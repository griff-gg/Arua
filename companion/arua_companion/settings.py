"""Companion settings (arua_companion.json in the ROSE Online folder). Defaults = the current Arua look."""
import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

MARKER_NAMES = ('red', 'blue', 'green')
OPACITIES = (100, 75, 50)


@dataclass
class Settings:
    marker: str = 'red'
    drop_box: bool = False
    drop_outline: bool = True
    drop_opacity: int = 100
    group_rows: int = 3
    group_columns: int = 0
    class_icons: bool = True
    minimap_size: int = 190
    party_bars: str = 'normal'


def _clean(raw: dict) -> Settings:
    s = Settings()
    names = {f.name for f in fields(Settings)}
    for k, v in raw.items():
        if k in names:
            setattr(s, k, v)
    d = Settings()
    s.marker = s.marker if s.marker in MARKER_NAMES else d.marker
    s.party_bars = s.party_bars if s.party_bars in ('normal', 'faded') else d.party_bars
    s.drop_box, s.drop_outline, s.class_icons = bool(s.drop_box), bool(s.drop_outline), bool(s.class_icons)
    try:
        s.drop_opacity = int(s.drop_opacity) if int(s.drop_opacity) in OPACITIES else d.drop_opacity
        s.group_rows = min(3, max(1, int(s.group_rows)))
        s.group_columns = 2 if int(s.group_columns) == 2 else 0
        s.minimap_size = min(300, max(190, int(s.minimap_size)))
    except (TypeError, ValueError):
        return Settings()
    return s


def load_settings(path: Path) -> Settings:
    try:
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return Settings()
    return _clean(raw) if isinstance(raw, dict) else Settings()


def save_settings(path: Path, s: Settings) -> None:
    Path(path).write_text(json.dumps(asdict(s), indent=2, sort_keys=True) + '\n', encoding='utf-8')
