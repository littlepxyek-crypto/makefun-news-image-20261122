#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Illustration library for the news-image-20261122 broadsheet entry.

Every picture on the poster is an original flat-vector drawing produced
procedurally with PIL: no stock art, no traced photographs. Each routine
receives a design-space box (x, y, w, h) on the 1024x1024 page and paints
inside it. Coordinates are design units; the primitives below scale them
by the supersample factor S so the final render stays crisp.

The library is deliberately layered: skies are stacked colour bands,
buildings carry window grids and lit panes, the sea gets wave arcs and
reflections, and the night sky uses a deterministic linear congruential
generator for its stars so the output PNG is byte-for-byte reproducible.
"""
import math

from PIL import ImageFont

S = 2                      # supersample factor, shared with main.py
W = H = 1024

# ---------------------------------------------------------------- palette
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
SKY_DEEP = (172, 198, 216)
DUSK_TOP = (38, 52, 92)
DUSK_MID = (104, 96, 116)
DUSK_LOW = (232, 148, 92)
SAND = (232, 196, 138)
SAND_DARK = (206, 164, 102)
OLIVE = (96, 122, 62)
LEAF = (70, 110, 54)
BRICK = (168, 92, 62)
STEEL = (96, 104, 116)
STEEL_DARK = (58, 64, 74)
GLASS = (120, 156, 178)
LIT = (250, 214, 120)
FLAME_OUT = (232, 110, 36)
FLAME_MID = (246, 168, 52)
FLAME_IN = (252, 226, 150)
SMOKE = (148, 144, 136)
SMOKE_LT = (196, 192, 182)
NIGHT = (18, 24, 48)
PANEL_BLUE = (52, 92, 168)
WHITE = (252, 250, 240)

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
    d.line([(X(px), X(py)) for px, py in pts], fill=fill,
           width=max(1, int(width * S)))


def ellipse(d, box, fill=None, outline=None, width=1):
    d.ellipse([X(box[0]), X(box[1]), X(box[2]), X(box[3])],
              fill=fill, outline=outline, width=max(1, int(width * S)))


def poly(d, pts, fill=None, outline=None):
    d.polygon([(X(px), X(py)) for px, py in pts], fill=fill, outline=outline)


def arc(d, box, a0, a1, fill=INK, width=1):
    d.arc([X(box[0]), X(box[1]), X(box[2]), X(box[3])], a0, a1,
          fill=fill, width=max(1, int(width * S)))


def chord(d, box, a0, a1, fill=None, outline=None, width=1):
    d.chord([X(box[0]), X(box[1]), X(box[2]), X(box[3])], a0, a1,
            fill=fill, outline=outline, width=max(1, int(width * S)))


# ------------------------------------------------------- shared techniques

def bands(d, x, y, w, h, colors):
    """Stack horizontal colour bands (a flat-design sky or sea gradient)."""
    n = len(colors)
    for i, c in enumerate(colors):
        rect(d, (x, y + h * i / n, x + w, y + h * (i + 1) / n + 0.6), fill=c)


def lcg(seed):
    """Deterministic pseudo-random stream in [0, 1); same seed, same art."""
    state = seed & 0x7FFFFFFF
    while True:
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        yield state / 0x7FFFFFFF


def starfield(d, x, y, w, h, count, seed, max_r=1.5):
    rnd = lcg(seed)
    for _ in range(count):
        sx = x + next(rnd) * w
        sy = y + next(rnd) * h
        r = 0.5 + next(rnd) * max_r
        tone = 200 + int(next(rnd) * 55)
        ellipse(d, (sx - r, sy - r, sx + r, sy + r), fill=(tone, tone, tone - 12))
        if r > 1.25:  # the brightest few get a cross sparkle
            line(d, [(sx - r * 2.2, sy), (sx + r * 2.2, sy)],
                 fill=(tone, tone, tone - 12), width=0.7)
            line(d, [(sx, sy - r * 2.2), (sx, sy + r * 2.2)],
                 fill=(tone, tone, tone - 12), width=0.7)


def cloud(d, cx, cy, scale, fill):
    """One flat cumulus puff built from overlapping ellipses."""
    for ox, oy, r in ((-0.9, 0.18, 0.52), (-0.3, -0.10, 0.72),
                      (0.35, -0.02, 0.62), (0.85, 0.20, 0.46), (0.0, 0.26, 0.66)):
        ellipse(d, (cx + (ox - r) * scale, cy + (oy - r * 0.62) * scale,
                    cx + (ox + r) * scale, cy + (oy + r * 0.62) * scale), fill=fill)
    rect(d, (cx - 1.35 * scale, cy + 0.05 * scale,
             cx + 1.3 * scale, cy + 0.34 * scale), fill=fill)


def smoke_plume(d, bx, by, w, h, tones=(SMOKE_LT, SMOKE)):
    """A rising plume: widening puffs drifting sideways as they climb."""
    steps = 7
    for i in range(steps):
        t = i / (steps - 1)
        cx = bx + w * 0.34 * t * t + w * 0.05 * math.sin(t * 5.0)
        cy = by - h * t
        r = w * (0.10 + 0.16 * t)
        cloud(d, cx, cy, r, tones[i % len(tones)])


def flame(d, cx, base, w, h):
    """A three-layer teardrop flame: outer, mid and bright core."""
    for fw, fh, c in ((1.0, 1.0, FLAME_OUT), (0.66, 0.74, FLAME_MID),
                      (0.36, 0.46, FLAME_IN)):
        pts = []
        for k in range(13):
            t = k / 12
            ang = math.pi * t
            px = cx + math.cos(ang) * w * fw * 0.5 * (0.35 + 0.65 * math.sin(ang))
            py = base - fh * h * math.sin(ang) ** 0.7
            pts.append((px, py))
        pts.append((cx + w * fw * 0.5, base))
        pts.append((cx - w * fw * 0.5, base))
        poly(d, pts, fill=c)


def wave_row(d, x, y, w, count, r, color, width=1.4):
    for i in range(count):
        cx = x + w * (i + 0.5) / count
        arc(d, (cx - r, y - r * 0.55, cx + r, y + r * 0.55), 180, 360,
            fill=color, width=width)


def window_grid(d, bx, by, bw, bh, cols, rows, lit_every=0, seed=7,
                dark=(86, 100, 114), lit=LIT):
    """A facade of small windows; every Nth pane glows if lit_every > 0."""
    rnd = lcg(seed)
    cw, ch = bw / cols, bh / rows
    for r in range(rows):
        for c in range(cols):
            glow = lit_every and next(rnd) < lit_every
            rect(d, (bx + c * cw + cw * 0.18, by + r * ch + ch * 0.18,
                     bx + (c + 1) * cw - cw * 0.18, by + (r + 1) * ch - ch * 0.18),
                 fill=lit if glow else dark)


def spark_dots(d, cx, base, w, h, count, seed):
    rnd = lcg(seed)
    for _ in range(count):
        sx = cx + (next(rnd) - 0.5) * w
        sy = base - next(rnd) * h
        r = 0.5 + next(rnd) * 0.9
        ellipse(d, (sx - r, sy - r, sx + r, sy + r), fill=FLAME_MID)


# ------------------------------------------------------------------ heroes

def ill_climate(d, x, y, w, h):
    """COP31, Antalya: conference hall, flags, chimneys and a rejected draft."""
    bands(d, x, y, w, h * 0.72, [(196, 216, 228), (214, 228, 235), (228, 236, 238)])
    # low sun and its rays, top right
    sx, sy, sr = x + w * 0.90, y + h * 0.16, w * 0.045
    for k in range(8):
        a = math.radians(k * 45 + 10)
        line(d, [(sx + sr * 1.25 * math.cos(a), sy + sr * 1.25 * math.sin(a)),
                 (sx + sr * 1.9 * math.cos(a), sy + sr * 1.9 * math.sin(a))],
             fill=(240, 190, 90), width=1.6)
    ellipse(d, (sx - sr, sy - sr, sx + sr, sy + sr), fill=(246, 200, 84))
    cloud(d, x + w * 0.16, y + h * 0.14, w * 0.05, WHITE)
    cloud(d, x + w * 0.55, y + h * 0.09, w * 0.038, WHITE)
    # sea and the Antalya headland
    rect(d, (x, y + h * 0.72, x + w, y + h), fill=SEA)
    wave_row(d, x + w * 0.03, y + h * 0.82, w * 0.94, 7, w * 0.018, (240, 246, 248))
    poly(d, [(x, y + h * 0.72), (x + w * 0.30, y + h * 0.60),
             (x + w * 0.46, y + h * 0.72)], fill=(148, 156, 132))
    # twin chimneys with smoke, far left
    for i, cx in enumerate((0.055, 0.115)):
        bx = x + w * cx
        rect(d, (bx, y + h * 0.40, bx + w * 0.035, y + h * 0.72), fill=(104, 100, 94))
        rect(d, (bx - w * 0.006, y + h * 0.40, bx + w * 0.041, y + h * 0.45), fill=RED)
        smoke_plume(d, bx + w * 0.017, y + h * 0.36, w * 0.10, h * 0.30)
    # the conference hall: glass front, dome, entrance steps
    hx, hy, hw, hh = x + w * 0.34, y + h * 0.38, w * 0.40, h * 0.34
    rect(d, (hx, hy, hx + hw, hy + hh), fill=(238, 234, 222), outline=INK, width=1.1)
    window_grid(d, hx + hw * 0.05, hy + hh * 0.14, hw * 0.9, hh * 0.62, 9, 3,
                dark=GLASS)
    chord(d, (hx + hw * 0.28, hy - hh * 0.52, hx + hw * 0.72, hy + hh * 0.30),
          180, 360, fill=NAVY2, outline=INK, width=1)
    line(d, [(hx + hw * 0.5, hy - hh * 0.52), (hx + hw * 0.5, hy - hh * 0.72)],
         fill=INK, width=1.4)
    poly(d, [(hx + hw * 0.5, hy - hh * 0.72), (hx + hw * 0.60, hy - hh * 0.655),
             (hx + hw * 0.5, hy - hh * 0.59)], fill=GOLD)
    rect(d, (hx - hw * 0.04, hy + hh, hx + hw * 1.04, hy + hh * 1.10), fill=(196, 188, 168))
    # a row of delegation flags in front of the hall
    for i, fc in enumerate((TEAL, RED, GOLD, NAVY2, (52, 128, 62), (120, 60, 140))):
        fx = hx + hw * (0.06 + 0.155 * i)
        line(d, [(fx, hy + hh * 1.10), (fx, hy + hh * 0.52)], fill=STEEL_DARK, width=1.1)
        poly(d, [(fx, hy + hh * 0.52), (fx + hw * 0.085, hy + hh * 0.575),
                 (fx, hy + hh * 0.65)], fill=fc)
    # the rejected draft, big at the right, with the red no-deal seal
    dx, dy, dw, dh = x + w * 0.80, y + h * 0.34, w * 0.155, h * 0.52
    poly(d, [(dx + dw * 0.10, dy + dh * 0.05), (dx + dw, dy + dh * 0.05),
             (dx + dw * 0.92, dy + dh), (dx, dy + dh * 0.94)], fill=WHITE, outline=INK)
    for k in range(4):
        line(d, [(dx + dw * 0.14, dy + dh * (0.22 + 0.15 * k)),
                 (dx + dw * 0.82, dy + dh * (0.20 + 0.15 * k))], fill=GREY, width=1.1)
    cxr, cyr, rr = dx + dw * 0.48, dy + dh * 0.47, dw * 0.34
    ellipse(d, (cxr - rr, cyr - rr, cxr + rr, cyr + rr), outline=RED, width=2.6)
    line(d, [(cxr - rr * 0.72, cyr + rr * 0.72), (cxr + rr * 0.72, cyr - rr * 0.72)],
         fill=RED, width=2.6)


def ill_ship(d, x, y, w, h):
    """Benghazi: a burning corvette, a freighter behind, a sea drone's sights."""
    bands(d, x, y, w, h * 0.60, [DUSK_TOP, DUSK_MID, DUSK_LOW])
    starfield(d, x + w * 0.03, y + h * 0.03, w * 0.6, h * 0.3, 26, seed=41, max_r=1.0)
    rect(d, (x, y + h * 0.60, x + w, y + h), fill=(58, 92, 122))
    wave_row(d, x + w * 0.02, y + h * 0.80, w * 0.96, 9, w * 0.016, (170, 205, 225))
    wave_row(d, x + w * 0.05, y + h * 0.92, w * 0.90, 8, w * 0.014, (140, 180, 205))
    # distant freighter silhouette, right, with stacked containers
    fx, fy = x + w * 0.70, y + h * 0.52
    poly(d, [(fx, fy), (fx + w * 0.26, fy), (fx + w * 0.22, fy + h * 0.09),
             (fx + w * 0.03, fy + h * 0.09)], fill=(40, 48, 62))
    for i, cc in enumerate(((150, 90, 70), (70, 110, 130), (120, 120, 90))):
        rect(d, (fx + w * (0.05 + 0.055 * i), fy - h * 0.075,
                 fx + w * (0.10 + 0.055 * i), fy), fill=cc)
    rect(d, (fx + w * 0.225, fy - h * 0.11, fx + w * 0.25, fy), fill=(40, 48, 62))
    # the corvette: hull, deck, superstructure, mast, turret
    hx, hy = x + w * 0.07, y + h * 0.55
    poly(d, [(hx, hy), (hx + w * 0.52, hy), (hx + w * 0.585, hy + h * 0.075),
             (hx + w * 0.47, hy + h * 0.155), (hx + w * 0.05, hy + h * 0.155)],
         fill=(70, 78, 90))
    rect(d, (hx, hy + h * 0.115, hx + w * 0.50, hy + h * 0.135), fill=RED)
    rect(d, (hx + w * 0.16, hy - h * 0.10, hx + w * 0.34, hy), fill=(88, 96, 108))
    window_grid(d, hx + w * 0.185, hy - h * 0.085, w * 0.13, h * 0.055, 5, 1,
                lit_every=0.8, seed=9, dark=(40, 48, 60))
    rect(d, (hx + w * 0.36, hy - h * 0.065, hx + w * 0.43, hy), fill=(88, 96, 108))
    line(d, [(hx + w * 0.245, hy - h * 0.10), (hx + w * 0.245, hy - h * 0.24)],
         fill=INK, width=1.8)
    line(d, [(hx + w * 0.185, hy - h * 0.225), (hx + w * 0.305, hy - h * 0.225)],
         fill=INK, width=2.2)  # radar bar
    ellipse(d, (hx + w * 0.245 - 2.2, hy - h * 0.265, hx + w * 0.245 + 2.2,
                hy - h * 0.245), fill=LIT)
    poly(d, [(hx + w * 0.03, hy - h * 0.015), (hx + w * 0.10, hy - h * 0.055),
             (hx + w * 0.13, hy - h * 0.015)], fill=(88, 96, 108))  # fore turret
    line(d, [(hx + w * 0.115, hy - h * 0.045), (hx + w * 0.175, hy - h * 0.075)],
         fill=INK, width=2)  # gun barrel
    for i in range(3):  # missile cells aft
        rect(d, (hx + w * (0.455 + 0.02 * i), hy - h * 0.05,
                 hx + w * (0.47 + 0.02 * i), hy), fill=STEEL_DARK)
    # fire amidships: starburst, layered flame, smoke, sea reflection
    fx2, fy2 = hx + w * 0.40, hy - h * 0.05
    pts = []
    for i in range(12):
        ang = math.radians(i * 30)
        r = w * (0.075 if i % 2 == 0 else 0.034)
        pts.append((fx2 + r * math.cos(ang), fy2 + r * math.sin(ang) * 0.75))
    poly(d, pts, fill=FLAME_OUT)
    flame(d, fx2, fy2 + h * 0.03, w * 0.055, h * 0.30)
    smoke_plume(d, fx2, fy2 - h * 0.16, w * 0.09, h * 0.34, tones=((70, 68, 66), SMOKE))
    for k in range(4):
        line(d, [(fx2 - w * 0.03 + k * w * 0.018, y + h * 0.70),
                 (fx2 - w * 0.015 + k * w * 0.018, y + h * 0.70)],
             fill=(240, 160, 80), width=1.6)
    # the sea drone in the sights, lower left
    dx, dy = x + w * 0.115, y + h * 0.30
    ellipse(d, (dx - w * 0.045, dy - w * 0.045, dx + w * 0.045, dy + w * 0.045),
            outline=(240, 240, 230), width=1.5)
    line(d, [(dx - w * 0.065, dy), (dx - w * 0.02, dy)], fill=(240, 240, 230), width=1.5)
    line(d, [(dx + w * 0.02, dy), (dx + w * 0.065, dy)], fill=(240, 240, 230), width=1.5)
    line(d, [(dx, dy - w * 0.065), (dx, dy - w * 0.02)], fill=(240, 240, 230), width=1.5)
    line(d, [(dx, dy + w * 0.02), (dx, dy + w * 0.065)], fill=(240, 240, 230), width=1.5)
    poly(d, [(dx - w * 0.016, dy + w * 0.008), (dx + w * 0.02, dy + w * 0.008),
             (dx + w * 0.012, dy - w * 0.012), (dx - w * 0.008, dy - w * 0.012)],
         fill=(30, 34, 42))


def ill_mercury(d, x, y, w, h):
    """BepiColombo: the probe, its panel grids, Mercury and a dashed orbit."""
    rect(d, (x, y, x + w, y + h), fill=(16, 22, 46))
    starfield(d, x, y, w, h, 110, seed=97)
    rnd = lcg(1234)  # a faint milky-way band of dust dots
    for _ in range(70):
        t = next(rnd)
        sx = x + w * t
        sy = y + h * (0.16 + 0.5 * t) + (next(rnd) - 0.5) * h * 0.10
        r = 0.4 + next(rnd) * 0.7
        ellipse(d, (sx - r, sy - r, sx + r, sy + r), fill=(120, 128, 160))
    # the sun, top-left, ringed and rayed
    sx, sy, sr = x + w * 0.085, y + h * 0.20, w * 0.038
    ellipse(d, (sx - sr * 1.7, sy - sr * 1.7, sx + sr * 1.7, sy + sr * 1.7),
            outline=(150, 120, 60), width=1.2)
    for k in range(8):
        a = math.radians(k * 45 + 20)
        line(d, [(sx + sr * 1.15 * math.cos(a), sy + sr * 1.15 * math.sin(a)),
                 (sx + sr * 1.55 * math.cos(a), sy + sr * 1.55 * math.sin(a))],
             fill=(246, 200, 84), width=1.8)
    ellipse(d, (sx - sr, sy - sr, sx + sr, sy + sr), fill=(246, 200, 84))
    # Mercury: cratered disc with a flat terminator shadow
    mx, my, mr = x + w * 0.76, y + h * 0.60, w * 0.155
    ellipse(d, (mx - mr, my - mr, mx + mr, my + mr), fill=(172, 164, 150))
    for cx, cy, cr, tone in ((0.30, 0.34, 0.17, (150, 142, 126)),
                             (0.60, 0.58, 0.12, (156, 148, 130)),
                             (0.44, 0.74, 0.085, (150, 142, 126)),
                             (0.72, 0.30, 0.075, (158, 150, 132)),
                             (0.20, 0.62, 0.06, (158, 150, 132))):
        ox, oy = mx + mr * (cx * 2 - 1), my + mr * (cy * 2 - 1)
        ellipse(d, (ox - mr * cr, oy - mr * cr, ox + mr * cr, oy + mr * cr), fill=tone)
        arc(d, (ox - mr * cr, oy - mr * cr, ox + mr * cr, oy + mr * cr), 200, 330,
            fill=(196, 190, 174), width=1.1)
    chord(d, (mx - mr, my - mr, mx + mr * 0.35, my + mr), 90, 270, fill=(104, 98, 88))
    # dashed transfer orbit sweeping past the planet
    for a0 in range(196, 420, 18):
        arc(d, (mx - mr * 1.55, my - mr * 1.30, mx + mr * 1.55, my + mr * 1.30),
            a0, a0 + 9, fill=GOLD, width=2)
    # the spacecraft: gold bus, two gridded panel wings, dish, thruster glow
    bx, by = x + w * 0.335, y + h * 0.46
    for side in (-1, 1):
        px0 = bx + side * w * 0.035
        px1 = bx + side * w * 0.185
        poly(d, [(min(px0, px1), by - h * 0.13), (max(px0, px1), by - h * 0.20),
                 (max(px0, px1), by + h * 0.10), (min(px0, px1), by + h * 0.05)],
             fill=PANEL_BLUE, outline=(150, 180, 230))
        for g in range(1, 5):
            t = g / 5
            line(d, [(px0 + (px1 - px0) * t, by - h * 0.13 - h * 0.07 * t * side * side),
                     (px0 + (px1 - px0) * t, by + h * 0.05 + h * 0.05 * t)],
                 fill=(150, 180, 230), width=0.8)
        for g in range(1, 3):
            t = g / 3
            line(d, [(min(px0, px1), by - h * (0.13 + 0.07 * (0 if side < 0 else 1)) + h * 0.30 * t),
                     (max(px0, px1), by - h * 0.20 + h * 0.30 * t)],
                 fill=(150, 180, 230), width=0.8)
    rect(d, (bx - w * 0.035, by - h * 0.10, bx + w * 0.035, by + h * 0.10),
         fill=GOLD, outline=INK, width=1)
    rect(d, (bx - w * 0.035, by - h * 0.02, bx + w * 0.035, by + h * 0.012),
         fill=(160, 120, 40))
    ellipse(d, (bx - w * 0.020, by - h * 0.30, bx + w * 0.020, by - h * 0.10),
            outline=(232, 232, 224), width=1.8)  # high-gain dish
    line(d, [(bx, by - h * 0.10), (bx, by - h * 0.20)], fill=(232, 232, 224), width=1.4)
    poly(d, [(bx - w * 0.012, by + h * 0.10), (bx + w * 0.012, by + h * 0.10),
             (bx, by + h * 0.20)], fill=(140, 200, 250))  # thruster plume
    # distant Earth, a small blue marble
    ex, ey, er = x + w * 0.565, y + h * 0.16, w * 0.016
    ellipse(d, (ex - er, ey - er, ex + er, ey + er), fill=(86, 140, 210))
    ellipse(d, (ex - er * 0.4, ey - er * 0.5, ex + er * 0.3, ey + er * 0.1),
            fill=(90, 170, 110))


# ------------------------------------------------------------------- cards

def ill_missile(d, x, y, w, h):
    """Kryvyi Rih: tower blocks, a missile on its arc, the burst at impact."""
    bands(d, x, y, w, h * 0.80, [(206, 200, 182), (226, 218, 198), (236, 228, 208)])
    cloud(d, x + w * 0.14, y + h * 0.16, w * 0.035, (240, 236, 224))
    # apartment skyline with lit windows; the struck block is third along
    blocks = ((0.02, 0.34, 0.13), (0.17, 0.46, 0.15), (0.34, 0.30, 0.14),
              (0.50, 0.42, 0.13), (0.65, 0.36, 0.15), (0.82, 0.44, 0.16))
    for i, (bx, bh, bw) in enumerate(blocks):
        bxw = x + w * bx
        rect(d, (bxw, y + h * (0.80 - bh), bxw + w * bw, y + h * 0.80),
             fill=(104, 100, 92) if i != 2 else (88, 84, 78))
        window_grid(d, bxw + w * 0.012, y + h * (0.80 - bh) + 2,
                    w * bw - w * 0.024, h * bh - 4, 3, 4,
                    lit_every=0.35, seed=20 + i, dark=(70, 68, 62))
    # jagged broken crown on the struck block
    bx2 = x + w * 0.34
    poly(d, [(bx2, y + h * 0.50), (bx2 + w * 0.035, y + h * 0.44),
             (bx2 + w * 0.07, y + h * 0.52), (bx2 + w * 0.105, y + h * 0.45),
             (bx2 + w * 0.14, y + h * 0.50)], fill=(236, 228, 208))
    rect(d, (x, y + h * 0.80, x + w, y + h), fill=(110, 104, 94))
    # the missile, nose down at 38 degrees, smoke rings trailing behind
    cx, cy = x + w * 0.60, y + h * 0.30
    ang = math.radians(38)
    dx, dy = math.cos(ang), math.sin(ang)
    px, py = -dy, dx
    L, Wd = w * 0.30, w * 0.062
    nose = (cx + dx * L / 2, cy + dy * L / 2)
    tail = (cx - dx * L / 2, cy - dy * L / 2)
    for k in range(5):  # smoke trail
        t = (k + 1) / 5
        sx = tail[0] - dx * w * 0.16 * t
        sy = tail[1] - dy * w * 0.16 * t - h * 0.05 * t
        r = w * (0.014 + 0.02 * t)
        ellipse(d, (sx - r, sy - r * 0.7, sx + r, sy + r * 0.7), fill=SMOKE_LT)
    poly(d, [(tail[0] + px * Wd / 2, tail[1] + py * Wd / 2), (nose[0], nose[1]),
             (tail[0] - px * Wd / 2, tail[1] - py * Wd / 2)],
         fill=(216, 214, 204), outline=INK)
    poly(d, [(tail[0] + px * Wd * 0.2, tail[1] + py * Wd * 0.2),
             (tail[0] - dx * w * 0.055 + px * w * 0.045, tail[1] - dy * w * 0.055 + py * w * 0.045),
             (tail[0] - dx * w * 0.02, tail[1] - dy * w * 0.02)], fill=RED)  # fin
    poly(d, [(tail[0] - px * Wd * 0.2, tail[1] - py * Wd * 0.2),
             (tail[0] - dx * w * 0.055 - px * w * 0.045, tail[1] - dy * w * 0.055 - py * w * 0.045),
             (tail[0] - dx * w * 0.02, tail[1] - dy * w * 0.02)], fill=RED)  # fin
    flame(d, tail[0] - dx * w * 0.012, tail[1] - dy * w * 0.012 + h * 0.30,
          w * 0.05, h * 0.30)
    # impact burst over the struck block
    ex, ey = bx2 + w * 0.07, y + h * 0.40
    pts = []
    for i in range(10):
        a = math.radians(i * 36)
        r = w * (0.055 if i % 2 == 0 else 0.026)
        pts.append((ex + r * math.cos(a), ey + r * math.sin(a) * 0.8))
    poly(d, pts, fill=FLAME_OUT)
    ellipse(d, (ex - w * 0.016, ey - w * 0.016, ex + w * 0.016, ey + w * 0.016),
            fill=FLAME_IN)


def ill_building(d, x, y, w, h):
    """Dymer: an intact block, its neighbour sheared away, crane and rubble."""
    bands(d, x, y, w, h * 0.86, [(196, 214, 226), SKY, (226, 234, 238)])
    cloud(d, x + w * 0.82, y + h * 0.14, w * 0.04, WHITE)
    # intact block, left, with balconies and one lit window row
    bx, by, bw, bh = x + w * 0.06, y + h * 0.16, w * 0.34, h * 0.70
    rect(d, (bx, by, bx + bw, by + bh), fill=(232, 226, 208), outline=INK, width=1.1)
    window_grid(d, bx + bw * 0.08, by + bh * 0.08, bw * 0.84, bh * 0.84, 3, 4,
                lit_every=0.25, seed=31, dark=GLASS)
    for r in range(4):
        line(d, [(bx - bw * 0.03, by + bh * (0.24 + 0.19 * r)),
                 (bx + bw * 1.03, by + bh * (0.24 + 0.19 * r))], fill=GREY, width=0.9)
    # the sheared block: leaning slabs, exposed floors, crack lines
    sx0, sy0 = bx + bw + w * 0.05, y + h * 0.30
    poly(d, [(sx0, y + h * 0.86), (sx0, sy0), (sx0 + w * 0.20, sy0 + h * 0.10),
             (sx0 + w * 0.24, y + h * 0.86)], fill=(206, 198, 178), outline=INK)
    for k in range(3):
        ly = sy0 + h * (0.14 + 0.15 * k)
        line(d, [(sx0 + w * 0.01, ly), (sx0 + w * 0.205 + w * 0.013 * k, ly + h * 0.035)],
             fill=(120, 112, 96), width=1.2)
    line(d, [(sx0 + w * 0.05, sy0 + h * 0.05), (sx0 + w * 0.09, sy0 + h * 0.22),
             (sx0 + w * 0.06, sy0 + h * 0.38)], fill=INK, width=1.1)  # crack
    # rubble pile at the foot of the break
    for i, (rx, rw, rh) in enumerate(((0.40, 0.20, 0.16), (0.52, 0.24, 0.22),
                                      (0.66, 0.18, 0.12))):
        poly(d, [(x + w * rx, y + h * 0.86), (x + w * (rx + rw / 2), y + h * (0.86 - rh)),
                 (x + w * (rx + rw), y + h * 0.86)], fill=(150, 142, 124))
    cloud(d, x + w * 0.60, y + h * 0.60, w * 0.055, (214, 208, 192))  # dust
    # tower crane over the rescue work
    tx = x + w * 0.90
    line(d, [(tx, y + h * 0.86), (tx, y + h * 0.08)], fill=(70, 68, 64), width=2)
    line(d, [(tx - w * 0.30, y + h * 0.08), (tx + w * 0.06, y + h * 0.08)],
         fill=(70, 68, 64), width=2)
    line(d, [(tx - w * 0.24, y + h * 0.08), (tx - w * 0.24, y + h * 0.30)],
         fill=(70, 68, 64), width=1)
    rect(d, (tx - w * 0.265, y + h * 0.30, tx - w * 0.215, y + h * 0.38),
         fill=GOLD, outline=INK, width=0.8)  # hook block lifting a slab
    rect(d, (x, y + h * 0.86, x + w, y + h), fill=(120, 114, 100))


def ill_gulf(d, x, y, w, h):
    """Bahrain: island base, radar dome, two dotted missile arcs over the sea."""
    bands(d, x, y, w, h * 0.62, [(222, 208, 178), (234, 222, 192), (240, 230, 204)])
    ellipse(d, (x + w * 0.86, y + h * 0.06, x + w * 0.96, y + h * 0.06 + w * 0.10),
            fill=(246, 178, 60))
    rect(d, (x, y + h * 0.62, x + w, y + h), fill=SEA)
    wave_row(d, x + w * 0.04, y + h * 0.80, w * 0.92, 8, w * 0.015, (240, 246, 248))
    # the island: sand spit with a runway strip and low base buildings
    poly(d, [(x + w * 0.30, y + h * 0.62), (x + w * 0.52, y + h * 0.44),
             (x + w * 0.80, y + h * 0.50), (x + w * 0.97, y + h * 0.62)],
         fill=SAND_DARK)
    line(d, [(x + w * 0.40, y + h * 0.575), (x + w * 0.86, y + h * 0.545)],
         fill=(70, 70, 72), width=2.4)  # runway
    line(d, [(x + w * 0.44, y + h * 0.568), (x + w * 0.82, y + h * 0.54)],
         fill=WHITE, width=0.8)
    rect(d, (x + w * 0.60, y + h * 0.475, x + w * 0.68, y + h * 0.525), fill=(120, 116, 108))
    rect(d, (x + w * 0.70, y + h * 0.49, x + w * 0.755, y + h * 0.53), fill=(120, 116, 108))
    # radar dome on its drum
    dx, dy = x + w * 0.50, y + h * 0.475
    rect(d, (dx - w * 0.035, dy, dx + w * 0.035, dy + h * 0.05), fill=(150, 146, 138))
    chord(d, (dx - w * 0.052, dy - h * 0.115, dx + w * 0.052, dy + h * 0.02),
          180, 360, fill=(240, 238, 228), outline=INK, width=1)
    arc(d, (dx - w * 0.052, dy - h * 0.115, dx + w * 0.052, dy + h * 0.02),
        200, 320, fill=GREY, width=0.9)
    # two launchers on the mainland shore, left, firing dotted arcs
    for k, sx in enumerate((0.055, 0.135)):
        ax, ay = x + w * sx, y + h * 0.60
        poly(d, [(ax - w * 0.025, ay), (ax, ay - h * 0.15), (ax + w * 0.025, ay)],
             fill=STEEL_DARK)
        for t_i in range(15):
            t = t_i / 14
            px_ = ax + w * (0.44 - 0.06 * k) * t
            py_ = ay - h * (0.52 - 0.10 * k) * (4 * t * (1 - t)) - h * 0.06 * t
            r = 1.1 + 0.5 * math.sin(t * math.pi)
            ellipse(d, (px_ - r, py_ - r, px_ + r, py_ + r), fill=RED)
    # burst where the arcs come down, by the dome
    ex, ey = dx + w * 0.10, dy - h * 0.06
    pts = []
    for i in range(10):
        a = math.radians(i * 36 + 8)
        r = w * (0.045 if i % 2 == 0 else 0.02)
        pts.append((ex + r * math.cos(a), ey + r * math.sin(a) * 0.8))
    poly(d, pts, fill=FLAME_OUT)
    ellipse(d, (ex - w * 0.012, ey - w * 0.012, ex + w * 0.012, ey + w * 0.012),
            fill=FLAME_IN)


def ill_desert(d, x, y, w, h):
    """Sinaloa: dunes, mesas, a cactus, and the handcuffs of a capture."""
    bands(d, x, y, w, h * 0.55, [(238, 200, 140), (244, 214, 160), (248, 226, 178)])
    ellipse(d, (x + w * 0.80, y + h * 0.05, x + w * 0.93, y + h * 0.05 + w * 0.13),
            fill=(246, 178, 60))
    for k in range(3):  # heat shimmer under the sun
        arc(d, (x + w * (0.795 + 0.01 * k), y + h * (0.30 + 0.07 * k),
                x + w * (0.885 + 0.01 * k), y + h * (0.40 + 0.07 * k)),
            200, 330, fill=(240, 190, 110), width=1)
    # distant mesas
    for mx, mw, mh in ((0.02, 0.20, 0.16), (0.60, 0.26, 0.20)):
        poly(d, [(x + w * mx, y + h * 0.55), (x + w * (mx + 0.03), y + h * (0.55 - mh)),
                 (x + w * (mx + mw - 0.03), y + h * (0.55 - mh)),
                 (x + w * (mx + mw), y + h * 0.55)], fill=(196, 138, 96))
    # layered dunes
    poly(d, [(x, y + h * 0.66), (x + w * 0.38, y + h * 0.52), (x + w, y + h * 0.68),
             (x + w, y + h), (x, y + h)], fill=(228, 186, 118))
    poly(d, [(x, y + h * 0.80), (x + w * 0.55, y + h * 0.66), (x + w, y + h * 0.82),
             (x + w, y + h), (x, y + h)], fill=SAND_DARK)
    for k in range(4):  # dune crest highlights
        arc(d, (x + w * (0.08 + 0.22 * k), y + h * (0.70 + 0.05 * (k % 2)),
                x + w * (0.24 + 0.22 * k), y + h * (0.80 + 0.05 * (k % 2))),
            190, 300, fill=(246, 222, 172), width=1.2)
    # a saguaro with arms and spine dots
    gx = x + w * 0.16
    rect(d, (gx, y + h * 0.30, gx + w * 0.038, y + h * 0.80), fill=(52, 128, 62))
    rect(d, (gx - w * 0.062, y + h * 0.42, gx, y + h * 0.475), fill=(52, 128, 62))
    rect(d, (gx - w * 0.062, y + h * 0.34, gx - w * 0.024, y + h * 0.475), fill=(52, 128, 62))
    rect(d, (gx + w * 0.038, y + h * 0.50, gx + w * 0.10, y + h * 0.555), fill=(52, 128, 62))
    rect(d, (gx + w * 0.062, y + h * 0.40, gx + w * 0.10, y + h * 0.555), fill=(52, 128, 62))
    rnd = lcg(55)
    for _ in range(14):
        sx = gx + next(rnd) * w * 0.03
        sy = y + h * (0.33 + next(rnd) * 0.42)
        ellipse(d, (sx, sy, sx + 0.9, sy + 0.9), fill=(30, 92, 40))
    ellipse(d, (gx + w * 0.006, y + h * 0.245, gx + w * 0.032, y + h * 0.30),
            fill=(226, 92, 108))  # cactus flower
    # scrub tufts
    for tx in (0.34, 0.52, 0.90):
        for k in range(5):
            a = math.radians(200 + k * 35)
            line(d, [(x + w * tx, y + h * 0.82),
                     (x + w * tx + w * 0.02 * math.cos(a), y + h * 0.82 + h * 0.07 * math.sin(a))],
                 fill=OLIVE, width=1.1)
    # the handcuffs, big and central: two rings and a chain
    for cx, cy in ((0.60, 0.42), (0.735, 0.50)):
        ex, ey = x + w * cx, y + h * cy
        r = w * 0.052
        ellipse(d, (ex - r, ey - r, ex + r, ey + r), outline=STEEL_DARK, width=2.6)
        ellipse(d, (ex - r * 0.68, ey - r * 0.68, ex + r * 0.68, ey + r * 0.68),
                outline=STEEL, width=1.2)
        rect(d, (ex - w * 0.010, ey - r - w * 0.014, ex + w * 0.010, ey - r + w * 0.004),
             fill=STEEL_DARK)
    for k in range(3):
        lx = x + w * (0.648 + 0.020 * k)
        ly = y + h * (0.435 + 0.026 * k)
        ellipse(d, (lx - w * 0.011, ly - w * 0.008, lx + w * 0.011, ly + w * 0.008),
                outline=STEEL_DARK, width=1.6)


def ill_factory(d, x, y, w, h):
    """Banten: sawtooth sheds, chimneys, layered fire and a fire hose arc."""
    bands(d, x, y, w, h * 0.88, [(178, 172, 158), (198, 192, 178), (210, 204, 190)])
    smoke_plume(d, x + w * 0.20, y + h * 0.30, w * 0.16, h * 0.26)
    smoke_plume(d, x + w * 0.55, y + h * 0.26, w * 0.20, h * 0.30)
    # two chimneys behind the sheds
    for cx in (0.16, 0.26):
        rect(d, (x + w * cx, y + h * 0.28, x + w * (cx + 0.045), y + h * 0.60),
             fill=(130, 124, 114))
        rect(d, (x + w * (cx - 0.006), y + h * 0.28, x + w * (cx + 0.051), y + h * 0.325),
             fill=BRICK)
    # sawtooth roof line over a long shed
    base = y + h * 0.60
    rect(d, (x + w * 0.05, base, x + w * 0.95, y + h * 0.88), fill=(104, 98, 90))
    for i in range(5):
        tx0 = x + w * (0.05 + 0.18 * i)
        poly(d, [(tx0, base), (tx0 + w * 0.055, base - h * 0.16), (tx0 + w * 0.18, base)],
             fill=(84, 80, 74))
        poly(d, [(tx0, base), (tx0 + w * 0.055, base - h * 0.16), (tx0 + w * 0.075, base)],
             fill=GLASS)
    window_grid(d, x + w * 0.08, base + h * 0.06, w * 0.84, h * 0.16, 12, 2,
                dark=(70, 66, 60))
    # the fire: three flame tongues along the roof, sparks, ember base
    for fx, fw, fh in ((0.30, 0.10, 0.42), (0.50, 0.13, 0.54), (0.70, 0.09, 0.36)):
        flame(d, x + w * fx, base + h * 0.02, w * fw, h * fh)
    spark_dots(d, x + w * 0.50, base, w * 0.5, h * 0.6, 22, seed=77)
    rect(d, (x + w * 0.05, y + h * 0.845, x + w * 0.95, y + h * 0.88), fill=FLAME_OUT)
    # a fire engine corner and its dotted water arc, right
    rect(d, (x + w * 0.86, y + h * 0.70, x + w * 0.99, y + h * 0.88), fill=RED)
    rect(d, (x + w * 0.885, y + h * 0.735, x + w * 0.925, y + h * 0.79), fill=GLASS)
    ellipse(d, (x + w * 0.885, y + h * 0.845, x + w * 0.885 + w * 0.045,
                y + h * 0.845 + w * 0.045), fill=INK)
    ellipse(d, (x + w * 0.945, y + h * 0.845, x + w * 0.945 + w * 0.045,
                y + h * 0.845 + w * 0.045), fill=INK)
    for t_i in range(13):
        t = t_i / 12
        px_ = x + w * 0.875 - w * 0.30 * t
        py_ = y + h * 0.72 - h * 0.34 * (4 * t * (1 - t)) + h * 0.10 * t
        r = 1.0 + 0.4 * math.sin(t * math.pi)
        ellipse(d, (px_ - r, py_ - r, px_ + r, py_ + r), fill=(120, 190, 235))
    rect(d, (x, y + h * 0.88, x + w, y + h), fill=(76, 72, 66))


def ill_football(d, x, y, w, h):
    """Anfield: the Kop's dot crowd, a striped pitch, a goal and the 4-0."""
    # crowd band: five rows of deterministic dots in home red
    rect(d, (x, y, x + w, y + h * 0.26), fill=(120, 30, 34))
    rnd = lcg(2024)
    for r in range(4):
        for c in range(46):
            tone = next(rnd)
            cc = (196, 70, 66) if tone < 0.7 else ((240, 238, 230) if tone < 0.85
                                                   else (240, 190, 90))
            px_ = x + w * (0.012 + 0.0215 * c) + (r % 2) * w * 0.008
            py_ = y + h * (0.045 + 0.052 * r)
            ellipse(d, (px_, py_, px_ + 1.6, py_ + 1.6), fill=cc)
    # pitch with mowing stripes
    bands_v = 6
    for i in range(bands_v):
        rect(d, (x + w * i / bands_v, y + h * 0.26, x + w * (i + 1) / bands_v + 0.6,
                 y + h), fill=(58, 138, 70) if i % 2 == 0 else (74, 152, 84))
    rect(d, (x + w * 0.03, y + h * 0.32, x + w * 0.97, y + h * 0.95),
         outline=WHITE, width=1.4)
    line(d, [(x + w * 0.5, y + h * 0.32), (x + w * 0.5, y + h * 0.95)], fill=WHITE, width=1.2)
    ellipse(d, (x + w * 0.415, y + h * 0.475, x + w * 0.585, y + h * 0.475 + w * 0.17),
            outline=WHITE, width=1.2)
    rect(d, (x + w * 0.03, y + h * 0.44, x + w * 0.17, y + h * 0.83), outline=WHITE, width=1.1)
    rect(d, (x + w * 0.83, y + h * 0.44, x + w * 0.97, y + h * 0.83), outline=WHITE, width=1.1)
    # goal at the right with a net
    gx, gy = x + w * 0.90, y + h * 0.50
    rect(d, (gx, gy, gx + w * 0.075, gy + h * 0.26), outline=WHITE, width=1.8)
    for k in range(3):
        line(d, [(gx + w * 0.019 * (k + 1), gy), (gx + w * 0.019 * (k + 1), gy + h * 0.26)],
             fill=(210, 220, 210), width=0.7)
    line(d, [(gx, gy + h * 0.09), (gx + w * 0.075, gy + h * 0.09)], fill=(210, 220, 210), width=0.7)
    line(d, [(gx, gy + h * 0.18), (gx + w * 0.075, gy + h * 0.18)], fill=(210, 220, 210), width=0.7)
    # the ball, pentagon-spotted, lower left of centre
    bx, by, br = x + w * 0.335, y + h * 0.66, w * 0.052
    ellipse(d, (bx - br, by - br, bx + br, by + br), fill=WHITE, outline=INK, width=1.1)
    ellipse(d, (bx - br * 0.30, by - br * 0.30, bx + br * 0.30, by + br * 0.30), fill=INK)
    for a_deg in (90, 162, 234, 306, 18):
        a = math.radians(a_deg)
        px_ = bx + br * 0.72 * math.cos(a)
        py_ = by + br * 0.72 * math.sin(a)
        ellipse(d, (px_ - br * 0.16, py_ - br * 0.16, px_ + br * 0.16, py_ + br * 0.16),
                fill=INK)
    # floodlight glows in the top corners of the stand
    for fx in (0.04, 0.96):
        for k in range(3):
            ellipse(d, (x + w * fx - 1 - k, y + h * 0.02 - k * 0.4,
                        x + w * fx + 1 + k, y + h * 0.02 + 2 + k * 0.4),
                    outline=(250, 240, 200), width=0.7)
    f = F("display", h * 0.46)
    draw_text(d, (x + w * 0.615, y + h * 0.33), "4-0", f, fill=WHITE)


def ill_tennis(d, x, y, w, h):
    """Turin: court lines, a meshed net, a strung racket, ball and trophy."""
    rect(d, (x, y, x + w, y + h), fill=(44, 84, 140))
    rect(d, (x + w * 0.07, y + h * 0.12, x + w * 0.93, y + h * 0.88),
         fill=(52, 138, 80), outline=WHITE, width=1.4)
    line(d, [(x + w * 0.07, y + h * 0.30), (x + w * 0.93, y + h * 0.30)], fill=WHITE, width=0.9)
    line(d, [(x + w * 0.07, y + h * 0.70), (x + w * 0.93, y + h * 0.70)], fill=WHITE, width=0.9)
    line(d, [(x + w * 0.5, y + h * 0.30), (x + w * 0.5, y + h * 0.70)], fill=WHITE, width=0.9)
    # the net: posts, white tape and a mesh of fine lines
    ny = y + h * 0.5
    line(d, [(x + w * 0.05, ny - h * 0.05), (x + w * 0.95, ny - h * 0.05)], fill=WHITE, width=2)
    for k in range(24):
        lx = x + w * (0.05 + 0.0375 * k)
        line(d, [(lx, ny - h * 0.05), (lx, ny + h * 0.10)], fill=(30, 34, 40), width=0.6)
    for k in range(3):
        line(d, [(x + w * 0.05, ny + h * (0.0 + 0.05 * k)),
                 (x + w * 0.95, ny + h * (0.0 + 0.05 * k))], fill=(30, 34, 40), width=0.6)
    line(d, [(x + w * 0.05, ny - h * 0.09), (x + w * 0.05, ny + h * 0.12)], fill=INK, width=2)
    line(d, [(x + w * 0.95, ny - h * 0.09), (x + w * 0.95, ny + h * 0.12)], fill=INK, width=2)
    # racket, right: oval head, string grid, throat and grip
    rx, ry = x + w * 0.76, y + h * 0.30
    ellipse(d, (rx - w * 0.075, ry - h * 0.21, rx + w * 0.075, ry + h * 0.21),
            outline=(238, 238, 232), width=2.2)
    for k in range(-2, 3):
        line(d, [(rx + k * w * 0.026, ry - h * 0.185), (rx + k * w * 0.026, ry + h * 0.185)],
             fill=(200, 205, 210), width=0.6)
        line(d, [(rx - w * 0.062, ry + k * h * 0.075), (rx + w * 0.062, ry + k * h * 0.075)],
             fill=(200, 205, 210), width=0.6)
    line(d, [(rx - w * 0.018, ry + h * 0.20), (rx - w * 0.006, ry + h * 0.33)], fill=(238, 238, 232), width=2)
    line(d, [(rx + w * 0.018, ry + h * 0.20), (rx + w * 0.006, ry + h * 0.33)], fill=(238, 238, 232), width=2)
    line(d, [(rx, ry + h * 0.33), (rx + w * 0.035, ry + h * 0.52)], fill=(120, 74, 40), width=3)
    # the ball with its motion arcs, left
    bx, by, br = x + w * 0.20, y + h * 0.34, w * 0.038
    for k in range(3):
        arc(d, (bx - br * (1.6 + 0.8 * k), by - br * (1.6 + 0.8 * k),
                bx + br * (1.6 + 0.8 * k), by + br * (1.6 + 0.8 * k)),
            100, 190, fill=(190, 214, 120), width=1.1)
    ellipse(d, (bx - br, by - br, bx + br, by + br), fill=(214, 232, 84), outline=(150, 170, 60), width=1)
    arc(d, (bx - br * 0.8, by - br * 0.8, bx + br * 0.8, by + br * 0.8), 300, 120,
        fill=WHITE, width=1)
    # the trophy, lower left: cup, handles, stem, plinth, one sparkle
    tx, ty = x + w * 0.155, y + h * 0.60
    poly(d, [(tx - w * 0.045, ty), (tx + w * 0.045, ty), (tx + w * 0.030, ty + h * 0.15),
             (tx - w * 0.030, ty + h * 0.15)], fill=GOLD, outline=(150, 110, 40))
    arc(d, (tx - w * 0.075, ty - h * 0.01, tx - w * 0.028, ty + h * 0.13), 90, 270,
        fill=GOLD, width=2.2)
    arc(d, (tx + w * 0.028, ty - h * 0.01, tx + w * 0.075, ty + h * 0.13), 270, 90,
        fill=GOLD, width=2.2)
    rect(d, (tx - w * 0.008, ty + h * 0.15, tx + w * 0.008, ty + h * 0.21), fill=GOLD)
    rect(d, (tx - w * 0.038, ty + h * 0.21, tx + w * 0.038, ty + h * 0.26),
         fill=(150, 110, 40))
    sx, sy = tx + w * 0.075, ty - h * 0.05
    line(d, [(sx - w * 0.014, sy), (sx + w * 0.014, sy)], fill=WHITE, width=1.4)
    line(d, [(sx, sy - h * 0.045), (sx, sy + h * 0.045)], fill=WHITE, width=1.4)


def ill_moto(d, x, y, w, h):
    """Portimao: a leaning race bike, its rider, speed lines, crown and 8."""
    bands(d, x, y, w, h * 0.78, [(214, 224, 230), (228, 232, 226), (236, 232, 214)])
    # distant grandstand strip with a dot crowd
    rect(d, (x + w * 0.03, y + h * 0.30, x + w * 0.42, y + h * 0.46), fill=(168, 172, 178))
    rnd = lcg(8)
    for r in range(3):
        for c in range(26):
            cc = (200, 90, 80) if next(rnd) < 0.4 else (90, 110, 160)
            px_ = x + w * (0.04 + 0.0145 * c)
            py_ = y + h * (0.325 + 0.04 * r)
            ellipse(d, (px_, py_, px_ + 1.3, py_ + 1.3), fill=cc)
    rect(d, (x + w * 0.03, y + h * 0.28, x + w * 0.42, y + h * 0.315), fill=NAVY2)
    # asphalt with a red-and-white kerb
    rect(d, (x, y + h * 0.78, x + w, y + h), fill=(104, 102, 98))
    for i in range(8):
        rect(d, (x + w * i / 8, y + h * 0.78, x + w * (i + 0.5) / 8, y + h * 0.815),
             fill=RED if i % 2 == 0 else WHITE)
    # speed lines behind the bike
    for k, ly in enumerate((0.42, 0.52, 0.62)):
        line(d, [(x + w * 0.02, y + h * ly), (x + w * (0.16 - 0.03 * k), y + h * ly)],
             fill=(150, 148, 140), width=1.6)
    # wheels with discs and spokes
    for wx, wr in ((0.30, 0.105), (0.76, 0.115)):
        cx, cy = x + w * wx, y + h * 0.70
        r = w * wr
        ellipse(d, (cx - r, cy - r, cx + r, cy + r), fill=(32, 32, 34))
        ellipse(d, (cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55),
                fill=(168, 166, 158))
        for a_deg in (0, 60, 120):
            a = math.radians(a_deg)
            line(d, [(cx - r * 0.5 * math.cos(a), cy - r * 0.5 * math.sin(a)),
                     (cx + r * 0.5 * math.cos(a), cy + r * 0.5 * math.sin(a))],
                 fill=(120, 118, 110), width=1.2)
    # fairing, tank and tail in race red with a white number plate
    poly(d, [(x + w * 0.26, y + h * 0.66), (x + w * 0.40, y + h * 0.40),
             (x + w * 0.60, y + h * 0.36), (x + w * 0.78, y + h * 0.40),
             (x + w * 0.82, y + h * 0.62), (x + w * 0.66, y + h * 0.55),
             (x + w * 0.44, y + h * 0.58)], fill=RED)
    poly(d, [(x + w * 0.60, y + h * 0.36), (x + w * 0.78, y + h * 0.40),
             (x + w * 0.80, y + h * 0.50), (x + w * 0.64, y + h * 0.46)], fill=(140, 36, 30))
    poly(d, [(x + w * 0.70, y + h * 0.415), (x + w * 0.775, y + h * 0.44),
             (x + w * 0.765, y + h * 0.52), (x + w * 0.70, y + h * 0.50)], fill=WHITE)
    line(d, [(x + w * 0.34, y + h * 0.60), (x + w * 0.30, y + h * 0.70)], fill=STEEL_DARK, width=2)
    line(d, [(x + w * 0.72, y + h * 0.52), (x + w * 0.76, y + h * 0.70)], fill=STEEL_DARK, width=2)
    # the rider, leant over the tank: back, arm, leg and helmet
    poly(d, [(x + w * 0.44, y + h * 0.38), (x + w * 0.56, y + h * 0.20),
             (x + w * 0.66, y + h * 0.28), (x + w * 0.54, y + h * 0.42)], fill=(36, 52, 104))
    poly(d, [(x + w * 0.56, y + h * 0.24), (x + w * 0.70, y + h * 0.36),
             (x + w * 0.665, y + h * 0.42), (x + w * 0.545, y + h * 0.32)], fill=(36, 52, 104))
    poly(d, [(x + w * 0.46, y + h * 0.40), (x + w * 0.60, y + h * 0.50),
             (x + w * 0.565, y + h * 0.565), (x + w * 0.435, y + h * 0.47)], fill=(24, 36, 78))
    hx, hy, hr = x + w * 0.635, y + h * 0.155, w * 0.052
    ellipse(d, (hx - hr, hy - hr, hx + hr, hy + hr), fill=WHITE, outline=INK, width=1.1)
    chord(d, (hx - hr, hy - hr, hx + hr, hy + hr), 300, 130, fill=RED)
    rect(d, (hx + hr * 0.05, hy - hr * 0.25, hx + hr * 0.95, hy + hr * 0.18), fill=(30, 40, 60))
    # crown motif and the eighth title
    cx0, cy0 = x + w * 0.045, y + h * 0.10
    poly(d, [(cx0, cy0 + h * 0.13), (cx0 + w * 0.028, cy0 + h * 0.03),
             (cx0 + w * 0.056, cy0 + h * 0.11), (cx0 + w * 0.084, cy0),
             (cx0 + w * 0.112, cy0 + h * 0.13)], fill=GOLD, outline=(150, 110, 40))
    rect(d, (cx0, cy0 + h * 0.13, cx0 + w * 0.112, cy0 + h * 0.165), fill=GOLD)
    f = F("display", h * 0.44)
    draw_text(d, (x + w * 0.865, y + h * 0.06), "8", f, fill=NAVY)


def ill_f1(d, x, y, w, h):
    """Las Vegas at night: lit towers, neon, and a sparking grand prix car."""
    rect(d, (x, y, x + w, y + h), fill=NIGHT)
    starfield(d, x, y, w, h * 0.4, 22, seed=63, max_r=0.9)
    # the Strip skyline: towers with deterministic lit windows
    towers = ((0.02, 0.46, 0.11), (0.15, 0.60, 0.10), (0.27, 0.40, 0.09),
              (0.62, 0.52, 0.10), (0.74, 0.64, 0.11), (0.87, 0.44, 0.11))
    for i, (bx, bh, bw) in enumerate(towers):
        bxw = x + w * bx
        rect(d, (bxw, y + h * (0.66 - bh), bxw + w * bw, y + h * 0.66),
             fill=(30, 40, 76))
        window_grid(d, bxw + w * 0.012, y + h * (0.66 - bh) + 2,
                    w * bw - w * 0.024, h * bh - 4, 3, 6,
                    lit_every=0.55, seed=300 + i, dark=(24, 32, 60))
    # a pyramid and its sky beam, centre
    poly(d, [(x + w * 0.40, y + h * 0.66), (x + w * 0.475, y + h * 0.30),
             (x + w * 0.55, y + h * 0.66)], fill=(36, 48, 84))
    poly(d, [(x + w * 0.469, y + h * 0.315), (x + w * 0.481, y + h * 0.315),
             (x + w * 0.545, y), (x + w * 0.43, y)], fill=(140, 190, 235))
    # neon dots along the boulevard
    rnd = lcg(414)
    for c in range(30):
        cc = (246, 120, 160) if next(rnd) < 0.5 else (120, 220, 250)
        px_ = x + w * (0.015 + 0.033 * c)
        ellipse(d, (px_, y + h * 0.635, px_ + 1.7, y + h * 0.635 + 1.7), fill=cc)
    # track, kerb and the car
    rect(d, (x, y + h * 0.66, x + w, y + h), fill=(44, 46, 58))
    for i in range(10):
        rect(d, (x + w * i / 10, y + h * 0.66, x + w * (i + 0.5) / 10, y + h * 0.685),
             fill=RED if i % 2 == 0 else WHITE)
    line(d, [(x, y + h * 0.90), (x + w, y + h * 0.90)], fill=(230, 230, 224), width=1.2)
    cy = y + h * 0.70
    poly(d, [(x + w * 0.14, cy + h * 0.13), (x + w * 0.30, cy + h * 0.05),
             (x + w * 0.55, cy + h * 0.02), (x + w * 0.80, cy + h * 0.05),
             (x + w * 0.90, cy + h * 0.13), (x + w * 0.78, cy + h * 0.16),
             (x + w * 0.28, cy + h * 0.16)], fill=RED)
    poly(d, [(x + w * 0.42, cy + h * 0.035), (x + w * 0.58, cy + h * 0.035),
             (x + w * 0.66, cy + h * 0.10), (x + w * 0.38, cy + h * 0.10)], fill=(30, 30, 36))
    arc(d, (x + w * 0.44, cy - h * 0.015, x + w * 0.60, cy + h * 0.09), 180, 360,
        fill=INK, width=2.2)  # the halo
    rect(d, (x + w * 0.075, cy + h * 0.015, x + w * 0.20, cy + h * 0.05), fill=(24, 24, 28))
    rect(d, (x + w * 0.80, cy - h * 0.03, x + w * 0.875, cy + h * 0.05), fill=(24, 24, 28))
    line(d, [(x + w * 0.837, cy - h * 0.03), (x + w * 0.837, cy + h * 0.015)], fill=INK, width=1.6)
    for wx in (0.235, 0.735):
        cx, cy2 = x + w * wx, cy + h * 0.155
        r = w * 0.048
        ellipse(d, (cx - r, cy2 - r, cx + r, cy2 + r), fill=(14, 14, 16))
        ellipse(d, (cx - r * 0.4, cy2 - r * 0.4, cx + r * 0.4, cy2 + r * 0.4),
                fill=(90, 90, 96))
    spark_dots(d, x + w * 0.52, cy + h * 0.175, w * 0.3, h * 0.05, 12, seed=19)
    line(d, [(x + w * 0.01, cy + h * 0.09), (x + w * 0.12, cy + h * 0.09)],
         fill=(120, 200, 240), width=2)  # a rival's light streak


def ill_capitol(d, x, y, w, h):
    """Washington: the Capitol dome, its columns, and 258 seats in dots."""
    bands(d, x, y, w, h * 0.86, [(188, 206, 224), SKY, (226, 234, 238)])
    cloud(d, x + w * 0.13, y + h * 0.14, w * 0.035, WHITE)
    bx, base = x + w * 0.07, y + h * 0.86
    # side wings
    for wx in (0.0, 0.66):
        rect(d, (bx + w * wx, base - h * 0.20, bx + w * (wx + 0.20), base),
             fill=(226, 222, 208))
        window_grid(d, bx + w * (wx + 0.02), base - h * 0.17, w * 0.16, h * 0.12,
                    4, 2, dark=GLASS)
    # main block: steps, columns, entablature
    for k in range(3):
        rect(d, (bx + w * (0.16 - 0.02 * k), base - h * (0.05 + 0.045 * k),
                 bx + w * (0.70 + 0.02 * k), base - h * (0.005 + 0.045 * k)),
             fill=(214, 210, 196))
    for i in range(7):
        cx = bx + w * (0.235 + 0.068 * i)
        rect(d, (cx, base - h * 0.36, cx + w * 0.030, base - h * 0.13),
             fill=(240, 236, 224))
        rect(d, (cx - w * 0.004, base - h * 0.375, cx + w * 0.038, base - h * 0.36),
             fill=(240, 236, 224))
    rect(d, (bx + w * 0.17, base - h * 0.415, bx + w * 0.69, base - h * 0.375),
         fill=(240, 236, 224))
    poly(d, [(bx + w * 0.20, base - h * 0.415), (bx + w * 0.66, base - h * 0.415),
             (bx + w * 0.43, base - h * 0.50)], fill=(226, 222, 208))
    # the dome: ribbed half-disc on a drum, statue spike and flag
    dx0, dy0 = bx + w * 0.245, base - h * 0.80
    rect(d, (bx + w * 0.235, base - h * 0.545, bx + w * 0.625, base - h * 0.50),
         fill=(226, 222, 208))
    chord(d, (dx0, dy0, dx0 + w * 0.37, base - h * 0.475), 180, 360,
          fill=(206, 212, 220), outline=INK, width=1)
    for k in range(-2, 3):
        arc(d, (dx0 + w * 0.185 - w * 0.185 * (1 - abs(k) * 0.18) - w * 0.02 * k,
                dy0, dx0 + w * 0.185 + w * 0.185 * (1 - abs(k) * 0.18) - w * 0.02 * k,
                base - h * 0.475), 180, 360, fill=(170, 178, 190), width=0.8)
    line(d, [(bx + w * 0.43, base - h * 0.80), (bx + w * 0.43, base - h * 0.90)],
         fill=INK, width=1.5)
    poly(d, [(bx + w * 0.43, base - h * 0.90), (bx + w * 0.505, base - h * 0.855),
             (bx + w * 0.43, base - h * 0.815)], fill=RED)
    # 258: the seat tally as three arcs of dots, blue with a red minority
    cx, cy = x + w * 0.80, y + h * 0.60
    rnd = lcg(258)
    for ring, (rr, n) in enumerate(((0.105, 17), (0.078, 13), (0.051, 9))):
        for i in range(n):
            a = math.radians(180 + 180 * i / (n - 1))
            px_ = cx + w * rr * math.cos(a)
            py_ = cy - w * rr * math.sin(a) * 0.62
            blue = (i + ring) < n * 0.59
            ellipse(d, (px_ - 1.5, py_ - 1.5, px_ + 1.5, py_ + 1.5),
                    fill=NAVY2 if blue else RED)
    f = F("display", h * 0.40)
    draw_text(d, (x + w * 0.715, y + h * 0.06), "258", f, fill=NAVY)
    rect(d, (x, base, x + w, y + h), fill=(150, 160, 128))


def ill_village(d, x, y, w, h):
    """Ramallah hills: stone houses, an olive tree, a burning pickup."""
    bands(d, x, y, w, h * 0.62, [(206, 214, 200), (220, 222, 196), (230, 226, 198)])
    # terraced hills behind
    poly(d, [(x, y + h * 0.52), (x + w * 0.35, y + h * 0.36), (x + w * 0.72, y + h * 0.46),
             (x + w, y + h * 0.40), (x + w, y + h * 0.62), (x, y + h * 0.62)],
         fill=(168, 172, 138))
    for k in range(3):
        line(d, [(x + w * (0.05 + 0.08 * k), y + h * (0.50 + 0.035 * k)),
                 (x + w * (0.55 + 0.05 * k), y + h * (0.44 + 0.035 * k))],
             fill=(140, 146, 110), width=1.1)
    # two stone houses with flat roofs, doors and small windows
    for hx, hw, hh in ((0.05, 0.27, 0.34), (0.60, 0.30, 0.30)):
        bx = x + w * hx
        by = y + h * (0.84 - hh)
        rect(d, (bx, by, bx + w * hw, y + h * 0.84), fill=(238, 232, 214), outline=INK, width=1)
        rect(d, (bx - w * 0.015, by - h * 0.035, bx + w * hw + w * 0.015, by), fill=BRICK)
        rect(d, (bx + w * hw * 0.40, by + h * hh * 0.45, bx + w * hw * 0.60, y + h * 0.84),
             fill=(110, 84, 60))
        window_grid(d, bx + w * hw * 0.08, by + h * 0.05, w * hw * 0.26, h * 0.11,
                    2, 1, dark=GLASS)
        window_grid(d, bx + w * hw * 0.68, by + h * 0.05, w * hw * 0.26, h * 0.11,
                    2, 1, lit_every=0.5, seed=66, dark=GLASS)
    # the olive tree: gnarled trunk, clustered canopy, olive dots
    tx = x + w * 0.44
    poly(d, [(tx - w * 0.016, y + h * 0.84), (tx - w * 0.006, y + h * 0.52),
             (tx + w * 0.014, y + h * 0.52), (tx + w * 0.022, y + h * 0.84)],
         fill=(110, 84, 60))
    line(d, [(tx + w * 0.004, y + h * 0.56), (tx - w * 0.05, y + h * 0.40)], fill=(110, 84, 60), width=2)
    line(d, [(tx + w * 0.006, y + h * 0.56), (tx + w * 0.06, y + h * 0.42)], fill=(110, 84, 60), width=2)
    for cx, cy, cr in ((0.40, 0.30, 0.075), (0.50, 0.24, 0.095), (0.475, 0.36, 0.085),
                       (0.545, 0.33, 0.06), (0.415, 0.42, 0.055)):
        ellipse(d, (x + w * cx - w * cr, y + h * cy - w * cr * 0.8,
                    x + w * cx + w * cr, y + h * cy + w * cr * 0.8), fill=LEAF)
    rnd = lcg(71)
    for _ in range(16):
        px_ = x + w * (0.375 + next(rnd) * 0.20)
        py_ = y + h * (0.20 + next(rnd) * 0.24)
        ellipse(d, (px_ - 1.1, py_ - 1.4, px_ + 1.1, py_ + 1.4), fill=(52, 74, 40))
    # dry-stone wall segments in front of the houses
    for k in range(6):
        rect(d, (x + w * (0.03 + 0.075 * k), y + h * (0.845 + 0.028 * (k % 2)),
                 x + w * (0.095 + 0.075 * k), y + h * (0.87 + 0.028 * (k % 2))),
             fill=(168, 158, 138), outline=(130, 120, 100), width=0.7)
    # the burning pickup, right: cab, bed, wheels, flame and smoke
    vx, vy = x + w * 0.70, y + h * 0.70
    rect(d, (vx, vy, vx + w * 0.24, vy + h * 0.13), fill=(70, 74, 82))
    poly(d, [(vx + w * 0.155, vy), (vx + w * 0.185, vy - h * 0.085),
             (vx + w * 0.235, vy - h * 0.085), (vx + w * 0.24, vy)], fill=(70, 74, 82))
    rect(d, (vx + w * 0.175, vy - h * 0.075, vx + w * 0.225, vy - h * 0.02), fill=GLASS)
    for wx in (0.045, 0.195):
        ellipse(d, (vx + w * wx, vy + h * 0.10, vx + w * wx + w * 0.05,
                    vy + h * 0.10 + w * 0.05), fill=(26, 26, 28))
    flame(d, vx + w * 0.07, vy + h * 0.01, w * 0.075, h * 0.34)
    flame(d, vx + w * 0.13, vy + h * 0.01, w * 0.05, h * 0.24)
    smoke_plume(d, vx + w * 0.09, vy - h * 0.30, w * 0.07, h * 0.26,
                tones=((80, 78, 76), SMOKE))
    rect(d, (x, y + h * 0.90, x + w, y + h), fill=(168, 156, 128))


def ill_boat(d, x, y, w, h):
    """Nigeria: a capsized hull awash, life rings, crates and a rescue boat."""
    bands(d, x, y, w, h * 0.34, [(188, 208, 220), (204, 220, 228), (216, 228, 234)])
    ellipse(d, (x + w * 0.90, y + h * 0.05, x + w * 0.90 + w * 0.055, y + h * 0.05 + w * 0.055),
            fill=(246, 200, 84))
    for bx_, by_ in ((0.16, 0.12), (0.24, 0.09)):  # two birds
        arc(d, (x + w * bx_, y + h * by_, x + w * bx_ + w * 0.03, y + h * by_ + h * 0.08),
            200, 330, fill=INK, width=1.1)
        arc(d, (x + w * bx_ + w * 0.028, y + h * by_, x + w * bx_ + w * 0.058,
                y + h * by_ + h * 0.08), 210, 340, fill=INK, width=1.1)
    # layered sea
    bands(d, x, y + h * 0.34, w, h * 0.66, [(140, 182, 204), SEA, (120, 168, 196)])
    wave_row(d, x + w * 0.03, y + h * 0.52, w * 0.94, 8, w * 0.016, (240, 246, 248))
    wave_row(d, x + w * 0.06, y + h * 0.86, w * 0.88, 7, w * 0.014, (225, 240, 246))
    # the capsized hull: an upturned curved shell, keel up, riding awash
    hx, hy = x + w * 0.16, y + h * 0.60
    chord(d, (hx, hy - h * 0.30, hx + w * 0.44, hy + h * 0.16), 180, 360,
          fill=(146, 96, 58), outline=(110, 70, 40), width=1.2)
    for k in range(4):  # hull strakes
        arc(d, (hx + w * 0.03 + k * w * 0.012, hy - h * (0.26 - 0.015 * k),
                hx + w * 0.41 - k * w * 0.012, hy + h * 0.13), 185, 355,
            fill=(110, 70, 40), width=0.9)
    line(d, [(hx + w * 0.05, hy - h * 0.015), (hx + w * 0.39, hy - h * 0.015)],
         fill=(110, 70, 40), width=1.6)  # the keel line
    ellipse(d, (hx + w * 0.19, hy - h * 0.055, hx + w * 0.25, hy - h * 0.005),
            fill=(110, 70, 40))  # rudder post boss
    wave_row(d, hx + w * 0.01, hy + h * 0.015, w * 0.42, 6, w * 0.013,
             (240, 246, 248))  # foam along the waterline of the hull
    # floating debris: two crates and a barrel
    for cx, cy, s_ in ((0.60, 0.66, 0.045), (0.665, 0.72, 0.036)):
        rect(d, (x + w * cx, y + h * cy, x + w * (cx + s_), y + h * cy + w * s_ * 0.8),
             fill=(170, 130, 84), outline=(120, 88, 52), width=0.9)
    ellipse(d, (x + w * 0.715, y + h * 0.60, x + w * 0.715 + w * 0.034,
                y + h * 0.60 + w * 0.045), fill=TEAL, outline=INK, width=0.8)
    # two life rings riding the swell
    for rx, ry, rr in ((0.545, 0.52, 0.030), (0.795, 0.50, 0.024)):
        cx, cy = x + w * rx, y + h * ry
        ellipse(d, (cx - w * rr, cy - w * rr, cx + w * rr, cy + w * rr),
                fill=WHITE, outline=RED, width=2.2)
        ellipse(d, (cx - w * rr * 0.45, cy - w * rr * 0.45, cx + w * rr * 0.45,
                    cy + w * rr * 0.45), outline=RED, width=1.2)
    # the rescue boat coming in from the right, wake behind it
    bx, by = x + w * 0.80, y + h * 0.68
    poly(d, [(bx, by), (bx + w * 0.17, by), (bx + w * 0.145, by + h * 0.09),
             (bx + w * 0.02, by + h * 0.09)], fill=(52, 90, 130))
    rect(d, (bx + w * 0.055, by - h * 0.075, bx + w * 0.105, by), fill=(52, 90, 130))
    ellipse(d, (bx + w * 0.068, by - h * 0.135, bx + w * 0.068 + w * 0.026,
                by - h * 0.135 + w * 0.026), fill=(60, 48, 40))  # coxswain's head
    for k in range(3):
        arc(d, (bx - w * (0.03 + 0.025 * k), by + h * 0.02, bx + w * 0.02,
                by + h * (0.10 + 0.03 * k)), 60, 140, fill=(240, 246, 248), width=1.2)


def ill_cricket(d, x, y, w, h):
    """Wellington: striped outfield, the pitch, stumps, bat, ball and 720."""
    # outfield with alternating mowing bands radiating as flat stripes
    for i in range(7):
        rect(d, (x + w * i / 7, y, x + w * (i + 1) / 7 + 0.6, y + h),
             fill=(104, 168, 88) if i % 2 == 0 else (124, 182, 100))
    # a white sightscreen, left
    rect(d, (x + w * 0.035, y + h * 0.16, x + w * 0.115, y + h * 0.62),
         fill=(244, 244, 238), outline=GREY, width=0.9)
    line(d, [(x + w * 0.05, y + h * 0.62), (x + w * 0.05, y + h * 0.70)], fill=GREY, width=1.2)
    line(d, [(x + w * 0.10, y + h * 0.62), (x + w * 0.10, y + h * 0.70)], fill=GREY, width=1.2)
    # the pitch strip, centre
    rect(d, (x + w * 0.335, y + h * 0.06, x + w * 0.475, y + h * 0.94),
         fill=(228, 210, 170))
    line(d, [(x + w * 0.335, y + h * 0.20), (x + w * 0.475, y + h * 0.20)], fill=WHITE, width=1)
    line(d, [(x + w * 0.335, y + h * 0.80), (x + w * 0.475, y + h * 0.80)], fill=WHITE, width=1)
    # stumps and bails at the near end
    for i in range(3):
        sx = x + w * (0.368 + 0.037 * i)
        rect(d, (sx, y + h * 0.60, sx + w * 0.013, y + h * 0.86), fill=(242, 236, 212))
    rect(d, (x + w * 0.372, y + h * 0.575, x + w * 0.402, y + h * 0.60), fill=(242, 236, 212))
    rect(d, (x + w * 0.414, y + h * 0.575, x + w * 0.444, y + h * 0.60), fill=(242, 236, 212))
    # the bat, angled across the crease, with its edge highlight
    poly(d, [(x + w * 0.545, y + h * 0.88), (x + w * 0.60, y + h * 0.88),
             (x + w * 0.545, y + h * 0.36), (x + w * 0.50, y + h * 0.36)],
         fill=(216, 192, 142), outline=INK)
    line(d, [(x + w * 0.522, y + h * 0.36), (x + w * 0.505, y + h * 0.16)],
         fill=(90, 70, 50), width=2.4)  # handle
    line(d, [(x + w * 0.565, y + h * 0.42), (x + w * 0.525, y + h * 0.80)],
         fill=(240, 224, 184), width=1.1)
    # the ball in flight with seam dots and a motion arc
    bx, by, br = x + w * 0.665, y + h * 0.30, w * 0.034
    arc(d, (bx - w * 0.10, by - h * 0.10, bx + w * 0.02, by + h * 0.30), 250, 340,
        fill=(240, 246, 238), width=1.1)
    ellipse(d, (bx - br, by - br, bx + br, by + br), fill=RED, outline=(120, 30, 26), width=0.9)
    arc(d, (bx - br * 0.7, by - br * 0.7, bx + br * 0.7, by + br * 0.7), 60, 240,
        fill=WHITE, width=0.9)
    # boundary rope arc along the bottom
    arc(d, (x + w * 0.05, y + h * 0.55, x + w * 0.98, y + h * 1.25), 20, 160,
        fill=WHITE, width=1.6)
    f = F("display", h * 0.44)
    draw_text(d, (x + w * 0.56, y + h * 0.05), "720", f, fill=WHITE)


ILLUSTRATIONS = {
    "climate": ill_climate, "ship": ill_ship, "mercury": ill_mercury,
    "missile": ill_missile, "building": ill_building, "gulf": ill_gulf,
    "desert": ill_desert, "factory": ill_factory, "football": ill_football,
    "tennis": ill_tennis, "moto": ill_moto, "f1": ill_f1,
    "capitol": ill_capitol, "village": ill_village, "boat": ill_boat,
    "cricket": ill_cricket,
}
