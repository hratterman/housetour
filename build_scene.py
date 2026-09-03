"""
build_scene.py: builds the house from plan.json inside Blender and renders it.

Run inside Blender:
    blender -b -P build_scene.py -- --plan plan.json --shot main_floor --res 640x360 --samples 32

Everything is data-driven. Coordinates in plan.json are feet; this script converts to
meters. See README.md for the full CLI.
"""
import argparse
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ----------------------------------------------------------------------------- args


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--plan", default=os.path.join(HERE, "plan.json"))
    p.add_argument("--shot", default="none", help="shot name, 'all', or 'none' (build only)")
    p.add_argument("--res", default="1280x720")
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("--frame-step", type=int, default=1)
    p.add_argument("--still", default=None, help="shot:t[:name]  render one frame and exit")
    p.add_argument("--view", default=None, help="name:px,py,pz,lx,ly,lz  render one frame from a free pose (feet) and exit")
    p.add_argument("--out", default=os.path.join(HERE, "renders"))
    p.add_argument("--device", default="CPU", help="CPU, METAL, CUDA, OPTIX, HIP, ONEAPI")
    p.add_argument("--exposure", type=float, default=None, help="override plan camera.exposure")
    p.add_argument("--stage", default="auto",
                   help="phase1 (boxes only), phase2 (textures, details, staging), or auto")
    p.add_argument("--no-blend", action="store_true", help="do not save renders/scene.blend")
    p.add_argument("--check-paths", action="store_true", help="key every shot, run the collision check, render nothing")
    p.add_argument("--staging", default=None, help="alternate staging json (default staging.json)")
    p.add_argument("--no-bevel", action="store_true", help="skip the edge bevel pass (faster builds)")
    p.add_argument("--frame-start", type=int, default=None)
    p.add_argument("--frame-end", type=int, default=None)
    p.add_argument("--motion-blur", default=None, help="on/off override")
    p.add_argument("--dof", default=None, help="on/off override")
    return p.parse_args(argv)


# ----------------------------------------------------------------------------- helpers

from geom import (FT, m, log, box_ft, bounds_of, overlap, get_collection, boolean_cut,  # noqa: E402
                  kelvin_rgb, cut_with_box)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block_list in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                       bpy.data.cameras, bpy.data.images, bpy.data.node_groups):
        for b in list(block_list):
            block_list.remove(b)


# ----------------------------------------------------------------------------- materials

_MAT_CACHE = {}


def make_material(name, spec):
    """Principled BSDF from a spec. Phase 2 texture sets are handled by materials_pbr.py."""
    if name in _MAT_CACHE:
        return _MAT_CACHE[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    rgb = spec.get("rgb", [0.8, 0.8, 0.8])
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = spec.get("rough", 0.5)
    bsdf.inputs["Metallic"].default_value = spec.get("metallic", 0.0)
    if "ior" in spec:
        bsdf.inputs["IOR"].default_value = spec["ior"]
    if spec.get("transmission"):
        bsdf.inputs["Transmission Weight"].default_value = spec["transmission"]
    if spec.get("emit"):
        bsdf.inputs["Emission Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        bsdf.inputs["Emission Strength"].default_value = spec["emit"]
    if spec.get("thin"):
        mat.blend_method = "HASHED"
    _MAT_CACHE[name] = mat
    return mat


class Materials:
    def __init__(self, plan, stage):
        path = plan.get("materials_file", "materials/materials.json")
        if not os.path.isabs(path):
            path = os.path.join(HERE, path)
        with open(path) as f:
            self.specs = json.load(f)
        self.stage = stage
        self.pbr = None
        if stage == "phase2":
            try:
                import materials_pbr
                self.pbr = materials_pbr.PBRLibrary(HERE, self.specs)
                log("PBR library:", self.pbr.summary())
            except Exception as e:  # noqa
                log("PBR library unavailable, falling back to flat materials:", e)

    def get(self, name):
        if name not in self.specs:
            raise KeyError("unknown material %r" % name)
        if self.pbr is not None:
            mat = self.pbr.get(name)
            if mat is not None:
                return mat
        return make_material(name, self.specs[name])


# ----------------------------------------------------------------------------- rooms


class House:
    """Rooms are unions of axis-aligned rectangles ("parts", wall centerlines). Walls are built per edge
    segment: nothing where the segment borders another part of the same room, a half wall (wt/2, inside the
    bounds) where it borders another room, a full exterior wall (ext_t, inside the bounds) elsewhere."""

    def __init__(self, plan, mats):
        self.plan = plan
        self.mats = mats
        self.wt = plan.get("wall_thickness", 0.5)
        self.st = plan.get("slab_thickness", 0.5)
        self.ext_t = plan.get("exterior", {}).get("wall_t", self.wt)
        self.rooms = plan["rooms"]
        for r in self.rooms:  # legacy single-rect rooms
            if "parts" not in r:
                r["parts"] = [r["b"]]
            if "b" not in r:
                xs = [p[0] for p in r["parts"]] + [p[2] for p in r["parts"]]
                ys = [p[1] for p in r["parts"]] + [p[3] for p in r["parts"]]
                r["b"] = [min(xs), min(ys), max(xs), max(ys)]
        self.floors = plan["floors"]
        self.walls = []
        self.slabs = []
        self.room_by_name = {r["name"]: r for r in self.rooms}
        self.col_shell = get_collection("shell")
        self.col_features = get_collection("features")
        self.col_lights = get_collection("lights")
        self.col_cameras = get_collection("cameras")
        # edges declared fully open (no wall at all) by openings with kind "open" and full=true
        self.open_edges = [o for o in plan.get("openings", []) if o.get("kind") == "open" and o.get("full")]

    # -- geometry helpers ---------------------------------------------------------------------
    def parts_on_floor(self, floor):
        return [(r, p) for r in self.rooms if r["floor"] == floor for p in r["parts"]]

    def edge_segments(self, room, part, side):
        """Split one edge of a part into segments tagged 'same' (same room), 'room' (other room) or 'ext'."""
        x0, y0, x1, y1 = part
        if side in ("south", "north"):
            at = y0 if side == "south" else y1
            lo, hi = x0, x1
        else:
            at = x0 if side == "west" else x1
            lo, hi = y0, y1
        cuts = {lo, hi}
        nbrs = []
        for r, p in self.parts_on_floor(room["floor"]):
            if p is part:
                continue
            if side in ("south", "north"):
                touches = abs((p[3] if side == "south" else p[1]) - at) < 1e-6
                a, b = p[0], p[2]
            else:
                touches = abs((p[2] if side == "west" else p[0]) - at) < 1e-6
                a, b = p[1], p[3]
            if touches and min(b, hi) - max(a, lo) > 1e-6:
                nbrs.append((max(a, lo), min(b, hi), r))
                cuts.add(max(a, lo))
                cuts.add(min(b, hi))
        # fully open edges also split the segments
        for o in self.open_edges:
            if o["floor"] != room["floor"]:
                continue
            if side in ("south", "north") and o["axis"] == "x" and abs(o["at"] - at) < 1e-6:
                a, b = o["c"] - o["w"] / 2, o["c"] + o["w"] / 2
            elif side in ("west", "east") and o["axis"] == "y" and abs(o["at"] - at) < 1e-6:
                a, b = o["c"] - o["w"] / 2, o["c"] + o["w"] / 2
            else:
                continue
            if min(b, hi) - max(a, lo) > 1e-6:
                cuts.add(max(a, lo))
                cuts.add(min(b, hi))
        pts = sorted(cuts)
        segs = []
        for a, b in zip(pts[:-1], pts[1:]):
            if b - a < 1e-6:
                continue
            mid = (a + b) / 2
            kind, other = "ext", None
            for na, nb, r in nbrs:
                if na - 1e-6 <= mid <= nb + 1e-6:
                    kind, other = ("same" if r is room else "room"), r
                    break
            is_open = False
            for o in self.open_edges:
                if o["floor"] != room["floor"]:
                    continue
                if ((side in ("south", "north") and o["axis"] == "x") or (side in ("west", "east") and o["axis"] == "y")) \
                        and abs(o["at"] - at) < 1e-6 and o["c"] - o["w"] / 2 - 1e-6 <= mid <= o["c"] + o["w"] / 2 + 1e-6:
                    is_open = True
            if is_open:
                kind = "open"
            segs.append((a, b, kind, other))
        return segs

    def build_rooms(self):
        wt, st = self.wt, self.st
        half = wt / 2
        ext = self.plan.get("exterior", {})
        for room in self.rooms:
            fl = self.floors[room["floor"]]
            z, h = fl["z"], fl["h"]
            nm = room["name"]
            wall_mat = self.mats.get(room["wall"])
            floor_mat = self.mats.get(room["floorm"])
            ceil_mat = self.mats.get(room["ceil"])
            ext_t = room.get("exterior_wall", self.ext_t)
            for pi, part in enumerate(room["parts"]):
                x0, y0, x1, y1 = part
                tag = nm if len(room["parts"]) == 1 else "%s_%d" % (nm, pi)
                if not room.get("void"):
                    s = box_ft("floor_%s" % tag, x0, y0, x1, y1, z - st / 2, z, floor_mat, self.col_shell,
                               {"room": nm, "floor": room["floor"], "kind": "floor"})
                    self.slabs.append(s)
                if not room.get("no_ceiling"):
                    s = box_ft("ceil_%s" % tag, x0, y0, x1, y1, z + h, z + h + st / 2, ceil_mat, self.col_shell,
                               {"room": nm, "floor": room["floor"], "kind": "ceil"})
                    self.slabs.append(s)
                # walls, per edge segment; inset the side walls by the front/back wall thickness at each end
                seg_info = {side: self.edge_segments(room, part, side) for side in ("south", "north", "west", "east")}

                def thickness(kind):
                    return None if kind in ("same", "open") else (half if kind == "room" else ext_t)

                def end_kind(side_segs, coord):
                    for a, b, kind, other in side_segs:
                        if a - 1e-6 <= coord <= b + 1e-6:
                            return kind
                    return None

                def end_inset(side_segs, coord, ext_only=False):
                    # thickness of the perpendicular wall touching this end (0 if none). Exterior walls run continuous
                    # past interior partitions (ext_only), so only another exterior wall at a corner insets them.
                    for a, b, kind, other in side_segs:
                        if a - 1e-6 <= coord <= b + 1e-6:
                            if ext_only and kind != "ext":
                                return 0.0
                            t = thickness(kind)
                            return t or 0.0
                    return 0.0

                k = 0
                for side, segs in seg_info.items():
                    for a, b, kind, other in segs:
                        t = thickness(kind)
                        if t is None:
                            continue
                        axis = "x" if side in ("south", "north") else "y"
                        if side == "south":
                            bx = [a, y0, b, y0 + t]
                        elif side == "north":
                            bx = [a, y1 - t, b, y1]
                        elif side == "west":
                            ia = end_inset(seg_info["south"], x0, kind == "ext") if abs(a - y0) < 1e-6 else 0.0
                            ib = end_inset(seg_info["north"], x0, kind == "ext") if abs(b - y1) < 1e-6 else 0.0
                            bx = [x0, a + ia, x0 + t, b - ib]
                        else:
                            ia = end_inset(seg_info["south"], x1, kind == "ext") if abs(a - y0) < 1e-6 else 0.0
                            ib = end_inset(seg_info["north"], x1, kind == "ext") if abs(b - y1) < 1e-6 else 0.0
                            bx = [x1 - t, a + ia, x1, b - ib]
                        if bx[2] - bx[0] < 1e-4 or bx[3] - bx[1] < 1e-4:
                            continue
                        w = box_ft("wall_%s_%s_%d" % (tag, side, k), bx[0], bx[1], bx[2], bx[3], z, z + h, wall_mat,
                                   self.col_shell, {"room": nm, "floor": room["floor"], "kind": "wall", "axis": axis,
                                                    "side": side, "exterior": kind == "ext"})
                        k += 1
                        if kind == "ext":
                            # clad the end faces only where they turn an outside corner (the perpendicular wall is exterior)
                            if side in ("south", "north"):
                                perp_a = end_kind(seg_info["west"], y0 if side == "south" else y1) if abs(a - x0) < 1e-6 else None
                                perp_b = end_kind(seg_info["east"], y0 if side == "south" else y1) if abs(b - x1) < 1e-6 else None
                            else:
                                perp_a = end_kind(seg_info["south"], x0 if side == "west" else x1) if abs(a - y0) < 1e-6 else None
                                perp_b = end_kind(seg_info["north"], x0 if side == "west" else x1) if abs(b - y1) < 1e-6 else None
                            self.face_exterior(w, side, room["floor"], ext, corners=(perp_a == "ext", perp_b == "ext"))
                        self.walls.append(w)
        # voids: cut slabs
        for v in self.plan.get("voids", []):
            b = v["b"]
            fl = self.floors[v["floor"]]
            z = fl["z"] if v["what"] == "floor" else fl["z"] + fl["h"]
            bnd = [b[0], b[1], b[2], b[3], z - self.st, z + self.st]
            targets = [s for s in self.slabs if s["floor"] == v["floor"] and s["kind"] == v["what"] and overlap(bounds_of(s), bnd)]
            if targets:
                cut_with_box(targets, bnd, "cut_void")
        log("rooms:", len(self.rooms), "walls:", len(self.walls), "slabs:", len(self.slabs), "voids:", len(self.plan.get("voids", [])))

    def face_exterior(self, wall, side, floor, ext, corners=(False, False)):
        """Give the outward face of an exterior wall its cladding material (brick base, cedar upper)."""
        from geom import set_face_material
        spec = None
        if floor in ext.get("base", {}).get("floors", []):
            spec = ext["base"]["m_out"]
        elif floor in ext.get("upper", {}).get("floors", []):
            spec = ext["upper"]["m_out"]
        elif floor == "garage" and "garage" in ext:
            spec = ext["garage"]["m_out_low"]
        if not spec:
            return
        faces = {"south": 2, "east": 3, "north": 4, "west": 5}
        set_face_material(wall, faces[side], self.mats.get(spec))
        # end faces at outside corners are exposed too (a: low end, b: high end along the wall)
        ends = ("west", "east") if side in ("south", "north") else ("south", "north")
        for is_corner, end in zip(corners, ends):
            if is_corner:
                set_face_material(wall, faces[end], self.mats.get(spec))

    def build_openings(self):
        cut = 0
        skipped = []
        for op in self.plan["openings"]:
            if op.get("kind") == "open" and op.get("full"):
                op["_cut_walls"] = []
                continue
            fl = self.floors[op["floor"]]
            z0 = fl["z"] + op.get("z0", 0)
            z1 = z0 + op["h"]
            pad = max(self.wt, self.ext_t) * 1.2
            if op["axis"] == "x":
                b = [op["c"] - op["w"] / 2, op["at"] - pad, op["c"] + op["w"] / 2, op["at"] + pad, z0, z1]
            else:
                b = [op["at"] - pad, op["c"] - op["w"] / 2, op["at"] + pad, op["c"] + op["w"] / 2, z0, z1]
            if op.get("z0", 0) == 0:
                b[4] -= 0.02
            cutter = box_ft("cutter_%s" % op["note"].replace(" ", "_"), *b)
            targets = [w for w in self.walls
                       if w["floor"] == op["floor"] and w["axis"] == op["axis"] and overlap(bounds_of(w), b)]
            if not targets:
                skipped.append(op["note"])
            for w in targets:
                boolean_cut(w, cutter)
                cut += 1
            bpy.data.objects.remove(cutter, do_unlink=True)
            op["_cut_walls"] = [w.name for w in targets]
        log("openings:", len(self.plan["openings"]), "wall cuts:", cut)
        if skipped:
            log("WARNING openings that hit no wall:", skipped)

    def build_columns(self):
        for c in self.plan.get("columns", []):
            box_ft("col_%s" % c["note"].replace(" ", "_"), *c["b"], mat=self.mats.get(c["m"]), collection=self.col_features)

    def build_pits(self):
        for pit in self.plan.get("pits", []):
            room = self.room_by_name[pit["room"]]
            fl = self.floors[room["floor"]]
            z = fl["z"]
            px0, py0, px1, py1 = pit["b"]
            d = pit["depth"]
            floors_ = [o for o in self.slabs if o["room"] == room["name"] and o["kind"] == "floor"]
            cut_with_box(floors_, [px0, py0, px1, py1, z - self.st, z + 0.1], "cutter_pit")
            edge = self.mats.get(pit["edge"])
            seat = self.mats.get(pit["seat"])
            floor_mat = self.mats.get(pit.get("floor_m", room["floorm"]))
            box_ft("pit_floor", px0, py0, px1, py1, z - d - self.st / 2, z - d, floor_mat, self.col_features)
            t = 0.25
            lip = pit.get("lip", 0.9)
            zb, zt = z - d - self.st / 2, z + lip
            box_ft("pit_wall_s", px0, py0, px1, py0 + t, zb, zt, edge, self.col_features)
            box_ft("pit_wall_n", px0, py1 - t, px1, py1, zb, z + (0.0 if pit.get("open_side") == "north" else lip), edge, self.col_features)
            box_ft("pit_wall_w", px0, py0 + t, px0 + t, py1 - t, zb, zt, edge, self.col_features)
            box_ft("pit_wall_e", px1 - t, py0 + t, px1, py1 - t, zb, zt, edge, self.col_features)
            log("pit in", room["name"], "depth", d)

    def build_ground(self):
        g = self.plan.get("ground")
        if not g:
            return
        half = g.get("size", 400) / 2
        parts = [p for r, p in self.parts_on_floor("main")]
        X0 = min(p[0] for p in parts); Y0 = min(p[1] for p in parts)
        X1 = max(p[2] for p in parts); Y1 = max(p[3] for p in parts)
        z0, z1 = g["z"] - 0.5, g["z"]
        mat = self.mats.get(g.get("m", "lawn"))
        cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
        box_ft("ground_s", cx - half, cy - half, cx + half, Y0, z0, z1, mat, self.col_shell, {"kind": "ground"})
        box_ft("ground_n", cx - half, Y1, cx + half, cy + half, z0, z1, mat, self.col_shell, {"kind": "ground"})
        box_ft("ground_w", cx - half, Y0, X0, Y1, z0, z1, mat, self.col_shell, {"kind": "ground"})
        box_ft("ground_e", X1, Y0, cx + half, Y1, z0, z1, mat, self.col_shell, {"kind": "ground"})

    def build_features(self):
        n = 0
        for f in self.plan.get("features", []):
            box_ft("feat_%s" % f["note"].replace(" ", "_"), *f["box"], mat=self.mats.get(f["m"]), collection=self.col_features)
            n += 1
        log("features:", n)

    def build_stairs(self):
        """plan['stairs'] entries by kind: 'flight' (straight run along Y: treads, closed risers, stringers, handrail,
        optional open-side guard), 'landing' (platform), 'wall' (solid box), 'guard' (posts + top rail + glass)."""
        from geom import beam_between, cylinder_ft, prism_yz
        for st in self.plan.get("stairs", []):
            kind = st.get("kind", "flight")
            if kind == "landing":
                b = st["b"]
                box_ft("landing_%s" % st["name"], b[0], b[1], b[2], b[3], st["z"] - st.get("t", 0.6), st["z"],
                       self.mats.get(st.get("tread_m", "oak_floor")), self.col_features)
                continue
            if kind == "wall":
                box_ft(st["name"], *st["b"], mat=self.mats.get(st.get("m", "plaster_warm")), collection=self.col_features)
                continue
            if kind == "guard":
                self.build_guard(st)
                continue
            n = st["risers"]
            x0, x1 = st["x0"], st["x1"]
            yf, yt = st["y_from"], st["y_to"]
            zf, zt = st["z_from"], st["z_to"]
            rise = (zt - zf) / n
            run = (yt - yf) / (n - 1) if n > 1 else 0
            tread_m = self.mats.get(st.get("tread_m", "oak_floor"))
            riser_m = self.mats.get(st.get("riser_m", "oak_floor"))
            str_m = self.mats.get(st.get("stringer_m", "walnut"))
            rail_m = self.mats.get(st.get("rail_m", "bronze_black"))
            tt = 1.5 / 12
            d = 1 if run > 0 else -1
            for i in range(1, n):
                # tread i has its nosing at y = yf + (i-1)*run, top at zf + i*rise
                ya = yf + (i - 1) * run
                yb = ya + run
                zt_i = zf + i * rise
                box_ft("%s_tread_%d" % (st["name"], i), x0 + 0.08, min(ya, yb) - (0.08 if d > 0 else 0), x1 - 0.08,
                       max(ya, yb) + (0.08 if d < 0 else 0), zt_i - tt, zt_i, tread_m, self.col_features)
                box_ft("%s_riser_%d" % (st["name"], i), x0 + 0.08, ya - 0.04, x1 - 0.08, ya + 0.04,
                       zt_i - rise - tt, zt_i - tt, riser_m, self.col_features)
            # top riser to the upper floor / landing
            box_ft("%s_riser_%d" % (st["name"], n), x0 + 0.08, yt - 0.04, x1 - 0.08, yt + 0.04, zt - rise - tt, zt, riser_m, self.col_features)
            # stringers: sloped boards each side, 1 ft deep, under the nosing line
            depth = 1.0
            prof = [(yf - 0.4 * d, zf - rise * 0.6), (yt + 0.4 * d, zt - rise * 0.6), (yt + 0.4 * d, zt - rise * 0.6 - depth), (yf - 0.4 * d, zf - rise * 0.6 - depth)]
            if d < 0:
                prof = prof[::-1]
            prism_yz("%s_stringer_w" % st["name"], prof, x0, x0 + 0.1, str_m, self.col_features)
            prism_yz("%s_stringer_e" % st["name"], prof, x1 - 0.1, x1, str_m, self.col_features)
            # soffit board closing the underside (the flight below sees a walnut ceiling, not open risers)
            prism_yz("%s_soffit" % st["name"], [(yf - 0.4 * d, zf - rise * 0.6 - depth), (yt + 0.4 * d, zt - rise * 0.6 - depth),
                                                 (yt + 0.4 * d, zt - rise * 0.6 - depth + 0.1), (yf - 0.4 * d, zf - rise * 0.6 - depth + 0.1)][::(1 if d > 0 else -1)],
                     x0 + 0.1, x1 - 0.1, str_m, self.col_features)
            # handrail on the named wall side, 3 ft above nosings
            side = st.get("handrail", "east")
            hx = x1 - 0.2 if side == "east" else x0 + 0.2
            beam_between("%s_handrail" % st["name"], (hx, yf, zf + 3.0), (hx, yt, zt + 3.0 - rise), 0.15, 0.2, self.mats.get("walnut"), self.col_features)
            # guard on the open side: posts every 3 treads + top rail
            gside = st.get("guard")
            if gside:
                gx = x0 + 0.08 if gside == "west" else x1 - 0.08
                pts = []
                for i in range(1, n, 3):
                    y = yf + (i - 1) * run + run * 0.5
                    zt_i = zf + i * rise
                    cylinder_ft("%s_post_%d" % (st["name"], i), (gx, y, zt_i), 0.04, 3.2, rail_m, self.col_features, 10)
                    pts.append((gx, y, zt_i + 3.2))
                if len(pts) >= 2:
                    beam_between("%s_guard" % st["name"], pts[0], pts[-1], 0.12, 0.08, rail_m, self.col_features)
            log("stair %s: %d risers, rise %.3f ft, run %.3f ft" % (st["name"], n, rise, abs(run)))

    def build_guard(self, st):
        """Level guard: bronze posts every ~3 ft, a top rail at h, and a glass panel between."""
        from geom import beam_between, cylinder_ft
        p0, p1 = st["p0"], st["p1"]
        h = st.get("h", 3.5)
        rail_m = self.mats.get(st.get("m", "bronze_black"))
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        nseg = max(1, int(math.ceil(L / 3.0)))
        for i in range(nseg + 1):
            t = i / nseg
            x, y = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
            cylinder_ft("%s_post_%d" % (st["name"], i), (x, y, p0[2]), 0.05, h, rail_m, self.col_features, 12)
        beam_between("%s_rail" % st["name"], (p0[0], p0[1], p0[2] + h), (p1[0], p1[1], p1[2] + h), 0.15, 0.1, self.mats.get("walnut"), self.col_features)
        if st.get("glass", True):
            along_x = abs(p1[0] - p0[0]) >= abs(p1[1] - p0[1])
            g = self.mats.get("glass")
            if along_x:
                box_ft("%s_glass" % st["name"], min(p0[0], p1[0]) + 0.1, p0[1] - 0.02, max(p0[0], p1[0]) - 0.1, p0[1] + 0.02,
                       p0[2] + 0.2, p0[2] + h - 0.15, g, get_collection("glass"))
            else:
                box_ft("%s_glass" % st["name"], p0[0] - 0.02, min(p0[1], p1[1]) + 0.1, p0[0] + 0.02, max(p0[1], p1[1]) - 0.1,
                       p0[2] + 0.2, p0[2] + h - 0.15, g, get_collection("glass"))

    # -- lights (phase 1 fill only)
    def build_lights(self, room_fill_scale=1.0):
        warm = kelvin_rgb(2700)
        for room in self.rooms:
            fl = self.floors[room["floor"]]
            x0, y0, x1, y1 = room["parts"][0]
            ld = bpy.data.lights.new("area_%s" % room["name"], "AREA")
            ld.shape = "SQUARE"
            ld.size = m(2.0)
            ld.energy = room.get("light", 50) * room_fill_scale
            ld.color = warm
            ob = bpy.data.objects.new("light_%s" % room["name"], ld)
            ob.location = (m((x0 + x1) / 2), m((y0 + y1) / 2), m(fl["z"] + fl["h"] - 0.15))
            self.col_lights.objects.link(ob)
        sun = self.plan.get("sun", {"direction": [-0.4, 0.5, -0.75], "strength": 4.0})
        sd = bpy.data.lights.new("sun", "SUN")
        sd.energy = sun["strength"]
        sd.color = kelvin_rgb(5000)
        sd.angle = math.radians(1.5)
        so = bpy.data.objects.new("sun", sd)
        so.location = (m(21), m(23), m(40))
        so.rotation_euler = Vector(sun["direction"]).normalized().to_track_quat("-Z", "Y").to_euler()
        self.col_lights.objects.link(so)
        w = bpy.data.worlds.new("world")
        bpy.context.scene.world = w
        w.use_nodes = True
        bg = w.node_tree.nodes["Background"]
        wr = self.plan.get("world", {"rgb": [0.9, 0.85, 0.78], "strength": 0.8})
        bg.inputs[0].default_value = (wr["rgb"][0], wr["rgb"][1], wr["rgb"][2], 1.0)
        bg.inputs[1].default_value = wr["strength"]
        log("lights:", len(self.rooms), "area +", "sun")


# ----------------------------------------------------------------------------- camera / shots


def bevel_pass(plan):
    """Soften every hard edge: a small unapplied Bevel modifier on procedural boxes and shell walls.
    Imported models keep their own geometry. Width in inches from plan['bevel'] (default 0.4 in)."""
    spec = plan.get("bevel", {})
    w_detail = spec.get("detail_in", 0.4) / 12.0 * FT
    w_shell = spec.get("shell_in", 0.25) / 12.0 * FT
    w_soft = spec.get("soft_in", 1.2) / 12.0 * FT
    n = 0
    soft_tags = ("sofa_cushion", "sofa_back", "pillow", "bed_mattress", "bed_duvet", "bed_pillow", "bed_throw",
                 "bench_cush", "pit_seat", "pit_back", "fold", "towel", "jacket", "bag")
    skip_tags = ("glass", "canvas", "flame", "embers", "rug", "runner", "puzzle", "piece", "panel", "cove",
                 "reveal", "sput_rod", "stem", "leaf", "arc_seg", "tree_", "ground", "hedge")
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.hide_render or ob.name.startswith("proto_"):
            continue
        if ob.users_collection and ob.users_collection[0].name == "asset_lib":
            continue
        if ob.data.users > 1 and "size_m" in (ob.data.get("_proto") or {}):
            continue
        nm = ob.name
        if any(tag in nm for tag in skip_tags):
            continue
        if ob.get("kind") == "ground":
            continue
        # imported model instances share a mesh with the prototype; leave them alone
        if ob.data.users > 1 and not nm.startswith(("wall_", "floor_", "ceil_")):
            continue
        if any(tag in nm for tag in soft_tags):
            w, seg = w_soft, 3
        elif nm.startswith(("wall_", "floor_", "ceil_", "skin_", "roof", "gable", "chimney", "terrace", "walk")):
            w, seg = w_shell, 1
        else:
            w, seg = w_detail, 2
        # do not bevel wider than a third of the smallest dimension
        d = [abs(v) for v in ob.dimensions]
        d = [v for v in d if v > 1e-5]
        if not d:
            continue
        w = min(w, min(d) / 3.0)
        if w < 0.0005:
            continue
        mod = ob.modifiers.new("bevel", "BEVEL")
        mod.width = w
        mod.segments = seg
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(40)
        mod.use_clamp_overlap = True
        mod.harden_normals = False
        n += 1
    # smooth shading plus hardened normals on the bevel so the chamfers catch highlights cleanly
    for ob in bpy.data.objects:
        if ob.type == "MESH" and any(md.type == "BEVEL" for md in ob.modifiers):
            try:
                ob.data.shade_smooth()
            except Exception:
                for pg in ob.data.polygons:
                    pg.use_smooth = True
            for md in ob.modifiers:
                if md.type == "BEVEL":
                    md.harden_normals = True
    log("bevel pass: %d objects" % n)


def setup_camera(plan):
    cam_spec = plan.get("camera", {})
    cd = bpy.data.cameras.new("cam")
    cd.lens = cam_spec.get("focal_mm", 24)
    cd.sensor_width = cam_spec.get("sensor_mm", 36)
    cd.sensor_fit = "HORIZONTAL"
    cd.clip_start = 0.05
    cd.clip_end = 500
    cam = bpy.data.objects.new("camera", cd)
    get_collection("cameras").objects.link(cam)
    tgt = bpy.data.objects.new("cam_target", None)
    tgt.empty_display_size = 0.2
    get_collection("cameras").objects.link(tgt)
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    bpy.context.scene.camera = cam
    return cam, tgt


_PLAN_CAMERA = {}


def key_shot(scene, cam, tgt, shot, fps, base_exposure=None, override=None):
    """Keyframe camera and target along the shot path. Returns (frame_start, frame_end)."""
    if override is not None:
        scene.view_settings.exposure = override
    elif "exposure" in shot:
        scene.view_settings.exposure = shot["exposure"]
    elif base_exposure is not None:
        scene.view_settings.exposure = base_exposure
    cam.animation_data_clear()
    tgt.animation_data_clear()
    n = int(round(shot["seconds"] * fps))
    for wp in shot["path"]:
        f = 1 + int(round(wp["t"] * fps))
        cam.location = tuple(m(v) for v in wp["pos"])
        tgt.location = tuple(m(v) for v in wp["look"])
        cam.keyframe_insert("location", frame=f)
        tgt.keyframe_insert("location", frame=f)
    for ob in (cam, tgt):
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.handle_left_type = "AUTO_CLAMPED"
                kp.handle_right_type = "AUTO_CLAMPED"
    # subtle handheld drift: slow noise on the look target so the move is not rail-perfect
    hh = shot.get("handheld_ft", _PLAN_CAMERA.get("handheld_ft", 0.0))
    if hh > 0:
        for i, fc in enumerate(tgt.animation_data.action.fcurves):
            mod = fc.modifiers.new("NOISE")
            mod.scale = 45.0
            mod.strength = m(hh) * 2
            mod.phase = 7.0 * i + 1
            mod.blend_in = 6
            mod.blend_out = 6
    scene.frame_start = 1
    scene.frame_end = n
    return 1, n


def check_path(scene, cam, shot, radius_ft=0.22):
    """Sample every frame; report any frame where the camera is within radius of shell/feature geometry."""
    from geom import world_bounds
    obs = []
    for o in bpy.data.objects:
        if o.type != "MESH" or o.get("kind") == "ground" or o.hide_render or o.name.startswith("proto_"):
            continue
        if o.users_collection and o.users_collection[0].name == "asset_lib":
            continue
        mn, mx = world_bounds(o)
        obs.append((o, mn, mx))
    hits = []
    r = m(radius_ft)
    for f in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(f)
        p = cam.matrix_world.translation
        for o, mn, mx in obs:
            if not (mn.x - r <= p.x <= mx.x + r and mn.y - r <= p.y <= mx.y + r and mn.z - r <= p.z <= mx.z + r):
                continue
            lp = o.matrix_world.inverted() @ p
            ok, loc, nrm, idx = o.closest_point_on_mesh(lp)
            if not ok:
                continue
            d = ((o.matrix_world @ loc) - p).length
            # parity ray cast along +X in local space: odd hit count means inside the solid
            count, origin, guard = 0, lp.copy(), 0
            while guard < 32:
                ok2, hloc, hn, hidx = o.ray_cast(origin, Vector((1, 0, 0)))
                if not ok2:
                    break
                count += 1
                origin = hloc + Vector((1e-4, 0, 0))
                guard += 1
            inside = (count % 2) == 1 and d < m(0.5)
            if inside or d < r:
                hits.append((f, o.name, round(d / FT, 2), inside))
    if hits:
        log("WARNING camera path %s: %d frame-object hits near/inside geometry" % (shot["name"], len(hits)))
        seen = set()
        for f, n, d, inside in hits:
            if n not in seen:
                log("   first at frame %d: %s dist %.2fft inside=%s" % (f, n, d, inside))
                seen.add(n)
    else:
        log("camera path %s clear (%d frames)" % (shot["name"], scene.frame_end))
    return hits


def shot_by_name(plan, name):
    for s in plan["shots"]:
        if s["name"] == name:
            return s
    raise KeyError("no shot named %r" % name)


# ----------------------------------------------------------------------------- render setup


def setup_render(scene, args, plan, stage):
    w, h = [int(v) for v in args.res.lower().split("x")]
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    scene.render.fps = plan.get("fps", 24)
    scene.render.engine = "CYCLES"
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.use_persistent_data = True
    cy = scene.cycles
    cy.samples = args.samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02 if args.samples < 64 else 0.01
    cy.use_denoising = bool(getattr(bpy.app.build_options, "openimagedenoise", True))
    if cy.use_denoising:
        try:
            cy.denoiser = "OPENIMAGEDENOISE"
            cy.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        except Exception:
            pass
    cy.max_bounces = 8
    cy.diffuse_bounces = 4
    cy.glossy_bounces = 4
    cy.transmission_bounces = 8
    cy.transparent_max_bounces = 8
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 1.0
    cy.sample_clamp_indirect = 10.0
    # device
    dev = args.device.upper()
    prefs = bpy.context.preferences.addons.get("cycles")
    if dev != "CPU" and prefs is not None:
        cprefs = prefs.preferences
        try:
            cprefs.compute_device_type = dev
            cprefs.get_devices()
            for d in cprefs.devices:
                d.use = (d.type == dev or d.type == "CPU")
            cy.device = "GPU"
            log("render device:", dev, [d.name for d in cprefs.devices if d.use])
        except Exception as e:  # noqa
            log("could not enable", dev, "falling back to CPU:", e)
            cy.device = "CPU"
    else:
        cy.device = "CPU"
        log("render device: CPU", os.cpu_count(), "threads")
    # color management
    vs = scene.view_settings
    try:
        vs.view_transform = "AgX"
        vs.look = "AgX - Medium High Contrast" if stage == "phase2" else "AgX - Base Contrast"
    except TypeError:
        vs.view_transform = "Filmic"
        vs.look = "Medium Contrast"
    exp = plan.get("camera", {}).get("exposure", 0.5)
    if args.exposure is not None:
        exp = args.exposure
    vs.exposure = exp
    vs.gamma = 1.0
    # motion blur / dof are phase 2 defaults, overridable
    mb = (stage == "phase2")
    if args.motion_blur is not None:
        mb = args.motion_blur.lower() in ("1", "on", "true", "yes")
    scene.render.use_motion_blur = mb
    scene.render.motion_blur_shutter = 0.5
    log("render:", w, "x", h, "samples", args.samples, "denoise", cy.use_denoising,
        "view", vs.view_transform, vs.look, "exposure", exp, "motion blur", mb)


def setup_dof(cam, tgt, plan, args, stage):
    on = (stage == "phase2")
    if args.dof is not None:
        on = args.dof.lower() in ("1", "on", "true", "yes")
    cam.data.dof.use_dof = on
    if on:
        cam.data.dof.focus_object = tgt
        cam.data.dof.aperture_fstop = plan.get("camera", {}).get("fstop", 4.0)


# ----------------------------------------------------------------------------- main


def render_frames(scene, out_dir, start, end, step, label):
    os.makedirs(out_dir, exist_ok=True)
    times = []
    t_all = time.time()
    for f in range(start, end + 1, step):
        scene.frame_set(f)
        scene.render.filepath = os.path.join(out_dir, "frame_%04d.png" % f)
        if os.path.exists(scene.render.filepath):
            log(label, "frame", f, "exists, skipping")
            continue
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        dt = time.time() - t0
        times.append(dt)
        log(label, "frame %d/%d  %.1fs" % (f, end, dt))
    total = time.time() - t_all
    if times:
        log(label, "rendered %d frames, mean %.1fs/frame, total %.1fs (%.1f min)" %
            (len(times), sum(times) / len(times), total, total / 60))
    return times, total


def main():
    args = parse_args()
    with open(args.plan) as f:
        plan = json.load(f)
    stage = args.stage
    if stage == "auto":
        stage = "phase2" if os.path.exists(os.path.join(HERE, "staging.json")) else "phase1"
    log("stage:", stage)
    t_build = time.time()
    clear_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    _PLAN_CAMERA.update(plan.get("camera", {}))
    mats = Materials(plan, stage)
    house = House(plan, mats)
    house.root = HERE
    house.build_rooms()
    house.build_openings()
    house.build_pits()
    house.build_features()
    house.build_columns()
    house.build_stairs()
    if plan.get("site"):
        import site_build
        site_build.build(plan, house, mats)
    else:
        house.build_ground()
    if stage == "phase2":
        import details
        import staging
        details.build(plan, house, mats)
        staging.build(plan, house, mats, args.staging)
        import lighting
        lighting.build(plan, house, mats)
        if not args.no_bevel:
            bevel_pass(plan)
    else:
        house.build_lights()

    cam, tgt = setup_camera(plan)
    setup_dof(cam, tgt, plan, args, stage)
    setup_render(scene, args, plan, stage)
    fps = plan.get("fps", 24)
    log("build time %.1fs, objects %d" % (time.time() - t_build, len(bpy.data.objects)))

    os.makedirs(args.out, exist_ok=True)
    if not args.no_blend:
        # key the first shot so the saved blend is inspectable
        key_shot(scene, cam, tgt, plan["shots"][0], fps)
        blend_path = os.path.join(args.out, "scene.blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)
        log("saved", blend_path)

    if args.view:
        name, coords = args.view.split(":")
        v = [float(x) for x in coords.split(",")]
        cam.animation_data_clear()
        tgt.animation_data_clear()
        cam.location = tuple(m(x) for x in v[:3])
        tgt.location = tuple(m(x) for x in v[3:6])
        if args.exposure is None:
            scene.view_settings.exposure = plan.get("camera", {}).get("exposure", 0.0) + (0.8 if v[2] < -1 else 0.0)
        scene.frame_set(1)
        still_dir = os.path.join(args.out, "stills")
        os.makedirs(still_dir, exist_ok=True)
        scene.render.filepath = os.path.join(still_dir, name + ".png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        log("view", name, "%.1fs" % (time.time() - t0))
        return

    if args.still:
        parts = args.still.split(":")
        shot = shot_by_name(plan, parts[0])
        t = float(parts[1])
        name = parts[2] if len(parts) > 2 else "%s_t%s" % (shot["name"], parts[1].replace(".", "p"))
        key_shot(scene, cam, tgt, shot, fps, plan.get("camera", {}).get("exposure", 0.0), args.exposure)
        check_path(scene, cam, shot)
        frame = 1 + int(round(t * fps))
        scene.frame_set(frame)
        still_dir = os.path.join(args.out, "stills")
        os.makedirs(still_dir, exist_ok=True)
        scene.render.filepath = os.path.join(still_dir, name + ".png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        log("still", name, "frame", frame, "%.1fs" % (time.time() - t0))
        return

    if args.check_paths:
        for shot in plan["shots"]:
            key_shot(scene, cam, tgt, shot, fps, plan.get("camera", {}).get("exposure", 0.0), args.exposure)
            check_path(scene, cam, shot)
        return
    if args.shot == "none":
        return
    shots = plan["shots"] if args.shot == "all" else [shot_by_name(plan, args.shot)]
    for shot in shots:
        s, e = key_shot(scene, cam, tgt, shot, fps, plan.get("camera", {}).get("exposure", 0.0), args.exposure)
        check_path(scene, cam, shot)
        log("shot", shot["name"], "exposure", scene.view_settings.exposure)
        if args.frame_start:
            s = max(s, args.frame_start)
        if args.frame_end:
            e = min(e, args.frame_end)
        out_dir = os.path.join(args.out, "frames", shot["name"])
        times, total = render_frames(scene, out_dir, s, e, args.frame_step, shot["name"])
        with open(os.path.join(args.out, "timing_%s.json" % shot["name"]), "w") as f:
            json.dump({"shot": shot["name"], "res": args.res, "samples": args.samples,
                       "frame_step": args.frame_step, "frames": len(times),
                       "mean_s": (sum(times) / len(times)) if times else None,
                       "total_s": total, "device": args.device, "stage": stage}, f, indent=2)


if __name__ == "__main__":
    main()
