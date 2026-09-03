"""
site_build.py: exterior architecture and site from plan["exterior"] and plan["site"] (spec sections 1, 2, 7).
Roofs (gable, shed, flat with posts and beams), foundation and cladding bands, the vent chase, ground, slabs,
beds, hedges, trees, neighbor massing, and typed structures (spa, grill counter, catio, screens).
"""
import math

import bpy

from geom import (FT, IN, m, log, box_ft, box_local, beam_between, cylinder_ft, sphere_ft, prism_yz, prism_xz,
                  get_collection, cut_with_box, set_face_material, overlap, bounds_of)


class Site:
    def __init__(self, plan, house, mats):
        self.plan = plan
        self.house = house
        self.mats = mats
        self.col = get_collection("site")
        self.col_roof = get_collection("roofs")
        self.gz = plan.get("site", {}).get("grade_z", -0.5)
        self.counts = {}

    def n(self, k, v=1):
        self.counts[k] = self.counts.get(k, 0) + v

    # ------------------------------------------------------------------ footprints
    def footprint(self, floor, skip_void=False):
        parts = [p for r, p in self.house.parts_on_floor(floor) if not r.get("void")]
        return (min(p[0] for p in parts), min(p[1] for p in parts), max(p[2] for p in parts), max(p[3] for p in parts))

    # ------------------------------------------------------------------ roofs
    def build_roofs(self):
        for r in self.plan.get("exterior", {}).get("roofs", []):
            t = r["type"]
            if t == "gable":
                self.gable(r)
            elif t == "shed":
                self.shed(r)
            elif t == "flat":
                self.flat(r)
            self.n("roofs")

    def gable(self, r):
        mat = self.mats.get(r["m"])
        soffit = self.mats.get(r.get("soffit_m", "cedar_ext"))
        pitch = r["pitch"]
        thick = r.get("thick", 0.6)
        x0, x1, y0, y1 = r["x0"], r["x1"], r["y0"], r["y1"]
        if r["ridge_axis"] == "x":
            ridge = r["ridge_at"]
            half_s = ridge - y0
            half_n = y1 - ridge
            # z at the wall line is z_wall; the plane passes through the wall line at the footprint edge
            wall_y0 = self.plan["site"].get("house_y0", 0) if False else None
            # rise from the eave edge to the ridge: slope continues over the overhang
            z_edge_s = r["z_wall"] - (half_s - (half_s - r.get("eave_ft", 4.0))) * 0  # placeholder for clarity
            # define the plane by its height at the ridge: ridge_z = z_wall + pitch * (ridge - wall_line)
            wall_line_s = y0 + r.get("eave_ft", 4.0)
            ridge_z = r["z_wall"] + pitch * (ridge - wall_line_s)
            ang = math.degrees(math.atan(pitch))
            Ls = half_s / math.cos(math.radians(ang))
            Ln = half_n / math.cos(math.radians(ang))
            rs = box_local("roof_%s_s" % r["name"].replace(" ", "_"), (x1, ridge, ridge_z), (x1 - x0, Ls, thick), 180, mat, self.col_roof, rot_x_deg=-ang)
            rn = box_local("roof_%s_n" % r["name"].replace(" ", "_"), (x0, ridge, ridge_z), (x1 - x0, Ln, thick), 0, mat, self.col_roof, rot_x_deg=-ang)
            for ob in (rs, rn):
                set_face_material(ob, 0, soffit)
            box_ft("ridge_%s" % r["name"].replace(" ", "_"), x0, ridge - 0.3, x1, ridge + 0.3, ridge_z + thick - 0.1, ridge_z + thick + 0.12, mat, self.col_roof)
            # fascias at both eaves
            fz_s = ridge_z - pitch * half_s
            fz_n = ridge_z - pitch * half_n
            fas = self.mats.get("bronze_black")
            fh = r.get("fascia", 1.0)
            box_ft("fascia_%s_s" % r["name"].replace(" ", "_"), x0, y0 - 0.15, x1, y0, fz_s - fh + thick, fz_s + thick + 0.1, fas, self.col_roof)
            box_ft("fascia_%s_n" % r["name"].replace(" ", "_"), x0, y1, x1, y1 + 0.15, fz_n - fh + thick, fz_n + thick + 0.1, fas, self.col_roof)
            # cuts: footprints (x0, y0, x1, y1) of volumes that rise through the roof (the stair tower through the south eave)
            cuts = r.get("cuts", [])
            fas_s = bpy.data.objects["fascia_%s_s" % r["name"].replace(" ", "_")]
            fas_n = bpy.data.objects["fascia_%s_n" % r["name"].replace(" ", "_")]
            for cb in cuts:
                cut_with_box([rs, rn, fas_s, fas_n], [cb[0], cb[1], cb[2], cb[3], r["z_wall"] - 4, ridge_z + 4], "cut_roof")

            def in_cut(x, y):
                return any(cb[0] - 0.5 <= x <= cb[2] + 0.5 and cb[1] - 0.5 <= y <= cb[3] + 0.5 for cb in cuts)
            # rafter tails under both eaves
            rt = r.get("rafter_tails")
            if rt:
                ced = self.mats.get("cedar_ext")
                x = x0 + 2
                while x < x1 - 1:
                    if not in_cut(x, y0 + 1):
                        box_local("tail_s_%s_%d" % (r["name"][:4], int(x)), (x - 0.17, y0 + 0.2, fz_s - 0.9), (0.33, r.get("eave_ft", 4.0) + 1.0, 0.95), 0, ced, self.col_roof)
                    if not in_cut(x, y1 - 1):
                        box_local("tail_n_%s_%d" % (r["name"][:4], int(x)), (x - 0.17, y1 - r.get("eave_ft", 4.0) - 1.2, fz_n - 0.9), (0.33, r.get("eave_ft", 4.0) + 1.0, 0.95), 0, ced, self.col_roof)
                    x += rt
            # skylights: cut and add a glass pane + curb
            for sk in r.get("skylights", []):
                sx, sy, sw, sh = sk
                zc = ridge_z - pitch * abs(sy - ridge)
                cut_with_box([rs if sy < ridge else rn], [sx - sw / 2, sy - sh / 2, sx + sw / 2, sy + sh / 2, zc - 2, zc + 2], "cut_sky")
                box_ft("skylight_curb_%d_%d" % (int(sx), int(sy)), sx - sw / 2 - 0.15, sy - sh / 2 - 0.15, sx + sw / 2 + 0.15, sy + sh / 2 + 0.15, zc - 0.2, zc + thick + 0.3, self.mats.get("bronze_black"), self.col_roof)
                box_ft("skylight_glass_%d_%d" % (int(sx), int(sy)), sx - sw / 2, sy - sh / 2, sx + sw / 2, sy + sh / 2, zc + thick + 0.25, zc + thick + 0.29, self.mats.get("glass"), get_collection("glass"))
            # gable end walls (triangles) filled in cedar at both X ends over the upper volume walls
            gx0, gx1 = r.get("gable_x", [x0 + r.get("rake_ft", 4.0), x1 - r.get("rake_ft", 4.0)])
            prof = [(y0 + r.get("eave_ft", 4.0), r["z_wall"] - 0.6), (y1 - r.get("eave_ft", 4.0), r["z_wall"] - 0.6), (ridge, ridge_z + 0.2)]
            ced = self.mats.get(r.get("gable_m", "cedar_ext"))
            prism_yz("gable_%s_w" % r["name"][:4], prof, gx0, gx0 + 1.0, ced, self.col_roof)
            prism_yz("gable_%s_e" % r["name"][:4], prof, gx1 - 1.0, gx1, ced, self.col_roof)
        else:
            # ridge along Y at X = ridge_at (garage)
            ridge = r["ridge_at"]
            half_w = ridge - x0
            half_e = x1 - ridge
            wall_line_w = x0 + r.get("eave_ft", 3.0)
            ridge_z = r["z_wall"] + pitch * (ridge - wall_line_w)
            ang = math.degrees(math.atan(pitch))
            Lw = half_w / math.cos(math.radians(ang))
            Le = half_e / math.cos(math.radians(ang))
            # build along Y with rotation about Y
            rw = box_local("roof_%s_w" % r["name"][:6], (ridge, y0, ridge_z), (Lw, y1 - y0, thick), 0, mat, self.col_roof, rot_y_deg=ang)
            # rotate so local +X goes toward -X and down: rot_z 180 then rot_y ang? use rot_z=180 with rot_y=-ang
            bpy.data.objects.remove(rw, do_unlink=True)
            rw = box_local("roof_%s_w" % r["name"][:6], (ridge, y1, ridge_z), (Lw, y1 - y0, thick), 180, mat, self.col_roof, rot_y_deg=ang)
            re = box_local("roof_%s_e" % r["name"][:6], (ridge, y0, ridge_z), (Le, y1 - y0, thick), 0, mat, self.col_roof, rot_y_deg=ang)
            for ob in (rw, re):
                set_face_material(ob, 0, soffit)
            box_ft("ridge_%s" % r["name"][:6], ridge - 0.3, y0, ridge + 0.3, y1, ridge_z + thick - 0.1, ridge_z + thick + 0.12, mat, self.col_roof)
            prof = [(x0 + r.get("eave_ft", 3.0), r["z_wall"] - 0.6), (x1 - r.get("eave_ft", 3.0), r["z_wall"] - 0.6), (ridge, ridge_z + 0.2)]
            ced = self.mats.get("cedar_ext")
            gy0, gy1 = y0 + r.get("rake_ft", 3.0), y1 - r.get("rake_ft", 3.0)
            prism_xz("gable_%s_s" % r["name"][:6], prof, gy0, gy0 + 1.0, ced, self.col_roof)
            prism_xz("gable_%s_n" % r["name"][:6], prof, gy1 - 1.0, gy1, ced, self.col_roof)

    def shed(self, r):
        mat = self.mats.get(r["m"])
        soffit = self.mats.get(r.get("soffit_m", "cedar_ext"))
        x0, x1, y0, y1 = r["x0"], r["x1"], r["y0"], r["y1"]
        thick = r.get("thick", 0.5)
        to = r.get("slope_to", "south")
        zh, zl = r["z_high"], r["z_low"]
        if to in ("south", "north"):
            L = y1 - y0
            ang = math.degrees(math.atan((zh - zl) / L))
            if to == "south":
                ob = box_local("roof_%s" % r["name"].replace(" ", "_"), (x1, y1, zh), (x1 - x0, L / math.cos(math.radians(ang)), thick), 180, mat, self.col_roof, rot_x_deg=-ang)
            else:
                ob = box_local("roof_%s" % r["name"].replace(" ", "_"), (x0, y0, zh), (x1 - x0, L / math.cos(math.radians(ang)), thick), 0, mat, self.col_roof, rot_x_deg=-ang)
        else:
            L = x1 - x0
            ang = math.degrees(math.atan((zh - zl) / L))
            if to == "east":
                ob = box_local("roof_%s" % r["name"].replace(" ", "_"), (x0, y0, zh), (L / math.cos(math.radians(ang)), y1 - y0, thick), 0, mat, self.col_roof, rot_y_deg=ang)
            else:
                ob = box_local("roof_%s" % r["name"].replace(" ", "_"), (x1, y1, zh), (L / math.cos(math.radians(ang)), y1 - y0, thick), 180, mat, self.col_roof, rot_y_deg=ang)
        set_face_material(ob, 0, soffit)
        fas = self.mats.get("bronze_black")
        fh = r.get("fascia", 1.0)
        # fascia on the low edge
        if to == "south":
            box_ft("fascia_%s" % r["name"][:8], x0, y0 - 0.15, x1, y0, zl - fh + thick, zl + thick + 0.05, fas, self.col_roof)
        elif to == "north":
            box_ft("fascia_%s" % r["name"][:8], x0, y1, x1, y1 + 0.15, zl - fh + thick, zl + thick + 0.05, fas, self.col_roof)
        elif to == "east":
            box_ft("fascia_%s" % r["name"][:8], x1, y0, x1 + 0.15, y1, zl - fh + thick, zl + thick + 0.05, fas, self.col_roof)
        else:
            box_ft("fascia_%s" % r["name"][:8], x0 - 0.15, y0, x0, y1, zl - fh + thick, zl + thick + 0.05, fas, self.col_roof)
        self.posts_and_beams(r, zl)

    def flat(self, r):
        mat = self.mats.get(r["m"])
        soffit = self.mats.get(r.get("soffit_m", "cedar_ext"))
        x0, x1, y0, y1 = r["x0"], r["x1"], r["y0"], r["y1"]
        thick = r.get("thick", 0.5)
        ob = box_ft("roof_%s" % r["name"].replace(" ", "_"), x0, y0, x1, y1, r["z"], r["z"] + thick, mat, self.col_roof)
        set_face_material(ob, 0, soffit)
        fas = self.mats.get("bronze_black")
        fh = r.get("fascia", 1.0)
        for nm, b in (("s", [x0, y0 - 0.15, x1, y0]), ("n", [x0, y1, x1, y1 + 0.15]), ("w", [x0 - 0.15, y0, x0, y1]), ("e", [x1, y0, x1 + 0.15, y1])):
            box_ft("fascia_%s_%s" % (r["name"][:8], nm), b[0], b[1], b[2], b[3], r["z"] - fh + thick, r["z"] + thick + 0.05, fas, self.col_roof)
        self.posts_and_beams(r, r["z"])

    def posts_and_beams(self, r, z_under):
        ced = self.mats.get("cedar_ext")
        ps = r.get("post_size", 0.67)
        for (px, py) in r.get("posts", []):
            box_ft("post_%s_%d_%d" % (r["name"][:6], int(px), int(py)), px - ps / 2, py - ps / 2, px + ps / 2, py + ps / 2, r.get("post_z0", self.gz), z_under, ced, self.col_roof)
        bm = r.get("beams")
        if bm:
            w = bm.get("w_in", 6) / 12.0
            d = bm.get("d_in", 12) / 12.0
            x0, x1, y0, y1 = r["x0"], r["x1"], r["y0"], r["y1"]
            if bm.get("axis", "x") == "x":
                y = y0 + bm["spacing"] / 2
                while y < y1:
                    box_ft("beam_%s_%d" % (r["name"][:6], int(y * 10)), x0 + 0.3, y - w / 2, x1 - 0.3, y + w / 2, z_under - d, z_under, ced, self.col_roof)
                    y += bm["spacing"]
            else:
                x = x0 + bm["spacing"] / 2
                while x < x1:
                    box_ft("beam_%s_%d" % (r["name"][:6], int(x * 10)), x - w / 2, y0 + 0.3, x + w / 2, y1 - 0.3, z_under - d, z_under, ced, self.col_roof)
                    x += bm["spacing"]

    # ------------------------------------------------------------------ house exterior extras
    def build_bands(self):
        ex = self.plan.get("exterior", {})
        X0, Y0, X1, Y1 = self.footprint("main")
        brick = self.mats.get(ex.get("base", {}).get("m_out", "roman_brick"))
        # foundation band from grade to the main floor, outside face flush with the wall face
        gz = self.gz
        box_ft("found_s", X0, Y0, X1, Y0 + 1.0, gz - 0.8, 0.0, brick, self.col)
        box_ft("found_n", X0, Y1 - 1.0, X1, Y1, gz - 0.8, 0.0, brick, self.col)
        box_ft("found_w", X0, Y0 + 1.0, X0 + 1.0, Y1 - 1.0, gz - 0.8, 0.0, brick, self.col)
        box_ft("found_e", X1 - 1.0, Y0 + 1.0, X1, Y1 - 1.0, gz - 0.8, 0.0, brick, self.col)
        # reveal band between brick base and cedar upper (east, west, north only)
        up = ex.get("upper", {})
        rv = up.get("reveal")
        if rv and any(r["floor"] == "second" for r in self.house.rooms):
            sx0, sy0, sx1, sy1 = self.footprint("second", skip_void=True)
            bm = self.mats.get(rv["m"])
            box_ft("reveal_n", sx0, sy1 - 0.5, sx1, sy1 + 0.02, rv["z0"], rv["z1"], bm, self.col)
            box_ft("reveal_w", sx0 - 0.02, sy0, sx0 + 0.5, sy1, rv["z0"], rv["z1"], bm, self.col)
            box_ft("reveal_e", sx1 - 0.5, sy0, sx1 + 0.02, sy1, rv["z0"], rv["z1"], bm, self.col)
        for bd in ex.get("bands", []):
            box_ft("band_%s" % bd["note"].replace(" ", "_")[:24], *bd["b"], mat=self.mats.get(bd["m"]), collection=self.col)
        # stair tower: cedar parapet from the second-floor ceiling to the cap, bronze reveal at the brick line
        tw = ex.get("tower")
        if tw:
            b, inner = tw["b"], tw["inner"]
            ced = self.mats.get(tw.get("m", "cedar_ext"))
            zt0, zt1 = tw["z_wall_top"], tw["z_top"]
            box_ft("tower_par_s", b[0], b[1], b[2], inner[1], zt0, zt1, ced, self.col)
            box_ft("tower_par_n", b[0], inner[3], b[2], b[3], zt0, zt1, ced, self.col)
            box_ft("tower_par_w", b[0], inner[1], inner[0], inner[3], zt0, zt1, ced, self.col)
            box_ft("tower_par_e", inner[2], inner[1], b[2], inner[3], zt0, zt1, ced, self.col)
            trv = tw.get("reveal")
            if trv:
                bm = self.mats.get(trv["m"])
                box_ft("tower_reveal_s", b[0] - 0.02, b[1] - 0.02, b[2] + 0.02, b[1] + 0.5, trv["z0"], trv["z1"], bm, self.col)
                box_ft("tower_reveal_w", b[0] - 0.02, b[1], b[0] + 0.5, b[3], trv["z0"], trv["z1"], bm, self.col)
                box_ft("tower_reveal_e", b[2] - 0.5, b[1], b[2] + 0.02, b[3], trv["z0"], trv["z1"], bm, self.col)
        # vent chase
        ch = ex.get("chase")
        if ch:
            b = ch["b"]
            box_ft("chase", *b, mat=self.mats.get(ch["m"]), collection=self.col)
            box_ft("chase_cap", b[0] - 0.1, b[1] - 0.1, b[2] + 0.1, b[3] + 0.1, b[5], b[5] + 0.25, self.mats.get(ch.get("cap_m", "steel_black")), self.col)
        # garage: cedar above the brick split
        g = ex.get("garage")
        if g and any(r["floor"] == "garage" for r in self.house.rooms):
            gx0, gy0, gx1, gy1 = self.footprint("garage")
            ced = self.mats.get(g["m_out_high"])
            zs = g["split_z"]
            zt = self.plan["floors"]["garage"]["z"] + self.plan["floors"]["garage"]["h"] + 0.3
            t = 0.06
            box_ft("gar_cedar_s", gx0 - t, gy0 - t, gx1 + t, gy0, zs, zt, ced, self.col)
            box_ft("gar_cedar_n", gx0 - t, gy1, gx1 + t, gy1 + t, zs, zt, ced, self.col)
            box_ft("gar_cedar_w", gx0 - t, gy0, gx0, gy1, zs, zt, ced, self.col)
            box_ft("gar_cedar_e", gx1, gy0, gx1 + t, gy1, zs, zt, ced, self.col)
        self.n("bands")

    # ------------------------------------------------------------------ site
    def build_site(self):
        s = self.plan.get("site", {})
        gz = self.gz
        g = s.get("ground")
        if g:
            b = g["b"]
            box_ft("ground", b[0], b[1], b[2], b[3], gz - 1.0, gz, self.mats.get(g.get("m", "lawn")), self.col, {"kind": "ground"})
            # carve the house and garage footprints out of the ground so basements stay dark and slabs sit flush
            for fl in ("main", "garage"):
                if any(r["floor"] == fl for r in self.house.rooms):
                    X0, Y0, X1, Y1 = self.footprint(fl)
                    cut_with_box([bpy.data.objects["ground"]], [X0, Y0, X1, Y1, gz - 2, gz + 1], "cut_ground")
        for sl in s.get("slabs", []):
            b = sl["b"]
            if sl.get("cut_ground") and g:
                cut_with_box([bpy.data.objects["ground"]], [b[0], b[1], b[2], b[3], sl["z"] - 0.01, gz + 1], "cut_slab")
            box_ft("slab_%s" % sl["note"].replace(" ", "_"), b[0], b[1], b[2], b[3], sl["z"] - sl.get("t", 0.3), sl["z"], self.mats.get(sl["m"]), self.col)
        bed_m = self.mats.get("gravel_gray")
        import random
        rnd = random.Random(3)
        leaf = self.mats.get("olive_paint")
        for bd in s.get("beds", []):
            b = bd["b"]
            box_ft("bed_%s" % bd["note"].replace(" ", "_"), b[0], b[1], b[2], b[3], gz - 0.1, gz + 0.05, self.mats.get("concrete_sealed"), self.col)
            # low planting: grasses and boxwood mounds under 3 ft
            n = int((b[2] - b[0]) * (b[3] - b[1]) / 12)
            for i in range(n):
                px, py = rnd.uniform(b[0] + 0.5, b[2] - 0.5), rnd.uniform(b[1] + 0.5, b[3] - 0.5)
                r = rnd.uniform(0.6, 1.1)
                sp = sphere_ft("plant_%s_%d" % (bd["note"][:6], i), (px, py, gz + r * 0.5), r, leaf, self.col, 10, 6)
                sp.scale = (1, 1, 0.8)
        for h in s.get("hedges", []):
            b = h["b"]
            box_ft("hedge_%s" % h["note"].replace(" ", "_"), b[0], b[1], b[2], b[3], gz, gz + h["h"], self.mats.get("leaf"), self.col)
        self.build_wells()
        for i, t in enumerate(s.get("trees", [])):
            self.tree(i, t)
        for nb in s.get("neighbors", []):
            self.neighbor(nb)
        for st in s.get("structures", []):
            self.structure(st)
        self.n("site items", len(s.get("slabs", [])) + len(s.get("structures", [])))

    def build_wells(self):
        """Window wells for basement openings flagged well=True: a cavity cut from the ground outside the wall,
        galvanized liner, gravel floor, a steel grate at grade and a ladder when the well is deeper than 44 in."""
        gz = self.gz
        ext_t = self.house.ext_t
        steel = self.mats.get("stainless")
        dark = self.mats.get("steel_black")
        gravel = self.mats.get("gravel_gray")
        ground = bpy.data.objects.get("ground")
        for op in self.plan["openings"]:
            if not op.get("well"):
                continue
            fl = self.plan["floors"][op["floor"]]
            sill = fl["z"] + op.get("z0", 0)
            zf = sill - 0.5                       # well floor 6 in below the sill
            depth = 3.0                           # projection from the wall face
            w = op["w"] + 1.0                     # 6 in wider than the window each side
            c = op["c"]
            X0, Y0, X1, Y1 = self.footprint("main")
            if op["axis"] == "y":                 # wall runs along Y at X = at
                out = -1 if op["at"] <= X0 + 1e-6 else 1
                face = op["at"]                    # exterior walls sit inside the room line; the face is on it
                b = [min(face, face + out * depth), c - w / 2, max(face, face + out * depth), c + w / 2]
            else:
                out = -1 if op["at"] <= Y0 + 1e-6 else 1
                face = op["at"]
                b = [c - w / 2, min(face, face + out * depth), c + w / 2, max(face, face + out * depth)]
            tag = op["note"].replace(" ", "_")
            if ground is not None:
                cut_with_box([ground], [b[0], b[1], b[2], b[3], zf - 1, gz + 1], "cut_well")
            # the foundation band runs through the window head: cut it with the opening
            z0o, z1o = sill, sill + op["h"]
            # the wall sits inside the room line: X/Y at..at+ext_t on the west/south sides, at-ext_t..at on the east/north
            lo_w, hi_w = (op["at"] - 0.1, op["at"] + ext_t + 0.1) if out < 0 else (op["at"] - ext_t - 0.1, op["at"] + 0.1)
            if op["axis"] == "y":
                ob_box = [lo_w, c - op["w"] / 2, hi_w, c + op["w"] / 2, z0o, z1o]
            else:
                ob_box = [c - op["w"] / 2, lo_w, c + op["w"] / 2, hi_w, z0o, z1o]
            found = [o for o in bpy.data.objects if o.name.startswith("found_") and overlap(bounds_of(o), ob_box)]
            if found:
                cut_with_box(found, ob_box, "cut_found")
            for sl in [o for o in bpy.data.objects if o.name.startswith("slab_") and overlap(bounds_of(o), [b[0], b[1], b[2], b[3], zf, gz + 1])]:
                cut_with_box([sl], [b[0], b[1], b[2], b[3], zf - 1, gz + 1], "cut_well")
            # liner: three sides (the fourth is the house wall), 1 in thick, 4 in above grade
            t = 0.08
            top = gz + 0.35
            if op["axis"] == "y":
                box_ft("well_%s_s" % tag, b[0], b[1] - t, b[2], b[1], zf, top, steel, self.col)
                box_ft("well_%s_n" % tag, b[0], b[3], b[2], b[3] + t, zf, top, steel, self.col)
                xo = b[0] - t if out < 0 else b[2]
                box_ft("well_%s_o" % tag, xo, b[1] - t, xo + t, b[3] + t, zf, top, steel, self.col)
            else:
                box_ft("well_%s_w" % tag, b[0] - t, b[1], b[0], b[3], zf, top, steel, self.col)
                box_ft("well_%s_e" % tag, b[2], b[1], b[2] + t, b[3], zf, top, steel, self.col)
                yo = b[1] - t if out < 0 else b[3]
                box_ft("well_%s_o" % tag, b[0] - t, yo, b[2] + t, yo + t, zf, top, steel, self.col)
            box_ft("well_%s_floor" % tag, b[0], b[1], b[2], b[3], zf - 0.2, zf, gravel, self.col)
            # grate: bars every 4 in across the short direction, flush with the liner top
            gtop = top
            if op["axis"] == "y":
                y = b[1] + 0.2
                while y < b[3]:
                    box_ft("grate_%s_%d" % (tag, int(y * 10)), b[0], y - 0.03, b[2], y + 0.03, gtop - 0.15, gtop, dark, self.col)
                    y += 0.33
            else:
                x = b[0] + 0.2
                while x < b[2]:
                    box_ft("grate_%s_%d" % (tag, int(x * 10)), x - 0.03, b[1], x + 0.03, b[3], gtop - 0.15, gtop, dark, self.col)
                    x += 0.33
            # ladder on the outer liner when the well is deeper than 44 in (egress)
            if gz - zf > 44 / 12:
                if op["axis"] == "y":
                    xl = (b[0] + 0.15) if out < 0 else (b[2] - 0.15)
                    for zz in [zf + 1 + k for k in range(int(gz - zf - 1))]:
                        box_ft("ladder_%s_%d" % (tag, int(zz * 10)), xl - 0.05, c - 0.75, xl + 0.05, c + 0.75, zz, zz + 0.08, dark, self.col)
                    box_ft("ladder_%s_ra" % tag, xl - 0.05, c - 0.75, xl + 0.05, c - 0.7, zf + 0.5, gz + 0.3, dark, self.col)
                    box_ft("ladder_%s_rb" % tag, xl - 0.05, c + 0.7, xl + 0.05, c + 0.75, zf + 0.5, gz + 0.3, dark, self.col)
                else:
                    yl = (b[1] + 0.15) if out < 0 else (b[3] - 0.15)
                    for zz in [zf + 1 + k for k in range(int(gz - zf - 1))]:
                        box_ft("ladder_%s_%d" % (tag, int(zz * 10)), c - 0.75, yl - 0.05, c + 0.75, yl + 0.05, zz, zz + 0.08, dark, self.col)
                    box_ft("ladder_%s_ra" % tag, c - 0.75, yl - 0.05, c - 0.7, yl + 0.05, zf + 0.5, gz + 0.3, dark, self.col)
                    box_ft("ladder_%s_rb" % tag, c + 0.7, yl - 0.05, c + 0.75, yl + 0.05, zf + 0.5, gz + 0.3, dark, self.col)
            self.n("window wells")

    def tree(self, i, t):
        gz = self.gz
        x, y = t["pos"]
        trunk = self.mats.get("walnut")
        leaf = self.mats.get("leaf_autumn" if t.get("autumn") else "leaf")
        r = t["canopy_r"]
        zc = t["canopy_z"]
        cylinder_ft("tree_%d_trunk" % i, (x, y, gz), t["trunk_d"] / 2, zc + r * 0.6, trunk, self.col, 12)
        import random
        rnd = random.Random(i + 11)
        for j in range(5):
            rr = r * rnd.uniform(0.45, 0.7)
            ox, oy = rnd.uniform(-r * 0.4, r * 0.4), rnd.uniform(-r * 0.4, r * 0.4)
            sp = sphere_ft("tree_%d_crown_%d" % (i, j), (x + ox, y + oy, gz + zc + rr * 0.6 + j * r * 0.12), rr, leaf, self.col, 14, 8)
            sp.scale = (1, 1, 0.7)

    def neighbor(self, nb):
        b = nb["b"]
        gz = self.gz
        m_ = self.mats.get(nb.get("m", "roman_brick"))
        box_ft("nbr_%s" % nb["note"].replace(" ", "_"), b[0], b[1], b[2], b[3], gz, nb["eave_z"], m_, self.col)
        roof = self.mats.get("metal_roof_charcoal")
        if nb.get("ridge_axis", "y") == "y":
            prof = [(b[0] - 1.5, nb["eave_z"]), (b[2] + 1.5, nb["eave_z"]), ((b[0] + b[2]) / 2, nb["ridge_z"])]
            prism_xz("nbr_roof_%s" % nb["note"][:5], prof, b[1] - 1.5, b[3] + 1.5, roof, self.col)
        else:
            prof = [(b[1] - 1.5, nb["eave_z"]), (b[3] + 1.5, nb["eave_z"]), ((b[1] + b[3]) / 2, nb["ridge_z"])]
            prism_yz("nbr_roof_%s" % nb["note"][:5], prof, b[0] - 1.5, b[2] + 1.5, roof, self.col)

    def structure(self, st):
        k = st["kind"]
        nm = "st_%s" % st["note"].replace(" ", "_")
        mat = self.mats.get(st.get("m", "concrete_sealed"))
        if k == "box":
            if st.get("hollow"):
                b = st["b"]
                t = 0.15
                box_ft(nm + "_s", b[0], b[1], b[2], b[1] + t, b[4], b[5], mat, self.col)
                box_ft(nm + "_n", b[0], b[3] - t, b[2], b[3], b[4], b[5], mat, self.col)
                box_ft(nm + "_w", b[0], b[1], b[0] + t, b[3], b[4], b[5], mat, self.col)
                box_ft(nm + "_e", b[2] - t, b[1], b[2], b[3], b[4], b[5], mat, self.col)
            else:
                box_ft(nm, *st["b"], mat=mat, collection=self.col)
        elif k == "ring":
            b, i = st["b"], st["inner"]
            z0, z1 = st["z0"], st["z1"]
            box_ft(nm + "_s", b[0], b[1], b[2], i[1], z0, z1, mat, self.col)
            box_ft(nm + "_n", b[0], i[3], b[2], b[3], z0, z1, mat, self.col)
            box_ft(nm + "_w", b[0], i[1], i[0], i[3], z0, z1, mat, self.col)
            box_ft(nm + "_e", i[2], i[1], b[2], i[3], z0, z1, mat, self.col)
        elif k == "steps":
            b = st["b"]
            n = st.get("n", 2)
            dz = (st["z1"] - st["z0"]) / n
            dy = (b[3] - b[1]) / n
            for j in range(n):
                box_ft(nm + "_%d" % j, b[0], b[1] + j * dy, b[2], b[3], st["z0"], st["z0"] + (j + 1) * dz, mat, self.col)
        elif k == "frame":
            b = st["b"]
            p = st.get("post", 0.33)
            xs = [b[0], (b[0] + b[2]) / 2, b[2] - p]
            for x in (b[0], b[2] - p):
                for y in (b[1], b[3] - p):
                    box_ft(nm + "_post_%d_%d" % (int(x), int(y)), x, y, x + p, y + p, b[4], b[5], mat, self.col)
            box_ft(nm + "_post_mid", b[2] - p, (b[1] + b[3]) / 2 - p / 2, b[2], (b[1] + b[3]) / 2 + p / 2, b[4], b[5], mat, self.col)
            box_ft(nm + "_plate_s", b[0], b[1], b[2], b[1] + p, b[5] - p, b[5], mat, self.col)
            box_ft(nm + "_plate_n", b[0], b[3] - p, b[2], b[3], b[5] - p, b[5], mat, self.col)
            box_ft(nm + "_plate_e", b[2] - p, b[1], b[2], b[3], b[5] - p, b[5], mat, self.col)
            scr = self.mats.get(st.get("screen_m", "screen_black"))
            gl = get_collection("glass")
            box_ft(nm + "_screen_e", b[2] - 0.02, b[1], b[2], b[3], b[4] + 0.3, b[5] - p, scr, gl)
            box_ft(nm + "_screen_s", b[0], b[1], b[2], b[1] + 0.02, b[4] + 0.3, b[5] - p, scr, gl)
            box_ft(nm + "_screen_n", b[0], b[3] - 0.02, b[2], b[3], b[4] + 0.3, b[5] - p, scr, gl)
            box_ft(nm + "_screen_top", b[0], b[1], b[2], b[3], b[5] - 0.02, b[5], scr, gl)
        elif k == "slats":
            b = st["b"]
            sw, gap = st.get("slat_w", 0.29), st.get("gap", 0.17)
            y = b[1]
            j = 0
            while y < b[3] - sw:
                box_ft(nm + "_%d" % j, b[0], y, b[2], y + sw, b[4], b[5], mat, self.col)
                y += sw + gap
                j += 1
        elif k == "cylinder":
            cylinder_ft(nm, (st["pos"][0], st["pos"][1], st["z0"]), st["r"], st["z1"] - st["z0"], mat, self.col, 12)

    def build_all(self):
        self.build_bands()
        self.build_roofs()
        self.build_site()
        log("site:", ", ".join("%s %d" % kv for kv in sorted(self.counts.items())))


def build(plan, house, mats):
    s = Site(plan, house, mats)
    s.build_all()
    house.site = s
    if "neighborhood" in plan.get("site", {}):
        import neighborhood
        from staging import Stager
        import os
        stager = Stager(plan, house, mats, os.path.dirname(os.path.abspath(__file__)))
        neighborhood.build(plan, house, mats, stager)
    return s
