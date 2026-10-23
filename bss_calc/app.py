"""Flet UI for the Bee Swarm Simulator honey calculator."""

import copy
import json
import math
from pathlib import Path

import flet as ft

from . import storage
from .data import GAME
from .abilities import NOT_MODELLED
from .passives import STAR_PASSIVES
from .engine import GEAR_SLOTS, alt_impact, compute, new_alt, new_bee, new_setup, sensitivity, token_interval
from .stats import (STAT_DEFS, AMULET_GROUPS, BEE_KEYS, HIVE_KEYS, amulet_pool, amulet_rows, beequip_allowed, beequip_possible,
                    beequip_rows, describe, from_display, kind, label, to_display)

# black / dark grey / grey / white palette
BG = "#0B0B0C"
PANEL = "#141416"
CARD = "#1B1B1E"
RAISED = "#26262B"
LINE = "#333338"
MUTED = "#9A9AA0"
TEXT = "#F2F2F2"
HONEY = "#DDCB02"          # accent (kept as a name so highlights stay in one place)
GIFTED = "#E8C547"         # the one warm touch: gifted rings and stars, like the game
RARITY_COLORS = {"Common": "#A0703C", "Rare": "#D8D8D8", "Epic": "#D9B53A", "Legendary": "#5AB4E0",
                 "Mythic": "#9B6BD6", "Event": "#4CB86A"}
ASSETS_DIR = Path(__file__).parent / "assets"
try:
    IMAGES = json.loads((Path(__file__).parent / "image_index.json").read_text())
except OSError:
    IMAGES = {}
NONE = "__none__"  # dropdown key for "nothing selected"
GOOD = ft.Colors.GREEN_400
BAD = ft.Colors.RED_400
SLOT_NAMES = {"bag": "Bag", "hat": "Hat / Mask", "left_guard": "Left Guard", "right_guard": "Right Guard",
              "belt": "Belt", "boots": "Boots"}
SETTING_INFO = [
    ("base_crit_chance", "Base Critical Chance", "pct", "Crit chance with no buffs. Check your System Page and adjust."),
    ("base_crit_power", "Base Critical Power", "pct", "A crit doubles a gather (200%), per every bee page's pollen table."),
    ("base_super_crit_power", "Super-Crit Power", "pct", "A super-crit collects 2x a regular crit (200%)."),
    ("bee_flight_studs", "Bee flight per gather (studs)", "flat", "How far a bee flies between you and a flower each trip."),
    ("hive_distance_studs", "Field to hive distance (studs)", "flat", "Used for bees going home to sleep and for you walking to convert."),
    ("player_speed", "Your walk speed (studs/s)", "flat", "Base movespeed plus boots, Haste and so on."),
    ("tool_uptime", "Tool uptime (0 to 1)", "flat", "How much of your field time you spend swinging the tool."),
    ("ability_pollen_pct", "Extra ability pollen %", "flat",
     "Most ability tokens are now simulated. Use this only for things that aren't (passives, Pulse, Tornado...)."),
    ("fuzz_bomb_catch_pct", "Fuzz bombs you catch %", "flat", "Share of Fuzzy Bee fuzz bombs you run into."),
    ("mark_stand_pct", "Time standing in Pollen Marks %", "flat",
     "How much of the time you're inside your active Pollen Marks (x1.5 per linked mark, up to x2.5)."),
    ("triangle_flowers", "Flowers in a Triangulate triangle", "flat", "Average flowers inside Vector Bee's triangle."),
    ("targets_hit", "Target Practice targets hit (0-3)", "flat", "Precise Bee targets you walk over."),
    ("tabby_love_stacks", "Tabby Love stacks", "flat", "Your Tabby Love stacks (0-1000): +1% Tabby Scratch pollen each."),
    ("balloon_blessing", "Balloon Blessing stacks (0-100)", "flat",
     "From your buff bar. Each stack is x1.03 Capacity and x1.015 Honey at Hive (x4 and x2.5 at 100)."),
    ("polar_power", "Polar Power stacks", "flat", "Each stack gives +5% bee energy."),
    ("max_gather_minutes", "Gather time before converting (min)", "flat",
     "You convert when the bag is full or after this long (macros usually use about 14 min)."),
    ("star_catch_pct", "Star Shower stars caught %", "flat", "Shooting stars you catch (each converts 1M + 200% Convert Total)."),
    ("sleep_time", "Bee sleep time (s)", "flat", "Time a bee rests in the hive after running out of energy."),
    ("gather_area_flowers", "Gathering area (flowers)", "flat",
     "Flowers around you that your bees and tool work. Pollination is spread over these."),
    ("fuzzy_coat_fill", "Fuzzy Coat fill (0 to 1)", "flat",
     "Fuzzy Coat pollinates 'up to' 5 flowers per gather (9 gifted). 0.5 means half of that on average."),
    ("token_pickup_pct", "Your token pickup %", "flat",
     "Share of your own ability tokens you collect (Pollen Haze, Summon Frog, Fuzz Bombs)."),
    ("bubble_pop_pct", "Bubbles you pop %", "flat",
     "Share of bubbles in your area that you pop: your own and frog bubbles."),
    ("fuzz_bomb_pollination", "Flowers pollinated per fuzz bomb", "flat",
     "The wiki says fuzz bombs 'may pollinate nearby flowers' but gives no number. 0 leaves them out."),
    ("guiding_star_uptime_pct", "Guiding Star uptime %", "flat",
     "Star Amulet passive: 15 flowers (+1 per gifted bee type) every 15 s while active."),
    ("diamond_drain_per_min", "Diamond Drain activations / min", "flat",
     "Diamond Mask passive: pollinates 10 blue flowers +3 per blue bee each time."),
]


def fmt(n, digits=3):
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "-"
    if isinstance(n, float) and math.isinf(n):
        return "∞"
    a = abs(n)
    for div, suf in ((1e15, "Qd"), (1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= div:
            return f"{n / div:.{digits}g}{suf}"
    return f"{n:.{digits}g}"


def fmt_time(sec):
    if not math.isfinite(sec):
        return "∞"
    if sec >= 3600:
        return f"{sec / 3600:.1f} h"
    if sec >= 60:
        return f"{sec / 60:.1f} min"
    return f"{sec:.0f} s"


def fmt_stat(key, value):
    if kind(key) == "flat":
        return fmt(value, 4)
    return f"{value * 100:.1f}%"


def num(text, default=0.0):
    try:
        return float(str(text).replace(",", "").strip())
    except ValueError:
        return default


def opts(items):
    return [ft.dropdown.Option(key=k, text=t) for k, t in items]


def img(cat, name, size=32, fallback=ft.Icons.HEXAGON_OUTLINED):
    """Wiki image for a bee face / bee / gifted bee / beequip / tool / gear / amulet."""
    path = IMAGES.get(cat, {}).get(name)
    if not path:
        return ft.Icon(fallback, size=size * 0.7, color=MUTED)
    return ft.Image(src=path, width=size, height=size, fit=ft.BoxFit.CONTAIN)


def img_opts(cat, items, size=22):
    """Dropdown options with a picture in front: items are (key, text)."""
    return [ft.dropdown.Option(key=k, text=t, leading_icon=img(cat, k, size) if k in IMAGES.get(cat, {}) else None)
            for k, t in items]


def bee_face(bee_type, size=40, gifted=False, level=None):
    """A bee's hive-slot face, gifted ring and level badge included."""
    face = img("face", bee_type, size)
    layers = [ft.Container(content=face, border_radius=size * 0.18, clip_behavior=ft.ClipBehavior.HARD_EDGE)]
    if gifted:
        layers.append(ft.Container(right=1, top=1, content=ft.Icon(ft.Icons.STAR, color=GIFTED, size=size * 0.32)))
    if level is not None:
        layers.append(ft.Container(left=2, bottom=1, padding=ft.Padding.symmetric(horizontal=3),
                                   bgcolor=ft.Colors.with_opacity(0.75, BG), border_radius=4,
                                   content=ft.Text(str(level), size=max(9, size * 0.2), color=TEXT,
                                                   weight=ft.FontWeight.BOLD)))
    return ft.Container(width=size, height=size, border_radius=size * 0.2,
                        border=ft.Border.all(2, GIFTED) if gifted else None, content=ft.Stack(layers))


def card(title, *controls, expand=False, image=None):
    head = ft.Text(title, weight=ft.FontWeight.BOLD, size=15, color=TEXT)
    if image is not None:
        head = ft.Row([image, head], spacing=10)
    return ft.Container(
        expand=expand, padding=14, border_radius=14, bgcolor=PANEL, border=ft.Border.all(1, LINE),
        content=ft.Column([head, *controls], spacing=8, tight=True),
    )


def stat_box(title, value, sub=None, color=None):
    items = [ft.Text(title, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
             ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=color)]
    if sub:
        items.append(ft.Text(sub, size=11, color=ft.Colors.ON_SURFACE_VARIANT))
    return ft.Container(content=ft.Column(items, spacing=2, tight=True), padding=12, border_radius=10,
                        bgcolor=CARD, border=ft.Border.all(1, LINE), width=190)


class StatRows:
    """Editable list of [stat, op, value(, label)] rows, shared by beequips, amulets, mutations and buffs."""

    def __init__(self, rows, keys, on_change, with_label=False, hint=None):
        self.rows, self.keys, self.on_change, self.with_label = rows, keys, on_change, with_label
        self.col = ft.Column(spacing=6)
        self.hint = hint
        self.view = ft.Column([self.col, ft.TextButton(content="Add stat", icon=ft.Icons.ADD, on_click=self._add)]
                              + ([ft.Text(hint, size=11, color=ft.Colors.ON_SURFACE_VARIANT)] if hint else []), spacing=4)
        self._render()

    def _add(self, e):
        row = [self.keys[0], "add", 0.0] + ([""] if self.with_label else [])
        self.rows.append(row)
        self._render()
        self.view.update()
        self.on_change()

    def _render(self):
        self.col.controls = [self._row(r) for r in self.rows] or [ft.Text("No stats yet.", italic=True, size=12)]

    def _row(self, row):
        unit = ft.Text(self._unit(row), width=24)
        value = ft.TextField(value=f"{to_display(row[0], row[1], row[2]):g}", width=110, dense=True,
                             text_align=ft.TextAlign.RIGHT)

        def set_value(e):
            row[2] = from_display(row[0], row[1], num(e.control.value))
            self.on_change()

        def set_key(e):
            shown = num(value.value)
            row[0] = e.control.value
            row[2] = from_display(row[0], row[1], shown)
            unit.value = self._unit(row)
            unit.update()
            self.on_change()

        def set_op(e):
            shown = num(value.value, 1.0)
            row[1] = e.control.value
            if row[1] == "mul" and shown == 0:
                shown = 1.0
                value.value = "1"
                value.update()
            row[2] = from_display(row[0], row[1], shown)
            unit.value = self._unit(row)
            unit.update()
            self.on_change()

        def remove(e):
            self.rows.remove(row)
            self._render()
            self.view.update()
            self.on_change()

        value.on_change = set_value
        controls = [
            ft.Dropdown(value=row[0], options=opts((k, label(k)) for k in self.keys), width=230, dense=True,
                        menu_height=380, on_select=set_key),
            ft.Dropdown(value=row[1], options=opts([("add", "+"), ("mul", "×")]), width=80, dense=True, on_select=set_op),
            value, unit,
        ]
        if self.with_label:
            while len(row) < 4:
                row.append("")

            def set_label(e):
                row[3] = e.control.value
                self.on_change()

            controls.append(ft.TextField(value=row[3], hint_text="source (e.g. badge)", width=170, dense=True,
                                         on_change=set_label))
        controls.append(ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, tooltip="Remove", on_click=remove))
        return ft.Row(controls, spacing=6, wrap=True)

    @staticmethod
    def _unit(row):
        if row[1] == "mul":
            return "×"
        return "" if kind(row[0]) == "flat" else "%"


class App:
    def __init__(self, page: ft.Page, prefs, setups):
        self.page = page
        self.prefs = prefs
        self.setups = setups
        self.cur = 0
        page.title = "BSS Honey Calculator"
        scheme = ft.ColorScheme(
            primary=TEXT, on_primary=BG, primary_container=RAISED, on_primary_container=TEXT,
            secondary="#BDBDC2", on_secondary=BG, secondary_container=RAISED, on_secondary_container=TEXT,
            tertiary="#BDBDC2", on_tertiary=BG, surface=PANEL, on_surface=TEXT, on_surface_variant=MUTED,
            outline=LINE, outline_variant="#26262A", surface_tint=BG, inverse_surface=TEXT, on_inverse_surface=BG,
            surface_container_lowest=BG, surface_container_low=PANEL, surface_container=CARD,
            surface_container_high=RAISED, surface_container_highest=RAISED, error="#E06C6C", on_error=BG)
        theme = ft.Theme(color_scheme=scheme, scaffold_bgcolor=BG, canvas_color=PANEL, card_bgcolor=CARD,
                         divider_color=LINE, hover_color=ft.Colors.with_opacity(0.06, TEXT),
                         splash_color=ft.Colors.with_opacity(0.08, TEXT))
        page.theme = page.dark_theme = theme
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = BG
        page.padding = 0
        try:
            page.window.width, page.window.height = 1300, 860
        except AttributeError:
            pass

        self.live = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=HONEY)
        self.setup_dd = ft.Dropdown(width=240, dense=True, on_select=self._pick_setup)
        self.body = ft.Container(expand=True, padding=16)
        self.sel = None          # selected hive slot (0-49)
        self.moving = False      # next slot click moves the selected bee there
        self.brush = {"type": "Basic", "level": 15, "gifted": False}
        self.rail = ft.NavigationRail(
            selected_index=0, label_type=ft.NavigationRailLabelType.ALL, on_change=self._nav, bgcolor=PANEL,
            indicator_color=RAISED,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.HIVE_OUTLINED, selected_icon=ft.Icons.HIVE, label="Setup"),
                ft.NavigationRailDestination(icon=ft.Icons.INSIGHTS_OUTLINED, selected_icon=ft.Icons.INSIGHTS, label="Results"),
                ft.NavigationRailDestination(icon=ft.Icons.COMPARE_ARROWS, label="Compare"),
                ft.NavigationRailDestination(icon=ft.Icons.MENU_BOOK_OUTLINED, selected_icon=ft.Icons.MENU_BOOK, label="Guide"),
                ft.NavigationRailDestination(icon=ft.Icons.INFO_OUTLINE, selected_icon=ft.Icons.INFO, label="How it works"),
            ],
        )
        top = ft.Container(
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            bgcolor=PANEL, border=ft.Border.only(bottom=ft.BorderSide(1, LINE)),
            content=ft.Row([
                img("face", "Basic", 30),
                ft.Text("BSS Honey Calculator", size=18, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.Container(width=12),
                self.setup_dd,
                ft.IconButton(icon=ft.Icons.ADD, tooltip="New setup", on_click=self._new_setup),
                ft.IconButton(icon=ft.Icons.COPY, tooltip="Duplicate setup (to try a change)", on_click=self._dup_setup),
                ft.IconButton(icon=ft.Icons.EDIT, tooltip="Rename setup", on_click=self._rename_setup),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, tooltip="Delete setup", on_click=self._delete_setup),
                ft.Container(expand=True),
                img("ui", "Honey", 26),
                ft.Text("Estimated honey/hr", size=13, color=MUTED),
                self.live,
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )
        page.add(ft.Column([top, ft.Row([self.rail, ft.VerticalDivider(width=1, color=LINE), self.body], expand=True)],
                           expand=True, spacing=0))
        self._refresh_setup_dd()
        self._show(0)

    # ------------------------------------------------------------ helpers
    @property
    def s(self):
        return self.setups[self.cur]

    def _persist(self):
        async def write():
            await storage.save(self.prefs, self.setups)
        self.page.run_task(write)

    def changed(self):
        self._persist()
        r = compute(self.s)
        self.live.value = fmt(r["honey_per_hour"])
        self.live.update()

    def _refresh_setup_dd(self):
        self.setup_dd.options = opts((str(i), s["name"]) for i, s in enumerate(self.setups))
        self.setup_dd.value = str(self.cur)
        r = compute(self.s)
        self.live.value = fmt(r["honey_per_hour"])

    def _show(self, idx):
        self.rail.selected_index = idx
        self.body.content = [self.setup_view, self.results_view, self.compare_view, self.guide_view, self.about_view][idx]()
        self.page.update()

    def _nav(self, e):
        self._show(e.control.selected_index)

    def _toast(self, msg):
        self.page.show_dialog(ft.SnackBar(content=ft.Text(msg)))

    def _ask_name(self, title, initial, done):
        field = ft.TextField(value=initial, autofocus=True)

        def ok(e):
            self.page.pop_dialog()
            done(field.value.strip() or initial)

        field.on_submit = ok
        self.page.show_dialog(ft.AlertDialog(title=ft.Text(title), content=field, actions=[
            ft.TextButton(content="Cancel", on_click=lambda e: self.page.pop_dialog()),
            ft.FilledButton(content="OK", on_click=ok)]))

    # ------------------------------------------------------------ setup management
    def _pick_setup(self, e):
        self.cur = int(e.control.value)
        self.sel = None
        self._refresh_setup_dd()
        self._show(self.rail.selected_index)

    def _new_setup(self, e):
        def done(name):
            self.setups.append(new_setup(name))
            self.cur = len(self.setups) - 1
            self._persist()
            self._refresh_setup_dd()
            self._show(0)
        self._ask_name("New setup", f"Setup {len(self.setups) + 1}", done)

    def _dup_setup(self, e):
        def done(name):
            c = copy.deepcopy(self.s)
            c["name"] = name
            self.setups.append(c)
            self.cur = len(self.setups) - 1
            self._persist()
            self._refresh_setup_dd()
            self._show(self.rail.selected_index)
            self._toast("Duplicated. Change something here, then use Compare to see the gain or loss.")
        self._ask_name("Duplicate setup as", self.s["name"] + " (new)", done)

    def _rename_setup(self, e):
        def done(name):
            self.s["name"] = name
            self._persist()
            self._refresh_setup_dd()
            self.page.update()
        self._ask_name("Rename setup", self.s["name"], done)

    def _delete_setup(self, e):
        if len(self.setups) == 1:
            self._toast("You need at least one setup.")
            return

        def really(ev):
            self.page.pop_dialog()
            self.setups.pop(self.cur)
            self.cur = 0
            self._persist()
            self._refresh_setup_dd()
            self._show(self.rail.selected_index)
        self.page.show_dialog(ft.AlertDialog(title=ft.Text(f"Delete “{self.s['name']}”?"), actions=[
            ft.TextButton(content="Cancel", on_click=lambda ev: self.page.pop_dialog()),
            ft.FilledButton(content="Delete", on_click=really)]))

    # ------------------------------------------------------------ SETUP VIEW
    def setup_view(self):
        tabs = [("Hive", self.hive_tab), ("Gear", self.gear_tab), ("Amulets", self.amulet_tab), ("Badges", self.badge_tab),
                ("Buffs & Items", self.buff_tab), ("Alts", self.alt_tab), ("Field & Settings", self.settings_tab),
                ("System Page", self.overrides_tab)]
        return ft.Tabs(
            length=len(tabs), selected_index=0, expand=True,
            content=ft.Column(expand=True, controls=[
                ft.TabBar(tabs=[ft.Tab(label=t) for t, _ in tabs]),
                ft.TabBarView(expand=True, controls=[ft.Container(content=f(), padding=ft.Padding.only(top=10))
                                                     for _, f in tabs]),
            ]),
        )

    # ---- hive
    SLOT = 54          # hive slot size in px
    RARITY_ORDER = ["Common", "Rare", "Epic", "Legendary", "Mythic", "Event"]

    def hive_tab(self):
        self.hive_grid = ft.Column(spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.hive_head = ft.Text(size=13, color=MUTED)
        self.editor = ft.Column(spacing=10)
        self.palette = ft.Column(spacing=8)
        self.palette_filter = "All"
        self._render_hive(update=False)
        hive_panel = ft.Container(
            padding=14, border_radius=14, bgcolor=PANEL, border=ft.Border.all(1, LINE),
            content=ft.Column([
                ft.Row([ft.Text("Your hive", size=16, weight=ft.FontWeight.BOLD), ft.Container(expand=True),
                        self.hive_head]),
                ft.Text("Click any empty slot to place the brush bee there. Click a bee to edit or move it.",
                        size=11, color=MUTED),
                self.hive_grid,
            ], spacing=8, tight=True),
        )
        return ft.Row(expand=True, vertical_alignment=ft.CrossAxisAlignment.START, spacing=14, controls=[
            ft.Column([hive_panel], scroll=ft.ScrollMode.AUTO),
            ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=14, controls=[
                ft.Container(self.editor, padding=14, border_radius=14, bgcolor=PANEL, border=ft.Border.all(1, LINE)),
                ft.Container(self.palette, padding=14, border_radius=14, bgcolor=PANEL, border=ft.Border.all(1, LINE)),
            ]),
        ])

    # Slot 1 is bottom-left, like the game. Every bee keeps its own slot, so gaps are allowed.
    def _slots(self):
        """slot number -> bee, giving any bee without a valid, unique slot the lowest free one."""
        taken, loose = {}, []
        for b in self.s["bees"][:50]:
            sl = b.get("slot")
            if isinstance(sl, int) and 0 <= sl < 50 and sl not in taken:
                taken[sl] = b
            else:
                loose.append(b)
        free = (i for i in range(50) if i not in taken)
        for b in loose:
            b["slot"] = next(free)
            taken[b["slot"]] = b
        del self.s["bees"][50:]
        return taken

    def _free_slot(self, start=0):
        used = self._slots()
        for i in list(range(start, 50)) + list(range(0, start)):
            if i not in used:
                return i
        return None

    def _render_hive(self, update=True):
        bees = self.s["bees"]
        if self.sel is not None and self.sel not in self._slots():
            self.sel, self.moving = None, False
        gifted_types = len({b["type"] for b in bees if b["gifted"]})
        self.hive_head.value = f"{len(bees)}/50 bees · {gifted_types} gifted types"
        rows = []
        for r in range(9, -1, -1):
            rows.append(ft.Row([self._slot(r * 5 + c) for c in range(5)], spacing=5))
        self.hive_grid.controls = rows
        self._render_editor()
        self._render_palette()
        if update:
            self.hive_grid.update()
            self.hive_head.update()
            self.editor.update()
            self.palette.update()

    def _slot(self, i):
        size = self.SLOT
        selected = i == self.sel
        b = self._slots().get(i)
        if b is None:
            hint = f"Move the bee to slot {i + 1}" if self.moving else f"Place {self.brush['type']} Bee in slot {i + 1}"
            return ft.Container(
                width=size, height=size, border_radius=12, bgcolor=CARD,
                border=ft.Border.all(1, TEXT if self.moving else LINE),
                content=ft.Column([ft.Icon(ft.Icons.OPEN_WITH if self.moving else ft.Icons.ADD, color=MUTED, size=16),
                                   ft.Text(str(i + 1), size=9, color=MUTED)], spacing=0, tight=True,
                                  horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment.CENTER, tooltip=hint, ink=True,
                on_click=lambda e: self._slot_click(i),
            )
        bee = GAME["bees"][b["type"]]
        lvl_badge = ft.Container(
            left=3, bottom=3, padding=ft.Padding.symmetric(horizontal=4), border_radius=5,
            bgcolor=ft.Colors.with_opacity(0.8, BG),
            content=ft.Text(str(b["level"]), size=11, weight=ft.FontWeight.BOLD, color=TEXT))
        layers = [ft.Container(content=img("face", b["type"], size - 4), border_radius=10,
                               clip_behavior=ft.ClipBehavior.HARD_EDGE), lvl_badge,
                  ft.Container(left=6, right=6, bottom=0, height=3, border_radius=2,
                               bgcolor=RARITY_COLORS[bee["rarity"]])]
        if b["gifted"]:
            layers.append(ft.Container(right=2, top=2, content=ft.Icon(ft.Icons.STAR, color=GIFTED, size=15)))
        if b.get("beequip"):
            layers.append(ft.Container(right=2, bottom=4, width=20, height=20, border_radius=10,
                                       bgcolor=ft.Colors.with_opacity(0.85, BG),
                                       content=img("beequip", b["beequip"], 16), alignment=ft.Alignment.CENTER))
        border = ft.Border.all(3, TEXT) if selected else ft.Border.all(2, GIFTED) if b["gifted"] else ft.Border.all(1, LINE)

        if self.moving and not selected:
            border = ft.Border.all(2, MUTED)

        return ft.Container(
            width=size, height=size, border_radius=12, bgcolor=CARD, border=border, ink=True,
            on_click=lambda e: self._slot_click(i),
            tooltip=f"#{i + 1} {'Gifted ' if b['gifted'] else ''}{b['type']} Bee · Lvl {b['level']}"
                    + (f" · {b['beequip']}" if b.get("beequip") else ""),
            content=ft.Stack(layers, width=size - 4, height=size - 4),
        )

    def _slot_click(self, i):
        slots = self._slots()
        if self.moving and self.sel is not None:
            # move the selected bee here, swapping with whatever is in the slot
            mover, other = slots[self.sel], slots.get(i)
            if other is not None:
                other["slot"] = self.sel
            mover["slot"] = i
            self.sel, self.moving = i, False
            self._render_hive()
            self.changed()
        elif i in slots:
            self.sel = None if self.sel == i else i
            self._render_hive()
        else:
            self._place(i)

    def _place(self, slot):
        b = new_bee(self.brush["type"], self.brush["level"], self.brush["gifted"])
        b["slot"] = slot
        self.s["bees"].append(b)
        self.sel = slot
        self._render_hive()
        self.changed()

    # ---- slot editor
    def _render_editor(self):
        bees = self.s["bees"]
        if self.sel is None:
            b = self.brush
            self.editor.controls = [
                ft.Row([ft.Text("Brush", size=16, weight=ft.FontWeight.BOLD), ft.Container(expand=True),
                        ft.Text("used when you click an empty slot", size=11, color=MUTED)]),
                ft.Row([
                    ft.Image(src=IMAGES.get("gifted" if b["gifted"] else "bee", {}).get(b["type"], ""), width=120,
                             height=90, fit=ft.BoxFit.CONTAIN),
                    ft.Column([
                        ft.Text(f"{'Gifted ' if b['gifted'] else ''}{b['type']} Bee", size=18, weight=ft.FontWeight.BOLD),
                        self._bee_blurb(b["type"]),
                        ft.Row([
                            ft.TextField(value=str(b["level"]), label="Level", width=80, dense=True,
                                         on_change=lambda e: b.__setitem__("level", int(min(25, max(1, num(e.control.value, 1)))))),
                            ft.Switch(label="Gifted", value=b["gifted"], on_change=self._brush_gifted),
                        ]),
                    ], spacing=6, expand=True),
                ], vertical_alignment=ft.CrossAxisAlignment.START),
                ft.Row([
                    ft.FilledButton(content="Fill empty slots", icon=ft.Icons.FORMAT_COLOR_FILL, on_click=self._fill_hive),
                    ft.OutlinedButton(content="Set every bee to this level", on_click=self._all_levels),
                    ft.TextButton(content="Clear hive", icon=ft.Icons.DELETE_SWEEP, on_click=self._clear_hive),
                ], wrap=True),
            ]
            return
        i, b = self.sel, self._slots()[self.sel]
        ok, why = beequip_allowed(b["beequip"], b["type"], int(b["level"]), b["gifted"]) if b.get("beequip") else (True, "")

        def set_type(e):
            b["type"] = e.control.value
            self._render_hive()
            self.changed()

        def set_level(e):
            b["level"] = int(min(25, max(1, num(e.control.value, 1))))
            self.changed()

        def bump(d):
            def h(e):
                b["level"] = int(min(25, max(1, b["level"] + d)))
                self._render_hive()
                self.changed()
            return h

        def set_gifted(e):
            b["gifted"] = e.control.value
            self._render_hive()
            self.changed()

        def set_bq(e):
            b["beequip"] = None if e.control.value == NONE else e.control.value
            b["beequip_stats"] = beequip_rows(b["beequip"]) if b["beequip"] else []
            self._render_hive()
            self.changed()

        def remove(e):
            bees.remove(b)
            self.sel, self.moving = None, False
            self._render_hive()
            self.changed()

        def dup(e):
            j = self._free_slot(i + 1)
            if j is None:
                self._toast("A hive holds 50 bees at most.")
                return
            c = copy.deepcopy(b)
            c["slot"] = j
            bees.append(c)
            self.sel = j
            self._render_hive()
            self.changed()

        def move(d):
            def h(e):
                j = i + d
                if not 0 <= j < 50 or (d in (-1, 1) and j // 5 != i // 5):
                    return
                other = self._slots().get(j)
                if other is not None:
                    other["slot"] = i
                b["slot"] = j
                self.sel = j
                self._render_hive()
                self.changed()
            return h

        def toggle_move(e):
            self.moving = not self.moving
            self._render_hive()

        def jump(e):
            j = int(num(e.control.value, i + 1)) - 1
            if 0 <= j < 50 and j != i:
                self.moving = True
                self._slot_click(j)

        bq_items = [(NONE, "No beequip")] + [(n, f"{n} (Lvl {d['Requirements'].get('Lvl')})")
                                             for n, d in sorted(GAME["beequips"].items())]
        self.editor.controls = [
            ft.Row([ft.Text(f"Slot {i + 1}", size=16, weight=ft.FontWeight.BOLD), ft.Container(expand=True),
                    ft.TextField(value=str(i + 1), label="Go to slot", width=90, dense=True, on_submit=jump),
                    ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, tooltip="Move left", on_click=move(-1)),
                    ft.IconButton(icon=ft.Icons.KEYBOARD_ARROW_UP, tooltip="Move up", on_click=move(5)),
                    ft.IconButton(icon=ft.Icons.KEYBOARD_ARROW_DOWN, tooltip="Move down", on_click=move(-5)),
                    ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, tooltip="Move right", on_click=move(1)),
                    ft.IconButton(icon=ft.Icons.OPEN_WITH, tooltip="Pick a slot to move this bee to",
                                  selected=self.moving, on_click=toggle_move,
                                  icon_color=GIFTED if self.moving else None),
                    ft.IconButton(icon=ft.Icons.CONTENT_COPY, tooltip="Duplicate", on_click=dup),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, tooltip="Remove", on_click=remove),
                    ft.IconButton(icon=ft.Icons.CLOSE, tooltip="Back to brush",
                                  on_click=lambda e: (setattr(self, "sel", None), setattr(self, "moving", False),
                                                      self._render_hive()))]),
            *([ft.Text("Click any slot to move this bee there. A bee already there swaps places.", size=12,
                       color=GIFTED)] if self.moving else []),
            ft.Row([
                ft.Image(src=IMAGES.get("gifted" if b["gifted"] else "bee", {}).get(b["type"], ""), width=140,
                         height=104, fit=ft.BoxFit.CONTAIN),
                ft.Column([
                    ft.Text(f"{'Gifted ' if b['gifted'] else ''}{b['type']} Bee", size=18, weight=ft.FontWeight.BOLD),
                    self._bee_blurb(b["type"], b["gifted"]),
                ], spacing=4, expand=True),
            ], vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Row([
                ft.Dropdown(value=b["type"], options=img_opts("face", ((n, n) for n in sorted(GAME["bees"]))),
                            width=200, dense=True, menu_height=420, label="Bee", on_select=set_type),
                ft.IconButton(icon=ft.Icons.REMOVE, on_click=bump(-1)),
                ft.TextField(value=str(b["level"]), label="Level", width=70, dense=True, on_change=set_level),
                ft.IconButton(icon=ft.Icons.ADD, on_click=bump(1)),
                ft.Switch(label="Gifted", value=b["gifted"], on_change=set_gifted),
            ], wrap=True),
            ft.Row([
                img("beequip", b["beequip"], 44) if b.get("beequip") else ft.Icon(ft.Icons.CHECKROOM, color=MUTED, size=32),
                ft.Dropdown(value=b.get("beequip") or NONE, options=img_opts("beequip", bq_items), width=260, dense=True,
                            menu_height=420, label="Beequip", on_select=set_bq),
                ft.Text(f"Can't wear: {why}" if not ok else f"Note: {why}" if why else ("OK to wear" if b.get("beequip") else ""),
                        size=12, color="#E06C6C" if not ok else MUTED),
            ], wrap=True),
            ft.OutlinedButton(content=f"Beequip & mutation stats ({len(b.get('beequip_stats', [])) + len(b.get('mods', []))})",
                              icon=ft.Icons.TUNE, on_click=lambda e: self._bee_dialog(b)),
        ]

    def _bee_blurb(self, bee_type, gifted=False):
        d = GAME["bees"][bee_type]
        colour = d["color"].replace("white", "colorless").title()
        energy = "∞" if d["energy"] is None else f"{d['energy']:g}"
        lines = [
            ft.Row([ft.Container(width=10, height=10, border_radius=5, bgcolor=RARITY_COLORS[d["rarity"]]),
                    ft.Text(f"{d['rarity']} · {colour}", size=12, color=MUTED)], spacing=6),
            ft.Text(f"Gathers {d['gather']:g} per {d['gather_time']:g}s · converts {d['convert']:g} per "
                    f"{d['convert_time']:g}s · speed {d['speed']:g} · energy {energy}", size=12, color=MUTED),
            ft.Text(f"Gifted hive bonus: {d['gifted_bonus_text']}", size=12,
                    color=GIFTED if gifted else MUTED),
        ]
        if d["tokens"] and d["tokens"] != "–":
            lines.append(ft.Text(f"Abilities: {d['tokens']}", size=12, color=MUTED))
        return ft.Column(lines, spacing=3)

    def _brush_gifted(self, e):
        self.brush["gifted"] = e.control.value
        self._render_hive()

    def _fill_hive(self, e):
        used = self._slots()
        for i in range(50):
            if i not in used:
                b = new_bee(self.brush["type"], self.brush["level"], self.brush["gifted"])
                b["slot"] = i
                self.s["bees"].append(b)
        self._render_hive()
        self.changed()

    def _all_levels(self, e):
        for b in self.s["bees"]:
            b["level"] = self.brush["level"]
        self._render_hive()
        self.changed()

    def _clear_hive(self, e):
        self.s["bees"].clear()
        self.sel = None
        self._render_hive()
        self.changed()

    # ---- bee palette
    def _render_palette(self):
        def set_filter(name):
            def h(e):
                self.palette_filter = name
                self._render_palette()
                self.palette.update()
            return h

        def pick(name):
            def h(e):
                self.brush["type"] = name
                if self.sel is not None:
                    self._slots()[self.sel]["type"] = name
                    self.changed()
                self._render_hive()
            return h

        chips = [ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=4), border_radius=14, ink=True,
            bgcolor=RAISED if self.palette_filter == r else None, border=ft.Border.all(1, LINE),
            on_click=set_filter(r),
            content=ft.Row([ft.Container(width=8, height=8, border_radius=4, bgcolor=RARITY_COLORS.get(r, TEXT)),
                            ft.Text(r, size=12)], spacing=5, tight=True))
            for r in ["All"] + self.RARITY_ORDER]
        bees = sorted(GAME["bees"].items(), key=lambda kv: (self.RARITY_ORDER.index(kv[1]["rarity"]), kv[0]))
        tiles = []
        for name, d in bees:
            if self.palette_filter not in ("All", d["rarity"]):
                continue
            chosen = self.brush["type"] == name
            tiles.append(ft.Container(
                width=70, padding=4, border_radius=10, ink=True, on_click=pick(name),
                bgcolor=RAISED if chosen else None, border=ft.Border.all(2 if chosen else 1, TEXT if chosen else LINE),
                tooltip=f"{name} Bee ({d['rarity']})",
                content=ft.Column([
                    ft.Container(content=img("face", name, 48), border_radius=8, clip_behavior=ft.ClipBehavior.HARD_EDGE),
                    ft.Container(height=3, width=40, border_radius=2, bgcolor=RARITY_COLORS[d["rarity"]]),
                    ft.Text(name, size=10, text_align=ft.TextAlign.CENTER, no_wrap=True),
                ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True)))
        hint = "Pick a bee to paint with" + (" (also changes the selected slot)" if self.sel is not None else "")
        self.palette.controls = [
            ft.Row([ft.Text("Bees", size=16, weight=ft.FontWeight.BOLD), ft.Container(expand=True),
                    ft.Text(hint, size=11, color=MUTED)]),
            ft.Row(chips, wrap=True, spacing=6),
            ft.Row(tiles, wrap=True, spacing=6, run_spacing=6),
        ]

    def _bee_dialog(self, b):
        bq = b.get("beequip")
        parts = []
        if bq:
            info = GAME["beequips"][bq]
            parts += [
                ft.Text(f"{bq}: {info.get('Description', '')}", italic=True, size=12),
                ft.Text("Set these to the exact numbers shown on your beequip. Wax upgrades just change the numbers. "
                        "The defaults are the guaranteed base stats at mid-roll.", size=12),
                StatRows(b.setdefault("beequip_stats", []), BEE_KEYS + HIVE_KEYS, self.changed,
                         hint="Can appear on this beequip: " + ", ".join(beequip_possible(bq))).view,
                ft.Divider(),
            ]
        parts += [ft.Text("Mutation / other bee-only bonuses", weight=ft.FontWeight.BOLD),
                  StatRows(b.setdefault("mods", []), BEE_KEYS, self.changed,
                           hint="For example, a +% Gather mutation is Bee: Gather Amount × 1.xx").view]

        def close(e):
            self.page.pop_dialog()
            self._render_hive()

        self.page.show_dialog(ft.AlertDialog(
            title=ft.Text(f"{'⭐ Gifted ' if b['gifted'] else ''}{b['type']} Bee · Lvl {b['level']}"),
            content=ft.Container(width=760, height=480, content=ft.ListView(parts, spacing=8)),
            actions=[ft.FilledButton(content="Done", on_click=close)]))

    # ---- gear
    def gear_tab(self):
        def stats_text(slot, name):
            if not name:
                return "-"
            it = GAME["gear"][slot][name]
            lines = [describe(*st) for st in it["stats"]]
            if it["notes"]:
                lines.append("Not modelled: " + ", ".join(it["notes"]))
            return "\n".join(lines) + (f"\nCost: {it['cost']}" if it.get("cost") else "")

        def tool_text(name):
            t = GAME["tools"][name]
            m = t["mult"]
            colours = ", ".join(f"x{v:g} {c}" for c, v in m.items() if v != 1)
            return (f"{t['base']} pollen × {t['flowers']:g} flowers every {t['swing_time']}s"
                    + (f" · {colours}" if colours else "") + (f"\n{t['note']}" if t["note"] else "")
                    + f"\nCost: {t['cost']}")

        tool_info = ft.Text(tool_text(self.s["tool"]), size=12, selectable=True, color=MUTED)
        tool_pic = ft.Container(img("tool", self.s["tool"], 72), width=80, height=80, alignment=ft.Alignment.CENTER)

        def set_tool(e):
            self.s["tool"] = e.control.value
            tool_info.value = tool_text(e.control.value)
            tool_pic.content = img("tool", e.control.value, 72)
            tool_info.update()
            tool_pic.update()
            self.changed()

        cards = [card("Tool", ft.Row([tool_pic, ft.Column([
            ft.Dropdown(value=self.s["tool"], options=img_opts("tool", ((n, n) for n in GAME["tools"])), width=240,
                        dense=True, menu_height=420, on_select=set_tool), tool_info], expand=True, spacing=6)],
            vertical_alignment=ft.CrossAxisAlignment.START))]
        for slot in GEAR_SLOTS:
            info = ft.Text(stats_text(slot, self.s["gear"].get(slot)), size=12, selectable=True, color=MUTED)
            current = self.s["gear"].get(slot)
            pic = ft.Container(img("gear", current, 72) if current else ft.Icon(ft.Icons.BLOCK, color=LINE, size=40),
                               width=80, height=80, alignment=ft.Alignment.CENTER)

            def set_item(e, slot=slot, info=info, pic=pic):
                if e.control.value != NONE:
                    self.s["gear"][slot] = e.control.value
                else:
                    self.s["gear"].pop(slot, None)
                name = self.s["gear"].get(slot)
                info.value = stats_text(slot, name)
                pic.content = img("gear", name, 72) if name else ft.Icon(ft.Icons.BLOCK, color=LINE, size=40)
                info.update()
                pic.update()
                self.changed()

            choices = ([] if slot == "bag" else [(NONE, "None")]) + [(n, n) for n in GAME["gear"][slot]]
            cards.append(card(SLOT_NAMES[slot], ft.Row([pic, ft.Column([
                ft.Dropdown(value=current or (NONE if slot != "bag" else "Pouch"), options=img_opts("gear", choices),
                            width=240, dense=True, menu_height=420, on_select=set_item), info], expand=True, spacing=6)],
                vertical_alignment=ft.CrossAxisAlignment.START)))
        return ft.ListView(expand=True, controls=[ft.ResponsiveRow(
            [ft.Container(c, col={"xs": 12, "md": 6, "xl": 4}) for c in cards])])

    # ---- amulets
    def amulet_tab(self):
        cards = []
        builders = {}
        for group, names in AMULET_GROUPS.items():
            am = self.s["amulets"].setdefault(group, {"name": None, "stats": []})
            body = ft.Column(spacing=6)
            pic = ft.Container(img("amulet", am["name"], 56) if am.get("name") else
                               ft.Icon(ft.Icons.CIRCLE_OUTLINED, color=LINE, size=40),
                               width=60, height=60, alignment=ft.Alignment.CENTER)

            def build(group=group, am=am, body=body):
                body.controls = []
                if not am.get("name"):
                    return
                rows = StatRows(am["stats"], HIVE_KEYS, self.changed)
                pool = amulet_pool(am["name"])

                def add_pool(e):
                    k, op, lo, hi = pool[int(e.control.value)]
                    am["stats"].append([k, op, round((lo + hi) / 2, 4)])
                    build()
                    body.update()
                    self.changed()

                pool_opts = [(str(i), f"{label(k)}  ({describe(k, op, lo)} to {describe(k, op, hi)})")
                             for i, (k, op, lo, hi) in enumerate(pool)]
                body.controls = [rows.view] + ([ft.Dropdown(options=opts(pool_opts), label="Add a stat it rolled",
                                                            width=460, dense=True, on_select=add_pool)] if pool else [])

            def set_tier(e, group=group, am=am, build=build, body=body, pic=pic):
                am["name"] = None if e.control.value == NONE else e.control.value
                am["stats"] = amulet_rows(am["name"]) if am["name"] else []
                pic.content = (img("amulet", am["name"], 56) if am["name"] else
                               ft.Icon(ft.Icons.CIRCLE_OUTLINED, color=LINE, size=40))
                builders[group]()
                body.update()
                pic.update()
                self.changed()

            if group == "Star":
                inner_build = build

                def build(am=am, body=body, inner_build=inner_build):
                    inner_build()
                    allowed = STAR_PASSIVES.get(am.get("name") or "", [])
                    if not allowed:
                        return
                    chosen = am.setdefault("passives", [])

                    def toggle(e, p):
                        if e.control.value and p not in chosen:
                            chosen.append(p)
                        elif not e.control.value and p in chosen:
                            chosen.remove(p)
                        self.changed()

                    body.controls.append(ft.Text("Passives on your amulet", weight=ft.FontWeight.BOLD, size=12))
                    body.controls.append(ft.Row([ft.Checkbox(label=p, value=p in chosen,
                                                             on_change=lambda e, p=p: toggle(e, p)) for p in allowed],
                                                wrap=True))
            builders[group] = build
            build()
            cards.append(card(f"{group} Amulet", ft.Row([pic, ft.Dropdown(
                value=am.get("name") or NONE, options=img_opts("amulet", [(NONE, "None")] + [(n, n) for n in names]),
                width=280, dense=True, on_select=set_tier)]), body))
        return ft.ListView(expand=True, controls=[
            ft.Text("Choose each amulet you wear, then edit its stats to match the numbers on yours. "
                    "Guaranteed stats are prefilled at mid-roll. Add the random stats your amulet rolled from the menu.", size=12),
            ft.ResponsiveRow([ft.Container(c, col={"xs": 12, "lg": 6}) for c in cards])])

    # ---- buffs
    def buff_tab(self):
        rows = StatRows(self.s["buffs"], HIVE_KEYS, self.changed, with_label=True,
                        hint="Everything else that boosts you: badges, the sticker stack, field boosts, nectar, "
                             "Inspire, Polar Power, and so on. Values are what the game shows.")

        def preset(items):
            def go(e):
                self.s["buffs"].extend([list(r) for r in items])
                rows._render()
                rows.view.update()
                self.changed()
            return go

        f = self.s["field"]
        def item(name, *rows_):
            return (name, [list(r) + [name] for r in rows_])

        presets = [   # values from the wiki's Buffs & Debuffs page
            item("Field Boost x2", (f"field_pollen:{f}", "add", 1.0)),
            item("Field Boost x5 (max)", (f"field_pollen:{f}", "add", 4.0)),
            item("Super Smoothie", ("capacity", "mul", 1.5), ("red_pollen", "mul", 1.6), ("blue_pollen", "mul", 1.6),
                 ("white_pollen", "mul", 1.6), ("bee_gather_pollen", "mul", 1.4), ("tool_pollen", "mul", 1.4),
                 ("convert_rate", "mul", 2), ("convert_rate_at_hive", "mul", 1.5), ("instant_conversion", "add", 0.12),
                 ("crit_chance", "add", 0.07), ("bee_movespeed", "mul", 1.25)),
            item("Purple Potion", ("capacity", "mul", 1.25), ("red_pollen", "mul", 1.5), ("blue_pollen", "mul", 1.5),
                 ("bee_gather_pollen", "mul", 1.3), ("tool_pollen", "mul", 1.3)),
            item("Tropical Drink", ("white_pollen", "mul", 1.25), ("instant_conversion", "add", 0.10), ("crit_chance", "add", 0.05)),
            item("Blue Extract", ("blue_pollen", "mul", 1.25)),
            item("Red Extract", ("red_pollen", "mul", 1.25)),
            item("Glue", ("bee_gather_pollen", "mul", 1.25), ("tool_pollen", "mul", 1.25)),
            item("Enzymes", ("convert_rate", "mul", 1.25), ("instant_conversion", "add", 0.10)),
            item("Oil", ("bee_movespeed", "mul", 1.2), ("player_movespeed_flat", "add", 0)),
            item("Marshmallow Bee", ("white_pollen", "add", 0.5), ("capacity", "add", 0.5), ("convert_rate", "add", 2.5)),
            item("Cool Breeze (max)", ("convert_rate_at_hive", "add", 0.25), ("tool_pollen", "add", 0.25),
                 ("bee_gather_pollen", "add", 0.25), ("honey_per_pollen", "add", 0.05), ("capacity", "mul", 1.25)),
            item("Stinger", ("attack_mult", "mul", 1.5)),
        ]
        return ft.ListView(expand=True, controls=[
            ft.Text("Items and boosts you keep running. Each button adds the item's exact wiki buff.", size=12, color=MUTED),
            ft.Row([ft.Text("Quick add:")] + [ft.OutlinedButton(content=n, on_click=preset(r)) for n, r in presets], wrap=True),
            rows.view])

    # ---- alts
    ALT_PRESETS = {
        "Fuzzy alt": [{"type": "Fuzzy", "count": 40, "level": 15, "gifted": True}],
        "Tad alt": [{"type": "Tadpole", "count": 40, "level": 15, "gifted": True}],
        "Fuzzy + Tad alt": [{"type": "Fuzzy", "count": 25, "level": 15, "gifted": True},
                            {"type": "Tadpole", "count": 25, "level": 15, "gifted": True}],
    }

    def alt_tab(self):
        alts = self.s.setdefault("alts", [])
        self.alt_list = ft.Column(spacing=10)

        def add(name, groups):
            def go(e):
                a = new_alt(f"{name} {len(alts) + 1}")
                a["bees"] = copy.deepcopy(groups)
                alts.append(a)
                self._render_alts()
                self.changed()
            return go

        self._render_alts(update=False)
        return ft.ListView(expand=True, spacing=10, controls=[
            ft.Text("Alt accounts macroing in the same field. Flowers are shared, so an alt's pollination "
                    "(Fuzzy Coat, Pollen Haze) raises your flower tiers, and bubbles from its frogs pay you as well. "
                    "Its own Gathering Bubbles, tokens and buffs only help the alt (tokens are client-side, and a "
                    "popped bubble pays its owner).", size=12),
            ft.Row([ft.Text("Add:")] + [ft.OutlinedButton(content=n, icon=ft.Icons.PERSON_ADD, on_click=add(n, g))
                                        for n, g in self.ALT_PRESETS.items()]
                   + [ft.TextButton(content="Empty alt", on_click=add("Alt", []))], wrap=True),
            self.alt_list,
        ])

    def _render_alts(self, update=True):
        alts = self.s["alts"]
        self.alt_list.controls = [self._alt_card(a) for a in alts] or [
            ft.Text("No alts. Add one above to see what it does for your main.", italic=True)]
        if update:
            self.alt_list.update()

    def _alt_card(self, a):
        groups_col = ft.Column(spacing=4)
        bee_names = sorted(GAME["bees"])

        def render_groups(update=True):
            groups_col.controls = [group_row(g) for g in a["bees"]] or [ft.Text("No bees yet.", italic=True, size=12)]
            if update:
                groups_col.update()

        def group_row(g):
            def set_(key, cast):
                def h(e):
                    g[key] = cast(e.control.value)
                    self.changed()
                return h

            def remove(e):
                a["bees"].remove(g)
                render_groups()
                self.changed()

            return ft.Row([
                ft.Dropdown(value=g["type"], options=img_opts("face", ((n, n) for n in bee_names)), width=170,
                            dense=True, menu_height=400, on_select=set_("type", str)),
                ft.TextField(value=str(g["count"]), label="Count", width=80, dense=True,
                             on_change=set_("count", lambda v: max(0, min(50, int(num(v, 0)))))),
                ft.TextField(value=str(g["level"]), label="Lvl", width=70, dense=True,
                             on_change=set_("level", lambda v: max(1, min(25, int(num(v, 1)))))),
                ft.Checkbox(label="Gifted", value=g["gifted"], on_change=set_("gifted", bool)),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, on_click=remove),
            ], spacing=8)

        def add_group(e):
            a["bees"].append({"type": "Fuzzy", "count": 1, "level": 10, "gifted": False})
            render_groups()
            self.changed()

        def field(key, label_, width=150):
            def h(e):
                a[key] = num(e.control.value, a[key])
                self.changed()
            return ft.TextField(value=f"{a[key]:g}", label=label_, width=width, dense=True, on_change=h)

        def set_name(e):
            a["name"] = e.control.value or a["name"]
            self.changed()

        def set_gear(key):
            def h(e):
                a[key] = e.control.value
                self.changed()
            return h

        def remove_alt(e):
            self.s["alts"].remove(a)
            self._render_alts()
            self.changed()

        render_groups(update=False)
        faces = [bee_face(g["type"], 30, g["gifted"]) for g in a["bees"][:6]]
        return card(
            a["name"],
            ft.Row(faces, spacing=4) if faces else ft.Container(),
            ft.Row([ft.TextField(value=a["name"], label="Name", width=180, dense=True, on_change=set_name),
                    ft.Dropdown(value=a["tool"], options=img_opts("tool", ((n, n) for n in GAME["tools"])), label="Tool",
                                width=210, dense=True, menu_height=420, on_select=set_gear("tool")),
                    ft.Dropdown(value=a["bag"], options=img_opts("gear", ((n, n) for n in GAME["gear"]["bag"])), label="Bag",
                                width=230, dense=True, menu_height=420, on_select=set_gear("bag")),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, tooltip="Remove alt", on_click=remove_alt)], wrap=True),
            ft.Row([field("overlap_pct", "Overlap with you %"), field("token_pickup_pct", "Token pickup %"),
                    field("ability_rate_pct", "Extra Bee Ability Rate %", 190)], wrap=True),
            ft.Text("Overlap: how much of the alt's gathering is inside your area (100 = standing with you). "
                    "Token pickup: how many of its Pollen Haze / Summon Frog tokens its macro grabs.", size=11,
                    color=ft.Colors.ON_SURFACE_VARIANT),
            groups_col,
            ft.TextButton(content="Add bees", icon=ft.Icons.ADD, on_click=add_group),
        )

    def _alts_card(self):
        solo, full, each = alt_impact(self.s)
        r = compute(self.s)
        own = {a["name"]: a["honey_per_hour"] for a in r["alts"]}
        gain = full - solo
        lines = [
            ft.Text(f"Your main: {fmt(solo)}/hr alone → {fmt(full)}/hr with alts "
                    f"({'+' if gain >= 0 else ''}{fmt(gain)}/hr, {gain / solo:+.0%})" if solo else "-",
                    size=16, weight=ft.FontWeight.BOLD, color=GOOD if gain > 0 else None),
        ]
        for name, d in each:
            alt = next(a for a in self.s["alts"] if a["name"] == name)
            kinds = {g["type"] for g in alt["bees"] if g.get("count")}
            why = []
            if "Fuzzy" in kinds:
                why.append("Fuzzy Coat pollinates flowers near it, raising your flower tiers"
                           + (" plus field-wide Pollen Haze" if any(g["type"] == "Fuzzy" and g["gifted"] for g in alt["bees"])
                              else " (no Pollen Haze: its Fuzzy Bees aren't gifted)"))
            if "Tadpole" in kinds:
                why.append(f"its frogs (1 per {token_interval('Summon Frog'):.0f} s per Tadpole) make bubbles that pay "
                           "you too. Its Gathering Bubbles only pay the alt")
            if not why:
                why.append("it doesn't change your field: only Fuzzy and Tadpole alts feed your main")
            lines.append(ft.Text(f"{name}: +{fmt(d)}/hr to your main, plus {fmt(own.get(name, 0))}/hr of its own "
                                 f"honey. {'; '.join(why)}.", size=12))
        total = full + sum(own.values())
        lines.append(ft.Text(f"All accounts together: {fmt(total)}/hr ({fmt(total * 24)}/day).", size=13))
        if r["flower_tier"] > 4.8:
            lines.append(ft.Text("Your flowers are almost all stars, so more pollination won't add much. The alt's extra "
                                 "bees are past the point of diminishing returns.", size=12, italic=True))
        return card("Alt accounts", *lines)

    # ---- field & settings
    def settings_tab(self):
        st = self.s["settings"]

        def field_text(name):
            fd = GAME["fields"][name]
            tiers = ", ".join(f"{share:.0%} {n}" for n, share in zip(("single", "double", "triple", "large", "star"),
                                                                    fd["sizes"]) if share)
            return (f"{fd['flowers']} flowers · {fd['white']:.0%} white, {fd['red']:.0%} red, {fd['blue']:.0%} blue · "
                    f"{tiers} (average tier {fd['avg_size']:.2f})")

        finfo = ft.Text(field_text(self.s["field"]), size=12)

        def set_field(e):
            self.s["field"] = e.control.value
            finfo.value = field_text(e.control.value)
            finfo.update()
            self.changed()

        controls = [card("Field", ft.Dropdown(value=self.s["field"], options=opts((n, n) for n in sorted(GAME["fields"])),
                                              width=280, dense=True, on_select=set_field), finfo)]
        fields = []
        for key, name, k, help_ in SETTING_INFO:
            shown = st[key] * 100 if k == "pct" else st[key]

            def set_(e, key=key, k=k):
                v = num(e.control.value, st[key] * (100 if k == "pct" else 1))
                st[key] = v / 100 if k == "pct" else v
                self.changed()

            fields.append(ft.Row([ft.TextField(value=f"{shown:g}", label=name + (" %" if k == "pct" else ""), width=300,
                                               dense=True, on_change=set_),
                                  ft.Text(help_, size=11, expand=True, color=ft.Colors.ON_SURFACE_VARIANT)]))

        def set_honeyday(e):
            st["honeyday"] = e.control.value
            self.changed()

        nectar_rows = []
        for n in ("comforting", "motivating", "satisfying", "refreshing", "invigorating"):
            lbl = ft.Text(f"{st[f'nectar_{n}']:.0f}%", width=44)

            def set_nectar(e, n=n, lbl=lbl):
                st[f"nectar_{n}"] = float(e.control.value)
                lbl.value = f"{st[f'nectar_{n}']:.0f}%"
                lbl.update()
                self.changed()

            nectar_rows.append(ft.Row([ft.Text(n.title(), width=110), ft.Slider(min=0, max=100, divisions=20,
                                       value=st[f"nectar_{n}"], expand=True, on_change_end=set_nectar), lbl]))
        controls.append(card(
            "Nectars & event buffs",
            ft.Text("Nectar strength scales with time left (100% = 24 h). Each nectar also gives up to x1.05 Honey Per Pollen.",
                    size=11, color=MUTED),
            *nectar_rows,
            ft.Switch(label="Honeyday (x2 Pollen and Convert Rate)", value=bool(st.get("honeyday")), on_change=set_honeyday)))
        controls.append(card("Model settings", *fields))
        return ft.ListView(expand=True, controls=controls, spacing=10)

    # ---- badges
    def badge_tab(self):
        badges = self.s.setdefault("badges", {})
        tiers = ["Cadet", "Hotshot", "Ace", "Master", "Grandmaster"]
        cards = []
        for cat, by_tier in GAME.get("badges", {}).items():
            info = ft.Text(size=11, color=MUTED)

            def show(cat=cat, info=info):
                tier = badges.get(cat)
                info.value = (", ".join(describe(*x) for x in GAME["badges"][cat][tier]) if tier else "No badge")

            def set_tier(e, cat=cat, info=info, show=show):
                if e.control.value == NONE:
                    badges.pop(cat, None)
                else:
                    badges[cat] = e.control.value
                show()
                info.update()
                self.changed()

            show()
            cards.append(ft.Container(col={"xs": 12, "md": 6, "xl": 4}, content=card(
                f"{cat} Badge", ft.Dropdown(value=badges.get(cat, NONE), options=opts([(NONE, "None")] + [(t, t) for t in tiers]),
                                            width=200, dense=True, on_select=set_tier), info)))

        def all_gm(e):
            for cat in GAME.get("badges", {}):
                badges[cat] = "Grandmaster"
            self.changed()
            self._show(0)

        return ft.ListView(expand=True, spacing=10, controls=[
            ft.Row([ft.Text("Your badge tiers (System Page → Badges). Higher tiers replace lower ones.", size=12),
                    ft.TextButton(content="Set all to Grandmaster", on_click=all_gm)], wrap=True),
            ft.ResponsiveRow(cards)])

    # ---- system page overrides
    def overrides_tab(self):
        ov = self.s.setdefault("overrides", {})
        r = compute({**self.s, "overrides": {}})
        keys = [k for k in r["stats"] if not k.startswith("field_pollen")] + ["bubble_pollen", "bomb_pollen", "white_field_capacity",
                                                                           "red_field_capacity", "unique_instant_conversion"]
        seen, rows = set(), []
        for k in keys:
            if k in seen or k not in STAT_DEFS:
                continue
            seen.add(k)
            computed = r["stats"].get(k)
            if computed is None:
                from .engine import _hive_stats
                computed = _hive_stats({**self.s, "overrides": {}}).get(k)

            def set_ov(e, k=k):
                txt = e.control.value.strip()
                if txt == "":
                    ov.pop(k, None)
                else:
                    ov[k] = num(txt) / 100 if kind(k) != "flat" else num(txt)
                self.changed()

            cur = ov.get(k)
            shown = "" if cur is None else (f"{cur * 100:g}" if kind(k) != "flat" else f"{cur:g}")
            rows.append(ft.Row([ft.Text(label(k), width=230), ft.Text(fmt_stat(k, computed), width=110, color=MUTED),
                                ft.TextField(value=shown, hint_text="auto", width=130, dense=True, on_change=set_ov),
                                ft.Text("%" if kind(k) != "flat" else "", width=20)]))
        return ft.ListView(expand=True, spacing=6, controls=[
            ft.Text("Type in the totals from your in-game System Page to replace the calculated ones. They then include "
                    "everything the app can't see: the sticker stack, Robo upgrades, hive bonuses and so on. Leave a box empty "
                    "to use the calculated value. Take the numbers with no temporary buffs running (no boosts, items or "
                    "tokens), because the app adds those itself.", size=12, color=MUTED),
            ft.Row([ft.Text("Stat", width=230, weight=ft.FontWeight.BOLD),
                    ft.Text("Calculated", width=110, weight=ft.FontWeight.BOLD),
                    ft.Text("Your System Page", width=150, weight=ft.FontWeight.BOLD)]),
            *rows,
            ft.TextButton(content="Clear all overrides", icon=ft.Icons.RESTART_ALT,
                          on_click=lambda e: (ov.clear(), self.changed(), self._show(0)))])

    # ------------------------------------------------------------ RESULTS
    def results_view(self):
        r = compute(self.s)
        base, sens = sensitivity(self.s)
        boxes = ft.Row(wrap=True, spacing=10, controls=[
            stat_box("Honey / hour", fmt(r["honey_per_hour"]), color=HONEY),
            stat_box("Honey / day", fmt(r["honey_per_day"])),
            stat_box("Converted in the field", f"{fmt(r['field_converted_per_sec'])}/s",
                     "Diamond Drain, Star Shower, Coin Scatter, Petal Storm"),
            stat_box("Pollen / sec (total)", fmt(r["gross_pollen_per_sec"]),
                     f"bees {fmt(r['bee_pollen_per_sec'])} · tool {fmt(r['tool_pollen_per_sec'])}"
                     + (f" · abilities {fmt(r['ability_pollen_per_sec'])}" if r["ability_pollen_per_sec"] else "")
                     + (f" · bubbles {fmt(r['bubble_pollen_per_sec'])}" if r["bubble_pollen_per_sec"] else "")),
            stat_box("Capacity", fmt(r["capacity"]), f"fills in {fmt_time(r['fill_time'])}"),
            stat_box("Convert time", fmt_time(r["convert_time"]), f"hive converts {fmt(r['hive_convert_per_sec'])}/s"),
            stat_box("Instantly converted", f"{r['instant_share']:.1%}", "of the pollen you collect"),
            stat_box("Time in field", f"{r['field_time_share']:.0%}",
                     f"cycle {fmt_time(r['cycle_time'])} incl. {fmt_time(r['walk_time'])} walking"),
        ])
        tier_names = ("Single", "Double", "Triple", "Large", "Star")
        tier_cols = ["#3A3A3F", "#5C5C63", "#86868D", "#B5B5BA", TEXT]
        tier_bar = ft.Row(spacing=0, height=18, controls=[
            ft.Container(expand=max(1, int(1000 * share)), bgcolor=col, tooltip=f"{n}: {share:.0%}")
            for n, share, col in zip(tier_names, r["tier_dist"], tier_cols) if share > 0.001])
        poll_lines = [ft.Text(f"{src}: {rate * 60:.1f} flowers/min", size=12) for src, rate in r["pollination"].items()]
        flowers_card = card(
            "Flowers (bee and tool pollen scale with flower tier: single x1 up to star x5)",
            ft.Text(f"Average tier {r['natural_tier']:.2f} natural → {r['flower_tier']:.2f} with pollination "
                    f"({r['flower_tier'] / r['natural_tier'] - 1:+.0%} pollen) across {r['gather_area']:.0f} flowers", size=13),
            tier_bar,
            ft.Row([ft.Text(f"{n} {share:.0%}", size=11) for n, share in zip(tier_names, r["tier_dist"])], spacing=14),
            *(poll_lines or [ft.Text("No pollination. Fuzzy Bees, Lei/Poinsettia/Rose Headband, Pollen Haze, "
                                     "Guiding Star and Diamond Drain raise flower tiers.", size=12, italic=True)]),
            *([ft.Text(f"Pollen Haze is over the field {r['haze_uptime']:.0%} of the time "
                       f"(max ~{30 / 180:.0%}: one haze per 3 minutes per field).", size=12)] if r["haze_uptime"] else []),
            *[ft.Text(f"{src}: {fmt(v)} pollen/s to you", size=12) for src, v in r["bubble_sources"].items()],
        )
        alts_card = self._alts_card() if self.s.get("alts") else None
        tot = sum(r["pollen_by_color"].values()) or 1
        colour_bar = ft.Row(spacing=0, height=18, controls=[
            ft.Container(expand=max(1, int(1000 * v / tot)), bgcolor=col, tooltip=f"{c}: {fmt(v)}/s")
            for (c, v), col in zip(r["pollen_by_color"].items(), [ft.Colors.GREY_300, ft.Colors.RED_400, ft.Colors.BLUE_400])
            if v > 0]) if tot > 1 else ft.Text("-")

        best = max((d for _, d in sens), default=0) or 1
        sens_rows = [ft.Row([
            ft.Text(n, width=210, size=13),
            ft.Container(width=max(2, 260 * max(d, 0) / best), height=12, bgcolor=HONEY, border_radius=3),
            ft.Text(f"+{fmt(d)}/hr ({d / base:+.1%})" if base else "-", size=12)]) for n, d in sens]

        stat_rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(label(k))), ft.DataCell(ft.Text(fmt_stat(k, v)))])
                     for k, v in r["stats"].items()]
        bee_rows = [ft.DataRow(cells=[
            ft.DataCell(ft.Row([bee_face(b["type"], 26, b["gifted"]), ft.Text(b["type"])], spacing=8)),
            ft.DataCell(ft.Text(str(b["level"]))),
            ft.DataCell(ft.Row([img("beequip", b["beequip"], 22), ft.Text(b["beequip"])], spacing=6) if b["beequip"]
                        else ft.Text("-")), ft.DataCell(ft.Text(fmt(b["gather"]))), ft.DataCell(ft.Text(fmt(b["attack"]))),
            ft.DataCell(ft.Text(f"{b['uptime']:.0%}")), ft.DataCell(ft.Text(fmt(b["pollen_per_sec"]))),
            ft.DataCell(ft.Text(fmt(b["convert_per_sec"])))]) for b in sorted(r["bees"], key=lambda x: -x["pollen_per_sec"])]

        return ft.ListView(expand=True, spacing=12, controls=[
            ft.Text(self.s["name"], size=22, weight=ft.FontWeight.BOLD),
            ft.Text(f"Gathering in {self.s['field']} with a {self.s['tool']}", size=13),
            boxes,
            card("Pollen by flower colour", colour_bar),
            self._honey_card(r),
            self._abilities_card(r),
            flowers_card,
            *([alts_card] if alts_card else []),
            card("Where your next gains come from (honey/hr from each change)", *sens_rows),
            ft.ResponsiveRow([
                ft.Container(col={"xs": 12, "lg": 5}, content=card("Your totals (compare with your System Page)", ft.DataTable(
                    columns=[ft.DataColumn(ft.Text("Stat")), ft.DataColumn(ft.Text("Value"), numeric=True)],
                    rows=stat_rows, data_row_min_height=28, data_row_max_height=32))),
                ft.Container(col={"xs": 12, "lg": 7}, content=card("Per bee", ft.DataTable(
                    columns=[ft.DataColumn(ft.Text(c), numeric=c not in ("Bee", "Beequip")) for c in
                             ("Bee", "Lvl", "Beequip", "Gather", "Attack", "Awake", "Pollen/s", "Converts/s")],
                    rows=bee_rows, data_row_min_height=28, data_row_max_height=32) if bee_rows else ft.Text("No bees."))),
            ]),
        ])

    def _honey_card(self, r):
        """Balloons, Shimmering Honey, passives and attack."""
        lines = []
        if r["balloons_alive"]:
            lines.append(ft.Text(
                f"Balloons: about {r['balloons_alive']:.1f} out at once, covering {r['balloon_cover']:.0%} of your area. "
                f"They catch {fmt(r['balloon_pollen_per_sec'])} pollen/s, which is {fmt(r['balloon_per_trip'])} per trip "
                "to the hive. Buoyant Bees convert it x3.", size=12))
        bb = self.s["settings"].get("balloon_blessing", 0)
        lines.append(ft.Text(f"Balloon Blessing: x{bb:.0f}" + (f" (x{1 + 0.03 * bb:.2f} Capacity, x{1 + 0.015 * bb:.2f} Honey at Hive)"
                                                              if bb else ". Set your stacks under Field & Settings."),
                             size=12, color=MUTED if not bb else None))
        if r["shimmering"] > 1:
            lines.append(ft.Text(f"Shimmering Honey (Diamond Bees): x{r['shimmering']:.2f} honey from hive conversion.", size=12))
        pop = r["pop_star"]
        if pop["bloat"] > 1 or pop["blue_pollen"] > 1:
            lines.append(ft.Text(f"Pop Star: x{pop['blue_pollen']:.2f} Blue Pollen on average, Bubble Bloat x{pop['bloat']:.2f} "
                                 "(Blue Field Capacity and Convert Rate at Hive).", size=12))
        for name, d in r["passives"].items():
            extra = f", converts {fmt(d['pollen_per_sec'])} pollen/s from your bag" if d["pollen_per_sec"] else ""
            lines.append(ft.Text(f"{name}: {d['per_min']:.2f} activations/min{extra}", size=12))
        lines.append(ft.Text(f"Attack total: {fmt(r['attack_total'])} · Convert total: {fmt(r['convert_total'])}",
                             size=12, color=MUTED))
        return card("Honey extras: balloons, passives & attack", *lines)

    def _abilities_card(self, r):
        b = r["buffs"]

        def chip(name, value, sub=None):
            return ft.Container(padding=ft.Padding.symmetric(horizontal=10, vertical=6), border_radius=10, bgcolor=CARD,
                                border=ft.Border.all(1, LINE), content=ft.Column([
                                    ft.Text(name, size=11, color=MUTED), ft.Text(value, size=15, weight=ft.FontWeight.BOLD),
                                    *([ft.Text(sub, size=10, color=MUTED)] if sub else [])], spacing=1, tight=True))

        boosts = b["boost"]
        chips = [
            chip("All buffs on Pollen", f"x{b['pollen']:.2f}", "average, multiplied together"),
            chip("Inspire", f"x{b['inspire']:.2f}", "gifted bees, up to x51"),
            chip("Baby Love", f"x{b['baby_love']:.2f}", "x2 while active"),
            chip("Bear Morph", f"x{b['bear_morph']:.2f}", "x2, Mother x2.5"),
            chip("Pollen Mark", f"x{b['pollen_mark']:.2f}", "x1.5 per mark"),
            chip("Boosts W / R / B", f"x{boosts['white']:.2f} / {boosts['red']:.2f} / {boosts['blue']:.2f}", "up to x3"),
            chip("Focus", f"+{b['crit_chance'] * 100:.0f}% crit", "up to +30%"),
            chip("Melody", f"+{b['crit_power'] * 100:.0f}% crit power", "+100% while active"),
            chip("Bomb Combo", f"x{b['bomb_power']:.2f} bombs", "up to x3.5"),
            chip("Haste", f"x{b['haste']:.2f} speed", "up to x2"),
        ]
        rows = []
        for name, d in sorted(r["tokens"].items(), key=lambda kv: -(kv[1]["pollen"] + kv[1]["honey"] / 3600)):
            what = (f"{fmt(d['pollen'])} pollen/s" if d["pollen"] else f"{fmt(d['honey'] * 3600)} honey/hr" if d["honey"]
                    else "buff")
            rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(name)), ft.DataCell(ft.Text(f"{d['rate'] * 60:.1f}")),
                                          ft.DataCell(ft.Text(what))]))
        table = ft.DataTable(columns=[ft.DataColumn(ft.Text("Ability")), ft.DataColumn(ft.Text("Tokens/min"), numeric=True),
                                      ft.DataColumn(ft.Text("Adds"))], rows=rows,
                             data_row_min_height=26, data_row_max_height=30) if rows else ft.Text(
            "Your bees don't spawn any modelled abilities.", italic=True, size=12)
        return card(
            "Abilities & buffs (from your bees' ability tokens)",
            ft.Text(f"Ability tokens add {fmt(r['ability_pollen_per_sec'])} pollen/s and "
                    f"{fmt(r['token_honey_per_hour'])} honey/hr from honey tokens. Spawn rates and buff values come "
                    "from the wiki, using your Bee Ability Rate and token pickup %.", size=12, color=MUTED),
            ft.Row(chips, wrap=True, spacing=8, run_spacing=8),
            table,
            ft.Text("Not modelled yet: " + NOT_MODELLED + ".", size=11, color=MUTED, italic=True),
        )

    # ------------------------------------------------------------ COMPARE
    def compare_view(self):
        names = opts((str(i), s["name"]) for i, s in enumerate(self.setups))
        other = 0 if self.cur != 0 else min(1, len(self.setups) - 1)
        a_dd = ft.Dropdown(options=names, value=str(other), label="Current setup (A)", width=260, dense=True)
        b_dd = ft.Dropdown(options=names, value=str(self.cur), label="New setup (B)", width=260, dense=True)
        out = ft.Column(spacing=12)

        def render(e=None):
            A, B = self.setups[int(a_dd.value)], self.setups[int(b_dd.value)]
            ra, rb = compute(A), compute(B)
            ha, hb = ra["honey_per_hour"], rb["honey_per_hour"]
            diff = hb - ha
            pct = diff / ha if ha else 0
            colour = GOOD if diff > 0 else BAD if diff < 0 else None
            metrics = [
                ("Honey / hour", "honey_per_hour", fmt), ("Pollen / sec", "gross_pollen_per_sec", fmt),
                ("Bee pollen / sec", "bee_pollen_per_sec", fmt), ("Tool pollen / sec", "tool_pollen_per_sec", fmt),
                ("Capacity", "capacity", fmt), ("Bag fill time", "fill_time", fmt_time),
                ("Convert time", "convert_time", fmt_time), ("Instantly converted", "instant_share", lambda v: f"{v:.1%}"),
                ("Average flower tier", "flower_tier", lambda v: f"{v:.2f}"),
                ("Bubble pollen / sec", "bubble_pollen_per_sec", fmt),
                ("Ability pollen / sec", "ability_pollen_per_sec", fmt),
                ("Honey from tokens / hr", "token_honey_per_hour", fmt),
                ("Time in field", "field_time_share", lambda v: f"{v:.0%}"),
            ]

            def delta_cell(va, vb, neutral=False):
                if not all(map(math.isfinite, (va, vb))) or va == vb:
                    return ft.Text("-")
                d = (vb - va) / va if va else 0
                return ft.Text(f"{d:+.1%}", color=None if neutral else GOOD if vb > va else BAD)

            rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(n)), ft.DataCell(ft.Text(f(ra[k]))),
                                      ft.DataCell(ft.Text(f(rb[k]))),
                                      ft.DataCell(delta_cell(ra[k], rb[k], neutral=k in ("fill_time", "convert_time", "field_time_share")))])
                    for n, k, f in metrics]
            stat_rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(label(k))), ft.DataCell(ft.Text(fmt_stat(k, ra["stats"][k]))),
                                           ft.DataCell(ft.Text(fmt_stat(k, rb["stats"].get(k, 0)))),
                                           ft.DataCell(delta_cell(ra["stats"][k], rb["stats"].get(k, 0)))])
                         for k in ra["stats"] if k in rb["stats"] and abs(ra["stats"][k] - rb["stats"][k]) > 1e-9]
            out.controls = [
                ft.Container(padding=18, border_radius=12, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, content=ft.Column([
                    ft.Text(f"{B['name']} vs {A['name']}", size=14),
                    ft.Text(("+" if diff >= 0 else "") + f"{fmt(diff)} honey/hr ({pct:+.2%})", size=30,
                            weight=ft.FontWeight.BOLD, color=colour),
                    ft.Text(f"That's {('+' if diff >= 0 else '')}{fmt(diff * 24)} honey per day.", size=13)], tight=True)),
                card("Side by side", ft.DataTable(columns=[ft.DataColumn(ft.Text(c)) for c in ("", "A", "B", "Change")],
                                                  rows=rows, data_row_min_height=28, data_row_max_height=32)),
                card("Stats that differ", ft.DataTable(columns=[ft.DataColumn(ft.Text(c)) for c in ("Stat", "A", "B", "Change")],
                                                       rows=stat_rows, data_row_min_height=28, data_row_max_height=32)
                     if stat_rows else ft.Text("No stat differences.")),
            ]
            if e is not None:
                out.update()

        a_dd.on_select = render
        b_dd.on_select = render
        render()
        return ft.ListView(expand=True, spacing=12, controls=[
            ft.Text("Tip: duplicate a setup (copy icon at the top), make your change, then compare the two here.", size=12),
            ft.Row([a_dd, ft.Icon(ft.Icons.ARROW_FORWARD), b_dd]), out])

    # ------------------------------------------------------------ GUIDE
    def guide_view(self):
        from .guide import COMPS, SECTIONS, SOURCE

        def visuals(items, cat):
            if not items:
                return None
            if cat == "face":
                return ft.Row([ft.Column([bee_face(b, 34), ft.Text(f"×{n}" if n > 1 else b, size=10, color=MUTED)],
                                         spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True)
                               for b, n in items], wrap=True, spacing=8)
            return ft.Row([ft.Column([img(cat, name, 44), ft.Text(name, size=10, color=MUTED)], spacing=2, tight=True,
                                     horizontal_alignment=ft.CrossAxisAlignment.CENTER) for name in items],
                          wrap=True, spacing=10)

        def load_comp(name):
            def go(e):
                c = new_setup(f"Guide: {name}")
                c["field"], c["tool"] = "Pine Tree Forest", self.s.get("tool", "Scooper")
                c["gear"] = dict(self.s.get("gear", {}))
                c["amulets"] = copy.deepcopy(self.s.get("amulets", {}))
                c["badges"] = dict(self.s.get("badges", {}))
                c["settings"] = dict(self.s["settings"])
                lvl = max((b["level"] for b in self.s["bees"]), default=15)
                slot = 0
                for bee, n in COMPS[name]:
                    for _ in range(n):
                        b = new_bee(bee, lvl, True)
                        b["slot"] = slot
                        slot += 1
                        c["bees"].append(b)
                self.setups.append(c)
                self.cur = len(self.setups) - 1
                self.sel = None
                self._persist()
                self._refresh_setup_dd()
                self._show(0)
                self._toast(f"Loaded the {name} comp as a new setup, using your gear, amulets and badges. "
                            "Compare it with your own setup on the Compare page.")
            return go

        blocks = [
            ft.Text("Blue Hive Guide", size=24, weight=ft.FontWeight.BOLD),
            ft.Text(SOURCE, size=12, color=MUTED),
            card("Try a guide comp",
                 ft.Text("Load one of the guide's hive comps as a new setup (gifted, at your hive's level) and compare "
                         "it with yours.", size=12, color=MUTED),
                 ft.Row([ft.OutlinedButton(content=n, icon=ft.Icons.HIVE, on_click=load_comp(n)) for n in COMPS], wrap=True)),
        ]
        for title, rows in SECTIONS:
            items = []
            for name, text, vis, cat in rows:
                v = visuals(vis, cat)
                items.append(ft.Container(
                    padding=ft.Padding.symmetric(vertical=8), border=ft.Border.only(top=ft.BorderSide(1, LINE)),
                    content=ft.Column([ft.Text(name, weight=ft.FontWeight.BOLD, size=13),
                                       ft.Text(text, size=12, color=MUTED, selectable=True), *([v] if v else [])],
                                      spacing=6, tight=True)))
            blocks.append(card(title, *items))
        return ft.ListView(expand=True, spacing=12, controls=blocks)

    # ------------------------------------------------------------ ABOUT
    def about_view(self):
        md = f"""
## How the estimate is made

All game numbers come from the Bee Swarm Simulator wiki ({GAME['source']}). Beequip and amulet values come from its copy of the game files.

**Bees.** Each bee gathers `base gather × flower tier × (1 + 5% per level above 1) × 1.5 if gifted`. Flower tier is single ×1, double ×2, triple ×3, large ×4 and star ×5, so a Basic Bee collects 10/20/30/40/50. A crit doubles a gather. Red and blue bees get **+50% on flowers of their own colour**.
A trip takes the bee's gather time plus flight time, and flight time depends on movespeed (`+3% per level`).
Energy is `base × (1 + 5% per level)`. When it runs out, the bee flies home at half speed, sleeps 30 s (Shocked Bee 15 s) and flies back at 1.5× speed.

**Stats.** Each stat is `(100% + all the "+%" bonuses) × all the "x" multipliers`, just like the System Page.
Gifted hive bonuses count once per bee type. Crits use your crit chance, crit power and super-crit values.

**Tool.** `pollen per flower × flower tier × flowers hit ÷ swing time × colour multipliers × Tool Pollen`.

**Flowers and pollination.** Fields only grow single, double and triple flowers. Large and star flowers come only from pollination.
Each pollination raises a flower one tier (star is the cap). A flower drops one tier for every minute it isn't pollinated again, down to its natural tier.
Lower-tier flowers are more likely to be picked.
The app simulates your gathering area second by second to find the steady-state mix of flower tiers. Sources:
- Fuzzy Coat: up to 5 nearby flowers per gather, 9 if gifted.
- Lei, Poinsettia and Rose Headband: a chance per gather.
- Pollen Haze: 30 flowers/s.
- Guiding Star: 15 + 1 per gifted type every 15 s.
- Diamond Drain: 10 + 3 per blue bee.

Uptimes for the triggered ones are under Field & Settings.

**Ability tokens.** Each bee spawns its abilities while it's gathering. The wiki's spawn formula is `use cooldown / r + attempt cooldown / r × (1 / (success × r) − 1)`, where r is Bee Ability Rate; a Bomb, for example, spawns about once every 20 s.
Bombs collect 7 pollen (Buzz, every colour) or 10 pollen (Red/Blue, their colour only) from 13 flowers (29 for Bomb+), × level/10 × Bomb Power × Bomb Pollen.
Beamstorm, Scratch, Triangulate, Mark Surge, Target Practice, Fuzz Bombs and Inferno's Fire Bees use their wiki amounts. Honey Gift gives 100 × level² (Gift+ 250 × level²), and Token Link gives 25 + 10 × level per linked token.

**Buffs.** Boost gives x1.2 colour pollen per stack (up to x3, 15 s). Inspire gives x2 per stack (up to x51, 5 s). Focus gives +3% crit per stack (up to +30%).
Bomb Combo gives x1.25 Bomb Power per stack (up to x3.5). Baby Love gives x2, Bear Morph x2 (Mother x2.5), Pollen Mark x1.5 per linked mark (up to x2.5), and Melody +100% crit power.
Stacking buffs average E[min(stacks, cap)], where the number of stacks is Poisson-distributed from the token rate × duration. One-off buffs count for the share of time they're active.

**Balloons.** Each Buoyant Bee spawns Inflate Balloons about every 52 s. A blue balloon lasts 20 s + 2 s per level and holds your capacity ÷ 6 (gold balloons from gifted Buoyants hold ×1.25).
Pollen collected under a balloon's 5-tile shadow goes into the balloon (+10%, or +20% on blue flowers) instead of your bag. Each Inflate Balloons token also adds +5% to every balloon, up to 10 times.
Balloons are converted at the hive after your bag, and Buoyant Bees convert balloon pollen ×3 (Balloon Enthusiast).
**Balloon Blessing** gives ×1.03 Capacity and ×1.015 Honey at Hive per stack, up to ×4 and ×2.5 at 100. Set your stacks under Field & Settings.

**Honey at Hive.** Hive conversions are multiplied by Honey Per Pollen and Honey at Hive (Dandelion badge, Satisfying nectar, Elf Cap, Candy Ring, Balloon Blessing).
Diamond Bees add **Shimmering Honey**: +25% honey (+2.5% per level, doubled if gifted), weighted by how much of the converting they do.

**Passives.** Diamond Drain (every 30th blue token, 45 s cooldown) converts 5M + your Convert Total (+10% per blue bee, +50% per gifted blue type).
Star Shower (every 40th Boost or Mark token, 30 s cooldown) drops 10 stars, each converting 1M + 200% of your Convert Total.
Coin Scatter, Petal Storm and Bubble Bombs use their wiki trigger counts and amounts.
Pop Star gives ×2 Blue Pollen (+1% per bubble you pop, up to ×4.5) and +10% Instant Blue Conversion for 45 s. Its Bubble Bloat gives up to ×6 Blue Field Capacity and Convert Rate at Hive.
Star Amulet passives also add their permanent ×1.25 capacity bonuses.

**Badges, nectars & items.** Badges use their wiki tier rewards. Nectars scale between their wiki minimum and maximum. Item presets (Super Smoothie, Purple Potion, Field Boost…) use the wiki buff values.

**System Page overrides.** Any total you type in from your in-game System Page replaces the calculated value. That covers everything the app can't see, like the sticker stack and Robo upgrades.

**Attack.** (base + Bee Attack + colour attack) × Attack Multiplier × 1.5 if gifted. Buoyant attack scales up to ×3 with Balloon Blessing.

**Bubbles.** A popped bubble collects 4 red / 6 white / 8 blue pollen from 29 flowers (+15% per gifted blue bee type, +5% per bee level), times flower tier and your Bubble Pollen.
Tadpole Bees make one on 65% of gathers (85% gifted) and Bubble Bees on 25% (50%). Frogs from Summon Frog (1 token per 80 s per Tadpole) make 3 bubbles each.

**Alt accounts.** Flowers are shared in a server, so an alt's pollination raises *your* flower tiers.
Pollen Haze covers the whole field for 30 s and can't happen again within 3 minutes, whoever summoned it.
If you pop an alt's bubble, the pollen goes to the alt. Bubbles from an alt's frogs pay both of you.
Tokens are client-side, so an alt's Baby Love, Inspire and so on only buff the alt.
Token rates use the wiki's spawn data (cooldowns and success rate, adjusted by Bee Ability Rate) times how many tokens the macro picks up.
Not modelled: alts taking pollen from the same flowers.

**Honey loop.** Pollen fills your bag, minus whatever is instantly converted (colour instant conversion first, then regular) and whatever balloons catch. You head back when the bag is full or after your gather time (14 min by default).
When the bag is full you walk to the hive and your bees convert it. Each bee converts
`(base convert + Convert Amount) × (1 + 10% per level) × Convert Rate × Convert Rate At Hive × 1.5 if gifted`.
Honey/hr = honey per loop ÷ loop time.

**Not simulated:** passives (Pop Star, Scorching Star, Petal Storm...), Pulse, Tornado, balloons, flames, goo, mobs and planters.
Add these on the **Buffs** tab, or use the *Extra ability pollen %* setting.
If your game numbers differ (base crit chance, for example), change them under **Field & Settings**.

Setups are saved automatically on this device (in your browser on the website).
"""
        return ft.ListView(expand=True, controls=[ft.Markdown(md, selectable=True)])


async def main(page: ft.Page):
    prefs = ft.SharedPreferences()
    App(page, prefs, await storage.load(prefs))
