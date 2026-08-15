# Turing Pulse Expander — archive

> **This repository is an archive.** The finished work has moved out into its own
> repositories; what remains here is upstream material and the studies that were
> superseded along the way.

| Live work | |
|---|---|
| **[Doubleplus_Pulses](https://github.com/kuangmk11/Doubleplus_Pulses)** | **Pulses Plus** — the built and tested hardware. KiCad schematic, PCB, panel v4, BOM, gerbers, and the full design write-up. CC BY-NC-SA 4.0. |
| **[Doubleplus_Pulses_VCV](https://github.com/kuangmk11/Doubleplus_Pulses_VCV)** | The VCV Rack 2 port of the same module. GPL-3.0-or-later. |

Both were extracted with `git subtree split`, so their commit history came with
them. Their files remain in this repository's history too, up to the commit that
removed them — nothing was rewritten here.

---

## What Pulses Plus is

A performance-oriented gate router for the Music Thing Turing Machine: eight pulse
channels, each switchable to one of two merge buses or off, with each bus computing
the OR or the AND of whatever is routed to it, chosen live from the panel. It
generalises the stock Pulses expander's four hard-wired AND outputs into any subset
of the eight bits, OR'd or AND'd, by hand.

See [Doubleplus_Pulses](https://github.com/kuangmk11/Doubleplus_Pulses) for the
design and the write-up.

---

## What's left here

### Upstream: Rev 2 Turing Pulse Expander

This repository is a fork of
[TomWhitwell/Turing-Pulse-Expander](https://github.com/TomWhitwell/Turing-Pulse-Expander),
and keeps that link deliberately — it is the right home for Tom Whitwell's files.

- `Hardware/pulses_rev2.brd`, `Hardware/pulses_rev2.sch` — the original Eagle design
- `Collateral/` — his gerbers, panel artwork and schematic PDF

The Rev 2 expander is a slightly updated Turing Machine Pulse Expander with more
outputs — SMD, but still an easy build. Its BOM:

- 1 × 4081 Quad AND Gate, SO14 package
- 11 × 3 mm LEDs
- 11 × 1k resistors, 1206
- 11 × 2k resistors, 1206 (LED protection — change the value for high-intensity LEDs)
- 11 × [Thonkiconn](https://www.thonk.co.uk/shop/thonkiconn-3-5mm-jack-sockets-x50/) sockets
- 1 × 16-pin header 2×8 (e.g. Mouser 649-67997-216HLF)
- 1 × ribbon cable

### Dead ends and studies

- `Docs/build_*.py`, `kfp.py`, `ksym.py`, `panel_geom.py`, `patch_footprints.py` —
  the generator scripts that built the earlier `pulses_plus` board from source.
  The finished module took a different route: it carries a single, much smaller
  `tools/build_panel.py` that regenerates only panel artwork from the v1 panel.
- `Docs/panel/` — two early panel layout studies (`v1-two-column-grid.html`,
  `v2-zigzag.html`) and the notes comparing them. The zig-zag won and became the
  shipped panel.
- `Hardware/pulses_plus/` — the superseded full-size design that preceded the
  sub-miniature-toggle version. **Present on disk but never committed**; it is
  gitignored and always has been, so it does not exist in this repository's
  history and will not appear in a fresh clone.
- Assorted scratch material at the repository root (`Chat.txt`, `path30.svg`,
  panel artwork exports) — likewise gitignored, on disk only.

---

## Licence

**Tom Whitwell's Rev 2 expander** — `Hardware/pulses_rev2.brd`, `Hardware/pulses_rev2.sch`
and `Collateral/` — is his, inherited by forking
[TomWhitwell/Turing-Pulse-Expander](https://github.com/TomWhitwell/Turing-Pulse-Expander).
Nothing here grants rights over it. For context, the parent
[Turing Machine](https://github.com/TomWhitwell/TuringMachine) project's README states
[CC-BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/), but that is not
stated in the expander repository itself.

**The Pulses Plus studies** in `Docs/` are Missing Mile Modular's, under
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — the same
terms as the finished hardware.
