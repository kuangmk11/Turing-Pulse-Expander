"""Fill in the Footprint field of every symbol in the schematic, in place.

An in-place patch rather than a regenerate, so any hand edits to the schematic survive.
Footprints for the panel-facing parts come from the project library; the rest are stock
KiCad parts chosen to match the SMD style of the Rev 2 board -- change freely.

NOTE: this only fills Footprint fields that are EMPTY (see the regex below) -- it never
overwrites one that is already set. On a fully-populated schematic it matches nothing and
exits. The map below has been corrected to describe what the board ACTUALLY carries: the
ICs are DIP, the passives are the HandSolder 1206 variants, and the ribbon headers are
IDC -- the design moved on from the SMD choices this file originally listed.
"""
import re, sys

SCH = ("/mnt/g/Documents/GitHub/Turing-Pulse-Expander/Hardware/"
       "pulses_plus_submin/pulses_plus_submin.kicad_sch")

def fp_for(ref):
    if ref.startswith("SW"):  return "pulses_plus_submin:SW_200_MDP3_DPDT"
    # The board places the STOCK LED footprint, which is origined on pad 1. The project
    # library's LED_3mm is a body-centred variant that exists only so panel_geom.py can
    # reason about where the panel hole goes -- do not hand it to the board.
    if ref.startswith("LED"): return "LED_THT:LED_D3.0mm"
    if ref in ("J3", "J4", "J5"): return "pulses_plus_submin:Thonkiconn_PJ301M"
    if ref in ("J1", "J2"):
        return "Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical"
    if ref in ("U1", "U2"):   return "Package_DIP:DIP-16_W7.62mm"
    if ref == "U3":           return "Package_DIP:DIP-14_W7.62mm"
    if ref == "Q1":           return "Package_TO_SOT_SMD:SOT-23"
    if ref.startswith("D"):   return "Diode_SMD:D_SOD-123"
    if ref.startswith("R"):   return "Resistor_SMD:R_1206_3216Metric_Pad1.30x1.75mm_HandSolder"
    if ref.startswith("C"):   return "Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder"
    if ref.startswith("#"):   return ""          # power flags
    raise KeyError(ref)

txt = open(SCH, encoding="utf8").read()

# Only patch the placed symbol INSTANCES. The lib_symbols cache near the top of the
# file also has Reference/Value/Footprint properties and must be left alone.
head_end = txt.index('\t(symbol\n\t\t(lib_id')
head, body = txt[:head_end], txt[head_end:]

pat = re.compile(
    r'(\(property "Reference" "([^"]+)"[\s\S]{0,400}?'
    r'\(property "Value" "[^"]*"[\s\S]{0,400}?'
    r'\(property "Footprint" ")(")'
)
seen = {}
def sub(m):
    ref = m.group(2)
    fp = fp_for(ref)
    seen[ref] = fp
    return m.group(1) + fp + m.group(3)

new, n = pat.subn(sub, body)
if n == 0:
    sys.exit("no Footprint fields matched - schematic format changed?")
open(SCH, "w", encoding="utf8").write(head + new)

by_fp = {}
for ref, fp in seen.items():
    by_fp.setdefault(fp or "(none)", []).append(ref)
print(f"patched {n} symbol units, {len(seen)} components\n")
for fp, refs in sorted(by_fp.items()):
    print(f"  {len(refs):3} x {fp}")
