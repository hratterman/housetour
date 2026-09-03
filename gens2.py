"""gens2: second generation of procedural furniture and fixture generators for staging.py (mixed into Stager).

Conventions (feet, absolute Z unless a 'room' is given for floor_z):
    pos     [x, y, z] point on the floor (bottom centre) unless stated
    b       [x0, y0, x1, y1, z0, z1] box in world feet
    wall    {"axis": "x"|"y", "at": coord, "face": "-y"|"+y"|"-x"|"+x"}  the face the object hangs on;
            face is the direction the object projects INTO the room from that wall
Every light-emitting piece registers a practical with self.light(...) so lighting.py builds a real source.
"""
import math
import random

import bpy
from mathutils import Vector, Matrix

from geom import (FT, IN, m, log, box_ft, box_local, box_centered, beam_between, cylinder_ft, sphere_ft,
                  prism_yz, prism_xz, get_collection)


def _face_dir(wall):
    f = wall["face"]
    return {"-x": (-1, 0), "+x": (1, 0), "-y": (0, -1), "+y": (0, 1)}[f]


class Gens2:
    def gen_throw(self, e):
        """Folded wool throw draped over an arm or a bench: two soft slabs, the lower one hanging down."""
        b = e["b"]
        x0, y0, x1, y1 = b[:4]
        z = e["z"]
        mat = self.mat(e.get("m", "wool_mustard"))
        rot = e.get("rot_z", 0)
        objs = [box_centered(self.uid("throw_fold"), ((x0 + x1) / 2, (y0 + y1) / 2, z + 0.12), (x1 - x0, y1 - y0, 0.24), rot, mat, self.col)]
        drop = e.get("drop", 1.2)
        side = e.get("hang", "+x")
        if side in ("+x", "-x"):
            hx = x1 if side == "+x" else x0
            objs.append(box_centered(self.uid("throw_hang"), (hx + (0.1 if side == "+x" else -0.1), (y0 + y1) / 2, z + 0.12 - drop / 2), (0.2, (y1 - y0) * 0.9, drop), rot, mat, self.col))
        else:
            hy = y1 if side == "+y" else y0
            objs.append(box_centered(self.uid("throw_hang"), ((x0 + x1) / 2, hy + (0.1 if side == "+y" else -0.1), z + 0.12 - drop / 2), ((x1 - x0) * 0.9, 0.2, drop), rot, mat, self.col))
        return objs

    def _room_floor(self, room):
        for r in self.plan.get("rooms", []):
            if r["name"] == room:
                return r["floor"]
        return "main"

    def _wall_cuts(self, wall, floor, margin=0.25):
        """Openings (doors, windows, cased openings) in this wall on this floor as (u0, u1, z0, z1) in absolute
        feet, grown by the casing margin. 'at' may already be shifted to the finished face, so match loosely."""
        fz = self.plan.get("floors", {}).get(floor, {}).get("z", 0.0)
        cuts = []
        for op in self.plan.get("openings", []):
            if op.get("floor") != floor or op.get("axis") != wall["axis"] or abs(op["at"] - wall["at"]) > 1.1:
                continue
            c, w = op["c"], op["w"]
            cuts.append((c - w / 2 - margin, c + w / 2 + margin, fz + op.get("z0", 0) - margin, fz + op.get("z0", 0) + op["h"] + margin))
        return cuts

    def gen_wall_finish(self, e):
        """Thin finish panel (paint colour, wallpaper, tile, mirror) on a wall face: wall spec, span [u0,u1], z [z0,z1].
        Split around every door and window in that wall, so the panel never covers an opening."""
        wall = e["wall"]
        u0, u1 = e["span"]
        z0, z1 = e["z"]
        dx, dy = _face_dir(wall)
        at = wall["at"]
        t = e.get("thick", 0.03)
        mat = self.mat(e["m"])
        cuts = [c for c in self._wall_cuts(wall, self._room_floor(e.get("room", ""))) if c[0] < u1 and c[1] > u0 and c[2] < z1 and c[3] > z0]
        # rectangles to place: start with the whole span, subtract each cut into left / right / below / above pieces
        rects = [(u0, u1, z0, z1)]
        for (cu0, cu1, cz0, cz1) in cuts:
            nxt = []
            for (a0, a1, b0, b1) in rects:
                if cu0 >= a1 or cu1 <= a0 or cz0 >= b1 or cz1 <= b0:
                    nxt.append((a0, a1, b0, b1))
                    continue
                if cu0 > a0:
                    nxt.append((a0, cu0, b0, b1))
                if cu1 < a1:
                    nxt.append((cu1, a1, b0, b1))
                m0, m1 = max(a0, cu0), min(a1, cu1)
                if cz0 > b0:
                    nxt.append((m0, m1, b0, cz0))
                if cz1 < b1:
                    nxt.append((m0, m1, cz1, b1))
            rects = nxt
        objs = []
        for (a0, a1, b0, b1) in rects:
            if a1 - a0 < 0.02 or b1 - b0 < 0.02:
                continue
            if wall["axis"] == "y":
                xs = sorted((at, at + dx * t))
                objs.append(box_ft(self.uid("panel_finish"), xs[0], a0, xs[1], a1, b0, b1, mat, self.col))
            else:
                ys = sorted((at, at + dy * t))
                objs.append(box_ft(self.uid("panel_finish"), a0, ys[0], a1, ys[1], b0, b1, mat, self.col))
        return objs

    # ================================================================== lighting fixtures
    def gen_downlight(self, e):
        """Recessed trimless downlight: a dark 3 in aperture disc flush with the ceiling plus a warm spot."""
        p = e["pos"]
        z = p[2] if len(p) > 2 else self.ceil_z(e.get("room", ""))
        aperture = cylinder_ft(self.uid("dl_aperture"), (p[0], p[1], z - 0.02), 0.13, 0.02, self.mat("black"), self.col, 16)
        self.light(type="spot", pos=(p[0], p[1], z - 0.05), aim=(p[0], p[1], z - 9.0), watts=e.get("watts", 9),
                   kelvin=e.get("kelvin", 2700), angle=e.get("angle", 42), blend=0.75, name="downlight")
        return [aperture]

    def gen_downlights(self, e):
        objs = []
        for p in e["positions"]:
            objs += self.gen_downlight({"pos": p if len(p) > 2 else [p[0], p[1], e["z"]], "watts": e.get("watts", 9),
                                        "kelvin": e.get("kelvin", 2700), "angle": e.get("angle", 42)})
        return objs

    def gen_sconce(self, e):
        """Brass cylinder wall sconce, opal diffuser top and bottom, projecting from a wall face."""
        wall = e["wall"]
        u, z = e["u"], e.get("z", 6.0)
        dx, dy = _face_dir(wall)
        at = wall["at"]
        if wall["axis"] == "y":
            cx, cy = at + dx * 0.32, u
            arm = box_ft(self.uid("sc_arm"), min(at, at + dx * 0.25), u - 0.05, max(at, at + dx * 0.25), u + 0.05, z - 0.05, z + 0.05, self.mat("brass"), self.col)
        else:
            cx, cy = u, at + dy * 0.32
            arm = box_ft(self.uid("sc_arm"), u - 0.05, min(at, at + dy * 0.25), u + 0.05, max(at, at + dy * 0.25), z - 0.05, z + 0.05, self.mat("brass"), self.col)
        r = e.get("radius", 0.18)
        h = e.get("height", 0.75)
        objs = [arm,
                cylinder_ft(self.uid("sc_body"), (cx, cy, z - h / 2), r, h, self.mat("brass"), self.col, 20),
                cylinder_ft(self.uid("sc_lens"), (cx, cy, z - h / 2 - 0.03), r * 0.8, 0.03, self.mat("lamp_glow" if e.get("on", True) else "lamp_shade"), self.col, 16),
                cylinder_ft(self.uid("sc_lens"), (cx, cy, z + h / 2), r * 0.8, 0.03, self.mat("lamp_glow" if e.get("on", True) else "lamp_shade"), self.col, 16)]
        if e.get("on", True):
            self.light(type="point", pos=(cx, cy, z), watts=e.get("watts", 10), kelvin=e.get("kelvin", 2700), radius=0.12, name="sconce")
        return objs

    def gen_picture_light(self, e):
        """Brass cylinder picture light on a short arm, aimed down the wall at the art."""
        wall = e["wall"]
        u, z = e["u"], e.get("z", 8.3)
        w = e.get("width", 0.85)
        dx, dy = _face_dir(wall)
        at = wall["at"]
        brass = self.mat("brass")
        objs = []
        if wall["axis"] == "y":
            cx, cy = at + dx * 0.45, u
            objs.append(box_ft(self.uid("pl_arm"), min(at, at + dx * 0.45), u - 0.04, max(at, at + dx * 0.45), u + 0.04, z + 0.2, z + 0.28, brass, self.col))
            objs.append(cylinder_ft(self.uid("pl_body"), (cx, cy - w / 2, z), 0.09, w, brass, self.col, 14, axis="Y"))
            objs.append(box_ft(self.uid("pl_lens"), cx - 0.05, cy - w / 2 + 0.05, cx + 0.05, cy + w / 2 - 0.05, z - 0.1, z - 0.085, self.mat("lamp_glow"), self.col))
            aim = (at, u, e.get("aim_z", z - 3.2))
        else:
            cx, cy = u, at + dy * 0.45
            objs.append(box_ft(self.uid("pl_arm"), u - 0.04, min(at, at + dy * 0.45), u + 0.04, max(at, at + dy * 0.45), z + 0.2, z + 0.28, brass, self.col))
            objs.append(cylinder_ft(self.uid("pl_body"), (cx - w / 2, cy, z), 0.09, w, brass, self.col, 14, axis="X"))
            objs.append(box_ft(self.uid("pl_lens"), cx - w / 2 + 0.05, cy - 0.05, cx + w / 2 - 0.05, cy + 0.05, z - 0.1, z - 0.085, self.mat("lamp_glow"), self.col))
            aim = (u, at, e.get("aim_z", z - 3.2))
        self.light(type="spot", pos=(cx, cy, z - 0.1), aim=aim, watts=e.get("watts", 4.5), kelvin=2700, angle=e.get("angle", 50), blend=0.9, name="piclight")
        return objs

    def gen_floor_lamp(self, e):
        """Brass floor lamp with a drum or cone shade; on/off."""
        p = e["pos"]
        h = e.get("height", 5.2)
        brass = self.mat("brass")
        kind = e.get("kind", "drum")
        on = e.get("on", True)
        objs = [cylinder_ft(self.uid("fl_base"), p, 0.5, 0.08, brass, self.col, 24),
                cylinder_ft(self.uid("fl_stem"), (p[0], p[1], p[2] + 0.08), 0.045, h - 1.3, brass, self.col, 10)]
        if kind == "drum":
            shade = cylinder_ft(self.uid("fl_shade"), (p[0], p[1], p[2] + h - 1.25), 0.7, 1.05, self.mat("linen_white"), self.col, 28)
        else:
            shade = cylinder_ft(self.uid("fl_shade"), (p[0], p[1], p[2] + h - 1.25), 0.75, 1.0, brass, self.col, 28)
            shade.scale = (1, 1, 1)
        objs.append(shade)
        if on:
            objs.append(sphere_ft(self.uid("fl_bulb"), (p[0], p[1], p[2] + h - 0.75), 0.18, self.mat("lamp_glow"), self.col, 12, 8))
            self.light(type="point", pos=(p[0], p[1], p[2] + h - 0.75), watts=e.get("watts", 32), kelvin=2700, radius=0.3, name="floor_lamp")
        return objs

    def gen_pendant_cone(self, e):
        """Brass cone pendant (bar, games table)."""
        p = e["pos"]           # bottom of the shade
        drop = e.get("drop", 4.0)
        brass = self.mat("brass")
        objs = [cylinder_ft(self.uid("pc_cord"), (p[0], p[1], p[2]), 0.015, drop, self.mat("black"), self.col, 6),
                cylinder_ft(self.uid("pc_canopy"), (p[0], p[1], p[2] + drop - 0.08), 0.2, 0.08, brass, self.col, 16)]
        cone = cylinder_ft(self.uid("pc_shade"), (p[0], p[1], p[2]), 0.5, 0.6, brass, self.col, 24)
        objs.append(cone)
        objs.append(cylinder_ft(self.uid("pc_lens"), (p[0], p[1], p[2] + 0.01), 0.42, 0.02, self.mat("lamp_glow"), self.col, 20))
        self.light(type="spot", pos=(p[0], p[1], p[2] + 0.1), aim=(p[0], p[1], p[2] - 4), watts=e.get("watts", 30), kelvin=2700, angle=80, blend=0.7, name="cone_pendant")
        return objs

    def gen_led_strip(self, e):
        """Thin emissive strip with an area light: b = [x0,y0,x1,y1,z0,z1] (thin in one axis), aims down by default."""
        b = e["b"]
        objs = [box_ft(self.uid("led_strip"), *b, mat=self.mat(e.get("m", "lamp_glow")), collection=self.col)]
        cx, cy, cz = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2, (b[4] + b[5]) / 2
        rot = tuple(math.radians(a) for a in e.get("rot", (0, 0, 0)))
        self.light(type="area", pos=(cx, cy, cz - 0.05 if not e.get("rot") else cz), size=max(b[2] - b[0], 0.1), size_y=max(b[3] - b[1], 0.1),
                   shape="RECTANGLE", watts=e.get("watts", 8), kelvin=e.get("kelvin", 2700), rot=rot, name="led")
        return objs

    def gen_shop_light(self, e):
        """4 ft linear LED shop light hung from the ceiling."""
        p = e["pos"]  # centre, z = fixture bottom
        L = e.get("length", 4.0)
        rot = e.get("rot_z", 0)
        objs = [box_centered(self.uid("shop_hsg"), (p[0], p[1], p[2] + 0.15), (L, 0.45, 0.25), rot, self.mat("stainless"), self.col),
                box_centered(self.uid("shop_lens"), (p[0], p[1], p[2] + 0.01), (L - 0.1, 0.35, 0.02), rot, self.mat("lamp_glow"), self.col)]
        self.light(type="area", pos=(p[0], p[1], p[2] - 0.02), size=L if rot % 180 == 0 else 0.4, size_y=0.4 if rot % 180 == 0 else L,
                   shape="RECTANGLE", watts=e.get("watts", 45), kelvin=e.get("kelvin", 4000), rot=(0, 0, 0), name="shoplight")
        return objs

    # ================================================================== tables and seating
    def gen_console(self, e):
        """Walnut console table with tapered legs; optional objects (lamp, bowl, mail stack)."""
        p = e["pos"]
        L, D, H = e.get("length", 5.0), e.get("depth", 1.0), e.get("height", 2.7)
        rot = e.get("rot_z", 0)
        wood = self.mat("walnut_h")
        objs = [box_centered(self.uid("con_top"), (p[0], p[1], p[2] + H - 0.06), (L, D, 0.12), rot, wood, self.col),
                box_centered(self.uid("con_apron"), (p[0], p[1], p[2] + H - 0.35), (L - 0.3, D - 0.25, 0.45), rot, wood, self.col)]
        r = math.radians(rot)
        for sx in (-1, 1):
            for sy in (-1, 1):
                lx, ly = sx * (L / 2 - 0.2), sy * (D / 2 - 0.15)
                wx, wy = p[0] + lx * math.cos(r) - ly * math.sin(r), p[1] + lx * math.sin(r) + ly * math.cos(r)
                objs.append(cylinder_ft(self.uid("con_leg"), (wx, wy, p[2]), 0.06, H - 0.12, wood, self.col, 10))
        top = p[2] + H
        items = e.get("items", ["lamp", "bowl", "mail"])
        if "lamp" in items:
            lx = -L / 2 + 0.7
            objs += self.gen_table_lamp({"pos": (p[0] + lx * math.cos(r), p[1] + lx * math.sin(r), top), "height": 2.0, "base_r": 0.25, "shade_r": 0.5,
                                         "base_m": e.get("lamp_base_m", "brass"), "watts": e.get("lamp_watts", 28)})
        if "bowl" in items:
            bw = sphere_ft(self.uid("con_bowl"), (p[0] + 0.3 * math.cos(r), p[1] + 0.3 * math.sin(r), top + 0.16), 0.5, self.mat(e.get("bowl_m", "ceramic_white")), self.col)
            bw.scale = (1, 1, 0.32)
            objs.append(bw)
        if "mail" in items:
            ux = L / 2 - 1.0
            for k in range(4):
                objs.append(box_centered(self.uid("con_mail"), (p[0] + ux * math.cos(r), p[1] + ux * math.sin(r), top + 0.012 + k * 0.02),
                                         (0.75, 0.95, 0.02), rot + k * 4 - 6, self.mat("paper"), self.col))
        if "object" in items:
            objs.append(cylinder_ft(self.uid("con_obj"), (p[0] + 1.2 * math.cos(r), p[1] + 1.2 * math.sin(r), top), 0.2, 0.9, self.mat("teal"), self.col, 20))
        return objs

    def gen_window_seat(self, e):
        """Built-in bench under a window with a cushion, pillows and books. b = bench box; cushion_m."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        objs = [box_ft(self.uid("ws_box"), x0, y0, x1, y1, z0, z1 - 0.05, wood, self.col)]
        # drawer reveals on the room-facing side
        face = e.get("face", "+y")
        nd = max(1, int((x1 - x0) / 2.0)) if face in ("-y", "+y") else max(1, int((y1 - y0) / 2.0))
        for i in range(1, nd):
            if face in ("-y", "+y"):
                u = x0 + i * (x1 - x0) / nd
                fy = (y1 - 0.005, y1 + 0.01) if face == "+y" else (y0 - 0.01, y0 + 0.005)
                objs.append(box_ft(self.uid("reveal"), u - 0.01, fy[0], u + 0.01, fy[1], z0 + 0.15, z1 - 0.2, self.mat("black"), self.col))
            else:
                u = y0 + i * (y1 - y0) / nd
                fx = (x1 - 0.005, x1 + 0.01) if face == "+x" else (x0 - 0.01, x0 + 0.005)
                objs.append(box_ft(self.uid("reveal"), fx[0], u - 0.01, fx[1], u + 0.01, z0 + 0.15, z1 - 0.2, self.mat("black"), self.col))
        cush = box_ft(self.uid("bench_cush"), x0 + 0.05, y0 + 0.05, x1 - 0.05, y1 - 0.05, z1 - 0.05, z1 + e.get("cushion_t", 0.33), self.mat(e.get("cushion_m", "wool_mustard")), self.col)
        objs.append(cush)
        rng = random.Random(e.get("seed", 4))
        mats = e.get("pillow_mats", ["velvet_teal", "wool_oatmeal", "oxblood"])
        for i in range(e.get("pillows", 2)):
            s = rng.uniform(1.2, 1.6)
            # pillows lean against the wall side
            if face in ("-y", "+y"):
                px = rng.uniform(x0 + s / 2 + 0.2, x1 - s / 2 - 0.2)
                py = y0 + 0.45 if face == "+y" else y1 - 0.45
                ob = box_centered(self.uid("pillow"), (px, py, z1 + 0.33 + s * 0.45), (s, 0.35, s * 0.9), rng.uniform(-8, 8), self.mat(mats[i % len(mats)]), self.col)
                ob.rotation_euler = (math.radians(-18 if face == "+y" else 18), 0, math.radians(rng.uniform(-8, 8)))
            else:
                py = rng.uniform(y0 + s / 2 + 0.2, y1 - s / 2 - 0.2)
                px = x0 + 0.45 if face == "+x" else x1 - 0.45
                ob = box_centered(self.uid("pillow"), (px, py, z1 + 0.33 + s * 0.45), (0.35, s, s * 0.9), rng.uniform(-8, 8), self.mat(mats[i % len(mats)]), self.col)
                ob.rotation_euler = (0, math.radians(18 if face == "+x" else -18), math.radians(rng.uniform(-8, 8)))
            objs.append(ob)
        if e.get("books", 2):
            bx = x0 + (x1 - x0) * 0.72
            by = (y0 + y1) / 2
            for k in range(e.get("books", 2)):
                objs.append(box_centered(self.uid("ws_book"), (bx, by, z1 + 0.33 + 0.06 + k * 0.11), (0.75, 1.0, 0.11), rng.uniform(-14, 14), self.mat(rng.choice(["book_a", "book_d", "book_g"])), self.col))
        if e.get("throw"):
            objs.append(box_centered(self.uid("throw"), (x0 + 1.0, (y0 + y1) / 2, z1 + 0.33 + 0.12), (1.6, y1 - y0 - 0.4, 0.24), 3, self.mat(e["throw"]), self.col))
        return objs

    def gen_lounge_chair(self, e):
        """Mid-century armchair stand-in: walnut frame, upholstered seat and back, angled; pos = centre bottom."""
        p = e["pos"]
        rot = e.get("rot_z", 0)
        fab = self.mat(e.get("m", "wool_mustard"))
        wood = self.mat("walnut_h")
        W, D = e.get("width", 2.7), e.get("depth", 2.8)
        objs = []

        def part(name, x0, y0, x1, y1, z0, z1, mat):
            ob = box_local(self.uid(name), (0, 0, 0), (x1 - x0, y1 - y0, z1 - z0), 0, mat, self.col)
            ob.data.transform(Matrix.Translation((m(x0 - W / 2), m(y0 - D / 2), m(z0))))
            ob.location = (m(p[0]), m(p[1]), m(p[2]))
            ob.rotation_euler = (0, 0, math.radians(rot))
            objs.append(ob)
        # front is -y in local space (sitter faces -y)
        part("ch_seat_cushion", 0.25, 0.3, W - 0.25, D - 0.5, 1.05, 1.45, fab)
        part("ch_back", 0.25, D - 0.65, W - 0.25, D - 0.3, 1.3, 2.9, fab)
        part("ch_arm", 0.0, 0.3, 0.22, D - 0.3, 1.5, 2.0, wood)
        part("ch_arm", W - 0.22, 0.3, W, D - 0.3, 1.5, 2.0, wood)
        part("ch_frame", 0.1, 0.35, W - 0.1, D - 0.45, 0.85, 1.05, wood)
        for lx in (0.2, W - 0.2):
            part("ch_leg", lx - 0.06, 0.45, lx + 0.06, 0.57, 0, 1.5, wood)
            part("ch_leg", lx - 0.06, D - 0.55, lx + 0.06, D - 0.43, 0, 1.5, wood)
        if e.get("throw_m"):
            part("throw", W - 0.7, 0.6, W + 0.15, D - 0.6, 1.95, 2.15, self.mat(e["throw_m"]))
        return objs

    def gen_dining_chair(self, e):
        """Molded walnut shell chair with an upholstered seat, four splayed legs."""
        p = e["pos"]
        rot = e.get("rot_z", 0)
        wood = self.mat("walnut_h")
        fab = self.mat(e.get("m", "wool_mustard"))
        objs = []
        W, D = 1.6, 1.7

        def part(name, x0, y0, x1, y1, z0, z1, mat, rx=0):
            ob = box_local(self.uid(name), (0, 0, 0), (x1 - x0, y1 - y0, z1 - z0), 0, mat, self.col)
            ob.data.transform(Matrix.Translation((m(x0 - W / 2), m(y0 - D / 2), m(z0))))
            if rx:
                ob.data.transform(Matrix.Rotation(math.radians(rx), 4, "X"))
            ob.location = (m(p[0]), m(p[1]), m(p[2]))
            ob.rotation_euler = (0, 0, math.radians(rot))
            objs.append(ob)
        part("dc_seat", 0.05, 0.1, W - 0.05, D - 0.25, 1.45, 1.55, wood)
        part("dc_pad", 0.12, 0.2, W - 0.12, D - 0.3, 1.55, 1.68, fab)
        part("dc_back", 0.12, D - 0.32, W - 0.12, D - 0.2, 1.7, 2.75, wood, rx=6)
        for lx in (0.2, W - 0.2):
            for ly in (0.25, D - 0.35):
                objs.append(beam_between(self.uid("dc_leg"), (p[0] + (lx - W / 2) * math.cos(math.radians(rot)) - (ly - D / 2) * math.sin(math.radians(rot)),
                                                            p[1] + (lx - W / 2) * math.sin(math.radians(rot)) + (ly - D / 2) * math.cos(math.radians(rot)), p[2]),
                                         (p[0] + (lx - W / 2) * 0.55 * math.cos(math.radians(rot)) - (ly - D / 2) * 0.55 * math.sin(math.radians(rot)),
                                          p[1] + (lx - W / 2) * 0.55 * math.sin(math.radians(rot)) + (ly - D / 2) * 0.55 * math.cos(math.radians(rot)), p[2] + 1.45),
                                         0.08, 0.08, wood, self.col))
        return objs

    def gen_task_chair(self, e):
        """Mid-century office chair: five-star base on casters, gas lift, leather seat, walnut back."""
        p = e["pos"]
        rot = math.radians(e.get("rot_z", 0))
        chrome = self.mat("chrome")
        objs = [cylinder_ft(self.uid("tc_hub"), (p[0], p[1], p[2] + 0.1), 0.15, 0.25, chrome, self.col, 12),
                cylinder_ft(self.uid("tc_lift"), (p[0], p[1], p[2] + 0.3), 0.07, 1.2, chrome, self.col, 10)]
        for i in range(5):
            a = rot + i * 2 * math.pi / 5
            end = (p[0] + math.cos(a) * 1.05, p[1] + math.sin(a) * 1.05, p[2] + 0.12)
            objs.append(beam_between(self.uid("tc_spoke"), (p[0], p[1], p[2] + 0.22), end, 0.1, 0.08, chrome, self.col))
            objs.append(sphere_ft(self.uid("tc_caster"), (end[0], end[1], p[2] + 0.12), 0.12, self.mat("black"), self.col, 10, 6))
        seat = box_centered(self.uid("tc_seat"), (p[0], p[1], p[2] + 1.6), (1.6, 1.6, 0.25), e.get("rot_z", 0), self.mat(e.get("m", "leather_brown")), self.col)
        objs.append(seat)
        # back, offset toward -y local (sitter faces +y local by default; rot_z turns it)
        bx, by = p[0] - math.sin(rot) * 0.7 * -1, p[1] + math.cos(rot) * -0.7
        back = box_centered(self.uid("tc_back"), (bx, by, p[2] + 2.55), (1.5, 0.15, 1.5), e.get("rot_z", 0), self.mat("walnut_h"), self.col)
        objs.append(back)
        pad = box_centered(self.uid("tc_pad"), (bx - math.cos(rot) * 0 + math.sin(rot) * 0.1 * 0, by + math.cos(rot) * 0.1, p[2] + 2.5), (1.3, 0.12, 1.2), e.get("rot_z", 0), self.mat(e.get("m", "leather_brown")), self.col)
        objs.append(pad)
        for sx in (-1, 1):
            ax, ay = p[0] + math.cos(rot) * sx * 0.85, p[1] + math.sin(rot) * sx * 0.85
            objs.append(box_centered(self.uid("tc_armrest"), (ax, ay, p[2] + 2.25), (0.15, 1.0, 0.1), e.get("rot_z", 0), self.mat("walnut_h"), self.col))
            objs.append(box_centered(self.uid("tc_armpost"), (ax, ay + 0.2, p[2] + 1.95), (0.1, 0.1, 0.5), e.get("rot_z", 0), chrome, self.col))
        return objs

    def gen_kid_chair(self, e):
        p = e["pos"]
        wood = self.mat(e.get("m", "walnut_h"))
        rot = e.get("rot_z", 0)
        objs = [box_centered(self.uid("kc_seat"), (p[0], p[1], p[2] + 1.0), (1.1, 1.1, 0.08), rot, wood, self.col),
                box_centered(self.uid("kc_back"), (p[0] - math.sin(math.radians(rot)) * -0.5, p[1] + math.cos(math.radians(rot)) * -0.5, p[2] + 1.6), (1.0, 0.08, 1.1), rot, wood, self.col)]
        for sx in (-1, 1):
            for sy in (-1, 1):
                objs.append(cylinder_ft(self.uid("kc_leg"), (p[0] + sx * 0.45, p[1] + sy * 0.45, p[2]), 0.04, 1.0, wood, self.col, 8))
        return objs

    def gen_round_table(self, e):
        p = e["pos"]
        R, H = e.get("radius", 1.5), e.get("height", 1.4)
        wood = self.mat(e.get("m", "walnut_h"))
        objs = [cylinder_ft(self.uid("rt_top"), (p[0], p[1], p[2] + H - 0.1), R, 0.1, wood, self.col, 40),
                cylinder_ft(self.uid("rt_stem"), (p[0], p[1], p[2] + 0.1), 0.15, H - 0.2, wood, self.col, 14),
                cylinder_ft(self.uid("rt_foot"), p, R * 0.55, 0.1, wood, self.col, 30)]
        return objs

    def gen_square_table(self, e):
        p = e["pos"]
        L, D, H = e.get("length", 4.0), e.get("depth", 4.0), e.get("height", 2.45)
        wood = self.mat(e.get("m", "walnut_h"))
        objs = [box_centered(self.uid("sq_top"), (p[0], p[1], p[2] + H - 0.08), (L, D, 0.16), e.get("rot_z", 0), wood, self.col)]
        for sx in (-1, 1):
            for sy in (-1, 1):
                objs.append(box_centered(self.uid("sq_leg"), (p[0] + sx * (L / 2 - 0.2), p[1] + sy * (D / 2 - 0.2), p[2]), (0.2, 0.2, H - 0.16), 0, wood, self.col))
        return objs

    def gen_ottoman(self, e):
        p = e["pos"]
        objs = [box_centered(self.uid("ott_cushion"), (p[0], p[1], p[2] + 1.05), (2.1, 1.8, 0.45), e.get("rot_z", 0), self.mat(e.get("m", "leather_brown")), self.col),
                box_centered(self.uid("ott_shell"), (p[0], p[1], p[2] + 0.75), (2.15, 1.85, 0.15), e.get("rot_z", 0), self.mat("walnut_h"), self.col),
                cylinder_ft(self.uid("ott_base"), p, 0.7, 0.7, self.mat("steel_black"), self.col, 20)]
        if e.get("throw_m"):
            objs.append(box_centered(self.uid("throw"), (p[0] + 0.3, p[1], p[2] + 1.35), (1.4, 1.9, 0.18), 6, self.mat(e["throw_m"]), self.col))
        return objs

    def gen_beanbag(self, e):
        p = e["pos"]
        bb = sphere_ft(self.uid("beanbag"), (p[0], p[1], p[2] + 0.75), 1.4, self.mat(e.get("m", "velvet_teal")), self.col, 20, 12)
        bb.scale = (1, 1, 0.55)
        return [bb]

    # ================================================================== beds
    def gen_platform_bed(self, e):
        """Walnut platform bed with headboard, rumpled duvet, pillows, folded blanket. Head toward +Y in local space."""
        p = e["pos"]                # centre of the mattress footprint at floor level
        W, L = e.get("width", 6.5), e.get("length", 7.0)
        rot = e.get("rot_z", 0)
        plat_h = e.get("platform_h", 1.0)
        matt_top = e.get("mattress_top", 2.0)
        hb_w, hb_h = e.get("headboard_w", 9.0), e.get("headboard_h", 4.0)
        wood = self.mat("walnut_h")
        lin = self.mat(e.get("sheet_m", "linen_white"))
        duv = self.mat(e.get("duvet_m", "linen_white"))
        rng = random.Random(e.get("seed", 8))
        objs = []

        def part(name, x0, y0, x1, y1, z0, z1, mat, rz=0.0, rx=0.0):
            ob = box_local(self.uid(name), (0, 0, 0), (x1 - x0, y1 - y0, z1 - z0), 0, mat, self.col)
            mtx = Matrix.Translation((m(x0 - W / 2), m(y0 - L / 2), m(z0)))
            if rz or rx:
                c = Matrix.Translation((m((x0 + x1) / 2 - W / 2), m((y0 + y1) / 2 - L / 2), m(z0)))
                mtx = c @ Matrix.Rotation(math.radians(rz), 4, "Z") @ Matrix.Rotation(math.radians(rx), 4, "X") @ c.inverted() @ mtx
            ob.data.transform(mtx)
            ob.location = (m(p[0]), m(p[1]), m(p[2]))
            ob.rotation_euler = (0, 0, math.radians(rot))
            objs.append(ob)
            return ob
        part("bed_platform", -0.5, -0.4, W + 0.5, L, plat_h - 0.35, plat_h, wood)
        part("bed_plinth", 0.4, 0.5, W - 0.4, L - 0.3, 0, plat_h - 0.35, self.mat("black"))
        part("bed_mattress", 0, 0, W, L, plat_h, matt_top, lin)
        # fitted sheet edge line
        part("bed_sheet", -0.02, -0.02, W + 0.02, L + 0.02, plat_h + 0.02, matt_top - 0.35, lin)
        # duvet: thrown back on one side (state 'thrown') or flat
        # the duvet drapes over the exposed edges: thin drop panels hang from the top slab down the sides
        drop = 0.85
        if e.get("duvet", "flat") == "thrown":
            part("bed_duvet", W * 0.42, -0.3, W + 0.35, L - 2.3, matt_top, matt_top + 0.42, duv, rz=rng.uniform(-3, 3))
            part("bed_duvet_drop", W + 0.2, -0.3, W + 0.36, L - 2.3, matt_top - drop, matt_top + 0.1, duv)
            part("bed_duvet_drop", W * 0.42, -0.31, W + 0.36, -0.15, matt_top - drop, matt_top + 0.1, duv)
            part("bed_duvet", W * 0.1, L * 0.35, W * 0.55, L - 2.4, matt_top, matt_top + 0.6, duv, rz=rng.uniform(-12, -4))  # folded-back roll
            part("bed_duvet", -0.3, -0.3, W * 0.5, L * 0.35, matt_top, matt_top + 0.25, duv, rz=rng.uniform(-2, 2))
            part("bed_duvet_drop", -0.31, -0.3, -0.15, L * 0.35, matt_top - drop * 0.6, matt_top + 0.05, duv)
        else:
            # made bed: one duvet slab to just below the pillows, its top edge folded back as a soft roll,
            # dropping over both sides and the foot
            part("bed_duvet", -0.3, -0.3, W + 0.3, L - 2.2, matt_top, matt_top + 0.35, duv, rz=rng.uniform(-1, 1))
            part("bed_duvet_fold", -0.3, L - 3.0, W + 0.3, L - 2.15, matt_top + 0.3, matt_top + 0.75, duv)
            part("bed_duvet_drop", W + 0.15, -0.3, W + 0.31, L - 2.2, matt_top - drop, matt_top + 0.1, duv)
            part("bed_duvet_drop", -0.31, -0.3, -0.15, L - 2.2, matt_top - drop, matt_top + 0.1, duv)
            part("bed_duvet_drop", -0.3, -0.31, W + 0.3, -0.15, matt_top - drop, matt_top + 0.1, duv)
        # pillows: two rows
        pm = e.get("pillow_mats", ["linen_white", "linen_white", "olive_paint", "olive_paint"])
        pw = (W - 0.6) / 2
        for i, x in enumerate((0.2, W / 2 + 0.1)):
            part("bed_pillow", x, L - 2.05, x + pw, L - 0.25, matt_top, matt_top + 0.55, self.mat(pm[i % len(pm)]), rz=rng.uniform(-3, 3))
            part("bed_pillow", x + 0.15, L - 1.35, x + pw - 0.15, L - 0.15, matt_top + 0.5, matt_top + 1.05, self.mat(pm[(i + 2) % len(pm)]), rx=-25)
        if e.get("blanket_m"):
            # folded wool throw across the foot: two thin layers, the lower one hanging over the end
            bm = self.mat(e["blanket_m"])
            top = matt_top + 0.36
            part("bed_throw", W * 0.3, -0.2, W + 0.4, 1.6, top, top + 0.16, bm, rz=rng.uniform(-4, 4))
            part("bed_throw", W * 0.36, 0.05, W + 0.3, 1.45, top + 0.16, top + 0.3, bm, rz=rng.uniform(-4, 4))
            part("bed_throw_drop", W * 0.3, -0.36, W + 0.4, -0.2, top - 0.9, top + 0.16, bm)
        if hb_w:
            part("bed_headboard", W / 2 - hb_w / 2, L + 0.02, W / 2 + hb_w / 2, L + 0.3, 0, hb_h, wood)
            part("bed_headpad", W / 2 - hb_w / 2 + 0.3, L - 0.1, W / 2 + hb_w / 2 - 0.3, L + 0.02, plat_h + 0.6, hb_h - 0.3, self.mat(e.get("headpad_m", "leather_brown")))
        return objs

    def gen_slippers(self, e):
        p = e["pos"]
        rot = e.get("rot_z", 0)
        mat = self.mat(e.get("m", "wool_oatmeal"))
        objs = []
        for i, dx in enumerate((-0.28, 0.28)):
            ob = box_centered(self.uid("slipper"), (p[0] + dx, p[1], p[2] + 0.06), (0.36, 0.95, 0.12), rot + (8 if i else -5), mat, self.col)
            objs.append(ob)
            objs.append(box_centered(self.uid("slipper_vamp"), (p[0] + dx, p[1] + 0.25, p[2] + 0.17), (0.34, 0.4, 0.1), rot + (8 if i else -5), mat, self.col))
        return objs

    def gen_kid_bed(self, e):
        """Twin XL platform bed against a wall: b = mattress footprint box (z0 floor, z1 mattress top)."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        rng = random.Random(e.get("seed", 5))
        objs = [box_ft(self.uid("kb_platform"), x0 - 0.2, y0 - 0.2, x1 + 0.2, y1 + 0.2, z0 + 0.5, z0 + 0.95, wood, self.col),
                box_ft(self.uid("kb_plinth"), x0 + 0.3, y0 + 0.3, x1 - 0.3, y1 - 0.3, z0, z0 + 0.5, self.mat("black"), self.col),
                box_ft(self.uid("bed_mattress"), x0, y0, x1, y1, z0 + 0.95, z1, self.mat("linen_white"), self.col)]
        head = e.get("head", "+y")
        duv = self.mat(e.get("duvet_m", "wool_mustard"))
        if head in ("+y", "-y"):
            L = y1 - y0
            if head == "+y":
                objs.append(box_ft(self.uid("bed_duvet"), x0 - 0.15, y0 - 0.15, x1 + 0.15, y1 - 1.8, z1, z1 + 0.35, duv, self.col))
                objs.append(box_ft(self.uid("bed_pillow"), x0 + 0.3, y1 - 1.6, x1 - 0.3, y1 - 0.2, z1, z1 + 0.5, self.mat("linen_white"), self.col))
                hb = box_ft(self.uid("kb_headboard"), x0 - 0.2, y1 + 0.02, x1 + 0.2, y1 + 0.25, z0, z0 + 3.2, wood, self.col)
            else:
                objs.append(box_ft(self.uid("bed_duvet"), x0 - 0.15, y0 + 1.8, x1 + 0.15, y1 + 0.15, z1, z1 + 0.35, duv, self.col))
                objs.append(box_ft(self.uid("bed_pillow"), x0 + 0.3, y0 + 0.2, x1 - 0.3, y0 + 1.6, z1, z1 + 0.5, self.mat("linen_white"), self.col))
                hb = box_ft(self.uid("kb_headboard"), x0 - 0.2, y0 - 0.25, x1 + 0.2, y0 - 0.02, z0, z0 + 3.2, wood, self.col)
        else:
            if head == "+x":
                objs.append(box_ft(self.uid("bed_duvet"), x0 - 0.15, y0 - 0.15, x1 - 1.8, y1 + 0.15, z1, z1 + 0.35, duv, self.col))
                objs.append(box_ft(self.uid("bed_pillow"), x1 - 1.6, y0 + 0.3, x1 - 0.2, y1 - 0.3, z1, z1 + 0.5, self.mat("linen_white"), self.col))
                hb = box_ft(self.uid("kb_headboard"), x1 + 0.02, y0 - 0.2, x1 + 0.25, y1 + 0.2, z0, z0 + 3.2, wood, self.col)
            else:
                objs.append(box_ft(self.uid("bed_duvet"), x0 + 1.8, y0 - 0.15, x1 + 0.15, y1 + 0.15, z1, z1 + 0.35, duv, self.col))
                objs.append(box_ft(self.uid("bed_pillow"), x0 + 0.2, y0 + 0.3, x0 + 1.6, y1 - 0.3, z1, z1 + 0.5, self.mat("linen_white"), self.col))
                hb = box_ft(self.uid("kb_headboard"), x0 - 0.25, y0 - 0.2, x0 - 0.02, y1 + 0.2, z0, z0 + 3.2, wood, self.col)
        objs.append(hb)
        # stuffed animal: a small ellipsoid pair
        cx, cy = (x0 + x1) / 2 + rng.uniform(-0.8, 0.8), (y0 + y1) / 2 + rng.uniform(-1, 1)
        body = sphere_ft(self.uid("plush"), (cx, cy, z1 + 0.35 + 0.35), 0.4, self.mat("wool_oatmeal"), self.col, 12, 8)
        body.scale = (1, 1.2, 0.8)
        headp = sphere_ft(self.uid("plush"), (cx, cy + 0.45, z1 + 0.35 + 0.55), 0.3, self.mat("wool_oatmeal"), self.col, 12, 8)
        objs += [body, headp]
        return objs

    def gen_daybed(self, e):
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        objs = [box_ft(self.uid("db_box"), x0, y0, x1, y1, z0, z1 - 0.4, wood, self.col),
                box_ft(self.uid("bench_cush"), x0 + 0.05, y0 + 0.05, x1 - 0.05, y1 - 0.05, z1 - 0.4, z1, self.mat(e.get("cushion_m", "olive_paint")), self.col)]
        objs += self.gen_cushions({"b": [x0 + 0.3, y0 + 0.2, x1 - 0.3, y1 - 0.3], "z": z1, "back": e.get("back", "+y"), "count": e.get("pillows", 5), "seed": e.get("seed", 3),
                                   "mats": ["wool_mustard", "velvet_teal", "wool_oatmeal", "oxblood", "olive_paint"]})
        return objs

    def gen_nightstand2(self, e):
        """Walnut nightstand 2 x 1.5 x 2.2 with a drawer, optional lamp on/off and objects."""
        p = e["pos"]
        wood = self.mat("walnut_h")
        W, D, H = 2.0, 1.5, 2.2
        rot = e.get("rot_z", 0)
        objs = [box_centered(self.uid("ns_body"), (p[0], p[1], p[2] + 0.5 + (H - 0.5) / 2), (W, D, H - 0.5), rot, wood, self.col)]
        for sx in (-1, 1):
            for sy in (-1, 1):
                objs.append(cylinder_ft(self.uid("ns_leg"), (p[0] + sx * (W / 2 - 0.15), p[1] + sy * (D / 2 - 0.15), p[2]), 0.05, 0.5, wood, self.col, 8))
        top = p[2] + H
        r = math.radians(rot)
        if e.get("lamp", True):
            lx = -0.45
            objs += self.gen_table_lamp({"pos": (p[0] + lx * math.cos(r), p[1] + lx * math.sin(r), top), "height": 1.15, "base_r": 0.16, "shade_r": 0.33,
                                         "base_m": "brass", "watts": e.get("lamp_watts", 22) if e.get("on", True) else 0})
        for it in e.get("items", []):
            if it == "books":
                for k in range(3):
                    objs.append(box_centered(self.uid("ns_book"), (p[0] + 0.45 * math.cos(r), p[1] + 0.45 * math.sin(r), top + 0.06 + k * 0.12), (0.7, 0.95, 0.12), rot + k * 5, self.mat(["book_b", "book_e", "book_h"][k]), self.col))
                objs.append(box_centered(self.uid("ns_glasses"), (p[0] + 0.45 * math.cos(r), p[1] + 0.45 * math.sin(r), top + 0.42), (0.5, 0.15, 0.03), rot + 20, self.mat("black"), self.col))
            elif it == "glass":
                objs.append(cylinder_ft(self.uid("ns_glass"), (p[0] + 0.1 * math.cos(r) - 0.4 * math.sin(r), p[1] + 0.1 * math.sin(r) + 0.4 * math.cos(r), top), 0.13, 0.33, self.mat("glass"), get_collection("glass"), 16))
            elif it == "watch":
                objs.append(box_centered(self.uid("ns_strap"), (p[0] + 0.45 * math.cos(r), p[1] + 0.45 * math.sin(r), top + 0.01), (0.65, 0.09, 0.02), rot + 35, self.mat("leather_brown"), self.col))
                objs.append(cylinder_ft(self.uid("ns_watch"), (p[0] + 0.45 * math.cos(r), p[1] + 0.45 * math.sin(r), top + 0.01), 0.09, 0.04, self.mat("brass"), self.col, 16))
            elif it == "phone":
                objs.append(box_centered(self.uid("ns_pad"), (p[0] + 0.15 * math.cos(r) + 0.35 * math.sin(r), p[1] + 0.15 * math.sin(r) - 0.35 * math.cos(r), top + 0.02), (0.4, 0.4, 0.04), rot, self.mat("black"), self.col))
                objs.append(box_centered(self.uid("ns_phone"), (p[0] + 0.15 * math.cos(r) + 0.35 * math.sin(r), p[1] + 0.15 * math.sin(r) - 0.35 * math.cos(r), top + 0.06), (0.24, 0.5, 0.03), rot + 8, self.mat("screen_dark"), self.col))
        return objs

    # ================================================================== kitchen
    def gen_kitchen2(self, e):
        """The spec kitchen: cooking wall on the east wall (X 22 face), south run, island (work + table end), nook.
        All coordinates are the spec's; the entry carries only overrides."""
        objs = []
        z = e.get("z", 0.0)
        wood = self.mat("walnut_h")
        olive = self.mat("olive_paint")
        soap = self.mat("soapstone")
        black = self.mat("steel_black")
        ss = self.mat("stainless")
        brass = self.mat("brass")
        glassc = get_collection("glass")
        wx = 21.75                     # cooking wall face (the X 22 partition is 3 in thick on this side)
        # --- cooking wall: base run Y 19.5-25 (range at 19.5-22.5), counter, uppers, columns 25-30
        objs.append(box_ft(self.uid("k_filler"), wx - 2.1, 19.0, wx, 19.5, z, z + 3.0, wood, self.col))
        # range 36 in: stainless body, black glass top, oven door with handle
        objs.append(box_ft(self.uid("k_range"), wx - 2.1, 19.5, wx - 0.05, 22.5, z + 0.3, z + 2.95, ss, self.col))
        objs.append(box_ft(self.uid("k_range_toe"), wx - 1.9, 19.6, wx - 0.05, 22.4, z, z + 0.3, black, self.col))
        objs.append(box_ft(self.uid("k_cooktop"), wx - 2.15, 19.45, wx - 0.05, 22.55, z + 2.95, z + 3.02, self.mat("screen_dark"), self.col))
        for cy in (20.2, 21.0, 21.8):
            objs.append(cylinder_ft(self.uid("k_ring"), (wx - 1.35, cy, z + 3.02), 0.28, 0.004, self.mat("black"), self.col, 24))
        objs.append(box_ft(self.uid("k_oven_glass"), wx - 2.12, 19.7, wx - 2.1, 22.3, z + 0.8, z + 2.2, self.mat("screen_dark"), self.col))
        objs.append(box_ft(self.uid("k_oven_handle"), wx - 2.25, 19.8, wx - 2.17, 22.2, z + 2.45, z + 2.53, ss, self.col))
        # hood 42 in wide, bottom Z 6, top 8, black steel canopy, duct box above
        objs.append(box_ft(self.uid("k_hood"), wx - 1.9, 19.25, wx, 22.75, z + 6.0, z + 6.55, black, self.col))
        objs.append(box_ft(self.uid("k_hood_box"), wx - 1.3, 19.6, wx, 22.4, z + 6.55, z + 8.0, black, self.col))
        objs.append(box_ft(self.uid("k_hood_lens"), wx - 1.6, 19.6, wx - 0.3, 22.4, z + 5.98, z + 6.0, self.mat("lamp_glow"), self.col))
        self.light(type="area", pos=(wx - 1.0, 21.0, z + 5.95), size=1.2, size_y=2.6, shape="RECTANGLE", watts=8, kelvin=2700, rot=(0, 0, 0), name="hood")
        # pot filler
        objs.append(cylinder_ft(self.uid("k_potfiller"), (wx - 0.02, 21.0, z + 5.0), 0.04, 0.9, brass, self.col, 8, axis="X"))
        objs.append(cylinder_ft(self.uid("k_potfiller"), (wx - 0.9, 21.0 - 0.5, z + 5.0), 0.035, 1.0, brass, self.col, 8, axis="Y"))
        # base cabinets Y 22.5-25 with soapstone top 25 in deep
        objs.append(box_ft(self.uid("k_base"), wx - 2.05, 22.5, wx, 25.0, z + 0.35, z + 2.9, wood, self.col))
        objs.append(box_ft(self.uid("k_toe"), wx - 1.8, 22.5, wx, 25.0, z, z + 0.35, black, self.col))
        objs.append(box_ft(self.uid("k_counter"), wx - 2.15, 22.5, wx, 25.05, z + 2.9, z + 3.0, soap, self.col))
        objs.append(box_ft(self.uid("reveal"), wx - 2.06, 23.75 - 0.01, wx - 2.045, 23.75 + 0.01, z + 0.4, z + 2.85, self.mat("black"), self.col))
        # uppers Y 19-25 (13 in deep) Z 5-8.5, interrupted by the hood 19.25-22.75
        for (ya, yb) in ((19.0, 19.2), (22.8, 25.0)):
            if yb - ya > 0.5:
                objs += self.gen_cabinet({"b": [wx - 1.08, ya, wx, yb, z + 5.0, z + 8.5], "doors": 2, "face": "-x"})
        # under-cabinet strip under the 22.8-25 upper
        objs += self.gen_led_strip({"b": [wx - 1.0, 22.9, wx - 0.9, 24.9, z + 4.97, z + 5.0], "watts": 6})
        # backsplash: tile Z 3-5 along Y 19-25 and up to Z 8 behind the hood
        objs.append(box_ft(self.uid("k_backsplash"), wx - 0.03, 19.0, wx, 25.0, z + 3.0, z + 5.0, self.mat("tile_backsplash"), self.col))
        objs.append(box_ft(self.uid("k_backsplash"), wx - 0.03, 19.25, wx, 22.75, z + 5.0, z + 8.0, self.mat("tile_backsplash"), self.col))
        # freezer and fridge columns, 30 in wide, walnut panels with long brass pulls
        for (ya, yb) in ((25.0, 27.5), (27.5, 30.0)):
            objs.append(box_ft(self.uid("k_column"), wx - 2.1, ya, wx, yb, z, z + 8.5, wood, self.col))
            objs.append(box_ft(self.uid("k_pull"), wx - 2.2, ya + 0.35, wx - 2.12, ya + 0.42, z + 2.5, z + 6.5, brass, self.col))
            objs.append(box_ft(self.uid("reveal"), wx - 2.11, ya + 0.02, wx - 2.1, yb - 0.02, z + 0.02, z + 8.48, self.mat("black"), self.col))
        # --- south wall run X 8.5-21.5, full height, with the oven stack at X 9-11.5
        objs.append(box_ft(self.uid("k_south"), 8.5, 13.25, 21.5, 14.5, z, z + 8.5, wood, self.col))
        for u in (11.5, 14.0, 16.5, 19.0):
            objs.append(box_ft(self.uid("reveal"), u - 0.01, 14.5 - 0.005, u + 0.01, 14.51, z + 0.05, z + 8.45, self.mat("black"), self.col))
        for zz in (3.0, 5.6):
            objs.append(box_ft(self.uid("reveal"), 11.6, 14.5 - 0.005, 21.4, 14.51, z + zz - 0.01, z + zz + 0.01, self.mat("black"), self.col))
        # ovens: steam Z 3.5-5, convection Z 5-6.8, warming drawer below
        for (za, zb) in ((3.5, 5.0), (5.0, 6.8)):
            objs.append(box_ft(self.uid("k_oven_glass"), 9.15, 14.51, 11.35, 14.53, z + za + 0.15, z + zb - 0.15, self.mat("screen_dark"), self.col))
            objs.append(box_ft(self.uid("k_oven_handle"), 9.3, 14.55, 11.2, 14.62, z + zb - 0.3, z + zb - 0.22, ss, self.col))
        objs.append(box_ft(self.uid("k_warm_drawer"), 9.1, 14.51, 11.4, 14.53, z + 2.6, z + 3.4, ss, self.col))
        # --- island: work end Y 15-21 olive with soapstone; table end Y 21-26 walnut slab at 2.5
        ix0, ix1 = 12.0, 15.5
        objs.append(box_ft(self.uid("k_island"), ix0, 15.0, ix1, 21.0, z + 0.35, z + 2.9, olive, self.col))
        objs.append(box_ft(self.uid("k_island_toe"), ix0 + 0.25, 15.25, ix1 - 0.25, 21.0, z, z + 0.35, black, self.col))
        objs.append(box_ft(self.uid("k_island_top"), ix0 - 0.125, 14.875, ix1 + 0.125, 21.1, z + 2.9, z + 3.0, soap, self.col))
        # drawer/door reveals on the west face, dishwasher panel on the east face Y 19-21
        for u in (17.0, 19.0):
            objs.append(box_ft(self.uid("reveal"), ix0 - 0.01, u - 0.01, ix0 + 0.005, u + 0.01, z + 0.4, z + 2.85, self.mat("black"), self.col))
        objs.append(box_ft(self.uid("reveal"), ix1 - 0.005, 19.0, ix1 + 0.01, 19.02, z + 0.4, z + 2.85, self.mat("black"), self.col))
        objs.append(box_ft(self.uid("k_dw_pull"), ix1 + 0.01, 19.4, ix1 + 0.08, 20.6, z + 2.55, z + 2.62, brass, self.col))
        # sink 30 in at (13.75, 18), stainless basin recessed, bridge faucet behind at Y 16.8
        objs.append(box_ft(self.uid("k_sink_rim"), 13.75 - 1.25, 17.25, 13.75 + 1.25, 18.75, z + 2.98, z + 3.005, ss, self.col))
        objs.append(box_ft(self.uid("k_sink_basin"), 13.75 - 1.2, 17.3, 13.75 + 1.2, 18.7, z + 2.3, z + 2.98, ss, self.col))
        objs.append(box_ft(self.uid("k_sink_hole"), 13.75 - 1.15, 17.35, 13.75 + 1.15, 18.65, z + 2.35, z + 3.0, self.mat("steel_black"), self.col))
        for dx in (-0.35, 0.35):
            objs.append(cylinder_ft(self.uid("k_faucet"), (13.75 + dx, 16.8, z + 3.0), 0.05, 0.6, brass, self.col, 10))
        objs.append(cylinder_ft(self.uid("k_faucet"), (13.75 - 0.35, 16.8, z + 3.6), 0.04, 0.7, brass, self.col, 8, axis="X"))
        objs.append(cylinder_ft(self.uid("k_faucet"), (13.75, 16.8, z + 3.6), 0.05, 0.9, brass, self.col, 10))
        objs.append(cylinder_ft(self.uid("k_faucet"), (13.75, 16.8, z + 4.5), 0.045, 1.1, brass, self.col, 8, axis="Y"))
        objs.append(cylinder_ft(self.uid("k_hot_tap"), (13.2, 16.8, z + 3.0), 0.03, 0.55, brass, self.col, 8))
        # table end: walnut slab top at Z 2.5, 2.5 in thick, cantilevered from the island over a leg frame
        objs.append(box_ft(self.uid("k_table"), ix0, 21.0, ix1, 26.0, z + 2.29, z + 2.5, wood, self.col))
        objs.append(box_ft(self.uid("k_table_apron"), ix0 + 0.3, 21.0, ix1 - 0.3, 25.7, z + 2.05, z + 2.29, wood, self.col))
        for (lx, ly) in ((ix0 + 0.35, 25.5), (ix1 - 0.35, 25.5)):
            objs.append(box_ft(self.uid("k_table_leg"), lx - 0.1, ly - 0.1, lx + 0.1, ly + 0.1, z, z + 2.29, wood, self.col))
        objs.append(box_ft(self.uid("k_table_leg"), ix0 + 0.35, 25.4, ix1 - 0.35, 25.6, z + 0.25, z + 0.35, wood, self.col))
        # six shell chairs
        for cy in (22.0, 23.75, 25.5):
            objs += self.gen_dining_chair({"pos": [11.0, cy, z], "rot_z": -90, "m": "wool_mustard"})
            objs += self.gen_dining_chair({"pos": [16.5, cy, z], "rot_z": 90, "m": "wool_mustard"})
        # counter objects: bowl of oranges, cutting board, linen towel over the sink edge
        bowl = sphere_ft(self.uid("k_bowl"), (13.75, 20.0, z + 3.16), 0.55, self.mat("walnut"), self.col)
        bowl.scale = (1, 1, 0.32)
        objs.append(bowl)
        rng = random.Random(7)
        for i in range(7):
            a = i * 0.9
            objs.append(sphere_ft(self.uid("k_orange"), (13.75 + math.cos(a) * 0.22 * (i % 3), 20.0 + math.sin(a) * 0.22 * (i % 3), z + 3.18 + 0.13 + (0.2 if i == 6 else 0)), 0.14, self.mat("orange"), self.col, 12, 8))
        objs.append(box_ft(self.uid("k_board"), 12.4, 19.2, 13.3, 20.6, z + 3.0, z + 3.07, self.mat("oak"), self.col))
        objs.append(box_ft(self.uid("k_towel"), 14.6, 17.6, 15.6, 18.4, z + 2.6, z + 3.03, self.mat("linen_white"), self.col))
        # --- nook: marble counter along Y 27.3-29.8, X 0.5-8, walnut base, open shelves at 5.5 and 7
        objs.append(box_ft(self.uid("n_base"), 1.0, 27.3, 8.0, 29.7, z + 0.35, z + 2.9, wood, self.col))
        objs.append(box_ft(self.uid("n_toe"), 1.0, 27.3, 8.0, 29.45, z, z + 0.35, black, self.col))
        objs.append(box_ft(self.uid("n_top"), 0.98, 27.25, 8.0, 29.8, z + 2.9, z + 3.0, self.mat("marble_white"), self.col))
        for u in (2.5, 4.5, 6.5):
            objs.append(box_ft(self.uid("reveal"), u - 0.01, 29.69, u + 0.01, 29.71, z + 0.4, z + 2.85, self.mat("black"), self.col))
        for zz in (5.5, 7.0):
            objs.append(box_ft(self.uid("n_shelf"), 1.0, 27.25, 8.0, 28.2, z + zz, z + zz + 0.1, wood, self.col))
        for i in range(9):
            zz = 5.6 if i < 5 else 7.1
            xx = 1.5 + (i % 5) * 1.4 + rng.uniform(-0.15, 0.15)
            objs.append(cylinder_ft(self.uid("n_ceramic"), (xx, 27.7, z + zz), rng.uniform(0.15, 0.28), rng.uniform(0.35, 0.85),
                                    self.mat(rng.choice(["ceramic_white", "teal", "mustard", "olive_paint"])), self.col, 18))
        # prep sink 15 in at (6.5, 28.5) with a small brass faucet
        objs.append(box_ft(self.uid("n_sink"), 6.5 - 0.62, 27.9, 6.5 + 0.62, 29.1, z + 2.5, z + 2.99, brass, self.col))
        objs.append(box_ft(self.uid("n_sink_hole"), 6.5 - 0.58, 27.95, 6.5 + 0.58, 29.05, z + 2.55, z + 3.0, self.mat("steel_black"), self.col))
        objs.append(cylinder_ft(self.uid("n_faucet"), (6.5, 27.65, z + 3.0), 0.04, 0.8, brass, self.col, 8))
        objs.append(cylinder_ft(self.uid("n_faucet"), (6.5, 27.65, z + 3.75), 0.035, 0.7, brass, self.col, 8, axis="Y"))
        # stand mixer pale green at (2, 28.5): base, post, head, bowl
        mint = self.mat("mint_enamel")
        objs.append(box_ft(self.uid("n_mixer_base"), 1.6, 28.05, 2.4, 29.1, z + 3.0, z + 3.35, mint, self.col))
        objs.append(box_ft(self.uid("n_mixer_post"), 2.1, 28.75, 2.4, 29.05, z + 3.35, z + 4.15, mint, self.col))
        objs.append(box_ft(self.uid("n_mixer_head"), 1.55, 28.35, 2.4, 28.95, z + 3.95, z + 4.3, mint, self.col))
        mb = sphere_ft(self.uid("n_mixer_bowl"), (1.9, 28.5, z + 3.55), 0.36, ss, self.col)
        mb.scale = (1, 1, 0.8)
        objs.append(mb)
        # cake stand with dome and cake at (5, 28.5)
        objs.append(cylinder_ft(self.uid("n_stand"), (5.0, 28.5, z + 3.0), 0.55, 0.08, self.mat("ceramic_white"), self.col, 28))
        objs.append(cylinder_ft(self.uid("n_stand_stem"), (5.0, 28.5, z + 3.08), 0.12, 0.35, self.mat("ceramic_white"), self.col, 16))
        objs.append(cylinder_ft(self.uid("n_stand_plate"), (5.0, 28.5, z + 3.43), 0.6, 0.05, self.mat("ceramic_white"), self.col, 32))
        objs.append(cylinder_ft(self.uid("n_cake"), (5.0, 28.5, z + 3.48), 0.42, 0.42, self.mat("cake_cream"), self.col, 28))
        objs.append(cylinder_ft(self.uid("n_cake_layer"), (5.0, 28.5, z + 3.62), 0.425, 0.03, self.mat("oxblood"), self.col, 28))
        dome = sphere_ft(self.uid("n_glass_dome"), (5.0, 28.5, z + 3.5), 0.66, self.mat("glass"), glassc, 24, 12)
        dome.scale = (1, 1, 1.1)
        objs.append(dome)
        # a second surface just inside makes it a hollow shell instead of a solid glass lens
        inner = sphere_ft(self.uid("n_glass_dome_in"), (5.0, 28.5, z + 3.5), 0.66, self.mat("glass"), glassc, 24, 12)
        inner.scale = tuple(v * 0.955 for v in (1, 1, 1.1))
        objs.append(inner)
        # rolling pin, canister set
        objs.append(cylinder_ft(self.uid("n_pin"), (3.0, 29.0, z + 3.12), 0.12, 1.4, self.mat("marble_white"), self.col, 14, axis="X"))
        for i, hgt in enumerate((0.9, 0.75, 0.6)):
            objs.append(cylinder_ft(self.uid("n_canister"), (7.0 + i * 0.0 - 0.0, 28.0 + i * 0.0, z + 3.0), 0.22, hgt, self.mat("ceramic_white"), self.col, 20)) if False else None
            objs.append(cylinder_ft(self.uid("n_canister"), (7.2 - i * 0.55, 28.1, z + 3.0), 0.2, hgt, self.mat("ceramic_white"), self.col, 20))
            objs.append(cylinder_ft(self.uid("n_canister_lid"), (7.2 - i * 0.55, 28.1, z + 3.0 + hgt), 0.21, 0.05, wood, self.col, 20))
        # nook wall lamp at (0.3, 28.5, 6.5): brass articulated
        objs += self.gen_sconce({"wall": {"axis": "y", "at": 1.0, "face": "+x"}, "u": 28.5, "z": 6.5, "watts": 12, "radius": 0.2, "height": 0.5})
        # small things: cookbooks on the south counter, radio, step stool
        for k in range(2):
            objs.append(box_ft(self.uid("k_cookbook"), 17.0, 14.55 + k * 0.05, 17.9, 15.4, z + 3.0 + k * 0.1, z + 3.1 + k * 0.1, self.mat(["book_c", "book_f"][k]), self.col)) if False else None
        objs.append(box_ft(self.uid("k_radio"), 19.5, 14.6, 20.4, 15.05, z + 3.0, z + 3.45, self.mat("walnut"), self.col)) if False else None
        # wool runner along the cooking wall and the step stool
        objs.append(self.gen_rug({"b": [18.8, 19.5, 21.3, 27.5], "m": "runner", "thick": 0.04, "room": "kitchen"}))
        objs.append(box_ft(self.uid("k_stool"), 19.0, 28.6, 20.0, 29.5, z + 0.1, z + 0.85, wood, self.col))
        objs.append(box_ft(self.uid("k_stool"), 19.0, 28.6, 20.0, 29.5, z, z + 0.1, self.mat("black"), self.col))
        return objs

    # ================================================================== appliances and utility
    def gen_washer_dryer(self, e):
        """Front-load washer and dryer stacked on a walnut plinth: b = machine box, plinth below."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        ss = self.mat("stainless")
        objs = [box_ft(self.uid("wd_plinth"), x0 - 0.1, y0 - 0.1, x1 + 0.1, y1 + 0.1, e.get("floor_z", z0 - 1.2), z0, self.mat("walnut_h"), self.col)]
        mid = (z0 + z1) / 2
        face = e.get("face", "-x")
        for (za, zb) in ((z0, mid - 0.03), (mid + 0.03, z1)):
            objs.append(box_ft(self.uid("wd_body"), x0, y0, x1, y1, za, zb, ss, self.col))
            cz = (za + zb) / 2 - 0.15
            cy = (y0 + y1) / 2
            if face == "-x":
                objs.append(cylinder_ft(self.uid("wd_door"), (x0 - 0.06, cy, cz), 1.0, 0.06, self.mat("steel_black"), self.col, 32, axis="X"))
                objs.append(cylinder_ft(self.uid("wd_glass"), (x0 - 0.1, cy, cz), 0.75, 0.04, self.mat("glass"), get_collection("glass"), 28, axis="X"))
                objs.append(box_ft(self.uid("wd_panel"), x0 - 0.02, y0 + 0.2, x0, y1 - 0.2, zb - 0.45, zb - 0.1, self.mat("screen_dark"), self.col))
        return objs

    def gen_fridge_small(self, e):
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        objs = [box_ft(self.uid("fr_body"), x0, y0, x1, y1, z0, z1, self.mat("steel_black"), self.col)]
        face = e.get("face", "-x")
        if face == "-x":
            objs.append(box_ft(self.uid("fr_glass"), x0 - 0.03, y0 + 0.1, x0, y1 - 0.1, z0 + 0.3, z1 - 0.2, self.mat("glass"), get_collection("glass")))
            objs.append(box_ft(self.uid("fr_interior"), x0 + 0.02, y0 + 0.1, x0 + 0.05, y1 - 0.1, z0 + 0.3, z1 - 0.2, self.mat("lamp_shade"), self.col))
            self.light(type="area", pos=(x0 + 0.1, (y0 + y1) / 2, (z0 + z1) / 2), size=y1 - y0 - 0.3, size_y=z1 - z0 - 0.6, shape="RECTANGLE", watts=4, kelvin=4000, rot=(0, math.radians(90), 0), name="fridge")
        elif face == "+y":
            objs.append(box_ft(self.uid("fr_glass"), x0 + 0.1, y1, x1 - 0.1, y1 + 0.03, z0 + 0.3, z1 - 0.2, self.mat("glass"), get_collection("glass")))
        else:
            objs.append(box_ft(self.uid("fr_glass"), x0 + 0.1, y0 - 0.03, x1 - 0.1, y0, z0 + 0.3, z1 - 0.2, self.mat("glass"), get_collection("glass")))
        # bottles inside
        rng = random.Random(3)
        for i in range(8):
            bx = rng.uniform(x0 + 0.2, x1 - 0.2); by = rng.uniform(y0 + 0.2, y1 - 0.2)
            objs.append(cylinder_ft(self.uid("fr_bottle"), (bx, by, z0 + 0.35 + (0.9 if i > 4 else 0)), 0.11, 0.75, self.mat(rng.choice(["glass", "teal", "ceramic_white"])), self.col, 10))
        return objs

    def gen_utility_sink(self, e):
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        objs = [box_ft(self.uid("us_cab"), x0, y0, x1, y1, z0 + 0.3, z1 - 0.05, self.mat("walnut_h"), self.col),
                box_ft(self.uid("us_toe"), x0 + 0.2, y0 + 0.2, x1 - 0.2, y1 - 0.2, z0, z0 + 0.3, self.mat("black"), self.col),
                box_ft(self.uid("us_top"), x0 - 0.03, y0 - 0.03, x1 + 0.03, y1 + 0.03, z1 - 0.05, z1 + 0.05, self.mat("stainless"), self.col),
                box_ft(self.uid("us_basin"), x0 + 0.15, y0 + 0.15, x1 - 0.15, y1 - 0.15, z1 - 0.7, z1 + 0.06, self.mat("steel_black"), self.col)]
        wall = e.get("faucet_wall", "+x")
        fx = x1 - 0.15 if wall == "+x" else x0 + 0.15
        objs.append(cylinder_ft(self.uid("us_faucet"), (fx, (y0 + y1) / 2, z1 + 0.05), 0.04, 0.9, self.mat("brass"), self.col, 8))
        objs.append(cylinder_ft(self.uid("us_faucet"), (fx - (0.6 if wall == "+x" else 0.0), (y0 + y1) / 2, z1 + 0.95), 0.035, 0.6, self.mat("brass"), self.col, 8, axis="X"))
        return objs

    def gen_toilet(self, e):
        """Wall-hung toilet: bowl (rounded box), seat, brass flush plate on the wall behind."""
        p = e["pos"]           # centre of the bowl at floor level
        facing = e.get("facing", "-x")   # direction the user faces (bowl projects this way from the wall)
        dx, dy = {"-x": (-1, 0), "+x": (1, 0), "-y": (0, -1), "+y": (0, 1)}[facing]
        cer = self.mat("ceramic_white")
        objs = []
        L, W = 1.9, 1.2
        cx, cy = p[0] + dx * 0.0, p[1] + dy * 0.0
        if dx:
            objs.append(box_ft(self.uid("wc_bowl"), min(cx - dx * 0.4, cx + dx * 1.5), cy - W / 2, max(cx - dx * 0.4, cx + dx * 1.5), cy + W / 2, p[2] + 1.05, p[2] + 1.45, cer, self.col))
            objs.append(box_ft(self.uid("wc_seat"), min(cx - dx * 0.3, cx + dx * 1.5), cy - W / 2 + 0.03, max(cx - dx * 0.3, cx + dx * 1.5), cy + W / 2 - 0.03, p[2] + 1.45, p[2] + 1.52, self.mat("linen_white"), self.col))
            objs.append(box_ft(self.uid("wc_bowl_u"), min(cx - dx * 0.2, cx + dx * 1.35), cy - W / 2 + 0.15, max(cx - dx * 0.2, cx + dx * 1.35), cy + W / 2 - 0.15, p[2] + 0.75, p[2] + 1.05, cer, self.col))
            wall_x = cx - dx * 0.45
            objs.append(box_ft(self.uid("wc_plate"), min(wall_x, wall_x + dx * 0.02), cy - 0.35, max(wall_x, wall_x + dx * 0.02), cy + 0.35, p[2] + 3.2, p[2] + 3.7, self.mat("brass"), self.col))
        else:
            objs.append(box_ft(self.uid("wc_bowl"), cx - W / 2, min(cy - dy * 0.4, cy + dy * 1.5), cx + W / 2, max(cy - dy * 0.4, cy + dy * 1.5), p[2] + 1.05, p[2] + 1.45, cer, self.col))
            objs.append(box_ft(self.uid("wc_seat"), cx - W / 2 + 0.03, min(cy - dy * 0.3, cy + dy * 1.5), cx + W / 2 - 0.03, max(cy - dy * 0.3, cy + dy * 1.5), p[2] + 1.45, p[2] + 1.52, self.mat("linen_white"), self.col))
            objs.append(box_ft(self.uid("wc_bowl_u"), cx - W / 2 + 0.15, min(cy - dy * 0.2, cy + dy * 1.35), cx + W / 2 - 0.15, max(cy - dy * 0.2, cy + dy * 1.35), p[2] + 0.75, p[2] + 1.05, cer, self.col))
            wall_y = cy - dy * 0.45
            objs.append(box_ft(self.uid("wc_plate"), cx - 0.35, min(wall_y, wall_y + dy * 0.02), cx + 0.35, max(wall_y, wall_y + dy * 0.02), p[2] + 3.2, p[2] + 3.7, self.mat("brass"), self.col))
        if e.get("paper", True):
            # paper holder beside the bowl on the side wall or on a post
            objs.append(cylinder_ft(self.uid("wc_roll"), (cx + dx * 1.0 + (0 if dx else 0.8), cy + dy * 1.0 + (0.8 if dx else 0), p[2] + 2.0), 0.2, 0.35, self.mat("paper"), self.col, 16, axis="Y" if dx else "X"))
        return objs

    def gen_round_mirror(self, e):
        wall = e["wall"]
        u, z = e["u"], e.get("z", 5.5)
        r = e.get("radius", 1.0)
        dx, dy = _face_dir(wall)
        at = wall["at"]
        objs = []
        if wall["axis"] == "y":
            objs.append(cylinder_ft(self.uid("rm_frame"), (at + dx * 0.0, u, z), r + 0.06, 0.08, self.mat("brass"), self.col, 40, axis="X"))
            objs.append(cylinder_ft(self.uid("rm_glass"), (at + dx * 0.05, u, z), r, 0.02, self.mat("mirror"), self.col, 40, axis="X"))
        else:
            objs.append(cylinder_ft(self.uid("rm_frame"), (u, at + dy * 0.0, z), r + 0.06, 0.08, self.mat("brass"), self.col, 40, axis="Y"))
            objs.append(cylinder_ft(self.uid("rm_glass"), (u, at + dy * 0.05, z), r, 0.02, self.mat("mirror"), self.col, 40, axis="Y"))
        return objs

    def gen_wall_vanity(self, e):
        """Small wall-hung vanity with a vessel sink and wall faucet. b = cabinet box; face = direction into the room."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        cer = self.mat("ceramic_white")
        brass = self.mat("brass")
        objs = [box_ft(self.uid("wv_body"), x0, y0, x1, y1, z0, z1, wood, self.col),
                box_ft(self.uid("wv_top"), x0 - 0.03, y0 - 0.03, x1 + 0.03, y1 + 0.03, z1, z1 + 0.08, self.mat("soapstone"), self.col)]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        bowl = sphere_ft(self.uid("wv_vessel"), (cx, cy, z1 + 0.08 + 0.2), 0.62, cer, self.col, 28, 14)
        bowl.scale = (1, 1, 0.45)
        objs.append(bowl)
        face = e.get("face", "+x")
        if face == "+x":
            objs.append(cylinder_ft(self.uid("wv_faucet"), (x0 + 0.02, cy, z1 + 1.15), 0.045, 0.7, brass, self.col, 8, axis="X"))
            objs.append(cylinder_ft(self.uid("wv_faucet"), (x0 + 0.02, cy, z1 + 1.15), 0.09, 0.05, brass, self.col, 16, axis="X"))
        return objs

    def gen_vanity2(self, e):
        """Double wall-hung walnut vanity along a wall of either axis, undermount sinks, wall faucets, full-width backlit
        mirror, two sconces. span [u0,u1] along the wall, wall {axis, at, face}, top_z."""
        wall = e["wall"]
        u0, u1 = e["span"]
        top = e.get("top_z", 2.9)
        depth = e.get("depth", 1.8)
        dx, dy = _face_dir(wall)
        at = wall["at"]
        wood = self.mat("walnut_h")
        stone = self.mat(e.get("top_m", "soapstone"))
        cer = self.mat("ceramic_white")
        brass = self.mat("brass")
        objs = []

        def B(name, a0, a1, d0, d1, z0, z1, mat, col=None):
            # a along the wall, d out from the wall face
            if wall["axis"] == "y":
                xs = sorted((at + dx * d0, at + dx * d1)); return box_ft(self.uid(name), xs[0], a0, xs[1], a1, z0, z1, mat, col or self.col)
            ys = sorted((at + dy * d0, at + dy * d1)); return box_ft(self.uid(name), a0, ys[0], a1, ys[1], z0, z1, mat, col or self.col)
        objs.append(B("v_body", u0, u1, 0.0, depth, top - 1.25, top - 0.1, wood))
        objs.append(B("v_top", u0 - 0.03, u1 + 0.03, 0.0, depth + 0.05, top - 0.1, top, stone))
        nd = e.get("drawers", 4)
        for i in range(1, nd):
            u = u0 + i * (u1 - u0) / nd
            objs.append(B("reveal", u - 0.01, u + 0.01, depth - 0.005, depth + 0.01, top - 1.2, top - 0.15, self.mat("black")))
        for su in e.get("sinks", [u0 + (u1 - u0) * 0.27, u0 + (u1 - u0) * 0.73]):
            objs.append(B("v_sink_hole", su - 0.75, su + 0.75, 0.35, depth - 0.35, top - 0.55, top + 0.002, self.mat("steel_black")))
            basin = B("v_basin", su - 0.72, su + 0.72, 0.38, depth - 0.38, top - 0.5, top - 0.02, cer)
            objs.append(basin)
            # wall-mounted faucet at Z top+0.7
            if wall["axis"] == "y":
                objs.append(cylinder_ft(self.uid("v_faucet"), (at + dx * 0.02, su, top + 0.7), 0.045, 0.75, brass, self.col, 8, axis="X"))
                objs.append(cylinder_ft(self.uid("v_faucet_p"), (at + dx * 0.02, su, top + 0.7), 0.1, 0.05, brass, self.col, 16, axis="X"))
                for hu in (-0.45, 0.45):
                    objs.append(cylinder_ft(self.uid("v_handle"), (at + dx * 0.02, su + hu, top + 0.7), 0.06, 0.25, brass, self.col, 10, axis="X"))
            else:
                objs.append(cylinder_ft(self.uid("v_faucet"), (su, at + dy * 0.02, top + 0.7), 0.045, 0.75, brass, self.col, 8, axis="Y"))
                objs.append(cylinder_ft(self.uid("v_faucet_p"), (su, at + dy * 0.02, top + 0.7), 0.1, 0.05, brass, self.col, 16, axis="Y"))
                for hu in (-0.45, 0.45):
                    objs.append(cylinder_ft(self.uid("v_handle"), (su + hu, at + dy * 0.02, top + 0.7), 0.06, 0.25, brass, self.col, 10, axis="Y"))
        # backlit mirror from top+0.7 to top+4.6 (Z 3.6-7.5 in the spec), glow behind
        mz0, mz1 = e.get("mirror_z", [top + 0.7, top + 4.6])
        objs.append(B("v_mirror", u0 + 0.1, u1 - 0.1, 0.06, 0.1, mz0, mz1, self.mat("mirror")))
        objs.append(B("v_glow", u0 + 0.05, u1 - 0.05, 0.02, 0.06, mz0 - 0.05, mz1 + 0.05, self.mat("glow_soft")))
        gc = (u0 + u1) / 2
        if wall["axis"] == "y":
            self.light(type="area", pos=(at + dx * 0.15, gc, (mz0 + mz1) / 2), size=u1 - u0 - 0.4, size_y=mz1 - mz0, shape="RECTANGLE", watts=e.get("glow_watts", 18),
                       rot=(0, math.radians(90 * dx), 0), name="mirror_glow")
        else:
            self.light(type="area", pos=(gc, at + dy * 0.15, (mz0 + mz1) / 2), size=u1 - u0 - 0.4, size_y=mz1 - mz0, shape="RECTANGLE", watts=e.get("glow_watts", 18),
                       rot=(math.radians(-90 * dy), 0, 0), name="mirror_glow")
        for su in e.get("sconces", [u0 + 0.3, u1 - 0.3]):
            objs += self.gen_sconce({"wall": wall, "u": su, "z": e.get("sconce_z", 6.0), "watts": 8})
        # towels, a stool, a plant are placed by the caller
        return objs

    def gen_shower2(self, e):
        """Curbless shower: glass panel(s), brass thermostatic columns with rain heads and handhelds, niche, bench,
        linear drain. b footprint, head_wall ('+y' = the Y max wall), glass list of (side, u0, u1)."""
        b = e["b"]
        x0, y0, x1, y1 = b
        z = e.get("z", 0)
        glass = self.mat("glass")
        gc = get_collection("glass")
        brass = self.mat("brass")
        objs = []
        h = e.get("glass_h", 7.2)
        for (side, ua, ub) in e.get("glass", []):
            if side == "-x":
                objs.append(box_ft(self.uid("sh_glass"), x0, ua, x0 + 0.03, ub, z + 0.05, z + h, glass, gc))
                objs.append(box_ft(self.uid("sh_clip"), x0 - 0.02, ua, x0 + 0.05, ua + 0.15, z + 0.0, z + 0.3, self.mat("bronze"), self.col))
            elif side == "+x":
                objs.append(box_ft(self.uid("sh_glass"), x1 - 0.03, ua, x1, ub, z + 0.05, z + h, glass, gc))
                objs.append(box_ft(self.uid("sh_clip"), x1 - 0.05, ua, x1 + 0.02, ua + 0.15, z + 0.0, z + 0.3, self.mat("bronze"), self.col))
            elif side == "-y":
                objs.append(box_ft(self.uid("sh_glass"), ua, y0, ub, y0 + 0.03, z + 0.05, z + h, glass, gc))
            else:
                objs.append(box_ft(self.uid("sh_glass"), ua, y1 - 0.03, ub, y1, z + 0.05, z + h, glass, gc))
        hw = e.get("head_wall", "+y")
        for hu in e.get("heads", []):
            # exposed thermostatic column: vertical bar, crossbar with wheels at 3.8, rain head arm at 7, handheld on a slide bar
            if hw in ("+y", "-y"):
                wy = y1 - 0.03 if hw == "+y" else y0 + 0.03
                dyy = -1 if hw == "+y" else 1
                objs.append(cylinder_ft(self.uid("sh_col"), (hu, wy + dyy * 0.15, z + 3.3), 0.06, 3.9, brass, self.col, 12))
                objs.append(cylinder_ft(self.uid("sh_cross"), (hu - 0.6, wy + dyy * 0.15, z + 3.8), 0.06, 1.2, brass, self.col, 12, axis="X"))
                for wx_ in (-0.5, 0.5):
                    objs.append(cylinder_ft(self.uid("sh_wheel"), (hu + wx_, wy + dyy * 0.15, z + 3.8), 0.13, 0.12, brass, self.col, 16, axis="Y"))
                objs.append(cylinder_ft(self.uid("sh_arm"), (hu, wy, z + 7.0), 0.05, 1.3, brass, self.col, 10, axis="Y")) if dyy > 0 else \
                    objs.append(cylinder_ft(self.uid("sh_arm"), (hu, wy - 1.3, z + 7.0), 0.05, 1.3, brass, self.col, 10, axis="Y"))
                objs.append(cylinder_ft(self.uid("sh_rain"), (hu, wy + dyy * 1.25, z + 6.9), 0.5, 0.06, brass, self.col, 28))
                objs.append(cylinder_ft(self.uid("sh_hand"), (hu + 0.75, wy + dyy * 0.2, z + 5.2), 0.07, 0.9, brass, self.col, 10))
                objs.append(cylinder_ft(self.uid("sh_slide"), (hu + 0.75, wy + dyy * 0.1, z + 4.2), 0.03, 2.2, brass, self.col, 8))
        if e.get("niche"):
            nx0, nx1, nz0, nz1 = e["niche"]
            ny = y1 if hw == "+y" else y0
            objs.append(box_ft(self.uid("sh_niche"), nx0, ny - 0.35 if hw == "+y" else ny, nx1, ny if hw == "+y" else ny + 0.35, z + nz0, z + nz1, self.mat("terrazzo"), self.col))
            objs.append(box_ft(self.uid("sh_niche_in"), nx0 + 0.05, (ny - 0.33) if hw == "+y" else ny + 0.02, nx1 - 0.05, (ny - 0.02) if hw == "+y" else ny + 0.33, z + nz0 + 0.05, z + nz1 - 0.05, self.mat("steel_black"), self.col))
            rng = random.Random(2)
            for i in range(3):
                bx = nx0 + 0.25 + i * (nx1 - nx0 - 0.5) / 2
                objs.append(cylinder_ft(self.uid("sh_bottle"), (bx, ny - 0.18 if hw == "+y" else ny + 0.18, z + nz0 + 0.05), 0.08, rng.uniform(0.5, 0.8), self.mat(rng.choice(["glass", "teal", "olive_paint"])), self.col, 12))
        if e.get("bench"):
            bb = e["bench"]
            objs.append(box_ft(self.uid("sh_bench"), bb[0], bb[1], bb[2], bb[3], z + bb[4] if len(bb) > 4 else z, z + (bb[5] if len(bb) > 5 else 1.5), self.mat("walnut_h"), self.col))
        # linear drain along the head wall
        dy0 = (y1 - 0.5, y1 - 0.3) if hw == "+y" else (y0 + 0.3, y0 + 0.5)
        objs.append(box_ft(self.uid("sh_drain"), x0 + 0.5, dy0[0], x1 - 0.5, dy0[1], z + 0.001, z + 0.01, self.mat("stainless"), self.col))
        return objs

    def gen_tub(self, e):
        """Alcove tub: white shell with a rounded inner basin, brass filler and handheld, tile surround by caller."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        cer = self.mat("ceramic_white")
        objs = [box_ft(self.uid("tub_shell"), x0, y0, x1, y1, z0, z1, cer, self.col),
                box_ft(self.uid("tub_basin"), x0 + 0.35, y0 + 0.35, x1 - 0.35, y1 - 0.35, z0 + 0.35, z1 + 0.01, self.mat("linen_white"), self.col)]
        brass = self.mat("brass")
        fx = x1 - 0.8
        objs.append(cylinder_ft(self.uid("tub_filler"), (fx, y1 - 0.02, z1 + 0.6), 0.05, 0.7, brass, self.col, 10, axis="Y")) if False else None
        objs.append(cylinder_ft(self.uid("tub_filler"), (fx, y1 - 0.7, z1 + 0.6), 0.05, 0.7, brass, self.col, 10, axis="Y"))
        objs.append(cylinder_ft(self.uid("tub_valve"), (fx, y1 - 0.06, z1 + 1.3), 0.12, 0.08, brass, self.col, 16, axis="Y"))
        objs.append(cylinder_ft(self.uid("tub_slide"), (fx + 0.6, y1 - 0.1, z1 + 2.0), 0.03, 2.5, brass, self.col, 8))
        objs.append(cylinder_ft(self.uid("tub_hand"), (fx + 0.6, y1 - 0.25, z1 + 3.6), 0.07, 0.8, brass, self.col, 10))
        return objs

    def gen_towel_bar(self, e):
        wall = e["wall"]
        u, z = e["u"], e.get("z", 3.6)
        L = e.get("length", 2.0)
        dx, dy = _face_dir(wall)
        at = wall["at"]
        objs = []
        if wall["axis"] == "y":
            objs.append(cylinder_ft(self.uid("tb_bar"), (at + dx * 0.3, u - L / 2, z), 0.035, L, self.mat("brass"), self.col, 10, axis="Y"))
            for t, mt in enumerate(e.get("towels", ["towel_white"])):
                objs.append(box_ft(self.uid("towel"), min(at + dx * 0.15, at + dx * 0.4), u - L / 2 + 0.2 + t * 1.0, max(at + dx * 0.15, at + dx * 0.4), u - L / 2 + 1.0 + t * 1.0, z - 2.2, z + 0.05, self.mat(mt), self.col))
        else:
            objs.append(cylinder_ft(self.uid("tb_bar"), (u - L / 2, at + dy * 0.3, z), 0.035, L, self.mat("brass"), self.col, 10, axis="X"))
            for t, mt in enumerate(e.get("towels", ["towel_white"])):
                objs.append(box_ft(self.uid("towel"), u - L / 2 + 0.2 + t * 1.0, min(at + dy * 0.15, at + dy * 0.4), u - L / 2 + 1.0 + t * 1.0, max(at + dy * 0.15, at + dy * 0.4), z - 2.2, z + 0.05, self.mat(mt), self.col))
        return objs

    def gen_tile_wainscot(self, e):
        """Thin tile panel on wall faces: list of boxes."""
        return [box_ft(self.uid("panel_tile"), *bb, mat=self.mat(e.get("m", "tile_white")), collection=self.col) for bb in e["boxes"]]

    # ================================================================== closets and storage
    def gen_wardrobe(self, e):
        """Built-in wardrobe section. b = box, face = open side, kind: hanging | shelves | drawers | bins | shoes.
        Hanging: rod with a row of shirts/jackets (thin slabs on hangers) over drawers to Z drawer_h."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        face = e.get("face", "-y")
        kind = e.get("kind", "hanging")
        wood = self.mat("walnut_h")
        rng = random.Random(e.get("seed", 11))
        objs = []
        t = 0.08
        # carcass: back, sides, top
        if face in ("-y", "+y"):
            back = (y1 - t, y1) if face == "-y" else (y0, y0 + t)
            objs.append(box_ft(self.uid("wr_back"), x0, back[0], x1, back[1], z0, z1, wood, self.col))
            objs.append(box_ft(self.uid("wr_side"), x0, y0, x0 + t, y1, z0, z1, wood, self.col))
            objs.append(box_ft(self.uid("wr_side"), x1 - t, y0, x1, y1, z0, z1, wood, self.col))
        else:
            back = (x1 - t, x1) if face == "-x" else (x0, x0 + t)
            objs.append(box_ft(self.uid("wr_back"), back[0], y0, back[1], y1, z0, z1, wood, self.col))
            objs.append(box_ft(self.uid("wr_side"), x0, y0, x1, y0 + t, z0, z1, wood, self.col))
            objs.append(box_ft(self.uid("wr_side"), x0, y1 - t, x1, y1, z0, z1, wood, self.col))
        objs.append(box_ft(self.uid("wr_top"), x0, y0, x1, y1, z1 - t, z1, wood, self.col))
        along_x = face in ("-y", "+y")
        length = (x1 - x0) if along_x else (y1 - y0)
        depth = (y1 - y0) if along_x else (x1 - x0)
        dmid = (y0 + y1) / 2 if along_x else (x0 + x1) / 2

        def slab(u0, u1, d0, d1, za, zb, mat):
            if along_x:
                return box_ft(self.uid("wr_item"), x0 + u0, dmid + d0, x0 + u1, dmid + d1, za, zb, mat, self.col)
            return box_ft(self.uid("wr_item"), dmid + d0, y0 + u0, dmid + d1, y0 + u1, za, zb, mat, self.col)
        if kind == "hanging":
            dh = e.get("drawer_h", 3.0)
            # drawers below
            objs.append(slab(t, length - t, -depth / 2 + t, depth / 2 - 0.01, z0, z0 + dh, wood))
            for k in range(1, 3):
                zz = z0 + dh * k / 3
                objs.append(slab(t + 0.05, length - t - 0.05, depth / 2 - 0.02, depth / 2 + 0.005, zz - 0.01, zz + 0.01, self.mat("black")))
            for k in range(3):
                zz = z0 + dh * (k + 0.5) / 3
                objs.append(slab(length / 2 - 0.5, length / 2 + 0.5, depth / 2 - 0.005, depth / 2 + 0.05, zz - 0.03, zz + 0.03, self.mat("brass")))
            rod_z = e.get("rod_z", 6.5)
            objs.append(cylinder_ft(self.uid("wr_rod"), (x0 + t, dmid, z0 + rod_z) if along_x else (dmid, y0 + t, z0 + rod_z), 0.05, length - 2 * t, self.mat("brass"), self.col, 10, axis="X" if along_x else "Y"))
            cols = ["linen_white", "linen_white", "olive_paint", "teal_paint", "oxblood", "black", "wool_oatmeal", "denim", "mustard_paint"]
            u = t + 0.25
            while u < length - t - 0.35:
                w = rng.uniform(0.12, 0.22)
                hgt = rng.uniform(2.4, 3.3)
                c = self.mat(rng.choice(cols))
                garment = slab(u, u + w, -0.85, 0.85, z0 + rod_z - hgt, z0 + rod_z - 0.15, c)
                garment.name = self.uid("wr_garment")      # cloth-tagged: wrinkles and soft edges
                objs.append(garment)
                objs.append(slab(u + w / 2 - 0.01, u + w / 2 + 0.01, -0.02, 0.02, z0 + rod_z - 0.15, z0 + rod_z + 0.05, self.mat("brass")))
                u += w + rng.uniform(0.05, 0.14)
            # LED strip under the top
            objs += self.gen_led_strip({"b": [x0 + t, dmid - 0.05, x1 - t, dmid + 0.05, z1 - t - 0.03, z1 - t] if along_x else [dmid - 0.05, y0 + t, dmid + 0.05, y1 - t, z1 - t - 0.03, z1 - t], "watts": 4})
        elif kind in ("shelves", "shoes"):
            nsh = e.get("shelves", 6)
            for k in range(nsh + 1):
                zz = z0 + 0.4 + k * (z1 - z0 - 0.8) / nsh
                objs.append(slab(t, length - t, -depth / 2 + t, depth / 2 - 0.02, zz, zz + 0.06, wood))
                if k < nsh:
                    u = t + 0.15
                    while u < length - t - 0.6:
                        if kind == "shelves":
                            w = rng.uniform(0.9, 1.3)
                            hh = rng.uniform(0.25, 0.55)
                            folded = slab(u, u + min(w, length - t - u - 0.05), -depth / 2 + t + 0.1, depth / 2 - 0.25, zz + 0.06, zz + 0.06 + hh,
                                             self.mat(rng.choice(["linen_white", "olive_paint", "wool_oatmeal", "teal_paint", "oxblood", "mustard_paint"])))
                            folded.name = self.uid("wr_fold")
                            objs.append(folded)
                            u += w + 0.15
                        else:
                            w = 0.38
                            objs.append(slab(u, u + w, -depth / 2 + t + 0.15, depth / 2 - 0.2, zz + 0.06, zz + 0.36, self.mat(rng.choice(["leather_brown", "black", "linen_white", "oxblood"]))))
                            u += w + 0.1
        elif kind == "drawers":
            nd = e.get("count", 4)
            objs.append(slab(t, length - t, -depth / 2 + t, depth / 2 - 0.01, z0, z1 - t, wood))
            for k in range(1, nd):
                zz = z0 + (z1 - z0) * k / nd
                objs.append(slab(t + 0.05, length - t - 0.05, depth / 2 - 0.02, depth / 2 + 0.005, zz - 0.01, zz + 0.01, self.mat("black")))
            for k in range(nd):
                zz = z0 + (z1 - z0) * (k + 0.5) / nd
                objs.append(slab(length / 2 - 0.6, length / 2 + 0.6, depth / 2 - 0.005, depth / 2 + 0.05, zz - 0.03, zz + 0.03, self.mat("brass")))
        elif kind == "bins":
            nb = e.get("count", 3)
            for k in range(nb):
                u0 = t + 0.1 + k * (length - 2 * t - 0.2) / nb
                u1 = u0 + (length - 2 * t - 0.2) / nb - 0.12
                objs.append(slab(u0, u1, -depth / 2 + t + 0.1, depth / 2 - 0.15, z0 + 0.1, z0 + 2.2, self.mat("linen")))
                objs.append(slab(u0 + 0.05, u1 - 0.05, -depth / 2 + t + 0.15, depth / 2 - 0.2, z0 + 2.2, z0 + 2.3, self.mat(rng.choice(["linen_white", "oxblood", "denim"]))))
        return objs

    def gen_watch_island(self, e):
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        brass = self.mat("brass")
        objs = [box_ft(self.uid("wi_body"), x0, y0, x1, y1, z0 + 0.3, z1 - 0.35, wood, self.col),
                box_ft(self.uid("wi_toe"), x0 + 0.2, y0 + 0.2, x1 - 0.2, y1 - 0.2, z0, z0 + 0.3, self.mat("black"), self.col),
                box_ft(self.uid("wi_tray"), x0 + 0.1, y0 + 0.1, x1 - 0.1, y1 - 0.1, z1 - 0.35, z1 - 0.08, self.mat("felt_charcoal"), self.col),
                box_ft(self.uid("wi_glass"), x0 - 0.02, y0 - 0.02, x1 + 0.02, y1 + 0.02, z1 - 0.06, z1, self.mat("glass"), get_collection("glass"))]
        for (ya, yb) in ((y0, y0 + 0.02), (y1 - 0.02, y1)):
            objs.append(box_ft(self.uid("wi_rail"), x0 - 0.03, ya - 0.01, x1 + 0.03, yb + 0.01, z1 - 0.12, z1 + 0.03, brass, self.col))
        # drawer reveals on both long sides
        for k in range(1, 4):
            u = x0 + k * (x1 - x0) / 4
            for yy in (y0, y1):
                objs.append(box_ft(self.uid("reveal"), u - 0.01, yy - 0.01, u + 0.01, yy + 0.01, z0 + 0.35, z1 - 0.4, self.mat("black"), self.col))
        # eight watches in a 2 x 4 grid, straps laid flat
        cols_ = 4
        for i in range(8):
            cx = x0 + 0.5 + (i % cols_) * (x1 - x0 - 1.0) / (cols_ - 1)
            cy = y0 + 0.55 + (i // cols_) * (y1 - y0 - 1.1)
            objs.append(box_ft(self.uid("wi_strap"), cx - 0.06, cy - 0.45, cx + 0.06, cy + 0.45, z1 - 0.08, z1 - 0.06, self.mat(["leather_brown", "black", "leather_brown", "oxblood"][i % 4]), self.col))
            objs.append(cylinder_ft(self.uid("wi_watch"), (cx, cy, z1 - 0.08), 0.09, 0.05, self.mat(["brass", "stainless", "brass", "steel_black"][i % 4]), self.col, 18))
            objs.append(cylinder_ft(self.uid("wi_dial"), (cx, cy, z1 - 0.03), 0.07, 0.004, self.mat(["ceramic_white", "black", "teal", "ceramic_white"][i % 4]), self.col, 16))
        objs += self.gen_table_lamp({"pos": (x1 - 0.45, (y0 + y1) / 2, z1), "height": 1.2, "base_r": 0.15, "shade_r": 0.3, "base_m": "brass", "watts": 15})
        return objs

    def gen_media_cabinet(self, e):
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        objs = [box_ft(self.uid("mc_body"), x0, y0, x1, y1, z0 + 0.25, z1, wood, self.col),
                box_ft(self.uid("mc_toe"), x0 + 0.3, y0 + 0.2, x1 - 0.3, y1, z0, z0 + 0.25, self.mat("black"), self.col)]
        # slatted doors: vertical grooves on the front face
        face_y = y0 if e.get("face", "-y") == "-y" else y1
        objs += self.gen_panel_grooves({"b": [x0 + 0.05, face_y - 0.01, x1 - 0.05, face_y + 0.01, z0 + 0.35, z1 - 0.1], "pitch": 0.2, "width": 0.03})
        if e.get("soundbar", True):
            objs.append(box_ft(self.uid("mc_soundbar"), x0 + (x1 - x0) * 0.2, y0 + 0.3, x1 - (x1 - x0) * 0.2, y0 + 0.65, z1, z1 + 0.22, self.mat("steel_black"), self.col))
        return objs

    def gen_low_bookcase(self, e):
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        objs = [box_ft(self.uid("lb_side"), x0, y0, x0 + 0.06, y1, z0, z1, wood, self.col),
                box_ft(self.uid("lb_side"), x1 - 0.06, y0, x1, y1, z0, z1, wood, self.col),
                box_ft(self.uid("lb_top"), x0, y0, x1, y1, z1 - 0.06, z1, wood, self.col),
                box_ft(self.uid("lb_bottom"), x0, y0, x1, y1, z0, z0 + 0.06, wood, self.col)]
        back = e.get("back", "+y")
        if back == "+y":
            objs.append(box_ft(self.uid("lb_back"), x0, y1 - 0.04, x1, y1, z0, z1, wood, self.col))
        elif back == "-y":
            objs.append(box_ft(self.uid("lb_back"), x0, y0, x1, y0 + 0.04, z0, z1, wood, self.col))
        elif back == "-x":
            objs.append(box_ft(self.uid("lb_back"), x0, y0, x0 + 0.04, y1, z0, z1, wood, self.col))
        else:
            objs.append(box_ft(self.uid("lb_back"), x1 - 0.04, y0, x1, y1, z0, z1, wood, self.col))
        n = e.get("shelves", 2)
        for k in range(1, n):
            zz = z0 + (z1 - z0) * k / n
            objs.append(box_ft(self.uid("lb_shelf"), x0, y0, x1, y1, zz, zz + 0.05, wood, self.col))
        for k in range(n):
            za = z0 + 0.06 + (z1 - z0) * k / n
            zb = z0 + (z1 - z0) * (k + 1) / n - 0.02
            cav = [x0 + 0.08, y0 + 0.08, x1 - 0.08, y1 - 0.08, za, zb]
            objs += self.gen_books({"b": cav, "density": e.get("density", 0.85), "seed": e.get("seed", 5) + k})
        return objs

    def gen_toy_chest(self, e):
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        objs = [box_ft(self.uid("tc_box"), x0, y0, x1, y1, z0, z1 - 0.1, wood, self.col),
                box_ft(self.uid("tc_lid"), x0 - 0.03, y0 - 0.03, x1 + 0.03, y1 + 0.03, z1 - 0.1, z1, wood, self.col)]
        return objs

    def gen_corkboard(self, e):
        wall = e["wall"]
        u0, u1 = e["span"]
        z0, z1 = e["z"]
        dx, dy = _face_dir(wall)
        at = wall["at"]
        objs = []
        rng = random.Random(e.get("seed", 9))
        if wall["axis"] == "y":
            xs = sorted((at, at + dx * 0.06))
            objs.append(box_ft(self.uid("cork_board"), xs[0], u0, xs[1], u1, z0, z1, self.mat("cork"), self.col))
            for i in range(e.get("papers", 7)):
                pu = rng.uniform(u0 + 0.5, u1 - 0.5); pz = rng.uniform(z0 + 0.5, z1 - 0.5)
                w, h = rng.uniform(0.5, 0.9), rng.uniform(0.6, 1.0)
                paper = box_ft(self.uid("cork_paper"), xs[1] if dx > 0 else xs[0] - 0.01, pu - w / 2, (xs[1] + 0.01) if dx > 0 else xs[0], pu + w / 2, pz - h / 2, pz + h / 2, self.art_material(rng.randint(0, 999)) if rng.random() < 0.6 else self.mat("paper"), self.col)
                paper.rotation_euler = (math.radians(rng.uniform(-8, 8)), 0, 0)
                objs.append(paper)
        else:
            ys = sorted((at, at + dy * 0.06))
            objs.append(box_ft(self.uid("cork_board"), u0, ys[0], u1, ys[1], z0, z1, self.mat("cork"), self.col))
            for i in range(e.get("papers", 7)):
                pu = rng.uniform(u0 + 0.5, u1 - 0.5); pz = rng.uniform(z0 + 0.5, z1 - 0.5)
                w, h = rng.uniform(0.5, 0.9), rng.uniform(0.6, 1.0)
                paper = box_ft(self.uid("cork_paper"), pu - w / 2, ys[1] if dy > 0 else ys[0] - 0.01, pu + w / 2, (ys[1] + 0.01) if dy > 0 else ys[0], pz - h / 2, pz + h / 2, self.art_material(rng.randint(0, 999)) if rng.random() < 0.6 else self.mat("paper"), self.col)
                paper.rotation_euler = (0, math.radians(rng.uniform(-8, 8)), 0)
                objs.append(paper)
        return objs

    def gen_pantry_shelves(self, e):
        """Shallow walnut shelves on a wall with jars, tins, boxes."""
        wall = e["wall"]
        u0, u1 = e["span"]
        zs = e.get("z", [1.5, 3.25, 5.0, 6.75, 8.5])
        depth = e.get("depth", 0.85)
        dx, dy = _face_dir(wall)
        at = wall["at"]
        wood = self.mat("walnut_h")
        rng = random.Random(e.get("seed", 12))
        objs = []
        for zz in zs:
            if wall["axis"] == "y":
                xs = sorted((at, at + dx * depth))
                objs.append(box_ft(self.uid("ps_shelf"), xs[0], u0, xs[1], u1, zz, zz + 0.08, wood, self.col))
            else:
                ys = sorted((at, at + dy * depth))
                objs.append(box_ft(self.uid("ps_shelf"), u0, ys[0], u1, ys[1], zz, zz + 0.08, wood, self.col))
            u = u0 + 0.2
            while u < u1 - 0.3:
                kind = rng.random()
                if kind < 0.5:
                    r = rng.uniform(0.12, 0.2)
                    hgt = rng.uniform(0.4, 0.9)
                    c = (at + dx * depth * 0.5, u + r) if wall["axis"] == "y" else (u + r, at + dy * depth * 0.5)
                    objs.append(cylinder_ft(self.uid("ps_jar"), (c[0], c[1], zz + 0.08), r, hgt, self.mat(rng.choice(["glass", "glass", "ceramic_white", "brass", "olive_paint", "paper"])), self.col if rng.random() < 0.5 else get_collection("glass"), 14))
                    u += 2 * r + 0.08
                else:
                    w = rng.uniform(0.3, 0.7); hgt = rng.uniform(0.5, 1.0)
                    if wall["axis"] == "y":
                        xs = sorted((at + dx * 0.1, at + dx * (depth - 0.1)))
                        objs.append(box_ft(self.uid("ps_box"), xs[0], u, xs[1], u + w, zz + 0.08, zz + 0.08 + hgt, self.mat(rng.choice(["paper", "oxblood", "olive_paint", "teal", "mustard_paint", "black"])), self.col))
                    else:
                        ys = sorted((at + dy * 0.1, at + dy * (depth - 0.1)))
                        objs.append(box_ft(self.uid("ps_box"), u, ys[0], u + w, ys[1], zz + 0.08, zz + 0.08 + hgt, self.mat(rng.choice(["paper", "oxblood", "olive_paint", "teal", "mustard_paint", "black"])), self.col))
                    u += w + 0.1
        return objs

    def gen_safe_door(self, e):
        return self.gen_cabinet(dict(e, doors=1))

    def gen_coats(self, e):
        """Rod with hangers and coats along a wall (closets)."""
        return self.gen_wardrobe(dict(e, kind="hanging", drawer_h=0.0))

    # ================================================================== offices
    def gen_desk(self, e):
        """Walnut desk or built-in counter: b = top slab box (z0 = underside, z1 = top). gables at ends; optional
        monitors (count, arrangement), laptop, keyboard, mouse, lamp, headphones."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        objs = [box_ft(self.uid("desk_top"), x0, y0, x1, y1, z0, z1, wood, self.col)]
        floor = e.get("floor_z", z0 - 2.4)
        along_x = (x1 - x0) >= (y1 - y0)
        if e.get("gables", True):
            if along_x:
                objs.append(box_ft(self.uid("desk_gable"), x0, y0 + 0.1, x0 + 0.1, y1 - 0.1, floor, z0, wood, self.col))
                objs.append(box_ft(self.uid("desk_gable"), x1 - 0.1, y0 + 0.1, x1, y1 - 0.1, floor, z0, wood, self.col))
            else:
                objs.append(box_ft(self.uid("desk_gable"), x0 + 0.1, y0, x1 - 0.1, y0 + 0.1, floor, z0, wood, self.col))
                objs.append(box_ft(self.uid("desk_gable"), x0 + 0.1, y1 - 0.1, x1 - 0.1, y1, floor, z0, wood, self.col))
        else:
            for (lx, ly) in ((x0 + 0.2, y0 + 0.2), (x1 - 0.2, y0 + 0.2), (x0 + 0.2, y1 - 0.2), (x1 - 0.2, y1 - 0.2)):
                objs.append(cylinder_ft(self.uid("desk_leg"), (lx, ly, floor), 0.07, z0 - floor, wood, self.col, 10))
        # a drawer box under one end
        if e.get("drawers", True):
            if along_x:
                objs.append(box_ft(self.uid("desk_drawer"), x1 - 1.6, y0 + 0.15, x1 - 0.12, y1 - 0.15, z0 - 0.7, z0, wood, self.col))
            else:
                objs.append(box_ft(self.uid("desk_drawer"), x0 + 0.15, y1 - 1.6, x1 - 0.15, y1 - 0.12, z0 - 0.7, z0, wood, self.col))
        top = z1
        facing = e.get("facing", "+y")     # direction the sitter looks (monitors stand on the far edge)
        dxf, dyf = {"-x": (-1, 0), "+x": (1, 0), "-y": (0, -1), "+y": (0, 1)}[facing]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        # far edge line
        if facing == "+y":
            fe = y1 - 0.35
        elif facing == "-y":
            fe = y0 + 0.35
        elif facing == "+x":
            fe = x1 - 0.35
        else:
            fe = x0 + 0.35
        mons = e.get("monitors", 0)
        mw = e.get("monitor_w", 2.3)
        for i in range(mons):
            off = (i - (mons - 1) / 2) * (mw + 0.15)
            if facing in ("+y", "-y"):
                mx, my = cx + off, fe
                arm = cylinder_ft(self.uid("mon_arm"), (mx, my + (0.25 if facing == "+y" else -0.25), top), 0.06, 1.2, self.mat("steel_black"), self.col, 10)
                scr = box_ft(self.uid("mon"), mx - mw / 2, my - 0.03, mx + mw / 2, my + 0.03, top + 0.55, top + 0.55 + mw * 0.56, self.mat("screen_dark"), self.col)
                img = box_ft(self.uid("mon_img"), mx - mw / 2 + 0.05, (my - 0.035) if facing == "+y" else (my + 0.03), mx + mw / 2 - 0.05, (my - 0.03) if facing == "+y" else (my + 0.035), top + 0.6, top + 0.5 + mw * 0.56, self.mat("screen_code"), self.col)
            else:
                mx, my = fe, cy + off
                arm = cylinder_ft(self.uid("mon_arm"), (mx + (0.25 if facing == "+x" else -0.25), my, top), 0.06, 1.2, self.mat("steel_black"), self.col, 10)
                scr = box_ft(self.uid("mon"), mx - 0.03, my - mw / 2, mx + 0.03, my + mw / 2, top + 0.55, top + 0.55 + mw * 0.56, self.mat("screen_dark"), self.col)
                img = box_ft(self.uid("mon_img"), (mx - 0.035) if facing == "+x" else (mx + 0.03), my - mw / 2 + 0.05, (mx - 0.03) if facing == "+x" else (mx + 0.035), my + mw / 2 - 0.05, top + 0.6, top + 0.5 + mw * 0.56, self.mat("screen_code"), self.col)
            objs += [arm, scr, img]
        if e.get("keyboard", True):
            kx, ky = cx - dxf * 0.55, cy - dyf * 0.55
            objs.append(box_centered(self.uid("keyboard"), (kx, ky, top + 0.04), (1.35, 0.45, 0.08) if facing in ("+y", "-y") else (0.45, 1.35, 0.08), 0, self.mat("black"), self.col))
            objs.append(box_centered(self.uid("mouse"), (kx + (1.0 if facing in ("+y", "-y") else 0.0), ky + (0 if facing in ("+y", "-y") else 1.0), top + 0.06), (0.22, 0.38, 0.12), 15, self.mat("black"), self.col))
        if e.get("laptop"):
            lx, ly = e["laptop"]
            objs.append(box_centered(self.uid("laptop_base"), (lx, ly, top + 0.035), (1.15, 0.85, 0.07), 0, self.mat("stainless"), self.col))
            lid = box_centered(self.uid("laptop_lid"), (lx, ly + 0.42, top + 0.45), (1.15, 0.03, 0.78), 0, self.mat("stainless"), self.col)
            lid.rotation_euler = (math.radians(-15), 0, 0)
            objs.append(lid)
            objs.append(box_centered(self.uid("laptop_scr"), (lx, ly + 0.40, top + 0.45), (1.05, 0.02, 0.68), 0, self.mat("screen_code"), self.col).__class__ and box_centered(self.uid("laptop_scr"), (lx, ly + 0.405, top + 0.45), (1.05, 0.015, 0.68), 0, self.mat("screen_code"), self.col))
            objs[-1].rotation_euler = (math.radians(-15), 0, 0)
        if e.get("lamp"):
            lx, ly = e["lamp"]
            objs += self.gen_desk_lamp({"pos": [lx, ly, top]})
        if e.get("mug"):
            objs.append(cylinder_ft(self.uid("mug"), (e["mug"][0], e["mug"][1], top), 0.17, 0.38, self.mat(e.get("mug_m", "ceramic_white")), self.col, 18))
        if e.get("notebook"):
            objs.append(box_centered(self.uid("notebook"), (e["notebook"][0], e["notebook"][1], top + 0.03), (0.7, 0.95, 0.06), 12, self.mat("oxblood"), self.col))
        return objs

    def gen_desk_lamp(self, e):
        p = e["pos"]
        brass = self.mat("brass")
        objs = [cylinder_ft(self.uid("dl_base"), p, 0.3, 0.06, brass, self.col, 20),
                beam_between(self.uid("dl_arm"), (p[0], p[1], p[2] + 0.06), (p[0] + 0.5, p[1] + 0.2, p[2] + 1.5), 0.04, 0.04, brass, self.col),
                beam_between(self.uid("dl_arm"), (p[0] + 0.5, p[1] + 0.2, p[2] + 1.5), (p[0] + 1.1, p[1] + 0.5, p[2] + 1.35), 0.04, 0.04, brass, self.col)]
        head = cylinder_ft(self.uid("dl_head"), (p[0] + 1.1, p[1] + 0.5, p[2] + 1.05), 0.25, 0.32, brass, self.col, 18)
        objs.append(head)
        objs.append(cylinder_ft(self.uid("dl_lens"), (p[0] + 1.1, p[1] + 0.5, p[2] + 1.04), 0.2, 0.01, self.mat("lamp_glow"), self.col, 16))
        self.light(type="spot", pos=(p[0] + 1.1, p[1] + 0.5, p[2] + 1.0), aim=(p[0] + 1.3, p[1] + 0.6, p[2]), watts=e.get("watts", 8), kelvin=2700, angle=70, blend=0.8, name="desk_lamp")
        return objs

    def gen_workbench(self, e):
        """Butcher-block workbench on walnut drawer cabinets with a French-cleat tool wall above.
        b = bench box (z1 = top); wall = the wall behind it; items dict."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        block = self.mat("oak")
        objs = [box_ft(self.uid("wb_top"), x0, y0, x1, y1, z1 - 0.2, z1, block, self.col),
                box_ft(self.uid("wb_cabs"), x0 + 0.1, y0 + 0.1, x1 - 0.1, y1 - 0.1, z0 + 0.3, z1 - 0.2, wood, self.col),
                box_ft(self.uid("wb_toe"), x0 + 0.3, y0 + 0.3, x1 - 0.3, y1 - 0.3, z0, z0 + 0.3, self.mat("black"), self.col)]
        along_x = (x1 - x0) >= (y1 - y0)
        n = int(((x1 - x0) if along_x else (y1 - y0)) / 1.6)
        for k in range(1, n):
            if along_x:
                u = x0 + k * (x1 - x0) / n
                objs.append(box_ft(self.uid("reveal"), u - 0.01, y0 + 0.09, u + 0.01, y0 + 0.11, z0 + 0.35, z1 - 0.25, self.mat("black"), self.col))
            else:
                u = y0 + k * (y1 - y0) / n
                objs.append(box_ft(self.uid("reveal"), x1 - 0.11 if e.get("face", "+x") == "+x" else x0 + 0.09, u - 0.01, x1 - 0.09 if e.get("face", "+x") == "+x" else x0 + 0.11, u + 0.01, z0 + 0.35, z1 - 0.25, self.mat("black"), self.col))
        wall = e.get("wall")
        rng = random.Random(e.get("seed", 6))
        if wall:
            dx, dy = _face_dir(wall)
            at = wall["at"]
            zs0, zs1 = e.get("cleat_z", [z1 + 0.5, z1 + 4.5])
            u0, u1 = e.get("cleat_span", [y0, y1] if not along_x else [x0, x1])
            zz = zs0
            while zz < zs1:
                if wall["axis"] == "y":
                    xs = sorted((at, at + dx * 0.08))
                    objs.append(box_ft(self.uid("cleat"), xs[0], u0, xs[1], u1, zz, zz + 0.25, wood, self.col))
                else:
                    ys = sorted((at, at + dy * 0.08))
                    objs.append(box_ft(self.uid("cleat"), u0, ys[0], u1, ys[1], zz, zz + 0.25, wood, self.col))
                zz += 0.5
            # hanging tools: assorted small slabs and cylinders
            for i in range(e.get("tools", 22)):
                u = rng.uniform(u0 + 0.3, u1 - 0.3)
                tz = rng.uniform(zs0 + 0.3, zs1 - 0.3)
                kind = rng.random()
                mt = self.mat(rng.choice(["steel_black", "stainless", "oxblood", "black", "teal"]))
                if wall["axis"] == "y":
                    d0, d1 = sorted((at + dx * 0.1, at + dx * 0.25))
                    if kind < 0.5:
                        objs.append(box_ft(self.uid("tool"), d0, u - 0.05, d1, u + 0.05, tz - rng.uniform(0.3, 0.7), tz, mt, self.col))
                    else:
                        objs.append(cylinder_ft(self.uid("tool"), ((d0 + d1) / 2, u, tz - rng.uniform(0.3, 0.6)), rng.uniform(0.03, 0.08), rng.uniform(0.3, 0.7), mt, self.col, 8))
                else:
                    d0, d1 = sorted((at + dy * 0.1, at + dy * 0.25))
                    if kind < 0.5:
                        objs.append(box_ft(self.uid("tool"), u - 0.05, d0, u + 0.05, d1, tz - rng.uniform(0.3, 0.7), tz, mt, self.col))
                    else:
                        objs.append(cylinder_ft(self.uid("tool"), (u, (d0 + d1) / 2, tz - rng.uniform(0.3, 0.6)), rng.uniform(0.03, 0.08), rng.uniform(0.3, 0.7), mt, self.col, 8))
        # bench-top items
        for it in e.get("items", []):
            kind = it["kind"]
            px, py = it["pos"]
            if kind == "printer":
                objs.append(box_centered(self.uid("printer"), (px, py, z1 + 0.75), (1.5, 1.5, 1.5), 0, self.mat("steel_black"), self.col))
                objs.append(box_centered(self.uid("printer_win"), (px - 0.76 if it.get("face", "+x") == "-x" else px + 0.76, py, z1 + 0.8), (0.02, 1.1, 1.0), 0, self.mat("screen_dark"), self.col))
                self.light(type="point", pos=(px, py, z1 + 0.8), watts=2, kelvin=5000, radius=0.2, name="printer")
            elif kind == "mat":
                objs.append(box_centered(self.uid("esd_mat"), (px, py, z1 + 0.01), (it.get("w", 3.0), it.get("d", 2.0), 0.02), 0, self.mat("wool_carpet_charcoal"), self.col))
                objs.append(box_centered(self.uid("pcb"), (px + 0.3, py - 0.2, z1 + 0.04), (0.5, 0.35, 0.03), 20, self.mat("green_deep"), self.col))
            elif kind == "lamp":
                objs += self.gen_task_lamp({"pos": [px, py, z1], "rot_z": it.get("rot_z", 0)})
            elif kind == "microscope":
                objs.append(box_centered(self.uid("scope_base"), (px, py, z1 + 0.06), (0.6, 0.8, 0.12), 0, self.mat("steel_black"), self.col))
                objs.append(cylinder_ft(self.uid("scope_post"), (px, py + 0.3, z1 + 0.12), 0.06, 1.1, self.mat("steel_black"), self.col, 10))
                objs.append(cylinder_ft(self.uid("scope_head"), (px, py, z1 + 0.8), 0.12, 0.6, self.mat("stainless"), self.col, 12))
            elif kind == "psu":
                objs.append(box_centered(self.uid("psu"), (px, py, z1 + 0.35), (0.9, 1.1, 0.7), 0, self.mat("stainless"), self.col))
                objs.append(box_centered(self.uid("psu_scr"), (px - 0.46, py, z1 + 0.45), (0.02, 0.5, 0.25), 0, self.mat("screen_green"), self.col))
            elif kind == "soldering":
                objs.append(box_centered(self.uid("solder_base"), (px, py, z1 + 0.25), (0.6, 0.5, 0.5), 0, self.mat("black"), self.col))
                objs.append(cylinder_ft(self.uid("solder_iron"), (px + 0.5, py, z1 + 0.05), 0.04, 0.8, self.mat("stainless"), self.col, 8, axis="Y"))
            elif kind == "organizer":
                for rr in range(4):
                    for cc in range(6):
                        objs.append(box_centered(self.uid("drawer_small"), (px + cc * 0.32 - 0.8, py, z1 + it.get("z", 4.0) + rr * 0.4), (0.3, 0.6, 0.36), 0, self.mat("glass_frosted"), self.col))
            elif kind == "spools":
                for k in range(3):
                    objs.append(cylinder_ft(self.uid("spool"), (px, py + k * 0.75, z1 + 0.35), 0.35, 0.3, self.mat(["teal", "orange", "black"][k]), self.col, 24, axis="X"))
            elif kind == "hood":
                objs.append(box_centered(self.uid("vent_hood"), (px, py, z1 + it.get("z", 2.0) + 0.3), (2.0, 1.5, 0.6), 0, self.mat("steel_black"), self.col))
                objs.append(cylinder_ft(self.uid("vent_duct"), (px, py, z1 + it.get("z", 2.0) + 0.6), 0.25, it.get("duct_h", 5.0), self.mat("stainless"), self.col, 16))
        return objs

    def gen_task_lamp(self, e):
        p = e["pos"]
        blk = self.mat("steel_black")
        rot = math.radians(e.get("rot_z", 0))
        d = (math.cos(rot), math.sin(rot))
        objs = [box_centered(self.uid("tl_clamp"), (p[0], p[1], p[2] + 0.15), (0.3, 0.3, 0.3), 0, blk, self.col),
                beam_between(self.uid("tl_arm"), (p[0], p[1], p[2] + 0.3), (p[0] - d[0] * 0.3, p[1] - d[1] * 0.3, p[2] + 1.9), 0.04, 0.04, blk, self.col),
                beam_between(self.uid("tl_arm"), (p[0] - d[0] * 0.3, p[1] - d[1] * 0.3, p[2] + 1.9), (p[0] + d[0] * 1.2, p[1] + d[1] * 1.2, p[2] + 1.6), 0.04, 0.04, blk, self.col)]
        head = cylinder_ft(self.uid("tl_head"), (p[0] + d[0] * 1.2, p[1] + d[1] * 1.2, p[2] + 1.25), 0.28, 0.35, blk, self.col, 18)
        objs.append(head)
        objs.append(cylinder_ft(self.uid("tl_lens"), (p[0] + d[0] * 1.2, p[1] + d[1] * 1.2, p[2] + 1.24), 0.22, 0.01, self.mat("lamp_glow"), self.col, 16))
        self.light(type="spot", pos=(p[0] + d[0] * 1.2, p[1] + d[1] * 1.2, p[2] + 1.2), aim=(p[0] + d[0] * 1.5, p[1] + d[1] * 1.5, p[2]), watts=8, kelvin=3000, angle=75, blend=0.8, name="task_lamp")
        return objs

    def gen_rack(self, e):
        """24U network rack with a glass front: patch panels, switch with lit ports, servers, NAS with blinking LEDs,
        miners glowing amber, a small dashboard screen, a cool LED strip inside the frame."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        blk = self.mat("steel_black")
        face = e.get("face", "+x")
        objs = [box_ft(self.uid("rack_frame"), x0, y0, x1, y1, z0, z1, blk, self.col)]
        # front face recess with equipment slabs
        rng = random.Random(3)
        inner = (x1 - 0.02, x1 + 0.0) if face == "+x" else (x0, x0 + 0.02)
        units = [("patch", 0.35, "teal"), ("patch", 0.35, "orange"), ("switch", 0.35, "black"), ("fw", 0.3, "black"), ("server", 0.35, "stainless"),
                 ("gpu", 1.0, "black"), ("nas", 0.9, "black"), ("shelf", 0.6, "steel"), ("screen", 0.6, "screen_dark"), ("pdu", 0.3, "black"), ("ups", 0.9, "black")]
        zz = z1 - 0.35
        for (kind, h, mt) in units:
            zz -= h + 0.05
            if zz < z0 + 0.2:
                break
            fx0, fx1 = (x1 - 0.55, x1 - 0.05) if face == "+x" else (x0 + 0.05, x0 + 0.55)
            objs.append(box_ft(self.uid("rack_unit"), fx0, y0 + 0.15, fx1, y1 - 0.15, zz, zz + h, self.mat(mt if mt in ("stainless", "steel", "screen_dark") else "steel_black"), self.col))
            fface = fx1 if face == "+x" else fx0
            if kind in ("patch", "switch"):
                for i in range(16):
                    py = y0 + 0.35 + i * (y1 - y0 - 0.7) / 15
                    c = "led_green" if kind == "switch" and rng.random() < 0.7 else ("led_amber" if kind == "switch" else ("cable_blue" if mt == "teal" else "cable_orange"))
                    objs.append(box_ft(self.uid("rack_led"), min(fface, fface + (0.01 if face == "+x" else -0.01)), py - 0.03, max(fface, fface + (0.01 if face == "+x" else -0.01)), py + 0.03, zz + h * 0.4, zz + h * 0.6, self.mat(c), self.col))
                    if kind == "patch":
                        objs.append(cylinder_ft(self.uid("cable"), (fface, py, zz + h * 0.2), 0.02, 0.9, self.mat(c), self.col, 6, axis="X" if False else "Z")) if False else None
            if kind == "nas":
                for i in range(8):
                    py = y0 + 0.3 + i * (y1 - y0 - 0.6) / 7
                    objs.append(box_ft(self.uid("rack_led"), min(fface, fface + (0.01 if face == "+x" else -0.01)), py - 0.02, max(fface, fface + (0.01 if face == "+x" else -0.01)), py + 0.02, zz + 0.1, zz + 0.16, self.mat("led_blue"), self.col))
            if kind == "shelf":
                for i in range(3):
                    py = y0 + 0.5 + i * 0.9
                    objs.append(box_ft(self.uid("miner"), fx0 + 0.05, py - 0.3, fx1 - 0.05, py + 0.3, zz + 0.05, zz + 0.45, self.mat("steel_black"), self.col))
                    objs.append(box_ft(self.uid("rack_led"), min(fface, fface + (0.01 if face == "+x" else -0.01)), py - 0.15, max(fface, fface + (0.01 if face == "+x" else -0.01)), py + 0.15, zz + 0.15, zz + 0.22, self.mat("led_amber"), self.col))
            if kind == "screen":
                objs.append(box_ft(self.uid("rack_screen"), min(fface, fface + (0.01 if face == "+x" else -0.01)), y0 + 0.4, max(fface, fface + (0.01 if face == "+x" else -0.01)), y1 - 0.4, zz + 0.08, zz + h - 0.08, self.mat("screen_dash"), self.col))
        # glass front door
        gx = (x1 + 0.03, x1 + 0.06) if face == "+x" else (x0 - 0.06, x0 - 0.03)
        objs.append(box_ft(self.uid("rack_glass"), gx[0], y0 + 0.05, gx[1], y1 - 0.05, z0 + 0.15, z1 - 0.15, self.mat("glass"), get_collection("glass")))
        # cool LED strip inside the frame edges
        objs += self.gen_led_strip({"b": [x1 - 0.1 if face == "+x" else x0 + 0.05, y0 + 0.08, x1 - 0.05 if face == "+x" else x0 + 0.1, y0 + 0.12, z0 + 0.3, z1 - 0.3], "m": "emissive_cool", "watts": 3, "kelvin": 4000,
                                    "rot": (0, 90 if face == "+x" else -90, 0)})
        return objs

    # ================================================================== living room specifics
    def gen_linear_fire(self, e):
        """Linear gas fireplace: black steel firebox set in a stone surround panel, glass front, ribbon flame."""
        # firebox opening centred at (cx, cy) on the west wall face (x = at), width w, from z0 to z1
        wall = e["wall"]
        at = wall["at"]
        u, z0, z1 = e["u"], e["z0"], e["z1"]
        w = e.get("width", 5.0)
        depth = 1.2
        blk = self.mat("steel_black")
        objs = []
        dx, dy = _face_dir(wall)
        if wall["axis"] == "y":
            # optional chimney breast: a stone block proud of the wall, built as four pieces around the firebox
            # cavity (a recess cut into a solid wall would put the flames inside the wall mesh, invisible)
            br = e.get("breast")
            if br:
                bd = br.get("depth", depth + 0.1)
                s0, s1 = br["span"]
                bz0, bz1 = br["z"]
                bm = self.mat(br.get("m", "limestone"))
                fx0, fx1 = sorted((at, at - dx * bd))
                objs.append(box_ft(self.uid("breast"), fx0, s0, fx1, u - w / 2 - 0.08, bz0, bz1, bm, self.col))
                objs.append(box_ft(self.uid("breast"), fx0, u + w / 2 + 0.08, fx1, s1, bz0, bz1, bm, self.col))
                objs.append(box_ft(self.uid("breast"), fx0, u - w / 2 - 0.08, fx1, u + w / 2 + 0.08, bz0, z0 - 0.08, bm, self.col))
                objs.append(box_ft(self.uid("breast"), fx0, u - w / 2 - 0.08, fx1, u + w / 2 + 0.08, z1 + 0.08, bz1, bm, self.col))
                depth = min(depth, bd - 0.05)
            bx0, bx1 = sorted((at, at - dx * depth))
            # the firebox is a hollow: five thin black panels (back, top, bottom, two ends) open toward the glass,
            # so the flames inside are visible (a solid box here hid them entirely)
            t = 0.05
            back = (bx0, bx0 + t) if dx > 0 else (bx1 - t, bx1)
            fbi = self.mat("fire_black_int")
            objs.append(box_ft(self.uid("fire_back"), back[0], u - w / 2, back[1], u + w / 2, z0, z1, fbi, self.col))
            objs.append(box_ft(self.uid("fire_top"), bx0, u - w / 2, bx1, u + w / 2, z1 - t, z1, fbi, self.col))
            objs.append(box_ft(self.uid("fire_bottom"), bx0, u - w / 2, bx1, u + w / 2, z0, z0 + t, fbi, self.col))
            objs.append(box_ft(self.uid("fire_end"), bx0, u - w / 2, bx1, u - w / 2 + t, z0, z1, fbi, self.col))
            objs.append(box_ft(self.uid("fire_end"), bx0, u + w / 2 - t, bx1, u + w / 2, z0, z1, fbi, self.col))
            objs.append(box_ft(self.uid("fire_glass"), min(at + dx * 0.01, at + dx * 0.03), u - w / 2 + 0.05, max(at + dx * 0.01, at + dx * 0.03), u + w / 2 - 0.05, z0 + 0.05, z1 - 0.05, self.mat("glass"), get_collection("glass")))
            objs.append(box_ft(self.uid("fire_frame"), min(at, at + dx * 0.04), u - w / 2 - 0.08, max(at, at + dx * 0.04), u + w / 2 + 0.08, z0 - 0.08, z1 + 0.08, blk, self.col))
            # ember bed and flames along the length
            fcx = at - dx * depth * 0.5
            objs.append(box_ft(self.uid("embers"), bx0 + 0.2, u - w / 2 + 0.2, bx1 - 0.2, u + w / 2 - 0.2, z0 + 0.06, z0 + 0.14, self.mat("embers"), self.col))
            rng = random.Random(4)
            n = int(w / 0.28)
            for i in range(n):
                fy = u - w / 2 + 0.3 + i * (w - 0.6) / (n - 1)
                h = rng.uniform(0.55, 1.0)
                fl = sphere_ft(self.uid("flame"), (fcx + rng.uniform(-0.15, 0.15), fy, z0 + 0.15 + h * 0.45), 0.13, self.mat("fire"), self.col, 10, 8)
                fl.scale = (rng.uniform(0.7, 1.1), rng.uniform(0.8, 1.2), h / 0.26)
                fl.rotation_euler = (math.radians(rng.uniform(-10, 10)), math.radians(rng.uniform(-8, 8)), 0)
                objs.append(fl)
                if i % 2 == 0:
                    core = sphere_ft(self.uid("flame_core"), (fcx, fy, z0 + 0.15 + h * 0.25), 0.07, self.mat("fire_core"), self.col, 8, 6)
                    core.scale = (0.7, 0.8, h / 0.26 * 0.5)
                    objs.append(core)
            # rotated 90 deg about Y the area light's local X becomes world Z, so 'size' is the height and
            # 'size_y' the length along the firebox (the first cut had them swapped: a tall stripe up the stone)
            # an area light emits along its local -Z; rotating -90*dx about Y turns that toward +dx, out of the
            # firebox into the room (with +90*dx it shone back into the box and lit the glass white)
            self.light(type="area", pos=(at + dx * 0.08, u, z0 + (z1 - z0) * 0.45), size=(z1 - z0) * 0.7, size_y=w * 0.9, shape="RECTANGLE",
                       watts=e.get("watts", 25), kelvin=1900, rot=(0, math.radians(-90 * dx), 0), name="fire")
        return objs

    def gen_paneled_wall(self, e):
        """Walnut vertical-board paneling on a wall face: a thin panel plus grooves at 6 in."""
        b = e["b"]
        objs = [box_ft(self.uid("panel_wood"), *b, mat=self.mat(e.get("m", "walnut_panel")), collection=self.col)]
        x0, y0, x1, y1, z0, z1 = b
        thin_x = (x1 - x0) < (y1 - y0)
        face = e.get("face", "+x")
        if thin_x:
            fx = (x1, x1 + 0.01) if face == "+x" else (x0 - 0.01, x0)
            objs += self.gen_panel_grooves({"b": [fx[0], y0, fx[1], y1, z0, z1], "pitch": e.get("pitch", 0.5), "width": 0.025})
        else:
            fy = (y1, y1 + 0.01) if face == "+y" else (y0 - 0.01, y0)
            objs += self.gen_panel_grooves({"b": [x0, fy[0], x1, fy[1], z0, z1], "pitch": e.get("pitch", 0.5), "width": 0.025})
        return objs

    def gen_hearth_bench(self, e):
        b = e["b"]
        objs = [box_ft(self.uid("hearth"), *b, mat=self.mat(e.get("m", "limestone")), collection=self.col)]
        x0, y0, x1, y1, z0, z1 = b
        # objects: stack of books, ceramic vase, brass candle holder
        objs.append(box_ft(self.uid("hb_book"), x0 + 0.4, y0 + 2.0, x1 - 0.3, y0 + 3.0, z1, z1 + 0.12, self.mat("book_g"), self.col))
        objs.append(box_ft(self.uid("hb_book"), x0 + 0.45, y0 + 2.05, x1 - 0.35, y0 + 2.95, z1 + 0.12, z1 + 0.22, self.mat("book_b"), self.col))
        objs.append(box_ft(self.uid("hb_book"), x0 + 0.5, y0 + 2.1, x1 - 0.4, y0 + 2.9, z1 + 0.22, z1 + 0.3, self.mat("book_j"), self.col))
        objs.append(cylinder_ft(self.uid("hb_vase"), ((x0 + x1) / 2, y1 - 2.0, z1), 0.3, 1.1, self.mat("teal"), self.col, 22))
        objs.append(cylinder_ft(self.uid("hb_candle_h"), ((x0 + x1) / 2, y1 - 3.2, z1), 0.12, 0.35, self.mat("brass"), self.col, 14))
        objs.append(cylinder_ft(self.uid("hb_candle"), ((x0 + x1) / 2, y1 - 3.2, z1 + 0.35), 0.08, 0.45, self.mat("linen_white"), self.col, 12))
        objs.append(sphere_ft(self.uid("flame"), ((x0 + x1) / 2, y1 - 3.2, z1 + 0.88), 0.03, self.mat("fire_core"), self.col, 8, 6))
        self.light(type="point", pos=((x0 + x1) / 2, y1 - 3.2, z1 + 0.9), watts=1.5, kelvin=1800, radius=0.03, name="candle")
        return objs

    def gen_builtin_shelves(self, e):
        """Open walnut shelving within a paneled wall: b (depth is the thin axis), face into room, shelves n,
        contents: books + ceramics + a plant + a framed photo + a clock/globe."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        n = e.get("shelves", 5)
        objs = []
        face = e.get("face", "+x")
        rng = random.Random(e.get("seed", 14))
        # sides and shelves
        objs.append(box_ft(self.uid("bs_side"), x0, y0, x1, y0 + 0.06, z0, z1, wood, self.col))
        objs.append(box_ft(self.uid("bs_side"), x0, y1 - 0.06, x1, y1, z0, z1, wood, self.col))
        zs = [z0 + k * (z1 - z0) / n for k in range(n + 1)]
        for k, zz in enumerate(zs):
            objs.append(box_ft(self.uid("bs_shelf"), x0, y0, x1, y1, zz, zz + 0.06, wood, self.col))
            if k < n:
                cav = [x0 + 0.08, y0 + 0.1, x1 - 0.05, y1 - 0.1, zz + 0.06, zs[k + 1] - 0.02]
                filler = rng.random()
                if filler < 0.7:
                    objs += self.gen_books({"b": cav, "density": rng.uniform(0.75, 0.95), "seed": e.get("seed", 14) * 3 + k})
                    if rng.random() < 0.6:
                        self._shelf_object(cav, objs)
                else:
                    # objects shelf: ceramics, a small plant, a framed photo
                    cy = rng.uniform(y0 + 0.5, y1 - 0.5)
                    objs.append(cylinder_ft(self.uid("bs_vase"), ((x0 + x1) / 2, cy, zz + 0.06), rng.uniform(0.15, 0.25), rng.uniform(0.6, 1.0), self.mat(rng.choice(["ceramic_white", "teal", "mustard", "oxblood"])), self.col, 18))
                    objs.append(box_ft(self.uid("bs_photo"), x1 - 0.1, cy + 0.6, x1 - 0.08, cy + 1.3, zz + 0.06, zz + 0.9, self.mat("walnut"), self.col))
                    objs.append(box_ft(self.uid("bs_photo_img"), x1 - 0.11, cy + 0.66, x1 - 0.1, cy + 1.24, zz + 0.12, zz + 0.84, self.art_material(900 + k), self.col))
                    if rng.random() < 0.5:
                        objs += self.gen_books({"b": [x0 + 0.08, y0 + 0.1, x1 - 0.05, cy - 0.5, zz + 0.06, zs[k + 1] - 0.02], "density": 0.9, "seed": k})
        return objs

    def gen_records(self, e):
        """A stack of records leaning against a wall or cabinet side and a pair of small speakers."""
        p = e["pos"]
        rot = e.get("rot_z", 0)
        objs = []
        rng = random.Random(2)
        for k in range(e.get("count", 8)):
            ob = box_centered(self.uid("record"), (p[0] + k * 0.035, p[1], p[2] + 0.52), (0.03, 1.03, 1.03), rot, self.mat(rng.choice(["oxblood", "black", "paper", "teal", "mustard_paint", "olive_paint"])), self.col)
            ob.rotation_euler = (0, math.radians(-12 - k * 1.5), math.radians(rot))
            objs.append(ob)
        return objs

    def gen_speaker(self, e):
        p = e["pos"]
        objs = [box_centered(self.uid("speaker"), (p[0], p[1], p[2] + 0.55), (0.6, 0.75, 1.1), e.get("rot_z", 0), self.mat("walnut_h"), self.col),
                box_centered(self.uid("speaker_grille"), (p[0], p[1] - 0.38 if e.get("face", "-y") == "-y" else p[1] + 0.38, p[2] + 0.55), (0.52, 0.02, 1.0), e.get("rot_z", 0), self.mat("wool_carpet_charcoal"), self.col)]
        return objs

    def gen_basket(self, e):
        p = e["pos"]
        objs = [cylinder_ft(self.uid("basket"), p, e.get("radius", 0.75), e.get("height", 1.4), self.mat("wicker"), self.col, 24)]
        objs.append(box_centered(self.uid("throw"), (p[0], p[1], p[2] + e.get("height", 1.4) + 0.15), (1.2, 1.0, 0.3), 20, self.mat(e.get("throw_m", "wool_mustard")), self.col))
        return objs

    def gen_scratching_post(self, e):
        p = e["pos"]
        return [box_centered(self.uid("sp_base"), (p[0], p[1], p[2] + 0.06), (1.3, 1.3, 0.12), 0, self.mat("wool_carpet_charcoal"), self.col),
                cylinder_ft(self.uid("sp_post"), (p[0], p[1], p[2] + 0.12), 0.18, e.get("height", 3.0) - 0.2, self.mat("sisal"), self.col, 16),
                cylinder_ft(self.uid("sp_top"), (p[0], p[1], p[2] + e.get("height", 3.0) - 0.08), 0.45, 0.08, self.mat("walnut_h"), self.col, 20)]

    def gen_wall_frame(self, e):
        """One framed piece of art at a given centre on a wall: w x h, matted option."""
        wall = e["wall"]
        u, zc = e["u"], e.get("zc", 5.5)
        w, h = e.get("w", 2.0), e.get("h", 3.0)
        dx, dy = _face_dir(wall)
        at = wall["at"]
        fm = self.mat(e.get("frame_m", "walnut_h"))
        art = self.art_material(e.get("seed", 5)) if not e.get("art_m") else self.mat(e["art_m"])
        ft, fd = 0.05, 0.1
        objs = []
        matted = e.get("matted", True)
        mw = min(0.22, w * 0.12) if matted else 0.0
        if wall["axis"] == "y":
            xs = sorted((at, at + dx * fd))
            objs.append(box_ft(self.uid("frame"), xs[0], u - w / 2, xs[1], u + w / 2, zc - h / 2, zc + h / 2, fm, self.col))
            f = xs[1] if dx > 0 else xs[0]
            c = sorted((f, f + dx * 0.006))
            if matted:
                objs.append(box_ft(self.uid("canvas_mat"), c[0], u - w / 2 + ft, c[1], u + w / 2 - ft, zc - h / 2 + ft, zc + h / 2 - ft, self.mat("paper"), self.col))
                c = sorted((c[1] if dx > 0 else c[0], (c[1] if dx > 0 else c[0]) + dx * 0.004))
            objs.append(box_ft(self.uid("canvas"), c[0], u - w / 2 + ft + mw, c[1], u + w / 2 - ft - mw, zc - h / 2 + ft + mw, zc + h / 2 - ft - mw, art, self.col))
        else:
            ys = sorted((at, at + dy * fd))
            objs.append(box_ft(self.uid("frame"), u - w / 2, ys[0], u + w / 2, ys[1], zc - h / 2, zc + h / 2, fm, self.col))
            f = ys[1] if dy > 0 else ys[0]
            c = sorted((f, f + dy * 0.006))
            if matted:
                objs.append(box_ft(self.uid("canvas_mat"), u - w / 2 + ft, c[0], u + w / 2 - ft, c[1], zc - h / 2 + ft, zc + h / 2 - ft, self.mat("paper"), self.col))
                c = sorted((c[1] if dy > 0 else c[0], (c[1] if dy > 0 else c[0]) + dy * 0.004))
            objs.append(box_ft(self.uid("canvas"), u - w / 2 + ft + mw, c[0], u + w / 2 - ft - mw, c[1], zc - h / 2 + ft + mw, zc + h / 2 - ft - mw, art, self.col))
        return objs

    def gen_picture_rail(self, e):
        wall = e["wall"]
        u0, u1 = e["span"]
        z = e.get("z", 9.0)
        dx, dy = _face_dir(wall)
        at = wall["at"]
        if wall["axis"] == "y":
            xs = sorted((at, at + dx * 0.08))
            return [box_ft(self.uid("pic_rail"), xs[0], u0, xs[1], u1, z - 0.06, z + 0.06, self.mat("bronze_black"), self.col)]
        ys = sorted((at, at + dy * 0.08))
        return [box_ft(self.uid("pic_rail"), u0, ys[0], u1, ys[1], z - 0.06, z + 0.06, self.mat("bronze_black"), self.col)]

    def gen_pendant_row(self, e):
        objs = []
        for p in e["positions"]:
            objs += self.gen_globe_pendant({"pos": p, "radius": e.get("radius", 0.5), "drop": e.get("drop", 4.0), "watts": e.get("watts", 30)})
        return objs

    def gen_three_globe_pendant(self, e):
        p = e["pos"]
        objs = [cylinder_ft(self.uid("tg_canopy"), (p[0], p[1], p[2] - 0.08), 0.35, 0.08, self.mat("brass"), self.col, 20)]
        for i, (dx, dy, drop) in enumerate(((-0.6, 0, 1.4), (0.5, 0.35, 1.9), (0.3, -0.5, 1.1))):
            objs.append(cylinder_ft(self.uid("tg_stem"), (p[0] + dx, p[1] + dy, p[2] - drop), 0.02, drop - 0.08, self.mat("brass"), self.col, 6))
            objs.append(sphere_ft(self.uid("tg_globe"), (p[0] + dx, p[1] + dy, p[2] - drop - 0.35), 0.38, self.mat("lamp_shade"), self.col))
            self.light(type="point", pos=(p[0] + dx, p[1] + dy, p[2] - drop - 0.35), watts=14, radius=0.3, name="three_globe")
        return objs
