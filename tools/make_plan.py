#!/usr/bin/env python3
"""Write plan.json from the master build specification (housemasterspec.md), room by room.

The spec is the source of truth; this file is its transcription into the program the builder reads.
Every number here is copied from the spec section named in the comment. Anything interpreted rather
than copied is flagged with "ASK:" and collected into plan["questions"] for Henry.

    python3 tools/make_plan.py            # writes plan.json
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Q = []  # questions for Henry: spec ambiguities, with coordinates


def ask(msg):
    Q.append(msg)


# ----------------------------------------------------------------------------- floors  (spec 0.1)
floors = {
    "basement": {"z": -10.0, "h": 9.5},
    "main":     {"z": 0.0,   "h": 9.5},
    "second":   {"z": 10.0,  "h": 9.0},
    "garage":   {"z": -0.4,  "h": 12.0},
}

# ----------------------------------------------------------------------------- rooms
# Each room: name, floor, parts (list of rects, wall centerlines), finishes, light (fill watts), flags.
# Flags: void (no floor slab), no_ceiling, exterior_faces (override), label.
rooms = []


def room(name, floor, parts, floorm, wall, ceil, light=60, **kw):
    if isinstance(parts[0], (int, float)):
        parts = [parts]
    r = {"name": name, "floor": floor, "parts": parts, "floorm": floorm, "wall": wall, "ceil": ceil, "light": light}
    r.update(kw)
    rooms.append(r)
    return r


# --- main floor (spec 3, table)
room("gear_closet", "main", [0, 0, 8, 6], "terrazzo", "plaster_warm", "plaster_warm", 30, label="gear closet")
room("vestibule", "main", [8, 0, 14, 6], "terrazzo", "walnut_panel", "plaster_warm", 50)
room("powder", "main", [14, 0, 18, 6], "terrazzo", "wallpaper_botanical_dark", "oxblood", 30)
room("coat_closet", "main", [18, 0, 22, 6], "oak_floor", "plaster_warm", "plaster_warm", 20, label="coat closet")
room("panel_closet", "main", [0, 6, 8, 13], "concrete_sealed", "plaster_warm", "plaster_warm", 20, label="panel closet")
room("entry_hall", "main", [8, 6, 22, 13], "oak_floor", "plaster_warm", "plaster_warm", 80, label="entry hall")
room("spine", "main", [22, 0, 28, 32], "oak_floor", "oxblood", "oxblood", 90, label="gallery spine")
room("stair_hall", "main", [28, 0, 34, 13], "oak_floor", "plaster_warm", "plaster_warm", 60, no_ceiling=True, label="stair hall")
room("laundry", "main", [[34, 0, 42, 6], [37, 6, 42, 9], [34, 9, 42, 13]], "terrazzo", "plaster_warm", "plaster_warm", 70)
room("elevator_closet", "main", [34, 6, 37, 9], "concrete_sealed", "plaster_warm", "plaster_warm", 10, label="elevator")
room("mudroom", "main", [[3, 13, 8, 16], [0, 16, 8, 21]], "terrazzo", "plaster_warm", "plaster_warm", 70)
room("litter_closet", "main", [0, 13, 3, 16], "terrazzo", "plaster_warm", "plaster_warm", 10, label="litter")
room("pantry", "main", [0, 21, 8, 27], "terrazzo", "plaster_warm", "plaster_warm", 50)
room("kitchen", "main", [[8, 13, 22, 30], [0, 27, 8, 30]], "oak_floor", "plaster_warm", "plaster_warm", 160)
room("living", "main", [0, 30, 22, 46], "oak_floor", "plaster_warm", "oak_decking", 150, label="living room")
room("away", "main", [22, 32, 28, 46], "oak_floor", "wallpaper_geo_olive", "olive_paint", 60, label="away room")
room("primary_bath", "main", [[28, 13, 39, 22], [39, 16.5, 42, 22]], "terrazzo", "plaster_warm", "plaster_warm", 90, label="primary bath")
room("wc", "main", [39, 13, 42, 16.5], "terrazzo", "plaster_warm", "plaster_warm", 20, label="wc")
room("suite_hall", "main", [28, 22, 31, 30], "oak_floor", "oxblood", "plaster_warm", 30, label="suite hall")
room("primary_closet", "main", [31, 22, 42, 30], "wool_carpet", "walnut", "plaster_warm", 80, label="primary closet")
room("primary_bedroom", "main", [28, 30, 42, 46], "wool_carpet", "plaster_warm", "plaster_warm", 90, label="primary bedroom")

# --- second floor (spec 4, table). The well over the stair hall is a void with walls two stories high.
room("her_office", "second", [0, 6, 11, 26], "wool_carpet_charcoal", "plaster_warm", "plaster_warm", 100, label="her office")
room("lab", "second", [[11, 6, 22, 16], [14, 16, 22, 22], [22, 6, 28, 13]], "cork", "plaster_warm", "plaster_warm", 120)
room("rack_closet", "second", [11, 16, 14, 22], "concrete_sealed", "plaster_warm", "plaster_warm", 15, label="rack")
room("work_corridor", "second", [11, 22, 22, 26], "oak_floor", "oxblood", "plaster_warm", 30, label="work corridor")
room("stair_well", "second", [28, 0, 34, 13], "oak_floor", "plaster_warm", "plaster_warm", 40, void=True, label="stair well (open)")
room("landing", "second", [22, 13, 42, 19], "oak_floor", "oxblood", "plaster_warm", 80)
room("elevator_closet2", "second", [34, 6, 37, 9], "concrete_sealed", "plaster_warm", "plaster_warm", 10, label="elevator")
room("up_laundry", "second", [[34, 9, 42, 13], [37, 6, 42, 9]], "terrazzo", "plaster_warm", "plaster_warm", 30, label="laundry closet")
room("hall_south", "second", [22, 19, 28, 26], "oak_floor", "oxblood", "plaster_warm", 40, label="hall")
room("hall", "second", [22, 26, 28, 46], "oak_floor", "oxblood", "plaster_warm", 80, label="hall (kid zone)")
room("kid_bath_sink", "second", [28, 19, 35, 28], "terrazzo", "tile_white", "plaster_warm", 60, label="kid bath")
room("kid_bath_tub", "second", [35, 19, 42, 28], "terrazzo", "tile_white", "plaster_warm", 50, label="tub room")
room("bedroom_b", "second", [[31, 28, 42, 37], [28, 37, 42, 46]], "wool_carpet", "plaster_warm", "plaster_warm", 80, label="bedroom B")
room("closet_b", "second", [28, 28, 31, 33], "wool_carpet", "plaster_warm", "plaster_warm", 10, label="closet")
room("linen", "second", [28, 33, 31, 37], "oak_floor", "plaster_warm", "plaster_warm", 10, label="linen")
room("bedroom_a", "second", [[0, 26, 11, 31], [0, 31, 14, 40]], "wool_carpet", "plaster_warm", "plaster_warm", 80, label="bedroom A")
room("closet_a", "second", [11, 26, 14, 31], "wool_carpet", "plaster_warm", "plaster_warm", 10, label="closet")
room("hedge_alcove", "second", [0, 40, 14, 46], "wool_carpet", "plaster_warm", "plaster_warm", 50, label="hedge alcove")
room("loft", "second", [14, 26, 22, 46], "oak_floor", "plaster_warm", "plaster_warm", 90)

# --- basement (spec 5, table)
room("gym", "basement", [0, 0, 22, 20], "rubber_floor", "plaster_warm", "plaster_warm", 260)
room("sauna", "basement", [0, 20, 8, 28], "cedar_sauna", "cedar_sauna", "cedar_sauna", 25)
room("recovery", "basement", [8, 20, 22, 28], "terrazzo", "plaster_warm", "plaster_warm", 90, label="recovery suite")
room("lounge", "basement", [0, 28, 22, 46], "wool_carpet_charcoal", "oxblood", "ceiling_dark", 90)
room("bar", "basement", [22, 34, 28, 46], "terrazzo", "wallpaper_botanical_dark", "ceiling_dark", 60)
room("bhall", "basement", [22, 0, 28, 34], "oak_floor", "oxblood", "oxblood", 60, label="basement hall")
room("bstair_hall", "basement", [28, 0, 34, 13], "oak_floor", "plaster_warm", "plaster_warm", 40, label="stair hall")
room("battery", "basement", [34, 0, 42, 13], "concrete_sealed", "concrete_sealed", "concrete_sealed", 60, label="battery room")
room("mechanical", "basement", [28, 13, 42, 34], "concrete_sealed", "concrete_sealed", "concrete_sealed", 120)
room("storage", "basement", [28, 34, 42, 46], "concrete_sealed", "plaster_warm", "plaster_warm", 60, label="storage / projects")

# --- garage (spec 7): one open volume, brick to Z 8 then cedar (handled by the exterior pass)
room("garage", "garage", [-6, 64, 18, 94], "concrete_sealed", "plaster_warm", "plaster_warm", 200, exterior_wall=1.0)

# ----------------------------------------------------------------------------- openings
# axis x: wall runs along X at Y=at; axis y: wall runs along Y at X=at. c = center along the wall.
openings = []


def op(note, floor, axis, at, c, w, z0, h, kind, **kw):
    o = {"note": note, "floor": floor, "axis": axis, "at": at, "c": c, "w": w, "z0": z0, "h": h, "kind": kind}
    o.update(kw)
    openings.append(o)
    return o


# exterior schedule (spec 2.5)
op("S1 front door", "main", "x", 0, 11, 4, 0, 8.0, "door", exterior=True, swing="in", open_deg=0, leaf="walnut_slab")
op("S2 sidelight", "main", "x", 0, 13.5, 1, 0, 8.0, "window")
op("S3 powder slot", "main", "x", 0, 16, 2, 6.0, 1.5, "window", obscure=True)
op("S4 spine bench window", "main", "x", 0, 25, 5, 0, 8.5, "window", portal=True)
op("S5 stair hall clerestory", "main", "x", 0, 31, 4, 7.0, 2.0, "window")
op("S6 laundry window", "main", "x", 0, 38.5, 5, 5.0, 2.5, "window", obscure=True)
op("W1 mudroom side door", "main", "y", 0, 17.75, 3, 0, 7.0, "door", exterior=True, swing="in", open_deg=0, leaf="half_glass")
ask("2.5 W1 mudroom side door Y 15.5-18.5 overlaps the litter closet (X 0-3, Y 13-16) by 6 in on the west wall. "
    "Moved the door 9 in north to Y 16.25-19.25. OK, or should the litter closet shrink to Y 13-15.5?")
op("N1 living lift-and-slide", "main", "x", 46, 11, 16, 0, 8.5, "glasswall", panels=4, portal=True, door_panel=None)
op("N2 away window", "main", "x", 46, 25, 4, 2.5, 5.0, "window")
op("N3 bedroom window", "main", "x", 46, 36, 8, 2.0, 6.0, "window", portal=True, mullions=[2, 6])
op("E1 laundry high window", "main", "y", 42, 4, 4, 6.0, 2.0, "window")
op("E2 bath window", "main", "y", 42, 18, 3, 5.0, 2.0, "window", obscure=True)
ask("2.5 E2 bath window Y 15-18 straddles the WC compartment wall at Y 16.5 (WC is X 39-42, Y 13-16.5). "
    "Moved the window to Y 16.5-19.5 so it lands over the shower. OK?")
op("E3 closet window", "main", "y", 42, 26, 4, 5.0, 2.5, "window", obscure=True)
op("E4 bedroom window", "main", "y", 42, 39, 6, 2.5, 5.0, "window", portal=True)
op("E5 cat tunnel", "main", "y", 42, 38.25, 1.5, 0.2, 1.5, "hatch")
op("S7 her office window", "second", "x", 6, 5.5, 7, 2.5, 5.0, "window")
op("S8 lab window run", "second", "x", 6, 20, 14, 2.5, 5.0, "window", portal=True, panels=4)
op("S9 landing clerestory", "second", "x", 0, 31, 4, 6.5, 2.0, "window")
op("W3 her office", "second", "y", 0, 12, 6, 2.5, 5.0, "window")
op("W4 her office", "second", "y", 0, 21, 6, 2.5, 5.0, "window")
op("W5 bedroom A", "second", "y", 0, 32, 6, 2.5, 5.0, "window")
op("W6 hedge alcove", "second", "y", 0, 43, 4, 2.5, 4.0, "window")
op("N4 hedge alcove", "second", "x", 46, 5, 6, 2.5, 4.0, "window")
op("N5 loft window seat", "second", "x", 46, 18, 6, 1.5, 6.0, "window")
op("N6 hall window", "second", "x", 46, 25, 4, 2.5, 5.0, "window")
op("N7 bedroom B", "second", "x", 46, 37, 6, 2.5, 5.0, "window")
op("E6 landing window", "second", "y", 42, 16, 4, 3.0, 4.0, "window")
op("E7 kid bath tub", "second", "y", 42, 23, 4, 4.0, 2.5, "window", obscure=True)
op("E8 bedroom B", "second", "y", 42, 36, 6, 2.5, 5.0, "window")
op("B1 gym well", "basement", "y", 0, 6, 4, 6.5, 3.0, "window", well=True)
op("B2 lounge well", "basement", "y", 0, 38, 4, 6.5, 3.0, "window", well=True)
op("B3 lounge well", "basement", "x", 46, 18, 4, 6.5, 3.0, "window", well=True)
op("B4 storage well", "basement", "x", 46, 34, 4, 6.5, 2.5, "window", well=True)

# main floor interior doors and openings (spec 3.x)
op("gear closet door", "main", "y", 8, 3, 3, 0, 7, "door", open_deg=0)
op("vestibule inner glass door", "main", "x", 6, 11, 4, 0, 8, "glassdoor", open_deg=90)
op("vestibule inner sidelight", "main", "x", 6, 13.5, 1, 0, 8, "window", interior=True)
op("powder door", "main", "x", 6, 16, 2.67, 0, 7, "door", open_deg=0)
op("coat closet door", "main", "x", 6, 20, 2.67, 0, 7, "door", open_deg=0)
op("panel closet door", "main", "y", 8, 9.5, 3, 0, 7, "door", open_deg=0)
op("entry hall to spine", "main", "y", 22, 9.5, 5, 0, 8.5, "cased")
op("spine to stair hall", "main", "y", 28, 7, 4, 0, 8.5, "cased")
op("spine to kitchen", "main", "y", 22, 16, 6, 0, 9.0, "cased")
op("spine to suite hall", "main", "y", 28, 28.5, 3, 0, 7, "door", open_deg=0)
op("bath to laundry", "main", "x", 13, 36.5, 3, 0, 7, "door", open_deg=0)
op("elevator closet door", "main", "y", 37, 7.5, 2.5, 0, 7, "door", open_deg=0)
op("mudroom to kitchen", "main", "y", 8, 14.5, 3, 0, 7, "door", open_deg=80)
op("litter cat door", "main", "y", 3, 14.5, 0.67, 0.2, 0.7, "hatch")
op("litter service door", "main", "x", 16, 1.5, 2, 0, 7, "door", open_deg=0)
op("pantry door", "main", "y", 8, 24, 3, 0, 7, "door", open_deg=45)
op("kitchen open to living", "main", "x", 30, 11, 22, 0, 9.5, "open", full=True)
op("living to away pocket door", "main", "y", 22, 38.5, 5, 0, 8, "pocket", open_ft=3)
op("wc door", "main", "y", 39, 14.75, 2.5, 0, 7, "door", open_deg=0, leaf="frosted")
op("closet to bath", "main", "x", 22, 36, 3, 0, 7, "door", open_deg=80)
op("suite hall to bedroom", "main", "x", 30, 29.5, 3, 0, 7, "door", open_deg=80)
op("suite hall to closet", "main", "y", 31, 26, 3, 0, 7, "door", open_deg=80)
op("closet to bedroom", "main", "x", 30, 36, 3, 0, 7, "door", open_deg=80)

# second floor (spec 4.x)
op("her office door", "second", "y", 11, 24, 3, 0, 7, "door", open_deg=0)
op("hall to work corridor", "second", "y", 22, 24, 3, 0, 7, "door", open_deg=80)
op("work corridor to lab", "second", "x", 22, 16.5, 3, 0, 7, "door", open_deg=80)
op("rack closet glass door", "second", "y", 14, 19, 2.5, 0, 7, "glassdoor", open_deg=0)
op("landing to lab", "second", "y", 22, 16, 3, 0, 7, "door", open_deg=80)
op("landing to laundry closet", "second", "x", 13, 39, 4, 0, 7, "door", open_deg=0, leaves=2)
op("chute flap", "second", "x", 13, 35, 1.5, 3.0, 1.5, "hatch")
op("elevator closet2 door", "second", "x", 9, 35.5, 2.5, 0, 7, "door", open_deg=0)
op("kid zone door", "second", "x", 26, 25, 3, 0, 7, "door", open_deg=90)
op("kid zone sidelight", "second", "x", 26, 27.25, 1.5, 0, 7, "window", interior=True)
op("hall to kid bath", "second", "y", 28, 23.5, 3, 0, 7, "door", open_deg=0)
op("sink room to tub room", "second", "y", 35, 23.5, 2.67, 0, 7, "door", open_deg=45, leaf="frosted")
op("hall to bedroom B", "second", "y", 28, 40, 3, 0, 7, "door", open_deg=80)
op("hall to linen", "second", "y", 28, 35, 2, 0, 7, "door", open_deg=0)
op("closet B door", "second", "y", 31, 30.5, 2.67, 0, 7, "door", open_deg=60)
op("loft to bedroom A", "second", "y", 14, 37, 3, 0, 7, "door", open_deg=80)
op("closet A door", "second", "y", 11, 28.5, 2.67, 0, 7, "door", open_deg=0)
op("loft to hedge alcove", "second", "y", 14, 43, 4, 0, 7, "cased")
op("loft open to hall", "second", "y", 22, 36, 20, 0, 9.0, "open", full=True)

# basement (spec 5.x)
op("bhall to bstair hall", "basement", "y", 28, 7, 4, 0, 8.5, "cased")
op("gym glass door", "basement", "y", 22, 10, 3, 0, 7, "glassdoor", open_deg=0)
ask("5.1 gym glass door at X 22, Y 10 with 'a glass sidelight from Y 8 to Y 12': the 3 ft door already spans Y 8.5-11.5, "
    "so a sidelight Y 8-12 leaves 6 in each side. I built the sidelight as a 4 ft fixed pane at Y 12-16 north of the door. Correct?")
op("gym sidelight", "basement", "y", 22, 14, 4, 0, 7, "window", interior=True)
op("hall to recovery", "basement", "y", 22, 24, 3, 0, 7, "door", open_deg=80)
op("gym to recovery glass door", "basement", "x", 20, 20.5, 3, 0, 7, "glassdoor", open_deg=0)
ask("5.2 gym-to-recovery glass door at Y 20, X 21 (3 ft) would span X 19.5-22.5, past the gym's east wall at X 22. "
    "Moved it 6 in west to X 19-22, tight to the corner. OK?")
op("sauna glass front", "basement", "y", 8, 24, 6, 0, 8, "glasswall", panels=1, door_panel=None, interior=True)
op("hall to mechanical", "basement", "y", 28, 16, 3, 0, 7, "door", open_deg=0, leaf="steel")
op("hall open to lounge", "basement", "x", 34, 25, 6, 0, 9.5, "open", full=True)
op("bar open to lounge", "basement", "y", 22, 40, 12, 0, 9.5, "open", full=True)
op("bar to storage", "basement", "y", 28, 40, 3, 0, 7, "door", open_deg=0)
op("mechanical to storage", "basement", "x", 34, 35, 3, 0, 7, "door", open_deg=0, leaf="steel")
op("mechanical to battery", "basement", "x", 13, 38.5, 3, 0, 7, "door", open_deg=0, leaf="steel")

# garage (spec 7.1)
op("garage door W", "garage", "x", 94, 0, 9, 0, 8, "garagedoor")
op("garage door E", "garage", "x", 94, 12, 9, 0, 8, "garagedoor")
op("garage pedestrian door", "garage", "x", 64, -3, 3, 0, 7, "door", exterior=True, open_deg=0, leaf="half_glass")
op("garage clerestory E", "garage", "y", 18, 79, 26, 9, 2, "window")
op("garage clerestory W", "garage", "y", -6, 79, 26, 9, 2, "window")

# ----------------------------------------------------------------------------- voids (slab cuts)  spec 3.8, 6
voids = [
    {"note": "down-stair slot through the main floor", "floor": "main", "what": "floor", "b": [31, 0.75, 34, 13.25]},
    {"note": "two-story well: no main ceiling / second floor over the stair hall", "floor": "main", "what": "ceil", "b": [28, 0, 34, 13]},
    {"note": "two-story well: no second floor slab", "floor": "second", "what": "floor", "b": [28, 0, 34, 13]},
    {"note": "down-stair passes the basement ceiling", "floor": "basement", "what": "ceil", "b": [31, 0.75, 34, 13.25]},
    {"note": "laundry chute", "floor": "main", "what": "ceil", "b": [34.25, 11.25, 35.75, 12.75]},
    {"note": "laundry chute", "floor": "second", "what": "floor", "b": [34.25, 11.25, 35.75, 12.75]},
]

# ----------------------------------------------------------------------------- stairs  spec 6
stairs = [
    {"name": "up_stair", "x0": 31, "x1": 34, "y_from": 0.75, "y_to": 13.25, "z_from": 0.0, "z_to": 10.0,
     "risers": 16, "tread_m": "oak_floor", "riser_m": "oak_floor", "stringer_m": "walnut", "rail_m": "bronze_black",
     "guard": "west", "handrail": "east"},
    {"name": "down_stair", "x0": 31, "x1": 34, "y_from": 13.25, "y_to": 0.75, "z_from": 0.0, "z_to": -10.0,
     "risers": 16, "tread_m": "oak_floor", "riser_m": "oak_floor", "stringer_m": "walnut", "rail_m": "bronze_black",
     "guard": "west", "handrail": "east"},
]
ask("6 / 3.8: the up-stair's first tread (Y 0.75, Z 0) sits directly above the down-stair's last tread (Y 0.75, Z -10) with the "
    "up-stair rising north and the down-stair descending south beneath it. That works geometrically (10 ft between runs "
    "everywhere), but the main-floor stair slot X 31-34, Y 0.75-13.25 is then open from the basement to the second floor, "
    "and the only way past the slot on the main floor is the 3 ft aisle X 28-31. Confirm that is intended.")

# ----------------------------------------------------------------------------- exterior + roofs  spec 2
exterior = {
    "wall_t": 1.0,
    "base": {"m_out": "roman_brick", "z0": -0.5, "z1": 9.5, "floors": ["main"]},
    "upper": {"m_out": "cedar_ext", "z0": 10.0, "z1": 19.0, "floors": ["second"], "reveal": {"m": "bronze_black", "z0": 9.5, "z1": 10.0}},
    "garage": {"m_out_low": "roman_brick", "m_out_high": "cedar_ext", "split_z": 8.0},
    "roofs": [
        {"name": "main gable", "type": "gable", "ridge_axis": "x", "ridge_at": 26, "x0": -4, "x1": 46, "y0": 2, "y1": 50,
         "z_wall": 19.5, "pitch": 0.25, "thick": 0.6, "fascia": 1.0, "m": "metal_roof_charcoal", "soffit_m": "cedar_ext",
         "rafter_tails": 4.0, "skylights": [[26, 16, 3, 4], [38, 16, 3, 4], [18, 40, 3, 4]]},
        {"name": "front shed", "type": "shed", "x0": 0, "x1": 42, "y0": -1.5, "y1": 6, "z_high": 10.5, "z_low": 10.0, "slope_to": "south",
         "thick": 0.5, "fascia": 1.0, "m": "metal_roof_charcoal", "soffit_m": "cedar_ext", "beams": {"axis": "y", "spacing": 4, "w_in": 6, "d_in": 12}},
        {"name": "porch canopy", "type": "shed", "x0": 4, "x1": 22, "y0": -7, "y1": -1.5, "z_high": 10.2, "z_low": 10.0, "slope_to": "south",
         "thick": 0.5, "fascia": 1.0, "m": "metal_roof_charcoal", "soffit_m": "cedar_ext",
         "posts": [[4, -6.5], [13, -6.5], [22, -6.5]], "post_size": 0.67, "post_z0": -0.5},
        {"name": "terrace canopy", "type": "flat", "x0": 4, "x1": 22, "y0": 46, "y1": 58, "z": 10.5, "thick": 0.6, "fascia": 1.0,
         "m": "metal_roof_charcoal", "soffit_m": "cedar_ext", "posts": [[4, 57.5], [22, 57.5]], "post_size": 0.67, "post_z0": -0.3,
         "beams": {"axis": "x", "spacing": 4, "w_in": 4, "d_in": 10}},
        {"name": "breezeway", "type": "flat", "x0": -6.5, "x1": 0, "y0": 15, "y1": 64, "z": 9.5, "thick": 0.5, "fascia": 0.5,
         "m": "metal_roof_charcoal", "soffit_m": "cedar_ext",
         "posts": [[-6, y] for y in range(16, 65, 8)], "post_size": 0.5, "post_z0": -0.4,
         "beams": {"axis": "x", "spacing": 8, "w_in": 4, "d_in": 10}},
        {"name": "garage gable", "type": "gable", "ridge_axis": "y", "ridge_at": 6, "x0": -9, "x1": 21, "y0": 61, "y1": 97,
         "z_wall": 12.5, "pitch": 0.25, "thick": 0.5, "fascia": 0.8, "m": "metal_roof_charcoal", "soffit_m": "cedar_ext"},
        {"name": "catio lean-to", "type": "shed", "x0": 42, "x1": 48, "y0": 37, "y1": 41, "z_high": 8.0, "z_low": 7.4, "slope_to": "east",
         "thick": 0.3, "fascia": 0.3, "m": "metal_roof_charcoal", "soffit_m": "cedar_ext"},
    ],
    "chase": {"b": [-1.5, 36, 0.5, 40, -0.5, 26], "m": "cedar_ext", "cap_m": "steel_black"},
}
ask("1.1 says the lot runs to Y 140 with the alley at Y 140; 1.9 says to model the alley as asphalt from Y 100 to Y 116 "
    "right behind the 6 ft apron. I used 1.9 (alley Y 100-116), which puts the honey locust at (30, 110) in the alley and the "
    "rear hedge at Y 100 on the alley edge. Which is right: alley at Y 100 or at Y 140?")
ask("2.2 direct-vent chase [-1.5, 36, 0.5, 40] rises to Z 26 along the west gable wall; the main gable's west rake "
    "overhang runs X -4 to 0, so the chase passes up through the roof overhang at Y 36-40. I cut the roof around it. OK?")

# ----------------------------------------------------------------------------- site  spec 1
site = {
    "grade_z": -0.5,
    "lot": [-9, -30, 51, 140],
    "ground": {"m": "lawn", "b": [-70, -60, 110, 150]},
    "slabs": [
        {"note": "sidewalk", "b": [-70, -30, 110, -25], "z": -0.6, "t": 0.4, "m": "concrete_sealed"},
        {"note": "street", "b": [-70, -60, 110, -30], "z": -0.7, "t": 0.4, "m": "asphalt"},
        {"note": "front walk", "b": [8, -25, 13, -7], "z": -0.5, "t": 0.3, "m": "bluestone"},
        {"note": "porch step 1", "b": [4, -7, 22, -6.5], "z": -0.3, "t": 0.5, "m": "bluestone"},
        {"note": "porch step 2", "b": [4, -6.5, 22, -6], "z": -0.2, "t": 0.5, "m": "bluestone"},
        {"note": "porch floor", "b": [4, -6, 22, 0], "z": -0.2, "t": 0.5, "m": "bluestone"},
        {"note": "gravel band south", "b": [-1.5, -1.5, 43.5, 0], "z": -0.5, "t": 0.15, "m": "gravel_gray"},
        {"note": "gravel band north", "b": [-1.5, 46, 43.5, 47.5], "z": -0.5, "t": 0.15, "m": "gravel_gray"},
        {"note": "gravel band west", "b": [-1.5, 0, 0, 46], "z": -0.5, "t": 0.15, "m": "gravel_gray"},
        {"note": "gravel band east", "b": [42, 0, 43.5, 46], "z": -0.5, "t": 0.15, "m": "gravel_gray"},
        {"note": "breezeway walk", "b": [-6, 15, 0, 64], "z": -0.4, "t": 0.3, "m": "bluestone"},
        {"note": "terrace", "b": [0, 46, 42, 62], "z": -0.3, "t": 0.4, "m": "bluestone"},
        {"note": "catio floor", "b": [42, 33, 48, 41], "z": -0.3, "t": 0.3, "m": "bluestone"},
        {"note": "driveway apron", "b": [-6, 94, 18, 100], "z": -0.5, "t": 0.3, "m": "concrete_sealed"},
        {"note": "alley", "b": [-70, 100, 110, 116], "z": -0.6, "t": 0.4, "m": "asphalt"},
        {"note": "lawn rectangle (edged)", "b": [18, 64, 42, 94], "z": -0.5, "t": 0.1, "m": "lawn"},
    ],
    "beds": [
        {"note": "front bed west", "b": [0, -5.5, 8, -1.5]}, {"note": "front bed east", "b": [22, -5.5, 42, -1.5]},
        {"note": "terrace north bed", "b": [0, 62, 18, 66]}, {"note": "east lot line bed", "b": [48, 0, 51, 100]},
    ],
    "hedges": [
        {"note": "east lot line hedge", "b": [48.5, 0, 50.5, 100], "h": 6},
        {"note": "rear privacy hedge", "b": [18, 100, 51, 101], "h": 7},
    ],
    "trees": [
        {"note": "red oak", "pos": [-3, -22], "trunk_d": 2.5, "canopy_r": 22, "canopy_z": 14, "autumn": True},
        {"note": "red oak", "pos": [36, -24], "trunk_d": 2.0, "canopy_r": 18, "canopy_z": 12, "autumn": True},
        {"note": "sugar maple", "pos": [48, 20], "trunk_d": 1.5, "canopy_r": 14, "canopy_z": 9, "autumn": True},
        {"note": "honey locust", "pos": [30, 110], "trunk_d": 1.2, "canopy_r": 16, "canopy_z": 10},
        {"note": "japanese maple", "pos": [9, 64], "trunk_d": 0.6, "canopy_r": 6, "canopy_z": 4, "autumn": True},
    ],
    "neighbors": [
        {"note": "west neighbor", "b": [-55, 0, -20, 40], "eave_z": 20, "ridge_z": 28, "ridge_axis": "y", "m": "roman_brick"},
        {"note": "east neighbor", "b": [60, 0, 95, 40], "eave_z": 20, "ridge_z": 28, "ridge_axis": "y", "m": "roman_brick"},
    ],
    "structures": [
        {"note": "swim spa shell", "kind": "box", "b": [30, 50, 37.5, 64, -3.3, 1.2], "m": "steel_black"},
        {"note": "swim spa water", "kind": "box", "b": [30.3, 50.3, 37.2, 63.7, 0.85, 0.9], "m": "water_teal"},
        {"note": "spa deck rim", "kind": "ring", "b": [28.5, 48.5, 39, 65.5], "inner": [30, 50, 37.5, 64], "z0": 1.0, "z1": 1.2, "m": "walnut"},
        {"note": "spa brick wall north", "kind": "box", "b": [28.5, 65.5, 39, 66.5, -0.3, 1.2], "m": "roman_brick"},
        {"note": "spa brick wall east", "kind": "box", "b": [39, 48.5, 40, 66.5, -0.3, 1.2], "m": "roman_brick"},
        {"note": "spa steps", "kind": "steps", "b": [31.5, 47.2, 36, 48.5], "z0": -0.3, "z1": 1.0, "n": 2, "m": "bluestone"},
        {"note": "spa equipment box", "kind": "box", "b": [38.5, 58, 41.5, 62, -0.3, 3], "m": "cedar_ext"},
        {"note": "grill counter", "kind": "box", "b": [22, 46.5, 30, 49.5, -0.3, 2.7], "m": "roman_brick"},
        {"note": "trash corral", "kind": "box", "b": [18, 94, 24, 100, -0.5, 4.5], "m": "cedar_ext", "hollow": True},
        {"note": "catio frame", "kind": "frame", "b": [42, 33, 48, 41, -0.5, 8], "post": 0.33, "m": "cedar_ext", "screen_m": "screen_black"},
        {"note": "breezeway slat screen", "kind": "slats", "b": [-6.2, 30, -6.0, 64, 0, 7], "m": "cedar_ext", "slat_w": 0.29, "gap": 0.17},
        {"note": "utility pole", "kind": "cylinder", "pos": [52, 108], "r": 0.5, "z0": -0.5, "z1": 30, "m": "walnut"},
    ],
}

# ----------------------------------------------------------------------------- lighting, camera, shots  spec 9, 10
lighting = {"fill_scale": {"main": 0.35, "second": 0.35, "basement": 1.2, "garage": 1.0}, "practical_scale": 1.3,
            "sun_strength": 2.0, "sky_strength": 0.45, "hdri": "sky", "hdri_rot_deg": 0, "sun_kelvin": 4800, "sun_angle_deg": 1.0,
            "fill_kelvin": 3000}
camera = {"focal_mm": 24, "sensor_mm": 36, "exposure": 0.0, "fstop": 4.0, "handheld_ft": 0.06}
shots = [
    {"name": "street", "seconds": 12, "exposure": -0.3, "path": [
        {"t": 0, "pos": [10.5, -34, 5.5], "look": [14, 0, 6]}, {"t": 4, "pos": [10.5, -22, 5.5], "look": [12, 0, 5]},
        {"t": 8, "pos": [10.5, -12, 5.5], "look": [11, 0, 4.5]}, {"t": 12, "pos": [11, -6.5, 5.5], "look": [11, 0, 4]}]},
    {"name": "main_floor", "seconds": 26, "path": [
        {"t": 0, "pos": [11, 3, 5.5], "look": [11, 12, 5]}, {"t": 3, "pos": [11, 9, 5.5], "look": [22, 9.5, 5]},
        {"t": 6, "pos": [23, 9.5, 5.5], "look": [25, 1, 4]}, {"t": 9, "pos": [25, 8, 5.5], "look": [25, 30, 5]},
        {"t": 13, "pos": [25, 17, 5.5], "look": [12, 22, 4.5]}, {"t": 17, "pos": [17, 20, 5.5], "look": [6, 28, 4.5]},
        {"t": 21, "pos": [12, 31, 5.5], "look": [2, 38, 4.5]}, {"t": 24, "pos": [9, 37, 5.5], "look": [14, 46, 5]},
        {"t": 26, "pos": [9, 39, 5.5], "look": [25, 38, 4.5]}]},
    {"name": "basement", "seconds": 20, "exposure": 0.8, "path": [
        {"t": 0, "pos": [29.5, 10, 4.5], "look": [29.5, 4, -4]}, {"t": 3, "pos": [32.5, 9, -1], "look": [32.5, 2, -8]},
        {"t": 6, "pos": [29.5, 3, -4.5], "look": [24, 8, -5]}, {"t": 9, "pos": [25, 10, -4.5], "look": [8, 8, -5.5]},
        {"t": 12, "pos": [25, 24, -4.5], "look": [12, 24, -5.5]}, {"t": 15, "pos": [23, 34, -4.5], "look": [10, 38, -7]},
        {"t": 18, "pos": [14, 42, -4.5], "look": [10, 34, -8]}, {"t": 20, "pos": [17, 40, -4.5], "look": [25, 41, -6.5]}]},
    {"name": "upstairs", "seconds": 18, "path": [
        {"t": 0, "pos": [32.5, 11, 14.5], "look": [32, 16, 15]}, {"t": 3, "pos": [25, 16, 15.5], "look": [22, 16, 15]},
        {"t": 6, "pos": [20, 14, 15.5], "look": [25, 9, 15]}, {"t": 9, "pos": [16, 12, 15.5], "look": [12, 10, 14.5]},
        {"t": 11, "pos": [15, 17, 15.5], "look": [12.5, 19, 14.5]}, {"t": 12.2, "pos": [16.5, 21.5, 15.5], "look": [20, 25, 15]},
        {"t": 13.1, "pos": [21.5, 24, 15.5], "look": [25, 29, 15]}, {"t": 14, "pos": [25, 30, 15.5], "look": [18, 40, 15]},
        {"t": 18, "pos": [19, 36, 15.5], "look": [17, 44, 14.5]}]},
    {"name": "terrace_dusk", "seconds": 12, "dusk": True, "exposure": 0.5, "path": [
        {"t": 0, "pos": [36, 78, 5.5], "look": [12, 46, 6]}, {"t": 5, "pos": [26, 66, 5.5], "look": [10, 46, 5]},
        {"t": 9, "pos": [16, 58, 5.5], "look": [8, 40, 4.5]}, {"t": 12, "pos": [11, 48, 5.5], "look": [2, 38, 4]}]},
    {"name": "bedroom", "seconds": 8, "morning": True, "path": [
        {"t": 0, "pos": [33, 44, 5.5], "look": [35, 31, 3.5]}, {"t": 4, "pos": [30, 41, 5.5], "look": [39, 32, 2.5]},
        {"t": 8, "pos": [31, 37, 5.5], "look": [41, 41, 4]}]},
    {"name": "garage", "seconds": 8, "path": [
        {"t": 0, "pos": [6, 96, 5.5], "look": [0, 76, 5]}, {"t": 1.6, "pos": [2.5, 94.3, 5.5], "look": [0, 76, 5.5]},
        {"t": 4, "pos": [2, 86, 5.5], "look": [0, 74, 6.5]},
        {"t": 8, "pos": [-2, 78, 5.5], "look": [6, 66, 3.5]}]},
]
stills = [
    {"name": "01_street_end", "shot": "street", "t": 12}, {"name": "02_main_kitchen", "shot": "main_floor", "t": 13},
    {"name": "03_main_living", "shot": "main_floor", "t": 21}, {"name": "04_main_end", "shot": "main_floor", "t": 26},
    {"name": "05_basement_gym", "shot": "basement", "t": 9}, {"name": "06_basement_pit", "shot": "basement", "t": 18},
    {"name": "07_basement_end", "shot": "basement", "t": 20}, {"name": "08_upstairs_rack", "shot": "upstairs", "t": 11},
    {"name": "09_upstairs_end", "shot": "upstairs", "t": 18}, {"name": "10_terrace_end", "shot": "terrace_dusk", "t": 12},
    {"name": "11_bedroom_end", "shot": "bedroom", "t": 8}, {"name": "12_garage_end", "shot": "garage", "t": 8},
]
views = [
    {"name": "v01_vestibule", "pos": [11, 1, 5.5], "look": [11, 12, 4.5]},
    {"name": "v02_spine_south", "pos": [25, 30, 5.5], "look": [25, 0, 4.5]},
    {"name": "v03_stair_hall", "pos": [29.5, 12, 5.5], "look": [32, 1, 4]},
    {"name": "v04_kitchen_nook", "pos": [20, 28, 5.5], "look": [2, 28.5, 3.5]},
    {"name": "v05_living_wide", "pos": [20, 32, 5.5], "look": [3, 42, 4]},
    {"name": "v06_bath", "pos": [29, 21, 5.5], "look": [40, 14, 4]},
    {"name": "v07_closet", "pos": [32, 23, 5.5], "look": [41, 29, 3.5]},
    {"name": "v08_bedroom", "pos": [29, 44, 5.5], "look": [38, 31, 3.5]},
    {"name": "v09_office", "pos": [9, 8, 15.5], "look": [2, 18, 14.5]},
    {"name": "v10_lab", "pos": [21, 21, 15.5], "look": [12, 8, 14.5]},
    {"name": "v11_loft", "pos": [23, 28, 15.5], "look": [16, 44, 14.5]},
    {"name": "v12_bedroom_b", "pos": [29, 45, 15.5], "look": [40, 31, 14]},
    {"name": "v13_gym", "pos": [20, 18, -4.5], "look": [4, 4, -6.5]},
    {"name": "v14_recovery", "pos": [21, 21, -4.5], "look": [4, 25, -6.5]},
    {"name": "v15_lounge", "pos": [20, 44, -4.5], "look": [4, 32, -7.5]},
    {"name": "v16_exterior_front", "pos": [-12, -40, 6], "look": [16, 6, 8]},
    {"name": "v17_exterior_rear", "pos": [20, 90, 8], "look": [14, 46, 8]},
    {"name": "v18_garage", "pos": [6, 104, 6], "look": [4, 80, 6]},
]

ask("10 Shot 4 (upstairs) t 11 -> t 14 runs from the rack closet straight to the hall through two 3 ft doors on a curve; "
    "the camera clipped both jambs. Added waypoints in the corridor door (16.5, 21.5) and the hall door (21.5, 24). "
    "Shot 7 (garage) t 0 -> t 4 passed through the north wall beside the west door; added a waypoint in the door at (2.5, 94.3).")

plan = {
    "units": "feet", "fps": 24, "wall_thickness": 0.5, "slab_thickness": 0.5,
    "materials_file": "materials/materials.json", "source": "housemasterspec.md",
    "floors": floors, "rooms": rooms, "openings": openings, "voids": voids, "stairs": stairs,
    "beams": [{"room": "living", "axis": "x", "positions": [30.5, 34.5, 38.5, 42.5, 45.5], "w_in": 6, "d_in": 12, "m": "walnut", "deck_m": "oak_decking"}],
    "columns": [{"note": "walnut-wrapped column", "b": [7.5, 29.5, 8.5, 30.5, 0, 9.5], "m": "walnut"},
                {"note": "walnut-wrapped column", "b": [21.5, 29.5, 22.5, 30.5, 0, 9.5], "m": "walnut"}],
    "no_baseboard": ["gym", "mechanical", "battery", "storage", "gear_closet", "coat_closet", "panel_closet", "elevator_closet",
                     "elevator_closet2", "litter_closet", "closet_a", "closet_b", "linen", "rack_closet", "garage", "up_laundry", "sauna"],
    "exterior": exterior, "site": site, "lighting": lighting, "camera": camera,
    "sun": {"direction": [0.35, -0.55, -0.75], "strength": 2.0},
    "shots": shots, "stills": stills, "views": views, "questions": Q,
}


def check():
    """Sanity: rooms on a floor tile their footprint without overlap; openings sit on a room edge."""
    problems = []
    for fl in floors:
        rs = [r for r in rooms if r["floor"] == fl]
        parts = [(r["name"], p) for r in rs for p in r["parts"]]
        area = sum((p[2] - p[0]) * (p[3] - p[1]) for _, p in parts)
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                a, b = parts[i][1], parts[j][1]
                if min(a[2], b[2]) - max(a[0], b[0]) > 1e-6 and min(a[3], b[3]) - max(a[1], b[1]) > 1e-6:
                    problems.append("overlap on %s: %s %s vs %s %s" % (fl, parts[i][0], a, parts[j][0], b))
        print("%-9s rooms %2d  parts %2d  area %6.1f sq ft" % (fl, len(rs), len(parts), area))
    for o in openings:
        rs = [r for r in rooms if r["floor"] == o["floor"]]
        lo, hi = o["c"] - o["w"] / 2, o["c"] + o["w"] / 2
        # the opening span must be covered by the edges of parts of ONE room on at least one side of the wall
        covered_by_room = set()
        for r in rs:
            segs = []
            for p in r["parts"]:
                if o["axis"] == "x" and (abs(p[1] - o["at"]) < 1e-6 or abs(p[3] - o["at"]) < 1e-6):
                    segs.append((p[0], p[2]))
                if o["axis"] == "y" and (abs(p[0] - o["at"]) < 1e-6 or abs(p[2] - o["at"]) < 1e-6):
                    segs.append((p[1], p[3]))
            # merge and test coverage
            segs.sort()
            cur = lo
            for a, b in segs:
                if a - 1e-6 <= cur <= b + 1e-6:
                    cur = max(cur, b)
            if cur >= hi - 1e-6 and segs:
                covered_by_room.add(r["name"])
        if not covered_by_room:
            problems.append("opening not covered by one room's edge: %s" % o["note"])
    return problems


if __name__ == "__main__":
    probs = check()
    for p in probs:
        print("PROBLEM", p)
    out = os.path.join(ROOT, "plan.json")
    json.dump(plan, open(out, "w"), indent=1)
    print("wrote", out, "rooms", len(rooms), "openings", len(openings), "questions", len(Q))
