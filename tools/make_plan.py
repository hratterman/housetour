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

# ----------------------------------------------------------------------------- stair core geometry
# Switchback (U) stair in the 7 x 13 stair hall, stacked: two flights 3 ft clear between finished faces (IRC 36 in), 8 risers each at 7.5 in,
# 7 treads at 10 in (5.83 ft), a 3.25 ft landing against the south wall, and a 3.17 ft arrival zone at the north end
# that opens to the spine (main), the landing (second) and the basement hall. The down stair sits directly under the
# up stair with 10 ft between flights everywhere. A solid walnut-panelled centre wall separates the flights.
RISE = 10.0 / 16          # 7.5 in
TREAD = 10.0 / 12         # 10 in
FLIGHT = 7 * TREAD        # 5.833 ft between first nosing and top riser
LAND_S = 0.5              # inside face of the south exterior wall
LAND_N = LAND_S + 3.25    # landing depth 3.25 ft (>= stair width)
WELL_N = round(LAND_N + FLIGHT, 3)   # 9.583: north edge of the flights / south edge of the arrival zone
CW = 0.25                 # centre wall half thickness

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
room("vestibule", "main", [8, 0, 14, 6], "terrazzo_3ft", "walnut_panel", "plaster_warm", 50)
room("powder", "main", [14, 0, 19, 6], "terrazzo", "wallpaper_botanical_dark", "oxblood", 30)
room("coat_closet", "main", [19, 0, 22, 6], "oak_floor", "plaster_warm", "plaster_warm", 20, label="coat closet")
room("panel_closet", "main", [0, 6, 8, 13], "concrete_sealed", "plaster_warm", "plaster_warm", 20, label="panel closet")
room("entry_hall", "main", [8, 6, 22, 13], "oak_floor", "plaster_warm", "plaster_warm", 80, label="entry hall")
room("spine", "main", [22, 0, 28, 30], "oak_floor", "oxblood", "oxblood", 90, label="gallery spine")
room("stair_hall", "main", [28, 0, 35, 13], "oak_floor", "plaster_warm", "plaster_warm", 60, label="stair hall")
room("laundry", "main", [[35, 0, 42, 6], [38, 6, 42, 9], [35, 9, 42, 13]], "terrazzo", "plaster_warm", "plaster_warm", 70)
room("elevator_closet", "main", [35, 6, 38, 9], "concrete_sealed", "plaster_warm", "plaster_warm", 10, label="elevator")
room("mudroom", "main", [[3, 13, 8, 16], [0, 16, 8, 21]], "terrazzo", "plaster_warm", "plaster_warm", 70)
room("litter_closet", "main", [0, 13, 3, 16], "terrazzo", "plaster_warm", "plaster_warm", 10, label="litter")
room("pantry", "main", [0, 21, 8, 27], "terrazzo", "plaster_warm", "plaster_warm", 50)
room("kitchen", "main", [[8, 13, 22, 30], [0, 27, 8, 30]], "oak_floor", "plaster_warm", "plaster_warm", 160)
room("living", "main", [0, 30, 20, 46], "oak_floor", "plaster_warm", "oak_decking", 150, label="living room")
room("away", "main", [20, 30, 28, 46], "oak_floor", "wallpaper_geo_olive", "olive_paint", 60, label="away room")
room("primary_bath", "main", [[28, 13, 37.75, 22], [37.75, 18, 42, 22]], "terrazzo", "plaster_warm", "plaster_warm", 90, label="primary bath")
room("wc", "main", [37.75, 13, 42, 18], "terrazzo", "plaster_warm", "plaster_warm", 20, label="wc")
room("suite_hall", "main", [28, 22, 32, 30], "oak_floor", "oxblood", "plaster_warm", 30, label="suite hall")
room("primary_closet", "main", [32, 22, 42, 30], "wool_carpet", "walnut", "plaster_warm", 80, label="primary closet")
room("primary_bedroom", "main", [28, 30, 42, 46], "wool_carpet", "plaster_warm", "plaster_warm", 90, label="primary bedroom")

# --- second floor (spec 4, table). The well over the stair hall is a void with walls two stories high.
room("her_office", "second", [0, 6, 11, 26], "wool_carpet_charcoal", "plaster_warm", "plaster_warm", 100, label="her office")
room("lab", "second", [[11, 6, 22, 16], [14, 16, 22, 22], [22, 6, 28, 13]], "cork", "plaster_warm", "plaster_warm", 120)
room("rack_closet", "second", [11, 16, 14, 22], "concrete_sealed", "plaster_warm", "plaster_warm", 15, label="rack")
room("work_corridor", "second", [11, 22, 22, 26], "oak_floor", "oxblood", "plaster_warm", 30, label="work corridor")
room("stair_well", "second", [28, 0, 35, WELL_N], "oak_floor", "plaster_warm", "plaster_warm", 40, void=True, label="stair well (open)")
room("landing", "second", [[22, 13, 42, 19], [28, WELL_N, 35, 13]], "oak_floor", "oxblood", "plaster_warm", 80)
room("elevator_closet2", "second", [35, 6, 38, 9], "concrete_sealed", "plaster_warm", "plaster_warm", 10, label="elevator")
room("up_laundry", "second", [[35, 9, 42, 13], [38, 6, 42, 9]], "terrazzo", "plaster_warm", "plaster_warm", 30, label="laundry closet")
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
room("bstair_hall", "basement", [28, 0, 35, 13], "oak_floor", "plaster_warm", "plaster_warm", 40, label="stair hall")
room("battery", "basement", [35, 0, 42, 13], "concrete_sealed", "concrete_sealed", "concrete_sealed", 60, label="battery room")
room("mechanical", "basement", [28, 13, 42, 34], "concrete_sealed", "concrete_sealed", "concrete_sealed", 120)
room("storage", "basement", [28, 34, 42, 46], "concrete_sealed", "plaster_warm", "plaster_warm", 60, label="storage / projects")

# --- garage (spec 7): one open volume, brick to Z 8 then cedar (handled by the exterior pass)
room("garage", "garage", [-6, 64, 18, 94], "concrete_sealed", "plaster_warm", "plaster_warm", 200, exterior_wall=1.0)

# ----------------------------------------------------------------------------- openings
# axis x: wall runs along X at Y=at; axis y: wall runs along Y at X=at. c = center along the wall.
openings = []
ARRIVE_C = round((WELL_N + 12.75) / 2, 3)   # centre of the 3.17 ft arrival zone at the north end of the stair hall


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
op("S5 stair hall clerestory", "main", "x", 0, 31.5, 4, 7.0, 2.0, "window")
op("S6 laundry window", "main", "x", 0, 38.5, 5, 5.0, 2.5, "window", obscure=True)
op("W1 mudroom side door", "main", "y", 0, 17.75, 3, 0, 7.0, "door", exterior=True, swing="in", open_deg=0, leaf="half_glass")
op("N1 living lift-and-slide", "main", "x", 46, 11, 16, 0, 8.5, "glasswall", panels=4, portal=True, door_panel=None)
op("N2 away window", "main", "x", 46, 25, 4, 2.5, 5.0, "window")
op("N3 bedroom window", "main", "x", 46, 36, 8, 2.0, 6.0, "window", portal=True, mullions=[2, 6])
op("E1 laundry high window", "main", "y", 42, 4, 4, 6.0, 2.0, "window")
op("E2 bath window", "main", "y", 42, 20, 3, 5.0, 2.0, "window", obscure=True)  # over the shower, clear of the WC (Y 13-18)
op("E3 closet window", "main", "y", 42, 26, 4, 5.0, 2.5, "window", obscure=True)
op("E4 bedroom window", "main", "y", 42, 39, 6, 2.5, 5.0, "window", portal=True)
op("E5 cat tunnel", "main", "y", 42, 38.25, 1.5, 0.2, 1.5, "hatch")
op("S7 her office window", "second", "x", 6, 5.5, 7, 2.5, 5.0, "window")
op("S8 lab window run", "second", "x", 6, 20, 14, 2.5, 5.0, "window", portal=True, panels=4)
op("S9 landing clerestory", "second", "x", 0, 31.5, 4, 6.5, 2.0, "window")
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
op("B1 gym well", "basement", "y", 0, 6, 4, 3.5, 6.0, "window", well=True)  # egress: sill 42 in, deep well with ladder
op("B2 lounge well", "basement", "y", 0, 38, 4, 3.5, 6.0, "window", well=True)  # egress
op("B3 lounge well", "basement", "x", 46, 18, 4, 6.5, 3.0, "window", well=True)
op("B4 storage well", "basement", "x", 46, 34, 4, 6.5, 2.5, "window", well=True)

# main floor interior doors and openings (spec 3.x)
op("gear closet door", "main", "y", 8, 3, 3, 0, 7, "door", open_deg=0)
op("vestibule inner glass door", "main", "x", 6, 11, 4, 0, 8, "glassdoor", open_deg=90)
op("vestibule inner sidelight", "main", "x", 6, 13.5, 1, 0, 8, "window", interior=True)
op("powder door", "main", "x", 6, 17, 2.67, 0, 7, "door", open_deg=0)
op("coat closet door", "main", "x", 6, 20.5, 2.0, 0, 7, "door", open_deg=0)
op("panel closet door", "main", "y", 8, 9.5, 3, 0, 7, "door", open_deg=0)
op("entry hall to spine", "main", "y", 22, 9.5, 5, 0, 8.5, "cased")
op("spine to stair hall", "main", "y", 28, ARRIVE_C, 3, 0, 8.5, "cased")
op("spine to kitchen", "main", "y", 22, 16.5, 6, 0, 9.0, "cased")
op("spine to suite hall", "main", "y", 28, 28, 3, 0, 7, "door", open_deg=0)
op("spine to away room", "main", "x", 30, 25, 3.5, 0, 8, "glassdoor", open_deg=0)  # terminates the gallery axis on N2
op("stair hall to laundry", "main", "y", 35, 10.9, 2.5, 0, 7, "door", open_deg=0)   # off the arrival zone; the bath keeps its privacy
op("elevator closet door", "main", "y", 38, 7.5, 2.5, 0, 7, "door", open_deg=0)
op("mudroom to kitchen", "main", "y", 8, 17.5, 3, 0, 7, "door", open_deg=80)  # on axis with the side door W1
op("litter cat door", "main", "y", 3, 14.5, 0.67, 0.2, 0.7, "hatch")
op("litter service door", "main", "x", 16, 1.5, 2, 0, 7, "door", open_deg=0)
op("pantry door", "main", "y", 8, 24, 3, 0, 7, "door", open_deg=45, swing="out")   # into the pantry, clear of the island chairs
op("kitchen open to living", "main", "x", 30, 10, 20, 0, 9.5, "open", full=True)
op("living to away pocket door", "main", "y", 20, 38.5, 5, 0, 8, "pocket", open_ft=3)
op("wc door", "main", "y", 37.75, 15.5, 2.5, 0, 7, "door", open_deg=0, leaf="frosted", swing="out")
op("closet to bath", "main", "x", 22, 37, 3, 0, 7, "door", open_deg=80)
op("suite hall to bath", "main", "x", 22, 30, 3, 0, 7, "door", open_deg=0)
op("suite hall to bedroom", "main", "x", 30, 30, 3, 0, 7, "door", open_deg=80)
op("suite hall to closet", "main", "y", 32, 26, 3, 0, 7, "door", open_deg=80)
op("closet to bedroom", "main", "x", 30, 36, 3, 0, 7, "door", open_deg=80)

# second floor (spec 4.x)
op("her office door", "second", "y", 11, 24, 3, 0, 7, "door", open_deg=0)
op("hall to work corridor", "second", "y", 22, 24, 3, 0, 7, "door", open_deg=80)
op("work corridor to lab", "second", "x", 22, 16.5, 3, 0, 7, "door", open_deg=80)
op("rack closet glass door", "second", "y", 14, 19, 2.5, 0, 7, "glassdoor", open_deg=0)
op("landing to lab", "second", "y", 22, 16, 3, 0, 7, "door", open_deg=80)
op("landing to laundry closet", "second", "x", 13, 37.5, 4, 0, 7, "door", open_deg=0, leaves=2)
op("chute flap", "second", "x", 13, 40.25, 1.5, 3.0, 1.5, "hatch")
op("elevator closet2 door", "second", "x", 9, 36.5, 2.5, 0, 7, "door", open_deg=0)
op("kid zone door", "second", "x", 26, 25, 3, 0, 7, "door", open_deg=90)
op("kid zone sidelight", "second", "x", 26, 27.125, 1.25, 0, 7, "window", interior=True)
op("hall to kid bath", "second", "y", 28, 23.5, 3, 0, 7, "door", open_deg=0)
op("sink room to tub room", "second", "y", 35, 23.5, 2.67, 0, 7, "door", open_deg=45, leaf="frosted")
op("hall to bedroom B", "second", "y", 28, 40, 3, 0, 7, "door", open_deg=80)
op("hall to linen", "second", "y", 28, 35, 2, 0, 7, "door", open_deg=0)
op("closet B door", "second", "y", 31, 30.5, 2.67, 0, 7, "door", open_deg=60)
op("loft to bedroom A", "second", "y", 14, 37, 3, 0, 7, "door", open_deg=80)
op("closet A door", "second", "y", 11, 28.5, 2.67, 0, 7, "door", open_deg=0)
op("loft to hedge alcove", "second", "y", 14, 43, 4, 0, 7, "cased")
op("loft open to hall", "second", "y", 22, 36, 20, 0, 9.0, "open", full=True)
op("well open to landing", "second", "x", WELL_N, 31.5, 7, 0, 9.0, "open", full=True)  # guard built with the stair

# basement (spec 5.x)
op("bhall to bstair hall", "basement", "y", 28, ARRIVE_C, 3, 0, 8.5, "cased")
op("gym glass door", "basement", "y", 22, 10, 3, 0, 7, "glassdoor", open_deg=0)
op("gym sidelight", "basement", "y", 22, 14, 4, 0, 7, "window", interior=True)
op("hall to recovery", "basement", "y", 22, 24, 3, 0, 7, "door", open_deg=80)
op("gym to recovery glass door", "basement", "x", 20, 20, 3, 0, 7, "glassdoor", open_deg=0)
op("sauna glass front", "basement", "y", 8, 24, 6, 0, 8, "glasswall", panels=1, door_panel=None, interior=True)
op("hall to mechanical", "basement", "y", 28, 16, 3, 0, 7, "door", open_deg=0, leaf="steel")
op("hall open to bar", "basement", "x", 34, 25, 6, 0, 9.5, "open", full=True)
op("hall to lounge", "basement", "y", 22, 31, 5, 0, 8.5, "cased")
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
    {"note": "stair core: down flights and landing pass through the main floor", "floor": "main", "what": "floor", "b": [28, LAND_S, 35, WELL_N]},
    {"note": "stair core: two-story well over the up flights", "floor": "main", "what": "ceil", "b": [28, LAND_S, 35, WELL_N]},
    {"note": "stair core: no second floor slab over the well", "floor": "second", "what": "floor", "b": [28, LAND_S, 35, WELL_N]},
    {"note": "stair core: down flights pass the basement ceiling", "floor": "basement", "what": "ceil", "b": [28, LAND_S, 35, WELL_N]},
    {"note": "laundry chute", "floor": "main", "what": "ceil", "b": [40.0, 11.75, 41.0, 12.75]},
    {"note": "laundry chute", "floor": "second", "what": "floor", "b": [40.0, 11.75, 41.0, 12.75]},
]

# ----------------------------------------------------------------------------- stairs  spec 6
FIN = {"tread_m": "oak_floor", "riser_m": "oak_floor", "stringer_m": "walnut", "rail_m": "bronze_black"}
stairs = [
    # up: west flight rises south from the arrival zone to the landing, east flight rises north to the second floor
    dict(kind="flight", name="up_a", x0=28, x1=31.5, y_from=WELL_N, y_to=LAND_N, z_from=0.0, z_to=5.0, risers=8, handrail="west", **FIN),
    dict(kind="landing", name="up_landing", b=[28, LAND_S, 35, LAND_N], z=5.0, t=0.6, **FIN),
    dict(kind="flight", name="up_b", x0=31.5, x1=35, y_from=LAND_N, y_to=WELL_N, z_from=5.0, z_to=10.0, risers=8, handrail="east", **FIN),
    # down: east flight descends south under up_b, west flight descends north under up_a
    dict(kind="flight", name="down_a", x0=31.5, x1=35, y_from=WELL_N, y_to=LAND_N, z_from=0.0, z_to=-5.0, risers=8, handrail="east", **FIN),
    dict(kind="landing", name="down_landing", b=[28, LAND_S, 35, LAND_N], z=-5.0, t=0.6, **FIN),
    dict(kind="flight", name="down_b", x0=28, x1=31.5, y_from=LAND_N, y_to=WELL_N, z_from=-5.0, z_to=-10.0, risers=8, handrail="west", **FIN),
    # centre wall between the flights, basement floor to guard height above the second floor
    dict(kind="wall", name="stair_centre_wall", b=[31.5 - CW, LAND_N, 31.5 + CW, WELL_N, -10.0, 13.5], m="walnut_panel"),
    # fill the slab-thickness band around the well where the main ceiling slab is cut
    dict(kind="wall", name="well_band_w", b=[28, 0.5, 28.25, WELL_N + 0.25, 9.5, 10.0], m="plaster_warm"),
    dict(kind="wall", name="well_band_e", b=[34.75, 0.5, 35, WELL_N + 0.25, 9.5, 10.0], m="plaster_warm"),
    dict(kind="wall", name="well_band_s", b=[28, 0, 35, 1.0, 9.5, 10.0], m="plaster_warm"),   # inside the 1 ft exterior wall zone
    # bronze-post glass guard on the second floor along the well edge west of the up_b arrival
    dict(kind="guard", name="well_guard", p0=[28.1, WELL_N + 0.1, 10.0], p1=[31.5 - CW, WELL_N + 0.1, 10.0], h=3.5, m="bronze_black", glass=True),
]

# ----------------------------------------------------------------------------- exterior + roofs  spec 2
# The stair core X 28-35, Y 0-13 rises through the low front band as a cedar stair tower (the spec puts clerestories
# S5 and S9 stacked on its Y 0 face); its cap sits 2 ft above the main gable's eave and the low roofs stop against it.
TOWER_X0, TOWER_X1 = 28.0, 35.0   # exterior wall faces sit on the room lines
TOWER_TOP = 21.0
exterior = {
    "wall_t": 1.0,
    "base": {"m_out": "roman_brick", "z0": -0.5, "z1": 9.5, "floors": ["main"]},
    "upper": {"m_out": "cedar_ext", "z0": 10.0, "z1": 19.0, "floors": ["second"], "reveal": {"m": "bronze_black", "z0": 9.5, "z1": 10.0}},
    "garage": {"m_out_low": "roman_brick", "m_out_high": "cedar_ext", "split_z": 8.0},
    "roofs": [
        {"name": "main gable", "type": "gable", "ridge_axis": "x", "ridge_at": 26, "x0": -4, "x1": 46, "y0": 2, "y1": 50,
         "z_wall": 19.5, "pitch": 0.25, "thick": 0.6, "fascia": 1.0, "m": "metal_roof_charcoal", "soffit_m": "cedar_ext",
         "rafter_tails": 4.0, "skylights": [[26, 16, 3, 4], [38, 16, 3, 4], [18, 40, 3, 4]],
         "cuts": [[TOWER_X0, 1.5, TOWER_X1, 7.0], [-1.5, 36, 0.5, 40]]},  # stair tower through the south eave; vent chase through the west rake
        {"name": "stair tower cap", "type": "flat", "x0": TOWER_X0, "x1": TOWER_X1, "y0": 0, "y1": 7.0, "z": TOWER_TOP, "thick": 0.5, "fascia": 1.0,
         "m": "metal_roof_charcoal", "soffit_m": "cedar_ext"},
        {"name": "front shed west", "type": "shed", "x0": -1.0, "x1": TOWER_X0, "y0": -1.5, "y1": 6, "z_high": 10.5, "z_low": 10.21, "slope_to": "south",
         "thick": 0.5, "fascia": 1.0, "m": "metal_roof_charcoal", "soffit_m": "cedar_ext", "beams": {"axis": "y", "spacing": 4, "w_in": 6, "d_in": 12}},
        {"name": "front shed east", "type": "shed", "x0": TOWER_X1, "x1": 43.0, "y0": -1.5, "y1": 6, "z_high": 10.5, "z_low": 10.21, "slope_to": "south",
         "thick": 0.5, "fascia": 1.0, "m": "metal_roof_charcoal", "soffit_m": "cedar_ext", "beams": {"axis": "y", "spacing": 4, "w_in": 6, "d_in": 12}},
        {"name": "porch canopy", "type": "shed", "x0": 4, "x1": 22, "y0": -7, "y1": -1.5, "z_high": 10.21, "z_low": 10.0, "slope_to": "south",
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
    "bands": [
        {"note": "front band brick to the low roof, south west", "b": [0, 0, TOWER_X0, 1.0, 9.5, 10.0], "m": "roman_brick"},
        {"note": "front band brick to the low roof, south east", "b": [TOWER_X1, 0, 42, 1.0, 9.5, 10.0], "m": "roman_brick"},
        {"note": "front band brick, west return", "b": [0, 1.0, 1.0, 6.0, 9.5, 10.0], "m": "roman_brick"},
        {"note": "front band brick, east return", "b": [41, 1.0, 42, 6.0, 9.5, 10.0], "m": "roman_brick"},
    ],
    "tower": {"b": [TOWER_X0, 0, TOWER_X1, 7.0], "inner": [29, 1, 34, 6], "z_wall_top": 19.0, "z_top": TOWER_TOP,
              "m": "cedar_ext", "reveal": {"m": "bronze_black", "z0": 9.5, "z1": 10.0}},
}
# ----------------------------------------------------------------------------- neighborhood (Henry: "set in the context of
# other surrounding homes, like the North Shore villages"). A village block: 30 ft street with concrete curbs and
# gutters, 8 ft parkways with big street trees, 5 ft sidewalks, 30 ft setbacks, mixed 1910s-1950s houses, rear
# garages on the alley, wood fences between back yards. The spec's two brick neighbours become the first two lots.
def lot(x0, x1, hx0, style, front_y, facing, walk_x, **kw):
    d = {"x0": x0, "x1": x1, "hx0": hx0, "style": style, "front_y": front_y, "facing": facing, "walk_x": walk_x}
    d.update(kw)
    return d


NEIGHBORHOOD = {
    "seed": 1926,
    "street": {
        "x": [-230, 270],
        "curb_y": [-38, -68],                    # north curb (our side), south curb
        "sidewalks": [[-30, -25], [-81, -76]],
        "sidewalk_y": [-25, -81],
        "trees": {"y": [-34, -72], "spacing": 42, "offset": 14, "species": ["elm", "oak", "maple", "elm", "locust"],
                  "skip_x": [10.5], "skip_x_s": [21]},
        "lamps": [[-150, -35.5], [-10, -35.5], [130, -35.5], [-80, -70.5], [60, -70.5], [200, -70.5]],
        "hydrants": [[26, -33.5]],
        "aprons": [[-105, -70, -93, -64], [77, -70, 88, -64], [188, -70, 208, -64]],
    },
    "lots": [
        # our block, north side of the street, houses face south
        lot(-75, -9, -62, "tudor", 1, "s", -38.5, garage={"b": [-56, 78, -34, 100], "m": "brick_common"},
            trees=[{"pos": [-58, -16], "species": "maple"}]),
        lot(-140, -75, -126, "georgian", 2, "s", -107, garage={"b": [-120, 78, -98, 100], "m": "brick_red"},
            trees=[{"pos": [-135, -12], "species": "oak"}]),
        lot(-205, -140, -188, "foursquare", 3, "s", -182, garage={"b": [-180, 78, -158, 100], "m": "siding_gray"},
            trees=[{"pos": [-150, -10], "species": "spruce"}]),
        lot(51, 111, 65, "bungalow", 4, "s", 75.2, garage={"b": [70, 78, 92, 100], "m": "siding_sage"},
            trees=[{"pos": [105, -14], "species": "maple"}]),
        lot(111, 171, 118, "colonial", 2, "s", 136, wing="right", garage={"b": [125, 78, 147, 100], "m": "siding_white"},
            trees=[{"pos": [160, -16], "species": "elm"}]),
        lot(171, 235, 183, "tudor", 1, "s", 206.5, wall_m="brick_red", garage={"b": [190, 78, 212, 100], "m": "brick_red"}),
        # across the street, houses face north; a few have side driveways to rear garages
        lot(-150, -90, -144, "georgian", -111, "n", -125, wall_m="brick_common", shutter_m="shutter_green", portico="flat",
            driveway={"x": -104, "w": 10, "y": [-81, -160]}, garage={"b": [-104, -160, -84, -140], "m": "brick_common", "door_side": "n"},
            trees=[{"pos": [-140, -95], "species": "oak"}]),
        lot(-90, -30, -75, "foursquare", -112, "n", -69, wall_m="stucco_cream", roof_m="shingle_brown",
            trees=[{"pos": [-36, -100], "species": "maple"}]),
        lot(-30, 30, -12, "colonial", -110, "n", 6, wing="left", shutter_m="shutter_black",
            trees=[{"pos": [26, -96], "species": "elm"}]),
        lot(30, 90, 44, "bungalow", -108, "n", 54.2, wall_m="siding_gray", roof_m="shingle_dark",
            driveway={"x": 78, "w": 9, "y": [-81, -150]}, garage={"b": [70, -152, 90, -132], "m": "siding_gray", "door_side": "n"}),
        lot(90, 150, 100, "tudor", -111, "n", 123.5, trees=[{"pos": [146, -96], "species": "oak"}]),
        lot(150, 215, 153, "ranch", -114, "n", 177, driveway={"x": 189, "w": 18, "y": [-81, -112]}),
        # the next street north (backs to our alley) and the next street south: depth for aerials and gaps
        lot(-200, -140, -186, "colonial", 214, "n", None, wing=None, trees=[{"pos": [-150, 150], "species": "oak"}]),
        lot(-140, -80, -126, "georgian", 212, "n", None, wall_m="brick_common"),
        lot(-80, -20, -66, "bungalow", 216, "n", None, wall_m="siding_gray", trees=[{"pos": [-30, 145], "species": "maple"}]),
        lot(-20, 40, -6, "tudor", 213, "n", None),
        lot(40, 100, 55, "foursquare", 214, "n", None, wall_m="siding_white", trees=[{"pos": [95, 150], "species": "elm"}]),
        lot(100, 160, 112, "colonial", 212, "n", None, wing="right", wall_m="siding_sage"),
        lot(160, 225, 170, "georgian", 214, "n", None, wall_m="brick_red"),
        lot(-190, -130, -176, "tudor", -292, "s", None, trees=[{"pos": [-140, -230], "species": "oak"}]),
        lot(-130, -70, -114, "colonial", -290, "s", None, wing="left"),
        lot(-70, -10, -56, "georgian", -292, "s", None, wall_m="brick_common", portico="flat"),
        lot(-10, 50, 4, "foursquare", -291, "s", None, wall_m="stucco_cream", trees=[{"pos": [40, -232], "species": "elm"}]),
        lot(50, 110, 62, "bungalow", -290, "s", None),
        lot(110, 175, 122, "tudor", -292, "s", None, wall_m="brick_red", trees=[{"pos": [170, -228], "species": "maple"}]),
    ],
    "fences": [
        {"b": [-9.3, 46, -8.7, 100]}, {"b": [-75.3, 40, -74.7, 100]}, {"b": [-140.3, 40, -139.7, 100]},
        {"b": [110.7, 40, 111.3, 100]}, {"b": [170.7, 40, 171.3, 100]},
        {"b": [-90.3, -200, -89.7, -125]}, {"b": [29.7, -200, 30.3, -125]},
    ],
    "hedges": [
        {"b": [-150, -83.5, -92, -82.5], "h": 3.0}, {"b": [-205, -24, -142, -23], "h": 2.5},
    ],
    "trees": [
        # spec 1.1 trees on our lot
        {"pos": [-3, -22], "species": "oak", "h": 42}, {"pos": [36, -24], "species": "oak", "h": 36},
        {"pos": [48, 20], "species": "maple", "h": 40}, {"pos": [30, 110], "species": "locust", "h": 42},
        {"pos": [25, 60], "species": "maple", "h": 16},
        {"pos": [-40, 62], "species": "oak"}, {"pos": [132, 52], "species": "elm"}, {"pos": [-118, -140], "species": "oak"},
        {"pos": [-160, 40], "species": "maple"}, {"pos": [225, 30], "species": "oak"}, {"pos": [120, -150], "species": "elm"},
        {"pos": [-60, -150], "species": "maple"}, {"pos": [200, -100], "species": "spruce"},
    ],
}

# ----------------------------------------------------------------------------- site  spec 1
site = {
    "grade_z": -0.5,
    "lot": [-9, -30, 51, 140],
    "ground": {"m": "lawn", "b": [-400, -400, 450, 450]},
    "slabs": [
        {"note": "front walk", "b": [8, -25, 13, -7], "z": -0.42, "t": 0.3, "m": "bluestone"},
        {"note": "porch step 1", "b": [4, -7, 22, -6.5], "z": -0.3, "t": 0.5, "m": "bluestone"},
        {"note": "porch step 2", "b": [4, -6.5, 22, -6], "z": -0.2, "t": 0.5, "m": "bluestone"},
        {"note": "porch floor", "b": [4, -6, 22, 0], "z": -0.2, "t": 0.5, "m": "bluestone"},
        {"note": "gravel band south", "b": [-1.5, -1.5, 43.5, 0], "z": -0.46, "t": 0.15, "m": "gravel_gray"},
        {"note": "gravel band north", "b": [-1.5, 46, 43.5, 47.5], "z": -0.46, "t": 0.15, "m": "gravel_gray"},
        {"note": "gravel band west", "b": [-1.5, 0, 0, 46], "z": -0.46, "t": 0.15, "m": "gravel_gray"},
        {"note": "gravel band east", "b": [42, 0, 43.5, 46], "z": -0.46, "t": 0.15, "m": "gravel_gray"},
        {"note": "breezeway walk", "b": [-6, 15, 0, 64], "z": -0.4, "t": 0.3, "m": "bluestone"},
        {"note": "terrace", "b": [0, 46, 42, 62], "z": -0.3, "t": 0.4, "m": "bluestone"},
        {"note": "catio floor", "b": [42, 33, 48, 41], "z": -0.3, "t": 0.3, "m": "bluestone"},
        {"note": "driveway apron", "b": [-6, 94, 18, 100], "z": -0.42, "t": 0.3, "m": "concrete_sealed"},
        {"note": "alley", "b": [-230, 100, 270, 116], "z": -0.7, "t": 0.4, "m": "asphalt", "cut_ground": True},
        {"note": "lawn rectangle (edged)", "b": [18, 64, 42, 94], "z": -0.46, "t": 0.1, "m": "lawn"},
    ],
    "beds": [
        {"note": "front bed west", "b": [0, -5.5, 8, -1.5]}, {"note": "front bed east", "b": [22, -5.5, 42, -1.5]},
        {"note": "terrace north bed", "b": [0, 62, 18, 66]}, {"note": "east lot line bed", "b": [48, 0, 51, 100]},
    ],
    "hedges": [
        {"note": "east lot line hedge", "b": [48.5, 0, 50.5, 100], "h": 6},
        {"note": "rear privacy hedge", "b": [18, 100, 51, 101], "h": 7},
    ],
    "trees": [],   # the spec's trees are built by the neighborhood tree builder (models), see NEIGHBORHOOD["trees"]
    "neighbors": [],   # replaced by the neighborhood block below
    "neighborhood": NEIGHBORHOOD,
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
            "sun_strength": 4.0, "sky_strength": 3.0, "sky_clamp": 4.0, "hdri": "sky", "hdri_rot_deg": 0, "sun_kelvin": 4800, "sun_angle_deg": 1.0,
            "fill_kelvin": 3000,
            # camera white balance: lamps at this temperature render neutral (a photo balanced for the room lights)
            "white_balance_k": 3800,
            # per-shot modes (spec 9): blue hour for the terrace shot, low eastern sun for the bedroom shot
            "modes": {
                "dusk": {"sun_strength": 0.25, "sun_direction": [0.85, 0.25, -0.12], "sun_kelvin": 2600, "sky_strength": 0.35,
                         "sky_rgb": [0.55, 0.62, 0.95], "hdri_rot_deg": 60, "fill_mul": 1.6, "practical_mul": 1.5},
                "morning": {"sun_strength": 6.0, "sun_direction": [-0.82, 0.25, -0.38], "sun_kelvin": 3400, "sky_strength": 3.5,
                            "hdri_rot_deg": 180, "fill_mul": 0.8, "practical_mul": 0.9},
            }}
camera = {"focal_mm": 24, "sensor_mm": 36, "exposure": 0.0, "fstop": 4.0, "handheld_ft": 0.06}
shots = [
    {"name": "block", "seconds": 10, "exposure": 0.0, "white_balance_k": 5600, "path": [
        {"t": 0, "pos": [-46, -79, 5.5], "look": [-10, -20, 12]}, {"t": 5, "pos": [-20, -78.5, 5.5], "look": [12, -6, 10]},
        {"t": 10, "pos": [4, -78, 5.5], "look": [20, 0, 9]}]},
    {"name": "street", "seconds": 12, "exposure": 0.0, "white_balance_k": 5600, "path": [
        # exposure rides up as the camera walks from the sunlit sidewalk into the shaded porch
        {"t": 0, "pos": [10.5, -34, 5.5], "look": [14, 0, 6], "exp": 0.0}, {"t": 4, "pos": [10.5, -22, 5.5], "look": [12, 0, 5], "exp": 0.0},
        {"t": 8, "pos": [10.5, -15, 5.5], "look": [11, 0, 4.5], "exp": 0.4}, {"t": 12, "pos": [11, -9.5, 5.3], "look": [12.5, 0, 4.5], "exp": 0.9}]},   # ends on the porch, door and sidelight
    {"name": "main_floor", "seconds": 26, "path": [
        {"t": 0, "pos": [11, 3, 5.5], "look": [11, 12, 5]}, {"t": 3, "pos": [11, 9, 5.5], "look": [22, 9.5, 5]},
        {"t": 4.8, "pos": [19.5, 9.4, 5.5], "look": [28, 9.5, 5]},   # keep looking through the opening at the spine art wall while passing the jamb
        {"t": 6.3, "pos": [23.5, 9.2, 5.5], "look": [25.5, 1.5, 4]}, {"t": 9, "pos": [25, 8, 5.5], "look": [25, 30, 5]},
        {"t": 13, "pos": [25, 17, 5.5], "look": [12, 22, 4.5]}, {"t": 17, "pos": [17, 20, 5.5], "look": [6, 28, 4.5]},
        {"t": 21, "pos": [12, 31, 5.5], "look": [2, 38, 4.5]}, {"t": 24, "pos": [9, 37, 5.5], "look": [14, 46, 5]},
        {"t": 26, "pos": [9, 39, 5.5], "look": [25, 38, 4.5]}]},
    {"name": "basement", "seconds": 24, "exposure": 0.8, "path": [
        # down the switchback: east flight south from the main-floor arrival, landing, west flight north to the basement
        {"t": 0, "pos": [33.25, 12.2, 5.5], "look": [33.25, 4, 0]}, {"t": 3, "pos": [33.25, 6.5, 3.0], "look": [33.25, 1, -3]},
        {"t": 5, "pos": [33.25, 2.2, 0.5], "look": [29.75, 8, -3]}, {"t": 6, "pos": [29.75, 2.2, 0.5], "look": [29.75, 12, -6]},
        {"t": 9, "pos": [29.75, 8, -2.9], "look": [27, 12, -6]}, {"t": 11, "pos": [29.75, 11.2, -4.5], "look": [20, 11.2, -5.5]},
        {"t": 13, "pos": [25, 11.2, -4.5], "look": [8, 8, -5.5]}, {"t": 16, "pos": [25.8, 24, -4.5], "look": [12, 24, -5.5]},
        {"t": 19, "pos": [24, 31, -4.5], "look": [10, 38, -7]}, {"t": 20, "pos": [21, 31.5, -4.5], "look": [8, 40, -7]},
        {"t": 22, "pos": [16, 40, -4.5], "look": [10, 34, -8]}, {"t": 24, "pos": [17, 40, -4.5], "look": [25, 41, -6.5]}]},
    {"name": "upstairs", "seconds": 18, "path": [
        {"t": 0, "pos": [33.25, 11, 14.5], "look": [32.5, 16, 15]}, {"t": 3, "pos": [25, 16, 15.5], "look": [22, 16, 15]},
        {"t": 6, "pos": [20, 14, 15.5], "look": [25, 9, 15]}, {"t": 9, "pos": [16, 12, 15.5], "look": [12, 10, 14.5]},
        {"t": 11, "pos": [15, 17, 15.5], "look": [12.5, 19, 14.5]}, {"t": 12.2, "pos": [16.5, 21.6, 15.5], "look": [18, 25, 15]},
        {"t": 12.8, "pos": [16.8, 24, 15.5], "look": [24, 24, 15]}, {"t": 13.4, "pos": [21.4, 24, 15.5], "look": [25, 28, 15]},
        {"t": 14.0, "pos": [24.8, 25.0, 15.5], "look": [25, 32, 15]}, {"t": 14.6, "pos": [25, 27.6, 15.5], "look": [20, 38, 15]},
        {"t": 18, "pos": [19, 36, 15.5], "look": [17, 44, 14.5]}]},
    {"name": "terrace_dusk", "seconds": 12, "dusk": True, "exposure": 0.5, "white_balance_k": 4600, "path": [
        {"t": 0, "pos": [36, 78, 5.5], "look": [12, 46, 6]}, {"t": 5, "pos": [26, 66, 5.5], "look": [10, 46, 5]},
        {"t": 9, "pos": [16, 58, 5.5], "look": [8, 40, 4.5]}, {"t": 12, "pos": [11, 48, 5.5], "look": [2, 38, 4]}]},
    {"name": "bedroom", "seconds": 8, "morning": True, "exposure": 0.3, "white_balance_k": 4200, "path": [
        {"t": 0, "pos": [38.5, 44.0, 5.5], "look": [30.5, 36.5, 3.5]}, {"t": 4, "pos": [36.0, 40.5, 5.5], "look": [29.3, 42.8, 2.6]},
        {"t": 8, "pos": [34.0, 38.0, 5.5], "look": [40.5, 43.0, 4.0]}]},
    {"name": "garage", "seconds": 8, "white_balance_k": 4500, "path": [
        # in through the east door, up the aisle between the sedan and the lift, ending on the roadster and the bench
        {"t": 0, "pos": [12, 97, 5.5], "look": [4, 76, 5]}, {"t": 1.6, "pos": [11.5, 94.5, 5.5], "look": [3, 76, 5.5]},
        {"t": 4, "pos": [9.5, 93.0, 5.5], "look": [0, 74, 5.5]},
        {"t": 8, "pos": [6.5, 92.0, 5.5], "look": [-1.5, 70, 3.0]}]},   # along the door line, ending square on the lift and both cars
]
stills = [
    {"name": "00_block_end", "shot": "block", "t": 10}, {"name": "01_street_end", "shot": "street", "t": 12}, {"name": "02_main_kitchen", "shot": "main_floor", "t": 13},
    {"name": "03_main_living", "shot": "main_floor", "t": 21}, {"name": "04_main_end", "shot": "main_floor", "t": 26},
    {"name": "05_basement_gym", "shot": "basement", "t": 13}, {"name": "06_basement_lounge", "shot": "basement", "t": 22},
    {"name": "07_basement_end", "shot": "basement", "t": 24}, {"name": "08_upstairs_rack", "shot": "upstairs", "t": 11},
    {"name": "09_upstairs_end", "shot": "upstairs", "t": 18}, {"name": "10_terrace_end", "shot": "terrace_dusk", "t": 12},
    {"name": "11_bedroom_end", "shot": "bedroom", "t": 8}, {"name": "12_garage_end", "shot": "garage", "t": 8},
]
views = [
    {"name": "v01_vestibule", "pos": [11, 1, 5.5], "look": [11, 12, 4.5]},
    {"name": "v02_spine_south", "pos": [25, 30, 5.5], "look": [25, 0, 4.5]},
    {"name": "v03_stair_hall", "pos": [24.5, 11.2, 5.5], "look": [32, 3, 4]},
    {"name": "v04_kitchen_nook", "pos": [20, 28, 5.5], "look": [2, 28.5, 3.5]},
    {"name": "v05_living_wide", "pos": [20, 32, 5.5], "look": [3, 42, 4]},
    {"name": "v06_bath", "pos": [29, 21, 5.5], "look": [40, 14, 4]},
    {"name": "v07_closet", "pos": [32, 23, 5.5], "look": [41, 29, 3.5]},
    {"name": "v08_bedroom", "pos": [39, 33, 5.5], "look": [30, 41, 3.5]},
    {"name": "v09_office", "pos": [9, 8, 15.5], "look": [2, 18, 14.5]},
    {"name": "v10_lab", "pos": [21, 21, 15.5], "look": [12, 8, 14.5]},
    {"name": "v11_loft", "pos": [23, 28, 15.5], "look": [16, 44, 14.5]},
    {"name": "v12_bedroom_b", "pos": [29, 45, 15.5], "look": [40, 31, 14]},
    {"name": "v13_gym", "pos": [20, 18, -4.5], "look": [4, 4, -6.5]},
    {"name": "v14_recovery", "pos": [21, 21, -4.5], "look": [4, 25, -6.5]},
    {"name": "v15_lounge", "pos": [20, 44, -4.5], "look": [4, 32, -7.5]},
    {"name": "v16_exterior_front", "pos": [16, -46, 6], "look": [20, 6, 9]},
    {"name": "v17_exterior_rear", "pos": [34, 84, 8], "look": [14, 46, 8]},
    {"name": "v18_garage", "pos": [6, 104, 6], "look": [4, 80, 6]},
    {"name": "v19_block_west", "pos": [-70, -84, 6], "look": [21, -2, 12]},
    {"name": "v20_aerial_block", "pos": [21, -280, 230], "look": [21, 0, 0]},
    {"name": "v21_across", "pos": [21, -95, 5.5], "look": [21, 0, 9]},
    {"name": "v22_street_east", "pos": [130, -56, 5.5], "look": [0, -32, 9]},
]


plan = {
    "units": "feet", "fps": 24, "wall_thickness": 0.5, "slab_thickness": 0.5,
    "materials_file": "materials/materials.json", "source": "housemasterspec.md",
    "floors": floors, "rooms": rooms, "openings": openings, "voids": voids, "stairs": stairs,
    "beams": [{"room": "living", "axis": "x", "positions": [30.5, 34.5, 38.5, 42.5, 45.5], "w_in": 6, "d_in": 12, "m": "walnut", "deck_m": "oak_decking"}],
    "pits": [{"note": "conversation pit", "room": "lounge", "b": [4, 32, 16, 42], "depth": 1.5, "lip": 0.9, "open_side": "north",
              "edge": "walnut_panel", "seat": "velvet_teal", "floor_m": "wool_oatmeal"}],
    "columns": [{"note": "walnut-wrapped column", "b": [7.5, 29.5, 8.5, 30.5, 0, 9.5], "m": "walnut"},
                {"note": "walnut-wrapped column", "b": [19.5, 29.5, 20.5, 30.5, 0, 9.5], "m": "walnut"}],
    "no_baseboard": ["gym", "mechanical", "battery", "storage", "gear_closet", "coat_closet", "panel_closet", "elevator_closet",
                     "elevator_closet2", "litter_closet", "closet_a", "closet_b", "linen", "rack_closet", "garage", "up_laundry", "sauna"],
    "exterior": exterior, "site": site, "lighting": lighting, "camera": camera,
    "sun": {"direction": [0.5, 0.6, -0.62], "strength": 2.0},   # afternoon sun from the south-west: lights the street fronts
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
