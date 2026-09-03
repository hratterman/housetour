"""Render the soft-goods primitives alone on a grey floor with the house materials, for a quick look.

    blender -b -P tools/sg_test.py -- [--out renders/sg_test.png]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

import softgoods as sg  # noqa: E402
from geom import box_ft, cylinder_ft, get_collection, m  # noqa: E402
import json  # noqa: E402
from materials_pbr import PBRLibrary  # noqa: E402


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(HERE, "renders", "sg_test.png")
    scene = bpy.context.scene
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    specs = json.load(open(os.path.join(HERE, "materials", "materials.json")))
    specs = specs.get("materials", specs)
    lib = PBRLibrary(HERE, specs)
    col = get_collection("sg")
    grey = lib.get("plaster_warm")
    wood = lib.get("walnut_h")
    box_ft("floor", -2, -2, 14, 10, -0.1, 0, lib.get("oak_floor"), col)
    box_ft("wall", -2, 9.75, 14, 10, 0, 9, grey, col)
    # a bench with a slab cushion and pillows leaning on the wall
    box_ft("bench", 0, 8.0, 5, 9.75, 0, 1.4, wood, col)
    sg.slab("sg_cush", (2.5, 8.9, 1.55), (4.9, 1.7, 0.3), lib.get("wool_mustard"), col, sag=0.08)
    for k, (x, mat) in enumerate(((0.9, "velvet_teal"), (2.4, "oxblood"), (3.9, "wool_oatmeal"))):
        sg.pillow("sg_pillow", (x, 9.2, 1.7 + 0.75), (1.5, 1.5, 0.4), lib.get(mat), col,
                  rot=(math.radians(68), 0, math.radians(-6 + 4 * k)), seed=k)
    sg.pillow("sg_pillow_flat", (4.2, 8.4, 1.7 + 0.2), (1.4, 1.4, 0.4), lib.get("velvet_orange"), col,
              rot=(0, 0, math.radians(20)), seed=7, dent=0.2)
    # a bed: platform, mattress, duvet with drops and a folded head, two pillows, throw at the foot
    box_ft("plat", 6.5, 1.0, 11.5, 8.0, 0, 1.2, wood, col)
    box_ft("matt", 6.7, 1.2, 11.3, 7.8, 1.2, 2.0, lib.get("linen_white"), col)
    sg.duvet("sg_duvet", (6.7, 1.2, 11.3, 5.9), 2.0, {"-x": 1.0, "+x": 1.0, "-y": 0.9}, 0.16, lib.get("linen_white"), col, seed=3)
    sg.duvet_fold("sg_fold", 6.6, 11.4, 5.9, 1.3, 2.0 + 0.03, 0.16, lib.get("linen_white"), col, axis="y", toward=-1)
    sg.pillow("sg_bp", (7.9, 7.0, 2.0 + 0.22), (2.2, 1.5, 0.45), lib.get("linen_white"), col, rot=(math.radians(12), 0, 0), seed=11)
    sg.pillow("sg_bp", (10.1, 7.0, 2.0 + 0.22), (2.2, 1.5, 0.45), lib.get("linen_white"), col, rot=(math.radians(15), 0, math.radians(3)), seed=12)
    sg.pillow("sg_bp2", (7.9, 6.6, 2.0 + 0.55), (1.8, 1.2, 0.4), lib.get("olive_paint"), col, rot=(math.radians(35), 0, 0), seed=13)
    sg.drape("sg_throw", (8.2, 1.2, 2.16), (11.0, 1.2, 2.16), (0, -1), 1.4, 1.1, 0.06, lib.get("wool_mustard"), col, seed=5)
    # towels: a bar with two hung towels, a folded stack
    cylinder_ft("bar", (12.5, 9.45, 4.0), 0.035, 2.0, lib.get("brass"), col, 10, axis="X")
    sg.towel_hung("sg_towel", (12.0, 9.45, 4.0), "x", 0.035, 0.9, 2.0, 0.6, (0, 1), lib.get("towel_white"), col, seed=1)
    sg.towel_hung("sg_towel", (13.0, 9.45, 4.0), "x", 0.035, 0.9, 1.7, 0.5, (0, 1), lib.get("wool_oatmeal"), col, seed=2)
    box_ft("shelf", 12.0, 9.0, 13.5, 9.75, 0, 1.0, wood, col)
    sg.towel_stack("sg_stack", (12.75, 9.35, 1.0), 1.2, 0.7, 4, lib.get("towel_white"), col, seed=4)
    # a curtain panel beside a window on the back wall
    box_ft("win", 5.6, 9.7, 6.4, 9.78, 3.0, 7.5, lib.get("glass"), col)
    sg.curtain("sg_curtain", 6.6, 8.0, 9.75, -1, 8.0, 0.25, lib.get("linen_white"), col, seed=2)
    cylinder_ft("rod", (7.0, 9.4, 8.1), 0.05, 3.2, lib.get("brass"), col, 10, axis="X")
    # light and camera
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(55), 0, math.radians(-40))
    scene.collection.objects.link(sun)
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.8, 0.85, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    scene.world = w
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.lens = 28
    cam.location = (m(6.0), m(-4.5), m(6.0))
    cam.rotation_euler = (math.radians(70), 0, math.radians(-4))
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.view_settings.view_transform = "AgX"
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("[sg_test] wrote", out)


main()
