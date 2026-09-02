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
