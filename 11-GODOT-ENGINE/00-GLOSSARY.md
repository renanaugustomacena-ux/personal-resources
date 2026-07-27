---
course: "Godot 4 in Production"
file-role: "Course-wide glossary — canonical terminology reference for modules 01-14"
version: "Godot 4.5 / GDScript 2.0"
updated: 2026-07-27
tags: [godot, gdscript, glossary, terminology, reference, isometric, desktop-companion]
---

# Glossary — Godot 4 in Production

> **Updated:** 2026-07-27

This glossary aggregates and normalizes every technical term used across the fourteen course modules, the capstone, the exercise catalogue, and the Relax Room case study. Definitions are pinned to **Godot 4.5 / GDScript 2.0** semantics: where Godot 3.x or early 4.x used a different name (e.g., `TileMap` vs. `TileMapLayer`, `Engine.target_fps` vs. `Engine.max_fps`), the current name is the headword and the legacy name appears as its own entry marked *deprecated/legacy*.

**How to use this file.** Terms are grouped thematically, mirroring the course phases, so you can revise a whole topic area in one sitting. Each row gives a 1-3 sentence definition that is precise enough to stand alone, plus the module(s) where the term is taught in depth. When two definitions seem to conflict, this glossary is authoritative for the course. An alphabetical quick index at the bottom maps every term to its section for fast lookup.

**Module map** (numbers used in the "See module" column):

| # | File | # | File |
|---|---|---|---|
| 01 | [GODOT_ENGINE_STUDY.md](GODOT_ENGINE_STUDY.md) | 08 | [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md) |
| 02 | [SCENES_AND_NODES.md](SCENES_AND_NODES.md) | 09 | [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) |
| 03 | [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) | 10 | [GAME_DEV_PLANNING.md](GAME_DEV_PLANNING.md) |
| 04 | [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) | 11 | [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md) |
| 05 | [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md) | 12 | [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md) |
| 06 | [VISUAL_SYSTEMS_SUMMARY.md](VISUAL_SYSTEMS_SUMMARY.md) | 13 | [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) |
| 07 | [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md) | 14 | [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) |

## Contents

1. [Engine core & architecture](#1-engine-core--architecture)
2. [GDScript language](#2-gdscript-language)
3. [Scenes & nodes](#3-scenes--nodes)
4. [2D rendering & sprites](#4-2d-rendering--sprites)
5. [Tiles & isometric](#5-tiles--isometric)
6. [Shaders](#6-shaders)
7. [Persistence & data](#7-persistence--data)
8. [Audio](#8-audio)
9. [Physics & input](#9-physics--input)
10. [UI / Control](#10-ui--control)
11. [Performance & profiling](#11-performance--profiling)
12. [Build & export](#12-build--export)
13. [Project management & testing](#13-project-management--testing)
14. [Relax Room project terms](#14-relax-room-project-terms)
15. [Alphabetical quick index](#15-alphabetical-quick-index)

---

## 1. Engine core & architecture

The runtime skeleton: what actually executes your project, in what order, and through which global services.

| Term | Definition | See module |
|---|---|---|
| **Godot Engine** | Free, MIT-licensed open-source game engine maintained by the Godot Foundation and thousands of contributors. This course pins Godot 4.5. | 01 |
| **MainLoop** | The engine's top-level iteration object; `SceneTree` is the default `MainLoop` implementation that pumps `_process`, physics, and events every frame. | 01 |
| **SceneTree** | Runtime object holding the tree of active nodes, plus groups, timers, and pause state. Accessed from any node via `get_tree()`. | 01, 02 |
| **Server architecture** | Godot's internal split into low-level singletons (`RenderingServer`, `PhysicsServer2D`, `AudioServer`, `DisplayServer`, `NavigationServer2D`) that nodes are thin wrappers around. Direct server calls bypass node overhead for bulk work. | 01, 14 |
| **RenderingServer** | Server that owns all drawing primitives (canvas items, viewports, textures). Every `CanvasItem` ultimately becomes RenderingServer commands. | 01, 04 |
| **PhysicsServer2D** | Server simulating 2D bodies, areas, and shapes; nodes like `CharacterBody2D` are front-ends to it. | 01, 09 |
| **DisplayServer** | Server abstracting OS windowing: windows, vsync mode, clipboard, tray, screen DPI. Central to desktop-companion window tricks. | 01, 14 |
| **Object** | Base class of almost everything in Godot; provides signals, properties, and metadata. Manually memory-managed unless subclassing `RefCounted`. | 01 |
| **RefCounted** | `Object` subclass with automatic reference-counted memory management; base of `Resource`. Plain `Object`s must be freed with `free()`. | 01 |
| **Variant** | The dynamic any-type container used by GDScript variables, signals, and serialization; holds any of ~40 built-in types. | 01 |
| **Autoload** | A script or scene registered in Project Settings to be instantiated once at startup as a child of the root; the Godot idiom for singletons (e.g., `SaveManager`, `EventBus`). | 01, 13 |
| **Singleton** | A class with exactly one global instance. In Godot: engine singletons (`Input`, `OS`) plus user autoloads. Course rule: keep the autoload budget small and justified. | 01, 13 |
| **Autoload init order** | Autoloads initialize top-to-bottom as listed in Project Settings (not alphabetically at runtime — the list order is authoritative); an autoload must never assume a later one is ready. | 13 |
| **Init-time assertion** | `assert()` placed in `_ready()`/`_enter_tree()` of an autoload to fail fast on misconfiguration (missing node, empty config) instead of failing minutes later. | 13 |
| **Signal bus (event bus)** | An autoload whose only job is declaring globally interesting signals, letting distant nodes communicate without direct references. Core architecture pattern of this course. | 02, 09, 13 |
| **Dependency injection** | Passing a collaborator into a node (via property, `_init` argument, or setter) instead of having the node fetch it globally; reduces autoload coupling and eases testing. | 09, 13 |
| **`Engine` singleton** | Runtime engine settings and info: `Engine.max_fps` (frame cap), `Engine.time_scale`, `Engine.get_frames_per_second()`, `Engine.is_editor_hint()`. | 01, 14 |
| **`Engine.max_fps`** | Property capping the rendered frame rate at runtime (0 = uncapped). The lever behind the course's adaptive 15/60 FPS pattern. Replaces 3.x `Engine.target_fps`. | 14 |
| **`OS` singleton** | Operating-system facade: environment variables, executable path, `OS.low_processor_usage_mode`, process spawning, feature detection. | 01, 11, 14 |
| **`ProjectSettings`** | Singleton exposing `project.godot` configuration (window size, autoloads, input map, rendering options) with runtime read and (some) write access. | 01, 11 |
| **`call_deferred()`** | Queues a method call to run at idle time, after the current frame's processing; the safe way to mutate the tree from signal callbacks or threads. | 02, 13 |
| **Main thread** | The single thread that owns the scene tree; touching nodes from other threads is undefined behavior unless synchronized. | 13 |
| **`WorkerThreadPool`** | Engine-managed thread pool for parallel tasks (`add_task`, `add_group_task`); preferred over raw `Thread` for one-off background work such as save serialization. | 13 |
| **`Mutex` / `Semaphore`** | Synchronization primitives for guarding data shared between threads (e.g., a save queue written by the game and flushed by a worker). | 13 |
| **Thread guard** | Course pattern: an autoload method asserting `OS.get_thread_caller_id() == main_thread_id` (or using `is_on_main_thread` checks) before touching the tree. | 13 |
| **Notification** | Low-level engine message (`NOTIFICATION_WM_CLOSE_REQUEST`, `NOTIFICATION_APPLICATION_FOCUS_OUT`, …) delivered to `_notification()`; how a companion app detects focus loss or shutdown. | 01, 14 |
| **GDExtension** | Godot 4's native extension ABI for loading C/C++/Rust libraries without recompiling the engine; how plugins like godot-sqlite ship. | 01, 08 |
| **ClassDB** | Registry of all engine and extension classes; queried for reflection (`ClassDB.class_exists`, instantiating by name). | 01 |
| **Headless mode** | Running Godot with `--headless` (no window, no audio) for CI, tests, and command-line exports. | 11 |
| **Feature tags** | Strings describing the running build (`"windows"`, `"debug"`, `"editor"`, custom tags per export preset) queried via `OS.has_feature()` for platform-conditional logic. | 11 |

## 2. GDScript language

GDScript 2.0 as shipped with Godot 4.x: annotations, static typing, first-class callables and signals.

| Term | Definition | See module |
|---|---|---|
| **GDScript** | Godot's built-in, Python-flavored scripting language, tightly integrated with the editor (live reload, typed autocompletion, per-node scripts). | 01 |
| **GDScript 2.0** | The Godot 4 revision of the language: annotations (`@export`, `@onready`), first-class `Callable`/`Signal`, `await`, lambdas, typed arrays, and stricter static typing. | 01 |
| **Annotation** | `@`-prefixed metadata modifying a declaration: `@export`, `@onready`, `@tool`, `@rpc`, `@warning_ignore`, `@abstract` (4.5+). | 01 |
| **`@export`** | Annotation exposing a property in the Inspector and serializing it with the scene; variants like `@export_range`, `@export_enum`, `@export_file` add editor hints. | 01, 02 |
| **`@onready`** | Defers a variable's initializer until `_ready()`, when child nodes exist — the standard way to cache node references (`@onready var lbl := $Label`). | 02 |
| **`@tool`** | Makes a script execute inside the editor, enabling custom drawing/validation at edit time; guard editor-only logic with `Engine.is_editor_hint()`. | 04 |
| **`class_name`** | Registers a script as a global type usable in declarations and `is` checks, and (optionally with an icon) in the node creation dialog. | 01, 02 |
| **`@abstract`** | Godot 4.5+ annotation marking a class or method abstract: it cannot be instantiated / must be overridden. Useful for contract-style base scripts. | 01 |
| **Static typing** | Declaring types (`var hp: int`, `func f() -> void`) for editor autocompletion, error detection, and measurable runtime speedups in 4.x. Course style: type everything public. | 01 |
| **Type inference (`:=`)** | `var speed := 120.0` infers the static type from the initializer; combines brevity with typing. | 01 |
| **Typed array** | `Array[int]`, `Array[Node2D]` — arrays that enforce element type at runtime and in the analyzer. | 01 |
| **Typed dictionary** | `Dictionary[String, int]` — key/value typed dictionaries, added in Godot 4.4. | 01 |
| **`Callable`** | First-class reference to a method or lambda (`my_func`, `obj.method`, `func(x): return x*2`); passed to signals, `Tween`s, sort functions. | 01, 02 |
| **Lambda** | Anonymous inline function (`var f = func(a): return a + 1`); captures outer variables by value. | 01 |
| **`Signal` type** | Signals are first-class values in GDScript 2.0: `pressed.connect(_on_pressed)`, `died.emit()`, `await timeout`. | 02 |
| **`await`** | Suspends a function until a signal fires or a coroutine returns (`await get_tree().create_timer(1.0).timeout`); the function becomes a coroutine. | 01, 02 |
| **Coroutine** | Any GDScript function containing `await`; it returns control to the caller and resumes later on the awaited signal. | 01 |
| **`match`** | Structural switch statement supporting literals, types, arrays/dictionary patterns, and binding (`var`) patterns. | 01 |
| **Enum** | Named integer constants (`enum State { IDLE, WALK, WAVE }`); exportable with `@export var s: State`. | 01 |
| **Property (`set`/`get`)** | GDScript 2.0 inline accessors replacing 3.x `setget`: `var hp: int : set = _set_hp, get = _get_hp` or block syntax; the hook for validation and change signals. | 01 |
| **`StringName`** | Interned, cheap-to-compare string type (`&"jump"`) used for names of actions, groups, signals, and methods. | 01 |
| **`NodePath`** | Path value (`^"UI/Label"`) identifying a node relative to another; resolved with `get_node()`. | 02 |
| **`preload()` vs `load()`** | `preload` resolves a resource at parse time (constant, fails early); `load` at runtime (dynamic paths, lazy loading of heavy scenes). | 02, 14 |
| **`assert()`** | Debug-build-only check that halts with a message when false; stripped from release exports, so never use it for control flow. | 13 |
| **Duck typing** | Calling a method if it exists (`if obj.has_method("interact")`) rather than checking class; idiomatic at loosely-coupled boundaries, avoided in core systems. | 01, 09 |
| **`super`** | Keyword calling the parent-class implementation from an overriding method (`super()` or `super.method()`). | 01 |
| **Static function/variable** | `static func` / `static var` belong to the script, not instances; handy for pure helpers (iso math) without an autoload. | 01, 07 |
| **`@warning_ignore`** | Suppresses a named analyzer warning on the next line; course style requires a justification comment beside it. | 10 |

## 3. Scenes & nodes

Composition model: everything is a tree of nodes, and reusable subtrees are scenes.

| Term | Definition | See module |
|---|---|---|
| **Node** | The atomic building block: has a name, a parent, children, lifecycle callbacks, signals, and optionally a script. | 02 |
| **Scene** | A saved tree of nodes (`.tscn` text format); Godot apps are compositions of scenes instancing other scenes. | 02 |
| **Scene tree (runtime hierarchy)** | The live tree of all instantiated nodes under the root `Window`; distinct from any single `.tscn` file. | 02 |
| **`PackedScene`** | Resource holding a serialized scene; call `instantiate()` to create a fresh node tree from it. | 02 |
| **`instantiate()`** | Creates a new node hierarchy from a `PackedScene`; the instance is inert until added with `add_child()`. | 02 |
| **Instancing** | Placing one scene inside another (editor or code); the primary reuse mechanism, analogous to composition over inheritance. | 02 |
| **Inherited scene** | A scene created from another scene as its base, overriding properties while tracking upstream changes — Godot's scene-level inheritance. | 02 |
| **Editable children** | Editor option exposing an instanced scene's internal nodes for per-instance overrides; use sparingly, since it couples you to internals. | 02 |
| **Scene root** | The single top node of a scene file; its script usually forms the scene's public API. | 02 |
| **`owner`** | Property linking a node to its scene root for serialization; nodes created in code need `owner` set before `PackedScene.pack()` will save them. | 02 |
| **Node lifecycle** | Order of callbacks: `_init` → `_enter_tree` → `_ready` (children first) → per-frame `_process`/`_physics_process` → `_exit_tree`. | 02 |
| **`_init` / `_enter_tree` / `_ready`** | Constructor (no tree access) / entered the tree (parent valid, children not ready) / node and all children ready — pick the earliest callback that has what you need. | 02 |
| **`_process(delta)`** | Per-rendered-frame callback with elapsed seconds; variable rate. Use for visuals; disable it when idle to save CPU. | 02, 14 |
| **`_physics_process(delta)`** | Fixed-rate callback (default 60 Hz) synchronized with physics; use for movement and anything that must be deterministic per tick. | 02, 09 |
| **`queue_free()`** | Marks a node for safe deletion at end of frame; always prefer it to `free()` for nodes in the tree. | 02 |
| **`add_child()` / `remove_child()`** | Attach/detach a node; `remove_child` does not free the node — reuse it or `queue_free()` it explicitly. | 02 |
| **Group** | String tag applied to nodes (`add_to_group("saveable")`); queried via `get_tree().get_nodes_in_group()` or called via `call_group()` — a lightweight broadcast mechanism. | 02, 08 |
| **Scene-unique name (`%`)** | Node marked "Access as Unique Name" and referenced as `%Timer` from within the scene, robust against reparenting; preferred over long `$Path/To/Node` chains. | 02 |
| **Signal** | Event declared on an object and emitted to any number of connected `Callable`s; Godot's observer pattern and this course's default communication mechanism. | 02 |
| **`connect()` / connection flags** | Wires a signal to a callable; flags like `CONNECT_ONE_SHOT` (auto-disconnect after first emission) and `CONNECT_DEFERRED` (deliver at idle) tune delivery. | 02, 13 |
| **`emit()`** | Godot 4 emission syntax on the signal value itself: `health_changed.emit(hp)` (replaces 3.x `emit_signal("health_changed", hp)`). | 02 |
| **Signals up, calls down** | Rule of thumb: parents may call children directly; children report upward only via signals, keeping scenes reusable in isolation. | 02, 09 |
| **`Marker2D`** | Invisible positional node used as spawn point/anchor (3.x `Position2D`). | 02, 07 |
| **`Timer`** | Node emitting `timeout` after a wait time, one-shot or repeating; the scene-friendly alternative to counting `delta` manually. | 02, 14 |
| **`get_tree().create_timer()`** | One-off `SceneTreeTimer` for `await`-style delays without adding a node. | 02 |
| **Reparenting** | Moving a node to a new parent (`reparent()` keeps global transform); needed when a picked-up item must follow another branch of the tree. | 02, 07 |
| **`.tscn` / `.tres`** | Text-based scene and resource file formats — diff-able and merge-able in Git, which is why the course mandates them over binary `.scn`/`.res`. | 02, 10 |
| **`.uid` file** | Sidecar file (Godot 4.4+) storing a resource's stable unique ID so references survive file moves; must be committed to version control. | 10 |

## 4. 2D rendering & sprites

Everything between a PNG on disk and pixels on screen.

| Term | Definition | See module |
|---|---|---|
| **`CanvasItem`** | Abstract base of all 2D drawable things (`Node2D` and `Control`); owns visibility, modulate, z-index, material, and the `_draw()` pipeline. | 03, 04 |
| **`Sprite2D`** | Node displaying a static texture, optionally a region or a frame of a grid (`hframes`/`vframes`). | 03 |
| **`AnimatedSprite2D`** | Node playing named frame animations from a `SpriteFrames` resource; ideal for chibi idle/walk/wave cycles. | 03 |
| **`SpriteFrames`** | Resource holding animation → frame-list mappings with per-animation FPS and loop flags; editable in the SpriteFrames bottom panel. | 03 |
| **`AnimationPlayer`** | Node animating arbitrary node properties along keyframed tracks (position, modulate, function calls, audio); heavier but far more general than `AnimatedSprite2D`. | 03, 04 |
| **`AtlasTexture`** | Texture type exposing a sub-region of a larger atlas image as if it were a standalone texture. | 03 |
| **Spritesheet (atlas)** | Single image packing many frames/sprites; reduces texture switches and enables batching. | 03, 14 |
| **Texture filter — Nearest** | No interpolation between texels; mandatory for crisp pixel art. Set per-project (`default_texture_filter`) or per-node. | 03 |
| **Texture filter — Linear** | Bilinear interpolation; smooth for high-res art, blurry for pixel art. | 03 |
| **Mipmaps** | Precomputed downscaled texture chain reducing shimmer when minified (e.g., zoomed-out camera); costs ~33% extra VRAM. | 03, 14 |
| **Repeat (import)** | Texture wrap setting allowing UVs outside 0-1 to tile; required for scrolling-texture shader tricks. | 03, 12 |
| **Texture bleeding** | Neighboring atlas frame pixels leaking into a frame's edge due to filtering; fixed with padding/extrusion or nearest filtering. | 03 |
| **Pixel snapping** | Project settings (`2D → snap_2d_transforms_to_pixel`, `snap_2d_vertices_to_pixel`) that align rendering to whole pixels, preventing pixel-art shimmer. | 03, 04 |
| **`modulate` / `self_modulate`** | Color multiplier applied to a CanvasItem and its children / to the item only; the cheap way to tint, flash, or fade sprites. | 03, 04 |
| **`z_index` / `z_as_relative`** | Manual draw-order override within a canvas layer (-4096..4096); relative mode adds the parent's z-index. | 04, 07 |
| **Y-sort** | `CanvasItem.y_sort_enabled`: children are drawn in ascending global Y order so lower-on-screen objects overlap higher ones — the backbone of isometric depth. | 04, 05, 07 |
| **`CanvasLayer`** | Node placing its subtree on an independent canvas with its own transform; standard for HUD/UI immune to camera movement. | 04 |
| **`Parallax2D`** | Godot 4.3+ node scrolling its children at a configurable ratio of camera movement, with optional infinite repeat; successor to `ParallaxBackground`. | 04 |
| **`ParallaxBackground` / `ParallaxLayer`** | Legacy parallax pair still functional but superseded by `Parallax2D`; mentioned for migration literacy. | 04 |
| **Custom `_draw()`** | Overridable callback issuing immediate-mode draw commands (`draw_line`, `draw_texture`, `draw_polygon`) on a CanvasItem; cached until invalidated. | 04 |
| **`queue_redraw()`** | Invalidates a CanvasItem so `_draw()` runs again next frame (3.x `update()`); call it only when the drawing actually changed. | 04, 14 |
| **`Tween`** | Object created via `create_tween()` chaining property interpolations (`tween_property`), callbacks, and parallel steps with easing/transition curves; replaces the 3.x Tween node. | 04 |
| **Easing / transition curves** | Shape of a tween's interpolation (`TRANS_QUAD`, `EASE_OUT`…): the difference between mechanical and juicy motion. | 04 |
| **`Camera2D`** | Node defining the visible 2D region: zoom, limits, drag margins, smoothing. | 04, 07 |
| **`Viewport` / `SubViewport`** | Render targets; the root window is a viewport, and `SubViewport` renders a subtree offscreen for minimaps, portraits, or low-res pixel-perfect scaling. | 04 |
| **Stretch mode / aspect** | Project display settings (`canvas_items` vs `viewport` stretch) governing how the game scales across window sizes; `viewport` + integer scaling is the pixel-art recipe. | 03, 04, 11 |
| **`GPUParticles2D`** | GPU-simulated particle node with a `ParticleProcessMaterial`; cheap per-particle, but each system has fixed per-frame cost. | 04, 14 |
| **`CPUParticles2D`** | CPU fallback particle node; predictable on weak GPUs/integrated graphics, used when GPU particles misbehave. | 04, 14 |
| **`PointLight2D` / `DirectionalLight2D`** | 2D light nodes multiplying lit areas with a texture or direction; combine with occluders for mood lighting in the Relax Room. | 04 |
| **`LightOccluder2D`** | Polygon that blocks 2D light, producing shadows. | 04 |
| **`CanvasTexture`** | Texture type bundling diffuse + normal + specular maps so 2D lights can shade sprites. | 03, 04 |
| **`VisibleOnScreenNotifier2D` / `Enabler2D`** | Nodes signaling when a region enters/leaves the screen, or automatically pausing processing of offscreen subtrees — key culling tools. | 04, 14 |
| **Draw call** | One batch of geometry submitted to the GPU; texture/material switches break batching and multiply draw calls. Tracked per-frame in the profiler. | 04, 14 |
| **2D batching** | The renderer's automatic merging of compatible canvas items (same texture/material) into single draw calls. | 04, 14 |

## 5. Tiles & isometric

Grid-based worlds and the math of fake 3D.

| Term | Definition | See module |
|---|---|---|
| **`TileMapLayer`** | Godot 4.3+ node rendering one grid layer of tiles from a `TileSet`; scenes use several stacked layers (ground, walls, props). Replaces the multi-layer `TileMap` node. | 05 |
| **`TileMap` (legacy)** | Deprecated since Godot 4.3 in favor of one `TileMapLayer` node per layer; still loads for migration. | 05 |
| **`TileSet`** | Resource defining the tile palette: sources, physics/navigation/occlusion layers, terrain sets, and custom data layers. | 05 |
| **Tile source** | A provider of tiles inside a TileSet — atlas source (from a texture) or scene collection source (from scenes). | 05 |
| **Atlas source** | Tile source slicing a spritesheet into a grid of tiles, with support for animation columns and alternative tiles. | 05 |
| **Scene collection source** | Tile source whose "tiles" are full scenes (e.g., an animated fountain), placed and serialized like tiles. | 05 |
| **Alternative tile** | Variant of an atlas tile (flipped, recolored, different probability or custom data) addressed by an alternative ID. | 05 |
| **Terrain / terrain set** | TileSet feature that auto-selects transition tiles as you paint, based on peering-bit rules between neighboring tiles (Godot 4's autotiling). | 05 |
| **Autotiling** | Generic name for automatic tile-transition selection; in Godot 4 implemented by terrains. | 05 |
| **Peering bits** | Per-side/corner terrain tags on a tile telling the terrain system which neighbors it can sit next to. | 05 |
| **Physics layer (TileSet)** | Collision polygons assigned to tiles per TileSet physics layer, giving level geometry without manual collider nodes. | 05, 09 |
| **Navigation layer (TileSet)** | Navigation polygons baked into tiles so `NavigationAgent2D` can path across the map. | 05 |
| **Custom data layer** | Typed per-tile metadata (e.g., `walk_cost`, `is_water`) queried at runtime via `TileData.get_custom_data()`. | 05, 07 |
| **Cell coordinates** | Integer `Vector2i` grid position of a tile; distinct from local/world pixel positions. | 05, 07 |
| **`map_to_local()` / `local_to_map()`** | TileMapLayer conversions between cell coordinates and local pixel positions (center of tile); the bridge between grid logic and rendering. | 05, 07 |
| **`get_used_cells()` / `set_cell()`** | Query and mutate tiles at runtime — procedural rooms, destructible floors, load-time map building. | 05 |
| **Isometric projection** | Axonometric 2D projection simulating a 3D viewpoint with fixed camera angle; classic game "iso" is usually dimetric 2:1, not true 30° isometric. | 07 |
| **Dimetric (2:1)** | The pragmatic iso variant where tiles are twice as wide as tall (e.g., 64×32); angles work out to ~26.57°, and pixel art stays clean. | 07 |
| **Cartesian-to-iso transform** | `iso_x = cart_x - cart_y; iso_y = (cart_x + cart_y) / 2` (and its inverse) — the two-line math converting logic grids to screen diamonds. | 07 |
| **Diamond down / diamond right** | TileSet iso layout options controlling how odd rows/columns offset; diamond down is the common 2:1 staggerless layout. | 05, 07 |
| **Depth sorting** | Deciding draw order so nearer iso objects cover farther ones; solved with Y-sort plus per-tile `y_sort_origin` and z-index bands for flying/overlay elements. | 05, 07 |
| **`y_sort_origin`** | Per-tile / per-node vertical offset shifting the point used for Y-sort comparisons — how tall iso props sort as if anchored at their base. | 05, 07 |
| **Tile origin / anchor** | The point of the tile texture mapped to the cell position; tall iso tiles draw upward from a bottom-center anchor. | 05, 07 |
| **`AStar2D` / `AStarGrid2D`** | Built-in A* pathfinding classes; `AStarGrid2D` maps directly onto tile grids with diagonal-mode and heuristic options — usually enough for iso movement. | 07 |
| **`NavigationRegion2D` / `NavigationAgent2D`** | Polygon-based navigation alternative with dynamic obstacle avoidance; heavier than grid A*, used when free-form movement matters. | 05, 07 |
| **Staggered map** | Iso/hex layout offsetting alternate rows; changes neighbor math — document which layout your helpers assume. | 07 |
| **Elevation (iso)** | Faking height by offsetting sprites in screen-Y and adjusting sort origin; requires a consistent "height unit" convention project-wide. | 07 |

## 6. Shaders

GDShader for 2D: the course covers `canvas_item` shaders and pixel-art recipes.

| Term | Definition | See module |
|---|---|---|
| **GDShader** | Godot's GLSL-like shader language, saved as `.gdshader`; compiled per rendering backend by the engine. | 12 |
| **`shader_type`** | Mandatory first declaration: `canvas_item` (2D), `spatial` (3D), `particles`, `sky`, `fog`. This course uses `canvas_item` almost exclusively. | 12 |
| **canvas_item shader** | 2D shader with `vertex()`, `fragment()`, and `light()` stages operating on CanvasItems. | 12 |
| **spatial shader** | 3D shader type; out of scope here beyond knowing it exists. | 12 |
| **`fragment()`** | Per-pixel stage; reads `UV`/`TEXTURE`, writes `COLOR`. Where 90% of 2D effects live. | 12 |
| **`vertex()`** | Per-vertex stage; can displace `VERTEX` for wobble/squash effects at near-zero cost. | 12 |
| **`light()`** | Optional per-light stage on canvas_item shaders customizing how 2D lights hit the sprite. | 12 |
| **`COLOR`** | Fragment output color (premultiplied by `modulate`); assigning it is the shader's whole job. | 12 |
| **`UV`** | Normalized 0-1 texture coordinates of the current fragment. | 12 |
| **`TEXTURE`** | The CanvasItem's own texture sampler inside its shader; sampled as `texture(TEXTURE, UV)`. | 12 |
| **`TEXTURE_PIXEL_SIZE`** | `1.0 / texture_size` — the size of one texel in UV space; essential for outline and pixel-precise effects. | 12 |
| **`TIME`** | Built-in float of seconds since startup, the clock driving animated shader effects. | 12 |
| **Uniform** | Shader parameter set from the Inspector or `material.set_shader_parameter()`; the bridge between GDScript and the GPU. | 12 |
| **Global uniform** | Project-wide shader variable (`global uniform vec4 ambient;`) defined in Project Settings and set via `RenderingServer.global_shader_parameter_set()` — one write updates every material. | 12 |
| **`hint_range` / hints** | Uniform annotations (`: hint_range(0.0, 1.0)`, `: source_color`) controlling Inspector widgets and color-space handling. | 12 |
| **`hint_screen_texture`** | Godot 4 way to read the screen behind the item: `uniform sampler2D screen_tex : hint_screen_texture;` sampled at `SCREEN_UV` (replaces 3.x `SCREEN_TEXTURE` built-in). | 12 |
| **`SCREEN_UV`** | Fragment position in screen space 0-1, used with screen-reading uniforms for distortion/blur/frost effects. | 12 |
| **`BackBufferCopy`** | Node capturing the region behind it so screen-reading shaders have valid data in that area. | 12 |
| **Varying** | Variable computed in `vertex()` and interpolated into `fragment()`; how per-vertex data reaches per-pixel code. | 12 |
| **`ShaderMaterial`** | Material resource pairing a shader with its uniform values; assigned to a CanvasItem's `material` slot. | 12 |
| **Material duplication (`resource_local_to_scene`)** | Flag making each scene instance get its own material copy so per-instance uniform edits don't leak to every user of the shared resource. | 12 |
| **`VisualShader`** | Node-graph alternative to writing GDShader text; generates the same shader code under the hood. | 12 |
| **`discard`** | Fragment keyword dropping the pixel entirely; used for cutouts and dissolve effects (breaks early-Z on spatial, harmless for most 2D uses). | 12 |
| **Outline shader** | Recipe sampling the texture's alpha at ±`TEXTURE_PIXEL_SIZE` offsets to draw a colored rim — hover feedback on Relax Room furniture. | 12 |
| **Palette swap** | Recipe remapping source colors through a lookup gradient/texture, giving costume variants from one spritesheet. | 12 |
| **Dithering** | Simulating gradients with patterns of available colors; retro look and banding fix. | 12 |
| **Bayer matrix** | Ordered dithering threshold matrix (2×2, 4×4, 8×8) indexed by screen pixel to decide dither pattern. | 12 |
| **Scanline / CRT shader** | Screen-space recipe combining darkened line pattern, slight curvature, and chromatic offset to emulate CRT displays. | 12 |
| **Shader compilation stutter** | Frame hitch when a shader variant compiles on first use; mitigated by warming up materials at load and, since Godot 4.5, by the shader baker at export. | 12, 14 |
| **Shader baker (4.5)** | Export-time precompilation of shaders introduced in Godot 4.5, cutting first-run compilation stutter and load times. | 11, 12 |

## 7. Persistence & data

Saving state so it survives crashes, upgrades, and users.

| Term | Definition | See module |
|---|---|---|
| **`user://`** | Writable per-user directory (on Windows: `%APPDATA%\Godot\app_userdata\<project>` unless `custom_user_dir_name` is set); the only sane place for saves, settings, and logs. | 08 |
| **`res://`** | Read-only project/PCK root at runtime; never write here in exported builds. | 08, 11 |
| **`FileAccess`** | File I/O class (`open`, `store_string`, `get_as_text`, `store_var`); Godot 4 static-open API replacing 3.x `File`. | 08 |
| **`DirAccess`** | Directory operations: list, make, rename, remove — used by save-slot and backup-rotation code. | 08 |
| **Atomic write (temp + rename)** | Course-mandated save pattern: write to `save.json.tmp`, `flush()`, then `DirAccess.rename_absolute()` over the real file — a crash never destroys the previous good save. | 08, 13 |
| **`flush()`** | Forces buffered file writes to the OS before rename/close; the step that makes "atomic" actually atomic in practice. | 08 |
| **`JSON.stringify()` / `JSON.parse_string()`** | Serialize/parse between `Variant` structures and JSON text; human-readable saves, no code execution risk. | 08 |
| **`store_var()` / `get_var()`** | Binary Variant serialization in `FileAccess`; compact and fast, but with `full_objects = true` it can instantiate scripts — never enable that on untrusted files. | 08 |
| **`ConfigFile`** | INI-style key/section store with typed values; ideal for settings (volume, window mode) as opposed to game saves. | 08 |
| **Resource-based save** | Saving a custom `Resource` subclass via `ResourceSaver.save()`; convenient but `.tres` can embed scripts, so treat foreign save files as untrusted. | 08 |
| **`ResourceLoader` / `ResourceSaver`** | Engine APIs for loading/saving `Resource` files with caching and type filters. | 02, 08 |
| **Serialization / deserialization** | Converting runtime state to storable bytes/text and back; the course pattern serializes plain dictionaries, never live nodes. | 08 |
| **Schema version** | Integer stored inside every save file identifying its structure generation; the first thing `load()` reads. | 08 |
| **Migration chain** | Ordered list of `migrate_vN_to_vN+1()` functions upgrading any old save step-by-step to current; each step is individually testable. | 08 |
| **Save slot** | Independent named save file/directory per profile; slot management lives above the serialization layer. | 08 |
| **Backup rotation** | Keeping the last N good saves (`save.json.1`, `.2`, …) so corruption or bad migrations are recoverable. | 08 |
| **SQLite** | Embedded, serverless, single-file SQL database in the public domain; the course's choice once relational queries or partial updates outgrow JSON. | 08 |
| **godot-sqlite** | GDExtension plugin (2shady4u) binding SQLite into Godot: `SQLite.new()`, `query_with_bindings()`, blob support. | 08 |
| **Prepared statement / bindings** | Parameterized SQL (`query_with_bindings("... WHERE id = ?", [id])`) preventing SQL injection and improving reuse. | 08 |
| **Transaction** | `BEGIN`/`COMMIT` batch making multiple statements atomic; wrap every multi-table save in one. | 08 |
| **WAL mode** | SQLite write-ahead logging (`PRAGMA journal_mode=WAL`): readers don't block writers and commits are faster — good default for companion apps. | 08 |
| **`PRAGMA user_version`** | SQLite's built-in integer version slot, the SQL twin of the JSON schema version, driving SQL migration chains. | 08 |
| **Offline-first** | Design stance: the app is fully functional with no network; sync, if any, is an enhancement layered on later. | 08, 09 |
| **Supabase** | Open-source Firebase alternative (Postgres + auth + REST); the course's reference target for optional cloud sync of Relax Room data. | 08 |
| **Sync conflict resolution** | Policy for divergent local/remote state (last-write-wins, per-field merge); must be chosen deliberately, not left to chance. | 08 |
| **Encryption at rest** | `FileAccess.open_encrypted_with_pass()` for saves; protects against casual tampering only — the key ships inside your binary. | 08 |

## 8. Audio

Sound architecture for a calm companion app: buses, streams, and not annoying the user.

| Term | Definition | See module |
|---|---|---|
| **`AudioServer`** | Server managing buses, effects, and output devices; scriptable at runtime (`AudioServer.set_bus_volume_db`). | 01, 09 |
| **Audio bus** | Mixer channel (Master, Music, SFX…) that streams route into; per-bus volume, mute, and effect chains. | 09 |
| **Audio bus layout** | `.tres` resource storing the bus configuration; set as project default and edited in the Audio bottom panel. | 09 |
| **Bus effect** | DSP inserted on a bus (reverb, low-pass, limiter, compressor); a low-pass on Music is the classic "app lost focus" softening. | 09 |
| **`AudioStreamPlayer`** | Non-positional playback node (UI sounds, ambient music); the default for desktop companions. | 09 |
| **`AudioStreamPlayer2D`** | Positional 2D playback with distance attenuation; only worth it when the room is larger than the window. | 09 |
| **`AudioStreamOggVorbis` / WAV** | Compressed Ogg for long music/ambience (small, loop points); uncompressed WAV for short SFX (zero decode latency). | 09 |
| **Loop points (Ogg)** | Import-defined sample-accurate loop start/end letting ambience loop seamlessly. | 09 |
| **`AudioStreamRandomizer`** | Stream wrapper picking randomized variants with pitch/volume jitter, preventing repetitive SFX fatigue. | 09 |
| **`AudioStreamInteractive`** | Godot 4.3+ stream that transitions between named clips on cue (calm → focus music without hard cuts). | 09 |
| **`volume_db` / `linear_to_db()`** | Volume is exposed in decibels; UI sliders should map linear 0-1 through `linear_to_db()` or loudness feels wrong. | 09 |
| **Audio latency** | Delay between trigger and audible output; tuned via output latency project setting, rarely an issue for non-rhythm apps. | 14 |
| **Focus-loss audio policy** | Companion-app rule: decide explicitly what happens to audio when the window loses focus (duck, pause, continue) and expose it as a setting. | 09, 14 |

## 9. Physics & input

Just enough physics for interaction, and a disciplined input layer.

| Term | Definition | See module |
|---|---|---|
| **`CharacterBody2D`** | Kinematic body moved by script via `move_and_slide()`/`move_and_collide()`; the standard player/chibi controller. | 02, 09 |
| **`StaticBody2D`** | Immovable collider (walls, furniture); zero per-frame cost while idle. | 02, 05 |
| **`RigidBody2D`** | Physics-simulated body with forces and impulses; rarely needed in a companion app, but great for toy physics interactions. | 02 |
| **`Area2D`** | Non-solid region detecting overlaps and emitting `body_entered`/`area_entered`; hotspots, triggers, click zones. | 02, 09 |
| **`CollisionShape2D`** | Child node giving a body/area its shape resource (rectangle, circle, capsule, polygon). | 02 |
| **Collision layer vs. mask** | Layer = "what I am"; mask = "what I scan". A body detects another only if its mask includes the other's layer — the single most misunderstood physics setting. | 02, 09 |
| **`move_and_slide()`** | CharacterBody2D helper integrating `velocity`, sliding along collisions, and reporting floor/wall contact. | 02 |
| **`velocity`** | Built-in CharacterBody2D property (pixels/second) consumed by `move_and_slide()`; replaces passing velocity manually as in 3.x. | 02 |
| **`RayCast2D` / `ShapeCast2D`** | Nodes querying "what's in this direction/volume" each physics frame; line-of-sight, cursor probing, ledge checks. | 05, 07 |
| **One-way collision** | Shape flag letting bodies pass in one direction (platforms); also useful for iso doorway tricks. | 05 |
| **Physics tick rate** | `physics/common/physics_ticks_per_second` (default 60); fixed timestep independent of render FPS. | 14 |
| **Physics interpolation (2D)** | Godot 4.3+ option rendering bodies interpolated between physics ticks, decoupling smooth visuals from tick rate — pairs with the 15/60 adaptive pattern. | 14 |
| **`delta`** | Seconds elapsed since the previous frame/tick, passed to process callbacks; multiply all rates by it for frame-rate independence. | 02, 14 |
| **`InputMap`** | Project-settings table mapping named actions ("interact", "pause") to keys/buttons/axes; code references actions, never raw keys. | 09 |
| **Action** | Named abstract input ("ui_accept", custom "toggle_overlay") with a deadzone; queried via `Input.is_action_pressed()` and friends. | 09 |
| **`Input` singleton** | Polling API: `is_action_just_pressed`, `get_vector`, mouse position/mode, gamepad state. | 09 |
| **`InputEvent`** | Event object (key, mouse button/motion, action, touch) delivered through the input pipeline. | 09 |
| **`_input()` vs `_unhandled_input()`** | `_input` sees every event before UI; `_unhandled_input` only what Controls didn't consume — put gameplay input in the latter so clicking a button doesn't also click the world. | 09 |
| **`mouse_filter`** | Control property (Stop/Pass/Ignore) deciding whether UI consumes mouse events; the #1 cause of "my clicks don't reach the game". | 04, 09 |
| **Echo event** | Auto-repeated key event while held; filter with `event.is_echo()` when you want the initial press only. | 09 |
| **`Shortcut` / shortcut context** | Resource binding key combos to buttons/menu items with scoped delivery; the desktop way to add hotkeys. | 09 |

## 10. UI / Control

The Control subtree: layout containers, themes, and desktop-window behavior.

| Term | Definition | See module |
|---|---|---|
| **`Control`** | Base class of all UI nodes; adds anchors, focus, theming, and mouse filtering on top of CanvasItem. | 04 |
| **Anchors & offsets** | Control layout system positioning edges relative to the parent's rect (anchors 0-1) plus pixel offsets; use anchor presets before touching numbers. | 04 |
| **Container** | Control that owns its children's layout (`HBoxContainer`, `VBoxContainer`, `GridContainer`, `MarginContainer`, `PanelContainer`, `CenterContainer`); children's manual positions are overridden by design. | 04 |
| **Size flags** | Per-child expand/fill/shrink hints that containers use to distribute space. | 04 |
| **`custom_minimum_size`** | Floor size a Control reports to its container; the correct fix when a container squashes content. | 04 |
| **`Label` / `RichTextLabel`** | Plain text vs. BBCode-capable text (colors, images, wave/shake effects); RichTextLabel is heavier — don't use it for static captions. | 04 |
| **BBCode** | Markup understood by RichTextLabel (`[b]`, `[color]`, `[img]`, custom effects). | 04 |
| **`Button` / `BaseButton`** | Clickable controls emitting `pressed`/`toggled`; `TextureButton` for image-based skins. | 04 |
| **`TextureRect` / `NinePatchRect`** | Image display in UI; NinePatch stretches borders without distorting corners — the classic panel skin. | 04 |
| **`Theme`** | Resource centralizing UI styling (fonts, colors, StyleBoxes per control type); one project theme + local overrides beats per-node styling. | 04 |
| **Theme override** | Per-node style exception (`theme_override_*`); flag each one in review — too many means the theme is wrong. | 04 |
| **`StyleBox`** | Drawable UI background primitive (Flat, Texture, Line, Empty) used by themes for panels and button states. | 04 |
| **Focus (UI)** | Which Control receives keyboard/gamepad input; `focus_mode` and neighbor paths define traversal — required for keyboard accessibility. | 04 |
| **Tooltip** | Hover text via `tooltip_text`; cheap affordance for icon-only companion UI. | 04 |
| **`Window` / `Popup`** | Godot 4 windows are nodes; subwindows can be embedded in the main window or native OS windows — dialogs, settings panels, detachable overlays. | 04, 14 |
| **Always-on-top / borderless / transparent** | Window flags composing the "desktop pet" look: frameless, floating above other apps, with per-pixel transparency. | 14 |
| **Per-pixel transparency** | Project + window setting making the window background truly transparent so only the chibi/room shape is visible on the desktop; costs compositing overhead — measure it. | 14 |
| **Mouse passthrough** | `Window.mouse_passthrough` / passthrough polygon letting clicks fall through transparent regions to apps underneath — mandatory for non-intrusive overlays. | 14 |
| **`StatusIndicator`** | Godot 4.3+ node creating a system-tray icon with menu/click signals; the "minimize to tray" backbone of a companion app. | 14 |
| **HiDPI / content scale** | Display scaling settings (`content_scale_factor`, scale mode/aspect) keeping UI readable on 4K and mixed-DPI multi-monitor setups. | 04, 11 |
| **Accessibility (4.5)** | Godot 4.5 ships experimental screen-reader support (AccessKit) and per-Control accessibility descriptions; the course requires descriptions on all interactive Controls. | 04 |
| **Internationalization (i18n)** | `tr()` + translation CSV/PO resources; even a two-language companion app must externalize user-facing strings. | 04, 10 |

## 11. Performance & profiling

Measure, don't guess — and respect the desktop: a companion app shares the machine.

| Term | Definition | See module |
|---|---|---|
| **FPS (frames per second)** | Rendered frames per second; course targets: stable 60 active, throttled 15 (or less) idle. | 14 |
| **Frame time** | Milliseconds per frame (16.6 ms ↔ 60 FPS); the honest metric — FPS averages hide spikes, frame time shows them. | 14 |
| **Frame pacing** | Evenness of frame delivery; 55 FPS steady feels better than 60 FPS with hitches. Watch the frame-time graph, not the counter. | 14 |
| **`Performance.get_monitor()`** | Runtime metrics API: `TIME_FPS`, `TIME_PROCESS`, `MEMORY_STATIC`, `RENDER_TOTAL_DRAW_CALLS_IN_FRAME`, `OBJECT_ORPHAN_NODE_COUNT`, and more — the data source for in-app perf HUDs. | 01, 14 |
| **Custom monitor** | User-registered metric (`Performance.add_custom_monitor()`) graphed alongside built-ins in the editor Monitors tab. | 14 |
| **Profiler (editor)** | Debugger tab sampling script functions per frame with self/total times; the first stop for CPU spikes. | 14 |
| **Visual Profiler** | Debugger tab breaking down GPU/render time per stage; the first stop when the GPU, not scripts, is the bottleneck. | 14 |
| **Monitors tab** | Live-graph view of engine metrics over time; ideal for spotting slow leaks (memory, node count) during soak tests. | 14 |
| **CPU-bound vs. GPU-bound** | Diagnosis of which processor limits frame rate; determined by comparing script/process time vs. render time before optimizing anything. | 14 |
| **Draw-call hotspot** | Scene region generating disproportionate draw calls (unbatchable materials, many unique textures); found via monitors, fixed via atlases/shared materials. | 04, 14 |
| **Overdraw** | Painting the same pixel multiple times per frame (stacked transparent layers); a hidden GPU cost in decorated iso rooms. | 14 |
| **Culling (2D)** | Skipping offscreen work — the renderer clips automatically, but scripts, particles, and animations keep running unless you gate them (`VisibleOnScreenEnabler2D`, manual `set_process(false)`). | 04, 14 |
| **`set_process(false)`** | Disables a node's per-frame callback; the primary idle-mode tool — a sleeping chibi should cost zero script time. | 02, 14 |
| **Object pooling** | Reusing instances instead of instantiate/free cycles; worth it only for high-churn objects (particles' floaty numbers), measure first. | 14 |
| **`OS.low_processor_usage_mode`** | Skips redrawing when nothing changed (application-style rendering); combined with `Engine.max_fps` for near-zero idle CPU. | 14 |
| **VSync** | Synchronizing presentation to monitor refresh (`DisplayServer.window_set_vsync_mode`); eliminates tearing, caps FPS, interacts with frame pacing. | 14 |
| **Adaptive FPS (15/60 pattern)** | Course pattern: drop `Engine.max_fps` (and disable processing) when idle/unfocused, restore 60 on interaction — ≤1% CPU idle is the capstone NFR. | 14 |
| **Orphan node** | Node created but never added to the tree nor freed; tracked by `OBJECT_ORPHAN_NODE_COUNT` — a steady climb is a leak. | 13, 14 |
| **Memory leak (Godot flavors)** | Un-freed `Object`s, orphan nodes, reference cycles with signals — found via Monitors + `--verbose` leak dump at exit. | 13, 14 |
| **Static memory** | `MEMORY_STATIC` monitor: engine-side allocations; baseline plus per-feature deltas belong in the capstone performance report. | 14 |
| **VRAM / texture memory** | GPU memory held by textures; the video RAM monitor plus import settings (compression, mipmaps) control it. | 03, 14 |
| **Soak test** | Running the app for hours under automation to expose leaks and drift; required before capstone submission. | 10, 14 |

## 12. Build & export

From project folder to installed application on someone else's machine.

| Term | Definition | See module |
|---|---|---|
| **Export template** | Precompiled Godot runtime per platform/architecture that your project data is packaged with; must exactly match the editor version. | 11 |
| **Export preset** | Named per-platform configuration (features, icons, signing, resource filters) stored in `export_presets.cfg`. | 11 |
| **`export_presets.cfg`** | Text file holding all presets; commit it, but keep secrets (keystore passwords) in environment variables, not in the file. | 11 |
| **PCK file** | Godot's packed archive of project resources; shipped beside the executable or embedded into it. | 11 |
| **Embedded PCK** | Single-file executable with the PCK inside; simpler distribution, larger patcher downloads. | 11 |
| **Resource export filters** | Preset rules including/excluding files from the PCK (strip dev assets, include licenses). | 11 |
| **`--headless --export-release`** | CLI export invocation used by CI: no window, preset name + output path, exit code signals success. | 11 |
| **Debug vs. release export** | Debug builds include remote debugger and `assert()`s; release builds strip them and enable optimizations — never ship debug. | 11 |
| **Code signing** | Cryptographically signing binaries/installers so OSes trust them (Authenticode on Windows, codesign on macOS); unsigned apps trigger SmartScreen/Gatekeeper warnings. | 11 |
| **Notarization** | Apple's automated malware scan + ticket stapling required for macOS distribution outside the App Store. | 11 |
| **rcedit** | Tool Godot invokes to stamp Windows EXEs with icon and version metadata; configured in editor settings. | 11 |
| **Inno Setup** | Free scriptable Windows installer system (`.iss` scripts); course tool for the capstone's `setup.exe` with install dir, shortcuts, uninstaller. | 11 |
| **`.iss` script** | Inno Setup's declarative install script: files, registry, shortcuts, upgrade behavior — versioned with the project. | 11 |
| **AppImage** | Linux single-file portable app format: bundle Godot binary + PCK + desktop metadata into one executable file, no install needed. | 11 |
| **APK / AAB** | Android package formats: APK installs directly (sideload/testing); AAB is the Play-Store upload format that generates device-optimized APKs. | 11 |
| **Keystore (debug/release)** | Java keystore holding Android signing keys; losing the release key means losing app-update ability — back it up offline. | 11 |
| **Gradle build** | Full Android build path (custom templates) needed for plugins/manifest edits; otherwise Godot's prebuilt templates suffice. | 11 |
| **CI/CD** | Continuous Integration/Delivery: every push runs checks, every tag builds artifacts — removes "works on my machine" from shipping. | 11 |
| **godot-ci** | Community Docker images (e.g., `abarichello/godot-ci`) with editor + templates preinstalled, the standard base for Godot GitHub Actions jobs. | 11 |
| **GitHub Actions** | GitHub's CI runner; course pipeline: lint → headless tests → matrix export → upload artifacts → release on tag. | 11 |
| **Build artifact** | File produced by CI (installer, AppImage, APK) retained per run and attached to releases. | 11 |
| **Semantic versioning** | `MAJOR.MINOR.PATCH` scheme; the course ties save-schema bumps to MAJOR and surfaces the version in-app and in the installer. | 10, 11 |
| **Release tag** | Git tag (`v1.2.0`) marking a shippable commit; the trigger for the release pipeline. | 10, 11 |

## 13. Project management & testing

Keeping a solo/small project shippable for years, and proving it works.

| Term | Definition | See module |
|---|---|---|
| **Technical debt** | Future cost incurred by expedient shortcuts; acceptable when logged and scheduled, toxic when invisible. | 10 |
| **Refactoring** | Behavior-preserving restructuring done in small, tested steps; never mixed into feature commits. | 10 |
| **Pre-modification checklist** | Course ritual before touching production code: reproduce current behavior, note invariants, ensure a test or manual probe exists, plan rollback. | 10 |
| **Version control (Git)** | Non-negotiable baseline; Godot-specific rules: ignore `.godot/`, commit `.uid` files, use text formats, small focused commits. | 10 |
| **Git LFS** | Large File Storage for binary assets (PSDs, audio) keeping the repo clonable; pointers in Git, blobs in LFS. | 10 |
| **`.gitignore` (Godot)** | Must exclude `.godot/` (editor cache), export outputs, and local overrides; must NOT exclude `.uid`, `project.godot`, or import files' metadata. | 10 |
| **Scene merge conflict** | Two branches editing one `.tscn`; mitigated by text formats, one-scene-one-owner conventions, and small scenes. | 10 |
| **Conventional commits** | Commit message convention (`feat:`, `fix:`, `refactor:`) enabling changelog generation and intent-searchable history. | 10 |
| **Vertical slice** | Thin end-to-end version of the product (one room, one habit, save + export working) proving the architecture before content scales. | 10 |
| **Milestone** | Dated scope checkpoint with explicit deliverables and acceptance criteria; the capstone plan uses eight. | 10 |
| **Definition of done** | Agreed checklist a task must pass (tested, profiled, documented) before it counts as complete. | 10 |
| **Scope creep** | Uncontrolled requirement growth; countered with a parking-lot list and milestone discipline. | 10 |
| **MoSCoW** | Prioritization buckets — Must/Should/Could/Won't — used to scope capstone variants honestly. | 10 |
| **Post-mortem** | Structured retrospective after ship: what worked, what didn't, what changes next time; a capstone deliverable. | 10 |
| **Bus factor** | How many people can disappear before the project stalls; solo devs raise it with documentation and boring, standard tooling. | 10 |
| **Unit test** | Test of one script/function in isolation (iso math, migration steps — pure logic first). | 10 |
| **Integration test** | Test crossing systems (save → load → state intact; signal chain end-to-end). | 10 |
| **Smoke test** | Minimal "does it even run" check: app boots headless, main scene loads, exits cleanly — the cheapest CI gate. | 10, 11 |
| **GUT** | Godot Unit Test (bitwes/GUT): GDScript test framework with asserts, doubles/spies, and CLI runner for CI. | 10 |
| **GdUnit4** | Actively maintained testing framework for Godot 4 (MikeSchulze/gdUnit4): fluent asserts, scene runners, parameterized tests, CI reports. Either GUT or GdUnit4 satisfies course requirements. | 10 |
| **Test double / spy** | Stand-in object recording calls or faking behavior so a unit test isolates its subject (fake `FileAccess`, spy on signal emission). | 10 |
| **gdlint / gdformat** | Linter and formatter from `gdscript-toolkit` (Scony) enforcing style and catching smells in CI. | 10 |
| **`--check-only`** | Godot CLI flag parsing scripts without running; a fast syntax gate in pipelines. | 10, 11 |
| **Headless test run** | Executing the test suite via `godot --headless` in CI; exit code fails the build. | 10, 11 |
| **Regression** | Previously working behavior that breaks; every fixed bug earns a test pinning it closed. | 10 |

## 14. Relax Room project terms

Vocabulary specific to the running case study — a calm isometric desktop companion. (Preserved and extended from the original project glossary.)

| Term | Definition | See module |
|---|---|---|
| **Relax Room** | The course's running case-study application: an isometric cozy room rendered in a desktop window, inhabited by a chibi character, persisting user state locally. | 09 |
| **Desktop companion** | App genre this course targets: small always-available desktop program (tray icon, low idle cost, optional overlay) mixing a utility with an ambient game layer. | 09, 14 |
| **Chibi character** | The small stylized inhabitant of the room; an `AnimatedSprite2D`-driven actor with an idle/walk/wave state machine. | 03, 09 |
| **Idle state machine** | The chibi's behavior model (idle → wander → interact → sleep) implemented as an enum-driven or node-based FSM; transitions are signal-observable. | 09 |
| **Isometric room** | The 2:1 dimetric TileMapLayer stack (floor, walls, furniture) forming the app's visual core. | 05, 07, 09 |
| **Decoration (unlockable)** | Furniture/prop items the user earns and places; each is a tile or scene-collection tile plus a persisted inventory record. | 05, 09 |
| **Room state** | The serializable snapshot of the room: placed decorations, chibi mood, timers, currency; the payload of the save system. | 08, 09 |
| **Focus session** | The pomodoro-style timed activity the companion tracks; sessions mutate room state (rewards) and are logged for streaks. | 09 |
| **Streak** | Consecutive-day count of completed habits/sessions; a derived value recomputed from the activity log, never stored as truth. | 08, 09 |
| **Ambience loop** | The seamless background soundscape (rain, lo-fi, fireplace) on its own audio bus with user-controlled volume. | 09 |
| **Tray mode** | Running minimized to a `StatusIndicator` tray icon with the window hidden and FPS throttled to near zero. | 14 |
| **Overlay mode** | Borderless, transparent, always-on-top presentation where only the chibi is visible over the user's desktop, with mouse passthrough elsewhere. | 14 |
| **Save schema v4.0.0** | The current Relax Room save-format generation; the capstone requires demonstrating a working migration chain into it from at least two older schemas. | 08 |
| **Cloud sync (optional)** | Supabase-backed backup of room state for users who opt in; strictly layered above the offline-first local save. | 08 |
| **VirtIO** | Standard for paravirtualized I/O devices in virtual machines. Game-irrelevant; retained here because it appears in the original project notes' environment context (testing builds inside VMs). | 11 |

---

## 15. Alphabetical quick index

Section key: **Core** §1 · **GD** §2 · **Scn** §3 · **2D** §4 · **Tile** §5 · **Shd** §6 · **Data** §7 · **Aud** §8 · **Phys** §9 · **UI** §10 · **Perf** §11 · **Exp** §12 · **PM** §13 · **RR** §14

- **A** — AAB (Exp) · `@abstract` (GD) · Accessibility 4.5 (UI) · Action (Phys) · Adaptive FPS 15/60 (Perf) · `add_child` (Scn) · Alternative tile (Tile) · Always-on-top (UI) · Ambience loop (RR) · Anchors & offsets (UI) · `AnimatedSprite2D` (2D) · `AnimationPlayer` (2D) · Annotation (GD) · APK (Exp) · AppImage (Exp) · `Area2D` (Phys) · `assert()` (GD) · `AStar2D`/`AStarGrid2D` (Tile) · `AtlasTexture` (2D) · Atlas source (Tile) · Atomic write (Data) · Audio bus / layout / effect (Aud) · `AudioServer` (Aud) · `AudioStreamInteractive` (Aud) · `AudioStreamPlayer`/`2D` (Aud) · `AudioStreamRandomizer` (Aud) · Autoload (Core) · Autoload init order (Core) · Autotiling (Tile) · `await` (GD)
- **B** — `BackBufferCopy` (Shd) · Backup rotation (Data) · Batching 2D (2D) · Bayer matrix (Shd) · BBCode (UI) · Bus effect (Aud) · Bus factor (PM) · Build artifact (Exp) · `Button` (UI)
- **C** — `call_deferred` (Core) · `Callable` (GD) · `Camera2D` (2D) · canvas_item shader (Shd) · `CanvasItem` (2D) · `CanvasLayer` (2D) · `CanvasTexture` (2D) · Cartesian-to-iso (Tile) · Cell coordinates (Tile) · `CharacterBody2D` (Phys) · `--check-only` (PM) · Chibi character (RR) · CI/CD (Exp) · ClassDB (Core) · `class_name` (GD) · Cloud sync (RR) · Code signing (Exp) · Collision layer vs mask (Phys) · `CollisionShape2D` (Phys) · `COLOR` (Shd) · `ConfigFile` (Data) · `connect()` / flags (Scn) · Container (UI) · Conventional commits (PM) · Coroutine (GD) · CPU-bound vs GPU-bound (Perf) · `CPUParticles2D` (2D) · CRT/scanline shader (Shd) · Culling 2D (Perf) · Custom `_draw()` (2D) · Custom data layer (Tile) · Custom monitor (Perf) · `custom_minimum_size` (UI)
- **D** — Debug vs release export (Exp) · Decoration (RR) · `delta` (Phys) · Definition of done (PM) · Dependency injection (Core) · Depth sorting (Tile) · Desktop companion (RR) · Diamond down/right (Tile) · Dimetric 2:1 (Tile) · `DirAccess` (Data) · `discard` (Shd) · `DisplayServer` (Core) · Dithering (Shd) · Draw call (2D) · Draw-call hotspot (Perf) · Duck typing (GD)
- **E** — Easing curves (2D) · Echo event (Phys) · Editable children (Scn) · Elevation iso (Tile) · Embedded PCK (Exp) · `emit()` (Scn) · Encryption at rest (Data) · `Engine` singleton / `max_fps` (Core) · Enum (GD) · Export preset / template (Exp) · `export_presets.cfg` (Exp)
- **F** — Feature tags (Core) · `FileAccess` (Data) · `flush()` (Data) · Focus (UI) · Focus-loss audio policy (Aud) · Focus session (RR) · FPS (Perf) · `fragment()` (Shd) · Frame pacing (Perf) · Frame time (Perf)
- **G** — GDExtension (Core) · gdlint/gdformat (PM) · GDScript / 2.0 (GD) · GDShader (Shd) · GdUnit4 (PM) · `get_tree().create_timer()` (Scn) · `get_used_cells()` (Tile) · Git LFS (PM) · `.gitignore` Godot (PM) · Global uniform (Shd) · Godot Engine (Core) · godot-ci (Exp) · godot-sqlite (Data) · `GPUParticles2D` (2D) · Gradle build (Exp) · Group (Scn) · GUT (PM)
- **H** — Headless mode (Core) · `--headless --export-release` (Exp) · Headless test run (PM) · HiDPI / content scale (UI) · `hint_range` (Shd) · `hint_screen_texture` (Shd)
- **I** — Idle state machine (RR) · Inherited scene (Scn) · `_init`/`_enter_tree`/`_ready` (Scn) · Init-time assertion (Core) · Inno Setup / `.iss` (Exp) · `Input` singleton (Phys) · `_input` vs `_unhandled_input` (Phys) · `InputEvent` (Phys) · `InputMap` (Phys) · Instancing / `instantiate()` (Scn) · Integration test (PM) · Internationalization (UI) · Isometric projection (Tile) · Isometric room (RR)
- **J** — `JSON.stringify`/`parse_string` (Data)
- **K** — Keystore (Exp)
- **L** — `Label`/`RichTextLabel` (UI) · Lambda (GD) · `light()` (Shd) · `LightOccluder2D` (2D) · Linear filter (2D) · `linear_to_db()` (Aud) · `load()` (GD) · Loop points (Aud) · `OS.low_processor_usage_mode` (Perf)
- **M** — Main thread (Core) · MainLoop (Core) · `map_to_local`/`local_to_map` (Tile) · `Marker2D` (Scn) · `match` (GD) · Material duplication (Shd) · Memory leak (Perf) · Migration chain (Data) · Milestone (PM) · Mipmaps (2D) · `modulate`/`self_modulate` (2D) · Monitors tab (Perf) · MoSCoW (PM) · Mouse passthrough (UI) · `mouse_filter` (Phys) · `move_and_slide()` (Phys) · `Mutex`/`Semaphore` (Core)
- **N** — Navigation layer (Tile) · `NavigationRegion2D`/`Agent2D` (Tile) · Nearest filter (2D) · `NinePatchRect` (UI) · Node (Scn) · Node lifecycle (Scn) · `NodePath` (GD) · Notarization (Exp) · Notification (Core)
- **O** — Object (Core) · Object pooling (Perf) · Offline-first (Data) · One-way collision (Phys) · `@onready` (GD) · Orphan node (Perf) · Outline shader (Shd) · Overdraw (Perf) · Overlay mode (RR) · `owner` (Scn) · `OS` singleton (Core)
- **P** — `PackedScene` (Scn) · Palette swap (Shd) · `Parallax2D` (2D) · `ParallaxBackground` legacy (2D) · PCK file (Exp) · Peering bits (Tile) · `Performance.get_monitor()` (Perf) · Per-pixel transparency (UI) · Physics interpolation 2D (Phys) · Physics layer TileSet (Tile) · Physics tick rate (Phys) · `PhysicsServer2D` (Core) · Pixel snapping (2D) · `PointLight2D` (2D) · Post-mortem (PM) · `PRAGMA user_version` (Data) · Pre-modification checklist (PM) · `preload()` (GD) · Prepared statement (Data) · `_process`/`_physics_process` (Scn) · Profiler (Perf) · `ProjectSettings` (Core) · Property set/get (GD)
- **Q** — `queue_free()` (Scn) · `queue_redraw()` (2D)
- **R** — `RayCast2D`/`ShapeCast2D` (Phys) · rcedit (Exp) · `RefCounted` (Core) · Refactoring (PM) · Regression (PM) · Relax Room (RR) · Release tag (Exp) · `RenderingServer` (Core) · Reparenting (Scn) · Repeat import (2D) · `res://` (Data) · Resource export filters (Exp) · Resource-based save (Data) · `ResourceLoader`/`ResourceSaver` (Data) · `RigidBody2D` (Phys) · Room state (RR)
- **S** — Save schema v4.0.0 (RR) · Save slot (Data) · Scene (Scn) · Scene collection source (Tile) · Scene merge conflict (PM) · Scene root (Scn) · Scene tree (Scn) · Scene-unique name `%` (Scn) · `SceneTree` (Core) · Schema version (Data) · Scope creep (PM) · `SCREEN_UV` (Shd) · Semantic versioning (Exp) · Serialization (Data) · Server architecture (Core) · `set_process(false)` (Perf) · Shader baker 4.5 (Shd) · Shader compilation stutter (Shd) · `ShaderMaterial` (Shd) · `shader_type` (Shd) · `Shortcut` (Phys) · Signal (Scn) · `Signal` type (GD) · Signal bus (Core) · Signals up calls down (Scn) · Singleton (Core) · Size flags (UI) · Smoke test (PM) · Soak test (Perf) · spatial shader (Shd) · `Sprite2D` (2D) · `SpriteFrames` (2D) · Spritesheet (2D) · SQLite (Data) · Staggered map (Tile) · Static function (GD) · Static memory (Perf) · Static typing (GD) · `StaticBody2D` (Phys) · `StatusIndicator` (UI) · `store_var`/`get_var` (Data) · Streak (RR) · Stretch mode (2D) · `StringName` (GD) · `StyleBox` (UI) · `super` (GD) · Supabase (Data) · Sync conflict resolution (Data)
- **T** — Technical debt (PM) · Terrain / terrain set (Tile) · Test double/spy (PM) · `TEXTURE` (Shd) · Texture bleeding (2D) · `TEXTURE_PIXEL_SIZE` (Shd) · `TextureRect` (UI) · Theme / theme override (UI) · Thread guard (Core) · Tile origin (Tile) · Tile source (Tile) · `TileMap` legacy (Tile) · `TileMapLayer` (Tile) · `TileSet` (Tile) · `TIME` (Shd) · `Timer` (Scn) · `@tool` (GD) · Tooltip (UI) · Transaction (Data) · Tray mode (RR) · `.tscn`/`.tres` (Scn) · `Tween` (2D) · Type inference `:=` (GD) · Typed array / dictionary (GD)
- **U** — `.uid` file (Scn) · Uniform (Shd) · Unit test (PM) · `user://` (Data) · `UV` (Shd)
- **V** — Variant (Core) · Varying (Shd) · `velocity` (Phys) · Version control (PM) · Vertical slice (PM) · `vertex()` (Shd) · `Viewport`/`SubViewport` (2D) · VirtIO (RR) · `VisibleOnScreenNotifier2D`/`Enabler2D` (2D) · `VisualShader` (Shd) · Visual Profiler (Perf) · `volume_db` (Aud) · VRAM (Perf) · VSync (Perf)
- **W** — WAL mode (Data) · `@warning_ignore` (GD) · Wav vs Ogg (Aud) · `Window`/`Popup` (UI) · `WorkerThreadPool` (Core)
- **Y** — Y-sort (2D) · `y_sort_origin` (Tile)
- **Z** — `z_index`/`z_as_relative` (2D)

---

*Course: Godot 4 in Production — see [00-SYLLABUS.md](00-SYLLABUS.md) for the module sequence, [00-CAPSTONE.md](00-CAPSTONE.md) for the final project, and [99-EXERCISES/README.md](99-EXERCISES/README.md) for practice.*
