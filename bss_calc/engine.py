"""Honey-per-hour model for a Bee Swarm Simulator setup.

The model follows the wiki's documented formulas:
  * bee gather   = base gather x flower tier (single 1 .. star 5) x (1 + 0.10 x (lvl-1)) x 1.5 if gifted,
                   +50% on flowers of the bee's colour; a crit doubles it (bee pages' pollen tables)
  * bee convert  = (base convert + Convert Amount) x (1 + 0.10 x (lvl-1)) x Convert Rate x 1.5 if gifted
  * bee energy   = base energy x (1 + 0.05 x (lvl-1));  speed = base speed x (1 + 0.03 x (lvl-1))
  * each stat    = (100% + sum of "+%" bonuses) x product of "x" multipliers
  * capacity     = flat capacity x Capacity Multiplier x field capacity (weighted by the field's flower colours)
  * instant conversion is applied colour first, then regular, then any bee-only instant conversion
  * pollination  = +1 flower tier per hit (star can't go higher); a flower drops 1 tier for every minute it isn't
                   pollinated, down to its natural tier; lower-tier flowers are more likely to be picked.
                   Sources: Fuzzy Coat (up to 5 flowers per gather, 9 gifted), Lei/Poinsettia/Rose Headband,
                   Pollen Haze (30 flowers/s for 30 s, at most once per 3 min per field), Guiding Star
                   (15 + 1 per gifted type every 15 s), Diamond Drain (10 + 3 per blue bee).
  * bubbles      = 4 red / 6 white / 8 blue pollen from 29 flowers (+15% per gifted blue type, +5% per level).
                   You only get pollen from your own bubbles and from frog bubbles - an alt's Gathering Bubbles
                   pay the alt. Flowers are shared, so an alt's pollination lifts your flowers too.

It then plays out the gather -> walk to hive -> convert loop to get honey per hour.
Ability tokens, passives, boosts and mob kills aren't simulated; add them as buffs if you want them counted.
"""

import copy
import functools
import math
import random

from . import abilities
from .data import GAME
from .stats import COLORS, kind

DEFAULT_SETTINGS = {
    "base_crit_chance": 0.05,      # assumption: shown on the System Page with no buffs
    "base_crit_power": 2.0,        # every bee page's pollen table shows a crit doubling the gather
    "base_super_crit_power": 2.0,  # super-crits collect 2x a regular crit (wiki)
    "bee_flight_studs": 10.0,      # average distance a bee flies per gather trip
    "hive_distance_studs": 60.0,   # field -> hive distance (bees resting / you walking to convert)
    "player_speed": 30.0,          # your walking speed in studs/s (base movespeed + boots etc.)
    "tool_uptime": 1.0,            # fraction of field time you are swinging the tool
    "ability_pollen_pct": 0.0,     # extra pollen from ability tokens as a % of bee gathering
    "sleep_time": 30.0,
    "gather_area_flowers": 200.0,  # flowers your bees and tool work in around you
    "fuzzy_coat_fill": 0.5,        # Fuzzy Coat pollinates "up to" 5/9 flowers; share of that max per gather
    "token_pickup_pct": 100.0,     # share of your own ability tokens you collect
    "bubble_pop_pct": 50.0,        # share of bubbles in your area that you pop
    "fuzz_bomb_pollination": 0.0,  # flowers each fuzz bomb pollinates (wiki: "may pollinate", no number given)
    "fuzz_bomb_catch_pct": 50.0,   # share of fuzz bombs you run into
    "mark_stand_pct": 60.0,        # share of time you stand inside your Pollen Marks
    "triangle_flowers": 30.0,      # flowers inside an average Vector Triangulate triangle
    "targets_hit": 2.0,            # Precise Bee Target Practice targets you activate (0-3)
    "tabby_love_stacks": 0.0,      # your Tabby Love stacks (0-1000)
    "guiding_star_uptime_pct": 0.0,  # % of time Guiding Star (Star Amulet passive) is active
    "diamond_drain_per_min": 0.0,  # Diamond Drain activations per minute (Diamond Mask)
}

TIER_DECAY_SECONDS = 60


@functools.lru_cache(maxsize=256)
def pollinated_tiers(sizes, area, rate, seconds=480, warmup=240):
    """Steady-state flower tiers in your gathering area under a pollination rate (flowers/s).

    sizes: natural share of single..star flowers. Returns (mean tier, share of each tier 1..5)."""
    sizes = list(sizes)
    n = max(20, min(int(area), 250))
    natural = []
    for tier, share in enumerate(sizes, start=1):
        natural += [tier] * round(share * n)
    natural = (natural + [natural[-1]] * n)[:n]
    if rate <= 0:
        return sum(natural) / n, tuple(natural.count(t) / n for t in range(1, 6))
    rng = random.Random(7)
    rate_here = rate * n / area   # same pollinations per flower as the real area
    tiers, idle = list(natural), [0] * n
    owed, samples, counts = 0.0, 0, [0] * 5
    for second in range(seconds):
        owed += rate_here
        hits = int(owed)
        owed -= hits
        if hits:
            weights = [6 - t if t < 5 else 0 for t in tiers]
            if any(weights):
                for i in rng.choices(range(n), weights=weights, k=hits):
                    if tiers[i] < 5:
                        tiers[i] += 1
                    idle[i] = 0
        for i in range(n):
            idle[i] += 1
            if idle[i] >= TIER_DECAY_SECONDS:
                idle[i] = 0
                if tiers[i] > natural[i]:
                    tiers[i] -= 1
        if second >= warmup:
            samples += 1
            for t in tiers:
                counts[t - 1] += 1
    total = samples * n
    dist = tuple(c / total for c in counts)
    return sum((t + 1) * d for t, d in enumerate(dist)), dist

GEAR_SLOTS = ("bag", "hat", "left_guard", "right_guard", "belt", "boots")


def new_setup(name="My Setup"):
    return {
        "name": name,
        "field": "Pine Tree Forest",
        "tool": "Scooper",
        "gear": {"bag": "Pouch"},
        "bees": [],
        "amulets": {},
        "buffs": [],
        "alts": [],
        "settings": dict(DEFAULT_SETTINGS),
    }


def new_bee(bee_type="Basic", level=1, gifted=False):
    return {"type": bee_type, "level": level, "gifted": gifted, "beequip": None, "beequip_stats": [], "mods": []}


class StatBag:
    """Collects (+) and (x) contributions per stat and resolves them like the game does."""

    def __init__(self, bases=None):
        self.adds, self.muls, self.bases = {}, {}, dict(bases or {})
        self.sources = {}

    def apply(self, key, op, value, source=""):
        if op == "mul":
            self.muls[key] = self.muls.get(key, 1.0) * value
        else:
            self.adds[key] = self.adds.get(key, 0.0) + value
        self.sources.setdefault(key, []).append((source, op, value))

    def get(self, key):
        base = self.bases.get(key)
        if base is None:
            base = 1.0 if kind(key) == "pct" else 0.0
            if key.startswith("field_pollen:"):
                base = 1.0
        return (base + self.adds.get(key, 0.0)) * self.muls.get(key, 1.0)


def _hive_stats(setup):
    s = setup["settings"]
    hive = StatBag({
        "crit_chance": s["base_crit_chance"],
        "crit_power": s["base_crit_power"],
        "super_crit_power": s["base_super_crit_power"],
        "capacity_flat": 0.0,
    })
    for slot in GEAR_SLOTS:
        name = setup["gear"].get(slot)
        if name:
            for key, op, v in GAME["gear"][slot][name]["stats"]:
                hive.apply(key, op, v, name)
    gifted_types = sorted({b["type"] for b in setup["bees"] if b["gifted"]})
    for t in gifted_types:
        for key, op, v in GAME["bees"][t]["gifted_effects"]:
            hive.apply(key, op, v, f"Gifted {t} Bee")
    for group, am in setup["amulets"].items():
        if am and am.get("name"):
            for key, op, v in am.get("stats", []):
                hive.apply(key, op, v, am["name"])
    for b in setup["bees"]:
        for key, op, v in b.get("beequip_stats", []):
            if not key.startswith("bee:"):
                hive.apply(key, op, v, f"{b.get('beequip')} ({b['type']})")
    for row in setup["buffs"]:
        key, op, v = row[:3]
        hive.apply(key, op, v, row[3] if len(row) > 3 and row[3] else "Buff")
    return hive


def _crit_factor(cc, cp, scc, scp):
    cc, scc = min(max(cc, 0), 1), min(max(scc, 0), 1)
    normal = 1 - cc
    crit = cc * (1 - scc) * cp
    sup = cc * scc * cp * scp
    total = normal + crit + sup
    return total, (sup / total if total else 0.0)


# Ability tokens that matter for pollination / bubbles: (use cooldown, attempt cooldown, success rate) from the wiki
TOKENS = {
    "Pollen Haze": (75, 15, 1 / 6),     # gifted Fuzzy Bee, avg 1 per 150 s
    "Fuzz Bombs": (20, 10, 1 / 3),      # Fuzzy Bee, avg 1 per 40 s
    "Summon Frog": (50, 10, 0.25),      # Tadpole Bee, avg 1 per 80 s
}
HAZE_SECONDS, HAZE_LOCKOUT, HAZE_FLOWERS_PER_SEC = 30, 180, 30
FROG_BUBBLES = 3                        # frogs make a bubble on their 2nd, 3rd and 4th hop
GATHER_BUBBLE_CHANCE = {"Tadpole": (0.65, 0.85), "Bubble": (0.25, 0.50)}   # (normal, gifted)
BUBBLE_BASE = {"red": 4, "white": 6, "blue": 8}   # pollen per flower from a bubble, 29 flowers
BUBBLE_FLOWERS = 29


def token_interval(name, ability_rate=1.0):
    """Average seconds between spawns of a token for one bee that's gathering (wiki's formula, Bee Ability Rate
    divides both cooldowns and multiplies the success rate)."""
    use, attempt, p = TOKENS[name]
    r = max(ability_rate, 0.01)
    return use / r + attempt / r * (1 / min(1.0, p * r) - 1)


def new_alt(name="Alt 1"):
    return {"name": name, "tool": "Porcelain Dipper", "bag": "Port-O-Hive", "bees": [],
            "overlap_pct": 100.0, "token_pickup_pct": 80.0, "ability_rate_pct": 0.0}


def _alt_setup(alt, main):
    """A standalone setup for an alt account gathering in the main's field."""
    s = new_setup(alt["name"])
    s["field"], s["tool"], s["gear"] = main["field"], alt.get("tool", "Scooper"), {"bag": alt.get("bag", "Pouch")}
    s["settings"] = {**main["settings"], "token_pickup_pct": alt.get("token_pickup_pct", 80.0)}
    for group in alt.get("bees", []):
        for _ in range(int(group.get("count", 1))):
            s["bees"].append(new_bee(group["type"], int(group.get("level", 1)), bool(group.get("gifted"))))
    s["bees"] = s["bees"][:50]
    if alt.get("ability_rate_pct"):
        s["buffs"].append(["bee_ability_rate", "add", alt["ability_rate_pct"] / 100, "Alt ability rate"])
    return s


def _bee_rates(setup, hive, s):
    """Per-bee gather/convert rates plus everything the bees put into the shared field."""
    rows = []
    hive_convert = 0.0
    local_poll = {}          # flowers/s pollinated right around this account
    haze_tokens = 0.0        # Pollen Haze tokens collected per second
    frogs = []               # (frogs per second, tadpole level)
    own_bubbles = []         # (bubbles per second, bee level, per-bee bubble pollen mult)
    pickup = s["token_pickup_pct"] / 100
    ability_rate = hive.get("bee_ability_rate")
    for b in setup["bees"]:
        base = GAME["bees"][b["type"]]
        bs = StatBag()
        for key, op, v in b.get("beequip_stats", []) + b.get("mods", []):
            if key.startswith("bee:"):
                bs.apply(key, op, v)
        lvl = max(1, min(int(b["level"]), 25))
        gift = 1.5 if b["gifted"] else 1.0

        gather = (base["gather"] + bs.adds.get("bee:gather", 0)) * (1 + 0.10 * (lvl - 1)) * gift * bs.muls.get("bee:gather", 1)
        convert = ((base["convert"] + bs.adds.get("bee:convert", 0) + hive.get("convert_amount"))
                   * (1 + 0.10 * (lvl - 1)) * gift * bs.muls.get("bee:convert", 1)
                   * hive.get("convert_rate") * hive.get("convert_rate_at_hive") * bs.get("bee:convert_at_hive"))
        speed = ((base["speed"] + bs.adds.get("bee:speed", 0)) * (1 + 0.03 * (lvl - 1))
                 * bs.muls.get("bee:speed", 1) * hive.get("bee_movespeed"))
        if base["energy"] is None:
            energy = math.inf
        else:
            energy = ((base["energy"] + bs.adds.get("bee:energy", 0)) * (1 + 0.05 * (lvl - 1))
                      * bs.muls.get("bee:energy", 1) * hive.get("bee_energy"))

        cycle = base["gather_time"] + s["bee_flight_studs"] / max(speed, 0.1)
        if math.isinf(energy):
            uptime = 1.0
        else:
            sleep = base.get("sleep_time", s["sleep_time"])
            # bees fly home at 0.5x speed and back out at 1.5x speed
            rest = sleep + s["hive_distance_studs"] / (0.5 * speed) + s["hive_distance_studs"] / (1.5 * speed)
            awake = energy * cycle
            uptime = awake / (awake + rest)
        gathers_per_sec = uptime / cycle

        if b["type"] == "Fuzzy":
            coat = (9 if b["gifted"] else 5) * s["fuzzy_coat_fill"]
            local_poll["Fuzzy Coat"] = local_poll.get("Fuzzy Coat", 0) + coat * gathers_per_sec
            bombs = 2 + lvl // 5
            fb = uptime / token_interval("Fuzz Bombs", ability_rate) * pickup * bombs * s["fuzz_bomb_pollination"]
            if fb:
                local_poll["Fuzz Bombs"] = local_poll.get("Fuzz Bombs", 0) + fb
            if b["gifted"]:
                haze_tokens += uptime / token_interval("Pollen Haze", ability_rate) * pickup
        if b["type"] == "Tadpole":
            frogs.append((uptime / token_interval("Summon Frog", ability_rate) * pickup, lvl))
        chance = min(bs.get("bee:pollination_chance"), 1.0)
        if chance > 0:
            src = f"{b.get('beequip') or 'Beequip'} pollination"
            local_poll[src] = local_poll.get(src, 0) + chance * gathers_per_sec
        bubble_chance = GATHER_BUBBLE_CHANCE.get(b["type"], (0, 0))[b["gifted"]] + bs.get("bee:bubble_chance")
        if bubble_chance > 0:
            own_bubbles.append((min(bubble_chance, 1.0) * gathers_per_sec, lvl, bs.get("bee:bubble_pollen")))

        convert_per_sec = convert / (base["convert_time"] + s["bee_flight_studs"] / max(speed, 0.1))
        hive_convert += convert_per_sec
        rows.append({
            "type": b["type"], "level": lvl, "gifted": b["gifted"], "beequip": b.get("beequip") or "",
            "gather": gather, "speed": speed, "energy": energy, "uptime": uptime,
            "pollen_per_sec": 0.0, "convert_per_sec": convert_per_sec,
            "_bs": bs, "_base": base, "_gps": gathers_per_sec,
        })
    gifted_blue = len({b["type"] for b in setup["bees"] if b["gifted"] and GAME["bees"][b["type"]]["color"] == "blue"})
    return rows, hive_convert, {"local_poll": local_poll, "haze_tokens": haze_tokens, "frogs": frogs,
                                "own_bubbles": own_bubbles, "gifted_blue_types": gifted_blue}


def _bubble_pollen(level, gifted_blue_types, frac, tier, pollen, color_pollen, bubble_stat, bee_mult=1.0):
    """Pollen by colour from one popped bubble: 4 red / 6 white / 8 blue from 29 flowers,
    +15% per gifted blue bee type and +5% per bee level (of the bubble's owner)."""
    scale = (1 + 0.15 * gifted_blue_types + 0.05 * level) * tier * pollen * bubble_stat * bee_mult
    return {c: BUBBLE_FLOWERS * frac[c] * BUBBLE_BASE[c] * color_pollen[c] * scale for c in COLORS}


def compute(setup, include_alts=True):
    s = {**DEFAULT_SETTINGS, **setup.get("settings", {})}
    setup = {**setup, "settings": s}
    field = GAME["fields"][setup["field"]]
    frac = {c: field[c] for c in COLORS}
    hive = _hive_stats(setup)

    pollen = hive.get("pollen") * hive.get(f"field_pollen:{setup['field']}")
    color_pollen = {c: hive.get(f"{c}_pollen") for c in COLORS}
    bee_gather_pollen = hive.get("bee_gather_pollen")
    gifted_pollen = hive.get("gifted_bee_pollen")
    hpp = hive.get("honey_per_pollen")
    area = min(s["gather_area_flowers"], field["flowers"])
    field_share = area / field["flowers"]          # field-wide pollinators only hit your area this often

    bee_rows, hive_convert, mine = _bee_rates(setup, hive, s)

    # ---------------- alt accounts in the same field ----------------
    alts = []
    for alt in (setup.get("alts", []) if include_alts else []):
        if not alt.get("bees"):
            continue
        alt_setup = _alt_setup(alt, setup)
        alt_hive = _hive_stats(alt_setup)
        _, _, out = _bee_rates(alt_setup, alt_hive, alt_setup["settings"])
        alts.append({"name": alt["name"], "overlap": alt.get("overlap_pct", 100) / 100, "out": out,
                     "honey_per_hour": compute(alt_setup, include_alts=False)["honey_per_hour"]})

    # ---------------- pollination & flower tiers ----------------
    pollination = dict(mine["local_poll"])
    for a in alts:
        for src, rate in a["out"]["local_poll"].items():
            key = f"{a['name']}: {src}"
            pollination[key] = pollination.get(key, 0) + rate * a["overlap"]
    # Pollen Haze is field-wide and can't start again within 3 minutes of the last one, whoever summoned it
    haze_sources = {"Your Pollen Haze": mine["haze_tokens"]}
    haze_sources.update({f"{a['name']}: Pollen Haze": a["out"]["haze_tokens"] for a in alts})
    haze_rate = sum(haze_sources.values())
    haze_uptime = HAZE_SECONDS / (HAZE_LOCKOUT + 1 / haze_rate) if haze_rate > 0 else 0.0
    for src, rate in haze_sources.items():
        if rate > 0:
            pollination[src] = HAZE_FLOWERS_PER_SEC * haze_uptime * field_share * rate / haze_rate
    gifted_types = len({b["type"] for b in setup["bees"] if b["gifted"]})
    if s["guiding_star_uptime_pct"] > 0:
        pollination["Guiding Star"] = (15 + gifted_types) / 15 * s["guiding_star_uptime_pct"] / 100 * field_share
    if setup["gear"].get("hat") == "Diamond Mask" and s["diamond_drain_per_min"] > 0:
        blue_bees = sum(GAME["bees"][b["type"]]["color"] == "blue" for b in setup["bees"])
        drained = min(10 + 3 * blue_bees, field["flowers"] * field["blue"])
        pollination["Diamond Drain"] = drained * s["diamond_drain_per_min"] / 60 * field_share
    poll_rate = sum(pollination.values())
    natural_tier = field["avg_size"]
    tier, tier_dist = pollinated_tiers(tuple(field["sizes"]), area, round(poll_rate, 3))

    # ---------------- ability tokens & buffs ----------------
    tokens = abilities.token_rates(setup["bees"], bee_rows, hive.get("bee_ability_rate"), s["token_pickup_pct"] / 100)
    buff = abilities.buffs(tokens, hive, s)
    pollen *= buff["pollen"]
    color_pollen = {c: color_pollen[c] * buff["boost"][c] for c in COLORS}
    bee_gather_pollen *= buff["bee_gather"]

    # ---------------- bees: pollen (pass 2) ----------------
    bee_pollen = {c: 0.0 for c in COLORS}          # gross pollen/s by flower colour
    bee_instant = {c: 0.0 for c in COLORS}         # pollen/s converted by super-crits / bee-only instant conversion
    for row in bee_rows:
        bs, base = row.pop("_bs"), row.pop("_base")
        gps = row.pop("_gps")
        cf, sup_share = _crit_factor(hive.get("crit_chance") + bs.get("bee:crit_chance") + buff["crit_chance"],
                                     hive.get("crit_power") + bs.get("bee:crit_power") + buff["crit_power"],
                                     hive.get("super_crit_chance") + bs.get("bee:super_crit_chance"),
                                     hive.get("super_crit_power") + bs.get("bee:super_crit_power"))
        mult = (pollen * bee_gather_pollen * (gifted_pollen if row["gifted"] else 1.0) * cf * tier
                * (1 + s["ability_pollen_pct"] / 100))
        bee_inst = bs.get("bee:instant_conversion")
        for c in COLORS:
            match = 1.5 if base["color"] == c and c != "white" else 1.0
            p = frac[c] * row["gather"] * match * bs.get(f"bee:gather_{c}") * color_pollen[c] * mult * gps
            bee_pollen[c] += p
            bee_instant[c] += p * (1 - (1 - sup_share) * (1 - bee_inst))
            row["pollen_per_sec"] += p

    # ---------------- ability token pollen & honey ----------------
    crit_avg, _ = _crit_factor(hive.get("crit_chance") + buff["crit_chance"], hive.get("crit_power") + buff["crit_power"],
                               hive.get("super_crit_chance"), hive.get("super_crit_power"))

    def fire_bee_rate(level):
        fire = GAME["bees"]["Fire"]
        speed = fire["speed"] * (1 + 0.03 * (level - 1)) * hive.get("bee_movespeed")
        per_gather = fire["gather"] * (1 + 0.10 * (level - 1)) * tier * pollen * bee_gather_pollen * crit_avg
        gps = 1 / (fire["gather_time"] + s["bee_flight_studs"] / speed)
        return {c: frac[c] * per_gather * (1.5 if c == "red" else 1.0) * color_pollen[c] * gps for c in COLORS}

    ctx = {"frac": frac, "tier": tier, "pollen": pollen, "color_pollen": color_pollen, "hive": hive, "settings": s,
           "crit_factor": crit_avg, "crit_power": hive.get("crit_power") + buff["crit_power"],
           "sync": buff["bomb_sync"], "bomb_power": buff["bomb_power"], "active_marks": buff["active_marks"],
           "fire_bee_rate": fire_bee_rate}
    token_pollen, token_instant, token_honey, token_detail = abilities.token_yield(tokens, ctx)

    # ---------------- bubbles ----------------
    # Your own bubbles (Gathering Bubbles, your frogs) pay you. An alt's own bubbles pay the alt even if you pop
    # them, but bubbles from an alt's frogs pay both players (wiki: Bubble, Frog).
    pop = s["bubble_pop_pct"] / 100
    bubble_stat = hive.get("bubble_pollen")
    bubble_pollen = {c: 0.0 for c in COLORS}
    bubble_sources = {}

    def add_bubbles(label_, per_sec, level, owner_gifted_blue, bee_mult=1.0):
        got = _bubble_pollen(level, owner_gifted_blue, frac, tier, pollen, color_pollen, bubble_stat, bee_mult)
        for c in COLORS:
            bubble_pollen[c] += got[c] * per_sec * pop
        bubble_sources[label_] = bubble_sources.get(label_, 0) + sum(got.values()) * per_sec * pop

    for per_sec, lvl, mult_ in mine["own_bubbles"]:
        add_bubbles("Your Gathering Bubbles", per_sec, lvl, mine["gifted_blue_types"], mult_)
    for frogs_per_sec, lvl in mine["frogs"]:
        add_bubbles("Your frogs", frogs_per_sec * FROG_BUBBLES, lvl, mine["gifted_blue_types"])
    for a in alts:
        for frogs_per_sec, lvl in a["out"]["frogs"]:
            add_bubbles(f"{a['name']}: frogs", frogs_per_sec * FROG_BUBBLES * a["overlap"], lvl,
                        a["out"]["gifted_blue_types"])

    # ---------------- tool ----------------
    tool = GAME["tools"][setup["tool"]]
    tool_pollen = {c: 0.0 for c in COLORS}
    # dig-all tools empty the flower: 30 pollen on a single flower, +15 per tier (Pollen page)
    flower_take = (30 + 15 * (tier - 1)) if tool["dig_all"] else tool["base"] * tier
    for c in COLORS:
        tool_pollen[c] = (frac[c] * flower_take * tool["flowers"] * tool["mult"][c] * pollen * color_pollen[c]
                          * hive.get("tool_pollen") / tool["swing_time"] * s["tool_uptime"])

    # ---------------- instant conversion & bag ----------------
    ic = min(hive.get("instant_conversion"), 1.0)
    bag_rate = 0.0
    instant_pollen = 0.0
    for c in COLORS:
        keep = (1 - min(hive.get(f"instant_{c}_conversion"), 1.0)) * (1 - ic)
        kept = ((bee_pollen[c] - bee_instant[c]) + tool_pollen[c] + bubble_pollen[c]
                + (token_pollen[c] - token_instant[c])) * keep
        bag_rate += kept
        instant_pollen += bee_pollen[c] + tool_pollen[c] + bubble_pollen[c] + token_pollen[c] - kept
    gross = (sum(bee_pollen.values()) + sum(tool_pollen.values()) + sum(bubble_pollen.values())
             + sum(token_pollen.values()))

    field_cap = 1 + sum(frac[c] * (hive.get(f"{c}_field_capacity") - 1) for c in COLORS)
    capacity = hive.get("capacity_flat") * hive.get("capacity") * field_cap

    walk = 2 * s["hive_distance_studs"] / max(s["player_speed"] * buff["haste"], 1)
    honey_at_hive = hive.get("honey_at_hive")
    if bag_rate <= 0 or capacity <= 0:
        fill_time, convert_time = math.inf, 0.0
        honey_per_hour = instant_pollen * hpp * 3600
        cycle_time = math.inf
    else:
        fill_time = capacity / bag_rate
        convert_time = capacity / hive_convert if hive_convert > 0 else math.inf
        cycle_time = fill_time + walk + convert_time
        honey_cycle = capacity * hpp * honey_at_hive + instant_pollen * hpp * fill_time
        honey_per_hour = honey_cycle / cycle_time * 3600 if math.isfinite(cycle_time) else 0.0
    # honey tokens only spawn while your bees are out gathering
    time_in_field = fill_time / cycle_time if cycle_time and math.isfinite(cycle_time) else 1.0
    honey_per_hour += token_honey * time_in_field * 3600

    stat_keys = ["pollen", "white_pollen", "red_pollen", "blue_pollen", "bee_gather_pollen", "tool_pollen",
                 "bubble_pollen", "capacity_flat", "capacity", "convert_rate", "convert_rate_at_hive", "convert_amount",
                 "honey_per_pollen", "instant_conversion", "instant_white_conversion", "instant_red_conversion",
                 "instant_blue_conversion", "crit_chance", "crit_power", "super_crit_chance", "bee_movespeed",
                 "bee_energy", "bee_ability_rate", f"field_pollen:{setup['field']}"]
    return {
        "honey_per_hour": honey_per_hour,
        "honey_per_day": honey_per_hour * 24,
        "gross_pollen_per_sec": gross,
        "bee_pollen_per_sec": sum(bee_pollen.values()),
        "tool_pollen_per_sec": sum(tool_pollen.values()),
        "bubble_pollen_per_sec": sum(bubble_pollen.values()),
        "ability_pollen_per_sec": sum(token_pollen.values()),
        "token_honey_per_hour": token_honey * time_in_field * 3600,
        "tokens": token_detail,
        "buffs": buff,
        "bubble_sources": bubble_sources,
        "pollen_by_color": {c: bee_pollen[c] + tool_pollen[c] + bubble_pollen[c] + token_pollen[c] for c in COLORS},
        "instant_share": instant_pollen / gross if gross else 0.0,
        "bag_fill_per_sec": bag_rate,
        "capacity": capacity,
        "fill_time": fill_time,
        "walk_time": walk,
        "convert_time": convert_time,
        "cycle_time": cycle_time,
        "hive_convert_per_sec": hive_convert,
        "field_time_share": fill_time / cycle_time if cycle_time and math.isfinite(cycle_time) else 1.0,
        "bees": bee_rows,
        "natural_tier": natural_tier,
        "flower_tier": tier,
        "tier_dist": tier_dist,
        "pollination": pollination,
        "pollination_per_sec": poll_rate,
        "haze_uptime": haze_uptime,
        "gather_area": area,
        "alts": [{"name": a["name"], "honey_per_hour": a["honey_per_hour"]} for a in alts],
        "stats": {k: hive.get(k) for k in stat_keys},
        "sources": hive.sources,
    }


def alt_impact(setup):
    """What each alt adds to the main account: main honey/hr with vs. without it."""
    full = compute(setup)["honey_per_hour"]
    solo = compute(setup, include_alts=False)["honey_per_hour"]
    each = []
    for i, alt in enumerate(setup.get("alts", [])):
        if not alt.get("bees"):
            continue
        trial = {**setup, "alts": [a for j, a in enumerate(setup["alts"]) if j != i]}
        each.append((alt["name"], full - compute(trial)["honey_per_hour"]))
    return solo, full, each

SENSITIVITY_TESTS = [
    ("+10% Pollen", [["pollen", "add", 0.10]]),
    ("+10% Bee Gather Pollen", [["bee_gather_pollen", "add", 0.10]]),
    ("+10% Red Pollen", [["red_pollen", "add", 0.10]]),
    ("+10% Blue Pollen", [["blue_pollen", "add", 0.10]]),
    ("+10% White Pollen", [["white_pollen", "add", 0.10]]),
    ("+10% Tool Pollen", [["tool_pollen", "add", 0.10]]),
    ("+10% Capacity Multiplier", [["capacity", "add", 0.10]]),
    ("+100,000 Capacity", [["capacity_flat", "add", 100000]]),
    ("+10% Convert Rate", [["convert_rate", "add", 0.10]]),
    ("+5% Instant Conversion", [["instant_conversion", "add", 0.05]]),
    ("+5% Critical Chance", [["crit_chance", "add", 0.05]]),
    ("+25% Critical Power", [["crit_power", "add", 0.25]]),
    ("+10% Honey Per Pollen", [["honey_per_pollen", "add", 0.10]]),
    ("+5% Bee Movespeed", [["bee_movespeed", "add", 0.05]]),
    ("+10% Bee Ability Rate", [["bee_ability_rate", "add", 0.10]]),
    ("+10% Bomb Pollen", [["bomb_pollen", "add", 0.10]]),
]


def sensitivity(setup):
    """Honey/hr gain from a small bump to each stat, so you can see what to chase next."""
    base = compute(setup)["honey_per_hour"]
    out = []
    for name, rows in SENSITIVITY_TESTS:
        trial = copy.deepcopy(setup)
        trial["buffs"] = trial["buffs"] + [r + ["test"] for r in rows]
        out.append((name, compute(trial)["honey_per_hour"] - base))
    trial = copy.deepcopy(setup)
    for b in trial["bees"]:
        b["level"] = min(25, int(b["level"]) + 1)
    out.append(("+1 level on every bee", compute(trial)["honey_per_hour"] - base))
    out.sort(key=lambda r: -r[1])
    return base, out
