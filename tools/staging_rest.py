"""Second floor, basement and garage staging entries from housemasterspec.md sections 4, 5, 7.
Boxes against walls start at the finished face (perimeter: 1 ft inside the line; partitions: 3 in)."""
from staging_main import add, note, model, proc, frames, W

Z2 = 10.0      # second floor
ZB = -10.0     # basement floor
ZG = -0.4      # garage slab


def second_floor():
    z = Z2
    # ------------------------------------------------------------------ 4.1 her office (west face X 1, north partition face 25.75)
    note("her office")
    proc("wall_finish", "her_office", wall=W("y", 11.0, "-x"), span=[6.3, 25.7], z=[z + 0.3, z + 8.9], m="teal_paint")
    proc("desk", "her_office", b=[1.0, 9.0, 3.7, 24.0, z + 2.4, z + 2.5], floor_z=z, gables=True, drawers=False, facing="-x",
         monitors=0, keyboard=False, laptop=[2.5, 16.0], lamp=[2.9, 12.0], mug=[3.1, 18.5], notebook=[2.7, 19.6])
    # six 24 in monitors, 3 x 2, on a black rail centred on the pier between W3 and W4 (Y 16.5), arms off the rail
    for i, yy in enumerate((14.4, 16.5, 18.6)):
        for k, zz in enumerate((z + 3.35, z + 4.7)):
            proc("monitor", "her_office", pos=[1.55, yy, zz], facing="+x", w=2.0, mount="wall", mount_d=0.43, m="screen_code" if (i + k) % 2 else "screen_dash")
    add(asset="proc:cabinet", room="her_office", b=[1.0, 13.2, 1.12, 19.8, z + 4.6, z + 4.72], doors=1, face="+x", m="steel_black")   # rail
    model("classic_laptop", (2.5, 16.0, z + 2.5), "her_office", length_ft=1.2, rot_z=90)
    proc("task_chair", "her_office", pos=[5.0, 16.5, z], rot_z=90, m="leather_brown")
    proc("lounge_chair", "her_office", pos=[7.5, 9.5, z], rot_z=225, m="wool_mustard")
    proc("floor_lamp", "her_office", pos=[9.9, 7.8, z], height=5.4, on=True, kind="drum")
    model("side_table_01", (9.2, 12.0, z), "her_office", height_ft=1.9)
    model("binder_notebook", (8.8, 11.6, z + 1.9), "her_office", length_ft=0.9, rot_z=30)
    proc("bookwall", "her_office", b=[1.0, 24.85, 10.5, 25.75, z + 3.0, z + 8.5], face="-y", seed=17, density=0.75, shelf_ft=1.3)
    add(asset="proc:cabinet", room="her_office", b=[1.0, 24.6, 10.5, 25.75, z, z + 2.4], doors=4, face="-y", m="walnut_h")
    add(asset="proc:cabinet", room="her_office", b=[2.0, 24.8, 3.6, 25.7, z + 2.4, z + 3.0], doors=1, face="-y", m="stainless")   # printer
    model("mantel_clock_01", (6.0, 25.2, z + 3.06), "her_office", height_ft=0.6)
    proc("plant", "her_office", pos=[9.9, 19.6, z], kind="bop", height=5.5, rot_z=180, seed=7)   # spec: a tall bird of paradise against the teal wall
    proc("wall_frame", "her_office", wall=W("y", 11.0, "-x"), u=16.5, zc=z + 5.5, w=4.0, h=3.0, seed=121, frame_m="brass")
    proc("wall_frame", "her_office", wall=W("y", 11.0, "-x"), u=12.0, zc=z + 5.0, w=1.5, h=1.8, seed=122)
    proc("wall_frame", "her_office", wall=W("y", 11.0, "-x"), u=21.0, zc=z + 5.0, w=1.5, h=1.8, seed=123)
    proc("rug", "her_office", b=[4.0, 12.0, 9.0, 21.0], m="rug_oxblood", thick=0.05)
    proc("led_strip", "her_office", b=[1.0, 9.5, 1.1, 23.5, z + 8.5, z + 8.53], watts=10, rot=[0, 90, 0])
    proc("downlights", "her_office", positions=[[5.5, 11], [5.5, 21]], z=z + 9.0, watts=7)
    # ------------------------------------------------------------------ 4.2 work corridor
    note("work corridor")
    proc("runner", "work_corridor", b=[12.0, 22.75, 20.5, 25.25], m="runner")
    proc("wall_frame", "work_corridor", wall=W("x", 26.0, "-y"), u=14.0, zc=z + 5.5, w=1.8, h=2.2, seed=131)
    proc("wall_frame", "work_corridor", wall=W("x", 26.0, "-y"), u=19.0, zc=z + 5.5, w=1.8, h=2.2, seed=132)
    proc("picture_light", "work_corridor", wall=W("x", 26.0, "-y"), u=16.5, z=z + 8.3, watts=8)
    proc("downlight", "work_corridor", pos=[16.5, 24.0, z + 9.0], watts=7)
    # ------------------------------------------------------------------ 4.3 lab
    note("lab")
    proc("wall_finish", "lab", wall=W("x", 22.0, "-y"), span=[11.3, 21.7], z=[z + 0.3, z + 8.9], m="teal_paint")
    proc("wall_finish", "lab", wall=W("x", 13.0, "-y"), span=[22.3, 27.7], z=[z + 0.3, z + 8.9], m="teal_paint")
    proc("desk", "lab", b=[22.5, 8.0, 27.5, 10.5, z + 2.4, z + 2.5], floor_z=z, gables=True, drawers=True, facing="-y",
         monitors=2, monitor_w=2.7, keyboard=True, laptop=[26.6, 9.6], lamp=[23.2, 9.8], mug=[23.6, 8.6])
    proc("task_chair", "lab", pos=[25.0, 11.5, z], rot_z=180, m="leather_brown")
    add(asset="proc:cabinet", room="lab", b=[23.0, 12.45, 27.0, 12.75, z + 4.95, z + 5.05], doors=1, face="-y", m="walnut_h")   # shelf on the teal wall
    model("security_camera_01", (23.6, 12.6, z + 5.05), "lab", length_ft=0.6, rot_z=180)
    model("potted_plant_01", (24.6, 12.6, z + 5.05), "lab", height_ft=0.9)
    model("book_encyclopedia_set_01", (25.9, 12.6, z + 5.05), "lab", length_ft=0.8)
    proc("wall_frame", "lab", wall=W("x", 13.0, "-y"), u=25.0, zc=z + 5.8, w=0.67, h=0.83, seed=140, frame_m="black")   # the dad print
    proc("workbench", "lab", b=[11.25, 7.0, 13.75, 15.7, z, z + 3.0], wall=W("y", 11.0, "+x"), cleat_z=[z + 3.5, z + 7.5], cleat_span=[7.0, 15.6], tools=12,
         items=[{"kind": "lamp", "pos": [12.3, 8.0], "rot_z": 0}, {"kind": "lamp", "pos": [12.3, 14.0], "rot_z": 0}, {"kind": "mat", "pos": [12.5, 10.5], "w": 2.0, "d": 3.0},
                {"kind": "printer", "pos": [12.5, 14.6], "face": "+x"}, {"kind": "soldering", "pos": [12.9, 12.8]}, {"kind": "psu", "pos": [12.4, 9.0]},
                {"kind": "microscope", "pos": [12.6, 12.0]}, {"kind": "organizer", "pos": [12.0, 7.5], "z": 0.5}, {"kind": "spools", "pos": [11.8, 13.2]},
                {"kind": "hood", "pos": [12.5, 14.7], "z": 2.0, "duct_h": 4.0}])
    proc("rack", "rack_closet", b=[11.5, 17.0, 13.5, 20.0, z, z + 6.5], face="+x")
    proc("downlight", "rack_closet", pos=[12.5, 21.0, z + 9.0], watts=5, kelvin=4000)
    add(asset="proc:cabinet", room="lab", b=[20.75, 18.6, 21.75, 21.5, z, z + 8.0], doors=2, face="-x", m="walnut_h")   # north of the landing door (Y 14.5-17.5)
    proc("rug", "lab", b=[14.5, 9.5, 19.5, 14.5], m="rug_teal", thick=0.05)
    model("metal_stool_01", (14.5, 11.5, z), "lab", height_ft=2.0, rot_z=30)   # at the workbench
    # real tools on the cleat wall (thin axis turned into the wall) and on the bench top
    model("pliers", (11.14, 9.6, z + 5.3), "lab", height_ft=0.6, rot_z=90)
    model("adjustable_wrench", (11.15, 10.5, z + 5.0), "lab", height_ft=0.85, rot_z=90)
    model("metal_toolbox", (12.7, 7.7, z + 3.0), "lab", length_ft=1.3, rot_z=90)
    model("screwdrivers_02", (13.1, 10.1, z + 3.0), "lab", length_ft=0.9, rot_z=70)
    model("measuring_tape_01", (12.2, 13.9, z + 3.0), "lab", length_ft=0.55, rot_z=20)
    model("lubricant_spray", (13.3, 13.5, z + 3.0), "lab", height_ft=0.55)
    model("clipboard", (12.6, 11.4, z + 3.05), "lab", length_ft=1.1, rot_z=8)
    model("round_wooden_table_01", (17.5, 18.0, z), "lab", length_ft=2.4)
    model("decorative_book_set_01", (17.5, 18.0, z + 2.35), "lab", length_ft=0.9, rot_z=20, fallback="book_encyclopedia_set_01")
    proc("led_strip", "lab", b=[11.35, 7.0, 11.45, 16.0, z + 7.6, z + 7.63], watts=10, rot=[0, 90, 0])
    proc("sconce", "lab", wall=W("x", 22.0, "-y"), u=15.0, z=z + 7.5, watts=3, radius=0.1, height=0.3)
    proc("downlights", "lab", positions=[[16, 9], [16, 19], [25, 8], [19, 14]], z=z + 9.0, watts=8)
    # ------------------------------------------------------------------ 4.4 landing (east face X 41)
    note("landing")
    proc("window_seat", "landing", b=[39.5, 14.75, 41.0, 17.5, z, z + 1.5], face="-x", cushion_m="wool_oatmeal", pillows=1, pillow_mats=["oxblood"], books=1)
    proc("runner", "landing", b=[24.0, 14.5, 38.5, 17.5], m="runner")
    for x in (30, 34, 38):
        proc("wall_frame", "landing", wall=W("x", 19.0, "-y"), u=x, zc=z + 5.5, w=1.8, h=2.2, seed=150 + x)
    proc("picture_light", "landing", wall=W("x", 19.0, "-y"), u=32.0, z=z + 8.3, watts=8)
    proc("picture_light", "landing", wall=W("x", 19.0, "-y"), u=38.0, z=z + 8.3, watts=8)
    proc("downlights", "landing", positions=[[26, 16], [38, 16]], z=z + 9.0, watts=7)
    # ------------------------------------------------------------------ 4.5 upstairs laundry closet
    note("upstairs laundry closet")
    add(asset="proc:cabinet", room="up_laundry", b=[39.5, 11.6, 41.0, 12.75, z, z + 4.0], doors=1, face="-y", m="walnut_h")
    proc("downlights", "up_laundry", positions=[[38.0, 11.0], [39.5, 7.5]], z=z + 9.0, watts=10)
    proc("wardrobe", "up_laundry", b=[38.0, 9.4, 41.0, 11.0, z, z + 8.5], face="+y", kind="shelves", shelves=5, seed=161)
    # ------------------------------------------------------------------ 4.6 hall
    note("hall")
    proc("runner", "hall_south", b=[23.5, 20.0, 26.5, 25.5], m="runner")
    proc("runner", "hall", b=[23.5, 27.0, 26.5, 44.0], m="runner")
    proc("low_bookcase", "hall", b=[26.75, 42.0, 27.75, 44.9, z, z + 3.0], back="+x", shelves=2, seed=171)
    proc("wall_frame", "hall", wall=W("y", 28.0, "-x"), u=30.0, zc=z + 5.5, w=3.5, h=2.6, seed=172, frame_m="walnut_h")
    proc("picture_light", "hall", wall=W("y", 28.0, "-x"), u=30.0, z=z + 8.3, watts=8)
    proc("picture_light", "hall", wall=W("y", 28.0, "-x"), u=43.5, z=z + 8.3, watts=6)
    proc("downlights", "hall", positions=[[25, 22], [25, 30], [25, 38]], z=z + 9.0, watts=7)
    # ------------------------------------------------------------------ 4.7 kid bath (partition faces 28.25 / 27.75 / 19.25 / 35.25; east face X 41)
    note("kid bath")
    proc("wall_finish", "kid_bath_sink", wall=W("y", 28.0, "+x"), span=[19.3, 27.7], z=[z, z + 4.0], m="tile_white")
    proc("wall_finish", "kid_bath_sink", wall=W("x", 28.0, "-y"), span=[28.3, 34.7], z=[z, z + 4.0], m="tile_white")
    proc("wall_finish", "kid_bath_sink", wall=W("x", 19.0, "+y"), span=[28.3, 34.7], z=[z, z + 4.0], m="tile_white")
    proc("wall_finish", "kid_bath_sink", wall=W("x", 28.0, "-y"), span=[28.3, 34.7], z=[z + 4.0, z + 8.9], m="mustard_paint")
    proc("vanity2", "kid_bath_sink", wall=W("x", 28.0, "-y"), span=[29.0, 34.7], top_z=z + 2.5, depth=1.5, sinks=[30.4, 33.3],
         sconces=[29.5, 34.2], sconce_z=z + 6.0, mirror_z=[z + 3.3, z + 6.6], glow_watts=12, top_m="marble_white")
    model("wooden_stool_01", (29.4, 26.6, z), "kid_bath_sink", height_ft=1.0)   # step stool beside the vanity
    proc("towel_bar", "kid_bath_sink", wall=W("x", 19.0, "+y"), u=31.5, z=z + 3.8, length=2.5, towels=["towel_white", "wool_mustard"])
    proc("basket", "kid_bath_sink", pos=[29.0, 20.0, z], radius=0.6, height=2.0, throw_m="linen_white")
    proc("wall_finish", "kid_bath_tub", wall=W("x", 28.0, "-y"), span=[35.3, 41.0], z=[z, z + 7.0], m="tile_white")
    proc("wall_finish", "kid_bath_tub", wall=W("y", 35.0, "+x"), span=[25.5, 27.7], z=[z, z + 7.0], m="tile_white")
    proc("wall_finish", "kid_bath_tub", wall=W("y", 42.0, "-x"), span=[25.5, 27.7], z=[z, z + 7.0], m="tile_white")
    proc("tub", "kid_bath_tub", b=[35.5, 25.5, 41.0, 27.75, z, z + 1.6])
    proc("toilet", "kid_bath_tub", pos=[38.5, 19.7, z], facing="+y")
    model("rubber_duck_toy", (40.5, 25.7, z + 1.6), "kid_bath_tub", length_ft=0.35, rot_z=40)
    add(asset="proc:cabinet", room="kid_bath_tub", b=[36.0, 27.4, 36.3, 27.7, z + 1.6, z + 2.3], doors=1, face="-y", m="teal")   # shampoo bottle
    proc("downlights", "kid_bath_tub", positions=[[38.5, 26.5], [38.5, 21]], z=z + 9.0, watts=8)
    proc("downlights", "kid_bath_sink", positions=[[31.5, 22]], z=z + 9.0, watts=8)
    # ------------------------------------------------------------------ 4.8 bedroom B (east face X 41, north face Y 45)
    note("bedroom B")
    proc("wall_finish", "bedroom_b", wall=W("x", 46.0, "-y"), span=[28.3, 41.0], z=[z + 0.3, z + 8.9], m="wallpaper_kid_teal")
    proc("kid_bed", "bedroom_b", b=[37.7, 29.0, 40.9, 36.0, z, z + 1.6], head="-y", duvet_m="bedding_stripe_teal", seed=5)
    proc("nightstand2", "bedroom_b", pos=[36.45, 29.6, z], rot_z=0, on=True, items=[])
    model("alarm_clock_01", (36.4, 29.3, z + 2.2), "bedroom_b", height_ft=0.35, rot_z=200)
    proc("desk", "bedroom_b", b=[32.0, 28.3, 35.3, 30.3, z + 2.3, z + 2.4], floor_z=z, gables=True, drawers=True, facing="-y", monitors=0, keyboard=False,
         laptop=[33.5, 29.5], lamp=[34.5, 29.6], mug=[32.5, 29.9], mug_m="teal")
    proc("corkboard", "bedroom_b", wall=W("x", 28.0, "+y"), span=[32.2, 35.8], z=[z + 4.0, z + 6.5], papers=8, seed=181)
    model("schoolchair_01", (34.0, 31.5, z), "bedroom_b", height_ft=2.6, rot_z=0)   # faces the desk (-Y)
    proc("low_bookcase", "bedroom_b", b=[33.0, 44.0, 41.0, 45.0, z, z + 2.5], back="+y", shelves=2, seed=182)
    proc("rug", "bedroom_b", b=[31.0, 37.5, 38.0, 44.0], m="rug_teal", thick=0.05)
    proc("toy_chest", "bedroom_b", b=[29.0, 43.0, 31.5, 45.0, z, z + 1.8])
    model("american_football", (30.5, 41.0, z), "bedroom_b", length_ft=0.9, rot_z=30)
    proc("wall_frame", "bedroom_b", wall=W("y", 42.0, "-x"), u=32.5, zc=z + 5.5, w=2.0, h=1.6, seed=183)
    proc("sconce", "bedroom_b", wall=W("y", 42.0, "-x"), u=32.0, z=z + 4.5, watts=6, radius=0.1, height=0.4)
    proc("downlight", "bedroom_b", pos=[35.0, 41.0, z + 9.0], watts=8)
    proc("roller_shade", "bedroom_b", span=[34.0, 40.0], at=45.0, inward=-1, top=z + 8.8, drop=3.0)
    proc("coats", "closet_b", b=[28.25, 28.25, 30.75, 32.75, z, z + 8.5], face="+x", rod_z=4.5, drawer_h=0.0, seed=184)
    proc("wardrobe", "linen", b=[28.25, 33.25, 30.75, 36.75, z, z + 8.5], face="-x", kind="shelves", shelves=5, seed=185)
    proc("coats", "closet_a", b=[11.25, 26.25, 13.75, 30.75, z, z + 8.5], face="-x", rod_z=4.5, drawer_h=0.0, seed=186)
    # ------------------------------------------------------------------ 4.9 bedroom A (west face X 1)
    note("bedroom A")
    proc("wall_finish", "bedroom_a", wall=W("y", 0.0, "+x"), span=[26.3, 39.7], z=[z + 0.3, z + 8.9], m="wallpaper_kid_botanical")
    proc("kid_bed", "bedroom_a", b=[4.0, 36.55, 11.0, 39.55, z, z + 1.6], head="-x", duvet_m="bedding_stripe_mustard", seed=6)
    proc("nightstand2", "bedroom_a", pos=[2.3, 38.5, z], rot_z=0, on=True, items=[])
    proc("desk", "bedroom_a", b=[1.0, 26.3, 6.0, 28.3, z + 2.3, z + 2.4], floor_z=z, gables=True, drawers=True, facing="-y", monitors=0, keyboard=False,
         lamp=[1.7, 27.6], notebook=[3.5, 27.4])
    model("book_encyclopedia_set_01", (5.2, 27.6, z + 2.4), "bedroom_a", length_ft=0.9, rot_z=0)
    proc("corkboard", "bedroom_a", wall=W("x", 26.0, "+y"), span=[1.2, 5.8], z=[z + 4.0, z + 6.5], papers=7, seed=191)
    model("schoolchair_01", (3.5, 29.5, z), "bedroom_a", height_ft=2.6, rot_z=0)   # faces the desk (-Y)
    proc("low_bookcase", "bedroom_a", b=[1.0, 35.5, 4.0, 36.5, z, z + 3.0], back="-x", shelves=2, seed=192)
    proc("rug", "bedroom_a", b=[4.0, 30.0, 11.0, 36.5], m="rug_stripe_mustard", thick=0.05)
    proc("beanbag", "bedroom_a", pos=[8.0, 30.5, z], m="velvet_teal")
    proc("basket", "bedroom_a", pos=[12.5, 34.0, z], radius=0.7, height=1.3, throw_m="oxblood")
    model("baseball_01", (7.5, 33.0, z), "bedroom_a", length_ft=0.25)
    proc("wall_frame", "bedroom_a", wall=W("x", 26.0, "+y"), u=9.0, zc=z + 5.5, w=1.6, h=2.0, seed=193)
    proc("sconce", "bedroom_a", wall=W("y", 0.0, "+x"), u=38.5, z=z + 4.5, watts=6, radius=0.1, height=0.4)
    proc("downlight", "bedroom_a", pos=[7.0, 34.0, z + 9.0], watts=8)
    # ------------------------------------------------------------------ 4.10 hedge alcove (faces X 1, Y 45)
    note("hedge alcove")
    proc("daybed", "hedge_alcove", b=[1.0, 43.0, 8.0, 45.0, z, z + 1.5], cushion_m="olive_paint", pillows=5, seed=201)
    proc("low_bookcase", "hedge_alcove", b=[1.0, 40.3, 4.0, 41.0, z, z + 3.0], back="-y", shelves=2, seed=202)
    proc("sconce", "hedge_alcove", wall=W("x", 46.0, "-y"), u=4.0, z=z + 4.5, watts=8, radius=0.14, height=0.5)
    proc("rug", "hedge_alcove", b=[3.0, 41.3, 12.0, 43.0], m="rug_cream", thick=0.05)
    proc("basket", "hedge_alcove", pos=[10.0, 44.2, z], radius=0.8, height=1.3, throw_m="wool_mustard")
    # ------------------------------------------------------------------ 4.11 loft (west partition face 14.25, north face Y 45)
    note("loft")
    proc("wall_finish", "loft", wall=W("y", 14.0, "+x"), span=[26.3, 40.0], z=[z + 0.3, z + 8.9], m="mustard_paint")
    proc("window_seat", "loft", b=[15.0, 43.5, 21.0, 45.0, z, z + 1.5], face="-y", cushion_m="velvet_teal", pillows=4, pillow_mats=["wool_mustard", "wool_oatmeal", "oxblood", "olive_paint"], books=3, throw="wool_oatmeal")
    proc("bookwall", "loft", b=[14.28, 30.0, 15.2, 36.0, z, z + 7.5], face="+x", seed=27, density=0.9, shelf_ft=1.1)
    proc("wall_frame", "loft", wall=W("y", 14.0, "+x"), u=33.0, zc=z + 8.3, w=1.6, h=1.2, seed=211)
    add(asset="proc:cabinet", room="loft", b=[14.28, 27.0, 14.95, 29.5, z + 3.5, z + 3.58], doors=1, face="+x", m="walnut_h")   # charging shelf
    model("classic_laptop", (14.6, 28.6, z + 3.58), "loft", length_ft=0.8, rot_z=90)
    proc("round_table", "loft", pos=[18.0, 33.0, z], radius=1.5, height=1.4)
    proc("puzzle", "loft", b=[17.0, 32.3, 19.0, 33.7], z=z + 1.41, seed=33)
    model("painted_wooden_chair_01", (16.5, 31.8, z), "loft", height_ft=2.0, rot_z=129)   # toward the table at (18, 33)
    model("painted_wooden_chair_01", (19.6, 33.6, z), "loft", height_ft=2.0, rot_z=-69)
    proc("cushions", "loft", b=[17.5, 34.6, 19.0, 35.6], z=z, count=1, seed=3, mats=["velvet_teal"])
    proc("rug", "loft", b=[15.3, 30.5, 21.0, 41.5], m="rug_stripe_multi", thick=0.05)
    proc("toy_chest", "loft", b=[19.5, 26.5, 21.5, 29.0, z, z + 1.8])
    model("chess_set", (18.0, 40.0, z), "loft", length_ft=1.3, rot_z=15)
    proc("globe_pendant", "loft", pos=[18.0, 36.0, z + 8.2], radius=0.5, drop=0.8, watts=35)
    proc("downlights", "loft", positions=[[18, 29], [18, 43]], z=z + 9.0, watts=7)


def basement():
    z = ZB
    # ------------------------------------------------------------------ 5.1 basement hall
    note("basement hall")
    proc("runner", "bhall", b=[23.5, 2.0, 26.5, 32.0], m="runner")
    for y in (2, 16, 20, 30):
        proc("wall_frame", "bhall", wall=W("y", 22.0, "+x"), u=y, zc=z + 5.5, w=1.6, h=2.0, seed=220 + y)
        proc("picture_light", "bhall", wall=W("y", 22.0, "+x"), u=y, z=z + 8.3, watts=7)
    proc("console", "bhall", pos=[27.25, 28.0, z], length=4.0, depth=1.0, height=2.7, rot_z=90, items=["lamp", "bowl"], lamp_base_m="brass")
    proc("downlights", "bhall", positions=[[25, 6], [25, 18], [25, 30]], z=z + 9.5, watts=4)
    # ------------------------------------------------------------------ 5.2 gym (faces X 1, Y 1, partition 19.75 / 21.75)
    note("gym")
    proc("wall_finish", "gym", wall=W("x", 0.0, "+y"), span=[1.3, 21.7], z=[z + 0.3, z + 9.4], m="olive_paint")
    proc("wall_finish", "gym", wall=W("y", 0.0, "+x"), span=[2.0, 19.5], z=[z + 0.1, z + 7.0], m="mirror_wall", thick=0.02)
    for x in (5, 11, 17):
        proc("poster", "gym", wall=W("x", 0.0, "+y"), u=x, zc=z + 5.0, w=2.0, h=2.9, seed=230 + x)
    proc("wall_screen", "gym", b=[7.2, 19.68, 12.8, 19.75, z + 3.4, z + 6.6])
    proc("platform", "gym", b=[3.0, 3.0, 11.0, 11.0, z, z + 0.15])
    proc("power_rack", "gym", pos=[7.0, 7.0, z + 0.15], width=4.0, depth=4.0, height=7.5)
    proc("plate_tree", "gym", pos=[8.8, 2.0, z])
    proc("functional_trainer", "gym", pos=[16.0, 18.5, z], rot_z=0)
    proc("gym_bench", "gym", pos=[12.0, 12.0, z], rot_z=0)
    proc("dumbbell_rack", "gym", pos=[5.0, 1.9, z], length=5.0, rot_z=0)
    proc("treadmill", "gym", pos=[18.0, 4.0, z], rot_z=180)
    proc("rower", "gym", pos=[19.5, 14.0, z], rot_z=90)
    proc("kettlebells", "gym", pos=[12.4, 2.0, z])
    proc("yoga_basket", "gym", pos=[1.9, 18.0, z])
    proc("rings", "gym", pos=[14.0, 7.0, z + 9.4], drop=5.5)
    proc("floor_fan", "gym", pos=[2.7, 12.0, z])
    proc("towel_shelf", "gym", pos=[21.4, 17.0, z + 4.0])
    proc("wall_clock", "gym", wall=W("x", 0.0, "+y"), u=11.0, z=z + 7.0)
    proc("band_rail", "gym", wall=W("y", 22.0, "-x"), u=3.0, z=z + 5.0)
    proc("downlights", "gym", positions=[[4, 4], [11, 4], [18, 4], [4, 10], [11, 10], [18, 10], [4, 16], [11, 16], [18, 16]], z=z + 9.5, watts=28, kelvin=3500, angle=55)
    # ------------------------------------------------------------------ 5.3 recovery suite
    note("recovery suite")
    proc("wall_finish", "recovery", wall=W("y", 22.0, "-x"), span=[20.3, 27.7], z=[z + 0.3, z + 9.4], m="green_deep")
    proc("sauna2", "sauna", b=[1.0, 20.25, 7.6, 27.75, z, z + 9.5])
    proc("bench", "recovery", pos=[10.0, 26.9, z], length=3.0, depth=1.5, height=1.5, rot_z=0, cushion=False, m="walnut_h")
    proc("hooks", "recovery", wall=W("x", 28.0, "-y"), span=[8.5, 11.5], z=z + 4.0, count=3, jacket=True)
    proc("towel_warmer", "recovery", wall=W("x", 28.0, "-y"), u=10.0, z=z + 3.5)
    # the shower's west wall stops at Y 22 so the dry path along the south edge reaches the landing and the sauna
    # (the spec's full-length wall left the landing with no way in)
    proc("tile_wainscot", "recovery", boxes=[[12.0, 22.0, 12.03, 27.75, z, z + 9.5], [11.97, 22.0, 12.0, 27.75, z, z + 9.5], [12.0, 27.72, 20.0, 27.75, z, z + 9.5]], m="terrazzo")
    proc("shower2", "recovery", b=[12.03, 20.25, 20.0, 27.75], glass=[["+x", 22.0, 27.75]], head_wall="+y", heads=[14.0, 18.0], z=z,
         niche=[13.0, 14.5, 4.0, 5.2], bench=[12.5, 20.5, 15.0, 22.0, 0, 1.5])
    proc("fridge_small", "recovery", b=[20.3, 26.0, 21.75, 27.5, z, z + 2.5], face="-x")
    add(asset="proc:cabinet", room="recovery", b=[20.3, 26.0, 21.75, 27.5, z + 3.2, z + 3.28], doors=1, face="-x", m="walnut_h")
    proc("towels", "recovery", pos=[21.0, 26.2, z + 3.3], count=2)
    proc("hooks", "recovery", wall=W("y", 22.0, "-x"), span=[21.0, 22.5], z=z + 5.0, count=2, jacket=False)
    proc("downlights", "recovery", positions=[[10, 24], [14, 24], [18, 24], [21, 22]], z=z + 9.5, watts=5)
    # ------------------------------------------------------------------ 5.4 lounge (north face Y 45, west face X 1)
    note("lounge")
    proc("paneled_wall", "lounge", b=[1.3, 44.94, 21.7, 45.0, z + 0.3, z + 9.4], face="-y", m="walnut_panel")
    proc("pit_furnish", "lounge", b=[4.0, 32.0, 16.0, 42.0], floor_z=z - 1.5, room_z=z, m="velvet_teal")
    proc("pendant_row", "lounge", positions=[[7, 37, z + 5.5], [10, 37, z + 5.5], [13, 37, z + 5.5]], radius=0.5, drop=3.5, watts=28)
    proc("wall_screen", "lounge", b=[6.0, 44.85, 14.0, 44.94, z + 1.75, z + 6.25])
    proc("media_cabinet", "lounge", b=[5.0, 44.2, 15.0, 44.94, z, z + 1.8], face="-y")
    proc("game_table", "lounge", pos=[19.0, 32.6, z], chairs="ns")   # 5.75 ft between the pit and the wall: two chairs
    proc("pendant_cone", "lounge", pos=[18.5, 31.0, z + 5.5], drop=3.5, watts=26)
    proc("cabinet_row", "lounge", b=[1.0, 28.5, 2.0, 32.0, z, z + 7.0], doors=2, face="+x", m="walnut_h", games=True)
    proc("rug", "lounge", b=[2.5, 29.0, 15.5, 32.0], m="rug_oxblood", thick=0.05)
    add(asset="proc:rug", room="lounge", b=[16.0, 29.0, 21.0, 33.0], m="rug_teal", thick=0.08, rot_z=6)
    proc("arc_lamp", "lounge", pos=[2.8, 43.5, z], reach=4.5, height=7.0, rot_z=-30, watts=45)
    proc("wall_frame", "lounge", wall=W("y", 0.0, "+x"), u=33.0, zc=z + 4.5, w=2.5, h=3.2, seed=241, frame_m="brass")
    proc("wall_frame", "lounge", wall=W("y", 0.0, "+x"), u=43.0, zc=z + 4.5, w=2.5, h=3.2, seed=242, frame_m="brass")
    proc("picture_light", "lounge", wall=W("y", 0.0, "+x"), u=33.0, z=z + 7.5, watts=8)
    proc("picture_light", "lounge", wall=W("y", 0.0, "+x"), u=43.0, z=z + 7.5, watts=8)
    model("gamepad", (9.0, 44.5, z + 1.8), "lounge", length_ft=0.5, rot_z=20)
    proc("downlights", "lounge", positions=[[3, 30], [19, 36], [3, 44], [19, 44]], z=z + 9.5, watts=3)
    # ------------------------------------------------------------------ 5.5 bar
    note("bar")
    proc("wall_finish", "bar", wall=W("x", 46.0, "-y"), span=[22.3, 27.7], z=[z + 0.3, z + 9.4], m="wallpaper_botanical_dark")
    proc("wall_finish", "bar", wall=W("y", 28.0, "-x"), span=[34.3, 45.0], z=[z + 0.3, z + 9.4], m="wallpaper_botanical_dark")
    proc("bar2", "bar", z=z)
    for y in (37.5, 40.0, 42.5):
        model("bar_chair_round_01", (21.8, y, z), "bar", height_ft=2.5, rot_z=90)
    proc("globe_pendant", "bar", pos=[24.0, 38.5, z + 5.7], radius=0.4, drop=3.3, watts=22)
    proc("globe_pendant", "bar", pos=[24.0, 42.5, z + 5.7], radius=0.4, drop=3.3, watts=22)
    proc("wall_frame", "bar", wall=W("x", 46.0, "-y"), u=25.0, zc=z + 5.0, w=1.2, h=1.5, seed=251)
    model("wine_bottles_01", (27.1, 39.0, z + 4.54), "bar", height_ft=1.0)
    # ------------------------------------------------------------------ 5.6 basement stair hall
    note("basement stair hall")
    proc("globe_pendant", "bstair_hall", pos=[29.75, 11.2, z + 7.5], radius=0.45, drop=1.9, watts=30)   # 7 ft clear under the globe at the foot of the stair
    # ------------------------------------------------------------------ 5.8 mechanical, 5.9 storage, 5.7 battery
    note("mechanical")
    proc("mechanical", "mechanical", z=z)
    proc("shop_light", "mechanical", pos=[33.0, 20.0, z + 9.2], length=4.0, rot_z=90, kelvin=4000, watts=45)
    proc("shop_light", "mechanical", pos=[38.0, 28.0, z + 9.2], length=4.0, rot_z=90, kelvin=4000, watts=45)
    note("storage")
    proc("shelving_unit", "storage", pos=[39.9, 40.0, z], length=10.0, depth=2.0, height=7.0, rot_z=90, seed=8)
    proc("bike", "storage", pos=[31.0, 44.0, z], rot_z=0, m="oxblood")
    proc("bike", "storage", pos=[31.0, 42.0, z], rot_z=0, m="steel_black", wheel_r=1.0)
    proc("square_table", "storage", pos=[35.0, 38.0, z], length=6.0, depth=2.5, height=2.5, m="plaster_warm")
    model("cardboard_box_01", (33.5, 38.0, z + 2.5), "storage", length_ft=1.4, rot_z=20)
    model("tool_cart", (30.5, 36.5, z), "storage", height_ft=3.0, rot_z=90)
    model("plastic_crate_01", (37.0, 44.0, z), "storage", length_ft=1.8)
    proc("shop_light", "storage", pos=[35.0, 40.0, z + 9.2], length=4.0, rot_z=0, kelvin=4000, watts=40)
    note("battery room")
    add(asset="proc:cabinet", room="battery", b=[40.7, 2.0, 41.0, 5.0, z + 2.0, z + 6.0], doors=1, face="-x", m="steel_black")
    add(asset="proc:cabinet", room="battery", b=[40.7, 9.0, 41.0, 12.0, z + 2.0, z + 6.0], doors=1, face="-x", m="steel_black")
    add(asset="proc:cabinet", room="battery", b=[38.0, 12.45, 40.0, 12.75, z + 3.0, z + 6.0], doors=1, face="-y", m="galvanized")


def garage():
    z = ZG
    # garage walls are 1 ft inside the lines: faces X -5 / 17, Y 65 / 93
    note("garage")
    proc("lift", "garage", posts=[[-4.5, 70], [4.5, 70], [-4.5, 86], [4.5, 86]], runways=[[-3.8, -2.1], [2.1, 3.8]], y=[68.5, 88], z=z, runway_z=5.5)   # clear of the bench (Y 65-67.5)
    model("covered_car", (0.0, 78.5, z + 5.5), "garage", height_ft=4.6, rot_z=0)   # the roadster under its fitted cover, on the lift runways (Poly Haven covered_car)
    proc("car", "garage", pos=[0.0, 77.0, z], kind="suv", length=15.5, width=6.3, height=5.6, rot_z=0, m="car_white")
    proc("car", "garage", pos=[12.0, 77.0, z], kind="sedan", length=15.5, width=6.1, height=4.7, rot_z=0, m="car_gray")
    proc("charger", "garage", wall=W("y", 18.0, "-x"), u=70.0, z=z + 4.0)
    proc("charger", "garage", wall=W("y", -6.0, "+x"), u=75.0, z=z + 4.0)
    proc("garage_bench", "garage", b=[-3.0, 65.0, 17.0, 67.5, z, z + 3.0], wall=W("x", 64.0, "+y"), peg_z=[z + 3.5, z + 7.5], tools=36, shelf=False)   # the rolling chest lives under it
    model("metal_tool_chest", (10.0, 66.3, z), "garage", height_ft=3.0, rot_z=0)
    model("metal_toolbox", (14.0, 66.0, z + 3.0), "garage", length_ft=1.6, rot_z=10)
    model("wooden_ladder", (-3.9, 88.3, z), "garage", height_ft=5.5, rot_z=90)   # it is a step ladder
    # (no free wall for a 6 ft shelving unit with three cars, the lift and the bench; storage is on the pegboard and under the bench)
    proc("compressor_closet", "garage", b=[-5.0, 65.0, -3.0, 67.5, z, z + 6.0])
    proc("reel", "garage", pos=[13.5, 69.5, z + 11.5], m="steel_black")   # over the aisle in front of the bench
    proc("reel", "garage", pos=[15.5, 69.5, z + 11.5], m="rubber_red")
    model("plastic_broom", (-3.9, 92.1, z), "garage", height_ft=4.5, rot_z=200)
    proc("shovel", "garage", pos=[-2.6, 92.4, z])
    proc("ice_melt", "garage", pos=[-1.6, 92.3, z])
    model("cardboard_box_01", (16.2, 66.4, z + 3.0), "garage", length_ft=1.5)
    model("garden_hose_wall_mounted_01", (-4.55, 91.5, z + 3.5), "garage", length_ft=1.8, rot_z=90)
    for x in (-3.0, 3.0, 9.0, 15.0):
        for y in (70, 86):
            proc("shop_light", "garage", pos=[x, y, z + 11.4], length=4.0, rot_z=90, kelvin=4000, watts=60)
