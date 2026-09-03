#!/usr/bin/env python3
"""Write a views file with one bird's-eye pose per room (camera in a top corner looking at the room centre),
for a furniture orientation and clipping audit:

    python3 tools/audit_views.py > /tmp/audit_views.json
    blender -b -P build_scene.py -- --views-file /tmp/audit_views.json --res 640x360 --samples 24 --out renders/audit
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
plan = json.load(open(os.path.join(os.path.dirname(HERE), "plan.json")))
floors = plan["floors"]
views = []
for r in plan["rooms"]:
    parts = r["parts"]
    x0 = min(p[0] for p in parts); y0 = min(p[1] for p in parts); x1 = max(p[2] for p in parts); y1 = max(p[3] for p in parts)
    fz = floors[r["floor"]]["z"]; h = floors[r["floor"]]["h"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # the corner of the largest part, 0.6 ft inside, just under the ceiling
    big = max(parts, key=lambda p: (p[2] - p[0]) * (p[3] - p[1]))
    corner = (big[0] + 1.4, big[1] + 1.4)     # inside the 1 ft exterior wall
    views.append({"name": "au_%s_%s" % (r["floor"], r["name"]), "pos": [corner[0], corner[1], fz + h - 1.3], "look": [cx, cy, fz + 1.2]})
    if (x1 - x0) * (y1 - y0) > 250:      # big rooms: a second corner
        views.append({"name": "au_%s_%s_b" % (r["floor"], r["name"]), "pos": [big[2] - 1.4, big[3] - 1.4, fz + h - 1.3], "look": [cx, cy, fz + 1.2]})
json.dump(views, sys.stdout)
print(len(views), "views", file=sys.stderr)
