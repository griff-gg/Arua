"""Export Arua's interface art to PNGs for the Companion window.
Usage: python export_art.py <theme dir, e.g. themes/arua_ice> <out dir, e.g. companion/ui/art>
Reads only the theme's own sprite sheets (styles/ice_sprites*.css + imgs/*.dds)."""
import re
import sys
from pathlib import Path

from PIL import Image

PREFIXES = ('ice-frame-', 'ice-panel-', 'ice-tab-', 'ice-corner-', 'ice-close-', 'ice-check-')
MARKERS = {'red': (211, 878), 'blue': (2, 910), 'green': (38, 910)}   # imgs/iceinv2.dds, 32x28


def sheets(theme: Path):
    for css in sorted((theme / 'styles').glob('ice_sprites*.css')):
        text = re.sub(r'/\*.*?\*/', '', css.read_text(encoding='utf-8'), flags=re.S)
        for body in re.findall(r'@spritesheet[^{]*\{(.*?)\}', text, re.S):
            src = re.search(r'src:\s*([^;]+);', body)
            if not src:
                continue
            image = (css.parent / src.group(1).strip()).resolve()
            for name, x, y, w, h in re.findall(r'^\s*([\w-]+)\s*:\s*(\d+)px\s+(\d+)px\s+(\d+)px\s+(\d+)px', body, re.M):
                yield image, name, int(x), int(y), int(w), int(h)


def main(theme: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    cache, count = {}, 0
    for image, name, x, y, w, h in sheets(theme):
        if not name.startswith(PREFIXES) or 'hd' in name:
            continue
        im = cache.setdefault(image, Image.open(image).convert('RGBA'))
        im.crop((x, y, x + w, y + h)).save(out / (name[len('ice-'):] + '.png'))
        count += 1
    atlas2 = Image.open(theme / 'imgs' / 'iceinv2.dds').convert('RGBA')
    for color, (x, y) in MARKERS.items():
        atlas2.crop((x, y, x + 32, y + 28)).save(out / f'marker-{color}.png')
        count += 1
    print('exported', count, 'images to', out)


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
