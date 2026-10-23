"""Passive abilities (gear, Star Amulet, bees) and Buoyant balloons, from the wiki's Passive Abilities,
Balloon and Buffs & Debuffs pages.

Triggered passives fire every Nth token of a kind, but not faster than their cooldown:
    activations/s = min(1 / cooldown, token rate / N)
"""

import math

from .abilities import family, interval, uptime

STAR_PASSIVES = {
    "Diamond Star Amulet": ["Guiding Star", "Star Shower"],
    "Supreme Star Amulet": ["Guiding Star", "Pop Star", "Star Shower", "Gummy Star", "Scorching Star", "Star Saw"],
}
# permanent bonus each Star passive gives just by being on the amulet
STAR_STATIC = {
    "Guiding Star": [["capacity", "mul", 1.25]], "Star Shower": [["capacity", "mul", 1.25]],
    "Pop Star": [["blue_field_capacity", "mul", 1.25]], "Gummy Star": [["white_field_capacity", "mul", 1.25]],
    "Scorching Star": [["red_field_capacity", "mul", 1.25]],
}
GEAR_PASSIVES = {   # passive -> items that grant it
    "Diamond Drain": ["Diamond Mask"], "Coin Scatter": ["Honey Mask"], "Petal Storm": ["Petal Belt", "Coconut Belt"],
    "Bubble Bombs": ["Bubble Mask", "Diamond Mask"],
}
BLOAT_MAX_SECONDS = 2.5 * 3600
BALLOON_SHADOW_FLOWERS = math.pi * 5 ** 2      # a balloon's shadow has a 5-tile radius
INFLATE = (28, 8, 0.25)                         # Inflate Balloons spawn data


def star_passives(setup):
    am = setup.get("amulets", {}).get("Star") or {}
    allowed = STAR_PASSIVES.get(am.get("name") or "", [])
    return [p for p in am.get("passives", []) if p in allowed]


def gear_passives(setup):
    worn = set(setup.get("gear", {}).values())
    return [p for p, items in GEAR_PASSIVES.items() if worn & set(items)]


def activations(rate, every, cooldown=0.0):
    per_s = rate / every
    return min(per_s, 1 / cooldown) if cooldown else per_s


def triggered(tokens, setup, ctx):
    """Pollen/s converted straight out of your bag in the field, extra bubbles/s and buff multipliers from
    triggered passives. Diamond Drain, Star Shower, Coin Scatter and Petal Storm all convert pollen you're
    carrying, so they can't convert more than you collect.

    ctx: hpp, honey_from_tokens, convert_total (sum of bees' convert amounts), blue_bees, gifted_blue_types,
    gifted_types, own_bubbles_per_sec, pop_pct."""
    rate_of = lambda pred: sum(t["rate"] for t in tokens if pred(t["token"]))
    boosts = rate_of(lambda n: family(n) == "Boost")
    marks = rate_of(lambda n: family(n) == "Mark")
    bombs = rate_of(lambda n: family(n) == "Bomb")
    blue = rate_of(lambda n: n.startswith("Blue"))
    converts, detail = 0.0, {}
    out = {"blue_pollen": 1.0, "red_pollen": 1.0, "instant_blue": 0.0, "bloat": 1.0, "bubbles_per_sec": 0.0}
    stars, gear = star_passives(setup), gear_passives(setup)

    def give(name, per_s, pollen):
        nonlocal converts
        converts += per_s * pollen
        detail[name] = {"per_min": per_s * 60, "pollen_per_sec": per_s * pollen}

    if "Diamond Drain" in gear:
        # every 30th blue token (45 s cooldown): converts 5M + Convert Total, +10% per blue bee, +50% per gifted blue type
        a = activations(blue, 30, 45)
        pollen = (5e6 + ctx["convert_total"]) * (1 + 0.1 * ctx["blue_bees"] + 0.5 * ctx["gifted_blue_types"])
        give("Diamond Drain", a, pollen)
    if "Coin Scatter" in gear:
        # every 20th mark (2 min cooldown): 300% of Convert Total as 24 honey tokens (1,000 minimum each)
        a = activations(marks, 20, 120)
        give("Coin Scatter", a, max(3 * ctx["convert_total"], 24_000))
    if "Petal Storm" in gear:
        # every 30th boost (30 s cooldown): 30 shurikens, each makes a bee convert 10,000 + 7% of its convert amount
        a = activations(boosts, 30, 30)
        give("Petal Storm", a, 30 * (10_000 + 0.07 * ctx["avg_convert"]))
    if "Bubble Bombs" in gear:
        a = activations(bombs, 25, 120)
        out["bubbles_per_sec"] += 25 * a
        detail["Bubble Bombs"] = {"per_min": a * 60, "pollen_per_sec": 0.0}
    if "Star Shower" in stars:
        # every 40th boost/mark (30 s cooldown): 10 shooting stars, each caught converts 1M + 200% of Convert Total
        a = activations(boosts + marks, 40, 30)
        caught = 10 * ctx["catch_pct"]
        give("Star Shower", a, caught * (1e6 + 2 * ctx["convert_total"]))
    if "Pop Star" in stars:
        # every 30th boost (1 min cooldown): 45 s of x2 Blue Pollen (+1% per own bubble popped, up to x4.5)
        # and +10% Instant Blue Conversion; 2 min of Bubble Bloat plus 4 s per own bubble popped
        a = activations(boosts, 30, 60)
        on = min(1.0, a * 45)
        popped = ctx["own_bubbles_per_sec"] * ctx["pop_pct"] * 45
        during = 2 + min(2.5, 0.01 * popped / 2)
        out["blue_pollen"] *= 1 + on * (during - 1)
        out["instant_blue"] += 0.10 * on
        if a > 0:
            gained, period = 120 + 4 * popped, 1 / a
            remaining = BLOAT_MAX_SECONDS if gained >= period else gained / 2
            out["bloat"] = 1 + 5 * min(remaining, BLOAT_MAX_SECONDS) / BLOAT_MAX_SECONDS
        detail["Pop Star"] = {"per_min": a * 60, "pollen_per_sec": 0.0}
    if "Scorching Star" in stars:
        a = activations(boosts, 30, 60)
        on = min(1.0, a * 45)
        out["red_pollen"] *= 1 + on        # x2 Red Pollen while active (more with flames, not modelled)
        detail["Scorching Star"] = {"per_min": a * 60, "pollen_per_sec": 0.0}
    if "Guiding Star" in stars:
        detail["Guiding Star"] = {"per_min": activations(boosts, 250, 300) * 60, "pollen_per_sec": 0.0}
    return converts, out, detail


def balloons(bees, rows, hive_ability_rate, pickup, capacity, area):
    """Blue/gold balloons from Buoyant Bees' Inflate Balloons.

    Returns (share of your field pollen the balloons catch, max pollen/s they can hold, boost on caught pollen)."""
    alive, hold = 0.0, 0.0
    for b, row in zip(bees, rows):
        if b["type"] != "Buoyant":
            continue
        rate = row["uptime"] / interval_raw(INFLATE, hive_ability_rate * row["_bs"].get("bee:ability_rate")) * pickup
        life = 20 + 2 * row["level"]
        gold = min(1.0, 0.05 + 0.005 * row["level"]) if b["gifted"] else 0.0
        size = capacity / 6 * (1 + 0.25 * gold)                 # blue balloon = capacity/6, gold x1.25
        alive += rate * life
        hold += rate * size
    if alive <= 0:
        return 0.0, 0.0, 1.0, 0.0
    cover = 1 - math.exp(-alive * BALLOON_SHADOW_FLOWERS / max(area, 1))
    inflate = 1 + 0.05 * min(10, alive)                         # Inflate Balloons adds +5% to every balloon, 10 times max
    return cover, hold * inflate, inflate, alive


def interval_raw(spawn, r):
    use, attempt, p = spawn
    r = max(r, 0.01)
    return use / r + attempt / r * (1 / min(1.0, p * r) - 1)
