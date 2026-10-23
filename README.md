# BSS Honey Calculator

A desktop app (Python + [Flet](https://flet.dev)) that estimates **honey per hour** for a Bee Swarm Simulator setup and shows how much you gain or lose when you change it.

**Website:** https://rontherentalcop.github.io/BeeSwarmSimulator-Calculator/
It runs entirely in your browser. The first load takes a little while, and your setups save in your browser.

## Run it on your computer

```bash
cd bss-honey-calc
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

The first launch downloads Flet's desktop client, which takes a moment.

## What you can do

- **Setup**
  - **Hive:** a visual 5×10 hive (slot 1 is bottom-left, like the game). Pick a bee from the palette of all 46 bee faces (filterable by rarity), then click any empty slot to place it there; gaps are allowed. Click a placed bee to edit its level, gifted status, beequip and exact stats, or to move it (arrows, "Go to slot", or move mode: click any slot and it moves or swaps), copy it or remove it.
  - **Gear:** pick your tool, bag, mask, guards, belt and boots.
  - **Amulets:** choose each amulet and enter the stats it rolled.
  - **Badges:** pick your tier in each badge category.
  - **Buffs & Items:** add item buffs (Super Smoothie, Purple Potion, Field Boost…) with their exact wiki values, plus anything else you keep running.
  - **Alts:** add alt accounts macroing in your field, such as a Fuzzy alt, a Tad alt or both.
  - **Field & Settings:** pick your field and set nectars, Balloon Blessing, Polar Power, Honeyday, your gather time and the other model settings.
  - **System Page:** type in totals from your in-game System Page to replace the calculated ones. This covers the sticker stack, Robo upgrades and anything else the app can't see.
- **Results**
  - Shows honey/hr, honey/day, pollen/s from bees and from your tool, capacity, bag fill and convert times, and instant conversion.
  - Shows your stat totals, so you can check them against your in-game System Page, and a per-bee breakdown.
  - **"Where your next gains come from"** ranks how much honey/hr each stat bump would add.
- **Guide & template hives:** blue and red template hives taken only from published guides. Blue covers Anthrax's stages 1-4 (by level) plus Meta Bee's Standard and Diamond hives; red is Meta Bee's endgame hive (credible red guides only publish level 20+ hives). Load any template as a new setup with the guide's beequips. Below the templates is a blue hive guide covering comps, progression, beequips, amulets, mutations and gifting.
- **Compare:** duplicate a setup (copy icon at the top), change something, and see the honey/hr difference stat by stat.

Setups save automatically: in your browser on the website, and in the app's own storage on desktop.

## Images

Bee faces, bee renders (normal and gifted), beequips, tools, gear and amulets are downloaded from the Bee Swarm Simulator Fandom wiki into `bss_calc/assets/img`. The game art belongs to Onett / Bee Swarm Simulator. To fetch them again:

```bash
.venv/bin/python tools/fetch_images.py
```

## Game data

`bss_calc/game_data.json` holds 46 bees, 20 tools, 46 gear items, 17 fields, 41 beequips and 26 amulets. It was pulled from the Bee Swarm Simulator Fandom wiki on 2026-10-21. Beequip and amulet stats come from the wiki's copy of the game files.

## How the estimate works

The **How it works** page in the app explains the full model. In short:

- **Bees**
  - Gather is `base × flower tier × (1 + 5%/level) × 1.5 if gifted`; convert is +10% per level, where single = ×1 up to star = ×5. A crit doubles a gather.
  - Red and blue bees get +50% on flowers of their own colour.
  - Energy and movespeed scale with level; tired bees fly home and sleep.
- **Pollination**
  - Each hit raises a flower one tier; it drops a tier per minute without one; lower tiers are picked more often.
  - The app simulates your gathering area to find the average tier.
  - Sources: Fuzzy Coat, Lei/Poinsettia/Rose Headband, Pollen Haze, Guiding Star and Diamond Drain.
- **Bubbles:** 4 red / 6 white / 8 blue pollen from 29 flowers (+15% per gifted blue type, +5% per level). You only get pollen from your own bubbles and from frog bubbles.
- **Alts:** flowers are shared, so an alt's Fuzzy Coat and Pollen Haze raise your flower tiers. Pollen Haze can only happen once per 3 minutes per field. An alt's frogs pay you too, but its own Gathering Bubbles and tokens only help the alt. Token rates come from the wiki's spawn data.
- **Ability tokens:** every bee spawns its abilities at the wiki's spawn rates (adjusted by Bee Ability Rate). Bombs, Beamstorm, Scratch, Triangulate, Target Practice and the rest collect their wiki amounts. Boost, Inspire, Focus, Melody, Baby Love, Bear Morph, Pollen Mark and Bomb Combo buffs stack using their wiki values.
- **Balloons:** Buoyant balloons catch pollen under their shadow and are converted at the hive, where Buoyant Bees convert them ×3. Balloon Blessing multiplies Capacity and Honey at Hive.
- **Honey at Hive:** Shimmering Honey from Diamond Bees, Honey at Hive stats and Honey Per Pollen multiply every hive conversion.
- **Passives:** Diamond Drain, Star Shower, Coin Scatter and Petal Storm convert bag pollen while you're in the field. Pop Star gives Blue Pollen and Bubble Bloat. Star Amulet passives add their capacity bonuses.
- **Attack:** each bee's attack is calculated and shown.
- **Stats:** each stat is `(100% + every "+%") × every "x"`. Gifted hive bonuses count once per bee type.
- **Honey loop:** you gather until the bag is full (less any instant conversion), walk to the hive, and your bees convert the bag.

**Not simulated:** Pulse, Tornado, Rain Cloud, Glob and goo, flames, Coconut Combo, Tide Popper waves, mobs, planters, and alts taking pollen from the same flowers. Use the Buffs & Items tab or System Page overrides for these.

**Assumptions you can change:**
- Base crit chance 5%.
- Average flight distances.
- Gathering area (200 flowers).
- How full Fuzzy Coat's "up to 5/9 flowers" is (50%).
- Uptimes for Pollen Haze, Guiding Star and Diamond Drain.

## Update the website

The site is a static build made with `flet publish`, which runs Python in the browser through Pyodide. It's hosted on GitHub Pages from the `gh-pages` branch. To rebuild and redeploy it:

```bash
tools/deploy_site.sh
```
