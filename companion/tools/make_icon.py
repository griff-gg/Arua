"""Builds the Arua icon -> companion/ui/arua.ico (+ installer wizard images).

Big sizes (48 px and up) are the Arua logo (art/arua_logo.png, kept outside the repo). Small sizes (16-32 px) are the
logo's compass redrawn simply, so they stay sharp in the taskbar.
    python companion/tools/make_icon.py [preview.png]"""
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

S = 1024  # the compass is drawn large, then scaled down
HERE = os.path.dirname(os.path.abspath(__file__))
COMP = os.path.dirname(HERE)
LOGO = os.path.join(COMP, 'art', 'arua_logo.png')
ICO = os.path.join(COMP, 'ui', 'arua.ico')
WIZ = os.path.join(os.path.dirname(COMP), 'installer')

NAVY = (14, 36, 92, 255)
GOLD_T, GOLD_B = (255, 226, 96), (222, 140, 16)


def vgrad(size, top, bottom):
    g = Image.new('RGBA', (1, size[1]))
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        g.putpixel((0, y), tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)) + (255,))
    return g.resize(size)


def paint(im, mask, top, bottom):
    im.paste(vgrad(im.size, top, bottom), (0, 0), mask)


def shape(fn):
    m = Image.new('L', (S, S), 0)
    fn(ImageDraw.Draw(m))
    return m


def outlined(im, mask, width, top, bottom):
    im.paste(NAVY, (0, 0), mask.filter(ImageFilter.MaxFilter(width)))
    paint(im, mask, top, bottom)


def spike(cx, cy, length, half, angle):
    a = math.radians(angle)
    ux, uy, px, py = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    return [(cx + ux * length, cy + uy * length), (cx + px * half, cy + py * half), (cx - px * half, cy - py * half)]


def four_star(cx, cy, ro, ri):
    pts = []
    for i in range(8):
        r = ro if i % 2 == 0 else ri
        a = math.radians(-90 + i * 45)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def compass():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    cx, cy, R = 512, 560, 330
    # gold spikes: a long one up, short ones left and right
    sp = shape(lambda d: [d.polygon(spike(cx, cy, l, h, a), fill=255) for l, h, a in
                          ((470, 74, -90), (395, 62, 0), (395, 62, 180), (385, 62, 90))])
    outlined(im, sp, 41, GOLD_T, GOLD_B)
    # gold ring
    ring = shape(lambda d: d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=255))
    outlined(im, ring, 41, GOLD_T, GOLD_B)
    # blue face
    r2 = R - 78
    face = shape(lambda d: d.ellipse((cx - r2, cy - r2, cx + r2, cy + r2), fill=255))
    im.paste(NAVY, (0, 0), face.filter(ImageFilter.MaxFilter(25)))
    paint(im, face, (70, 140, 230), (20, 60, 160))
    # white four-point star
    st = shape(lambda d: d.polygon(four_star(cx, cy, 200, 52), fill=255))
    paint(im, st, (255, 255, 255), (200, 220, 245))
    # shine on the ring
    hi = shape(lambda d: d.arc((cx - R + 22, cy - R + 22, cx + R - 22, cy + R - 22), 200, 300, fill=255, width=26))
    im.alpha_composite(Image.merge('RGBA', [Image.new('L', (S, S), 255)] * 3 + [hi.point(lambda v: v * 0.7)]))
    return im.crop(im.getchannel('A').getbbox())


def square(im, pad=0.0):
    w, h = im.size
    side = int(max(w, h) * (1 + pad))
    sq = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    sq.alpha_composite(im, ((side - w) // 2, (side - h) // 2))
    return sq


def logo():
    src = Image.open(LOGO).convert('RGBA')
    return src.crop(src.getchannel('A').point(lambda v: 255 if v > 40 else 0).getbbox())


def wizard_images(lg):
    """Setup wizard: logo on the left panel (164x314 @ 100 %, 2x for high DPI) and a small top-right image."""
    for name, size, scale in (('wizard.bmp', (164, 314), 2), ('wizard_small.bmp', (55, 55), 2)):
        w, h = size[0] * scale, size[1] * scale
        bg = Image.new('RGBA', (w, h), (232, 244, 252, 255))
        bg.alpha_composite(vgrad((w, h), (238, 248, 255), (188, 222, 246)))
        pic = lg.copy()
        pic.thumbnail((int(w * 0.92), int(h * 0.92)), Image.LANCZOS)
        bg.alpha_composite(pic, ((w - pic.width) // 2, (h - pic.height) // 2))
        bg.convert('RGB').save(os.path.join(WIZ, name))


def main():
    lg, cp = logo(), compass()
    big, small = square(lg, 0.02), square(cp, 0.04)
    sizes = [(s, big if s >= 48 else small) for s in (16, 20, 24, 32, 40, 48, 64, 128, 256)]
    frames = [src.resize((s, s), Image.LANCZOS) for s, src in sizes]
    frames[-1].save(ICO, format='ICO', sizes=[f.size for f in frames], append_images=frames[:-1])
    wizard_images(lg)
    if len(sys.argv) > 1:
        sheet = Image.new('RGBA', (620, 560), (32, 36, 48, 255))
        sheet.paste((236, 240, 244, 255), (0, 280, 620, 560))
        for y0 in (10, 290):
            x = 0
            for f in reversed(frames):
                if f.width in (256, 64, 48, 32, 24, 16):
                    sheet.alpha_composite(f, (x, y0))
                    x += f.width + 10
        sheet.save(sys.argv[1])
    print('wrote', os.path.normpath(ICO))


if __name__ == '__main__':
    main()
