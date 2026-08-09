"""Place the panel-facing components on the main board at the panel hole coordinates.

The main PCB sits behind the panel with its F side facing the player, so panel (x, y)
and board (x, y) are the same frame -- no mirroring.

Only the parts that must line up with panel holes are placed here: the 10 toggles, the
3 jacks and the 10 LEDs. Everything else (ICs, passives, ribbon headers) is left for
hand placement.

Includes a MECHANICAL clearance check on component bodies. This is the check that a
PCB DRC does not do and that killed 6 HP: the toggle bushing is only 6 mm, but its
BODY is 13.2 mm, and the centreline LED has to live between two of them.
"""
import os, sys, math, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ksym import tokenize, parse, find_all

from panel_geom import (HP, W, H, CX, SWL, SWR, ROWS, LED_RISE, EXT_Y,
                        BUS_LED_Y, BUS_SW_Y, BUS_JACK_Y, BOARD_TOP, BOARD_BOT)

PRETTY = "/mnt/g/Documents/GitHub/Turing-Pulse-Expander/Hardware/pulses_plus/pulses_plus.pretty"
OUT = "/mnt/g/Documents/GitHub/Turing-Pulse-Expander/Hardware/pulses_plus/pulses_plus.kicad_pcb"

U = lambda: str(uuid.uuid4())
f = lambda v: ("%.4f" % v).rstrip("0").rstrip(".")

BX0, BY0, BX1, BY1 = 0.5, BOARD_TOP, W - 0.5, BOARD_BOT


from kfp import fp_bbox


BB = {n: fp_bbox(n) for n in ("SW_T2_4X_DPDT", "Thonkiconn_PJ301M", "LED_3mm")}
print("library footprint extents (mm, rotation 0):")
for n, (x0, y0, x1, y1) in BB.items():
    print(f"  {n:20} {x1-x0:6.2f} x {y1-y0:6.2f}")

# ---- placement --------------------------------------------------------------
place = []   # (ref, fp, x, y, rot)
for i, y in enumerate(ROWS):
    place.append((f"SW{i+1}", "SW_T2_4X_DPDT", SWL if i % 2 == 0 else SWR, y, 0))
    place.append((f"LED{i+1}", "LED_3mm", CX, y - LED_RISE, 0))
place.append(("J3", "Thonkiconn_PJ301M", SWL, EXT_Y, 0))
for sx, bus, n in ((SWL, "A", 9), (SWR, "B", 10)):
    place.append((f"LED{n}", "LED_3mm", sx, BUS_LED_Y, 0))
    place.append((f"SW{n}", "SW_T2_4X_DPDT", sx, BUS_SW_Y, 90))   # vertical throw
    place.append((f"J{n-5}", "Thonkiconn_PJ301M", sx, BUS_JACK_Y, 0))  # J4, J5

# ---- mechanical check -------------------------------------------------------
def rect(ref, fp, x, y, rot):
    x0, y0, x1, y1 = BB[fp]
    if rot % 180:                       # 90 deg: swap the extents
        x0, y0, x1, y1 = y0, x0, y1, x1
    return (ref, x + x0, y + y0, x + x1, y + y1)

boxes = [rect(*p) for p in place]
worst = []
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        r1, a0, b0, a1, b1 = boxes[i]
        r2, c0, d0, c1, d1 = boxes[j]
        dx = max(c0 - a1, a0 - c1)      # >0 = separated in x
        dy = max(d0 - b1, b0 - d1)
        if dx < 0 and dy < 0:
            worst.append((min(-dx, -dy), r1, r2, "OVERLAP"))
        else:
            worst.append((max(dx, dy), r1, r2, "clear"))
worst.sort()
print("\ntightest body-to-body clearances:")
for gap, r1, r2, state in worst[:6]:
    flag = "  *** OVERLAP ***" if state == "OVERLAP" else ""
    print(f"  {r1:>5} <-> {r2:<5} {gap:6.2f} mm{flag}")

off = [(r, x0, y0, x1, y1) for r, x0, y0, x1, y1 in boxes
       if x0 < BX0 or y0 < BY0 or x1 > BX1 or y1 > BY1]
print(f"\nboard outline: {f(BX0)},{f(BY0)} -> {f(BX1)},{f(BY1)}  "
      f"({f(BX1-BX0)} x {f(BY1-BY0)} mm)")
print("  parts outside the outline:", ", ".join(r[0] for r in off) if off else "none")

if any(s == "OVERLAP" for _, _, _, s in worst):
    sys.exit("\nREFUSING TO WRITE: bodies overlap.")

# ---- emit -------------------------------------------------------------------
LAYERS = """	(layers
		(0 "F.Cu" signal)
		(2 "B.Cu" signal)
		(9 "F.Adhes" user "F.Adhesive")
		(11 "B.Adhes" user "B.Adhesive")
		(13 "F.Paste" user)
		(15 "B.Paste" user)
		(5 "F.SilkS" user "F.Silkscreen")
		(7 "B.SilkS" user "B.Silkscreen")
		(1 "F.Mask" user)
		(3 "B.Mask" user)
		(17 "Dwgs.User" user "User.Drawings")
		(19 "Cmts.User" user "User.Comments")
		(21 "Eco1.User" user "User.Eco1")
		(23 "Eco2.User" user "User.Eco2")
		(25 "Edge.Cuts" user)
		(27 "Margin" user)
		(31 "F.CrtYd" user "F.Courtyard")
		(29 "B.CrtYd" user "B.Courtyard")
		(35 "F.Fab" user)
		(33 "B.Fab" user)
	)"""

parts = [f'''(kicad_pcb
	(version 20260206)
	(generator "pcbnew")
	(generator_version "10.0")
	(general (thickness 1.6) (legacy_teardrops no))
	(paper "A4")
{LAYERS}
	(setup (pad_to_mask_clearance 0))
	(net 0 "")''']

for (x1, y1), (x2, y2) in (((BX0, BY0), (BX1, BY0)), ((BX1, BY0), (BX1, BY1)),
                           ((BX1, BY1), (BX0, BY1)), ((BX0, BY1), (BX0, BY0))):
    parts.append(f'''	(gr_line
		(start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)})
		(stroke (width 0.1) (type default))
		(layer "Edge.Cuts") (uuid {U()})
	)''')

for ref, fp, x, y, rot in place:
    body = open(os.path.join(PRETTY, fp + ".kicad_mod"), encoding="utf8").read()
    inner = body.strip()[body.strip().index("\n"):].rstrip()[:-1].rstrip()  # drop header + trailing )
    inner = "\n".join("\t" + ln for ln in inner.splitlines())
    parts.append(f'''	(footprint "pulses_plus:{fp}"
		(layer "F.Cu")
		(uuid {U()})
		(at {f(x)} {f(y)} {rot})
		(property "Reference" "{ref}" (at 0 -8 {rot}) (layer "F.SilkS")
			(uuid {U()}) (effects (font (size 1 1) (thickness 0.15)))
		)
		(property "Value" "{fp}" (at 0 8 {rot}) (layer "F.Fab") (hide yes)
			(uuid {U()}) (effects (font (size 1 1) (thickness 0.15)))
		)
{inner}
	)''')

parts.append(")")
open(OUT, "w", encoding="utf8").write("\n".join(parts) + "\n")
print(f"\nwrote {OUT}\n  {len(place)} footprints placed "
      f"({sum(1 for p in place if p[1].startswith('SW'))} switches, "
      f"{sum(1 for p in place if 'Thonk' in p[1])} jacks, "
      f"{sum(1 for p in place if 'LED' in p[1])} LEDs)")
