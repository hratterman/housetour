# House walkthrough

A data-driven Blender pipeline that builds Henry's house from `plan.json`, stages it with textures,
architectural details, furniture and lighting, flies a camera through two shots, and stitches a short
walkthrough video. Everything is regenerated from JSON; nothing is hand-modeled in a .blend file.

- `renders/walkthrough_preview.mp4` is the committed check render (640x360, 32 samples, every 3rd frame, 8 fps).
- The final render (1280x720 or 1920x1080, every frame, 24 fps) is a one-command job on a machine with a GPU.
  See "Rendering on the Mac Mini" below.

## What you need

- Blender 4.2 LTS or newer (4.0 works but the Ubuntu apt build lacks the denoiser; use the official build).
- ffmpeg.
- Python 3 with Pillow (`pip install pillow`) for the contact sheet. Blender's own Python runs the scene script.
- About 500 MB of CC0 assets from Poly Haven and ambientCG, fetched by `tools/fetch_assets.py` (cached in `assets/`,
  gitignored; every file is recorded with its source URL and license in `assets/manifest.json`).

## Quick start

```sh
python3 tools/fetch_assets.py          # one time: downloads textures, models and the sky HDRI into assets/
PREVIEW=1 ./render.sh                  # fast check: both shots, stills, contact sheet (about 2.5 h on a 4-core CPU)
./render.sh                            # final: 1280x720, 128 samples, every frame
```

Outputs land in `renders/`: `walkthrough.mp4` (or `walkthrough_preview.mp4`), per-shot mp4s, `frames/<shot>/`,
`stills/`, `contact_sheet.png`, `timing_<shot>.json`, and `scene.blend` (the built scene, for inspection in the UI).

### Rendering on the Mac Mini

`render.sh` auto-detects `/Applications/Blender.app` and uses Metal on macOS. Nothing else changes.

```sh
brew install ffmpeg
pip3 install pillow
python3 tools/fetch_assets.py
./render.sh                                   # 1280x720, 128 samples, Metal
RES=1920x1080 SAMPLES=256 ./render.sh         # the 1080p version the brief asks for
```

Time a single frame first if you want a total before committing:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -P build_scene.py -- \
    --still main_floor:9.2:test --res 1920x1080 --samples 256 --device METAL
```

The build itself takes about 15 s; the log prints the per-still render time. Multiply by 480 frames
(12 s + 8 s at 24 fps). If a frame is slower than about 90 s, `SAMPLES=160` is a fine compromise; denoising
carries it. Frames that already exist are skipped, so a killed render resumes where it stopped.

## The two shots

| shot | length | path |
| --- | --- | --- |
| `main_floor` | 12 s | street, through the front door, foyer, down the oxblood spine, into the kitchen past the island, into the living room ending on the fireplace wall and the rear glass |
| `basement` | 8 s | gym looking through the glass wall, into the lounge, along the rim of the sunken pit, ending on the bar |

Both are keyframed from `plan.json` (`shots`), Bezier with clamped handles, a Track To target with a slow
noise drift on the target for a faint handheld feel. The camera path is sampled every frame against every
mesh; the build refuses to render silently if the camera is within 0.3 ft of geometry (it logs a warning
with the first frame and object).

## Repository layout

```
plan.json           the architectural program: rooms, openings, pit, features, shots, stills, views, lighting
materials/materials.json   material library keyed by name (flat RGB for Phase 1, PBR sets + procedural overlays for Phase 2)
staging.json        furniture and objects: CC0 model placements and procedural generators, per room
build_scene.py      Blender entry point: builds, keys the camera, renders (CLI below)
geom.py             geometry helpers (boxes, prisms, cylinders, booleans, lights)
materials_pbr.py    PBR materials with world-space box projection at physical scale, procedural wallpapers, terrazzo strips, art
details.py          door casings and doors, window frames, glass, mullions, portals, baseboards, beams, picture lights, stair, brick shell, roof, terrace
staging.py          model import (glTF, joined, instanced) and about 35 procedural generators (sofa, credenza, sputnik, books, frames, fire, sauna, bar, gym...)
lighting.py         per-floor ceiling fills, practical lights registered by staging, HDRI sky and sun, per-shot exposure
render.sh           orchestration: shots, ffmpeg stitch with a 12-frame cross-dissolve, stills, contact sheet
tools/stills.py     renders the named stills (camera-path frames) or the free-pose room views
tools/contact_sheet.py     tiles PNGs into one labeled sheet
tools/fetch_assets.py      downloads and records the CC0 assets listed in assets/wanted.json
notes/log.md        running log: every plan edit, every bug, every measured timing
```

### build_scene.py CLI (after `--`)

```
--plan plan.json          program to build
--shot NAME|all|none      render a shot, all shots, or just build
--still SHOT:T[:NAME]     render one frame of a shot at time T seconds
--view NAME:px,py,pz,lx,ly,lz   render one frame from a free pose (feet)
--res WxH  --samples N  --frame-step N  --frame-start N  --frame-end N
--device CPU|METAL|CUDA|OPTIX|HIP
--stage phase1|phase2|auto    box model, staged house, or auto (phase2 when staging.json exists)
--exposure EV             override the plan / shot exposure
--motion-blur on|off  --dof on|off
--out DIR                 output root (default renders/)
--no-blend                skip saving renders/scene.blend
```

### render.sh environment

`PREVIEW=1`, `RES`, `SAMPLES`, `STEP`, `DEVICE`, `BLENDER`, `STAGE`, `SHOTS`, `OUT`, `SKIP_FRAMES=1` (stitch and stills only).

## How the house is built

- Feet in the JSON, meters in Blender. X runs across the lot (garage side at 0), Y from the street to the back
  yard, Z up with the main floor at 0 and the basement at -10.
- Each room is a floor slab, a ceiling slab and four walls. Walls shared with a neighbor are half thickness inside
  each room; exterior walls are full thickness. Slabs are split the same way so the basement ceiling and the main
  floor do not occupy the same volume.
- Openings find their walls by bounding-box overlap plus wall axis, then boolean-difference them (Exact solver, applied).
  Phase 2 reads the same list to add casings, doors left open at 80 degrees, window frames, glass, mullions, sills and
  light portals.
- The pit is cut from the lounge floor with a lower slab, walnut lining with a lip, cushions on three sides and an LED
  strip under the lip.
- Features are boxes from the plan; staging replaces the ones that become real objects (sofa, bed, bookwalls, rack,
  TV panel, sauna front) and leaves the rest.
- The stair descends from the north end of the spine into the lounge through a well cut in both slabs (14 risers).
- Materials are world-space box-projected at a physical size, so adjacent objects tile continuously and nothing is UV mapped.
  Painted walls use the plaster normal map under a flat color. Terrazzo has a procedural brass strip grid. Wallpapers,
  the tile backsplash, the spine runner and all framed art are procedural, so no real artwork is used.
- Lighting: a dim 2700K ceiling fill per room (35 percent of the plan wattage on the main floor, 130 percent in the
  windowless basement), then practicals: every lamp, pendant, picture light, the fire, the sauna, the under-cabinet
  strips, the bar shelves, the pit cove and the gym panels each carry a small light. Daylight is a Poly Haven late
  afternoon sky plus a sun lamp entering through the rear glass.

## Measured render times

All on the build VM: 4 CPU threads, Blender 4.2.11, denoised, adaptive sampling.

| what | resolution / samples | per frame |
| --- | --- | --- |
| Phase 1 boxes, main floor shot | 640x360 / 32 | 19.8 s mean over 96 frames |
| Phase 1 boxes, basement shot | 640x360 / 32 | 25.0 s mean over 64 frames |
| Phase 2 staged, main floor shot | 640x360 / 32 | 29.9 s mean over 96 frames (47.9 min) |
| Phase 2 staged, basement shot | 640x360 / 32 | 27.0 s mean over 64 frames (28.8 min) |
| Phase 2 staged, review stills | 640x360 / 48 | 58 to 67 s |
| Phase 2 staged, room views | 480x270 / 24 | 38 to 54 s |
| scene build, Phase 1 | | 0.9 s, 172 objects |
| scene build, Phase 2 | | about 14 s, about 1950 objects |

`PREVIEW=1 ./render.sh` end to end (both shots, stills, sheet) took 83 minutes on this VM.
Extrapolated from those, a full Phase 2 render at 1280x720 / 128 samples on this VM is roughly 6 to 8 minutes a
frame (4x the pixels, 4x the samples, adaptive sampling helping a little), so 45 to 60 hours for 480 frames. That is why the final render is Jamie's job on the Mac Mini: Cycles on
Metal on an M-series chip is typically 8 to 15 times faster than these four cores, which puts 720p at a few hours
and 1080p / 256 samples at an overnight run. Measure one frame first (command above) and multiply.

## What I would change next

1. Replace the procedural trees and hedges outside with Poly Haven's `shrub_*` and `jacaranda_tree` models; the
   exterior reads as a house but the planting is crude.
2. Swap the procedural sofa for a modeled one with real cushions and piping; it is the closest large object to the
   camera at the end of the main shot.
3. Real glass in the picture frames and a slight bevel on every casing and cabinet edge; hard 90-degree edges are
   the biggest remaining "render" tell at 1080p.
4. Open the front door with an animated swing during the first two seconds instead of leaving it standing open.
5. A third shot for the exterior approach and a fourth for the bedroom wing, both of which are already furnished.

## Licensing

All downloaded assets are CC0 1.0 from polyhaven.com and ambientcg.com and are listed with URLs in
`assets/manifest.json`. All artwork on the walls, wallpapers and textiles are procedural.
