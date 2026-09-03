#!/usr/bin/env python3
"""Draw dimensioned floor plans of plan.json (every floor) plus a site plan, as one PNG for review.

    python3 tools/floorplan.py [--out renders/floorplan.png] [--scale 12]
Rooms (unions of parts) with names and overall W x D in feet, doors as gaps with a swing tick, windows as blue
bars, cased openings as dashed gaps, voids hatched, stairs with treads, columns, beams (living), and the site
with slabs, roofs (dashed outlines), hedges, trees and the garage.
"""
import argparse
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILL = {"plaster_warm": (238, 231, 219), "oxblood": (200, 130, 126), "olive_paint": (200, 204, 166), "terrazzo": (224, 222, 214),
        "walnut": (196, 168, 138), "walnut_panel": (196, 168, 138), "concrete_sealed": (208, 208, 203), "wallpaper_geo_olive": (200, 204, 166),
        "wallpaper_botanical_dark": (150, 150, 140), "tile_white": (232, 236, 236), "cedar_sauna": (222, 190, 150), "default": (232, 228, 220)}


def parts_of(r):
    return r["parts"] if "parts" in r else [r["b"]]


def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(p):
            return ImageFont.truetype(p, max(8, int(size)))
    return ImageFont.load_default()


class Sheet:
    def __init__(self, scale, X0, Y0, X1, Y1, title, pad=50):
        self.s = scale
        self.X0, self.Y0, self.X1, self.Y1 = X0, Y0, X1, Y1
        self.pad = pad
        self.W = int((X1 - X0) * scale + 2 * pad)
        self.H = int((Y1 - Y0) * scale + 2 * pad + 36)
        self.im = Image.new("RGB", (self.W, self.H), (250, 248, 244))
        self.d = ImageDraw.Draw(self.im)
        self.d.text((pad, 10), title, fill=(40, 34, 30), font=font(scale * 1.5))

    def P(self, x, y):
        return (self.pad + (x - self.X0) * self.s, self.pad + 36 + (self.Y1 - y) * self.s)

    def rect(self, b, fill=None, outline=None, width=1):
        self.d.rectangle([self.P(b[0], b[3]), self.P(b[2], b[1])], fill=fill, outline=outline, width=width)

    def line(self, a, b, fill, width=1):
        self.d.line([self.P(*a), self.P(*b)], fill=fill, width=width)

    def text(self, x, y, s, size, fill=(30, 26, 22), center=True):
        f = font(size)
        tw = self.d.textlength(s, font=f)
        px, py = self.P(x, y)
        self.d.text((px - (tw / 2 if center else 0), py - size / 2), s, fill=fill, font=f)


def draw_floor(plan, floor, scale):
    rooms = [r for r in plan["rooms"] if r["floor"] == floor]
    parts = [p for r in rooms for p in parts_of(r)]
    X0 = min(p[0] for p in parts); Y0 = min(p[1] for p in parts)
    X1 = max(p[2] for p in parts); Y1 = max(p[3] for p in parts)
    fz = plan["floors"][floor]["z"]
    sh = Sheet(scale, X0, Y0, X1, Y1, "%s  (Z %g to %g ft)" % (floor.capitalize(), fz, fz + plan["floors"][floor]["h"]))
    # rooms
    for r in rooms:
        fill = FILL.get(r["wall"], FILL["default"])
        if r.get("void"):
            fill = (215, 215, 222)
        for p in parts_of(r):
            sh.rect(p, fill=fill)
    # internal part boundaries are not walls: draw walls per edge segment between different rooms or exterior
    for r in rooms:
        for p in parts_of(r):
            sh.rect(p, outline=(70, 58, 50), width=3)
    # erase same-room part boundaries by redrawing shared edges in the fill color
    for r in rooms:
        ps = parts_of(r)
        fill = FILL.get(r["wall"], FILL["default"]) if not r.get("void") else (215, 215, 222)
        for i in range(len(ps)):
            for j in range(len(ps)):
                if i == j:
                    continue
                a, b = ps[i], ps[j]
                if abs(a[2] - b[0]) < 1e-6:  # a's east touches b's west
                    lo, hi = max(a[1], b[1]), min(a[3], b[3])
                    if hi - lo > 0.01:
                        sh.line((a[2], lo + 0.15), (a[2], hi - 0.15), fill, width=5)
                if abs(a[3] - b[1]) < 1e-6:
                    lo, hi = max(a[0], b[0]), min(a[2], b[2])
                    if hi - lo > 0.01:
                        sh.line((lo + 0.15, a[3]), (hi - 0.15, a[3]), fill, width=5)
    # voids
    for v in plan.get("voids", []):
        if v["floor"] == floor and v["what"] == "floor":
            b = v["b"]
            sh.rect(b, outline=(120, 60, 60), width=2)
            for k in range(int((b[2] - b[0]) * 2)):
                x = b[0] + k / 2
                sh.line((x, b[1]), (min(b[2], x + (b[3] - b[1])), min(b[3], b[1] + (b[3] - b[1]))), (160, 120, 120), 1)
    # stairs: flights (treads + UP/DOWN), landings, centre walls
    flights = [st for st in plan.get("stairs", []) if st.get("kind", "flight") == "flight"]
    for st in plan.get("stairs", []):
        kind = st.get("kind", "flight")
        if kind == "landing":
            b = st["b"]
            if abs(st["z"] - fz) < 5.01 and st["z"] != fz:
                sh.rect(b, fill=(235, 215, 175), outline=(120, 90, 40), width=2)
                sh.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, "landing %+g" % (st["z"] - fz), scale * 0.7, (80, 60, 20))
            continue
        if kind == "wall":
            b = st["b"]
            if b[4] <= fz + 3 and b[5] >= fz + 3:
                sh.rect(b[:4], fill=(60, 50, 40), outline=(60, 50, 40), width=1)
            continue
        if kind != "flight":
            continue
        zf, zt = st["z_from"], st["z_to"]
        if not (min(zf, zt) - 0.01 <= fz <= max(zf, zt) + 0.01):
            continue
        n = st["risers"]
        y0, y1 = sorted([st["y_from"], st["y_to"]])
        sh.rect([st["x0"], y0, st["x1"], y1], fill=(235, 215, 175), outline=(120, 90, 40), width=2)
        for i in range(n):
            y = y0 + i * (y1 - y0) / (n - 1)
            sh.line((st["x0"], y), (st["x1"], y), (120, 90, 40), 1)
        arrow = "UP" if zt > fz + 0.01 else "DOWN"
        sh.text((st["x0"] + st["x1"]) / 2, (y0 + y1) / 2, arrow, scale * 0.75, (80, 60, 20))
    # columns, beams
    for c in plan.get("columns", []):
        b = c["b"]
        if abs(b[4] - fz) < 0.6:
            sh.rect(b[:4], fill=(120, 90, 60))
    for bm in plan.get("beams", []):
        room = next((r for r in rooms if r["name"] == bm["room"]), None)
        if room:
            ps_ = parts_of(room)
            rb = [min(p[0] for p in ps_), min(p[1] for p in ps_), max(p[2] for p in ps_), max(p[3] for p in ps_)]
            for y in bm.get("positions", []):
                sh.line((rb[0], y), (rb[2], y), (170, 140, 110), 2)
    # openings
    for o in plan["openings"]:
        if o["floor"] != floor:
            continue
        lo, hi = o["c"] - o["w"] / 2, o["c"] + o["w"] / 2
        kind = o.get("kind", "door")
        is_win = kind in ("window", "glasswall") or o.get("z0", 0) > 0
        if kind == "open" and o.get("full"):
            col, w = (250, 248, 244), 6
        elif is_win:
            col, w = (80, 140, 205), 4
        elif kind == "cased":
            col, w = (250, 248, 244), 6
        else:
            col, w = (250, 248, 244), 6
        if o["axis"] == "x":
            sh.line((lo, o["at"]), (hi, o["at"]), col, w)
            if kind in ("door", "glassdoor"):
                sh.line((lo, o["at"]), (lo, o["at"] + (o["w"] if o.get("swing", "pos") != "neg" else -o["w"])), (90, 80, 70), 1)
            if kind == "cased":
                sh.line((lo, o["at"]), (hi, o["at"]), (150, 140, 130), 1)
        else:
            sh.line((o["at"], lo), (o["at"], hi), col, w)
            if kind in ("door", "glassdoor"):
                sh.line((o["at"], lo), (o["at"] + o["w"], lo), (90, 80, 70), 1)
            if kind == "cased":
                sh.line((o["at"], lo), (o["at"], hi), (150, 140, 130), 1)
    # labels
    for r in rooms:
        ps = parts_of(r)
        big = max(ps, key=lambda p: (p[2] - p[0]) * (p[3] - p[1]))
        cx, cy = (big[0] + big[2]) / 2, (big[1] + big[3]) / 2
        bb = [min(p[0] for p in ps), min(p[1] for p in ps), max(p[2] for p in ps), max(p[3] for p in ps)]
        name = r.get("label", r["name"].replace("_", " "))
        area = sum((p[2] - p[0]) * (p[3] - p[1]) for p in ps)
        small = (bb[2] - bb[0]) * (bb[3] - bb[1]) < 40
        if any(st["x0"] < cx < st["x1"] and min(st["y_from"], st["y_to"]) < cy < max(st["y_from"], st["y_to"]) for st in flights):
            cx = bb[0] + 1.5
            small = True
        sh.text(cx, cy + (0.45 if not small else 0.3), name, scale * (0.8 if small else 1.05))
        if not small:
            sh.text(cx, cy - 0.75, "%g x %g   %d sf" % (bb[2] - bb[0], bb[3] - bb[1], area), scale * 0.72, (90, 78, 66))
    sh.d.text((sh.pad, sh.H - 24), "street (south) at the bottom. Blue = glass. Gaps = doors (tick shows the leaf). Hatched = open to below.", fill=(80, 70, 60), font=font(scale * 0.75))
    return sh.im


def draw_site(plan, scale):
    site = plan.get("site", {})
    lot = site.get("lot", [-9, -30, 51, 140])
    X0, Y0, X1, Y1 = lot[0] - 8, lot[1] - 20, lot[2] + 8, lot[3] + 6
    sh = Sheet(scale, X0, Y0, X1, Y1, "Site plan (lot %g x %g ft, house footprint 42 x 46)" % (lot[2] - lot[0], lot[3] - lot[1]))
    sh.rect([X0, Y0, X1, Y1], fill=(214, 226, 200))
    sh.rect(lot, outline=(90, 90, 90), width=2)
    for sl in site.get("slabs", []):
        m = sl["m"]
        col = {"bluestone": (150, 158, 168), "asphalt": (90, 90, 92), "concrete_sealed": (190, 190, 186), "lawn": (176, 200, 140), "gravel_gray": (200, 198, 190)}.get(m, (200, 200, 200))
        sh.rect(sl["b"], fill=col)
    for bd in site.get("beds", []):
        sh.rect(bd["b"], fill=(150, 170, 120), outline=(100, 120, 80))
    for h in site.get("hedges", []):
        sh.rect(h["b"], fill=(70, 110, 60))
    for t in site.get("trees", []):
        x, y = t["pos"]
        r = t["canopy_r"]
        sh.d.ellipse([sh.P(x - r, y + r), sh.P(x + r, y - r)], outline=(60, 100, 50), width=2)
        sh.d.ellipse([sh.P(x - t["trunk_d"], y + t["trunk_d"]), sh.P(x + t["trunk_d"], y - t["trunk_d"])], fill=(80, 60, 40))
        sh.text(x, y - r - 2, t["note"], scale * 0.9, (50, 80, 40))
    for nb in site.get("neighbors", []):
        sh.rect(nb["b"], fill=(205, 180, 165), outline=(120, 90, 80), width=2)
        b = nb["b"]
        sh.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, nb["note"], scale * 0.9, (90, 60, 50))
    # house footprints
    for floor, col in (("main", (238, 231, 219)), ("garage", (225, 220, 210))):
        parts = [p for r in plan["rooms"] if r["floor"] == floor for p in parts_of(r)]
        if not parts:
            continue
        b = [min(p[0] for p in parts), min(p[1] for p in parts), max(p[2] for p in parts), max(p[3] for p in parts)]
        sh.rect(b, fill=col, outline=(60, 50, 44), width=3)
        sh.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, "house" if floor == "main" else "garage", scale * 1.3)
    parts2 = [p for r in plan["rooms"] if r["floor"] == "second" for p in parts_of(r)]
    if parts2:
        b = [min(p[0] for p in parts2), min(p[1] for p in parts2), max(p[2] for p in parts2), max(p[3] for p in parts2)]
        sh.rect([0, 6, 42, 46], outline=(120, 90, 60), width=2)
        sh.text(21, 44, "upper volume (cedar) Y 6-46", scale * 0.9, (110, 80, 50))
    for r in plan.get("exterior", {}).get("roofs", []):
        sh.rect([r["x0"], r["y0"], r["x1"], r["y1"]], outline=(60, 60, 60), width=1)
        sh.text((r["x0"] + r["x1"]) / 2, r["y1"] - 1.2, r["name"], scale * 0.8, (60, 60, 60))
        for (px, py) in r.get("posts", []):
            sh.rect([px - 0.4, py - 0.4, px + 0.4, py + 0.4], fill=(90, 70, 40))
    for st in site.get("structures", []):
        if "b" in st:
            b = st["b"]
            sh.rect(b[:4], outline=(70, 70, 90), width=1, fill=(230, 232, 240) if st["kind"] in ("box", "frame") else None)
            sh.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, st["note"], scale * 0.7, (60, 60, 80))
    sh.d.text((sh.pad, sh.H - 24), "north up. Sidewalk and street at the bottom, alley at the top.", fill=(80, 70, 60), font=font(scale * 0.75))
    return sh.im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=os.path.join(ROOT, "plan.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "renders", "floorplan.png"))
    ap.add_argument("--scale", type=float, default=13.0)
    ap.add_argument("--site-scale", type=float, default=4.2)
    args = ap.parse_args()
    plan = json.load(open(args.plan))
    ims = [draw_floor(plan, f, args.scale) for f in ("second", "main", "basement") if any(r["floor"] == f for r in plan["rooms"])]
    if plan.get("site"):
        ims.append(draw_site(plan, args.site_scale))
    gap = 24
    W = sum(i.width for i in ims) + gap * (len(ims) - 1)
    H = max(i.height for i in ims)
    out = Image.new("RGB", (W, H), (250, 248, 244))
    x = 0
    for im in ims:
        out.paste(im, (x, 0))
        x += im.width + gap
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out.save(args.out)
    print("wrote", args.out, out.size)


if __name__ == "__main__":
    main()
