#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""The World in One Image - entry generator for make.fun news-image-20261122.

Renders a one-page broadsheet of Sunday 22 November 2026 from stories.json
(the verified corpus shipped in this repository) and writes the entry image
to the kit output path (/output/entry.png, or $MAKEFUN_OUTPUT_DIR/entry.png).

The code is split by concern: illustrations.py holds the original
flat-vector artwork for the sixteen drawn stories, layout.py paints the
page furniture below the card grid (timeline, numbers strip, ALSO list,
pin map, date check, footer), and this module owns the page skeleton -
masthead, hero row and card grid - plus the shared data tables below.
The drawing is fully deterministic: same data in, same PNG bytes out.
"""
import json
import os
import sys

from PIL import Image, ImageDraw

from illustrations import (CREAM, GOLD, GREY, ILLUSTRATIONS, INK, NAVY, PAPER,
                           RED, RULE, F, draw_text, line, rect, tw, wrap)
from layout import (also_list, date_check_box, footer, numbers_strip,
                    timeline_band, world_map)

W = H = 1024
MARGIN = 10

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


# ------------------------------------------------------------------- cards

def number_badge(d, x, y, n, size=15):
    rect(d, (x, y, x + size, y + size), fill=RED)
    f = F("sans_b", size * 0.62)
    draw_text(d, (x + size / 2, y + size * 0.10), str(n), f,
              fill=(252, 250, 240), anchor="ma")


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


# ------------------------------------------------------------------ render

def render(data):
    stories = data["stories"]
    total = len(stories)
    drawn = [s for s in stories if s["kind"] in ("hero", "card")]
    regions = {}
    for s in stories:
        regions[s["region"]] = regions.get(s["region"], 0) + 1
    fields = len({s["field"] for s in stories})

    img = Image.new("RGB", (W * 2, H * 2), CREAM)
    d = ImageDraw.Draw(img)

    # top strip
    rect(d, (0, 0, W, 20), fill=RED)
    f = F("sans_b", 9.5)
    draw_text(d, (MARGIN, 4.5), "THE WORLD IN ONE IMAGE - DAILY BROADSHEET", f,
              fill=(252, 246, 230))
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

    # page furniture below the grid (layout.py)
    timeline_band(d, data, 606)
    numbers_strip(d, data, 656)
    also_list(d, data, 700)
    world_map(d, data, LAND, (598, 700, 416, 168))
    date_check_box(d, data, (598, 878, 416))
    footer(d, data)

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
