"""Architectural detail a real house has and a model usually forgets.

From plan.json alone: a rocker light switch 48 in high on the latch side of every door, in every room the door
serves; duplex outlets 15 in high about every 10 ft of usable wall; a linear slot diffuser in the ceiling of
every room over 60 sq ft, a return grille in each hall; a smoke detector on every floor and in every bedroom;
a thermostat per floor in a hall. Everything sits on the finished wall face (exterior walls are 1 ft inward
from the room line, partitions 3 in) and clear of openings.

Called once from build_scene after staging: archdetail.build(plan, mat, col) -> objects.
"""
import math

from geom import box_ft, cylinder_ft

EXT_T = 1.0            # exterior wall thickness inside the room line
PART_T = 0.25          # partition half thickness

NO_OUTLETS = {"gear_closet", "coat_closet", "panel_closet", "litter_closet", "closet_a", "closet_b", "linen",
              "rack_closet", "elevator_closet", "elevator_closet2", "stair_hall", "bstair_hall", "stair_well",
              "sauna", "kitchen", "pantry", "wc", "mechanical", "battery", "storage", "up_laundry", "laundry"}
NO_DIFFUSER = NO_OUTLETS | {"powder", "vestibule", "mudroom", "suite_hall", "hall_south", "landing", "work_corridor"}
HALLS = {"entry_hall", "spine", "hall", "hall_south", "landing", "bhall", "work_corridor", "suite_hall"}
BEDROOMS = {"primary_bedroom", "bedroom_a", "bedroom_b"}


def _envelope(rooms, floor):
    xs = [v for r in rooms if r["floor"] == floor for p in r["parts"] for v in (p[0], p[2])]
    ys = [v for r in rooms if r["floor"] == floor for p in r["parts"] for v in (p[1], p[3])]
    return min(xs), min(ys), max(xs), max(ys)


def _faces(room, env):
    """Finished wall faces of a room as (axis, at, face_dir, u0, u1): axis 'x' means the wall runs along X at
    Y=at; face_dir +1/-1 is the direction into the room. Interior part-to-part boundaries are skipped."""
    faces = []
    parts = room["parts"]
    ex0, ey0, ex1, ey1 = env
    for p in parts:
        x0, y0, x1, y1 = p[:4]
        for (axis, at, fd, u0, u1, ext) in (("x", y0, 1, x0, x1, abs(y0 - ey0) < 1e-6),
                                            ("x", y1, -1, x0, x1, abs(y1 - ey1) < 1e-6),
                                            ("y", x0, 1, y0, y1, abs(x0 - ex0) < 1e-6),
                                            ("y", x1, -1, y0, y1, abs(x1 - ex1) < 1e-6)):
            # skip edges shared with another part of the same room
            shared = False
            for q in parts:
                if q is p:
                    continue
                qx0, qy0, qx1, qy1 = q[:4]
                if axis == "x" and (abs(qy0 - at) < 1e-6 or abs(qy1 - at) < 1e-6) and qx0 < u1 and qx1 > u0:
                    shared = True
                if axis == "y" and (abs(qx0 - at) < 1e-6 or abs(qx1 - at) < 1e-6) and qy0 < u1 and qy1 > u0:
                    shared = True
            if shared:
                continue
            t = EXT_T if ext else PART_T
            # the usable run is inset by the perpendicular walls' thickness
            faces.append((axis, at + fd * t, fd, u0 + PART_T, u1 - PART_T))
    return faces


def _openings_on(plan, floor, axis, at):
    out = []
    for op in plan["openings"]:
        if op["floor"] != floor or op["axis"] != axis:
            continue
        if abs(op["at"] - at) > 1.05:
            continue
        out.append(op)
    return out


def _clear(u, ops, margin, z0=0.0, z1=1.6):
    """True when nothing in ops (door, window, cased opening) spans u +/- margin at heights z0..z1."""
    for op in ops:
        if op["kind"] in ("hatch",):
            continue
        a, b = op["c"] - op["w"] / 2 - margin, op["c"] + op["w"] / 2 + margin
        oz0, oz1 = op.get("z0", 0.0), op.get("z0", 0.0) + op["h"]
        if a <= u <= b and oz0 < z1 and oz1 > z0:
            return False
    return True


def _in_avoid(floor, axis, at, u, avoid, margin=1.0):
    """True when the point (axis, at, u) on this floor lies within margin of a wet-area box (floor, x0, y0, x1, y1)."""
    x, y = (at, u) if axis == "y" else (u, at)
    for (fl, x0, y0, x1, y1) in avoid:
        if fl == floor and x0 - margin <= x <= x1 + margin and y0 - margin <= y <= y1 + margin:
            return True
    return False


def _plate(uid, axis, at, fd, u, z, w, h, mat_plate, mat_inset, col, inset_w, inset_h, name):
    """A cover plate on a wall face: plate w x h, 0.03 ft proud, with an inset detail."""
    d0, d1 = (at, at + fd * 0.03)
    lo, hi = min(d0, d1), max(d0, d1)
    objs = []
    if axis == "x":
        objs.append(box_ft(uid(name), u - w / 2, lo, u + w / 2, hi, z - h / 2, z + h / 2, mat_plate, col))
        i0, i1 = (hi, hi + fd * 0.004) if fd > 0 else (lo + fd * 0.004, lo)
        objs.append(box_ft(uid(name + "_in"), u - inset_w / 2, min(i0, i1), u + inset_w / 2, max(i0, i1), z - inset_h / 2, z + inset_h / 2, mat_inset, col))
    else:
        objs.append(box_ft(uid(name), lo, u - w / 2, hi, u + w / 2, z - h / 2, z + h / 2, mat_plate, col))
        i0, i1 = (hi, hi + fd * 0.004) if fd > 0 else (lo + fd * 0.004, lo)
        objs.append(box_ft(uid(name + "_in"), min(i0, i1), u - inset_w / 2, max(i0, i1), u + inset_w / 2, z - inset_h / 2, z + inset_h / 2, mat_inset, col))
    return objs


def build(plan, mat, col, uid, avoid=()):
    """mat(name) -> material; uid(base) -> unique object name."""
    plate = mat("ceramic_white")
    dark = mat("steel_black")
    grille = mat("plaster_warm")
    rooms = plan["rooms"]
    floors = plan["floors"]
    objs = []
    counts = {"switch": 0, "outlet": 0, "diffuser": 0, "return": 0, "smoke": 0, "thermostat": 0}
    envs = {f: _envelope(rooms, f) for f in floors}
    # --- switches: one per door per room served, latch side, 48 in
    for op in plan["openings"]:
        if op["kind"] not in ("door", "pocket", "glassdoor", "cased"):
            continue
        floor = op["floor"]
        fz = floors[floor]["z"]
        for r in rooms:
            if r["floor"] != floor:
                continue
            for p in r["parts"]:
                x0, y0, x1, y1 = p[:4]
                if op["axis"] == "x" and x0 - 1e-6 <= op["c"] <= x1 + 1e-6 and (abs(y0 - op["at"]) < 1e-6 or abs(y1 - op["at"]) < 1e-6):
                    fd = 1 if abs(y0 - op["at"]) < 1e-6 else -1
                    ext = abs(op["at"] - envs[floor][1]) < 1e-6 or abs(op["at"] - envs[floor][3]) < 1e-6
                    face_at = op["at"] + fd * (EXT_T if ext else PART_T)
                    u = op["c"] + op["w"] / 2 + 0.5
                    if u > x1 - 0.4:
                        u = op["c"] - op["w"] / 2 - 0.5
                    if u < x0 + 0.4:
                        break
                    objs += _plate(uid, "x", face_at, fd, u, fz + 4.0, 0.23, 0.38, plate, mat("plaster_warm"), col, 0.11, 0.22, "switch")
                    counts["switch"] += 1
                    break
                if op["axis"] == "y" and y0 - 1e-6 <= op["c"] <= y1 + 1e-6 and (abs(x0 - op["at"]) < 1e-6 or abs(x1 - op["at"]) < 1e-6):
                    fd = 1 if abs(x0 - op["at"]) < 1e-6 else -1
                    ext = abs(op["at"] - envs[floor][0]) < 1e-6 or abs(op["at"] - envs[floor][2]) < 1e-6
                    face_at = op["at"] + fd * (EXT_T if ext else PART_T)
                    u = op["c"] + op["w"] / 2 + 0.5
                    if u > y1 - 0.4:
                        u = op["c"] - op["w"] / 2 - 0.5
                    if u < y0 + 0.4:
                        break
                    objs += _plate(uid, "y", face_at, fd, u, fz + 4.0, 0.23, 0.38, plate, mat("plaster_warm"), col, 0.11, 0.22, "switch")
                    counts["switch"] += 1
                    break
    # --- outlets, diffusers, smoke detectors, thermostats per room
    for r in rooms:
        floor = r["floor"]
        fz = floors[floor]["z"]
        ch = floors[floor]["h"]
        name = r["name"]
        area = sum((p[2] - p[0]) * (p[3] - p[1]) for p in r["parts"])
        if name not in NO_OUTLETS:
            for (axis, at, fd, u0, u1) in _faces(r, envs[floor]):
                ops = _openings_on(plan, floor, axis, at)
                run = u1 - u0
                if run < 3.0:
                    continue
                n = max(1, int(round(run / 10.0)))
                for k in range(n):
                    u = u0 + run * (k + 0.5) / n
                    if not _clear(u, ops, 0.6, fz - 0.1 - fz, 1.6):
                        u = u0 + 1.5 if k == 0 else u1 - 1.5
                        if not _clear(u, ops, 0.6, 0.0, 1.6):
                            continue
                    if _in_avoid(floor, axis, at, u, avoid):
                        continue
                    objs += _plate(uid, axis, at, fd, u, fz + 1.25, 0.23, 0.38, plate, mat("plaster_warm"), col, 0.09, 0.26, "outlet")
                    counts["outlet"] += 1
        if name not in NO_DIFFUSER and area >= 60:
            # linear slot diffuser along the long axis, 1 ft off the widest exterior-ish wall, 3 ft long
            p = max(r["parts"], key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
            x0, y0, x1, y1 = p[:4]
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            zc = fz + ch
            if (x1 - x0) >= (y1 - y0):
                objs.append(box_ft(uid("diffuser"), cx - 1.5, y1 - PART_T - 1.2, cx + 1.5, y1 - PART_T - 0.95, zc - 0.02, zc, plate, col))
                objs.append(box_ft(uid("diffuser_slot"), cx - 1.45, y1 - PART_T - 1.13, cx + 1.45, y1 - PART_T - 1.02, zc - 0.021, zc - 0.005, dark, col))
            else:
                objs.append(box_ft(uid("diffuser"), x1 - PART_T - 1.2, cy - 1.5, x1 - PART_T - 0.95, cy + 1.5, zc - 0.02, zc, plate, col))
                objs.append(box_ft(uid("diffuser_slot"), x1 - PART_T - 1.13, cy - 1.45, x1 - PART_T - 1.02, cy + 1.45, zc - 0.021, zc - 0.005, dark, col))
            counts["diffuser"] += 1
        if any(k in name for k in ("bath", "wc", "powder", "laundry", "shower")) and area >= 12:
            # ceiling exhaust grille, 10 in square with slots, near the room centre but off any downlight line
            p = max(r["parts"], key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
            x0, y0, x1, y1 = p[:4]
            cx, cy = (x0 + x1) / 2 + 0.8, (y0 + y1) / 2 - 0.6
            zc = fz + ch
            objs.append(box_ft(uid("exhaust"), cx - 0.42, cy - 0.42, cx + 0.42, cy + 0.42, zc - 0.02, zc, plate, col))
            for i in range(6):
                yy = cy - 0.3 + i * 0.12
                objs.append(box_ft(uid("exhaust_slot"), cx - 0.32, yy - 0.02, cx + 0.32, yy + 0.02, zc - 0.03, zc - 0.02, dark, col))
            counts["exhaust"] = counts.get("exhaust", 0) + 1
        if name in HALLS and area >= 40:
            p = max(r["parts"], key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
            x0, y0, x1, y1 = p[:4]
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            zc = fz + ch
            objs.append(box_ft(uid("return_grille"), cx - 0.9, cy - 0.6, cx + 0.9, cy + 0.6, zc - 0.02, zc, plate, col))
            for i in range(9):
                yy = cy - 0.5 + i * 0.125
                objs.append(box_ft(uid("return_fin"), cx - 0.8, yy - 0.02, cx + 0.8, yy + 0.02, zc - 0.03, zc - 0.02, dark, col))
            counts["return"] += 1
        if name in BEDROOMS or (name in HALLS and area >= 60):
            p = max(r["parts"], key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
            x0, y0, x1, y1 = p[:4]
            cx, cy = (x0 + x1) / 2 + 1.5, (y0 + y1) / 2 - 1.0
            zc = fz + ch
            objs.append(cylinder_ft(uid("smoke"), (cx, cy, zc - 0.06), 0.24, 0.12, plate, col, 24))
            objs.append(cylinder_ft(uid("smoke_ring"), (cx, cy, zc - 0.13), 0.16, 0.02, dark, col, 24))
            counts["smoke"] += 1
    # --- one thermostat per floor: on a hall wall at 5 ft
    for floor in floors:
        if floor == "garage":
            continue
        fz = floors[floor]["z"]
        for r in rooms:
            if r["floor"] != floor or r["name"] not in ("spine", "hall", "bhall"):
                continue
            for (axis, at, fd, u0, u1) in _faces(r, envs[floor]):
                if u1 - u0 < 6:
                    continue
                ops = _openings_on(plan, floor, axis, at)
                u = (u0 + u1) / 2 + 2.0
                if not _clear(u, ops, 0.8, 3.0, 6.0):
                    continue
                lo, hi = min(at, at + fd * 0.08), max(at, at + fd * 0.08)
                if axis == "x":
                    objs.append(box_ft(uid("thermostat"), u - 0.17, lo, u + 0.17, hi, fz + 4.9, fz + 5.24, plate, col))
                    i0, i1 = (hi, hi + fd * 0.003) if fd > 0 else (lo + fd * 0.003, lo)
                    objs.append(box_ft(uid("thermostat_lcd"), u - 0.1, min(i0, i1), u + 0.1, max(i0, i1), fz + 5.0, fz + 5.14, dark, col))
                else:
                    objs.append(box_ft(uid("thermostat"), lo, u - 0.17, hi, u + 0.17, fz + 4.9, fz + 5.24, plate, col))
                    i0, i1 = (hi, hi + fd * 0.003) if fd > 0 else (lo + fd * 0.003, lo)
                    objs.append(box_ft(uid("thermostat_lcd"), min(i0, i1), u - 0.1, max(i0, i1), u + 0.1, fz + 5.0, fz + 5.14, dark, col))
                counts["thermostat"] += 1
                break
            else:
                continue
            break
    return objs, counts
