"""Main floor + exterior staging entries, room by room from housemasterspec.md sections 1, 2.6, 3.

Coordinates follow plan.json (the audited program): away room X 20-28 Y 30-46, living X 0-20, suite hall X 28-32,
closet X 32-42, WC X 39-42 Y 13-18, shower X 35-42 Y 18-22, mudroom-kitchen door at Y 16-19.
Walls sit inside the room lines (1 ft exterior, 3 in each side of a partition), so boxes against a wall start at the
finished face: X 1 / X 41 / Y 1 / Y 45 on the perimeter, line +/- 0.25 at partitions. Entries that carry a "wall"
spec are shifted to the face automatically by Stager.wall_face (wall_is_face=True disables that)."""

E = []


def add(**kw):
    E.append(kw)
    return kw


def note(t):
    E.append({"note": "== %s ==" % t})


def model(asset, pos, room, **kw):
    d = {"asset": asset, "pos": list(pos), "room": room}
    d.update(kw)
    E.append(d)
    return d


def proc(gen, room=None, **kw):
    d = {"asset": "proc:" + gen}
    if room:
        d["room"] = room
    d.update(kw)
    E.append(d)
    return d


def frames(room, wall, span, count, zc=5.2, seed=1):
    proc("frames", room, wall=wall, span=span, count=count, zc=zc, seed=seed)


def W(axis, at, face):
    return {"axis": axis, "at": at, "face": face}


def main_floor():
    # ------------------------------------------------------------------ 3.1 gear closet (not seen; low detail)
    note("gear closet")
    proc("hooks", "gear_closet", wall=W("x", 6.0, "-y"), span=[1.5, 7.5], z=5.5, count=5, jacket=False)
    proc("stroller", "gear_closet", pos=[3.0, 3.0, 0], rot_z=0)
    proc("bike", "gear_closet", pos=[1.9, 2.2, 0], rot_z=90, wheel_r=0.8, m="teal")
    proc("bike", "gear_closet", pos=[1.9, 4.6, 0], rot_z=90, wheel_r=0.7, m="oxblood")
    proc("shelving_unit", "gear_closet", pos=[6.0, 4.9, 0], length=3.5, depth=1.6, height=7.0, rot_z=0, seed=2)
    # ------------------------------------------------------------------ 3.2 vestibule
    note("vestibule")
    proc("panel_grooves", "vestibule", b=[8.25, 1.0, 8.26, 5.75, 0.3, 9.4], pitch=0.5, width=0.025)
    proc("panel_grooves", "vestibule", b=[13.74, 1.0, 13.75, 5.75, 0.3, 9.4], pitch=0.5, width=0.025)
    proc("globe_pendant", "vestibule", pos=[11.0, 3.4, 8.0], radius=0.58, drop=1.4, watts=40)
    proc("bench", "vestibule", pos=[8.9, 3.3, 0], length=4.0, depth=1.2, height=1.5, rot_z=90, cushion_m="wool_oatmeal")
    proc("hooks", "vestibule", wall=W("y", 8.0, "+x"), span=[1.8, 4.8], z=5.5, count=3, jacket=True)
    proc("runner", "vestibule", b=[9.8, 1.6, 12.8, 5.2], m="rug_oxblood")
    model("rubber_boots", (9.2, 5.3, 0), "vestibule", height_ft=1.1, rot_z=20)
    # ------------------------------------------------------------------ 3.3 powder room
    note("powder")
    proc("wall_finish", "powder", wall=W("x", 6.0, "-y"), span=[14.3, 17.7], z=[0.3, 9.4], m="wallpaper_botanical_dark")
    proc("wall_finish", "powder", wall=W("y", 14.0, "+x"), span=[1.0, 5.75], z=[0.3, 9.4], m="wallpaper_botanical_dark")
    proc("wall_finish", "powder", wall=W("y", 18.0, "-x"), span=[1.0, 5.75], z=[0.3, 9.4], m="wallpaper_botanical_dark")
    proc("wall_vanity", "powder", b=[14.28, 2.1, 15.28, 4.6, 2.6, 3.2], face="+x")
    proc("round_mirror", "powder", wall=W("y", 14.0, "+x"), u=3.35, z=5.5, radius=1.0)
    proc("sconce", "powder", wall=W("y", 14.0, "+x"), u=1.9, z=6.0, watts=6, radius=0.12, height=0.5)
    proc("sconce", "powder", wall=W("y", 14.0, "+x"), u=4.8, z=6.0, watts=6, radius=0.12, height=0.5)
    proc("toilet", "powder", pos=[17.3, 3.3, 0], facing="-x")
    proc("towel_bar", "powder", wall=W("x", 6.0, "-y"), u=15.0, z=4.2, length=1.2, towels=["towel_white"])
    proc("downlight", "powder", pos=[16.0, 3.3, 9.5], watts=6)
    # ------------------------------------------------------------------ 3.4 coat closet / 3.5 panel closet (closed)
    note("coat closet")
    proc("coats", "coat_closet", b=[18.3, 1.0, 21.7, 3.0, 0, 9.0], face="+y", rod_z=6.0, seed=3)
    note("panel closet")
    add(asset="proc:cabinet", room="panel_closet", b=[1.0, 7.5, 1.3, 12.0, 2.0, 7.5], doors=3, face="+x", m="steel_black")
    # ------------------------------------------------------------------ 3.6 entry hall
    note("entry hall")
    proc("console", "entry_hall", pos=[14.5, 12.25, 0], length=5.0, depth=1.0, height=2.7, rot_z=0, items=["lamp", "bowl", "mail"], lamp_base_m="brass")
    proc("wall_frame", "entry_hall", wall=W("x", 13.0, "-y"), u=14.5, zc=5.5, w=3.0, h=2.0, seed=31, frame_m="brass")
    proc("rug", "entry_hall", b=[12.0, 6.6, 18.0, 11.6], m="rug_oxblood", thick=0.05)
    proc("globe_pendant", "entry_hall", pos=[15.0, 9.5, 8.2], radius=0.66, drop=1.2, watts=45)
    model("pachira_aquatica_01", (19.6, 10.3, 0), "entry_hall", height_ft=5.8, rot_z=30)
    proc("downlight", "entry_hall", pos=[11.0, 9.5, 9.5], watts=8)
    proc("downlight", "entry_hall", pos=[19.0, 9.5, 9.5], watts=8)
    # ------------------------------------------------------------------ 3.7 gallery spine
    note("spine")
    proc("runner", "spine", b=[23.25, 3.5, 26.75, 29.0], m="runner")
    proc("window_seat", "spine", b=[22.5, 1.0, 27.5, 3.0, 0, 1.5], face="+y", cushion_m="wool_mustard", pillows=1, pillow_mats=["velvet_teal"], books=2)
    proc("picture_rail", "spine", wall=W("y", 22.0, "+x"), span=[1.2, 29.5], z=9.0)
    proc("picture_rail", "spine", wall=W("y", 28.0, "-x"), span=[1.2, 29.5], z=9.0)
    for y in (5, 11, 17, 23, 29):
        proc("picture_light", "spine", wall=W("y", 22.0, "+x"), u=y, z=8.3, watts=4.5)
    for y in (3, 10, 17, 24, 29):
        proc("picture_light", "spine", wall=W("y", 28.0, "-x"), u=y, z=8.3, watts=4.5)
    frames("spine", W("y", 22.0, "+x"), [1.4, 6.0], 5, zc=5.5, seed=101)
    frames("spine", W("y", 22.0, "+x"), [20.2, 26.2], 7, zc=5.3, seed=102)
    proc("wall_frame", "spine", wall=W("y", 22.0, "+x"), u=28.3, zc=5.5, w=2.5, h=3.33, seed=103, frame_m="brass")
    frames("spine", W("y", 28.0, "-x"), [13.8, 19.5], 4, zc=5.4, seed=104)
    proc("wall_frame", "spine", wall=W("y", 28.0, "-x"), u=22.0, zc=5.5, w=1.3, h=1.6, seed=105)
    proc("console", "spine", pos=[27.25, 22.0, 0], length=4.0, depth=1.0, height=2.7, rot_z=90, items=["lamp", "object"], lamp_base_m="brass")
    model("marble_bust_01", (27.25, 21.0, 2.7), "spine", height_ft=1.1, rot_z=-90)
    proc("downlights", "spine", positions=[[25, 8], [25, 18], [25, 28]], z=9.5, watts=5)
    # ------------------------------------------------------------------ 3.8 stair hall / well
    note("stair hall")
    proc("globe_pendant", "stair_hall", pos=[31.0, 5.0, 14.0], radius=0.83, drop=5.0, watts=70)
    proc("downlight", "stair_hall", pos=[31.0, 11.2, 9.5], watts=8)
    # ------------------------------------------------------------------ 3.9 laundry
    note("laundry")
    proc("washer_dryer", "laundry", b=[39.0, 8.5, 41.0, 11.5, 1.2, 6.8], floor_z=0, face="-x")
    add(asset="proc:cabinet", room="laundry", b=[34.5, 1.0, 41.0, 3.0, 0.3, 2.9], doors=5, face="+y", m="walnut_h")
    add(asset="proc:rug", room="laundry", b=[34.5, 1.0, 41.0, 3.05], z=2.9, thick=0.12, m="walnut_h")   # folding counter top
    proc("utility_sink", "laundry", b=[39.0, 1.0, 41.0, 3.0, 0, 3.05], faucet_wall="+x")
    proc("coats", "laundry", b=[35.0, 1.0, 40.5, 2.1, 6.0, 9.4], face="+y", rod_z=0.5, drawer_h=0.0, seed=6)
    add(asset="proc:cabinet", room="laundry", b=[37.5, 9.5, 39.5, 12.75, 0, 8.0], doors=2, face="-x", m="walnut_h")
    add(asset="proc:cabinet", room="laundry", b=[34.25, 11.0, 36.0, 12.75, 0, 4.0], doors=1, face="-y", m="walnut_h")   # chute hopper
    proc("basket", "laundry", pos=[35.2, 9.8, 0], radius=0.7, height=1.6, throw_m="linen_white")
    proc("rug", "laundry", b=[35.0, 4.0, 38.5, 8.5], m="rug_cream", thick=0.05)
    proc("downlights", "laundry", positions=[[36, 5], [39, 10]], z=9.5, watts=9)
    # ------------------------------------------------------------------ 3.11 mudroom
    note("mudroom")
    proc("lockers2", "mudroom", b=[1.0, 19.25, 7.75, 20.75, 0, 9.5], dividers=[2.7, 4.4, 6.1])
    proc("utility_sink", "mudroom", b=[5.75, 13.25, 7.75, 15.25, 0, 3.0], faucet_wall="+x")
    proc("cat_station", "mudroom", pos=[4.2, 13.9, 0])
    proc("runner", "mudroom", b=[2.2, 14.5, 4.7, 18.8], m="runner")
    proc("sconce", "mudroom", wall=W("y", 0.0, "+x"), u=17.75, z=8.3, watts=10)
    proc("downlights", "mudroom", positions=[[3, 17], [6, 17]], z=9.5, watts=9)
    model("rubber_boots", (2.0, 18.4, 0), "mudroom", height_ft=1.1, rot_z=100)
    # ------------------------------------------------------------------ 3.12 litter closet
    note("litter closet")
    add(asset="proc:cabinet", room="litter_closet", b=[1.1, 13.4, 2.6, 15.0, 0, 1.6], doors=1, face="+x", m="plaster_warm")
    # ------------------------------------------------------------------ 3.13 pantry
    note("pantry")
    proc("pantry_shelves", "pantry", wall=W("x", 27.0, "-y"), span=[1.2, 7.6], z=[1.5, 3.25, 5.0, 6.75, 8.5], depth=0.85, seed=41)
    proc("pantry_shelves", "pantry", wall=W("x", 21.0, "+y"), span=[3.3, 7.6], z=[1.5, 3.25, 5.0, 6.75, 8.5], depth=0.85, seed=42)
    add(asset="proc:cabinet", room="pantry", b=[1.0, 21.5, 3.0, 26.5, 0.3, 3.1], doors=3, face="+x", m="walnut_h")
    add(asset="proc:rug", room="pantry", b=[0.98, 21.45, 3.05, 26.55], z=3.1, thick=0.1, m="soapstone")
    add(asset="proc:cabinet", room="pantry", b=[1.0, 21.5, 3.0, 23.5, 0.3, 2.9], doors=1, face="+x", m="stainless")   # freezer drawer face
    model("vintage_electric_kettle", (1.9, 25.5, 3.2), "pantry", height_ft=0.85, rot_z=40)
    proc("downlights", "pantry", positions=[[3.5, 24], [6.5, 24]], z=9.5, watts=8)
    add(asset="proc:cabinet", room="pantry", b=[1.2, 23.8, 2.2, 24.6, 3.2, 3.9], doors=1, face="+x", m="stainless")   # toaster
    add(asset="proc:cabinet", room="pantry", b=[1.2, 21.8, 2.7, 22.9, 3.2, 4.2], doors=1, face="+x", m="walnut_h")   # bread box
    add(asset="proc:cabinet", room="pantry", b=[1.0, 26.25, 1.3, 26.75, 0, 3.0], doors=1, face="+x", m="walnut_h")   # island leaves slot
    # ------------------------------------------------------------------ 3.14 kitchen
    note("kitchen")
    proc("kitchen2", "kitchen")
    proc("sputnik", "kitchen", pos=[13.75, 23.5, 7.5], arms=18, radius=1.6, ceil_z=9.5, watts=110, seed=11)
    proc("downlights", "kitchen", positions=[[10.5, 17], [10.5, 22], [19.5, 17], [19.5, 24], [15, 28.5]], z=9.5, watts=9)
    model("boombox", (18.3, 14.9, 3.0), "kitchen", length_ft=1.3, rot_z=180)
    model("book_encyclopedia_set_01", (16.2, 14.9, 3.0), "kitchen", length_ft=0.9, rot_z=0)
    model("wooden_cutting_board", (20.5, 14.9, 3.05), "kitchen", length_ft=1.3, rot_z=80)
    model("brass_pot_01", (20.9, 23.7, 3.0), "kitchen", height_ft=0.7)
    # ------------------------------------------------------------------ 3.15 living room (X 0-20; west face at X 1)
    note("living")
    proc("paneled_wall", "living", b=[1.0, 30.5, 1.06, 34.5, 0.0, 9.5], face="+x", m="walnut_panel")
    proc("paneled_wall", "living", b=[1.0, 41.5, 1.06, 45.0, 0.0, 9.5], face="+x", m="walnut_panel")
    add(asset="proc:cabinet", room="living", b=[1.0, 34.5, 1.08, 41.5, 0.0, 9.5], doors=1, face="+x", m="limestone")   # limestone slab
    proc("linear_fire", "living", wall=W("y", 1.08, "+x"), wall_is_face=True, u=38.0, z0=2.2, z1=3.7, width=5.0, watts=45)
    proc("hearth_bench", "living", b=[1.5, 32.0, 3.1, 44.0, 0.0, 1.4], m="limestone")
    proc("builtin_shelves", "living", b=[1.06, 30.6, 2.3, 33.9, 1.6, 8.5], face="+x", shelves=5, seed=51)
    proc("builtin_shelves", "living", b=[1.06, 42.1, 2.3, 44.9, 1.6, 8.5], face="+x", shelves=5, seed=52)
    proc("mushroom_lamp", "living", pos=[2.3, 33.0, 1.4], height=1.6, m="brass", watts=18)
    proc("rug", "living", b=[4.5, 33.5, 16.5, 45.0], m="rug_cream", thick=0.05)
    add(asset="proc:rug", room="living", b=[6.0, 35.0, 11.0, 42.0], m="rug_oxblood", thick=0.09, rot_z=8)
    proc("sofa", "living", pos=[10.5, 40.0, 0], rot_z=90, length=8.0, depth=3.0, m="velvet_orange")
    proc("cushions", "living", b=[10.6, 37.0, 12.2, 43.0], z=1.77, back="+x", count=3, seed=12, mats=["velvet_teal", "velvet_teal", "wool_mustard"])
    proc("throw", "living", b=[9.3, 36.35, 11.6, 37.35], z=2.0, m="wool_oatmeal", hang="-y", drop=1.3)   # throw over the south arm
    model("modern_arm_chair_01", (5.5, 34.5, 0), "living", length_ft=2.9, rot_z=-60, recolor=[0.75, 0.58, 0.16])
    model("modern_arm_chair_01", (5.5, 43.0, 0), "living", length_ft=2.9, rot_z=-120, recolor=[0.75, 0.58, 0.16])
    model("coffee_table_round_01", (7.0, 39.0, 0), "living", length_ft=3.5)
    model("book_encyclopedia_set_01", (6.7, 38.7, 1.32), "living", length_ft=1.1, rot_z=15)
    model("ceramic_vase_02", (7.6, 39.6, 1.32), "living", height_ft=0.55)
    model("brass_candleholders", (6.4, 39.7, 1.32), "living", height_ft=0.5, rot_z=30)
    proc("credenza", "living", pos=[19.0, 33.3, 0], length=5.0, depth=1.5, height=2.4, rot_z=90, turntable=True)
    proc("records", "living", pos=[19.35, 31.1, 2.4], rot_z=90, count=8)
    proc("speaker", "living", pos=[19.15, 35.2, 2.4], rot_z=90, face="-y")
    proc("speaker", "living", pos=[19.15, 31.5, 2.4], rot_z=90, face="-y")
    proc("table_lamp", "living", pos=[19.05, 35.4, 2.4], height=1.8, base_r=0.22, shade_r=0.45, base_m="brass", watts=25)
    proc("tv_wall", "living", wall=W("y", 20.0, "-x"), u=33.0, zc=5.0, w=4.8, h=2.75, on=True, seed=88, watts=8)
    frames("living", W("y", 20.0, "-x"), [30.6, 35.9], 6, zc=6.5, seed=61)
    frames("living", W("y", 20.0, "-x"), [41.2, 44.9], 8, zc=5.3, seed=62)
    proc("picture_light", "living", wall=W("y", 20.0, "-x"), u=33.0, z=8.3, watts=4.5)
    proc("picture_light", "living", wall=W("y", 20.0, "-x"), u=43.3, z=8.3, watts=4.5)
    proc("arc_lamp", "living", pos=[13.8, 43.6, 0], reach=4.9, height=7.3, rot_z=-135, watts=55)
    model("potted_plant_02", (17.8, 43.8, 0), "living", height_ft=6.0, rot_z=20)
    model("calathea_orbifolia_01", (3.0, 44.0, 0), "living", height_ft=4.6, rot_z=50)
    proc("basket", "living", pos=[16.8, 32.0, 0], radius=0.75, height=1.4, throw_m="wool_mustard")
    proc("downlights", "living", positions=[[5, 32.5], [15, 32.5], [5, 36.5], [15, 36.5], [5, 40.5], [15, 40.5], [5, 44], [15, 44]], z=9.5, watts=5)
    proc("roller_shade", "living", span=[3.0, 19.0], at=45.0, inward=-1, top=9.3, drop=0.15)
    # ------------------------------------------------------------------ 3.16 away room (X 20-28, Y 30-46)
    note("away room")
    proc("wall_finish", "away", wall=W("y", 28.0, "-x"), span=[30.3, 45.0], z=[0.3, 9.4], m="wallpaper_geo_olive")
    proc("wall_finish", "away", wall=W("y", 20.0, "+x"), span=[30.3, 35.7], z=[0.3, 9.4], m="wallpaper_geo_olive")
    proc("wall_finish", "away", wall=W("y", 20.0, "+x"), span=[41.3, 45.0], z=[0.3, 9.4], m="wallpaper_geo_olive")
    proc("wall_finish", "away", wall=W("x", 30.0, "+y"), span=[20.3, 23.0], z=[0.3, 9.4], m="wallpaper_geo_olive")
    proc("wall_finish", "away", wall=W("x", 30.0, "+y"), span=[27.0, 27.7], z=[0.3, 9.4], m="wallpaper_geo_olive")
    model("mid_century_lounge_chair", (25.0, 42.8, 0), "away", length_ft=2.9, rot_z=180)
    model("ottoman_01", (25.0, 40.3, 0), "away", length_ft=2.1, rot_z=180, recolor=[0.3, 0.18, 0.1])
    proc("mushroom_lamp", "away", pos=[26.8, 43.9, 0], height=5.0, m="brass", watts=38)
    proc("bookwall", "away", b=[26.75, 30.6, 27.75, 44.9, 0.0, 9.0], face="-x", seed=7, density=0.92, shelf_ft=1.2)
    model("side_table_01", (23.4, 42.8, 0), "away", height_ft=1.9)
    model("book_encyclopedia_set_01", (23.4, 42.9, 1.9), "away", length_ft=0.8, rot_z=200)
    proc("rug", "away", b=[22.3, 34.5, 26.5, 42.5], m="rug_cream", thick=0.05)
    add(asset="proc:rug", room="away", b=[23.2, 39.3, 26.0, 44.3], m="rug_teal", thick=0.08, rot_z=-4)
    proc("scratching_post", "away", pos=[21.3, 31.7, 0], height=3.0)
    add(asset="proc:cabinet", room="away", b=[22.5, 44.2, 27.5, 45.0, 0, 2.5], doors=3, face="-y", m="walnut_h")
    model("ceramic_vase_03", (23.6, 44.6, 2.5), "away", height_ft=0.9)
    model("brass_vase_01", (26.4, 44.6, 2.5), "away", height_ft=0.6)
    proc("wall_frame", "away", wall=W("y", 20.0, "+x"), u=33.0, zc=5.5, w=2.0, h=3.0, seed=71)
    proc("downlights", "away", positions=[[24, 35], [24, 42]], z=9.5, watts=4)
    # ------------------------------------------------------------------ 3.17 primary bath
    note("primary bath")
    proc("vanity2", "primary_bath", wall=W("y", 28.0, "+x"), span=[13.6, 21.5], top_z=2.9, depth=1.8, sinks=[15.6, 19.5],
         sconces=[13.9, 21.2], sconce_z=6.0, mirror_z=[3.6, 7.5], glow_watts=20)
    proc("shower2", "primary_bath", b=[35.0, 18.0, 41.0, 21.75], glass=[["-x", 18.0, 21.0]], head_wall="+y", heads=[36.8, 39.6],
         niche=[38.0, 39.3, 3.5, 4.8], bench=[39.4, 18.2, 41.0, 19.6, 0, 1.5])
    proc("tile_wainscot", "primary_bath", boxes=[[35.0, 21.72, 41.0, 21.75, 0, 9.5], [40.97, 18.0, 41.0, 21.75, 0, 9.5]], m="terrazzo")
    proc("toilet", "wc", pos=[40.55, 15.5, 0], facing="-x")
    proc("downlight", "wc", pos=[40.2, 15.5, 9.5], watts=4)
    proc("towel_bar", "wc", wall=W("x", 13.0, "+y"), u=40.2, z=3.2, length=0.8, towels=["towel_white"])
    proc("towel_warmer", "primary_bath", wall=W("x", 13.0, "+y"), u=33.0, z=3.5)
    model("wooden_stool_01", (31.5, 20.5, 0), "primary_bath", height_ft=1.5, rot_z=20)
    model("potted_plant_04", (33.0, 21.0, 0), "primary_bath", height_ft=2.2)
    proc("towel_bar", "primary_bath", wall=W("x", 13.0, "+y"), u=30.5, z=4.0, length=2.0, towels=["towel_white", "towel_white"])
    proc("downlights", "primary_bath", positions=[[38.5, 20], [33, 17], [30, 15]], z=9.5, watts=8)
    # ------------------------------------------------------------------ 3.18 suite hall (X 28-32)
    note("suite hall")
    proc("runner", "suite_hall", b=[28.8, 22.8, 31.2, 29.3], m="runner")
    proc("wall_frame", "suite_hall", wall=W("y", 28.0, "+x"), u=24.5, zc=5.5, w=2.0, h=2.5, seed=81)
    proc("picture_light", "suite_hall", wall=W("y", 28.0, "+x"), u=24.5, z=8.3, watts=8)
    proc("downlight", "suite_hall", pos=[30.0, 26.0, 9.5], watts=7)
    # ------------------------------------------------------------------ 3.19 primary closet (X 32-42)
    note("primary closet")
    proc("wall_finish", "primary_closet", wall=W("y", 32.0, "+x"), span=[22.3, 29.7], z=[0.3, 9.4], m="walnut_panel")
    proc("wardrobe", "primary_closet", b=[32.5, 28.15, 34.5, 29.75, 0, 9.4], face="-y", kind="hanging", drawer_h=3.0, rod_z=6.5, seed=91)
    proc("wardrobe", "primary_closet", b=[37.5, 28.15, 41.0, 29.75, 0, 9.4], face="-y", kind="hanging", drawer_h=3.0, rod_z=6.5, seed=92)
    proc("wardrobe", "primary_closet", b=[32.5, 22.25, 35.0, 23.85, 0, 9.4], face="+y", kind="bins", count=3, seed=93)
    proc("wardrobe", "primary_closet", b=[39.0, 22.25, 41.0, 23.85, 0, 9.4], face="+y", kind="shelves", shelves=6, seed=94)
    proc("wardrobe", "primary_closet", b=[39.4, 24.0, 41.0, 28.0, 0, 4.0], face="-x", kind="drawers", count=4, seed=95)
    proc("watch_island", "primary_closet", b=[34.5, 25.0, 38.5, 27.0, 0, 3.0])
    proc("wall_finish", "primary_closet", wall=W("y", 32.0, "+x"), span=[27.0, 29.5], z=[0.3, 8.5], m="mirror", thick=0.04)
    add(asset="proc:cabinet", room="primary_closet", b=[39.5, 28.0, 41.0, 29.75, 0, 2.5], doors=1, face="-x", m="walnut_h")   # safe cabinet door
    proc("three_globe_pendant", "primary_closet", pos=[36.5, 26.0, 9.5])
    proc("downlights", "primary_closet", positions=[[33.5, 23], [39.5, 23], [33.5, 29], [39.5, 29]], z=9.5, watts=11)
    model("vintage_suitcase", (33.5, 23.0, 7.0), "primary_closet", length_ft=2.2, rot_z=0)
    # ------------------------------------------------------------------ 3.20 primary bedroom
    note("primary bedroom")
    # headboard on the west wall: the spec's south wall carries the two suite doors, so the bed turns to face the
    # east window and the catio; nightstands north and south of it
    proc("wall_finish", "primary_bedroom", wall=W("y", 28.0, "+x"), span=[30.3, 45.0], z=[0.3, 9.4], m="wallpaper_geo_muted")
    proc("platform_bed", "primary_bedroom", pos=[31.85, 38.0, 0], width=6.5, length=7.0, rot_z=90, platform_h=1.0, mattress_top=2.0,
         headboard_w=9.0, headboard_h=4.0, duvet="thrown", blanket_m="velvet_orange", pillow_mats=["linen_white", "linen_white", "olive_paint", "olive_paint"], seed=8)
    proc("nightstand2", "primary_bedroom", pos=[29.05, 33.4, 0], rot_z=90, on=False, items=["books", "glass"])
    proc("nightstand2", "primary_bedroom", pos=[29.05, 42.6, 0], rot_z=90, on=True, items=["watch", "phone"])
    proc("sconce", "primary_bedroom", wall=W("y", 28.0, "+x"), u=33.4, z=5.2, on=False, radius=0.12, height=0.5)
    proc("sconce", "primary_bedroom", wall=W("y", 28.0, "+x"), u=42.6, z=5.2, on=False, radius=0.12, height=0.5)
    model("green_chair_01", (39.6, 43.4, 0), "primary_bedroom", length_ft=2.8, rot_z=210, recolor=[0.08, 0.32, 0.36])
    proc("throw", "primary_bedroom", b=[38.7, 42.4, 39.6, 43.6], z=2.0, m="wool_oatmeal", rot_z=25, hang="-x", drop=0.9)   # sweater over the arm
    model("side_table_01", (38.0, 44.2, 0), "primary_bedroom", height_ft=1.9)
    model("jug_01", (38.0, 44.2, 1.9), "primary_bedroom", height_ft=0.35)
    proc("floor_lamp", "primary_bedroom", pos=[40.3, 44.3, 0], height=5.2, on=False, kind="drum")
    proc("rug", "primary_bedroom", b=[33.5, 33.5, 40.0, 42.5], m="rug_oxblood", thick=0.05)
    proc("bench", "primary_bedroom", pos=[36.2, 38.0, 0], length=5.0, depth=1.5, height=1.5, rot_z=90, cushion_m="wool_oatmeal")
    model("potted_plant_02", (33.0, 44.0, 0), "primary_bedroom", height_ft=6.0, rot_z=70)
    proc("slippers", "primary_bedroom", pos=[31.5, 34.2, 0], rot_z=110)
    proc("slippers", "primary_bedroom", pos=[37.5, 41.5, 0], rot_z=-70)
    proc("wall_frame", "primary_bedroom", wall=W("x", 46.0, "-y"), u=30.2, zc=5.5, w=2.5, h=3.5, seed=111, frame_m="brass")
    proc("wall_frame", "primary_bedroom", wall=W("x", 30.0, "+y"), u=35.0, zc=5.5, w=1.2, h=1.5, seed=112)
    proc("wall_frame", "primary_bedroom", wall=W("x", 30.0, "+y"), u=39.5, zc=5.5, w=1.2, h=1.5, seed=113)
    proc("downlights", "primary_bedroom", positions=[[31, 44], [39, 44]], z=9.5, watts=3)
    proc("roller_shade", "primary_bedroom", span=[32.0, 40.0], at=45.0, inward=-1, top=9.3, drop=2.6)


def exterior():
    note("porch")
    proc("porch_bench", "vestibule", b=[14.0, -1.5, 22.0, 0.0, 0.0, 1.5])
    model("ceiling_fan", (13.0, -3.5, 9.5), "vestibule", length_ft=4.3)
    proc("ext_sconce", "vestibule", wall=W("x", 0.0, "-y"), wall_is_face=True, u=13.5, z=6.5, watts=22)
    # porch canopy underside (Z 10.0): three warm downlights so the recessed door is not a black hole by day
    for x in (7.0, 13.0, 19.0):
        proc("soffit_downlight", "vestibule", pos=[x, -4.0, 9.95], watts=14, angle=50, kelvin=3000)
    proc("house_numbers", "vestibule", wall=W("x", 0.0, "-y"), wall_is_face=True, u=16.0, z=5.5, height=0.5, text="1956")
    proc("mail_slot", "vestibule", wall=W("x", 0.0, "-y"), wall_is_face=True, u=8.5, z=3.5)
    model("planter_pot_clay", (5.0, -1.0, -0.2), "vestibule", height_ft=1.6)
    model("potted_plant_01", (5.0, -1.0, 1.2), "vestibule", height_ft=2.6)
    for x in (4, 12, 20, 28, 36):
        proc("soffit_downlight", "vestibule", pos=[x, 3.2, 18.45], watts=10, angle=45)
    note("terrace")
    proc("grill", "living", b=[23.5, 47.0, 27.5, 49.2, 2.7, 3.7])
    model("outdoor_table_chair_set_01", (12.0, 52.0, -0.3), "living", length_ft=7.5, rot_z=0)
    proc("heater", "living", pos=[8.0, 49.5, 10.1], length=3.0, on=True, watts=20)
    proc("heater", "living", pos=[18.0, 49.5, 10.1], length=3.0, on=True, watts=20)
    proc("planter", "living", pos=[5.0, 56.5, -0.3], w=2.2, d=2.2, height=3.5, seed=5)
    proc("planter", "living", pos=[21.0, 56.5, -0.3], w=2.2, d=2.2, height=3.2, seed=6)
    proc("spa_cover", "living", b=[30.0, 50.0, 37.5, 64.0, 1.2])
    proc("rain_chain", "living", pos=[2.0, 50.0, 18.4], drop=18.6)
    proc("rain_chain", "living", pos=[44.0, 50.0, 18.4], drop=18.6)
    note("garage exterior")
    for x in (-5.5, 6.0, 17.5):
        proc("ext_sconce", "garage", wall=W("x", 94.0, "+y"), wall_is_face=True, u=x, z=9.5, watts=14)
    proc("house_numbers", "garage", wall=W("x", 94.0, "+y"), wall_is_face=True, u=17.0, z=7.0, height=0.4, text="1956")
    add(asset="proc:cabinet", room="garage", b=[17.2, 93.98, 17.9, 94.0, 2.7, 3.4], doors=1, face="+y", m="brass")   # utility inlet plate
