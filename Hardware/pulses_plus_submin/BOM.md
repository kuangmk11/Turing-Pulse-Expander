# Pulses Plus (sub-mini) — Bill of Materials

Generated from `pulses_plus_submin.kicad_sch` (87 placed components, 18 line items).
Two sourcing columns:

- **DigiKey** — for hand assembly (the THT parts and jacks are hand-solder anyway).
- **JLCPCB / LCSC** — the LCSC `C`-number is what JLCPCB SMT assembly needs for the SMD parts.

Switches are sourced from **Love My Switches** (they are the Taiway 200 sub-mini toggles,
not a DigiKey/LCSC stock part).

> ⚠ **Verify before ordering** — part numbers marked *(verify)* are the correct manufacturer
> series but the exact distributor SKU / LCSC stock C-number should be confirmed against live
> stock at order time. Confirmed numbers came from distributor listings and are noted as such.

---

## BOM table

| # | Qty | Value | Refs | Package / Footprint | Mfr Part | DigiKey | JLCPCB / LCSC |
|---|-----|-------|------|---------------------|----------|---------|---------------|
| 1 | 10 | **DPDT ON-OFF-ON toggle** | SW1–SW10 | Taiway 200 sub-mini, PC vertical, ø4.95 bushing | Taiway **200-MDP3-T2B1M2QE** | — | — |
| 2 | 2 | CD4050 hex buffer | U1, U2 | DIP-16 | **CD4050BE** (TI) | 296-2056-ND | C(verify) |
| 3 | 1 | CD40106 hex Schmitt | U3 | DIP-14 | **CD40106BE** (TI) | 296-9797-5-ND *(verify)* | **C71251** |
| 4 | 1 | MMBT3904 NPN | Q1 | SOT-23 | **MMBT3904** | MMBT3904FSCT-ND | **C20526** |
| 5 | 33 | 1N4148 switching diode | D1–D33 | SOD-123 (`Diode_SMD:D_SOD-123`) | **1N4148W** | 1N4148W-FDICT-ND | **C81598** |
| 6 | 10 | 4k7 resistor | R1–R10 | 1206, 1% | Yageo **RC1206FR-074K7L** | search mfr PN | C(verify) |
| 7 | 6 | 10k resistor | R11–R14, R19, R21 | 1206, 1% | Yageo **RC1206FR-0710KL** | search mfr PN | C(verify) |
| 8 | 2 | 1k resistor | R17, R18 | 1206, 1% | Yageo **RC1206FR-071KL** | search mfr PN | C(verify) |
| 9 | 1 | 22k resistor | R20 | 1206, 1% | Yageo **RC1206FR-0722KL** | search mfr PN | C(verify) |
| 10 | 2 | 1M resistor | R15, R16 | 1206, 1% | Yageo **RC1206FR-071ML** | search mfr PN | C(verify) |
| 11 | 3 | 100n capacitor | C1, C2, C3 | 1206, X7R, 50V | Samsung **CL31B104KBCNNNC** | 1276-1092-1-ND *(verify)* | C(verify) |
| 12 | 1 | 10µ capacitor | C4 | 1206, X5R, 25V | Samsung **CL31A106KBHNNNE** | 1276-1940-1-ND *(verify)* | C(verify) |
| 13 | 10 | 3mm LED, high-brightness | LED1–LED10 | 3mm THT | e.g. Kingbright WP710A10 series | any 3mm LED | — |
| 14 | 3 | 3.5mm mono jack "Thonkiconn" | J3 (EXT, switched), J4 (OUT A), J5 (OUT B) | PJ301M-12 / PJ398SM | **PJ398SM** | not stocked | not stocked |
| 15 | 2 | 2×8 IDC box header, 2.54mm | J1 (PULSES IN), J2 (CHAIN THRU) | shrouded, vertical | generic 2x8 IDC | 2×8 shrouded header | C(verify) |

**J3 must be the switched (normalling) variant** — its break contact normals buffered BIT8 into
channel 8. J4/J5 are plain mono. All three are the same Thonkiconn body.

---

## Sourcing notes

**Switches (SW1–SW10) — Love My Switches**
Taiway **200-MDP3-T2B1M2QE**, "Sub-Mini DPDT On-Off-On, PCB Mount, Short Shaft."
~$2.15 ea (≈ $21.50 for 10). Body 8.1 × 23.2 mm, ships with two nuts + a washer.
Product page: <https://lovemyswitches.com/taiway-sub-mini-dpdt-on-off-on-switch-pcb-mount-short-shaft/>
Panel hole is ø4.95 mm (10-48 UNS bushing). All 10 switches are this one part.

**Thonkiconn jacks (J3/J4/J5)** — not a DigiKey/LCSC catalog part. Buy from Thonk, Love My
Switches, Synthrotek, or Oddvolt (PJ398SM / PJ301M-12; the two are interchangeable). If you want
JLCPCB to place them, you'll need to supply them as a consigned part or substitute a catalog jack
with the same footprint.

**Resistors** — Yageo RC1206 series part numbers above are deterministic (`RC1206FR-07` + value
code + `L`, F = 1%). Any 1206 thick-film at 1% is fine; values are non-critical. On JLCPCB these
are Basic parts — pick the in-stock C-number for each value in the parts tool.

**Ceramics** — 100n/10µ 1206 X7R/X5R; any reputable 1206 MLCC works. The Samsung CL31 series
numbers are representative JLCPCB Basic parts.

---

## Action items before fab

1. **Diode footprint — DONE on the board, still needs the schematic.** All 33 diodes (D1–D33)
   are now on `Diode_SMD:D_SOD-123` on the PCB, part **1N4148W / C81598 / DK 1N4148W-FDICT-ND**.
   Nets verified intact after the swap (8 diodes per bus, pad 1 = K → bus/GND, pad 2 = A).
   > ⚠ **The change was made in the PCB only — the schematic Footprint fields still read
   > `D_1206_3216Metric` (33 of them).** Until those are updated, *Update PCB from Schematic* will
   > revert all 33 diodes to 1206. Fix in KiCad: **pcbnew → Tools → Update Schematic from PCB**
   > (back-annotate footprints), or in the schematic editor set the Footprint field of D1–D33 to
   > `Diode_SMD:D_SOD-123` via **Tools → Edit Symbol Fields**.

2. **Meter the switch** — confirm centre pin = common on the actual Taiway part before committing
   to a board run (design open-question #1). Everything assumes centre-is-common.

3. **LED polarity/brightness** — footprint pad 1 = cathode → GND, pad 2 = anode → 4k7. Use
   modern high-brightness 3mm LEDs (drive is only ~2 mA through 4k7 from a CD4050 output at 12 V).

---

## Verified vs. representative

| Confirmed from distributor listings | Representative (confirm at order) |
|---|---|
| Taiway 200-MDP3-T2B1M2QE (Love My Switches) | CD4050BE LCSC C-number |
| CD4050BE — DigiKey 296-2056-ND | CD40106BE DigiKey SKU |
| CD40106BE — LCSC C71251 | all passive LCSC C-numbers |
| MMBT3904 — LCSC C20526 | ceramic cap DigiKey SKUs |
| 1N4148W — LCSC C81598, DigiKey 1N4148W-FDICT-ND | LED / IDC header specifics |
