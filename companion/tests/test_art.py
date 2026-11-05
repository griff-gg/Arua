from pathlib import Path

from PIL import Image

ART = Path(__file__).resolve().parents[1] / 'ui' / 'art'
NEEDED = ([f'frame-{p}' for p in ('tl', 't', 'tr', 'l', 'c', 'r', 'bl', 'b', 'br')]
          + [f'panel-{p}' for p in ('tl', 't', 'tr', 'l', 'c', 'r', 'bl', 'b', 'br')]
          + [f'{t}-{p}' for t in ('tab', 'tab-hover', 'tab-sel') for p in ('l', 'c', 'r')]
          + ['corner-tl', 'corner-br', 'close-n', 'close-h', 'close-a', 'check-off', 'check-on',
             'marker-red', 'marker-blue', 'marker-green'])


def test_all_art_exported():
    missing = [n for n in NEEDED if not (ART / f'{n}.png').is_file()]
    assert missing == []


def test_markers_are_32x28():
    for c in ('red', 'blue', 'green'):
        assert Image.open(ART / f'marker-{c}.png').size == (32, 28)
