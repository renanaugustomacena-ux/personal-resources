---
course: "Godot 4 in Production"
phase: "1 — Foundations"
module: "03"
title: "Sprites and Textures — 2D Assets, Import Pipeline and Animation"
version: "Godot 4.5 / GDScript 2.0"
level: "Beginner-Intermediate"
prerequisites: [ "GODOT_ENGINE_STUDY.md", "SCENES_AND_NODES.md" ]
objectives:
  - "Choose the correct Texture2D subclass (ImageTexture, CompressedTexture2D, AtlasTexture, ViewportTexture, NoiseTexture2D) for a given asset"
  - "Configure the import pipeline (compress mode, mipmaps, fix alpha border) deliberately instead of accepting defaults"
  - "Set up a pixel-perfect project: nearest filtering, snap settings, viewport stretch with integer scaling"
  - "Drive Sprite2D and AnimatedSprite2D from typed GDScript, including spritesheet slicing with hframes/vframes and AtlasTexture regions"
  - "Select the right animation tool (AnimatedSprite2D, AnimationPlayer, Tween, shader) using explicit decision criteria"
  - "Measure texture memory and draw calls with Performance monitors and budget VRAM for a desktop-companion app"
  - "Generate and mutate textures at runtime with the Image class without ever touching lock()/unlock()"
tags: [godot, gdscript, sprites, textures, pixel-art, import-pipeline, animation, spritesheet, atlas, vram, 2d, spriteframes]
---

# Sprites and Textures — 2D Assets, Import Pipeline and Animation — Complete Guide

> **Module 03** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Godot Engine Study — Foundations](GODOT_ENGINE_STUDY.md), [Scenes and Nodes](SCENES_AND_NODES.md)
>
> By the end of this module you will be able to:
> 1. Explain the full journey of an image file from `assets/` to the GPU: importer, `.import` file, `.godot/imported/` cache, `CompressedTexture2D` at runtime.
> 2. Choose compression, mipmap and filtering settings deliberately — and defend why pixel art demands **Lossless + no mipmaps + Nearest**.
> 3. Configure a pixel-perfect project from scratch: filter, snapping, stretch mode, integer scaling — and diagnose every common cause of "my pixel art is blurry".
> 4. Use `Sprite2D` (region, hframes/vframes, offset, flipping, modulate) and `AtlasTexture` fluently, from the Inspector and from typed GDScript.
> 5. Build multi-animation characters with `AnimatedSprite2D` + `SpriteFrames`, and know precisely when to reach for `AnimationPlayer`, `AnimationTree`, a `Tween`, or a shader instead.
> 6. Generate, inspect and mutate pixels at runtime with `Image` and `ImageTexture` (lock-free 4.x API).
> 7. Measure texture memory and draw calls with `Performance` monitors and keep a sprite-heavy scene inside a VRAM budget.
>
> **Estimated time:** 6-8 hours (reading 2.5 h · labs 3.5-5.5 h) · **Level:** Beginner-Intermediate

## Guiding ideas

1. **Pixel art means `Nearest` filtering, always — `Linear` blurs, `Nearest` preserves crisp edges.**
2. **The importer is part of your codebase: `.import` files are settings-as-code and belong in version control.**
3. **One atlas beats a hundred PNGs — fewer files, fewer texture switches, better 2D batching.**
4. **Pick the animation tool by what you animate: frames → `AnimatedSprite2D`, properties → `AnimationPlayer`, one-shots → `Tween`, per-pixel effects → shaders.**
5. **VRAM compression is for 3D photorealism; it eats pixel art alive — a 4×4 block codec cannot represent a 1-pixel outline.**
6. **Measure before optimizing: `Performance.get_monitor()` tells you the real texture memory and draw-call cost.**

## Concept map

```
                          ┌───────────────────────────────────┐
                          │      SPRITES AND TEXTURES         │
                          │  (2D assets, import, animation)   │
                          └────────────────┬──────────────────┘
                                           │
          ┌────────────────────────────────┼───────────────────────────────┐
          │                                │                               │
 ┌────────▼─────────┐            ┌────────▼─────────┐            ┌────────▼─────────┐
 │  TEXTURE FAMILY  │            │  IMPORT PIPELINE │            │    DISPLAYING    │
 │                  │            │                  │            │                  │
 │ Texture2D (base) │            │ .import files    │            │ Sprite2D         │
 │ CompressedTex2D  │            │ Lossless / Lossy │            │  region, frames  │
 │ ImageTexture     │            │ VRAM Compressed  │            │  offset, flip    │
 │ AtlasTexture     │            │ mipmaps          │            │  modulate        │
 │ ViewportTexture  │            │ fix alpha border │            │ AnimatedSprite2D │
 │ GradientTexture  │            │ size limit       │            │  + SpriteFrames  │
 │ NoiseTexture2D   │            │ detect 3D        │            │ NinePatchRect    │
 │ Image (CPU side) │            │ Import Defaults  │            │ TextureRect      │
 └────────┬─────────┘            └────────┬─────────┘            └────────┬─────────┘
          │                               │                               │
          │                     ┌─────────▼──────────┐                    │
          │                     │  PIXEL-ART CONFIG  │                    │
          │                     │                    │                    │
          │                     │ Nearest filter     │                    │
          │                     │ snap 2D transforms │                    │
          │                     │ viewport stretch   │                    │
          │                     │ integer scaling    │                    │
          │                     └─────────┬──────────┘                    │
          │                               │                               │
          └───────────────┬───────────────┴───────────────┬───────────────┘
                          │                               │
                ┌─────────▼──────────┐          ┌─────────▼──────────┐
                │    ANIMATION       │          │   PERFORMANCE      │
                │                    │          │                    │
                │ AnimatedSprite2D   │          │ draw calls         │
                │ AnimationPlayer    │          │ 2D batching        │
                │ AnimationTree      │          │ VRAM monitors      │
                │ Tween / shaders    │          │ texture budgets    │
                │ decision table     │          │ channel packing    │
                └────────────────────┘          └────────────────────┘
```

## Table of contents

1. [Overview — the 2D asset pipeline at a glance](#overview--the-2d-asset-pipeline-at-a-glance)
2. [The Texture2D class family](#the-texture2d-class-family)
3. [The Image class — CPU-side pixel work](#the-image-class--cpu-side-pixel-work)
4. [The import pipeline in depth](#the-import-pipeline-in-depth)
5. [Compression modes explained](#compression-modes-explained)
6. [Filtering, mipmaps and color space](#filtering-mipmaps-and-color-space)
7. [Pixel-art configuration recipe](#pixel-art-configuration-recipe)
8. [Sprite2D deep dive](#sprite2d-deep-dive)
9. [AtlasTexture and spritesheets](#atlastexture-and-spritesheets)
10. [Draw calls and 2D batching](#draw-calls-and-2d-batching)
11. [AnimatedSprite2D and SpriteFrames](#animatedsprite2d-and-spriteframes)
12. [Choosing an animation approach](#choosing-an-animation-approach)
13. [AnimationPlayer for sprite animation](#animationplayer-for-sprite-animation)
14. [AnimationTree — a first taste](#animationtree--a-first-taste)
15. [Nine-patch and UI textures](#nine-patch-and-ui-textures)
16. [Texture memory and performance](#texture-memory-and-performance)
17. [Case study: Relax Room](#case-study-relax-room)
18. [Best practices](#best-practices)
19. [Common errors & troubleshooting](#common-errors--troubleshooting)
20. [Exercises](#exercises)
21. [Further reading](#further-reading)
22. [Glossary](#glossary)

---

## Overview — the 2D asset pipeline at a glance

Every 2D game is, at its core, a machine that draws textured rectangles very fast. Understanding what a *texture* is, how it gets from a PNG on your disk into GPU memory, and how the engine samples it when drawing, is the difference between a project that "mostly looks right" and one that is pixel-perfect, memory-efficient and fast. This module covers that entire journey for Godot 4.5, with a persistent focus on the constraints of our production context: a desktop-companion, 2D-isometric pixel-art application — the **Relax Room** case study.

### From file to frame

When you drop `character.png` into your project folder, a surprising amount happens before a single pixel reaches the screen:

1. **Detection.** The editor's filesystem scanner notices the new file. Image files are *not* usable by the engine directly — they must be converted into an engine-native format first.
2. **Import.** The *texture importer* reads the PNG, applies the import options (compression mode, mipmaps, alpha-border fixing, size limits), and writes the result into the hidden `.godot/imported/` cache directory as a `.ctex` file.
3. **Metadata.** A small text file, `character.png.import`, appears next to the source. It records which importer ran, which options were used, and where the cached artifact lives. This file *is* your import configuration — it belongs in version control.
4. **Loading.** At runtime, `load("res://assets/character.png")` does not read the PNG at all. It reads the imported `.ctex` and hands you a `CompressedTexture2D` — a GPU-ready resource.
5. **Drawing.** A node such as `Sprite2D` submits the texture to the 2D renderer, which batches it with neighboring draws that share the same texture and material, and the GPU samples it using the node's *texture filter* (nearest or linear).

Every stage has decisions attached, and every decision has a visible consequence. Choose the wrong compression and your art gets smeared with block artifacts. Leave the default linear filter on and your 32×32 pixel-art character turns into a blurry ghost when scaled 4×. Forget snapping settings and sprites shimmer as the camera scrolls. This module makes each decision explicit.

### The three axes of this module

The material is organized along three axes that you will keep returning to in production:

- **Data** — what texture types exist, what the importer does to them, and what they cost in memory (§2-§6, §16).
- **Display** — the nodes that put textures on screen: `Sprite2D`, `AnimatedSprite2D`, `NinePatchRect`, `TextureRect` (§8-§9, §15).
- **Motion** — the four ways to animate sprites and the decision framework for choosing between them (§11-§14).

Threaded through all three is the **pixel-art configuration recipe** (§7): a checklist you can apply to any new project in ten minutes, and which the Relax Room project applies verbatim.

> ✅ **Best practice** — Read this module next to an open Godot editor. Every Inspector screenshot described here ("Import dock", "SpriteFrames panel") is worth locating in the real UI once; the muscle memory pays for itself for years.

### What changed from Godot 3.x (orientation for veterans)

If you learned 2D asset handling in Godot 3, four things moved and one thing disappeared:

| Godot 3.x | Godot 4.x |
|---|---|
| Filter/repeat were **import flags** on each texture | Filter/repeat are **CanvasItem properties** (`texture_filter`, `texture_repeat`) with a project-wide default — not import options at all |
| `StreamTexture` | `CompressedTexture2D` |
| `Image.lock()` / `Image.unlock()` required around pixel access | **Lock-free API** — call `get_pixel()` / `set_pixel()` directly |
| `ImageTexture.create_from_image(img, flags)` instance method | `ImageTexture.create_from_image(img)` **static** constructor, no flags argument |
| `Sprite` node | `Sprite2D` node (and `AnimatedSprite` → `AnimatedSprite2D`) |

The first row is the one that bites hardest in practice: countless Godot 3 tutorials tell you to "disable filtering in the Import dock". In Godot 4 that checkbox does not exist there — you set the default in Project Settings and override per node. Section 6 covers this in full.

---

## The Texture2D class family

`Texture2D` is the abstract base class for every two-dimensional texture in Godot. You never instantiate `Texture2D` itself; you work with its subclasses, each of which answers a different question about *where the pixels come from*. Choosing the right subclass is an architectural decision, not a cosmetic one — it determines memory behavior, update cost and tooling.

### Family tree

```
Resource
└── Texture
    └── Texture2D                    (abstract — "something that can be drawn as a 2D image")
        ├── CompressedTexture2D      (imported assets — what load("res://….png") returns)
        ├── PortableCompressedTexture2D  (embeddable compressed texture, survives export tweaks)
        ├── ImageTexture             (created at runtime from an Image)
        ├── AtlasTexture             (a rectangular window into another Texture2D)
        ├── ViewportTexture          (live output of a SubViewport)
        ├── CanvasTexture            (diffuse + normal + specular for 2D lighting)
        ├── GradientTexture1D        (procedural: a Gradient sampled into a strip)
        ├── GradientTexture2D        (procedural: 2D gradient fills — linear, radial, square)
        ├── NoiseTexture2D           (procedural: FastNoiseLite rendered to a texture)
        ├── CurveTexture             (a Curve resource baked into a 1D texture, for shaders)
        ├── AnimatedTexture          (deprecated — do not use in new code)
        └── PlaceholderTexture2D     (stand-in used by the dedicated-server export)
```

### CompressedTexture2D — the workhorse

`CompressedTexture2D` is what the import pipeline produces and what `load()` / `preload()` return for any imported image. The name is slightly misleading: it does not mean the texture is VRAM-compressed. It means the texture was serialized through the importer's container format (`.ctex`), which may hold **losslessly compressed**, **lossy-compressed** or **VRAM-compressed** data depending on the import options. Even a pixel-art sprite imported with `Lossless` mode arrives as a `CompressedTexture2D`.

```gdscript
# Typical usage — you rarely name the class explicitly:
var tex: Texture2D = load("res://assets/room/room.png")   # CompressedTexture2D at runtime
print(tex.get_class())        # "CompressedTexture2D"
print(tex.get_size())         # e.g. (320.0, 180.0) as Vector2

# preload() resolves at parse time and is the standard for fixed assets:
const ROOM_TEXTURE: Texture2D = preload("res://assets/room/room.png")
```

You should treat `CompressedTexture2D` as read-only: it is a view over the imported artifact. If you need to modify pixels, go through `Image` (§3).

### ImageTexture — runtime-created textures

`ImageTexture` wraps an `Image` you built or loaded in code. It is the bridge from CPU-side pixel data to a GPU resource, and the only standard way to display an image file that lives *outside* `res://` (for example, a user-selected wallpaper in a desktop companion app — a real requirement in Relax Room's roadmap).

```gdscript
# Load an image from an absolute filesystem path at runtime (NOT via the importer):
func load_external_wallpaper(path: String) -> Texture2D:
    var img: Image = Image.load_from_file(path)   # static; returns null-equivalent empty on failure
    if img.is_empty():
        push_error("Could not load image: %s" % path)
        return null
    return ImageTexture.create_from_image(img)     # static constructor in 4.x
```

Two update paths exist once an `ImageTexture` is alive:

```gdscript
var tex := ImageTexture.create_from_image(img)

# 1) Same size and format → cheap in-place update (no reallocation):
img.set_pixel(0, 0, Color.RED)
tex.update(img)

# 2) Different size or format → full replacement:
var bigger := Image.create_empty(256, 256, false, Image.FORMAT_RGBA8)
tex.set_image(bigger)
```

> ⚠️ **Pitfall** — `ImageTexture.update()` requires the new `Image` to have the **same size and format** as the original. If they differ you get an error and an unchanged texture. Use `set_image()` when dimensions change.

### AtlasTexture — a window into a bigger texture

`AtlasTexture` exposes a rectangular region of another `Texture2D` as if it were an independent texture. Anywhere the engine accepts a `Texture2D` — a `Sprite2D.texture`, a `SpriteFrames` frame, a button icon — you can hand it an `AtlasTexture` instead, and only the region is drawn. Its properties:

| Property | Type | Meaning |
|---|---|---|
| `atlas` | `Texture2D` | The source sheet |
| `region` | `Rect2` | The sub-rectangle to expose, in pixels of the atlas |
| `margin` | `Rect2` | Extra empty space drawn around the region (position = left/top padding, size = added width/height) |
| `filter_clip` | `bool` | If `true`, clamps texture sampling to the region — prevents neighboring frames from bleeding in when linear filtering is active |

Section 9 is dedicated to atlas workflows; the key mental model is: *one big texture on the GPU, many lightweight `AtlasTexture` resources pointing into it*.

### ViewportTexture — render-to-texture

A `ViewportTexture` shows the live rendered output of a `SubViewport`. This is Godot's render-to-texture mechanism: minimaps, security-camera screens, applying a 2D shader to a whole subtree, or rendering a 3D model into a 2D interface all go through it.

```gdscript
# Scene structure:
#   Main
#   ├── SubViewport            (size = Vector2i(160, 90))
#   │   └── MinimapWorld …
#   └── Sprite2D               (shows the viewport's output)

@onready var sub_viewport: SubViewport = $SubViewport
@onready var minimap_sprite: Sprite2D = $Sprite2D

func _ready() -> void:
    minimap_sprite.texture = sub_viewport.get_texture()   # returns ViewportTexture
```

> ⚠️ **Pitfall** — A `ViewportTexture` only works while its `SubViewport` is inside the scene tree, and when assigned in the Inspector the viewport must live in the **same scene** as the consumer. Trying to save a `ViewportTexture` inside a standalone `.tres` resource breaks the path and produces errors at load time.

### CanvasTexture — 2D lighting maps

`CanvasTexture` bundles a diffuse texture with an optional **normal map** and **specular map** so 2D lights (`PointLight2D`, `DirectionalLight2D`) can shade sprites. For a flat-lit pixel-art project like Relax Room it is optional, but it is the standard answer when someone asks "how do I make my 2D sprites react to light direction?" — you author a normal map (e.g. with Laigter or Sprite DLight), then assign a `CanvasTexture` with `diffuse_texture`, `normal_texture` and per-texture `texture_filter` to the sprite.

### GradientTexture1D / GradientTexture2D — procedural ramps

Both bake a `Gradient` resource (a list of color stops) into a texture without any image file on disk:

- `GradientTexture1D` — a horizontal strip (`width` px, default 256). Perfect as a **lookup table for shaders**: health-bar color ramps, palette-mapping, fake day/night tinting.
- `GradientTexture2D` — a filled rectangle with `fill` = linear / radial / square, and `fill_from` / `fill_to` control points in UV space. Handy for vignettes, sky backdrops and soft shadows under UI cards.

```gdscript
var ramp := GradientTexture1D.new()
var g := Gradient.new()
g.set_color(0, Color("2e3440"))
g.set_color(1, Color("88c0d0"))
ramp.gradient = g
ramp.width = 64
$TextureRect.texture = ramp
```

The 2D variant, configured for a radial vignette — no PNG, endlessly tweakable in the Inspector:

```gdscript
var vignette := GradientTexture2D.new()
vignette.fill = GradientTexture2D.FILL_RADIAL
vignette.fill_from = Vector2(0.5, 0.5)     # center, in UV space
vignette.fill_to = Vector2(0.5, 0.0)       # radius reference point
var vg := Gradient.new()
vg.set_color(0, Color(0, 0, 0, 0))         # transparent center
vg.set_color(1, Color(0, 0, 0, 0.6))       # darkened edges
vignette.gradient = vg
vignette.width = 320
vignette.height = 180
$VignetteRect.texture = vignette           # stretched full-screen TextureRect
```

### NoiseTexture2D — procedural noise

`NoiseTexture2D` renders a `Noise` resource (in practice `FastNoiseLite`) into a texture: clouds, dithering masks, dissolve effects, heightmaps. Two production-relevant details:

```gdscript
var noise_tex := NoiseTexture2D.new()
noise_tex.width = 256
noise_tex.height = 256
noise_tex.seamless = true          # tileable — costs some generation time
var noise := FastNoiseLite.new()
noise.noise_type = FastNoiseLite.TYPE_SIMPLEX
noise.frequency = 0.04
noise_tex.noise = noise

# 1) Generation is ASYNCHRONOUS (runs on a thread). If you need the pixels
#    immediately — e.g. to read them with get_image() — you must wait:
await noise_tex.changed
var img: Image = noise_tex.get_image()

# 2) As a shader uniform or sprite texture you can assign it right away;
#    it will pop in when ready.
$Sprite2D.texture = noise_tex
```

> ⚠️ **Pitfall** — Reading `NoiseTexture2D.get_image()` in `_ready()` without `await noise_tex.changed` returns nothing useful, because the texture has not been generated yet. This is the single most common surprise with procedural textures in 4.x.

### AnimatedTexture — avoid

`AnimatedTexture` (a texture that cycles through frames on its own) is **deprecated** in Godot 4. It suffers from severe limitations (global frame timing, no per-instance control, max 256 frames) and will likely be removed. Any use case it served is covered better by `AnimatedSprite2D` (§11) or an `AnimationPlayer` (§13). If you meet it in an old project, plan a migration.

### The shared Texture2D surface

Whatever the subclass, every `Texture2D` answers the same basic questions — worth knowing because generic code (placement math, tooling, custom drawing) should depend on the base class, not on any concrete subclass:

```gdscript
var tex: Texture2D = sprite.texture
print(tex.get_width())        # int, pixels
print(tex.get_height())       # int, pixels
print(tex.get_size())         # Vector2 — convenience for both
var img: Image = tex.get_image()   # CPU-side copy (decompresses if needed — not per-frame!)
print(tex.resource_path)      # "res://assets/…" for loaded resources, "" for runtime-built
```

Textures are `Resource`s, which carries three practical behaviors:

1. **Sharing by default.** Assigning one texture to fifty sprites stores one GPU texture and fifty cheap references. There is no "instance per sprite" cost, and mutating a shared resource (e.g. an `AtlasTexture.region`) affects *every* user — call `duplicate()` when you want an independent copy:

```gdscript
var solo := (sprite.texture as AtlasTexture).duplicate() as AtlasTexture
solo.region = Rect2(32, 0, 32, 32)     # only this copy changes
other_sprite.texture = solo
```

2. **Path-cached loading.** `load()` caches by `resource_path`; loading the same path twice returns the same object (§16 discusses the memory consequences).
3. **Inspector-editable sub-resources.** An `AtlasTexture` embedded in a scene is stored *inside* the `.tscn`; saved as a `.tres` it becomes shareable across scenes. The tradeoff is the usual embedded-vs-external resource decision from [SCENES_AND_NODES.md](SCENES_AND_NODES.md).

Textures can also draw themselves without any node, inside a `CanvasItem._draw()` callback — the escape hatch for custom-drawn widgets, debug overlays and high-count static decor:

```gdscript
extends Node2D
## Draws a repeated icon row without instantiating a node per icon.
var icon: Texture2D = preload("res://assets/ui/heart.png")
var hp: int = 3

func _draw() -> void:
    for i in hp:
        draw_texture(icon, Vector2(i * 18, 0))
    # Also available: draw_texture_rect(), draw_texture_rect_region() for
    # scaled drawing and atlas-region drawing respectively.

func set_hp(value: int) -> void:
    hp = value
    queue_redraw()          # _draw() runs only when the item is dirtied
```

Two lesser-known family members complete the picture:

- **`PortableCompressedTexture2D`** — a compressed texture that embeds its own data inside the resource file instead of depending on the import cache. Niche but valuable when a texture must live *inside* a `.tres`/`.scn` that ships across projects (e.g. an addon's bundled icons): `create_from_image(image, PortableCompressedTexture2D.COMPRESSION_MODE_LOSSLESS)`.
- **`CurveTexture`** — bakes a `Curve` resource into a 1-D texture (`width` samples). The standard vehicle for handing an artist-editable falloff/easing curve to a shader: attenuation ramps, dissolve profiles, brush shapes.

```gdscript
var falloff := CurveTexture.new()
var curve := Curve.new()
curve.add_point(Vector2(0.0, 1.0))
curve.add_point(Vector2(1.0, 0.0))
falloff.curve = curve
material.set_shader_parameter(&"falloff", falloff)
```

### Decision table — which texture class when?

| You need… | Use | Why |
|---|---|---|
| Show an imported PNG/WebP/SVG | `CompressedTexture2D` (implicit via `load`) | The importer already produced GPU-ready data |
| Display a file from the user's disk (outside `res://`) | `Image.load_from_file()` + `ImageTexture` | Importer never ran on external files |
| Slice a spritesheet into frames | `AtlasTexture` | One GPU texture, many logical sprites; batching-friendly |
| Show live output of another scene / minimap | `ViewportTexture` | Render-to-texture |
| Sprites that react to 2D lights | `CanvasTexture` | Carries normal + specular maps |
| Color ramp for a shader or UI | `GradientTexture1D/2D` | Procedural, no asset file, editable in Inspector |
| Clouds, dissolve masks, dithering | `NoiseTexture2D` | Procedural noise, seamless option |
| Generate/modify pixels in code | `Image` + `ImageTexture` | CPU-side read/write, then upload |
| Self-animating texture | **Nothing — use `AnimatedSprite2D`** | `AnimatedTexture` is deprecated |

---

## The Image class — CPU-side pixel work

`Texture2D` and its children live on the GPU: fast to draw, opaque to inspect. `Image` is their CPU-side counterpart — a plain block of pixel data you can read, write, resize, composite and save. Whenever you hear "generate a texture from code", "read a pixel color", or "screenshot", the answer starts with `Image`.

### The 4.x lock-free API

In Godot 3, pixel access required a `lock()` / `unlock()` dance. **Godot 4 removed it entirely** — you call `get_pixel()` and `set_pixel()` directly. If you see `lock()` in a tutorial, that tutorial is for Godot 3; the 4.x port is: delete those lines.

```gdscript
# Create an empty RGBA image and paint a procedural checkerboard.
func make_checkerboard(size: int, cell: int) -> ImageTexture:
    var img := Image.create_empty(size, size, false, Image.FORMAT_RGBA8)
    for y in size:
        for x in size:
            var dark := ((x / cell) + (y / cell)) % 2 == 0
            img.set_pixel(x, y, Color("3b4252") if dark else Color("d8dee9"))
    return ImageTexture.create_from_image(img)
```

The `create_empty(width, height, use_mipmaps, format)` static constructor replaces the older `Image.create()` (deprecated, same signature). The `use_mipmaps` flag reserves space for mipmap levels; for 2D work it is almost always `false`.

### Key operations, grouped

**Creation and loading**

```gdscript
var a := Image.create_empty(64, 64, false, Image.FORMAT_RGBA8)     # blank canvas
var b := Image.create_from_data(w, h, false, Image.FORMAT_RGBA8, byte_array)  # raw bytes
var c := Image.load_from_file("C:/Users/alex/Pictures/photo.png")   # external file, static
var d := (load("res://assets/icon.png") as Texture2D).get_image()   # download from GPU side
var e := Image.new()
var err: Error = e.load("res://raw/heightmap.png")                  # into existing instance
```

`Texture2D.get_image()` is the reverse bridge: it retrieves the pixel data of any texture (decompressing if necessary — not free, do not call it per frame).

**Pixel access**

```gdscript
var color: Color = img.get_pixel(10, 20)          # x, y ints
img.set_pixel(10, 20, Color.TRANSPARENT)
var c2: Color = img.get_pixelv(Vector2i(10, 20))  # Vector2i variants
img.set_pixelv(Vector2i(10, 20), Color.RED)
```

**Bulk operations**

```gdscript
img.fill(Color.BLACK)                                   # whole image
img.fill_rect(Rect2i(0, 0, 32, 32), Color.WHITE)        # sub-rectangle
img.blit_rect(src_img, Rect2i(0, 0, 16, 16), Vector2i(8, 8))   # copy (alpha OVERWRITES)
img.blend_rect(src_img, Rect2i(0, 0, 16, 16), Vector2i(8, 8))  # copy (alpha BLENDS)
img.resize(128, 128, Image.INTERPOLATE_NEAREST)         # NEAREST for pixel art!
img.flip_x(); img.flip_y()
img.crop(64, 64)
```

> ✅ **Best practice** — When resizing pixel art in code, always pass `Image.INTERPOLATE_NEAREST`. The default (`INTERPOLATE_BILINEAR`) will smear your palette exactly like a linear texture filter does at render time. The other modes (`INTERPOLATE_CUBIC`, `INTERPOLATE_LANCZOS`) are for photographic content.

**Format and conversion**

```gdscript
print(img.get_format())              # e.g. Image.FORMAT_RGB8
img.convert(Image.FORMAT_RGBA8)      # add an alpha channel
print(img.get_size())                # Vector2i
print(img.has_mipmaps())
```

Formats you will actually meet in 2D work: `FORMAT_RGBA8` (the default workhorse, 4 bytes/pixel), `FORMAT_RGB8` (no alpha, 3 bytes), `FORMAT_L8` (grayscale, 1 byte — masks and heightmaps), `FORMAT_RGBAF` (float HDR). Compressed formats (`FORMAT_DXT5`, `FORMAT_ETC2_RGBA8`, `FORMAT_ASTC_4x4`, …) appear when you `get_image()` from a VRAM-compressed texture; you cannot `set_pixel()` on those until you `decompress()` them.

**Saving**

```gdscript
img.save_png("user://export/avatar.png")
img.save_jpg("user://export/photo.jpg", 0.85)         # quality 0-1
img.save_webp("user://export/anim_frame.webp", false)  # lossless webp
var bytes: PackedByteArray = img.save_png_to_buffer()  # in-memory, e.g. for network upload
```

### Worked example — runtime palette swap

A classic pixel-art trick: recolor a character by replacing exact palette entries. With the lock-free API this is a straightforward double loop; for a 32×32 sprite it is microseconds.

```gdscript
## Replaces every occurrence of each key color with its value color.
## Suitable for small pixel-art sprites (exact-match palettes, no anti-aliasing).
func palette_swap(source: Texture2D, mapping: Dictionary[Color, Color]) -> ImageTexture:
    var img: Image = source.get_image()
    if img.is_compressed():
        img.decompress()                       # needed if source was VRAM-compressed
    img.convert(Image.FORMAT_RGBA8)
    for y in img.get_height():
        for x in img.get_width():
            var c := img.get_pixel(x, y)
            if mapping.has(c):
                img.set_pixel(x, y, mapping[c])
    return ImageTexture.create_from_image(img)

# Usage:
var recolored := palette_swap(
    preload("res://assets/charachters/male/old/male_idle/male_idle_down.png"),
    { Color("6d4c41"): Color("263238") }       # brown hair → black hair
)
$Sprite2D.texture = recolored
```

> ⚠️ **Pitfall** — `get_pixel()`/`set_pixel()` loops are fine for sprite-sized images and one-shot operations, but they are **not** a per-frame technique for large images: a 1920×1080 image is two million pixels per pass, in interpreted GDScript. For per-frame, full-screen pixel effects, use a shader (see [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md)); for palette swaps at scale, a palette-LUT shader beats CPU loops.

### Worked example — images as pure data

Nothing forces an `Image` to be *drawn*. Importing an image with the **Image** importer type (§4) and reading it with `get_pixel()` turns any paint program into a level/data editor. Relax Room's roadmap uses this for room layout masks; here is the generic pattern — a walkability mask where white pixels mean "the character may stand here":

```gdscript
## Reads a walkability mask authored as a black/white PNG.
## The PNG is imported with importer type "Image", so load() returns an Image directly.
class_name WalkabilityMask
extends RefCounted

var _mask: Image
var _cell_size: int

func _init(mask_path: String, cell_size: int = 64) -> void:
    _mask = load(mask_path) as Image
    _cell_size = cell_size

func is_walkable(world_pos: Vector2) -> bool:
    var cell := Vector2i(world_pos) / _cell_size
    if cell.x < 0 or cell.y < 0 \
            or cell.x >= _mask.get_width() or cell.y >= _mask.get_height():
        return false
    return _mask.get_pixelv(cell).r > 0.5     # white = walkable

# Usage in a controller:
# var mask := WalkabilityMask.new("res://data/room_mask.png")
# if mask.is_walkable(target):  move_to(target)
```

One authored PNG replaces a hand-maintained 2D array in code, artists can edit it in Aseprite, and diffs are visual. The same technique carries spawn maps (color-coded pixels → entity types), heat/influence maps, and biome layouts. For *tile-based* level data specifically, prefer the dedicated systems in [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md); the image-as-data trick shines for irregular, low-resolution, purely-logical grids.

### Worked example — screenshots and thumbnails

The viewport's rendered output is one `get_image()` away — the foundation for screenshot features, save-slot thumbnails and bug-report attachments:

```gdscript
## Captures the current frame and saves both a full screenshot and a thumbnail.
func capture_screenshot() -> void:
    # Wait for the frame to finish rendering before grabbing it:
    await RenderingServer.frame_post_draw
    var img: Image = get_viewport().get_texture().get_image()

    var dir := "user://screenshots"
    DirAccess.make_dir_recursive_absolute(dir)
    var stamp := Time.get_datetime_string_from_system().replace(":", "-")
    img.save_png("%s/shot_%s.png" % [dir, stamp])

    # Save-slot thumbnail: downscale a copy. NEAREST keeps the pixel-art look.
    var thumb := img.duplicate() as Image
    thumb.resize(160, 90, Image.INTERPOLATE_NEAREST)
    thumb.save_png("%s/thumb_%s.png" % [dir, stamp])
```

Details that separate this from a naive version: `await RenderingServer.frame_post_draw` guarantees the capture happens after the current frame is complete (calling mid-frame can grab a stale or partial image); `user://` is the only portably writable location in exported builds; and the thumbnail is resized on a *duplicate* so the full-size capture stays intact.

### Dirty-rectangle updates — keeping runtime textures cheap

For textures you mutate continuously (a fog-of-war overlay, a paint canvas, a minimap), the cost profile is: `set_pixel()` is nearly free, `ImageTexture.update()` re-uploads the **whole** image. Strategy: batch all pixel writes for a frame, call `update()` at most once per frame, and skip it entirely on frames where nothing changed.

```gdscript
var _img: Image
var _tex: ImageTexture
var _dirty := false

func reveal_area(center: Vector2i, radius: int) -> void:
    for y in range(center.y - radius, center.y + radius + 1):
        for x in range(center.x - radius, center.x + radius + 1):
            if Vector2i(x, y).distance_to(center) <= radius:
                _img.set_pixel(x, y, Color(0, 0, 0, 0))   # punch a transparent hole
    _dirty = true                                          # write now, upload later

func _process(_delta: float) -> void:
    if _dirty:
        _tex.update(_img)                                  # one upload per frame, max
        _dirty = false
```

At fog-of-war resolutions (one pixel per tile, e.g. 64×64) this is effectively free; the texture is then drawn scaled over the world with Nearest filtering, or fed to a blur shader for soft edges.

### When Image is the right tool

- **Procedural content baked once** — dungeon minimaps, identicon avatars, dithering masks generated at startup.
- **Reading data** — sampling a heightmap or a "walkability mask" authored as an image (`get_pixel()` as a data query, never drawn at all).
- **Screenshots** — `get_viewport().get_texture().get_image()` then `save_png()`.
- **External files** — anything the user provides at runtime.
- **Import-time processing** — custom `EditorImportPlugin`s manipulate `Image`s.

When it is the wrong tool: continuous per-frame effects (shader territory) and anything the importer can do for you offline.

---

## The import pipeline in depth

Godot never uses your source image files directly at runtime. Everything passes through the **import pipeline**, and the pipeline is configurable per file, per preset and per project. Teams that ignore it ship blurry pixel art and bloated VRAM; teams that master it get deterministic, versionable asset processing for free.

### Supported source formats

The texture importer accepts: **PNG** (the 2D default — lossless, alpha, universally supported), **WebP** (smaller than PNG at equal quality, both lossless and lossy variants), **JPEG** (photos; no alpha), **SVG** (rasterized at import time by the ThorVG library — vector sources for crisp UI at any scale), **TGA**, **BMP**, plus HDR-oriented formats (**OpenEXR** `.exr`, **Radiance** `.hdr`) and pre-compressed containers (**DDS**, **KTX**).

> ✅ **Best practice** — For pixel art, standardize on PNG sources exported at **1× native resolution** (a 32×32 sprite is a 32×32 PNG). Scaling belongs to the engine (node `scale`, stretch settings), never to the asset. A "pre-scaled 4×" PNG quadruples memory in both dimensions for zero visual gain and breaks the atlas math.

### Anatomy of a `.import` file

For every imported file, Godot writes a sibling `<name>.<ext>.import` text file. Here is a real one for a pixel-art sprite, annotated:

```ini
[remap]

importer="texture"                 ; which importer processed this file
type="CompressedTexture2D"         ; runtime class produced
uid="uid://c3v0a2l7xkq8m"          ; stable unique ID (survives moves/renames)
path="res://.godot/imported/male_idle_down.png-8a41c…f2.ctex"   ; cached artifact

[deps]

source_file="res://assets/charachters/male/old/male_idle/male_idle_down.png"
dest_files=["res://.godot/imported/male_idle_down.png-8a41c…f2.ctex"]

[params]

compress/mode=0                    ; 0 = Lossless (see §5)
compress/high_quality=false
compress/lossy_quality=0.7
compress/hdr_compression=1
compress/normal_map=0
compress/channel_pack=0
mipmaps/generate=false             ; no mipmaps for 2D pixel art
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/fix_alpha_border=true      ; prevents dark fringes on transparent edges
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0               ; 0 = no downscaling at import
detect_3d/compress_to=1            ; what to switch to if used in 3D (see below)
```

Three practical consequences:

1. **`.import` files go in version control.** They are the reproducible recipe. The `.godot/` directory, by contrast, is a cache — always gitignored; any teammate's editor regenerates it from sources + `.import` files.
2. **They are diffable.** A code review can catch "someone flipped this sprite to VRAM Compressed" as a one-line diff.
3. **They are editable in bulk.** Since they are plain INI-style text, batch operations (e.g. forcing `mipmaps/generate=false` across a folder) are scriptable — though the supported route is import presets, below.

> ⚠️ **Pitfall** — Editing a `.import` file by hand while the editor is open will be silently overwritten by the editor's in-memory state. Make bulk edits with the editor closed, or use the Import dock / Import Defaults instead.

### The Import dock workflow

Select any image in the **FileSystem dock** and the **Import dock** (top-left tab group by default) shows its options. The workflow:

1. Select one file — or multi-select a whole folder of sprites.
2. Change options (e.g. Compress → Mode → Lossless).
3. Click **Reimport**. The editor regenerates the `.ctex` artifacts and updates the `.import` files.
4. Optionally choose **Preset ▸ Set as Default for 'Texture2D'** to make the current options the default for future imports of that resource type.

For per-project defaults there is a cleaner, centralized mechanism: **Project Settings → Import Defaults** tab. Pick the importer ("Texture2D"), override options, and every *newly imported* image uses them. Existing files keep their own `.import` until reimported.

> ✅ **Best practice** — First task in any new pixel-art project: open **Import Defaults**, set Compress Mode to *Lossless* and Mipmaps Generate to *Off* for `Texture2D` (usually already the 2D defaults, but making it explicit documents intent), and set the project's default texture filter to *Nearest* (§7). Then delete-and-reimport (or select-all + Reimport) any assets that were imported before the change.

### Changing the import *type*

The Import dock's top dropdown selects the **importer**, not just its options. The default "Texture2D" covers sprites, but alternatives matter:

| Import as | Produces | Use case |
|---|---|---|
| `Texture2D` | `CompressedTexture2D` | Everything drawable — the default |
| `Image` | `Image` | Data files you only read with `get_pixel()` (masks, heightmaps) — skips GPU upload |
| `BitMap` | `BitMap` | 1-bit masks, e.g. click-through regions for irregular buttons |
| `Texture2DArray` / `Texture3D` | layered textures | Shader-driven effects, LUTs |
| `Cubemap` | `Cubemap` | Sky/reflection maps (3D) |
| `Font Data (Monospace Image Font)` | bitmap font | Retro image-based fonts |
| **Keep File (exported as is)** | raw file | Ship the original bytes untouched (e.g. for a manual parser) |
| **Skip File (not exported)** | nothing | Source-only files: `.xcf`, `.psd` mockups, reference art |

The last two are underused: marking your Aseprite/Photoshop working files as *Skip File* keeps them in the repo for artists without bloating exports.

### `detect_3d` — the setting that "ruins" pixel art mysteriously

Fresh images import with 2D-friendly settings (Lossless, no mipmaps) **plus** a tripwire: `detect_3d/compress_to`. The first time the texture is used in a 3D context (a `StandardMaterial3D`, a `Sprite3D`, even just previewing it on a mesh), Godot **automatically reimports it** with VRAM compression and mipmaps — sensible for 3D, catastrophic for pixel art you also draw in 2D.

Symptoms: a previously crisp sprite suddenly shows smeary 4×4 blocks and slightly darker fringes, and its `.import` diff shows `compress/mode=2` appearing out of nowhere.

Fix and prevention:

```ini
detect_3d/compress_to=0   ; 0 = Disabled — never auto-convert this texture
```

Set **Detect 3D → Compress To → Disabled** on your 2D asset folders (multi-select + Reimport), or simply never open 2D sprites in 3D contexts. If it already happened, set Compress Mode back to Lossless, Mipmaps off, and Reimport.

### SVG import — crisp UI at any scale

SVG sources are rasterized at import time; the **SVG → Scale** option controls the rasterization multiplier. A 24×24 SVG icon imported at scale 4.0 yields a 96×96 texture. This is the professional route for *non-pixel-art* UI iconography in a desktop app: author once as vector, re-rasterize at the resolution the design needs, never suffer upscaling blur. (For Relax Room's pixel-art aesthetic we deliberately do the opposite — tiny PNGs, nearest filter, integer scale — but its settings windows could legitimately mix in SVG-sourced icons.)

> ⚠️ **Pitfall** — SVG `<text>` elements are not rendered by the import-time rasterizer; convert text to paths in your vector editor before exporting.

### UIDs, moves and renames

The `uid="uid://…"` line in every `.import` file is the asset's **stable identity**. Scenes and scripts that reference the texture record the UID alongside the path, so renaming or moving the file *inside the editor* updates nothing but a lookup table — references survive. Rules of engagement:

- **Move/rename inside the editor's FileSystem dock** (or at minimum move the `.import` file together with its source when reorganizing externally). A source file that arrives without its `.import` is treated as brand new: fresh UID, default import options, and every scene that referenced the old UID breaks.
- `load("uid://c3v0a2l7xkq8m")` works anywhere `load("res://…")` does, and survives any future reorganization. Editor UI (Copy UID in the FileSystem context menu) hands you the string. For hand-written code, paths remain more readable; UIDs shine in generated/serialized data.
- Merge conflicts in `.import` files are usually trivial (`uid` and `path` lines) — resolve by keeping *your* UID line consistently, then reimporting.

### Importing at scale — teams and CI

Three operational facts every team hits eventually:

1. **The import cache is disposable.** Deleting `.godot/` and reopening the project triggers a full reimport from sources + `.import` files. Slow on large projects, but a guaranteed clean-slate fix for cache corruption ("texture shows as pink/missing after a crash").
2. **Headless import for CI.** Export pipelines must import before they can export. The canonical build step is `godot --headless --import path/to/project` — it opens the editor headlessly, waits for all resources to import, and quits. Run it before `--export-release` in every build script (details in [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md)).
3. **Import settings drift is a review problem.** Nothing *technically* stops a teammate importing one sprite as Lossy. Defend with (a) Import Defaults set project-wide, (b) `.import` diffs reviewed like code, and (c) optionally a CI grep asserting `compress/mode=0` across `assets/sprites/**/*.import` — a two-line script that has caught real regressions.

> ✅ **Best practice** — Treat the pair *(source file, `.import` file)* as one atomic unit in every operation: commits, moves, deletions, code review. Half the "mysterious asset breakage" in team projects is these two files getting separated.

### What actually ships in an export

When you export the project, Godot packs the **imported artifacts** (`.ctex` from `.godot/imported/`), not your PNGs (unless "Keep File" was chosen). This means: import options are burned into the shipped data; there is no "reimport on the player's machine". The export dialog additionally lets you transcode texture formats per platform (e.g. ETC2/ASTC for mobile targets) — see [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md).

---

## Compression modes explained

`compress/mode` is the single most consequential import option. It decides how pixels are stored on disk **and** in VRAM, and it is where pixel art most often gets damaged. The five modes:

### Lossless (mode 0)

Pixels are stored exactly; the file is compressed like a ZIP (internally PNG or lossless WebP — the `compress/lossless_force_png` option forces PNG when WebP is undesirable). On the GPU the texture is **fully uncompressed** (e.g. RGBA8, 4 bytes per pixel).

- **Quality:** perfect, bit-for-bit.
- **Disk:** good compression for typical art.
- **VRAM:** highest — no GPU-side compression at all.
- **Use for:** all pixel art, UI, small/medium 2D sprites. **This is the correct default for 2D** and the standard for every sprite in Relax Room.

### Lossy (mode 1)

Stored as lossy WebP at `compress/lossy_quality` (default 0.7). Decompressed to full RGBA8 in VRAM — identical VRAM cost to Lossless; only the *download/disk* size shrinks.

- **Quality:** artifacts possible; edges and flat colors of pixel art show them first.
- **Use for:** very large photographic 2D assets (backdrops, splash art) where disk size matters and VRAM does not. Never for pixel art.

### VRAM Compressed (mode 2)

Encoded with a GPU block-compression codec — S3TC/BPTC on desktop, ETC2/ASTC on mobile. These codecs store each **4×4 pixel block** in a few bytes by approximating its colors with two endpoints and per-pixel interpolation weights.

- **Quality:** visible artifacts on hard edges, gradients and flat-color regions — i.e., exactly what pixel art is made of. A 1-pixel black outline through a 4×4 block simply cannot be represented faithfully.
- **VRAM:** 4-6× smaller than uncompressed. Also **uploads faster** and samples cheaper on bandwidth.
- **Use for:** 3D textures (albedo, normal, ORM), very large 2D backgrounds in HD art styles where mild artifacts are invisible. **Never for pixel art.**
- `compress/high_quality=true` switches desktop encoding from S3TC to BPTC (and mobile to ASTC) — better quality, larger, Forward+/Mobile renderers only.

Why block codecs and pixel art are fundamentally incompatible — schematically, one 4×4 block from a character's face where a black outline meets blue clothing and skin tones:

```
Source block (4×4):                 Block-compressed reconstruction:
┌────┬────┬────┬────┐               ┌────┬────┬────┬────┐
│blue│blue│ BLK│skin│  codec keeps  │blue│blue│gray│skin│
│blue│ BLK│skin│skin│  only TWO     │blue│gray│skin│skin│
│ BLK│skin│skin│skin│  endpoint     │gray│skin│skin│skin│
│skin│skin│skin│skin│  colors +     │skin│skin│skin│skin│
└────┴────┴────┴────┘  blend weights└────┴────┴────┴────┘
```

S3TC-class codecs store two endpoint colors per block and reconstruct every pixel as a blend of them. A block containing *three* unrelated hues (outline black, blue, skin) mathematically cannot round-trip: one hue becomes a blend of the others — the outline turns muddy gray, exactly the smeared look reported as "my sprite got dirty". HD art survives because neighboring pixels are already similar; pixel art, defined by maximal per-pixel contrast, is the codec's worst case by construction.

### VRAM Uncompressed (mode 3)

Raw pixels in VRAM, minimal processing on disk. Mostly relevant for float/HDR formats that block codecs cannot hold. Rarely chosen manually for 2D — Lossless already gives raw VRAM with better disk size.

### Basis Universal (mode 4)

A "transcodable" compressed format: one small file on disk that the engine transcodes at load time to whatever block format the local GPU prefers. Excellent download size for multi-platform 3D-heavy projects; slower imports and slightly lower quality than direct VRAM compression. Not relevant to a desktop pixel-art project.

### Side-by-side

| | Lossless | Lossy | VRAM Compressed | VRAM Uncompr. | Basis Universal |
|---|---|---|---|---|---|
| `compress/mode` | 0 | 1 | 2 | 3 | 4 |
| Pixel fidelity | perfect | artifacts | block artifacts | perfect | block artifacts |
| Disk size | medium | small | small | large | smallest |
| VRAM size | full | full | **4-6× less** | full | 4-6× less |
| Load cost | decode PNG/WebP | decode WebP | direct upload | direct upload | transcode |
| Pixel art | ✅ **the choice** | ❌ | ❌❌ | acceptable, pointless | ❌ |
| HD 2D art | ✅ small/med | ✅ large assets | ⚠️ backdrops only | ❌ wasteful | ⚠️ niche |
| 3D textures | ⚠️ VRAM-hungry | ⚠️ | ✅ **the choice** | HDR panoramas | ✅ web/mobile |

> ⚠️ **Pitfall** — "VRAM Compressed made my game *slower* to look worse!" is a real report pattern from 2D devs: for small sprites the VRAM savings are negligible (a 32×32 sprite is 4 KiB uncompressed — there is nothing to save), while the artifacts are maximal. VRAM compression earns its keep on 1024×1024-and-up 3D textures, not on sprite sheets.

> ✅ **Best practice** — Decide compression **per asset class, once**, and encode the decision in Import Defaults + a line in your project's `CONTRIBUTING`/art bible: *"All sprites: Lossless, no mipmaps. All splash art ≥1024px: Lossy 0.8. No VRAM compression anywhere (2D-only project)."* Relax Room's art bible says exactly this.

---

## Filtering, mipmaps and color space

Compression decides how pixels are *stored*; filtering decides how they are *sampled* when a texture is drawn larger, smaller, rotated or at a fractional position. This is where "why is my pixel art blurry?" is usually answered.

### Nearest vs linear

When a texture is not drawn exactly 1:1, the GPU must decide what color a screen pixel gets when it falls "between" texels:

- **Nearest (nearest-neighbor):** take the single closest texel. Result: hard, crisp, blocky — pixels stay pixels. Scaling 32×32 → 128×128 yields perfect 4×4 blocks per source pixel.
- **Linear (bilinear):** blend the four surrounding texels weighted by distance. Result: smooth gradients — ideal for HD art and photos, fatal for pixel art (every edge becomes a 2-pixel gradient of mush).

### Where filtering is configured in Godot 4 (not the importer!)

This is the biggest 3.x → 4.x relocation. Filtering has **two levels**:

**1. Project default** — Project Settings → Rendering → Textures → Canvas Textures → **Default Texture Filter**:

```ini
# project.godot — the pixel-art setting:
[rendering]
textures/canvas_textures/default_texture_filter=0
# 0 = Nearest · 1 = Linear (engine default) · 2 = Linear Mipmap · 3 = Nearest Mipmap
```

**2. Per-node override** — every `CanvasItem` (so every 2D node and Control) has `texture_filter`:

```gdscript
# CanvasItem.TextureFilter — the full enum:
# TEXTURE_FILTER_PARENT_NODE (0)  inherit from parent; root inherits the project default
# TEXTURE_FILTER_NEAREST (1)      crisp — pixel art
# TEXTURE_FILTER_LINEAR (2)       smooth — HD art
# TEXTURE_FILTER_NEAREST_WITH_MIPMAPS (3)
# TEXTURE_FILTER_LINEAR_WITH_MIPMAPS (4)
# TEXTURE_FILTER_NEAREST_WITH_MIPMAPS_ANISOTROPIC (5)
# TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC (6)

sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
```

The default value `TEXTURE_FILTER_PARENT_NODE` cascades down the tree until something overrides it, ultimately falling back to the project setting. This gives you an elegant pattern: set the **project** to Nearest for the pixel-art world, and override to Linear on the one `Control` subtree that shows smooth photographic content (or vice versa for HD games with a retro minigame).

All seven modes, mapped to decisions:

| Filter mode | Magnified | Minified | When you actually pick it |
|---|---|---|---|
| `PARENT_NODE` | inherits | inherits | the default — leave it unless this node is an exception |
| `NEAREST` | crisp blocks | texel-skipping (shimmer if heavily downscaled) | pixel art at ≥1× scale — the workhorse |
| `LINEAR` | smooth blur | smooth (still shimmers when tiny) | HD art, photos, smooth UI |
| `NEAREST_WITH_MIPMAPS` | crisp | mip-blended | pixel art a camera zooms far *out* from (rare; mips blur the aesthetic anyway) |
| `LINEAR_WITH_MIPMAPS` | smooth | mip-blended, stable | HD art under a zooming `Camera2D` — the "2D game with real zoom" setting |
| `NEAREST_WITH_MIPMAPS_ANISOTROPIC` | crisp | angle-aware mips | strongly skewed/rotated pixel art being minified (exotic) |
| `LINEAR_WITH_MIPMAPS_ANISOTROPIC` | smooth | angle-aware mips | perspective-skewed 2D (mode-7 style floors, sheared cards) |

Remember the coupling from the mipmap discussion below: every `_WITH_MIPMAPS` mode silently degrades to its non-mip cousin on textures imported without `mipmaps/generate=true`. And note that `Control` nodes are `CanvasItem`s too — the same `texture_filter` property and the same project default govern your UI, which is why a pixel-art project's *smooth* logo may need an explicit per-node `LINEAR` override.

`texture_repeat` works identically (`TEXTURE_REPEAT_PARENT_NODE` / `TEXTURE_REPEAT_DISABLED` / `TEXTURE_REPEAT_ENABLED` / `TEXTURE_REPEAT_MIRROR`, project default `rendering/textures/canvas_textures/default_texture_repeat`, engine default Disabled). Repeat matters for scrolling backgrounds via UV offsets; for spritesheets it must stay **Disabled** or edge sampling can wrap to the opposite side of the sheet.

> ⚠️ **Pitfall** — Setting `texture_filter` on a parent `Node2D` does *not* help a child whose own `texture_filter` was explicitly set to something other than `PARENT_NODE`. When a single sprite stays blurry in an otherwise crisp scene, inspect *that node's* `texture_filter` — someone probably hard-set it to Linear.

### Mipmaps — what they are, when 2D wants them

Mipmaps are a precomputed chain of half-resolution copies (256 → 128 → 64 → …) stored with the texture (+~33% memory). When the GPU draws a texture *smaller* than native, it samples the appropriately-sized mip level instead of skipping texels, eliminating shimmering/graininess ("minification aliasing").

In 2D, mipmaps are off by default and usually should stay off. Turn them on (`mipmaps/generate=true` at import **and** a `_WITH_MIPMAPS` filter on the node) only when you *significantly downscale* at runtime: a zooming `Camera2D` over HD art, world-map thumbnails of large images. Note the coupling — imported mipmaps do nothing unless the node's filter mode actually uses them, and a `_WITH_MIPMAPS` filter does nothing if the import didn't generate them.

For pixel art, mipmaps are always wrong: each mip level is a *blurred average* of your art, so any minification instantly abandons the crisp aesthetic. Keep the camera at integer zooms instead.

### sRGB and color space in 2D

Godot 4 renders 3D in linear color space and converts for display, but **2D canvas rendering operates in sRGB space** — your PNG's bytes are the values that get blended. Practical consequences for a 2D project:

- What you see in Aseprite/Photoshop (sRGB) is what you get; no washed-out surprises. `process/hdr_as_srgb` and friends are for 3D/HDR sources.
- Alpha blending in sRGB is technically "wrong" (midtones darken slightly) but it is the retro/2D-standard look everyone expects.
- Godot 4.2+ offers **HDR in 2D** (`rendering/viewport/hdr_2d=true`) enabling glow and values >1.0 in canvas rendering, at extra bandwidth cost — an aesthetic tool for neon-style games, off by default and off in Relax Room.

### `process/fix_alpha_border` — the dark-fringe killer

When a sprite has transparent regions, the RGB values of fully-transparent pixels are undefined — many editors write black there. With linear filtering (or scaling/rotation), the GPU blends edge texels with those invisible black neighbors, producing an ugly dark outline. `fix_alpha_border=true` (default on) flood-fills transparent pixels near edges with the color of their opaque neighbors, so any blending picks up sensible colors. Keep it on; it is free insurance — even for Nearest-filtered art that might ever be rotated or scaled non-integrally.

---

## Pixel-art configuration recipe

Everything above condenses into a checklist you can apply to a fresh project in ten minutes. This is the exact recipe behind Relax Room, and it matches current community consensus (see Further reading) and the official *Multiple resolutions* guidance.

### Step 1 — Rendering defaults

Project Settings → Rendering → Textures → Canvas Textures:

```ini
[rendering]
textures/canvas_textures/default_texture_filter=0   ; Nearest
; default_texture_repeat stays 0 (Disabled)
```

Every sprite in the project is now crisp by default; no per-node fiddling, no per-import fiddling.

### Step 2 — Pixel snapping

Project Settings → Rendering → 2D → Snap (enable *Advanced Settings* to see them):

```ini
[rendering]
2d/snap/snap_2d_transforms_to_pixel=true
2d/snap/snap_2d_vertices_to_pixel=false    ; second line of defense — see below
```

Why: with a smoothly-following `Camera2D`, node positions end up at fractional pixels (`x = 12.34`). The GPU then samples between texels and neighboring sprites disagree about where a "pixel" is — the result is the infamous **wobble/shimmer/jitter** during scrolling, and 1-pixel gaps flickering between tiles.

- `snap_2d_transforms_to_pixel` rounds each CanvasItem's **final rendered transform** to whole pixels. It fixes 95% of wobble and is the primary switch. (Since 4.3 the rounding is stabilized — it rounds half-to-even consistently, eliminating the frame-to-frame flip-flop older versions showed.)
- `snap_2d_vertices_to_pixel` additionally snaps every **vertex**. Enable it only if rotated/scaled elements still shimmer — it is more aggressive and can distort non-pixel-art geometry (particles, smooth UI). Start with it off.

Neither setting changes your actual node positions — physics and logic still run at full float precision; only rendering snaps.

> ⚠️ **Pitfall** — Do not confuse these runtime settings with the editor toolbar's **Use Pixel Snap** (grid snapping while *placing* nodes in the 2D editor). That one only affects your editing gestures; it does nothing at runtime.

### Step 3 — Base resolution and stretch

Project Settings → Display → Window:

```ini
[display]
window/size/viewport_width=640
window/size/viewport_height=360
window/stretch/mode="viewport"
window/stretch/aspect="keep"          ; or "expand" to support multiple ratios
window/stretch/scale_mode="integer"
```

Reasoning, setting by setting:

- **Base resolution 640×360** is the official recommendation for pixel art: it multiplies cleanly into 1280×720 (2×), 1920×1080 (3×), 2560×1440 (4×) and 3840×2160 (6×) — every mainstream 16:9 monitor gets an exact integer scale with zero black bars. Other classic choices: 320×180 (chunkier), 480×270.
- **`stretch/mode = "viewport"`**: the game renders into an off-screen viewport at *exactly* the base resolution, then that finished low-res frame is scaled to the window. Sub-pixel positions cannot exist in the output — the entire frame is authentically low-res, rotations become chunky "as if drawn in the sprite", and the pixel grid is globally consistent. The alternative `"canvas_items"` renders each item at the *target* resolution and scales coordinates instead — smoother motion (sub-pixel scrolling is possible) and sharper rotated edges, at the cost of a less strict retro look and per-item rounding artifacts. Both are defensible for pixel art; `viewport` is the purist default, `canvas_items` + snap settings is the pragmatic hybrid many modern pixel-art games use. **Pick one and test scrolling early.**
- **`scale_mode = "integer"`** forces the final upscale to whole multiples (2×, 3×, 4×…), letterboxing the remainder. Fractional scaling (e.g. 2.5×) makes some source pixels 2 screen pixels wide and others 3 — visibly uneven "wobbly" pixels. Integer scaling is non-negotiable for strict pixel art.
- **`aspect = "keep"`** letterboxes non-16:9 displays; `"expand"` instead reveals more world. Expand is friendlier on ultrawide/phone-shaped windows but means your UI must tolerate variable visible area — see [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md).

### Deep dive — `viewport` vs `canvas_items` for pixel art

The two stretch modes embody two philosophies of what "pixel art on a modern monitor" means, and the choice ripples through motion feel, UI text and rotation. The full contrast:

| Aspect | `viewport` | `canvas_items` |
|---|---|---|
| What renders at base resolution | **everything** — the whole frame is truly 640×360, then upscaled once | nothing — items render at window resolution with scaled coordinates |
| Sub-pixel motion | impossible; global pixel grid; motion is chunky-but-coherent | possible; scrolling is butter-smooth; needs snap settings to avoid wobble |
| Rotated / scaled sprites | rotate *within* the low-res grid — authentically chunky edges | rotate at display resolution — smooth edges that can look "off-grid" |
| UI text and fonts | low-res and chunky (authentic, sometimes illegible) | crisp at native resolution — huge win for text-heavy games |
| Mixed art styles | everything forced low-res | HD UI over pixel-art world works naturally |
| GPU cost | renders ~0.03× the pixels of 4K + one upscale blit — cheapest | full-resolution canvas rendering |
| Failure mode | fractional window scale → uneven pixels (fix: `scale_mode = integer`) | forgotten snap settings → shimmer; per-item rounding artifacts |

The **hybrid architecture** used by many modern releases gives you both: project stretch stays `canvas_items` (or `disabled`), the *game world* renders inside a `SubViewport` sized at the base resolution with Nearest filtering and integer scale, and the UI lives outside it at native resolution. That is more moving parts than a foundations module needs, but knowing it exists prevents "we must choose between crisp text and crisp pixels" paralysis — you don't. Relax Room uses plain `viewport` stretch: its UI is itself pixel art, so the trade-off costs nothing.

One further nuance: keep game logic in floats regardless. Positions like `x = 12.34` are *correct* — snapping belongs to rendering (step 2), never to physics or logic. Projects that `round()` positions every frame fight their own movement code (acceleration under 1 px/frame rounds to zero motion) for a benefit the snap settings already deliver for free.

### Step 4 — Import defaults

Project Settings → Import Defaults → Texture2D: Compress Mode **Lossless**, Mipmaps Generate **Off**, Fix Alpha Border **On**, Detect 3D → Compress To **Disabled** (2D-only project). Reimport any pre-existing assets.

### Step 5 — Camera discipline

Even with snapping enabled, camera habits matter:

```gdscript
# A pixel-art-friendly follow camera.
extends Camera2D

@export var follow_speed: float = 8.0
var _target: Node2D

func _process(delta: float) -> void:
    if _target == null:
        return
    # Smooth-follow in float space… the snap settings handle rendering.
    global_position = global_position.lerp(_target.global_position, 1.0 - exp(-follow_speed * delta))
```

Keep `Camera2D.zoom` at integer values (`Vector2(3, 3)`, not `Vector2(2.5, 2.5)`) unless you deliberately want a fractional-zoom effect; fractional zoom reintroduces uneven pixels no matter what the stretch settings say.

### The whole recipe as one `project.godot` block

For reference (and for pasting into new prototypes), every setting from steps 1-3 in its serialized form — this is the diff the recipe produces against a fresh project:

```ini
config_version=5

[display]

window/size/viewport_width=640
window/size/viewport_height=360
window/stretch/mode="viewport"
window/stretch/aspect="keep"
window/stretch/scale_mode="integer"

[rendering]

textures/canvas_textures/default_texture_filter=0
2d/snap/snap_2d_transforms_to_pixel=true
```

Absent lines mean engine defaults are already correct: `default_texture_repeat` defaults to Disabled, `snap_2d_vertices_to_pixel` stays `false` until shimmer evidence demands it, and step 4's import defaults live in the editor's Import Defaults store, not in `project.godot`. Reviewing a teammate's "pixel art setup" PR reduces to checking this block plus the Import Defaults screenshot.

### The blur diagnosis table

Every cause of blurry/wobbly pixel art maps to one recipe step:

| Symptom | Cause | Recipe step |
|---|---|---|
| Uniform blur when scaled | Linear filter active | Step 1 (or node `texture_filter`) |
| Blur + blocky smearing | VRAM Compressed import (often via detect_3d) | Step 4 |
| Shimmer/wobble while camera moves | Sub-pixel transforms, no snapping | Step 2 |
| Some pixels fatter than others | Fractional scale (window or zoom) | Step 3 / Step 5 |
| Dark outline at sprite edges | `fix_alpha_border` off + filtering | Step 4 |
| Crisp at 1× but soft in full screen | `canvas_items` stretch + fractional scale | Step 3 |
| One sprite blurry, rest fine | Per-node `texture_filter` override to Linear | inspect the node |
| Blurry only in editor preview | Editor zoom is fractional — harmless | run the project (F5) |

---

## Sprite2D deep dive

`Sprite2D` is the fundamental "draw a texture at this transform" node — a `Node2D` with a texture, some slicing options, and virtually zero overhead. Most of what looks like exotic sprite behavior (sheet slicing, atlas regions, flipping, tinting) is built into this one node.

### Property reference

| Property | Type | Default | Meaning |
|---|---|---|---|
| `texture` | `Texture2D` | `null` | The texture to draw (any `Texture2D` subclass) |
| `centered` | `bool` | `true` | If `true`, texture is centered on the node origin; if `false`, top-left corner sits at the origin |
| `offset` | `Vector2` | `(0, 0)` | Drawing offset applied on top of the position (in texture pixels, pre-scale) |
| `flip_h` / `flip_v` | `bool` | `false` | Mirror horizontally / vertically |
| `hframes` / `vframes` | `int` | 1 / 1 | Slice the texture into a grid of columns / rows |
| `frame` | `int` | 0 | Which grid cell to display (row-major, 0-based) |
| `frame_coords` | `Vector2i` | `(0, 0)` | The same cell addressed as (column, row) |
| `region_enabled` | `bool` | `false` | Draw only `region_rect` of the texture |
| `region_rect` | `Rect2` | `(0,0,0,0)` | The sub-rectangle to draw when region is enabled |
| `region_filter_clip_enabled` | `bool` | `false` | Clamp sampling to the region — anti-bleeding with linear filter |

Signals: `frame_changed()` and `texture_changed()`. Useful methods: `get_rect()` (local-space bounds — handy for click detection and placement math) and `is_pixel_opaque(pos)` (per-pixel hit testing for irregular shapes).

```gdscript
# Creating a sprite fully from code — the Relax Room decoration pattern:
var sprite := Sprite2D.new()
sprite.texture = load("res://assets/room/room.png")
sprite.centered = true
sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST  # explicit, though project default covers it
sprite.scale = Vector2(4.0, 4.0)                            # uniform integer scale
add_child(sprite)
```

### `centered` and `offset` — controlling the anchor

`centered = true` (default) puts the texture's center on the node origin — natural for characters that rotate or flip in place. `centered = false` anchors the top-left corner — natural for grid/tile placement where "position" should mean "the cell's corner".

`offset` shifts drawing without moving the node — the classic use is aligning a character's *feet* to the node origin so Y-sorting and shadows behave:

```gdscript
# 32×48 character in a 64×64 frame: anchor the feet at the node origin.
sprite.centered = false
sprite.offset = Vector2(-32, -60)   # texture drawn so the feet line lands on (0, 0)
```

> ✅ **Best practice** — Decide a per-asset-class anchor convention early (Relax Room: *characters centered, decorations top-left*) and write it down. Mixed conventions in one scene make every placement computation a special case.

### `flip_h` / `flip_v` — free mirroring

Flipping costs nothing and halves your art budget for side views: author the right-facing walk, set `flip_h = true` when moving left. Two caveats: (1) asymmetric details (a sword always in the right hand) visibly swap sides — accept it or author both directions; (2) `flip_h` mirrors around the sprite's own anchor, so with `centered = false` the sprite visually jumps — with flipping, prefer `centered = true` or compensate via `offset`.

Flipping the node with `scale.x = -1` also works but inverts the whole child transform (children, collision shapes, particles all mirror too) and can surprise physics; for the sprite alone, `flip_h` is the cleaner tool.

### `hframes` / `vframes` / `frame` — the built-in spritesheet slicer

When one texture holds a uniform grid of frames, `Sprite2D` slices it without any `AtlasTexture`:

```gdscript
# male_walk_side.png is a 128×32 strip: 4 frames of 32×32.
sprite.texture = preload("res://assets/charachters/male/old/male_walk/male_walk_side.png")
sprite.hframes = 4
sprite.vframes = 1
sprite.frame = 0

# Manual animation — advance one frame:
sprite.frame = (sprite.frame + 1) % (sprite.hframes * sprite.vframes)

# Addressing a multi-row sheet by (column, row) is clearer than flat math:
sprite.frame_coords = Vector2i(2, 1)    # column 2, row 1  ==  frame = 1 * hframes + 2
```

`frame` is row-major: with `hframes = 4`, frame 5 is row 1, column 1. `frame_coords` expresses the same thing two-dimensionally and prevents the classic off-by-one bugs. This mechanism is also exactly what `AnimationPlayer` keys when it animates sprites (§13) — which is why the humble `frame` property matters more than it looks.

> ⚠️ **Pitfall** — `hframes`/`vframes` assume a *perfectly uniform grid with no padding*. If your sheet has margins between frames or mixed cell sizes, the slice boundaries land mid-pixel-art. Non-uniform sheets need `AtlasTexture` regions (§9) or region_rect.

Since sheet-slicing overlaps `AnimatedSprite2D`'s territory, the head-to-head (previewing §11-§12):

| Criterion | `AnimatedSprite2D` | `Sprite2D` + `hframes` |
|---|---|---|
| Multiple named animations | ✅ N named animations in one resource | ❌ one grid at a time |
| Playback control | `play("name")`, autoplay, loop flags, signals | manual — Timer/Tween/code drives `frame` |
| Per-animation speeds | ✅ fps per animation + per-frame durations | ❌ whatever your driver does |
| Overhead | small (frame clock, resource) | essentially none |
| Sweet spot | characters and anything stateful | one-loop props, effects, UI bits, precise custom timing |

### Which node displays this image? — placement cheat sheet

`Sprite2D` is not the only texture-bearing node, and picking by habit instead of by role produces layout fights (world nodes in UI) or transform fights (UI nodes in world). The map:

| Node | Space | Role |
|---|---|---|
| `Sprite2D` | world (`Node2D`) | a positioned/rotated/scaled object in the scene |
| `AnimatedSprite2D` | world | the same, with built-in flipbook playback (§11) |
| `TileMapLayer` | world | grid-repeated level geometry — never build floors from Sprite2Ds ([TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md)) |
| `TextureRect` | UI (`Control`) | an image inside a layout container (§15) |
| `NinePatchRect` | UI | resizable frame/panel art (§15) |
| `TextureButton` | UI | clickable art with per-state textures (normal/hover/pressed) |
| `GPUParticles2D` | world | many short-lived textured quads with simulated motion |
| `CanvasItem._draw()` | either | many static images without per-node cost (§2) |

Rule of thumb: **if a container should be able to move or resize it, it is a Control-family node; if the camera should affect it, it is a Node2D-family node.** Mixing them compiles fine and behaves badly — the classic symptom is UI art that scrolls away with the camera.

### `region_*` — draw a sub-rectangle directly

`region_enabled + region_rect` makes the sprite draw an arbitrary rectangle of the texture — like an inline `AtlasTexture` without a separate resource:

```gdscript
sprite.region_enabled = true
sprite.region_rect = Rect2(64, 0, 32, 32)      # third 32×32 frame of a strip
sprite.region_filter_clip_enabled = true       # clamp sampling — no neighbor bleeding
```

Use `region_rect` for one-off crops (e.g. showing a slice of a big illustration); use `AtlasTexture` when the crop should be a *reusable resource* shared by multiple consumers. A second, underrated use: with `texture_repeat = TEXTURE_REPEAT_ENABLED` and a `region_rect` larger than the texture, `Sprite2D` tiles the texture across the region — an instant scrolling-background primitive:

```gdscript
extends Sprite2D
## Endless scrolling background from one small tileable texture.
## Texture: a seamless 64×64 sky/pattern tile. No duplicated nodes, no wrapping math.

@export var scroll_speed := Vector2(20.0, 0.0)   # pixels/second

func _ready() -> void:
    texture = preload("res://assets/backgrounds/clouds_tile.png")
    texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED   # allow sampling outside 0-1
    region_enabled = true
    # Cover the whole base resolution (plus one tile of slack for the scroll):
    region_rect = Rect2(0, 0, 640 + 64, 360 + 64)

func _process(delta: float) -> void:
    # Sliding the region's origin shifts WHICH part of the (repeating) texture
    # shows — the sprite itself never moves. fposmod keeps numbers small forever.
    region_rect.position.x = fposmod(region_rect.position.x + scroll_speed.x * delta, 64.0)
    region_rect.position.y = fposmod(region_rect.position.y + scroll_speed.y * delta, 64.0)
```

This is the cheapest scrolling background Godot can express — one node, one draw, no per-frame allocation. Layer two or three at different speeds for parallax (or use `Parallax2D`, which packages the same idea with camera coupling). Note the deliberate exception to the "repeat Disabled" default: *tileable* art is the one place repeat belongs on, and setting it per-node keeps the project default safely Disabled for everything else.

### Pixel-perfect click detection with `is_pixel_opaque()`

Desktop-companion apps are click-heavy, and rectangular hit areas feel wrong on irregular sprites (clicking the empty corner of a plant's bounding box should *not* select the plant). `Sprite2D` ships the fix: `get_rect()` for the cheap bounds test, `is_pixel_opaque()` for the exact one — both in the sprite's local space, so one `to_local()` handles position, scale, rotation and flips in a single stroke:

```gdscript
extends Sprite2D
## Emits when the user clicks visible (non-transparent) pixels of this sprite.
signal clicked

func _unhandled_input(event: InputEvent) -> void:
    var mb := event as InputEventMouseButton
    if mb == null or not mb.pressed or mb.button_index != MOUSE_BUTTON_LEFT:
        return
    var local := to_local(get_global_mouse_position())
    if get_rect().has_point(local) and is_pixel_opaque(local):
        clicked.emit()
        get_viewport().set_input_as_handled()   # stop propagation to sprites behind
```

`is_pixel_opaque()` tests against a 1-bit opacity mask Godot derives from the texture's alpha, so it is fast enough for per-click use (not for per-frame sweeps over hundreds of sprites — give those an `Area2D` with a fitted `CollisionShape2D` instead). For overlapping decorations, the `set_input_as_handled()` line plus checking sprites in front-to-back order decides who "wins" the click — the same ordering problem [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md) treats in depth.

### Manual animation — the honest bottom tier

Before reaching for animation nodes, remember that `frame` is just an int. For a background prop with one looping animation, a `Timer` and three lines beat any resource setup (this generic form is exactly what Relax Room's menu character does, §17.2):

```gdscript
extends Sprite2D
## Self-contained flipbook for background props: assign a strip texture,
## set fps, done. No SpriteFrames, no AnimationPlayer.
@export var fps: float = 6.0
@export var columns: int = 4

func _ready() -> void:
    hframes = columns
    var timer := Timer.new()
    timer.wait_time = 1.0 / fps
    timer.autostart = true
    timer.timeout.connect(
        func() -> void: frame = (frame + 1) % (hframes * vframes))
    add_child(timer)
```

The moment requirements grow — a second animation, non-looping playback, per-frame timing — stop extending this script and graduate to `AnimatedSprite2D` (§11). The skill is recognizing the boundary, not defending either side of it.

### Anchors, Y-sorting and the isometric look

In Y-sorted scenes (`Node2D.y_sort_enabled`), drawing order derives from each node's **origin** Y — which is why §8's anchor discussion is not cosmetic. A character whose origin sits at its *feet* (via `centered = false` + `offset`, or a parent node at the feet position) sorts correctly against furniture whose origin sits at its *base edge*; a center-anchored tall sprite pops in front of things it should stand behind whenever its midpoint crosses theirs. The working rule for isometric-flavored rooms: **origin = the point where the object touches the floor**. Full treatment — diamond grids, multi-tile furniture, sort margins — in [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md); this module's contribution is that `offset` is the tool that decouples "where the art draws" from "where the origin sorts".

### `modulate` vs `self_modulate` — tinting

Both multiply the sprite's colors; the difference is scope:

- `modulate` (from `CanvasItem`) — affects this node **and all CanvasItem descendants**. Fading a character *and* its attached hat/labels: animate `modulate.a`.
- `self_modulate` — affects **only this node's own drawing**; children keep their colors.

```gdscript
sprite.modulate = Color(1, 1, 1, 0.5)      # 50% transparent, whole subtree
sprite.self_modulate = Color(1, 0.6, 0.6)  # reddish tint, this sprite only

# Classic hit-flash with a tween (see RENDERING_AND_VISUAL_LOGIC.md for tweens):
func flash_hit() -> void:
    var tw := create_tween()
    sprite.self_modulate = Color(4.0, 4.0, 4.0)   # overbright multiply
    tw.tween_property(sprite, "self_modulate", Color.WHITE, 0.18)
```

Note that modulate is a **multiply**: white (1,1,1) is identity, black zeroes everything, and values above 1.0 over-brighten (visibly, with HDR 2D or glow; clamped otherwise). You cannot *add* color with modulate — a true "flash to solid white" needs a tiny shader (`SHADERS_GDSHADER.md`) or a white duplicate sprite.

---

## AtlasTexture and spritesheets

A **spritesheet** (or atlas) packs many images into one texture. It is first an *authoring* convention (animation strips exported from Aseprite), then a *performance* tool (fewer GPU texture binds → better batching), and finally a *workflow* decision (one file to import and version instead of 400).

### Layout conventions that keep you sane

- **Animation strips:** one row per animation, fixed cell size, left-to-right time order. Relax Room standard: 128×32 strips = 4 frames of 32×32. Trivially sliced by `hframes` or the SpriteFrames sheet importer.
- **Grid sheets:** rows = animations (or directions), columns = frames. Document the row order — "row 0: idle, row 1: walk…" — in the art bible; the engine cannot guess it.
- **Packed atlases:** heterogeneous sprites tightly packed by a tool (TexturePacker, Free Texture Packer, Aseprite export). Maximum density, but cell positions are irregular — you need the tool's JSON/metadata or hand-authored `AtlasTexture` regions.
- **Padding/extrusion:** with linear filtering or mipmaps, adjacent cells bleed into each other at the edges; packers solve this with 1-2 px padding and *edge extrusion* (duplicating border pixels outward). With Nearest filtering, no mipmaps and integer scaling — the pixel-art recipe — bleeding cannot occur and tight packing is safe.

> ✅ **Best practice** — Keep cell sizes power-of-two-ish and consistent per asset class (16, 32, 48, 64). Not because GPUs still require power-of-two textures (they don't), but because uniform cells make slicing, packing and placement math trivial and mistakes visible at a glance.

### Authoring flow — from Aseprite to Godot

The de-facto pixel-art tool, Aseprite, exports both halves of the atlas story. The manual route: *File → Export Sprite Sheet*, sheet type **Horizontal Strip** (for the one-row convention) or **By Rows** with *Tags as rows* (each animation tag becomes a row). The automated route belongs in a build script:

```bash
# One .ase file → sheet + metadata, deterministic, CI-friendly:
aseprite -b male_walk.ase \
    --sheet male_walk.png \
    --sheet-type horizontal \
    --data male_walk.json --format json-hash \
    --list-tags
```

`--list-tags` writes the animation-tag ranges (name, from-frame, to-frame, direction) into the JSON — exactly the metadata a build script needs to generate `SpriteFrames` automatically (§11's `build_frames` pattern) instead of hand-clicking the sheet importer after every re-export. The full loop — artist saves `.ase`, script re-exports sheet + rebuilds frames, engine hot-reloads — is how animation-heavy teams keep iteration under a minute. Keep `.ase` sources in the repo marked **Skip File** in the Import dock (§4): versioned for artists, invisible to exports.

### AtlasTexture in practice

```gdscript
# Slice one 128×32 strip into four reusable frame textures:
var frames: Array[AtlasTexture] = []
var sheet: Texture2D = preload("res://assets/charachters/male/old/male_idle/male_idle_down.png")
for i in 4:
    var at := AtlasTexture.new()
    at.atlas = sheet
    at.region = Rect2(i * 32, 0, 32, 32)
    at.filter_clip = true            # belt-and-braces against bleeding
    frames.append(at)

$Sprite2D.texture = frames[0]        # AtlasTexture is a Texture2D — drop-in anywhere
```

Because `AtlasTexture` *is a* `Texture2D`, every consumer works unchanged: `Sprite2D.texture`, `SpriteFrames` frames, `TextureRect.texture`, `Button.icon`, custom `draw_texture()` calls. Godot itself leans on this: when you build `SpriteFrames` animations from a spritesheet in the editor, the generated `.tscn` contains one `AtlasTexture` sub-resource per frame:

```
[sub_resource type="AtlasTexture" id="AtlasTexture_1"]
atlas = ExtResource("male_idle_down.png")    ; the 128×32 strip
region = Rect2(0, 0, 32, 32)                 ; frame 0

[sub_resource type="AtlasTexture" id="AtlasTexture_2"]
atlas = ExtResource("male_idle_down.png")
region = Rect2(32, 0, 32, 32)                ; frame 1
```

The `margin` property adds virtual empty space around the region — useful when a packer *trimmed* transparent borders off a sprite and you must restore its original footprint so animation frames don't shift.

### The "Import as TextureAtlas" alternative

The Import dock also offers importing an image as **TextureAtlas**: you assign each PNG a shared atlas file, and Godot merges them into one texture at import time, replacing each source with an `AtlasTexture` pointing into the merged sheet. Your scenes keep referencing individual files while the GPU sees one texture. It is a low-friction way to retrofit atlasing onto a project authored as loose files — at the cost of less control over packing than a dedicated tool.

### Consuming a packed atlas — TexturePacker-style JSON

Dedicated packers (TexturePacker, Free Texture Packer, Aseprite's JSON export) emit a sheet plus metadata describing each packed sprite's rectangle — and, when *trimming* is enabled, how much transparent border was cut so you can restore the original footprint. A loader is ~30 lines and turns the whole sheet into a name → `AtlasTexture` dictionary:

```gdscript
## Loads a packed atlas (TexturePacker "JSON Hash" style) into named AtlasTextures.
## Handles trimmed sprites by restoring their original size via AtlasTexture.margin.
class_name PackedAtlas
extends RefCounted

var _frames: Dictionary[String, AtlasTexture] = {}

func _init(sheet_path: String, json_path: String) -> void:
    var sheet: Texture2D = load(sheet_path)
    var json_text := FileAccess.get_file_as_string(json_path)
    var data: Dictionary = JSON.parse_string(json_text)
    for sprite_name: String in data["frames"]:
        var entry: Dictionary = data["frames"][sprite_name]
        var f: Dictionary = entry["frame"]                     # rect inside the sheet
        var at := AtlasTexture.new()
        at.atlas = sheet
        at.region = Rect2(f["x"], f["y"], f["w"], f["h"])
        if entry.get("trimmed", false):
            var src: Dictionary = entry["spriteSourceSize"]    # offset within original
            var full: Dictionary = entry["sourceSize"]         # original untrimmed size
            at.margin = Rect2(src["x"], src["y"],
                    full["w"] - f["w"], full["h"] - f["h"])
        _frames[sprite_name] = at

func get_texture(sprite_name: String) -> AtlasTexture:
    assert(_frames.has(sprite_name), "Unknown atlas sprite: " + sprite_name)
    return _frames[sprite_name]

# Usage:
# var atlas := PackedAtlas.new("res://assets/packed/props.png",
#                              "res://assets/packed/props.json")
# $Sprite2D.texture = atlas.get_texture("plant_big.png")
```

The `margin` handling is the subtle part: without it, trimmed sprites of one animation visibly *jump* between frames because each frame lost a different amount of transparent border. `margin.position` re-pads the left/top, `margin.size` restores the missing total width/height — the sprite occupies its original footprint again and frame-to-frame alignment survives packing.

> ✅ **Best practice** — Wire the packer into the build, not the artist. A watch script (or pre-commit step) that regenerates `props.png` + `props.json` from a `raw_sprites/` folder keeps "add a sprite" a one-file operation and makes the atlas an *artifact*, never a hand-edited source.

### Atlas vs separate files — the real trade-offs

| Criterion | One atlas | Separate PNGs |
|---|---|---|
| Draw-call batching | ✅ consecutive sprites share the texture → batch | ❌ texture switch per different sprite breaks batches |
| Load overhead | one file open/decode | hundreds of small opens |
| Artist iteration | re-export whole sheet on any change | touch only the changed sprite |
| Version-control diffs | whole-sheet binary diff | per-sprite diffs, fewer conflicts |
| Engine tooling | needs regions/metadata | drag-and-drop simplicity |
| Memory granularity | whole atlas always resident | unused sprites can stay unloaded |

The production pattern that falls out: **atlas what animates together** (a character's frames live and load as one unit anyway), **keep independent things separate** while iterating (decorations that artists add weekly), and **pack for release** if measurements (§10, §16) show texture switches or load times actually hurt. Relax Room follows exactly this: per-animation strips for characters, individual PNGs for furniture.

---

## Draw calls and 2D batching

A **draw call** is one "draw these primitives with this state" command submitted to the GPU. Each call carries CPU-side overhead (validation, state binding), so thousands of tiny calls can bottleneck the CPU while the GPU idles. The 2D renderer defends itself by **batching**: consecutive canvas items that share compatible state — most importantly the **same texture and the same material** — are merged into a single draw call.

The two batch-breakers you control directly:

1. **Texture switches.** Drawing sprite A (texture X), then sprite B (texture Y), then sprite C (texture X) costs three state changes. If A, B and C all sample regions of one atlas, they can merge. This is the performance case for atlases: `AtlasTexture` regions of the same sheet count as *the same texture*.
2. **Material/shader changes.** Every distinct `ShaderMaterial` (or per-instance uniform set) splits batches. A hundred sprites sharing one material batch; a hundred sprites each owning a unique material do not.

Draw order matters too: 2D draws back-to-front following tree order (and `z_index`), so *interleaving* — atlas sprite, off-atlas sprite, atlas sprite — produces more switches than grouping visually-adjacent layers by sheet. You rarely contort a scene for this, but it explains measurements.

### Measuring instead of guessing

```gdscript
# Print the renderer's actual per-frame numbers (also visible in
# Debugger → Monitors while the game runs):
func _process(_delta: float) -> void:
    if Input.is_action_just_pressed("debug_stats"):
        print("draw calls: ", Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
        print("objects:    ", Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME))
        print("primitives: ", Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
```

A healthy 2D pixel-art scene runs in the tens of draw calls. If you see hundreds, look for per-sprite materials or heavy texture interleaving. And keep perspective: **for a scene the size of Relax Room (~dozens of sprites) batching is a non-issue** — this section matters when you scale to thousands of sprites (bullet-hell, particles, huge tilemaps) or target weak hardware. Optimize when the monitor says so, not before. Deeper treatment in [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md).

### Beyond nodes — MultiMeshInstance2D in sixty seconds

When counts climb into the thousands (confetti, falling leaves, bullet-hell patterns), per-node overhead — not draw calls — becomes the bottleneck: every `Sprite2D` is a full scene-tree citizen with transform notifications and processing hooks. `MultiMeshInstance2D` collapses N instances into **one node and one draw call**; you pay by managing transforms yourself:

```gdscript
extends MultiMeshInstance2D
## 2000 drifting leaf sprites in a single draw call.
const COUNT := 2000

var _velocities: PackedVector2Array = PackedVector2Array()

func _ready() -> void:
    texture = preload("res://assets/particles/leaf.png")
    multimesh = MultiMesh.new()
    multimesh.transform_format = MultiMesh.TRANSFORM_2D
    var quad := QuadMesh.new()
    quad.size = Vector2(8, 8)                      # one leaf's world size
    multimesh.mesh = quad
    multimesh.instance_count = COUNT               # set AFTER format/mesh
    _velocities.resize(COUNT)
    for i in COUNT:
        multimesh.set_instance_transform_2d(i,
                Transform2D(randf() * TAU, Vector2(randf() * 640.0, randf() * 360.0)))
        _velocities[i] = Vector2(randf_range(-8, 8), randf_range(10, 30))

func _process(delta: float) -> void:
    for i in COUNT:
        var xform := multimesh.get_instance_transform_2d(i)
        xform.origin += _velocities[i] * delta
        if xform.origin.y > 380.0:
            xform.origin.y = -20.0
        multimesh.set_instance_transform_2d(i, xform)
```

All instances share one texture and material (per-instance variation is limited to `set_instance_color()` and custom data consumed by a shader) — which is exactly why it batches perfectly. For purely decorative effects, compare `GPUParticles2D` first: it moves even the *transform updates* to the GPU. And for cases needing full control without node overhead, `RenderingServer.canvas_item_create()` exposes the renderer directly — the deep end, covered in [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md).

> ✅ **Best practice** — Escalate in order and only on evidence: `Sprite2D`s → shared-atlas `Sprite2D`s → `MultiMeshInstance2D` / `GPUParticles2D` → `RenderingServer`. Each step trades authoring comfort for throughput; jumping straight to the bottom is how prototypes calcify into unmaintainable "engines".

---

## AnimatedSprite2D and SpriteFrames

`AnimatedSprite2D` is the dedicated frame-flipbook node: it owns a `SpriteFrames` resource — a library of named animations, each an ordered list of textures with a playback speed — and steps through frames on its own clock. For characters with a handful of looping animations it is the fastest path from art to motion.

### The data model

```
AnimatedSprite2D                      (node — plays and displays)
  └── sprite_frames: SpriteFrames    (resource — the animation library)
        ├── "idle_down"  → [tex0, tex1, tex2, tex3]   @ 5.0 fps, loop
        ├── "walk_side"  → [tex0, tex1, tex2, tex3]   @ 5.0 fps, loop
        ├── "interact"   → [tex0..tex3]               @ 5.0 fps, no loop
        └── "rotate"     → [tex0..tex7]               @ 3.0 fps, loop
```

Because `SpriteFrames` is a `Resource`, it can be embedded in the scene (default) or saved as a standalone `.tres` and **shared** — e.g. multiple character skins reusing one animation structure, or many instances of the same NPC type sharing frame data instead of duplicating it.

Each frame stores a texture (any `Texture2D` — in sheet-based workflows, an `AtlasTexture`) plus a **relative duration multiplier** (default 1.0): a frame with duration 2.0 displays twice as long as its siblings without changing the animation's fps. Perfect for anticipation poses and impact holds.

### Building animations in the editor

Select the node → *Animations* → `SpriteFrames` → the **SpriteFrames bottom panel** opens:

- **From individual files:** create an animation, drag the frame PNGs into the frame list in order.
- **From a spritesheet:** click **Add frames from a Sprite Sheet**, pick the image, set the grid (horizontal × vertical cell counts), click the cells that belong to the animation, confirm. Godot generates the `AtlasTexture` regions for you.
- Per animation, set **Speed (FPS)**, the **loop** toggle, and optionally **autoplay** (the ▶-on-load icon) so the animation starts without code.

### Controlling playback from GDScript

```gdscript
extends CharacterBody2D

@onready var anim: AnimatedSprite2D = $AnimatedSprite2D

func _ready() -> void:
    anim.play(&"idle_down")               # StringName literals (&"…") for animation names

func update_animation(direction: Vector2) -> void:
    if direction == Vector2.ZERO:
        anim.play(&"idle_down")
        return
    anim.flip_h = direction.x < 0         # mirror for leftward movement
    anim.play(&"walk_side")

func play_hurt() -> void:
    anim.play(&"hurt", 1.5)               # custom_speed: 1.5× this once
    await anim.animation_finished          # non-looping animations emit this at the end
    anim.play(&"idle_down")
```

The API surface worth memorizing:

| Member | Notes |
|---|---|
| `play(name, custom_speed = 1.0, from_end = false)` | Starts (or restarts if a *different* animation was playing) |
| `play_backwards(name)` | Convenience for `play(name, -1.0, true)` |
| `pause()` / `stop()` | Pause keeps position; stop resets to frame 0 |
| `is_playing()` | `false` when stopped, paused or finished |
| `animation: StringName` | Current animation; setting it switches *without* starting playback |
| `frame: int`, `frame_progress: float` | Position within the animation; writable for syncing |
| `set_frame_and_progress(frame, progress)` | Atomic set of both — use when synchronizing two sprites (e.g. body + outfit layers) |
| `speed_scale: float` | Persistent multiplier for everything (`2.0` = double speed; **negative plays backwards**; `0.0` freezes) |
| `get_playing_speed()` | Effective fps × scales, `0.0` if not playing |
| `autoplay: String` | Animation started on entering the tree |

Signals: `animation_finished` (non-looping animation reached its end), `animation_looped` (looping animation wrapped), `frame_changed` (any frame advance — the hook for frame-synced footsteps), `animation_changed`, `sprite_frames_changed`.

> ⚠️ **Pitfall** — Calling `play(&"walk")` every physics frame while already walking is *safe* (it does not restart a playing animation of the same name), but calling `stop()` then `play()` restarts from frame 0 — a character that "moonwalks on frame 0" usually has an over-eager state handler doing exactly that. Guard transitions on `anim.animation != desired` if you also mutate other playback state.

> ⚠️ **Pitfall** — `animation_finished` never fires for looping animations. If your `await anim.animation_finished` hangs forever, check the loop flag on that animation in the SpriteFrames panel.

### Lifecycle notes — autoplay, pause and visibility

Three runtime behaviors worth knowing before they surprise you:

- **Autoplay** is resource-level configuration for script-free scenes: the ▶ icon per animation in the SpriteFrames panel sets `autoplay`, and playback starts when the node enters the tree. Ideal for loading screens and decor (§17.4); for characters, prefer an explicit `play()` in `_ready()` so the initial state lives with the rest of the state logic.
- **Pausing.** `AnimatedSprite2D` advances during normal node processing, so `get_tree().paused` freezes it according to the node's `process_mode` like everything else — a pause menu needs no sprite-specific code. For *selective* freezing (hit-stop on one character), `pause()` (resumable via `play()` without reset) or `speed_scale = 0.0` are the local tools.
- **Visibility does not stop playback.** A sprite with `visible = false` (or simply off-camera) keeps advancing frames and emitting `frame_changed` — rendering is culled, processing is not. Dozens of animated off-screen decorations are usually negligible, but if profiling disagrees, pair a `VisibleOnScreenNotifier2D` with `pause()`/`play()` on its `screen_exited`/`screen_entered` signals.

### Building SpriteFrames from code

For generated content, or to keep animation definitions in data files rather than scenes:

```gdscript
## Builds a SpriteFrames library from horizontal strip textures.
## strips: animation name → { "path": String, "frames": int, "fps": float, "loop": bool }
func build_frames(strips: Dictionary) -> SpriteFrames:
    var sf := SpriteFrames.new()
    sf.remove_animation(&"default")                 # SpriteFrames always starts with "default"
    for anim_name: StringName in strips:
        var info: Dictionary = strips[anim_name]
        var sheet: Texture2D = load(info["path"])
        var frame_w: int = sheet.get_width() / info["frames"]
        sf.add_animation(anim_name)
        sf.set_animation_speed(anim_name, info["fps"])
        sf.set_animation_loop(anim_name, info["loop"])
        for i: int in info["frames"]:
            var at := AtlasTexture.new()
            at.atlas = sheet
            at.region = Rect2(i * frame_w, 0, frame_w, sheet.get_height())
            sf.add_frame(anim_name, at)             # add_frame(anim, texture, duration=1.0, at_position=-1)
    return sf

func _ready() -> void:
    $AnimatedSprite2D.sprite_frames = build_frames({
        &"idle": { "path": "res://assets/charachters/male/old/male_idle/male_idle_down.png",
                   "frames": 4, "fps": 5.0, "loop": true },
        &"walk": { "path": "res://assets/charachters/male/old/male_walk/male_walk_down.png",
                   "frames": 4, "fps": 5.0, "loop": true },
    })
    $AnimatedSprite2D.play(&"idle")
```

The full `SpriteFrames` API mirrors the panel: `add_animation`, `remove_animation`, `rename_animation`, `has_animation`, `get_animation_names`, `set_animation_speed` / `get_animation_speed`, `set_animation_loop` / `get_animation_loop`, `add_frame`, `set_frame`, `remove_frame`, `get_frame_count`, `get_frame_texture`, `get_frame_duration`, `clear`, `clear_all`.

### fps vs `speed_scale` vs per-frame duration — three speed knobs

| Knob | Lives on | Scope | Typical use |
|---|---|---|---|
| Speed (FPS) | `SpriteFrames`, per animation | every instance using the resource | the animation's authored tempo |
| frame duration | `SpriteFrames`, per frame | every instance | holds and snappy frames within one animation |
| `speed_scale` | `AnimatedSprite2D` node | this instance only | gameplay modulation: walk animation speed ∝ velocity, slow-motion, `0.0` to freeze |
| `custom_speed` arg of `play()` | one call | until next `play()` | one-shot variations |

```gdscript
# Scale walk-cycle tempo with actual movement speed:
anim.speed_scale = velocity.length() / max_speed if velocity != Vector2.ZERO else 1.0
```

Author tempo in the resource; modulate per-instance with `speed_scale`. Mixing the two arbitrarily ("this NPC walks at 7 fps because I nudged the resource") makes speeds impossible to reason about later.

### Frame-synced effects with `frame_changed`

Footsteps, dust puffs and cloth swishes must land on *specific frames* of the walk cycle or they read as detached. Polling `frame` in `_process` races the animation clock; the `frame_changed` signal fires exactly when the displayed frame advances:

```gdscript
const FOOTSTEP_FRAMES: Array[int] = [1, 3]   # contact frames in our 4-frame walk

@onready var anim: AnimatedSprite2D = $AnimatedSprite2D
@onready var steps: AudioStreamPlayer2D = $Steps

func _ready() -> void:
    anim.frame_changed.connect(_on_frame_changed)

func _on_frame_changed() -> void:
    if anim.animation.begins_with("walk") and anim.frame in FOOTSTEP_FRAMES:
        steps.pitch_scale = randf_range(0.95, 1.05)   # cheap variation
        steps.play()
```

This scales to two or three sync points per animation. Beyond that — per-frame hitboxes, particle bursts, camera kicks — the constants multiply and drift from the art; that is the threshold where §13's `AnimationPlayer` method tracks, which keep the sync points *on the timeline next to the frames*, become the better design.

### Layered characters — keeping two sprites in lockstep

Customizable characters are usually stacked `AnimatedSprite2D`s: body below, outfit/hair above, each with structurally identical `SpriteFrames` (same animation names, frame counts and fps). The naive sync — call `play()` on both — drifts the moment one node processes before the other or an animation switches mid-frame. The robust sync copies the full playback state through `set_frame_and_progress()`, which exists precisely for this:

```gdscript
@onready var body: AnimatedSprite2D = $Body
@onready var outfit: AnimatedSprite2D = $Outfit

func play_synced(anim_name: StringName) -> void:
    body.play(anim_name)
    outfit.play(anim_name)
    _hard_sync()

func set_flipped(flipped: bool) -> void:
    body.flip_h = flipped
    outfit.flip_h = flipped

func _hard_sync() -> void:
    # Copy frame AND intra-frame progress so the layers can never be
    # half a frame apart, regardless of process order.
    outfit.animation = body.animation
    outfit.set_frame_and_progress(body.frame, body.frame_progress)
```

Call `_hard_sync()` after every `play()` and whenever `speed_scale` changes on the driver. (The heavyweight alternative — one `AnimationPlayer` keyframing both sprites' `frame` properties on a single timeline — removes the sync problem structurally, at the cost of §13's ceremony. Both are legitimate; pick per project and stay consistent.)

### A complete locomotion pattern

Everything in this section composes into the standard production skeleton — a typed state enum, animation selection isolated in one function, `flip_h` mirroring, and velocity-scaled tempo. This is the generalized form of Relax Room's controller (§17.1):

```gdscript
extends CharacterBody2D
## Minimal 4-direction character: AnimatedSprite2D + explicit state.

enum State { IDLE, WALK, INTERACT }

const SPEED := 90.0

@onready var anim: AnimatedSprite2D = $AnimatedSprite2D

var state: State = State.IDLE

func _physics_process(_delta: float) -> void:
    if state == State.INTERACT:
        return                                  # locked until the one-shot ends
    var input := Input.get_vector("move_left", "move_right", "move_up", "move_down")
    velocity = input * SPEED
    move_and_slide()
    _update_state(input)
    _update_animation(input)

func _update_state(input: Vector2) -> void:
    state = State.WALK if input != Vector2.ZERO else State.IDLE

func _update_animation(input: Vector2) -> void:
    match state:
        State.IDLE:
            anim.speed_scale = 1.0
            anim.play(&"idle_down")
        State.WALK:
            anim.speed_scale = velocity.length() / SPEED     # tempo follows speed
            if absf(input.x) >= absf(input.y):
                anim.flip_h = input.x < 0.0
                anim.play(&"walk_side")
            else:
                anim.play(&"walk_down" if input.y > 0.0 else &"walk_up")

func interact() -> void:
    state = State.INTERACT
    anim.speed_scale = 1.0
    anim.play(&"interact_down")                 # non-looping in SpriteFrames
    await anim.animation_finished
    state = State.IDLE
```

Note what the structure buys: animation names appear in exactly one function (skins and refactors touch one place); the `await` on the non-looping interact animation replaces a timer that would desync from `speed_scale`; and because `play()` of an already-playing animation never restarts it, calling `_update_animation()` every physics tick is safe. When the state × direction matrix outgrows this shape, §14's AnimationTree is the exit ramp.

---

## Choosing an animation approach

Godot gives you four (and a half) legitimate ways to make a sprite move. Choosing well is an architecture decision — each tool has a sweet spot, and forcing one tool to do everything produces either spaghetti (everything in code) or scene files nobody dares open (everything in one giant AnimationPlayer).

### The contenders

1. **`AnimatedSprite2D`** — frame flipbooks with named animations (§11).
2. **`AnimationPlayer`** — keyframes *any property of any node* over a timeline: sprite frames, position, modulate, shader uniforms, audio, method calls (§13).
3. **`Tween`** — code-created, fire-and-forget interpolation of properties; no editor asset (details in [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md)).
4. **Shader animation** — the GPU animates UVs/vertices/colors per-pixel; zero CPU per frame ([SHADERS_GDSHADER.md](SHADERS_GDSHADER.md)).
5. *(4½)* **Manual code** — `sprite.frame += 1` on a `Timer`; the zero-infrastructure option for trivial cases.

### Decision table

| | AnimatedSprite2D | AnimationPlayer | Tween | Shader | Manual (Timer) |
|---|---|---|---|---|---|
| Animates | texture frames | **any property**, methods, audio | any property | pixels/vertices on GPU | whatever you code |
| Authored in | SpriteFrames panel | timeline editor | code only | shader code | code |
| Multiple named clips | ✅ | ✅ (libraries) | ❌ one-shot | ❌ | ❌ |
| Sync several nodes | ❌ one sprite | ✅ one timeline, many tracks | ⚠️ chains/parallel | ❌ | ⚠️ DIY |
| Blending/transitions | ❌ hard cuts | ⚠️ blend times | ✅ eases | ✅ anything | ❌ |
| Runtime dynamism | good (`speed_scale`, code-built frames) | ⚠️ clips are static assets | ✅ fully dynamic | ✅ uniforms | ✅ |
| Designer-friendly | ✅✅ | ✅ | ❌ | ❌ | ❌ |
| CPU cost / instance | tiny | small | tiny | **zero** (GPU) | tiny |
| Sweet spot | character loops: idle/walk/run | cutscenes, attacks with hitboxes+sound, UI intros | hit-flash, pickup pop, panel slide | water, dissolve, palette cycling, wind on 1000 plants | 1 background prop |

### Decision rules of thumb

- **"A character with looping locomotion states"** → `AnimatedSprite2D`, driven by your state machine. This is Relax Room's character setup.
- **"Frames *plus* anything else in lockstep"** — a slash animation that moves a hitbox, flashes modulate, and plays a swing sound on frame 3 → `AnimationPlayer`; that is precisely what multi-track timelines are for.
- **"A one-off programmatic motion with easing"** — button pop, damage flash, item float-up → `Tween`. Creating an AnimationPlayer clip for a half-second one-shot is bureaucracy.
- **"The same cheap effect on hundreds of instances"** or per-pixel effects → shader. The CPU never wakes up.
- **"One prop, one loop, no states"** → either a 2-line Timer + `frame` script or a one-clip AnimationPlayer; do not overthink it.

Note the tools **compose**: the standard production character is *AnimatedSprite2D for frames* + *Tween for hit-flash modulate* + *AnimationPlayer for the scripted cutscene it stars in*. Choosing "one" is a per-behavior decision, not a per-project religion.

### The two "exotic" contenders, concretely

The table's last columns deserve working code, because they are the ones newcomers never consider and veterans quietly use everywhere.

**Tween-driven frame animation** — a one-shot flipbook with follow-through, entirely in code. A chest opens once; no SpriteFrames resource, no AnimationPlayer clip, and the squash-and-stretch rides the same chain:

```gdscript
func open_chest(chest: Sprite2D) -> void:
    chest.hframes = 6                       # 6-frame opening strip
    var tw := create_tween()
    # Step the frames: tween_method with int endpoints yields 0,1,2,3,4,5.
    tw.tween_method(func(f: int) -> void: chest.frame = f, 0, 5, 0.45)
    # Follow-through on the same timeline:
    tw.tween_property(chest, "scale", Vector2(4.2, 3.8), 0.06)
    tw.tween_property(chest, "scale", Vector2(4.0, 4.0), 0.12) \
      .set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
```

The chain is created, runs, and garbage-collects itself — zero assets, zero lingering state. That self-destructing nature is also its limit: no pause, no named clips, no editor visibility. (Full Tween treatment: [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md).)

**Shader flipbook** — the GPU flips frames; the CPU is never involved after setup. Setup: a `Sprite2D` with the full strip as `texture`, `region_enabled = true` and `region_rect` covering *frame 0 only* (so the quad is one frame's size and `UV` spans one frame's texture range), plus this material:

```glsl
shader_type canvas_item;

uniform int hframes = 4;      // frames in the strip
uniform float fps = 8.0;

void fragment() {
    int frame = int(TIME * fps) % hframes;
    // UV covers frame 0's slice of the sheet; shift right by whole frames:
    vec2 uv = UV + vec2(float(frame) / float(hframes), 0.0);
    COLOR = texture(TEXTURE, uv);
}
```

A field of 500 grass tufts animated this way costs the CPU nothing and — because they share one material and one texture — batches into a handful of draw calls (§10). Two caveats define its niche: `TIME` is global, so all instances animate in phase (per-instance desync needs unique materials with a phase uniform, which breaks batching — or vertex-data tricks from [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md)); and gameplay cannot query "which frame is showing" — the CPU genuinely does not know. Decorative mass animation: perfect. Anything logic reads: wrong tool.

> ✅ **Best practice** — Keep gameplay-critical timing out of visual tools. If the attack's active window is defined by "frames 2-4 of the swing animation", encode it in the AnimationPlayer's method/track keys (or in code constants) — never by polling `anim.frame` from `_process` and hoping playback kept up with a paused/slowed timeline.

---

## AnimationPlayer for sprite animation

`AnimationPlayer` is Godot's general-purpose keyframe timeline. Where `AnimatedSprite2D` answers "which texture now?", `AnimationPlayer` answers "what is the value of *any* property at time *t*" — for many nodes at once, with method calls and audio on the same timeline. For sprite work, the canonical pattern is: a plain `Sprite2D` with `hframes`/`vframes` set, and an `AnimationPlayer` keyframing its `frame` property.

### The sprite-flipbook pattern, step by step

Scene: `CharacterBody2D → Sprite2D` (sheet assigned, `hframes = 6`, `vframes = 1`) and a sibling `AnimationPlayer`.

1. In the **Animation** bottom panel: *Animation → New*, name it `walk`, set length (e.g. `0.6` s) and enable looping.
2. Select the `Sprite2D`, set `frame = 0`. A **key** icon appears next to the property in the Inspector — click it to create a *value track* for `frame` with a keyframe at the playhead.
3. Move the playhead, change `frame`, key again — or simply key frame 0 at t=0 and frame 5 at t=0.5 and set the track's **update mode to Discrete**: integer interpolation steps through 1, 2, 3, 4 on the way.
4. Play with the panel's ▶ or from code.

```gdscript
@onready var player: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
    player.play(&"walk")

func stop_walking() -> void:
    player.play(&"idle")

# The 4.x await pattern — animation_finished carries the animation's name:
func play_attack() -> void:
    player.play(&"attack")
    var finished: StringName = await player.animation_finished
    print("done: ", finished)
```

> ⚠️ **Pitfall** — For integer `frame` tracks, the update mode must be **Discrete** (the default for int properties). If someone switches it to Continuous, Godot interpolates 0 → 5 *fractionally* and the truncation makes frame timing drift from your keys. Conversely, for `position` or `modulate` tracks you want **Continuous**.

> ⚠️ **Pitfall** — If a script sets `sprite.frame` (or any keyed property) while an `AnimationPlayer` animation is playing, the animation overwrites it every frame it processes. One property, one owner: either the timeline drives it or code does.

### Track types — the real power

One `walk` animation can simultaneously contain:

| Track type | Example use with sprites |
|---|---|
| **Property (value)** | `Sprite2D:frame` (Discrete), `Sprite2D:flip_h`, `modulate`, `offset`, shader uniform `material:shader_parameter/flash` |
| **Call Method** | invoke `spawn_footstep_dust()` exactly on the frame where the foot lands |
| **Audio Playback** | play the footstep sample on an `AudioStreamPlayer2D`, sample-accurately on the timeline |
| **Animation Playback** | trigger *another* AnimationPlayer — nesting cutscenes |
| **Bezier** | curved easing for float properties (better than linear keys for smooth motion) |

This multi-track capability is the decisive argument versus `AnimatedSprite2D`: when the *frame flip* must stay synchronized with hitboxes, sounds and VFX, putting all of them on one timeline eliminates an entire class of drift bugs.

```gdscript
# Editing animations from code — occasionally useful for tooling:
var anim: Animation = player.get_animation(&"walk")
print(anim.length, " ", anim.loop_mode)              # e.g. 0.6, Animation.LOOP_LINEAR
var track := anim.find_track("Sprite2D:frame", Animation.TYPE_VALUE)
print(anim.track_get_key_count(track))
```

### Libraries, blend times, speed

- **Animation libraries.** In 4.x, an AnimationPlayer stores animations inside named `AnimationLibrary` resources (the default library is named `""`, so plain names keep working). Libraries can be saved as `.res`/`.tres` and shared between scenes — e.g. one `humanoid.res` library reused by every character. Names are addressed as `"library/animation"` when the library is non-default.
- **Blend times.** `player.set_blend_time(&"idle", &"walk", 0.2)` cross-fades 0.2 s whenever idle transitions to walk; `playback_default_blend_time` sets the global default. For *continuous* properties this is a smooth cross-fade; for **Discrete `frame` tracks there is nothing to interpolate** — blending buys you little for pure flipbooks and shines for position/modulate/skeletal tracks.
- **Speed.** `player.speed_scale` (persistent) or `player.play(&"walk", -1, 2.0)` — the second argument is custom blend, the third is speed; negative speed plays backwards, or use `play_backwards()`.
- **Sync quirk.** After `play()`, tracks are applied on the *next* process pass. If you `play()` and in the same frame need the first keyed values applied (e.g. teleport + pose), call `player.advance(0.0)` to force an immediate update — an officially documented idiom.

Sharing a library across characters, concretely — author the clips once on any character, save the library from the animation panel (or via code), then attach it wherever the node paths line up:

```gdscript
# One humanoid clip set, N characters. Clips address relative paths
# ("Sprite2D:frame"), so any scene with the same child naming can host them.
const HUMANOID_CLIPS: AnimationLibrary = preload("res://animation/humanoid.res")

func _ready() -> void:
    var player: AnimationPlayer = $AnimationPlayer
    player.add_animation_library(&"humanoid", HUMANOID_CLIPS)
    player.play(&"humanoid/idle")          # non-default libraries use the prefix
```

The prerequisite hiding in the comment is the real discipline: shared libraries only work when every consumer scene keeps the **same relative node structure** the tracks were authored against (`Sprite2D:frame` must resolve). Teams encode that as a base character scene that variants inherit — scene inheritance from [SCENES_AND_NODES.md](SCENES_AND_NODES.md) doing animation work.

### Building an animation clip from code

Tooling, procedural characters and data-driven pipelines sometimes need to *construct* clips rather than author them. The `Animation` resource API mirrors the timeline editor one-to-one — building the sprite-flipbook pattern programmatically also cements how the pieces relate:

```gdscript
## Creates a "walk" clip: a Discrete frame track plus a footstep method track.
func build_walk_clip(player: AnimationPlayer) -> void:
    var anim := Animation.new()
    anim.length = 0.6
    anim.loop_mode = Animation.LOOP_LINEAR

    # Value track stepping Sprite2D.frame through 0..3:
    var frames := anim.add_track(Animation.TYPE_VALUE)
    anim.track_set_path(frames, NodePath("Sprite2D:frame"))
    anim.value_track_set_update_mode(frames, Animation.UPDATE_DISCRETE)
    for i in 4:
        anim.track_insert_key(frames, i * 0.15, i)

    # Method track: footsteps exactly on the contact frames (t = 0.15, 0.45):
    var calls := anim.add_track(Animation.TYPE_METHOD)
    anim.track_set_path(calls, NodePath("."))          # method lives on the root node
    for t in [0.15, 0.45]:
        anim.track_insert_key(calls, t, { "method": &"play_footstep", "args": [] })

    # Clips live inside libraries in 4.x; "" is the default (unprefixed) library:
    if not player.has_animation_library(&""):
        player.add_animation_library(&"", AnimationLibrary.new())
    player.get_animation_library(&"").add_animation(&"walk", anim)

func play_footstep() -> void:
    $Steps.play()
```

Everything the editor does reduces to these calls — `add_track`, `track_set_path`, `track_insert_key`, update modes — which also means everything is *diffable and generatable*: a script can translate Aseprite frame-tag metadata straight into `Animation` resources, keeping art and clips in lockstep without hand-keying.

### When AnimationPlayer earns its place for sprites

Choose it over `AnimatedSprite2D` when at least one of these is true: (1) the animation coordinates **more than the texture frames** — sounds, hitboxes, particles, camera; (2) you need **precise timeline control** — non-uniform key spacing without duration hacks, bezier eases on accompanying properties; (3) the animation belongs to a **cutscene** touching many nodes; (4) you want **shared libraries** across many scenes. For plain looping locomotion, `AnimatedSprite2D` remains less ceremony.

---

## AnimationTree — a first taste

When a character accumulates states (idle/walk/run/interact × 8 directions in Relax Room's case), driving `play()` calls from nested `if`s becomes brittle. `AnimationTree` layers a *state machine* (or blend spaces) on top of an `AnimationPlayer`'s clips:

- Node setup: `AnimationTree` with `anim_player` pointing at the AnimationPlayer, `tree_root = AnimationNodeStateMachine`, and the tree's `active = true`.
- In the state machine editor you drop animation states and draw transitions (with conditions, auto-advance, and cross-fade times *per transition* — far better than global blend times).
- Code talks to the machine through its playback object:

```gdscript
@onready var tree: AnimationTree = $AnimationTree
@onready var state: AnimationNodeStateMachinePlayback = tree.get(&"parameters/playback")

func _physics_process(_delta: float) -> void:
    if velocity.length() > 10.0:
        state.travel(&"walk")     # walks the transition graph for you
    else:
        state.travel(&"idle")
```

`travel()` finds a legal path of transitions from the current state and honors each transition's blend — the state machine, not your `if` ladder, owns "how do I get from *interact* to *walk*". For directional 2D movement, `AnimationNodeBlendSpace2D` picks between 8-direction clips from a `Vector2` parameter — an elegant replacement for threshold-based direction pickers.

The blend-space variant, sketched — eight directional walk clips placed on a unit circle inside an `AnimationNodeBlendSpace2D` named `Walk`, selected by a single vector parameter instead of an `if` ladder:

```gdscript
@onready var tree: AnimationTree = $AnimationTree   # tree_root: state machine containing "Walk"

func _physics_process(_delta: float) -> void:
    if velocity != Vector2.ZERO:
        # One line replaces the whole threshold-based direction picker:
        tree.set(&"parameters/Walk/blend_position", velocity.normalized())
        state.travel(&"Walk")
    else:
        state.travel(&"Idle")
```

With the blend space's mode set to *Discrete*, it snaps to the nearest clip — flipbook-correct behavior (interpolated blending between different pixel-art frames just cross-fades two images, which reads as ghosting; Discrete avoids it).

This is a *taste* on purpose: full AnimationTree treatment (blend spaces, one-shots, expressions) belongs to a later module. What you should retain now: **when animation-selection logic grows past ~3 states, migrate the selection into an AnimationTree** rather than growing the `if` forest. Note that `AnimationTree` requires clips in an `AnimationPlayer` — one more reason production characters often graduate from `AnimatedSprite2D` to the Sprite2D + AnimationPlayer pattern as they grow.

---

## Nine-patch and UI textures

Sprites live in world space; UI art lives in `Control` land, where elements must **resize** with content and window — and naive texture stretching deforms corners and borders. Two nodes do the heavy lifting.

### NinePatchRect — 9-slice scaling

`NinePatchRect` draws a texture divided into a 3×3 grid: **corners never scale**, edges stretch/tile along one axis, the center fills the rest. One tiny 24×24 panel texture skins dialog boxes of any size with crisp pixel-art borders.

| Property | Meaning |
|---|---|
| `texture` | the source panel art |
| `patch_margin_left/top/right/bottom` | border thickness in texture pixels — defines the 9 slices |
| `axis_stretch_horizontal` / `axis_stretch_vertical` | how edges/center grow: `AXIS_STRETCH_MODE_STRETCH`, `AXIS_STRETCH_MODE_TILE`, `AXIS_STRETCH_MODE_TILE_FIT` |
| `draw_center` | `false` = frame only (e.g. selection outline) |
| `region_rect` | use only a sub-rectangle of the texture (panel art inside an atlas) |

```gdscript
var panel := NinePatchRect.new()
panel.texture = preload("res://assets/ui/panel_wood.png")   # e.g. 24×24 source
for side in ["left", "top", "right", "bottom"]:
    panel.set(&"patch_margin_%s" % side, 8)                  # 8px pixel-art border
panel.axis_stretch_horizontal = NinePatchRect.AXIS_STRETCH_MODE_TILE
panel.axis_stretch_vertical = NinePatchRect.AXIS_STRETCH_MODE_TILE
panel.custom_minimum_size = Vector2(160, 90)
add_child(panel)
```

Mode choice: **Stretch** suits gradients/flat centers (may smear patterns); **Tile** repeats a seamless pattern undistorted — the pixel-art favorite; **Tile Fit** tiles, then scales slightly so only whole tiles show. For pixel art, draw border patterns so they tile, and keep margins multiples of your pixel grid.

> ⚠️ **Pitfall** — `NinePatchRect` is a plain texture frame: it has no styling, no content margin management, and no theme integration. For panels that should follow the UI **Theme** (and skin every `PanelContainer`/`Button` consistently), the theme resource `StyleBoxTexture` provides the same 9-slice math *inside* the theming system. Rule of thumb: one-off decorative frame → `NinePatchRect`; reusable UI skin → `StyleBoxTexture` in a Theme.

For completeness, the theme-integrated form of the same 24×24 panel — three margin properties different, everything else conceptually identical:

```gdscript
# StyleBoxTexture: 9-slice inside the theming system.
var sb := StyleBoxTexture.new()
sb.texture = preload("res://assets/ui/panel_wood.png")
sb.texture_margin_left = 8.0      # the 9-slice borders (texture pixels)
sb.texture_margin_top = 8.0
sb.texture_margin_right = 8.0
sb.texture_margin_bottom = 8.0
sb.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
sb.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
sb.content_margin_left = 12.0     # padding for child content — NinePatchRect has no equivalent
sb.content_margin_top = 12.0
sb.content_margin_right = 12.0
sb.content_margin_bottom = 12.0

var theme := Theme.new()
theme.set_stylebox(&"panel", &"PanelContainer", sb)
# Assign the theme high in the Control tree; every PanelContainer below is skinned.
```

The `content_margin_*` properties are the functional difference: containers using the stylebox automatically inset their children by them — layout awareness a bare `NinePatchRect` cannot offer.

### TextureRect — textures in UI layouts

`TextureRect` is "Sprite2D for Controls": it displays a texture *inside a layout*, where the container decides its rectangle. Two orthogonal properties define behavior:

**`expand_mode`** — how the texture influences the control's *minimum size*:

| Mode | Effect |
|---|---|
| `EXPAND_KEEP_SIZE` (default) | minimum size = texture size; the control refuses to shrink below it |
| `EXPAND_IGNORE_SIZE` | texture doesn't constrain layout — the usual choice inside containers |
| `EXPAND_FIT_WIDTH` / `_PROPORTIONAL` | height drives width (aspect-aware variants) |
| `EXPAND_FIT_HEIGHT` / `_PROPORTIONAL` | width drives height |

**`stretch_mode`** — how the texture fills whatever rectangle it got:

| Mode | Effect |
|---|---|
| `STRETCH_SCALE` | fill the rect, ignore aspect (distorts) |
| `STRETCH_TILE` | repeat the texture |
| `STRETCH_KEEP` / `STRETCH_KEEP_CENTERED` | native size, top-left / centered (crop if smaller rect) |
| `STRETCH_KEEP_ASPECT` / `_CENTERED` | fit inside, preserve aspect (letterbox) |
| `STRETCH_KEEP_ASPECT_COVERED` | cover the rect, preserve aspect (crop overflow) |

The production pairing for "show this image in a card": `EXPAND_IGNORE_SIZE` + `STRETCH_KEEP_ASPECT_CENTERED`. For pixel-art UI at exact scale: `EXPAND_KEEP_SIZE` + `STRETCH_KEEP` and size the layout around the art. `flip_h`/`flip_v` exist here too.

> ✅ **Best practice** — In pixel-art UIs, prefer *integer-scaled* art via the project stretch (§7) and `STRETCH_KEEP`; if a `TextureRect` must scale art itself, keep the control's rect an exact multiple of the texture size, or the nearest filter will drop/duplicate pixel rows unevenly.

---

## Texture memory and performance

Textures are almost always the biggest memory consumer in a 2D project. VRAM budgeting is not a console-era relic: integrated GPUs share RAM with the OS, and a desktop-companion app like Relax Room is a *guest* on the user's machine — it must stay lean while Chrome and an IDE hog the rest.

### The arithmetic

Uncompressed (Lossless-imported) textures cost `width × height × bytes_per_pixel`, RGBA8 = 4 bytes:

| Texture | VRAM (RGBA8, no mips) |
|---|---|
| 32×32 sprite frame | 4 KiB |
| 128×32 animation strip | 16 KiB |
| 640×360 full-screen background | 900 KiB |
| 1024×1024 packed atlas | 4 MiB |
| 4096×4096 "just in case" atlas | **64 MiB** |
| any of the above + mipmaps | +~33% |

The table carries the lesson: **pixel-art assets are almost free** — an entire 16-animation character at 32×32 costs about as much as one *icon* from a 4K asset pack. Waste creeps in through oversized sources: a decoration authored at 1024×1024 but displayed at 64×64 spends 4 MiB where 16 KiB would do, plus scaling artifacts. Export at native resolution; if a source must stay big, the importer's `process/size_limit` caps its imported dimensions without touching the file.

### Measuring — monitors and the Video RAM panel

```gdscript
# Live VRAM numbers from anywhere:
func print_vram() -> void:
    var tex_mib := Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0
    var vid_mib := Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0
    var buf_mib := Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED) / 1048576.0
    print("textures: %.1f MiB · video total: %.1f MiB · buffers: %.1f MiB"
            % [tex_mib, vid_mib, buf_mib])
```

Tooling equivalents while the game runs from the editor: **Debugger → Monitors** graphs the same counters over time (spikes reveal load-time churn), and **Debugger → Video RAM** lists *every loaded texture with its individual size* — sort by size, and the offending 4096×4096 "temp" asset has nowhere to hide.

Set a budget the way production teams do: pick a ceiling (e.g. *"total video memory under 256 MiB on the minimum-spec iGPU"*), automate a debug overlay showing the number, and treat crossing it like a failing test. Two habits make budgets stick: capture the numbers at the *same* moment each time (e.g. "standing in the furnished room, all systems loaded"), so runs are comparable; and record them per release, so growth is a visible trend instead of a surprise. See [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) for the full budgeting method (CPU, memory and battery included).

### Size limits — how big is too big?

Two ceilings bound texture dimensions, one hard and one prudent:

- **Hard:** GPUs cap maximum texture dimensions. Modern desktop hardware allows 16384×16384; older or low-end mobile GPUs stop at 4096 (some ancient ones at 2048). A texture over the device limit fails or gets downscaled — the importer's `process/size_limit` exists partly to guard this.
- **Prudent:** even where 16384 is legal, a 16384×16384 RGBA8 texture is **1 GiB** of VRAM. Atlas builders therefore page at 2048² or 4096² (16-64 MiB per page uncompressed) — big enough to batch hundreds of sprites, small enough to load fast, evictable in sensible units, and safe on every desktop GPU of the last decade.

For a pixel-art desktop app the guidance collapses to: keep every texture ≤2048², which the native-resolution rule (§4) achieves automatically — a 2048² page holds four thousand 32×32 sprites, several projects' worth of art.

### Loading behavior

`load()` pulls a texture into memory the first time and caches it by path; further `load()`s of the same path return the cached resource. Textures unload when the last reference dies. Consequences:

- Two `Sprite2D`s sharing `character.png` share one GPU texture — duplication anxiety is unfounded.
- A `preload()` in a script keeps the texture alive as long as the script resource lives — fine for gameplay assets, wasteful for a 20 MiB splash image referenced by a long-lived autoload.
- Scene transitions in small projects can simply let textures drop and reload; larger projects preload during loading screens (Relax Room does — §17.4) or use `ResourceLoader.load_threaded_request()` for background streaming.

### Worked worksheet — what a pixel-art character actually costs

Applying the arithmetic to Relax Room's main character (§17.1) makes the scale of pixel-art budgets concrete. The character ships as 24 strips of 128×32 (idle, walk, interact × 8 direction files) plus one 256×32 rotate strip, all Lossless (RGBA8, no mipmaps):

```
24 strips × (128 × 32 × 4 B)  =  24 × 16 KiB  =  384 KiB
 1 strip  × (256 × 32 × 4 B)  =       32 KiB
────────────────────────────────────────────────
one fully-animated 16-animation character       ≈  416 KiB
```

Less than half a megabyte for the entire protagonist — roughly **0.6%** of one 4096×4096 atlas. Extending the estimate across a hypothetical full room (numbers illustrative, method exact): 40 decorations averaging 64×64 → 40 × 16 KiB = 640 KiB; a 640×360 background → 900 KiB; UI sheets ~500 KiB. Total: **~2.5 MiB** — three orders of magnitude under a 256 MiB desktop-companion ceiling. The worksheet's real lesson is diagnostic: when the Video RAM panel shows tens of MiB in a project like this, the cause is never "too many sprites" — it is a handful of oversized sources, which is why §16's audit sorts by size instead of counting files.

### Custom monitors — first-class numbers for your own metrics

The Monitors tab is extensible: `Performance.add_custom_monitor()` registers any zero-argument callable, and its value gets graphed alongside the built-ins while the game runs — history, scale and all. Registering the numbers you actually budget turns "we should keep an eye on that" into a graph someone will notice:

```gdscript
# In an autoload (see AUTOLOAD_SAFETY.md for autoload discipline):
func _ready() -> void:
    Performance.add_custom_monitor(&"relax_room/texture_mib",
            func() -> float:
                return Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0)
    Performance.add_custom_monitor(&"relax_room/decoration_sprites",
            func() -> int:
                return get_tree().get_node_count_in_group("decorations"))
```

The `"category/name"` id convention groups your monitors under their own header in the panel. Custom monitors cost one callable invocation per sample — keep them O(1) reads, not scene traversals.

### Background loading — big textures without hitches

`load()` is synchronous: a 4 MiB background decoded on the main thread is a visible frame hitch. For assets known in advance, `ResourceLoader`'s threaded API loads during gameplay or a loading screen (this is what powers §17.4's screen):

```gdscript
const NEXT_ROOM_BG := "res://assets/rooms/penthouse_background.png"

@onready var progress_bar: Range = %ProgressBar

func _ready() -> void:
    ResourceLoader.load_threaded_request(NEXT_ROOM_BG)

func _process(_delta: float) -> void:
    var progress: Array = []
    match ResourceLoader.load_threaded_get_status(NEXT_ROOM_BG, progress):
        ResourceLoader.THREAD_LOAD_IN_PROGRESS:
            progress_bar.value = progress[0] * 100.0
        ResourceLoader.THREAD_LOAD_LOADED:
            var tex: Texture2D = ResourceLoader.load_threaded_get(NEXT_ROOM_BG)
            _enter_room(tex)
            set_process(false)
        ResourceLoader.THREAD_LOAD_FAILED:
            push_error("Background failed to load")
            set_process(false)
```

For a pixel-art project the individual sprites never need this — they are kilobytes — but scene *transitions* that load dozens of resources at once do, and the pattern generalizes to scenes and audio unchanged.

> ⚠️ **Pitfall** — Do not mix a threaded request and a plain `load()` of the same path in the same window of time: the synchronous `load()` blocks until the threaded one completes, silently re-serializing the exact hitch you were avoiding. Once a path goes threaded, collect it with `load_threaded_get()` only.

### Channel packing basics

A texture has four 8-bit channels; nothing forces them to mean "red, green, blue, alpha". **Channel packing** stores independent grayscale maps in one texture — the standard 3D example packs ambient-occlusion/roughness/metallic into R/G/B of one map. In 2D the trick appears in shaders: a single "effects mask" texture can carry, say, *dissolve threshold* in R, *emission mask* in G and *outline mask* in B; the sprite shader samples one texture instead of three. Benefits: one sampler, one file, a third of the memory. Costs: unreadable in an image viewer, and channels can't use different compression. The import option `compress/channel_pack = Optimized` relatedly lets the importer drop unused channels (e.g. storing an RG-only map as such). File the concept away until [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md) gives you shaders to exploit it.

> ✅ **Best practice** — Audit texture memory *before* shipping, not when a user with an old iGPU reports stutter: open Video RAM panel → sort by size → for each of the top ten ask "is this displayed anywhere near its native resolution?" Ten minutes, routinely recovers tens of MiB.

---

## Case study: Relax Room

> 📦 **Case study** — The subsections below document how the running course project, **Relax Room** (desktop-companion, 2D isometric-flavored pixel art), applies this module in its actual source tree. Paths, scale factors and animation names are the project's real ones; treat them as a worked reference implementation, not as universal law.

### 17.1 Character system — 8 directions, 16 animations

The main character (`male_old`) has **16 animations** organized around 8 movement directions, authored as per-animation horizontal strips:

```
assets/charachters/male/old/          ← historical typo preserved in the real tree
├── male_idle/
│   ├── male_idle_down.png            # 128×32 → 4 frames of 32×32
│   ├── male_idle_down_side.png
│   ├── male_idle_down_side_sx.png
│   ├── male_idle_side.png
│   ├── male_idle_side_sx.png
│   ├── male_idle_up.png
│   ├── male_idle_up_side.png
│   └── male_idle_up_side_sx.png
├── male_walk/        (same 8-file structure)
├── male_interact/    (same 8-file structure)
└── male_rotate/
    └── male_rotate.png               # 256×32 → 8 frames of 32×32
```

Every strip is 128 px wide holding 4 frames of 32×32 — except `rotate`, an 8-frame 256×32 strip. This uniformity is deliberate (§9's layout conventions): one slicing rule covers the whole character.

**Scene side (`scenes/male-old-character.tscn`).** The `AnimatedSprite2D` node has:

- `texture_filter = 1` (Nearest — explicit, belt-and-braces over the project default);
- `scale = Vector2(3, 3)` — 32 px of art becomes 96 px on screen, integer scale per §7;
- a `SpriteFrames` resource with all 16 animations, each frame an `AtlasTexture` region into its strip (the pattern shown in §9):
  - **idle** (5): `idle_down`, `idle_side`, `idle_up`, `idle_vertical_down`, `idle_vertical_up`
  - **walk** (5): `walk_down`, `walk_side`, `walk_up`, `walk_side_down`, `walk_side_up`
  - **interact** (5): `interact_down`, `interact_side`, `interact_up`, `interact_vertical_down`, `interact_vertical_up`
  - **rotate** (1): 8 frames at **3.0 fps** (all others run at **5.0 fps**)

Only 5 sprite-facing directions are authored per state; the remaining 3 come free from `flip_h` mirroring — the art-budget-halving trick from §8.

**Control side (`scripts/rooms/character_controller.gd`).** Direction → animation selection:

```gdscript
# Line 10 — the AnimatedSprite2D reference
@onready var _anim: AnimatedSprite2D = $AnimatedSprite2D

# Lines 48-62 — pick animation from the movement vector
var abs_x := absf(direction.x)
var abs_y := absf(direction.y)
if abs_x > abs_y * DIRECTION_THRESHOLD:        # predominantly horizontal
    _anim.flip_h = direction.x < 0             # mirror for leftward walk
    anim_name = "walk_side"
elif abs_y > abs_x * DIRECTION_THRESHOLD:      # predominantly vertical
    anim_name = "walk_down" if direction.y > 0 else "walk_up"
elif direction.y > 0:                          # downward diagonal
    _anim.flip_h = direction.x < 0
    anim_name = "walk_side_down"
else:                                          # upward diagonal
    _anim.flip_h = direction.x < 0
    anim_name = "walk_side_up"
```

**The `DIRECTION_THRESHOLD` trick (1.2).** Requiring one axis to *dominate* the other by 20% before choosing a cardinal animation creates a dead zone around the diagonals: slightly-off joystick input still reads as "walking straight", which feels dramatically better than animations flickering at exact 45° boundaries. This is a miniature of the AnimationTree blend-space idea (§14) implemented by hand — and precisely the kind of `if` ladder that would migrate to an `AnimationNodeBlendSpace2D` if the state count grew further.

### 17.2 MenuCharacter — manual animation with Sprite2D

On the menu screen, a character strolls across the bottom using the *other* flipbook mechanism: `Sprite2D` + `hframes` + a `Timer` (`scripts/menu/menu_character.gd`). No `SpriteFrames`, no `AnimatedSprite2D`:

```gdscript
# Lines 41-49 — sprite with a frame grid
_sprite = Sprite2D.new()
_sprite.texture = load(char_data["walk_path"])   # male_walk_side.png (128×32)
_sprite.hframes = 4        # 4 columns
_sprite.vframes = 1        # 1 row
_sprite.frame = 0
_sprite.flip_h = false
_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
_sprite.scale = Vector2(4.0, 4.0)                # 32 px → 128 px

# Lines 55-59 — frame-advance timer
_frame_timer = Timer.new()
_frame_timer.wait_time = FRAME_INTERVAL          # 0.15 s ≈ 6.67 fps
_frame_timer.timeout.connect(_next_frame)

# Lines 68-70 — advance the cycle
func _next_frame() -> void:
    _current_frame = (_current_frame + 1) % _hframes     # 0→1→2→3→0→…
    _sprite.frame = _walk_row * _hframes + _current_frame
```

**Why not `AnimatedSprite2D` here?** One animation, one short scripted sequence, frames already in a strip: building a whole `SpriteFrames` library would be ceremony without benefit. This is decision rule "one prop, one loop → manual" from §12 applied verbatim — and a live demonstration that `frame = row * hframes + column` row-major math from §8.

### 17.3 Decorations — dynamic sprites from data

Room decorations are spawned at runtime by `scripts/rooms/room_base.gd`, driven by a `decorations.json` data file:

```gdscript
# Lines 96-104 — decoration sprite creation
var sprite := Sprite2D.new()
sprite.centered = false                              # origin at top-left
sprite.texture = load(sprite_path) as Texture2D      # path from decorations.json
sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
sprite.scale = Vector2(item_scale, item_scale)       # from JSON: 3.0 / 6.0 / 4.0
sprite.position = pos                                # world position
sprite.rotation_degrees = rot                        # 0 / 90 / 180 / 270
sprite.flip_h = flipped
```

**`centered = false` is the load-bearing choice:** the node's position means "the texture's top-left corner", which makes grid placement (64 px snap) a pure multiplication with no half-size offsets — the anchor-convention decision from §8 (*characters centered, decorations top-left*).

**Per-category scales (from `decorations.json`):**

| Category | `item_scale` |
|---|---|
| Furniture (beds, desks, chairs, wardrobes) | 3.0 |
| Plants (potted and not) | 6.0 |
| Animals (Void Cat) | 4.0 |

All integer, all uniform (`Vector2(n, n)`) — distortion-free per the pixel-art recipe. Decorations stay as *individual PNGs* rather than an atlas: they change weekly while the room is furnished out, and §9's trade-off table says iteration speed wins until draw-call measurements argue otherwise.

### 17.4 Loading screen — AnimatedSprite2D in scene composition

The loading screen (`scenes/menu/loading_screen.tscn`) mixes both static and animated sprites:

```
background (Sprite2D) → loading/background.png
├── Camera2D (zoom 3.6×)
├── characters (AnimatedSprite2D)
│   ├── animation "loading" — 4 frames @ 5.0 fps
│   ├── autoplay = "loading"
│   └── scale (1.65625, 1.65625)
├── bar (Sprite2D) → loading/loading_base_bar.png
└── title (AnimatedSprite2D)
    ├── animation "default" — 4 frames @ 5.0 fps
    └── scale (0.90625, 0.90625)
```

`autoplay` earns its keep here: the loading screen has no gameplay script driving animations, so the resource-level autoplay flag (§11) starts the loop the moment the scene enters the tree. Note the honest imperfection: the `Camera2D` zoom (3.6×) and the sprite scales are *not* integers — on this transitional, motion-light screen the wobble risk was accepted; §7's rules are defaults, and knowing when a rule is safe to bend is part of mastering it. In gameplay scenes the project stays strictly integer.

### 17.5 Import standards (project art bible excerpt)

Every sprite in the project imports with the §7 recipe; the standard `.import` params block:

```ini
importer="texture"
type="CompressedTexture2D"

[params]
compress/mode=0                 ; Lossless — pixel-perfect storage
compress/high_quality=false
mipmaps/generate=false          ; 2D top-down — mips would only blur
process/fix_alpha_border=true   ; kill dark fringes on transparent edges
detect_3d/compress_to=0         ; never auto-convert (2D-only project)
```

and the global filter default lives in `project.godot`:

```ini
[rendering]
textures/canvas_textures/default_texture_filter=0    ; Nearest
```

Individual sprites still set `texture_filter` explicitly when created *from code* (§17.2, §17.3) — redundant with the project default, but self-documenting and robust if the code is ever copied into a differently-configured project.

### 17.6 What the case study leaves open

Reading production code teaches by omission too. Three things Relax Room does *not* yet do, each pointing at a later module: the character's direction-picking `if` ladder (§17.1) is one growth spurt away from an `AnimationNodeBlendSpace2D` (§14); the decoration PNGs are unpacked — if the furniture catalog triples, §9's release-packing argument and Lab 4's measurements decide whether an atlas pass joins the build; and the character has no 2D lighting, so `CanvasTexture` normal maps (§2) stay on the shelf until an ambience feature asks for them. Recognizing which "missing" optimizations are *correctly* missing — because no measurement has demanded them — is itself the production skill this course keeps returning to.

---

## Best practices

A consolidated checklist — each item earned its place in the sections above or in Relax Room production:

1. **Author at 1×, scale in-engine.** Source PNGs at native pixel size; scaling is the job of node `scale` and project stretch. Pre-scaled exports waste memory and break atlas math (§4, §16).
2. **Nearest everywhere, once.** Set `rendering/textures/canvas_textures/default_texture_filter = 0` and rely on inheritance; override per-node only for deliberate exceptions — and still set it explicitly on sprites you create purely from code, as self-documentation (§6, §17).
3. **Lossless + no mipmaps + fix alpha border for all pixel art**, encoded in Import Defaults so nobody has to remember, with `detect_3d/compress_to = 0` in 2D-only projects (§4, §5).
4. **`.import` files in version control, `.godot/` ignored.** Review import-setting diffs like code diffs — a stray `compress/mode=2` is a bug (§4).
5. **Integer, uniform scales.** `Vector2(3, 3)`, never `Vector2(2.5, 3.1)`; integer camera zoom; `stretch/scale_mode = "integer"` (§7).
6. **Enable `snap_2d_transforms_to_pixel`; reach for `snap_2d_vertices_to_pixel` only if shimmer survives** (§7).
7. **Pick anchors per asset class and write it down** — Relax Room: characters `centered = true`, grid decorations `centered = false`; feet-alignment via `offset` (§8, §17).
8. **Atlas what animates together; keep iterating assets separate; pack for release only if measurements demand it** (§9, §10).
9. **Choose the animation tool by what varies:** frames → `AnimatedSprite2D`; frames+sound+hitboxes → `AnimationPlayer`; one-shot property motion → `Tween`; mass/per-pixel effects → shader; and let them compose on one character (§12).
10. **`Repeat = Disabled` for spritesheets** (the project default) — with repeat on, edge sampling can wrap to the sheet's far side; enable repeat only for deliberately tiling backgrounds (§6, §9).
11. **One property, one owner.** Never let a script and an `AnimationPlayer` both write `frame`/`modulate`; use Discrete update mode for integer tracks (§13).
12. **Budget and measure VRAM and draw calls** with `Performance.get_monitor()`, the Monitors graphs and the Video RAM panel; audit the top-ten textures before every release (§10, §16).
13. **Use the lock-free `Image` API for one-shot CPU pixel work; use shaders for per-frame pixel work** — and always `INTERPOLATE_NEAREST` when resizing pixel art in code (§3).
14. **Don't hand-edit import settings per file when a preset can do it** — Import Defaults for the project baseline, multi-select + Reimport for migrations (§4).
15. **Keep source `.ase`/`.psd` files in the repo as Skip File imports** and automate sheet export (Aseprite CLI) so packed atlases and `SpriteFrames` are build artifacts, never hand-maintained state (§4, §9).
16. **Escalate rendering machinery only on evidence:** nodes → shared atlases → `MultiMeshInstance2D`/particles → `RenderingServer`; each step trades authoring comfort for throughput (§10).

### Quick reference card

The module's operational core, dense enough to pin next to the monitor:

```
PIXEL-ART PROJECT SWITCHES (project.godot)
  rendering/textures/canvas_textures/default_texture_filter = 0   (Nearest)
  rendering/2d/snap/snap_2d_transforms_to_pixel = true
  display/window/stretch/mode = "viewport"   aspect = "keep"   scale_mode = "integer"
  base resolution 640×360 (or 320×180 / 480×270)

IMPORT (per texture / Import Defaults)
  pixel art:  compress/mode=0 (Lossless) · mipmaps off · fix_alpha_border on
              detect_3d/compress_to=0
  never:      VRAM Compressed on pixel art (4×4 block codecs vs 1-px outlines)

DISPLAY NODES               ANIMATION TOOLS
  world object  Sprite2D      frames only        AnimatedSprite2D (+SpriteFrames)
  animated      AnimatedSp.   frames+sound+hitbox AnimationPlayer (Discrete frame track)
  UI image      TextureRect   one-shot property   Tween
  UI frame      NinePatchRect mass/per-pixel      canvas_item shader
  level grid    TileMapLayer  >3 states           AnimationTree (travel())

RUNTIME PIXELS (lock-free)
  img := Image.create_empty(w, h, false, Image.FORMAT_RGBA8)
  img.get_pixel(x, y) / img.set_pixel(x, y, color)      # no lock() in 4.x
  tex := ImageTexture.create_from_image(img)            # then tex.update(img)

MEASURE
  Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED)        # bytes
  Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
  Editor: Debugger → Monitors (graphs) · Debugger → Video RAM (per-texture)
```

---

## Common errors & troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Pixel art blurry when scaled up | Linear filtering (engine default) | Set `rendering/textures/canvas_textures/default_texture_filter = 0` (Nearest) or the node's `texture_filter`; §7 step 1 |
| Sprite suddenly blocky/smeared after working fine for weeks | `detect_3d` auto-reimported it as VRAM Compressed (it was previewed in a 3D context) | Import dock: Compress Mode → Lossless, Mipmaps → Off, Detect 3D → Compress To → Disabled, Reimport |
| Sprites wobble/shimmer while the camera scrolls | Sub-pixel final transforms | Enable `rendering/2d/snap/snap_2d_transforms_to_pixel`; keep camera zoom integer; consider `viewport` stretch |
| Some pixels drawn fatter than others | Fractional overall scale (window scaling 2.5×, non-integer node scale or zoom) | `stretch/scale_mode = "integer"`; uniform integer `scale`; integer `Camera2D.zoom` |
| Dark outline around transparent sprite edges | Transparent pixels' RGB (often black) bleeding via filtering, `fix_alpha_border` off | Re-enable `process/fix_alpha_border = true` and Reimport; keep Nearest for pixel art |
| Thin lines from *neighboring frames* flicker at sprite edges | Spritesheet bleeding: linear filter/mipmaps sampling across cell borders, or Repeat enabled | Nearest + no mipmaps; `texture_repeat = Disabled`; add padding/extrusion in the packer; `AtlasTexture.filter_clip = true` |
| `hframes`-sliced frames drift off the art | Sheet has margins/padding or non-uniform cells — grid math assumes neither | Use `AtlasTexture`/`region_rect` with explicit rects, or re-export the sheet with uniform, padding-free cells |
| `await anim.animation_finished` never resumes | The animation is looping — looping animations never emit `animation_finished` | Disable loop for one-shot animations in the SpriteFrames panel, or listen to `animation_looped` |
| Character stutters at frame 0 while moving | Code calls `stop()`/`play()` (or resets `frame`) every physics tick | Only change animation when the target differs; `play()` on an already-playing animation is safe by itself |
| `AnimationPlayer` sprite animation shows wrong in-between frames | `frame` value track set to Continuous update | Set the track's update mode to Discrete |
| Property snaps back while an animation plays | Script and `AnimationPlayer` both write the same property | One owner per property: remove the track or stop writing it from code |
| `ImageTexture.update()` errors / texture unchanged | New `Image` differs in size or format from the original | Use `set_image()` (reallocates) or recreate with `create_from_image()` |
| `NoiseTexture2D.get_image()` returns nothing useful at startup | Procedural generation is asynchronous | `await noise_texture.changed` before reading pixels |
| `get_pixel()` fails on an imported texture's image | `get_image()` returned VRAM-compressed data | Call `img.decompress()` (and usually `convert(Image.FORMAT_RGBA8)`) first — or import as Lossless |
| External image file won't `load()` at runtime | `load()` only reads *imported* `res://` resources; user files never passed the importer | `Image.load_from_file(path)` + `ImageTexture.create_from_image(img)` (§3) |
| `ViewportTexture` errors: "path to node is invalid" | Texture saved into a resource/scene where the viewport path can't resolve | Assign via `sub_viewport.get_texture()` in code, or keep viewport and consumer in the same scene |
| VRAM climbs scene after scene | Long-lived references (autoload `preload`s, static arrays) pin textures in cache | Drop references on transition; check Debugger → Video RAM for what's actually resident |
| Draw calls unexpectedly high in a sprite-heavy scene | Per-sprite materials or heavy atlas/off-atlas interleaving breaking batches | Share materials; consolidate sheets; verify with `RENDER_TOTAL_DRAW_CALLS_IN_FRAME` |
| Sprite jumps sideways when `flip_h` toggles | Flipping mirrors around the anchor and `centered = false` | Use `centered = true` for flippable sprites, or compensate with `offset` |
| Textures render pink/missing after a crash or branch switch | Corrupted or stale import cache | Close the editor, delete `.godot/`, reopen — full clean reimport (§4) |
| SVG icon is blurry when displayed large | Rasterized at 1× at import time | Raise **SVG → Scale** in the Import dock and Reimport; author UI icons at the size the design needs |
| `AnimatedSprite2D` shows frame 0 forever in game (fine in editor preview) | Neither `autoplay` set nor `play()` called | Set autoplay in the SpriteFrames panel or call `play()` in `_ready()` |
| `MultiMesh` instances don't appear | `instance_count` set before `transform_format`/`mesh` (setting format resets the buffer) | Configure `transform_format` and `mesh` first, then `instance_count`, then per-instance transforms |
| Scene references break after moving assets outside the editor | Source moved without its `.import` (new UID assigned) | Move files in the FileSystem dock, or always move source + `.import` together (§4) |

---

## Exercises

Work in a scratch project configured with the §7 recipe (do Lab 1 first — every later lab depends on it). Labs marked ★ are the module's core; finish those before the stretch goals.

### Lab 1 ★ — Pixel-perfect project bootstrap

Create a new project and apply the full pixel-art recipe: Nearest default filter, `snap_2d_transforms_to_pixel`, 640×360 base resolution, `viewport` stretch, `keep` aspect, `integer` scale mode, Import Defaults (Lossless, no mipmaps, detect_3d disabled). Add one 32×32 test sprite at scale 4 and a `Camera2D` that lerps toward the mouse.
**Acceptance criteria:** window resize letterboxes instead of producing uneven pixels; camera motion causes zero sprite shimmer; toggling the filter setting to Linear (temporarily) visibly blurs the sprite, proving the pipeline is under your control.
**Stretch:** expose a debug key that toggles each recipe setting at runtime (`ProjectSettings` reads are enough for display; filter/zoom can change live) and observe each artifact appear.

### Lab 2 ★ — Import-pipeline autopsy

Import the same 64×64 pixel-art PNG four times (copies) with modes Lossless, Lossy 0.7, VRAM Compressed and VRAM Compressed + mipmaps. Display them side by side at 4× scale, labeled.
**Acceptance criteria:** you can point at concrete block artifacts in the VRAM copies; a short comment in the scene script records each variant's `Performance.RENDER_TEXTURE_MEM_USED` contribution (load them one at a time to isolate); the `.import` diffs for all four are committed and explained in one sentence each.
**Stretch:** write the same comparison for a 1024×1024 photograph and articulate why the verdict flips.

### Lab 3 ★ — Character animation with AnimatedSprite2D

From any free 32×32 character sheet (e.g. itch.io CC0 packs), build a `SpriteFrames` library with four animations (idle, walk, run, jump), sheet-sliced in the SpriteFrames panel. Drive it from a `CharacterBody2D` state machine, mirroring with `flip_h`, walk tempo scaled by `speed_scale ∝ velocity`.
**Acceptance criteria:** no animation restarts while its state persists (no frame-0 stutter); left movement mirrors; jump is non-looping and returns to idle via `await animation_finished`; all animation names are `StringName` constants — zero magic strings at call sites.
**Stretch:** rebuild the whole `SpriteFrames` in code from a dictionary (§11's `build_frames` pattern), loaded from a JSON file, and hot-swap it at runtime as a "character skin" switch.

### Lab 4 ★ — Atlas vs separate files, measured

Generate 100 moving sprites two ways: (a) each with its own small PNG texture (script-generate 20 distinct files with `Image.save_png()` if needed), (b) all pulling `AtlasTexture` regions from one packed sheet.
**Acceptance criteria:** a debug overlay shows `RENDER_TOTAL_DRAW_CALLS_IN_FRAME` live; you record both numbers and explain the difference in terms of §10's batching rules; frame time is captured for both on your machine.
**Stretch:** find the sprite count at which the two approaches' frame times measurably diverge on your hardware; then break batching *on purpose* by giving alternating sprites a unique `ShaderMaterial` and measure again.

### Lab 5 — AnimationPlayer attack timeline

Recreate Lab 3's character attack as a `Sprite2D` (`hframes` sheet) + `AnimationPlayer` clip: a Discrete `frame` track, a Call Method track spawning a hitbox `Area2D` exactly on the strike frame, an Audio track playing a whoosh, and a `self_modulate` flash track.
**Acceptance criteria:** slowing the clip via `speed_scale = 0.25` keeps *all* elements (hitbox, sound, flash) synchronized with the visible frames — demonstrating why this beats polling `frame` from code; the hitbox exists for exactly the keyed duration.
**Stretch:** add idle/walk clips, wire an `AnimationTree` state machine over them, and drive it with `travel()`; add per-transition blend only where it visually helps (spoiler: not on the flipbook tracks).

### Lab 6 — Runtime texture painting

Build a minimal 64×64 pixel-art painting canvas: an `Image`-backed `ImageTexture` on a scaled `Sprite2D`; left-drag paints, right-drag erases (transparent), a palette of 4 colors, PNG export.
**Acceptance criteria:** painting uses `set_pixel` + `tex.update(img)` (no texture re-creation per stroke — verify with a counter); mouse-to-texel mapping stays correct under the sprite's scale (use `get_rect()` / affine inverse math); `save_png()` writes into `user://` and the file reopens correctly.
**Stretch:** add a palette-swap button implementing §3's `palette_swap()` over the canvas, and an undo stack of `Image` snapshots (`Image.duplicate()`), capped at 20.

### Lab 7 — Nine-patch UI kit

Draw (or adapt) a 24×24 pixel-art panel texture with an 8 px border, and skin a settings dialog: `NinePatchRect` panel (Tile mode edges), a `TextureRect` character portrait (`EXPAND_IGNORE_SIZE` + `STRETCH_KEEP_ASPECT_CENTERED`), and a title bar.
**Acceptance criteria:** resizing the dialog from 160×90 to 480×270 keeps corners pixel-crisp and borders undistorted; switching axis stretch to Stretch mode visibly smears the border pattern (screenshot both); the portrait never distorts at any dialog size.
**Stretch:** re-implement the same skin as a `StyleBoxTexture` inside a Theme applied to a `PanelContainer`, and write three sentences on when each approach wins.

### Lab 8 — VRAM audit drill

Take any project (Lab 3's or a jam project) and run a §16 audit: Video RAM panel top-ten, `print_vram()` overlay, one deliberately oversized 2048×2048 asset planted as the "bug".
**Acceptance criteria:** the audit finds the planted asset; the fix (native-resolution re-export or `process/size_limit`) is measured — before/after `RENDER_TEXTURE_MEM_USED` numbers are recorded in a comment; total texture memory for the project is stated with one sentence judging it against a 256 MiB desktop-companion budget.
**Stretch:** automate the overlay as a reusable autoload debug panel (FPS, draw calls, texture MiB, video MiB) you will carry into every future module.

### Lab 9 — Stretch — CRT/scanline shader over crisp pixels

Write a `canvas_item` shader (post-processing over a `SubViewport` + `ViewportTexture` showing Lab 3's scene) adding scanlines or a CRT mask *without* destroying pixel crispness underneath.
**Acceptance criteria:** the underlying sprites remain Nearest-crisp (the effect darkens lines, it does not resample the art); effect strength is a uniform animatable from code; disabling the shader returns a bit-identical crisp image.
**Stretch:** add barrel distortion, and pixel-snap the scanline frequency to the *base resolution* so lines never alias against the integer upscale. (Full shader theory: [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md).)

### Lab 10 — Image as data: walkability mask

Author a 20×12 black/white PNG in any pixel editor (one pixel = one 32 px world cell; white = walkable). Import it with importer type **Image**, and implement §3's `WalkabilityMask` pattern: the Lab 3 character may only move onto walkable cells; a debug toggle draws the mask scaled over the world (Nearest filter) with 30% opacity.
**Acceptance criteria:** editing the PNG and reimporting changes movement with zero code changes; the mask never renders in normal play (the importer type keeps it off the GPU — verify it is absent from the Video RAM panel); out-of-bounds queries return non-walkable instead of crashing.
**Stretch:** add a second color channel meaning "slow terrain" (green = half speed) and read both channels from one `get_pixelv()` call; document why this is channel packing (§16) in miniature.

### Self-check questions

Answer from memory, then verify against the sections in parentheses:

1. Nearest vs Linear filtering — what does each do at the texel level, and which project setting establishes the default? (§6)
2. Why exactly does VRAM compression destroy pixel art, mechanically? (§5)
3. `AtlasTexture`'s main advantage over separate files — and the workflow cost you pay for it? (§9, §10)
4. `AnimatedSprite2D` vs `AnimationPlayer` for a sword swing with sound and hitbox — which and why? (§12, §13)
5. What does `texture_repeat = Disabled` protect spritesheets from? (§6, §9)
6. A sprite went blurry-and-blocky by itself last Tuesday. What almost certainly happened, and which two `.import` lines prove it? (§4)
7. Which three "speed knobs" affect an `AnimatedSprite2D`'s playback tempo, and which one belongs to gameplay code? (§11)
8. Why must an `AnimationPlayer` track keying `Sprite2D.frame` use Discrete update mode? (§13)

---

## Further reading

Official documentation first — always your primary source for API truth (links pinned to `stable`):

- [Importing images — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_images.html) — the authoritative reference for every import option in §4-§6: compress modes, mipmaps, processing flags, detect_3d, per-format notes. Reread it whenever an import checkbox looks unfamiliar.
- [2D Sprite animation — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/2d/2d_sprite_animation.html) — the official walkthrough of both flipbook workflows (§11, §13): AnimatedSprite2D from files and sheets, and AnimationPlayer over `hframes`/`frame`; includes the `advance(0)` sync idiom.
- [Multiple resolutions — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/rendering/multiple_resolutions.html) — stretch modes, aspect options and integer scaling; source of the 640×360 pixel-art recommendation used in §7.
- [Sprite2D](https://docs.godotengine.org/en/stable/classes/class_sprite2d.html) · [AnimatedSprite2D](https://docs.godotengine.org/en/stable/classes/class_animatedsprite2d.html) · [SpriteFrames](https://docs.godotengine.org/en/stable/classes/class_spriteframes.html) · [AtlasTexture](https://docs.godotengine.org/en/stable/classes/class_atlastexture.html) — class references for §8-§11; skim the signal lists, they answer most "how do I know when…" questions.
- [Image](https://docs.godotengine.org/en/stable/classes/class_image.html) · [ImageTexture](https://docs.godotengine.org/en/stable/classes/class_imagetexture.html) — the CPU-side API of §3, including every format constant and the create/update contracts.
- [NinePatchRect](https://docs.godotengine.org/en/stable/classes/class_ninepatchrect.html) · [TextureRect](https://docs.godotengine.org/en/stable/classes/class_texturerect.html) — §15's UI nodes; the enum tables there mirror this module's.
- [Performance](https://docs.godotengine.org/en/stable/classes/class_performance.html) — all monitor constants used in §10 and §16, plus custom-monitor registration for your own overlays.

Community and ecosystem (verify version applicability — the ecosystem still hosts many Godot 3 pages):

- [GDQuest — godotengine tutorials](https://www.gdquest.com/) — consistently high-quality, Godot-4-current tutorials and open-source demo projects; their free 2D content complements this module's animation sections with video pacing.
- [Godot 4.4 settings for pixel art (itch.io community post)](https://itch.io/blog/806788/godot-44-settings-for-pixel-art) — a concise community-consensus checklist that independently converges on §7's recipe; useful as a second opinion when onboarding teammates.
- [Snap 2D Transforms vs Snap 2D Vertices — Godot Forum](https://forum.godotengine.org/t/difference-between-snap-2d-vertices-to-pixel-and-snap-2d-transforms-to-pixel/78642) — practitioner discussion of the two snap settings' differing effects, matching §7's "transforms first, vertices only if needed" guidance.
- **Aseprite documentation** (aseprite.org/docs) — the de-facto pixel-art authoring tool; its sheet-export options (strips, padding, JSON metadata) map directly onto §9's layout conventions and the CLI flags used in §9's build-script example.
- [Godot demo projects (github.com/godotengine/godot-demo-projects)](https://github.com/godotengine/godot-demo-projects) — official, version-matched sample projects; the 2D folder contains runnable references for sprite animation, viewports and screen-capture patterns that pair well with this module's labs.
- **Lospec** (lospec.com) — community hub for pixel-art palettes and tutorials; relevant here because disciplined palettes are what make §3's exact-match palette swapping and §16's channel-packed masks workable in practice.

Sibling modules in this course:

- [SCENES_AND_NODES.md](SCENES_AND_NODES.md) — the node/scene/resource foundations this module builds on.
- [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) — tweens, modulate choreography, draw order and visibility: the "motion" half continues there.
- [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md) — TileSet atlases apply §9's atlas thinking to level geometry.
- [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md) — Y-sorting and depth for the isometric look, where §8's anchor/offset decisions become critical.
- [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md) — palette LUTs, dissolves and every "per-pixel, per-frame" effect this module deferred.
- [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) — the full budgeting methodology sketched in §16.

---

## Glossary

| Term | Definition |
|---|---|
| **Texture** | GPU-resident image data an engine samples when drawing; in Godot, any `Texture2D` subclass. |
| **Sprite** | A 2D image drawn at a transform in the game world; in Godot, typically a `Sprite2D`/`AnimatedSprite2D` node showing a texture. |
| **Sprite2D** | The basic "draw one texture" 2D node: anchor, offset, flip, grid-slicing (`hframes`/`vframes`) and region support. |
| **AnimatedSprite2D** | Node that plays named flipbook animations from a `SpriteFrames` resource on its own clock. |
| **SpriteFrames** | Resource holding named animations — ordered frame textures with fps, loop flag and per-frame duration multipliers. |
| **AtlasTexture** | A `Texture2D` exposing a rectangular region of another texture; the building block of sheet slicing. |
| **Spritesheet / atlas** | One image packing many sprites/frames; improves batching and load behavior at some iteration cost. |
| **Texture bleeding** | Neighboring atlas cells leaking into a frame's edge via linear filtering, mipmaps or repeat wrapping. |
| **Nearest (filter)** | Sampling that picks the single closest texel — crisp, blocky; the pixel-art filter. |
| **Linear (filter)** | Bilinear sampling blending the 4 nearest texels — smooth; blurs pixel art. |
| **Mipmaps** | Precomputed half-resolution texture chain (+~33% memory) that prevents shimmer when drawing textures smaller than native. |
| **Import pipeline** | Godot's conversion of source assets into engine-native cached artifacts (`.godot/imported/*.ctex`), configured per file by `.import` files. |
| **`.import` file** | Versionable text sidecar recording importer, options and cache paths for one asset. |
| **CompressedTexture2D** | Runtime class of imported textures — "compressed" refers to the storage container, which may hold lossless data. |
| **Lossless / Lossy / VRAM Compressed** | Import compress modes: exact pixels; smaller-on-disk with artifacts; GPU block-compressed (4-6× less VRAM, block artifacts — never for pixel art). |
| **VRAM** | Video memory holding textures and buffers; measured via `Performance.RENDER_TEXTURE_MEM_USED` and the Video RAM panel. |
| **Draw call** | One draw command submitted to the GPU; CPU-side overhead makes thousands of small ones expensive. |
| **Batching** | The 2D renderer merging consecutive draws that share texture and material into one draw call. |
| **Image (class)** | CPU-side pixel buffer with lock-free read/write (`get_pixel`/`set_pixel`), load/save and compositing operations. |
| **ImageTexture** | GPU texture created from an `Image` at runtime; updated in place via `update()` (same size/format) or replaced via `set_image()`. |
| **ViewportTexture** | Texture showing a `SubViewport`'s live rendered output — Godot's render-to-texture. |
| **NoiseTexture2D** | Procedural texture rendering a `FastNoiseLite` noise field; generates asynchronously (`await changed`). |
| **Pixel snapping** | Rounding rendered 2D transforms/vertices to whole pixels (`rendering/2d/snap/*`) to kill sub-pixel wobble. |
| **Integer scaling** | Restricting the final upscale to whole multiples so every source pixel covers an equal number of screen pixels. |
| **Nine-patch (9-slice)** | Scaling scheme keeping a texture's corners fixed while edges/center stretch or tile; `NinePatchRect` / `StyleBoxTexture`. |
| **Modulate** | `CanvasItem` color multiplier; `modulate` affects the node and its canvas descendants, `self_modulate` only the node itself. |
| **Flipbook animation** | Animation by swapping discrete frames over time — the technique behind both `AnimatedSprite2D` and keyed `frame` tracks. |
| **Channel packing** | Storing independent grayscale maps in the R/G/B/A channels of one texture to save samplers and memory. |
| **Autoplay** | Per-animation flag (`AnimatedSprite2D.autoplay` / SpriteFrames panel) starting playback when the node enters the tree. |
| **detect_3d** | Import tripwire that silently re-imports a texture with 3D-friendly (pixel-art-hostile) settings on first 3D use; disable in 2D projects. |
| **UID (`uid://`)** | Stable resource identifier recorded in `.import` files; keeps references alive across moves and renames. |
| **StyleBoxTexture** | Theme-system resource providing 9-slice drawing plus content margins; the skinnable sibling of `NinePatchRect`. |
| **MultiMesh** | One mesh drawn N times with per-instance transforms in a single draw call; `MultiMeshInstance2D` is its 2D node. |
| **frame_progress** | `AnimatedSprite2D`'s fractional position within the current frame (0-1); copied via `set_frame_and_progress()` to hard-sync layered sprites. |
| **Blend space** | AnimationTree node selecting/blending clips by a 1D or 2D parameter (e.g. movement direction); Discrete mode suits flipbooks. |
| **Trimming** | Packer optimization that crops transparent borders off packed sprites; must be compensated (e.g. `AtlasTexture.margin`) to preserve frame alignment. |

---

> **Module 03 — Sprites and Textures** · Course: *Godot 4 in Production* · Previous: [SCENES_AND_NODES.md](SCENES_AND_NODES.md) · Next: [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md)

