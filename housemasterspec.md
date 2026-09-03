# The house: master build specification for Claude Code
"""Write plan.json from the master build specification (housemasterspec.md), room by room.
This document supersedes every earlier brief and the earlier `plan.json`. It is the single source of truth for the geometry, contents, materials, lighting, and camera work of the house. Build exactly what is written here. Where a number is given, use the number. Where a position is given, use the position. Where an item is listed, it must exist in the model and be visible when the camera passes it. Nothing here is a suggestion.
The spec is the source of truth; this file is its transcription into the program the builder reads.
If anything in this document is geometrically impossible as written (two objects occupying the same space, a door in a wall that does not exist), stop, log the exact conflict with coordinates in `notes/log.md`, and ask Henry before changing it. Do not silently simplify, merge, delete, or approximate.
than copied is flagged with "ASK:" and collected into plan["questions"] for Henry.
The pipeline requirements from the earlier brief still apply (data-driven Blender build, Cycles, milestones, review stills, commits, CC0 assets with a license manifest). This document replaces the earlier program and the earlier furniture manifest entirely; regenerate `plan.json`, `materials.json`, and `staging.json` from this document, room by room, and check each room off against section 12 before rendering it.
    python3 tools/make_plan.py            # writes plan.json
## 0. Conventions
import json
### 0.1 Coordinates and units

- Feet. Convert to meters in code (x 0.3048). Blender scene units metric. Every coordinate in this document is in house-relative feet.
- X runs west to east. X = 0 is the house's west wall face. X = 42 is the east wall face.
- Y runs south to north. Y = 0 is the house's front (street) wall face. Y = 46 is the rear (terrace) wall face. The street is south, the alley is north.
- Z is up. Z = 0 is the main-floor finished floor. Z = 9.5 is the main-floor ceiling. Z = 10.0 is the second-floor finished floor (6-inch structure). Z = 19.0 is the second-floor ceiling. Z = -10.0 is the basement finished floor. Z = -0.5 is the basement ceiling.
- Room bounds are written `X a-b, Y c-d`. These are wall centerlines for interior walls and the outer face for exterior walls.
- Openings are written by the wall they sit in, the position along the wall, width, sill height (above that floor's Z), and height. "Door" means sill 0 unless stated.
- Boxes are written `[x0, y0, x1, y1, z0, z1]` in absolute feet.

### 0.2 Walls
# ----------------------------------------------------------------------------- floors  (spec 0.1)
- Exterior walls 1.0 ft thick (brick veneer and framing). Model as 1.0 ft solid.
- Interior walls 0.5 ft thick, built as two 0.25 ft half-walls inside each adjoining room's bounds so shared walls tile without overlap.
- Wall height per floor: main 9.5, second 9.0, basement 9.5.
- All interior doors 7.0 ft tall unless stated; cased openings and pocket doors as dimensioned.
    "garage":   {"z": -0.4,  "h": 12.0},
### 0.3 Naming

Use the room names in this document as object and collection names. Every furniture object gets a name `room.item` (for example `living.sofa`, `lounge.pit.seat_west`). This lets Henry point at anything by name.
# Each room: name, floor, parts (list of rects, wall centerlines), finishes, light (fill watts), flags.
# Flags: void (no floor slab), no_ceiling, exterior_faces (override), label.
rooms = []
Allowed without asking: rounding a position by up to 3 inches to clear a wall; choosing a specific CC0 model where this document names a generic item; procedural stand-ins where no CC0 model exists (sized per this document). Everything else: ask.

def room(name, floor, parts, floorm, wall, ceil, light=60, **kw):
    if isinstance(parts[0], (int, float)):
        parts = [parts]
    r = {"name": name, "floor": floor, "parts": parts, "floorm": floorm, "wall": wall, "ceil": ceil, "light": light}
- 60 ft wide (east-west) by 170 ft deep (north-south). In house coordinates the lot runs X -9 to 51 and Y -30 to 140. Street at Y = -30 (sidewalk along Y -30 to -25, curb at Y -25). Alley at Y = 140, 16 ft wide, running east-west.
- The house sits centered-left: west side yard 9 ft (X -9 to 0), east side yard 9 ft (X 42 to 51). Front setback 30 ft (Y -30 to 0). The house occupies X 0-42, Y 0-46.
- Grade is flat at Z = -0.5 (finished grade 6 inches below main floor). Sidewalk at Z = -0.6.
- Mature trees: red oak at (-3, -22), trunk 2.5 ft diameter, canopy radius 22 ft, canopy base 14 ft up. Red oak at (36, -24), trunk 2 ft, canopy radius 18 ft. Sugar maple at (48, 20), trunk 1.5 ft, canopy radius 14 ft. Honey locust at (30, 110), canopy radius 16 ft. Use CC0 tree models or procedural canopies; autumn foliage for the street shots.
- Neighbors: hint a 1920s brick two-story on each side, set back 30 ft, 35 ft wide, gabled, 20 ft to eave, at X -55 to -20 and X 60 to 95. Low detail, they exist to frame the street.
# --- main floor (spec 3, table)
room("gear_closet", "main", [0, 0, 8, 6], "terrazzo", "plaster_warm", "plaster_warm", 30, label="gear closet")
room("vestibule", "main", [8, 0, 14, 6], "terrazzo", "walnut_panel", "plaster_warm", 50)
- Front walk: bluestone, 5 ft wide, from the public sidewalk at (10.5, -25) straight north to the porch step at (10.5, -7). Two 6-inch risers up onto the porch at Y -7 to -6. Snow-melt (no visible effect; note only).
room("coat_closet", "main", [18, 0, 22, 6], "oak_floor", "plaster_warm", "plaster_warm", 20, label="coat closet")
- Planting beds: 18-inch gravel band (gray river stone) along the entire house perimeter, 0 ft from the wall to 1.5 ft out. Outside the gravel, a 4-ft bed of low planting (grasses, ferns, a few boxwood mounds 2 ft round) along the front wall Y -5.5 to -1.5 between X 0-8 and X 22-42. Nothing taller than 3 ft within 6 ft of the house.
- Gas lantern: none. One bronze cylinder wall sconce at (13.5, 0, 6.5) on the brick beside the front door, warm light.
room("spine", "main", [22, 0, 28, 32], "oak_floor", "oxblood", "oxblood", 90, label="gallery spine")
room("stair_hall", "main", [28, 0, 34, 13], "oak_floor", "plaster_warm", "plaster_warm", 60, no_ceiling=True, label="stair hall")
room("laundry", "main", [[34, 0, 42, 6], [37, 6, 42, 9], [34, 9, 42, 13]], "terrazzo", "plaster_warm", "plaster_warm", 70)
room("elevator_closet", "main", [34, 6, 37, 9], "concrete_sealed", "plaster_warm", "plaster_warm", 10, label="elevator")
room("mudroom", "main", [[3, 13, 8, 16], [0, 16, 8, 21]], "terrazzo", "plaster_warm", "plaster_warm", 70)
- Post-and-beam canopy X 4-22, Y -7 to 0, roof at Z 10 (see 2.3). Three 8x8 cedar posts at (4, -6.5), (13, -6.5), (22, -6.5), from Z -0.5 to Z 10.
- Porch floor: bluestone, X 4-22, Y -6 to 0, at Z -0.2 (2 inches below the main floor threshold).
- Built-in bench: walnut slab 8 ft long, 1.5 ft deep, 1.5 ft tall, at [14, -1.5, 22, 0, 0, 1.5], backed against the brick to the east of the door. Two wool cushions on it (mustard, olive).
room("living", "main", [0, 30, 22, 46], "oak_floor", "plaster_warm", "oak_decking", 150, label="living room")
- Two infrared heaters: black bar heaters 3 ft long mounted under the canopy beam at (8, -1, 9.2) and (18, -1, 9.2), angled toward the bench.
room("primary_bath", "main", [[28, 13, 39, 22], [39, 16.5, 42, 22]], "terrazzo", "plaster_warm", "plaster_warm", 90, label="primary bath")
- Porch light: recessed warm downlights in the canopy soffit at (7, -3.5, 9.9) and (19, -3.5, 9.9).
room("suite_hall", "main", [28, 22, 31, 30], "oak_floor", "oxblood", "plaster_warm", 30, label="suite hall")
room("primary_closet", "main", [31, 22, 42, 30], "wool_carpet", "walnut", "plaster_warm", 80, label="primary closet")
room("primary_bedroom", "main", [28, 30, 42, 46], "wool_carpet", "plaster_warm", "plaster_warm", 90, label="primary bedroom")
- Roofed walk along the west side yard connecting the mudroom's side door at (0, 17) to the garage's pedestrian door at (-3, 64). Walk surface bluestone X -6 to 0, Y 15 to 64, at Z -0.4.
- Roof: flat cedar-and-steel canopy at Z 9.5 spanning X -6.5 to 0 (attached to the house wall on the east), supported on 6x6 cedar posts at X -6, every 8 ft from Y 16 to Y 64 (7 posts). Standing-seam charcoal metal roof, exposed 4x10 cedar beams every 8 ft running east-west.
- Windbreak: a cedar slat screen (1x4 verticals, 2-inch gaps) on the west side between posts from Z 0 to Z 7, for Y 30-64. Open from Y 15-30 so the mudroom door area breathes.
room("lab", "second", [[11, 6, 22, 16], [14, 16, 22, 22], [22, 6, 28, 13]], "cork", "plaster_warm", "plaster_warm", 120)
room("rack_closet", "second", [11, 16, 14, 22], "concrete_sealed", "plaster_warm", "plaster_warm", 15, label="rack")
room("work_corridor", "second", [11, 22, 22, 26], "oak_floor", "oxblood", "plaster_warm", 30, label="work corridor")
room("stair_well", "second", [28, 0, 34, 13], "oak_floor", "plaster_warm", "plaster_warm", 40, void=True, label="stair well (open)")
room("landing", "second", [22, 13, 42, 19], "oak_floor", "oxblood", "plaster_warm", 80)
- Bluestone terrace X 0-42, Y 46-62, at Z -0.3, three steps down from the living room threshold is NOT correct: the living room's lift-and-slide sill sits at Z 0 and the terrace at Z -0.3, a single 3.5-inch step. Bluestone in a random ashlar pattern, 2x3 ft average stone.
- Roofed section: the main roof's rear eave is extended over X 4-22, Y 46-58 as a post-and-beam canopy at Z 10.5, on two 8x8 cedar posts at (4, 57.5) and (22, 57.5). Same standing-seam charcoal roof and exposed beams as the porch.
- Under the canopy: outdoor dining table (walnut-look teak, 10 ft long, 3.5 ft wide) centered at (13, 52, 0) with eight chairs; ceiling fan at (13, 52, 10); two black infrared bar heaters under the beam at (8, 49, 10.2) and (18, 49, 10.2); recessed downlights in the soffit at (8, 51, 10.4) and (18, 51, 10.4).
- Grill counter: Roman brick counter along the east edge of the canopy, [22, 46.5, 30, 49.5, -0.3, 2.7], with a stainless built-in grill 3 ft wide centered at (26, 48) in the counter top, a stainless side burner, and a small under-counter fridge door facing south. Hood: none (open air).
- Gas and 240V stubs: represent as two small brass cover plates on the brick at (30, 50, 1) and (30, 50, 1.6). Note only.
room("kid_bath_tub", "second", [35, 19, 42, 28], "terrazzo", "tile_white", "plaster_warm", 50, label="tub room")
room("bedroom_b", "second", [[31, 28, 42, 37], [28, 37, 42, 46]], "wool_carpet", "plaster_warm", "plaster_warm", 80, label="bedroom B")
- Terrace lighting: warm 12V path lights (brass, 18 inches tall) at the terrace's east and west edges every 8 ft; string of round bulbs is NOT used (the spec's earlier mention was for the summer render only; omit).
room("linen", "second", [28, 33, 31, 37], "oak_floor", "plaster_warm", "plaster_warm", 10, label="linen")
room("bedroom_a", "second", [[0, 26, 11, 31], [0, 31, 14, 40]], "wool_carpet", "plaster_warm", "plaster_warm", 80, label="bedroom A")
room("closet_a", "second", [11, 26, 14, 31], "wool_carpet", "plaster_warm", "plaster_warm", 10, label="closet")
room("hedge_alcove", "second", [0, 40, 14, 46], "wool_carpet", "plaster_warm", "plaster_warm", 50, label="hedge alcove")
room("loft", "second", [14, 26, 22, 46], "oak_floor", "plaster_warm", "plaster_warm", 90)
- Beds: 4-ft planting along the terrace's north edge Y 62-66 across X 0-18 (grasses and a Japanese maple at (9, 64), 12 ft canopy); 3-ft bed along the east lot line X 48-51 for Y 0-100 (hedge, 6 ft tall, arborvitae or hornbeam, continuous).
- Privacy hedge at the rear: hornbeam hedge 7 ft tall along Y 100-101 from X 18 to 51.
room("gym", "basement", [0, 0, 22, 20], "rubber_floor", "plaster_warm", "plaster_warm", 260)
room("sauna", "basement", [0, 20, 8, 28], "cedar_sauna", "cedar_sauna", "cedar_sauna", 25)
room("recovery", "basement", [8, 20, 22, 28], "terrazzo", "plaster_warm", "plaster_warm", 90, label="recovery suite")
room("lounge", "basement", [0, 28, 22, 46], "wool_carpet_charcoal", "oxblood", "ceiling_dark", 90)
- Single-zone counter-current swim spa, 14 ft long by 7.5 ft wide, exterior shell height 4.5 ft, recessed so its rim sits 1.5 ft above the terrace. Position [30, 50, 37.5, 64, -3.3, 1.2] (rim top at Z 1.2). Dark charcoal acrylic shell, water surface at Z 0.9, water color teal-clear.
- Surround: a walnut-look composite deck rim 1.5 ft wide around the spa at Z 1.2, and a Roman brick wall (1 ft thick, 1.2 ft tall) on the north and east sides.
- Cover: insulated cover in charcoal, hinged, shown OPEN and folded back on the north end in the dusk shot, closed otherwise.
room("battery", "basement", [34, 0, 42, 13], "concrete_sealed", "concrete_sealed", "concrete_sealed", 60, label="battery room")
room("mechanical", "basement", [28, 13, 42, 34], "concrete_sealed", "concrete_sealed", "concrete_sealed", 120)
room("storage", "basement", [28, 34, 42, 46], "concrete_sealed", "plaster_warm", "plaster_warm", 60, label="storage / projects")
### 1.8 Catio
# --- garage (spec 7): one open volume, brick to Z 8 then cedar (handled by the exterior pass)
- Screened post-and-beam enclosure attached to the east wall of the primary bedroom: [42, 33, 48, 41, -0.5, 8]. 4x4 cedar posts at the four corners and one mid-span, cedar top plate, black insect screen on all exposed faces and the roof (roof is screen under a shallow standing-seam lean-to that covers the north half only). Bluestone floor. Two cedar shelves inside at Z 2.5 and Z 5 along the east screen, a cat tunnel (wood, 1.5 ft square section) connecting through the house wall at (42, 38, 0.2) with a flap.
- One small tree in a pot inside, one cat (see 11.5).
# ----------------------------------------------------------------------------- openings
# axis x: wall runs along X at Y=at; axis y: wall runs along Y at X=at. c = center along the wall.
openings = []
- Detached garage: see section 7. Position X -6 to 18, Y 64 to 94.
- Driveway apron: concrete, X -6 to 18, Y 94 to 100, then gravel-look concrete to the alley edge at Y 140 is NOT needed; the alley runs immediately north of a 6-ft apron. Model the alley as asphalt from Y 100 to Y 116 (16 ft) across the full lot width and beyond.
- Utility pole and overhead lines along the alley at X 52, Y 108, for realism in the rear shot.
- Trash enclosure: cedar-slat bin corral [18, 94, 24, 100, -0.5, 4.5] with three bins inside, east of the apron.
- Rear lighting: a bronze wall sconce on the garage's north wall each side of each door at Z 8, warm.

## 2. Exterior architecture

### 2.1 Massing

Two volumes:

- **The main level:** a single-story brick base occupying the full footprint X 0-42, Y 0-46, wall top at Z 9.5, with the front row Y 0-6 reading as a low entry band.
- **The upper volume:** a cedar-clad second story over X 0-42, Y 6-46 (set back 6 ft from the front wall), wall top at Z 19.0, under a low-pitched gable whose ridge runs east-west at Y = 26.

From the street you see the low brick entry band and porch canopy in front, the cedar volume rising behind it, the long window run on the second floor, and the deep eaves. The east and west ends show the cedar gable.

### 2.2 Main roof (over the upper volume)

- Gable, ridge along X at Y = 26, from X -4 to X 46 (4-ft rake overhangs at both gable ends).
- Pitch 3:12. Top of wall at Z 19.0; add a 1.0-ft deep eave fascia so the roof deck at the wall line is Z 19.5; rise over the 20-ft half-span is 5.0 ft; ridge at Z 24.5.
- Eaves overhang 4 ft to the south (eave line at Y = 2, Z 18.5 at the outer edge because the slope continues down over the overhang) and 4 ft to the north (eave line Y = 50). Exposed 4x12 cedar rafter tails every 4 ft along both eaves, visible from below, with a cedar T&G soffit.
- Roofing: standing-seam metal, charcoal, 16-inch panels with 1.5-inch seams. Ridge cap in matching charcoal.
- Skylights: two 3x4 ft flat skylights in the south roof plane over the landing at (26, 16) and (38, 16); one over the loft at (18, 40) in the north plane.
- Solar: optional layer, a flush 12-panel array on the south plane X 4-28, Y 8-22. Omit from the primary renders, include as a toggle.
- Direct-vent chase: cedar-clad chase for the living room's gas insert, [-1.5, 36, 0.5, 40, -0.5, 26], projecting 1.5 ft from the west wall and rising 1.5 ft above the roof deck it passes beside (it stands outside the upper volume's west gable wall at the main level and continues up along the gable wall to Z 26). Cap: black metal.
- Gutters: concealed within the fascia; two bronze rain chains at the north eave at (2, 50) and (44, 50) into stone splash basins.

### 2.3 Low roofs

- Front entry band X 0-42, Y 0-6 and porch canopy X 4-22, Y -7 to 0: one continuous shallow shed roof sloping from Z 10.5 at Y 6 (where it tucks under the upper volume's south wall) to Z 10.0 at Y -7. Standing-seam charcoal. Fascia 1.0 ft deep. East of the porch (X 22-42) the roof stops at Y -1.5 (an 18-inch eave). Exposed 6x12 cedar beams running north-south every 4 ft under the entire low roof, visible from the porch and inside the vestibule's ceiling only as beams above a plaster ceiling at 9.5 (the vestibule ceiling is plaster at 9.5; the beams are exterior only).
- Rear terrace canopy X 4-22, Y 46-58 at Z 10.5, same construction, fascia to Z 9.5 at the outer edge.
- Breezeway roof and garage roofs: see 1.4 and 7.

### 2.4 Exterior materials by surface

- All main-level exterior walls (Y 0 front, Y 46 rear, X 0, X 42) from grade to Z 9.5: Roman brick, 12 x 3.6 x 1.6 in faces laid in running bond with raked mortar joints 3/8 in, blend of warm sand, tan, and umber, 3 tones randomly mixed. Mortar warm gray.
- Upper volume walls Z 10-19 and both gable ends up to the roof: vertical cedar, 1x6 tongue-and-groove, clear-stained (honey), vertical joint lines every 5.5 in, a 1x4 cedar trim at outside corners.
- The band between Z 9.5 and Z 10 (floor structure) is a bronze-black metal flashing reveal 6 inches tall running around the upper volume where it meets the brick base below; where the upper volume sits back from the front wall (Y 6), the low roof meets it, so the reveal only appears on the east, west, and north walls.
- Window and door frames: bronze-black aluminum-clad, frames 2.5 in wide, glass slightly green-tinted, low reflection.
- Soffits: cedar T&G. Fascias: bronze-black metal.
- Porch, terrace, front walk, breezeway floors: bluestone.
- Garage doors, front door: see below.

### 2.5 Exterior window and door schedule

Every opening. Position is the wall coordinate of the opening's centerline; width; sill above the floor of the level named; height. Frames bronze-black unless stated. "Fixed" means non-operable; "awning" means top-hinged operable; "casement" side-hinged.

Main level, south wall (Y = 0):
- S1 Front door: X 9-13, sill 0, height 8.0. Solid walnut slab, flat, 3 in thick, with a full-height brass pull bar 4 ft long on the exterior at X 12.6, and one 8-inch square brass peep window at eye height.
- S2 Sidelight: X 13-14, sill 0, height 8.0, fixed, one pane.
- S3 Powder slot: X 15-17, sill 6.0, height 1.5, fixed, obscure glass.
- S4 Spine bench window: X 22.5-27.5, sill 0, height 8.5, fixed, one pane (a full-height 5-ft window). Interior bench in front, see 3.7.
- S5 Stair hall clerestory: X 29-33, sill 7.0, height 2.0, awning.
- S6 Laundry window: X 36-41, sill 5.0, height 2.5, awning, obscure.

Main level, west wall (X = 0):
- W1 Mudroom side door: Y 15.5-18.5, sill 0, height 7.0, half-glass door in bronze-black frame, walnut lower panel.
- W2 Living clerestory: none (the fireplace wall is solid). No other main-level openings on the west wall.

Main level, north wall (Y = 46):
- N1 Living lift-and-slide: X 3-19, sill 0, height 8.5, four 4-ft panels; the two center panels slide open. Render with the western pair open 4 ft in the terrace shot, closed otherwise.
- N2 Away room window: X 23-27, sill 2.5, height 5.0, casement.
- N3 Bedroom window: X 32-40, sill 2.0, height 6.0, fixed center 4 ft with casement flanks 2 ft each.

Main level, east wall (X = 42):
- E1 Laundry high window: Y 2-6, sill 6.0, height 2.0, awning.
- E2 Bath window: Y 15-18, sill 5.0, height 2.0, awning, obscure.
- E3 Closet window: Y 24-28, sill 5.0, height 2.5, awning, obscure.
- E4 Bedroom window: Y 36-42, sill 2.5, height 5.0, casement pair.
- E5 Cat tunnel: Y 37.5-39, sill 0.2, height 1.5, a cedar-framed cat door into the catio.

Second level, south wall (Y = 6):
- S7 Her office window: X 2-9, sill 2.5, height 5.0, fixed center with a casement at X 2-3.5.
- S8 Lab window run: X 13-27, sill 2.5, height 5.0, four fixed panes 3.5 ft each; the easternmost pane is a casement.
- S9 Landing clerestory: X 29-33, sill 6.5, height 2.0, awning (aligned above S5).

Second level, west wall (X = 0):
- W3 Her office: Y 9-15, sill 2.5, height 5.0, fixed with casement at Y 9-10.5.
- W4 Her office: Y 18-24, sill 2.5, height 5.0, same.
- W5 Bedroom A: Y 29-35, sill 2.5, height 5.0, casement pair.
- W6 Hedge alcove: Y 41-45, sill 2.5, height 4.0, casement.

Second level, north wall (Y = 46):
- N4 Hedge alcove: X 2-8, sill 2.5, height 4.0, fixed.
- N5 Loft window seat: X 15-21, sill 1.5, height 6.0, fixed center 3 ft, casements each side 1.5 ft.
- N6 Hall window: X 23-27, sill 2.5, height 5.0, fixed.
- N7 Bedroom B: X 34-40, sill 2.5, height 5.0, casement pair.

Second level, east wall (X = 42):
- E6 Landing window: Y 14-18, sill 3.0, height 4.0, fixed.
- E7 Kid bath (tub room): Y 21-25, sill 4.0, height 2.5, awning, obscure.
- E8 Bedroom B: Y 33-39, sill 2.5, height 5.0, casement pair.

Basement (window wells, all with a 4x4 ft galvanized well outside and a grate):
- B1 Gym: X = 0 wall, Y 4-8, sill 6.5 above basement floor, height 3.0 (egress).
- B2 Lounge: X = 0 wall, Y 36-40, sill 6.5, height 3.0 (egress).
- B3 Lounge: Y = 46 wall, X 16-20, sill 6.5, height 3.0.
- B4 Storage: Y = 46 wall, X 32-36, sill 6.5, height 2.5.

### 2.6 Exterior fixtures

- Soffit outlets: brass cover plates every 12 ft along the north and south eaves at Z 18.3 (note only, tiny).
- Switched holiday-light outlets: same plates.
- Downlights in the main eave soffit every 8 ft along the south eave, warm, on in dusk shots.
- Address numerals, sconce, mailbox slot: see 1.2.
- Rain chains: see 2.2.

## 3. Main floor (Z 0 to 9.5)

Floor plan summary. Every room listed with bounds in feet. Interior wall centerlines at the shared edges.

| Room | X | Y | Area | Floor | Walls | Ceiling |
|---|---|---|---|---|---|---|
| Gear closet | 0-8 | 0-6 | 48 | terrazzo | plaster | plaster |
| Vestibule | 8-14 | 0-6 | 36 | terrazzo | walnut | plaster |
| Powder | 14-18 | 0-6 | 24 | terrazzo | dark botanical wallpaper | oxblood |
| Coat closet | 18-22 | 0-6 | 24 | oak | plaster | plaster |
| Panel closet | 0-8 | 6-13 | 56 | concrete | plaster | plaster |
| Entry hall | 8-22 | 6-13 | 98 | oak | plaster | plaster |
| Gallery spine | 22-28 | 0-32 | 192 | oak | oxblood | plaster (oxblood) |
| Stair hall | 28-34 | 0-13 | 78 | oak | plaster | plaster |
| Laundry | 34-42 | 0-13 (less elevator closet) | 95 | terrazzo | plaster | plaster |
| Elevator closet | 34-37 | 6-9 | 9 | concrete | plaster | plaster |
| Mudroom | 0-8 | 13-21 | 64 (less litter closet) | terrazzo | plaster | plaster |
| Litter closet | 0-3 | 13-16 | 9 | terrazzo | plaster | plaster |
| Pantry | 0-8 | 21-27 | 48 | terrazzo | plaster | plaster |
| Kitchen | 8-22 / 0-8 | 13-30 / 27-30 | 262 | oak | plaster | plaster |
| Living room | 0-22 | 30-46 | 352 | oak | plaster + walnut | exposed walnut beams, oak decking |
| Away room | 22-28 | 32-46 | 84 | oak | olive geometric wallpaper | olive |
| Primary bath | 28-42 | 13-22 | 126 | terrazzo | terrazzo + plaster | plaster |
| Suite hall | 28-31 | 22-30 | 24 | oak | oxblood | plaster |
| Primary closet | 31-42 | 22-30 | 88 | wool carpet | walnut | plaster |
| Primary bedroom | 28-42 | 30-46 | 224 | wool carpet | plaster + wallpaper | plaster |

Total 1,932 sq ft.

All main-floor ceilings 9.5 ft. Baseboards: 3-inch walnut throughout except the gym, mechanical, and closets. Interior doors: flat-panel solid walnut, 7.0 ft tall, with aged brass lever handles, unless noted as pocket, glass, or cased opening.

### 3.1 Gear closet (X 0-8, Y 0-6)

Purpose: strollers, bikes for kids, seasonal gear. Door: 3 ft wide at X 8, Y 3 (opens from the vestibule). Contents: wall hooks at Z 5.5 on the north wall, a stroller [1, 1, 3.5, 4, 0, 3.5] (any CC0 stroller or a box stand-in), two kid bikes leaning on the west wall, a shelf unit [0.2, 0.2, 2, 5.8, 0, 7] with bins. One ceiling light. Not seen by the camera; keep low detail.

### 3.2 Vestibule (X 8-14, Y 0-6)

The air-lock. Front door S1 on the south wall; inner door: a full-glass door 4 ft wide in a bronze-black frame at Y 6, X 9-13, with a sidelight X 13-14. Walnut paneling on the east and west walls (vertical boards). Terrazzo floor with brass divider strips in a 3-ft grid. One brass globe pendant, 14-inch opal glass, hung at Z 8.0 over the center (11, 3). A walnut bench 4 ft long, 1.2 deep, 1.5 tall against the west wall at [8.2, 1, 9.4, 5, 0, 1.5], with a wool cushion. A brass coat hook rail on the west wall above the bench at Z 5.5 with three hooks (one jacket hanging). A 3x5 ft wool runner in oxblood and cream stripe. Door to the gear closet on the west wall at Y 3.

### 3.3 Powder room (X 14-18, Y 0-6)

Natalie's room. Door 2.67 ft at Y 6, X 16, opens from the entry hall, walnut, brass lever. Walls: dark botanical wallpaper, black ground with olive, oxblood, and mustard foliage in a large repeat (procedural is fine: a dark base with a scattered leaf pattern). Ceiling painted oxblood. Terrazzo floor. Wall-hung walnut vanity 2.5 ft wide at the west wall [14.2, 2, 15.2, 4.5, 2.6, 3.2] with a white ceramic vessel sink and a wall-mounted brass faucet; a round brass-framed mirror 2 ft diameter above at Z 5.5; two small brass sconces flanking the mirror at Z 6. Wall-hung toilet on the east wall at (17.4, 3) facing west, brass flush plate. Slot window S3 high on the south wall. A small brass shelf with a hand towel. One brass toilet-paper holder.

### 3.4 Coat closet (X 18-22, Y 0-6)

Door 2.67 ft at Y 6, X 20 from the entry hall. Rod at Z 6 with 12 coats, shelf above, shoes below. Low detail; door closed in all shots.

### 3.5 Panel closet (X 0-8, Y 6-13)

Door 3 ft at X 8, Y 9.5 from the entry hall (flat walnut, closed in all shots). Inside (for completeness only): main electrical panel and two lighting-control panels on the west wall, a smart panel monitor, a network conduit chase. Concrete floor, bare. Not rendered.

### 3.6 Entry hall (X 8-22, Y 6-13)

The foyer proper, opening to the spine through a cased opening 5 ft wide at X 22, Y 7-12 (walnut jambs 6 in wide, full height 8.5). Doors: vestibule glass door at Y 6 (X 9-13), powder at (16, 6), coat closet at (20, 6), panel closet at (8, 9.5), There is no door from this hall to the mudroom; the mudroom connects to the kitchen. Oak floor. Walls warm white plaster. Ceiling plaster.

Contents: a walnut console table 5 ft long against the north wall at [12, 12.2, 17, 13, 0, 2.7] with a ceramic bowl, a brass table lamp (on), and a stack of mail; above it a framed piece 3 x 2 ft centered at (14.5, 13, 5.5); a wool rug 6 x 9 ft centered at (15, 9.5); a brass globe pendant 16-inch at (15, 9.5, 8.2); a large potted fiddle-leaf fig in a terracotta pot at (9, 12, 0), 7 ft tall.

### 3.7 Gallery spine (X 22-28, Y 0-32)

The 6-ft-wide, 32-ft-long central hallway. Walls painted oxblood (deep red-brown, RGB 0.32, 0.08, 0.09), matte. Ceiling painted the same oxblood. Oak floor with a wool runner 3.5 ft wide running Y 3-31, pattern: cream ground with an oxblood and olive geometric border.

Openings, all listed with their room: entry hall cased opening at X 22, Y 7-12; stair hall cased opening 4 ft at X 28, Y 5-9 (walnut jambs, height 8.5); kitchen cased opening 6 ft at X 22, Y 13-19 (height 9.0); suite hall door 3 ft at X 28, Y 27-30, solid walnut with an acoustic seal (closed in shots).

Front terminus: the bench window S4 at Y 0, X 22.5-27.5, full height. In front of it a walnut window seat [22.5, 0.5, 27.5, 2.5, 0, 1.5] with a mustard wool cushion, one throw pillow (teal), and one cat asleep on it (this is the cat's location in the main-floor shot). Two books on the seat.

Rear terminus at Y 32: a solid wall (the away room's south wall). On it, one large framed piece 4 x 5 ft (portrait) centered at (25, 32, 5), lit by a picture light.

Picture rail: a continuous bronze rail at Z 9.0 along both long walls (X 22 face and X 28 face). Picture lights: brass cylinder picture lights 10 inches wide, mounted at Z 8.3, five on each long wall at Y 5, 11, 17, 23, 29 (west wall) and Y 3, 10, 17, 24, 31 (east wall, avoiding the openings). Each is an emissive warm source aimed down.

Art hang, deliberately unfinished: on the west wall (X 22 face) three clusters: cluster 1 at Y 1-6 (five frames, sizes from 10x12 to 24x30 in, salon-style, centers between Z 4 and Z 7); cluster 2 at Y 20-26 (seven frames, dense, mixed sizes); cluster 3 is a single 30x40 in piece at Y 29-31, center Z 5.5. Open wall between clusters. On the east wall (X 28 face): cluster at Y 10-16 (four frames), a single small piece at Y 22 (Z 5.5), and open wall elsewhere. Frames: brass and walnut, narrow; images procedural abstracts in the house palette, plus two black-and-white "photographs" (grayscale noise compositions). Total frames on the spine: 21.

One walnut console table 4 ft long, 1 ft deep, against the east wall at [27, 20, 28, 24, 0, 2.7] with a brass lamp (on) and a ceramic object. One floor lamp: none.

Ceiling: three recessed warm downlights on a dim setting at Y 8, 18, 28, center X 25. The room reads dim and warm with pools of light on the art.

### 3.8 Stair hall (X 28-34, Y 0-13)

The stair core. See section 6 for the full stair geometry; summary here:

- The AISLE is X 28-31, Y 0-13: oak floor, plaster walls, the cased opening to the spine on its west wall at X 28, Y 5-9 (4 ft wide, 8.5 tall, walnut jambs).
- The STAIR SLOT is X 31-34, Y 0.75-13.25: the up-stair rises northward from its bottom tread at Y 0.75 to the second-floor landing at Y 13.25; the down-stair descends southward beneath it from its top tread at Y 13.25 to the basement at Y 0.75. Standing in the aisle, you turn east and walk south to go up, or turn east and walk north to go down.
- The well over the whole stair hall (X 28-34, Y 0-13) is open two stories, from Z 0 to Z 19, with the south wall at Y 0 carrying clerestories S5 (Z 7-9) and S9 (Z 16.5-18.5). A bronze-post glass guard runs along the well's edges on the second floor. A brass 20-inch opal globe pendant hangs in the well at (31, 6.5, 14).
- Guard between the up-stair and the aisle: a walnut-and-glass guard 3.5 ft above the nosings along X 31 for the length of the run, with a walnut oval handrail on the east wall (X 34 face) for the up-stair and on the guard's stair side for the down-stair.
- Treads oak 1.5 in, closed oak risers, walnut stringers and skirt boards.
- No doors open into the aisle other than the spine opening; the laundry is entered from the primary bath (see 3.9), and the elevator closet from inside the laundry.
- Finishes: oak floor in the aisle, walnut paneling under the up-stair's underside where visible from the basement, plaster walls, plaster ceiling at Z 19 (the well's top), which carries the two landing skylights' light down the well.

### 3.9 Laundry (X 34-42, Y 0-13, less the elevator closet X 34-37, Y 6-9)

Door from the primary bath at Y 13, X 36.5 (3 ft, walnut, closed in shots). No other door. Terrazzo floor. Plaster walls. Windows S6 (south, high) and E1 (east, high). Contents: a front-load washer and dryer stacked on a raised walnut plinth with a drain pan against the east wall, machines [40, 8.5, 42, 11.5, 1.2, 6.8] on the plinth [40, 8.5, 42, 11.5, 0, 1.2]; a walnut folding counter 7.5 ft long, 2 ft deep, at [34.5, 0.5, 42, 2.5, 3, 3.1] under the south window with drawers below and a deep utility sink in its east end at (41, 1.5) with a brass faucet; a hanging rod above the counter at Z 6.5 from X 35 to X 41 with six hangers and two shirts; a tall walnut cabinet [37.5, 9.5, 39.5, 13, 0, 8] for supplies; the laundry chute terminus: a walnut hopper box [34, 11, 36, 13, 0, 4] with a canvas bin under a square opening in the ceiling at (35, 12) (the chute shaft, 1.5 x 1.5 ft, runs from Z 9.5 up to the second floor at Z 10); the elevator closet's door on the laundry side at X 37, Y 7.5 (2.5 ft, walnut, closed). Two recessed downlights, a 3 x 5 wool rug.

### 3.10 Elevator closet (X 34-37, Y 6-9)

Stacked closet, door from the stair hall at X 34, Y 7.5. Concrete floor, empty except a broom. Represents the future elevator shaft; ceiling has a removable panel. Closed in all shots.

### 3.11 Mudroom (X 0-8, Y 13-21)

The working entry. Doors: side door W1 at X 0, Y 17 (from the breezeway); door to the kitchen 3 ft at X 8, Y 14.5 (walnut); the litter closet at the southwest corner. Terrazzo floor. Radiant (note). Plaster walls.

Contents: locker bay along the north wall: four open walnut lockers each 2 ft wide, 1.5 deep, 7 tall at [0.5, 19.5, 8, 21, 0, 7] divided at X 2.5, 4.5, 6.5; each with a bench seat at Z 1.5, a hook rail at Z 5, a cubby above at Z 6; closed cabinet doors above from Z 7 to 9.5. Coats hanging in two lockers, shoes in the bench cubbies. Charging drawer: one drawer face at Z 2 in the east locker with a cable trailing out. A utility sink 2 ft wide in a walnut cabinet on the east wall at [6.5, 16, 8, 18, 0, 3] with a brass faucet. Package cabinet: a walnut cabinet [0.5, 16.2, 3, 17.5, 0, 4] beside the side door, with a parcel slot in its top. Cat feeding station: a walnut tray with two ceramic bowls and a small fountain at (3.5, 13.6, 0) against the south wall east of the litter closet. A wool runner 2.5 x 7 ft along the room. Two recessed downlights and one brass wall sconce beside the side door at (0.2, 19.5, 6.5).

### 3.12 Litter closet (X 0-3, Y 13-16)

A ventilated closet inside the mudroom's southwest corner. Cat door (8 x 8 in, wood flap) in its east wall at X 3, Y 14.5, Z 0.2-0.9; a full 2-ft service door in its north wall at Y 16, X 1.5 (closed). Inside: a covered litter box, a shelf with supplies, a small exhaust grille in the ceiling at (1.5, 14.5, 9.5). Closed; not rendered in detail.

### 3.13 Pantry (X 0-8, Y 21-27)

Door 3 ft at X 8, Y 24 (walnut, half-open in the kitchen shot). Terrazzo floor. Plaster walls. Contents: shallow walnut shelves (10 in deep) on the north and south walls from Z 1.5 to Z 8.5, five shelves each, filled with jars, boxes, tins, a stand of oils; a standing-height counter [0.5, 21.5, 2.5, 26.5, 0, 3.2] along the west wall with a toaster, a bread box, a coffee grinder on it and an outlet strip above; a freezer drawer unit [0.5, 21.5, 2.5, 23.5, 0, 2.9] built under the counter's south end (stainless drawer face); the island's extension leaves stored upright in a slot at [0.3, 26.2, 0.6, 26.9, 0, 3]. Two recessed downlights, a motion sensor.

### 3.14 Kitchen (X 8-22, Y 13-30 plus the nook X 0-8, Y 27-30)

The heart. Oak floor. Plaster walls warm white. Plaster ceiling. Openings: cased opening to the spine at X 22, Y 13-19 (6 ft wide, 9 ft tall, walnut jambs); mudroom door at X 8, Y 14.5; pantry door at X 8, Y 24; the north edge Y 30 is fully open to the living room from X 0 to X 22 except for a 1-ft square walnut-wrapped structural column at (8, 30) and a matching one at (22, 30) that also terminates the east wall. The ceiling beams of the living room stop at Y 30; the kitchen ceiling is flat plaster.

Cooking wall (east wall, X 22, Y 19-30), from south to north:
- Y 19-19.5: a 6-inch walnut filler.
- Y 19.5-22.5: induction range, 36-inch, black glass top, stainless body, in a run of flat-front walnut base cabinets; range top at Z 3.0. Above it a black steel range hood 42 inches wide, 3 ft above the cooktop (bottom at Z 6.0, top at Z 8.0), duct concealed in the wall above.
- Y 22.5-25: base cabinets, honed soapstone counter (dark gray-green, subtle veining) 1.25 in thick at Z 3.0, 25 in deep; flat-front walnut uppers from Z 5 to Z 8.5, 13 in deep, from Y 19 to Y 25 (interrupted by the hood). Under-cabinet LED strip along the uppers' bottom edge, warm, on.
- Y 25-27.5: paneled column freezer (walnut front, 30 in wide, full height to Z 8.5).
- Y 27.5-30: paneled column refrigerator (walnut front, 30 in wide, full height to Z 8.5).
- Backsplash: from the counter (Z 3) to the uppers (Z 5) along Y 19-25 and rising to Z 8 behind the hood: burnt-orange and cream patterned ceramic tile, 4 x 4 in, a geometric pattern (quarter-circle "moon" tiles arranged into circles is the reference); this is the kitchen's one loud surface.
- The east wall from Y 13 to Y 19 is the cased opening to the spine; no cabinetry there.

South wall (Y 13, X 8-22): a run of full-height flat-front walnut cabinets [8.25, 13.25, 22, 14.5, 0, 8.5] interrupted by the mudroom door at X 8 (the door is on the west wall, so this run is continuous from X 8.5 to 21.5): includes a walnut wall-oven stack at X 9-11.5 (steam oven at Z 3.5-5, convection oven at Z 5-6.8, warming drawer below), and tall pantry-style cabinets elsewhere. This is where small appliances live.

The island: total [12, 15, 15.5, 26, 0, 3] running north-south, 11 ft long, 3.5 ft wide.
- Work end, Y 15-21 (6 ft): base in olive-green painted flat-front cabinetry (RGB 0.32, 0.36, 0.20, satin), soapstone top at Z 3.0 overhanging 1.5 in; an undermount stainless main sink 30 in wide centered at (13.75, 18), with a brass bridge faucet mounted behind it at (13.75, 16.8), rising 1.5 ft. A dishwasher panel (olive) on the east face at Y 19-21. A pot filler: brass, at the cooking wall above the range at (22, 21, 5). Instant-hot tap: small brass at (13.2, 16.8, 3).
- Table end, Y 21-26 (5 ft): the island steps down to table height: a walnut slab table top 2.5 in thick at Z 2.5 (top face), 3.5 ft wide, cantilevered from the cabinetry over a walnut leg frame; six dining chairs, mid-century molded wood shell chairs in walnut with mustard upholstered seats: three on the west side at (11, 22), (11, 23.75), (11, 25.5) facing east, and three on the east side at (16.5, 22), (16.5, 23.75), (16.5, 25.5) facing west.
- Above the table end: the Sputnik chandelier centered at (13.75, 23.5, 7.5): brass central sphere 8 in, 18 brass rods of 16-20 in length radiating, each ending in a 2-in opal globe bulb (emissive, warm). Total diameter about 3.3 ft.
- On the counter: a wooden bowl of oranges at (13.75, 20, 3), a cutting board, a knife block is NOT on the island (keep it clean); a linen towel over the sink edge.

The nook (X 0-8, Y 27-30): the dessert corner. A honed white marble counter (Carrara-look, light veining) 8 ft long, 2.5 ft deep, at [0.5, 27.3, 8, 29.8, 0, 3] on walnut base cabinets with the marble top at Z 3.0, running along the south wall of the nook (which is the pantry's north wall). On it: a stand mixer (pale green enamel) at (2, 28.5, 3), a cake stand with a glass dome and a cake at (5, 28.5, 3), a marble rolling pin, a canister set. A brass prep sink 15 in at (6.5, 28.5) in the marble with a small brass faucet. Above: open walnut shelves at Z 5.5 and Z 7 along the south wall holding ceramics (mustard, teal, cream). The nook's west wall (X 0) is solid; a brass wall lamp at (0.3, 28.5, 6.5). The nook's north edge is open to the living room.

Lighting: five recessed warm downlights over the work zones; the Sputnik over the table; under-cabinet strips; the nook wall lamp; in-cabinet lighting is omitted. All 2700K.

Objects: a wool runner 2.5 x 8 ft on the floor along the cooking wall; a wooden step stool; a fruit bowl; a linen towel; two cookbooks on the south cabinet's counter; a small radio. Keep the counters 70 percent clear.

### 3.15 Living room (X 0-22, Y 30-46)

Continuous with the kitchen at Y 30. Oak floor. Rear wall Y 46 carries the lift-and-slide N1 (X 3-19). East wall X 22 carries the away room's pocket door at Y 36-41 and is otherwise the Frame-TV gallery wall. West wall X 0 is the fireplace wall. South edge open to the kitchen.

Ceiling: exposed walnut beams, 6 x 12 in, running east-west (along X) from X 0 to X 22, at Y 30.5, 34.5, 38.5, 42.5, and 45.5 (five beams, 4 ft on center), bottoms at Z 8.5, tops at Z 9.5; between them, oak T&G decking at Z 9.5 (the underside of the second floor). Two warm recessed downlights between each pair of beams, dim; two picture lights over the gallery wall.

Fireplace wall (X 0 face, Y 30-46): full-height walnut paneling, vertical boards 6 in wide, from Y 30.5 to Y 45.5, Z 0 to Z 9.5 (the wall is solid, no windows). Firebox: a linear gas fireplace 5 ft wide, 1.5 ft tall, glass front, black steel interior with a ribbon flame (emissive orange, animated flicker acceptable but not required), centered at (0.3, 38, 2.9) with its opening from Z 2.2 to Z 3.7; the firebox is set in a full-height honed limestone surround panel 7 ft wide (Y 34.5-41.5) that reads as a slab within the walnut. Hearth bench: honed limestone, 12 ft long (Y 32-44), 1.6 ft deep, 1.4 ft tall, at [0.5, 32, 2.1, 44, 0, 1.4]. On the bench: a stack of three books, a ceramic vase, a brass candle holder.

The four sides, exactly:
- North wall Y 46: glass (N1), with the recessed shade pocket.
- West wall X 0: the walnut fireplace wall (above). Built-in bookshelves are part of it: from Y 30.5 to Y 34 and from Y 42 to Y 45.5, open walnut shelving 14 in deep, from Z 1.6 (just above the hearth bench line; the bench stops at Y 32 and Y 44 so the shelves' lowest tier sits directly on the floor for Y 30.5-32 and Y 44-45.5) to Z 8.5, five shelves each, packed with books (doubled up in places), ceramics, a small brass clock, a globe, three plants, and one framed photo per unit. The cat route: the shelves at Z 5.9 and Z 7.6 in the north unit are 18 in deep with a wool pad at (1, 44, 7.6). Between the two units sits the limestone slab with the firebox.
- East wall X 22: the Frame TV gallery wall, warm plaster, hung salon-style, with the pocket door at Y 36-41. Frame TV: 65-inch, recessed flush, walnut bezel, centered at (22, 33, 5.0), showing a warm abstract painting in the house palette. Around it on Y 30.5-36, and on Y 41-45.5, fourteen framed pieces of mixed size in brass and walnut frames, dense but not touching, centers between Z 3 and Z 8, lit by two picture lights.
- South edge Y 30: open to the kitchen except the two walnut-wrapped columns at (8, 30) and (22, 30).

Furniture:
- Sofa: low mid-century sofa, 8 ft long, 3 ft deep, seat height 1.4, back height 2.5, tapered walnut legs, burnt-orange fabric (RGB 0.72, 0.30, 0.10, velvet), centered at (11, 40), facing WEST toward the fireplace (its back toward the east wall). Throw pillows: two teal, one mustard. A wool throw folded over one arm.
- Two lounge chairs: mid-century armchairs, mustard fabric, walnut frames, at (5, 34.5) and (5, 43) angled 30 degrees toward the room center, facing east-southeast and east-northeast.
- Coffee table: walnut, round, 3.5 ft diameter, 1.3 tall, at (6.5, 39). On it: a stack of two art books, a ceramic bowl, a lit brass candle, a remote.
- Credenza: walnut, 5 ft long, 1.5 deep, 2.4 tall, tapered legs, against the east wall under the Frame TV at [20.5, 30.8, 22, 35.8, 0, 2.4]. On it: a turntable with a record playing (a black disc on the platter, tonearm down), two small speakers, a stack of eight records leaning, a brass table lamp (on) at the north end.
- Arc floor lamp: brass, 7.5 ft tall, arcing over the sofa from a base at (15, 43.5), shade 1.5 ft diameter ending at (11, 40, 6.5), on.
- Two table lamps: on the credenza (above) and a mushroom lamp on the hearth bench at (1.3, 33, 1.4).
- Rugs: a large wool rug 9 x 12 ft, oatmeal with an olive geometric border, centered at (10, 39.5); layered on top, a smaller vintage-look rug 5 x 7 ft in oxblood and cream centered at (8, 38.5), rotated 8 degrees.
- Plants: a large monstera in a terracotta pot at (20, 44.5, 0), 6 ft tall; a rubber plant at (2.5, 45, 0), 5 ft.
- A wool blanket basket at (18, 32, 0).
- The lift-and-slide's interior: a ceiling-recessed roller shade pocket along Y 45.7 (a 6-inch slot), shade fully up. A walnut threshold.

### 3.16 Away room (X 22-28, Y 32-46)

Door: a glass-and-walnut pocket door 5 ft wide (two 2.5-ft leaves) in the west wall X 22 at Y 36-41, open 3 ft in the shot; walnut frame with a single large pane per leaf. Window N2 on the north wall. Oak floor. Walls: olive-and-cream geometric wallpaper (large-scale interlocking squares, olive ground). Ceiling painted olive.

Contents: an Eames-style lounge chair and ottoman in worn dark-brown leather with a walnut shell, chair at (25, 43) facing south toward the door, ottoman at (25, 40.5); a brass mushroom floor lamp at (27, 44, 0), 5 ft, on; a book wall: walnut shelves on the east wall X 28 face, 12 in deep, from Y 32.5 to Y 45.5, Z 0 to Z 9.0, seven shelves, completely full of books, some horizontal stacks; a small walnut side table at (23.5, 43) with a book face-down and a glass; layered rugs: a 5 x 8 wool rug centered at (25, 39) and a 3 x 5 kilim on top centered at (25, 41); one framed piece on the south wall at (25, 32.3, 5.5) 2 x 3 ft; a scratching post (sisal, 3 ft) at (23, 33, 0); a wool throw on the ottoman. A closed walnut cabinet below the window [22.5, 45.2, 27.5, 46, 0, 2.5] with two ceramic objects on it.

Lighting: the floor lamp, plus two recessed warm downlights at 20 percent.

### 3.17 Primary bath (X 28-42, Y 13-22)

Doors: from the primary closet at Y 22, X 36 (3 ft, walnut, open in shots); to the laundry at Y 13, X 36.5 (3 ft, walnut, closed); WC compartment door at X 39, Y 14.75, 2.5 ft, walnut with a frosted glass panel. Window E2 (east, high, obscure). Terrazzo floor with brass strips in a 2-ft grid, heated (note). Walls: terrazzo slabs (large-format, same material as the floor) on the shower walls; warm plaster elsewhere. Plaster ceiling.

Layout:
- WC compartment: X 39-42, Y 13-16.5 (3 x 3.5 ft) with a wall-hung toilet on the east wall at (41.4, 14.7) facing west, a bidet seat (a slightly thicker seat with a small side control), a brass paper holder, a small brass shelf, a linear slot vent.
- Shower: X 35-42, Y 17-22 (7 x 5 ft), curbless, a single frameless glass panel 4 ft long on its west edge at X 35 from Y 17 to Y 21, with the walk-in entry at Y 21-22; a walnut bench [40, 17.2, 42, 19, 0, 1.5]; two brass shower heads on the north wall at (37, 22, 7) and (40, 22, 7), each with a brass handheld on a bar and a thermostatic control set (a crossbar temperature dial with two volume wheels) at (37, 22, 3.8) and (40, 22, 3.8); a linear drain along the north wall; a recessed niche in the north wall at X 38-39.5, Z 3.5-4.8 with three bottles.
- Vanity: wall-hung double vanity, walnut, 8 ft long, 1.8 deep, mounted with its top at Z 2.9, against the west wall X 28 from Y 13.5 to Y 21.5, two undermount white sinks at Y 15.5 and Y 19.5 with brass wall-mounted faucets at Z 3.6; a full-width backlit mirror above from Z 3.6 to Z 7.5 with a warm halo glow; two brass sconces at Y 13.8 and Y 21.2, Z 6; in-drawer outlets (note); a brass towel warmer ladder on the south wall at (33, 13.3, 3.5), 2 ft wide, 4 ft tall, with two towels; a small walnut stool; a plant.
- Freestanding tub: none, by decision (flagged for Natalie).
- Lighting: recessed downlights over the shower and WC, the mirror glow, the sconces, all warm.

### 3.18 Suite hall (X 28-31, Y 22-30)

The private vestibule. Door from the spine at X 28, Y 27-30 (solid walnut, acoustic, closed); door to the bedroom at Y 30, X 29.5 (3 ft walnut, open); door to the closet at X 31, Y 26 (3 ft, walnut, open). Oak floor, oxblood walls continuing the spine's color, one picture light and one 24 x 30 in framed piece on the west wall X 28 face at Y 24, Z 5.5. A wool runner. One recessed downlight.

### 3.19 Primary closet (X 31-42, Y 22-30)

Doors: from the suite hall at X 31, Y 26; to the bedroom at Y 30, X 36 (3 ft walnut, open); to the bath at Y 22, X 36 (3 ft walnut, open). Window E3 (east, high). Wool carpet, oatmeal. Walnut everything.

Contents: walnut wardrobe built-ins along the north wall (Y 30 face) X 31.5-34.5 and X 37.5-41.5 (flanking the bedroom door): hanging rods at Z 6.5 with a row of shirts and jackets above drawers from Z 0 to Z 3; along the south wall (Y 22 face) X 31.5-34.5 and X 37.5-41.5 (flanking the bath door): shelves with folded clothes, shoe shelves below; along the east wall (X 42 face, under the window) a bank of drawers from Z 0 to Z 4 from Y 23 to Y 29; center island: walnut, 4 ft long, 2 ft wide, 3 ft tall, at [34.5, 25, 38.5, 27, 0, 3], with a glass top over a felt-lined tray showing eight vintage wristwatches on leather straps, laid flat in a 2 x 4 grid, under a slim brass rail; drawers on both long sides; a small brass lamp on one end. Full-height mirror on the west wall X 31 face at Y 27-29.5. Laundry sorting: the south built-in's X 31.5-34.5 section has three canvas bins in a walnut frame from Z 0 to Z 2.5 instead of shoe shelves. A safe: a black steel safe 2 x 2 x 2.5 ft bolted at floor level in the northeast corner behind a walnut cabinet door [40.5, 28, 42, 30, 0, 2.5], door closed. Lighting: a brass three-globe pendant over the island at Z 8.2, LED strips inside the hanging sections.

### 3.20 Primary bedroom (X 28-42, Y 30-46)

The sleeping room. Doors: from the suite hall at Y 30, X 29.5; from the closet at Y 30, X 36. Windows N3 (north, over the garden) and E4 (east, over the catio); cat door E5. Wool carpet, oatmeal, wall to wall. Walls: warm white plaster on three sides; the SOUTH wall (Y 30 face, the headboard wall) is papered in a muted large-scale geometric wallpaper, olive ground with cream and mustard interlocking forms. Plaster ceiling painted warm white. Blackout roller shades recessed in ceiling pockets over N3 and E4, N3's shade one-third down, E4's up.

Furniture:
- Bed: walnut platform bed, king, 6.5 x 7 ft frame, platform 1.0 ft tall, mattress top at Z 2.0, a walnut headboard 4 ft tall and 9 ft wide (flanking the bed) against the south wall centered at X 35, from Y 30.5. Bedding: white linen duvet thrown back on the west side, four pillows (two white, two olive), a burnt-orange wool blanket folded at the foot and half slid off toward the east.
- Nightstands: walnut, 2 x 1.5 x 2.2 ft, at (31, 31.5) and (39, 31.5). West nightstand: a stack of three books, reading glasses on top, a water glass. East nightstand: a small vintage watch on a leather strap lying flat, a phone on a charging pad, a brass lamp. Both nightstands have a brass lamp (12 in high, opal shade), the east one on, the west one off.
- Reading chair: a mid-century armchair in teal velvet with a walnut frame at (40, 44), angled toward the window, a sweater over one arm; a small walnut side table at (38.5, 45) with a mug; a brass floor lamp at (41, 45.5, 0), off.
- Rug: a 6 x 9 wool rug in oxblood and oatmeal pattern centered at (35, 39) under the foot of the bed.
- Bench: a walnut bench with a wool cushion at the foot of the bed, [32.5, 38.5, 37.5, 40, 0, 1.5].
- Dresser: none (the closet handles it). A tall plant at (29, 45, 0), 6 ft.
- Slippers: two pairs, one at (33, 34) one at (38, 41), unpaired.
- Art: one piece 2.5 x 3.5 ft on the north wall west of N3, centered at (30, 46, 5.5); two small frames on the west wall X 28 face at Y 42 and Y 44, Z 5.5.
- Lighting: the two lamps, the floor lamp, two recessed downlights at the foot of the room on a 15 percent dim, and a small brass wall sconce over each nightstand at Z 5.2 (both off in the morning shot).

## 4. Second floor (Z 10.0 to 19.0)

All Z values in this section are absolute: the floor is Z 10.0, desk tops are about Z 12.5, ceiling Z 19.0. Where a height like "Z 5" is written for a wall-mounted item, read it as 5 ft above this floor (absolute Z 15).

Footprint X 0-42, Y 6-46, plus the two-story stair well over X 28-34, Y 0-13 (whose floor is open to below). Ceilings 9.0 ft flat plaster, except where noted. The kid zone is separated from the rest by a door across the hall at Y 26.

| Room | X | Y | Area | Floor | Walls |
|---|---|---|---|---|---|
| Her office | 0-11 | 6-26 | 220 | wool carpet | plaster + one teal wall |
| Lab | 11-22 / 22-28 | 6-22 / 6-13 | 218 | cork | plaster + one teal camera wall |
| Rack closet | 11-14 | 16-22 | 18 | sealed concrete | plaster |
| Work corridor | 11-22 | 22-26 | 44 | oak | oxblood |
| Stair well (open) | 28-34 | 0-13 | 78 | (void over the stair) | plaster |
| Landing | 22-42 | 13-19 | 120 | oak | oxblood |
| Elevator closet | 34-37 | 6-9 | 9 | concrete | plaster |
| Upstairs laundry closet | 34-42 / 37-42 | 9-13 / 6-9 | 47 | terrazzo | plaster |
| Hall | 22-28 | 19-46 | 162 | oak | oxblood |
| Kid bath, sink room | 28-35 | 19-28 | 63 | terrazzo | plaster + tile |
| Kid bath, tub room | 35-42 | 19-28 | 63 | terrazzo | tile |
| Bedroom B | 28-42 | 28-46 (less closets) | 213 | wool carpet | plaster + wallpaper |
| Bedroom A | 0-14 | 26-40 (less closet) | 181 | wool carpet | plaster + wallpaper |
| Hedge alcove | 0-14 | 40-46 | 84 | wool carpet | plaster |
| Loft | 14-22 | 26-46 | 160 | oak | plaster + one mustard wall |

Note on the stair well: the second floor's south wall is at Y 6 everywhere except X 28-34, where the stair well's south wall is at Y 0 and rises the full two stories (see 3.8). The upstairs landing receives the stair at X 31-34, Y 13.6.

### 4.1 Her office (X 0-11, Y 6-26)

Door 3 ft at X 11, Y 24 (solid walnut, acoustic seal), opening from the work corridor. Windows S7 (south), W3 and W4 (west). Wool carpet, charcoal, low pile. Walls warm plaster; the EAST wall (X 11 face) is painted deep teal (RGB 0.08, 0.32, 0.36) from floor to ceiling as the camera-ready wall behind her chair. Ceiling plaster.

Contents:
- The monitor desk: a walnut built-in counter along the WEST wall (X 0 face) from Y 9 to Y 24, 32 inches deep [0.5, 9, 3.2, 24, 12.4, 12.5], on walnut gables, with a continuous grommet channel at the back; six 27-inch monitors on articulating arms mounted to a black steel rail on the wall at Z 5.0, arranged 3 x 2, screens showing dark charts and spreadsheets (emissive, dim); a laptop on a dock at (2, 16, 2.5); a mechanical keyboard, a mouse, a mug, a notebook; cable channel neatly tied.
- Task chair: a mid-century style office chair with a walnut back and leather seat at (4.5, 16.5), facing west toward the monitors (so the camera behind her sees the teal east wall).
- Reading chair: a low mid-century lounge chair in mustard tight-weave wool, walnut frame, at (7.5, 9.5), facing northeast, with a floor lamp (brass, on) at (9.5, 8, 0) and a small side table with a stack of reports.
- Shelving: walnut shelves on the north wall Y 26 face from X 0.5 to X 10.5, Z 3 to Z 8.5, four shelves: binders, books, a plant, two framed photos, a small brass clock. Below: a low walnut credenza [0.5, 24.8, 10.5, 26, 10, 12.4] with a printer on it.
- Art on the teal wall: one large framed print 4 x 3 ft centered at (11, 16.5, 5.5), two smaller pieces at (11, 12, 5) and (11, 21, 5).
- Rug: 6 x 9 wool in oxblood and cream under the chair area, centered at (5.5, 16.5).
- Lighting: two recessed downlights, a linear LED cove along the west wall above the monitors at Z 8.5, the floor lamp, a desk lamp (brass, on).
- Plants: one tall bird-of-paradise at (9.5, 24, 0).
- Blackout shades recessed at S7, W3, W4, all up.

### 4.2 Work corridor (X 11-22, Y 22-26)

The short hall serving both offices. Door from the hall at X 22, Y 24 (3 ft, walnut, open); door to the lab at Y 22, X 16.5 (3 ft, walnut, open); door to her office at X 11, Y 24. Oak floor, oxblood walls (the spine color continues), a 2.5 x 8 runner, one picture light and two framed pieces on the north wall at (14, 26, 5.5) and (19, 26, 5.5). One recessed downlight.

### 4.3 Lab (X 11-22, Y 6-22, plus X 22-28, Y 6-13)

The L-shaped office-workshop. Door from the work corridor at Y 22, X 16.5. Windows S8 (the long south run, X 13-27). Cork floor (warm tan, fine grain). Walls warm plaster; the NORTH wall of the main leg (Y 22 face, X 11-22) is painted deep teal as the camera wall. Ceiling plaster.

Layout:
- Desk zone in the east leg (X 22-28, Y 6-13): a walnut desk 6 ft long, 2.5 deep [22.5, 8, 27.5, 10.5, 12.4, 12.5] facing SOUTH toward the window run (the desk's front edge at Y 8), two 32-inch monitors on arms (emissive, dim, code and a dashboard), a laptop on a dock, a mechanical keyboard, a mouse, a desk lamp (brass, on), headphones on a hook. Task chair at (25, 11.5) facing south. Behind the chair (north), the wall Y 13 is the landing's south wall: paint it teal too, with a walnut shelf at Z 5 holding a small camera, a plant, three books, and one framed print (a kitschy space print, 8 x 10 in, in an archival frame, at (25, 13, 5.8): this is the dad-gift print's home).
- Bench wall in the main leg along the WEST wall (X 11 face), Y 6-16 (10 ft): a butcher-block workbench 10 ft long, 2.5 deep, 3.0 tall [11.25, 6.5, 13.75, 16.5, 10, 13.0] on walnut cabinets with drawers; above it, a French-cleat tool wall (walnut slats at 6-inch spacing from Z 3.5 to Z 7.5, with hanging tools: pliers, screwdrivers, a soldering iron holder, spools of filament, bins); two articulated black task lamps clamped to the bench at Y 8 and Y 14 (on); an ESD mat (charcoal) at Y 9-12; a small vent hood (black, 2 ft wide) over the bench's north end at Z 5 with a duct up the wall; an enclosed 3D printer (a black cube 1.5 ft) on the bench at Y 15; a soldering station, a bench power supply, a microscope, a parts organizer with clear drawers on the wall at Y 6.5-8, Z 3.5-5.5; a half-finished PCB project on the mat.
- Rack closet at X 11-14, Y 16-22: a full-glass door 2.5 ft wide in a walnut frame in its EAST wall at X 14, Y 19; inside, a black 24U rack [11.5, 17, 13.5, 20, 10, 16.5] with a glass front, populated top to bottom: two patch panels (blue and orange cables in neat bundles), a switch with lit ports (green and amber LEDs), a small firewall, a 1U server, a 3U GPU box, a NAS with eight drive bays with blinking blue LEDs, a shelf with two mini computers and three small miners glowing amber, a small screen showing a dashboard, a PDU, a UPS at the bottom; a slim LED strip inside the rack's frame (cool white 4000K, the only cool light in the house, dim). Exhaust grille in the ceiling. Concrete floor sealed.
- Storage: the main leg's east wall at X 22 from Y 13 to Y 22 is a solid wall (the landing and hall are behind it). Closed flat-front walnut cabinets along it [21, 13.5, 22, 21.5, 10, 18], a few doors open showing labeled bins.
- Center: an open floor with a wool rug 5 x 8 in teal and cream at (17, 12), a rolling stool, and a small round walnut table at (17.5, 18) with a stack of magazines.
- Lighting: linear LED over the bench (warm), the task lamps, the desk lamp, four recessed downlights, the rack glow. A "do not disturb" light: a small brass fixture beside the corridor door at (16.5, 22, 7.5) glowing amber.
- Windows S8 with roller shades up, view of oak canopy outside.

### 4.4 Landing (X 22-42, Y 13-19) and stair well

Oak floor, oxblood walls, plaster ceiling. The up-stair arrives at X 31-34, Y 13.25. A bronze-post glass guard runs along Y 13 from X 28 to X 31 (the open well over the aisle) and along X 28 from Y 6 to Y 13 on the well's west side. Openings: lab door at X 22, Y 16 (3 ft walnut); hall continues north at X 22-28, Y 19; laundry closet door at Y 13, X 39 (a pair of 2-ft walnut doors); the chute hopper door at Y 13, X 35 (an 18 x 18 in walnut flap at Z 13). The elevator closet X 34-37, Y 6-9 is entered from inside the upstairs laundry closet at X 35.5, Y 9 (closed, never rendered). Window E6 on the east wall. Skylights over the landing at (26, 16) and (38, 16).

Contents: a walnut bench under the east window [40.5, 15, 42, 17.5, 10, 11.5], a runner 3 x 12 along the landing, three framed pieces on the north wall Y 19 face at X 30, 34, 38 (Z 5.5), two picture lights. The brass globe pendant over the well (see 3.8) is visible from here.

### 4.5 Upstairs laundry closet (X 34-42, Y 9-13 plus X 37-42, Y 6-9)

Doors from the landing (pair at X 39, Y 13). Inside: rough-in only. A capped water supply box, a drain stub, a 240V outlet, and a dryer vent stub on the east wall; shelves with linens; the chute: a walnut hopper at [34, 11, 36, 13, 10, 14] with an 18 x 18 in flap at the top (Z 13) facing the landing through the wall at Y 13, and the shaft dropping through the floor at [34.25, 11.25, 35.75, 12.75]. Terrazzo floor. Closed doors in all shots.

### 4.6 Hall (X 22-28, Y 19-46)

Oak floor, oxblood walls, runner 3 x 24 from Y 20 to Y 44. The kid-zone door: a solid walnut door 3 ft wide with a 1.5-ft sidelight, across the hall at Y 26 (door at X 23.5-26.5, sidelight X 26.5-28), open in the shots. Window N6 at the north end. Doors along the east wall X 28: kid bath sink room at Y 23.5 (3 ft), bedroom B at Y 40 (3 ft), linen at Y 35 (2 ft). Along the west wall X 22: the work corridor at Y 24 (3 ft), and the loft opens fully at X 22 from Y 26 to Y 46 (no wall; the loft and hall read as one space, distinguished by the loft's oak floor continuing and its mustard wall).

Contents north of the kid door: a low walnut bookcase [27, 42, 28, 45.5, 10, 13] under the window with kid books, a large framed map at (28, 30, 5.5), two picture lights. Three recessed downlights.

### 4.7 Kid bath (X 28-42, Y 19-28)

Compartmentalized: sink room X 28-35 and tub room X 35-42.
- Sink room: door from the hall at X 28, Y 23.5; door to the tub room at X 35, Y 23.5 (2.67 ft, walnut with frosted glass). Terrazzo floor; walls: white 3 x 6 ceramic tile in a stacked bond to Z 4, plaster above painted mustard; a double vanity in walnut, 6 ft, wall-hung, on the north wall Y 28 face [29, 26.5, 35, 28, 12.5, 13] with two round white sinks and brass faucets, a mirror band above with two round brass sconces, two toothbrush cups, a step stool; a wall-hung towel bar with two towels (one striped); a laundry hamper at (28.5, 19.5).
- Tub room: window E7 (east, obscure). A 5-ft alcove tub along the north wall [35.5, 25.5, 41.5, 28, 10, 11.6] with a brass tub filler and a brass handheld shower on a bar, white tile surround to Z 7 on the three walls of the alcove; a wall-hung toilet on the south wall at (38.5, 19.5) facing north; a brass paper holder; a small brass shelf; a rubber duck on the tub edge, a bottle of kid shampoo.
- Lighting: recessed downlights, the sconces.

### 4.8 Bedroom B (X 28-42, Y 28-46, less two closets)

Two closets occupy the strip X 28-31: the bedroom closet at Y 28-33 (door into the bedroom at X 31, Y 30.5) and the hall linen closet at Y 33-37 (door to the hall at X 28, Y 35). The bedroom's usable area is X 31-42, Y 28-37 plus X 28-42, Y 37-46. Door from the hall at X 28, Y 40 (3 ft). Windows N7 (north) and E8 (east). Wool carpet, oatmeal. Walls warm plaster; the north wall (Y 46 face) papered in a playful pattern (teal ground, cream and mustard shapes: rockets, or leaves, generic). Plaster ceiling.

Contents: a twin-XL walnut platform bed against the east wall at [37.5, 29, 41, 36, 10, 11.6] with striped bedding (teal and cream), a stuffed animal; a nightstand at (36, 29.5) with a small lamp (on); a desk wall on the south wall Y 28 face X 32-36: a walnut desk [32, 28.3, 36, 30.3, 10, 12.4] with a lamp, a laptop, pencils in a cup, a corkboard above at Z 4-6.5 with pinned drawings; a desk chair; a low bookshelf under the north window [33, 45, 41, 46, 10, 12.5]; a rug 5 x 7 with a bold geometric; a toy bin; a framed print above the bed; a wall-mounted reading sconce over the bed at (41.8, 32, 4.5); a recessed downlight; blackout shade at N7 half down. Closet door open showing clothes on a low rod.

### 4.9 Bedroom A (X 0-14, Y 26-40, less closet X 11-14, Y 26-31)

Door from the loft at X 14, Y 37 (3 ft, walnut). Closet door at X 11, Y 28.5 (2.67 ft) inside the room. Window W5 (west). Wool carpet, oatmeal. Walls warm plaster; the west wall (X 0 face) papered in an olive-and-cream botanical. Plaster ceiling.

Contents: a twin-XL walnut platform bed along the north wall [4, 37, 11, 40, 10, 11.6] with mustard-and-cream bedding and two pillows, a stuffed animal; nightstand at (2.5, 38.5) with a lamp (on); desk wall along the south wall Y 26 face X 1-6: walnut desk [1, 26.3, 6, 28.3, 10, 12.4], lamp, books, a corkboard above; desk chair; a low bookshelf against the west wall south of the window at [0.5, 35.5, 3.5, 36.5, 10, 13]; rug 5 x 7 with stripes; a beanbag at (8, 30); a toy basket; framed print above the desk; reading sconce over the bed at (0.2, 38.5, 4.5); recessed downlight; blackout shade up. Closet door closed.

### 4.10 Hedge alcove (X 0-14, Y 40-46)

The third-bedroom hedge, currently an open reading alcove off the loft. Its east side opens to the loft through a 4-ft cased opening at X 14, Y 41-45 (with a door header framed, no door). Windows W6 (west) and N4 (north). The alcove floor is wool carpet (the loft beside it is oak). Walls warm plaster. Contents: a built-in daybed along the north wall under N4 [0.5, 44, 8, 46, 10, 11.5] with a mattress cushion in olive and five throw pillows, a low bookshelf on the west wall south of W6 at [0.5, 40.3, 4, 41, 10, 13]; a brass wall lamp over the daybed at (4, 46, 4.5); a rug; a roughed closet outline at X 11-14, Y 40-43 is invisible framing (note only). A basket of blankets.

### 4.11 Loft (X 14-22, Y 26-46)

Open to the hall along X 22 (no wall) for Y 26-46. Oak floor. Walls: the west wall (X 14 face, the bedroom A wall) painted mustard (RGB 0.75, 0.58, 0.16) from Y 26 to Y 40, and warm plaster around the alcove opening; the north wall Y 46 carries N5 with the window seat. Ceiling plaster with the loft skylight at (18, 40).

Contents:
- Window seat: a walnut built-in bench under N5 [15, 44.5, 21, 46, 10, 11.5] with a deep wool cushion (teal), four throw pillows, a small stack of books, a blanket; drawers below.
- Book wall: walnut shelves on the mustard west wall from Y 30 to Y 36, Z 0 to Z 7.5, filled with kids' books (bright spines), toys, a globe, a small speaker. Above the shelves, a framed alphabet print.
- Charging shelf: a walnut shelf on the west wall at Y 27-29.5, Z 3.5, 8 in deep, with four device slots (brass outlets behind), two phones and a tablet on it with cables.
- A round low table (walnut, 3 ft) at (18, 33) with a puzzle half done; two kid chairs and one floor cushion.
- A rug 6 x 9 in a bold multicolor stripe centered at (18, 36).
- A toy chest at [19.5, 26.5, 21.5, 29, 10, 11.8].
- Lighting: two recessed downlights, a brass globe pendant at (18, 36, 8.2), the skylight.

## 5. Basement (Z -10.0 to -0.5)

Footprint X 0-42, Y 0-46. Ceilings 9.5 ft. Ceilings are removable acoustic panels painted per room (they must look like flat painted ceilings; model as flat planes with a faint 2 x 4 ft grid line). Walls: painted concrete block texture is NOT used; walls are finished plaster on framing over insulation, so they read as normal painted walls. Floors as listed.

| Room | X | Y | Area | Floor | Walls | Ceiling |
|---|---|---|---|---|---|---|
| Gym | 0-22 | 0-20 | 440 | rubber (platform inset) | plaster, one olive wall, mirror wall | white |
| Recovery suite | 0-22 | 20-28 | 176 | terrazzo | terrazzo + cedar | white |
| Lounge | 0-22 | 28-46 | 396 | wool carpet (pit: upholstery) | walnut paneling + plaster | dark (near black, matte) |
| Bar | 22-28 | 34-46 | 72 | terrazzo | botanical wallpaper | dark |
| Basement hall | 22-28 | 0-34 | 204 | oak-look LVP | oxblood | oxblood |
| Basement stair hall | 28-34 | 0-13 | 78 | oak | plaster | plaster |
| Battery room | 34-42 | 0-13 | 104 | concrete | concrete | concrete |
| Mechanical | 28-42 | 13-34 | 294 | concrete | concrete | concrete |
| Storage / projects | 28-42 | 34-46 | 168 | sealed concrete | painted plaster | white |

### 5.1 Basement hall (X 22-28, Y 0-34)

Stacked under the spine. Oak-look floor, oxblood walls and ceiling (continuing the spine's identity), a runner. Openings: the stair arrives from the west run at X 28-31, Y 13.6 into the basement stair hall, which opens into the hall through a cased opening at X 28, Y 5-9; gym glass door at X 22, Y 10 (a full-glass door 3 ft in a walnut frame, with a glass sidelight from Y 8 to Y 12 so the gym is visible from the hall); recovery suite door at X 22, Y 24 (3 ft walnut); mechanical door at X 28, Y 16 (3 ft, painted steel, closed); at Y 34 the hall opens fully into the lounge (the hall's north end has no wall; the bar's west edge X 22 from Y 34-46 is also open to the lounge). Lighting: picture lights with four framed pieces along the west wall X 22 face at Y 2, 16, 20, 30; three recessed downlights at 30 percent. A walnut console at [27, 26, 28, 30, 0, 2.7] with a brass lamp.

### 5.2 Gym (X 0-22, Y 0-20)

Doors: from the hall at X 22, Y 10 (glass); to the recovery suite at Y 20, X 21 (a full-glass door 3 ft in a walnut frame). Window well B1 on the west wall. Floor: 3/4-inch black rubber tile with a fine speckle. Walls: the SOUTH wall (Y 0 face) painted olive with three framed vintage athletics posters (procedural type-and-shape posters) centered at X 5, 11, 17 at Z -5; the WEST wall (X 0 face) is a full mirror from Y 1 to Y 19, Z -9.9 to Z -3 (Principled metallic 1.0, roughness 0.0) except around the window well; the north wall (Y 20 face) is white plaster with the glass door and a wall-mounted 65-inch screen at (10, 20, -5) showing a paused workout video; the east wall (X 22 face) white plaster with the glass door and sidelight. Ceiling white, bright: eight recessed downlights on full, cool-neutral 3500K (the gym is the one bright room).

Equipment (all black steel unless noted):
- Lifting platform: oak-veneer platform 8 x 8 ft [3, 3, 11, 11, -10, -9.85] with black rubber inserts on both sides; a full power rack (black, 4 x 4 ft footprint, 7.5 ft tall) centered on the platform at (7, 7) with a pull-up bar, safety arms, a barbell racked at Z -6.5 with two 45-lb plates each side, and a plate tree behind the rack at (7, 2, -10) with plates in black and red.
- Functional trainer (dual-cable machine): 4 ft wide, 3 ft deep, 7 ft tall, against the north wall at (16, 18.5, -10) facing south.
- Adjustable bench at (12, 12, -10), pointing east.
- Dumbbell rack: a two-tier rack 5 ft long against the south wall at (5, 1, -10) with ten pairs of rubber hex dumbbells; a set of adjustable dumbbells beside it.
- Cardio: one premium treadmill (her machine) at (18, 4, -10) facing the mirror wall (west), screen lit; one rowing machine folded upright at (20, 14, -10).
- Accessories: a kettlebell trio at (13, 2, -10), a foam roller and two yoga mats rolled in a basket at (1, 18, -10), gymnastics rings hung from a ceiling mount at (14, 7, -0.6) hanging to Z -3.5, a large floor fan (black, 3 ft) at (2, 12, -10), a wall-mounted towel shelf at (21.5, 17, -6) with rolled white towels, two water bottles on the bench, a wall clock at (11, 0.2, -3).
- A resistance band rail on the east wall at (21.8, 3, -5).

### 5.3 Recovery suite (X 0-22, Y 20-28)

Doors: from the gym at Y 20, X 21 (glass); from the hall at X 22, Y 24 (walnut). Terrazzo floor with brass strips, heated (note). Walls: terrazzo slab on the shower's walls; warm plaster elsewhere; the east wall (X 22 face) painted deep green (RGB 0.10, 0.28, 0.18). White ceiling with a dedicated exhaust grille over the shower and one over the sauna.

Layout, west to east:
- Sauna X 0-8, Y 20-28: a cedar box, interior clear cedar T&G on walls and ceiling, two tiers of cedar benches along the west and north walls (lower bench top at Z -8.4, upper at Z -7.0, each 2 ft deep), an electric heater (black, with a basket of stones) at (1, 21, -9.5) with a wood guard rail, a bucket and ladle, a cedar headrest, a small thermometer. Its EAST face at X 8 is a full-height walnut-framed glass front from Y 21 to Y 27 with a glass door 2.5 ft wide at Y 23-25.5 (hinged, closed); the rest of its exterior is walnut paneling. Interior lighting: warm strips under the benches and one small warm sconce, so the box glows.
- Dry landing X 8-12, Y 20-28: terrazzo floor, a walnut bench [8.5, 26, 11.5, 27.5, -10, -8.5], hooks on the north wall at Z -6 with two robes, a brass towel-warmer ladder on the north wall at (10, 27.8, -6.5), 2 ft wide, 4 ft tall, with two towels.
- Double shower X 12-20, Y 20-28: its west edge at X 12 is a full-height terrazzo wall from Y 20 to Y 28 (backing the landing's bench and hooks); its EAST edge at X 20 is a single frameless glass panel from Y 22 to Y 28, with the walk-in entry at Y 20-22. The head wall is the NORTH wall (Y 28 face), terrazzo slab: two exposed-thermostatic brass shower columns at (14, 28, -5.5) and (18, 28, -5.5), each with a temperature crossbar and two volume wheels at Z -6.2, a rain head at Z -2.5, and a handheld on a bar; two brass niches in the north wall at X 13-14.5 and X 17-18.5, Z -6 to -4.8, with bottles; a walnut bench [12.5, 20.5, 15, 22, -10, -8.5]; a linear drain along the north wall; a floor slope toward it (visual only).
- Cold plunge zone X 20-22, Y 20-28: a brass drain cap in the floor at (21, 24, -10), a small glass-front fridge [20.3, 26, 21.8, 27.5, -10, -7.5] with water bottles, a walnut shelf above it with two folded towels, hooks. The hall door at X 22, Y 24 and the gym door at Y 20, X 21 both land here, keeping the traffic dry.
- Lighting: warm recessed downlights (the shower's are wet-rated), the sauna glow, the towel warmer. Steam: a faint volumetric haze in the shower zone for the render is optional.

### 5.4 Lounge (X 0-22, Y 28-46)

Openings: the lounge's east boundary at X 22 is a solid wall from Y 28 to Y 34 (the hall runs behind it) and fully OPEN from Y 34 to Y 46, where the bar sits; the hall's north end at Y 34 opens into this same corner, so arriving from the hall you step into the lounge with the bar on your right. The south wall at Y 28 is solid (the recovery suite is behind it). Window wells B2 (west) and B3 (north). Floor: wool carpet, charcoal, low pile, wall to wall, except the pit. Walls: the NORTH wall (Y 46 face) is full-height walnut paneling from X 0 to X 22; other walls warm plaster painted deep oxblood. Ceiling painted near-black matte with a faint grid.

The pit: a true sunken conversation pit. Outer rectangle X 4-16, Y 32-42 (12 x 10 ft). The pit floor is at Z -11.5 (1.5 ft below the room floor). On the south, west, and east sides a continuous built-in banquette in teal velvet: seat cushions 2.5 ft deep with the seat top at Z -10.3, backs rising to Z -9.1 against the pit walls (the backs stand 0.9 ft above the room floor); the walnut cap, 6 in wide, runs along the top of the backs at Z -9.1 around those three sides and steps down to the room floor level at the north corners. The NORTH side is open, facing the panel: three walnut steps 1 ft wide descend from the room floor at Y 42 into the pit across the full 12-ft width. Pit floor: a shag rug in oatmeal over the sunken floor. Throw pillows: nine, in mustard, oxblood, olive, and cream, scattered on the banquette. A low round walnut table 2.5 ft diameter, 1 ft tall, at the pit center (10, 37, -11.5) with a bowl of popcorn and two glasses. No toddler rail is installed.
- Over the pit: three brass globe pendants (12-inch opal) hung at Z -4.5 in a row along Y 37 at X 7, 10, 13.
- The panel: a 98-inch (8 ft wide, 4.5 ft tall) black display recessed flush into the walnut north wall, centered at (10, 46, -6), showing a paused film frame (a dark, warm image). Below it, a low walnut media cabinet [5, 45.2, 15, 46, -10, -8.2] with a soundbar and consoles behind slatted doors.
- Games table: a walnut card table 4 x 4 ft at (19, 31, -10) with a jigsaw half done and four chairs; a brass pendant over it at (19, 31, -4.5).
- Closed walnut cabinets along the west wall X 0 face from Y 28.5 to Y 32 [0.3, 28.5, 1.3, 32, -10, -3] for board games, doors closed; a stack of five board games on top.
- The Malm-style cone fireplace is NOT installed.
- Layered rugs on the room floor: a 9 x 12 in oxblood and cream around the pit's south side, and a 4 x 6 kilim near the games table.
- A floor lamp (brass arc) at (2, 44, -10) reaching over the west end of the pit, on. Two picture lights on the west wall with two large framed pieces at (0, 36, -5.5) and (0, 41, -5.5) flanking B2.
- Egress well B2 shown with a linen shade drawn; B3 shows the window well's stone.
- Sound: two plaster-in speakers (invisible). A record crate is NOT here.

### 5.5 Bar (X 22-28, Y 34-46)

Open to the lounge along X 22, Y 34-46. Terrazzo floor. Walls: the north wall (Y 46) and east wall (X 28 face) papered in a dark botanical wallpaper (black ground, oversized olive and teal leaves) as the basement's one loud surface; the bar's south edge at Y 34 is where the hall arrives, so it is open too; the bar has two open edges (west to the lounge, south to the hall) and two papered walls (north, east). Ceiling dark.

Contents: the bar counter: terrazzo-topped with a brass edge band, 9 ft long, 2 ft deep, at [23, 36, 25, 45, -10, -6.5], its long axis north-south, with the service side to the east (X 25-28) and the guest side facing the lounge to the west; three brass-and-leather backless stools on the lounge side at (21.8, 37.5), (21.8, 40), (21.8, 42.5), standing just inside the lounge at the open edge. An undercounter sink (brass) in the counter's south end at (24, 37), a drawer fridge with a glass front [25.5, 43, 27.5, 45, -10, -7.5] against the east wall, a clear-ice machine (stainless, 2 ft) at [25.5, 40.5, 27.5, 42.5, -10, -7.2], an espresso machine (chrome and walnut, 1.5 ft) on the back-bar counter at (26.5, 37.5, -7.0), a walnut back-bar counter along the east wall [25.5, 35, 27.8, 45, -10, -7.0] with the appliances, and above it open brass-and-glass shelves at Z -5.5 and Z -4.0 from Y 35 to Y 45 holding colorful glassware (teal, amber, clear), six bottles, a cocktail shaker; a cake stand under a glass dome with a layer cake at (24, 44, -6.5) on the counter's north end; a bowl of lemons; a brass bar lamp (on) at (24, 36.5, -6.5); two brass pendants over the counter at (24, 38.5, -4.3) and (24, 42.5, -4.3). A walnut cabinet under the counter with the dessert program (closed). A framed small print on the north wall at (25, 46, -5).

### 5.6 Basement stair hall (X 28-34, Y 0-13)

The down-stair arrives at X 31-34, Y 0.75 (its bottom tread at the south end, having descended southward beneath the up-stair). The aisle X 28-31 is oak floor with the cased opening to the basement hall on its west wall at X 28, Y 5-9. The up-stair's underside forms the ceiling over the stair slot, paneled in walnut; the aisle's ceiling is plaster at Z -0.5. Plaster walls, a walnut handrail on the east wall of the run. No door to the battery room from here (it opens from mechanical). One brass globe pendant at (29.5, 9, -3).

### 5.7 Battery room (X 34-42, Y 0-13)

Door from mechanical at Y 13, X 38.5 (steel, closed). Concrete floor, painted concrete walls, bare. Contents (never rendered): two wall-mounted battery units, a critical-loads subpanel, an inverter, a surge protector box, the elevator closet's shaft base at X 34-37, Y 6-9.

### 5.8 Mechanical (X 28-42, Y 13-34)

Door from the hall at X 28, Y 16 (steel), door to storage at Y 34, X 35 (steel). Concrete floor with a floor drain at (35, 24), painted concrete walls, bare ceiling with visible ducts (silver), pipes (PEX in red and blue on a manifold board on the east wall X 42 face from Y 20 to Y 30), two water heaters (one heat-pump unit, tall) at (40, 15, -10) and (40, 18.5, -10), an ERV box hung near the ceiling at (32, 30, -2), a dehumidifier, a large media filter cabinet, a sump basin with a bolted lid at (30, 32, -10) and an ejector basin at (33, 32, -10), a softener and filtration stack at (41, 32, -10), labeled everything (small white labels). Bright cool light (4000K). The camera passes the door only; model at medium detail so a still through the open door reads.

### 5.9 Storage / projects (X 28-42, Y 34-46)

Doors: from the bar at X 28, Y 40 (walnut, closed in shots); from mechanical at Y 34, X 35. Window well B4. Sealed concrete floor, painted plaster walls white. Contents: steel shelving along the east wall with labeled bins and the attic-stock boxes (tile, flooring, wallpaper rolls, paint cans), two bikes, a folding table with a project on it, a rolling tool cart. Low detail.

## 6. Vertical circulation summary

- Stair core: X 31-34 carries both runs stacked: the up-stair rises northward from Y 0.75 (main floor) to Y 13.25 (second floor); the down-stair descends southward beneath it from Y 13.25 (main floor) to Y 0.75 (basement). The aisle X 28-31 alongside is floor on all three levels and connects to the spine (main), the landing (second, via the arrival at Y 13.25), and the basement hall. 16 risers at 7.5 in, 15 treads at 10 in per run. Oak treads and closed risers, walnut stringers and skirt, a walnut oval handrail on the east wall of each run at 3 ft above the nosings, a bronze-post glass guard along the open edges. The well over X 28-34, Y 0-13 is open two stories with the brass globe pendant at (31, 6.5, 14) and the stacked clerestories S5 and S9.
- Elevator hedge: stacked closets at X 34-37, Y 6-9 on all three levels (inside the main-floor laundry, the upstairs laundry closet, and the battery room). Doors closed, never rendered.
- Laundry chute: from the upstairs laundry closet hopper at [34, 11, 36, 13] down through the floor to the main-floor laundry hopper at the same plan position.

## 7. Garage (detached, X -6 to 18, Y 64 to 94, slab at Z -0.4, clear height 12.0)

### 7.1 Shell

- Two bays, 24 ft wide overall, 30 ft deep. Bay W (the deep lift bay) X -6 to 6; Bay E X 6 to 18. No interior wall between bays.
- Walls: Roman brick from the slab to Z 8, vertical cedar from Z 8 to the eave at Z 12, matching the house. Low-pitched gable roof, ridge along Y (north-south) at X 6, pitch 3:12, eaves at Z 12.5 with 3-ft overhangs, ridge at Z 15.5, standing-seam charcoal.
- Doors on the NORTH wall (Y 94, alley side): two sectional doors 9 ft wide by 8 ft tall, cedar-clad flush panels with a horizontal window band at Z 6-7 (four small panes each), at X -4.5 to 4.5 and X 7.5 to 16.5. Bronze-black trim.
- Pedestrian door on the SOUTH wall at X -3, Y 64, 3 ft, half-glass, into the breezeway.
- Windows: a clerestory band on the east wall (X 18) from Y 66 to Y 92, sill 9, height 2; same on the west wall.
- Interior walls: white-painted plaster on all walls; ceiling white with the roof structure exposed (collar-tied cedar rafters).
- Floor: sealed concrete, light gray, with a trench drain across both bays at Y 80 and a floor drain at (0, 72). Radiant (note).

### 7.2 Contents

- Four-post storage lift in Bay W: posts (black steel 6-in square) at (-4.5, 68), (4.5, 68), (-4.5, 84), (4.5, 84), 8 ft tall; two runways 20 in wide from Y 66 to Y 86 at X -3.8 to -2.1 and X 2.1 to 3.8, raised to Z 5.5 (runway top), with a rolling jack tray between them; a dark green vintage sports car (a 1960s British roadster silhouette, CC0 model, or a procedural stand-in of correct proportions 14.5 ft long, 5.4 wide, 4.0 tall) parked on the runways with its nose at Y 84; a battery tender cable clipped to its front. Beneath the lift, a white mid-size electric SUV (generic, no badges, 15.5 ft long) parked nose-in at Y 66-81.5, centered at X 0.
- Bay E: a gray electric sedan (generic, no badges, 15.5 ft long) parked nose-in centered at X 12, Y 66-81.5, plugged into a wall charger (black box with a coiled cable) on the east wall at (17.8, 70, 4).
- Second wall charger (unused) on the west wall at (-5.8, 70, 4) for the lift bay.
- Workbench along the SOUTH wall from X -5.5 to X 17.5 [ -5.5, 64.5, 17.5, 67, 0, 3 ] with a butcher-block top, black rolling toolbox 4 ft wide at (10, 66, 0), a vise, a shop vac, a pegboard tool wall above the bench from Z 3.5 to Z 7.5 with wrenches, sockets, screwdrivers, a torque wrench, a creeper leaning at (16, 65, 0), a parts washer at (-5, 65.5, 0), a compressor in a slatted closet at the southwest corner [-6, 64, -4, 66.5, 0, 6] with an air line running along the wall to a ceiling reel.
- Ceiling reels: a cord reel at (0, 76, 11.5) and an air hose reel at (2, 76, 11.5), red and black.
- Shelving: steel shelving along the west wall X -6 face from Y 86 to Y 92 with bins, a folded ladder.
- Snow shovel and a broom in the northeast corner at (17.5, 93, 0). A bag of ice melt. Two cardboard boxes on a shelf.
- Lighting: six 4-ft linear LED shop lights in two rows at Z 11.5 (neutral 4000K), and one warm bronze sconce each side of each garage door outside.
- Exterior: bronze address plaque on the alley side, the utility inlet plate (brass, 8 x 8 in) at (17.5, 93.8, 3) on the north wall's east end.

## 8. Materials library

Create `materials.json` with exactly these entries. Base color as RGB 0-1 (linear). Texture scale in feet per repeat where a texture is used. Source: CC0 texture sets from Poly Haven or ambientCG with the closest match; the base color tints the albedo map toward the value given.

| Name | Base color | Roughness | Metallic | Notes |
|---|---|---|---|---|
| plaster_warm | 0.93, 0.89, 0.82 | 0.95 | 0 | fine plaster bump, 2 ft repeat |
| oxblood | 0.32, 0.08, 0.09 | 0.90 | 0 | flat paint over plaster bump |
| olive_paint | 0.32, 0.36, 0.20 | 0.85 | 0 | |
| teal_paint | 0.08, 0.32, 0.36 | 0.85 | 0 | |
| mustard_paint | 0.75, 0.58, 0.16 | 0.85 | 0 | |
| green_deep | 0.10, 0.28, 0.18 | 0.85 | 0 | recovery suite wall |
| ceiling_dark | 0.05, 0.05, 0.06 | 1.0 | 0 | basement lounge and bar |
| oak_floor | 0.72, 0.56, 0.36 | 0.45 | 0 | plank texture, planks 5 in wide, direction along Y, 8 ft repeat |
| oak_decking | 0.70, 0.54, 0.34 | 0.55 | 0 | ceiling between beams, boards 5 in, along Y |
| walnut | 0.24, 0.14, 0.08 | 0.40 | 0 | straight-grain texture, 4 ft repeat, satin |
| walnut_panel | 0.22, 0.13, 0.08 | 0.45 | 0 | vertical boards 6 in |
| cedar_ext | 0.62, 0.40, 0.22 | 0.70 | 0 | vertical T&G 5.5 in |
| cedar_sauna | 0.70, 0.50, 0.30 | 0.65 | 0 | clear, lighter |
| roman_brick | 0.55, 0.38, 0.28 | 0.95 | 0 | 12 x 1.6 in faces, running bond, 3-tone variation |
| limestone | 0.78, 0.74, 0.66 | 0.50 | 0 | honed, faint fossil texture |
| soapstone | 0.22, 0.24, 0.22 | 0.35 | 0 | dark gray-green with subtle white veins |
| marble_white | 0.90, 0.88, 0.86 | 0.25 | 0 | honed Carrara-like veining |
| terrazzo | 0.80, 0.78, 0.74 | 0.30 | 0 | multicolor chips (cream, ochre, oxblood, charcoal), 1.5 ft repeat; brass divider strips procedural at 2 ft grid where specified |
| concrete_sealed | 0.55, 0.55, 0.53 | 0.60 | 0 | |
| rubber_floor | 0.12, 0.12, 0.12 | 0.90 | 0 | fine speckle |
| cork | 0.70, 0.52, 0.32 | 0.75 | 0 | cork grain, 1 ft repeat |
| wool_carpet | 0.78, 0.72, 0.62 | 1.0 | 0 | low pile bump |
| wool_carpet_charcoal | 0.25, 0.25, 0.26 | 1.0 | 0 | |
| brass_aged | 0.85, 0.65, 0.35 | 0.35 | 1 | slight patina noise on roughness |
| bronze_black | 0.08, 0.07, 0.06 | 0.45 | 1 | window frames, rails |
| steel_black | 0.05, 0.05, 0.05 | 0.55 | 1 | gym, lift, appliances |
| stainless | 0.75, 0.75, 0.75 | 0.30 | 1 | brushed |
| glass | 1, 1, 1 | 0.02 | 0 | transmission 1.0, IOR 1.45, thin, slight green tint 0.95, 1, 0.97 |
| glass_frosted | 1, 1, 1 | 0.55 | 0 | transmission 1.0 |
| mirror | 1, 1, 1 | 0.0 | 1 | |
| velvet_orange | 0.72, 0.30, 0.10 | 0.85 | 0 | sheen 0.6, velvet-like |
| velvet_teal | 0.08, 0.32, 0.36 | 0.85 | 0 | sheen 0.6 |
| wool_mustard | 0.75, 0.58, 0.16 | 1.0 | 0 | weave bump |
| wool_oatmeal | 0.80, 0.74, 0.62 | 1.0 | 0 | |
| leather_brown | 0.30, 0.18, 0.10 | 0.55 | 0 | worn, slight sheen variation |
| linen_white | 0.94, 0.92, 0.88 | 0.95 | 0 | fine weave, used for bedding |
| tile_backsplash | pattern | 0.35 | 0 | burnt orange (0.72, 0.30, 0.10) and cream (0.92, 0.86, 0.74) quarter-circle tiles 4 in forming circles |
| tile_white | 0.94, 0.94, 0.92 | 0.25 | 0 | 3 x 6 in stacked, gray grout |
| wallpaper_botanical_dark | pattern | 0.90 | 0 | black ground, olive/teal/mustard leaves, 3 ft repeat |
| wallpaper_geo_olive | pattern | 0.90 | 0 | olive ground, cream interlocking squares, 2 ft repeat |
| wallpaper_geo_muted | pattern | 0.90 | 0 | muted olive/cream/mustard forms, 2.5 ft repeat (primary bedroom) |
| wallpaper_kid_teal | pattern | 0.90 | 0 | teal ground, cream/mustard shapes |
| wallpaper_kid_botanical | pattern | 0.90 | 0 | olive/cream leaves |
| bluestone | 0.40, 0.42, 0.45 | 0.75 | 0 | random ashlar, 2 x 3 ft stones |
| asphalt | 0.12, 0.12, 0.12 | 0.95 | 0 | alley |
| lawn | 0.25, 0.40, 0.15 | 1.0 | 0 | grass texture or particle grass |
| gravel_gray | 0.55, 0.55, 0.52 | 0.95 | 0 | river stone |
| metal_roof_charcoal | 0.15, 0.15, 0.16 | 0.45 | 0.6 | standing seams 16 in |
| emissive_warm | 1.0, 0.85, 0.60 | 0.5 | 0 | emission strength per fixture (2700K) |
| emissive_cool | 0.85, 0.92, 1.0 | 0.5 | 0 | rack LEDs only (4000K) |
| emissive_fire | 1.0, 0.45, 0.10 | 0.5 | 0 | fire ribbon, strength 12 |
| screen_dark | 0.02, 0.02, 0.03 | 0.15 | 0 | emission of the displayed image, strength 1.5 |

Book palette (procedural spines): muted red (0.55, 0.15, 0.12), olive (0.35, 0.40, 0.22), ochre (0.75, 0.55, 0.20), navy (0.12, 0.18, 0.35), black (0.05, 0.05, 0.05), cream (0.90, 0.85, 0.75), forest (0.10, 0.30, 0.20), rust (0.62, 0.28, 0.12). Spine heights 7-11 in, thickness 0.6-2 in, random, with occasional horizontal stacks of 3-6.

Art palette (procedural abstracts): compositions of two to four color blocks from the house palette on cream or black grounds, plus 20 percent grayscale "photographs" (soft noise gradients with a horizon). Frames: brass_aged or walnut, 0.75 in wide, 1 in deep. Mats: cream, 2 in.

## 9. Lighting rules

- Indoor light is 2700K (emissive_warm and area lights at RGB 1.0, 0.83, 0.65) everywhere except: the gym (3500K, bright), the mechanical rooms and garage interior (4000K), and the rack LEDs (4000K, dim).
- Every lamp, pendant, sconce, picture light, and under-cabinet strip listed in the room sections is a real source: an emissive shade or lens plus a small area or point light inside for clean shadows. Bulbs inside opal shades: emission strength 8-15. Picture lights: a narrow spot aimed at the art, 30-degree cone. Under-cabinet strips: a thin emissive plane, strength 6.
- Recessed downlights: 3-inch trimless warm spots, 40-degree cone, dimmed as stated per room (default 35 percent).
- Daylight: an HDRI sky (late afternoon autumn, sun low in the southwest) for the exterior and main-floor shots, rotated so sun enters through the living room's rear glass at a low angle and rakes across the kitchen. The bedroom shot uses a morning sky (sun low in the east). Light portals in N1, S4, S8, and the bedroom windows.
- Basement: no daylight except through the window wells (dim, gray); the rooms are lit by their fixtures.
- Exposure: AgX, Medium Contrast; exposure per shot tuned so plaster reads warm white, never gray, and windows are bright but not clipped.
- The fireplace ribbon and the sauna interior are the two strongest emissive accents; keep them warm and slightly overexposed.

## 10. Camera shots

Camera: 24 mm on a 36 mm sensor, f/4 depth of field with focus on the look target, motion blur shutter 0.5, a barely perceptible handheld noise on rotation (0.15 degrees, slow). Eye height 5.5 ft above the current floor unless stated. Waypoints `t` in seconds, `pos` and `look` in feet, absolute Z. Bezier interpolation, clamped handles, no overshoot. Each shot renders to its own frame directory; final assembly concatenates in order with 12-frame cross dissolves.

### Shot 1, street approach (12 s)

Autumn afternoon. Cat visible in the S4 bench window.
- t 0: pos (10.5, -34, 5.5), look (14, 0, 6). Standing on the sidewalk.
- t 4: pos (10.5, -22, 5.5), look (12, 0, 5).
- t 8: pos (10.5, -12, 5.5), look (11, 0, 4.5). The porch and bench fill the frame.
- t 12: pos (11, -6.5, 5.5), look (11, 0, 4). At the porch step, door ahead.

### Shot 2, main floor (26 s)

- t 0: pos (11, 3, 5.5), look (11, 12, 5). Inside the vestibule looking through the glass door.
- t 3: pos (11, 9, 5.5), look (22, 9.5, 5). Entry hall, the cased opening ahead.
- t 6: pos (23, 9.5, 5.5), look (25, 1, 4). Turning south to the bench window: the cat, the daylight.
- t 9: pos (25, 8, 5.5), look (25, 30, 5). Turning north down the oxblood gallery.
- t 13: pos (25, 17, 5.5), look (12, 22, 4.5). Turning west through the kitchen opening toward the island.
- t 17: pos (17, 20, 5.5), look (6, 28, 4.5). Passing the island's east side, the Sputnik overhead, the nook and the living beyond.
- t 21: pos (12, 31, 5.5), look (2, 38, 4.5). Entering the living room, fireplace wall ahead.
- t 24: pos (9, 37, 5.5), look (14, 46, 5). Turning toward the rear glass and terrace.
- t 26: pos (9, 39, 5.5), look (25, 38, 4.5). Ending on the gallery wall with the Frame TV, the away room's pocket door open beyond.

### Shot 3, basement (20 s)

- t 0: pos (29.5, 10, 4.5), look (29.5, 4, -4). At the top of the down-stair looking down the run.
- t 3: pos (32.5, 9, -1), look (32.5, 2, -8). Mid-descent.
- t 6: pos (29.5, 3, -4.5), look (24, 8, -5). Arriving in the basement stair hall, turning toward the cased opening.
- t 9: pos (25, 10, -4.5), look (8, 8, -5.5). In the hall looking through the gym's glass at the rack and platform.
- t 12: pos (25, 24, -4.5), look (12, 24, -5.5). Passing the recovery suite door, open, sauna glowing.
- t 15: pos (23, 34, -4.5), look (10, 38, -7). Emerging into the lounge, the pit below, pendants low.
- t 18: pos (14, 42, -4.5), look (10, 34, -8). Standing at the pit's open north edge looking down into it, the panel behind the camera.
- t 20: pos (17, 40, -4.5), look (25, 41, -6.5). Turning to the bar, cake dome, glassware.

### Shot 4, upstairs (18 s)

- t 0: pos (32.5, 11, 14.5), look (32, 16, 15). Arriving at the top of the up-stair.
- t 3: pos (25, 16, 15.5), look (22, 16, 15). Turning to the lab door.
- t 6: pos (20, 14, 15.5), look (25, 9, 15). Inside the lab: the desk zone, the window run, the dad print on the shelf.
- t 9: pos (16, 12, 15.5), look (12, 10, 14.5). The bench wall and tool wall.
- t 11: pos (15, 17, 15.5), look (12.5, 19, 14.5). The rack closet through its glass door, LEDs blinking.
- t 14: pos (25, 30, 15.5), look (18, 40, 15). Through the kid-zone door into the loft, window seat ahead.
- t 18: pos (19, 36, 15.5), look (17, 44, 14.5). Ending on the window seat and the alcove beyond.

### Shot 5, terrace at dusk (12 s)

Blue hour, all interior lights on, the lift-and-slide open 4 ft, heaters glowing, the swim spa cover open, one cat in the catio.
- t 0: pos (36, 78, 5.5), look (12, 46, 6). On the lawn looking back at the house.
- t 5: pos (26, 66, 5.5), look (10, 46, 5). Past the swim spa toward the terrace.
- t 9: pos (16, 58, 5.5), look (8, 40, 4.5). Under the canopy looking through the glass into the lit living room.
- t 12: pos (11, 48, 5.5), look (2, 38, 4). At the threshold, the fireplace visible inside.

### Shot 6, primary bedroom (8 s, morning)

- t 0: pos (33, 44, 5.5), look (35, 31, 3.5). From the window corner toward the bed.
- t 4: pos (30, 41, 5.5), look (39, 32, 2.5). Slow drift toward the east nightstand: the watch, the phone, the cat on the bed.
- t 8: pos (31, 37, 5.5), look (41, 41, 4). Ending on the reading chair and the east window with the catio beyond.

### Shot 7, garage (8 s)

- t 0: pos (6, 96, 5.5), look (0, 76, 5). Both doors open, from the apron.
- t 4: pos (2, 86, 5.5), look (0, 74, 6.5). Looking up at the roadster on the lift with the SUV beneath.
- t 8: pos (-2, 78, 5.5), look (6, 66, 3.5). Turning to the bench and tool wall.

Review stills: render one still at each shot's last waypoint plus Shot 2 t 13 and t 21, Shot 3 t 9 and t 18, Shot 4 t 11, at 1920x1080 and 256 samples. Present them as a contact sheet before any animation renders.

## 11. Modeling and asset rules

### 11.1 Geometry

- Build rooms from the tables: floor slab, ceiling slab, half-walls inside bounds (0.25 ft) for interior walls, full 1.0 ft for exterior walls. Cut openings by boolean using the schedule in 2.5 and the per-room door lists. Every door gets a frame (walnut jambs 5 in wide, head casing) and a door leaf (flat walnut, 1.75 in thick, brass lever handle) at the stated swing state; cased openings get jambs only. Pocket doors get a walnut frame and the leaf recessed the stated amount.
- Windows get a bronze_black frame 2.5 in wide, a glass pane, mullions as scheduled, a 1-in walnut interior stool, and, where stated, a recessed roller-shade pocket 6 in wide at the ceiling with a charcoal shade at the stated height.
- Baseboards: 3 x 0.75 in walnut along every wall of every finished room except gym, mechanical, battery, storage, closets, and the garage.
- Ceiling beams (living room): 6 x 12 in walnut at the stated positions, with oak decking between.
- Stairs, guards, handrails per section 6.
- Terrazzo brass strips: a procedural stripe pattern in the terrazzo material at the stated grid, 1/4 in wide.

### 11.2 Assets

- Prefer CC0 models from Poly Haven for furniture, plants, appliances, and vehicles; ambientCG for textures. Record every download in `assets/manifest.json` with the URL and license. No account-gated or non-CC0 sources.
- Where a CC0 model does not exist, build a procedural stand-in with the exact dimensions given here and a plausible silhouette (rounded edges, tapered legs on furniture, cushions as slightly inflated boxes). A box is never acceptable for anything the camera sees within 10 ft.
- Scale every asset to the dimensions in this document. Do not accept a model's native scale.

### 11.3 Procedural helpers (write once, reuse)

- `books(bounds, fill=0.95)`: fills shelves per the book palette, with random leaning and stacks.
- `frames(wall_face, layout)`: art frames per the art palette; sizes from a list; salon or single placement.
- `sputnik(center, arms=18, r=1.6)`.
- `globe_pendant(pos, diameter, drop)`.
- `picture_light(pos, aim)`.
- `rug(bounds, material, rotation, pattern)`.
- `plant(pos, height, kind)` if no CC0 model fits.
- `cushion(bounds, material)` with slight inflation.
- `stair(run_bounds, risers, treads, direction)`.
- `terrazzo_with_strips(bounds, grid)`.

### 11.4 The cats

Two cats total in the house, both the same tabby model (CC0) or a low-poly stand-in: one asleep on the spine's window seat (main floor shots) and on the bed (bedroom shot), one in the catio (terrace shot). Never both in one frame. If no acceptable cat model exists, omit the cats entirely and log it; do not use a box.

### 11.5 Render settings

Cycles, CPU unless a GPU is available, adaptive sampling, denoising on, light portals in the windows named in section 9, AgX Medium Contrast. Review stills at 1920x1080, 256 samples. Animation at 1920x1080, 256 samples if the measured per-frame time allows the full set (about 2,500 frames) within 24 hours on the machine; otherwise 1280x720 at 256 samples, and say so in the README.

## 12. Room-by-room acceptance checklist

Before rendering any shot, open the scene and verify each room against its section. A room passes only when every listed object exists, is named per 0.3, is at its stated position, has its stated material, and every listed door and window exists with its stated state. Log the check in `notes/log.md` as a table with one row per room and a pass/fail per column: geometry, openings, finishes, furniture, lighting, objects.

Rooms to check: gear closet, vestibule, powder, coat closet, panel closet, entry hall, spine, stair hall and core, laundry, elevator closets, mudroom, litter closet, pantry, kitchen, living room, away room, primary bath, suite hall, primary closet, primary bedroom, her office, work corridor, lab, rack closet, landing, upstairs laundry closet, hall, kid bath (both rooms), bedroom B, bedroom A, hedge alcove, loft, basement hall, gym, recovery suite (sauna, landing, shower, cold plunge zone), lounge (pit, panel, bar edge), bar, basement stair hall, battery room, mechanical, storage, garage, porch, breezeway, terrace (canopy, grill, swim spa, catio), lawn and beds, street and neighbors.

The build is complete when every row passes, the seven shots and the review stills are rendered, the contact sheet exists, the asset manifest is complete, and the README reports measured render times.

