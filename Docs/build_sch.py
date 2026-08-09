"""Generate pulses_plus.kicad_sch from the netlist in Docs/pulses-plus-design.md.

Connectivity is made with net labels placed on short stubs off each pin, rather than
routed wires. Electrically complete; visually it will want tidying by hand.
"""
import re, uuid, math, sys
import ksym

ROOT_UUID = "26a2b0ab-b556-45bb-8d80-d737de428f9e"   # from the existing empty sheet
PROJECT = "pulses_plus"
OUT = "/mnt/g/Documents/GitHub/Turing-Pulse-Expander/Hardware/pulses_plus/pulses_plus.kicad_sch"

U = lambda: str(uuid.uuid4())

# ---------------------------------------------------------------- netlist ----
# comp: ref -> (lib, sym, value, {unit: (x, y)}, {pin: net})
comps = {}

def add(ref, lib, sym, value, units, pins):
    comps[ref] = dict(lib=lib, sym=sym, value=value, units=units, pins=pins)

# --- ribbon headers: PULSES IN, and CHAIN THRU wired in parallel
HDR = {}
for p in range(1, 9):
    HDR[str(p)] = f"BIT{p}"
HDR["9"] = HDR["10"] = "CLOCK"
HDR["11"] = HDR["12"] = "-12V"
HDR["13"] = HDR["14"] = "GND"
HDR["15"] = HDR["16"] = "+12V"
add("J1", "Connector_Generic", "Conn_02x08_Odd_Even", "PULSES IN", {1: (30, 55)}, HDR)
add("J2", "Connector_Generic", "Conn_02x08_Odd_Even", "CHAIN THRU", {1: (75, 55)}, HDR)

# --- U1/U2 CD4050 input buffers.  units 1-6 = buffers, unit 7 = power.
# buffer unit -> (input pin, output pin)
BUF = {1: ("3", "2"), 2: ("5", "4"), 3: ("7", "6"),
       4: ("9", "10"), 5: ("11", "12"), 6: ("14", "15")}

u1_pins, u1_units = {"1": "+12V", "8": "GND"}, {7: (300, 40)}
for u, bit in zip(range(1, 7), range(1, 7)):          # BIT1..BIT6 -> P1..P6
    i, o = BUF[u]
    u1_pins[i] = f"BIT{bit}"
    u1_pins[o] = f"P{bit}"
    u1_units[u] = (115 + (u - 1) * 30, 40)
add("U1", "4xxx", "4050", "CD4050", u1_units, u1_pins)

u2_pins, u2_units = {"1": "+12V", "8": "GND"}, {7: (300, 85)}
NC = []                                                # no-connect points, filled later
for u in range(1, 7):
    i, o = BUF[u]
    u2_units[u] = (115 + (u - 1) * 30, 85)
    if u == 1:
        u2_pins[i], u2_pins[o] = "BIT7", "P7"
    elif u == 2:
        u2_pins[i], u2_pins[o] = "BIT8", "P8N"
    else:
        u2_pins[i] = "GND"                             # unused CMOS inputs must not float
        u2_pins[o] = None                              # spare output -> no-connect
add("U2", "4xxx", "4050", "CD4050", u2_units, u2_pins)

# --- channel 8 front end: EXT jack, transistor conditioner
add("J3", "Connector_Audio", "AudioJack2_SwitchT", "EXT",
    {1: (350, 55)}, {"T": "CH8_IN", "TN": "P8N", "S": "GND"})
add("R19", "Device", "R", "10k", {1: (385, 50)}, {"1": "CH8_IN", "2": "CH8_BASE"})
add("R20", "Device", "R", "22k", {1: (405, 65)}, {"1": "CH8_BASE", "2": "GND"})
add("D33", "Diode", "1N4148", "1N4148", {1: (425, 65)}, {"2": "GND", "1": "CH8_BASE"})
add("Q1", "Transistor_BJT", "2N3904", "2N3904",
    {1: (450, 55)}, {"2": "CH8_BASE", "1": "GND", "3": "CH8_COL"})
add("R21", "Device", "R", "10k", {1: (480, 40)}, {"1": "CH8_COL", "2": "+12V"})

# --- 8 channels: DPDT routing switch, 4 merge diodes, LED
# pole 1 (unit 1) carries the OR diodes, pole 2 (unit 2) the AND diodes.
# Splitting the poles is what stops the AND pullup leaking into the OR pulldown
# through an unselected throw.  A=common, B=throw A(bus A), C=throw B(bus B).
for n in range(1, 9):
    bx = 25 + (n - 1) * 63.5
    P = f"P{n}"
    add(f"SW{n}", "Switch", "SW_DPDT_x2", "DPDT ON-OFF-ON",
        {1: (bx, 150), 2: (bx + 30, 150)},
        {"1": P,  "2": f"ORA{n}",  "3": f"ORB{n}",
         "4": P,  "5": f"ANDA{n}", "6": f"ANDB{n}"})
    # 1N4148: pin 1 = K (cathode), pin 2 = A (anode)
    add(f"D{4*n-3}", "Diode", "1N4148", "1N4148",
        {1: (bx, 190)},      {"2": f"ORA{n}",  "1": "BUSA_OR"})
    add(f"D{4*n-1}", "Diode", "1N4148", "1N4148",
        {1: (bx, 212)},      {"2": f"ORB{n}",  "1": "BUSB_OR"})
    add(f"D{4*n-2}", "Diode", "1N4148", "1N4148",
        {1: (bx + 30, 190)}, {"2": "BUSA_AND", "1": f"ANDA{n}"})
    add(f"D{4*n}",   "Diode", "1N4148", "1N4148",
        {1: (bx + 30, 212)}, {"2": "BUSB_AND", "1": f"ANDB{n}"})
    # channel LED taps pre-switch, so it shows the channel firing however it is routed
    add(f"R{n}", "Device", "R", "4k7", {1: (bx + 52, 165)}, {"1": P, "2": f"LEDA{n}"})
    add(f"LED{n}", "Device", "LED", "LED", {1: (bx + 52, 192)},
        {"2": f"LEDA{n}", "1": "GND"})               # pin 2 = A, pin 1 = K

# --- bus pull resistors
add("R11", "Device", "R", "10k", {1: (30, 285)},  {"1": "BUSA_OR",  "2": "GND"})
add("R12", "Device", "R", "10k", {1: (50, 285)},  {"1": "BUSA_AND", "2": "+12V"})
add("R13", "Device", "R", "10k", {1: (70, 285)},  {"1": "BUSB_OR",  "2": "GND"})
add("R14", "Device", "R", "10k", {1: (90, 285)},  {"1": "BUSB_AND", "2": "+12V"})

# --- bus mode switches.  Same Adam Tech SW-T2-4X-E (DPDT ON-OFF-ON) as the routing
# switches, so the whole panel is one part number and one footprint.  Pole 2 is unused.
# Centre-off leaves the common floating and R15/R16 pull the Schmitt input low, so the
# centre position is a per-bus MUTE: OR / MUTE / AND.
add("SW9",  "Switch", "SW_DPDT_x2", "OR/MUTE/AND A", {1: (130, 285), 2: (130, 320)},
    {"1": "BUSA_SEL", "2": "BUSA_OR", "3": "BUSA_AND",
     "4": None, "5": None, "6": None})
add("SW10", "Switch", "SW_DPDT_x2", "OR/MUTE/AND B", {1: (170, 285), 2: (170, 320)},
    {"1": "BUSB_SEL", "2": "BUSB_OR", "3": "BUSB_AND",
     "4": None, "5": None, "6": None})
add("R15", "Device", "R", "1M", {1: (205, 285)}, {"1": "BUSA_SEL", "2": "GND"})
add("R16", "Device", "R", "1M", {1: (225, 285)}, {"1": "BUSB_SEL", "2": "GND"})

# --- U3 CD40106: 2 gates per bus (double inversion = buffer), 1 gate for channel 8
add("U3", "4xxx", "40106", "CD40106",
    {1: (260, 285), 2: (295, 285), 3: (330, 285),
     4: (365, 285), 5: (400, 285), 6: (435, 285), 7: (470, 285)},
    {"1": "BUSA_SEL", "2": "BUSA_N",              # gate A
     "3": "BUSA_N",   "4": "BUSA_OUT",            # gate B
     "5": "BUSB_SEL", "6": "BUSB_N",              # gate C
     "9": "BUSB_N",   "8": "BUSB_OUT",            # gate D
     "11": "GND",     "10": None,                 # gate E spare
     "13": "CH8_COL", "12": "P8",                 # gate F -> channel 8
     "7": "GND", "14": "+12V"})

# --- output stage
add("R17", "Device", "R", "1k", {1: (505, 285)}, {"1": "BUSA_OUT", "2": "OUTA_JACK"})
add("R18", "Device", "R", "1k", {1: (525, 285)}, {"1": "BUSB_OUT", "2": "OUTB_JACK"})
add("J4", "Connector_Audio", "AudioJack2", "OUT A", {1: (555, 285)},
    {"T": "OUTA_JACK", "S": "GND"})
add("J5", "Connector_Audio", "AudioJack2", "OUT B", {1: (590, 285)},
    {"T": "OUTB_JACK", "S": "GND"})
add("R9",  "Device", "R", "4k7", {1: (625, 280)}, {"1": "BUSA_OUT", "2": "LEDA9"})
add("LED9", "Device", "LED", "LED", {1: (625, 305)}, {"2": "LEDA9", "1": "GND"})
add("R10", "Device", "R", "4k7", {1: (650, 280)}, {"1": "BUSB_OUT", "2": "LEDA10"})
add("LED10", "Device", "LED", "LED", {1: (650, 305)}, {"2": "LEDA10", "1": "GND"})

# --- decoupling
for i, x in zip(range(1, 4), (685, 705, 725)):
    add(f"C{i}", "Device", "C", "100n", {1: (x, 285)}, {"1": "+12V", "2": "GND"})
add("C4", "Device", "C", "10u", {1: (745, 285)}, {"1": "+12V", "2": "GND"})

# --- power flags so ERC sees the rails as driven
for i, (net, x) in enumerate((("+12V", 775), ("GND", 795), ("-12V", 815))):
    add(f"#FLG{i}", "power", "PWR_FLAG", "PWR_FLAG", {1: (x, 275)}, {"1": net})

# ------------------------------------------------------------ emit ----------
def pin_xy(px, py, x, y):
    """Symbol-space pin -> schematic coords (placement angle 0, no mirror)."""
    return (px + x, py - y)

def outward(a):
    """Unit vector pointing away from the symbol body, in schematic coords."""
    return (-math.cos(math.radians(a)), math.sin(math.radians(a)))

def fnum(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")

lib_ids, body, nets_seen = {}, [], set()
no_connects = []

for ref, c in sorted(comps.items()):
    lib_id = f"{c['lib']}:{c['sym']}"
    lib_ids[lib_id] = (c["lib"], c["sym"])
    raw_units = ksym.pins_by_unit(c["lib"], c["sym"])
    shared = raw_units.get(0, [])          # unit 0 = pins common to every unit
    upins = {u: p + shared for u, p in raw_units.items() if u != 0}
    if not upins:                          # symbol keeps all its pins in unit 0
        upins = {1: shared}
    known = {p[0] for pins in upins.values() for p in pins}
    unknown = set(c["pins"]) - known
    if unknown:
        sys.exit(f"ERROR {ref} ({lib_id}): pins not in symbol: {sorted(unknown)}")

    for unit, (px, py) in c["units"].items():
        if unit not in upins:
            sys.exit(f"ERROR {ref}: unit {unit} not in {lib_id} (units: {sorted(upins)})")
        body.append(f'''	(symbol
		(lib_id "{lib_id}")
		(at {fnum(px)} {fnum(py)} 0)
		(unit {unit})
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(uuid {U()})
		(property "Reference" "{ref}"
			(at {fnum(px)} {fnum(py - 12)} 0)
			(effects (font (size 1.27 1.27)))
		)
		(property "Value" "{c['value']}"
			(at {fnum(px)} {fnum(py + 12)} 0)
			(effects (font (size 1.27 1.27)))
		)
		(property "Footprint" "" (at {fnum(px)} {fnum(py)} 0)
			(effects (font (size 1.27 1.27)) (hide yes))
		)
		(instances
			(project "{PROJECT}"
				(path "/{ROOT_UUID}"
					(reference "{ref}")
					(unit {unit})
				)
			)
		)
	)''')

        for num, name, ptype, x, y, ang in upins[unit]:
            if num not in c["pins"]:
                continue
            net = c["pins"][num]
            sx, sy = pin_xy(px, py, x, y)
            dx, dy = outward(ang)
            ex, ey = sx + dx * 2.54, sy + dy * 2.54
            if net is None:                       # spare pin -> explicit no-connect
                no_connects.append((sx, sy))
                continue
            nets_seen.add(net)
            body.append(f'''	(wire
		(pts (xy {fnum(sx)} {fnum(sy)}) (xy {fnum(ex)} {fnum(ey)}))
		(stroke (width 0) (type default))
		(uuid {U()})
	)''')
            lang = 0 if dx > 0.5 else 180 if dx < -0.5 else (90 if dy < 0 else 270)
            body.append(f'''	(label "{net}"
		(at {fnum(ex)} {fnum(ey)} {lang})
		(effects (font (size 1.27 1.27)) (justify left bottom))
		(uuid {U()})
	)''')

for sx, sy in no_connects:
    body.append(f'	(no_connect (at {fnum(sx)} {fnum(sy)}) (uuid {U()}))')

# --- lib_symbols: copy KiCad's own definitions verbatim, resolving `extends`
lib_blocks = []
for lib_id, (lib, sym) in sorted(lib_ids.items()):
    node = ksym.get_symbol(lib, sym)
    parent = ksym.extends_of(node)
    src = parent or sym
    raw = ksym.raw_block(lib, src)
    # rename the outer symbol and its "<base>_u_s" sub-symbols to match the lib_id
    raw = re.sub(r'^\(symbol "%s"' % re.escape(src), '(symbol "%s"' % lib_id, raw)
    raw = re.sub(r'\(symbol "%s_(\d+_\d+)"' % re.escape(src),
                 lambda m: '(symbol "%s_%s"' % (sym, m.group(1)), raw)
    lib_blocks.append("\n".join("\t\t" + ln for ln in raw.splitlines()))

sch = f'''(kicad_sch
	(version 20260306)
	(generator "eeschema")
	(generator_version "10.0")
	(uuid {ROOT_UUID})
	(paper "A1")
	(lib_symbols
{chr(10).join(lib_blocks)}
	)
{chr(10).join(body)}
	(sheet_instances
		(path "/"
			(page "1")
		)
	)
	(embedded_fonts no)
)
'''

open(OUT, "w", encoding="utf8").write(sch)

units = sum(len(c["units"]) for c in comps.values())
print(f"wrote {OUT}")
print(f"  {len(comps)} components, {units} symbol units, {len(nets_seen)} nets, "
      f"{len(no_connects)} no-connects, {len(lib_blocks)} lib symbols")
print("  nets:", ", ".join(sorted(nets_seen)))
