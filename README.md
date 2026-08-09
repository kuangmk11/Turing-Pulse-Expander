# Turing Pulse Expander — Pulses Plus

A performance-oriented gate router for the Music Thing Turing Machine. Eight pulse channels,
each switchable to one of two merge buses or off; each bus computes the OR or the AND of
whatever is routed to it, chosen live from the panel.

<p align="center">
  <img src="Hardware/pulses_plus_submin/pp.PNG" alt="Pulses Plus front panel, v4" width="280">
</p>

It sits **alongside** a stock Pulses expander rather than replacing it, taking its signals from
the Turing Machine's 16-pin expander ribbon and passing that ribbon through so other expanders
can still be chained downstream.

The stock Pulses gives you seven fixed outputs plus four hard-wired AND combinations. Those AND
outputs are the musical ones — ANDing two shift-register taps gives a sparser, related rhythm.
This generalises that: any subset of the eight bits, OR'd or AND'd, chosen by hand, live. The
four fixed ANDs become a strict subset of what the switches can do.

---

## The finished project: `pulses_plus_submin`

**[`Hardware/pulses_plus_submin/`](Hardware/pulses_plus_submin/) is the built and tested
hardware.** 8 HP, 128.5 × 40.16 mm. Everything else in this repository is either upstream
history or a study that fed into it.

| | |
|---|---|
| `pulses_plus_submin.kicad_sch` | schematic — 87 placed components |
| `pulses_plus_submin.kicad_pcb` | main board |
| **`pulses_plus_submin_panel_v4.kicad_pcb`** | **current panel** |
| `pulses_plus_submin.pretty/` | project footprints — toggle, jack, LED, panel holes |
| `switch_fix.kicad_sym` | the DPDT symbol with the pin numbering the footprint expects |
| `3d/` | 3D models the footprints reference |
| `BOM.md` | bill of materials, DigiKey and JLCPCB/LCSC columns |
| `gerbers/` | fab packages |
| `tools/build_panel.py` | regenerates the panel artwork |
| `PANEL_STYLE_v1.04.md` | the panel house style |

### How it works

Each channel's DPDT ON-OFF-ON toggle throws left to bus A, right to bus B, or centre for off.
Both poles are used: pole 1 carries only the OR diodes, pole 2 only the AND diodes. That
separation is the one non-obvious constraint in the design — sharing a pole leaks current
through the unselected bus and pins its OR net high.

Per bus, a second toggle picks OR, MUTE or AND. Both nets are computed continuously and in
parallel, so the mode switch only selects which one reaches the output buffer and the 32 merge
diodes never switch. Centre-off leaves the buffer input pulled low, which is the mute.

The **EXT** jack is switched (normalled): unplugged, buffered BIT8 feeds channel 8; plugged, an
external gate takes its place through a transistor and Schmitt stage that squares up whatever
amplitude arrives.

Full write-up, including the diode-leak analysis and why 6 HP was abandoned:
**[`Docs/pulses-plus-design.md`](Docs/pulses-plus-design.md)**.

### Key parts

10 × Taiway 200-MDP3 sub-miniature DPDT ON-OFF-ON toggles (ø4.95 bushing), 2 × CD4050 buffers,
1 × CD40106 Schmitt, 33 × 1N4148, 10 × 3 mm LEDs, 3 × Thonkiconn jacks — **J3 must be the
switched variant** — and 2 × 2×8 IDC headers for ribbon in and thru. See
[`BOM.md`](Hardware/pulses_plus_submin/BOM.md).

---

## Panel

The current panel is **v4**, `pulses_plus_submin_panel_v4.kicad_pcb` — white silkscreen on black
soldermask, drawn to [`PANEL_STYLE_v1.04.md`](Hardware/pulses_plus_submin/PANEL_STYLE_v1.04.md).

It is generated. [`tools/build_panel.py`](Hardware/pulses_plus_submin/tools/build_panel.py) reads
the v1 panel and regenerates only the artwork, inheriting every control-hole position, so the
style guide's one non-negotiable rule — hole positions are inherited, never computed — holds by
construction rather than by inspection:

```sh
cd Hardware/pulses_plus_submin && python3 tools/build_panel.py
```

Mounting is four 6.4 × 3.2 mm obround slots on Edge.Cuts, horizontal for ±1.6 mm of slide.
`kicad-cli pcb drc` reports zero violations. Zones refill on open — refill before plotting.

Reading the panel: a ring means signal leaves there, so the two output jacks are the only closed
circles. `A`/`B` beside each toggle are throw directions, not names. The mode stack is `AND` up,
`MUTE` centre, `OR` down. Names sit below the thing they name.

---

## VCV Rack

A Rack 2 port lives in [`Hardware/pulses_plus_vcvrack/`](Hardware/pulses_plus_vcvrack/). It
reconstructs the Turing Machine's shift register locally from BIT and CLOCK, so it runs without
the hardware.

```sh
cd Hardware/pulses_plus_vcvrack && make
```

---

## Upstream: Rev 2 Turing Pulse Expander

This repository is a fork of [TomWhitwell/Turing-Pulse-Expander](https://github.com/TomWhitwell/Turing-Pulse-Expander).
The original Rev 2 expander — a slightly updated Turing Machine Pulse Expander with more outputs,
SMD but still an easy build — remains here as `Hardware/pulses_rev2.brd` / `.sch` with its gerbers
and panel artwork under `Collateral/`.

Its BOM:

- 1 × 4081 Quad AND Gate, SO14 package
- 11 × 3 mm LEDs
- 11 × 1k resistors, 1206
- 11 × 2k resistors, 1206 (LED protection — change the value for high-intensity LEDs)
- 11 × [Thonkiconn](https://www.thonk.co.uk/shop/thonkiconn-3-5mm-jack-sockets-x50/) sockets
- 1 × 16-pin header 2×8 (e.g. Mouser 649-67997-216HLF)
- 1 × ribbon cable

---

## Licence

Designed by Missing Mile Modular. **CC BY-NC-SA 4.0**, as printed on the back of the panel.
