"""
geom.py: geometry helpers shared by build_scene.py and the Phase 2 modules. Feet in, Blender meters out.
"""
import math

import bpy
import bmesh
from mathutils import Vector, Matrix

FT = 0.3048
IN = FT / 12.0


def log(*a):
    print("[build]", *a, flush=True)


def m(v):
    return v * FT


def get_collection(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def link(ob, collection=None):
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def _mesh_from_pydata(name, verts, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


_BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
# face order: 0 bottom, 1 top, 2 -Y, 3 +X, 4 +Y, 5 -X


def box_ft(name, x0, y0, x1, y1, z0, z1, mat=None, collection=None, props=None):
    """Axis-aligned box from feet bounds, origin at the center. Returns the object."""
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    if z1 < z0:
        z0, z1 = z1, z0
    sx, sy, sz = m(x1 - x0), m(y1 - y0), m(z1 - z0)
    cx, cy, cz = m((x0 + x1) / 2), m((y0 + y1) / 2), m((z0 + z1) / 2)
    verts = [(-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
             (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5)]
    verts = [(vx * sx, vy * sy, vz * sz) for vx, vy, vz in verts]
    mesh = _mesh_from_pydata(name, verts, _BOX_FACES)
    ob = bpy.data.objects.new(name, mesh)
    ob.location = (cx, cy, cz)
    link(ob, collection)
    if mat is not None:
        ob.data.materials.append(mat)
    ob["bounds_ft"] = [x0, y0, x1, y1, z0, z1]
    if props:
        for k, v in props.items():
            ob[k] = v
    return ob


def box_local(name, origin_ft, size_ft, rot_z_deg=0.0, mat=None, collection=None, rot_x_deg=0.0, rot_y_deg=0.0):
    """Box from local (0,0,0) to size, placed at origin, rotated about Z (then X, Y) around the origin."""
    sx, sy, sz = [m(v) for v in size_ft]
    verts = [(0, 0, 0), (sx, 0, 0), (sx, sy, 0), (0, sy, 0), (0, 0, sz), (sx, 0, sz), (sx, sy, sz), (0, sy, sz)]
    mesh = _mesh_from_pydata(name, verts, _BOX_FACES)
    ob = bpy.data.objects.new(name, mesh)
    ob.location = tuple(m(v) for v in origin_ft)
    ob.rotation_euler = (math.radians(rot_x_deg), math.radians(rot_y_deg), math.radians(rot_z_deg))
    link(ob, collection)
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def box_centered(name, center_ft, size_ft, rot_z_deg=0.0, mat=None, collection=None):
    """Box centered at center (bottom at center z), rotated about Z."""
    sx, sy, sz = size_ft
    ob = box_local(name, (0, 0, 0), size_ft, 0.0, mat, collection)
    # shift mesh so the local origin is bottom-center
    ob.data.transform(Matrix.Translation((-m(sx) / 2, -m(sy) / 2, 0)))
    ob.location = tuple(m(v) for v in center_ft)
    ob.rotation_euler = (0, 0, math.radians(rot_z_deg))
    return ob


def beam_between(name, p0_ft, p1_ft, w_ft, h_ft, mat=None, collection=None, up=(0, 0, 1)):
    """Rectangular bar from p0 to p1 with cross-section w (sideways) by h (along up). Origin at p0."""
    p0 = Vector([m(v) for v in p0_ft])
    p1 = Vector([m(v) for v in p1_ft])
    d = p1 - p0
    length = d.length
    if length < 1e-6:
        return None
    x = d.normalized()
    upv = Vector(up)
    if abs(x.dot(upv)) > 0.999:
        upv = Vector((0, 1, 0))
    y = upv.cross(x).normalized()
    z = x.cross(y).normalized()
    w, h = m(w_ft), m(h_ft)
    verts = []
    for ex in (0, length):
        for ey, ez in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
            verts.append(tuple(x * ex + y * ey + z * ez))
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh = _mesh_from_pydata(name, verts, faces)
    ob = bpy.data.objects.new(name, mesh)
    ob.location = p0
    link(ob, collection)
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def cylinder_ft(name, center_ft, radius_ft, height_ft, mat=None, collection=None, segments=24, axis="Z",
                cap=True):
    """Cylinder with its base at center (for Z) or centered along the axis (X/Y)."""
    bm = bmesh.new()
    r, h = m(radius_ft), m(height_ft)
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=segments, radius1=r, radius2=r, depth=h)
    if axis == "Z":
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, h / 2))
    elif axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = len(p.vertices) == 4
    ob = bpy.data.objects.new(name, mesh)
    ob.location = tuple(m(v) for v in center_ft)
    link(ob, collection)
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def sphere_ft(name, center_ft, radius_ft, mat=None, collection=None, segments=24, rings=12):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=m(radius_ft))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, mesh)
    ob.location = tuple(m(v) for v in center_ft)
    link(ob, collection)
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def plane_ft(name, x0, y0, x1, y1, z, mat=None, collection=None, flip=False):
    verts = [(m(x0), m(y0), m(z)), (m(x1), m(y0), m(z)), (m(x1), m(y1), m(z)), (m(x0), m(y1), m(z))]
    faces = [(0, 3, 2, 1)] if flip else [(0, 1, 2, 3)]
    mesh = _mesh_from_pydata(name, verts, faces)
    ob = bpy.data.objects.new(name, mesh)
    link(ob, collection)
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def prism_yz(name, profile_yz_ft, x0_ft, x1_ft, mat=None, collection=None):
    """Extrude a closed 2D profile (list of (y,z) in feet) along X from x0 to x1."""
    n = len(profile_yz_ft)
    verts = []
    for x in (x0_ft, x1_ft):
        for (y, z) in profile_yz_ft:
            verts.append((m(x), m(y), m(z)))
    faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    mesh = _mesh_from_pydata(name, verts, faces)
    ob = bpy.data.objects.new(name, mesh)
    link(ob, collection)
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def prism_xz(name, profile_xz_ft, y0_ft, y1_ft, mat=None, collection=None):
    n = len(profile_xz_ft)
    verts = []
    for y in (y0_ft, y1_ft):
        for (x, z) in profile_xz_ft:
            verts.append((m(x), m(y), m(z)))
    faces = [tuple(range(n)), tuple(range(n, 2 * n))[::-1]]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, n + i, n + j, j))
    mesh = _mesh_from_pydata(name, verts, faces)
    ob = bpy.data.objects.new(name, mesh)
    link(ob, collection)
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def set_face_material(ob, face_index, mat):
    """Give one face of a box a different material (e.g. cedar soffit under a roof)."""
    if mat.name not in [s.material.name for s in ob.material_slots if s.material]:
        ob.data.materials.append(mat)
    idx = [s.material for s in ob.material_slots].index(mat)
    ob.data.polygons[face_index].material_index = idx


def bounds_of(ob):
    return list(ob["bounds_ft"])


def overlap(a, b, eps=1e-4):
    """True if two feet-bounds boxes overlap with positive volume."""
    return (min(a[2], b[2]) - max(a[0], b[0]) > eps and
            min(a[3], b[3]) - max(a[1], b[1]) > eps and
            min(a[5], b[5]) - max(a[4], b[4]) > eps)


def boolean_cut(target, cutter, solver="EXACT"):
    mod = target.modifiers.new("cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = solver
    mod.object = cutter
    bpy.context.view_layer.objects.active = target
    for o in bpy.context.selected_objects:
        o.select_set(False)
    target.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    target.select_set(False)


def cut_with_box(targets, bounds_ft, name="cutter"):
    """Boolean-subtract a temporary box from each target, then delete it."""
    cutter = box_ft(name, *bounds_ft)
    for t in targets:
        boolean_cut(t, cutter)
    bpy.data.objects.remove(cutter, do_unlink=True)


def kelvin_rgb(k):
    """Rough blackbody to linear RGB. Good enough for 2700K to 6500K lamps."""
    t = k / 100.0
    if t <= 66:
        r = 255
        g = 99.4708025861 * math.log(t) - 161.1195681661
        b = 0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592)
        g = 288.1221695283 * ((t - 60) ** -0.0755148492)
        b = 255
    c = [max(0, min(255, v)) / 255.0 for v in (r, g, b)]
    return tuple(v ** 2.2 for v in c)


# camera white balance: light colours are divided by the colour of a WHITE_BALANCE_K blackbody, so a lamp at
# that temperature renders neutral, warmer lamps stay warm and daylight goes slightly cool, as in a photograph
# balanced for the room lights. set_white_balance() is called by the lighting setup from plan["lighting"].
WB = (1.0, 1.0, 1.0)


def set_white_balance(kelvin):
    global WB
    if not kelvin:
        WB = (1.0, 1.0, 1.0)
        return WB
    w = kelvin_rgb(kelvin)
    WB = (w[1] / w[0], 1.0, w[1] / w[2])
    return WB


def light_rgb(kelvin):
    c = kelvin_rgb(kelvin)
    return (c[0] * WB[0], c[1] * WB[1], c[2] * WB[2])


def point_light(name, pos_ft, watts, kelvin=2700, radius_ft=0.15, collection=None):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = watts
    ld.color = light_rgb(kelvin)
    ld.shadow_soft_size = m(radius_ft)
    ob = bpy.data.objects.new(name, ld)
    ob.location = tuple(m(v) for v in pos_ft)
    link(ob, collection)
    return ob


def area_light(name, pos_ft, size_ft, watts, kelvin=2700, collection=None, rot=(0, 0, 0), shape="SQUARE",
               size_y_ft=None, portal=False):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = shape
    ld.size = m(size_ft)
    if size_y_ft is not None:
        ld.size_y = m(size_y_ft)
    ld.energy = watts
    ld.color = light_rgb(kelvin)
    if portal:
        ld.cycles.is_portal = True
    ob = bpy.data.objects.new(name, ld)
    ob.location = tuple(m(v) for v in pos_ft)
    ob.rotation_euler = rot
    link(ob, collection)
    return ob


def spot_light(name, pos_ft, aim_ft, watts, kelvin=2700, angle_deg=50, blend=0.5, collection=None):
    ld = bpy.data.lights.new(name, "SPOT")
    ld.energy = watts
    ld.color = light_rgb(kelvin)
    ld.spot_size = math.radians(angle_deg)
    ld.spot_blend = blend
    ld.shadow_soft_size = m(0.1)
    ob = bpy.data.objects.new(name, ld)
    p = Vector([m(v) for v in pos_ft])
    a = Vector([m(v) for v in aim_ft])
    ob.location = p
    ob.rotation_euler = (a - p).to_track_quat("-Z", "Y").to_euler()
    link(ob, collection)
    return ob


def join_objects(objs, name):
    """Join a list of mesh objects into one (keeps materials). Returns the joined object."""
    objs = [o for o in objs if o.type == "MESH"]
    if not objs:
        return None
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.select_set(False)
    return ob


def world_bounds(ob):
    """World-space bounds of an object as (min Vector, max Vector), in meters."""
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx
