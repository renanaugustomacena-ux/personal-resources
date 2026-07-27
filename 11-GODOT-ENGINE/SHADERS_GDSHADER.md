---
course: "Godot 4 in Production"
phase: "5 — Specialized modules"
module: "12"
title: "Shaders and GDShader — 2D Shader Programming for Pixel Art"
version: "Godot 4.5 / GDScript 2.0"
level: "Intermediate-Advanced"
prerequisites: [ "SPRITES_AND_TEXTURES.md", "RENDERING_AND_VISUAL_LOGIC.md" ]
objectives:
  - "Write canvas_item shaders from scratch using GDShader types, uniforms, varyings, and the vertex/fragment/light stages"
  - "Use every canvas_item built-in variable correctly, knowing which are read-only and which are writable"
  - "Drive shader parameters from GDScript with set_shader_parameter, instance uniforms (4.4+), and global shader uniforms"
  - "Build screen-reading and full-screen post-processing effects with hint_screen_texture, BackBufferCopy, and CanvasLayer recipes"
  - "Implement fourteen production shader recipes: outline, hit-flash, dissolve, palette swap, CRT, Bayer dithering, radial wipe, and more"
  - "Diagnose compile errors, invisible effects, and pipeline-compilation stutter with a repeatable debugging workflow"
  - "Preserve crisp pixel-art edges under shader effects with nearest sampling, TEXTURE_PIXEL_SIZE math, and integer snapping"
tags: [godot, gdshader, shaders, canvas-item, 2d, pixel-art, post-processing, uniforms, screen-texture, glsl, performance, rendering]
---

# Shaders and GDShader — 2D Shader Programming for Pixel Art — Complete Guide

> **Module 12** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Sprites and Textures](SPRITES_AND_TEXTURES.md), [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) · helpful: basic linear algebra (vec2/vec3/vec4) and any prior GLSL/HLSL exposure.
>
> By the end of this module you will be able to:
> 1. Explain what runs on the GPU when Godot draws a `CanvasItem`, and why fragment work is paid *per pixel, per frame*.
> 2. Write complete `canvas_item` shaders using GDShader types, control flow, functions, includes, and the preprocessor.
> 3. Use the `vertex()`, `fragment()`, and `light()` stages with their exact built-in variables (and know which ones are writable).
> 4. Connect GDScript to shaders through uniforms, per-instance uniforms, uniform arrays, and project-wide global uniforms.
> 5. Read the screen with `hint_screen_texture` and build full-screen post-processing with `CanvasLayer` + `ColorRect` and `BackBufferCopy`.
> 6. Ship the module's recipe cookbook — outline, hit-flash, dissolve, palette swap, pixelate, CRT, dithering, radial wipe, and friends — and adapt each one.
> 7. Debug broken shaders methodically and keep effects cheap enough for an always-running desktop companion like **Relax Room**.
>
> **Estimated time:** 8-10 hours reading and experimenting · 6-8 hours of labs
> **Level:** Intermediate-Advanced

## Guiding ideas

1. **GDShader is GLSL-flavored, not GLSL exact.** `shader_type`, `render_mode`, hints, and built-ins are Godot inventions — port GLSL knowledge, not GLSL files.
2. **`canvas_item` shaders for 2D, `spatial` for 3D. No mixing.** A shader's first line decides which pipeline, built-ins, and render modes exist.
3. **The GPU runs `fragment()` for every covered pixel, every frame.** Think in parallel; the cost model is *pixels × instructions × texture fetches*.
4. **Uniforms are the contract between GDScript and the GPU.** Everything dynamic flows through `set_shader_parameter`, instance uniforms, or globals — never by editing shader code at runtime.
5. **Shader > tween for per-pixel effects; tween > shader for property motion.** A tween animates a property over time; a shader decides every pixel's color. Pick the tool that matches the granularity.
6. **Pixel art needs care.** Nearest filtering, `TEXTURE_PIXEL_SIZE`-aligned offsets, and integer snapping keep the grid crisp; one careless bilinear sample smears the whole aesthetic.

## Concept map

```
                          ┌────────────────────────────┐
                          │   GDSHADER (canvas_item)   │
                          └──────────────┬─────────────┘
                                         │
        ┌───────────────────┬────────────┼──────────────────┬───────────────────┐
        │                   │            │                  │                   │
  ┌─────▼──────┐    ┌──────▼──────┐  ┌───▼────────┐  ┌──────▼───────┐  ┌───────▼───────┐
  │  LANGUAGE  │    │  PIPELINE   │  │  BRIDGE    │  │  SCREEN FX   │  │    CRAFT      │
  └─────┬──────┘    └──────┬──────┘  └───┬────────┘  └──────┬───────┘  └───────┬───────┘
        │                  │             │                  │                  │
  ┌─────┴──────┐    ┌──────┴──────┐  ┌───┴────────┐  ┌──────┴───────┐  ┌───────┴───────┐
  │types/arrays│    │vertex()     │  │uniforms +  │  │hint_screen_  │  │recipe         │
  │swizzling   │    │fragment()   │  │hints       │  │texture       │  │cookbook       │
  │precision   │    │light()      │  │set_shader_ │  │SCREEN_UV     │  │pixel-art      │
  │control flow│    │built-ins    │  │parameter   │  │BackBufferCopy│  │crispness      │
  │functions   │    │render_mode  │  │instance    │  │CanvasLayer + │  │performance    │
  │varyings    │    │blend modes  │  │uniforms    │  │ColorRect     │  │(fill rate,    │
  │#include /  │    │TIME clock   │  │global      │  │post-process  │  │ stutter)      │
  │preprocessor│    │             │  │uniforms    │  │multi-pass    │  │debugging      │
  └────────────┘    └─────────────┘  └────────────┘  └──────────────┘  └───────────────┘
```

## Table of contents

1. [Overview: why shaders in a desktop companion](#1-overview-why-shaders-in-a-desktop-companion)
2. [Mental model: what runs on the GPU](#2-mental-model-what-runs-on-the-gpu)
3. [GDShader vs GLSL](#3-gdshader-vs-glsl)
4. [Language fundamentals](#4-language-fundamentals)
5. [Functions, includes and the preprocessor](#5-functions-includes-and-the-preprocessor)
6. [shader_type and render_mode](#6-shader_type-and-render_mode)
7. [Built-in variables for canvas_item](#7-built-in-variables-for-canvas_item)
8. [Uniforms deep dive](#8-uniforms-deep-dive)
9. [Varyings and interpolation](#9-varyings-and-interpolation)
10. [ShaderMaterial workflow](#10-shadermaterial-workflow)
11. [Screen-reading shaders and post-processing](#11-screen-reading-shaders-and-post-processing)
12. [Shader animation and TIME](#12-shader-animation-and-time)
13. [Recipe cookbook I: sprite effects](#13-recipe-cookbook-i-sprite-effects)
14. [Recipe cookbook II: retro and full-screen effects](#14-recipe-cookbook-ii-retro-and-full-screen-effects)
15. [Recipe cookbook III: motion and gameplay effects](#15-recipe-cookbook-iii-motion-and-gameplay-effects)
16. [Visual shaders](#16-visual-shaders)
17. [Performance](#17-performance)
18. [Debugging shaders](#18-debugging-shaders)
19. [Pixel-art shader craft and the Relax Room](#19-pixel-art-shader-craft-and-the-relax-room)
20. [Best practices](#best-practices)
21. [Common errors & troubleshooting](#common-errors--troubleshooting)
22. [Exercises](#exercises)
23. [Further reading](#further-reading)
24. [Glossary](#glossary)

---

## 1. Overview: why shaders in a desktop companion

Everything Godot draws in 2D — every `Sprite2D`, `TileMapLayer`, `Label`, `ColorRect` — is ultimately rendered by a shader. When you do not provide one, Godot supplies a default `canvas_item` shader that samples the node's texture, multiplies it by modulate colors, and writes the result. Writing your own shader means *replacing* that default program with one that you control, pixel by pixel.

For **Relax Room**, our desktop-companion case study, shaders are not optional polish. They are the difference between "a sprite that changes" and "a scene that feels alive":

- The pet's **hit-flash** and **outline-on-hover** feedback are single-material effects that would be awkward and expensive to fake with duplicated sprites.
- The **day-night tint** that follows the user's real clock is one global uniform read by every material in the room — no script touches individual nodes.
- The optional **CRT filter** and **Bayer dithering** looks are full-screen post-processing passes: one `ColorRect` on a `CanvasLayer`, one shader, zero changes to the scene beneath.
- **Dissolve** transitions between room states replace scene-wide `AnimationPlayer` choreography with a two-line progress uniform driven by a tween.

There is also a performance argument that matters *more* for a companion app than for a game. Relax Room runs all day next to the user's real work, so [Desktop Companion Performance](DESKTOP_COMPANION_PERFORMANCE.md) sets a strict CPU budget. Shaders move per-pixel work from GDScript (interpreted, single-threaded, per-frame allocations) to the GPU (massively parallel, designed for exactly this). A GDScript loop touching every pixel of a 64×64 sprite is 4,096 interpreted iterations per frame; a fragment shader does the same work in what is effectively "free real estate" on any GPU from the last fifteen years — *if* you follow the cost model in [§17](#17-performance).

### What this module covers, and what it does not

We focus on `shader_type canvas_item` — the 2D pipeline — because that is what a pixel-art desktop companion uses. The `spatial` (3D), `particles`, `sky`, and `fog` shader types are introduced in [§6](#6-shader_type-and-render_mode) so you can recognize them, but their built-ins and techniques are out of scope. Compute shaders (GLSL files dispatched through `RenderingDevice`) are a different technology entirely and belong to an advanced rendering module.

### Your first shader in ninety seconds

Before any theory, put a shader on screen — the loop you are about to learn is only pleasant if you have felt how fast it is:

1. Open any scene with a `Sprite2D` (or make one with the Godot icon).
2. Inspector → *CanvasItem → Material* → **New ShaderMaterial** → click it → *Shader* → **New Shader** → name it `first.gdshader` → click it to open the shader editor.
3. Type:

```glsl
shader_type canvas_item;

void fragment() {
    vec4 base = texture(TEXTURE, UV);
    base.rgb = base.rgb * vec3(1.0, 0.6, 0.6);   // redden
    base.rgb *= 0.8 + 0.2 * sin(TIME * 3.0);     // pulse
    COLOR = base;
}
```

4. Watch the sprite pulse red, live, in the editor viewport — no save, no run, no compile step visible to you.
5. Change `3.0` to `12.0` and watch the pulse speed change *as you type*.

That immediacy is the workflow (§18.3 formalizes it). Everything else in this module is vocabulary for what you can type into that box.

> ✅ **Best practice** — Treat this module as two passes. First pass: read §1-§12 with the shader editor open, typing every example into a scratch `Sprite2D`. Second pass: work through the cookbook (§13-§15) and the labs, adapting each recipe to your own project assets.

## 2. Mental model: what runs on the GPU

### 2.1 The journey of a CanvasItem

When Godot renders a frame, each visible `CanvasItem` contributes one or more *draw commands*. For a `Sprite2D`, the command is essentially: "draw this quad (two triangles, four vertices) with this texture and this material." The GPU processes the command in stages, and your shader plugs into three of them:

```
  CPU (Godot)                      GPU
 ─────────────                    ─────────────────────────────────────────────
  scene tree      ─────────▶       vertex()      runs once per VERTEX (4 for
  draw commands                       │          a Sprite2D quad) — can move
  uniforms                            │          vertices, set varyings
  textures                            ▼
                                   rasterizer    fixed function: decides which
                                      │          screen pixels the triangles
                                      │          cover, interpolates UV/COLOR
                                      ▼
                                   fragment()    runs once per covered pixel —
                                      │          computes COLOR
                                      ▼
                                   light()       runs once per pixel *per
                                      │          Light2D touching it* (only if
                                      ▼          the item is shaded)
                                   blending      COLOR combined with what is
                                                 already in the framebuffer
                                                 (render_mode blend_*)
```

Three consequences fall out of this picture and explain almost every rule in the module:

1. **`vertex()` is cheap, `fragment()` is where the money goes.** A `Sprite2D` has 4 vertices but can cover hundreds of thousands of pixels when scaled up. Anything you can compute per-vertex and interpolate (via a varying, [§9](#9-varyings-and-interpolation)) instead of per-pixel is nearly free.
2. **Stages communicate forward only.** `vertex()` can pass data to `fragment()`; `fragment()` cannot ask the vertex stage anything, and neither stage can read the result of another pixel's computation. Each fragment invocation is an island: its inputs are built-ins, uniforms, varyings, and texture reads.
3. **You never "loop over pixels."** The GPU launches thousands of fragment invocations in parallel. Your `fragment()` function describes what *one* pixel does; the hardware handles the rest.

### 2.2 Per-pixel parallelism and why branches cost

GPUs execute fragments in *lockstep groups* (warps/wavefronts of 32-64 invocations). Every invocation in a group runs the same instruction at the same time. This is why GPU folklore says "branches are expensive" — but the truth is more precise, and worth stating carefully because the folklore causes people to write worse code:

- **A branch on a uniform or constant is essentially free.** All invocations take the same path, so the hardware just skips the dead branch. `if (enable_outline) { ... }` where `enable_outline` is a uniform costs nothing meaningful.
- **A branch on per-pixel data (UV, texture reads) is *divergent*.** If some invocations in a group take the `if` and others the `else`, the hardware executes *both* paths for the whole group, masking out the inactive lanes. You pay for the sum of both branches — you do not crash, and it is often still faster than the branchless alternative if one path is rare and cheap.
- **Loops with a dynamic trip count keep the whole group alive** until the slowest invocation finishes. Fixed-count loops (`for (int i = 0; i < 9; i++)`) are unrolled or executed uniformly and are fine.

The practical rules: prefer `mix()`, `step()`, and `smoothstep()` for small either/or decisions (they compile to a couple of instructions with no divergence), but do not contort readable code to avoid an `if` on a uniform. [§17.3](#17-performance) revisits this with measurements in mind.

### 2.3 What the shader cannot do

Fragment shaders have hard limits that beginners bump into within the first hour, so let's list them up front:

| You might want to… | Reality in a canvas_item shader |
|---|---|
| Draw outside the node's rect | Impossible from `fragment()` — the rasterizer only generates fragments inside the triangles. Grow the geometry in `vertex()` or add transparent padding to the texture. |
| Read the pixel you are about to write | Impossible — but you can read *the screen as it was before this item drew* via `hint_screen_texture` ([§11](#11-screen-reading-shaders-and-post-processing)). |
| Remember state between frames | Uniforms are your only memory; the shader itself is stateless. Persist state in GDScript and feed it in, or render to a `SubViewport` and sample it next frame. |
| Return data to GDScript | One-way street. GPU→CPU readback exists (`Viewport.get_texture().get_image()`) but stalls the pipeline; treat it as a debugging tool, not an architecture. |
| `print()` for debugging | No such thing. You debug by *writing colors* — see [§18](#18-debugging-shaders). |

> ⚠️ **Pitfall** — The single most common beginner surprise: an outline or drop-shadow shader "does not work" because the sprite's texture has no transparent margin and the effect has no pixels to draw into. The shader can only color pixels the quad covers. Fix it in the art (padding) or in `vertex()` (grow the quad and compensate UV), never by wishing.

### 2.4 Where materials meet batching

One more piece of the mental model pays for itself later: Godot's 2D renderer **batches** — it merges consecutive draw commands that share the same shader, material, texture, and blend state into a single GPU submission. Batching is why a `TileMapLayer` with ten thousand tiles is one draw call, not ten thousand.

Shaders interact with batching in exactly one way: **state changes break batches**. Every time the renderer must switch material (different shader *or* different uniform values held in a different material resource), the current batch ends and a new one starts. The implications, previewed here and developed in §8.5 and §17:

- Fifty sprites sharing one `ShaderMaterial` → potentially one batch.
- Fifty sprites each holding `material.duplicate()` → fifty state changes, even though the *code* is identical.
- Fifty sprites sharing one material with **instance uniforms** for their per-node differences → batching preserved *and* per-node variation. This is the feature's entire reason to exist.

You can watch this live: Debugger → Monitors → *Raster* → "Draw Calls in Frame". Toggle between the three arrangements above and the graph tells the story better than any paragraph.

## 3. GDShader vs GLSL

GDShader is Godot's own shading language. It is deliberately close to **GLSL ES 3.0** — types, operators, and most built-in functions carry over — but it is a *dialect*, and the differences are exactly the things you will type most often. If you arrive from raw OpenGL, WebGL, or Shadertoy, this table is your porting guide:

| Concern | Raw GLSL (ES 3.0) | GDShader (Godot 4.x) |
|---|---|---|
| Program declaration | Separate vertex + fragment files, `void main()` in each | One `.gdshader` file; `shader_type canvas_item;` header; optional `vertex()`, `fragment()`, `light()` functions |
| Entry point | `void main()` | `void fragment()`, `void vertex()`, `void light()` — all optional; omitted stages use Godot's default behavior |
| Vertex→fragment data | `out` in vertex shader, `in` in fragment | `varying` declared once at file scope, written in `vertex()`, read in `fragment()`/`light()` |
| Uniform UI | None (raw API calls) | Hints generate Inspector widgets: `uniform vec4 c : source_color;`, `hint_range(0,1)` |
| Screen access | Manual framebuffer copy + sampler | `uniform sampler2D t : hint_screen_texture;` + `SCREEN_UV` |
| Textures | You bind units yourself | `TEXTURE` built-in = the node's own texture; extra samplers are uniforms with filter/repeat hints |
| Outputs | `out vec4 fragColor` (name it yourself) | Write to the built-in `COLOR` |
| Coordinates | `gl_FragCoord`, `gl_Position` | `FRAGCOORD`, and `VERTEX` (2D local position, already "unprojected") |
| Time | Pass a uniform yourself | `TIME` built-in, engine-managed ([§12](#12-shader-animation-and-time)) |
| Preprocessor | Full C-style | Supported subset: `#include` (`.gdshaderinc`), `#define`, `#if[def]`… ([§5](#5-functions-includes-and-the-preprocessor)) |
| Constants | `const float PI = 3.14159;` yourself | `PI`, `TAU`, `E` are built-in |
| Blend state | Set on the CPU via API | Declared in the shader: `render_mode blend_add;` |

Two mindset shifts matter more than any single row:

**First**, GDShader files are *self-describing materials*. A `.gdshader` file declares its pipeline (`shader_type`), its fixed-function state (`render_mode`), its editable parameters (uniform hints), and its code — everything the renderer and the Inspector need. There is no separate "material definition" format; a `ShaderMaterial` is just a shader plus current uniform values ([§10](#10-shadermaterial-workflow)).

**Second**, Godot compiles your GDShader into *actual* backend shaders (GLSL for the Compatibility renderer, SPIR-V via Vulkan/D3D12/Metal for Forward+ and Mobile), weaving your functions into its own template that handles transforms, batching, and lighting. This is why you write `fragment()` and not `main()`: your code is a hook inside a larger generated program. It also explains compile-time surprises — an error may point at generated code context — and the pipeline-stutter story in [§17.5](#17-performance).

> ✅ **Best practice** — When porting a Shadertoy or Book of Shaders snippet: replace `mainImage(out vec4 fragColor, in vec2 fragCoord)` with `void fragment()`, `fragCoord` with `FRAGCOORD.xy` (or better, `UV`/`SCREEN_UV`), `iTime` with `TIME`, `iResolution` with `1.0 / SCREEN_PIXEL_SIZE`, and the final `fragColor =` with `COLOR =`. Ninety percent of 2D snippets port in five minutes with exactly these substitutions.

### 3.1 Porting cheat sheet: Godot 3.x → Godot 4.x

A large share of community shader code online still targets Godot 3. These are the renames and removals you will hit when pasting it into 4.5 — memorize the first two rows and look up the rest:

| Godot 3.x | Godot 4.x | Notes |
|---|---|---|
| `texture(SCREEN_TEXTURE, SCREEN_UV)` | `uniform sampler2D t : hint_screen_texture;` + `textureLod(t, SCREEN_UV, 0.0)` | The built-in is gone; declare the sampler yourself (§11.1) |
| `hint_color` | `source_color` | Same idea, renamed; also applies to sampler color hints |
| `.shader` file extension | `.gdshader` | 4.x also adds `.gdshaderinc` includes (§5.2) |
| `set_shader_param()` | `set_shader_parameter()` | GDScript API rename; property path is now `shader_parameter/name` |
| `WORLD_MATRIX` | `MODEL_MATRIX` | Same matrix, clearer name |
| `EXTRA_MATRIX` | removed | Was mostly internal; restructure around `CANVAS_MATRIX`/`SCREEN_MATRIX` |
| `LIGHT_VEC`, `SHADOW_VEC` | `LIGHT_DIRECTION`, `SHADOW_VERTEX` | Light stage reworked; see the §7.4 table for the full 4.x set |
| `NORMALMAP`, `NORMALMAP_DEPTH` | `NORMAL_MAP`, `NORMAL_MAP_DEPTH` | Underscore added |
| `SCREEN_TEXTURE` mip via `textureLod` | same call, but requires a `filter_*_mipmap` hint on the sampler | Mipmaps are opt-in per uniform in 4.x |
| `DEPTH_TEXTURE` | `hint_depth_texture` uniform — **spatial only** | Never available to canvas_item in either version |
| `render_mode blend_*` | unchanged | The canvas_item blend list survives intact (§6.2) |

If a pasted 3.x shader produces a wall of errors, fix them top-to-bottom with this table before judging the shader itself — the *logic* of 3.x canvas shaders almost always survives; only the declarations rot.

## 4. Language fundamentals

### 4.1 Anatomy of a shader file

Every `.gdshader` file follows the same skeleton. Here is a minimal but complete example with each part labeled:

```glsl
// 1. Pipeline selection — must be the first statement.
shader_type canvas_item;

// 2. Fixed-function state (optional).
render_mode blend_mix;

// 3. Includes and preprocessor (optional) — see §5.
#include "res://shaders/common/color_utils.gdshaderinc"

// 4. Uniforms: parameters visible to the Inspector and GDScript.
uniform vec4 tint : source_color = vec4(1.0);
uniform float strength : hint_range(0.0, 1.0) = 0.5;

// 5. Varyings: data computed per-vertex, interpolated per-pixel.
varying vec2 local_pos;

// 6. Constants and helper functions.
const float EPSILON = 0.0001;

float luminance(vec3 rgb) {
    return dot(rgb, vec3(0.2126, 0.7152, 0.0722));
}

// 7. Stage functions — any subset of vertex(), fragment(), light().
void vertex() {
    local_pos = VERTEX;
}

void fragment() {
    vec4 base = texture(TEXTURE, UV);
    COLOR = mix(base, tint * base.a, strength);
}
```

Statements end with semicolons. Comments are C-style (`//` and `/* */`). Identifiers are case-sensitive; built-ins are ALL_CAPS by convention, which conveniently keeps your own names from colliding.

### 4.2 Scalar and vector types

GDShader inherits the GLSL ES 3.0 type zoo:

| Category | Types | Notes |
|---|---|---|
| Void | `void` | Function return only |
| Boolean | `bool`, `bvec2`, `bvec3`, `bvec4` | Result of comparisons; `bvec` from `equal()`, `lessThan()`, etc. |
| Integer | `int`, `ivec2`, `ivec3`, `ivec4` | 32-bit signed; `%` works on ints |
| Unsigned | `uint`, `uvec2`, `uvec3`, `uvec4` | Literal suffix `u`: `3u` |
| Float | `float`, `vec2`, `vec3`, `vec4` | The workhorses; literals need a decimal point |
| Matrix | `mat2`, `mat3`, `mat4` | Column-major, like GLSL |
| Samplers | `sampler2D`, `isampler2D`, `usampler2D`, `sampler2DArray`, `sampler3D`, `samplerCube`, … | **Uniforms only** — cannot be locals or function-local arrays |

The single biggest syntax trap for GDScript programmers: **GDShader does not implicitly convert `int` to `float`.** In GDScript, `x * 2` works on floats. In GDShader, `some_float * 2` is a compile error ("invalid arguments to operator"); you must write `some_float * 2.0`. Constructors convert explicitly: `float(my_int)`, `int(my_float)` (truncates), `vec2(1.0)` (splats to both components).

Vector constructors are flexible and compose:

```glsl
vec3 a = vec3(1.0);              // (1.0, 1.0, 1.0) — splat
vec4 b = vec4(a, 0.5);           // vec3 + float
vec4 c = vec4(a.xy, 0.0, 1.0);   // vec2 + two floats
mat2 rot = mat2(vec2(c0), vec2(c1));  // matrices from column vectors
```

### 4.3 Swizzling

Vector components are addressed through three interchangeable letter sets — `xyzw` (positions), `rgba` (colors), `stpq` (texture coordinates). You can read any combination, in any order, with repetition:

```glsl
vec4 col = texture(TEXTURE, UV);
vec3 rgb   = col.rgb;      // first three components
vec3 bgr   = col.bgr;      // reversed — free channel swap!
vec3 grey3 = col.rrr;      // repetition allowed when reading
vec2 ar    = col.ar;       // any subset, any order
```

Writing through a swizzle is allowed *without* repetition — each target component may appear only once:

```glsl
col.rgb = vec3(0.0);       // OK
col.br  = col.rb;          // OK — swaps red and blue
// col.rr = vec2(1.0);     // ERROR: 'r' assigned twice
```

Swizzling is not sugar — it compiles to register selection and is completely free. Idiomatic shader code leans on it heavily: `COLOR.rgb *= 0.5;` dims without touching alpha; `uv.yx` transposes; `col.a` isolates coverage.

### 4.4 Precision qualifiers

Every float-family declaration can carry a precision qualifier: `lowp` (~8-bit fixed), `mediump` (~16-bit half float), `highp` (32-bit, the default in Godot):

```glsl
lowp vec4 tint = vec4(0.5);      // fine for colors in 0-1
mediump vec2 offset;              // fine for small UV deltas
highp float world_x;              // needed for large coordinates
```

On desktop GPUs these are usually ignored (everything runs highp), so for the Relax Room target platform they are documentation more than optimization. On mobile GPUs they matter a great deal — `mediump` halves register pressure and can double throughput — but they also cause the classic "works on desktop, banding/garbage on Android" bug when 16 bits cannot represent your values (large `TIME` values are the classic offender). Rule of thumb: colors and normalized factors may be `lowp`/`mediump`; UVs, positions, and time should stay `highp` unless profiled.

### 4.5 Arrays

Arrays exist at global scope (as `const` or `uniform`) and locally inside functions:

```glsl
// Local, with three equivalent initializer forms:
float weights[3];
float kernel[] = { 0.25, 0.5, 0.25 };
float kernel2[3] = float[3](0.25, 0.5, 0.25);

// Global constant array — the Bayer matrix in §14 uses this:
const int BAYER[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6,
                              3, 11, 1, 9, 15, 7, 13, 5);

// Uniform array — sized, no default values allowed:
uniform vec3 palette[8];
```

Arrays have a `.length()` method, handy for loops: `for (int i = 0; i < kernel.length(); i++)`. Restrictions to remember: sampler arrays cannot be local variables; uniform arrays cannot declare per-element defaults in the shader (initialize them from GDScript with a typed array, see [§8.4](#8-uniforms-deep-dive)); and indexing with a *dynamic* (per-pixel) index may force the compiler to spill the array to slower storage — constant or uniform indices are cheapest.

### 4.6 Matrices and 2D rotation

Matrices appear in 2D shader work in exactly two roles: the pipeline's transform built-ins (§7.2 — which you mostly leave alone) and *your own* small rotations/skews of UVs or offsets. The idioms:

```glsl
// Construct a 2D rotation matrix (column-major: each vec2 is a COLUMN):
mat2 rot2(float angle) {
    float s = sin(angle);
    float c = cos(angle);
    return mat2(vec2(c, s), vec2(-s, c));
}

void fragment() {
    // Rotate UVs around the sprite center:
    vec2 uv = rot2(TIME * 0.5) * (UV - 0.5) + 0.5;
    COLOR = texture(TEXTURE, uv);
}
```

Rules that prevent the classic transposition bug: GDShader matrices are **column-major** like GLSL — `mat2(a, b)` takes columns, and `M * v` treats `v` as a column vector. If a rotation goes the "wrong way," you have either swapped the sign of `s` or multiplied `v * M` (row-vector convention) — both produce the transpose. Matrix-matrix multiplication composes right-to-left: `A * B * v` applies `B` first. And the `mat3`/`mat4` constructors accept smaller matrices for embedding (`mat3(m2)` pads with identity), which matters only on the rare day you feed a custom transform into `MODEL_MATRIX` math under `skip_vertex_transform`.

The sepia matrix in §13.6 and this rotation are the two matrix uses the whole module needs — if you find yourself writing heavier matrix code in a canvas_item shader, step back and check whether a varying (§9) or a GDScript-side `Transform2D` uniform expresses it more clearly.

### 4.7 Control flow

`if`/`else`, `switch` (on ints), `for`, `while`, `do…while`, `break`, `continue` all work as in C. Two shader-specific keywords:

- `discard;` — valid only in `fragment()`; abandons the pixel entirely (nothing is written, not even to depth in 3D). This is how the dissolve recipe punches holes. Note that discarding does *not* refund the cost of work already done for that pixel, and heavy use can defeat early-depth optimizations in 3D — in 2D it is generally fine.
- There is no recursion, ever — the compiler rejects it. All loops must have compile-time-boundable behavior in practice; a `while` that depends on a texture read will compile, but see the divergence discussion in [§2.2](#2-mental-model-what-runs-on-the-gpu).

The built-in function library is the GLSL ES 3.0 set: `mix`, `step`, `smoothstep`, `clamp`, `fract`, `floor`, `ceil`, `round`, `mod`, `abs`, `sign`, `min`, `max`, `pow`, `exp`, `log`, `sqrt`, `sin`/`cos`/`tan` and inverses, `atan(y, x)`, `length`, `distance`, `normalize`, `dot`, `cross`, `reflect`, `refract`, texture functions (`texture`, `textureLod`, `texelFetch`, `textureSize`), derivative functions (`dFdx`, `dFdy`, `fwidth`), and the pack/unpack family. Three idioms you will use constantly:

```glsl
// 1. Branchless threshold: 0.0 below edge, 1.0 at/above.
float mask = step(0.5, value);

// 2. Smooth threshold with antialiased edge:
float soft = smoothstep(0.45, 0.55, value);

// 3. Linear blend — the single most used function in this module:
vec3 result = mix(color_a, color_b, t);   // t in 0-1
```

> ✅ **Best practice** — `smoothstep(a, b, x)` with a narrow `a`-`b` band is the shader equivalent of antialiasing. Whenever a hard `step()` edge shimmers or crawls (common on rotating sprites), widen it into a `smoothstep` over one pixel: `smoothstep(edge - fwidth(x), edge + fwidth(x), x)`. For pixel art you often *want* the hard edge — see §19 for when to break this rule.

### 4.8 A worked example: tint-by-height

Let's tie the fundamentals together with a small, complete shader that tints a sprite darker toward its bottom — a cheap fake ambient occlusion used on furniture sprites in Relax Room:

```glsl
shader_type canvas_item;

uniform vec4 shade_color : source_color = vec4(0.1, 0.05, 0.2, 1.0);
uniform float shade_start : hint_range(0.0, 1.0) = 0.55;
uniform float shade_max : hint_range(0.0, 1.0) = 0.45;

void fragment() {
    vec4 base = texture(TEXTURE, UV);                 // node's own texture
    float t = smoothstep(shade_start, 1.0, UV.y);     // 0 at top band, 1 at bottom
    vec3 shaded = mix(base.rgb, shade_color.rgb, t * shade_max);
    COLOR = vec4(shaded, base.a);                     // never forget alpha
}
```

Line by line: `UV.y` runs 0→1 top→bottom over the sprite's texture; `smoothstep` remaps the lower portion into a 0→1 ramp; `mix` blends toward the shade color, scaled by `shade_max` so it never fully replaces the art; the final constructor reassembles the color with the *original* alpha so transparent pixels stay transparent. That last line embodies a habit worth building: in canvas_item shaders, treat `.rgb` and `.a` as separate channels with separate stories, and recombine deliberately.

### 4.9 Built-in function quick reference

The functions below are the working vocabulary of every recipe in §13-§15. All are component-wise on vectors unless noted. This is a *selection* ordered by how often this module uses them — the full list lives in the official shading-language reference.

**Interpolation and thresholds** — the big three:

| Function | Returns | Typical use |
|---|---|---|
| `mix(a, b, t)` | `a` when `t`=0, `b` when `t`=1, linear between | Every blend, tint, crossfade in this module |
| `step(edge, x)` | 0.0 if `x < edge`, else 1.0 | Hard masks, branchless selects |
| `smoothstep(e0, e1, x)` | 0→1 with Hermite easing across `e0..e1` | Soft masks, antialiased edges, band carving (§14.5) |
| `clamp(x, lo, hi)` | `x` limited to `[lo, hi]` | Guarding computed colors/UVs |

**Shaping and repetition:**

| Function | Returns | Typical use |
|---|---|---|
| `fract(x)` | Fractional part | Tiling patterns, wrapping phases (§12.1) |
| `floor(x)` / `ceil(x)` / `round(x)` | Integer-valued floats | Quantization (§14.1, §14.3), texel snapping (§19.2) |
| `mod(x, y)` | Float modulo | Repeating stripes/grids (int `%` exists for ints) |
| `abs(x)` / `sign(x)` | Magnitude / -1,0,1 | Symmetric falloffs, direction extraction |
| `min(a, b)` / `max(a, b)` | Extremes | Combining masks (union/intersection) |
| `pow(x, y)` / `exp(x)` / `log(x)` / `sqrt(x)` | Power family | Easing curves (§12.3), gamma-ish adjustments |

**Trigonometry and geometry:**

| Function | Returns | Typical use |
|---|---|---|
| `sin(x)` / `cos(x)` | Oscillation in -1..1 | All periodic animation; remap with `* 0.5 + 0.5` |
| `atan(y, x)` | Angle of vector (two-argument form) | Radial effects (§15.3) |
| `length(v)` / `distance(a, b)` | Magnitude / separation | Circular masks, vignettes, SDF-style shapes |
| `normalize(v)` | Unit vector | Directions for lighting (§7.4) |
| `dot(a, b)` | Scalar product | Luminance weights, Lambert lighting, squared distance |

**Texture access:**

| Function | Returns | Typical use |
|---|---|---|
| `texture(s, uv)` | Filtered sample | The default read |
| `textureLod(s, uv, lod)` | Sample at explicit mip level | Screen texture (§11.1), controlled blur |
| `texelFetch(s, ivec2, lod)` | Exact texel by integer coordinate, unfiltered | Pixel-perfect LUT/atlas reads without filtering risk |
| `textureSize(s, lod)` | `ivec2` dimensions | Resolution-adaptive math (§13.5) |

**Derivatives** (fragment stage only): `dFdx(x)`, `dFdy(x)`, `fwidth(x)` (= `abs(dFdx) + abs(dFdy)`) report how a value changes between neighboring screen pixels — the basis of resolution-independent antialiasing (`smoothstep(edge - fwidth(x), edge + fwidth(x), x)`). Two cautions: derivatives are approximated per 2×2 pixel quad, so they misbehave inside divergent branches, and on pixel art you frequently *want* aliasing (§19) — reach for `fwidth` in smooth-art or UI contexts, not on the sprite grid.

> ✅ **Best practice** — Learn to read `mix`/`step`/`smoothstep` chains as sentences: `mix(base, effect, step(0.5, mask))` = "effect where mask passes, base elsewhere." The cookbook's recipes are long sentences in exactly this grammar; once the grammar is automatic, unfamiliar shaders from godotshaders.com become skimmable.

## 5. Functions, includes and the preprocessor

### 5.1 User functions

Functions are declared before use (there is no forward declaration and no overloading of your own functions across files) and use value semantics with GLSL qualifiers for outputs:

```glsl
// in (default): copied in. out: copied out. inout: both.
void rotate_uv(inout vec2 uv, vec2 pivot, float angle) {
    float s = sin(angle);
    float c = cos(angle);
    uv -= pivot;
    uv = vec2(uv.x * c - uv.y * s, uv.x * s + uv.y * c);
    uv += pivot;
}

float vignette(vec2 uv, float softness) {
    vec2 centered = uv * 2.0 - 1.0;
    return 1.0 - smoothstep(1.0 - softness, 1.4, length(centered));
}
```

The compiler aggressively inlines; do not hesitate to factor readable helpers. What you *cannot* do: recursion, sampler parameters on some backends prior to 4.x normalization (in Godot 4.x passing a `sampler2D` as a function parameter is supported and common), and defining functions named after built-ins.

### 5.2 Shader includes: .gdshaderinc

Once two shaders share a helper — Relax Room's `luminance()`, palette utilities, dither matrix — copy-paste becomes a maintenance bug factory. GDShader's answer is the **shader include file**, extension `.gdshaderinc`, pulled in with `#include`:

```glsl
// res://shaders/common/color_utils.gdshaderinc
// NOTE: no shader_type here — include files are fragments of code.

float luminance(vec3 rgb) {
    return dot(rgb, vec3(0.2126, 0.7152, 0.0722));
}

vec3 to_grayscale(vec3 rgb) {
    return vec3(luminance(rgb));
}
```

```glsl
// res://shaders/fx/sepia.gdshader
shader_type canvas_item;

#include "res://shaders/common/color_utils.gdshaderinc"

void fragment() {
    vec4 base = texture(TEXTURE, UV);
    COLOR = vec4(to_grayscale(base.rgb) * vec3(1.1, 0.95, 0.75), base.a);
}
```

Rules verified against the 4.x preprocessor reference:

- Only `.gdshaderinc` files can be included — you cannot `#include` a `.gdshader`.
- Includes may nest, to a **maximum depth of 25**; **cyclic includes are a compile error**.
- Paths can be absolute (`res://…`) anywhere; relative paths work when including from another shader file.
- An include file may contain anything a shader may contain *except* `shader_type` — uniforms, varyings, functions, other includes. Uniforms declared in an include appear in every material using a shader that includes it.
- Guard against double inclusion the C way, since there is no `#pragma once`:

```glsl
#ifndef COLOR_UTILS_INC
#define COLOR_UTILS_INC
// ...contents...
#endif
```

What a mature include library buys you is *composability*. With effect bodies factored as functions, a new combined effect is a few lines of glue:

```glsl
// res://shaders/common/fx_lib.gdshaderinc
#ifndef FX_LIB_INC
#define FX_LIB_INC

vec3 apply_flash(vec3 rgb, vec3 flash_rgb, float amount) {
    return mix(rgb, flash_rgb, amount);
}

float outline_mask(sampler2D tex, vec2 uv, vec2 texel, float thickness, float self_a) {
    float n = texture(tex, uv + vec2(0.0, -texel.y * thickness)).a
            + texture(tex, uv + vec2(0.0,  texel.y * thickness)).a
            + texture(tex, uv + vec2(-texel.x * thickness, 0.0)).a
            + texture(tex, uv + vec2( texel.x * thickness, 0.0)).a;
    return step(0.01, n) * (1.0 - self_a);
}

#endif
```

```glsl
// res://shaders/fx/pet_feedback.gdshader — outline + flash in nine lines of body
shader_type canvas_item;
#include "res://shaders/common/fx_lib.gdshaderinc"

uniform vec4 outline_color : source_color = vec4(1.0);
uniform float thickness : hint_range(0.0, 4.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0);
uniform float flash_amount : hint_range(0.0, 1.0) = 0.0;

void fragment() {
    vec4 base = texture(TEXTURE, UV);
    float outline = outline_mask(TEXTURE, UV, TEXTURE_PIXEL_SIZE, thickness, base.a);
    vec3 rgb = apply_flash(base.rgb, flash_color.rgb, flash_amount);
    vec4 body = vec4(rgb, base.a);
    COLOR = mix(body, outline_color, outline);
}
```

This *is* the pet's production material in the §19.3 case-study stack — two cookbook recipes (§13.1, §13.2) merged through the library, which is also the honest answer to 2D's missing `next_pass` (§10.3): composition happens in code, at authoring time.

### 5.3 The preprocessor

Godot 4 ships a C-like preprocessor supporting `#define` / `#undef`, `#if` / `#elif` / `#else` / `#endif`, `#ifdef` / `#ifndef`, `#error`, `#include`, and `#pragma`. Macros can take arguments and use `##` concatenation:

```glsl
#define DEBUG_CHANNELS            // flag-style define

#define SAMPLE_OFFSET(dx, dy) texture(TEXTURE, UV + vec2(dx, dy) * TEXTURE_PIXEL_SIZE)

#if defined(DEBUG_CHANNELS)
    // compiled only when the flag is defined
#endif
```

Since Godot 4.4 the preprocessor also exposes **renderer detection defines**, which let one shader adapt to the active backend:

```glsl
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
    // OpenGL path — e.g., skip an effect that needs features GL ES 3.0 lacks
#else
    // Forward+ / Mobile (Vulkan, D3D12, Metal)
#endif
```

(`RENDERER_COMPATIBILITY` is 0, `RENDERER_MOBILE` is 1, `RENDERER_FORWARD_PLUS` is 2.)

> ⚠️ **Pitfall** — Preprocessor lines never end with a semicolon, and a `#define` *with* a trailing semicolon silently bakes that semicolon into every expansion — producing baffling errors at the usage site, not the definition. When a compile error points at a line that looks innocent, expand any macros on it by eye first.

> ✅ **Best practice** — Keep a project-wide `res://shaders/common/` directory with three include files: `color_utils.gdshaderinc` (luminance, grayscale, hue shift), `pixel_utils.gdshaderinc` (pixel-snapping helpers, §19), and `dither.gdshaderinc` (the Bayer matrix, §14). Every recipe in this module that repeats a helper is a candidate for extraction there.

## 6. shader_type and render_mode

### 6.1 The five shader types

The mandatory first statement of every shader selects the pipeline and therefore the entire vocabulary available to you:

| `shader_type` | Renders | Stages | This course |
|---|---|---|---|
| `canvas_item` | Everything 2D: `Sprite2D`, controls, `TileMapLayer`, `ColorRect`, … | `vertex`, `fragment`, `light` | **Our focus** |
| `spatial` | 3D geometry (`MeshInstance3D`, …) | `vertex`, `fragment`, `light` | Mentioned only |
| `particles` | Computes particle *behavior* for `GPUParticles2D/3D` (not their look) | `start`, `process` | Mentioned only |
| `sky` | Skybox / radiance backgrounds | `sky` | Out of scope |
| `fog` | Volumetric fog volumes (3D) | `fog` | Out of scope |

Note the `particles` subtlety, because it trips up 2D developers: a particles shader replaces the *simulation* (positions, velocities, lifetimes) of a `GPUParticles2D`; the *appearance* of each particle is still drawn by a `canvas_item` material on the particle's texture. You can therefore combine both: a particles shader moving snowflakes, and a canvas_item shader tinting them.

Using a built-in from the wrong pipeline (`SCREEN_UV` in a particles shader, `NORMAL_MAP` in `vertex()`, `LIGHT` in `fragment()`) is a compile error naming the offending identifier — the error is accurate; trust it and check which stage/type you are in.

### 6.2 render_mode for canvas_item

`render_mode` sets fixed-function state that your code alone cannot express. Multiple modes combine with commas: `render_mode blend_add, unshaded;`. The full canvas_item list, verified against the 4.x reference:

| render_mode | Effect |
|---|---|
| `blend_mix` | Standard alpha blending — the default; source over destination weighted by alpha. |
| `blend_add` | Additive: source added to destination. Light, fire, glow sprites. Black contributes nothing. |
| `blend_sub` | Subtractive: source subtracted from destination. Rare; smoke/darkening tricks. |
| `blend_mul` | Multiplicative: tints what is behind. White contributes nothing. Stained glass, shadow overlays. |
| `blend_premul_alpha` | Pre-multiplied alpha blending — expects RGB already multiplied by A. Correct compositing for pre-multiplied art and some render-to-texture flows. |
| `blend_disabled` | No blending; RGBA written as-is, replacing the destination including alpha. |
| `unshaded` | Skip the light pass entirely — `Light2D` nodes do not affect this item. The result is exactly your `fragment()` output. |
| `light_only` | Item is invisible except where `Light2D`s touch it — drawn only in light passes. |
| `skip_vertex_transform` | `VERTEX` arrives untransformed; you must apply `MODEL_MATRIX`/`CANVAS_MATRIX` yourself in `vertex()`. For advanced billboarding/anchoring tricks. |
| `world_vertex_coords` | `VERTEX` in `vertex()` is in world space instead of local space. Lets effects align across differently-positioned nodes (e.g., wind over many grass sprites). |

Blend modes interact with effects in ways worth internalizing through one example: a "ghost pet" in Relax Room. With `blend_mix` and `COLOR.a = 0.5` you get a translucent pet that *darkens* a bright background (normal transparency). With `blend_add` the pet becomes an apparition that only ever brightens, disappearing over white backgrounds — and its own alpha is effectively a brightness dial. Neither is "right"; they are different physical statements.

```glsl
shader_type canvas_item;
render_mode blend_add, unshaded;   // ghostly, ignores Light2D

uniform float presence : hint_range(0.0, 1.0) = 0.6;

void fragment() {
    vec4 base = texture(TEXTURE, UV);
    COLOR = vec4(base.rgb * presence, base.a);   // with blend_add, rgb scale = intensity
}
```

A chooser table for the effects this module builds:

| You are making… | Blend mode |
|---|---|
| Ordinary sprite effects (outline, flash, dissolve, palette) | `blend_mix` (default — omit it) |
| Light cones, fire, sparks, glints, ghosts | `blend_add` |
| Shadow overlays, stained glass, color filters over the scene | `blend_mul` |
| Post-processing rect that fully replaces each pixel | `blend_mix` with `COLOR.a = 1.0` (writes opaque) |
| Render-to-texture compositing with premultiplied sources | `blend_premul_alpha` |

> ⚠️ **Pitfall** — `render_mode` is part of the *shader*, not the material. Two materials sharing one shader share its blend mode. If you need the same effect in `blend_mix` and `blend_add` variants, that is two `.gdshader` files (share the body via an include) — or one shader with the effect parameterized differently.

### 6.3 Light processing and the light() stage

By default, `Light2D` nodes (`PointLight2D`, `DirectionalLight2D`) modulate every non-`unshaded` canvas item using a built-in formula (multiply by light color/energy, respecting shadows). Providing a `light()` function replaces that formula with yours, per pixel, per light. The stage exists so you can implement 2D normal mapping, rim lighting, cel-banding, or custom shadow tinting — its built-ins are tabled in [§7.4](#7-built-in-variables-for-canvas_item), and a worked cel-shading example appears there too. If your scene has no `Light2D` at all (many desktop-companion scenes do not), `light()` never runs and `unshaded` is a free micro-optimization that also documents intent.

Cost accounting for the light stage is multiplicative and deserves a number: a shaded item overlapped by three `PointLight2D`s runs `light()` **three times per pixel** on top of `fragment()` once. For a handful of lamps over a room scene this is nothing; for twenty dynamic lights over full-screen parallax layers it is the dominant cost. The lighting-design side of that trade-off (how many lights, shadow settings, light textures) belongs to [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md); this module's concern is only that you know the multiplier exists and that `unshaded` exempts an item from it entirely.

## 7. Built-in variables for canvas_item

Built-ins are the pre-wired inputs and outputs of each stage. The tables below are verified against the official *CanvasItem shaders* reference for Godot 4.x. "in" means read-only; "inout" means readable and writable (writing is how you affect the pipeline); "out" means write-only in practice.

### 7.1 Global built-ins (available in every stage)

| Name | Type | Access | Meaning |
|---|---|---|---|
| `TIME` | float | in | Seconds since the engine started. Rolls over per the `rendering/limits/time/time_rollover_secs` project setting (default 3600). **Not affected by pausing or `Engine.time_scale`** — see §12. |
| `PI` | float | in | 3.141592…. |
| `TAU` | float | in | 6.283185… (= 2·PI). Full circle in radians — prefer `TAU` for rotations. |
| `E` | float | in | 2.718281…. |

### 7.2 vertex() built-ins

Runs once per vertex — four times for a standard `Sprite2D` quad, more for `Polygon2D`, meshes, or tile geometry.

| Name | Type | Access | Meaning |
|---|---|---|---|
| `VERTEX` | vec2 | inout | Vertex position in **local** space (pixels). Write it to move geometry. With `world_vertex_coords`, it is in world space instead. |
| `UV` | vec2 | inout | Normalized texture coordinate for this vertex (0-1). Writable — offsetting here scrolls the texture. |
| `COLOR` | vec4 | inout | Vertex color: the node's modulate/self-modulate product. Writable; interpolates into `fragment()`'s incoming `COLOR`. |
| `MODEL_MATRIX` | mat4 | in | Local → world transform of the canvas item. |
| `CANVAS_MATRIX` | mat4 | in | World → canvas transform (camera & canvas layers). |
| `SCREEN_MATRIX` | mat4 | in | Canvas → clip-space transform. |
| `TEXTURE_PIXEL_SIZE` | vec2 | in | `1.0 / texture_size` — the UV size of one texel of the node's texture. |
| `INSTANCE_ID` | int | in | Index when instanced (e.g., particles / multimesh). |
| `INSTANCE_CUSTOM` | vec4 | in | Per-instance custom data (set by particles or `MultiMesh`). |
| `VERTEX_ID` | int | in | Index of the current vertex in the buffer (0-3 on a quad). |
| `AT_LIGHT_PASS` | bool | in | Always `false` in 4.x (kept for 3.x porting). |
| `POINT_SIZE` | float | inout | Size when drawing point primitives. |
| `CUSTOM0`, `CUSTOM1` | vec4 | in | Custom vertex data supplied by the drawing primitive. |

A note on the matrices: for everyday 2D effects you never touch them — Godot transforms `VERTEX` for you after `vertex()` returns. They exist for `skip_vertex_transform` workflows and for converting between spaces (e.g., computing a world-space position to feed a varying, as the wind example in §15 does).

A worked `vertex()` example — procedural squash-and-stretch, the animation principle that makes the Relax Room pet feel rubbery when it lands, done without touching the sprite's `scale` property (so physics and child positioning stay unaffected):

```glsl
shader_type canvas_item;

uniform float squash : hint_range(-0.5, 0.5) = 0.0;  // + = squash, - = stretch

void vertex() {
    // Scale y down and x up (or vice versa), preserving area, anchored at the feet.
    float sy = 1.0 - squash;
    float sx = 1.0 / sy;                 // area preservation: sx * sy = 1
    // Assume sprite origin at center; feet at +half height in local space.
    float half_h = 0.5 / TEXTURE_PIXEL_SIZE.y;
    VERTEX.x *= sx;
    VERTEX.y = (VERTEX.y - half_h) * sy + half_h;
}
```

Line by line: `sy`/`sx` are reciprocal scales so the sprite's *area* stays constant — the classical animation rule that sells squash as weight rather than shrinkage; `half_h` recovers the sprite's half-height in pixels from `TEXTURE_PIXEL_SIZE` (1 / texel size = texture size); the `y` line re-anchors the scaling at the sprite's bottom edge so the feet stay planted while the body compresses. Drive `squash` from a landing signal with a spring-like tween (overshoot then settle) and four vertices do the work of a whole squash animation strip.

> ⚠️ **Pitfall** — Vertex displacement does not move the node's *bounds* as physics or `Control` layout see them; a heavily displaced sprite can visually exit its clickable `Area2D`. Keep vertex motion cosmetic and small, or size interaction shapes for the extremes.

### 7.3 fragment() built-ins

Runs once per covered pixel. This is where 90% of your code in this module lives.

| Name | Type | Access | Meaning |
|---|---|---|---|
| `COLOR` | vec4 | inout | **The output.** Comes in as vertex `COLOR` × sampled `TEXTURE` at `UV`; whatever it holds when `fragment()` ends is blended to screen. |
| `UV` | vec2 | in | Interpolated texture coordinate from `vertex()`. Read-only here. |
| `TEXTURE` | sampler2D | in | The node's own texture (sprite frame, tile atlas, font page…). |
| `TEXTURE_PIXEL_SIZE` | vec2 | in | UV size of one texel of `TEXTURE` — the key to neighbor sampling (outline, blur). |
| `FRAGCOORD` | vec4 | in | Pixel center coordinate in screen space (`.xy` = pixels from top-left). Drives screen-space patterns like dithering. |
| `SCREEN_UV` | vec2 | in | This pixel's position as 0-1 UV over the whole screen — pairs with `hint_screen_texture` (§11). |
| `SCREEN_PIXEL_SIZE` | vec2 | in | `1.0 / screen_size_in_pixels`. |
| `POINT_COORD` | vec2 | in | 0-1 UV when drawing point primitives. |
| `REGION_RECT` | vec4 | in | Sprite region in the texture as (x, y, width, height) — useful with atlas regions. |
| `VERTEX` | vec2 | inout | Interpolated pixel position (screen space). |
| `LIGHT_VERTEX` | vec3 | inout | Position used by lighting; write `.z` to fake height for 2D lights. |
| `SHADOW_VERTEX` | vec2 | inout | Write to offset where this pixel casts/receives 2D shadows. |
| `NORMAL` | vec3 | inout | Normal read from `NORMAL_TEXTURE`; writable for procedural normals. |
| `NORMAL_TEXTURE` | sampler2D | in | The node's normal map, if assigned (`CanvasTexture`). |
| `NORMAL_MAP` | vec3 | out | Write a tangent-space normal map sample (RGB 0-1) here instead of `NORMAL` when using standard normal-map textures. |
| `NORMAL_MAP_DEPTH` | float | out | Strength multiplier for `NORMAL_MAP`. |
| `SPECULAR_SHININESS` | vec4 | in | Specular color/shininess from the `CanvasTexture`. |
| `SPECULAR_SHININESS_TEXTURE` | sampler2D | in | The specular map sampler. |
| `AT_LIGHT_PASS` | bool | in | Always `false` in 4.x. |

The incoming value of `COLOR` deserves emphasis because it encodes Godot's default behavior. When you write a `fragment()` that starts with `COLOR = texture(TEXTURE, UV);` you have *discarded* the node's modulate tint (which arrived pre-multiplied into `COLOR`). Often that is exactly the bug behind "my sprite ignores modulate since I added a shader."

```glsl
void fragment() {
    // Respects modulate — starts from the default pipeline's value:
    vec4 base = COLOR;                       // already texture × modulate

    // Ignores modulate — resamples raw:
    vec4 raw = texture(TEXTURE, UV);

    COLOR = base;                            // choose deliberately
}
```

> ✅ **Best practice** — Decide per effect whether modulate should compose with it, and write the first line of `fragment()` accordingly. Recipes in this module sample `texture(TEXTURE, UV)` when they need the *unmodified art* (palette swap must see true colors) and start from `COLOR` when they post-process *whatever the pipeline produced*.

### 7.4 light() built-ins

Runs once per pixel **per Light2D** affecting the item (skipped entirely under `render_mode unshaded`).

| Name | Type | Access | Meaning |
|---|---|---|---|
| `LIGHT` | vec4 | inout | **The output** — this light's contribution for this pixel. |
| `COLOR` | vec4 | in | The pixel's color as produced by `fragment()`. |
| `LIGHT_COLOR` | vec4 | in | The `Light2D`'s color (already including its texture). |
| `LIGHT_ENERGY` | float | in | The light's energy multiplier. |
| `LIGHT_POSITION` | vec3 | in | Light position in screen space (0 for directional lights). |
| `LIGHT_DIRECTION` | vec3 | in | Direction of the light in screen space. |
| `LIGHT_IS_DIRECTIONAL` | bool | in | `true` during a `DirectionalLight2D` pass. |
| `LIGHT_VERTEX` | vec3 | in | Pixel position as (possibly) modified in `fragment()`. |
| `NORMAL` | vec3 | in | Pixel normal (flat `(0,0,1)` unless a normal map / `NORMAL` write exists). |
| `SHADOW_MODULATE` | vec4 | out | Tint multiplier applied where this pixel is shadowed. |
| `SCREEN_UV`, `UV`, `POINT_COORD`, `FRAGCOORD` | vec2/vec4 | in | As in `fragment()`. |
| `TEXTURE`, `TEXTURE_PIXEL_SIZE` | — | in | As in `fragment()`. |
| `SPECULAR_SHININESS` | vec4 | in | As in `fragment()`. |

A compact, practical example — banded (cel) 2D lighting, which reads beautifully on pixel art because it quantizes light into flat zones instead of smooth (and grid-breaking) gradients:

```glsl
shader_type canvas_item;

uniform int bands : hint_range(2, 8) = 3;

void light() {
    // Default-ish diffuse term from the light direction and surface normal:
    float diffuse = max(dot(normalize(-LIGHT_DIRECTION), NORMAL), 0.0);
    // Quantize into N flat bands:
    float banded = floor(diffuse * float(bands)) / float(bands - 1);
    LIGHT = vec4(COLOR.rgb * LIGHT_COLOR.rgb * LIGHT_ENERGY * banded, COLOR.a);
}
```

Line by line: the dot product of the (negated, normalized) light direction against the pixel normal is the textbook Lambert term; `floor(x * N) / (N-1)` snaps the continuous 0-1 term to N discrete levels; the final `LIGHT` multiplies the fragment's color by light color, energy, and the banded term. Add a `PointLight2D` with a soft texture over the Relax Room scene and furniture visibly "steps" into light as the lamp approaches — a very Game-Boy-adjacent look.

## 8. Uniforms deep dive

### 8.1 What a uniform is

A **uniform** is a shader-scope variable whose value is constant across a draw call but settable from outside — the Inspector, GDScript, or the animation system. Uniforms are the *only* front door into a running shader. Declaring one does three things at once: reserves a GPU-visible parameter slot, exposes an Inspector widget on every `ShaderMaterial` using the shader, and registers a name for `set_shader_parameter`.

```glsl
uniform vec4 flash_color : source_color = vec4(1.0);
uniform float flash_amount : hint_range(0.0, 1.0) = 0.0;
uniform sampler2D noise_tex : filter_nearest, repeat_enable;
```

The general form is `uniform <type> <name> [: hint[, hint…]] [= default];` — hints before the default, multiple hints comma-separated. Uniform names use snake_case by convention, matching what GDScript will type.

### 8.2 The hint catalog

Hints tell the editor how to present a uniform and tell the renderer how to treat texture data. The ones that matter in 2D, verified against the shading-language reference:

| Applies to | Hint | Effect |
|---|---|---|
| `vec3`, `vec4` | `source_color` | Inspector shows a color picker; value treated as color (sRGB→linear conversion handled correctly for the current renderer). **Always use for colors.** |
| `float`, `int` | `hint_range(min, max [, step])` | Inspector slider; also documents valid range. |
| `int` | `hint_enum("A", "B", "C")` | Inspector dropdown; value is the index. Great for mode switches (grayscale/sepia/off). |
| `sampler2D` | `source_color` | Texture contains color data (needs sRGB handling) — use for palettes/LUTs. |
| `sampler2D` | `hint_default_white` / `hint_default_black` / `hint_default_transparent` | Fallback content when no texture is assigned — pick so the effect degrades gracefully. |
| `sampler2D` | `hint_normal` | Texture is a normal map. |
| `sampler2D` | `filter_nearest`, `filter_linear`, `filter_nearest_mipmap`, `filter_linear_mipmap`, `filter_nearest_mipmap_anisotropic`, `filter_linear_mipmap_anisotropic` | Per-uniform sampling filter — overrides project/node defaults for this sampler. Pixel-art LUTs and noise want `filter_nearest`. |
| `sampler2D` | `repeat_enable`, `repeat_disable` | Whether UVs outside 0-1 wrap. Scrolling noise wants `repeat_enable`. |
| `sampler2D` | `hint_screen_texture` | The sampler *is the screen* — §11. |
| `sampler2D` | `hint_depth_texture`, `hint_normal_roughness_texture` | Depth / normal-roughness buffers — **spatial shaders only** (Forward+/Mobile); not available to canvas_item. The screen texture is the only screen buffer 2D can read. |

> ⚠️ **Pitfall** — Forgetting `source_color` on a color uniform produces washed-out or too-dark colors depending on renderer, because the raw vec4 skips color-space conversion. The shader compiles, the Inspector even shows a 4-float editor — the only symptom is "the color looks wrong," which makes it a classic hard-to-spot bug. Color uniform ⇒ `source_color`, every time.

### 8.3 Setting uniforms from GDScript

The bridge is `ShaderMaterial.set_shader_parameter(name, value)` (and its read twin `get_shader_parameter`). Types map naturally: `float`→float, `Color`→vec4 (use with `source_color`), `Vector2`→vec2, `Vector3`/`Color`→vec3/vec4, `Transform2D`→mat (rarely needed), `Texture2D`→sampler2D, typed arrays→uniform arrays.

```gdscript
# pet.gd — driving the hit-flash recipe (§13.2)
@onready var _mat: ShaderMaterial = $Sprite2D.material

func flash() -> void:
    _mat.set_shader_parameter("flash_amount", 1.0)
    var tw := create_tween()
    tw.tween_property(_mat, "shader_parameter/flash_amount", 0.0, 0.25)
```

Two details in that snippet repay attention. First, uniforms are addressable as *properties* under the `shader_parameter/` prefix, which means **tweens and AnimationPlayer tracks can animate them directly** — that one line replaces a hand-written interpolation loop. Second, the material is fetched once in `@onready`; `set_shader_parameter` is cheap, but a per-frame string lookup of `$Sprite2D.material` in `_process` is the kind of avoidable cost [Desktop Companion Performance](DESKTOP_COMPANION_PERFORMANCE.md) audits for.

Reading goes the other way when you need the current value (e.g., saving effect settings with the systems from [Database and Persistence](DATABASE_AND_PERSISTENCE.md)):

```gdscript
var current: float = _mat.get_shader_parameter("flash_amount")
```

For tooling (an in-game effects panel, a debug console), a shader's uniforms are introspectable — the basis of "settings UI generated from the shader itself":

```gdscript
for u in _mat.shader.get_shader_uniform_list():
    print("%s : %s (hint %d)" % [u.name, type_string(u.type), u.hint])
    # e.g. "flash_amount : float (hint 1)"  — hint 1 = PROPERTY_HINT_RANGE
```

Each entry is a property-info dictionary (name, type, hint, hint_string) — the same structure the Inspector consumes, which is *why* hints (§8.2) double as UI metadata.

> ⚠️ **Pitfall** — `set_shader_parameter` with a misspelled name does **not** error — it silently does nothing (the parameter may simply not exist on this shader). When an effect "ignores the script," diff the string against the uniform declaration character by character before debugging anything else.

The full type correspondence, for reference when declaring uniforms you intend to drive from code:

| GDShader uniform | GDScript value to pass | Notes |
|---|---|---|
| `float` | `float` | `int` is auto-converted |
| `int` / `uint` | `int` | With `hint_enum`, pass the index |
| `bool` | `bool` | Shows as a checkbox in the Inspector |
| `vec2` / `ivec2` | `Vector2` / `Vector2i` | |
| `vec3` | `Vector3` (or `Color` — first three channels) | |
| `vec4` + `source_color` | `Color` | The intended pairing for colors |
| `vec4` (no color hint) | `Vector4` / `Quaternion` / `Color` | Prefer `Vector4` for non-colors, self-documenting |
| `mat2/3/4` | `Transform2D` / `Basis` / `Transform3D` or `Projection` | Rare in 2D effects |
| `sampler2D` | any `Texture2D` (`ImageTexture`, `AtlasTexture`, `NoiseTexture2D`, `ViewportTexture`…) | Assigning a `SubViewport`'s texture wires live render-to-texture |
| `uniform T name[N]` | `PackedFloat32Array`, `PackedVector3Array`, `PackedColorArray`, or typed `Array` matching `T` | Length must match `N` (§8.4) |

One integration worth flagging from that table: passing a **`ViewportTexture`** into an ordinary `sampler2D` uniform means a shader can consume the live output of any `SubViewport` — minimap-style composites, trail buffers, or the "remember state across frames" workaround from §2.3. The viewport side of that wiring is covered in [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md).

### 8.4 Uniform arrays

Uniform arrays hold fixed-size lists — palettes, kernel weights, positions:

```glsl
uniform vec3 palette[4];
uniform float kernel[9];
```

Uniform arrays cannot declare per-element defaults in the shader; feed them from GDScript with a matching typed array:

```gdscript
_mat.set_shader_parameter("palette", PackedVector3Array([
    Vector3(0.06, 0.22, 0.06),
    Vector3(0.19, 0.38, 0.19),
    Vector3(0.55, 0.67, 0.06),
    Vector3(0.61, 0.74, 0.06),
]))
```

(That particular palette is the classic DMG Game Boy green ramp — it returns in the palette-swap recipe, §13.5.) Iterate with `.length()` and prefer constant loop bounds when you can; a dynamic index into a uniform array is fine, but a *divergent* dynamic index is the slow variant per §2.2.

### 8.5 Instance uniforms: per-node values without material copies

The shared-material dilemma: give every furniture sprite in Relax Room the same `ShaderMaterial` and setting `flash_amount` on one flashes *all* of them (materials are shared resources — §10.2). Duplicate the material per node and you multiply resources and break batching. **Instance uniforms** solve this precisely: the shader is shared, the material is shared, but each node carries its own value.

```glsl
shader_type canvas_item;

instance uniform float flash_amount : hint_range(0.0, 1.0) = 0.0;
instance uniform vec4 tint : source_color = vec4(1.0);

void fragment() {
    vec4 base = texture(TEXTURE, UV) * tint;
    COLOR = vec4(mix(base.rgb, vec3(1.0), flash_amount), base.a);
}
```

```gdscript
# Per node — no material duplication anywhere:
$Chair.set_instance_shader_parameter("flash_amount", 1.0)
$Lamp.set_instance_shader_parameter("tint", Color(1.0, 0.9, 0.7))
```

Facts to pin down, verified against the 4.x documentation and release notes:

- Instance uniforms for **`canvas_item` shaders arrived in Godot 4.4** (they were `spatial`-only from 4.0-4.3). On our pinned 4.5 they are fully available in 2D — and they work **without breaking 2D batching**, which is what makes them the performant choice for per-node variation.
- Set them with `CanvasItem.set_instance_shader_parameter()` (also visible in the Inspector under *Instance Shader Parameters*), not `set_shader_parameter`.
- Limits: **at most 16 instance uniforms per shader**, and they cannot be samplers or arrays.
- When two shaders on nested items both declare instance uniforms, `instance_index(N)` can partition the 16 slots explicitly: `instance uniform vec4 c : instance_index(5);`.

> ✅ **Best practice** — Default to this decision ladder for "same effect, different values per node": instance uniform (shared everything, 4.4+) → `material.duplicate()` at runtime for one-off cases (§10.3) → `resource_local_to_scene` for scene-instanced variants. Reach for later rungs only when the earlier ones cannot express the need (e.g., a per-node *texture* cannot be an instance uniform).

### 8.6 Global shader uniforms: project-wide values

Some values are facts about the *world*, not any node: time of day, weather intensity, screen-shake amount, an accessibility "reduce flashing" flag. Declaring them as regular uniforms would mean setting the same value on dozens of materials. **Global shader uniforms** are declared once per project and readable by any shader:

1. Define the name and type in **Project Settings → Globals → Shader Globals** (e.g., `day_phase`, type `float`, default `0.0`). This creates the registry entry; a global used in a shader must exist here.
2. Reference it in any shader with the `global` qualifier — note: *no* hints, *no* per-shader default; the project owns those:

```glsl
shader_type canvas_item;

global uniform float day_phase;   // 0 = midnight … 0.5 = noon … 1 = midnight

uniform vec4 night_tint : source_color = vec4(0.4, 0.45, 0.8, 1.0);

void fragment() {
    vec4 base = COLOR;
    float night = 1.0 - smoothstep(0.20, 0.35, abs(day_phase - 0.5) * -1.0 + 0.5);
    // (see §14.5 for the cleaner curve version of this)
    COLOR = vec4(mix(base.rgb, base.rgb * night_tint.rgb, night), base.a);
}
```

3. Set it at runtime through the `RenderingServer` (typically from an autoload — see [Autoload Safety](AUTOLOAD_SAFETY.md) for the singleton pattern rules):

```gdscript
# day_night_clock.gd (autoload)
func _process(_delta: float) -> void:
    var now := Time.get_time_dict_from_system()
    var phase := float(now.hour * 3600 + now.minute * 60 + now.second) / 86400.0
    RenderingServer.global_shader_parameter_set("day_phase", phase)
```

`RenderingServer.global_shader_parameter_set()` updates the value; `global_shader_parameter_add()` / `global_shader_parameter_remove()` can even manage the registry from code (with `RenderingServer.GLOBAL_VAR_TYPE_*` constants) for plugin-style setups, and `global_shader_parameter_get()` reads it back — but note that reading is intended for tooling/debugging, not hot paths.

> ⚠️ **Pitfall** — A `global uniform` whose name is missing from Project Settings fails at shader compile time ("global uniform … not found"); a *typo* in the `global_shader_parameter_set` call fails silently like any parameter miss. Keep global names in one GDScript constants file (`const GLOBAL_DAY_PHASE := &"day_phase"`) and use it at every call site so both sides can only be wrong together.

> ✅ **Best practice** — Globals are read-only from the shader's perspective and shared by everything; treat them like environment state, not per-effect knobs. Relax Room ships exactly three: `day_phase` (float), `ambient_tint` (color), `reduce_motion` (float 0/1, an accessibility toggle honored by the CRT and wave recipes).

## 9. Varyings and interpolation

A **varying** carries data forward through the pipeline: written in `vertex()`, read in `fragment()` and/or `light()`. Between the four vertices of a quad and the thousands of pixels inside it, the rasterizer *interpolates* the value — each fragment receives the perspective-correct blend of the vertex values, exactly as `UV` and `COLOR` already do (they are, in effect, built-in varyings).

```glsl
shader_type canvas_item;

varying vec2 world_pos;          // declared at file scope
varying flat int quadrant;       // 'flat' = no interpolation

void vertex() {
    world_pos = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
    quadrant = VERTEX.x > 0.0 ? 1 : 0;
}

void fragment() {
    // world_pos here is this PIXEL's world position — smoothly interpolated.
    float stripe = step(0.5, fract(world_pos.y / 16.0));
    COLOR = vec4(vec3(stripe), 1.0) * COLOR;
}
```

Interpolation qualifiers:

- `smooth` (default) — perspective-correct interpolation. What you want almost always.
- `flat` — no interpolation; every fragment receives the value from the *provoking vertex*. **Required for integer varyings** (integers cannot be interpolated) and useful when a value must be uniform across the primitive.

Why varyings matter for performance: anything that varies *linearly* across the surface can be computed 4 times instead of 100,000 times. World position, gradient ramps, precomputed rotation sines — compute in `vertex()`, ship via varying. The catch is the linearity: interpolating a *nonlinear* function of position (e.g., `sin(world_pos.x)`) gives a different (wrong) result than computing it per-pixel, because the interpolation happens on the *result*, not the input. Interpolate inputs, compute nonlinear math in the fragment.

A second worked example that shows the optimization pattern cleanly — the §4.6 UV rotation moved to the vertex stage. The rotation *matrix* is uniform across the sprite (it depends only on `TIME`), so building it per-pixel wastes two transcendentals per fragment; but the rotated *coordinate* is linear in UV, so it interpolates correctly:

```glsl
shader_type canvas_item;

uniform float spin_speed : hint_range(-4.0, 4.0) = 1.0;

varying vec2 rotated_uv;

void vertex() {
    float a = TIME * spin_speed;
    float s = sin(a);
    float c = cos(a);
    rotated_uv = mat2(vec2(c, s), vec2(-s, c)) * (UV - 0.5) + 0.5;
}

void fragment() {
    COLOR = texture(TEXTURE, rotated_uv);   // zero trig per pixel
}
```

Four `sin`/`cos` evaluations per frame instead of one pair per pixel — and the result is *identical*, because rotation is a linear map. This "hoist uniform-per-primitive math to `vertex()`, interpolate the linear result" move is the single most broadly applicable shader optimization; apply it whenever `fragment()` computes something whose only per-pixel input enters linearly.

> ⚠️ **Pitfall** — A varying assigned in `fragment()` is a compile error in Godot 4.x when it was also written in `vertex()` (stage misuse); a varying *never written at all* reads as zero. If an effect mysteriously outputs black where a varying is involved, confirm the `vertex()` function actually exists and assigns it — a typo'd function name (`void vertx()`) compiles happily as dead code and leaves the varying unwritten.

## 10. ShaderMaterial workflow

### 10.1 Shader vs material: two resources, two jobs

Godot separates the *program* from its *parameter values*:

- **`Shader`** — the `.gdshader` file: code, uniform declarations, render modes. One per effect.
- **`ShaderMaterial`** — a resource that references a `Shader` and stores current values for its uniforms. Potentially many per shader.

Every `CanvasItem` has a `material` slot. The workflow in the editor: select the node → Inspector → *Material* → *New ShaderMaterial* → click the material → *Shader* → *New Shader* (or load a `.gdshader`). Once assigned, the material's Inspector grows a **Shader Parameters** section with one widget per hinted uniform — this is your effect's control panel, live-updating the viewport as you drag.

The same separation in code:

```gdscript
var shader := load("res://shaders/fx/outline.gdshader") as Shader
var mat := ShaderMaterial.new()
mat.shader = shader
mat.set_shader_parameter("outline_color", Color.CYAN)
$Sprite2D.material = mat
```

### 10.2 The shared-material gotcha

Materials are **resources**, and resources in Godot are shared by reference. Assign one `ShaderMaterial` to ten sprites (or instance a scene whose sprite carries a material) and there is exactly *one* set of uniform values in memory. `set_shader_parameter` on "one node's" material changes all ten — the number-one shader surprise in production, and the 2D sibling of the `SPRITES_AND_TEXTURES.md` shared-resource discussion.

This is a feature until it isn't: shared materials are what make batching effective, and for uniform-less effects (grayscale everything) sharing is exactly right. When you need divergence, choose deliberately:

| Need | Tool | Cost |
|---|---|---|
| Same effect, per-node scalar/vector values | **Instance uniforms** (§8.5, 4.4+) | Zero duplication, batching preserved — the default answer |
| One node needs an independent copy right now | `node.material = node.material.duplicate()` | One material copy; do it once, not per frame |
| Every instanced copy of a scene should get its own material automatically | Check **`resource_local_to_scene`** on the material | One copy per scene instance, made at instantiation |
| Per-node *texture* input (instance uniforms can't) | Duplicate material, or restructure (atlas + per-node UV offset uniform) | Case by case |

```gdscript
# One-off duplication — e.g., the pet gets a unique material at spawn:
func _ready() -> void:
    $Sprite2D.material = $Sprite2D.material.duplicate()
    # From here on, set_shader_parameter affects only this node.
```

> ⚠️ **Pitfall** — `duplicate()` on a material does **not** duplicate the `Shader` it points to (nor should it — code is safely shareable). But editing the *shader text* in the editor edits it for every material referencing that `.gdshader` file. Duplicated material ≠ private shader; it is only private *values*.

### 10.3 Group effects: CanvasGroup, and why next_pass is not a 2D tool

Two workflow questions come up as soon as effects meet scene structure:

**"Can I stack two shaders on one sprite?"** In 3D, `Material.next_pass` chains materials. In 2D, `next_pass` has no effect — the canvas renderer ignores it. Your options: merge the two effects into one shader (usually best — an include file per effect makes composition clean), or route through a container that re-renders its result (`SubViewport`, or a `BackBufferCopy` + screen-reading second node, §11).

**"Can I apply one shader to a whole group of nodes?"** Yes — `CanvasGroup`. It renders its children into an intermediate buffer, then draws that buffer as a single item, applying *its* material to the combined result. An outline around "the pet plus its held item plus its hat" — as one silhouette rather than three overlapping outlines — is the canonical use:

```
CanvasGroup            ← material: outline shader (applies to merged result)
 ├─ Sprite2D (pet)
 ├─ Sprite2D (item)
 └─ Sprite2D (hat)
```

Inside a `CanvasGroup`'s material, `TEXTURE` is the composited children. Mind the cost: the group is an extra render target and an extra full blit — trivial for one pet, meaningful if you nest dozens.

For applying a shader to *everything* (the whole game view), the tools are the full-screen `ColorRect` pattern (§11.3) or a `SubViewport` containing the world with a shader on the displaying `TextureRect`/`SubViewportContainer` — [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) covers the viewport plumbing side.

### 10.4 Materials in the animation system

Because uniforms are properties (`material:shader_parameter/name`), the whole animation stack applies: `AnimationPlayer` tracks can key uniform values (a dissolve keyed alongside a sound effect), tweens can ease them, and `AnimationTree` blends can drive them indirectly. One structural warning: an `AnimationPlayer` track path baked to `Sprite2D:material:shader_parameter/flash_amount` pins the material *resource* — if you later swap to `duplicate()`-per-node at runtime, verify tracks still resolve to the node's current material (they do — the path resolves through the property, not the resource identity — but only if the new material's shader still has that uniform).

### 10.5 Applying a shader to a viewport's output

The remaining workflow pattern: render a subtree into a **`SubViewport`**, then shade its *result* as a single texture. This differs from both `CanvasGroup` (which re-composites within the same rendering pass structure) and the screen-reading rect (which reads the back-buffer): a `SubViewport` is a fully independent render target with its own resolution, its own clear color, and a `ViewportTexture` you can display anywhere.

```
Main scene
 ├─ SubViewport               size = (426, 240)  ← design resolution
 │   └─ (entire game world)
 └─ TextureRect               texture = ViewportTexture of the SubViewport
                              material: any canvas_item shader
                              stretch across window (integer scale)
```

Why this structure earns its complexity for a pixel-art app:

- The world renders at **design resolution**; every full-screen effect on the `TextureRect` shades 426×240 ≈ 102 k fragments instead of 2 M+ at 1080p — a 20× fill-rate discount on the whole §19.3 post stack (only pixel-anchored passes like dithering still belong at native resolution, §14.3).
- The shader on the `TextureRect` sees the world as its plain `TEXTURE` — no screen-reading hint, no back-buffer copies, no draw-order constraints. `UV` spans the whole world image, which makes transition effects (§14.1 pixelate, §13.4-style dissolve on the *entire screen*) trivially applicable to everything at once.
- Upscaling behavior is explicit: nearest-filter the `TextureRect` for crisp integer scaling ([Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) covers the window-size math).

The cost is indirection: the world's coordinate space and the display's are no longer the same (mouse positions must be mapped through the viewport), and `hint_screen_texture` *inside* the SubViewport sees only the SubViewport's own content. Adopt the structure when the resolution discount or the whole-world-as-texture capability pays for that plumbing — for Relax Room's fixed-window companion profile, it does.

## 11. Screen-reading shaders and post-processing

### 11.1 Reading what is already on screen

Sometimes an effect's input is not the node's texture but *the screen itself* — everything drawn before this node: heat-haze, frosted glass, magnifiers, and every full-screen filter. In Godot 3 this was the `SCREEN_TEXTURE` built-in; **in Godot 4 it is a uniform with a hint** — the single most important migration fact in this module:

```glsl
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

void fragment() {
    COLOR = textureLod(screen_texture, SCREEN_UV, 0.0);   // identity: shows the screen
}
```

Mechanics, verified against the *Screen-reading shaders* documentation:

- When the renderer meets the first node using `hint_screen_texture` in a frame, it **copies the entire screen to a back-buffer** just before drawing that node. Later screen-reading nodes in the same frame reuse that copy — efficient, but it means **overlapping screen-reading nodes do not see each other's output**, only the pre-copy screen. Two stacked "distortion" sprites distort the same original background, not each other.
- Sample with `textureLod(screen_texture, SCREEN_UV, 0.0)` — explicit LOD 0. With a mipmap filter hint (`filter_nearest_mipmap`), higher LOD values sample downscaled (blurred) versions of the screen: `textureLod(screen_texture, SCREEN_UV, 2.0)` is a nearly-free two-level blur, the basis of cheap frosted glass.
- The filter and repeat hints ride along the declaration exactly like any sampler uniform: `hint_screen_texture, repeat_disable, filter_nearest` is the standard trio for crisp reads.

### 11.2 BackBufferCopy: taking manual control

The `BackBufferCopy` node makes the copy explicit. Placed in the tree, it copies either a **rect** or the **whole viewport** to the back-buffer at its position in draw order; screen-reading nodes drawn after it read *that* copy, and the automatic full-screen copy is skipped. Two reasons to use it:

1. **Chaining:** put a `BackBufferCopy` *between* two screen-reading nodes and the second one now sees the first one's output — the escape hatch from the "overlapping distorters" limitation above.
2. **Cost control:** if only a small region needs reading (the glass panel of one window in the Relax Room scene), a rect-mode copy is cheaper than a full-screen one.

The chaining structure, concretely — draw order is tree order, top to bottom:

```
Room
 ├─ (background, furniture …)
 ├─ HeatHaze          Sprite2D, screen-reading shader   ← reads copy #1 (auto)
 ├─ BackBufferCopy    copy_mode: Viewport               ← snapshots screen incl. HeatHaze
 └─ GlassPanel        Sprite2D, screen-reading shader   ← reads copy #2: sees the haze
```

Remove the `BackBufferCopy` and `GlassPanel` reads copy #1 too — both effects distort the *original* background and visually ignore each other. Each copy is a full read+write of the covered pixels (§17's cheat sheet), so chain deliberately, not habitually.

> ⚠️ **Pitfall** — Reading `SCREEN_UV` coordinates *outside* the region a rect-mode `BackBufferCopy` copied yields undefined results (usually stale garbage). If a screen-reading effect shows smearing/trails near its edges, the copy rect is smaller than the UV range you sample — grow the rect to cover the effect's maximum offset reach.

### 11.3 The full-screen post-processing recipe

The canonical Godot 4 structure for "apply a shader to the whole frame," straight from the *Custom post-processing* documentation, is a `ColorRect` stretched over the screen on its own `CanvasLayer`:

```
Main scene
 ├─ (world: room, pet, furniture …)
 └─ CanvasLayer            layer = 100  ← draws above everything
     └─ ColorRect          anchors: Full Rect
                            material: ShaderMaterial (screen-reading shader)
                            mouse_filter: Ignore   ← critical for a companion app!
```

Setup checklist: the `CanvasLayer` isolates the rect from camera transforms and guarantees draw order; the `ColorRect` uses the *Full Rect* anchor preset so it always covers the window; **`mouse_filter = Ignore`** so the invisible rect does not eat every click (in an interactive desktop companion this omission "breaks the entire app" — the pet stops responding to the mouse and nothing looks wrong).

The shader on the rect reads the screen and writes a processed version:

```glsl
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;
uniform float strength : hint_range(0.0, 1.0) = 1.0;

void fragment() {
    vec3 scene = textureLod(screen_texture, SCREEN_UV, 0.0).rgb;
    vec3 graded = pow(scene, vec3(1.1)) * vec3(1.02, 1.0, 0.98);  // tiny warm grade
    COLOR = vec4(mix(scene, graded, strength), 1.0);
}
```

For **multi-pass** effects (separable blur being the textbook case), stack `CanvasLayer` + `ColorRect` pairs: each layer's shader reads the screen as produced by the layers below it, because each screen-reading node triggers (or reuses) a copy that includes previous layers' output when they are on *earlier* layers in draw order. The documentation's two-pass Gaussian does horizontal offsets in the first rect's shader and vertical in the second. Godot cannot render to multiple buffers from a canvas shader, and 2D has no depth/normal buffers to read — heavier compositing belongs to `SubViewport` chains or (in 3D) `CompositorEffect`.

> ✅ **Best practice** — Give every post-processing `ColorRect` a `strength`-style uniform and drive it from your settings system, defaulting to subtle. Full-screen filters are the first thing to disable for accessibility ("reduce motion" honoring, §8.6) and for performance triage (§17), so wire the kill switch on day one: `layer_node.visible = false` costs exactly zero when off.

### 11.4 Worked example: rain-on-window distortion

A screen-space effect that earns its keep in Relax Room — a subtle glass distortion band at the top of the room when the weather system says "rain":

```glsl
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear;
uniform sampler2D droplet_noise : repeat_enable, filter_linear, hint_default_black;
uniform float amount : hint_range(0.0, 0.02) = 0.006;
uniform float speed : hint_range(0.0, 2.0) = 0.35;

void fragment() {
    // Scroll the noise downward over time; two octaves for variety.
    vec2 n_uv = SCREEN_UV * vec2(6.0, 3.0) + vec2(0.0, TIME * speed);
    vec2 wobble = texture(droplet_noise, n_uv).rg * 2.0 - 1.0;   // -1..1
    vec2 offset = wobble * amount * COLOR.a;                     // rect alpha = mask
    COLOR = vec4(textureLod(screen_texture, SCREEN_UV + offset, 0.0).rgb, 1.0);
}
```

Line by line: the noise texture (any tileable RGB noise) is scrolled by `TIME`; its red/green channels are remapped from 0-1 to -1..1 to give a signed 2D offset; the offset is scaled by `amount` (note the tiny range — screen-space offsets beyond ~2% read as broken, not wet) and by the rect's own alpha so you can paint the effect's mask with the `ColorRect` color or a gradient; finally the screen is sampled *at the displaced coordinate* — displacement effects always move the *read* position, never "the pixels." This shader lives on a `ColorRect` covering just the window region of the room art, not the whole screen: cheaper, and the effect stays diegetic.

### 11.5 Worked example: magnifier lens

A second screen-reading pattern with different math — a circular lens that magnifies whatever it hovers over. In Relax Room this is the "inspect" cursor mode; the same shader is a scope, a bubble, or a fisheye by parameter choice.

```glsl
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;
uniform float zoom : hint_range(1.0, 4.0) = 2.0;
uniform vec2 radius_uv = vec2(0.10, 0.15);   // node half-size in SCREEN_UV units — set from GDScript
uniform float rim_width : hint_range(0.0, 0.2) = 0.06;
uniform vec4 rim_color : source_color = vec4(0.1, 0.1, 0.15, 1.0);

void fragment() {
    // Position within this node's own quad, centered: -1..1.
    vec2 local = UV * 2.0 - 1.0;
    float r = length(local);

    if (r > 1.0) {
        discard;                              // outside the lens circle: show nothing
    }

    // Magnify: pull the sample toward the lens center; the pull grows with zoom.
    vec2 sample_uv = SCREEN_UV - local * radius_uv * (1.0 - 1.0 / zoom);
    vec3 col = textureLod(screen_texture, sample_uv, 0.0).rgb;

    // Rim: dark ring at the lens edge.
    float rim = smoothstep(1.0 - rim_width, 1.0, r);
    COLOR = vec4(mix(col, rim_color.rgb, rim), 1.0);
}
```

The magnification line is the whole trick: at the lens center (`local` = 0) the sample lands exactly under the pixel; toward the edge, the sample is pulled *back toward the center* by a fraction `(1 - 1/zoom)` of the lens radius — so the lens shows a smaller region of screen stretched over its full circle, which *is* magnification. The subtlety is `radius_uv`: `SCREEN_UV` is normalized against a non-square screen, so the shader needs the node's on-screen half-size *in screen-UV units*, and it cannot derive that by itself in one step. Supply it as a uniform, updated whenever the lens moves or the window resizes:

```gdscript
# lens.gd — attached to the lens Sprite2D/ColorRect
func _process(_delta: float) -> void:
    var vp_size := get_viewport_rect().size
    var radius_uv := (size * 0.5) / vp_size          # Control; for Sprite2D use texture size * scale
    material.set_shader_parameter("radius_uv", radius_uv)
```

The lesson generalizes beyond lenses: **screen-reading effects that must relate their own geometry to screen coordinates need that relation passed in** — the shader alone knows its UVs and the screen's pixel size, but not "how big am I on screen." Passing one small uniform is the honest fix; deriving it from `FRAGCOORD`/`UV` gymnastics in-shader is possible but unreadable.

> ✅ **Best practice** — `discard` outside the circle makes the lens node's *rect* irrelevant to its rendered shape — but input still follows the rect. Pair the visual circle with a matching circular `Area2D`/mouse region when the lens is interactive, echoing the §7.2 bounds warning.

## 12. Shader animation and TIME

### 12.1 TIME semantics — measured, not assumed

`TIME` is the engine-maintained clock: seconds since startup, as a `float`, identical across all shaders in a frame. Facts that production code must respect:

- **It rolls over.** At `rendering/limits/time/time_rollover_secs` (default **3600** seconds) `TIME` snaps back to 0. Any effect computing `sin(TIME * k)` survives rollover gracefully *if* the wave completes whole cycles per rollover period; effects accumulating `TIME` linearly (scrolling UVs) show a one-frame jump each hour. For an app designed to run all day — Relax Room's exact profile — prefer wrapping math (`fract`, `sin`) over unbounded accumulation, or lower the rollover setting and test the seam.
- **It ignores pausing and `Engine.time_scale`.** Pause the `SceneTree` and every `TIME`-driven shader keeps animating. Sometimes that is desirable (menu background stays alive behind a pause dialog); when it is not, the documented remedy is a **custom clock global uniform**:

```gdscript
# game_clock.gd (autoload) — a pausable, scalable shader clock
var shader_time := 0.0

func _process(delta: float) -> void:
    if not get_tree().paused:
        shader_time = fmod(shader_time + delta * Engine.time_scale, 3600.0)
        RenderingServer.global_shader_parameter_set("game_time", shader_time)
```

Shaders that should respect pause read `global uniform float game_time;` instead of `TIME`; shaders that should not (loading spinners, the pause menu's own effects) keep `TIME`. Precision note: keep any time value under a few thousand seconds (hence the `fmod`) — huge floats degrade `sin`/`fract` precision and animations visibly stutter or die, the classic "effect breaks after the app runs overnight" bug.

The facts, as a card:

| Property of `TIME` | Value |
|---|---|
| Unit / type | Seconds, `float` |
| Zero point | Engine start |
| Rollover | `rendering/limits/time/time_rollover_secs`, default 3600 s |
| Affected by `SceneTree.paused` | **No** |
| Affected by `Engine.time_scale` | **No** |
| Same value across all shaders in a frame | Yes |
| Pausable/scalable alternative | Custom global uniform driven from `_process` |

### 12.2 TIME vs GDScript-driven uniforms: the decision rule

Two ways to animate a shader, with a clean division of labor:

| Drive with | When | Example |
|---|---|---|
| `TIME` in-shader | Perpetual, autonomous, uneventful motion — nothing ever needs to sync with gameplay | Water shimmer, candle flicker, scanline drift |
| Uniform + tween/AnimationPlayer | The animation has a *beginning triggered by an event*, an end, easing, or must sync with sound/logic | Hit-flash, dissolve-out on despawn, cooldown wipe |

The `TIME` route costs zero CPU forever; the uniform route costs one property update per frame *only while the tween runs*. The mistake to avoid is polling in `_process` to fake either: a `_process` that sets `wave_phase += delta` every frame forever is strictly worse than `TIME`, and a hand-rolled interpolation loop is strictly worse than `tween_property` on `shader_parameter/x` (§8.3).

Within the "event-driven" column, the sub-choice between Tween and `AnimationPlayer` follows the same logic as everywhere else in Godot — code-shaped vs asset-shaped:

```gdscript
# Tween: constructed in code, parameterizable, perfect for logic-driven effects.
func dissolve_out(duration: float) -> void:
    create_tween().tween_property(_mat, "shader_parameter/progress", 1.0, duration)
```

```
# AnimationPlayer: authored in the editor, perfect for choreographed multi-track moments —
# an animation named "treat_appear" might contain, in one timeline:
#   track 1: Sprite2D:material:shader_parameter/progress   1.0 → 0.0   (dissolve-in)
#   track 2: Sprite2D:material:shader_parameter/flash_amount  key at 0.3
#   track 3: AudioStreamPlayer "play" call method track
```

Rule of thumb: one uniform, dynamic duration → tween; several uniforms synchronized with sound/motion on a fixed timeline → `AnimationPlayer`. Both address uniforms through the same `shader_parameter/` property path, so migrating between them is mechanical.

### 12.3 Easing inside the shader

When `TIME` drives an effect but raw sine feels mechanical, shape it in-shader — these three lines cover most needs:

```glsl
float wave  = sin(TIME * speed) * 0.5 + 0.5;          // raw 0-1 oscillation
float eased = wave * wave * (3.0 - 2.0 * wave);        // smoothstep-shaped: gentler turnarounds
float pulse = pow(abs(sin(TIME * speed)), 3.0);        // sharp spikes, long rests — heartbeat
```

The middle line is the Hermite `smoothstep` polynomial applied to a signal — the same math as `smoothstep(0.0, 1.0, wave)` — turning constant-velocity oscillation into ease-in-out. `pow` on a rectified sine concentrates energy near the peaks: the Relax Room pet's "sleeping" glow breathes with exponent 2.2, reading as inhale-pause-exhale rather than metronome.

## 13. Recipe cookbook I: sprite effects

The cookbook sections are the module's practical core. Every recipe is complete (paste it into a `.gdshader`, assign, run), explained line by line, and annotated with the pixel-art considerations that generic tutorials skip. Recipes assume `shader_type canvas_item` on a `Sprite2D` unless stated otherwise.

The full index, for later reference:

| # | Recipe | Applied to | Animated by | Key techniques |
|---|---|---|---|---|
| 13.1 | Outline | Sprite / CanvasGroup | Tween on thickness | Neighbor alpha taps, `TEXTURE_PIXEL_SIZE` |
| 13.2 | Hit-flash | Sprite | Tween | `mix` to color, alpha preservation |
| 13.3 | Drop shadow | Sprite | Static | Offset self-sampling |
| 13.4 | Dissolve | Sprite | Tween on progress | Noise threshold, `discard`, edge band |
| 13.5 | Palette swap | Sprite / full screen | Tween on mix | LUT sampling, luminance, texel centers |
| 13.6 | Grayscale/sepia | Sprite / full screen | State-driven | `hint_enum` modes, color matrix |
| 13.7 | Shine sweep | Sprite | `TIME` | Axis projection, distance-to-band |
| 14.1 | Pixelate | Full screen / sprite | Tween (snapped) | Cell snapping via `floor` |
| 14.2 | CRT | Full screen | `TIME` | Barrel UV remap, per-channel taps, `FRAGCOORD` mask |
| 14.3 | Bayer dithering | Full screen | Static | Const matrix, `FRAGCOORD` anchoring, quantization |
| 14.4 | Glow emitters | Sprites + WorldEnvironment | `TIME` pulse | HDR 2D, overbright output |
| 14.5 | Day-night tint | Everywhere | Global uniform | Cosine phase curve, multiplicative tint |
| 15.1 | Wave / flag / wind | Sprite / mesh | `TIME` / `game_time` | UV vs vertex displacement, `world_vertex_coords` |
| 15.2 | Water reflection | Region rect | `TIME` | Mirrored `SCREEN_UV`, depth-scaled ripple |
| 15.3 | Radial wipe | Sprite / UI | Tween on progress | `atan` angle normalization |
| 15.4 | Click shockwave | Full screen | Tween + input | Aspect-correct rings, radial displacement |

### 13.1 Outline

The classic selection/hover treatment: a colored border drawn in the transparent pixels *around* the sprite's silhouette.

```glsl
shader_type canvas_item;

uniform vec4 outline_color : source_color = vec4(1.0);
uniform float thickness : hint_range(0.0, 5.0) = 1.0;

void fragment() {
    vec2 px = TEXTURE_PIXEL_SIZE;
    float a = texture(TEXTURE, UV).a;
    float top    = texture(TEXTURE, UV + vec2(0.0, -px.y * thickness)).a;
    float bottom = texture(TEXTURE, UV + vec2(0.0,  px.y * thickness)).a;
    float left   = texture(TEXTURE, UV + vec2(-px.x * thickness, 0.0)).a;
    float right  = texture(TEXTURE, UV + vec2( px.x * thickness, 0.0)).a;
    float outline = step(0.01, top + bottom + left + right) * (1.0 - a);
    COLOR = mix(texture(TEXTURE, UV), outline_color, outline);
}
```

Line by line:

- `px = TEXTURE_PIXEL_SIZE` — one texel expressed in UV units; multiplying offsets by this is what makes the shader resolution-independent (the same shader outlines a 16×16 icon and a 64×64 pet).
- The four `texture(...).a` reads sample the **alpha of the four orthogonal neighbors** at `thickness` texels away. Alpha is the silhouette; color is irrelevant to edge detection.
- `step(0.01, sum)` — 1.0 if *any* neighbor is opaque (sum over threshold), else 0.0. The 0.01 threshold tolerates slightly-soft alpha from import.
- `* (1.0 - a)` — the crucial mask: we are an outline pixel only if a neighbor is solid **and we ourselves are transparent**. Without this factor the outline paints over the sprite's own edge pixels.
- `mix(base, outline_color, outline)` — with `outline` at exactly 0 or 1, this is a branchless select: sprite where sprite, outline where outline.

Production notes: (1) the texture needs at least `thickness` texels of transparent padding on every side, or the outline clips at the quad boundary (§2.3); (2) four taps outline orthogonally — diagonal gaps appear on thin diagonal art. The 8-direction upgrade adds four diagonal taps:

```glsl
    float d1 = texture(TEXTURE, UV + vec2(-px.x,  -px.y) * thickness).a;
    float d2 = texture(TEXTURE, UV + vec2( px.x,  -px.y) * thickness).a;
    float d3 = texture(TEXTURE, UV + vec2(-px.x,   px.y) * thickness).a;
    float d4 = texture(TEXTURE, UV + vec2( px.x,   px.y) * thickness).a;
    float outline = step(0.01, top + bottom + left + right + d1 + d2 + d3 + d4) * (1.0 - a);
```

Eight taps per pixel is still trivially cheap for sprites; a smooth-growing outline (fractional thickness) fights pixel-art aesthetics — on the pixel grid, snap `thickness` to whole texels and animate it in steps.

**Variant — animated "selection" outline.** Replacing the flat `outline_color` with a computed one animates the border without touching the mask logic. Two production-tested choices:

```glsl
    // (a) Pulsing brightness — calm, reads as "hoverable":
    vec4 oc = outline_color * (0.75 + 0.25 * sin(TIME * 4.0));

    // (b) Marching stripes — reads as "currently selected":
    float stripe = step(0.5, fract((UV.x + UV.y) * 40.0 - TIME * 1.5));
    vec4 oc = mix(outline_color, outline_color * 0.35, stripe);

    COLOR = mix(texture(TEXTURE, UV), oc, outline);
```

Variant (b)'s diagonal stripes come from thresholding `fract()` of a scrolled diagonal coordinate — the same fract-pattern grammar as §4.9 — and the `- TIME * 1.5` term makes them march. Keep both variants inside one shader behind a `hint_enum` mode uniform (§13.6 pattern) rather than shipping three outline shaders.

> ✅ **Best practice** — For "outline on hover," toggle by tweening `thickness` 0→1 (or setting a `vec4` with zero alpha), not by swapping `material` at runtime; material swaps can trigger pipeline work (§17.5), a uniform change never does. For outlining a multi-sprite character as one silhouette, put this shader on a `CanvasGroup` (§10.3).

### 13.2 Hit-flash

The universal "took damage / was clicked" feedback: the sprite flashes solid white (or any color) and fades back, preserving its silhouette.

```glsl
shader_type canvas_item;

uniform vec4 flash_color : source_color = vec4(1.0);
uniform float flash_amount : hint_range(0.0, 1.0) = 0.0;

void fragment() {
    vec4 base = texture(TEXTURE, UV);
    COLOR = vec4(mix(base.rgb, flash_color.rgb, flash_amount), base.a);
}
```

Three lines of substance: sample the art; `mix` the RGB toward the flash color by `flash_amount`; keep the original alpha so the flash never bleeds outside the silhouette. At `flash_amount = 1.0` the sprite is a flat-colored stencil of itself — which is exactly the effect, and something plain `modulate` **cannot do**: modulate multiplies (white modulate = no-op, and nothing can *brighten toward* white), while this shader *replaces*.

Drive it from GDScript with a tween (the snippet in §8.3), or with an `AnimationPlayer` track keying `material:shader_parameter/flash_amount` 1.0 → 0.0 over ~0.2 s with an ease-out. If many nodes share the material, make `flash_amount` an **instance uniform** (§8.5) and the same shared material flashes nodes individually.

> ⚠️ **Pitfall** — Flashing via `modulate = Color.WHITE * 5.0` "sort of works" in HDR-enabled setups and silently does nothing in others. The mix-to-color shader is deterministic across renderers; prefer it.

**Variants — the feedback family.** The same two-uniform skeleton, with the mix target swapped, covers the whole vocabulary of instant feedback:

```glsl
    // (a) Classic white hit-flash (the base recipe):
    vec3 fx = flash_color.rgb;

    // (b) Invert flash — "critical hit" / glitch feedback:
    vec3 fx = vec3(1.0) - base.rgb;

    // (c) Silhouette pop — flatten to a solid stencil (flash_amount = 1 held briefly):
    vec3 fx = flash_color.rgb;              // same math; the *hold* makes the effect

    // (d) Poison/freeze tint pulse — flash toward a status color, driven by TIME:
    vec3 fx = flash_color.rgb;
    // and drive: flash_amount = 0.25 + 0.15 * sin(TIME * 5.0) while the status lasts

    COLOR = vec4(mix(base.rgb, fx, flash_amount), base.a);
```

The design insight is that these differ in *driver*, not shader: (a) is a 0.2 s tween spike, (c) is a two-frame hold at 1.0 then release, (d) is a standing oscillation gated by game state. One shader uniform, four distinct game-feel meanings — parameterization living exactly where §12.2's decision table says it should.

### 13.3 Drop shadow

A soft offset silhouette behind the sprite — grounding decorative items on Relax Room's shelves without baking shadows into every texture.

```glsl
shader_type canvas_item;

uniform vec4 shadow_color : source_color = vec4(0.0, 0.0, 0.0, 0.45);
uniform vec2 shadow_offset = vec2(2.0, 3.0);   // in texels

void fragment() {
    vec4 base = texture(TEXTURE, UV);
    vec2 offset_uv = UV - shadow_offset * TEXTURE_PIXEL_SIZE;
    float shadow_a = texture(TEXTURE, offset_uv).a * shadow_color.a;
    // Shadow exists where the *offset* sprite is opaque and we are not covered by the sprite itself.
    vec4 shadow = vec4(shadow_color.rgb, shadow_a);
    COLOR = mix(shadow, base, base.a);
}
```

Line by line: `offset_uv` looks *backwards* along the offset — pixel P shows shadow if the sprite, shifted by `shadow_offset`, covers P; the sampled alpha times the shadow color's alpha gives shadow coverage; the final `mix` layers the actual sprite over the shadow using the sprite's own alpha as the blend factor, so opaque art wins, transparent shows shadow, and semi-transparent edges blend correctly.

Constraints inherited from §2.3: the quad must contain the shadow — padding of at least `shadow_offset` texels on the shadow side. Sampling outside 0-1 UV must not wrap: ensure the texture imports with repeat off (default for sprites), otherwise the shadow of the sprite's *top* appears at its *bottom*. For pixel art keep the offset in whole texels; a (1.5, 1.5) offset bilinear-smears even under nearest filtering of the *screen* because the sample lands between texels.

**Variant — soft shadow.** For non-pixel-art contexts (UI panels, smooth art), average several offset taps to feather the shadow's edge:

```glsl
uniform float softness : hint_range(0.0, 4.0) = 1.5;   // blur radius in texels

float soft_shadow_alpha(vec2 base_uv) {
    vec2 px = TEXTURE_PIXEL_SIZE * softness;
    float a = 0.0;
    // 3x3 tap cross — 9 fetches, plenty for small shadows:
    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            a += texture(TEXTURE, base_uv + vec2(float(x), float(y)) * px).a;
        }
    }
    return a / 9.0;
}
```

Call it in place of the single offset fetch: `float shadow_a = soft_shadow_alpha(offset_uv) * shadow_color.a;`. The fixed-bound double loop is the uniform-cost kind (§2.2) and its 9 taps are §17.2's budget well spent — but on the pixel grid, prefer the hard single-tap version: soft shadows under crisp sprites read as a style clash.

### 13.4 Dissolve

The workhorse despawn/transition effect: the sprite burns away along a noise pattern, with a glowing edge at the dissolution front.

```glsl
shader_type canvas_item;

uniform sampler2D noise_tex : filter_nearest, repeat_enable, hint_default_white;
uniform float progress : hint_range(0.0, 1.0) = 0.0;   // 0 = intact, 1 = gone
uniform vec4 edge_color : source_color = vec4(1.0, 0.6, 0.1, 1.0);
uniform float edge_width : hint_range(0.0, 0.2) = 0.06;

void fragment() {
    vec4 base = texture(TEXTURE, UV);
    float noise = texture(noise_tex, UV).r;

    // Remap so progress 0 keeps everything, progress 1 removes everything,
    // including the edge band.
    float threshold = progress * (1.0 + edge_width);

    if (noise < threshold - edge_width) {
        discard;                                        // fully dissolved
    }

    float edge = 1.0 - smoothstep(threshold - edge_width, threshold, noise);
    vec3 rgb = mix(base.rgb, edge_color.rgb, edge);
    COLOR = vec4(rgb, base.a);
}
```

How it works: every pixel owns a noise value in 0-1; as `progress` rises, pixels whose noise falls below the moving threshold `discard` — the noise pattern *is* the dissolution order. Just above the discard line, a `smoothstep` band of width `edge_width` blends toward `edge_color`, producing the burning rim that sells the effect. The `(1.0 + edge_width)` remap guarantees `progress = 1.0` clears the edge band too — without it the sprite never fully disappears, a subtle off-by-epsilon that ships embarrassingly often.

Noise choice is the art direction: `NoiseTexture2D` with FastNoiseLite (smooth clouds → organic burn), a white-noise texture (per-pixel static → digital disintegration), or a hand-drawn gradient (directional wipe). For pixel art, set the noise texture's size to match the sprite's resolution and use `filter_nearest`, so dissolution happens in whole art-pixels — high-res noise under a low-res sprite dissolves in sub-texel crumbs that break the grid. Drive `progress` with a tween; pair with `await tween.finished` then `queue_free()` for despawns.

**Variant — directional dissolve.** Blending a UV gradient into the noise steers the burn — bottom-up "teleport", left-to-right "page turn":

```glsl
uniform vec2 direction = vec2(0.0, -1.0);        // (0,-1) = burns bottom-up
uniform float direction_bias : hint_range(0.0, 1.0) = 0.5;

    // Inside fragment(), replace the noise line with:
    float raw_noise = texture(noise_tex, UV).r;
    float gradient = dot(UV - 0.5, normalize(direction)) + 0.5;   // 0..1 along direction
    float noise = mix(raw_noise, gradient, direction_bias);
```

At `direction_bias` 0 the dissolve is pure noise; at 1 it is a clean directional wipe; between, a wipe with a ragged noisy front — usually the sweet spot at ~0.5-0.7. The `dot` against a normalized direction is the standard "project position onto an axis" idiom, worth recognizing: it turns any 2D direction into a 0-1 progress gradient across the sprite.

The complete despawn driver, for reference:

```gdscript
func despawn() -> void:
    var tw := create_tween()
    tw.tween_property(_mat, "shader_parameter/progress", 1.0, 0.6)\
      .set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUAD)
    await tw.finished
    queue_free()
```

> ⚠️ **Pitfall** — `discard` prevents the *write*, not the *work*, and it disables some hardware fast paths; a fully-dissolved node still pays fragment cost every frame it remains in the tree. Free or hide the node when `progress` reaches 1.0 — do not leave "invisible" dissolved sprites running.

### 13.5 Palette swap (LUT)

Recolor art through a lookup table: map each pixel's brightness to a position in a tiny palette texture. One shader gives you day/night furniture variants, team colors, and the Game Boy look — without re-exporting a single sprite.

```glsl
shader_type canvas_item;

uniform sampler2D palette : source_color, filter_nearest, repeat_disable, hint_default_white;
uniform float mix_amount : hint_range(0.0, 1.0) = 1.0;

void fragment() {
    vec4 base = texture(TEXTURE, UV);
    float lum = dot(base.rgb, vec3(0.2126, 0.7152, 0.0722));   // Rec. 709 luminance
    // Sample the Nx1 palette strip by luminance. Half-texel inset avoids edge bleed.
    float w = float(textureSize(palette, 0).x);
    float u = clamp(lum, 0.0, 1.0) * (w - 1.0) / w + 0.5 / w;
    vec3 mapped = texture(palette, vec2(u, 0.5)).rgb;
    COLOR = vec4(mix(base.rgb, mapped, mix_amount), base.a);
}
```

Line by line: luminance collapses the pixel to a single 0-1 brightness (the Rec. 709 weights match how bright channels actually *look*); `textureSize` reads the palette's width so the shader adapts to any strip length; the `(w-1)/w + 0.5/w` arithmetic maps brightness onto **texel centers** — sampling a 4-wide strip at u=1.0 without the inset lands on the texture's edge and, under linear filtering or repeat, bleeds into the wrong color, so we do the inset *and* declare `filter_nearest, repeat_disable`; finally `mix_amount` lets you blend between original art and swapped palette (crossfading to night palette over 60 real seconds is one tween on this uniform).

The palette itself is a 4×1 (or 8×1, 16×1) PNG, darkest color on the left — author strips in any pixel editor. The DMG palette from §8.4 as a strip gives instant Game Boy. Two upgrades worth knowing: a 2D LUT (luminance × palette-row) selected by a second uniform animates *between* palettes in-shader; true *index-based* swap (replace exact color A with exact color B, ignoring brightness) instead compares against key colors directly.

**Variant — exact-color swap.** When brightness-indexing is too blunt (two different colors share a luminance — the pet's red scarf and brown fur), swap specific colors:

```glsl
shader_type canvas_item;

uniform vec3 key_colors[4];      // colors to find   (set from GDScript)
uniform vec3 out_colors[4];      // their replacements
uniform float tolerance : hint_range(0.0, 0.2) = 0.02;

void fragment() {
    vec4 base = texture(TEXTURE, UV);
    vec3 rgb = base.rgb;
    for (int i = 0; i < key_colors.length(); i++) {
        float match = 1.0 - step(tolerance, distance(base.rgb, key_colors[i]));
        rgb = mix(rgb, out_colors[i], match);
    }
    COLOR = vec4(rgb, base.a);
}
```

Per key: `distance` in RGB space measures closeness; `step(tolerance, …)` inverted gives a 1.0 match flag within tolerance; `mix` applies the replacement only on match. Four keys = four fixed loop iterations = uniform cost. Exact-match swaps demand `filter_nearest` on the **sprite texture** (bilinear-filtered edge pixels are blends that match no key — the symptom is a halo of unswapped fringe pixels) and a small nonzero `tolerance` to absorb PNG quantization. Feed the arrays as `PackedVector3Array`s per §8.4; `Color` converts with `Vector3(c.r, c.g, c.b)`.

> ✅ **Best practice** — Keep palettes as committed `.png` assets, not procedurally generated gradients: artists can eyedrop, diff, and review them, and the [Build and Export](BUILD_AND_EXPORT.md) pipeline treats them as ordinary textures with no import surprises. Turn off mipmaps and filtering in the import settings as well as in the hint — belt and suspenders.

### 13.6 Grayscale / sepia toggle

A mode-switched color grade — the "away/paused" state for Relax Room, and a template for any N-mode effect via `hint_enum`.

```glsl
shader_type canvas_item;

uniform int mode : hint_enum("Normal", "Grayscale", "Sepia") = 0;
uniform float amount : hint_range(0.0, 1.0) = 1.0;

const mat3 SEPIA = mat3(
    vec3(0.393, 0.349, 0.272),   // column 0: red output weights
    vec3(0.769, 0.686, 0.534),   // column 1: green output weights
    vec3(0.189, 0.168, 0.131)    // column 2: blue output weights
);

void fragment() {
    vec4 base = COLOR;   // post-modulate: grade whatever the pipeline produced
    vec3 graded = base.rgb;

    if (mode == 1) {
        graded = vec3(dot(base.rgb, vec3(0.2126, 0.7152, 0.0722)));
    } else if (mode == 2) {
        graded = clamp(SEPIA * base.rgb, 0.0, 1.0);
    }

    COLOR = vec4(mix(base.rgb, graded, amount), base.a);
}
```

Points of technique: starting from `COLOR` rather than `texture(TEXTURE, UV)` means the grade composes with modulate and vertex colors — correct for a *state* effect that should desaturate the node however it currently looks. The sepia matrix is the standard photographic transform expressed as a `mat3` (GDShader matrices are column-major: each `vec3` is a *column*, so `SEPIA * rgb` computes the three classic weighted sums); `clamp` guards the slight >1.0 the matrix can produce on bright pixels. The `if/else if` on a **uniform** is the cheap kind of branch (§2.2) — all pixels take the same path, so resist the urge to "optimize" it into arithmetic.

Because the `mode` uniform is an int with `hint_enum`, the Inspector shows a dropdown, and GDScript reads naturally:

```gdscript
enum GradeMode { NORMAL, GRAYSCALE, SEPIA }

func set_away(is_away: bool) -> void:
    _mat.set_shader_parameter("mode", GradeMode.GRAYSCALE if is_away else GradeMode.NORMAL)
    # Fade the effect in rather than snapping:
    create_tween().tween_property(_mat, "shader_parameter/amount",
            1.0 if is_away else 0.0, 0.4)
```

Applied to the post-processing `ColorRect` from §11.3 — with `base` sampled from a `hint_screen_texture` uniform at `SCREEN_UV` instead of read from `COLOR` — the same grading logic desaturates the entire scene: the cookbook's first demonstration that sprite effects and full-screen effects are the same language with a different input.

### 13.7 Shine sweep

The diagonal gleam that slides across an item — "new!", "rare!", or Relax Room's daily-gift chest. A pure fragment effect: no second texture, no extra nodes.

```glsl
shader_type canvas_item;

uniform vec4 shine_color : source_color = vec4(1.0, 1.0, 0.9, 1.0);
uniform float shine_width : hint_range(0.01, 0.5) = 0.12;
uniform float shine_angle : hint_range(0.0, 3.14159) = 0.9;   // radians
uniform float period : hint_range(0.5, 10.0) = 3.0;            // seconds between sweeps
uniform float intensity : hint_range(0.0, 1.0) = 0.7;

void fragment() {
    vec4 base = texture(TEXTURE, UV);

    // Project UV onto the sweep axis: 0..~1.4 across the sprite diagonally.
    vec2 axis = vec2(cos(shine_angle), sin(shine_angle));
    float along = dot(UV, axis);

    // A band that travels from -width to 1.4+width once per period, then waits.
    float t = fract(TIME / period);                       // 0..1 sawtooth
    float pos = mix(-shine_width, 1.4 + shine_width, t);  // band center this frame
    float band = 1.0 - smoothstep(0.0, shine_width, abs(along - pos));

    vec3 rgb = base.rgb + shine_color.rgb * band * intensity * base.a;
    COLOR = vec4(rgb, base.a);
}
```

Reading it with the §4.9 grammar: `dot(UV, axis)` projects each pixel onto the sweep direction (the same projection idiom as the directional dissolve); `fract(TIME / period)` is a sawtooth clock restarting every `period` seconds; `mix` maps that clock to a band position that fully crosses the sprite (the 1.4 covers the diagonal of UV space); `abs(along - pos)` measured against `shine_width` through an inverted `smoothstep` is a soft distance-to-band mask. The shine *adds* light (`+`, scaled by `base.a` to respect the silhouette) rather than mixing — gleams brighten. With HDR 2D and the §14.4 glow chain active, raise `intensity` above 1.0 and the sweep blooms.

Pixel-grid adaptation, per §19: quantize the band — `band = step(0.5, band);` after computing it — and set `shine_width` so the lit diagonal is a whole number of texels wide. The sweep then advances as a crisp stair-stepped ribbon, matching the art.

## 14. Recipe cookbook II: retro and full-screen effects

These recipes target the post-processing `ColorRect` structure from §11.3 unless noted — they process the whole frame.

### 14.1 Pixelate

Quantize the screen (or a sprite) to a coarser grid — transition effect, censor blur, or "the app is dreaming" state. On sprite art that is *already* pixelated, this reads as dropping to a lower resolution tier.

```glsl
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;
uniform float pixel_size : hint_range(1.0, 64.0) = 4.0;   // screen pixels per cell

void fragment() {
    vec2 cell = pixel_size * SCREEN_PIXEL_SIZE;            // cell size in UV units
    vec2 snapped = (floor(SCREEN_UV / cell) + 0.5) * cell; // center of this pixel's cell
    COLOR = vec4(textureLod(screen_texture, snapped, 0.0).rgb, 1.0);
}
```

The entire trick is two lines: divide the screen into `pixel_size`-wide cells, and make every fragment inside a cell sample the **same** point — the cell's center (`floor(...) + 0.5`). All pixels of a cell fetch one identical texel, so the screen appears rebuilt from large blocks. The `+ 0.5` matters: snapping to cell *corners* instead of centers samples along texel boundaries where filtering can shimmer.

Sprite-local variant: replace `SCREEN_UV`/`SCREEN_PIXEL_SIZE` with `UV`/`TEXTURE_PIXEL_SIZE` and drop the screen sampler — the same math pixelates one node's texture. Animate `pixel_size` 1→32 with an ease-in tween for a "signal lost" transition; snap it to powers of two if the intermediate sizes look muddy against the pixel-art grid:

```gdscript
# Mosaic scene transition: pixelate out, switch, pixelate in.
func transition_to(scene_path: String) -> void:
    var tw := create_tween()
    tw.tween_method(_set_mosaic, 1.0, 32.0, 0.35)          # coarsen (snapped inside)
    tw.tween_callback(get_tree().change_scene_to_file.bind(scene_path))
    tw.tween_method(_set_mosaic, 32.0, 1.0, 0.35)          # refine

func _set_mosaic(value: float) -> void:
    var snapped_size := float(nearest_po2(int(value)))     # 1, 2, 4, 8, 16, 32
    _mosaic_mat.set_shader_parameter("pixel_size", snapped_size)
```

`tween_method` routes the tweened value through a snapping function before it touches the uniform — the general pattern for any uniform that must move through *quantized* values (§19.2's texel snapping is the same idea living inside the shader instead). The effect rect must live on a `CanvasLayer` that survives the scene change (an autoload-managed layer), or the second half of the transition has nothing to run on.

### 14.2 Scanline CRT (curvature + RGB shift)

The module's flagship full-screen recipe: the original scanline pass from earlier versions of this course, upgraded with barrel curvature, RGB phosphor shift, and a vignette — a complete CRT look with every stage toggleable.

```glsl
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear;

uniform float scanline_intensity : hint_range(0.0, 1.0) = 0.35;
uniform float scanline_count = 240.0;
uniform float curvature : hint_range(0.0, 0.25) = 0.06;
uniform float rgb_shift : hint_range(0.0, 3.0) = 0.8;      // in screen pixels
uniform float vignette_strength : hint_range(0.0, 1.0) = 0.25;

vec2 curve_uv(vec2 uv, float amount) {
    vec2 centered = uv * 2.0 - 1.0;                        // -1..1, center = 0
    centered *= 1.0 + amount * dot(centered, centered);    // push edges outward
    return centered * 0.5 + 0.5;                           // back to 0..1
}

void fragment() {
    vec2 uv = curve_uv(SCREEN_UV, curvature);

    // Outside the curved tube: black bezel.
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        COLOR = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
        // RGB shift: sample each channel at a slightly different x.
        vec2 shift = vec2(rgb_shift * SCREEN_PIXEL_SIZE.x, 0.0);
        float r = textureLod(screen_texture, uv + shift, 0.0).r;
        float g = textureLod(screen_texture, uv, 0.0).g;
        float b = textureLod(screen_texture, uv - shift, 0.0).b;
        vec3 col = vec3(r, g, b);

        // Scanlines: darken every other virtual line.
        float scan = sin(uv.y * scanline_count * PI) * 0.5 + 0.5;
        col *= mix(1.0, scan, scanline_intensity);

        // Vignette: darken toward corners.
        vec2 v = uv * 2.0 - 1.0;
        col *= 1.0 - vignette_strength * dot(v, v) * 0.5;

        COLOR = vec4(col, 1.0);
    }
}
```

Stage by stage:

- **Curvature** — `curve_uv` remaps flat screen UVs as if projected on a bulging tube. `dot(centered, centered)` is squared distance from center, so displacement grows quadratically toward edges — the classic barrel-distortion form. We move the *read* coordinate (displacement always moves reads, §11.4); pixels whose curved UV falls outside 0-1 become the black bezel. This outer `if` is divergent only along the bezel boundary — harmless.
- **RGB shift** — each channel samples at a slightly different horizontal position, imitating phosphor misconvergence. Even 0.8 px reads as "CRT" at normal viewing; 3 px reads as "broken VHS." Note the shift scales with `SCREEN_PIXEL_SIZE`, staying constant in *physical* pixels at any window size.
- **Scanlines** — the preserved core of the original recipe: a sine over `uv.y` at `scanline_count` line-pairs, remapped to 0-1, attenuating brightness. Set `scanline_count` to your game's *design* vertical resolution (e.g., 240 for a 426×240 base) so lines align with art rows; a mismatched count produces moiré (which, at low intensity, is itself period-authentic).
- **Vignette** — quadratic corner darkening; cheap and it composes the previous stages into "one physical object."

Every stage at 0 disables itself, so this one shader scales from "subtle scanlines" to "full retro TV," and the `reduce_motion`/accessibility toggle from §8.6 can zero `curvature` and `rgb_shift` while keeping the look.

Two optional stages complete the period kit — append before the final `COLOR` write:

```glsl
        // Phosphor mask: alternate mild R/G/B emphasis across pixel columns.
        int column = int(FRAGCOORD.x) % 3;
        vec3 mask = vec3(1.0);
        if (column == 0) { mask = vec3(1.0, 0.85, 0.85); }
        else if (column == 1) { mask = vec3(0.85, 1.0, 0.85); }
        else { mask = vec3(0.85, 0.85, 1.0); }
        col *= mix(vec3(1.0), mask, phosphor_strength);   // uniform, 0-1

        // Flicker: tiny brightness wobble at mains-adjacent frequency.
        col *= 1.0 + flicker_strength * 0.03 * sin(TIME * 60.0 * TAU);
```

The phosphor mask keys off `FRAGCOORD.x % 3` — physical screen columns, like the dither matrix — tinting alternate columns toward R/G/B the way an aperture grille does; keep `phosphor_strength` subtle (~0.3) or the image visibly darkens (the mask removes light; real CRTs compensated with brightness). The flicker term is a 60 Hz sine at ±3% maximum — and it is *exactly* the kind of effect the `reduce_motion` global must zero, since flicker is an accessibility hazard before it is an aesthetic.

> ⚠️ **Pitfall** — Apply CRT *after* any UI you want inside the effect and *below* any UI you don't (layer order of `CanvasLayer`s decides). Shipping a settings menu that is itself curved and RGB-shifted is a real accessibility complaint, not a vibe; put the options UI on a layer above the effect rect.

### 14.3 Bayer-matrix ordered dithering

The stub in the previous edition of this module — "implement Bayer matrix lookup" — expanded to the full, working implementation. Ordered dithering quantizes colors to a limited set while faking intermediate shades through a fixed screen-space threshold pattern: *the* 1-bit / retro-print look.

```glsl
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;
uniform int color_levels : hint_range(2, 16) = 4;   // shades per channel after quantization
uniform float dither_strength : hint_range(0.0, 1.0) = 1.0;

// 4x4 Bayer matrix, row-major. Values 0-15; (v + 0.5)/16 gives thresholds
// evenly distributed in (0,1).
const int BAYER[16] = int[16](
     0,  8,  2, 10,
    12,  4, 14,  6,
     3, 11,  1,  9,
    15,  7, 13,  5
);

float bayer_threshold(ivec2 pixel) {
    int idx = (pixel.x % 4) + (pixel.y % 4) * 4;
    return (float(BAYER[idx]) + 0.5) / 16.0;
}

void fragment() {
    vec3 col = textureLod(screen_texture, SCREEN_UV, 0.0).rgb;

    float levels = float(color_levels - 1);
    float threshold = bayer_threshold(ivec2(FRAGCOORD.xy));

    // Add a sub-quantum bias based on the threshold, then quantize.
    vec3 biased = col + (threshold - 0.5) / levels * dither_strength;
    vec3 quantized = floor(biased * levels + 0.5) / levels;

    COLOR = vec4(clamp(quantized, 0.0, 1.0), 1.0);
}
```

How ordered dithering actually works, in three steps:

1. **The matrix.** The 4×4 Bayer matrix arranges the numbers 0-15 so that any small neighborhood contains a spread of values — thresholds `(v + 0.5)/16` tile the screen in a fixed pattern. Each screen pixel owns one threshold via `FRAGCOORD.xy % 4` (`FRAGCOORD` is in *screen* pixels, so the pattern is stable regardless of what moves underneath — the signature "fixed dither field" look).
2. **The bias.** `(threshold - 0.5) / levels` nudges each pixel's color up or down by *up to half a quantization step*, differently per pixel according to the matrix.
3. **The quantization.** `floor(x * levels + 0.5) / levels` rounds each channel to `color_levels` evenly spaced values. Because neighboring pixels were biased differently, a mid-tone flips between adjacent quantized shades in the Bayer pattern — at viewing distance, the eye integrates the checkered flips back into the intermediate tone.

At `color_levels = 2` each channel is pure 0-or-1 — eight colors total, the harshest look; combine with the palette-swap LUT from §13.5 (dither first, palette second) for authentic 1-bit or DMG rendering of the *entire scene*. For a finer pattern, the 8×8 Bayer matrix is the same construction with 64 values — worth it above ~1080p where 4×4 cells become visible as texture. For completeness (destined for `dither.gdshaderinc`):

```glsl
const int BAYER8[64] = int[64](
     0, 32,  8, 40,  2, 34, 10, 42,
    48, 16, 56, 24, 50, 18, 58, 26,
    12, 44,  4, 36, 14, 46,  6, 38,
    60, 28, 52, 20, 62, 30, 54, 22,
     3, 35, 11, 43,  1, 33,  9, 41,
    51, 19, 59, 27, 49, 17, 57, 25,
    15, 47,  7, 39, 13, 45,  5, 37,
    63, 31, 55, 23, 61, 29, 53, 21
);

float bayer8_threshold(ivec2 pixel) {
    int idx = (pixel.x % 8) + (pixel.y % 8) * 8;
    return (float(BAYER8[idx]) + 0.5) / 64.0;
}
```

Note the recursive structure visible in the numbers: each 4×4 quadrant of the 8×8 matrix is the 4×4 matrix scaled and offset — Bayer matrices of any power-of-two size are generated this way, which is also your correctness check when transcribing: quadrant top-left values must be `4 * v_4x4 + {0, 2, 3, 1}` per quadrant.

> ✅ **Best practice** — Dithering must operate on *final* colors: place this rect above color grading and glow layers. And because the pattern is anchored to physical screen pixels, run it at native resolution even if the game renders at a low base resolution and upscales — dithering the low-res buffer then scaling by 3× produces 3×3 blocks of dither, which reads as noise, not shading. (Viewport scaling architecture: [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md).)

### 14.4 Glow, paired with WorldEnvironment

Glow/bloom — bright pixels bleeding light — is *not* a canvas_item shader: it is a scene-level effect provided by a `WorldEnvironment` node, and shaders participate by deciding **which pixels count as bright**. The 2D setup on Godot 4.x:

1. Project Settings → Rendering → Viewport → **HDR 2D = On**. Without this the 2D buffer clamps colors at 1.0 and glow has nothing to find. (Requires Forward+ or Mobile renderer for full quality.)
2. Add a `WorldEnvironment` node; in its `Environment` resource enable **Glow**, set *Blend Mode* (Additive for neon, Softlight for subtle), and raise *HDR Threshold* to taste (e.g., 1.0 — only overbright pixels bloom).
3. In shaders, push emissive pixels **above 1.0**:

```glsl
shader_type canvas_item;

uniform float glow_strength : hint_range(1.0, 8.0) = 3.0;
uniform vec4 glow_color : source_color = vec4(1.0, 0.85, 0.4, 1.0);

void fragment() {
    vec4 base = texture(TEXTURE, UV);
    // The sprite's alpha-masked bright parts become overbright emitters:
    float emit = step(0.9, dot(base.rgb, vec3(0.333)));   // bright art = emitter
    vec3 rgb = base.rgb + glow_color.rgb * emit * (glow_strength - 1.0);
    COLOR = vec4(rgb, base.a);
}
```

The `emit` mask selects near-white parts of the art (the lamp's bulb pixels, the pet's magic eyes); multiplying by `glow_strength - 1.0` and *adding* pushes exactly those pixels past 1.0. The WorldEnvironment does the rest — threshold, downsampled blur chain, and composite — far better and cheaper than any hand-rolled canvas blur. Animate `glow_strength` with the eased `TIME` pulse from §12.3 for breathing lamps:

```gdscript
# lamp.gd — breathing glow, shader-clock version (zero per-frame script cost):
# in the shader: rgb += glow_color.rgb * emit * (glow_strength - 1.0)
#                       * (0.85 + 0.15 * pow(abs(sin(TIME * 0.8)), 2.2));

# Or event-driven (lamp turns on): one tween, then the shader idles.
func turn_on() -> void:
    create_tween().tween_property(_mat, "shader_parameter/glow_strength", 3.0, 1.2)\
        .from(1.0).set_trans(Tween.TRANS_SINE)
```

A control-flow choice worth copying: the *breathing* lives in the shader (perpetual, §12.2's left column), the *state change* lives in a tween (event, right column) — the two clocks compose because the shader multiplies them.

> ⚠️ **Pitfall** — "Glow works in the editor but not in the export" is almost always HDR 2D off in the exported project settings, or the Compatibility renderer silently in use on the target machine (glow in Compatibility is limited). Verify `RenderingServer.get_current_rendering_method()` at startup in debug builds and test the exported build on the minimum-spec target — see [Build and Export](BUILD_AND_EXPORT.md) for the renderer-fallback matrix.

### 14.5 Day-night tint via global uniform

The promised clean version of §8.6's sketch — the effect that makes Relax Room feel like it lives in the user's timezone. One global `day_phase` (0 at midnight, 0.5 at noon, wrapping at 1) set by the clock autoload; every tinted material reads it.

```glsl
shader_type canvas_item;

global uniform float day_phase;

uniform vec4 night_color : source_color = vec4(0.45, 0.50, 0.85, 1.0);
uniform vec4 dusk_color : source_color = vec4(1.0, 0.65, 0.45, 1.0);
uniform float max_tint : hint_range(0.0, 1.0) = 0.55;

void fragment() {
    vec4 base = COLOR;

    // Daylight curve: cosine over the day. 1.0 at noon, -1.0 at midnight.
    float daylight = cos((day_phase - 0.5) * TAU) * 0.5 + 0.5;   // 0 night … 1 noon

    // Night factor rises as daylight falls; dusk factor peaks at the transition.
    float night = smoothstep(0.45, 0.15, daylight);
    float dusk = smoothstep(0.55, 0.35, daylight) * (1.0 - night);

    vec3 rgb = base.rgb;
    rgb = mix(rgb, rgb * dusk_color.rgb, dusk * max_tint);
    rgb = mix(rgb, rgb * night_color.rgb, night * max_tint);
    COLOR = vec4(rgb, base.a);
}
```

Design notes: the cosine turns wrapping clock-phase into a smooth, symmetric daylight signal with no seam at midnight (the naive `abs(phase - 0.5)` sketch from §8.6 has a corner there — this is why the module promised a cleaner curve). Two `smoothstep` windows carve *night* and *dusk* bands out of the daylight signal; dusk is masked by `(1.0 - night)` so the warm tint yields to the cool one instead of fighting it. Tints **multiply** (`rgb * color`) rather than mix toward flat color — multiplication preserves the art's value structure, reading as *lighting* rather than *fog*.

Deployment is the elegant part: this shader (or just its two `mix` lines via a `.gdshaderinc`) goes on room background, furniture, and pet materials — or once on the full-screen rect with a screen sampler. Nothing subscribes to signals, nothing loops over nodes; the autoload writes one float per frame (`RenderingServer.global_shader_parameter_set`, §8.6) and the entire scene agrees about the hour. When the user drags the OS clock forward, the room follows on the next frame — a moment that consistently delights testers.

The complete clock autoload, including the frugality that a companion app owes the CPU (update the global once per second, not per frame — sky light does not change faster than that):

```gdscript
# day_night_clock.gd — autoload (see AUTOLOAD_SAFETY.md for singleton rules)
extends Node

const SECONDS_PER_DAY := 86400.0
var _accumulator := 0.0

func _ready() -> void:
    _push_phase()   # correct tint on the very first frame

func _process(delta: float) -> void:
    _accumulator += delta
    if _accumulator >= 1.0:
        _accumulator = 0.0
        _push_phase()

func _push_phase() -> void:
    var t := Time.get_time_dict_from_system()
    var seconds := float(t.hour * 3600 + t.minute * 60 + t.second)
    RenderingServer.global_shader_parameter_set("day_phase", seconds / SECONDS_PER_DAY)
```

Extension hooks that fall out for free: a *weather* system multiplies the pushed phase toward dusk values during storms (overcast = perpetual dusk); a *demo mode* sweeps `day_phase` over 30 seconds for screenshots; and a settings option can freeze the phase for users who dislike the changing tint — all by owning this single writer. One writer per global, always: two systems calling `global_shader_parameter_set` on the same name is a race wearing a trench coat.

## 15. Recipe cookbook III: motion and gameplay effects

### 15.1 Wave / flag motion

Cloth-like waving for banners, plants, and the curtain in Relax Room's window. There are two honest implementations with different geometry requirements — know both, choose by node type.

**Variant A — fragment-space UV wave (works on any Sprite2D):**

```glsl
shader_type canvas_item;

uniform float amplitude : hint_range(0.0, 0.2) = 0.03;   // in UV units
uniform float frequency : hint_range(0.0, 20.0) = 6.0;
uniform float speed : hint_range(0.0, 10.0) = 2.5;
uniform float pin_left : hint_range(0.0, 1.0) = 1.0;      // 1 = left edge pinned

void fragment() {
    float pin = mix(1.0, UV.x, pin_left);   // 0 at pinned edge → no motion there
    vec2 uv = UV;
    uv.y += sin(UV.x * frequency + TIME * speed) * amplitude * pin;
    vec4 col = texture(TEXTURE, uv);
    // Kill samples displaced outside the texture:
    col.a *= step(0.0, uv.y) * step(uv.y, 1.0);
    COLOR = col;
}
```

The read coordinate's `y` oscillates as a traveling wave along `x`; `pin` scales amplitude from 0 at the flagpole edge to full at the free edge, which is what makes it read as *attached* cloth rather than a floating jelly. The alpha guard handles displaced samples that leave the 0-1 range (without it, `repeat_enable` textures wrap and the flag's bottom appears at its top). Requirement from §2.3: the texture needs vertical transparent padding of at least `amplitude` so the wave has room inside the quad.

**Variant B — vertex-space wave (real geometry motion):**

```glsl
shader_type canvas_item;

uniform float amplitude : hint_range(0.0, 20.0) = 4.0;    // in pixels
uniform float frequency : hint_range(0.0, 0.5) = 0.08;
uniform float speed : hint_range(0.0, 10.0) = 2.5;

void vertex() {
    VERTEX.y += sin(VERTEX.x * frequency + TIME * speed) * amplitude * UV.x;
}
```

Three lines — but on a plain `Sprite2D` it does almost nothing visible, and understanding *why* is the lesson: a sprite quad has **four vertices**, so the "wave" can only tilt/stretch the quad linearly between corners. Vertex effects need vertex *density*. Give the shader real geometry with a subdivided `MeshInstance2D` (a `QuadMesh`/`PlaneMesh` with `subdivide_width` cranked up, converted for 2D use) or a `Polygon2D` with added internal vertices — then each interior vertex displaces independently and the cloth truly ripples, at per-vertex cost instead of per-pixel.

**Variant C — world-space wind over many sprites.** Variant B composes with `render_mode world_vertex_coords` for the wind-over-many-grass-sprites setup teased in §7.2 — the complete shader, shared by every grass/plant sprite in the scene:

```glsl
shader_type canvas_item;
render_mode world_vertex_coords;

global uniform float game_time;    // pause-respecting clock, §12.1

uniform float sway : hint_range(0.0, 8.0) = 2.0;         // pixels at the tip
uniform float wavelength : hint_range(10.0, 400.0) = 120.0;  // world px per wave
uniform float wind_speed : hint_range(0.0, 6.0) = 1.2;

void vertex() {
    // UV.y: 0 at the sprite's top (free tip), 1 at its bottom (rooted).
    float root = 1.0 - UV.y;                  // 1 at tip, 0 at base
    float phase = VERTEX.x / wavelength * TAU + game_time * wind_speed;
    VERTEX.x += sin(phase) * sway * root * root;   // quadratic: tips move most
}
```

Because `VERTEX` is in **world** coordinates, `phase` depends on each vertex's *world* x — a whole row of tufts sways as one connected field, each at its own position along the same traveling wave, with zero coordination code. `root * root` anchors bases and exaggerates tips quadratically (linear looks like rigid sticks pivoting). Each tuft is only a 4-vertex quad, but here that is *enough*: grass reads as "tilting from the root," which a linear quad deformation genuinely is — the rare case where Variant B needs no subdivision. Reading `game_time` instead of `TIME` means the meadow freezes when the game pauses, consistent with everything else.

> ✅ **Best practice** — Rule of thumb: **UV waves for texture-level shimmer, vertex waves for silhouette-level motion.** If the *outline* of the object must move (flag edge against the sky), only Variant B on subdivided geometry does it truthfully; if the motion stays inside the silhouette (curtain folds), Variant A is cheaper and needs no special geometry.

### 15.2 Water reflection

A shimmering reflection band below the scene — Relax Room's fish-tank surface, or a puddle under the window. The screen-space version reflects *everything above the water line* automatically, whatever it is:

```glsl
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear;
uniform float water_top : hint_range(0.0, 1.0) = 0.72;   // waterline, in SCREEN_UV.y
uniform float wave_strength : hint_range(0.0, 0.02) = 0.004;
uniform float wave_speed : hint_range(0.0, 8.0) = 2.0;
uniform vec4 water_tint : source_color = vec4(0.25, 0.45, 0.65, 1.0);
uniform float fade : hint_range(0.0, 1.0) = 0.6;

void fragment() {
    // How deep below the waterline this pixel is (0 at surface):
    float depth = SCREEN_UV.y - water_top;

    // Mirror: sample as far ABOVE the line as we are below it.
    vec2 uv = vec2(SCREEN_UV.x, water_top - depth);

    // Ripple grows with depth; two sines at different frequencies avoid periodicity.
    float ripple = sin(SCREEN_UV.y * 90.0 + TIME * wave_speed)
                 + 0.5 * sin(SCREEN_UV.y * 150.0 - TIME * wave_speed * 1.3);
    uv.x += ripple * wave_strength * depth * 20.0;

    vec3 reflected = textureLod(screen_texture, uv, 0.0).rgb;
    vec3 col = mix(reflected, reflected * water_tint.rgb, 0.55);

    // Fade out with depth so the reflection dissolves into water color:
    float vis = 1.0 - smoothstep(0.0, 0.28, depth) * fade;
    COLOR = vec4(mix(water_tint.rgb * 0.6, col, vis), 1.0);
}
```

This shader lives on a `ColorRect` covering only the water region (its top edge at the waterline). Mechanics: `depth` measures how far into the water we are; the mirror line `water_top - depth` reads the screen *reflected across the waterline* — the geometric heart of the effect; the ripple is two incommensurate sines whose horizontal displacement **scales with depth** (`* depth * 20.0`), matching how real reflections wobble more the farther they stretch; tint and depth-fade then turn a perfect mirror into *water*. Because it is screen-reading, the reflection updates live — the pet walking past the tank is reflected with zero extra wiring.

A sprite-local alternative avoids screen reads entirely and works when the reflected subject is a single known sprite: a second `Sprite2D` with `flip_v = true` and the same texture, placed under the original, carrying this smaller shader —

```glsl
shader_type canvas_item;

uniform float wave_strength : hint_range(0.0, 0.05) = 0.01;
uniform float wave_speed : hint_range(0.0, 8.0) = 2.0;
uniform vec4 water_tint : source_color = vec4(0.3, 0.5, 0.7, 1.0);
uniform float fade_start : hint_range(0.0, 1.0) = 0.1;

void fragment() {
    vec2 uv = UV;
    uv.x += sin(UV.y * 30.0 + TIME * wave_speed) * wave_strength * UV.y;
    vec4 base = texture(TEXTURE, uv);
    base.rgb = mix(base.rgb, base.rgb * water_tint.rgb, 0.5);
    base.a *= (1.0 - smoothstep(fade_start, 1.0, UV.y)) * 0.7;   // fade with depth
    COLOR = base;
}
```

Because the node is already flipped, `UV.y` runs 0 at the waterline and 1 at the reflection's deep end — the ripple and the alpha fade both scale with it, echoing the depth-scaling of the screen-space version at a fraction of the cost. Choose this variant when the effect must live inside a `SubViewport` the screen texture cannot see, on the Compatibility renderer where you are rationing back-buffer copies, or whenever only one known subject reflects.

> ⚠️ **Pitfall** — Screen-space reflection can only reflect what is *on screen and already drawn*: draw order and layers decide what exists in the back-buffer when the water rect draws (§11.1). If the reflection is mysteriously missing the pet, the pet is drawn on a later `CanvasLayer` than the water — reorder, or accept the omission as art direction.

### 15.3 Radial cooldown / progress wipe

The circular sweep every ability icon and timer needs — as a shader, one draw, no mask textures, no `Clip Children`. In Relax Room it rings the pet's "attention" button while the cooldown runs.

```glsl
shader_type canvas_item;

uniform float progress : hint_range(0.0, 1.0) = 0.0;      // 0 = fully dimmed, 1 = ready
uniform vec4 dim_color : source_color = vec4(0.0, 0.0, 0.0, 0.6);
uniform float smoothing : hint_range(0.0, 0.05) = 0.008;
uniform bool clockwise = true;

void fragment() {
    vec4 base = texture(TEXTURE, UV);

    // Angle of this pixel around the sprite center, 0 at 12 o'clock, 0-1 over a turn.
    vec2 dir = UV - vec2(0.5);
    float angle = atan(dir.x, -dir.y);            // 0 at top, ±PI at bottom
    float turn = fract(angle / TAU + 1.0);        // normalize to 0-1
    if (!clockwise) {
        turn = 1.0 - turn;
    }

    // Pixels with turn < progress are "recharged"; smooth the sweep edge slightly.
    float charged = smoothstep(turn - smoothing, turn + smoothing, progress);

    vec3 rgb = mix(mix(base.rgb, dim_color.rgb, dim_color.a), base.rgb, charged);
    COLOR = vec4(rgb, base.a);
}
```

The geometry: `dir` points from sprite center to this pixel; `atan(dir.x, -dir.y)` — note the argument order and negation — yields an angle that is 0 at 12 o'clock and increases clockwise, the convention every cooldown UI uses; dividing by `TAU` and `fract`-ing normalizes a full revolution to 0-1 so it compares directly against `progress`. Each pixel then asks one question — *has the sweep passed me?* — and `smoothstep` with a small `smoothing` width antialiases the sweep's leading edge (set `smoothing` to 0 for hard pixel-art edges, per §19's crispness rules). The double-`mix` composes the dimmed version (respecting `dim_color`'s alpha as dim *strength*) with the live version.

Drive `progress` 0→1 with a tween over the cooldown duration, or bind it to actual timer state each time it changes. The same shader with `dim_color` alpha at 1.0 and a solid ring texture is a radial progress *bar*; with `progress` animated by `TIME` and `fract`, a radar sweep. One angle formula, a family of UI.

> ✅ **Best practice** — For rectangular wipes, the same structure with `UV.x` (horizontal) or `UV.y` in place of `turn` gives linear progress fills — resist adding a second shader; add a `hint_enum` mode uniform (§13.6 pattern) and keep one "wipe.gdshader" for the whole UI. Cross-link: UI-level alternatives (`TextureProgressBar`) in [Scenes and Nodes](SCENES_AND_NODES.md); the shader wins when you need the effect *on arbitrary art* rather than a dedicated control.

### 15.4 Click shockwave

The last recipe closes the loop back to screen-reading: a circular distortion ripple expanding from wherever the user clicks — tactile feedback that makes the whole room feel physical. One rect, one shader, driven entirely by two uniforms.

```glsl
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear;
uniform vec2 center = vec2(0.5, 0.5);      // click position in SCREEN_UV space
uniform float progress : hint_range(0.0, 1.0) = 1.0;   // 0 = just clicked, 1 = done
uniform float max_radius : hint_range(0.0, 0.6) = 0.25;
uniform float ring_width : hint_range(0.005, 0.1) = 0.03;
uniform float strength : hint_range(0.0, 0.1) = 0.03;

void fragment() {
    // Aspect-corrected distance so the ring is circular, not elliptical.
    vec2 aspect = vec2(SCREEN_PIXEL_SIZE.y / SCREEN_PIXEL_SIZE.x, 1.0);
    vec2 to_pixel = (SCREEN_UV - center) * aspect;
    float dist = length(to_pixel);

    float radius = progress * max_radius;               // ring's current radius
    float ring = 1.0 - smoothstep(0.0, ring_width, abs(dist - radius));
    float fade = 1.0 - progress;                        // ripple weakens as it grows

    // Push the sample radially outward inside the ring band.
    vec2 dir = normalize(to_pixel + vec2(0.0001));      // guard the center singularity
    vec2 offset = dir * ring * fade * strength / aspect;

    COLOR = vec4(textureLod(screen_texture, SCREEN_UV - offset, 0.0).rgb, 1.0);
}
```

The construction, piece by piece:

- **Aspect correction** — `SCREEN_UV` is square math on a non-square screen; multiplying the offset-from-center by the pixel aspect makes `dist` isotropic, so the wave is a circle on any window shape. The final offset divides the correction back out to return to UV space.
- **The ring mask** — `abs(dist - radius)` is distance *to the ring itself*; smoothstepped against `ring_width`, it is 1 on the ring and falls to 0 within one ring-width — the same distance-to-band idiom as the shine sweep (§13.7).
- **The displacement** — pixels in the band sample the screen slightly *toward* the center (`SCREEN_UV - offset` with outward `dir`), which visually pushes the image outward: a compression wave. `fade` decays the push as the ring expands, so the wave dies naturally.
- **The singularity guard** — `normalize` of a zero vector is undefined; the epsilon nudge costs nothing and prevents a one-frame sparkle at the exact click point.

The driver connects input to uniforms and owns the lifecycle:

```gdscript
# shockwave_layer.gd — on the CanvasLayer holding the effect rect
@onready var _mat: ShaderMaterial = $ColorRect.material

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.pressed:
        var uv := event.position / get_viewport().get_visible_rect().size
        _mat.set_shader_parameter("center", uv)
        var tw := create_tween()
        tw.tween_property(_mat, "shader_parameter/progress", 1.0, 0.45)\
          .from(0.0).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
```

At `progress = 1.0` the ring has zero `fade` and displaces nothing, so the effect idles harmlessly between clicks — but per §17.1 the rect still *shades* full-screen every frame. The production refinement: `$ColorRect.visible = false` when the tween finishes, `true` when a click arrives; visibility is the only true zero-cost state. This recipe honors `reduce_motion` (§8.6) by zeroing `strength` — screen-wide distortion is on every accessibility checklist.

## 16. Visual shaders

Godot offers a node-based shader editor: create a `VisualShader` resource instead of a `Shader`, and build graphs — input nodes (`UV`, `Time`, `Texture2D`), operation nodes (`Mix`, `Step`, `VectorOp`), output node (`Fragment`'s ports). The graph compiles to the same GDShader underneath.

**Where visual shaders genuinely help:**

- **Learning and exploration.** Seeing values flow — every intermediate wire can be previewed — teaches the *dataflow* mental model of §2 faster than text for many people.
- **Artist-owned tweaking.** A technical artist who will not open a code editor can restructure a graph.
- **Live experimentation** with immediate preview per node, before committing to a final structure.

**Where they fall down, and why this course is code-first:**

- Non-trivial effects become **wire spaghetti**: the dissolve recipe (§13.4) is ~20 readable lines of code or ~30 nodes with crossing connections. Loops and arrays (Bayer matrix!) range from painful to impossible in the graph.
- **Diff/review hostility:** a `.tres` graph diff is unreadable in code review; `.gdshader` diffs read like any code, which matters for the collaborative workflow in [Game Dev Planning](GAME_DEV_PLANNING.md).
- **No includes:** the shared-helpers architecture of §5.2 has no graph equivalent; graphs duplicate logic.
- An **Expression node** exists as an escape hatch (write GDShader inside a graph node) — by the time you reach for it, you have conceded the point.

**Converting graph → code:** there is no one-click export button in the editor UI, but the compiled source is accessible — `VisualShader` *is* a `Shader` subclass, so `visual_shader.get_code()` (in a `@tool` script or the editor's script console) returns the generated GDShader text. Paste it into a `.gdshader`, rename the auto-generated identifiers, and refactor. Treat generated code as a starting sketch, not a final artifact — it is verbose and hint-free.

> ✅ **Best practice** — A defensible team policy: visual shaders for *prototyping* and for artist-owned one-offs; every effect that ships, gets parameters, or gets reused is committed as a `.gdshader` with hints and comments. This module's recipes all assume the code path.

For readers converting in either direction, the core node↔code correspondence — knowing it makes graphs skimmable even if you never build one:

| VisualShader node | GDShader equivalent |
|---|---|
| `Input` (UV, Time, Color, ScreenUV…) | The §7 built-ins (`UV`, `TIME`, `COLOR`, `SCREEN_UV`) |
| `Texture2DParameter` + `Texture2D` (sample) | `uniform sampler2D …;` + `texture(…, uv)` |
| `FloatParameter` / `ColorParameter` | `uniform float …;` / `uniform vec4 … : source_color;` |
| `Mix`, `Step`, `SmoothStep`, `Clamp` | The §4.9 function calls, one node each |
| `VectorCompose` / `VectorDecompose` | Constructors (`vec3(x, y, z)`) / swizzles (`v.x`) |
| `Expression` | An inline GDShader block — the escape hatch |
| `Output` (Fragment ports) | Writing `COLOR`, `NORMAL_MAP`, etc. |
| Wire between nodes | A named local variable |

The last row is the deep one: a graph is code where every intermediate value is anonymous *and visible*. That visibility is the pedagogic win; the anonymity is the maintenance loss.

## 17. Performance

A desktop companion is judged by a metric games rarely face: *the user's laptop fan*. Relax Room targets negligible GPU load on integrated graphics while running eight hours straight. That budget is achievable with every effect in this module — if you understand where shader cost actually comes from.

### 17.1 The cost model: fill rate and overdraw

Fragment cost ≈ **pixels shaded × cost per fragment**. The first factor dominates and is the one beginners ignore:

- A fullscreen 1920×1080 pass shades ~2.07 million fragments. Three stacked fullscreen `ColorRect` effects shade 6.2 million — *per frame*. This is **overdraw**: the same screen pixel shaded multiple times.
- Transparent sprites always pay for their full quad, including fully transparent texels — the GPU cannot know a texel's alpha without running your fragment. A 512×512 sprite that is 90% transparent padding still shades all 262,144 fragments it covers on screen. Trim sprite rects close to the art (leaving only the padding effects need, §13.1) and keep decorative layering shallow.
- Scaling *up* multiplies cost: the same 64×64 sprite at 4× scale covers 16× the fragments. Full-screen effects cost by *window* size, not design resolution — a user maximizing the companion on a 4K display quadruples your 1080p budget. Where the architecture allows, render the world at design resolution in a `SubViewport` and post-process *that*, then upscale (§10.5, [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md)).

Overdraw is visible if you ask for it. A two-minute diagnostic: temporarily assign every large transparent layer a debug material with `render_mode blend_add;` and `COLOR = vec4(0.1, 0.0, 0.0, 1.0);` — the screen becomes a heat map where brighter red literally *is* more layers shading the same pixel. (The 3D editor has a built-in overdraw view; 2D earns the same insight with this three-line shader.) Any region glowing past dull red deserves a look at its layer stack.

### 17.2 Texture fetches

Per-fragment cost is mostly **texture sampling**, not arithmetic. Modern GPUs chew through hundreds of math ops per fetch-latency window. Consequences:

- Count your taps: the 8-direction outline does 9 fetches/fragment; a naive 9×9 box blur does 81. The two-pass separable blur (§11.3) does 9 + 9 = 18 for the same result — *this* is why multi-pass exists.
- **Dependent reads** (a fetch whose coordinates come from another fetch — dissolve's noise, rain distortion) defeat the texture prefetcher and cost more than their count suggests. One dependent hop is fine; chains of them are where "it's just a texture read" dies.
- Mipmapped `textureLod` on the screen texture (§11.1) is the cheapest blur in the engine — the mip chain is amortized; exploit it before writing kernel loops.

### 17.3 Branching: the myth, calibrated

Restating §2.2 as performance guidance: branches on **uniforms** are free (the compiler often specializes them); branches on **per-pixel data** cost both sides *only where a warp diverges* — a screen-region branch (bezel vs tube in the CRT, §14.2) diverges only along the boundary and is effectively free; a per-pixel noise branch (`discard` in dissolve) diverges everywhere mid-effect and pays. The modern rule: **write it clearly first**. `mix`/`step` micro-transformations of readable `if`s are justified only by a measured win, with one exception — never gate a *texture fetch* behind a divergent branch expecting to save the fetch; the warp likely fetches anyway.

### 17.4 Measuring, not guessing

- **Godot profiler → Visual Profiler tab** (debugger panel): GPU time per rendering stage while the game runs. Your effect's cost is the delta with the effect toggled — this is why every effect gets a kill switch (§11.3).
- `RenderingServer.viewport_set_measure_render_time(viewport_rid, true)` then `viewport_get_measured_render_time_gpu()` / `_cpu()` — per-frame numbers you can log or graph in a debug overlay; ideal for the before/after harness in the exercises.
- **Monitors** (Debugger → Monitors): draw-call and primitive counts reveal batching breaks (per-node duplicated materials show up here — the §8.5 instance-uniform argument, in graph form).
- Test on the **Compatibility renderer** and on integrated GPUs — the machines Relax Room actually runs on. A Vulkan-tuned discrete GPU hides sins.

A minimal measuring harness worth keeping in every project — the one Lab 8 builds on:

```gdscript
# gpu_meter.gd — debug overlay; add to the main scene in debug builds only
extends Label

func _ready() -> void:
    var vp := get_viewport()
    RenderingServer.viewport_set_measure_render_time(vp.get_viewport_rid(), true)

func _process(_delta: float) -> void:
    var rid := get_viewport().get_viewport_rid()
    var gpu_ms := RenderingServer.viewport_get_measured_render_time_gpu(rid)
    var cpu_ms := RenderingServer.viewport_get_measured_render_time_cpu(rid)
    text = "GPU %.2f ms · CPU %.2f ms" % [gpu_ms, cpu_ms]
```

Toggle each effect while watching the GPU number; write the deltas down. Numbers beat adjectives: "the CRT filter costs 0.21 ms at 1080p on the 2019 test laptop" is an engineering fact; "shaders are slow" is a mood.

And the summary cost intuition, as a cheat sheet (orders of magnitude, not gospel — measure yours):

| Action | Rough relative cost |
|---|---|
| Arithmetic op (`mix`, `dot`, `*`) | 1× |
| Transcendental (`sin`, `pow`, `atan`) | ~2-4× |
| Texture fetch, cache-friendly | ~10-30× |
| Dependent texture fetch | ~30-80× |
| Full-screen pass at 1080p | ~2 M fragments × the above |
| Extra render target (CanvasGroup, SubViewport, BackBufferCopy) | one full write + read of its pixels |
| Pipeline compilation (first use, unwarmed) | *milliseconds* — a visible hitch (§17.5) |

### 17.5 Shader compilation stutter and pre-warming

The first frame that needs a pipeline (shader + render state combination) may compile it *on the driver, synchronously* — the infamous first-use hitch. Godot 4.4+ attacks this with **ubershaders**: on Forward+/Mobile (Vulkan, D3D12, Metal), a generic specialization-constant-driven pipeline is precompiled at load (during mesh/resource load and scene-tree entry), used immediately, and quietly replaced by an optimized specialization compiled in the background. Practical rules that survive contact with this system:

- **Instantiate materials at load time, not first-use time.** A material first assigned mid-session (the classic: equipping an effect on first click) can still hit the *draw-time* compilation path. Keep a hidden warm-up node using every runtime-assigned material, or assign materials in `_ready` and toggle `visible` instead.
- On the **Compatibility renderer** there are no ubershaders — pre-warm by *actually drawing* each material once behind a loading screen (an offscreen 1×1 quad per material works).
- Watch the **pipeline compilation monitors** in the debugger: compilations counted under "Surface"/draw during gameplay are the stutters users will feel; move them to load.
- Changing a *uniform* never recompiles anything; changing a material's *shader* (or toggling features that change render state) can. Prefer mode uniforms (§13.6) over shader swapping at runtime.

### 17.6 Mobile vs desktop, briefly

Should the companion ever target mobile: tile-based mobile GPUs make overdraw and back-buffer copies disproportionately expensive (`hint_screen_texture` forces a tile flush), `mediump` precision (§4.4) becomes a real optimization *and* a real bug source, and alpha-blended fullscreen rects are the first thing to cut. The desktop advice in this module is a *superset* — everything here works on mobile, just with tighter multipliers.

## 18. Debugging shaders

No `print`, no breakpoints, no stack traces — shader debugging is its own discipline with three tools: **compiler errors**, **output-color probes**, and **bisection**.

### 18.1 Reading compile errors

The shader editor compiles as you type; errors appear inline and in the panel below. The frequent offenders, decoded:

| Error text (abridged) | Actual meaning |
|---|---|
| `Invalid arguments to operator '*' ('float' and 'int')` | Missing decimal point — `x * 2` → `x * 2.0` (§4.2, the #1 error). |
| `Expected expression, found ';'` / `Expected ';'` | Usually the *previous* line — a missing semicolon or an unclosed parenthesis upstream. Read one line above the marker. |
| `Unknown identifier in expression: 'SCREEN_TEXTURE'` | Godot 3 built-in in Godot 4 code — declare `hint_screen_texture` uniform instead (§11.1). Same class of error: any built-in used in the wrong stage/type (§6.1). |
| `Function 'texture' not found for given arguments` | Wrong argument types — commonly passing `UV` where a `sampler2D` goes, or a vec3 UV to a 2D sampler. |
| `Varying may not be assigned in the 'fragment' function` | Varying written in the wrong stage (§9). |
| `Global uniform '…' not found in Project Settings` | The `global uniform`'s name is missing from Shader Globals (§8.6). |
| `Redefinition of '…'` | Name collision — often a uniform re-declared in an included `.gdshaderinc` (add include guards, §5.2). |

A broken *3D* material renders as the loud error-magenta checker; a failing **canvas_item** shader typically renders the node with the *default* shader or not at all — quieter, so in 2D your habit must be: **any visual anomaly → check the shader editor's error panel first**. It is never wrong; a shader with a red line is not running your code at all.

### 18.2 Output-color probes

The shader equivalent of `print` is *writing the suspect value to the screen* and reading it with your eyes:

```glsl
void fragment() {
    vec4 base = texture(TEXTURE, UV);
    float mask = compute_suspicious_mask(base, UV);

    // PROBE: visualize the mask as grayscale — comment out the real output.
    COLOR = vec4(vec3(mask), 1.0);
    // COLOR = final_effect(base, mask);
}
```

The standard probe kit:

- `COLOR = vec4(UV, 0.0, 1.0);` — UV sanity: must show a black→red gradient left-to-right, black→green top-to-bottom. Anything else means your UVs are transformed, flipped, or you are on a node whose UV space differs from your assumption (a `ColorRect`'s UV covers the rect; a `TileMapLayer`'s covers each tile).
- `COLOR = vec4(vec3(value), 1.0);` — any scalar as grayscale. If the screen is all black or all white, your value's *range* is wrong (a classic: an angle in -PI..PI probed without remapping).
- `COLOR = vec4(value * 0.5 + 0.5, 0.0, 1.0);` — signed scalars remapped to visible range.
- Channel isolation: `COLOR = vec4(base.aaa, 1.0);` shows the alpha channel that outline/shadow logic depends on — revealing, e.g., that your "transparent" padding is actually alpha 0.004 from an import artifact.
- Temporal probes: `COLOR = vec4(vec3(fract(TIME)), 1.0);` — confirms the shader is *live and updating* (diagnoses the "editing the wrong file / wrong material" class of confusion in one look).

Bisect with probes exactly like you would with `print`: probe halfway through the computation; if the intermediate is right, move the probe later; wrong, earlier. Three probes locate any bug in a 30-line shader.

Codify the kit as an include so probing is one line, not five minutes of retyping:

```glsl
// debug_probes.gdshaderinc
#ifndef DEBUG_PROBES_INC
#define DEBUG_PROBES_INC

// Scalar as grayscale; out-of-range values tinted (red = negative, blue = >1).
vec4 probe(float v) {
    if (v < 0.0) { return vec4(1.0, 0.0, 0.0, 1.0); }
    if (v > 1.0) { return vec4(0.0, 0.0, 1.0, 1.0); }
    return vec4(vec3(v), 1.0);
}

// vec2 as red/green (UV convention).
vec4 probe2(vec2 v) { return vec4(v, 0.0, 1.0); }

// Signed scalar remapped: gray = 0, black = -1, white = +1.
vec4 probe_signed(float v) { return vec4(vec3(v * 0.5 + 0.5), 1.0); }

#endif
```

The out-of-range tinting in `probe()` earns its lines: half of all "the mask looks wrong" bugs are range bugs, and a screen going red or blue diagnoses them faster than staring at gray. Use as `COLOR = probe(mask);` — and grep for `probe(` before committing; shipped probes are this discipline's forgotten-`print` equivalent.

### 18.4 A debugging decision tree

The full workflow, linearized — follow it top to bottom and most shader bugs fall out in under five minutes:

1. **Error panel red?** Fix the *first* error only, recompile, repeat. Later errors are usually cascades of the first (§18.1).
2. **Compiles, but no visible effect?** Probe liveness: `COLOR = vec4(1.0, 0.0, 1.0, 1.0);` as line one of `fragment()`. Not magenta? You are editing the wrong file, the wrong material, or the node's material slot is empty — a *workflow* bug, not a shader bug (§10.2).
3. **Magenta shows, effect doesn't?** Probe inputs: `UV`, then each uniform (`COLOR = probe(my_uniform);`) — a defaulted uniform means the GDScript side never reached this material (misspelled name §8.3, shared-vs-duplicated material §10.2, instance vs regular parameter call §8.5).
4. **Inputs right, output wrong?** Bisect the computation with probes (§18.2).
5. **Right on your machine, wrong elsewhere?** Renderer difference (Compatibility vs Forward+ — check the §5.3 defines), missing HDR 2D (§14.4), precision (§4.4), or pipeline warm-up (§17.5) — in that order of likelihood.

### 18.3 Editor live-edit workflow

The fast loop that makes shader work pleasant: dock the shader editor beside the 2D viewport; every save (or keystroke, for the built-in editor) hot-reloads the shader on all materials using it — with the scene *running* via the "Run current scene" button, you edit effects against live animation. Combine with: **Inspector sliders** on hinted uniforms for hands-on parameter search (then bake the found values as defaults into the shader); a dedicated `shader_lab.tscn` scene containing one sprite, one `ColorRect`, checkerboard and gradient test textures — your workbench for every new recipe, kept out of the main scene's way; and `File → Save As` on a duplicate material when A/B-comparing two parameter sets.

The workbench scene, since every lab uses it — build it once:

```
shader_lab.tscn
 ├─ TextureRect "Checker"     checkerboard.png — reveals UV/filter bugs instantly
 ├─ TextureRect "Gradient"    horizontal black→white ramp — reveals range/banding bugs
 ├─ Sprite2D  "Subject"       a real game sprite — the material under test goes here
 ├─ Sprite2D  "SubjectScaled" same sprite at 3× — catches resolution-dependent bugs
 ├─ PointLight2D (disabled)   enable when testing light() stages
 └─ CanvasLayer
     └─ ColorRect "Post"      Full Rect, mouse_filter Ignore — full-screen shader slot
```

Two test textures do disproportionate work: the checkerboard turns any unintended filtering or UV distortion into an unmissable pattern break, and the gradient makes quantization effects (palette §13.5, dither §14.3) verifiable by eye against known input values.

For deeper GPU forensics (what did the back-buffer actually contain? which pipeline ran?), **RenderDoc** captures a Godot frame like any Vulkan/GL app — outside this module's scope, but know the name for the day a driver-specific artifact appears only on one machine.

## 19. Pixel-art shader craft and the Relax Room

Pixel art is a contract: *every visible pixel is a deliberate, grid-aligned, palette-colored decision*. Shaders can silently break all three clauses. This section is the checklist that keeps effects on-contract, and how the module's recipes assemble into the running case study.

### 19.1 Filtering: the grid's first line of defense

As established in [Sprites and Textures](SPRITES_AND_TEXTURES.md), pixel art imports with **nearest** filtering (project default `rendering/textures/canvas_textures/default_texture_filter = Nearest`, or per-node). Shaders add three new places where linear filtering sneaks back in:

1. **Sampler uniform hints** — every `sampler2D` uniform you add (noise, palette, LUT) has its *own* filter state; declare `filter_nearest` explicitly (§8.2). An unhinted sampler follows the node/project default, which is right for Relax Room but wrong the day someone reuses your shader elsewhere. Hint it always.
2. **The screen texture** — `hint_screen_texture, filter_nearest` for crisp reads; `filter_linear`(+mipmap) only when the effect *wants* softness (blur, water).
3. **Sub-texel UV math** — even with nearest filtering everywhere, an offset like `UV + 0.5 * TEXTURE_PIXEL_SIZE` samples *between* art pixels; nearest filtering then picks one side per screen pixel, producing ragged edges. Offsets in whole texels only: `UV + vec2(1.0, 0.0) * TEXTURE_PIXEL_SIZE`.

### 19.2 Snapping in the shader

When an effect must move things (wave, shake, scrolling), the pixel grid demands **quantized motion**. The general tool is snapping any computed offset to whole texels:

```glsl
// pixel_utils.gdshaderinc
vec2 snap_to_texel(vec2 uv_offset, vec2 texel) {
    return floor(uv_offset / texel + 0.5) * texel;   // round to nearest whole texel
}
```

```glsl
// Waving curtain, grid-respecting version of §15.1 Variant A:
float raw = sin(UV.x * frequency + TIME * speed) * amplitude * pin;
vec2 offset = snap_to_texel(vec2(0.0, raw), TEXTURE_PIXEL_SIZE);
vec4 col = texture(TEXTURE, UV + offset);
```

The wave now advances in discrete one-texel steps — staircase motion that *matches* the art style instead of smearing across it. The same snap in `vertex()` (`VERTEX = floor(VERTEX + 0.5);` as the last line) kills **sub-pixel shimmer** on vertex-animated geometry: without it, a vertex at y = 10.5 makes the rasterizer's coverage flicker between rows as the fraction drifts, reading as edge crawl. Note the interaction with camera zoom: snapping to *texels* is correct when the game renders at design resolution and upscales (integer-scaled `SubViewport`); if instead nodes scale arbitrarily on a native-resolution canvas, snap to *screen pixels* (`SCREEN_PIXEL_SIZE`) — the two strategies disagree precisely when your scaling architecture is inconsistent, which is itself the bug to fix first ([Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md)).

The other grid rules recap themselves from the recipes: **hard thresholds over smooth ones** (`step` not `smoothstep`, `smoothing = 0.0` in the radial wipe §15.3) so effect edges are as crisp as art edges; **effect resolution = art resolution** (dissolve noise sized to the sprite, §13.4; scanline count matched to design resolution, §14.2); **palette discipline** — tints and grades produce off-palette colors by construction, so either constrain effects to palette-preserving operations (palette swap §13.5, ordered dithering §14.3) or explicitly accept a "lighting layer" of off-palette colors as art direction (day-night tint §14.5 chooses acceptance; the module's DMG mode chooses constraint).

Condensed into the pre-ship checklist — run it once per effect, against the exported build:

- [ ] Every sampler uniform declares `filter_*` and `repeat_*` explicitly (§19.1).
- [ ] All UV offsets are whole-texel multiples of `TEXTURE_PIXEL_SIZE`; all animated offsets snapped (§19.2).
- [ ] Effect edges use `step`/zero-width `smoothstep` unless softness is an explicit art call.
- [ ] Auxiliary textures (noise, LUT, masks) match the art's resolution and import with mipmaps off.
- [ ] Screenshot at 1× and 3× integer scale: no effect pixel is a different size than an art pixel.
- [ ] Effect colors either come from the palette or are documented as the lighting layer.
- [ ] Motion effects checked against `reduce_motion`; flicker/flash amplitudes within accessibility limits (§14.2).

### 19.3 The Relax Room shader stack

Assembled from this module's recipes, the case study's complete shader inventory — a realistic production loadout for a polished 2D companion:

| Layer | Node | Shader (recipe) | Driven by |
|---|---|---|---|
| Post 3 (top) | `ColorRect` on `CanvasLayer` 102 | Bayer dithering §14.3 — optional "retro" setting | Settings toggle |
| Post 2 | `ColorRect` on `CanvasLayer` 101 | CRT §14.2 — optional | Settings toggle, `reduce_motion` global |
| Post 1 | `ColorRect` on `CanvasLayer` 100 | Grade: grayscale-away §13.6 + day-night §14.5 (merged via includes) | `day_phase` global, presence state |
| Scene FX | Water `ColorRect` | Reflection §15.2 | `TIME` |
| Scene FX | Window rect | Rain distortion §11.4 | Weather state uniform |
| Pet | `CanvasGroup` (pet + accessories) | Outline §13.1 + hit-flash §13.2 (one shader, two uniforms) | Hover signal → tween; click → tween |
| Furniture | Shared material, per-node **instance uniforms** | Tint + flash §8.5 | Interaction scripts |
| Lamp/candle | Sprite materials | Glow emitters §14.4 | `TIME` pulse §12.3 |
| Plants | Shared material, `world_vertex_coords` | Grass wind §15.1-C | `game_time` global |
| Gift chest | Sprite material | Shine sweep §13.7 | `TIME`, daily flag uniform |
| Input feedback | `ColorRect` on `CanvasLayer` 99 | Click shockwave §15.4 | `_unhandled_input` → tween |
| Transitions | Any despawning item | Dissolve §13.4 | Tween → `queue_free()` |

Total: nine shaders, three global uniforms, zero per-frame GDScript beyond the two autoload writers (`day_phase`, `game_time`). Every optional layer has a kill switch; the whole stack profiles under a millisecond of GPU time at 1080p on integrated graphics — the standing proof that "shaders everywhere" and "laptop-friendly" are compatible claims when §17's rules are followed. The [Project Deep Dive](PROJECT_DEEP_DIVE.md) module walks this exact scene tree; [Visual Systems Summary](VISUAL_SYSTEMS_SUMMARY.md) places the stack alongside particles and animation in the broader visual architecture.

## Best practices

**Language and structure**

1. **One effect, one `.gdshader`; shared helpers in `.gdshaderinc` with include guards** (§5.2). Copy-pasted `luminance()` across five shaders is technical debt with a compile step.
2. **Hint every uniform**: `source_color` on colors (non-negotiable — §8.2), `hint_range` on scalars, explicit `filter_*`/`repeat_*` on every sampler. Hints are the effect's documentation *and* its artist UI.
3. **Float literals get decimal points.** Write `2.0`, `0.5`, `1.0` reflexively; `* 2` is the module's most common compile error.
4. **Preserve alpha deliberately.** End fragment logic by reassembling `vec4(rgb, base.a)` — effects that "leak" outside the silhouette almost always forgot whose alpha they shipped.
5. **Respect or bypass modulate consciously**: start from `COLOR` to compose with the pipeline, from `texture(TEXTURE, UV)` to see raw art (§7.3). Comment which and why.

**Architecture**

6. **The variation ladder** (§10.2): instance uniforms → `duplicate()` → `resource_local_to_scene`. Never per-frame material creation; never editing a shared material believing it is private.
7. **Globals for world state, uniforms for effect knobs, instance uniforms for per-node state** (§8.6). Three tiers, no exceptions, and the tier is visible in the declaration.
8. **Every full-screen effect ships with a kill switch and a `strength` uniform** (§11.3) — for settings, accessibility, and performance triage alike.
9. **Animate uniforms with tweens/AnimationPlayer via `shader_parameter/*` paths**, `TIME` for perpetual motion (§12.2). No `_process` polling for either.
10. **Warm every runtime-assigned material at load** (§17.5); change modes with uniforms, not shader swaps.

**Craft**

11. **Whole-texel offsets and snapped motion on pixel art** (§19.1-19.2); hard edges unless softness is the point.
12. **Probe with colors, bisect, and trust the error panel** (§18) — a red line means your code is not running at all.
13. **Profile with the effect toggled, on the weakest target hardware** (§17.4). The delta is the truth; everything else is folklore.

**Project layout** — the directory convention the recipes assume, worth standardizing on day one:

```
res://shaders/
 ├─ common/     # .gdshaderinc only: color_utils, pixel_utils, dither, fx_lib, debug_probes
 ├─ fx/         # per-sprite effects: outline.gdshader, dissolve.gdshader, …
 ├─ post/       # full-screen passes: crt.gdshader, dither_screen.gdshader, grade.gdshader
 └─ lab/        # experiments and probes — never referenced by shipping scenes
```

The `lab/` quarantine matters most: experiments referenced from a real scene become load-bearing by accident, and a `.gdshader` is invisible to "unused asset" intuition because nothing imports it — only materials reference it. A quarterly grep of `res://shaders/lab/` against scene files keeps the boundary honest.

## Common errors & troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Node renders magenta/pink (3D) or falls back to default look (2D) | Shader failed to compile — it is not running at all | Open the shader in the editor; fix the first error listed (§18.1). In 2D, always check the error panel before debugging visuals |
| `Invalid arguments to operator` compile error | Int literal in float math (`x * 2`) | Add the decimal point: `x * 2.0`; convert explicitly with `float()` / `int()` (§4.2) |
| `Unknown identifier 'SCREEN_TEXTURE'` (or `LIGHT` in `fragment()`, etc.) | Godot 3 built-in, or right built-in in wrong stage/shader type | Declare `uniform sampler2D t : hint_screen_texture;` (§11.1); check the stage tables in §7 |
| Effect ignores `set_shader_parameter` calls | Misspelled uniform name (silent no-op), or setting a different material instance than the one rendering | Diff the string against the declaration; verify with `get_shader_parameter`; confirm which material the node holds (§8.3, §10.2) |
| Changing one node's uniform changes many nodes | Shared `ShaderMaterial` resource | Instance uniforms (4.4+), `material.duplicate()`, or `resource_local_to_scene` (§10.2) |
| Outline / drop shadow / wave clipped at sprite edge | No transparent padding — fragments cannot exist outside the quad | Add padding to the texture, or grow geometry in `vertex()` (§2.3, §13.1, §13.3) |
| Sprite ignores `modulate` since the shader was added | `fragment()` starts from `texture(TEXTURE, UV)`, discarding the pipeline's `COLOR` | Start from `COLOR`, or multiply modulate back in deliberately (§7.3) |
| Colors look washed out / too dark, but only in some renderers | Color uniform missing `source_color` (no color-space conversion) | Add the hint to every color uniform and color texture (§8.2) |
| `screen_texture` samples black/empty | Read before anything drew beneath it (layer/draw order); rect-mode `BackBufferCopy` smaller than sampled area; sampling with mipmap filter but plain `texture()` | Fix `CanvasLayer` ordering so content draws first; grow the copy rect (§11.2); use `textureLod(…, 0.0)` (§11.1) |
| Two overlapping distortion effects ignore each other | Both read the same pre-copy back-buffer | Insert a `BackBufferCopy` between them (§11.2), or merge into one shader |
| Full-screen effect works in editor, missing in export | HDR 2D off in export, Compatibility renderer fallback on target machine, or effect layer culled by a different window size | Verify project settings ship correctly; log `RenderingServer.get_current_rendering_method()` in debug; test the export on min-spec (§14.4, [Build and Export](BUILD_AND_EXPORT.md)) |
| Post-processing rect blocks all mouse input | `ColorRect` default `mouse_filter` swallows events | Set `mouse_filter = Ignore` on every effect rect (§11.3) |
| Effect stutters once on first use | Draw-time pipeline compilation | Warm materials at load; keep a hidden warm-up node; monitor pipeline compilations (§17.5) |
| Shader animation freezes/jumps after hours of uptime | `TIME` rollover (default 3600 s) with unbounded accumulation, or float precision loss | Use wrapping math (`fract`/`sin`); custom `game_time` global with `fmod` (§12.1) |
| Effects keep animating while game is paused | `TIME` ignores pause and `time_scale` by design | Drive pause-respecting effects from a `game_time` global updated in `_process` (§12.1) |
| Pixel art looks blurry/smeared under an effect | Linear filtering on a sampler uniform or screen texture; sub-texel UV offsets | `filter_nearest` hints everywhere intended; whole-texel offsets; snap motion (§19.1-19.2) |
| Dither/scanline pattern shows as blocks or moiré | Pattern applied at design resolution then upscaled, or scanline count mismatched to resolution | Apply screen-space patterns at native resolution; match `scanline_count` to design height (§14.2-14.3) |
| Varying reads as zero in `fragment()` | Never assigned — `vertex()` missing or misnamed, so it compiled as dead code | Confirm the exact `void vertex()` signature assigns it (§9) |
| Instance uniform has no effect | Set with `set_shader_parameter` instead of `set_instance_shader_parameter`; or running a pre-4.4 Godot where 2D instance uniforms don't exist | Use the instance API (§8.5); verify engine version ≥ 4.4 |
| Uniform array silently ignores assignment | Array length mismatch with the declared size, or wrong packed-array type | Match `N` exactly; use the §8.3 type table |
| Circular effect renders as an ellipse | Math done in raw `SCREEN_UV` without aspect correction | Multiply center-relative coordinates by the pixel aspect (§15.4) |
| `CanvasGroup` effect double-applies or children look wrong | Children carry their own conflicting materials, or blend modes inside the group fight the group's compositing | Keep effect materials on the group, not the children; audit child `blend_*` modes (§10.3) |
| Vertex-wave shader does nothing on a Sprite2D | Only four vertices to displace — linear deformation between corners | Use fragment UV distortion, or subdivided `MeshInstance2D`/`Polygon2D` geometry (§15.1) |

## Exercises

The original module's three labs survive as Labs 1, 2, and 6 — each expanded with acceptance criteria. Build all labs inside a dedicated `shader_lab.tscn` workbench scene (§18.3), then port survivors into your project.

1. **Lab — outline shader.** Apply the §13.1 outline to a character sprite with uniform-controllable color and thickness; upgrade to 8 directions.
   *Acceptance criteria:* outline appears on hover and disappears on exit via a tween on `thickness` (no material swap); diagonal edges show no gaps; sprite has documented padding; works at 1× and 4× node scale without thickness drift.
   *Stretch:* apply to a `CanvasGroup` of pet + accessory and demonstrate the single merged silhouette vs the per-sprite version in a side-by-side screenshot.

2. **Lab — animated shader via TIME.** A pulsing glow on hover using `sin(TIME * speed)` shaped by the easing techniques of §12.3.
   *Acceptance criteria:* pulse uses `TAU`-based phase (no magic 6.28…); an exponent uniform switches "metronome" vs "breathing" character; effect fully stops (not just invisible) when disabled.
   *Stretch:* make it pause-respecting by switching the clock source to a `game_time` global — demonstrate both behaviors with the scene tree paused.

3. **Lab — hit-flash with instance uniforms.** Implement §13.2 across five sprites sharing **one** material.
   *Acceptance criteria:* clicking any sprite flashes only that sprite; the debugger Monitors show no additional draw-call cost vs the shared-material baseline; `flash_amount` returns to exactly 0.0 (verify with `get_instance_shader_parameter`).
   *Stretch:* an "all flash" panic button that tweens all five with staggered 50 ms delays.

4. **Lab — dissolve despawn.** Wire §13.4 to a despawn flow: tween `progress` 0→1, `await` completion, `queue_free()`.
   *Acceptance criteria:* sprite is fully gone at `progress = 1.0` (no ghost edge band); noise texture resolution matches sprite resolution with `filter_nearest`; no dissolved-but-alive nodes remain (verify node count in the remote tree).
   *Stretch:* reverse the tween for a *spawn* effect, and add a `direction_bias` uniform that makes the dissolve sweep bottom-up by blending a UV gradient into the noise.

5. **Lab — palette-swap day cycle.** Combine §13.5's LUT with §14.5's `day_phase` global: furniture palettes crossfade between day and night strips as the clock advances.
   *Acceptance criteria:* palettes are committed `.png` strips; sampling shows no edge bleed at brightness 0.0 or 1.0 (probe with a black-to-white gradient test texture); changing the OS clock changes the room within one frame.
   *Stretch:* three palettes (day/dusk/night) with the two-window blending pattern from §14.5.

6. **Lab — CRT stack.** The original stretch goal, now in full: combine scanlines + curvature + RGB shift (§14.2) as a full-screen `CanvasLayer` effect.
   *Acceptance criteria:* every stage individually zeroable from a settings panel; settings UI renders on a layer *above* the effect (readable while CRT is active); `mouse_filter` correctly set (all UI clickable); `reduce_motion` global zeroes curvature and RGB shift.
   *Stretch:* add §14.3's Bayer dithering as a separate layer above it and produce three screenshots: clean / CRT / CRT+dither at `color_levels = 2` with a DMG palette.

7. **Lab — screen-reading water.** Implement §15.2 over a scene with moving elements.
   *Acceptance criteria:* reflection tracks moving sprites live; waterline is uniform-adjustable at runtime; an element on a higher `CanvasLayer` demonstrably does *not* reflect — include a one-paragraph explanation of why, citing back-buffer copy order.
   *Stretch:* insert a `BackBufferCopy` so a distortion effect *behind* the water is included in the reflection, and measure the added GPU cost with `viewport_get_measured_render_time_gpu()`.

8. **Lab — performance harness.** Build a debug overlay showing GPU frame time (§17.4) with keys toggling each effect from the §19.3 stack.
   *Acceptance criteria:* per-effect GPU deltas measured and recorded in a table at 1080p; the full stack stays under your chosen budget on your weakest available machine; one deliberate pessimization (e.g., 81-tap single-pass blur) measured against its separable version with the numbers written up.
   *Stretch:* demonstrate first-use stutter — a material assigned on first click vs pre-warmed at load — and capture the frame-time spike difference in the profiler.

9. **Lab — interaction pair: magnifier + shockwave.** Implement §11.5 and §15.4 together: right-drag moves the lens; left-click ripples.
   *Acceptance criteria:* lens stays circular at three different window aspect ratios (aspect correction verified); `radius_uv` updates on window resize; shockwave rect is `visible = false` between clicks (verify via remote tree); neither effect consumes input meant for the scene (`mouse_filter` / `_unhandled_input` discipline).
   *Stretch:* make the shockwave respect `reduce_motion` by zeroing `strength` — and prove it with a settings toggle demo.

10. **Lab — the include library refactor.** Extract every helper duplicated across your Labs 1-9 shaders into `res://shaders/common/` include files (`color_utils`, `pixel_utils`, `dither`, `debug_probes`).
    *Acceptance criteria:* all include files carry `#ifndef` guards; every lab shader still compiles and renders identically (screenshot diff); no helper function is defined in more than one file; a new "sepia + outline" shader is written in under 15 lines by composing includes.
    *Stretch:* add a renderer-detection `#if` (§5.3) that degrades one effect gracefully on the Compatibility renderer, and verify by switching renderers.

### Self-check questions

Answer from memory, then verify against the cited section — the original module's five questions, grown to twelve:

1. `canvas_item` vs `spatial`: what exactly does the first line of a shader decide? (§6.1)
2. Where does `TIME` come from, when does it roll over, and what does it ignore? (§12.1)
3. Shader vs tween: state the granularity criterion in one sentence. (§12.2)
4. Why does bilinear filtering break pixel art, and name the three places filtering hides in a shader workflow. (§19.1)
5. Is a texture sample cheap or expensive relative to arithmetic — and what makes a *dependent* read worse? (§17.2)
6. Two sprites share a `ShaderMaterial`; you set a uniform on one. What happens, and name the three-rung remediation ladder. (§10.2)
7. Why must a color uniform carry `source_color`? What is the symptom if it doesn't? (§8.2)
8. Write from memory the Godot 4 declaration that replaces Godot 3's `SCREEN_TEXTURE`. (§11.1)
9. When is an `if` in a fragment shader essentially free, and when does it cost both branches? (§2.2)
10. A varying reads as zero in `fragment()` — name the two most likely causes. (§9)
11. What is an ubershader, which renderers use it, and what does it buy you? (§17.5)
12. Your effect works in the editor but not in the exported build — list the first three hypotheses to test, in order. (§14.4, §17.5, troubleshooting table)

## Further reading

Official documentation first — these are the pages this module was verified against:

- **Godot Docs — Shading language** (docs.godotengine.org → Shaders → Shader reference): the normative grammar — types, precision, arrays, uniforms, hints, varyings. When this module and your memory disagree, this page wins.
- **Godot Docs — CanvasItem shaders**: the built-ins tables of §7 in their canonical form, including additions in point releases. Bookmark; consult per new built-in.
- **Godot Docs — Shader preprocessor**: directives, `.gdshaderinc` rules, renderer defines (§5.3).
- **Godot Docs — Screen-reading shaders** and **Custom post-processing**: back-buffer mechanics, `BackBufferCopy`, the `CanvasLayer` + `ColorRect` pattern, multi-pass (§11).
- **Godot Docs — Your first 2D shader / Your second 2D shader**: the official gentle on-ramp; useful as a second telling of §4 and §7 with different examples.
- **Godot Docs — Pipeline compilations** (Performance section): the ubershader/precompilation model behind §17.5.
- **godotshaders.com**: community shader library — hundreds of canvas_item effects with source. Read critically: quality varies, many entries predate 4.x syntax (watch for `SCREEN_TEXTURE`), but it is the best "how did others approach this effect" index in the ecosystem.
- **The Book of Shaders** (Vila & Lowe): the finest conceptual text on fragment-shader thinking — shaping functions, randomness, noise, patterns. GLSL-based; port examples using the §3 substitution table. Read chapters 5-12 after finishing this module and the cookbook recipes will reorganize themselves in your head into a smaller set of primitives.
- **Inigo Quilez — articles** (iquilezles.org): the field's reference collection for distance functions, gradients, and shader math tricks; 3D-slanted but the 2D SDF material powers advanced outline/glow/shape work beyond this module.
- **Godot Docs — 2D lights and shadows**: the scene-side counterpart to §6.3/§7.4 — `PointLight2D`, `DirectionalLight2D`, occluders, and shadow settings that your `light()` functions plug into.
- **Shadertoy** (shadertoy.com): the largest live-editable fragment-shader gallery. Everything is raw GLSL against `mainImage` — port with the §3 substitution table. Best used as a *reading* gym: pick a small effect, predict each line's output, verify with the built-in editor.

Course-internal follow-ups: [Visual Systems Summary](VISUAL_SYSTEMS_SUMMARY.md) situates shaders among particles, lights, and animation; [Desktop Companion Performance](DESKTOP_COMPANION_PERFORMANCE.md) owns the frame-budget methodology that §17 plugs into; the [Capstone](00-CAPSTONE.md) requires at least four cookbook recipes integrated and profiled.

## Glossary

| Term | Definition |
|---|---|
| **GDShader** | Godot's shading language — a GLSL ES 3.0 dialect with `shader_type`, `render_mode`, hints, and engine built-ins (§3). |
| **`shader_type canvas_item`** | Declares a 2D-pipeline shader for any `CanvasItem` (§6.1). |
| **`shader_type spatial`** | 3D-pipeline shader; different built-ins, out of this module's scope (§6.1). |
| **Fragment** | One shaded pixel candidate; `fragment()` runs once per fragment (§2.1). |
| **`vertex()` / `fragment()` / `light()`** | The three optional stage functions of a canvas_item shader: geometry, per-pixel color, per-light contribution (§2.1, §7). |
| **Built-in** | Engine-provided stage variable (`UV`, `COLOR`, `TIME`…) — read-only or writable per the §7 tables. |
| **`TIME`** | Engine clock in seconds; rolls over (default 3600 s); ignores pause and `time_scale` (§12.1). |
| **`UV`** | Normalized texture coordinate, 0-1 across the node's texture (§7.2-7.3). |
| **`COLOR`** | In `fragment()`: incoming pipeline color and the output you write (§7.3). |
| **`TEXTURE` / `TEXTURE_PIXEL_SIZE`** | The node's own texture sampler, and one texel's size in UV units — the key to neighbor sampling (§7.3). |
| **`FRAGCOORD` / `SCREEN_UV` / `SCREEN_PIXEL_SIZE`** | Screen-space position in pixels; as 0-1 UV; and one screen pixel in UV units (§7.3). |
| **Uniform** | Shader parameter, constant per draw, set from Inspector/GDScript via `set_shader_parameter` (§8). |
| **Hint** | Uniform annotation (`source_color`, `hint_range`, `filter_nearest`…) controlling editor UI and sampler behavior (§8.2). |
| **Instance uniform** | Per-node uniform value on a shared material; canvas_item support since Godot 4.4; max 16, no samplers/arrays (§8.5). |
| **Global shader uniform** | Project-wide uniform declared in Project Settings, set via `RenderingServer.global_shader_parameter_set` (§8.6). |
| **Varying** | Value written per-vertex, interpolated per-fragment; `flat` disables interpolation (§9). |
| **`ShaderMaterial`** | Resource pairing a `Shader` with current uniform values; shared by reference — the origin of the shared-material gotcha (§10). |
| **`CanvasGroup`** | Node that composites its children into one buffer, then applies its material to the merged result (§10.3). |
| **`hint_screen_texture`** | Sampler hint making a uniform read the back-buffer (replaces Godot 3's `SCREEN_TEXTURE` built-in) (§11.1). |
| **Back-buffer / `BackBufferCopy`** | The screen copy that screen-reading shaders sample; the node that controls when/what is copied (§11.1-11.2). |
| **Post-processing** | Full-frame effects via a screen-reading shader on a `ColorRect` in a `CanvasLayer` (§11.3). |
| **`discard`** | Fragment keyword abandoning the pixel entirely — the dissolve effect's engine (§4.7, §13.4). |
| **Swizzling** | Free reordering/duplication of vector components (`col.bgr`, `col.rrr`) (§4.3). |
| **LUT (lookup table)** | Small texture mapping input values to output colors — the palette-swap mechanism (§13.5). |
| **Bayer matrix** | Ordered-dithering threshold matrix (4×4 shown in full in §14.3); anchored to screen pixels via `FRAGCOORD`. |
| **Overdraw / fill rate** | Shading the same screen pixel multiple times; the pixels-per-second cost dimension that dominates 2D shader budgets (§17.1). |
| **Divergence** | Within a GPU warp, fragments taking different branch paths, forcing both paths to execute (§2.2, §17.3). |
| **Ubershader** | Godot 4.4+ precompiled generic pipeline enabling stutter-free first draws while specialized pipelines compile in the background (§17.5). |
| **Pipeline compilation stutter** | The first-use hitch when a driver compiles a shader/state combination at draw time; mitigated by warming materials at load (§17.5). |
| **`.gdshaderinc`** | Shader include file for shared functions/uniforms; pulled in with `#include`, guarded with `#ifndef` (§5.2). |

---

*End of Module 12. Previous: [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) · Companion reading: [Desktop Companion Performance](DESKTOP_COMPANION_PERFORMANCE.md) · Course index: [00-INDEX](00-INDEX.md)*

