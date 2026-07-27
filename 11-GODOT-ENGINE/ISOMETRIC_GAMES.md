---
course: "Godot 4 in Production"
phase: "2 — Visual systems"
module: "07"
title: "Isometric Games — Projection Math, Depth Sorting and Movement"
version: "Godot 4.5 / GDScript 2.0"
level: "Intermediate-Advanced"
prerequisites: [ "RENDERING_AND_VISUAL_LOGIC.md", "TILES_AND_TILEMAPS.md" ]
objectives:
  - "Derive the cartesian↔isometric transforms as 2×2 matrices and implement them as a typed GDScript helper class"
  - "Convert between tile, world and screen coordinates, including robust mouse picking with diamond hit-testing"
  - "Choose and implement the correct depth-sorting strategy (y-sort, z_index formulas, topological sort) for a given scene"
  - "Build isometric worlds three ways: TileMapLayer diamond modes, manual Sprite2D placement with snap grid, and hybrids"
  - "Implement 8-direction isometric character movement with correct normalization and direction-set animation"
  - "Ship grid pathfinding with AStarGrid2D (diagonal modes, heuristics, weights) and graph pathfinding with AStar2D"
  - "Configure Camera2D and pixel-art constraints (integer zoom, 2:1 tiles, nearest filtering) for a clean isometric look"
tags: [godot, gdscript, isometric, dimetric, projection, depth-sorting, y-sort, tilemap, astar, pathfinding, pixel-art, camera2d]
---

# Isometric Games — Projection Math, Depth Sorting and Movement — Complete Guide

> **Module 07** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md), [Tiles and TileMaps](TILES_AND_TILEMAPS.md) — plus trigonometry basics and 2D matrix multiplication from [Godot Engine Study](GODOT_ENGINE_STUDY.md).
>
> By the end of this module you will be able to:
> 1. Explain the axonometric projection family (isometric, dimetric, trimetric, oblique) and justify why pixel-art games use the 2:1 dimetric compromise instead of true 30° isometric.
> 2. Derive and implement the cartesian↔isometric coordinate transforms as matrices and as a reusable static GDScript class, including elevation faking with y-offsets.
> 3. Convert mouse positions to tile coordinates with correct diamond hit-testing, and tiles back to screen positions for placement previews.
> 4. Diagnose and fix depth-sorting problems using `y_sort_enabled`, per-sprite origin discipline, `z_index` formulas, and sprite splitting for tall or multi-tile objects.
> 5. Build an isometric map with `TileMapLayer` (isometric tile shape, diamond layouts) and compare it against manual `Sprite2D` placement as used in Relax Room.
> 6. Implement click-to-move characters with `AStarGrid2D`, including diagonal modes, heuristics, and per-tile cost weights read from TileSet custom data.
> 7. Tune `Camera2D` limits, smoothing and integer zoom so scrolling and shake never break the pixel grid.
>
> **Estimated time:** 8-10 hours reading + labs · **Level:** Intermediate-Advanced

## Guiding ideas

1. **Isometric is 2D pretending to be 3D — the whole genre is one 2×2 matrix plus a sorting rule.**
2. **Pixel art does not use true isometric: the 2:1 dimetric compromise (26.565°) exists because pixels are square.**
3. **Depth sorting is the hard part; projection math is the easy part. Budget your effort accordingly.**
4. **The sprite's origin is a contract: y-sort only works if every origin sits at the object's ground contact point.**
5. **Logic lives in tile space, rendering lives in screen space — convert at the boundary, never mix the two.**
6. **A desktop companion like Relax Room can borrow isometric techniques (y-sort, snapping, zones) without adopting the full grid.**

## Concept map

```
                        ┌──────────────────────────────┐
                        │   ISOMETRIC GAMES (Module 07)│
                        └──────────────┬───────────────┘
                                       │
        ┌──────────────────┬───────────┼─────────────┬──────────────────┐
        │                  │           │             │                  │
 ┌──────▼──────┐   ┌───────▼──────┐ ┌──▼─────────┐ ┌─▼────────────┐ ┌───▼──────────┐
 │ PROJECTION  │   │ COORDINATES  │ │ DEPTH      │ │ WORLD        │ │ MOVEMENT &   │
 │ MATH        │   │ & PICKING    │ │ SORTING    │ │ BUILDING     │ │ PATHFINDING  │
 └──────┬──────┘   └───────┬──────┘ └──┬─────────┘ └─┬────────────┘ └───┬──────────┘
        │                  │           │             │                  │
 ┌──────┴──────┐   ┌───────┴──────┐ ┌──┴─────────┐ ┌─┴────────────┐ ┌───┴──────────┐
 │ axonometric │   │ tile↔world↔  │ │ y_sort_    │ │ TileMapLayer │ │ input→iso    │
 │ taxonomy    │   │ screen       │ │ enabled    │ │ diamond      │ │ axes         │
 │ 30° vs 2:1  │   │ diamond hit- │ │ origin     │ │ layouts      │ │ AStarGrid2D  │
 │ 2×2 matrix  │   │ testing      │ │ discipline │ │ manual snap  │ │ AStar2D      │
 │ elevation   │   │ mouse→tile   │ │ z_index    │ │ (Relax Room) │ │ NavAgent2D   │
 │ (y-offset)  │   │ picking      │ │ formulas   │ │ hybrid       │ │ 8-dir anim   │
 └─────────────┘   └──────────────┘ │ topo sort  │ └──────┬───────┘ └───┬──────────┘
                                    │ splitting  │        │             │
                                    └──┬─────────┘        │             │
                                       │                  │             │
                          ┌────────────▼─────────┐ ┌──────▼─────────────▼─────┐
                          │ PIXEL-ART DISCIPLINE │ │ PRESENTATION             │
                          │ 64×32 tiles, 2:1     │ │ Camera2D limits/zoom     │
                          │ line stepping, no AA │ │ performance, culling     │
                          │ palette, atlases     │ │ famous games analysis    │
                          └──────────────────────┘ └──────────────────────────┘
```

## Table of contents

1. [Overview — the isometric illusion](#1-overview--the-isometric-illusion)
2. [Axonometric projections — a taxonomy](#2-axonometric-projections--a-taxonomy)
3. [Projection math — deriving the transforms](#3-projection-math--deriving-the-transforms)
4. [Coordinate spaces — tile, world, screen](#4-coordinate-spaces--tile-world-screen)
5. [Mouse picking and diamond hit-testing](#5-mouse-picking-and-diamond-hit-testing)
6. [Faking elevation — the z axis that isn't there](#6-faking-elevation--the-z-axis-that-isnt-there)
7. [Depth sorting I — y-sort and origin discipline](#7-depth-sorting-i--y-sort-and-origin-discipline)
8. [Depth sorting II — z_index formulas and topological sorting](#8-depth-sorting-ii--z_index-formulas-and-topological-sorting)
9. [Depth sorting III — artifacts, splitting, occlusion](#9-depth-sorting-iii--artifacts-splitting-occlusion)
10. [Building isometric worlds with TileMapLayer](#10-building-isometric-worlds-with-tilemaplayer)
11. [Manual placement — the Relax Room way (case study)](#11-manual-placement--the-relax-room-way-case-study)
12. [Character movement in isometric space](#12-character-movement-in-isometric-space)
13. [Animation direction sets](#13-animation-direction-sets)
14. [Pathfinding on grids — AStarGrid2D](#14-pathfinding-on-grids--astargrid2d)
15. [Pathfinding beyond grids — AStar2D and NavigationServer2D](#15-pathfinding-beyond-grids--astar2d-and-navigationserver2d)
16. [Camera for isometric scenes](#16-camera-for-isometric-scenes)
17. [Pixel art for isometric games](#17-pixel-art-for-isometric-games)
18. [Performance engineering for isometric scenes](#18-performance-engineering-for-isometric-scenes)
19. [Famous isometric games — technical analysis](#19-famous-isometric-games--technical-analysis)
20. [Room-based isometric design for companion apps (case study)](#20-room-based-isometric-design-for-companion-apps-case-study)
21. [Best practices](#best-practices)
22. [Common errors & troubleshooting](#common-errors--troubleshooting)
23. [Exercises](#exercises)
24. [Further reading](#further-reading) · [Glossary](#glossary)

**How to study this module.** Three passes work well: (1) read Sections 1-9 straight through — projection and sorting are one continuous argument, and the labs assume it whole; (2) work Sections 10-16 *at the editor*, pairing each section with its lab (Lab 4 with §10, Lab 7 with §14, Lab 9 with §16); (3) treat Sections 17-20 as reference and case-study material to revisit when your own project reaches each topic. If you are here to fix a specific bug, jump straight to the [troubleshooting table](#common-errors--troubleshooting) — every row links back to the explaining section. Relax Room material is confined to clearly marked case-study blocks (§11, §20) and short "Relax Room note" paragraphs elsewhere; the rest of the module is project-agnostic Godot 4.5.

---

## 1. Overview — the isometric illusion

Isometric games occupy a peculiar and productive middle ground in game rendering. They present a world that *reads* as three-dimensional — you see the tops and two sides of objects, characters walk "behind" furniture, buildings have visible height — yet everything on screen is flat 2D sprites drawn in a carefully chosen order. There is no 3D camera, no perspective divide, no depth buffer doing the work for you. The illusion is manufactured from exactly two ingredients:

1. **A projection**: a fixed linear mapping that converts logical grid coordinates into screen positions, so that a square grid appears as a field of diamonds.
2. **A sorting rule**: a policy that decides which sprite is drawn over which, so that near things occlude far things.

Everything else in this module — picking, elevation, movement, pathfinding, camera work — is a consequence of those two decisions. This is worth internalizing early because it tells you where the difficulty lives. The projection is a one-time mathematical decision that you implement once in a helper class and never touch again. The sorting rule, by contrast, interacts with *every sprite you ever add to the scene*: its texture, its origin point, its footprint on the grid, whether it is taller than one tile, whether it spans multiple tiles. Teams that budget a week for "the isometric engine" typically spend a day on projection and the rest of the month on sorting edge cases.

### Why choose isometric at all?

Compared with pure top-down (Zelda-style) and side-view (platformer) presentations, isometric buys you:

| Property | Top-down | Side view | Isometric |
|---|---|---|---|
| Object height visible | No (implied) | Yes | Yes |
| Floor layout visible | Yes | No | Yes |
| Sprite reuse across rotations | High | High | Low (per-direction art) |
| Depth sorting complexity | Low-medium | Low | **High** |
| Feels "architectural" | Weak | Weak | **Strong** |
| Art cost | Low | Low | **High (2-5× frames)** |

That "architectural" quality is why the projection dominates city builders (SimCity 2000), base builders (RollerCoaster Tycoon), tactics games (Final Fantasy Tactics, Into the Breach), and room-decoration games (The Sims, Habbo Hotel). When the *space itself* is the subject of the game — building it, decorating it, reasoning about it tactically — the player needs to see both the floor plan and the vertical structure at once, and isometric is the cheapest projection that delivers both.

For **Relax Room**, our running case study, this is exactly the appeal: the room is the product. The app is a desktop companion whose core loop is decorating a small personal space, so the presentation must show the floor (where the rug and desk go) and the wall (where the paintings hang) simultaneously. Relax Room deliberately stops short of a full isometric grid — Section 11 examines that decision in detail — but every technique it does use (y-sort, snapping, placement zones, origin discipline) comes straight from the isometric toolbox.

### The two coordinate worlds

The single most important habit in isometric programming is keeping two coordinate systems rigorously separate:

```
LOGICAL SPACE (tile coordinates)          VISUAL SPACE (screen pixels)

  +----+----+----+----+                            ◇
  |0,0 |1,0 |2,0 |3,0 |                          ◇   ◇
  +----+----+----+----+                        ◇   ◇   ◇
  |0,1 |1,1 |2,1 |3,1 |      project        ◇   ◇   ◇   ◇
  +----+----+----+----+     ─────────►        ◇   ◇   ◇
  |0,2 |1,2 |2,2 |3,2 |                         ◇   ◇
  +----+----+----+----+     ◄─────────            ◇
  |0,3 |1,3 |2,3 |3,3 |      unproject
  +----+----+----+----+

  Game rules live here:                   Rendering lives here:
  - pathfinding                           - sprite positions
  - occupancy / collision                 - draw order
  - "is this tile free?"                  - mouse coordinates (raw)
```

All game logic — occupancy checks, pathfinding, adjacency, save data — operates on plain integer tile coordinates as if the game were a spreadsheet viewed from directly above. Only at the rendering boundary do you project those coordinates into diamond-world screen positions; only at the input boundary do you unproject mouse pixels back into tile coordinates. Games that blur this line (storing "the chair is at pixel 412, 217") accumulate unfixable bugs: pathfinding distances stop matching visual distances, saves break when tile art changes size, and every feature needs its own ad-hoc math.

> ✅ **Best practice** — Decide on day one that tile coordinates are the source of truth and screen positions are *derived data*. If you can delete every sprite in the scene and rebuild the visual state purely from the logical grid, your architecture is correct.

> ⚠️ **Pitfall** — "Isometric" in game development almost never means mathematically isometric. As Section 2 shows, nearly every pixel-art "isometric" game is actually *dimetric* at a 2:1 pixel ratio. The industry uses the word loosely; the math in this module is precise about the difference, and you should be too when reading tile dimensions off reference art.

### Module roadmap

Sections 2-6 build the mathematical foundation: the projection family, the transform matrices, the three coordinate spaces, picking, and elevation. Sections 7-9 attack depth sorting from simple (`y_sort_enabled`) to hard (multi-tile topological sorting). Sections 10-11 cover the two ways to build isometric worlds in Godot 4.5 — `TileMapLayer` and manual placement — with Relax Room as the case study for the latter. Sections 12-15 handle characters: input mapping, animation sets, and pathfinding with `AStarGrid2D`, `AStar2D` and `NavigationAgent2D`. Sections 16-18 cover presentation and performance. Section 19 mines eight famous games for transferable techniques, and Section 20 closes with the room-based design pattern for companion apps.

---

## 2. Axonometric projections — a taxonomy

"Isometric" belongs to a family of projections called **axonometric projections**: parallel projections in which the object is rotated relative to the viewing plane so that multiple faces are visible at once. *Parallel* is the operative word — unlike perspective projection, parallel lines in the world stay parallel on screen, and objects do not shrink with distance. This is what makes axonometric rendering trivially compatible with 2D sprites: a chair sprite looks identical at every position on the map, so one texture serves the whole world.

### 2.1 The projection family tree

```
                         3D → 2D PROJECTIONS
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
        PERSPECTIVE                             PARALLEL
   (lines converge at                    (parallel lines stay
    vanishing points;                     parallel; size is
    size shrinks with                     distance-independent)
    distance)                                      │
              │                    ┌───────────────┴───────────────┐
        FPS, racing,               │                               │
        modern 3D            ORTHOGRAPHIC                       OBLIQUE
                          (projection rays ⊥              (projection rays hit
                           to picture plane)               picture plane at an angle;
                                   │                       front face undistorted)
              ┌────────────────────┼──────────────┐               │
              │                    │              │         Ultima Online-style
          TOP-DOWN /          AXONOMETRIC     SIDE VIEW     "cheated" 3/4 views,
          PLAN VIEW         (object rotated   (platformers) cavalier & cabinet
        (Zelda NES-ish)      to show 3 faces)               drawings
                                   │
                  ┌────────────────┼────────────────┐
                  │                │                │
             ISOMETRIC         DIMETRIC         TRIMETRIC
           (all 3 axes       (2 axes share     (all 3 axes
            equally           a scale, 1        differently
            foreshortened)    differs)          foreshortened)
                  │                │                │
            SimCity 2000     ALL 2:1 pixel     Rare; used for
            (true 30° art)   art "isometric"   stylistic slants
                             games; Diablo     (some Fallout art
                             (26.565°-ish)     leans trimetric)
```

The three axonometric variants differ only in how the three world axes are foreshortened:

| Projection | Axis scales | Typical screen angle | Pixel-art friendliness |
|---|---|---|---|
| **Isometric** | all three equal | 30° from horizontal | Poor — 30° lines produce ragged pixel stairs |
| **Dimetric** | two equal, one different | 26.565° (the 2:1 case) | **Excellent** — perfect 2:1 pixel steps |
| **Trimetric** | all three different | anything | Poor — two different ragged angles |
| **Oblique** | front face 1:1, depth axis slanted | 45° depth typically | Moderate — front faces are easy, depth looks "wrong" |

### 2.2 True isometric — the 30° ideal

In a mathematically true isometric projection, the three world axes are projected 120° apart on screen, and each makes a 30° angle with the horizontal. All three axes are foreshortened equally (by a factor of √(2/3) ≈ 0.8165), which is what *iso-metric* — "equal measure" — means.

```
TRUE ISOMETRIC (engineering drawing standard)

               +z (up)
                │
                │
                │
                ●
               ╱ ╲
        30°  ╱     ╲  30°
           ╱         ╲
         ╱             ╲
       +x               +y
   (down-left)      (down-right)

   Angle between any two axes on screen: 120°
   Slope of the x and y axes: tan(30°) = 1/√3 ≈ 0.577
   A unit cube's top face appears as a rhombus with
   width : height = √3 : 1 ≈ 1.732 : 1
```

The problem for pixel art is that 0.577 slope: to draw a 30° line on a square pixel grid you need a repeating pattern that rises 1 pixel for every ≈1.732 pixels of run. Since you cannot draw 0.732 of a pixel, the line becomes an irregular stutter of 2-step and 1-step segments. Tile edges drawn this way look chewed, and adjacent tiles never seam cleanly.

```
Attempting a true 30° edge in pixels (slope 1 : 1.732):

        ██
      ██          ← 2 across, 1 up
    ██
  ██              ← sometimes 1 across, 1 up to average out
██                   the 1.732 — the rhythm is IRREGULAR
                     and the eye catches it immediately
```

### 2.3 The 2:1 dimetric compromise — 26.565°

Pixel artists solved this by asking the question backwards: *what angle produces a perfectly regular pixel pattern?* The answer is the line that advances exactly 2 pixels horizontally for every 1 pixel vertically. Its angle is:

```
θ = arctan(1/2) = 26.565°   (precisely: arctan(0.5) ≈ 26.56505°)
```

Because the two "ground" axes now sit at 26.565° instead of 30°, the projection is technically **dimetric** — the vertical axis is foreshortened differently from the two ground axes. But the pixel payoff is enormous:

```
The 2:1 edge — perfectly regular:

            ████
        ████          ← every step: exactly 2 across, 1 up
    ████
████                     Clean, repeatable, seam-friendly.
                         This IS "isometric pixel art".

A 2:1 diamond tile (the atom of the genre):

              ██████
          ████░░░░░░████
      ████░░░░░░░░░░░░░░████
  ████░░░░░░░░░░░░░░░░░░░░░░████     width  = 2 × height
  ████░░░░░░░░░░░░░░░░░░░░░░████     e.g. 64 × 32, 128 × 64
      ████░░░░░░░░░░░░░░░░████
          ████░░░░░░░░████
              ██████
```

This is why virtually every tile size you will ever encounter in "isometric" games is a 2:1 rectangle — 32×16, 64×32, 128×64, 256×128 — and why this module, like the industry, says "isometric" while meaning "2:1 dimetric" unless explicitly discussing true 30° projection.

> ✅ **Best practice** — When you receive or commission isometric art, verify the ratio before writing any code: measure the diamond's bounding box. If it is exactly 2:1, all the math in Section 3 applies with `tile_width = 2 × tile_height`. If an artist hands you true-30° art (1.732:1), either re-commission it or adjust every transform constant — mixing the two in one project guarantees seam artifacts.

### 2.4 Trimetric and oblique — the outliers

**Trimetric** projection foreshortens all three axes differently. It appears occasionally as a stylistic choice — some classic Fallout art and SimCity 4's renderer lean trimetric — because slightly unequal angles can look more "photographed" and less diagrammatic. The cost is that no two edges share a pixel pattern, so hand-drawn trimetric pixel art is punishing; the games that used it typically pre-rendered 3D models to sprites (Section 19).

**Oblique** projection keeps the front face of every object completely undistorted (a true 1:1 elevation drawing) and slants the depth axis, usually at 45°. Ultima VI-era RPGs and many JRPG interiors use an oblique-ish cheat: floors drawn as if from above, furniture fronts drawn as if from the side. It is easy to draw and easy to read but geometrically inconsistent — the projection cannot survive object rotation, and depth-sorting rules become object-specific.

```
OBLIQUE (cabinet-style)               DIMETRIC 2:1

  ┌─────────┐                              ██████
  │  FRONT  │╲                         ████░░░░░░████
  │  FACE   │ ╲  depth at 45°,     ████░  TOP FACE  ░████
  │ (1:1,   │  ╲ often half-scale  ████░░░░░░░░░░░░░░████
  │ undis-  │   ╲                    ╲ LEFT ╲ ╱ RIGHT ╱
  │ torted) │    ╲                    ╲ FACE ╲╱ FACE ╱
  └─────────┘     ╲                    ╲░░░░░╱╲░░░░░╱
                                        ╲░░░╱  ╲░░░╱
  Fronts perfect, depth "wrong"        All faces consistently angled
```

**Relax Room's presentation is closest to oblique**: the back wall is drawn flat-on (a 1:1 elevation), the floor is an implied receding plane, and furniture sprites are drawn from a straight-ahead 3/4 view. This is a deliberate simplification examined in Sections 11 and 20 — the room reads as a cozy diorama without requiring diamond tiles or per-direction furniture art.

### 2.5 Choosing a projection — decision table

| If your game needs… | Choose | Because |
|---|---|---|
| Tile-grid building/tactics with pixel art | 2:1 dimetric | Clean edges, standard tooling, the entire genre's conventions apply |
| Pre-rendered 3D sprites (no hand pixeling) | true isometric or trimetric | Renderer doesn't care about pixel stepping; pick the best-looking angle |
| One flat decorated wall + floor (companion app) | oblique/flat hybrid | Cheapest art, no per-direction furniture, still reads as a room |
| Free camera rotation | none of these — go real 3D | Axonometric sprite sets lock you to fixed view angles (usually 1 or 4) |

> ⚠️ **Pitfall** — Do not pick a projection by aesthetics alone. The projection determines your art budget multiplier: a character in a side-view game needs 1-2 facing directions; in 2:1 isometric it needs 4-8 (Section 13); with camera rotation in a pre-rendered iso game (RollerCoaster Tycoon) every *building* needs 4 rotations too. Projection choice is a production decision first and an art decision second.

### 2.6 Angle and ratio cheat sheet

Numbers you will reach for constantly when auditing art or debugging transforms:

| Quantity | True isometric | 2:1 dimetric | Notes |
|---|---|---|---|
| Ground-axis screen angle | 30° | 26.565° (arctan ½) | measured from horizontal |
| Ground-edge slope | 1 : 1.732 (1/√3) | **1 : 2 exactly** | rise : run in pixels |
| Diamond aspect (W : H) | 1.732 : 1 | **2 : 1 exactly** | bounding box of a floor tile |
| Axis foreshortening | ≈ 0.8165 all axes | ground ≈ 0.8944, vertical differs | rarely needed in 2D work |
| Pixel step pattern | irregular (2,2,1,2,2,1…) | regular (2,2,2,…) | why 2:1 wins (§17.1) |
| Angle between ground axes on screen | 120° | ≈ 126.87° | 180° − 2·26.565° |
| Common tile sizes | n/a (pre-rendered) | 32×16, 64×32, 128×64, 256×128 | §4.4 |

Two derived identities worth memorizing for 2:1 worlds: one tile step moves `(±W/2, ±H/2) = (±2, ±1)·(H/2)` pixels on screen, and one full tile of "screen vertical" travel (`(1,1)` in tile space) covers `H` pixels — half the `W` pixels that the equivalent horizontal travel `(1,-1)` covers. That 2:1 anisotropy reappears in movement speed (§12.2), shake design (§16.4), and path smoothing.

---

## 3. Projection math — deriving the transforms

This section derives the cartesian↔isometric transforms from first principles, states them as 2×2 matrices, and packages them into a production-grade static helper class. The derivation matters: if you memorize only the final formulas you will be helpless the moment your project uses a non-standard tile size, a staggered layout, or an elevation offset.

### 3.1 Setting up the problem

We have a logical grid where a tile is addressed as `(tx, ty)` — integers, with `tx` increasing "east" and `ty` increasing "south" in plan view. We want a screen position for each tile such that:

- moving one tile in `+tx` moves the sprite **right and down** on screen (down-right diamond edge);
- moving one tile in `+ty` moves the sprite **left and down** on screen (down-left diamond edge);
- the whole grid forms the familiar diamond.

With a tile diamond of pixel size `W × H` (e.g. 64×32), one step along `+tx` must displace the sprite by `(+W/2, +H/2)` and one step along `+ty` by `(−W/2, +H/2)`:

```
                     screen x →
   screen y   (0,0)tile
      ↓          ◇
               ◇   ◇            +tx step: right W/2, down H/2
             ◇   ◇   ◇          +ty step: left  W/2, down H/2
           (0,3)◇  (3,0)
             ◇   ◇   ◇
               ◇   ◇
                 ◇
               (3,3)
```

### 3.2 The forward transform (cart → iso) as a matrix

Because each screen coordinate is a *linear combination* of `tx` and `ty`, the mapping is a matrix multiplication:

```
⎡ sx ⎤   ⎡  W/2   −W/2 ⎤ ⎡ tx ⎤
⎢    ⎥ = ⎢              ⎥ ⎢    ⎥
⎣ sy ⎦   ⎣  H/2    H/2 ⎦ ⎣ ty ⎦
```

Written out:

```
sx = (tx − ty) · (W / 2)
sy = (tx + ty) · (H / 2)
```

Sanity checks (with W=64, H=32):

| Tile (tx, ty) | sx | sy | Where |
|---|---|---|---|
| (0, 0) | 0 | 0 | origin, top of diamond |
| (1, 0) | 32 | 16 | one step down-right |
| (0, 1) | −32 | 16 | one step down-left |
| (1, 1) | 0 | 32 | straight down (one full tile height) |
| (3, 0) | 96 | 48 | right edge of a 4×4 map |
| (0, 3) | −96 | 48 | left edge |
| (3, 3) | 0 | 96 | bottom of diamond |

Note two structural facts you will reuse constantly:

1. **`sx` depends on the difference `tx − ty`; `sy` depends on the sum `tx + ty`.** The sum `tx + ty` is the "depth row" of a tile — every tile on the same down-diagonal shares one `sy` band, which is exactly why depth formulas in Section 8 are functions of `x + y`.
2. **The matrix is a rotation by 45° composed with a non-uniform scale.** Rotating the square grid 45° puts tiles in diamond orientation; scaling y by `H/W` (0.5 for 2:1 tiles) squashes it into the dimetric view. That is the entire "3D engine".

### 3.3 The inverse transform (iso → cart)

To go from screen back to tile space — needed for mouse picking — invert the matrix. For a 2×2 matrix `[[a, b], [c, d]]` the inverse is `1/(ad − bc) · [[d, −b], [−c, a]]`. Here `a = W/2, b = −W/2, c = H/2, d = H/2`, so the determinant is:

```
det = (W/2)(H/2) − (−W/2)(H/2) = WH/2
```

The determinant is nonzero for any real tile size, so the projection is always invertible — every screen point maps to exactly one (fractional) tile coordinate. The inverse works out to:

```
⎡ tx ⎤   ⎡  1/W    1/H ⎤ ⎡ sx ⎤
⎢    ⎥ = ⎢             ⎥ ⎢    ⎥
⎣ ty ⎦   ⎣ −1/W    1/H ⎦ ⎣ sy ⎦
```

Written out:

```
tx = sx / W + sy / H          e.g. tx = (sx/32 + sy/16) / 2   for 64×32… 
ty = sy / H − sx / W               (equivalently, using half-sizes:)

tx = (sx / (W/2) + sy / (H/2)) / 2
ty = (sy / (H/2) − sx / (W/2)) / 2
```

Both spellings are algebraically identical; the half-size form appears more often in tutorials, the full-size form has fewer divisions. Verify against the table above: screen (32, 16) → tx = 32/64 + 16/32 = 0.5 + 0.5 = 1, ty = 16/32 − 32/64 = 0. Correct: tile (1, 0).

The result is *fractional*: screen point (16, 8) yields (0.5, 0.0) — halfway along the top-right edge of tile (0,0). Picking (Section 5) decides how to round; the raw transform must never round, because sub-tile precision is exactly what smooth movement and placement previews need.

### 3.4 A production helper — `IsoProjection` static class

GDScript 2.0 supports static functions and static variables on named classes, which is the right home for pure math with no scene-tree dependencies:

```gdscript
# iso_projection.gd
## Pure cart↔iso math. No nodes, no state per instance — safe to call
## from anywhere, including editor tools (@tool scripts) and unit tests.
class_name IsoProjection
extends RefCounted

## Diamond size of one floor tile in pixels. 2:1 ratio expected.
const TILE_W: float = 64.0
const TILE_H: float = 32.0

## Tile (may be fractional) → screen-space position of the tile's
## diamond CENTER TOP vertex projected point (the map origin anchor).
static func tile_to_screen(tile: Vector2) -> Vector2:
    return Vector2(
        (tile.x - tile.y) * (TILE_W * 0.5),
        (tile.x + tile.y) * (TILE_H * 0.5),
    )

## Screen-space position → fractional tile coordinates.
static func screen_to_tile(screen: Vector2) -> Vector2:
    return Vector2(
        screen.x / TILE_W + screen.y / TILE_H,
        screen.y / TILE_H - screen.x / TILE_W,
    )

## Screen-space position → the integer tile containing it.
static func screen_to_cell(screen: Vector2) -> Vector2i:
    var t := screen_to_tile(screen)
    return Vector2i(floori(t.x), floori(t.y))

## Convenience: center of a cell in screen space (for sprite placement).
static func cell_center(cell: Vector2i) -> Vector2:
    return tile_to_screen(Vector2(cell) + Vector2(0.5, 0.5))
```

Design notes:

- **`class_name` + `static func`** makes call sites read like math: `IsoProjection.tile_to_screen(Vector2(3, 5))`. No autoload needed; statics involve no instance.
- **`Vector2` in, `Vector2` out** for the raw transforms; `Vector2i` only at the cell boundary. The typed signatures document which functions are exact and which quantize.
- **`floori`, not `roundi`**, converts fractional tiles to cells. `floori(t.x)` assigns each point to the diamond whose *top vertex* row/column bracket it; rounding instead shifts every boundary by half a tile and is the classic source of "picking is off by one tile on two edges" bugs. (Section 5 refines this further for pixel-perfect diamond picking.)
- Constants are `const`, so the compiler folds them; if your project needs runtime-configurable tile sizes, promote them to `static var` and inject them at boot.

> ✅ **Best practice** — Unit-test the transforms as pure functions before any scene exists. A five-line test that asserts `screen_to_tile(tile_to_screen(v)) == v` for a handful of vectors (including negatives) catches sign errors that would otherwise surface as "everything mirrors when I walk north", hours later and three systems away.

```gdscript
# test_iso_projection.gd — run with a GUT/GdUnit4 harness or a tool script
static func run() -> void:
    for v: Vector2 in [Vector2.ZERO, Vector2(1, 0), Vector2(0, 1),
            Vector2(7, 3), Vector2(-2, 5), Vector2(0.25, 9.75)]:
        var round_trip := IsoProjection.screen_to_tile(
                IsoProjection.tile_to_screen(v))
        assert(round_trip.is_equal_approx(v),
                "round trip failed for %s -> %s" % [v, round_trip])
```

### 3.5 Where Godot does this for you — and where it doesn't

`TileMapLayer` implements exactly these transforms internally: `map_to_local()` is our `tile_to_screen` (returning the tile *center*), `local_to_map()` is our `screen_to_cell`, both parameterized by the TileSet's `tile_size`, `tile_shape` and `tile_layout` (Section 10). When your world is a TileMapLayer, prefer the node's methods — they respect the layer's transform and every layout variant.

You still need your own `IsoProjection` when:

- entities move *between* tiles and you need fractional tile coordinates (TileMapLayer's `local_to_map` quantizes);
- you build the world without TileMapLayer (Relax Room's approach, Section 11);
- game logic (server code, tests, headless simulation) must run without a scene tree;
- you implement elevation (Section 6), which TileMapLayer's flat transforms know nothing about.

> ⚠️ **Pitfall** — `map_to_local()` returns positions in the **TileMapLayer's local space**. If the layer node is itself translated, scaled, or nested under a moving parent, convert with `tile_layer.to_global(...)` before comparing against global positions such as `get_global_mouse_position()`. Mixing local and global spaces produces offsets that look like projection-math bugs but aren't.

### 3.6 The transform as a `Transform2D` — letting the node tree project for you

Section 3.2 observed that the forward matrix is "rotate 45°, squash y". Godot can express that matrix *as a node transform*, because `Transform2D` is precisely a 2×2 basis plus origin. Set a container node's transform to the projection and everything parented under it can be positioned in **raw tile coordinates** — the renderer projects on the way to the screen:

```gdscript
# iso_container.gd — children use tile coords as their `position`
extends Node2D

func _ready() -> void:
    # Basis columns = images of the tile-space unit vectors (§3.2):
    transform = Transform2D(
        Vector2(IsoProjection.TILE_W * 0.5, IsoProjection.TILE_H * 0.5),  # x axis
        Vector2(-IsoProjection.TILE_W * 0.5, IsoProjection.TILE_H * 0.5), # y axis
        Vector2.ZERO,                                                     # origin
    )

# Elsewhere: a marker at tile (3, 5), no explicit projection call:
#   $IsoContainer/Marker.position = Vector2(3, 5)
```

This trick is powerful and sharp-edged in equal measure:

- **Great for**: debug overlays (draw grid lines, path previews, and region highlights with plain `draw_line(Vector2(x, 0), Vector2(x, h))` calls in tile space — the transform bends them into diamonds); placement ghosts; quickly projecting entire generated layouts.
- **Dangerous for sprites**: the basis has non-uniform scale-with-shear, so child *textures* are also distorted by it — sprites parented inside get squashed. Use it for vector drawing and positioning of otherwise-unscaled markers (or counter-transform the visuals), not as a general scene container.
- **Physics dislikes it**: collision shapes under sheared transforms behave unreliably; keep physics bodies outside such containers.

The practical middle path used by most projects: keep `IsoProjection` (explicit math) for gameplay entities, and reserve the `Transform2D` container for debug/editor visualization where its one-liner drawing pays off daily. Either way, understanding that *the projection is literally a `Transform2D`* demystifies both: `IsoProjection.tile_to_screen(v)` and `iso_container.transform * v` compute the same product `B·v`, with `basis_xform` / `affine_inverse()` available when you want Godot to run the §3.3 inversion for you.

---

## 4. Coordinate spaces — tile, world, screen

Real projects juggle not two but three coordinate spaces, and most "isometric math is broken" reports are actually confusion about which space a value lives in. Name them explicitly and write the conversion functions once.

### 4.1 The three spaces

```
┌──────────────────────────────────────────────────────────────────────┐
│ TILE SPACE          Vector2i / Vector2 (fractional)                  │
│   Integer grid addresses. Pathfinding, occupancy, save data.         │
│   Unit: 1 tile.                                                      │
└───────────────┬──────────────────────────────────────────────────────┘
                │  IsoProjection.tile_to_screen()  /  map_to_local()
┌───────────────▼──────────────────────────────────────────────────────┐
│ WORLD SPACE         Vector2 (pixels)                                 │
│   Godot's 2D global space: Node2D.global_position lives here.        │
│   Sprites, physics bodies, Area2D, NavigationAgent2D all use it.     │
│   Unit: 1 pixel at zoom 1.                                           │
└───────────────┬──────────────────────────────────────────────────────┘
                │  Camera2D transform (get_canvas_transform())
┌───────────────▼──────────────────────────────────────────────────────┐
│ SCREEN SPACE        Vector2 (pixels on the viewport)                 │
│   What InputEventMouse gives you in event.position.                  │
│   Affected by camera position, zoom, and viewport stretch.           │
│   Unit: 1 window pixel.                                              │
└──────────────────────────────────────────────────────────────────────┘
```

The rookie mistake is converting *mouse screen position* directly with `screen_to_tile()`. That works only while the camera sits at the origin with zoom 1. The correct chain is screen → world → tile, and Godot gives you the screen→world step for free:

```gdscript
# Inside any CanvasItem-derived node:
var world_pos := get_global_mouse_position()   # screen→world handled by Godot
var cell := IsoProjection.screen_to_cell(world_pos - map_origin)
```

`get_global_mouse_position()` applies the inverse canvas transform (camera pan, zoom, viewport stretch) for you. `map_origin` is the world position of tile (0,0) — keep it as a single exported `Vector2` on your map node rather than baking it into the math.

### 4.2 Choosing the map origin

Where should tile (0,0) sit on screen? Two conventions dominate:

```
ORIGIN AT TOP VERTEX               ORIGIN AT MAP CENTER
(0,0) at the top of the diamond    (0,0) in the middle

        ◇ (0,0)                          ◇
      ◇   ◇                            ◇   ◇
    ◇   ◇   ◇                        ◇  (0,0) ◇     negative tile
      ◇   ◇                            ◇   ◇        coords exist
        ◇                                ◇
Simple bounds math                 Symmetric scrolling, but every
(0..w-1, 0..h-1)                   loop needs -w/2..w/2 ranges
```

Prefer the **top-vertex origin with non-negative tile coordinates**. `AStarGrid2D.region` (Section 14), 2D arrays, and `Rect2i` bounds all become simpler, and `Vector2i` keys hash cleanly in dictionaries. Center the *node* on screen by translating `map_origin`, not by shifting tile numbering.

> ✅ **Best practice** — Write the origin decision down (a comment block in `IsoProjection` is enough): which tile is (0,0), which way each axis runs on screen, and where the map node sits. Every joining teammate re-derives these three facts painfully from behavior otherwise, and every future system (saves §4.5, pathfinding §14, editor tools) silently depends on them.

### 4.3 Diamond vs staggered layouts

There are two ways to linearize an isometric grid, and they change both the transforms and the neighbor rules:

```
DIAMOND (a.k.a. "rhombus")            STAGGERED (offset rows)

        (0,0)                          (0,0) (1,0) (2,0) (3,0)
      (0,1) (1,0)                         (0,1) (1,1) (2,1)
    (0,2) (1,1) (2,0)                  (0,2) (1,2) (2,2) (3,2)
      (1,2) (2,1)                         (0,3) (1,3) (2,3)
        (2,2)
                                       Rows alternate a half-tile
  Axes run along diamond edges.        x-offset. The MAP is a
  The MAP is diamond-shaped for        rectangle on screen — good
  rectangular tile ranges.             for screen-filling worlds.
  Neighbors are uniform:               Neighbors DEPEND ON ROW
  (±1,0),(0,±1) always.                PARITY — even and odd rows
                                       have different neighbor
  Used by: Age of Empires,             offsets. Used by: Civilization II,
  Diablo, most engines' default        many strategy titles
```

Everything derived in Section 3 is the diamond layout. Staggered maps trade uniform math for a rectangular silhouette; their picking and pathfinding need parity-aware neighbor tables (the same complication hex grids have). Godot's `TileSet` supports both families: `tile_layout = TILE_LAYOUT_DIAMOND_RIGHT` / `TILE_LAYOUT_DIAMOND_DOWN` for diamond, `TILE_LAYOUT_STACKED` / `TILE_LAYOUT_STACKED_OFFSET` for staggered, plus `TILE_LAYOUT_STAIRS_RIGHT` / `TILE_LAYOUT_STAIRS_DOWN` variants (Section 10).

> ✅ **Best practice** — Unless you specifically need a rectangular world silhouette (e.g. a screen-filling strategic map), use the diamond layout. Uniform neighbor offsets simplify pathfinding, flood fills, range queries, and every algorithm you will ever port from an article.

### 4.4 Standard tile sizes

All 2:1, all powers of two wide — atlas packing and mipmap-free scaling both prefer it:

| Size (W×H) | Pixels per tile | Typical use | Examples |
|---|---|---|---|
| 32×16 | 512 | retro/mobile, huge maps | classic-era strategy, Habbo-likes |
| 64×32 | 2,048 | **the indie standard** | most modern pixel iso games |
| 128×64 | 8,192 | detailed pixel art | modern "HD pixel" titles |
| 256×128 | 32,768 | painterly/pre-rendered | late-90s big-budget iso, HD remasters |

Larger tiles mean fewer tiles on screen (cheaper sorting, costlier art), and the tile size fixes your whole scale system: a 64×32 floor tile implies roughly a 1-meter grid square, so a human character sprite should stand about 1.5-2 tile-heights tall (48-64 px) to read as human-scale. Decide the tile size before commissioning a single sprite.

### 4.5 Persisting tile coordinates

Because tile space is the source of truth (§1), it is also what you *save*. Three rules keep saves robust across art and layout changes:

```gdscript
# Serializing a placed decoration — save LOGIC, derive VISUALS on load:
func to_save_dict(deco: Decoration) -> Dictionary:
    return {
        "id": deco.item_id,          # catalog key, not a scene path
        "cell": [deco.cell.x, deco.cell.y],   # Vector2i → portable array
        "level": deco.level,         # elevation/storey if applicable (§6)
        "rot": deco.rotation_step,   # 0-3 for 4-rotation objects
    }

func from_save_dict(d: Dictionary) -> void:
    var deco := Catalog.instantiate(StringName(d["id"]))
    deco.cell = Vector2i(d["cell"][0], d["cell"][1])
    deco.position = IsoProjection.cell_center(deco.cell)   # DERIVED
    decorations_node.add_child(deco)
```

1. **Never save projected positions.** A save containing `position: (412, 217)` breaks the day the tile size, map origin, or projection changes; `cell: (6, 3)` survives all three. (Relax Room, being flat, correctly saves positions — its snap grid *is* its logical space; the rule is "save in your logical space", whatever that is.)
2. **Serialize `Vector2i` explicitly.** JSON has no vector types; write `[x, y]` arrays (or `"6,3"` strings) and reconstruct. Binary saves via `var_to_bytes` keep the type but cost human readability — trade deliberately, and see [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md) for the project's serialization stack.
3. **Version the coordinate contract.** If a later migration renumbers the grid (origin move, layout change), a `"format": 2` field plus a load-time migrator is one afternoon; silently reinterpreting old cells under new numbering corrupts every veteran player's room.

---

## 5. Mouse picking and diamond hit-testing

Picking — converting a mouse click into "the player clicked tile (7, 3)" or "the player clicked the lamp" — is the input half of the projection. Done naively it feels *almost* right, which is worse than wrong: players learn they must click slightly above what they want.

### 5.1 Tile picking with the inverse transform

The core is Section 3's inverse transform plus `floori`:

```gdscript
# In the map node (a Node2D at position `map_origin`):
func pick_cell(global_mouse: Vector2) -> Vector2i:
    var local := to_local(global_mouse)          # world → map-local space
    return IsoProjection.screen_to_cell(local)   # exact diamond containment
```

Why does `floori` on the *fractional tile coordinates* give exact diamond containment, with no extra hit-test? Because the inverse transform literally rotates the diamond world back into a square grid — in tile space every tile *is* a unit square, and "which unit square contains this point" is `floor`. The diamond shape only exists in screen space. This is the elegant fact most tutorials miss when they bolt a separate point-in-diamond test onto a rounded transform.

```
SCREEN SPACE (diamonds)          TILE SPACE (after inverse transform)

       ◇  ◇  ◇                    ┌──┬──┬──┐
      ◇  ◇▪ ◇  ◇      inverse     │  │  │  │
       ◇  ◇  ◇       ─────────►   ├──┼▪─┼──┤     ▪ = mouse point
        ◇  ◇                      │  │  │  │     floor() → cell
                                  └──┴──┴──┘
```

The "mouse map" / color-mask technique found in older tutorials (sampling a red/green/blue diamond-quadrant bitmap to correct a rectangular pick) solves the same problem the slow, art-dependent way. With the exact inverse transform it is obsolete — skip it.

### 5.2 When you DO need an explicit diamond test

An explicit point-in-diamond test earns its keep when the clickable shape is a *single* diamond detached from any grid — a UI minimap cell, a floor highlight, a drop target. Use the L1 (Manhattan) norm: a 2:1 diamond centered at `c` with width `W`, height `H` contains point `p` iff

```
|dx| / (W/2) + |dy| / (H/2) ≤ 1        where d = p − c
```

```gdscript
static func point_in_diamond(p: Vector2, center: Vector2,
        w: float, h: float) -> bool:
    var d := (p - center).abs()
    return d.x / (w * 0.5) + d.y / (h * 0.5) <= 1.0
```

This is exact, allocation-free, and branchless — preferable to building a `Polygon2D` and calling `Geometry2D.is_point_in_polygon()` for a shape this simple (that function is the right tool for *irregular* click regions).

### 5.3 Picking objects, not tiles

For decorations, characters and anything with a silhouette taller than the floor diamond, tile picking is the wrong granularity — a lamp occupies one floor cell but its sprite towers three cells "up" the screen. Two production approaches:

**Physics picking (recommended default).** Give each object an `Area2D` with a `CollisionPolygon2D` matched to its visual silhouette, and let Godot route input:

```gdscript
# decoration.gd
extends Area2D

signal clicked(decoration: Area2D)

func _ready() -> void:
    input_pickable = true
    input_event.connect(_on_input_event)

func _on_input_event(_viewport: Node, event: InputEvent, _shape_idx: int) -> void:
    if event is InputEventMouseButton \
            and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
        clicked.emit(self)
```

Godot delivers `input_event` **topmost-first** among overlapping pickable areas, which usually matches visual stacking; call `get_viewport().set_input_as_handled()` in the top receiver to stop the event from reaching objects behind it.

**Manual reverse-paint picking.** Iterate pickable objects in *reverse draw order* (front-most first) and test the click against each silhouette; first hit wins. You need this when picking must respect pixel-perfect transparency (query the sprite's `Texture2D` → `get_image().get_pixelv()` alpha at the click point, with the image cached — `get_image()` fetches from GPU memory and is far too slow to call per click without caching) or when objects aren't physics nodes at all.

**Relax Room case study.** Decorations in Relax Room are draggable `Area2D` nodes; the drop logic converts the release position through `Helpers.snap_to_grid()` (an 8-pixel snap, Section 11) instead of a diamond transform, because its rooms are flat. The pattern — pickable areas, topmost-first input, snap on release — transfers unchanged to a true isometric room; only the snap function body would swap to `IsoProjection.cell_center(pick_cell(pos))`.

> ⚠️ **Pitfall** — Never pick tiles by iterating all cells and testing `point_in_diamond` per cell. It is O(cells) per click versus O(1) for the inverse transform, and at 128×128 tiles the difference is a frame hitch on every click. The inverse transform *is* the hit test.

### 5.4 Hover highlight — the standard feedback loop

Every iso builder shows a diamond cursor under the mouse. The implementation is the picking pipeline run per-frame, feeding a single highlight sprite:

```gdscript
# tile_cursor.gd — child of the map node
extends Sprite2D   # texture: a 64×32 diamond outline, centered = true

@onready var map: Node2D = get_parent()

func _process(_delta: float) -> void:
    var cell := map.pick_cell(get_global_mouse_position())
    visible = map.is_valid_cell(cell)
    if visible:
        position = IsoProjection.cell_center(cell)
```

Because the highlight is *derived from the same function* that placement/selection uses, cursor and click can never disagree — a small architectural choice that eliminates an entire class of "the outline said this tile but it placed on that one" bugs.

### 5.5 Placement ghosts — the full drag-preview pipeline

Decoration and building games extend the hover cursor into a **ghost**: a translucent copy of the object being placed, snapped live to the pick result and tinted by validity. The pipeline generalizes Relax Room's drop flow (§11) and every builder in Section 19:

```gdscript
# placement_ghost.gd — active while the player is placing an object
extends Node2D

@export var map: Node2D                      # pick_cell / is_valid_cell provider
@export var occupancy: Occupancy             # your occupancy service
var item: DecorationDef                      # footprint, texture, zone rules
@onready var preview: Sprite2D = $Preview

const TINT_OK := Color(0.6, 1.0, 0.6, 0.55)
const TINT_BAD := Color(1.0, 0.5, 0.5, 0.55)

func _process(_delta: float) -> void:
    var cell := map.pick_cell(get_global_mouse_position())
    var valid := map.is_valid_cell(cell) \
            and occupancy.footprint_free(cell, item.footprint) \
            and item.zone_allows(cell)
    position = IsoProjection.cell_center(cell)
    preview.modulate = TINT_OK if valid else TINT_BAD
    set_meta(&"valid", valid)                # read by the confirm handler

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.pressed \
            and event.button_index == MOUSE_BUTTON_LEFT \
            and get_meta(&"valid", false):
        occupancy.claim(map.pick_cell(get_global_mouse_position()),
                item.footprint)
        placed.emit(item)
        get_viewport().set_input_as_handled()

signal placed(item: DecorationDef)
```

Design points that make ghosts feel professional:

- **The ghost is not the real object.** It is a throwaway preview node; the real scene is instantiated only on confirmed placement. This keeps "escape cancels" trivial and prevents half-configured objects leaking into saves.
- **Validity is computed from the same services** (occupancy, zone rules) that the confirm path uses — the §5.4 no-disagreement principle again, now for rules instead of geometry.
- **Render the ghost above the sorted band** (`z_index` above the world) so it never interleaves with existing furniture while previewing — a ghost half-hidden behind a sofa is unreadable.
- **Show the footprint, not just the sprite**: for multi-tile items, draw the claimed diamonds (a second, tile-space visualization — the §3.6 container trick shines here) so players see *why* a spot is invalid.

---

## 6. Faking elevation — the z axis that isn't there

Isometric worlds routinely show height — raised platforms, table tops, flying characters, terrain cliffs — despite having no third dimension. The trick is a single rule:

> **Elevation is a pure screen-space y-offset.** A point at logical height `z` renders exactly `z · ELEVATION_STEP` pixels higher than the same point at ground level. Nothing else changes: not `sx`, not the tile it logically occupies, not its depth-sort key.

### 6.1 The extended transform

Extend the forward transform with a third input:

```
sx = (tx − ty) · W/2
sy = (tx + ty) · H/2 − z · STEP        STEP is commonly H/2 or H
```

```gdscript
## Extended: tile + elevation → screen. z in "elevation units".
const ELEVATION_STEP: float = 16.0   # px per unit; H/2 for 64×32 tiles

static func tile_to_screen_3(tile: Vector2, z: float) -> Vector2:
    var p := tile_to_screen(tile)
    p.y -= z * ELEVATION_STEP
    return p
```

The inverse is now ambiguous — one screen point maps to a whole family of `(tile, z)` pairs, one per elevation. That is not a bug in your math; it is the geometry of the projection:

```
The picking ambiguity:

        ▛▀▀▜   ← top of a z=2 column at tile (3,1)
        ▌  ▐
   ◆────▙▄▄▟────      Screen point ◆ could be:
        ▲              • ground-level tile (2,2), or
        │              • the z=2 SURFACE of tile (3,1)
   same screen         (each +1 z shifts the candidate tile
   pixel               by (+1,+1)·(H/2·…)/… one row "back")
```

Games resolve it with a policy, not more math. Common policies: pick at a fixed reference elevation (builders pick on the ground plane, or on the currently selected "floor level" — SimCity 2000's approach with its level slider); or iterate elevations from highest to lowest, unproject at each `z`, and accept the first candidate whose column actually contains a solid surface at that height (tactics games do this so clicking a cliff top selects the top, not the hidden tile behind it).

### 6.2 Sprites with height vs tiles with height

Distinguish two different "heights" that beginners conflate:

1. **A tall sprite on flat ground** (a lamp, a tree). Logical `z = 0`. The sprite's *texture* simply extends upward from its origin. No elevation math involved — this is entirely an origin-placement matter (Section 7).
2. **An object at raised elevation** (a cat on a table, a unit on a cliff). Logical `z > 0`. Its *render position* gets the `−z · STEP` offset, while its depth sorting and occupancy still use the ground tile it belongs to.

Godot's TileSet has native support for the *drawing* side of case 2: each atlas tile has a `texture_origin` (in `TileData`), so a "raised platform" tile's art can be authored taller than the diamond and offset so its base aligns with the cell. For dynamic entities, apply the offset in code — and keep `z` in a separate field, never folded into `position.y` permanently, or you can no longer recover the ground tile from the position.

```gdscript
# elevated_entity.gd
extends Node2D

var grid_pos: Vector2 = Vector2.ZERO:      # fractional tile coords
    set(v):
        grid_pos = v
        _reproject()
var elevation: float = 0.0:                # logical z, in elevation units
    set(v):
        elevation = v
        _reproject()

func _reproject() -> void:
    position = IsoProjection.tile_to_screen_3(grid_pos, elevation)
```

### 6.3 Shadows sell the height

A y-offset alone reads as "the sprite is further north", not "the sprite is higher" — the projection makes those literally identical. The disambiguating cue used by every isometric game with jumping or flying is a **ground shadow**: a small ellipse rendered at the *ground* projection of the entity (its `z = 0` position) while the body renders at the offset position. The vertical gap between shadow and body is what the eye decodes as height.

```gdscript
# In _reproject(), with a `shadow: Sprite2D` child kept at z = 0:
shadow.global_position = IsoProjection.tile_to_screen_3(grid_pos, 0.0) \
        + shadow_local_offset
```

The shadow, not the body, should also carry the y-sort position (Section 7): sorting by the *ground contact*, wherever the body currently floats, keeps a jumping character correctly layered with the furniture it jumps past.

> ⚠️ **Pitfall** — Implementing a jump by tweening `position.y` directly destroys both picking and sorting, because the node's position no longer corresponds to its ground tile. Always store `(grid_pos, elevation)` as the truth and derive `position`. The moment "where the sprite is drawn" and "where the entity is" become the same variable, elevation bugs multiply.

> ✅ **Best practice** — Pick `ELEVATION_STEP = H/2` so that one elevation unit equals one "tile wall" of height. Then a `z=1` platform tile aligns pixel-perfectly with the diamond of the tile one row behind it, and stacked terrain reads as clean voxel-like steps — the SimCity 2000 / RollerCoaster Tycoon terrain look.

### 6.4 Multi-storey interiors

Elevation's hardest special case is buildings with full floors stacked on one footprint — the upper floor *entirely covers* the lower one in screen space:

```
Level 1:    ┌──────────┐        Both levels project onto overlapping
            │  lofted   │        screen pixels. Showing one hides the
            │  bedroom  │        other; characters exist on both.
            └────┬─────┘
Level 0:    ┌────┴─────┐        Questions a design must answer:
            │  living   │        • what renders when the player is on 0?
            │  room     │        • how do characters change levels?
            └──────────┘        • how does picking know which level?
```

The shipped solutions (all appear in Section 19's catalogue):

1. **Level visibility toggle** — an explicit floor selector shows exactly one level at a time (SimCity 2000's level slider, X-COM's floor buttons, The Sims' floor switcher). Simplest, always correct, and it *also* solves picking: the active level is the picking plane (§6.1's policy). Implementation: one parent node per level; the selector flips `visible` and routes input.
2. **Upper-level transparency** — when the player is on a lower floor, upper floors render at reduced alpha or as outlines. Keeps global context visible; costs a modulate pass per level and careful banding (each level is a `z_index` super-band per §8.2, faded as a unit via a parent's `modulate`).
3. **Cutaway** — remove/roof-off only the portion of upper floors overlapping the camera's focus area. The prettiest and the costliest: needs per-region masking (a `clip_children` mask or shader) and constant tuning.
4. **Separate scenes per floor** — treat each storey as its own room and *transition* between them (stairs are doors). This is the room-based answer (§20) and by far the cheapest correct option for interior-focused games — multi-storey becomes multi-room.

Characters move between levels at **link tiles** (stairs, ladders, elevators): logically an edge connecting `(cell, level)` to `(cell', level+1)` — exactly the special-edge case that motivates graph pathfinding (`AStar2D.connect_points`, §15.1). During the traversal animation, interpolate `elevation` (this section) while the sort band switches at the midpoint — the standard trick so the climber sorts with the departure floor for the first half of the climb and the arrival floor for the second.

**Relax Room note**: the roadmap's "loft bed / split-level room" idea is deliberately option 4 plus a *partial* level — a raised platform within one room (§6.1-6.3 machinery, one extra z band) rather than a true second storey; full multi-storey would arrive as new rooms, never as a floor selector. Scope discipline again: the cheapest structure that delivers the fantasy.

---

## 7. Depth sorting I — y-sort and origin discipline

Depth sorting decides which sprite draws over which. In a 3D engine the depth buffer resolves this per pixel; in 2D you must produce a correct *total order* of sprites and paint back-to-front (the painter's algorithm). This section covers the workhorse — Godot's built-in y-sort — and the discipline that makes it work. Sections 8 and 9 cover the cases y-sort cannot handle.

### 7.1 Why y works as a depth key

Recall from Section 3 that `sy = (tx + ty) · H/2`: screen y is proportional to `tx + ty`, the tile's depth row. An object further "into" the scene (smaller `tx + ty`) always projects higher on screen. So for objects standing on the ground, **screen y at the ground-contact point is a valid depth key** — sort ascending, draw top-of-screen first, and occlusion is correct.

```
     ◇  A (tx+ty = 2)  → smaller sy → drawn FIRST (behind)
    ◇ ◇
   ◇  ◇  B (tx+ty = 4) → larger sy  → drawn LAST (in front)

Painter's algorithm: sort by sy ascending, paint in order.
B's sprite overlaps A's where they intersect → correct occlusion.
```

The load-bearing phrase is *at the ground-contact point*. A sprite's texture extends upward from where the object touches the floor; two objects compare correctly only if each one's sort key is its floor contact, not its texture center or top.

### 7.2 y-sort in Godot 4.5

Y-sorting is a `CanvasItem` property, so it exists on every `Node2D` and `Control`:

```gdscript
# Scene structure for a sorted room:
# Room (Node2D)                 y_sort_enabled = true  ← parent enables sorting
# ├── FloorLayer (TileMapLayer) y_sort_enabled = false (flat floor never sorts)
# ├── Props (Node2D)            y_sort_enabled = true  ← nested sorted group
# │   ├── Plant (Sprite2D)
# │   ├── Desk  (Sprite2D)
# │   └── Lamp  (Sprite2D)
# └── Character (CharacterBody2D)

$Room.y_sort_enabled = true
```

Semantics to know precisely:

- With `y_sort_enabled = true` on a parent, its child `CanvasItem`s render in order of their **global y position** (lowest y first). Children with equal y draw in tree order.
- Y-sorting **nests**: if a y-sorted child is itself y-sorted, its children join the parent's sort pool rather than forming an isolated island. This is how a character (one branch) interleaves with props (another branch) — enable y-sort on *both* the shared parent and the intermediate group nodes.
- The sort key is the node's **origin** (its `position` in global space), not its visual bounding box. Godot does not know where your artwork's "feet" are — you tell it, via origin placement.
- For `TileMapLayer`, enabling `y_sort_enabled` switches the layer from quadrant-batched rendering to per-tile sorted rendering so *individual tiles* can interleave with other nodes; each tile's key can be tuned per-tile via `TileData.y_sort_origin`, plus a whole-layer `y_sort_origin` offset. `x_draw_order_reversed` flips the tie-break direction along x if your art's overlap direction requires it (Section 10).

### 7.3 Origin discipline

The rule that makes all of this work:

> **Every y-sorted sprite's node origin must sit at the object's ground contact point — the lowest point where it meets the floor.** For a diamond-footprint object that is the *front (bottom) corner* of its footprint diamond.

In Godot terms: keep the node's `position` semantically meaningful ("where the object stands") and push the artwork upward using the sprite's own offset, so the texture hangs above the origin:

```gdscript
# Option A — offset on the Sprite2D (art hangs up from the origin):
sprite.centered = false
sprite.offset = Vector2(-texture_w * 0.5, -texture_h + footprint_inset)
# footprint_inset: pixels from the texture's bottom edge up to the
# visual ground-contact line (artists often leave a shadow margin).

# Option B — child arrangement (cleaner for multi-sprite objects):
# Lamp (Node2D)            ← origin at feet; THIS is what y-sort reads
# └── Visual (Sprite2D)    ← position = (0, -art_height/2), centered
```

```
Origin placement, right and wrong:

  WRONG (centered origin)          RIGHT (feet origin)
     ┌────────┐                       ┌────────┐
     │  art   │                       │  art   │
     │   ●    │← origin mid-air       │        │
     │        │  sorts as if the      │        │
     └────────┘  object stood         └───●────┘← origin at feet:
                 half a tile north                 sorts correctly
```

A centered origin makes a tall object sort as if it stood *behind* where it visually stands — the classic symptom is a character's head clipping through a bookshelf they are clearly in front of. Because the error is proportional to half the texture height, it is invisible on short props and glaring on tall ones, which is why it survives playtesting until the artist delivers the wardrobe sprite.

> ✅ **Best practice** — Standardize origin placement in the asset pipeline, not per-scene: decide "all decoration scenes have the root origin at the visual ground contact, artwork offset upward" and encode it in your decoration template scene. Relax Room's decoration scenes follow exactly this contract, which is why its character interleaves correctly with furniture using nothing but `y_sort_enabled` (see [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md)).

### 7.4 What y-sort cannot do

Y-sort produces a correct order only under an assumption: **each object occupies a single ground point, and occlusion between any two objects is decided entirely by their ground y**. The assumption breaks when:

| Breakage | Example | Fix (section) |
|---|---|---|
| Object spans multiple tiles along both axes | 2×3 table, long wall | anchor choice, splitting, topo sort (8, 9) |
| Objects at different elevations overlap | bridge over path | z_index bands per level (8) |
| Sprite art overhangs *below* its ground line | wide-canopy tree | split canopy to overlay sprite (9) |
| Two objects interpenetrate | character *inside* a fountain arch | design it out, or split the arch (9) |
| Flying object | bird over furniture | sort by ground shadow (6), body offset |

Everything in the table shares one root cause: a single scalar (y) cannot encode a partial order that genuinely depends on 2D footprints. When you hit these cases, do not fight y-sort with magic `position` nudges — move deliberately to the tools of the next two sections.

> ⚠️ **Pitfall** — Nudging a sprite's `position.y` by a few pixels to "fix" a sort glitch also *moves the sprite on screen* and changes its collision/pick position. If you need to bias sorting without moving art, that is exactly what `TileData.y_sort_origin` (tiles) or restructured origins (sprites) are for. Position-nudging is how projects end up with furniture that is visually 3 px off its logical tile forever.

---

## 8. Depth sorting II — z_index formulas and topological sorting

When y-sort's single-scalar model fails, you take manual control. Godot gives you a second, coarser ordering channel — `z_index` — and, for the genuinely hard cases, you can compute the order yourself.

### 8.1 The two-channel model

Godot 2D draws canvas items ordered by, in priority:

1. **`z_index`** (int, −4096..4096, optionally `z_as_relative` to accumulate down the tree) — a hard layer number. Higher draws later (on top).
2. Within equal `z_index`: **y-sort order** where enabled, else tree order.

So the production pattern is: *bands via `z_index`, fine order via y-sort within each band*.

```gdscript
# Typical band assignment for an isometric room:
# z_index  content
# ─────────────────────────────────────────────
#  -20     far background (sky, parallax)      ← see window_background.gd
#  -10     floor tiles (never sort)
#   -5     floor decals: rugs, shadows, tile highlights
#    0     THE SORTED WORLD: props, characters (y-sort inside)
#  +10     always-above overlays: ceiling beams, tree canopies
#  +20     room-level VFX (dust, light shafts)
# +100     UI (or better: a CanvasLayer, which is a separate stack)
```

Rugs are the canonical band citizen: a rug lies *on* the floor, every standing object must beat it, yet y-sort would put a rug in front of a chair whose origin is above the rug's origin. Banding (`rug.z_index = -5`) states the invariant directly: rugs never compete with standing objects at all. Relax Room does exactly this for floor mats and shadows.

### 8.2 z_index formulas — z = f(x + y)

Engines without per-node y-sort (and Godot projects that need explicit control, e.g. custom `RenderingServer` canvas items) compute a z_index directly from tile coordinates. From Section 3, depth grows with `tx + ty`, so the base formula is:

```
z = (tx + ty)                        # one band per diagonal row
```

Fold in elevation and a stable tie-break if you need total determinism:

```gdscript
const Z_PER_ROW := 1
const Z_PER_LEVEL := 64        # rows per elevation level, > max map diagonal

static func z_for(cell: Vector2i, level: int = 0) -> int:
    return level * Z_PER_LEVEL + (cell.x + cell.y) * Z_PER_ROW
```

- `level * Z_PER_LEVEL` guarantees that *everything* on floor 1 draws over *everything* on floor 0 — the standard multi-storey solution. Choose `Z_PER_LEVEL` larger than the maximum `tx + ty` on one level so bands can never interleave.
- Stay inside `z_index`'s ±4096 hardware of range: a 64×64 map with 8 levels at these constants peaks at 8·64 + 126 = 638 — fine. A 2048-tile diagonal would not be; at that scale you use y-sort (which has no range limit) or server-side sorting.
- `z_as_relative = true` (default) means a child's effective z is parent z + own z — convenient for moving whole rooms between bands, but remember it when debugging "why is this z=3 node drawing over z=500": its *accumulated* z may differ.

> ✅ **Best practice** — In Godot, prefer `y_sort_enabled` for intra-band ordering and reserve formulas for *band* assignment. The engine's y-sort is C++-side, handles fractional positions natively (no quantization pops when a character crosses a tile boundary), and costs you no per-frame GDScript.

### 8.3 Multi-tile objects and why scalars fail

Now the hard case. A 1×3 wall segment along the x axis, and a character standing beside its middle tile:

```
        Wall occupies (2,1)(3,1)(4,1) — one sprite.
        Character stands at (3,2).

              ◇ (2,1)
            ◇   ◇ (3,1)          Character at (3,2): tx+ty = 5
          ◇   ◇   ◇ (4,1)        Wall anchor candidates:
            ◇   ◇                  front corner (4,1): tx+ty = 5  TIE
              ◇  ← character       middle       (3,1): tx+ty = 4  wall behind
                                   back  corner (2,1): tx+ty = 3  wall behind
```

Whichever single anchor tile you give the wall, there exists a character position for which the resulting order is wrong — when the character stands beside the wall's *far* end, the correct order differs from when they stand beside its *near* end. No scalar key fixes this, because occlusion between extended footprints is not a total order induced by any single number. Your options, in ascending order of effort:

1. **Anchor at the front-most corner** (max `tx + ty` of the footprint) and *accept* the residual artifacts, which for many footprints (especially convex, 2×2-ish ones) never visibly manifest. This is the 90% solution.
2. **Split the object into per-tile sprites** (Section 9) so each column sorts independently — restores correctness at art-pipeline cost.
3. **Topological sorting** — compute the order from pairwise occlusion relations.

### 8.4 Topological sorting — the correct general solution

Instead of a sort *key*, define a pairwise relation: for sprites A and B whose screen bounds overlap, decide "A behind B" from their **footprints** — in tile space, A is behind B if A's footprint lies entirely on the far side of B's near edge (comparisons on min/max of footprint x and y ranges decide this in O(1)). These pairwise edges form a DAG (in sane scenes), and a depth-first traversal emits a valid draw order:

```gdscript
# topo_sort.gd — order sprites by pairwise "behind" relations.
# Each entry: { node: Node2D, fp: Rect2i }  # fp = tile-space footprint

static func is_behind(a: Rect2i, b: Rect2i) -> bool:
    # a entirely on the far side of b along either tile axis?
    if a.position.x + a.size.x - 1 < b.position.x: return true   # a fully west
    if a.position.y + a.size.y - 1 < b.position.y: return true   # a fully north
    return false

static func sorted_draw_order(items: Array[Dictionary]) -> Array[Node2D]:
    var behind: Dictionary = {}            # index -> Array[int] drawn-before
    for i in items.size():
        behind[i] = []
        for j in items.size():
            if i != j and is_behind(items[j]["fp"], items[i]["fp"]):
                behind[i].append(j)        # j must draw before i
    var order: Array[Node2D] = []
    var visited: Array[bool] = []
    visited.resize(items.size())
    for i in items.size():
        _visit(i, items, behind, visited, order)
    return order

static func _visit(i: int, items: Array[Dictionary], behind: Dictionary,
        visited: Array[bool], order: Array[Node2D]) -> void:
    if visited[i]:
        return
    visited[i] = true
    for j: int in behind[i]:
        _visit(j, items, behind, visited, order)
    order.append(items[i]["node"])
```

Apply the resulting order by assigning ascending `z_index` values (or re-ordering children with `move_child`, which changes tree order — valid because tree order breaks z ties). Notes from production use:

- **Cost is O(n²)** in overlap tests; restrict n by only sorting sprites whose *screen AABBs* intersect the dirty region, and only re-sorting when something moves. In a room-scale scene (tens of props) brute force per-frame is still trivially cheap; in a Diablo-scale scene you spatially bucket first.
- **Cycles are possible** with concave/interlocking footprints (three L-shaped sofas arranged in a pinwheel can each be "behind" the next). Real games design them out — footprint rules like "props are rectangles" guarantee acyclicity along each axis. If you cannot, break cycles arbitrarily but *stably* (e.g. by object id) so the glitch at least doesn't flicker.
- This is the technique classic isometric engines (and the well-known 2013 Shaun Inman / Andreas Fredriksson writeups on iso sorting) converge on; it is what "y-sort with origins" approximates for the single-tile case.

### 8.5 Decision guide

```
                     ┌──────────────────────────────┐
                     │ Does every sorted object      │
                     │ stand on ≤ 1 tile (or a      │
                     │ compact ~square footprint)?  │
                     └──────┬────────────┬──────────┘
                        yes │            │ no
                            ▼            ▼
               ┌────────────────┐  ┌───────────────────────────────┐
               │ y_sort_enabled │  │ Can you split it into per-tile │
               │ + origin       │  │ or per-column sprites?         │
               │ discipline     │  └──────┬────────────┬───────────┘
               │ (Section 7)    │     yes │            │ no
               └────────────────┘         ▼            ▼
                              ┌──────────────────┐ ┌──────────────────┐
                              │ split + y-sort   │ │ topological sort │
                              │ (Section 9)      │ │ (this section)   │
                              └──────────────────┘ └──────────────────┘
      Cross-cutting: use z_index BANDS for decals-below and canopies-above
      (8.1), and per-LEVEL bands for multi-storey maps (8.2).
```

---

## 9. Depth sorting III — artifacts, splitting, occlusion

This section is the field guide: the recurring visual artifacts of isometric sorting, what each one means, and the standard fixes — including the two structural techniques every shipped iso game uses, sprite splitting and walk-behind occlusion handling.

### 9.1 Artifact catalogue

| Artifact (what you see) | Diagnosis | Fix |
|---|---|---|
| Character's head clips through furniture they stand in front of | sprite origins not at ground contact | origin discipline (7.3) |
| Character "pops" behind/in front while walking past a prop | correct y-sort, but the *prop's* origin is off; or both origins sit at identical y and tie-breaks flicker | fix prop origin; add deterministic tie-break (x, then instance id) |
| Long wall/fence sorts wrong at one end | multi-tile footprint with single anchor | split per tile, or topo sort (8.3-8.4) |
| Rug draws over shoes | rug competes in the sorted band | move rugs to a lower z_index band (8.1) |
| Tree canopy hides a character standing clearly south of the trunk | canopy art overhangs the footprint | split trunk/canopy; canopy to +band (9.2) |
| Upper-floor furniture appears "inside" ground floor | levels share one band | per-level z bands (8.2) |
| Tiles themselves overlap wrong (terrain cliffs) | tall tiles without per-tile y-sort | `TileMapLayer.y_sort_enabled` + per-tile `y_sort_origin` (10) |
| Flicker between two static props | equal sort keys, unstable order | never rely on incidental order; offset one origin by ≥1px or band them |

### 9.2 Splitting tall and wide sprites

**The problem, concretely.** A tree: 1×1 trunk footprint, but a canopy 3 tiles wide. A character at the tile *south-east of the trunk* should be **in front of the trunk but behind the canopy overhang**. One sprite cannot satisfy both — one draw call is entirely before or after the character.

**The fix.** Author the object as two sprites with different sorting behavior:

```
        ▓▓▓▓▓▓▓▓▓▓▓          canopy → z_index = +10 band (always above
        ▓▓▓▓▓▓▓▓▓▓▓                    ground-level actors), or its own
           ▓▓▓▓▓                       y-sorted node with origin pushed
            ║║║                        far south (its "occlusion line")
            ║║║   ← trunk    trunk  → normal y-sorted sprite,
        ────●────              origin at base
```

The same decomposition solves **arches, doorways, and bridges**: the pillars/deck-front are normal sorted sprites; the span that actors pass *under* goes to an upper band. The general principle:

> **Split along the occlusion boundary.** Whenever one region of an object should occlude actors and another region should not (or should occlude differently), those regions must be separate canvas items. Sorting granularity must match occlusion granularity.

For *wide* multi-tile objects (the 1×3 wall), split into per-tile column sprites, each with its own base origin. In TileMapLayer worlds you get this for free — build long walls out of tiles rather than one placed sprite, and the layer's per-tile sorting handles every case. This is a strong argument for tile-building walls even in otherwise sprite-composed scenes.

Cost accounting: splitting multiplies canvas items (usually irrelevant at room scale; measurable at city scale — see Section 18) and adds an art-pipeline rule ("export trees as trunk + canopy layers"). Aseprite layers make the export nearly free; retrofitting it onto 200 flattened PNGs does not. Decide before mass production of art.

### 9.3 Walk-behind occlusion: seeing the hidden character

When the player walks behind a wall or tall furniture, correct sorting hides them — which is *correct* and *bad UX* simultaneously. The three shipped solutions, in ascending implementation cost:

**1. Transparency-on-overlap.** Detect the character behind an occluder (an `Area2D` matching the occluder's screen silhouette works) and fade the occluder:

```gdscript
# occluder_fade.gd — on the wall/furniture sprite
extends Sprite2D

@onready var reveal_zone: Area2D = $RevealZone

func _ready() -> void:
    reveal_zone.body_entered.connect(_on_zone.bind(true))
    reveal_zone.body_exited.connect(_on_zone.bind(false))

func _on_zone(_body: Node2D, entered: bool) -> void:
    var tween := create_tween()
    tween.tween_property(self, "modulate:a", 0.45 if entered else 1.0, 0.15)
```

Cheap, readable, used by The Sims (whole-wall cutaway modes) and countless indies. Weakness: fading a *shared* wall reveals more than intended.

**2. Silhouette shader.** Draw the character normally, then draw a flat-color silhouette pass with a material whose `z_index` is above occluders, masked so it only shows where the character is covered. In Godot: duplicate sprite with a `CanvasItem` shader (`COLOR = vec4(silhouette_rgb, texture(TEXTURE, UV).a * covered)`), or a screen-reading shader comparing against the occluder band. The Diablo III / Hades approach; crisp UX, moderate shader work — see [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md) for the canvas shader toolkit.

**3. Structural cutaway.** Never draw the near walls at all (rooms are built with only north and west walls visible — the near sides are implied). This is the room-diorama convention: The Sims' "walls down", Habbo's L-shaped rooms, and **Relax Room**, whose room shows only the back wall and floor, making the problem vanish by construction. When your design allows it, the best occlusion code is none.

### 9.4 Debugging draw order

Practical tools when a scene sorts wrong and you cannot see why:

- **Visualize sort keys.** Temporary `Label` children showing each prop's `global_position.y` (the actual key) turn "mystery flicker" into "these two are both 384.0".
- **Draw origin crosses.** A debug overlay drawing a 5-px cross at each sorted node's origin instantly exposes centered-origin offenders — the cross floats mid-sprite instead of at the feet.
- **Freeze and step.** Pause the scene and toggle `visible` on suspects from the remote scene tree; binary-search the pair that actually conflicts rather than guessing among ten overlapping sprites.
- **Check accumulated z.** The remote inspector shows each node's own `z_index`; remember `z_as_relative` accumulation when the effective value seems impossible.

> ⚠️ **Pitfall** — Do not "fix" sorting bugs you cannot reproduce deterministically. Ties broken by scene-tree order will resolve differently after any innocent reorder of children (or a `move_child` elsewhere), so the bug will return wearing a different costume. Every pair of sortable objects must differ in key or band *by design*.

---

## 10. Building isometric worlds with TileMapLayer

Godot 4.5's tile system understands isometric natively. Since Godot 4.3 the scene node is **`TileMapLayer`** — one node per layer (floor, walls, decor), replacing the older multi-layer `TileMap` node, which is deprecated. The projection knowledge lives in the **`TileSet` resource** the layers share; the layers themselves are thin, paintable grids. (Baseline tile mechanics — atlases, terrain sets, physics layers — are covered in [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md); this section covers only what isometric changes.)

### 10.1 Configuring the TileSet for isometric

The four properties that define the projection, with their exact API names:

| TileSet property | Isometric value | Meaning |
|---|---|---|
| `tile_shape` | `TileSet.TILE_SHAPE_ISOMETRIC` | cells are diamonds, not squares |
| `tile_layout` | `TileSet.TILE_LAYOUT_DIAMOND_RIGHT` or `TILE_LAYOUT_DIAMOND_DOWN` | how cell coordinates map onto the diamond field |
| `tile_offset_axis` | `TileSet.TILE_OFFSET_AXIS_HORIZONTAL` (typical) | which axis half-offset rows/columns run along |
| `tile_size` | `Vector2i(64, 32)` (or your 2:1 size) | the diamond's bounding box in pixels |

```gdscript
# Building the tileset in code (usually you do this in the editor):
var ts := TileSet.new()
ts.tile_shape = TileSet.TILE_SHAPE_ISOMETRIC
ts.tile_layout = TileSet.TILE_LAYOUT_DIAMOND_DOWN
ts.tile_offset_axis = TileSet.TILE_OFFSET_AXIS_HORIZONTAL
ts.tile_size = Vector2i(64, 32)

var floor_layer := TileMapLayer.new()
floor_layer.tile_set = ts
add_child(floor_layer)
```

The two diamond layouts differ in where the coordinate axes point on screen:

```
TILE_LAYOUT_DIAMOND_DOWN               TILE_LAYOUT_DIAMOND_RIGHT

        (0,0)                                  (0,0)  (1,0)  (2,0)
     (0,1)  (1,0)                          (0,1)  (1,1)  (2,1)
  (0,2)  (1,1)  (2,0)                  (0,2)  (1,2)  (2,2)
     (1,2)  (2,1)                      x axis runs down-RIGHT along
        (2,2)                          the screen; y axis down-left —
  +x down-right, +y down-left:         the diamond leans rightward.
  matches Section 3's math and
  most tutorials. RECOMMENDED.
```

`TILE_LAYOUT_DIAMOND_DOWN` reproduces exactly the axes this module derived, so all your `IsoProjection` intuition transfers; the stacked/stairs layouts (`TILE_LAYOUT_STACKED`, `TILE_LAYOUT_STACKED_OFFSET`, `TILE_LAYOUT_STAIRS_RIGHT`, `TILE_LAYOUT_STAIRS_DOWN`) produce the staggered families from Section 4.3. Pick one at project start; converting a painted map between layouts renumbers every cell.

> ⚠️ **Pitfall** — `tile_size` is the size of the *cell diamond*, not of your textures. Wall and terrain tiles are routinely taller than the cell (a 64×32 cell with 64×96 wall art). The atlas accommodates this: set the atlas source's texture region per tile, then align the art with the cell using `TileData.texture_origin`. If tall tiles look "sunk into the floor", `texture_origin` is what you forgot.

### 10.2 Painting, and the cell API

Painting works exactly as in orthogonal maps — the editor draws a diamond grid once `tile_shape` is isometric. Programmatic access, verified signatures:

```gdscript
# Write
floor_layer.set_cell(Vector2i(5, 3), source_id, atlas_coords)  # alternative_tile := 0
floor_layer.erase_cell(Vector2i(5, 3))

# Read
var src: int = floor_layer.get_cell_source_id(Vector2i(5, 3))       # -1 if empty
var atlas: Vector2i = floor_layer.get_cell_atlas_coords(Vector2i(5, 3))
var data: TileData = floor_layer.get_cell_tile_data(Vector2i(5, 3)) # null if empty

# Coordinate conversion — the engine's own Section-3 transforms
var local_pos: Vector2 = floor_layer.map_to_local(Vector2i(5, 3))   # cell center
var cell: Vector2i = floor_layer.local_to_map(local_pos)

# Bulk queries
var used: Array[Vector2i] = floor_layer.get_used_cells()
var bounds: Rect2i = floor_layer.get_used_rect()
```

`map_to_local` returns the **center** of the cell in the layer's local space — convenient for placing entities ("stand on tile (5,3)" = `entity.global_position = floor_layer.to_global(floor_layer.map_to_local(cell))`). Remember the local/global distinction from Section 3.5.

### 10.3 Layering an isometric scene

A representative production layer stack:

```
World (Node2D, y_sort_enabled = true)
├── Ground      (TileMapLayer)  y_sort_enabled = false, z_index = -10
│     flat floor diamonds only — never needs sorting; stays quadrant-batched
├── GroundDecal (TileMapLayer)  y_sort_enabled = false, z_index = -5
│     rugs, cracks, tile highlights
├── Walls       (TileMapLayer)  y_sort_enabled = true,  z_index = 0
│     tall tiles that must interleave with actors; per-tile sorting on
├── Props       (Node2D)        y_sort_enabled = true,  z_index = 0
│     scene-instance furniture (multi-tile, interactive)
├── Actors      (Node2D)        y_sort_enabled = true,  z_index = 0
└── Canopy      (TileMapLayer)  y_sort_enabled = false, z_index = +10
      overhangs actors never occlude from below
```

Key facts, per the class reference:

- Setting `y_sort_enabled` on a TileMapLayer makes the layer origin-sort **each tile individually**, allowing tiles to interleave with sibling actors — required for walls/cliffs, wasted cost for flat floors.
- Each tile's sort key can be biased in the TileSet editor via `TileData.y_sort_origin` (per-tile, in pixels), plus the layer-wide `TileMapLayer.y_sort_origin` int. Tall wall tiles typically need their sort origin pushed to the tile's *base*.
- `TileMapLayer.x_draw_order_reversed` (default `false`) flips tie-breaking along x for y-sorted layers — use when your wall art's overlap direction runs the other way (e.g. west-facing walls drawn after east-facing at the same y).
- Per-layer `navigation_enabled` toggles the layer's baked navigation polygons (Section 15).

### 10.4 TileSet custom data — logic painted with the art

TileSet **custom data layers** attach typed metadata to every tile — the bridge from painted art to game logic, and the input for pathfinding costs in Section 14:

```gdscript
# One-time TileSet setup (editor: TileSet panel → Custom Data Layers):
ts.add_custom_data_layer()
ts.set_custom_data_layer_name(0, "walkable")
ts.set_custom_data_layer_type(0, TYPE_BOOL)
ts.add_custom_data_layer()
ts.set_custom_data_layer_name(1, "move_cost")
ts.set_custom_data_layer_type(1, TYPE_FLOAT)

# Then per atlas tile, set values in the TileSet editor. Read at runtime:
func is_walkable(cell: Vector2i) -> bool:
    var data := floor_layer.get_cell_tile_data(cell)
    return data != null and bool(data.get_custom_data("walkable"))
```

> ✅ **Best practice** — Treat custom data as the *single source* of tile semantics. If "walkable" lives in custom data, then level designers control walkability by painting, and your `AStarGrid2D` rebuild (Section 14) reads it — no parallel hand-maintained obstacle lists that drift out of sync with the art.

### 10.5 TileMapLayer vs manual placement vs hybrid

| Criterion | TileMapLayer world | Manual Sprite2D placement | Hybrid |
|---|---|---|---|
| Authoring | paint in editor; terrain autotiling | drag scenes; runtime placement UIs | paint ground, place props |
| Ideal content | floors, walls, terrain, repeated structure | unique furniture, interactive objects, player-placed items | most real games |
| Depth sorting | per-tile, built-in | your discipline (Sections 7-9) | both |
| Physics/nav | baked per-tile in TileSet | per-scene collision shapes | both |
| Runtime mutation | `set_cell` — instant, data-driven | instantiate/free scenes | both |
| Per-object behavior | none (tiles are dumb data) | full scripts, signals, tweens | scripts on props |
| Memory/draw cost | excellent (quadrant batching when unsorted) | fine at room scale, watch at city scale | good |

The decision rule: **structure is tiles, objects are scenes.** Floors, walls, cliffs and anything repeated-and-passive belong in TileMapLayers; anything the player clicks, moves, animates, or saves individually deserves a scene instance.

**The hybrid pattern in practice.** The two halves must agree on three contracts, and each has one canonical answer:

1. *One projection.* Scene props are placed with `map_to_local()` (or an `IsoProjection` configured with the same `tile_size`) so tiles and props share the grid exactly — never eyeball prop positions over a tile floor:

```gdscript
# Spawning a scene prop onto the tile grid it shares with the floor:
func spawn_prop(scene: PackedScene, cell: Vector2i) -> Node2D:
    var prop := scene.instantiate() as Node2D
    prop.position = floor_layer.map_to_local(cell)   # same transform as tiles
    props_node.add_child(prop)                        # y-sorted band (§10.3)
    occupancy.claim(cell, prop.footprint)             # contract 3
    return prop
```

2. *One sort pool.* The wall TileMapLayer (per-tile y-sort) and the props/actors nodes are siblings under one y-sorted parent (§10.3's stack), so a character passes correctly both behind a *painted* wall tile and behind an *instanced* wardrobe in the same walk.
3. *One occupancy authority.* Pathfinding state merges both sources — tile data seeds the grid, placed scenes stamp their footprints:

```gdscript
func rebuild_occupancy() -> void:
    nav.refresh_from_tiles()                 # custom data: walkable, cost (§14.1)
    for prop: Node2D in props_node.get_children():
        for cell: Vector2i in prop.footprint_cells():
            nav.astar.set_point_solid(cell, true)
```

Get the three contracts right and the hybrid is invisible — which is why it is the default architecture of shipped iso games, and the end state of Relax Room's upgrade path (§20.5). Which leads directly to the case study.

### 10.6 Editor workflow notes for isometric maps

Practicalities that save hours in the TileMap editor once `tile_shape` is isometric:

- **Terrain sets work in iso.** Godot's terrain system (autotiling successor — see [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md)) is shape-agnostic: define a terrain for "grass↔dirt" with the diamond-edge peering bits and painting produces correct transitions exactly as in orthogonal maps. Authoring the transition *art* is the hard part — each diamond edge needs its blend tile (§17.2's seam rules apply doubly).
- **Painting feel differs.** Rectangle-fill tools operate in *cell space*, so a "rectangle" of cells is a diamond on screen; for room-shaped floors this is what you want, but expect a mental gear-shift. The editor's grid overlay (View → grid) is essential — enable it before any serious painting session.
- **Preview y-sort in-editor.** `y_sort_enabled` takes effect in the editor viewport too: drop a placeholder character scene beside your wall layer while building and mis-sorted wall tiles reveal themselves immediately, instead of at runtime.
- **Alternative tiles for mirrored props.** The atlas editor can register flipped/transposed *alternative tiles*; a west-facing wall is the east-facing art with `flip_h` as an alternative — halving wall art the same way §13.1 halves character art.
- **Keep one test scene per TileSet** containing a swatch of every tile against a garish background — the fastest way to spot stray semi-transparent edge pixels (§17.3) and `texture_origin` mistakes the moment art is imported.

---

## 11. Manual placement — the Relax Room way (case study)

> 📦 **Case study — Relax Room.** This section documents project-specific architecture from the running case study. The *pattern* (zone-constrained free placement with snapping) generalizes to any decoration game; the constants and file names are Relax Room's own.

Relax Room builds its rooms with **no TileMapLayer at all**: every room is a flat 2D scene, decorations are draggable scene instances, and placement is constrained by zones and an invisible snap grid. This is a legitimate end of the world-building spectrum, chosen deliberately.

### 11.1 The room model

```
Relax Room's room anatomy (window ≈ 1280×720):

┌──────────────────────────────────────────────┐  ─┐
│  WALL ZONE  (top 40% — WALL_ZONE_RATIO 0.4)  │   │ wall_rect
│  [painting]   [clock]   [shelf]   [window]   │   │ (flat ColorRect,
│                                              │   │  theme-tinted)
├──────────────────────────────────────────────┤  ─┤ baseboard line
│  FLOOR ZONE (bottom 60%)                     │   │ floor_rect
│   [desk]   [chair]      [plant]              │   │
│        🧍 character (y-sorted with props)    │   │
│   [rug: z_index band below]     [lamp]       │   │
└──────────────────────────────────────────────┘  ─┘
```

- The **back wall is drawn flat-on** (the oblique/diorama simplification from Section 2.4): wall art needs no diamond perspective, and the walk-behind occlusion problem of Section 9.3 is designed away — there are no near walls.
- **Two placement zones** replace the tile grid's semantic layer: a decoration's catalog entry (`decorations.json`) declares whether it is a wall item or a floor item, and the drop logic rejects drops in the wrong zone. `WALL_ZONE_RATIO = 0.4` is the single constant that splits the room.
- The character is a `CharacterBody2D` that free-moves within the floor zone, sharing one y-sorted parent with the floor decorations — Section 7's machinery, minus the grid.

### 11.2 Snapping without tiles

Instead of `IsoProjection.cell_center(...)`, Relax Room snaps drops to a fine square grid:

```gdscript
# helpers.gd (autoload "Helpers") — the project's snap utility
const GRID_SIZE := 8   # pixels

static func snap_to_grid(pos: Vector2) -> Vector2:
    return Vector2(snappedf(pos.x, GRID_SIZE), snappedf(pos.y, GRID_SIZE))
```

An 8-px snap is coarse enough that placements look intentional and aligned, fine enough that the player never feels fought. This is the key insight of the hidden-grid pattern (Unpacking uses the same trick, Section 19): **players want alignment, not grids**. The snap resolution is a UX dial — 1 px feels like free placement, 8 px feels "assisted", a full 64-px tile feels like a board game.

### 11.3 Overlap prevention

With no occupancy grid, Relax Room prevents furniture stacking geometrically, in `drop_zone.gd`:

```gdscript
# drop_zone.gd — reject drops that would bury an existing decoration
const OVERLAP_THRESHOLD := 0.5   # ≤ 50% mutual overlap allowed

func _has_overlap(new_rect: Rect2) -> bool:
    for deco_data: Dictionary in SaveManager.decorations:
        var existing_rect := _get_decoration_rect(deco_data)
        var intersection := new_rect.intersection(existing_rect)
        if intersection.has_area():
            var overlap_ratio := intersection.get_area() \
                    / minf(new_rect.get_area(), existing_rect.get_area())
            if overlap_ratio > OVERLAP_THRESHOLD:
                return true
    return false
```

Notes on the design: the *ratio against the smaller rect* means a big rug can sit under a small chair (chair covers little of the rug ⇒ but ratio uses the chair — hence the 50% threshold rather than 0), and partial overlaps that read as "beside" are allowed. A tile-occupancy system would express this as "rug is a decal band, chair claims cells"; the geometric version trades exactness for zero grid bookkeeping. At Relax Room's scale (tens of decorations, checked only on drop) the O(n) scan is irrelevant.

### 11.4 What transfers to a true isometric room

The comparison this case study exists to teach — every column already runs in Relax Room today, and the middle column shows the drop-in isometric upgrade:

| Concern | Relax Room today (flat) | Same room, isometric grid | Shared machinery |
|---|---|---|---|
| Placement target | `snap_to_grid(pos)` (8 px) | `cell_center(pick_cell(pos))` | drag/drop UI, ghost preview |
| Valid position | zone check + `_has_overlap` | zone via tile bands + occupancy set | catalog-driven rules from `decorations.json` |
| Depth order | `y_sort_enabled` + rug band | identical + per-tile wall sorting | Sections 7-8 verbatim |
| Persistence | exact `position` saved | `Vector2i` cell saved | `SaveManager` shape unchanged |
| Character | free move in floor polygon | grid/nav movement (12, 14) | same body, same animation sets |

That the right column changes only two function calls in the placement path is the payoff of the boundary discipline preached since Section 1: because Relax Room keeps logic (catalog, save data, rules) separate from presentation (snap function, room art), the projection is swappable. The project's roadmap lists exactly this as a possible evolution — diamond floor via a `TileMapLayer` under the existing decoration system, isometric furniture art, multi-level lofts — none of which would disturb `SaveManager` or the catalog. See [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) for the full component inventory and Section 20 for the room-based design rationale.

---

## 12. Character movement in isometric space

Movement is where players *feel* the projection: get the mapping wrong and walking "up" drifts diagonally; get normalization wrong and diagonal walking is 41% too fast. This section builds the input→velocity pipeline for both flat rooms and true isometric grids.

### 12.1 The input problem

Keyboard input arrives in *screen* axes; an isometric world's natural axes are the *diamond* edges. You must choose what "pressing up" means:

```
   Screen-aligned movement            Iso-aligned movement
   (up = screen north)               (up-key = north-WEST tile axis)

          ▲                                 ↗ (+x tile axis on screen)
          │                               ╱
   ◄──────┼──────►                 ◄────◇────►
          │                               ╲
          ▼                                 ↘ (+y tile axis)

   Feels natural in rooms          Aligns walking with tile edges;
   and free-move games;            standard in grid tactics; feels
   crosses tile edges obliquely    "rotated 45°" to new players
```

Both are shipped conventions. Diablo-likes and free-movement games use screen-aligned (mouse/stick pointing is already screen-space); tile-step tactics games use iso-aligned so a "move north" order lands on the adjacent tile. Decide once, per game.

### 12.2 Screen-aligned movement, done correctly

The baseline — and the home of the most famous bug in 2D movement. Use `Input.get_vector()`, which returns an already length-clamped vector:

```gdscript
# character_controller.gd — screen-aligned, Relax Room style
extends CharacterBody2D

const SPEED := 140.0   # px/s

func _physics_process(_delta: float) -> void:
    var input_dir := Input.get_vector(
            "move_left", "move_right", "move_up", "move_down")
    velocity = input_dir * SPEED
    move_and_slide()
    if input_dir != Vector2.ZERO:
        _update_animation(input_dir)
    else:
        _play_idle()
```

**Why normalization matters — the diagonal speed bug.** Composing raw axes gives `(±1, ±1)` on diagonals, a vector of length √2 ≈ 1.414: diagonal walkers move 41% faster. `Input.get_vector()` clamps the composed vector's length to 1.0 (and applies deadzone handling for analog sticks correctly, per-vector rather than per-axis) — prefer it over hand-rolled `Input.get_axis()` pairs plus `normalized()`, which crushes analog magnitudes (a gentle stick push would still full-speed the character; `get_vector` preserves sub-unit lengths).

**The isometric wrinkle:** even screen-aligned games should decide whether *vertical* screen movement uses the same pixel speed as horizontal. In a 2:1 world, a character crossing one tile north-south covers half the screen pixels of an east-west crossing; using one uniform pixel speed means north-south travel is twice as fast *in tiles*. Purist fix: scale `velocity.y` by 0.5 so tile-space speed is uniform (many classic iso games do); pragmatic fix: ignore it in room-scale games where players never count tiles. Relax Room ignores it — the room is one screen and uniform pixel speed simply feels right. Know that you are choosing.

### 12.3 Iso-aligned movement

To align movement with the diamond axes, feed the input vector through the *direction part* of Section 3's forward matrix — i.e. treat input as tile-space direction and project it:

```gdscript
## Screen-space unit velocity for a tile-space direction.
## Column vectors of the forward matrix, normalized: (2,1)/√5 and (−2,1)/√5.
static func iso_direction(input_dir: Vector2) -> Vector2:
    if input_dir == Vector2.ZERO:
        return Vector2.ZERO
    var screen_dir := Vector2(
        (input_dir.x - input_dir.y) * 2.0,   # W/2 : H/2 = 2 : 1
        (input_dir.x + input_dir.y) * 1.0,
    )
    return screen_dir.normalized() * minf(input_dir.length(), 1.0)
```

Now "right" walks down-the-right-diamond-edge, "up" walks up-the-left-edge, and diagonal *inputs* walk pure screen north/east/south/west (the sums/differences of the two edge vectors). Movement visually hugs tile rows — the Age-of-Empires feel. The same matrix trick applies to any world-space vector you need on screen: knockback impulses, projectile velocities, wind particles.

### 12.4 Grid-stepped movement

Tactics and puzzle games move in whole-tile steps instead of free velocity. The pattern: logical position is a cell; the visual node tweens between projected cell centers; input queues the next step. This is also the foundation the pathfinding sections build on (a path is just a queue of steps):

```gdscript
# grid_walker.gd
extends Node2D

const STEP_TIME := 0.22
var cell: Vector2i = Vector2i.ZERO
var _moving := false

func try_step(delta_cell: Vector2i) -> void:
    if _moving:
        return
    var target := cell + delta_cell
    if not WorldGrid.is_walkable(target):      # your occupancy service
        return
    _moving = true
    cell = target                              # logic commits IMMEDIATELY
    var tween := create_tween()
    tween.tween_property(self, "position",
            IsoProjection.cell_center(cell), STEP_TIME)
    tween.finished.connect(func() -> void: _moving = false)
```

Committing `cell` at step *start* (not at tween end) is deliberate: game logic (occupancy, interactions, save) sees the character on the destination tile for the whole step, so two entities can never claim one tile by racing mid-tween.

> ⚠️ **Pitfall** — Physics interpolation: if your project enables 2D physics interpolation, avoid mixing tween-driven `position` writes on physics bodies with `move_and_slide()` movement elsewhere in the same actor; pick one movement authority per node. Symptoms of mixing: rubber-banding at step ends and doubled footstep events.

### 12.5 Collision setup in a fake-3D world

`CharacterBody2D` collision shapes must match the *floor plan*, not the sprite:

```
   Sprite (tall)              Collision (feet only)
   ┌──────────┐
   │   head   │               The collision shape is a small
   │   body   │               ellipse/capsule at the FEET:
   │          │                        ╭────╮
   └────╥─────┘                        ╰────╯  ← at origin
        ╨  ← origin/feet
```

A full-sprite collision box would collide the character's *head* with furniture that is merely *behind* them on screen. In iso, collision is a plan-view problem: feet ellipse vs furniture footprint rectangles/diamonds. Give furniture `StaticBody2D` shapes matching their floor footprint only, never their visual silhouette. (Relax Room: the character's capsule sits at the feet; room bounds are `StaticBody2D` walls at the floor-zone edges.)

### 12.6 Footstep alignment — grounding characters in the grid

Footsteps are the cheapest, highest-yield polish in an isometric game: sounds, dust puffs and prints that align with the *tiles* make the grid feel physical. The pipeline has two halves — *when* a step happens, and *where* its effect spawns.

**When: drive events from animation, never from timers.** A step occurs on the walk cycle's contact frames (typically 2 per loop). Timers drift against animation speed changes; frame-driven events cannot:

```gdscript
# On AnimatedSprite2D — contact frames known per animation:
const CONTACT_FRAMES := { &"walk_down": [1, 5], &"walk_side": [2, 6] }

func _ready() -> void:
    sprite.frame_changed.connect(_on_frame)

func _on_frame() -> void:
    var contacts: Array = CONTACT_FRAMES.get(sprite.animation, [])
    if sprite.frame in contacts:
        _emit_footstep()
```

(With `AnimationPlayer` instead, a *method call track* keyed on contact frames calls `_emit_footstep()` directly — more editor-friendly, same result.)

**Where: spawn on the logical grid, pick surface from tile data.** Convert the character's position to its cell, center the print, and let the tile's custom data choose the sound set:

```gdscript
func _emit_footstep() -> void:
    var cell := IsoProjection.screen_to_cell(global_position - map.global_position)
    var data := map.floor_layer.get_cell_tile_data(cell)
    var surface := StringName(data.get_custom_data("surface")) \
            if data else &"default"                    # wood / stone / rug…
    AudioBus.play_footstep(surface)                    # your audio service
    var print := FOOT_PRINT_SCENE.instantiate()
    print.position = IsoProjection.cell_center(cell)   # tile-centered decal
    print.z_index = -5                                 # decal band (§8.1)
    map.add_child(print)
```

The `surface` custom data layer (§10.4) is the same mechanism as `walkable`/`move_cost` — one more painted property, and every future tile automatically sounds right. Prints and dust go to the decal band below the sorted world so they never fight actors for order. In Relax Room the equivalent is simpler but identical in spirit: footstep audio switches between wood and rug based on whether the character's feet position falls inside a rug decoration's rect — surface-aware feedback without a grid.

---

## 13. Animation direction sets

An isometric character faces more directions than a platformer character, and each drawn direction multiplies your frame count. Direction-set design is therefore a *budget* decision first.

### 13.1 The direction economy

| Set | Drawn directions | With h-flip you cover | Typical use | Frame cost (×8-frame walk) |
|---|---|---|---|---|
| 1-dir | 1 (front) | 1 | icons, static NPCs | 8 |
| 4-dir | down, up, side ×1 | 4 (flip side) | *3 drawn*: retro, room games | 24 |
| 8-dir | down, up, side, down-side, up-side | 8 (flip 3 of them) | *5 drawn*: standard iso | 40 |
| 8-dir no-flip | 8 | 8 | asymmetric characters (sword hand!) | 64 |
| 16-dir | 16 (usually pre-rendered) | 16 | classic RTS/RPG (Diablo, AoE) | 128+ |

Horizontal flipping halves side-facing art but **mirrors asymmetric details** — a satchel, a sword arm, a hair parting swaps sides as the character turns. Symmetric character design is a real production strategy, not laziness; Diablo-era studios instead pre-rendered 3D models to sprites precisely because 16 directions × N animations was undrawable by hand (Section 19).

### 13.2 Choosing the facing from a velocity

Map the movement vector to a direction index by angle, with hysteresis so the facing doesn't flicker on near-boundary vectors:

```gdscript
# direction_set.gd — 8-direction facing from a velocity vector
const DIR_NAMES: Array[StringName] = [
    &"e", &"se", &"s", &"sw", &"w", &"nw", &"n", &"ne",  # 45° sectors, CCW from +x
]
const HYSTERESIS_DEG := 10.0

var _current_dir: int = 2   # start facing south

func dir_index_for(v: Vector2) -> int:
    if v == Vector2.ZERO:
        return _current_dir
    var deg := fposmod(rad_to_deg(v.angle()), 360.0)
    var sector := deg / 45.0
    var nearest := wrapi(roundi(sector), 0, 8)
    # Keep the old facing unless we are clearly inside the new sector:
    var boundary_dist := absf(sector - roundf(sector)) * 45.0
    if nearest != _current_dir and boundary_dist > (22.5 - HYSTERESIS_DEG):
        return _current_dir
    _current_dir = nearest
    return nearest
```

Then resolve to an animation and a flip:

```gdscript
func _update_animation(v: Vector2) -> void:
    var dir := dir_index_for(v)
    match dir:
        0: _play(&"walk_side", false)        # e
        1: _play(&"walk_down_side", false)   # se
        2: _play(&"walk_down", false)        # s
        3: _play(&"walk_down_side", true)    # sw  (flip)
        4: _play(&"walk_side", true)         # w   (flip)
        5: _play(&"walk_up_side", true)      # nw  (flip)
        6: _play(&"walk_up", false)          # n
        7: _play(&"walk_up_side", false)     # ne

func _play(anim: StringName, flip: bool) -> void:
    sprite.flip_h = flip
    if sprite.animation != anim:
        sprite.play(anim)
```

Details that separate polished from janky:

- **Idle keeps the last facing** — snap-to-south on stop reads as broken. Store the facing index, and give each direction an idle animation (or a single idle frame per direction).
- **Angle sectors, not component comparisons.** `if abs(x) > abs(y)` style laddering handles 4 directions and then collapses into unmaintainable nesting at 8; the sector formula scales to 16 unchanged.
- **`StringName` animation keys** (`&"walk_side"`) avoid per-frame `String` allocations in hot paths — GDScript 2.0 idiom.
- **Flip the sprite node, not the parent** — flipping a parent `Node2D` with `scale.x = -1` also mirrors child positions (held items, emitters) and can interact badly with physics; `AnimatedSprite2D.flip_h` touches only the texture.

> ⚠️ **Pitfall** — In a 2:1 world, walking one tile "north" moves mostly leftward-and-up on screen at 26.565°, which sits inside the *side* sector of a naive screen-angle mapping — so tile-stepped characters can play `walk_side` while logically walking north. For grid-stepped movement, map from the **tile-space** step direction (`delta_cell`), not the screen velocity; the 8 `delta_cell` values map 1:1 to the 8 animations with no angle math at all.

### 13.3 Sprite sheet organization

The 8-direction × N-animation matrix gets unwieldy fast; lay sheets out as **one row per direction, one sheet (or atlas region) per animation**, and let `SpriteFrames` (the `AnimatedSprite2D` resource) name entries `walk_down`, `walk_side`, `idle_up_side`, etc. Import with `filter = Nearest` per [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md). For characters authored in Aseprite, tag each direction-animation pair and export tags to JSON — the tag names become your `StringName` keys, keeping art and code in lockstep.

Character proportions for iso: with 64×32 tiles, a standing character of 48-64 px height (1.5-2 tile heights) reads correctly against furniture; the feet contact patch should be near the sprite's bottom edge with 2-4 px of shadow margin — and that contact line, per Section 7.3, is where the node origin goes.

### 13.4 Scaling up: AnimationTree and BlendSpace2D

The `match`-statement mapper of §13.2 is perfect at walk/idle scale. When the matrix grows — walk, run, carry, sit, wave, each × 8 directions — hand-written branching collapses, and Godot's animation middleware takes over. The idiomatic Godot 4 structure is an **`AnimationTree`** whose states are **`AnimationNodeBlendSpace2D`** nodes, one per action:

```
AnimationTree (state machine root)
├── idle  : BlendSpace2D — 8 idle animations placed at their
│           direction vectors: (1,0)=e, (0.7,0.7)=se, (0,1)=s …
├── walk  : BlendSpace2D — 8 walk animations, same layout
└── carry : BlendSpace2D — 8 carry-walk animations, same layout
```

Each frame you feed the *movement direction* into the active blend space, and the state machine handles action changes:

```gdscript
@onready var anim_tree: AnimationTree = $AnimationTree
@onready var state := anim_tree.get(&"parameters/playback") \
        as AnimationNodeStateMachinePlayback

func _update_animation(v: Vector2) -> void:
    if v != Vector2.ZERO:
        _facing = v.normalized()          # remember for idle
        state.travel(&"walk")
    else:
        state.travel(&"idle")
    anim_tree.set(&"parameters/walk/blend_position", _facing)
    anim_tree.set(&"parameters/idle/blend_position", _facing)
```

Set each blend space's blend mode to **discrete** (no interpolation between neighboring clips) — sprite directions must *switch*, not crossfade; blending two different sprite sheets produces ghosting garbage. The wins over hand-rolled `match`: direction selection becomes data (drag animation points in the editor), adding a 9th action touches zero movement code, and transitions (walk→sit) get the state machine's blending and conditions for free. The cost is indirection — debugging "why is he moon-walking" now involves the tree inspector. Adopt it at the third action, not before; the two-action character of §13.2 does not need it.

> ✅ **Best practice** — Whichever system drives selection, keep *one* place that maps movement vectors to facing (`dir_index_for` or the blend position write). Facing bugs are almost always two systems fighting — e.g. the state machine setting `walk` while legacy code still flips `flip_h`.

---

## 14. Pathfinding on grids — AStarGrid2D

Click-to-move, NPC routines, and AI all reduce to: *given the occupancy grid, produce a tile path from A to B*. For grid worlds Godot ships a dedicated, C++-optimized solver — **`AStarGrid2D`** — that should be your default. It even understands isometric cell shapes natively.

### 14.1 Setup, verified API

```gdscript
# nav_grid.gd — pathfinding service for a tile world
class_name NavGrid
extends RefCounted

var astar := AStarGrid2D.new()
var _layer: TileMapLayer

func setup(layer: TileMapLayer) -> void:
    _layer = layer
    astar.region = layer.get_used_rect()                 # Rect2i of cells
    astar.cell_size = Vector2(layer.tile_set.tile_size)  # 64×32
    astar.cell_shape = AStarGrid2D.CELL_SHAPE_ISOMETRIC_DOWN
    astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
    astar.default_compute_heuristic = AStarGrid2D.HEURISTIC_OCTILE
    astar.default_estimate_heuristic = AStarGrid2D.HEURISTIC_OCTILE
    astar.jumping_enabled = false
    astar.update()          # REQUIRED after region/cell_size/offset changes
    refresh_from_tiles()

func refresh_from_tiles() -> void:
    for cell: Vector2i in _layer.get_used_cells():
        var data := _layer.get_cell_tile_data(cell)
        var walkable: bool = data != null and bool(data.get_custom_data("walkable"))
        astar.set_point_solid(cell, not walkable)
        if walkable:
            var cost := maxf(1.0, float(data.get_custom_data("move_cost")))
            astar.set_point_weight_scale(cell, cost)

func find_path(from: Vector2i, to: Vector2i) -> Array[Vector2i]:
    if astar.is_point_solid(to):
        return []
    var id_path := astar.get_id_path(from, to)   # Array[Vector2i] of cells
    var out: Array[Vector2i] = []
    for c: Vector2i in id_path:
        out.append(c)
    return out
```

Walkability and costs come *from TileSet custom data* (Section 10.4) — paint the level, call `refresh_from_tiles()`, done. When a single tile changes at runtime (a door opens, furniture is placed), call `set_point_solid(cell, ...)` for just that cell; no `update()` needed for solidity/weight changes — `update()` is only required after changing structural properties (`region`, `cell_size`, `offset`, `cell_shape`).

`get_id_path()` returns the path as **cell coordinates** — usually what game logic wants; `get_point_path()` returns **positions** (cell centers scaled by `cell_size`, in the grid's own frame — offset by your map origin before use, or simply re-derive positions from cells via your own projection, which avoids frame-mismatch bugs entirely). Both accept an optional `allow_partial_path: bool` — with `true`, an unreachable target yields the path to the closest reachable cell instead of an empty array, which is almost always the right UX for click-to-move (walk *toward* the blocked chair, don't ignore the click).

> ⚠️ **Pitfall** — `AStarGrid2D` has no automatic connection to your TileMapLayer. It is a pure math object: if furniture placement changes occupancy and you forget `set_point_solid`, characters will confidently path through the new sofa. Route *all* occupancy mutations through one service (the `NavGrid` above) so grid and world cannot desynchronize.

### 14.2 Diagonal modes — the corner-cutting problem

`diagonal_mode` decides how diagonal steps interact with obstacles, and the wrong choice produces the classic "character clips through wall corners" complaint:

```
        A = actor   X = solid   . = free   → attempted diagonal

           A X            DIAGONAL_MODE_ALWAYS: A may step ↘ to g,
           X g            *visually passing between two solids* —
                          corner clipping. Fast, looks broken.

Modes (exact enum values):
  DIAGONAL_MODE_ALWAYS                → all diagonals allowed (clips corners)
  DIAGONAL_MODE_NEVER                 → 4-dir paths only (staircase movement)
  DIAGONAL_MODE_AT_LEAST_ONE_WALKABLE → diagonal ok unless BOTH flanks solid
  DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES  → diagonal only when BOTH flanks free
```

`DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES` is the safe default for characters with visible bodies: a diagonal step happens only when the two orthogonal cells flanking it are free, so sprites never overlap wall corners. `NEVER` suits games whose art only supports 4-direction movement. `ALWAYS` is fine for abstract markers, projectiles, and UI paths.

### 14.3 Heuristics and jumping

The two heuristic properties tune A*'s cost model: `default_compute_heuristic` scores *actual accumulated* cost between neighbors, `default_estimate_heuristic` scores the *estimate to the goal*. The four options (`HEURISTIC_EUCLIDEAN`, `HEURISTIC_MANHATTAN`, `HEURISTIC_OCTILE`, `HEURISTIC_CHEBYSHEV`) correspond to different movement geometries:

| Heuristic | Diagonal cost model | Use with |
|---|---|---|
| `HEURISTIC_MANHATTAN` | diagonals don't exist (cost 2) | `DIAGONAL_MODE_NEVER` |
| `HEURISTIC_OCTILE` | diagonal = √2 ≈ 1.414 | 8-dir movement (**standard**) |
| `HEURISTIC_CHEBYSHEV` | diagonal = 1 (as cheap as straight) | 8-dir where diagonals are free moves (some tactics rules) |
| `HEURISTIC_EUCLIDEAN` | straight-line distance | any-angle-ish smoothing, default |

Mismatched heuristic and diagonal mode doesn't crash — it produces *ugly* paths (unnecessary zigzags) or slower searches (underestimating heuristics expand more cells). Match the pair.

`jumping_enabled = true` activates Jump Point Search-style acceleration — dramatic speedups on large open grids by skipping symmetric path segments. Its documented constraint: it assumes uniform cell costs, so **it ignores `set_point_weight_scale` values**. Weighted terrain (mud costs 2×) and jumping are mutually exclusive; pick per map.

Weight semantics, precisely: `weight_scale` multiplies the cost of *entering* that cell. `1.0` is neutral, `4.0` means "cross only if the detour would cost more than 4× the straight route", `0.5` is a highway. Painting roads with weight 0.5 in custom data is how builder-game NPCs "prefer paths" with zero extra AI code.

### 14.4 Worked example — click-to-move actor

The complete loop, tying together picking (5), stepping (12.4), facing (13.2) and the grid:

```gdscript
# click_walker.gd
extends CharacterBody2D

const STEP_TIME := 0.18
@export var map: Node2D              # provides pick_cell() / is_valid_cell()
@export var nav: NavGrid

var _path: Array[Vector2i] = []
var _cell: Vector2i
var _stepping := false

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton \
            and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
        var goal := map.pick_cell(get_global_mouse_position())
        if map.is_valid_cell(goal):
            _path = nav.find_path(_cell, goal)
            if not _path.is_empty() and _path[0] == _cell:
                _path.remove_at(0)          # solver includes the start cell

func _physics_process(_delta: float) -> void:
    if _stepping or _path.is_empty():
        return
    var next := _path.pop_front() as Vector2i
    if nav.astar.is_point_solid(next):      # world changed mid-walk
        _path = nav.find_path(_cell, _path.back() if _path else next)
        return
    _step_to(next)

func _step_to(next: Vector2i) -> void:
    _stepping = true
    _update_animation(Vector2(next - _cell))      # tile-space facing (13.2)
    _cell = next
    var tween := create_tween()
    tween.tween_property(self, "position",
            IsoProjection.cell_center(next), STEP_TIME)
    tween.finished.connect(func() -> void: _stepping = false)
```

The mid-walk revalidation (`is_point_solid(next)`) is what makes dynamic worlds safe: when the player drops a bookshelf onto an NPC's path, the NPC re-plans at the next step instead of walking through it. For smooth (non-stepped) followers, replace the tween with velocity toward `cell_center(next)` and advance the path index when within an arrival radius — that variant is exactly what `NavigationAgent2D` automates in the next section.

### 14.5 Debugging and profiling pathfinding

Pathfinding bugs are invisible until drawn. Standard instrumentation for a grid world:

```gdscript
# path_debug.gd — draws the grid's solidity and the last path.
# Cheap trick: parent this under the §3.6 iso container and draw in
# TILE SPACE; the container's transform renders it as diamonds.
extends Node2D

var nav: NavGrid
var last_path: Array[Vector2i] = []

func _draw() -> void:
    for cell: Vector2i in nav.all_cells():
        if nav.astar.is_point_solid(cell):
            draw_rect(Rect2(Vector2(cell), Vector2.ONE), Color(1, 0, 0, 0.25))
        else:
            var w := nav.astar.get_point_weight_scale(cell)
            if w > 1.0:
                draw_rect(Rect2(Vector2(cell), Vector2.ONE),
                        Color(1, 0.6, 0, minf(0.08 * w, 0.4)))
    for i in range(last_path.size() - 1):
        draw_line(Vector2(last_path[i]) + Vector2(0.5, 0.5),
                Vector2(last_path[i + 1]) + Vector2(0.5, 0.5),
                Color.CYAN, 0.1)
```

Toggle it with a debug key and most grid mysteries resolve on sight: desynchronized occupancy shows as characters detouring around empty air (a red cell where no furniture is), missing custom data shows as uniformly white grids, and heuristic mismatches show as zigzag paths across open ground.

Performance expectations, so you know when something is wrong rather than merely busy: `AStarGrid2D` is C++-side and comfortably solves dozens of medium-map (≈100×100) queries per frame on desktop hardware. If profiling ([DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) covers the profiler) still shows pathfinding hotspots, apply in order: (1) cache paths — followers re-request only when the goal cell changes; (2) stagger requests — one NPC re-plans per frame round-robin, not all N on the frame the player moves; (3) shrink the search — path between region waypoints (the two-level §15.1 pattern) instead of across the full map; (4) `jumping_enabled` on unweighted maps. Reaching for threads comes after all four, and rarely.

---

## 15. Pathfinding beyond grids — AStar2D and NavigationServer2D

Two situations outgrow `AStarGrid2D`: worlds whose connectivity isn't a uniform grid (multi-room graphs, teleporters, one-way drops), and worlds with free-form walkable *areas* rather than cells. Godot covers the first with `AStar2D` and the second with the navigation server stack.

### 15.1 AStar2D — arbitrary graphs

`AStar2D` is A* over a point graph you build by hand: points with ids and positions, segments connecting them. Verified core API:

```gdscript
var graph := AStar2D.new()

# Build: waypoints at doorways, room centers, teleporter pads…
var id_a := graph.get_available_point_id()
graph.add_point(id_a, Vector2(320, 180))          # optional weight_scale arg
var id_b := graph.get_available_point_id()
graph.add_point(id_b, Vector2(704, 372), 1.0)
graph.connect_points(id_a, id_b)                  # bidirectional := true
# one-way connections: connect_points(a, b, false)  — drops, conveyor exits

# Query
var start_id := graph.get_closest_point(actor_pos)
var goal_id := graph.get_closest_point(click_pos)
var points: PackedVector2Array = graph.get_point_path(start_id, goal_id)
var ids: PackedInt64Array = graph.get_id_path(start_id, goal_id)

# Runtime mutation
graph.set_point_disabled(door_id, true)           # locked door: exclude node
graph.set_point_weight_scale(mud_id, 3.0)         # discourage without forbidding
graph.are_points_connected(id_a, id_b)
```

Where it shines in iso games:

- **Room-graph navigation for companion/sim games**: one point per doorway and per furniture "interaction spot"; an NPC's plan is a path through rooms, executed room-by-room by local movement. This two-level scheme (graph globally, grid or steering locally) is how large iso sims keep pathfinding cheap.
- **Special edges**: teleporters, ladders between elevation levels, and one-way jumps are just extra `connect_points` calls — things a grid cannot express at all.
- **Custom cost logic**: subclass and override the virtual `_compute_cost(from_id, to_id)` / `_estimate_cost(from_id, to_id)` to make cost depend on anything (danger maps, time of day). `weight_scale` multiplies the computed cost of entering a point.

`AStar2D` computes costs from **straight-line point distances** by default — with isometric projected positions this means screen distances, which under-weight north-south travel (Section 12.2's wrinkle) — mostly harmless for coarse room graphs, fixable via `_compute_cost` in logical space if it matters.

### 15.2 The navigation server stack — NavigationAgent2D

The third option replaces cells and hand-built graphs with **navigation meshes**: polygonal walkable regions baked from your scene, queried through `NavigationServer2D`, and consumed by `NavigationAgent2D` nodes that handle path following and (optionally) local avoidance between agents. TileSets participate directly — atlas tiles can carry navigation polygons, and `TileMapLayer.navigation_enabled` toggles their contribution.

```gdscript
# nav_follower.gd — CharacterBody2D + NavigationAgent2D child
extends CharacterBody2D

const SPEED := 120.0
@onready var agent: NavigationAgent2D = $NavigationAgent2D

func _ready() -> void:
    agent.path_desired_distance = 4.0     # waypoint arrival radius
    agent.target_desired_distance = 6.0   # final arrival radius
    agent.navigation_finished.connect(func() -> void: _play_idle())

func go_to(world_pos: Vector2) -> void:
    agent.target_position = world_pos     # requests a new path

func _physics_process(_delta: float) -> void:
    if agent.is_navigation_finished():
        return
    var next := agent.get_next_path_position()   # call once per physics frame
    velocity = global_position.direction_to(next) * SPEED
    _update_animation(velocity)
    move_and_slide()
```

With `avoidance_enabled = true`, you instead set `agent.velocity` each frame and move using the safe velocity delivered via the `velocity_computed` signal — agents then steer around each other (RVO avoidance), which matters the moment two NPCs share a hallway.

### 15.3 Choosing among the three

| | `AStarGrid2D` | `AStar2D` | NavigationServer2D + Agent |
|---|---|---|---|
| World model | uniform cell grid | arbitrary point graph | polygon meshes |
| Setup cost | minimal (region + solids) | manual graph authoring | bake/author nav polygons |
| Iso awareness | native (`CELL_SHAPE_ISOMETRIC_*`) | none needed (you place points) | none needed (polygons are projected shapes) |
| Dynamic obstacles | `set_point_solid` per cell — instant | disable points/edges | re-bake or carve via server (heavier) |
| Path style | cell steps | waypoint hops | smooth any-angle strings |
| Agent avoidance | no | no | yes (RVO) |
| Best iso fit | tile tactics, builders, grid sims | room graphs, teleports, meta-travel | free-move action iso (Hades-like), crowds |

Rule of thumb: **if the player thinks in tiles, path in tiles** (`AStarGrid2D`); **if the world is rooms-and-doors, path the graph** (`AStar2D`); **if movement is free and analog, use the nav mesh** — and combine them freely, since the layers answer different questions. Relax Room today needs none of them (one open floor polygon, direct steering); the moment its roadmap adds a second room or a walkabout NPC, the room-graph pattern is the natural first step.

---

## 16. Camera for isometric scenes

Isometric worlds are usually larger than the window, so the camera is a gameplay surface: what it shows, how it moves, and — for pixel art — whether it destroys the pixel grid. All on `Camera2D`, verified property names throughout.

### 16.1 Limits — clamping to the diamond's bounding box

`Camera2D` limits are a world-space rectangle the viewport edge will not cross: `limit_left`, `limit_top`, `limit_right`, `limit_bottom` (plus `limit_enabled`, default `true`). For a diamond map, compute the *projected* bounding box from the four extreme corners:

```gdscript
func fit_camera_limits(cam: Camera2D, map_w: int, map_h: int) -> void:
    var top    := IsoProjection.tile_to_screen(Vector2.ZERO)
    var right  := IsoProjection.tile_to_screen(Vector2(map_w, 0))
    var left   := IsoProjection.tile_to_screen(Vector2(0, map_h))
    var bottom := IsoProjection.tile_to_screen(Vector2(map_w, map_h))
    cam.limit_left   = int(left.x)
    cam.limit_right  = int(right.x)
    cam.limit_top    = int(top.y) - 64        # headroom for tall back-row art
    cam.limit_bottom = int(bottom.y) + 32     # foot-room for front-row tiles
```

The diamond leaves triangular void at the bounding box corners; games either fill beyond the map with "ocean"/skirt tiles, or accept letterbox-colored voids at extreme pans, or shape stricter limits per edge. `limit_smoothed = true` eases the camera into limits instead of hard-stopping — enable it whenever position smoothing is on, or the smooth follow will visibly *slam* at map edges.

### 16.2 Following and drag margins

```gdscript
cam.position_smoothing_enabled = true
cam.position_smoothing_speed = 6.0     # higher = tighter follow

# Optional dead-zone follow (camera moves only when player nears edges):
cam.drag_horizontal_enabled = true
cam.drag_vertical_enabled = true
cam.drag_left_margin = 0.15            # fractions of half-viewport
cam.drag_right_margin = 0.15
cam.drag_top_margin = 0.12
cam.drag_bottom_margin = 0.18          # more foot-room: iso worlds read downward
```

Drag margins suit builder/tactics games where the *world*, not the avatar, is the subject — small player movements shouldn't scroll the whole diorama. Action iso games (Hades) use tight centered follow with `position_smoothing` and small look-ahead offsets via `offset`. Edge-scroll and middle-mouse pan (RTS style) are trivial additions that write `cam.position` directly; clamp manually to the same limits since limits constrain *rendering*, and a scripted pan writing `position` can otherwise fight smoothing at the boundary.

### 16.3 Zoom without murdering pixels

`Camera2D.zoom` is a `Vector2` scale factor — `Vector2(2, 2)` shows the world at 200%. For pixel art the rule is hard:

> **Zoom must be an integer multiple (or an integer divisor at your peril).** At `zoom = 1.5`, every second texel maps to a fractional screen span; nearest-neighbor filtering then drops/doubles rows irregularly and the image *shimmers* during pans. 1×, 2×, 3×, 4× are safe. Fractions are not, no matter how nice `tween`ed zoom feels.

```gdscript
const ZOOM_STEPS: Array[float] = [1.0, 2.0, 3.0, 4.0]
var _zoom_i := 1

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.pressed:
        if event.button_index == MOUSE_BUTTON_WHEEL_UP:
            _set_zoom(_zoom_i + 1)
        elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            _set_zoom(_zoom_i - 1)

func _set_zoom(i: int) -> void:
    _zoom_i = clampi(i, 0, ZOOM_STEPS.size() - 1)
    $Camera2D.zoom = Vector2.ONE * ZOOM_STEPS[_zoom_i]
```

Snap zoom between integer steps (optionally with a very fast tween that *lands* on the integer); combine with project-level integer scaling for window resizes — `display/window/stretch/mode = canvas_items` with `display/window/stretch/scale_mode = integer` keeps the game's pixels square when the OS window scales. Non-pixel-art iso (HD painted sprites, linear filtering) is exempt from all of this; zoom freely.

### 16.4 Screen shake that respects the grid

Naive shake — random `offset` each frame — puts the camera at fractional pixel positions and makes pixel art crawl. Grid-respecting shake quantizes the offset to whole *texels* (world pixels at current zoom):

```gdscript
# pixel_shake.gd — attach to Camera2D
extends Camera2D

var _trauma := 0.0                       # 0..1, add on impact events

func add_trauma(amount: float) -> void:
    _trauma = minf(_trauma + amount, 1.0)

func _process(delta: float) -> void:
    _trauma = maxf(_trauma - 1.8 * delta, 0.0)
    var shake := _trauma * _trauma       # square: small trauma ≈ no shake
    var raw := Vector2(
        randf_range(-1, 1), randf_range(-1, 1)) * 6.0 * shake
    offset = raw.snapped(Vector2.ONE)    # ← whole-pixel offsets only
```

Two refinements for iso specifically: bias shake amplitude to the **y axis ×0.5** so the shake matches the world's 2:1 anisotropy (a purely stylistic but noticeably "right" touch), and never shake via `position` (it fights smoothing and limits) — `offset` exists precisely to compose on top of the followed position.

### 16.5 The camera-less option — fixed-view presentation

**Relax Room note.** Relax Room ships **no Camera2D at all**: the room fits the window exactly, so the viewport *is* the camera (a fixed full-view presentation — the same choice as Into the Breach's single-board framing). This is the correct minimal choice for a desktop companion; the sections above are the upgrade path if a future feature (a garden view larger than the window, a zoomable dollhouse) ever needs one. Performance implications of static-view rendering are covered in [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md).

Going camera-less is still a set of decisions, not an absence of them:

- **Design resolution and stretch.** Author the room at a fixed design size (Relax Room: 1280×720) and let the project's stretch settings own resizing: `display/window/stretch/mode = canvas_items` scales the whole canvas; with pixel art add `display/window/stretch/scale_mode = integer` so an OS-resized window snaps to whole multiples instead of producing fractional texel scaling (§16.3's rule, enforced project-wide).
- **Aspect policy.** A companion window can be freely resized by the user; choose between `aspect = keep` (letterbox bars — safe, framed) and `expand` (the room canvas grows, revealing margin you must art-direct — e.g. more wall and floor at the edges). `keep` is the low-effort correct answer; `expand` is nicer and costs deliberate over-painting of the room's borders.
- **The world still needs an origin contract.** With no camera transform, world space *is* screen space at scale 1 — which quietly hardcodes the map origin into every position. Keep positions relative to a room root node anyway (§4.2); the day a camera or a second room arrives, nothing has assumed "global (640, 500) is the room center".
- **Sub-window motion still exists.** Fixed view doesn't mean static frame: the parallax window (§20.3), light flicker, and micro pan-and-zoom moments (a 2-second push-in when the character sleeps, at integer-safe scale, via the root node's transform) all live comfortably inside a camera-less scene — a `Camera2D` earns its place only when the *player* needs view control.

---

## 17. Pixel art for isometric games

Programmers on small teams end up making, fixing, or at least *specifying* isometric art. This section covers the rules that make iso pixel art read cleanly, and the pipeline that gets it into Godot unmangled. (General sprite import mechanics live in [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md); this section is the iso-specific craft.)

### 17.1 Line stepping — the one rule that makes it "iso"

Every edge in 2:1 isometric pixel art follows a fixed stepping pattern. The ground-plane edges are the defining one:

```
THE 2:1 STEP (ground edges, 26.565°):
                                    ████
                                ████
                            ████            2 across, 1 down.
                        ████                ALWAYS. No 1-steps,
                    ████                    no 3-steps, no "close
                                            enough". Any deviation
                                            reads as a broken edge.

VERTICALS: straight columns.        1:1 DIAGONALS (45°): stair-step
    ██                                  ██
    ██   (object side edges,              ██     (used for "rotated"
    ██    wall corners)                     ██    details, ramps)

FORBIDDEN in clean iso: slopes like 3:1, 2:2 mixes on one edge,
and anti-aliased "soft" edges on the tile boundary (see 17.3).
```

The three legal line families — 2:1 steps, verticals, 45° stairs — cover almost every edge in classic iso art. When drawing a new prop, block its silhouette *only* from these families first; texture and shading come after. This is also the acceptance test when reviewing outsourced art: zoom to 800% and walk the silhouette.

### 17.2 Constructing a floor tile

The canonical 64×32 diamond, step by step:

```
1. Outline: four 2:1 edges meeting at      2. The vertex rule: top and bottom
   left/right POINTS and top/bottom          vertices are 2px wide plateaus,
   points.                                   left/right are 1px points — this
                                             is what lets adjacent tiles
              ▄▄████▄▄                       interlock with NO seams and NO
          ▄▄██░░░░░░██▄▄                     doubled pixels.
      ▄▄██░░░░░░░░░░░░██▄▄
    ◄██░░░░░░░░░░░░░░░░░░██►             3. Fill flat base color.
      ▀▀██░░░░░░░░░░░░██▀▀               4. Shade: light from top-right
          ▀▀██░░░░░░██▀▀                    (or pick one; NEVER vary per
              ▀▀████▀▀                      asset). Top face lightest,
                                            left face darkest.
                                          5. Texture sparsely — floor tiles
                                            repeat; loud detail tiles.
```

When tiles are placed with the Section 3 transforms (or by TileMapLayer), adjacent diamonds share edge pixels perfectly *if and only if* every tile obeys the same vertex convention. Mixed conventions produce the 1-px "grout lines" or doubled dark edges that plague first iso projects — an art bug that looks exactly like a math bug.

For **cube/wall tiles**, extrude the diamond: copy the top face, draw vertical side edges of the chosen wall height (commonly `H` or `1.5·H`), and shade the two visible faces with the fixed light direction:

```
        ▄▄████▄▄                 Face brightness (light: top-right):
    ▄▄██░░░░░░██▄▄                top    = base color + 15-20% L
  ██▓▓▓▓██░░░░▓▒▒▒██              right  = base
  ██▓▓▓▓▓▓████▒▒▒▒██              left   = base − 15-20% L
  ██▓▓▓▓▓▓█║█▒▒▒▒▒██              Keep the SAME hue; shift lightness
    ▀▀██▓▓█║█▒▒██▀▀               and a little saturation — pure
        ▀▀█║█▀▀                   black shading looks like soot.
```

### 17.3 Anti-aliasing: where it is banned and where it is allowed

- **Tile boundary edges: no AA, ever.** Semi-transparent or blended pixels on the diamond edge break the interlock; adjacent tiles show halos and seams — especially visible the moment tiles draw over a different background.
- **Interior detail: manual AA is fine.** Within a sprite's interior, hand-placed intermediate colors soften curves exactly as in any pixel art.
- **Engine-side: filtering off.** Import with nearest-neighbor — project-wide via `rendering/textures/canvas_textures/default_texture_filter = Nearest`, or per-node `texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST`. Linear filtering (the default look of blurry sprite edges) both blurs and *creates* edge translucency where none was drawn.
- **No rotation, no fractional scale at runtime.** Rotating pixel art resamples every edge; scale only by integers (Section 16.3). If a design needs a rotated prop, draw the rotation.

### 17.4 Palette discipline

Limited palettes are what make disparate iso assets look like one world:

- **One global ramp set.** Define 4-6 lightness ramps (wood, stone, foliage, metal, cloth, accent) of 4-6 colors each — a 24-36 color world palette. Every asset picks from these ramps; nothing introduces private colors.
- **Hue-shift the ramps**: shadows lean cool (toward blue/purple), highlights lean warm — straight darkened-same-hue ramps look muddy at iso's large flat faces.
- **Reserve one accent range** for interactive/highlight states so "clickable" reads instantly (Relax Room tints its placement ghost green/red by validity — same principle).
- **Test at 100% and at target zoom.** Iso games are played at 2-3× zoom; a dither texture invisible at 100% can moiré at 3×.

### 17.5 Tools and pipeline

| Tool | Type | Cost | Why it earns a slot |
|---|---|---|---|
| **Aseprite** | pixel editor | ~$20 (or free self-compiled) | animation timeline, tags→JSON export, palette control, layer-split export (trunk/canopy from Section 9.2) |
| **Piskel** | pixel editor (web) | free | zero-install prototyping and jam art |
| **Pyxel Edit** | tile-focused editor | ~$9 | draw *into* a tiled preview — seam problems visible while drawing |
| **Tiled** | map editor | free (OSS) | full iso/staggered map support; JSON export importable into Godot tooling |
| **GIMP / Krita** | general editors | free (OSS) | batch ops, palette mapping, post-processing |
| **TexturePacker / Aseprite CLI** | atlas builders | free-ish | build atlases in CI so artists never hand-pack |

Pipeline rules that prevent recurring accidents:

1. **Author at 1×.** Never draw at 4× and downscale — resampling shreds the stepping. Zoom the *editor*, not the canvas.
2. **One `.aseprite` source per asset, exports generated.** PNGs in the repo are build artifacts; the layered source is the truth (this is what makes the Section 9.2 split retrofittable).
3. **Fix the grid template.** Ship artists a template canvas with the 64×32 diamond guide and the origin marker; every decoration is authored against it, so `footprint_inset` (Section 7.3) is a known constant per asset class, not a per-sprite surprise.
4. **Import presets in Godot**: nearest filter, no mipmaps, lossless compression for pixel sources — set once as an import default, not per-file.

### 17.6 Dynamic light on iso pixel art

Baked shading (the fixed top-right light of §17.2) and Godot's dynamic 2D lights can coexist, and the combination is the modern refresh of Diablo's per-tile lighting (§19.3):

- **`PointLight2D` over flat sprites** already reads well in iso rooms: a lamp decoration carrying a warm point light with gentle falloff makes the whole y-sorted neighborhood respond. Keep `energy` low — baked shading is doing most of the modeling, and strong dynamic light flattens it.
- **Normal maps take it further**: author (or auto-generate and then hand-fix) a normal map per sprite so light rakes across the diamond faces — the top face responding differently from the left face is what sells volume. In Godot, assign the normal map on the sprite's `CanvasTexture`; the pixel-art caveat is that generated normals from stepped edges are noisy, so blur the *normal source*, never the albedo.
- **Occluders**: `LightOccluder2D` polygons matching furniture *footprints* (not silhouettes — the same plan-view rule as §12.5's collision) give credible shadow casting in room scenes.
- **Consistency rule**: dynamic lights must agree with the baked light's story. A baked top-right sun plus a roaming blue point light from the left produces mud; theme dynamic lights as *local sources* (lamps, screens, fireplaces) and keep the global directional feel baked.

The full 2D lighting model — blend modes, shadow filtering, light-only textures — is [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md)'s territory; the takeaway here is that the *pixel-art pipeline* must plan for it (export normal sources from the layered files) if the project's look calls for living light, and Relax Room's cozy-lamp aesthetic is the textbook use case.

---

## 18. Performance engineering for isometric scenes

Isometric scenes stress the 2D renderer in specific, predictable ways: many small sprites, heavy per-frame sorting, and overdraw from overlapping diamonds. The fixes are equally specific. (General profiling methodology: [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md).)

### 18.1 Know what y-sort costs

Y-sorting is re-evaluated when sorted content moves — for large sorted sets this is real work, and it also *changes batching*: a y-sorted TileMapLayer abandons quadrant-batched rendering in favor of per-tile draws so tiles can interleave with other nodes.

The high-leverage decisions:

| Decision | Effect |
|---|---|
| Flat floors on **non-sorted** layers | floors stay quadrant-batched; typically the majority of tiles |
| Sort only the interleaving band | walls + props + actors, nothing else, joins the y-sort pool |
| Split static from dynamic | a sorted-but-static props layer re-sorts only when edited; actors churn in a smaller pool |
| Keep sorted pools shallow | y-sort pools are per-parent; three rooms as three sorted parents beat one 3-room pool |

### 18.2 Culling and chunking large maps

The window shows a few hundred tiles; a 256×256 map has 65,536. Strategies, cheapest first:

1. **Let TileMapLayer cull.** Unsorted layers cull by quadrant out of the box. Prefer building *structure* as tiles partly for this reason (Section 10.5).
2. **Chunk scene-based content.** Group placed scenes into region parents (e.g. 16×16-tile chunks) and toggle chunk `visible` by camera rect. `VisibleOnScreenNotifier2D` automates per-object visibility for expensive one-offs (animated fountains, particle emitters).
3. **Chunk *processing*, not just drawing.** Off-screen NPCs should also drop `_physics_process` work: `process_mode = PROCESS_MODE_DISABLED` on sleeping chunks, or timers ticking coarse simulation instead of per-frame AI.
4. **Custom `RenderingServer` canvas items** for extreme cases (bullet-heaven-scale iso): allocate canvas items directly and set transforms yourself, skipping node overhead. Measure before resorting to this — the node path is fine into the thousands.

Overdraw deserves one paragraph: diamond tiles overlap their neighbors' bounding boxes by construction, and tall walls overlap floors, so iso scenes repaint many pixels per frame. On desktop GPUs this is rarely the bottleneck; on integrated GPUs at 4K it can be. The mitigations are honest ones — fewer stacked decorative layers, no full-screen semi-transparent overlays, `self_modulate` tint instead of duplicate tinted sprites.

### 18.3 Atlases and batching

The 2D renderer batches consecutive draws that share texture and material. Isometric games, with hundreds of small props, live or die by this:

```
Per-decoration textures:                One category atlas:
  chair.png, desk.png, plant.png,        furniture_atlas.png (2048²)
  lamp.png … 120 files                     ↓
    ↓                                    long runs of same-texture draws
  texture switch per sprite               → few draw calls
  → up to a draw call per sprite
```

Practical rules: pack per *category and band* (floors atlas, walls atlas, furniture atlas, characters atlas) so draw order runs through few textures per band; let Godot's import-time atlas or an external packer do the packing; keep character animation in `SpriteFrames` backed by sheet textures rather than per-frame files. Note the interaction with sorting: y-sort interleaves *different* objects by design, so band-aligned atlases (everything in the sorted band sharing one atlas) is precisely what keeps interleaving batchable.

### 18.4 The desktop-companion budget

A companion app like Relax Room has an inverted performance goal: not "hit 60 fps under load" but "consume approximately nothing while idle on someone's second monitor". The iso-relevant consequences:

- **Static view ⇒ static cost.** No camera, no culling churn, no per-frame sorting once decorations settle: y-sort work only happens when the character moves. An idle room should render at near-zero CPU.
- **Cap the frame rate** (`Engine.max_fps`, or low-processor mode) — a decoration app does not need 144 Hz.
- **Prefer event-driven redraw thinking**: tween-driven motion that *stops* (and lets the scene go quiescent) beats perpetual idle animations; if ambience is wanted, one subtle looping shader beats twenty animated sprites.

Full treatment — including window transparency and always-on-top costs — in [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md).

### 18.5 Measurement checklist

Optimize from numbers, not vibes. The iso-specific readings to collect before touching anything, using the profiler and the Rendering monitors (`Performance.get_monitor()` / the debugger's Monitors tab):

| Reading | Where | Healthy (room-scale) | Suspect means |
|---|---|---|---|
| Draw calls per frame | Monitors → Raster | tens | atlas fragmentation (§18.3) or over-split sprites |
| CanvasItems drawn | Monitors → Raster | low hundreds | culling not engaged; everything always visible (§18.2) |
| Physics process time | Profiler | ~0 when idle | off-screen NPCs still simulating (§18.2 step 3) |
| Frame time, idle scene | Profiler | flat, near-vsync-wait | perpetual animations keeping the scene hot (§18.4) |
| Frame time while dragging a decoration | Profiler | no spike | per-frame overlap scans or ghost re-instantiation (§5.5, §11.3) |
| Path query time under N NPCs | custom timer | µs-ms range | missing caching/staggering (§14.5) |

Two habits close the loop: profile on the *weakest target machine* (a companion app's real habitat is an aging office laptop, not your dev box), and re-run the same three scripted scenarios (idle room, decoration drag, character walking a long path) after every performance change so improvements are attributable. The general methodology — budgets, monitors, flame graphs — is [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md)'s subject; this table is its isometric appendix.

---

## 19. Famous isometric games — technical analysis

Four decades of shipped isometric games form a catalogue of solved problems. This section reads them as engineering case studies: for each, the projection choice, the sorting/production technique, and the transferable lesson.

### 19.1 Timeline

| Year | Game | Technical innovation |
|---|---|---|
| 1982 | **Zaxxon** (Sega) | first mainstream axonometric arcade rendering; shadow as altitude cue |
| 1989 | **SimCity** (Maxis) | tile-based city sim (orthogonal; iso arrives with SC2000) |
| 1993 | **Ultima VII** (Origin) | large seamless iso-style RPG world; object-rich interiors |
| 1993 | **SimCity 2000** (Maxis) | dimetric city building; terrain elevation with y-offset stacking |
| 1994 | **X-COM: UFO Defense** | destructible multi-level iso tactics; per-tile occupancy logic |
| 1996 | **Diablo** (Blizzard) | real-time iso ARPG; pre-rendered sprites; dynamic light on tiles |
| 1997 | **Age of Empires** (Ensemble) | iso RTS at scale; hundreds of sorted units |
| 1997 | **Fallout** (Interplay) | trimetric-leaning look; hex logical grid under iso-style art |
| 1999 | **RollerCoaster Tycoon** (Sawyer) | assembly-tuned iso; 4-rotation everything; extreme sprite economy |
| 2000 | **The Sims** (Maxis) | room decoration sim; wall cutaway modes; object interaction slots |
| 2000 | **Diablo II** (Blizzard) | refined pre-rendered iso; 8-direction character sets at scale |
| 2001 | **Habbo Hotel** (Sulake) | web iso rooms; strict 2:1 pixel art; catalog-driven furniture |
| 2016 | **Stardew Valley** (ConcernedApe) | top-down comparison point: depth *without* iso projection |
| 2018 | **Into the Breach** (Subset) | one-screen iso board; perfect-information presentation |
| 2020 | **Hades** (Supergiant) | painted pseudo-iso; 3D-lit characters over 2D backgrounds |
| 2019-21 | **Disco Elysium** (ZA/UM) / **Unpacking** (Witch Beam) | painterly iso over 3D nav / hidden-grid decoration storytelling |
| 1997 | **Final Fantasy Tactics** (Square) | iso tactics with true tile elevation as a core mechanic |
| 2014 | **Transistor** (Supergiant) | painted pseudo-iso action; authored per-scene composition |
| 2023 | **Baldur's Gate 3** (Larian) | full 3D with iso-inherited camera grammar |

The table is curated for *technique*, not completeness: each row introduced or perfected something this module teaches — elevation stacking, sprite economy, sorting at scale, the decoration loop, the hybrid pipelines, or the survival of the iso camera grammar into full 3D. The subsections below pull those threads.

### 19.2 SimCity 2000 — elevation as offset stacking

SC2000's terrain is Section 6 shipped in 1993: a heightfield where each tile's `z` renders as a fixed y-offset, cliff tiles bridge levels, and the level slider resolves picking ambiguity by letting the user *choose* the active elevation plane. Water is height-capped terrain with a different tile family. **Lesson:** convincing terrain needs no 3D — a per-tile integer height, offset rendering, and transition tiles for the seams. Its four fixed view rotations also set the industry pattern: rotation is a *data* problem (4 sprite sets), not a camera problem.

### 19.3 Diablo I/II — pre-rendered sprites and light

Blizzard modeled characters and monsters in 3D and rendered them to sprites at fixed angles (8 directions for most actors) — trading runtime cost for disk and RAM at a time when real-time 3D of that fidelity was impossible. Two transferable techniques: **direction quantization** (a continuous-feeling ARPG runs on 8 facing directions — Section 13's economics), and **per-tile dynamic light**: vertex/tile-level light values modulating sprite color, which reads as dramatic dungeon lighting without any real light transport. In Godot terms: `PointLight2D` over normal-mapped sprites achieves per-pixel what Diablo faked per-tile — see [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md).

### 19.4 RollerCoaster Tycoon — sprite economy at the limit

RCT (largely hand-written x86 assembly by Chris Sawyer) renders parks of thousands of objects — every coaster piece drawable at 4 rotations × multiple slopes/banks — through disciplined sprite tables and the painter's algorithm. The playable lesson is **asset combinatorics**: track pieces exist for every (rotation × slope × bank) combination *because the projection cannot rotate sprites*; the design constrained content (piece types) to keep the table finite. When you spec a rotatable iso object today, you are budgeting the same table.

### 19.5 Age of Empires — sorting hundreds of movers

An iso RTS is a stress test of Section 8 at scale: hundreds of units crossing, buildings with multi-tile footprints, projectiles arcing between elevations. Classic RTS engines bucket units by tile row and repaint dirty rows, an ancestor of "sort within bands, bands by row" (`z = f(x + y)`). **Lesson:** at high object counts you do not sort one big list; you exploit the grid to keep sorting local.

### 19.6 The Sims and Habbo Hotel — the decoration lineage

The Sims is the direct ancestor of every room-decoration game, Relax Room included: catalog-driven objects, grid-snapped placement with rotation, wall/floor slot types, and the structural cutaway (walls-down mode) from Section 9.3. Its deeper innovation is architectural: objects advertise their own interactions to characters (the "smart object" pattern) — the room is a database the sim queries. Habbo Hotel proved the same loop works in strict 2:1 pixel art with a server-authoritative catalog. **Lesson for Relax Room:** its `decorations.json` catalog, zone rules and snap-on-drop are this lineage's minimal viable core; the growth path (object interactions, character autonomy) is already mapped by these two games.

### 19.7 Stardew Valley — the top-down comparison point

Stardew is *not* isometric — it is top-down with a tilted "3/4" reading: floors are seen from above, object fronts from the side (the oblique cheat of Section 2.4). It still needs y-sort, feet origins and band layering — everything in Sections 7-8 — while entirely avoiding projection math, diamond picking, and per-direction furniture art. **Lesson:** the depth-sorting toolkit is independent of the projection; adopt it even when you reject the diamond. That is precisely Relax Room's position on the spectrum.

### 19.8 Hades — pseudo-iso with 3D actors

Supergiant paints fixed-perspective environments (no tile grid — bespoke painted rooms with authored walkable areas) and renders *characters* as real-time 3D models lit dynamically, composited into the 2D scene at an iso-ish camera angle. Sorting is handled by ground-anchor comparisons like any 2D game. **Lesson:** "isometric" is a *camera grammar*, separable from both tiles and sprites; and hybrid pipelines (2D world, 3D actors) buy dynamic lighting and animation blending while keeping hand-painted world art. In Godot this maps to `Sprite3D`/viewport-composited actors or simply to shader-lit 2D — the grammar, not the tech, is what players recognize.

### 19.9 Unpacking and Into the Breach — small-scope masterclasses

**Unpacking** hides its grid: items snap to fine positions with plausibility rules per surface, and the *decoration itself is the narrative*. Its lesson is Relax Room's thesis — placement freedom with gentle snapping (Section 11.2) reads as self-expression, and saved layouts are the player's story. **Into the Breach** frames one iso board per screen — no camera, no scrolling, total information visible — showing that the diamond can be a *board-game presentation* with UI-grade clarity: highlighted tiles, previewed outcomes, zero ambiguity. Both prove scope discipline: a single-screen iso presentation (as in Relax Room) is not a lesser version of Diablo; it is a different, complete genre.

### 19.10 X-COM and Fallout — logic grids under looser art

Two 90s classics demonstrate that the *logical* grid and the *visual* projection are independent choices. **X-COM: UFO Defense** runs a strict 3D cell grid (x, y, *and* level) under its iso art: every tile tracks occupancy, cover and destructibility per level, which is why its tactical reasoning (line of sight, explosions chewing through floors) works — the renderer merely projects a rigorous voxel-ish model, Sections 6.4 and 8.2 at 1994 scale. **Fallout** went the other way: its art leans trimetric for a distinctive look, while the *logic* runs on a hexagonal grid — hexes gave it natural 6-direction facing and more isotropic movement costs than squares. **Lesson:** choose the logic grid for the *rules* you want and the projection for the *look* you want; the transform layer between them is yours to define, and nothing forces them to match.

### 19.11 Disco Elysium and Baldur's Gate 3 — the grammar outlives the tech

**Disco Elysium** renders painterly pre-rendered backgrounds with 3D characters navigating baked walkable meshes — the Hades hybrid (19.8) tuned for a reading-heavy RPG: the fixed iso-ish view keeps every scene composition authored, like a painting the player walks through. **Baldur's Gate 3** is fully real-time 3D, yet ships an overhead "tactical" camera whose grammar — fixed-feeling angle, click-to-move, area templates on the ground plane — is pure isometric inheritance, because three decades of iso RPGs taught players to *read* encounters that way. **Lesson:** the isometric tradition persists as an interaction language even when every rendering constraint that created it is gone. What you are really learning in this module is that language: legible space, ground-plane picking, depth without ambiguity — portable to any renderer you will ever use.

> ✅ **Best practice** — When studying a reference game, extract the *constraint* that produced its technique, not the technique alone. Pre-rendered sprites answered 1996 hardware; assembly answered 1999 CPUs; walls-down answered The Sims' interior camera problem. Your project inherits the answers only where it shares the constraints — Relax Room shares The Sims' constraint (interior visibility) and Unpacking's (expressive placement), not Diablo's (dungeon scale).

---

## 20. Room-based isometric design for companion apps (case study)

> 📦 **Case study — Relax Room.** This closing section consolidates the module's Relax Room threads into one architectural argument: why a desktop companion should be a *room-based* isometric-family app, and how the pieces studied in Sections 1-19 assemble into that shape.

### 20.1 Room-based vs open-world isometric

| Feature | Room-based | Open world |
|---|---|---|
| Map size | fixed (one screen or few) | large, scrollable |
| Camera | none or minimal pan (16) | follow + limits + zoom (16) |
| Loading | instant, whole-scene | chunk streaming (18.2) |
| Depth sorting | one shallow y-sort pool (7) | banded, bucketed, culled (8, 18) |
| Pathfinding | trivial or none (15.3) | grid/nav infrastructure (14-15) |
| Memory & CPU | tiny, near-zero idle | proportional to view + sim |
| Content model | curated catalog per room | procedural/streamed world |
| Exemplars | The Sims rooms, Habbo, Unpacking, Into the Breach | Diablo, Age of Empires, SC2000 |
| **Relax Room** | **this column, deliberately** | — |

Every row of the left column deletes a system this module taught you to build. That is the point: **room-based design is the aggressive application of scope discipline to the isometric formula**, keeping the emotionally load-bearing parts (a legible diorama, expressive placement, characters inhabiting the space) while deleting the infrastructure that exists only to serve scale.

### 20.2 Why room-based fits a desktop companion

1. **The window is small and shared.** A companion app lives beside the user's real work at modest size; a single room fills that frame with meaning, where an open world would render as an illegible sliver.
2. **The loop is decoration, not traversal.** Sessions are minutes of rearranging, not hours of exploring; one dense, ownable space beats many shallow ones (Unpacking's lesson, 19.9).
3. **Idle cost is the primary budget.** Section 18.4's inverted goal — near-zero resting consumption — is structurally guaranteed by a static single-view scene and merely *hoped for* in a streaming world.
4. **Production reality.** One artist can furnish one room to a high standard: a catalog of dozens of decorations at consistent scale, light and palette (17.4). The same effort spread over an open world yields visible thinness everywhere.

### 20.3 The architecture, assembled

The room-based pattern as a component diagram — each component annotated with the section that specified it:

```
┌────────────────────────── Room scene ───────────────────────────┐
│  WindowBackground (z=-20)  8-layer parallax sky/city            │
│    │        window_background.gd — depth WITHOUT projection      │
│  WallRect / FloorRect (z=-10)  theme-tinted flat planes (11.1)  │
│  RugBand (z=-5)          floor decals under everything (8.1)    │
│  ┌──────────── Decorations + Character (z=0) ────────────────┐  │
│  │  y_sort_enabled = true      (7.2)                         │  │
│  │  every origin at ground contact  (7.3)                    │  │
│  │  drop pipeline: pick → zone check → snap → overlap check  │  │
│  │     (5.3)      (11.1)       (11.2)        (11.3)          │  │
│  └───────────────────────────────────────────────────────────┘  │
│  Ambient VFX (z=+20)      dust, light shafts — optional         │
└─────────────────────────────────────────────────────────────────┘
        ▲ reads                              ▲ writes
┌───────┴─────────┐   ┌────────────┐   ┌─────┴────────┐
│ decorations.json│   │ GameManager │   │ SaveManager  │
│ catalog: id,    │   │ themes,     │   │ persisted    │
│ zone, scale,    │   │ palettes    │   │ layout:      │
│ price, sprite   │   │ per room    │   │ id+position  │
└─────────────────┘   └────────────┘   └──────────────┘
```

Note what is *absent*: no TileMapLayer, no AStarGrid2D, no Camera2D, no chunking. Each absence is a Section 15.3/16.4/18-style decision with a documented upgrade path, not an omission.

The parallax window deserves a highlight because it shows depth-craft transferring outside the projection entirely: `window_background.gd` layers eight sky/skyline planes moving at graded factors behind the window frame — depth from *motion parallax* instead of from diamonds, at a fraction of the cost. Depth cues are a toolbox (occlusion, elevation offset, shadows, parallax); the diamond grid is only one tool in it.

### 20.4 Room transitions and theming

Multiple rooms (bedroom, study, garden…) in a room-based app are *reconfigurations of one scene*, not separate worlds:

```gdscript
# Relax Room's transition — clear, retheme, respawn, reposition:
func change_room(room_id: String, theme: String) -> void:
    # 1. Clear current decorations
    for child in decorations_node.get_children():
        child.queue_free()

    # 2. Update wall/floor colors from the theme palette
    var colors := GameManager.get_theme_colors(room_id, theme)
    wall_rect.color = Color(colors.get("wall", "#2a2a3e"))
    floor_rect.color = Color(colors.get("floor", "#3a3a4e"))

    # 3. Re-instantiate decorations from save data
    for deco_data: Dictionary in SaveManager.decorations:
        _spawn_decoration(deco_data)

    # 4. Reset character position
    character.position = Vector2(640, 500)
```

The sequence encodes the architecture's core invariant one final time: *the room is a pure function of data* — catalog + theme + save. Because rebuild-from-data is the only construction path (there is no hand-edited room state to preserve), transitions, save-loading, and even a hypothetical "share your room" export all reuse the same four steps. Persistence mechanics for `SaveManager` live in [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md).

Theming — wall/floor tints from a per-room palette dictionary — is the room-based answer to open-world biomes: cheap variety through *recoloring* rather than re-authoring, which works precisely because Section 17.4's palette discipline kept decoration sprites theme-neutral.

### 20.5 The isometric upgrade path

If Relax Room (or your own companion app) later wants the full diamond look, the module's map for that migration, in dependency order:

1. **Floor becomes a `TileMapLayer`** (`TILE_SHAPE_ISOMETRIC`, `TILE_LAYOUT_DIAMOND_DOWN`, 64×32) under the existing decoration band — purely visual at first (10.1).
2. **Snap function swaps** from `Helpers.snap_to_grid()` to `cell_center(pick_cell(...))` — the two-line change Section 11.4 promised; the drop pipeline, catalog and saves are untouched (saves gain a cell field alongside position).
3. **Furniture art migrates** to 2:1 iso sprites against the 17.5 template, category by category — flat and iso decorations can coexist during the transition since both obey origin discipline.
4. **Occupancy replaces overlap-ratio** (11.3 → footprint cells in an occupancy set), enabling…
5. **Grid pathfinding for the character** (`AStarGrid2D`, 14) and, with it, click-to-walk and NPC visitors.
6. **Walls rise last** — north/west wall tiles with per-tile y-sort (10.3), keeping the structural-cutaway convention so occlusion handling stays unnecessary (9.3).

Each step ships independently. That property — *an incremental path from flat room to full isometric with no rewrites* — is the final examination of everything this module taught: it exists only because logic and projection were kept separate from the first line of code.

---

## Best practices

**Math and coordinates**

- Keep tile coordinates as the single source of truth; derive screen positions, never the reverse (§1, §3).
- Implement the transforms once, in a static `class_name` helper, and round-trip-test them before any scene work (§3.4).
- Convert mouse input screen→world→tile, letting `get_global_mouse_position()` handle the camera; never feed raw event positions to the inverse transform (§4.1).
- Use `floori` on fractional tile coordinates for cell assignment; reserve rounding for snap-to-center operations (§3.4, §5.1).

**Sorting**

- Enforce ground-contact origins as an asset-pipeline contract (template scenes, authoring guides), not as per-scene fixes (§7.3, §17.5).
- Structure scenes as z_index bands (decals below, sorted world at 0, canopies above) with y-sort only inside the interleaving band (§8.1).
- Give multi-tile objects a front-corner anchor first; escalate to splitting, then topological sorting, only on visible artifacts (§8.3-8.5).
- Never fix sorting by nudging `position`; bias `y_sort_origin` or restructure origins instead (§7.4).

**World building and movement**

- Structure is tiles, objects are scenes; let TileMapLayer own repetition and physics/nav baking, scenes own behavior (§10.5).
- Put tile semantics (walkable, cost) in TileSet custom data and derive pathfinding state from it through one service (§10.4, §14.1).
- Use `Input.get_vector()` for movement input — it solves diagonal speed and analog deadzones in one call (§12.2).
- Match `diagonal_mode` to your art (corner-safe: `DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES`) and heuristic to your movement rules (8-dir: `HEURISTIC_OCTILE`) (§14.2-14.3).

**Presentation**

- Nearest filtering project-wide, integer zoom steps, whole-pixel shake offsets — the pixel grid is sacred or it is gone (§16.3-16.4, §17.3).
- Author pixel art at 1× from layered sources; export splits (trunk/canopy) from layers, atlas per category in the build (§17.5, §18.3).
- Sort only what interleaves; keep floors on unsorted, quadrant-batched layers (§18.1).
- For companion apps, design for near-zero idle: static view, capped fps, quiescent scenes (§18.4, §20).

---

## Common errors & troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Picking selects a tile one row off along two diamond edges | `roundi` used instead of `floori` when converting fractional tile coords to cells | use `floori` per axis (§3.4); reserve rounding for snapping to cell centers |
| Picking is correct at zoom 1 but drifts when the camera moves or zooms | raw `event.position` (screen space) fed into the inverse transform | use `get_global_mouse_position()`, then subtract the map origin (§4.1) |
| Everything mirrors / walking north renders as south-east | sign error in one matrix entry of the transform pair | round-trip unit test the helper class; compare against §3.2's table |
| Character's head clips through furniture they stand in front of | sprite origin centered instead of at ground contact | move origin to feet; offset artwork upward (§7.3) |
| Two static props flicker order between frames | identical y sort keys, order falling back to unstable incidental order | offset one origin ≥1 px, or separate them into z_index bands (§9.4) |
| Long wall or fence sorts wrong at one end only | multi-tile footprint anchored on a single tile | split per tile / build walls as tiles; topological sort as last resort (§8.3-8.4) |
| Rug or shadow draws on top of characters | decal competing inside the y-sorted band | move decals to a lower `z_index` band, e.g. −5 (§8.1) |
| Tall wall/terrain tiles sink into the floor | `TileData.texture_origin` left at default for oversized tile art | set per-tile `texture_origin` so the art base aligns with the cell (§10.1) |
| Wall tiles don't interleave with the player at all | layer's `y_sort_enabled` still false (floors-only default copied) | enable y-sort on the wall layer and on the shared parent (§7.2, §10.3) |
| Diagonal movement 41% faster than straight | composing raw axes without length clamping | `Input.get_vector()` or normalize the composed vector (§12.2) |
| Grid character plays side-walk animation when stepping north | facing derived from screen angle in a 2:1 world | derive facing from tile-space `delta_cell` for stepped movement (§13.2) |
| NPCs path through freshly placed furniture | occupancy changed without updating the grid | route all placement through one service that calls `set_point_solid` (§14.1) |
| Paths clip through wall corners diagonally | `DIAGONAL_MODE_ALWAYS` with solid-flanked diagonals | `DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES` (§14.2) |
| Weighted "road" tiles ignored by the pathfinder | `jumping_enabled = true` bypasses weight scales | disable jumping on weighted maps — the two are exclusive (§14.3) |
| `map_to_local` results don't match global mouse checks | layer local space compared against global coordinates | wrap with `to_global()` / `to_local()` at the boundary (§3.5) |
| Pixel art shimmers/crawls during camera pan or zoom | fractional zoom, or linear filtering, or non-integer shake offsets | integer zoom steps (§16.3), nearest filter (§17.3), snapped shake (§16.4) |
| Tile seams: thin grout lines or doubled dark edges between diamonds | mixed tile vertex conventions or AA on boundary edges | enforce the 2px/1px vertex rule; ban boundary AA (§17.2-17.3) |
| Frame cost spikes when many actors move | one giant y-sort pool including static floors and props | unsorted floor layers; static vs dynamic sorted parents; shallow pools (§18.1) |
| Camera slams at map edges during smoothed follow | hard limits with smoothing enabled | `limit_smoothed = true`; fit limits from projected corners (§16.1) |
| Elevated/jumping entity picks and sorts wrong | elevation folded permanently into `position.y` | store `(grid_pos, elevation)` as truth; derive position; sort by ground shadow (§6) |
| Ghost preview disagrees with where the item actually lands | preview and confirm paths use different pick/snap code | derive both from the same `pick_cell`/validity functions (§5.4-5.5) |
| Saved room loads shifted after an art or tile-size update | projected pixel positions persisted instead of logical coordinates | save cells/logical coords, derive positions on load; version the format (§4.5) |
| Sprites parented under a §3.6 iso container render squashed | container's sheared basis also transforms child textures | keep sprites outside; use the container for vector drawing and markers only (§3.6) |

---

## Exercises

Each lab states acceptance criteria you can verify objectively, plus a stretch goal. Labs 1-2 are paper-first (from the original module — do them before touching the editor); the rest build on each other toward a small iso sandbox. Set up a fresh Godot 4.5 project with nearest filtering and a 64×32 diamond template before Lab 3.

### Lab 1 — Coordinate conversion on paper

Using tile size 64×32 and the inverse transform from §3.3, convert screen position `(640, 360)` (center of a 1280×720 viewport, map origin at the viewport origin) to fractional tile coordinates by hand. Note: this lab descends from the original module's exercise, whose printed formula divided full tile sizes by an extra 2 and reported `(10.625, 0.625)` — verifying why that was wrong is part of the lab.

- **Acceptance:** applying `tx = sx/W + sy/H` and `ty = sy/H − sx/W` you obtain `tx = 640/64 + 360/32 = 21.25` and `ty = 360/32 − 640/64 = 1.25`, i.e. cell `(21, 1)` — and you confirm the half-size spelling `(sx/(W/2) + sy/(H/2))/2` gives the identical result.
- **Acceptance:** you state that cell `(21, 1)` is *invalid* for a 10×10 grid anchored at the viewport origin, and explain the correct remedy: translate the map origin (e.g. center the diamond in the viewport) rather than bend the transform (§4.2).
- **Acceptance:** you identify the error in the legacy formula (`(sx/W + sy/H)/2` mixes the full-size and half-size spellings, halving both outputs) — a sign-and-scale audit exactly like the one §3.4's round-trip test automates.
- **Stretch:** repeat with the map origin at `(640, 100)`; show that subtracting the origin first yields fractional tile `(4.0625, ...)`-range values landing inside the 10×10 grid, and give the cell.

### Lab 2 — Draw order on paper

Four decorations occupy tiles: bed `(2,3)`, desk `(4,1)`, plant `(2,5)`, chair `(4,3)`.

- **Acceptance:** you produce the correct back-to-front paint order by depth row `tx + ty`: desk and bed first (both row 5 — a genuine tie needing a tie-break rule), then chair and plant (both row 7 — a second tie). Show all four `tx + ty` values and state your tie-break (by x, or stable id — §8.2, §9.4); note that the legacy answer sorted by `ty` alone, which orders desk before bed but cannot justify chair-vs-plant.
- **Acceptance:** you can state what Godot mechanism produces this order automatically and which node property is the sort key (`y_sort_enabled`, origin y — §7).
- **Stretch:** design the tile layout of an 8×6 room on paper — bed 2×1 in the top-right area, desk 1×2 along the left wall, plants in visible corners — choosing each multi-tile object's anchor cell and justifying it with §8.3's front-corner rule.

### Lab 3 — The projection helper, tested

Implement `IsoProjection` (§3.4) with `tile_to_screen`, `screen_to_tile`, `screen_to_cell`, `cell_center`, `tile_to_screen_3`.

- **Acceptance:** a test script asserts round-trip equality for ≥8 vectors including negatives and fractional values, and asserts the §3.2 table values exactly.
- **Acceptance:** the vertical line below the map origin behaves correctly: `screen_to_cell(Vector2(0, 31)) == Vector2i(0, 0)` but `screen_to_cell(Vector2(0, 33)) == Vector2i(1, 1)` — explain geometrically (the segment from the top vertex `(0,0)` down to `(0,32)` is the vertical diagonal of cell `(0,0)`'s diamond, whose bottom vertex is tile `(1,1)`).
- **Stretch:** add `cells_in_screen_rect(rect: Rect2) -> Array[Vector2i]` returning all cells whose diamonds intersect a screen rectangle (needed later for culling), with its own tests.

### Lab 4 — Diamond field with hover cursor

Render a 10×10 diamond grid (either a `TileMapLayer` configured per §10.1, or 100 `Sprite2D` diamonds placed via `cell_center`) with a hover highlight driven by `pick_cell` (§5.4).

- **Acceptance:** the highlight tracks the mouse with no offset error at every edge and corner tile, including after you move the map node to a non-zero position.
- **Acceptance:** with a `Camera2D` added and zoom set to 2, picking still lands correctly (proves §4.1's conversion chain).
- **Stretch:** click to toggle tiles "blocked", tinting them red — you are building Lab 7's obstacle editor.

### Lab 5 — Sorted room with origin discipline

Build a room scene: unsorted floor, y-sorted band containing 6+ props of varying heights (at least one tall bookshelf), a rug on a lower z_index band, and a placeholder character moving with `Input.get_vector()` (§12.2).

- **Acceptance:** walking a full circle around every prop shows correct occlusion at every angle; the rug never covers feet.
- **Acceptance:** a debug overlay draws each sorted node's origin cross at its visual ground contact (§9.4) — submit a screenshot showing all crosses at feet.
- **Stretch:** add a tree with an overhanging canopy split into trunk + canopy sprites (§9.2) and demonstrate standing south-east of the trunk: in front of the trunk, behind the canopy.

### Lab 6 — 8-direction character

Give the Lab 5 character an 8-direction walk/idle set (place-holder art acceptable: 5 drawn directions + 3 flips) using the sector-plus-hysteresis mapper (§13.2).

- **Acceptance:** slowly rotating the input direction through 360° produces exactly 8 clean facing changes with no flicker at sector boundaries.
- **Acceptance:** releasing input keeps the last facing's idle; asymmetric marker on the character (a satchel) visibly mirrors on flipped directions — state whether your design tolerates it (§13.1).
- **Stretch:** switch the character to grid-stepped movement (§12.4) and drive facing from `delta_cell` instead of velocity; verify the §13.2 pitfall (north step ≠ side animation).

### Lab 7 — Click-to-move with AStarGrid2D

Wire §14's `NavGrid` to Lab 4's grid: walkability from blocked tiles (or TileSet custom data if you used a TileMapLayer), `DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES`, octile heuristics, and the click-walker from §14.4.

- **Acceptance:** clicking any free tile walks the character there along a sensible path; clicking a blocked tile with `allow_partial_path` walks to the nearest reachable tile.
- **Acceptance:** blocking a tile *while* the character is en route causes a visible re-plan without walking through the new obstacle (§14.4's revalidation).
- **Acceptance:** demonstrate the corner-clip difference by temporarily switching to `DIAGONAL_MODE_ALWAYS` beside an L-shaped wall and back.
- **Stretch:** paint three "road" tiles with `weight_scale 0.5` and three "mud" tiles with `3.0`; show two screenshots where the chosen path detours exactly as the weights predict — then enable `jumping_enabled` and document what breaks (§14.3).

### Lab 8 — Elevation and shadow

Add a raised platform (2 elevation units) to the sandbox using `tile_to_screen_3` (§6.1), and make the character jump with a tweened `elevation` while its ground shadow stays planted (§6.3).

- **Acceptance:** the platform's diamonds align pixel-perfectly with ground tiles one row behind (`ELEVATION_STEP = H/2` check).
- **Acceptance:** during a jump, y-sort order against nearby props never changes (sorting follows the shadow, not the body).
- **Stretch:** implement elevation-aware picking: clicking the platform's top surface selects the platform cell, not the hidden ground cell behind it (§6.1's highest-first policy).

### Lab 9 — Occlusion fade and camera polish

Add one tall wall segment the character can walk behind; implement transparency-on-overlap (§9.3). Add a `Camera2D` with projected-corner limits, smoothed follow, integer zoom steps, and pixel-snapped trauma shake (§16).

- **Acceptance:** the wall fades to ~45% alpha within 150 ms of the character entering its silhouette zone and restores on exit.
- **Acceptance:** zooming through 1×-4× during a pan shows zero shimmer; shake on a test keypress never produces sub-pixel crawl.
- **Stretch:** replace the fade with a silhouette pass: a flat-color duplicate of the character visible only where covered (§9.3, option 2 — pairs with [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md)).

### Lab 10 — Capstone: the Relax Room upgrade, step 1-2

Perform the first two steps of §20.5 on a copy of a flat room (your own Lab 5 room stands in if you don't have the Relax Room project): put an isometric `TileMapLayer` floor under the sorted band, and reroute the decoration drop pipeline through `cell_center(pick_cell(...))` while leaving catalog and save format untouched.

- **Acceptance:** existing saved layouts still load (positions map onto nearest cells); new drops land on cell centers with a diamond ghost preview that is green on free cells and red on occupied ones.
- **Acceptance:** a written diff summary shows the change touched only the snap/placement path — zero changes in save/catalog code (the §11.4 promise, verified empirically).
- **Stretch:** add occupancy tracking (footprint cells per decoration) and reject drops on occupied cells, replacing the overlap-ratio check (§20.5 step 4).

### Self-assessment

Answer from memory, then verify against the sections cited:

1. What angle does 2:1 pixel isometric actually use, and why not 30°? (§2.2-2.3)
2. Write both directions of the transform for W=64, H=32 without looking. (§3.2-3.3)
3. Give one concrete scene y-sort cannot order correctly and name two escalation options. (§7.4, §8.3)
4. Why does `Input.get_vector()` beat two `get_axis` calls plus `normalized()`? (§12.2)
5. Which `AStarGrid2D` settings prevent corner clipping, and which feature silently disables weights? (§14.2-14.3)
6. SimCity 2000 vs Diablo: how did each fake its third dimension, and which technique does your current project need? (§19.2-19.3, §6)

---

## Further reading

**Official documentation (verify everything here first)**

- [Godot Docs — Using TileMaps](https://docs.godotengine.org/en/stable/tutorials/2d/using_tilemaps.html) — painting, terrain sets, and layer workflow; the isometric options live in the TileSet inspector described here.
- [Godot Docs — TileSet class reference](https://docs.godotengine.org/en/stable/classes/class_tileset.html) — authoritative for `TILE_SHAPE_ISOMETRIC`, the six `TileLayout` values, custom data layers (§10.1, §10.4).
- [Godot Docs — TileMapLayer class reference](https://docs.godotengine.org/en/stable/classes/class_tilemaplayer.html) — cell API, `map_to_local`/`local_to_map`, per-layer `y_sort_origin`, `x_draw_order_reversed` (§10.2-10.3).
- [Godot Docs — AStarGrid2D class reference](https://docs.godotengine.org/en/stable/classes/class_astargrid2d.html) — the isometric cell shapes, diagonal modes, heuristics and jumping caveats used throughout §14.
- [Godot Docs — AStar2D class reference](https://docs.godotengine.org/en/stable/classes/class_astar2d.html) — graph API and the `_compute_cost`/`_estimate_cost` virtuals (§15.1).
- [Godot Docs — NavigationAgent2D class reference](https://docs.godotengine.org/en/stable/classes/class_navigationagent2d.html) and the 2D navigation overview — the mesh-based third option (§15.2).
- [Godot Docs — Camera2D class reference](https://docs.godotengine.org/en/stable/classes/class_camera2d.html) — limits, smoothing, drag margins, zoom (§16).
- [Godot Docs — 2D coordinate systems and canvas layers / CanvasItem](https://docs.godotengine.org/en/stable/tutorials/2d/canvas_layers.html) — the z_index/y-sort rendering model behind §7-8.
- [Godot Docs — 2D movement overview](https://docs.godotengine.org/en/stable/tutorials/2d/2d_movement.html) — `Input.get_vector`, `CharacterBody2D` patterns underlying §12.
- [Godot Docs — Matrices and transforms](https://docs.godotengine.org/en/stable/tutorials/math/matrices_and_transforms.html) — the `Transform2D` theory behind §3.2 and §3.6.

**Isometric craft (community classics)**

- [Pixel Parmesan — Fundamentals of Isometric Pixel Art](https://pixelparmesan.com/blog/fundamentals-of-isometric-pixel-art) — the 2:1 stepping rules, tile vertex conventions and shading discipline of §17, from a working pixel artist.
- [SLYNYRD Pixelblog 41 — Isometric Pixel Art](https://www.slynyrd.com/blog/2022/11/28/pixelblog-41-isometric-pixel-art) — tile construction walkthroughs and palette ramps; excellent visual companion to §17.2-17.4.
- [Pixelbath — Isometric Pixel Art Guide](https://www.pixelbath.com/isometric-pixel-art-guide/chapter-2-basic-pixel-art/) — line families and clean-edge practice drills (§17.1).
- [Screaming Brain Studios — Isometric Grids](https://screamingbrainstudios.com/isometric-grids/) — grid templates and the 26.565° derivation with diagrams (§2.3).
- Clint Bellanger, *Isometric Tiles Math* (widely mirrored) — a compact independent derivation of §3's transforms; good second opinion when debugging signs.
- Amit Patel, *Red Blob Games* — the grid/pathfinding articles (A*, heuristics, grid geometry) behind §14's tuning advice; the hex pages illuminate §4.3's staggered-parity problem.

**Sibling modules**

- [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) — the canvas rendering model, lights and materials that §7-9 build on.
- [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md) — baseline TileSet/TileMapLayer mechanics assumed by §10.
- [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) — import settings, `SpriteFrames`, atlas workflow (§13.3, §17.5).
- [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md) — silhouette and tint shaders for §9.3's occlusion options.
- [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) — the idle-cost budget of §18.4 in full.
- [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) — Relax Room's complete architecture, of which §11 and §20 are the isometric-relevant slice.
- [VISUAL_SYSTEMS_SUMMARY.md](VISUAL_SYSTEMS_SUMMARY.md) — Phase 2 recap connecting this module to its siblings.

---

## Glossary

| Term | Definition |
|---|---|
| **Axonometric projection** | Family of parallel projections (isometric, dimetric, trimetric) showing multiple faces of an object with no perspective convergence (§2.1). |
| **Isometric (true)** | Axonometric projection with all three axes equally foreshortened, 120° apart on screen, ground axes at 30°; pixel-hostile slope 1:√3 (§2.2). |
| **Dimetric** | Axonometric projection with two axes sharing one foreshortening; the 2:1 pixel-art standard at arctan(½) ≈ 26.565° is dimetric (§2.3). |
| **Trimetric** | Axonometric projection with all three axes foreshortened differently; mostly seen in pre-rendered art (§2.4). |
| **Oblique projection** | Parallel projection keeping the front face undistorted and slanting the depth axis; the "flat room" cheat used by Relax Room's presentation (§2.4). |
| **2:1 tile** | Diamond tile whose width is exactly twice its height (32×16, 64×32, 128×64); the atom of pixel-art isometric (§2.3, §4.4). |
| **Cart↔iso transform** | The 2×2 linear map (and its inverse) between tile coordinates and screen positions; `sx=(tx−ty)·W/2`, `sy=(tx+ty)·H/2` (§3). |
| **Tile / world / screen space** | The three coordinate systems of an iso project: logical grid, Godot's global 2D pixels, and viewport pixels under the camera transform (§4.1). |
| **Diamond layout** | Grid linearization whose axes run along diamond edges; uniform neighbor offsets; Godot's `TILE_LAYOUT_DIAMOND_*` (§4.3). |
| **Staggered layout** | Grid linearization with half-offset alternating rows; rectangular silhouette but parity-dependent neighbors (§4.3). |
| **Picking** | Converting a pointer position to the tile or object under it; in iso, the inverse transform plus `floor` is an exact diamond hit test (§5). |
| **Elevation faking** | Rendering logical height `z` as a pure screen y-offset (`−z·STEP`) while logic stays on the ground tile (§6). |
| **Painter's algorithm** | Producing correct occlusion by drawing back-to-front in depth order — the foundation of all 2D iso sorting (§7.1). |
| **Y-sort** | Ordering canvas items by global y of their origins; Godot's `CanvasItem.y_sort_enabled`, nesting across parents (§7.2). |
| **Origin discipline** | The contract that every sorted sprite's node origin sits at its ground contact point, making y a valid depth key (§7.3). |
| **z_index band** | Coarse draw-order layer (`CanvasItem.z_index`) reserved for a content class (decals, world, canopies); fine order via y-sort within (§8.1). |
| **Topological sorting (sprites)** | Deriving draw order from pairwise "A behind B" footprint relations via DFS over the occlusion DAG — the general fix for multi-tile objects (§8.4). |
| **Sprite splitting** | Cutting one object into separately sorted canvas items along its occlusion boundaries (trunk/canopy, per-tile wall columns) (§9.2). |
| **Walk-behind occlusion** | UX handling for actors hidden by correct sorting: fade, silhouette shader, or structural cutaway (§9.3). |
| **`TileMapLayer`** | Godot 4.3+ single-layer tile node; isometric behavior comes from its `TileSet`'s `tile_shape`/`tile_layout`; per-tile y-sort when enabled (§10). |
| **`texture_origin`** | Per-tile `TileData` offset aligning oversized tile art (tall walls) with its cell (§10.1). |
| **Custom data layer** | Typed per-tile metadata in a TileSet (walkable, move_cost) — the paint-time source of gameplay semantics (§10.4). |
| **Hidden-grid placement** | Free-feeling placement snapped to a fine grid (Relax Room's 8 px; Unpacking) — alignment without visible tiles (§11.2). |
| **Diagonal speed bug** | 41% overspeed on diagonals from composing unit axes without clamping; solved by `Input.get_vector()` (§12.2). |
| **Direction set** | The drawn facing directions of a character (4/5+flip/8/16); a production budget as much as an art style (§13.1). |
| **`AStarGrid2D`** | Godot's grid A* with native isometric cell shapes, diagonal modes, octile/Manhattan/Chebyshev/Euclidean heuristics, weights and jumping (§14). |
| **Weight scale** | Multiplier on the cost of entering a cell/point (`set_point_weight_scale`); >1 discourages, <1 attracts; ignored when jumping is enabled (§14.3). |
| **Navigation mesh** | Polygonal walkable-area representation served by `NavigationServer2D` and followed by `NavigationAgent2D`; the free-movement alternative to grids (§15.2). |
| **Line stepping** | The fixed pixel patterns of clean iso edges: 2:1 steps, verticals, 45° stairs — and nothing else (§17.1). |
| **Room-based design** | Building the game as one fixed-view decorated room rather than a scrolling world; scope-disciplined isometric for companion apps (§20). |

---

*Module 07 · Phase 2 — Visual systems · "Godot 4 in Production"*
*Case study: Relax Room — IFTS Projectwork 2026 · Author: Renan Augusto Macena (System Architect & Project Supervisor)*

