#!/usr/bin/env python3
"""Check a .drawio file against the mechanically verifiable layout rules.

Usage:  validate_drawio.py <file.drawio> [--gap 40] [--inset 20] [--json]

Checks, per page:
  1. sibling shapes are >=40px apart on at least one axis (nesting is allowed,
     but a nested shape must sit >=20px inside its container)
  2. labels fit their shape at the declared font size
  3. `whiteSpace=wrap;html=1` is present on every labelled vertex
  4. the content fits the page (draw.io tiles the overflow onto extra pages)
  5. no two edges leave the same node through the same port
  6. coordinates are on the 10px grid (warning)

Anything about rendered edge routing is NOT checked here -- that is why the
skill states those rules constructively.

Exit status: 0 = pass (warnings allowed), 1 = failures found, 2 = bad input.
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import re
import sys
import unicodedata
import urllib.parse
import zlib
import xml.etree.ElementTree as ET

ROW_HEIGHT = 18          # 12px font, 1.5 line spacing
BOX_PAD_X = 20           # 10px each side
BOX_PAD_Y = 16
DEFAULT_FONT = 12.0


# --------------------------------------------------------------------------- io

def load_pages(path):
    """Return [(page_name, mxGraphModel element)], decompressing when needed."""
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as exc:
        sys.exit(f"cannot read {path}: {exc}")
    root = tree.getroot()

    if root.tag == "mxGraphModel":
        return [("(single)", root)]

    pages = []
    for i, diagram in enumerate(root.iter("diagram")):
        model = diagram.find("mxGraphModel")
        if model is None:
            model = inflate(diagram.text or "")
            if model is None:
                sys.exit(f"page {i} is neither plain XML nor a valid compressed payload")
        pages.append((diagram.get("name") or f"page{i}", model))
    if not pages:
        sys.exit("no <diagram> found")
    return pages


def inflate(payload):
    """Decode draw.io's deflate-raw + base64 + URI-encoded diagram payload."""
    try:
        raw = zlib.decompress(base64.b64decode(payload.strip()), -15)
        return ET.fromstring(urllib.parse.unquote(raw.decode("utf-8")))
    except Exception:
        return None


# ------------------------------------------------------------------------ model

def parse_style(style):
    out = {}
    for part in (style or "").split(";"):
        if not part:
            continue
        key, _, value = part.partition("=")
        out[key.strip()] = value.strip()
    return out


def geometry(cell):
    geo = cell.find("mxGeometry")
    if geo is None:
        return None
    try:
        return {
            "x": float(geo.get("x", 0)),
            "y": float(geo.get("y", 0)),
            "w": float(geo.get("width", 0)),
            "h": float(geo.get("height", 0)),
        }
    except ValueError:
        return None


def waypoints(cell):
    geo = cell.find("mxGeometry")
    if geo is None:
        return []
    pts = []
    for array in geo.findall("Array"):
        if array.get("as") != "points":
            continue
        for pt in array.findall("mxPoint"):
            try:
                pts.append((float(pt.get("x", 0)), float(pt.get("y", 0))))
            except ValueError:
                pass
    return pts


def collect(model):
    """Return (vertices, edges). Vertex coords are resolved to absolute."""
    root = model.find("root")
    if root is None:
        sys.exit("mxGraphModel has no <root>")

    cells = {}
    order = []
    for cell in root.iter("mxCell"):
        cid = cell.get("id")
        if cid is None:
            continue
        cells[cid] = cell
        order.append(cid)
    # user objects (<object label=... ><mxCell/></object>) wrap a cell
    for obj in root.iter("object"):
        inner = obj.find("mxCell")
        oid = obj.get("id")
        if inner is not None and oid:
            cells[oid] = inner
            inner.set("_label", obj.get("label", ""))
            order.append(oid)

    vertices, edges = {}, []
    for cid in order:
        cell = cells[cid]
        if cell.get("edge") == "1":
            edges.append({
                "id": cid,
                "style": parse_style(cell.get("style")),
                "source": cell.get("source"),
                "target": cell.get("target"),
                "points": waypoints(cell),
            })
        elif cell.get("vertex") == "1":
            geo = geometry(cell)
            if geo is None:
                continue
            vertices[cid] = {
                "id": cid,
                "parent": cell.get("parent"),
                "label": cell.get("value") or cell.get("_label") or "",
                "style": parse_style(cell.get("style")),
                **geo,
            }

    for v in vertices.values():          # relative -> absolute
        ax, ay, seen = v["x"], v["y"], set()
        p = v["parent"]
        while p in vertices and p not in seen:
            seen.add(p)
            ax += vertices[p]["x"]
            ay += vertices[p]["y"]
            p = vertices[p]["parent"]
        v["ax"], v["ay"] = ax, ay

    return vertices, edges


# ------------------------------------------------------------------------- text

def strip_html(label):
    label = re.sub(r"<br\s*/?>", "\n", label or "", flags=re.I)
    label = re.sub(r"<[^>]+>", "", label)
    return (label.replace("&nbsp;", " ").replace("&amp;", "&")
                 .replace("&lt;", "<").replace("&gt;", ">").strip())


def text_width(text, font):
    scale = font / DEFAULT_FONT
    width = 0.0
    for ch in text:
        wide = unicodedata.east_asian_width(ch) in ("W", "F", "A")
        width += (12 if wide else 7) * scale
    return width


def longest_token(text, font):
    """Widest run that word wrap cannot break (CJK breaks anywhere)."""
    widest = 0.0
    for token in re.split(r"\s+", text):
        if not token:
            continue
        if any(unicodedata.east_asian_width(c) in ("W", "F") for c in token):
            widest = max(widest, text_width(token[:1], font))
        else:
            widest = max(widest, text_width(token, font))
    return widest


# ------------------------------------------------------------------------ rules

def is_container_of(outer, inner, inset):
    return (inner["ax"] >= outer["ax"] + inset
            and inner["ay"] >= outer["ay"] + inset
            and inner["ax"] + inner["w"] <= outer["ax"] + outer["w"] - inset
            and inner["ay"] + inner["h"] <= outer["ay"] + outer["h"] - inset)


def encloses(outer, inner):
    return (inner["ax"] >= outer["ax"] and inner["ay"] >= outer["ay"]
            and inner["ax"] + inner["w"] <= outer["ax"] + outer["w"]
            and inner["ay"] + inner["h"] <= outer["ay"] + outer["h"])


def axis_gap(a, b, key, size):
    return max(b[key] - (a[key] + a[size]), a[key] - (b[key] + b[size]))


def check_page(name, model, gap, inset):
    vertices, edges = collect(model)
    fails, warns = [], []

    def fail(msg):
        fails.append(f"[{name}] {msg}")

    def warn(msg):
        warns.append(f"[{name}] {msg}")

    visible = [v for v in vertices.values()
               if v["w"] > 0 and v["h"] > 0
               and v["style"].get("shape") != "umlLifeline"]

    # 1. sibling spacing / nesting
    for i, a in enumerate(visible):
        for b in visible[i + 1:]:
            if a["parent"] != b["parent"]:
                continue
            if encloses(a, b) or encloses(b, a):
                outer, innr = (a, b) if encloses(a, b) else (b, a)
                if not is_container_of(outer, innr, inset):
                    fail(f"{innr['id']} sits <{inset:g}px inside the border of "
                         f"{outer['id']} -- inset it or enlarge the container")
                continue
            gx = axis_gap(a, b, "ax", "w")
            gy = axis_gap(a, b, "ay", "h")
            if gx < gap and gy < gap:
                fail(f"{a['id']} and {b['id']} are only "
                     f"{max(gx, gy):.0f}px apart (need {gap:g}px on one axis)")

    # 2 + 3. label fits, wrap declared
    for v in visible:
        text = strip_html(v["label"])
        if not text:
            continue
        font = float(v["style"].get("fontSize", DEFAULT_FONT) or DEFAULT_FONT)
        if v["style"].get("whiteSpace") != "wrap":
            fail(f"{v['id']} has a label but no whiteSpace=wrap "
                 f"-- draw.io will render it on one line")
        usable = v["w"] - BOX_PAD_X
        if usable <= 0:
            fail(f"{v['id']} is too narrow to hold any text")
            continue
        if longest_token(text, font) > usable:
            fail(f"{v['id']} label {text!r} has an unbreakable run wider than "
                 f"{usable:.0f}px -- widen the shape")
        lines = 0
        for para in text.split("\n"):
            lines += max(1, math.ceil(text_width(para, font) / usable))
        need_h = lines * ROW_HEIGHT * (font / DEFAULT_FONT) + BOX_PAD_Y
        if need_h > v["h"] + 0.5:
            fail(f"{v['id']} label {text!r} needs {lines} lines "
                 f"({need_h:.0f}px) but the shape is {v['h']:.0f}px tall")

    # 4. page fit
    page = model.get("page", "1")
    xs = [v["ax"] for v in visible] + [v["ax"] + v["w"] for v in visible]
    ys = [v["ay"] for v in visible] + [v["ay"] + v["h"] for v in visible]
    for e in edges:
        for px, py in e["points"]:
            xs.append(px)
            ys.append(py)
    if xs and page != "0":
        try:
            pw = float(model.get("pageWidth", 850))
            ph = float(model.get("pageHeight", 1100))
        except ValueError:
            pw, ph = 850.0, 1100.0
        span_w, span_h = max(xs) - min(xs), max(ys) - min(ys)
        if span_w + 2 * gap > pw or span_h + 2 * gap > ph:
            fail(f"content spans {span_w:.0f}x{span_h:.0f}px; with a {gap:g}px "
                 f"margin it needs {span_w + 2 * gap:.0f}x{span_h + 2 * gap:.0f}px "
                 f"but the page is {pw:.0f}x{ph:.0f} -- draw.io will tile the "
                 f"overflow onto extra pages")

    # 5. shared ports
    for role, xk, yk in (("source", "exitX", "exitY"), ("target", "entryX", "entryY")):
        used = {}
        for e in edges:
            node = e[role]
            if not node or xk not in e["style"]:
                continue
            port = (e["style"].get(xk), e["style"].get(yk))
            prev = used.get((node, port))
            if prev:
                fail(f"edges {prev} and {e['id']} use the same {role} port "
                     f"{port} on {node} -- fan them out (0.25/0.5/0.75)")
            else:
                used[(node, port)] = e["id"]
        for e in edges:
            if e[role] and xk not in e["style"]:
                warn(f"edge {e['id']} has no {xk} on its {role} "
                     f"-- draw.io will route it from the shape centre")

    # 6. grid
    off = [v["id"] for v in visible
           if any(abs(v[k] % 10) > 1e-6 for k in ("x", "y", "w", "h"))]
    if off:
        warn(f"off-grid coordinates on: {', '.join(sorted(off)[:8])}"
             f"{' ...' if len(off) > 8 else ''}")

    return fails, warns


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--gap", type=float, default=40.0,
                    help="minimum separation between sibling shapes (default 40)")
    ap.add_argument("--inset", type=float, default=20.0,
                    help="minimum inset of a nested shape (default 20)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    fails, warns = [], []
    for name, model in load_pages(args.file):
        f, w = check_page(name, model, args.gap, args.inset)
        fails += f
        warns += w

    if args.json:
        print(json.dumps({"pass": not fails, "failures": fails, "warnings": warns},
                         ensure_ascii=False, indent=2))
    else:
        for line in fails:
            print(f"FAIL  {line}")
        for line in warns:
            print(f"warn  {line}")
        print(f"\n{len(fails)} failure(s), {len(warns)} warning(s)"
              + ("" if fails else " -- layout checks passed"))
        if not fails:
            print("Not checked here: rendered edge routing, label collisions "
                  "with edges, colour/position grouping. Those hold by "
                  "construction -- do not claim to have verified them.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
