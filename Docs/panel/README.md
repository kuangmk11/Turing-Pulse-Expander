# Panel layout iterations — Pulses Plus

Open the HTML files in a browser. Both draw the panel **to scale** (1 HP = 5.08 mm, 3U = 128.5 mm).

| File | Layout | Outcome |
|---|---|---|
| `v1-two-column-grid.html` | Toggles in a 2 × 4 grid, LEDs outboard | Superseded. Needed 8–12 HP. |
| `v2-zigzag.html` | Toggles alternating left/right of a centred LED column | **Current.** Fits 6 HP. |

## What each iteration established

**v1** proved the constraint that shapes everything else: a 3U panel has ~110 mm of usable height,
and a single column of ten toggles plus three jacks needs ~160 mm. There is no single-column version
of this module — the channels have to be split across two columns somehow.

**v2** found the better way to split them. Staggering the toggles left and right of a centred LED
column means vertically adjacent toggles are never on the same side, so **row pitch no longer has to
clear a toggle nut**. That decoupling is what buys 6 HP: same-side toggles end up 17.25 mm apart —
more finger room than v1's 10 HP grid had — in half the width.

With the bus outputs moved to the bottom (jacks at the very bottom, vertical-throw mode toggles
above them, bus LEDs above those), the channel zigzag stretches to fill the panel at an 8.625 mm row
pitch. That pitch isn't chosen — it's back-solved from landing the EXT jack one full zigzag step
below channel 8 while still clearing the bus LEDs.

Each channel LED rides 2.5 mm above its toggle's row with the channel number silkscreened directly
beneath it, which is what makes the alternation readable at a glance.

## The remaining constraint is horizontal, and the nut decides it

Switch selected: **Adam Tech SW-T2-4X-E-A2-MA2** — DPDT ON-OFF-ON, M6 × 0.75 bushing, PCB vertical.
DPDT is an electrical requirement, not a preference; a single-pole switch leaks the AND bus into the
OR bus through the unselected throw (see the topology note in
[`../pulses-plus-design.md`](../pulses-plus-design.md)).

That's a *miniature* bushing, not sub-miniature, so at 6 HP there is only **1.6 mm of panel between
each toggle nut and its LED hole** — buildable, but only with bare 3 mm LEDs in bare holes, no bezels
or holders. Behind the panel, the 13.2 mm body against a 14.5 mm column pitch leaves 1.3 mm between
adjacent switch bodies. Tight, but it clears.

**Panel gets the ø6.00 mm bushing hole only — no anti-rotation key hole.** Adam Tech's recommended
cut-out puts a ø2.40 mm key hole 6.40 mm from the bushing centre, which would overlap the channel
LED hole outright. The six solder pins prevent rotation once the switch is PCB-mounted, so the key
hole is unnecessary. Don't copy the datasheet cut-out into the panel DXF.

**The nut turned out not to be a gate — 6 HP works.** Worst plausible M6 toggle nut (11 mm across
corners) still clears the LED hole by 0.52 mm; a typical 9.2 mm nut clears by 1.42 mm. It never
overlaps. So the nut only decides how tight the panel *looks*, and whether an LED bezel is possible
(it isn't). 6 HP vs 8 HP is now a rack-space call, not an engineering one — 8 HP takes that gap to
6.3 mm and leaves room for real legends.

## The panel as a PCB

`../build_panel.py` generates the panel as a standalone board — holes and silkscreen only, no
components — to `../../Hardware/pulses_plus/pulses_plus_panel_{6,8}hp.kicad_pcb`. Switches and jacks
mount on the main board behind and their own nuts hold the panel on. Artwork is on F.SilkS with the
F side facing the player.

Toggle columns are pinned to the panel **edge** rather than the centreline, so extra HP goes into the
toggle-to-LED gap — the only place it's needed.
