"""Procedural cars that hold up in a photograph: a quad control cage lofted through cross-sections along the
length, smoothed with two levels of Catmull-Clark, wheel arches cut with booleans, tyres and rims, glass band,
lights, grille, mirrors. Local axes: +Y forward, X across, Z up; feet in, metres out.

    build_car(stager, e) -> [objects]   e: pos [x,y,z] (floor, centre of footprint), kind sedan|suv|roadster,
                                        rot_z, m (paint), covered (fabric cover), length/width/height overrides
"""
import math
import bmesh
import bpy
from mathutils import Vector, Matrix

from geom import m, get_collection, box_ft, cylinder_ft

FT = 0.3048

# side-profile keys per kind: lists of (y, value) in feet at the reference size, linearly interpolated and
# sampled every ~0.7 ft into cage stations. z_top is the centre-line silhouette (deck, glass, roof, hood),
# z_belt the shoulder line, w_body the half width at the widest point, w_roof the half width at the roof edge.
KINDS = {
    "sedan": {
        "L": 15.5, "W": 6.1, "H": 4.7, "gc": 0.62, "wheel_r": 1.15, "wheelbase": 0.60, "wheel_x": 0.45,
        "z_top": [(-7.75, 2.7), (-6.8, 3.0), (-4.7, 3.12), (-4.4, 3.2), (-3.0, 4.45), (-2.4, 4.68), (-0.6, 4.72), (1.2, 4.6), (1.9, 4.3), (3.2, 3.25), (3.6, 3.1), (5.2, 2.95), (7.0, 2.72), (7.75, 2.4)],
        "z_belt": [(-7.75, 2.3), (-6.5, 2.5), (-4.0, 2.62), (0.0, 2.66), (3.5, 2.6), (6.0, 2.42), (7.75, 2.05)],
        "w_body": [(-7.75, 2.5), (-6.8, 2.85), (-5.0, 3.0), (-2.0, 3.06), (2.0, 3.06), (4.5, 2.98), (6.5, 2.8), (7.75, 2.45)],
        "w_roof": [(-7.75, 2.2), (-4.7, 2.55), (-4.4, 2.5), (-3.0, 2.25), (0.0, 2.3), (1.9, 2.25), (3.2, 2.5), (3.6, 2.55), (7.75, 2.15)],
        "side_glass": (-4.4, 3.2), "rear_glass": (-4.4, -3.0), "front_glass": (1.9, 3.2), "pillars": [(-3.0, -2.4), (-0.6, -0.2), (1.2, 1.9)],
        "doors": [-1.7, 1.9], "step": 0.7,
    },
    "suv": {
        "L": 15.8, "W": 6.4, "H": 5.7, "gc": 0.85, "wheel_r": 1.3, "wheelbase": 0.60, "wheel_x": 0.5,
        "z_top": [(-7.9, 3.5), (-7.6, 4.6), (-7.2, 5.45), (-6.4, 5.68), (-4.0, 5.72), (0.0, 5.7), (2.0, 5.6), (2.8, 5.3), (3.9, 3.85), (4.3, 3.65), (6.0, 3.5), (7.4, 3.3), (7.9, 2.85)],
        "z_belt": [(-7.9, 3.0), (-6.0, 3.1), (0.0, 3.12), (4.0, 3.05), (6.5, 2.9), (7.9, 2.45)],
        "w_body": [(-7.9, 2.7), (-7.0, 3.05), (-5.0, 3.2), (0.0, 3.22), (4.0, 3.15), (6.5, 2.95), (7.9, 2.6)],
        "w_roof": [(-7.9, 2.4), (-7.2, 2.6), (-6.4, 2.72), (0.0, 2.75), (2.8, 2.65), (3.9, 2.7), (7.9, 2.3)],
        "side_glass": (-7.2, 3.9), "rear_glass": (-7.6, -7.2), "front_glass": (2.8, 3.9), "pillars": [(-6.4, -6.0), (-1.6, -1.0), (2.0, 2.8)],
        "doors": [-1.6, 2.4], "step": 0.7,
    },
    "roadster": {
        "L": 14.5, "W": 5.6, "H": 4.0, "gc": 0.45, "wheel_r": 1.05, "wheelbase": 0.62, "wheel_x": 0.4,
        "z_top": [(-7.25, 2.15), (-6.4, 2.5), (-4.2, 2.7), (-3.2, 2.78), (-2.6, 3.3), (-2.0, 3.92), (-0.8, 4.0), (0.6, 3.8), (1.3, 3.2), (1.9, 2.75), (4.5, 2.5), (6.5, 2.25), (7.25, 1.95)],
        "z_belt": [(-7.25, 1.9), (-5.0, 2.25), (0.0, 2.4), (4.0, 2.25), (7.25, 1.7)],
        "w_body": [(-7.25, 2.3), (-6.0, 2.7), (-3.0, 2.8), (2.0, 2.8), (5.0, 2.65), (7.25, 2.3)],
        "w_roof": [(-7.25, 2.0), (-3.2, 2.4), (-2.0, 2.0), (0.6, 2.05), (1.9, 2.4), (7.25, 2.0)],
        "side_glass": (-3.2, 1.9), "rear_glass": (-3.2, -2.0), "front_glass": (0.6, 1.9), "pillars": [(-2.0, -1.6)],
        "doors": [0.4], "step": 0.6,
    },
}


def _interp(keys, y):
    if y <= keys[0][0]:
        return keys[0][1]
    for (ya, va), (yb, vb) in zip(keys, keys[1:]):
        if ya <= y <= yb:
            t = (y - ya) / max(yb - ya, 1e-9)
            return va + (vb - va) * t
    return keys[-1][1]


def _stations(K):
    """Sample y positions: every 'step' plus every key y (so silhouette corners are held)."""
    ys = set()
    y0, y1 = K["z_top"][0][0], K["z_top"][-1][0]
    y = y0
    while y < y1:
        ys.add(round(y, 3))
        y += K["step"]
    ys.add(y1)
    for k in ("z_top", "z_belt", "w_body", "w_roof"):
        for (yy, _) in K[k]:
            ys.add(round(yy, 3))
    for a, b in [K["side_glass"], K["rear_glass"], K["front_glass"]] + K["pillars"]:
        ys.add(round(a, 3))
        ys.add(round(b, 3))
    return sorted(ys)


def build_car(stager, e):
    kind = e.get("kind", "sedan")
    K = KINDS[kind]
    L, W, H = e.get("length", K["L"]), e.get("width", K["W"]), e.get("height", K["H"])
    sy, sx, sz = L / K["L"], W / K["W"], H / K["H"]
    gc = K["gc"] * sz
    p = e["pos"]
    rot = math.radians(e.get("rot_z", 0))
    covered = e.get("covered", False)
    col = stager.col
    paint = stager.mat("car_cover" if covered else e.get("m", "car_white"))
    glass = stager.mat("car_cover" if covered else "car_glass")
    parts = []

    # ---- body cage: rings of 12 verts per station (top centre, roof edge, shoulder, widest, rocker,
    # bottom edge, bottom centre, mirrored), lofted with quads, creased along the shoulder and the sill
    bm = bmesh.new()
    crease = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
    ys_ref = _stations(K)
    rings, ys = [], []
    for yr in ys_ref:
        zt, zb, wbdy, wrf = _interp(K["z_top"], yr) * sz, _interp(K["z_belt"], yr) * sz, _interp(K["w_body"], yr) * sx, _interp(K["w_roof"], yr) * sx
        wrf = min(wrf, wbdy - 0.05)
        zt = max(zt, zb + 0.12)
        right = [(0.0, zt), (wrf, zt - 0.05), (wbdy * 0.97, zb + 0.12), (wbdy, zb - 0.28), (wbdy * 0.985, gc + 0.42), (wbdy * 0.93, gc)]
        left = [(-x, z) for (x, z) in reversed(right[1:])]
        ring = right + [(0.0, gc)] + left
        y = yr * sy
        rings.append([bm.verts.new((m(x), m(y), m(z))) for (x, z) in ring])
        ys.append(yr)
    n = len(rings[0])
    faces_glass = []
    sg = K["side_glass"]; rg = K["rear_glass"]; fg = K["front_glass"]
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        ya, yb = ys[i], ys[i + 1]
        within = lambda span: span[0] - 1e-6 <= ya and yb <= span[1] + 1e-6
        in_pillar = any(within(p) for p in K["pillars"])
        for j in range(n):
            j2 = (j + 1) % n
            f = bm.faces.new((a[j], a[j2], b[j2], b[j]))
            if j in (1, 10) and within(sg) and not in_pillar:
                faces_glass.append(f)                      # side windows
            if j in (0, 11) and (within(rg) or within(fg)):
                faces_glass.append(f)                      # rear window, windshield
        # creases along the length: shoulder (verts 2/3 and 9/10 rings) and sill (5/7)
        for j, cval in ((2, 0.7), (3, 0.85), (9, 0.85), (10, 0.7), (5, 0.7), (7, 0.7), (1, 0.5), (11, 0.5)):
            ed = bm.edges.get((a[j], b[j]))
            if ed is not None:
                ed[crease] = cval
    # ring creases where the silhouette turns (deck to glass, glass to roof, cowl)
    hold = set()
    for span in (rg, fg):
        hold.add(round(span[0], 3)); hold.add(round(span[1], 3))
    for i, yr in enumerate(ys):
        if round(yr, 3) in hold:
            for j in range(n):
                ed = bm.edges.get((rings[i][j], rings[i][(j + 1) % n]))
                if ed is not None and j in (0, 1, 10, 11):
                    ed[crease] = 0.45
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("car_body_mesh")
    me.materials.append(paint)
    me.materials.append(glass)
    for f in bm.faces:
        f.material_index = 0
    for f in faces_glass:
        f.material_index = 1
    bm.to_mesh(me)
    bm.free()
    body = bpy.data.objects.new(stager.uid("car_cover_body" if covered else "car_body"), me)
    col.objects.link(body)
    for pg in me.polygons:
        pg.use_smooth = True
    sub = body.modifiers.new("subsurf", "SUBSURF")
    sub.levels = sub.render_levels = 2
    # wheel arches: boolean cylinders after the subdivision
    wb = L * K["wheelbase"]
    wr = K["wheel_r"] * sz
    arch_r = wr * 1.18
    cutters = []
    for syy in (-wb / 2, wb / 2):
        cut = cylinder_ft(stager.uid("car_arch_cut"), (-W / 2 - 0.2, syy, wr + 0.05), arch_r, W + 0.4, None, col, 32, axis="X")
        cut.hide_render = True
        cut.hide_viewport = True
        cut.display_type = "WIRE"
        boo = body.modifiers.new("arch", "BOOLEAN")
        boo.operation = "DIFFERENCE"
        boo.object = cut
        boo.solver = "EXACT"
        cutters.append(cut)
    parts.append(body)
    parts += cutters

    # ---- wheels: tyre, alloy rim with five spokes, hub. Each wheel's outer face sits at |x| = W/2 - wheel_x,
    # 0.8 ft of tyre inboard of it (mirrored per side, so both sides tuck equally into the arches)
    tire = stager.mat("tire")
    rim_m = stager.mat("alloy_dark")
    for syy in (-wb / 2, wb / 2):
        for sxx in (-W / 2 + K["wheel_x"], W / 2 - K["wheel_x"]):
            sgn = 1 if sxx > 0 else -1
            t = cylinder_ft(stager.uid("car_tire"), (sxx - sgn * 0.4, syy, wr), wr, 0.8, tire, col, 40, axis="X")
            r = cylinder_ft(stager.uid("car_rim"), (sxx - sgn * 0.37, syy, wr), wr * 0.64, 0.74, rim_m, col, 32, axis="X")
            hub = cylinder_ft(stager.uid("car_hub"), (sxx + sgn * 0.02, syy, wr), wr * 0.16, 0.06, stager.mat("chrome_dark"), col, 16, axis="X")
            parts += [t, r, hub]
            for k in range(5):
                a = math.radians(k * 72 + (0 if sxx > 0 else 36))
                x0s, x1s = sxx - 0.035, sxx + 0.035
                z0s, z1s = wr, wr + wr * 0.58
                spoke = box_ft(stager.uid("car_spoke"), x0s, syy - 0.09, x1s, syy + 0.09, z0s, z1s, stager.mat("chrome_dark"), col)
                cz = m((z0s + z1s) / 2)
                spoke.data.transform(Matrix.Translation((0, 0, m(wr) - cz)) @ Matrix.Rotation(a, 4, "X") @ Matrix.Translation((0, 0, cz - m(wr))))
                parts.append(spoke)

    if not covered:
        bh = _interp(K["z_belt"], K["z_belt"][-1][0]) * sz    # belt height at the nose
        zt_nose = _interp(K["z_top"], K["z_top"][-1][0]) * sz
        wn = _interp(K["w_body"], K["w_body"][-1][0]) * sx
        bh_mid = _interp(K["z_belt"], 0.0) * sz
        zt_tail = K["z_top"][0][1] * sz
        zb_tail = K["z_belt"][0][1] * sz
        w_tail = K["w_body"][0][1] * sx
        # headlights: slim glass strips wrapped at the front corners; tail lights red
        for s in (-1, 1):
            parts.append(box_ft(stager.uid("car_headlight"), s * wn * 0.25 - 0.55 * (s < 0), L / 2 - 0.12, s * wn * 0.25 + 0.55 * (s > 0), L / 2 + 0.06,
                                zt_nose - 0.55, zt_nose - 0.25, stager.mat("headlight"), col))
            parts.append(box_ft(stager.uid("car_taillight"), s * wn * 0.6 - 0.5, -L / 2 - 0.06, s * wn * 0.6 + 0.5, -L / 2 + 0.1,
                                zb_tail + 0.05, zt_tail - 0.12, stager.mat("taillight"), col))
            # mirrors on the A pillar
            my_ref = K["front_glass"][1] - 0.3
            my = my_ref * sy
            wsh = _interp(K["w_body"], my_ref) * sx * 0.97     # shoulder half-width at the A pillar: the mirror sits on the door there
            mz = _interp(K["z_belt"], my_ref) * sz + 0.05
            parts.append(box_ft(stager.uid("car_mirror"), min(s * (wsh + 0.05), s * (wsh + 0.42)), my - 0.3, max(s * (wsh + 0.05), s * (wsh + 0.42)), my + 0.3, mz, mz + 0.42, paint, col))
            parts.append(box_ft(stager.uid("car_mirror_arm"), min(s * (wsh - 0.25), s * (wsh + 0.12)), my - 0.06, max(s * (wsh - 0.25), s * (wsh + 0.12)), my + 0.06, mz + 0.1, mz + 0.22, paint, col))
            # door handles
            for hy in K["doors"]:
                hy2 = (hy - 1.1) * sy
                parts.append(box_ft(stager.uid("car_handle"), s * (W / 2) - 0.08, hy2 - 0.35, s * (W / 2) + 0.03, hy2 + 0.35, bh_mid - 0.3, bh_mid - 0.17, stager.mat("chrome_dark"), col))
        # grille and bumpers
        parts.append(box_ft(stager.uid("car_grille"), -wn * 0.45, L / 2 - 0.05, wn * 0.45, L / 2 + 0.04, gc + 0.55, zt_nose - 0.75, stager.mat("grille_black"), col))
        parts.append(box_ft(stager.uid("car_bumper"), -wn * 0.98, L / 2 - 0.1, wn * 0.98, L / 2 + 0.12, gc + 0.05, gc + 0.5, stager.mat("bumper_black"), col))
        parts.append(box_ft(stager.uid("car_bumper"), -w_tail * 0.98, -L / 2 - 0.12, w_tail * 0.98, -L / 2 + 0.1, gc + 0.05, gc + 0.5, stager.mat("bumper_black"), col))
        parts.append(box_ft(stager.uid("car_plate"), -0.5, -L / 2 - 0.14, 0.5, -L / 2 - 0.1, gc + 0.55, gc + 1.05, stager.mat("plate"), col))
        # door seams: thin dark lines cut as boxes proud by a hair
        for hy in K["doors"]:
            sy_line = hy * sy
            for s in (-1, 1):
                parts.append(box_ft(stager.uid("car_seam"), s * (W / 2) - 0.02, sy_line - 0.02, s * (W / 2) + 0.01, sy_line + 0.02, gc + 0.5, bh_mid + 0.05, stager.mat("seam_black"), col))
    # place
    base = Matrix.Translation((m(p[0]), m(p[1]), m(p[2]))) @ Matrix.Rotation(rot, 4, "Z")
    for ob in parts:
        # matrix_world is not evaluated yet for objects created this tick; compose from loc/rot/scale
        ob.matrix_world = base @ ob.matrix_basis
    return parts
