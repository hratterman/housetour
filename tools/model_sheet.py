"""Render a thumbnail of every model in assets/models (or a list) on a grey ground, then tile them into
contact sheets with names, so a model can be judged before it goes into the staging.

    blender -b -P tools/model_sheet.py -- [--out renders/model_sheet] [--only a,b,c] [--size 320]
    python3 tools/model_sheet.py --tile renders/model_sheet     # tile the thumbnails into sheets (Pillow)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse(argv):
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.join(HERE, "renders", "model_sheet"))
    p.add_argument("--only", default="")
    p.add_argument("--size", type=int, default=320)
    p.add_argument("--tile", default="")
    return p.parse_args(argv)


def tile(out):
    from PIL import Image, ImageDraw
    files = sorted(f for f in os.listdir(out) if f.endswith(".png") and not f.startswith("sheet_"))
    per = 20
    for si in range(0, len(files), per):
        chunk = files[si:si + per]
        cols = 5
        rows = math.ceil(len(chunk) / cols)
        w, h = 320, 260
        sheet = Image.new("RGB", (cols * w, rows * h), (40, 40, 40))
        d = ImageDraw.Draw(sheet)
        for i, f in enumerate(chunk):
            im = Image.open(os.path.join(out, f)).convert("RGB").resize((w, 240))
            x, y = (i % cols) * w, (i // cols) * h
            sheet.paste(im, (x, y))
            d.text((x + 4, y + 242), f[:-4], fill=(230, 230, 230))
        path = os.path.join(out, "sheet_%02d.png" % (si // per))
        sheet.save(path)
        print("wrote", path, len(chunk))


def main_blender(args):
    import bpy
    from mathutils import Vector
    os.makedirs(args.out, exist_ok=True)
    names = sorted(os.listdir(os.path.join(HERE, "assets", "models")))
    if args.only:
        names = [n for n in names if n in args.only.split(",")]
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = args.size
    scene.render.resolution_y = int(args.size * 0.75)
    scene.view_settings.view_transform = "AgX"
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    # ground, sun, sky
    bpy.ops.mesh.primitive_plane_add(size=40)
    ground = bpy.context.object
    gm = bpy.data.materials.new("ground")
    gm.diffuse_color = (0.45, 0.45, 0.45, 1)
    ground.data.materials.append(gm)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    scene.collection.objects.link(sun)
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.7, 0.75, 0.8, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    scene.world = w
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.lens = 40
    for name in names:
        out_png = os.path.join(args.out, name + ".png")
        if os.path.exists(out_png):
            continue
        gl = os.path.join(HERE, "assets", "models", name, name + ".gltf")
        if not os.path.exists(gl):
            gls = [f for f in os.listdir(os.path.join(HERE, "assets", "models", name)) if f.endswith((".gltf", ".glb"))]
            if not gls:
                continue
            gl = os.path.join(HERE, "assets", "models", name, gls[0])
        before = set(bpy.data.objects)
        try:
            bpy.ops.import_scene.gltf(filepath=gl)
        except Exception as e:
            print("import failed", name, e)
            continue
        new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == "MESH"]
        if not meshes:
            for o in new:
                bpy.data.objects.remove(o, do_unlink=True)
            continue
        bpy.context.view_layer.update()
        lo = Vector((1e9, 1e9, 1e9))
        hi = Vector((-1e9, -1e9, -1e9))
        for o in meshes:
            for c in o.bound_box:
                p = o.matrix_world @ Vector(c)
                lo = Vector(map(min, lo, p))
                hi = Vector(map(max, hi, p))
        size = max(hi - lo)
        centre = (lo + hi) / 2
        # drop to the ground
        for o in new:
            if o.parent is None:
                o.location.z -= lo.z
        centre.z -= lo.z
        dist = size * 2.1
        cam.location = centre + Vector((dist * 0.7, -dist * 0.75, dist * 0.45))
        direction = centre - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = out_png
        bpy.ops.render.render(write_still=True)
        print("[sheet]", name, "size %.2f m" % size, "parts", len(meshes), flush=True)
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)
        for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
            for b in list(block):
                if b.users == 0:
                    block.remove(b)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    a = parse(argv)
    if a.tile:
        tile(a.tile)
    else:
        main_blender(a)
