"""Footprint body extents, read from the project footprint library."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ksym import tokenize, parse, find_all

PRETTY = "/mnt/g/Documents/GitHub/Turing-Pulse-Expander/Hardware/pulses_plus_submin/pulses_plus_submin.pretty"


def fp_bbox(name):
    """Bounding box of a library footprint's graphics + pads, at rotation 0."""
    txt = open(os.path.join(PRETTY, name + ".kicad_mod"), encoding="utf8").read()
    node = parse(tokenize(txt))
    xs, ys = [], []
    for tag in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"):
        for g in find_all(node, tag):
            lay = find_all(g, "layer")
            if not lay or str(lay[0][1]) not in ("F.Fab", "F.CrtYd", "F.SilkS"):
                continue
            for pt in ("start", "end", "center", "mid"):
                for p in find_all(g, pt):
                    xs.append(float(p[1])); ys.append(float(p[2]))
            for poly in find_all(g, "pts"):
                for p in find_all(poly, "xy"):
                    xs.append(float(p[1])); ys.append(float(p[2]))
    for pad in find_all(node, "pad"):
        at = find_all(pad, "at")[0]
        sz = find_all(pad, "size")[0]
        xs += [float(at[1]) - float(sz[1]) / 2, float(at[1]) + float(sz[1]) / 2]
        ys += [float(at[2]) - float(sz[2]) / 2, float(at[2]) + float(sz[2]) / 2]
    return min(xs), min(ys), max(xs), max(ys)
