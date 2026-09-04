"""The lived-in layer: small real things on counters, tables and floors, room by room.

Everything here is CC0 Poly Haven where a model exists (dims and forward directions measured with
tools/model_sheet.py and tools/model_facing.py) and a small procedural prop otherwise (gens3.gen_small_props).
Positions are feet, base-centred, on the surface heights the furniture generators use (island top 3.0, counters
3.0, desks 12.4 upstairs, nightstands 2.2, coffee table 1.32, media cabinet 1.39, bench 1.5, cabinet 2.5).

Model facing at rot 0 (yaw of the forward direction, degrees): chairs -90 (-Y); desk lamp -91; covered car -89;
treasure chest -90; chalkboard -90; hand truck 78; broom 176; tire pump -172; extinguisher -174; microscope 87;
chemistry set -174; radio -18; camera -95; throw pillows -139; watering can 90; gnome -142.
"""
from staging_main import add, model, note, proc, W

Z2 = 10.0      # second floor
ZB = -10.0     # basement
ZG = -0.4      # garage slab


def main_floor():
    # ------------------------------------------------------------------ entry
    note("entry clutter")
    model("wooden_bowl_02", (13.3, 12.25, 2.7), "entry_hall", height_ft=0.22)                       # keys bowl on the console
    model("round_spectacles", (15.9, 12.35, 2.7), "entry_hall", rot_z=25, height_ft=0.12)
    model("wicker_basket_01", (14.5, 12.25, 0.0), "entry_hall", height_ft=0.4, rot_z=0)              # tray basket under it
    proc("small_props", "vestibule", kind="magazines", pos=[9.0, 4.3, 1.5], rot_z=90, count=2, seed=4)   # post on the bench
    # ------------------------------------------------------------------ kitchen: the cooking wall counter (X 19.6-21.75, Y 22.5-25.05, top 3.0)
    note("kitchen clutter")
    proc("small_props", "kitchen", kind="oil_bottles", pos=[20.9, 22.85, 3.0], rot_z=10)
    proc("small_props", "kitchen", kind="knife_block", pos=[20.7, 24.85, 3.0], rot_z=180)
    proc("small_props", "kitchen", kind="paper_towel", pos=[20.4, 23.35, 3.0])
    model("wooden_spoon", (20.9, 23.95, 3.02), "kitchen", rot_z=70, height_ft=0.05)
    model("food_avocado_01", (15.25, 18.55, 3.12), "kitchen", height_ft=0.36, rot_z=30)              # on the cutting board
    model("food_lime_01", (14.85, 18.15, 3.12), "kitchen", height_ft=0.24)
    model("lemon", (14.7, 18.6, 3.12), "kitchen", height_ft=0.28, rot_z=80)
    model("tea_set_01", (5.4, 28.55, 3.0), "kitchen", length_ft=1.5, rot_z=0)                        # nook counter
    model("bananas", (3.2, 28.5, 3.0), "kitchen", length_ft=0.95, rot_z=-30)
    model("wooden_bowl_01", (7.0, 28.6, 3.0), "kitchen", height_ft=0.3)
    model("food_apple_01", (7.0, 28.6, 3.18), "kitchen", height_ft=0.26)
    model("food_apple_01", (7.25, 28.45, 3.18), "kitchen", height_ft=0.25, rot_z=60)
    proc("small_props", "kitchen", kind="mug", pos=[14.9, 26.2, 2.5], rot_z=-40)                      # on the table end
    # ------------------------------------------------------------------ pantry (counter top 3.1 along the west wall)
    note("pantry clutter")
    model("wine_bottles_01", (2.0, 23.0, 3.1), "pantry", height_ft=1.0, rot_z=90)
    model("wooden_bowl_02", (1.9, 24.4, 3.1), "pantry", height_ft=0.24)
    model("croissant", (1.9, 24.4, 3.3), "pantry", height_ft=0.18, rot_z=20)
    model("plastic_container", (6.6, 23.2, 0.0), "pantry", height_ft=1.35, rot_z=90)
    # ------------------------------------------------------------------ living
    note("living clutter")
    proc("small_props", "living", kind="remote", pos=[7.7, 38.3, 1.32], rot_z=15)
    proc("small_props", "living", kind="magazines", pos=[18.95, 33.2, 1.39], rot_z=90, count=3, seed=7)  # on the media cabinet (top 1.39)
    model("camera_01", (18.9, 34.6, 1.39), "living", rot_z=60, height_ft=0.25)
    proc("small_props", "living", kind="mug", pos=[5.9, 38.9, 1.32], rot_z=120, m="teal")
    proc("small_props", "living", kind="candle", pos=[6.3, 40.3, 1.32])
    # ------------------------------------------------------------------ away room
    note("away clutter")
    model("round_spectacles", (22.5, 42.6, 1.9), "away", rot_z=-20, height_ft=0.12)
    model("wooden_candlestick", (24.4, 44.6, 2.5), "away", height_ft=0.7)
    model("wooden_candlestick", (24.85, 44.55, 2.5), "away", height_ft=0.55)
    model("carved_wooden_elephant", (25.6, 44.6, 2.5), "away", height_ft=0.32, rot_z=-70)
    proc("small_props", "away", kind="mug", pos=[23.2, 42.5, 1.9], rot_z=200, m="oxblood")
    # ------------------------------------------------------------------ powder and primary bath
    note("bath clutter")
    proc("small_props", "powder", kind="soap_pump", pos=[14.9, 4.25, 3.2], rot_z=0)
    proc("small_props", "primary_bath", kind="soap_pump", pos=[29.3, 19.4, 2.95], rot_z=0)
    proc("towel_stack", "primary_bath", pos=[29.3, 21.0, 2.95], w=0.9, d=0.55, count=3, layer=0.09, seed=2)
    proc("rug", "primary_bath", b=[33.4, 19.3, 34.9, 20.7], m="towel_white", thick=0.06)              # bath mat at the shower
    proc("small_props", "primary_bath", kind="shampoo_set", pos=[40.4, 18.55, 0.0], rot_z=90)
    # ------------------------------------------------------------------ primary bedroom (nightstand top 2.2, bench 1.5)
    note("bedroom clutter")
    model("alarm_clock_01", (29.1, 33.0, 2.2), "primary_bedroom", rot_z=90, height_ft=0.4)
    model("binder_notebook", (29.0, 31.9, 2.2), "primary_bedroom", rot_z=85, length_ft=0.95)
    proc("small_props", "primary_bedroom", kind="water_glass", pos=[29.35, 42.9, 2.2])
    proc("small_props", "primary_bedroom", kind="phone", pos=[29.0, 44.1, 2.2], rot_z=95)
    model("round_spectacles", (28.9, 43.5, 2.2), "primary_bedroom", rot_z=110, height_ft=0.12)
    proc("throw", "primary_bedroom", b=[36.3, 36.9, 37.5, 38.3], z=1.5, m="knit_charcoal", hang=None)   # folded on the bench
    model("wicker_basket_02", (39.8, 36.8, 0.0), "primary_bedroom", height_ft=1.9)                    # hamper
    # ------------------------------------------------------------------ laundry (counter top 2.9)
    note("laundry clutter")
    model("all_purpose_cleaner", (36.4, 1.6, 2.9), "laundry", height_ft=1.0, rot_z=20)
    model("multi_cleaner_bottle", (37.0, 1.5, 2.9), "laundry", height_ft=0.75, rot_z=-10)
    model("bleach_bottle", (37.6, 1.7, 2.9), "laundry", height_ft=0.95, rot_z=40)
    proc("towel_stack", "laundry", pos=[38.4, 2.0, 2.9], w=1.1, d=0.7, count=4, seed=6, mats=["towel_white", "linen_grey", "towel_white", "wool_oatmeal"])
    model("wooden_broom", (38.05, 9.8, 0.0), "laundry", height_ft=4.6, rot_z=20)   # leaning in the corner where the elevator closet meets the neck
    model("dustpan", (37.4, 9.45, 0.0), "laundry", height_ft=0.3, rot_z=80)
    # ------------------------------------------------------------------ mudroom
    note("mudroom clutter")
    model("wicker_basket_02", (6.7, 18.3, 0.0), "mudroom", height_ft=1.1)
    model("watering_can_metal_01", (7.1, 16.2, 0.0), "mudroom", height_ft=0.65, rot_z=-90)
    # ------------------------------------------------------------------ spine and stair hall
    note("spine clutter")
    model("wicker_basket_01", (27.3, 22.0, 0.0), "spine", height_ft=0.4, rot_z=90)                    # under the console


def exterior():
    note("terrace clutter")
    model("propane_tank", (25.5, 48.1, 0.0), "living", height_ft=1.5)                                   # under the grill
    model("garden_gnome", (21.9, 55.0, -0.3), "living", height_ft=1.6, rot_z=100)
    model("watering_can_metal_01", (3.4, 54.6, -0.3), "living", height_ft=0.65, rot_z=40)
    model("wooden_picnic_table", (13.0, 60.5, -0.3), "living", length_ft=7.3, rot_z=90)   # on the lawn between terrace and garage
    model("stone_fire_pit", (4.0, 60.5, -0.3), "living", length_ft=4.7)
    model("exterior_aircon_unit", (-2.6, 40.0, -0.3), "living", height_ft=3.0, rot_z=90)              # condensers on the west side


def second_floor():
    z = Z2
    # ------------------------------------------------------------------ her office (desk top 12.4 along the west wall)
    note("office clutter")
    model("desk_lamp_arm_01", (2.3, 12.6, z + 2.4), "her_office", height_ft=1.9, rot_z=180)          # head over the desk, toward +Y
    model("office_notepads", (2.6, 14.1, z + 2.4), "her_office", rot_z=15, length_ft=1.0)
    model("stationery_supplies", (2.9, 18.3, z + 2.4), "her_office", rot_z=90, length_ft=0.6)
    model("vintage_stapler", (2.3, 19.3, z + 2.4), "her_office", rot_z=100, length_ft=0.8)
    proc("small_props", "her_office", kind="mug", pos=[2.1, 15.3, z + 2.4], rot_z=160)
    proc("small_props", "her_office", kind="phone", pos=[2.8, 17.0, z + 2.4], rot_z=80)
    model("pocket_watch", (8.6, 11.6, z + 1.9), "her_office", height_ft=0.3, rot_z=30)              # on the side table
    # ------------------------------------------------------------------ lab (desk top 12.4 at Y 8-10.5; workbench top 13.0 at X 11.25-13.75)
    note("lab clutter")
    model("classic_laptop", (25.0, 9.3, z + 2.4), "lab", rot_z=180, length_ft=1.4)
    model("circuit_board", (26.8, 8.8, z + 2.4), "lab", rot_z=20, length_ft=0.9)
    model("retro_multimeter", (23.3, 8.7, z + 2.4), "lab", rot_z=200, height_ft=0.6)
    model("chemistry_set", (22.9, 9.9, z + 2.4), "lab", rot_z=90, height_ft=1.1)
    model("bunsen_burner", (12.6, 11.6, z + 3.0), "lab", height_ft=0.55)
    model("magnifying_glass_01", (12.3, 12.6, z + 3.0), "lab", rot_z=40, height_ft=0.8)
    model("industrial_microscope", (12.5, 9.2, z + 3.0), "lab", rot_z=-90, height_ft=1.2)           # eyepiece toward the stool
    model("vintage_radio_transceiver", (17.4, 18.0, z + 2.35), "lab", rot_z=190, length_ft=1.2)     # on the round table
    proc("small_props", "lab", kind="mug", pos=[26.6, 9.9, z + 2.4], rot_z=30, m="teal")
    # ------------------------------------------------------------------ bedroom A (bed head -x at X 4; desk along the south wall)
    note("bedroom A clutter")
    model("throw_pillows_01", (8.6, 38.3, z + 1.62), "bedroom_a", rot_z=150, length_ft=1.6)
    model("treasure_chest", (12.6, 37.6, z), "bedroom_a", length_ft=2.6, rot_z=-90)                 # toy chest against the east wall
    model("football", (9.6, 31.9, z), "bedroom_a", height_ft=0.7)
    model("wooden_display_shelves_01", (13.1, 33.2, z), "bedroom_a", height_ft=4.6, rot_z=0)        # cube shelves, east wall
    model("postcard_set_01", (3.5, 26.32, z + 4.9), "bedroom_a", length_ft=0.5, rot_z=0)            # on the corkboard
    proc("small_props", "bedroom_a", kind="water_glass", pos=[2.1, 38.9, z + 2.2])
    # ------------------------------------------------------------------ bedroom B (bed head -y at Y 29; desk along the south wall)
    note("bedroom B clutter")
    model("standing_chalkboard_01", (29.6, 38.6, z), "bedroom_b", height_ft=4.6, rot_z=180)          # A-frame, faces the room (+X)
    model("football", (31.0, 39.8, z), "bedroom_b", height_ft=0.7, rot_z=40)
    model("sungka_board", (35.0, 44.5, z + 2.5), "bedroom_b", length_ft=1.8, rot_z=0)
    model("gaming_console", (38.6, 44.35, z + 2.5), "bedroom_b", length_ft=1.0, rot_z=30)
    model("gamepad", (37.4, 44.4, z + 2.5), "bedroom_b", rot_z=-30, length_ft=0.7)
    model("throw_pillows_01", (39.2, 32.8, z + 1.62), "bedroom_b", rot_z=230, length_ft=1.5)
    proc("small_props", "bedroom_b", kind="water_glass", pos=[36.5, 30.0, z + 2.2])
    # ------------------------------------------------------------------ kid bath (vanity top 2.9 along the Y 28 wall; tub at Y 25.5)
    note("kid bath clutter")
    proc("small_props", "kid_bath_sink", kind="toothbrush_cup", pos=[30.4, 27.35, z + 2.9])
    proc("small_props", "kid_bath_sink", kind="soap_pump", pos=[32.6, 27.35, z + 2.9], m="plastic_teal")
    proc("rug", "kid_bath_tub", b=[37.0, 24.0, 39.6, 25.3], m="towel_white", thick=0.06)
    proc("small_props", "kid_bath_tub", kind="shampoo_set", pos=[40.5, 27.4, z + 1.6], rot_z=180)
    # ------------------------------------------------------------------ halls and loft
    note("hall clutter")
    model("potted_plant_04", (27.25, 43.0, z + 3.0), "hall", height_ft=1.0)
    model("wooden_display_shelves_01", (20.9, 31.3, z), "loft", height_ft=4.6, rot_z=180)             # cube shelves on the loft's east wall
    model("treasure_chest", (20.2, 38.5, z), "loft", length_ft=2.4, rot_z=0)
    model("rockingchair_01", (16.4, 41.4, z), "loft", height_ft=3.2, rot_z=180)                         # faces the window seat (+Y)


def basement():
    z = ZB
    note("basement clutter")
    model("brass_vase_02", (27.3, 27.1, z + 2.7), "bhall", height_ft=1.0)
    model("gaming_console", (11.4, 44.55, z + 1.8), "lounge", length_ft=1.05, rot_z=0)
    model("wicker_basket_02", (17.4, 43.2, z), "lounge", height_ft=1.5)
    model("dartboard", (1.08, 40.2, z + 4.3), "lounge", height_ft=1.45, rot_z=-90)                   # on the west wall, faces +X
    proc("towel_stack", "recovery", pos=[9.2, 26.9, z + 1.5], w=1.0, d=0.6, count=3, seed=8)
    model("wooden_crate_02", (35.0, 42.3, z), "storage", length_ft=3.6, rot_z=0)
    model("plastic_crate_03", (37.0, 44.0, z + 0.9), "storage", length_ft=1.6, rot_z=10)
    model("vintage_suitcase", (37.6, 41.5, z), "storage", length_ft=2.2, rot_z=0)


def garage():
    z = ZG
    note("garage clutter")
    model("korean_fire_extinguisher_01", (-4.4, 68.2, z), "garage", height_ft=2.1, rot_z=-90)
    model("hand_truck", (15.4, 91.4, z), "garage", height_ft=4.5, rot_z=90)                           # against the north wall
    model("tire_pump", (13.9, 92.0, z), "garage", height_ft=1.9, rot_z=90)
    model("metal_jerrycan", (14.6, 91.4, z), "garage", height_ft=1.45, rot_z=20)
    model("plastic_crate_02", (16.0, 70.2, z), "garage", length_ft=1.65, rot_z=0)
    model("plastic_crate_03", (16.0, 70.3, z + 0.83), "garage", length_ft=1.6, rot_z=6)
    model("metal_trash_can", (15.9, 88.4, z), "garage", height_ft=3.1)
    model("metal_stool_02", (8.0, 69.3, z), "garage", height_ft=1.5, rot_z=30)
    model("oil_tin", (12.0, 66.0, z + 3.0), "garage", height_ft=0.65, rot_z=15)
    model("lubricant_spray", (13.0, 66.4, z + 3.0), "garage", height_ft=0.55)
    model("spray_paint_bottles", (8.0, 66.5, z + 3.0), "garage", height_ft=0.75, rot_z=40)
    model("measuring_tape_01", (6.5, 66.2, z + 3.0), "garage", length_ft=0.55, rot_z=70)
    model("pliers", (7.4, 66.6, z + 3.0), "garage", height_ft=0.55, rot_z=-30)
    model("screwdrivers_02", (5.8, 66.4, z + 3.0), "garage", length_ft=0.85, rot_z=15)
    model("adjustable_wrench", (4.6, 66.3, z + 3.0), "garage", height_ft=0.75, rot_z=100)
    model("garden_gloves_01", (2.0, 66.4, z + 3.0), "garage", length_ft=0.95, rot_z=-20)
    model("seeding_tray_01", (0.5, 66.4, z + 3.0), "garage", length_ft=0.7)
    model("wooden_bucket_01", (-3.6, 90.6, z), "garage", height_ft=1.15)
    model("plastic_bottle_gallon", (-2.1, 69.9, z), "garage", height_ft=0.9, rot_z=30)
    model("medical_box", (16.4, 66.4, z + 3.0), "garage", length_ft=1.4, rot_z=0)
