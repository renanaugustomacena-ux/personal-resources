---
course: "Godot 4 in Production"
phase: "2 — Visual systems"
module: "05"
title: "Tiles and TileMaps — TileSet, TileMapLayer, Terrains and Isometric Modes"
version: "Godot 4.5 / GDScript 2.0"
level: "Intermediate"
prerequisites: [ "SPRITES_AND_TEXTURES.md", "RENDERING_AND_VISUAL_LOGIC.md" ]
objectives:
  - "Assemble a production-grade TileSet with atlas sources, alternative tiles and scene collection sources"
  - "Structure levels with stacked TileMapLayer nodes and migrate legacy TileMap scenes to the 4.3+ architecture"
  - "Configure per-tile physics, navigation, occlusion and typed custom data layers, and read them from GDScript"
  - "Build terrain sets, explain peering bits for corner/side match modes, and paint terrains without artifacts"
  - "Script tilemaps through the cell API (set_cell, map_to_local, get_used_cells) and write a procedural room generator"
  - "Set up isometric tilemaps with diamond layouts, correct Y-sort and elevation faking"
  - "Choose between TileMapLayer, GridMap and freeform sprite placement with justified trade-offs for a real project"
tags: [godot, gdscript, tilemap, tilemaplayer, tileset, terrains, autotiling, isometric, 2d, collision, navigation, procedural-generation]
---

# Tiles and TileMaps — TileSet, TileMapLayer, Terrains and Isometric Modes — Complete Guide

> **Module 05** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Sprites and Textures](SPRITES_AND_TEXTURES.md), [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md)
>
> By the end of this module you will be able to:
> 1. Assemble a production-grade `TileSet` with atlas sources, alternative tiles and scene collection sources
> 2. Structure levels with stacked `TileMapLayer` nodes and migrate legacy `TileMap` scenes to the 4.3+ architecture
> 3. Configure per-tile physics, navigation, occlusion and typed custom data, and read them from GDScript
> 4. Build terrain sets and explain peering bits for corner/side match modes without hand-waving
> 5. Script tilemaps through the cell API and write a small procedural room generator
> 6. Set up isometric tilemaps with diamond layouts, correct Y-sort and elevation faking
> 7. Argue — with numbers and trade-offs — when a project should *not* use tilemaps, using the Relax Room
>    decoration system as the case study
>
> **Estimated time:** 6–8 hours reading · 4–6 hours labs · **Level:** Intermediate

## Guiding ideas

1. **A tilemap is a database, not a picture.** Every painted cell stores `(source_id, atlas_coords, alternative_tile)`; rendering, physics, navigation and metadata are all *derived* from that record.
2. **TileMapLayer replaced TileMap (Godot 4.3).** One node per layer: less inspector clutter, a flat API, per-layer transforms/materials, and the full `Node2D` toolbox on each layer.
3. **The TileSet is the single source of truth.** Collision polygons, navigation polygons, occluders, terrains and custom data live in the *resource*, so every layer and every scene that shares it stays consistent.
4. **Terrains automate transitions; peering bits are the contract.** Autotiling is not magic — it is a constraint solver over the bits you paint. Understand the bits and terrains stop misbehaving.
5. **Isometric is a projection, not a different engine.** Same cell API, same TileSet — only `tile_shape`, layout, Y-sort and texture origins change.
6. **Tilemaps are a choice, not a default.** Relax Room ships without a single TileMapLayer — freeform, snap-to-grid `Sprite2D` decorations won that trade-off. Know why, and know when the answer flips.

## Concept map

```
                          ┌─────────────────────────────────────┐
                          │        TILES & TILEMAPS             │
                          │      (the Godot 4.5 tile stack)     │
                          └──────────────────┬──────────────────┘
                                             │
            ┌────────────────────────────────┼────────────────────────────────┐
            │                                │                                │
   ┌────────▼─────────┐            ┌─────────▼─────────┐            ┌─────────▼────────┐
   │     TileSet      │            │   TileMapLayer    │            │    Workflows     │
   │    (Resource)    │  assigned  │     (Node2D)      │            │                  │
   │                  │───────────▶│                   │            │  editor painting │
   └────────┬─────────┘            └─────────┬─────────┘            │  terrains brush  │
            │                                │                      │  patterns        │
   ┌────────┴─────────┐            ┌─────────┴─────────┐            │  scripting       │
   │ sources          │            │ per-layer state   │            │  procedural gen  │
   │  · atlas         │            │  · enabled        │            └─────────┬────────┘
   │  · scenes        │            │  · modulate       │                      │
   │ tile shapes      │            │  · z_index        │            ┌─────────┴────────┐
   │  · square        │            │  · y_sort_enabled │            │ cell API         │
   │  · isometric     │            │  · collision_*    │            │  set_cell        │
   │  · half-offset   │            │  · navigation_*   │            │  erase_cell      │
   │  · hexagon       │            │  · quadrants      │            │  get_used_cells  │
   └────────┬─────────┘            └─────────┬─────────┘            │  map_to_local    │
            │                                │                      │  local_to_map    │
   ┌────────┴─────────┐            ┌─────────┴─────────┐            └─────────┬────────┘
   │ per-tile data    │            │ layer stacking    │                      │
   │  · collision     │            │  · ground         │            ┌─────────┴────────┐
   │  · navigation    │            │  · props (y-sort) │            │ decisions        │
   │  · occlusion     │            │  · overlay        │            │  TileMapLayer    │
   │  · custom data   │            │  · iso elevation  │            │  vs GridMap      │
   │  · terrains ────────▶ peering bits & match modes  │            │  vs freeform     │
   │  · probability   │            └───────────────────┘            │  (Relax Room)    │
   └──────────────────┘                                             └──────────────────┘
```

## Table of contents

1. [Overview: the Godot 4 tile stack](#overview-the-godot-4-tile-stack)
2. [TileSet anatomy: shapes, layouts and tile size](#tileset-anatomy-shapes-layouts-and-tile-size)
3. [Atlas sources: regions, margins and separation](#atlas-sources-regions-margins-and-separation)
4. [Alternative tiles: flips, transposes and variants](#alternative-tiles-flips-transposes-and-variants)
5. [Scene collection sources: when a tile is a whole scene](#scene-collection-sources-when-a-tile-is-a-whole-scene)
6. [TileMapLayer: the node that replaced TileMap](#tilemaplayer-the-node-that-replaced-tilemap)
7. [Layer stacking patterns: ground, props, overlay](#layer-stacking-patterns-ground-props-overlay)
8. [Editor workflow: painting tools, random tiles and patterns](#editor-workflow-painting-tools-random-tiles-and-patterns)
9. [Physics on tiles](#physics-on-tiles)
10. [Navigation on tiles](#navigation-on-tiles)
11. [Occlusion and 2D lighting](#occlusion-and-2d-lighting)
12. [Custom data layers: typed per-tile metadata](#custom-data-layers-typed-per-tile-metadata)
13. [Terrains: autotiling in depth](#terrains-autotiling-in-depth)
14. [Scripting tilemaps: the cell API and coordinates](#scripting-tilemaps-the-cell-api-and-coordinates)
15. [Procedural generation: a room generator](#procedural-generation-a-room-generator)
16. [Runtime changes, internals and performance](#runtime-changes-internals-and-performance)
17. [Isometric tilemaps](#isometric-tilemaps)
18. [Case study: Relax Room and the freeform alternative](#case-study-relax-room-and-the-freeform-alternative)
19. [Decision guide: TileMapLayer vs GridMap vs freeform sprites](#decision-guide-tilemaplayer-vs-gridmap-vs-freeform-sprites)
20. [Best practices](#best-practices)
21. [Common errors & troubleshooting](#common-errors--troubleshooting)
22. [Exercises](#exercises)
23. [Further reading](#further-reading)
24. [Glossary](#glossary)

---

## Overview: the Godot 4 tile stack

A **tilemap** is a grid of reusable images — *tiles* — used to assemble a 2D level. Instead of
authoring one enormous bitmap per room, you author a small palette of cells (16×16, 32×32,
64×32…) and paint them onto a grid. The idea is as old as the NES, and it survives because the
economics never stopped being true: memory stays flat while level size grows, collision comes
for free per tile, and iteration happens in minutes instead of paint-over sessions.

In Godot 4 the tile stack has exactly three moving parts, and keeping their roles straight is
half the module:

| Part | Type | Role |
|---|---|---|
| `TileSet` | `Resource` (`.tres`) | The *palette*: which tiles exist, what they look like, what physics/navigation/occlusion/metadata each one carries |
| `TileMapLayer` | `Node2D` subclass | The *canvas*: one grid of placed cells, drawn and simulated in the scene tree |
| `TileData` | `Object` (per tile) | The *record*: runtime view of a single tile's properties, obtained via `get_cell_tile_data()` |

A fourth part, the **TileMap node**, exists only as legacy: it was the all-in-one node of Godot
4.0–4.2 that held every layer internally as an array. Since **Godot 4.3 it is deprecated** in
favor of one `TileMapLayer` node per layer. Everything in this module targets `TileMapLayer`;
the migration path from `TileMap` is covered in
[TileMapLayer: the node that replaced TileMap](#tilemaplayer-the-node-that-replaced-tilemap).

### What a cell actually stores

This is the single most clarifying fact about the whole system. A painted cell does **not**
store an image. It stores three integers-worth of reference data:

```
cell(coords: Vector2i)  ─►  ( source_id:        which source in the TileSet,
                              atlas_coords:     which tile inside that source,
                              alternative_tile: which variant of that tile )
```

Everything else — texture region, collision polygons, navigation polygons, occluders, terrain
membership, custom data — is looked up in the `TileSet` at draw/physics time. Change the
TileSet and every placed cell everywhere updates. This is why the TileSet is described in this
course as *the single source of truth*: the map is a table of foreign keys into it.

```gdscript
# The three components of a cell, read back from a layer:
var layer: TileMapLayer = $Ground
var coords := Vector2i(5, 3)

var source_id: int = layer.get_cell_source_id(coords)          # -1 if empty
var atlas_coords: Vector2i = layer.get_cell_atlas_coords(coords)
var alternative: int = layer.get_cell_alternative_tile(coords)

print("cell %s -> source %d, atlas %s, alt %d" % [coords, source_id, atlas_coords, alternative])
```

### Why tilemaps at all

Compared to hand-placing `Sprite2D` nodes (the approach studied in
[Sprites and Textures](SPRITES_AND_TEXTURES.md)), a tilemap gives you:

- **Memory efficiency.** One 32×32 tile referenced 10,000 times costs one texture region plus
  10,000 tiny cell records — not 10,000 sprites with transforms, canvas items and per-node
  overhead.
- **Batched rendering.** Cells are grouped into *rendering quadrants* (16×16 cells by default)
  that draw as few canvas items, dramatically reducing draw calls versus thousands of nodes.
- **Structural collision.** Draw a polygon once per tile in the TileSet; every placed instance
  collides. No `StaticBody2D` forest in the scene tree.
- **Autotiling.** Terrains pick edge and corner transitions for you while you paint.
- **Editor tooling.** Rect/line/bucket tools, random scattering, saved patterns, terrain
  brushes — a level editor you did not have to write.

And compared to what it costs you:

- **Grid discipline.** Everything lives on the grid. Off-grid art either becomes oversized
  tiles with offsets or leaves the tilemap entirely.
- **Palette authoring.** You need a coherent tileset (consistent light direction, seams,
  transitions). For a game with one hand-painted room, that is real work with no payoff.
- **A second data model.** Your level now lives in `tile_map_data` inside a scene, not in your
  own JSON/resources — relevant if, like Relax Room, you persist layouts yourself (see
  [Database and Persistence](DATABASE_AND_PERSISTENCE.md)).

> ✅ **Best practice** — Decide *data-first*: ask "is my level fundamentally a grid of repeated
> cells?" If yes, tilemaps. If it is a handful of unique artworks with freeform placement,
> sprites. Module section [19](#decision-guide-tilemaplayer-vs-gridmap-vs-freeform-sprites)
> turns this into a checklist.

### The version story, precisely

Because tutorials online mix eras freely, pin the history once:

| Godot version | Tile stack state |
|---|---|
| 3.x | `TileMap` node + old `TileSet` with autotile bitmasks (different API, ignore for this course) |
| 4.0–4.2 | New `TileSet` resource; single `TileMap` node containing multiple *internal* layers (`set_cell(layer, coords, …)`) |
| **4.3** | **`TileMapLayer` introduced; `TileMap` deprecated.** Editor gains "Extract TileMap layers as individual TileMapLayer nodes" |
| 4.4 | `TileMapLayer` gains `physics_quadrant_size` (batched tile physics); occluders become multi-polygon (`get_occluder_polygon`) |
| **4.5 (course pin)** | `TileMapLayer` is the only recommended API; everything in this module verified against it |

> ⚠️ **Pitfall** — Any snippet you find calling `set_cell(layer_index, coords, …)` with a
> *first* integer argument is pre-4.3 `TileMap` code. On `TileMapLayer` the layer is the node
> itself, so `set_cell(coords, source_id, atlas_coords, alternative)` has no layer parameter.
> This one-argument shift is the most common breakage when pasting old tutorials.

### Where this module sits in the course

- [Sprites and Textures](SPRITES_AND_TEXTURES.md) (Module 03) gave you texture import,
  filtering and atlas hygiene — all of it applies to tilesheet textures.
- [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) (Module 04) covered Y-sort,
  `z_index` and draw order — tilemaps consume those concepts wholesale.
- [Isometric Games](ISOMETRIC_GAMES.md) (Module 07) builds on
  [Isometric tilemaps](#isometric-tilemaps) below.
- [Project Deep Dive](PROJECT_DEEP_DIVE.md) documents the Relax Room scene tree this module's
  case study dissects.

---

## TileSet anatomy: shapes, layouts and tile size

A `TileSet` is a `Resource`, which means everything from
[Scenes and Nodes](SCENES_AND_NODES.md) about resources applies: it can be built-in to a
scene or saved as a standalone `.tres`/`.res` file, it is shared by reference, and editing it
updates every user simultaneously.

> ✅ **Best practice** — Always save production TileSets as external `.tres` files
> (`res://tilesets/interior.tres`). Built-in TileSets lock the palette inside one scene, break
> pattern reuse across layers, and turn every palette tweak into a scene-file diff. The
> official docs recommend the same for any reuse scenario.

### Top-level properties

The TileSet resource has a small set of *global* properties that shape everything else:

| Property | Type | Meaning |
|---|---|---|
| `tile_shape` | `TileSet.TileShape` | Geometry of a cell: square, isometric diamond, half-offset square, hexagon |
| `tile_layout` | `TileSet.TileLayout` | How cell coordinates map onto the plane (stacked, stairs, diamond…) — only meaningful for offset shapes |
| `tile_offset_axis` | `TileSet.TileOffsetAxis` | Horizontal vs vertical offset for half-offset/hex shapes |
| `tile_size` | `Vector2i` | The size of one grid cell in pixels (default `16×16`) |
| `uv_clipping` | `bool` | Clip tile textures to their region during rendering (prevents oversized tiles from drawing outside their cell) |

```gdscript
# Building a TileSet's skeleton in code (usually you do this in the editor,
# but the API mirrors it 1:1 and is what procedural pipelines use):
var tile_set := TileSet.new()
tile_set.tile_shape = TileSet.TILE_SHAPE_SQUARE
tile_set.tile_size = Vector2i(32, 32)
```

### The four tile shapes

`tile_shape` selects the cell geometry. It is a property of the whole TileSet — you cannot mix
shapes inside one resource.

| Shape | Enum constant | Grid geometry | Typical use |
|---|---|---|---|
| Square | `TileSet.TILE_SHAPE_SQUARE` | Axis-aligned rectangles | Platformers, top-down RPGs, roguelikes |
| Isometric | `TileSet.TILE_SHAPE_ISOMETRIC` | Diamonds (2:1 ratio is the classic) | Iso city-builders, tactics games, cozy sims — *the Relax Room aesthetic* |
| Half-offset square | `TileSet.TILE_SHAPE_HALF_OFFSET_SQUARE` | Squares where alternate rows/columns shift by half a cell | Brick-like layouts, some hex substitutes |
| Hexagon | `TileSet.TILE_SHAPE_HEXAGON` | True hexagons | Strategy maps, board-game hybrids |

For half-offset and hexagon shapes, `tile_offset_axis` decides whether the *rows* shift
(`TILE_OFFSET_AXIS_HORIZONTAL`, pointy-top hexes) or the *columns* shift
(`TILE_OFFSET_AXIS_VERTICAL`, flat-top hexes).

### Tile layout: how coordinates walk the plane

For square grids, `tile_layout` barely matters. For isometric and offset grids it decides how
the `Vector2i` cell coordinates you script against map to screen positions:

| Layout | Enum constant | Coordinate behavior |
|---|---|---|
| Stacked | `TILE_LAYOUT_STACKED` | Rows stack downward; offset rows shift right (default) |
| Stacked offset | `TILE_LAYOUT_STACKED_OFFSET` | Like stacked, but the *other* rows shift |
| Stairs right | `TILE_LAYOUT_STAIRS_RIGHT` | +X walks down-right like a staircase |
| Stairs down | `TILE_LAYOUT_STAIRS_DOWN` | +Y walks down-left like a staircase |
| Diamond right | `TILE_LAYOUT_DIAMOND_RIGHT` | Axes follow the diamond edges; +X goes down-right, +Y down-left |
| Diamond down | `TILE_LAYOUT_DIAMOND_DOWN` | Diamond axes rotated so +Y goes straight down the screen |

For isometric maps, `TILE_LAYOUT_DIAMOND_DOWN` or `TILE_LAYOUT_DIAMOND_RIGHT` give the
"classic iso" coordinate feel where both axes run along diamond edges — this is what
[Isometric tilemaps](#isometric-tilemaps) assumes, and what the debugging chapter of
[Isometric Games](ISOMETRIC_GAMES.md) uses in its worked examples.

> ⚠️ **Pitfall** — Changing `tile_layout` (or `tile_shape`) on a TileSet that already has
> painted maps *reinterprets every existing cell coordinate*. Your maps will visually scramble
> even though no cell data changed. Lock these properties down at project start; treat a
> late change as a migration project, not a checkbox flip.

### Tile size: the grid cell, not the art

`tile_size` is the size of a *grid cell*, and it is deliberately independent from the size of
any tile texture:

- A square top-down game typically uses `tile_size = Vector2i(32, 32)` with 32×32 art.
- A classic 2:1 isometric game uses `tile_size = Vector2i(64, 32)` — the on-screen diamond —
  while wall and furniture *textures* are 64×64 or taller, hanging above the cell via
  `texture_origin` (covered with atlas sources below).
- Oversized props (a 64×96 tree on a 32×32 grid) occupy one *logical* cell but paint over
  several visual cells.

The rule: **`tile_size` describes the logic grid; textures merely decorate it.** Collision,
navigation and terrain matching all reason in grid cells; rendering happily overflows them
(unless `uv_clipping` is on).

### Layers *inside* the TileSet

Beyond shape and size, the TileSet declares the *schemas* that its tiles can fill in. Each is
an ordered list you manage in the TileSet inspector (or via code):

| TileSet schema | Added with | Per-tile payload |
|---|---|---|
| Physics layers | `add_physics_layer()` | Collision polygons per tile ([section 9](#physics-on-tiles)) |
| Navigation layers | `add_navigation_layer()` | Navigation polygons per tile ([section 10](#navigation-on-tiles)) |
| Occlusion layers | `add_occlusion_layer()` | Light occluder polygons per tile ([section 11](#occlusion-and-2d-lighting)) |
| Custom data layers | `add_custom_data_layer()` | Typed metadata per tile ([section 12](#custom-data-layers-typed-per-tile-metadata)) |
| Terrain sets | `add_terrain_set()` | Peering bits per tile ([section 13](#terrains-autotiling-in-depth)) |

```gdscript
# Declaring schemas from code — the editor UI writes exactly these calls' results:
var ts := TileSet.new()

ts.add_physics_layer()
ts.set_physics_layer_collision_layer(0, 1)        # physics layer 0 -> collision bit 1
ts.set_physics_layer_collision_mask(0, 1)

ts.add_custom_data_layer()
ts.set_custom_data_layer_name(0, "move_cost")
ts.set_custom_data_layer_type(0, TYPE_INT)

ts.add_terrain_set()
ts.set_terrain_set_mode(0, TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES)
ts.add_terrain(0)
ts.set_terrain_name(0, 0, "Carpet")
ts.set_terrain_color(0, 0, Color(0.55, 0.35, 0.55))
```

The mental model to keep: **the TileSet declares columns; each tile fills in rows.** A physics
layer is a column ("collision on layer 0"); each atlas tile then contributes its own polygon
for that column, or nothing.

### Sources: where tiles come from

Finally, the TileSet holds one or more **sources** — the actual suppliers of tiles:

- **Atlas sources** (`TileSetAtlasSource`): tiles cut from a texture sheet. The workhorse;
  next section.
- **Scene collection sources** (`TileSetScenesCollectionSource`): tiles that instantiate whole
  scenes. [Section 5](#scene-collection-sources-when-a-tile-is-a-whole-scene).

Each source gets an integer **source ID**, unique within the TileSet. That ID is the first
component of every painted cell, and the first argument after coordinates in `set_cell()`.

```gdscript
# Enumerating sources:
for i in tile_set.get_source_count():
	var sid := tile_set.get_source_id(i)
	var source := tile_set.get_source(sid)
	print("source %d -> %s" % [sid, source.get_class()])
	# TileSetAtlasSource or TileSetScenesCollectionSource
```

> ✅ **Best practice** — Treat source IDs as stable, public identifiers. Renumbering a source
> orphans every cell painted from it (they render as error placeholders). Godot preserves IDs
> for you; just never "clean them up" manually in a project with existing maps, and consider
> keeping a `const SOURCE_INTERIOR := 0` style constants block in the scripts that paint cells.

---

## Atlas sources: regions, margins and separation

An **atlas source** slices a single texture — a *tilesheet* — into a grid of tiles. It is the
`TileSetAtlasSource` class, and its inspector fields map directly onto properties you can also
set from code.

### Creating one in the editor

1. Select a `TileMapLayer` node and assign a new (or existing) `TileSet` in the inspector.
2. Open the **TileSet** bottom panel.
3. Drag your tilesheet PNG from the FileSystem dock into the left column of the panel.
4. Godot offers to **automatically create tiles in the non-transparent texture regions** —
   accept for dense sheets; decline and hand-place tiles for sparse or irregular sheets.
5. Fine-tune with the **Setup**, **Select** and **Paint** tabs of the atlas view.

The automatic step is worth understanding: Godot scans the sheet in `texture_region_size`
steps and creates a tile wherever it finds any opaque pixel. Fully transparent cells are
skipped. You can erase unwanted tiles later with the eraser in the Setup tab, and re-run
creation from the "three dots" toolbar menu if the texture changes.

> ⚠️ **Pitfall** — Texture *import* settings still matter. A tilesheet imported with default
> filtering will bleed neighboring pixels at tile edges when the camera zooms or moves
> sub-pixel. For pixel art, set the project default texture filter to "Nearest" or per-node
> `CanvasItem.texture_filter = TEXTURE_FILTER_NEAREST` — the full story is in
> [Sprites and Textures](SPRITES_AND_TEXTURES.md).

### The geometry four: region size, margins, separation, padding

Four properties define how the sheet is cut. Getting them wrong produces the classic "my tiles
are all shifted by one pixel" bug.

| Property | Type | Meaning |
|---|---|---|
| `texture_region_size` | `Vector2i` | Size in pixels of one tile region on the sheet — usually equals `TileSet.tile_size`, but may be larger for oversized tiles |
| `margins` | `Vector2i` | Dead pixels at the sheet's top-left before the first tile begins |
| `separation` | `Vector2i` | Dead pixels *between* adjacent tile regions (spacing/gutters baked into the sheet) |
| `use_texture_padding` | `bool` (default `true`) | Godot internally rebuilds the atlas with a 1-pixel duplicated border around each tile to prevent texture bleeding |

Visually:

```
        margins.x
        ◄──►
   ┌────────────────────────────────────────────┐
   │ ▲                                          │
   │ │ margins.y                                │
   │ ▼   ┌────────┐  ┌────────┐  ┌────────┐     │
   │     │ (0,0)  │  │ (1,0)  │  │ (2,0)  │     │
   │     │        │◄►│        │◄►│        │     │   ◄► = separation.x
   │     └────────┘  └────────┘  └────────┘     │
   │          ▲                                 │
   │          │ separation.y                    │
   │          ▼                                 │
   │     ┌────────┐  ┌────────┐  ┌────────┐     │
   │     │ (0,1)  │  │ (1,1)  │  │ (2,1)  │     │
   │     │        │  │        │  │        │     │
   │     └────────┘  └────────┘  └────────┘     │
   │       each box = texture_region_size       │
   └────────────────────────────────────────────┘
```

The pixel rectangle for atlas tile `(c, r)` is therefore:

```
position = margins + (texture_region_size + separation) * Vector2i(c, r)
size     = texture_region_size            # times tile size_in_atlas if oversized
```

`use_texture_padding` deserves a highlight: without it, GPU texture sampling at tile borders
can read the neighboring tile's pixels (half-texel bleed), producing flickering seams — the
single most-reported tilemap rendering artifact. With padding on (the default), Godot copies
each tile into an internal padded atlas at import cost but with clean edges. Leave it on
unless memory profiling on a huge atlas says otherwise.

### Oversized tiles

A tile region can span multiple base cells. In the Setup tab, drag a tile's handles to make it,
say, 1×2 regions tall — a tall bookshelf on a 32×32 grid. Two facts govern oversized tiles:

- They still occupy **one logical cell** in the map. Collision, terrain and neighbors reason
  about that one cell.
- Their visual anchor is controlled by `texture_origin` (a `TileData` property, settable per
  tile in the Select tab). For a 32×64 bookshelf standing on its cell, you shift the texture up
  so the *base* of the art sits in the cell.

This is exactly the mechanism isometric games use for tall walls and furniture — see
[Isometric tilemaps](#isometric-tilemaps).

### Per-tile properties in an atlas

With the **Select** tab active, clicking any tile exposes its *base tile data* — the same
`TileData` record you will later read from code:

| Property | Type | Effect |
|---|---|---|
| `texture_origin` | `Vector2i` | Pixel offset of texture vs cell center — anchors oversized art |
| `modulate` | `Color` | Per-tile tint multiplier |
| `material` | `Material` | Custom `CanvasItemMaterial`/`ShaderMaterial` for this tile (see [Shaders](SHADERS_GDSHADER.md)) |
| `z_index` | `int` | Draw-order offset for cells using this tile |
| `y_sort_origin` | `int` | Vertical offset (pixels) of the Y-sort comparison point |
| `probability` | `float` | Relative weight when painting with random mode ([section 8](#editor-workflow-painting-tools-random-tiles-and-patterns)) |
| terrain, physics, navigation, occlusion, custom data | — | Filled per schema, sections 9–13 |

```gdscript
# Programmatic atlas construction — the pattern used by import pipelines
# and tests. Mirrors what the editor Setup tab does.
var atlas := TileSetAtlasSource.new()
atlas.texture = preload("res://art/tiles/interior_sheet.png")
atlas.texture_region_size = Vector2i(32, 32)
atlas.margins = Vector2i(0, 0)
atlas.separation = Vector2i(0, 0)
atlas.use_texture_padding = true

atlas.create_tile(Vector2i(0, 0))                 # single-cell tile
atlas.create_tile(Vector2i(1, 0), Vector2i(1, 2)) # oversized: 1 wide, 2 tall

var source_id := tile_set.add_source(atlas)       # returns the assigned source ID
print("atlas registered as source ", source_id)

# Reading a tile's data record back:
var td: TileData = atlas.get_tile_data(Vector2i(0, 0), 0)  # atlas_coords, alternative 0
td.probability = 0.25
```

> ✅ **Best practice** — Keep one atlas source per *theme sheet* (interior, garden, dungeon)
> rather than one mega-sheet, and name each source in the inspector. Named sources make the
> painting palette navigable and let artists iterate on one sheet without re-importing
> everything. IDs stay stable per source, so maps survive the reorganization.

---

## Alternative tiles: flips, transposes and variants

Every atlas tile has an implicit **alternative 0** — the base tile. You can create numbered
**alternative tiles** on top of it: variants that share the same texture region but override
some properties. In the editor: Select tab → right-click a base tile → **Create an Alternative
Tile**. Each alternative gets a unique **alternative ID** within that atlas tile, and that ID
is the third component of a painted cell.

### What alternatives can override

| Property | Typical use |
|---|---|
| `flip_h` / `flip_v` | Mirrored props (left/right facing chairs) without duplicate art |
| `transpose` | Swaps texture axes — combined with flips this yields all 90° rotations |
| `texture_origin` | A variant anchored differently (e.g., wall-mounted vs floor-standing) |
| `modulate` | Recolored variants (worn/mossy/dyed versions of one tile) |
| `material` | A shader variant — e.g., only *some* water tiles get the animated shader |
| `z_index`, `y_sort_origin` | Draw-order variants |
| collision / navigation / occlusion polygons | e.g., a "broken fence" alternative with a gap in its collision |
| custom data | Different metadata per variant (a trap tile whose "armed" variant deals damage) |

The one thing an alternative **cannot** change is the texture region itself — that is what
makes it an alternative of *that* tile rather than a new tile.

### Rotations from flips + transpose

There is no rotation angle on tiles. Instead, the three booleans compose into the eight
symmetries of a square (the dihedral group, if you want to impress someone):

| Desired orientation | transpose | flip_h | flip_v |
|---|---|---|---|
| 0° | off | off | off |
| 90° clockwise | on | on | off |
| 180° | off | on | on |
| 270° clockwise (90° CCW) | on | off | on |
| Mirror | off | on | off |
| Mirror + 90° CW | on | on | on |
| Mirror + 180° | off | off | on |
| Mirror + 270° | on | off | off |

When painting, the editor exposes these as keyboard shortcuts (default: **Z** rotates the
brush clockwise, **Shift+Z** counter-clockwise, **X** flips horizontally, **Y** flips
vertically — check *Editor Settings → Shortcuts → Tiles Editor* for your bindings). When
*scripting*, the same flags are baked into the `alternative_tile` integer as bit flags on
`TileSetAtlasSource`:

```gdscript
# The alternative ID namespace reserves high bits for transform flags:
# TileSetAtlasSource.TRANSFORM_FLIP_H = 4096
# TileSetAtlasSource.TRANSFORM_FLIP_V = 8192
# TileSetAtlasSource.TRANSFORM_TRANSPOSE = 16384

var alt := 0 | TileSetAtlasSource.TRANSFORM_FLIP_H   # base tile, mirrored
layer.set_cell(Vector2i(4, 2), source_id, Vector2i(3, 1), alt)

# Reading orientation back without decoding bits:
print(layer.is_cell_flipped_h(Vector2i(4, 2)))   # true
print(layer.is_cell_flipped_v(Vector2i(4, 2)))   # false
print(layer.is_cell_transposed(Vector2i(4, 2)))  # false
```

> ⚠️ **Pitfall** — Transform-flag alternatives and *authored* alternatives are different
> things. `create_alternative_tile()` IDs count 1, 2, 3…; the transform flags occupy bits
> 4096+. A cell can combine both (`authored_id | TRANSFORM_FLIP_H`). If you compare
> `get_cell_alternative_tile()` against a plain ID while painted cells carry flip flags, your
> comparisons silently fail. Mask with
> `alt & ~(TileSetAtlasSource.TRANSFORM_FLIP_H | TileSetAtlasSource.TRANSFORM_FLIP_V | TileSetAtlasSource.TRANSFORM_TRANSPOSE)`
> when you only care about the authored variant.

### When to reach for alternatives

Use an alternative when variants are *property-level* (orientation, tint, metadata, physics
tweak). Create a *separate atlas tile* when the art itself differs. Use *scene tiles* (next
section) when the variant needs behavior. Keeping this ladder in mind prevents both palette
explosion and scene-tile overuse.

```gdscript
# Creating alternatives in code:
var atlas_src := tile_set.get_source(0) as TileSetAtlasSource
var alt_id := atlas_src.create_alternative_tile(Vector2i(3, 1))   # returns new ID (e.g. 1)
var alt_data := atlas_src.get_tile_data(Vector2i(3, 1), alt_id)
alt_data.modulate = Color(0.8, 0.9, 1.0)   # "cold" recolor of the same tile
```

---

## Scene collection sources: when a tile is a whole scene

Atlas tiles are cheap because they are *not nodes* — they render in batched quadrants with no
per-tile scene machinery. But sometimes a "tile" needs to *do* something: emit particles,
play audio, run a script, own an `AnimationPlayer`. That is what a **scene collection source**
(`TileSetScenesCollectionSource`) is for: each tile in it is a `PackedScene`, and every painted
cell **instantiates that scene as a child of the TileMapLayer**, positioned at the cell.

### Setting one up

1. In the TileSet bottom panel, click **Add** (the `+`) → **Scenes Collection**.
2. Drag `.tscn` files into the source. Each becomes a scene tile with its own ID.
3. Paint them like any other tile — the editor shows the scene's icon/preview.

```gdscript
# Programmatic equivalent:
var scenes := TileSetScenesCollectionSource.new()
var torch_id := scenes.create_scene_tile(preload("res://props/wall_torch.tscn"))
var fountain_id := scenes.create_scene_tile(preload("res://props/fountain.tscn"))
var scenes_source_id := tile_set.add_source(scenes)

# Painting a scene tile: atlas_coords is always Vector2i.ZERO,
# the scene is selected by the *alternative* argument:
layer.set_cell(Vector2i(8, 4), scenes_source_id, Vector2i.ZERO, torch_id)
```

Note the quirk: for scene tiles, `atlas_coords` is meaningless (always `(0, 0)`) and the
**alternative ID selects which scene**. This trips up everyone once.

### What you gain and what you pay

| | Atlas tile | Scene tile |
|---|---|---|
| Rendering | Batched in quadrants | One node tree per cell |
| Behavior | None (data only) | Full scripts, signals, animation, audio |
| Physics | Merged tile collision | Whatever bodies the scene contains |
| Cost per 1,000 cells | Trivial | 1,000 scene instances — very real |
| Editing | TileSet panel | The scene itself (updates everywhere) |

> ✅ **Best practice** — Scene tiles are for *sparse, behavioral* cells: torches, spawners,
> chests, checkpoints, one-off interactive props. If you are painting hundreds of the same
> scene tile, redesign: keep visuals as atlas tiles and drive behavior from a manager script
> that reads [custom data](#custom-data-layers-typed-per-tile-metadata) or cell positions.

> ⚠️ **Pitfall** — Scene tiles are instantiated when the layer enters the tree and when cells
> change, and the instances are *children of the layer*. Do not hand-reparent or free them —
> erase the cell instead, or the layer's bookkeeping desynchronizes from the scene tree.

### Scene tiles vs "just placing scenes"

A fair question: why not simply instance `wall_torch.tscn` as a normal child of the level?
Because scene tiles participate in the *grid workflow*: they snap to cells, they are painted
and erased with the same tools as ground tiles, they serialize inside `tile_map_data`, and
level designers never leave the TileMap editor. If your placement is not grid-aligned or not
level-designer-driven, ordinary scene instancing is simpler — that is exactly the trade Relax
Room made for decorations, as [section 18](#case-study-relax-room-and-the-freeform-alternative)
shows.

---

## TileMapLayer: the node that replaced TileMap

`TileMapLayer` is a `Node2D` that renders and simulates **one grid of cells** using one
`TileSet`. Where Godot 4.0–4.2 packed multiple layers *inside* a single `TileMap` node (with
every API call taking a `layer` index), 4.3+ makes each layer a first-class node.

### Why the split happened

The layered-inside-one-node design had accumulated real problems:

- **API noise.** Every one of the ~40 cell methods needed a `layer` first argument;
  layer-level properties needed `set_layer_*` twins (`set_layer_modulate`,
  `set_layer_y_sort_enabled`, …) duplicating what `Node2D`/`CanvasItem` already offered.
- **Inspector clutter.** Layers lived in a custom list widget instead of the scene tree; you
  could not select one, script one, or group one.
- **No per-layer node powers.** You could not give a single layer its own material, shader,
  visibility notifier, tween, or child nodes — all trivial once a layer *is* a node.
- **Composition beats configuration.** One node per layer matches Godot's design language
  everywhere else (think `CanvasLayer`, `CollisionShape2D`): build structure in the tree, not
  in nested inspector arrays.

Since 4.3, `TileMap` still loads for compatibility but is formally deprecated, and the
official docs' tilemap tutorials are written exclusively against `TileMapLayer`.

### Migrating a legacy TileMap

For scenes created in 4.0–4.2:

1. Select the old `TileMap` node.
2. Open the **TileMap** bottom panel and click the toolbox icon (top-right of the panel).
3. Choose **Extract TileMap layers as individual TileMapLayer nodes**.
4. Godot creates one `TileMapLayer` sibling per internal layer, copying cells, per-layer
   modulate/Y-sort/Z-index, and the TileSet reference. Verify, then delete the old node.

Code migration is mechanical:

| Godot 4.2 (`TileMap`) | Godot 4.3+ (`TileMapLayer`) |
|---|---|
| `tilemap.set_cell(0, coords, sid, atlas)` | `ground_layer.set_cell(coords, sid, atlas)` |
| `tilemap.get_used_cells(1)` | `props_layer.get_used_cells()` |
| `tilemap.set_layer_modulate(1, c)` | `props_layer.modulate = c` |
| `tilemap.set_layer_enabled(2, false)` | `overlay_layer.enabled = false` |
| `tilemap.set_layer_y_sort_enabled(1, true)` | `props_layer.y_sort_enabled = true` (inherited from `Node2D`) |
| `tilemap.set_layer_z_index(1, 5)` | `props_layer.z_index = 5` (inherited from `CanvasItem`) |
| `tilemap.map_to_local(coords)` | unchanged — `layer.map_to_local(coords)` |

> ⚠️ **Pitfall** — The one-click extractor only works on scenes you can open directly. A
> `TileMap` embedded in an instanced scene or serialized inside a `.tres` needs the owning
> scene opened and converted there, or a manual rebuild (create `TileMapLayer` nodes, assign
> the same TileSet, copy cells via script with `get_used_cells()` + `set_cell()`).

### The property surface, verified against 4.5

Because `TileMapLayer` is "just" a `Node2D`, its effective API is the union of its own
properties and everything inherited. The own properties, from the class reference:

| Property | Type / default | Meaning |
|---|---|---|
| `tile_set` | `TileSet` | The palette this layer paints from |
| `tile_map_data` | `PackedByteArray` | The serialized cell database (what the scene file stores) |
| `enabled` | `bool = true` | Master switch: disables rendering *and* physics *and* navigation while keeping data |
| `collision_enabled` | `bool = true` | Toggle tile physics bodies for this layer |
| `collision_visibility_mode` | `DebugVisibilityMode = 0` | Debug drawing of tile collision (default / force show / force hide) |
| `use_kinematic_bodies` | `bool = false` | Back tiles with kinematic instead of static bodies (moving-platform layers) |
| `physics_quadrant_size` | `int = 16` | Cells per merged physics quadrant (4.4+) |
| `navigation_enabled` | `bool = true` | Toggle tile navigation regions |
| `navigation_visibility_mode` | `DebugVisibilityMode = 0` | Debug drawing of tile navmesh |
| `occlusion_enabled` | `bool = true` | Toggle tile light occluders |
| `rendering_quadrant_size` | `int = 16` | Cells per rendering batch quadrant |
| `x_draw_order_reversed` | `bool = false` | With Y-sort: draw same-row tiles right-to-left (isometric tie-breaker) |
| `y_sort_origin` | `int = 0` | Layer-wide Y-sort offset in pixels, added to each tile's own |

Plus the inherited essentials you will use constantly:

```gdscript
var layer := TileMapLayer.new()
layer.tile_set = preload("res://tilesets/interior.tres")
layer.modulate = Color(1, 1, 1, 1)     # CanvasItem — tint/fade the whole layer
layer.z_index = 0                      # CanvasItem — stack order
layer.y_sort_enabled = false           # Node2D — per-cell Y ordering (see section 7)
layer.visible = true                   # CanvasItem
layer.position = Vector2.ZERO          # Node2D — yes, layers can be offset/scaled/rotated
add_child(layer)
```

And the signal: `changed` — emitted when the layer's content or configuration mutates
(cells painted, TileSet swapped…). Useful for minimap/refresh logic:

```gdscript
func _ready() -> void:
	$Ground.changed.connect(_on_ground_changed)

func _on_ground_changed() -> void:
	_minimap.queue_redraw()
```

### `enabled` vs `visible`

Two switches that look alike but are not:

- `visible = false` hides rendering; **collision and navigation stay live**. An invisible
  wall layer still blocks the player.
- `enabled = false` suspends the layer wholesale — rendering, physics bodies, navigation
  regions, occluders — while `tile_map_data` is preserved. This is the switch for "this floor
  of the building is not active right now".

> ✅ **Best practice** — For room/floor streaming in a companion app, prefer toggling
> `enabled` over freeing and rebuilding layers: the cell database stays in memory (cheap) and
> re-enabling is far faster than re-instantiating and re-painting.

### Debug visibility: seeing collision while you build

`collision_visibility_mode` (and its navigation twin) takes the `DebugVisibilityMode` enum:

| Constant | Value | Behavior |
|---|---|---|
| `DEBUG_VISIBILITY_MODE_DEFAULT` | 0 | Follow the global debug setting |
| `DEBUG_VISIBILITY_MODE_FORCE_SHOW` | 1 | Always draw tile collision/nav shapes, even in release runs |
| `DEBUG_VISIBILITY_MODE_FORCE_HIDE` | 2 | Never draw them, even with debug on |

"The global debug setting" is **Debug → Visible Collision Shapes** in the editor: with it
checked, a running game overlays every tile collision polygon (and navigation with **Visible
Navigation**). This is your first stop for "why does my character stop here?" — before reading
a single line of code, *look* at what the physics server believes.

> ⚠️ **Pitfall** — Force-show modes render in exported release builds too. Ship with
> `DEFAULT`, and gate any diagnostic overlay behind `OS.is_debug_build()`.

---

## Layer stacking patterns: ground, props, overlay

One layer is rarely enough. The canonical production stack for a top-down or isometric scene
is three to five `TileMapLayer` nodes sharing one TileSet:

```
Room (Node2D)
├── Ground     (TileMapLayer)   z_index 0, no Y-sort   ← floors, carpets, terrain
├── GroundDeco (TileMapLayer)   z_index 0, no Y-sort   ← cracks, rugs, stains (no collision)
├── Props      (TileMapLayer)   y_sort_enabled = true  ← walls, furniture, anything with height
├── Overlay    (TileMapLayer)   z_index 10             ← canopy, arches, fog — draws OVER actors
└── Player     (CharacterBody2D)
```

Why split at all, when a single layer could hold every tile?

1. **One tile per cell per layer.** A cell holds exactly one tile. A rug *on* a wooden floor
   requires two layers, or a pre-composited "rug on wood" tile for every combination — the
   combinatorial explosion nobody wants.
2. **Different rules per layer.** Ground never collides and never Y-sorts. Props collide and
   Y-sort. Overlay draws above everything and usually has collision disabled. Encoding these
   as per-node properties is exactly what the 4.3 split was for.
3. **Different update cadence.** A procedural game may regenerate `Ground` wholesale while
   `Props` persists; separate nodes localize the rebuild cost
   ([section 16](#runtime-changes-internals-and-performance)).
4. **Selective effects.** Fading the `Overlay` to reveal the player under a canopy is one
   `modulate` tween on one node. With internal layers it used to be `set_layer_modulate`
   bookkeeping.

```gdscript
# The canopy fade — a classic overlay-layer trick:
func _on_canopy_area_body_entered(body: Node2D) -> void:
	if body is CharacterBody2D:
		var tween := create_tween()
		tween.tween_property($Overlay, "modulate:a", 0.35, 0.2)

func _on_canopy_area_body_exited(_body: Node2D) -> void:
	var tween := create_tween()
	tween.tween_property($Overlay, "modulate:a", 1.0, 0.2)
```

### Y-sort across layers and actors

Recall from [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md): with
`y_sort_enabled`, a `Node2D` draws its children ordered by their global Y position instead of
tree order — and the sorting *pool* is the set of Y-sorted siblings under a Y-sorted parent.

For actors to interleave with props (player walks in front of the sofa, then behind it), the
**parent**, the **props layer** and the **actor** must all opt in:

```
Room (Node2D)                 y_sort_enabled = true   ← the arbiter
├── Ground (TileMapLayer)     y_sort_enabled = false  ← ignores the contest, draws first (z or tree order)
├── Props  (TileMapLayer)     y_sort_enabled = true   ← its CELLS join the contest individually
└── Player (CharacterBody2D)  y_sort_enabled = true   ← joins the contest
```

When a `TileMapLayer` has `y_sort_enabled`, its cells stop batching as one blob and are
ordered cell-by-cell against the other Y-sorted participants, using each cell's Y position
plus `y_sort_origin` (tile-level + layer-level). That is what makes "walk behind the
bookshelf" work — and it has a rendering cost examined in
[section 16](#runtime-changes-internals-and-performance).

> ⚠️ **Pitfall** — Y-sort only interleaves nodes under a **common Y-sorted parent**. A player
> that is a sibling of `Room` rather than a child will never sort against the props, no matter
> what flags are set on the layer. When "Y-sort does nothing", check the parent first.

> ✅ **Best practice** — Y-sort only the layers that need it. Ground and overlay layers should
> keep `y_sort_enabled = false` so they render as cheap batched quadrants; reserve per-cell
> sorting for the props layer where actors actually interleave.

### How many layers is too many

Each layer costs: its own quadrant set (draw items), its own physics bodies, its own
navigation regions, one more node to update. Five layers is a comfortable stack; fifty is a
design smell (you are probably encoding *data* — biome, damage state, moisture — as layers
when it belongs in [custom data](#custom-data-layers-typed-per-tile-metadata) or alternative
tiles). The practical ceiling is "as few as your draw-order and rules require".

---

## Editor workflow: painting tools, random tiles and patterns

Scripting is this course's center of gravity, but the TileMap editor is where levels actually
get built, and knowing its tools cold makes you an order of magnitude faster. Select any
`TileMapLayer` node: the **TileMap** bottom panel opens with two tabs — **Tiles** (paint from
the palette) and **Terrains** (paint with autotiling, [section 13](#terrains-autotiling-in-depth))
— plus the **Patterns** tab inside Tiles.

### The toolbar, tool by tool

| Tool | Use | Power details |
|---|---|---|
| **Selection (S)** | Select painted cells | Shift+click appends, Ctrl+click removes; Ctrl+C/Ctrl+V copy-paste selections as a floating brush; Delete clears |
| **Paint (D)** | Stamp the current brush | Right-click erases; Shift+click draws a straight line from the last point; Ctrl+Shift drags a rectangle |
| **Line (L)** | Single-tile-thick lines | Respects multi-tile brushes as repeating patterns |
| **Rect (R)** | Axis-aligned filled rectangles | Repeats a multi-tile brush across the area |
| **Bucket (B)** | Flood fill | **Contiguous** checkbox (on by default) fills the connected region of same tiles; off = replace every matching tile on the layer |
| **Picker (P)** | Sample tiles from the map | Also: hold Ctrl with Paint active to pick without switching tools |
| **Eraser (E)** | Erase mode toggle | Combines with Paint/Line/Rect/Bucket — e.g., Eraser+Rect erases a rectangle |

The brush itself can be *multiple* tiles: drag-select several tiles in the palette and the
selection paints as a stamp. This is how multi-cell furniture drawn as separate tiles
(sofa-left + sofa-right) is placed in one click.

While painting, the transform shortcuts rotate/flip the brush by toggling the alternative-tile
transform bits from [section 4](#alternative-tiles-flips-transposes-and-variants) — no extra
art, no extra tiles.

### Random painting: scattering and probability

Toggle the **random tile placement** die icon in the toolbar and select several palette tiles:
each stamp now picks one at random. Two dials shape the distribution:

- **Scattering** (toolbar spinbox): probability of painting *nothing* for a given cell.
  `0.0` paints every cell; higher values leave organic gaps. Works with Paint, Line, Rect and
  Bucket.
- **`probability`** (per-tile `TileData` property, painted in the TileSet's Select tab): the
  relative *weight* of each tile within the random pool. A tile with `probability 0.1` among
  tiles at `1.0` appears roughly once per ten placements.

The combination is the standard recipe for natural ground: a base grass tile at weight 1.0,
three flower/pebble variants at 0.1–0.2, painted with the bucket over the whole meadow.

```gdscript
# probability is data, so procedural generators can reuse the same weights:
var td := atlas_src.get_tile_data(Vector2i(2, 0), 0)
td.probability = 0.15    # rare variant, both for the editor brush and for your own RNG
```

> ✅ **Best practice** — Author variation *into the TileSet* (weights on tiles) rather than
> into the painter's habits. Weighted tiles make every future bucket-fill — and every
> procedural pass — consistent with the art direction, with zero extra discipline.

### The patterns library

Some arrangements recur: a 3×3 fountain, a bed with nightstand, a door frame with its two
side pillars. The **Patterns** tab stores them:

1. With the Selection tool, select the arrangement on the map.
2. Ctrl+C to lift it, then Ctrl+V… into the **Patterns** tab area to store it (or drag the
   selection into the tab).
3. Click a stored pattern any time to load it as the current brush.

Patterns are stored **in the TileSet resource** (`add_pattern()` / `get_pattern()` /
`get_patterns_count()` on `TileSet`, as `TileMapPattern` objects). Saved into the external
`.tres`, they travel with the palette to every layer and every scene — one more reason the
external-file rule from [section 2](#tileset-anatomy-shapes-layouts-and-tile-size) matters.

Patterns also have a scripting API on the layer, which procedural generators exploit to stamp
authored chunks (see [section 15](#procedural-generation-a-room-generator)):

```gdscript
# Stamp a stored pattern at a map position:
var pattern: TileMapPattern = layer.tile_set.get_pattern(0)
layer.set_pattern(Vector2i(10, 6), pattern)

# Or lift a live region into a pattern at runtime:
var cells: Array[Vector2i] = [Vector2i(0, 0), Vector2i(1, 0), Vector2i(0, 1), Vector2i(1, 1)]
var lifted: TileMapPattern = layer.get_pattern(cells)
```

### Shortcut card

The defaults worth memorizing (verify against *Editor Settings → Shortcuts → Tiles Editor*
if your bindings differ):

| Keys | Action |
|---|---|
| **S / D / L / R / B / P / E** | Selection / Paint / Line / Rect / Bucket / Picker / Eraser |
| **Ctrl (held, while painting)** | Temporary picker — sample under the cursor |
| **Shift + click (Paint)** | Straight line from last placed cell |
| **Ctrl + Shift + drag (Paint)** | Rectangle |
| **Z / Shift+Z** | Rotate brush clockwise / counter-clockwise (transform bits) |
| **X / Y** | Flip brush horizontally / vertically |
| **Ctrl+C / Ctrl+V** | Copy / paste selection as floating brush (paste into Patterns tab to store) |
| **Delete** | Clear selected cells |
| **F** (TileSet polygon editors) | Stamp a full-cell rectangle polygon |

Ten minutes of deliberate practice with these turns level blocking from a chore into
sketching.

### Missing and invalid tiles

Delete a tile (or a whole source) from the TileSet and any painted cells referencing it render
as error placeholders in the editor — but the *cell data is preserved*, so restoring the
source heals the map. If the removal is intentional, `fix_invalid_tiles()` scrubs the orphans:

```gdscript
layer.fix_invalid_tiles()   # deletes every cell whose (source, atlas, alt) no longer resolves
```

> ⚠️ **Pitfall** — Run `fix_invalid_tiles()` only after confirming the palette change is
> final. It is a data deletion, and "the artist renamed the sheet and re-imported" is not the
> moment to scrub — that is the moment to fix the source's texture reference.

---

## Physics on tiles

Tile collision turns a painted wall into a physical wall. The design is strictly two-phase:
the **TileSet declares physics layers** (the schema), and **each tile contributes polygons**
to those layers (the data). At runtime, the `TileMapLayer` feeds merged static bodies to the
physics server — no `StaticBody2D` nodes appear in your tree.

### Step 1 — physics layers on the TileSet

In the TileSet inspector: **Physics Layers → Add Element**. Each element carries:

- **Collision Layer** — which physics layers these tile bodies *occupy* (bit flags).
- **Collision Mask** — which layers they *scan*. For static scenery the mask usually stays
  default; bodies moving into the tiles do the detecting.
- **Physics Material** — optional friction/bounce override for every polygon on this layer.

```gdscript
# Code equivalent (from section 2, now with meaning):
ts.add_physics_layer()
ts.set_physics_layer_collision_layer(0, 1)      # occupy bit 1 ("world")
ts.set_physics_layer_collision_mask(0, 0)       # scan nothing; movers detect us
```

Multiple physics layers exist for *semantics*, not shapes: e.g., layer 0 = solid walls
(collides with everything), layer 1 = "water" (collides only with non-swimmers). One tile can
carry polygons on several physics layers at once.

### Step 2 — polygons per tile

In the TileSet panel, **Select** tab, pick a tile and expand *Physics → Physics Layer 0*.
The polygon editor appears over the tile preview:

- Press **F** to stamp a full-cell rectangle — the 90% case for walls.
- Click to place vertices for custom shapes (slopes, half-tiles, rounded corners);
  right-click removes a vertex.
- A tile may hold **multiple polygons** per layer (`add_collision_polygon()` in code).
- Use **Paint** mode on the *Physics* property to stamp the same polygon across many tiles
  in one sweep — the bulk-assignment workflow for "every tile in this row is solid".

Per polygon, two extra switches:

- **One Way** — the polygon only blocks bodies arriving against its top face (classic
  jump-through platforms). **One Way Margin** tunes tolerance.
- Per layer, tiles can also carry **constant linear/angular velocity** — conveyor-belt tiles
  that push bodies standing on them (`get_constant_linear_velocity()` on `TileData`).

```gdscript
# Reading collision data back at runtime — e.g., for a debug overlay or a tool:
var td: TileData = layer.get_cell_tile_data(Vector2i(5, 3))
if td != null:
	var count := td.get_collision_polygons_count(0)         # physics layer 0
	for i in count:
		var points: PackedVector2Array = td.get_collision_polygon_points(0, i)
		var one_way: bool = td.is_collision_polygon_one_way(0, i)
		print("polygon %d: %d points, one_way=%s" % [i, points.size(), one_way])
```

### One-way platforms: the complete mini-setup

Because one-way tiles combine three separate settings, here is the whole recipe in one
place — the jump-through platforms of every platformer:

1. **TileSet**: physics layer 0 exists; the platform tile has a *thin* collision polygon
   along its top edge (a full-cell box makes the "pass through from below" window feel
   wrong — a strip 4–6 px tall reads best at 32 px tiles).
2. **Polygon flags**: select that polygon in the tile's physics editor and enable
   **One Way**; leave **One Way Margin** at default unless fast falls tunnel through, then
   raise it a few pixels.
3. **The body**: `CharacterBody2D` needs nothing special to *land* — one-way blocking is
   resolved by the physics server. Drop-through on demand is gameplay code: the standard
   trick is briefly ignoring the collision, e.g. temporarily disabling the body's collision
   mask bit for the platform layer while "down" is held, restoring it after a short timer
   or once clear.

```gdscript
# Drop-through: momentarily stop scanning the platform physics layer (bit 2 here).
func _physics_process(delta: float) -> void:
	if Input.is_action_just_pressed(&"move_down") and is_on_floor():
		set_collision_mask_value(2, false)
		get_tree().create_timer(0.25).timeout.connect(
			set_collision_mask_value.bind(2, true))
	# …normal movement…
```

This is also the cleanest argument for **multiple physics layers on the TileSet**
(solid walls on physics layer 0 / mask bit 1, platforms on physics layer 1 / mask bit 2):
the drop-through toggle switches one mask bit without ever letting the player fall through
actual walls.

### How the runtime assembles bodies

Since 4.4, tile collision is grouped into **physics quadrants** (`physics_quadrant_size`,
default 16 cells): all polygons within a quadrant merge into shared static bodies, keeping
the physics server's body count low even on huge maps. Consequences worth knowing:

- **Identifying "which tile did I hit"** from a collision requires mapping the body RID back
  to a cell: `layer.get_coords_for_body_rid(body_rid)` (with `has_body_rid()` to guard). A
  `KinematicCollision2D` or a `body_shape_entered` signal gives you the RID.
- `use_kinematic_bodies = true` swaps the merged static bodies for kinematic ones — required
  if you *move the layer itself* (a scrolling hazard wall, an elevator platform layer) and
  want proper collision response for bodies riding it.

```gdscript
# "What tile did the player just bump into?"
func _physics_process(_delta: float) -> void:
	var collision := move_and_collide(velocity * _delta)
	if collision:
		var collider := collision.get_collider()
		if collider is TileMapLayer:
			var rid := collision.get_collider_rid()
			if collider.has_body_rid(rid):
				var cell: Vector2i = collider.get_coords_for_body_rid(rid)
				var td := collider.get_cell_tile_data(cell)
				if td and td.get_custom_data("breakable"):
					collider.erase_cell(cell)     # smash-through wall
```

### Seeing it: debug visibility revisited

Everything from the `collision_visibility_mode` discussion in
[section 6](#tilemaplayer-the-node-that-replaced-tilemap) applies here — during development,
run with **Debug → Visible Collision Shapes** enabled and the tile polygons draw themselves.
Nine out of ten "collision doesn't work" reports are visible instantly: the polygon is on the
wrong physics layer, the polygon was never stamped on that one tile variant, or the layer has
`collision_enabled = false`.

> ⚠️ **Pitfall** — Collision polygons belong to a *tile*, not to a cell. If you created an
> alternative tile after drawing the base tile's polygon, the alternative inherited a copy at
> creation time — but polygons added to the base *later* do not propagate to existing
> alternatives. Audit alternatives after physics edits, or author physics before variants.

> ✅ **Best practice** — Keep tile collision *coarse*. Boxes and simple slopes simulate faster
> and merge better into quadrants than 20-vertex tracings of the art. Physics does not need to
> hug every pixel of a skirting board; it needs to feel right at gameplay scale.

---

## Navigation on tiles

Navigation answers "where can agents walk?", and tiles can answer it declaratively: mark the
walkable polygon on each floor tile and the map *is* the navmesh. As with physics, the schema
lives on the TileSet, the data on tiles, and the runtime upload is automatic.

### Tile-based navigation setup

1. TileSet inspector → **Navigation Layers → Add Element**. Each element exposes **Layers**
   bit flags (`set_navigation_layer_layers()` in code) that agents filter against with their
   own `navigation_layers` mask.
2. TileSet panel → **Select** tab → pick a floor tile → *Navigation → Navigation Layer 0* →
   draw the walkable polygon (**F** for full cell, vertices for partial walkability — e.g.,
   a floor tile whose edge is occupied by a hedge).
3. On the `TileMapLayer`, leave `navigation_enabled = true`. Every painted cell now
   contributes its navigation polygon to the default 2D navigation map.
4. Give NPCs a `NavigationAgent2D` and standard pathfinding "just works":

```gdscript
# Minimal agent driving across tile navigation:
extends CharacterBody2D

@export var speed := 120.0
@onready var _agent: NavigationAgent2D = $NavigationAgent2D

func go_to(target_global: Vector2) -> void:
	_agent.target_position = target_global

func _physics_process(_delta: float) -> void:
	if _agent.is_navigation_finished():
		velocity = Vector2.ZERO
	else:
		var next := _agent.get_next_path_position()
		velocity = global_position.direction_to(next) * speed
	move_and_slide()
```

Debugging mirrors physics: `navigation_visibility_mode` on the layer, and **Debug → Visible
Navigation** globally, draw the tile navmesh over the running game.

> ⚠️ **Pitfall** — Navigation region setup is not instantaneous: the navigation server
> synchronizes on the *next physics frame*. Querying a path on the very first frame of a
> freshly loaded map returns garbage. Defer the first query
> (`await get_tree().physics_frame`) — the classic "pathfinding works except on frame one"
> bug, doubly common with tilemaps because they are big nodes that populate late.

### Tile-based vs baked navigation

Tile navigation polygons are convenient but structurally naive: the map contributes **one
small region per cell**, and the navigation server stitches thousands of edge connections.
The alternative is *baking*: one `NavigationRegion2D` with a `NavigationPolygon` that parses
source geometry (including tilemap collision or meshes) into a single coherent navmesh.

| | Tile-based (polygons on tiles) | Baked (`NavigationRegion2D`) |
|---|---|---|
| Authoring | Free with the TileSet | One extra node + bake step |
| Runtime updates | Automatic per `set_cell` | Re-bake (can run on a thread: `bake_navigation_polygon(true)`) |
| Server load | Thousands of merged micro-regions | One region, few polygons |
| `agent_radius` support | No — paths hug walls | Yes — mesh shrinks by agent size |
| Path quality | Zig-zag prone near cell borders | Smooth, fewer corners |
| Best for | Small/medium maps, frequently edited cells | Large static maps, quality-sensitive movement |

The official navigation docs flag the tilemap case explicitly: parsing a tilemap at runtime
is performance-intensive because *every used cell* contributes polygons. For a large static
level, bake once; for a small dynamic board (or a room the player renovates tile by tile),
tile-based wins on simplicity.

> ✅ **Best practice** — Do not mix the two systems on the same cells. Overlapping tile
> regions and a baked region double-report the same walkable area, and agents oscillate at
> the seams. Pick one strategy per map; if you bake, leave tile navigation polygons out of
> the TileSet (or disable `navigation_enabled` on the layer).

### Grid pathfinding without the navigation server: `AStarGrid2D`

For strictly cell-based movement — tactics games, roguelikes, a companion character that
walks tile to tile — the navigation server is often the wrong abstraction: you do not want
smooth any-angle paths, you want *sequences of cells*. Godot ships a dedicated class for
exactly this, and it pairs beautifully with the tile stack: **`AStarGrid2D`**, an
A* implementation specialized for rectangular grids (no graph-building boilerplate).

The integration pattern: size the grid from `get_used_rect()`, mark solids from the wall
layer (or from custom data), weight cells from a `move_cost` custom data layer, and convert
the resulting cell path to pixels with `map_to_local()`:

```gdscript
class_name TileGridPathfinder
extends RefCounted

var _astar := AStarGrid2D.new()
var _ground: TileMapLayer
var _walls: TileMapLayer

func setup(ground: TileMapLayer, walls: TileMapLayer) -> void:
	_ground = ground
	_walls = walls

	var rect := ground.get_used_rect()
	_astar.region = rect                              # supports negative coords directly
	_astar.cell_size = Vector2(ground.tile_set.tile_size)
	_astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
	_astar.default_compute_heuristic = AStarGrid2D.HEURISTIC_MANHATTAN
	_astar.update()                                   # allocate AFTER configuring

	for cell in ground.get_used_cells():
		# Solid if the walls layer occupies the cell:
		if _walls.get_cell_source_id(cell) != -1:
			_astar.set_point_solid(cell, true)
			continue
		# Weighted by tile metadata (defaults to 1.0):
		var td := ground.get_cell_tile_data(cell)
		if td:
			var cost: int = td.get_custom_data("move_cost")
			_astar.set_point_weight_scale(cell, maxf(1.0, float(cost)))

func cell_path(from_cell: Vector2i, to_cell: Vector2i) -> Array[Vector2i]:
	if not _astar.is_in_boundsv(to_cell) or _astar.is_point_solid(to_cell):
		return []
	return _astar.get_id_path(from_cell, to_cell)

func world_path(from_global: Vector2, to_global: Vector2) -> PackedVector2Array:
	var from_cell := _ground.local_to_map(_ground.to_local(from_global))
	var to_cell := _ground.local_to_map(_ground.to_local(to_global))
	var points := PackedVector2Array()
	for cell in cell_path(from_cell, to_cell):
		points.append(_ground.to_global(_ground.map_to_local(cell)))
	return points
```

Notes worth internalizing:

- **`region` accepts the used rect verbatim**, negative coordinates included — no index
  translation layer needed between the tilemap and the pathfinder.
- **`update()` must follow configuration** (region/cell size/modes); reconfigure + `update()`
  again after map regeneration. For single-cell edits, `set_point_solid()` is incremental
  and cheap — perfect inside a build/dig game's `set_cell` wrapper.
- **Weights come from data.** The `move_cost` custom data layer from
  [section 12](#custom-data-layers-typed-per-tile-metadata) drives the pathfinder with zero
  duplicated tables: mud costs 3, carpet costs 1, and level designers tune it in the
  TileSet panel.
- **Isometric maps work unchanged**: map coordinates form a rectangular lattice regardless
  of `tile_shape`, and `map_to_local()` translates the path into diamond-space pixels. Only
  your *heuristic intuition* changes, not the code.
- Choose per use: `AStarGrid2D` for cell-stepped movement and tactical range queries;
  `NavigationAgent2D` (tile-based or baked) for free movement with avoidance. Shipping both
  in one game — agents for NPC wandering, the grid for a placement-range preview — is
  common and fine.

Cross-reference: agent behavior, avoidance and the navigation servers get full treatment in
the course's AI-adjacent material; here we only wire tiles into the system.

---

## Occlusion and 2D lighting

If your scene uses 2D lights ([Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md)
covered `PointLight2D`, `DirectionalLight2D` and `LightOccluder2D`), walls painted on a
tilemap can cast shadows — again declaratively.

### Setup

1. TileSet inspector → **Occlusion Layers → Add Element**. Each layer has a **Light Mask**
   (which lights it blocks, `set_occlusion_layer_light_mask()`) and an **SDF Collision**
   toggle (participation in signed-distance-field effects used by some shaders).
2. TileSet panel → **Select** → wall tile → *Occlusion → Occlusion Layer 0* → draw the
   occluder polygon. Usually the tile's silhouette, often just the full cell rect.
3. On the layer, `occlusion_enabled = true` (default). Painted walls now block any
   `PointLight2D` whose shadow is enabled and whose light mask matches.

Since Godot 4.4, a tile can hold **multiple occluder polygons per occlusion layer** — the
code-side accessor is `TileData.get_occluder_polygon(layer_id, polygon_index)`, which
supersedes the deprecated single-polygon `get_occluder(layer_id)`.

```gdscript
var td := layer.get_cell_tile_data(wall_cell)
if td:
	var occ: OccluderPolygon2D = td.get_occluder_polygon(0, 0)
	if occ:
		print("occluder points: ", occ.polygon.size())
```

### Design notes for tile occlusion

- Occluders are about *shadows*, not visibility of the tile itself. A torch in a tile-walled
  dungeon reads dramatically better with wall occluders — the light pools in the corridor
  instead of leaking through masonry.
- Full-cell occluders on every wall tile produce hard, blocky shadow edges. For softer
  results, inset the polygon a couple of pixels from the tile border, and consider the
  light's shadow filter quality.
- Occlusion is per-tile data: door tiles simply *don't* get an occluder, and light spills
  through doorways with zero extra logic — a lovely emergent win of the declarative model.

> ⚠️ **Pitfall** — An occluder polygon that exactly coincides with the light's position
> (a torch *inside* a wall cell) makes the light appear dead. Keep light sources out of
> occluder-bearing cells, or shrink the occluder so the emitter sits outside it.

---

## Custom data layers: typed per-tile metadata

Custom data is the feature that turns a tilemap from scenery into a *queryable world model*.
The TileSet declares named, typed fields; every tile fills them; gameplay code reads them
through the cell under any position. Footstep sounds, movement costs, "is this water",
"can decorations be placed here" — all belong in custom data, not in parallel arrays or
name-based hacks.

### Declaring the schema

TileSet inspector → **Custom Data Layers → Add Element**, then per element set **Name** and
**Type** (any Variant type: `bool`, `int`, `float`, `String`, `Color`, `Vector2i`,
`Array`, …). In code:

```gdscript
ts.add_custom_data_layer()
ts.set_custom_data_layer_name(0, "footstep_sound")
ts.set_custom_data_layer_type(0, TYPE_STRING)

ts.add_custom_data_layer()
ts.set_custom_data_layer_name(1, "move_cost")
ts.set_custom_data_layer_type(1, TYPE_INT)

ts.add_custom_data_layer()
ts.set_custom_data_layer_name(2, "decoration_surface")   # can a plant pot sit here?
ts.set_custom_data_layer_type(2, TYPE_BOOL)

print(ts.get_custom_data_layer_by_name("move_cost"))     # -> 1 (layer index)
```

### Filling values per tile

TileSet panel → **Select** → tile → *Custom Data* section: each declared layer appears as an
editable field. The **Paint** property mode works here too — pick the property
"Custom Data → footstep_sound", set the value `"wood"`, and click across every wooden tile.

Alternative tiles can override custom data (the "armed trap" variant carrying
`damage = 25` while the base tile has `0`), which composes nicely with the variant ladder
from [section 4](#alternative-tiles-flips-transposes-and-variants).

### Reading it from gameplay code

The canonical read path is three hops: **position → cell → TileData → value**.

```gdscript
# Footstep audio chosen by the ground under the player's feet:
@onready var _ground: TileMapLayer = %Ground

func _get_footstep_sound() -> StringName:
	var cell: Vector2i = _ground.local_to_map(_ground.to_local(global_position))
	var td: TileData = _ground.get_cell_tile_data(cell)
	if td == null:
		return &"default"
	var sound: String = td.get_custom_data("footstep_sound")
	return StringName(sound) if sound != "" else &"default"
```

```gdscript
# Movement cost for a grid tactics/companion pathfinder (feeds AStarGrid2D):
func build_cost_grid(layer: TileMapLayer) -> Dictionary:
	var costs: Dictionary = {}          # Vector2i -> int
	for cell in layer.get_used_cells():
		var td := layer.get_cell_tile_data(cell)
		costs[cell] = td.get_custom_data("move_cost") if td else 1
	return costs
```

Two API notes, verified against the class reference:

- `get_custom_data(layer_name: String)` looks up by *name*;
  `get_custom_data_by_layer_id(layer_id: int)` by index — the by-id form skips a string
  lookup and suits per-frame hot paths.
- Reading a custom data layer that exists returns the field's default (zero value) for tiles
  that never set it — you do not need null-checks per field, only for the `TileData` itself
  (empty cell → `null`).

> ⚠️ **Pitfall** — `get_custom_data()` with a *misspelled name* fails at runtime, not at
> parse time. Centralize layer names as constants
> (`const DATA_FOOTSTEP := "footstep_sound"`) next to the code that owns the TileSet, exactly
> as you would for input action names.

> ✅ **Best practice** — Custom data describes **the tile kind**, not **the cell instance**.
> All cells sharing a tile share the value. Per-cell state (this specific crop's growth
> stage, this door's open/closed) belongs in your own `Dictionary[Vector2i, …]` keyed by
> cell — or in a scene tile if the state is complex. Trying to bend custom data into
> per-cell storage is the most common misuse of the feature.

---

## Terrains: autotiling in depth

Hand-picking edge and corner tiles is the most tedious job in tile art usage: a path through
grass needs straight edges, outer corners, inner corners, end caps… **Terrains** automate the
choice. You declare which tiles belong to which terrain and how their borders behave; the
editor (and the runtime API) then *solves* for the correct tile at each cell while you paint
broad strokes.

Godot 4's terrains replace Godot 3's "autotile bitmask" system — same goal, more general
machinery, different vocabulary.

### The three-level hierarchy

```
TileSet
└── Terrain Set 0                      mode: Match Corners and Sides
    ├── Terrain 0: "Grass"    (color: green — editor overlay only)
    ├── Terrain 1: "Dirt"     (color: brown)
    └── Terrain 2: "Water"    (color: blue)
└── Terrain Set 1                      mode: Match Sides
    └── Terrain 0: "Pipes"
```

- A **terrain set** groups terrains that can *transition into each other* and fixes one
  **match mode** for all of them. Tiles belong to at most one terrain set.
- A **terrain** is one material within the set ("Grass"). A tile is assigned to a terrain
  (its center) and declares, via peering bits, which neighbors it tolerates.
- Terrains in *different* sets know nothing about each other — grass cannot auto-transition
  into pipes.

### Match modes

| Mode | Enum constant | What must agree between neighbors | Full transition tile count (1 terrain vs empty) |
|---|---|---|---|
| Match Corners and Sides | `TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES` | All 8 neighbor relationships (4 sides + 4 corners) | 47 (the classic "blob") |
| Match Corners | `TileSet.TERRAIN_MODE_MATCH_CORNERS` | Only diagonal corners | 16 |
| Match Sides | `TileSet.TERRAIN_MODE_MATCH_SIDES` | Only orthogonal sides | 16 |

Rules of thumb: **Corners and Sides** for organic ground (grass/dirt/sand blobs, the standard
47-tile template every asset pack ships); **Sides** for path/pipe/wall networks where only
orthogonal continuation matters; **Corners** for chunky cliff or fence styles where diagonal
adjacency is the visual driver.

### Peering bits, carefully

The peering bits are the heart of the system and the part most tutorials wave through, so we
go slowly. Every tile in a terrain set exposes a small diagram of clickable zones — the
**terrain peering bits** — one per neighbor relationship that the match mode cares about. For
a square tile in Corners-and-Sides mode:

```
        top-left  top   top-right
             ┌────┬────┬────┐
             │ TL │ T  │ TR │
             ├────┼────┼────┤
       left  │ L  │ C  │ R  │  right          C  = the tile's own terrain
             ├────┼────┼────┤                 T,R,B,L      = side bits
             │ BL │ B  │ BR │                 TL,TR,BL,BR  = corner bits
             └────┴────┴────┘
      bottom-left bottom bottom-right
```

Each bit stores a terrain index (or `-1` = "empty / no terrain"). Read a painted bit as a
promise: **"in a finished map, the neighbor across this bit will be showing this terrain."**

Concretely, for a "Grass" blob against empty background:

```
  Full grass center tile:            Top edge tile:               Top-left outer corner:
  ┌────┬────┬────┐                   ┌────┬────┬────┐             ┌────┬────┬────┐
  │ G  │ G  │ G  │                   │ -1 │ -1 │ -1 │             │ -1 │ -1 │ -1 │
  ├────┼────┼────┤                   ├────┼────┼────┤             ├────┼────┼────┤
  │ G  │ G  │ G  │                   │ G  │ G  │ G  │             │ -1 │ G  │ G  │
  ├────┼────┼────┤                   ├────┼────┼────┤             ├────┼────┼────┤
  │ G  │ G  │ G  │                   │ G  │ G  │ G  │             │ -1 │ G  │ G  │
  └────┴────┴────┘                   └────┴────┴────┘             └────┴────┴────┘
  (surrounded by grass               (grass below and beside,     (grass only to the
   on all 8 relationships)            emptiness above)             bottom-right quadrant)
```

When you paint terrain "Grass" over a region, the solver examines each affected cell's
neighborhood and picks — from all tiles assigned to the set — the tile whose bits best match
the surrounding terrain values. If no tile matches perfectly, it takes the closest match
(and visibly "wrong" transitions are your cue that a bit combination has no authored tile).

For isometric tilesets the diagram rotates 45° (bits sit on the diamond's edges and points);
hex tiles show six side bits. The concept is identical.

> ⚠️ **Pitfall** — The solver can only choose tiles that *exist*. The eternal beginner trap
> is authoring the 16 obvious edge tiles and wondering why inner corners glitch: Corners-and-
> Sides mode needs all 47 neighborhood classes covered (or at least the ones your maps
> produce). If a transition draws wrong, list which neighborhood class the cell is in and
> check whether any tile's bits encode it.

> ⚠️ **Pitfall** — Two tiles with *identical* bits are fine (the solver picks randomly,
> weighted by `probability` — free variation!). Two tiles with *accidentally different* bits
> that you believed identical produce flickering choices between paints. The editor's
> terrain-bit overlay (Select tab, Terrains property) is the audit tool.

### A worked solve: three cells of grass on empty ground

To make the machinery concrete, trace what happens when you paint a 3×1 horizontal stroke
of "Grass" (terrain 0, Corners-and-Sides) onto an empty map. The solver must choose a tile
for each of the three cells — call them A, B, C — knowing the final neighborhood each will
sit in:

```
   map after the stroke:          neighborhood of A:        neighborhood of B:
                                  (left end of stroke)      (middle of stroke)
   . . . . . .                    ┌────┬────┬────┐          ┌────┬────┬────┐
   . A B C . .                    │ -1 │ -1 │ -1 │          │ -1 │ -1 │ -1 │
   . . . . . .                    ├────┼────┼────┤          ├────┼────┼────┤
                                  │ -1 │ A  │ G  │          │ G  │ B  │ G  │
   . = empty (-1)                 ├────┼────┼────┤          ├────┼────┼────┤
   G = grass                      │ -1 │ -1 │ -1 │          │ -1 │ -1 │ -1 │
                                  └────┴────┴────┘          └────┴────┴────┘
```

- Cell **A** needs a tile whose bits say: *right side = Grass, everything else = empty* —
  the "left end cap" tile of your template. If the template has no end caps (a common
  authoring gap!), the solver falls back to the closest match, typically a left-edge tile,
  and the stroke's end looks subtly wrong.
- Cell **B** needs *left = Grass, right = Grass, all else empty* — the "horizontal middle"
  tile.
- Cell **C** mirrors A with the right end cap.

Now paint one more grass cell directly **below B**. The solver re-evaluates not just the
new cell but **every neighbor whose promised neighborhood changed**: B must swap from
"horizontal middle" to a "T-junction downward" class (bottom side now Grass), and A and C
may need corner-bit variants if the template distinguishes them. This cascade is why
terrain edits feel "smart" — and why they cost more than raw `set_cell()`: each affected
cell is a small constraint-solving problem over the whole tile template.

The exercise that cements this (Lab 3's stretch goal): delete one template tile, repeat the
strokes above, and predict *before looking* which placements go wrong.

### Painting terrains

The **Terrains** tab of the TileMap panel lists terrain sets and their terrains. Two modes:

- **Connect mode** — painted cells connect with *all* surrounding cells of the same terrain.
  The default; right for blobs and areas.
- **Path mode** — painted cells connect only with the *previous and next cells of the current
  stroke*. Right for roads and rivers you want to stay one cell wide instead of fusing into
  neighboring same-terrain regions.

Erasing with the terrain brush (right-click) sets cells to empty **and re-solves the
neighbors**, healing borders — the whole point over manual erasing.

### Scripting terrains

The same solver is scriptable, which procedural generation leans on heavily:

```gdscript
# Paint a connected grass area from code:
var cells: Array[Vector2i] = []
for x in range(4, 12):
	for y in range(3, 9):
		cells.append(Vector2i(x, y))

layer.set_cells_terrain_connect(cells, 0, 0)     # terrain set 0, terrain 0 ("Grass")

# Carve a dirt path that keeps to its stroke:
var path: Array[Vector2i] = [Vector2i(4, 6), Vector2i(5, 6), Vector2i(6, 6), Vector2i(6, 7)]
layer.set_cells_terrain_path(path, 0, 1)         # terrain 1 ("Dirt")
```

Both take an optional `ignore_empty_terrains: bool = true` — with it, empty-terrain cells in
the neighborhood are not forced to update, which is almost always what you want.

> ✅ **Best practice** — Terrain calls are *solver* operations: substantially slower than raw
> `set_cell()` because each affected cell re-evaluates its neighborhood. In generators, lay
> bulk cells with `set_cell()` and reserve `set_cells_terrain_connect()` for the borders —
> or run terrain solving once at the end over the whole region, not per placed cell.

### Terrains vs Godot 3 autotile — expectations to reset

Veterans of 3.x autotiles should note: terrains are a *placement-time* solver, not a
*live constraint*. Editing one cell with the plain tile brush will not re-solve its
neighbors; only terrain-brush (or terrain API) edits do. Also, a tile can hold bits for one
terrain set only — multi-set tiles are not a thing. Both limits are deliberate: the data
stays plain cells, with no hidden reactive machinery in the map.

---

## Scripting tilemaps: the cell API and coordinates

Everything the editor does, scripts can do. The `TileMapLayer` cell API is small and
orthogonal; mastering it is a prerequisite for procedural generation, save systems, tile
gameplay (farming, digging, building) and the case-study analysis later.

### Writing cells

```gdscript
# set_cell(coords, source_id := -1, atlas_coords := Vector2i(-1, -1), alternative_tile := 0)
layer.set_cell(Vector2i(5, 3), 0, Vector2i(0, 0))        # place: source 0, atlas tile (0,0)
layer.set_cell(Vector2i(6, 3), 0, Vector2i(1, 0), 2)     # …with authored alternative 2

layer.erase_cell(Vector2i(5, 3))                          # remove one cell
layer.set_cell(Vector2i(6, 3))                            # defaults erase too (source -1)

layer.clear()                                             # remove every cell on the layer
```

`erase_cell(coords)` and `set_cell(coords)` with defaults are equivalent; prefer
`erase_cell` for intent-revealing code.

### Reading cells

```gdscript
var coords := Vector2i(5, 3)

layer.get_cell_source_id(coords)         # int   — -1 means "empty cell"
layer.get_cell_atlas_coords(coords)      # Vector2i — (-1, -1) when empty
layer.get_cell_alternative_tile(coords)  # int   — includes transform flag bits
layer.get_cell_tile_data(coords)         # TileData or null — the rich record
```

The idiomatic emptiness check is `get_cell_source_id(coords) == -1`. For anything beyond
identity — custom data, collision, terrain — go through `get_cell_tile_data()` and null-check.

### Querying the map

```gdscript
var all_cells: Array[Vector2i] = layer.get_used_cells()

# Only cells painted with a specific tile (all filters optional):
var grass_cells := layer.get_used_cells_by_id(0, Vector2i(0, 0))

# The tight bounding rectangle of everything painted:
var bounds: Rect2i = layer.get_used_rect()
print("map spans %s cells starting at %s" % [bounds.size, bounds.position])
```

`get_used_rect()` is the standard way to size minimaps, clamp cameras
(`bounds` × `tile_size` gives pixel bounds), and iterate "the whole map" without guessing
coordinates — used cells can be negative, since the grid extends in all four directions from
origin.

```gdscript
# Camera limits from the map, the classic recipe:
func apply_camera_limits(cam: Camera2D, layer: TileMapLayer) -> void:
	var r := layer.get_used_rect()
	var ts := layer.tile_set.tile_size
	cam.limit_left = r.position.x * ts.x
	cam.limit_top = r.position.y * ts.y
	cam.limit_right = r.end.x * ts.x
	cam.limit_bottom = r.end.y * ts.y
```

### The three coordinate spaces

Tilemap code juggles three spaces, and mixing them up is the number-one source of
off-by-one-cell bugs:

| Space | Type | Meaning |
|---|---|---|
| **Map** | `Vector2i` | Cell indices on the grid — what `set_cell` and friends speak |
| **Local** | `Vector2` | Pixels in the `TileMapLayer`'s own coordinate system |
| **Global** | `Vector2` | Pixels in world space — what other nodes' `global_position` speaks |

Conversions:

```gdscript
# map -> local: center of the cell, in the layer's local pixels
var local_pos: Vector2 = layer.map_to_local(Vector2i(5, 3))

# local -> map: which cell contains this local point
var cell: Vector2i = layer.local_to_map(local_pos)

# The layer may be transformed! Bridge global <-> local with Node2D helpers:
var cell_under_mouse: Vector2i = layer.local_to_map(layer.to_local(get_global_mouse_position()))
var cell_center_global: Vector2 = layer.to_global(layer.map_to_local(cell_under_mouse))
```

> ⚠️ **Pitfall** — `map_to_local()` returns the cell's **center**, not its top-left corner.
> Positioning a spawned scene at `map_to_local(cell)` centers it in the cell; if the scene's
> sprite is anchored top-left you will be half a tile off. Also: never feed a *global*
> position to `local_to_map()` while the layer (or an ancestor) is offset or scaled —
> always route through `to_local()` first. Both mistakes produce that maddening
> "everything is shifted" screenshot.

> ⚠️ **Pitfall** — For isometric maps, map coordinates do **not** align with screen axes:
> `+x` walks down-right along the diamond. Code that assumes `cell + Vector2i(1, 0)` means
> "one tile to the screen right" is wrong on iso maps. Reason in map space, convert for
> display, and use `get_neighbor_cell()` when you mean a *logical* neighbor.

### Neighbors, properly

Because "the cell above" differs per tile shape (square vs iso vs hex), the API abstracts it
with the `TileSet.CellNeighbor` enum:

```gdscript
var right := layer.get_neighbor_cell(cell, TileSet.CELL_NEIGHBOR_RIGHT_SIDE)
var below := layer.get_neighbor_cell(cell, TileSet.CELL_NEIGHBOR_BOTTOM_SIDE)
var diag  := layer.get_neighbor_cell(cell, TileSet.CELL_NEIGHBOR_BOTTOM_RIGHT_CORNER)

# All valid direct neighbors for the current tile shape:
var around: Array[Vector2i] = layer.get_surrounding_cells(cell)
```

On a square grid `get_surrounding_cells()` returns the 4 side-adjacent cells; on hex grids,
6. Flood fills, cellular automata and tile-graph algorithms written against these helpers
survive a change of tile shape untouched — hardcoded `Vector2i(0, -1)` arithmetic does not.

### Worked micro-example: click-to-toggle tiles

The "hello world" of tile interactivity — a dig/build toggle under the mouse:

```gdscript
extends TileMapLayer

const SOURCE_ID := 0
const DIRT := Vector2i(1, 0)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		var cell := local_to_map(to_local(get_global_mouse_position()))
		match event.button_index:
			MOUSE_BUTTON_LEFT:
				set_cell(cell, SOURCE_ID, DIRT)      # build
			MOUSE_BUTTON_RIGHT:
				erase_cell(cell)                     # dig
```

Ten lines, and collision/navigation/occlusion for the placed tile all come along for free —
the payoff of the declarative TileSet model, and the essence of every tile-building game.

### Ghost previews: build-mode UX with a second layer

Every building game shows a translucent "ghost" of the tile you are about to place. The
cleanest implementation is a dedicated **preview layer**: same TileSet, no collision,
half-transparent, holding at most one cell — moved on hover, committed on click:

```gdscript
extends Node2D

const SOURCE_ID := 0
var selected_tile := Vector2i(1, 0)          # what the player is placing

@onready var _world: TileMapLayer = $World
@onready var _preview: TileMapLayer = $Preview

var _hover_cell := Vector2i(-9999, -9999)

func _ready() -> void:
	_preview.tile_set = _world.tile_set
	_preview.collision_enabled = false        # ghosts must not collide
	_preview.navigation_enabled = false
	_preview.modulate = Color(1, 1, 1, 0.5)   # the "ghost" look, one property

func _process(_delta: float) -> void:
	var cell := _world.local_to_map(_world.to_local(get_global_mouse_position()))
	if cell == _hover_cell:
		return
	_preview.erase_cell(_hover_cell)
	_hover_cell = cell
	var valid := _world.get_cell_source_id(cell) == -1     # only over empty cells
	_preview.modulate = Color(1, 1, 1, 0.5) if valid else Color(1, 0.3, 0.3, 0.5)
	_preview.set_cell(cell, SOURCE_ID, selected_tile)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"place") and _world.get_cell_source_id(_hover_cell) == -1:
		_world.set_cell(_hover_cell, SOURCE_ID, selected_tile)
```

The idioms to steal: validity feedback via the preview layer's `modulate` (white ghost =
allowed, red ghost = blocked), a sentinel hover cell to avoid redundant repaints, and the
world/preview layer pair sharing one TileSet so the ghost is always pixel-faithful to what
will be placed.

### API quick reference

The working set of `TileMapLayer` calls, grouped the way you reach for them:

| Task | Call |
|---|---|
| Place / replace a cell | `set_cell(coords, source_id, atlas_coords, alternative)` |
| Remove a cell | `erase_cell(coords)` · everything: `clear()` |
| Is the cell empty? | `get_cell_source_id(coords) == -1` |
| Which tile is here? | `get_cell_atlas_coords(coords)` + `get_cell_alternative_tile(coords)` |
| Tile properties / metadata | `get_cell_tile_data(coords)` → `TileData` (null if empty) |
| Orientation of a painted cell | `is_cell_flipped_h/v(coords)`, `is_cell_transposed(coords)` |
| All painted cells | `get_used_cells()` · filtered: `get_used_cells_by_id(src, atlas, alt)` |
| Map bounds | `get_used_rect()` → `Rect2i` |
| Pixels → cell | `local_to_map(to_local(global_pos))` |
| Cell → pixels (center) | `to_global(map_to_local(coords))` |
| Shape-aware neighbors | `get_neighbor_cell(coords, TileSet.CELL_NEIGHBOR_*)`, `get_surrounding_cells(coords)` |
| Autotile from code | `set_cells_terrain_connect(cells, set, terrain)`, `set_cells_terrain_path(...)` |
| Stamp / lift arrangements | `set_pattern(pos, pattern)`, `get_pattern(cells)`, `map_pattern(...)` |
| Collision RID → cell | `get_coords_for_body_rid(rid)` guarded by `has_body_rid(rid)` |
| Scrub orphaned cells | `fix_invalid_tiles()` |
| Force internals mid-frame | `update_internals()` (sparingly!) |
| Per-cell visual overrides | `_use_tile_data_runtime_update()` + `_tile_data_runtime_update()` + `notify_runtime_tile_data_update()` |
| React to any change | `changed` signal |

---

## Procedural generation: a room generator

Procedural generation is where the cell API earns its keep. We build a compact but complete
**room-and-corridor generator** — the same species of algorithm behind countless roguelikes —
sized so you can type it in and extend it in the exercises. It also demonstrates the correct
layering of raw `set_cell` (bulk) and terrain solving (borders), plus custom data reads for
gameplay.

### The plan

1. Scatter N non-overlapping rectangular rooms inside the map bounds.
2. Connect consecutive room centers with L-shaped corridors.
3. Stamp floors on a `Ground` layer; walls wherever floor meets emptiness, on a `Walls`
   layer (which carries collision in its tiles).
4. Optionally, let terrains dress the floor edges.

```gdscript
class_name RoomGenerator
extends Node2D

@export var map_size := Vector2i(48, 32)
@export var room_count := 8
@export var room_min := Vector2i(5, 4)
@export var room_max := Vector2i(11, 8)
@export var rng_seed := 0

const SRC := 0                          # atlas source ID in both layers' TileSet
const FLOOR := Vector2i(0, 0)           # atlas coords
const WALL := Vector2i(1, 0)

@onready var _ground: TileMapLayer = $Ground
@onready var _walls: TileMapLayer = $Walls

var _rng := RandomNumberGenerator.new()
var _floor_cells: Dictionary = {}       # Vector2i -> true (a set)

func _ready() -> void:
	_rng.seed = rng_seed if rng_seed != 0 else randi()
	generate()

func generate() -> void:
	_ground.clear()
	_walls.clear()
	_floor_cells.clear()

	var rooms: Array[Rect2i] = _place_rooms()
	for i in rooms.size() - 1:
		_carve_corridor(rooms[i].get_center(), rooms[i + 1].get_center())
	_stamp_floors()
	_stamp_walls()

func _place_rooms() -> Array[Rect2i]:
	var rooms: Array[Rect2i] = []
	var attempts := 0
	while rooms.size() < room_count and attempts < room_count * 20:
		attempts += 1
		var size := Vector2i(
			_rng.randi_range(room_min.x, room_max.x),
			_rng.randi_range(room_min.y, room_max.y))
		var pos := Vector2i(
			_rng.randi_range(1, map_size.x - size.x - 1),
			_rng.randi_range(1, map_size.y - size.y - 1))
		var candidate := Rect2i(pos, size)
		var padded := candidate.grow(1)             # keep 1 cell between rooms
		if rooms.any(func(r: Rect2i) -> bool: return padded.intersects(r)):
			continue
		rooms.append(candidate)
		for x in range(candidate.position.x, candidate.end.x):
			for y in range(candidate.position.y, candidate.end.y):
				_floor_cells[Vector2i(x, y)] = true
	return rooms

func _carve_corridor(from: Vector2i, to: Vector2i) -> void:
	var corner := Vector2i(to.x, from.y)            # L-shape: horizontal, then vertical
	for x in range(mini(from.x, corner.x), maxi(from.x, corner.x) + 1):
		_floor_cells[Vector2i(x, from.y)] = true
	for y in range(mini(corner.y, to.y), maxi(corner.y, to.y) + 1):
		_floor_cells[Vector2i(to.x, y)] = true

func _stamp_floors() -> void:
	for cell: Vector2i in _floor_cells:
		_ground.set_cell(cell, SRC, FLOOR)

func _stamp_walls() -> void:
	# A wall belongs on every empty cell that touches a floor cell (8-neighborhood):
	var wall_cells: Dictionary = {}
	for cell: Vector2i in _floor_cells:
		for dx in [-1, 0, 1]:
			for dy in [-1, 0, 1]:
				var n: Vector2i = cell + Vector2i(dx, dy)
				if not _floor_cells.has(n):
					wall_cells[n] = true
	for cell: Vector2i in wall_cells:
		_walls.set_cell(cell, SRC, WALL)
```

Study points, beyond the algorithm itself:

- **A `Dictionary` used as a set** buffers the whole plan before any cell is painted.
  Generating into data first, painting second, keeps painting a dumb, fast loop — and makes
  the generator testable without a scene (`_floor_cells` can be asserted in a unit test).
- **Two layers, two responsibilities.** `Ground` has no collision; `Walls` tiles carry
  polygons in the TileSet. The generator never touches physics explicitly.
- **Determinism.** Seeding `RandomNumberGenerator` makes bugs reproducible and lets a saved
  game re-generate identical maps from one integer — pair this with
  [Database and Persistence](DATABASE_AND_PERSISTENCE.md).
- `Rect2i.get_center()`, `grow()`, `intersects()` do all the geometry; hand-rolled
  overlap math is where generator bugs breed.

### Dressing with terrains

If the TileSet defines a terrain set (say set 0, terrain 0 = "Dungeon floor"), replace
`_stamp_floors()` with a terrain solve to get authored edge transitions for free:

```gdscript
func _stamp_floors_with_terrain() -> void:
	var cells: Array[Vector2i] = []
	for cell: Vector2i in _floor_cells:
		cells.append(cell)
	_ground.set_cells_terrain_connect(cells, 0, 0)   # one solver pass over the whole set
```

One solver pass over N cells is dramatically cheaper than N single-cell terrain calls —
the batching advice from [section 13](#terrains-autotiling-in-depth) in practice.

### Spawning content from the generated map

Close the loop with custom data: mark some floor tiles as valid spawn surfaces in the
TileSet (`spawnable: bool`), then:

```gdscript
func pick_spawn_cells(count: int) -> Array[Vector2i]:
	var candidates: Array[Vector2i] = []
	for cell in _ground.get_used_cells():
		var td := _ground.get_cell_tile_data(cell)
		if td and td.get_custom_data("spawnable"):
			candidates.append(cell)
	candidates.shuffle()
	return candidates.slice(0, count)
```

### A second recipe: cellular-automata caves

Rooms-and-corridors produces architecture; **cellular automata** produce *nature* — caves,
lakes, organic clearings. The algorithm is beautifully dumb: start with noise, then apply a
smoothing rule a few times ("a cell becomes wall if enough neighbors are walls"), and
structure emerges. It slots into the same two-layer stamping scaffold as `RoomGenerator`:

```gdscript
class_name CaveGenerator
extends Node2D

@export var map_size := Vector2i(64, 40)
@export var initial_wall_chance := 0.44     # noise density — the character of the caves
@export var smoothing_passes := 5
@export var wall_threshold := 5             # >= this many wall neighbors -> become wall
@export var rng_seed := 0

const SRC := 0
const FLOOR := Vector2i(0, 0)
const WALL := Vector2i(1, 0)

@onready var _ground: TileMapLayer = $Ground
@onready var _walls: TileMapLayer = $Walls

var _rng := RandomNumberGenerator.new()
var _is_wall: Dictionary = {}               # Vector2i -> bool, the working grid

func _ready() -> void:
	_rng.seed = rng_seed if rng_seed != 0 else randi()
	generate()

func generate() -> void:
	_seed_noise()
	for i in smoothing_passes:
		_smooth()
	_stamp()

func _seed_noise() -> void:
	_is_wall.clear()
	for x in map_size.x:
		for y in map_size.y:
			var edge := x == 0 or y == 0 or x == map_size.x - 1 or y == map_size.y - 1
			_is_wall[Vector2i(x, y)] = edge or _rng.randf() < initial_wall_chance

func _smooth() -> void:
	var next: Dictionary = {}
	for cell: Vector2i in _is_wall:
		var walls := 0
		for dx in [-1, 0, 1]:
			for dy in [-1, 0, 1]:
				if dx == 0 and dy == 0:
					continue
				var n: Vector2i = cell + Vector2i(dx, dy)
				# Out-of-bounds counts as wall: caves seal at the border.
				walls += 1 if _is_wall.get(n, true) else 0
		next[cell] = walls >= wall_threshold
	_is_wall = next

func _stamp() -> void:
	_ground.clear()
	_walls.clear()
	for cell: Vector2i in _is_wall:
		if _is_wall[cell]:
			_walls.set_cell(cell, SRC, WALL)
		else:
			_ground.set_cell(cell, SRC, FLOOR)
```

Tuning notes, because this algorithm is all feel:

- **`initial_wall_chance`** is the master dial: 0.40 gives open caverns, 0.48 gives narrow
  tunnels, 0.55+ mostly seals the map.
- **The double-buffer matters.** `_smooth()` writes into `next` and swaps; mutating
  `_is_wall` in place while reading it lets early cells influence later ones in the same
  pass and produces directional artifacts (a subtle, classic bug).
- **Out-of-bounds counts as wall** so caves never bleed off the map edge — encode the rule
  in `get(n, true)` rather than special-casing borders.
- **Disconnected pockets are expected.** Production generators follow up with a flood fill
  (`get_surrounding_cells()` makes it four lines) to find regions, then either discard all
  but the largest or tunnel between them — Lab 7's stretch goal in spirit.
- Dress the result with a terrain pass exactly as `_stamp_floors_with_terrain()` did:
  cave-wall terrain against floor terrain makes the automata's blobby borders look
  hand-drawn.

> ✅ **Best practice** — Keep generators **idempotent**: `generate()` starts with `clear()`
> and rebuilds from `_rng.seed`. A generator you can re-run safely at any moment is a
> generator you can hook to a "reroll" button, a test suite and a save file with equal ease.

---

## Runtime changes, internals and performance

You now mutate maps at runtime — so it is time to look under the hood. This section explains,
at working-knowledge altitude, what a `set_cell()` actually costs, how the renderer and
physics server organize tile data, and which strategies keep huge or highly dynamic maps
fast. It extends the general performance doctrine of
[Desktop Companion Performance](DESKTOP_COMPANION_PERFORMANCE.md) with tilemap specifics.

### Rendering quadrants: how tiles become draw calls

A `TileMapLayer` does not draw cells one by one. Cells are grouped into **rendering
quadrants** — square blocks of `rendering_quadrant_size × rendering_quadrant_size` cells
(default 16×16 = 256 cells) — and each quadrant's tiles that share a texture and material are
merged into batched geometry on a small number of canvas items. A 200×200 map is therefore
on the order of ~169 quadrants, not 40,000 sprites; with one shared atlas texture, the whole
layer can render in a handful of draw calls.

Two forces pull `rendering_quadrant_size` in opposite directions:

- **Bigger quadrants** → fewer canvas items → fewer draw calls for *static* maps.
- **Smaller quadrants** → cheaper updates, because changing any cell **rebuilds its whole
  quadrant's** geometry, and finer culling granularity (off-screen quadrants skip drawing).

The default 16 is a sane middle. Tune only with the profiler open: a mostly-static
overworld can go to 32+; a sand-digging game with constant edits may prefer 8.

### What `set_cell` really costs

`set_cell()` itself is cheap — it updates the cell database and *marks the affected quadrant
dirty*. The real work (rebuilding quadrant geometry, physics polygons, navigation regions)
is **deferred and batched**: Godot processes dirty quadrants once, at the end of the frame.
Consequences:

- A loop placing 5,000 cells in one frame triggers each quadrant's rebuild **once**, not
  5,000 times. Bulk generation is therefore far cheaper than its call count suggests.
- Reads *within the same frame* (`get_cell_*`) see the new data immediately — the database
  is updated synchronously; only the derived artifacts lag until frame end.
- If something downstream needs the *internals* current mid-frame (e.g., you query the
  physics server directly right after painting), force the flush:

```gdscript
layer.update_internals()   # immediate, synchronous rebuild of dirty internals — use sparingly
```

> ⚠️ **Pitfall** — Calling `update_internals()` inside a placement loop turns the deferred
> batch into per-call rebuilds and can multiply generation time by orders of magnitude. It
> exists for the rare mid-frame dependency, not as a "make sure" incantation.

### Physics quadrants

Since 4.4 the same idea applies to collision: `physics_quadrant_size` (default 16) merges
tile collision polygons into shared static bodies per quadrant. Fewer bodies = a lighter
broadphase for the physics server on large maps. The trade mirrors rendering: an edit
rebuilds its physics quadrant, so heavy-edit games may prefer smaller physics quadrants.

### The cost of Y-sort

Y-sorted layers cannot batch by quadrant alone: draw order must interleave *per cell* with
external nodes (actors), so the renderer effectively sorts and emits much finer-grained
items for that layer. The practical doctrine, restated from
[section 7](#layer-stacking-patterns-ground-props-overlay): **Y-sort only the props layer**.
A Y-sorted 200×200 ground layer is pure waste — ground never overlaps actors ambiguously.
`x_draw_order_reversed` exists for isometric edge cases where same-row tiles must draw
right-to-left; it changes order, not cost.

### Per-cell runtime customization without data explosion

Sometimes you want *this one cell* drawn differently — flash a tile red, dim unexplored
cells — without authoring alternatives for every state. `TileMapLayer` exposes a dedicated
virtual-method pipeline for exactly this:

```gdscript
extends TileMapLayer

var highlighted: Dictionary = {}       # Vector2i -> true

func _use_tile_data_runtime_update(coords: Vector2i) -> bool:
	return highlighted.has(coords)     # opt-in per cell — keep this cheap and honest

func _tile_data_runtime_update(coords: Vector2i, tile_data: TileData) -> void:
	tile_data.modulate = Color(1.0, 0.4, 0.4)   # modifies a per-cell COPY, not the TileSet

func set_highlight(coords: Vector2i, on: bool) -> void:
	if on:
		highlighted[coords] = true
	else:
		highlighted.erase(coords)
	notify_runtime_tile_data_update()  # tell the layer to re-ask _use_... for affected cells
```

The engine calls `_use_tile_data_runtime_update()` to ask *which* cells need custom data,
and `_tile_data_runtime_update()` to let you mutate a **copy** of the `TileData` for those
cells only — the shared TileSet is untouched. When your conditions change, call
`notify_runtime_tile_data_update()` to schedule re-evaluation. This is the sanctioned way to
do fog-of-war tinting, damage flashes and selection highlights on tiles.

> ✅ **Best practice** — Return `true` from `_use_tile_data_runtime_update()` for as few
> cells as possible: every opted-in cell leaves the fast shared path and costs per-frame
> bookkeeping. A `Dictionary` of exceptional cells (as above) is the right shape; `return
> true` unconditionally is the wrong one.

### Chunking strategies for huge maps

For genuinely large worlds (thousands × thousands of cells), a single layer — even
quadrant-batched — eventually strains memory and update latency. The production pattern is
**chunking**: the world is a grid of fixed-size chunks (say 64×64 cells), each chunk one
`TileMapLayer` (or a small stack), loaded around the camera and freed (or `enabled = false`)
beyond a radius:

```gdscript
# Sketch: chunk manager keyed by chunk coordinates
const CHUNK := 64
var live_chunks: Dictionary = {}       # Vector2i -> TileMapLayer

func _process(_delta: float) -> void:
	var center: Vector2i = Vector2i((get_viewport().get_camera_2d().global_position
			/ Vector2(tile_px * CHUNK)).floor())
	for dx in [-1, 0, 1]:
		for dy in [-1, 0, 1]:
			_ensure_chunk(center + Vector2i(dx, dy))
	for key: Vector2i in live_chunks.keys():
		if (key - center).length_squared() > 4:
			live_chunks[key].queue_free()          # or .enabled = false to keep data warm
			live_chunks.erase(key)
```

Design notes:

- Persist chunk contents *as data* (your own arrays / `tile_map_data` snapshots), not as
  live nodes; regenerate or restore on load.
- Align `CHUNK` with `rendering_quadrant_size` multiples so chunk boundaries do not split
  quadrants pathologically.
- For a desktop companion app — small stage, always visible — chunking is over-engineering;
  it earns its complexity at open-world scale. Know the pattern, deploy it when map size
  demands it.

### The serialized form: `tile_map_data`

The whole cell database round-trips through one property:
`tile_map_data: PackedByteArray`. This is what the scene file stores, and it doubles as a
free save-game format for player-modified maps:

```gdscript
# Save:
save_dict["garden_tiles"] = Marshalls.raw_to_base64(garden_layer.tile_map_data)

# Load:
garden_layer.tile_map_data = Marshalls.base64_to_raw(save_dict["garden_tiles"])
```

The format is engine-internal — treat it as an opaque blob (store it, don't parse it), and
prefer your own cell list if you need forward-compatible or human-readable saves (see
[Database and Persistence](DATABASE_AND_PERSISTENCE.md) for the trade-offs).

### Worked example: persisting a player-built map, two ways

Concretely, for a hypothetical Relax Room garden the player tiles herself. **Way one** — the
opaque blob, three lines, zero forward-compatibility guarantees across engine versions:

```gdscript
func save_garden() -> Dictionary:
	return { "tiles_blob": Marshalls.raw_to_base64($Garden.tile_map_data) }

func load_garden(data: Dictionary) -> void:
	$Garden.tile_map_data = Marshalls.base64_to_raw(data["tiles_blob"])
```

**Way two** — an explicit cell list: verbose, human-readable, diff-able, survives engine
upgrades and even a move away from tilemaps entirely (it is *your* schema):

```gdscript
func save_garden_cells(layer: TileMapLayer) -> Array:
	var cells := []
	for coords in layer.get_used_cells():
		cells.append({
			"x": coords.x,
			"y": coords.y,
			"src": layer.get_cell_source_id(coords),
			"ax": layer.get_cell_atlas_coords(coords).x,
			"ay": layer.get_cell_atlas_coords(coords).y,
			"alt": layer.get_cell_alternative_tile(coords),
		})
	return cells

func load_garden_cells(layer: TileMapLayer, cells: Array) -> void:
	layer.clear()
	for c: Dictionary in cells:
		layer.set_cell(Vector2i(c.x, c.y), c.src, Vector2i(c.ax, c.ay), c.alt)
```

The decision rule: blob for *ephemeral or engine-pinned* state (autosaves, undo snapshots
within a session), explicit cells for *the player's canonical creation* — anything you would
be embarrassed to lose in an engine upgrade. Relax Room's own JSON-first persistence
philosophy ([Database and Persistence](DATABASE_AND_PERSISTENCE.md)) lands firmly on way
two, and note the pleasant symmetry: the explicit format is exactly the cell triple from
[section 1](#overview-the-godot-4-tile-stack) — proof that you understand the data model is
that you can serialize it yourself.

An undo stack for a build mode falls out of the blob form almost for free, because
`tile_map_data` is a value snapshot:

```gdscript
var _undo_stack: Array[PackedByteArray] = []

func before_edit(layer: TileMapLayer) -> void:
	_undo_stack.append(layer.tile_map_data)      # snapshot is a copy
	if _undo_stack.size() > 32:
		_undo_stack.pop_front()

func undo(layer: TileMapLayer) -> void:
	if not _undo_stack.is_empty():
		layer.tile_map_data = _undo_stack.pop_back()
```

Snapshots of a small map are a few kilobytes; for huge maps, snapshot per-chunk layers
instead of the world — the chunking structure above pays off twice.

### A measurement mindset

Numbers beat folklore. The relevant instruments, all covered in
[Desktop Companion Performance](DESKTOP_COMPANION_PERFORMANCE.md):

- **Profiler → Rendering**: draw call count before/after layer or quadrant changes.
- **Monitors**: `Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME`, physics island counts.
- The 200×200 test: paint a full map, toggle `y_sort_enabled` on the ground layer, watch
  draw calls and frame time — the cost of careless Y-sort stops being abstract immediately.

And a repeatable protocol, so tilemap performance discussions in your team happen over a
filled-in table instead of adjectives:

1. Build a benchmark scene: one script that paints an N×N map (parameterize N), a camera
   sweep, and a `Label` printing the monitors below each frame.
2. Record, per configuration, after 5 seconds of steady state:

| Configuration | Draw calls | Frame time (ms) | Notes |
|---|---|---|---|
| 200×200, 1 layer, no Y-sort | | | baseline |
| + `y_sort_enabled` on ground | | | expect draw calls to jump |
| split into ground + props, Y-sort props only | | | the recommended stack |
| `rendering_quadrant_size` 8 / 16 / 32 | | | static map: bigger wins |
| 1,000 `set_cell()` per frame | | | dirty-quadrant rebuild cost |
| same, `physics_quadrant_size` 4 | | | edit-heavy tuning |

```gdscript
# The two monitor reads that power the label:
var draw_calls := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
var frame_ms := Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
```

3. Change **one** variable per row, re-run, and keep the table in the repo next to the
   scene. Numbers from *your* tileset on *your* target hardware are the only ones that
   matter — this module supplies the levers and the expected directions, never substitute
   its prose for your measurements.

---

## Isometric tilemaps

Isometric presentation — the diamond-grid, three-quarter view of classic tycoons, tactics
games and cozy sims — is a first-class citizen of the tile stack: same nodes, same API, a
handful of configuration changes, and one hard problem (draw order) that Godot's Y-sort
machinery solves for you *if* you configure it deliberately. This section covers the tilemap
side; the projection math, camera work and genre patterns live in
[Isometric Games](ISOMETRIC_GAMES.md).

### Configuring the TileSet

```gdscript
tile_set.tile_shape = TileSet.TILE_SHAPE_ISOMETRIC
tile_set.tile_layout = TileSet.TILE_LAYOUT_DIAMOND_DOWN   # +Y walks straight down the screen
tile_set.tile_size = Vector2i(64, 32)                     # the on-screen diamond, 2:1 ratio
```

- **`tile_size` is the diamond**, not the artwork. The classic 2:1 ratio (64×32, 128×64,
  256×128) makes the diamond's edges move 2 pixels horizontally per 1 vertical — crisp for
  pixel art. Other ratios work but complicate art production.
- **`tile_layout`** decides how `Vector2i` map coordinates traverse the diamond plane.
  `DIAMOND_DOWN` and `DIAMOND_RIGHT` both run the axes along diamond edges; pick one at
  project start and never change it
  (the [section 2](#tileset-anatomy-shapes-layouts-and-tile-size) migration warning applies
  in full).

The grid then looks like this, with `DIAMOND_DOWN` coordinates:

```
                    ╱╲
                  ╱    ╲
                ╱ (0,0)  ╲
              ╱╲          ╱╲
            ╱    ╲      ╱    ╲
          ╱ (0,1)  ╲  ╱ (1,0)  ╲
        ╱╲          ╱╲          ╱╲
      ╱    ╲      ╱    ╲      ╱    ╲
    ╱ (0,2)  ╲  ╱ (1,1)  ╲  ╱ (2,0)  ╲
    ╲        ╱  ╲        ╱  ╲        ╱
      ╲    ╱      ╲    ╱      ╲    ╱
        ╲╱          ╲╱          ╲╱
         +Y down-left  +X down-right
```

### Tall art and `texture_origin`

Floor tiles fill the 64×32 diamond exactly. Everything with height — walls, furniture,
characters-as-tiles — uses **taller textures** (64×64, 64×96…) whose *base diamond* must sit
on the cell. That alignment is `texture_origin`'s job (per tile, in the atlas Select tab):
shift the texture up by `(art_height - tile_height)` so the bottom diamond of the art
coincides with the cell's diamond.

```
   64×96 wall texture         The bottom 64×32 of the art is the "footprint";
  ┌────────────────┐          texture_origin lifts the rest above the cell:
  │   upper wall   │  ▲
  │     body       │  │ 64 px above the cell
  │                │  ▼
  ├────────────────┤
  │  base diamond  │  ← this part sits IN the 64×32 cell
  └────────────────┘
```

> ⚠️ **Pitfall** — If tall tiles look "sunken into the floor" or float above it, the
> `texture_origin` is wrong — not the layout, not Y-sort. Fix origin first; only then judge
> sorting. Diagnosing in the wrong order wastes hours, because a bad origin *also* shifts
> the Y-sort comparison point.

### Y-sort for isometric: the full recipe

Orthogonal top-down games can often dodge Y-sort; isometric games cannot — overlap ambiguity
is the genre. The complete, working configuration:

1. **Parent container** (`Room`): `y_sort_enabled = true`.
2. **Floor layer**: `y_sort_enabled = false` — floors never contest draw order. Give the
   layer a lower `z_index` or just place it first.
3. **Props/walls layer**: `y_sort_enabled = true` — cells now sort individually.
4. **Actors** (player, NPCs): `y_sort_enabled = true`, children of the same parent; sprite
   offset so the *feet* sit at the node's Y (see
   [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) on sort points).
5. **Per-tile `y_sort_origin`**: for tiles whose visual base is not where the default
   comparison lands (long sofas, arches), nudge the tile's sort point in pixels.
6. **`x_draw_order_reversed`** on the props layer if your art's overlap direction demands
   right-to-left drawing within a row (some wall styles read wrong without it).

### Faking elevation

True isometric height (cliffs, raised platforms, mezzanines) is a *fiction* built from three
levers, since the map is genuinely flat:

- **Stacked layers with offsets.** One `TileMapLayer` per elevation level, each offset
  upward by half a tile height per level (`position.y -= level * tile_size.y / 2` — i.e.,
  16 px per level at 64×32). Cliff-face tiles visually bridge levels.
- **`y_sort_origin` per layer**: raise each elevation layer's sort origin so upper-level
  tiles win draw order against lower-level actors appropriately.
- **Gameplay data**: an "elevation" [custom data](#custom-data-layers-typed-per-tile-metadata)
  field per tile lets movement code refuse cliff transitions and lets spawners reason about
  height — the *logic* of elevation, decoupled from the rendering trick.

This is exactly the technique the Relax Room concept would use for, say, a lofted reading
nook — and the deep worked example (with character transitions between levels) belongs to
[Isometric Games](ISOMETRIC_GAMES.md).

> ✅ **Best practice** — Prototype your isometric sorting with *ugly placeholder tiles* (flat
> colors, big coordinate labels) before committing art. Sorting bugs are configuration bugs;
> they are found in minutes with readable tiles and in days with finished art that hides the
> cell boundaries.

### Beyond isometric: half-offset squares and hexagons

The remaining two tile shapes get honorable-mention treatment here because they reuse every
mechanism already covered, with three localized differences.

**Half-offset square** (`TILE_SHAPE_HALF_OFFSET_SQUARE`): square tiles where every second
row (or column) shifts by half a cell — brickwork layouts, and a budget substitute for
hexes when the art is actually square. **Hexagon** (`TILE_SHAPE_HEXAGON`): true hex cells,
the strategy-game staple.

The three differences:

1. **`tile_offset_axis` becomes load-bearing.** `TILE_OFFSET_AXIS_HORIZONTAL` shifts
   alternate *rows* (pointy-top hexes); `TILE_OFFSET_AXIS_VERTICAL` shifts alternate
   *columns* (flat-top hexes). Combined with `tile_layout` (stacked vs stacked-offset vs
   stairs), this fixes how your `Vector2i` coordinates walk the plane — same
   decide-once-never-change rule as isometric layouts.
2. **Neighborhoods change size and meaning.** A hex cell has *six* side neighbors and no
   meaningful corners-through-which-terrain-flows; the peering-bit diagram in the TileSet
   editor shows six side bits accordingly, and `get_surrounding_cells()` returns six cells.
   Code written against `get_neighbor_cell()` + `CellNeighbor` constants — as
   [section 14](#scripting-tilemaps-the-cell-api-and-coordinates) insisted — keeps working;
   code doing `cell + Vector2i(0, -1)` arithmetic breaks *silently* on offset rows, the
   nastiest class of hex bug.
3. **Distance intuition breaks.** On offset grids, straight-line cell arithmetic zigzags:
   two cells with equal `Vector2i` distance can be different numbers of *steps* apart.
   Pathfinding via `AStarGrid2D` (which understands rectangular lattices, not hex
   adjacency) needs replacing with `AStar2D` built over `get_surrounding_cells()` edges for
   correct hex movement.

Everything else — atlas sources, alternatives, physics/navigation/occlusion polygons
(drawn on hex outlines in the polygon editor), custom data, terrains, the whole cell API —
carries over verbatim. A hex strategy prototype is the same module you just read with a
different `tile_shape` and more patience for coordinate reasoning.

---

## Case study: Relax Room and the freeform alternative

> **Case study context.** Relax Room — this course's running project, dissected in
> [Project Deep Dive](PROJECT_DEEP_DIVE.md) — is a desktop-companion app with one isometric
> room the player decorates. This section preserves and expands the original study notes:
> the project **deliberately ships without tilemaps**, and understanding *why* is as
> instructive as the previous seventeen sections about using them. The tilemap knowledge
> remains foundational for the project's future (modular rooms, a level editor) and for
> reading virtually any 2D Godot codebase.

### How the room actually works (no TileMap)

The shipped scene is a **single-artwork room with freeform decoration sprites**:

```
RoomBackground (Sprite2D)      → room.png (180×155 source, scaled to ~720×620 on screen)
├── WallRect (ColorRect)       → wall color overlay (hex from rooms.json)
├── FloorRect (ColorRect)      → floor color overlay
└── Decorations (Node2D)       → individual Sprite2D nodes created at runtime
    ├── bed_black_1 (Sprite2D)   → sprite_bed_black1.png, scale 3.0
    ├── plant_5 (Sprite2D)       → sc_indoor_plants_w_pot_4.png, scale 6.0
    └── … (other decorations)
```

**Theming** is not tile swapping: it is semi-transparent `ColorRect` overlays
(`alpha = 0.6`) above the base artwork, with palettes defined in `rooms.json`:

```json
"themes": [
	{ "id": "modern",  "wall_color": "2a2535", "floor_color": "3d3347" },
	{ "id": "natural", "wall_color": "2d3025", "floor_color": "3a4230" },
	{ "id": "pink",    "wall_color": "352530", "floor_color": "453540" }
]
```

**Decoration placement** is drag-and-drop of free `Sprite2D` nodes — with an optional
**snap-to-grid** pass, which is the design's quiet nod to tile thinking: positions quantize
to a virtual grid on drop, giving tidy alignment without any tile machinery:

```gdscript
# The essence of Relax Room's snap-to-grid decoration drop:
const GRID := Vector2(24, 12)          # a virtual iso-ish grid — no TileSet involved

func _drop_decoration(deco: Sprite2D, drop_global: Vector2) -> void:
	var local := decorations_root.to_local(drop_global)
	deco.position = local.snapped(GRID)              # quantize — the "tile feel"
	deco.z_index = int(deco.position.y)              # painter's trick: lower = in front
```

Note what this snippet *is*: a hand-rolled, three-line reimplementation of exactly two
tilemap ideas — cell quantization (`local_to_map`/`map_to_local`) and Y-ordered drawing
(Y-sort). The project needed only those two ideas, so it paid three lines instead of a
tileset.

### What a TileMap version would look like

The study's counterfactual, updated to 4.5 idioms:

```
Room (Node2D, y_sort_enabled)
├── Floor (TileMapLayer)          → wood/carpet floor tiles, themes = alternative tiles or modulate
├── Walls (TileMapLayer)          → wall tiles with collision + occluders
├── Furniture (TileMapLayer)      → furniture as tiles (or scene tiles), y_sort_enabled
└── Character (CharacterBody2D)
```

**What the project would gain:**

- Rooms with *different layouts* — L-shapes, balconies, multiple rooms — become paint jobs
  instead of new artworks.
- Wall collision for free, per tile, instead of hand-authored polygons.
- A path to shipping a *room editor* to players: the TileMap editor's data model
  (`set_cell` + `tile_map_data`) is exactly what a player-facing editor needs underneath.
- Theme variants could become TileSet swaps or per-layer `modulate` — comparable effort to
  the ColorRect trick.

**What the project would lose (why the decision went the other way):**

- **The artwork.** `room.png` is a single hand-painted composition. Rebuilding it as tiles
  means cutting it into a seamless, reusable palette — real art budget — and accepting a
  "constructed from parts" look in place of a painterly one.
- **The decoration system already works.** Freeform drag-and-drop with snap gives players
  *continuous* placement freedom; a `Furniture` TileMapLayer would quantize placement to
  full cells and demand every decoration be authored as a tile with origins and sort data.
- **A second source of truth.** Layouts persist today in the project's own JSON (see
  [Database and Persistence](DATABASE_AND_PERSISTENCE.md)); a tilemap would either duplicate
  that in `tile_map_data` or force a migration.
- **Scale mismatch.** One room, ~180×155 source pixels, a few dozen decorations: every
  tilemap efficiency argument (memory, draw calls, bulk collision) is about *scale the
  project does not have*.

### The verdict, as an engineering lesson

The original study notes conclude — and this course endorses — that for the current product
the freeform approach wins. The generalizable lesson is about *thresholds*: tilemaps are an
infrastructure investment whose returns start at "many cells, many rooms, repeated art."
Relax Room sits below every threshold. The moment the roadmap adds modular room layouts or a
player-facing room editor, the calculus flips, and this module is the migration manual.

### If migration ever happens: a sketch

Because Relax Room's layouts already live in JSON, a future structural migration would not
start from the editor — it would start from a *loader* that turns data into cells. The
sketch below is deliberately concrete: it is the shape of the bridge, should the roadmap
ever call for it, and a useful exercise in reading even if it never ships.

```gdscript
# Hypothetical: build a Walls layer from a rooms.json layout block.
# "layout" is a list of strings, one character per cell — the humble, diffable
# level format that has powered roguelikes for forty years:
#
#   "layout": [
#       "##########",
#       "#........#",
#       "#........#",
#       "#####..###"
#   ]

const CHAR_TILES := {
	"#": { "src": 0, "atlas": Vector2i(1, 0) },   # wall
	".": { "src": 0, "atlas": Vector2i(0, 0) },   # floor
}

func build_room(walls: TileMapLayer, ground: TileMapLayer, layout: Array) -> void:
	walls.clear()
	ground.clear()
	for y in layout.size():
		var row: String = layout[y]
		for x in row.length():
			var spec: Dictionary = CHAR_TILES.get(row[x], {})
			if spec.is_empty():
				continue
			var target := walls if row[x] == "#" else ground
			target.set_cell(Vector2i(x, y), spec.src, spec.atlas)
```

Decorations, by contrast, would *stay freeform* even in this future: the migration argument
only ever applied to structure (layout variety, wall collision), never to the drag-and-drop
system players already love. That split — tilemap structure, sprite decorations — is the
hybrid pattern from [section 19](#decision-guide-tilemaplayer-vs-gridmap-vs-freeform-sprites),
and reaching it from the current codebase is a loader function away, not a rewrite.

### A worked reference inside the repo

The study notes also flag a live example already vendored into the project — the virtual
joystick plugin's demo, which *does* use the 4.3+ stack and is worth opening alongside this
module:

```
addons/virtual_joystick/example/main_game/main_game.tscn
├── Parallax2D
│   └── Tiles (Node2D)
│       ├── Floor (TileMapLayer)         → floor with terrains
│       └── Decorations (TileMapLayer)   → decorative overlay tiles
└── Player (CharacterBody2D)
```

Reading checklist for that scene: which node owns the TileSet, how the two layers divide
responsibilities, where terrains are configured, and what the `Parallax2D` wrapper adds —
then compare every observation against
[sections 6](#tilemaplayer-the-node-that-replaced-tilemap)
and [7](#layer-stacking-patterns-ground-props-overlay).

---

## Decision guide: TileMapLayer vs GridMap vs freeform sprites

Three placement technologies compete for any grid-ish Godot scene. This section turns the
case study into a reusable decision procedure.

### The contenders

| | `TileMapLayer` (2D) | `GridMap` (3D) | Freeform sprites (`Sprite2D` + code) |
|---|---|---|---|
| Space | 2D canvas | True 3D grid | 2D canvas |
| Palette | `TileSet` | `MeshLibrary` | Your textures + your data |
| Cell content | Texture region (+ data) | Mesh (+ collision/nav) | Anything |
| Placement | Grid cells | 3D grid cells | Continuous (snap optional) |
| Autotiling | Terrains | None built-in | None |
| Collision | Per-tile polygons, merged | Per-mesh-item shapes | Hand-authored per scene |
| Batching | Rendering quadrants | Octant-based mesh batching | Per-node (unless you optimize) |
| Editor tooling | Full paint suite | 3D paint tools | Whatever you build |
| Sweet spot | Grid-based 2D levels at scale | Blocky/modular 3D levels | Few unique elements, freeform layouts |

`GridMap` appears here for completeness and disambiguation: it is the 3D analogue
(a grid of *meshes* from a `MeshLibrary`), the right tool for voxel-ish or modular-kit 3D
levels — including "3D isometric" games that render true 3D from a locked camera. It shares
tilemap *thinking* but zero API. If your project is 2D, it is simply not in the running; if
you are choosing 2D-iso-with-tiles vs true-3D-with-GridMap, that is an art-pipeline and
camera decision first ([Isometric Games](ISOMETRIC_GAMES.md) discusses it).

### The decision checklist

Score your project honestly; the majority answer usually decides.

1. **Is the level fundamentally repeated cells?** Many cells from a small palette →
   tilemap. A few unique artworks → sprites.
2. **How many levels/rooms share the palette?** One → sprites tolerable. Five+ → tilemap
   authoring cost amortizes fast.
3. **Does placement need to be continuous?** Players dragging items anywhere (Relax Room) →
   sprites (with snap if wanted). Designer-painted structure → tilemap.
4. **Does structure need collision/nav/occlusion at scale?** Hundreds of collidable cells →
   tilemap's declarative model wins. A dozen colliders → hand-authoring is fine.
5. **Will players edit the world in cells?** Building/digging/farming → tilemap,
   near-automatically (the cell API *is* the feature).
6. **Is the art painterly and composed, or modular?** Composed single pieces resist
   tile-ification; modular kits beg for it.
7. **Where does the layout data live?** If an external system (JSON, server) is the source
   of truth, sprites read from data are simple; a tilemap adds a second model to sync —
   unless you generate cells *from* the data at load, which is a fine hybrid.
8. **3D meshes under a fixed camera?** → `GridMap`, different module.

### Hybrids are normal

Production scenes mix freely, and the healthiest architectures usually do:

- **Tilemap structure + sprite actors** — the default: layers for the world,
  `CharacterBody2D`/props as nodes Y-sorted against the props layer.
- **Tilemap structure + freeform decoration** — a Relax Room upgrade path: walls/floor as
  `TileMapLayer` (layout variety, free collision), decorations remain draggable sprites.
  The two systems coexist without friction because Y-sort arbitrates across both.
- **Sprites now, tilemap-shaped data model** — Relax Room today: freeform visuals over a
  quantized virtual grid, keeping a future tilemap migration mechanical (cells already
  exist conceptually in the JSON).

> ✅ **Best practice** — Revisit the decision at roadmap inflection points, not mid-sprint.
> The checklist takes ten minutes with a coffee; migrating a shipped scene takes weeks.
> Write the decision down (an ADR-style note in the repo) so future contributors inherit
> the *reasoning*, not just the scene tree — the original Relax Room study notes preserved
> above are precisely that artifact, and this module exists because they were written.

---

## Best practices

A consolidated checklist of the doctrine developed through the module.

### TileSet authoring

1. **External `.tres` TileSets, always.** Reuse across layers/scenes, pattern sharing,
   clean diffs.
2. **Name sources and keep IDs stable.** Painted maps are foreign keys into the TileSet;
   renumbering is data loss.
3. **Leave `use_texture_padding` on** unless a profiler says otherwise — seams are worse
   than the memory.
4. **Author the variant ladder deliberately:** alternative tile for property tweaks, new
   atlas tile for new art, scene tile for behavior.
5. **Lock `tile_shape`, `tile_layout` and `tile_size` at project start.** Late changes
   scramble every painted map.
6. **Encode variation as data:** `probability` weights on tiles, not painter discipline.

### Scene structure

7. **One `TileMapLayer` per responsibility** (ground / props / overlay), as few layers as
   draw order and rules require.
8. **Y-sort only where actors interleave** — the props layer, not ground or overlay.
9. **`enabled`, not `queue_free()`,** for temporarily inactive floors/areas.
10. **Constants for source IDs, atlas coords and custom-data names** in the scripts that
    paint or query cells — stringly/inty-typed tile code rots fast.

### Physics, navigation, data

11. **Coarse collision polygons.** Boxes and slopes, not art tracings.
12. **Debug visibility first** (Visible Collision Shapes / Visible Navigation) when
    behavior surprises you — look before you read code.
13. **One navigation strategy per map:** tile polygons *or* baked `NavigationRegion2D`,
    never both on the same cells.
14. **Custom data for tile-kind facts; your own dictionaries for per-cell state.**

### Scripting and performance

15. **Bulk-edit then let the frame flush.** Never call `update_internals()` in a loop.
16. **Terrain-solve borders in one pass**, bulk-place interiors with `set_cell()`.
17. **Route positions through `to_local()`/`to_global()`** around `local_to_map()` /
    `map_to_local()`; remember `map_to_local()` returns cell centers.
18. **Seed your generators** and keep `generate()` idempotent.
19. **Use `_tile_data_runtime_update` for per-cell visual exceptions**, not alternative-tile
    explosions or shader hacks.
20. **Re-run the tilemap-vs-alternatives decision at roadmap turns** and write it down —
    the Relax Room case study is the template.

---

## Common errors & troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `set_cell()` seems ignored / "method takes 3 arguments" errors | Pre-4.3 `TileMap` code: layer index passed as first argument | Drop the layer argument; on `TileMapLayer` the signature is `set_cell(coords, source_id, atlas_coords, alternative)` |
| Tiles render as gray/error placeholders | Cells reference a deleted or renumbered source/tile | Restore the source (IDs matter) or run `fix_invalid_tiles()` once the palette change is final |
| Flickering seams / bleeding lines between tiles | Texture filtering on pixel art, or `use_texture_padding` disabled | Set nearest filtering (project default or per-node), re-enable padding on the atlas source |
| Everything shifted by one cell / half a tile | Global position fed to `local_to_map()`, or `map_to_local()` treated as top-left | Wrap with `to_local()`; remember `map_to_local()` returns the **center** of the cell |
| Character walks through painted walls | No physics layer on the TileSet, no polygon on that tile/alternative, `collision_enabled = false`, or wrong collision layer/mask bits | Run with **Debug → Visible Collision Shapes**; add the physics layer, stamp the polygon (press F), check layer/mask matrix |
| Collision works but "which tile did I hit?" is wrong | Assuming one body per cell; bodies are merged per physics quadrant | Map back with `get_coords_for_body_rid(rid)` guarded by `has_body_rid()` |
| Y-sort "does nothing" — player always in front/behind props | Parent container not Y-sorted, or player is not a sibling under it | Enable `y_sort_enabled` on the common parent, the props layer *and* the actor; verify tree structure |
| Props sort against each other wrongly (sofa vs player looks swapped) | Sort points misaligned: sprite feet not at node Y, tile `y_sort_origin` unset | Offset actor sprites so feet sit at node origin; nudge per-tile `y_sort_origin`; consider `x_draw_order_reversed` on iso |
| Tall isometric tiles sink into or float above the floor | Wrong `texture_origin` on the oversized tile | Shift origin so the art's base diamond sits in the cell — fix this **before** judging Y-sort |
| Terrain painting picks visibly wrong transition tiles | Missing neighborhood coverage (e.g., inner corners absent from the 47-set) or mispainted peering bits | Identify the failing neighborhood class; audit bits in the Select tab's terrain overlay; add/fix the tile |
| Terrain tiles flicker between two choices while painting | Two tiles with unintentionally different (or identical-but-wrong) bits | Audit bits; if variants are intentional, differentiate via `probability` weights |
| Pathfinding returns empty paths on the first frame | Navigation server syncs on the next physics frame after map setup | `await get_tree().physics_frame` before the first query |
| Agents jitter or hug walls on tile navigation | Tile-based nav has no `agent_radius`; thousands of micro-regions create seam artifacts | Bake a `NavigationRegion2D` navmesh for large/static maps; keep tile nav for small dynamic boards |
| Massive frame spikes during procedural generation | `update_internals()` (or terrain solving) called per cell inside the loop | Batch: raw `set_cell()` in bulk, one terrain pass at the end, let the frame flush internals |
| Hitches every time one cell changes on a huge static map | Large dirty quadrants rebuilt per edit | Lower `rendering_quadrant_size` (and `physics_quadrant_size`) on frequently edited layers |
| Whole map draws slowly despite few tiles on screen | Ground layer Y-sorted (per-cell items defeat batching) | Disable `y_sort_enabled` everywhere actors don't interleave |
| Scene tiles duplicate or vanish after reparenting them | Scene-tile instances are managed children of the layer | Never reparent/free them manually — `erase_cell()` / `set_cell()` instead |
| Alternative-tile comparisons fail randomly | Transform flag bits (4096+) set on painted cells | Mask flags out before comparing authored IDs (see [section 4](#alternative-tiles-flips-transposes-and-variants)) |
| Editor tile collision shown, but exported build lacks debug shapes you relied on | `DEBUG_VISIBILITY_MODE_FORCE_SHOW` left on / expectations about release builds | Ship `DEFAULT`; gate overlays behind `OS.is_debug_build()` |

---

## Exercises

The labs escalate from palette authoring to a small generator and an isometric build-out.
Where they reference Relax Room assets (`floor_mess*.png`, `room.png`, `rooms.json`), any
similar placeholder art works. Labs 1–3 modernize the original module's practice exercises;
labs 6–8 absorb its isometric, terrain and pathfinding labs.

### Lab 1 — First TileSet and layer *(45 min)*

Build `test_tilemap.tscn`: one `TileMapLayer`, a new external TileSet
(`tile_size = 32×32`), one atlas source from a floor sheet (the project's `floor_mess*.png`
sprites tiled into a sheet, or any 32×32 tileset). Paint a 20×12 floor with the rect and
bucket tools.

- **Acceptance criteria:** TileSet saved as `.tres`; atlas has named source with correct
  `texture_region_size`; at least three distinct tiles painted; no error placeholders.
- **Stretch:** enable random painting with two decorative variants at `probability 0.15`
  and re-bucket the floor; confirm the variant density looks right.

### Lab 2 — Collision playground *(45 min)*

Add a `Walls` TileMapLayer sharing the TileSet. Add a physics layer to the TileSet, stamp
full-cell polygons on wall tiles (F key), paint a walled arena, and drop in a
`CharacterBody2D` with simple 8-direction movement.

- **Acceptance criteria:** character cannot leave the arena; **Debug → Visible Collision
  Shapes** shows polygons exactly on wall cells; ground tiles have no collision.
- **Stretch:** add a one-way platform tile and verify jump-through behavior; add a
  conveyor tile using constant linear velocity and observe the push.

### Lab 3 — Terrains: two-terrain autotiling *(60 min)*

Create a terrain set (Corners and Sides) with terrains "Grass" and "Dirt" using a standard
47-tile template sheet. Paint peering bits, then draw with the terrain brush in Connect
mode; carve a one-cell dirt path in Path mode.

- **Acceptance criteria:** painting large grass blobs produces correct outer *and inner*
  corners; the path stays one cell wide; erasing with the terrain brush heals borders.
- **Stretch:** deliberately delete one inner-corner tile, reproduce the wrong-transition
  artifact, then restore it — you now recognize the failure signature from
  [section 13](#terrains-autotiling-in-depth) on sight.

### Lab 4 — Custom data: footsteps and surfaces *(45 min)*

Add custom data layers `footstep_sound: String` and `decoration_surface: bool` to the
TileSet. Paint values across floor tiles (property painting mode). In the character script,
print the footstep sound of the tile underfoot each time movement starts.

- **Acceptance criteria:** crossing from wood to carpet changes the printed sound with no
  per-tile `if` chains in code; empty cells fall back to a default.
- **Stretch:** implement `can_place_decoration(global_pos) -> bool` from
  `decoration_surface` — the Relax Room bridge — and reject drops on walls.

### Lab 5 — Patterns and the layer stack *(45 min)*

Restructure into the canonical Ground / Props / Overlay stack
([section 7](#layer-stacking-patterns-ground-props-overlay)). Build one furniture
arrangement, store it as a pattern, and stamp it three times. Add an overlay archway that
fades (`modulate` tween) when the character walks under it.

- **Acceptance criteria:** three layers with correct per-layer flags (only Props Y-sorted);
  pattern stored in the TileSet and stamped via the Patterns tab; archway fade works both
  directions.
- **Stretch:** stamp the same pattern from code with `set_pattern()` at a random valid
  location on a key press.

### Lab 6 — Isometric room *(90 min)*

New TileSet: `TILE_SHAPE_ISOMETRIC`, `TILE_LAYOUT_DIAMOND_DOWN`, `tile_size 64×32`
(placeholder diamond tiles are fine — flat colors with painted coordinates encouraged).
Build floor + walls with tall (64×64) wall tiles, configure the full Y-sort recipe from
[section 17](#isometric-tilemaps), and walk a character behind and in front of a wall.

- **Acceptance criteria:** tall tiles sit exactly on their cells (`texture_origin`
  correct); the character correctly disappears behind south-facing walls and draws in
  front of north-facing ones; floor layer is *not* Y-sorted.
- **Stretch:** add a second elevation layer offset by −16 px with a cliff tile bridging
  levels; give raised tiles `elevation = 1` custom data and block walking up without a
  ramp cell.

### Lab 7 — Procedural dungeon *(120 min)*

Implement the `RoomGenerator` from
[section 15](#procedural-generation-a-room-generator) in a fresh scene, with your Lab 2
TileSet. Wire a "reroll" key that calls `generate()` with a new seed and an on-screen label
showing the current seed.

- **Acceptance criteria:** every reroll yields connected, walled, non-overlapping rooms;
  the same seed reproduces the same map; walls collide; generation of a 48×32 map is
  visually instant.
- **Stretch:** replace `_stamp_floors()` with the terrain variant; then time both with
  `Time.get_ticks_usec()` and record the difference — you have now measured the solver
  cost claimed in [section 13](#terrains-autotiling-in-depth).

### Lab 8 — Navigation two ways *(90 min)*

On a copy of the Lab 7 dungeon: (a) add a navigation layer to the TileSet, nav polygons on
floor tiles, and a `NavigationAgent2D` NPC that walks to clicked cells; (b) on a second
copy, strip tile navigation and bake a `NavigationRegion2D` over the same geometry.

- **Acceptance criteria:** both NPCs reach clicked destinations; the first query waits one
  physics frame; you can articulate two observed differences (path smoothness near walls,
  behavior on a re-generated map).
- **Stretch:** regenerate the dungeon at runtime in both variants and compare what it takes
  to keep navigation correct (automatic vs re-bake with
  `bake_navigation_polygon(true)`).

### Lab 9 — The Relax Room memo *(60 min, design exercise)*

Using the checklist in
[section 19](#decision-guide-tilemaplayer-vs-gridmap-vs-freeform-sprites), write a one-page
ADR-style memo: *"Should Relax Room v2 adopt TileMapLayer for (a) room structure and
(b) decorations?"* Score all eight checklist questions for both subsystems against the case
study facts in [section 18](#case-study-relax-room-and-the-freeform-alternative).

- **Acceptance criteria:** separate verdicts for structure vs decorations, each with at
  least three checklist-grounded arguments; an explicit trigger condition ("adopt tiles for
  structure when the roadmap includes X").
- **Stretch:** prototype the hybrid — a 10-minute `Walls` TileMapLayer under the existing
  freeform decorations — and note every friction point you hit for the memo's appendix.

### Self-check questions

Answer without notes; every answer is in this module.

1. What three values does a painted cell store, and where does everything else live?
2. In which Godot version was `TileMap` deprecated, and what is the one-click migration
   path?
3. Why does `map_to_local()` + `global_position` without `to_global()` produce shifted
   results on a transformed layer?
4. When does a tile deserve to be a scene tile rather than an atlas tile with custom data?
5. How many peering-bit relationships does Corners-and-Sides mode check on a square tile,
   and why does full coverage take 47 tiles rather than 2⁸ = 256?
6. What exactly happens, and when, after you call `set_cell()` 5,000 times in one frame?
7. Which layers in a ground/props/overlay stack should have `y_sort_enabled`, and what
   does it cost where enabled?
8. Give two reasons Relax Room's freeform decoration system beat a `Furniture`
   TileMapLayer — and the roadmap change that would most strongly reverse one of them.

---

## Further reading

Official documentation first — every API claim in this module was verified against these
pages at the course's 4.5 pin.

### Official Godot documentation

- [Using TileSets](https://docs.godotengine.org/en/4.5/tutorials/2d/using_tilesets.html) —
  the canonical walkthrough of everything in sections 2–5 and 9–13: atlas setup, physics/
  navigation/occlusion layers, custom data, terrain sets and alternative tiles, with
  editor screenshots this text deliberately does not duplicate.
- [Using TileMaps](https://docs.godotengine.org/en/4.5/tutorials/2d/using_tilemaps.html) —
  the painting-workflow companion: every tool, random/scattering, terrains brush modes and
  the patterns tab. Keep it open during Labs 1–5.
- [TileMapLayer class reference](https://docs.godotengine.org/en/4.5/classes/class_tilemaplayer.html) —
  the full API surface from section 6; read the property descriptions for quadrant and
  debug-visibility details, and the virtual methods for the runtime-update pipeline.
- [TileSet class reference](https://docs.godotengine.org/en/4.5/classes/class_tileset.html) —
  shapes, layouts, schema-layer management and the `CellNeighbor` enum used by
  `get_neighbor_cell()` and peering bits.
- [TileData class reference](https://docs.godotengine.org/en/4.5/classes/class_tiledata.html) —
  the per-tile record: custom data accessors, per-physics-layer polygon queries, occluder
  polygons and terrain bits.
- [TileMap class reference](https://docs.godotengine.org/en/4.5/classes/class_tilemap.html) —
  read *only* for migration: the deprecation notice and the mapping from layer-indexed
  methods to `TileMapLayer`.
- [Navigation using NavigationMeshes](https://docs.godotengine.org/en/4.5/tutorials/navigation/navigation_using_navigationmeshes.html) —
  the baked-navigation side of section 10, including why runtime-parsing tilemaps is
  flagged as performance-intensive.

### Community and course-adjacent

- [GDQuest — Tilemap Editor Basics cheat sheet](https://www.gdquest.com/library/cheatsheet_tilemap_basics/)
  and [Setting Up Tilesets cheat sheet](https://www.gdquest.com/library/cheatsheet_tileset_setup/) —
  one-page visual references for the editor tools; print-worthy during the labs.
- [GDQuest — Hands-On Terrains lesson](https://school.gdquest.com/courses/learn_2d_gamedev_godot_4/side_scroller_levels/configuring_terrain_autotiles) —
  a guided first terrain setup that pairs well with Lab 3 if peering bits refuse to click
  from prose alone.
- [GameFromScratch — Godot TileMap replaced with TileMapLayers](https://gamefromscratch.com/godot-tilemap-replaced-with-tilelayers/) —
  contemporaneous coverage of the 4.3 split, useful for the *why* behind the migration
  section when reading older codebases.

### Sibling modules

- [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) — texture import, filtering and atlas
  hygiene that tilesheets inherit.
- [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) — Y-sort, `z_index` and
  draw order, assumed throughout sections 7 and 17.
- [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md) — projection math, cameras and genre patterns on
  top of section 17.
- [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) — the full Relax Room scene tree behind the
  case study.
- [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) — profiling
  methodology referenced in section 16.
- [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md) — where layout data should
  live, and the `tile_map_data` save trade-offs.
- [VISUAL_SYSTEMS_SUMMARY.md](VISUAL_SYSTEMS_SUMMARY.md) — the Phase 2 recap that places
  this module among its siblings.

---

## Glossary

| Term | Definition |
|---|---|
| **Alternative tile** | A numbered variant of an atlas tile sharing its texture region but overriding properties (flips, modulate, physics, custom data). Alternative 0 is the base tile. |
| **Atlas source** | `TileSetAtlasSource` — a TileSet source that slices tiles from one texture sheet using region size, margins and separation. |
| **Autotiling** | Automatic selection of transition tiles while painting; implemented in Godot 4 by terrains. |
| **Blob (47-tile)** | The standard template covering all neighborhood classes of one terrain vs empty in Corners-and-Sides mode. |
| **Cell** | One grid position on a `TileMapLayer`, storing `(source_id, atlas_coords, alternative_tile)`. |
| **Custom data layer** | A named, typed field declared on the TileSet that every tile can fill; read via `TileData.get_custom_data()`. |
| **GridMap** | The 3D analogue of a tilemap: a grid of meshes from a `MeshLibrary`. No API overlap with the 2D tile stack. |
| **Half-offset square** | Tile shape where alternate rows/columns shift by half a cell; with hexagons, governed by `tile_offset_axis`. |
| **Isometric (tile shape)** | Diamond-cell projection (`TILE_SHAPE_ISOMETRIC`), classically at a 2:1 width:height ratio such as 64×32. |
| **Map coordinates** | `Vector2i` cell indices — the space of `set_cell()`; converted to pixels via `map_to_local()`. |
| **Match mode** | A terrain set's neighbor-agreement rule: Corners and Sides, Corners only, or Sides only. |
| **Occlusion layer** | TileSet schema whose per-tile polygons block 2D lights, feeding `LightOccluder2D`-style shadows. |
| **One-way collision** | Per-polygon flag making a tile block bodies from one face only (jump-through platforms). |
| **Pattern** | A stored multi-cell arrangement (`TileMapPattern`), kept in the TileSet and stamped via the Patterns tab or `set_pattern()`. |
| **Peering bit** | A per-tile terrain value on one neighbor relationship (side or corner), promising what terrain shows across that border; `-1` = empty. |
| **Physics layer (TileSet)** | Schema declaring collision layer/mask/material; tiles contribute collision polygons to it. |
| **Physics quadrant** | Block of cells (default 16×16) whose tile collision merges into shared static bodies (`physics_quadrant_size`, 4.4+). |
| **Probability** | `TileData` weight used by random painting (and reusable by your own RNG) to pick among candidate tiles. |
| **Rendering quadrant** | Block of cells (default 16×16) batched into few canvas items; the unit of rebuild when cells change (`rendering_quadrant_size`). |
| **Scene collection source** | `TileSetScenesCollectionSource` — a source whose tiles instantiate `PackedScene`s at their cells; selected via the alternative ID. |
| **Source ID** | Stable integer identifying one source inside a TileSet; first component of every painted cell. |
| **Terrain** | One material within a terrain set ("Grass"); tiles assigned to it carry peering bits describing tolerated neighbors. |
| **Terrain set** | A group of terrains that can transition into each other under a single match mode. |
| **`texture_origin`** | Per-tile pixel offset anchoring the texture relative to its cell — the tool that seats oversized/tall art. |
| **TileData** | The per-tile record object exposing rendering, physics, navigation, terrain and custom-data properties; obtained via `get_cell_tile_data()`. |
| **TileMap (node)** | The legacy all-layers-in-one node of Godot 4.0–4.2; deprecated since 4.3 in favor of `TileMapLayer`. |
| **`tile_map_data`** | The `PackedByteArray` serializing a layer's entire cell database; storable as an opaque save blob. |
| **TileMapLayer** | The Godot 4.3+ node rendering and simulating one grid of cells with one TileSet; one node per layer. |
| **TileSet** | The palette resource: sources, shapes, and the physics/navigation/occlusion/custom-data/terrain schemas all tiles share. |
| **Y-sort origin** | Pixel offset (per tile and per layer) of the point used in Y-sorted draw-order comparisons. |

---

> **Module 05 complete.** Next in Phase 2: [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md) applies
> materials to everything you can now paint, and [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md)
> deepens the projection work begun in [Isometric tilemaps](#isometric-tilemaps). For the
> phase overview, see [VISUAL_SYSTEMS_SUMMARY.md](VISUAL_SYSTEMS_SUMMARY.md).






