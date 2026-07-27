---
course: "Godot 4 in Production"
phase: "2 — Visual systems"
module: "06"
title: "Visual Systems Summary — Decision Guide for the 2D Stack"
version: "Godot 4.5 / GDScript 2.0"
level: "Intermediate"
prerequisites:
  - "SPRITES_AND_TEXTURES.md"
  - "RENDERING_AND_VISUAL_LOGIC.md"
  - "TILES_AND_TILEMAPS.md"
objectives:
  - "Choose the correct node for any 2D visual requirement using the decision trees, in under a minute"
  - "Predict the final draw order of any scene by applying the four ordering mechanisms in their priority order"
  - "Select the cheapest adequate technique (modulate, tween, shader, particles) for a given effect using the cost tables"
  - "Trace one 2D frame from SceneTree to GPU and name where each visual mechanism hooks into the pipeline"
  - "Justify GPUParticles2D vs CPUParticles2D for a given target platform and effect"
  - "Implement any of the 22 quick recipes and cite which deep module documents each one"
  - "Audit a scene for draw-call, y-sort and texture-memory hotspots using the performance cheat-sheet"
tags: [godot, gdscript, 2d, rendering, sprites, tilemap, draw-order, shaders, particles, performance, decision-guide, relax-room]
---

# Visual Systems Summary — Decision Guide for the 2D Stack — Complete Guide

> **Module 06** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Sprites and Textures](SPRITES_AND_TEXTURES.md), [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md), [Tiles and Tilemaps](TILES_AND_TILEMAPS.md) — plus [Scenes and Nodes](SCENES_AND_NODES.md) for tree fundamentals.
>
> By the end of this module you will be able to:
> 1. Pick the right node for any 2D visual requirement (static image, grid, animation, procedural drawing, UI) using the decision trees — without opening the class reference.
> 2. Predict the on-screen draw order of any scene by applying tree order, `z_index`, Y-sort and `CanvasLayer` in the correct priority.
> 3. Choose the cheapest technique that achieves a visual effect, using the comparison tables with their cost columns.
> 4. Narrate what happens in one rendered 2D frame — from `SceneTree` traversal through `RenderingServer` to GPU draw calls — and say where each mechanism (modulate, shaders, particles, `_draw()`) plugs in.
> 5. Decide between `GPUParticles2D` and `CPUParticles2D`, and between particles, shaders and tweens, for a given effect.
> 6. Apply the recipe index to solve 22 recurring "how do I…" visual problems, and know which sibling module holds the deep version.
> 7. Run a first-pass performance audit of a 2D scene (draw calls, batching breaks, y-sort cost, texture memory) before reaching for the profiler.
>
> **Estimated time:** 4-6 hours for a full read · minutes per lookup afterwards · **Level:** Intermediate

This module is deliberately different from its siblings. Modules [03](SPRITES_AND_TEXTURES.md), [04](RENDERING_AND_VISUAL_LOGIC.md), [05](TILES_AND_TILEMAPS.md), [07](ISOMETRIC_GAMES.md) and [12](SHADERS_GDSHADER.md) each teach **one component** of the 2D visual stack in depth. This module teaches **the joints between them**: which tool to reach for, in what order things draw, what each choice costs, and where to go for the full treatment. Treat it as the page you keep open while building.

## Guiding ideas

1. **Pick the node by the problem shape, not by habit** — one image, a grid, a flipbook, a procedural shape and a UI panel are five different problems with five different best nodes.
2. **Draw order has exactly four levers, applied in a strict priority** — `CanvasLayer` beats `z_index`, `z_index` beats Y-sort, Y-sort beats tree order. Memorize the priority once and every "why is this behind that?" bug becomes mechanical.
3. **Reach for the cheapest technique that works** — `modulate` before tween, tween before shader, shader before particles, particles before a `SubViewport`. Escalate only when the cheaper tool visibly fails.
4. **The renderer is a server, not your scene tree** — nodes are a convenient authoring facade; `RenderingServer` owns the canvas items that actually draw. Understanding that split explains caching (`_draw()`), batching, and why hidden nodes still cost memory.
5. **Every visual decision is also a performance decision** — a per-instance `ShaderMaterial` breaks batching, Y-sort re-sorts every frame, particles allocate GPU buffers. The cheat-sheet in this module puts numbers and rules of thumb on each.
6. **Relax Room chooses simplicity on purpose** — one painted background, free `Sprite2D` decorations, no TileMap, manual layering. The case study shows that "less machinery" is a valid, defensible stack for a desktop companion app.

## Concept map

```
                            ┌───────────────────────────────────────┐
                            │        THE GODOT 4 2D VISUAL STACK    │
                            │        (what this module unifies)     │
                            └───────────────────┬───────────────────┘
                                                │
        ┌──────────────┬───────────────┬────────┴────────┬────────────────┬───────────────┐
        │              │               │                 │                │               │
 ┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼───────┐ ┌───────▼───────┐ ┌──────▼───────┐ ┌─────▼─────┐
 │  CONTENT    │ │  ORDERING  │ │   MOTION     │ │   EFFECTS     │ │  DELIVERY    │ │  BUDGET   │
 │  what draws │ │ what's on  │ │ what changes │ │ how it looks  │ │ how it gets  │ │ what it   │
 │             │ │    top     │ │  over time   │ │   special     │ │  to screen   │ │   costs   │
 ├─────────────┤ ├────────────┤ ├──────────────┤ ├───────────────┤ ├──────────────┤ ├───────────┤
 │ Sprite2D    │ │ tree order │ │ AnimatedSpr. │ │ modulate      │ │ SceneTree    │ │ draw calls│
 │ TextureRect │ │ z_index    │ │ AnimPlayer   │ │ self_modulate │ │ CanvasItem   │ │ batching  │
 │ TileMapLayer│ │ y_sort_    │ │ Tween        │ │ CanvasModulate│ │ Rendering-   │ │ y-sort    │
 │ Animated-   │ │   enabled  │ │ SpriteFrames │ │ ShaderMaterial│ │   Server     │ │ overdraw  │
 │   Sprite2D  │ │ CanvasLayer│ │ Particles    │ │ GPU/CPU       │ │ Viewport /   │ │ texture   │
 │ Line2D /    │ │ (y_sort_   │ │ _process +   │ │   Particles2D │ │   SubViewport│ │   memory  │
 │  Polygon2D  │ │  origin,   │ │  queue_      │ │ Light2D /     │ │ draw calls   │ │ shader    │
 │ _draw()     │ │  isometric │ │  redraw()    │ │  CanvasGroup  │ │ GPU raster   │ │   cost    │
 │ Control/UI  │ │  sort M07) │ │ Parallax2D   │ │ hint_screen_  │ │ present      │ │ particle  │
 │ NinePatch   │ │            │ │              │ │   texture     │ │              │ │   cost    │
 └──────┬──────┘ └─────┬──────┘ └──────┬───────┘ └───────┬───────┘ └──────┬───────┘ └─────┬─────┘
        │              │               │                 │                │               │
   Module 03,05   Module 04,07    Module 03,04       Module 04,12    Module 04 (§pipeline)│
   (+ 02 tree)    (this: §5)      (this: §4)         (this: §8,10)   (this: §9)      Module 14
                                                                                  (this: §12)
```

Read the map top-down when designing ("what content, in what order, moving how, styled how?") and bottom-up when debugging ("this costs too much — which column produced it?").

## Table of contents

1. [How to use this module](#1-how-to-use-this-module)
2. [The 2D visual stack at a glance](#2-the-2d-visual-stack-at-a-glance)
3. [Decision trees — which node do I use?](#3-decision-trees--which-node-do-i-use)
4. [Master table — sprite and animation options](#4-master-table--sprite-and-animation-options)
5. [Master table — draw-order mechanisms](#5-master-table--draw-order-mechanisms)
6. [Master table — texture types](#6-master-table--texture-types)
7. [Master table — parallax options](#7-master-table--parallax-options)
8. [Master table — visual-effect techniques](#8-master-table--visual-effect-techniques)
9. [One frame in 2D — the render pipeline as a story](#9-one-frame-in-2d--the-render-pipeline-as-a-story)
10. [Particles essentials — GPU vs CPU](#10-particles-essentials--gpu-vs-cpu)
11. [Recipe index — how do I…](#11-recipe-index--how-do-i)
12. [Performance cheat-sheet for the 2D stack](#12-performance-cheat-sheet-for-the-2d-stack)
13. [Case study — the Relax Room visual stack](#13-case-study--the-relax-room-visual-stack)
14. [Glossary map — every concept to its owning module](#14-glossary-map--every-concept-to-its-owning-module)
15. [Best practices](#best-practices)
16. [Common errors & troubleshooting](#common-errors--troubleshooting)
17. [Exercises](#exercises)
18. [Further reading](#further-reading)
19. [Glossary](#glossary)

---

## 1. How to use this module

### 1.1 Three reading modes

| Mode | You are… | Read |
|------|----------|------|
| **Design mode** | starting a new scene, deciding the node stack | §3 decision trees → §4-8 tables to compare finalists → §13 to see a full worked stack |
| **Debug mode** | staring at a wrong-looking screen | [Common errors](#common-errors--troubleshooting) first → §5 for ordering bugs → §9 to reason about the pipeline |
| **Budget mode** | frame time or memory is climbing | §12 cheat-sheet → §8 cost column → [Module 14](DESKTOP_COMPANION_PERFORMANCE.md) for the profiler workflow |

### 1.2 Relationship to the sibling modules

This module **summarizes and cross-references**; it does not replace. Every section ends with a pointer to the module that owns the topic:

| Sibling module | Owns | This module gives you |
|----------------|------|----------------------|
| [Module 02 — Scenes and Nodes](SCENES_AND_NODES.md) | tree, lifecycle, `PackedScene`, node types | the tree as the *first* draw-order mechanism |
| [Module 03 — Sprites and Textures](SPRITES_AND_TEXTURES.md) | `Sprite2D`, `AnimatedSprite2D`, import, filtering, atlases | decision trees §3.1/§3.3, tables §4 and §6 |
| [Module 04 — Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) | `z_index`, `CanvasLayer`, `modulate`, `_draw()`, `Tween`, `Viewport`, Theme | tables §5 and §8, pipeline story §9 |
| [Module 05 — Tiles and Tilemaps](TILES_AND_TILEMAPS.md) | `TileSet`, `TileMapLayer`, terrains, tile physics | decision tree §3.2, tilemap rows in every table |
| [Module 07 — Isometric Games](ISOMETRIC_GAMES.md) | isometric projection, diamond tiles, iso Y-sort | the "isometric" branches of §3.2 and §5 |
| [Module 12 — Shaders (GDShader)](SHADERS_GDSHADER.md) | `canvas_item` shaders, uniforms, screen reads | the "shader" rows of §8 and half of §11's recipes |
| [Module 14 — Desktop Companion Performance](DESKTOP_COMPANION_PERFORMANCE.md) | profiling, monitors, budgets | §12 is the visual-stack front door to it |
| [Module 09 — Project Deep Dive](PROJECT_DEEP_DIVE.md) | the whole Relax Room codebase | §13 is its visual chapter in miniature |

### 1.3 Version pinning

Everything here targets **Godot 4.5 / GDScript 2.0**. Three renames matter constantly when you read older tutorials:

| Godot 3.x / early 4.x term | Godot 4.5 term | Since |
|----------------------------|----------------|-------|
| `TileMap` node (multi-layer monolith) | **`TileMapLayer`** — one node per layer | 4.3 (TileMap deprecated) |
| `ParallaxBackground` + `ParallaxLayer` | **`Parallax2D`** — one plain Node2D-style scroller per layer | 4.3 (old pair deprecated) |
| `YSort` node | **`y_sort_enabled`** property on any `CanvasItem` | 4.0 |
| `update()` (redraw request) | **`queue_redraw()`** | 4.0 |
| `SCREEN_TEXTURE` built-in (shaders) | **`hint_screen_texture`** uniform | 4.0 |

If a snippet you find online uses the left column, translate before pasting. [Module 05](TILES_AND_TILEMAPS.md) and [Module 12](SHADERS_GDSHADER.md) cover the migrations in detail.

### 1.4 The one-page cheat card

The whole module compressed to lines you can recite. If any line surprises you, the section in parentheses is your reading assignment.

```
NODES
  one world image → Sprite2D · one UI image → TextureRect        (§3.1)
  grid → TileMapLayer · iso grid → TileMapLayer ISOMETRIC        (§3.2)
  named flipbook states → AnimatedSprite2D                       (§3.3)
  timeline across properties → AnimationPlayer                   (§3.3)
  runtime one-off motion → Tween (kill before recreate!)         (§4.2)
  shapes/gizmos → _draw() + queue_redraw() on events             (§3.4)
  per-pixel looks → canvas_item shader (share materials!)        (§8)
  populations → GPUParticles2D (CPU only for weakest targets)    (§10)

ORDER (strongest → weakest)
  CanvasLayer  ▸  z_index (relative by default)  ▸  Y-sort
  (parent flag, z ties, origin at the feet)  ▸  tree order       (§5)

EFFECTS LADDER (stop at the first rung that works)
  visible → modulate/self_modulate → CanvasModulate → Tween/
  AnimationPlayer → shader → screen-reading shader →
  CanvasGroup → particles → lights → SubViewport                 (§8)

COST REFLEXES
  same texture+material = one batch · unique materials split     (§12)
  y-sort: only the moving band · redraw: only on events
  alpha 0 still draws — use visible = false
  full-screen transparent layers: count them (≤ 4-5)

PIXEL ART
  NEAREST project-wide · lossless import · no mipmaps ·
  integer scaling · snap positions                               (§6, R19)
```

---

## 2. The 2D visual stack at a glance

### 2.1 The five questions every visual element answers

Any pixel that reaches the screen in a Godot 2D game answered five questions on the way. This is the mental checklist for designing *and* for debugging:

```
┌────────────────────────────────────────────────────────────────────┐
│ Q1  WHAT draws it?          → content node (Sprite2D, TileMapLayer,│
│                               Label, _draw(), particles…)          │
│ Q2  WHERE does it sit?      → transform: position/rotation/scale,  │
│                               inherited down the tree              │
│ Q3  WHAT is on top of it?   → CanvasLayer > z_index > Y-sort >     │
│                               tree order                           │
│ Q4  HOW is it styled/moved? → modulate, ShaderMaterial, Tween,     │
│                               AnimationPlayer, particles           │
│ Q5  WHAT does it cost?      → draw calls, batching, fill rate,     │
│                               texture memory, per-frame CPU        │
└────────────────────────────────────────────────────────────────────┘
```

### 2.2 Node census — every visual node you will actually use

The Godot class tree is large; the working set for a 2D project is not. These are the nodes that cover ~99% of 2D visual work, with the module that owns each:

| Node | One-line job | Typical count per scene | Deep dive |
|------|--------------|------------------------|-----------|
| `Sprite2D` | draw one texture at a transform | dozens-hundreds | [M03](SPRITES_AND_TEXTURES.md) |
| `AnimatedSprite2D` | flipbook player with named animations (`SpriteFrames`) | a few (characters) | [M03](SPRITES_AND_TEXTURES.md) |
| `TileMapLayer` | draw a grid of reusable tiles from a `TileSet` | 2-6 layers | [M05](TILES_AND_TILEMAPS.md) |
| `TextureRect` | draw a texture **inside UI layout** | per panel | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `NinePatchRect` | 9-slice scalable frame in UI | per panel | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `Label` / `RichTextLabel` | text | many | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `Line2D` / `Polygon2D` | polyline / filled polygon, retained | occasional | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `ColorRect` | flat colored rectangle (overlays, tints, fades) | a few | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `CanvasLayer` | independent rendering layer (UI, popups, parallax root) | 2-4 | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `CanvasModulate` | tint the **whole canvas** (day/night) | 0-1 | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `CanvasGroup` | composite children, then apply opacity/shader once | rare, deliberate | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `Camera2D` | choose what part of the world the viewport shows | 1 per world | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `Parallax2D` | auto-scroll a layer at a speed ratio vs camera | 1 per depth layer | [M04](RENDERING_AND_VISUAL_LOGIC.md) §parallax |
| `GPUParticles2D` / `CPUParticles2D` | many small ephemeral quads | 1 per effect | this module §10 |
| `PointLight2D` / `DirectionalLight2D` / `LightOccluder2D` | 2D lighting and shadow | optional | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `SubViewport` + `SubViewportContainer` | render-to-texture (minimap, portrait, CRT) | rare, expensive | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `MultiMeshInstance2D` | thousands of identical quads in one draw call | rare, deliberate | [M14](DESKTOP_COMPANION_PERFORMANCE.md) |
| any `Node2D` with `_draw()` | fully procedural drawing, cached until `queue_redraw()` | occasional | [M04](RENDERING_AND_VISUAL_LOGIC.md) |

**Rule of thumb:** if you are about to add a node not on this list *for a visual purpose*, pause and check §3 — there is usually a simpler standard answer.

### 2.3 The stack as physical layers

A finished 2D game screen is a sandwich. From back to front, the canonical arrangement (and the one Relax Room uses — see §13):

```
FRONT (drawn last, wins)
 ▲
 │  CanvasLayer layer=100   modal popups, transition fades, debug overlay
 │  CanvasLayer layer=10    HUD / UI  (Control tree, ignores the camera)
 │  ── world space below: follows Camera2D ─────────────────────────────
 │  world: z_index high     floating text, selection cursors
 │  world: Y-sorted band    characters + obstacles sharing the floor
 │  world: z_index 0        decorations, props (tree order decides ties)
 │  world: z_index low/bg   floor overlays, floor/ground TileMapLayer
 │  Parallax2D layers       distant background, slower scroll ratios
 │  Viewport clear color    the color behind everything
 ▼
BACK (drawn first, loses)
```

Keep this picture in mind; §5 turns it into exact rules and §13 shows the concrete Relax Room instance.

### 2.4 Worked micro-example — five questions, one campfire

To make §2.1 concrete before the trees: *"a campfire in a forest clearing; the character can walk behind or in front of it; warm flickering light; the HUD must not be tinted."* Answer the five questions per element:

| Element | Q1 What draws it | Q2 Where | Q3 Ordering | Q4 Styling/motion | Q5 Cost note |
|---------|------------------|----------|-------------|-------------------|--------------|
| Forest floor | `TileMapLayer` (grid content, §3.2) | world origin | first sibling, z=0 | — | 1 draw call per quadrant |
| Fire pit + logs | `Sprite2D` | world position | inside the y-sort band (character overlaps it) | — | batches with other props if atlased |
| Flames | `AnimatedSprite2D` (flipbook) or `GPUParticles2D` (§10.3) | child of fire pit | same y-sort origin as the pit | per-anim FPS / particle lifetime | flipbook is cheaper; particles look richer |
| Flicker glow | `PointLight2D` with soft texture | child of flames | additive blend, not ordered | tween `energy` ±10% on a loop | one 2D light = fine (§12) |
| Warm ambience | `CanvasModulate` toward orange at night | world layer | affects whole world layer | tweened `color` (R3) | ~free |
| Character | `CharacterBody2D` + `AnimatedSprite2D` | world | same y-sort band, z ties | `play()` per state (§4.1) | one batch if same sheet |
| HUD | `Control` tree | `CanvasLayer layer=10` | above everything (§5 P1) | Theme (§13.4) | unaffected by `CanvasModulate` — different layer, by design |

Every design conversation about a 2D scene can be run as this table. Note how the *HUD must not be tinted* requirement was solved by an **ordering** decision (own CanvasLayer), not a styling one — the questions interact, which is exactly why the priority rules of §5 matter.

### 2.5 Near-twins you must not confuse

Eight pairs that cause a disproportionate share of beginner-to-intermediate confusion. If a bug report contains one of these words, check its twin first:

| This… | …is not this | The one-line difference |
|-------|--------------|------------------------|
| `modulate` | `self_modulate` | modulate multiplies down to children; self_modulate stops at the node (§8.1) |
| `self_modulate` | `CanvasModulate` | property on one item vs a node tinting its **entire canvas layer** (R3) |
| `z_index` | `CanvasLayer.layer` | priority *within* a layer vs choosing *which* layer — layer always wins (§5) |
| `visible = false` | `modulate.a = 0.0` | invisible-and-skipped vs invisible-but-still-drawn (costs fill rate, still gets input) |
| `Sprite2D.offset` | `Sprite2D.position` | shifts the texture relative to the node origin (y-sort tuning!) vs moves the node itself |
| `texture_filter` | import compression | runtime sampling (NEAREST/LINEAR) vs on-disk/VRAM encoding — both must match the art style (§6.1) |
| `AnimatedSprite2D` | `AnimationPlayer` | plays *frame lists* vs keyframes *any property on any node* (§4) |
| `Parallax2D.scroll_scale` | `Camera2D.zoom` | per-layer relative scroll speed (depth illusion) vs magnifying the whole view |

---

## 3. Decision trees — which node do I use?

Five trees cover the recurring choices. Follow the arrows; every leaf names a node and the module that documents it. When two leaves both seem right, jump to the master tables (§4-§8) and compare on the cost column.

### 3.1 Static image on screen

```
"I need to show one image."
        │
        ▼
Is it part of the GAME WORLD (moves with Camera2D, has a position
in world coordinates) or part of the UI (anchored to the screen)?
        │
   ┌────┴──────────────────────────────┐
   │ WORLD                             │ UI
   ▼                                   ▼
Does it need to STRETCH with     Does it need to resize with
a container/layout?  (No —       its container / anchors?
world images never do.)               │
   │                              ┌───┴────────────────────┐
   ▼                              │ YES                    │ It's a frame/panel
Sprite2D                          ▼                        ▼
· offset/centered control    TextureRect              NinePatchRect
· region_rect for atlas      · expand_mode,           · 9-slice margins
  crops                        stretch_mode           · or StyleBoxTexture
· flip_h / flip_v            · lives in Control         inside a Theme
· cheap, batches well          layout flow            [M04 §theme]
[M03]                        [M04 §ui]
   │
   ▼
Special cases for WORLD images:
· Huge background bigger than the screen, must scroll slower
  than the camera            → Parallax2D + Sprite2D child   (§7)
· Same small image repeated on a grid
                             → you are in tree 3.2, use TileMapLayer
· Image must tile/repeat inside one node
                             → Sprite2D + region_enabled + texture
                               repeat mode, or a shader UV trick [M12]
```

**Common mistake this tree prevents:** using `TextureRect` in the world (it ignores the camera transform when placed under a `CanvasLayer`, and layout containers fight manual positioning) or `Sprite2D` inside UI (it ignores anchors, breaks on window resize). World → `Sprite2D`; UI → `TextureRect`. Full rationale in [Module 04](RENDERING_AND_VISUAL_LOGIC.md).

### 3.2 Repeated / grid-based content

```
"I have many copies of small images arranged in space."
        │
        ▼
Are they aligned to a REGULAR GRID (square, isometric, hex)?
        │
   ┌────┴───────────────────────────────────┐
   │ YES                                    │ NO (free placement)
   ▼                                        ▼
Do the pieces need per-cell logic       How many instances?
(terrain autotiling, per-tile               │
collision, cell queries)?              ┌────┴─────────────┐
        │                              │ tens-hundreds    │ thousands,
   ┌────┴─────────────┐                ▼                  │ identical
   │ YES              │ NO, purely     Sprite2D per       ▼
   ▼                  │ decorative     instance           MultiMeshInstance2D
TileMapLayer          │ + few cells    (Relax Room        · 1 draw call
· one node per        ▼                decorations:       · no per-instance
  visual layer     Either works;       runtime Sprite2D     logic, transform
· TileSet shared      prefer           from JSON, §13)      via buffer
  across layers    TileMapLayer     · Area2D/StaticBody  [M14 §instancing]
· terrains =       once you have       siblings for
  autotiling       > ~20 cells         interaction
· per-tile         [M05]            [M03] + [M02]
  y_sort_origin,
  occluders,
  navigation
[M05]
        │
        ▼
Is the grid ISOMETRIC (diamond)?
        │
   ┌────┴────────────┐
   │ YES             │ NO
   ▼                 ▼
TileMapLayer with    TileMapLayer with
tile_shape =         tile_shape = SQUARE
ISOMETRIC on the     (default)
TileSet; read        [M05]
[M07] for diamond
down/right layout,
y-sort per tile and
elevation fakery.
```

**Threshold worth remembering:** a handful of static props → individual `Sprite2D`s are simpler to place and Y-sort. A floor, walls, or anything you will *paint* or edit repeatedly → `TileMapLayer` pays for itself immediately (autotiling, collision baked into tiles, one draw call per quadrant). Relax Room sits deliberately on the `Sprite2D` side — see §13.6 for the argued trade-off.

### 3.3 Animation

```
"Something needs to change over time."
        │
        ▼
Is it FRAME-BY-FRAME art (a flipbook of pre-drawn images)?
        │
   ┌────┴──────────────────────────────────────────────┐
   │ YES                                               │ NO — it's a property
   ▼                                                   │ changing (position,
How many named animations / do you need                │ alpha, scale, shader
per-animation FPS and autoplay?                        │ uniform…)
        │                                              ▼
   ┌────┴───────────────────┐              Is it a one-off transition
   │ several (character     │ exactly one, │ (fire-and-forget) or a
   │ states: idle/walk/…)   │ trivial loop │ choreographed sequence
   ▼                        ▼              │ you want editable in a
AnimatedSprite2D        Sprite2D +         │ timeline?
· SpriteFrames          hframes/vframes    │
  resource, editor      + Timer or         ├─ one-off, from code
  preview               AnimationPlayer    │  ▼
· play("walk"),         on `frame`         │  Tween  (create_tween())
  frame signals         · fewer moving     │  · tween_property/method
· speed_scale             parts for a      │  · chaining, parallel,
· per-anim fps            menu prop        │  · ease/trans curves
[M03]                   [M03], §13.3       │  · kill-before-recreate!
        │                                  │  [M04 §tween]
        ▼                                  │
Do frames need to sync WITH other          ├─ choreographed / multi-node
properties (hitboxes, sounds,              │  ▼
movement) on one timeline?                 │  AnimationPlayer
        │                                  │  · keyframe ANY property
   YES  ▼                                  │  · call-method + audio tracks
AnimationPlayer animating                  │  · editable timeline, blending
Sprite2D.frame (or                         │  [M03 §animationplayer]
AnimatedSprite2D.frame) +                  │
other tracks on the same                   └─ state-machine blending
timeline. AnimatedSprite2D                    (walk↔run↔jump)
alone can't keyframe other                    ▼
properties.  [M03]                            AnimationTree (advanced;
                                              out of scope here, see
                                              official docs)
```

**The three-way rule of thumb:**

- `AnimatedSprite2D` → *sprite flipbooks with named states* (Relax Room's character: 16 animations).
- `AnimationPlayer` → *anything keyframed on a timeline*, possibly many nodes and property types at once.
- `Tween` → *transitions created from code at runtime*, when authoring a timeline asset would be overkill (panel fades, walk-ins, shakes).

Full comparison with code in §4; tween lifecycle pitfalls in [Module 04](RENDERING_AND_VISUAL_LOGIC.md).

### 3.4 Procedural visuals (no pre-made texture)

```
"I need to draw something that isn't an image asset."
        │
        ▼
Is it a SHAPE (lines, polygons, circles, grids, gizmos)
or a SURFACE EFFECT (per-pixel color math on existing art)?
        │
   ┌────┴────────────────────────────────────┐
   │ SHAPE                                   │ SURFACE EFFECT
   ▼                                         ▼
Does it change every frame,             Per-pixel math (tint ramps,
or only when state changes?             outlines, dissolve, distortion,
        │                               palette swap, scanlines)?
   ┌────┴──────────────┐                     ▼
   │ rarely changes    │ it's a         canvas_item SHADER
   ▼                   │ polyline/      (ShaderMaterial on the node)
Node2D + _draw()       │ polygon that   · runs on GPU, per fragment
· draw_line/rect/      │ artists/code   · uniforms animated from
  circle/texture…      │ edit as data     GDScript or Tween
· result is CACHED;    ▼                · reads the screen with
  call queue_redraw()  Line2D /           hint_screen_texture
  only on change       Polygon2D        [M12 — the whole module]
· perfect for grids,   · width, joints,      │
  debug overlays,        gradient,           ▼
  selection boxes        textured line  If the effect needs to apply to
[M04 §draw]            · points are     MANY nodes composited as one
                         a property     (group fade without overlap
Relax Room example:      you tween or   artifacts, group outline):
64px placement grid,     append to     CanvasGroup (then shade/fade the
redrawn only on          (trails!)     group) [M04]
edit-mode toggle       [M04]
(§13.4)                              If it needs POST-PROCESSING of the
                                     whole screen: ColorRect (full-rect)
                                     + screen-reading shader on a top
                                     CanvasLayer, or SubViewport for
                                     hard isolation [M12 §screen]
```

**Cost intuition:** `_draw()` is CPU-cheap after caching (it costs only when redrawn), `Line2D`/`Polygon2D` are retained nodes you can tween, shaders are per-pixel GPU work (fill-rate bound), `SubViewport` is a whole extra render pass. Escalate in that order — the details live in §8 and §12.

### 3.5 UI vs world visuals

```
"Where does this element live?"
        │
        ▼
Should it MOVE when the Camera2D moves / zooms?
        │
   ┌────┴─────────────────────────────┐
   │ YES → it's part of the world     │ NO → it's screen-furniture
   ▼                                  ▼
Node2D family                    Control family, under a CanvasLayer
· Sprite2D, AnimatedSprite2D,    · Button, Label, Panel, TextureRect…
  TileMapLayer, particles…       · anchors + containers handle window
· position in world pixels         resize; never hand-position in px
· ordered by §5 mechanisms       · ordered by tree order within the
[M02][M03][M05]                    layer (z_index is almost never
        │                          needed in UI)
        │                        [M04 §ui + §theme]
        ▼
Hybrid cases (the classic traps):
· Health bar ABOVE a character's head → it must track a world
  position → Node2D child of the character (a small Control is OK
  as a child, but do NOT put it under the UI CanvasLayer).
· Floating damage text → world Node2D + Label child, tweened (§11 R6).
· Speech bubble pinned to a character but readable at any zoom →
  either world-space child (scales with zoom) or UI element that
  projects the position each frame:
  get_viewport().canvas_transform * world_pos.
· Full-screen fade → NOT world: ColorRect on a top CanvasLayer (§11 R8).
· Cursor/selection highlight on a world object → world-space, high
  z_index, not UI.
```

**Litmus test:** *"if the camera pans away, should it stay on screen?"* Yes → `Control` under a `CanvasLayer`. No → `Node2D` family in the world. The projection formula for hybrid pinning is derived in [Module 04](RENDERING_AND_VISUAL_LOGIC.md) §viewport.

### 3.6 Requirement → node quick-scan table

The five trees, flattened for lookup speed. If a row's "Why not the runner-up" argument doesn't apply to your case, take the runner-up.

| Requirement | Node | Why not the runner-up |
|-------------|------|----------------------|
| One image in the world | `Sprite2D` | `TextureRect` ignores camera/world transforms in UI use |
| One image in a menu/panel | `TextureRect` | `Sprite2D` ignores anchors, breaks on resize |
| Scalable panel frame | `NinePatchRect` / `StyleBoxTexture` | stretched `TextureRect` distorts corners |
| Solid color block, overlay, fade | `ColorRect` | a 1×1 white `Sprite2D` scaled up works but says nothing |
| Plain text | `Label` | `RichTextLabel` is heavier; only for BBCode/effects |
| Formatted/animated text | `RichTextLabel` | `Label` has no BBCode |
| Square-grid floor/walls | `TileMapLayer` | hundreds of `Sprite2D`s = no autotiling, no per-cell queries |
| Isometric floor | `TileMapLayer` (`tile_shape = ISOMETRIC`, [M07](ISOMETRIC_GAMES.md)) | faking with offsets breaks y-sort per tile |
| A few free-placed props | `Sprite2D` each | a tilemap forces a grid the design doesn't have (§13.6) |
| Thousands of identical quads | `MultiMeshInstance2D` | individual nodes → node overhead + draw calls |
| Character flipbook, named states | `AnimatedSprite2D` | `AnimationPlayer` needs a timeline per state |
| Timeline synced across properties | `AnimationPlayer` | `AnimatedSprite2D` animates frames only |
| Runtime one-off transition | `Tween` | authoring an animation asset for a fade is ceremony |
| Blended locomotion (walk↔run) | `AnimationTree` | manual `play()` calls can't crossfade |
| Polyline, ribbon, trail | `Line2D` | `_draw()` re-records on every point change |
| Filled arbitrary shape | `Polygon2D` | shader on a rect wastes fill rate outside the shape |
| Debug/grid/gizmo overlay | `Node2D` + `_draw()` | node-per-line explodes the tree (R20) |
| Rain, sparks, dust, confetti | `GPUParticles2D` | tween-per-flake does not scale (§10.3) |
| Particles on weakest hardware | `CPUParticles2D` | GPU sim edge cases on old drivers (§10.1) |
| Scrolling depth background | `Parallax2D` per layer | deprecated `ParallaxBackground` (§7) |
| Whole-world tint (day/night) | `CanvasModulate` | modulating the root also tints what shouldn't be (UI on same layer) |
| UI above the world | `CanvasLayer` (10) | giant z_index still loses to any higher layer |
| Modal/fade above UI | `CanvasLayer` (100) | reordering the UI tree is fragile |
| Group fade without seams | `CanvasGroup` | per-child modulate double-darkens overlaps (§8.1) |
| Minimap / portrait / screen-in-screen | `SubViewport` + `ViewportTexture` | `_draw()` dots if a stylized map suffices (R9) |
| Lamp glow, light pools | `PointLight2D` (+`CanvasTexture` normals) | additive sprites can't react to occluders |
| 2D shadows / line of sight | `LightOccluder2D` | manual shadow sprites don't track lights |
| Per-pixel surface effect | `ShaderMaterial` (canvas_item) | modulate can only tint uniformly (§8) |
| Effect on what's *behind* | shader + `hint_screen_texture` | normal shaders can't see other items |
| Choose what the player sees | `Camera2D` | moving the whole world inversely is madness with physics |
| Screen shake | `Camera2D.offset` (R5) | shaking `position` fights limits/smoothing |
| Health/progress bar | `TextureProgressBar` | hand-rolled `_draw()` bars re-solve a solved problem |
| Text pinned to a world object | Label as world-space child (§3.5) | UI-layer text detaches when the camera moves |
| Weather in front of everything | particles on a front `CanvasLayer` | in-world emitters slip behind high-z props |
| Render-only mirror/reflection | `SubViewport` + flipped `ViewportTexture` | shader reflections of off-screen content can't exist (`hint_screen_texture` sees only what's drawn) |

---

## 4. Master table — sprite and animation options

Every way to put moving (or still) sprite art on screen, side by side. "Cost" is relative CPU+GPU load for typical use; "Authoring" is where the work happens.

| Technique | Best for | Control surface | Per-anim FPS | Can drive other properties | Authoring | Cost | Deep dive |
|-----------|----------|-----------------|--------------|---------------------------|-----------|------|-----------|
| `Sprite2D` (static) | props, backgrounds, decorations | `texture`, `offset`, `flip_h/v`, `region_rect` | — | — | inspector / code | ★ (cheapest) | [M03](SPRITES_AND_TEXTURES.md) |
| `Sprite2D` + `hframes`/`vframes` + code | one trivial loop; menu props | set `frame` yourself (Timer/`_process`) | manual | via your own code | code | ★ | [M03](SPRITES_AND_TEXTURES.md) |
| `AnimatedSprite2D` + `SpriteFrames` | characters with named states | `play("name")`, `animation_finished`, `speed_scale` | yes, per animation | no (frames only) | SpriteFrames editor | ★★ | [M03](SPRITES_AND_TEXTURES.md) |
| `AnimationPlayer` (keyframing `frame` or any property) | cutscene-ish sequences, synced hitboxes/sfx | `play("name")`, timeline, method/audio tracks | keyframe spacing | **yes — any property, any node** | animation timeline editor | ★★ | [M03](SPRITES_AND_TEXTURES.md) |
| `AnimationTree` | blended locomotion state machines | state machine / blend spaces | inherited | yes | tree editor | ★★★ | official docs |
| `Tween` (runtime interpolation) | fades, slides, pulses, procedural motion | `create_tween()`, chained calls, ease/trans | n/a (continuous) | **yes — any property** | pure code | ★ | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| Shader-driven animation (`TIME` in GDShader) | wobble, scroll, flags, water — infinite loops with zero CPU | uniforms | n/a (continuous) | fragment/vertex only | shader code | ★★ (GPU) | [M12](SHADERS_GDSHADER.md) |
| Particles (§10) | many short-lived sprites | emitting, one_shot, `ParticleProcessMaterial` | lifetime-based | no | inspector | ★★-★★★ | this module §10 |

### 4.1 Choosing between the big three (flipbook context)

| Question | AnimatedSprite2D | AnimationPlayer | Tween |
|----------|------------------|-----------------|-------|
| Named art states (idle/walk/…)? | **best fit** | works, more setup | wrong tool |
| Sync frames + collision + audio on one timeline? | no | **best fit** | no |
| Created/varied at runtime from code? | fine (`play`) | clumsy | **best fit** |
| Artist-editable without code? | yes (SpriteFrames) | yes (timeline) | no |
| Interruptible/blendable states? | manual `play()` calls | `AnimationTree` on top | `kill()` + recreate |
| Relax Room usage | room character (16 anims, 8-way input → `play()` + `flip_h`) | loading screen | panel fades, menu walk-in (2.0 s, `EASE_OUT`+`TRANS_QUAD`) |

**Relax Room detail worth keeping:** the character controller collapses 8-way joystick input into 5 sprite states plus `flip_h` mirroring (halves the sprite count), with a `DIRECTION_THRESHOLD = 1.2` dead-zone ratio so near-vertical input snaps to straight movement instead of jittering diagonally. Full listing in [Module 09](PROJECT_DEEP_DIVE.md).

### 4.2 Tween lifecycle rule (the #1 tween bug)

A tween created by `create_tween()` is bound to the node and dies with it — but calling the creating function twice gives **two live tweens fighting over one property**. Standard fix:

```gdscript
var _tween: Tween

func fade_in() -> void:
    if _tween:
        _tween.kill()          # stop the previous animation first
    _tween = create_tween()
    _tween.tween_property(self, "modulate:a", 1.0, 0.3)
```

Sequencing (`tween_interval` → `tween_property` → `tween_callback`) runs steps in order; `set_parallel(true)` runs them together. Relax Room's whole menu intro (wait 0.4 s → fade loading 0.5 s → hide → character walk-in) is one chained tween. Details: [Module 04](RENDERING_AND_VISUAL_LOGIC.md) §tween.

### 4.3 One effect, three ways — a bobbing collectible

The same requirement ("a coin bobs up and down forever") implemented with each tool, so the trade-offs stop being abstract.

**Tween version — pure code, per instance:**

```gdscript
# coin.gd
func _ready() -> void:
    var t := create_tween().set_loops()
    t.tween_property(self, "position:y", position.y - 6.0, 0.7)\
     .set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
    t.tween_property(self, "position:y", position.y, 0.7)\
     .set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
```

*Pros:* zero assets, parametrizable per instance (randomize duration to desync coins). *Cons:* invisible to artists; every behavior change is a code change.

**AnimationPlayer version — timeline asset:**

```
AnimationPlayer ▸ "bob" (0.0 s: position.y = 0; 0.7 s: y = −6; 1.4 s: y = 0)
loop_mode = LINEAR · autoplay = "bob"
easing per key from the timeline editor
```

*Pros:* artist-editable, can grow extra tracks later (sparkle frames at the apex, a soft "ting" audio track) without touching code. *Cons:* one more node + asset per scene; desyncing instances needs `seek(randf() * length)`.

**Shader version — vertex offset, zero CPU:**

```glsl
shader_type canvas_item;
uniform float amp = 6.0;
uniform float speed = 2.2;
void vertex() {
    VERTEX.y += sin(TIME * speed + INSTANCE_CUSTOM.x * 6.28) * amp;
}
```

*Pros:* one shared material animates *any number* of coins with no per-frame CPU or per-instance tween; desync via instance data. *Cons:* the node's `position` never changes — collision shapes, children and y-sort don't follow the visual bob (usually fine for ±6 px; fatal if gameplay reads the position).

**Verdict table:**

| Criterion | Tween | AnimationPlayer | Shader |
|-----------|-------|-----------------|--------|
| CPU cost at 200 coins | 200 tweens (still small) | 200 players (still small) | ~0 |
| Physics/children follow the motion | yes | yes | **no** |
| Artist-editable | no | **yes** | uniforms only |
| Best when | few instances, code-driven variation | sequence will grow tracks | pure decoration at scale |

This three-way comparison generalizes to most "small looping motion" problems (floating icons, breathing idle scale, hovering UI arrows). [M04](RENDERING_AND_VISUAL_LOGIC.md) for tweens, [M03](SPRITES_AND_TEXTURES.md) for AnimationPlayer, [M12](SHADERS_GDSHADER.md) for vertex shaders.

### 4.4 SpriteFrames vs raw atlas mechanics — 30-second refresher

Two ways to express "frame N of a strip", both used in Relax Room:

```
male_idle_down.png (128×32 = 4 frames of 32×32)
┌────────┬────────┬────────┬────────┐
│ frame 0│ frame 1│ frame 2│ frame 3│
└────────┴────────┴────────┴────────┘

Way 1 — AtlasTexture regions inside SpriteFrames (the .tscn way):
  frame 0 = AtlasTexture(region = Rect2(0,  0, 32, 32))
  frame 1 = AtlasTexture(region = Rect2(32, 0, 32, 32))  …
  SpriteFrames animation "idle_down" = [f0, f1, f2, f3] @ 5 fps
  → AnimatedSprite2D.play("idle_down")

Way 2 — hframes/vframes on a plain Sprite2D (the code way):
  sprite.texture = strip;  sprite.hframes = 4
  sprite.frame = (sprite.frame + 1) % 4        # Timer-driven
```

Way 1 scales to many named animations with per-animation FPS (the room character's 16). Way 2 is four lines for a single loop (the menu character). Both read **the same texture memory** — the choice is pure authoring ergonomics, never performance. Import/slicing pipeline: [M03](SPRITES_AND_TEXTURES.md).

---

## 5. Master table — draw-order mechanisms

Four mechanisms decide what draws on top. **They are not equal — they nest.** Higher rows always beat lower rows; lower rows only break ties left by the higher ones.

| Priority | Mechanism | Scope | Granularity | Changes at runtime? | Typical use | Deep dive |
|----------|-----------|-------|-------------|--------------------|-------------|-----------|
| 1 (strongest) | `CanvasLayer.layer` | whole subtrees, independent of camera by default | integer layer index | rarely (structural) | UI (10), popups (100), parallax roots (negative) | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| 2 | `z_index` (± `z_as_relative`) | within one canvas layer | per `CanvasItem`, −4096…4096 | yes, cheap | put cursors/fx above the world band | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| 3 | Y-sort (`y_sort_enabled`) | among children of a y-sorted parent, **same z_index** | per node, by global Y of origin | automatic every frame | characters vs furniture on a shared floor | [M04](RENDERING_AND_VISUAL_LOGIC.md), iso: [M07](ISOMETRIC_GAMES.md) |
| 4 (weakest) | Tree order | siblings, same layer/z/no y-sort | node position in tree | `move_child()` etc. | default stacking of static layers | [M02](SCENES_AND_NODES.md) |

### 5.1 Interaction rules (memorize these six)

1. **CanvasLayer is absolute.** A node on `layer = 10` draws above *everything* on `layer = 0`, no `z_index` can cross that boundary. Layers with a higher index draw later (on top).
2. **`z_index` is relative by default.** With `z_as_relative = true` (default), effective z = parent's effective z + own `z_index`. Turn it off for an absolute value.
3. **Y-sort only reorders items whose effective z_index ties.** Y-sort compares the **global Y of each node's origin** among children of the y-sorted parent; a different z_index overrides it entirely.
4. **Y-sort needs the parent flag.** `y_sort_enabled` must be true on the **parent** whose children you want sorted (and on each `TileMapLayer` that participates). Nested y-sorted parents sort their subtrees together.
5. **Tree order is the final tiebreaker.** Same layer, same z, same Y (or no y-sort): later siblings draw on top ("the painter paints in tree order").
6. **`CanvasLayer` breaks camera following on purpose.** Children ignore `Camera2D` unless `follow_viewport_enabled = true`. That is why UI goes there — and why putting world objects there is a classic bug (§ troubleshooting).

### 5.2 Worked example — predicting an order

```
Main (Node2D)
├── Background (Sprite2D)                      z=0            (a)
├── Floor (TileMapLayer)                       z=0            (b)
├── World (Node2D, y_sort_enabled=true)
│   ├── Chair  (Sprite2D)  y_origin=400        z=0            (c)
│   ├── Player (CharacterBody2D) y=380         z=0            (d)
│   └── Cursor (Sprite2D)                      z=50           (e)
└── UILayer (CanvasLayer, layer=10)
    └── HUD (Control)                                         (f)

Resulting order, back → front:
  a (tree order first sibling)
  b (tree order, ties with a on z: later sibling wins)
  d (y-sorted: y=380 sorts BEFORE…)
  c (…y=400 → chair in front — player is "behind" the chair)
  e (z=50 escapes y-sort entirely, above the whole world band)
  f (CanvasLayer 10 beats every z_index below)
```

If the player walks to `y = 420`, d and c swap automatically next frame — that *is* Y-sort. For isometric floors the same rule applies per-tile via `y_sort_origin` on `TileMapLayer` tiles; the diamond-specific setup lives in [Module 07](ISOMETRIC_GAMES.md).

### 5.3 Which lever for which problem

| "I want…" | Use | Not |
|-----------|-----|-----|
| UI always above the game | `CanvasLayer layer=10` | giant z_index on Controls |
| a fade/modal above the UI too | higher `CanvasLayer` (100) | reordering the UI tree |
| characters to overlap furniture correctly on a floor | Y-sort band (shared parent, z ties) | per-object z_index micromanagement |
| a selection ring always above the world | `z_index` (e.g. 50) inside the world | a CanvasLayer (it would stop following the camera) |
| background always behind | first sibling or negative `z_index` | y-sort |
| swap two static layers | tree order (`move_child`) | z_index churn |
| a debug overlay above absolutely everything | highest reserved `CanvasLayer` (§5.5 registry) | per-scene z escalation wars |

### 5.4 Draw-order debugging flowchart

When something draws in the wrong place, resist the urge to sprinkle `z_index`. Walk this instead:

```
"A is drawing above/below B and shouldn't be."
        │
        ▼
1. Same CanvasLayer?  ── NO ──► the layer indices decide, full stop.
        │ YES                   Fix the layer assignment, not z.
        ▼
2. Effective z_index equal?  (remember z_as_relative sums
   down the tree — check ANCESTORS' z too)
        │                ── NO ──► z decides. Either intended, or an
        │ YES                      ancestor is leaking z: set the
        ▼                          child's z_as_relative = false or
3. Is a common ancestor            fix the ancestor.
   y_sort_enabled?
        │                ── YES ─► global Y of the ORIGINS decides.
        │ NO                       Wrong result = wrong origins:
        ▼                          move sprite offset so origins sit
4. Tree order decides:             at the feet/base (troubleshooting
   later sibling wins.             table, "flickering y-sort").
   move_child() or reorder
   the scene file.
```

Ninety percent of "mystery ordering" bugs die at step 1 or the *ancestors* clause of step 2. The Remote scene tree (running game ▸ Remote tab) shows effective layer and z per node — check reality there, not in the editor ([M02](SCENES_AND_NODES.md)).

### 5.5 Project layer registry — a one-table convention

Draw-order bugs are cheapest to prevent by **reserving numbers once**. Copy this table into any new project's docs (values = Relax Room's):

| Range | Reserved for | Nodes |
|-------|--------------|-------|
| CanvasLayer −10 | far parallax skies (if camera-driven) | `Parallax2D` roots |
| CanvasLayer 0 | the world | everything camera-following |
| CanvasLayer 10 | HUD / persistent UI | Control tree, Theme-styled |
| CanvasLayer 100 | modals, popups, transition fades | popup panels, R4 fade rect |
| world z −10…−1 | backgrounds behind the y-band | floors, wall overlays |
| world z 0 | the y-sort band + default props | characters, furniture |
| world z 10…50 | above-world markers | cursors, selection rings, R6 floating text |
| world z 100+ | reserved, exceptional | debug drawings |

The point is not these exact numbers — it's that *everyone on the project can answer "what layer does X go on" without opening scenes*. [M04](RENDERING_AND_VISUAL_LOGIC.md) discusses layer conventions; §13.1 shows this registry live.

### 5.6 Isometric ordering in ninety seconds

Isometric scenes are the stress test of §5, because *visual depth* is a function of screen Y — exactly what Y-sort measures. The [Module 07](ISOMETRIC_GAMES.md) essentials, compressed:

```
   screen Y grows ↓ = "closer to the viewer" = must draw LATER

        ◇ tile (0,0)              Ordering recipe:
      ◇     ◇                     1. floor TileMapLayer: y_sort OFF
    ◇    ◇     ◇                     (flat ground never overlaps actors)
      ◇     ◇                     2. everything standing: ONE y-sorted
        ◇ deeper rows                parent; TileMapLayer walls/props
          draw later                 participate with y_sort_enabled ON
                                  3. per-tile y_sort_origin shifts a
                                     tile's comparison point to its BASE
                                  4. actor origins at the FEET (offset!)
                                  5. tall objects spanning tiles: split
                                     into base+top tiles or give the
                                     scene an explicit y_sort_origin
```

The two failure smells: an actor "standing on" a wall it should be behind (origin not at the base — rule 3/4) and whole tile rows popping as one (layer not in the y-sorted parent — rule 2). Diamond math, elevation fakery and camera bounds: [Module 07](ISOMETRIC_GAMES.md).

---

## 6. Master table — texture types

All textures feed the same nodes; the type decides *where the pixels come from*. Full import pipeline (formats, compression, mipmaps) in [Module 03](SPRITES_AND_TEXTURES.md).

| Type | Pixels come from | Killer feature | Typical use | Watch out | Deep dive |
|------|------------------|----------------|-------------|-----------|-----------|
| `CompressedTexture2D` | imported `.png`/`.jpg` (the default `.ctex`) | import presets per asset | virtually everything | pixel art needs lossless + no mipmaps | [M03](SPRITES_AND_TEXTURES.md) |
| `AtlasTexture` | a **region** of another texture | many sprites, one file, one GPU texture → batching | spritesheet frames, icon sets | region math errors show neighbors' pixels (add padding) | [M03](SPRITES_AND_TEXTURES.md) |
| `ImageTexture` | an `Image` built/modified at runtime | fully procedural pixels | generated maps, screenshots, paint tools | `update()` re-uploads to GPU — don't do it per frame casually | [M03](SPRITES_AND_TEXTURES.md) |
| `ViewportTexture` | a `SubViewport`'s render result | render-to-texture | minimap, character portrait, CRT screen-in-screen | an entire extra render pass per frame | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `NoiseTexture2D` | generated `FastNoiseLite` | free organic patterns | dissolve masks, clouds, variation | generation is async at load | [M12](SHADERS_GDSHADER.md) |
| `GradientTexture1D/2D` | a `Gradient` resource | tiny memory, smooth ramps | tint ramps for shaders/particles, vignettes | 1D vs 2D confusion | [M12](SHADERS_GDSHADER.md) |
| `CanvasTexture` | diffuse + normal + specular maps bundled | 2D lighting response | lit sprites with `PointLight2D` | only meaningful with 2D lights | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `PlaceholderTexture2D` | nothing (solid size-holder) | zero-cost stand-in | prototyping, stripped exports | shipping it by accident | [M03](SPRITES_AND_TEXTURES.md) |

**Filtering reminder (pixel art):** filtering is per-`CanvasItem` (`texture_filter`) with a project default — `rendering/textures/canvas_textures/default_texture_filter`. Relax Room sets the default to **NEAREST** globally so 180×155 px `room.png` scales 4× to screen with crisp pixels; LINEAR would smear it. Import side: lossless compression, `mipmaps = false`, `fix_alpha_border = true`. The whole story is in [Module 03](SPRITES_AND_TEXTURES.md).

### 6.1 Import cheat-table by art style

| Art style | Filter | Compression | Mipmaps | Notes |
|-----------|--------|-------------|---------|-------|
| Pixel art | NEAREST | Lossless | off | `fix_alpha_border = true`; scale by integers (R19) |
| Painted / HD 2D | LINEAR | Lossless or VRAM (big textures) | off for pure 2D at 1:1; on if heavily downscaled | VRAM compression trades quality for memory |
| UI / icons | LINEAR (crisp vectors: use SVG import scale) | Lossless | off | 9-slice sources need clean margins |
| Photos / backgrounds | LINEAR | VRAM compressed | optional | JPEG-ish artifacts acceptable, memory matters |

One import preset per style, set as **Import Defaults** in project settings, then per-asset overrides only with a reason — the [M03](SPRITES_AND_TEXTURES.md) discipline in one row each.

### 6.2 Texture memory back-of-envelope

Uncompressed RGBA8 = 4 bytes per pixel. Quick math you should be able to do in your head during design review:

```
 512×512   sprite sheet ≈  1 MB      1024×1024 atlas ≈  4 MB
2048×2048  atlas        ≈ 16 MB      4096×4096 atlas ≈ 64 MB
mipmaps: ×1.33          VRAM-compressed (e.g. S3TC/BPTC): ÷4-8
```

Relax Room's entire art budget (tiny sources, NEAREST upscaling) is a rounding error — the 180×155 background is ~110 KB of VRAM. That is the *strategy*, not an accident: small sources + integer upscale is the cheapest possible texture pipeline ([M03](SPRITES_AND_TEXTURES.md), [M14](DESKTOP_COMPANION_PERFORMANCE.md)).

---

## 7. Master table — parallax options

| Option | Status in 4.5 | How it works | Pros | Cons | Deep dive |
|--------|---------------|--------------|------|------|-----------|
| **`Parallax2D`** | **current, recommended** | plain `Node2D`-style scroller: `scroll_scale` per layer, `repeat_size` for infinite tiling, `autoscroll` | works like any Node2D (z_index, y-sort friendly), one node per layer, mirrors via `repeat_size`, no special container | one node per depth layer to manage | [M04](RENDERING_AND_VISUAL_LOGIC.md) §parallax |
| `ParallaxBackground` + `ParallaxLayer` | **deprecated** (kept for compatibility) | a `CanvasLayer` subclass intercepting camera motion; layers hold `motion_scale`/`motion_mirroring` | familiar from Godot 3 tutorials | CanvasLayer quirks (draw-order surprises, camera decoupling), two-node ceremony, deprecated | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| Manual offset in code | always available | move layer nodes yourself from camera/mouse position | total control; works without a `Camera2D` at all | you own the math and the tiling | §13.5 (Relax Room does this) |
| Shader UV scroll | always available | fragment shader offsets UVs by a uniform (or `TIME`) | zero nodes, infinitely tileable, cheapest for pure backgrounds | not a real transform: children/collisions don't follow | [M12](SHADERS_GDSHADER.md) |

**When to pick which:** scrolling *game world* with a `Camera2D` → `Parallax2D`. Decorative *menu* parallax driven by the mouse with no camera → manual offsets are honest and simple; that is exactly Relax Room's 8-layer forest menu (`PARALLAX_STRENGTH = 8.0` px max shift; layer i moves i px — §13.5). Pure texture scroll (endless sky) → shader.

### 7.1 Minimal setups, side by side

**Camera-driven world parallax (`Parallax2D`):**

```
Main
├── Parallax2D  "Sky"        scroll_scale (0.05, 0.05)  repeat_size (1280, 0)
│   └── Sprite2D (sky.png, centered=false)
├── Parallax2D  "Mountains"  scroll_scale (0.25, 0.25)  repeat_size (1280, 0)
│   └── Sprite2D
├── Parallax2D  "Trees"      scroll_scale (0.70, 0.70)  repeat_size (1280, 0)
│   └── Sprite2D
└── ... world (scroll_scale 1.0 = no Parallax2D needed)
```

`scroll_scale < 1` = farther than the action; `> 1` = foreground sweeping past; `autoscroll` adds camera-independent drift (clouds). Each `Parallax2D` is an ordinary canvas item — order the layers with tree order like anything else (§5).

**Mouse-driven menu parallax (manual, the Relax Room way):**

```gdscript
# window_background.gd (essence)
const PARALLAX_STRENGTH := 8.0

func _process(_delta: float) -> void:
    var center := get_viewport_rect().size / 2.0
    var norm := (get_viewport().get_mouse_position() - center) / center  # −1..1
    for i in layers.size():
        layers[i].position = base_positions[i] + norm * PARALLAX_STRENGTH * float(i) / layers.size()
```

Eight forest layers, nearest moves most — the train-window illusion with fifteen lines and no camera. Promote to `Parallax2D` the day a real `Camera2D` enters the scene. [M04](RENDERING_AND_VISUAL_LOGIC.md) §parallax.

---

## 8. Master table — visual-effect techniques

The escalation ladder. For any effect, start at the top row that can express it.

| Technique | What it can change | Granularity | Runs on | Cost | Breaks batching? | Typical effects | Deep dive |
|-----------|--------------------|-------------|---------|------|------------------|-----------------|-----------|
| `visible` / `show()`/`hide()` | on/off | node + subtree | CPU (free) | ~0 | n/a (skipped) | toggling layers, grid overlay | [M02](SCENES_AND_NODES.md) |
| `modulate` / `self_modulate` | uniform tint + alpha | node (+children / self only) | CPU→vertex color | ★ | **no** | fades, flashes, theme tints, ghosting | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `CanvasModulate` | uniform tint | **entire canvas layer** | vertex color | ★ | no | day/night, mood lighting | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `Tween` on any of the above (or transform) | anything scriptable over time | per property | CPU (tiny) | ★ | no | panel fades, shakes, pulses, walk-ins | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `AnimationPlayer` | keyframed anything | per timeline | CPU (tiny) | ★ | no | synced multi-property sequences | [M03](SPRITES_AND_TEXTURES.md) |
| canvas_item **shader** | per-pixel / per-vertex math | per material | **GPU** | ★★ (fill-rate) | **yes — unique materials split batches** | outline, dissolve, palette swap, distortion, water | [M12](SHADERS_GDSHADER.md) |
| screen-reading shader (`hint_screen_texture`) | pixels already drawn behind | per material | GPU (+screen copy) | ★★★ | yes | blur, grayscale pause, heat haze, magnifier | [M12](SHADERS_GDSHADER.md) |
| `CanvasGroup` | composite subtree, then style once | subtree | GPU (extra composite) | ★★★ | partially | group fade w/o overlap artifacts, group outline | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| **Particles** (§10) | many ephemeral quads | per emitter | GPU or CPU | ★★-★★★ | own draw call | rain, dust, sparks, confetti | this module §10 |
| 2D lights + occluders | additive/mask lighting, shadows | per light | GPU | ★★★ | extra passes | lamp glow, darkness, LOS | [M04](RENDERING_AND_VISUAL_LOGIC.md) |
| `SubViewport` render-to-texture | a whole separate scene render | per viewport | GPU (full pass) | ★★★★ | own pass | minimap, portraits, per-object post-fx | [M04](RENDERING_AND_VISUAL_LOGIC.md) |

### 8.1 The modulate multiplication rule

`modulate` multiplies down the tree: parent `a=0.5` × child `a=0.5` → child renders at 0.25 alpha. Use `self_modulate` to tint a node **without** touching its children. Overlapping semi-transparent children fading as a group show double-darkening seams — that is the one honest reason to pay for `CanvasGroup`. ([Module 04](RENDERING_AND_VISUAL_LOGIC.md).)

### 8.2 Decision ladder in one paragraph

Tint or fade → `modulate` (+`Tween` for motion). Whole-world mood → `CanvasModulate`. Per-pixel look (outline, dissolve, swap) → shader. Needs what's *behind* it → screen-reading shader. Many small moving things → particles. A second camera's view → `SubViewport`. Each step multiplies cost roughly 2-5×; never start at the bottom of the ladder "because shaders are cooler".

### 8.3 Worked escalation — "highlight the hovered furniture"

The ladder applied to one real requirement, showing where each rung stops being enough:

1. **`self_modulate = Color(1.2, 1.2, 1.0)`** (slight overbright tint). One line, batch-safe, children untouched. *Relax Room ships this* (R14). Stops being enough when: the art is already near-white (tint invisible) or design wants an outline, not a tint.
2. **Tween the tint** (pulse between 1.0 and 1.2). Adds life for the cost of one tween. Stops when: a shape-following outline is required.
3. **Outline shader** (neighbor-alpha sampling, R1). Per-pixel, needs a material — share ONE material across all decorations and flip a per-instance uniform, or you split every batch (§12). Stops when: the outline must also glow through occluding furniture.
4. **Second render** (silhouette pass R22, or `CanvasGroup` composite outline). Real cost; needs a §12 audit before adoption.

Most projects should ship rung 1-2 and file rungs 3-4 under "when a designer asks twice". Writing the escalation into the task ("hover feedback, rung 2, escalate on request") keeps effect-creep visible and priced.

### 8.4 Blend modes — the forgotten fourth styling knob

Between modulate and shaders sits `CanvasItemMaterial.blend_mode` — no shader code, big look changes:

| Blend mode | Pixel math (roughly) | Classic use |
|------------|----------------------|-------------|
| Mix (default) | alpha-over | everything normal |
| **Add** | screen += sprite | glows, fire, magic, lens flares — black backgrounds vanish for free |
| Subtract | screen −= sprite | darkness auras, negative effects |
| Multiply | screen ×= sprite | fake shadows, stains, vignettes on world art |
| Premultiplied alpha | premult compositing | correct fades of additive art, [M03](SPRITES_AND_TEXTURES.md) edge notes |

One `CanvasItemMaterial` with `blend_mode = ADD` on a soft white circle is a complete lamp-glow implementation — rung 1½ on the ladder, far cheaper than 2D lights when nothing needs occlusion. Like shaders, a *unique* material per node splits batches: share it (§12).

---

## 9. One frame in 2D — the render pipeline as a story

You press Play. Sixty times a second (or whatever the display refresh is), the following story runs to completion. Knowing the acts tells you **where each mechanism from this module hooks in** — and therefore where each class of bug or cost lives.

### 9.1 The cast

| Actor | Role |
|-------|------|
| `SceneTree` | the director: owns the node hierarchy, dispatches process callbacks and signals |
| `CanvasItem` nodes | the actors: each *records* what it wants drawn (they do not draw!) |
| `RenderingServer` | the stage manager: keeps its own list of canvas items + recorded draw commands, independent of your tree |
| Renderer backend (Forward+/Mobile/Compatibility) | translates canvas items into GPU API calls (Vulkan / GL) |
| GPU | rasterizes triangles into the framebuffer |
| Compositor / OS | presents the finished image to the monitor |

### 9.2 Act I — Simulation (CPU, your code)

The frame starts on the CPU. The `SceneTree` runs, in order: physics ticks (`_physics_process`, fixed rate) as needed, then `_process(delta)` on every node that has it, plus pending timers, tweens and signal callbacks.

**Everything you script happens here**: a `Tween` advances `modulate:a`, the character controller calls `play("walk_side")`, `CPUParticles2D` integrates its particles, code flips `visible`, sets `z_index`, moves nodes. None of this draws anything — it only **changes state** on canvas items, and each change marks the item dirty on the `RenderingServer`.

- Hook: `_draw()` does **not** run every frame. It runs only for items flagged by `queue_redraw()` (or on first show); the resulting command list is cached on the server. That is why Relax Room's placement grid costs nothing except on edit-mode toggles (§13.4).

### 9.3 Act II — Canvas cull and sort (RenderingServer, CPU)

When the tree is done mutating state, the `RenderingServer` prepares the 2D scene:

1. **Cull:** items outside the visible canvas region (camera rect per layer) are skipped. `visible = false` subtrees were never in the list.
2. **Sort:** the surviving items are ordered by exactly the §5 priority — canvas layer index, then effective `z_index`, then Y (for y-sorted bands, comparing global Y of origins), then tree order. Y-sort re-runs its comparisons **every frame** for moving items; that's its cost.
3. **Batch:** consecutive items in the final order that share texture + material + blend settings are merged into single draw calls. An `AtlasTexture` spritesheet keeps a hundred decorations in a handful of batches; giving one sprite in the middle its own `ShaderMaterial` splits the run into three.

- Hook: this act is where **draw-order bugs** live (wrong layer/z/y assumptions → §5, troubleshooting table) and where **draw-call counts** are decided (§12).

### 9.4 Act III — Recording to the GPU (backend)

The backend walks the sorted, batched list and emits GPU commands: bind this texture, this material's shader and uniforms, draw these vertex ranges. Per item it uploads small per-instance data (transform, `modulate` color — which is why modulate is nearly free: it rides along as vertex data, no state change).

Special items schedule extra work here:

- **Screen-reading shaders** (`hint_screen_texture`) force a copy of the screen so far, so the shader can sample it — one copy per "backbuffer" break.
- **`CanvasGroup` / `SubViewport`** render their content to an offscreen target first, then composite it as a single quad.
- **2D lights** add their blending passes over the affected items; occluders render shadow geometry.
- **`GPUParticles2D`** runs its particle **simulation on the GPU** (a compute/transform step) before its quads are drawn; the CPU only sees "draw N instances".

### 9.5 Act IV — Rasterization and present (GPU)

The GPU executes the queue: vertex shaders position each quad (canvas transforms multiplied in), fragment shaders — default or your GDShader — compute every covered pixel, blending writes them into the framebuffer back-to-front. Fill rate is consumed by every drawn pixel, **including fully transparent overdraw**: five full-screen semi-transparent rects = five full screens of fragment work. When the queue finishes, the image is presented (swapped) to the display, v-synced by default.

### 9.6 The whole frame on one screen

```
 CPU  ┌────────────────────────────────────────────────────────────┐
      │ ACT I   SceneTree: _physics_process → _process → tweens/   │
      │         timers/signals  → state changes mark items dirty   │
      │         (queue_redraw() re-records _draw() items)          │
      ├────────────────────────────────────────────────────────────┤
      │ ACT II  RenderingServer: cull → sort (layer ▸ z ▸ y ▸ tree)│
      │         → batch by texture/material                        │
      ├────────────────────────────────────────────────────────────┤
      │ ACT III backend: bind/record draw calls, screen copies,    │
      │         offscreen targets (CanvasGroup/SubViewport), lights│
 GPU  ├────────────────────────────────────────────────────────────┤
      │ ACT IV  vertex → fragment (your shaders here) → blend →    │
      │         framebuffer → present (v-sync)                     │
      └────────────────────────────────────────────────────────────┘
 Budget rule: Act I overruns → "script" time in profiler (M14).
              Act II/III overruns → draw calls / sorting (§12).
              Act IV overruns → fill rate / shader cost (§12, M12).
```

The profiler in [Module 14](DESKTOP_COMPANION_PERFORMANCE.md) splits time along exactly these seams — which is why this story is worth internalizing before profiling anything.

### 9.7 Sidebar — the transform chain (where "position" becomes pixels)

Between Act II and Act IV, every vertex is multiplied through a chain of transforms. Naming them demystifies half the coordinate bugs in 2D:

```
local vertex
  × node's transform (position/rotation/scale/skew)
  × every ancestor Node2D's transform          ← "children move with parents"
  = GLOBAL / WORLD coordinates  (global_position lives here)
  × canvas transform (Camera2D: −camera pos, × zoom)   ← skipped for
  = SCREEN-SPACE canvas coordinates                     CanvasLayers that
  × viewport stretch transform (project stretch mode)   don't follow the
  = actual framebuffer pixels                           viewport (§5 rule 6)
```

Practical corollaries:

- `global_position` vs `position`: assigning across parents without conversion is the classic teleport bug ([M02](SCENES_AND_NODES.md)).
- Screen → world for mouse picking: `get_global_mouse_position()` already applies the inverse chain; doing it by hand, it's `get_canvas_transform().affine_inverse() * mouse_pos` ([M04](RENDERING_AND_VISUAL_LOGIC.md)).
- World → screen for pinning UI over a world object (§3.5): `get_viewport().canvas_transform * world_pos`.
- The stretch transform is why "1280×720" positions still land correctly on a 4K monitor — and why physical-pixel hacks break on resize (R19).

### 9.8 Bug class → act of the frame — the triage table

The practical payoff of the story: every visual bug family lives in exactly one act, which fixes your first debugging move.

| Bug family | Act | First move |
|------------|-----|-----------|
| Wrong values animating (jumps, fights, stale state) | I — simulation | breakpoint/print in the tween/signal path; check kill-before-recreate (§4.2) |
| Wrong stacking, missing items, "invisible but visible=true" | II — cull & sort | Remote tree + §5.4 flowchart |
| Draw calls exploded, batching decayed | II/III — batch & record | monitor before/after; hunt unique materials (§12) |
| Wrong pixels *within* an item (shader artifacts, filtering, bleeding) | IV — raster | isolate the material/texture; test with a plain material ([M12](SHADERS_GDSHADER.md), [M03](SPRITES_AND_TEXTURES.md)) |
| Frame time spikes on *specific events* (popup opens, first effect) | III/IV — first-use compile/upload | warm up assets at load (troubleshooting, last row) |
| Steady slow burn as content grows | II+IV — sort cost + fill rate | §12.2 audit, then [M14](DESKTOP_COMPANION_PERFORMANCE.md) profiler |

---

## 10. Particles essentials — GPU vs CPU

Particles are the fourth motion tool (after tween, animation, shader) and the first one that manages **populations** instead of single objects. Both 2D particle nodes emit textured quads with lifetime, velocity, color ramps; they differ in *who simulates*.

### 10.1 Head-to-head

| | `GPUParticles2D` | `CPUParticles2D` |
|---|------------------|------------------|
| Simulation runs on | GPU (`ParticleProcessMaterial`) | CPU (built-in properties) |
| Particle count sweet spot | thousands+ | dozens-hundreds |
| Renderer support | all backends (Compatibility too, since 4.3) | everywhere, always |
| Extra features | sub-emitters, attractors, collision (SDF), trails | simpler feature set |
| Per-frame CPU cost | ~constant (dispatch only) | grows linearly with count |
| Determinism / low-end safety | driver-dependent edge cases | most predictable |
| Convert between them | — | editor: "Convert to CPUParticles2D" exists for the reverse path (GPU→CPU) |
| Relax Room stance | fine for ambience (dust, fireflies) | safest choice given desktop-companion, battery-friendly goals ([M14](DESKTOP_COMPANION_PERFORMANCE.md)) |

**Default advice for this course's scope** (desktop companion, modest effects): start with `GPUParticles2D` for anything dense or decorative; drop to `CPUParticles2D` when targeting very weak iGPUs/web exports or when a few dozen particles don't justify GPU buffers. Measure, don't guess — `Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME` and the Monitors tab ([M14](DESKTOP_COMPANION_PERFORMANCE.md)).

### 10.2 The five properties that do 90% of the work

```
amount        how many particles exist at once (budget!)
lifetime      seconds each particle lives
one_shot      true → burst (confetti); false → continuous (rain)
explosiveness 0 = steady stream … 1 = all at once
preprocess    simulate N seconds before first frame (rain already falling)
```

Plus, on the process material (GPU) or node (CPU): direction/spread, initial velocity, gravity, scale curve, **color ramp** (a `GradientTexture1D` — fade-out for free).

### 10.3 When particles beat shaders and tweens (and when not)

| Effect | Right tool | Why |
|--------|-----------|-----|
| 100 falling snowflakes | particles | population with per-instance randomness — that's the definition |
| One floating "+5" text | Tween on a Label ([§11 R6](#11-recipe-index--how-do-i)) | a single object; a particle system is overhead and hard to control |
| Sprite dissolving to nothing | shader (noise threshold) | per-pixel erosion of *existing* art — particles can't eat pixels |
| Dust burst when furniture drops | particles, `one_shot` | short-lived population, fire-and-forget |
| Waterfall shimmer on one sprite | shader (`TIME`-driven UV) | continuous surface effect, zero management |
| Trail behind a moving sprite | `Line2D` + point history, or GPU particle **trails** | Line2D = precise ribbon; particles = smoky/spark trail |
| Screen-wide rain in front of everything | particles on a front `CanvasLayer` | population + ordering via §5 |

**Litmus test:** *many short-lived instances with randomized parameters* → particles. *One object* → tween. *Changing the pixels of existing art* → shader ([Module 12](SHADERS_GDSHADER.md)).

### 10.4 A complete emitter, annotated — "dust burst when furniture drops"

The one-shot pattern, end to end (this is R15/R21's skeleton with every decision written out):

```gdscript
# dust_burst.gd — attach to a GPUParticles2D
func _ready() -> void:
    emitting = false            # do NOT autoplay; we fire on demand
    one_shot = true             # burst, not stream
    amount = 24                 # budget decided here, not after profiling
    lifetime = 0.6
    explosiveness = 1.0         # all 24 at once
    local_coords = false        # particles stay where emitted even if
                                # the parent (furniture) keeps moving

    var mat := ParticleProcessMaterial.new()
    mat.direction = Vector3(0, -1, 0)          # up-ish
    mat.spread = 60.0
    mat.initial_velocity_min = 40.0
    mat.initial_velocity_max = 90.0
    mat.gravity = Vector3(0, 180, 0)           # settle back down
    mat.scale_min = 0.5
    mat.scale_max = 1.2
    mat.color_ramp = preload("res://fx/dust_ramp.tres")  # GradientTexture1D
                                                          # → alpha fades to 0
    process_material = mat

func burst_at(world_pos: Vector2) -> void:
    global_position = world_pos
    restart()                   # re-fires a finished one_shot cleanly
```

Ordering: parent it in the world's y-band (dust belongs *on the floor*, §5), never on the UI layer. Cost: 24 tiny quads, one draw call, GPU-simulated — invisible in the §12 audit. The same skeleton with `one_shot = false`, a tall emission box and `preprocess = 2.0` is the rain of R15; with `spread = 180`, upward gravity and a confetti sheet it's R21.

**CPU fallback:** the editor's *Convert to CPUParticles2D* keeps these properties (they mirror onto the node itself); only `ParticleProcessMaterial`-exclusive features (sub-emitters, attractors, collision) are lost — §10.1's table tells you whether you were using any.

### 10.5 Particle production checklist

Before an emitter ships, walk this list (it is §12 and §5 applied to particles):

- [ ] **`amount` justified in a comment** — "24 because one burst per drop, never overlapping" beats a magic number.
- [ ] **Texture is small and opaque-ish** — giant soft-alpha quads are pure overdraw (§12.1).
- [ ] **`local_coords` decided consciously** — `false` for world-anchored effects (dust stays where it was emitted), `true` for effects glued to the emitter (engine exhaust).
- [ ] **Ordering assigned via §5** — weather on a front layer, floor dust in the y-band, never "wherever it landed".
- [ ] **`one_shot` emitters re-fired with `restart()`**, not by toggling `emitting` and hoping.
- [ ] **Continuous emitters use `preprocess`** so scenes don't start empty (R15).
- [ ] **Lifetime × amount sanity**: `amount / lifetime` = spawns per second — say the number out loud once.
- [ ] **Low-end plan named**: GPU everywhere, or a CPU fallback path for the §10.1 edge platforms.

---

## 11. Recipe index — how do I…

Twenty-five answers to the questions that come up during real work. Each recipe: minimal approach, essential code where it clarifies, and the module that owns the full treatment. Recipes assume Godot 4.5 API.

### Recipe finder

| # | Goal | Core tool | §8 cost rung |
|---|------|-----------|--------------|
| R1 | outline on hover | shader + Area2D signals | shader |
| R2 | flash white on hit | shader or HDR modulate tween | modulate/shader |
| R3 | day/night tint | `CanvasModulate` + tween | canvas tint |
| R4 | fade scene transition | ColorRect on layer 100 + tween | modulate |
| R5 | screen shake | `Camera2D.offset` tween | tween |
| R6 | floating damage text | spawned Node2D + parallel tween | tween |
| R7 | dissolve away | noise-threshold shader | shader |
| R8 | trail behind sprite | sibling `Line2D` + point history | retained node |
| R9 | minimap | `SubViewport` or `_draw()` dots | subviewport / draw |
| R10 | pulsing button | looping tween (+ `pivot_offset`) | tween |
| R11 | parallax background | `Parallax2D` per layer | node transform |
| R12 | grayscale pause | screen-reading shader | screen shader |
| R13 | health/progress bar | `TextureProgressBar` | UI node |
| R14 | hover-highlight furniture | `self_modulate` overbright | modulate |
| R15 | rain / snow / dust | `GPUParticles2D` + preprocess | particles |
| R16 | drop shadow | offset dark duplicate sprite | modulate |
| R17 | scrolling texture | UV-offset shader or region tween | shader |
| R18 | 9-slice panel | `NinePatchRect` / `StyleBoxTexture` | UI node |
| R19 | crisp pixel art | NEAREST + integer scaling | settings |
| R20 | placement grid overlay | `_draw()` + event redraw | draw |
| R21 | confetti burst | one-shot particles + `restart()` | particles |
| R22 | silhouette through walls | duplicate sprite, solid shader, high z | shader + z |
| R23 | palette swap / skins | index-lookup shader | shader |
| R24 | swaying grass | height-weighted vertex shader | shader |
| R25 | vignette / CRT | full-rect fragment shader | screen shader |

### R1 — …outline a sprite on hover?

`Area2D` (with a `CollisionShape2D`) over the sprite for `mouse_entered`/`mouse_exited`; toggle a shader parameter on a shared outline material.

```gdscript
func _on_mouse_entered() -> void:
    sprite.material.set_shader_parameter("outline_width", 2.0)
func _on_mouse_exited() -> void:
    sprite.material.set_shader_parameter("outline_width", 0.0)
```

The outline shader (neighbor-alpha sampling) is built step by step in [Module 12](SHADERS_GDSHADER.md). Cheap alternative for flat-color art: a slightly scaled black duplicate behind (`self_modulate`), zero shaders.

### R2 — …flash a sprite white when hit?

`modulate` can only multiply (darken/tint), never push toward white. Two options: a 3-line shader with `mix(color, vec3(1.0), flash)` ([M12](SHADERS_GDSHADER.md)), or tween `modulate` to a bright additive-looking color and back for a "good enough" pulse:

```gdscript
var t := create_tween()
t.tween_property(sprite, "modulate", Color(8, 8, 8), 0.05)  # HDR overbright
t.tween_property(sprite, "modulate", Color.WHITE, 0.10)
```

### R3 — …tint the whole scene for day/night?

One `CanvasModulate` node in the world; tween its `color` between presets (`Color(1,1,1)` noon → `Color(0.35,0.4,0.65)` night). It multiplies every canvas item on the layer — UI on its own `CanvasLayer` is unaffected, which is exactly what you want. [M04](RENDERING_AND_VISUAL_LOGIC.md).

### R4 — …fade between scenes?

Full-rect black `ColorRect` on a top `CanvasLayer` (layer 100), `mouse_filter = IGNORE` while transparent. Fade alpha up, switch scene, fade down. Persistent version: put it in an autoload so it survives `change_scene_to_packed()` — pattern in [Module 13](AUTOLOAD_SAFETY.md); tween details [M04](RENDERING_AND_VISUAL_LOGIC.md). Relax Room's loading-screen fade (0.5 s) is the same idea (§13.5).

### R5 — …shake the screen?

Tween or noise-drive `Camera2D.offset` — never `position` (it fights camera smoothing/limits):

```gdscript
func shake(strength: float = 8.0, time: float = 0.25) -> void:
    var t := create_tween()
    for i in 6:
        t.tween_property(camera, "offset",
            Vector2(randf_range(-1, 1), randf_range(-1, 1)) * strength, time / 6.0)
    t.tween_property(camera, "offset", Vector2.ZERO, time / 6.0)
```

Decay strength over time for a natural feel. [M04](RENDERING_AND_VISUAL_LOGIC.md) §camera.

### R6 — …show floating damage/reward text?

Spawn a small scene (Node2D + Label) at the world position; tween up + fade; free on finish:

```gdscript
var t := create_tween().set_parallel(true)
t.tween_property(self, "position", position + Vector2(0, -40), 0.6)
t.tween_property(self, "modulate:a", 0.0, 0.6)
t.chain().tween_callback(queue_free)
```

World-space Node2D (not UI!) so it stays pinned — §3.5. [M04](RENDERING_AND_VISUAL_LOGIC.md).

### R7 — …dissolve a sprite away?

Shader: sample a `NoiseTexture2D`, discard/alpha-out pixels below a threshold uniform; tween the uniform 0→1.

```glsl
uniform sampler2D noise_tex;
uniform float threshold : hint_range(0.0, 1.0) = 0.0;
void fragment() {
    if (texture(noise_tex, UV).r < threshold) { COLOR.a = 0.0; }
}
```

Edge-glow variant and burn colors in [Module 12](SHADERS_GDSHADER.md).

### R8 — …put a trail behind a moving sprite?

`Line2D` as **sibling** (not child — a child inherits the movement and the ribbon collapses); push the object's global position each frame, cap the length:

```gdscript
func _process(_d: float) -> void:
    trail.add_point(target.global_position, 0)  # prepend
    if trail.get_point_count() > 24:
        trail.remove_point(trail.get_point_count() - 1)
```

Width curve + gradient make it taper and fade. Smoky alternative: GPU particle trails (§10). [M04](RENDERING_AND_VISUAL_LOGIC.md).

### R9 — …make a minimap?

Honest version: `SubViewport` with its own `Camera2D` (high zoom-out, `world_2d` shared with the main viewport), shown through a `SubViewportContainer` or `TextureRect` + `ViewportTexture` in the HUD. Cheap version (usually better): a `Control` with `_draw()` painting dots from entity positions scaled into map space — no extra render pass. Costs: §12. [M04](RENDERING_AND_VISUAL_LOGIC.md).

### R10 — …pulse a button / blink a cursor?

Looping tween on the node itself:

```gdscript
var t := create_tween().set_loops()
t.tween_property(btn, "scale", Vector2(1.06, 1.06), 0.4)
t.tween_property(btn, "scale", Vector2.ONE, 0.4)
```

Set `pivot_offset` to the Control's center first or it scales from the corner (top troubleshooting entry). [M04](RENDERING_AND_VISUAL_LOGIC.md).

### R11 — …scroll a parallax background behind the world?

One `Parallax2D` per depth layer, each with a `Sprite2D` child; `scroll_scale` < 1 for distant layers (0.1 mountains … 0.9 near trees), `repeat_size.x` = texture width for seamless horizontal looping; optional `autoscroll` for self-moving skies. §7 table; [M04](RENDERING_AND_VISUAL_LOGIC.md). (Relax Room's mouse-driven menu variant: §13.5.)

### R12 — …gray out the whole screen when paused?

Full-rect `ColorRect` on a top `CanvasLayer` with a screen-reading shader:

```glsl
uniform sampler2D screen_tex : hint_screen_texture;
void fragment() {
    vec3 c = texture(screen_tex, SCREEN_UV).rgb;
    COLOR = vec4(vec3(dot(c, vec3(0.299, 0.587, 0.114))), 1.0);
}
```

Set the layer/rect to keep processing while the tree is paused (`process_mode = ALWAYS`). [M12](SHADERS_GDSHADER.md) §screen.

### R13 — …show a health/progress bar?

UI: `TextureProgressBar` (fill textures, 9-slice aware) or plain `ProgressBar` + Theme. Above a character's head: small `TextureProgressBar` as a **world-space child** of the character (§3.5 hybrid rules). Never rebuild bars with `_draw()` unless you need custom shapes. [M04](RENDERING_AND_VISUAL_LOGIC.md) §ui.

### R14 — …highlight a furniture piece under the mouse (Relax Room)?

Decorations are runtime `Sprite2D`s with `Area2D` pickers. On hover: `sprite.self_modulate = Color(1.2, 1.2, 1.0)` (slight overbright); on exit: `Color.WHITE`. `self_modulate` leaves any child labels untouched (§8.1). In edit mode Relax Room also swaps the character's `collision_mask` from 3 to 1 so it can pass through furniture — visual + physics change together (§13, [M09](PROJECT_DEEP_DIVE.md)).

### R15 — …make rain / snow / dust?

`GPUParticles2D`, emission box wider than the screen, positioned above it; gravity + slight angular randomness; `preprocess = 2.0` so the first frame is already raining. Order it with §5: front `CanvasLayer` for "in front of everything" weather, or in-world z band for behind-the-window ambience. §10; conversions and budgets in [M14](DESKTOP_COMPANION_PERFORMANCE.md).

### R16 — …give a sprite a drop shadow?

Cheapest: duplicate `Sprite2D` child, same texture, `self_modulate = Color(0,0,0,0.4)`, offset `(3, 3)`, drawn first (tree order). Batches fine (same texture!). Shader version (skews for fake sun angle) in [M12](SHADERS_GDSHADER.md); for isometric ground shadows use a flattened ellipse under the y-sort origin ([M07](ISOMETRIC_GAMES.md)).

### R17 — …scroll/repeat a texture inside one node (conveyor, sky)?

Shader UV offset is the clean way (`UV + vec2(TIME * speed, 0.0)` with repeat-enabled texture). Node-only alternative: `Sprite2D` with `region_enabled = true` and tween `region_rect.position` — needs texture repeat import/`CanvasTexture` settings. [M12](SHADERS_GDSHADER.md); [M03](SPRITES_AND_TEXTURES.md) for repeat flags.

### R18 — …build a 9-slice panel that scales cleanly?

UI node: `NinePatchRect` with margins at the frame border widths. Themed UI (the right way for buttons/panels app-wide): `StyleBoxTexture` inside a Theme resource — Relax Room's `cozy_theme.tres` does exactly this with Kenney UI textures, four styleboxes per button state (normal/hover/pressed/disabled). [M04](RENDERING_AND_VISUAL_LOGIC.md) §theme.

### R19 — …keep pixel art crisp at any window size?

Project settings: `default_texture_filter = Nearest`, stretch mode `canvas_items` with aspect `keep` (Relax Room: 1280×720 base), scale by **integer factors** where possible (`stretch/scale_mode = integer` for strict pixel-perfect). Never mix: one LINEAR-filtered sprite in a NEAREST world screams. Full pipeline: [M03](SPRITES_AND_TEXTURES.md) §import.

### R20 — …draw a placement grid overlay (Relax Room)?

`Node2D` with `_draw()` looping `draw_line()` every `CELL_SIZE` (64 px) across the floor zone, color `Color(1,1,1,0.12)`; call `queue_redraw()` only when edit mode toggles — the cached command list makes the grid free while idle. Verbatim pattern from `room_grid.gd` (§13.4). [M04](RENDERING_AND_VISUAL_LOGIC.md) §draw.

### R21 — …burst confetti on an achievement?

`GPUParticles2D`: `one_shot = true`, `explosiveness = 1.0`, spread ~45°, gravity down, color ramp over lifetime, `emitting = true` from code per burst. Restarting: `restart()` re-fires a one-shot cleanly. On a UI `CanvasLayer` so it rains over panels (§5 priority). §10.

### R22 — …show a character silhouette through walls?

Second `AnimatedSprite2D` (or duplicate mesh of frames) as child, solid-color shader, `z_index` above the wall band, `show_behind_parent = false`; visible always, but since the normal sprite draws on top when unoccluded you only *see* it through occluders. Ordering math: §5; solid-color shader: [M12](SHADERS_GDSHADER.md). Isometric wall-fade alternative (fade the wall instead): [M07](ISOMETRIC_GAMES.md).

### R23 — …palette-swap a sprite (team colors, skins)?

Shader with a lookup: encode the source sprite in N flat "index" colors, then map each to a row of a palette texture:

```glsl
uniform sampler2D palette;   // 1×N strip: output colors
uniform int palette_row = 0; // which skin
void fragment() {
    vec4 src = texture(TEXTURE, UV);
    // red channel encodes the palette index (art authored that way)
    COLOR = vec4(texture(palette, vec2(src.r, float(palette_row))).rgb, src.a);
}
```

One sprite sheet, unlimited skins, zero extra texture memory per skin. Authoring discipline (index-encoded art) is the real cost. Full recipe with dithering caveats: [M12](SHADERS_GDSHADER.md).

### R24 — …make grass/plants sway in the wind?

Vertex shader offset weighted by height (only the top moves):

```glsl
uniform float strength = 3.0;
uniform float speed = 1.5;
void vertex() {
    float sway = sin(TIME * speed + NODE_POSITION_WORLD.x * 0.05);
    VERTEX.x += sway * strength * (1.0 - UV.y);  // UV.y=0 top … 1 root
}
```

Share one material across all plants; the `NODE_POSITION_WORLD.x` phase term desyncs them for free. Relax Room's potted plants (6× scale, §13.2) take this shader unchanged. [M12](SHADERS_GDSHADER.md) §vertex.

### R25 — …add a vignette / CRT feel over everything?

Full-rect `ColorRect` on the top `CanvasLayer` with a fragment shader: darken by distance from center (vignette), optionally add scanlines (`sin(SCREEN_UV.y * resolution)`) and slight UV barrel distortion. Pure fragment math on one quad — cheap despite being full-screen *once* (§12: it's stacked full-screen layers that hurt). Complete CRT shader walkthrough: [M12](SHADERS_GDSHADER.md) §postfx.

### Recipe → module quick map

| Recipes | Owning module |
|---------|---------------|
| R1, R2, R7, R12, R17, R22, R23, R24, R25 (shader-centric) | [Module 12 — Shaders](SHADERS_GDSHADER.md) |
| R3, R4, R5, R6, R8, R9, R10, R13, R18, R20 (rendering/tween/UI) | [Module 04 — Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) |
| R16, R17, R19 (textures/import) | [Module 03 — Sprites and Textures](SPRITES_AND_TEXTURES.md) |
| R11 (parallax) | [Module 04](RENDERING_AND_VISUAL_LOGIC.md) + §7 |
| R15, R21 (particles) | this module §10 + [Module 14](DESKTOP_COMPANION_PERFORMANCE.md) |
| R14, R20 (Relax Room patterns) | §13 + [Module 09 — Project Deep Dive](PROJECT_DEEP_DIVE.md) |
| R16, R22 isometric variants | [Module 07 — Isometric Games](ISOMETRIC_GAMES.md) |
| R4 autoload-persistent variant | [Module 13 — Autoload Safety](AUTOLOAD_SAFETY.md) |

---

## 12. Performance cheat-sheet for the 2D stack

The short version of [Module 14](DESKTOP_COMPANION_PERFORMANCE.md), restricted to visuals. Numbers are rules of thumb for a desktop 2D game at 1080p; measure before optimizing anything.

### 12.1 What each mechanism costs

| Mechanism | Cost center | Scales with | Rule of thumb |
|-----------|------------|-------------|---------------|
| Sprite2D / TileMapLayer quads | draw calls + fill rate | batches, covered pixels | hundreds of *batched* sprites are trivial |
| Draw calls (batches) | CPU→GPU submission | texture/material switches in sorted order | 2D scene comfortably < ~200; alarm at thousands |
| Batching break | extra draw call each | unique materials, texture switches, interleaved z | atlas your sprites; share `ShaderMaterial`s |
| Y-sort | CPU sort every frame | items in the y-sorted band | keep the band to dozens-hundreds, not thousands; don't y-sort static props |
| `modulate` / tint | ~free | — | never optimize this |
| Tweens / AnimationPlayer | ~free CPU | active tween count | thousands before it matters |
| canvas_item shader | GPU fragment (fill rate) | pixels covered × instruction count | full-screen shaders: budget like a post-process |
| `hint_screen_texture` | screen copy | copies per frame | 1 is fine; N stacked ⇒ N copies |
| `CanvasGroup` | offscreen composite | group screen area | use only for the overlap-fade problem |
| 2D lights + shadows | extra blend passes | lights × lit pixels; occluder count | a few lights fine; dozens = measure |
| GPUParticles2D | GPU sim + instancing | amount × overdraw | 10k particles OK on desktop GPU; overdraw kills first |
| CPUParticles2D | CPU integrate | amount | keep to hundreds |
| `SubViewport` | full extra render pass | viewport resolution | minimize size + `render_target_update_mode` only when needed |
| Texture memory | VRAM | Σ width×height×4 bytes (uncompressed RGBA) | 4096×4096 RGBA ≈ 64 MB + mipmaps; atlas + import compression |
| Overdraw | fill rate | stacked transparent layers | count worst-case layers under one pixel; > 4-5 full-screen ⇒ redesign |

### 12.2 The four questions of a visual perf audit

```
1. How many draw calls?      Performance.get_monitor(
                               Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
                             Debugger ▸ Monitors ▸ Raster/Video RAM
2. What breaks the batches?  unique ShaderMaterials? mixed textures in one
                             visual band? interleaved z jumping textures?
3. Where is the fill rate?   stacked full-screen transparencies, oversized
                             particles, screen-reading shaders
4. What re-runs per frame?   y-sort band size, _process count, per-frame
                             queue_redraw() (should be event-driven!),
                             SubViewports with UPDATE_ALWAYS
```

Then, and only then, open the profiler — workflow, monitors and budgets in [Module 14](DESKTOP_COMPANION_PERFORMANCE.md); the frame anatomy you're measuring is §9.

### 12.3 Cheap wins checklist

- [ ] All frequently co-drawn sprites share an atlas (one texture ⇒ one batch candidate) — [M03](SPRITES_AND_TEXTURES.md)
- [ ] One shared `ShaderMaterial` resource per effect, parameters via `instance uniforms` when per-node values are needed — [M12](SHADERS_GDSHADER.md)
- [ ] Y-sort only on the band that needs it (characters + obstacles), never the whole world
- [ ] `queue_redraw()` called on events, never in `_process`
- [ ] Particles: modest `amount`, small textures, avoid huge semi-transparent quads (overdraw)
- [ ] `SubViewport.render_target_update_mode = UPDATE_ONCE`/`WHEN_VISIBLE` where possible
- [ ] `visible = false` for off-duty overlays (culling is good, not existing is better)
- [ ] Pixel-art project: small source textures + NEAREST beats big textures scaled down (Relax Room's 180×155 background is the poster child)

### 12.4 Monitors worth knowing by name

Readable in code (`Performance.get_monitor(...)`) and live in **Debugger ▸ Monitors** while the game runs — no profiler session needed for a first look:

| Monitor | Tells you | First-look threshold (desktop 2D) |
|---------|-----------|-----------------------------------|
| `TIME_FPS` / `TIME_PROCESS` | overall frame health / Act I script time | 60 fps stable; process < ~8 ms |
| `RENDER_TOTAL_DRAW_CALLS_IN_FRAME` | Act II/III output — batches submitted | < ~200 comfortable; investigate at 1,000+ |
| `RENDER_TOTAL_PRIMITIVES_IN_FRAME` | vertex volume | rarely the 2D bottleneck; huge = runaway particles |
| `RENDER_TEXTURE_MEM_USED` | VRAM held by textures (§6.2 math check) | should match your back-of-envelope; jumps = import regressions |
| `RENDER_TOTAL_OBJECTS_IN_FRAME` | canvas items submitted after culling (Act II output) | tracks scene density; sudden spikes = runaway spawns |
| `RENDER_TOTAL_VIDEO_MEM_USED` | total VRAM (textures + buffers) | ≈ texture memory + particle/mesh buffers; compare with §6.2 math |
| `OBJECT_NODE_COUNT` | tree size (runtime spawns leaking?) | steady in steady state; climbing = leak |
| `TIME_PHYSICS_PROCESS` | physics tick cost (not visual, but shares the frame) | < ~4 ms |

A 10-line debug overlay `Label` printing these once per second is the cheapest performance culture a project can buy — Relax Room-sized apps never need more. Full profiler workflow (frame profiler, visual profiler, external tools): [Module 14](DESKTOP_COMPANION_PERFORMANCE.md).

### 12.5 Frame-budget worksheet (fill in per project)

At 60 fps you have **16.6 ms**; at 120 fps, 8.3 ms. Apportion *before* building, then hold changes against the allocation:

```
Target: 60 fps → 16.6 ms/frame          Relax Room actuals (desktop, iGPU):
┌───────────────────────────┬────────┐   script/tweens        < 0.5 ms
│ Act I   scripts + tweens  │ ___ ms │   static sandwich +
│ Act II  sort + batch      │ ___ ms │     ~70 decorations    < 1 ms total
│ Act III submission        │ ___ ms │   no y-sort, no lights,
│ Act IV  GPU (fill rate)   │ ___ ms │     no particles yet   ≈ idle GPU
│ physics + audio + other   │ ___ ms │   headroom             > 14 ms
│ HEADROOM (keep ≥ 20%)     │ ___ ms │   (deliberate: it's a companion
└───────────────────────────┴────────┘    app sharing the user's desktop)
```

The desktop-companion twist: Relax Room's real budget is **battery and background CPU**, not fps — a game that idles at 2% CPU is the goal, which is why every §8 ladder decision in §13 leans cheap. That budget philosophy, `low_processor_usage_mode`, and measuring idle draw are [Module 14](DESKTOP_COMPANION_PERFORMANCE.md)'s opening chapter.

### 12.6 The batching mental model — one picture

Batching is not mystical; it is a single-pass walk over the §5-sorted list that merges neighbors. Visualize the sorted draw list as beads on a string:

```
sorted draw list (one canvas layer, back → front):

 [floor][floor][floor] [chair][plant][cat] [player] [glowFX] [text][text]
  tex A  tex A  tex A   tex B  tex B  tex B  tex B    mat X!   font  font
 └────── batch 1 ─────┘└──────── batch 2 ────────┘  └batch 3┘└─ batch 4 ─┘

 4 draw calls.  Now give the plant its own outline material:

 [floor×3]        [chair] [plant] [cat][player]  [glowFX] [text×2]
 └─ batch 1 ─┘    └─ 2 ─┘ └─ 3 ─┘└──── 4 ────┘   └─ 5 ─┘  └─ 6 ─┘

 6 draw calls — one material inserted TWO breaks (before and after).
```

Three rules fall out of the picture: (1) *interleaving* different textures in draw order is as bad as different materials — atlas what draws together so neighbors share; (2) a per-instance effect is cheapest when expressed as *data* the shared material reads (instance uniforms, `INSTANCE_CUSTOM`), not as a copied material; (3) z_index shuffling that interleaves texture groups silently multiplies batches — another reason to order with structure (§5.5 registry) instead of scattered z values.

---

## 13. Case study — the Relax Room visual stack

Everything above, instantiated in one small production project. Relax Room is a desktop companion app: one isometric-ish cozy room, a controllable character, drag-and-drop furniture, themed color overlays, and a parallax menu. Its stack is deliberately minimal — a worked argument that you should **buy only the machinery your game needs**.

### 13.1 The theater, in stack terms

```
VIEWPORT 1280×720 (stretch: canvas_items, clear color #1f1c2e)
┌──────────────────────────────────────────────────────────────┐
│ CanvasLayer layer=100  → decoration popup, auth screen       │  §5 P1
│ CanvasLayer layer=10   → UILayer: buttons, HUD, panels       │  §5 P1
│ ── world (follows nothing; static camera in-room) ────────── │
│ RoomGrid (Node2D, _draw 64px grid, event-driven redraw)      │  §3.4
│ Character (CharacterBody2D + AnimatedSprite2D, 16 anims)     │  §3.3
│ Decorations (Node2D; runtime Sprite2D per furniture item)    │  §3.1
│ RoomBounds (StaticBody2D — invisible, physics only)          │
│ Baseboard (ColorRect, 1px wall/floor divider)                │
│ WallRect + FloorRect (ColorRect overlays, alpha 0.6, themed) │  §8
│ RoomBackground (Sprite2D, room.png 180×155 scaled 4×)        │  §3.1
└──────────────────────────────────────────────────────────────┘
```

Boot flow: `main.gd` loads the saved room → places `room.png` → reads the theme from `rooms.json` and colors `WallRect`/`FloorRect` → `room_base.gd` reads saved decorations and instantiates `Sprite2D`s → instantiates the character `PackedScene` → shows UI on the CanvasLayer.

### 13.2 Room geometry — the numbers that shape every visual decision

```
0px                                                        1280px
 ┌────────────────────────────────────────────────────────────┐
 │                       WALL ZONE (40%)                      │
 │                 wall_color overlay, alpha 0.6              │
 ├──────────────────── y = 288 ───────────────────────────────┤ ← baseboard
 │   x=280 ┌──────────────────────────────┐ x=1000            │
 │         │      FLOOR ZONE (60%)        │                   │
 │         │  floor_color overlay, α 0.6  │                   │
 │         │  64px placement grid         │                   │
 │         │  furniture + character here  │                   │
 │         └──────────────────────────────┘ y=670             │
 └────────────────────────────────────────────────────────────┘ 720px
```

| Constant | Value | Meaning |
|----------|-------|---------|
| Viewport | 1280 × 720 | base resolution; stretch `canvas_items` |
| Clear color | `#1f1c2e` | dark violet behind everything |
| Default filter | NEAREST | global pixel-art crispness ([M03](SPRITES_AND_TEXTURES.md)) |
| `WALL_ZONE_RATIO` | 0.4 | top 40% wall, bottom 60% floor |
| `ROOM_LEFT` / `ROOM_RIGHT` | 280 / 1000 px | playable horizontal bounds |
| `ROOM_BOTTOM` | 670 px | bottom margin |
| `CELL_SIZE` | 64 px | placement grid cell |
| `OVERLAY_ALPHA` | 0.6 | theme overlay opacity |
| Grid opacity | 12% | near-invisible white guide lines |
| Character scale (room / menu) | 3.0× / 4.0× | 32 px frames → 96 / 128 px |
| Furniture / plants / pet scale | 3.0× / 6.0× / 4.0× | plants' source art is finer, hence 6× |
| Animation FPS (normal / rotate) | 5.0 / 3.0 | SpriteFrames per-animation FPS (§4) |
| Panel fade / scene fade / walk-in | 0.3 s / 0.5 s / 2.0 s | tween durations |
| `PARALLAX_STRENGTH` | 8.0 px | menu parallax max shift |
| CanvasLayer UI / popup | 10 / 100 | §5 priority in action |
| Collision layer walls / decorations | 1 / 2 | mask 3 normally, 1 in edit mode |

### 13.3 Sprites and animation choices

- **Background:** a single hand-painted `room.png` (180×155!) scaled 4×, NEAREST-filtered — the "poster, not tiles" decision (§13.6). Import: lossless, no mipmaps, `fix_alpha_border = true`.
- **Decorations:** created **at runtime** from `data/decorations.json` (69 items): `Sprite2D.new()` → `load(sprite_path)` → `scale` by type → `centered = false` → position snapped to the 64 px grid. `centered = false` makes grid math trivial: position = cell origin, no half-size offsets.
- **Room character:** `AnimatedSprite2D` + `SpriteFrames` with 16 animations (idle/walk/interact × directions + `rotate`), frames as `AtlasTexture` regions of 128×32 strips (4 × 32×32). 8-way input collapses to 5 states + `flip_h` (§4.1).
- **Menu character:** plain `Sprite2D` + `hframes` + a 0.15 s `Timer` cycling `frame = (frame + 1) % 4` — one trivial loop didn't justify a `SpriteFrames` asset (§3.3's "exactly one animation" leaf, argued for real).

### 13.4 Rendering mechanisms in use

- **Theme system as color math:** three themes in `rooms.json` (`modern` violet, `natural` green, `pink`) recolor the room purely via two `ColorRect` overlays at `OVERLAY_ALPHA 0.6` — the base art never changes. This is the `modulate`-family row of §8 applied at architecture level: cheapest technique that works.
- **Placement grid:** `room_grid.gd` `_draw()`s 64 px lines across the floor zone at 12% white; `decoration_mode_changed` (via the signal bus) triggers `queue_redraw()` — the §9 Act I hook used correctly (zero idle cost).
- **Draw order:** pure tree order for the static sandwich (§5 P4 is enough when layers never interleave), `CanvasLayer` 10/100 for UI/popups (§5 P1). No z_index gymnastics, no y-sort — the character visually overlapping furniture is accepted as a simplification (and listed as future work in §13.6).
- **UI:** `cozy_theme.tres` Theme resource, `StyleBoxTexture` 9-slice from Kenney UI art, four styleboxes per button state; simple panels are **built in code** and faded in/out by `panel_manager.gd` with the kill-before-recreate tween pattern (§4.2).

### 13.5 The menu sequence — tweens + manual parallax

```
loading screen (alpha 1)
   │ tween_interval(0.4)
   │ tween_property(loading, "modulate:a", 0.0, 0.5)
   │ tween_callback(hide loading)
   ▼
8-layer forest background, mouse parallax
   │ tween_callback(character.walk_in)      # x: −100 → 640 over 2.0 s
   │                                        # EASE_OUT + TRANS_QUAD
   ▼
buttons fade in (0.3 s) → interactive
```

In code, the whole intro is a single chained tween (`main_menu.gd`) — the §4.2 sequencing pattern verbatim:

```gdscript
var tween := create_tween()
tween.tween_interval(0.4)                                # hold the loading art
tween.tween_property(loading, "modulate:a", 0.0, 0.5)    # fade it out
tween.tween_callback(loading.set_visible.bind(false))    # then truly hide it
tween.tween_callback(character.walk_in)                  # hand off to the walk-in
```

The parallax is **manual** (§7's third row): `window_background.gd` shifts each of the 8 forest layers by `layer_index` pixels of mouse offset, max `PARALLAX_STRENGTH = 8.0`. No camera exists in the menu, so `Parallax2D` would add machinery without adding value — a textbook "cheapest adequate technique" call.

### 13.6 The TileMap question — a defended "no"

| Why Relax Room skips `TileMapLayer` | When the decision flips |
|--------------------------------------|-------------------------|
| The room is one hand-painted artwork; slicing it into tiles would cost its character | multiple room layouts (L-shaped, balcony, floors) |
| Free-placed `Sprite2D` decorations already give drag-and-drop with pixel freedom | a player-facing level/room editor with cell semantics |
| One rectangular room ⇒ no autotiling, no terrain, no per-cell queries needed | wall variants needing terrain autotiling + per-tile collision |
| Collision is two hand-made `StaticBody2D` polygons — cheaper than a tileset physics setup at this scale | many rooms where per-tile physics amortizes |

The full tilemap machinery this project consciously declined — `TileSet`, terrains, per-tile `y_sort_origin`, physics/navigation layers — is [Module 05](TILES_AND_TILEMAPS.md); the isometric variant it would need for diamond floors is [Module 07](ISOMETRIC_GAMES.md). A working `TileMapLayer` example ships in the repo under `addons/virtual_joystick/example/` if you want to poke one without building it.

### 13.7 Where every concept lives in the codebase

```
SPRITES & TEXTURES                         RENDERING & MOTION
├─ project.godot        NEAREST default    ├─ scripts/main.gd            theme overlays
├─ scripts/rooms/room_base.gd  runtime     ├─ scripts/rooms/room_grid.gd _draw grid
│                       decorations        ├─ scripts/rooms/window_background.gd
├─ scripts/menu/menu_character.gd          │                             8-layer parallax
│                       manual flipbook    ├─ scripts/ui/panel_manager.gd fade tweens
├─ scenes/male-old-character.tscn          ├─ scripts/menu/main_menu.gd  intro sequence
│                       16-anim SpriteFrames├─ scripts/rooms/decoration_system.gd
├─ data/decorations.json 69 items          │                             popup on layer 100
└─ data/characters.json  spritesheet paths ├─ scripts/rooms/character_controller.gd
                                           │                             8-way anim select
SCENES                                     └─ assets/ui/cozy_theme.tres  9-slice theme
├─ scenes/main/main.tscn      game room
├─ scenes/menu/main_menu.tscn menu         DATA
├─ scenes/room/*.tscn         furniture    ├─ data/rooms.json   wall/floor theme colors
└─ scenes/menu/loading_screen.tscn         └─ data/tracks.json  music catalog
```

Deeper walk-through of the same codebase (architecture, signals, persistence): [Module 09 — Project Deep Dive](PROJECT_DEEP_DIVE.md).

### 13.8 Node census with teaching analogies

The project's complete visual-node vocabulary, with the analogies this course uses when onboarding non-Godot readers (kept from the original summary — they work):

| Node | Analogy | Where Relax Room uses it |
|------|---------|--------------------------|
| `Node2D` | empty box for grouping | `Room`, `Decorations`, `ForestBackground` |
| `Sprite2D` | a sticker / photo | room background, decorations, parallax layers |
| `AnimatedSprite2D` | automatic flipbook | room character, loading screen |
| `CharacterBody2D` | an actor that walks and hits walls | the playable character |
| `StaticBody2D` | an immovable wall | room bounds, furniture collision |
| `CollisionShape2D` / `CollisionPolygon2D` | the invisible outline used for collision | character capsule / 8-point furniture polygons |
| `CanvasLayer` | a glass sheet in front of everything | UILayer (10), popups (100) |
| `ColorRect` | a sheet of colored film | wall/floor theme overlays, menu dim |
| `Camera2D` | the camera framing the stage | loading screen (3.6× zoom) |
| `Control` | base for all UI furniture | buttons, panels, labels |
| `Timer` | an alarm clock | menu character frame stepping |

Two analogies deserve promotion to principles: **CanvasLayer = separate glass sheets** (reordering papers on one desk never beats a higher desk — §5 rule 1) and **modulate = colored film that multiplies** (two 50% films stack to 25% — §8.1).

### 13.9 Signals, lifecycle and visual state — the wiring under the visuals

Three lifecycle rules from [Module 02](SCENES_AND_NODES.md) keep Relax Room's visual state honest, and every visual system in this module depends on them:

1. **Visual reactions ride the signal bus, not polling.** The placement grid never checks a flag in `_process`; it connects to `SignalBus.decoration_mode_changed` and calls `queue_redraw()` on the event. Event-driven redraws are the difference between a free overlay and a per-frame cost (§9 Act I, §12 checklist).
2. **Global signal connections are disconnected in `_exit_tree()`.** A room being freed while the immortal `SignalBus` still holds its callback is a crash on the next emit:

```gdscript
# room_base.gd
func _exit_tree() -> void:
    if SignalBus.character_changed.is_connected(_on_character_changed):
        SignalBus.character_changed.disconnect(_on_character_changed)
```

   Parent→child connections (`$Timer.timeout.connect(...)`) clean themselves up with the subtree; only *outliving* emitters need manual hygiene. The full autoload-safety contract is [Module 13](AUTOLOAD_SAFETY.md).
3. **Structural changes defer.** Spawning decorations while the tree is mid-iteration uses `call_deferred("add_child", sprite)` — mutate the tree between frames, not during traversal. Same discipline for freeing: `queue_free()`, never `free()` mid-signal ([M02](SCENES_AND_NODES.md)).

The takeaway for the visual stack: **rendering state (what §5 orders and §8 styles) is downstream of tree state** — a visually flawless scene with sloppy lifecycle wiring is a crash reported as "the screen went black".

### 13.10 Thought experiment — the same game at 10× scope

What survives if Relax Room grew into a multi-room, multi-floor home designer? Running the §3 trees again with the new requirements is a great final exercise in decision hygiene:

| Current choice | At 10× scope | Verdict |
|----------------|--------------|---------|
| One painted `room.png` per room | dozens of layouts, wall variants, player-built walls | flips to `TileMapLayer` + terrains (§3.2, [M05](TILES_AND_TILEMAPS.md)); painted art survives as *hero* set-pieces |
| Free `Sprite2D` decorations, JSON-driven | hundreds of items, rotation, stacking rules | keeps! — free placement is the product; add an `AtlasTexture` mega-atlas for batching (§12.6) |
| No y-sort (accepted overlap glitches) | characters walking among tall furniture across rooms | flips: one y-sorted band per floor, origins at bases (§5.6) |
| Tree-order static sandwich | interleaved floors/mezzanines | keeps the registry idea (§5.5) but adds per-floor z bands |
| ColorRect theme overlays | per-room lighting moods, windows with daylight | `CanvasModulate` per floor + a few `PointLight2D`s; overlays stay for tint accents (§8 ladder — still no shaders needed) |
| Manual menu parallax | a real camera scrolling between rooms | flips to `Parallax2D` (§7's own advice) |
| No particles | fireplace, dust in sunbeams | `GPUParticles2D` with §10.4-style budgets |

The pattern: **content-scaling flips content decisions (tiles, y-sort); the ordering registry, the effects ladder discipline, and the batching habits scale unchanged.** That is why this module spends more lines on principles than on nodes.

---

## 14. Glossary map — every concept to its owning module

Use this table as the domain's visual-stack index: concept → where it is taught in depth.

| Concept | Owning module | Also touched in |
|---------|---------------|-----------------|
| `Sprite2D`, `offset`, `centered`, `flip_h/v` | [M03 Sprites](SPRITES_AND_TEXTURES.md) | §3.1, §13.3 |
| Texture import, filters (NEAREST/LINEAR), mipmaps | [M03 Sprites](SPRITES_AND_TEXTURES.md) | §6, R19 |
| `AtlasTexture`, spritesheets, `hframes/vframes` | [M03 Sprites](SPRITES_AND_TEXTURES.md) | §6, §13.3 |
| `AnimatedSprite2D`, `SpriteFrames` | [M03 Sprites](SPRITES_AND_TEXTURES.md) | §3.3, §4 |
| `AnimationPlayer`, `AnimationTree` | [M03 Sprites](SPRITES_AND_TEXTURES.md) | §4 |
| Scene tree, lifecycle, `PackedScene`, `@onready` | [M02 Scenes](SCENES_AND_NODES.md) | §5 (tree order) |
| `z_index`, `z_as_relative`, Y-sort | [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | §5 |
| `CanvasLayer`, `follow_viewport_enabled` | [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | §5, §13.4 |
| `modulate`, `self_modulate`, `CanvasModulate` | [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | §8, R3 |
| `_draw()`, `queue_redraw()`, draw_* API | [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | §3.4, R20 |
| `Tween`, easing, chaining, lifecycle | [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | §4.2, R4-R6, R10 |
| `Viewport`, `SubViewport`, `Camera2D` | [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | §6, R5, R9 |
| Theme, `StyleBoxTexture`, 9-slice, `NinePatchRect` | [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | R18, §13.4 |
| 2D lights, occluders, shadows | [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | §8 |
| `Parallax2D` (and deprecated ParallaxBackground) | [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | §7, R11, §13.5 |
| `TileSet`, `TileMapLayer`, terrains/autotiling | [M05 Tilemaps](TILES_AND_TILEMAPS.md) | §3.2, §13.6 |
| Per-tile physics, navigation, custom data | [M05 Tilemaps](TILES_AND_TILEMAPS.md) | §3.2 |
| Isometric projection, diamond tiles, iso y-sort | [M07 Isometric](ISOMETRIC_GAMES.md) | §3.2, §5.2 |
| GDShader, uniforms, `TIME`, `hint_screen_texture` | [M12 Shaders](SHADERS_GDSHADER.md) | §8, R1-R2, R7, R12 |
| Particles (GPU/CPU), process material | this module §10 | [M14 Performance](DESKTOP_COMPANION_PERFORMANCE.md) |
| Draw calls, batching, profiling, monitors | [M14 Performance](DESKTOP_COMPANION_PERFORMANCE.md) | §9, §12 |
| `CanvasItemMaterial`, blend modes (add/multiply) | [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | §8.4 |
| `CanvasGroup`, group compositing | [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | §8, R-map |
| Transform chain (local→global→canvas→screen) | [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | §9.7 |
| `MultiMeshInstance2D`, instancing | [M14 Performance](DESKTOP_COMPANION_PERFORMANCE.md) | §3.6 |
| Batching model, draw-call budgets | [M14 Performance](DESKTOP_COMPANION_PERFORMANCE.md) | §12.6 |
| Signal bus hygiene, `_exit_tree` disconnects | [M13 Autoload Safety](AUTOLOAD_SAFETY.md) | §13.9 |
| Relax Room architecture, signal bus, persistence | [M09 Deep Dive](PROJECT_DEEP_DIVE.md) | §13 |
| Full terminology | [00-GLOSSARY.md](00-GLOSSARY.md) | this module's glossary |

### 14.1 Reverse index — "I'm opening module X; what does it owe this summary?"

| Module | Pull from it when this summary says… |
|--------|--------------------------------------|
| [M02 Scenes](SCENES_AND_NODES.md) | "tree order", "lifecycle", "`call_deferred`", "Remote tab" |
| [M03 Sprites](SPRITES_AND_TEXTURES.md) | "import settings", "atlas", "SpriteFrames", "filtering" |
| [M04 Rendering](RENDERING_AND_VISUAL_LOGIC.md) | "z/layer/y-sort details", "tween API", "`_draw()` API", "Theme", "viewport" |
| [M05 Tilemaps](TILES_AND_TILEMAPS.md) | "TileSet setup", "terrains", "per-tile anything" |
| [M07 Isometric](ISOMETRIC_GAMES.md) | "diamond", "iso y-sort", "elevation" |
| [M12 Shaders](SHADERS_GDSHADER.md) | any GLSL block in §11, "instance uniforms", "screen texture" |
| [M14 Performance](DESKTOP_COMPANION_PERFORMANCE.md) | "profiler", "monitors", "budget", "warm-up" |
| [M09 Deep Dive](PROJECT_DEEP_DIVE.md) | any `scripts/…` or `data/…` path in §13 |

---

## Best practices

The consolidated visual-stack checklist. Each item condenses a rule argued at length in the linked module; run through it at scene-design time and again before shipping.

### Choosing nodes (§3)

- [ ] **World visuals are Node2D-family, UI is Control-family under a CanvasLayer** — never mix directions (§3.5).
- [ ] **One image → `Sprite2D` (world) / `TextureRect` (UI); grid → `TileMapLayer`; population → particles.** If your choice isn't a leaf of a §3 tree, re-derive it.
- [ ] **Prefer the boring node.** `ColorRect` before shader, `Sprite2D` before `_draw()`, `_draw()` before `SubViewport`.
- [ ] **Name the decision in a comment** when you deviate ("Sprite2D grid instead of TileMapLayer because artwork is one painting" — Relax Room does this culture right, §13.6).

### Draw order (§5)

- [ ] **Reserve CanvasLayer indices project-wide** and write them down (Relax Room: 0 world, 10 UI, 100 popups). Ad-hoc layer numbers are how "why is the popup under the HUD" happens.
- [ ] **Use the weakest lever that solves the problem**: tree order → y-sort → z_index → CanvasLayer, not the reverse.
- [ ] **Y-sort one band, not the world**; all members at the same effective `z_index`, parent flag on.
- [ ] **Never position UI with `z_index`** — order the Control tree instead.

### Textures and sprites (§4, §6)

- [ ] **Pick the filter per art style project-wide** (`default_texture_filter = Nearest` for pixel art) and override per-item only with a reason.
- [ ] **Atlas what draws together**; same texture ⇒ batchable (§12).
- [ ] **`centered = false` for grid-snapped sprites** — position math becomes cell math (§13.3).
- [ ] **Mirror with `flip_h`, don't duplicate art** (halves sprite memory; §4.1).
- [ ] **Import settings are part of the asset**: lossless + no mipmaps for pixel art, and commit the `.import` files.

### Motion and effects (§4, §8, §10)

- [ ] **Kill-before-recreate for every retriggerable tween** (§4.2). No exceptions; this is the most common visual-state bug.
- [ ] **Escalate the §8 ladder top-down** and stop at the first rung that looks right.
- [ ] **Share `ShaderMaterial` resources**; per-node values via instance uniforms, not duplicated materials (§12).
- [ ] **`queue_redraw()` on events, never per frame**, unless the drawing truly changes every frame.
- [ ] **Particles get budgets** (`amount`, texture size) at creation time, not after the frame drops.

### Performance hygiene (§12)

- [ ] **Check draw calls once per milestone** (`Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME`), so regressions surface while the cause is fresh.
- [ ] **Count worst-case transparent layers under one pixel**; > 4-5 full-screen layers means restructure (overdraw).
- [ ] **Hide (or free) what's off-duty** — `visible = false` beats alpha 0 (alpha 0 still draws!).
- [ ] **Profile before optimizing** — [Module 14](DESKTOP_COMPANION_PERFORMANCE.md) workflow; this module only tells you where to look first.

### Review script for a visual-stack PR

When reviewing (or self-reviewing) any change that touches visuals, ask in order:

1. Is every new node a leaf of a §3 tree? If not, why not — is the reason written down?
2. Which §5 lever orders each new element, and is it the weakest one that works?
3. Which §8 rung is each new effect on, and did anything skip a cheaper rung without a stated reason?
4. Did draw calls move? (One monitor read before/after — 30 seconds.)
5. Do new tweens follow kill-before-recreate? Do new `_draw()`s redraw on events only?
6. Are new materials shared resources, or per-node copies?

Six questions, five minutes, and the two most expensive classes of visual debt (ordering hacks and batching decay) never land on main.

### Phase 2 exit criteria

You are done with the visual-systems phase (Modules 03-07 + 12 + this summary) when you can, without notes:

1. Take any mockup and produce a node stack + ordering plan in ten minutes (Exercise 1 standard).
2. Explain a draw-order bug to a teammate using only the words *layer, z, y-sort, tree order* — in that order (§5).
3. Name the §8 rung of every effect in your current project, and defend the two most expensive ones.
4. Read a frame's draw-call count and say whether it is normal *for that scene* (§12).
5. Point at any concept in the concept map and name its owning module file within seconds (§14).

If one of the five fails, the §14 table says exactly which module to reopen. The [capstone](00-CAPSTONE.md) design review grades against this list.

---

## Common errors & troubleshooting

Visual bugs sorted by symptom. The Fix column names the exact property/section; deep explanations live in the linked modules.

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Pixel art looks blurry | LINEAR filtering (default in some templates) | project `default_texture_filter = Nearest`, or per-node `texture_filter`; re-check imports ([M03](SPRITES_AND_TEXTURES.md), R19) |
| Pixel art blurry only when moving | camera/sprite at fractional pixel positions | snap positions (`round()`), enable 2D pixel snap (`rendering/2d/snap/snap_2d_transforms_to_pixel`) |
| Sprite has dark halo at transparent edges | alpha bleed in source PNG | import `fix_alpha_border = true`; re-export art with premultiplied-safe edges ([M03](SPRITES_AND_TEXTURES.md)) |
| Spritesheet frame shows slivers of neighbor frames | `AtlasTexture` region touching adjacent frames + filtering | add padding/extrude margins in the atlas; exact region rects ([M03](SPRITES_AND_TEXTURES.md)) |
| Node invisible though `visible = true` | parent hidden, `modulate.a == 0`, off-screen position, or behind an opaque item | walk the checklist in §2.1 Q2/Q3: parent chain → alpha chain → position → draw order |
| "My z_index does nothing" | element is on a different `CanvasLayer` — layer beats z (§5 rule 1) | move it to the same layer, or change `CanvasLayer.layer` |
| UI element scrolls away with the camera | UI placed in the world instead of a `CanvasLayer` | reparent under the UI CanvasLayer (§3.5) |
| World object frozen on screen, ignores camera | world object parked under a `CanvasLayer` | move it back into the world tree (§5 rule 6) |
| Character draws behind/in front of furniture wrongly | no shared y-sort band, or different z_index breaking ties | same parent with `y_sort_enabled = true`, equal z (§5.2) |
| Y-sorted character flickers in front/behind while walking | sprite origin at top-left/center instead of at the **feet** | set sprite `offset` so the node origin sits at the visual base; per-tile `y_sort_origin` for tiles ([M07](ISOMETRIC_GAMES.md)) |
| Y-sort "just doesn't work" | `y_sort_enabled` set on the children, not the parent | flag the **parent** (and each participating `TileMapLayer`) (§5 rule 4) |
| Two static sprites randomly swap order | identical layer/z/y → tree order is the tiebreaker and someone `add_child`ed in variable order | set explicit z or fixed tree order (`move_child`) (§5 rule 5) |
| Fade-in fades to 25% then jumps | nested `modulate` multiplication (parent also faded) | fade one ancestor only, or use `self_modulate` (§8.1) |
| Group fade shows dark overlapping seams | children blended individually | `CanvasGroup`, then fade the group (§8, cost note §12) |
| Flash-to-white does nothing | `modulate` can only multiply toward black | white-flash shader or HDR overbright tween (R2) |
| Tween stutters or property "fights" itself | two live tweens on one property | kill-before-recreate pattern (§4.2) |
| Tween error "invalid property" | wrong property path (e.g. `alpha` instead of `modulate:a`) | use `"modulate:a"`, `"position:x"` sub-property syntax ([M04](RENDERING_AND_VISUAL_LOGIC.md)) |
| Button scales from its corner when pulsed | `pivot_offset` at (0,0) default | set `pivot_offset = size / 2` before scaling (R10) |
| `_draw()` never appears | drew once before data was ready, never redrawn | call `queue_redraw()` when state changes; check it's a `CanvasItem` subclass ([M04](RENDERING_AND_VISUAL_LOGIC.md)) |
| `_draw()` grid eats CPU | `queue_redraw()` in `_process` | redraw on events only (§13.4 pattern) |
| Screen-reading shader shows black | forgot `hint_screen_texture` uniform, or reading in the same item being drawn first | declare `uniform sampler2D t : hint_screen_texture;` sample `SCREEN_UV`; put the effect on a top layer (R12, [M12](SHADERS_GDSHADER.md)) |
| Shader works in editor, breaks on export | GLES/compatibility-only syntax, or texture not imported | test with the target renderer; [M12](SHADERS_GDSHADER.md) portability notes |
| Draw calls exploded after adding an effect | per-node duplicated `ShaderMaterial`s splitting batches | share one material; instance uniforms for per-node params (§12) |
| Particles invisible | `emitting = false`, lifetime 0, texture missing, or emitting off-screen with local coords | check `emitting`, `amount`, `texture`, and `local_coords` vs moving parent (§10) |
| One-shot particles fire once then never again | `one_shot` finished and `emitting` stayed false | call `restart()` per burst (R21) |
| Rain appears only after a delay | particles start empty | `preprocess` = a few seconds (R15) |
| Particles freeze when many spawn (low-end) | CPU particles over budget | reduce `amount` or switch to `GPUParticles2D` (§10.1) |
| TileMap tutorial code errors (`set_cell` on TileMap, layers argument) | Godot ≤4.2 API — `TileMap` deprecated | one `TileMapLayer` node per layer, `set_cell(coords, source_id, atlas_coords)` ([M05](TILES_AND_TILEMAPS.md)) |
| Parallax layers don't move | `ParallaxBackground` without camera scroll, or deprecated pair misconfigured | use `Parallax2D` + `scroll_scale`; manual offsets if there's no camera (§7, §13.5) |
| Parallax texture shows a hard seam | repeat size not matching texture width | `Parallax2D.repeat_size.x = texture width` (R11) |
| Minimap costs half the frame | `SubViewport` at full resolution, `UPDATE_ALWAYS` | shrink resolution, `WHEN_VISIBLE`/lower update rate, or `_draw()` dots instead (R9, §12) |
| Whole game tinted unexpectedly | forgotten `CanvasModulate` (often from an experiment) | search the scene for `CanvasModulate`; it affects its entire layer (R3) |
| Everything invisible after "cleanup" | an ancestor's `visible`/`modulate.a` toggled by leftover code | binary-search the tree with the Remote tab while running ([M02](SCENES_AND_NODES.md)) |
| 9-slice frame corners look stretched | margins not matching the texture's border widths | set `NinePatchRect` patch margins / `StyleBoxTexture` margins to the frame's pixel borders (R18) |
| Themed button ignores your style change | style overridden at a more specific level (node override beats Theme) | check `add_theme_*_override` on the node, then Theme type variations ([M04](RENDERING_AND_VISUAL_LOGIC.md) §theme) |
| `Line2D` trail moves with the sprite instead of trailing | trail node is a **child** of the moving object | make it a sibling; feed `global_position` (R8) |
| Y-sorted `TileMapLayer` draws whole rows wrongly against characters | layer not participating in the parent's y-sort | `y_sort_enabled` on the TileMapLayer too; tune per-tile `y_sort_origin` ([M05](TILES_AND_TILEMAPS.md)) |
| Isometric tiles overlap in the wrong diagonal order | square y-sort assumptions on a diamond grid | follow [M07](ISOMETRIC_GAMES.md)'s iso ordering setup (origin at tile base, correct layout mode) |
| Sudden aliasing/shimmer when camera zooms out (HD art) | mipmaps disabled on heavily downscaled textures | enable mipmaps for that asset class (§6.1) — pixel art excepted |
| Colors slightly off after export | VRAM compression on art meant to be lossless | per-asset import: Lossless; check Import Defaults (§6.1) |
| Frame spikes when a big popup opens | first-use shader compilation / texture upload | warm up: instance the popup once at load, hidden ([M14](DESKTOP_COMPANION_PERFORMANCE.md)) |
| Additive glow invisible over bright areas | ADD blend saturates against light backgrounds | reduce glow brightness, or switch to a mix-blended halo sprite (§8.4) |
| Particles emit from the wrong place after reparenting | `local_coords = true` with a moved parent | set `local_coords = false` for world-anchored effects (§10.4) |
| `ViewportTexture` shows nothing / error about local-to-scene | texture resource not marked local to scene, or path set before the viewport entered the tree | enable "Local to Scene" on the resource; assign the path in `_ready()` ([M04](RENDERING_AND_VISUAL_LOGIC.md)) |

---

## Exercises

Synthesis exercises: each one forces a **choice between stack options plus a justification** — the skill this module exists to train. Write the justification down; comparing it to the cited sections is the actual exercise.

### Exercise 1 — Node stack from a mockup

A mockup shows: painted sky, three scrolling hill layers at different speeds, a square-grid meadow with paths, ~30 free-placed trees, a player character with 8-direction walk cycles, birds occasionally crossing the sky, and a HUD (hearts + coin counter).

**Task:** name the full node stack — one node type per element, parent structure, and every draw-order lever used. Justify each against §3's trees and §5's table. Then write the §12 audit answers you'd *expect* (rough draw-call count, y-sort band size).

### Exercise 2 — Draw-order prediction on paper

Take §5.2's worked example and (a) move `Cursor` under `UILayer`, (b) set `Chair.z_index = 1`, (c) set `y_sort_enabled = false` on `World`. For each change independently, write the new back-to-front order and one sentence on why. Verify in a scratch project only after committing to answers.

### Exercise 3 — Effect ladder judgment calls

For each effect, name the *cheapest adequate* technique from §8 and the first reason the next-cheaper rung fails: (a) poison tint on a character, (b) character flashing white on hit, (c) whole screen desaturating on pause, (d) sparkles around a collected coin, (e) a 3-item inventory panel fading in as one unit over the game, (f) heat shimmer above a stove.

### Exercise 4 — Animation tool triage

Classify each into `AnimatedSprite2D` / `AnimationPlayer` / `Tween` / shader / particles (§3.3, §4): (a) 12-state enemy with synced attack hitboxes and footstep sounds, (b) chest lid opening once when clicked, (c) waterfall surface, (d) menu camera slowly drifting, (e) leaves falling continuously, (f) NPC with two idle frames. One sentence each.

### Exercise 5 — Frame-story debugging

A tester reports: "game hitches every time the shop opens." Using §9's acts, list — in order — the four questions you'd ask and the tool/monitor answering each (e.g. Act I script spike? Act II batch explosion from the shop's unique materials? …). End with your single most likely hypothesis for a shop popup built from 40 uniquely-materialed item icons.

### Exercise 6 — Particles vs the world

Design "fireflies at dusk in the Relax Room window" twice: once with `GPUParticles2D` (list the five §10.2 properties with concrete values) and once **without** particles (nodes + tweens/shader). Compare: node count, per-frame cost class, authoring time, and which you'd ship for a battery-friendly desktop companion ([M14](DESKTOP_COMPANION_PERFORMANCE.md) mindset).

### Exercise 7 — Relax Room extension: the balcony

Relax Room adds an L-shaped balcony with a different floor material, reachable through a door. Decide: does the "no TileMap" position (§13.6) survive? Specify what changes in the sandwich (§13.1), whether y-sort becomes necessary for the character vs balcony railing, and which constants of §13.2 must generalize. Defend in ~10 lines.

### Exercise 8 — Recipe remix

Combine R5 (screen shake), R6 (floating text) and R21 (confetti burst) into one "achievement unlocked" moment. Write the orchestration code skeleton (one function, tweens + `restart()` calls), then annotate each line with the §5 layer it plays on and the §8/§10 cost class it incurs.

### Self-check quiz

Twelve rapid checks; answers cite the section that settles each. Aim for 10+ before relying on this module as a reference.

| # | Question | Answer (check yourself against…) |
|---|----------|-------------------------------|
| 1 | A node has `z_index = 4096` but still draws under the HUD. Why? | HUD is on a higher `CanvasLayer`; layer beats z (§5 rule 1) |
| 2 | What must be true for Y-sort to decide between two items? | common y-sorted parent AND equal effective z_index (§5 rule 3) |
| 3 | Parent `modulate.a = 0.5`, child `= 0.5` — child's on-screen alpha? | 0.25 — modulate multiplies down the tree (§8.1) |
| 4 | Cheapest way to tint the whole world at dusk without touching the UI? | `CanvasModulate` in the world layer; UI lives on its own CanvasLayer (R3) |
| 5 | When does `_draw()` re-run? | only after `queue_redraw()` (or first show) — output is cached (§9.2) |
| 6 | One animation, four frames, on a menu prop — which tool? | `Sprite2D` + `hframes` + Timer/`frame` stepping; SpriteFrames is overkill (§3.3, §13.3) |
| 7 | Name the two things that most commonly split 2D batches. | texture switches and unique per-node materials in draw order (§9.3, §12) |
| 8 | Confetti burst: which three particle properties define "burst"? | `one_shot = true`, `explosiveness = 1.0`, `restart()` per fire (R21, §10.4) |
| 9 | Why does a flash-to-white via `modulate` fail? | modulate multiplies (can only darken/tint); use a shader mix or HDR overbright (R2) |
| 10 | The character's feet flicker in front of/behind a table while walking. First fix? | move the sprite `offset` so the node origin sits at the feet (troubleshooting) |
| 11 | Which node replaced `ParallaxBackground`, and its two key properties? | `Parallax2D`; `scroll_scale` and `repeat_size` (§7) |
| 12 | A tween-driven panel sometimes "sticks" half-open. Most likely cause? | a second tween created without killing the first (§4.2) |

### Stretch goals

1. **Batching microscope.** Build a scene of 200 `Sprite2D`s: measure `RENDER_TOTAL_DRAW_CALLS_IN_FRAME` with (a) one shared atlas, (b) 4 different textures interleaved, (c) one unique `ShaderMaterial` per sprite. Chart the three numbers and write the §12 explanation for each jump.
2. **Y-sort stress test.** 1,000 moving y-sorted sprites vs the same with y-sort off: compare frame time in the Monitors tab; find the count where sorting becomes visible on your machine.
3. **Decision-tree PR review.** Take any open-source Godot 4 2D project, pick one scene, and review its visual stack against §3/§5 as if reviewing a pull request — three findings minimum, each citing a section of this module.
4. **Write recipe R26.** Pick a visual trick this module lacks (e.g. water reflection, footprint decals, chromatic aberration on damage), write it in the R-format (problem → minimal approach → code → owning module), and check it against the §8 ladder.

5. **Re-derive the cheat card.** Without opening this file, rewrite §1.4 from memory; diff against the original. The lines you missed are the sections to reread — repeat monthly until the diff is empty.

6. **Instrument Relax Room.** Add the §12.4 debug overlay (fps, draw calls, texture memory) to the actual project, toggle it on a key, and record the §12.5 worksheet numbers on your machine. Compare against the "actuals" column and explain any difference.

### Answer key — Exercise 2 (check only after committing to answers)

Baseline order from §5.2 was: `a, b, d, c, e, f`.

**(a) `Cursor` moved under `UILayer`.** New order: `a, b, d, c, f-and-cursor`. The cursor now draws above the HUD's earlier siblings by tree order within layer 10 — but it also **stops following the camera** (§5 rule 6) and its `z=50` becomes meaningless across layers: layer membership replaced z as its ordering mechanism. Almost always a bug, which is the point.

**(b) `Chair.z_index = 1`.** New order: `a, b, d, e-relative…, c, e, f` — precisely: the chair leaves the y-sort tie (z now differs, §5 rule 3), so `d` (player, z=0) draws before `c` (chair, z=1) *regardless of Y*. The player can never stand in front of the chair again. One stray z value silently disabled y-sort for that pair.

**(c) `y_sort_enabled = false` on `World`.** New order: `a, b, c, d, e, f` — pure tree order among the children (§5 rule 5). Chair-vs-player overlap is now frozen by scene-file order: whichever was added later always wins, no matter who is nearer the camera. Walking "behind" the chair visually breaks immediately.

Meta-lesson: each change swapped the *governing mechanism* (layer ↔ z ↔ y-sort ↔ tree), not just the outcome — which is exactly how §5.4's flowchart diagnoses such bugs in reverse.

---

## Further reading

Official documentation (docs.godotengine.org, Godot 4.5 branch) — the canonical sources behind this module's tables:

- **[2D — Godot docs index](https://docs.godotengine.org/en/stable/tutorials/2d/index.html)** — umbrella for canvas layers, viewport/canvas transforms, and every 2D tutorial cited below. Read after §9 to see the pipeline in the engine's own words.
- **[Canvas layers](https://docs.godotengine.org/en/stable/tutorials/2d/canvas_layers.html)** and **[2D drawing (custom drawing in 2D)](https://docs.godotengine.org/en/stable/tutorials/2d/custom_drawing_in_2d.html)** — the two mechanisms most people half-know; §5 and §3.4 summarize them.
- **[Parallax2D class reference](https://docs.godotengine.org/en/stable/classes/class_parallax2d.html)** and **[2D parallax tutorial](https://docs.godotengine.org/en/stable/tutorials/2d/2d_parallax.html)** — confirms the ParallaxBackground deprecation and the `scroll_scale`/`repeat_size` model of §7.
- **[TileMapLayer class reference](https://docs.godotengine.org/en/stable/classes/class_tilemaplayer.html)** + **[Using TileMaps](https://docs.godotengine.org/en/stable/tutorials/2d/using_tilemaps.html)** — the post-4.3 layer-per-node model assumed throughout §3.2; pairs with [Module 05](TILES_AND_TILEMAPS.md).
- **[GPUParticles2D](https://docs.godotengine.org/en/stable/classes/class_gpuparticles2d.html)** / **[CPUParticles2D](https://docs.godotengine.org/en/stable/classes/class_cpuparticles2d.html)** class references + **[Particle systems (2D)](https://docs.godotengine.org/en/stable/tutorials/2d/particle_systems_2d.html)** — property-level detail behind §10.
- **[Shading language & canvas_item shaders](https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/canvas_item_shader.html)** — the reference [Module 12](SHADERS_GDSHADER.md) builds on; skim after using R7/R12.
- **[Performance: GPU optimization](https://docs.godotengine.org/en/stable/tutorials/performance/gpu_optimization.html)** and the **Performance monitors** class docs — engine-level backing for §12; continue in [Module 14](DESKTOP_COMPANION_PERFORMANCE.md).

- **[CanvasItem class reference](https://docs.godotengine.org/en/stable/classes/class_canvasitem.html)** — the single most load-bearing class page in 2D Godot: `modulate`, `z_index`, `y_sort_enabled`, `texture_filter`, `_draw()` all live here. Worth one careful full read.
- **[Viewport and canvas transforms](https://docs.godotengine.org/en/stable/tutorials/2d/2d_transforms.html)** — the official version of §9.7's transform chain, with the exact matrix names.
- **[Optimizing 2D rendering / general performance pages](https://docs.godotengine.org/en/stable/tutorials/performance/index.html)** — background for §12; note that Godot 3's "batching" article does not describe the 4.x renderer, which batches in the RenderingServer as summarized in §12.6.

In-repo continuations:

- **[Module 09 — Project Deep Dive](PROJECT_DEEP_DIVE.md)** — the full Relax Room codebase behind §13.
- **[00-GLOSSARY.md](00-GLOSSARY.md)** — domain-wide terminology superset of the glossary below.
- **[00-CAPSTONE.md](00-CAPSTONE.md)** — the final project rubric expects the §3-§5 decision vocabulary in your design doc.
- **[99-EXERCISES/README.md](99-EXERCISES/README.md)** — the domain-wide exercise ladder; this module's Exercise 1 and Stretch 3 feed its review track.

---

## Glossary

| Term | Definition |
|------|------------|
| **AtlasTexture** | Texture type exposing a rectangular region of another texture; the standard way to slice spritesheets while keeping one GPU texture (batch-friendly). |
| **Batching** | RenderingServer merging consecutive canvas items that share texture/material/blend into one draw call; broken by material or texture switches in draw order. |
| **CanvasItem** | Base class of everything drawable in 2D (`Node2D` and `Control` both inherit it); owns `visible`, `modulate`, `z_index`, `texture_filter`, `_draw()`. |
| **CanvasLayer** | Node creating an independent rendering layer with its own transform; higher `layer` draws on top of all lower layers regardless of z_index; ignores the camera unless `follow_viewport_enabled`. |
| **CanvasModulate** | Node multiplying a color over its entire canvas layer — the one-node day/night system. |
| **CanvasGroup** | Node that composites its children offscreen, then draws the result once — fixes overlapping-transparency seams at the cost of an extra composite. |
| **Draw call** | One GPU submission ("draw these vertices with this texture+shader"); the unit §12 budgets; fewer via batching. |
| **Fill rate** | GPU capacity for writing pixels per frame; consumed by every covered pixel including transparent overdraw; the cost center of full-screen shaders and big particles. |
| **Flipbook animation** | Frame-by-frame animation from pre-drawn images; in Godot: `AnimatedSprite2D`/`SpriteFrames`, or `hframes`+code. |
| **hint_screen_texture** | GDShader uniform hint giving a canvas_item shader a snapshot of the screen drawn so far (replaces Godot 3's `SCREEN_TEXTURE`); enables blur/grayscale/distortion of what's behind. |
| **Modulate** | Per-item color multiplier inherited down the tree (`self_modulate` = this item only); the cheapest tint/fade mechanism — rides along as vertex data. |
| **NinePatchRect / 9-slice** | Scaling scheme keeping corners fixed while edges/center stretch; as a Control node or as `StyleBoxTexture` in a Theme. |
| **Overdraw** | The same screen pixel being written multiple times per frame by stacked (especially transparent) items; the silent fill-rate killer. |
| **Parallax2D** | Godot 4.3+ node scrolling its children at `scroll_scale` relative to camera motion, with `repeat_size` looping; replaces the deprecated ParallaxBackground/ParallaxLayer pair. |
| **ParticleProcessMaterial** | Resource defining GPU particle simulation (velocity, gravity, color ramp, scale curve); the "brain" of `GPUParticles2D`. |
| **queue_redraw()** | Request that a CanvasItem's `_draw()` be re-recorded next frame; without it, `_draw()` output stays cached forever. |
| **RenderingServer** | The engine server owning actual canvas items and draw commands; nodes are an authoring facade over it (§9's stage manager). |
| **SpriteFrames** | Resource holding named animations (each a frame list + per-animation FPS + loop flag) consumed by `AnimatedSprite2D`. |
| **StyleBox / StyleBoxTexture** | Theme resource describing how to paint a UI element's background — flat color or 9-sliced texture; per-state (normal/hover/pressed/disabled) on buttons. |
| **SubViewport** | An offscreen viewport rendering its own subtree to a texture (`ViewportTexture`); powers minimaps and per-object post-fx at the cost of a full extra pass. |
| **TileMapLayer** | Godot 4.3+ node drawing one grid layer of tiles from a `TileSet`; one node per layer (replaces the multi-layer `TileMap` monolith). |
| **TileSet** | Resource cataloguing tiles: atlas regions, physics/occlusion/navigation per tile, terrain (autotiling) rules, custom data layers. |
| **Tween** | Runtime interpolator (`create_tween()`) animating any property over time with easing curves; fire-and-forget but must be killed before retriggering. |
| **ViewportTexture** | Texture type sampling a (Sub)Viewport's render result — render-to-texture glue. |
| **Y-sort** | Per-frame ordering of sibling canvas items by the global Y of their origin (`y_sort_enabled` on the parent); only breaks z_index ties; the mechanism behind "walk behind the table". |
| **z_index** | Per-item draw priority within a canvas layer (−4096…4096), relative to the parent's by default (`z_as_relative`); overrides tree order and Y-sort, loses to CanvasLayer. |

Domain-wide terminology: [00-GLOSSARY.md](00-GLOSSARY.md).

---

**Maintenance note.** This is a synthesis document: when a sibling module changes a recommendation (a node deprecation, a new API), the corresponding row here must change in the same commit — a decision guide that disagrees with its deep modules is worse than none. The §1.3 rename table is the first place to extend on every Godot minor-version bump.

---

*Course "Godot 4 in Production" — Phase 2, Module 06 · Synthesis of Modules [03](SPRITES_AND_TEXTURES.md), [04](RENDERING_AND_VISUAL_LOGIC.md), [05](TILES_AND_TILEMAPS.md), [07](ISOMETRIC_GAMES.md), [12](SHADERS_GDSHADER.md) · Case study: Relax Room ([Module 09](PROJECT_DEEP_DIVE.md)) · IFTS Projectwork 2026 — Relax Room Team*
