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
