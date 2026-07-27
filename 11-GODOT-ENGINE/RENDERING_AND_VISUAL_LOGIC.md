---
course: "Godot 4 in Production"
phase: "2 — Visual systems"
module: "04"
title: "Rendering and Visual Logic — Draw Order, Custom Drawing, Tweens and Themes"
version: "Godot 4.5 / GDScript 2.0"
level: "Intermediate"
prerequisites: [ "SCENES_AND_NODES.md", "SPRITES_AND_TEXTURES.md" ]
objectives:
  - "Predict and control 2D draw order by combining tree order, z_index, Y-sort, CanvasLayer and show_behind_parent"
  - "Convert positions between local, canvas, viewport and screen coordinate spaces using Transform2D"
  - "Implement debug overlays and procedural visuals with _draw() and queue_redraw() at stable frame rates"
  - "Render to SubViewports, consume ViewportTexture, and configure resolution-independent scaling for desktop apps"
  - "Animate any property with Tween chains, selecting appropriate ease/trans pairs and killing tweens safely"
  - "Build parallax depth with Parallax2D and light a 2D scene with PointLight2D and LightOccluder2D"
  - "Skin an entire application with Theme resources, type variations, StyleBoxes and crisp font settings"
tags: [godot, gdscript, 2d-rendering, z-index, y-sort, canvaslayer, custom-drawing, tween, viewport, parallax, theme, 2d-lighting]
---

# Rendering and Visual Logic — Draw Order, Custom Drawing, Tweens and Themes — Complete Guide

> **Module 04** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Scenes and Nodes](SCENES_AND_NODES.md), [Sprites and Textures](SPRITES_AND_TEXTURES.md)
>
> By the end of this module you will be able to:
> 1. Explain exactly why any two overlapping CanvasItems draw in the order they do, using the full priority chain: CanvasLayer → z_index → Y-sort → tree order.
> 2. Move points between local, canvas, viewport and screen space with `Transform2D`, `to_global()`, `get_canvas_transform()` and `get_global_transform_with_canvas()`.
> 3. Write `_draw()` overlays (grids, gizmos, health bars, debug shapes) that redraw only when their data changes.
> 4. Set up a SubViewport as a render target, sample it with `ViewportTexture`, and pick the right project stretch settings for a desktop-resolution-independent app.
> 5. Author production-quality Tween animations: chained and parallel tweeners, correct ease/trans pairs, looping, speed scaling and leak-free kill discipline.
> 6. Add depth with `Parallax2D`, light with `PointLight2D`/`DirectionalLight2D`, and tint globally with `CanvasModulate`.
> 7. Ship a coherent UI skin with a single `Theme` resource, per-node overrides only where justified, and fonts that stay crisp at any DPI.
>
> **Estimated time:** 8-10 hours (reading 3 h · labs 5-7 h) · **Level:** Intermediate

## Guiding ideas

1. **Draw order is a pipeline, not a property.** CanvasLayer beats z_index, z_index beats Y-sort, Y-sort beats tree order — learn the chain once and every "why is this behind that?" bug becomes mechanical.
2. **`_draw()` is cached vector drawing, not immediate mode.** It runs only when Godot decides (or you call `queue_redraw()`); never put game logic in it.
3. **Tweens are fire-and-forget, but killing them is your job.** A bound tween dies with its node — every other early-exit path needs an explicit `kill()`.
4. **The viewport is a texture factory.** Everything you see is a render target; SubViewports just let you point that machinery at your own textures.
5. **Theme first, overrides last.** One `Theme` resource defines the skin; `add_theme_*_override()` is a scalpel for exceptions, not a styling system.
6. **Modulate is multiplication.** `modulate` cascades down the tree and multiplies; alpha stacks multiplicatively, which is exactly why fades compose so well — and why nested fades surprise you.

## Concept map

```
                        ┌────────────────────────────────────┐
                        │   RENDERING & VISUAL LOGIC (2D)    │
                        └──────────────────┬─────────────────┘
                                           │
        ┌──────────────────┬───────────────┼────────────────┬──────────────────┐
        │                  │               │                │                  │
 ┌──────▼──────┐   ┌───────▼───────┐ ┌─────▼──────┐  ┌──────▼──────┐  ┌────────▼───────┐
 │ DRAW ORDER  │   │  COORDINATES  │ │  DRAWING   │  │  ANIMATION  │  │   PRESENTATION │
 │             │   │  & TRANSFORMS │ │            │  │             │  │                │
 ├─────────────┤   ├───────────────┤ ├────────────┤  ├─────────────┤  ├────────────────┤
 │ tree order  │   │ local/global  │ │ _draw()    │  │ Tween       │  │ Theme          │
 │ z_index     │   │ Transform2D   │ │ draw_line  │  │  tweeners   │  │  StyleBoxFlat  │
 │ z_as_relative│  │ canvas xform  │ │ draw_rect  │  │  ease/trans │  │  StyleBoxTex.  │
 │ y_sort      │   │ viewport vs   │ │ draw_circle│  │  chain/     │  │  type variation│
 │ CanvasLayer │   │   canvas      │ │ draw_string│  │   parallel  │  │  font hinting  │
 │ show_behind │   │ mouse pos     │ │ queue_     │  │  kill()     │  │ DPI scaling    │
 │  _parent    │   │  (global vs   │ │  redraw()  │  │  vs Anim-   │  │                │
 └──────┬──────┘   │   local)      │ └─────┬──────┘  │  ationPlayer│  └────────┬───────┘
        │          └───────┬───────┘       │         └──────┬──────┘           │
        │                  │               │                │                  │
 ┌──────▼──────────────────▼───────────────▼────────────────▼──────────────────▼──────┐
 │                              VIEWPORT & COMPOSITION                                │
 ├────────────────────────────────────────────────────────────────────────────────────┤
 │ SubViewport · ViewportTexture · stretch modes · CanvasItemMaterial (blend/light)   │
 │ modulate/self_modulate · Parallax2D · PointLight2D/LightOccluder2D · CanvasModulate │
 │ WorldEnvironment (2D glow, HDR 2D)                                                 │
 └────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                              ┌────────────▼─────────────┐
                              │  CASE STUDY: RELAX ROOM  │
                              │  1280×720 · canvas_items │
                              │  z-layer conventions     │
                              │  tween & theme patterns  │
                              └──────────────────────────┘
```

## Table of contents

1. [Overview: how Godot draws a 2D frame](#overview-how-godot-draws-a-2d-frame)
2. [CanvasItem: the base of all 2D rendering](#canvasitem-the-base-of-all-2d-rendering)
3. [Draw order I: tree order and z_index](#draw-order-i-tree-order-and-z_index)
4. [Draw order II: Y-sort, CanvasLayer and show_behind_parent](#draw-order-ii-y-sort-canvaslayer-and-show_behind_parent)
5. [2D transforms and coordinate systems](#2d-transforms-and-coordinate-systems)
6. [Custom drawing with _draw()](#custom-drawing-with-_draw)
7. [Custom drawing: performance and patterns](#custom-drawing-performance-and-patterns)
8. [Viewports and SubViewport](#viewports-and-subviewport)
9. [Resolution independence for desktop apps](#resolution-independence-for-desktop-apps)
10. [CanvasItemMaterial: blend and light modes](#canvasitemmaterial-blend-and-light-modes)
11. [Modulate patterns](#modulate-patterns)
12. [Tween deep dive I: lifecycle and tweeners](#tween-deep-dive-i-lifecycle-and-tweeners)
13. [Tween deep dive II: sequencing, easing and control](#tween-deep-dive-ii-sequencing-easing-and-control)
14. [Tween discipline: kill(), cleanup and Tween vs AnimationPlayer](#tween-discipline-kill-cleanup-and-tween-vs-animationplayer)
15. [Parallax: Parallax2D and the legacy nodes](#parallax-parallax2d-and-the-legacy-nodes)
16. [2D lighting overview](#2d-lighting-overview)
17. [UI theming: Theme, StyleBox and fonts](#ui-theming-theme-stylebox-and-fonts)
18. [Environment and post-processing in 2D](#environment-and-post-processing-in-2d)
19. [Case study: Relax Room rendering conventions](#case-study-relax-room-rendering-conventions)
20. [Best practices](#best-practices)
21. [Common errors & troubleshooting](#common-errors--troubleshooting)
22. [Exercises](#exercises)
23. [Further reading](#further-reading)
24. [Glossary](#glossary)

---

## Overview: how Godot draws a 2D frame

Every visible pixel of a Godot 2D application is the end product of a surprisingly small set of concepts. Before diving into each one, it pays to see the whole pipeline once, end to end, because almost every rendering bug you will ever debug is a misunderstanding of *one stage* of this pipeline.

When Godot renders a frame in 2D, conceptually this happens:

1. **The scene tree is traversed depth-first.** Every node that inherits from `CanvasItem` (that is: every `Node2D` and every `Control`) emits *draw commands* — "draw this texture here", "draw this rect there". A `Sprite2D` emits a textured quad; a `Label` emits glyph quads; your own `_draw()` override emits whatever you tell it to.
2. **Each item's commands are transformed** by the item's global transform (its position/rotation/scale accumulated from its ancestors), then by the canvas transform (the camera), then by the stretch transform (window scaling). This chain is what makes "the same scene" work in a maximized window, a small window and a different aspect ratio.
3. **Items are sorted** into their final order: first by `CanvasLayer`, then by effective `z_index`, then — where enabled — by Y position (`y_sort_enabled`), and finally by tree order as a tiebreaker.
4. **The sorted commands are rasterized** by the `RenderingServer` into the viewport's render target, applying per-item material (blend mode, shader), `modulate` color, and any 2D lights that touch the item.
5. **The viewport's texture is presented** to the window (or, for a `SubViewport`, kept as a texture for you to sample).

Two mental models follow from this and will save you hours:

- **Nothing draws "immediately".** Your script code never paints pixels; it *describes* what should be painted. That is why `_draw()` results are cached, why changing a property mid-frame never produces half-updated visuals, and why the `RenderingServer` can batch thousands of items efficiently.
- **Order is decided globally, not locally.** A child being "inside" a node does not trap it visually under a sibling subtree. `z_index` and `CanvasLayer` can lift any item above (or sink it below) anything else in the same viewport. When you *want* containment semantics, you have to build them deliberately (see `clip_children` and the decision table in section 4).

### Where each module concept lives in the pipeline

| Pipeline stage | Concepts in this module |
|---|---|
| Command emission | `_draw()`, `draw_*` methods, `queue_redraw()` |
| Transformation | `Transform2D`, local vs global, canvas vs viewport coordinates |
| Sorting | tree order, `z_index`, `z_as_relative`, `y_sort_enabled`, `CanvasLayer`, `show_behind_parent` |
| Rasterization | `CanvasItemMaterial` blend/light modes, `modulate`, 2D lights, `CanvasModulate` |
| Presentation | `Viewport`, `SubViewport`, `ViewportTexture`, stretch modes, `WorldEnvironment` glow |
| Change over time | `Tween` (this module), `AnimationPlayer` (decision criteria here, details in the animation notes of [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md)) |

> ✅ **Best practice** — When you hit a visual ordering bug, resist the urge to sprinkle `z_index = 999`. Instead, name the pipeline stage: is this a *layer* problem (CanvasLayer), a *priority* problem (z_index), a *world-depth* problem (Y-sort), or a *tree order* problem (move_child)? Each has exactly one correct tool.

### Under the hood: the RenderingServer and batching

Nodes are a convenience layer. The actual renderer is the **`RenderingServer`** singleton: every `CanvasItem` owns a server-side item (exposed via `get_canvas_item()`, an RID), and node properties are just setters that forward to it. Two production-relevant consequences:

**Batching.** The 2D renderer merges consecutive draw commands that share state (same texture, same material, same blend mode) into single GPU draw calls. What *breaks* a batch: switching textures, switching materials, and interleaving item types. This is the performance rationale behind advice you'll meet across modules:

- **Texture atlases** ([SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md)) keep many sprites on one texture → one batch instead of dozens.
- **Shared material resources** (section 10) instead of per-node duplicates.
- Draw-order interleaving matters: 100 icons then 100 labels batches far better than icon-label-icon-label — occasionally worth restructuring a heavy list for.

**Direct server drawing.** For extreme cases (thousands of static items), you can bypass nodes entirely and feed the server canvas items yourself:

```gdscript
var rid := RenderingServer.canvas_item_create()
RenderingServer.canvas_item_set_parent(rid, get_canvas_item())
RenderingServer.canvas_item_add_texture_rect(rid, Rect2(0, 0, 32, 32), tex.get_rid())
# No node, no per-node overhead — but also no transforms, signals or lifecycle.
```

You will rarely need this — `MultiMeshInstance2D` and well-batched nodes cover almost everything — but knowing the node layer is *optional* demystifies the pipeline: everything in this module ultimately compiles down to server commands like these.

This module is deliberately 2D-only. Godot's 3D pipeline shares the servers architecture but uses a completely different sorting and material model. For the shader side of the 2D pipeline (what happens *inside* the rasterization stage), continue to [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md).

---

## CanvasItem: the base of all 2D rendering

Everything visible in 2D — `Sprite2D`, `AnimatedSprite2D`, `TileMapLayer`, `Line2D`, `Control`, `Label`, `Button`, `ColorRect`, `Polygon2D` — inherits from **`CanvasItem`**. `CanvasItem` is abstract: you never instance it directly, but its properties are the shared vocabulary of the whole 2D engine. Learn this class once and you have learned half of 2D rendering.

### The two families: Node2D and Control

`CanvasItem` has exactly two concrete branches:

| Branch | Positioning model | Typical use |
|---|---|---|
| `Node2D` | Free transform: `position`, `rotation`, `scale`, `skew` | Game world: sprites, characters, effects, tilemaps |
| `Control` | Anchor/offset layout, sized rectangles, containers | UI: buttons, panels, labels, HUD |

Both draw through the same pipeline and share every property below. The difference is *who decides where they are*: a `Node2D` goes where you put it; a `Control` inside a container goes where the layout system puts it. Mixing them is legal (a `Control` under a `Node2D` and vice versa) but layout stops at the boundary — a `Sprite2D` inside a `VBoxContainer` will not be arranged by it.

### Core properties

| Property | Type | Effect |
|---|---|---|
| `visible` | `bool` | Shows/hides the item **and its entire subtree**. Hidden items emit no draw commands and cost nothing to render. |
| `modulate` | `Color` | Color multiplier applied to this item **and all children** (cascades). |
| `self_modulate` | `Color` | Color multiplier applied **only to this item**, not children. |
| `z_index` | `int` | Draw priority, −4096 to 4096. Section 3. |
| `z_as_relative` | `bool` | If `true` (default), `z_index` adds to the parent's effective Z. |
| `y_sort_enabled` | `bool` | Sorts **children** by global Y position. Section 4. |
| `show_behind_parent` | `bool` | Draws this item just below its direct parent. Section 4. |
| `top_level` | `bool` | Ignores the parent's *transform* (not its draw order): the item positions itself in canvas space. |
| `clip_children` | `ClipChildrenMode` | Uses this item as a mask for its children (`CLIP_CHILDREN_ONLY`, `CLIP_CHILDREN_AND_DRAW`). |
| `light_mask` | `int` (bitmask) | Which 2D lights affect this item. Section 16. |
| `visibility_layer` | `int` (bitmask) | Which viewports render this item (matched against `Viewport.canvas_cull_mask`). |
| `material` | `Material` | `CanvasItemMaterial` or `ShaderMaterial`. Section 10. |
| `use_parent_material` | `bool` | Inherit the parent's material — handy for effect subtrees. |
| `texture_filter` | `TextureFilter` | Per-item override of nearest/linear filtering (pixel art vs smooth). |
| `texture_repeat` | `TextureRepeat` | Per-item override of texture tiling behavior. |

Three of these deserve immediate attention because they are the source of the most common early confusions.

### visible vs modulate.a = 0

Both make a node disappear, but they are not interchangeable:

```gdscript
# Fully removes the subtree from rendering AND stops _draw() being called.
sprite.visible = false

# Renders the subtree at alpha 0: still traversed, still "there",
# still receives _process and input as usual. Cost is near-zero for
# the GPU (transparent), but the pipeline still walks it.
sprite.modulate.a = 0.0
```

Use `visible` for on/off state; use `modulate.a` only as the *animated* path of a fade — and flip `visible` at the ends of the fade if the subtree is large:

```gdscript
func fade_out(target: CanvasItem, duration := 0.3) -> void:
    var tween := create_tween()
    tween.tween_property(target, "modulate:a", 0.0, duration)
    tween.tween_callback(target.hide)  # visible = false at the end

func fade_in(target: CanvasItem, duration := 0.3) -> void:
    target.modulate.a = 0.0
    target.show()                      # visible = true before animating
    var tween := create_tween()
    tween.tween_property(target, "modulate:a", 1.0, duration)
```

> ⚠️ **Pitfall** — `visible = false` on a `Control` does **not** free its layout slot in most containers; the container skips hidden children when arranging (for `BoxContainer` and friends), but a manually-anchored Control simply stops drawing. If a "gap" appears or disappears unexpectedly when hiding UI, check which container is doing your layout.

### modulate vs self_modulate

`modulate` cascades multiplicatively down the tree; `self_modulate` does not cascade at all:

```gdscript
# Tint the node AND everything under it red at half alpha:
root_item.modulate = Color(1, 0, 0, 0.5)

# Tint ONLY this node; its children keep their own colors:
root_item.self_modulate = Color(1, 0, 0, 0.5)
```

Because the cascade *multiplies*, alphas stack:

```
parent.modulate.a = 0.5
child.modulate.a  = 0.5
→ the child renders at 0.5 × 0.5 = 0.25 effective alpha
```

This multiplication is a feature: a panel fading out takes its buttons and labels with it, proportionally, with no extra code. It becomes a bug only when you *forget* an ancestor is already tinted — if a sprite refuses to reach full opacity, walk up the tree looking for a stray `modulate`.

A classic production use of `self_modulate` is flashing a container's background without dimming its contents:

```gdscript
# Flash the panel red on invalid input, leaving child text readable.
func flash_error(panel: Panel) -> void:
    var tween := create_tween()
    tween.tween_property(panel, "self_modulate", Color(1.0, 0.55, 0.55), 0.08)
    tween.tween_property(panel, "self_modulate", Color.WHITE, 0.25)
```

> ⚠️ **Pitfall** — Semi-transparent `modulate` on a parent with *overlapping* children reveals the overlaps: each child is blended individually, so two stacked 50%-alpha sprites show a darker seam where they intersect. When a subtree must fade as *one flattened image*, parent it under a **`CanvasGroup`** node, which renders children into an intermediate buffer first, then applies transparency to the composite.

### top_level: escaping the parent transform

`top_level = true` detaches the item from its parent's *transform chain* while keeping it in the tree (signals, lifetime, groups all unchanged). Its `position` becomes canvas-space. This is the standard tool for:

- **Drop shadows / decals** that must not rotate with a spinning parent.
- **Health bars** parented to an enemy for lifetime, but positioned in world space so they don't inherit the enemy's squash-and-stretch scale.
- **Trail effects** whose emitted points must stay where they were emitted.

```gdscript
extends Node2D  # a floating damage number, child of the enemy that spawned it

func _ready() -> void:
    top_level = true                       # stop inheriting enemy movement
    global_position = get_parent().global_position + Vector2(0, -24)
    var tween := create_tween()
    tween.set_parallel(true)
    tween.tween_property(self, "position:y", position.y - 32.0, 0.6)
    tween.tween_property(self, "modulate:a", 0.0, 0.6).set_delay(0.2)
    tween.chain().tween_callback(queue_free)
```

> ✅ **Best practice** — Reach for `top_level` before you reach for "reparent the node at runtime". Reparenting mid-frame invalidates node paths, may fire `_exit_tree`/`_enter_tree`, and interacts badly with tweens bound to the node. `top_level` gives you the visual independence with none of the lifecycle churn.

### clip_children: masking a subtree

`clip_children` turns the item's own drawing into a **mask** for its children — the 2D equivalent of "clip to parent shape":

| Mode | Effect |
|---|---|
| `CLIP_CHILDREN_DISABLED` | Default: children draw freely. |
| `CLIP_CHILDREN_ONLY` | The parent's pixels become a pure mask: children show only where the parent has opaque pixels; the parent itself is not drawn. |
| `CLIP_CHILDREN_AND_DRAW` | The parent draws normally *and* masks its children. |

```gdscript
# A circular avatar: a circle sprite masking a photo.
avatar_circle.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
avatar_circle.add_child(photo_sprite)   # photo shows only inside the circle
```

Classic uses: progress-bar fills revealed by a shaped mask, portrait frames, "wipe" transitions (animate the mask's scale), minimap circles. The mask is *alpha-based* — any texture or `_draw()` output works as the stencil.

> ⚠️ **Pitfall** — `clip_children` clips **rendering only**: a masked-away Button still occupies its layout rect and still receives mouse input. For input-correct scissoring of scrollable UI, use `Control.clip_contents` (rect-based) or a real `ScrollContainer` instead.

### Visibility signals and lifecycle

Two notifications complete the visibility toolkit:

```gdscript
# Fires when THIS item's effective visibility changes (own flag or an ancestor's):
sprite.visibility_changed.connect(_on_visibility_changed)

func _on_visibility_changed() -> void:
    if sprite.is_visible_in_tree():      # true only if ALL ancestors are visible
        _resume_expensive_updates()
    else:
        _pause_expensive_updates()
```

`visible` tells you the node's own flag; **`is_visible_in_tree()`** answers the question that matters — "will this actually render?". Gate per-frame work (particle emission, `queue_redraw()` loops, animation advancement) on it: a desktop companion minimized to the tray should drop its canvas work to zero. (The processing side of that discipline — `process_mode`, minimized-window throttling — is covered in [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md).)

### Per-item texture filtering

Filtering usually comes from the project default (`rendering/textures/canvas_textures/default_texture_filter`), but any `CanvasItem` can override it — the override cascades to children unless they override again:

```gdscript
# Crisp pixel-art sprite in an otherwise smooth (linear-filtered) UI:
pixel_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
```

This matters for mixed-art projects (a pixel-art scene with smooth vector UI, or vice versa). The Relax Room project ships with the *project default* set to Nearest because nearly everything is pixel art — see section 19.

Cross-reference: texture import settings, mipmaps and atlases are covered in [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md); this module only deals with what happens after the texture reaches the canvas.

---

## Draw order I: tree order and z_index

Draw order in Godot 2D is decided by a **priority chain**. From strongest to weakest:

```
1. CanvasLayer  (which layer are you on?)               ← section 4
2. z_index      (effective Z within the layer)          ← this section
3. Y-sort       (if an ancestor enables it, Y position) ← section 4
4. Tree order   (depth-first scene traversal)           ← this section
```

A stronger rule always wins; weaker rules only break ties. We start at the bottom of the chain because tree order is the default everything else modifies.

### Tree order: the default painter's algorithm

With no `z_index`, no Y-sort and no `CanvasLayer`, Godot draws nodes in **depth-first tree order**: a parent draws first (below), then each child *and its entire subtree*, top to bottom as listed in the Scene dock. Later siblings draw on top of earlier siblings.

```
Root
├── Background      ← drawn 1st (bottom)
├── Furniture       ← drawn 2nd
│   ├── Rug         ← drawn 3rd
│   └── Table       ← drawn 4th   (on top of Rug)
└── Character       ← drawn 5th (top: after Furniture AND its subtree)
```

Two immediate consequences:

- **Children always draw on top of their parent** (unless `show_behind_parent` or negative relative Z intervenes).
- **Reordering siblings reorders rendering.** `move_child(node, index)`, or dragging in the Scene dock, *is* a draw-order operation. For dynamic cases:

```gdscript
# Bring a window-like panel to the front among its siblings:
func bring_to_front(panel: Control) -> void:
    panel.get_parent().move_child(panel, -1)   # -1 = last = drawn on top
```

For simple UIs, tree order alone is a complete, robust z-management strategy — and it is self-documenting, because the Scene dock *is* the layer list, bottom-to-top.

> ✅ **Best practice** — Prefer tree order for static layering. Reserve `z_index` for cases where render order must *differ* from the logical tree structure. A scene where the tree reads top-to-bottom as back-to-front needs no comments to explain its rendering.

### z_index: explicit priority

`z_index` (int, clamped to **−4096 … 4096**, the `RenderingServer.CANVAS_ITEM_Z_MIN/MAX` limits) overrides tree order *within a canvas layer*. Higher draws on top. Equal `z_index` falls back to tree order.

```gdscript
background.z_index = -1   # behind everything at Z 0
player.z_index      = 0   # default
tooltip.z_index     = 50  # above world items
auth_screen.z_index = 100 # above all gameplay visuals (Relax Room convention)
```

The crucial subtlety: **z_index is not scoped to the parent**. Every item in the same canvas layer competes in one global Z ordering. A `z_index = 1` node deep inside a "background" subtree will draw above a `z_index = 0` node in a "foreground" subtree. Z is a *global escalator*, not a local nudge — the only containment mechanisms are `CanvasLayer` (hard separation) and `clip_children` (masking).

### z_as_relative: additive Z chains

By default `z_as_relative = true`: an item's *effective* Z is its own `z_index` **plus the parent's effective Z**.

```
Room        (z_index = 5)
└── Table   (z_index = 2, z_as_relative = true)   → effective Z = 7
    └── Vase (z_index = 1, z_as_relative = true)  → effective Z = 8
```

With `z_as_relative = false` the item's `z_index` is absolute — effective Z is exactly the number you set, regardless of ancestors:

```
Room        (z_index = 5)
└── Overlay (z_index = 2, z_as_relative = false)  → effective Z = 2 (draws BELOW Room content at 5)
```

Relative Z (the default) is almost always what you want: it lets you design a subtree's internal layering ("vase is 1 above the table") and then move the whole subtree up or down the stack by changing only the root's Z. Absolute Z is for pinning: "this vignette overlay is always at Z 4000, whatever it's parented to".

```gdscript
# A reusable "selected item" highlight that must render just above
# whatever piece of furniture it decorates:
highlight.z_as_relative = true
highlight.z_index = 1        # parent's Z + 1, wherever it is mounted
```

> ⚠️ **Pitfall** — A *negative* relative `z_index` on a child (e.g. `-1`) sinks it below the parent — and below anything else at the parent's Z. If you only want "behind my parent, but still above the parent's background siblings", use `show_behind_parent` instead (section 4), which slots the child *immediately* below the parent without changing its Z bracket.

> ⚠️ **Pitfall** — Do not use giant Z values as a "definitely on top" hammer (`z_index = 4096` everywhere). Z is clamped, collisions between subsystems become inevitable, and debugging requires a project-wide search. Define a small set of named constants (see the Relax Room conventions in section 19) and treat any literal Z in code as a review flag.

### Where z_index applies — and where it doesn't

`z_index` exists on all `CanvasItem`s, including `Control`s, and it does affect Control rendering. But **it does not affect Control input**: GUI mouse handling walks the Control tree, not the Z order. A Control drawn on top via `z_index` may still let clicks fall through to a sibling that is "visually below" it. For UI, layering with tree order (or separate `CanvasLayer`s) keeps drawing and input consistent — treat `z_index` on Controls as a decoration-only tool.

| You want | Use |
|---|---|
| Sprite drawn behind its parent's other children | negative relative `z_index` |
| Sprite drawn immediately behind its parent only | `show_behind_parent` |
| Subtree movable up/down the stack as a unit | `z_index` on the subtree root, children relative |
| An always-on-top world-space marker | absolute Z (`z_as_relative = false`) with a documented constant |
| UI panel above other UI, receiving input correctly | tree order (`move_child`) or a higher `CanvasLayer` |

### Dynamic Z in practice: lift-while-dragging

The most common runtime Z manipulation in 2D apps is the *lift*: while the user drags an object, it must render above everything it could be dropped onto, then settle back into normal ordering on release. The pattern, as used for Relax Room's furniture dragging:

```gdscript
const Z_DRAGGING := 50        # documented in the project layer plan (section 19)

var _original_z := 0

func _start_drag() -> void:
    _original_z = z_index
    z_index = Z_DRAGGING              # above the Y-sorted furniture plane

func _end_drag() -> void:
    z_index = _original_z             # rejoin normal depth competition
```

Three details make this production-grade rather than hacky:

1. **The lift value is a named constant** from the project's layer table, chosen *below* system strata (auth screen at 100) so a drag can never cover critical UI.
2. **The original Z is saved and restored**, not assumed to be zero — the object may legitimately carry a non-default Z (a wall-mounted shelf at +1).
3. **The lift is Z, not CanvasLayer.** The dragged item must still be affected by the camera (it lives in the world); moving it to a CanvasLayer would freeze it on screen while the world scrolls beneath.

The same save-lift-restore shape serves selection highlights, "bring window to front" (via `move_child` instead of Z), and pieces animating between board slots.

---

## Draw order II: Y-sort, CanvasLayer and show_behind_parent

### Y-sort: depth from vertical position

In top-down and isometric games, "in front of" means "lower on the screen": a character standing *below* a table (larger Y) should draw *over* it; standing behind (smaller Y) should draw *under* it. Hand-managing that with `z_index` is hopeless — the order changes every frame as things move. **Y-sort** automates it.

In Godot 4, Y-sort is a `CanvasItem` property: **`y_sort_enabled`**. Setting it on a node sorts that node's **children** by their **global Y position** (of their origin) — smaller Y drawn first (further away), larger Y drawn last (nearer).

```gdscript
# One parent gathers everything that competes for depth:
# World (Node2D, y_sort_enabled = true)
# ├── Character   (origin at the feet!)
# ├── Table
# ├── Plant
# └── Pet

world.y_sort_enabled = true
```

Three rules govern real-world use:

1. **Only siblings under a Y-sorted parent are sorted against each other.** Objects that must interleave (player weaving between furniture) must share a Y-sorted ancestor.
2. **Sorting uses the node's origin.** Art must be authored (or offset) so the origin sits at the *contact point with the ground* — a character's feet, a table's legs. An origin at the sprite's center makes tall objects pop in front too early. In practice: `Sprite2D.centered = false` plus an offset, or wrap the sprite in a parent `Node2D` placed at the feet.
3. **Y-sort nests.** If a Y-sorted parent has a child with `y_sort_enabled` also on, that child's children join the *same* sorting space as the parent's other children — the hierarchy is "flattened" for sorting purposes. This is exactly what `TileMapLayer` relies on: enable `y_sort_enabled` on both the layer and the world parent, and tiles interleave with characters. (Details and `y_sort_origin` tuning in [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md); full isometric workflow in [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md).)

Y-sort combines with Z: items are first bucketed by effective `z_index`, and Y-sort orders items *within the same Z bucket*. So a flying character can get `z_index = 1` to hover above the entire Y-sorted furniture plane, then return to Z 0 on landing.

```gdscript
# Relax Room-style: pet jumps onto the sofa — while airborne it must not
# interleave with floor furniture.
func _on_jump_started() -> void:
    pet.z_index = 1          # above the Y-sorted plane

func _on_jump_landed() -> void:
    pet.z_index = 0          # back into normal depth competition
```

> ⚠️ **Pitfall** — "Y-sort doesn't work" is almost always one of: (a) the movers don't share a Y-sorted ancestor; (b) origins are at sprite centers, not feet; (c) one item carries a stray non-zero `z_index`, moving it into a different Z bucket where Y-sort can't reach it. Check those three before anything else.

> ✅ **Best practice** — Keep the Y-sorted world *flat-ish*: one Y-sort parent, direct children per depth-competing entity. Deep decorative hierarchies inside each entity are fine (they don't compete), but avoid multiple unrelated Y-sort roots for entities that must interleave.

### CanvasLayer: hard separation from the world

`CanvasLayer` is **not** a `CanvasItem` — it is a rendering *bracket*. Every CanvasItem in the tree belongs to some canvas layer: by default the implicit **layer 0** (the "world" canvas), or the nearest `CanvasLayer` ancestor. Layers render strictly in `layer` order (lower first), and **no `z_index` can cross a layer boundary**: `layer = 1` content always draws above *all* `layer = 0` content, even `z_index = 4096`.

The second superpower: a `CanvasLayer` has its **own transform**, independent of the camera. Content inside it does not scroll when `Camera2D` moves. That makes it the canonical home for:

| Layer content | Typical `layer` value |
|---|---|
| Full-screen background behind the world | negative (e.g. `-1`) |
| Game world (implicit canvas) | 0 |
| HUD, panels, menus | 1 … 10 |
| Popups, tooltips, toasts | ~100 |
| Screen-fade / loading overlay | above everything used by gameplay |

```gdscript
# HUD that ignores the camera entirely:
var hud_layer := CanvasLayer.new()
hud_layer.layer = 10
add_child(hud_layer)
hud_layer.add_child(hud_scene.instantiate())
```

Useful properties beyond `layer`:

| Property | Purpose |
|---|---|
| `visible` | Hide the whole layer (4.x; handy for toggling entire UI stacks). |
| `offset`, `rotation`, `scale`, `transform` | The layer's own transform (e.g. screen-shake *only* the world by shaking layer 0's camera, or shake UI by animating `offset`). |
| `follow_viewport_enabled` | Makes the layer follow the canvas transform again — with `follow_viewport_scale` it can fake cheap parallax depth. |
| `custom_viewport` | Render the layer against a different `Viewport`'s transform. |

The `follow_viewport` pair deserves one concrete example, because it is the cheapest parallax in the engine — a *background* layer that scrolls at 40 % of camera speed with zero scripting:

```gdscript
var bg_layer := CanvasLayer.new()
bg_layer.layer = -1                       # behind the world
bg_layer.follow_viewport_enabled = true   # move with the camera again...
bg_layer.follow_viewport_scale = 0.4      # ...but only 40% as fast
add_child(bg_layer)
bg_layer.add_child(distant_hills_sprite)
```

For anything beyond a single backdrop plane, use the real parallax nodes (section 15) — but for one distant layer this is unbeatable.

> ⚠️ **Pitfall** — `CanvasLayer` is not a `CanvasItem`: it has **no `modulate`**, and an ancestor's `modulate` does **not** cascade into it. You cannot fade a whole layer by tinting its parent. Fade a full-screen `ColorRect` on top instead, or put the layer's content under a single root Control and tween *that* root's modulate.

> ⚠️ **Pitfall** — A `Control` inside a `CanvasLayer` still receives input normally, but a `Control` in the *world* canvas under a camera transform receives input in *transformed* coordinates. If clicks land "offset" from buttons, check whether UI accidentally lives in the world canvas while the camera is zoomed — moving it into a `CanvasLayer` is usually the fix.

### show_behind_parent: the precision tool

`show_behind_parent = true` draws an item **immediately below its direct parent** — same Z bracket, same layer, no arithmetic. It is the exact tool for attachments that must sit behind their owner but in front of everything the owner is in front of:

```gdscript
# A shadow blob under a character: behind the body, but still above the floor.
shadow_sprite.show_behind_parent = true
```

Compare with the alternatives: a negative relative `z_index` sinks the child below the parent's *entire Z bracket* (it may fall behind the floor too); reordering the tree would require the shadow to be a *sibling*, complicating the prefab. `show_behind_parent` keeps the prefab self-contained.

### The draw-order decision table

The complete resolution algorithm, highest priority first, for two items A and B in the same `Viewport`:

| # | Question | If different | If equal |
|---|---|---|---|
| 1 | Which `CanvasLayer` (`layer` value)? | Higher `layer` draws on top — **unconditionally** | ↓ |
| 2 | Effective `z_index` (own + relative ancestors)? | Higher Z draws on top | ↓ |
| 3 | Under a common Y-sorted parent? | Larger global Y draws on top | ↓ |
| 4 | `show_behind_parent` involved? | Item slots just below its parent | ↓ |
| 5 | Tree order (depth-first) | Later in traversal draws on top | — |

And the tool-selection table — start from what you need, pick the *weakest* mechanism that does it:

| Need | Reach for | Not |
|---|---|---|
| Static back-to-front scene layering | Tree order (Scene dock order) | z_index everywhere |
| Dynamic depth for moving top-down/iso entities | `y_sort_enabled` on a shared parent | per-frame z_index scripts |
| One item lifted above/sunk below its world peers | `z_index` (relative) | CanvasLayer |
| Attachment rendered right behind its owner | `show_behind_parent` | z_index = −1 |
| UI immune to camera; strict stacking of UI strata | `CanvasLayer` with documented `layer` constants | z_index = 4096 |
| Children visually confined to parent's silhouette | `clip_children` (mask) | manual cropping |
| Whole-subtree fade without overlap seams | `CanvasGroup` | per-child alpha juggling |

> ✅ **Best practice** — In production projects, write the layer plan down. Relax Room's plan (section 19) fits in a 6-row table — world at layer 0 with Y-sorted furniture, UI at 10, popups at 100 — and every rendering decision in the codebase traces back to it.

### Debugging draw order

When the decision table and your scene disagree, debug systematically instead of poking values:

1. **Inspect the *running* scene, not the editor scene.** Editor → Remote tab while the game runs: runtime-created CanvasLayers (like Relax Room's popup layer) and script-modified `z_index` values only exist there.
2. **Binary-search with `visible`.** Toggle subtrees off in the Remote tree until the offending pair is isolated; ordering bugs between *two* known items are trivial, bugs in a 200-node scene are not.
3. **Interrogate the numbers.** A temporary hotkey that dumps the contested items tells you which rule is in play:

```gdscript
func _dump_order_info(item: CanvasItem) -> void:
    print("%s  layer=%s  z=%d  rel=%s  ysort_parent=%s  tree_idx=%d" % [
        item.name,
        _nearest_canvas_layer(item),          # walk ancestors for a CanvasLayer
        item.z_index,
        item.z_as_relative,
        item.get_parent() is CanvasItem and (item.get_parent() as CanvasItem).y_sort_enabled,
        item.get_index(),
    ])

func _nearest_canvas_layer(item: Node) -> String:
    var n := item.get_parent()
    while n:
        if n is CanvasLayer:
            return "%s(%d)" % [n.name, (n as CanvasLayer).layer]
        n = n.get_parent()
    return "root(0)"
```

4. **Check the camera last.** If ordering looks right but *positions* look wrong (items "swallowed" by backgrounds at some zooms), the bug is usually section 5's territory — a coordinate-space mixup, not draw order.

The editor's **CanvasItem debugger** (Debugger → Misc tab, "clicked Control" info) and turning on **Visible Collision Shapes / Navigation** for spatial context complete the toolbox.

---

## 2D transforms and coordinate systems

Rendering puts things *somewhere*; this section is about what "somewhere" means. Godot 2D has a small stack of coordinate spaces, and every positioning bug — popups drifting off their anchor, clicks landing beside buttons, drag-and-drop offsets — is a confusion between two of them.

### The spaces

| Space | Origin | Units | You meet it in |
|---|---|---|---|
| **Local** | The node's own origin | pixels (pre-transform) | `position`, `_draw()` coordinates, `get_local_mouse_position()` |
| **Canvas (world)** | The canvas origin | world pixels | `global_position`, `get_global_mouse_position()`, physics |
| **Viewport** | Top-left of the viewport | viewport pixels | `Viewport.get_mouse_position()`, `get_global_transform_with_canvas()` |
| **Screen** | Top-left of the OS screen | physical pixels | `DisplayServer` window APIs, multi-window desktop apps |

The chain that maps a local point all the way to the screen:

```
local point
  → CanvasItem global transform      (node + ancestors: get_global_transform())
  → canvas transform                 (the camera: Viewport.canvas_transform)
  → stretch transform                (window scaling from stretch settings)
  → window/screen transform          (final placement)
```

The official formula for "where is this local point on the viewport" is:

```gdscript
var viewport_pos: Vector2 = get_global_transform_with_canvas() * local_pos
```

and for physical screen coordinates:

```gdscript
var screen_pos: Vector2 = get_viewport().get_screen_transform() \
        * get_global_transform_with_canvas() * local_pos
```

You rarely type these chains by hand, because the helpers below cover the common cases — but knowing the chain tells you *which helper* you need.

### Transform2D essentials

A `Transform2D` is a 2×3 matrix: two basis vectors `x` and `y` (rotation & scale) plus an `origin` (translation). The API you actually use:

```gdscript
var t := Transform2D(rotation_angle, origin_vec)   # build from rotation + origin
var t2 := Transform2D.IDENTITY

# Composition: apply t_inner first, then t_outer (right-to-left, like matrices):
var combined := t_outer * t_inner

# Transform a point (full transform: rotation, scale AND translation):
var world_p: Vector2 = t * local_p

# Direction-only transform (rotation/scale, NO translation):
var world_dir: Vector2 = t.basis_xform(local_dir)

# Inverse mapping — world point back into t's local space:
var local_p2: Vector2 = t.affine_inverse() * world_p

# Immutable helpers (return modified copies):
var moved  := t.translated(Vector2(10, 0))
var turned := t.rotated(PI / 4)
var bigger := t.scaled(Vector2(2, 2))
```

`affine_inverse()` is the one to memorize: *every* "convert back" operation in 2D is "multiply by the affine inverse of the forward transform". Screen → world, world → local, canvas → layer: same trick.

> ⚠️ **Pitfall** — `Transform2D.basis_xform()` vs full multiplication: transforming a *velocity* or *offset* with the full transform (`t * v`) wrongly adds the translation. Points use `t * p`; directions use `t.basis_xform(v)` (or `t.basis_xform_inv(v)` for the reverse).

Reading a transform back into human terms:

```gdscript
var t := node.global_transform
var rot: float = t.get_rotation()          # radians
var scl: Vector2 = t.get_scale()
var skew: float = t.get_skew()
var pos: Vector2 = t.origin

# Rebuild from components (the constructor order matters):
var rebuilt := Transform2D(rot, scl, skew, pos)

# Interpolate whole transforms (position+rotation+scale in one blend):
var blended := from_t.interpolate_with(to_t, 0.25)

# Orthonormalized copy: scale/skew stripped, pure rotation+translation —
# use before comparing rotations or when accumulated float error skews a matrix:
var clean := t.orthonormalized()
```

`interpolate_with()` is the transform-level cousin of tweening (section 12): it blends rotation *angularly* (through the shortest arc) rather than lerping matrix cells, which is what you want for smoothly parking an object into a slot's full transform.

### Node-level helpers: to_local, to_global

`Node2D` and `Control` expose the transform chain as friendly methods:

```gdscript
# Where is this world point, expressed in my local space?
var local_target := to_local(enemy.global_position)

# Where is my local offset (e.g. muzzle at (12, -3)) in world space?
var muzzle_world := to_global(Vector2(12, -3))
```

`to_global(p)` is exactly `global_transform * p`; `to_local(p)` is `global_transform.affine_inverse() * p`. Prefer them over manual matrix math for readability. Also remember `global_position`, `global_rotation`, `global_scale` — direct global accessors that skip manual composition.

### Viewport vs canvas coordinates — and the two mouse positions

The **canvas transform** (`Viewport.canvas_transform`) is the camera: `Camera2D` continuously writes it (offset, zoom, smoothing). Because of it, *the same world point lands on different viewport pixels as the camera moves* — which is why there are two mouse-position APIs and they are **not** interchangeable:

```gdscript
# WORLD-space mouse — where the cursor points inside the game world.
# Use for: aiming, placing furniture, drag-and-drop of world objects.
var world_mouse: Vector2 = get_global_mouse_position()      # CanvasItem method

# LOCAL-space mouse — world mouse expressed in this node's local space.
# Use for: "is the cursor inside my shape", custom _draw() hit tests.
var local_mouse: Vector2 = get_local_mouse_position()       # CanvasItem method

# VIEWPORT-space mouse — raw position on the viewport rectangle.
# Use for: UI positioned in a CanvasLayer, screen-anchored effects.
var vp_mouse: Vector2 = get_viewport().get_mouse_position() # Viewport method
```

With no camera and no stretch, world and viewport coincide — which is precisely why bugs of this class survive until the day you add a `Camera2D` with zoom. Choose by *consumer*: world logic consumes `get_global_mouse_position()`; CanvasLayer UI consumes the viewport position.

Manual conversions, when helpers don't fit:

```gdscript
# world → viewport (e.g. anchor a CanvasLayer popup over a world object):
var canvas_xform := get_canvas_transform()          # CanvasItem helper
var vp_point: Vector2 = canvas_xform * world_point

# viewport → world (e.g. spawn under a UI cursor):
var world_point2: Vector2 = canvas_xform.affine_inverse() * vp_point
```

This is exactly the pattern Relax Room uses to place decoration popups (a `CanvasLayer` at layer 100) above furniture that lives in the camera-transformed world — see section 19.

```gdscript
# Continuous anchoring: keep a CanvasLayer label glued to a moving world node.
func _process(_delta: float) -> void:
    var vp_pos := world_target.get_global_transform_with_canvas().origin
    floating_label.position = vp_pos + Vector2(0, -36)
```

`get_global_transform_with_canvas()` composes the node's global transform with the canvas transform in one call — the standard "where is this node on screen" one-liner.

### Screen space and multiple windows

Desktop apps (like a desktop companion) sometimes need true OS-screen coordinates — placing a borderless window near the tray, or spawning a secondary `Window`:

```gdscript
# Viewport → screen:
var screen_xform := get_viewport().get_screen_transform()
var on_screen: Vector2 = screen_xform * vp_point

# Window placement (physical pixels, DisplayServer space):
var win := get_window()
win.position = DisplayServer.screen_get_position(0) + Vector2i(100, 100)
```

Every `Window` is itself a `Viewport` in Godot 4 — the root of your scene tree is a `Window`. Multi-window UIs therefore reuse everything from section 8; the desktop-specific practices (always-on-top, per-monitor DPI) live in [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md).

> ⚠️ **Pitfall** — In `_input()`/`_gui_input()`, `InputEventMouse.position` is in *viewport* coordinates (already stretch-adjusted), while `InputEventMouseMotion.relative` is a raw delta unaffected by camera zoom. Dragging a world object by adding `event.relative` to `global_position` drifts under zoom: divide by the camera zoom (`event.relative / camera.zoom`) or recompute from `get_global_mouse_position()` each frame — the latter is drift-proof.

> ✅ **Best practice** — When a coordinate bug appears, print *both* interpretations once: `print(get_global_mouse_position(), " vs ", get_viewport().get_mouse_position())`. The pair instantly tells you whether you are off by the camera transform (values differ by offset/zoom) or by the stretch transform (values differ by a constant scale).

### Control-side helpers

`Control` nodes add rect-aware conveniences on top of the CanvasItem base — worth knowing so you don't recompute them:

```gdscript
var rect: Rect2 = panel.get_rect()          # position + size, in PARENT space
var grect: Rect2 = panel.get_global_rect()  # in canvas space
var spos: Vector2 = panel.get_screen_position()  # top-left in viewport coords
var inside: bool = panel.get_global_rect().has_point(get_global_mouse_position())
```

`get_screen_position()` is the Control shortcut for the `get_global_transform_with_canvas().origin` pattern — the standard way to spawn a popup aligned to a button:

```gdscript
func _on_options_pressed() -> void:
    popup_menu.position = Vector2i(options_btn.get_screen_position()
            + Vector2(0, options_btn.size.y))     # flush under the button
    popup_menu.popup()
```

### Worked example: robust drag-and-drop in world space

Everything from this section in one canonical implementation — the drag logic behind Relax Room's furniture placement. Note which space every value lives in:

```gdscript
extends Node2D   # a draggable world object

var _dragging := false
var _grab_offset := Vector2.ZERO      # LOCAL-ish: world offset from object origin to grab point

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
        if event.pressed and _mouse_over():
            _dragging = true
            # WORLD-space grab offset: keeps the object from snapping its
            # origin to the cursor on pickup.
            _grab_offset = global_position - get_global_mouse_position()
            get_viewport().set_input_as_handled()
        elif not event.pressed:
            _dragging = false

func _process(_delta: float) -> void:
    if _dragging:
        # Recompute from the WORLD mouse every frame: immune to camera zoom,
        # camera movement and window resize — no accumulated drift.
        global_position = get_global_mouse_position() + _grab_offset

func _mouse_over() -> bool:
    # LOCAL-space test against the sprite's rect:
    var tex_rect := Rect2(-$Sprite2D.texture.get_size() * 0.5,
            $Sprite2D.texture.get_size())
    return tex_rect.has_point(get_local_mouse_position())
```

The three space decisions are the whole lesson: grab offset in *world* space (survives camera motion), per-frame position from the *world* mouse (no `event.relative` accumulation — see the pitfall above), hit test in *local* space (survives the object's own scale/rotation). Change any one of the three spaces and a camera zoom will break the feature.

---

## Custom drawing with _draw()

Every `CanvasItem` can emit its own draw commands by overriding **`_draw()`**. This is Godot's retained-mode vector API: you describe lines, rects, circles, polygons, textures and text in *local coordinates*, the engine caches the command list, and the cache is replayed every frame until something invalidates it.

When is `_draw()` the right tool rather than sprites or Controls?

- **Debug overlays** — trajectories, collision outlines, pathfinding graphs, grid guides (Relax Room's placement grid, section 19).
- **Procedural visuals** — waveforms, charts, minimaps, radial timers, node-graph edges: anything whose geometry is computed, not authored.
- **Many simple shapes** — one node drawing 500 grid cells beats 500 `ColorRect` nodes by a wide margin in memory and per-node overhead.
- **Resolution-independent primitives** — vector shapes stay crisp under any zoom, where a scaled texture would blur.

When it is the wrong tool: static images (use `Sprite2D`/`TextureRect` — texture quads are the fast path), skinned UI (use Theme StyleBoxes, section 17), anything needing per-pixel effects (use shaders, [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md)).

### The lifecycle: draw once, cache, invalidate

```gdscript
extends Node2D

var points: PackedVector2Array = []

func _draw() -> void:
    # Called by the engine when the item must (re)build its command list:
    # on first entering the tree, on visibility changes, and after queue_redraw().
    if points.size() >= 2:
        draw_polyline(points, Color.CYAN, 2.0, true)   # antialiased

func add_point(p: Vector2) -> void:
    points.append(p)
    queue_redraw()          # data changed → request a fresh _draw()
```

The contract:

1. **`_draw()` is not called every frame.** The command list is cached and replayed. If your visuals depend on data, *you* must call **`queue_redraw()`** whenever that data changes.
2. **`queue_redraw()` is cheap and idempotent** — it only flags the item; multiple calls in one frame coalesce into one `_draw()` on the next frame. Call it freely from setters.
3. **All `draw_*` methods are only valid inside `_draw()`** (technically: during `NOTIFICATION_DRAW`). Calling them elsewhere is a runtime error.
4. Coordinates are **local** to the item: the item's transform, `modulate`, material and draw order all apply to the result exactly as they would to a sprite.

For genuinely continuous visuals (an oscilloscope, a clock), request a redraw every frame explicitly:

```gdscript
func _process(_delta: float) -> void:
    queue_redraw()    # acceptable: the flag is cheap; _draw() runs once per frame
```

> ⚠️ **Pitfall** — Mutating state *inside* `_draw()` (advancing an animation variable, appending points) is a design error even when it appears to work: `_draw()` runs at unpredictable times and never runs while invisible. Update state in `_process()`; render it in `_draw()`. The two callbacks form a tiny MVC: process = controller, draw = view.

### API tour: shapes

```gdscript
func _draw() -> void:
    # ---- Lines -------------------------------------------------------------
    draw_line(Vector2(0, 0), Vector2(120, 0), Color.WHITE, 2.0)
    draw_line(Vector2(0, 8), Vector2(120, 8), Color.WHITE, 2.0, true)  # antialiased
    draw_dashed_line(Vector2(0, 16), Vector2(120, 16), Color.GRAY, 1.0, 4.0)
    draw_polyline(PackedVector2Array([Vector2(0, 30), Vector2(40, 60), Vector2(80, 30)]),
            Color.CYAN, 2.0)
    var seg := PackedVector2Array([          # independent segments: pairs of points
        Vector2(0, 70), Vector2(20, 70),
        Vector2(30, 70), Vector2(50, 70),
    ])
    draw_multiline(seg, Color.DIM_GRAY, 1.0)

    # ---- Rectangles ---------------------------------------------------------
    draw_rect(Rect2(0, 90, 60, 30), Color.RED)                    # filled
    draw_rect(Rect2(70, 90, 60, 30), Color.GREEN, false, 2.0)     # outline, 2 px

    # ---- Circles & arcs -----------------------------------------------------
    draw_circle(Vector2(30, 160), 20.0, Color.BLUE)               # filled
    draw_circle(Vector2(90, 160), 20.0, Color.BLUE, false, 2.0, true)  # ring, AA
    draw_arc(Vector2(150, 160), 20.0, 0.0, TAU * 0.75, 32, Color.ORANGE, 2.0)

    # ---- Polygons -----------------------------------------------------------
    var tri := PackedVector2Array([Vector2(0, 220), Vector2(40, 200), Vector2(40, 240)])
    draw_colored_polygon(tri, Color.YELLOW)
    # draw_polygon takes per-vertex colors (gradients!) and optional UVs/texture:
    draw_polygon(tri, PackedColorArray([Color.RED, Color.GREEN, Color.BLUE]))
```

Signature notes (Godot 4.x):

| Method | Key parameters |
|---|---|
| `draw_line(from, to, color, width = -1.0, antialiased = false)` | `width = -1.0` → hairline: always 1 pixel wide *on screen*, regardless of zoom. |
| `draw_dashed_line(from, to, color, width = -1.0, dash = 2.0, aligned = true, antialiased = false)` | `dash` is segment length. |
| `draw_polyline(points, color, width = -1.0, antialiased = false)` | Connected strip; per-point colors via `draw_polyline_colors`. |
| `draw_arc(center, radius, start_angle, end_angle, point_count, color, width = -1.0, antialiased = false)` | Angles in radians; `point_count` controls smoothness. |
| `draw_rect(rect, color, filled = true, width = -1.0, antialiased = false)` | `width` only meaningful when `filled = false`. |
| `draw_circle(position, radius, color, filled = true, width = -1.0, antialiased = false)` | Outline + AA parameters available since 4.2. |
| `draw_polygon(points, colors, uvs = ..., texture = null)` | One color total, or one per vertex. |

Per-vertex colors extend to strips too — `draw_polyline_colors` and `draw_multiline_colors` take a `PackedColorArray` matching the points, giving free gradients along a stroke:

```gdscript
# A trail that fades toward its tail — no shader, no texture:
func _draw() -> void:
    var cols := PackedColorArray()
    for i in trail_points.size():
        var t := float(i) / float(trail_points.size() - 1)
        cols.append(Color(0.5, 0.8, 1.0, t))       # transparent tail → solid head
    draw_polyline_colors(trail_points, cols, 3.0, true)
```

> ⚠️ **Pitfall** — The hairline convention bites in reverse: a *positive* width is in **local units**, so `width = 2.0` under a `Camera2D` zoom of 3.6 renders ~7 screen pixels. For debug overlays that must stay visually thin at any zoom, use `-1.0`; for world geometry that should scale with the world (a rope, a wall), use positive widths.

### API tour: textures and text

```gdscript
func _draw() -> void:
    # Textures — same rendering path as Sprite2D, but batched into this item:
    var tex: Texture2D = preload("res://icon.svg")
    draw_texture(tex, Vector2.ZERO)                          # natural size
    draw_texture(tex, Vector2(140, 0), Color(1, 1, 1, 0.5))  # tinted/translucent
    draw_texture_rect(tex, Rect2(0, 140, 64, 64), false)     # stretched into rect
    draw_texture_rect_region(tex, Rect2(80, 140, 32, 32),    # atlas sub-region
            Rect2(0, 0, 32, 32))

    # Text — needs a Font; ThemeDB provides a safe fallback:
    var font: Font = ThemeDB.fallback_font
    draw_string(font, Vector2(0, 230), "Hello, canvas!",
            HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
    draw_multiline_string(font, Vector2(0, 260), "wrapped\ntext",
            HORIZONTAL_ALIGNMENT_LEFT, 200, 14)
    # draw_char(font, pos, "A", 16) exists for glyph-level control.
```

`draw_string`'s position is the **baseline** of the first line, not the top-left corner — add roughly `font.get_ascent(font_size)` to a top-left anchor to place text like a Label would. The `width` parameter (`-1` = unlimited) clips/aligns within a box, which is how `HORIZONTAL_ALIGNMENT_CENTER` becomes meaningful.

### Transform state while drawing

Instead of transforming every point yourself, push a temporary transform for subsequent commands:

```gdscript
func _draw() -> void:
    for i in 12:
        draw_set_transform(Vector2(100, 100), TAU * i / 12.0, Vector2.ONE)
        draw_line(Vector2(30, 0), Vector2(40, 0), Color.WHITE, -1.0)  # clock ticks
    draw_set_transform(Vector2.ZERO)          # reset for whatever follows
    # draw_set_transform_matrix(Transform2D(...)) for full control.
```

`draw_set_transform(position, rotation = 0.0, scale = Vector2.ONE)` affects **all subsequent** commands in this `_draw()` call — remember to reset it.

### Antialiasing

Line-based methods accept a per-call `antialiased` flag. Filled polygons and the flag-less methods rely on **2D MSAA** (`rendering/anti_aliasing/quality/msaa_2d`), which smooths *all* canvas geometry edges at a GPU cost — usually worth enabling for vector-heavy desktop UIs, usually pointless for pixel art (where crunchy edges are the aesthetic and Nearest filtering dominates anyway).

### Drawing inside Control nodes

`_draw()` works identically on `Control`s, with two adjustments:

- **Coordinates are relative to the Control's top-left corner**, and the useful bound is `size` (the layout-assigned rect). A well-behaved custom Control draws inside `Rect2(Vector2.ZERO, size)` and re-renders on resize — which the engine triggers automatically (`NOTIFICATION_RESIZED` queues a redraw).
- **Report a minimum size** so containers reserve room for your drawing:

```gdscript
extends Control   # a sparkline widget usable inside any container

var samples: PackedFloat32Array = []

func _get_minimum_size() -> Vector2:
    return Vector2(80, 24)

func _draw() -> void:
    draw_rect(Rect2(Vector2.ZERO, size), Color(1, 1, 1, 0.06))   # subtle bg
    if samples.size() < 2:
        return
    var lo := samples[samples.size() - 1]
    var hi := lo
    for v in samples: lo = minf(lo, v); hi = maxf(hi, v)
    var span := maxf(hi - lo, 0.0001)
    var pts := PackedVector2Array()
    for i in samples.size():
        pts.append(Vector2(
            size.x * i / float(samples.size() - 1),
            size.y * (1.0 - (samples[i] - lo) / span)))
    draw_polyline(pts, Color("7ec8a9"), 1.5, true)
```

Drop this into any `VBoxContainer` and it behaves like a first-class themed widget — the pattern behind custom charts, waveform monitors and mini-graphs in tool UIs. (Pull colors from the theme — `get_theme_color(...)` — instead of hardcoding, once you reach section 17.)

### Worked example: an annotated radial timer

A complete, production-shaped `_draw()` node — a circular countdown used for "focus session" style timers:

```gdscript
class_name RadialTimer
extends Node2D

@export var radius := 28.0
@export var thickness := 5.0
@export var bg_color := Color(1, 1, 1, 0.15)
@export var fg_color := Color("7ec8a9")

var _progress := 1.0   # 1.0 = full, 0.0 = elapsed

func set_progress(value: float) -> void:
    var clamped := clampf(value, 0.0, 1.0)
    if is_equal_approx(clamped, _progress):
        return                     # no visual change → no redraw
    _progress = clamped
    queue_redraw()

func _draw() -> void:
    # Track (full ring):
    draw_arc(Vector2.ZERO, radius, 0.0, TAU, 64, bg_color, thickness, true)
    # Progress arc, from 12 o'clock, clockwise:
    if _progress > 0.0:
        var start := -TAU / 4.0
        draw_arc(Vector2.ZERO, radius, start, start + TAU * _progress,
                64, fg_color, thickness, true)
```

Note the guard in `set_progress()`: redrawing *only on change* is the habit that keeps `_draw()` nodes essentially free. Driving it is one line from a Tween (`tween_method(timer.set_progress, 1.0, 0.0, duration)` — section 12) or from a timer's `_process`.

---

## Custom drawing: performance and patterns

`_draw()` is fast — but it has its own cost model, different from sprites. Understanding it prevents both premature optimization and real regressions.

### The cost model

| Cost | When it's paid | Scale factor |
|---|---|---|
| Running your `_draw()` GDScript | Only on redraw (after `queue_redraw()`) | number of `draw_*` calls & script work |
| Replaying cached commands | Every frame the item is visible | number of commands in the list |
| GPU rasterization | Every frame | covered pixels, overdraw, MSAA |

Consequences:

1. **A static `_draw()` is nearly free after the first frame.** A 10,000-segment map drawn once costs script time once; replay is a GPU-side batch.
2. **Redraw frequency × command count is the real budget.** 200 commands redrawn on change: trivial. 20,000 commands redrawn every frame from `_process`: measurable script time — batch or cache.
3. **Fewer, bigger calls beat many small calls.** `draw_polyline` (1 call, N segments) over N × `draw_line`; `draw_multiline` for segment soups; one `draw_polygon` over triangle-by-triangle.

```gdscript
# SLOW-ish: 3 draw calls per cell, executed per redraw
for cell in cells:
    draw_rect(cell.rect, cell.fill)
    draw_rect(cell.rect, border_color, false, 1.0)
    draw_line(cell.rect.position, cell.rect.end, cross_color)

# BETTER: accumulate, then emit few large commands
var borders := PackedVector2Array()
for cell in cells:
    draw_rect(cell.rect, cell.fill)          # fills can't batch further in script
    borders.append_array(_rect_outline_points(cell.rect))
draw_multiline(borders, border_color, 1.0)
```

### Pattern: dirty-flag redraw

The universal structure for data-driven drawing — never redraw on a timer, always on change:

```gdscript
var _dirty := false
var _samples: PackedFloat32Array

func push_sample(v: float) -> void:
    _samples.append(v)
    _dirty = true

func _process(_delta: float) -> void:
    if _dirty:
        _dirty = false
        queue_redraw()      # coalesces any number of pushes into one redraw
```

(For a single mutating entry point, calling `queue_redraw()` directly in the setter — as `RadialTimer` does — is the same pattern with the flag inlined.)

### Pattern: debug overlay singleton

A dedicated overlay node at a high Z collects debug primitives from anywhere, renders once per frame, and compiles out of release builds:

```gdscript
# autoload: DebugDraw  (see AUTOLOAD_SAFETY.md for autoload discipline)
extends Node2D

var _lines: Array[Dictionary] = []

func line(from: Vector2, to: Vector2, color := Color.RED) -> void:
    if not OS.is_debug_build():
        return
    _lines.append({ "from": from, "to": to, "color": color })
    queue_redraw()

func _ready() -> void:
    z_index = 4000            # documented debug bracket, above gameplay Z
    top_level = true          # canvas-space coordinates

func _draw() -> void:
    for l in _lines:
        draw_line(l.from, l.to, l.color, -1.0, true)
    _lines.clear()            # collected fresh each frame by callers
```

Callers write `DebugDraw.line(pos, pos + velocity)` from any script; the overlay costs nothing when no one calls it.

### When to graduate away from _draw()

| Symptom | Better tool |
|---|---|
| Redrawing tens of thousands of commands every frame | `MultiMeshInstance2D` (GPU instancing), or move the visual into a shader |
| Thousands of identical shapes with per-instance transforms | `MultiMeshInstance2D` — see below |
| Complex per-pixel effects (glow, distortion, dissolve) | `ShaderMaterial` — [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md) |
| Drawing = a static image you keep re-emitting | Render once into a `SubViewport`, display the `ViewportTexture` (section 8) |
| Thick outlined shapes with joints/caps | `Line2D` node (miter joints, caps, width curves, textures) |
| Text-heavy layout | `Label`/`RichTextLabel` — the font layout engine handles shaping, wrapping, BiDi |

### Graduating to MultiMeshInstance2D

When the visual is *N copies of the same shape* with different transforms — starfields, rain, confetti, crowd dots on a map — `MultiMeshInstance2D` renders all instances in one draw call, with per-instance data set from script:

```gdscript
@onready var mmi: MultiMeshInstance2D = $Stars

func _ready() -> void:
    var mm := MultiMesh.new()
    mm.transform_format = MultiMesh.TRANSFORM_2D
    mm.use_colors = true
    mm.instance_count = 2000
    mm.mesh = _make_quad_mesh(Vector2(2, 2))       # a tiny QuadMesh
    for i in mm.instance_count:
        var t := Transform2D(0.0, Vector2(randf() * 1280.0, randf() * 720.0))
        mm.set_instance_transform_2d(i, t)
        mm.set_instance_color(i, Color(1, 1, 1, randf_range(0.2, 1.0)))
    mmi.multimesh = mm
```

Updating an instance is `set_instance_transform_2d(i, t)` per frame — cheap enough for thousands, since the geometry never leaves the GPU. The trade-off versus `_draw()`: every instance shares one mesh and texture; heterogeneous shapes stay in `_draw()` territory.

> ✅ **Best practice** — Keep `_draw()` overrides *pure*: read state, emit commands, never mutate. Pure draw functions can be called at any time by the engine, are trivially testable (feed state, screenshot-compare), and never cause the "works until I minimize the window" class of bugs that state-mutating draw code produces.

> ⚠️ **Pitfall** — `_draw()` never runs while `visible = false`, and `queue_redraw()` on a hidden item defers the redraw until it is shown. If a node reappears showing stale visuals, the redraw you issued while it was hidden did fire on show — the stale look means you *didn't* queue one; re-queue in `_ready()`-adjacent show logic or connect to `visibility_changed`.

---

## Viewports and SubViewport

A **Viewport** is a rendering surface: a rectangle of pixels the engine draws a world into. Godot 4 has three concrete flavors:

| Class | Role |
|---|---|
| `Window` | A viewport that projects onto an OS window. The scene tree root **is** a `Window` (the *root viewport*). |
| `SubViewport` | An off-screen viewport: renders into a texture instead of a window — a **render target**. |
| `Viewport` | The abstract base both inherit from; where most properties live. |

Everything from sections 1-7 happens *per viewport*: each viewport has its own canvas, its own camera (`canvas_transform`), its own CanvasLayer stack, its own 2D world. That makes `SubViewport` the engine's universal "render this somewhere else" tool.

### SubViewport as a render target

A `SubViewport` renders its children into an internal texture you can read with `get_texture()`:

```gdscript
# Scene structure:
# Main (Node2D)
# ├── SubViewport            ← size = Vector2i(256, 256)
# │   └── MinimapWorld       ← any 2D content, cameras, layers...
# └── Sprite2D               ← displays the result

func _ready() -> void:
    var svp: SubViewport = $SubViewport
    svp.size = Vector2i(256, 256)
    $Sprite2D.texture = svp.get_texture()   # a ViewportTexture, live-updating
```

The returned **`ViewportTexture`** is not a snapshot — it is a live handle: as the SubViewport re-renders, every user of the texture updates automatically. In the editor you can wire the same thing without code: on a `Sprite2D`/`TextureRect`, choose *New ViewportTexture* and pick the SubViewport node.

Canonical 2D production uses:

- **Minimap / picture-in-picture** — a second camera on the same world (see per-viewport worlds below).
- **Compositing for effects** — render a subtree once, then apply *one* shader to the flattened result (outline, dissolve, pixelation of a whole character).
- **UI in the world** — render a Control hierarchy onto a texture that lives on an in-world object (a computer screen inside the room).
- **Thumbnails / photo mode** — capture a scene to an `Image` and save it (below).
- **Fixed-resolution sub-rendering** — render pixel-art at a small native resolution and scale it up crisply while UI stays high-res.

### Update and clear modes

Render targets don't have to re-render every frame — that's a scheduling decision you own:

| `render_target_update_mode` | Behavior | Use for |
|---|---|---|
| `UPDATE_DISABLED` | Never re-renders | Frozen content |
| `UPDATE_ONCE` | Renders next frame, then resets to disabled | Thumbnails, static composites |
| `UPDATE_WHEN_VISIBLE` | Re-renders while its texture is visible (default) | Most cases |
| `UPDATE_WHEN_PARENT_VISIBLE` | Follows the parent's visibility | Nested viewport rigs |
| `UPDATE_ALWAYS` | Re-renders every frame regardless | Off-screen consumers (saving frames, shader input that's always sampled) |

```gdscript
# Cheap thumbnail: render one frame, then keep the texture forever.
svp.render_target_update_mode = SubViewport.UPDATE_ONCE
```

`render_target_clear_mode` (`CLEAR_MODE_ALWAYS` default, `CLEAR_MODE_NEVER`, `CLEAR_MODE_ONCE`) controls whether the target is wiped between renders. `CLEAR_MODE_NEVER` enables accumulation tricks — paint trails, fog-of-war reveal — where each frame draws *on top of* the previous content.

Other properties that matter in 2D work:

| Property | Effect |
|---|---|
| `size` | Render resolution in pixels (`Vector2i`). |
| `size_2d_override` + `size_2d_override_stretch` | Render the canvas at a *logical* size different from the texture size — the core of crisp pixel-art upscaling. |
| `transparent_bg` | Transparent instead of clear-color background — essential for composited overlays. |
| `disable_3d` | Skips 3D machinery entirely; enable for pure-2D targets. |
| `snap_2d_transforms_to_pixel`, `snap_2d_vertices_to_pixel` | Per-viewport pixel snapping for pixel-art stability. |
| `canvas_cull_mask` | Which `visibility_layer` bits this viewport renders — one world, different views. |
| `world_2d` | The `World2D` this viewport renders (see below). |
| `gui_disable_input` | Stop the viewport from processing GUI input (display-only targets). |

### Per-viewport worlds and shared worlds

Each viewport renders **a** `World2D` — by default its own. To make a minimap that shows *the same* world as the main game, point the SubViewport at the root viewport's world:

```gdscript
# Minimap: second camera on the SAME world.
minimap_viewport.world_2d = get_viewport().world_2d
# A Camera2D inside minimap_viewport now frames the shared world independently:
minimap_camera.zoom = Vector2(0.1, 0.1)
```

Conversely, leaving `world_2d` as its own gives you an **isolated** world: nothing leaks in or out — ideal for rendering a character preview that must not be lit, y-sorted or post-processed with the main scene.

> ⚠️ **Pitfall** — A `Camera2D` only drives the viewport it lives in. Dropping a camera inside a SubViewport controls the SubViewport; it will never scroll the main game, and vice versa. If a "camera does nothing", check which viewport tree it sits in.

### Displaying interactively: SubViewportContainer

To *embed* a SubViewport in a UI with automatic sizing and **input forwarding**, use `SubViewportContainer` (a Control):

```
UI (Control)
└── SubViewportContainer     ← stretch = true
    └── SubViewport
        └── GameWorld
```

With `stretch = true` the container drives the SubViewport's size to match its own rect; `stretch_shrink = N` renders at 1/N of that size and scales up — a one-property performance knob (render an expensive sub-scene at half resolution) or, at `1` with a larger manual `size`, a supersampling tool. The container also translates mouse events into the SubViewport's coordinate space, so buttons and drag-and-drop inside the sub-world just work. When you display a ViewportTexture manually (via `Sprite2D`/`TextureRect`) you get *no* input forwarding — for interactive content you must push events yourself with `Viewport.push_input()`, which is exactly what `SubViewportContainer` does for you.

> ✅ **Best practice** — Interactive sub-scenes → `SubViewportContainer`. Pure visual sampling (materials, minimap sprites, thumbnails) → `get_texture()` on a bare `SubViewport`. Mixing the two models (container *and* manual texture reuse) is legal but makes input paths hard to reason about.

### Worked example: a UI screen inside the world

A computer monitor in the room that displays — and runs — a real Control interface, drawn as part of the world (perspective, lighting, camera zoom all apply):

```gdscript
# Scene:
# Monitor (Sprite2D — the monitor frame art)
# ├── SubViewport  "ScreenVP"     size = (192, 128), transparent_bg = true
# │   └── ScreenUI (Control)      the actual interface scene
# └── ScreenSprite (Sprite2D)     positioned over the frame's screen area

@onready var screen_vp: SubViewport = $ScreenVP
@onready var screen_sprite: Sprite2D = $ScreenSprite

func _ready() -> void:
    screen_vp.disable_3d = true
    screen_vp.gui_disable_input = false
    screen_sprite.texture = screen_vp.get_texture()

func _unhandled_input(event: InputEvent) -> void:
    # Forward mouse events into the sub-world, remapped to its coordinates:
    if event is InputEventMouse:
        var local := screen_sprite.to_local(get_global_mouse_position())
        var uv := local / screen_sprite.texture.get_size() + Vector2(0.5, 0.5)
        if Rect2(Vector2.ZERO, Vector2.ONE).has_point(uv):
            var forwarded := event.duplicate() as InputEventMouse
            forwarded.position = uv * Vector2(screen_vp.size)
            screen_vp.push_input(forwarded)
```

The remap chain is section 5 again: world mouse → sprite-local → normalized UV → sub-viewport pixels, then **`push_input()`** delivers the event as if the cursor were inside the SubViewport. This exact structure powers in-world computers, phones, minigame cabinets — and, because the screen is just a sprite, it Y-sorts, tints and lights like any other furniture.

### Capturing to an image (screenshots, thumbnails)

Any viewport's current content can be copied to a CPU-side `Image`:

```gdscript
func save_screenshot(path: String) -> void:
    # Wait until the frame has fully rendered, or you may read an empty/old target:
    await RenderingServer.frame_post_draw
    var img: Image = get_viewport().get_texture().get_image()
    img.save_png(path)
```

`get_image()` is a GPU→CPU download — slow (milliseconds, plus a pipeline stall). Fine for a user-triggered screenshot or a one-off thumbnail; never per-frame. For Relax Room this powers the "share my room" capture: render the room's subtree in a `SubViewport` at a fixed 1280×720, `UPDATE_ONCE`, then save.

> ⚠️ **Pitfall** — Capturing in `_ready()` yields a black/empty image: nothing has been drawn yet. Always `await RenderingServer.frame_post_draw` (or at minimum two process frames) before the first `get_image()`.

> ⚠️ **Pitfall** — A `ViewportTexture` set up in the editor stores a *node path* to its viewport. Reparenting or renaming the SubViewport at runtime silently breaks the texture (pink/empty). Prefer assigning `svp.get_texture()` in code for anything dynamic.

---

## Resolution independence for desktop apps

A desktop companion app lives in a resizable window on monitors from 1366×768 laptops to 4K displays with 150 % OS scaling. "Resolution independence" is the discipline of designing at one **logical resolution** and letting the engine map it to any physical window. In Godot this is three project settings plus a handful of habits.

### The stretch system

Under **Project Settings → Display → Window → Stretch**:

| Setting | Options | Meaning |
|---|---|---|
| `stretch/mode` | `disabled`, `canvas_items`, `viewport` | *How* content scales when window size ≠ design size |
| `stretch/aspect` | `ignore`, `keep`, `keep_width`, `keep_height`, `expand` | *What happens* to the aspect ratio |
| `stretch/scale` | float | Extra global zoom factor on top of the computed scale |
| `stretch/scale_mode` | `fractional`, `integer` | Whether the computed scale may be non-integer (pixel art wants `integer`) |

The design size comes from `display/window/size/viewport_width` / `viewport_height`.

**`disabled`** — no scaling: a bigger window shows *more world* (or empty space). Only right when you handle layout entirely with Control anchors and want 1:1 pixels — e.g. tool-style apps.

**`canvas_items`** — the workhorse. Every CanvasItem is drawn directly at the *target* resolution with a scaling transform. Vector content (fonts, StyleBoxFlat, `_draw()`) stays **sharp at any window size** because it is rasterized at final resolution. This is what Relax Room ships (design size 1280×720, see section 19) and the right default for desktop apps.

**`viewport`** — the scene renders at the design resolution into the root viewport, and the *finished image* is stretched to the window. Content is pixel-perfect relative to the design grid but visibly scaled (soft or chunky). Choose it only for strict low-res pixel-art aesthetics where the doubled pixels *are* the look.

Aspect handling: `keep` letterboxes (black bars); **`expand`** keeps the design scale but *reveals more canvas* on wider/taller windows — the professional choice when your UI anchors can gracefully use extra space. `keep_width`/`keep_height` fix one axis and expand the other.

```ini
# project.godot — desktop app baseline (Relax Room values):
[display]
window/size/viewport_width=1280
window/size/viewport_height=720
window/stretch/mode="canvas_items"
```

> ✅ **Best practice** — Test resizing *early*. Run the app, drag the window to extreme sizes and to a portrait-ish shape, and watch every screen. Stretch bugs found at the end of a project mean re-anchoring every scene; found in week one, they cost minutes.

### Pixel-art inside a scaled app

`canvas_items` + fractional scaling resamples pixel art at non-integer factors → shimmering and uneven pixels. The toolkit:

- `stretch/scale_mode = integer` — snaps the global scale to whole numbers (letterboxing absorbs the remainder).
- Nearest filtering (project default or per-item `texture_filter`).
- `Camera2D.zoom` at chosen integer-ish factors (Relax Room uses 3.6 deliberately with Nearest filtering at 1280×720 — a pragmatic compromise; see section 19).
- For strict purity: render the world in a `SubViewport` at native pixel resolution with `size_2d_override`, scale the ViewportTexture by integers, keep UI outside at full resolution. This "hybrid resolution" pattern gives chunky world + crisp text, the standard for modern pixel-art titles.

### DPI and OS display scaling

On Windows, a 4K monitor at 150 % scaling reports a *smaller logical* window unless the app opts into DPI awareness (`display/window/dpi/allow_hidpi`, on by default in 4.x). What you tune:

```gdscript
# Query the environment:
var scale := DisplayServer.screen_get_scale()       # e.g. 1.5 on 150% (per-OS support)
var dpi := DisplayServer.screen_get_dpi()           # ~96 = 100% on Windows

# Scale the whole UI at runtime (root window content scale):
get_window().content_scale_factor = 1.5
```

`content_scale_factor` multiplies the stretch scale for the window — the one-line "make everything bigger" knob for accessibility settings or auto-DPI matching. Because `canvas_items` re-rasterizes vectors, fonts stay sharp after scaling; only bitmaps need high-res sources (provide 2× texture variants for critical UI art, or use SVG imports / MSDF fonts — section 17).

> ⚠️ **Pitfall** — Hardcoding pixel positions from `get_viewport().get_visible_rect().size` at `_ready()` and never updating breaks on resize. Either anchor Controls properly (layout system handles it) or connect to `get_viewport().size_changed` and re-derive. Any literal `1280`/`720` outside the project-constants file is a smell — Relax Room centralizes them (section 19).

### Desktop-companion specifics: transparent and borderless windows

A companion app that "sits on the desktop" — a character floating over the wallpaper with no window chrome — is a rendering configuration, not a special engine mode:

```ini
# project.godot
[display]
window/size/borderless=true
window/size/transparent=true              # window supports per-pixel alpha
window/size/always_on_top=true
window/per_pixel_transparency/allowed=true

[rendering]
viewport/transparent_background=true      # the viewport clears to transparent
```

```gdscript
# Runtime equivalents / toggles:
get_window().borderless = true
get_window().transparent_bg = true
get_window().always_on_top = true
```

Everything renders as normal — draw order, tweens, lights — but pixels nobody draws stay *transparent*, showing the desktop through. The consequences to design for:

- **Every stray opaque pixel is visible.** Background `ColorRect`s, the clear color, a full-screen `CanvasModulate` — all become giant desktop-covering slabs. The scene must be authored "floating": only the character/widget draws.
- **Click-through** needs managing: by default the whole window rectangle eats mouse input. `DisplayServer.window_set_mouse_passthrough(polygon)` restricts clickable area to a polygon (e.g. the character's silhouette), letting clicks elsewhere reach the desktop.
- **Per-pixel transparency costs compositing performance** and disables some optimizations — keep such windows small (size the window to the character, not the screen).
- 2D glow (section 18) composites against transparency poorly — bloom halos get premultiplied against the desktop; prefer additive fake glows (section 10) in transparent windows.

Window management details (multi-monitor placement, DPI per screen, tray behavior) continue in [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md); the rendering side above is complete.

---

## CanvasItemMaterial: blend and light modes

Every `CanvasItem` has a `material` slot. Two resource types fit in it: `ShaderMaterial` (custom code — [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md)) and **`CanvasItemMaterial`**, a tiny fixed-function material with exactly three knobs. Small as it is, it unlocks effects that `modulate` alone cannot express.

### Blend modes

`blend_mode` selects how the item's pixels combine with what's already drawn beneath it:

| Mode | Formula (conceptually) | Typical use |
|---|---|---|
| `BLEND_MODE_MIX` (default) | alpha blending | Normal sprites/UI |
| `BLEND_MODE_ADD` | `dst + src` | Glows, fire, sparks, "light blob" fakes — bright, over-exposes on stacking |
| `BLEND_MODE_SUB` | `dst − src` | Darkening effects, negative "shadow" splashes |
| `BLEND_MODE_MUL` | `dst × src` | Tint by underlying content: stained glass, fake shadow gradients |
| `BLEND_MODE_PREMULT_ALPHA` | premultiplied blending | Assets authored premultiplied; correct compositing of rendered smoke/fog |

```gdscript
var mat := CanvasItemMaterial.new()
mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
glow_sprite.material = mat
```

Additive sprites are the classic cheap substitute for 2D lights: a soft radial-gradient texture with `BLEND_MODE_ADD` reads as a light halo at a fraction of the cost of a real `PointLight2D` (which it can't fully replace — no shadows, cannot darken; see section 16).

> ⚠️ **Pitfall** — Materials do **not** cascade to children by default. Tinting a parent affects the subtree (`modulate` cascades); an additive material on a parent affects *only the parent's own drawing*. Set `use_parent_material = true` on children that should share it — useful for multi-sprite effects that must switch blend mode together.

### Light modes

`light_mode` controls how the item interacts with 2D lights (section 16):

| Mode | Behavior |
|---|---|
| `LIGHT_MODE_NORMAL` | Lit by lights, darkened by `CanvasModulate` (default) |
| `LIGHT_MODE_UNSHADED` | Ignores lights and `CanvasModulate` entirely — always renders at full authored color |
| `LIGHT_MODE_LIGHT_ONLY` | Visible **only** where lights touch it |

`LIGHT_MODE_UNSHADED` is the pragmatic answer to "the night tint is darkening my UI/highlight": exempt the item instead of fighting layer masks. `LIGHT_MODE_LIGHT_ONLY` enables reveal mechanics — hidden glyphs that appear only inside a lantern's radius.

The third property, `particles_animation` (with `particles_anim_h_frames` / `v_frames` / `loop`), exists solely to let `GPUParticles2D` play flipbook textures; leave it off for everything else.

> ✅ **Best practice** — Share material *resources*: one `additive.tres` `CanvasItemMaterial` reused by every glow in the project, not a fresh material per node. Shared materials mean fewer state changes when batching and one place to tweak. (Resource sharing mechanics: [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md).)

---

## Modulate patterns

`modulate` looks trivial — it's a color multiply — yet a disciplined handful of patterns built on it covers most of an app's visual feedback vocabulary. This section is the pattern catalog; all of it composes with Tweens from section 12.

### Pattern: fade in / fade out (with visibility bookends)

The canonical implementation (introduced in section 2, completed here as an API):

```gdscript
## Fades `item` out and hides it. Returns the tween so callers can await it.
func fade_out(item: CanvasItem, duration := 0.3) -> Tween:
    var tween := item.create_tween()
    tween.tween_property(item, "modulate:a", 0.0, duration)
    tween.tween_callback(item.hide)
    return tween

## Shows `item` and fades it in.
func fade_in(item: CanvasItem, duration := 0.3) -> Tween:
    item.modulate.a = 0.0
    item.show()
    var tween := item.create_tween()
    tween.tween_property(item, "modulate:a", 1.0, duration)
    return tween

# Caller:
await fade_out(old_panel).finished
await fade_in(new_panel).finished
```

Details that make it production-grade: the tween is created on the *target* (`item.create_tween()`) so it dies with the target; `show()` precedes the fade-in so the first frame renders at alpha 0 rather than popping; the function returns the `Tween` so callers can `await`, chain or kill it.

### Pattern: crossfade between two states

Two stacked items, opposite alpha ramps, one tween:

```gdscript
func crossfade(from_item: CanvasItem, to_item: CanvasItem, duration := 0.4) -> void:
    to_item.modulate.a = 0.0
    to_item.show()
    var tween := create_tween()
    tween.set_parallel(true)
    tween.tween_property(from_item, "modulate:a", 0.0, duration)
    tween.tween_property(to_item, "modulate:a", 1.0, duration)
    tween.chain().tween_callback(from_item.hide)
```

Relax Room uses exactly this shape for room-theme changes (wall/floor overlay colors crossfading rather than snapping — section 19).

### Pattern: flash (damage, confirmation, attention)

A quick out-and-back on `modulate` (or `self_modulate` to spare children — section 2):

```gdscript
func flash(item: CanvasItem, color := Color(1.6, 1.6, 1.6), up := 0.06, down := 0.18) -> void:
    var tween := item.create_tween()
    tween.tween_property(item, "modulate", color, up)
    tween.tween_property(item, "modulate", Color.WHITE, down)
```

Note the **overbright** color `(1.6, 1.6, 1.6)`: modulate values above 1.0 are legal and *brighten* the texture. Without HDR 2D they clamp at white per channel — which is exactly what a "white flash" wants. (With `rendering/viewport/hdr_2d` enabled, overbright modulate additionally feeds glow — section 18.)

For a *repeating* attention pulse, loop and remember to kill:

```gdscript
var _pulse: Tween

func start_pulse(item: CanvasItem) -> void:
    stop_pulse()
    _pulse = item.create_tween().set_loops()          # infinite
    _pulse.tween_property(item, "modulate:a", 0.45, 0.5) \
          .set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
    _pulse.tween_property(item, "modulate:a", 1.0, 0.5) \
          .set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)

func stop_pulse() -> void:
    if _pulse:
        _pulse.kill()
        _pulse = null
```

### Pattern: color-coding UI state

Central palette, one function, no scattered literals:

```gdscript
const STATE_COLORS := {
    "normal":   Color.WHITE,
    "hovered":  Color(1.08, 1.08, 1.08),
    "selected": Color("aef2c9"),
    "disabled": Color(1, 1, 1, 0.4),
    "invalid":  Color(1.0, 0.55, 0.55),
}

func set_slot_state(slot: CanvasItem, state: StringName) -> void:
    var tween := slot.create_tween()
    tween.tween_property(slot, "modulate", STATE_COLORS[state], 0.12)
```

Tweening *to the state color* (rather than setting it) makes every state change feel intentional for one line of extra code. For themed Controls prefer Theme-level colors (section 17) — modulate-based state coloring is for world items and hybrid cases like Relax Room's furniture placement preview (valid = white, colliding = red).

### Pattern: ghost preview for placement

The drag-to-place preview — semi-transparent copy that colors by validity — is pure modulate composition, and it exercises the "partitioned channels" discipline: *alpha says "I am a preview", RGB says "valid or not"*, and the two never conflict:

```gdscript
const GHOST_ALPHA := 0.55
const VALID_TINT := Color(1, 1, 1)
const INVALID_TINT := Color(1.0, 0.45, 0.45)

var _ghost: Node2D

func begin_placement(furniture_scene: PackedScene) -> void:
    _ghost = furniture_scene.instantiate()
    _ghost.modulate.a = GHOST_ALPHA          # alpha channel: preview-ness
    world.add_child(_ghost)

func _process(_delta: float) -> void:
    if _ghost == null:
        return
    _ghost.global_position = _snap_to_grid(get_global_mouse_position())
    var ok := _placement_valid(_ghost.global_position)
    var tint := VALID_TINT if ok else INVALID_TINT
    _ghost.modulate = Color(tint.r, tint.g, tint.b, GHOST_ALPHA)   # RGB: validity

func commit_placement() -> void:
    _ghost.modulate = Color.WHITE            # restore full color — now it's real
    _ghost = null
```

The commit is one line *because* the ghost was the real node all along, just tinted — no swap of preview art for final art, no duplicate scene. This is Relax Room's decoration-mode preview in miniature (grid snapping from section 19's `CELL_SIZE`).

> ⚠️ **Pitfall** — Modulate multiplies, so it can only *remove* (or overdrive) channels: a pure-red modulate on a pure-blue sprite yields black, not red. To *replace* hue, you need a shader (or author a white/grayscale variant designed for tinting). Design tint-target art in near-white so modulate has range to work with.

> ✅ **Best practice** — Treat `modulate` as owned by exactly one system per node. If the state system, a flash effect and a fade can all write `modulate` on the same node, they will fight (a flash restoring "WHITE" mid-fade breaks the fade). Either route all changes through one manager function, or partition channels: state → `self_modulate`, fades → `modulate:a`, flash → a dedicated overlay sprite.

---

## Tween deep dive I: lifecycle and tweeners

**`Tween`** is Godot 4's code-first animation primitive: a lightweight object that interpolates values over time and then disposes of itself. It replaced the Godot 3 Tween *node* — in 4.x a tween is created, used, and forgotten; there is nothing to add to the scene tree.

### Creating a tween: binding matters

```gdscript
# The standard way — BOUND to the creating node:
var tween := create_tween()          # Node.create_tween()

# The exceptional way — unbound, owned by the scene tree:
var free_tween := get_tree().create_tween()
```

A **bound** tween's lifecycle follows its node:

- The node leaves the tree → the tween **pauses** (default `TWEEN_PAUSE_BOUND`).
- The node is freed → the tween is **killed** automatically.
- `tween.bind_node(other)` re-binds an unbound tween to a node after creation.

An **unbound** tween keeps running regardless of any node — necessary for the one pattern where the animating node *itself* is about to die (scene transitions animating a node across scene changes), and dangerous everywhere else, because it happily tweens properties of freed objects if you let it (section 14).

> ✅ **Best practice** — Default to `create_tween()` on the node whose properties you animate (or `target.create_tween()` when animating another node, as in the fade helpers of section 11). Binding is your free safety net; `get_tree().create_tween()` should appear only with a comment explaining why the tween must outlive a node.

A new tween starts **automatically**: processing begins on the next frame; you never call "start". An empty tween (no tweeners appended by the time it processes) reports an error and dies — a symptom you'll meet if a branch skips all `tween_*` calls.

### The four tweeners

Each `tween_*` call appends a **Tweener** — one step in the animation program:

| Call | Tweener | Animates |
|---|---|---|
| `tween_property(object, property, final_val, duration)` | `PropertyTweener` | Any property (incl. sub-paths like `"modulate:a"`, `"position:x"`) |
| `tween_interval(time)` | `IntervalTweener` | Nothing — a pause step |
| `tween_callback(callable)` | `CallbackTweener` | Nothing — invokes the callable at that point |
| `tween_method(callable, from, to, duration)` | `MethodTweener` | Calls the callable every frame with an interpolated value |

```gdscript
var tween := create_tween()
tween.tween_property(panel, "position:y", 40.0, 0.25)      # slide down
tween.tween_interval(0.1)                                  # beat
tween.tween_callback(sfx.play)                             # fire once
tween.tween_method(_set_counter, 0.0, 100.0, 1.0)          # animate a *value*

func _set_counter(value: float) -> void:
    counter_label.text = str(roundi(value))                # "0" … "100"
```

**`tween_property`** is the workhorse. The start value is sampled **when the tweener begins running** (not when you build the tween) — so a chained move continues from wherever the previous step left the node. Its modifiers:

```gdscript
tween.tween_property(sprite, "position", Vector2(200, 0), 0.5) \
    .from(Vector2(-50, 0))     # explicit start value
#   .from_current()            # sample start at BUILD time instead of run time
#   .as_relative()             # final_val becomes an OFFSET from the start
#   .set_delay(0.2)            # wait before this step
#   .set_ease(...) .set_trans(...)   # per-step curve override (section 13)
```

`as_relative()` turns "go to X" into "move by X" — the right semantics for nudges and shakes. `from_current()` matters when a *later* step should start from the value the property had when you *built* the tween, not whatever earlier steps did to it.

**`tween_method`** is the underrated one: it tweens a *number that doesn't exist as a property*. Progress bars driven through a setter, shader uniforms, typewriter text, count-up score labels — anything with a function taking one argument:

```gdscript
# Typewriter: reveal one character at a time.
func type_in(label: Label, text: String, cps := 40.0) -> void:
    label.text = text
    label.visible_characters = 0
    var tween := label.create_tween()
    tween.tween_method(
        func(n: float) -> void: label.visible_characters = int(n),
        0.0, float(text.length()), text.length() / cps)
```

**`tween_callback`** with `bind()` passes arguments; with `set_delay()` it becomes a poor-man's timer that dies with its node — often exactly right for one-shot delayed actions:

```gdscript
create_tween().tween_callback(spawn_particles.bind(global_position)).set_delay(0.5)
```

> ⚠️ **Pitfall** — `tween_property()` resolves the property path immediately, but the *target object* is only weakly referenced: if the target is freed mid-animation, the tween stops with an error in the debugger. Bound tweens on the target (`target.create_tween()`) eliminate the class of bugs; for tweens on *other* nodes' properties, kill them in `_exit_tree()` (section 14).

### Sub-property paths

Property paths accept component sub-paths — tween exactly the channel you mean, leaving the rest writable by other systems:

```gdscript
tween.tween_property(node, "modulate:a", 0.0, 0.3)    # alpha only
tween.tween_property(node, "position:x", 640.0, 1.0)  # x only; y stays free
tween.tween_property(node, "scale:y", 0.0, 0.2)       # squash
```

This composes with the "one owner per channel" discipline from section 11: fades own `modulate:a`, state colors own the RGB, and neither stomps the other.

### Sequencing game flow with awaits

Because every tweener call returns quickly and the tween runs on its own, `await` turns multi-step visual sequences into linear, readable functions — the async/await pattern applied to presentation:

```gdscript
func play_purchase_sequence(item: Node2D, slot: Control) -> void:
    _input_locked = true

    # 1. Item flies to the slot (position is runtime-dependent → Tween, not AnimationPlayer)
    var fly := item.create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
    fly.tween_property(item, "global_position",
            slot.get_screen_position() + slot.size * 0.5, 0.35)
    await fly.finished

    # 2. Slot pops
    var pop := slot.create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
    pop.tween_property(slot, "scale", Vector2(1.15, 1.15), 0.1)
    pop.tween_property(slot, "scale", Vector2.ONE, 0.15)
    await pop.finished

    # 3. Only now update the data and unlock
    inventory.add(item.id)
    item.queue_free()
    _input_locked = false
```

The structure to copy: *lock input → animate → mutate state → unlock*. State changes after the animation completes keep logic and visuals honest with each other. The kill-vs-await caveat detailed in section 13 applies doubly here — if any awaited tween can be killed (scene change mid-sequence), the function never resumes and `_input_locked` stays true; production versions either make the sequence unkillable-by-design (short, node-bound, no external kill paths) or wrap the unlock in a `tween_callback` that runs on the tween regardless of the awaiter.

---

## Tween deep dive II: sequencing, easing and control

### Sequential by default, parallel on demand

Tweeners appended to a tween run **one after another**. Two tools change that:

```gdscript
# parallel(): the NEXT tweener runs alongside the PREVIOUS one.
var tween := create_tween()
tween.tween_property(panel, "position:y", 40.0, 0.3)
tween.parallel().tween_property(panel, "modulate:a", 1.0, 0.3)   # same time as the move
tween.tween_property(panel, "scale", Vector2.ONE, 0.15)          # after both

# set_parallel(true): EVERYTHING from here on runs simultaneously.
var t2 := create_tween()
t2.set_parallel(true)
t2.tween_property(sprite, "position", target, 0.5)
t2.tween_property(sprite, "rotation", TAU, 0.5)
t2.tween_property(sprite, "modulate:a", 0.0, 0.5)
t2.chain().tween_callback(sprite.queue_free)    # chain(): back to sequential
```

`chain()` after `set_parallel(true)` inserts a sequence point: the chained tweener waits for the whole parallel block. The grammar in one line: *default = sequence; `parallel()` = join previous step; `set_parallel` = change the default; `chain()` = insert a barrier.*

Mixed timing inside a parallel block comes from `set_delay()` on individual tweeners — the idiom for staggered list animations:

```gdscript
# Stagger: each menu item flies in 0.06 s after the previous one.
var tween := create_tween().set_parallel(true)
for i in items.size():
    var item: Control = items[i]
    item.position.x -= 40.0
    item.modulate.a = 0.0
    tween.tween_property(item, "position:x", item.position.x + 40.0, 0.25) \
         .set_delay(i * 0.06).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
    tween.tween_property(item, "modulate:a", 1.0, 0.25).set_delay(i * 0.06)
```

For **reusable composed animations**, Godot 4.4+ adds `tween_subtween(subtween)`: build a self-contained `Tween` (e.g. "the standard button pop") and embed it as a single step inside a larger sequence.

### Easing: the trans × ease matrix

Interpolation shape is set by two orthogonal choices:

- **`set_trans(TransitionType)`** — the *curve family*: how the value accelerates.
- **`set_ease(EaseType)`** — *which end* of the curve is emphasized: `EASE_IN` (slow start), `EASE_OUT` (slow end), `EASE_IN_OUT`, `EASE_OUT_IN`.

`TransitionType` families in 4.x: `TRANS_LINEAR`, `TRANS_SINE`, `TRANS_QUAD`, `TRANS_CUBIC`, `TRANS_QUART`, `TRANS_QUINT`, `TRANS_EXPO`, `TRANS_CIRC`, `TRANS_ELASTIC`, `TRANS_BOUNCE`, `TRANS_BACK`, `TRANS_SPRING`. Defaults: **`TRANS_LINEAR`** with **`EASE_IN_OUT`** (ease is irrelevant for linear).

The practical selection matrix — memorize the first four rows and you cover 90 % of UI work:

| Trans + Ease | Feel | Use for |
|---|---|---|
| `TRANS_QUAD` + `EASE_OUT` | Natural deceleration | Default for almost everything arriving: panels, characters, camera |
| `TRANS_QUAD` + `EASE_IN` | Gentle acceleration | Things *leaving* the screen |
| `TRANS_CUBIC` + `EASE_OUT` | Stronger, snappier arrival | Menus, cards, tooltips |
| `TRANS_LINEAR` | Mechanical constancy | Progress bars, countdowns, rotations of gears/loaders |
| `TRANS_SINE` + `EASE_IN_OUT` | Soft both ends | Loops (pulse, breathing, hover bob) |
| `TRANS_EXPO` + `EASE_OUT` | Fast snap, long settle | Zooms, "whoosh" reveals |
| `TRANS_BACK` + `EASE_OUT` | Small overshoot past target | Playful UI pops (buttons, badges) |
| `TRANS_ELASTIC` + `EASE_OUT` | Springy wobble around target | Notifications, bouncy icons — use sparingly |
| `TRANS_BOUNCE` + `EASE_OUT` | Bounces like dropped object | Physical drops, comedic effects |
| `TRANS_SPRING` + `EASE_OUT` | Damped spring settle | Softer alternative to elastic |

Scoping rules: `tween.set_trans()/set_ease()` set the **default for every subsequent tweener** on that tween; per-tweener `.set_trans()/.set_ease()` override for that step only.

```gdscript
var tween := create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
tween.tween_property(card, "position", slot_pos, 0.3)                  # quad/out
tween.tween_property(card, "scale", Vector2.ONE, 0.2) \
     .set_trans(Tween.TRANS_BACK)                                      # back/out for the pop
```

> ✅ **Best practice** — Standardize motion in project constants: one duration scale (e.g. `0.15 / 0.3 / 0.5` for micro/standard/large) and one or two trans/ease pairs. Uniform motion grammar is what makes an app feel "designed"; a different curve on every panel feels random. Relax Room pins `PANEL_TWEEN_DURATION = 0.3` and `FADE_DURATION = 0.5` (section 19).

> ⚠️ **Pitfall** — `TRANS_ELASTIC`/`TRANS_BACK` with `EASE_OUT` *overshoot the target*. Never use them on properties with hard limits — alpha (clamps visibly), a health-bar fill (shows >100 %), positions flush against a screen edge. Overshoot belongs on scale and free positions.

### Loops, speed and time

```gdscript
var tween := create_tween()
tween.set_loops(3)        # run the whole sequence 3 times
tween.set_loops()         # 0 = infinite — MUST be killed manually eventually
tween.set_speed_scale(2.0)  # play at double speed (durations halved)
tween.set_ignore_time_scale(true)   # real-time even when Engine.time_scale = 0.2
tween.set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)  # step with physics ticks
tween.set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)      # keep running while tree paused
```

- `set_loops(n)` loops the **entire tweener sequence**; per-step loops require nesting via subtweens or restructuring.
- `set_speed_scale()` is live — a settings-driven "reduce motion / faster animations" toggle can walk active tweens or set it at creation from a global constant.
- `set_ignore_time_scale(true)` and `TWEEN_PAUSE_PROCESS` are the pair that keeps *UI* animating while *gameplay* is paused or slow-motion'd — pause menus that still fade, hit-stop effects that don't freeze the HUD.
- `TWEEN_PROCESS_PHYSICS` matters when tweening physics-relevant positions, keeping steps aligned with the physics tick.

### Tween timing vs SceneTreeTimer

Godot offers three ways to say "do X in 0.4 seconds" — choosing deliberately avoids a whole class of lifetime bugs:

```gdscript
# A) Tween interval + callback — dies with the node (bound), kill-able:
create_tween().tween_callback(_open_door).set_delay(0.4)

# B) SceneTreeTimer — fires even if this node is freed meanwhile:
get_tree().create_timer(0.4).timeout.connect(_open_door)

# C) await on a SceneTreeTimer — suspends this function:
await get_tree().create_timer(0.4).timeout
_open_door()
```

| Criterion | Tween delay (A) | SceneTreeTimer (B/C) |
|---|---|---|
| Auto-cancel when node dies | yes (bound tween) | **no** — callback fires into a freed node unless you guard |
| Can be killed early | yes (`kill()`) | no (only disconnect) |
| Pause behavior | configurable (`set_pause_mode`) | `process_always` flag at creation |
| Part of a larger sequence | naturally (chain more tweeners) | manual |

The rule: **delays that belong to a node's behavior → tween; delays that must survive the node → SceneTreeTimer.** Variant C after a node's death raises "resumed after await, but instance is gone" errors — guard with `is_instance_valid(self)`-style checks or prefer A. For *repeating* schedules, a `Timer` node (with `autostart`/`one_shot`) remains the clearest tool.

### Signals and awaiting

```gdscript
var tween := create_tween()
tween.tween_property(panel, "modulate:a", 0.0, 0.3)

# Style A — await (reads sequentially; resumes this function later):
await tween.finished
panel.queue_free()

# Style B — connect (fire-and-forget):
tween.finished.connect(panel.queue_free)

# Also available:
# tween.step_finished(idx)  — after each sequential step
# tween.loop_finished(loop) — after each loop iteration
```

> ⚠️ **Pitfall** — `await tween.finished` **never resumes** if the tween is killed first (kill ≠ finish). Code after such an `await` silently never runs — a notorious source of "stuck" state machines. If a tween can be killed (and per section 14, most can), prefer callbacks attached to the tween, or guard the await path so the killer also unwinds whatever awaited.

### Runtime control

| Method | Effect |
|---|---|
| `pause()` / `play()` | Suspend / resume processing |
| `stop()` | Stop **and reset** to the beginning (elapsed time cleared) |
| `kill()` | Destroy the tween; properties freeze at current values |
| `custom_step(delta)` | Manually advance a paused tween — scrubbing, debug stepping |
| `is_running()` / `is_valid()` | State queries; `is_valid()` is false after kill/finish |
| `get_total_elapsed_time()` | Time since start (loops included) |

`custom_step()` turns a tween into a scrubbable timeline — pause it, then feed deltas from any source (a slider, a "frame advance" debug key):

```gdscript
var _scrub: Tween

func _ready() -> void:
    _scrub = create_tween()
    _scrub.tween_property(character, "position:x", 900.0, 2.0)
    _scrub.pause()                       # never advances on its own

func _on_timeline_slider_changed(value: float) -> void:   # slider 0..2 s
    var delta := value - _scrub.get_total_elapsed_time()
    if delta > 0.0:
        _scrub.custom_step(delta)        # forward only; rebuild to rewind
```

(Backwards scrubbing requires rebuilding the tween or driving the property from an interpolation function directly — `Tween.interpolate_value()` is the static helper for exactly that.)

---

## Tween discipline: kill(), cleanup and Tween vs AnimationPlayer

Tweens are the easiest animation tool to *start* using and the easiest to leak. This section is the module's safety chapter — the difference between demo code and production code.

### The two failure modes

**Failure 1 — the overlapping tween.** Calling an animation function twice creates two tweens driving the same property; they fight every frame and the visual stutters or snaps:

```gdscript
# BUG: hover in/out rapidly → several tweens tug at scale simultaneously.
func _on_mouse_entered() -> void:
    create_tween().tween_property(self, "scale", Vector2(1.1, 1.1), 0.2)

func _on_mouse_exited() -> void:
    create_tween().tween_property(self, "scale", Vector2.ONE, 0.2)
```

**Failure 2 — the immortal loop.** An infinite (`set_loops()`) or unbound tween that nobody stores can never be stopped early — you have no reference to `kill()`.

Both share one root cause: *a tween someone might need to stop was not stored.* Hence the discipline:

### The member-variable kill pattern

```gdscript
var _scale_tween: Tween

func _animate_scale(target: Vector2) -> void:
    if _scale_tween:
        _scale_tween.kill()               # kill() on an already-dead tween is safe
    _scale_tween = create_tween()
    _scale_tween.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
    _scale_tween.tween_property(self, "scale", target, 0.2)

func _on_mouse_entered() -> void: _animate_scale(Vector2(1.1, 1.1))
func _on_mouse_exited() -> void:  _animate_scale(Vector2.ONE)
```

Because the *new* tween samples the property's current value when it starts, killing mid-flight and retargeting produces a smooth redirect, not a snap — the property simply turns toward the new goal from wherever it is. This "kill-and-replace" is the single most important tween idiom.

Rules of thumb:

1. **Store every tween that outlives the function that made it** (loops, long moves, anything user-interruptible).
2. **Kill before recreate** for any animation reachable twice (`hover`, `open/close`, `select`).
3. Fire-and-forget *is fine* for short one-shots on self (`flash`, a 0.2 s pop) — bound tweens die with the node, and nothing else will ever need to stop them.

### The _exit_tree cleanup pattern

Bound tweens die with their node — but tweens you created on *yourself* that animate *another* node, and any unbound tween, survive your death and then poke freed objects. Standard hygiene:

```gdscript
var _tween: Tween

func _exit_tree() -> void:
    if _tween and _tween.is_valid():
        _tween.kill()
    _tween = null
```

This costs three lines and retires an entire category of "ObjectDB instance leaked / previously freed" errors — including the audit findings that motivated Relax Room's tween rules (section 19).

> ⚠️ **Pitfall** — `stop()` is not `kill()`. `stop()` resets and keeps the tween alive for reuse via `play()`; `kill()` destroys it. Using `stop()` where you meant `kill()` leaves valid-but-idle tweens accumulating; using `kill()` where you meant "pause" forces you to rebuild. And a killed tween's properties freeze mid-flight — if the node must land in a defined state, set it explicitly after killing (`panel.modulate.a = 0.0`).

> ✅ **Best practice** — Wrap recurring animated behaviors in small functions returning the `Tween` (as the fade helpers in section 11 do). Call sites stay one-line, the kill pattern lives in one place, and refactoring a curve or duration touches a single function.

### Tween vs AnimationPlayer

Both animate properties; they answer different questions.

| Criterion | `Tween` | `AnimationPlayer` |
|---|---|---|
| Authoring | Code, at runtime | Editor timeline, keyframes |
| Targets/values known… | at runtime (dynamic positions, computed colors) | at design time |
| Multi-property choreography | possible, verbose beyond ~5 tracks | native: unlimited tracks, one timeline |
| Preview | run the game | scrub in editor |
| Blending/transitions between animations | manual | `AnimationTree`, cross-fade |
| Designer-editable without code | no | yes |
| Method/audio/sub-anim tracks | callbacks only | built-in track types |
| Cost of a one-liner | one line | new Animation resource + node |

Decision rule: **values computed at runtime → Tween; choreography authored by a human → AnimationPlayer.** A panel sliding to a position that depends on window size: Tween. A character's 12-keyframe wave with sound cues: AnimationPlayer. A cutscene: AnimationPlayer. "Fade this arbitrary node out": Tween. They compose, too — an `AnimationPlayer` animation can call a method that starts a Tween for the runtime-dependent part.

Relax Room draws the line exactly there: sprite-frame animations (walk cycles) live in `AnimationPlayer`/`AnimatedSprite2D` assets; every *interface* motion — panel fades, character walk-in position, popup pops — is Tweens, because targets depend on runtime layout (section 19).

### Tween cheat sheet

The whole of sections 12-14 on one card:

```gdscript
var tween := create_tween()                     # bound to self; auto-starts next frame
tween.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)   # defaults for all steps

tween.tween_property(node, "position", target, 0.3)          # step 1
tween.parallel().tween_property(node, "modulate:a", 1.0, 0.3)# with step 1
tween.tween_interval(0.1)                                    # then wait
tween.tween_method(_set_progress, 0.0, 1.0, 0.5)             # then animate a value
tween.tween_callback(_done)                                  # then fire once

# Modifiers per step:   .from(v) .from_current() .as_relative() .set_delay(t)
#                       .set_trans(...) .set_ease(...)
# Whole-tween:          .set_parallel() .chain() .set_loops(n) .set_speed_scale(s)
#                       .set_pause_mode(...) .set_process_mode(...)
#                       .set_ignore_time_scale()
# Control:              pause() play() stop()=reset kill()=destroy
# Signals:              finished  step_finished(i)  loop_finished(n)
# Discipline:           store if interruptible · kill-before-recreate ·
#                       _exit_tree() kills tweens touching other nodes ·
#                       never await .finished on a killable tween
```

---

## Parallax: Parallax2D and the legacy nodes

Parallax is depth from *differential scrolling*: far layers move less than near layers as the camera pans, and the brain reads distance. Godot 4 has two APIs for it — one current, one legacy — plus a manual pattern for non-camera parallax.

### Parallax2D (Godot 4.3+, recommended)

**`Parallax2D`** replaced the `ParallaxBackground`/`ParallaxLayer` pair as the recommended approach in 4.3. It is a plain `Node2D`: one node per depth layer, placed anywhere in the scene, no special container required. Its children scroll according to its properties whenever the camera moves.

```
World
├── Parallax2D  "SkyLayer"      scroll_scale = (0.0, 0.0)   ← static backdrop
│   └── Sprite2D
├── Parallax2D  "FarTrees"      scroll_scale = (0.3, 0.3)
│   └── Sprite2D
├── Parallax2D  "NearTrees"     scroll_scale = (0.7, 0.7)
│   └── Sprite2D
├── TileMapLayer "Ground"                                    ← normal, scale 1.0
└── Player + Camera2D
```

Key properties (verified against the 4.x class reference):

| Property | Type | Meaning |
|---|---|---|
| `scroll_scale` | `Vector2` | Multiplier on camera motion. `< 1` = far (moves less), `1` = with the world, `> 1` = nearer than the action (foreground). |
| `repeat_size` | `Vector2` | Tiles the children's textures with this period — infinite scrolling backgrounds. `0` = no repeat. |
| `repeat_times` | `int` | How many extra repetitions to draw across the viewport. |
| `autoscroll` | `Vector2` | Automatic drift in px/s, independent of camera — clouds, ambient motion. |
| `scroll_offset` | `Vector2` | Manual offset added on top of camera-driven scroll. |
| `screen_offset` | `Vector2` | The camera-driven offset itself; auto-updated unless you take control. |
| `ignore_camera_scroll` | `bool` | Stop following the camera — you drive `screen_offset` yourself. |
| `follow_viewport` | `bool` | Whether the node uses the viewport's canvas transform. |
| `limit_begin` / `limit_end` | `Vector2` | Clamp scrolling inside a range — stop the sky sliding past level bounds. |

```gdscript
# Endless horizontally-scrolling cloud layer with ambient drift:
var clouds := Parallax2D.new()
clouds.scroll_scale = Vector2(0.2, 1.0)     # weak horizontal parallax, no vertical trick
clouds.repeat_size = Vector2(1536, 0)       # texture repeats every 1536 px
clouds.autoscroll = Vector2(12.0, 0.0)      # slow constant drift
add_child(clouds)
clouds.add_child(cloud_sprite)
```

> ⚠️ **Pitfall** — `repeat_size` must match (or divide evenly into) the child texture's scaled width, or seams appear at every period. Compute it: `texture.get_width() * sprite.scale.x`. And keep the child sprite's own position near origin — offsets inside the layer shift the repeat window.

> ✅ **Best practice** — Migrating a 4.0-4.2 project? Replace each `ParallaxLayer` with a `Parallax2D` (motion_scale → `scroll_scale`, motion_mirroring → `repeat_size`), delete the `ParallaxBackground` container, and re-test limits. The editor's node-conversion tooling can do the mechanical part; verify the repeat sizes by eye afterward.

### Camera interaction notes

`Parallax2D` reads the camera's motion through the viewport's canvas transform, which has practical consequences:

- **Camera smoothing is inherited for free**: `position_smoothing_enabled` on the `Camera2D` eases the canvas transform, so parallax layers glide with the same easing — no extra work.
- **Zoom scrolls parallax too.** Zooming changes the canvas transform; far layers (low `scroll_scale`) visually "resist" the zoom, which usually looks *right* (distant mountains grow slower) but surprises people expecting a pure pan effect. If a backdrop must be zoom-immune, keep it on a `CanvasLayer` instead.
- **Physics-interpolated cameras** (4.x `physics_interpolation`) pair fine with `Parallax2D`; the node exposes `physics_interpolation_mode` to opt in/out per layer if a layer stutters against an interpolated camera.
- With `ignore_camera_scroll = true` you own `screen_offset` completely — the bridge between engine-assisted and manual parallax: keep the repeat/limit machinery, drive the motion from anything (mouse, scroll position of a UI, elapsed time).

### The legacy pair: ParallaxBackground + ParallaxLayer

Still shipped and functional, and you *will* meet it in tutorials and older codebases:

- **`ParallaxBackground`** — a `CanvasLayer` subclass acting as container; hooks the camera and drives its children. Offers `scroll_base_offset`, `scroll_base_scale`, `scroll_ignore_camera_zoom`, and scroll limits.
- **`ParallaxLayer`** — one per depth plane, child of the background; per-layer `motion_scale` (≈ `scroll_scale`), `motion_offset`, `motion_mirroring` (≈ `repeat_size`).

Mapping table for reading old code:

| Legacy | Parallax2D equivalent |
|---|---|
| `ParallaxLayer.motion_scale` | `scroll_scale` |
| `ParallaxLayer.motion_mirroring` | `repeat_size` |
| `ParallaxLayer.motion_offset` | `scroll_offset` |
| `ParallaxBackground.scroll_limit_begin/end` | `limit_begin` / `limit_end` per node |
| container-level base offset/scale | per-node properties (no container) |

Because `ParallaxBackground` is a CanvasLayer, it lives outside the world canvas — a common source of "my parallax ignores z_index" confusion that `Parallax2D` (a normal canvas citizen) simply doesn't have. New work: `Parallax2D`, always.

### Manual parallax: input-driven depth without a camera

Parallax nodes react to the **camera**. Relax Room's main menu has no moving camera — its depth effect tracks the **mouse** instead, which calls for the manual pattern: N layers, one normalized depth factor each, offsets written every frame.

```gdscript
# Simplified from scripts/rooms/window_background.gd (see section 19 for the real one):
const PARALLAX_STRENGTH := 8.0        # max shift in px for the nearest layer

var _layers: Array[Sprite2D] = []
var _factors: Array[float] = []       # 0.0 (far, static) … 1.0 (near, full shift)

func _process(_delta: float) -> void:
    var vp_size := get_viewport_rect().size
    var mouse := get_viewport().get_mouse_position()
    var offset := (mouse - vp_size * 0.5) / (vp_size * 0.5)   # −1 … +1
    for i in _layers.size():
        _layers[i].position.x = -offset.x * PARALLAX_STRENGTH * _factors[i]
```

The same three ingredients appear in every parallax implementation, engine-assisted or manual: a *driver signal* (camera or mouse), a *per-layer factor*, and an *offset application*. If you can name those three in any effect you see, you can rebuild it.

> ✅ **Best practice** — Derive factors from layer index (`float(i) / float(count - 1)`) rather than hand-tuning each: the depth ramp stays monotonic when layers are added or removed, and one strength constant tunes the whole effect.

---

## 2D lighting overview

Godot's 2D renderer supports real dynamic lights: textures that *add or modulate illumination* on the canvas items they touch, with occluders casting real-time shadows. Used sparingly, 2D lighting turns flat scenes atmospheric — a desk lamp pooling warm light in a cozy room is exactly this feature.

### The cast

| Node | Role |
|---|---|
| `PointLight2D` | Positional light with a **texture** defining its falloff shape — lamps, candles, projectiles. |
| `DirectionalLight2D` | Infinitely-distant parallel light — sun/moon over the whole scene. |
| `LightOccluder2D` | Polygonal shadow caster (holds an `OccluderPolygon2D`). |
| `CanvasModulate` | Not a light: darkens the *whole canvas* to give lights something to contrast against (section 18). |

### PointLight2D essentials

A `PointLight2D` without a texture emits nothing: the **texture is the light** — typically a soft radial gradient (white center fading to black). Author it once (a `GradientTexture2D` works) and reuse.

```gdscript
var lamp := PointLight2D.new()
lamp.texture = preload("res://assets/lights/soft_radial.tres")
lamp.texture_scale = 2.0                    # size of the pool of light
lamp.color = Color(1.0, 0.87, 0.7)          # warm tungsten
lamp.energy = 1.2                           # intensity multiplier
lamp.blend_mode = Light2D.BLEND_MODE_ADD    # default: adds light
add_child(lamp)
```

Shared `Light2D` properties that matter:

| Property | Effect |
|---|---|
| `energy` | Brightness multiplier. |
| `color` | Tint of the emitted light. |
| `blend_mode` | `BLEND_MODE_ADD` (illuminate), `BLEND_MODE_SUB` (darkness "anti-light"), `BLEND_MODE_MIX` (replace toward light color). |
| `range_item_cull_mask` | Bitmask matched against each item's `light_mask` — *which items* this light affects. |
| `range_layer_min/max`, `range_z_min/max` | Constrain lighting by CanvasLayer range and Z range — keep room lights off the UI. |
| `height` | Virtual Z-height of the light for **normal-map** shading — no effect without normal maps. |
| `shadow_enabled` | Enables shadow casting from occluders. |
| `shadow_color` | Color (and alpha) of the shadowed region. |
| `shadow_filter` | `SHADOW_FILTER_NONE` (hard, fastest), `SHADOW_FILTER_PCF5`, `SHADOW_FILTER_PCF13` (softest, priciest). |
| `shadow_filter_smooth` | Softening amount for PCF filters; high values can band. |
| `shadow_item_cull_mask` | Which occluders cast shadows for this light. |

`DirectionalLight2D` adds `max_distance` (how far from the camera shadows stay valid) and reads its direction from the node's rotation. Keep `energy` modest (0.2-0.6) when combined with `CanvasModulate` night tints, or the scene washes out.

### Authoring light textures in code

You don't need art assets to prototype lights — `GradientTexture2D` builds soft radial falloffs procedurally, so light shapes live in version-controllable resources:

```gdscript
func make_radial_light(size := 256) -> GradientTexture2D:
    var grad := Gradient.new()
    grad.set_color(0, Color(1, 1, 1, 1))       # bright center
    grad.set_color(1, Color(1, 1, 1, 0))       # transparent edge
    var tex := GradientTexture2D.new()
    tex.gradient = grad
    tex.fill = GradientTexture2D.FILL_RADIAL
    tex.fill_from = Vector2(0.5, 0.5)          # center
    tex.fill_to = Vector2(0.5, 0.0)            # radius reaches the edge
    tex.width = size
    tex.height = size
    return tex

# lamp.texture = make_radial_light()
```

Tuning the gradient's midpoints shapes the falloff curve (a fast-then-slow fade reads as a focused bulb; near-linear reads as ambient spill). Save the configured `GradientTexture2D` as a `.tres` and every light in the project shares one falloff definition — same reuse argument as materials in section 10.

### Shadows

Shadows come from **`LightOccluder2D`** nodes holding an `OccluderPolygon2D`:

```gdscript
var occluder := LightOccluder2D.new()
var poly := OccluderPolygon2D.new()
poly.polygon = PackedVector2Array([
    Vector2(-16, -8), Vector2(16, -8), Vector2(16, 8), Vector2(-16, 8),
])
poly.closed = true
# cull_mode: CULL_DISABLED (both faces), CULL_CLOCKWISE / CULL_COUNTER_CLOCKWISE
# to cast from one side only (useful when the light sits INSIDE the shape).
occluder.occluder = poly
furniture.add_child(occluder)
```

Then enable `shadow_enabled` on the light. Design notes: give occluders *simple* polygons (a rectangle at the base of a table reads perfectly; tracing the sprite silhouette wastes performance and looks wrong for top-down perspectives), and remember the shadow direction radiates *away from the light's position*.

### Normal maps: fake relief in 2D

With a **`CanvasTexture`** wrapping your sprite art you can attach a normal map (and specular map). Lit by a `PointLight2D` with a meaningful `height`, flat pixel art gains embossed relief — surfaces facing the light brighten, opposite edges fall dark, and the light's movement makes the surface *roll*:

```gdscript
var ct := CanvasTexture.new()
ct.diffuse_texture = preload("res://art/crate.png")
ct.normal_texture = preload("res://art/crate_n.png")     # generated or hand-authored
ct.specular_shininess = 8.0
sprite.texture = ct
```

Normal maps for pixel art can be generated (Laigter, Sprite DLight and similar tools) or drawn. The effect is strongest with moving lights; for a static scene with static lights, consider baking the lighting into the art instead.

### Recipe: a warm evening in five nodes

The complete cozy-room lighting stack, combining this section with section 18 — each ingredient one node:

```
Room (Node2D)
├── CanvasModulate            color = (0.45, 0.5, 0.68)   ← dusk base
├── DirectionalLight2D        energy = 0.25, cool blue    ← moonlight wash
├── Lamp (PointLight2D)       warm, energy 1.2, shadows   ← the hero light
│   └── (texture_scale sized to pool on the desk)
├── Table
│   └── LightOccluder2D       simple base rectangle       ← one real shadow
└── Window (Sprite2D)         additive material glow      ← faked, free
```

Flicker, the detail that makes it alive — a two-line tween loop on the lamp:

```gdscript
func start_flicker(lamp: PointLight2D) -> void:
    var tween := lamp.create_tween().set_loops()
    tween.tween_property(lamp, "energy", 1.28, 0.9) \
         .set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
    tween.tween_property(lamp, "energy", 1.12, 1.1) \
         .set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
```

(Randomize the durations slightly per loop via `tween_callback` if the regularity shows.) One shadow-casting light, one shadowless directional, one fake — that budget runs everywhere, including integrated GPUs, and already reads as "atmosphere".

### Performance caveats

2D lights are per-pixel work layered onto every item they touch, and shadows add a geometry pass per light. The budget rules:

1. **Lights are a scarce resource.** A handful of shadow-casting lights is fine; dozens are not. The renderer also caps how many lights can affect a single item — overlapping many lights on one sprite silently drops the excess.
2. **Shadows cost more than lights.** Enable `shadow_enabled` only where shadows are *seen*. `SHADOW_FILTER_NONE` for many small lights; PCF13 reserved for one or two hero lights.
3. **Cull aggressively**: `range_item_cull_mask` and layer/Z ranges shrink each light's workload — and keep light off layers (UI!) where it's meaningless. Mask assignment in practice:

```gdscript
# Bit 1 = "world receives light", bit 2 = "characters receive light":
floor_sprite.light_mask = 1
character.light_mask = 1 | 2
lamp.range_item_cull_mask = 1            # lamp lights the world only
rim_light.range_item_cull_mask = 2       # rim light touches characters only
```
4. **Fake what you can.** Short-lived glows (muzzle flashes, pickups) read identically as additive sprites (section 10) at near-zero cost — no shadows, cannot darken, but often indistinguishable in motion.
5. For a desktop companion app idling on someone's second monitor, every always-on light is battery drain — gate lighting behind a quality setting. (Frame-budget methodology: [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md).)

> ⚠️ **Pitfall** — "My light does nothing": check, in order — (1) the light has a texture (`PointLight2D` without one emits nothing); (2) the target items' `light_mask` overlaps `range_item_cull_mask`; (3) the item's material isn't `LIGHT_MODE_UNSHADED`; (4) for `BLEND_MODE_ADD` on an already-bright scene, add a `CanvasModulate` so there is darkness to lift.

---

## UI theming: Theme, StyleBox and fonts

Godot's Control nodes are skinned by the **Theme** system: a resource that says, for every control type, which colors, fonts, icons, spacing constants and box styles to use. Done right, the entire application's look lives in one `.tres` file, and restyling never touches scene files.

### The six theme item types

A Theme is a table of *items*, each addressed by `(item type, theme type, name)`:

| Item type | Examples | Godot type |
|---|---|---|
| **Color** | `font_color`, `font_hover_color` | `Color` |
| **Constant** | `separation`, `margin_left`, `outline_size` | `int` |
| **Font** | `font` | `Font` |
| **Font size** | `font_size` | `int` |
| **Icon** | `checked`, `arrow` | `Texture2D` |
| **StyleBox** | `normal`, `hover`, `pressed`, `panel` | `StyleBox` |

The *theme type* is normally the control class name (`Button`, `Label`, `PanelContainer`), and child classes inherit their parents' items automatically. Which names each control consumes is listed in its class reference under "Theme Properties" — that list is the control's styling API.

### Resolution order: who wins

When a control needs, say, its `font_color`, it resolves through this chain — **first hit wins**:

```
1. Local override        control.add_theme_color_override("font_color", c)
2. The control's `theme` property … and `theme` of each ANCESTOR, walking up
   (nearest ancestor first), matching type/variation
3. Project custom theme  (Project Settings → GUI → Theme → Custom)
4. The default theme     (built-in fallback look, ThemeDB)
```

This yields the two golden rules:

- **Set the project theme once** (`gui/theme/custom`) — every Control in every scene inherits it with zero per-scene wiring.
- **Attach `theme` to a subtree root** only to make an intentionally different island (e.g. a "dark editor panel" inside a light app). Because ancestor themes cascade, a theme on a dialog's root skins the whole dialog.

Local overrides sit above everything, which makes them powerful and dangerous:

```gdscript
# One-off tweaks — a destructive-action button:
delete_btn.add_theme_color_override("font_color", Color(0.9, 0.3, 0.3))
delete_btn.add_theme_font_size_override("font_size", 13)
margin.add_theme_constant_override("margin_left", 12)

# Interrogate the resolved values (works on any control):
var c := label.get_theme_color("font_color")
var has := btn.has_theme_stylebox_override("normal")

# Undo an override:
delete_btn.remove_theme_color_override("font_color")
```

> ⚠️ **Pitfall** — Overrides applied in the editor are saved *into the scene*, invisible to the Theme resource. A project "styled" through hundreds of scattered overrides cannot be re-skinned without editing every scene — the exact failure Theme exists to prevent. Overrides are for *semantic exceptions* (this one button is dangerous), never for the default look of a control class.

### Theme type variations

The sanctioned middle ground between "all buttons look the same" and per-node overrides: define a **variation** — a named style that *inherits from* a base type — in the Theme, then opt controls into it:

```gdscript
# In the theme (editor: Manage Items → Add Type → set Base Type; or in code):
theme.add_type("AccentButton")
theme.set_type_variation("AccentButton", "Button")     # inherits all Button items
theme.set_color("font_color", "AccentButton", Color.WHITE)
theme.set_stylebox("normal", "AccentButton", accent_style)

# On any button that should use it:
buy_button.theme_type_variation = "AccentButton"
```

Variations keep the styling *in the theme* while allowing families: `AccentButton`, `DangerButton`, `TitleLabel`, `CardPanel`. If you find yourself repeating the same override on three nodes, it should be a variation.

### Building and manipulating themes in code

The theme editor is the daily driver, but the code API matters for generated themes (user-selectable accent colors, high-contrast modes) and for understanding what the editor writes:

```gdscript
# Build a minimal theme programmatically:
var theme := Theme.new()
theme.set_color("font_color", "Label", Color("e8e2d0"))
theme.set_font_size("font_size", "Label", 14)
theme.set_constant("separation", "VBoxContainer", 8)
theme.set_stylebox("panel", "PanelContainer", my_stylebox)

# Read back / introspect:
var names := theme.get_color_list("Label")          # what's defined for Labels
var types := theme.get_type_list()                  # all themed types

# Apply to a subtree at runtime (instant restyle of everything under it):
settings_root.theme = theme
```

Swapping the `theme` property on a subtree root re-resolves every control instantly — that *is* the runtime skin-switch mechanism; no per-node work needed. For **many overrides on one node**, batch them so the control re-layouts once instead of per call:

```gdscript
btn.begin_bulk_theme_override()
btn.add_theme_color_override("font_color", accent)
btn.add_theme_color_override("font_hover_color", accent.lightened(0.2))
btn.add_theme_stylebox_override("normal", accent_box)
btn.end_bulk_theme_override()
```

`ThemeDB` rounds out the API: `ThemeDB.fallback_font`, `fallback_font_size`, `fallback_stylebox` and friends expose the engine's last-resort values (used in section 6 for `draw_string`), and `ThemeDB.get_project_theme()` returns the project custom theme.

> ⚠️ **Pitfall** — Generated themes must be *complete* for the types they claim: defining only `font_color` for `Button` while a hover state relies on `font_hover_color` from a different theme in the chain gives Frankenstein styling that differs by ancestor context. When generating, copy from a complete base (`theme.merge_with()` semantics via duplicating the project theme) and override the deltas.

### StyleBox: the box model

A **StyleBox** paints a control's background box. The two workhorses:

**`StyleBoxFlat`** — vector: fills, borders, rounded corners, shadows, all resolution-independent and cheap:

```gdscript
var sb := StyleBoxFlat.new()
sb.bg_color = Color("2a2535")
sb.set_corner_radius_all(6)
sb.border_color = Color("4a4458")
sb.set_border_width_all(2)
sb.content_margin_left = 12.0      # padding between box edge and content
sb.content_margin_right = 12.0
sb.content_margin_top = 8.0
sb.content_margin_bottom = 8.0
sb.shadow_color = Color(0, 0, 0, 0.3)
sb.shadow_size = 4
sb.anti_aliasing = true            # smooth corner edges
theme.set_stylebox("panel", "PanelContainer", sb)
```

**`StyleBoxTexture`** — a nine-slice (9-patch) texture: corners stay fixed, edges stretch along one axis, the center fills. One small bitmap skins any size of panel:

```
┌───┬─────────┬───┐
│ A │    B    │ C │   corners A,C,G,I: never scaled
├───┼─────────┼───┤   edges B,H stretch horizontally; D,F vertically
│ D │    E    │ F │   center E fills both ways
├───┼─────────┼───┤
│ G │    H    │ I │
└───┴─────────┴───┘
```

```gdscript
var sbt := StyleBoxTexture.new()
sbt.texture = preload("res://assets/ui/panel_brown.png")
sbt.set_texture_margin_all(5.0)    # the 5-px slice guides that define the 9 zones
# axis_stretch_horizontal / _vertical: AXIS_STRETCH_MODE_STRETCH (default),
#   _TILE, _TILE_FIT — tile the edges instead of stretching for pixel-art borders.
```

Also in the family: `StyleBoxEmpty` (reserves content margins, draws nothing — great for invisible flat buttons) and `StyleBoxLine` (a single line, used by separators). Rule of thumb: modern flat/vector look → `StyleBoxFlat`; hand-drawn/pixel borders → `StyleBoxTexture` (Relax Room's cozy Kenney-based skin, section 19).

Controls draw *states* with different styleboxes — for `Button`: `normal`, `hover`, `pressed`, `disabled`, plus `focus` drawn *as an overlay on top* of the state box. Always style `focus` visibly if the app is keyboard-navigable.

### Fonts: crispness engineering

Godot 4 fonts are `FontFile` resources (imported TTF/OTF/WOFF2), optionally wrapped in `FontVariation` for weight/slant/spacing presets. The import settings that decide whether desktop UI text looks *professional*:

| Setting | Recommendation for desktop UI |
|---|---|
| **Antialiasing** | Grayscale (default). LCD subpixel exists but constrains layouts. |
| **Hinting** | `Light` (default) or `Normal` — snaps stems to pixels; without it small text goes mushy. |
| **Subpixel positioning** | Auto — disables itself at small sizes where it would blur hinted glyphs. |
| **Multichannel signed distance field (MSDF)** | Enable when text scales dynamically (zooming UI): one import stays sharp at any size, at the cost of slightly heavier rendering and no hinting. |
| **Fallbacks** | Add fonts covering scripts/emoji your primary font lacks; missing-glyph boxes (▯) in user text mean an incomplete fallback chain. |
| **Oversampling** | Handled automatically by the engine for scaled UI — one reason `canvas_items` stretch keeps text sharp. |

```gdscript
# Runtime access to the theme's font machinery:
var font: Font = ThemeDB.fallback_font          # engine's last-resort font
var fv := FontVariation.new()
fv.base_font = preload("res://assets/fonts/inter.ttf")
fv.variation_embolden = 0.4                     # fake semibold when no real weight exists
theme.set_font("font", "TitleLabel", fv)
```

For pixel-art aesthetics, use an actual bitmap pixel font at its native size (no AA, no hinting debates) — Relax Room pairs a pixel font for in-world text with a hinted vector font for menus.

**`LabelSettings`** deserves a mention as the middle path for display text: a small resource bundling font, size, color, outline and shadow for `Label`s specifically. Where a Theme styles *classes* of controls, one `LabelSettings` resource styles a *family of labels* (all damage numbers, all card titles) and is shared by reference — edit the resource, every label updates:

```gdscript
var ls := LabelSettings.new()
ls.font = preload("res://assets/fonts/pixel.ttf")
ls.font_size = 16
ls.font_color = Color("e8e2d0")
ls.outline_size = 4
ls.outline_color = Color(0, 0, 0, 0.8)
title_label.label_settings = ls        # takes precedence over theme font items
```

Use it for decorative/display text; keep *interface* text (buttons, menus) in the Theme so it restyles with the skin.

### Scaling UI for DPI

Theme metrics are authored in design-resolution pixels; the stretch system (section 9) scales them with everything else, and `Window.content_scale_factor` provides the global accessibility knob. Two extra theme-level tools:

- `Theme.default_base_scale` — declares the scale the theme was authored at; controls use it to scale constants/margins coherently.
- Prefer *even* corner radii, border widths and margins — odd values land on half-pixels at 150 % scale and look soft.

> ✅ **Best practice** — Build the theme in this order: (1) project-wide Theme with the app's base look per control type; (2) type variations for every recurring family; (3) local overrides only for one-off semantics. Then audit: any override that appears twice becomes a variation; any variation used everywhere becomes the base style.

---

## Environment and post-processing in 2D

Post-processing — effects applied to the *rendered image* rather than to individual items — is mostly a 3D story in Godot, but two pieces matter enormously for 2D apps: **glow** via `WorldEnvironment`, and the humble **`CanvasModulate`** for global tinting.

### CanvasModulate: whole-canvas tint

A `CanvasModulate` node multiplies **every CanvasItem in its canvas** by its `color`. One node, one property — and it is the backbone of day/night cycles and mood shifts:

```gdscript
# Day-night: tween the whole world's tint. UI in CanvasLayers is unaffected
# (separate canvas) — exactly what you want.
@onready var canvas_mod: CanvasModulate = $CanvasModulate

const DAY := Color(1.0, 1.0, 1.0)
const DUSK := Color(1.0, 0.75, 0.6)
const NIGHT := Color(0.35, 0.4, 0.6)

func set_time_of_day(target: Color, duration := 3.0) -> void:
    var tween := create_tween()
    tween.tween_property(canvas_mod, "color", target, duration)
```

Rules: only **one visible `CanvasModulate` per canvas** is honored (the engine warns otherwise); it affects the world canvas it lives in, so UI on `CanvasLayer`s escapes automatically; and it *multiplies*, so it can only darken/tint — brightening beyond the art requires lights (section 16) or glow (below).

`CanvasModulate` + 2D lights is the classic night formula: darken the canvas to ~30-40 % blue-gray, then punch holes of warmth with `PointLight2D`s. Each ingredient is trivial; the combination sells the scene.

### 2D glow via WorldEnvironment

Glow (bloom) makes bright pixels bleed light. In 2D it requires two prerequisites, both frequently missed:

1. **HDR 2D**: enable `rendering/viewport/hdr_2d` in Project Settings (Viewport section). Without it the 2D canvas renders in 8-bit and nothing exceeds 1.0, so "bright" doesn't exist and the glow threshold never trips.
2. **Forward+ or Mobile renderer.** The Compatibility (GL) renderer does not support 2D glow.

Then add a `WorldEnvironment` node with an `Environment` resource:

```gdscript
var env := Environment.new()
env.glow_enabled = true
env.glow_intensity = 0.6
env.glow_strength = 1.1
env.glow_bloom = 0.1
env.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
env.glow_hdr_threshold = 1.0        # pixels brighter than this bloom
$WorldEnvironment.environment = env
```

Feeding the glow: anything pushed above 1.0 — overbright `modulate` (`Color(2.0, 1.6, 1.2)` on a lamp sprite), additive-blend overlaps (section 10), high-`energy` lights, or shader output. Because the threshold is a *brightness gate*, you sculpt which pixels glow by controlling which pixels exceed it — a neon sign at modulate 2.5 blooms; the wall behind it at 1.0 stays flat.

> ⚠️ **Pitfall** — Glow is a full-screen post effect: it applies to the whole viewport, UI included, unless the UI lives in a `Window`/separate viewport or you keep UI colors safely below the threshold. Test glowing screens with every panel open — a white panel at 1.0 with `glow_hdr_threshold = 0.95` will haze the entire interface.

> ✅ **Best practice** — For a soft "cozy warm bloom" (the Relax Room look), keep `glow_intensity` low (0.3-0.7) and drive glow from a *few deliberate* overbright emitters (lamp cores, fireflies, the moon) rather than lowering the threshold globally. Restraint reads as atmosphere; ubiquity reads as smeared vaseline.

### Adjustments: the cheap "filters" system

Other Environment features (tonemap, adjustments, color correction) also apply to the 2D viewport when HDR 2D is active. The adjustments block alone implements a screenshot-filter feature in a dozen lines:

```gdscript
var env: Environment = $WorldEnvironment.environment
env.adjustment_enabled = true

const FILTERS := {
    "none":    { "brightness": 1.0, "contrast": 1.0, "saturation": 1.0 },
    "warm":    { "brightness": 1.05, "contrast": 1.05, "saturation": 1.15 },
    "vintage": { "brightness": 1.0, "contrast": 0.92, "saturation": 0.6 },
    "mono":    { "brightness": 1.0, "contrast": 1.1, "saturation": 0.0 },
}

func apply_filter(name: String) -> void:
    var f: Dictionary = FILTERS[name]
    var tween := create_tween().set_parallel(true)
    tween.tween_property(env, "adjustment_brightness", f.brightness, 0.4)
    tween.tween_property(env, "adjustment_contrast", f.contrast, 0.4)
    tween.tween_property(env, "adjustment_saturation", f.saturation, 0.4)
```

(Environment properties tween like any others — section 12's machinery applies everywhere.) A `adjustment_color_correction` LUT texture takes this further into full color grading. For anything fancier (vignette, chromatic aberration, scanlines), the 2D-native route is a full-screen shader on a `ColorRect`/`BackBufferCopy` — see [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md).

---

## Case study: Relax Room rendering conventions

> **Case study.** This section documents how the concepts of this module are applied in the course's running project, *Relax Room* — a 2D desktop companion app (1280×720 logical resolution, pixel-art style, isometric-ish room view). File paths and line references point into the project repository; keep them in sync when refactoring. See [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) for the project's overall architecture.

### Project rendering constants

The authoritative table of rendering values. Any literal duplicating one of these in code is a refactoring target:

| Constant | Value | File | Description |
|---|---|---|---|
| Viewport | 1280 × 720 | `project.godot` | Logical design resolution |
| Stretch mode | `canvas_items` | `project.godot` | Scale to window, vectors re-rasterized (section 9) |
| Clear color | `#1f1c2e` | `project.godot` | Dark violet background |
| Default texture filter | 0 (Nearest) | `project.godot` | Crisp pixel art project-wide |
| `OVERLAY_ALPHA` | 0.6 | `main.gd:5` | Room theme overlay transparency |
| `CELL_SIZE` | 64 | `room_grid.gd:5` | Placement grid cell, px |
| `ROOM_LEFT` | 280 | `room_grid.gd:9` | Room left bound, px |
| `ROOM_RIGHT` | 1000 | `room_grid.gd:10` | Room right bound, px |
| `ROOM_BOTTOM` | 670 | `room_grid.gd:11` | Room bottom bound, px |
| `WALL_ZONE_RATIO` | 0.4 | `room_grid.gd:7` | Top 40 % = wall, bottom 60 % = floor |
| `PARALLAX_STRENGTH` | 8.0 | `window_background.gd:5` | Max parallax shift, px |
| `SCALE_FACTOR` | 1.38 | `window_background.gd:6` | 1280 / 928 — background art fills viewport |
| `PANEL_TWEEN_DURATION` | 0.3 | `constants.gd` | Panel fade duration, s |
| `FADE_DURATION` | 0.5 | `constants.gd` | Scene fade duration, s |
| Camera zoom | 3.6 | camera setup | Pixel-art upscale factor |
| Character scale | 3.0 (in-game) / 4.0 (menu) | `*.tscn`, `menu_character.gd` | Sprite upscaling |
| Furniture scale | 3.0 | `decorations.json` | Furniture sprite scale |
| Plants scale | 6.0 | `decorations.json` | Plant sprite scale |
| Pet scale | 4.0 | `decorations.json` | Pet sprite scale |

### Z-layer conventions

The project's draw-order plan, applying the decision table of section 4 — one glance answers every "what goes on top" question:

| Stratum | Mechanism | Value | Contents |
|---|---|---|---|
| Backdrop | `z_index` | −1 | Window backdrop, distant scenery |
| World | implicit canvas (layer 0) | z 0 | Room, furniture, character, pet — Y-sorted where depth-competing |
| World accents | `z_index` | 1 … 10 | Selection highlights (relative Z +1), airborne pet |
| Auth screen | `z_index` | 100 | Above all gameplay visuals, still in the world canvas |
| UI | `CanvasLayer` | layer 10 | HUD, panels, menus (camera-independent) |
| Popups | `CanvasLayer` | layer 100 | Decoration popups, tooltips, toasts |

Notes: gameplay never touches Z values above 100; the two CanvasLayers are the only layers in the project; and per section 3, any new Z literal in code must reference this table (via constants) or be rejected in review.

### Room theming: ColorRect overlays

`scripts/main.gd` (lines 50-65) applies each room's color theme not by re-rendering textures but by compositing two translucent `ColorRect`s over the art — the cheap-overlay pattern from section 11:

```gdscript
const OVERLAY_ALPHA := 0.6

func _apply_theme(room_id: String, theme_id: String) -> void:
    var colors := GameManager.get_theme_colors(room_id, theme_id)

    # Wall: top 40% of the screen
    var wall_color := Color(wall_hex)     # e.g. Color("2a2535") → dark violet
    wall_color.a = OVERLAY_ALPHA          # 60% opacity
    _wall_rect.color = wall_color

    # Floor: bottom 60%
    var floor_color := Color(floor_hex)
    floor_color.a = OVERLAY_ALPHA
    _floor_rect.color = floor_color

    # Baseboard: 10% lighter than the wall
    _baseboard.color = Color(wall_hex).lightened(0.1)
```

How `Color()` reads hex strings: `Color("2a2535")` → R = 0.165, G = 0.145, B = 0.208 (dark violet); `Color("3d3347")` → a slightly lighter violet. Zone layout at design resolution:

```
0px   ┌─────────────────────────┐
      │          WALL            │  ← WallRect (40%)
      │    (wall_color, a=0.6)   │
288px ├─────────────────────────┤  ← Baseboard (1px)
      │          FLOOR           │  ← FloorRect (60%)
      │   (floor_color, a=0.6)   │
720px └─────────────────────────┘
      0px                     1280px
```

### Menu parallax: mouse tracking over 8 layers

`scripts/rooms/window_background.gd` implements the manual-parallax pattern of section 15 — no camera in the menu, so the driver signal is the mouse:

```gdscript
# Lines 5-7 — constants
const PARALLAX_STRENGTH := 8.0    # max shift in pixels
const SCALE_FACTOR := 1.38        # 1280 / 928, background fills the viewport

# Lines 44-54 — layer construction (in _build_layers)
for i in valid_count:
    var sprite := Sprite2D.new()
    sprite.texture = valid_textures[i]
    sprite.centered = false
    sprite.scale = Vector2(SCALE_FACTOR, SCALE_FACTOR)
    sprite.position.y = -505.0
    sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
    _parallax_factors.append(float(i) / float(valid_count))  # 0.0 → 1.0

# Lines 57-71 — per-frame parallax update
func _update_parallax() -> void:
    var mouse := get_viewport().get_mouse_position()
    var center := vp_size * 0.5
    var offset := (mouse - center) / center    # normalized −1.0 … +1.0

    for i in _layers.size():
        var shift := offset * PARALLAX_STRENGTH * _parallax_factors[i]
        _layers[i].position.x = -shift.x
```

Depth reading: layer 0 (far forest) has factor 0.0 → static; layer 4 (middle) factor 0.5 → shifts up to 4 px; layer 7 (foreground) factor 1.0 → full 8 px. Distant trees stand still while near ones sweep past — depth for eight sprites and one loop. (If the menu ever gains a scrolling camera, this migrates to `Parallax2D` nodes with `scroll_scale = factor`.)

### Placement grid: custom _draw()

`scripts/rooms/room_grid.gd` draws the decoration-placement guide grid with `_draw()` — the canonical "many simple shapes, one node" case from section 6:

```gdscript
const CELL_SIZE := 64                            # 64 px per cell
const GRID_COLOR := Color(1.0, 1.0, 1.0, 0.12)   # white at 12% opacity
const WALL_ZONE_RATIO := 0.4                     # top 40% = wall
const ROOM_LEFT := 280.0
const ROOM_RIGHT := 1000.0
const ROOM_BOTTOM := 670.0

func _draw() -> void:
    if not visible:
        return
    var floor_top := vp.y * WALL_ZONE_RATIO      # 720 * 0.4 = 288 px

    var x := ROOM_LEFT                           # vertical lines: 280 → 1000
    while x <= ROOM_RIGHT:
        draw_line(Vector2(x, floor_top), Vector2(x, ROOM_BOTTOM), GRID_COLOR)
        x += CELL_SIZE

    var y := floor_top                           # horizontal lines: 288 → 670
    while y <= ROOM_BOTTOM:
        draw_line(Vector2(ROOM_LEFT, y), Vector2(ROOM_RIGHT, y), GRID_COLOR)
        y += CELL_SIZE
```

Visibility is signal-driven, with the redraw queued on change:

```gdscript
func _on_decoration_mode_changed(active: bool) -> void:
    visible = active
    queue_redraw()
```

The grid exists only in "edit mode": zero cost otherwise (hidden items emit no commands — section 2).

### Panel animations: fade with Tween

`scripts/ui/panel_manager.gd` opens and closes UI panels with the fade pattern of section 11, storing the tween per the kill discipline of section 14:

```gdscript
# Open: fade in from transparent
_current_panel.modulate.a = 0.0               # start invisible
_ui_layer.add_child(_current_panel)           # attach to the UI CanvasLayer (10)
_tween = create_tween()
_tween.tween_property(_current_panel, "modulate:a", 1.0, 0.3)   # 0→1 in 0.3 s

# Close: fade out, then free
_tween = create_tween()
_tween.tween_property(closing_panel, "modulate:a", 0.0, 0.3)    # 1→0 in 0.3 s
_tween.tween_callback(closing_panel.queue_free)                 # destroy after fade
```

`"modulate:a"` is the alpha sub-property path from section 12 — the RGB channels stay free for state tinting.

**Audit lessons (N-Q1, N-Q2).** Two findings from the project's tween audit are now house rules:

1. *Unstored tween*: a local `var tween := create_tween()` cannot be killed early when the user closes a panel mid-fade — store tweens that anyone might interrupt.
2. *Double call*: calling `walk_in()` twice spawned two competing tweens. Fix: the member-variable kill pattern —

```gdscript
var _tween: Tween

func fade_in() -> void:
    if _tween:
        _tween.kill()            # kill the previous tween first
    _tween = create_tween()
    _tween.tween_property(self, "modulate:a", 1.0, 0.3)
```

### Scene transition: loading-screen intro sequence

`scripts/menu/main_menu.gd` choreographs the menu intro as one sequential tween — interval, property, callbacks (section 12's tweener types in one chain):

```gdscript
_intro_tween = create_tween()
_intro_tween.tween_interval(0.4)             # 1. hold the loading screen 0.4 s
_intro_tween.tween_property(                 # 2. fade it out
    _loading_screen, "modulate:a", 0.0, 0.5)  #    1.0 → 0.0 in 0.5 s
_intro_tween.tween_callback(                 # 3. hide it
    _loading_screen.set_visible.bind(false))
_intro_tween.tween_callback(                 # 4. start the character walk-in
    _menu_character.walk_in)

# Character walk-in (menu_character.gd, lines 61-65):
var tween := create_tween()
tween.set_ease(Tween.EASE_OUT)               # natural deceleration
tween.set_trans(Tween.TRANS_QUAD)            # quad curve (the section-13 default pair)
tween.tween_property(self, "position",
    Vector2(640, 530), 2.0)                  # from (−100, 530) to (640, 530) in 2 s
tween.tween_callback(_on_walk_finished)      # signal completion
```

### Decoration popups: dynamic CanvasLayer + coordinate conversion

`scripts/rooms/decoration_system.gd` (lines 80-137) spawns interactive popups above furniture. Two module concepts meet: hard layer separation (section 4) and world→viewport conversion (section 5):

```gdscript
# Layer 100 = above everything, including the UI layer at 10
_popup_layer = CanvasLayer.new()
_popup_layer.layer = 100
get_tree().root.add_child(_popup_layer)

# World → screen conversion
var screen_pos := get_canvas_transform() * global_position
#                  canvas (camera) transform  world position
# get_canvas_transform() folds in: camera zoom, offset, viewport stretch

# Center the popup above the decoration
_popup.position = Vector2(
    screen_pos.x + tex_size.x * canvas_scale.x * 0.5 - 50,   # centered
    screen_pos.y - 36)                                       # 36 px above
```

*Why a CanvasLayer for popups?* The popup's `Button`s must receive GUI input cleanly. In the world canvas, clicks could be intercepted by the `DropZone` (`mouse_filter = PASS`); on layer 100 the popup sits above that entire input situation — consistent with the section 3 warning that Control input follows the Control tree, not z_index.

### cozy_theme.tres: the project theme

`assets/ui/cozy_theme.tres` skins every Control (section 17's architecture, StyleBoxTexture flavor). Source art: Kenney Pixel UI Pack, "Ancient" style (beige/brown). Structure:

```
Button:
  ├── normal  → StyleBoxTexture (brown, 9-slice, 5 px margins)
  ├── hover   → StyleBoxTexture (tan, 9-slice)
  └── pressed → StyleBoxTexture (grey, 9-slice)

PanelContainer:
  └── panel   → StyleBoxTexture (brown background, 9-slice)

HSlider:
  ├── slider  → StyleBoxTexture (grey, 9-slice)
  └── grabber → StyleBoxTexture (tan, 9-slice)

Label:
  └── font_color → Color (tan/cream)
```

Assigned once as the project theme (`gui/theme/custom`). Per-node overrides are used sparingly and semantically, e.g.:

```gdscript
delete_btn.add_theme_color_override("font_color", Color(0.9, 0.3, 0.3))
label.add_theme_font_size_override("font_size", 13)
margin.add_theme_constant_override("margin_left", 12)
```

Per section 17: the recurring ones (danger buttons appear in three panels) are scheduled to become theme type variations (`DangerButton`) in the next UI pass.

### Camera and pixel-art scale

The room camera applies the pixel-art upscale (sections 8-9):

```gdscript
var camera := Camera2D.new()
camera.zoom = Vector2(3.6, 3.6)          # 3.6× upscale for pixel art
camera.position_smoothing_enabled = true
camera.position_smoothing_speed = 10.0
```

3.6 is deliberately non-integer: at 1280×720 with Nearest filtering the artifacts are acceptable, and the framing wins. If shimmer ever becomes objectionable, the documented plan is the hybrid-resolution SubViewport pattern from section 9 (native-res world render, integer upscale, UI outside).

### Module-to-project map

Where each concept of this module is exercised in the codebase — the reverse index for code reading:

| Module concept | Section | Project location |
|---|---|---|
| Z conventions & CanvasLayer strata | 3-4 | layer table above; `decoration_system.gd` (layer 100), UI layer (10) |
| Y-sort | 4 | room world parent (furniture/character/pet interleaving) |
| World → screen conversion | 5 | `decoration_system.gd:80-137` popup anchoring |
| `_draw()` + `queue_redraw()` | 6-7 | `room_grid.gd` placement grid |
| Stretch configuration | 9 | `project.godot` (1280×720, `canvas_items`) |
| Modulate fades & kill discipline | 11, 14 | `panel_manager.gd` open/close |
| Ghost preview modulate | 11 | decoration placement preview |
| Tween sequencing (interval/property/callback) | 12-13 | `main_menu.gd` intro; `menu_character.gd` walk-in |
| Manual parallax | 15 | `window_background.gd` (8 layers, mouse-driven) |
| Theme + StyleBoxTexture 9-slice | 17 | `assets/ui/cozy_theme.tres` |
| Overlay tinting (ColorRect) | 11, 19 | `main.gd:50-65` room themes |

---

## Best practices

**Draw order**

1. **Pick the weakest mechanism that works** (section 4's table): tree order → Y-sort → z_index → CanvasLayer. Escalating to CanvasLayer for a problem tree order solves buys complexity for nothing.
2. **Write the layer plan down** as a table of named constants; treat Z literals in code as review flags. Never use `z_index = 4096` as a hammer.
3. **Y-sorted entities share one Y-sorted parent, with origins at their ground contact point.** Both halves of that sentence are load-bearing.
4. **z_index for world layering, CanvasLayer for UI strata** — z_index affects Control drawing but not Control input, so UI stacking belongs to tree order and layers.

**Coordinates**

5. **Name the space of every position variable** (`world_pos`, `vp_pos`, `local_pos`). Half of all coordinate bugs are two spaces meeting in one variable name.
6. **`get_global_mouse_position()` for world logic, `Viewport.get_mouse_position()` for CanvasLayer UI** — never interchangeable once a camera or stretch exists.
7. **Converting back = `affine_inverse()`** of the forward transform; prefer `to_local`/`to_global`/`get_global_transform_with_canvas()` over hand-rolled math.

**Custom drawing**

8. **`_draw()` renders state; `_process()` updates state.** Keep draw functions pure, and `queue_redraw()` only on change (dirty-flag pattern).
9. **Batch draw calls**: `draw_polyline`/`draw_multiline`/`draw_polygon` over loops of tiny calls; hairline width `-1.0` for zoom-independent debug lines.

**Viewports & scaling**

10. **`canvas_items` stretch + `expand` aspect** is the desktop-app default; test window resizing from week one.
11. **SubViewports don't have to re-render every frame** — schedule with `render_target_update_mode`, and `await RenderingServer.frame_post_draw` before any capture.

**Tweens**

12. **Bound tweens by default** (`create_tween()` on the animated node); `get_tree().create_tween()` only with a written justification.
13. **Kill before recreate** for any re-triggerable animation; store any tween someone might interrupt; `_exit_tree()` kills tweens that touch other nodes.
14. **Standardize motion**: shared duration constants and one or two trans/ease pairs project-wide (`TRANS_QUAD`/`EASE_OUT` is the workhorse).
15. **Runtime-computed values → Tween; authored choreography → AnimationPlayer.**

**Presentation**

16. **One Theme resource, variations for families, overrides for one-off semantics** — in that order; audit overrides regularly.
17. **Modulate is owned by one system per node** (or partitioned by channel: RGB vs `:a`); use `CanvasGroup` when a subtree must fade as one image.
18. **Fake lights with additive sprites when shadows aren't needed**; real 2D lights and glow are quality-setting material for an always-running desktop app.

---

## Common errors & troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Node invisible though `visible = true` | Ancestor hidden; `modulate.a` ≈ 0 somewhere up the tree; covered by higher layer/Z | Walk ancestors checking `visible` and `modulate`; check CanvasLayer stack |
| `z_index` "does nothing" | Other item is in a higher `CanvasLayer`; or z clamped (−4096…4096); or comparing across viewports | Layers beat Z always — restructure layers, not Z |
| Y-sort ignored | Movers don't share a Y-sorted parent; origin at sprite center, not feet; stray non-zero `z_index` on one item | Common Y-sorted ancestor; origins at ground contact; zero the Z |
| Child won't draw behind parent | Expected containment that doesn't exist | `show_behind_parent = true`, or negative relative `z_index` |
| Clicks land beside buttons | UI in world canvas under camera zoom; or stretch mismatch | Move UI to a `CanvasLayer`; verify stretch settings |
| Click "through" an overlay onto world UI | Control input follows tree, not Z | Put overlay in higher CanvasLayer; set `mouse_filter` deliberately |
| `_draw()` never called | Node hidden; or you expected per-frame calls | It runs on invalidation only — `queue_redraw()` on data change |
| Drawing frozen/stale | Data changed without `queue_redraw()` | Call it in setters (dirty-flag pattern) |
| "Drawing is only allowed inside NOTIFICATION_DRAW" error | `draw_*` called outside `_draw()` | Move calls into `_draw()`; trigger via `queue_redraw()` |
| Debug lines fat when zoomed | Positive width is in local units | Hairline width `-1.0` for screen-constant thickness |
| SubViewport texture empty/black | Captured before first render; `UPDATE_DISABLED`; ViewportTexture node path broken | `await RenderingServer.frame_post_draw`; check update mode; assign `get_texture()` in code |
| Minimap camera doesn't move the game | Camera drives only its own viewport | Put the camera in the intended viewport; share `world_2d` for same-world views |
| Pixel art shimmers when window resizes | Fractional scaling of nearest-filtered art | `stretch/scale_mode = integer`, or SubViewport native-res + integer upscale |
| Tween stutters / snaps mid-animation | Two tweens fighting over one property | Member-var kill pattern: `kill()` before recreate |
| "Tween started with no Tweeners" error | A code path created a tween but appended nothing | Ensure every branch adds a tweener or don't create the tween |
| Code after `await tween.finished` never runs | Tween was killed — `finished` never fires on kill | Use `tween_callback`, or make the killer unwind the awaiter |
| Tween errors about freed object | Unbound tween (or tween on another node) outlived the target | Bind to the target (`target.create_tween()`); kill in `_exit_tree()` |
| Loop animation never stops | Infinite `set_loops()` tween not stored | Store the reference; `kill()` in the stop path |
| Panel fades but children pop | Children had own alpha; or fade fought state-tint system | One modulate owner per node; `CanvasGroup` for flattened fades |
| Overlapping sprites show seams when parent fades | Per-child alpha blending | `CanvasGroup` parent |
| `PointLight2D` has no effect | No texture; `light_mask` mismatch; `UNSHADED` material; scene already at full brightness | Assign texture; align masks; check material; add `CanvasModulate` darkness |
| Glow does nothing in 2D | HDR 2D off, or Compatibility renderer | Enable `rendering/viewport/hdr_2d`; use Forward+/Mobile |
| Night tint darkens the UI too | UI in the same canvas as `CanvasModulate` | UI belongs in a `CanvasLayer` (separate canvas) |
| Parallax layers show seams | `repeat_size` ≠ scaled texture period | `repeat_size = texture_size * sprite.scale` |
| Theme edits don't affect a control | Local override wins; or control uses a variation/different type | Remove overrides; check `theme_type_variation` and the control's theme-property names |
| Text blurry at small sizes | Hinting off / MSDF at tiny sizes / non-integer final scale | Hinting Light/Normal; avoid MSDF for fixed small text; integer-friendly metrics |
| Glyphs show as ▯ boxes | Font lacks those characters | Add fallback fonts in the font resource |
| Masked child still clickable outside mask | `clip_children` clips rendering only | `Control.clip_contents` or restructure input areas |
| Screenshot black on first frame | Captured before first render completed | `await RenderingServer.frame_post_draw` before `get_image()` |
| Dragged object drifts under camera zoom | Accumulating `event.relative` in world space | Recompute from `get_global_mouse_position()` per frame |
| Desktop overlay window shows opaque rectangle | Transparency chain incomplete | Enable window transparent + per-pixel allowed + viewport transparent_bg |
| Whole UI hazes when glow enabled | Glow threshold below UI brightness | Raise `glow_hdr_threshold` ≥ 1.0; drive glow via overbright emitters only |
| Frame rate sinks with many lights | Per-item light cost, shadow passes | Fewer shadow casters, `SHADOW_FILTER_NONE`, cull masks, fake with additive sprites |

---

## Exercises

Work in a scratch project pinned to Godot 4.5. Each lab lists acceptance criteria (AC) and a stretch goal. Labs 2, 4 and 6 extend this module's original exercise set (Y-sort isometric, `_draw()` health bar, tween chaining); the self-check quiz replaces the old auto-evaluation list.

### Lab 1 — The draw-order gauntlet *(sections 3-4)*

Build a scene that demonstrates every rule of the decision table: two sibling sprites (tree order), a `z_index` inversion, a relative-vs-absolute Z pair under a Z-raised parent, a `show_behind_parent` shadow, and a `CanvasLayer` that beats `z_index = 4096`.
**AC:** a Label annotates each pair with the rule that decides it; toggling one exported bool per pair flips the order live; predictions written before running match the result.
**Stretch:** add a "quiz mode" script that randomizes the properties and asks you to predict the order before revealing it.

### Lab 2 — Isometric Y-sort with a flying pet *(section 4, [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md))*

N characters (≥ 6) walking randomly around furniture on a Y-sorted parent, origins at feet.
**AC:** no depth popping at any overlap; one character can "jump" — while airborne it renders above all furniture (`z_index` bump) and re-enters depth competition on landing; a `TileMapLayer` floor participates via nested Y-sort.
**Stretch:** reproduce a *broken* version (origins at sprite centers) side by side and screenshot the difference for your notes.

### Lab 3 — Coordinate-space instrument panel *(section 5)*

A HUD (CanvasLayer) shows, live: `get_global_mouse_position()`, `get_viewport().get_mouse_position()`, the hovered node's `get_local_mouse_position()`, and the camera's `canvas_transform.origin`, while you pan/zoom a `Camera2D`.
**AC:** a marker placed with the *world* mouse position stays glued under the cursor at any zoom; a second marker placed with the *viewport* position visibly drifts — and you can explain why in one sentence each.
**Stretch:** anchor a CanvasLayer label over a moving world node via `get_global_transform_with_canvas()`, correct at every zoom level.

### Lab 4 — `_draw()` health bar and radial timer *(sections 6-7)*

Implement a gradient health bar (`draw_rect` + `draw_polygon` per-vertex colors) and the `RadialTimer` ring, both redrawing only on change.
**AC:** a print counter inside `_draw()` proves zero redraws while values are static; the bar animates smoothly when driven by `tween_method`; hairline outlines stay 1 px at camera zoom 0.5× and 4×.
**Stretch:** a `DebugDraw` autoload overlay (velocity vectors for 100 moving nodes) with a measured frame-time budget under 0.5 ms script time.

### Lab 5 — Minimap and photo mode *(section 8)*

A SubViewport minimap sharing `world_2d` with the main scene (second camera, 0.1 zoom), plus a "photo" button capturing the room to PNG at exactly 1280×720.
**AC:** minimap updates live in a corner `TextureRect`; photo file opens correctly in an image viewer; capture waits for `RenderingServer.frame_post_draw` (no black frames, tested by capturing on the first frame after startup).
**Stretch:** an in-world "security monitor" — a second SubViewport rendering an *isolated* world (own `world_2d`) displayed on a screen sprite in the main room.

### Lab 6 — Tween choreography: staggered menu *(sections 12-14)*

A vertical menu whose items fly in staggered (delay `i * 0.06`), each moving and fading in parallel; opening while it is already animating must not glitch.
**AC:** rapid open/close spam never stutters or leaves ghosts (kill-before-recreate verified by logging tween kills); the sequence uses `parallel()`, `set_delay`, `chain()` and at least three trans/ease pairs from the section 13 matrix, each justified in a comment.
**Stretch:** package the per-item animation as a subtween via `tween_subtween()` (4.4+) and reuse it in a second menu.

### Lab 7 — Cozy-corner lighting *(sections 16, 18)*

A dark room (`CanvasModulate` ~`Color(0.35, 0.4, 0.6)`), a warm `PointLight2D` desk lamp with an occluding table casting a soft shadow, and a moon `DirectionalLight2D` at low energy.
**AC:** UI on a CanvasLayer is provably unaffected by the night tint; toggling the lamp crossfades its `energy` with a tween; shadow filter compared (`NONE` vs `PCF13`) with a screenshot pair and a one-line verdict.
**Stretch:** enable HDR 2D + `WorldEnvironment` glow and make *only* the lamp core bloom (overbright modulate), with a "quality: low" toggle that disables lights and glow entirely.

### Lab 8 — Theme from scratch *(section 17)*

Reskin a settings dialog (buttons, slider, panel, labels) with one Theme: `StyleBoxFlat` styles for all Button states + focus, a `DangerButton` type variation, and a font with proper hinting.
**AC:** deleting every local override from the scene changes nothing visually (all styling lives in the theme); keyboard focus is clearly visible on every control; the dialog survives `content_scale_factor = 1.5` with crisp text and unbroken layout.
**Stretch:** a second Theme resource ("high contrast") swappable at runtime by reassigning the subtree root's `theme`, animated with a 0.2 s full-screen crossfade.

### Lab 9 — Parallax window, twice *(section 15)*

Build the same 5-layer forest-through-a-window scene both ways: (a) `Parallax2D` nodes with `scroll_scale` factors driven by a scrolling `Camera2D`; (b) manual mouse-tracking parallax (no camera), Relax Room style.
**AC:** version (a) scrolls seamlessly forever via `repeat_size` with no visible seams (repeat computed from scaled texture width); version (b) shifts layers proportionally to normalized mouse offset with factors derived from layer index; a written 3-line comparison states when each approach applies.
**Stretch:** add `autoscroll` drifting clouds to (a), and to (b) an `ignore_camera_scroll`-based hybrid: `Parallax2D` nodes whose `screen_offset` you drive from the mouse — engine repeat machinery, manual driver.

### Self-check quiz

Answer from memory, then verify against the sections:

1. Two overlapping sprites, one at `z_index = 3` in `CanvasLayer` 0, one at `z_index = 0` in layer 1 — who wins, and why is it not close?
2. When is `get_global_mouse_position()` equal to `get_viewport().get_mouse_position()` — and which two features break the equality?
3. `_draw()`: exactly when does the engine call it, and what are the three costs in its cost model?
4. Why does `await tween.finished` hang forever after `kill()`, and what are the two structural fixes?
5. Which four properties would you check, in order, when a `PointLight2D` appears to do nothing?
6. Why does a fading parent with overlapping semi-transparent children show seams, and which node fixes it?
7. `stop()` vs `kill()` on a Tween — state after each, and one bug each causes when misused?
8. Your pixel-art game shimmers on resize under `canvas_items` stretch — name two fixes at different engineering costs.

---

## Further reading

Official documentation first — every API in this module links from these pages:

- [2D coordinate systems and 2D transforms — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/2d/2d_transforms.html) — the transform chain of section 5, from the source; short and canonical.
- [Custom drawing in 2D — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/2d/custom_drawing_in_2d.html) — the `_draw()` tutorial: lifecycle, all primitives, the arc example.
- [CanvasItem — class reference](https://docs.godotengine.org/en/stable/classes/class_canvasitem.html) — the property table of section 2 in full, including every `draw_*` signature.
- [Viewports — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/rendering/viewports.html) — SubViewport, render targets, worlds, capture; pairs with the [Viewport class reference](https://docs.godotengine.org/en/stable/classes/class_viewport.html).
- [Multiple resolutions — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/rendering/multiple_resolutions.html) — the stretch system decision guide behind section 9; read before shipping any resizable window.
- [Tween — class reference](https://docs.godotengine.org/en/stable/classes/class_tween.html) — the definitive tweener/ease/trans reference; the intro paragraphs are a tutorial in disguise.
- [Parallax2D — class reference](https://docs.godotengine.org/en/stable/classes/class_parallax2d.html) — all section 15 properties; note the 4.3+ availability.
- [2D lights and shadows — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/2d/2d_lights_and_shadows.html) — lighting setup, shadow filters, normal maps via `CanvasTexture`, performance notes.
- [Introduction to GUI skinning — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/ui/gui_skinning.html) — the Theme architecture and lookup order; continue with [Using the theme editor](https://docs.godotengine.org/en/stable/tutorials/ui/gui_using_theme_editor.html).
- [Environment and post-processing — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/3d/environment_and_post_processing.html) — glow parameters (3D-focused; the 2D notes of section 18 tell you which parts apply with HDR 2D).
- [Camera2D — class reference](https://docs.godotengine.org/en/stable/classes/class_camera2d.html) — zoom, smoothing, limits; the camera side of sections 5 and 19.
- [GDQuest — Godot tutorials](https://www.gdquest.com/) — high-quality free/paid Godot 4 courses; their tween and juice tutorials are excellent applied follow-ups to sections 12-14.

Sibling modules: [SCENES_AND_NODES.md](SCENES_AND_NODES.md) · [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) · [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md) · [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md) · [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md) · [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) · [VISUAL_SYSTEMS_SUMMARY.md](VISUAL_SYSTEMS_SUMMARY.md) · course glossary: [00-GLOSSARY.md](00-GLOSSARY.md).

---

## Glossary

| Term | Definition |
|---|---|
| **CanvasItem** | Abstract base of all 2D drawable nodes (`Node2D`, `Control`); owns visibility, modulate, Z, materials and the `_draw()` API. |
| **CanvasLayer** | Rendering bracket with its own transform; its `layer` value orders it against other layers and always beats `z_index`. |
| **z_index** | Integer draw priority (−4096…4096) within a canvas layer; relative to the parent's effective Z when `z_as_relative` is on. |
| **z_as_relative** | When true (default), the item's Z adds to its parent's effective Z instead of being absolute. |
| **Y-sort** | `y_sort_enabled` on a parent: children draw ordered by global Y (lower on screen = drawn later = in front). |
| **show_behind_parent** | CanvasItem flag drawing the item immediately below its direct parent, without changing its Z bracket. |
| **top_level** | Detaches a CanvasItem from its parent's *transform* (not its draw order or lifetime); position becomes canvas-space. |
| **modulate / self_modulate** | Multiplicative color tint; `modulate` cascades to children, `self_modulate` applies to the item only. |
| **CanvasGroup** | Node rendering its subtree into an intermediate buffer so transparency applies to the flattened result (no overlap seams). |
| **clip_children** | CanvasItem mode using the item as a mask that visually confines its children. |
| **Transform2D** | 2×3 matrix (two basis vectors + origin) representing position/rotation/scale/skew; inverted with `affine_inverse()`. |
| **Canvas transform** | The camera's transform (`Viewport.canvas_transform`), mapping world (canvas) coordinates to viewport coordinates. |
| **`_draw()`** | CanvasItem callback where `draw_*` commands are emitted; results are cached until invalidated. |
| **queue_redraw()** | Requests a fresh `_draw()` next frame; cheap, idempotent, the only correct way to refresh custom drawing. |
| **Hairline width** | `width = -1.0` in line-drawing methods: always one screen pixel regardless of zoom. |
| **Viewport / SubViewport** | A rendering surface; `SubViewport` renders off-screen into a texture (render target) instead of a window. |
| **ViewportTexture** | Live texture handle onto a viewport's rendered content, obtained via `get_texture()` or the inspector. |
| **Stretch mode** | Project setting mapping the design resolution to the window: `disabled`, `canvas_items` (re-rasterize, desktop default), `viewport` (render small, scale image). |
| **content_scale_factor** | Per-`Window` multiplier on the stretch scale — the runtime DPI/accessibility zoom knob. |
| **CanvasItemMaterial** | Fixed-function 2D material: blend mode (mix/add/sub/mul/premult) and light mode (normal/unshaded/light-only). |
| **Tween** | Runtime interpolation object from `create_tween()`; executes a program of tweeners, then invalidates. |
| **Tweener** | One step of a tween: `PropertyTweener`, `IntervalTweener`, `CallbackTweener`, `MethodTweener` (and `SubtweenTweener`, 4.4+). |
| **trans / ease** | Curve family (`TRANS_QUAD`, `TRANS_ELASTIC`, …) and which end it emphasizes (`EASE_IN/OUT/IN_OUT/OUT_IN`). |
| **kill()** | Destroys a tween immediately; properties freeze mid-flight and `finished` never fires. |
| **Parallax2D** | Node2D (4.3+) scrolling its children against camera motion via `scroll_scale`; successor to `ParallaxBackground`/`ParallaxLayer`. |
| **PointLight2D / DirectionalLight2D** | 2D lights: positional (texture-shaped falloff) and infinite-parallel; blend, cull-mask and shadow controls on both. |
| **LightOccluder2D** | Shadow-casting polygon (`OccluderPolygon2D`) for 2D lights. |
| **CanvasModulate** | Node multiplying every CanvasItem in its canvas by one color — global tint/day-night; one visible instance per canvas. |
| **Theme** | Resource mapping control types (and type variations) to colors, constants, fonts, icons and styleboxes; resolved local override → node/ancestor theme → project theme → default. |
| **StyleBox** | A control's box style: `StyleBoxFlat` (vector fills/borders/corners), `StyleBoxTexture` (nine-slice bitmap), `StyleBoxEmpty`, `StyleBoxLine`. |
| **Nine-slice (9-patch)** | Texture split into 9 zones — fixed corners, stretched edges, filled center — so one small bitmap skins any panel size. |
| **HDR 2D** | Project setting rendering the 2D canvas in high dynamic range; prerequisite for 2D glow and meaningful overbright colors. |

