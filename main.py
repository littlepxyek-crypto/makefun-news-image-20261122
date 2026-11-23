#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""The World in One Image - entry generator for make.fun news-image-20261122.

Renders a one-page broadsheet of Sunday 22 November 2026 from stories.json
(the verified corpus shipped in this repository) and writes the entry image
to the kit output path (/output/entry.png, or $MAKEFUN_OUTPUT_DIR/entry.png).
The drawing is fully deterministic: same data in, same PNG bytes out.
All illustrations are original flat drawings made by this program.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

S = 2                      # supersample factor; final image is 1024x1024
W = H = 1024
MARGIN = 10

CREAM = (247, 241, 222)
PAPER = (252, 248, 233)
INK = (26, 26, 24)
NAVY = (20, 44, 78)
NAVY2 = (28, 58, 99)
RED = (176, 48, 40)
GOLD = (190, 148, 56)
TEAL = (26, 92, 108)
GREY = (108, 101, 88)
RULE = (198, 189, 163)
SKY = (214, 228, 235)
SEA = (168, 200, 214)

FONT_FILES = {
    "display": "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf",
    "serif_b": "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf",
    "serif": "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf",
    "sans_b": "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "sans": "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
}
_font_cache = {}


def F(kind, size):
    key = (kind, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONT_FILES[kind], int(size * S))
    return _font_cache[key]


def X(v):
    return v * S


def tw(d, s, font):
    return d.textlength(s, font=font) / S


def wrap(d, s, font, maxw):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(d, t, font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def draw_text(d, xy, s, font, fill=INK, anchor="la"):
    d.text((X(xy[0]), X(xy[1])), s, font=font, fill=fill, anchor=anchor)


def rect(d, box, fill=None, outline=None, width=1):
    d.rectangle([X(box[0]), X(box[1]), X(box[2]), X(box[3])],
                fill=fill, outline=outline, width=max(1, int(width * S)))


def line(d, pts, fill=INK, width=1):
    d.line([(X(x), X(y)) for x, y in pts], fill=fill, width=max(1, int(width * S)))


def ellipse(d, box, fill=None, outline=None, width=1):
    d.ellipse([X(box[0]), X(box[1]), X(box[2]), X(box[3])],
              fill=fill, outline=outline, width=max(1, int(width * S)))


def poly(d, pts, fill=None, outline=None):
    d.polygon([(X(x), X(y)) for x, y in pts], fill=fill, outline=outline)


def arc(d, box, a0, a1, fill=INK, width=1):
    d.arc([X(box[0]), X(box[1]), X(box[2]), X(box[3])], a0, a1,
          fill=fill, width=max(1, int(width * S)))


LABEL_COLORS = {
    "CONFIRMED": (30, 104, 52),
    "REPORTED": (146, 106, 18),
    "CLAIM": (168, 52, 38),
    "OFFICIAL": (20, 44, 78),
}

# Coarse world land grid: rows from lat 76 down to -64 (step ~3.18 deg),
# each row a list of (first_col, last_col) land spans over 90 columns
# spanning lon -168..192 (step 4 deg). Good enough for a pin map.
LAND = {
    0: [(8, 20), (33, 38), (56, 88)],
    1: [(3, 7), (10, 24), (32, 39), (52, 89)],
    2: [(2, 8), (10, 26), (33, 38), (44, 47), (50, 89)],
    3: [(2, 9), (11, 27), (34, 37), (40, 40), (44, 48), (50, 88)],
    4: [(3, 9), (12, 28), (41, 42), (44, 88)],
    5: [(4, 7), (13, 29), (41, 42), (44, 52), (53, 87)],
    6: [(14, 30), (43, 55), (56, 86)],
    7: [(15, 30), (42, 56), (57, 85)],
    8: [(16, 29), (42, 55), (56, 84), (79, 81)],
    9: [(16, 29), (42, 54), (58, 82), (80, 80)],
    10: [(15, 29), (42, 50), (52, 58), (59, 80)],
    11: [(15, 29), (41, 48), (50, 53), (56, 75), (68, 80), (81, 81)],
    12: [(15, 28), (43, 50), (52, 57), (62, 66), (67, 79)],
    13: [(15, 28), (40, 52), (53, 58), (59, 64), (63, 67), (68, 78)],
    14: [(15, 20), (16, 27), (38, 54), (54, 58), (63, 67), (70, 77)],
    15: [(14, 20), (24, 25), (37, 55), (63, 66), (70, 74)],
    16: [(14, 19), (37, 55), (55, 58), (63, 66), (70, 73)],
    17: [(14, 17), (37, 54), (63, 65), (70, 73), (76, 77)],
    18: [(14, 16), (37, 53), (63, 64), (70, 72)],
    19: [(19, 22), (38, 52), (64, 64), (70, 72)],
    20: [(19, 24), (38, 51), (71, 78)],
    21: [(19, 25), (39, 50), (70, 80)],
    22: [(20, 26), (40, 49), (72, 82)],
    23: [(20, 27), (40, 48), (78, 83)],
    24: [(21, 27), (41, 47)],
    25: [(21, 28), (41, 47)],
    26: [(21, 28), (41, 46), (50, 50)],
    27: [(21, 27), (41, 46), (50, 50), (74, 80)],
    28: [(21, 27), (41, 45), (50, 50), (72, 81)],
    29: [(21, 26), (41, 45), (71, 82)],
    30: [(21, 26), (41, 44), (71, 82)],
    31: [(21, 25), (41, 44), (72, 81)],
    32: [(21, 25), (41, 43), (73, 80)],
    33: [(21, 24), (41, 43), (74, 79), (86, 86)],
    34: [(21, 24), (76, 79), (85, 86)],
    35: [(21, 23), (85, 87)],
    36: [(21, 23), (85, 86)],
    37: [(21, 22)],
    38: [(21, 22)],
    39: [(21, 22)],
    40: [(21, 21)],
}


# ---------------------------------------------------------------- drawings
# Sixteen original flat illustrations, one per drawn story. Each receives a
# design-space box and paints inside it with simple shapes.

def ill_climate(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=SKY)
    for i, cx in enumerate((0.18, 0.45, 0.72)):
        bx = x + w * cx
        rect(d, (bx, y + h * 0.42, bx + w * 0.09, y + h * 0.86), fill=(90, 88, 84))
        for k in range(3):
            r = w * (0.045 + 0.012 * k)
            ellipse(d, (bx + w * 0.045 - r + k * w * 0.05, y + h * (0.30 - 0.09 * k) - r,
                        bx + w * 0.045 + r + k * w * 0.05, y + h * (0.30 - 0.09 * k) + r),
                    fill=(240, 238, 230))
    rect(d, (x, y + h * 0.86, x + w, y + h), fill=(70, 66, 60))
    dx, dy = x + w * 0.60, y + h * 0.52
    rect(d, (dx, dy, dx + w * 0.30, dy + h * 0.36), fill=(252, 250, 240), outline=INK, width=1.4)
    line(d, [(dx + w * 0.04, dy + h * 0.10), (dx + w * 0.26, dy + h * 0.10)], fill=GREY, width=1.2)
    line(d, [(dx + w * 0.04, dy + h * 0.20), (dx + w * 0.26, dy + h * 0.20)], fill=GREY, width=1.2)
    cxr, cyr, rr = dx + w * 0.15, dy + h * 0.18, w * 0.13
    ellipse(d, (cxr - rr, cyr - rr, cxr + rr, cyr + rr), outline=RED, width=3)
    line(d, [(cxr - rr * 0.7, cyr + rr * 0.7), (cxr + rr * 0.7, cyr - rr * 0.7)], fill=RED, width=3)


def ill_ship(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(198, 216, 228))
    rect(d, (x, y + h * 0.62, x + w, y + h), fill=SEA)
    for i in range(5):
        arc(d, (x + w * (0.06 + 0.18 * i), y + h * 0.78, x + w * (0.20 + 0.18 * i), y + h * 0.94), 180, 360, fill=(240, 246, 248), width=1.6)
    hx, hy = x + w * 0.16, y + h * 0.50
    poly(d, [(hx, hy), (hx + w * 0.52, hy), (hx + w * 0.44, hy + h * 0.14), (hx + w * 0.06, hy + h * 0.14)], fill=(84, 90, 98))
    rect(d, (hx + w * 0.18, hy - h * 0.16, hx + w * 0.30, hy), fill=(104, 110, 118))
    rect(d, (hx + w * 0.32, hy - h * 0.09, hx + w * 0.40, hy), fill=(104, 110, 118))
    line(d, [(hx + w * 0.24, hy - h * 0.30), (hx + w * 0.24, hy - h * 0.16)], fill=INK, width=1.6)
    sx, sy = hx + w * 0.50, hy - h * 0.06
    pts = []
    for i in range(12):
        ang = i * 30
        import math
        r = w * (0.085 if i % 2 == 0 else 0.038)
        pts.append((sx + r * math.cos(math.radians(ang)), sy + r * math.sin(math.radians(ang)) * 0.8))
    poly(d, pts, fill=(238, 128, 42))
    ellipse(d, (sx - w * 0.028, sy - w * 0.028, sx + w * 0.028, sy + w * 0.028), fill=RED)
    dx_, dy_ = x + w * 0.78, y + h * 0.16
    line(d, [(dx_ - w * 0.05, dy_), (dx_ + w * 0.05, dy_)], fill=INK, width=2)
    line(d, [(dx_, dy_ - h * 0.07), (dx_, dy_ + h * 0.07)], fill=INK, width=2)
    rect(d, (dx_ - w * 0.02, dy_ - h * 0.035, dx_ + w * 0.02, dy_ + h * 0.035), fill=INK)


def ill_mercury(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(24, 30, 52))
    for sx, sy in ((0.08, 0.16), (0.2, 0.7), (0.88, 0.2), (0.7, 0.85), (0.45, 0.1)):
        ellipse(d, (x + w * sx, y + h * sy, x + w * sx + 2.4, y + h * sy + 2.4), fill=(240, 240, 230))
    mx, my, mr = x + w * 0.70, y + h * 0.58, w * 0.21
    ellipse(d, (mx - mr, my - mr, mx + mr, my + mr), fill=(168, 160, 148))
    for cx, cy, cr in ((0.3, 0.35, 0.16), (0.62, 0.6, 0.11), (0.45, 0.72, 0.08), (0.7, 0.28, 0.07)):
        ellipse(d, (mx + mr * (cx * 2 - 1) - mr * cr, my + mr * (cy * 2 - 1) - mr * cr,
                    mx + mr * (cx * 2 - 1) + mr * cr, my + mr * (cy * 2 - 1) + mr * cr), fill=(146, 138, 124))
    arc(d, (mx - mr * 1.45, my - mr * 1.45, mx + mr * 1.45, my + mr * 1.45), 300, 60, fill=GOLD, width=2.2)
    bx, by = x + w * 0.30, y + h * 0.44
    poly(d, [(bx - w * 0.16, by - h * 0.10), (bx - w * 0.05, by - h * 0.04), (bx - w * 0.05, by + h * 0.10), (bx - w * 0.16, by + h * 0.04)], fill=(64, 96, 168))
    poly(d, [(bx + w * 0.06, by - h * 0.04), (bx + w * 0.17, by - h * 0.10), (bx + w * 0.17, by + h * 0.04), (bx + w * 0.06, by + h * 0.10)], fill=(64, 96, 168))
    rect(d, (bx - w * 0.05, by - h * 0.07, bx + w * 0.06, by + h * 0.07), fill=GOLD, outline=INK, width=1)
    ellipse(d, (bx - w * 0.018, by - h * 0.30, bx + w * 0.028, by - h * 0.10), outline=(230, 230, 220), width=1.6)
    for i in range(6):
        import math
        a = math.radians(i * 60 + 15)
        line(d, [(x + w * 0.10 + w * 0.05 * math.cos(a), y + h * 0.14 + w * 0.05 * math.sin(a) * 0.6),
                 (x + w * 0.10 + w * 0.085 * math.cos(a), y + h * 0.14 + w * 0.085 * math.sin(a) * 0.6)], fill=(246, 200, 84), width=2)
    ellipse(d, (x + w * 0.065, y + h * 0.085, x + w * 0.135, y + h * 0.195), fill=(246, 200, 84))


def ill_missile(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(232, 222, 200))
    for i, bw in enumerate((0.16, 0.22, 0.13, 0.19)):
        bx = x + w * (0.05 + 0.24 * i)
        rect(d, (bx, y + h * 0.68, bx + w * bw, y + h), fill=(96, 92, 84))
    import math
    cx, cy = x + w * 0.56, y + h * 0.36
    ang = math.radians(38)
    L, Wd = w * 0.34, w * 0.075
    dx, dy = math.cos(ang), math.sin(ang)
    px, py = -dy, dx
    nose = (cx + dx * L / 2, cy + dy * L / 2)
    tail = (cx - dx * L / 2, cy - dy * L / 2)
    poly(d, [(tail[0] + px * Wd / 2, tail[1] + py * Wd / 2), (nose[0], nose[1]),
             (tail[0] - px * Wd / 2, tail[1] - py * Wd / 2)], fill=(210, 208, 200), outline=INK)
    poly(d, [(tail[0], tail[1]), (tail[0] - dx * w * 0.09 - px * w * 0.05, tail[1] - dy * w * 0.09 - py * w * 0.05),
             (tail[0] - dx * w * 0.09 + px * w * 0.05, tail[1] - dy * w * 0.09 + py * w * 0.05)], fill=RED)
    flame = (tail[0] - dx * w * 0.16, tail[1] - dy * w * 0.16)
    poly(d, [(tail[0] - px * w * 0.03, tail[1] - py * w * 0.03), (flame[0], flame[1]),
             (tail[0] + px * w * 0.03, tail[1] + py * w * 0.03)], fill=(238, 140, 40))
    line(d, [(x + w * 0.10, y + h * 0.16), (cx - dx * L * 0.8, cy - dy * L * 0.8)], fill=(180, 175, 160), width=2)


def ill_building(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=SKY)
    bx, by, bw, bh = x + w * 0.14, y + h * 0.18, w * 0.44, h * 0.68
    rect(d, (bx, by, bx + bw, by + bh), fill=(226, 220, 204), outline=INK, width=1.2)
    for r in range(4):
        for c in range(3):
            rect(d, (bx + bw * (0.12 + 0.3 * c), by + bh * (0.12 + 0.22 * r),
                     bx + bw * (0.30 + 0.3 * c), by + bh * (0.26 + 0.22 * r)), fill=(120, 140, 155))
    poly(d, [(bx + bw, by), (x + w * 0.92, y + h * 0.40), (x + w * 0.86, by + bh), (bx + bw, by + bh)], fill=(196, 188, 168))
    line(d, [(bx + bw, by + bh * 0.3), (x + w * 0.80, y + h * 0.52), (bx + bw, by + bh * 0.62)], fill=INK, width=1.4)
    for i in range(4):
        poly(d, [(x + w * (0.60 + 0.09 * i), y + h * 0.86), (x + w * (0.65 + 0.09 * i), y + h * 0.70),
                 (x + w * (0.70 + 0.09 * i), y + h * 0.86)], fill=(150, 142, 126))
    rect(d, (x, y + h * 0.86, x + w, y + h), fill=(120, 114, 100))
    line(d, [(x + w * 0.06, y + h * 0.10), (x + w * 0.06, y + h * 0.86)], fill=(90, 88, 84), width=2)
    line(d, [(x + w * 0.06, y + h * 0.10), (x + w * 0.34, y + h * 0.10)], fill=(90, 88, 84), width=2)
    line(d, [(x + w * 0.30, y + h * 0.10), (x + w * 0.30, y + h * 0.30)], fill=(90, 88, 84), width=1.2)


def ill_gulf(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(226, 214, 186))
    rect(d, (x, y + h * 0.66, x + w, y + h), fill=SEA)
    poly(d, [(x, y + h * 0.66), (x + w * 0.4, y + h * 0.44), (x + w * 0.62, y + h * 0.66)], fill=(150, 138, 108))
    ellipse(d, (x + w * 0.40, y + h * 0.26, x + w * 0.58, y + h * 0.46), fill=(236, 232, 220), outline=INK, width=1.2)
    line(d, [(x + w * 0.49, y + h * 0.46), (x + w * 0.49, y + h * 0.50)], fill=INK, width=2)
    import math
    for k, sx in enumerate((0.10, 0.22)):
        ax, ay = x + w * sx, y + h * 0.60
        for t in range(13):
            tt = t / 12
            px_ = ax + w * 0.42 * tt
            py_ = ay - h * 0.52 * (4 * tt * (1 - tt)) - h * 0.1 * tt
            ellipse(d, (px_ - 1.2, py_ - 1.2, px_ + 1.2, py_ + 1.2), fill=RED)
    poly(d, [(x + w * 0.06, y + h * 0.62), (x + w * 0.10, y + h * 0.44), (x + w * 0.14, y + h * 0.62)], fill=(80, 80, 78))
    poly(d, [(x + w * 0.17, y + h * 0.62), (x + w * 0.21, y + h * 0.44), (x + w * 0.25, y + h * 0.62)], fill=(80, 80, 78))


def ill_desert(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(240, 214, 160))
    ellipse(d, (x + w * 0.76, y + h * 0.08, x + w * 0.92, y + h * 0.34), fill=(246, 178, 60))
    poly(d, [(x, y + h * 0.78), (x + w * 0.4, y + h * 0.62), (x + w, y + h * 0.80), (x + w, y + h), (x, y + h)], fill=(228, 186, 118))
    gx = x + w * 0.24
    rect(d, (gx, y + h * 0.34, gx + w * 0.045, y + h * 0.78), fill=(52, 128, 62))
    rect(d, (gx - w * 0.07, y + h * 0.42, gx - w * 0.028, y + h * 0.58), fill=(52, 128, 62))
    rect(d, (gx - w * 0.07, y + h * 0.42, gx + w * 0.10, y + h * 0.47), fill=(52, 128, 62))
    rect(d, (gx + w * 0.045, y + h * 0.50, gx + w * 0.115, y + h * 0.66), fill=(52, 128, 62))
    hx, hy = x + w * 0.62, y + h * 0.30
    ellipse(d, (hx - w * 0.10, hy - h * 0.09, hx + w * 0.10, hy + h * 0.09), fill=(70, 74, 80))
    line(d, [(hx - w * 0.16, hy - h * 0.13), (hx + w * 0.16, hy - h * 0.13)], fill=INK, width=2.4)
    line(d, [(hx + w * 0.10, hy), (hx + w * 0.20, hy - h * 0.05)], fill=INK, width=2)
    line(d, [(hx - w * 0.03, hy + h * 0.09), (hx - w * 0.03, hy + h * 0.17)], fill=INK, width=1.6)
    line(d, [(hx + w * 0.05, hy + h * 0.09), (hx + w * 0.05, hy + h * 0.17)], fill=INK, width=1.6)


def ill_factory(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(206, 200, 186))
    rect(d, (x + w * 0.08, y + h * 0.52, x + w * 0.92, y + h * 0.88), fill=(110, 104, 96))
    for i in range(4):
        poly(d, [(x + w * (0.08 + 0.21 * i), y + h * 0.52), (x + w * (0.185 + 0.21 * i), y + h * 0.38),
                 (x + w * (0.29 + 0.21 * i), y + h * 0.52)], fill=(88, 84, 78))
    for i, fx in enumerate((0.30, 0.52, 0.72)):
        bx = x + w * fx
        poly(d, [(bx - w * 0.05, y + h * 0.52), (bx, y + h * 0.16), (bx + w * 0.05, y + h * 0.52)], fill=(238, 128, 42))
        poly(d, [(bx - w * 0.028, y + h * 0.52), (bx, y + h * 0.30), (bx + w * 0.028, y + h * 0.52)], fill=(246, 196, 64))
    for i in range(3):
        ellipse(d, (x + w * (0.16 + 0.2 * i), y + h * (0.06 + 0.03 * i), x + w * (0.30 + 0.2 * i), y + h * (0.20 + 0.03 * i)), fill=(120, 116, 108))
    rect(d, (x, y + h * 0.88, x + w, y + h), fill=(84, 80, 74))


def ill_football(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(64, 142, 74))
    rect(d, (x + w * 0.05, y + h * 0.08, x + w * 0.95, y + h * 0.92), outline=(240, 244, 238), width=1.6)
    line(d, [(x + w * 0.5, y + h * 0.08), (x + w * 0.5, y + h * 0.92)], fill=(240, 244, 238), width=1.6)
    ellipse(d, (x + w * 0.40, y + h * 0.30, x + w * 0.60, y + h * 0.70), outline=(240, 244, 238), width=1.6)
    bx, by, br = x + w * 0.30, y + h * 0.56, w * 0.075
    ellipse(d, (bx - br, by - br, bx + br, by + br), fill=(250, 250, 246), outline=INK, width=1.2)
    ellipse(d, (bx - br * 0.32, by - br * 0.32, bx + br * 0.32, by + br * 0.32), fill=INK)
    f = F("display", h * 0.52)
    draw_text(d, (x + w * 0.60, y + h * 0.16), "4-0", f, fill=(252, 250, 240))


def ill_tennis(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(52, 96, 150))
    rect(d, (x + w * 0.10, y + h * 0.14, x + w * 0.90, y + h * 0.86), fill=(58, 148, 84), outline=(245, 245, 240), width=1.4)
    line(d, [(x + w * 0.10, y + h * 0.5), (x + w * 0.90, y + h * 0.5)], fill=(245, 245, 240), width=1.8)
    line(d, [(x + w * 0.5, y + h * 0.14), (x + w * 0.5, y + h * 0.86)], fill=(245, 245, 240), width=1.2)
    rx, ry = x + w * 0.68, y + h * 0.34
    ellipse(d, (rx - w * 0.09, ry - h * 0.20, rx + w * 0.09, ry + h * 0.20), outline=(240, 240, 235), width=2.2)
    line(d, [(rx, ry + h * 0.20), (rx + w * 0.06, ry + h * 0.42)], fill=(240, 240, 235), width=2.4)
    ellipse(d, (x + w * 0.24, y + h * 0.62, x + w * 0.24 + w * 0.05, y + h * 0.62 + w * 0.05), fill=(214, 232, 84))
    tx, ty = x + w * 0.16, y + h * 0.16
    poly(d, [(tx, ty), (tx + w * 0.10, ty), (tx + w * 0.085, ty + h * 0.16), (tx + w * 0.015, ty + h * 0.16)], fill=GOLD)
    rect(d, (tx + w * 0.03, ty - h * 0.05, tx + w * 0.07, ty), fill=GOLD)
    rect(d, (tx - w * 0.01, ty + h * 0.16, tx + w * 0.11, ty + h * 0.21), fill=GOLD)


def ill_moto(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(226, 220, 200))
    rect(d, (x, y + h * 0.80, x + w, y + h), fill=(120, 116, 108))
    for wx in (0.26, 0.74):
        ellipse(d, (x + w * wx - w * 0.085, y + h * 0.56, x + w * wx + w * 0.085, y + h * 0.56 + w * 0.17), fill=(40, 40, 42))
        ellipse(d, (x + w * wx - w * 0.035, y + h * 0.56 + w * 0.05, x + w * wx + w * 0.035, y + h * 0.56 + w * 0.12), fill=(190, 188, 180))
    poly(d, [(x + w * 0.24, y + h * 0.62), (x + w * 0.44, y + h * 0.36), (x + w * 0.66, y + h * 0.34), (x + w * 0.76, y + h * 0.60),
             (x + w * 0.60, y + h * 0.52), (x + w * 0.40, y + h * 0.56)], fill=RED)
    poly(d, [(x + w * 0.46, y + h * 0.34), (x + w * 0.58, y + h * 0.18), (x + w * 0.68, y + h * 0.30), (x + w * 0.56, y + h * 0.38)], fill=(40, 60, 110))
    ellipse(d, (x + w * 0.60, y + h * 0.06, x + w * 0.70, y + h * 0.06 + w * 0.10), fill=(250, 246, 238), outline=INK, width=1.2)
    poly(d, [(x + w * 0.05, y + h * 0.16), (x + w * 0.09, y + h * 0.06), (x + w * 0.13, y + h * 0.16), (x + w * 0.17, y + h * 0.06),
             (x + w * 0.21, y + h * 0.16), (x + w * 0.21, y + h * 0.22), (x + w * 0.05, y + h * 0.22)], fill=GOLD)
    f = F("display", h * 0.40)
    draw_text(d, (x + w * 0.80, y + h * 0.10), "8", f, fill=NAVY)


def ill_f1(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(16, 22, 48))
    for i, bh in enumerate((0.34, 0.5, 0.28, 0.44, 0.38)):
        bx = x + w * (0.04 + 0.19 * i)
        rect(d, (bx, y + h * (0.66 - bh), bx + w * 0.15, y + h * 0.66), fill=(30, 40, 74))
        for r in range(3):
            for c in range(2):
                rect(d, (bx + w * (0.03 + 0.06 * c), y + h * (0.60 - bh + 0.08 * r), bx + w * (0.055 + 0.06 * c), y + h * (0.635 - bh + 0.08 * r)), fill=(246, 210, 110))
    rect(d, (x, y + h * 0.66, x + w, y + h), fill=(52, 54, 66))
    line(d, [(x, y + h * 0.83), (x + w, y + h * 0.83)], fill=(240, 240, 235), width=1.4)
    cy = y + h * 0.60
    poly(d, [(x + w * 0.16, cy + h * 0.10), (x + w * 0.34, cy + h * 0.02), (x + w * 0.52, cy), (x + w * 0.70, cy + h * 0.03),
             (x + w * 0.86, cy + h * 0.10), (x + w * 0.70, cy + h * 0.13), (x + w * 0.30, cy + h * 0.13)], fill=RED)
    rect(d, (x + w * 0.10, cy - h * 0.015, x + w * 0.24, cy + h * 0.025), fill=(30, 30, 34))
    rect(d, (x + w * 0.78, cy - h * 0.015, x + w * 0.92, cy + h * 0.025), fill=(30, 30, 34))
    for wx in (0.26, 0.74):
        ellipse(d, (x + w * wx - w * 0.045, cy + h * 0.08, x + w * wx + w * 0.045, cy + h * 0.08 + w * 0.09), fill=(18, 18, 20))
    line(d, [(x + w * 0.02, cy + h * 0.05), (x + w * 0.14, cy + h * 0.05)], fill=(120, 200, 240), width=2)


def ill_capitol(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=SKY)
    bx, by = x + w * 0.10, y + h * 0.86
    rect(d, (bx, by - h * 0.18, x + w * 0.90, by), fill=(238, 234, 222))
    for i in range(6):
        cx = x + w * (0.17 + 0.115 * i)
        rect(d, (cx, by - h * 0.34, cx + w * 0.045, by - h * 0.18), fill=(238, 234, 222))
    rect(d, (bx, by - h * 0.38, x + w * 0.90, by - h * 0.34), fill=(238, 234, 222))
    arc(d, (x + w * 0.32, by - h * 0.78, x + w * 0.68, by - h * 0.10), 180, 360, fill=(210, 214, 220), width=3)
    poly(d, [(x + w * 0.32, by - h * 0.45), (x + w * 0.68, by - h * 0.45), (x + w * 0.62, by - h * 0.66), (x + w * 0.38, by - h * 0.66)], fill=(210, 214, 220))
    line(d, [(x + w * 0.5, by - h * 0.66), (x + w * 0.5, by - h * 0.80)], fill=INK, width=1.6)
    poly(d, [(x + w * 0.5, by - h * 0.80), (x + w * 0.60, by - h * 0.755), (x + w * 0.5, by - h * 0.71)], fill=RED)
    f = F("display", h * 0.44)
    draw_text(d, (x + w * 0.71, y + h * 0.05), "258", f, fill=NAVY)


def ill_village(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(216, 206, 178))
    for hx, hw in ((0.08, 0.30), (0.58, 0.34)):
        bx = x + w * hx
        rect(d, (bx, y + h * 0.44, bx + w * hw, y + h * 0.80), fill=(238, 232, 214))
        poly(d, [(bx - w * 0.02, y + h * 0.44), (bx + w * hw / 2, y + h * 0.26), (bx + w * hw + w * 0.02, y + h * 0.44)], fill=(150, 96, 62))
        rect(d, (bx + w * hw * 0.38, y + h * 0.58, bx + w * hw * 0.62, y + h * 0.80), fill=(110, 84, 60))
    tx = x + w * 0.47
    rect(d, (tx, y + h * 0.48, tx + w * 0.03, y + h * 0.80), fill=(110, 84, 60))
    for cx, cy, cr in ((0.44, 0.30, 0.075), (0.53, 0.26, 0.09), (0.50, 0.38, 0.08)):
        ellipse(d, (x + w * cx - w * cr, y + h * cy - w * cr, x + w * cx + w * cr, y + h * cy + w * cr), fill=(86, 128, 66))
    rect(d, (x + w * 0.66, y + h * 0.70, x + w * 0.94, y + h * 0.84), fill=(70, 74, 82))
    ellipse(d, (x + w * 0.70, y + h * 0.80, x + w * 0.76, y + h * 0.80 + w * 0.06), fill=(30, 30, 32))
    ellipse(d, (x + w * 0.85, y + h * 0.80, x + w * 0.91, y + h * 0.80 + w * 0.06), fill=(30, 30, 32))
    poly(d, [(x + w * 0.76, y + h * 0.70), (x + w * 0.80, y + h * 0.50), (x + w * 0.84, y + h * 0.70)], fill=(238, 128, 42))
    poly(d, [(x + w * 0.78, y + h * 0.70), (x + w * 0.80, y + h * 0.58), (x + w * 0.82, y + h * 0.70)], fill=(246, 196, 64))
    rect(d, (x, y + h * 0.86, x + w, y + h), fill=(168, 156, 128))


def ill_boat(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(190, 216, 226))
    rect(d, (x, y + h * 0.30, x + w, y + h), fill=SEA)
    for i in range(4):
        arc(d, (x + w * (0.05 + 0.24 * i), y + h * 0.66, x + w * (0.22 + 0.24 * i), y + h * 0.84), 180, 360, fill=(240, 246, 248), width=1.6)
    poly(d, [(x + w * 0.18, y + h * 0.52), (x + w * 0.82, y + h * 0.52), (x + w * 0.68, y + h * 0.38), (x + w * 0.32, y + h * 0.38)], fill=(146, 96, 58))
    line(d, [(x + w * 0.24, y + h * 0.45), (x + w * 0.76, y + h * 0.45)], fill=(110, 70, 40), width=2)
    for px_ in (0.38, 0.55):
        ellipse(d, (x + w * px_, y + h * 0.60, x + w * px_ + w * 0.10, y + h * 0.60 + w * 0.10), outline=(250, 250, 246), width=3)
        ellipse(d, (x + w * px_, y + h * 0.60, x + w * px_ + w * 0.10, y + h * 0.60 + w * 0.10), outline=RED, width=1.4)
    ellipse(d, (x + w * 0.80, y + h * 0.16, x + w * 0.88, y + h * 0.16 + w * 0.08), outline=INK, width=1.4)


def ill_cricket(d, x, y, w, h):
    rect(d, (x, y, x + w, y + h), fill=(120, 178, 96))
    rect(d, (x + w * 0.30, y + h * 0.10, x + w * 0.52, y + h * 0.90), fill=(226, 208, 168))
    for i in range(3):
        sx = x + w * (0.345 + 0.045 * i)
        rect(d, (sx, y + h * 0.58, sx + w * 0.016, y + h * 0.84), fill=(240, 234, 210))
    rect(d, (x + w * 0.345, y + h * 0.565, x + w * 0.435, y + h * 0.585), fill=(240, 234, 210))
    poly(d, [(x + w * 0.60, y + h * 0.86), (x + w * 0.66, y + h * 0.86), (x + w * 0.60, y + h * 0.34), (x + w * 0.545, y + h * 0.34)], fill=(214, 188, 138), outline=INK)
    ellipse(d, (x + w * 0.70, y + h * 0.30, x + w * 0.70 + w * 0.075, y + h * 0.30 + w * 0.075), fill=RED)
    f = F("display", h * 0.42)
    draw_text(d, (x + w * 0.56, y + h * 0.06), "720", f, fill=(252, 250, 240))


ILLUSTRATIONS = {
    "climate": ill_climate, "ship": ill_ship, "mercury": ill_mercury,
    "missile": ill_missile, "building": ill_building, "gulf": ill_gulf,
    "desert": ill_desert, "factory": ill_factory, "football": ill_football,
    "tennis": ill_tennis, "moto": ill_moto, "f1": ill_f1,
    "capitol": ill_capitol, "village": ill_village, "boat": ill_boat,
    "cricket": ill_cricket,
}


# ------------------------------------------------------------------ layout

def number_badge(d, x, y, n, size=15):
    rect(d, (x, y, x + size, y + size), fill=RED)
    f = F("sans_b", size * 0.62)
    draw_text(d, (x + size / 2, y + size * 0.10), str(n), f, fill=(252, 250, 240), anchor="ma")


def meta_line(d, x, y, story, maxw, size=7.4):
    f = F("sans_b", size)
    label = story["label"]
    draw_text(d, (x, y), label, f, fill=LABEL_COLORS[label])
    lx = x + tw(d, label, f) + 4
    f2 = F("sans", size)
    src = story.get("source", "")
    while src and tw(d, src, f2) > maxw - (lx - x):
        src = src[:-2]
    draw_text(d, (lx, y), src, f2, fill=GREY)


def hero_card(d, x, y, w, h, n, story):
    rect(d, (x, y, x + w, y + h), fill=PAPER, outline=INK, width=1.1)
    pad = 7
    ILLUSTRATIONS[story["icon"]](d, x + pad, y + pad, w - 2 * pad, 84)
    number_badge(d, x + pad, y + pad, n, 16)
    hy = y + pad + 84 + 5
    f = F("serif_b", 14.5)
    for ln in wrap(d, story["headline"], f, w - 2 * pad)[:2]:
        draw_text(d, (x + pad, hy), ln, f)
        hy += 17.5
    hy += 2
    f = F("serif", 9.2)
    for ln in wrap(d, story["dek"], f, w - 2 * pad)[:4]:
        draw_text(d, (x + pad, hy), ln, f)
        hy += 11.8
    meta_line(d, x + pad, y + h - 13, story, w - 2 * pad - 4)
    fp = F("sans_b", 7.4)
    place = story["place"].upper()
    draw_text(d, (x + w - pad - tw(d, place, fp), y + h - 13), place, fp, fill=GREY)


def grid_card(d, x, y, w, h, n, story, ill_h):
    rect(d, (x, y, x + w, y + h), fill=PAPER, outline=RULE, width=1)
    pad = 5
    ILLUSTRATIONS[story["icon"]](d, x + pad, y + pad, w - 2 * pad, ill_h)
    number_badge(d, x + pad, y + pad, n, 13)
    hy = y + pad + ill_h + 4
    f = F("serif_b", 10.2)
    for ln in wrap(d, story["headline"], f, w - 2 * pad)[:3]:
        draw_text(d, (x + pad, hy), ln, f)
        hy += 12.2
    meta_line(d, x + pad, y + h - 11.5, story, w - 2 * pad - 2, size=6.6)


def render(data):
    stories = data["stories"]
    total = len(stories)
    drawn = [s for s in stories if s["kind"] in ("hero", "card")]
    regions = {}
    for s in stories:
        regions[s["region"]] = regions.get(s["region"], 0) + 1
    fields = len({s["field"] for s in stories})

    img = Image.new("RGB", (X(W), X(H)), CREAM)
    d = ImageDraw.Draw(img)

    # top strip
    rect(d, (0, 0, W, 20), fill=RED)
    f = F("sans_b", 9.5)
    draw_text(d, (MARGIN, 4.5), "THE WORLD IN ONE IMAGE - DAILY BROADSHEET", f, fill=(252, 246, 230))
    right = "make.fun/bounty/news-image-20261122"
    draw_text(d, (W - MARGIN - tw(d, right, f), 4.5), right, f, fill=(252, 246, 230))

    # masthead
    rect(d, (0, 20, W, 112), fill=NAVY)
    f = F("sans_b", 11)
    t = "T H E   W O R L D   I N   O N E   I M A G E"
    draw_text(d, (W / 2 - tw(d, t, f) / 2, 27), t, f, fill=GOLD)
    f = F("display", 55)
    t = data["day"]
    draw_text(d, (W / 2 - tw(d, t, f) / 2, 44), t, f, fill=(250, 246, 228))

    # promise strip
    rect(d, (0, 112, W, 138), fill=GOLD)
    f = F("sans_b", 13.5)
    t = "%d STORIES  •  %d REGIONS  •  %d DRAWN  •  %d FIELDS  •  ALL FROM THIS SUNDAY" % (
        total, len(regions), len(drawn), fields)
    draw_text(d, (W / 2 - tw(d, t, f) / 2, 118), t, f, fill=NAVY)

    # region strip
    order = sorted(regions.items(), key=lambda kv: -kv[1])
    names = {"North America": "N. AMERICA", "Latin America": "LATIN AMERICA",
             "Oceania & Space": "OCEANIA & SPACE"}
    f = F("sans_b", 10)
    t = "   ·   ".join("%s %d" % (names.get(k, k.upper()), v) for k, v in order)
    draw_text(d, (W / 2 - tw(d, t, f) / 2, 143), t, f, fill=INK)
    line(d, [(MARGIN, 160), (W - MARGIN, 160)], fill=INK, width=1.6)

    # heroes
    hy0, hh = 166, 186
    hw = (W - 2 * MARGIN - 16) / 3
    for i, s in enumerate([s for s in stories if s["kind"] == "hero"]):
        hero_card(d, MARGIN + i * (hw + 8), hy0, hw, hh, i + 1, s)
    line(d, [(MARGIN, 360), (W - MARGIN, 360)], fill=RULE, width=1.2)
    f = F("sans_b", 9)
    draw_text(d, (MARGIN, 363), "THE DAY DRAWN - STORIES 4-16", f, fill=GREY)

    # grid cards: row of 7, then row of 6
    cards = [s for s in stories if s["kind"] == "card"]
    gy = 378
    cw1 = (W - 2 * MARGIN - 6 * 8) / 7
    for i, s in enumerate(cards[:7]):
        grid_card(d, MARGIN + i * (cw1 + 8), gy, cw1, 106, 4 + i, s, 40)
    cw2 = (W - 2 * MARGIN - 5 * 8) / 6
    for i, s in enumerate(cards[7:]):
        grid_card(d, MARGIN + i * (cw2 + 8), gy + 114, cw2, 106, 11 + i, s, 40)

    # timeline band
    ty = 606
    rect(d, (MARGIN, ty, W - MARGIN, ty + 44), fill=PAPER, outline=RULE, width=1)
    f = F("sans_b", 9.5)
    draw_text(d, (MARGIN + 7, ty + 8), "THE DAY", f, fill=RED)
    draw_text(d, (MARGIN + 7, ty + 20), "IN UTC", f, fill=RED)
    line(d, [(MARGIN + 62, ty + 5), (MARGIN + 62, ty + 39)], fill=RULE, width=1)
    colw = (W - 2 * MARGIN - 76) / 7
    for i, (tt, tx) in enumerate(data["timeline"]):
        cx = MARGIN + 70 + i * colw
        draw_text(d, (cx, ty + 4), tt, F("sans_b", 8.6), fill=NAVY)
        yy = ty + 16
        for ln in wrap(d, tx, F("sans", 7.8), colw - 8)[:3]:
            draw_text(d, (cx, yy), ln, F("sans", 7.8), fill=INK)
            yy += 9.6

    # numbers strip
    ny = 656
    rect(d, (MARGIN, ny, W - MARGIN, ny + 34), fill=INK)
    f = F("sans_b", 9)
    draw_text(d, (MARGIN + 8, ny + 11), "THE DAY IN NUMBERS", f, fill=GOLD)
    nx = MARGIN + 128
    cellw = (W - MARGIN - nx - 6) / 6
    for i, (num, cap) in enumerate(data["numbers"]):
        cx = nx + i * cellw
        fn = F("display", 17)
        draw_text(d, (cx, ny + 3), num, fn, fill=GOLD)
        yy = ny + 23
        for ln in wrap(d, cap, F("sans", 6.9), cellw - 6)[:1]:
            draw_text(d, (cx, yy), ln, F("sans", 6.9), fill=(238, 234, 220))

    # bottom: also list (left) + map and date check (right)
    by = 700
    f = F("sans_b", 10.5)
    draw_text(d, (MARGIN, by), "ALSO ON SUNDAY", f, fill=INK)
    f2 = F("sans", 9)
    draw_text(d, (MARGIN + tw(d, "ALSO ON SUNDAY", f) + 6, by + 1), "- the rest of the day in brief, stories 17-56", f2, fill=GREY)
    line(d, [(MARGIN, by + 15), (590, by + 15)], fill=INK, width=1.2)
    lst = [s for s in stories if s["kind"] == "list"]
    half = (len(lst) + 1) // 2
    cols = [(MARGIN, lst[:half], 17), (304, lst[half:], 17 + half)]

    def item_lines(s, n, size):
        head = "%d  %s - " % (n, s["place"].upper())
        fb, fr = F("sans_b", size), F("sans", size)
        headw = tw(d, head, fb)
        lines, cur, curw = [], [], headw
        for w_ in s["text"].split():
            ww = tw(d, w_ + " ", fr)
            if curw + ww <= 282 or not cur:
                cur.append(w_)
                curw += ww
            else:
                lines.append(cur)
                cur, curw = [w_], tw(d, w_ + " ", fr)
        if cur:
            lines.append(cur)
        return head, lines

    def col_height(items, start, size):
        return sum(len(item_lines(s, start + j, size)[1]) * (size + 2.0) + 2.6
                   for j, s in enumerate(items))

    size = 9.2
    while size > 7.5 and any(by + 21 + col_height(items, start, size) > 990
                             for _, items, start in cols):
        size -= 0.4
    for cx, items, start in cols:
        yy = by + 21
        for j, s in enumerate(items):
            head, lines = item_lines(s, start + j, size)
            fb, fr = F("sans_b", size), F("sans", size)
            draw_text(d, (cx, yy), head, fb, fill=INK)
            draw_text(d, (cx + tw(d, head, fb), yy), " ".join(lines[0]), fr, fill=INK)
            yy += size + 2.0
            for ln in lines[1:]:
                draw_text(d, (cx, yy), " ".join(ln), fr, fill=INK)
                yy += size + 2.0
            yy += 2.6

    # map
    mx0, my0, mw, mh = 598, by, 416, 168
    rect(d, (mx0, my0, mx0 + mw, my0 + mh), fill=(238, 233, 210), outline=RULE, width=1)
    f = F("sans_b", 8.6)
    draw_text(d, (mx0 + 7, my0 + 4), "WHERE IT HAPPENED - PIN NUMBERS MATCH THE STORIES", f, fill=NAVY)
    gx, gy2, gw, gh = mx0 + 8, my0 + 18, mw - 16, mh - 26
    cellw2, cellh2 = gw / 90, gh / 44
    for r, spans in LAND.items():
        for c0, c1 in spans:
            for c in range(c0, c1 + 1):
                rect(d, (gx + c * cellw2 + 0.4, gy2 + r * cellh2 + 0.4,
                         gx + (c + 1) * cellw2 - 0.4, gy2 + (r + 1) * cellh2 - 0.4),
                     fill=(168, 172, 158))

    def pin_xy(lon, lat):
        return (gx + (lon + 168) / 360 * gw, gy2 + (76 - lat) / 140 * gh)

    for s in lst:
        if s["lon"] is not None:
            px_, py_ = pin_xy(s["lon"], s["lat"])
            ellipse(d, (px_ - 1.7, py_ - 1.7, px_ + 1.7, py_ + 1.7), fill=(90, 88, 80))
    placed = []
    offsets = [(0, 0), (10, -7), (-10, -7), (10, 8), (-10, 8), (0, -12), (0, 12), (13, 0), (-13, 0)]
    for i, s in enumerate(drawn):
        px_, py_ = pin_xy(s["lon"], s["lat"])
        for ox, oy in offsets:
            cand = (px_ + ox, py_ + oy)
            if all((cand[0] - q[0]) ** 2 + (cand[1] - q[1]) ** 2 >= 121 for q in placed):
                px_, py_ = cand
                break
        placed.append((px_, py_))
        r = 7.2
        ellipse(d, (px_ - r, py_ - r, px_ + r, py_ + r), fill=RED, outline=(252, 250, 240), width=1.2)
        fn = F("sans_b", 7.6)
        draw_text(d, (px_, py_ - 3.6), str(i + 1), fn, fill=(252, 250, 240), anchor="ma")

    # date check
    dy0 = by + 178
    rect(d, (mx0, dy0, mx0 + mw, 990), fill=PAPER, outline=RED, width=1.4)
    f = F("sans_b", 9.6)
    draw_text(d, (mx0 + 8, dy0 + 5), "DATE CHECK - NOT SUNDAY, SO NOT HEADLINES", f, fill=RED)
    yy = dy0 + 21
    for item in data["date_check"]:
        lines = wrap(d, item, F("serif", 8.8), mw - 30)
        draw_text(d, (mx0 + 8, yy), "x", F("sans_b", 8.8), fill=RED)
        for ln in lines:
            draw_text(d, (mx0 + 20, yy), ln, F("serif", 8.8), fill=INK)
            yy += 11
        yy += 2.5

    # footer
    line(d, [(MARGIN, 994), (W - MARGIN, 994)], fill=INK, width=1.2)
    f = F("sans", 7.6)
    draw_text(d, (MARGIN, 999), "Sources: Reuters - AP - BBC - AFP - Al Jazeera - ATP - MotoGP - Formula 1 - Kyiv Independent - ESA - Premier League. Every story dated Sunday 22 Nov 2026.", f, fill=GREY)
    t = "Original drawings - drawn by this program from stories.json"
    draw_text(d, (W - MARGIN - tw(d, t, f), 1009), t, f, fill=GREY)
    draw_text(d, (MARGIN, 1009), "Labels: CONFIRMED = multiple outlets - REPORTED = single wire/OSINT - CLAIM = one side's account - OFFICIAL = official tally", f, fill=GREY)

    return img.resize((W, H), Image.LANCZOS)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    data_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "stories.json")
    with open(data_path, encoding="utf-8") as fh:
        data = json.load(fh)
    img = render(data)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(out_dir, exist_ok=True)
        img.save(os.path.join(out_dir, "entry.png"))
    except OSError:
        img.save(os.path.join(here, "entry.png"))
    try:
        img.save(os.path.join(here, "poster.png"))
    except OSError:
        pass
    print("wrote entry.png", img.size)


if __name__ == "__main__":
    main()
