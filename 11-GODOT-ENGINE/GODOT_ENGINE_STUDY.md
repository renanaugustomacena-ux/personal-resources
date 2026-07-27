---
course: "Godot 4 in Production"
phase: "1 — Foundations"
module: "01"
title: "Godot Engine Study — Architecture, GDScript and Core Systems"
version: "Godot 4.5 / GDScript 2.0"
level: "Beginner-Intermediate"
prerequisites:
  - "General programming basics: variables, functions, control flow, basic OOP"
  - "00-SYLLABUS.md — course roadmap and module map"
  - "GAME_DEV_PLANNING.md — project vocabulary (scene, asset, build, runtime)"
objectives:
  - "Explain Godot's layered architecture (OS/DisplayServer, servers, SceneTree) and trace what happens in one frame"
  - "Write idiomatic, statically typed GDScript 2.0 using annotations, lambdas, signals, and await"
  - "Choose correctly between direct calls, signals, and groups, and implement a signal bus autoload"
  - "Model game data with custom Resources and apply preload/load and duplication rules correctly"
  - "Route input through InputMap actions and the correct callback (_input vs _unhandled_input)"
  - "Animate with Tweens using kill/tracking discipline and drive audio through buses with a crossfade"
  - "Diagnose problems with breakpoints, the remote scene tree, the profiler, and Performance monitors"
tags: [godot, gdscript, game-engine, architecture, signals, scene-tree, autoload, resources, input, audio, tweens, debugging]
---

# Godot Engine Study — Architecture, GDScript and Core Systems — Complete Guide

> **Module 01** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [00-SYLLABUS.md](00-SYLLABUS.md) (course roadmap), [GAME_DEV_PLANNING.md](GAME_DEV_PLANNING.md) (project vocabulary), plus general programming basics in any language.
>
> By the end of this module you will be able to:
> 1. Explain Godot's layered architecture — OS/DisplayServer abstraction, servers, SceneTree — and trace the full frame lifecycle including `_process` vs `_physics_process`
> 2. Write idiomatic, statically typed GDScript 2.0: `:=` inference, annotations, first-class functions, lambdas, setters/getters, static members, typed collections
> 3. Declare, emit, connect, and disconnect signals with Callables, `bind()`, and connection flags, and use `await` for coroutines
> 4. Decide between direct calls, signals, and groups; implement and defend a signal bus architecture
> 5. Build custom Resources, explain `preload` vs `load` and resource sharing vs duplication
> 6. Handle input through InputMap actions in the correct callback, lay out UI with anchors and containers, and play audio through buses
> 7. Use Tweens with correct kill/tracking discipline, understand the four 2D physics body types, and profile a running game
>
> **Estimated time:** 8-10 hours reading · 12-16 hours hands-on labs
> **Level:** Beginner-Intermediate

## Guiding ideas

1. **Godot is server-architectured under the hood.** RenderingServer, PhysicsServer2D, AudioServer — your scene tree is a thin, convenient layer above the servers. Knowing this explains both the API design and the performance characteristics.
2. **Signals decouple sender from receiver.** Call down, signal up: a node may call methods on its children, but should report to the rest of the world by emitting signals.
3. **Static typing is not optional in production.** Typed GDScript catches errors at parse time, unlocks full autocompletion, and is measurably faster.
4. **Autoloads are global state — use sparingly and document the init order.** Every autoload is implicit coupling; each one must justify its existence.
5. **Profile before optimizing.** `Performance.get_monitor()` and the profiler tell you where the frame time goes; intuition usually does not.
6. **GDScript is fast enough until proven otherwise.** Only reach for C# or GDExtension when a profile — not a feeling — justifies it.

## Concept map

```
                        ┌────────────────────────────────────────┐
                        │   MODULE 01 — GODOT ENGINE STUDY       │
                        └───────────────────┬────────────────────┘
                                            │
        ┌──────────────────┬────────────────┼───────────────────┬──────────────────┐
        │                  │                │                   │                  │
┌───────▼───────┐  ┌───────▼───────┐ ┌──────▼───────┐  ┌────────▼───────┐ ┌────────▼───────┐
│ ARCHITECTURE  │  │  GDSCRIPT 2.0 │ │ SCENE MODEL  │  │  CORE SYSTEMS  │ │  PRODUCTION    │
│               │  │               │ │              │  │                │ │                │
│ OS layer      │  │ static typing │ │ nodes/scenes │  │ Input actions  │ │ Performance    │
│ DisplayServer │  │ annotations   │ │ instancing   │  │ Control/UI     │ │ monitors       │
│ Servers       │  │ lambdas       │ │ ownership    │  │ Audio buses    │ │ Profiler       │
│ MainLoop      │  │ signals/await │ │ groups       │  │ Tweens/Timers  │ │ Debugger       │
│ SceneTree     │  │ setters/get   │ │ autoloads    │  │ Physics 2D     │ │ Remote tree    │
│ frame cycle   │  │ classes       │ │ resources    │  │ File I/O       │ │ Editor tools   │
│ Object model  │  │ match/enums   │ │ signal bus   │  │                │ │                │
└───────┬───────┘  └───────┬───────┘ └──────┬───────┘  └────────┬───────┘ └────────┬───────┘
        │                  │                │                   │                  │
        └──────────────────┴────────────────┼───────────────────┴──────────────────┘
                                            │
                        ┌───────────────────▼────────────────────┐
                        │  CASE STUDY: RELAX ROOM                │
                        │  desktop companion · 2D · pixel art    │
                        │  SignalBus · AudioManager · autoloads  │
                        └────────────────────────────────────────┘
```

## Table of contents

1. [Overview](#overview)
2. [Engine architecture](#engine-architecture)
3. [The frame lifecycle](#the-frame-lifecycle)
4. [GDScript fundamentals](#gdscript-fundamentals)
5. [Static typing and annotations](#static-typing-and-annotations)
6. [Functions, lambdas and Callables](#functions-lambdas-and-callables)
7. [Signals, await and coroutines](#signals-await-and-coroutines)
8. [Object-oriented GDScript](#object-oriented-gdscript)
9. [Scenes, instancing and groups](#scenes-instancing-and-groups)
10. [Signals as architecture](#signals-as-architecture)
11. [Autoloads](#autoloads)
12. [Resources and file I/O](#resources-and-file-io)
13. [Input handling](#input-handling)
14. [Control and UI essentials](#control-and-ui-essentials)
15. [The audio system](#the-audio-system)
16. [Tweens and timers](#tweens-and-timers)
17. [2D physics introduction](#2d-physics-introduction)
18. [Performance fundamentals](#performance-fundamentals)
19. [Debugging workflow](#debugging-workflow)
20. [Editor productivity](#editor-productivity)
21. [Godot 3 to 4 migration notes](#godot-3-to-4-migration-notes)
22. [Best practices](#best-practices)
23. [Common errors and troubleshooting](#common-errors-and-troubleshooting)
24. [Exercises](#exercises)
25. [Further reading](#further-reading)
26. [Glossary](#glossary)

---

## Overview

Godot is a **free and open-source** game engine released under the MIT license. That single sentence hides three consequences that shape everything else in this course. First, there are **no royalties and no subscription**: whatever you ship, you keep 100% of the revenue, and the engine can never change its terms retroactively on a build you already have. Second, you have the **full source code**, which means that when documentation is ambiguous you can read the actual C++ implementation — a habit worth developing early. Third, the engine is **small**: the editor binary is roughly 100 MB and requires no installation, which matters for this course's target — a lightweight desktop companion application — far more than it would for a AAA production.

Unlike engines that treat 2D as a projection of a 3D world, Godot maintains a **dedicated 2D engine** with its own coordinate system (pixels, y-down), its own renderer, and its own physics server. For pixel-art and interface-heavy projects this is a decisive advantage: there is no camera-perspective bookkeeping, no unit-scale debate, and nearest-neighbor filtering is a project setting away.

### Brief history

| Year | Milestone |
|------|-----------|
| 2007 | Juan Linietsky and Ariel Manzur start developing Godot as an in-house engine |
| 2014 | Open-sourced under the MIT license (v1.0) |
| 2016 | Godot 2.0 — visual scripting, improved 2D workflow |
| 2018 | Godot 3.0 — OpenGL ES 3.0 renderer, PBR, GDNative |
| 2023 | Godot 4.0 — Vulkan renderer, GDScript 2.0, near-complete core rewrite |
| 2024 | Godot 4.3 — TileMapLayer, 2D physics interpolation, major stability work |
| 2025 | Godot 4.4 — typed dictionaries, embedded game window in the editor |
| 2025 | Godot 4.5 — **our pinned version**: abstract classes, variadic functions, accessibility (screen-reader support), shader baker, stencil buffer support |

> ✅ **Best practice** — Pin an exact engine version per project (this course pins **4.5**) and record it in your README and CI. Godot minor versions are generally compatible, but resaved scenes and `.godot` caches are not guaranteed to open in older editors. Upgrading mid-project is a deliberate, tested migration, not an automatic update.

### Binaries, templates and where things live

Practicalities that save first-week confusion. The **editor** download comes in two flavors: *standard* (GDScript + GDExtension) and *.NET* (adds C# — a separate, larger binary requiring the .NET SDK). **Export templates** are a separate download per engine version — the stripped runtime binaries your exported game actually ships with; the editor prompts for them on first export ([BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md)). A **project** is any folder containing `project.godot`; the editor's Project Manager lists known ones. Inside a project, `.godot/` is the regenerable import cache (never committed), and `*.import`/`*.uid` sidecar files are metadata that *is* committed. Nothing installs system-wide: the editor is a single portable executable, which makes pinning versions per project (just keep the old executable) trivial.

### Godot compared with other engines

Understanding what Godot is *not* helps calibrate expectations. This comparison is a snapshot, not a verdict — every row has exceptions.

| Aspect | Godot 4 | Unity | Unreal Engine |
|--------|---------|-------|---------------|
| Language | GDScript, C#, C++ (GDExtension) | C# | C++, Blueprints |
| License | MIT — fully free and open source | Free below a revenue threshold, then fees | Free below $1M revenue, then 5% royalty |
| Editor size | ~100 MB | ~5-10 GB | ~30-50 GB |
| Ideal for | 2D, pixel art, prototypes, indie, tools | 2D/3D, mobile, AR/VR | AAA 3D, photorealism, open worlds |
| Scene model | Node tree, composition of scenes | GameObject + Component | Actor + Component |
| 2D pipeline | Excellent (native, dedicated renderer) | Good (built on the 3D pipeline) | Possible but not the focus |
| Learning curve | Low (GDScript is Python-like) | Medium (C# is powerful but verbose) | High (C++ plus visual scripting) |
| Web export | Supported (HTML5/WASM) | Supported (WebGL) | Limited |
| Source access | Full, MIT | Reference-only source access tiers | Full (custom license) |

### Case study — Relax Room: why Godot?

> This module's running case study is **Relax Room**, a 2D pixel-art desktop companion app (music player, ambience mixer, decoratable room) built for an IFTS project work. Case-study blocks like this one connect the general theory to that concrete project. They are supplementary — the surrounding theory stands on its own.

1. **2D-first design** — Godot's 2D engine is native, not a layer over 3D. A desktop companion never needs a 3D pipeline.
2. **Pixel-art friendly** — built-in nearest-neighbor filtering and integer-scaling options; no shader workarounds needed.
3. **Lightweight** — the exported executable is tens of MB and idles at near-zero CPU with low-processor mode, which is essential for an app that runs *alongside* the user's real work.
4. **GDScript** — Python-like scripting keeps the codebase approachable for students without C#/C++ background.
5. **Signal system** — a built-in observer pattern, which Relax Room extends into a global `SignalBus` autoload (see [Signals as architecture](#signals-as-architecture)).
6. **MIT license** — no cost and no legal constraints for an academic project.
7. **Windowing control** — `DisplayServer` exposes always-on-top, borderless, and per-pixel-transparent windows: exactly the API surface a desktop companion needs.

### The four languages of Godot

Godot exposes four programming surfaces, and a production team should know what each is *for* even when using only one:

| Language | Runs as | Choose it for |
|---|---|---|
| **GDScript** | Bytecode in the engine VM | Gameplay, UI, tools — the default; tightest editor integration, fastest iteration |
| **C#** (.NET builds) | JIT-compiled .NET | Teams with C# background; heavy game logic; large refactorable codebases |
| **C++ via GDExtension** | Native shared library | Performance-critical subsystems, wrapping native libraries — without recompiling the engine |
| **Godot shader language** | GPU programs | All material/visual effects — see [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md) |

The languages interoperate: GDScript can call into C# and GDExtension classes and vice versa, because everything speaks the same `Object`/`Variant` protocol underneath. This course uses **GDScript exclusively** — the correct default until a profiler proves otherwise (Guiding idea 6) — plus the shader language in the rendering modules.

### How this module fits the course

This is the **foundation survey**: it visits every core system once, at working depth, and forward-links the deep dives. You should finish it able to read any GDScript file in the case-study project and explain what each line does. The deep dives are: [SCENES_AND_NODES.md](SCENES_AND_NODES.md) (Module 02, scene tree in depth), [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) (Module 13, autoload discipline), and [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) (Module 14, profiling workflow). Rendering-side material continues in [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md), [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md), and [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md).

---

## Engine architecture

### The layer cake

Godot is built in layers, and almost every "why does the API look like this?" question has its answer in this diagram:

```
┌─────────────────────────────────────────────┐
│           YOUR GAME (GDScript / C#)         │  ← You write code here
├─────────────────────────────────────────────┤
│           SCENE SYSTEM                      │  ← Nodes, Scenes, SceneTree
│           (high-level, convenient API)      │
├─────────────────────────────────────────────┤
│           SERVERS                           │  ← The actual engines
│  RenderingServer  │ PhysicsServer2D/3D      │
│  AudioServer      │ NavigationServer2D/3D   │
│  DisplayServer    │ TextServer / XRServer   │
├─────────────────────────────────────────────┤
│           CORE                              │  ← Memory, math, containers
│  Object │ Variant │ StringName │ Callable   │
├─────────────────────────────────────────────┤
│           OS / PLATFORM LAYER               │  ← Platform abstraction
│  Windows │ macOS │ Linux │ Web │ Android    │
└─────────────────────────────────────────────┘
```

Reading bottom-up: the **OS layer** abstracts the operating system (threads, file paths, environment, process control) behind the `OS` singleton. Since Godot 4, everything related to *display* — windows, monitors, clipboard, cursor, dialogs — was split out of `OS` into its own singleton, **`DisplayServer`**. This split is why Godot 4 can run **headless** (server builds, CI test runs) simply by selecting a `DisplayServer` implementation that renders nothing: the rest of the engine does not know or care.

On top of the platform layer sits the **core**: `Object` (the root of the class hierarchy), `Variant` (the dynamic value container that lets GDScript hold any engine type), `StringName` (interned, cheap-to-compare strings used everywhere the engine compares names), and `Callable` (a first-class reference to a method). Then come the **servers** — the real engines — and only at the top the **scene system** you interact with daily.

### Servers: the real engine

The scene system (nodes and scenes) is technically optional — it is a convenience layer built on top of servers. Every server runs the actual simulation and owns the actual data:

| Server | Responsibility |
|--------|----------------|
| `RenderingServer` | All graphics: canvas items, viewports, materials, shaders, lights |
| `PhysicsServer2D` | 2D collision detection, bodies, areas, joints, raycasting |
| `PhysicsServer3D` | 3D physics (unused in a 2D-only project) |
| `AudioServer` | Audio buses, effects, mixing, master volume |
| `DisplayServer` | Windows, monitors, screen info, clipboard, mouse cursor, dialogs |
| `NavigationServer2D` | Pathfinding, navigation meshes, agent avoidance |
| `TextServer` | Font shaping, BiDi, complex script layout |
| `XRServer` | AR/VR interfaces (unused here) |

When you create a `Sprite2D` node, the node is a thin wrapper: in `_enter_tree()` it registers a *canvas item* with `RenderingServer` and forwards property changes to it via an RID (resource ID) handle. You could bypass nodes entirely and talk to servers directly — creating thousands of canvas items with `RenderingServer.canvas_item_create()` is a legitimate optimization for particle-like workloads — but for ordinary development, nodes buy you the tree, lifecycle callbacks, the editor, and serialization.

```gdscript
# The node-free way to draw a sprite — you will (almost) never do this,
# but seeing it once demystifies what Sprite2D actually is.
func _ready() -> void:
	var canvas_item: RID = RenderingServer.canvas_item_create()
	# Parent it to this node's canvas so it renders in our tree's context.
	RenderingServer.canvas_item_set_parent(canvas_item, get_canvas_item())
	var texture: Texture2D = preload("res://assets/icon.svg")
	RenderingServer.canvas_item_add_texture_rect(
		canvas_item,
		Rect2(Vector2.ZERO, texture.get_size()),
		texture.get_rid()
	)
```

> ⚠️ **Pitfall** — Server resources created manually (RIDs) are **not** garbage collected. Anything you `*_create()` on a server you must free with `RenderingServer.free_rid()` (and equivalents) or it leaks for the lifetime of the process. This is the main reason to stay on the node layer until profiling says otherwise.

Not everything global is a server. Godot also exposes plain **engine singletons** — `Engine`, `OS`, `Time`, `Input`, `InputMap`, `ProjectSettings`, `ResourceLoader`, `ResourceSaver`, `Performance`, `Marshalls` — which are utility interfaces rather than simulation engines. The distinction matters when reading docs: servers own state you can manipulate by RID; singletons are mostly stateless helpers or settings registries.

### The OS and DisplayServer split

In Godot 3 a single `OS` singleton handled both operating-system services and windowing. Godot 4 splits it:

| Concern | Godot 4 API |
|---------|-------------|
| Time and dates | `Time.get_ticks_msec()`, `Time.get_datetime_dict_from_system()` |
| Environment, paths, processes | `OS.get_environment()`, `OS.get_user_data_dir()`, `OS.execute()` |
| Windows and monitors | `DisplayServer.window_set_position()`, `DisplayServer.screen_get_size()` |
| Clipboard | `DisplayServer.clipboard_set()`, `DisplayServer.clipboard_get()` |
| Window flags | `DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, true)` |
| Power state | `OS.get_processor_name()`, `DisplayServer.screen_get_refresh_rate()` |

### Case study — Relax Room: DisplayServer as a product feature

For a desktop companion, `DisplayServer` is not plumbing — it *is* the product's window behavior. Relax Room uses:

```gdscript
# window_manager.gd — desktop-companion window setup (Godot 4.5 API).
extends Node

func _ready() -> void:
	# Keep the room floating above other applications.
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, true)
	# Borderless: the room's own pixel-art frame acts as the chrome.
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, true)
	# Restore last window position from the save file (fall back to centered).
	var saved_pos: Vector2i = SaveManager.get_window_position()
	if saved_pos != Vector2i(-1, -1):
		DisplayServer.window_set_position(saved_pos)

func _notification(what: int) -> void:
	# The user clicked the OS close button: persist window state first.
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		SaveManager.set_window_position(DisplayServer.window_get_position())
		SaveManager.save_game()
		get_tree().quit()
```

Per-pixel window transparency (a companion character floating on the desktop with no visible window) additionally requires the project settings `display/window/per_pixel_transparency/allowed = true` plus a transparent viewport background, and the `WINDOW_FLAG_TRANSPARENT` flag. The same feature exists as properties on the root `Window` node (`get_window().always_on_top`, `.borderless`, `.transparent`) — the node properties and the DisplayServer calls manipulate the same underlying state.

### Beyond one window

Godot 4 windows are nodes: the root is a `Window`, and *additional* `Window` (or `Popup`/`PopupPanel`/`AcceptDialog`) nodes in the tree become real OS windows — native multi-window support that Godot 3 lacked and desktop apps love:

```gdscript
var settings_window := Window.new()
settings_window.title = "Relax Room — Settings"
settings_window.size = Vector2i(420, 520)
settings_window.transient = true          # stays above its parent window
settings_window.exclusive = false         # true = modal (blocks parent input)
settings_window.close_requested.connect(settings_window.hide)   # X hides, not frees
add_child(settings_window)
settings_window.popup_centered()
```

Embedded vs native: with `display/window/subwindows/embed_subwindows` enabled (the default), sub-windows render *inside* the main window as lightweight embedded panels — fine for games; disable it for a desktop companion that wants genuine OS windows the user can drag to a second monitor. The dialog conveniences (`AcceptDialog`, `ConfirmationDialog`, `FileDialog` — including native OS file pickers via `use_native_dialog`) are pre-assembled `Window` subclasses worth reaching for before hand-rolling.

### The Object class hierarchy

Everything scriptable in Godot descends from `Object`. The first fork in the hierarchy is the single most important design decision in the engine's memory model:

```
Object                        ← manual memory management (free())
├── RefCounted                ← automatic: freed when last reference dies
│   └── Resource              ← RefCounted + path + serialization (.tres/.res)
│       ├── Texture2D, AudioStream, PackedScene, Theme, Shader, ...
│       └── YourCustomResource (extends Resource)
│
└── Node                      ← manual: freed by parent, or queue_free()
    ├── CanvasItem            ← abstract base of everything drawn in 2D
    │   ├── Node2D            ← 2D transform (position, rotation, scale, skew)
    │   │   ├── Sprite2D, AnimatedSprite2D, Camera2D, TileMapLayer
    │   │   ├── CharacterBody2D, RigidBody2D, StaticBody2D, Area2D
    │   │   └── ...
    │   └── Control           ← UI: anchors, focus, themes
    │       ├── Button, Label, HSlider, TextEdit, ...
    │       └── Container → VBoxContainer, HBoxContainer, GridContainer, ...
    ├── Node3D                ← 3D branch (unused in this course)
    ├── CanvasLayer           ← independent 2D render layer (HUD)
    ├── Timer, AudioStreamPlayer, HTTPRequest, AnimationPlayer
    └── Window                ← the SceneTree root is a Window
```

Two reading rules for this tree. First, **`CanvasItem` is where 2D drawing lives**: `visible`, `modulate`, `z_index`, `material`, and the `draw()` API are defined there, which is why both `Node2D` (game objects) and `Control` (UI) can draw, tint, and sort. Second, **`Node2D` vs `Control` is a transform-model split**: `Node2D` positions itself with a free 2D transform; `Control` positions itself with anchors and offsets relative to its parent. Mixing them carelessly (a `Control` inside a deep `Node2D` rig, or vice versa) works but usually signals a design smell.

### RefCounted vs Node: two memory models

Godot deliberately has **no garbage collector**. Instead it uses two explicit ownership models, and knowing which one applies to an object is the difference between a leak-free app and a slowly bloating one.

**`RefCounted` (and everything under it, including all `Resource` types)** is reference-counted. Every variable holding the object increments a counter; when the counter reaches zero, the object frees itself immediately and deterministically. You never call `free()` on a `RefCounted`.

```gdscript
func parse_config() -> Dictionary:
	var json := JSON.new()          # JSON extends RefCounted
	json.parse(FileAccess.get_file_as_string("user://config.json"))
	return json.data                # `json` goes out of scope here → freed. No cleanup code.
```

**`Node` (and raw `Object`)** is manually managed. A node is freed in exactly three ways: its parent is freed (freeing cascades down the tree), you call `free()` on it (immediate — dangerous mid-frame), or you call `queue_free()` (freed safely at the end of the current frame). Removing a node from the tree does **not** free it:

```gdscript
func detach_panel(panel: Control) -> void:
	remove_child(panel)   # panel still exists in memory, just parentless.
	# If nothing keeps a reference and you never re-add or free it,
	# it is now an ORPHAN NODE — a leak.

func close_panel(panel: Control) -> void:
	panel.queue_free()    # freed at end of frame; children freed with it.
```

> ⚠️ **Pitfall** — `queue_free()` does not null out your variables. After the end of the frame, any stored reference to the freed node becomes a dangling "previously freed instance". Guard with `is_instance_valid(node)` before use, and prefer setting your own references to `null` right after queueing the free.

> ⚠️ **Pitfall** — Two `RefCounted` objects referencing each other form a **cycle** that reference counting cannot collect. Break cycles by storing one side as a `weakref(obj)` (returns a `WeakRef`; call `.get_ref()` to access, which returns `null` once the target died).

The debugging aids for this model are built in: the **Monitors** tab exposes `Performance.OBJECT_ORPHAN_NODE_COUNT`, and calling the static `Node.print_orphan_nodes()` at runtime lists every node that exists outside the tree — run it before quitting during development and treat any non-zero output as a bug.

> ✅ **Best practice** — Decide the owner of every dynamically created node at creation time. The idiom `add_child(thing)` immediately after `Scene.instantiate()` is not just convenience: it hands lifetime responsibility to the tree, so freeing the parent scene cleans up everything.

### Where Resource sits

`Resource` extends `RefCounted` and adds three things: a `resource_path` (its identity on disk), serialization to `.tres`/`.res`, and engine-wide **caching** — loading the same path twice returns the *same instance*. This combination is why resources behave like shared data blocks while nodes behave like unique live objects. The full consequences (sharing, duplication, `resource_local_to_scene`) are covered in [Resources and file I/O](#resources-and-file-io).

---

## The frame lifecycle

### MainLoop and SceneTree

When the Godot binary starts, it initializes the OS layer, the servers, and then hands control to a `MainLoop` — an object with one job: be called every iteration until it says "quit". You could implement `MainLoop` yourself (some tool scripts do), but in every normal project the main loop is **`SceneTree`**: the `MainLoop` subclass that owns the node tree, dispatches lifecycle callbacks, delivers input, propagates pause state, and manages groups. `get_tree()` from any node returns it.

The `SceneTree` root is not your scene — it is a `Window` (the OS window). Your "main scene", every autoload, and any extra windows are children of that root:

```
SceneTree
└── root (Window)
    ├── AutoloadA          ← autoloads first, in project.godot order
    ├── AutoloadB
    └── Main               ← get_tree().current_scene
        └── ... your game
```

### One frame, step by step

Every iteration of the main loop performs, in order:

```
┌──────────────────────────────────────────────────────────────┐
│                        ONE FRAME                             │
│                                                              │
│  1. INPUT                                                    │
│     OS events → Window → _input() → GUI → _shortcut_input()  │
│     → _unhandled_key_input() → _unhandled_input()            │
│                                                              │
│  2. PHYSICS STEP(S) — fixed timestep, default 60 Hz          │
│     0..N iterations to catch up with wall-clock time:        │
│       _physics_process(delta)   (delta is CONSTANT: 1/60)    │
│       PhysicsServer2D step: integrate, detect, resolve       │
│       physics signals fire (body_entered, area_exited, ...)  │
│                                                              │
│  3. IDLE / PROCESS — variable timestep                       │
│       _process(delta)           (delta VARIES per frame)     │
│       Timers, Tweens (idle-mode), animation advance          │
│                                                              │
│  4. RENDER                                                   │
│       RenderingServer draws canvas items (z-sorted),         │
│       compositing of viewports and CanvasLayers              │
│                                                              │
│  5. AUDIO / SWAP                                             │
│       AudioServer mixes buses; frame is presented            │
└──────────────────────────────────────────────────────────────┘
```

The key subtlety is step 2's "0..N iterations". The physics step runs on a **fixed timestep** (`Engine.physics_ticks_per_second`, project setting `physics/common/physics_ticks_per_second`, default 60). If rendering slows down to 30 FPS, each rendered frame runs *two* physics ticks so simulation time keeps up with wall-clock time; if you render at 144 FPS, most rendered frames run *zero* physics ticks. This decoupling is what makes physics deterministic regardless of rendering performance — and it is also why physics-visible movement done in `_process` stutters.

### _process vs _physics_process

```gdscript
func _process(delta: float) -> void:
	# Runs once per RENDERED frame. `delta` is the real elapsed time
	# (≈0.0166 s at 60 FPS, ≈0.033 s at 30 FPS) — always multiply by it.
	_update_parallax(delta)
	_advance_ui_animations(delta)

func _physics_process(delta: float) -> void:
	# Runs at the fixed physics rate. `delta` is constant (1.0/60 by default).
	velocity = _input_direction() * speed
	move_and_slide()
```

| | `_process(delta)` | `_physics_process(delta)` |
|--|--|--|
| Frequency | Every rendered frame | Fixed rate (60 Hz default) |
| `delta` | Varies with frame rate | Constant (`1.0 / ticks_per_second`) |
| Use for | Visuals, UI, camera smoothing, non-physics motion | Anything touching physics: bodies, raycasts, `move_and_slide()` |
| Runs when paused? | Only if `process_mode` allows | Only if `process_mode` allows |

> ⚠️ **Pitfall** — Reading physics state (raycasts, `is_on_floor()`, overlap queries) from `_process` gives you *last tick's* results and can tear within a frame. Query physics only in `_physics_process`. Conversely, moving a `Camera2D` in `_physics_process` while sprites move per-frame produces judder — either enable 2D **physics interpolation** (project setting `physics/common/physics_interpolation`, Godot 4.3+) or drive the camera in `_process`.

Frame-rate context is available everywhere: `Engine.get_frames_per_second()` (smoothed FPS), `Engine.get_process_frames()` / `Engine.get_physics_frames()` (frame counters, useful to make something run every Nth frame), and `Engine.max_fps` to cap rendering.

### Disabling and prioritizing callbacks

Every node with a `_process` or `_physics_process` implementation is called every frame even if the body does nothing useful — the call itself has a cost across thousands of nodes. Processing is toggleable per node, and ordering is controllable:

```gdscript
func _ready() -> void:
	set_process(false)            # stop _process being called
	set_physics_process(false)    # stop _physics_process
	process_priority = -10        # lower value runs EARLIER among siblings
	process_physics_priority = 0  # same idea for the physics callback

func wake_up() -> void:
	set_process(true)
```

> ✅ **Best practice** — Event-driven beats polled. A desktop companion that redraws only when a signal reports a change (track changed, decoration placed) can keep `_process` disabled on almost every node, which is a large part of how Relax Room idles near 0% CPU. Combine with `OS.low_processor_usage_mode = true` (see [Performance fundamentals](#performance-fundamentals)).

### SceneTree timing utilities

The tree exposes its own heartbeat as signals — the building blocks of frame-precise coordination:

```gdscript
await get_tree().process_frame       # resume next idle frame — "wait one frame"
await get_tree().physics_frame       # resume at the next physics tick

# Why "wait one frame" is a real tool and not a hack — three legitimate uses:
# 1. You just add_child()-ed something and need its layout computed (Controls
#    report real sizes only after a frame).
# 2. You changed a physics property and want queries to see it (server state
#    syncs at the next physics step).
# 3. You are spreading heavy setup across frames to avoid a hitch:
func build_room_incrementally(items: Array[DecorationData]) -> void:
	for i in items.size():
		_place(items[i])
		if i % 10 == 9:                        # 10 placements per frame
			await get_tree().process_frame
```

The tree also emits `node_added(node)` / `node_removed(node)` (the hook auto-wiring systems use to notice, say, every new `AudioStreamPlayer`) and `tree_changed`. Use these sparingly — they fire for *every* node — but know they exist: they are how plugins observe the world without polluting your scripts.

### Notifications: the low-level event stream

Beneath the named callbacks sits a raw channel: every `Object` receives integer **notifications**, and `_ready`/`_process` are really just sugar over them. You tap the stream by overriding `_notification()` — necessary for window/application events that have no dedicated virtual method:

```gdscript
func _notification(what: int) -> void:
	match what:
		NOTIFICATION_WM_CLOSE_REQUEST:          # user clicked the OS close button
			_save_and_quit()
		NOTIFICATION_APPLICATION_FOCUS_OUT:     # app lost focus → low-power mode
			Engine.max_fps = 10
		NOTIFICATION_APPLICATION_FOCUS_IN:
			Engine.max_fps = 30
		NOTIFICATION_WM_MOUSE_ENTER:            # pointer entered our window
			_character.wave()
		NOTIFICATION_PREDELETE:                 # last chance before memory is freed
			pass                                # (object is being destructed — keep it trivial)
```

| Notification | Fires when |
|---|---|
| `NOTIFICATION_WM_CLOSE_REQUEST` | OS window close button / Alt+F4 |
| `NOTIFICATION_APPLICATION_FOCUS_IN` / `_OUT` | App gains/loses focus (any window) |
| `NOTIFICATION_WM_WINDOW_FOCUS_IN` / `_OUT` | This specific window gains/loses focus |
| `NOTIFICATION_WM_MOUSE_ENTER` / `_EXIT` | Pointer enters/leaves the window |
| `NOTIFICATION_PAUSED` / `NOTIFICATION_UNPAUSED` | Tree pause state changes |
| `NOTIFICATION_TRANSFORM_CHANGED` | Global transform changed (opt-in: `set_notify_transform(true)`) |
| `NOTIFICATION_PREDELETE` | Object about to be destroyed |

For a desktop companion the focus pair is a *product feature* (drop to a 10 FPS cap when unfocused — see [Performance fundamentals](#performance-fundamentals)), and `WM_CLOSE_REQUEST` is the save-on-exit hook. By default closing the window quits automatically; set `get_tree().set_auto_accept_quit(false)` to intercept and quit manually after cleanup.

### Pause semantics

`get_tree().paused = true` suspends processing tree-wide, but each node decides how to react through `process_mode`:

| `process_mode` value | Behavior while tree is paused |
|---|---|
| `PROCESS_MODE_INHERIT` (default) | Do what the parent does |
| `PROCESS_MODE_PAUSABLE` | Stop (the default effective behavior) |
| `PROCESS_MODE_WHEN_PAUSED` | Run **only** while paused (pause menus) |
| `PROCESS_MODE_ALWAYS` | Run regardless (music, network) |
| `PROCESS_MODE_DISABLED` | Never run |

A pause menu is therefore just a `CanvasLayer` with `process_mode = PROCESS_MODE_WHEN_PAUSED` whose "Resume" button sets `get_tree().paused = false`. Note that pausing suspends `_process`, `_physics_process`, and input callbacks — but **not** signal emission or manual method calls, and audio keeps playing unless you route it through a pausable node.

### Engine.time_scale

`Engine.time_scale` multiplies the delta fed to both process callbacks and to physics tick scheduling — `0.5` is slow motion, `2.0` is fast-forward. Tweens follow it unless created with `set_ignore_time_scale(true)`; `Time.get_ticks_msec()` ignores it entirely (it is wall-clock). Use it for game feel, never as a pause substitute (`time_scale = 0` starves physics and can wedge `await`-based logic).

---

## GDScript fundamentals

### What GDScript is

GDScript is Godot's built-in scripting language: Python-like in surface syntax, but statically analyzable, compiled to bytecode at load time, and designed around the engine's object model — every script *is* a class that extends an engine type. Compared to Python, there are no modules-as-files semantics (a file is a class, not a namespace), no exceptions (errors are values and `push_error` calls), and whitespace is significant but tabs are the convention.

The language identity of this course: **GDScript 2.0** — the redesign that shipped with Godot 4.0 and has since gained static variables and `_static_init()` (4.1), pattern guards in `match` (4.3), typed dictionaries (4.4), and `@abstract` classes plus variadic functions (4.5).

### Null, Variant and defensive boundaries

Untyped GDScript variables hold a `Variant` — a tagged union fitting any engine type, including `null`. Typed object variables may *also* be `null` (there are no non-nullable references), so boundary code checks:

```gdscript
var maybe_node := get_node_or_null("Optional/Panel")   # typed Node, possibly null
if maybe_node == null:
	return

var data: Variant = JSON.parse_string(text)            # null on parse failure!
if data == null or not data is Dictionary:
	push_warning("Malformed payload, ignoring")
	return
var dict := data as Dictionary                          # now safe to narrow

typeof(data) == TYPE_DICTIONARY                         # int-constant type test
```

Three null-related rules from the style guides worth internalizing: prefer meaningful defaults over null (`Vector2.ZERO`, empty arrays, `&""`) so most code never branches on null at all; check `null` and `is_instance_valid()` as *distinct* questions (a variable can hold a non-null reference to a freed object); and confine `Variant`-typed variables to the parse-and-validate edge — the interior of the program should be fully typed.

### Anatomy of a script

The official style guide prescribes an exact ordering of declarations inside a script. Follow it mechanically — consistent structure is what makes a 40-file project navigable:

```gdscript
@tool                              # 1. file-level annotations (@tool, @icon)
@icon("res://icons/relax.svg")
class_name AmbienceToggle          # 2. global class name (optional)
extends Control                    # 3. base class — every script has one

## A toggle row for one ambience loop (rain, fireplace, birds...).
## Double-hash comments are docstrings: they show in the editor help.  # 4. docs

signal toggled_on(ambience_id: String)      # 5. signals

enum Category { NATURE, INDOOR, WEATHER }   # 6. enums

const FADE_TIME: float = 0.4                # 7. constants

static var active_count: int = 0            # 8. static variables

@export var ambience_id: String = ""        # 9. exports
@export var category: Category = Category.NATURE

var is_active: bool = false                 # 10. public variables

var _fade_tween: Tween                      # 11. private (by convention: _prefix)

@onready var _label: Label = $HBox/Label    # 12. @onready variables

func _init() -> void: pass                  # 13. methods: _init, _ready,
func _ready() -> void: pass                 #     virtual callbacks,
func toggle() -> void: pass                 #     public methods,
func _apply_fade(on: bool) -> void: pass    #     private methods
```

Naming conventions, verbatim from the official style guide: files `snake_case.gd`, classes `PascalCase`, functions and variables `snake_case`, private members `_leading_underscore`, constants `CONSTANT_CASE`, enum names `PascalCase` with `CONSTANT_CASE` members, signals `snake_case` **in past tense** (`door_opened`, not `open_door` — a signal reports a fact, it does not command an action). Booleans read as predicates: `is_active`, `has_focus`, `can_drop`.

### Documentation comments

Lines starting with `##` are **doc comments**: placed above a class declaration, a member, or a signal, they feed the editor's built-in class reference (`F1`) and the hover tooltips — your own classes get first-class documentation next to the engine's.

```gdscript
## Manages the dual-player music crossfade.
##
## Call [method crossfade_to] to change tracks; volume is controlled through
## the [code]Music[/code] bus, not per-player. Emits [signal track_started].
class_name MusicDirector
extends Node

## Emitted after the incoming track begins (before the fade completes).
signal track_started(track_id: StringName)

## Seconds a full crossfade takes. Clamped to 0.1 on assignment.
@export var fade_time: float = 1.0
```

The bracket tags (`[method x]`, `[signal x]`, `[code]...[/code]`, `[b]`, `[param name]`) cross-link inside the help viewer. Two habits make this pay off: document *why and contract*, not the restated signature; and write the class-level comment first — it forces you to state the class's single responsibility, and classes that resist a one-paragraph summary are usually two classes.

### Variables and core types

```gdscript
# Primitives
var lives: int = 3                 # 64-bit integer
var speed: float = 120.0           # 64-bit float
var paused: bool = false
var title: String = "Relax Room"

# Godot math types (structs — copied on assignment, not referenced)
var pos: Vector2 = Vector2(64, 32)      # 2D float vector
var cell: Vector2i = Vector2i(4, 7)     # 2D integer vector (grid coords)
var tint: Color = Color(1.0, 0.8, 0.8)  # RGBA, also Color.RED, Color("#ff8080")
var area: Rect2 = Rect2(0, 0, 320, 180) # position + size
var xform: Transform2D                   # 2D affine matrix

# Identity types
var action: StringName = &"toggle_music"   # interned string, O(1) compare
var target: NodePath = ^"UI/Panel/Label"   # path literal

# Reference types (assignment shares, does not copy)
var stats: Dictionary = {"plays": 0, "favorites": []}
var tracks: Array[String] = ["forest.ogg", "rain.ogg"]
```

The struct/reference split above is a classic trap for Python developers: `Vector2`, `Color`, `Rect2` and friends are **value types** — `var b := a` copies — while `Array`, `Dictionary`, and all `Object`-derived types are **reference types** — `var b := a` aliases. Related trap: mutating a returned struct member does nothing.

```gdscript
position.x += 10.0          # OK — compound assignment on a property is special-cased
var p := position
p.x += 10.0                 # modifies the COPY, not the node
get_parent().position.x = 5 # ⚠ works in GDScript, but read the docs note on
                            #   value types when doing this through untyped Variants
```

### Control flow

```gdscript
# if / elif / else — parentheses optional, indentation is the block
if energy <= 0.0:
	_enter_sleep_mode()
elif energy < 0.25:
	_show_low_energy_hint()
else:
	_continue_idle_animation()

# Ternary expression (Python-style)
var label_text := "playing" if player.playing else "stopped"

# while
while _pending_jobs.size() > 0:
	_run_job(_pending_jobs.pop_back())

# for — over ranges, arrays, dictionaries (keys), strings (chars)
for i in range(3):              # 0, 1, 2
	print(i)
for i in 3:                     # shorthand for range(3)
	print(i)
for track in tracks:            # over array elements
	print(track)
for key in stats:               # over dictionary KEYS
	print(key, " = ", stats[key])
for i in range(10, 0, -2):      # 10, 8, 6, 4, 2
	print(i)

# break / continue work as in Python
```

### Operators and expressions

Arithmetic is Python-like with a few engine-specific edges worth committing to memory:

```gdscript
var q := 7 / 2            # 3   — int / int is INTEGER division!
var f := 7.0 / 2.0        # 3.5 — make one operand float for real division
var r := 7 % 3            # 1   — % is for ints only…
var fr := fmod(7.5, 2.0)  # 1.5 — …floats use fmod()
var pw := 2 ** 10         # 1024 — power operator (GDScript 2.0)
var neg := -7 % 3         # -1  — sign follows the dividend; for always-positive
var wrap := posmod(-7, 3) # 2   — wrapping (grid/ring indices), use posmod/fposmod

# Compound assignment: += -= *= /= %= **= &= |= <<= …
# Bitwise: & | ^ ~ << >>  — collision masks, flags enums.
var mask := (1 << 2) | (1 << 4)

# Logical: prefer the word forms — they read better and short-circuit identically.
if is_open and not is_locked: pass          # `and`, `or`, `not` (or &&, ||, !)

# Membership and type tests:
if "volume" in settings: pass               # Dictionary: tests KEYS
if track_id in owned_tracks: pass           # Array/String: tests contents
if node is Button: pass                     # type test; `is not` also exists
var b := node as Button                     # safe cast: null if incompatible
```

> ⚠️ **Pitfall** — Integer division silently truncates: `passed / total` for two ints is `0` for any partial progress, which then renders a progress bar stuck at zero. Any ratio, percentage, or average must promote to float first: `float(passed) / total`.

### Vector2 survival kit

`Vector2` carries most 2D gameplay math. Remember the coordinate system: **x grows right, y grows down**, so `Vector2.UP` is `(0, -1)` and positive angles rotate *clockwise* — both are consequences of screen-space convention, and both trip up everyone once.

```gdscript
var v := Vector2(3.0, 4.0)

v.length()                    # 5.0 — magnitude (involves sqrt)
v.length_squared()            # 25.0 — cheap; use for comparisons
v.normalized()                # (0.6, 0.8) — unit vector; ZERO stays ZERO
a.distance_to(b)              # scalar distance between points
a.direction_to(b)             # unit vector from a toward b — THE chase idiom
a.dot(b)                      # projection: >0 same-facing, 0 perpendicular, <0 opposed
v.angle()                     # radians from +x axis (clockwise-positive, y-down!)
v.rotated(deg_to_rad(90.0))   # rotated copy
a.lerp(b, 0.25)               # 25% of the way from a to b
v.move_toward(target, 4.0)    # step toward target by AT MOST 4 px — no overshoot
v.limit_length(100.0)         # clamp magnitude (max speed caps)
v.snapped(Vector2(16, 16))    # snap to a grid — decoration placement!

Vector2.ZERO  Vector2.ONE  Vector2.UP  Vector2.DOWN  Vector2.LEFT  Vector2.RIGHT
```

Two idioms cover most movement code. **Chase**: `velocity = global_position.direction_to(target) * speed`. **Arrive without jitter**: `global_position = global_position.move_toward(target, speed * delta)` — `move_toward` stops exactly at the target instead of oscillating around it, which naive `+= direction * speed * delta` does.

Use `Vector2i` for anything that is conceptually a grid cell (tile coords, pixel-perfect window sizes): it never accumulates float drift, and comparing `Vector2i`s for equality is exact — comparing `Vector2`s should go through `is_equal_approx()`.

### Math helpers and randomness

```gdscript
# Interpolation & mapping — the global function family:
lerpf(a, b, t)                     # a + (b-a)*t  (also lerp() for vectors/colors)
inverse_lerp(a, b, value)          # which t would produce `value`?
remap(v, 0.0, 100.0, -80.0, 0.0)   # map a range onto another — slider→dB in one call
clampf(v, 0.0, 1.0)                # also clampi, clamp (Variant)
wrapf(angle, 0.0, TAU)             # wrap into a ring; wrapi for ints
snappedf(v, 0.25)                  # quantize to steps
move_toward(current, target, max_step)
is_equal_approx(a, b)              # float equality done right
is_zero_approx(v)

# Frame-rate-independent smoothing (exponential decay) — the correct version of
# the old "lerp with 0.1 every frame" trick, stable at ANY frame rate:
func _process(delta: float) -> void:
	var t := 1.0 - exp(-SMOOTH_SPEED * delta)      # SMOOTH_SPEED ≈ 5..15
	camera.position = camera.position.lerp(target.position, t)
```

Randomness has two tiers. Global convenience functions share one internal generator (auto-seeded at startup):

```gdscript
randf()                        # 0.0..1.0
randf_range(-3.0, 3.0)         # float in range
randi_range(1, 6)              # inclusive int — dice
randfn(0.0, 1.0)               # normal distribution (mean, deviation)
tracks.pick_random()           # random Array element
tracks.shuffle()               # in-place shuffle
seed(12345)                    # deterministic runs (tests, replays)
```

When a system needs *its own* reproducible stream (procedural room decoration that must not change when unrelated code consumes randomness), instantiate `RandomNumberGenerator`, give it a stored `seed`, and draw only from it. That isolation is the difference between "same seed, same room, forever" and "the room reshuffles because the menu animation rolled a die first".

### Time

```gdscript
Time.get_ticks_msec()                  # ms since engine start — durations, cooldowns
Time.get_ticks_usec()                  # µs precision — micro-benchmarks
Time.get_unix_time_from_system()       # wall-clock epoch seconds (float)
Time.get_datetime_dict_from_system()   # {year, month, day, hour, minute, second, …}
Time.get_datetime_string_from_system() # ISO-ish "2026-07-27T14:03:22"
```

`Time` is wall-clock and ignores `Engine.time_scale` and pause; `delta` accumulation respects them. Pick the one matching your intent: gameplay cooldowns usually want accumulated delta (they should freeze with pause); autosave timestamps and log lines want `Time`.

### Error handling without exceptions

GDScript has **no exceptions** — no `try`/`catch`, no `raise`. Errors are values, and the engine's convention is the global `Error` enum: functions that can fail return `OK` (which is `0`) or a specific error code, and *your* code's job is to check.

```gdscript
var err := DirAccess.make_dir_recursive_absolute("user://saves")
if err != OK:
	push_error("Could not create save dir: %s" % error_string(err))  # readable name
	return

# The composite idiom for functions that must return data OR failure:
# 1) sentinel returns (null / empty) plus a pushed error…
func load_catalog(path: String) -> Dictionary:      # {} means "failed" here
	if not FileAccess.file_exists(path):
		push_error("Catalog missing: %s" % path)
		return {}
	...

# 2) …or a result dictionary when the caller must distinguish failure kinds:
func import_track(path: String) -> Dictionary:
	if not path.get_extension() in ["ogg", "wav", "mp3"]:
		return {"ok": false, "reason": "unsupported_format"}
	...
	return {"ok": true, "track_id": id}
```

The consequences of "errors are values" are cultural as much as technical: **check return codes** (raise the `return_value_discarded` warning and the compiler nags you), **fail loudly at the source** (`push_error` where the failure is detected, not three layers up where the null finally explodes), and **make invalid states unrepresentable** where possible — a typed parameter, a clamped setter, or an `@abstract` contract prevents the error instead of reporting it. `assert()` complements the enum: error codes are for *expected* failures (missing file, bad input); assertions are for *impossible* ones (programmer bugs).

### match — structural pattern matching

`match` is Godot's `switch`, but it matches *patterns*, not just constants. It compares the subject against each branch top-to-bottom and runs the first match; there is no fallthrough.

```gdscript
enum State { IDLE, WALKING, SITTING, SLEEPING }
var state: State = State.IDLE

func _physics_process(delta: float) -> void:
	match state:
		State.IDLE:
			_play_idle(delta)
		State.WALKING, State.SITTING:      # multiple values, one branch
			_play_active(delta)
		_:                                  # wildcard = default branch
			_play_sleep(delta)
```

Beyond constants, patterns can destructure arrays and dictionaries and bind variables:

```gdscript
func handle_command(cmd: Array) -> void:
	match cmd:
		["play"]:
			AudioManager.resume()
		["play", var track]:                    # binds second element to `track`
			AudioManager.play_track(track)
		["volume", var v] when v is float:      # guard clause (Godot 4.3+)
			AudioManager.set_volume_linear(v)
		["seek", var seconds, ..]:              # `..` = "and any further elements"
			AudioManager.seek(seconds)
		{"action": "quit"}:                     # dictionary pattern (subset match)
			get_tree().quit()
		_:
			push_warning("Unknown command: %s" % [cmd])
```

> ⚠️ **Pitfall** — A bare identifier in a pattern is a **binding**, not a comparison: `match x:` / `some_name:` always matches and *creates* a variable `some_name`. To compare against a variable's value, wrap the logic in a guard (`_ when x == some_name:`) or use constants/enum members, which are matched by value.

### Strings and formatting

GDScript has no f-strings; the two workhorses are `%` formatting and `String.format()`:

```gdscript
var track := "Forest Dawn"
var pos := 72.5
var length := 180.0

# printf-style: %s any value, %d int, %f float, %.1f precision, %% literal percent
var status := "%s — %.0f/%.0f s (%d%%)" % [track, pos, length, int(pos / length * 100)]

# Named placeholders: readable for UI templates and localization glue
var msg := "{track} · {artist}".format({"track": track, "artist": "Unknown"})

# Useful String API (all methods return NEW strings — String is immutable)
"  hi  ".strip_edges()          # "hi"
"a,b,,c".split(",", false)      # ["a", "b", "c"]  (false = skip empty)
"res://audio/rain.ogg".get_file()          # "rain.ogg"
"res://audio/rain.ogg".get_basename()      # "res://audio/rain"
"rain.OGG".get_extension().to_lower()      # "ogg"
"track_%02d" % 7                # "track_07" — zero-padded numbering
"Relax Room".to_snake_case()    # "relax_room" — handy in tool scripts
var n := "42".to_int()          # parsing; also to_float(), is_valid_int()
```

Use `String` for text you display and manipulate; use `StringName` (`&"jump"`) for identifiers compared frequently — action names, group names, animation names. The engine interns `StringName`s so comparison is pointer equality, and most engine APIs that take names accept them directly.

### Arrays and dictionaries (untyped view)

```gdscript
var mixed: Array = [1, "two", Vector2.ONE]      # Variant array — allowed, discouraged
mixed.append(4)
mixed.erase("two")               # removes first matching VALUE
mixed.remove_at(0)               # removes by INDEX
var last = mixed.pop_back()      # remove + return last (fast); pop_front() is O(n)
print(mixed.has(4), " ", mixed.find(4))         # membership / index-of

var settings: Dictionary = {
	"volume": 0.8,
	"muted": false,
	"last_track": "rain.ogg",
}
settings["muted"] = true
var vol: float = settings.get("volume", 1.0)    # with default — never crashes
settings.erase("last_track")
if settings.has("volume"): pass                 # or: if "volume" in settings

# Iteration order of Dictionary is INSERTION order (guaranteed).
for key in settings:
	print(key, ": ", settings[key])
```

The typed versions of both — `Array[T]` and `Dictionary[K, V]` — are covered in the next section, and in production code they are the default. Alongside general arrays, the `Packed*Array` family (`PackedByteArray`, `PackedFloat32Array`, `PackedVector2Array`, `PackedStringArray`, ...) stores raw contiguous data with much lower memory overhead — the engine uses them for geometry, audio buffers, and file APIs, and you should use them for large homogeneous datasets.

> ✅ **Best practice** — `Array.duplicate()` and `Dictionary.duplicate()` are **shallow** by default. Pass `true` (`duplicate(true)`) to deep-copy nested containers. Forgetting this is a classic source of "changing one saved room mutated all rooms" bugs.

---

## Static typing and annotations

### Why typed GDScript

GDScript is gradually typed: untyped code runs, but every production script in this course is fully typed. The reasons are concrete, not stylistic:

1. **Parse-time errors.** A typo like `positon` in untyped code explodes at runtime, possibly minutes into a play session; typed code refuses to compile.
2. **Real autocompletion.** The editor can only suggest members if it knows the type. Typed code turns the script editor from a text box into an IDE.
3. **Performance.** The bytecode compiler emits specialized, faster instructions for typed operations — typed hot loops are measurably quicker.
4. **Self-documentation.** `func fade(target_db: float, duration: float) -> void` needs no comment to explain its contract.

### The three forms

```gdscript
var a: float = 120.0     # explicit type + value
var b: float             # explicit type, default zero-value (0.0)
var c := 120.0           # INFERRED type — reads the type from the value

func damage(amount: int) -> void:      # typed parameter, typed return
	health -= amount

func peak_db() -> float:               # return type is part of the signature
	return _current_peak
```

Use `:=` whenever the right-hand side makes the type obvious (`:= Vector2.ZERO`, `:= []` does *not* — that infers plain `Array`). Use explicit annotations when the value alone is ambiguous or when you intentionally want a wider type (`var node: Node = $Sprite2D`).

> ⚠️ **Pitfall** — `var speed := 100` infers **int**, and later `speed = 100.5` is a compile error (or worse, a silent truncation when passed onward). Write `100.0` for floats, always. Related: `@export var volume := 0.0` exports a float; `:= 0` exports an int with an integer-only inspector field.

Casting and runtime checks:

```gdscript
var item := scene.instantiate()               # inferred as Node
var button := item as Button                  # cast: null if incompatible (safe)
if item is Button:                            # type test
	(item as Button).disabled = true
var forced: Button = item                     # implicit downcast: RUNTIME ERROR if wrong

@warning_ignore("unused_parameter")           # silence a specific warning, one statement
func _on_tab_changed(tab: int) -> void:
	pass
```

Project-wide, open **Project Settings → Debug → GDScript** and raise `untyped_declaration` (and friends) from *Ignore* to *Warn* or *Error* — this is how a team enforces "typed everywhere" mechanically instead of by review comments. The warnings that matter most for a typed codebase:

| Warning setting | Catches |
|---|---|
| `untyped_declaration` | Any `var x = ...` without a type or `:=` |
| `inferred_declaration` | (Optional, stricter teams) every `:=` — forces explicit types |
| `unsafe_property_access` / `unsafe_method_access` | Member access on a `Variant`/untyped value |
| `unsafe_cast` | Casts the checker cannot prove |
| `return_value_discarded` | Ignoring a return value (e.g. an `Error` code!) |
| `integer_division` | The silent `7 / 2 == 3` truncation |
| `unused_parameter` / `unused_variable` | Dead code and typo'd names |
| `shadowed_variable` | Local hiding a member — a classic silent bug |

The pragmatic production baseline: `untyped_declaration`, `unsafe_*`, `integer_division`, and `shadowed_variable` as **errors**; the rest as warnings. Silence individual justified cases with `@warning_ignore("...")` at the statement — never by lowering the project setting.

### Typed collections

```gdscript
var tracks: Array[AudioStream] = []            # element type enforced on write
var owned_ids: Array[int] = [1, 4, 9]
var by_id: Dictionary[String, TrackData] = {}  # typed dictionary — Godot 4.4+

tracks.append(preload("res://audio/rain.ogg")) # OK
# tracks.append("rain.ogg")                    # parse/runtime error: wrong element type

# Typed arrays give typed iteration for free:
for t in tracks:
	print(t.get_length())                      # `t` is known to be AudioStream
```

Two facts worth memorizing. First, **array covariance is not a thing**: `Array[Node2D]` is not assignable to `Array[Node]`; use `Array[Node]` from the start or convert explicitly with `Array(nodes, TYPE_OBJECT, "Node", null)`-style constructions only when you truly must. Second, `.duplicate()` on a typed array preserves the element type, but JSON round-trips do not — everything parsed from JSON comes back as untyped `Array`/`Dictionary` with `float` numbers, so re-validate at the boundary.

### The annotation catalogue

Annotations are compiler directives prefixed with `@`. They replaced several Godot 3 keywords (`export`, `onready`, `tool`) and grew into a small language of their own. The ones you will actually use:

| Annotation | Effect |
|---|---|
| `@export` | Show the variable in the Inspector; serialized with the scene |
| `@export_range(min, max, step)` | Numeric slider with bounds |
| `@export_enum("A", "B")` | Dropdown of named values (stores int or String) |
| `@export_flags("Fire", "Ice")` | Bitmask checkboxes |
| `@export_file("*.json")` / `@export_dir` | File/directory picker (res:// paths) |
| `@export_global_file("*.png")` | Picker for absolute filesystem paths |
| `@export_multiline` | Multi-line text box for Strings |
| `@export_placeholder("id...")` | Placeholder text in the field |
| `@export_color_no_alpha` | Color picker without alpha channel |
| `@export_node_path("Sprite2D")` | NodePath picker restricted to a type |
| `@export_group("Motion")` / `@export_subgroup` / `@export_category` | Inspector organization |
| `@export_custom(...)` | Manual property hint control (4.3+) |
| `@export_storage` | Serialized but hidden from the Inspector (4.3+) |
| `@export_tool_button("Bake")` | Inspector button bound to a Callable (4.4+, `@tool` scripts) |
| `@onready` | Defer initialization until just before `_ready()` |
| `@tool` | Run this script inside the editor too |
| `@icon("res://icon.svg")` | Editor icon for a `class_name` |
| `@abstract` | Abstract class/method — cannot instantiate / must override (4.5+) |
| `@warning_ignore("...")` | Suppress one named warning for the next statement |
| `@static_unload` | Allow static variables to be released with the script |
| `@rpc(...)` | Multiplayer RPC configuration (out of scope here) |

### @export in practice

`@export` is the bridge between code and the Inspector — it is how designers (or you, wearing the designer hat) tune values without touching scripts, and how scenes persist per-instance configuration.

```gdscript
extends Node2D
class_name Decoration

@export_category("Decoration")
@export var display_name: String = ""
@export_multiline var description: String = ""

@export_group("Placement")
@export_enum("floor", "wall", "table") var placement: String = "floor"
@export_range(0.5, 2.0, 0.05) var scale_factor: float = 1.0

@export_group("Economy")
@export var price: int = 100
@export var unlocked_by_default: bool = false

# Godot 4 can export object references directly:
@export var icon: Texture2D            # drag a texture from the FileSystem dock
@export var placement_sound: AudioStream
@export var linked_light: Node2D       # drag a NODE from the scene dock (4.0+)
```

Exporting a typed `Resource` subclass (`@export var data: TrackData`) gives you an *inline editable* resource in the Inspector — the foundation of data-driven design covered in [Resources and file I/O](#resources-and-file-io).

> ⚠️ **Pitfall** — Exported values saved in a scene **override** the script's default. If you change the default in the script and nothing happens in-game, the scene stored the old value: right-click the property in the Inspector → *Revert*, or click the ↺ arrow. This bites everyone at least once.

### @onready and node references

`@onready var x := $Path` is sugar for assigning in `_ready()`: the expression runs after the node's children exist, so `$` lookups are safe.

```gdscript
@onready var _sprite: AnimatedSprite2D = $Body/AnimatedSprite2D
@onready var _label: Label = %TrackLabel      # % = scene-unique node, see below
@onready var _bus_index: int = AudioServer.get_bus_index(&"Music")

func _ready() -> void:
	_sprite.play(&"idle")     # safe: @onready ran just before _ready()
```

`$Path/To/Node` is shorthand for `get_node("Path/To/Node")` and resolves *relative to this node*, which makes it brittle under refactoring: rename or move a child and every `$` referencing it breaks at runtime. The **scene-unique name** feature fixes the fragility: right-click a node in the Scene dock → *Access as Unique Name* → reference it as `%TrackLabel` from anywhere inside the same scene, independent of its position in the hierarchy.

> ✅ **Best practice** — Order of preference for node references: `%UniqueName` inside a scene, `@export var node: NodeType` across scene boundaries (drag-assigned in the editor), and raw `$paths` only for stable, shallow, obviously-local children. Never reach *upward* with `get_parent().get_parent()` — that inverts the ownership direction and breaks reuse (see [Signals as architecture](#signals-as-architecture)).

### @tool scripts

`@tool` at the top of a script makes it execute in the editor. This is how gizmos, in-editor previews, and procedural placement work — and it is also how an innocent script wipes data at design time, so treat it with respect.

```gdscript
@tool
extends Node2D

@export var radius: float = 48.0:
	set(value):
		radius = value
		queue_redraw()          # editor updates live as you drag the slider

func _draw() -> void:
	draw_circle(Vector2.ZERO, radius, Color(0.4, 0.8, 1.0, 0.3))

func _process(delta: float) -> void:
	if Engine.is_editor_hint():
		return                  # guard: skip game-only logic while in the editor
	_game_only_update(delta)
```

`Engine.is_editor_hint()` is the standard guard separating editor behavior from runtime behavior inside a `@tool` script. More editor tooling (EditorScript, EditorPlugin) is covered in [Editor productivity](#editor-productivity).

---

## Functions, lambdas and Callables

### Function declarations

```gdscript
# Fully typed signature: parameter types + return type. -> void = returns nothing.
func fade_to(target_db: float, duration: float = 0.5) -> void:
	pass

# Return values
func linear_volume() -> float:
	return db_to_linear(_volume_db)

# Static functions belong to the class, not an instance — pure helpers.
static func format_time(seconds: float) -> String:
	var m := int(seconds) / 60
	var s := int(seconds) % 60
	return "%d:%02d" % [m, s]

# Variadic functions (Godot 4.5+): the rest-parameter collects extra args
# into an Array. Useful for logger-style APIs.
func log_all(level: String, ...parts: Array) -> void:
	print(level, ": ", " ".join(parts.map(func(p): return str(p))))
```

Default parameter values are evaluated per call, and optional parameters must come last. There is no function overloading in GDScript — one name, one signature — so idiomatic APIs use optional parameters or differently named functions (`play()`, `play_at(position)`).

### Callables: functions as values

Every function reference in Godot 4 is a `Callable` — a first-class value bundling an object and a method (or a lambda). This is the type that powers signal connections, `Array.map/filter/sort_custom`, deferred calls, and tween callbacks.

```gdscript
var c: Callable = format_time          # method reference — no parentheses!
print(c.call(93.0))                    # "1:33"  — invoke
c.call_deferred(93.0)                  # invoke at end of frame
var bound := c.bind(42.0)              # pre-fill arguments (appended at call time)
bound.call()                           # same as format_time(42.0)

# Callable utilities you will actually use:
c.is_valid()                           # object alive and method exists?
c.get_object()                         # the bound instance
Callable(self, "format_time")          # explicit construction (string name)
```

`bind()` **appends** its arguments after whatever the call site provides — crucial for signals: if a signal emits `(a, b)` and you connected `handler.bind(c)`, the handler receives `(a, b, c)`. Its mirror `unbind(n)` *discards* the last `n` call-site arguments before invoking — the standard trick when connecting an argument-emitting signal to a zero-argument method.

### Lambdas

Lambdas are anonymous functions declared inline; they produce Callables and may capture local variables.

```gdscript
# Expression-style
var double := func(x: int) -> int: return x * 2
print(double.call(21))          # 42

# Block-style (multi-line body) — note the trailing comma-free syntax
var announce := func(track: String) -> void:
	print("Now playing: ", track)
	SignalBus.track_started.emit(track)

# The killer app: inline signal handlers and functional array ops
button.pressed.connect(func() -> void: _open_panel(&"shop"))

var names: Array[String] = ["rain", "fire", "birds"]
var upper := names.map(func(n: String) -> String: return n.to_upper())
var short := names.filter(func(n: String) -> bool: return n.length() <= 4)
var total := [1, 2, 3].reduce(func(acc: int, x: int) -> int: return acc + x, 0)

# sort_custom takes a "less than" predicate:
tracks.sort_custom(func(a: TrackData, b: TrackData) -> bool:
	return a.title.naturalnocasecmp_to(b.title) < 0)
```

> ⚠️ **Pitfall** — Lambdas capture local variables **by value at creation time**. Mutating the outer local afterwards does not affect the captured copy, and mutating the copy inside the lambda does not write back. If you need shared mutable state, capture a *reference type* (an Array, Dictionary, or object) and mutate its contents — or better, restructure to avoid shared state.

```gdscript
var count := 0
var bump := func() -> void:
	# count += 1        # ⚠ this modifies a captured COPY — outer `count` stays 0
	pass

var box := {"count": 0}          # reference type: capture works as expected
var bump_ok := func() -> void:
	box["count"] += 1
```

> ✅ **Best practice** — Use lambdas for three-line-or-shorter glue (a button opening a panel). The moment a lambda needs a name to explain itself, promote it to a private method: named methods are debuggable (they appear in stack traces and the profiler by name) and disconnectable individually.

---

## Signals, await and coroutines

### Declaring and emitting

Signals are Godot's built-in observer pattern: a node announces *that something happened*, and any number of listeners react, without the emitter knowing who they are.

```gdscript
extends Node
class_name MusicPlayerCore

signal track_started(track_id: String)          # typed parameters (documented
signal track_finished(track_id: String)         # in the editor's help panel)
signal volume_changed(linear: float)
signal playlist_ended                            # no parameters

func play(track_id: String) -> void:
	_load_and_start(track_id)
	track_started.emit(track_id)                 # first-class emission

func _on_stream_finished() -> void:
	track_finished.emit(_current_id)
	if _queue.is_empty():
		playlist_ended.emit()
```

In Godot 4, a declared signal is a real member of type `Signal` — you can pass it around, store it, and connect to it through a variable. Emission is synchronous: `emit()` calls every connected Callable *immediately, in connection order*, before the next line of the emitter runs. This synchronicity is what makes signals predictable — and what makes a slow handler the emitter's problem.

> ⚠️ **Pitfall** — Synchronous emission enables **re-entrancy**: if a handler for `coins_changed` calls something that changes coins again, you are emitting *inside* the previous emission — handlers observe values out of order, and a careless cycle recurses until the stack dies. Defenses: setters that early-out on no-change (shown in [Object-oriented GDScript](#object-oriented-gdscript)), never mutating the emitting system from its own handler, and `CONNECT_DEFERRED` on the connection that closes a loop — deferral breaks the cycle by postponing the handler to idle time.

### Connecting and disconnecting

```gdscript
func _ready() -> void:
	# 1. The standard form: connect a method reference.
	player.track_started.connect(_on_track_started)

	# 2. With extra bound arguments (appended after the signal's own args).
	for i in _ambience_buttons.size():
		_ambience_buttons[i].pressed.connect(_on_ambience_pressed.bind(i))

	# 3. Lambda for trivial glue.
	quit_button.pressed.connect(func() -> void: get_tree().quit())

	# 4. Connection flags.
	player.track_finished.connect(_advance_queue, CONNECT_DEFERRED)  # run at frame end
	boss.defeated.connect(_roll_credits, CONNECT_ONE_SHOT)           # auto-disconnect after 1 call

func _exit_tree() -> void:
	# Only needed for connections to OUTSIDE this branch (e.g. autoloads):
	if SignalBus.room_changed.is_connected(_on_room_changed):
		SignalBus.room_changed.disconnect(_on_room_changed)

func _on_track_started(track_id: String) -> void:
	_label.text = GameManager.get_track_title(track_id)

func _on_ambience_pressed(index: int) -> void:   # `index` arrived via bind()
	_toggle_ambience(index)
```

Connection flags worth knowing: `CONNECT_DEFERRED` (handler runs at idle time instead of mid-emission — the standard fix when a handler must modify the scene tree), `CONNECT_ONE_SHOT` (disconnects itself after the first delivery), `CONNECT_PERSIST` (serialized with the scene — what editor-made connections use), `CONNECT_REFERENCE_COUNTED` (allows stacking duplicate connections).

> ⚠️ **Pitfall** — Connecting the same Callable to the same signal twice without `CONNECT_REFERENCE_COUNTED` is a runtime error ("signal is already connected"). It typically appears when `_ready()`-style setup runs again after a scene re-enters the tree. Either connect in `_ready()` (which runs once per node lifetime), guard with `is_connected()`, or disconnect in `_exit_tree()`.

**Automatic cleanup rule:** when either endpoint of a connection is freed, the connection is severed automatically. This means node-to-sibling connections need no manual disconnect. The dangerous direction is connecting to something that outlives you **while passing a lambda**: an anonymous lambda cannot be looked up later with `is_connected(_method)` — hold the Callable in a variable if you will ever need to disconnect it.

### Designing signal payloads

A signal's parameter list is an API contract; design it like one.

**Send the facts, not the object graph.** `track_started(track_id: String)` beats `track_started(player_node)`: listeners get exactly what the event *means*, cannot reach into the emitter's internals, and the payload survives serialization into logs. If listeners routinely need more, send more fields — or a small typed `Resource`/`RefCounted` payload object when the tuple grows past three-ish values.

**Include the "old" value when transitions matter.** `state_changed(from: State, to: State)` lets listeners react to *edges* ("just fell asleep") without keeping shadow copies of the emitter's state — the shadow copy is a desynchronization bug waiting for its moment.

**Granularity: one signal per fact.** Prefer `coins_changed(total)`, `decoration_placed(id, pos)` over a generic `something_changed(kind: String, data: Dictionary)`. The generic bus-within-a-signal loses typing, autocompletion, and greppability — the three reasons signals beat string events in the first place. The symmetric failure is signal-per-micro-detail (`coin_added`, `coin_removed`, `coins_reset`) when every listener treats them identically; merge until each signal has at least one listener that cares about the distinction.

### Editor connections vs code connections

The Node dock's *Signals* tab can wire connections visually; they are stored in the `.tscn` and appear in code as auto-named handlers (`_on_button_pressed`). Editor connections are fine for UI scenes where the connection is part of the scene's identity. Prefer code connections when the target is decided at runtime, when you need `bind()`, or when the connection crosses scene boundaries — code is greppable, scene files are less so.

### await: coroutines on top of signals

`await` suspends the current function until a signal fires (or until an awaited coroutine returns), then resumes on the next line. Any function containing `await` becomes a **coroutine**; execution up to the first `await` is synchronous.

```gdscript
func play_intro_sequence() -> void:
	_fade_overlay.visible = true
	var tween := create_tween()
	tween.tween_property(_fade_overlay, "modulate:a", 0.0, 1.0)
	await tween.finished                          # suspend until the tween ends

	await get_tree().create_timer(0.5).timeout    # one-shot delay, no Timer node
	await get_tree().process_frame                # "wait one frame" idiom

	_character.play_entrance()
	await _character.entrance_finished            # wait for a custom signal
	SignalBus.intro_completed.emit()
```

Awaiting a coroutine composes naturally, and calling a coroutine *without* `await` is legal fire-and-forget (it runs until its first suspension and control returns to you):

```gdscript
func _ready() -> void:
	await _load_catalogs()        # sequential: wait for it
	_build_ui()                   # runs only after catalogs are loaded

func _on_button_pressed() -> void:
	_flash_feedback()             # fire-and-forget coroutine: intentionally not awaited
```

> ⚠️ **Pitfall** — If the object whose signal you are awaiting is freed before emitting, the coroutine is silently abandoned: every line after the `await` never runs. Symptoms are "my function stops halfway with no error". Defensive patterns: await signals of objects you own; re-validate state after every `await` (`if not is_instance_valid(target): return`); and remember that even `self` may have been freed while suspended.

> ⚠️ **Pitfall** — `await` does not create a thread and does not run anything "in the background". It is cooperative single-threaded suspension: the rest of the game continues frame by frame, and your function resumes on the emitting frame. CPU-heavy work still blocks the frame regardless of `await`; true parallelism needs `Thread` or `WorkerThreadPool` (out of scope for this module).

A frequent composition question: *how do I await either of two signals?* There is no built-in `select`; the idiom is a small relay — connect both signals with `CONNECT_ONE_SHOT` to a local lambda that emits one custom signal, and await that. If you find yourself needing this often, your flow probably wants a state machine instead of coroutines.

The most common instance of "either of two" is *signal or timeout*, and it deserves its own helper:

```gdscript
## Awaits `sig` but gives up after `timeout` seconds. Returns true if the
## signal fired, false on timeout. (Declared in a shared utility class.)
static func await_with_timeout(sig: Signal, timeout: float, tree: SceneTree) -> bool:
	var done := {"fired": false}                       # reference type: lambda-writable
	var relay := func() -> void: done["fired"] = true
	sig.connect(relay, CONNECT_ONE_SHOT)
	var timer := tree.create_timer(timeout)
	while not done["fired"] and timer.time_left > 0.0:
		await tree.process_frame
	if sig.is_connected(relay):
		sig.disconnect(relay)
	return done["fired"]
```

Real uses in a desktop app: waiting for a cloud-sync reply that may never come, or for an animation that a skip button may cancel. The polling loop costs one boolean check per frame for the duration — negligible — and reads far more honestly than the callback pyramid it replaces.

### Signal API reference table

| Operation | Syntax |
|---|---|
| Declare | `signal changed(value: int)` |
| Emit | `changed.emit(42)` |
| Connect | `obj.changed.connect(_on_changed)` |
| Connect with flags | `obj.changed.connect(_on_changed, CONNECT_ONE_SHOT)` |
| Connect with extra args | `obj.changed.connect(_on_changed.bind(id))` |
| Disconnect | `obj.changed.disconnect(_on_changed)` |
| Query | `obj.changed.is_connected(_on_changed)`, `obj.changed.get_connections()` |
| Await | `await obj.changed` |
| Await + capture args | `var value = await obj.changed` (single arg; multiple args arrive as an Array) |
| Dynamic (by name) | `obj.connect("changed", _on_changed)` — avoid; loses compile-time checking |

---

## Object-oriented GDScript

### Every script is a class

A `.gd` file *is* a class: `extends` names its base (defaulting to `RefCounted` if omitted), and the optional `class_name` registers it as a global type usable anywhere without `preload` — in type annotations, in `is`/`as` checks, and in the editor's "Create Node"/"Create Resource" dialogs.

```gdscript
class_name Ambience
extends Node

## One looping ambience layer (rain, fireplace...). Docstring lines starting
## with ## appear in the editor's class reference for this class.

var _player: AudioStreamPlayer

func _init() -> void:
	# Constructor: runs on .new() / instantiate(), BEFORE entering the tree.
	# No scene access here — the node has no parent and no tree yet.
	_player = AudioStreamPlayer.new()

func _ready() -> void:
	add_child(_player)
```

`_init()` is the constructor and may take parameters — but note that scenes instantiate scripts with no arguments, so parameterized `_init` is only usable for classes you construct manually with `MyClass.new(args)`. Node setup that needs the tree belongs in `_enter_tree()` or `_ready()`, never `_init()`.

### Inheritance

```gdscript
# panel_base.gd — shared behavior for all four Relax Room panels.
class_name PanelBase
extends PanelContainer

signal opened
signal closed

var is_open: bool = false

func open() -> void:
	is_open = true
	visible = true
	_on_open()                 # extension hook for subclasses
	opened.emit()

func _on_open() -> void:
	pass                       # default: nothing. Subclasses override.


# music_panel.gd
class_name MusicPanel
extends PanelBase              # extends a script class, not just an engine class

func _on_open() -> void:
	super()                    # call the base implementation (here a no-op)
	_refresh_track_list()
```

`super()` calls the same-named method of the base class; `super.some_method()` calls a *different* base method. One engine-specific rule surprises newcomers: if you override a lifecycle callback like `_ready()` in a subclass, the base class's `_ready()` is **not** called automatically — call `super()` yourself when the base has setup logic.

Since Godot 4.5, contracts can be made explicit with `@abstract`:

```gdscript
@abstract
class_name SaveableSystem
extends Node

@abstract func collect_save_data() -> Dictionary   # no body allowed
@abstract func apply_save_data(data: Dictionary) -> void

func save_key() -> String:                          # concrete members mix freely
	return String(name).to_snake_case()
```

Attempting `SaveableSystem.new()` is now a compile-time error, as is a subclass that forgets to implement `collect_save_data()`. Before 4.5 the convention was a base method containing `push_error("override me")` — you will still see that pattern in older codebases.

### Properties: setters and getters

Godot 4 attaches accessors directly to the variable declaration. The crucial mechanic: **inside** `set`/`get`, the bare variable name accesses the backing storage directly (no recursion); **everywhere else** — including other methods of the same class and the Inspector — assignment goes through the setter.

```gdscript
signal energy_changed(value: float)

var max_energy: float = 100.0

var energy: float = 100.0:
	set(value):
		var clamped := clampf(value, 0.0, max_energy)
		if is_equal_approx(clamped, energy):
			return                      # no-op writes don't spam the signal
		energy = clamped                # direct write to backing field — no recursion
		energy_changed.emit(energy)
	get:
		return energy

# Derived, storage-less property: define only `get`.
var energy_ratio: float:
	get:
		return energy / max_energy
```

This pattern — clamp, early-out on no-change, emit — is the idiomatic "reactive property" and pairs perfectly with UI: a `ProgressBar` connects once to `energy_changed` and never polls.

> ⚠️ **Pitfall** — Setters run during scene loading too: when a saved scene restores an `@export` property, your setter executes *before* `_ready()`, possibly before `@onready` variables exist. Guard tree-touching setters with `if not is_node_ready(): return` (and re-apply the value in `_ready()`), or keep setters pure (no node access).

### Static members

```gdscript
class_name IdGenerator
extends RefCounted

static var _next_id: int = 0          # static variable (Godot 4.1+): per-script, not per-instance

static func next() -> int:
	_next_id += 1
	return _next_id

static func _static_init() -> void:   # runs once when the class is first loaded
	_next_id = 1000
```

Static state lives on the script itself and survives as long as the script stays loaded. Use it for stateless helpers and cheap counters — not as a poor man's autoload: statics have no lifecycle callbacks, no signals of their own, and no place in the remote scene tree, which makes them invisible to most debugging tools. If it holds *game state*, make it an autoload (see [Autoloads](#autoloads)).

### Enums

```gdscript
enum PlaybackState { STOPPED, PLAYING, PAUSED }         # 0, 1, 2
enum Layer { FLOOR = 1, WALL = 2, TABLE = 4 }           # explicit values (bit flags)

var state: PlaybackState = PlaybackState.STOPPED        # enum-typed variable

func describe() -> String:
	# An enum is really a Dictionary constant: name → int.
	# find_key() reverse-maps a value to its name — handy for logs and saves.
	return PlaybackState.find_key(state)                # "STOPPED"

@export var initial_state: PlaybackState                # Inspector shows a dropdown
```

Enums are `int`-backed, which has a serialization consequence: if you save raw enum ints and later reorder members, old saves silently mean different things. Persist the *name* (`find_key`) or freeze explicit values, and never reorder a shipped enum.

### Inner classes

A script may define named classes inside itself with `class` — useful for small data carriers scoped to one system:

```gdscript
extends Node

class QueueEntry:
	var track_id: String
	var requested_by: String
	func _init(id: String, by: String = "user") -> void:
		track_id = id
		requested_by = by

var _queue: Array[QueueEntry] = []

func enqueue(id: String) -> void:
	_queue.append(QueueEntry.new(id))
```

The moment an inner class is needed by a second file, promote it to its own script with `class_name` — or, if it is pure data you want editable in the Inspector, to a custom `Resource` (next section but one).

### Duck typing and safe calls

GDScript retains dynamic escape hatches for boundary code — plugin systems, loosely coupled interactions:

```gdscript
if body.has_method("interact"):
	body.interact()                       # duck typing: "if it quacks"

var maybe := node.get("health")           # property by name, null if absent
node.set("health", 50)                    # set by name (no-op if absent)
node.call_deferred("rebuild")             # deferred call by name
```

These bypass the type checker; contain them at boundaries and convert to typed calls (`if body is Interactable:`) as soon as a real class or `@abstract` base can express the contract.

### Two recurring state patterns

Before leaving OOP, two micro-patterns appear in virtually every Godot project — learn them as vocabulary.

**The enum state machine.** When an object has modes with different per-frame behavior, reach for an enum + `match` before anything fancier:

```gdscript
enum State { IDLE, WALKING, SITTING, SLEEPING }

var _state: State = State.IDLE

func _physics_process(delta: float) -> void:
	match _state:
		State.IDLE:      _tick_idle(delta)
		State.WALKING:   _tick_walking(delta)
		State.SITTING:   _tick_sitting(delta)
		State.SLEEPING:  _tick_sleeping(delta)

func _change_state(next: State) -> void:
	if next == _state:
		return
	_exit_state(_state)          # centralized transitions = one place to debug,
	_state = next                # one place to log, one place to emit
	_enter_state(next)
	SignalBus.character_state_changed.emit(State.find_key(next))
```

The crucial discipline is the single `_change_state()` funnel — scattered `_state = X` assignments are how impossible-state bugs are born. When states multiply and carry their own data, the pattern graduates to node-based state machines (one child node per state) — a Module 02 topic.

**The dirty flag.** Expensive work (saving, rebuilding a UI list, re-sorting) triggered by frequent events should coalesce: mark, then act once.

```gdscript
var _dirty: bool = false

func _on_anything_changed() -> void:      # cheap: called dozens of times/second is fine
	_dirty = true

func _on_autosave_timer_timeout() -> void:   # every 30 s
	if _dirty:
		save_game()                          # expensive: runs at most once per tick
		_dirty = false
```

Relax Room's `SaveManager` is exactly this: every bus event marks dirty; a 30-second `Timer` (plus `NOTIFICATION_WM_CLOSE_REQUEST`) performs the actual disk write. The same shape with `call_deferred` instead of a Timer coalesces *within one frame*: mark dirty, `_rebuild.call_deferred()`, and guard the rebuild with the flag so ten changes in one frame rebuild once.

### Introspection and metadata

Every `Object` carries a small reflective toolkit that production code leans on for debugging, serialization, and editor tooling:

```gdscript
node.get_class()                       # "CharacterBody2D" — the ENGINE class,
                                       #   NOT your class_name (a known gotcha)
node is Decoration                     # the correct way to test script classes
node.get_script()                      # the attached Script resource (or null)

# Metadata: ad-hoc key/values serialized with the node/resource. Handy for
# editor-assigned tags without subclassing; visible under Inspector → Metadata.
node.set_meta(&"placed_by_user", true)
if node.get_meta(&"placed_by_user", false):    # second arg = default
	pass

# Custom debug representation — what print(obj) and the debugger show:
func _to_string() -> String:
	return "<Decoration %s at %s>" % [display_name, global_position]
```

Use metadata for *incidental* annotations (editor bookkeeping, migration flags). The moment logic branches on a meta key in more than one file, that key is an undeclared property — promote it to a real (typed, discoverable, autocompleted) variable.

---

## Scenes, instancing and groups

> This is the working overview; [SCENES_AND_NODES.md](SCENES_AND_NODES.md) (Module 02) covers scene composition patterns, ownership subtleties, and editable children in depth.

### What a scene is

A **scene** is a reusable tree of nodes saved as a `.tscn` file (text) or `.scn` (binary). Loaded into memory it becomes a `PackedScene` — a `Resource` describing nodes, properties, and internal connections — and calling `instantiate()` stamps out a fresh, independent node tree from that description. If nodes are LEGO bricks, scenes are pre-built kits: design the "ambience toggle row" once, instantiate it fourteen times.

```gdscript
const TOGGLE_SCENE := preload("res://scenes/ui/ambience_toggle.tscn")

func _build_rows(catalog: Array[Dictionary]) -> void:
	for entry in catalog:
		var row := TOGGLE_SCENE.instantiate() as AmbienceToggle
		row.ambience_id = entry["id"]         # configure BEFORE adding: _ready()
		_list.add_child(row)                  # fires during add_child()
		row.toggled_on.connect(_on_ambience_toggled)
```

Note the ordering comment: `add_child()` triggers `_enter_tree()` and (once all children enter) `_ready()` on the instance. Any configuration the instance needs during `_ready()` must be assigned *before* `add_child()` — a top-five rookie bug.

### The scene tree at runtime

All instantiated scenes form one tree under the root `Window`. Changing "the current scene" swaps one branch:

```gdscript
get_tree().change_scene_to_file("res://scenes/main/main.tscn")   # by path
get_tree().change_scene_to_packed(MAIN_SCENE)                    # by PackedScene
get_tree().reload_current_scene()                                # restart branch
get_tree().current_scene                                         # the active root branch
```

`change_scene_to_*` is deferred: the old scene is freed and the new one added at the end of the frame, so code after the call still runs in the old scene. Autoloads, being children of root rather than of the current scene, survive the swap — that is precisely their job.

### Scene inheritance

Besides *instancing* a scene inside another, a scene can *inherit* one (Scene menu → New Inherited Scene, or right-click a scene file): the child scene starts as a live view of the base — same nodes, same scripts — and records only its **differences** (overridden properties, added nodes). Change the base and every inherited scene updates. It is the scene-level analogue of class inheritance, and the same design advice applies: superb for genuine "is-a" families sharing structure (Relax Room's four panels inherit `panel_base.tscn` for frame, margins, and close button), fragile when used to dodge composition — deleting a base node that inherited scenes rearranged is a classic source of broken-scene errors. Prefer instancing (composition) by default; inherit when the *shape itself* is the shared thing.

### Node lifecycle

```
scene.instantiate() / Node.new()
        │  _init()                 ← constructor; NOT in tree
        ▼
add_child(node)
        │  _enter_tree()           ← parent first, then children
        │  (children all enter and become ready)
        ▼
        │  _ready()                ← CHILDREN FIRST, then parent; runs ONCE
        ▼
   per frame: _process / _physics_process / input callbacks
        ▼
remove_child(node) or queue_free()
        │  _exit_tree()            ← children first, then parent
        ▼
queue_free() → freed at end of frame
```

Two ordering facts do a lot of work. `_enter_tree()` runs **parent-first** — a parent can prepare context for children. `_ready()` runs **children-first** — by the time a parent's `_ready()` executes, `$Child` references are fully initialized, which is why `@onready` and signal wiring belong there. `_ready()` fires only once per node lifetime; if a node re-enters the tree after being removed (not freed), only `_enter_tree()` runs again — use `request_ready()` to force another `_ready()`.

### Ownership and `owner`

Every node has an `owner` — the scene root it "belongs to". The editor sets it automatically; it determines which nodes get saved when the scene is packed. This matters the day you build trees in code and try to save them:

```gdscript
func save_room_as_scene(root: Node2D, path: String) -> Error:
	for child in root.get_children():
		child.owner = root                 # without this, pack() skips the child!
	var packed := PackedScene.new()
	var err := packed.pack(root)
	if err != OK:
		return err
	return ResourceSaver.save(packed, path)
```

Instanced sub-scenes appear as a single sealed node in the parent scene (their internals owned by their own scene file) — the encapsulation that makes scene composition safe. "Editable Children" pierces it in the editor; treat that as a last resort.

### Navigating the tree: the query API

The complete toolbox for locating nodes, ordered from "use freely" to "justify yourself":

| Call | Cost | Notes |
|---|---|---|
| `%UniqueName` | O(1)-ish | Scene-scoped, refactor-proof — first choice inside a scene |
| `$Child/Sub` / `get_node(path)` | Path walk | Fine for stable local children; crashes if missing |
| `get_node_or_null(path)` | Path walk | Returns `null` instead of erroring — for optional nodes |
| `get_children()` | O(1) | Returns `Array[Node]`; iterate with a typed filter |
| `get_parent()` | O(1) | Reading is fine; *commanding* the parent violates call-down/signal-up |
| `get_tree().get_first_node_in_group(&"hud")` | Group lookup | Service discovery without paths |
| `find_child("Name*", true, false)` | **Recursive search** | Wildcards; slow — never per frame, prefer at `_ready` if at all |
| `find_children("*", "Sprite2D")` | **Recursive search** | Type-filtered sweep; tool scripts and one-shot setup |

```gdscript
# Typed iteration over children — the everyday pattern:
for child in _list.get_children():
	if child is AmbienceToggle:
		(child as AmbienceToggle).set_muted(true)

# Structure editing beyond add/remove:
child.reparent(new_parent)            # keeps global transform by default (4.x)
move_child(node, 0)                   # reorder among siblings (z/draw order for 2D!)
add_sibling(other)                    # insert next to self
var rel: NodePath = get_path_to(other)  # relative path between two nodes
```

Sibling order doubles as 2D draw order (later children draw on top, within the same `z_index`), so `move_child` is also a rendering tool — Relax Room reorders decoration sprites by their room-depth with it (full treatment in [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md)).

### Groups

Groups are lightweight tags on nodes — the engine's built-in service locator for *categories* of nodes:

```gdscript
func _ready() -> void:
	add_to_group(&"pausable_audio")            # code way; editor: Node dock → Groups

# Fetch all members:
for node in get_tree().get_nodes_in_group(&"pausable_audio"):
	node.stream_paused = true

# Or broadcast a method call to every member that has it:
get_tree().call_group(&"pausable_audio", &"pause_playback")

# Deferred-flag variant when handlers modify the tree:
get_tree().call_group_flags(SceneTree.GROUP_CALL_DEFERRED, &"spawners", &"reset")

# Single well-known node idiom:
var hud := get_tree().get_first_node_in_group(&"hud")

if is_in_group(&"pausable_audio"):
	pass
```

Groups shine for one-to-many *commands* ("everything flammable: ignite") and for finding scene-crossing services without hard paths. Their weakness is stringliness: no compile-time check that a group name is spelled right, and no type guarantee on what `get_nodes_in_group` returns. Mitigate by centralizing group names as constants (`const GROUP_HUD := &"hud"`) in one file. The decision matrix — direct call vs signal vs group — is in [Signals as architecture](#signals-as-architecture).

### Case study — Relax Room: the runtime tree

The whole application at runtime, annotated — reading a project's live tree like this (Remote tab!) is the fastest way to absorb its architecture:

```
SceneTree
└── root (Window)
    ├── SignalBus            ┐
    ├── AppLogger            │
    ├── GameManager          │  autoloads, in project.godot order
    ├── SaveManager          │  (see the Autoloads section)
    ├── LocalDatabase        │
    ├── AudioManager         │
    ├── SupabaseClient       │
    └── PerfManager          ┘
    │
    └── Main (current scene, Node2D)
        ├── WallRect (ColorRect)          ← themed flat backdrop
        ├── FloorRect (ColorRect)
        ├── Room (Node2D)
        │   ├── Bounds (StaticBody2D)     ← 4 wall segments
        │   ├── Decorations (Node2D)      ← children reordered by depth
        │   └── Character (CharacterBody2D, instanced scene)
        │       ├── AnimatedSprite2D
        │       └── CollisionShape2D
        └── UILayer (CanvasLayer, layer=10)
            ├── DropZone (Control)
            └── HUD (Control)
                └── panels instanced on demand
```

The node-type cast of the project, as a vocabulary check — every one of these appeared in this module:

| Node | Role in Relax Room |
|---|---|
| `Node2D` | Room, decoration containers — anything with a 2D transform |
| `Sprite2D` / `AnimatedSprite2D` | Decorations / character animation |
| `CharacterBody2D` + `CollisionShape2D` | The walkable character |
| `StaticBody2D` | Room boundaries |
| `Area2D` | Drop zones, interaction triggers |
| `CanvasLayer` | UI overlay independent of the room camera |
| `PanelContainer`, `VBox/HBoxContainer`, `ScrollContainer` | Panel chrome and layout |
| `Button`, `Label`, `HSlider`, `CheckButton` | Interactive UI atoms |
| `AudioStreamPlayer` ×2 | Crossfading music pair (AudioManager) |
| `Timer` | Autosave tick, blink cycles |
| `ColorRect` | Wall/floor/baseboard flats |

### Deferred operations

Godot forbids some tree mutations at "bad" moments — during physics callbacks, while the tree is flushing signals — and the escape hatch is deferring work to the end of the current frame:

```gdscript
func _on_area_2d_body_entered(body: Node2D) -> void:
	# Physics callback: adding/removing/reparenting nodes here can error with
	# "Can't change this state while flushing queries".
	body.queue_free()                              # safe: queue_free is inherently deferred
	call_deferred(&"_spawn_pickup_effect")         # method deferred to idle time
	get_parent().add_child.call_deferred(_ghost)   # any Callable can be deferred
	_door.set_deferred(&"monitoring", false)       # property set at idle time
```

`queue_free()` vs `free()`: `free()` destroys immediately — if anything later this frame still touches the node (a pending signal, an iterator), you crash. `queue_free()` waits for a safe point. Default to `queue_free()`; reach for `free()` only in tool scripts and tight teardown code where you fully control the frame.

---

## Signals as architecture

### Call down, signal up

The single most useful architectural rule in Godot, popularized by GDQuest and consistent with the official best-practice docs, fits in four words: **call down, signal up**. A node may *call methods* on nodes it owns (its children — it created or configured them, it knows their API). A node must never call *upward* or *sideways* into nodes it does not own; instead it *emits a signal* describing what happened, and whoever cares — usually an ancestor that owns both parties — connects and reacts.

```
            ┌────────────┐
            │  RoomScene │  owns both, so it wires them:
            └─────┬──────┘  character.arrived.connect(hud.show_prompt)
        calls ↓       ↑ signals
   ┌──────────▼──┐  ┌─┴──────────┐
   │  Character  │  │    HUD     │
   └─────────────┘  └────────────┘
```

The payoff is reusability and testability: `Character` compiles and runs in an empty test scene because it references nothing above itself. The moment a child does `get_parent().get_node("HUD").show_prompt()`, it can only ever exist inside that exact tree shape.

### Direct call vs signal vs group — decision table

| Situation | Mechanism | Why |
|---|---|---|
| Parent commanding its own child | Direct method call | Ownership is explicit; typed; fastest |
| Child reporting an event upward | Signal | Child stays ignorant of consumers |
| Sibling reacting to sibling | Signal, wired by the common parent | Neither sibling knows the other |
| Distant systems, cross-scene | Signal bus (autoload) | No path coupling at all |
| One-to-many broadcast command | Group (`call_group`) | Receivers self-register; no list to maintain |
| Querying a well-known service | Autoload method call | Global façade, one instance |
| Response needed (a question, not an event) | Direct call / autoload call | Signals do not return values |

Two smells to memorize. **Signal round-trips**: if A signals B and B immediately signals back to A, that is a call wearing a costume — use a method. **Signal chains**: A → B → C → D relays, where each hop just re-emits, mean your event belongs on a bus visible to all four.

### The signal bus (event bus) pattern

A signal bus is an autoload whose only content is signal declarations — a global notice board. Emitters post facts; listeners subscribe; neither knows the other exists.

```gdscript
# signal_bus.gd — autoloaded as SignalBus. Declarations ONLY: no state, no logic.
extends Node

# Room domain
signal room_changed(room_id: String, theme: String)
signal decoration_placed(item_id: String, position: Vector2)
signal decoration_removed(item_id: String)

# Audio domain
signal track_started(track_id: String)
signal ambience_toggled(ambience_id: String, active: bool)

# Meta
signal save_requested
signal coins_changed(new_total: int)
```

```gdscript
# shop_panel.gd — emitter. Knows nothing about saving, audio, or the HUD.
func _purchase(item_id: String) -> void:
	GameManager.spend_coins(_price_of(item_id))
	SignalBus.decoration_placed.emit(item_id, _drop_position)

# save_manager.gd — listener. Knows nothing about the shop UI.
func _ready() -> void:
	SignalBus.decoration_placed.connect(_on_decoration_placed)
	SignalBus.decoration_removed.connect(_on_decoration_removed)

func _on_decoration_placed(item_id: String, position: Vector2) -> void:
	_pending_state.decorations[item_id] = position
	_mark_dirty()
```

**Benefits:** components are added/removed without breaking each other; every event in the app is enumerated in one greppable file; testing is trivial (emit the signal manually, assert the reaction). **Costs, stated honestly:** control flow becomes invisible at the call site (who listens to `decoration_placed`? — you must search); overuse turns architecture into "everything is global events", which is as tangled as everything-is-global-calls; and ordering between multiple listeners of one signal is connection-order, which is fragile to rely on.

> ✅ **Best practice** — Bus signals must be **facts, not commands**: `decoration_placed`, not `please_save_decoration`. The moment a bus signal has exactly one intended listener and imperatively names the action, it should have been a direct call to that system's public method. Keep local events local: a button's `pressed` reaching its own panel does not belong on the bus.

> ⚠️ **Pitfall** — Because the bus outlives scenes, every scene-owned listener **must disconnect in `_exit_tree()`** (or connect with `CONNECT_ONE_SHOT` where appropriate). A freed-but-connected listener is severed automatically, but a listener that is *removed and kept alive* (cached panels, pooled objects) keeps receiving and mutating state from offstage — a maddening class of bug.

### Testing through the bus

The bus's decoupling pays a dividend the day you write tests: any system that reacts to bus signals can be exercised without constructing the systems that normally emit them.

```gdscript
# test_save_manager.gd — a minimal harness scene, run with F6.
extends Node

func _ready() -> void:
	# No shop UI, no room, no character — just fire the facts they would emit:
	SignalBus.decoration_placed.emit(&"plant_01", Vector2(120, 80))
	SignalBus.decoration_placed.emit(&"lamp_02", Vector2(200, 64))
	SignalBus.decoration_removed.emit(&"plant_01")

	await get_tree().create_timer(0.1).timeout          # let deferred handlers run
	var state := SaveManager.peek_pending_state()        # test-only accessor
	assert(not state.decorations.has(&"plant_01"), "removed item persisted!")
	assert(state.decorations.has(&"lamp_02"), "placed item lost!")
	print("SaveManager bus-reaction test: PASS")
	get_tree().quit()
```

Run headless in CI with `godot --headless res://tests/test_save_manager.tscn`. This is not a full testing framework (GUT and gdUnit4 exist for that), but the pattern — *emit facts, assert reactions* — is the unit-test shape that a signal-bus architecture makes nearly free, and it works because emitters and listeners never needed each other in the first place.

### Case study — Relax Room: SignalBus in production

Relax Room routes 23 cross-system events through `SignalBus`, grouped by domain exactly as above. Three rules the project enforces in review: (1) UI panels never call `SaveManager` — they emit domain facts and `SaveManager` listens with its dirty-flag accumulator; (2) every `connect` to `SignalBus` from a scene-owned node has a matching `disconnect` in `_exit_tree()`; (3) any new bus signal must list its intended listeners in a comment, and if the list has one entry, the PR gets challenged to justify not using a direct call.

---

## Autoloads

> Working overview; the deep dive — dependency discipline, init-order hazards, testing autoload-heavy projects — is [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) (Module 13).

### Mechanics

An **autoload** (Project Settings → Globals → Autoload) is a script or scene the engine instantiates as a child of `root` before the main scene, keeps alive across scene changes, and exposes by name to every script:

```ini
# project.godot
[autoload]
SignalBus="*res://scripts/autoload/signal_bus.gd"
AppLogger="*res://scripts/autoload/logger.gd"
GameManager="*res://scripts/autoload/game_manager.gd"
SaveManager="*res://scripts/autoload/save_manager.gd"
AudioManager="*res://scenes/autoload/audio_manager.tscn"
```

The `*` prefix means "instantiate as a node" (for scripts: wrap in a plain `Node`); without it, a script autoload merely loads the script resource. Access is by bare name — `GameManager.current_room_id` — which works because the engine registers each autoload's name globally; `get_node("/root/GameManager")` reaches the same instance.

Autoloads initialize **in list order**, top to bottom: each one's `_enter_tree()` and `_ready()` complete before the next loads, and all complete before the main scene's. Order is therefore a dependency declaration.

### An autoload done well: the typed facade shape

A production autoload keeps its state private and its surface small, typed, and signal-announced — the same discipline as any class, with extra scrutiny because *everyone* can call it:

```gdscript
# game_manager.gd — autoloaded as GameManager (excerpt).
extends Node

signal coins_changed(new_total: int)

var _coins: int = 0                                # private: nobody pokes this directly
var _tracks_by_id: Dictionary[StringName, TrackData] = {}

func _ready() -> void:
	_tracks_by_id = _load_track_catalog()

# --- Public, typed, intention-named API ---------------------------------
func coins() -> int:
	return _coins

func can_afford(price: int) -> bool:
	return _coins >= price

func spend_coins(amount: int) -> bool:
	if amount < 0 or amount > _coins:
		push_error("Invalid spend: %d (have %d)" % [amount, _coins])
		return false
	_coins -= amount
	coins_changed.emit(_coins)
	return true

func get_track(id: StringName) -> TrackData:
	return _tracks_by_id.get(id)                   # null for unknown → caller checks
```

The shape to copy: private fields, a boolean-returning mutator that *validates* (global state that anything can corrupt must defend itself), and a signal per externally interesting change so UI never polls. What the shape forbids is equally important: no `GameManager._coins -= price` from a panel script — if the field were public, that line *would* get written, and the coins display would silently desynchronize.

### Case study — Relax Room: autoload stack and init order

```
1. SignalBus       ← zero dependencies (declarations only) — always first
2. AppLogger       ← structured logging; needs nothing at init
3. GameManager     ← loads JSON catalogs; logs via AppLogger
4. SaveManager     ← reads save file; resolves against GameManager catalogs
5. LocalDatabase   ← opens SQLite; registers with SaveManager
6. AudioManager    ← needs GameManager (track catalog) + SaveManager (volumes)
7. SupabaseClient  ← optional cloud sync; needs SaveManager
8. PerfManager     ← window position + low-CPU mode; needs SaveManager
```

Swapping 3 and 6 makes `AudioManager._ready()` read `GameManager.tracks_catalog` before it exists — an immediate null-access crash, which is the *good* failure mode; the bad one is a subtly empty catalog. The project rule: an autoload may depend only on autoloads **above** it, and the dependency must appear in this comment block in `project.godot`'s companion doc.

### When (not) to use an autoload

| Good autoload | Should NOT be an autoload |
|---|---|
| Signal bus (pure declarations) | Anything per-scene or per-instance |
| Persistent services: audio, save, logging | UI panels (instantiate per use) |
| Session state that must survive scene swaps | Data that should reset with the scene |
| Configuration/catalog access façade | Utility functions → `static func` in a `class_name` instead |

The honest test: *does this need to be a node, alive, unique, and eternal?* Pure functions need none of those — make them static. Constants need none — make them a `class_name` with `const`s. Data tables need lifecycle only for loading — consider a static var + static loader, or a Resource. Reserve autoloads for genuinely global *stateful services*, because each one is invisible coupling available to (and abusable by) every script in the project.

> ⚠️ **Pitfall** — Autoloads are singletons *by convention only*: nothing stops `load("res://.../game_manager.gd").new()` from creating a rogue second instance whose state diverges. Never instantiate an autoload script manually, and treat static `instance`-style backdoors as review failures.

---

## Resources and file I/O

### Nodes vs Resources — the two halves of the data model

| | Nodes | Resources |
|--|-------|-----------|
| Role | Live objects in the tree (behavior) | Data containers (state/config/assets) |
| Memory | Manual: `queue_free()`, freed by parent | Reference-counted, freed automatically |
| Identity | Unique per instance | **Shared**: same path ⇒ same instance (cache) |
| Serialized as | `.tscn`/`.scn` scenes | `.tres`/`.res` files, or embedded in scenes |
| Examples | `Sprite2D`, `Button`, `Timer` | `Texture2D`, `AudioStream`, `PackedScene`, `Theme` |

The sharing rule deserves emphasis because it inverts newcomer intuition: `load()` and `preload()` return **the cached instance** if the resource is already in memory. Load the same `.tres` from ten scripts and all ten hold the *same object* — edit one field and everyone sees it. That is a feature (memory efficiency, live tuning) until it isn't (mutating a shared template).

```gdscript
var a := load("res://data/tracks/forest.tres") as TrackData
var b := load("res://data/tracks/forest.tres") as TrackData
print(a == b)                      # true — same instance!

var mine := a.duplicate() as TrackData      # personal shallow copy
var deep := a.duplicate(true) as TrackData  # also duplicates nested sub-resources
mine.title = "Forest (custom)"              # cache instance untouched
```

For scene-embedded resources (a material tweaked per enemy, say), `resource_local_to_scene = true` on the resource makes each scene instance receive its own copy automatically at instantiation.

> ⚠️ **Pitfall** — "I changed the color of one button's StyleBox and every button changed" is the shared-resource rule in action: all buttons referenced one StyleBox resource. Fix with `duplicate()` at runtime or *Make Unique* in the Inspector at design time.

### preload vs load

| | `preload(path)` | `load(path)` |
|--|---|--|
| When it runs | At script **parse/compile** time | When the line executes |
| Path | Must be a **string literal** | Any String expression |
| Cost at call site | None (already resident) | Disk hit on first load, then cache |
| Failure mode | Script fails to load at all | Returns `null` at runtime — check it |
| Use for | Assets a script always needs | Conditional/dynamic assets, user content |

```gdscript
const CLICK_SFX := preload("res://audio/ui/click.ogg")          # constant + preload: idiomatic
var portrait := load("res://portraits/%s.png" % character_id)   # dynamic path → must be load
```

For big scenes, blocking `load()` causes a visible hitch; the answer is threaded loading:

```gdscript
func start_loading(path: String) -> void:
	ResourceLoader.load_threaded_request(path)

func _process(_delta: float) -> void:
	var progress: Array = []
	match ResourceLoader.load_threaded_get_status(_path, progress):
		ResourceLoader.THREAD_LOAD_IN_PROGRESS:
			_bar.value = progress[0] * 100.0
		ResourceLoader.THREAD_LOAD_LOADED:
			var scene := ResourceLoader.load_threaded_get(_path) as PackedScene
			get_tree().change_scene_to_packed(scene)
		ResourceLoader.THREAD_LOAD_FAILED, ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
			push_error("Failed to load %s" % _path)
```

### Custom Resources: data-driven design

Subclassing `Resource` turns the Inspector into your data-entry tool and `.tres` files into your database rows — with type safety JSON can never give you:

```gdscript
# track_data.gd
class_name TrackData
extends Resource

@export var id: StringName
@export var title: String = ""
@export var artist: String = ""
@export var stream: AudioStream               # the audio itself, drag-and-dropped
@export_range(0.0, 1.0, 0.01) var default_volume: float = 0.8
@export var tags: Array[StringName] = []

func matches(tag: StringName) -> bool:        # resources can carry behavior too
	return tag in tags
```

```gdscript
# Loading a folder of .tres rows into a typed catalog:
func load_catalog(dir_path: String) -> Array[TrackData]:
	var out: Array[TrackData] = []
	for file in ResourceLoader.list_directory(dir_path):    # Godot 4.3+ helper
		if file.ends_with(".tres"):
			var res := load(dir_path.path_join(file))
			if res is TrackData:
				out.append(res)
	return out
```

When to choose which data format:

| Format | Choose when |
|---|---|
| Custom Resource (`.tres`) | Editor-authored game data; wants type safety, Inspector editing, sub-resources |
| JSON | Interop with external tools/servers; user-writable files; save files you must inspect |
| SQLite (Module: [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md)) | Queryable, growing, relational user data |
| `ConfigFile` | INI-style settings with sections; trivial API |

> ⚠️ **Pitfall** — Do not deserialize `.tres`/`.res` (or any resource with embedded scripts) from **untrusted sources**: resource files can reference scripts and loading them executes code. User-generated content and save files should be JSON, ConfigFile, or raw bytes you parse yourself — never `load()`-ed resources. (Relax Room saves JSON; catalogs, which ship read-only inside the build, are resources.)

### Bridging resources and save files

Custom Resources describe *content*; save files record *state referring to that content*. The clean seam between them is an id-based `to_dict`/`from_catalog` pair — the save file stores plain JSON-able values and **ids**, never serialized resources:

```gdscript
# placed_decoration.gd — runtime state wrapping catalog content.
class_name PlacedDecoration
extends RefCounted

var data: DecorationData         # catalog resource (content — NOT saved directly)
var position: Vector2            # instance state (saved)
var rotation_steps: int = 0

func to_dict() -> Dictionary:
	return {
		"id": String(data.id),                     # reference by id…
		"x": position.x, "y": position.y,          # …plus JSON-safe primitives
		"rot": rotation_steps,
	}

static func from_dict(d: Dictionary, catalog: Dictionary) -> PlacedDecoration:
	var out := PlacedDecoration.new()
	out.data = catalog.get(StringName(d.get("id", "")))
	if out.data == null:
		push_warning("Save references unknown decoration '%s' — skipped" % d.get("id"))
		return null                                # tolerate removed content
	out.position = Vector2(d.get("x", 0.0), d.get("y", 0.0))
	out.rotation_steps = int(d.get("rot", 0))
	return out
```

Note the two defensive moves that make save files survive *content updates*: unknown ids are skipped with a warning (the catalog shrank), and every field reads through `get(key, default)` (the schema grew). This id-indirection is also the security answer from the earlier pitfall — the save file never contains loadable resources, only strings and numbers validated on the way in.

### The two filesystems: res:// and user://

```
res://   → project root. READ-ONLY once exported (packed into the .pck).
           scenes, scripts, art, catalogs.
user://  → per-app writable directory. Survives updates.
           Windows: %APPDATA%\Godot\app_userdata\<Project Name>\
           Linux:   ~/.local/share/godot/app_userdata/<Project Name>/
           macOS:   ~/Library/Application Support/Godot/app_userdata/<Project Name>/
```

Writing to `res://` works in the editor (it is just your project folder) and **fails silently or loudly after export** — a bug that by definition only appears in production builds. Everything the app writes goes to `user://`; `OS.get_user_data_dir()` gives the absolute path for shell-open buttons.

### FileAccess and DirAccess

```gdscript
# Write JSON (atomically enough for a desktop app: write temp, then rename).
func save_json(path: String, data: Dictionary) -> Error:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		var err := FileAccess.get_open_error()
		push_error("Cannot write %s (error %d)" % [path, err])
		return err
	file.store_string(JSON.stringify(data, "\t"))
	file.close()                       # optional: closing happens when file is freed
	return OK

# Read JSON with full error reporting.
func load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var text := FileAccess.get_file_as_string(path)      # one-liner helper
	var json := JSON.new()
	if json.parse(text) != OK:
		push_error("JSON error in %s line %d: %s" %
				[path, json.get_error_line(), json.get_error_message()])
		return {}
	return json.data if json.data is Dictionary else {}
```

```gdscript
# Directory operations
DirAccess.make_dir_recursive_absolute("user://saves/backups")
DirAccess.dir_exists_absolute("user://saves")
DirAccess.copy_absolute("user://save.json", "user://saves/backups/save_1.json")
DirAccess.remove_absolute("user://old_cache.bin")        # files only; dirs must be empty

# Listing — the modern loop:
func list_files(path: String) -> PackedStringArray:
	var dir := DirAccess.open(path)
	if dir == null:
		return PackedStringArray()
	return dir.get_files()                               # non-recursive, sorted
```

Other write formats in the same API family: `store_var()`/`get_var()` (binary Variant serialization — compact, fast, not human-readable; pass `full_objects = false` to stay safe against script injection), `store_csv_line()`, and `FileAccess.open_compressed()` for transparent compression.

### ConfigFile: settings without ceremony

For INI-style user settings — window position, volumes, toggles — `ConfigFile` beats hand-rolled JSON:

```gdscript
const SETTINGS_PATH := "user://settings.cfg"

func save_settings() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("audio", "music_volume", _music_volume)      # (section, key, value)
	cfg.set_value("audio", "ambience_muted", _ambience_muted)
	cfg.set_value("window", "position", DisplayServer.window_get_position())
	var err := cfg.save(SETTINGS_PATH)
	if err != OK:
		push_error("Settings save failed: %d" % err)

func load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SETTINGS_PATH) != OK:
		return                                                  # first run: keep defaults
	_music_volume = cfg.get_value("audio", "music_volume", 0.8) # default per key
	_ambience_muted = cfg.get_value("audio", "ambience_muted", false)
```

`ConfigFile` serializes full Variants (Vector2i round-trips intact — note the window position above), tolerates missing keys via defaults, and stays human-editable. Its limits: flat section/key structure and no schema — when settings grow nested or validated, graduate to JSON with an explicit migration step, and for *world state* use the save-file architecture in [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md).

### Resource UIDs

Alongside paths, Godot assigns every imported/saved resource a **UID** (`uid://c4n0m...`), stored in `.import` files and scene references. UIDs survive file moves and renames — a scene referencing `uid://...` keeps working after you reorganize folders, where a raw `res://old/path.png` string in *code* would break. Practical consequences: `load("uid://c4n0m...")` is valid and refactor-proof for code-side references to frequently-moved assets; keep the `.uid` sidecar files (Godot 4.4+ generates them for scripts too) committed to version control, because regenerating them re-links every reference.

---

## Input handling

### Actions, not keys

Godot's input model is **action-based**: you define named logical actions in Project Settings → Input Map (or at runtime via the `InputMap` singleton), bind any number of physical events to each (keys, mouse buttons, gamepad buttons/axes), and query the *action*. Code never mentions physical keys, which buys you rebinding, multi-device support, and readable intent for free.

```ini
# project.godot [input] — conceptually:
move_left  = A, Left Arrow, Gamepad Left Stick -X
move_right = D, Right Arrow, Gamepad Left Stick +X
move_up    = W, Up Arrow
move_down  = S, Down Arrow
toggle_music = Space
open_shop    = B
```

> ✅ **Best practice** — Also mind the built-in `ui_*` actions (`ui_accept`, `ui_cancel`, `ui_focus_next`...): Control nodes consume them for keyboard/gamepad UI navigation. Do not overload `ui_*` names for gameplay — define your own actions and leave the UI set intact for accessibility.

### Polling: the Input singleton

Polling asks "what is the state *right now*?" — the natural fit for continuous controls inside `_physics_process`:

```gdscript
func _physics_process(_delta: float) -> void:
	# get_vector handles normalization AND per-action deadzones correctly:
	# (negative_x, positive_x, negative_y, positive_y)
	var direction := Input.get_vector(&"move_left", &"move_right", &"move_up", &"move_down")
	velocity = direction * speed
	move_and_slide()

func _process(_delta: float) -> void:
	if Input.is_action_just_pressed(&"toggle_music"):   # edge: this frame only
		AudioManager.toggle_playback()
	if Input.is_action_pressed(&"open_shop"):           # level: true while held
		_hold_time += _delta
	if Input.is_action_just_released(&"open_shop"):
		_on_shop_released(_hold_time)
```

Semantics worth being precise about: `is_action_pressed` is *level* (true every frame while held); `is_action_just_pressed` / `just_released` are *edges* (true only on the frame the state changed — and they are aware of whether you call them from `_process` or `_physics_process`, so each callback sees the edge exactly once). `Input.get_axis(neg, pos)` returns a −1..1 scalar for a single axis pair; `get_action_strength()` returns the analog 0..1 strength (gamepad triggers).

### Events: the callback chain

Events answer "something *happened*" — the natural fit for discrete reactions, text input, and anything that must respect UI. Each `InputEvent` travels through the viewport's chain and stops as soon as someone consumes it:

```
1. Node._input(event)              — every node, tree bottom-up. Raw firehose.
2. Control._gui_input(event)       — UI: delivered to the control under the mouse /
                                     with focus. Buttons consume clicks HERE.
3. Node._shortcut_input(event)     — key/shortcut/joy-button events only.
4. Node._unhandled_key_input(event)— leftover key events.
5. Node._unhandled_input(event)    — everything not consumed above: GAMEPLAY.
6. Physics picking                 — CollisionObject2D.input_event fires last.
```

Consuming: `get_viewport().set_input_as_handled()` in `_input`/`_unhandled_input`; `accept_event()` inside `_gui_input`. The design consequence of the ordering is the golden rule:

> ✅ **Best practice** — Gameplay input goes in `_unhandled_input()` (or polling), never `_input()`. Because UI processes events at stage 2, a click on a button is consumed *before* stage 5 — your character will not also "walk to the click" underneath a menu. Use `_input()` only for capture-everything cases: global hotkeys, input recording, an active rebinding dialog.

```gdscript
func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"open_shop"):
		SignalBus.shop_open_requested.emit()
		get_viewport().set_input_as_handled()

	# Typed event handling: `is` + cast pattern.
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
			_try_place_decoration(get_global_mouse_position())
```

The `InputEvent` family: `InputEventKey`, `InputEventMouseButton`, `InputEventMouseMotion` (has `relative` — mouse delta), `InputEventJoypadButton`, `InputEventJoypadMotion`, `InputEventScreenTouch`/`Drag`, `InputEventAction` (synthetic, for programmatic input). Two flags matter constantly: `event.is_echo()` — true for OS key-repeat events (holding a key spams pressed events; `is_action_pressed(action)` on an echo event still reports true, so filter with `event.is_echo()` when you want physical presses only) — and `pressed` vs release for buttons.

Echo filtering in practice — a chat-style input where holding a key must not re-trigger an action, while the text field still auto-repeats:

```gdscript
func _unhandled_key_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key.echo:
		return                       # OS auto-repeat: real for typing, noise for actions
	if key.pressed and key.keycode == KEY_F1:
		_toggle_debug_overlay()
```

### Runtime remapping

```gdscript
func rebind(action: StringName, new_event: InputEvent) -> void:
	InputMap.action_erase_events(action)         # clear old bindings
	InputMap.action_add_event(action, new_event) # bind captured event
	# Note: InputMap changes are RUNTIME-ONLY. Persist them yourself:
	_save_binding(action, new_event)             # e.g. into a ConfigFile
```

A rebinding dialog is just `_input()` capturing the next `InputEventKey`/`InputEventJoypadButton`, calling the function above, then `set_input_as_handled()`.

### Mouse utilities

```gdscript
get_global_mouse_position()                     # world coords (CanvasItem method)
get_viewport().get_mouse_position()             # viewport/screen coords
Input.mouse_mode = Input.MOUSE_MODE_HIDDEN      # also CAPTURED, CONFINED
Input.set_custom_mouse_cursor(cursor_texture)   # pixel-art cursor
Input.warp_mouse(Vector2(640, 360))             # teleport the pointer
```

### Case study — Relax Room: two input layers

Relax Room's input is a clean two-layer split. Layer 1, UI: all panels are Controls, so clicks on them are consumed at `_gui_input` stage with zero custom code. Layer 2, room interaction: the character's walk-to-click and decoration drag-drop live in `_unhandled_input` on the room scene — they physically cannot fire through a panel, because the panel consumed the click first. The only `_input()` user in the project is the global hotkey handler (media keys and the panic-hide shortcut), which must work even while a panel has focus.

---

## Control and UI essentials

### The Control positioning model

`Control` nodes do not use free transforms; they are positioned by **anchors** (four values in 0..1, fractions of the parent's rect) plus **offsets** (pixel distances from those anchor lines). You almost never set these numerically: the toolbar's **anchor presets** (center, full-rect, top-right...) set both in one click, and `set_anchors_preset(Control.PRESET_FULL_RECT)` does it in code.

```
(0,0) ────────────── (1,0)       anchors 0,0..1,1 + offsets 0 = fill parent
  │    parent rect     │         anchors all (1,1) = pinned bottom-right corner
  │   ┌─────────┐      │         → resize the window and the control follows
  │   │ Control │      │           its anchor, not absolute pixels
(0,1) └─────────┘─── (1,1)
```

Rules that prevent 90% of layout confusion: **inside a Container, anchors are ignored** — the container owns the child geometry (you influence it via size flags); `custom_minimum_size` is *your* voice in the negotiation ("never smaller than this"); `size` is an outcome, not an input — set it only on free (non-contained) controls, and never in `_process`.

In code, the preset functions do what the toolbar buttons do:

```gdscript
var overlay := ColorRect.new()
overlay.set_anchors_preset(Control.PRESET_FULL_RECT)     # fill the parent
add_child(overlay)

var badge := TextureRect.new()
badge.set_anchors_and_offsets_preset(
	Control.PRESET_TOP_RIGHT, Control.PRESET_MODE_KEEP_SIZE, 8)  # pin corner, 8px margin
add_child(badge)

# Reading actual layout (valid only AFTER a frame of layout):
await get_tree().process_frame
print(badge.size, " at ", badge.global_position)
```

That final caveat generalizes: a Control's `size` is computed by the layout pass, so measuring right after `add_child()` reads zeros — await one `process_frame` first, or react to the control's `resized` signal instead of polling.

### Containers

| Container | Layout behavior | Typical use |
|-----------|-----------------|-------------|
| `VBoxContainer` / `HBoxContainer` | Stack children vertically / horizontally | Menus, panel bodies, toolbars |
| `GridContainer` | Fixed column count grid | Inventory/shop grids |
| `MarginContainer` | Pads its single child | Outer padding of panels |
| `CenterContainer` | Centers child at its minimum size | Modal content |
| `ScrollContainer` | Scrollbars around one child | Long lists |
| `PanelContainer` | Draws a StyleBox behind child | Panel chrome |
| `TabContainer` | One child per tab | Settings pages |
| `SplitContainer` (H/V) | User-draggable divider | Editor-like layouts |
| `AspectRatioContainer` | Keeps child at fixed ratio | Thumbnails, video |
| `FlowContainer` (H/V) | Wraps children to next row/column | Tag clouds, chips |

Within a container, **size flags** decide how children share space:

```gdscript
# SIZE_FILL (default): occupy the space assigned, request nothing extra.
# SIZE_EXPAND: request a share of leftover space.
# SIZE_EXPAND_FILL: request extra space AND stretch into it — the workhorse.
# SIZE_SHRINK_CENTER / SHRINK_END: stay at minimum size, positioned in the slot.
_track_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
_time_label.size_flags_horizontal = Control.SIZE_SHRINK_END
# stretch_ratio weights multiple expanders: 2.0 gets twice the leftover of 1.0.
_track_label.size_flags_stretch_ratio = 2.0
```

> ⚠️ **Pitfall** — Setting `position`/`size` on a child of a container does nothing (the container reasserts its layout next frame) — this is the most-asked UI question in every Godot forum. Configure `custom_minimum_size`, size flags, and the container's own properties instead. If you need free placement, the parent should be a plain `Control`, not a container.

### The everyday Control vocabulary

The controls that cover 95% of a typical app UI, with the signal you will actually connect:

| Control | Purpose | Key signal(s) |
|---|---|---|
| `Label` | Static text | — (`text` property) |
| `RichTextLabel` | BBCode text: colors, links, images | `meta_clicked` (links) |
| `Button` | Click action | `pressed`; `toggled(on)` in toggle mode |
| `TextureButton` / `TextureRect` | Image button / image display | `pressed` / — |
| `CheckBox` / `CheckButton` | Boolean choice / switch styling | `toggled(on)` |
| `LineEdit` | Single-line input | `text_submitted(text)`, `text_changed(text)` |
| `TextEdit` / `CodeEdit` | Multi-line input | `text_changed` |
| `HSlider` / `VSlider` | Ranged value | `value_changed(value)`, `drag_ended` |
| `SpinBox` | Numeric entry with arrows | `value_changed(value)` |
| `ProgressBar` / `TextureProgressBar` | Read-only progress | — (`value` property) |
| `OptionButton` | Dropdown selection | `item_selected(index)` |
| `ItemList` | Selectable list/grid of items | `item_activated(index)` |
| `Tree` | Hierarchical data view | `item_selected` |
| `ColorRect` / `Panel` | Flat color / themed backdrop | — |

> ⚠️ **Pitfall** — Slider-driven settings connected via `value_changed` fire on *every pixel* of a drag — dozens of writes per second. Apply the value live (cheap), but persist on `drag_ended` (or debounce with a short Timer), or your settings file gets rewritten sixty times per slider gesture.

### Building UI in code

Everything the editor does, code can do — and for catalog-driven UI (contents unknown until data loads), code is the right tool:

```gdscript
func _build_row(track: TrackData) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)

	var play_btn := Button.new()
	play_btn.text = "▶"
	play_btn.custom_minimum_size = Vector2(28, 28)
	play_btn.pressed.connect(_on_play_pressed.bind(track.id))
	row.add_child(play_btn)

	var title := Label.new()
	title.text = track.title
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	row.add_child(title)
	return row
```

### Case study — Relax Room: why the panels are code-built

Relax Room's four panels (music, ambience, shop, decorations) build their contents programmatically because they are **catalog-driven**: the rows come from JSON/`.tres` catalogs that change without touching scenes. The *frames* (PanelContainer + margins + title bar) are `.tscn` scenes designed visually; only the dynamic list interiors are code. This hybrid is the pragmatic default: design static structure visually, generate repeated data-bound content in code.

### Theming

A `Theme` resource centralizes the look: per-control-type colors, fonts, font sizes, icons, constants (separations, margins), and StyleBoxes (the drawable backgrounds — `StyleBoxFlat` covers rounded rects, borders, and shadows without art assets). Set one project-wide via Project Settings → GUI → Theme → Custom, then override locally:

```gdscript
# Per-node overrides (highest priority, good for one-offs):
_title.add_theme_font_size_override(&"font_size", 20)
_title.add_theme_color_override(&"font_color", Color("#e8d8c0"))
_panel.add_theme_stylebox_override(&"panel", _make_cozy_stylebox())

func _make_cozy_stylebox() -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("#2b2320")
	sb.set_corner_radius_all(8)
	sb.set_content_margin_all(12)
	return sb
```

Resolution order for any theme item: node override → node's `theme` resource (walking up ancestors) → project theme → engine default. Type variations (e.g. a `"TitleLabel"` variation of `Label`) let one theme carry named styles you assign via `theme_type_variation`.

> ✅ **Best practice** — Put every color and font in the Theme, never hard-coded across scripts. Reskinning (dark mode, seasonal themes — a planned Relax Room feature) then means swapping one resource, not hunting hex codes through forty files.

### Focus and keyboard navigation

Keyboard/gamepad UI works through the focus system: one Control holds focus and receives key events; `ui_focus_next`/`ui_up`... move it along.

```gdscript
_play_button.focus_mode = Control.FOCUS_ALL       # FOCUS_NONE / FOCUS_CLICK / FOCUS_ALL
_play_button.grab_focus()                          # move focus here (e.g. on panel open)
get_viewport().gui_get_focus_owner()               # who has focus now (may be null)
_slider.focus_neighbor_right = _mute_button.get_path()   # manual override of auto layout
```

Two habits make UIs keyboard-clean: on opening any modal, `grab_focus()` its default control; on closing, return focus to the invoker. Godot 4.5's accessibility work (screen-reader support via AccessKit) reads focus and control metadata — a correctly focused UI is an accessible UI almost for free.

### Shortcuts on controls

Desktop apps live on keyboard shortcuts, and `Button` (via `BaseButton`) supports them natively — no `_input` code:

```gdscript
var ev := InputEventKey.new()
ev.keycode = KEY_SPACE
var sc := Shortcut.new()
sc.events = [ev]
_play_button.shortcut = sc            # Space now presses Play, wherever focus is
_play_button.shortcut_in_tooltip = true   # tooltip shows "(Space)" automatically
```

Because the shortcut routes through the button, you get the pressed visual state, the same `pressed` signal path, and disabled-state handling for free — reasons to prefer this over a parallel `_shortcut_input` implementation whenever the shortcut *is* conceptually a button press. Relax Room binds Space to play/pause and `M` to mute this way.

### Mouse filter and click-through

Every Control has `mouse_filter`: `STOP` (consume mouse events — default for interactive controls), `PASS` (react, then let the event continue to the control *behind*), `IGNORE` (invisible to mouse). This one property explains most "my clicks don't reach X" bugs:

> ⚠️ **Pitfall** — A full-screen `Control` (a ColorRect dimmer, an empty margin overlay) with default `mouse_filter = STOP` silently eats every click in the game. If an overlay is decorative, set `mouse_filter = IGNORE`. Inversely, if your popup should block clicks to the game behind it, `STOP` on its background is exactly what you want.

### Drag and drop between Controls

Controls have a built-in drag-and-drop protocol — three virtual methods, no manual mouse tracking:

```gdscript
# shop_item_card.gd — the SOURCE: what does dragging me mean?
extends PanelContainer

@export var item_id: StringName

func _get_drag_data(_at_position: Vector2) -> Variant:
	var preview := TextureRect.new()             # ghost that follows the cursor
	preview.texture = _icon.texture
	preview.modulate.a = 0.7
	set_drag_preview(preview)                    # tree-managed; do not free it yourself
	return {"type": "decoration", "id": item_id} # the payload — any Variant


# drop_zone_panel.gd — the TARGET: can I take it? then take it.
extends Control

func _can_drop_data(_at_position: Vector2, data: Variant) -> bool:
	return data is Dictionary and data.get("type") == "decoration"

func _drop_data(at_position: Vector2, data: Variant) -> void:
	SignalBus.decoration_placed.emit(data["id"], _to_room_coords(at_position))
```

The engine handles the rest: press-and-move on the source starts the drag, the cursor previews validity by querying `_can_drop_data` on whatever it hovers, and release on a willing target calls `_drop_data`. Relax Room's shop-to-room placement is exactly this trio plus a `_to_room_coords` conversion — about thirty lines total, versus the hundred-line hand-rolled version with mouse state flags that new Godot developers write first.

### Custom drawing with _draw

Every `CanvasItem` (Control *and* Node2D) can paint itself procedurally: override `_draw()`, call the `draw_*` API, and request repaints with `queue_redraw()`. This is the tool for widgets no stock control provides — progress rings, waveform displays, grid overlays — and it renders as a single canvas item, often cheaper than assembling the same visual from many nodes.

```gdscript
# progress_ring.gd — circular track progress around the play button.
extends Control

var progress: float = 0.0:                # 0..1
	set(value):
		progress = clampf(value, 0.0, 1.0)
		queue_redraw()                    # _draw runs only when requested!

func _draw() -> void:
	var center := size / 2.0
	var radius := minf(center.x, center.y) - 4.0
	draw_arc(center, radius, 0.0, TAU, 48, Color(1, 1, 1, 0.15), 3.0, true)
	draw_arc(center, radius, -TAU / 4.0, -TAU / 4.0 + TAU * progress,
			48, Color("#e8d8c0"), 3.0, true)      # antialiased arc from 12 o'clock
```

The contract: drawing happens *only* inside `_draw()`; outside it, `draw_*` calls error. The engine caches the result — `_draw` re-runs only after `queue_redraw()`, so a static shape costs nothing per frame. The API family covers `draw_line`, `draw_rect`, `draw_circle`, `draw_arc`, `draw_polygon`, `draw_texture_rect`, `draw_string`, and transforms via `draw_set_transform`.

### Localization hooks

Even a two-language app (Relax Room ships English and Italian) should route UI strings through the translation system from day one — retrofitting is misery. Mechanics: add translation files (CSV or gettext `.po`) under Project Settings → Localization; every `tr("KEY")` call — and, automatically, every Control `text` property whose value matches a key — resolves through the active locale.

```gdscript
_title.text = tr("PANEL_MUSIC_TITLE")               # explicit
TranslationServer.set_locale("it")                  # switch at runtime
var n := 3
_label.text = tr_n("TRACK_ONE", "TRACK_MANY", n) % n  # plural-aware
```

Two conventions keep it sane: keys are `SCREAMING_SNAKE` namespaced by screen (`SHOP_BUY_BUTTON`), never English sentences (sentence-keys break the moment copy is edited); and no string concatenation of translated fragments — word order differs across languages, so always translate whole sentences with `%s` placeholders. Godot 4.5's in-editor translation preview (viewport language switcher) lets you audit layouts for the 30%-longer German/Italian strings without running the game.

### CanvasLayer: UI above the world

`CanvasLayer` renders its subtree in an independent 2D layer with its own transform — unaffected by the game `Camera2D`. The standard scene shape is game world under `Node2D`, HUD under a `CanvasLayer` (layer = 10 in Relax Room), so the camera can roam while the UI stays screen-fixed. Higher `layer` values render on top; a `CanvasLayer` with `follow_viewport_enabled` can opt back into camera space for world-anchored labels.

The camera side of that pairing, in brief: a `Camera2D` node makes the viewport follow its position — enable one per playable scene (`enabled`, and only one active at a time). The properties that do the heavy lifting: `zoom` (`Vector2(2, 2)` = 2× magnification — for pixel art use integer zooms to keep pixels square), `limit_left/top/right/bottom` (clamp the view to the room so the void beyond never shows), `position_smoothing_enabled` + `position_smoothing_speed` (lag-behind follow that makes motion feel alive), and `drag_*` margins (move the camera only when the target nears the edge). A "screen shake" is a short tween on the camera's `offset` — leaving `position` untouched keeps the follow logic undisturbed.

---

## The audio system

### Buses: the mixing board

Godot's audio flows through **buses** — channels on a virtual mixing board (Audio panel, bottom dock; saved as `default_bus_layout.tres`). Every `AudioStreamPlayer` outputs into exactly one bus; buses process (volume, effects), then route **leftward** toward `Master`, which feeds the hardware. The unidirectional right-to-left routing makes feedback loops impossible.

```
AudioStreamPlayer ─▶ "Music" bus ──┐
AudioStreamPlayer ─▶ "Ambience" ───┼──▶ "Master" ──▶ speakers
AudioStreamPlayer ─▶ "SFX" ────────┘
   (volume_db per player)   (volume + effects per bus)   (keep < 0 dB!)
```

A sensible small-project layout — and Relax Room's actual one — is `Master`, `Music`, `Ambience`, `SFX`: user volume sliders map one-to-one onto buses, muting a category is one call, and effects (a gentle low-pass on `Ambience` for the "cozy rain behind glass" feel) apply per category. Buses support chains of effects: reverb, compressor, limiter, EQ, low/high-pass, spectrum analyzer (for visualizers), and more.

### Decibels, not percentages

All engine volume APIs speak **decibels** — a logarithmic scale matching human hearing. `0 dB` is full digital amplitude (not "loud" — the *ceiling*: above it, clipping distortion); `-6 dB` is roughly half amplitude; `-60 dB` and below is effectively silence; `-80 dB` is the conventional "off". Sliders must convert, because linear volume-to-dB mapping sounds wrong at the quiet end:

```gdscript
# Slider (0..1 linear) → dB, and back:
func _on_volume_slider_changed(value: float) -> void:
	var bus := AudioServer.get_bus_index(&"Music")
	AudioServer.set_bus_volume_db(bus, linear_to_db(value))   # linear_to_db(0.5) ≈ -6.02

func current_volume_linear() -> float:
	var bus := AudioServer.get_bus_index(&"Music")
	return db_to_linear(AudioServer.get_bus_volume_db(bus))

# Other AudioServer essentials:
AudioServer.set_bus_mute(AudioServer.get_bus_index(&"Ambience"), true)
```

> ⚠️ **Pitfall** — Assigning the slider value straight to `volume_db` (`player.volume_db = 0.7`) technically works — 0.7 dB is just *slightly louder than full* — which is why the bug ships: it does not sound obviously broken until the user drags the slider down and nothing much changes. Always `linear_to_db()` at the UI boundary.

### The three players

| Node | Positioning | Use |
|---|---|---|
| `AudioStreamPlayer` | None — plays "in your head" | Music, ambience, UI sounds |
| `AudioStreamPlayer2D` | Pans/attenuates by 2D distance to listener | Positional world SFX |
| `AudioStreamPlayer3D` | Full 3D spatialization | 3D games (unused here) |

```gdscript
var player := AudioStreamPlayer.new()
player.stream = preload("res://audio/music/forest_dawn.ogg")
player.bus = &"Music"
player.volume_db = linear_to_db(0.8)
add_child(player)
player.play()                                  # optionally play(from_seconds)
player.seek(42.0)                              # jump; get_playback_position() to read
player.stream_paused = true                    # pause WITHOUT resetting position
player.finished.connect(_on_track_finished)    # NOTE: never fires for looping streams
```

Format guidance: **Ogg Vorbis** for music/ambience (small, loops well — looping is a property on the `AudioStreamOggVorbis` resource); **WAV** for short SFX (decodes free, loop points set in the Import dock); MP3 is supported but Ogg is the better citizen. For randomized SFX variation, wrap streams in an `AudioStreamRandomizer` (random pitch/volume/stream selection) instead of writing your own jitter code.

### Bus effects at runtime

The Audio panel configures effects at design time; `AudioServer` manipulates the same chain live — the mechanism behind "muffle the music when a panel opens" polish:

```gdscript
var _lowpass := AudioEffectLowPassFilter.new()

func set_muffled(on: bool) -> void:
	var bus := AudioServer.get_bus_index(&"Music")
	if on and AudioServer.get_bus_effect_count(bus) == 0:
		_lowpass.cutoff_hz = 800.0                       # everything above sounds "behind a door"
		AudioServer.add_bus_effect(bus, _lowpass)
	elif not on and AudioServer.get_bus_effect_count(bus) > 0:
		AudioServer.remove_bus_effect(bus, 0)

# Or cheaper: keep the effect permanently and toggle it,
# which avoids add/remove churn:
AudioServer.set_bus_effect_enabled(bus, 0, on)
```

Sweeping `cutoff_hz` with a `tween_method` (from ~20000 down to ~600 over 0.3 s) turns the toggle into the smooth "dive underwater" transition players recognize from every polished game menu. The effect classes worth knowing by name: `AudioEffectLowPassFilter`/`HighPass`, `AudioEffectReverb`, `AudioEffectCompressor`, `AudioEffectLimiter` (a safety limiter on Master is cheap ship insurance against clipping), `AudioEffectEQ`, and `AudioEffectSpectrumAnalyzer` — the last one paired with `AudioServer.get_bus_effect_instance()` powers music visualizers.

### Fire-and-forget SFX

UI clicks and feedback sounds need a player that exists exactly as long as the sound. The standard autoload helper:

```gdscript
# Part of AudioManager: transient one-shot players on the SFX bus.
func play_sfx(stream: AudioStream, pitch_jitter: float = 0.0) -> void:
	var p := AudioStreamPlayer.new()
	p.stream = stream
	p.bus = &"SFX"
	if pitch_jitter > 0.0:
		p.pitch_scale = randf_range(1.0 - pitch_jitter, 1.0 + pitch_jitter)
	add_child(p)
	p.finished.connect(p.queue_free)     # self-cleaning: player dies with its sound
	p.play()
```

The `finished → queue_free` connection is the whole trick — no pool bookkeeping, no leaked players (verify with the orphan-node monitor). Pitch jitter of ±5-10% stops a repeated click sound from feeling machine-gun identical; for richer variation (multiple takes, volume ranges) configure an `AudioStreamRandomizer` resource in the editor instead of coding it. If profiling ever shows allocation churn from very high SFX rates — not a realistic concern for a desktop companion — this graduates into a fixed pool of reusable players, same API.

For world-positioned sound, swap in `AudioStreamPlayer2D` at the emitter's position: panning and distance attenuation (`max_distance`, `attenuation`) come free, relative to the current `AudioListener2D` (by default the active camera).

### Case study — Relax Room: dual-player crossfade

One `AudioStreamPlayer` cannot crossfade with itself — changing `stream` cuts audio instantly. The standard production pattern is two players and a tween:

```gdscript
# audio_manager.gd (autoload, excerpt) — seamless track transitions.
const FADE_TIME := 1.0

var _player_a: AudioStreamPlayer     # active
var _player_b: AudioStreamPlayer     # standby
var _fade_tween: Tween

func crossfade_to(stream: AudioStream) -> void:
	if _fade_tween and _fade_tween.is_valid():
		_fade_tween.kill()                       # interrupting a fade must not stack
	_player_b.stream = stream
	_player_b.volume_db = -80.0
	_player_b.play()

	_fade_tween = create_tween().set_parallel(true)
	_fade_tween.tween_property(_player_a, "volume_db", -80.0, FADE_TIME)
	_fade_tween.tween_property(_player_b, "volume_db", linear_to_db(_music_volume), FADE_TIME)
	_fade_tween.chain().tween_callback(_finish_swap)

func _finish_swap() -> void:
	_player_a.stop()
	var tmp := _player_a
	_player_a = _player_b
	_player_b = tmp
```

Fading in *decibel space* (as above) sounds slightly "middle-heavy"; fading the *linear* value via `tween_method(func(v: float): player.volume_db = linear_to_db(maxf(v, 0.0001)), 1.0, 0.0, FADE_TIME)` gives an equal-power feel. Relax Room ships the simple dB version — at 1 s fades, listeners cannot tell — but the linear variant is the audiophile answer.

---

## Tweens and timers

### Tween fundamentals

A `Tween` interpolates values over time — the tool for every "animate this property from here to there" need where an `AnimationPlayer` track would be overkill or where end values are only known at runtime (the official docs' own criterion). Tweens are created *bound to context*, start automatically, and free themselves when finished:

```gdscript
# Fade in a panel: animate the alpha sub-property over 0.3 s.
var tween := create_tween()
tween.tween_property(_panel, "modulate:a", 1.0, 0.3)

# Sequential by default — each tweener starts when the previous ends:
var t := create_tween()
t.tween_property(_sprite, "position:x", 500.0, 0.5)   # 1) slide right
t.tween_interval(0.2)                                  # 2) beat of silence
t.tween_property(_sprite, "modulate:a", 0.0, 0.3)      # 3) fade out
t.tween_callback(_sprite.queue_free)                   # 4) remove

# Parallel:
var p := create_tween().set_parallel(true)
p.tween_property(_sprite, "position:x", 500.0, 0.5)
p.tween_property(_sprite, "modulate:a", 0.0, 0.5)
p.chain().tween_callback(_done)          # chain(): back to sequential for the tail

# Mixed: parallel() marks ONE tweener to run alongside the previous one.
var m := create_tween()
m.tween_property(_a, "position:y", 0.0, 0.4)
m.parallel().tween_property(_b, "position:y", 0.0, 0.4)
```

The four tweener types: `tween_property` (animate a property; sub-properties via `:` paths like `"modulate:a"`, `"position:x"`), `tween_interval` (pure delay step), `tween_callback` (invoke a Callable at that point), `tween_method` (call a method every tick with the interpolated value — for anything not directly a property: shader parameters, `seek()` positions, custom setters). Godot 4.5 adds `tween_subtween(other_tween)` to compose reusable sub-animations.

Per-tweener modifiers refine each step: `.set_delay(0.1)`, `.set_trans(...)`, `.set_ease(...)`, `.from(start_value)` (animate from an explicit start instead of the current value), `.from_current()`, `.as_relative()` (target becomes an offset).

### Easing: transition × ease

Tween curves are the product of a **transition** (the mathematical shape) and an **ease** (which end gets the acceleration):

```gdscript
create_tween()\
	.set_trans(Tween.TRANS_BACK)\
	.set_ease(Tween.EASE_OUT)\
	.tween_property(_popup, "scale", Vector2.ONE, 0.35)
```

| Transition | Character |
|---|---|
| `TRANS_LINEAR` | Constant speed — mechanical; fine for volume/progress |
| `TRANS_SINE` | Gentle, subtle — the default choice for UI |
| `TRANS_QUAD/CUBIC/QUART/QUINT` | Increasingly sharp polynomial acceleration |
| `TRANS_EXPO` | Very sharp — dramatic swooshes |
| `TRANS_CIRC` | Circular curve — soft start, abrupt end (or inverse) |
| `TRANS_BACK` | Overshoots past the target, settles back — playful UI |
| `TRANS_ELASTIC` | Springy oscillation around the target |
| `TRANS_BOUNCE` | Bounces at the destination like a dropped ball |
| `TRANS_SPRING` | Physical spring feel (4.x addition) |

`EASE_IN` (slow start), `EASE_OUT` (slow end — usually right for things *arriving*), `EASE_IN_OUT`, `EASE_OUT_IN`. Rule of thumb: UI elements entering → `TRANS_SINE`/`TRANS_BACK` + `EASE_OUT`; leaving → `EASE_IN`.

### tween_method: animating what isn't a property

`tween_property` needs a real property path; everything else goes through `tween_method`, which calls a Callable with the interpolated value each tick — the bridge to shader parameters, audio positions, and derived state:

```gdscript
# Animate a shader uniform (no property path exists for it):
var mat := _sprite.material as ShaderMaterial
create_tween().tween_method(
	func(v: float) -> void: mat.set_shader_parameter(&"dissolve", v),
	0.0, 1.0, 0.8)

# Animated typewriter text — interpolate an INT and derive the display:
create_tween().tween_method(
	func(chars: int) -> void: _label.text = full_text.left(chars),
	0, full_text.length(), 1.2)

# Equal-power volume fade (interpolate LINEAR, apply as dB):
create_tween().tween_method(
	func(v: float) -> void: _player.volume_db = linear_to_db(maxf(v, 0.0001)),
	1.0, 0.0, FADE_TIME)
```

The lambda receives the eased, transitioned value; everything about trans/ease/delay composes exactly as with property tweeners.

### Kill/tracking discipline

Tweens run to completion even if you start another one on the same property — the two then fight, last-writer-wins per frame. Every retriggerable animation therefore needs the **track-and-kill idiom** (already visible in the crossfade case study):

```gdscript
var _hover_tween: Tween

func _on_mouse_entered() -> void:
	if _hover_tween and _hover_tween.is_valid():
		_hover_tween.kill()                      # cancel the running animation first
	_hover_tween = create_tween()
	_hover_tween.tween_property(self, "scale", Vector2(1.05, 1.05), 0.15)\
			.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)

func _on_mouse_exited() -> void:
	if _hover_tween and _hover_tween.is_valid():
		_hover_tween.kill()
	_hover_tween = create_tween()
	_hover_tween.tween_property(self, "scale", Vector2.ONE, 0.15)
```

Lifecycle facts to keep straight: a tween created with `node.create_tween()` is bound to that node — it pauses with it and dies with it (so tweens do not outlive their targets); `get_tree().create_tween()` is unbound, useful for tweening autoload state, and `bind_node()` can attach it later. `kill()` aborts and invalidates; `stop()` halts and *rewinds* state, allowing `play()` again; `pause()` halts in place. `await tween.finished` is the idiomatic way to sequence code after an animation. `set_loops()` (no args = infinite) repeats the whole sequence — remember infinite-looping tweens never emit `finished`.

> ⚠️ **Pitfall** — A tween with **zero valid tweeners** (e.g., you created it but a guard skipped all `tween_*` calls) emits an error and self-destructs at frame end. Similarly, tweening a property on a freed object kills the tween with an error. If a tween may target a dying node, bind it to that node so they die together — silently and correctly.

### Timers

For "do something after N seconds" without interpolation, use timers — node or one-shot:

```gdscript
# One-shot, no node: SceneTreeTimer. Fire-and-forget delays.
await get_tree().create_timer(1.5).timeout
_show_hint()

# Repeating / controllable: the Timer node.
var timer := Timer.new()
timer.wait_time = 30.0
timer.one_shot = false                 # repeat every 30 s
timer.autostart = true
timer.timeout.connect(_on_autosave_tick)
add_child(timer)
# timer.start(5.0) restarts with an override; stop(); time_left to inspect.
```

| | `SceneTreeTimer` (`create_timer`) | `Timer` node | `Tween` |
|--|--|--|--|
| Repeats | No | Yes | Via `set_loops()` |
| Cancelable | Not directly (let it lapse) | `stop()` | `kill()` |
| Pauses with tree | Optional (arg 2) | Follows `process_mode` | Follows bound node |
| Best for | Ad-hoc delays in coroutines | Autosave ticks, cooldowns, polling | Value animation |

> ⚠️ **Pitfall** — `await get_tree().create_timer(...)` inside a node that might be freed: the timer fires anyway (it belongs to the tree, not to you), resuming a coroutine whose `self` is gone; the next property access errors. In such flows re-check `is_instance_valid(self)`-sensitive state after the await, or use a `Timer` child node, which dies with you.

### Tween or AnimationPlayer?

Both animate properties; they solve different problems and coexist in most projects:

| | `Tween` | `AnimationPlayer` |
|--|---|---|
| Authored | In code, at runtime | Visually, on a timeline in the editor |
| End values | Computed at runtime — dynamic targets | Fixed keyframes (with some runtime params) |
| Strength | Reactive UI, procedural motion, chained logic | Choreography: multi-property, multi-node, artist-tunable |
| Events | `tween_callback`, `finished` | Call-method tracks, `animation_finished` |
| Typical use here | Panel fades, crossfades, hover states | Cutscene-like sequences, complex character rigs |

The official docs' rule of thumb is the right one: *AnimationPlayer when you know the animation at design time; Tween when you only know it at runtime.* A door that always opens the same way is a keyframed animation an animator can polish; a panel that slides to wherever the mouse happens to be is a tween by definition.

### Case study — Relax Room: animation inventory

Everything animated in Relax Room is either a Tween or an `AnimatedSprite2D` — no `AnimationPlayer` at all, a deliberate scope decision. Tweens: panel fade/slide in-out, crossfades, coin-count roll-up, decoration drop bounce (`TRANS_BOUNCE`, `EASE_OUT`, 0.4 s), hover scaling. Timers: 30 s autosave tick (with dirty-flag check), menu character blink (randomized `wait_time` between cycles), idle-detection for the low-CPU mode downshift.

---

## 2D physics introduction

### The four body types

Every physics participant is a `CollisionObject2D` with one or more `CollisionShape2D` children defining its geometry. The four flavors divide by *who moves it and how*:

| Node | Moved by | Collides | Use for |
|---|---|---|---|
| `StaticBody2D` | Nobody (fixed) | Others collide with it | Walls, floors, furniture |
| `AnimatableBody2D` | You/AnimationPlayer (kinematic) | Pushes others correctly | Moving platforms, doors |
| `CharacterBody2D` | Your code via `move_and_slide()` | Slides along others | Player/NPC characters |
| `RigidBody2D` | The physics simulation (forces) | Full dynamics | Crates, balls, ragdolls |
| `Area2D` | N/A — no collision, detection only | Overlap events | Triggers, pickups, zones |

The philosophical split: `CharacterBody2D` gives you *control* (you write the movement, physics gives you collision resolution); `RigidBody2D` gives you *simulation* (you apply forces and impulses; setting its `position` directly fights the simulator and is a bug — steer inside `_integrate_forces()` when you must override).

### CharacterBody2D and move_and_slide

```gdscript
extends CharacterBody2D

const SPEED := 90.0          # pixels/second

func _physics_process(_delta: float) -> void:
	var direction := Input.get_vector(&"move_left", &"move_right", &"move_up", &"move_down")
	velocity = direction * SPEED       # velocity is a BUILT-IN property (px/s)
	move_and_slide()                   # no arguments: reads velocity, applies delta itself

	if velocity.length_squared() > 0.0:
		_sprite.play(&"walk")
		_sprite.flip_h = velocity.x < 0.0
	else:
		_sprite.play(&"idle")
```

`move_and_slide()` semantics, precisely: it moves by `velocity * delta` (delta applied internally — do **not** pre-multiply), slides along surfaces it hits, *modifies* `velocity` to reflect the slides, and updates the floor/wall state. For a top-down game like Relax Room set `motion_mode = MOTION_MODE_FLOATING` (every contact is a "wall"; no gravity concept); the default `MOTION_MODE_GROUNDED` is for side-scrollers, where `is_on_floor()`, `up_direction`, `floor_snap_length`, and slope properties become meaningful.

For a platformer flavor of the same node:

```gdscript
func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity += get_gravity() * delta          # project-configured gravity vector
	if Input.is_action_just_pressed(&"jump") and is_on_floor():
		velocity.y = -320.0
	velocity.x = Input.get_axis(&"move_left", &"move_right") * SPEED
	move_and_slide()
```

Inspecting what you hit after a slide:

```gdscript
for i in get_slide_collision_count():
	var col := get_slide_collision(i)              # KinematicCollision2D
	var other := col.get_collider()
	if other is RigidBody2D:
		(other as RigidBody2D).apply_central_impulse(-col.get_normal() * 20.0)
```

The lower-level alternative `move_and_collide(velocity * delta)` (note: *you* multiply by delta here) stops at the first contact and returns it — the right tool for projectiles and custom responses.

The `_sprite` in the movement example is an `AnimatedSprite2D` — worth one paragraph here since character code always pairs with it (full sprite pipeline: [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md)). Its `SpriteFrames` resource holds named animations ("idle", "walk") built from frames or spritesheet regions in the bottom-panel editor; code drives it with `play(&"walk")`, `stop()`, `flip_h`, `speed_scale`, and reacts to `animation_finished` / `frame_changed`. The one habit to form: check `_sprite.animation != &"walk"` before `play(&"walk")` in per-frame code — unconditional `play()` calls are harmless in 4.x (they do not restart the animation), but the guard documents intent and survives engine-behavior edge cases around `frame` manipulation.

### RigidBody2D in brief

`RigidBody2D` hands motion to the simulator; your job becomes *influencing*, not positioning:

```gdscript
extends RigidBody2D

func _ready() -> void:
	mass = 0.5
	gravity_scale = 1.0                       # 0.0 = floats; multiplies project gravity
	# body_entered requires OPT-IN contact reporting — the #1 RigidBody FAQ:
	contact_monitor = true
	max_contacts_reported = 4
	body_entered.connect(_on_body_entered)

func nudge(direction: Vector2) -> void:
	apply_central_impulse(direction * 40.0)   # instantaneous kick (one-time)

func _physics_process(_delta: float) -> void:
	if _fan_active:
		apply_central_force(Vector2.LEFT * 15.0)   # continuous push (per tick)

func _on_body_entered(_body: Node) -> void:
	AudioManager.play_sfx(THUD_SFX, 0.08)
```

Rules of engagement: *impulses* for instant events, *forces* for continuous influence, `linear_velocity` writable but with care (it overrides accumulated simulation), `position` effectively read-only — teleporting requires `PhysicsServer2D` state resets or the `freeze` property. `freeze = true` with `FREEZE_MODE_KINEMATIC` turns it into a scripted body temporarily (pick-up-and-carry mechanics). Bodies **sleep** when idle (an optimization — `sleeping`/`can_sleep`); a sleeping stack of crates wakes on contact automatically. Relax Room uses exactly one `RigidBody2D`: the cat toy ball, because "physics toy" is its entire feature description.

### Area2D: sensing without colliding

`Area2D` detects overlaps and reports them as signals — plus it can locally override gravity and audio attenuation:

```gdscript
# drop_zone.gd — where decorations may be placed.
extends Area2D

func _ready() -> void:
	body_entered.connect(_on_body_entered)     # also: body_exited, area_entered/exited
	monitoring = true                          # I actively scan (default true)
	monitorable = false                        # others cannot scan me

func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group(&"character"):
		SignalBus.character_entered_zone.emit(name)

func occupied() -> bool:
	return not get_overlapping_bodies().is_empty()   # polling alternative to signals
```

> ⚠️ **Pitfall** — Physics signals (`body_entered` etc.) fire **during the physics step**. Adding/removing/reparenting nodes inside the handler raises "Can't change this state while flushing queries". The fix is always the same: defer the mutation (`queue_free()`, `call_deferred(...)`, `set_deferred(...)`) — see [Scenes, instancing and groups](#scenes-instancing-and-groups).

### Collision layers and masks

Every `CollisionObject2D` has two 32-bit fields that together answer "who interacts with whom":

- **`collision_layer` — what I *am*.** The categories this object belongs to.
- **`collision_mask` — what I *look for*.** Interaction happens when *my mask* contains *your layer*.

```
Named layers (Project Settings → Layer Names → 2D Physics):
  1: world      2: character      3: furniture      4: drop_zones

Character body:  layer = character            mask = world | furniture
Drop zone area:  layer = drop_zones           mask = character
Furniture:       layer = furniture            mask = (empty — it scans nobody)
```

The relation is directional: a zone with `mask = character` sees the character even if the character's mask ignores `drop_zones` — detection needs only one side to look. In code, layers are bit numbers:

```gdscript
collision_layer = 0b0010                        # raw bits: layer 2 only
set_collision_mask_value(3, true)               # by index: also scan layer 3
var scans_furniture := get_collision_mask_value(3)
```

> ✅ **Best practice** — Name every layer you use in Project Settings *before* wiring bodies, and audit with the debugger's **Visible Collision Shapes** (Debug menu → Visible Collision Shapes) whenever an interaction mysteriously fails. Nine out of ten "collision doesn't work" reports are an unchecked mask bit or a `CollisionShape2D` with no shape assigned.

### Choosing collision shapes

Shape choice affects both feel and cost. The working rules: **characters get capsules or circles** — rounded bottoms glide over 1-pixel seams and corners that snag a rectangle; **walls and floors get rectangles/segments** (or `WorldBoundaryShape2D` for infinite planes); **use the fewest, simplest shapes that lie to the player acceptably** — a top-down character's shape should cover the *feet*, not the sprite, so it can walk "behind" furniture correctly. Never scale a `CollisionShape2D` node (the editor warns; scaled shapes break the physics math) — set the shape resource's own extents/radius instead. And remember shape resources are Resources: two `CollisionShape2D`s sharing one `RectangleShape2D` resize together — `duplicate()` or *Make Unique* when they must differ.

### Raycasts and direct space queries

```gdscript
# Persistent ray as a node: enabled every physics frame.
@onready var _ray: RayCast2D = $RayCast2D    # set target_position + mask in Inspector

func _physics_process(_delta: float) -> void:
	if _ray.is_colliding():
		_highlight(_ray.get_collider())

# Ad-hoc query without a node — from _physics_process only:
func _clear_path_to(target: Vector2) -> bool:
	var space := get_world_2d().direct_space_state
	var query := PhysicsRayQueryParameters2D.create(global_position, target)
	query.collision_mask = 0b0001              # only the "world" layer blocks walking
	var hit := space.intersect_ray(query)      # {} if nothing hit
	return hit.is_empty()
```

For area-of-effect checks, the same `direct_space_state` offers `intersect_shape()` and `intersect_point()` with `PhysicsShapeQueryParameters2D` — the no-node counterpart of `ShapeCast2D`.

### Case study — Relax Room: minimal physics

A desktop companion needs almost no physics, and using *almost none* is the lesson: the character is a `CharacterBody2D` (floating mode, WASD + walk-to-click), room bounds are four `StaticBody2D` segments, drop zones are `Area2D`s, and *decorations have no physics at all* — placement validity is a rectangle check in code, because simulating fifty static sofas would buy nothing and cost broad-phase time every tick. Choosing *not* to use a physics feature is a performance decision (see next section).

---

## Performance fundamentals

> Working overview; [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) (Module 14) is the full profiling workflow with the 15 FPS idle-budget methodology.

### Measure first: the Performance singleton

```gdscript
# The numbers behind the Debugger → Monitors graphs, queryable in code:
Performance.get_monitor(Performance.TIME_FPS)                         # frames/second
Performance.get_monitor(Performance.TIME_PROCESS)                     # s spent in process
Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)             # s spent in physics
Performance.get_monitor(Performance.MEMORY_STATIC)                    # bytes
Performance.get_monitor(Performance.OBJECT_NODE_COUNT)                # live nodes
Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)         # leaked nodes!
Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME) # batching health

# Project-specific counters graph themselves alongside the built-ins:
Performance.add_custom_monitor(&"relax_room/decorations",
		func() -> int: return _decoration_count)
```

An in-game FPS/node overlay is a ten-line Label reading these — Relax Room binds one to a debug hotkey. For frame-by-frame *attribution* (which function costs what), use the **Profiler** panel: run the game, press Start on the Profiler tab, interact, then sort by self-time. The **Visual Profiler** tab does the same for GPU-side work, and **Video RAM** lists textures by memory.

### Common 2D bottlenecks (ranked by frequency in practice)

1. **Per-frame allocation.** Building Strings, Arrays, or Dictionaries inside `_process` on many nodes. Symptoms: rising `MEMORY_STATIC`, periodic hitches. Fix: hoist allocations, reuse buffers, format strings only when the value changed.
2. **Node lookups in hot paths.** `$Path` and `get_node()` every frame instead of `@onready` caching.
3. **Unbatched draws.** Thousands of `CanvasItem`s with mixed textures break batching; watch `RENDER_TOTAL_DRAW_CALLS_IN_FRAME`. Fix: texture atlases (see [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md)), fewer unique materials, `MultiMeshInstance2D` for swarms.
4. **Everything processes.** Hundreds of nodes with non-empty `_process`. Fix: `set_process(false)` on idle nodes; event-driven design (signals wake things up).
5. **Physics oversubscription.** Bodies that never needed to be bodies; masks so broad every pair is tested. Fix: narrow masks; use plain sprites when nothing collides.
6. **Overdraw and oversized textures.** Full-screen semi-transparent layers stacked; 4K textures displayed at 64 px.

### Visibility culling helpers

The renderer already skips canvas items outside the camera, but your *scripts* keep running for off-screen nodes. Two helper nodes close that gap: `VisibleOnScreenNotifier2D` emits `screen_entered`/`screen_exited` (pause an off-screen animation, despawn a fled projectile), and `VisibleOnScreenEnabler2D` goes further — it automatically disables processing of a target node while off-screen and re-enables on entry, a zero-code optimization for busy scrolling scenes:

```gdscript
@onready var _notifier: VisibleOnScreenNotifier2D = $VisibleOnScreenNotifier2D

func _ready() -> void:
	_notifier.screen_exited.connect(func() -> void: _sprite.pause())
	_notifier.screen_entered.connect(func() -> void: _sprite.play())
```

### Object pooling

Instantiating and freeing nodes is not free — script `_init`, tree entry, server registration. When the *same kind* of node churns rapidly (bullets, particles-with-logic, floating damage numbers), recycle instead:

```gdscript
# float_text_pool.gd — recycles floating "+5" labels instead of churning nodes.
extends Node

const SCENE := preload("res://scenes/fx/float_text.tscn")
var _pool: Array[FloatText] = []

func acquire() -> FloatText:
	var item: FloatText
	if _pool.is_empty():
		item = SCENE.instantiate()
		add_child(item)
	else:
		item = _pool.pop_back()
	item.visible = true
	item.set_process(true)
	return item

func release(item: FloatText) -> void:
	item.visible = false
	item.set_process(false)          # parked: invisible, not processing, NOT freed
	_pool.append(item)
```

The pooled object must expose a `reset()` the acquirer calls — stale state from the previous life is the classic pooling bug. And the honest caveat first: pool only what profiling convicts. Godot instantiation is fast enough that a desktop companion never needs this; a bullet-hell spawning 500 nodes/second does. Premature pooling adds lifecycle complexity (who resets? who releases? double-release?) with zero measured benefit.

### The desktop-companion budget

A game may happily use 100% of a core; a companion app that does so gets uninstalled. Godot has first-class support for the "mostly idle" profile:

```gdscript
# Low-processor mode: render ONLY when something changed (also a Project Setting:
# application/run/low_processor_mode — enabled by default for non-game apps).
OS.low_processor_usage_mode = true
OS.low_processor_usage_mode_sleep_usec = 8000   # sleep granularity between frames

Engine.max_fps = 30                              # cap active-state rendering
# Relax Room policy: 30 FPS focused, drop to a 10 FPS cap when the window
# loses focus (NOTIFICATION_APPLICATION_FOCUS_OUT), restore on focus-in.
```

> ✅ **Best practice** — Optimize only what the profiler convicts. The sequence is: reproduce → measure (Monitors) → attribute (Profiler) → fix the top item → measure again. GDScript rewrites in C#/GDExtension are the *last* resort, after algorithmic and structural fixes — in UI-heavy 2D apps the bottleneck is almost never raw script arithmetic.

### Case study — Relax Room: renderer choice and the settings that matter

Performance begins in Project Settings, before any code. Godot 4 offers three rendering methods:

| Method | API | GPU requirement | Features | Relax Room? |
|--------|-----|-----------------|----------|-------------|
| Forward+ | Vulkan | Modern discrete/recent iGPU | Everything (clustered lights, advanced 3D) | No — overkill for 2D UI |
| Mobile | Vulkan | Mid-range | Most features, mobile-optimized | No — still heavier than needed |
| **GL Compatibility** | OpenGL 3.3 | Practically any GPU of the last decade | 2D-complete feature set | **Yes** — widest laptop/office-PC support |

For a 2D desktop companion the Compatibility renderer is the strategic choice: it runs on the integrated graphics of every machine the target audience owns, starts faster, and gives up nothing the app uses. The full settings block the project pins:

```ini
[application]
config/name = "Relax Room"
run/main_scene = "res://features/menu/main_menu.tscn"
run/low_processor_mode = true                      # render only on change

[display]
window/size/viewport_width = 1280
window/size/viewport_height = 720
window/stretch/mode = "canvas_items"               # UI scales with the window
window/per_pixel_transparency/allowed = true       # companion-on-desktop mode

[rendering]
renderer/rendering_method = "gl_compatibility"
textures/canvas_textures/default_texture_filter = 0  # NEAREST — crisp pixel art

[gui]
theme/custom = "res://common/theme/cozy_theme.tres"

[physics]
common/physics_ticks_per_second = 30               # a companion needs no 60 Hz physics
```

Each line is a decision with a reason attached — the halved physics rate alone removes half the physics cost for an app whose only body ambles across a room. Stretch modes, filters, and export presets get full treatment in [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) and [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md).

---

## Debugging workflow

### The debugger, properly used

Run with F5 and the **Debugger** bottom panel becomes mission control. Breakpoints: click the script editor gutter (or F9) on any line; execution freezes there with locals, stack, and the full remote tree inspectable. Step Over `F10`, Step Into `F11`, Continue `F12`. Two less-known powers: the `breakpoint` *keyword* — a line of GDScript that triggers the debugger when executed, perfect inside an `if` for conditional breaks — and **Break on Error**, which freezes the game at the moment a `push_error` or engine error fires, stack intact.

```gdscript
if coins < 0:        # "how did coins go negative?!"
	breakpoint       # acts exactly like a gutter breakpoint, but conditional & committable
```

### The debugger panels, mapped

| Panel (Debugger dock) | What it answers |
|---|---|
| **Stack Trace** | Where am I, and how did I get here? (while paused) |
| **Errors** | Every `push_error`/`push_warning`/engine error with expandable C++/GDScript stacks |
| **Profiler** | Which GDScript functions cost what, per frame — sortable by self/total time |
| **Visual Profiler** | GPU/render pipeline cost breakdown per frame |
| **Monitors** | Live graphs of every `Performance` monitor, custom ones included |
| **Video RAM** | Which textures occupy how much GPU memory |
| **Misc** | *Clicked Control* (which Control ate the click) and last-clicked info |
| **Network Profiler** | RPC traffic (multiplayer projects) |

### Remote scene tree

While the game runs, the Scene dock gains a **Remote** tab: the *live* tree of the running game. Click any node to inspect and *edit* its properties in real time — volume, positions, `visible` flags — without restarting. This is the fastest answer to the two most common confusions: "did my node actually get added?" and "what is the actual value at runtime?" (The Local tab shows the edited scene again.) Under Debugger → Misc, "Clicked Control" reports which Control consumed your last click — the instant diagnosis for `mouse_filter` problems.

### Printing and logging

```gdscript
print("state=", state, " pos=", global_position)   # concatenates args
print_rich("[color=yellow]slow frame[/color]")     # BBCode in the output panel
print_debug("only in debug builds, with script:line suffix")
prints("a", "b", "c")                              # space-separated
printerr("goes to stderr")

push_warning("Recoverable oddity — yellow entry, collapsible, with stack")
push_error("Broken invariant — red entry with stack trace; does NOT halt")

assert(coins >= 0, "coins must never go negative")  # debug builds only:
                                                    # halts at this line in the debugger.
                                                    # STRIPPED in release — never put
                                                    # side effects inside assert()!
```

`push_error` vs `assert`: `push_error` reports and continues (production telemetry); `assert` documents an invariant and stops the debugger exactly where it broke (development). Both beat `print` spam, which scrolls away and lies about ordering across threads.

The engine can mirror all output to disk without code: **Project Settings → Debug → File Logging** (`debug/file_logging/enable_file_logging`) writes rotating logs to `user://logs/` in exported builds too — enable it before your first external tester, because "send me `user://logs/godot.log`" is the cheapest crash report pipeline you will ever build.

### Case study — Relax Room: the AppLogger rule

Project rule: **no naked `print()` in committed code.** Everything goes through the `AppLogger` autoload — `AppLogger.info("AudioManager", "Track started", {"id": track_id})` — which timestamps, levels, and mirrors entries to `user://logs/app.log` with rotation. The payoff arrives the first time a tester says "it broke yesterday evening": you read the log instead of asking them to reproduce. `push_warning`/`push_error` remain in use for programmer-facing contract violations, because they carry stack traces into the debugger.

### Micro-benchmarking honestly

When two implementations compete, measure with `Time.get_ticks_usec()` — but respect the checklist that keeps the numbers meaningful:

```gdscript
func benchmark(label: String, iterations: int, fn: Callable) -> void:
	fn.call()                                    # warm-up: JIT caches, resource loads
	var start := Time.get_ticks_usec()
	for i in iterations:
		fn.call()
	var total := Time.get_ticks_usec() - start
	print("%s: %.2f µs/op (%d ops)" % [label, float(total) / iterations, iterations])

func _ready() -> void:
	benchmark("typed sum", 10_000, _sum_typed)
	benchmark("untyped sum", 10_000, _sum_untyped)
```

The checklist: warm up before timing; iterate enough that the clock granularity vanishes; compare **release builds** too (debug builds carry checks that distort ratios); and benchmark the *real workload*, not a toy loop the optimizer may treat differently. Most importantly: a 3× win in a function taking 0.01% of the frame is a 0.02% win — check the profiler's attribution *before* the bake-off.

### Command line and diagnostics

```
godot --verbose            # engine internals: driver init, resource loads
godot -d                   # run project in debug from CLI
godot --debug-collisions   # visible collision shapes without the editor
godot --headless           # no window/audio — CI and batch tools
```

In-editor equivalents live under the **Debug menu**: Visible Collision Shapes, Visible Navigation, plus Debugger → Monitors/Profiler covered above. Runtime introspection helpers: `get_tree().root.print_tree_pretty()` dumps the live tree to the console; `Node.print_orphan_nodes()` lists leaks; `OS.is_debug_build()` gates debug-only overlays; `Engine.is_editor_hint()` distinguishes editor execution in `@tool` scripts.

> ⚠️ **Pitfall** — "It works in the editor but not when exported" is a *category*, not a mystery: usual suspects are writes to `res://` (read-only when packed), resources loaded by string paths the export scanner missed (add them under Export → Resources), `assert`/debug-only code holding logic, and case-sensitive path mismatches that Windows forgave but the packed filesystem does not. Test exported builds early — [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md) covers the pipeline.

---

## Editor productivity

### Shortcuts that pay rent

| Shortcut | Action |
|----------|--------|
| `F1` | Search the built-in class reference (offline, always current for your version) |
| `F5` / `F6` / `F8` | Run project / run current scene / stop |
| `F9` | Toggle breakpoint on current line |
| `F10` / `F11` / `Shift+F11` / `F12` | Step over / into / out / continue (while paused) |
| `Ctrl+Shift+F` | Find in Files — search text across the whole project |
| `Ctrl+Click` on a symbol | Go to definition (works for engine classes too) |
| `Ctrl+Space` | Force the autocomplete popup |
| `Ctrl+D` | Duplicate line (script editor) / duplicate node (scene dock) |
| `Ctrl+K` | Toggle comment on selection |
| `Alt+Up` / `Alt+Down` | Move current line/selection up/down |
| `Ctrl+Alt+O` | Quick-open any resource by fuzzy name (verify in Editor Settings → Shortcuts) |
| `Ctrl+B` | Toggle bookmark on current line; navigate bookmarks from the gutter menu |

The class reference deserves a habit: `F1`, type `Tween`, and you get the exact API *for the version you are running* — faster and more reliable than a browser, and it works offline. Docstrings you write with `##` comments join this system for your own classes.

### Editor features that beginners under-use

- **Scene-unique names (`%`)** — right-click a node → *Access as Unique Name*. Refactor-proof references within a scene; covered in [Static typing and annotations](#static-typing-and-annotations).
- **Script templates** — Editor Settings lets you define the skeleton new scripts start from; a team template with `class_name`-slot, section comments in style-guide order, and a typed `_ready` saves a decision per file.
- **The embedded game window (4.4+)** — the running game docks inside the editor; combined with the Remote tree you can tweak-and-observe on one monitor.
- **Multi-caret editing** — `Ctrl+Click` for extra carets; `Ctrl+D`-style select-next-occurrence workflows make repetitive edits safe.
- **FileSystem dock dependencies** — right-click a file → *View Owners* / *Dependencies* before moving or deleting anything; Godot tracks references and offers to fix paths on move (still: move files *inside the editor*, not in Explorer, or you orphan `.import` metadata).
- **Node dock → Groups tab** — inspect and assign groups visually; the Project Settings *Global Groups* page (4.2+) registers names with descriptions so typos surface.

### Project layout conventions

Godot imposes no folder structure; adopt one on day one. This course uses feature-first grouping (the GDQuest recommendation): everything belonging to a feature — scene, script, art, sounds — lives together, so deleting the folder deletes the feature.

```
res://
├── autoload/            # signal_bus.gd, game_manager.gd, audio_manager.tscn ...
├── common/              # shared across features: theme, base classes, utils
│   ├── theme/           #   cozy_theme.tres, fonts
│   └── components/      #   reusable scenes (fade_overlay.tscn ...)
├── features/
│   ├── room/            #   room.tscn, room.gd, room sprites
│   ├── character/       #   character.tscn/.gd, spritesheets
│   ├── music_panel/     #   panel scene+script+icons together
│   └── shop/
├── data/                # .tres catalogs, JSON — content, not code
├── audio/               # music/, ambience/, sfx/  (shared streams)
└── tools/               # EditorScripts, dev-only scenes
```

Version-control hygiene that goes with it: ignore `.godot/` (cache) and exported builds; **commit** `.import` and `.uid` sidecars; move/rename files only inside the editor so references re-link. Text-format everything (`.tscn`/`.tres`, not binary) so diffs are reviewable — a merge conflict in a text scene is unpleasant; in a binary one it is fatal.

### Tool scripts: automating the editor

For one-off batch work — renaming nodes, generating placeholder resources, auditing scenes — an `EditorScript` beats manual clicking:

```gdscript
# tools/audit_missing_textures.gd — run with File → Run (Ctrl+Shift+X)
@tool
extends EditorScript

func _run() -> void:
	var root := get_scene()                    # the scene open in the editor
	if root == null:
		push_warning("Open a scene first.")
		return
	var missing := 0
	for node in root.find_children("*", "Sprite2D", true):
		if (node as Sprite2D).texture == null:
			print("Missing texture: ", root.get_path_to(node))
			missing += 1
	print("Audit done — %d sprite(s) without texture." % missing)
```

One rung up, an **EditorPlugin** (an `addons/<name>/` folder with a `plugin.cfg` and a `@tool` script extending `EditorPlugin`) can add dock panels, custom node types (`add_custom_type`), import plugins, and inspector extensions — the mechanism behind everything on the Asset Library. Writing one is out of scope here, but recognize the shape: much of "the editor" is itself plugins, and a project-local plugin that automates *your* repetitive task is often an afternoon's work.

> ✅ **Best practice** — Keep an eye on the `.godot/` directory's role: it is a *disposable cache* (imported assets, script metadata). Never commit it; deleting it forces a clean reimport, which is the first remedy for mysterious editor state (stale autocompletion, ghost resources). Commit `.import` sidecar files *next to assets*, though — they carry your import settings.

---

## Godot 3 to 4 migration notes

> **Migration note** — This section exists because most tutorials older than 2023 (and many AI answers trained on them) use Godot 3 syntax. Everything on the *left* column is **Godot 3 only** and will not run in 4.5; use it solely to translate old material while reading.

| Godot 3 | Godot 4 | Notes |
|---------|---------|-------|
| `export var x` | `@export var x` | Annotations replaced keywords |
| `onready var x` | `@onready var x` | Same change |
| `tool` (first line) | `@tool` | Same change |
| `yield(obj, "signal")` | `await obj.signal_name` | Coroutines redesigned |
| `yield(get_tree(), "idle_frame")` | `await get_tree().process_frame` | Renamed signal too |
| `connect("sig", self, "_m")` | `obj.sig.connect(_m)` | Callable-based; typo-safe |
| `emit_signal("sig", a)` | `sig.emit(a)` | First-class signals |
| `funcref(self, "m")` | `m` (method reference) | Callables everywhere |
| `var t = Tween.new()` + node | `var t = create_tween()` | Tweens are transient, node-bound |
| `KinematicBody2D` | `CharacterBody2D` | Renamed + reworked |
| `move_and_slide(vel, up)` | `velocity = vel; move_and_slide()` | Velocity is a property; no args |
| `Area2D.overlaps_body()` | same | Unchanged, listed to reassure |
| `instance()` | `instantiate()` | Renamed |
| `PoolStringArray` etc. | `PackedStringArray` etc. | Pool→Packed family rename |
| `OS.get_screen_size()` | `DisplayServer.screen_get_size()` | OS/DisplayServer split |
| `VisualServer` | `RenderingServer` | Renamed |
| `File` / `Directory` | `FileAccess` / `DirAccess` | Static-friendly redesign |
| `rand_range(a, b)` | `randf_range(a, b)` / `randi_range(a, b)` | Typed variants |
| `deg2rad` / `rad2deg` | `deg_to_rad` / `rad_to_deg` | Renamed |
| `setget setter, getter` | inline `set(v):` / `get:` blocks | Property syntax redesign |
| `TileMap` (3.x/4.0-4.2) | `TileMapLayer` (4.3+) | One node per layer now |
| `master`/`puppet` keywords | `@rpc(...)` annotation | Networking reworked |
| GDScript untyped by default | Static typing throughout | 2.0 compiler optimizes typed code |

Version-inside-4.x notes you may hit in slightly older 4.x material: static variables and `_static_init()` need 4.1+; `@export_custom`/`@export_storage` and `match ... when` guards need 4.3+; typed dictionaries `Dictionary[K, V]` and `@export_tool_button` need 4.4+; `@abstract`, variadic `...args`, and `tween_subtween` need 4.5+.

---

## Best practices

The consolidated checklist — every item was argued for in its section above; this is the review-time reference.

**Language and style**
1. Fully type everything: parameters, returns, variables (`:=` where the value makes the type obvious). Raise the `untyped_declaration` warning to error project-wide.
2. Follow the official order-of-declarations and naming conventions (files `snake_case`, classes `PascalCase`, signals past-tense, privates `_prefixed`). Consistency is a navigation feature.
3. Prefer `StringName` literals (`&"jump"`) for identifiers used in comparisons: actions, groups, animations, bus names.
4. `100.0` not `100` for floats; watch what `:=` infers.
5. Promote any lambda that outgrows three lines into a named private method.

**Architecture**
6. Call down, signal up. A node never reaches for `get_parent()` to *command* anything.
7. Bus signals are facts (`decoration_placed`), never commands (`save_decoration_please`); one-listener imperative signals should be method calls.
8. Every `connect` to a longer-lived object (autoload, bus) has a `disconnect` in `_exit_tree()`.
9. Autoloads only for global, stateful, unique, eternal services; order = dependency declaration; each depends only on autoloads above it.
10. Reference nodes as `%UniqueName` within scenes, `@export var n: NodeType` across boundaries; raw `$deep/paths` only for stable local children.

**Lifecycle and memory**
11. Configure instances *before* `add_child()`; wire signals in `_ready()`.
12. `queue_free()`, not `free()`; `is_instance_valid()` before touching stored references that might have died; `print_orphan_nodes()` in your quit path during development.
13. Re-validate state after every `await`; never await signals of objects you do not own without a plan for their death.
14. Track-and-kill every retriggerable Tween; bind tweens to the node they animate.

**Data**
15. Ship read-only data as typed custom Resources; persist user data as JSON/ConfigFile/SQLite in `user://` — never `load()` untrusted resource files, never write to `res://`.
16. `duplicate()` consciously: shared resources are a feature until they are a bug; `duplicate(true)` for nested containers/sub-resources.
17. Persist enum *names*, not ints; never reorder a shipped enum.

**Input, UI, audio**
18. Gameplay input in `_unhandled_input` or polling; `_input()` only for capture-everything features; leave `ui_*` actions to the UI.
19. Inside containers, configure `custom_minimum_size` + size flags — never `position`/`size`. Decorative overlays get `mouse_filter = IGNORE`.
20. All colors/fonts in the Theme; `linear_to_db()` at every volume-slider boundary; keep the Master bus under 0 dB.

**Production**
21. Profile before optimizing; watch draw calls and orphan nodes in Monitors; `low_processor_usage_mode` for desktop-companion idling.
22. No naked `print()` in committed code — structured logger plus `push_warning`/`push_error`; `assert` for invariants (side-effect-free — it is stripped in release).
23. Test exported builds early and often; the editor forgives what the export does not.

---

## Common errors and troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Node not found: "X"` on `$X` or `get_node` | Wrong path (case-sensitive), node renamed/moved, or node created later at runtime | Check the **Remote** tree for the real names; switch to `%UniqueName` or an `@export`ed reference; for late-created nodes, defer the lookup |
| `Invalid get index 'prop' (on base: 'Nil')` | Accessing a member of `null` — usually an `@onready` that failed (bad path) or a reference to a freed node | Fix the path; guard with `is_instance_valid()`; null your references after `queue_free()` |
| `Invalid get index 'prop' (on base: 'previously freed')` | Using a stored reference after the node was freed | Same as above — the message even tells you it *was* valid once |
| `Signal 'x' is already connected` | `connect()` ran twice (setup code re-entered, e.g. `_enter_tree` reconnects) | Connect in `_ready()`; guard with `is_connected()`; or disconnect in `_exit_tree()` |
| `Can't change this state while flushing queries` | Tree mutation (add/remove/reparent/`monitoring=`) inside a physics callback | `call_deferred()` / `set_deferred()` / `queue_free()` for the mutation |
| Function stops mid-body, no error | `await` on a signal whose emitter was freed (or never emits) | Await only signals you control; add timeouts; re-validate after each `await` |
| `Cannot convert argument from int to float` (or similar) | Untyped `Variant` flowed into a typed parameter; often JSON numbers | Cast explicitly (`float(x)`, `x as float`); re-validate types at JSON boundaries |
| Changed a script default; scene ignores it | The scene stored the old exported value, which overrides the default | Inspector → right-click property → *Revert* (the ↺ arrow) |
| Clicks never reach the game world | A full-rect Control with `mouse_filter = STOP` (dimmer, margin, spacer) is eating them | Debugger → Misc → *Clicked Control* to identify it; set `mouse_filter = IGNORE` |
| UI child won't move/resize from code | It sits inside a Container, which owns its geometry | Set `custom_minimum_size` + size flags, or reparent under a plain Control |
| Bodies pass through each other | Mask/layer mismatch (mask must contain the *other's* layer), or empty `CollisionShape2D` | Audit with *Visible Collision Shapes*; name layers; assign shapes |
| `is_on_floor()` always false | Motion mode is FLOATING, or moving via `position` instead of `move_and_slide()`, or wrong `up_direction` | Use GROUNDED mode and `move_and_slide()`; check `up_direction` |
| Volume slider "does nothing" near the top | Linear 0..1 assigned directly to `volume_db` | Convert with `linear_to_db()` |
| `Cyclic reference` between two scripts | Mutual `preload`/`class_name` type dependencies | Break one side: `load()` instead of `preload`, signals instead of direct types, or extract a shared base |
| `res://...: No such file or directory` at runtime | Typo'd path, file moved outside the editor, or export missed a string-loaded resource | Move files inside the editor; `Ctrl+Shift+F` for old paths; add non-scene-referenced files to export filters |
| Works in editor, breaks when exported | Writing to `res://`, debug-only code carrying logic, path case mismatch | Write to `user://`; keep `assert` side-effect-free; test exports early |
| FPS fine, but periodic hitches | Per-frame allocations triggering cleanup, synchronous `load()` of big assets | Profiler → sort by self-time; hoist allocations; `load_threaded_request` |
| Editor behaves strangely (stale completions, ghost files) | Corrupted `.godot/` cache | Close editor, delete `.godot/`, reopen (safe: it is a cache) |
| Every instance changed when one was edited | Shared Resource (StyleBox, material, custom resource) mutated at runtime | `duplicate()` before mutating, *Make Unique* in the Inspector, or `resource_local_to_scene` |
| Tween error: "started with no Tweeners" | Created a tween but conditions skipped all `tween_*` calls | Guard the `create_tween()` itself, not just the steps |

---

## Exercises

Complete these in a fresh project pinned to Godot 4.5 with typed-GDScript warnings raised to errors (Project Settings → Debug → GDScript). Each lab lists concrete acceptance criteria — treat them as a definition of done.

### Lab 1 — Typed GDScript kata
Build a `PlaylistQueue` class (`class_name`, extends `RefCounted`) managing an `Array[StringName]` of track ids: `enqueue`, `dequeue`, `shuffle_remaining`, `peek`, plus a `changed` signal.
**Acceptance criteria:** every declaration typed (zero warnings); a `match`-based `describe_state() -> String` with at least one array pattern and one `when` guard; a test script exercising all paths via `assert`; no `print` calls.

### Lab 2 — Signal wiring three ways
One scene: a `Character` (child) that emits `arrived(position: Vector2)`, a `HUD` (sibling) showing the last arrival, and a parent wiring them. Implement the link three times: (a) parent-wired direct connection, (b) editor-made connection, (c) global `SignalBus`.
**Acceptance criteria:** character script contains no reference to HUD or parent in all three variants; variant (c) disconnects in `_exit_tree()` and survives the HUD being freed and re-instanced at runtime without errors; a written comment (5-10 lines) stating which variant you would keep and why.

### Lab 3 — Autoload init-order forensics
Create autoloads `CatalogService` (loads a JSON catalog in `_ready`) and `AudioBootstrap` (reads the catalog in `_ready`). Order them wrongly on purpose; observe and document the failure; fix the order; then make `AudioBootstrap` robust even under wrong order using a `catalog_ready` signal + `await`.
**Acceptance criteria:** a `NOTES.md` (in the project, not this repo) with the exact error text from the wrong order; final version runs correctly in *both* orders; `AudioBootstrap` contains exactly one `await`.

### Lab 4 — Custom Resource catalog
Define `DecorationData` (`extends Resource`): id, display name, price, icon `Texture2D`, `@export_enum` placement. Author 6+ `.tres` rows; write a loader returning `Array[DecorationData]`; render a `GridContainer` shop of code-built cards.
**Acceptance criteria:** editing a `.tres` price changes the UI with no code edits; loader skips non-`DecorationData` files with a `push_warning`; one card's icon is deliberately shared between two rows to demonstrate resource sharing, documented in a comment.

### Lab 5 — Input layers done right
A clickable field of sprites under a UI panel with buttons. Clicking a button must never affect the field; clicking the field moves a marker; `Esc` toggles the panel; a rebind screen captures a new key for `toggle_panel` at runtime.
**Acceptance criteria:** field input lives in `_unhandled_input` only; the "Clicked Control" debugger tool screenshot (or note) proves the panel consumes its clicks; rebinding persists across restarts via `ConfigFile`.

### Lab 6 — Tween discipline gauntlet
A card that scales up on hover, down on exit, flips (scale.x to 0, swap texture, back to 1) on click — all interruptible mid-animation without visual glitches, spam-clicking included.
**Acceptance criteria:** exactly one stored `Tween` per animated concern with the track-and-kill idiom; no property ends in a corrupted state after 20 rapid hover/click cycles; flip sequencing uses `chain()`/`tween_callback`, not timers.

### Lab 7 — Two-player crossfade
Implement the dual-`AudioStreamPlayer` crossfade as an autoload with a `Music` bus: `crossfade_to(stream)`, volume slider (linear↔dB correct), mute toggle.
**Acceptance criteria:** interrupting a fade mid-way (spam next-track) never doubles volume or leaks a tween; slider at 50% reads ≈ −6 dB on the bus; `finished` of the outgoing player never fires after a swap (explain why in a comment).

### Lab 8 — Physics mini-room
A top-down `CharacterBody2D` (floating mode) in a `StaticBody2D`-walled room with two `Area2D` zones ("desk", "rug") announcing enter/exit via named collision layers.
**Acceptance criteria:** layers named in Project Settings; character collides with walls but zones do not block movement; zone handlers mutate the tree only via deferred calls; *Visible Collision Shapes* screenshot/note confirming shapes.

### Lab 9 — Profile a deliberately bad scene
Spawn 1,000 moving sprites, each allocating a Dictionary and formatting a String in `_process`. Record TIME_FPS, draw calls, and MEMORY_STATIC from `Performance`; then fix (hoist allocations, cache references, batch textures) and measure again.
**Acceptance criteria:** before/after table of the three monitors plus profiler top-3 functions; ≥ 2× frame-time improvement; one custom monitor (`add_custom_monitor`) graphing live sprite count.

### Lab 10 — Drag-and-drop placement
Using the Control drag protocol (`_get_drag_data` / `_can_drop_data` / `_drop_data`): drag item cards from a shop grid into a room area; snap the drop to a 16 px grid with `Vector2.snapped()`; invalid regions (a "wall" strip) must refuse the drop.
**Acceptance criteria:** drag preview follows the cursor at 70% alpha; drops on the wall strip are rejected by `_can_drop_data` (verify the forbidden-cursor feedback); a `decoration_placed(id, pos)` signal fires exactly once per successful drop, with grid-snapped coordinates.

### Stretch A — Desktop companion shell
Borderless, always-on-top, per-pixel transparent window showing one animated character; remembers position across runs; idles ≤ 1% CPU when unfocused (low-processor mode + focus-out FPS cap).
**Acceptance criteria:** Task Manager (or equivalent) reading noted while unfocused; `NOTIFICATION_WM_CLOSE_REQUEST` saves state before quit.

### Stretch B — GDExtension hello world
Build a minimal C++ GDExtension exposing `compute_heavy_thing()`; benchmark against the same algorithm in typed GDScript with `Time.get_ticks_usec()`.
**Acceptance criteria:** both run in the same scene; a table of timings over 5 runs; one paragraph: at what workload size does the extension pay for its complexity?

### Self-assessment

Answer without the docs, then verify against them: (1) Node vs Resource — memory model and identity differences? (2) Server-based architecture in two sentences? (3) When is a signal wrong and a direct call right? (4) What determines autoload init order and why does it matter? (5) Why does gameplay input belong in `_unhandled_input`? (6) What exactly does `move_and_slide()` do with `velocity` and `delta`? (7) Why `linear_to_db` at the slider boundary?

---

## Further reading

**Official documentation** (docs.godotengine.org/en/stable — always match your engine version):

- [GDScript reference](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_basics.html) — the language, feature by feature; re-read after a month of practice.
- [GDScript style guide](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_styleguide.html) — the naming/ordering conventions this module enforces.
- [Static typing in GDScript](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/static_typing.html) — the how and why of the typed style.
- [Godot's design philosophy & Best practices series](https://docs.godotengine.org/en/stable/tutorials/best_practices/index.html) — scene organization, node communication ("call down, signal up" in official form), autoload trade-offs.
- [Engine internals / architecture](https://docs.godotengine.org/en/stable/contributing/development/core_and_modules/godot_internals.html) — the server layer from the source side.
- [Using InputEvent](https://docs.godotengine.org/en/stable/tutorials/inputs/inputevent.html) — the event propagation chain, authoritatively.
- [Tween class reference](https://docs.godotengine.org/en/stable/classes/class_tween.html) — every tweener and modifier, with the sequencing rules.
- [Audio buses](https://docs.godotengine.org/en/stable/tutorials/audio/audio_buses.html) — dB scale, routing, effects.
- [Using CharacterBody2D](https://docs.godotengine.org/en/stable/tutorials/physics/using_character_body_2d.html) — motion modes, `move_and_slide` vs `move_and_collide`.
- [Performance tutorials](https://docs.godotengine.org/en/stable/tutorials/performance/) — general + 2D-specific optimization.
- [Godot 4.5 release notes](https://godotengine.org/releases/4.5/) — what our pinned version added (`@abstract`, variadic functions, accessibility, shader baker).

**Community:**

- [GDQuest — GDScript guidelines](https://gdquest.gitbook.io/gdquests-guidelines/godot-gdscript-guidelines) — the most widely adopted community style, source of several conventions here.
- [KidsCanCode — Godot Recipes](https://kidscancode.org/godot_recipes/4.x/) — task-shaped snippets ("how do I…") for Godot 4.x; excellent for input, movement, and UI patterns.
- [Godot forum](https://forum.godotengine.org/) — searchable Q&A; check answer dates against Godot versions.
- *Godot 4 Game Development Projects* style books — see [00-BIBLIOGRAPHY.md](00-BIBLIOGRAPHY.md) for the vetted list.

**Sibling modules:** [SCENES_AND_NODES.md](SCENES_AND_NODES.md) · [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) · [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) · [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) · [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) · [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md) · [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md) · [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md) · [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md) · [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md)

---

## Glossary

| Term | Definition |
|---|---|
| **Annotation** | `@`-prefixed compiler directive (`@export`, `@onready`, `@tool`, `@abstract`) modifying a declaration. |
| **Autoload** | Script/scene instantiated under `root` before the main scene; global by name; survives scene changes. |
| **Callable** | First-class reference to a method or lambda; the currency of connections, callbacks, and functional APIs. |
| **CanvasItem** | Abstract base of all 2D-drawn nodes; owns `visible`, `modulate`, `z_index`, and the draw API. |
| **CanvasLayer** | Node rendering its subtree in an independent 2D layer, unaffected by the world camera. |
| **Collision layer / mask** | Bit fields on physics objects: layer = what I am; mask = whose layers I detect. |
| **Coroutine** | Function suspended by `await` and resumed when the awaited signal/coroutine completes. |
| **Delta** | Seconds elapsed for the current callback: variable in `_process`, fixed in `_physics_process`. |
| **GDScript 2.0** | The Godot 4 language generation: typed, annotation-based, first-class functions and signals. |
| **Group** | String tag on nodes; queried (`get_nodes_in_group`) or broadcast to (`call_group`) via the SceneTree. |
| **MainLoop / SceneTree** | The per-frame driver of the engine; `SceneTree` is the node-tree implementation used by games. |
| **Node** | Building block of scenes: named, tree-positioned, lifecycle callbacks, manually memory-managed. |
| **NodePath** | Path literal (`^"UI/Label"`) locating a node relative to another. |
| **Orphan node** | Node existing outside the tree with no owner freeing it — a leak; audit with `print_orphan_nodes()`. |
| **Owner** | The scene root a node is saved with; must be set when building scenes procedurally for `pack()`. |
| **PackedScene** | Resource holding a serialized node tree; `instantiate()` produces a live copy. |
| **preload / load** | Resource acquisition at parse time (literal path) vs call time (any path); both hit the resource cache. |
| **RefCounted** | Base class with automatic reference-counted lifetime; parent of all Resources. |
| **Resource** | Shareable, serializable data object (`.tres`/`.res`); same path ⇒ same cached instance. |
| **RID** | Opaque handle identifying an object owned by a server (texture, body, canvas item). |
| **Scene-unique name** | `%Name` reference resolving anywhere inside its scene regardless of tree position. |
| **Server** | Low-level engine singleton owning a domain's real state: `RenderingServer`, `PhysicsServer2D`, `AudioServer`, `DisplayServer`. |
| **Signal** | Declared event on an Object; `emit()` synchronously invokes connected Callables in order. |
| **Signal bus** | Autoload containing only signal declarations; global observer board decoupling emitters from listeners. |
| **StringName** | Interned string with O(1) comparison (`&"name"`); used for actions, groups, buses, animations. |
| **Tween** | Transient interpolator created by `create_tween()`; sequences tweeners, auto-starts, self-frees. |
| **Theme / StyleBox** | Centralized UI styling resource / drawable background primitive (`StyleBoxFlat` etc.). |
| **Variant** | The engine's dynamic value container; what untyped GDScript variables hold. |
| **@tool script** | Script executing inside the editor; guard runtime-only logic with `Engine.is_editor_hint()`. |
| **Anchor / offset** | Control positioning: parent-relative fractions (0-1) plus pixel distances from them. |
| **Size flags** | Per-child negotiation rules (`FILL`, `EXPAND`, `SHRINK_*`) inside a Container. |
| **Audio bus** | Mixing channel with volume and effect chain; players route into it, it routes toward Master. |
| **dB (decibel)** | Logarithmic volume unit; 0 dB = digital ceiling, −6 dB ≈ half amplitude, −80 dB ≈ silence. |
| **Draw call / batching** | One GPU submission / the renderer's merging of compatible canvas items into fewer calls. |
| **Physics tick** | One fixed-timestep simulation step (`physics_ticks_per_second`, default 60 Hz). |
| **UID** | Move-proof resource identifier (`uid://…`) stable across renames, unlike `res://` paths. |
| **user:// / res://** | Writable per-user data directory vs read-only (once exported) project resources. |

---

*Study document for the "Godot 4 in Production" course — Module 01. Case study: Relax Room, IFTS Projectwork 2026.*
*Author: Renan Augusto Macena (System Architect & Project Supervisor).*










