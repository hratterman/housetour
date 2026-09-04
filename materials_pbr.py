"""
materials_pbr.py: Phase 2 material library. Builds Principled BSDF materials with PBR texture sets
from assets/textures/<name>/ using world-space box projection at a physical scale, so nothing needs
UV work. Falls back to the flat Phase 1 material when a texture set is missing.

Material spec keys (materials/materials.json), all optional beyond rgb/rough:
    tex        texture folder name under assets/textures
    size_ft    physical size in feet of one texture tile (default 4)
    rot        rotation in degrees about Z for plank / course direction (default 0)
    tint       [r,g,b] multiplied into the diffuse map
    paint      true: use only the texture's roughness/normal, color comes from rgb (painted plaster)
    bump       normal map strength (default 0.6)
    rough_mul  multiply roughness map (default 1.0)
    rough_add  add to roughness (default 0.0)
    metallic, emit, transmission, ior, thin   as in Phase 1
    overlay    {"type": "stripes"|"geo_wallpaper"|"botanical_wallpaper"|"tile_backsplash", ...}
"""
import os

import bpy

FT = 0.3048


def _img(path, colorspace):
    key = os.path.abspath(path)
    for im in bpy.data.images:
        if im.filepath and os.path.abspath(bpy.path.abspath(im.filepath)) == key:
            return im
    im = bpy.data.images.load(path)
    im.colorspace_settings.name = colorspace
    return im


def world_empty():
    ob = bpy.data.objects.get("tex_origin")
    if ob is None:
        ob = bpy.data.objects.new("tex_origin", None)
        ob.empty_display_size = 0.1
        bpy.context.scene.collection.objects.link(ob)
        ob.hide_render = True
        ob.hide_viewport = True
    return ob


PREFER_2K = False      # set by build_scene for renders under 1280 wide: the 15 GB build box cannot hold the 4k sets


class PBRLibrary:
    def __init__(self, root, specs):
        self.root = root
        self.specs = specs
        self.tex_root = os.path.join(root, "assets", "textures")
        self.cache = {}
        self.available = set()
        if os.path.isdir(self.tex_root):
            for d in os.listdir(self.tex_root):
                if os.path.exists(os.path.join(self.tex_root, d, "diffuse.jpg")):
                    self.available.add(d)
        self.missing = set()

    def summary(self):
        return "%d texture sets on disk" % len(self.available)

    def get(self, name):
        if name in self.cache:
            return self.cache[name]
        spec = self.specs[name]
        mat = self.build(name, spec)
        self.cache[name] = mat
        return mat

    # ------------------------------------------------------------------ builders
    def _flame(self, mat, spec):
        """Flame shader for the fire ellipsoids: emission graded from white-yellow at the base to deep orange at the tip,
        eaten away by noise and fading to transparent toward the top, so the shells read as flame tongues."""
        nt = mat.node_tree
        nodes, links = nt.nodes, nt.links
        for n in list(nodes):
            nodes.remove(n)
        out = nodes.new("ShaderNodeOutputMaterial")
        tc = nodes.new("ShaderNodeTexCoord")
        sep = nodes.new("ShaderNodeSeparateXYZ")
        # Generated coordinates run 0..1 across the object's bounding box whatever its size or scale, so z is the
        # height up the flame directly
        links.new(tc.outputs["Generated"], sep.inputs[0])
        zmap = nodes.new("ShaderNodeMapRange")
        zmap.inputs["From Min"].default_value = 0.0
        zmap.inputs["From Max"].default_value = 1.0
        links.new(sep.outputs["Z"], zmap.inputs["Value"])
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 3.0
        noise.inputs["Detail"].default_value = 5.0
        noise.inputs["Roughness"].default_value = 0.6
        links.new(tc.outputs["Generated"], noise.inputs["Vector"])
        # alpha = (1 - z) * (noise * 1.6 - 0.2), clamped
        nz = nodes.new("ShaderNodeMath"); nz.operation = "MULTIPLY_ADD"
        nz.inputs[1].default_value = 1.6; nz.inputs[2].default_value = -0.25
        links.new(noise.outputs["Fac"], nz.inputs[0])
        inv = nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        links.new(zmap.outputs["Result"], inv.inputs[1])
        pw = nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 0.6
        links.new(inv.outputs[0], pw.inputs[0])
        al = nodes.new("ShaderNodeMath"); al.operation = "MULTIPLY"; al.use_clamp = True
        links.new(pw.outputs[0], al.inputs[0]); links.new(nz.outputs[0], al.inputs[1])
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (1.0, 0.85, 0.45, 1.0)
        ramp.color_ramp.elements[1].position = 1.0
        ramp.color_ramp.elements[1].color = (1.0, 0.18, 0.02, 1.0)
        mid = ramp.color_ramp.elements.new(0.45)
        mid.color = (1.0, 0.45, 0.06, 1.0)
        links.new(zmap.outputs["Result"], ramp.inputs["Fac"])
        em = nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = spec.get("emit", 5.0)
        links.new(ramp.outputs["Color"], em.inputs["Color"])
        tr = nodes.new("ShaderNodeBsdfTransparent")
        mix = nodes.new("ShaderNodeMixShader")
        links.new(al.outputs[0], mix.inputs["Fac"])
        links.new(tr.outputs[0], mix.inputs[1])
        links.new(em.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], out.inputs["Surface"])
        mat.blend_method = "HASHED"
        try:
            mat.shadow_method = "NONE"
        except Exception:
            pass
        try:
            mat.cycles.use_transparent_shadow = True
        except Exception:
            pass

    def build(self, name, spec):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        nodes, links = nt.nodes, nt.links
        if spec.get("kind") == "flame":
            self._flame(mat, spec)
            return mat
        bsdf = nodes.get("Principled BSDF")
        rgb = spec.get("rgb", [0.8, 0.8, 0.8])
        bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        bsdf.inputs["Roughness"].default_value = spec.get("rough", 0.5)
        bsdf.inputs["Metallic"].default_value = spec.get("metallic", 0.0)
        if "ior" in spec:
            bsdf.inputs["IOR"].default_value = spec["ior"]
        if spec.get("transmission"):
            bsdf.inputs["Transmission Weight"].default_value = spec["transmission"]
        if spec.get("emit"):
            ec = spec.get("emit_rgb", rgb)
            if spec.get("wb", True):
                import geom
                ec = [ec[i] * geom.WB[i] for i in range(3)]     # lamp glows follow the camera white balance
            bsdf.inputs["Emission Color"].default_value = (ec[0], ec[1], ec[2], 1.0)
            bsdf.inputs["Emission Strength"].default_value = spec["emit"]
        if spec.get("thin"):
            mat.blend_method = "HASHED"
        if "alpha" in spec:
            bsdf.inputs["Alpha"].default_value = spec["alpha"]   # insect screen, sheer fabric
        if spec.get("coat"):
            bsdf.inputs["Coat Weight"].default_value = spec["coat"]
            bsdf.inputs["Coat Roughness"].default_value = spec.get("coat_rough", 0.1)
        if spec.get("sheen"):
            bsdf.inputs["Sheen Weight"].default_value = spec["sheen"]
        if "spec" in spec:
            bsdf.inputs["Specular IOR Level"].default_value = spec["spec"]

        tex = spec.get("tex")
        color_socket = None
        if tex and tex in self.available:
            color_socket = self._wire_textures(nt, bsdf, spec, tex)
        elif tex:
            self.missing.add(tex)

        ov = spec.get("overlay")
        if ov:
            self._wire_overlay(nt, bsdf, spec, ov, color_socket)
        if spec.get("transmission", 0) >= 0.5 and spec.get("shadow_transparent", True):
            # Cycles blocks shadow rays at refractive surfaces, so sun and sky light sampled through
            # window glass never reached the interiors (only multi-bounce paths did). Let shadow rays
            # pass as tinted transparency, the standard archviz trick; the camera still sees glass.
            out = next((n for n in nodes if n.type == "OUTPUT_MATERIAL"), None)
            if out is not None and out.inputs["Surface"].is_linked:
                src = out.inputs["Surface"].links[0].from_socket
                lp = nodes.new("ShaderNodeLightPath")
                tr = nodes.new("ShaderNodeBsdfTransparent")
                t = spec.get("tint", [1.0, 1.0, 1.0])
                tr.inputs["Color"].default_value = (t[0], t[1], t[2], 1.0)
                mix = nodes.new("ShaderNodeMixShader")
                links.new(lp.outputs["Is Shadow Ray"], mix.inputs["Fac"])
                links.new(src, mix.inputs[1])
                links.new(tr.outputs[0], mix.inputs[2])
                links.new(mix.outputs[0], out.inputs["Surface"])
        return mat

    def _mapping(self, nt, spec):
        nodes, links = nt.nodes, nt.links
        tc = nodes.new("ShaderNodeTexCoord")
        tc.object = world_empty()
        mp = nodes.new("ShaderNodeMapping")
        mp.vector_type = "POINT"
        size = spec.get("size_ft", 4.0) * FT
        mp.inputs["Scale"].default_value = (1.0 / size, 1.0 / size, 1.0 / size)
        import math
        mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(spec.get("rot", 0.0)))
        links.new(tc.outputs["Object"], mp.inputs["Vector"])
        return mp

    def _rough_var(self, nt, spec, src, mp):
        """Multiply a roughness signal by a soft noise so large flat surfaces stop reading as uniform plastic."""
        var = spec.get("rough_var", 0.0)
        if not var:
            return src
        nodes, links = nt.nodes, nt.links
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 1.0 / max(spec.get("rough_var_ft", 1.5) * 0.3048, 0.05)
        noise.inputs["Detail"].default_value = 3.0
        noise.inputs["Roughness"].default_value = 0.6
        if mp is not None:
            links.new(mp.outputs["Vector"], noise.inputs["Vector"])
        rng_ = nodes.new("ShaderNodeMapRange")
        rng_.inputs["From Min"].default_value = 0.3
        rng_.inputs["From Max"].default_value = 0.7
        rng_.inputs["To Min"].default_value = 1.0 - var
        rng_.inputs["To Max"].default_value = 1.0 + var
        links.new(noise.outputs["Fac"], rng_.inputs["Value"])
        mul = nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.use_clamp = True
        links.new(src, mul.inputs[0])
        links.new(rng_.outputs["Result"], mul.inputs[1])
        return mul.outputs[0]

    def _image_node(self, nt, folder, mapname, colorspace, mapping):
        path = os.path.join(self.tex_root, folder, mapname + ".jpg")
        if PREFER_2K and os.path.exists(os.path.join(self.tex_root, folder + "_2k", mapname + ".jpg")):
            path = os.path.join(self.tex_root, folder + "_2k", mapname + ".jpg")     # previews: the 2k twin of a 4k hero set
        if not os.path.exists(path):
            return None
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = _img(path, colorspace)
        n.projection = "BOX"
        n.projection_blend = 0.2
        n.interpolation = "Linear"
        nt.links.new(mapping.outputs["Vector"], n.inputs["Vector"])
        return n

    def _wire_textures(self, nt, bsdf, spec, folder):
        nodes, links = nt.nodes, nt.links
        mp = self._mapping(nt, spec)
        out_color = None
        if not spec.get("paint"):
            diff = self._image_node(nt, folder, "diffuse", "sRGB", mp)
            if diff is not None:
                src = diff.outputs["Color"]
                tint = spec.get("tint")
                if tint:
                    mix = nodes.new("ShaderNodeMix")
                    mix.data_type = "RGBA"
                    mix.blend_type = "MULTIPLY"
                    mix.inputs["Factor"].default_value = 1.0
                    links.new(src, mix.inputs[6])
                    mix.inputs[7].default_value = (tint[0], tint[1], tint[2], 1.0)
                    src = mix.outputs[2]
                # optional hue/sat/value
                hsv = spec.get("hsv")
                if hsv:
                    h = nodes.new("ShaderNodeHueSaturation")
                    h.inputs["Hue"].default_value = hsv[0]
                    h.inputs["Saturation"].default_value = hsv[1]
                    h.inputs["Value"].default_value = hsv[2]
                    links.new(src, h.inputs["Color"])
                    src = h.outputs["Color"]
                links.new(src, bsdf.inputs["Base Color"])
                if spec.get("emit_tex"):
                    links.new(src, bsdf.inputs["Emission Color"])   # screens: the image is what glows
                out_color = src
        rough = self._image_node(nt, folder, "rough", "Non-Color", mp)
        if rough is not None:
            mul = spec.get("rough_mul", 1.0)
            add = spec.get("rough_add", 0.0)
            src = rough.outputs["Color"]
            if mul != 1.0 or add != 0.0:
                mm = nodes.new("ShaderNodeMath")
                mm.operation = "MULTIPLY_ADD"
                mm.inputs[1].default_value = mul
                mm.inputs[2].default_value = add
                mm.use_clamp = True
                links.new(src, mm.inputs[0])
                src = mm.outputs[0]
            src = self._rough_var(nt, spec, src, mp)
            links.new(src, bsdf.inputs["Roughness"])
        elif spec.get("rough_var"):
            val = nodes.new("ShaderNodeValue")
            val.outputs[0].default_value = spec.get("rough", 0.5)
            links.new(self._rough_var(nt, spec, val.outputs[0], mp), bsdf.inputs["Roughness"])
        nor = self._image_node(nt, folder, "normal", "Non-Color", mp)
        if nor is not None:
            nm = nodes.new("ShaderNodeNormalMap")
            nm.space = "OBJECT" if False else "TANGENT"
            # box projection has no proper tangents; use the bump trick via displacement height instead
            # when a displacement map exists, else use the normal map in world space approximation
            nm.inputs["Strength"].default_value = spec.get("bump", 0.6)
            links.new(nor.outputs["Color"], nm.inputs["Color"])
            links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        disp = self._image_node(nt, folder, "disp", "Non-Color", mp)
        if disp is not None and spec.get("disp_bump", 0.0) > 0:
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = spec["disp_bump"]
            bump.inputs["Distance"].default_value = 0.02
            links.new(disp.outputs["Color"], bump.inputs["Height"])
            if nor is not None:
                links.new(nm.outputs["Normal"], bump.inputs["Normal"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        return out_color

    # ------------------------------------------------------------------ procedural overlays
    def _wire_overlay(self, nt, bsdf, spec, ov, base_color_socket):
        nodes, links = nt.nodes, nt.links
        kind = ov.get("type")
        tc = nodes.new("ShaderNodeTexCoord")
        tc.object = world_empty()
        mp = nodes.new("ShaderNodeMapping")
        mp.vector_type = "POINT"
        size = ov.get("size_ft", 2.0) * FT
        mp.inputs["Scale"].default_value = (1.0 / size, 1.0 / size, 1.0 / size)
        links.new(tc.outputs["Object"], mp.inputs["Vector"])
        base = base_color_socket
        rgb = spec.get("rgb", [0.8, 0.8, 0.8])

        def const_color(c):
            n = nodes.new("ShaderNodeRGB")
            n.outputs[0].default_value = (c[0], c[1], c[2], 1.0)
            return n.outputs[0]

        if base is None:
            base = const_color(rgb)

        if kind == "stripes":
            # thin brass divider strips on a grid (terrazzo). Strips are metallic and smooth.
            sep = nodes.new("ShaderNodeSeparateXYZ")
            links.new(mp.outputs["Vector"], sep.inputs[0])
            width = ov.get("width", 0.02)
            masks = []
            for axis in ov.get("axes", (0, 1)):        # axes [2] = horizontal courses (clapboard, standing seam on a wall)
                fr = nodes.new("ShaderNodeMath")
                fr.operation = "FRACT"
                links.new(sep.outputs[axis], fr.inputs[0])
                lt = nodes.new("ShaderNodeMath")
                lt.operation = "LESS_THAN"
                lt.inputs[1].default_value = width
                links.new(fr.outputs[0], lt.inputs[0])
                masks.append(lt.outputs[0])
            if len(masks) > 1:
                mx = nodes.new("ShaderNodeMath")
                mx.operation = "MAXIMUM"
                links.new(masks[0], mx.inputs[0])
                links.new(masks[1], mx.inputs[1])
                mask = mx.outputs[0]
            else:
                mask = masks[0]
            brass = const_color(ov.get("rgb", [0.85, 0.62, 0.30]))
            mix = nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            links.new(mask, mix.inputs["Factor"])
            links.new(base, mix.inputs[6])
            links.new(brass, mix.inputs[7])
            links.new(mix.outputs[2], bsdf.inputs["Base Color"])
            if not ov.get("metallic", True):
                return
            links.new(mask, bsdf.inputs["Metallic"])
            rm = nodes.new("ShaderNodeMix")
            rm.data_type = "FLOAT"
            links.new(mask, rm.inputs["Factor"])
            rm.inputs[2].default_value = spec.get("rough", 0.3)
            rm.inputs[3].default_value = 0.3
            links.new(rm.outputs[0], bsdf.inputs["Roughness"])

        elif kind == "geo_wallpaper":
            # mid-century geometric: overlapping circles on a grid via voronoi-ish distance
            vor = nodes.new("ShaderNodeTexVoronoi")
            vor.feature = "F1"
            vor.distance = "EUCLIDEAN"
            vor.inputs["Randomness"].default_value = 0.0
            vor.inputs["Scale"].default_value = 1.0
            links.new(mp.outputs["Vector"], vor.inputs["Vector"])
            ramp = nodes.new("ShaderNodeValToRGB")
            c0 = ov.get("rgb_a", [0.32, 0.36, 0.20])
            c1 = ov.get("rgb_b", [0.90, 0.85, 0.72])
            ramp.color_ramp.interpolation = "CONSTANT"
            ramp.color_ramp.elements[0].position = 0.0
            ramp.color_ramp.elements[0].color = (c1[0], c1[1], c1[2], 1)
            ramp.color_ramp.elements[1].position = ov.get("split", 0.36)
            ramp.color_ramp.elements[1].color = (c0[0], c0[1], c0[2], 1)
            e = ramp.color_ramp.elements.new(ov.get("split", 0.36) + 0.06)
            e.color = (c1[0], c1[1], c1[2], 1)
            e2 = ramp.color_ramp.elements.new(0.62)
            e2.color = (c0[0], c0[1], c0[2], 1)
            links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
            links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

        elif kind == "botanical_wallpaper":
            # leaves: a voronoi cell field warped by noise, thresholded on distance so each cell reads as a
            # rounded leaf on a dark ground, with a second smaller layer in a lighter tone
            warp = nodes.new("ShaderNodeTexNoise")
            warp.inputs["Scale"].default_value = 1.5
            warp.inputs["Detail"].default_value = 2.0
            links.new(mp.outputs["Vector"], warp.inputs["Vector"])
            add = nodes.new("ShaderNodeVectorMath")
            add.operation = "MULTIPLY_ADD"
            add.inputs[1].default_value = (0.35, 0.35, 0.35)
            links.new(warp.outputs["Color"], add.inputs[0])
            links.new(mp.outputs["Vector"], add.inputs[2])
            c0 = ov.get("rgb_a", [0.08, 0.20, 0.18])
            c1 = ov.get("rgb_b", [0.25, 0.42, 0.28])
            c2 = ov.get("rgb_c", [0.72, 0.55, 0.22])
            base_col = const_color(c0)
            prev = base_col
            for layer, (scale, thr, col) in enumerate(((3.0, 0.30, c1), (5.5, 0.22, c2))):
                vor = nodes.new("ShaderNodeTexVoronoi")
                vor.feature = "F1"
                vor.inputs["Scale"].default_value = scale
                vor.inputs["Randomness"].default_value = 1.0
                links.new(add.outputs[0], vor.inputs["Vector"])
                # stretch cells into leaves by scaling Y before the voronoi
                lt = nodes.new("ShaderNodeMath")
                lt.operation = "LESS_THAN"
                lt.inputs[1].default_value = thr
                links.new(vor.outputs["Distance"], lt.inputs[0])
                mix = nodes.new("ShaderNodeMix")
                mix.data_type = "RGBA"
                links.new(lt.outputs[0], mix.inputs["Factor"])
                links.new(prev, mix.inputs[6])
                links.new(const_color(col), mix.inputs[7])
                prev = mix.outputs[2]
            links.new(prev, bsdf.inputs["Base Color"])

        elif kind == "tile_backsplash":
            # square tiles with grout: brick node gives tile mask + per-tile color variation.
            # Remap coordinates so the pattern lies in the wall plane (xz for walls along X, yz along Y).
            sep = nodes.new("ShaderNodeSeparateXYZ")
            links.new(mp.outputs["Vector"], sep.inputs[0])
            comb = nodes.new("ShaderNodeCombineXYZ")
            plane = ov.get("plane", "xz")
            links.new(sep.outputs[0 if plane[0] == "x" else 1], comb.inputs[0])
            links.new(sep.outputs[2 if plane[1] == "z" else 1], comb.inputs[1])
            br = nodes.new("ShaderNodeTexBrick")
            br.offset = ov.get("offset", 0.0)            # 0 = stacked bond, 0.5 = running bond
            br.inputs["Scale"].default_value = 1.0
            br.inputs["Mortar Size"].default_value = ov.get("grout", 0.03)
            br.inputs["Bias"].default_value = 0.0
            br.inputs["Brick Width"].default_value = ov.get("aspect", 1.0)   # tile width in units of its height (size_ft)
            br.inputs["Row Height"].default_value = 1.0
            ca = ov.get("rgb_a", [0.72, 0.30, 0.10])
            cb = ov.get("rgb_b", [0.92, 0.86, 0.72])
            br.inputs["Color1"].default_value = (ca[0], ca[1], ca[2], 1)
            br.inputs["Color2"].default_value = (cb[0], cb[1], cb[2], 1)
            br.inputs["Mortar"].default_value = (0.85, 0.82, 0.76, 1)
            br.inputs["Mortar Smooth"].default_value = 0.1
            links.new(comb.outputs[0], br.inputs["Vector"])
            links.new(br.outputs["Color"], bsdf.inputs["Base Color"])
            rr = nodes.new("ShaderNodeMath")
            rr.operation = "MULTIPLY_ADD"
            rr.inputs[1].default_value = 0.7
            rr.inputs[2].default_value = 0.15
            links.new(br.outputs["Fac"], rr.inputs[0])
            links.new(rr.outputs[0], bsdf.inputs["Roughness"])
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.4
            links.new(br.outputs["Fac"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

        elif kind == "runner":
            # striped kilim-style runner: stripes along the long axis with two accent colors
            sep = nodes.new("ShaderNodeSeparateXYZ")
            links.new(mp.outputs["Vector"], sep.inputs[0])
            axis = 0 if ov.get("along", "y") == "y" else 1
            fr = nodes.new("ShaderNodeMath")
            fr.operation = "FRACT"
            links.new(sep.outputs[axis], fr.inputs[0])
            ramp = nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.interpolation = "CONSTANT"
            cols = ov.get("colors", [[0.32, 0.08, 0.09], [0.75, 0.58, 0.16], [0.08, 0.32, 0.36], [0.85, 0.78, 0.65]])
            ramp.color_ramp.elements[0].position = 0
            ramp.color_ramp.elements[0].color = (*cols[0], 1)
            ramp.color_ramp.elements[1].position = 0.15
            ramp.color_ramp.elements[1].color = (*cols[1], 1)
            pos = [0.25, 0.55, 0.62, 0.85]
            for i, p in enumerate(pos):
                e = ramp.color_ramp.elements.new(p)
                c = cols[(i + 2) % len(cols)]
                e.color = (c[0], c[1], c[2], 1)
            links.new(fr.outputs[0], ramp.inputs["Fac"])
            if base_color_socket is not None:
                mix = nodes.new("ShaderNodeMix")
                mix.data_type = "RGBA"
                mix.blend_type = "MULTIPLY"
                mix.inputs["Factor"].default_value = 0.85
                links.new(ramp.outputs["Color"], mix.inputs[6])
                links.new(base_color_socket, mix.inputs[7])
                links.new(mix.outputs[2], bsdf.inputs["Base Color"])
            else:
                links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

        elif kind == "abstract_art":
            # procedural canvas: color blocks from a low-frequency voronoi plus a few stripes
            seed = ov.get("seed", 0)
            vor = nodes.new("ShaderNodeTexVoronoi")
            vor.feature = "F1"
            vor.inputs["Scale"].default_value = 2.0 + (seed % 3)
            vor.inputs["Randomness"].default_value = 0.8
            off = nodes.new("ShaderNodeVectorMath")
            off.operation = "ADD"
            off.inputs[1].default_value = (seed * 3.7, seed * 1.3, seed * 0.7)
            links.new(mp.outputs["Vector"], off.inputs[0])
            links.new(off.outputs[0], vor.inputs["Vector"])
            ramp = nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.interpolation = "CONSTANT"
            palette = ov.get("palette", [[0.72, 0.30, 0.10], [0.90, 0.85, 0.72], [0.08, 0.32, 0.36],
                                         [0.75, 0.58, 0.16], [0.32, 0.08, 0.09], [0.15, 0.15, 0.14]])
            k = len(palette)
            ramp.color_ramp.elements[0].position = 0
            ramp.color_ramp.elements[0].color = (*palette[seed % k], 1)
            ramp.color_ramp.elements[1].position = 1.0 / k
            ramp.color_ramp.elements[1].color = (*palette[(seed + 1) % k], 1)
            for i in range(2, k):
                e = ramp.color_ramp.elements.new(i / k)
                c = palette[(seed + i) % k]
                e.color = (c[0], c[1], c[2], 1)
            links.new(vor.outputs["Color"], ramp.inputs["Fac"])
            # canvas texture bump
            nz = nodes.new("ShaderNodeTexNoise")
            nz.inputs["Scale"].default_value = 400
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.15
            links.new(nz.outputs["Fac"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
            links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
            bsdf.inputs["Roughness"].default_value = 0.8
