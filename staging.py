"""
staging.py: Phase 2 furniture and objects. Reads staging.json, a list of placements:

    {"asset": "sofa_03" | "proc:<generator>", "room": "living", "pos": [x, y, z], "rot_z": 0,
     "scale": 1.0, "height_ft": 2.4, "length_ft": 7.5, "tint": [r,g,b], "note": "...", ...}

Model assets come from assets/models/<name>/<id>.gltf (CC0, see assets/manifest.json). Each model is
imported once, joined into one mesh, normalized to a bottom-center origin, then instanced.
Procedural generators build stand-ins with real proportions. Generators register practical lights
on house.practicals for lighting.py.
"""
import softgoods as sg
import json
import math
import os
import random

import bpy
from mathutils import Vector, Matrix

from geom import (FT, IN, m, log, box_ft, box_local, box_centered, beam_between, cylinder_ft, sphere_ft,
                  plane_ft, get_collection, join_objects, world_bounds, cut_with_box, prism_xz)

BOOK_MATS = ["book_a", "book_b", "book_c", "book_d", "book_e", "book_f", "book_g", "book_h", "book_i", "book_j"]


from gens2 import Gens2  # noqa: E402
from gens3 import Gens3  # noqa: E402


# models that are genuinely a group of separate pieces (a pair of boots, a set of books), not variants
KEEP_ALL_PARTS = {"book_encyclopedia_set_01", "brass_candleholders", "outdoor_table_chair_set_01",
                  "wine_bottles_01", "decorative_book_set_01", "kitchen_utensils", "wooden_ladder", "metal_tool_chest"}


class Stager(Gens2, Gens3):
    def __init__(self, plan, house, mats, root, staging_path=None):
        self.plan = plan
        self.house = house
        self.mats = mats
        self.root = root
        self.col = get_collection("staging")
        self.lib = get_collection("asset_lib")
        self.lib.hide_render = True
        self.protos = {}
        self.rng = random.Random(plan.get("seed", 1956))
        self.practicals = []
        house.practicals = self.practicals
        self.counts = {"models": 0, "procedural": 0, "missing": 0}
        path = staging_path or os.path.join(root, "staging.json")
        if not os.path.isabs(path):
            path = os.path.join(root, path)
        self.entries = json.load(open(path)) if os.path.exists(path) else []
        self.serial = 0

    def uid(self, base):
        self.serial += 1
        return "%s_%03d" % (base, self.serial)

    def ceil_z(self, room_name):
        r = self.house.room_by_name.get(room_name) if hasattr(self.house, "room_by_name") else None
        if r is None:
            return 9.5
        fl = self.house.floors[r["floor"]]
        return fl["z"] + fl["h"]

    def floor_z(self, room):
        r = self.house.room_by_name.get(room)
        if r is None:
            return 0.0
        return self.house.floors[r["floor"]]["z"]

    def mat(self, name):
        return self.mats.get(name)

    # ------------------------------------------------------------------ models
    def load_proto(self, name):
        if name in self.protos:
            return self.protos[name]
        d = os.path.join(self.root, "assets", "models", name)
        gltf = None
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".gltf") or f.endswith(".glb"):
                    gltf = os.path.join(d, f)
        if gltf is None:
            self.protos[name] = None
            return None
        before = {o.name for o in bpy.data.objects}
        try:
            bpy.ops.import_scene.gltf(filepath=gltf)
        except Exception as e:  # noqa
            log("gltf import failed", name, e)
            self.protos[name] = None
            return None
        new = [o for o in bpy.data.objects if o.name not in before]
        meshes = [o for o in new if o.type == "MESH"]
        other_names = [o.name for o in new if o.type != "MESH"]
        # apply transforms so joined geometry is in world space
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            self.lib.objects.link(o)
        for o in bpy.context.selected_objects:
            o.select_set(False)
        for o in meshes:
            o.select_set(True)
        if meshes:
            bpy.context.view_layer.objects.active = meshes[0]
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        # Poly Haven plant and prop files often carry several variants laid out side by side; keep the
        # largest piece and whatever touches its (slightly grown) bounds, drop the rest
        if len(meshes) > 1 and name not in KEEP_ALL_PARTS:
            bpy.context.view_layer.update()
            boxes = {}
            for o in meshes:
                mn, mx = world_bounds(o)
                boxes[o.name] = (mn, mx, (mx.x - mn.x) * (mx.y - mn.y) * max(mx.z - mn.z, 1e-4))
            main = max(meshes, key=lambda o: boxes[o.name][2])
            mmn, mmx = boxes[main.name][0].copy(), boxes[main.name][1].copy()
            grow = 0.15 * max(mmx.x - mmn.x, mmx.y - mmn.y, mmx.z - mmn.z) + 0.02
            keep, drop = [], []
            for o in meshes:
                mn, mx = boxes[o.name][0], boxes[o.name][1]
                touches = all(mn[i] <= mmx[i] + grow and mx[i] >= mmn[i] - grow for i in range(3))
                (keep if touches else drop).append(o)
            if drop:
                log("  %s: %d mesh parts kept, %d side-by-side variants dropped" % (name, len(keep), len(drop)))
                for o in drop:
                    bpy.data.objects.remove(o, do_unlink=True)
                meshes = keep
        ob = join_objects(meshes, "proto_%s" % name)
        for nm in other_names:
            o = bpy.data.objects.get(nm)
            if o is not None:
                bpy.data.objects.remove(o, do_unlink=True)
        if ob is None:
            self.protos[name] = None
            return None
        # normalize: origin at bottom center
        mn, mx = world_bounds(ob)
        c = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
        ob.data.transform(Matrix.Translation(-c))
        ob.location = (0, 0, 0)
        ob.hide_render = True
        ob.hide_viewport = True
        ob["size_m"] = [mx.x - mn.x, mx.y - mn.y, mx.z - mn.z]
        for p in ob.data.polygons:
            p.use_smooth = True
        self.protos[name] = ob
        return ob

    def place_model(self, e):
        proto = self.load_proto(e["asset"])
        if proto is None:
            self.counts["missing"] += 1
            log("  missing model", e["asset"], "->", e.get("fallback", "skipped"))
            fb = e.get("fallback")
            if fb:
                e2 = dict(e)
                e2["asset"] = fb
                return self.place(e2)
            return None
        mesh = proto.data
        if e.get("tint") or e.get("recolor"):
            # one tinted copy per (asset, tint, recolor): every placement shares it, so Cycles instances the mesh
            key = (e["asset"], tuple(e.get("tint") or ()), tuple(e.get("recolor") or ()))
            cache = getattr(self, "_tinted", None)
            if cache is None:
                cache = self._tinted = {}
            if key not in cache:
                mesh = mesh.copy()
                only = e.get("tint_only")   # substrings of material names to tint (e.g. leaves, not bark)
                names = [mt.name.lower() for mt in mesh.materials if mt is not None]
                if only and not any(any(o in nm for o in only) for nm in names):
                    only = None
                for i, mt in enumerate(mesh.materials):
                    if mt is None:
                        continue
                    if only and not any(o in mt.name.lower() for o in only):
                        continue
                    mt2 = mt.copy()
                    self.tint_material(mt2, e.get("tint"), e.get("recolor"))
                    mesh.materials[i] = mt2
                cache[key] = mesh
            mesh = cache[key]
        ob = bpy.data.objects.new(self.uid(e["asset"]), mesh)
        self.col.objects.link(ob)
        sz = proto["size_m"]
        s = e.get("scale", 1.0)
        if e.get("height_ft"):
            s *= m(e["height_ft"]) / max(sz[2], 1e-6)
        elif e.get("length_ft"):
            s *= m(e["length_ft"]) / max(max(sz[0], sz[1]), 1e-6)
        pos = list(e["pos"])
        if len(pos) == 2:
            pos.append(self.floor_z(e.get("room", "")))
        ob.location = (m(pos[0]), m(pos[1]), m(pos[2]))
        ob.rotation_euler = (0, 0, math.radians(e.get("rot_z", 0.0)))
        ob.scale = (s, s, s)
        ob["room"] = e.get("room", "")
        self.counts["models"] += 1
        return ob

    def tint_material(self, mt, tint, recolor):
        if not mt.use_nodes:
            return
        nt = mt.node_tree
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            return
        inp = bsdf.inputs["Base Color"]
        if recolor:
            # replace the base color entirely, keep roughness/normal maps
            for l in list(inp.links):
                nt.links.remove(l)
            inp.default_value = (recolor[0], recolor[1], recolor[2], 1.0)
            return
        if inp.links:
            src = inp.links[0].from_socket
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            nt.links.new(src, mix.inputs[6])
            mix.inputs[7].default_value = (tint[0], tint[1], tint[2], 1.0)
            nt.links.new(mix.outputs[2], inp)
        else:
            c = inp.default_value
            inp.default_value = (c[0] * tint[0], c[1] * tint[1], c[2] * tint[2], 1.0)

    # ------------------------------------------------------------------ dispatch
    def wall_lines(self, floor):
        """(boundary_x, boundary_y, interior_x, interior_y) coordinate sets for a floor, from the plan's room parts."""
        if not hasattr(self, "_wl"):
            self._wl = {}
        if floor in self._wl:
            return self._wl[floor]
        parts = [p for r in self.plan["rooms"] if r["floor"] == floor for p in r["parts"]]
        xs = set(); ys = set()
        for p in parts:
            xs.update((p[0], p[2])); ys.update((p[1], p[3]))
        bx = {min(xs), max(xs)}; by = {min(ys), max(ys)}
        # the second floor's stair tower reaches Y 0 while the volume starts at Y 6: both are exterior lines
        if floor == "second":
            by.add(6.0)
        self._wl[floor] = (bx, by, xs - bx, ys - by)
        return self._wl[floor]

    def wall_face(self, e, wall):
        """Shift a wall spec from the room line to the finished face: 1 ft for exterior walls, 3 in for partitions."""
        room = self.house.room_by_name.get(e.get("room", ""))
        if room is None:
            return wall
        bx, by, ix, iy = self.wall_lines(room["floor"])
        at = wall["at"]
        lines_b, lines_i = (bx, ix) if wall["axis"] == "y" else (by, iy)
        t = 0.0
        if any(abs(at - v) < 1e-6 for v in lines_b):
            t = room.get("exterior_wall", self.house.ext_t) if hasattr(self.house, "ext_t") else 1.0
        elif any(abs(at - v) < 1e-6 for v in lines_i):
            t = self.house.wt / 2 if hasattr(self.house, "wt") else 0.25
        if not t:
            return wall
        sign = 1 if wall["face"] in ("+x", "+y") else -1
        w = dict(wall)
        w["at"] = at + sign * t
        return w

    def place(self, e):
        if isinstance(e.get("wall"), dict) and not e.get("wall_is_face"):
            e = dict(e)
            e["wall"] = self.wall_face(e, e["wall"])
        a = e["asset"]
        if a.startswith("proc:"):
            fn = getattr(self, "gen_" + a[5:], None)
            if fn is None:
                log("  unknown generator", a)
                self.counts["missing"] += 1
                return None
            self.counts["procedural"] += 1
            return fn(e)
        return self.place_model(e)

    def build_all(self):
        for e in self.entries:
            if "asset" not in e and "set_material" not in e:
                continue
            rf = e.get("replace_feature")
            if rf:
                for nm in ([rf] if isinstance(rf, str) else rf):
                    ob = bpy.data.objects.get("feat_%s" % nm.replace(" ", "_"))
                    if ob is not None:
                        bpy.data.objects.remove(ob, do_unlink=True)
            sm = e.get("set_material")
            if sm:
                ob = bpy.data.objects.get(sm["object"])
                if ob is not None:
                    ob.data.materials.clear()
                    ob.data.materials.append(self.mat(sm["m"]))
                continue
            try:
                before = {o.name for o in bpy.data.objects}
                self.place(e)
                # tag what this entry created, for the clipping audit (build_scene --audit)
                idx = self.entries.index(e)
                for o in bpy.data.objects:
                    if o.name not in before:
                        o["entry"] = idx
                        o["entry_asset"] = e["asset"]
                        o["entry_room"] = e.get("room", "")
            except Exception as ex:  # noqa
                import traceback
                traceback.print_exc()
                log("  FAILED placement", e.get("note", e["asset"]), ex)
        log("staging: %(models)d model instances, %(procedural)d procedural, %(missing)d missing" % self.counts)

    # ------------------------------------------------------------------ helpers
    def light(self, **kw):
        self.practicals.append(kw)

    def P(self, e, k, d=None):
        return e.get(k, d)

    # ================================================================== generators
    # Each takes the entry dict. Positions in feet. Most use pos=[x,y,z] as a bottom-center anchor.

    def gen_rug(self, e):
        b = e["b"]
        z = e.get("z", self.floor_z(e.get("room", "")))
        t = e.get("thick", 0.045)
        ob = box_ft(self.uid("rug"), b[0], b[1], b[2], b[3], z + 0.002, z + t, self.mat(e.get("m", "rug_cream")), self.col)
        if e.get("rot_z"):
            ob.rotation_euler = (0, 0, math.radians(e["rot_z"]))
        return ob

    def gen_books(self, e):
        """Fill a shelf cavity [x0,y0,x1,y1,z0,z1] along its long horizontal axis with books."""
        b = e["b"]
        density = e.get("density", 0.85)
        rng = random.Random(e.get("seed", self.rng.randint(0, 10 ** 6)))
        along_x = (b[2] - b[0]) >= (b[3] - b[1])
        length = (b[2] - b[0]) if along_x else (b[3] - b[1])
        depth = (b[3] - b[1]) if along_x else (b[2] - b[0])
        hmax = b[5] - b[4]
        objs = []
        u = 0.15
        while u < length - 0.15:
            if rng.random() > density:
                u += rng.uniform(0.3, 0.9)
                continue
            # a run of upright books, occasionally a flat stack or a leaner
            mode = rng.random()
            if mode < 0.12 and u < length - 1.2:
                # flat stack
                nstack = rng.randint(2, 5)
                zc = b[4]
                w = rng.uniform(0.55, 0.85)
                for k in range(nstack):
                    t = rng.uniform(0.08, 0.2)
                    d = rng.uniform(0.5, min(0.8, depth - 0.1))
                    self._book_box(objs, b, along_x, u + rng.uniform(-0.03, 0.03), w, d, zc, zc + t, rng)
                    zc += t
                u += w + rng.uniform(0.1, 0.4)
                continue
            run = rng.randint(3, 14)
            for k in range(run):
                if u > length - 0.15:
                    break
                t = rng.uniform(0.08, 0.22)
                h = rng.uniform(0.58, min(0.95, hmax - 0.15))
                d = rng.uniform(0.45, min(0.75, depth - 0.1))
                lean = 0.0
                if k == run - 1 and rng.random() < 0.3:
                    lean = rng.uniform(6, 14)
                self._book_box(objs, b, along_x, u, t, d, b[4], b[4] + h, rng, lean)
                u += t + 0.005
            u += rng.uniform(0.05, 0.6)
        return objs

    def _book_box(self, objs, b, along_x, u, t, d, z0, z1, rng, lean=0.0):
        mat = self.mat(rng.choice(BOOK_MATS))
        if along_x:
            ob = box_ft(self.uid("book"), b[0] + u, b[1] + 0.05, b[0] + u + t, b[1] + 0.05 + d, z0, z1, mat, self.col)
            if lean:
                ob.rotation_euler = (0, math.radians(lean), 0)
        else:
            ob = box_ft(self.uid("book"), b[0] + 0.05, b[1] + u, b[0] + 0.05 + d, b[1] + u + t, z0, z1, mat, self.col)
            if lean:
                ob.rotation_euler = (math.radians(-lean), 0, 0)
        objs.append(ob)

    def gen_bookwall(self, e):
        """Shelving unit with back, sides, shelves, filled with books. b = [x0,y0,x1,y1,z0,z1], face = -x|+x|-y|+y."""
        b = e["b"]
        face = e.get("face", "-x")
        mat = self.mat(e.get("m", "walnut_h"))
        t = 1 * IN
        shelf = e.get("shelf_ft", 1.25)
        objs = []
        x0, y0, x1, y1, z0, z1 = b
        # back panel and sides
        if face in ("-x", "+x"):
            bx = (x1 - t, x1) if face == "-x" else (x0, x0 + t)
            objs.append(box_ft(self.uid("bw_back"), bx[0], y0, bx[1], y1, z0, z1, mat, self.col))
            objs.append(box_ft(self.uid("bw_side"), x0, y0, x1, y0 + t, z0, z1, mat, self.col))
            objs.append(box_ft(self.uid("bw_side"), x0, y1 - t, x1, y1, z0, z1, mat, self.col))
        else:
            by = (y1 - t, y1) if face == "-y" else (y0, y0 + t)
            objs.append(box_ft(self.uid("bw_back"), x0, by[0], x1, by[1], z0, z1, mat, self.col))
            objs.append(box_ft(self.uid("bw_side"), x0, y0, x0 + t, y1, z0, z1, mat, self.col))
            objs.append(box_ft(self.uid("bw_side"), x1 - t, y0, x1, y1, z0, z1, mat, self.col))
        # shelves, with a taller bottom bay
        zs = [z0 + 0.35]
        z = z0 + 0.35 + shelf * 1.3
        while z < z1 - 0.5:
            zs.append(z)
            z += shelf
        zs.append(z1 - t)
        for i, zz in enumerate(zs):
            objs.append(box_ft(self.uid("bw_shelf"), x0, y0, x1, y1, zz, zz + t, mat, self.col))
            if i + 1 < len(zs):
                cav_z0, cav_z1 = zz + t, zs[i + 1]
                if face in ("-x", "+x"):
                    cav = [x0 + (0 if face == "-x" else t), y0 + t, x1 - (t if face == "-x" else 0), y1 - t, cav_z0, cav_z1]
                    # books sit against the back: shift cavity so depth measured from back
                    if face == "-x":
                        cav = [x1 - t - 0.85, y0 + t, x1 - t, y1 - t, cav_z0, cav_z1]
                    else:
                        cav = [x0 + t, y0 + t, x0 + t + 0.85, y1 - t, cav_z0, cav_z1]
                else:
                    if face == "-y":
                        cav = [x0 + t, y1 - t - 0.85, x1 - t, y1 - t, cav_z0, cav_z1]
                    else:
                        cav = [x0 + t, y0 + t, x1 - t, y0 + t + 0.85, cav_z0, cav_z1]
                dens = e.get("density", 0.8) * (0.6 if i == 0 else 1.0)
                objs += self.gen_books({"b": cav, "density": dens, "seed": e.get("seed", 3) * 7 + i})
                # a few objects among the books: small vases/boxes
                if self.rng.random() < 0.5:
                    self._shelf_object(cav, objs)
        # toe kick / plinth
        return objs

    def _shelf_object(self, cav, objs):
        rng = self.rng
        x0, y0, x1, y1, z0, z1 = cav
        along_x = (x1 - x0) >= (y1 - y0)
        u = rng.uniform(0.2, 0.8)
        if along_x:
            cx, cy = x0 + u * (x1 - x0), (y0 + y1) / 2
        else:
            cx, cy = (x0 + x1) / 2, y0 + u * (y1 - y0)
        kind = rng.random()
        if kind < 0.5:
            objs.append(cylinder_ft(self.uid("vase"), (cx, cy, z0), rng.uniform(0.12, 0.2), rng.uniform(0.5, 0.9),
                                    self.mat(rng.choice(["ceramic_white", "teal", "mustard", "brass"])), self.col, 16))
        else:
            s = rng.uniform(0.3, 0.5)
            objs.append(box_ft(self.uid("box"), cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2, z0, z0 + s * 0.6,
                               self.mat(rng.choice(["oxblood", "olive", "black"])), self.col))

    def gen_frames(self, e):
        """Salon-style cluster of framed abstract art on a wall.
        wall: {"axis":"y","at":23.75,"face":"-x"} or {"axis":"x","at":..,"face":"+y"}; span [u0,u1]; zc center height."""
        wall = e["wall"]
        u0, u1 = e["span"]
        zc = e.get("zc", 5.2)
        count = e.get("count", 5)
        rng = random.Random(e.get("seed", self.rng.randint(0, 10 ** 6)))
        objs = []
        placed = []
        tries = 0
        while len(placed) < count and tries < 200:
            tries += 1
            w = rng.choice([1.0, 1.3, 1.6, 2.0, 2.4, 3.0])
            h = w * rng.choice([0.75, 1.0, 1.25, 1.4])
            if h > 3.2:
                h = 3.2
            cu = rng.uniform(u0 + w / 2, u1 - w / 2)
            cz = zc + rng.uniform(-1.4, 1.4)
            ok = True
            for (pu, pz, pw, ph) in placed:
                if abs(pu - cu) < (pw + w) / 2 + 0.25 and abs(pz - cz) < (ph + h) / 2 + 0.25:
                    ok = False
                    break
            if not ok:
                continue
            placed.append((cu, cz, w, h))
            fm = self.mat(rng.choice(["walnut_h", "brass", "black", "walnut_h"]))
            art = self.art_material(rng.randint(0, 999))
            ft = 0.04
            fd = 0.12
            face = wall["face"]
            at = wall["at"]
            # about half the pieces get a cream mat with a smaller image; the rest are full-bleed canvases
            matted = rng.random() < 0.55 and w >= 1.3
            mw = min(0.22, w * 0.14) if matted else 0.0
            paper = self.mat("paper")
            if wall["axis"] == "y":
                d0, d1 = (at - fd, at) if face == "-x" else (at, at + fd)
                frame = box_ft(self.uid("frame"), d0, cu - w / 2, d1, cu + w / 2, cz - h / 2, cz + h / 2, fm, self.col)
                c0, c1 = (d0 - 0.005, d0) if face == "-x" else (d1, d1 + 0.005)
                objs.append(frame)
                if matted:
                    objs.append(box_ft(self.uid("canvas_mat"), c0, cu - w / 2 + ft, c1, cu + w / 2 - ft, cz - h / 2 + ft, cz + h / 2 - ft, paper, self.col))
                    c0, c1 = (c0 - 0.003, c0) if face == "-x" else (c1, c1 + 0.003)
                objs.append(box_ft(self.uid("canvas"), c0, cu - w / 2 + ft + mw, c1, cu + w / 2 - ft - mw, cz - h / 2 + ft + mw, cz + h / 2 - ft - mw, art, self.col))
            else:
                d0, d1 = (at - fd, at) if face == "-y" else (at, at + fd)
                frame = box_ft(self.uid("frame"), cu - w / 2, d0, cu + w / 2, d1, cz - h / 2, cz + h / 2, fm, self.col)
                c0, c1 = (d0 - 0.005, d0) if face == "-y" else (d1, d1 + 0.005)
                objs.append(frame)
                if matted:
                    objs.append(box_ft(self.uid("canvas_mat"), cu - w / 2 + ft, c0, cu + w / 2 - ft, c1, cz - h / 2 + ft, cz + h / 2 - ft, paper, self.col))
                    c0, c1 = (c0 - 0.003, c0) if face == "-y" else (c1, c1 + 0.003)
                objs.append(box_ft(self.uid("canvas"), cu - w / 2 + ft + mw, c0, cu + w / 2 - ft - mw, c1, cz - h / 2 + ft + mw, cz + h / 2 - ft - mw, art, self.col))
        return objs

    def art_material(self, seed, emit=0.0):
        name = "art_%d" % seed if not emit else "art_%d_e" % seed
        if name in self.mats.specs:
            return self.mats.get(name)
        palettes = [
            [[0.72, 0.30, 0.10], [0.90, 0.85, 0.72], [0.08, 0.32, 0.36], [0.75, 0.58, 0.16]],
            [[0.32, 0.08, 0.09], [0.90, 0.85, 0.72], [0.15, 0.15, 0.14], [0.75, 0.58, 0.16]],
            [[0.10, 0.22, 0.20], [0.85, 0.78, 0.65], [0.72, 0.30, 0.10], [0.30, 0.45, 0.30]],
            [[0.15, 0.22, 0.40], [0.90, 0.85, 0.72], [0.80, 0.35, 0.15], [0.15, 0.15, 0.14]],
        ]
        self.mats.specs[name] = {"rgb": [0.9, 0.85, 0.72], "rough": 0.8,
                                 "overlay": {"type": "abstract_art", "size_ft": 1.0 + (seed % 5) * 0.4,
                                             "seed": seed, "palette": palettes[seed % len(palettes)]}}
        if emit:
            self.mats.specs[name]["emit"] = emit
        return self.mats.get(name)

    def gen_sputnik(self, e):
        c = e["pos"]
        arms = e.get("arms", 14)
        r = e.get("radius", 1.6)
        brass = self.mat("brass")
        glow = self.mat("lamp_glow")
        objs = [sphere_ft(self.uid("sput_hub"), c, 0.22, brass, self.col)]
        ceil = e.get("ceil_z", c[2] + 2.3)
        objs.append(cylinder_ft(self.uid("sput_stem"), (c[0], c[1], c[2]), 0.03, ceil - c[2], brass, self.col, 8))
        rng = random.Random(e.get("seed", 11))
        for i in range(arms):
            # fibonacci sphere directions
            k = i + 0.5
            phi = math.acos(1 - 2 * k / arms)
            theta = math.pi * (1 + 5 ** 0.5) * k
            d = Vector((math.cos(theta) * math.sin(phi), math.sin(theta) * math.sin(phi), math.cos(phi)))
            L = r * rng.uniform(0.75, 1.0)
            p1 = (c[0] + d.x * L, c[1] + d.y * L, c[2] + d.z * L)
            objs.append(beam_between(self.uid("sput_rod"), c, p1, 0.04, 0.04, brass, self.col))
            objs.append(sphere_ft(self.uid("sput_bulb"), p1, 0.11, glow, self.col, 12, 8))
        self.light(type="point", pos=c, watts=e.get("watts", 90), radius=0.6, name="sputnik")
        return objs

    def gen_globe_pendant(self, e):
        p = e["pos"]
        r = e.get("radius", 0.5)
        drop = e.get("drop", 2.5)
        brass = self.mat("brass")
        shade = self.mat("lamp_shade")
        objs = [cylinder_ft(self.uid("pend_cord"), (p[0], p[1], p[2]), 0.015, drop, self.mat("black"), self.col, 6),
                cylinder_ft(self.uid("pend_canopy"), (p[0], p[1], p[2] + drop - 0.08), 0.2, 0.08, brass, self.col, 16),
                cylinder_ft(self.uid("pend_cap"), (p[0], p[1], p[2] - 0.15), 0.18, 0.15, brass, self.col, 16),
                sphere_ft(self.uid("pend_globe"), (p[0], p[1], p[2] - r), r, shade, self.col)]
        self.light(type="point", pos=(p[0], p[1], p[2] - r), watts=e.get("watts", 35), radius=r * 0.8, name="pendant")
        return objs

    def gen_table_lamp(self, e):
        p = e["pos"]
        h = e.get("height", 1.9)
        base_m = self.mat(e.get("base_m", "ceramic_white"))
        shade = self.mat("lamp_shade")
        objs = [cylinder_ft(self.uid("lamp_base"), p, e.get("base_r", 0.28), h * 0.5, base_m, self.col, 20),
                cylinder_ft(self.uid("lamp_stem"), (p[0], p[1], p[2] + h * 0.5), 0.03, h * 0.15, self.mat("brass"), self.col, 8)]
        sh = cylinder_ft(self.uid("lamp_shade"), (p[0], p[1], p[2] + h * 0.6), e.get("shade_r", 0.55), h * 0.4, shade, self.col, 24)
        sh.scale = (1, 1, 1)
        objs.append(sh)
        self.light(type="point", pos=(p[0], p[1], p[2] + h * 0.72), watts=e.get("watts", 30), radius=0.25, name="table_lamp")
        return objs

    def gen_arc_lamp(self, e):
        p = e["pos"]
        R = e.get("reach", 6.0)
        H = e.get("height", 7.2)
        brass = self.mat("brass")
        objs = [cylinder_ft(self.uid("arc_base"), p, 0.7, 0.25, self.mat("stone"), self.col, 24)]
        rot = math.radians(e.get("rot_z", 0))
        pts = []
        segs = 14
        for i in range(segs + 1):
            t = i / segs
            ang = t * math.pi / 2
            lx = R * math.sin(ang)
            lz = 0.25 + (H - 0.25) * (1 - math.cos(ang)) if False else 0.25 + (H - 0.25) * math.sin(ang * 1.0)
            # simple quarter-ellipse: rises then reaches out
            lx = R * (1 - math.cos(ang))
            lz = 0.25 + (H - 0.25) * math.sin(ang)
            pts.append((p[0] + lx * math.cos(rot), p[1] + lx * math.sin(rot), p[2] + lz))
        for a, b in zip(pts[:-1], pts[1:]):
            objs.append(beam_between(self.uid("arc_seg"), a, b, 0.07, 0.07, brass, self.col))
        end = pts[-1]
        dome = sphere_ft(self.uid("arc_shade"), (end[0], end[1], end[2] - 0.35), 0.75, brass, self.col)
        dome.scale = (1, 1, 0.75)
        inner = sphere_ft(self.uid("arc_glow"), (end[0], end[1], end[2] - 0.5), 0.55, self.mat("lamp_shade"), self.col, 16, 8)
        inner.scale = (1, 1, 0.6)
        objs += [dome, inner]
        self.light(type="spot", pos=(end[0], end[1], end[2] - 0.7), aim=(end[0], end[1], p[2]), watts=e.get("watts", 60), angle=95, blend=0.9, name="arc_lamp")
        return objs

    def gen_mushroom_lamp(self, e):
        p = e["pos"]
        h = e.get("height", 4.6)
        col_m = self.mat(e.get("m", "orange"))
        objs = [cylinder_ft(self.uid("mush_base"), p, 0.45, 0.12, col_m, self.col, 24),
                cylinder_ft(self.uid("mush_stem"), (p[0], p[1], p[2] + 0.12), 0.1, h - 0.9, self.mat("brass"), self.col, 12)]
        cap = sphere_ft(self.uid("mush_cap"), (p[0], p[1], p[2] + h - 0.6), 1.1, col_m, self.col)
        cap.scale = (1, 1, 0.55)
        glow = sphere_ft(self.uid("mush_glow"), (p[0], p[1], p[2] + h - 0.72), 0.95, self.mat("lamp_shade"), self.col, 16, 8)
        glow.scale = (1, 1, 0.45)
        objs += [cap, glow]
        self.light(type="point", pos=(p[0], p[1], p[2] + h - 0.9), watts=e.get("watts", 40), radius=0.4, name="mushroom")
        return objs

    def gen_sofa(self, e):
        """Low mid-century sofa. pos = center of the front-left... use center bottom; length along local X."""
        p = e["pos"]
        L = e.get("length", 8.0)
        D = e.get("depth", 3.1)
        rot = e.get("rot_z", 0)
        fab = self.mat(e.get("m", "orange"))
        wood = self.mat("walnut_h")
        objs = []

        def part(name, x0, y0, x1, y1, z0, z1, mat):
            ob = box_local(self.uid(name), (0, 0, 0), (x1 - x0, y1 - y0, z1 - z0), 0, mat, self.col)
            ob.data.transform(Matrix.Translation((m(x0 - L / 2), m(y0 - D / 2), m(z0))))
            ob.location = (m(p[0]), m(p[1]), m(p[2]))
            ob.rotation_euler = (0, 0, math.radians(rot))
            objs.append(ob)

        seat_h = 1.35
        part("sofa_frame", 0, 0, L, D, 0.55, seat_h - 0.35, wood)
        part("sofa_base", 0.15, 0.15, L - 0.15, D - 0.15, seat_h - 0.35, seat_h - 0.05, fab)
        nc = 3 if L > 6.5 else 2
        cw = (L - 0.5) / nc
        for i in range(nc):
            xa, xb = 0.25 + i * cw + 0.03, 0.25 + (i + 1) * cw - 0.03
            objs.append(sg.slab(self.uid("sg_sofa_cushion"), ((xa + xb) / 2 - L / 2, (D - 0.55) / 2 - D / 2, seat_h + 0.185), (xb - xa, D - 0.95, 0.47),
                                fab, self.col, origin_ft=p, rot_z_deg=rot, seed=i, puff=0.18, sag=0.05))
            objs.append(sg.slab(self.uid("sg_sofa_back"), ((xa + xb) / 2 - L / 2, D - 0.57 - D / 2, seat_h + 0.68), (xb - xa, 1.3, 0.42),
                                fab, self.col, rot=(math.radians(80), 0, 0), origin_ft=p, rot_z_deg=rot, seed=10 + i, puff=0.3))
        part("sofa_arm", 0, 0.2, 0.25, D - 0.3, seat_h - 0.35, seat_h + 0.65, wood)
        part("sofa_arm", L - 0.25, 0.2, L, D - 0.3, seat_h - 0.35, seat_h + 0.65, wood)
        part("sofa_backrail", 0, D - 0.4, L, D - 0.2, seat_h - 0.35, seat_h + 1.4, wood)
        for lx in (0.4, L - 0.4):
            for ly in (0.4, D - 0.5):
                part("sofa_leg", lx - 0.07, ly - 0.07, lx + 0.07, ly + 0.07, 0, 0.55, wood)
        return objs

    def gen_credenza(self, e):
        p = e["pos"]
        L, D, H = e.get("length", 6.0), e.get("depth", 1.5), e.get("height", 2.3)
        rot = e.get("rot_z", 0)
        wood = self.mat("walnut_h")
        objs = []

        def part(name, x0, y0, x1, y1, z0, z1, mat):
            ob = box_local(self.uid(name), (0, 0, 0), (x1 - x0, y1 - y0, z1 - z0), 0, mat, self.col)
            ob.data.transform(Matrix.Translation((m(x0 - L / 2), m(y0 - D / 2), m(z0))))
            ob.location = (m(p[0]), m(p[1]), m(p[2]))
            ob.rotation_euler = (0, 0, math.radians(rot))
            objs.append(ob)
        part("cred_body", 0, 0, L, D, 0.7, H, wood)
        # door reveals
        nd = 3
        for i in range(1, nd):
            part("cred_reveal", i * L / nd - 0.01, -0.01, i * L / nd + 0.01, 0.02, 0.75, H - 0.05, self.mat("black"))
        for lx in (0.3, L - 0.3):
            for ly in (0.25, D - 0.25):
                part("cred_leg", lx - 0.06, ly - 0.06, lx + 0.06, ly + 0.06, 0, 0.7, wood)
        if e.get("turntable", True):
            part("tt_plinth", L * 0.15, 0.2, L * 0.15 + 1.5, D - 0.2, H, H + 0.3, wood)
            tt = cylinder_ft(self.uid("tt_platter"), (0, 0, 0), 0.5, 0.05, self.mat("black"), self.col, 32)
            tt.location = (m(p[0]), m(p[1]), m(p[2]))
            tt.data.transform(Matrix.Translation((m(L * 0.15 + 0.7 - L / 2), m(D / 2 - D / 2), m(H + 0.3))))
            tt.rotation_euler = (0, 0, math.radians(rot))
            objs.append(tt)
            part("tt_arm", L * 0.15 + 1.25, D - 0.45, L * 0.15 + 1.32, D - 0.2, H + 0.3, H + 0.4, self.mat("chrome"))
        return objs

    def gen_coffee_table(self, e):
        p = e["pos"]
        L, D, H = e.get("length", 4.2), e.get("depth", 2.0), e.get("height", 1.3)
        wood = self.mat(e.get("m", "walnut_h"))
        objs = [box_centered(self.uid("ct_top"), (p[0], p[1], p[2] + H - 0.1), (L, D, 0.1), e.get("rot_z", 0), wood, self.col)]
        rot = math.radians(e.get("rot_z", 0))
        for sx in (-1, 1):
            for sy in (-1, 1):
                lx, ly = sx * (L / 2 - 0.3), sy * (D / 2 - 0.25)
                wx = p[0] + lx * math.cos(rot) - ly * math.sin(rot)
                wy = p[1] + lx * math.sin(rot) + ly * math.cos(rot)
                objs.append(cylinder_ft(self.uid("ct_leg"), (wx, wy, p[2]), 0.06, H - 0.1, wood, self.col, 10))
        # a few things on top: a book stack and a bowl
        objs.append(box_ft(self.uid("ct_book"), p[0] - 0.7, p[1] - 0.45, p[0] + 0.1, p[1] + 0.15, p[2] + H, p[2] + H + 0.12, self.mat("book_c"), self.col))
        objs.append(box_ft(self.uid("ct_book"), p[0] - 0.65, p[1] - 0.4, p[0] + 0.0, p[1] + 0.1, p[2] + H + 0.12, p[2] + H + 0.2, self.mat("book_e"), self.col))
        bowl = sphere_ft(self.uid("ct_bowl"), (p[0] + 0.9, p[1] + 0.2, p[2] + H + 0.18), 0.45, self.mat("teal"), self.col)
        bowl.scale = (1, 1, 0.4)
        objs.append(bowl)
        return objs

    def gen_tv_wall(self, e):
        """Frame TV among art on a wall. wall spec like frames; tv centered at (u, z)."""
        wall = e["wall"]
        u, zc = e["u"], e.get("zc", 4.8)
        w, h = e.get("w", 5.4), e.get("h", 3.1)
        at, face = wall["at"], wall["face"]
        objs = []
        screen_m = self.mat("screen")
        if e.get("on"):
            screen_m = self.art_material(e.get("seed", 88), emit=0.2)
            self.light(type="area", pos=(u, at + (-0.3 if face == "-y" else 0.3), zc) if wall["axis"] == "x" else (at + (-0.3 if face == "-x" else 0.3), u, zc),
                       size=w * 0.8, size_y=h * 0.8, shape="RECTANGLE", watts=e.get("watts", 25), kelvin=5500,
                       # area lights emit along local -Z: -90 about X -> -Y, +90 about X -> +Y, +90 about Y -> -X, -90 about Y -> +X
                       rot=(math.radians(-90 if face == "-y" else 90), 0, 0) if wall["axis"] == "x" else (0, math.radians(90 if face == "-x" else -90), 0), name="tv")
        if wall["axis"] == "y":
            d0, d1 = (at - 0.1, at) if face == "-x" else (at, at + 0.1)
            objs.append(box_ft(self.uid("tv_frame"), d0, u - w / 2, d1, u + w / 2, zc - h / 2, zc + h / 2, self.mat("walnut_h"), self.col))
            c0, c1 = (d0 - 0.004, d0) if face == "-x" else (d1, d1 + 0.004)
            objs.append(box_ft(self.uid("tv_screen"), c0, u - w / 2 + 0.06, c1, u + w / 2 - 0.06, zc - h / 2 + 0.06, zc + h / 2 - 0.06, screen_m, self.col))
        else:
            d0, d1 = (at - 0.1, at) if face == "-y" else (at, at + 0.1)
            objs.append(box_ft(self.uid("tv_frame"), u - w / 2, d0, u + w / 2, d1, zc - h / 2, zc + h / 2, self.mat("walnut_h"), self.col))
            c0, c1 = (d0 - 0.004, d0) if face == "-y" else (d1, d1 + 0.004)
            objs.append(box_ft(self.uid("tv_screen"), u - w / 2 + 0.06, c0, u + w / 2 - 0.06, c1, zc - h / 2 + 0.06, zc + h / 2 - 0.06, screen_m, self.col))
        return objs

    def gen_cove(self, e):
        """Warm LED strip around the inside top of a pit (under the lip): emissive strips plus area lights."""
        x0, y0, x1, y1 = e["b"]
        z = e["z"]
        glow = self.mat("lamp_glow")
        t = 0.25
        objs = []
        edges = [((x0 + t, y0 + t + 0.02), (x1 - t, y0 + t + 0.06), "x"), ((x0 + t, y1 - t - 0.06), (x1 - t, y1 - t - 0.02), "x"),
                 ((x0 + t + 0.02, y0 + t), (x0 + t + 0.06, y1 - t), "y"), ((x1 - t - 0.06, y0 + t), (x1 - t - 0.02, y1 - t), "y")]
        for (a, b, ax) in edges:
            objs.append(box_ft(self.uid("cove"), a[0], a[1], b[0], b[1], z - 0.12, z - 0.08, glow, self.col))
            cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            L = (b[0] - a[0]) if ax == "x" else (b[1] - a[1])
            self.light(type="area", pos=(cx, cy, z - 0.15), size=L if ax == "x" else 0.1, size_y=0.1 if ax == "x" else L,
                       shape="RECTANGLE", watts=e.get("watts", 15), kelvin=2200, rot=(0, 0, 0), name="cove")
        return objs

    def gen_fire(self, e):
        """Fire in a hearth: logs, ember bed, and layered ellipsoid flames with graded emission."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        objs = []
        rng = random.Random(e.get("seed", 3))
        cx = (x0 + x1) / 2
        # andirons and logs along Y
        for i, (dy, dz, r) in enumerate([(0.25, 0, 0.16), (0.55, 0, 0.15), (0.8, 0, 0.14), (0.4, 0.27, 0.13), (0.65, 0.26, 0.12)]):
            objs.append(cylinder_ft(self.uid("log"), (cx, y0 + dy * (y1 - y0), z0 + 0.12 + dz), r, (x1 - x0) * 0.85, self.mat("walnut"), self.col, 10, axis="X"))
        objs.append(box_ft(self.uid("embers"), x0 + 0.05, y0 + 0.1, x1 - 0.05, y1 - 0.1, z0 + 0.01, z0 + 0.1, self.mat("embers"), self.col))
        # flames: outer orange ellipsoids, inner yellow cores
        for i in range(7):
            fy = y0 + 0.2 + rng.uniform(0, 1) * (y1 - y0 - 0.4)
            h = rng.uniform(0.6, 1.3)
            fl = sphere_ft(self.uid("flame"), (cx + rng.uniform(-0.1, 0.1), fy, z0 + 0.3 + h * 0.45), 0.2, self.mat("fire"), self.col, 12, 8)
            fl.scale = (rng.uniform(0.6, 1.0), rng.uniform(0.8, 1.3), h / 0.4)
            fl.rotation_euler = (math.radians(rng.uniform(-12, 12)), math.radians(rng.uniform(-8, 8)), 0)
            objs.append(fl)
            if i % 2 == 0:
                core = sphere_ft(self.uid("flame_core"), (cx, fy, z0 + 0.25 + h * 0.25), 0.1, self.mat("fire_core"), self.col, 10, 6)
                core.scale = (0.7, 0.9, h / 0.4 * 0.5)
                objs.append(core)
        self.light(type="point", pos=(cx + 0.25, (y0 + y1) / 2, z0 + 0.8), watts=e.get("watts", 60), kelvin=1900, radius=0.5, name="fire")
        return objs

    def gen_ceiling_panels(self, e):
        """Grid of flush ceiling light panels (gym). b = [x0,y0,x1,y1] area, z = ceiling underside."""
        x0, y0, x1, y1 = e["b"]
        z = e["z"]
        cols, rows = e.get("cols", 2), e.get("rows", 3)
        sw, sl = e.get("size", [2, 4])
        objs = []
        for i in range(cols):
            for j in range(rows):
                cx = x0 + (i + 0.5) * (x1 - x0) / cols
                cy = y0 + (j + 0.5) * (y1 - y0) / rows
                objs.append(box_ft(self.uid("panel"), cx - sw / 2, cy - sl / 2, cx + sw / 2, cy + sl / 2, z - 0.06, z - 0.01, self.mat("lamp_shade"), self.col))
                self.light(type="area", pos=(cx, cy, z - 0.1), size=sw, size_y=sl, shape="RECTANGLE", watts=e.get("watts", 40), kelvin=e.get("kelvin", 3000), rot=(0, 0, 0), name="panel")
        return objs

    def gen_plant(self, e):
        p = e["pos"]
        h = e.get("height", 4.0)
        objs = [cylinder_ft(self.uid("pot"), p, h * 0.12, h * 0.25, self.mat(e.get("pot_m", "terrazzo")), self.col, 20)]
        rng = random.Random(e.get("seed", 5))
        leaf = self.mat("olive")
        for i in range(int(6 + h * 2)):
            ang = rng.uniform(0, 2 * math.pi)
            tilt = rng.uniform(20, 70)
            L = rng.uniform(h * 0.35, h * 0.7)
            base = (p[0], p[1], p[2] + h * 0.25)
            tip = (p[0] + math.cos(ang) * L * math.sin(math.radians(tilt)), p[1] + math.sin(ang) * L * math.sin(math.radians(tilt)),
                   base[2] + L * math.cos(math.radians(tilt)))
            stem = beam_between(self.uid("stem"), base, tip, 0.03, 0.03, leaf, self.col)
            lf = sphere_ft(self.uid("leaf"), tip, L * 0.28, leaf, self.col, 10, 6)
            lf.scale = (1, 0.5, 0.15)
            lf.rotation_euler = (0, math.radians(tilt), ang)
            objs += [stem, lf]
        return objs

    def gen_cushions(self, e):
        """Throw pillows on a surface: b = [x0,y0,x1,y1] surface, z = top of surface, back = the side they lean
        against ("-y", "+y", "-x", "+x"; None = all flat). Pillows take evenly spaced slots along the back with a
        little jitter, so they never pile into each other; about half lean, the rest lie flat in front."""
        b = e["b"]
        z = e["z"]
        n = e.get("count", 5)
        rng = random.Random(e.get("seed", 9))
        mats = e.get("mats", ["teal", "mustard", "orange", "oxblood", "rug_cream"])
        back = e.get("back")
        t = 0.38
        along_x = back in ("-y", "+y", None)          # slots run along X when the back is a Y side
        length = (b[2] - b[0]) if along_x else (b[3] - b[1])
        slot = length / max(n, 1)
        objs = []
        for i in range(n):
            s_ = min(rng.uniform(1.2, 1.7), slot * 0.95)
            d = s_ * rng.uniform(0.85, 1.0)
            u = (b[0] if along_x else b[1]) + slot * (i + 0.5) + rng.uniform(-0.08, 0.08) * slot
            lean = back is not None and (i % 2 == 0 or rng.random() < 0.3)
            mat = self.mat(mats[i % len(mats)])
            seed = e.get("seed", 9) * 31 + i
            if lean:
                # leaning back against the backrest: bottom edge forward on the seat, top edge on the back,
                # puffy face toward the room (the pillow's +Z)
                a = math.radians(rng.uniform(62, 74))
                yaw = math.radians(rng.uniform(-7, 7))
                zc = z + (d / 2) * math.sin(a) + (t / 2) * math.cos(a) - 0.02
                gap = (d / 2) * math.cos(a) + (t / 2) * math.sin(a) + 0.03
                if back == "-y":
                    cx, cy, rot, size = u, b[1] + gap, (-a, 0, yaw), (s_, d, t)
                elif back == "+y":
                    cx, cy, rot, size = u, b[3] - gap, (a, 0, yaw), (s_, d, t)
                elif back == "-x":
                    cx, cy, rot, size = b[0] + gap, u, (0, a, yaw), (d, s_, t)
                else:
                    cx, cy, rot, size = b[2] - gap, u, (0, -a, yaw), (d, s_, t)
                ob = sg.pillow(self.uid("sg_pillow"), (cx, cy, zc), size, mat, self.col, rot=rot, seed=seed)
            else:
                # flat, a little forward of the back so it does not sit under a leaning neighbour
                if along_x:
                    cy = (b[1] + d / 2 + 0.55) if back == "-y" else ((b[3] - d / 2 - 0.55) if back == "+y" else rng.uniform(b[1] + d / 2, b[3] - d / 2))
                    cx = u
                else:
                    cx = (b[0] + d / 2 + 0.55) if back == "-x" else (b[2] - d / 2 - 0.55)
                    cy = u
                ob = sg.pillow(self.uid("sg_pillow"), (cx, cy, z + t * 0.36), (s_, d, t), mat, self.col,
                               rot=(0, 0, math.radians(rng.uniform(-25, 25))), seed=seed, dent=0.12)
            objs.append(ob)
        return objs

    def gen_bed(self, e):
        p = e["pos"]  # center bottom of the mattress footprint, head toward +Y (rot_z 0)
        W, L = e.get("width", 6.5), e.get("length", 7.0)
        rot = e.get("rot_z", 0)
        wood = self.mat("walnut_h")
        objs = []

        def part(name, x0, y0, x1, y1, z0, z1, mat):
            ob = box_local(self.uid(name), (0, 0, 0), (x1 - x0, y1 - y0, z1 - z0), 0, mat, self.col)
            ob.data.transform(Matrix.Translation((m(x0 - W / 2), m(y0 - L / 2), m(z0))))
            ob.location = (m(p[0]), m(p[1]), m(p[2]))
            ob.rotation_euler = (0, 0, math.radians(rot))
            objs.append(ob)
        part("bed_platform", -0.6, -0.3, W + 0.6, L + 0.2, 0.35, 1.0, wood)
        part("bed_plinth", 0.3, 0.6, W - 0.3, L - 0.3, 0, 0.35, self.mat("black"))
        part("bed_mattress", 0, 0, W, L, 1.0, 1.75, self.mat("linen"))
        part("bed_duvet", -0.25, -0.4, W + 0.25, L - 2.2, 1.75, 2.15, self.mat(e.get("duvet_m", "rug_cream")))
        part("bed_throw", W - 3.5, -1.3, W + 0.6, 1.6, 2.15, 2.4, self.mat(e.get("throw_m", "mustard")))
        for i, x in enumerate((0.3, W / 2 + 0.15)):
            part("bed_pillow", x, L - 2.0, x + W / 2 - 0.45, L - 0.2, 1.75, 2.35, self.mat("linen"))
        part("bed_headboard", -0.6, L + 0.2, W + 0.6, L + 0.5, 0, 3.8, wood)
        part("bed_headpad", -0.4, L + 0.05, W + 0.4, L + 0.2, 1.8, 3.4, self.mat(e.get("headpad_m", "leather")))
        # slippers
        part("slipper", W + 0.9, 1.0, W + 1.35, 1.9, 0, 0.12, self.mat("mustard"))
        part("slipper", W + 1.45, 0.9, W + 1.9, 1.85, 0, 0.12, self.mat("mustard"))
        return objs

    def gen_nightstand(self, e):
        p = e["pos"]
        wood = self.mat("walnut_h")
        objs = [box_centered(self.uid("ns_body"), (p[0], p[1], p[2] + 0.6), (1.8, 1.5, 1.4), e.get("rot_z", 0), wood, self.col)]
        for sx in (-1, 1):
            for sy in (-1, 1):
                objs.append(cylinder_ft(self.uid("ns_leg"), (p[0] + sx * 0.7, p[1] + sy * 0.55, p[2]), 0.05, 0.6, wood, self.col, 8))
        objs += self.gen_table_lamp({"pos": (p[0], p[1], p[2] + 2.0), "height": 1.7, "base_r": 0.22, "shade_r": 0.45, "watts": 25})
        return objs

    def gen_cabinet(self, e):
        """Flat-front cabinet box with door reveals. b = [x0,y0,x1,y1,z0,z1], face direction for reveals."""
        b = e["b"]
        mat = self.mat(e.get("m", "walnut_h"))
        objs = [box_ft(self.uid("cab"), *b, mat=mat, collection=self.col)]
        nd = e.get("doors", 3)
        face = e.get("face", "-y")
        x0, y0, x1, y1, z0, z1 = b
        dark = self.mat("black")
        if face in ("-y", "+y"):
            fy0, fy1 = (y0 - 0.01, y0 + 0.005) if face == "-y" else (y1 - 0.005, y1 + 0.01)
            for i in range(1, nd):
                u = x0 + i * (x1 - x0) / nd
                objs.append(box_ft(self.uid("reveal"), u - 0.01, fy0, u + 0.01, fy1, z0 + 0.05, z1 - 0.05, dark, self.col))
            if e.get("hreveal"):
                objs.append(box_ft(self.uid("reveal"), x0 + 0.05, fy0, x1 - 0.05, fy1, e["hreveal"] - 0.01, e["hreveal"] + 0.01, dark, self.col))
        else:
            fx0, fx1 = (x0 - 0.01, x0 + 0.005) if face == "-x" else (x1 - 0.005, x1 + 0.01)
            for i in range(1, nd):
                u = y0 + i * (y1 - y0) / nd
                objs.append(box_ft(self.uid("reveal"), fx0, u - 0.01, fx1, u + 0.01, z0 + 0.05, z1 - 0.05, dark, self.col))
        return objs

    def gen_kitchen(self, e):
        """Kitchen back wall package: counter top, backsplash, uppers, hood, cooktop, oven stack, open shelves."""
        objs = []
        counter = bpy.data.objects.get("feat_kitchen_back_counter")
        cb = counter["bounds_ft"] if counter else [0.5, 14.5, 17.5, 16.5, 0, 3]
        x0, y0, x1, y1, z0, z1 = cb
        wall_y = y0  # wall face at south side of the counter
        stone = self.mat("stone")
        wood = self.mat("walnut_h")
        # counter top slab
        objs.append(box_ft(self.uid("ktop"), x0 - 0.05, y0, x1 + 0.05, y1 + 0.1, z1, z1 + 0.12, stone, self.col))
        # door reveals on lowers
        for i in range(1, 9):
            u = x0 + i * (x1 - x0) / 9
            objs.append(box_ft(self.uid("reveal"), u - 0.01, y1 - 0.005, u + 0.01, y1 + 0.01, z0 + 0.4, z1 - 0.05, self.mat("black"), self.col))
        objs.append(box_ft(self.uid("toekick"), x0, y0, x1, y1 - 0.25, z0, z0 + 0.35, self.mat("black"), self.col))
        # backsplash: tile between counter and uppers
        objs.append(box_ft(self.uid("backsplash"), x0, wall_y - 0.02, x1, wall_y + 0.03, z1 + 0.12, 4.9, self.mat("backsplash"), self.col))
        # uppers: two banks flanking the hood
        hood_x0, hood_x1 = 7.0, 10.0
        for ux0, ux1, nd in ((x0, hood_x0 - 0.1, 4), (hood_x1 + 0.1, 13.0, 2)):
            objs += self.gen_cabinet({"b": [ux0, wall_y, ux1, wall_y + 1.15, 4.9, 8.4], "doors": nd, "face": "+y"})
        # open shelves on the right with ceramics
        for zz in (5.4, 6.7):
            objs.append(box_ft(self.uid("shelf"), 13.2, wall_y, x1, wall_y + 0.95, zz, zz + 0.1, wood, self.col))
        rng = random.Random(4)
        for i in range(7):
            zz = 5.5 if i < 4 else 6.8
            xx = 13.5 + (i % 4) * 1.0 + rng.uniform(-0.1, 0.1)
            objs.append(cylinder_ft(self.uid("ceramic"), (xx, wall_y + 0.45, zz), rng.uniform(0.15, 0.3), rng.uniform(0.35, 0.8),
                                    self.mat(rng.choice(["ceramic_white", "teal", "mustard", "terrazzo"])), self.col, 16))
        # hood: steel canopy + duct
        objs.append(box_ft(self.uid("hood"), hood_x0, wall_y, hood_x1, wall_y + 1.6, 5.6, 6.2, self.mat("steel"), self.col))
        objs.append(box_ft(self.uid("duct"), hood_x0 + 0.6, wall_y, hood_x1 - 0.6, wall_y + 1.0, 6.2, 9.5, self.mat("steel"), self.col))
        # cooktop
        objs.append(box_ft(self.uid("cooktop"), hood_x0 + 0.1, y0 + 0.3, hood_x1 - 0.1, y1 - 0.2, z1 + 0.12, z1 + 0.16, self.mat("screen"), self.col))
        # wall oven stack (tall walnut box) at the far right end of the run
        objs.append(box_ft(self.uid("oven_tower"), 15.0, wall_y, x1, wall_y + 2.0, z0, 8.4, wood, self.col))
        objs.append(box_ft(self.uid("oven_door"), 15.15, wall_y + 2.0, x1 - 0.15, wall_y + 2.02, 2.8, 5.2, self.mat("screen"), self.col))
        objs.append(box_ft(self.uid("oven_handle"), 15.3, wall_y + 2.02, x1 - 0.3, wall_y + 2.08, 5.0, 5.08, self.mat("brass"), self.col))
        # under-cabinet light strip
        self.light(type="area", pos=(x0 + (hood_x0 - x0) / 2, wall_y + 1.0, 4.85), size=hood_x0 - x0 - 0.5, size_y=0.15, shape="RECTANGLE", watts=12, rot=(0, 0, 0), name="undercab")
        self.light(type="area", pos=((hood_x1 + 13.0) / 2, wall_y + 1.0, 4.85), size=2.5, size_y=0.15, shape="RECTANGLE", watts=6, rot=(0, 0, 0), name="undercab")
        # small appliances on the counter: stand mixer, cake stand with dome
        mx = 2.0
        objs.append(box_ft(self.uid("mixer_base"), mx, y0 + 0.5, mx + 0.75, y0 + 1.5, z1 + 0.12, z1 + 0.5, self.mat("teal"), self.col))
        objs.append(box_ft(self.uid("mixer_post"), mx + 0.5, y0 + 0.9, mx + 0.75, y0 + 1.1, z1 + 0.5, z1 + 1.25, self.mat("teal"), self.col))
        objs.append(box_ft(self.uid("mixer_head"), mx - 0.05, y0 + 0.7, mx + 0.75, y0 + 1.3, z1 + 1.05, z1 + 1.4, self.mat("teal"), self.col))
        bowl = sphere_ft(self.uid("mixer_bowl"), (mx + 0.25, y0 + 1.0, z1 + 0.75), 0.35, self.mat("chrome"), self.col)
        bowl.scale = (1, 1, 0.8)
        objs.append(bowl)
        return objs

    def gen_island_table(self, e):
        """Table end of the island: walnut top slab cantilevered off the island with one pedestal."""
        x0, x1 = e.get("x", [10.0, 15.0])
        y0, y1 = e.get("y", [19.0, 22.5])
        z = e.get("z", 0)
        H = e.get("height", 2.5)
        wood = self.mat("walnut_h")
        objs = [box_ft(self.uid("tbl_top"), x0, y0, x1, y1, z + H - 0.15, z + H, wood, self.col),
                box_ft(self.uid("tbl_apron"), x0, y0 + 0.3, x1 - 0.2, y1 - 0.3, z + H - 0.4, z + H - 0.15, wood, self.col),
                box_ft(self.uid("tbl_ped"), x1 - 0.7, (y0 + y1) / 2 - 0.4, x1 - 0.3, (y0 + y1) / 2 + 0.4, z, z + H - 0.4, wood, self.col),
                box_ft(self.uid("tbl_foot"), x1 - 1.0, (y0 + y1) / 2 - 1.2, x1 - 0.1, (y0 + y1) / 2 + 1.2, z, z + 0.12, wood, self.col)]
        # fruit bowl
        bowl = sphere_ft(self.uid("bowl"), ((x0 + x1) / 2, (y0 + y1) / 2, z + H + 0.2), 0.6, self.mat("ceramic_white"), self.col)
        bowl.scale = (1, 1, 0.4)
        objs.append(bowl)
        return objs

    def gen_runner(self, e):
        return self.gen_rug(dict(e, m=e.get("m", "runner"), thick=0.04))

    def gen_hooks(self, e):
        """Walnut rail with brass hooks. wall: axis/at/face; span; z."""
        wall = e["wall"]
        u0, u1 = e["span"]
        z = e.get("z", 5.5)
        at, face = wall["at"], wall["face"]
        objs = []
        n = e.get("count", 5)
        if wall["axis"] == "y":
            d0, d1 = (at - 0.08, at) if face == "-x" else (at, at + 0.08)
            objs.append(box_ft(self.uid("rail"), d0, u0, d1, u1, z - 0.15, z + 0.15, self.mat("walnut_h"), self.col))
            for i in range(n):
                u = u0 + (i + 0.5) * (u1 - u0) / n
                h0, h1 = (at - 0.35, at - 0.08) if face == "-x" else (at + 0.08, at + 0.35)
                objs.append(box_ft(self.uid("hook"), h0, u - 0.03, h1, u + 0.03, z - 0.03, z + 0.03, self.mat("brass"), self.col))
        else:
            d0, d1 = (at - 0.08, at) if face == "-y" else (at, at + 0.08)
            objs.append(box_ft(self.uid("rail"), u0, d0, u1, d1, z - 0.15, z + 0.15, self.mat("walnut_h"), self.col))
            for i in range(n):
                u = u0 + (i + 0.5) * (u1 - u0) / n
                h0, h1 = (at - 0.35, at - 0.08) if face == "-y" else (at + 0.08, at + 0.35)
                objs.append(box_ft(self.uid("hook"), u - 0.03, h0, u + 0.03, h1, z - 0.03, z + 0.03, self.mat("brass"), self.col))
        # a jacket on one hook
        if e.get("jacket", True):
            u = u0 + 1.5 * (u1 - u0) / n
            # a real coat shape hanging from the hook, back to the wall
            if wall["axis"] == "y":
                fd = (-1, 0) if face == "-x" else (1, 0)
                top = (at + fd[0] * 0.28, u, z - 0.02)
            else:
                fd = (0, -1) if face == "-y" else (0, 1)
                top = (u, at + fd[1] * 0.28, z - 0.02)
            objs += sg.garment(self.uid("sg_jacket"), top, fd, 1.7, 2.6, 0.5, self.mat(e.get("jacket_m", "wool_grey")), self.col,
                               seed=int(u * 7), hanger=False)
        return objs

    def gen_bench(self, e):
        p = e["pos"]
        L, D, H = e.get("length", 4.0), e.get("depth", 1.4), e.get("height", 1.5)
        wood = self.mat(e.get("m", "walnut_h"))
        objs = [box_centered(self.uid("bench_top"), (p[0], p[1], p[2] + H - 0.15), (L, D, 0.15), e.get("rot_z", 0), wood, self.col)]
        rot = math.radians(e.get("rot_z", 0))
        for sx in (-1, 1):
            lx = sx * (L / 2 - 0.3)
            wx, wy = p[0] + lx * math.cos(rot), p[1] + lx * math.sin(rot)
            objs.append(box_centered(self.uid("bench_leg"), (wx, wy, p[2]), (0.15, D - 0.2, H - 0.15), e.get("rot_z", 0), wood, self.col))
        if e.get("cushion", True):
            objs.append(sg.slab(self.uid("sg_bench_cush"), (0, 0, H + 0.125), (L - 0.2, D - 0.15, 0.25), self.mat(e.get("cushion_m", "oxblood")), self.col,
                                origin_ft=p, rot_z_deg=e.get("rot_z", 0), puff=0.2, sag=0.05))
        return objs

    def gen_lockers(self, e):
        """Mudroom locker bays: open walnut cubbies with a bench seat and upper cabinets."""
        b = e["b"]
        x0, y0, x1, y1, z0, z1 = b
        wood = self.mat("walnut_h")
        n = e.get("bays", 4)
        objs = [box_ft(self.uid("lk_back"), x0, y1 - 0.06, x1, y1, z0, z1, wood, self.col)]
        for i in range(n + 1):
            u = x0 + i * (x1 - x0) / n
            objs.append(box_ft(self.uid("lk_div"), u - 0.04, y0, u + 0.04, y1, z0, z1, wood, self.col))
        objs.append(box_ft(self.uid("lk_seat"), x0, y0, x1, y1, z0 + 1.4, z0 + 1.55, wood, self.col))
        objs.append(box_ft(self.uid("lk_plinth"), x0, y0 + 0.2, x1, y1, z0, z0 + 1.4, self.mat("black"), self.col))
        objs.append(box_ft(self.uid("lk_top"), x0, y0, x1, y1, z1 - 0.06, z1, wood, self.col))
        objs += self.gen_cabinet({"b": [x0, y0, x1, y1, z1 - 2.0, z1], "doors": n, "face": "-y"})
        for i in range(n):
            u = x0 + (i + 0.5) * (x1 - x0) / n
            objs.append(box_ft(self.uid("hook"), u - 0.03, y1 - 0.35, u + 0.03, y1 - 0.06, 5.4, 5.46, self.mat("brass"), self.col))
        objs.append(box_ft(self.uid("jacket"), x0 + 0.8, y1 - 0.6, x0 + 2.2, y1 - 0.1, 2.8, 5.3, self.mat("oxblood"), self.col))
        objs.append(box_ft(self.uid("bag"), x0 + 4.0, y1 - 0.7, x0 + 5.0, y1 - 0.1, 3.2, 5.3, self.mat("teal"), self.col))
        return objs

    def gen_cat_station(self, e):
        p = e["pos"]
        objs = [box_centered(self.uid("cat_mat"), p, (2.0, 1.3, 0.03), 0, self.mat("rubber"), self.col)]
        for dx in (-0.45, 0.45):
            objs.append(cylinder_ft(self.uid("bowl"), (p[0] + dx, p[1], p[2] + 0.03), 0.3, 0.2, self.mat("ceramic_white"), self.col, 16))
        return objs

    def gen_vanity(self, e):
        """Double wall-hung vanity with two basins, two mirrors with backlight glow. wall along x at y=at, face +y."""
        x0, x1 = e["x"]
        at = e["at"]
        z = e.get("z", 0)
        wood = self.mat("walnut_h")
        stone = self.mat("stone")
        objs = [box_ft(self.uid("van_body"), x0, at, x1, at + 1.8, z + 1.4, z + 2.6, wood, self.col),
                box_ft(self.uid("van_top"), x0 - 0.05, at, x1 + 0.05, at + 1.9, z + 2.6, z + 2.72, stone, self.col)]
        for cx in (x0 + (x1 - x0) * 0.27, x0 + (x1 - x0) * 0.73):
            basin = sphere_ft(self.uid("basin"), (cx, at + 1.0, z + 2.72), 0.6, self.mat("ceramic_white"), self.col)
            basin.scale = (1, 0.8, 0.35)
            objs.append(basin)
            objs.append(cylinder_ft(self.uid("tap"), (cx, at + 0.3, z + 2.72), 0.04, 0.9, self.mat("brass"), self.col, 10))
            objs.append(box_ft(self.uid("tap_spout"), cx - 0.03, at + 0.3, cx + 0.03, at + 0.8, z + 3.55, z + 3.62, self.mat("brass"), self.col))
            objs.append(box_ft(self.uid("mirror"), cx - 1.2, at + 0.06, cx + 1.2, at + 0.1, z + 3.6, z + 6.6, self.mat("mirror"), self.col))
            objs.append(box_ft(self.uid("mirror_glow"), cx - 1.25, at + 0.02, cx + 1.25, at + 0.06, z + 3.55, z + 6.65, self.mat("glow_soft"), self.col))
            self.light(type="area", pos=(cx, at + 0.2, z + 5.1), size=2.4, size_y=3.0, shape="RECTANGLE", watts=15, rot=(math.radians(90), 0, 0), name="mirror")   # -Z rotated +90 about X points +Y, into the room
        return objs

    def gen_shower(self, e):
        """Glass shower enclosure with bronze frame and brass heads. b = [x0,y0,x1,y1] footprint, glass on the open sides."""
        b = e["b"]
        z = e.get("z", 0)
        x0, y0, x1, y1 = b
        glass = self.mat("glass")
        bronze = self.mat("bronze")
        objs = []
        h = 7.0
        for side in e.get("glass_sides", ["+x", "-y"]):
            if side == "+x":
                objs.append(box_ft(self.uid("sh_glass"), x1 - 0.03, y0, x1, y1, z + 0.05, z + h, glass, get_collection("glass")))
                objs.append(box_ft(self.uid("sh_frame"), x1 - 0.06, y0, x1 + 0.03, y1, z + h, z + h + 0.1, bronze, self.col))
            elif side == "-x":
                objs.append(box_ft(self.uid("sh_glass"), x0, y0, x0 + 0.03, y1, z + 0.05, z + h, glass, get_collection("glass")))
            elif side == "-y":
                objs.append(box_ft(self.uid("sh_glass"), x0, y0, x1, y0 + 0.03, z + 0.05, z + h, glass, get_collection("glass")))
            elif side == "+y":
                objs.append(box_ft(self.uid("sh_glass"), x0, y1 - 0.03, x1, y1, z + 0.05, z + h, glass, get_collection("glass")))
        # heads on the wall named by head_wall
        hw = e.get("head_wall", "-x")
        n = e.get("heads", 2)
        for i in range(n):
            if hw in ("-x", "+x"):
                yy = y0 + (i + 0.5) * (y1 - y0) / n
                xx = x0 + 0.05 if hw == "-x" else x1 - 0.05
                arm = box_ft(self.uid("sh_arm"), xx, yy - 0.04, xx + (1.2 if hw == "-x" else -1.2), yy + 0.04, z + 6.8, z + 6.88, self.mat("brass"), self.col)
                head = cylinder_ft(self.uid("sh_head"), (xx + (1.1 if hw == "-x" else -1.1), yy, z + 6.72), 0.4, 0.08, self.mat("brass"), self.col, 20)
            else:
                xx = x0 + (i + 0.5) * (x1 - x0) / n
                yy = y0 + 0.05 if hw == "-y" else y1 - 0.05
                arm = box_ft(self.uid("sh_arm"), xx - 0.04, yy, xx + 0.04, yy + (1.2 if hw == "-y" else -1.2), z + 6.8, z + 6.88, self.mat("brass"), self.col)
                head = cylinder_ft(self.uid("sh_head"), (xx, yy + (1.1 if hw == "-y" else -1.1), z + 6.72), 0.4, 0.08, self.mat("brass"), self.col, 20)
            objs += [arm, head]
        # drain slot
        return objs

    def gen_towel_warmer(self, e):
        wall = e["wall"]
        u = e["u"]
        z = e.get("z", 2.5)
        at, face = wall["at"], wall["face"]
        objs = []
        for i in range(6):
            zz = z + i * 0.45
            if wall["axis"] == "y":
                d = at - 0.3 if face == "-x" else at + 0.3
                objs.append(cylinder_ft(self.uid("tw_bar"), (d, u, zz), 0.04, 2.0, self.mat("brass"), self.col, 10, axis="Y"))
            else:
                d = at - 0.3 if face == "-y" else at + 0.3
                objs.append(cylinder_ft(self.uid("tw_bar"), (u, d, zz), 0.04, 2.0, self.mat("brass"), self.col, 10, axis="X"))
        # a bath towel over the top bar, the short end toward the wall
        zt = z + 5 * 0.45
        if wall["axis"] == "y":
            d = at - 0.3 if face == "-x" else at + 0.3
            objs.append(sg.towel_hung(self.uid("sg_towel"), (d, u, zt), "y", 0.04, 1.4, 1.9, 0.5, ((1, 0) if face == "-x" else (-1, 0)), self.mat("towel_white"), self.col, seed=int(u)))
        else:
            d = at - 0.3 if face == "-y" else at + 0.3
            objs.append(sg.towel_hung(self.uid("sg_towel"), (u, d, zt), "x", 0.04, 1.4, 1.9, 0.5, ((0, 1) if face == "-y" else (0, -1)), self.mat("towel_white"), self.col, seed=int(u)))
        return objs

    def gen_closet(self, e):
        """Closet: island with glass top, shelving with folded clothes along walls. b = room interior bounds."""
        x0, y0, x1, y1 = e["b"]
        z = e.get("z", 0)
        wood = self.mat("walnut_h")
        objs = []
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        objs.append(box_ft(self.uid("cl_island"), cx - 2.0, cy - 1.25, cx + 2.0, cy + 1.25, z, z + 3.0, wood, self.col))
        objs.append(box_ft(self.uid("cl_glass"), cx - 2.05, cy - 1.3, cx + 2.05, cy + 1.3, z + 3.0, z + 3.05, self.mat("glass"), get_collection("glass")))
        rng = random.Random(21)
        for wall_y, face in ((y0, "+y"), (y1, "-y")):
            d0, d1 = (wall_y, wall_y + 1.6) if face == "+y" else (wall_y - 1.6, wall_y)
            objs.append(box_ft(self.uid("cl_unit"), x0 + 0.3, d0, x1 - 0.3, d1, z, z + 8.5, wood, self.col))
            # cut open bays with shelves: represent as recessed dark bays with fabric boxes
            for i in range(4):
                bx0 = x0 + 0.6 + i * (x1 - x0 - 1.2) / 4
                bx1 = bx0 + (x1 - x0 - 1.2) / 4 - 0.15
                bd0, bd1 = (d1 - 0.02, d1 + 0.01) if face == "+y" else (d0 - 0.01, d0 + 0.02)
                for zz in (1.0, 2.6, 4.2, 5.8, 7.2):
                    fold = box_ft(self.uid("fold"), bx0 + 0.15, bd0 - (0.9 if face == "-y" else 0), bx1 - 0.15, bd1 + (0.9 if face == "+y" else 0), z + zz, z + zz + rng.uniform(0.3, 0.6),
                                  self.mat(rng.choice(["linen", "olive", "oxblood", "teal", "rug_cream", "mustard"])), self.col)
                    objs.append(fold)
        return objs

    def gen_roller_shade(self, e):
        """Partly lowered roller shade over a window. wall axis x at y=at inside face; x-span; top z; drop."""
        x0, x1 = e["span"]
        at = e["at"]
        inward = e.get("inward", -1)
        top = e.get("top", 8.2)
        drop = e.get("drop", 2.0)
        d0, d1 = (at + 0.1 * inward, at + 0.3 * inward)
        d0, d1 = min(d0, d1), max(d0, d1)
        objs = [cylinder_ft(self.uid("shade_roll"), ((x0 + x1) / 2, (d0 + d1) / 2, top), 0.15, x1 - x0, self.mat("black"), self.col, 12, axis="X"),
                box_ft(self.uid("shade"), x0, (d0 + d1) / 2 - 0.01, x1, (d0 + d1) / 2 + 0.01, top - drop, top, self.mat("rug_cream"), self.col)]
        return objs

    def gen_wall_panel(self, e):
        """Thin panel on a wall face (wallpaper, mirror wall). b = [x0,y0,x1,y1,z0,z1]."""
        return [box_ft(self.uid("panel"), *e["b"], mat=self.mat(e.get("m", "wallpaper_geo")), collection=self.col)]

    def gen_bar(self, e):
        """Bar: brass edge on the counter, stools handled by models, back-bar shelves with glassware, espresso machine."""
        objs = []
        counter = bpy.data.objects.get("feat_bar_counter")
        cb = counter["bounds_ft"] if counter else [23, 24, 29, 26, -10, -6.5]
        x0, y0, x1, y1, z0, z1 = cb
        objs.append(box_ft(self.uid("bar_top"), x0 - 0.1, y0 - 0.1, x1 + 0.1, y1 + 0.1, z1, z1 + 0.12, self.mat("terrazzo"), self.col))
        objs.append(box_ft(self.uid("bar_edge"), x0 - 0.12, y1 + 0.08, x1 + 0.12, y1 + 0.12, z1 - 0.05, z1 + 0.14, self.mat("brass"), self.col))
        objs.append(box_ft(self.uid("bar_footrail"), x0, y1 + 0.6, x1, y1 + 0.66, z0 + 0.7, z0 + 0.76, self.mat("brass"), self.col))
        # back bar along the east wall (x=29.5 feature 'bar back wall' at x 29.5-29.9)
        bw = bpy.data.objects.get("feat_bar_back_wall")
        wx = bw["bounds_ft"][0] if bw else 29.5
        for zz in (z0 + 4.0, z0 + 5.4, z0 + 6.8):
            objs.append(box_ft(self.uid("bb_shelf"), wx - 0.9, 16.0, wx, 23.5, zz, zz + 0.08, self.mat("walnut_h"), self.col))
            self.light(type="area", pos=(wx - 0.45, 19.75, zz + 0.12), size=0.6, size_y=7.0, shape="RECTANGLE", watts=6, rot=(0, 0, 0), name="backbar")
        rng = random.Random(33)
        for i in range(24):
            zz = [z0 + 4.08, z0 + 5.48, z0 + 6.88][i % 3]
            yy = 16.3 + rng.uniform(0, 6.9)
            objs.append(cylinder_ft(self.uid("glass"), (wx - 0.45 + rng.uniform(-0.2, 0.2), yy, zz), rng.uniform(0.1, 0.16), rng.uniform(0.35, 0.8),
                                    self.mat(rng.choice(["glass", "glass", "brass", "teal"])), get_collection("glass") if rng.random() < 0.6 else self.col, 12))
        # lower back-bar cabinets
        objs += self.gen_cabinet({"b": [wx - 2.0, 15.5, wx, 23.5, z0, z0 + 3.0], "doors": 4, "face": "-x"})
        objs.append(box_ft(self.uid("bb_top"), wx - 2.05, 15.5, wx, 23.5, z0 + 3.0, z0 + 3.12, self.mat("terrazzo"), self.col))
        # espresso machine and cake stand on the back counter
        objs.append(box_ft(self.uid("espresso"), wx - 1.7, 17.0, wx - 0.3, 18.6, z0 + 3.12, z0 + 4.4, self.mat("chrome"), self.col))
        objs.append(box_ft(self.uid("espresso_top"), wx - 1.75, 16.95, wx - 0.25, 18.65, z0 + 4.4, z0 + 4.5, self.mat("black"), self.col))
        objs.append(cylinder_ft(self.uid("cake_stand"), (wx - 1.0, 21.5, z0 + 3.12), 0.55, 0.45, self.mat("ceramic_white"), self.col, 24))
        dome = sphere_ft(self.uid("cake_dome"), (wx - 1.0, 21.5, z0 + 3.6), 0.6, self.mat("glass"), get_collection("glass"))
        dome.scale = (1, 1, 0.9)
        objs.append(dome)
        objs.append(cylinder_ft(self.uid("cake"), (wx - 1.0, 21.5, z0 + 3.57), 0.4, 0.4, self.mat("mustard"), self.col, 20))
        return objs

    def gen_power_rack(self, e):
        p = e["pos"]  # center bottom
        w, d, h = e.get("width", 4.0), e.get("depth", 4.5), e.get("height", 7.5)
        black = self.mat("black")
        objs = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                objs.append(box_centered(self.uid("rack_post"), (p[0] + sx * w / 2, p[1] + sy * d / 2, p[2]), (0.25, 0.25, h), 0, black, self.col))
        for zz in (h - 0.1, 5.0):
            objs.append(box_ft(self.uid("rack_beam"), p[0] - w / 2, p[1] - d / 2 - 0.12, p[0] + w / 2, p[1] - d / 2 + 0.12, p[2] + zz - 0.25, p[2] + zz, black, self.col))
            objs.append(box_ft(self.uid("rack_beam"), p[0] - w / 2, p[1] + d / 2 - 0.12, p[0] + w / 2, p[1] + d / 2 + 0.12, p[2] + zz - 0.25, p[2] + zz, black, self.col))
        for sx in (-1, 1):
            objs.append(box_ft(self.uid("rack_beam"), p[0] + sx * w / 2 - 0.12, p[1] - d / 2, p[0] + sx * w / 2 + 0.12, p[1] + d / 2, p[2] + h - 0.35, p[2] + h - 0.1, black, self.col))
            objs.append(box_ft(self.uid("rack_beam"), p[0] + sx * w / 2 - 0.12, p[1] - d / 2, p[0] + sx * w / 2 + 0.12, p[1] + d / 2, p[2] + 0.1, p[2] + 0.35, black, self.col))
        # pull-up bar and j-hooks with a loaded barbell at 3.2 ft
        objs.append(cylinder_ft(self.uid("pullup"), (p[0], p[1] - d / 2, p[2] + h - 0.6), 0.06, w, self.mat("steel"), self.col, 12, axis="X"))
        bz = p[2] + 3.3
        for sx in (-1, 1):
            objs.append(box_ft(self.uid("jhook"), p[0] + sx * w / 2 - 0.15, p[1] - d / 2 - 0.35, p[0] + sx * w / 2 + 0.15, p[1] - d / 2 + 0.05, bz - 0.4, bz + 0.1, black, self.col))
        objs.append(cylinder_ft(self.uid("barbell"), (p[0], p[1] - d / 2 - 0.15, bz), 0.05, 7.2, self.mat("chrome"), self.col, 12, axis="X"))
        for sx in (-1, 1):
            for k, r in enumerate((0.75, 0.75, 0.55)):
                px = p[0] + sx * (2.7 + k * 0.13)
                objs.append(cylinder_ft(self.uid("plate"), (px, p[1] - d / 2 - 0.15, bz), r, 0.1, self.mat("iron_plate"), self.col, 24, axis="X"))
        return objs

    def gen_gym_bench(self, e):
        p = e["pos"]
        rot = e.get("rot_z", 0)
        objs = [box_centered(self.uid("gb_pad"), (p[0], p[1], p[2] + 1.25), (4.0, 1.0, 0.25), rot, self.mat("black"), self.col),
                box_centered(self.uid("gb_frame"), (p[0], p[1], p[2] + 0.1), (3.2, 0.25, 1.15), rot, self.mat("steel"), self.col),
                box_centered(self.uid("gb_foot"), (p[0], p[1], p[2]), (3.4, 1.6, 0.1), rot, self.mat("steel"), self.col)]
        return objs

    def gen_dumbbell_rack(self, e):
        p = e["pos"]
        L = e.get("length", 6.0)
        rot = e.get("rot_z", 0)
        objs = [box_centered(self.uid("db_rack"), (p[0], p[1], p[2] + 1.2), (L, 1.6, 0.15), rot, self.mat("steel"), self.col),
                box_centered(self.uid("db_rack"), (p[0], p[1], p[2] + 2.3), (L, 1.2, 0.15), rot, self.mat("steel"), self.col)]
        for sx in (-1, 1):
            objs.append(box_centered(self.uid("db_leg"), (p[0] + sx * (L / 2 - 0.2), p[1], p[2]), (0.15, 1.6, 2.3), rot, self.mat("steel"), self.col))
        n = int(L / 0.8)
        for tier, zz in ((0, 1.35), (1, 2.45)):
            for i in range(n):
                u = -L / 2 + 0.5 + i * (L - 1.0) / max(1, n - 1)
                r = 0.18 + 0.02 * i + 0.05 * tier
                wx, wy = p[0] + u * math.cos(math.radians(rot)), p[1] + u * math.sin(math.radians(rot))
                objs.append(cylinder_ft(self.uid("db"), (wx, wy, p[2] + zz + r), r, 0.95, self.mat("iron_plate"), self.col, 12, axis="Y" if rot % 180 == 0 else "X"))
        return objs

    def gen_functional_trainer(self, e):
        p = e["pos"]
        rot = e.get("rot_z", 0)
        black = self.mat("black")
        objs = [box_centered(self.uid("ft_tower"), (p[0] - 2.0, p[1], p[2]), (1.2, 1.4, 7.0), rot, black, self.col),
                box_centered(self.uid("ft_tower"), (p[0] + 2.0, p[1], p[2]), (1.2, 1.4, 7.0), rot, black, self.col),
                box_centered(self.uid("ft_top"), (p[0], p[1], p[2] + 6.6), (5.2, 0.5, 0.4), rot, black, self.col)]
        for sx in (-1, 1):
            objs.append(box_centered(self.uid("ft_stack"), (p[0] + sx * 2.0, p[1], p[2] + 0.3), (0.8, 0.8, 2.6), rot, self.mat("iron_plate"), self.col))
        return objs

    def gen_rower(self, e):
        p = e["pos"]
        rot = e.get("rot_z", 0)
        objs = [box_centered(self.uid("row_rail"), (p[0], p[1], p[2] + 0.6), (7.5, 0.5, 0.2), rot, self.mat("steel"), self.col),
                box_centered(self.uid("row_seat"), (p[0] + 1.0, p[1], p[2] + 0.8), (1.0, 1.0, 0.15), rot, black := self.mat("black"), self.col),
                box_centered(self.uid("row_foot"), (p[0] - 3.5, p[1], p[2]), (0.4, 1.5, 0.6), rot, black, self.col),
                box_centered(self.uid("row_foot"), (p[0] + 3.5, p[1], p[2]), (0.4, 1.5, 0.6), rot, black, self.col)]
        fan = cylinder_ft(self.uid("row_fan"), (p[0] - 2.8, p[1], p[2] + 1.4), 0.9, 0.8, black, self.col, 24, axis="Y")
        fan.rotation_euler = (0, 0, math.radians(rot))
        objs.append(fan)
        return objs

    def gen_towels(self, e):
        p = e["pos"]
        objs = []
        for i in range(e.get("count", 4)):
            objs.append(cylinder_ft(self.uid("towel"), (p[0], p[1] + i * 0.55, p[2]), 0.25, 1.2, self.mat("towel_white"), self.col, 12, axis="X"))
        return objs

    def gen_sauna(self, e):
        """Cedar sauna interior: benches, heater, glass front with door, warm glow. Uses the 'sauna box' feature bounds."""
        sb = bpy.data.objects.get("feat_sauna_box")
        b = sb["bounds_ft"] if sb else [23, 8, 29, 13.5, -10, -3]
        x0, y0, x1, y1, z0, z1 = b
        cedar = self.mat("cedar")
        objs = []
        # hollow the box: rebuild as walls (remove the solid feature)
        if sb is not None:
            bpy.data.objects.remove(sb, do_unlink=True)
        t = 0.25
        objs.append(box_ft(self.uid("sa_back"), x0, y1 - t, x1, y1, z0, z1, cedar, self.col))
        objs.append(box_ft(self.uid("sa_side"), x0, y0, x0 + t, y1, z0, z1, cedar, self.col))
        objs.append(box_ft(self.uid("sa_side"), x1 - t, y0, x1, y1, z0, z1, cedar, self.col))
        objs.append(box_ft(self.uid("sa_top"), x0, y0, x1, y1, z1 - t, z1, cedar, self.col))
        objs.append(box_ft(self.uid("sa_floor"), x0, y0, x1, y1, z0, z0 + 0.1, cedar, self.col))
        # front: glass with a bronze frame and a glass door (closed)
        glass = self.mat("glass")
        bronze = self.mat("bronze")
        objs.append(box_ft(self.uid("sa_glass"), x0 + t, y0 + 0.02, x1 - t, y0 + 0.04, z0 + 0.1, z1 - t, glass, get_collection("glass")))
        for u in (x0 + t, x0 + 2.8, x1 - t):
            objs.append(box_ft(self.uid("sa_mull"), u - 0.06, y0 - 0.02, u + 0.06, y0 + 0.08, z0, z1, bronze, self.col))
        objs.append(box_ft(self.uid("sa_head"), x0, y0 - 0.02, x1, y0 + 0.08, z1 - t - 0.1, z1, bronze, self.col))
        objs.append(box_ft(self.uid("sa_handle"), x0 + 2.35, y0 - 0.15, x0 + 2.45, y0 - 0.05, z0 + 2.5, z0 + 4.5, self.mat("brass"), self.col))
        # benches, two tiers along the back
        objs.append(box_ft(self.uid("sa_bench"), x0 + t, y1 - t - 2.0, x1 - t, y1 - t, z0 + 2.8, z0 + 3.0, cedar, self.col))
        objs.append(box_ft(self.uid("sa_bench"), x0 + t, y1 - t - 3.6, x1 - t, y1 - t - 2.0, z0 + 1.5, z0 + 1.7, cedar, self.col))
        objs.append(box_ft(self.uid("sa_bench_face"), x0 + t, y1 - t - 3.6, x1 - t, y1 - t - 3.5, z0 + 0.1, z0 + 1.5, cedar, self.col))
        # heater with stones
        objs.append(box_ft(self.uid("sa_heater"), x1 - t - 1.4, y0 + 0.4, x1 - t - 0.2, y0 + 1.6, z0 + 0.1, z0 + 2.4, self.mat("black"), self.col))
        for i in range(6):
            objs.append(sphere_ft(self.uid("stone"), (x1 - t - 0.8 + (i % 3 - 1) * 0.3, y0 + 1.0 + (i // 3) * 0.3, z0 + 2.5), 0.18, self.mat("stone"), self.col, 10, 6))
        # glow strip under the upper bench and a warm light
        objs.append(box_ft(self.uid("sa_glow"), x0 + t + 0.1, y1 - t - 2.0, x1 - t - 0.1, y1 - t - 1.9, z0 + 2.7, z0 + 2.75, self.mat("lamp_glow"), self.col))
        self.light(type="point", pos=((x0 + x1) / 2, y1 - t - 1.5, z0 + 2.4), watts=e.get("watts", 40), kelvin=2200, radius=0.3, name="sauna")
        self.light(type="point", pos=(x1 - t - 0.8, y0 + 1.0, z0 + 2.7), watts=15, kelvin=1800, radius=0.2, name="sauna_heater")
        return objs

    def gen_shelving_unit(self, e):
        """Steel utility shelving with boxes. pos center bottom, length along local X."""
        p = e["pos"]
        L, D, H = e.get("length", 6.0), e.get("depth", 2.0), e.get("height", 6.5)
        rot = e.get("rot_z", 0)
        steel = self.mat("steel")
        objs = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                lx, ly = sx * L / 2, sy * D / 2
                ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
                objs.append(box_centered(self.uid("sh_post"), (p[0] + lx * ca - ly * sa, p[1] + lx * sa + ly * ca, p[2]), (0.12, 0.12, H), rot, steel, self.col))
        rng = random.Random(e.get("seed", 2))
        for k in range(4):
            zz = p[2] + 0.3 + k * (H - 0.6) / 3
            objs.append(box_centered(self.uid("sh_shelf"), (p[0], p[1], zz), (L, D, 0.08), rot, steel, self.col))
            u = -L / 2 + 0.3
            while u < L / 2 - 0.8:
                w = rng.uniform(0.9, 1.6)
                if u + w > L / 2 - 0.1:
                    break
                off = u + w / 2
                objs.append(box_centered(self.uid("crate"), (p[0] + off * math.cos(math.radians(rot)), p[1] + off * math.sin(math.radians(rot)), zz + 0.08), (w - 0.1, D - 0.4, rng.uniform(0.8, 1.3)), rot,
                                         self.mat(rng.choice(["paper", "paper", "olive", "black"])), self.col))
                u += w + rng.uniform(0.05, 0.4)
        return objs

    def gen_water_heater(self, e):
        p = e["pos"]
        objs = [cylinder_ft(self.uid("wh"), p, 1.1, 5.5, self.mat("steel"), self.col, 24),
                box_ft(self.uid("panel"), p[0] + 3.0, p[1] - 0.15, p[0] + 4.4, p[1], p[2] + 3.0, p[2] + 6.0, self.mat("steel"), self.col)]
        return objs

    def gen_puzzle(self, e):
        b = e["b"]
        z = e["z"]
        objs = [box_ft(self.uid("puzzle"), b[0], b[1], b[2], b[3], z, z + 0.02, self.art_material(e.get("seed", 77)), self.col)]
        rng = random.Random(5)
        for i in range(14):
            s = 0.12
            cx, cy = rng.uniform(b[0] - 0.5, b[2] + 0.5), rng.uniform(b[1] - 0.3, b[3] + 0.3)
            objs.append(box_ft(self.uid("piece"), cx, cy, cx + s, cy + s, z, z + 0.02, self.art_material(rng.randint(0, 99)), self.col))
        return objs

    def gen_wall_screen(self, e):
        return [box_ft(self.uid("wscreen"), *e["b"], mat=self.mat("screen"), collection=self.col),
                box_ft(self.uid("wscreen_frame"), e["b"][0] - 0.05, e["b"][1] - 0.01, e["b"][2] + 0.05, e["b"][3] + 0.01, e["b"][4] - 0.05, e["b"][5] + 0.05, mat=self.mat("black"), collection=self.col)][::-1]

    def gen_curtain(self, e):
        """Stacked linen drape: alternating half-round pleats along a wall segment. wall axis x at y=at (inside face),
        span [u0,u1], z0..z1, face -y|+y (side of the wall the curtain hangs on)."""
        u0, u1 = e["span"]
        at = e["at"]
        z0, z1 = e.get("z", [0.05, 8.6])
        face = e.get("face", "-y")
        r = e.get("pleat_r", 0.14)
        lin = self.mat(e.get("m", "linen"))
        objs = []
        u = u0 + r
        k = 0
        d = at + (-(r + 0.05) if face == "-y" else (r + 0.05))
        while u < u1 - r:
            off = r * 0.55 * (1 if k % 2 == 0 else -1)
            c = cylinder_ft(self.uid("pleat"), (u, d + off, z0), r, z1 - z0, lin, self.col, 14)
            c.scale = (1.0, 0.75, 1.0)
            objs.append(c)
            u += r * 1.35
            k += 1
        # track
        objs.append(box_ft(self.uid("track"), u0 - 0.1, min(at, d) - 0.05, u1 + 0.1, max(at, d) + 0.05, z1, z1 + 0.08, self.mat("bronze"), self.col))
        return objs

    def gen_panel_grooves(self, e):
        """Vertical slat grooves on a paneled wall face: thin dark strips every 'pitch' feet.
        b = [x0,y0,x1,y1,z0,z1] of a thin box on the wall face (its thin axis is the depth)."""
        x0, y0, x1, y1, z0, z1 = e["b"]
        pitch = e.get("pitch", 0.5)
        gw = e.get("width", 0.03)
        dark = self.mat("black")
        objs = []
        if (x1 - x0) < (y1 - y0):
            u = y0 + pitch
            while u < y1 - 0.05:
                objs.append(box_ft(self.uid("groove"), x0, u - gw / 2, x1, u + gw / 2, z0, z1, dark, self.col))
                u += pitch
        else:
            u = x0 + pitch
            while u < x1 - 0.05:
                objs.append(box_ft(self.uid("groove"), u - gw / 2, y0, u + gw / 2, y1, z0, z1, dark, self.col))
                u += pitch
        return objs

    def gen_side_table(self, e):
        p = e["pos"]
        wood = self.mat(e.get("m", "walnut_h"))
        objs = [cylinder_ft(self.uid("st_top"), (p[0], p[1], p[2] + 1.8), 0.9, 0.08, wood, self.col, 28),
                cylinder_ft(self.uid("st_stem"), (p[0], p[1], p[2] + 0.1), 0.08, 1.7, self.mat("brass"), self.col, 10),
                cylinder_ft(self.uid("st_foot"), p, 0.55, 0.1, self.mat("stone"), self.col, 24)]
        if e.get("book", True):
            objs.append(box_ft(self.uid("st_book"), p[0] - 0.4, p[1] - 0.3, p[0] + 0.3, p[1] + 0.2, p[2] + 1.88, p[2] + 2.0, self.mat("book_a"), self.col))
        return objs


def build(plan, house, mats, staging_path=None):
    root = house.root
    s = Stager(plan, house, mats, root, staging_path)
    s.build_all()
    house.stager = s
    return s
