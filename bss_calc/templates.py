"""Template hives taken from published guides only.

Blue: the Anthrax blue hive guide (via the BssGuide summary doc) by stage, plus Meta Bee's 2026 blue guide.
Red: Meta Bee's 2026 red guide. Credible red guides only publish an endgame (level 20+) hive and say to stay
blue until about level 19, so there are no earlier red templates.

Where a guide gives only the core counts (e.g. "16 Buoyant / 7 Tadpole / 10 Diamond"), the remaining slots are
filled with the support bees that same guide lists, and the note says so.
"""

ANTHRAX = ("Anthrax blue hive guide (BssGuide summary)", "")
META_BLUE = ("Meta Bee — The Ultimate Blue Hive Guide 2026 (Acid)", "https://meta-bee.com/ultimate-blue-hive-meta/")
META_RED = ("Meta Bee — The Ultimate Red Hive Guide 2026 (Acid)", "https://meta-bee.com/red-hive-guide/")

# Anthrax's mandatory blue beequips. The doc puts a Pinecone on Bubble, but the game only allows Pinecones on
# Bumble, Stubborn, Bucko, Frosty, Carpenter and Bear, so the second one goes on Stubborn (in every Anthrax comp).
ANTHRAX_BEEQUIPS = [("Pinecone", "Stubborn"), ("Pinecone", "Bear"), ("Elf Cap", "Diamond"), ("Elf Cap", "Buoyant"),
                    ("Snow Tiara", "Diamond"), ("Camphor Lip Balm", "Bubble"), ("Candy Ring", "Diamond"),
                    ("Reindeer Antlers", "Puppy")]

TEMPLATES = [
    {
        "name": "Stage 1 — Early blue", "color": "blue", "level": 14, "levels": "Up to level 15 (before 50 bees)",
        "source": ANTHRAX, "gifted": {},
        "bees": [("Bubble", 14), ("Diamond", 5), ("Music", 4), ("Baby", 4), ("Fuzzy", 2), ("Bear", 1), ("Demon", 1),
                 ("Frosty", 1), ("Hasty", 1), ("Vicious", 1), ("Exhausted", 1), ("Stubborn", 1), ("Looker", 1),
                 ("Commander", 1), ("Ninja", 1), ("Cool", 1), ("Basic", 1), ("Tabby", 1), ("Gummy", 1), ("Windy", 1)],
        "beequips": [],
        "notes": "Guide core: 13-14 Bubble and 5 Diamond. Bubbles hold the places of future Tadpoles and Buoyants. "
                 "Demon and Frosty go once Bubbles are replaced with mythics; Vicious is for amulet grinding. Other "
                 "slots use the guide's support bees. Gifting isn't required yet (44 bees).",
    },
    {
        "name": "Stage 2 — Transition blue", "color": "blue", "level": 16, "levels": "Levels 15-17",
        "source": ANTHRAX, "gifted": {"Tadpole": 6},
        "bees": [("Buoyant", 14), ("Tadpole", 10), ("Diamond", 5), ("Music", 4), ("Baby", 3), ("Bear", 1), ("Fuzzy", 1),
                 ("Exhausted", 1), ("Stubborn", 1), ("Looker", 1), ("Commander", 1), ("Ninja", 1), ("Bubble", 1),
                 ("Cool", 1), ("Basic", 1), ("Gummy", 1), ("Vicious", 1), ("Windy", 1), ("Tabby", 1)],
        "beequips": [],
        "notes": "Guide core (most progressed): 14 Buoyant / 10 Tadpole / 5 Diamond. Babies stay until Tadpoles are "
                 "gifted (remove 1 Baby per 1.5 gifted Tadpoles). Vicious goes at 500+ Polar Power. 6 Tadpoles gifted.",
    },
    {
        "name": "Stage 3 — Semi-Diamond", "color": "blue", "level": 18, "levels": "Levels 18-20 (under 80x blessing)",
        "source": ANTHRAX, "gifted": "all",
        "bees": [("Buoyant", 17), ("Tadpole", 9), ("Diamond", 6), ("Music", 4), ("Bear", 1), ("Puppy", 1),
                 ("Exhausted", 1), ("Stubborn", 1), ("Looker", 1), ("Commander", 1), ("Ninja", 1), ("Bubble", 1),
                 ("Cool", 1), ("Basic", 1), ("Tabby", 1), ("Gummy", 1), ("Windy", 1), ("Fuzzy", 1)],
        "beequips": ANTHRAX_BEEQUIPS,
        "notes": "Guide core: 17 Buoyant / 9 Tadpole / 6 Diamond. Run this until level 20 if you can't hold 80x "
                 "Balloon Blessing. Assumes at least 1 Tad alt. Fully gifted.",
    },
    {
        "name": "Stage 3 — Full Diamond", "color": "blue", "level": 18, "levels": "Levels 18-20 (80x blessing)",
        "source": ANTHRAX, "gifted": "all",
        "bees": [("Buoyant", 17), ("Tadpole", 8), ("Diamond", 9), ("Music", 4), ("Bear", 1), ("Puppy", 1),
                 ("Exhausted", 1), ("Stubborn", 1), ("Looker", 1), ("Commander", 1), ("Ninja", 1), ("Bubble", 1),
                 ("Cool", 1), ("Basic", 1), ("Tabby", 1), ("Windy", 1)],
        "beequips": ANTHRAX_BEEQUIPS,
        "notes": "Guide core: 16-17 Buoyant / 8 Tadpole / 8-9 Diamond. Needs 80x Balloon Blessing and a Tad alt "
                 "(Fuzzy dropped because the alt pollinates; Gummy dropped with 7-12 Diamonds). Fully gifted.",
    },
    {
        "name": "Stage 4 — Endgame blue", "color": "blue", "level": 20, "levels": "Level 20+",
        "source": ANTHRAX, "gifted": "all",
        "bees": [("Buoyant", 16), ("Tadpole", 7), ("Diamond", 11), ("Music", 4), ("Bear", 1), ("Puppy", 1),
                 ("Exhausted", 1), ("Stubborn", 1), ("Looker", 1), ("Commander", 1), ("Ninja", 1), ("Bubble", 1),
                 ("Cool", 1), ("Basic", 1), ("Tabby", 1), ("Windy", 1)],
        "beequips": ANTHRAX_BEEQUIPS,
        "notes": "Guide core: 16 Buoyant / 7 Tadpole / 10 Diamond (outside Beesmas). The last open slot goes to "
                 "another Diamond, following the guide's \"fill extra slots with Diamonds\" rule. Assumes 2 Tad alts, "
                 "1-3 guiding alts and 100x Balloon Blessing. Fully gifted and mutated.",
    },
    {
        "name": "Stage 4 — Beesmas glitter", "color": "blue", "level": 20, "levels": "Level 20+ (Beesmas)",
        "source": ANTHRAX, "gifted": "all",
        "bees": [("Buoyant", 16), ("Tadpole", 7), ("Diamond", 13), ("Music", 4), ("Gummy", 1), ("Bear", 1), ("Puppy", 1),
                 ("Exhausted", 1), ("Stubborn", 1), ("Looker", 1), ("Commander", 1), ("Ninja", 1), ("Bubble", 1),
                 ("Cool", 1)],
        "beequips": ANTHRAX_BEEQUIPS,
        "notes": "Guide core: 16 Buoyant / 6-7 Tadpole / 12-13 Diamond, for macroing with lots of glitter. Gummy comes "
                 "back with 13+ Diamonds; Tabby and Basic are removed for the glitter comp.",
    },
    {
        "name": "Meta Bee — Standard blue", "color": "blue", "level": 20, "levels": "Endgame (level 20+)",
        "source": META_BLUE, "gifted": "all",
        "bees": [("Buoyant", 21), ("Tadpole", 9), ("Music", 3), ("Tabby", 1), ("Festive", 1), ("Bear", 1), ("Gummy", 1),
                 ("Puppy", 1), ("Fuzzy", 1), ("Diamond", 1), ("Ninja", 1), ("Shocked", 1), ("Commander", 1),
                 ("Bubble", 1), ("Bucko", 1), ("Stubborn", 1), ("Cool", 1), ("Bumble", 1), ("Looker", 1), ("Basic", 1)],
        "beequips": [("Elf Cap", "Tabby"), ("Elf Cap", "Gummy"), ("Pinecone", "Bear"), ("Pinecone", "Bumble"),
                     ("Kazoo", "Buoyant"), ("Camphor Lip Balm", "Bubble"), ("Whistle", "Commander"),
                     ("Candy Ring", "Diamond"), ("Toy Drum", "Bucko"), ("Reindeer Antlers", "Puppy"),
                     ("Snow Tiara", "Shocked"), ("Festive Wreath", "Festive")],
        "notes": "The guide's exact base hive. Drop Fuzzy with a Tad alt; drop Puppy without antlers. "
                 "Pinecones go on Bear and Frosty, or Bumble if you don't run Frosty.",
    },
    {
        "name": "Meta Bee — Diamond blue", "color": "blue", "level": 20, "levels": "Level 20+ (80x+ blessing, Tad alt)",
        "source": META_BLUE, "gifted": "all",
        "bees": [("Buoyant", 15), ("Diamond", 9), ("Tadpole", 8), ("Music", 3), ("Tabby", 1), ("Festive", 1), ("Bear", 1),
                 ("Gummy", 1), ("Windy", 1), ("Puppy", 1), ("Ninja", 1), ("Shocked", 1), ("Commander", 1), ("Bubble", 1),
                 ("Bucko", 1), ("Cool", 1), ("Bumble", 1), ("Looker", 1), ("Basic", 1)],
        "beequips": [("Elf Cap", "Diamond"), ("Elf Cap", "Diamond"), ("Pinecone", "Bear"), ("Pinecone", "Bumble"),
                     ("Kazoo", "Buoyant"), ("Camphor Lip Balm", "Bubble"), ("Whistle", "Commander"),
                     ("Candy Ring", "Diamond"), ("Toy Drum", "Bucko"), ("Reindeer Antlers", "Puppy"),
                     ("Snow Tiara", "Diamond"), ("Festive Wreath", "Festive")],
        "notes": "The guide's exact Diamond hive. Needs level 20+, fully gifted, at least 1 Tad alt with tad sync "
                 "and 80x+ Balloon Blessing.",
    },
    {
        "name": "Meta Bee — Endgame red", "color": "red", "level": 20, "levels": "Level 20+ (fully gifted, with Digital)",
        "source": META_RED, "gifted": "all",
        "bees": [("Spicy", 12), ("Precise", 10), ("Vector", 10), ("Baby", 4), ("Carpenter", 2), ("Music", 1),
                 ("Riley", 1), ("Rage", 1), ("Shocked", 1), ("Basic", 1), ("Stubborn", 1), ("Rad", 1), ("Crimson", 1),
                 ("Photon", 1), ("Bear", 1), ("Digital", 1), ("Tabby", 1)],
        "beequips": [("Camphor Lip Balm", "Stubborn"), ("Paper Angel", "Photon"), ("Sweatband", "Digital"),
                     ("Kazoo", "Shocked"), ("Toy Drum", "Riley"), ("Whistle", "Rage"), ("Pink Shades", "Rad")],
        "notes": "The guide's hive picture: 11 Spicy, 10 Precise and 10 Vector, plus one open slot for Spicy, Vector, "
                 "Precise, Shy (Paper Angel) or Fire (Token Link) — filled with a 12th Spicy here. The guide says it "
                 "won't work below level 20, fully gifted, with Digital Bee (500 red and white drives). Needs a Fuzzy "
                 "alt or helper.",
    },
]

RED_EARLY_NOTE = ("Credible red guides only publish an endgame hive. Meta Bee's red guide says it \"will NOT work out "
                  "if you aren't level 20+ and fully gifted\", and its author recommends staying blue until about "
                  "level 19, so use a blue template below that.")


def build_setup(t, new_setup, new_bee, beequip_rows, beequip_allowed, base=None):
    """A new setup from a template, keeping the player's gear, amulets, badges and settings if given."""
    s = new_setup(t["name"])
    if base:
        s["gear"] = dict(base.get("gear", {}))
        s["amulets"] = {k: dict(v) for k, v in base.get("amulets", {}).items()}
        s["badges"] = dict(base.get("badges", {}))
        s["settings"] = dict(base["settings"])
        s["tool"] = base.get("tool", s["tool"])
    s["field"] = "Pepper Patch" if t["color"] == "red" else "Pine Tree Forest"
    gifted, gifted_left = t["gifted"], dict(t["gifted"]) if isinstance(t["gifted"], dict) else {}
    slot = 0
    for bee, n in t["bees"]:
        for _ in range(n):
            g = gifted == "all" or gifted_left.get(bee, 0) > 0
            if g and bee in gifted_left:
                gifted_left[bee] -= 1
            b = new_bee(bee, t["level"], g)
            b["slot"] = slot
            slot += 1
            s["bees"].append(b)
    for item, bee_type in t["beequips"]:
        for b in s["bees"]:
            if b["type"] == bee_type and not b.get("beequip") and beequip_allowed(item, bee_type, b["level"], b["gifted"])[0]:
                b["beequip"] = item
                b["beequip_stats"] = beequip_rows(item)
                break
    return s
