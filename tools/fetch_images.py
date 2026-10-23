"""Downloads bee, gear, beequip, amulet and field images from the Bee Swarm Simulator Fandom wiki into
bss_calc/assets/img and writes bss_calc/image_index.json. Run once: .venv/bin/python tools/fetch_images.py"""

import json
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "bss_calc"
ASSETS = ROOT / "assets"
API = "https://bee-swarm-simulator.fandom.com/api.php"
UA = {"User-Agent": "Mozilla/5.0 (bss-honey-calc image fetch)"}
GAME = json.loads((ROOT / "game_data.json").read_text())

AMULET_FILES = {
    "Bronze Star Amulet": "Bronze_star.png", "Silver Star Amulet": "Silver_Star_Amulet.png",
    "Gold Star Amulet": "Gold_star.png", "Diamond Star Amulet": "Diamond_star.png", "Supreme Star Amulet": "Supremeicon.png",
    "Bronze Ant Amulet": "Bronze_Ant_Amulet.png", "Silver Ant Amulet": "Silver_Ant_Amulet.png",
    "Gold Ant Amulet": "Gold_Ant_Amulet.png", "Diamond Ant Amulet": "Diamond_Ant_Amulet.png",
    "Supreme Ant Amulet": "Supreme_Ant_Amulet.png",
    "Bronze Cog Amulet": "BronzeCogAmulet.png", "Silver Cog Amulet": "SilverCogAmulet.png",
    "Gold Cog Amulet": "GoldCogAmulet.png", "Diamond Cog Amulet": "DiamondCogAmulet.png",
    "Supreme Cog Amulet": "SupremeCogAmulet.png",
    "Bronze Shell Amulet": "BronzeShell.png", "Silver Shell Amulet": "SilverShell.png", "Gold Shell Amulet": "GoldShell.png",
    "Diamond Shell Amulet": "DiamondShell.png", "Supreme Shell Amulet": "SupremeShell.png",
    "Bronze Stick Bug Amulet": "BronzeStick.png", "Silver Stick Bug Amulet": "SilverStick.png",
    "Gold Stick Bug Amulet": "GoldStick.png", "Diamond Stick Bug Amulet": "DiamondStick.png",
    "King Beetle Amulet": "King_Beetle_Amulet.png", "Moon Amulet": "Moon_Amulet.png",
}


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def file_urls(titles):
    """File:title -> original url (None if missing)."""
    out = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        q = urllib.parse.urlencode(dict(action="query", titles="|".join(chunk), prop="imageinfo", iiprop="url",
                                        format="json", formatversion=2, redirects=1))
        d = json.load(urllib.request.urlopen(urllib.request.Request(f"{API}?{q}", headers=UA)))
        back = {}
        for n in d["query"].get("normalized", []) + d["query"].get("redirects", []):
            back[n["to"]] = back.get(n["from"], n["from"])
        for p in d["query"]["pages"]:
            src = back.get(p["title"], p["title"])
            src = back.get(src, src)
            ii = p.get("imageinfo")
            out[src] = ii[0]["url"] if ii else None
    return out


def main():
    wanted = []   # (category, name, [candidate File: titles])
    for bee in GAME["bees"]:
        wanted.append(("face", bee, [f"File:{bee}Icon.png"]))
        wanted.append(("bee", bee, [f"File:{bee} Bee.png"]))
        wanted.append(("gifted", bee, [f"File:Gifted {bee} Bee.png", f"File:Gifted{bee}Bee.png"]))
    for name in GAME["beequips"]:
        wanted.append(("beequip", name, [f"File:{name}.png", f"File:{name.title()}.png"]))
    for name in GAME["tools"]:
        wanted.append(("tool", name, [f"File:{name}.png"]))
    for slot, items in GAME["gear"].items():
        for name in items:
            wanted.append(("gear", name, [f"File:{name}.png", f"File:{name.replace(chr(39), '')}.png"]))
    for name, f in AMULET_FILES.items():
        wanted.append(("amulet", name, [f"File:{f}"]))
    for name in GAME["fields"]:
        wanted.append(("field", name, [f"File:{name}.png", f"File:{name} Icon.png"]))
    wanted.append(("ui", "Honey", ["File:Honey.png"]))
    wanted.append(("ui", "Pollen", ["File:Pollen.png"]))

    urls = file_urls(sorted({t for _, _, cands in wanted for t in cands}))
    manifest, missing = {}, []
    for cat, name, cands in wanted:
        url = next((urls.get(t) for t in cands if urls.get(t)), None)
        if not url:
            missing.append(f"{cat}: {name}")
            continue
        rel = Path("img") / cat / f"{slug(name)}.png"
        dest = ASSETS / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read()
            dest.write_bytes(data)
            # shrink to at most 160 px with macOS sips (keeps transparency)
            subprocess.run(["sips", "-s", "format", "png", "-Z", "160", str(dest), "--out", str(dest)],
                           capture_output=True)
        manifest.setdefault(cat, {})[name] = rel.as_posix()
    (ROOT / "image_index.json").write_text(json.dumps(manifest, indent=1))
    print({k: len(v) for k, v in manifest.items()})
    print("missing:", missing)


if __name__ == "__main__":
    main()
