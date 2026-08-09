"""Generate the Pulses Plus front panel as a standalone PCB (holes + silkscreen).

The panel carries no components: the switches and jacks are PCB-mounted on the main
board behind it and their bushings pass through these holes, so the panel is held on
by their own nuts. Artwork is on the F side, which faces the player.

Geometry is the v2 zigzag layout from Docs/panel/v2-zigzag.html.
Run with an HP argument to retarget:  python3 build_panel.py 8
"""
import sys, uuid, math

from panel_geom import (HP, W, H, CX, SWL, SWR, ROWS, LED_RISE, EXT_Y,
                        BUS_LED_Y, BUS_SW_Y, BUS_JACK_Y, D_BUSH, D_JACK, D_LED,
                        D_MNT, MNT_INSET, MNT_EDGE, LED_TO_BODY)

OUT = ("/mnt/g/Documents/GitHub/Turing-Pulse-Expander/Hardware/pulses_plus/"
       "pulses_plus_panel.kicad_pcb")


def confirm(target):
    """This generator overwrites the whole file. Hand edits in the target are lost."""
    import os, sys
    if not os.path.exists(target):
        return
    print(f"!! {target}")
    print("!! already exists and will be OVERWRITTEN. Any hand edits to it will be lost.")
    if input("Type 'yes' to overwrite: ").strip().lower() != "yes":
        sys.exit("aborted - nothing written")


confirm(OUT)

U = lambda: str(uuid.uuid4())
f = lambda v: ("%.4f" % v).rstrip("0").rstrip(".")

holes = []   # (x, y, dia, tag)
silk = []    # (x, y, text, size, thickness)

for i, y in enumerate(ROWS):
    sx = SWL if i % 2 == 0 else SWR
    holes.append((sx, y, D_BUSH, f"SW{i+1} bushing"))
    holes.append((CX, y - LED_RISE, D_LED, f"LED{i+1}"))
    silk.append((CX, y + 3.3, str(i + 1), 1.6, 0.25))

holes.append((SWL, EXT_Y, D_JACK, "J3 EXT jack"))
silk.append((CX + 2.6, EXT_Y + 0.6, "EXT", 1.3, 0.22))

for sx, bus in ((SWL, "A"), (SWR, "B")):
    holes.append((sx, BUS_LED_Y, D_LED, f"LED bus {bus}"))
    holes.append((sx, BUS_SW_Y, D_BUSH, f"SW mode {bus}"))
    holes.append((sx, BUS_JACK_Y, D_JACK, f"OUT {bus} jack"))
    silk.append((sx, BUS_SW_Y - 4.4, "OR", 1.1, 0.2))
    silk.append((sx, BUS_SW_Y + 5.2, "AND", 1.1, 0.2))
    silk.append((sx, BUS_JACK_Y + 6.4, bus, 1.8, 0.28))

silk.append((CX, BUS_SW_Y, "MUTE", 0.9, 0.16))      # centre detent, on the centreline
silk.append((CX, 122.0, "PULSES +", 2.0, 0.3))

for mx in (MNT_INSET, W - MNT_INSET):
    for my in (MNT_EDGE, H - MNT_EDGE):
        holes.append((mx, my, D_MNT, "mounting"))

# ---------------------------------------------------------------- checks ----
# (a) hole-to-hole: what the fab cares about
worst = None
for i in range(len(holes)):
    for j in range(i + 1, len(holes)):
        x1, y1, d1, t1 = holes[i]
        x2, y2, d2, t2 = holes[j]
        gap = math.hypot(x2 - x1, y2 - y1) - d1 / 2 - d2 / 2
        if worst is None or gap < worst[0]:
            worst = (gap, t1, t2)
edge = min(min(x - d / 2, W - x - d / 2, y - d / 2, H - y - d / 2)
           for x, y, d, _ in holes)

# (b) nut-to-LED: what assembly cares about. The nut is a washer sitting ON the
# panel, so it doesn't show up in any DRC -- it can quietly overlap the LED.
sw_to_led = math.hypot(CX - SWL, LED_RISE)
def nut_gap(ac):
    return sw_to_led - ac / 2 - D_LED / 2

# ------------------------------------------------------------------ emit ----
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
	(general
		(thickness 1.6)
		(legacy_teardrops no)
	)
	(paper "A4")
{LAYERS}
	(setup
		(pad_to_mask_clearance 0)
		(allow_soldermask_bridges_in_footprints no)
	)''']

# board outline
for (x1, y1), (x2, y2) in (((0, 0), (W, 0)), ((W, 0), (W, H)),
                           ((W, H), (0, H)), ((0, H), (0, 0))):
    parts.append(f'''	(gr_line
		(start {f(x1)} {f(y1)})
		(end {f(x2)} {f(y2)})
		(stroke (width 0.1) (type default))
		(layer "Edge.Cuts")
		(uuid {U()})
	)''')

# holes as self-contained NPTH footprints (no library dependency)
for x, y, d, tag in holes:
    parts.append(f'''	(footprint "Panel:Hole_{f(d)}mm"
		(layer "F.Cu")
		(uuid {U()})
		(at {f(x)} {f(y)})
		(descr "{tag}")
		(attr exclude_from_pos_files exclude_from_bom allow_missing_courtyard)
		(property "Reference" "" (at 0 0 0) (layer "F.SilkS") (hide yes)
			(uuid {U()}) (effects (font (size 1 1) (thickness 0.15)))
		)
		(property "Value" "{tag}" (at 0 0 0) (layer "F.Fab") (hide yes)
			(uuid {U()}) (effects (font (size 1 1) (thickness 0.15)))
		)
		(pad "" np_thru_hole circle
			(at 0 0)
			(size {f(d)} {f(d)})
			(drill {f(d)})
			(layers "F&B.Cu" "F&B.Mask")
			(uuid {U()})
		)
	)''')

for x, y, text, size, th in silk:
    parts.append(f'''	(gr_text "{text}"
		(at {f(x)} {f(y)} 0)
		(layer "F.SilkS")
		(uuid {U()})
		(effects
			(font (size {f(size)} {f(size)}) (thickness {f(th)}))
		)
	)''')

parts.append(")")
open(OUT, "w", encoding="utf8").write("\n".join(parts) + "\n")

kinds = {}
for _, _, _, tag in holes:
    k = ("bushing" if "bushing" in tag or "mode" in tag else
         "jack" if "jack" in tag else "LED" if "LED" in tag else "M3")
    kinds[k] = kinds.get(k, 0) + 1

print(f"wrote {OUT}")
print(f"  {HP} HP -> {f(W)} x {H} mm | {len(holes)} holes, {len(silk)} silk items")
print(f"  " + "  ".join(f"{k} x{v}" for k, v in sorted(kinds.items())))
print(f"  toggle columns at x = {f(SWL)} / {f(SWR)}, LEDs on centreline x = {f(CX)}")
print()
print(f"  FAB    tightest hole-to-hole: {worst[0]:5.2f} mm  ({worst[1]} <-> {worst[2]})")
print(f"         tightest hole-to-edge: {edge:5.2f} mm")
print(f"  ASSY   toggle centre to LED centre: {sw_to_led:.2f} mm")
print(f"  ASSY   centreline LED to toggle BODY: {LED_TO_BODY:5.2f} mm"
      f"   (-0.90 at 6 HP -- the collision that killed it)")
