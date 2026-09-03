# Build log

Running log of decisions, plan.json edits, and measured timings. Newest at the bottom.

## Environment

- Claude Code web VM, Ubuntu 24.04, 4 CPU threads, 15 GB RAM, no GPU.
- apt Blender 4.0.2 renders headlessly but is built without OpenImageDenoise, so it cannot denoise.
  Switched to the official Blender 4.2.11 LTS Linux tarball in /opt (has OIDN). All timings below are 4.2.11 on CPU.
- ffmpeg from apt. Pillow via pip for the contact sheet.

## M0: toolchain

- Default cube, 320x180, 16 samples, denoised: 1.0 s.

## M1: main floor from JSON

Plan edits (section 7 of the brief), all logged here:

1. Away room had no path to the spine: its door at X=30 faced the powder/laundry wall and straddled their
   boundary at Y=6. Fix: powder shrinks to Y 0-5, laundry to Y 5-10.5, and a new 3.5 ft "awayhall"
   at Y 10.5-14 connects the spine (cased opening at X=24) to the away room (door at X=30). Room count
   on the main floor is now 12. Footprint unchanged. This is an adjacency change; Henry told me to keep
   working rather than block, so I made the minimal one.
2. The living bookwall (X 17-17.5, Y 31-45.5) sat directly in front of the 10 ft living-to-spine opening
   (Y 33-43). Fix: opening narrowed to 4 ft at Y 30.5-34.5, bookwall shortened to Y 35-45.5.
3. Main shot camera walked through the kitchen/spine wall at about Y=14 between the t=4 and t=6.5
   waypoints, and the t=6.5 waypoint stood inside the island footprint. Rebuilt the path with explicit
   doorway waypoints (foyer-to-spine at [18,7], kitchen-to-spine at [18,22]) and moved the kitchen
   waypoint east of the island. Shot lengthened from 10 s to 12 s so the walk stays under about 4 ft/s.
4. Final living waypoint moved off the sofa footprint and back to [10.5, 34.5] looking at [3, 41] so the
   fireplace wall (left) and the rear glass (right) are both substantially in frame.
5. Basement "gym to mechanical" door was on X=30, which is the recovery/mechanical wall, not the gym's.
   Replaced with "storage to mechanical" at Y=20 so utility rooms chain off the stair hall.
6. "bar open to lounge" was 8 ft wide centered at 26, exactly the bar's full width, so the cutter nicked
   both corner walls. Narrowed to 7 ft.
7. Basement pit waypoint (t=5) moved from over the pit to the rim at [10, 31.8] looking diagonally down
   and across so the drop reads. Added a t=6.5 waypoint so the camera walks along the rim instead of
   cutting the pit corner.
8. Sun direction flipped to come from the back yard ([0.35, -0.55, -0.75]) so sun enters the rear glass,
   which is what section 11.7 asks for. The spec's original direction lit the street side.
9. Fire glow box was fully inside the firebox and invisible; moved it proud of the firebox face and cut the
   lamp emission from 25 to 8 (it clipped white).
10. Exposure: rendered the living still at +0.5, 0.0 and -0.5 EV. +0.5 washed out the walnut; 0.0 keeps
    the rear glass void unclipped and walnut readable. World strength 1.0 -> 0.8.
11. Added a ground plane (plan "ground") so window voids show a horizon instead of flat gray.

Construction notes:
- Walls shared with a neighbor are half thickness inside each room (per brief). Exterior walls are full
  thickness inside the room so the shell is not 3 in thick.
- Slabs are split: floor slab is the top half of the slab, ceiling slab the bottom half, so the basement
  ceiling and main floor do not occupy the same volume.
- Side walls are shortened to butt against the front/back walls so no coplanar faces at corners.
- Openings find walls by bounding-box overlap plus matching axis, then boolean difference (Exact), applied.
- The camera path is sampled every frame and tested against every shell/feature mesh (ray-parity inside
  test plus a 0.3 ft clearance). Both shots report clear.

Timings (640x360, 32 samples, denoised, CPU 4 threads):
- scene build: 0.9 s, 172 objects, 43 wall cuts
- front door still: 11.9 s
- kitchen still: 18.2 s
- living still: 12.0 s
- gym still: 17.8 s
- pit still: 15.8 s

## M2: main floor preview

- 96 frames (every 3rd of 288) at 640x360 / 32 samples: mean 19.8 s/frame, 31.6 min total.
- Camera path check reports clear for both shots (ray-parity inside test plus 0.3 ft clearance, every frame).
- Stitched at 8 fps: renders/preview/main_floor_preview_phase1.mp4 (12 s). Camera move is a slow walk; no wall clips.

## Phase 2 build (M6 to M10 collapsed into one iteration loop)

Henry asked me to keep working rather than stop for the M3/M8 approvals, so those gates are review stills committed
in renders/stills_preview and the contact sheet instead of a pause.

Assets: 21 texture sets (20 Poly Haven, 2 ambientCG terrazzo), 54 glTF models, 1 HDRI. All CC0, recorded with URLs in
assets/manifest.json. decorative_book_set_01 has no glTF export and was dropped (books are procedural anyway).
pachira_aquatica_01 and calathea_orbifolia_01 are multi-plant sets (22 ft and 8 ft wide) and are not placed.

Plan edits during Phase 2:
12. Stair: the basement "stair" room sits under the bedroom, not the spine, so a stair "from the spine" had nowhere
    to land. The stair now descends from the north end of the spine (X 18.5-23.5, from Y 33.5) into the lounge,
    14 risers at 8.57 in, through a well cut in both slabs. The basement "stair" room is a landing hall serving
    storage. To clear the run, the pit moved 2 ft west to X 4-18 and the lounge TV panel to X 7-15.
13. Living-to-spine opening moved to Y 30.5-33.5 (3 ft) so it does not open onto the stair well.
14. Island split into a 6 ft stone work end (3 ft high) and a 5 ft walnut table end (2.5 ft high) with six chairs,
    per the spec's "stone work end and a table end".
15. Kitchen back counter pulled to the wall face (Y 14.25) so the backsplash and uppers sit on the wall.
16. Away room walls are the geometric olive/cream wallpaper (spec 11.5). Bedroom has one wallpapered wall behind the
    headboard; the bed head faces east (X=42) because the north wall is the garden window.
17. Beams and oak decking in both the living room and kitchen (spec 11.4 names both).
18. Both glass walls are lift-and-slides with one panel slid open over its neighbour (gym-to-lounge panel 1, rear
    glass panel 3); the basement camera walks through the open bay.
19. Room fill wattages raised for the closet, bath, away, recovery, bedroom, mudroom and foyer after the room views
    came back too dark; the basement fill multiplier is 1.3 versus 0.35 on the main floor because it has no daylight.
20. Sun 4.0 -> 2.0 and sky 0.45 so the terrace outside the rear glass is bright but not clipped against interiors at 0 EV.
    Basement shot renders at +0.8 EV (per-shot exposure in plan.json).

Bugs found from stills:
- The 400 ft ground slab sat at Z -0.8 to -0.3, inside the basement rooms, and swallowed every basement ceiling
  light. The gym and recovery suite rendered black. Ground is now four boxes around the footprint.
- Mapping node was in Texture mode, which applies the inverse transform: a 1 ft wallpaper pattern rendered at 10 ft
  and plank textures repeated every 1.8 ft instead of 6 ft. Switched to Point mode.
- Tile backsplash evaluated its brick pattern in XY on an XZ wall (one flat row). Remapped into the wall plane.
- Blender's glTF importer left stale object references after the first import (StructRNA removed). Import bookkeeping
  now uses names.
- Fire at emission 25 to 40 clipped to white cards under AgX; now layered ellipsoids at 3 to 5 with an ember bed.
- The dark leather of the mid-century chair could not be tinted to mustard by multiplication; the two living-room
  chairs use a flat recolor instead. The away-room one keeps its leather.
- The lounge TV "on" and the pit LED cove were both several times too bright; halved and warmed to 2200K.

Timings (Phase 2, CPU 4 threads):
- scene build 13.5 s, 1939 objects (38 model instances, 91 procedural placements, 56 lights incl. 5 portals)
- review stills 640x360 / 32: 41 to 79 s each
- room views 480x270 / 24: 38 to 54 s each
- render.sh smoke test (STEP=24, 320x180, 8 samples) showed the xfade collapsing to the first clip at 1 fps because
  the 0.5 s dissolve was shorter than one output frame. The dissolve now floors at two output frames.

## M3: basement preview (Phase 1 boxes)

- 64 frames (every 3rd of 192) at 640x360 / 32 samples: mean 25.0 s/frame, 26.7 min total (rendered alongside
  other jobs, so per-frame is inflated versus the main floor's 19.8 s).
- Stitched at 8 fps: renders/preview/basement_preview_phase1.mp4 (8 s).

## Phase 2 preview (PREVIEW=1 ./render.sh, the whole pipeline)

- main_floor: 96 frames, mean 29.9 s/frame, 47.9 min. basement: 64 frames, mean 27.0 s/frame, 28.8 min.
- 6 stills at 48 samples: 58 to 67 s each. Total wall time 83 min. Output 156 frames, 19.5 s at 8 fps with the
  12-frame dissolve. Both camera paths clear against the staged scene.

## Second Phase 2 preview pass (after reviewing the first video)

21. Kitchen west wall under the clerestory was blank in the t=9 frame: added a 6.6 ft walnut pantry run
    (Y 17-28.5) and a plant in the corner.
22. Basement shot lengthened 8 s -> 9 s. The last segment panned about 40 deg/s and smeared into motion blur;
    the t=6.8 waypoint now already looks toward the bar so the final swing is about half as fast.
23. Ceiling fills moved from 2700K to 3000K so the practicals (still 2700K) read warmer than the ambient
    instead of everything being one orange. Lounge screen dimmed again (emission 0.35, darker palette).
24. Bar wallpaper rewritten as a two-layer voronoi leaf scatter on a dark teal ground; the wave-ring version read
    as stripes.
Both camera paths clear (288 + 216 frames). Full pipeline re-run in progress.
Second full preview: main_floor 96 frames at 30.7 s, basement 72 frames at 27.0 s, stills 60-68 s, 88 min wall.
Output renders/walkthrough_preview.mp4: 164 frames, 20.5 s at 8 fps. This is the committed deliverable from the VM;
the 24 fps final is Jamie's run on the Mac Mini (README).
- Dropped fabric_pattern_05 (no diffuse map on Poly Haven, unused) and decorative_book_set_01 (no glTF) from
  assets/wanted.json; fetch_assets.py now only exits non-zero if nothing at all could be fetched, so a flaky
  mirror cannot stop Jamie's render. Clean-clone test: build_scene.py --shot none builds the staged scene
  (39 model instances, 94 procedural placements, 62 lights) from a fresh clone plus the asset cache.

## Look pass (Henry: "let's make it look better")

25. Bevel pass: an unapplied Bevel modifier on every procedural box and shell wall (0.4 in detail, 0.25 in shell,
    1.2 in on upholstery), smooth shading with hardened normals. Adds about 20 s to the build and nothing measurable
    to render time. `--no-bevel` skips it.
26. Exterior plantings are now Poly Haven models: island_tree_01 x8, shrub_02 hedges, shrub_03/04, fern_02, planters,
    an outdoor table set and pots on the terrace. Procedural trees are off (plan exterior.procedural_trees=false).
    Trees cost about 9 s a frame at 640x360 (alpha leaves). jacaranda_tree and tree_small_02 only ship as 8k
    glTF (200 MB) and were dropped.
27. Sofa test: Poly Haven sofa_02 (curvy) and sofa_03 (chesterfield) both read wrong for the room; the procedural
    low sofa with beveled cushions stays.
28. Linen drape stacks at both ends of the rear glass; vertical slat reveals every 6 in on the walnut fireplace wall;
    about half the framed pieces now have a cream mat.
29. Plaster cooled slightly ([0.90,0.88,0.84]); lawn tint greener; roof black with specular level 0.12 because a
    rough dark roof at a grazing angle was mirroring the sky and reading light gray.

## Look-pass preview

- The harness container restarted mid-render but the render.sh process survived; my resumed launch then ran alongside
  it, so both shared the four cores. Per-frame numbers from that run (basement 58.6 s, stills 125-143 s) are doubled
  by contention and not representative. Main floor rendered before the overlap: 96 frames, mean 32.2 s (was 30.7
  before the plantings, so the tree models cost under 2 s a frame on the main-floor shot and about 9 s on views that
  look straight at them).
- Output renders/walkthrough_preview.mp4: 164 frames, 20.5 s at 8 fps. Committed with the contact sheet and stills.

## Web walkthrough (Henry: "a model I can walk through, like a video game house")

- export_web.py bakes all 87 world-space materials to tiles (Cycles diffuse-color bake on a one-tile plane),
  writes matching box-projected UVs on 1939 procedural meshes, swaps the 12.8 M-triangle tree models for
  procedural ones, decimates 7 models over 30k triangles, downscales every texture to 512 and exports glTF.
  Bugs on the way: Blender's bundled Python has no Pillow; the glTF importer packs textures so reload() after
  a downscale restored the 1K pixels (fixed by loading the scaled copy as a new image); recolored chairs held
  duplicated materials that still pointed at the originals. 80 MB -> 34.4 MB. Export takes about 4 min.
- web/index.html: three.js 0.160 (vendored, no CDN), pointer-lock first person, raycast collision at knee and
  chest height with wall sliding, floor snap with a 0.32 m step so the stair works, gravity, fly mode, minimap
  from plan_web.json with openings and the pit, room label, ten teleport spots, nearest-14 point lights from
  lights.json, ?lite mode without shadows.
- tools/web_screenshots.py drives it in headless Chromium (swiftshader) and screenshots every spot; all ten
  render, only console error is the missing favicon.


## Rebuild from housemasterspec.md (supersedes the brief and plan v1)

Henry supplied the master spec after the brief-built house missed the real program. plan.json is now generated by
tools/make_plan.py from the spec, room by room: 51 rooms on four levels (main 21, second 19, basement 10, garage),
92 openings from the window schedule and the per-room door lists, 6 slab voids (stair slot, two-story well, chute),
two stacked stair runs, 7 roofs, the site (lot, walk, porch, breezeway, terrace, spa, catio, garage, neighbors).
The old plan is kept as plan_v1_brief.json and the old furniture list as staging_v1_brief.json; staging.json is
empty until the layout is approved.

Engine changes for the spec: rooms are unions of rectangles with walls built per edge segment (none inside a
room, half walls between rooms, 1 ft exterior walls with brick or cedar on the outer face), slab voids, a
generalized stair generator (any run, either direction), and a site module for roofs and grounds.

Area check: main 1932 sq ft (matches the spec total), second 1716 incl. the well, basement 1932, garage 720.

Open questions for Henry (also in plan.json "questions"):
1. 2.5 W1 mudroom side door Y 15.5-18.5 overlaps the litter closet (X 0-3, Y 13-16) by 6 in on the west wall. Moved the door 9 in north to Y 16.25-19.25. OK, or should the litter closet shrink to Y 13-15.5?
2. 2.5 E2 bath window Y 15-18 straddles the WC compartment wall at Y 16.5 (WC is X 39-42, Y 13-16.5). Moved the window to Y 16.5-19.5 so it lands over the shower. OK?
3. 5.1 gym glass door at X 22, Y 10 with 'a glass sidelight from Y 8 to Y 12': the 3 ft door already spans Y 8.5-11.5, so a sidelight Y 8-12 leaves 6 in each side. I built the sidelight as a 4 ft fixed pane at Y 12-16 north of the door. Correct?
4. 5.2 gym-to-recovery glass door at Y 20, X 21 (3 ft) would span X 19.5-22.5, past the gym's east wall at X 22. Moved it 6 in west to X 19-22, tight to the corner. OK?
5. 6 / 3.8: the up-stair's first tread (Y 0.75, Z 0) sits directly above the down-stair's last tread (Y 0.75, Z -10) with the up-stair rising north and the down-stair descending south beneath it. That works geometrically (10 ft between runs everywhere), but the main-floor stair slot X 31-34, Y 0.75-13.25 is then open from the basement to the second floor, and the only way past the slot on the main floor is the 3 ft aisle X 28-31. Confirm that is intended.
6. 1.1 says the lot runs to Y 140 with the alley at Y 140; 1.9 says to model the alley as asphalt from Y 100 to Y 116 right behind the 6 ft apron. I used 1.9 (alley Y 100-116), which puts the honey locust at (30, 110) in the alley and the rear hedge at Y 100 on the alley edge. Which is right: alley at Y 100 or at Y 140?
7. 2.2 direct-vent chase [-1.5, 36, 0.5, 40] rises to Z 26 along the west gable wall; the main gable's west rake overhang runs X -4 to 0, so the chase passes up through the roof overhang at Y 36-40. I cut the roof around it. OK?
8. 10 Shot 4 (upstairs) t 11 -> t 14 runs from the rack closet straight to the hall through two 3 ft doors on a curve; the camera clipped both jambs. Added waypoints in the corridor door (16.5, 21.5) and the hall door (21.5, 24). Shot 7 (garage) t 0 -> t 4 passed through the north wall beside the west door; added a waypoint in the door at (2.5, 94.3).

## Architectural audit (Henry: "code compliant, navigable, not cramped, no clipping, no weird windows, no ugly exterior")

Henry released the exact spec numbers; every space should be what an architect would draw. Findings and fixes,
all in tools/make_plan.py unless noted:

Stair core. The spec's two straight runs in a 3 ft slot had their first and last treads against the south and
north walls, so both stairs were entered sideways from a 3 ft aisle and the main-floor slot was open from the
basement to the roof. Replaced with a stacked switchback: flights 3 ft wide, 8 risers at 7.5 in, 7 treads at
10 in (5.83 ft), a 3.25 ft landing against the south wall (>= stair width), a 3.17 ft arrival zone at the north
end that opens to the spine, the second-floor landing and the basement hall through 3 ft cased openings, and a
solid walnut centre wall from the basement floor to 3.5 ft above the second floor. Headroom is 10 ft less
structure everywhere; the up landing sits under clerestory S5 at 7 to 9 ft. build_scene.build_stairs now takes
kinds: flight, landing, wall, guard (bronze posts, walnut rail, glass). The floor voids shrank to the flights and
landing (X 28-34, Y 0.5-9.58). A bronze-and-glass guard closes the well edge on the second floor.

Stair tower. The stair hall sits in the low front band (Y 0-6) but the well needs the full height, so the core is
a cedar tower through the front shed and the main gable's south eave, capped flat at Z 21 (2 ft above the eave
surface). Roofs now take a "cuts" list; the front shed is two pieces either side of the tower and the vent chase
is cut through the west rake. Exterior faces sit on the room lines, so the tower parapet, reveal and brick bands
were pulled flush (first pass had them 6 in proud).

Exterior walls. East and west elevations showed white vertical stripes at every room boundary and at the
corners: exterior wall segments were inset by the thickness of whatever perpendicular wall met them, exposing the
plaster end faces of interior partitions, and corner end faces were never clad. Exterior segments now run
continuous past interior partitions (only another exterior wall at a corner insets them) and their end faces take
the cladding (build_scene.build_rooms / face_exterior).

Garage roof. The gable with its ridge along Y had both planes rotated the wrong way (a butterfly). Sign fixed in
site_build.gable.

Basement windows. All four sat below grade with no well, so they looked at dirt. site_build.build_wells cuts a
3 ft deep galvanized well (window width plus 1 ft), gravel floor, steel grate at grade, and a ladder when the well
is deeper than 44 in. B1 (gym) and B2 (lounge) are now egress: sill 3.5 ft, 6 ft tall.

Site. Street and sidewalk were buried inside the ground box; the front walk was co-planar with the lawn and
rendered black. Slabs with cut_ground carve the ground first (street and alley 6 in below the curb); walks and
gravel bands sit 0.5 to 1 in proud of the lawn. Tree crowns raised so the lowest crown sphere clears 12 ft
(the street camera was inside the red oak's crown). Catio screen now honours its alpha (materials_pbr).

Rooms and doors (main). Away room widened from 6 to 8 ft (X 20-28, Y 30-46) and given a glass door on the
spine axis, so the 30 ft gallery ends on N2 instead of a blank wall; the living room is 20 x 16 and its opening to
the kitchen X 0-20 with the columns at X 8 and X 20. WC compartment lengthened from 3.5 to 5 ft (21 in in front
of the bowl), its door swings out, E2 moved over the shower. Suite hall widened from 3 to 4 ft and given its own
door into the bath, so the bath is not only reached through the closet; closet 10 x 8. Laundry gets a door from
the stair-hall arrival zone as well as from the bath. Mudroom-to-kitchen door moved on axis with the side door
(it filled its 3 ft wall segment with no jambs). Spine-to-kitchen opening moved 6 in off the corner.

Rooms and doors (second, basement). Kid-zone sidelight shortened off the corner. Gym-to-recovery glass door
centred 6 in off the corner. The basement hall opens directly into the lounge (5 ft cased opening) as well as
through the bar. "hall open to lounge" was really the opening into the bar; renamed.

Checked and left alone: all doors >= 2 ft 8 in (baths and closets) or 3 ft; halls >= 4 ft except the 3 ft
basement/kid doors' corridors which are 6 ft; ceilings 9 to 9.5 ft; every bedroom has an operable window
>= 5.7 sq ft; guards 3.5 ft; handrails 3 ft above nosings; closets 3 ft deep; the elevator closets 3 x 3;
garage 24 x 30 with two 9 ft doors, a 3 ft pier and 18 in returns.

Camera. Basement shot rewritten to descend the switchback (24 s); upstairs shot gets waypoints through the
corridor and kid-zone doors. All seven paths are clear (build_scene --check-paths). render.sh now defaults to
all seven shots and cross-fades every cut through one chained xfade graph.

The eight spec questions are closed by these decisions (alley at Y 100 per 1.9, chase through the rake with a
roof cut, W1 shifted 9 in north).

Verification pass (renders/audit, 13 review views at 960x540/24 samples): east and west elevations clean,
tower flush, garage gable correct, gallery axis ends on the away-room glass and N2, suite hall and WC read right,
lounge opening from the basement hall works. Two more clipping bugs found and fixed on the way: the well's
slab-band filler stood 6 in proud of the tower face as a white plaster strip (it assumed a centred wall), and the
brick foundation band ran through the heads of the basement windows (now cut by the opening). Web viewer
re-exported for the new program (three floors, multi-part rooms, 14 teleport spots); screenshots checked headless.

## Neighborhood (Henry: "set in the context of other surrounding homes, similar to the north shore villages")

New module neighborhood.py, driven by plan["site"]["neighborhood"] (written in tools/make_plan.py). The block:
a 30 ft street six inches below the parkways with concrete curb and gutter both sides, 8 ft parkways carrying
big street trees every ~42 ft (elm, oak, maple, locust cycle, staggered across the street), 5 ft scored
sidewalks, black acorn lamp posts, a hydrant, curb-cut aprons where houses across the street have side
driveways, cedar fences between back yards, a couple of front hedges, and rear garages on the alley.
Twelve neighbours on 60 to 66 ft lots with 30 ft setbacks, six procedural period types with trim, sashes,
muntins, shutters, porches, dormers and chimneys: brick Georgian (five bays, gabled portico, end chimneys),
white clapboard colonial with a side wing, Tudor (brick base, stucco and half-timber cross gable, front
chimney), foursquare (hip roof, hipped dormer, full porch on brick piers), craftsman bungalow (front gable,
rafter tails, tapered columns), 1950s ranch (painted brick, picture window, attached garage). Our block:
Tudor, Georgian, foursquare to the west; bungalow, colonial, Tudor to the east. Across: Georgian, foursquare,
colonial, bungalow, Tudor, ranch. The spec's two placeholder brick boxes are gone.
Trees: island_tree_01/02 and tree_small_02 (Poly Haven CC0) tinted for autumn by species; a clumped
procedural crown (trunk, three limbs, 15 clumps in an ellipsoid envelope) when a model is missing; conifers
as stacked cones. jacaranda_tree and fir_tree_01 were tried and dropped: 200 to 470 MB of geometry each.
New materials: brick_red, brick_common, brick_painted, stucco_cream, three clapboard sidings (horizontal
course lines through the stripes overlay, now with an axes option and no metallic), trims, shutters, slate
and shingle roofs, half timber, dark window glass, leaf colours by species, bark, hydrant red.
Camera: an 8th shot "block" (10 s) walks the far sidewalk with the neighbours sliding past and settles on
the house; it now leads the walkthrough. Four review views v19 to v22. All eight paths clear.
Review pass on the block renders: the spec's four lot trees were still the old sphere crowns and read as
orange balloons beside the model trees, so they now go through the neighbourhood tree builder as oak, maple
and locust models. The island_tree models carry a ground disc at the base; they sit 0.9 ft below grade so it
is buried. Parkway trees are skipped within 14 ft of our front walk on both sides of the street, so the house
is visible from the far sidewalk. Ground extended to 850 x 850 ft for the aerial. Autumn tints apply to foliage
materials only (bark stayed brown) and are milder than the first try. Sun moved to the south-west: the spec's
north-east sun lit the rear glass but left every street front in shadow, and Chicago sun never comes from the
north anyway. Per-still render cost at 960x540 / 24 samples went from about 60 s to 110 to 190 s with the tree
models in frame; interiors are unchanged.
Added the next street north (backs to our alley) and the next street south, thirteen more houses, so the
aerial and the gaps between neighbours show a grid rather than empty lawn; 25 lots, 50 trees, about 4,500
objects, 90 s build. Block and street shots run at exposure +0.3 / +0.2; the street shot now ends on the porch
(door, sidelight, house number) instead of a close-up of the dark walnut slab. The two red oaks in front are
42 and 36 ft tall; taller and the house disappears under them. Review renders in renders/neighborhood.
Known limitation: the island_tree models have a banyan-like sprawling trunk that reads odd in close-ups; a
proper oak and elm model would replace them one for one through the SPECIES table in neighborhood.py.

## Staging, fixtures, lighting modes (Henry: "do it all ... IRL picture quality")

Furniture. staging.json is now generated by tools/make_staging.py from two room-by-room lists
(tools/staging_main.py: main floor and exterior; tools/staging_rest.py: second floor, basement, garage), written
against spec sections 1, 2.6, 3 to 7 at the audited coordinates. About 500 entries: 75 Poly Haven CC0 model
placements and some 380 procedural pieces. Two new generator mixins carry the procedural furniture: gens2.py
(downlights, sconces, picture lights, floor and cone pendants, LED strips, shop lights, console tables, window
seats, lounge/dining/task/kid chairs, round and square tables, ottoman, beanbag, platform bed with a thrown-back
duvet, slippers, kid beds, daybed, nightstands with the watch and phone, the whole spec kitchen (range and hood,
soapstone counters, walnut uppers, tile backsplash, fridge and freezer columns, the south wall with the oven
stack, the olive island with the bridge faucet and the walnut table end, six shell chairs, the marble nook with
the mixer, cake dome and prep sink), washer and dryer, glass-front fridge, utility sinks, wall-hung toilets,
round mirror, powder vanity, the double vanity with the backlit mirror, curbless showers with thermostatic
columns and niches, alcove tub, towel bars, tile wainscots, wardrobes (hanging with shirts, shelves, drawers,
bins, shoes), the watch island, media cabinet, low bookcases, toy chest, corkboards, pantry shelves, desks with
monitors and laptops, desk and task lamps, the French-cleat workbench with its instruments, the 24U rack with
lit ports and blinking drives, the linear gas fire in the limestone slab, walnut paneling, hearth bench, the
built-in shelves, records, speakers, baskets, scratching post, single frames, picture rails, pendant rows,
three-globe pendant) and gens3.py (spec mudroom lockers, the gym: platform, plate tree, kettlebells, rings,
fan, treadmill, towel shelf, clock, band rail, posters; the pit banquette with cap, steps, shag rug, pillows and
table; games table; the bar with its brass edge, back bar, glass shelves, espresso machine, ice machine, drawer
fridge, cake dome and lemons; the mechanical room; the garage: procedural cars with correct proportions (a
British roadster on the four-post lift, a white SUV under it, a gray sedan), the lift, chargers with coiled
cables, the pegboard bench, compressor closet, reels, bikes, shovel; exterior: brass house numerals from
seven-segment bars, mail slot, exterior sconces, soffit downlights, rain chains with splash basins, grill,
terrace heaters, planters, the open spa cover, the porch bench; the cedar sauna interior with two-tier benches,
heater and stones, guard rail, bucket, ladle, headrest, thermometer and warm strips).
Every lamp, pendant, sconce, picture light, strip, screen and fire registers a real light source.

Cats: no CC0 cat model exists on Poly Haven; per spec 11.4 the cats are omitted and logged here rather than
boxed. The package cabinet in the mudroom is dropped: with the side door at Y 16.25-19.25 and the litter closet
to Y 16 there is no west wall left for it. The laundry door I had added from the stair hall is removed again
(the chute hopper sits where it would swing; the spec's bath-side entry stands).

Lighting modes. build_scene derives a mode from the shot it renders: day, dusk (terrace shot: sun at 0.25 low
in the west at 2600K, sky at 0.12 tinted blue-hour, interiors and practicals up, lamp posts on, about 40 percent
of the neighbours' windows lit) and morning (bedroom shot: sun 3.2 low in the east at 4200K). Configured in
plan['lighting']['modes'].

Materials. Hero textures re-fetched at 4k (oak floor, walnut, plaster, brick, cedar, concrete); new sets for
slate (bluestone), asphalt, gravel, leafy autumn lawn, red and yellow brick, stucco, painted clapboard and
slate roofs; a noise-driven roughness variation option (rough_var) on floors, cedar, brick, plaster and
concrete; satin coat on walnut and the oak floor; tinted glass for the bar; terrazzo with a 3 ft brass grid in
the vestibule and 2 ft elsewhere.

Tooling. build_scene --views-file renders many poses from one build; tools/stills.py groups the review stills
by shot so each lighting mode builds once. Phase timings are logged. The staged build is about 6 minutes on
this 4-thread box, most of it in the 10,000 procedural objects; the Mac Mini will be faster.

## Overnight review pass (stage_a / stage_b / stage_c / stage_d renders)

Method: build once, render 19 to 23 free poses per batch at 960x540 / 48 samples (about 3 minutes a view on
4 threads), read every frame, fix, rebuild. Review images in renders/stage_*/stills.

Daylight. The single biggest finding: Cycles blocks shadow rays at refractive surfaces, so the sun and sky
sampled through the window glass never reached a single interior. Rooms were lit by the 2700K fills and
practicals only, hence the uniform orange cast in every stage_a and stage_b frame. Transmissive materials
now pass shadow rays as tinted transparency (Light Path > Is Shadow Ray into a Transparent BSDF, the archviz
standard); a 6 x 6 test room went from 52 to 68 mean pixel value and the sun patch appeared. Verified on the
stage_d batch.

Light fixtures. The linear fire's area light had its axes swapped (rotated 90 degrees about Y, 'size' is the
height), so it was a tall narrow panel painting a stripe up the limestone; it now lies along the firebox at
30 W just behind the glass. Picture lights halved to 4.5 W at a 50 degree cone (they were blowing the art
white). Lamp lens glow 14 to 7, lamp shade self-emission 1.4 to 0.9. Recovery downlights 8 to 5 W (the
terrazzo shower blew out), primary closet downlights 7 to 11 W (too dark to read).

Soft goods. Pillows, duvets, throws and cushions were beveled boxes. build_scene's bevel pass now gives the
cloth-tagged ones a simple subdivision, a global-coordinate Clouds displacement (so no two wrinkle alike) and
one level of Catmull-Clark; the bed duvet drops over the exposed mattress edges. gen_cushions passed a raised
z to a bottom-origin box, so every scattered pillow hovered 2 in above its seat and the tilted ones hung in
the air (visible in the pit); flat pillows sit on the surface, leaning ones tilt about their low edge against
a named back side. Kid beds get striped bedding (spec 4.8 / 4.9) instead of a flat velvet slab.

Screens. The office and lab monitors were a flat blue glow. tools/gen_textures.py draws a code-editor image
(gutter, tab bar, colored token runs, status bar) with Pillow; fetch_assets runs it after the downloads and
materials_pbr wires the diffuse into the emission (emit_tex).

Compositions that were wrong, not the rooms: the closet view stood inside the bins wardrobe, the lab view
inside the new east storage cabinet, the mudroom view inside the utility sink, the recovery view inside the
shower, the garage shot walked into the lift under the roadster (shot re-keyed down the east aisle between
the sedan and the lift). Cake domes were solid glass spheres (a dark lens); they are hollow shells now.

Frames that read right in stage_b with no change: spine (red walls, runner, console, art, front door glass),
entry, office (west sun, desk, six monitors, bookshelves), loft (bookwall, window seat, pendant, view over
the lower roof), bar (terrazzo top, brass edge, slatted front, lit shelves, stools), gym (rack, plates,
rings, mirror wall), lounge pit (banquette, steps, table, three globes), bath and vanity (floating walnut,
backlit mirror, sconces), kitchen (island, bridge faucet, sputnik, pantry), living (bookcases, fire wall,
sofa, arc lamp).

Daylight, second finding (stage_d). Doubling the sky changed nothing in the kitchen. Two causes. The kitchen
has no window by design (spec: no main-level openings on the west wall) and borrows light from the living room
glass 20 ft away, so it is honestly lit by its own lamps. And the HDRI (qwantani late afternoon) has an
upper-hemisphere mean luminance of 0.25 with a sun disc of 115,000: any world strength that lit the shade
also added a second sun. lighting.py now clamps the environment per channel at 4.0 (the disc is gone, the sun
lamp is the only sun) and runs the diffuse sky at 3.0 (dusk 0.35, morning 2.5), sun lamp 4.0 (morning 5.0).
While there: the dusk sky tint was being overridden by a second link into the background node; fixed.

White balance. With the daylight fixed the interiors were still orange: 2700K lamps under a daylight balance
are orange, and Blender 4.2 has no white balance in the view transform. geom.set_white_balance(3800) divides
every light colour (fills, practicals, sun), the sky and every emissive glow by the colour of a 3800K
blackbody, which is what a camera balanced for the room lights does: lamps read warm-neutral, the windows go
slightly cool. Flames keep their own colour (wb: false).

Lights aimed into walls. Area lights emit along local -Z, and three were rotated the wrong way: the fire
(shone back into its firebox and lit the glass white at dusk), the powder-room mirror light (into the wall),
and the Frame TV on Y-axis walls (lit its own screen white: the blown panel at the end of the main-floor
shot). Rule recorded in the code: -90 about X -> -Y, +90 about X -> +Y, +90 about Y -> -X, -90 about Y -> +X.
The firebox itself was a solid block that hid the flames; it is five thin panels now and the flame emission
is up so the fire reads through the glass.

Exposure. The street shot walks from the sunlit sidewalk into the shaded porch, which no single exposure
covers (the door frame was black at -0.6 and the sidewalk blown at +0.5). Waypoints can now carry "exp" and
key_shot keys the view exposure along the path: -0.3 to +0.5 over the street shot. Three 14 W downlights in
the porch canopy and a 22 W door sconce so the recess reads by day. Block shot at -0.3.

Frosted glass. The vanity mirror reflected a white panel: the lit water closet glowing through its frosted
door, because the new shadow-ray transparency let the WC light straight through. glass_frosted blocks shadow
rays again (shadow_transparent: false) and the WC downlight is 4 W.

Wall panels. The path check caught the upstairs camera grazing a teal paint panel that spanned the lab
doorway: gen_wall_finish never looked at the openings in its wall. It subtracts every door, window and cased
opening (plus the casing margin) now. The lab storage cabinet stood in front of the landing door; moved north
of it. All eight paths clear after the fix.

Garage shot re-keyed twice: the first path walked into the lift under the roadster; the second stood too
close beside it. It now enters by the east door, walks the aisle between the sedan and the lift and ends on a
three-quarter view of the lift from X 12.5. Car bodies get a 5 in, five-segment bevel so the extruded profile
reads as sheet metal.

Check batch (stage_e, first frames with the white balance). Kitchen, living, office, spine, lounge, bedroom all
read neutral: white plaster, olive island, oak, teal, oxblood, with the windows slightly cool. Kept 3800K.
Found and fixed from the same batch: the vanity mirror's white panel was the mirror backlight itself, aimed
into the mirror (rotation sign) and visible to reflection rays; all lights are now hidden from glossy and
transmission rays too, so no mirror or window shows a light panel. The living fire never showed its flames
because the firebox was recessed into the solid exterior wall (the flames sat inside the wall mesh); the fire
now sits in a 1.3 ft limestone chimney breast built as four pieces around the cavity, flush with the bookcase
fronts, the hearth bench in front of it. Two gallery frames hung across the Frame TV; the gallery moved up and
the TV art is dimmer. The roadster on the lift is stored under a fitted fabric cover (cloth pass): a
procedural car body will not pass as a photograph, a covered car will; the car bevel is 3 in. The garage shot
drifts along the east side and ends wide on the lift from X 15.5. The recovery suite's landing had no way in
(the spec's shower wall runs the full Y 20-28), so the shower's west wall stops at Y 22 and the dry path along
the south edge reaches the landing and the sauna; sauna strips and sconce about twice as bright. Hedges were
flat green boxes in every window; they carry a leafy texture and a subdivided, noise-displaced surface now.
Porch downlights were inside the canopy slab; moved below it. Mudroom downlights 14 W.

Preview run. The first block frames went blue: one white balance cannot serve the sidewalk and the kitchen.
Shots now carry white_balance_k (block and street 5600K, terrace dusk 4600K, bedroom morning 4200K, garage
4500K, the interiors keep 3800K) and the exterior exposures went back to 0.0 (street riding to +0.9 on the
porch). Stale frames from the September 2 preview (pre-furniture) were still in renders/frames and render.sh
skips existing frames, so they were deleted before the run reached those shots.
The fire's last tell: its trim frame was a solid slab across the glass, so the box stayed black through three
fixes (recess in a solid wall, solid interior, frame). It is four bars now; the flames read behind the glass and
reflect in the away-room glazing.
Web export: with the block the glTF passes 100 MB and the bake takes over half an hour, so export_web drops the
neighbourhood by default (--with-block keeps it). The export runs after the preview; two Blender processes do
not fit in 16 GB with this scene.

## Henry's morning review: cars, orientation, clipping

Cars. The extruded-profile cars are gone. car.py lofts a 12-vertex ring through side-profile stations sampled
every 0.7 ft (centre-line silhouette, shoulder line, body and roof half-widths as piecewise-linear keys per
kind), smooths it with two levels of Catmull-Clark under creased shoulder, sill and roof-edge loops, cuts the
wheel arches with boolean cylinders after the subdivision, and adds tyres, alloy rims with five spokes, a glass
band with pillars, windshield and rear glass, head and tail lights, grille, bumpers, mirrors off the A-pillar
glass line, handles, door seams and a plate. Sedan, SUV and roadster tables; the roadster stays under its
cover. Car paint has a clearcoat. Garage lift, cars and ladder moved off the bench; the garage shot ends behind
the cars from the doors.

Orientation. tools/model_facing.py measures a model's forward direction from its geometry (the backrest
centroid sits behind the seat centre): every Poly Haven chair faces -Y at rot 0, the procedural lounge and
dining chairs too, the procedural task and kid chairs face +Y. Against that: the living armchairs faced the
south-west corner, the away-room lounge chair the cabinet, both kid desk chairs away from their desks, the
loft chairs away from the puzzle table, the bedroom reading chair the corner, the office task chair the room
instead of the desk, all four games-table chairs and both island-table-end chairs outward. All corrected.

Clipping. build_scene --audit tags every object with its staging entry (Stager.build_all) and reports, per
entry AABB, overlaps with other entries (contact from above excepted), penetration into wall boxes deeper than
0.15 ft, and centres outside the entry's room; exterior fixtures are exempt from the room test. The first run
was garbage: object matrices and bound boxes are stale until view_layer.update(). tools/audit_views.py writes
a bird's-eye pose per room (59 views) for the eye check.

Audit findings, second pass. Model prototypes in the hidden asset library were being counted (they sit at
the origin, so every entry that first loaded a model had a bounding box stretched to the origin); excluded.
Poly Haven plant and prop files carry several variants side by side and the importer joined them all: the
pachira was 21 ft wide, the calathea 27 ft; load_proto now keeps the largest piece and whatever touches it
(known multi-piece sets exempt), which also revealed that rubber_boots imports as a single boot, so pairs are
two placements. gen_shelving_unit placed its crates and posts without rotating their offsets, so rotated
units spilled through walls (storage and garage). The water closet was 1.75 ft clear between the partition
face and the exterior wall, too narrow for any toilet; the partition moved to X 38.25 for 2.5 ft clear
(code minimum 30 in), the door with it. The games table corner is 5.75 ft between the pit and the wall, so
the table keeps two chairs. Garage shelving moved to the east wall clear of the lift posts, the ladder, broom,
shovel, salt and hose to the north-west corner; the bench's low shelf is off where the rolling chest parks.
Kitchen columns stop at Y 29.7, short of the column line. Bedroom B nightstand and desk separated, gym plate
tree off the dumbbell rack, laundry tall cabinet off the washer, the closet safe cabinet and the suitcase on
top of the wardrobe removed, primary nightstands and bench clear of the platform overhang.

Bird's-eye review, 59 rooms (renders/audit/stills/au_*). Found by eye, not by the numbers: the living sofa's
throw pillows were placed on the back cushion's zone instead of against its front face, so they sat on top
of the back (Henry: "the pillows on the couch are floating?"); the pillow generator now takes evenly spaced
slots along the back with jitter, leaning ones against the back, flat ones a little forward, so pillows never
pile onto each other (the daybed had a heap). The lab stool stood alone on the rug; it is at the workbench.
The kid bath step stool stood mid-floor; it is beside the vanity. The stair-hall pendant hung through the top
of the centre wall; it hangs over the arrival zone. The bar lamp sat in the bar sink (the spec puts both at
the counter's south end); the lamp is on the back bar. Toilets were rounded boxes; they are elongated bowls
with a seat ring. The stuffed animal was two ellipsoids; it is a small bear. The beanbag was a balloon; it
slouches under a coarse noise. Kid rugs are striped per the spec. Throws read as planks: the cloth pass now
sizes its wave amplitude from the second-smallest dimension and subdivides large pieces finer. Rooms whose
corner pose landed inside a cabinet (kitchen, closets, rack closet, work corridor, laundry) get a custom pose
in a follow-up set. Two false alarms recorded so I do not chase them again: bikes look flat from a steep
bird's-eye because a vertical wheel foreshortens to an ellipse (checked numerically: wheels stand 2.2 ft
tall), and the audit's per-entry union box makes any room-filling entry (kitchen run, garage bench with its
pegboard and air line, lift with its runways) "overlap" everything near it.

Verification set (renders/audit_x). The kitchen's south wall is a run of full-height cabinets, so the boombox,
books and cutting board that sat at Z 3 there were floating on the doors; removed, the board is on the island.
The spec's 16 ft maple stood in the bed against the garage's south wall and its crown grew through the garage
roof; it is in the yard between the terrace canopy and the spa. The hose reels hung over the lift bay; they
are over the bench aisle. The garage shelving unit stood in front of a door wherever it went (two 9 ft doors
leave no 6 ft of wall); dropped, storage is the pegboard and under the bench. The garage shot ends square on
the lift from the door line. Toilet seats are white and the roll is on the side wall. The upstairs laundry had
no light at all. Car wheels were asymmetric (left tyres stood proud of the body, right ones recessed, spokes
floated outside the right rims); mirrored per side. Cars pass at room scale in the garage frames.

## Dimension audit (Henry: "realistic and code compliant... would it be pleasant to live in? I don't want it cramped")

Measured every room, door, stair and fixture against IRC/IPC minimums from plan.json and staging.json (the numbers,
not the renders). Generous everywhere that matters: living 20 x 16, kitchen 14 x 17, primary 14 x 16 with a 10 x 9
bath and 10 x 8 closet, kids' rooms 181 and 225 sq ft with two egress windows each (sills 30 in), 9 to 9.5 ft
ceilings, 6 ft halls, 3 ft doors, gym 22 x 20, lounge 22 x 18, garage 24 x 30. Five failures, all fixed:

1. Stair flights were 30 in clear: the 6 ft core less the partition face and the 6 in centre wall left 2.5 ft per
   flight (IRC R311.7.1 wants 36). The core is now X 28-35: flights 28.25-31.25 and 31.75-34.75, centre wall at
   31.5, landings 7 ft, tower 7 ft, clerestories S5/S9 recentred, the well opening 7 ft. The foot came out of the
   main-floor laundry (7 ft wide now, elevator closet X 35-38), the upstairs laundry closet and the battery room.
   Basement and upstairs shots re-centred on the wider flights (X 33.25 down, 29.75 up).
2. The laundry's only door was from the primary bath, and with the WC widened the shared wall no longer took a
   door at all. It now opens off the stair-hall arrival zone (X 35, Y 9.65-12.15). The chute moved to the NE corner
   of both laundries (X 40-41) so its hopper is out of the door swing; the upstairs double doors moved west to clear it.
3. WC toilet had 7 in in front of it: the 30 in compartment had the bowl pointing across the short way. Partition
   moved to X 37.75 (36 in clear), bowl on the north wall facing down the 4.5 ft length, 18 in each side, 30 in in front.
4. Powder toilet was 6 in from the vanity across a 3.5 ft room. Partition to X 19 (4.5 ft clear; the coat closet is
   3 x 6 with a 2 ft door), toilet on the east wall at the south end, 2 ft clear in front, basin on the west wall north
   of the clear zone, door recentred at X 17 so its swing clears both.
5. Island seating: six chairs on both sides of a 3.5 ft island left 24 in behind the west chairs (the pantry door
   swung into them) and 28 in behind the east chairs in the cooking aisle. Island is 3 ft at X 13-16, 3 ft off the
   tall south run, sink and dishwasher on the work end, four chairs (three west, one at the north end), 36 in behind
   them, 42 in cooking aisle; the pantry door swings into the pantry (details.build_door honours swing="out" now,
   which the WC door had been asking for all along).
6. Coffee table (3.5 ft across) sat 10 in off the sofa; moved to 16 in.

Left open for Henry (README "Dimensions and code"): no dining table for more than four inside, no kitchen window,
the 3 x 3 elevator stack is a placeholder.

Verification of the dimension pass (renders/audit_y, 14 views at 960x540): the flights read at their new width
on all three levels; powder and WC show the clear floor in front of each bowl; the island from both aisles and
from the main shot at t 15; the sofa with the coffee table gap. Two things the views caught: the stair pendant
I had moved "clear of the centre wall" was hanging at head height on the second-floor landing walkway (it is in
the two-storey well over the west flight now, canopy on the upper ceiling), and the range hood's full-width
light lens blew out white under the camera at t 15 (two small lamps now). Audit after the plan changes: 72
findings, the four new ones from the moved walls fixed (coats, laundry basket and runner, cutting board); all
eight camera paths clear.

Web export. The furnished export came out at 331 MB: the block's 48 parkway trees are instanced outside the
neighbourhood collection so the "drop the block" step missed them, and decimation only looked at prototype
meshes. The bake also took an hour because every tile bake made Cycles synchronise the whole house scene.
export_web.py now bakes in a one-plane scene (149 tiles in under a minute), keeps the tiles in web/_tiles as a
cache (--rebake to refresh), drops trees off the lot, and decimates each heavy mesh datablock once so instances
stay shared. Result 65 MB (40 MB geometry, 21 MB textures, 6,045 meshes), no longer committed; tools/viewer_bundle.py
packages web/ as a zip with double-click starters and as one self-contained HTML.

Viewer delivery (Henry: "a format I can download and walk around in"). dist/housetour_viewer.zip, 20.8 MB after
Draco: geometry 40 MB to about 6 MB, model textures at 384 px. Headless Chromium reaches ready in about ten
minutes under software GL (the 6,045 draw calls are the cost; merging procedural meshes by material would be
the next step), with no page errors; a Mac GPU loads it in well under a minute. macOS refuses the unsigned
.command on a double-click; right-click, Open, or serve the folder by hand. The 27 MB house.glb is tracked again
so a clone of the branch walks out of the box.

## Realism pass (Henry: "so much of this stuff looks ultra low poly and extruded... audit everything and maximize detail")

Survey. 114 more Poly Haven models fetched (224 wanted, 223 on disk) and every model rendered to a thumbnail sheet
(tools/model_sheet.py, renders/model_sheet). What fits a 1950s-modern house: the covered car for the lift, the
slatted walnut cabinet and the mid-century drawer unit, school desk chairs for the kids, cube shelves, the
orange task lamp, chevron throw pillows, and a long list of props (lab gear, tools, cleaning bottles, food,
garden things). What does not: every sofa (a French settee, a chesterfield, a carved traditional three-seater),
the nightstands (one carved, one farmhouse), the chandeliers and the two CRT televisions; those pieces stay
procedural and got better geometry instead.

Soft goods (softgoods.py). The box-plus-noise cloth pass was the biggest tell. New grid-mesh primitives: a pillow
with domed faces meeting at a seam, pinched corners and a few creases; a slab with a flat top, rounded rim, puff
and a sat-on sag; a duvet as one surface with a rounded turn over the mattress edge, swaying drops and a plump
folded roll at the head; a drape over an edge (throws over arms and bed feet); a towel over a bar with a short
back and long front; a towel stack; a pinch-pleated curtain panel. Wired into gen_cushions (pillows now lean back
against the backrest with the puffy face to the room), the platform bed, the kid beds (drops only on sides not
against a wall), window seats, benches, daybed, ottoman, lounge chair, sofa cushions, the lounge pit and every
towel bar and warmer. The bevel/cloth pass skips them (sg_ prefix). Curtains on the primary bedroom's two
windows on brass rods; the reading corner's floor lamp moved off the curtain line.

Architectural detail (archdetail.py, from plan.json alone). A rocker switch 48 in high on the latch side of every
door in every room it serves, duplex outlets 15 in high about every 10 ft of usable wall (closets, the kitchen
run and mechanical rooms excepted), a linear slot diffuser in the ceiling of every room over 60 sq ft, a return
grille in each hall, smoke detectors in bedrooms and halls, a thermostat per floor.

Materials. Painted walls carry the ambientCG eggshell roller texture (colour still from rgb); textiles moved to
finer sets (terry towels, knit and wool throws, linen bedding); brass and blackened steel got brushed-metal
normals; ceramics a glaze map; new leather sets, tinted glass for oil bottles and candle jars, plastics and chrome
for the small props.

Clutter (tools/staging_clutter.py, 110 pieces). Keys bowl and glasses on the entry console, post on the vestibule
bench; oil bottles, knife block, paper towels, a spoon, fruit on the board, a tea set and bananas on the nook;
wine and bread in the pantry; a remote, magazines, a camera, a mug and a candle in the living room; candlesticks
and an elephant in the away room; soap pumps, folded towels, bath mats and shampoo in every bath; alarm clock,
notebook, glasses, phone and water glass on the nightstands, a folded knit throw on the bench, a hamper; cleaning
bottles, towel stack, broom and dustpan in the laundry; task lamp, notepads, pens, stapler, mug and phone on the
office desk; laptop, circuit board, multimeter, chemistry set, microscope, bunsen burner, magnifier and a radio
in the lab; chevron pillows, treasure chests, footballs, cube shelves, a chalkboard, a board game and a console
in the kids' rooms; a dartboard, console and blanket basket in the lounge; crates and a suitcase in storage; and
the garage bench dressed with tools, cans, crates, a stool, a fire extinguisher, hand truck, tire pump and
jerrycan. Sofa turned to face the fire: it had been sitting with its back to the fireplace and its own coffee
table since the first staging.
