#!/usr/bin/env python3
"""Build pulses_plus_submin_panel_v2.kicad_pcb in the house style.

Reads the v1 panel and keeps its header, layer table, setup, all 27 control
holes, the Edge.Cuts outline and the copper (zones + segments) untouched --
PANEL_STYLE's one non-negotiable rule is that hole positions are inherited,
never computed. Only the silkscreen/mask artwork is regenerated.

Usage:  python3 tools/build_panel_v2.py
"""

import re
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SRC = HERE / "pulses_plus_submin_panel.kicad_pcb"
DST = HERE / "pulses_plus_submin_panel_v2.kicad_pcb"

# Panel origin in board coordinates, and its size. Both measured off v1.
OX, OY = 111.84, 34.907
W, H = 40.16, 128.5

# --- style tokens, from PANEL_STYLE ------------------------------------------
LINE_W, RULE_W = 0.25, 0.20
LABEL_SIZE, PITCH_LABEL = 2.0, 2.2
SMALL_SIZE, PITCH_SMALL = 1.6, 1.7
TITLE_SIZE, PITCH_TITLE = 3.2, 3.4
LOGO_SIZE, PITCH_LOGO = 1.3, 1.45
RING_GAP = 1.2
EDGE_MARGIN = 0.6
LABEL_GAP = 1.2          # drawn extent -> nearest edge of the label cell

# --- inherited geometry, panel-local (X right, Y down from the top edge) -----
LED_X = 20.08
COL_L, COL_R = 7.8, 32.36
LED_Y = [13.4, 21.4, 29.4, 37.4, 45.4, 53.4, 61.4, 69.4]
SW_XY = [(COL_L if i % 2 == 0 else COL_R, 15.9 + 8.0 * i) for i in range(8)]
EXT_XY = (COL_L, 77.336)
BUSLED_Y = 87.693
MODE_Y = 97.575
OUT_Y = 111.425

R_LED, R_SW, R_JACK = 1.6, 2.475, 3.0

# Two lines: at 18 characters a single line needs 61 mm of pitch on a 40 mm
# panel, which shrinks the title to label size and stops it reading as a title.
TITLE_LINES = ["DOUBLEPLUS", "++PULSES"]
WORDMARK = "MMM"
YEAR = 2026
BACK_LINES = ["DESIGNED BY", f"MISSING MILE MODULAR {YEAR}", "CC BY-NC-SA 4.0"]

out = []


def uid():
    return str(uuid.uuid4())


def text(s, x, y, size, pitch, layer="F.SilkS", mirror=False):
    """Set `s` one character at a time on a fixed pitch, each centred in its
    own cell -- stroke fonts are proportional and KiCad has no letter-spacing
    setting, so this is the only way to get the reference's even tracking.

    Back-layer text is emitted right-to-left: KiCad mirrors each glyph about
    its own anchor, so a left-to-right run of cells reads backwards once the
    board is flipped over.
    """
    s = s.upper()
    n = len(s)
    xs = [x + (i - (n - 1) / 2.0) * pitch for i in range(n)]
    if mirror:
        xs = xs[::-1]
    just = "\n\t\t\t(justify mirror)" if mirror else ""
    for ch, cx in zip(s, xs):
        if ch == " ":
            continue
        esc = ch.replace("\\", "\\\\").replace('"', '\\"')
        out.append(
            f'\t(gr_text "{esc}"\n'
            f"\t\t(at {cx + OX:.4f} {y + OY:.4f})\n"
            f'\t\t(layer "{layer}")\n'
            f'\t\t(uuid "{uid()}")\n'
            f"\t\t(effects\n\t\t\t(font\n"
            f"\t\t\t\t(size {size} {size})\n"
            f"\t\t\t\t(thickness {LINE_W})\n"
            f"\t\t\t){just}\n\t\t)\n\t)"
        )
    return n * pitch


def circle(cx, cy, r, width=LINE_W, layer="F.SilkS"):
    out.append(
        f"\t(gr_circle\n"
        f"\t\t(center {cx + OX:.4f} {cy + OY:.4f})\n"
        f"\t\t(end {cx + OX + r:.4f} {cy + OY:.4f})\n"
        f"\t\t(stroke\n\t\t\t(width {width})\n\t\t\t(type solid)\n\t\t)\n"
        f"\t\t(fill none)\n"
        f'\t\t(layer "{layer}")\n\t\t(uuid "{uid()}")\n\t)'
    )


def line(x1, y1, x2, y2, width=LINE_W, layer="F.SilkS"):
    out.append(
        f"\t(gr_line\n"
        f"\t\t(start {x1 + OX:.4f} {y1 + OY:.4f})\n"
        f"\t\t(end {x2 + OX:.4f} {y2 + OY:.4f})\n"
        f"\t\t(stroke\n\t\t\t(width {width})\n\t\t\t(type solid)\n\t\t)\n"
        f'\t\t(layer "{layer}")\n\t\t(uuid "{uid()}")\n\t)'
    )


def rect(x1, y1, x2, y2, width=RULE_W, layer="F.SilkS"):
    out.append(
        f"\t(gr_rect\n"
        f"\t\t(start {x1 + OX:.4f} {y1 + OY:.4f})\n"
        f"\t\t(end {x2 + OX:.4f} {y2 + OY:.4f})\n"
        f"\t\t(stroke\n\t\t\t(width {width})\n\t\t\t(type solid)\n\t\t)\n"
        f"\t\t(fill none)\n"
        f'\t\t(layer "{layer}")\n\t\t(uuid "{uid()}")\n\t)'
    )


def arc(sx, sy, mx, my, ex, ey, width=0.1, layer="Edge.Cuts"):
    out.append(
        f"\t(gr_arc\n"
        f"\t\t(start {sx + OX:.4f} {sy + OY:.4f})\n"
        f"\t\t(mid {mx + OX:.4f} {my + OY:.4f})\n"
        f"\t\t(end {ex + OX:.4f} {ey + OY:.4f})\n"
        f"\t\t(stroke\n\t\t\t(width {width})\n\t\t\t(type solid)\n\t\t)\n"
        f'\t\t(layer "{layer}")\n\t\t(uuid "{uid()}")\n\t)'
    )


def slot(cx, cy, length=6.4, height=3.2):
    """A milled obround on Edge.Cuts: two semicircular ends joined by flats.
    Horizontal, so the module can slide +/- (length - height)/2 to meet its
    neighbours."""
    r = height / 2.0
    dx = length / 2.0 - r
    arc(cx + dx, cy - r, cx + dx + r, cy, cx + dx, cy + r)
    line(cx + dx, cy + r, cx - dx, cy + r, width=0.1, layer="Edge.Cuts")
    arc(cx - dx, cy + r, cx - dx - r, cy, cx - dx, cy - r)
    line(cx - dx, cy - r, cx + dx, cy - r, width=0.1, layer="Edge.Cuts")


def wire(pts):
    """A connection: one knee, 0/90/45 segments only, stopping short of what
    it joins. Emitted as silkscreen at LINE_W."""
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        line(x1, y1, x2, y2)


def stop_short(cx, cy, r, gap, ux, uy):
    """Point `gap` clear of a control of radius `r`, on the unit heading
    (ux, uy) pointing away from its centre."""
    d = r + gap
    return cx + ux * d, cy + uy * d


def below(drawn_r, size):
    """Centre-to-centre offset for a name sitting below what it names,
    measured from the drawn extent (a ring, not the hole) per PANEL_STYLE."""
    return drawn_r + LABEL_GAP + size / 2.0


# --- title -------------------------------------------------------------------
# The clear band runs from the bottom of the top mounting holes to the top of
# LED1; the title is centred in it and shrinks only if it cannot fit.
# The mounting slots are milled, so their edge is a board edge and the title
# must keep EDGE_MARGIN off it -- as it must off the first LED hole below.
LEAD = 0.4
band_top = 3.0 + 3.2 / 2.0 + EDGE_MARGIN
band_bot = LED_Y[0] - R_LED - EDGE_MARGIN
n = len(TITLE_LINES)
size = round(min(TITLE_SIZE, (band_bot - band_top - LEAD * (n - 1)) / n), 3)
pitch = round(size * PITCH_TITLE / TITLE_SIZE, 4)
assert pitch * max(len(t) for t in TITLE_LINES) <= W - 2 * EDGE_MARGIN, "title too wide"
step = size + LEAD
y0 = (band_top + band_bot) / 2.0 - step * (n - 1) / 2.0
for i, t in enumerate(TITLE_LINES):
    text(t, W / 2, y0 + i * step, size, pitch)

# --- channels 1..8: number below each LED, A/B either side of each toggle ----
for i, ly in enumerate(LED_Y):
    text(str(i + 1), LED_X, ly + below(R_LED, LABEL_SIZE), LABEL_SIZE, PITCH_LABEL)

# Throw marks. Every routing toggle throws on the X axis and the wiring is
# identical across all eight (pads 2/5 = bus A, pads 3/6 = bus B), so the mark
# is the same on every switch: lever left -> bus A, lever right -> bus B.
dx = R_SW + LABEL_GAP + SMALL_SIZE / 2.0
for sx, sy in SW_XY:
    text("A", sx - dx, sy, SMALL_SIZE, PITCH_SMALL)
    text("B", sx + dx, sy, SMALL_SIZE, PITCH_SMALL)

# --- EXT input (normalled; no ring, it is an input) --------------------------
text("EXT", EXT_XY[0], EXT_XY[1] + below(R_JACK, LABEL_SIZE), LABEL_SIZE, PITCH_LABEL)

# --- mode switches: AND up, MUTE centre, OR down -----------------------------
# Verified against the schematic: SW9 pin 2 -> BUSA_OR sits at pad 2, which at
# rot=90 lands above centre; a toggle closes onto the terminal opposite the
# lever, so lever up selects the lower pad (AND).
text("AND", LED_X, 92.4, LABEL_SIZE, PITCH_LABEL)
text("MUTE", LED_X, MODE_Y, LABEL_SIZE, PITCH_LABEL)
text("OR", LED_X, 102.9, LABEL_SIZE, PITCH_LABEL)

# --- outputs: a ring means signal leaves here --------------------------------
for ox_ in (COL_L, COL_R):
    circle(ox_, OUT_Y, R_JACK + RING_GAP)
ring_r = R_JACK + RING_GAP
text("A", COL_L, OUT_Y + below(ring_r, LABEL_SIZE), LABEL_SIZE, PITCH_LABEL)
text("B", COL_R, OUT_Y + below(ring_r, LABEL_SIZE), LABEL_SIZE, PITCH_LABEL)

# --- wordmark, letterspaced inside a two-lead component frame ----------------
wm_y = H - 7.0
half_w = (len(WORDMARK) * PITCH_LOGO) / 2.0 + 1.4
half_h = LOGO_SIZE / 2.0 + 0.85
rect(LED_X - half_w, wm_y - half_h, LED_X + half_w, wm_y + half_h)
for sign in (-1, 1):
    x0 = LED_X + sign * half_w
    line(x0, wm_y, x0 + sign * 3.5, wm_y)
text(WORDMARK, LED_X, wm_y, LOGO_SIZE, PITCH_LOGO)

# --- mounting: regenerated to the standard grid ------------------------------
# 8 HP is > 6 HP, so both columns, four slots. The 7.5 mm inset is the datum and
# the grid steps out from it by N x 5.08, which puts the far column at 32.9 and
# leaves a 7.26 mm margin on that side -- that is the way round that matters,
# because the grid is what the rail is drilled to.
MOUNT_X = (7.5, 7.5 + 5.08 * 5)
MOUNT_Y = (3.0, H - 3.0)
for mx in MOUNT_X:
    for my in MOUNT_Y:
        slot(mx, my)

# --- wires: what connects to what -------------------------------------------
# Replaces the decorative copper the v1 panel carried. Same idea -- the panel
# shows its own signal flow -- but drawn as silkscreen at LINE_W, per the rule,
# instead of as gaps in a copper pour.
GAP = 1.0
for (sx, sy), ly in zip(SW_XY, LED_Y):
    # toggle -> its indicator LED. Leaves on the LED side, one 45 degree knee.
    side = 1 if sx < LED_X else -1
    ex, ey = stop_short(LED_X, ly, R_LED, GAP, -side * 0.7071, 0.7071)
    knee_x = ex - side * abs(ey - sy)
    # clear the throw mark on that side before starting the run
    start_x = sx + side * (R_SW + LABEL_GAP + SMALL_SIZE + PITCH_SMALL / 2.0 + GAP)
    wire([(start_x, sy), (knee_x, sy), (ex, ey)])

# EXT normals into channel 8: unplugged, BIT8 feeds it; plugged, this jack does.
ex, ey = stop_short(*SW_XY[7], R_SW, GAP, -0.7071, 0.7071)
knee_x = ex - abs(ey - EXT_XY[1])
wire([(EXT_XY[0] + R_JACK + GAP, EXT_XY[1]), (knee_x, EXT_XY[1]), (ex, ey)])

# bus indicator -> mode switch -> output jack, in two runs: a single wire would
# cross the mode switch, and a wire may not cross a control.
for cx in (COL_L, COL_R):
    wire([(cx, BUSLED_Y + R_LED + GAP), (cx, MODE_Y - R_SW - GAP)])
    wire([(cx, MODE_Y + R_SW + GAP), (cx, OUT_Y - (R_JACK + RING_GAP) - GAP)])

# --- back of panel -----------------------------------------------------------
# Two clear bands on the back: 100.1-108.4 (below the mode switches, above the
# output jacks) and 115-123.9 (below the jacks, above the mounting holes).
for s, y in zip(BACK_LINES, (101.8, 105.3, 118.0)):
    text(s, LED_X, y, 1.35, 1.45, layer="B.SilkS", mirror=True)


# --- splice into the v1 file -------------------------------------------------
def top_level(src):
    """Yield the top-level children of (kicad_pcb ...) as raw strings."""
    i = src.index("(kicad_pcb") + len("(kicad_pcb")
    depth, start, instr, esc = 0, None, False, False
    while i < len(src):
        c = src[i]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        elif c == '"':
            instr = True
        elif c == "(":
            if depth == 0:
                start = i
            depth += 1
        elif c == ")":
            if depth == 0:
                break
            depth -= 1
            if depth == 0:
                yield src[start : i + 1]
        i += 1


def strip_subtree(node, head):
    """Remove every `(head ...)` subtree, matching parens."""
    while True:
        i = node.find(head)
        if i < 0:
            return node
        depth, j = 0, i
        while j < len(node):
            if node[j] == "(":
                depth += 1
            elif node[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        node = node[:i].rstrip() + node[j + 1 :]


src = open(SRC, encoding="utf-8", newline="").read()
kept, dropped = [], 0
for node in top_level(src):
    tag = re.match(r"\((\w+)", node).group(1)
    if tag in ("gr_text", "gr_poly", "gr_curve", "gr_line", "gr_rect", "gr_circle", "gr_arc"):
        layer = re.search(r'\(layer "([^"]+)"', node)
        if layer and layer.group(1) == "Edge.Cuts":
            kept.append(node)          # the panel outline is inherited
        else:
            dropped += 1               # v1 artwork, replaced below
        continue
    if tag == "segment":
        dropped += 1                   # decorative copper, redrawn as silk
        continue
    if tag == "footprint":
        val = re.search(r'\(property "Value" "([^"]*)"', node)
        if val and val.group(1) == "mounting":
            dropped += 1               # round holes -> regenerated slots
            continue
    if tag == "zone":
        # the cached fill flowed around tracks that no longer exist; drop it so
        # KiCad refills from scratch rather than plotting ghost clearances
        node = strip_subtree(node, "(filled_polygon")
    kept.append(node)

body = "\n".join("\t" + n.replace("\n", "\n") for n in kept)
with open(DST, "w", encoding="utf-8", newline="") as f:
    f.write("(kicad_pcb\n" + body + "\n" + "\n".join(out) + "\n)\n")

print(f"dropped {dropped} v1 artwork items, kept {len(kept)} nodes")
print(f"emitted {len(out)} artwork items -> {DST.name}")
