"""Single source of truth for Pulses Plus panel/board geometry.

build_panel.py (holes + silkscreen) and build_board.py (component placement) both
import this, so the panel and the board cannot drift apart.

The y positions are SOLVED, not chosen by eye: component body extents are read from
the footprint library and the stack is packed downward from the output jacks with a
fixed clearance. Bodies, not holes, are the binding constraint here -- the toggle
bushing is 6 mm but its body is 13.7 mm, and that is what killed 6 HP: two of those
bodies left a 1.2 mm gap, and a 3 mm LED has to sit between them on the centreline.

Note the Thonkiconn is ASYMMETRIC about its origin (-6.00 above, +7.33 below).

WARNING -- the toggle is now the Taiway 200-MDP3 (body 8.10 x 9.10) rather than the
Adam Tech SW-T2-4X (13.7 x 12.25), so this file no longer SOLVES to the positions the
committed panel and board actually carry: the smaller body lets the solver pack ~1.3 mm
tighter, and it would move all ten toggles. The boards are as-built and hand-maintained.
Do not re-run build_panel.py OR build_board.py over them -- the numbers below are now
for CHECKING clearances (all of which only got bigger), not for regenerating placement.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kfp import fp_bbox

HP = 8
W = HP * 5.08 - 0.48          # 40.16 mm
H = 128.5                     # 3U
CX = W / 2                    # LED spine

CLR = 1.0                     # body-to-body clearance target
EDGE = 0.5                    # body-to-board-edge margin

# --- real body extents, straight from the footprints -------------------------
SW = fp_bbox("SW_200_MDP3_DPDT")       # x0, y0, x1, y1
JK = fp_bbox("Thonkiconn_PJ301M")
LD = fp_bbox("LED_3mm")

SW_HX, SW_UP, SW_DN = SW[2], -SW[1], SW[3]     # 4.30, 4.85, 4.80
JK_UP, JK_DN = -JK[1], JK[3]                   # 6.00, 7.33
LD_UP, LD_DN, LD_HX = -LD[1], LD[3], -LD[0]    # 2.03, 2.03, 2.03

# --- horizontal --------------------------------------------------------------
# NUT_AC is the M6 nut of the old Adam Tech part. The Taiway's 10-48 nut is smaller, but
# the toggle columns are left where the boards were built, so this stays -- it is now a
# conservative bound rather than a tight one.
NUT_AC, EDGE_GAP = 9.2, 3.2
SWL = EDGE_GAP + NUT_AC / 2            # 7.80 -- nut sits clear of the panel edge
SWR = W - SWL                          # 32.36
LED_TO_BODY = (CX - SWL) - SW_HX - LD_HX       # the number that had to go positive

# --- vertical: board centred on the panel, 110 mm tall to clear the rails -----
BOARD_H = 110.0
BOARD_TOP = (H - BOARD_H) / 2          # 9.25
BOARD_BOT = BOARD_TOP + BOARD_H        # 119.25

# packed upward from the output jacks
BUS_JACK_Y = BOARD_BOT - JK_DN - EDGE                       # 111.42
BUS_SW_Y = BUS_JACK_Y - JK_UP - CLR - SW_HX                 # rotated 90: x-extent is its height
BUS_LED_Y = BUS_SW_Y - SW_HX - CLR - LD_DN
EXT_Y = BUS_LED_Y - LD_UP - CLR - JK_DN

# channel rows: pitch is capped by the EXT jack having to clear channel 7's toggle
ROW0 = BOARD_TOP + SW_UP + EDGE                             # 15.90
PITCH = 8.0                                                 # same-column toggles: 2 * PITCH
ROWS = [ROW0 + i * PITCH for i in range(8)]
LED_RISE = 2.5                         # channel LED rides above its toggle's row

# --- holes -------------------------------------------------------------------
D_BUSH, D_JACK, D_LED, D_MNT = 4.95, 6.0, 3.2, 3.2   # bushing: Taiway 10-48, o4.80 thread
MNT_INSET, MNT_EDGE = 7.5, 3.0


def check():
    return [
        ("toggle <-> toggle (same column)", 2 * PITCH - (SW_UP + SW_DN)),
        ("centreline LED <-> toggle body", LED_TO_BODY),
        ("board top <-> SW1 body", (ROWS[0] - SW_UP) - BOARD_TOP),
        ("ch7 toggle <-> EXT jack", (EXT_Y - JK_UP) - (ROWS[6] + SW_DN)),
        ("ch8 toggle <-> bus LED", (BUS_LED_Y - LD_UP) - (ROWS[7] + SW_DN)),
        ("EXT jack <-> bus LED", (BUS_LED_Y - LD_UP) - (EXT_Y + JK_DN)),
        ("bus LED <-> mode toggle", (BUS_SW_Y - SW_HX) - (BUS_LED_Y + LD_DN)),
        ("mode toggle <-> out jack", (BUS_JACK_Y - JK_UP) - (BUS_SW_Y + SW_HX)),
        ("out jack <-> board bottom", BOARD_BOT - (BUS_JACK_Y + JK_DN)),
    ]


if __name__ == "__main__":
    print(f"{HP} HP -> {W:.2f} x {H} mm, centreline x = {CX:.2f}")
    print(f"toggle columns x = {SWL:.2f} / {SWR:.2f}")
    print(f"board {BOARD_TOP:.2f} .. {BOARD_BOT:.2f}  ({BOARD_H:.0f} mm tall)")
    print(f"rows {[round(r, 2) for r in ROWS]}")
    print(f"EXT {EXT_Y:.2f}  busLED {BUS_LED_Y:.2f}  busSW {BUS_SW_Y:.2f}  "
          f"outJack {BUS_JACK_Y:.2f}")
    print("\nbody clearances:")
    bad = 0
    for label, g in check():
        bad += g < 0
        print(f"  {label:34} {g:6.2f} mm{'  *** FAIL ***' if g < 0 else ''}")
    print("\nALL CLEAR" if not bad else f"\n{bad} FAILURES")
