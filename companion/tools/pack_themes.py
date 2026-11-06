"""Zips each theme for a release: <out>/Arua-<VERSION>-<theme>.zip, each holding <theme>/...
The Companion's Themes tab downloads these.
    python companion/tools/pack_themes.py <out dir>"""
import os
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def main(out: str) -> None:
    version = (REPO / 'VERSION').read_text(encoding='utf-8').strip()
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for theme in sorted((REPO / 'themes').iterdir()):
        if not (theme / 'theme.toml').is_file():
            continue
        dest = out_dir / f'Arua-{version}-{theme.name}.zip'
        with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for root, _, files in os.walk(theme):
                for f in sorted(files):
                    p = Path(root) / f
                    z.write(p, p.relative_to(theme.parent).as_posix())
        print(f'{dest.name}: {dest.stat().st_size / 2**20:.0f} MB')


if __name__ == '__main__':
    main(sys.argv[1])
