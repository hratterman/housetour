# House walkthrough

A data-driven Blender pipeline that builds Henry's house from `plan.json`, furnishes and lights it from
`staging.json`, sets it on a North Shore village block, flies a camera through eight shots and stitches a
walkthrough video. Everything is regenerated from JSON and Python; nothing is hand-modeled in a .blend file.

- `plan.json` (rooms, openings, stairs, roof, site, neighbourhood, lighting, shots) is written by
  `tools/make_plan.py` from `housemasterspec.md`. Do not hand-edit it.
- `staging.json` (530 placements: 72 CC0 model instances, 415 procedural pieces, finishes and lights) is
  written by `tools/make_staging.py` from the room-by-room lists in `tools/staging_main.py` and
  `tools/staging_rest.py`. Do not hand-edit it either.
- `renders/walkthrough_preview.mp4` is the committed check render. The final render is a one-command job on a
  machine with a GPU; see "Rendering on the Mac Mini".

## What you need

- Blender 4.2 LTS (4.2.11 is what everything was built with; 4.3+ should work, 4.0 lacks the denoiser in the
  Ubuntu apt build, so use the official download).
- ffmpeg.
- Python 3 with Pillow (`pip3 install pillow`) for the contact sheet and the generated screen textures.
  Blender's own Python runs the scene scripts.
- About 1.1 GB of CC0 assets from Poly Haven and ambientCG, fetched once by `tools/fetch_assets.py` into
  `assets/` (gitignored). Every file is recorded with its source URL and licence in `assets/manifest.json`.

## Quick start

```sh
python3 tools/fetch_assets.py          # one time: textures (4k for the hero surfaces), 110 models, the sky HDRI
PREVIEW=1 ./render.sh                  # fast check: all eight shots, stills, contact sheet
./render.sh                            # final: 1280x720, 128 samples, every frame
```

Outputs land in `renders/`: `walkthrough.mp4` (or `walkthrough_preview.mp4`), per-shot mp4s,
`frames/<shot>/`, `stills/`, `contact_sheet.png`, `timing_<shot>.json` and `scene.blend` (the built scene,
for opening in the Blender UI).

## Rendering on the Mac Mini

`render.sh` finds `/Applications/Blender.app` and uses Metal on macOS. Nothing else changes.

```sh
brew install ffmpeg
pip3 install pillow
python3 tools/fetch_assets.py
./render.sh                                   # 1280x720, 128 samples, Metal
RES=1920x1080 SAMPLES=256 ./render.sh         # the 1080p version the brief asks for
```

Time one frame first and multiply by 2,832 (118 s of shots at 24 fps):

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -P build_scene.py -- \
    --still main_floor:21:test --res 1920x1080 --samples 256 --device METAL
```

The log prints the build time and the render time for that frame. Frames that already exist are skipped, so a
killed render resumes where it stopped; `SHOTS="bedroom garage" ./render.sh` renders a subset. If a 1080p frame
is slower than about two minutes, `SAMPLES=160` is a fine compromise; the denoiser carries it.

Memory: the staged scene peaks near 8 GB of RAM while rendering. Do not run two renders at once on a 16 GB
machine.

## The eight shots

| shot | length | mode | path |
| --- | --- | --- | --- |
| `block` | 10 s | day | along the far sidewalk, the neighbours sliding past, settling on the house |
| `street` | 12 s | day | up the front walk to the porch, ending on the door; exposure rides from the sunlit walk into the shaded porch |
| `main_floor` | 26 s | day | vestibule, entry, the red gallery spine, kitchen, living room, ending on the away room |
| `basement` | 24 s | day | down the switchback stair, the hall, gym glass, recovery suite, lounge pit, bar |
| `upstairs` | 18 s | day | landing, lab, rack closet, work corridor, kid-zone hall, ending in the loft |
| `terrace_dusk` | 12 s | dusk | from the lawn across the terrace under the heaters toward the lit living room |
| `bedroom` | 8 s | morning | low eastern sun across the made bed, ending on the reading corner |
| `garage` | 8 s | day | in by the east door, up the aisle between the sedan and the lift, ending on the roadster |

All are keyframed from `plan.json` (`shots`): Bezier with clamped handles, a Track To target with a slow noise
drift for a faint handheld feel, and per-waypoint exposure where a shot crosses a big light change. Every path
is sampled every frame against every mesh (`--check-paths`) and all eight are clear at the current plan.

Each shot selects a lighting mode. `day` is the late-afternoon sky with the sun from the south-west. `dusk`
drops the sun to the horizon, tints the sky for blue hour, turns on the lamp posts and lights 40 percent of the
neighbours' windows. `morning` puts a low warm sun in the east. Modes live in `plan["lighting"]["modes"]`.

## Walk through it yourself (web viewer)

`web/` holds a first-person version of the staged house: WASD and mouse look, wall collision, gravity and
stairs, a minimap, teleport buttons, the lamps as real point lights. It runs in any desktop browser.

```sh
blender -b -P export_web.py -- --out web     # rebuilds web/house.glb from the same plan.json and staging.json
cd web && python3 -m http.server 8000        # then open http://localhost:8000
```

By default the export carries the house and its lot only; `--with-block` keeps the 25 neighbouring lots and their
trees (the file grows past 100 MB, too big to commit).

`export_web.py` bakes every procedural material to a tile at its physical size, generates matching
box-projected UVs, swaps the heavy tree models for light ones, decimates anything over 30k triangles and writes
a glTF binary plus `lights.json` and `plan_web.json`. The viewer loads three.js from jsDelivr, so it needs the
internet once; the house itself is local.

## Repository layout

```
housemasterspec.md    the brief this is built from
plan.json             the program: rooms, openings, stairs, pit, roof, site, neighbourhood, lighting, shots, stills, views
staging.json          furniture, finishes, fixtures and lights, per room
materials/materials.json   176 materials: PBR texture sets, procedural overlays (terrazzo strips, stripes, wallpapers, art)
build_scene.py        Blender entry point: build, key the camera, render (CLI below); the bevel, cloth and hedge passes
geom.py               geometry helpers, lights, colour temperature and white balance
details.py            casings, doors, windows, glass, mullions, portals, baseboards, beams, stairs
site_build.py         roof, tower, terrace, spa, catio, window wells, lawn, beds, hedges
neighborhood.py       the block: street, parkway trees, 25 lots in six period styles, alley garages, lamps, fences
staging.py            model import (glTF, joined, instanced) and the Stager: wall-face placement, the first 40 generators
gens2.py, gens3.py    the other 110 procedural generators (kitchen, baths, beds, gym, bar, garage, cars, exterior)
lighting.py           room fills, practicals, sun, clamped HDRI sky, modes, white balance
materials_pbr.py      box-projected PBR at physical scale, procedural overlays, shadow-transparent glass
render.sh             orchestration: shots, ffmpeg stitch with cross-dissolves, stills, contact sheet
export_web.py         bakes materials and exports web/house.glb for the viewer
tools/make_plan.py    writes plan.json
tools/make_staging.py writes staging.json from staging_main.py and staging_rest.py
tools/stills.py       renders the named stills and the free-pose room views, one build per lighting mode
tools/acceptance.py   spec section by section: present / partial / missing table into notes/acceptance.md
tools/audit_views.py  one bird's-eye pose per room, for an orientation and clipping review with --views-file
tools/model_facing.py measures a model's forward direction (Poly Haven chairs face -Y at rot 0)
car.py                the cars: lofted subdivision cage, wheel arches, glass band, lights, wheels
tools/fetch_assets.py downloads the CC0 assets in assets/wanted.json; tools/gen_textures.py draws the screen images
tools/contact_sheet.py, tools/floorplan.py, tools/web_screenshots.py
notes/log.md          the running log: every plan edit, every bug, every measured timing
notes/acceptance.md   the spec checklist
```

### build_scene.py CLI (after `--`)

```
--shot NAME|all|none      render a shot, all shots, or just build
--still SHOT:T[:NAME]     render one frame of a shot at time T seconds
--view NAME:px,py,pz,lx,ly,lz   render one frame from a free pose (feet)
--views-file FILE         JSON list of {name,pos,look} or {name,shot,t}: build once, render each to <out>/stills
--check-paths             key every shot, run the collision check, render nothing
--audit                   build, then write notes/audit_clips.md: entries overlapping each other, sunk into walls, outside their room
--res WxH  --samples N  --frame-step N  --frame-start N  --frame-end N
--device CPU|METAL|CUDA|OPTIX|HIP
--exposure EV  --motion-blur on|off  --dof on|off  --no-bevel  --no-blend
--out DIR                 output root (default renders/)
```

### render.sh environment

`PREVIEW=1` (640x360, 32 samples, every 3rd frame), `RES`, `SAMPLES`, `STEP`, `DEVICE`, `BLENDER`, `STAGE`,
`SHOTS`, `OUT`, `SKIP_FRAMES=1` (stitch and stills only).

## How the house is built

- Feet in the JSON, metres in Blender. X runs west to east across the lot, Y from the street to the back yard,
  Z up with the main floor at 0, the second floor at 10 and the basement at -10.
- Walls occupy the inside of the room lines: exterior walls 1 ft thick inward, partitions 3 in each side of
  the line. Openings find their walls by overlap and are cut with booleans; Phase 2 adds casings, doors, frames,
  glass, mullions and light portals from the same list.
- The stair core (X 28-34, Y 0-13) is a stacked switchback: two 3 ft flights at 7.5 in risers on 10 in treads,
  a landing against the street wall, a solid walnut centre wall, a glass guard on the well. A cedar tower with
  stacked clerestories rises 2 ft above the eave over it.
- Staging entries name a wall (`axis`, `at`, `face`) and the Stager shifts them to the finished face, so
  nothing wall-mounted is buried. Paint and wallpaper panels cut themselves around every door and window in
  their wall.
- Materials are world-space box-projected at a physical size, so adjacent objects tile continuously and nothing
  is UV mapped. Terrazzo has a procedural brass strip grid, the bedding its stripes, the office monitors a
  generated code editor. All wallpapers and all framed art are procedural, so no real artwork is used.
- After the build, three passes: a bevel on every edge (a quarter inch on the shell, 0.4 in on details, 1.2 in
  on soft goods, 5 in on car bodies); a cloth pass that gives pillows, duvets, throws and cushions a subdivision,
  a noise displacement and a level of smoothing; and a hedge pass that displaces the hedge boxes into foliage.
- Lighting: a dim ceiling fill per room, then a real light for every lamp, pendant, sconce, picture light,
  strip, screen and fire (about 240 lights), the sun lamp, and the HDRI sky with its baked sun disc clamped out
  so the sky strength only scales the diffuse sky. Window glass passes shadow rays, so sun and sky reach the
  interiors. Everything is rendered through a 3800K white balance, the way a camera set for the room lights
  sees it: lamps warm-neutral, windows slightly cool.

## Measured times

All on the build VM: 4 CPU threads, Blender 4.2.11, Cycles, denoised, adaptive sampling. The Mac Mini's GPU
will be many times faster on the render numbers; the build is single-threaded Python and will be perhaps
twice as fast.

| what | value |
| --- | --- |
| staged build (house, block, 530 placements, 10,900 objects) | 6.3 min |
| review still, 960x540, 48 samples | 150 to 230 s (interiors slower than exteriors) |
| memory while rendering | 7 to 8 GB |

The preview run's per-frame times and totals are in `renders/timing_<shot>.json` and in `notes/log.md`.

## What I would change next

1. The cars are a lofted subdivision cage with real wheels, glass and trim; they pass at room scale in an
   8 second shot. A modelled roadster would still beat them in a close-up, so the one on the lift stays covered.
2. The sofa and lounge chairs are box-built under the cloth pass; modelled seating with piping would be the
   next step up in the living room, the closest thing to the camera at the end of the main shot.
3. No cats: Poly Haven has no CC0 cat model, so they are logged and omitted rather than boxed.
4. The block's trees are Poly Haven's island trees; a proper oak and elm model would replace them one for one
   through the species table in `neighborhood.py`.

## Licensing

All downloaded assets are CC0 1.0 from polyhaven.com and ambientcg.com and are listed with URLs in
`assets/manifest.json`. All artwork on the walls, wallpapers and textiles are procedural.
