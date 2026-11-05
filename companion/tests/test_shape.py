from arua_companion.shape import window_mask

W, H = 940, 684


def inside(runs, x, y):
    return any(ry == y and x0 <= x < x1 for ry, x0, x1 in runs)


def test_mask_keeps_frame_and_cuts_the_margin():
    runs = window_mask(W, H, 1.0)
    assert inside(runs, W // 2, H // 2)                  # middle of the window
    assert not inside(runs, 2, H // 2)                   # left margin
    assert not inside(runs, W // 2, 5)                   # above the title band
    assert not inside(runs, W // 2, H - 3)               # below the frame


def test_mask_keeps_the_flourishes_outside_the_frame():
    runs = window_mask(W, H, 1.0)
    assert any(y < 24 and x < 100 for y, x0, x in runs)   # top-left flourish sticks up past the frame
    assert any(y >= H - 24 and x0 > W - 100 for y, x0, x1 in runs)  # bottom-right one hangs below


def test_mask_scales_with_display_scaling():
    small = window_mask(W, H, 1.0)
    big = window_mask(W, H, 1.5)
    assert max(y for y, _, _ in big) > max(y for y, _, _ in small)
