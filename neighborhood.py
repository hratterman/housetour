"""The block around the house: a North Shore village street (Wilmette / Winnetka / Evanston flavour).

Built from plan["site"]["neighborhood"]:
    street      curb line, street width, parkway and sidewalk widths, X extent
    lots        one entry per neighbouring lot: x0, x1, front_y, facing ("s" faces the street to the south,
                "n" faces north), style, optional colour choices, garage, driveway, trees
    street_trees, lamps, hydrants, fences
Everything is procedural boxes and prisms in the house materials library; trees use the CC0 models in
assets/models when present (island_tree_01/02, tree_small_02) and a clumped procedural crown otherwise.
The houses are low-to-mid detail period types: brick Georgian, clapboard colonial, Tudor, foursquare,
craftsman bungalow, 1950s ranch. They exist to frame the street, so they carry trim, sashes, shutters,
porches and chimneys but no interiors.
"""
import math
import os
import random

import bpy
from mathutils import Vector

from geom import (box_ft, prism_xz, prism_yz, cylinder_ft, sphere_ft, m, log, get_collection, link,
                  _mesh_from_pydata)

ROOT = os.path.dirname(os.path.abspath(__file__))
FT = 0.3048


class Frame:
    """Local house coordinates: u across the front (left to right seen from the street), v depth from the
    front wall into the lot, z up. facing 's' means the front wall faces south (our side of the street)."""

    def __init__(self, x0, front_y, facing):
        self.x0, self.fy, self.f = x0, front_y, (1 if facing == "s" else -1)

    def X(self, u):
        return self.x0 + u

    def Y(self, v):
        return self.fy + self.f * v


class Hood:
    def __init__(self, plan, house, mats, stager=None):
        self.plan = plan
        self.house = house
        self.mats = mats
        self.cfg = plan["site"]["neighborhood"]
        self.gz = plan["site"].get("grade_z", -0.5)
        self.col = get_collection("neighborhood")
        self.stager = stager
        self.rng = random.Random(self.cfg.get("seed", 1926))
        self.n = 0
        self.tree_n = 0

    # ------------------------------------------------------------------ primitives in a frame
    def box(self, fr, u0, v0, u1, v1, z0, z1, mat, name="nb"):
        X0, X1 = sorted((fr.X(u0), fr.X(u1)))
        Y0, Y1 = sorted((fr.Y(v0), fr.Y(v1)))
        self.n += 1
        return box_ft("%s_%d" % (name, self.n), X0, Y0, X1, Y1, z0, z1, mat, self.col)

    def gable(self, fr, u0, u1, v0, v1, ze, pitch, axis, over, mat, wall_mat, thick=0.7, rake=None):
        """Gable roof. axis 'u': ridge runs across the front (side-gabled); axis 'v': ridge runs front to back."""
        rake = over if rake is None else rake
        if axis == "u":
            half = (v1 - v0) / 2 + over
            zr = ze + pitch * half
            mid = (v0 + v1) / 2
            prof = [(fr.Y(v0 - over), ze), (fr.Y(mid), zr), (fr.Y(v1 + over), ze),
                    (fr.Y(v1 + over), ze - thick), (fr.Y(mid), zr - thick), (fr.Y(v0 - over), ze - thick)]
            X0, X1 = sorted((fr.X(u0 - rake), fr.X(u1 + rake)))
            self.n += 1
            prism_yz("nb_roof_%d" % self.n, prof, X0, X1, mat, self.col)
            # gable end walls
            wprof = [(fr.Y(v0), ze - 0.3), (fr.Y(v1), ze - 0.3), (fr.Y(mid), zr - thick + 0.05)]
            for uu in (u0, u1 - 1.0):
                Xa, Xb = sorted((fr.X(uu), fr.X(uu + 1.0)))
                self.n += 1
                prism_yz("nb_gend_%d" % self.n, wprof, Xa, Xb, wall_mat, self.col)
            return zr
        else:
            half = (u1 - u0) / 2 + over
            zr = ze + pitch * half
            mid = (u0 + u1) / 2
            prof = [(fr.X(u0 - over), ze), (fr.X(mid), zr), (fr.X(u1 + over), ze),
                    (fr.X(u1 + over), ze - thick), (fr.X(mid), zr - thick), (fr.X(u0 - over), ze - thick)]
            Y0, Y1 = sorted((fr.Y(v0 - rake), fr.Y(v1 + rake)))
            self.n += 1
            prism_xz("nb_roof_%d" % self.n, prof, Y0, Y1, mat, self.col)
            wprof = [(fr.X(u0), ze - 0.3), (fr.X(u1), ze - 0.3), (fr.X(mid), zr - thick + 0.05)]
            for vv in (v0, v1 - 1.0):
                Ya, Yb = sorted((fr.Y(vv), fr.Y(vv + 1.0)))
                self.n += 1
                prism_xz("nb_gend_%d" % self.n, wprof, Ya, Yb, wall_mat, self.col)
            return zr

    def hip(self, fr, u0, u1, v0, v1, ze, pitch, over, mat, thick=0.6):
        """Hip roof as a closed solid: rectangular base at the eave, ridge along the longer axis."""
        X0, X1 = sorted((fr.X(u0 - over), fr.X(u1 + over)))
        Y0, Y1 = sorted((fr.Y(v0 - over), fr.Y(v1 + over)))
        w, d = X1 - X0, Y1 - Y0
        half = min(w, d) / 2
        zr = ze + pitch * half
        if w >= d:
            ridge = [(X0 + half, (Y0 + Y1) / 2, zr), (X1 - half, (Y0 + Y1) / 2, zr)]
        else:
            ridge = [((X0 + X1) / 2, Y0 + half, zr), ((X0 + X1) / 2, Y1 - half, zr)]
        base = [(X0, Y0, ze), (X1, Y0, ze), (X1, Y1, ze), (X0, Y1, ze)]
        lower = [(x, y, ze - thick) for x, y, _ in base]
        verts = [tuple(m(c) for c in p) for p in base + ridge + lower]
        if w >= d:
            faces = [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4),
                     (6, 9, 8, 7), (0, 6, 7, 1), (1, 7, 8, 2), (2, 8, 9, 3), (3, 9, 6, 0)]
        else:
            faces = [(0, 1, 4), (1, 2, 5, 4), (2, 3, 5), (3, 0, 4, 5),
                     (6, 9, 8, 7), (0, 6, 7, 1), (1, 7, 8, 2), (2, 8, 9, 3), (3, 9, 6, 0)]
        self.n += 1
        mesh = _mesh_from_pydata("nb_hip_%d" % self.n, verts, faces)
        ob = bpy.data.objects.new("nb_hip_%d" % self.n, mesh)
        link(ob, self.col)
        if mat is not None:
            ob.data.materials.append(mat)
        return zr

    def mat(self, name):
        return self.mats.get(name)

    def window(self, fr, face, a, z, w, h, trim, glass, muntins=None, shutters=None, sill=True, depth_u=None):
        """Window on a wall face. face: 'front' (v=0), 'back' (v=D), 'left' (u=0), 'right' (u=W); a is the
        coordinate along the wall (u for front/back, v for left/right). depth_u carries D or W for the far faces."""
        t = 0.3   # trim width
        p = 0.12  # trim projection
        if face in ("front", "back"):
            v = 0.0 if face == "front" else depth_u
            s = -1 if face == "front" else 1        # outward direction in v
            def B(u0, u1, d0, d1, z0, z1, mat, nm):
                return self.box(fr, u0, v + s * d0, u1, v + s * d1, z0, z1, mat, nm)
        else:
            u = 0.0 if face == "left" else depth_u
            s = -1 if face == "left" else 1
            def B(a0, a1, d0, d1, z0, z1, mat, nm):
                return self.box(fr, u + s * d0, a0, u + s * d1, a1, z0, z1, mat, nm)
        a0, a1 = a - w / 2, a + w / 2
        if self.plan.get("_dusk") and self.rng.random() < 0.4:
            glass = self.mat("window_lit")
        B(a0, a1, -0.3, 0.02, z, z + h, glass, "nb_glass")            # glass, recessed 4 in
        B(a0 - t, a0, -0.02, p, z - 0.1, z + h + t, trim, "nb_trim")
        B(a1, a1 + t, -0.02, p, z - 0.1, z + h + t, trim, "nb_trim")
        B(a0 - t, a1 + t, -0.02, p, z + h, z + h + t, trim, "nb_trim")
        if sill:
            B(a0 - t - 0.1, a1 + t + 0.1, -0.02, p + 0.15, z - 0.25, z, trim, "nb_sill")
        if muntins:
            cols, rows = muntins
            for i in range(1, cols):
                uu = a0 + w * i / cols
                B(uu - 0.04, uu + 0.04, -0.25, -0.15, z, z + h, trim, "nb_muntin")
            for j in range(1, rows):
                zz = z + h * j / rows
                B(a0, a1, -0.25, -0.15, zz - 0.04, zz + 0.04, trim, "nb_muntin")
            B(a0, a1, -0.22, -0.1, z + h / 2 - 0.1, z + h / 2 + 0.1, trim, "nb_meeting")   # meeting rail
        if shutters:
            sw = min(1.25, w / 2)
            B(a0 - t - sw, a0 - t, -0.02, p + 0.05, z - 0.05, z + h + 0.05, shutters, "nb_shutter")
            B(a1 + t, a1 + t + sw, -0.02, p + 0.05, z - 0.05, z + h + 0.05, shutters, "nb_shutter")

    def door(self, fr, a, w, h, trim, leaf, step_n=2, trim_w=0.4, portico=None):
        self.box(fr, a - w / 2, -0.35, a + w / 2, 0.0, self.gz + 0.5, self.gz + 0.5 + h, leaf, "nb_door")
        z0 = self.gz + 0.5
        self.box(fr, a - w / 2 - trim_w, -0.15, a - w / 2, 0.0, z0, z0 + h + trim_w, trim, "nb_dtrim")
        self.box(fr, a + w / 2, -0.15, a + w / 2 + trim_w, 0.0, z0, z0 + h + trim_w, trim, "nb_dtrim")
        self.box(fr, a - w / 2 - trim_w, -0.15, a + w / 2 + trim_w, 0.0, z0 + h, z0 + h + trim_w, trim, "nb_dtrim")
        # steps down to grade
        for i in range(step_n):
            zz = z0 - (i + 1) * 0.5 / step_n * 1.0
            self.box(fr, a - w / 2 - 1.0, -(1.2 * (i + 1)), a + w / 2 + 1.0, -1.2 * i - 0.2, self.gz - 0.2, z0 - i * (0.5 / step_n), self.mats.get("concrete_sealed"), "nb_step")
        if portico:
            kind = portico.get("kind", "gable")
            pw = w + 4.0
            pd = 4.5
            cz = z0 + h + 1.2
            col = self.mats.get("trim_white")
            for uu in (a - pw / 2 + 0.4, a + pw / 2 - 0.4):
                self.box(fr, uu - 0.35, -pd + 0.4, uu + 0.35, -pd + 1.1, self.gz - 0.2, cz, col, "nb_pcol")
            self.box(fr, a - pw / 2, -pd, a + pw / 2, 0.2, cz, cz + 0.8, col, "nb_pbeam")
            if kind == "gable":
                self.gable(fr, a - pw / 2, a + pw / 2, -pd, 0.2, cz + 0.8, 0.5, "v", 0.3, self.mats.get(portico.get("m", "slate_roof")), col, thick=0.4, rake=0.3)
            else:
                self.box(fr, a - pw / 2 - 0.3, -pd - 0.3, a + pw / 2 + 0.3, 0.3, cz + 0.8, cz + 1.2, self.mats.get(portico.get("m", "slate_roof")), "nb_proof")

    def chimney(self, fr, u, v, w, d, z_top, mat):
        self.box(fr, u, v, u + w, v + d, self.gz, z_top, mat, "nb_chim")
        self.box(fr, u - 0.15, v - 0.15, u + w + 0.15, v + d + 0.15, z_top, z_top + 0.4, self.mats.get("concrete_sealed"), "nb_chimcap")
        self.box(fr, u + 0.4, v + 0.4, u + w - 0.4, v + d - 0.4, z_top + 0.4, z_top + 0.9, self.mats.get("shingle_dark"), "nb_flue")

    def porch(self, fr, u0, u1, depth, z_floor, z_roof, ncol, style, roof, roof_m, trim, deck_m=None, pier_m=None):
        deck = deck_m or self.mats.get("concrete_sealed")
        self.box(fr, u0, -depth, u1, 0.0, self.gz - 0.3, z_floor, deck, "nb_pdeck")
        # steps centred
        cw = 5.0
        cu = (u0 + u1) / 2
        for i in range(2):
            self.box(fr, cu - cw / 2, -depth - 1.1 * (i + 1), cu + cw / 2, -depth - 1.1 * i, self.gz - 0.3, z_floor - (i + 1) * (z_floor - self.gz) / 3, deck, "nb_pstep")
        # columns
        for i in range(ncol):
            uu = u0 + 0.8 + (u1 - u0 - 1.6) * i / max(ncol - 1, 1)
            if style == "tapered":
                pier = pier_m or self.mats.get("brick_red")
                self.box(fr, uu - 1.0, -depth + 0.2, uu + 1.0, -depth + 2.2, z_floor, z_floor + 3.0, pier, "nb_pier")
                self.box(fr, uu - 0.6, -depth + 0.6, uu + 0.6, -depth + 1.8, z_floor + 3.0, z_roof, trim, "nb_pcol")
            elif style == "brick":
                pier = pier_m or self.mats.get("brick_red")
                self.box(fr, uu - 0.8, -depth + 0.3, uu + 0.8, -depth + 1.9, z_floor, z_roof, pier, "nb_pier")
            else:
                self.box(fr, uu - 0.4, -depth + 0.5, uu + 0.4, -depth + 1.3, z_floor, z_roof, trim, "nb_pcol")
        # rail between columns (not in front of the steps)
        self.box(fr, u0 + 0.4, -depth + 0.7, cu - cw / 2, -depth + 1.0, z_floor + 2.6, z_floor + 2.9, trim, "nb_rail")
        self.box(fr, cu + cw / 2, -depth + 0.7, u1 - 0.4, -depth + 1.0, z_floor + 2.6, z_floor + 2.9, trim, "nb_rail")
        # beam + roof
        self.box(fr, u0 - 0.3, -depth - 0.2, u1 + 0.3, 0.3, z_roof, z_roof + 0.9, trim, "nb_pbeam")
        if roof == "hip":
            self.hip(fr, u0, u1, -depth, 0.2, z_roof + 0.9, 0.3, 1.2, roof_m)
        elif roof == "shed":
            zh = z_roof + 0.9 + 0.25 * depth
            prof = [(fr.Y(-depth - 1.0), z_roof + 0.9 - 0.25), (fr.Y(0.3), zh), (fr.Y(0.3), zh - 0.5), (fr.Y(-depth - 1.0), z_roof + 0.9 - 0.75)]
            X0, X1 = sorted((fr.X(u0 - 1.0), fr.X(u1 + 1.0)))
            self.n += 1
            prism_yz("nb_proof_%d" % self.n, prof, X0, X1, roof_m, self.col)
        else:  # gable facing the street
            self.gable(fr, u0, u1, -depth, 0.2, z_roof + 0.9, 0.42, "v", 1.2, roof_m, trim, thick=0.5, rake=1.5)

    def dormer(self, fr, u, v, w, z_base, z_eave, roof_m, wall_m, trim, glass, kind="gable"):
        d = 6.0
        self.box(fr, u - w / 2, v, u + w / 2, v + d, z_base, z_eave, wall_m, "nb_dormer")
        self.window(fr, "front", 0, z_base + 0.8, w - 1.6, z_eave - z_base - 1.6, trim, glass, muntins=(2, 2), sill=False,
                    depth_u=None) if False else None
        # window on the dormer face (own little frame)
        f2 = Frame(fr.X(u - w / 2), fr.Y(v), "s" if fr.f > 0 else "n")
        self.window(f2, "front", w / 2, z_base + 0.8, min(w - 1.6, 3.0), z_eave - z_base - 1.4, trim, glass, muntins=(2, 3))
        if kind == "gable":
            self.gable(fr, u - w / 2, u + w / 2, v, v + d, z_eave, 0.75, "v", 0.4, roof_m, wall_m, thick=0.4, rake=0.4)
        else:
            self.hip(fr, u - w / 2, u + w / 2, v, v + d, z_eave, 0.5, 0.5, roof_m, thick=0.4)

    def foundation(self, fr, W, D, mat=None):
        mat = mat or self.mats.get("concrete_sealed")
        self.box(fr, -0.1, -0.1, W + 0.1, D + 0.1, self.gz - 0.8, self.gz + 1.2, mat, "nb_found")

    def band(self, fr, W, D, z0, z1, mat, proud=0.15):
        """Trim band (cornice / water table) around the whole body."""
        self.box(fr, -proud, -proud, W + proud, 0.0, z0, z1, mat, "nb_band")
        self.box(fr, -proud, D, W + proud, D + proud, z0, z1, mat, "nb_band")
        self.box(fr, -proud, 0, 0, D, z0, z1, mat, "nb_band")
        self.box(fr, W, 0, W + proud, D, z0, z1, mat, "nb_band")

    # ------------------------------------------------------------------ house styles
    def build_house(self, lot):
        st = lot["style"]
        fr = Frame(lot["hx0"], lot["front_y"], lot["facing"])
        getattr(self, "style_" + st)(fr, lot)
        self.n += 0

    def style_georgian(self, fr, lot):
        W, D = lot.get("w", 38), lot.get("d", 32)
        brick = self.mats.get(lot.get("wall_m", "brick_red"))
        trim = self.mats.get("trim_white")
        glass = self.mats.get("window_dark")
        shut = self.mats.get(lot.get("shutter_m", "shutter_black"))
        gz = self.gz
        ze = gz + 20.0
        self.foundation(fr, W, D)
        self.box(fr, 0, 0, W, D, gz, ze, brick, "nb_body")
        self.band(fr, W, D, ze - 1.0, ze, trim, 0.25)            # cornice
        zr = self.gable(fr, 0, W, 0, D, ze, 0.75, "u", 1.2, self.mats.get(lot.get("roof_m", "slate_roof")), brick, rake=0.4)
        # five bays, centre door with a gabled portico
        bays = [W * (i + 0.5) / 5 for i in range(5)]
        for i, b in enumerate(bays):
            if i == 2:
                self.door(fr, b, 3.2, 7.2, trim, self.mats.get("shutter_black"), portico={"kind": lot.get("portico", "gable")})
                self.window(fr, "front", b, gz + 12.2, 2.6, 4.6, trim, glass, muntins=(3, 4), shutters=shut)
            else:
                self.window(fr, "front", b, gz + 3.0, 3.0, 5.6, trim, glass, muntins=(3, 4), shutters=shut)
                self.window(fr, "front", b, gz + 12.2, 3.0, 4.8, trim, glass, muntins=(3, 4), shutters=shut)
        for a in (D * 0.3, D * 0.7):
            self.window(fr, "left", a, gz + 3.0, 2.8, 5.4, trim, glass, muntins=(3, 4), depth_u=W)
            self.window(fr, "right", a, gz + 3.0, 2.8, 5.4, trim, glass, muntins=(3, 4), depth_u=W)
            self.window(fr, "left", a, gz + 12.2, 2.8, 4.6, trim, glass, muntins=(3, 4), depth_u=W)
            self.window(fr, "right", a, gz + 12.2, 2.8, 4.6, trim, glass, muntins=(3, 4), depth_u=W)
        for u in (0.6, W - 3.6):
            self.chimney(fr, u, D / 2 - 2.5, 3.0, 5.0, zr + 3.0, brick)
        return zr

    def style_colonial(self, fr, lot):
        W, D = lot.get("w", 36), lot.get("d", 30)
        wall = self.mats.get(lot.get("wall_m", "siding_white"))
        trim = self.mats.get("trim_white")
        glass = self.mats.get("window_dark")
        shut = self.mats.get(lot.get("shutter_m", "shutter_green"))
        gz = self.gz
        ze = gz + 18.5
        self.foundation(fr, W, D)
        self.box(fr, 0, 0, W, D, gz, ze, wall, "nb_body")
        self.band(fr, W, D, ze - 0.7, ze, trim, 0.2)
        zr = self.gable(fr, 0, W, 0, D, ze, 0.83, "u", 1.0, self.mats.get(lot.get("roof_m", "shingle_dark")), wall, rake=0.3)
        bays = [W * (i + 0.5) / 5 for i in range(5)]
        for i, b in enumerate(bays):
            if i == 2:
                self.door(fr, b, 3.0, 7.0, trim, self.mats.get("oxblood"), portico={"kind": "flat", "m": "shingle_dark"})
                self.window(fr, "front", b, gz + 11.5, 2.6, 4.4, trim, glass, muntins=(2, 4))
            else:
                self.window(fr, "front", b, gz + 2.8, 2.9, 5.4, trim, glass, muntins=(2, 4), shutters=shut)
                self.window(fr, "front", b, gz + 11.5, 2.9, 4.6, trim, glass, muntins=(2, 4), shutters=shut)
        for a in (D * 0.3, D * 0.7):
            for face in ("left", "right"):
                self.window(fr, face, a, gz + 2.8, 2.8, 5.2, trim, glass, muntins=(2, 4), depth_u=W)
                self.window(fr, face, a, gz + 11.5, 2.8, 4.4, trim, glass, muntins=(2, 4), depth_u=W)
        self.chimney(fr, W / 2 - 1.5, D - 6, 3.0, 2.5, zr + 2.5, self.mats.get("brick_red"))
        # small side wing (sunroom / garage) on one side
        side = lot.get("wing", "right")
        if side:
            u0, u1 = (W, W + 14) if side == "right" else (-14, 0)
            self.box(fr, u0, 3, u1, D - 4, gz, gz + 10, wall, "nb_wing")
            self.hip(fr, u0, u1, 3, D - 4, gz + 10, 0.4, 1.0, self.mats.get(lot.get("roof_m", "shingle_dark")))
            self.window(fr, "front", (u0 + u1) / 2 - 3, gz + 3.0, 2.6, 4.6, trim, glass, muntins=(2, 3))
            self.window(fr, "front", (u0 + u1) / 2 + 3, gz + 3.0, 2.6, 4.6, trim, glass, muntins=(2, 3))
        return zr

    def style_tudor(self, fr, lot):
        W, D = lot.get("w", 40), lot.get("d", 34)
        brick = self.mats.get(lot.get("wall_m", "brick_common"))
        stucco = self.mats.get("stucco_cream")
        timber = self.mats.get("half_timber")
        trim = timber
        glass = self.mats.get("window_dark")
        gz = self.gz
        ze = gz + 18.0
        roof_m = self.mats.get(lot.get("roof_m", "slate_roof"))
        self.foundation(fr, W, D)
        self.box(fr, 0, 0, W, D, gz, gz + 10.0, brick, "nb_body")
        self.box(fr, 0, 0, W, D, gz + 10.0, ze, stucco, "nb_body")
        zr = self.gable(fr, 0, W, 0, D, ze, 0.9, "u", 1.0, roof_m, stucco, rake=0.6)
        # front cross gable wing, steep, projecting 4 ft
        gw0, gw1 = 4.0, 20.0
        self.box(fr, gw0, -4.0, gw1, 12.0, gz, gz + 10.0, brick, "nb_wing")
        self.box(fr, gw0, -4.0, gw1, 12.0, gz + 10.0, ze + 1.0, stucco, "nb_wing")
        f2 = Frame(fr.X(gw0), fr.Y(-4.0), "s" if fr.f > 0 else "n")
        zg = self.gable(f2, 0, gw1 - gw0, 0, 16.0, ze + 1.0, 1.15, "v", 0.8, roof_m, stucco, rake=0.8)
        # half-timbering on the wing gable and the upper walls
        for uu in [gw0 + 1.0 + i * 2.6 for i in range(6)]:
            self.box(fr, uu, -4.15, uu + 0.4, -3.98, gz + 10.2, ze + 0.6, timber, "nb_timber")
        self.box(fr, gw0, -4.15, gw1, -3.98, gz + 10.0, gz + 10.5, timber, "nb_timber")
        self.box(fr, gw0, -4.15, gw1, -3.98, ze + 0.3, ze + 0.8, timber, "nb_timber")
        for uu in [gw1 + 2.0 + i * 3.0 for i in range(int((W - gw1 - 3) / 3))]:
            self.box(fr, uu, -0.15, uu + 0.4, 0.02, gz + 10.2, ze - 0.2, timber, "nb_timber")
        self.box(fr, gw1, -0.15, W, 0.02, gz + 10.0, gz + 10.5, timber, "nb_timber")
        # windows: casement groups
        self.window(f2, "front", (gw1 - gw0) / 2, gz + 3.0, 7.5, 5.0, trim, glass, muntins=(3, 1))
        self.window(f2, "front", (gw1 - gw0) / 2, gz + 12.0, 6.0, 4.5, trim, glass, muntins=(3, 1), sill=True)
        self.window(fr, "front", (gw1 + W) / 2 + 2, gz + 3.2, 6.0, 4.6, trim, glass, muntins=(3, 1))
        self.window(fr, "front", (gw1 + W) / 2 + 2, gz + 12.0, 5.0, 4.0, trim, glass, muntins=(3, 1))
        for a in (D * 0.3, D * 0.7):
            for face in ("left", "right"):
                self.window(fr, face, a, gz + 3.2, 4.5, 4.6, trim, glass, muntins=(2, 1), depth_u=W)
                self.window(fr, face, a, gz + 12.0, 4.5, 4.0, trim, glass, muntins=(2, 1), depth_u=W)
        # arched-feel entry beside the wing, in a brick surround, and the big front chimney
        du = gw1 + 3.5
        self.box(fr, du - 2.6, -1.4, du + 2.6, 0.0, gz, gz + 9.0, brick, "nb_surround")
        f3 = Frame(fr.X(0), fr.Y(-1.4), "s" if fr.f > 0 else "n")
        self.door(f3, du, 3.2, 7.4, timber, self.mats.get("walnut"), step_n=2, trim_w=0.3)
        self.chimney(fr, gw0 - 3.5, 2.0, 3.5, 2.4, zr + 4.0, brick)
        self.chimney(fr, gw0 - 3.5, 4.4, 3.5, 1.2, zr + 2.0, brick)
        return zr

    def style_foursquare(self, fr, lot):
        W, D = lot.get("w", 30), lot.get("d", 32)
        wall = self.mats.get(lot.get("wall_m", "siding_gray"))
        trim = self.mats.get("trim_white")
        glass = self.mats.get("window_dark")
        gz = self.gz
        ze = gz + 19.5
        roof_m = self.mats.get(lot.get("roof_m", "shingle_dark"))
        self.foundation(fr, W, D)
        self.box(fr, 0, 0, W, D, gz, ze, wall, "nb_body")
        self.band(fr, W, D, gz + 10.0, gz + 10.5, trim, 0.12)
        self.band(fr, W, D, ze - 0.6, ze, trim, 0.2)
        self.hip(fr, 0, W, 0, D, ze, 0.5, 2.5, roof_m)
        self.dormer(fr, W / 2, 6.0, 8.0, ze + 0.8, ze + 5.5, roof_m, wall, trim, glass, kind="hip")
        # full-width porch with brick piers and square columns
        self.porch(fr, 0.5, W - 0.5, 8.0, gz + 1.2, gz + 9.8, 4, "tapered", "hip", roof_m, trim, pier_m=self.mats.get("brick_red"))
        # asymmetric front: door left, windows right; two above
        self.door(fr, 6.0, 3.0, 7.0, trim, self.mats.get("oxblood"), step_n=0)
        self.window(fr, "front", W - 9, gz + 3.2, 6.0, 5.4, trim, glass, muntins=(2, 2))
        self.window(fr, "front", 7.0, gz + 12.0, 3.0, 4.8, trim, glass, muntins=(1, 2))
        self.window(fr, "front", W - 9, gz + 12.0, 5.0, 4.8, trim, glass, muntins=(2, 2))
        for a in (D * 0.3, D * 0.7):
            for face in ("left", "right"):
                self.window(fr, face, a, gz + 3.2, 3.0, 5.0, trim, glass, muntins=(1, 2), depth_u=W)
                self.window(fr, face, a, gz + 12.0, 3.0, 4.6, trim, glass, muntins=(1, 2), depth_u=W)
        self.chimney(fr, W - 4.0, D - 8, 2.6, 2.6, ze + 6.0, self.mats.get("brick_red"))
        return ze + 6

    def style_bungalow(self, fr, lot):
        W, D = lot.get("w", 32), lot.get("d", 42)
        wall = self.mats.get(lot.get("wall_m", "siding_sage"))
        trim = self.mats.get("trim_cream")
        glass = self.mats.get("window_dark")
        gz = self.gz
        ze = gz + 11.0
        roof_m = self.mats.get(lot.get("roof_m", "shingle_brown"))
        self.foundation(fr, W, D)
        self.box(fr, 0, 0, W, D, gz, ze, wall, "nb_body")
        zr = self.gable(fr, 0, W, 0, D, ze, 0.42, "v", 2.5, roof_m, wall, rake=2.0)
        # rafter tails along both eaves
        for v in [2 + i * 2.5 for i in range(int(D / 2.5))]:
            self.box(fr, -2.5, v, 0.2, v + 0.3, ze - 0.9, ze - 0.2, trim, "nb_tail")
            self.box(fr, W - 0.2, v, W + 2.5, v + 0.3, ze - 0.9, ze - 0.2, trim, "nb_tail")
        # deep porch under its own lower gable, tapered columns on brick piers
        self.porch(fr, 1.0, W - 1.0, 9.0, gz + 1.0, gz + 8.6, 3, "tapered", "gable", roof_m, trim, pier_m=self.mats.get("brick_common"))
        self.door(fr, W * 0.32, 3.0, 6.8, trim, self.mats.get("walnut"), step_n=0)
        self.window(fr, "front", W * 0.7, gz + 2.8, 7.0, 4.8, trim, glass, muntins=(3, 1))
        # attic window in the gable
        self.window(fr, "front", W / 2, ze + 1.5, 3.5, 2.5, trim, glass, muntins=(2, 1), sill=True)
        for a in (D * 0.35, D * 0.6, D * 0.85):
            for face in ("left", "right"):
                self.window(fr, face, a, gz + 2.8, 4.0, 4.6, trim, glass, muntins=(2, 1), depth_u=W)
        self.chimney(fr, -0.5, D * 0.45, 2.4, 4.0, zr + 1.5, self.mats.get("brick_common"))
        return zr

    def style_ranch(self, fr, lot):
        W, D = lot.get("w", 58), lot.get("d", 30)
        wall = self.mats.get(lot.get("wall_m", "brick_painted"))
        trim = self.mats.get("trim_white")
        glass = self.mats.get("window_dark")
        gz = self.gz
        ze = gz + 9.0
        roof_m = self.mats.get(lot.get("roof_m", "shingle_dark"))
        self.foundation(fr, W, D)
        self.box(fr, 0, 0, W, D, gz, ze, wall, "nb_body")
        self.hip(fr, 0, W, 0, D, ze, 0.33, 2.0, roof_m)
        # attached garage on the right, door facing the street
        self.box(fr, W - 22, -2.0, W, 0.0, gz, ze, wall, "nb_gar")
        self.box(fr, W - 20.5, -2.05, W - 2.5, -1.75, gz, gz + 7.2, trim, "nb_gardoor")
        for z in (gz + 1.8, gz + 3.6, gz + 5.4):
            self.box(fr, W - 20.5, -2.1, W - 2.5, -2.04, z - 0.05, z + 0.05, self.mats.get("shutter_black"), "nb_garline")
        # picture window, entry, bedroom windows
        self.window(fr, "front", 12.0, gz + 2.5, 9.0, 5.0, trim, glass, muntins=(3, 1))
        self.door(fr, 24.0, 3.0, 6.8, trim, self.mats.get("teal_paint"), step_n=1)
        self.window(fr, "front", 31.0, gz + 3.5, 4.0, 3.5, trim, glass, muntins=(2, 1))
        for a in (D * 0.3, D * 0.7):
            self.window(fr, "left", a, gz + 3.5, 4.0, 3.5, trim, glass, muntins=(2, 1), depth_u=W)
        self.chimney(fr, 18.0, D * 0.5, 4.0, 2.0, ze + 4.5, self.mats.get("brick_red"))
        return ze + 4.5

    # ------------------------------------------------------------------ lot furnishing
    def garage(self, lot):
        """Detached garage at the alley, door facing the alley."""
        g = lot.get("garage")
        if not g:
            return
        gx0, gy0, gx1, gy1 = g["b"]
        wall = self.mats.get(g.get("m", lot.get("wall_m", "siding_white")))
        roof_m = self.mats.get(lot.get("roof_m", "shingle_dark"))
        ze = self.gz + 9.0
        box_ft("nb_gar_%d" % self.n, gx0, gy0, gx1, gy1, self.gz, ze, wall, self.col); self.n += 1
        fr = Frame(gx0, gy0, "s")
        if g.get("roof", "gable") == "gable":
            self.gable(fr, 0, gx1 - gx0, 0, gy1 - gy0, ze, 0.42, "v", 1.0, roof_m, wall, thick=0.5, rake=1.0)
        else:
            self.hip(fr, 0, gx1 - gx0, 0, gy1 - gy0, ze, 0.4, 1.0, roof_m, thick=0.5)
        # door on the alley side (north face when the alley is north)
        side = g.get("door_side", "n")
        trim = self.mats.get("trim_white")
        cx = (gx0 + gx1) / 2
        dw = min(16.0, gx1 - gx0 - 4)
        if side == "n":
            box_ft("nb_gdoor_%d" % self.n, cx - dw / 2, gy1 - 0.05, cx + dw / 2, gy1 + 0.25, self.gz, self.gz + 7.2, trim, self.col); self.n += 1
        else:
            box_ft("nb_gdoor_%d" % self.n, cx - dw / 2, gy0 - 0.25, cx + dw / 2, gy0 + 0.05, self.gz, self.gz + 7.2, trim, self.col); self.n += 1

    def walk(self, lot):
        """Front walk from the sidewalk to the entry, 4 ft concrete."""
        wx = lot.get("walk_x")
        if wx is None:
            return
        y_side = self.cfg["street"]["sidewalk_y"][0 if lot["facing"] == "s" else 1]
        y0, y1 = sorted((y_side, lot["front_y"] - (1.0 if lot["facing"] == "s" else -1.0)))
        box_ft("nb_walk_%d" % self.n, wx - 2.0, y0, wx + 2.0, y1, self.gz - 0.2, self.gz + 0.05, self.mats.get("concrete_sealed"), self.col); self.n += 1

    def driveway(self, lot):
        dv = lot.get("driveway")
        if not dv:
            return
        x0, x1 = dv["x"], dv["x"] + dv.get("w", 10)
        y0, y1 = sorted(dv["y"])
        box_ft("nb_drive_%d" % self.n, x0, y0, x1, y1, self.gz - 0.2, self.gz + 0.04, self.mats.get("concrete_sealed"), self.col); self.n += 1

    def plantings(self, lot):
        """Foundation shrubs along the front wall, a hedge stub, a yard tree or two."""
        fr = Frame(lot["hx0"], lot["front_y"], lot["facing"])
        W = lot.get("w", 36)
        rnd = self.rng
        leaf = self.mats.get("leaf")
        yew = self.mats.get("leaf_dark")
        n = int(W / 4)
        for i in range(n):
            u = 1.5 + (W - 3) * i / max(n - 1, 1)
            r = rnd.uniform(1.2, 2.2)
            if rnd.random() < 0.25:
                continue  # gaps for the walk and windows
            ob = sphere_ft("nb_shrub_%d" % self.n, (fr.X(u), fr.Y(-2.2), self.gz + r * 0.55), r, yew if i % 2 else leaf, self.col, 12, 7)
            ob.scale = (1, 1, 0.8)
            self.n += 1
        for t in lot.get("trees", []):
            self.tree(t)

    # ------------------------------------------------------------------ trees
    SPECIES = {
        # model, height range ft, crown tint (autumn), procedural crown colour
        "oak":    {"model": "island_tree_01", "h": (48, 62), "tint": [1.0, 0.82, 0.58], "leaf": "leaf_oak"},
        "elm":    {"model": "island_tree_02", "h": (55, 70), "tint": [1.0, 0.94, 0.62], "leaf": "leaf_elm"},
        "maple":  {"model": "tree_small_02", "h": (34, 44), "tint": [1.0, 0.55, 0.3], "leaf": "leaf_maple"},
        "locust": {"model": "tree_small_02", "h": (36, 46), "tint": [1.0, 0.95, 0.6], "leaf": "leaf_elm"},
        "spruce": {"model": None, "h": (34, 46), "tint": None, "leaf": "leaf_dark"},
    }

    def tree(self, t):
        sp = self.SPECIES.get(t.get("species", "oak"), self.SPECIES["oak"])
        x, y = t["pos"]
        h = t.get("h") or self.rng.uniform(*sp["h"])
        self.tree_n += 1
        if sp["model"] and self.stager is not None:
            # the island_tree models carry a ground disc at their base: sink it below grade
            sink = 0.9 if sp["model"].startswith("island_tree") else 0.1
            e = {"asset": sp["model"], "pos": [x, y, self.gz - sink], "height_ft": h + sink, "rot_z": self.rng.uniform(0, 360)}
            if t.get("autumn", True) and sp["tint"]:
                e["tint"] = sp["tint"]
                e["tint_only"] = ["leaf", "leav", "foli", "canopy"]
            ob = self.stager.place_model(e)
            if ob is not None:
                return ob
        return self.procedural_tree(x, y, h, sp, t)

    def procedural_tree(self, x, y, h, sp, t):
        """Trunk with taper, three limbs, and a crown of 14 overlapping clumps inside an ellipsoid envelope."""
        rnd = random.Random(self.tree_n * 7 + 3)
        bark = self.mats.get("bark")
        leaf = self.mats.get(sp["leaf"] if t.get("autumn", True) else "leaf")
        gz = self.gz
        if sp is self.SPECIES["spruce"]:
            # conifer: stacked cones
            cylinder_ft("nb_trunk_%d" % self.tree_n, (x, y, gz), 0.6, h * 0.35, bark, self.col, 10)
            n = 7
            for i in range(n):
                z0 = gz + h * (0.18 + 0.8 * i / n)
                r = (h * 0.16) * (1 - i / (n + 1))
                cyl = cylinder_ft("nb_cone_%d_%d" % (self.tree_n, i), (x, y, z0), r, h * 0.16, leaf, self.col, 12)
                cyl.scale = (1, 1, 1)
            return
        crown_base = h * 0.38
        crown_r = h * 0.36 * t.get("spread", 1.0)
        cylinder_ft("nb_trunk_%d" % self.tree_n, (x, y, gz), max(0.6, h * 0.02), crown_base + h * 0.2, bark, self.col, 12)
        for k in range(3):
            ang = rnd.uniform(0, 2 * math.pi) + k * 2.1
            lx, ly = x + math.cos(ang) * crown_r * 0.3, y + math.sin(ang) * crown_r * 0.3
            limb = cylinder_ft("nb_limb_%d_%d" % (self.tree_n, k), ((x + lx) / 2, (y + ly) / 2, crown_base + h * 0.12), max(0.3, h * 0.009), crown_r * 0.5, bark, self.col, 8)
            limb.rotation_euler = (math.radians(rnd.uniform(25, 40)), 0, ang + math.pi / 2)
        for j in range(14):
            ang = rnd.uniform(0, 2 * math.pi)
            rad = crown_r * rnd.uniform(0.0, 0.75)
            cz = crown_base + h * 0.28 + rnd.uniform(-0.35, 0.35) * h * 0.25
            rr = crown_r * rnd.uniform(0.35, 0.55)
            # keep clumps inside the ellipsoid envelope (r horizontally, 0.75 r vertically)
            sp_ = sphere_ft("nb_crown_%d_%d" % (self.tree_n, j), (x + math.cos(ang) * rad, y + math.sin(ang) * rad, cz), rr, leaf, self.col, 12, 7)
            sp_.scale = (1, 1, rnd.uniform(0.6, 0.8))
        top = sphere_ft("nb_crown_%d_top" % self.tree_n, (x, y, crown_base + h * 0.45), crown_r * 0.42, leaf, self.col, 12, 7)
        top.scale = (1, 1, 0.7)

    # ------------------------------------------------------------------ street
    def street(self):
        s = self.cfg["street"]
        gz = self.gz
        x0, x1 = s["x"]
        yc0, yc1 = s["curb_y"]          # north curb (our side), south curb
        conc = self.mats.get("concrete_sealed")
        asph = self.mats.get("asphalt")
        lawn = self.mats.get("lawn")
        ground = bpy.data.objects.get("ground")
        from geom import cut_with_box
        # roadway 6 in below the parkway, concrete curb and gutter both sides
        if ground is not None:
            cut_with_box([ground], [x0, yc1 - 1.5, x1, yc0 + 1.5, gz - 1.6, gz + 1], "cut_street")
        box_ft("nb_road", x0, yc1, x1, yc0, gz - 1.3, gz - 0.5, asph, self.col)
        for (ya, yb) in ((yc0, yc0 + 1.5), (yc1 - 1.5, yc1)):
            box_ft("nb_curb_%d" % self.n, x0, ya, x1, yb, gz - 1.3, gz + 0.02, conc, self.col); self.n += 1
        # gutter strip
        box_ft("nb_gutter_n", x0, yc0 - 1.5, x1, yc0, gz - 1.3, gz - 0.45, conc, self.col)
        box_ft("nb_gutter_s", x0, yc1, x1, yc1 + 1.5, gz - 1.3, gz - 0.45, conc, self.col)
        # sidewalks (5 ft) with scored joints every 5 ft
        for (ya, yb) in s["sidewalks"]:
            box_ft("nb_sidewalk_%d" % self.n, x0, ya, x1, yb, gz - 0.3, gz + 0.05, conc, self.col); self.n += 1
            xx = x0 + 2.5
            while xx < x1:
                box_ft("nb_joint_%d" % self.n, xx - 0.03, ya, xx + 0.03, yb, gz + 0.05, gz + 0.06, self.mats.get("asphalt"), self.col); self.n += 1
                xx += 5.0
        # street trees in both parkways
        st = s.get("trees", {})
        if st:
            sp_cycle = st.get("species", ["elm", "oak", "maple"])
            for side, y in (("n", st["y"][0]), ("s", st["y"][1])):
                xx = x0 + st.get("offset", 20) + (st["spacing"] / 2 if side == "s" else 0)
                i = 0
                while xx < x1 - 10:
                    skips = st.get("skip_x", []) if side == "n" else st.get("skip_x_s", [])
                    skip = any(abs(xx - sx) < 14 for sx in skips)
                    if not skip:
                        self.tree({"pos": [xx, y], "species": sp_cycle[i % len(sp_cycle)], "autumn": True})
                    xx += st["spacing"] * self.rng.uniform(0.85, 1.15)
                    i += 1
        # lamp posts (black acorn posts) and a hydrant
        for (lx, ly) in s.get("lamps", []):
            self.lamp(lx, ly)
        for (hx, hy) in s.get("hydrants", []):
            self.hydrant(hx, hy)
        # driveway aprons across the curb
        for ap in s.get("aprons", []):
            box_ft("nb_apron_%d" % self.n, ap[0], ap[1], ap[2], ap[3], gz - 1.3, gz - 0.3, conc, self.col); self.n += 1

    def lamp(self, x, y):
        blk = self.mats.get("steel_black")
        gz = self.gz
        box_ft("nb_lampbase_%d" % self.n, x - 0.6, y - 0.6, x + 0.6, y + 0.6, gz, gz + 1.0, blk, self.col); self.n += 1
        cylinder_ft("nb_lamppost_%d" % self.n, (x, y, gz + 1.0), 0.22, 11.0, blk, self.col, 12); self.n += 1
        glow = self.mats.get("glass_frosted")
        g = sphere_ft("nb_lampglobe_%d" % self.n, (x, y, gz + 13.2), 0.9, glow, self.col, 12, 8); self.n += 1
        g.scale = (1, 1, 1.25)
        box_ft("nb_lampcap_%d" % self.n, x - 0.5, y - 0.5, x + 0.5, y + 0.5, gz + 14.2, gz + 14.6, blk, self.col); self.n += 1
        if self.plan.get("_dusk"):
            from geom import point_light
            point_light("nb_lamplight_%d" % self.n, (x, y, gz + 13.2), 120, 2700, 0.5, get_collection("lights"))

    def hydrant(self, x, y):
        red = self.mats.get("hydrant_red")
        cylinder_ft("nb_hyd_%d" % self.n, (x, y, self.gz), 0.45, 2.4, red, self.col, 12); self.n += 1
        s = sphere_ft("nb_hydtop_%d" % self.n, (x, y, self.gz + 2.5), 0.5, red, self.col, 10, 6); self.n += 1
        box_ft("nb_hydarm_%d" % self.n, x - 0.9, y - 0.25, x + 0.9, y + 0.25, self.gz + 1.5, self.gz + 1.9, red, self.col); self.n += 1

    def fences(self):
        ced = self.mats.get("cedar_ext")
        for f in self.cfg.get("fences", []):
            b = f["b"]
            h = f.get("h", 6.0)
            box_ft("nb_fence_%d" % self.n, b[0], b[1], b[2], b[3], self.gz, self.gz + h, ced, self.col); self.n += 1
        for hg in self.cfg.get("hedges", []):
            b = hg["b"]
            box_ft("nb_hedge_%d" % self.n, b[0], b[1], b[2], b[3], self.gz, self.gz + hg.get("h", 3.5), self.mats.get("leaf_dark"), self.col); self.n += 1

    # ------------------------------------------------------------------ all
    def build_all(self):
        self.street()
        for lot in self.cfg.get("lots", []):
            try:
                self.build_house(lot)
            except Exception as e:  # noqa
                log("neighbour house failed", lot.get("style"), e)
                raise
            self.garage(lot)
            self.walk(lot)
            self.driveway(lot)
            self.plantings(lot)
        self.fences()
        for t in self.cfg.get("trees", []):
            self.tree(t)
        log("neighborhood: %d lots, %d trees, %d objects" % (len(self.cfg.get("lots", [])), self.tree_n, self.n))


def build(plan, house, mats, stager=None):
    if "neighborhood" not in plan.get("site", {}):
        return
    Hood(plan, house, mats, stager).build_all()
