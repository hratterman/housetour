"""Procedural house plants with real leaf geometry: a rubber plant (ficus), a monstera and a bird of paradise, each in a
pot. Leaves are curved grids (midrib sag, lateral fold, tip droop) so they catch light like leaves rather than flat cards.
Feet in, metres out, like the rest of the generators. Objects are named sg_* so the bevel pass leaves them alone."""
import math
import random

import bpy
from mathutils import Matrix, Vector

from geom import m, link, cylinder_ft, beam_between


def _leaf(name, base_ft, yaw_deg, tilt_deg, length, width, mat, col, kind="oval", sag=0.25, fold=0.18, droop=0.35,
          nu=14, nv=8, seed=0):
    """A leaf pointing from base_ft along yaw (about Z) and tilt (up from horizontal). kind: oval | monstera | paddle."""
    rng = random.Random(seed)
    verts, faces = [], []
    for i in range(nu + 1):
        u = i / nu
        if kind == "monstera":
            hw = width * 0.5 * (math.sin(math.pi * u) ** 0.55) * (1.0 + 0.35 * (1 - u) * (u < 0.25))
        elif kind == "paddle":
            hw = width * 0.5 * (math.sin(math.pi * min(1.0, u * 1.08)) ** 0.5)
        else:
            hw = width * 0.5 * (math.sin(math.pi * u) ** 0.7)
        x = u * length
        z_mid = -sag * length * u * u - droop * length * max(0.0, u - 0.6) ** 2 * 4
        for j in range(nv + 1):
            v = j / nv - 0.5
            y = v * 2 * hw
            z = z_mid - fold * abs(v) * 2 * hw + 0.02 * length * math.sin(6 * math.pi * u + v * 3) * (kind != "paddle")
            verts.append((m(x), m(y), m(z)))
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            if kind == "monstera":
                u = (i + 0.5) / nu
                v = abs((j + 0.5) / nv - 0.5) * 2
                # slits from the edge toward the midrib on every third column, past the first fifth of the length
                if 0.2 < u < 0.92 and v > 0.28 and (i % 3 == 1):
                    continue
            faces.append((a, a + 1, a + nv + 2, a + nv + 1))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for p in mesh.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, mesh)
    ob.matrix_world = Matrix.Translation(Vector(tuple(m(c) for c in base_ft))) @ Matrix.Rotation(math.radians(yaw_deg), 4, "Z") @ Matrix.Rotation(math.radians(-tilt_deg), 4, "Y")
    link(ob, col)
    if mat is not None:
        ob.data.materials.append(mat)
    sol = ob.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.0015
    sol.offset = 0.0
    return ob


def pot(name, pos_ft, r_top, h, mat, soil_mat, col):
    """Tapered pot: two stacked cylinders (a body and a rim), soil disc just under the rim."""
    x, y, z = pos_ft
    objs = [cylinder_ft(name + "_body", (x, y, z + h * 0.45), r_top * 0.85, h * 0.9, mat, col, 32),
            cylinder_ft(name + "_rim", (x, y, z + h * 0.94), r_top, h * 0.12, mat, col, 32),
            cylinder_ft(name + "_soil", (x, y, z + h * 0.86), r_top * 0.8, 0.02, soil_mat, col, 28)]
    objs[0].scale = (1.0, 1.0, 1.0)
    return objs


def ficus(uid, pos_ft, height, mats, col, seed=1):
    """Rubber plant: a single leaning trunk with two short branches, 18 to 30 dark glossy oval leaves getting bigger
    toward the top, pot about a fifth of the height."""
    rng = random.Random(seed)
    x, y, z = pos_ft
    ph = height * 0.18
    pr = height * 0.08
    objs = pot(uid("sg_pot"), pos_ft, pr, ph, mats["pot"], mats["soil"], col)
    top = z + height
    lean = rng.uniform(-6, 6)
    trunk_top = (x + 0.05 * (height - ph) * math.sin(math.radians(lean)), y, top - height * 0.05)
    objs.append(beam_between(uid("sg_trunk"), (x, y, z + ph * 0.8), trunk_top, 0.07, 0.07, mats["stem"], col))
    n = int(14 + height * 2.5)
    for k in range(n):
        t = 0.28 + 0.72 * (k / max(1, n - 1))          # position up the trunk
        tz = z + ph * 0.8 + (height - ph * 0.85) * t
        tx = x + (trunk_top[0] - x) * t
        yaw = k * 137.5 + rng.uniform(-10, 10)
        L = height * rng.uniform(0.13, 0.19) * (0.7 + 0.5 * math.sin(math.pi * min(1.0, t * 1.1)))
        tilt = rng.uniform(-25, 15) + 30 * (1 - t)
        base = (tx + 0.06 * math.cos(math.radians(yaw)), y + 0.06 * math.sin(math.radians(yaw)), tz)
        objs.append(beam_between(uid("sg_petiole"), (tx, y, tz), base, 0.02, 0.02, mats["stem"], col))
        objs.append(_leaf(uid("sg_leaf"), base, yaw, tilt, L, L * 0.5, mats["leaf"], col, "oval", sag=0.3, fold=0.22, droop=0.4, seed=k))
    return objs


def monstera(uid, pos_ft, height, mats, col, seed=2):
    """Monstera: a clump of long petioles from the soil fanning out, each with a big slit heart leaf; a moss pole."""
    rng = random.Random(seed)
    x, y, z = pos_ft
    ph = height * 0.2
    pr = height * 0.1
    objs = pot(uid("sg_pot"), pos_ft, pr, ph, mats["pot"], mats["soil"], col)
    objs.append(cylinder_ft(uid("sg_pole"), (x, y, z + ph + height * 0.32), 0.06, height * 0.65, mats["stem"], col, 12))
    n = int(7 + height)
    for k in range(n):
        yaw = k * 137.5 + rng.uniform(-12, 12)
        reach = height * rng.uniform(0.28, 0.5)
        h_top = z + ph + height * rng.uniform(0.3, 0.78)
        tip = (x + reach * math.cos(math.radians(yaw)), y + reach * math.sin(math.radians(yaw)), h_top)
        objs.append(beam_between(uid("sg_petiole"), (x + 0.1 * math.cos(math.radians(yaw)), y + 0.1 * math.sin(math.radians(yaw)), z + ph * 0.85), tip, 0.03, 0.03, mats["stem"], col))
        L = height * rng.uniform(0.28, 0.4)
        tilt = rng.uniform(-35, -5)
        objs.append(_leaf(uid("sg_leaf"), tip, yaw + rng.uniform(-15, 15), tilt, L, L * 0.85, mats["leaf_m"], col, "monstera", sag=0.2, fold=0.12, droop=0.3, nu=16, nv=10, seed=k))
    return objs


def bird_of_paradise(uid, pos_ft, height, mats, col, seed=3, fan_yaw=0.0):
    """Bird of paradise: tall petioles from a base clump, paddle leaves in one near-vertical fan plane."""
    rng = random.Random(seed)
    x, y, z = pos_ft
    ph = height * 0.16
    pr = height * 0.075
    objs = pot(uid("sg_pot"), pos_ft, pr, ph, mats["pot"], mats["soil"], col)
    n = int(7 + height * 1.2)
    for k in range(n):
        side = 1 if k % 2 == 0 else -1
        yaw = fan_yaw + side * rng.uniform(55, 100) + rng.uniform(-8, 8)
        frac = 0.45 + 0.55 * (k / max(1, n - 1))
        pl = height * frac * 0.62
        tilt = rng.uniform(58, 80) - 18 * frac
        tip = (x + pl * math.cos(math.radians(tilt)) * math.cos(math.radians(yaw)), y + pl * math.cos(math.radians(tilt)) * math.sin(math.radians(yaw)),
               z + ph * 0.85 + pl * math.sin(math.radians(tilt)))
        objs.append(beam_between(uid("sg_petiole"), (x + 0.05 * side, y, z + ph * 0.85), tip, 0.035, 0.035, mats["stem"], col))
        L = height * frac * 0.36
        objs.append(_leaf(uid("sg_leaf"), tip, yaw, tilt - 30 - rng.uniform(0, 15), L, L * 0.42, mats["leaf_b"], col, "paddle", sag=0.12, fold=0.2, droop=0.25, nu=12, nv=6, seed=k))
    return objs
