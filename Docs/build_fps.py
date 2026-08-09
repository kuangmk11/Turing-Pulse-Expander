"""Build the project footprint library: Hardware/pulses_plus/pulses_plus.pretty/

Three footprints:
  SW_T2_4X_DPDT      - Adam Tech toggle, drawn from the datasheet
  Thonkiconn_PJ301M   - lifted from the proven Rev 2 board, pads renamed T/TN/S
  LED_3mm             - same, pads renamed 1(K)/2(A)

The Eagle-imported originals use named pads (P$1_TIP, A/K); KiCad's stock symbols use
numbers/letters that don't match, so the pads are renamed here to link up cleanly.
"""
import os, re, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ksym import tokenize, parse, find_all

REV2 = "/mnt/g/Documents/GitHub/Turing-Pulse-Expander/Hardware/pulses_plus/pulses_rev2.kicad_pcb"
PRETTY = "/mnt/g/Documents/GitHub/Turing-Pulse-Expander/Hardware/pulses_plus/pulses_plus.pretty"
os.makedirs(PRETTY, exist_ok=True)
U = lambda: str(uuid.uuid4())
f = lambda v: ("%.4f" % v).rstrip("0").rstrip(".")


def raw_block(txt, start):
    depth, i = 0, start
    while True:
        if txt[i] == '"':
            i += 1
            while txt[i] != '"':
                i += 2 if txt[i] == "\\" else 1
        elif txt[i] == "(":
            depth += 1
        elif txt[i] == ")":
            depth -= 1
            if depth == 0:
                return txt[start:i + 1]
        i += 1


def harvest(name, renames, newname, descr):
    """Pull a footprint out of the Rev 2 board, rename its pads, strip placement."""
    txt = open(REV2, encoding="utf8").read()
    blk = raw_block(txt, txt.index('(footprint "%s"' % name))
    blk = re.sub(r'^\(footprint "%s"' % re.escape(name),
                 '(footprint "%s"' % newname, blk)
    for old, new in renames.items():
        blk = blk.replace('(pad "%s"' % old, '(pad "%s"' % new)
    # drop board-level placement / net / uuid state so it is a clean library part
    blk = re.sub(r'\n\s*\(at [\d.\- ]+\)(?=\n)', "", blk, count=1)
    blk = re.sub(r'\n\s*\(net \d+ "[^"]*"\)', "", blk)
    blk = re.sub(r'\n\s*\(uuid "?[0-9a-f\-]+"?\)', "", blk)
    blk = re.sub(r'\n\s*\(path "[^"]*"\)', "", blk)
    blk = re.sub(r'\(descr "[^"]*"\)', '(descr "%s")' % descr, blk)
    return blk


# ---- 1. Adam Tech SW-T2-4X-E-A2-MA2, DPDT ON-OFF-ON, PCB vertical -----------
# Datasheet: 2 rows x 3 pins, 4.70 mm within a row, 4.80 mm between rows.
# Pin cross-section 0.80 x 1.20 mm -> 1.5 mm drill clears its 1.44 mm diagonal.
# Body 13.2 mm (along the throw axis) x 11.7 mm.  Bushing M6 x 0.75 at the origin.
#
# PAD MAPPING (verify with a meter before ordering boards - see Docs):
#   The centre pin of each row of three is the common pole. Rows = poles.
#     pad 1 = pole 1 common (centre, upper row)   -> symbol SW_DPDT_x2 pin 1 (A)
#     pad 2 = pole 1 throw, RIGHT-hand pin        -> pin 2 (B) = Bus A
#     pad 3 = pole 1 throw, LEFT-hand pin         -> pin 3 (C) = Bus B
#     pads 4/5/6 likewise for pole 2 (lower row)
#   Pad 2 is the RIGHT-hand pin because a toggle connects its common to the terminal
#   OPPOSITE the way the lever is pushed: lever LEFT -> right-hand terminal -> Bus A.
PX, PY = 4.70, 4.80 / 2
DRILL, PADD = 1.5, 2.4
BODY_X, BODY_Y = 13.2, 11.7

pads = [("1", 0, -PY), ("2", +PX, -PY), ("3", -PX, -PY),
        ("4", 0, +PY), ("5", +PX, +PY), ("6", -PX, +PY)]

sw = [f'''(footprint "SW_T2_4X_DPDT"
	(version 20240108)
	(generator "hand")
	(layer "F.Cu")
	(descr "Adam Tech SW-T2-4X-E-A2-MA2 DPDT ON-OFF-ON toggle, PCB vertical, M6x0.75 bushing. Lever throws along X. Pad 1/4 = pole commons (centre pins).")
	(tags "toggle switch dpdt on-off-on eurorack")
	(attr through_hole)
	(property "Reference" "SW" (at 0 -7.5 0) (layer "F.SilkS")
		(uuid {U()}) (effects (font (size 1 1) (thickness 0.15)))
	)
	(property "Value" "SW_T2_4X_DPDT" (at 0 7.5 0) (layer "F.Fab")
		(uuid {U()}) (effects (font (size 1 1) (thickness 0.15)))
	)''']

# body outline (F.Fab) and courtyard
for lay, w, grow in (("F.Fab", 0.1, 0), ("F.CrtYd", 0.05, 0.25)):
    x, y = BODY_X / 2 + grow, BODY_Y / 2 + grow
    sw.append(f'''	(fp_rect
		(start {f(-x)} {f(-y)}) (end {f(x)} {f(y)})
		(stroke (width {w}) (type default)) (fill no)
		(layer "{lay}") (uuid {U()})
	)''')
# silk marker for the pole-1 (upper) row, so orientation is unambiguous on the board
sw.append(f'''	(fp_line
		(start {f(-BODY_X/2)} {f(-BODY_Y/2 - 0.3)}) (end {f(BODY_X/2)} {f(-BODY_Y/2 - 0.3)})
		(stroke (width 0.12) (type default))
		(layer "F.SilkS") (uuid {U()})
	)''')
# NB: no bushing hole in the board. The switch body sits ON the PCB and the bushing
# points forward through the PANEL, so only the panel is drilled 6 mm.
for num, x, y in pads:
    sw.append(f'''	(pad "{num}" thru_hole circle
		(at {f(x)} {f(y)}) (size {PADD} {PADD}) (drill {DRILL})
		(layers "F&B.Cu" "F&B.Mask") (uuid {U()})
	)''')
sw.append(")")
open(os.path.join(PRETTY, "SW_T2_4X_DPDT.kicad_mod"), "w").write("\n".join(sw) + "\n")

# ---- 2 & 3. jack and LED, harvested from the Rev 2 board --------------------
jack = harvest("WQP-PJ301M-12_JACK",
               {"P$1_TIP": "T", "P$2_SWITCH": "TN", "P$3_SLEEVE": "S"},
               "Thonkiconn_PJ301M",
               "Thonkiconn PJ301M-12 switched 3.5mm jack. Pads renamed T/TN/S to match "
               "Connector_Audio:AudioJack2_SwitchT. Origin = panel hole.")
open(os.path.join(PRETTY, "Thonkiconn_PJ301M.kicad_mod"), "w").write(jack + "\n")

led = harvest("LED3MM", {"A": "2", "K": "1"}, "LED_3mm",
              "3mm LED, pads renamed 1=K 2=A to match Device:LED.")
open(os.path.join(PRETTY, "LED_3mm.kicad_mod"), "w").write(led + "\n")

# ---- project fp-lib-table ---------------------------------------------------
open("/mnt/g/Documents/GitHub/Turing-Pulse-Expander/Hardware/pulses_plus/fp-lib-table", "w").write(
    '(fp_lib_table\n  (version 7)\n'
    '  (lib (name "pulses_plus")(type "KiCad")'
    '(uri "${KIPRJMOD}/pulses_plus.pretty")(options "")(descr "Pulses Plus project footprints"))\n)\n')

for n in sorted(os.listdir(PRETTY)):
    print("  ", n)
print("wrote fp-lib-table")
