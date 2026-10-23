"""Saves setups with Flet's SharedPreferences: browser storage on the website, app storage on desktop."""

import json
from pathlib import Path

from .engine import DEFAULT_SETTINGS, new_setup

KEY = "bss_honey_calc.setups"
LEGACY_FILE = Path.home() / ".bss-honey-calc" / "setups.json"   # where the desktop app used to save


def _normalise(setups):
    for s in setups:
        s["settings"] = {**DEFAULT_SETTINGS, **s.get("settings", {})}
        s.setdefault("gear", {}), s.setdefault("amulets", {}), s.setdefault("buffs", []), s.setdefault("bees", [])
        s.setdefault("alts", []), s.setdefault("badges", {}), s.setdefault("overrides", {})
    return setups or [new_setup()]


async def load(prefs):
    raw = None
    try:
        raw = await prefs.get(KEY)
    except Exception:
        pass
    if not raw:
        try:
            raw = LEGACY_FILE.read_text()
        except OSError:
            raw = None
    try:
        return _normalise(json.loads(raw)) if raw else [new_setup()]
    except ValueError:
        return [new_setup()]


async def save(prefs, setups):
    await prefs.set(KEY, json.dumps(setups))
