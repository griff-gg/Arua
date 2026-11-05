"""Window shape: the Arua frame plus its two corner flourishes, built from the page's own art.

Windows draws nothing outside this shape, so the window has no box around it. The numbers mirror app.css:
the frame sits MARGIN in from the window edge, the inner panel 6px inside the frame (40px below its top),
and the flourishes are placed against that panel like .ice-fx in the game's ice_window.css.
"""
from functools import lru_cache
from pathlib import Path

from PIL import Image

MARGIN = (14, 24, 14, 24)                      # left, top, right, bottom (app.css .window inset)
PANEL = (6, 40, 6, 6)                          # panel inside the frame
FX_TL = (-8, -63, 81, 70)                      # left, top, width, height against the panel
FX_BR = (-8, -21, 77, 67)                      # right, bottom, width, height against the panel
ALPHA_MIN = 110                                # pixels at least this solid belong to the window


def art_dir() -> Path:
    import sys
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    return base / 'ui' / 'art'


@lru_cache(maxsize=None)
def _art(name: str) -> Image.Image:
    return Image.open(art_dir() / f'{name}.png').convert('RGBA').getchannel('A')


def _frame_alpha(w: int, h: int) -> Image.Image:
    """The frame's nine-slice alpha at w x h (edges tiled like the page)."""
    out = Image.new('L', (w, h), 0)
    tl, tr, bl, br = _art('frame-tl'), _art('frame-tr'), _art('frame-bl'), _art('frame-br')
    left, top, right, bottom = tl.width, tl.height, br.width, br.height
    out.paste(255, (left, top, w - right, h - bottom))
    for x in range(left, w - right, _art('frame-t').width):
        out.paste(_art('frame-t'), (x, 0))
        out.paste(_art('frame-b'), (x, h - bottom))
    for y in range(top, h - bottom, _art('frame-l').height):
        out.paste(_art('frame-l'), (0, y))
        out.paste(_art('frame-r'), (w - right, y))
    out.paste(tl, (0, 0))
    out.paste(tr, (w - right, 0))
    out.paste(bl, (0, h - bottom))
    out.paste(br, (w - right, h - bottom))
    return out


def window_mask(width: int, height: int, scale: float) -> list[tuple[int, int, int]]:
    """Rows of the window shape as (y, x_start, x_end) runs, in device pixels.
    width / height are the window's client size in CSS pixels; scale is the display scaling (1.0 = 100%)."""
    ml, mt, mr, mb = MARGIN
    fw, fh = width - ml - mr, height - mt - mb
    mask = Image.new('L', (width, height), 0)
    mask.paste(_frame_alpha(fw, fh), (ml, mt))
    pl, pt = ml + PANEL[0], mt + PANEL[1]
    pr, pb = ml + fw - PANEL[2], mt + fh - PANEL[3]
    x, y, w, h = FX_TL
    tl = _art('corner-tl').resize((w, h), Image.LANCZOS)
    mask.paste(255, (pl + x, pt + y), tl)
    x, y, w, h = FX_BR
    br = _art('corner-br').resize((w, h), Image.LANCZOS)
    mask.paste(255, (pr - x - w, pb - y - h), br)
    if scale != 1.0:
        mask = mask.resize((round(width * scale), round(height * scale)), Image.NEAREST)
    px = mask.load()
    runs = []
    for yy in range(mask.height):
        start = None
        for xx in range(mask.width):
            on = px[xx, yy] >= ALPHA_MIN
            if on and start is None:
                start = xx
            elif not on and start is not None:
                runs.append((yy, start, xx))
                start = None
        if start is not None:
            runs.append((yy, start, mask.width))
    return runs


def apply_shape(hwnd: int, runs: list[tuple[int, int, int]]) -> bool:
    """Cut the window to the runs (Windows only)."""
    import ctypes
    gdi, user = ctypes.windll.gdi32, ctypes.windll.user32
    gdi.CreateRectRgn.restype = ctypes.c_void_p
    gdi.CombineRgn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
    gdi.DeleteObject.argtypes = [ctypes.c_void_p]
    user.SetWindowRgn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
    rgn = gdi.CreateRectRgn(0, 0, 0, 0)
    for y, x0, x1 in runs:
        r = gdi.CreateRectRgn(x0, y, x1, y + 1)
        gdi.CombineRgn(rgn, rgn, r, 2)          # RGN_OR
        gdi.DeleteObject(r)
    return bool(user.SetWindowRgn(ctypes.c_void_p(hwnd), rgn, True))   # Windows owns rgn from here
