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
    def __init__(self, plan, mats):
        self.plan = plan
        self.mats = mats
        self.wt = plan.get("wall_thickness", 0.5)
        self.st = plan.get("slab_thickness", 0.5)
        self.rooms = plan["rooms"]
        self.floors = plan["floors"]
        self.walls = []       # wall objects
        self.slabs = []
        self.room_by_name = {r["name"]: r for r in self.rooms}
        self.col_shell = get_collection("shell")
        self.col_features = get_collection("features")
        self.col_lights = get_collection("lights")
        self.col_cameras = get_collection("cameras")

    # -- adjacency: does another room on this floor share this edge?
    def neighbor_along(self, room, side):
        x0, y0, x1, y1 = room["b"]
        for r in self.rooms:
            if r is room or r["floor"] != room["floor"]:
                continue
            a0, b0, a1, b1 = r["b"]
            if side == "south" and abs(b1 - y0) < 1e-6 and min(a1, x1) - max(a0, x0) > 0.01:
                return r
            if side == "north" and abs(b0 - y1) < 1e-6 and min(a1, x1) - max(a0, x0) > 0.01:
                return r
            if side == "west" and abs(a1 - x0) < 1e-6 and min(b1, y1) - max(b0, y0) > 0.01:
                return r
            if side == "east" and abs(a0 - x1) < 1e-6 and min(b1, y1) - max(b0, y0) > 0.01:
                return r
        return None

    def build_rooms(self):
        wt, st = self.wt, self.st
        half = wt / 2
        for room in self.rooms:
            fl = self.floors[room["floor"]]
            z, h = fl["z"], fl["h"]
            x0, y0, x1, y1 = room["b"]
            nm = room["name"]
            wall_mat = self.mats.get(room["wall"])
            floor_mat = self.mats.get(room["floorm"])
            ceil_mat = self.mats.get(room["ceil"])
            # slabs: split slab thickness between floor of this room and ceiling of the one below
            s = box_ft("floor_%s" % nm, x0, y0, x1, y1, z - st / 2, z, floor_mat, self.col_shell,
                       {"room": nm, "floor": room["floor"], "kind": "floor"})
            self.slabs.append(s)
            s = box_ft("ceil_%s" % nm, x0, y0, x1, y1, z + h, z + h + st / 2, ceil_mat, self.col_shell,
                       {"room": nm, "floor": room["floor"], "kind": "ceil"})
            self.slabs.append(s)
            # walls: half thickness if shared with a neighbor, full if exterior
            tS = half if self.neighbor_along(room, "south") else wt
            tN = half if self.neighbor_along(room, "north") else wt
            tW = half if self.neighbor_along(room, "west") else wt
            tE = half if self.neighbor_along(room, "east") else wt
            specs = [
                ("south", x0, y0, x1, y0 + tS, "x"),
                ("north", x0, y1 - tN, x1, y1, "x"),
                ("west", x0, y0 + tS, x0 + tW, y1 - tN, "y"),
                ("east", x1 - tE, y0 + tS, x1, y1 - tN, "y"),
            ]
            for side, ax0, ay0, ax1, ay1, axis in specs:
                w = box_ft("wall_%s_%s" % (nm, side), ax0, ay0, ax1, ay1, z, z + h, wall_mat,
                           self.col_shell,
                           {"room": nm, "floor": room["floor"], "kind": "wall", "axis": axis,
                            "side": side})
                self.walls.append(w)
        log("rooms:", len(self.rooms), "walls:", len(self.walls), "slabs:", len(self.slabs))

    def build_openings(self):
        cut = 0
        skipped = []
        for op in self.plan["openings"]:
            fl = self.floors[op["floor"]]
            z0 = fl["z"] + op.get("z0", 0)
            z1 = z0 + op["h"]
            pad = self.wt * 1.2
            if op["axis"] == "x":
                b = [op["c"] - op["w"] / 2, op["at"] - pad, op["c"] + op["w"] / 2, op["at"] + pad, z0, z1]
            else:
                b = [op["at"] - pad, op["c"] - op["w"] / 2, op["at"] + pad, op["c"] + op["w"] / 2, z0, z1]
            # a door opening that starts at floor level: cut a hair below the floor so no sliver remains
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

    def build_pits(self):
        for pit in self.plan.get("pits", []):
            room = self.room_by_name[pit["room"]]
            fl = self.floors[room["floor"]]
            z = fl["z"]
            px0, py0, px1, py1 = pit["b"]
            d = pit["depth"]
            floor_ob = bpy.data.objects["floor_%s" % room["name"]]
            cutter = box_ft("cutter_pit", px0, py0, px1, py1, z - self.st, z + 0.1)
            boolean_cut(floor_ob, cutter)
            bpy.data.objects.remove(cutter, do_unlink=True)
            edge = self.mats.get(pit["edge"])
            seat = self.mats.get(pit["seat"])
            floor_mat = self.mats.get(room["floorm"])
            # pit floor
            box_ft("pit_floor", px0, py0, px1, py1, z - d - self.st / 2, z - d, floor_mat, self.col_features)
            # lining walls with a small lip above the room floor, capped in the edge material
            t = 0.25
            lip = 0.2
            zb, zt = z - d - self.st / 2, z + lip
            box_ft("pit_wall_s", px0, py0, px1, py0 + t, zb, zt, edge, self.col_features)
            box_ft("pit_wall_n", px0, py1 - t, px1, py1, zb, zt, edge, self.col_features)
            box_ft("pit_wall_w", px0, py0 + t, px0 + t, py1 - t, zb, zt, edge, self.col_features)
            box_ft("pit_wall_e", px1 - t, py0 + t, px1, py1 - t, zb, zt, edge, self.col_features)
            # seat cushions on three sides; open side faces the panel
            open_side = pit.get("open_side", "north")
            sd, sh = 2.5, 1.4
            zc0, zc1 = z - d, z - d + sh
            ix0, iy0, ix1, iy1 = px0 + t, py0 + t, px1 - t, py1 - t
            sides = {
                "south": (ix0, iy0, ix1, iy0 + sd),
                "north": (ix0, iy1 - sd, ix1, iy1),
                "west": (ix0, iy0, ix0 + sd, iy1),
                "east": (ix1 - sd, iy0, ix1, iy1),
            }
            # trim the E/W cushions so they butt against the S/N cushion instead of overlapping
            for side, (a0, b0, a1, b1) in sides.items():
                if side == open_side:
                    continue
                if side in ("west", "east"):
                    if "south" != open_side:
                        b0 += sd
                    if "north" != open_side:
                        b1 -= sd
                box_ft("pit_seat_%s" % side, a0, b0, a1, b1, zc0, zc1, seat, self.col_features)
            # back cushions leaning on the lining walls
            bt = 0.35
            zk0, zk1 = zc1, zc1 + 1.2
            if open_side != "south":
                box_ft("pit_back_s", ix0, iy0, ix1, iy0 + bt, zk0, zk1, seat, self.col_features)
            if open_side != "north":
                box_ft("pit_back_n", ix0, iy1 - bt, ix1, iy1, zk0, zk1, seat, self.col_features)
            if open_side != "west":
                box_ft("pit_back_w", ix0, iy0, ix0 + bt, iy1, zk0, zk1, seat, self.col_features)
            if open_side != "east":
                box_ft("pit_back_e", ix1 - bt, iy0, ix1, iy1, zk0, zk1, seat, self.col_features)
            log("pit in", room["name"], "depth", d)

    def build_ground(self):
        g = self.plan.get("ground")
        if not g:
            return
        half = g.get("size", 400) / 2
        rooms = [r for r in self.rooms if r["floor"] == "main"]
        skin = self.plan.get("exterior", {}).get("skin_t", 0.0)
        X0 = min(r["b"][0] for r in rooms) - skin
        Y0 = min(r["b"][1] for r in rooms) - skin
        X1 = max(r["b"][2] for r in rooms) + skin
        Y1 = max(r["b"][3] for r in rooms) + skin
        z0, z1 = g["z"] - 0.5, g["z"]
        mat = self.mats.get(g.get("m", "grass"))
        cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
        # four boxes around the house footprint so nothing intrudes into the basement
        box_ft("ground_s", cx - half, cy - half, cx + half, Y0, z0, z1, mat, self.col_shell, {"kind": "ground"})
        box_ft("ground_n", cx - half, Y1, cx + half, cy + half, z0, z1, mat, self.col_shell, {"kind": "ground"})
        box_ft("ground_w", cx - half, Y0, X0, Y1, z0, z1, mat, self.col_shell, {"kind": "ground"})
        box_ft("ground_e", X1, Y0, cx + half, Y1, z0, z1, mat, self.col_shell, {"kind": "ground"})

    def build_features(self):
        n = 0
        for f in self.plan.get("features", []):
            b = f["box"]
            box_ft("feat_%s" % f["note"].replace(" ", "_"), *b, mat=self.mats.get(f["m"]),
                   collection=self.col_features)
            n += 1
        log("features:", n)

    # -- lights
    def build_lights(self, room_fill_scale=1.0):
        warm = kelvin_rgb(2700)
        for room in self.rooms:
            fl = self.floors[room["floor"]]
            x0, y0, x1, y1 = room["b"]
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
        d = Vector(sun["direction"]).normalized()
        so.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        self.col_lights.objects.link(so)
        # world
        w = bpy.data.worlds.new("world")
        bpy.context.scene.world = w
        w.use_nodes = True
        bg = w.node_tree.nodes["Background"]
        wr = self.plan.get("world", {"rgb": [0.9, 0.85, 0.78], "strength": 1.0})
        bg.inputs[0].default_value = (wr["rgb"][0], wr["rgb"][1], wr["rgb"][2], 1.0)
        bg.inputs[1].default_value = wr["strength"]
        log("lights:", len(self.rooms), "area +", "sun")


# ----------------------------------------------------------------------------- camera / shots


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


def check_path(scene, cam, shot, radius_ft=0.3):
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
            inside = (count % 2) == 1
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
    house.build_ground()
    if stage == "phase2":
        import details
        import staging
        details.build(plan, house, mats)
        staging.build(plan, house, mats)
        import lighting
        lighting.build(plan, house, mats)
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
