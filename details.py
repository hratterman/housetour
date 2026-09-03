"""
details.py: Phase 2 architectural detail generator. Everything here is derived from plan.json
(openings, rooms, beams, stair, exterior, picture_lights). Called by build_scene.py in phase2.
"""
import math

import bpy
from mathutils import Vector

from geom import (FT, IN, m, log, box_ft, box_local, beam_between, cylinder_ft, sphere_ft, prism_yz, prism_xz,
                  plane_ft, get_collection, boolean_cut, cut_with_box, overlap, bounds_of, set_face_material,
                  area_light)

CASING_W = 4 * IN          # face casing width
LINER_T = 0.75 * IN        # jamb liner thickness inside the reveal
PROUD = 0.75 * IN          # casing stands proud of the wall face
DOOR_T = 1.75 * IN
BASE_H = 3 * IN
BASE_T = 0.6 * IN
FRAME_W = 2.5 * IN         # window frame member width
FRAME_D = 2.5 * IN         # window frame depth
MULLION_W = 1.5 * IN
GLASS_T = 0.25 * IN

HALL_ROOMS = {"spine", "awayhall", "foyer", "mudroom", "stair", "storage"}


class Details:
    def __init__(self, plan, house, mats):
        self.plan = plan
        self.house = house
        self.mats = mats
        self.col = get_collection("details")
        self.col_glass = get_collection("glass")
        self.col_lights = get_collection("lights")
        self.floors = plan["floors"]
        self.wt = plan.get("wall_thickness", 0.5)
        self.counts = {}

    def n(self, key, k=1):
        self.counts[key] = self.counts.get(key, 0) + k

    # ------------------------------------------------------------------ opening geometry
    def wall_range(self, op):
        """Normal-direction extent [n0, n1] of the wall slab(s) this opening cuts, in feet."""
        names = op.get("_cut_walls", [])
        n0, n1 = None, None
        for nm in names:
            ob = bpy.data.objects.get(nm)
            if ob is None:
                continue
            b = bounds_of(ob)
            lo, hi = (b[1], b[3]) if op["axis"] == "x" else (b[0], b[2])
            n0 = lo if n0 is None else min(n0, lo)
            n1 = hi if n1 is None else max(n1, hi)
        if n0 is None:
            n0, n1 = op["at"] - self.wt / 2, op["at"] + self.wt / 2
        return n0, n1

    def is_exterior(self, op):
        names = op.get("_cut_walls", [])
        if not names:
            return bool(op.get("exterior"))
        return all(bpy.data.objects[n].get("exterior") for n in names if n in bpy.data.objects)

    def rooms_either_side(self, op):
        """(room on the negative side, room on the positive side) of the opening, or None."""
        neg = pos = None
        for r in self.house.rooms:
            if r["floor"] != op["floor"]:
                continue
            for part in r.get("parts", [r.get("b")]):
                x0, y0, x1, y1 = part
                if op["axis"] == "x":
                    if not (x0 - 1e-6 <= op["c"] <= x1 + 1e-6):
                        continue
                    if abs(y1 - op["at"]) < 1e-6:
                        neg = r
                    if abs(y0 - op["at"]) < 1e-6:
                        pos = r
                else:
                    if not (y0 - 1e-6 <= op["c"] <= y1 + 1e-6):
                        continue
                    if abs(x1 - op["at"]) < 1e-6:
                        neg = r
                    if abs(x0 - op["at"]) < 1e-6:
                        pos = r
        return neg, pos

    # ------------------------------------------------------------------ casings + doors
    def build_casings_and_doors(self):
        walnut = self.mats.get("walnut_h")
        brass = self.mats.get("brass")
        for op in self.plan["openings"]:
            kind = op.get("kind", "door")
            if kind not in ("door", "cased", "glassdoor", "pocket"):
                continue
            if not op.get("_cut_walls"):
                continue
            fl = self.floors[op["floor"]]
            z = fl["z"]
            n0, n1 = self.wall_range(op)
            c, w, h = op["c"], op["w"], op["h"]
            a0, a1 = c - w / 2, c + w / 2
            tag = op["note"].replace(" ", "_")
            f0, f1 = n0 - PROUD, n1 + PROUD
            # legs (through the wall, covering the reveal liner and both face casings)
            for side, (u0, u1) in (("a", (a0 - CASING_W, a0 + LINER_T)), ("b", (a1 - LINER_T, a1 + CASING_W))):
                if op["axis"] == "x":
                    box_ft("casing_%s_%s" % (tag, side), u0, f0, u1, f1, z, z + h + CASING_W, walnut, self.col)
                else:
                    box_ft("casing_%s_%s" % (tag, side), f0, u0, f1, u1, z, z + h + CASING_W, walnut, self.col)
            # head
            if op["axis"] == "x":
                box_ft("casing_%s_head" % tag, a0 - CASING_W, f0, a1 + CASING_W, f1, z + h - LINER_T,
                       z + h + CASING_W, walnut, self.col)
            else:
                box_ft("casing_%s_head" % tag, f0, a0 - CASING_W, f1, a1 + CASING_W, z + h - LINER_T,
                       z + h + CASING_W, walnut, self.col)
            self.n("casings")
            if kind in ("door", "glassdoor") and op.get("open_deg", 80) > 0:
                self.build_door(op, z, n0, n1, a0 + LINER_T, a1 - LINER_T, h - LINER_T,
                                self.mats.get("glass") if kind == "glassdoor" else walnut, brass, tag)
            elif kind in ("door", "glassdoor"):
                # closed leaf in the plane of the wall
                leaf_m = self.mats.get("glass") if kind == "glassdoor" else walnut
                mid = (n0 + n1) / 2
                if op["axis"] == "x":
                    box_ft("door_%s" % tag, a0 + LINER_T, mid - DOOR_T / 2, a1 - LINER_T, mid + DOOR_T / 2, z + 0.01, z + h - LINER_T, leaf_m, self.col)
                else:
                    box_ft("door_%s" % tag, mid - DOOR_T / 2, a0 + LINER_T, mid + DOOR_T / 2, a1 - LINER_T, z + 0.01, z + h - LINER_T, leaf_m, self.col)
                self.n("doors")
            elif kind == "pocket":
                # leaf recessed into the wall except for open_ft showing
                mid = (n0 + n1) / 2
                show = op.get("open_ft", 0)
                leaf_w = (a1 - a0) / 2
                if op["axis"] == "x":
                    box_ft("pocket_%s" % tag, a0 + LINER_T, mid - DOOR_T / 2, a0 + LINER_T + max(0.05, leaf_w - show), mid + DOOR_T / 2, z + 0.01, z + h - LINER_T, walnut, self.col)
                else:
                    box_ft("pocket_%s" % tag, mid - DOOR_T / 2, a0 + LINER_T, mid + DOOR_T / 2, a0 + LINER_T + max(0.05, leaf_w - show), z + 0.01, z + h - LINER_T, walnut, self.col)
                self.n("pocket doors")

    def build_door(self, op, z, n0, n1, a0, a1, h, walnut, brass, tag):
        exterior = self.is_exterior(op)
        width = (a1 - a0) - 0.02
        height = h - 0.02
        neg, pos = self.rooms_either_side(op)
        # swing into the room that is not a hall; exterior doors swing inward
        if exterior:
            swing_pos = pos is not None
        elif pos is not None and pos["name"] in HALL_ROOMS and neg is not None and neg["name"] not in HALL_ROOMS:
            swing_pos = False
        else:
            swing_pos = True
        angle = 90.0 if exterior else op.get("open_deg", 80.0)
        thick = 2.25 * IN if exterior else DOOR_T
        mid = (n0 + n1) / 2 - thick / 2
        if op["axis"] == "x":
            base_rot = 0.0
            hinge = (a0, mid, z + 0.01)
            rot = base_rot + (angle if swing_pos else -angle)
        else:
            base_rot = 90.0
            hinge = (mid + thick, a0, z + 0.01)
            rot = base_rot + (-angle if swing_pos else angle)
        door = box_local("door_%s" % tag, hinge, (width, thick, height), rot, walnut, self.col)
        door["door"] = True
        # hardware: lever (interior) or long pull (exterior), on both faces near the free edge
        if exterior:
            for face in (-0.1, thick + 0.02):
                bar = box_local("pull_%s_%d" % (tag, face > 0), (0, 0, 0), (0.08, 0.08, 3.5), 0, brass, self.col)
                bar.parent = door
                bar.location = (m(width - 0.9), m(face), m(2.4))
        else:
            for face in (-0.05, thick):
                lever = box_local("lever_%s_%d" % (tag, face > 0), (0, 0, 0), (0.4, 0.06, 0.06), 0, brass, self.col)
                lever.parent = door
                lever.location = (m(width - 0.65), m(face), m(3.1))
        self.n("doors")

    # ------------------------------------------------------------------ windows + glass walls
    def build_windows(self):
        bronze = self.mats.get("bronze")
        glass = self.mats.get("glass")
        walnut = self.mats.get("walnut_h")
        for op in self.plan["openings"]:
            kind = op.get("kind", "door")
            if kind not in ("window", "glasswall"):
                continue
            if not op.get("_cut_walls"):
                continue
            fl = self.floors[op["floor"]]
            z0 = fl["z"] + op.get("z0", 0)
            z1 = z0 + op["h"]
            n0, n1 = self.wall_range(op)
            mid = (n0 + n1) / 2
            c, w = op["c"], op["w"]
            a0, a1 = c - w / 2, c + w / 2
            tag = op["note"].replace(" ", "_")
            d0, d1 = mid - FRAME_D / 2, mid + FRAME_D / 2

            def fbox(name, u0, u1, zz0, zz1, dd0=d0, dd1=d1, mat=bronze, col=self.col):
                if op["axis"] == "x":
                    return box_ft(name, u0, dd0, u1, dd1, zz0, zz1, mat, col)
                return box_ft(name, dd0, u0, dd1, u1, zz0, zz1, mat, col)

            # perimeter frame
            fbox("wf_%s_l" % tag, a0, a0 + FRAME_W, z0, z1)
            fbox("wf_%s_r" % tag, a1 - FRAME_W, a1, z0, z1)
            fbox("wf_%s_t" % tag, a0, a1, z1 - FRAME_W, z1)
            fbox("wf_%s_b" % tag, a0, a1, z0, z0 + FRAME_W)
            # mullions: panels about 4 ft (glass wall) or up to 3.5 ft (window)
            panel = 4.0 if kind == "glasswall" else 3.5
            npan = max(1, int(math.ceil(w / panel)))
            pw = w / npan
            for i in range(1, npan):
                u = a0 + i * pw
                fbox("wm_%s_%d" % (tag, i), u - MULLION_W / 2, u + MULLION_W / 2, z0, z1)
            # transom bar on tall glass walls at door height
            if kind == "glasswall" and op["h"] > 8.0:
                fbox("wt_%s" % tag, a0, a1, z0 + 7.5, z0 + 7.5 + MULLION_W)
            # glass panes, one per panel; a lift-and-slide "door_panel" is slid open over its neighbour
            door_panel = op.get("door_panel")
            for i in range(npan):
                u0 = a0 + i * pw + (FRAME_W if i == 0 else MULLION_W / 2)
                u1 = a0 + (i + 1) * pw - (FRAME_W if i == npan - 1 else MULLION_W / 2)
                if door_panel is not None and i == door_panel:
                    # draw this panel slid over the adjacent one, offset in depth, leaving its bay open
                    j = i - 1 if i > 0 else i + 1
                    v0 = a0 + j * pw + (FRAME_W if j == 0 else MULLION_W / 2)
                    v1 = a0 + (j + 1) * pw - (FRAME_W if j == npan - 1 else MULLION_W / 2)
                    off = FRAME_D * 0.9
                    fbox("glass_%s_%d" % (tag, i), v0, v1, z0 + FRAME_W, z1 - FRAME_W,
                         mid + off - GLASS_T / 2, mid + off + GLASS_T / 2, glass, self.col_glass)
                    fbox("wm_%s_slid_a" % tag, v0 - MULLION_W, v0, z0, z1, mid + off - FRAME_D / 2, mid + off + FRAME_D / 2)
                    fbox("wm_%s_slid_b" % tag, v1, v1 + MULLION_W, z0, z1, mid + off - FRAME_D / 2, mid + off + FRAME_D / 2)
                    continue
                fbox("glass_%s_%d" % (tag, i), u0, u1, z0 + FRAME_W, z1 - FRAME_W,
                     mid - GLASS_T / 2, mid + GLASS_T / 2, glass, self.col_glass)
            # interior sill for windows above the floor
            if op.get("z0", 0) > 0:
                neg, pos = self.rooms_either_side(op)
                inward = 1 if (pos is not None and neg is None) else -1
                if op["axis"] == "x":
                    s0, s1 = (n1, n1 + 0.2) if inward > 0 else (n0 - 0.2, n0)
                    box_ft("sill_%s" % tag, a0 - 0.15, s0, a1 + 0.15, s1, z0 - 0.12, z0, walnut, self.col)
                else:
                    s0, s1 = (n1, n1 + 0.2) if inward > 0 else (n0 - 0.2, n0)
                    box_ft("sill_%s" % tag, s0, a0 - 0.15, s1, a1 + 0.15, z0 - 0.12, z0, walnut, self.col)
            # light portal on exterior glass
            if self.is_exterior(op):
                neg, pos = self.rooms_either_side(op)
                inward = 1 if (pos is not None and neg is None) else -1
                cz = (z0 + z1) / 2
                if op["axis"] == "x":
                    pos_ft = (c, op["at"] + inward * 0.3, cz)
                    rot = (math.radians(90 * inward), 0, 0)
                else:
                    pos_ft = (op["at"] + inward * 0.3, c, cz)
                    rot = (0, math.radians(-90 * inward), 0)
                area_light("portal_%s" % tag, pos_ft, w, 0, collection=self.col_lights, rot=rot,
                           shape="RECTANGLE", size_y_ft=op["h"], portal=True)
            self.n("windows")

    # ------------------------------------------------------------------ baseboards
    def build_baseboards(self):
        skip = set(self.plan.get("no_baseboard", []))
        walnut = self.mats.get("walnut_h")
        boards = []
        for w in self.house.walls:
            room = w["room"]
            if room in skip:
                continue
            b = bounds_of(w)
            fl = self.floors[w["floor"]]
            z = fl["z"]
            side = w["side"]
            if side == "south":
                bb = box_ft("base_%s" % w.name, b[0] + BASE_T, b[3], b[2] - BASE_T, b[3] + BASE_T, z, z + BASE_H, walnut, self.col)
            elif side == "north":
                bb = box_ft("base_%s" % w.name, b[0] + BASE_T, b[1] - BASE_T, b[2] - BASE_T, b[1], z, z + BASE_H, walnut, self.col)
            elif side == "west":
                bb = box_ft("base_%s" % w.name, b[2], b[1] - BASE_T, b[2] + BASE_T, b[3] + BASE_T, z, z + BASE_H, walnut, self.col)
            else:
                bb = box_ft("base_%s" % w.name, b[0] - BASE_T, b[1] - BASE_T, b[0], b[3] + BASE_T, z, z + BASE_H, walnut, self.col)
            bb["floor"] = w["floor"]
            bb["axis"] = w["axis"]
            boards.append(bb)
        # cut door openings (and their casings) out of the boards
        cuts = 0
        for op in self.plan["openings"]:
            if op.get("z0", 0) != 0:
                continue
            fl = self.floors[op["floor"]]
            z = fl["z"]
            pad = self.wt * 1.5
            ext = CASING_W + 0.02
            if op["axis"] == "x":
                bnd = [op["c"] - op["w"] / 2 - ext, op["at"] - pad, op["c"] + op["w"] / 2 + ext, op["at"] + pad, z - 0.1, z + 1]
            else:
                bnd = [op["at"] - pad, op["c"] - op["w"] / 2 - ext, op["at"] + pad, op["c"] + op["w"] / 2 + ext, z - 0.1, z + 1]
            targets = [b for b in boards if b["floor"] == op["floor"] and b["axis"] == op["axis"] and overlap(bounds_of(b), bnd)]
            if targets:
                cut_with_box(targets, bnd, "cut_base")
                cuts += len(targets)
        self.n("baseboards", len(boards))
        self.n("baseboard cuts", cuts)

    # ------------------------------------------------------------------ beams
    def build_beams(self):
        for spec in self.plan.get("beams", []):
            room = self.house.room_by_name[spec["room"]]
            fl = self.floors[room["floor"]]
            x0, y0, x1, y1 = room["b"]
            zc = fl["z"] + fl["h"]
            w_ft = spec.get("w_in", 6) / 12.0
            d_ft = spec.get("d_in", 12) / 12.0
            mat = self.mats.get(spec.get("m", "walnut"))
            # deck material on the ceiling slab
            for ob in bpy.data.objects:
                if ob.name.startswith("ceil_") and ob.get("room") == room["name"] and spec.get("deck_m"):
                    ob.data.materials.clear()
                    ob.data.materials.append(self.mats.get(spec["deck_m"]))
            sp = spec.get("spacing", 4.0)
            k = 0
            if spec.get("positions") and spec.get("axis", "x") == "x":
                for y in spec["positions"]:
                    box_ft("beam_%s_%d" % (room["name"], k), x0 + 0.2, y - w_ft / 2, x1 - 0.2, y + w_ft / 2, zc - d_ft, zc, mat, self.col)
                    k += 1
            elif spec.get("axis", "x") == "x":
                y = y0 + sp / 2
                while y < y1 - 0.5:
                    box_ft("beam_%s_%d" % (room["name"], k), x0 + 0.2, y - w_ft / 2, x1 - 0.2, y + w_ft / 2, zc - d_ft, zc, mat, self.col)
                    y += sp
                    k += 1
            else:
                x = x0 + sp / 2
                while x < x1 - 0.5:
                    box_ft("beam_%s_%d" % (room["name"], k), x - w_ft / 2, y0 + 0.2, x + w_ft / 2, y1 - 0.2, zc - d_ft, zc, mat, self.col)
                    x += sp
                    k += 1
            self.n("beams", k)

    # ------------------------------------------------------------------ picture lights
    def build_picture_lights(self):
        brass = self.mats.get("brass")
        glow = self.mats.get("lamp_glow")
        self.picture_light_positions = []
        for spec in self.plan.get("picture_lights", []):
            room = self.house.room_by_name[spec["room"]]
            fl = self.floors[room["floor"]]
            x0, y0, x1, y1 = room["b"]
            wall = spec["wall"]
            zc = fl["z"] + 7.6
            for i, y in enumerate(spec["y"]):
                if wall == "east":
                    face = x1 - self.wt / 2
                    arm_x0, arm_x1 = face - 0.3, face
                    cx = face - 0.32
                    art_x = face
                else:
                    face = x0 + self.wt / 2
                    arm_x0, arm_x1 = face, face + 0.3
                    cx = face + 0.32
                    art_x = face
                tag = "%s_%s_%d" % (room["name"], wall, i)
                box_ft("pl_arm_%s" % tag, arm_x0, y - 0.03, arm_x1, y + 0.03, zc + 0.05, zc + 0.11, brass, self.col)
                cylinder_ft("pl_body_%s" % tag, (cx, y, zc), 0.08, 1.4, brass, self.col, segments=16, axis="Y")
                box_ft("pl_lens_%s" % tag, cx - 0.05, y - 0.6, cx + 0.05, y + 0.6, zc - 0.085, zc - 0.075, glow, self.col)
                self.picture_light_positions.append({"room": room["name"], "wall": wall, "x": art_x, "y": y, "z": zc,
                                                     "aim_x": art_x, "aim_z": zc - 2.2})
            self.n("picture lights", len(spec["y"]))

    # ------------------------------------------------------------------ stair
    def build_stair(self):
        st = self.plan.get("stair")
        if not st:
            return
        top = self.floors[st["floor_top"]]
        bot = self.floors[st["floor_bottom"]]
        rise_total = top["z"] - bot["z"]
        n = st["risers"]
        rise = rise_total / n
        tread = st.get("tread_in", 10.5) / 12.0
        x0, x1 = st["x0"], st["x1"]
        yt = st["y_top"]
        run = tread * (n - 1)
        yb = yt + run
        oak = self.mats.get(st.get("tread_m", "oak"))
        walnut = self.mats.get(st.get("stringer_m", "walnut"))
        rail_m = self.mats.get(st.get("rail_m", "bronze"))
        # well: cut the top floor slab and the ceiling slab below it
        well = [x0, yt, x1, yb + 0.9, bot["z"] + bot["h"] - 0.1, top["z"] + 0.1]
        targets = [o for o in self.house.slabs if overlap(bounds_of(o), well)]
        cut_with_box(targets, well, "cut_well")
        # treads and risers
        for i in range(1, n):
            ty0 = yt + (i - 1) * tread
            zt = top["z"] - i * rise
            box_ft("tread_%d" % i, x0 + 0.1, ty0 - 0.08, x1 - 0.1, ty0 + tread + 0.02, zt - 1.5 * IN, zt, oak, self.col)
            box_ft("riser_%d" % i, x0 + 0.1, ty0 - 0.02, x1 - 0.1, ty0 + 0.06, zt - rise, zt - 1.5 * IN, walnut, self.col)
        # bottom riser to the lower floor
        box_ft("riser_%d" % n, x0 + 0.1, yb - 0.02, x1 - 0.1, yb + 0.06, bot["z"], top["z"] - (n - 1) * rise - 1.5 * IN, walnut, self.col)
        # stringers: sloped boards under each side
        depth = 1.0
        prof = [(yt - 0.3, top["z"] + 0.0), (yb + 0.3, bot["z"] + 0.2 + 0.0),
                (yb + 0.3, bot["z"] + 0.2 - depth), (yt - 0.3, top["z"] - depth)]
        # shift the profile so the top edge sits just under the tread nosings
        prof = [(y, z - rise * 0.9) for (y, z) in prof]
        prism_yz("stringer_w", prof, x0, x0 + 0.12, walnut, self.col)
        prism_yz("stringer_e", prof, x1 - 0.12, x1, walnut, self.col)
        # rails: posts every 3 treads on both sides, top rail sloped, only below the upper floor level
        for side, xx in (("w", x0 + 0.06), ("e", x1 - 0.06)):
            pts = []
            for i in range(2, n, 3):
                ty = yt + (i - 1) * tread + tread / 2
                zt = top["z"] - i * rise
                if zt + 3.0 > top["z"] - 0.3:
                    continue
                cylinder_ft("post_%s_%d" % (side, i), (xx, ty, zt), 0.04, 3.0, rail_m, self.col, segments=10)
                pts.append((xx, ty, zt + 3.0))
            if len(pts) >= 2:
                p0 = (pts[0][0], pts[0][1] - tread, pts[0][2] + rise * (tread / tread))
                p1 = (pts[-1][0], pts[-1][1] + tread, pts[-1][2] - rise)
                beam_between("rail_%s" % side, p0, p1, 0.12, 0.08, rail_m, self.col)
        # handrail on the upper hall side walls is implied by the spine walls; nothing more needed
        log("stair: %d risers, rise %.2f ft, run %.1f ft, lands at y=%.1f" % (n, rise, run, yb))
        self.n("stair", 1)

    # ------------------------------------------------------------------ exterior
    def build_exterior(self):
        ex = self.plan.get("exterior")
        if not ex:
            return
        # footprint from main-floor rooms
        rooms = [r for r in self.house.rooms if r["floor"] == "main"]
        X0 = min(r["b"][0] for r in rooms)
        Y0 = min(r["b"][1] for r in rooms)
        X1 = max(r["b"][2] for r in rooms)
        Y1 = max(r["b"][3] for r in rooms)
        fl = self.floors["main"]
        st = self.plan.get("slab_thickness", 0.5)
        z_bot = self.plan.get("ground", {}).get("z", -0.3) - 0.6
        z_top = fl["z"] + fl["h"] + st / 2
        t = ex.get("skin_t", 0.5)
        skin = self.mats.get(ex.get("skin_m", "brick"))
        cedar = self.mats.get(ex.get("soffit_m", "cedar"))
        roof_m = self.mats.get(ex.get("roof_m", "roof"))
        skins = [
            box_ft("skin_s", X0 - t, Y0 - t, X1 + t, Y0, z_bot, z_top, skin, self.col, {"axis": "x", "floor": "main"}),
            box_ft("skin_n", X0 - t, Y1, X1 + t, Y1 + t, z_bot, z_top, skin, self.col, {"axis": "x", "floor": "main"}),
            box_ft("skin_w", X0 - t, Y0, X0, Y1, z_bot, z_top, skin, self.col, {"axis": "y", "floor": "main"}),
            box_ft("skin_e", X1, Y0, X1 + t, Y1, z_bot, z_top, skin, self.col, {"axis": "y", "floor": "main"}),
        ]
        # cut exterior openings through the skin
        for op in self.plan["openings"]:
            if op["floor"] != "main" or not self.is_exterior(op):
                continue
            z0 = fl["z"] + op.get("z0", 0)
            z1 = z0 + op["h"]
            if op.get("z0", 0) == 0:
                z0 -= 0.05
            if op["axis"] == "x":
                b = [op["c"] - op["w"] / 2, op["at"] - t - 0.1, op["c"] + op["w"] / 2, op["at"] + t + 0.1, z0, z1]
            else:
                b = [op["at"] - t - 0.1, op["c"] - op["w"] / 2, op["at"] + t + 0.1, op["c"] + op["w"] / 2, z0, z1]
            targets = [s for s in skins if s["axis"] == op["axis"] and overlap(bounds_of(s), b)]
            if targets:
                cut_with_box(targets, b, "cut_skin")
        # roof: low gable, ridge along X at mid Y, deep eaves
        eave = ex.get("eave", 4.0)
        pitch = ex.get("pitch", 0.25)
        thick = 0.6
        z_wall = z_top + 0.4
        ym = (Y0 + Y1) / 2
        ridge_z = z_wall + (ym - Y0) * pitch
        half = (ym - Y0) + eave
        ang = math.degrees(math.atan(pitch))
        length_slope = half / math.cos(math.radians(ang))
        # south plane: from ridge down toward -Y
        rs = box_local("roof_s", (X1 + eave + t, ym, ridge_z), (X1 - X0 + 2 * (eave + t), length_slope, thick),
                       180, roof_m, self.col, rot_x_deg=-ang)
        rn = box_local("roof_n", (X0 - eave - t, ym, ridge_z), (X1 - X0 + 2 * (eave + t), length_slope, thick),
                       0, roof_m, self.col, rot_x_deg=-ang)
        for ob in (rs, rn):
            set_face_material(ob, 0, cedar)  # underside = soffit
        # ridge cap
        box_ft("ridge", X0 - eave - t, ym - 0.3, X1 + eave + t, ym + 0.3, ridge_z + thick - 0.1, ridge_z + thick + 0.15, roof_m, self.col)
        # gable end walls (triangles) at X0 and X1
        prof = [(Y0 - t, z_top - 0.01), (Y1 + t, z_top - 0.01), (ym, ridge_z + 0.3)]
        prism_yz("gable_w", prof, X0 - t, X0 + 0.2, skin, self.col)
        prism_yz("gable_e", prof, X1 - 0.2, X1 + t, skin, self.col)
        # fascia boards along the eaves
        fasc = self.mats.get(ex.get("fascia_m", "cedar"))
        eave_z = ridge_z - half * pitch
        box_ft("fascia_s", X0 - eave - t, Y0 - eave - t - 0.15, X1 + eave + t, Y0 - eave - t, eave_z - 0.5, eave_z + 0.35, fasc, self.col)
        box_ft("fascia_n", X0 - eave - t, Y1 + eave + t, X1 + eave + t, Y1 + eave + t + 0.15, eave_z - 0.5, eave_z + 0.35, fasc, self.col)
        # chimney mass on the west wall behind the fireplace
        for f in self.plan.get("features", []):
            if "fireplace" in f["note"]:
                b = f["box"]
                box_ft("chimney", X0 - t - 1.8, b[1] + 3, X0 - t + 0.01, b[3] - 3, z_bot, ridge_z + 3.0, skin, self.col)
                box_ft("chimney_cap", X0 - t - 2.0, b[1] + 2.8, X0 - t + 0.2, b[3] - 2.8, ridge_z + 3.0, ridge_z + 3.25, self.mats.get("stone"), self.col)
        # terrace and walk
        gz = self.plan.get("ground", {}).get("z", -0.3)
        for key in ("terrace", "walk"):
            spec = ex.get(key)
            if spec:
                b = spec["b"]
                box_ft(key, b[0], b[1], b[2], b[3], gz - 0.2, gz + 0.25, self.mats.get(spec.get("m", "concrete")), self.col)
        # simple planting beds and a few tree stand-ins outside the rear glass so the view is not empty
        self.build_trees()
        self.n("exterior", 1)

    def build_trees(self):
        trunk = self.mats.get("walnut")
        leaf = self.mats.get("leaf")
        import random
        rnd = random.Random(7)
        gz = self.plan.get("ground", {}).get("z", -0.3)
        spots = [(-8, 64, 26), (12, 72, 30), (32, 66, 24), (52, 22, 28), (50, 56, 22), (-12, 30, 26), (-16, -26, 24), (-6, -20, 22), (60, -14, 26)]
        if not self.plan.get("exterior", {}).get("procedural_trees", True):
            spots = []
        for i, (x, y, h) in enumerate(spots):
            cylinder_ft("tree_trunk_%d" % i, (x, y, gz), 0.55, h * 0.5, trunk, self.col, segments=10)
            for j in range(4):
                r = h * rnd.uniform(0.22, 0.30)
                ox, oy = rnd.uniform(-h * 0.12, h * 0.12), rnd.uniform(-h * 0.12, h * 0.12)
                zc = gz + h * 0.5 + j * h * 0.12 + r * 0.4
                s = sphere_ft("tree_crown_%d_%d" % (i, j), (x + ox, y + oy, zc), r, leaf, self.col, 12, 8)
                s.scale = (1.0, 1.0, 0.8)
        if self.plan.get("exterior", {}).get("procedural_trees", True):
            # low hedges along the terrace edge and the street
            box_ft("hedge_n", -2, 60.5, 28, 62, gz, gz + 2.5, leaf, self.col)
            box_ft("hedge_s", -3, -16, 9, -14.5, gz, gz + 2.0, leaf, self.col)
            box_ft("hedge_s2", 19, -16, 45, -14.5, gz, gz + 2.0, leaf, self.col)

    # ------------------------------------------------------------------ run
    def build_all(self):
        if not self.plan.get("site"):
            self.build_exterior()
        self.build_casings_and_doors()
        self.build_windows()
        self.build_baseboards()
        self.build_beams()
        self.build_picture_lights()
        if self.plan.get("stair") and not self.plan.get("stairs"):
            self.build_stair()
        log("details:", ", ".join("%s %d" % kv for kv in sorted(self.counts.items())))


def build(plan, house, mats):
    d = Details(plan, house, mats)
    d.build_all()
    house.details = d
    return d
