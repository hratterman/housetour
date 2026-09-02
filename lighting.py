"""
lighting.py: Phase 2 layered lighting. Dim warm ceiling fill per room, an HDRI sky plus a sun lamp,
and practical lights registered by staging.py and details.py (lamps, pendants, picture lights, fire).
All indoor sources are 2700K. Global multipliers live in plan["lighting"].
"""
import math
import os

import bpy
from mathutils import Vector

from geom import m, log, get_collection, area_light, point_light, spot_light, kelvin_rgb


def build(plan, house, mats):
    col = get_collection("lights")
    L = plan.get("lighting", {})
    fill_scale = L.get("fill_scale", 0.35)
    if not isinstance(fill_scale, dict):
        fill_scale = {k: fill_scale for k in house.floors}
    practical_scale = L.get("practical_scale", 1.0)
    sun_strength = L.get("sun_strength", plan.get("sun", {}).get("strength", 4.0))
    sky_strength = L.get("sky_strength", 0.6)
    warm = kelvin_rgb(2700)
    n = 0

    # ceiling fill: one soft warm area light per room, dimmed
    for room in house.rooms:
        fl = house.floors[room["floor"]]
        x0, y0, x1, y1 = room["b"]
        w = room.get("light", 50) * fill_scale.get(room["floor"], 0.35)
        size = min(4.0, max(1.5, min(x1 - x0, y1 - y0) * 0.35))
        ob = area_light("fill_%s" % room["name"], ((x0 + x1) / 2, (y0 + y1) / 2, fl["z"] + fl["h"] - 0.12),
                        size, w, 2700, col)
        ob.data.spread = math.radians(150)
        n += 1

    # practicals registered by staging/details: list of dicts
    for i, p in enumerate(getattr(house, "practicals", [])):
        kind = p.get("type", "point")
        watts = p.get("watts", 20) * practical_scale
        k = p.get("kelvin", 2700)
        name = "prac_%02d_%s" % (i, p.get("name", kind))
        if kind == "point":
            ob = point_light(name, p["pos"], watts, k, p.get("radius", 0.12), col)
        elif kind == "spot":
            ob = spot_light(name, p["pos"], p["aim"], watts, k, p.get("angle", 40), p.get("blend", 0.6), col)
        elif kind == "area":
            ob = area_light(name, p["pos"], p.get("size", 1.0), watts, k, col, rot=p.get("rot", (0, 0, 0)),
                            shape=p.get("shape", "SQUARE"), size_y_ft=p.get("size_y"))
        else:
            continue
        n += 1

    # picture lights from details: narrow warm spots washing down the wall
    d = getattr(house, "details", None)
    if d is not None:
        for i, pl in enumerate(getattr(d, "picture_light_positions", [])):
            off = -0.35 if pl["wall"] == "east" else 0.35
            spot_light("piclight_%d" % i, (pl["x"] + off, pl["y"], pl["z"] - 0.1),
                       (pl["aim_x"], pl["y"], pl["aim_z"]), 12 * practical_scale, 2700, 70, 0.8, col)
            n += 1

    # sun
    sun = plan.get("sun", {"direction": [0.35, -0.55, -0.75]})
    sd = bpy.data.lights.new("sun", "SUN")
    sd.energy = sun_strength
    sd.color = kelvin_rgb(L.get("sun_kelvin", 4800))
    sd.angle = math.radians(L.get("sun_angle_deg", 1.0))
    so = bpy.data.objects.new("sun", sd)
    so.location = (m(21), m(23), m(40))
    so.rotation_euler = Vector(sun["direction"]).normalized().to_track_quat("-Z", "Y").to_euler()
    col.objects.link(so)

    # world: HDRI if present, else warm gray
    w = bpy.data.worlds.new("world")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    hdri = os.path.join(house.root, "assets", "hdris", L.get("hdri", "sky") + ".hdr")
    if os.path.exists(hdri):
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(hdri)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0, 0, math.radians(L.get("hdri_rot_deg", 0)))
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
        nt.links.new(env.outputs["Color"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = sky_strength
        # keep the sky from lighting interiors too flatly: slightly cooler multiplier is inherent in the HDRI
        log("world: HDRI", os.path.basename(hdri), "strength", sky_strength)
    else:
        wr = plan.get("world", {"rgb": [0.9, 0.85, 0.78], "strength": 0.8})
        bg.inputs[0].default_value = (wr["rgb"][0], wr["rgb"][1], wr["rgb"][2], 1.0)
        bg.inputs[1].default_value = wr["strength"]
        log("world: flat", wr)
    # world settings that help CPU noise
    try:
        w.cycles.sampling_method = "MANUAL"
        w.cycles.sample_map_resolution = 1024
    except Exception:
        pass
    log("lights: %d (fill %d rooms, practicals %d)" % (n, len(house.rooms), len(getattr(house, "practicals", []))))
