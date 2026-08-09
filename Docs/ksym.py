"""Minimal s-expression parser + KiCad symbol library reader.

Quoted strings become Str (a str subclass) so they can be told apart from bare
atoms, which matter when matching tags like `symbol` vs a symbol *named* "symbol".
Library blocks are copied as raw text rather than re-serialised.
"""
import re, os

LIBDIR = "/mnt/g/Program Files/KiCad/10.0/share/kicad/symbols"

class Str(str):
    """A quoted string from the s-expression."""

def tokenize(s):
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in '()':
            out.append(c); i += 1
        elif c == '"':
            j, buf = i + 1, []
            while j < n:
                if s[j] == '\\':
                    buf.append(s[j+1]); j += 2
                elif s[j] == '"':
                    break
                else:
                    buf.append(s[j]); j += 1
            out.append(Str(''.join(buf))); i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()"':
                j += 1
            out.append(s[i:j]); i = j
    return out

def parse(tokens):
    def helper(i):
        node, i = [], i + 1
        while tokens[i] != ')':
            if tokens[i] == '(':
                sub, i = helper(i)
                node.append(sub)
            else:
                node.append(tokens[i]); i += 1
        return node, i + 1
    node, _ = helper(0)
    return node

_libs, _syms, _text = {}, {}, {}

def _lib(name):
    if name not in _libs:
        path = os.path.join(LIBDIR, name + ".kicad_sym")
        _text[name] = open(path, encoding='utf8').read()
        _libs[name] = parse(tokenize(_text[name]))
    return _libs[name]

def find_all(node, tag):
    return [c for c in node
            if isinstance(c, list) and c and not isinstance(c[0], Str) and c[0] == tag]

def get_symbol(lib, sym):
    key = (lib, sym)
    if key not in _syms:
        for node in _lib(lib):
            if isinstance(node, list) and node and node[0] == 'symbol' \
               and isinstance(node[1], Str) and str(node[1]) == sym:
                _syms[key] = node
                break
        else:
            raise KeyError(f"{lib}:{sym} not found")
    return _syms[key]

def raw_block(lib, sym):
    """Raw text of `(symbol "name" ...)`, balanced-paren extracted."""
    _lib(lib)
    txt = _text[lib]
    start = txt.index('(symbol "%s"' % sym)
    depth, i = 0, start
    while True:
        if txt[i] == '"':                       # skip string literals
            i += 1
            while txt[i] != '"':
                i += 2 if txt[i] == '\\' else 1
        elif txt[i] == '(':
            depth += 1
        elif txt[i] == ')':
            depth -= 1
            if depth == 0:
                return txt[start:i+1]
        i += 1

def extends_of(node):
    e = find_all(node, 'extends')
    return str(e[0][1]) if e else None

def pins_by_unit(lib, sym):
    """{unit: [(number, name, type, x, y, angle)]} — follows `extends`."""
    node = get_symbol(lib, sym)
    parent = extends_of(node)
    if parent:
        node = get_symbol(lib, parent)
    base = str(node[1])
    units = {}
    for sub in find_all(node, 'symbol'):
        m = re.match(re.escape(base) + r'_(\d+)_(\d+)$', str(sub[1]))
        if not m:
            continue
        u = int(m.group(1))
        for pin in find_all(sub, 'pin'):
            at = find_all(pin, 'at')[0]
            units.setdefault(u, []).append((
                str(find_all(pin, 'number')[0][1]),
                str(find_all(pin, 'name')[0][1]),
                pin[1],
                float(at[1]), float(at[2]), float(at[3]),
            ))
    return units
