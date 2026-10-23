"""Stat catalogue: every stat key the calculator understands, how it is entered, and how
beequip/amulet data from the game files maps onto it."""

from .data import GAME

COLORS = ("white", "red", "blue")

# kind: "pct"  -> additive part is entered as a percent (25 means +25%), stat starts at 100%
#       "pct0" -> same, but the stat starts at 0% (instant conversion, crit chance...)
#       "flat" -> plain number (capacity, convert amount, gather amount)
STAT_DEFS = {
    # --- player / hive stats (System Page) ---
    "pollen": ("Pollen", "pct"),
    "white_pollen": ("White Pollen", "pct"),
    "red_pollen": ("Red Pollen", "pct"),
    "blue_pollen": ("Blue Pollen", "pct"),
    "bee_gather_pollen": ("Bee Gather Pollen", "pct"),
    "tool_pollen": ("Tool Pollen", "pct"),
    "bubble_pollen": ("Bubble Pollen", "pct"),
    "bomb_pollen": ("Bomb Pollen", "pct"),
    "buzz_bomb_pollen": ("Buzz Bomb Pollen", "pct"),
    "red_bomb_pollen": ("Red Bomb Pollen", "pct"),
    "blue_bomb_pollen": ("Blue Bomb Pollen", "pct"),
    "bomb_power": ("Bomb Power", "pct"),
    "instant_bomb_conversion": ("Instant Bomb Conversion", "pct0"),
    "bee_ability_pollen": ("Bee Ability Pollen", "pct"),
    "honey_from_tokens": ("Honey From Tokens", "pct"),
    "mark_duration": ("Mark Duration", "pct"),
    "gifted_bee_pollen": ("Gifted Bee Pollen", "pct"),
    "capacity_flat": ("Capacity (flat)", "flat"),
    "capacity": ("Capacity Multiplier", "pct"),
    "white_field_capacity": ("White Field Capacity", "pct"),
    "red_field_capacity": ("Red Field Capacity", "pct"),
    "blue_field_capacity": ("Blue Field Capacity", "pct"),
    "convert_rate": ("Convert Rate", "pct"),
    "convert_rate_at_hive": ("Convert Rate At Hive", "pct"),
    "convert_amount": ("Convert Amount (all bees)", "flat"),
    "honey_per_pollen": ("Honey Per Pollen", "pct"),
    "honey_at_hive": ("Honey At Hive", "pct"),
    "instant_conversion": ("Instant Conversion", "pct0"),
    "instant_white_conversion": ("Instant White Conversion", "pct0"),
    "instant_red_conversion": ("Instant Red Conversion", "pct0"),
    "instant_blue_conversion": ("Instant Blue Conversion", "pct0"),
    "crit_chance": ("Critical Chance", "pct0"),
    "crit_power": ("Critical Power", "pct0"),
    "super_crit_chance": ("Super-Crit Chance", "pct0"),
    "super_crit_power": ("Super-Crit Power", "pct0"),
    "bee_movespeed": ("Bee Movespeed", "pct"),
    "bee_energy": ("Bee Energy", "pct"),
    "bee_ability_rate": ("Bee Ability Rate", "pct"),
    "player_movespeed_flat": ("Player Movespeed (flat)", "flat"),
    "movement_collection": ("Movement Collection", "flat"),
    # --- stats on a single bee (beequip "bee stats", mutations) ---
    "bee:gather": ("Bee: Gather Amount", "flat"),
    "bee:convert": ("Bee: Convert Amount", "flat"),
    "bee:energy": ("Bee: Energy", "flat"),
    "bee:speed": ("Bee: Movespeed", "flat"),
    "bee:gather_white": ("Bee: White Gather", "pct"),
    "bee:gather_red": ("Bee: Red Gather", "pct"),
    "bee:gather_blue": ("Bee: Blue Gather", "pct"),
    "bee:crit_chance": ("Bee: Critical Chance", "pct0"),
    "bee:crit_power": ("Bee: Critical Power", "pct0"),
    "bee:super_crit_chance": ("Bee: Super-Crit Chance", "pct0"),
    "bee:super_crit_power": ("Bee: Super-Crit Power", "pct0"),
    "bee:instant_conversion": ("Bee: Instant Conversion", "pct0"),
    "bee:convert_at_hive": ("Bee: Convert At Hive", "pct"),
    "bee:pollination_chance": ("Bee: Pollination Chance", "pct0"),
    "bee:bubble_chance": ("Bee: Gathering Bubble Chance", "pct0"),
    "bee:bubble_pollen": ("Bee: Bubble Pollen", "pct"),
    "bee:ability_rate": ("Bee: Ability Rate", "pct"),
    "bee:ability_pollen": ("Bee: Ability Pollen", "pct"),
    "bee:bomb_pollen": ("Bee: Bomb Pollen", "pct"),
}
for _field in GAME["fields"]:
    STAT_DEFS[f"field_pollen:{_field}"] = (f"{_field} Pollen", "pct")

HIVE_KEYS = [k for k in STAT_DEFS if not k.startswith("bee:")]
BEE_KEYS = [k for k in STAT_DEFS if k.startswith("bee:")]


def label(key):
    return STAT_DEFS.get(key, (key, "flat"))[0]


def kind(key):
    return STAT_DEFS.get(key, (key, "flat"))[1]


def to_display(key, op, value):
    """Internal value -> the number a player types / sees in game."""
    if op == "add" and kind(key) != "flat":
        return round(value * 100, 4)
    return value


def from_display(key, op, number):
    if op == "add" and kind(key) != "flat":
        return number / 100
    return number


def describe(key, op, value):
    if op == "mul":
        return f"x{value:g} {label(key)}"
    if kind(key) == "flat":
        return f"+{value:,.6g} {label(key)}"
    return f"+{value * 100:.4g}% {label(key)}"


# ---------- mapping from the game's own stat names ----------
_BEEQUIP_BEE_STATS = {
    "GatherAdd": ("bee:gather", "add"), "GatherMul": ("bee:gather", "mul"),
    "ConvertAdd": ("bee:convert", "add"), "ConvertMul": ("bee:convert", "mul"),
    "EnergyAdd": ("bee:energy", "add"), "EnergyMul": ("bee:energy", "mul"),
    "MovespeedAdd": ("bee:speed", "add"), "MovespeedMul": ("bee:speed", "mul"),
    "GatherWhiteMul": ("bee:gather_white", "mul"), "GatherRedMul": ("bee:gather_red", "mul"),
    "GatherBlueMul": ("bee:gather_blue", "mul"),
    "CriticalChance": ("bee:crit_chance", "add"), "CriticalPower": ("bee:crit_power", "add"),
    "SuperCritChance": ("bee:super_crit_chance", "add"), "SuperCritPower": ("bee:super_crit_power", "add"),
    "InstantConversion": ("bee:instant_conversion", "add"), "ConvertAtHiveMul": ("bee:convert_at_hive", "mul"),
    "GatherPollinationChance": ("bee:pollination_chance", "add"),
    "BubbleChance": ("bee:bubble_chance", "add"), "BubblePollen": ("bee:bubble_pollen", "mul"),
    "AbilityRate": ("bee:ability_rate", "mul"), "AbilityPollen": ("bee:ability_pollen", "mul"),
    "BombPollen": ("bee:bomb_pollen", "mul"), "BuzzBombPollen": ("bee:bomb_pollen", "mul"),
    "RedBombPollen": ("bee:bomb_pollen", "mul"), "BlueBombPollen": ("bee:bomb_pollen", "mul"),
}
_HIVE_TYPES = {
    "BaseProductionRate": "convert_rate", "ContainerSpaceMultiplier": "capacity", "ContainerSpace": "capacity_flat",
    "CriticalPower": "crit_power", "CriticalChance": "crit_chance", "SuperCritChance": "super_crit_chance",
    "SuperCritPower": "super_crit_power", "ConversionAtHive": "convert_rate_at_hive", "HoneyAtHive": "honey_at_hive",
    "MaxBeeEnergy": "bee_energy", "BeeMovespeedMultiplier": "bee_movespeed", "PollenValue": "honey_per_pollen",
    "CollectorPollenMultiplier": "tool_pollen", "BaseConversionRate": "convert_amount",
    "PlayerMovespeed": "player_movespeed_flat", "MovementCollection": "movement_collection",
    "BeeAbilityRate": "bee_ability_rate", "HoneyFromTokens": "honey_from_tokens",
    "MarkDurationMultiplier": "mark_duration", "BombPollen": "bomb_pollen",
}


def hive_key(type_, params):
    params = params or {}
    if type_ == "PollenBonus":
        if "Color" in params:
            return f"{params['Color'].lower()}_pollen"
        if "Zone" in params:
            return f"field_pollen:{params['Zone']}"
        if params.get("Tag") == "Bee Gather":
            return "bee_gather_pollen"
        tag_keys = {"Bubble": "bubble_pollen", "Bomb": "bomb_pollen", "Buzz Bomb": "buzz_bomb_pollen",
                    "Red Bomb": "red_bomb_pollen", "Blue Bomb": "blue_bomb_pollen", "Bee Ability": "bee_ability_pollen"}
        if params.get("Tag") in tag_keys:
            return tag_keys[params["Tag"]]
        return None if params else "pollen"
    if type_ == "PollenConversion":
        if "Color" in params:
            return f"instant_{params['Color'].lower()}_conversion"
        return None if params else "instant_conversion"
    if type_ in ("ContainerSpace", "ContainerSpaceMultiplier") and "Color" in params:
        return f"{params['Color'].lower()}_field_capacity"
    if params:  # zone- or tag-limited versions of generic stats aren't modelled
        return None
    return _HIVE_TYPES.get(type_)


def _mid(value):
    if isinstance(value, dict):
        value = value.get("Value")
    if isinstance(value, list):
        return (value[0] + value[-1]) / 2
    return value


def beequip_rows(name):
    """Starting stat rows for a beequip: guaranteed base stats at the middle of their roll range.
    Optional stats and wax upgrades are left out - the player edits rows to match their item."""
    bq = GAME["beequips"].get(name)
    if not bq:
        return []
    rows = []
    for m in bq.get("Modifiers", []):
        if m.get("Chance", 1) != 1 or m["Stat"] not in _BEEQUIP_BEE_STATS:
            continue
        key, op = _BEEQUIP_BEE_STATS[m["Stat"]]
        rows.append([key, op, round(_mid(m["Value"]), 4)])
    for h in bq.get("HiveBonuses", []):
        key = hive_key(h["Type"], h.get("Params"))
        if key is None or not isinstance(h.get("Chance", 1), (int, float)) or h.get("Chance", 1) != 1:
            continue
        rows.append([key, "mul" if h.get("Op") == "Mul" else "add", round(_mid(h["Value"]), 4)])
    return rows


def beequip_possible(name):
    """Every stat a beequip can show (base or via wax), for the help text in the editor."""
    bq = GAME["beequips"].get(name) or {}
    seen = []
    for m in bq.get("Modifiers", []):
        if m["Stat"] in _BEEQUIP_BEE_STATS:
            seen.append(label(_BEEQUIP_BEE_STATS[m["Stat"]][0]))
    for u in bq.get("Upgrades", []):
        if u.get("BeeStat") in _BEEQUIP_BEE_STATS:
            seen.append(label(_BEEQUIP_BEE_STATS[u["BeeStat"]][0]))
        elif u.get("HiveBonusStat"):
            k = hive_key(u["HiveBonusStat"], u.get("Params"))
            if k:
                seen.append("Hive " + label(k))
    for h in bq.get("HiveBonuses", []):
        k = hive_key(h["Type"], h.get("Params"))
        if k:
            seen.append("Hive " + label(k))
    return sorted(set(seen))


def beequip_allowed(name, bee_type, level, gifted):
    """(ok, reason) for whether a bee can wear a beequip (mutation requirements are not tracked)."""
    bq = GAME["beequips"].get(name)
    if not bq:
        return True, ""
    req = bq.get("Requirements", {})
    bee = GAME["bees"][bee_type]
    if level < req.get("Lvl", 0):
        return False, f"needs level {req['Lvl']}"
    if "Color" in req and req["Color"].lower() != {"white": "colorless"}.get(bee["color"], bee["color"]):
        return False, f"needs a {req['Color']} bee"
    if "Types" in req and bee_type not in req["Types"]:
        return False, "only " + "/".join(req["Types"])
    if "Rarities" in req and bee["rarity"] not in req["Rarities"]:
        return False, "only " + "/".join(req["Rarities"]) + " bees"
    if req.get("Gifted") and not gifted:
        return False, "gifted bees only"
    if "Mutation" in req or "MutationGroup" in req:
        return True, "needs a mutated bee"
    return True, ""


def amulet_rows(name):
    """The amulet's guaranteed stats at mid-roll."""
    am = GAME["amulets"].get(name)
    rows = []
    for m in (am or {}).get("Mods", []):
        if "Pool" in m or "Chance" in m:
            continue
        key = hive_key(m["Type"], m.get("Params"))
        if key:
            rows.append([key, "mul" if m.get("Op") == "Mul" else "add", round(_mid(m["Value"]), 4)])
    return rows


def amulet_pool(name):
    """Optional stats this amulet can roll: list of (key, op, low, high)."""
    am = GAME["amulets"].get(name)
    out = []
    for m in (am or {}).get("Mods", []):
        for p in m.get("Pool", [m] if "Chance" in m else []):
            key = hive_key(p["Type"], p.get("Params"))
            if key:
                v = p["Value"] if isinstance(p["Value"], list) else [p["Value"]]
                out.append((key, "mul" if p.get("Op") == "Mul" else "add", v[0], v[-1]))
    return out


AMULET_GROUPS = {}
for _name, _am in GAME["amulets"].items():
    AMULET_GROUPS.setdefault(_am["Group"], []).append(_name)
