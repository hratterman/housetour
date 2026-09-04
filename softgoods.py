"""Soft goods with real geometry.

Pillows, seat cushions and slabs, duvets with drops and a folded-back head, throws draped over an edge, towels
hung over a bar or folded in a stack, pleated curtains on a rod. Every piece is a grid mesh shaped by a height
field or a parametric drape, shaded smooth, smoothed once more by a subdivision modifier and given thickness by
a solidify modifier where the sheet is single-layer. Names start with sg_ so the bevel and cloth passes leave
them alone. All inputs in feet; meshes are built in the object's local frame (feet converted to metres) and the
object is placed with origin_ft / rot_z_deg, so a generator working in a rotated local frame (a bed, a sofa)
can build in that frame and hand the yaw to the object.
"""
import math
import random

import bpy
from mathutils import Euler, Matrix, Vector

from geom import link, m


# ----------------------------------------------------------------------------- mesh plumbing

def _object(name, verts, faces, mat, col, origin_ft=(0, 0, 0), rot_z_deg=0.0, subsurf=1, solidify=None,
            crease_boundary=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    if mat is not None:
        me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = tuple(m(v) for v in origin_ft)
    ob.rotation_euler = (0, 0, math.radians(rot_z_deg))
    link(ob, col)
    if solidify:
        so = ob.modifiers.new("sg_thick", "SOLIDIFY")
        so.thickness = m(solidify)
        so.offset = 1.0            # grow toward the normal (up / out)
        so.use_even_offset = True
        so.use_rim = True
    if subsurf:
        ss = ob.modifiers.new("sg_smooth", "SUBSURF")
        ss.levels = subsurf
        ss.render_levels = subsurf          # one level is enough on these grids; two blew the 15 GB build box
    return ob


def _grid(nu, nv):
    """Face list for a (nu+1) x (nv+1) vertex grid indexed i*(nv+1)+j."""
    faces = []
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            faces.append((a, a + nv + 1, a + nv + 2, a + 1))
    return faces


def _xform(verts_ft, center_ft, rot_euler):
    """Rotate local-frame feet coordinates about the origin, translate to center, convert to metres."""
    R = Euler(rot_euler, "XYZ").to_matrix()
    c = Vector(center_ft)
    return [tuple(m(v) for v in (R @ Vector(p) + c)) for p in verts_ft]


def _super_r(a, b, p):
    return (abs(a) ** p + abs(b) ** p) ** (1.0 / p)


# ----------------------------------------------------------------------------- pillows and slabs

def pillow(name, center_ft, size_ft, mat, col, rot=(0, 0, 0), origin_ft=(0, 0, 0), rot_z_deg=0.0, seed=0,
           puff=1.0, dent=0.0, n=12, bottom=0.7):
    """A stuffed pillow: domed top and bottom meeting at a seam, corners pinched in, a few soft creases.
    center is the pillow centre (mid-thickness), size (w, d, t) in its own frame before rot (radians)."""
    w, d, t = size_ft
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6.28) for _ in range(4)]
    verts = []
    top_idx = {}
    bot_idx = {}
    for i in range(n + 1):
        for j in range(n + 1):
            a = 2.0 * i / n - 1.0
            b = 2.0 * j / n - 1.0
            r = min(1.0, _super_r(a, b, 5.0))
            pinch = 1.0 - 0.09 * (a * b) ** 2
            x = a * w / 2 * pinch
            y = b * d / 2 * pinch
            dome = max(0.0, 1.0 - r * r) ** 0.42
            crease = 1.0 + 0.07 * math.sin(2.3 * a + ph[0]) * math.cos(1.7 * b + ph[1]) + 0.04 * math.sin(4.1 * b + ph[2])
            h = t / 2 * puff * dome * crease
            if dent:
                h -= t * dent * math.exp(-(a * a + b * b) * 3.0) * dome
            top_idx[(i, j)] = len(verts)
            verts.append((x, y, h))
    for i in range(n + 1):
        for j in range(n + 1):
            if i in (0, n) or j in (0, n):
                bot_idx[(i, j)] = top_idx[(i, j)]
                continue
            a = 2.0 * i / n - 1.0
            b = 2.0 * j / n - 1.0
            r = min(1.0, _super_r(a, b, 5.0))
            pinch = 1.0 - 0.09 * (a * b) ** 2
            dome = max(0.0, 1.0 - r * r) ** 0.42
            bot_idx[(i, j)] = len(verts)
            verts.append((a * w / 2 * pinch, b * d / 2 * pinch, -t / 2 * puff * bottom * dome))
    faces = []
    for i in range(n):
        for j in range(n):
            faces.append((top_idx[(i, j)], top_idx[(i + 1, j)], top_idx[(i + 1, j + 1)], top_idx[(i, j + 1)]))
            faces.append((bot_idx[(i, j)], bot_idx[(i, j + 1)], bot_idx[(i + 1, j + 1)], bot_idx[(i + 1, j)]))
    return _object(name, _xform(verts, center_ft, rot), faces, mat, col, origin_ft, rot_z_deg, subsurf=1)


def slab(name, center_ft, size_ft, mat, col, rot=(0, 0, 0), origin_ft=(0, 0, 0), rot_z_deg=0.0, seed=0,
         puff=0.12, edge=8.0, n=10, sag=0.0):
    """A flat cushion or folded textile: flat top with rounded edges, a little puff, optional sag in the middle
    (a sat-on seat). center is mid-thickness; size (w, d, t)."""
    w, d, t = size_ft
    rng = random.Random(seed)
    ph = rng.uniform(0, 6.28)
    verts = []
    top_idx = {}
    bot_idx = {}
    for i in range(n + 1):
        for j in range(n + 1):
            a = 2.0 * i / n - 1.0
            b = 2.0 * j / n - 1.0
            r = min(1.0, _super_r(a, b, 6.0))
            rim = max(0.0, 1.0 - r ** edge) ** 0.5
            h = t / 2 * rim * (1.0 + puff * (1.0 - r * r) + 0.02 * math.sin(3.0 * a + ph) * math.cos(2.0 * b))
            if sag:
                h -= t * sag * math.exp(-(a * a + b * b) * 2.0)
            top_idx[(i, j)] = len(verts)
            verts.append((a * w / 2, b * d / 2, h))
    for i in range(n + 1):
        for j in range(n + 1):
            if i in (0, n) or j in (0, n):
                bot_idx[(i, j)] = top_idx[(i, j)]
                continue
            a = 2.0 * i / n - 1.0
            b = 2.0 * j / n - 1.0
            r = min(1.0, _super_r(a, b, 6.0))
            rim = max(0.0, 1.0 - r ** edge) ** 0.5
            bot_idx[(i, j)] = len(verts)
            verts.append((a * w / 2, b * d / 2, -t / 2 * rim))
    faces = []
    for i in range(n):
        for j in range(n):
            faces.append((top_idx[(i, j)], top_idx[(i + 1, j)], top_idx[(i + 1, j + 1)], top_idx[(i, j + 1)]))
            faces.append((bot_idx[(i, j)], bot_idx[(i, j + 1)], bot_idx[(i + 1, j + 1)], bot_idx[(i + 1, j)]))
    return _object(name, _xform(verts, center_ft, rot), faces, mat, col, origin_ft, rot_z_deg, subsurf=1)


# ----------------------------------------------------------------------------- duvets

def duvet(name, rect_ft, z_top, drops, thick, mat, col, origin_ft=(0, 0, 0), rot_z_deg=0.0, seed=0,
          corner_r=0.22, waves=0.035, lumps=0.03):
    """Duvet over a mattress top rect (x0, y0, x1, y1) at z_top, hanging down the sides named in drops
    ({'-x': ft, '+x': ft, '-y': ft, '+y': ft}; a side missing gets no overhang). Single surface plus solidify."""
    x0, y0, x1, y1 = rect_ft
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6.28) for _ in range(6)]
    dxm = drops.get("-x", 0.0)
    dxp = drops.get("+x", 0.0)
    dym = drops.get("-y", 0.0)
    dyp = drops.get("+y", 0.0)
    arc = corner_r * math.pi / 2
    X0 = x0 - (arc + dxm if dxm else 0.0)
    X1 = x1 + (arc + dxp if dxp else 0.0)
    Y0 = y0 - (arc + dym if dym else 0.0)
    Y1 = y1 + (arc + dyp if dyp else 0.0)
    nu = max(16, int((X1 - X0) / 0.2))
    nv = max(16, int((Y1 - Y0) / 0.2))
    verts = []
    for i in range(nu + 1):
        X = X0 + (X1 - X0) * i / nu
        for j in range(nv + 1):
            Y = Y0 + (Y1 - Y0) * j / nv
            bx = min(max(X, x0), x1)
            by = min(max(Y, y0), y1)
            sx = X - bx          # signed overhang
            sy = Y - by
            s = max(abs(sx), abs(sy))
            along = (Y if abs(sx) >= abs(sy) else X)
            if s <= 1e-6:
                u = (X - x0) / max(x1 - x0, 1e-6)
                v = (Y - y0) / max(y1 - y0, 1e-6)
                z = z_top + lumps * (math.sin(5.1 * u + ph[0]) * math.cos(3.7 * v + ph[1]) + 0.6 * math.sin(9.3 * v + ph[2]) * math.cos(6.1 * u + ph[3])) \
                    + 0.5 * lumps * (1.0 - (2 * u - 1) ** 2) * (1.0 - (2 * v - 1) ** 2)
                verts.append((X, Y, z))
                continue
            dx = (sx / s) if abs(sx) >= abs(sy) else 0.0
            dy = (sy / s) if abs(sy) > abs(sx) else 0.0
            if abs(sx) >= abs(sy) and abs(sy) > 0.5 * s:
                dx, dy = sx / s * 0.75, sy / s * 0.75     # corner: fold outward diagonally
            if s <= arc:
                th = s / corner_r
                off = corner_r * math.sin(th)
                z = z_top - corner_r * (1 - math.cos(th))
            else:
                hang = s - arc
                sway = waves * math.sin(2 * math.pi * along / 0.9 + ph[4]) * min(1.0, hang / 0.6) + 0.01 * hang
                off = corner_r + sway
                z = z_top - corner_r - hang
            verts.append((bx + dx * off, by + dy * off, z))
    faces = _grid(nu, nv)
    return _object(name, [tuple(m(c) for c in p) for p in verts], faces, mat, col, origin_ft, rot_z_deg,
                   subsurf=1, solidify=thick)


def duvet_fold(name, u0, u1, edge, depth, z_top, thick, mat, col, axis="y", toward=-1, origin_ft=(0, 0, 0),
               rot_z_deg=0.0, seed=0):
    """The head end of a made duvet folded back over itself: a plump roll along `edge` (a coordinate on
    `axis`) whose flap lies `depth` back over the body on the `toward` side (+1/-1 along axis). u0..u1 is the
    width across. A strip: the flap on top (rising from the body to the roll), the half-turn, a short return."""
    rng = random.Random(seed)
    ph = rng.uniform(0, 6.28)
    R = 0.8 * thick
    nu = max(10, int((u1 - u0) / 0.25))
    path = []
    steps = 8
    for k in range(steps + 1):
        f = k / steps                                  # 0 inner end of the flap, 1 at the turn
        path.append((edge + toward * depth * (1 - f), z_top + thick * (1.05 + 0.55 * f * f)))
    for k in range(1, 9):
        a = math.pi / 2 - math.pi * k / 8              # top of the roll round to the bottom
        path.append((edge - toward * R * math.cos(a), z_top + R + R * math.sin(a)))
    for k in range(1, 4):
        path.append((edge + toward * 0.35 * k / 3, z_top + 0.01))
    nv = len(path) - 1
    verts = []
    for i in range(nu + 1):
        u = u0 + (u1 - u0) * i / nu
        wob = 0.02 * math.sin(2 * math.pi * (u - u0) / 1.1 + ph)
        for (along, z) in path:
            if axis == "y":
                verts.append((u, along, z + wob))
            else:
                verts.append((along, u, z + wob))
    faces = _grid(nu, nv)
    return _object(name, [tuple(m(c) for c in p) for p in verts], faces, mat, col, origin_ft, rot_z_deg,
                   subsurf=1, solidify=thick * 0.5)


# ----------------------------------------------------------------------------- throws and towels

def drape(name, p0_ft, p1_ft, outward, top_len, hang_len, thick, mat, col, edge_r=0.12, waves=0.04,
          origin_ft=(0, 0, 0), rot_z_deg=0.0, seed=0, flare=0.03):
    """A textile draped over a horizontal edge from p0 to p1 (the edge line, at the top surface height):
    `top_len` lies flat on the inside, the fabric turns over a radius edge_r and hangs `hang_len` outside.
    outward is the horizontal unit direction away from the surface. Waves grow with the hang."""
    p0 = Vector(p0_ft)
    p1 = Vector(p1_ft)
    W = (p1 - p0).length
    ud = (p1 - p0) / max(W, 1e-6)
    od = Vector((outward[0], outward[1], 0.0)).normalized()
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6.28) for _ in range(3)]
    arc = edge_r * math.pi / 2
    total = top_len + arc + hang_len
    nu = max(8, int(W / 0.15))
    nv = max(12, int(total / 0.12))
    verts = []
    for i in range(nu + 1):
        u = i / nu
        base = p0 + ud * (W * u)
        for j in range(nv + 1):
            s = total * j / nv - top_len
            if s <= 0:
                off, z = s, 0.005 * math.sin(6 * u + ph[0])
            elif s <= arc:
                th = s / edge_r
                off, z = edge_r * math.sin(th), -edge_r * (1 - math.cos(th))
            else:
                hang = s - arc
                fr = min(1.0, hang / max(hang_len, 1e-6))
                sway = waves * fr * math.sin(2 * math.pi * u * W / 0.45 + ph[1]) + flare * fr * fr
                off, z = edge_r + sway, -edge_r - hang
            p = base + od * off + Vector((0, 0, z))
            verts.append((p.x, p.y, p.z))
    faces = _grid(nu, nv)
    return _object(name, [tuple(m(c) for c in p) for p in verts], faces, mat, col, origin_ft, rot_z_deg,
                   subsurf=1, solidify=thick)


def towel_hung(name, bar_center_ft, bar_axis, bar_r, width, front_drop, back_drop, wall_dir, mat, col,
               origin_ft=(0, 0, 0), rot_z_deg=0.0, seed=0, thick=0.035):
    """A towel over a round bar. bar_axis 'x' or 'y' is the bar's direction; wall_dir is the horizontal unit
    direction from the bar toward the wall (the short back drop hangs on that side)."""
    cx, cy, cz = bar_center_ft
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6.28) for _ in range(3)]
    R = bar_r + thick * 0.6
    wd = Vector((wall_dir[0], wall_dir[1], 0.0)).normalized()
    ad = Vector((1, 0, 0)) if bar_axis == "x" else Vector((0, 1, 0))
    nu = max(8, int(width / 0.12))
    path = []                                   # (n, z): n along -wd (toward the room)
    steps_b = max(4, int(back_drop / 0.1))
    for k in range(steps_b + 1):
        f = k / steps_b
        path.append((-R, cz - back_drop * (1 - f)))
    for k in range(1, 12):
        a = math.pi - math.pi * k / 12
        path.append((-R * math.cos(a), cz + R * math.sin(a)))
    steps_f = max(6, int(front_drop / 0.1))
    for k in range(1, steps_f + 1):
        f = k / steps_f
        path.append((R + 0.05 * f * f, cz - front_drop * f))
    nv = len(path) - 1
    verts = []
    for i in range(nu + 1):
        u = i / nu
        base = Vector((cx, cy, 0)) + ad * (width * (u - 0.5))
        for (nn, z) in path:
            hang = max(0.0, cz - z)
            sway = 0.018 * math.sin(2 * math.pi * u * width / 0.5 + ph[0]) * min(1.0, hang / 0.5) if nn > 0 else 0.0
            p = base - wd * (nn + sway)
            verts.append((p.x, p.y, z))
    faces = _grid(nu, nv)
    return _object(name, [tuple(m(c) for c in p) for p in verts], faces, mat, col, origin_ft, rot_z_deg,
                   subsurf=1, solidify=thick)


def towel_stack(name, center_ft, w, d, count, mat, col, layer=0.11, origin_ft=(0, 0, 0), rot_z_deg=0.0,
                seed=0, mats=None):
    """Folded towels stacked on a shelf or bench, each a rounded slab, a touch of yaw and offset per layer."""
    rng = random.Random(seed)
    objs = []
    for k in range(count):
        mk = (mats[k % len(mats)] if mats else mat)
        c = (center_ft[0] + rng.uniform(-0.03, 0.03), center_ft[1] + rng.uniform(-0.03, 0.03),
             center_ft[2] + layer * (k + 0.5))
        objs.append(slab(name, c, (w, d, layer), mk, col, rot=(0, 0, math.radians(rng.uniform(-4, 4))),
                         origin_ft=origin_ft, rot_z_deg=rot_z_deg, seed=seed + k, puff=0.25, edge=5.0, n=8))
    return objs


# ----------------------------------------------------------------------------- curtains

def curtain(name, u0, u1, at, face_dir, z_top, z_bot, mat, col, out=0.35, amp=0.11, period=0.52, seed=0,
            axis="x", thick=0.02):
    """A pleated curtain panel hanging beside a window. The wall runs along `axis` at coordinate `at`
    (finished face); face_dir is +1/-1, the side of the wall the room is on; the panel hangs `out` from the
    wall from u0 to u1 along the wall. Pleats are tighter at the top and fuller at the hem."""
    rng = random.Random(seed)
    ph = rng.uniform(0, 6.28)
    W = u1 - u0
    nu = max(24, int(W / (period / 6)))
    nv = 14
    verts = []
    for i in range(nu + 1):
        u = u0 + W * i / nu
        for j in range(nv + 1):
            v = j / nv                      # 0 top, 1 hem
            a = amp * (0.45 + 0.55 * v)
            n = out + a * math.sin(2 * math.pi * (u - u0) / period + ph) + 0.01 * math.sin(7 * v + ph)
            z = z_top - (z_top - z_bot) * v
            if axis == "x":
                verts.append((u, at + face_dir * n, z))
            else:
                verts.append((at + face_dir * n, u, z))
    faces = _grid(nu, nv)
    return _object(name, [tuple(m(c) for c in p) for p in verts], faces, mat, col, subsurf=1, solidify=thick)


# ----------------------------------------------------------------------------- garments

def garment(name, top_ft, facing, w, h, t, mat, col, seed=0, hanger=True, origin_ft=(0, 0, 0), rot_z_deg=0.0,
            hanger_mat=None, n_u=12, n_v=16):
    """A coat or shirt hanging from a point: top_ft is the shoulder top (the hook or rod), facing the horizontal
    unit direction the front faces; width w across (shoulders), height h down to the hem, thickness t at the
    shoulders tapering to the hem. Rounded shoulders, a neck notch, soft vertical folds. Front and back sheets
    meet at the sides. hanger adds a brass hook above the neck."""
    fx, fy = facing
    ln = math.hypot(fx, fy) or 1.0
    fx, fy = fx / ln, fy / ln
    sx, sy = -fy, fx                          # across the body
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6.28) for _ in range(3)]
    tx, ty, tz = top_ft
    verts = []
    idx = {}
    for side in (1, -1):                       # 1 front, -1 back
        for i in range(n_u + 1):
            u = i / n_u
            a = 2 * u - 1
            for j in range(n_v + 1):
                v = j / n_v                    # 0 top, 1 hem
                width = w * (0.72 + 0.28 * v) if v > 0.12 else w * (0.72 * math.sqrt(max(0.0, 1 - ((0.12 - v) / 0.12) ** 2)) + 0.05)
                if v <= 0.06 and abs(a) < 0.25:
                    width *= 1.0
                dome = math.sqrt(max(0.0, 1 - a * a)) if v > 0.12 else math.sqrt(max(0.0, 1 - a * a)) * (0.4 + 0.6 * v / 0.12)
                thick = t * (1.0 - 0.55 * v) * dome
                fold = 0.035 * math.sin(2 * math.pi * (u * 3.0) + ph[0]) * v + 0.02 * math.sin(2 * math.pi * (u * 5.0) + ph[1]) * v * v
                neck = 0.0
                if v < 0.1 and abs(a) < 0.3:
                    neck = 0.08 * (1 - v / 0.1) * (1 - (a / 0.3) ** 2)
                off = side * (thick / 2 + fold)
                px = tx + sx * (a * width / 2) + fx * off
                py = ty + sy * (a * width / 2) + fy * off
                pz = tz - h * v - neck
                idx[(side, i, j)] = len(verts)
                verts.append((px, py, pz))
    faces = []
    for side in (1, -1):
        for i in range(n_u):
            for j in range(n_v):
                q = (idx[(side, i, j)], idx[(side, i + 1, j)], idx[(side, i + 1, j + 1)], idx[(side, i, j + 1)])
                faces.append(q if side == 1 else tuple(reversed(q)))
    # close the sides and the hem between the two sheets
    for j in range(n_v):
        faces.append((idx[(1, 0, j)], idx[(1, 0, j + 1)], idx[(-1, 0, j + 1)], idx[(-1, 0, j)]))
        faces.append((idx[(1, n_u, j + 1)], idx[(1, n_u, j)], idx[(-1, n_u, j)], idx[(-1, n_u, j + 1)]))
    for i in range(n_u):
        faces.append((idx[(1, i + 1, n_v)], idx[(1, i, n_v)], idx[(-1, i, n_v)], idx[(-1, i + 1, n_v)]))
        faces.append((idx[(1, i, 0)], idx[(1, i + 1, 0)], idx[(-1, i + 1, 0)], idx[(-1, i, 0)]))
    ob = _object(name, [tuple(m(c) for c in p) for p in verts], faces, mat, col, origin_ft, rot_z_deg, subsurf=1)
    out = [ob]
    if hanger:
        from geom import cylinder_ft
        out.append(cylinder_ft(name + "_hanger", (tx, ty, tz - 0.05), 0.025, 0.42, hanger_mat or mat, col, 8))
        out[-1].name = name + "_hook"
        bar = cylinder_ft(name + "_bar", (tx - sx * w * 0.36, ty - sy * w * 0.36, tz - 0.06), 0.02, w * 0.72, hanger_mat or mat, col, 8,
                          axis=("X" if abs(sx) > abs(sy) else "Y"))
        out.append(bar)
    return out
