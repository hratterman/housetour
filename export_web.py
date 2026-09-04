"""
export_web.py: build the staged house and export a walkable web version.

    blender -b -P export_web.py -- [--out web] [--tex 512] [--max-tris 30000]

Produces in the output directory:
    house.glb     geometry with baked material tiles (box-projected UVs generated here), models decimated
    lights.json   practical and fill lights (meters) for the viewer to place point lights
    plan_web.json rooms, floors, openings and teleport spots for the minimap and labels

Why bake: the render materials are procedural and world-space projected, which glTF cannot carry. Each material
is baked (diffuse color only, no lighting) onto one tile of its physical size, and every procedural mesh gets
UVs that reproduce the same world-space box projection, so the web version tiles exactly like the render.
"""
import argparse
import json
import math
import os
import re
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FT = 0.3048


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.join(HERE, "web"))
    p.add_argument("--tex", type=int, default=512, help="baked tile resolution")
    p.add_argument("--hero-tex", type=int, default=1024, help="tile resolution for floors and walnut")
    p.add_argument("--max-tris", type=int, default=30000, help="decimate imported models above this")
    p.add_argument("--model-tex", type=int, default=384, help="downscale imported model textures to this")
    p.add_argument("--no-draco", action="store_true", help="write uncompressed geometry")
    p.add_argument("--no-trees", action="store_true", help="skip exterior trees entirely")
    p.add_argument("--rebake", action="store_true", help="bake every material tile again instead of reusing <out>/_tiles")
    p.add_argument("--with-block", action="store_true", help="keep the neighbourhood (25 lots, 50 trees); default exports the house and its lot only")
    return p.parse_args(argv)


def log(*a):
    print("[web]", *a, flush=True)


# ---------------------------------------------------------------------------- build the scene

def build_scene(args):
    import build_scene as bs
    plan = json.load(open(os.path.join(HERE, "plan.json")))
    plan.setdefault("exterior", {})["procedural_trees"] = True
    staging = json.load(open(os.path.join(HERE, "staging.json")))
    heavy = {"island_tree_01", "fern_02", "shrub_02"}
    staging = [e for e in staging if e.get("asset") not in heavy]
    tmp_plan = os.path.join(args.out, "_plan_web.json")
    tmp_staging = os.path.join(args.out, "_staging_web.json")
    os.makedirs(args.out, exist_ok=True)
    json.dump(plan, open(tmp_plan, "w"))
    json.dump(staging, open(tmp_staging, "w"))
    sys.argv = ["blender", "--", "--plan", tmp_plan, "--staging", tmp_staging, "--shot", "none",
                "--stage", "phase2", "--no-blend", "--no-bevel"]
    bs.main()
    os.remove(tmp_plan)
    os.remove(tmp_staging)
    return plan


# ---------------------------------------------------------------------------- material baking

HERO = {"oak", "oak_deck", "walnut", "walnut_h", "terrazzo", "brick", "concrete", "rubber", "cedar"}


def tile_ft_for(spec):
    """Physical tile size to bake: the texture size, widened to cover overlay periods when reasonable."""
    sizes = []
    if spec.get("tex"):
        sizes.append(spec.get("size_ft", 4.0))
    ov = spec.get("overlay")
    if ov:
        sizes.append(ov.get("size_ft", 2.0))
    if not sizes:
        return None
    base = max(sizes)
    # small patterns: bake several repeats so the tile is 2 to 4 ft
    while base < 2.0:
        base *= 2
    return base


REBAKE = False
_BAKE_SCENE = None


def bake_scene():
    """A scene holding nothing but the bake plane. Baking in the house scene made Cycles synchronise all
    10,000 objects and every texture for each of ~150 tiles (25 s a tile, an hour an export)."""
    global _BAKE_SCENE
    if _BAKE_SCENE is None:
        sc = bpy.data.scenes.new("bake_scene")
        sc.render.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.cycles.samples = 1
        sc.render.bake.use_pass_direct = False
        sc.render.bake.use_pass_indirect = False
        sc.render.bake.use_pass_color = True
        sc.render.bake.margin = 2
        _BAKE_SCENE = sc
    return _BAKE_SCENE


def bake_tile(mat, tile_m, res, out_path):
    """Bake the diffuse color of a world-space material onto a plane of one tile, save JPEG.

    Tiles already in <out>/_tiles are reused (pass --rebake after changing materials.json)."""
    if os.path.exists(out_path) and not REBAKE:
        img = bpy.data.images.load(out_path)
        img.name = "bake_" + mat.name
        return img
    scene = bake_scene()
    mesh = bpy.data.meshes.new("bake_plane")
    h = tile_m / 2
    mesh.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)], [], [(0, 1, 2, 3)])
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for i, co in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = co
    ob = bpy.data.objects.new("bake_plane", mesh)
    scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    img = bpy.data.images.new("bake_" + mat.name, res, res, alpha=False)
    nt = mat.node_tree
    node = nt.nodes.new("ShaderNodeTexImage")
    node.image = img
    nt.nodes.active = node
    vl = scene.view_layers[0]
    vl.objects.active = ob
    ob.select_set(True, view_layer=vl)
    with bpy.context.temp_override(scene=scene, view_layer=vl, object=ob, active_object=ob, selected_objects=[ob],
                                   selected_editable_objects=[ob]):
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, use_clear=True)
    img.filepath_raw = out_path
    img.file_format = "JPEG"
    scene.render.image_settings.quality = 88
    img.save()
    nt.nodes.remove(node)
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return img


def web_material(name, spec, base_img, normal_img, tile_m):
    """Export-friendly Principled material: UV image textures only."""
    mat = bpy.data.materials.new("web_" + name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    rgb = spec.get("rgb", [0.8, 0.8, 0.8])
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = min(1.0, spec.get("rough", 0.5) + spec.get("rough_add", 0.0))
    bsdf.inputs["Metallic"].default_value = spec.get("metallic", 0.0)
    if spec.get("emit"):
        ec = spec.get("emit_rgb", rgb)
        bsdf.inputs["Emission Color"].default_value = (ec[0], ec[1], ec[2], 1.0)
        bsdf.inputs["Emission Strength"].default_value = min(spec["emit"], 6.0)
    if spec.get("transmission"):
        # glass as alpha blend for the web
        bsdf.inputs["Base Color"].default_value = (0.85, 0.92, 0.95, 1.0)
        bsdf.inputs["Alpha"].default_value = 0.18
        bsdf.inputs["Roughness"].default_value = 0.05
        mat.blend_method = "BLEND"
    if base_img is not None:
        uvn = nt.nodes.new("ShaderNodeUVMap")
        uvn.uv_map = "UVMap"
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = base_img
        nt.links.new(uvn.outputs[0], tex.inputs[0])
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if normal_img is not None:
        uvn2 = nt.nodes.new("ShaderNodeUVMap")
        uvn2.uv_map = "UVMap"
        ntex = nt.nodes.new("ShaderNodeTexImage")
        ntex.image = normal_img
        nt.links.new(uvn2.outputs[0], ntex.inputs[0])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = min(1.0, spec.get("bump", 0.6))
        nt.links.new(ntex.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    mat["tile_m"] = tile_m or 0.0
    return mat


_SCALED = {}


def scaled_copy(path, size, out_dir, quality=85, src_image=None):
    """Downscale an image into out_dir with Blender's image API (cached by source path). Returns the new path.
    Keeps PNG when the source carries alpha (leaf cut-outs), JPEG otherwise. src_image may be a packed image."""
    key = (os.path.abspath(path) if path else src_image.name, size)
    if key in _SCALED:
        return _SCALED[key]
    if src_image is not None:
        img = src_image.copy()
    else:
        img = bpy.data.images.load(path)
    if img.size[0] > size or img.size[1] > size:
        img.scale(size, size)
    # PNG only when the alpha channel is actually used (leaf and fern cut-outs); most model textures carry an
    # opaque alpha channel and went out as PNG, which was 20 MB of the 45 MB glb
    has_alpha = False
    if img.channels == 4 and img.file_format == "PNG":
        try:
            import numpy as np
            buf = np.empty(len(img.pixels), dtype=np.float32)
            img.pixels.foreach_get(buf)
            has_alpha = bool(buf[3::4].min() < 0.98)
        except Exception:
            has_alpha = True
    base = os.path.splitext(os.path.basename(path or src_image.name))[0]
    tag = os.path.basename(os.path.dirname(path)) if path else "packed"
    out = os.path.join(out_dir, "%s_%s_%d.%s" % (tag, base, size, "png" if has_alpha else "jpg"))
    img.filepath_raw = out
    img.file_format = "PNG" if has_alpha else "JPEG"
    bpy.context.scene.render.image_settings.quality = quality
    img.save()
    bpy.data.images.remove(img)
    _SCALED[key] = out
    return out


_LOADED = {}


def load_scaled(path, size, name, out_dir):
    """Load a downscaled copy of an image, shared across materials that use the same source."""
    p = scaled_copy(path, size, out_dir)
    if p in _LOADED:
        return _LOADED[p]
    img = bpy.data.images.load(p)
    img.name = name
    img.colorspace_settings.name = "Non-Color"
    _LOADED[p] = img
    return img


# ---------------------------------------------------------------------------- UVs

def box_uvs(ob, tile_m):
    """World-space box projection UVs for a mesh object, matching the render's Object-space projection."""
    me = ob.data
    if me.uv_layers:
        return False
    uv = me.uv_layers.new(name="UVMap")
    mw = ob.matrix_world
    inv = 1.0 / max(tile_m, 1e-6)
    normals = [mw.to_3x3() @ p.normal for p in me.polygons]
    for p, n in zip(me.polygons, normals):
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in p.loop_indices:
            w = mw @ me.vertices[me.loops[li].vertex_index].co
            if ax == 2:
                uv.data[li].uv = (w.x * inv, w.y * inv)
            elif ax == 0:
                uv.data[li].uv = (w.y * inv, w.z * inv)
            else:
                uv.data[li].uv = (w.x * inv, w.z * inv)
    return True


# ---------------------------------------------------------------------------- main

def main():
    args = parse()
    global REBAKE
    REBAKE = args.rebake
    t0 = time.time()
    plan = build_scene(args)
    import build_scene as bs
    if not args.with_block:
        # the viewer is about the house: drop the block (about 4,500 objects, most of the glTF's weight)
        col = bpy.data.collections.get("neighborhood")
        gone = 0
        if col is not None:
            for ob in list(col.all_objects):
                bpy.data.objects.remove(ob, do_unlink=True)
                gone += 1
        log("dropped %d neighbourhood objects (use --with-block to keep them)" % gone)
        # the block's parkway and lot trees are instanced outside that collection; keep only the ones on our lot
        # (48 imported trees were 180 MB of the glTF even after decimation)
        gone = 0
        for ob in list(bpy.data.objects):
            if ob.type == "MESH" and not ob.name.startswith("proto_") and re.match(r"(tree_small|island_tree|tree_)", ob.name):
                x, y = ob.matrix_world.translation.x / FT, ob.matrix_world.translation.y / FT
                if args.no_trees or not (-12 < x < 54 and -45 < y < 105):
                    bpy.data.objects.remove(ob, do_unlink=True)
                    gone += 1
        log("dropped %d trees off the lot" % gone)
    specs = json.load(open(os.path.join(HERE, "materials", "materials.json")))
    # art materials were added to specs at build time by staging; pull them from the live library
    live = None
    for o in bpy.data.objects:
        pass
    # find the Materials object through the module-level cache: rebuild specs from bpy materials' names
    tex_root = os.path.join(HERE, "assets", "textures")
    tiles_dir = os.path.join(args.out, "_tiles")
    os.makedirs(tiles_dir, exist_ok=True)

    # 1. collect materials used by procedural meshes (not imported models)
    proto_meshes = {o.data for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("proto_")}
    web_mats = {}
    n_baked = 0
    scene = bpy.context.scene
    old_engine = scene.render.engine
    for mat in list(bpy.data.materials):
        name = mat.name
        if name.startswith("web_") or name.startswith("bake_"):
            continue
        if name not in specs:
            # art_N materials come from staging; reconstruct a spec that says "bake me"
            if name.startswith("art_"):
                specs[name] = {"rgb": [0.8, 0.8, 0.8], "rough": 0.8, "overlay": {"type": "abstract_art", "size_ft": 2.0}}
            else:
                continue
        spec = specs[name]
        tile_ft = tile_ft_for(spec)
        base_img = normal_img = None
        tile_m = None
        if tile_ft:
            tile_m = tile_ft * FT
            res = args.hero_tex if name in HERO else (256 if name.startswith("art_") else args.tex)
            out_path = os.path.join(tiles_dir, name + ".jpg")
            if spec.get("tex") or spec.get("overlay"):
                base_img = bake_tile(mat, tile_m, res, out_path)
                n_baked += 1
            if spec.get("tex"):
                npath = os.path.join(tex_root, spec["tex"], "normal.jpg")
                if os.path.exists(npath):
                    # the normal tile period is size_ft; when the bake tile is larger, the UV still maps
                    # world coords / tile, so scale the normal image lookup by repeating it: bake tile is an
                    # integer multiple of size_ft in the common cases, otherwise accept the mismatch
                    normal_img = load_scaled(npath, min(args.tex, 512), "nrm_" + spec["tex"], tiles_dir)
        web_mats[name] = web_material(name, spec, base_img, normal_img, tile_m)
    scene.render.engine = old_engine
    log("baked %d material tiles" % n_baked)

    # 2. swap materials + generate UVs on procedural meshes
    n_uv = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.data in proto_meshes:
            continue
        if ob.users_collection and ob.users_collection[0].name == "asset_lib":
            continue
        if ob.name.startswith("proto_") or ob.data.users > 1:
            continue
        if not ob.data.materials:
            continue
        first = ob.data.materials[0]
        if first is None or first.name not in web_mats:
            continue
        tile = web_mats[first.name].get("tile_m", 0.0) or 1.2192
        if box_uvs(ob, tile):
            n_uv += 1
        for i, m in enumerate(ob.data.materials):
            if m is not None and m.name in web_mats:
                ob.data.materials[i] = web_mats[m.name]
    log("uv-mapped %d procedural meshes" % n_uv)
    # soft goods and plants carry subdivision for the render; one level is plenty at web scale (two levels
    # quadruple the triangle count again and took the glb from 27 MB to 45 MB)
    n_ss = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        for mod in ob.modifiers:
            if mod.type == "SUBSURF" and (mod.levels > 1 or mod.render_levels > 1):
                mod.levels = min(mod.levels, 1)
                mod.render_levels = min(mod.render_levels, 1)
                n_ss += 1
    log("capped subdivision on %d meshes" % n_ss)

    # 3. imported models: decimate every heavy mesh that will be exported (multi-part models and the site
    # trees included; the first version only looked at prototype meshes and let 270 MB of tool-chest curves
    # and tree leaves through), downscale their textures
    n_dec = 0
    users = {}
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name.startswith("proto_") or not ob.visible_get():
            continue
        if ob.users_collection and ob.users_collection[0].name == "asset_lib":
            continue
        users.setdefault(ob.data, []).append(ob)
    for me, obs in users.items():
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        if tris <= args.max_tris:
            continue
        # decimate the datablock once and share it, so instances stay instances in the glTF (a modifier per
        # object made the exporter write every tree separately)
        ob0 = obs[0]
        mod = ob0.modifiers.new("dec", "DECIMATE")
        mod.ratio = args.max_tris / tris
        mod.use_collapse_triangulate = True
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        new_me = bpy.data.meshes.new_from_object(ob0.evaluated_get(dg))
        new_me.name = me.name + "_dec"
        ob0.modifiers.remove(mod)
        for ob in obs:
            ob.data = new_me
        n_dec += 1
    for m in bpy.data.materials:
        if m is None or not m.use_nodes or m.name.startswith("web_"):
            continue
        if True:
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image is not None and n.image.size[0] > args.model_tex:
                    if n.image.name in _LOADED:
                        n.image = _LOADED[n.image.name]
                        continue
                    src = bpy.path.abspath(n.image.filepath) if n.image.filepath else ""
                    out = scaled_copy(src if os.path.exists(src) else None, args.model_tex, tiles_dir, src_image=n.image)
                    new = bpy.data.images.load(out)
                    new.colorspace_settings.name = n.image.colorspace_settings.name
                    _LOADED[n.image.name] = new
                    n.image = new
    log("decimated %d heavy model meshes" % n_dec)

    # 4. lights and plan for the viewer
    house = bs._HOUSE if hasattr(bs, "_HOUSE") else None
    lights = []
    for ob in bpy.data.objects:
        if ob.type != "LIGHT":
            continue
        L = ob.data
        if getattr(L.cycles, "is_portal", False) or L.type == "SUN":
            continue
        p = ob.matrix_world.translation
        lights.append({"name": ob.name, "type": L.type, "pos": [p.x, p.y, p.z], "color": list(L.color),
                       "watts": L.energy, "kind": "fill" if ob.name.startswith("fill_") else "practical"})
    sun = plan.get("sun", {"direction": [0.35, -0.55, -0.75]})
    json.dump({"lights": lights, "sun": sun, "lighting": plan.get("lighting", {})},
              open(os.path.join(args.out, "lights.json"), "w"))
    spots = [
        {"name": "Street", "pos": [11, -12, 5.5], "look": [11, 10]},
        {"name": "Vestibule", "pos": [11, 3, 5.5], "look": [11, 12]},
        {"name": "Spine", "pos": [25, 5, 5.5], "look": [25, 30]},
        {"name": "Kitchen", "pos": [18, 20, 5.5], "look": [4, 28]},
        {"name": "Living", "pos": [10, 32, 5.5], "look": [3, 44]},
        {"name": "Stair hall", "pos": [29.5, 12, 5.5], "look": [32, 2]},
        {"name": "Primary bedroom", "pos": [30, 44, 5.5], "look": [40, 32]},
        {"name": "Landing (2nd)", "pos": [32, 16, 15.5], "look": [24, 16]},
        {"name": "Lab", "pos": [20, 20, 15.5], "look": [12, 8]},
        {"name": "Loft", "pos": [18, 28, 15.5], "look": [18, 45]},
        {"name": "Gym", "pos": [20, 16, -4.5], "look": [4, 4]},
        {"name": "Lounge", "pos": [18, 42, -4.5], "look": [4, 32]},
        {"name": "Terrace", "pos": [14, 56, 5.3], "look": [9, 44]},
        {"name": "Garage", "pos": [6, 90, 5.1], "look": [4, 70]},
    ]
    json.dump({"rooms": plan["rooms"], "floors": plan["floors"], "openings": plan["openings"],
               "pits": plan.get("pits", []), "spots": spots, "units": "feet"},
              open(os.path.join(args.out, "plan_web.json"), "w"))

    # 5. export
    # hide helpers that should not ship
    for ob in bpy.data.objects:
        if ob.type in ("CAMERA", "EMPTY", "LIGHT"):
            ob.hide_viewport = True
            ob.hide_render = True
    glb = os.path.join(args.out, "house.glb")
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", export_apply=True, use_visible=True,
                              export_cameras=False, export_lights=False, export_animations=False,
                              export_image_format="JPEG", export_jpeg_quality=80,
                              export_texcoords=True, export_normals=True, export_materials="EXPORT",
                              export_yup=True,
                              # Draco cuts the geometry about six to one; the viewer decodes it with the vendored
                              # three.js decoder (web/vendor/three/libs/draco)
                              export_draco_mesh_compression_enable=not args.no_draco,
                              export_draco_mesh_compression_level=6, export_draco_position_quantization=14,
                              export_draco_normal_quantization=10, export_draco_texcoord_quantization=12)
    size = os.path.getsize(glb) / 1e6
    log("wrote %s (%.1f MB) in %.0fs" % (glb, size, time.time() - t0))
    import shutil
    # tiles stay in <out>/_tiles (gitignored) as the bake cache for the next export


if __name__ == "__main__":
    main()
