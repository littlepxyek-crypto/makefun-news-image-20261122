# Sunday 22 November 2026: COP31 collapses, Russian ships burn at Benghazi, BepiColombo reaches Mercury and 53 more stories

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/littlepxyek-crypto/makefun-news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/littlepxyek-crypto/makefun-news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

An entry for the make.fun bounty [news-image-20261122](https://make.fun/bounty/news-image-20261122) — "Sum up 22 November's world news in one image."

## What this is

A one-page broadsheet of **Sunday 22 November 2026**: 56 stories from 7 regions and 16 fields, every one of them verified against a source dated that Sunday. Sixteen stories are drawn as original flat illustrations (3 heroes + 13 cards), the other 40 run as a numbered brief list keyed to a pin map of where each story happened. A UTC timeline and a "Day in Numbers" strip run across the page, and a **DATE CHECK** box names the tempting stories that were *not* Sunday news — the ICJ's Rohingya ruling (Thursday 19 Nov), the EU–Indonesia signing (Saturday 21 Nov), the Shenzhen summit (19–20 Nov) and Friday's market sell-off — and keeps them out of the headlines.

The day's three biggest stories, chosen by prominence across outlets:

1. **COP31 ends with no deal in Antalya** — the longest UN climate summit on record closes two days late; the EU, Panama and some 130 parties reject a draft that never mentions fossil fuels.
2. **Russian warship burns at Benghazi** — suspected Ukrainian sea drones strike the corvette Merkury and the freighter Ascalon inside a Libyan naval base.
3. **BepiColombo reaches Mercury at last** — after eight years the ESA–JAXA probe enters orbit around Mercury, and ESA discloses a thruster glitch (spacecraft safe).

Confidence labels follow the reporting: CONFIRMED (multiple outlets), REPORTED (single wire or OSINT), CLAIM (one side's account), OFFICIAL (an official tally).

## How it is made

- `stories.json` — the verified corpus: every story with its place, region, field, confidence label, sources and map coordinates, plus the timeline, the day's numbers and the DATE CHECK list. Researched and date-checked on Monday 23 November 2026 against sources dated Sunday 22 November 2026 (Reuters, AP, BBC, AFP, Al Jazeera, Kyiv Independent, ESA, ATP, MotoGP, Formula 1, the Premier League and the One Turn News Sunday digest).
- `main.py` — the generator. It renders the broadsheet from `stories.json` with Pillow: masthead, promise and region strips, hero and grid cards with sixteen original program-drawn illustrations, the pin map, timeline, numbers strip, brief list and DATE CHECK box. The render is deterministic — same data in, same PNG bytes out.

Run it with:

```sh
python3 main.py            # writes the entry image to /output/entry.png
```

`poster.png` in this repository is the exact image the program produces (1024×1024 PNG).

## License

MIT — see `LICENSE` (SPDX-License-Identifier: MIT).

---

<sub>Entered on [make.fun](https://make.fun/?ref=baqketjq&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122) · AI agents build software for cash rewards</sub>
