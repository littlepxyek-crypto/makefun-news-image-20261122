#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Section layout for the news-image-20261122 broadsheet entry.

main.py owns the page skeleton (masthead, hero row, card grid); this
module paints the furniture below it: the UTC timeline band, the
day-in-numbers strip, the two-column ALSO list with its auto-fitting
type size, the pin map, the DATE CHECK box and the footer rules.

Everything here works in the same 1024-unit design space as
illustrations.py and reuses its primitives, so the whole page shares
one scaling and palette. Data that belongs to the entry as a whole
(the coarse world-land grid, the label colours) is passed in by the
caller rather than duplicated here.
"""
from illustrations import (CREAM, GOLD, GREY, INK, NAVY, PAPER, RED, RULE,
                           WHITE, F, draw_text, ellipse, line, rect, tw, wrap)

MARGIN = 10
PAGE_W = 1024


def timeline_band(d, data, y):
    """A paper band: red 'THE DAY IN UTC' tab, then one column per entry."""
    rect(d, (MARGIN, y, PAGE_W - MARGIN, y + 44), fill=PAPER, outline=RULE, width=1)
    f = F("sans_b", 9.5)
    draw_text(d, (MARGIN + 7, y + 8), "THE DAY", f, fill=RED)
    draw_text(d, (MARGIN + 7, y + 20), "IN UTC", f, fill=RED)
    line(d, [(MARGIN + 62, y + 5), (MARGIN + 62, y + 39)], fill=RULE, width=1)
    entries = data["timeline"]
    colw = (PAGE_W - 2 * MARGIN - 76) / max(1, len(entries))
    for i, (stamp, text) in enumerate(entries):
        cx = MARGIN + 70 + i * colw
        draw_text(d, (cx, y + 4), stamp, F("sans_b", 8.6), fill=NAVY)
        yy = y + 16
        for ln in wrap(d, text, F("sans", 7.8), colw - 8)[:3]:
            draw_text(d, (cx, yy), ln, F("sans", 7.8), fill=INK)
            yy += 9.6


def numbers_strip(d, data, y):
    """A black band: gold title at the left, then big number + caption cells."""
    rect(d, (MARGIN, y, PAGE_W - MARGIN, y + 34), fill=INK)
    f = F("sans_b", 9)
    draw_text(d, (MARGIN + 8, y + 11), "THE DAY IN NUMBERS", f, fill=GOLD)
    nx = MARGIN + 128
    cells = data["numbers"]
    cellw = (PAGE_W - MARGIN - nx - 6) / max(1, len(cells))
    for i, (num, cap) in enumerate(cells):
        cx = nx + i * cellw
        draw_text(d, (cx, y + 3), num, F("display", 17), fill=GOLD)
        for ln in wrap(d, cap, F("sans", 6.9), cellw - 6)[:1]:
            draw_text(d, (cx, y + 23), ln, F("sans", 6.9), fill=(238, 234, 220))


def _also_item_lines(d, story, n, size):
    """Split one ALSO entry into its bold head and wrapped plain-text lines."""
    head = "%d  %s - " % (n, story["place"].upper())
    fb, fr = F("sans_b", size), F("sans", size)
    headw = tw(d, head, fb)
    lines, cur, curw = [], [], headw
    for word in story["text"].split():
        ww = tw(d, word + " ", fr)
        if curw + ww <= 282 or not cur:
            cur.append(word)
            curw += ww
        else:
            lines.append(cur)
            cur, curw = [word], tw(d, word + " ", fr)
    if cur:
        lines.append(cur)
    return head, lines


def _also_col_height(d, items, start, size):
    return sum(len(_also_item_lines(d, s, start + j, size)[1]) * (size + 2.0) + 2.6
               for j, s in enumerate(items))


def also_list(d, data, y, bottom=990):
    """The 'ALSO ON SUNDAY' briefs: two numbered columns, stories 17 onward.

    The type size steps down from 9.2 until both columns fit above the
    footer; the drawn stories never appear here, only the list kind.
    """
    stories = data["stories"]
    total = len(stories)
    lst = [s for s in stories if s["kind"] == "list"]
    first = total - len(lst) + 1
    f = F("sans_b", 10.5)
    draw_text(d, (MARGIN, y), "ALSO ON SUNDAY", f, fill=INK)
    note = "- the rest of the day in brief, stories %d-%d" % (first, total)
    draw_text(d, (MARGIN + tw(d, "ALSO ON SUNDAY", f) + 6, y + 1), note,
              F("sans", 9), fill=GREY)
    line(d, [(MARGIN, y + 15), (590, y + 15)], fill=INK, width=1.2)
    half = (len(lst) + 1) // 2
    cols = [(MARGIN, lst[:half], first), (304, lst[half:], first + half)]
    size = 9.2
    while size > 7.5 and any(y + 21 + _also_col_height(d, items, start, size) > bottom
                             for _, items, start in cols):
        size -= 0.4
    for cx, items, start in cols:
        yy = y + 21
        fb, fr = F("sans_b", size), F("sans", size)
        for j, s in enumerate(items):
            head, lines = _also_item_lines(d, s, start + j, size)
            draw_text(d, (cx, yy), head, fb, fill=INK)
            draw_text(d, (cx + tw(d, head, fb), yy), " ".join(lines[0]), fr, fill=INK)
            yy += size + 2.0
            for ln in lines[1:]:
                draw_text(d, (cx, yy), " ".join(ln), fr, fill=INK)
                yy += size + 2.0
            yy += 2.6


def world_map(d, data, land, box):
    """The pin map: land cells from the coarse grid, dots for list stories,
    and numbered red pins for the drawn stories, nudged apart so no two
    pins overlap."""
    mx0, my0, mw, mh = box
    rect(d, (mx0, my0, mx0 + mw, my0 + mh), fill=(238, 233, 210), outline=RULE, width=1)
    f = F("sans_b", 8.6)
    draw_text(d, (mx0 + 7, my0 + 4), "WHERE IT HAPPENED - PIN NUMBERS MATCH THE STORIES",
              f, fill=NAVY)
    gx, gy, gw, gh = mx0 + 8, my0 + 18, mw - 16, mh - 26
    cellw, cellh = gw / 90, gh / 44
    for r, spans in land.items():
        for c0, c1 in spans:
            for c in range(c0, c1 + 1):
                rect(d, (gx + c * cellw + 0.4, gy + r * cellh + 0.4,
                         gx + (c + 1) * cellw - 0.4, gy + (r + 1) * cellh - 0.4),
                     fill=(168, 172, 158))

    def pin_xy(lon, lat):
        return (gx + (lon + 168) / 360 * gw, gy + (76 - lat) / 140 * gh)

    stories = data["stories"]
    drawn = [s for s in stories if s["kind"] in ("hero", "card")]
    for s in stories:
        if s["kind"] == "list" and s["lon"] is not None:
            px_, py_ = pin_xy(s["lon"], s["lat"])
            ellipse(d, (px_ - 1.7, py_ - 1.7, px_ + 1.7, py_ + 1.7), fill=(90, 88, 80))
    placed = []
    offsets = [(0, 0), (10, -7), (-10, -7), (10, 8), (-10, 8),
               (0, -12), (0, 12), (13, 0), (-13, 0)]
    for i, s in enumerate(drawn):
        px_, py_ = pin_xy(s["lon"], s["lat"])
        for ox, oy in offsets:
            cand = (px_ + ox, py_ + oy)
            if all((cand[0] - q[0]) ** 2 + (cand[1] - q[1]) ** 2 >= 121
                   for q in placed):
                px_, py_ = cand
                break
        placed.append((px_, py_))
        r = 7.2
        ellipse(d, (px_ - r, py_ - r, px_ + r, py_ + r), fill=RED,
                outline=WHITE, width=1.2)
        draw_text(d, (px_, py_ - 3.6), str(i + 1), F("sans_b", 7.6),
                  fill=WHITE, anchor="ma")


def date_check_box(d, data, box, bottom=990):
    """The red-ruled box listing tempting stories that failed the date test."""
    mx0, dy0, mw = box
    rect(d, (mx0, dy0, mx0 + mw, bottom), fill=PAPER, outline=RED, width=1.4)
    f = F("sans_b", 9.6)
    draw_text(d, (mx0 + 8, dy0 + 5), "DATE CHECK - NOT SUNDAY, SO NOT HEADLINES",
              f, fill=RED)
    yy = dy0 + 21
    for item in data["date_check"]:
        lines = wrap(d, item, F("serif", 8.8), mw - 30)
        draw_text(d, (mx0 + 8, yy), "x", F("sans_b", 8.8), fill=RED)
        for ln in lines:
            draw_text(d, (mx0 + 20, yy), ln, F("serif", 8.8), fill=INK)
            yy += 11
        yy += 2.5


def footer(d, data):
    """Source line, label key and the original-drawings credit."""
    line(d, [(MARGIN, 994), (PAGE_W - MARGIN, 994)], fill=INK, width=1.2)
    f = F("sans", 7.6)
    draw_text(d, (MARGIN, 999),
              "Sources: Reuters - AP - BBC - AFP - Al Jazeera - ATP - MotoGP - "
              "Formula 1 - Kyiv Independent - ESA - Premier League. Every story "
              "dated Sunday 22 Nov 2026.", f, fill=GREY)
    draw_text(d, (MARGIN, 1009),
              "Labels: CONFIRMED = multiple outlets - REPORTED = single wire/OSINT - "
              "CLAIM = one side's account - OFFICIAL = official tally", f, fill=GREY)
    t = "Original drawings - drawn by this program from stories.json"
    draw_text(d, (PAGE_W - MARGIN - tw(d, t, f), 1009), t, f, fill=GREY)
