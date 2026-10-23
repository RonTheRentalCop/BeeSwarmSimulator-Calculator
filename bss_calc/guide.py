"""Blue hive guide content, summarised from Anthrax's blue hive guide (via the user's BssGuide doc).

Each section is a list of rows: (title, text, [(bee, count), ...] or [item names], image category)."""

SOURCE = "Based on Anthrax's blue hive guide (video and Google Doc), summarised."

SECTIONS = [
    ("Baseline blue hive", [
        ("Core ratio", "16 Buoyant : 7 Tadpole + 4 Music. The other bees are flexible.",
         [("Buoyant", 16), ("Tadpole", 7), ("Music", 4)], "face"),
        ("Fill bees you can remove", "Bubble, Cool, Basic and Tabby. Drop them during severe overfill for more Diamond "
         "Bees, after raising capacity first.", [("Bubble", 1), ("Cool", 1), ("Basic", 1), ("Tabby", 1)], "face"),
        ("Buoyant", "Can go as low as 14 during severe underfill in early blue. 16 is the goal.", [("Buoyant", 1)], "face"),
        ("Gummy", "Can be removed if you run more than 6 but fewer than 13 Diamond Bees.", [("Gummy", 1)], "face"),
        ("Focus producers", "Drop them for another Diamond if focus uptime is perfect: Commander first, then Looker or one "
         "Music. Keep Looker for focus and its +25% Critical Power hive bonus.",
         [("Commander", 1), ("Looker", 1), ("Music", 1)], "face"),
    ]),
    ("Important bees & extra slots", [
        ("Bear Bee", "Mandatory. Gives 1.5-2x honey through Bear Morph.", [("Bear", 1)], "face"),
        ("Diamond Bee", "Very important. Shimmering Honey gives +50% honey at hive (+5% per level) when gifted. Push as "
         "many Diamonds as you can; extra slots should almost always be Diamonds.", [("Diamond", 1)], "face"),
        ("Puppy Bee", "+20% bond from treats, x1.1 capacity and focus through Reindeer Antlers. Without antlers, only run "
         "it past level 16.", [("Puppy", 1)], "face"),
        ("Exhausted Bee", "Best Token Link source. +20% white field capacity. Better than Shocked.", [("Exhausted", 1)], "face"),
        ("Stubborn Bee", "Strongest token uptime boost: +15% ability token lifespan. Can sometimes swap for Hasty "
         "(+15% player movespeed); test both.", [("Stubborn", 1), ("Hasty", 1)], "face"),
        ("Digital Bee", "Worth running with 500 blue and red drives for extra token uptime through Corruption.",
         [("Digital", 1)], "face"),
        ("Tadpoles", "12 if underfilling. Past 12, another Diamond is better than a 13th Tadpole.", [("Tadpole", 1)], "face"),
        ("Buoyants", "Up to 18 during overfill (usually Honey Day). Past 16, a Diamond is almost always better.",
         [("Buoyant", 1)], "face"),
        ("Vicious Bee", "-15% monster respawn time, Polar Bear quests and amulet grinding.", [("Vicious", 1)], "face"),
        ("Windy Bee", "Tornado fruit collection, more pops, cloud buffs and guiding alts. Skip it with Tide Popper and "
         "Hydro planters, a fully gifted hive, tiles, no guiding alts, or a macro server that bans it.",
         [("Windy", 1)], "face"),
        ("Fuzzy Bees", "1-2 if you have no alts. About 8 across 6 players for full pollination; each macro player needs "
         "at least 1. Remove them as your alts develop.", [("Fuzzy", 2)], "face"),
        ("Baby Bees", "4 until 6 Tadpoles are gifted, then remove 1 Baby per 1.5 gifted Tadpoles. Baby Love from Baby and "
         "gifted Tadpoles is x2 pollen for 30 s.", [("Baby", 4)], "face"),
    ]),
    ("Stage 1 — Early blue", [
        ("Hive", "13-14 Bubble Bees and 5 Diamond Bees. Bubbles hold places for Tadpoles and Buoyants and build Bubble "
         "Bloat on their own.", [("Bubble", 14), ("Diamond", 5)], "face"),
        ("Notes", "Demon or Frosty can go once Bubbles are replaced with mythics. Gift Bubble and Diamond eventually. "
         "Vicious is for amulet grinding.", [], ""),
        ("Progression", "Get a Supreme Star Amulet with Pop Star (stats don't matter yet) → replace Bubbles with mythics "
         "(12 Tadpoles, as many Buoyants as possible) → 2/5 Pop Star with blue pollen and convert rate → 48B honey → "
         "level the hive to 15.", [], ""),
    ]),
    ("Stage 2 — Transition blue", [
        ("Earliest", "10 Buoyant / 12 Tadpole / 2 Diamond", [("Buoyant", 10), ("Tadpole", 12), ("Diamond", 2)], "face"),
        ("Middle", "13-15 Buoyant / 10-12 Tadpole / 3 Diamond", [("Buoyant", 14), ("Tadpole", 11), ("Diamond", 3)], "face"),
        ("Most progressed", "14 Buoyant / 10 Tadpole / 5 Diamond", [("Buoyant", 14), ("Tadpole", 10), ("Diamond", 5)], "face"),
        ("Purpose", "Bridges early blue to level 18+ honey-making blue. Maximise hourly honey to speed up gifting, "
         "levelling and Supreme Star Amulet rolling.", [], ""),
        ("Notes", "Remove Vicious at 500+ Polar Power (add it back for gold+ Cog grinding). Baby is needed until Tadpoles "
         "are gifted. Mutate Diamonds with +15% or more convert amount using bitterberries.", [], ""),
        ("Progression", "50 bees (don't go past hive level 15 before this) → 4/5 Pop Star with blue pollen, convert rate "
         "and two of ability rate / crit chance / pollen → level 16 → gift 6 Tadpoles (replace Babies) → level 17 and gift "
         "all Buoyants → level 18 and get a 3/5 double-passive amulet with blue pollen and convert rate.", [], ""),
    ]),
    ("Stage 3 — Honey-making blue", [
        ("Full Diamond", "16-17 Buoyant / 8 Tadpole / 8-9 Diamond", [("Buoyant", 17), ("Tadpole", 8), ("Diamond", 9)], "face"),
        ("Semi-Diamond", "17 Buoyant / 9 Tadpole / 6 Diamond", [("Buoyant", 17), ("Tadpole", 9), ("Diamond", 6)], "face"),
        ("Assumes a Tad alt", "From here on, comps assume at least 1 Tad alt. Full Diamond is much worse without Tad sync "
         "or 250 pops per star.", [("Tadpole", 1)], "face"),
        ("Balloon Blessing", "At level 18 and fully gifted, keep about 80x Balloon Blessing. If you can't, run Semi-Diamond "
         "until level 20 (limit 6 Diamonds without 80x blessing).", [], ""),
        ("Progression", "Finish gifting → mutate Music, Bear, Bubble and Diamonds → Diamonds +15% convert amount with "
         "bitterberries, then +25% with bitter jelly → improve the double-passive amulet.", [], ""),
    ]),
    ("Stage 4 — Endgame blue", [
        ("Outside Beesmas", "16 Buoyant / 7 Tadpole / 10 Diamond", [("Buoyant", 16), ("Tadpole", 7), ("Diamond", 10)], "face"),
        ("During Beesmas", "16 Buoyant / 6-7 Tadpole / 12-13 Diamond (if you have lots of glitter to macro with)",
         [("Buoyant", 16), ("Tadpole", 7), ("Diamond", 13)], "face"),
        ("Assumes", "2 Tad alts, 1-3 guiding alts, high-stat amulets and beequips, and many fully mutated bees.", [], ""),
        ("Progression", "Stay blue → mutate every bee (high convert amount on Diamonds) → keep 100x Balloon Blessing → "
         "Glitch Drives on Digital → 200+ stickers on the stack → finalise alts, amulets, beequips and tools.", [], ""),
    ]),
    ("Beequips", [
        ("Pinecone ×2 (mandatory)", "On Bubble and Bear. 15-19% capacity, 8-11% Pine Tree pollen, 1-2% bee ability rate. "
         "The most important blue beequip.", ["Pinecone"], "beequip"),
        ("Elf Cap ×2 (mandatory)", "On a new Diamond and a Buoyant. Must have Honey at Hive.", ["Elf Cap"], "beequip"),
        ("Snow Tiara (mandatory)", "On a Diamond. Blue and white field capacity, 25-30% convert rate.", ["Snow Tiara"], "beequip"),
        ("Camphor Lip Balm (mandatory)", "On Bubble. 13-20% bubble pollen. The most impactful field beequip.",
         ["Camphor Lip Balm"], "beequip"),
        ("Candy Ring (mandatory)", "On a Diamond. 5-10% honey at hive and 40-50% convert rate. Largest Honey at Hive source.",
         ["Candy Ring"], "beequip"),
        ("Reindeer Antlers (mandatory)", "On Puppy. Capacity through Reindeer Fetch and a focus source.",
         ["Reindeer Antlers"], "beequip"),
        ("Recommended", "Rose Headband (Diamond, 60-80% convert rate), Autumn Sunhat (Diamond), Toy Drum (Bucko, haste), "
         "Bead Lizard (Basic or Cool, Token Link).", ["Rose Headband", "Autumn Sunhat", "Toy Drum", "Bead Lizard"], "beequip"),
        ("Optional", "Paperclip, Whistle, Beesmas Tree Hat, Beret, Festive Wreath, Pink Shades.",
         ["Paperclip", "Whistle", "Beesmas Tree Hat", "Beret", "Festive Wreath", "Pink Shades"], "beequip"),
    ]),
    ("Amulets", [
        ("Star Amulet", "5/5 stats: blue pollen, convert rate, bee ability rate, critical chance, pollen. Passives: Pop Star "
         "with Guiding Star or Star Shower (+1.25x capacity).", ["Supreme Star Amulet"], "amulet"),
        ("Cog Amulet", "Blue pollen, bubble pollen, ability token lifespan, instant blue conversion, bee attack.",
         ["Supreme Cog Amulet"], "amulet"),
        ("King Beetle Amulet", "Convert rate, attack, and Bamboo pollen (any field pollen except Blue Flower).",
         ["King Beetle Amulet"], "amulet"),
        ("Shell Amulet", "Goo, Stump Field pollen, convert amount, any other field pollen.", ["Supreme Shell Amulet"], "amulet"),
        ("Ant Amulet", "Blue pollen, critical power, critical chance, player movespeed, white pollen.",
         ["Supreme Ant Amulet"], "amulet"),
        ("Stick Bug Amulet", "Capacity, convert rate, blue pollen, monster respawn time, blue bee attack, blue bomb pollen.",
         ["Diamond Stick Bug Amulet"], "amulet"),
        ("Moon Amulet", "Capacity, honey per pollen, bond from treats.", ["Moon Amulet"], "amulet"),
    ]),
    ("Mutations", [
        ("General", "Roll Rare, Epic and Legendary bees with Royal Jelly, not bitterberries. Save bitterberries for "
         "Event and Mythic bees.", [], ""),
        ("Bee Movespeed", "Tadpole, Music, Bubble and other rare/epic/legendary bees.",
         [("Tadpole", 1), ("Music", 1), ("Bubble", 1)], "face"),
        ("Bee Ability Rate", "Buoyant, Bear, Tabby, Festive, Gummy, Digital.",
         [("Buoyant", 1), ("Bear", 1), ("Tabby", 1), ("Festive", 1), ("Gummy", 1), ("Digital", 1)], "face"),
        ("Convert Amount", "Diamond Bees only.", [("Diamond", 1)], "face"),
        ("Gather Amount", "Digital only, once it has 100+ Glitch Drives.", [("Digital", 1)], "face"),
        ("Diamond mutation methods", "Levels 13-17: bitterberries. Levels 18-20: Royal Jelly + Blueberries (about 5T per "
         "Diamond for +25%). Level 20+: Royal Jelly only (about 100T per Diamond) or Royal Jelly + Blueberries.", [], ""),
    ]),
    ("Levels & gifting", [
        ("Per level", "+10% convert amount, +5% gather amount, +5% max energy, +3% bee movespeed, plus bee-specific buffs.",
         [], ""),
        ("Level order", "Diamond → Digital → Bear → Music/Bubble → Tadpole/Buoyant → Focus/Haste producers → the rest.",
         [("Diamond", 1), ("Digital", 1), ("Bear", 1), ("Music", 1), ("Tadpole", 1), ("Buoyant", 1)], "face"),
        ("Gifting", "x1.5 convert, x1.5 gather, x1.5 attack, plus a unique gifted hive bonus (doesn't stack).", [], ""),
        ("Mythic gifting order", "1 Buoyant → 1 Fuzzy → 1 Tadpole → 6 Tadpoles → 8 Tadpoles → 10 Buoyants → "
         "14 Buoyants → the remaining Tadpoles and Buoyants.", [("Buoyant", 1), ("Fuzzy", 1), ("Tadpole", 1)], "face"),
    ]),
]
