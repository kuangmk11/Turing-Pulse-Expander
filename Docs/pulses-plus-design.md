# Pulses Plus — circuit design and netlist

A performance-oriented gate router for the Music Thing Turing Machine. Eight pulse channels, each
switchable to one of two merge buses (or off); each bus computes OR or AND of whatever is routed to
it, selected live from the panel.

It sits **alongside** a stock Pulses expander rather than replacing it, taking its signals from the
Turing Machine's 16-pin expander ribbon and passing that ribbon through so other expanders can still
be chained downstream.

**Target: 8 HP.** (6 HP was pursued for a long time and is dead — see
[Why not 6 HP](#why-not-6-hp).) Panel study: [`Docs/panel/`](panel/).

| File | What it is |
|---|---|
| `Hardware/pulses_plus/pulses_plus.kicad_sch` | schematic — generated, complete |
| `Hardware/pulses_plus/pulses_plus.kicad_pcb` | main board — panel-facing parts placed, rest to do |
| `Hardware/pulses_plus/pulses_plus_panel.kicad_pcb` | front panel — holes + silkscreen |
| `Hardware/pulses_plus/pulses_plus.pretty/` | project footprints (toggle, jack, LED) |
| `Docs/panel_geom.py` | **single source of truth for all panel/board geometry** |

---

## Why this exists

The stock Pulses gives you seven fixed pulse outputs plus four hard-wired AND combinations
(1&2, 2&4, 4&7, 1&2&4&7). Those AND outputs are the musical ones — ANDing two shift-register taps
doesn't produce a rare coincidence, it produces a **thinned, loop-locked rhythm**, because the
register stages are one sequence read at eight different delays, not eight independent random bits.
Which pair you pick changes the pattern; that choice is what you want on a switch, not on a
patch cable.

This module generalises that: any subset of the eight bits, OR'd or AND'd, chosen by hand, live.
The four fixed AND outputs on the stock board become a strict subset of what the switches can do,
so no CD4081 is needed here.

---

## Signal chain

```
TM ribbon ──┬─→ [CD4050 buffers] ──→ P1..P7 ──┬─→ channel LED (4k7)
            │                                  │
            │   BIT8 ──→ [buffer] ──→ P8N ──→ [EXT jack normal] ──→ [Q1 + Schmitt] ──→ P8
            │
            └─→ chain-through header (all 16 pins in parallel)

P1..P8 ──→ [DPDT on-off-on] ──┬─ pole 1 (OR)  ──→ diode ──→ BUS_x_OR   (10k pulldown)
                              └─ pole 2 (AND) ←── diode ←── BUS_x_AND  (10k pullup)

BUS_x_OR ──┐
           ├─→ [SPDT mode switch] ──→ [2× CD40106] ──→ 1k ──→ jack + LED
BUS_x_AND ─┘
```

### Input buffering (why it isn't optional)

Each `BITn` line on the ribbon already drives, on the stock Pulses board, a 2k LED string (~5 mA)
plus a 1k series resistor into a jack. Hanging this module's LEDs and diode network on the same
lines in parallel would roughly double that load and sag the logic highs.

So every bit is buffered on entry by a **CD4050** (non-inverting, happy at +12 V). The ribbon sees
one CMOS input per line; all LEDs and diode current are drawn from the buffer outputs. Side benefit:
every channel now presents the same source impedance to the merge network.

### The diode merge network

Gates need *logical* combination, not voltage addition — two resistor-limited CMOS outputs fighting
over a shared node settle at some mid-rail voltage rather than a clean high or low. So each bus is a
diode network:

| Net | Diode orientation | Pull | Result |
|---|---|---|---|
| `BUS_x_OR` | anode at channel, cathode at bus | 10k **down** to GND | high if **any** routed channel is high |
| `BUS_x_AND` | anode at bus, cathode at channel | 10k **up** to +12 V | high only if **every** routed channel is high |

Both nets are computed continuously and in parallel for both buses. The mode switch sits downstream
and simply picks which net feeds the output buffer, so the 32 merge diodes never switch — only the
selection does.

Levels, with 1N4148 (Vf ≈ 0.7 V) into a CD40106 Schmitt (VT+ ≈ 6.8 V, VT- ≈ 4.5 V at 12 V):

- OR bus, routed channel high: 11.5 − 0.7 = **10.8 V** → comfortably HIGH
- AND bus, routed channel low: 0.1 + 0.7 = **0.8 V** → comfortably LOW

Both have over 3 V of margin, so **Schottky diodes buy nothing here** — plain 1N4148 is fine.

### ⚠ Why the switches must be DPDT, not SPDT

This is the one non-obvious constraint in the whole design, and it is easy to get wrong.

The tempting layout is a single-pole on-off-on switch whose two throws each carry a *pair* of
diodes — one into that bus's OR net, one out of its AND net. **This does not work.** When a channel
is routed to Bus A, its Bus B throw is left floating, and that floating node is connected to *both*
of Bus B's diodes. That completes a DC path straight through the merge network:

```
+12V ── 10k pullup ── [BUS_B_AND] ──▶|── (floating throw) ──▶|── [BUS_B_OR] ── 10k pulldown ── GND
```

Both diodes are forward-biased. The result is a permanent 0.53 mA leakage and **Bus B's OR net
sitting at 5.3 V** — right between the Schmitt thresholds, so the bus is not reliably low. Every
unrouted channel does this, and turning the switch to centre-off doesn't help; it makes it worse by
floating *both* throws.

The fix is to **give the OR and AND networks their own pole**:

- **Pole 1** carries only the OR diodes (throw → anode → bus)
- **Pole 2** carries only the AND diodes (bus → anode → cathode → throw)
- Both poles' commons tie to the same channel signal `Pn`

Now an unselected OR-throw touches only a diode *anode* with nothing to source current into it, so
the bus pulldown wins and the net sits at 0 V. An unselected AND-throw touches only a diode
*cathode*, so it charges to `VDD − Vf` and current stops. There is no path from the AND pullup to
the OR pulldown, and both buses stay clean.

**Required part: DPDT (2-pole) ON-OFF-ON toggle.** Same panel footprint, six pins instead of three.

### Channel 8 and the EXT jack

`BIT8` exists on the ribbon — confirmed against `Hardware/pulses_rev2.sch`, where header pin 8
carries `BIT8` and connects to nothing. The stock Pulses simply never jacks it out. Normalling it
into channel 8 is therefore a legitimate move, not a hack.

The EXT jack is a **switched** (normalled) mono jack. Unplugged, its break contact hands the
buffered `P8N` through to channel 8, so channel 8 is a genuine 8th Turing Machine bit doing real
work. Plug something in and the contact opens, handing channel 8 to whatever you patched.

That makes EXT the one input whose amplitude is unknown, and **the merge network only works if every
channel swings near the rails**. A 5 V gate arriving through a diode drop would not reliably register.
So channel 8 gets a conditioning front end:

```
EXT tip ──[10k]──┬── Q1 base (2N3904)          Q1 collector ──[10k pullup to +12V]── CD40106 ──→ P8
                 ├── [22k] ── GND                    (inverts)                       (re-inverts)
                 └── [1N4148 cathode] ── GND   (clamps negative inputs at −0.7 V)
```

Threshold lands around 1.2 V, so anything from a 3.3 V logic pulse to a 12 V CMOS gate reads
correctly; the 10k base resistor limits current for anything larger, and the clamp diode handles
bipolar sources. The Schmitt gate squares the result.

> **This replaces the LM393 comparator** from the earlier design sketch. The LM393 is
> *open-collector* (KiCad's own symbol marks pins 1 and 7 as such), so it needs a pullup nobody had
> budgeted; worse, its input common-mode range tops out at V+ − 2 V = 10 V, so a 12 V CMOS pulse
> driven straight into it is **out of spec** and would need a divider and a reference on top. The
> transistor front end is one part, has no common-mode limit, needs no reference, and costs one
> spare Schmitt gate we already have.

### Output stage

Per bus: mode switch selects the OR or the AND net → two cascaded CD40106 Schmitt inverters
(double inversion = non-inverting buffer, squared edges, restored rail-to-rail swing) → 1k series
resistor → output jack, with an LED off the same node through 4k7.

A 1M pulldown (R15/R16) on each mode-switch common defines the node during the switch's
make-before-break gap.

**The mode switch is the same DPDT ON-OFF-ON part as the routing switches**, which makes the whole
panel one part number and one footprint — and gives the centre position away for free. With the
common floating, R15/R16 hold the Schmitt input low, so the output goes silent:

> **OR / MUTE / AND** — centre-off mutes the bus.

Only pole 1 is used; pole 2 is left unconnected.

**Known quirk:** AND of zero terms is vacuously true. A bus in AND mode with nothing routed to it
sits high (DC). Harmless, but don't be surprised by it — and the mute position is right there.

---

## Gate and buffer budget

| IC | Used | Spare |
|---|---|---|
| U1 CD4050 | 6 buffers — BIT1..BIT6 | — |
| U2 CD4050 | 2 buffers — BIT7, BIT8 | 4 (tie inputs to GND) |
| U3 CD40106 | 5 gates — 2× Bus A, 2× Bus B, 1× channel 8 | 1 (tie input to GND) |

CLOCK is present on ribbon pins 9/10 and is passed through to the chain header. It is *not* used,
but a spare U2 buffer and the spare U3 gate mean a clock-as-9th-channel feature could be added later
without another IC.

---

## Netlist

Power comes from the ribbon: **+12 V on pins 15/16, GND on 13/14, −12 V on 11/12** (−12 V is
pass-through only; nothing on this board uses it).

### Connectors

| Ref | Part | Pin | Net |
|---|---|---|---|
| J1 | Conn_02x08_Odd_Even (PULSES IN) | 1–8 | BIT1 … BIT8 |
| | | 9, 10 | CLOCK |
| | | 11, 12 | −12V |
| | | 13, 14 | GND |
| | | 15, 16 | +12V |
| J2 | Conn_02x08_Odd_Even (CHAIN THRU) | 1–16 | *identical to J1, wired in parallel* |
| J3 | AudioJack2_SwitchT (EXT) | T | CH8_IN |
| | | TN | P8N |
| | | S | GND |
| J4 | AudioJack2 (OUT A) | T | OUTA_JACK |
| | | S | GND |
| J5 | AudioJack2 (OUT B) | T | OUTB_JACK |
| | | S | GND |

### Input buffers

| Ref | Pin | Net | | Ref | Pin | Net |
|---|---|---|---|---|---|---|
| U1 (4050) | 3 → 2 | BIT1 → P1 | | U2 (4050) | 3 → 2 | BIT7 → P7 |
| | 5 → 4 | BIT2 → P2 | | | 5 → 4 | BIT8 → P8N |
| | 7 → 6 | BIT3 → P3 | | | 7, 9, 11, 14 | GND *(unused inputs)* |
| | 9 → 10 | BIT4 → P4 | | | 6, 10, 12, 15 | *(no connect)* |
| | 11 → 12 | BIT5 → P5 | | | 1 | +12V |
| | 14 → 15 | BIT6 → P6 | | | 8 | GND |
| | 1 | +12V | | | | |
| | 8 | GND | | | | |

### Channel 8 conditioning

| Ref | Value | From | To |
|---|---|---|---|
| R19 | 10k | CH8_IN | Q1.B |
| R20 | 22k | Q1.B | GND |
| D33 | 1N4148 | cathode Q1.B | anode GND |
| Q1 | 2N3904 | E → GND | C → CH8_COL |
| R21 | 10k | CH8_COL | +12V |
| U3 gate F | 40106 | in 13 = CH8_COL | out 12 = **P8** |

### Routing switches (SW1 … SW8 — DPDT ON-OFF-ON)

For channel *n* ∈ 1…8, with `Pn` the buffered channel signal:

| Pin | Net |
|---|---|
| Pole 1 common | Pn |
| Pole 1 throw A | ORA_n |
| Pole 1 throw B | ORB_n |
| Pole 2 common | Pn |
| Pole 2 throw A | ANDA_n |
| Pole 2 throw B | ANDB_n |

### Merge diodes (D1 … D32, 1N4148)

For channel *n*, diodes `D(4n−3)` … `D(4n)`:

| Diode | Anode | Cathode | Net function |
|---|---|---|---|
| D(4n−3) | ORA_n | BUSA_OR | channel *n* → Bus A, OR |
| D(4n−2) | BUSA_AND | ANDA_n | channel *n* → Bus A, AND |
| D(4n−1) | ORB_n | BUSB_OR | channel *n* → Bus B, OR |
| D(4n) | BUSB_AND | ANDB_n | channel *n* → Bus B, AND |

So D1–D4 are channel 1, D5–D8 channel 2, … D29–D32 channel 8.

### Bus pulls, mode switches, output stage

| Ref | Value | From | To |
|---|---|---|---|
| R11 | 10k | BUSA_OR | GND |
| R12 | 10k | BUSA_AND | +12V |
| R13 | 10k | BUSB_OR | GND |
| R14 | 10k | BUSB_AND | +12V |
| SW9 | DPDT ON-OFF-ON | 1 = BUSA_SEL | 2 = BUSA_OR, 3 = BUSA_AND (pole 2: 4/5/6 n/c) |
| SW10 | DPDT ON-OFF-ON | 1 = BUSB_SEL | 2 = BUSB_OR, 3 = BUSB_AND (pole 2: 4/5/6 n/c) |
| R15 | 1M | BUSA_SEL | GND |
| R16 | 1M | BUSB_SEL | GND |
| U3 gate A | 40106 | in 1 = BUSA_SEL | out 2 = BUSA_N |
| U3 gate B | 40106 | in 3 = BUSA_N | out 4 = **BUSA_OUT** |
| U3 gate C | 40106 | in 5 = BUSB_SEL | out 6 = BUSB_N |
| U3 gate D | 40106 | in 9 = BUSB_N | out 8 = **BUSB_OUT** |
| U3 gate E | 40106 | in 11 = GND | out 10 = *(spare, no connect)* |
| U3 | — | 7 = GND | 14 = +12V |
| R17 | 1k | BUSA_OUT | OUTA_JACK |
| R18 | 1k | BUSB_OUT | OUTB_JACK |

### LEDs

| Ref | Anode from | Resistor | To |
|---|---|---|---|
| LED1 … LED8 | P1 … P8 | R1 … R8, 4k7 | GND |
| LED9 | BUSA_OUT | R9, 4k7 | GND |
| LED10 | BUSB_OUT | R10, 4k7 | GND |

Channel LEDs tap **pre-switch**, so each always shows that channel firing regardless of routing.
4k7 (≈ 2 mA) rather than the stock board's 2k, because a CD4050 output has limited drive at 12 V and
is also feeding the merge diodes — use modern high-brightness LEDs.

### Decoupling

| Ref | Value | Across |
|---|---|---|
| C1, C2, C3 | 100n | U1, U2, U3 VDD → GND |
| C4 | 10µ | +12V → GND (bulk) |

---

## Bill of materials

| Qty | Part | Ref | Notes |
|---|---|---|---|
| 2 | CD4050 hex non-inverting buffer | U1, U2 | input buffering, 8 of 12 used |
| 1 | CD40106 hex Schmitt inverter | U3 | output buffers + ch8, 5 of 6 used |
| 1 | 2N3904 NPN | Q1 | EXT input conditioning |
| 33 | 1N4148 | D1–D33 | 32 merge + 1 EXT clamp |
| 10 | **Adam Tech SW-T2-4X-E-A2-MA2** | SW1–SW10 | DPDT **ON-OFF-ON**, PCB vertical. ⚠ 2-pole is an electrical requirement — see topology note. SW9/SW10 use pole 1 only. |
| 10 | 3 mm LED | LED1–LED10 | high-brightness |
| 2 | 16-pin 2×8 IDC header | J1, J2 | in + chain-through |
| 1 | Switched mono 3.5 mm jack | J3 | EXT — **must** have break contact |
| 2 | Mono 3.5 mm jack | J4, J5 | OUT A / OUT B |
| 10 | 4k7 | R1–R10 | LED |
| 4 | 10k | R11–R14 | bus pulls |
| 2 | 1M | R15, R16 | mode-switch common pulldowns |
| 2 | 1k | R17, R18 | output series |
| 2 | 10k | R19, R21 | EXT base + collector |
| 1 | 22k | R20 | EXT threshold |
| 3 | 100n | C1–C3 | decoupling |
| 1 | 10µ | C4 | bulk |

Estimated current draw from the ribbon's +12 V: ~30 mA (10 LEDs at ~2 mA, four bus pull resistors at
~1.2 mA, ICs a few mA).

## KiCad symbols (verified against KiCad 10 libraries)

| Part | `lib_id` |
|---|---|
| Hex buffer | `4xxx:4050` |
| Hex Schmitt inverter | `4xxx:40106` |
| NPN | `Transistor_BJT:2N3904` |
| Diode | `Diode:1N4148` |
| Routing + mode switch | `Switch:SW_DPDT_x2` |
| Ribbon headers | `Connector_Generic:Conn_02x08_Odd_Even` |
| EXT jack | `Connector_Audio:AudioJack2_SwitchT` |
| Output jacks | `Connector_Audio:AudioJack2` |

Pin numbering used above is taken from these symbols. `SW_DPDT_x2` numbers pole 1 as A=1, B=2, C=3
and pole 2 as A=4, B=5, C=6, with A the common pole.

The schematic is generated by [`build_sch.py`](build_sch.py) (with [`ksym.py`](ksym.py)), which reads
the symbol definitions straight out of the KiCad libraries so pin numbers and geometry can't drift
from the netlist above. Re-run it to regenerate `Hardware/pulses_plus/pulses_plus.kicad_sch`.
Connectivity is made with net labels on pin stubs rather than routed wires — electrically complete,
but the layout wants tidying by hand.

---

## Mechanical notes (Adam Tech SW-T2-4X-E)

Datasheet: [`sw-t2-4x-b-a2-ma2-data-sheet.pdf`](sw-t2-4x-b-a2-ma2-data-sheet.pdf) (the `-B-` sheet
documents the ON-ON variant; `-E-` is the ON-OFF-ON member of the same family — identical body,
bushing and footprint).

| | |
|---|---|
| Bushing | M6 × 0.75 → **ø6.00 mm panel hole** |
| Body | 13.2 mm along the throw axis × 11.7 mm × 10.6 mm deep |
| Pins | 2 rows × 3, **4.70 mm** within a row, **4.80 mm** between rows; 0.80 × 1.20 mm |
| Mounting | PCB vertical — board sits parallel to the front panel |
| Life | 10 000 cycles (rated at 3 A; effectively far more at signal level) |

**Do not drill the anti-rotation key hole.** Adam Tech's recommended cut-out adds a ø2.40 mm hole
6.40 mm from the bushing centre. Our channel LED sits 7.66 mm from the switch centre with a 1.5 mm
radius, so that key hole's outer edge (7.60 mm) would **overlap the LED hole** (inner edge 6.16 mm)
by about 1.4 mm — one hole drilled into the other. It isn't needed: the six solder pins hold the
switch against rotation once it's PCB-mounted. Panel gets the ø6.00 mm hole only.

Rotated 90° for horizontal throw, the 13.2 mm body against the 6 HP column pitch of 14.5 mm leaves
**1.3 mm between adjacent switch bodies** behind the panel. Same-column switches are 17.25 mm apart
against an 11.7 mm body — 5.5 mm clear.

---

## The panel PCB

> ⚠ **The panel boards are hand-maintained from here on. Do not re-run `build_panel.py` over them.**
> It was scaffolding to get the hole pattern placed, and it has done that job. The committed
> `.kicad_pcb` files are now the source of truth — they carry hand corrections to the mounting holes
> and the silkscreen that the generator does not know about and will overwrite without warning.
> If the hole *pattern* ever needs to change, port the change into the board by hand, or fix the
> generator first and re-apply the hand edits deliberately.

Originally generated by [`build_panel.py`](build_panel.py) →
`Hardware/pulses_plus/pulses_plus_panel_6hp.kicad_pcb` (an 8 HP version sits alongside it).

The panel carries **no components**. The switches and jacks are PCB-mounted on the main board behind
it; their bushings pass through and their own nuts hold the panel on. Artwork is on **F.SilkS**, and
the F side faces the player — no mirroring.

| Hole | ø | Count |
|---|---|---|
| Toggle bushing (M6 × 0.75) | 6.00 mm | 10 |
| Jack (Thonkiconn / PJ301M-12) | 6.00 mm | 3 |
| LED (3 mm, with fit clearance) | 3.20 mm | 10 |
| Panel screw (M3) | 3.20 mm | 4 |

**Toggle columns are pinned to the panel edge, not to the centreline** — the nut sits 3.2 mm clear of
the edge — so extra HP goes into the toggle-to-LED gap, which is the only place it's needed.

Clearances at 8 HP (40.16 × 128.5 mm):

- tightest hole-to-hole: **4.80 mm** — comfortable for any fab
- tightest hole-to-edge: 1.40 mm (at the M3 holes)
- centreline LED to toggle **body**: **3.40 mm** (this was −0.90 mm at 6 HP)

**The mounting holes as generated are not to spec** — ø3.2 mm round holes, 7.5 mm in from each side
edge, 3.0 mm from top and bottom — and do not match the Eurorack rail pattern. Fix by hand on the
board; treat the board, not the script, as correct.

---

## Why not 6 HP

Worth recording, because the panel *holes* fit at 6 HP and everything looked fine right up until it
wasn't.

The toggle's **bushing** is 6 mm, but its **body** is 13.7 mm across (courtyard). At 6 HP the two
toggle columns sit 14.4 mm apart on centre, which leaves **1.2 mm between the two bodies** — and the
LED spine runs down the middle of exactly that gap. A 3 mm LED does not fit in a 1.2 mm slot:

```
6 HP panel                            30.0 mm
  left toggle body    1.2 .. 14.4
  right toggle body  15.6 .. 28.8      -> 1.2 mm between them
  LED (3 mm) at 15.0 needs            13.5 .. 16.5
  => LED body overlaps BOTH toggles by ~0.9 mm
```

A centreline LED needs `2 × (7.8 + 6.85) + 3.9 + clearance ≈ 33.3 mm`, so 6 HP misses by over 3 mm.
No LED size rescues it — even a 2 mm LED still needs more than 30 mm. Only a narrower-bodied
sub-miniature DPDT would have, and at $3.99 each plus 30 % tariff that was worse than spending 2 HP.

**The lesson, and the reason `panel_geom.py` exists:** a PCB DRC checks copper and holes. It does not
check the *bodies* of through-panel hardware, and on this module the bodies are what decide the
width. All geometry is now solved from real footprint extents with an explicit body-clearance check,
so this class of mistake fails loudly instead of silently.

> Two things a PCB DRC will *not* catch, because neither is a board feature: the switch **nut**, a
> washer sitting on top of the panel, and the switch **body** behind it. Both are checked by
> `build_panel.py` and in the mechanical notes above.

---

## The main board

`Hardware/pulses_plus/pulses_plus.kicad_pcb`, generated by [`build_board.py`](build_board.py).

The board sits **behind** the panel with its F side facing the player, so panel (x, y) and board
(x, y) are the **same frame — no mirroring**. Only the parts that must line up with panel holes are
placed: 10 toggles, 3 jacks, 10 LEDs. ICs, passives and the ribbon headers are left for hand
placement.

Board outline is 39.16 × **110 mm**, centred on the panel, which is what clears the Eurorack rails
top and bottom. Every body clearance is ≥ 1.00 mm and nothing sits outside the outline;
`build_board.py` refuses to write the file if any two bodies overlap.

No 6 mm hole in the *board* for the toggles: these are the PCB-vertical variant, so the body sits on
the PCB and only the bushing passes through the panel.

Footprint fields on all 90 schematic symbols are filled in by
[`patch_footprints.py`](patch_footprints.py) — an in-place patch, so it won't clobber hand edits to
the schematic. Panel-facing parts use the project library; the rest are stock KiCad SMD parts chosen
to match the Rev 2 board's style. Change them freely.

> ⚠ **Verify the toggle pad mapping with a meter before ordering boards.** The datasheet does not
> number the terminals. `SW_T2_4X_DPDT` assumes the **centre pin of each row of three is the common**
> (rows = poles), and that pad 2 is the **right-hand** pin because a toggle connects its common to
> the terminal *opposite* the way the lever is pushed (lever left → right-hand terminal → Bus A).
> The common-in-centre assumption is the critical one. If the lever sense is inverted, Bus A and
> Bus B simply swap — cosmetic, fixable by relabelling.

---

## Open questions

1. **Toggle pad mapping** — verify with a meter (above). This is the only thing that could scrap a
   board run.
2. **Mounting holes** — not to spec, fix by hand on the panel.
3. FR4 panels with zero copper: some fabs want a minimum copper area. Add a token pour if yours
   complains.
4. Whether to expose CLOCK as a ninth channel later, using the spare U2 buffer and U3 gate.
