"""Ability tokens and the buffs they give, using the wiki's spawn data (Ability Tokens page) and buff
values (Buffs & Debuffs page).

Every bee spawns its tokens while it's out gathering. A token's average spawn interval is
    use cooldown / r + attempt cooldown / r x (1 / (success x r) - 1)
where r is Bee Ability Rate. Collected tokens either collect pollen (bombs, Beamstorm, Scratch...),
give honey (Honey Gift, Token Link) or add buff stacks (Boost, Inspire, Focus, Pollen Mark...).

Buffs: a stacking buff keeps each stack for its duration, so the average number of stacks is
E[min(N, cap)] with N ~ Poisson(tokens/s x duration). A non-stacking buff is up 1 - e^(-rate x duration)
of the time.
"""

import math

from .data import GAME
from .stats import COLORS

# (use cooldown s, attempt cooldown s, success rate) per token, from the wiki
SPAWN = {
    "Bomb": (8, 4, 0.25), "Boost": (4.5, 4.5, 1 / 3), "Haste": (4.5, 4.5, 1 / 3), "Focus": (4.5, 4.5, 1 / 3),
    "Honey Gift": (120, 60, 0.25), "Token Link": (5, 5, 1 / 3), "Mark": (20, 5, 0.25), "Baby Love": (60, 5, 1 / 9),
    "Melody": (45, 15, 1 / 3), "Inspire": (60, 5, 0.01), "Fuzz Bombs": (20, 10, 1 / 3),
    "Target Practice": (24, 6, 0.25), "Inferno": (30, 5, 1 / 6), "Triangulate": (20, 10, 1 / 3),
    "Mark Surge": (24, 6, 0.25), "Bear Morph": (45, 15, 0.5), "Bomb Sync": (30, 15, 1 / 3),
    "Beamstorm": (20, 10, 1 / 3), "Puppy Love": (80, 10, 0.2), "Scratch": (12, 6, 0.25),
}

# Gather-category tokens each bee spawns (battle-only tokens like Rage and Impale don't spawn in a field).
BEE_TOKENS = {
    "Bomber": ["Buzz Bomb"], "Bumble": ["Blue Bomb"], "Cool": ["Blue Boost"], "Hasty": ["Haste"],
    "Looker": ["Focus"], "Rad": ["Red Boost"], "Rascal": ["Red Bomb"], "Stubborn": ["Pollen Mark"],
    "Bubble": ["Blue Bomb"], "Bucko": ["Blue Boost"], "Commander": ["Buzz Bomb", "Focus"], "Demo": ["Buzz Bomb+"],
    "Exhausted": ["Buzz Bomb", "Token Link"], "Fire": ["Red Bomb+"], "Frosty": ["Blue Bomb+", "Blue Boost"],
    "Honey": ["Honey Gift", "Honey Mark"], "Rage": ["Token Link"], "Riley": ["Red Boost"],
    "Shocked": ["Haste", "Token Link"], "Baby": ["Baby Love"], "Carpenter": ["Pollen Mark", "Honey Mark+"],
    "Demon": ["Red Bomb", "Red Bomb+"], "Diamond": ["Honey Gift+", "Blue Boost"], "Lion": ["Buzz Bomb+"],
    "Music": ["Focus", "Token Link", "Melody"], "Ninja": ["Blue Bomb+", "Haste"], "Shy": ["Red Bomb", "Red Boost"],
    "Buoyant": ["Blue Bomb"], "Fuzzy": ["Buzz Bomb+", "Fuzz Bombs"], "Precise": ["Target Practice"],
    "Spicy": ["Inferno"], "Tadpole": ["Blue Boost"], "Vector": ["Pollen Mark+", "Triangulate"],
    "Bear": ["Bear Morph"], "Cobalt": ["Blue Bomb Sync"], "Crimson": ["Red Bomb Sync"],
    "Festive": ["Honey Mark", "Red Bomb+"], "Photon": ["Haste", "Beamstorm"], "Puppy": ["Puppy Love"],
    "Tabby": ["Scratch"], "Vicious": ["Blue Bomb+"], "Windy": ["White Boost"],
}
GIFTED_TOKENS = {"Tadpole": ["Baby Love"], "Vector": ["Mark Surge"]}

NOT_MODELLED = ("Pulse, Glob, Gumdrop Barrage, Fetch, Tornado, Rain Cloud, Glitch, Mind Hack, Inflate Balloons, "
                "Surprise Party, Festive Gift, Honey Mark conversion links, flames, Tabby Love growth")

# Buffs: (per-stack value, max stacks, duration s)
BOOST = (0.2, 10, 15)          # x1.2 colour pollen per stack, up to x3
BOMB_COMBO = (0.25, 10, 5)     # x1.25 Bomb Power per stack, up to x3.5
FOCUS = (0.03, 10, 20)         # +3% Critical Chance per stack, up to +30%
INSPIRE = (1.0, 50, 5)         # x2 Pollen per stack, up to x51
HASTE = (0.1, 10, 20)          # x1.1 movespeed per stack, up to x2
MELODY_SECONDS, BABY_LOVE_SECONDS, BEAR_MORPH_SECONDS, BOMB_SYNC_SECONDS = 30, 30, 30, 30
TOKEN_LIFESPAN = 4             # most tokens fade after 4 s


def family(token):
    if "Bomb Sync" in token:
        return "Bomb Sync"
    if token.endswith(("Bomb", "Bomb+")):
        return "Bomb"
    if token.endswith("Boost"):
        return "Boost"
    if token.startswith("Honey Gift"):
        return "Honey Gift"
    if "Mark" in token and token != "Mark Surge":
        return "Mark"
    return token


def interval(token, ability_rate=1.0):
    use, attempt, p = SPAWN[family(token)]
    r = max(ability_rate, 0.01)
    return use / r + attempt / r * (1 / min(1.0, p * r) - 1)


def avg_stacks(rate, duration, cap):
    """E[min(N, cap)] for N ~ Poisson(rate x duration)."""
    lam = rate * duration
    if lam <= 0:
        return 0.0
    if lam > cap + 12 * math.sqrt(cap + lam):
        return float(cap)
    total, p = 0.0, math.exp(-lam)
    below = 0.0
    for k in range(cap):
        total += k * p
        below += p
        p *= lam / (k + 1)
    return total + cap * (1 - below)


def uptime(rate, duration):
    return 1 - math.exp(-rate * duration) if rate > 0 else 0.0


def bee_tokens(bee):
    toks = list(BEE_TOKENS.get(bee["type"], []))
    if bee["gifted"]:
        toks += GIFTED_TOKENS.get(bee["type"], []) + ["Inspire"]
    bq = GAME["beequips"].get(bee.get("beequip") or "")
    for a in (bq or {}).get("Abilities", []):
        name = a.get("Name", "")
        if family(name) in SPAWN and name not in toks:
            toks.append(name)
    return toks


def token_rates(bees, rows, hive_ability_rate, pickup):
    """Collected tokens per second: list of dicts (token, bee row, level, gifted, rate)."""
    out = []
    for b, row in zip(bees, rows):
        rate_mult = hive_ability_rate * row["_bs"].get("bee:ability_rate")
        for tok in bee_tokens(b):
            out.append({"token": tok, "type": b["type"], "level": row["level"], "gifted": b["gifted"],
                        "row": row, "bs": row["_bs"], "rate": row["uptime"] / interval(tok, rate_mult) * pickup})
    return out


def buffs(tokens, hive, s):
    """Average buff values from the collected tokens."""
    by = {}
    for t in tokens:
        by.setdefault(t["token"], []).append(t)
    rate = lambda name: sum(t["rate"] for t in by.get(name, []))

    boosts = {c: 1 + BOOST[0] * avg_stacks(rate(f"{c.title()} Boost"), BOOST[2], BOOST[1]) for c in COLORS}
    inspire = 1 + INSPIRE[0] * avg_stacks(rate("Inspire"), INSPIRE[2], INSPIRE[1])
    baby = 1 + uptime(rate("Baby Love"), BABY_LOVE_SECONDS)
    # Bear Morph: x2 pollen; a gifted Bear Bee has a 20% chance of Mother Bear (x2.5 pollen, x1.5 bee gather)
    bear_rate = rate("Bear Morph")
    gifted_bear = any(t["gifted"] for t in by.get("Bear Morph", []))
    mother_share = 0.2 if gifted_bear else 0.0
    bear_up = uptime(bear_rate, BEAR_MORPH_SECONDS)
    bear = 1 + bear_up * ((1 - mother_share) * 1.0 + mother_share * 1.5)
    bear_gather = 1 + bear_up * mother_share * 0.5
    # Pollen Mark: x1.5 per linked mark up to x2.5, only while you stand in it
    mark_mult = 1.0
    marks = by.get("Pollen Mark", []) + by.get("Pollen Mark+", [])
    m_rate = sum(t["rate"] for t in marks)
    if m_rate > 0:
        dur = sum(t["rate"] * ((8 + 0.25 * t["level"]) if t["token"].endswith("+") else (7 + 0.2 * t["level"]))
                  for t in marks) / m_rate * hive.get("mark_duration")
        mark_mult = 1 + 0.5 * avg_stacks(m_rate, dur, 3) * s["mark_stand_pct"] / 100
    active_marks = avg_stacks(m_rate, 8 * hive.get("mark_duration"), 5)
    focus = FOCUS[0] * avg_stacks(rate("Focus"), FOCUS[2], FOCUS[1])
    melody = 1.0 * uptime(rate("Melody"), MELODY_SECONDS)
    bomb_tokens = sum(t["rate"] for t in tokens if family(t["token"]) == "Bomb") + rate("Fuzz Bombs")
    bomb_combo = 1 + BOMB_COMBO[0] * avg_stacks(bomb_tokens, BOMB_COMBO[2], BOMB_COMBO[1])
    haste = 1 + HASTE[0] * avg_stacks(rate("Haste"), HASTE[2], HASTE[1])
    puppy = by.get("Puppy Love", [])
    puppy_up = uptime(rate("Puppy Love"), 10 + max([t["level"] for t in puppy], default=0))
    sync = {"red": uptime(rate("Red Bomb Sync"), BOMB_SYNC_SECONDS),
            "blue": uptime(rate("Blue Bomb Sync"), BOMB_SYNC_SECONDS)}
    return {
        "pollen": inspire * baby * bear * mark_mult,
        "inspire": inspire, "baby_love": baby, "bear_morph": bear, "pollen_mark": mark_mult,
        "boost": boosts, "crit_chance": focus, "crit_power": melody, "bomb_power": bomb_combo,
        "haste": haste, "bee_gather": (1 + 0.5 * puppy_up) * bear_gather, "bomb_sync": sync,
        "active_marks": active_marks,
    }


def token_yield(tokens, ctx):
    """Pollen (by colour), instantly-converted pollen and honey per second from pollen and honey tokens.

    ctx holds: frac, tier, pollen, color_pollen, hive, crit_factor (expected, for abilities that crit),
    crit_power, sync, bomb_power, settings, fire_bee_rate (pollen/s of a Fire Bee by level)."""
    frac, tier, hive, s = ctx["frac"], ctx["tier"], ctx["hive"], ctx["settings"]
    pollen_by = {c: 0.0 for c in COLORS}
    instant_by = {c: 0.0 for c in COLORS}
    honey, detail = 0.0, {}
    ability_pollen = hive.get("bee_ability_pollen") * (1 + s["ability_pollen_pct"] / 100)
    all_tokens_rate = sum(t["rate"] for t in tokens)

    def add(label_, per_color, rate, instant=0.0):
        got = 0.0
        for c in COLORS:
            p = per_color[c] * rate
            pollen_by[c] += p
            instant_by[c] += p * instant
            got += p
        detail[label_] = detail.get(label_, {"pollen": 0.0, "honey": 0.0, "rate": 0.0})
        detail[label_]["pollen"] += got
        detail[label_]["rate"] += rate

    def flowers(per_flower, count, colors=COLORS, extra=1.0, white_mult=1.0):
        return {c: (per_flower * count * frac[c] * tier * ctx["pollen"] * ctx["color_pollen"][c] * extra
                    * (white_mult if c == "white" else 1.0) if c in colors else 0.0) for c in COLORS}

    for t in tokens:
        tok, lvl, row = t["token"], t["level"], t["row"]
        bee_mult = ability_pollen * t["bs"].get("bee:ability_pollen")
        fam = family(tok)
        if fam == "Bomb":
            plus = tok.endswith("+")
            count = 29 if plus else 13
            power = ctx["bomb_power"] * hive.get("bomb_power")
            mult = lvl / 10 * power * hive.get("bomb_pollen") * t["bs"].get("bee:bomb_pollen") * bee_mult
            if tok.startswith("Buzz"):
                per = flowers(7, count, extra=mult * hive.get("buzz_bomb_pollen"))
            else:
                col = "red" if tok.startswith("Red") else "blue"
                sync = ctx["sync"][col]
                per = flowers(10, count, extra=mult * hive.get(f"{col}_bomb_pollen"))
                per = {c: (per[c] if c == col else per[c] * sync if c == "white" else 0.0) for c in COLORS}
            add(tok, per, t["rate"], min(hive.get("instant_bomb_conversion"), 1.0))
        elif tok == "Fuzz Bombs":
            n = 2 + lvl // 5
            caught = s["fuzz_bomb_catch_pct"] / 100
            power = ctx["bomb_power"] * hive.get("bomb_power")
            per = flowers(7, 29, extra=n * caught * lvl / 10 * power * hive.get("bomb_pollen")
                          * hive.get("buzz_bomb_pollen") * bee_mult)
            add(tok, per, t["rate"], min(hive.get("instant_bomb_conversion"), 1.0))
        elif tok == "Beamstorm":
            beams = 25 + 2 * lvl
            content = 30 + 15 * (tier - 1)       # a beam takes all the flower's pollen, x2
            per = {c: beams * frac[c] * content * 2 * ctx["pollen"] * ctx["color_pollen"][c] * bee_mult
                   * (3 if (t["gifted"] and c == "white") else 1) for c in COLORS}
            add(tok, per, t["rate"], 1.0 if t["gifted"] else 0.0)
        elif tok == "Scratch":
            tabby = 1 + s["tabby_love_stacks"] / 100
            crit = ctx["crit_power"] if t["gifted"] else ctx["crit_factor"]
            add(tok, flowers(7 + lvl, 12, extra=tabby * crit * bee_mult), t["rate"])
        elif tok == "Triangulate":
            add(tok, flowers(10 + 2 * lvl, s["triangle_flowers"], extra=bee_mult), t["rate"])
        elif tok == "Mark Surge":
            marks_up = ctx["active_marks"]
            add(tok, flowers(7 * lvl / 10, 64 * marks_up, extra=bee_mult), t["rate"])
        elif tok == "Target Practice":
            attack = GAME["bees"]["Precise"]["attack"] * (1.5 if t["gifted"] else 1)
            add(tok, flowers(2 * attack * lvl / 10, 29 * s["targets_hit"], extra=bee_mult), t["rate"])
        elif tok == "Inferno":
            # 2 temporary Fire Bees, 2 levels lower, for 15 s + 1 s per level
            bee_seconds = 2 * (15 + lvl)
            fire = ctx["fire_bee_rate"](max(1, lvl - 2))
            add(tok, {c: fire[c] * bee_seconds for c in COLORS}, t["rate"])
        elif fam == "Honey Gift":
            amount = (250 if tok.endswith("+") else 100) * lvl ** 2 * hive.get("honey_from_tokens")
            honey += amount * t["rate"]
            detail.setdefault(tok, {"pollen": 0.0, "honey": 0.0, "rate": 0.0})
            detail[tok]["honey"] += amount * t["rate"]
            detail[tok]["rate"] += t["rate"]
        elif tok == "Token Link":
            # links every other token still on the field: 25 + 10 per level honey each
            others = max(0.0, all_tokens_rate - t["rate"]) * TOKEN_LIFESPAN / 2
            amount = (25 + 10 * lvl) * others
            honey += amount * t["rate"]
            detail.setdefault(tok, {"pollen": 0.0, "honey": 0.0, "rate": 0.0})
            detail[tok]["honey"] += amount * t["rate"]
            detail[tok]["rate"] += t["rate"]
        else:
            detail.setdefault(tok, {"pollen": 0.0, "honey": 0.0, "rate": 0.0})
            detail[tok]["rate"] += t["rate"]
    return pollen_by, instant_by, honey, detail
