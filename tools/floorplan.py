#!/usr/bin/env python3
"""Draw a dimensioned floor plan of plan.json (both floors) as a PNG for review.

    python3 tools/floorplan.py [--out renders/floorplan.png] [--scale 14]
Rooms with names and W x D in feet, openings as gaps (doors) or bars (windows), key features labeled.
"""
import argparse
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOM_FILL = {"plaster": (236, 228, 214), "oxblood": (196, 122, 118), "olive": (196, 200, 160), "terrazzo": (222, 220, 212),
             "walnut": (190, 160, 130), "concrete": (205, 205, 200), "wallpaper_geo": (196, 200, 160), "default": (230, 226, 218)}
KEY_FEATURES = ["kitchen island", "kitchen back counter", "fireplace walnut wall", "hearth bench", "living sofa",
                "living bookwall", "away lounge chair", "away bookwall", "bed", "gym platform", "gym rack",
                "sauna box", "bar counter", "lounge tv panel", "lounge games table", "gym mirror wall"]


def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def draw_floor(plan, floor, scale, title):
    rooms = [r for r in plan["rooms"] if r["floor"] == floor]
    X0 = min(r["b"][0] for r in rooms)
    Y0 = min(r["b"][1] for r in rooms)
    X1 = max(r["b"][2] for r in rooms)
    Y1 = max(r["b"][3] for r in rooms)
    pad = 60
    W = int((X1 - X0) * scale + 2 * pad)
    H = int((Y1 - Y0) * scale + 2 * pad + 40)
    im = Image.new("RGB", (W, H), (250, 248, 244))
    d = ImageDraw.Draw(im)
    f_room = font(int(scale * 1.15))
    f_dim = font(int(scale * 0.85))
    f_small = font(int(scale * 0.75))
    f_title = font(int(scale * 1.6))

    def P(x, y):
        # plan y (street at 0) drawn at the bottom
        return (pad + (x - X0) * scale, pad + 40 + (Y1 - y) * scale)

    d.text((pad, 14), title, fill=(40, 34, 30), font=f_title)
    for r in rooms:
        x0, y0, x1, y1 = r["b"]
        fill = ROOM_FILL.get(r["wall"], ROOM_FILL["default"])
        d.rectangle([P(x0, y1), P(x1, y0)], fill=fill, outline=(60, 50, 44), width=3)
    # features
    fz = plan["floors"][floor]["z"]
    for f in plan.get("features", []):
        b = f["box"]
        if not (fz - 0.5 <= b[4] <= fz + 9.5):
            continue
        d.rectangle([P(b[0], b[3]), P(b[2], b[1])], fill=(170, 150, 128), outline=(110, 90, 70), width=1)
        if f["note"] in KEY_FEATURES and (b[2] - b[0]) * scale > 40:
            d.text((P(b[0], b[3])[0] + 3, P(b[0], b[3])[1] + 2), f["note"].replace("kitchen ", "").replace("living ", "").replace("lounge ", ""), fill=(70, 50, 35), font=f_small)
    for p in plan.get("pits", []):
        if plan["rooms"][[r["name"] for r in plan["rooms"]].index(p["room"])]["floor"] == floor:
            d.rectangle([P(p["b"][0], p["b"][3]), P(p["b"][2], p["b"][1])], fill=(150, 190, 190), outline=(40, 90, 90), width=3)
            d.text((P(p["b"][0], p["b"][3])[0] + 6, P(p["b"][0], p["b"][3])[1] + 4), "sunken pit %.0fx%.0f, %.1f ft down" % (p["b"][2] - p["b"][0], p["b"][3] - p["b"][1], p["depth"]), fill=(20, 60, 60), font=f_small)
    st = plan.get("stair")
    if st and floor in (st["floor_top"], st["floor_bottom"]):
        yt = st["y_top"]
        run = st.get("tread_in", 10.5) / 12.0 * (st["risers"] - 1)
        d.rectangle([P(st["x0"], yt + run), P(st["x1"], yt)], fill=(230, 210, 170), outline=(120, 90, 40), width=2)
        n = st["risers"]
        for i in range(1, n):
            yy = yt + i * run / (n - 1)
            d.line([P(st["x0"], yy), P(st["x1"], yy)], fill=(120, 90, 40), width=1)
        d.text((P(st["x0"], yt + run)[0] + 4, P(st["x0"], yt + run)[1] + 4), "stair %s" % ("down" if floor == st["floor_top"] else "up"), fill=(80, 60, 20), font=f_small)
    # openings
    for o in plan["openings"]:
        if o["floor"] != floor:
            continue
        w = o["w"]
        is_win = o.get("z0", 0) > 0 or o.get("kind") in ("window", "glasswall")
        col = (90, 150, 200) if is_win else (250, 248, 244)
        lw = 4 if is_win else 8
        if o["axis"] == "x":
            d.line([P(o["c"] - w / 2, o["at"]), P(o["c"] + w / 2, o["at"])], fill=col, width=lw)
        else:
            d.line([P(o["at"], o["c"] - w / 2), P(o["at"], o["c"] + w / 2)], fill=col, width=lw)
    # labels
    for r in rooms:
        x0, y0, x1, y1 = r["b"]
        cx, cy = P((x0 + x1) / 2, (y0 + y1) / 2)
        name = r["name"].replace("awayhall", "away hall")
        tw = d.textlength(name, font=f_room)
        d.text((cx - tw / 2, cy - scale * 1.1), name, fill=(30, 26, 22), font=f_room)
        dim = "%g x %g ft" % (x1 - x0, y1 - y0)
        tw = d.textlength(dim, font=f_dim)
        d.text((cx - tw / 2, cy + scale * 0.15), dim, fill=(80, 70, 60), font=f_dim)
    # outer dims and compass
    d.text((pad, H - 30), "street side (Y=0) at the bottom, back yard at the top. Footprint %g x %g ft. Blue = glass, gaps = doors." % (X1 - X0, Y1 - Y0), fill=(80, 70, 60), font=f_small)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=os.path.join(ROOT, "plan.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "renders", "floorplan.png"))
    ap.add_argument("--scale", type=float, default=14.0, help="pixels per foot")
    args = ap.parse_args()
    plan = json.load(open(args.plan))
    a = draw_floor(plan, "main", args.scale, "Main floor (as built from plan.json)")
    b = draw_floor(plan, "basement", args.scale, "Basement (as built from plan.json)")
    W = a.width + b.width + 30
    H = max(a.height, b.height)
    out = Image.new("RGB", (W, H), (250, 248, 244))
    out.paste(a, (0, 0))
    out.paste(b, (a.width + 30, 0))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out.save(args.out)
    print("wrote", args.out, out.size)


if __name__ == "__main__":
    main()
