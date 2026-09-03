"""Estimate each seating model's forward direction from its geometry: the backrest is the tall part, its XY
centroid sits behind the seat centre, so forward is the opposite way. Prints the yaw (degrees, world, at
rot_z 0) of the forward direction, to set rot_z in the staging lists.

    blender -b -P tools/model_facing.py -- mid_century_lounge_chair dining_chair_02 ...
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
bpy.ops.wm.read_factory_settings(use_empty=True)
import staging  # noqa: E402


class _House:
    root = ROOT
    rooms = []
    room_by_name = {}
    floors = {}


st = staging.Stager.__new__(staging.Stager)
st.root = ROOT
st.protos = {}
st.counts = {"models": 0, "procedural": 0, "missing": 0}
from geom import get_collection  # noqa: E402
st.lib = get_collection("asset_lib")
st.col = get_collection("staging")
names = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for name in names:
    proto = st.load_proto(name)
    if proto is None:
        print("FACING", name, "missing")
        continue
    vs = [v.co for v in proto.data.vertices]
    zmax = max(v.z for v in vs)
    zmin = min(v.z for v in vs)
    cx = sum(v.x for v in vs) / len(vs)
    cy = sum(v.y for v in vs) / len(vs)
    top = [v for v in vs if v.z > zmin + (zmax - zmin) * 0.6]
    if not top:
        print("FACING", name, "flat")
        continue
    tx = sum(v.x for v in top) / len(top)
    ty = sum(v.y for v in top) / len(top)
    bx, by = tx - cx, ty - cy          # points toward the back
    fwd = math.degrees(math.atan2(-by, -bx))
    size = proto["size_m"]
    print("FACING %s forward_yaw=%.0f (back offset %.2f,%.2f m) size %.2fx%.2fx%.2f" % (name, fwd, bx, by, size[0], size[1], size[2]))
