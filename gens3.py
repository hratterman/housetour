"""gens3: gym, garage and vehicles, pit furnishings, mechanical room, exterior fixtures, the spec mudroom lockers,
the spec bar. Mixed into Stager together with gens2."""
import math
import random

import bpy
from mathutils import Vector, Matrix

from geom import (FT, IN, m, log, box_ft, box_local, box_centered, beam_between, cylinder_ft, sphere_ft,
                  prism_yz, prism_xz, get_collection, _mesh_from_pydata, link)


def _face_dir(wall):
    return {"-x": (-1, 0), "+x": (1, 0), "-y": (0, -1), "+y": (0, 1)}[wall["face"]]


class Gens3:
    # ================================================================== mudroom (spec 3.11)
    def gen_lockers2(self, e):
        """Four open walnut lockers along a wall (back at y1), bench seat at 1.5, hook rail at 5, cubby shelf at 6,
        closed cabinet doors 7 to 9.5. b = [x0,y0,x1,y1,z0,z1]; dividers at given X."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        objs = [box_ft(self.uid("lk_back"), x0, y1 - 0.06, x1, y1, z0, z1, wood, self.col)]
        divs = [x0] + e.get("dividers", [2.5, 4.5, 6.5]) + [x1]
        for u in divs:
            objs.append(box_ft(self.uid("lk_div"), u - 0.04, y0, u + 0.04, y1, z0, z1, wood, self.col))
        objs.append(box_ft(self.uid("lk_seat"), x0, y0, x1, y1, z0 + 1.4, z0 + 1.55, wood, self.col))
        objs.append(box_ft(self.uid("lk_seat_face"), x0, y0, x1, y0 + 0.06, z0 + 0.3, z0 + 1.4, wood, self.col))
        objs.append(box_ft(self.uid("lk_cubby"), x0, y0, x1, y1, z0 + 6.0, z0 + 6.06, wood, self.col))
        objs.append(box_ft(self.uid("lk_top"), x0, y0, x1, y1, z0 + 7.0 - 0.06, z0 + 7.0, wood, self.col))
        objs += self.gen_cabinet({"b": [x0, y0, x1, y1, z0 + 7.0, z1], "doors": len(divs) - 1, "face": "-y"})
        rng = random.Random(4)
        for i in range(len(divs) - 1):
            cx = (divs[i] + divs[i + 1]) / 2
            for hu in (cx - 0.5, cx + 0.5):
                objs.append(box_ft(self.uid("hook"), hu - 0.03, y1 - 0.35, hu + 0.03, y1 - 0.06, z0 + 5.0, z0 + 5.06, self.mat("brass"), self.col))
            objs.append(box_ft(self.uid("hook_rail"), divs[i] + 0.1, y1 - 0.1, divs[i + 1] - 0.1, y1 - 0.06, z0 + 4.95, z0 + 5.1, wood, self.col))
            # shoes in the bench cubby, a bag or coat in some bays
            for k in range(2):
                sx = divs[i] + 0.3 + k * 0.7
                objs.append(box_ft(self.uid("shoe"), sx, y0 + 0.3, sx + 0.35, y0 + 1.15, z0 + 0.3, z0 + 0.58, self.mat(rng.choice(["leather_brown", "black", "linen_white", "oxblood"])), self.col))
            if i in (0, 2):
                objs.append(box_ft(self.uid("jacket"), cx - 0.7, y1 - 0.7, cx + 0.7, y1 - 0.12, z0 + 2.3, z0 + 4.9, self.mat(["oxblood", "olive_paint"][i // 2]), self.col))
            if i == 1:
                objs.append(box_ft(self.uid("bag"), cx - 0.45, y1 - 0.75, cx + 0.45, y1 - 0.15, z0 + 3.4, z0 + 4.9, self.mat("teal"), self.col))
            # cubby contents: a hat, a basket
            objs.append(box_ft(self.uid("basket_sq"), divs[i] + 0.2, y0 + 0.2, divs[i + 1] - 0.2, y1 - 0.2, z0 + 6.06, z0 + 6.7, self.mat("wicker"), self.col))
        # charging drawer with a cable in the east bay
        objs.append(box_ft(self.uid("lk_drawer"), divs[-2] + 0.1, y0 - 0.02, x1 - 0.1, y0 + 0.02, z0 + 1.8, z0 + 2.3, wood, self.col))
        objs.append(cylinder_ft(self.uid("cable"), (x1 - 0.5, y0 - 0.02, z0 + 0.4), 0.02, 1.6, self.mat("black"), self.col, 6))
        return objs

    # ================================================================== gym (spec 5.2)
    def gen_platform(self, e):
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        objs = [box_ft(self.uid("plat_oak"), x0 + (x1 - x0) * 0.3, y0, x0 + (x1 - x0) * 0.7, y1, z0, z1, self.mat("oak_platform"), self.col),
                box_ft(self.uid("plat_rub"), x0, y0, x0 + (x1 - x0) * 0.3, y1, z0, z1, self.mat("rubber_floor"), self.col),
                box_ft(self.uid("plat_rub"), x0 + (x1 - x0) * 0.7, y0, x1, y1, z0, z1, self.mat("rubber_floor"), self.col)]
        return objs

    def gen_plate_tree(self, e):
        p = e["pos"]
        blk = self.mat("steel_black")
        objs = [box_centered(self.uid("pt_base"), (p[0], p[1], p[2] + 0.06), (2.0, 1.4, 0.12), 0, blk, self.col),
                cylinder_ft(self.uid("pt_post"), (p[0], p[1], p[2] + 0.12), 0.09, 3.6, blk, self.col, 12)]
        rng = random.Random(1)
        for k, zz in enumerate((0.9, 1.7, 2.5, 3.2)):
            for sx in (-1, 1):
                objs.append(cylinder_ft(self.uid("pt_peg"), (p[0], p[1], p[2] + zz), 0.05, 0.9 * sx, blk, self.col, 8, axis="X") if False else
                            cylinder_ft(self.uid("pt_peg"), (p[0] + (0 if sx > 0 else -0.9), p[1], p[2] + zz), 0.05, 0.9, blk, self.col, 8, axis="X"))
                for i in range(rng.randint(1, 3)):
                    r = [0.75, 0.62, 0.5, 0.4][k]
                    objs.append(cylinder_ft(self.uid("plate"), (p[0] + sx * (0.25 + i * 0.14), p[1], p[2] + zz), r, 0.1, self.mat(rng.choice(["iron_plate", "iron_plate", "rubber_red"])), self.col, 24, axis="X"))
        return objs

    def gen_kettlebells(self, e):
        p = e["pos"]
        objs = []
        for i, r in enumerate((0.3, 0.34, 0.38)):
            cx = p[0] + i * 0.95
            kb = sphere_ft(self.uid("kb"), (cx, p[1], p[2] + r), r, self.mat("steel_black"), self.col, 16, 10)
            objs.append(kb)
            objs.append(cylinder_ft(self.uid("kb_handle"), (cx - 0.22, p[1], p[2] + 2 * r + 0.15), 0.05, 0.44, self.mat("steel_black"), self.col, 10, axis="X"))
            for sx in (-0.22, 0.22):
                objs.append(cylinder_ft(self.uid("kb_handle"), (cx + sx, p[1], p[2] + r), 0.05, r + 0.15, self.mat("steel_black"), self.col, 10))
        return objs

    def gen_rings(self, e):
        p = e["pos"]          # ceiling mount point
        drop = e.get("drop", 5.0)
        objs = [cylinder_ft(self.uid("ring_mount"), (p[0], p[1], p[2] - 0.05), 0.15, 0.05, self.mat("steel_black"), self.col, 16)]
        for sx in (-0.9, 0.9):
            objs.append(cylinder_ft(self.uid("ring_strap"), (p[0] + sx, p[1], p[2] - drop), 0.02, drop, self.mat("canvas_tan"), self.col, 6))
            ring = cylinder_ft(self.uid("ring"), (p[0] + sx, p[1] + 0.04, p[2] - drop - 0.45), 0.45, 0.08, self.mat("walnut_h"), self.col, 32, axis="Y")
            objs.append(ring)
            objs.append(cylinder_ft(self.uid("ring_hole"), (p[0] + sx, p[1] + 0.03, p[2] - drop - 0.45), 0.37, 0.1, self.mat("plaster_warm"), self.col, 32, axis="Y")) if False else None
        return objs

    def gen_floor_fan(self, e):
        p = e["pos"]
        blk = self.mat("steel_black")
        objs = [cylinder_ft(self.uid("fan_base"), p, 0.9, 0.1, blk, self.col, 24),
                box_centered(self.uid("fan_post"), (p[0], p[1], p[2] + 0.6), (0.3, 0.3, 1.0), 0, blk, self.col),
                cylinder_ft(self.uid("fan_drum"), (p[0], p[1] - 0.35, p[2] + 2.6), 1.5, 0.7, blk, self.col, 32, axis="Y"),
                cylinder_ft(self.uid("fan_grille"), (p[0], p[1] - 0.36, p[2] + 2.6), 1.3, 0.02, self.mat("screen_black"), self.col, 32, axis="Y")]
        return objs

    def gen_treadmill(self, e):
        p = e["pos"]
        rot = e.get("rot_z", 0)
        blk = self.mat("steel_black")
        objs = [box_centered(self.uid("tm_deck"), (p[0], p[1], p[2] + 0.4), (6.5, 2.8, 0.5), rot, blk, self.col),
                box_centered(self.uid("tm_belt"), (p[0] + 0.2, p[1], p[2] + 0.66), (5.4, 1.8, 0.02), rot, self.mat("rubber_floor"), self.col)]
        r = math.radians(rot)
        fx, fy = p[0] + math.cos(r) * -2.9, p[1] + math.sin(r) * -2.9
        for sy in (-1.1, 1.1):
            ux, uy = fx - math.sin(r) * sy, fy + math.cos(r) * sy
            objs.append(box_centered(self.uid("tm_upright"), (ux, uy, p[2] + 2.5), (0.25, 0.25, 4.2), rot, blk, self.col))
            objs.append(box_centered(self.uid("tm_rail"), (p[0] + math.cos(r) * -1.3 - math.sin(r) * sy, p[1] + math.sin(r) * -1.3 + math.cos(r) * sy, p[2] + 3.4), (3.2, 0.15, 0.15), rot, blk, self.col))
        console = box_centered(self.uid("tm_console"), (fx, fy, p[2] + 4.5), (0.5, 2.4, 1.2), rot, blk, self.col)
        console.rotation_euler = (0, math.radians(-25), r)
        objs.append(console)
        scr = box_centered(self.uid("tm_screen"), (fx + math.cos(r) * 0.27, fy + math.sin(r) * 0.27, p[2] + 4.6), (0.02, 1.9, 0.9), rot, self.mat("screen_dash"), self.col)
        scr.rotation_euler = (0, math.radians(-25), r)
        objs.append(scr)
        return objs

    def gen_towel_shelf(self, e):
        p = e["pos"]
        objs = [box_centered(self.uid("ts_shelf"), (p[0], p[1], p[2]), (0.6, 2.4, 0.08), 0, self.mat("steel_black"), self.col)]
        for i in range(4):
            objs.append(cylinder_ft(self.uid("towel"), (p[0] - 0.25, p[1] - 0.9 + i * 0.6, p[2] + 0.04 + 0.22), 0.22, 0.5, self.mat("towel_white"), self.col, 12, axis="X"))
        return objs

    def gen_wall_clock(self, e):
        wall = e["wall"]
        u, z = e["u"], e.get("z", 7.0)
        dx, dy = _face_dir(wall)
        at = wall["at"]
        if wall["axis"] == "y":
            return [cylinder_ft(self.uid("clock"), (at + dx * 0.0, u, z), 0.55, 0.12, self.mat("steel_black"), self.col, 32, axis="X"),
                    cylinder_ft(self.uid("clock_face"), (at + dx * 0.1, u, z), 0.48, 0.02, self.mat("ceramic_white"), self.col, 32, axis="X")]
        return [cylinder_ft(self.uid("clock"), (u, at, z), 0.55, 0.12, self.mat("steel_black"), self.col, 32, axis="Y"),
                cylinder_ft(self.uid("clock_face"), (u, at + dy * 0.1, z), 0.48, 0.02, self.mat("ceramic_white"), self.col, 32, axis="Y")]

    def gen_band_rail(self, e):
        wall = e["wall"]
        u, z = e["u"], e.get("z", 5.0)
        dx, dy = _face_dir(wall)
        at = wall["at"]
        objs = []
        rng = random.Random(6)
        if wall["axis"] == "y":
            objs.append(box_ft(self.uid("band_rail"), min(at, at + dx * 0.25), u - 1.5, max(at, at + dx * 0.25), u + 1.5, z - 0.05, z + 0.05, self.mat("steel_black"), self.col))
            for i in range(6):
                bu = u - 1.2 + i * 0.48
                objs.append(box_ft(self.uid("band"), min(at + dx * 0.1, at + dx * 0.2), bu - 0.06, max(at + dx * 0.1, at + dx * 0.2), bu + 0.06, z - rng.uniform(2.0, 3.2), z - 0.05, self.mat(rng.choice(["rubber_red", "black", "teal", "olive_paint"])), self.col))
        return objs

    def gen_poster(self, e):
        """Framed vintage athletics poster: art canvas with a big colour block; use the frame helper."""
        return self.gen_wall_frame(dict(e, matted=False, frame_m="black"))

    def gen_yoga_basket(self, e):
        p = e["pos"]
        objs = [cylinder_ft(self.uid("basket"), p, 0.8, 1.6, self.mat("wicker"), self.col, 24)]
        for i, c in enumerate(("teal", "oxblood", "black")):
            objs.append(cylinder_ft(self.uid("mat_roll"), (p[0] + (i - 1) * 0.3, p[1] + (i % 2) * 0.25 - 0.1, p[2] + 0.1), 0.2, 2.2 if i < 2 else 1.8, self.mat(c), self.col, 14))
        return objs

    # ================================================================== lounge pit (spec 5.4)
    def gen_pit_furnish(self, e):
        """Banquette in teal velvet on three sides of the pit, walnut cap, three steps on the north side, shag rug,
        pillows, round table. Uses the pit bounds from the plan (the slab cut and pit walls exist already)."""
        x0, y0, x1, y1 = e["b"]
        zf = e["floor_z"]            # pit floor
        zr = e["room_z"]             # room floor
        vel = self.mat(e.get("m", "velvet_teal"))
        wood = self.mat("walnut_h")
        objs = []
        d = 2.5
        seat_top = zr - 0.3
        back_top = zr + 0.9
        # seats and backs on S, W, E
        objs.append(box_ft(self.uid("pit_seat"), x0 + 0.25, y0 + 0.25, x1 - 0.25, y0 + 0.25 + d, zf, seat_top, vel, self.col))
        objs.append(box_ft(self.uid("pit_seat"), x0 + 0.25, y0 + 0.25 + d, x0 + 0.25 + d, y1 - 3.0, zf, seat_top, vel, self.col))
        objs.append(box_ft(self.uid("pit_seat"), x1 - 0.25 - d, y0 + 0.25 + d, x1 - 0.25, y1 - 3.0, zf, seat_top, vel, self.col))
        objs.append(box_ft(self.uid("pit_back"), x0 + 0.25, y0 + 0.25, x1 - 0.25, y0 + 0.75, seat_top, back_top, vel, self.col))
        objs.append(box_ft(self.uid("pit_back"), x0 + 0.25, y0 + 0.75, x0 + 0.75, y1 - 3.0, seat_top, back_top, vel, self.col))
        objs.append(box_ft(self.uid("pit_back"), x1 - 0.75, y0 + 0.75, x1 - 0.25, y1 - 3.0, seat_top, back_top, vel, self.col))
        # walnut cap along the three backs
        objs.append(box_ft(self.uid("pit_cap"), x0 - 0.1, y0 - 0.1, x1 + 0.1, y0 + 0.5, back_top, back_top + 0.1, wood, self.col))
        objs.append(box_ft(self.uid("pit_cap"), x0 - 0.1, y0 + 0.5, x0 + 0.5, y1 - 3.0, back_top, back_top + 0.1, wood, self.col))
        objs.append(box_ft(self.uid("pit_cap"), x1 - 0.5, y0 + 0.5, x1 + 0.1, y1 - 3.0, back_top, back_top + 0.1, wood, self.col))
        # three walnut steps down on the north side
        rise = (zr - zf) / 3
        for k in range(3):
            objs.append(box_ft(self.uid("pit_step"), x0 + 0.25, y1 - 3.0 + k * 1.0, x1 - 0.25, y1 - 3.0 + (k + 1) * 1.0, zf, zf + rise * (k + 1), wood, self.col))
        # shag rug on the pit floor
        objs.append(box_ft(self.uid("rug_shag"), x0 + 0.25 + d + 0.2, y0 + 0.25 + d + 0.2, x1 - 0.25 - d - 0.2, y1 - 3.2, zf + 0.002, zf + 0.09, self.mat("wool_oatmeal"), self.col))
        # pillows
        objs += self.gen_cushions({"b": [x0 + 0.6, y0 + 0.5, x1 - 0.6, y0 + 0.5 + d], "z": seat_top, "back": "-y", "count": 4, "seed": 21, "mats": ["wool_mustard", "oxblood", "olive_paint", "wool_oatmeal"]})
        objs += self.gen_cushions({"b": [x0 + 0.6, y0 + d + 0.6, x0 + 0.6 + d, y1 - 3.3], "z": seat_top, "back": "-x", "count": 3, "seed": 22, "mats": ["wool_mustard", "oxblood", "wool_oatmeal"]})
        objs += self.gen_cushions({"b": [x1 - 0.6 - d, y0 + d + 0.6, x1 - 0.6, y1 - 3.3], "z": seat_top, "back": "+x", "count": 2, "seed": 23, "mats": ["olive_paint", "oxblood"]})
        # low round table with popcorn and two glasses
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        objs += self.gen_round_table({"pos": [cx, cy, zf], "radius": 1.25, "height": 1.0})
        bowl = sphere_ft(self.uid("popcorn_bowl"), (cx, cy, zf + 1.0 + 0.2), 0.45, self.mat("ceramic_white"), self.col)
        bowl.scale = (1, 1, 0.45)
        objs.append(bowl)
        rng = random.Random(9)
        for i in range(18):
            objs.append(sphere_ft(self.uid("popcorn"), (cx + rng.uniform(-0.3, 0.3), cy + rng.uniform(-0.3, 0.3), zf + 1.0 + 0.3 + rng.uniform(0, 0.12)), 0.06, self.mat("linen_white"), self.col, 6, 4))
        for (gx, gy) in ((cx + 0.8, cy - 0.5), (cx - 0.7, cy + 0.6)):
            objs.append(cylinder_ft(self.uid("glass"), (gx, gy, zf + 1.0), 0.14, 0.4, self.mat("glass"), get_collection("glass"), 16))
        return objs

    def gen_cabinet_row(self, e):
        objs = self.gen_cabinet(e)
        b = e["b"]
        if e.get("games"):
            for k in range(5):
                objs.append(box_ft(self.uid("game_box"), b[0] + 0.1, b[1] + 0.3 + k * 0.05, b[2] - 0.1, b[3] - 0.3 - k * 0.03, b[5] + k * 0.18, b[5] + (k + 1) * 0.18, self.mat(["oxblood", "teal", "mustard_paint", "black", "olive_paint"][k]), self.col))
        return objs

    def gen_game_table(self, e):
        p = e["pos"]
        objs = self.gen_square_table({"pos": p, "length": 4.0, "depth": 4.0, "height": 2.45})
        objs += self.gen_puzzle({"b": [p[0] - 1.2, p[1] - 0.9, p[0] + 1.2, p[1] + 0.9], "z": p[2] + 2.46, "seed": 44})
        # dining chairs face -Y at rot 0; each turns toward the table centre
        sides = e.get("chairs", "nsew")
        for (side, dx, dy, rot) in (("s", 0, -2.6, 180), ("n", 0, 2.6, 0), ("w", -2.6, 0, 90), ("e", 2.6, 0, -90)):
            if side not in sides:
                continue
            objs += self.gen_dining_chair({"pos": [p[0] + dx, p[1] + dy, p[2]], "rot_z": rot, "m": "leather_brown"})
        return objs

    # ================================================================== bar (spec 5.5)
    def gen_bar2(self, e):
        z = e.get("z", -10.0)
        objs = []
        wood = self.mat("walnut_h")
        terr = self.mat("terrazzo")
        brass = self.mat("brass")
        gc = get_collection("glass")
        # counter 23-25 x 36-45, top at -6.5 with a brass edge band on the guest (west) side
        objs.append(box_ft(self.uid("bar_body"), 23.0, 36.0, 25.0, 45.0, z + 0.3, z + 3.4, wood, self.col))
        objs.append(box_ft(self.uid("bar_toe"), 23.3, 36.0, 25.0, 45.0, z, z + 0.3, self.mat("black"), self.col))
        objs.append(box_ft(self.uid("bar_top"), 22.85, 35.9, 25.1, 45.1, z + 3.4, z + 3.5, terr, self.col))
        objs.append(box_ft(self.uid("bar_edge"), 22.82, 35.88, 22.9, 45.12, z + 3.36, z + 3.52, brass, self.col))
        objs.append(box_ft(self.uid("bar_footrail"), 22.5, 36.2, 22.56, 44.8, z + 0.7, z + 0.76, brass, self.col))
        objs += self.gen_panel_grooves({"b": [22.99, 36.2, 23.01, 44.8, z + 0.4, z + 3.3], "pitch": 0.25, "width": 0.025})
        # undercounter sink at the south end, service side
        objs.append(box_ft(self.uid("bar_sink"), 23.4, 36.5, 24.6, 37.5, z + 2.9, z + 3.51, brass, self.col))
        objs.append(box_ft(self.uid("bar_sink_hole"), 23.45, 36.55, 24.55, 37.45, z + 2.95, z + 3.52, self.mat("steel_black"), self.col))
        objs.append(cylinder_ft(self.uid("bar_faucet"), (24.7, 37.0, z + 3.5), 0.035, 0.9, brass, self.col, 8))
        objs.append(cylinder_ft(self.uid("bar_faucet"), (24.1, 37.0, z + 4.35), 0.03, 0.6, brass, self.col, 8, axis="X"))
        # back-bar counter along the east wall 25.5-27.8 x 35-45 at -7.0, drawer fridge 43-45, ice machine 40.5-42.5
        objs.append(box_ft(self.uid("bb_cabs"), 25.5, 35.0, 27.8, 45.0, z + 0.3, z + 2.9, wood, self.col))
        objs.append(box_ft(self.uid("bb_toe"), 25.5, 35.0, 27.8, 45.0, z, z + 0.3, self.mat("black"), self.col))
        objs.append(box_ft(self.uid("bb_top"), 25.45, 35.0, 27.85, 45.0, z + 2.9, z + 3.0, terr, self.col))
        for u in (37.5, 40.0):
            objs.append(box_ft(self.uid("reveal"), 25.49, u - 0.01, 25.51, u + 0.01, z + 0.4, z + 2.85, self.mat("black"), self.col))
        objs += self.gen_fridge_small({"b": [25.5, 43.0, 27.5, 45.0, z, z + 2.5], "face": "-x"})
        objs.append(box_ft(self.uid("ice_machine"), 25.5, 40.5, 27.5, 42.5, z, z + 2.8, self.mat("stainless"), self.col))
        objs.append(box_ft(self.uid("ice_door"), 25.48, 40.7, 25.5, 42.3, z + 0.4, z + 2.4, self.mat("chrome_dark"), self.col))
        # espresso machine chrome and walnut at (26.5, 37.5, -7)
        objs.append(box_ft(self.uid("espresso"), 25.8, 36.8, 27.3, 38.2, z + 3.0, z + 4.2, self.mat("chrome"), self.col))
        objs.append(box_ft(self.uid("espresso_wood"), 25.75, 36.75, 27.35, 38.25, z + 3.3, z + 3.6, wood, self.col))
        objs.append(box_ft(self.uid("espresso_top"), 25.85, 36.85, 27.25, 38.15, z + 4.2, z + 4.35, self.mat("steel_black"), self.col))
        for pu in (37.1, 37.9):
            objs.append(cylinder_ft(self.uid("espresso_pf"), (25.7, pu, z + 3.45), 0.04, 0.5, self.mat("walnut"), self.col, 8, axis="X"))
        # brass and glass shelves at -5.5 and -4.0, Y 35-45 on the east wall
        rng = random.Random(33)
        for zz in (z + 4.5, z + 6.0):
            objs.append(box_ft(self.uid("bb_shelf_glass"), 26.7, 35.2, 27.75, 44.8, zz, zz + 0.04, self.mat("glass"), gc))
            for yy in (35.4, 40.0, 44.6):
                objs.append(box_ft(self.uid("bb_bracket"), 26.8, yy - 0.04, 27.75, yy + 0.04, zz - 0.06, zz, brass, self.col))
            objs += self.gen_led_strip({"b": [27.62, 35.3, 27.72, 44.7, zz + 0.04, zz + 0.07], "watts": 5})
            for i in range(14):
                yy = 35.6 + rng.uniform(0, 8.8)
                kind = rng.random()
                if kind < 0.55:
                    objs.append(cylinder_ft(self.uid("glassware"), (27.1 + rng.uniform(-0.2, 0.2), yy, zz + 0.04), rng.uniform(0.1, 0.16), rng.uniform(0.3, 0.7),
                                            self.mat(rng.choice(["glass", "glass", "teal_glass", "amber_glass"])), gc, 14))
                else:
                    objs.append(cylinder_ft(self.uid("bottle"), (27.2 + rng.uniform(-0.15, 0.15), yy, zz + 0.04), 0.13, rng.uniform(0.8, 1.05), self.mat(rng.choice(["amber_glass", "green_glass", "glass", "black"])), gc, 12))
                    objs.append(cylinder_ft(self.uid("bottle_neck"), (27.3, yy, zz + 0.04 + 0.9), 0.05, 0.3, self.mat("green_glass"), gc, 10)) if False else None
        objs.append(cylinder_ft(self.uid("shaker"), (27.1, 42.0, z + 4.54), 0.15, 0.7, self.mat("stainless"), self.col, 16))
        # cake stand under a dome at the north end of the counter, bowl of lemons, bar lamp
        objs.append(cylinder_ft(self.uid("cake_stand"), (24.0, 44.0, z + 3.5), 0.5, 0.08, self.mat("ceramic_white"), self.col, 28))
        objs.append(cylinder_ft(self.uid("cake_stem"), (24.0, 44.0, z + 3.58), 0.1, 0.35, self.mat("ceramic_white"), self.col, 14))
        objs.append(cylinder_ft(self.uid("cake_plate"), (24.0, 44.0, z + 3.93), 0.55, 0.05, self.mat("ceramic_white"), self.col, 32))
        objs.append(cylinder_ft(self.uid("cake"), (24.0, 44.0, z + 3.98), 0.4, 0.45, self.mat("cake_cream"), self.col, 28))
        for k in (0.15, 0.3):
            objs.append(cylinder_ft(self.uid("cake_layer"), (24.0, 44.0, z + 3.98 + k), 0.405, 0.025, self.mat("oxblood"), self.col, 28))
        dome = sphere_ft(self.uid("cake_dome"), (24.0, 44.0, z + 3.98), 0.62, self.mat("glass"), gc, 24, 12)
        dome.scale = (1, 1, 1.15)
        objs.append(dome)
        # a second surface just inside makes it a hollow shell instead of a solid glass lens
        inner = sphere_ft(self.uid("cake_dome_in"), (24.0, 44.0, z + 3.98), 0.62, self.mat("glass"), gc, 24, 12)
        inner.scale = tuple(v * 0.955 for v in (1, 1, 1.15))
        objs.append(inner)
        lb = sphere_ft(self.uid("lemon_bowl"), (24.0, 42.5, z + 3.5 + 0.15), 0.42, self.mat("ceramic_white"), self.col)
        lb.scale = (1, 1, 0.38)
        objs.append(lb)
        for i in range(5):
            a = i * 1.3
            lem = sphere_ft(self.uid("lemon"), (24.0 + math.cos(a) * 0.18, 42.5 + math.sin(a) * 0.18, z + 3.5 + 0.28 + (0.18 if i == 4 else 0)), 0.11, self.mat("mustard_paint"), self.col, 12, 8)
            lem.scale = (1.25, 1, 1)
            objs.append(lem)
        objs += self.gen_table_lamp({"pos": (24.0, 36.6, z + 3.5), "height": 1.4, "base_r": 0.18, "shade_r": 0.38, "base_m": "brass", "watts": 18})
        # cabinet under the counter (service side) with the dessert program: reveals on the east face
        for u in (39.0, 42.0):
            objs.append(box_ft(self.uid("reveal"), 24.99, u - 0.01, 25.01, u + 0.01, z + 0.4, z + 3.3, self.mat("black"), self.col))
        return objs

    # ================================================================== mechanical (spec 5.8)
    def gen_mechanical(self, e):
        z = e.get("z", -10.0)
        objs = []
        st = self.mat("stainless")
        objs += self.gen_water_heater({"pos": [40.0, 15.0, z]})
        objs.append(cylinder_ft(self.uid("hpwh"), (40.0, 18.5, z), 1.05, 6.4, self.mat("galvanized"), self.col, 24))
        objs.append(box_ft(self.uid("hpwh_top"), 39.0, 17.5, 41.0, 19.5, z + 6.4, z + 7.2, self.mat("steel_black"), self.col))
        # manifold board on the east wall Y 20-30 with red and blue PEX
        objs.append(box_ft(self.uid("manifold_board"), 40.8, 20.0, 40.98, 30.0, z + 2.0, z + 6.5, self.mat("plaster_warm"), self.col))
        for k in range(12):
            yy = 20.5 + k * 0.8
            c = "pex_red" if k % 2 else "pex_blue"
            objs.append(cylinder_ft(self.uid("pex"), (40.65, yy, z + 2.2), 0.04, 3.8, self.mat(c), self.col, 8))
        objs.append(cylinder_ft(self.uid("manifold"), (40.6, 20.2, z + 6.0), 0.12, 9.6, self.mat("copper"), self.col, 12, axis="Y"))
        objs.append(cylinder_ft(self.uid("manifold"), (40.6, 20.2, z + 2.3), 0.12, 9.6, self.mat("copper"), self.col, 12, axis="Y"))
        # ERV hung near the ceiling, ducts
        objs.append(box_ft(self.uid("erv"), 30.0, 28.5, 34.0, 31.5, z + 7.2, z + 9.0, self.mat("galvanized"), self.col))
        for (x, y0_, y1_) in ((31.0, 13.5, 28.5), (33.0, 13.5, 28.5)):
            # cylinder_ft centres an X/Y cylinder on its centre point, so pass the midpoint (it used to start at y0_ and run 7.5 ft into the stair hall)
            objs.append(cylinder_ft(self.uid("duct"), (x, (y0_ + y1_) / 2, z + 8.6), 0.5, y1_ - y0_, self.mat("duct_silver"), self.col, 18, axis="Y"))
        objs.append(cylinder_ft(self.uid("duct"), (34.6, 20.0, z + 8.6), 0.5, 12.0, self.mat("duct_silver"), self.col, 18, axis="X"))   # X 28.6-40.6, inside the room
        # dehumidifier, media filter, sump and ejector lids, softener stack
        objs.append(box_ft(self.uid("dehum"), 36.0, 30.0, 37.6, 31.6, z, z + 2.3, self.mat("plaster_warm"), self.col))
        objs.append(box_ft(self.uid("filter_cab"), 34.5, 14.0, 36.5, 16.0, z + 1.0, z + 5.0, self.mat("galvanized"), self.col))
        for (cx, cy) in ((30.0, 32.0), (33.0, 32.0)):
            objs.append(cylinder_ft(self.uid("sump_lid"), (cx, cy, z), 1.0, 0.2, self.mat("steel_black"), self.col, 24))
            for k in range(6):
                a = k * math.pi / 3
                objs.append(cylinder_ft(self.uid("bolt"), (cx + math.cos(a) * 0.85, cy + math.sin(a) * 0.85, z + 0.2), 0.04, 0.05, st, self.col, 8))
        for i, (r, h) in enumerate(((0.55, 5.0), (0.55, 5.0), (0.45, 3.5))):
            objs.append(cylinder_ft(self.uid("softener"), (40.2 - i * 1.3, 32.0, z), r, h, self.mat(["steel_black", "steel_black", "plaster_warm"][i]), self.col, 20))
        # labels
        rng = random.Random(3)
        for i in range(10):
            objs.append(box_ft(self.uid("label"), 40.76, 20.6 + i * 0.9, 40.8, 21.1 + i * 0.9, z + 6.6, z + 6.9, self.mat("paper"), self.col))
        return objs

    # ================================================================== garage (spec 7)
    def gen_car(self, e):
        """Procedural car: see car.py (lofted subdivision cage, wheel arches, glass band, lights)."""
        import importlib
        import car
        importlib.reload(car)
        return car.build_car(self, e)

    def gen_car_old(self, e):
        """Previous extruded-profile car, kept for reference."""
        p = e["pos"]
        L, W, H = e.get("length", 15.5), e.get("width", 6.2), e.get("height", 5.4)
        kind = e.get("kind", "suv")
        rot = e.get("rot_z", 0)
        covered = e.get("covered", False)          # a fitted fabric car cover: hides the procedural body honestly
        paint = self.mat("car_cover" if covered else e.get("m", "car_white"))
        glass = self.mat("car_cover" if covered else "screen_dark")
        tire = self.mat("tire")
        objs = []
        # side profile in (y, z) local, y from -L/2 (rear) to +L/2 (nose)
        gc = e.get("ground_clear", 0.7 if kind != "roadster" else 0.45)
        if kind == "roadster":
            bh = H * 0.62   # body height at the belt line
            prof = [(-L / 2, gc), (-L / 2, bh * 0.75), (-L / 2 + 0.6, bh), (-L * 0.15, bh + 0.05), (L * 0.12, bh),
                    (L * 0.38, bh * 0.92), (L / 2 - 0.4, bh * 0.75), (L / 2, bh * 0.55), (L / 2, gc)]
            cabin = [(-L * 0.22, bh), (-L * 0.16, H), (L * 0.02, H), (L * 0.12, bh)]
            cab_w = W * 0.74
        elif kind == "sedan":
            bh = H * 0.55
            prof = [(-L / 2, gc), (-L / 2, bh), (-L / 2 + 1.0, bh + 0.1), (L * 0.2, bh + 0.05), (L / 2 - 1.2, bh - 0.15), (L / 2, bh * 0.75), (L / 2, gc)]
            cabin = [(-L * 0.32, bh), (-L * 0.2, H), (L * 0.05, H), (L * 0.25, bh)]
            cab_w = W * 0.84
        else:  # suv
            bh = H * 0.5
            prof = [(-L / 2, gc), (-L / 2, bh), (L * 0.3, bh + 0.05), (L / 2 - 1.0, bh - 0.15), (L / 2, bh * 0.7), (L / 2, gc)]
            cabin = [(-L / 2 + 0.4, bh), (-L / 2 + 1.0, H), (L * 0.15, H), (L * 0.32, bh)]
            cab_w = W * 0.9
        # build in local space then rotate: use prism_yz for the body (extruded along local X)
        tag = "car_cover_" if covered else "car_"
        body = prism_yz(self.uid(tag + "body"), prof, -W / 2 + 0.15, W / 2 - 0.15, paint, self.col)
        cab = prism_yz(self.uid(tag + "cabin"), cabin, -cab_w / 2, cab_w / 2, glass, self.col)
        pillars = prism_yz(self.uid(tag + "roof"), [(cabin[1][0] + 0.2, H - 0.02), (cabin[2][0] - 0.2, H - 0.02), (cabin[2][0] - 0.2, H + 0.04), (cabin[1][0] + 0.2, H + 0.04)], -cab_w / 2 + 0.05, cab_w / 2 - 0.05, paint, self.col)
        parts = [body, cab, pillars]
        # wheels
        wr = 1.15 if kind != "roadster" else 1.0
        wb = L * 0.6
        for sy in (-wb / 2, wb / 2):
            for sx in (-W / 2 + 0.35, W / 2 - 0.35):
                t = cylinder_ft(self.uid("car_tire"), (sx - 0.35, sy, wr), wr, 0.7, tire, self.col, 28, axis="X")
                rim = cylinder_ft(self.uid("car_rim"), (sx - 0.36, sy, wr), wr * 0.62, 0.72, self.mat("chrome_dark"), self.col, 20, axis="X")
                # wheel arch cut is skipped; the body bottom sits above the wheel centres
                parts += [t, rim]
        # lights and details (none under a cover)
        for sx in ((-W * 0.32, W * 0.32) if not covered else ()):
            parts.append(box_ft(self.uid("car_headlight"), sx - 0.45, L / 2 - 0.05, sx + 0.45, L / 2 + 0.03, bh * 0.55, bh * 0.75, self.mat("glass_frosted"), self.col))
            parts.append(box_ft(self.uid("car_taillight"), sx - 0.45, -L / 2 - 0.03, sx + 0.45, -L / 2 + 0.05, bh * 0.6, bh * 0.85, self.mat("rubber_red"), self.col))
        if not covered:
            parts.append(box_ft(self.uid("car_grille"), -W * 0.3, L / 2 - 0.02, W * 0.3, L / 2 + 0.02, gc + 0.3, bh * 0.5, self.mat("steel_black"), self.col))
            parts.append(box_ft(self.uid("car_plate"), -0.5, -L / 2 - 0.03, 0.5, -L / 2 - 0.01, bh * 0.3, bh * 0.45, self.mat("paper"), self.col))
        for sx in ((-W / 2 + 0.16, W / 2 - 0.22) if not covered else ()):
            parts.append(box_ft(self.uid("car_mirror"), sx - 0.1, L * 0.14, sx + 0.16, L * 0.14 + 0.6, bh + 0.2, bh + 0.65, paint, self.col))
        # place: move everything by pos and rotate about Z
        for ob in parts:
            ob.location = (m(p[0]), m(p[1]), m(p[2]))
            ob.rotation_euler = (0, 0, math.radians(rot))
        return parts

    def gen_lift(self, e):
        """Four-post storage lift: posts, two runways at Z 5.5, cross members, a jack tray between."""
        posts = e["posts"]
        z = e.get("z", -0.4)
        blk = self.mat("steel_black")
        objs = []
        for (px, py) in posts:
            objs.append(box_ft(self.uid("lift_post"), px - 0.25, py - 0.25, px + 0.25, py + 0.25, z, z + 8.0, blk, self.col))
            objs.append(box_ft(self.uid("lift_foot"), px - 0.6, py - 0.6, px + 0.6, py + 0.6, z, z + 0.08, blk, self.col))
        rw_z = e.get("runway_z", 5.5)
        for (x0, x1) in e.get("runways", [[-3.8, -2.1], [2.1, 3.8]]):
            objs.append(box_ft(self.uid("lift_runway"), x0, e["y"][0], x1, e["y"][1], z + rw_z - 0.5, z + rw_z, blk, self.col))
            objs.append(box_ft(self.uid("lift_ramp"), x0, e["y"][0] - 2.5, x1, e["y"][0], z + rw_z - 0.5, z + rw_z - 0.45, blk, self.col)) if False else None
        # cross members at both ends
        for yy in (e["y"][0] + 1.5, e["y"][1] - 1.5):
            objs.append(box_ft(self.uid("lift_cross"), posts[0][0], yy - 0.3, posts[1][0], yy + 0.3, z + rw_z - 0.95, z + rw_z - 0.5, blk, self.col))
        # jack tray between runways
        objs.append(box_ft(self.uid("lift_tray"), -2.1, e["y"][0] + 6, 2.1, e["y"][0] + 9, z + rw_z - 0.75, z + rw_z - 0.55, self.mat("galvanized"), self.col))
        # cables inside the posts (visual lines) and a battery tender cable clipped to the roadster
        return objs

    def gen_garage_bench(self, e):
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        objs = [box_ft(self.uid("gb_top"), x0, y0, x1, y1, z1 - 0.2, z1, self.mat("oak"), self.col),
                box_ft(self.uid("gb_frame"), x0 + 0.2, y0 + 0.2, x1 - 0.2, y1 - 0.2, z0 + 0.3, z1 - 0.2, self.mat("steel_black"), self.col)]
        for (lx, ly) in ((x0 + 0.3, y0 + 0.3), (x1 - 0.3, y0 + 0.3), (x0 + 0.3, y1 - 0.3), (x1 - 0.3, y1 - 0.3)):
            objs.append(box_ft(self.uid("gb_leg"), lx - 0.12, ly - 0.12, lx + 0.12, ly + 0.12, z0, z1 - 0.2, self.mat("steel_black"), self.col))
        if e.get("shelf", True):
            objs.append(box_ft(self.uid("gb_shelf"), x0 + 0.3, y0 + 0.3, x1 - 0.3, y1 - 0.3, z0 + 0.6, z0 + 0.66, self.mat("steel_black"), self.col))
        # pegboard above with tools
        wall = e.get("wall")
        if wall:
            zp0, zp1 = e.get("peg_z", [z1 + 0.5, z1 + 4.5])
            dx, dy = _face_dir(wall)
            at = wall["at"]
            ys = sorted((at, at + dy * 0.06))
            objs.append(box_ft(self.uid("pegboard"), x0, ys[0], x1, ys[1], zp0, zp1, self.mat("pegboard"), self.col))
            rng = random.Random(8)
            for i in range(e.get("tools", 34)):
                u = rng.uniform(x0 + 0.3, x1 - 0.3); tz = rng.uniform(zp0 + 0.3, zp1 - 0.3)
                mt = self.mat(rng.choice(["steel_black", "stainless", "chrome", "rubber_red", "black", "teal"]))
                d0, d1 = sorted((at + dy * 0.1, at + dy * 0.22))
                if rng.random() < 0.6:
                    objs.append(box_ft(self.uid("tool"), u - 0.06, d0, u + 0.06, d1, tz - rng.uniform(0.4, 1.0), tz, mt, self.col))
                else:
                    objs.append(cylinder_ft(self.uid("tool"), (u, (d0 + d1) / 2, tz - rng.uniform(0.3, 0.7)), rng.uniform(0.03, 0.09), rng.uniform(0.3, 0.8), mt, self.col, 8))
        # a vise on the bench
        # a vise clamped to the front edge of the bench top
        objs.append(box_ft(self.uid("vise"), x0 + 4.0, y1 - 0.9, x0 + 4.8, y1, z1, z1 + 0.6, self.mat("steel_black"), self.col))
        objs.append(cylinder_ft(self.uid("vise_handle"), (x0 + 4.4, y1 + 0.15, z1 + 0.3), 0.03, 0.8, self.mat("chrome"), self.col, 8, axis="X"))
        return objs

    def gen_charger(self, e):
        wall = e["wall"]
        u, z = e["u"], e.get("z", 4.0)
        dx, dy = _face_dir(wall)
        at = wall["at"]
        objs = []
        if wall["axis"] == "y":
            xs = sorted((at, at + dx * 0.5))
            objs.append(box_ft(self.uid("charger"), xs[0], u - 0.6, xs[1], u + 0.6, z - 1.0, z + 0.4, self.mat("steel_black"), self.col))
            objs.append(box_ft(self.uid("charger_led"), xs[1] if dx > 0 else xs[0] - 0.01, u - 0.3, (xs[1] + 0.01) if dx > 0 else xs[0], u + 0.3, z + 0.1, z + 0.16, self.mat("led_green"), self.col))
            # coiled cable: torus-ish rings
            for k in range(5):
                ring = cylinder_ft(self.uid("cable_coil"), (at + dx * 0.55, u, z - 1.6 - k * 0.12), 0.55, 0.06, self.mat("black"), self.col, 20)
                objs.append(ring)
        return objs

    def gen_compressor_closet(self, e):
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        objs = [cylinder_ft(self.uid("compressor"), ((x0 + x1) / 2, (y0 + y1) / 2, z0 + 0.6), 0.55, 2.0, self.mat("rubber_red"), self.col, 20, axis="Y")]
        objs += self.gen_panel_grooves({"b": [x1, y0, x1 + 0.02, y1, z0, z1], "pitch": 0.25, "width": 0.09})
        objs.append(box_ft(self.uid("closet_slats"), x1 - 0.02, y0, x1, y1, z0, z1, self.mat("cedar_ext"), self.col))
        objs.append(box_ft(self.uid("closet_slats"), x0, y1 - 0.02, x1, y1, z0, z1, self.mat("cedar_ext"), self.col))
        # copper air line from the closet along the south wall above the bench (it used to be centred on the
        # closet and ran 10 ft out through the west wall)
        run = e.get("air_line_ft", 17.0)
        objs.append(cylinder_ft(self.uid("air_line"), (x1 + run / 2, y0 + 0.5, z1 - 0.3), 0.03, run, self.mat("copper"), self.col, 8, axis="X"))
        return objs

    def gen_reel(self, e):
        p = e["pos"]
        mt = self.mat(e.get("m", "rubber_red"))
        objs = [box_centered(self.uid("reel_bracket"), (p[0], p[1], p[2] - 0.2), (0.4, 0.4, 0.4), 0, self.mat("steel_black"), self.col),
                cylinder_ft(self.uid("reel_drum"), (p[0] - 0.45, p[1], p[2] - 1.1), 0.7, 0.9, mt, self.col, 24, axis="X")]
        objs.append(cylinder_ft(self.uid("reel_hose"), (p[0], p[1], p[2] - 1.8), 0.05, 1.6, self.mat("black" if e.get("m") == "steel_black" else "rubber_red"), self.col, 8))
        return objs

    def gen_bike(self, e):
        p = e["pos"]
        rot = math.radians(e.get("rot_z", 0))
        r = e.get("wheel_r", 1.1)
        frame = self.mat(e.get("m", "teal"))
        objs = []
        d = (math.cos(rot), math.sin(rot))
        for s in (-1.7, 1.7):
            c = (p[0] + d[0] * s, p[1] + d[1] * s, p[2] + r)
            w = cylinder_ft(self.uid("bike_wheel"), (c[0] - d[1] * 0.04, c[1] + d[0] * 0.04, c[2]), r, 0.08, self.mat("tire"), self.col, 32, axis="Y")
            w.rotation_euler = (0, 0, rot)
            objs.append(w)
        # frame triangle
        pts = [(p[0] - d[0] * 1.7, p[1] - d[1] * 1.7, p[2] + r), (p[0] - d[0] * 0.2, p[1] - d[1] * 0.2, p[2] + r + 0.2), (p[0] + d[0] * 1.0, p[1] + d[1] * 1.0, p[2] + r + 1.7),
               (p[0] - d[0] * 0.5, p[1] - d[1] * 0.5, p[2] + r + 1.9), (p[0] + d[0] * 1.7, p[1] + d[1] * 1.7, p[2] + r)]
        for a, b in ((0, 1), (1, 2), (2, 3), (3, 1), (0, 3), (2, 4), (1, 4)):
            objs.append(beam_between(self.uid("bike_tube"), pts[a], pts[b], 0.08, 0.08, frame, self.col))
        objs.append(box_centered(self.uid("bike_saddle"), (pts[3][0], pts[3][1], pts[3][2] + 0.15), (0.35, 0.9, 0.12), e.get("rot_z", 0), self.mat("leather_brown"), self.col))
        objs.append(cylinder_ft(self.uid("bike_bars"), (pts[2][0] - d[1] * 0.9, pts[2][1] + d[0] * 0.9, pts[2][2] + 0.3), 0.04, 1.8, self.mat("steel_black"), self.col, 8, axis="X" if abs(d[0]) > 0.5 else "Y"))
        return objs

    def gen_shovel(self, e):
        p = e["pos"]
        objs = [cylinder_ft(self.uid("shovel_handle"), (p[0], p[1], p[2] + 0.4), 0.05, 4.2, self.mat("walnut"), self.col, 8),
                box_ft(self.uid("shovel_blade"), p[0] - 0.5, p[1] - 0.05, p[0] + 0.5, p[1] + 0.05, p[2], p[2] + 1.1, self.mat("rubber_red"), self.col)]
        objs[0].rotation_euler = (math.radians(8), 0, 0)
        return objs

    def gen_ice_melt(self, e):
        p = e["pos"]
        bag = box_centered(self.uid("bag"), (p[0], p[1], p[2] + 0.7), (1.3, 0.8, 1.4), 15, self.mat("mustard_paint"), self.col)
        return [bag]

    def gen_garage_shelving(self, e):
        return self.gen_shelving_unit(e)

    # ================================================================== exterior fixtures (spec 1.2, 2.6, 7)
    def gen_house_numbers(self, e):
        """Brass numerals from 7-segment bars; text like '1956'. wall/face, u centre, z centre, height."""
        wall = e["wall"]
        u, z = e["u"], e.get("z", 5.5)
        h = e.get("height", 0.5)
        w = h * 0.55
        t = h * 0.12
        dx, dy = _face_dir(wall)
        at = wall["at"]
        brass = self.mat("brass")
        segs = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg"}
        text = e.get("text", "1956")
        total = len(text) * w + (len(text) - 1) * w * 0.5
        objs = []
        for i, ch in enumerate(text):
            cu = u - total / 2 + i * w * 1.5 + w / 2
            for s in segs.get(ch, ""):
                # segment boxes in (u, z) local
                if s == "a":
                    box = (cu - w / 2, cu + w / 2, z + h / 2 - t, z + h / 2)
                elif s == "g":
                    box = (cu - w / 2, cu + w / 2, z - t / 2, z + t / 2)
                elif s == "d":
                    box = (cu - w / 2, cu + w / 2, z - h / 2, z - h / 2 + t)
                elif s == "b":
                    box = (cu + w / 2 - t, cu + w / 2, z, z + h / 2)
                elif s == "c":
                    box = (cu + w / 2 - t, cu + w / 2, z - h / 2, z)
                elif s == "e":
                    box = (cu - w / 2, cu - w / 2 + t, z - h / 2, z)
                else:
                    box = (cu - w / 2, cu - w / 2 + t, z, z + h / 2)
                if wall["axis"] == "x":
                    ys = sorted((at, at + dy * 0.05))
                    objs.append(box_ft(self.uid("numeral"), box[0], ys[0], box[1], ys[1], box[2], box[3], brass, self.col))
                else:
                    xs = sorted((at, at + dx * 0.05))
                    objs.append(box_ft(self.uid("numeral"), xs[0], box[0], xs[1], box[1], box[2], box[3], brass, self.col))
        return objs

    def gen_mail_slot(self, e):
        wall = e["wall"]
        u, z = e["u"], e.get("z", 3.5)
        dx, dy = _face_dir(wall)
        at = wall["at"]
        if wall["axis"] == "x":
            ys = sorted((at, at + dy * 0.04))
            return [box_ft(self.uid("mail_slot"), u - 0.6, ys[0], u + 0.6, ys[1], z - 0.2, z + 0.2, self.mat("brass"), self.col),
                    box_ft(self.uid("mail_slot_in"), u - 0.5, ys[0] - 0.005, u + 0.5, ys[1] + 0.005, z - 0.08, z + 0.08, self.mat("black"), self.col)]
        return []

    def gen_ext_sconce(self, e):
        """Bronze cylinder wall sconce for outside: down-light, on at dusk (flag on)."""
        return self.gen_sconce(dict(e, radius=e.get("radius", 0.2), height=e.get("height", 0.9), watts=e.get("watts", 18), on=e.get("on", True)))

    def gen_soffit_downlight(self, e):
        return self.gen_downlight(e)

    def gen_rain_chain(self, e):
        p = e["pos"]           # top at the eave
        drop = e.get("drop", 18.5)
        objs = []
        for k in range(int(drop / 0.5)):
            zz = p[2] - k * 0.5
            cup = cylinder_ft(self.uid("rain_cup"), (p[0], p[1], zz - 0.4), 0.14, 0.4, self.mat("bronze_black"), self.col, 12)
            objs.append(cup)
        basin = cylinder_ft(self.uid("splash_basin"), (p[0], p[1], p[2] - drop - 0.3), 1.0, 0.35, self.mat("bluestone"), self.col, 24)
        objs.append(basin)
        return objs

    def gen_grill(self, e):
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        ss = self.mat("stainless")
        objs = [box_ft(self.uid("grill_body"), x0, y0, x1, y1, z0, z1, ss, self.col)]
        lid = prism_yz(self.uid("grill_lid"), [(y0, z1), (y1, z1), (y1 - 0.2, z1 + 0.5), (y0 + 0.4, z1 + 0.7), (y0, z1 + 0.5)], x0 + 0.05, x1 - 0.05, ss, self.col)
        objs.append(lid)
        objs.append(cylinder_ft(self.uid("grill_handle"), (x0 + 0.3, y0 - 0.1, z1 + 0.55), 0.04, x1 - x0 - 0.6, self.mat("steel_black"), self.col, 8, axis="X"))
        for i in range(4):
            objs.append(cylinder_ft(self.uid("grill_knob"), (x0 + 0.4 + i * (x1 - x0 - 0.8) / 3, y0 - 0.05, z1 - 0.35), 0.1, 0.1, self.mat("steel_black"), self.col, 12, axis="Y"))
        return objs

    def gen_heater(self, e):
        """Outdoor infrared heater under the canopy: black bar with a glowing element."""
        p = e["pos"]
        L = e.get("length", 3.0)
        objs = [box_centered(self.uid("heater_body"), (p[0], p[1], p[2]), (L, 0.5, 0.3), e.get("rot_z", 0), self.mat("steel_black"), self.col)]
        if e.get("on", True):
            objs.append(box_centered(self.uid("heater_el"), (p[0], p[1], p[2] - 0.12), (L - 0.4, 0.3, 0.06), e.get("rot_z", 0), self.mat("heater_glow"), self.col))
            self.light(type="area", pos=(p[0], p[1], p[2] - 0.2), size=L - 0.4, size_y=0.3, shape="RECTANGLE", watts=e.get("watts", 40), kelvin=1600, rot=(0, 0, 0), name="heater")
        return objs

    def gen_outdoor_sofa(self, e):
        p = e["pos"]
        objs = self.gen_sofa(dict(e, m=e.get("m", "canvas_tan")))
        return objs

    def gen_spa_cover(self, e):
        b = e["b"]
        x0, y0, x1, y1, z = b
        # folded open cover standing at the north end
        return [box_ft(self.uid("spa_cover"), x0, y1 - 0.5, x1, y1 + 0.1, z, z + 3.6, self.mat("canvas_tan"), self.col)]

    def gen_planter(self, e):
        p = e["pos"]
        objs = [box_centered(self.uid("planter"), (p[0], p[1], p[2] + 0.9), (e.get("w", 2.0), e.get("d", 2.0), 1.8), 0, self.mat("steel_black"), self.col)]
        objs += self.gen_plant({"pos": [p[0], p[1], p[2] + 1.6], "height": e.get("height", 3.5), "seed": e.get("seed", 3)})
        return objs

    def gen_porch_bench(self, e):
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        objs = [box_ft(self.uid("pb_slab"), x0, y0, x1, y1, z1 - 0.15, z1, wood, self.col),
                box_ft(self.uid("pb_leg"), x0 + 0.2, y0 + 0.1, x0 + 0.35, y1 - 0.1, z0, z1 - 0.15, wood, self.col),
                box_ft(self.uid("pb_leg"), x1 - 0.35, y0 + 0.1, x1 - 0.2, y1 - 0.1, z0, z1 - 0.15, wood, self.col),
                box_ft(self.uid("bench_cush"), x0 + 0.4, y0 + 0.1, x0 + 2.4, y1 - 0.1, z1, z1 + 0.25, self.mat("wool_mustard"), self.col),
                box_ft(self.uid("bench_cush"), x1 - 3.0, y0 + 0.1, x1 - 1.0, y1 - 0.1, z1, z1 + 0.25, self.mat("olive_paint"), self.col)]
        return objs

    def gen_stroller(self, e):
        p = e["pos"]
        objs = [box_centered(self.uid("stroller_seat"), (p[0], p[1], p[2] + 2.0), (1.8, 2.6, 1.2), e.get("rot_z", 0), self.mat("wool_carpet_charcoal"), self.col),
                box_centered(self.uid("stroller_hood"), (p[0], p[1] + 0.9, p[2] + 2.9), (1.8, 1.0, 0.6), e.get("rot_z", 0), self.mat("wool_carpet_charcoal"), self.col)]
        for sx in (-0.8, 0.8):
            for sy in (-1.0, 1.0):
                objs.append(cylinder_ft(self.uid("stroller_wheel"), (p[0] + sx, p[1] + sy, p[2] + 0.5), 0.5, 0.15, self.mat("tire"), self.col, 20, axis="X"))
        objs.append(cylinder_ft(self.uid("stroller_bar"), (p[0] - 0.9, p[1] - 1.4, p[2] + 3.4), 0.04, 1.8, self.mat("steel_black"), self.col, 8, axis="X"))
        return objs

    # ================================================================== sauna (spec 5.3)
    def gen_sauna2(self, e):
        """Cedar sauna interior inside the room shell X 0-8, Y 20-28: T&G lining, two-tier benches along the west
        and north walls, heater with stones and a guard rail, bucket and ladle, headrest, thermometer, warm strips.
        The glass front at X 8 is the plan's glasswall opening; this adds its walnut frame and door stile."""
        x0, y0, x1, y1, z0, z1 = e["b"]
        cedar = self.mat("cedar_sauna")
        wal = self.mat("walnut_h")
        objs = []
        t = 0.08
        # lining on walls and ceiling (thin panels inside the plaster shell)
        objs.append(box_ft(self.uid("sa_line"), x0 + 0.02, y0 + 0.25, x0 + 0.02 + t, y1 - 0.25, z0 + 0.05, z1 - 0.1, cedar, self.col))
        objs.append(box_ft(self.uid("sa_line"), x0, y1 - 0.25 - t, x1 - 0.5, y1 - 0.25, z0 + 0.05, z1 - 0.1, cedar, self.col))
        objs.append(box_ft(self.uid("sa_line"), x0, y0 + 0.25, x1 - 0.5, y0 + 0.25 + t, z0 + 0.05, z1 - 0.1, cedar, self.col))
        objs.append(box_ft(self.uid("sa_ceiling"), x0, y0 + 0.25, x1 - 0.3, y1 - 0.25, z1 - 0.1 - t, z1 - 0.1, cedar, self.col))
        objs += self.gen_panel_grooves({"b": [x0 + 0.02 + t, y0 + 0.4, x0 + 0.03 + t, y1 - 0.4, z0 + 0.1, z1 - 0.2], "pitch": 0.29, "width": 0.02})
        objs += self.gen_panel_grooves({"b": [x0 + 0.3, y1 - 0.26 - t, x1 - 0.6, y1 - 0.25 - t, z0 + 0.1, z1 - 0.2], "pitch": 0.29, "width": 0.02})
        objs.append(box_ft(self.uid("sa_floor"), x0 + 0.1, y0 + 0.3, x1 - 0.3, y1 - 0.3, z0, z0 + 0.12, cedar, self.col))
        # benches: lower top at z0+1.6, upper at z0+3.0, each 2 ft deep, along the west and north walls
        objs.append(box_ft(self.uid("sa_bench"), x0 + 0.1, y0 + 2.6, x0 + 2.1, y1 - 0.3, z0 + 2.85, z0 + 3.0, cedar, self.col))
        objs.append(box_ft(self.uid("sa_bench"), x0 + 0.1, y1 - 2.3, x1 - 0.6, y1 - 0.3, z0 + 2.85, z0 + 3.0, cedar, self.col))
        objs.append(box_ft(self.uid("sa_bench"), x0 + 2.1, y0 + 2.6, x0 + 4.1, y1 - 2.3, z0 + 1.45, z0 + 1.6, cedar, self.col))
        objs.append(box_ft(self.uid("sa_bench"), x0 + 2.1, y1 - 4.3, x1 - 0.6, y1 - 2.3, z0 + 1.45, z0 + 1.6, cedar, self.col))
        for (bx0, by0, bx1, by1, zz) in ((x0 + 0.1, y0 + 2.6, x0 + 2.1, y1 - 0.3, 3.0), (x0 + 0.1, y1 - 2.3, x1 - 0.6, y1 - 0.3, 3.0),
                                         (x0 + 2.1, y0 + 2.6, x0 + 4.1, y1 - 2.3, 1.6), (x0 + 2.1, y1 - 4.3, x1 - 0.6, y1 - 2.3, 1.6)):
            # slat gaps on the bench tops
            u = bx0 + 0.3
            while u < bx1 - 0.1:
                objs.append(box_ft(self.uid("sa_slat_gap"), u, by0, u + 0.03, by1, z0 + zz - 0.01, z0 + zz + 0.005, self.mat("black"), self.col))
                u += 0.33
            objs.append(box_ft(self.uid("sa_bench_face"), bx0, by0, bx1, by0 + 0.06, z0 + zz - 0.6, z0 + zz - 0.15, cedar, self.col))
        # heater at (1, 21): black box with a basket of stones and a cedar guard rail
        objs.append(box_ft(self.uid("sa_heater"), x0 + 0.4, y0 + 0.45, x0 + 1.6, y0 + 1.65, z0 + 0.12, z0 + 2.4, self.mat("steel_black"), self.col))
        rng = random.Random(3)
        for i in range(14):
            objs.append(sphere_ft(self.uid("stone"), (x0 + 0.65 + rng.uniform(0, 0.7), y0 + 0.7 + rng.uniform(0, 0.7), z0 + 2.45 + rng.uniform(0, 0.25)), rng.uniform(0.12, 0.2), self.mat("stone"), self.col, 10, 6))
        objs.append(box_ft(self.uid("sa_rail"), x0 + 0.25, y0 + 1.85, x0 + 1.85, y0 + 1.95, z0 + 2.7, z0 + 2.85, cedar, self.col))
        objs.append(box_ft(self.uid("sa_rail"), x0 + 1.85, y0 + 0.3, x0 + 1.95, y0 + 1.95, z0 + 2.7, z0 + 2.85, cedar, self.col))
        for (px, py) in ((x0 + 0.3, y0 + 1.9), (x0 + 1.9, y0 + 1.9), (x0 + 1.9, y0 + 0.35)):
            objs.append(box_ft(self.uid("sa_rail_post"), px - 0.05, py - 0.05, px + 0.05, py + 0.05, z0 + 0.12, z0 + 2.85, cedar, self.col))
        # bucket, ladle, headrest, thermometer
        objs.append(cylinder_ft(self.uid("sa_bucket"), (x0 + 3.0, y1 - 1.2, z0 + 3.0), 0.5, 0.65, cedar, self.col, 18))
        objs.append(cylinder_ft(self.uid("sa_bucket_band"), (x0 + 3.0, y1 - 1.2, z0 + 3.4), 0.52, 0.06, self.mat("steel_black"), self.col, 18))
        objs.append(cylinder_ft(self.uid("sa_ladle"), (x0 + 3.0, y1 - 1.2, z0 + 3.3), 0.03, 1.6, cedar, self.col, 6, axis="X"))
        hr = box_ft(self.uid("sa_headrest"), x0 + 4.5, y1 - 1.5, x1 - 1.2, y1 - 0.5, z0 + 3.0, z0 + 3.3, cedar, self.col)
        objs.append(hr)
        objs.append(cylinder_ft(self.uid("sa_thermo"), (x0 + 0.11 + t, y1 - 2.0, z0 + 6.0), 0.3, 0.06, self.mat("brass"), self.col, 20, axis="X"))
        # glass front frame at X 8 (opening Y 21-27): walnut jambs, door stile at Y 23-25.5 with a long cedar pull
        objs.append(box_ft(self.uid("sa_frame"), x1 - 0.15, y0 + 1.0 - 0.15, x1 + 0.15, y0 + 1.0, z0, z0 + 8.0, wal, self.col))
        objs.append(box_ft(self.uid("sa_frame"), x1 - 0.15, y1 - 1.0, x1 + 0.15, y1 - 1.0 + 0.15, z0, z0 + 8.0, wal, self.col))
        objs.append(box_ft(self.uid("sa_frame"), x1 - 0.15, y0 + 1.0 - 0.15, x1 + 0.15, y1 - 1.0 + 0.15, z0 + 8.0, z0 + 8.15, wal, self.col))
        for yy in (23.0, 25.5):
            objs.append(box_ft(self.uid("sa_stile"), x1 - 0.06, yy - 0.06, x1 + 0.06, yy + 0.06, z0, z0 + 8.0, wal, self.col))
        objs.append(cylinder_ft(self.uid("sa_pull"), (x1 + 0.2, 25.2, z0 + 2.5), 0.05, 2.0, cedar, self.col, 10))
        objs.append(cylinder_ft(self.uid("sa_pull"), (x1 - 0.2, 25.2, z0 + 2.5), 0.05, 2.0, cedar, self.col, 10))
        # warm strips under the benches and one sconce
        objs += self.gen_led_strip({"b": [x0 + 2.15, y0 + 2.7, x0 + 4.0, y0 + 2.75, z0 + 1.38, z0 + 1.42], "watts": 14, "kelvin": 2200})
        objs += self.gen_led_strip({"b": [x0 + 0.2, y1 - 2.4, x1 - 0.7, y1 - 2.35, z0 + 2.78, z0 + 2.82], "watts": 18, "kelvin": 2200})
        objs += self.gen_sconce({"wall": {"axis": "y", "at": x0 + 0.1 + t, "face": "+x"}, "u": y0 + 4.2, "z": z0 + 6.0, "watts": 26, "kelvin": 2200, "radius": 0.15, "height": 0.6})
        return objs
