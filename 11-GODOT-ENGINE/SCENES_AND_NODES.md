---
course: "Godot 4 in Production"
phase: "1 — Foundations"
module: "02"
title: "Scenes and Nodes — Composition, Lifecycle and Communication"
version: "Godot 4.5 / GDScript 2.0"
level: "Beginner-Intermediate"
prerequisites: [ "GODOT_ENGINE_STUDY.md" ]
objectives:
  - "Explain how the SceneTree drives processing, rendering and input, and navigate its API surface (paused, current_scene, groups, timers)"
  - "Predict the exact callback order of _init, _enter_tree, _ready, _process/_physics_process and _exit_tree across parents and children"
  - "Reference nodes robustly with $, %, get_node_or_null and exported references, and explain why deep NodePaths are fragile"
  - "Instantiate, reparent and free nodes at runtime safely, using call_deferred and queue_free to avoid mid-frame corruption"
  - "Apply the 'call down, signal up' rule, groups and a signal bus to decouple scenes from each other"
  - "Structure a production project with composition-first scenes, one-scene-one-responsibility and clear folder conventions"
  - "Write @tool scripts with configuration warnings that behave correctly both in the editor and at runtime"
tags: [godot, gdscript, scenetree, nodes, lifecycle, packedscene, instancing, signals, groups, composition, canvaslayer, tool-scripts]
---

# Scenes and Nodes — Composition, Lifecycle and Communication — Complete Guide

> **Module 02** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Godot Engine Study — Module 01](GODOT_ENGINE_STUDY.md)
>
> By the end of this module you will be able to:
> 1. Describe the SceneTree as the engine's living object graph and use `get_tree()` for pausing, scene changes, groups and one-shot timers.
> 2. Trace the full node lifecycle — `_init` → `_enter_tree` → `_ready` → `_process`/`_physics_process` → `_exit_tree` — and explain why `_ready` runs children-first while `_enter_tree` runs parent-first.
> 3. Choose the right node-lookup tool for the job (`$`, `%`, `get_node_or_null`, `find_child`, exported references) and refactor fragile `../../` paths out of a codebase.
> 4. Instantiate `PackedScene`s at runtime, manage `owner` for serialization, and add/remove/reparent/free nodes without mid-iteration crashes.
> 5. Wire scenes together with signals, groups, mediators and an autoload signal bus while keeping every scene testable in isolation.
> 6. Detect and eliminate orphan-node leaks with `Node.print_orphan_nodes()` and the debugger monitors.
> 7. Organize a real project — folders, naming, scene boundaries — the way the Relax Room case study does.
>
> **Estimated time:** reading 2-3 hours · labs 4-6 hours · **Level:** Beginner-Intermediate

## Guiding ideas

1. **Everything on screen is a node; every reusable group of nodes is a scene.** Scenes are Godot's unit of composition, testing and reuse.
2. **`_init` → `_enter_tree` → `_ready` is a fixed contract: enter is parent-first, ready is children-first.** Design initialization around that order instead of fighting it.
3. **`queue_free()` defers, `free()` is immediate.** Deferred deletion is the default in production because signals and physics callbacks may still be in flight.
4. **Call down, signal up.** A node may call methods on its children; it must never reach up or sideways with hard-coded paths — it emits signals instead.
5. **Groups find nodes by role, not by reference.** `get_tree().get_nodes_in_group("enemies")` survives refactors that would break every stored path.
6. **Prefer composition (child component nodes) over deep inheritance chains.** Godot's scene system is built for assembling behavior, not for subclass towers.

## Concept map

```
                          ┌────────────────────────────────────┐
                          │            SceneTree               │
                          │  root: Window · paused · groups    │
                          │  change_scene_to_* · create_timer  │
                          └─────────────────┬──────────────────┘
                                            │ drives every frame
              ┌─────────────────────────────┼─────────────────────────────┐
              │                             │                             │
    ┌─────────▼──────────┐       ┌──────────▼─────────┐        ┌──────────▼──────────┐
    │   Node lifecycle    │       │  Identity & lookup │        │   Communication     │
    │ _init → _enter_tree │       │  $Path  %Unique    │        │  call down          │
    │ → _ready → _process │       │  get_node_or_null  │        │  signal up          │
    │ → _exit_tree        │       │  find_child        │        │  groups / bus       │
    │ NOTIFICATION_*      │       │  @export refs      │        │  dependency inject. │
    └─────────┬──────────┘       └──────────┬─────────┘        └──────────┬──────────┘
              │                             │                             │
    ┌─────────▼──────────┐       ┌──────────▼─────────┐        ┌──────────▼──────────┐
    │  ProcessMode /      │       │    PackedScene     │        │  Composition        │
    │  pausing, priority  │       │  instantiate()     │        │  component nodes    │
    │  PAUSABLE / ALWAYS  │       │  owner · inherit.  │        │  vs deep class      │
    │  DISABLED           │       │  editable children │        │  hierarchies        │
    └─────────┬──────────┘       └──────────┬─────────┘        └──────────┬──────────┘
              │                             │                             │
              └─────────────┬───────────────┴──────────────┬──────────────┘
                            │                              │
                  ┌─────────▼──────────┐         ┌─────────▼──────────┐
                  │ Runtime add/remove │         │  2D node families  │
                  │ add_child (defer)  │         │  Node2D transforms │
                  │ queue_free vs free │         │  CanvasLayer / UI  │
                  │ reparent · orphans │         │  physics · camera  │
                  └────────────────────┘         └────────────────────┘
```

## Table of contents

1. [Overview](#overview)
2. [The SceneTree](#the-scenetree)
3. [The get_tree() API surface](#the-get_tree-api-surface)
4. [Node lifecycle in depth](#node-lifecycle-in-depth)
5. [Notifications](#notifications)
6. [Process modes, pausing and priority](#process-modes-pausing-and-priority)
7. [Node identity and lookup](#node-identity-and-lookup)
8. [PackedScene and instancing](#packedscene-and-instancing)
9. [Scene ownership and inheritance](#scene-ownership-and-inheritance)
10. [Creating and removing nodes at runtime](#creating-and-removing-nodes-at-runtime)
11. [Orphan nodes and leak detection](#orphan-nodes-and-leak-detection)
12. [Communication patterns](#communication-patterns)
13. [Groups in production](#groups-in-production)
14. [Composition over inheritance](#composition-over-inheritance)
15. [The 2D node families](#the-2d-node-families)
16. [CanvasLayer and draw order](#canvaslayer-and-draw-order)
17. [Tool scripts and editor integration](#tool-scripts-and-editor-integration)
18. [Scene organization for real projects](#scene-organization-for-real-projects)
19. [Case study: Relax Room scene architecture](#case-study-relax-room-scene-architecture)
20. [Best practices](#best-practices)
21. [Common errors & troubleshooting](#common-errors--troubleshooting)
22. [Exercises](#exercises)
23. [Further reading](#further-reading)
24. [Glossary](#glossary)

---

## Overview

Godot's core design decision — the one that shapes every project you will ever build with it — is that a game is a **tree of nodes**. A node is the smallest unit of behavior: a sprite, a collision shape, a timer, an audio player. A **scene** is a saved subtree of nodes: a character, a piece of furniture, a menu, an entire level. The engine does not distinguish between "levels", "prefabs", "actors" or "widgets" the way other engines do; all of them are just scenes, and scenes nest inside other scenes without limit.

This module is about mastering that model in production terms. It is one thing to drag a `Sprite2D` under a `CharacterBody2D` and press play; it is another to know *exactly* when `_ready` fires relative to a sibling's `_enter_tree`, why calling `add_child()` from a physics callback can corrupt the tree, or how to structure a 40-scene project so that renaming one node does not break twelve scripts. Those are the questions that separate a prototype from a shippable desktop companion like our **Relax Room** case study, and they are the questions this module answers.

Three mental models run through everything that follows:

**The tree is alive.** The SceneTree is not a passive data structure. Every frame it walks the tree to deliver `_process` callbacks, every physics tick it delivers `_physics_process`, and every input event ripples through it in a defined order. Adding a node to the tree is what switches it on; removing it switches it off. A node that exists but is not in the tree (an *orphan*) consumes memory and does nothing — a fact that powers both useful patterns (pre-instantiated pools) and painful bugs (leaks).

**Scenes are contracts.** A well-designed scene works when instantiated *anywhere*: in the main game, in a test scene, in the editor preview. That only holds if the scene never assumes anything about its surroundings — no `get_node("../../Main/HUD")`, no reliance on a specific parent type. The official best-practices docs state it bluntly: *"If at all possible, you should design scenes to have no dependencies."* When a scene must talk to the outside world, it signals upward and lets the owner decide what to do.

**Composition beats inheritance.** Godot lets you extend scripts and inherit scenes, and both have their place. But the idiomatic way to build a complex object is to *compose* it from small nodes and small scenes — a `HitboxComponent` here, a `HealthComponent` there — rather than to grow a `BaseEntity → BaseCharacter → BasePlayer → SwimmingPlayer` tower that collapses the first time a design requirement crosses the hierarchy.

### Translating from other engines

If you arrive from another engine, the scene/node model maps onto familiar concepts with instructive mismatches:

| Concept | Godot | Unity | Unreal |
|---|---|---|---|
| Smallest unit | Node (is *one* capability) | GameObject + Components | Actor + Components |
| Reusable template | Scene (`.tscn`) | Prefab | Blueprint class |
| Nesting templates | Scenes instance scenes, arbitrarily deep | Nested prefabs | Child actor components |
| A "level" | Just another scene | Scene (special) | Level/Map (special) |
| Per-instance tweaks | Editable children overrides | Prefab overrides | Instance property edits |

The mismatch that matters: a Godot node is closer to a Unity *component* than to a GameObject — it does one thing, and you build objects by parenting nodes, not by attaching components to a host. And because levels are not special, every technique in this module (instancing, lifecycle, communication) applies uniformly from the smallest button to the whole game.

### Where this module sits in the course

Module 01 ([GODOT_ENGINE_STUDY.md](GODOT_ENGINE_STUDY.md)) set up the engine, the editor and the GDScript 2.0 basics. This module gives you the structural vocabulary that every later module assumes: [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) hangs visual nodes on the trees you build here; [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) explains how the tree becomes pixels; [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) (Module 13) deepens the autoload/signal-bus patterns introduced in the communication section; and [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) walks the full Relax Room tree that this module's case study previews.

---

## The SceneTree

When your game starts, Godot creates one `SceneTree` object — the main loop of the whole application — and one root `Window`. The root Window is a *viewport*: it owns the rendering surface, receives OS input, and is the ancestor of everything else. Godot then instantiates your project's **main scene** (set in *Project Settings → Application → Run → Main Scene*) and adds it as a child of the root. From that moment on, the picture in memory looks like this:

```
SceneTree  (the MainLoop object — NOT a node)
└── root : Window  (the root viewport)
    ├── AutoloadA          ← autoload singletons come first…
    ├── AutoloadB          ← …in Project Settings order
    └── Main               ← your main scene (SceneTree.current_scene)
        ├── RoomBackground (Sprite2D)
        ├── Room (Node2D)
        │   ├── Decorations (Node2D)
        │   └── Character (CharacterBody2D)
        └── UILayer (CanvasLayer)
            └── HUD (HBoxContainer)
```

Two details in that diagram trip up newcomers constantly. First, **the SceneTree itself is not a node** — it is a `MainLoop` subclass that *contains* the node tree. You cannot `add_child` to it; you add to `get_tree().root` or below. Second, **autoloads are ordinary nodes** parented directly under the root Window, added *before* the main scene. That is why an autoload's `_ready` runs before the main scene's `_ready`, and why autoloads survive scene changes: `change_scene_to_file()` replaces `current_scene`, never the root's other children.

### Fundamental tree rules

The tree obeys a handful of invariants that the rest of this module builds on:

- **Every node has at most one parent.** Attaching a node that already has a parent is an error; you must `remove_child()` first or use `reparent()`.
- **Children inherit their parent's transform.** Move a `Node2D` and every `CanvasItem` descendant moves with it — position, rotation, and scale compose down the branch.
- **Children inherit `modulate`.** Tint or fade a parent `CanvasItem` and the whole branch tints or fades. (Use `self_modulate` to affect only the parent itself.)
- **Freeing a node frees its entire branch.** `queue_free()` on a parent recursively destroys all descendants — the standard way to unload a whole level or popup.
- **Tree order is meaningful.** Siblings are ordered; that order controls 2D draw order (later siblings draw on top), `_process` order, and UI focus traversal. `move_child()` and the editor's drag-and-drop both change it.

### How the tree drives the game

The SceneTree runs the frame loop. Simplified, each rendered frame it: (1) processes OS input and routes `InputEvent`s through the viewport into the node tree; (2) fires the `physics_frame` signal and calls `_physics_process(delta)` on subscribed nodes zero or more times, depending on the fixed timestep (60 Hz by default); (3) fires `process_frame` and calls `_process(delta)` on every node that has processing enabled, in tree order; (4) lets the rendering server draw the updated `CanvasItem`/3D state. Deferred calls (`call_deferred`, `queue_free`) are flushed between these phases — a detail that becomes crucial in [Creating and removing nodes at runtime](#creating-and-removing-nodes-at-runtime).

Because *membership in the tree is what enables all of this*, "is it in the tree?" is the first diagnostic question for a node that seems dead: no `_process` calls, no input, no rendering. `Node.is_inside_tree()` answers it at runtime.

```gdscript
# A minimal probe you can attach to any node while debugging.
extends Node

func _ready() -> void:
	print("in tree: ", is_inside_tree())            # true here by definition
	print("my path: ", get_path())                   # absolute path, e.g. /root/Main/Room
	print("tree node count: ", get_tree().get_node_count())
	print("current frame: ", get_tree().get_frame())
```

> ⚠️ **Pitfall** — Calling `get_tree()` on a node that is *not* in the tree returns `null`. This is the classic crash inside `_init()` (too early — the node has no parent yet) and inside code that runs after `remove_child()` (too late). If a helper may run in both situations, guard with `is_inside_tree()` first.

> ✅ **Best practice** — Treat the root Window as engine territory. Your code should add persistent, scene-independent nodes via autoloads (configured in Project Settings), not by manually parenting things under `get_tree().root` — manual root children are invisible to the scene system, easy to leak, and bypass the pause and scene-change conventions the rest of the team expects. The exceptions (loading screens that must survive a scene swap) belong in a documented autoload anyway — see [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md).

### Tree order, sibling order and why they matter

"Tree order" (also called scene order or top-down order) means: a parent comes before its children, and siblings come in the order shown in the Scene dock. Three systems read that order directly:

| System | Effect of tree order |
|---|---|
| 2D rendering | Later siblings draw **on top** of earlier ones (same `z_index`). Background nodes go first, foreground last. |
| Processing | `_process`/`_physics_process` run in tree order among nodes with equal `process_priority`. |
| UI input | `Control` nodes hit-test in **reverse** draw order — topmost drawn control gets the mouse event first. |

This is why the Relax Room main scene (see the [case study](#case-study-relax-room-scene-architecture)) lists `RoomBackground` first, the `Room` with characters and decorations in the middle, and the `UILayer` last: the Scene dock reads like the painter's algorithm, back to front.

### Inspecting the live tree

The tree you *think* you built and the tree that *exists at runtime* drift apart the moment code creates nodes — which is most of this module. Two habits close the gap.

**The Remote tab.** While the game runs from the editor, the Scene dock gains a **Remote** tab showing the actual live tree: runtime-spawned decorations, autoloads, internal nodes, everything. Select any node to inspect and *edit* its properties live. Every structural bug in this module's troubleshooting table — missing nodes, wrong parents, unexpected duplicates, a branch under the wrong CanvasLayer — is diagnosed here first. Learn the reflex: behavior wrong → Remote tab → does the structure match the plan?

**Printing the tree.** For logs, tests and headless runs, nodes can dump their subtree:

```gdscript
print(get_tree_string_pretty())   # returns the ASCII tree as a String
print_tree_pretty()                # same, printed directly

# Output for the Relax Room main scene (abridged):
# ┖╴Main
#    ┠╴RoomBackground
#    ┠╴Room
#    ┃  ┠╴Decorations
#    ┃  ┃  ┖╴@Sprite2D@42        ← runtime-spawned, auto-generated name
#    ┃  ┖╴Character
#    ┖╴UILayer
#       ┖╴HUD
```

The auto-generated `@Sprite2D@42`-style names instantly reveal which nodes came from code (and whether `force_readable_name` would be worth its cost). A CI smoke test that instantiates a scene and compares `get_tree_string_pretty()` against an expected snapshot is a cheap structural regression net for your most load-bearing scenes.

### Viewports, windows and where input comes from

The root of the tree is not a plain node but a **`Window`**, and `Window` descends from **`Viewport`** — the class that owns a rendering target and an input-routing context. This detail explains several things that otherwise look arbitrary. `get_viewport()` from any node returns the nearest viewport ancestor (usually the root Window); `get_window()` returns the nearest window. Screen-related queries route through them:

```gdscript
var vp_size: Vector2 = get_viewport_rect().size        # the visible area, in canvas units
var mouse: Vector2 = get_viewport().get_mouse_position()
get_viewport().set_input_as_handled()                   # stop further input propagation
```

Input events physically arrive at the OS window, enter the root viewport, and cascade through the tree in a fixed order: `_input` on every node (deepest-last is *not* guaranteed — order is tree order), then `Control` GUI handling, then `_unhandled_input` for whatever the GUI did not consume. The full pipeline belongs to a later module; what matters *here* is that the pipeline is a **tree walk** — a node outside the tree receives no input, and `set_input_as_handled()` is viewport-level, cutting the walk short for everyone after you.

Godot 4 also allows *embedded* sub-windows and additional `SubViewport` nodes — separate render targets living inside the tree. Relax Room's loading screen uses a `SubViewportContainer` + `SubViewport` to render an animated vignette independently of the main canvas. Treat sub-viewports as "a second screen inside a node": their children form a coordinate and input island, which is occasionally exactly what you need (minimaps, character portraits, render-to-texture effects — see [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md)).

### Watching the tree change

Because entering and leaving the tree are *events*, the SceneTree can tell you about every one of them — a superpower for debugging and for infrastructure code:

```gdscript
# debug_spawn_logger.gd — an autoload that logs every node entering the tree
# under a given branch. Invaluable when "something" keeps spawning nodes.
extends Node

var watch_prefix := "/root/Main/Room"

func _ready() -> void:
	get_tree().node_added.connect(_on_node_added)
	get_tree().node_removed.connect(_on_node_removed)

func _on_node_added(node: Node) -> void:
	if str(node.get_path()).begins_with(watch_prefix):
		print("[+] ", node.get_path(), "  (", node.get_class(), ")")

func _on_node_removed(node: Node) -> void:
	# NOTE: during this signal the node is mid-exit; do not reparent or free it here.
	if str(node.get_path()).begins_with(watch_prefix):
		print("[-] ", node.name)
```

Infrastructure uses of the same hooks: an object-count HUD for development builds, automatic registration of any node with a given script into a manager, or asserting in CI that a scene load creates no nodes outside its own branch. Keep production listeners cheap — `node_added` fires for *every* node, including engine-internal ones, and a slow handler taxes every spawn in the game.

---

## The get_tree() API surface

Every node that is inside the tree can call `get_tree()` to reach the `SceneTree` singleton for the running game. It is a small API, but nearly every subsystem of a production game touches it: pausing, scene changes, group broadcasts, ad-hoc timers, quitting. Learn it as a unit.

### Properties you will actually use

| Property | Type | What it does |
|---|---|---|
| `root` | `Window` | The root viewport/window. Ancestor of everything, including autoloads. |
| `current_scene` | `Node` | Root node of the currently loaded main scene. Swapped by `change_scene_to_*`. |
| `paused` | `bool` | Global pause switch. Interacts with each node's `process_mode` (next sections). |
| `auto_accept_quit` | `bool` | If `true` (default), the app closes itself on the OS quit request. Set `false` to intercept quitting (save prompts — essential for a desktop companion). |
| `quit_on_go_back` | `bool` | Android back-navigation equivalent of the above. |
| `debug_collisions_hint` | `bool` | Draw collision shapes while running from the editor. Priceless when a click-through bug hits the Relax Room drop zones. |
| `edited_scene_root` | `Node` | Root of the scene open in the editor — only meaningful in `@tool` scripts. |

### Signals worth memorizing

| Signal | Fires |
|---|---|
| `process_frame` | Just before `_process` runs on any node this frame. `await get_tree().process_frame` = "wait one frame". |
| `physics_frame` | Just before `_physics_process` on any node this tick. |
| `node_added(node)` / `node_removed(node)` | On every tree entry/exit — powerful for debugging and for auto-registering systems. |
| `node_renamed(node)` | When any node's `name` changes. |
| `tree_changed` | On any structural change. Fires a lot; use sparingly. |
| `scene_changed` | After `change_scene_to_*` finishes loading and adding the new scene. |

### Scene changes

```gdscript
# Three ways to swap the current scene, from most to least common in production:

# 1. From a preloaded PackedScene — fastest at the moment of the swap,
#    because the .tscn was parsed at load time.
const MAIN_MENU: PackedScene = preload("res://scenes/menu/main_menu.tscn")
get_tree().change_scene_to_packed(MAIN_MENU)

# 2. From a file path — loads from disk right now (blocking).
get_tree().change_scene_to_file("res://scenes/main.tscn")

# 3. Reload the scene that is already running (retry / restart buttons).
get_tree().reload_current_scene()
```

All three return an `Error` code (`OK` on success — check it for the file-based variant, which can fail with `ERR_CANT_OPEN`). The swap itself is **deferred**: the new scene becomes `current_scene` at the end of the frame, and the previous scene is freed as part of the swap. Two practical consequences:

- Never read `get_tree().current_scene` immediately after calling `change_scene_to_*` and expect the new root — subscribe to `scene_changed` instead.
- Any data that must survive the swap cannot live in the old scene. Put it in an autoload, or pass it through a loading-screen autoload — the pattern Relax Room uses between `main_menu.tscn` and `main.tscn`.

> ⚠️ **Pitfall** — `change_scene_to_*` replaces **only** `current_scene`. Autoloads and any node you manually parented under `root` stay alive. Forgetting this cuts both ways: state you expected to reset persists, and manually-rooted debug nodes silently accumulate across scene changes.

### SceneTree timers

`create_timer()` returns a fire-and-forget `SceneTreeTimer` — no node required, no cleanup required:

```gdscript
# Signature (Godot 4.5):
# create_timer(time_sec: float, process_always := true,
#              process_in_physics := false, ignore_time_scale := false) -> SceneTreeTimer

func flash_error(label: Label) -> void:
	label.visible = true
	await get_tree().create_timer(2.0).timeout   # suspend this function for 2 s
	label.visible = false
```

The flags matter in production. `process_always = true` (default) means the timer **keeps counting while the tree is paused** — right for UI feedback, wrong for gameplay cooldowns (pass `false`). `process_in_physics` aligns expiry with physics ticks; `ignore_time_scale` opts out of `Engine.time_scale` slow-motion effects.

> ⚠️ **Pitfall** — An `await get_tree().create_timer(...)` inside a node's method does **not** die with the node. If the node is freed while the await is pending, the resumed code runs on a freed object and errors. Guard resumption points: `if not is_instance_valid(self): return` is ugly; better, use a child `Timer` node (which dies with its parent) for anything tied to a node's lifetime, and reserve SceneTree timers for global, short-lived waits.

### Group operations from the tree

Groups are covered in depth [later](#groups-in-production); the tree-side API is:

```gdscript
var enemies: Array[Node] = get_tree().get_nodes_in_group("enemies")
var boss: Node = get_tree().get_first_node_in_group("boss")        # null if none
var n: int = get_tree().get_node_count_in_group("enemies")

get_tree().call_group("enemies", "set_alert", true)                # call method on all
get_tree().set_group("enemies", "speed", 0.0)                      # set property on all
get_tree().call_group_flags(SceneTree.GROUP_CALL_DEFERRED, "ui", "refresh")
```

`call_group` runs immediately, in scene order. When the called method might add or remove nodes, use `call_group_flags` with `GROUP_CALL_DEFERRED` so the calls flush at a safe point.

### Quitting properly

```gdscript
# A desktop companion must intercept the window close button to save state.
func _ready() -> void:
	get_tree().auto_accept_quit = false

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		SaveManager.save_all()          # autoload — see DATABASE_AND_PERSISTENCE.md
		get_tree().quit()               # optional exit code: quit(0)
```

`get_tree().quit()` asks the main loop to stop at the end of the current iteration — it is not `exit()`; the frame finishes, `_exit_tree` and `NOTIFICATION_PREDELETE` still run, files still flush. That is exactly what you want.

### Godot 3 → 4 rename map

Tutorials and forum answers written for Godot 3 remain everywhere; when one crosses your path, translate its scene/node API mentally with this table before typing anything:

| Godot 3 | Godot 4 (this course) |
|---|---|
| `instance()` | `instantiate()` |
| `change_scene(path)` / `change_scene_to(packed)` | `change_scene_to_file(path)` / `change_scene_to_packed(packed)` |
| `get_tree().paused` + `pause_mode` | `get_tree().paused` + `process_mode` (`ProcessMode` enum) |
| `connect("sig", self, "_cb")` | `sig.connect(_cb)` — Callable-based |
| `yield(obj, "sig")` | `await obj.sig` |
| `find_node()` | `find_child()` / `find_children()` |
| `Position2D` | `Marker2D` |
| `KinematicBody2D` + `move_and_slide(velocity)` | `CharacterBody2D` + `velocity` property + `move_and_slide()` |
| `onready var` | `@onready var` |
| `tool` (keyword) | `@tool` (annotation) |
| Camera `zoom` 2 = zoomed out | `zoom` 2 = zoomed **in** (inverted) |

A Godot 3 snippet pasted unedited into a 4.5 project fails loudly on most of these — the dangerous ones are the *semantic* flips (zoom, `move_and_slide`) that parse fine and behave wrong.

### A production scene-change flow

Raw `change_scene_to_file()` is fine for prototypes; a shipped game wraps it in a small autoload that owns the *transition* — fade, loading feedback, data hand-off. The wrapper also solves the "who carries the save-slot number into the next scene?" problem: the autoload does, because it survives the swap.

```gdscript
# scene_changer.gd — autoload "SceneChanger". Owns transitions between top scenes.
extends CanvasLayer

signal transition_finished

@onready var _fade: ColorRect = $FadeRect        # full-screen, black, alpha 0
var payload: Dictionary = {}                      # data the next scene may read

func change_to(scene: PackedScene, data: Dictionary = {}) -> void:
	payload = data
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", 1.0, 0.25)     # fade out
	await tween.finished

	get_tree().change_scene_to_packed(scene)               # swap happens end-of-frame
	await get_tree().scene_changed                          # resume once the new root exists

	tween = create_tween()
	tween.tween_property(_fade, "color:a", 0.0, 0.25)     # fade in
	await tween.finished
	transition_finished.emit()
```

```gdscript
# In the NEW scene's _ready — pull the hand-off data:
func _ready() -> void:
	var slot: int = SceneChanger.payload.get("save_slot", 0)
	_load_room_state(slot)
```

Because the autoload is a `CanvasLayer` with a high `layer`, the fade rect covers both the dying and the newborn scene — no one-frame flash of the new scene at full brightness. For heavyweight scenes, swap the blocking load for `ResourceLoader.load_threaded_request()` and poll progress into a loading bar; the flow structure stays identical (performance budgets: [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md)).

> ✅ **Best practice** — Route *every* top-level scene change through one such autoload, even when a particular transition needs no fade. One choke point means one place to attach analytics, save-on-exit hooks, and the "are you sure?" guard for unsaved changes — instead of hunting down a dozen scattered `change_scene_to_file` calls the week before release.

---

## Node lifecycle in depth

Every node moves through the same sequence of callbacks. You have seen the one-line summary in Module 01; here is the full contract, because the *ordering details across parents and children* are where real bugs live.

```
              CONSTRUCTION                TREE ENTRY                    ACTIVE LIFE
┌────────────────────────┐   ┌───────────────────────────────┐   ┌──────────────────────┐
│ _init()                │   │ _enter_tree()   (parent FIRST,│   │ _process(delta)      │
│  · new() / instantiate │──▶│                  then children│──▶│ _physics_process(dt) │
│  · no parent, no tree  │   │ _ready()        (children     │   │ _input / _unhandled  │
│  · get_tree() == null  │   │                  FIRST, then  │   │  (every frame while  │
└────────────────────────┘   │                  parent)      │   │   in the tree)       │
                             └───────────────────────────────┘   └──────────┬───────────┘
                                                                            │
              DESTRUCTION                     TREE EXIT                     │
┌────────────────────────┐   ┌───────────────────────────────┐              │
│ NOTIFICATION_PREDELETE │◀──│ _exit_tree()   (children      │◀─────────────┘
│  · free / queue_free   │   │                 FIRST, then   │   remove_child(), free,
│  · last chance to      │   │                 parent)       │   queue_free, scene change
│    release resources   │   └───────────────────────────────┘
└────────────────────────┘
```

### _init — construction, not initialization of the scene

`_init()` is GDScript's constructor. It runs the instant the object exists — during `Sprite2D.new()`, or for each node while `PackedScene.instantiate()` rebuilds a saved branch. At `_init` time the node has **no parent, no children attached by you, and no tree**: `get_parent()` is `null`, `$Child` fails, `get_tree()` is `null`.

Use `_init` only for pure-object setup: allocating internal data structures, storing constructor arguments (for classes you `new()` yourself), setting defaults that do not touch the tree.

```gdscript
class_name DecorationSlot
extends Node2D

var slot_id: int
var occupied: bool = false

# Custom constructor arguments work only with new(), never with instantiate():
# a PackedScene calls _init() with no arguments, so defaults are mandatory.
func _init(id: int = -1) -> void:
	slot_id = id
```

> ⚠️ **Pitfall** — If a script attached to a `.tscn` scene declares `_init(id: int)` *without* a default value, `instantiate()` crashes: the scene system constructs nodes with zero arguments. Every parameter of `_init` on a scene script must have a default.

### _enter_tree — parent first, top-down

`_enter_tree()` fires the moment the node becomes part of the SceneTree — during `add_child()`, during scene instantiation into the tree, and again on every re-entry. Order is **top-down**: the parent's `_enter_tree` runs, then each child's, recursively. At this point `get_tree()` works and ancestors exist, but *your own children may not have entered yet* — so `$Child` access is still unsafe here for nodes deep in an entering branch.

`_enter_tree` is the right hook for registering with systems that must know about you as early as possible (adding to groups in code, subscribing to a signal bus) and for logic that must re-run on every re-entry (unlike `_ready`, which fires once by default).

```gdscript
func _enter_tree() -> void:
	add_to_group("interactable")        # registered before anyone can query the group

func _exit_tree() -> void:
	pass  # group membership is removed automatically on exit — nothing to do here
```

### _ready — children first, bottom-up

`_ready()` fires when the node **and its entire subtree** have entered the tree: children run `_ready` before their parent. This inversion is deliberate and is the single most important ordering fact in Godot: when a parent's `_ready` executes, every descendant is guaranteed to be in the tree and already initialized. That guarantee is what makes `@onready` references and `$Child` calls safe inside `_ready`.

```gdscript
extends CharacterBody2D

# @onready assignments execute right before _ready(), in declaration order.
@onready var _anim: AnimatedSprite2D = $AnimatedSprite2D
@onready var _shape: CollisionShape2D = $CollisionShape2D

func _ready() -> void:
	_anim.play(&"idle")                       # safe: children readied first
	_shape.disabled = false
```

```gdscript
# WRONG — plain var initializers run at _init time, before the node
# is in the tree; $AnimatedSprite2D resolves against nothing and errors.
var _anim: AnimatedSprite2D = $AnimatedSprite2D   # ERROR at instantiation
```

The mirrored ordering of `_enter_tree` and `_ready` produces the classic interleaving. For this tree —

```
Main
├── Room
│   └── Character
└── UILayer
```

— adding `Main` to the tree prints:

```
Main._enter_tree
Room._enter_tree
Character._enter_tree
UILayer._enter_tree
Character._ready
Room._ready
UILayer._ready
Main._ready
```

Note that `UILayer._enter_tree` runs *before* `Character._ready`: the whole branch enters first, then readiness bubbles up. Siblings ready in tree order (each branch fully readies before the next sibling's `_ready` — but their `_enter_tree` callbacks all precede any `_ready`).

> ⚠️ **Pitfall** — Sibling access in `_ready` is a trap in one specific case: a node's `_ready` **can** safely touch its own descendants, but touching a *sibling's* internals from `_ready` couples the scene to sibling order and to the sibling's private structure. If `HUD._ready` reads `$../Room/Character.position`, reordering the Scene dock or renaming `Character` breaks the game. Let the shared parent wire siblings together instead (see [Communication patterns](#communication-patterns)).

> ✅ **Best practice** — Put *self-configuration* in `_ready` and *world interaction* later. `_ready` should make the scene internally consistent (connect internal signals, cache child references, set initial state). Anything that needs the rest of the game — other scenes, save data, servers — should happen when the owner calls a documented method on you (`setup()`, `activate()`), keeping the scene testable in isolation.

### _ready runs once — request_ready() resets it

By default `_ready` fires only on the **first** tree entry. Remove and re-add a node and only `_enter_tree`/`_exit_tree` repeat. When a node genuinely needs its `_ready` again on re-entry (say, a pooled projectile that re-initializes per spawn), call `request_ready()`:

```gdscript
func despawn_to_pool() -> void:
	get_parent().remove_child(self)   # back to the pool, still allocated
	request_ready()                    # next add_child() will fire _ready again
```

`request_ready()` does not call `_ready` immediately — it only re-arms the flag for the next tree entry, and it applies to the node it is called on (children keep their own flags).

### _process and _physics_process

Both callbacks receive `delta`, the elapsed seconds since the previous call, and both are enabled automatically when the script defines them. The division of labor is strict in a production codebase:

| | `_process(delta)` | `_physics_process(delta)` |
|---|---|---|
| Frequency | Every rendered frame (variable: 30-240+ fps) | Fixed timestep, default 60 Hz (`physics/common/physics_ticks_per_second`) |
| `delta` | Varies frame to frame | Nominally constant (1/60 s) |
| Use for | Animation polish, UI, camera smoothing, non-critical timers | Movement, collisions, anything touching physics state (`move_and_slide`, forces, raycasts) |
| Danger | Frame-rate-dependent logic if you forget `delta` | Doing heavy non-physics work here wastes the physics budget |

```gdscript
extends CharacterBody2D

const SPEED := 220.0

func _physics_process(_delta: float) -> void:
	var dir := Input.get_vector(&"move_left", &"move_right", &"move_up", &"move_down")
	velocity = dir * SPEED
	move_and_slide()                     # physics API → physics callback, always

func _process(delta: float) -> void:
	# cosmetic only: fade a highlight in/out; fine at any frame rate
	modulate.a = move_toward(modulate.a, _target_alpha, delta * 4.0)
```

You can toggle processing per node at runtime with `set_process(false)` / `set_physics_process(false)` — cheaper and more explicit than an `if disabled: return` guard at the top of the callback, and it composes with `ProcessMode` (next section).

### Input callbacks and toggling the machinery

Two more callback families join the active-life phase. `_input(event)` receives every input event routed through the viewport; `_unhandled_input(event)` receives only what the GUI and prior `_input` handlers left unconsumed — which is why gameplay input belongs in `_unhandled_input` (clicking a HUD button should not also click the world). Both exist only while the node is in the tree, like everything else in this section.

Each callback family has an enable switch, set implicitly when the script defines the method and togglable at runtime:

```gdscript
set_process(false)             # stop _process        · is_processing()
set_physics_process(false)     # stop _physics_process · is_physics_processing()
set_process_input(false)       # stop _input           · is_processing_input()
set_process_unhandled_input(false)
```

These switches are the *fine-grained* layer of the processing stack — per-callback, per-node — sitting under the *coarse* layer of `process_mode` (per-branch pause policy, next section). A stunned character keeps processing visuals but drops physics: `set_physics_process(false)`. A cutscene disables player input but leaves movement running: `set_process_unhandled_input(false)`. Using the right layer keeps intent readable; a boolean flag checked at the top of `_physics_process` does the same job while hiding the state from the debugger and from anyone auditing the node.

> ✅ **Best practice** — Toggle switches are also a performance tool: hundreds of decorations that only *react to events* should not define `_process` at all (an empty `_process` still costs a call per frame per node). Define processing callbacks only where per-frame work genuinely exists; event-driven nodes stay silent until a signal wakes them.

### _exit_tree — children first, and it will run again

`_exit_tree()` fires when the node is about to leave the tree — from `remove_child()`, from `free()`/`queue_free()`, and during scene changes. Like `_ready` (and unlike `_enter_tree`), it propagates **bottom-up**: children exit before their parent. It runs on *every* exit, not just the final one, so it must be idempotent and must not assume the node is being destroyed — it may be about to be reparented.

`_exit_tree` is the cleanup hook for anything you registered with the outside world: disconnect from autoload signals, unregister from managers, stop sounds routed through global buses.

```gdscript
# Relax Room production pattern — every script that connects to the SignalBus
# autoload disconnects in _exit_tree, because the bus outlives the scene.
func _exit_tree() -> void:
	if SignalBus.character_changed.is_connected(_on_character_changed):
		SignalBus.character_changed.disconnect(_on_character_changed)
	if SignalBus.decoration_placed.is_connected(_on_decoration_placed):
		SignalBus.decoration_placed.disconnect(_on_decoration_placed)
```

> ⚠️ **Pitfall** — `_exit_tree` does **not** mean "I am being freed". A `reparent()` call triggers exit + enter on the same live node. If your `_exit_tree` destroys state that `_enter_tree` does not rebuild, reparenting corrupts the node. Destruction-only cleanup belongs in `NOTIFICATION_PREDELETE` (next section).

### Lifecycle timeline — one table to memorize

| Callback / event | Direction | Fires when | Tree access | Repeats? |
|---|---|---|---|---|
| `_init()` | per node | `new()` / `instantiate()` | none — no parent, no tree | once |
| `NOTIFICATION_PARENTED` | per node | gains a parent (`add_child`) | parent yes, tree maybe | on every parenting |
| `_enter_tree()` | parent → children | enters the SceneTree | ancestors yes, own children not yet | every entry |
| `@onready` assignments | per node | right before that node's `_ready` | full subtree | first entry (re-armed by `request_ready`) |
| `_ready()` | children → parent | whole subtree entered | full subtree safe | once (re-armed by `request_ready`) |
| `_process` / `_physics_process` | tree order | every frame / physics tick | full | continuous |
| `_exit_tree()` | children → parent | leaves the SceneTree | still valid during the call | every exit |
| `NOTIFICATION_UNPARENTED` | per node | loses its parent | tree already left | on every unparenting |
| `NOTIFICATION_PREDELETE` | per node | about to be freed | do not touch other nodes | once, at destruction |

### A full trace, end to end

Reading about ordering is one thing; seeing a complete trace cements it. Instrument a two-level scene (`Parent` with children `A` and `B`, `A` having child `A1`) with prints in all four callbacks, then run this driver:

```gdscript
func _ready() -> void:
	var parent := PARENT_SCENE.instantiate()   # (1) construction
	print("--- built, not yet added ---")
	add_child(parent)                          # (2) entry cascade
	print("--- added ---")
	remove_child(parent)                       # (3) exit cascade, branch survives
	print("--- removed ---")
	add_child(parent)                          # (4) re-entry: no _ready this time
	print("--- re-added ---")
	parent.queue_free()                        # (5) marked; free happens end-of-frame
	print("--- queued ---")
```

Output (annotated):

```
Parent._init          ← (1) instantiate() constructs top-down…
A._init
A1._init
B._init
--- built, not yet added ---
Parent._enter_tree    ← (2) entry is top-down…
A._enter_tree
A1._enter_tree
B._enter_tree
A1._ready             ← …readiness is bottom-up, branch by branch
A._ready
B._ready
Parent._ready
--- added ---
A1._exit_tree         ← (3) exit is bottom-up (children first, in reverse order)
A._exit_tree
B._exit_tree
Parent._exit_tree
--- removed ---
Parent._enter_tree    ← (4) re-entry repeats _enter_tree…
A._enter_tree
A1._enter_tree
B._enter_tree
--- re-added ---      ← …but NO _ready lines: the once-flag is spent
--- queued ---        ← (5) prints BEFORE the free
A1._exit_tree         ← end-of-frame: exit cascade, then destruction
A._exit_tree
B._exit_tree
Parent._exit_tree
```

Every ordering bug in this module — sibling access in `_ready`, missing re-init after pooling, cleanup running on reparent — is visible somewhere in this trace. Lab 1 has you reproduce it yourself; do it once and the contract sticks.

### Property setters and the lifecycle

GDScript 2.0 property setters (`var hp: int: set(v): …`) interact with the lifecycle in a way that surprises everyone once. When `instantiate()` rebuilds a saved scene, it assigns saved property values **during construction — before `_enter_tree` and `_ready`**. A setter that touches child nodes therefore runs while those nodes are not yet reachable:

```gdscript
@export var title: String = "":
	set(value):
		title = value
		# WRONG unprotected: at instantiation time, %TitleLabel is not available yet.
		if is_inside_tree():
			%TitleLabel.text = value

func _ready() -> void:
	%TitleLabel.text = title          # re-apply once the subtree exists
```

The `is_inside_tree()` guard plus a re-apply in `_ready` is the standard idiom; `@tool` scripts need it doubly, since the editor assigns Inspector edits through the same setters. Alternatively `set_deferred`/`call_deferred` from the setter pushes the visual update past the entry cascade — choose one idiom per project and stick to it.

### Delta discipline

Both process callbacks hand you `delta` so that *rates* stay frame-rate independent. The rules are short but non-negotiable in production code:

```gdscript
position.x += 200 * delta            # ✅ 200 px per SECOND at any fps
position.x += 4                      # ❌ 4 px per FRAME — 2× faster at 120 fps

modulate.a = move_toward(modulate.a, target, 3.0 * delta)   # ✅ linear, framerate-safe

# Exponential smoothing: the naive weight is subtly framerate-dependent…
value = lerpf(value, target, 0.2)                 # ❌ converges faster at high fps
# …the corrected form uses an exponential decay in delta:
value = lerpf(value, target, 1.0 - exp(-8.0 * delta))   # ✅ same feel at any fps
```

In `_physics_process`, `delta` is nominally constant (1/60 s), which tempts people to hard-code it. Resist: the tick rate is a project setting, and `Engine.time_scale` scales delta for slow-motion. Write against `delta` everywhere and both knobs stay free.

### Lifecycle edge cases teams actually hit

**Inherited scripts and `_ready`.** When script `B` extends script `A` and both define `_ready`, only `B._ready` runs — GDScript overrides, it does not stack. Call `super._ready()` explicitly (first line, by convention) or the base class silently loses its initialization. The same applies to `_enter_tree`, `_process`, `_notification` — any inherited virtual. This is the top cause of "the base class worked until I subclassed it".

```gdscript
# panel_base.gd
func _ready() -> void:
	_animate_open()

# settings_panel.gd
extends PanelBase
func _ready() -> void:
	super._ready()            # without this, the open animation vanishes
	_populate_settings()
```

**Adding children inside `_ready`.** Legal and common (all the programmatic UI in this module does it). The child runs its full entry cascade — `_enter_tree` and `_ready` — *synchronously inside* your `add_child` call, because its subtree is complete the moment it enters. Do not confuse this with the deferred-add rule: `_ready` is not a physics callback, so direct `add_child` is fine here.

**Freeing inside `_ready`.** A scene that decides in `_ready` it should not exist (spawn condition failed) should `queue_free()` and return — never `free()` — because the parent's `add_child` is still on the call stack, and ancestors' `_ready` callbacks have not run yet.

**`@onready` and overridden scenes.** In an inherited scene, `@onready var x = $Path` resolves against the *inheritor's* tree — if the inheritor moved or renamed the node, the base script's path breaks. Prefer `%` unique names in scripts meant for inheritable scenes; unique names are re-registered per scene and survive inheritor restructuring.

**Awaiting inside `_ready`.** The moment `_ready` hits an `await`, the engine *does not wait*: the rest of the entry cascade proceeds, the frame renders, and your post-`await` code resumes later. The node is functional but half-initialized in between. If other nodes depend on your readiness, expose an explicit `initialized` signal they can await, and emit it at the true end of setup — do not let them trust "after `_ready`" semantics you already gave away.

---

## Notifications

Underneath the friendly virtual callbacks sits a lower-level mechanism: **notifications**. The engine sends integer notification codes to objects via `Object.notification()`, and each object can react in `_notification(what: int)`. Every lifecycle callback you just learned is sugar over a notification: `_ready` corresponds to `NOTIFICATION_READY`, `_enter_tree` to `NOTIFICATION_ENTER_TREE`, and so on. You will use `_notification` directly for the events that have *no* dedicated virtual method.

```gdscript
func _notification(what: int) -> void:
	match what:
		NOTIFICATION_PREDELETE:
			# The only reliable "destructor". The node is about to be freed;
			# children may already be gone — release non-node resources only.
			_close_log_file()
		NOTIFICATION_WM_CLOSE_REQUEST:
			# User clicked the window's X (with auto_accept_quit = false).
			_save_and_quit()
		NOTIFICATION_APPLICATION_FOCUS_OUT:
			# Desktop companion etiquette: throttle when not focused.
			Engine.max_fps = 10
		NOTIFICATION_APPLICATION_FOCUS_IN:
			Engine.max_fps = 60
```

### The notification catalog that matters in practice

| Constant | When it arrives | Typical production use |
|---|---|---|
| `NOTIFICATION_POSTINITIALIZE` | Object fully constructed (after `_init`) | Rare; low-level instrumentation |
| `NOTIFICATION_PREDELETE` | Immediately before the object is freed | True destructor: close files, free RIDs, flush caches |
| `NOTIFICATION_ENTER_TREE` (10) | = `_enter_tree` | Prefer the virtual method |
| `NOTIFICATION_EXIT_TREE` (11) | = `_exit_tree` | Prefer the virtual method |
| `NOTIFICATION_READY` (13) | = `_ready` | Prefer the virtual method |
| `NOTIFICATION_PAUSED` / `NOTIFICATION_UNPAUSED` (14/15) | This node's effective pause state flips | Pause/resume animations, audio, tweens manually |
| `NOTIFICATION_PHYSICS_PROCESS` (16) / `NOTIFICATION_PROCESS` (17) | Each tick/frame | Prefer the virtual methods |
| `NOTIFICATION_PARENTED` (18) | Node became someone's child (tree or not) | Component nodes discovering their host (see [Composition](#composition-over-inheritance)) |
| `NOTIFICATION_UNPARENTED` (19) | Node removed from its parent | Component teardown |
| `NOTIFICATION_SCENE_INSTANTIATED` (20) | Root of a `PackedScene.instantiate()` finished building | Post-instantiation fix-ups in tool code |
| `NOTIFICATION_CHILD_ORDER_CHANGED` (24) | Children added/removed/reordered | Container-style nodes re-laying-out |
| `NOTIFICATION_TRANSLATION_CHANGED` | Locale changed | Re-translate hand-built UI strings |
| `NOTIFICATION_WM_CLOSE_REQUEST` | OS window close button | Save-on-quit flow |
| `NOTIFICATION_WM_WINDOW_FOCUS_IN` / `_OUT` | This window gained/lost focus | Pause/mute in background |
| `NOTIFICATION_APPLICATION_FOCUS_IN` / `_OUT` | The whole app gained/lost focus | Throttle FPS — see [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) |

Two rules keep `_notification` code sane. First, **prefer the virtual method when one exists** — `_ready` is clearer than `match what: NOTIFICATION_READY`. Second, `_notification` on a script does not swallow the event: the engine's own handlers and the virtual methods still run, so you are *adding* behavior, not replacing it.

> ⚠️ **Pitfall** — Inside `NOTIFICATION_PREDELETE`, the object is half-dismantled. Do not call methods on child nodes (they may already be freed), do not `add_child`, do not touch the tree. Restrict yourself to releasing non-node resources the object owns: file handles, `RID`s created through servers, C-level allocations from extensions.

You can also *send* notifications yourself — `propagate_notification(what)` delivers a code to a node and its whole subtree, and `get_tree().notify_group("minimap", MY_CODE)` broadcasts to a group. Custom codes are a niche but legitimate decoupling tool:

```gdscript
# Custom notification: "the room theme was rebuilt" — pick codes far above
# the engine's reserved values to avoid collisions.
const NOTIFY_THEME_REBUILT := 12_000

# Sender — reaches the whole branch, scripts and built-ins alike:
%Room.propagate_notification(NOTIFY_THEME_REBUILT)

# Any descendant that cares:
func _notification(what: int) -> void:
	if what == NOTIFY_THEME_REBUILT:
		_refresh_palette()
```

Compared with a signal, a propagated notification needs no connections and no group membership — the *hierarchy* is the subscription. Compared with `propagate_call`, receivers opt in silently instead of erroring on a missing method. In practice, signals cover most of the same needs with better type safety (notifications carry no arguments); reach for custom notifications when a branch-wide, argument-free "something changed, re-derive your state" ping is genuinely all you need.

---

## Process modes, pausing and priority

Pausing in Godot is not a boolean freeze of the whole engine — it is a *negotiation* between one global switch (`get_tree().paused`) and a per-node policy (`Node.process_mode`). Understanding the negotiation is mandatory before shipping anything with a pause menu, and doubly so for a desktop companion that throttles itself in the background.

### The ProcessMode enum

| Value | Meaning while `paused == true` | Meaning while `paused == false` |
|---|---|---|
| `PROCESS_MODE_INHERIT` (default) | Do what the parent does | Do what the parent does |
| `PROCESS_MODE_PAUSABLE` | **Stops** | Runs |
| `PROCESS_MODE_WHEN_PAUSED` | Runs | **Stops** |
| `PROCESS_MODE_ALWAYS` | Runs | Runs |
| `PROCESS_MODE_DISABLED` | Stops | Stops |

"Stops" is comprehensive: no `_process`, no `_physics_process`, no `_input`/`_unhandled_input`, no physics integration for that node. Signals still work, `call()` still works — paused nodes are not frozen objects, they just receive no engine callbacks. The root Window's default behaves like PAUSABLE, so with everything on INHERIT, flipping `get_tree().paused = true` stops the whole game — which is exactly why your pause menu must opt out.

```gdscript
# pause_menu.gd — attached to the CanvasLayer holding the pause UI.
extends CanvasLayer

func _ready() -> void:
	# This branch keeps processing while the rest of the game is paused.
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"pause"):
		toggle()
		get_viewport().set_input_as_handled()

func toggle() -> void:
	var pausing := not get_tree().paused
	get_tree().paused = pausing
	visible = pausing
```

Because `INHERIT` resolves *upward through parents*, you set the policy once on a branch root and the whole branch follows. The idiomatic layout is: gameplay under a node left on `INHERIT`/`PAUSABLE`, pause UI under a node set to `ALWAYS`, and cutscene-only machinery on `WHEN_PAUSED` if you implement cutscenes as "paused world + scripted actors".

> ⚠️ **Pitfall** — Timers, tweens and awaited SceneTree timers each have their own pause story. A `Timer` node obeys its `process_mode` like any node. A `Tween` created with `create_tween()` is bound to the creating node and pauses with it (configurable via `Tween.set_pause_mode`). A `SceneTreeTimer` from `create_timer()` ignores pause by default (`process_always = true`) — the #1 cause of "my pause menu works but the boss attack still fired".

> ✅ **Best practice** — Never scatter `process_mode` overrides across dozens of leaf nodes. Decide pause policy at *branch* level (one setting on `World`, one on `PauseLayer`), document it in the scene's script header, and let `INHERIT` do the rest. An audit of who overrides `process_mode` should fit on one line of your project notes.

`PROCESS_MODE_DISABLED` doubles as a cheap "deactivate this branch" switch: a Relax Room panel that is closed can be disabled instead of freed, keeping its state warm while costing zero processing. Pair it with `visible = false` — disabling does not hide.

### Process priority

Within one frame, nodes with equal priority process in tree order. When ordering matters — a camera that must move *after* the player it follows, a manager that must tick *before* its minions — set `process_priority` (and, separately, `process_physics_priority`): **lower values run earlier**.

```gdscript
# camera_rig.gd — guarantee we sample the player's position after it moved.
func _ready() -> void:
	process_priority = 100          # default is 0; higher = later in the frame
```

Priorities beat fragile solutions like reordering the Scene dock (which also changes draw order — a coupling you do not want) or one-frame-delayed followers. Use a small documented scale (-100 managers, 0 gameplay, 100 cameras/UI sync) rather than ad-hoc numbers.

Godot 4 also exposes `process_thread_group` to move a branch's processing onto a worker thread. It is an optimization topic with real constraints (thread-safe API only inside the group) — out of scope here, but know it exists before inventing your own threading for heavy subtree updates.

### Throttling a desktop companion

Relax Room sits in the corner of a work monitor for hours; burning a full frame budget while unfocused would be hostile. The process-mode machinery plus two engine switches implement "polite background mode" in a dozen lines:

```gdscript
# power_manager.gd — autoload. Cuts work when the app loses focus.
extends Node

const FOCUSED_FPS := 60
const BACKGROUND_FPS := 10

@export var heavy_fx_root: NodePath      # branch of particles/animations to suspend

func _notification(what: int) -> void:
	match what:
		NOTIFICATION_APPLICATION_FOCUS_OUT:
			Engine.max_fps = BACKGROUND_FPS
			OS.low_processor_usage_mode = true        # sleep between frames
			_set_fx_enabled(false)
		NOTIFICATION_APPLICATION_FOCUS_IN:
			Engine.max_fps = FOCUSED_FPS
			OS.low_processor_usage_mode = false
			_set_fx_enabled(true)

func _set_fx_enabled(on: bool) -> void:
	var fx := get_node_or_null(heavy_fx_root)
	if fx:
		fx.process_mode = Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED
```

Note the division of labor: `Engine.max_fps` and `low_processor_usage_mode` throttle the *whole* loop (the latter is how the editor itself idles), while `PROCESS_MODE_DISABLED` on one branch surgically suspends the expensive subtree without touching the clock or audio. The character keeps its slow idle sway (it lives outside `heavy_fx_root`); the ambient particle systems stop entirely. Full energy-budget treatment: [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md).

---

## Node identity and lookup

A node's identity has three layers: its **name** (unique among siblings, `StringName`), its **path** (the chain of names from some base node), and its **instance** (the object pointer you hold in a variable). Production code is largely about choosing the *least fragile* of these for each situation.

### NodePaths, get_node and $

`get_node(path)` resolves a `NodePath` relative to the node you call it on. The `$` operator is pure syntax sugar for `get_node` with a literal path, resolved at parse time into the same call:

```gdscript
var sprite := get_node("AnimatedSprite2D") as AnimatedSprite2D
var sprite2: AnimatedSprite2D = $AnimatedSprite2D            # identical meaning
var deep: Label = $Panel/MarginContainer/VBox/TitleLabel     # path with slashes
var parent_sibling := get_node("../Sibling")                 # .. climbs to parent
var absolute := get_node("/root/Main/Room")                  # from the tree root
```

Rules of the road:

- Paths are **case-sensitive** and match node *names*, not types or scripts.
- `get_node` on a missing path is a **hard error** (and returns `null` after printing it); when absence is a legitimate state, use `get_node_or_null(path)` and branch on the result.
- `$` with names containing spaces or special characters needs quotes: `$"My Node"`.
- `NodePath` is a distinct type; you can store and export it: `@export var target_path: NodePath`, then `get_node(target_path)`.

### Why deep paths are fragile — and the fixes

Every `../` and every extra slash in a path is a structural assumption. `get_node("../../Main/UILayer/HUD/HealthBar")` encodes: my parent's parent is named Main, it has a UILayer, which has an HUD, which has a HealthBar. Rename one node, insert one wrapper, drag one branch, and the game breaks *at runtime*, often only on the code path that touches the node. The KidsCanCode recipe calls these paths out for three failure modes: the scene cannot be tested alone, tree reorganization breaks it, and `_ready`-order hazards appear when reaching upward before ancestors are ready.

The fixes, in order of preference:

1. **Own children: `$` is fine.** Reaching *down into your own scene* is safe — you control that structure, and renames show up immediately in the editor.
2. **Scene-internal but deep: `%` unique names** (next subsection) — immune to restructuring within the scene.
3. **Cross-scene: exported references.** `@export var health_bar: ProgressBar` lets the *assembling* scene wire the dependency in the Inspector; the script holds no path at all.
4. **Role-based: groups.** "Whoever the boss currently is" is a group query, not a path.
5. **Decoupled events: signals** — the subject of [Communication patterns](#communication-patterns).

```gdscript
# BEFORE — fragile: encodes four structural assumptions.
@onready var health_bar := get_node("../../UILayer/HUD/HealthBar") as ProgressBar

# AFTER — robust: the scene that composes player + HUD assigns this in the Inspector.
@export var health_bar: ProgressBar
```

### Unique names: %NodeName

Scene-unique names solve "deep inside my own scene" lookups. In the Scene dock, right-click a node and choose **Access as Unique Name** (this sets `unique_name_in_owner = true`; the node shows a `%` badge). From any script *inside the same scene*, reference it as `%Name`, regardless of depth:

```gdscript
# title_screen.gd — the label sits 5 containers deep; nobody cares.
@onready var title: Label = %TitleLabel
@onready var start_button: Button = %StartButton

func _ready() -> void:
	start_button.pressed.connect(_on_start_pressed)
```

The scope is the **owner**: `%` resolves against the scene the node was saved in. That gives you refactor freedom (move the node anywhere in the scene) with zero global namespace pollution — two different scenes can each have their own `%TitleLabel`. The limits follow from the scope: `%` cannot see into *another* scene's uniques, and it works only for nodes that belong to a saved scene (runtime-created nodes have no owner unless you set one).

> ✅ **Best practice** — Adopt a house rule: `$` only for direct children, `%` for anything deeper inside the same scene, exported references across scenes. The rule is mechanical enough to enforce in code review and eliminates the entire "path broke after refactor" bug class.

### Names and renaming at runtime

`name` is a writable `StringName`, and the engine enforces sibling uniqueness *for you*: assign a name that collides with a sibling and Godot silently appends a suffix (`Decoration` → `Decoration2`, or an `@`-mangled form for non-readable adds). That auto-rename is the quiet killer of name-based lookups — code that spawns two "Decoration" nodes and later calls `get_node("Decoration")` finds only the first, with no error pointing at the second's real name.

```gdscript
var deco := DECORATION_SCENE.instantiate()
deco.name = "Decoration_%s" % item_id      # make uniqueness explicit and meaningful
%Decorations.add_child(deco)
# get_node("Decoration_bed_black_1") is now stable and debuggable.
```

Renaming a node in the tree also fires `get_tree().node_renamed` and invalidates every stored `NodePath` that pointed through the old name — one more argument for references-over-paths in anything long-lived. Practical rules: give runtime-spawned nodes deterministic names when anything (paths, saves, logs) will refer to them; otherwise let the engine mangle freely and hold *references*. And never encode data in names that belongs in properties — `name = "Bed_x4_y7"` is a `cell: Vector2i` export wearing a disguise, unreadable to the type system and fragile to every renaming rule above.

### find_child and find_children — flexible, and slow

```gdscript
# find_child(pattern: String, recursive := true, owned := true) -> Node
# find_children(pattern: String, type := "", recursive := true, owned := true) -> Array[Node]
var any_shape := find_child("CollisionShape*")               # wildcard on names
var all_areas := find_children("*", "Area2D")                # filter by class
```

These walk the subtree comparing names (`String.match` wildcards) and optionally types. They are *discovery* tools — great in `@tool` scripts, editor utilities and one-off setup, wrong in per-frame code. Note the `owned` default: `true` means only nodes with an owner (i.e., saved in a scene) are considered — set it to `false` to also find nodes you created at runtime.

### Instance references, validity and null-safety

The strongest identity is the object reference itself — no name resolution, no path. The price: nodes are *not* reference-counted. When a node is freed, every variable still pointing at it becomes a dangling reference, and touching it raises "previously freed instance" errors. Three tools manage that risk:

```gdscript
if is_instance_valid(character):        # false after free/queue_free completion
	character.position = spawn_point

if character.is_queued_for_deletion():  # true between queue_free() and actual free
	return

var weak := weakref(character)          # WeakRef — get_ref() returns null once freed
```

`is_instance_valid` is a *check*, not a cure: code littered with validity checks usually signals an ownership problem — some other system should have told you (via signal) that the node died. Connect to `tree_exiting` on nodes you cache long-term, and clear the cache there.

### Lookup decision table

| Situation | Use | Why |
|---|---|---|
| Direct child of this node | `$Child` + `@onready` | Fast, visible in editor, breaks loudly on rename |
| Deep node in the same scene | `%UniqueName` | Immune to internal restructuring |
| Node in another scene you compose | `@export var x: Type` | Wiring lives in the Inspector, not the code |
| Node that may legitimately be absent | `get_node_or_null()` | Absence is data, not an error |
| "All nodes playing role R" | groups | Role-based, survives any refactor |
| Editor tooling / one-off discovery | `find_child` / `find_children` | Flexibility over speed |
| Long-lived cached reference | instance + `tree_exiting` hook | Explicit ownership of the invalidation |

### NodePath under the hood

`NodePath` is a real type with structure worth knowing, because animation tracks, tweens and exported paths all speak it:

```gdscript
var p := NodePath("Room/Character")        # relative: resolved from the calling node
var a := NodePath("/root/Main/Room")       # absolute: resolved from the tree root
var prop := NodePath("Sprite2D:modulate:a") # node path + PROPERTY subpath

print(p.get_name_count())                  # 2 → "Room", "Character"
print(prop.get_subname_count())            # 2 → "modulate", "a"
print(a.is_absolute())                     # true
```

The colon-suffixed **property subpath** is how `Tween.tween_property`, `AnimationPlayer` tracks and `Node.get_indexed()` address *properties of properties* — `"position:x"`, `"modulate:a"`. When you tween `"color:a"` on a fade rect (as the SceneChanger earlier does), you are using a NodePath with an empty node part.

Two navigation helpers complete the picture. `get_path()` returns a node's absolute path — great for logging, never for storage (paths go stale). `get_path_to(other)` returns the *relative* path from `self` to another node — the right thing to store in a saved scene or a save file, because it survives moving the common ancestor:

```gdscript
# Persist a reference to a sibling for save/load — relative, not absolute:
data["camera_target"] = str(get_path_to(current_target))
# …later:
current_target = get_node_or_null(NodePath(data["camera_target"]))
```

### Lookup cost, and caching without dogma

All lookup mechanisms are "fast enough" at event frequency; per-frame code is where the differences show. Rough production ranking, cheapest first:

| Mechanism | Relative cost | Notes |
|---|---|---|
| Cached reference in a variable | ~free | The `@onready` pattern — resolve once, use forever |
| `$Child` / `get_node("Child")` | cheap | One hash lookup per path segment, every call |
| `%Unique` | cheap | Owner-scoped map lookup; comparable to `$` |
| `get_node("A/B/C/D")` | scales with depth | Four segment lookups per call |
| `find_child("*pattern*")` | O(subtree) | Full walk with string matching — never per frame |
| `get_nodes_in_group(...)` | O(group size) + array alloc | Fine per event; cache for per-frame iteration |

The rule that falls out: **resolve in `_ready`, use the reference in `_process`.** Re-resolving `$AnimatedSprite2D` sixty times a second is wasted work and — worse — hides the moment a rename breaks the path deep in gameplay instead of at scene load.

```gdscript
# Anti-pattern: path resolution in the hot loop.
func _process(_delta: float) -> void:
	$Sprite2D.rotation += 0.01                 # lookup every frame

# Pattern: resolve once.
@onready var _sprite: Sprite2D = $Sprite2D
func _process(_delta: float) -> void:
	_sprite.rotation += 0.01
```

---

## PackedScene and instancing

A `.tscn` (text) or `.scn` (binary) file on disk is a serialized node branch. Loaded into memory it becomes a **`PackedScene`** — a `Resource` holding an optimized description of nodes, properties, signal connections and sub-instances. `PackedScene` is *not* nodes: it is a factory. Calling `instantiate()` manufactures a fresh, fully-built branch every time.

```gdscript
# Loading: preload() parses at script-load time and caches the resource;
# load() reads from disk when the line executes.
const CHARACTER_SCENE: PackedScene = preload("res://scenes/characters/male_old_character.tscn")
var late_scene := load("res://scenes/room/bed_black_1.tscn") as PackedScene

# Manufacturing an instance:
var character := CHARACTER_SCENE.instantiate() as CharacterBody2D
character.position = Vector2(640, 480)      # configure BEFORE adding — no callbacks yet
add_child(character)                        # _enter_tree/_ready fire here
```

Key facts about `instantiate()`:

- Signature: `instantiate(edit_state: GenEditState = GEN_EDIT_STATE_DISABLED) -> Node`. The `edit_state` parameter is editor machinery — game code always uses the default.
- It rebuilds the **entire saved branch**: nodes, property values, internal signal connections, nested scene instances. Contrast with `Sprite2D.new()`, which yields one bare node with default properties.
- Every call returns an **independent copy**. Instances share `Resource`s by default (textures, SpriteFrames — see [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) on `resource_local_to_scene`), but node state is per-instance.
- The instantiated root receives `NOTIFICATION_SCENE_INSTANTIATED`, and its `scene_file_path` property records where it came from — useful for save systems that must respawn "whatever this was" later.
- `can_instantiate()` reports whether the resource actually contains nodes — a cheap guard when scene paths come from data files, as Relax Room's decoration catalog does.

### preload vs load vs ResourceLoader

| | `preload("res://…")` | `load("res://…")` | `ResourceLoader.load_threaded_request` |
|---|---|---|---|
| When it loads | At script parse/load time | When the line runs (blocking) | In the background |
| Path | Must be a constant string | Any expression | Any expression |
| Best for | Scenes you will definitely need (bullets, UI panels) | Rarely-used or data-driven paths | Big scenes behind loading screens |
| Failure mode | Broken path = script fails to load | Returns `null` at runtime — check it | Poll `load_threaded_get_status` |

> ⚠️ **Pitfall** — Circular `preload`s deadlock script loading: `a.gd` preloading `b.tscn` whose script preloads `a.gd` fails with cryptic "cyclic dependency" errors. Break the cycle by switching one side to `load()` at call time, or restructure so shared code lives in a third script both sides preload.

> ✅ **Best practice** — Configure instances **before** `add_child()`. Between `instantiate()` and `add_child()` the branch exists but receives no callbacks — the perfect window to set positions, inject dependencies and connect signals, so that by the time `_ready` runs the instance is fully equipped. Setting properties *after* adding risks a visible one-frame flicker of default state and forces awkward "late init" code paths.

### Data-driven spawning — the decorations pipeline

Production games rarely hard-code "which scene to spawn"; a catalog decides. Relax Room's decoration system is the house example: `decorations.json` maps item ids to textures, prices and footprints, and the spawn path validates before instantiating anything:

```gdscript
# decoration_catalog.gd — loads once, validates early, fails loudly in dev builds.
class_name DecorationCatalog
extends RefCounted

var _entries: Dictionary = {}     # id -> { texture_path, scene_path?, size, … }

func load_catalog(path: String = "res://data/decorations.json") -> Error:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return FileAccess.get_open_error()
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed == null or not parsed is Dictionary:
		return ERR_PARSE_ERROR
	_entries = parsed
	return OK

func spawn(id: String) -> Node2D:
	var entry: Dictionary = _entries.get(id, {})
	assert(not entry.is_empty(), "Unknown decoration id: " + id)

	# Two spawn paths: full scene when one exists, bare sprite otherwise.
	if entry.has("scene_path"):
		var scene := load(entry["scene_path"]) as PackedScene
		if scene == null or not scene.can_instantiate():
			push_error("Broken decoration scene: " + str(entry.get("scene_path")))
			return null
		return scene.instantiate() as Node2D

	var sprite := Sprite2D.new()
	sprite.texture = load(entry["texture_path"]) as Texture2D
	return sprite
```

The structural lesson generalizes past decorations: **keep the catalog dumb (data) and the spawner strict (validation)**. `can_instantiate()` and null-checked `load()` turn a typo in the JSON into one readable error at spawn time instead of a null-instance crash three frames later, and the dual path (scene vs bare sprite) shows why furniture `.tscn` files can stay reference-only while the runtime goes data-driven — the [case study](#case-study-relax-room-scene-architecture) picks this thread back up. Persistence of *placed* decorations belongs to [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md).

### When to break a branch into its own scene

Everything could technically live in one giant `.tscn`. Production teams split aggressively, on these signals:

1. **Reuse** — the branch appears (or will appear) in more than one place: characters, furniture, projectiles, list rows. This is the obvious one.
2. **Independent testing** — you want to press F6 (Run Current Scene) on the branch alone. A character scene you can run standalone, with a test floor, debugs ten times faster than one buried in `main.tscn`.
3. **Team parallelism** — `.tscn` files are text but merge terribly. Two people editing one scene file is a conflict factory; two people editing two scenes is not. Scene boundaries are ownership boundaries.
4. **Conceptual unit** — the branch answers to a single name in design conversations ("the drop zone", "the settings panel"). If you can name it, you can save it.
5. **Runtime lifecycle** — the branch is spawned/despawned as a unit at runtime. Runtime instancing *requires* a `PackedScene` anyway.

The inverse signals matter too: a `CollisionShape2D` alone is not a scene; a `Label` + `Icon` pair used once is not a scene. Over-splitting produces a project where understanding one screen means opening nine files. The Relax Room rule of thumb: **a scene is something you could describe to a teammate without mentioning its parent.**

### Instantiating at runtime, safely

The two-line version (`instantiate()` + `add_child()`) works — until you call it from the wrong place. During physics callbacks, signal handlers fired by physics (`body_entered`!), and tree iteration, the engine is mid-walk through structures your `add_child` would mutate. Godot detects most of these cases and errors ("Parent node is busy setting up children"); the fix is to defer the mutation to the end-of-frame flush:

```gdscript
func _on_spawn_area_body_entered(_body: Node2D) -> void:
	var pickup := PICKUP_SCENE.instantiate()
	pickup.position = _next_spawn_point()
	# Signal handler fired from physics → defer the tree mutation.
	add_child.call_deferred(pickup)          # GDScript 2.0 Callable syntax
	# Legacy equivalent: call_deferred("add_child", pickup)
```

`call_deferred` queues the call until the current frame's deferred-flush point. If you need to *continue working with the node after it is inside the tree*, deferring the add is not enough — the very next line still runs before the deferred call executes. Await a frame boundary instead:

```gdscript
func spawn_and_focus(scene: PackedScene) -> void:
	var panel := scene.instantiate()
	add_child.call_deferred(panel)
	await get_tree().process_frame            # resume after deferred calls flushed
	panel.grab_focus_on_first_field()         # now panel._ready has run
```

| | `add_child.call_deferred(n)` | `await get_tree().process_frame` then `add_child(n)` |
|---|---|---|
| Style | Fire-and-forget | Suspends the calling function |
| Use when | You do not need the node ready *now* | Subsequent lines depend on the node being in the tree |
| Caveat | Later lines run *before* the add happens | The awaiting node may be freed before resumption — re-validate |

> ⚠️ **Pitfall** — `node.set_deferred("property", value)` is the property-flavored sibling of `call_deferred` and is required for physics state: flipping `CollisionShape2D.disabled` or moving a `StaticBody2D` during a physics callback must be deferred, or the physics server rightfully complains. File it in the same mental drawer as deferred `add_child`.

### Object pooling with PackedScene

Instantiation is not free: node construction, script attachment and property assignment cost real time, and freeing churns memory. For things spawned in bursts — projectiles, particles-with-logic, floating labels — production games pre-instantiate a **pool** and recycle instances. Pooling is also the flagship use of two APIs from this module: deliberate orphans and `request_ready()`.

```gdscript
# node_pool.gd — a minimal, type-agnostic scene pool.
class_name NodePool
extends Node

@export var scene: PackedScene
@export var prewarm_count: int = 16

var _free_list: Array[Node] = []      # deliberate orphans, owned by this array

func _ready() -> void:
	for i in prewarm_count:
		_free_list.append(scene.instantiate())

func acquire(parent: Node) -> Node:
	var node: Node = _free_list.pop_back() if not _free_list.is_empty() \
			else scene.instantiate()
	node.request_ready()               # re-arm _ready for per-spawn initialization
	parent.add_child(node)
	return node

func release(node: Node) -> void:
	node.get_parent().remove_child(node)   # orphan it — do NOT free
	_free_list.append(node)                # the pool owns it again

func _exit_tree() -> void:
	for node in _free_list:                # pool dies → orphans must die too
		node.free()                        # safe: orphans have no in-flight callbacks
	_free_list.clear()
```

The contract with pooled scenes: their `_ready` must fully (re)initialize state — position, velocity, animation frame, connected one-shot signals — because a recycled instance arrives carrying whatever its last life left behind. That is exactly the discipline `request_ready()` exists to support. Notice also the `_exit_tree` teardown: the free-list *is* the "owner in code" that the orphan-leak rules demand, and it settles its debts when the pool leaves the tree.

> ⚠️ **Pitfall** — Pool the right things. Pooling ten decorations that spawn once per user action is complexity for nothing; pooling matters at *dozens-per-second* spawn rates. Profile first ([DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md)); a desktop companion usually needs exactly one pool (UI feedback effects) or none.

### duplicate() — cloning live branches

`instantiate()` manufactures from a *saved* description; `Node.duplicate(flags)` clones a **live** branch, current property values included:

```gdscript
var copy := decoration.duplicate()           # default flags: signals+groups+scripts+instancing
copy.position += Vector2(64, 0)
%Decorations.add_child(copy)
```

The `flags` bitmask (`DUPLICATE_SIGNALS`, `DUPLICATE_GROUPS`, `DUPLICATE_SCRIPTS`, `DUPLICATE_USE_INSTANTIATION`) controls what carries over; the default includes all four. Caveats that earn `duplicate` its "handle with care" label: values live in *exported/storable properties* — private runtime state in plain variables does not travel; `_init` and the entry callbacks run on the copy as usual, possibly overwriting what you expected to be copied; and with `DUPLICATE_USE_INSTANTIATION`, branches that came from a scene file are re-instantiated from that file rather than deep-copied. For anything but quick "stamp another one of these" cases, prefer `instantiate()` + explicit configuration — it is boring, and boring is reproducible.

---

## Scene ownership and inheritance

### The owner property

Every node has an `owner: Node` — a pointer to the root of the scene it was *saved with*. The scene editor sets it automatically for everything you create in a scene. Ownership answers one question: **"when this branch is packed into a `.tscn`, which nodes get serialized?"** `PackedScene.pack(root)` saves the root plus exactly those descendants whose `owner` chain leads to that root. No owner → not saved.

This is invisible until you build nodes at runtime and want to persist them:

```gdscript
# A level editor feature: user places furniture, we save the room as a scene.
func save_room_as_scene(room_root: Node2D, path: String) -> Error:
	for child in room_root.get_children():
		_own_branch(child, room_root)         # claim ownership recursively
	var packed := PackedScene.new()
	var err := packed.pack(room_root)
	if err != OK:
		return err
	return ResourceSaver.save(packed, path)   # e.g. "user://rooms/my_room.tscn"

func _own_branch(node: Node, new_owner: Node) -> void:
	node.owner = new_owner
	for child in node.get_children():
		_own_branch(child, new_owner)
```

Ownership also gates other machinery you have already met: `%` unique names resolve against the owner, and `find_child(..., owned = true)` filters on it. In `@tool` scripts, nodes you add must receive `owner = get_tree().edited_scene_root` (or `EditorInterface.get_edited_scene_root()`) or they will exist in the editor but vanish from the saved file — the classic "my plugin's nodes disappear on save" bug.

> ⚠️ **Pitfall** — When you `instantiate()` a scene at runtime, the *instance's internals* keep their ownership pointing at the instance's root — they are that scene's business. If you then pack the *containing* scene, the instance is saved as a single "instance of res://…tscn" entry, not as expanded nodes. That is normally what you want; it breaks only when you expected a deep copy independent of the source file.

### Editable children

By default, an instanced scene appears in the parent scene's dock as a single collapsed node — its internals are encapsulated. Right-click the instance → **Editable Children** exposes the internal tree (grayed out) and lets you tweak *this instance's* properties: reposition one decoration's sprite, disable one door's collision. The changes are stored in the parent scene as **overrides** — the child `.tscn` file is untouched, and other instances are unaffected.

Editable children are a scalpel, not a workflow. Each override is invisible coupling: the parent scene now depends on the child's internal node names, and refactoring the child silently orphans the overrides. Use them for one-off placement tweaks; the moment you override the same property on three instances, promote it to an `@export` on the child's script and configure it like an honest API.

### Scene inheritance

*Scene → New Inherited Scene* (or right-clicking a `.tscn` and choosing "New Inherited Scene") creates a scene whose base is another scene. The inherited scene starts as a live view of the base — same nodes, same properties — and records only your *deltas*: added nodes, overridden properties, a different script. Edits to the base propagate to all inheritors that did not override them.

Relax Room's character roster is the canonical use case: a `character_base.tscn` defines the `CharacterBody2D` + `CollisionShape2D` + `AnimatedSprite2D` skeleton and the controller script; each concrete character (`male_old_character.tscn`, …) inherits it and overrides only the `SpriteFrames` resource and scale. Add a new node to the base — say a `ShadowSprite` — and every character gains it on next open.

The trade-offs mirror script inheritance: powerful for *N variants of one thing*, painful when variants start diverging structurally. You cannot delete a base node from an inheritor (only hide/disable it), and deep inheritance chains (base → variant → sub-variant) make it genuinely hard to answer "where does this property value come from?". If you find yourself fighting the base, the composition patterns [below](#composition-over-inheritance) — a plain scene with a `SpriteFrames` export, configured per instance — are usually the better trade.

> ✅ **Best practice** — Keep scene inheritance **one level deep** and reserve it for true "same structure, different assets/parameters" families (characters, furniture variants, themed buttons). Anything more heterogeneous should be composition: shared *components* inside otherwise independent scenes.

### What a .tscn actually stores

Seeing the serialization once demystifies ownership, overrides and merge conflicts simultaneously. A trimmed `main.tscn` excerpt:

```ini
[gd_scene load_steps=4 format=3 uid="uid://c1x2y3z4a5b6c"]

[ext_resource type="Script" path="res://scripts/main.gd" id="1_main"]
[ext_resource type="PackedScene" uid="uid://dq8r7s6t5u4v3"
    path="res://scenes/characters/male_old_character.tscn" id="2_char"]
[ext_resource type="Texture2D" path="res://assets/rooms/room.png" id="3_room"]

[node name="Main" type="Node2D"]
script = ExtResource("1_main")

[node name="RoomBackground" type="Sprite2D" parent="."]
position = Vector2(640, 360)
texture = ExtResource("3_room")

[node name="Character" parent="Room" instance=ExtResource("2_char")]
position = Vector2(640, 480)

[connection signal="pressed" from="UILayer/HUD/DecoButton" to="." method="_on_deco_pressed"]
```

Read the mechanics off the format: each `[node]` line records a name, type (or `instance=` for an instanced scene) and parent path — the *owner* is implicit (everything in this file is owned by `Main`, which is why unowned runtime nodes cannot appear here). The instanced `Character` stores **only overridden properties** (`position`) — everything else lives in the character's own file, which is exactly how editable-children overrides and scene inheritance deltas work. And `[connection]` sections are why editor-made signal connections survive reloads. When a git merge mangles a scene, it is these sections that duplicate or lose their parents — and the editor-reload validation habit catches it.

---

## Creating and removing nodes at runtime

Scenes cover structure you can plan; production games also build structure on the fly — spawned pickups, procedurally assembled UI, pooled projectiles. The API is small but every method has sharp edges worth knowing precisely.

### add_child and its options

```gdscript
# add_child(node: Node, force_readable_name := false, internal := INTERNAL_MODE_DISABLED)
var row := HBoxContainer.new()
list.add_child(row)                       # name auto-assigned: "@HBoxContainer@37"
list.add_child(row2, true)                # force_readable_name → "HBoxContainer2"
```

`add_child` triggers the entry cascade immediately (parenting notification, `_enter_tree`, and `_ready` if this branch's turn has come). `force_readable_name = true` produces human-readable names at a measurable cost (uniqueness checks against siblings) — leave it `false` in hot paths like bullet spawning, use it when node paths must be predictable. The `internal` parameter hides children from `get_children()`-style iteration; it exists so engine features (scrollbars inside containers) can add helper nodes without polluting your logic — you will rarely pass it, but you should know why `get_child_count()` can differ from what the remote tree shows.

Ordering helpers round out the family: `move_child(child, index)` repositions among siblings (index 0 = first = drawn first), `add_sibling(node)` inserts next to `self`, and `get_index()` reports a node's position under its parent.

### remove_child vs queue_free vs free

These three are routinely confused and must not be:

| | `remove_child(node)` | `node.queue_free()` | `node.free()` |
|---|---|---|---|
| Removes from tree | Yes, immediately | Yes (during deletion) | Yes, immediately |
| Destroys the node | **No** — node lives on as an orphan | Yes, **at end of frame** | Yes, **right now** |
| Children | Follow the node out of the tree | Freed recursively | Freed recursively |
| In-flight signals/callbacks | Safe | Safe — that is the point | **Can crash** |
| Typical use | Pooling, reparenting by hand, temporary detach | 99% of destruction | Tooling, teardown code where immediacy is proven safe |

`queue_free()` marks the branch for deletion and lets the engine free it at a safe point after the current frame's callbacks. Between the call and the actual free, the node is still valid — `is_queued_for_deletion()` returns `true`, and well-behaved code checks it before doing further work on the node. `free()` destroys immediately; if a signal emission list, physics callback, or group iteration still references the node, you get "previously freed instance" errors or worse. The original version of this module demonstrated the race on the Relax Room codebase: a `Timer.timeout` handler freeing the node with `free()` while a second connection to the same signal was still pending crashed reliably; `queue_free()` made it boringly safe. Keep `free()` for controlled contexts — editor tools, tests, unloading in a loading screen where you *know* nothing is iterating.

```gdscript
# Idiomatic despawn with a death animation:
func die() -> void:
	set_physics_process(false)                 # stop gameplay immediately
	collision_shape.set_deferred("disabled", true)
	animated_sprite.play(&"death")
	await animated_sprite.animation_finished
	queue_free()                               # actual free happens end-of-frame
```

> ⚠️ **Pitfall** — `queue_free()` does not null your variables. Other scripts holding a reference to the freed node keep a dangling pointer. If anything caches the node across frames, have the cache owner connect to the node's `tree_exiting` signal and clear the entry there — do not sprinkle `is_instance_valid` checks as a substitute for ownership discipline.

### reparent()

Moving a node between parents used to require the remove/add dance; Godot 4 provides the atomic version:

```gdscript
# reparent(new_parent: Node, keep_global_transform := true)
carried_item.reparent(player_hand)             # keeps world position by default
carried_item.reparent(inventory_grid, false)   # adopt the new parent's local space
```

`reparent` fires `_exit_tree` then `_enter_tree` (but **not** `_ready` again — the once-flag is unaffected), preserves the node and its children, and with `keep_global_transform = true` recomputes the local transform so the node does not visibly jump. This is the tool for pick-up/drop mechanics, moving popups between layers, and re-homing a character between rooms.

> ⚠️ **Pitfall** — Because `reparent` triggers `_exit_tree`, any cleanup you wrote there ("disconnect from the bus, unregister from the manager") runs on every reparent. Pair every `_exit_tree` teardown with an `_enter_tree` setup, or gate destruction-only logic behind `is_queued_for_deletion()`.

### Building UI in code — a worked example

Relax Room builds its small panels programmatically (see the [case study](#case-study-relax-room-scene-architecture) for why). The pattern generalizes to any runtime-assembled UI:

```gdscript
func _build_settings_panel() -> PanelContainer:
	var panel := PanelContainer.new()
	panel.name = "SettingsPanel"               # name it — debugging unnamed nodes hurts

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_top", 8)
	panel.add_child(margin)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 8)
	margin.add_child(vbox)

	var title := Label.new()
	title.text = "Settings"
	title.add_theme_font_size_override("font_size", 13)
	vbox.add_child(title)

	var mute := CheckButton.new()
	mute.text = "Mute audio"
	mute.toggled.connect(_on_mute_toggled)     # connect before returning — no tree needed
	vbox.add_child(mute)

	return panel                               # caller decides where it lives
```

Note two disciplines: the builder returns the branch instead of adding it to itself (the caller owns placement — dependency direction stays downward), and signals are connected during construction, which is legal because signal connections never require tree membership.

### Traversing and transforming the tree

Runtime structure work often means *walking* branches you did not build. The traversal toolkit:

```gdscript
# Direct children — typed iteration:
for child in %Decorations.get_children():
	if child is Decoration:
		child.refresh_theme(theme)

# Index access when order matters:
var first := list.get_child(0)
var last := list.get_child(list.get_child_count() - 1)

# Full recursive walk with a Callable — no engine helper needed, write it once:
func walk(node: Node, action: Callable) -> void:
	action.call(node)
	for child in node.get_children():
		walk(child, action)

# usage: count every CanvasItem under the room
var count := 0
walk(%Room, func(n: Node) -> void:
	if n is CanvasItem:
		count += 1)
```

For the common special case "call one method on everyone below me", the engine ships the walk: `propagate_call(method: StringName, args: Array = [], parent_first := false)` invokes the method on the node and all descendants *that have it*, children-first by default. Its notification sibling `propagate_notification(what)` does the same with a notification code:

```gdscript
%Room.propagate_call(&"on_theme_changed", [theme])   # no groups, no signals — pure hierarchy
```

Choose deliberately between the three broadcast mechanisms: `propagate_call` follows **structure** (this branch, whatever is in it), groups follow **role** (these tagged nodes, wherever they are), signals follow **subscription** (whoever asked). Structure-based broadcast is the right tool exactly when the branch *is* the meaning — "everything in this room" — and the wrong one the moment members can live elsewhere.

> ⚠️ **Pitfall** — Mutating while iterating: `for child in get_children(): child.queue_free()` is safe (deletion is deferred), but `for child in get_children(): remove_child(child)` mutates the sibling list mid-loop. `get_children()` returns a *copy* of the list in Godot 4, which saves you from the crash — but relying on that quietly is fragile style. Make the intent explicit: snapshot (`var kids := get_children()`), or iterate backwards by index when removing.

---

## Orphan nodes and leak detection

An **orphan node** is a node that exists in memory but is not inside the SceneTree. Orphans are not automatically bugs — a pooled bullet waiting for reuse is a deliberate orphan, and so is a panel you `remove_child`ed to show later. They become leaks when nothing holds a plan for them: nodes are plain `Object`s, **not reference-counted**, so an orphan nobody frees lives until the process exits.

The three classic leak factories:

```gdscript
# 1. Instantiate-and-forget: an early return skips add_child.
func try_spawn() -> void:
	var fx := FX_SCENE.instantiate()
	if not _can_spawn():
		return                    # LEAK — fx is never added and never freed
	add_child(fx)

# fix: instantiate after the guards, or free in the early-out:
	if not _can_spawn():
		fx.free()                 # safe: orphan, nothing references it
		return

# 2. remove_child without a plan:
get_parent().remove_child(self)   # who frees me now? Nobody → leak

# 3. "Detached" UI kept in a variable that later goes out of scope:
var _popup := PopupPanel.new()    # never added, never freed, variable overwritten later
```

### Detection tooling

- **`Node.print_orphan_nodes()`** — static method; prints every orphan's instance ID, name and script to the output. Call it from a debug hotkey or at scene teardown in development builds. Only works in debug builds.
- **Debugger → Monitors → Object/Node counts** — watch "Orphan Nodes" while playing; a counter that climbs during normal gameplay is a leak in a spawn path.
- **`--verbose` on exit** — the engine reports leaked instances (`ObjectDB instances leaked at exit`) when the process ends with objects alive. CI can grep for it.
- **Remote tab of the Scene dock** — shows the *live* tree while playing; a node you expected to exist that is missing here is either freed or orphaned.

```gdscript
# debug_overlay.gd — development-only leak probe on a hotkey.
func _unhandled_key_input(event: InputEvent) -> void:
	if OS.is_debug_build() and event.is_action_pressed(&"debug_orphans"):
		Node.print_orphan_nodes()
```

> ✅ **Best practice** — Every deliberate orphan needs an *owner in code*: the pool that holds pooled instances, the manager variable that holds the detached panel. Adopt the rule "whoever removes without freeing, stores" — then `print_orphan_nodes()` output should list only nodes you can account for, and anything else is a bug by definition.

> ⚠️ **Pitfall** — `RefCounted` objects (plain resources, custom `RefCounted` classes) free themselves when the last reference drops; nodes never do. Teams migrating from reference-counted mindsets leak nodes precisely because the habit says "dropping the variable is enough". For nodes it never is: `free`, `queue_free`, or keep it parented so a parent's free takes it along.

### Instance IDs and the ObjectDB

Every `Object` — nodes included — is registered in the engine's **ObjectDB** under a unique instance ID for the lifetime of the process run. Two functions expose it, and together they enable a safer flavor of long-lived reference:

```gdscript
var id: int = character.get_instance_id()      # stable for this object's lifetime
# … any amount of time later, possibly after the node died:
var maybe := instance_from_id(id)              # Object or null — NEVER a dangling pointer
if maybe is CharacterBody2D:
	(maybe as CharacterBody2D).position = spawn
```

Unlike a stored object reference, a stored *ID* cannot dangle: `instance_from_id()` simply returns `null` once the object is gone. Save systems, undo stacks and debug consoles use IDs for exactly this reason. The ObjectDB is also what the leak reports speak: the `ObjectDB instances leaked at exit` message on `--verbose` shutdown lists IDs of objects still alive — nodes you orphaned, but also `RefCounted` cycles and resources pinned by static variables. Treat a clean exit log as a shippable-build criterion; it is the cheapest memory audit you will ever run.

---

## Communication patterns

Scenes must talk — the character tells the HUD its mood changed, the drop zone tells the room a decoration landed, the settings panel tells everyone the theme flipped. *How* they talk determines whether the project stays refactorable. This section is the heart of the module.

### The prime rule: call down, signal up

A node may **know about and call** its descendants: they are its implementation. A node must **never** reach up (parent, grandparent) or sideways (siblings) by path: those are its *context*, and context changes. When information must flow upward, the node **emits a signal** and lets whoever composed it decide what happens.

```gdscript
# character_controller.gd — knows NOTHING about HUDs, rooms or panels.
extends CharacterBody2D

signal mood_changed(new_mood: StringName)
signal arrived_at(target: Vector2)

var _mood: StringName = &"calm":
	set(value):
		if value == _mood:
			return
		_mood = value
		mood_changed.emit(value)       # upward: "this happened", no addressee
```

```gdscript
# main.gd — the composing scene wires its children together. It is the ONLY
# script that knows both sides exist.
func _ready() -> void:
	%Character.mood_changed.connect(%HUD.show_mood)
	%Character.arrived_at.connect(_on_character_arrived)
	%HUD.decoration_requested.connect(%Room.begin_placement)   # down via method call
```

Read the wiring script as an *architecture diagram*: every dependency between siblings appears in one place, greppable and reviewable. The children stay ignorant of each other, which is precisely what lets you run `character.tscn` standalone with F6.

### Signals: mechanics worth being precise about

```gdscript
signal decoration_placed(item_id: String, cell: Vector2i)    # typed parameters

# connect / disconnect / query — Godot 4 Callable style:
decoration_placed.connect(_on_placed)
decoration_placed.connect(_on_placed_once, CONNECT_ONE_SHOT) # auto-disconnects after 1 emit
decoration_placed.connect(_on_placed_deferred, CONNECT_DEFERRED) # delivered at frame end
decoration_placed.is_connected(_on_placed)                   # true/false
decoration_placed.disconnect(_on_placed)
decoration_placed.emit("bed_black_1", Vector2i(4, 7))

# Binding extra arguments at connect time:
for button in deco_buttons:
	button.pressed.connect(_on_deco_button.bind(button.item_id))
```

Facts that prevent whole bug categories:

- **Emission is synchronous.** `emit()` calls every connected callable *right now*, in connection order, and returns when all have run. A handler that frees the emitter mid-emission is the `free()` race from earlier — one more reason for `queue_free`.
- **Duplicate connections error.** Connecting the same callable twice prints an error (unless `CONNECT_REFERENCE_COUNTED`). Guard re-connectable paths with `is_connected()`.
- **Connections die with either endpoint** — *if both are freed properly*. Godot auto-disconnects when the target object is freed. The dangerous case is an **autoload emitter + freed listener that was connected with a bound `self`** or a long-lived emitter whose listener forgot cleanup while using lambdas: anonymous lambdas capture `self` weakly enough to leave stale entries. House rule: any connection **to an autoload** is disconnected in `_exit_tree` (the Relax Room pattern shown earlier); parent→child connections inside one scene need no manual cleanup.
- **`CONNECT_DEFERRED`** delivers the callback at the deferred-flush point — the antidote when a handler must mutate the tree in response to a physics signal (`body_entered` → spawn something).
- **Performance is a non-issue at sane scales.** GDQuest measured on the order of two thousand signal emissions per millisecond; do not contort architecture to "save" signal overhead.

> ✅ **Best practice** — Name signals as *past-tense facts* about the emitter (`died`, `mood_changed`, `decoration_placed`), never as imperatives aimed at a listener (`update_hud`, `play_sound`). The emitter reports what happened; deciding what to do about it is the listener's business. The moment a signal name mentions the listener, the decoupling is already lost.

### Siblings via a mediator

When two siblings must coordinate, the shared parent is the mediator — it either connects signal to method directly (as `main.gd` above) or hosts a thin relay method when translation is needed:

```gdscript
# main.gd — mediator translating between two children's vocabularies.
func _on_drop_zone_item_dropped(item_id: String, screen_pos: Vector2) -> void:
	var cell := %Room.screen_to_cell(screen_pos)      # call down: coordinate math
	if %Room.is_cell_free(cell):                      # call down: query
		%Room.place_decoration(item_id, cell)         # call down: command
	else:
		%HUD.flash_invalid_drop()                     # call down: feedback
```

The drop zone knows nothing about rooms or cells; the room knows nothing about input; the HUD knows nothing about either. Ten lines of mediator buy three independently testable scenes.

### The autoload signal bus

Some events are genuinely global: theme changed, save completed, user logged out. Routing those through parent chains would mean every intermediate scene forwarding signals it does not care about — GDQuest's "signal bubbling" anti-pattern. The standard cure is a tiny autoload that only declares signals:

```gdscript
# signal_bus.gd — registered as autoload "SignalBus" in Project Settings.
extends Node

signal character_changed(character_id: String)
signal decoration_placed(item_id: String, cell: Vector2i)
signal theme_changed(theme_name: StringName)
signal save_completed(slot: int)
```

```gdscript
# Anywhere: emit without knowing listeners.
SignalBus.theme_changed.emit(&"forest_night")

# Anywhere: listen without knowing emitters — and clean up, because the bus outlives you.
func _ready() -> void:
	SignalBus.theme_changed.connect(_on_theme_changed)

func _exit_tree() -> void:
	if SignalBus.theme_changed.is_connected(_on_theme_changed):
		SignalBus.theme_changed.disconnect(_on_theme_changed)
```

The bus is powerful and dangerous in equal measure: it makes *any* coupling possible with one line, so undisciplined teams end up with a project where all data flow is invisible global events. Scope rules that keep it healthy — bus signals must be (1) genuinely many-to-many or cross-scene, (2) past-tense facts, (3) documented in the bus file itself. Local parent-child communication **stays local**. The full treatment, including load-order and safety patterns, is Module 13: [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md).

### Dependency injection for nodes

The official best-practices docs list five ways a parent can hand a child what it needs; in practice they collapse into a toolkit you should consciously pick from:

| Technique | Wire-up | Best for |
|---|---|---|
| `@export var target: Node` (typed reference) | Inspector, by the composing scene | Stable cross-scene references (HUD elements, cameras) |
| `@export var target_path: NodePath` | Inspector | When the reference must survive save/load of the scene as data |
| `setup(deps…)` method called before/after `add_child` | Code, at instantiation | Runtime-spawned instances needing data (item ids, configs) |
| `Callable` property | Code | Injecting *behavior* (a scoring rule, a formatter) without subclassing |
| Signals | Editor or code | Reactive, fire-and-forget notifications |

```gdscript
# Runtime injection at spawn time — the spawner provides everything the
# instance needs; the instance never looks upward for it.
func spawn_decoration(item_id: String, cell: Vector2i) -> void:
	var deco := DECORATION_SCENE.instantiate() as Decoration
	deco.setup(item_id, _catalog.texture_for(item_id))   # inject before add
	deco.position = _cell_to_position(cell)
	%Decorations.add_child(deco)
```

> ⚠️ **Pitfall** — Injection via `_ready` racing: if a child's `_ready` *consumes* injected data, the parent must inject **before** `add_child` (children ready before the parent's `_ready` finishes composing them — you cannot inject from the parent's `_ready` "in time" for children instantiated in the editor). For editor-placed children, have `_ready` tolerate missing data and provide an explicit `setup()` that (re)initializes.

### Anti-patterns gallery

Four communication smells appear in nearly every codebase review; learn to name them.

**The upward grab.** A child reaches into its context by path:

```gdscript
# character_controller.gd — WRONG: the character now requires this exact tree.
func _on_mood_changed() -> void:
	get_node("../../UILayer/HUD/MoodIcon").texture = _mood_texture()
```

*Fix:* emit `mood_changed`; let `main.gd` connect it to the HUD. The character works in any tree again.

**Signal bubbling.** Every intermediate scene forwards a child's signal upward:

```gdscript
# room_base.gd — WRONG: the room re-emits a signal it does not care about.
signal decoration_clicked(item_id: String)
func _ready() -> void:
	for deco in %Decorations.get_children():
		deco.clicked.connect(func(id: String) -> void: decoration_clicked.emit(id))
```

One hop is legitimate mediation; three hops of pure forwarding is plumbing that breaks on every refactor. *Fix:* if the real listener is far away and the event is a global fact, put it on the SignalBus; if it is not a global fact, ask why a distant node cares at all.

**The chatty signal.** A signal carrying live mutable state every frame (`position_changed(pos)` emitted from `_process`) is a method call wearing a costume — subscribers are effectively polling. *Fix:* let interested nodes read the property when *they* need it (call down), or emit only on meaningful transitions (`entered_zone`, `stopped_moving`).

**The omniscient bus.** Every interaction in the project routed through autoload signals — even parent-child wiring inside one scene:

```gdscript
# drop_zone.gd — WRONG: a scene-internal fact broadcast to the entire game.
SignalBus.drop_zone_hovered.emit(self, item_id)
```

The bus hides *who talks to whom*: with twenty bus signals, the architecture is invisible and every emission is a potential action-at-a-distance bug. *Fix:* the bus carries only cross-scene, many-to-many facts (the scope rules above); everything else uses local signals whose connections are greppable in the composing scene.

### Awaiting signals

GDScript 2.0's `await` turns any signal into a suspension point, which converts callback spaghetti into readable sequences. You have seen it with timers; it generalizes to every signal, including your own:

```gdscript
# Sequential choreography without a state machine:
func play_intro() -> void:
	%MenuCharacter.walk_in()
	await %MenuCharacter.arrived            # custom signal on the character
	%TitleLabel.visible = true
	await get_tree().create_timer(0.3).timeout
	%ButtonContainer.fade_in()
	await %ButtonContainer.faded_in
	_intro_done = true

# Awaiting a one-argument signal yields the argument:
var chosen_id: String = await %CharacterPicker.character_chosen
```

Rules for production use: an awaited function returns a coroutine — callers that care about completion must `await` it in turn (or fire-and-forget deliberately); the suspended function resumes *only if* the awaited object still exists, so a freed emitter silently strands the coroutine — keep awaited choreography inside one scene where lifetimes are shared; and never `await` inside `_process` (you would stack a new coroutine every frame). For cross-scene sequencing, prefer explicit signal connections over long-distance awaits — the wiring stays visible.

### Choosing a channel — the decision table

Every communication mechanism in this module, one table. "Coupling" reads as *what the sender must know*.

| Channel | Direction | Coupling | Cardinality | Use when |
|---|---|---|---|---|
| Direct method call | Parent → child | Child's API | 1 → 1 | Owner commanding its own composition — the default "down" |
| `@export` reference call | Anywhere → anywhere | The wired node's API | 1 → 1 | Cross-scene calls wired by the composing scene |
| Signal (local) | Child → parent/wiring | Nothing about listeners | 1 → N | Reporting facts upward — the default "up" |
| Signal bus (autoload) | Anywhere → anywhere | The bus schema | N → N | Genuinely global facts; document and disconnect |
| Group broadcast | Anywhere → role | Group name + member API | 1 → group | Role-based commands to scattered nodes |
| `propagate_call` | Ancestor → branch | Method name | 1 → subtree | The branch itself is the addressee ("this room") |
| `await` on a signal | Sequencer → emitter | Emitter's signal | 1 → 1 | Linear choreography within one lifetime scope |

If a communication need does not fit any row cleanly, that is usually the design telling you a node is missing — a mediator, a component, or a bus signal that names the *fact* instead of the participants.

---

## Groups in production

Groups are the tree's tagging system: any node can join any number of named groups, and the SceneTree can enumerate or broadcast to a group in one call. Where paths say "the node at this address" and references say "this exact object", groups say **"whoever currently plays this role"** — the most refactor-proof identity of the three.

```gdscript
# Joining: in the editor (Node dock → Groups) or in code:
func _enter_tree() -> void:
	add_to_group(&"pausable_fx")        # membership auto-clears on tree exit

# Querying:
var fx_nodes := get_tree().get_nodes_in_group(&"pausable_fx")   # Array[Node]
var first := get_tree().get_first_node_in_group(&"pausable_fx") # Node or null

# Broadcasting — method must exist on members (missing methods error):
get_tree().call_group(&"pausable_fx", &"on_theme_changed", theme)
get_tree().set_group(&"pausable_fx", "speed_scale", 0.5)
get_tree().call_group_flags(SceneTree.GROUP_CALL_DEFERRED, &"pausable_fx", &"reset")
```

Details that matter:

- Editor-assigned groups are **persistent** (saved in the scene); code-assigned ones are runtime-only unless you pass `persistent = true` to `add_to_group`. Both behave identically at runtime.
- Membership queries (`is_in_group`) are fast; `get_nodes_in_group` allocates an array — cache it if you query every frame, or better, maintain your own typed list fed by `_enter_tree`/`_exit_tree` of members.
- `call_group` is immediate and unordered-ish (scene order); use the `GROUP_CALL_DEFERRED` flag whenever handlers might mutate the tree.
- Groups carry no type information — `get_nodes_in_group` returns `Array[Node]`. Standard hardening: members implement a documented method set (an implicit interface), and callers `assert` in debug builds.

The **singleton-by-group** idiom deserves special mention: for "there is exactly one X right now" (current camera rig, current room), a group plus `get_first_node_in_group` beats both an autoload (no global state) and stored references (no dangling pointers after scene changes):

```gdscript
# whoever is the active room registers itself; nobody stores it long-term.
func _enter_tree() -> void:
	add_to_group(&"active_room")

# any system, any time:
var room := get_tree().get_first_node_in_group(&"active_room") as RoomBase
if room != null:
	room.place_decoration(id, cell)
```

### Worked example: a self-registering minimap

Groups shine when *unknown, changing sets* of nodes must feed one consumer. A minimap that tracks "everything trackable" needs zero configuration if trackables register themselves:

```gdscript
# trackable_component.gd — drop onto anything that should appear on the minimap.
class_name TrackableComponent
extends Node

@export var icon: Texture2D

func _enter_tree() -> void:
	add_to_group(&"minimap_trackable")
# membership clears itself on exit — despawned objects vanish from the map for free
```

```gdscript
# minimap.gd — consumer polls the group; it never knows concrete types.
extends Control

func _process(_delta: float) -> void:
	queue_redraw()

func _draw() -> void:
	for t in get_tree().get_nodes_in_group(&"minimap_trackable"):
		var host := t.get_parent() as Node2D
		if host:
			draw_texture(t.icon, _world_to_map(host.global_position))
```

Spawn a new character, drop a decoration, instance a visitor — each appears on the map the frame it enters the tree, and disappears when freed, with no registration calls anywhere. Compare the alternatives honestly: a manager with `register()`/`unregister()` calls does the same with more code and two new failure modes (forgot to register; forgot to unregister — the leak-shaped bug). The group *is* the registry, maintained by the tree itself.

> ✅ **Best practice** — Maintain a `groups.md` (or a constants file `res://scripts/groups.gd` with `const ENEMIES := &"enemies"`) listing every group name, its expected member API and who broadcasts to it. Stringly-typed systems live or die by documentation; the constants file additionally gives you autocomplete and refactorable names.

---

## Composition over inheritance

GDScript gives you class inheritance (`extends`), and the scene system gives you scene inheritance. Both are *vertical* reuse: a child is a kind-of its base. Godot's node model, though, was designed for *horizontal* reuse — building objects by **assembling small nodes**, each contributing one capability. Production experience across the Godot ecosystem converges hard on the horizontal style.

### Why deep inheritance hurts

Imagine the vertical route for Relax Room's interactive objects: `InteractableBase` → `FurnitureBase` → `SeatFurniture` → `BedFurniture`… Then design asks for a bed that is also a storage container, and a window seat that is furniture *and* a light source. Single inheritance forces a choice: duplicate code, or push everything into the base "just in case" until `InteractableBase` is a 900-line god class where every subclass pays for every feature. Each new cross-cutting requirement (highlightable? draggable? saveable?) multiplies the pain, because inheritance can only stack capabilities in one fixed order.

### Component nodes

The horizontal route models each capability as a small node — a **component** — that attaches as a child of whatever needs it:

```gdscript
# hover_highlight_component.gd — makes ANY CanvasItem parent glow on hover.
class_name HoverHighlightComponent
extends Node

@export var highlight_color: Color = Color(1.25, 1.25, 1.1)

var _target: CanvasItem

func _notification(what: int) -> void:
	if what == NOTIFICATION_PARENTED:
		_target = get_parent() as CanvasItem   # discover the host on attach

func _ready() -> void:
	if _target == null:
		push_warning("HoverHighlightComponent needs a CanvasItem parent")
		return
	var area := _target.get_node_or_null("HoverArea") as Area2D
	if area:
		area.mouse_entered.connect(func() -> void: _target.modulate = highlight_color)
		area.mouse_exited.connect(func() -> void: _target.modulate = Color.WHITE)
```

Now a bed is `StaticBody2D + Sprite2D + CollisionPolygon2D + HoverHighlightComponent + StorageComponent`, and the window seat composes a different set. Capabilities combine freely; deleting a component removes a capability with zero refactoring; and each component is testable in a scene of its own.

```
bed_black_1 (StaticBody2D)                 window_seat (StaticBody2D)
├── Sprite2D                               ├── Sprite2D
├── CollisionPolygon2D                     ├── CollisionPolygon2D
├── HoverArea (Area2D)                     ├── HoverArea (Area2D)
├── HoverHighlightComponent                ├── HoverHighlightComponent
└── StorageComponent                       └── LightSourceComponent
```

Design guidelines that keep components honest:

- **A component knows its host through a narrow door**: `get_parent()` typed to an interface-like base, or an `@export var target: Node` the assembler sets. It never assumes a specific concrete scene.
- **Components communicate outward with signals** (`storage_opened`, `highlight_started`), never by finding sibling components by name.
- **Configuration is `@export`ed**, so designers tune per instance in the Inspector.
- Keep them **Node-based unless they need a transform** — a pure-logic component extending `Node` costs nothing in 2D transform math.

### When a component deserves its own scene

A component that is a single script on a single node ships as a script (`class_name` + "Add Child Node → HoverHighlightComponent"). Promote it to a **component scene** the moment it has internal structure: the `HurtboxComponent` below carries its own `CollisionShape2D`; a `FootstepAudioComponent` might bundle an `AudioStreamPlayer2D` plus a `Timer`. The scene form buys Inspector-visible defaults, internal wiring saved once, and F6 testability — the same arguments as any scene split, applied at component scale.

```
hurtbox_component.tscn
└── HurtboxComponent (Area2D) — hurtbox_component.gd
    └── CollisionShape2D          (shape configured per use via editable children)
```

The assembly workflow changes only slightly: hosts instance the component scene instead of adding a node, and per-host tuning happens through exported properties (preferred) or editable children (for the shape). Either way, the host's dock reads as a *bill of capabilities* — which is the entire point of composition: the scene tree documents what the object does.

### Where inheritance still wins

Composition is the default, not a religion. Script inheritance earns its keep for **shared algorithms with template methods** (a `PanelBase` with open/close animation calling overridable `_populate()`), and scene inheritance for **N cosmetic variants of one structure** (the character roster from the previous section). The practical rule the codebase review should enforce: inheritance depth ≤ 2 for scripts and scenes alike, and *any* "Base" class that accumulates unrelated capabilities is scheduled for decomposition into components.

> ✅ **Best practice** — When you cannot decide, ask the substitution question: "will every future subclass need *all* of this, or just some of it?" All → inheritance is fine. Some → make components now; retrofitting composition later costs ten times more than starting with it.

### A complete component pair: Health + Hurtbox

One worked pair shows every composition rule in action. First, a health component — pure logic, `Node`-based, host-agnostic:

```gdscript
# health_component.gd
class_name HealthComponent
extends Node

signal health_changed(current: int, maximum: int)
signal died

@export var max_health: int = 100

var health: int:
	set(value):
		var clamped := clampi(value, 0, max_health)
		if clamped == health:
			return
		health = clamped
		health_changed.emit(health, max_health)
		if health == 0:
			died.emit()

func _ready() -> void:
	health = max_health

func take_damage(amount: int) -> void:
	health -= amount

func heal(amount: int) -> void:
	health += amount
```

Second, a hurtbox — an `Area2D` that *detects* incoming hits and forwards them to whichever health component it was wired to:

```gdscript
# hurtbox_component.gd
class_name HurtboxComponent
extends Area2D

@export var health: HealthComponent      # wired in the Inspector by the host scene

func _ready() -> void:
	area_entered.connect(_on_area_entered)

func _on_area_entered(area: Area2D) -> void:
	if health == null:
		return
	var damage := area.get(&"damage")     # duck-typed: any area with a 'damage' property
	if damage != null:
		health.take_damage(damage)

func _get_configuration_warnings() -> PackedStringArray:
	return PackedStringArray() if health != null \
			else PackedStringArray(["Assign a HealthComponent to 'health'."])
```

A host assembles them and decides what death *means* — the components never presume:

```
Character (CharacterBody2D) — character_controller.gd
├── CollisionShape2D
├── AnimatedSprite2D
├── HealthComponent
└── HurtboxComponent (Area2D)
    └── CollisionShape2D
```

```gdscript
# character_controller.gd — only the HOST knows the host's death behavior.
@onready var _health: HealthComponent = $HealthComponent

func _ready() -> void:
	_health.died.connect(_on_died)
	_health.health_changed.connect(func(c: int, m: int) -> void:
		mood = &"tired" if c < m / 4 else &"calm")

func _on_died() -> void:
	set_physics_process(false)
	%AnimatedSprite2D.play(&"faint")      # Relax Room characters faint, not die
	await %AnimatedSprite2D.animation_finished
	SignalBus.character_fainted.emit()
```

Audit the dependency arrows: `HurtboxComponent → HealthComponent` via an Inspector-wired export; `host → components` via `$`; components → host via signals only. Nothing points upward by path, every piece runs standalone under F6, and a decoration that should become damageable acquires the exact same two children plus five lines of wiring.

---

## The 2D node families

Godot's node classes form their own (engine-side) inheritance tree, and knowing the 2D branch's layout tells you instantly what any node can do. Everything visible in 2D descends from **`CanvasItem`**, which splits into **`Node2D`** (world objects, freely transformable) and **`Control`** (UI, anchor/layout-driven). This section tours the families you will compose daily; sibling modules deepen each ([SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md), [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md), [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md)).

### Node2D transforms — local vs global

Every `Node2D` carries a 2D transform composed of `position`, `rotation` (radians; `rotation_degrees` for the editor-friendly view), `scale`, and `skew`. The transform is **local** — expressed in the parent's coordinate space — and the engine multiplies transforms down the branch, which is what makes trees so convenient: move the `Room`, and every decoration inside moves along.

```gdscript
extends Node2D

func _ready() -> void:
	position = Vector2(64, 32)          # relative to the PARENT
	rotation = deg_to_rad(15.0)         # radians in code
	scale = Vector2(3, 3)               # multiplies all children too

	# Global variants — same node, world coordinates:
	print(global_position)              # parent transforms applied
	global_position = Vector2(640, 360) # engine recomputes the local value

	# Converting between spaces — essential for drag & drop:
	var local_click := to_local(get_global_mouse_position())
	var world_point := to_global(Vector2.ZERO)   # this node's origin in world space
```

> ⚠️ **Pitfall** — Mixing spaces is the classic isometric-project bug (see [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md)): comparing a `global_position` against a `position`, or feeding world coordinates into a child-space function. The symptom is objects "teleporting" by exactly the parent's offset. Convention that prevents it: variables holding world-space values end in `_global`, and any function taking coordinates documents its space in the parameter name (`screen_pos`, `cell`, `world_point`).

Two more transform behaviors worth knowing: `top_level = true` makes a `CanvasItem` ignore its parent's transform entirely (useful for health bars that should not rotate with the enemy), and non-uniform parent `scale` combined with child `rotation` produces skew — if a rotated child looks sheared, hunt for a `(1.3, 0.7)`-style scale upstream.

### CanvasItem visibility and tinting

`CanvasItem` contributes the visibility/tint layer shared by all 2D nodes:

| Property/method | Effect |
|---|---|
| `visible`, `show()`, `hide()` | Hides this node **and its whole branch**; hidden nodes still process (pair with `process_mode` if you want them dormant) |
| `is_visible_in_tree()` | `false` if any ancestor is hidden — the check that actually matters |
| `modulate` | Tint/alpha multiplied down the branch — fade a whole popup with one tween |
| `self_modulate` | Tint applied to this item only, children unaffected |
| `z_index`, `z_as_relative` | Draw-order override beyond sibling order; relative adds to the parent's z |
| `y_sort_enabled` | Children draw sorted by global Y — the isometric depth workhorse |
| `light_mask`, `material` | Interaction with 2D lights and shaders — see [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md) |

### The families at a glance

| Family | Key nodes | Role | Notes |
|---|---|---|---|
| Structure | `Node`, `Node2D`, `Marker2D` | Grouping, transforms, authored positions | `Node` for pure logic (no transform cost); `Marker2D` = editor-visible point |
| Visual | `Sprite2D`, `AnimatedSprite2D`, `Line2D`, `Polygon2D`, `TileMapLayer` | Drawing | Deep dive: [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md), [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md) |
| Physics bodies | `StaticBody2D`, `CharacterBody2D`, `RigidBody2D`, `Area2D` | Solidity, movement, detection | Body chooses the *movement model*; `Area2D` detects without blocking |
| Physics shapes | `CollisionShape2D`, `CollisionPolygon2D` | Define the body's extent | Always a **direct child** of the body/area — a shape without a body parent does nothing and warns |
| Path | `Path2D`, `PathFollow2D` | Curves and movement along them | `PathFollow2D.progress`/`progress_ratio` drives followers |
| Camera | `Camera2D` | Viewport into the world | `enabled`, `zoom`, limits, smoothing; one active camera per viewport |
| Audio | `AudioStreamPlayer2D` | Positional sound | Non-positional UI sound → plain `AudioStreamPlayer` |
| UI | `Control`, containers, `Label`, `Button`, `ColorRect` | Screen-space interface | Anchors/containers, not transforms — mixing the two models is the #1 UI mistake |
| Timing | `Timer` | Countdown with `timeout` signal | Dies with its parent — safer than SceneTree timers for node-bound waits |

### Two small nodes worth knowing early

**`Marker2D`** is a `Node2D` that draws a cross in the editor and nothing at runtime — an *authored position*. Use markers instead of magic-number `Vector2`s for spawn points, walk targets and camera anchors; designers can then move them visually, and code reads intent:

```gdscript
@onready var _entry_point: Marker2D = $EntryPoint
@onready var _seat_positions: Array[Node] = $Seats.get_children()  # all Marker2D

func seat_character(character: Node2D, index: int) -> void:
	character.global_position = (_seat_positions[index] as Marker2D).global_position
```

**`RemoteTransform2D`** pushes its own global transform onto another node, referenced by `remote_path` — transform-following *without* parenting. The canonical use: a status bubble that must track a character but draw in the UI layer (different parent, different canvas):

```gdscript
# Under the character:
# RemoteTransform2D · remote_path → ../../UILayer/MoodBubble  (wired via @export in code)
# The bubble follows the character's position while living — and drawing — in the UI stratum.
```

It is the structural answer to "this node needs *that* node's transform but a different parent" — a question that otherwise tempts people into per-frame `global_position` copying in `_process`.

### Physics quick-orientation: bodies, layers, masks

Full physics belongs to a later module, but scene composition requires the vocabulary now. A *body* owns shapes and participates in the physics world according to two bitfields: `collision_layer` — which layers **I am on** (what others can see me as) — and `collision_mask` — which layers **I look at** (what I collide with or detect). The Relax Room setup, preserved from the original module:

```
Layer 1 = room walls        (StaticBody2D of the floor bounds)
Layer 2 = decorations       (StaticBody2D of placed furniture)

CharacterBody2D:
  collision_layer = 0   # the character is an obstacle for nobody
  collision_mask  = 3   # collides WITH layers 1 and 2 (walls + decorations)
  collision_mask  = 1   # …reduced to walls only while in edit mode
```

`mask = 3` reads as a bitfield: layer 1 (bit 0, value 1) + layer 2 (bit 1, value 2) = 3 (binary `11`). Name your layers in *Project Settings → Layer Names → 2D Physics* so the Inspector shows words instead of bits, and never ship `collision_mask = -1` ("collide with everything") — it hides design intent and costs performance.

### Control nodes and mouse_filter

`Control` nodes position themselves through **anchors and offsets** relative to the parent control, not through `Node2D` transforms — the details are a UI-module topic, but two properties belong in this module because they shape scene structure. Anchor presets (`FULL_RECT` to fill the parent, `CENTER` to pin at the middle) determine how the branch reacts to window resizing — critical for a desktop companion whose window users resize freely. And `mouse_filter` decides how each control participates in input routing:

```gdscript
# Control.mouse_filter — who eats the click?
# MOUSE_FILTER_STOP   (0): consume the event; nothing below receives it (default for buttons)
# MOUSE_FILTER_PASS   (1): react AND let it continue to controls underneath
# MOUSE_FILTER_IGNORE (2): completely transparent to the mouse
```

The Relax Room `DropZone` is a full-screen `Control` with `MOUSE_FILTER_PASS`: it must observe drags anywhere on screen *without* stealing clicks from the HUD buttons above the room. A full-screen control accidentally left on `STOP` is the canonical "my buttons stopped working" bug — remember it for the troubleshooting table.

### Camera2D in a fixed-room game

`Camera2D` earns a note even in a mostly-static game like Relax Room, because "no camera" and "default camera" behave differently. With no `Camera2D` in the tree, the canvas renders from origin at 1:1 — fine while the room exactly fits the window. Add one camera (`enabled = true`; only one is active per viewport) and you gain the production knobs for free:

```gdscript
@onready var _cam: Camera2D = $Camera2D

func _ready() -> void:
	_cam.zoom = Vector2(1.0, 1.0)              # >1 zooms IN (Godot 4 semantics!)
	_cam.limit_left = 0                         # clamp the view to the room rect
	_cam.limit_right = 1280
	_cam.limit_top = 0
	_cam.limit_bottom = 720
	_cam.position_smoothing_enabled = true      # eased follow for the focus target
```

Remember from [CanvasLayer](#canvaslayer-and-draw-order): the camera transforms only the world canvas — the `UILayer` ignores it, which is the entire point of the layer split. And a zoom detail that bites Godot 3 veterans: in Godot 4, `zoom = Vector2(2, 2)` means *magnified twice*, the inverse of Godot 3's convention.

### The Timer node, precisely

The [SceneTree timer](#the-get_tree-api-surface) is fire-and-forget; the `Timer` **node** is its stateful sibling and the right choice whenever a wait belongs to a node's lifetime or needs control:

| Capability | `Timer` node | `SceneTreeTimer` |
|---|---|---|
| Stop / restart / query time left | `stop()`, `start()`, `time_left` | `time_left` only — cannot cancel |
| Repeating | `one_shot = false` | never — single shot |
| Dies with its owner | yes (it is a child) | no — runs to completion regardless |
| Pause behavior | via `process_mode`, like any node | `process_always` flag at creation |
| Editor-configurable | yes (Inspector, connections) | no |

```gdscript
@onready var _idle_timer: Timer = $IdleTimer    # wait_time = 8, one_shot = true (Inspector)

func _on_player_interaction() -> void:
	_idle_timer.start()                          # restart the countdown from full

func _on_idle_timer_timeout() -> void:
	%AnimatedSprite2D.play(&"stretch")           # character stretches when ignored for 8 s
```

The rule of thumb the [get_tree() section](#the-get_tree-api-surface) promised: **node-bound or cancellable waits → `Timer` node; global one-off waits → `create_timer()`.** Misusing the second for the first is how despawned characters play animations from beyond the grave.

### Y-sorting — depth for isometric rooms

Sibling order works as long as depth is static. The moment a character can walk *behind or in front of* the same bed depending on position, static order fails — the archetypal 2D-isometric problem, and the reason `y_sort_enabled` exists. Set it on the **container**, and that container draws its child canvas items sorted by their global Y (lower on screen = drawn later = in front), re-evaluated every frame:

```gdscript
# room_base.gd — depth sorting for the walkable area:
func _ready() -> void:
	%Decorations.y_sort_enabled = true    # decorations sort among themselves…
	# …and the character participates by being a sibling under the same sorted parent.
```

Two setup rules make or break it. First, **the sort key is each node's origin**, so sprites must have their origin at their *feet* (the point that touches the floor) — offset the `Sprite2D` upward (`offset.y < 0` or `centered = false` with a crafted offset) rather than moving the parent. A bed whose origin sits at its visual center will pop in front of the character too early. Second, **all competitors must be children of the same y-sorted parent** (y-sort nests: a y-sorted child container merges its children into the parent's sort). If the character lives outside `Decorations`, either move it under the sorted container or make `Room` itself the sorted parent — Relax Room does the latter, with `Decorations` and `Character` as sorted siblings.

Escape hatches for the exceptions: a rug must *always* lie under everything (`z_index = -1` — z beats y-sort), a floating hint bubble always on top (`z_index = 1`). Keep the exceptions in single digits; if half the room needs z overrides, the origins are wrong. Full isometric treatment — diamond grids, tile-level sorting, `TileMapLayer` y-sort origin: [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md) and [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md).

---

## CanvasLayer and draw order

2D draw order is resolved in this order of precedence: **CanvasLayer first, then `z_index`, then tree order.** Within one canvas layer, higher `z_index` wins; at equal z, later siblings draw on top. `CanvasLayer` nodes create *separate* canvases with an integer `layer` — every canvas item lives in the layer of its nearest `CanvasLayer` ancestor (or the implicit layer 0 of the scene canvas).

The property that makes `CanvasLayer` indispensable: **its children ignore the world camera**. A `Camera2D` transforms the scene canvas — pan, zoom, shake — but each `CanvasLayer` has its own transform, unaffected by default. That is precisely what UI needs: the HUD must not zoom when the room zooms.

```gdscript
var ui_layer := CanvasLayer.new()
ui_layer.layer = 10          # above the world (default layer of world content = 0)
add_child(ui_layer)

# Layer conventions (Relax Room):
#   layer < 0   → backgrounds behind the world (e.g. -10 sky)
#   layer  0    → the game world itself (no CanvasLayer needed)
#   layer 10    → HUD, buttons, panels
#   layer 100   → popups, modals, auth screen
```

Facts and edge cases:

- `CanvasLayer` is **not** a `CanvasItem`: it has no `modulate`, no `visible`-in-tree interplay with canvas items above it (it does have its own `visible`), and it cannot be tinted as a group directly — put a `Control` root inside the layer and modulate that instead.
- `follow_viewport_enabled = true` makes the layer follow the camera after all — for world-space overlays (damage numbers, speech bubbles) that still want layer-based draw grouping.
- A `CanvasLayer` affects **only its descendants**. Placing it as a sibling "above" other nodes does nothing to them — a common misread of the Scene dock.
- `z_index` never crosses layers: `z_index = 4096` in layer 0 still draws below everything in layer 1. When a popup hides behind the HUD despite a huge z, the fix is the *layer*, not more z.
- `Window`/`Popup` nodes (used for dialogs) render above all canvas layers of their parent viewport — the escape hatch when even layers are not enough.

> ✅ **Best practice** — Reserve `z_index` for *fine-grained* ordering within a system (overlap resolution inside the world, y-sorted decorations) and `CanvasLayer` for *coarse-grained* strata (world / HUD / modal). If you find yourself using three-digit z-indexes to fight the HUD, you needed a layer. Document the layer map in the main scene's script header, as the case study does.

### Worked example: a modal stack on layer 100

The "popups live on layer 100" convention becomes robust once one node owns it — a modal manager that stacks popups, dims the world, and restores state as they close:

```gdscript
# modal_layer.gd — autoload "Modals". CanvasLayer with layer = 100.
extends CanvasLayer

var _stack: Array[Control] = []
@onready var _dim: ColorRect = $DimRect     # full-rect, black, alpha 0, IGNORE mouse

func push_modal(modal: Control) -> void:
	if _stack.is_empty():
		_dim.mouse_filter = Control.MOUSE_FILTER_STOP   # swallow clicks under modals
		create_tween().tween_property(_dim, "color:a", 0.5, 0.15)
		get_tree().paused = true                         # world pauses; we are ALWAYS
	_stack.append(modal)
	add_child(modal)
	modal.tree_exiting.connect(_on_modal_gone.bind(modal), CONNECT_ONE_SHOT)

func _on_modal_gone(modal: Control) -> void:
	_stack.erase(modal)
	if _stack.is_empty():
		_dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
		create_tween().tween_property(_dim, "color:a", 0.0, 0.15)
		get_tree().paused = false
```

Half this module converges in twenty lines: the layer split keeps modals above any camera work; `process_mode = ALWAYS` on the autoload (set in its scene) lets modals run while the world pauses; the dim rect flips `mouse_filter` to become a click-shield only when needed; and cleanup keys off `tree_exiting` — a modal can die by any means (`queue_free`, scene change) and the stack stays consistent, with `CONNECT_ONE_SHOT` preventing stale connections. Popup content itself remains ordinary scenes; the manager owns *policy*, not layout.

---

## Tool scripts and editor integration

By default, scripts run only in the exported game and when you press Play. Add **`@tool`** as the first line and the script also executes **inside the editor** — its `_ready`, `_process`, `_draw`, setters, everything. This is how you build scenes that *preview themselves*: a room grid that draws its cells while you edit, a path that shows its curve, a procedural background that renders without pressing F5.

```gdscript
@tool
extends Node2D
## room_grid.gd — draws a 64 px grid in the editor and in debug builds.

@export var cell_size: int = 64:
	set(value):
		cell_size = maxi(8, value)
		queue_redraw()                  # re-run _draw when the Inspector changes it

@export var grid_color: Color = Color(1, 1, 1, 0.15):
	set(value):
		grid_color = value
		queue_redraw()

func _draw() -> void:
	# Runs in-editor thanks to @tool; at runtime only when visible.
	var view := get_viewport_rect().size
	for x in range(0, int(view.x) + 1, cell_size):
		draw_line(Vector2(x, 0), Vector2(x, view.y), grid_color)
	for y in range(0, int(view.y) + 1, cell_size):
		draw_line(Vector2(0, y), Vector2(view.x, y), grid_color)
```

### Separating editor and runtime behavior

`@tool` makes *everything* run in the editor — including gameplay logic you absolutely do not want executing while you edit (spawning, saving, network calls). `Engine.is_editor_hint()` is the switch:

```gdscript
@tool
extends CharacterBody2D

func _physics_process(delta: float) -> void:
	if Engine.is_editor_hint():
		return                          # never simulate movement inside the editor
	_apply_movement(delta)

func _ready() -> void:
	_update_preview_sprite()            # runs in BOTH contexts — visual setup
	if not Engine.is_editor_hint():
		SignalBus.character_changed.connect(_on_character_changed)  # runtime only
```

Rules and hazards, condensed from the official "Running code in the editor" guide:

- A `@tool` script that touches another script's members needs that script to be `@tool` as well (static methods and constants excepted). Extending a `@tool` script does **not** inherit tool mode — the child script must repeat the annotation.
- Editor-side mutations are *real*: change a property from tool code and the scene saves it, with **no undo**. `queue_free()` on nodes the editor is using can crash the editor. Guard destructive branches with `Engine.is_editor_hint()` paranoia.
- Nodes created by tool code persist only if you assign `owner = get_tree().edited_scene_root` — otherwise they exist in the editor session and vanish from the saved `.tscn`.
- Develop the logic first *without* `@tool`, test it at runtime, then add the annotation — debugging editor crashes caused by half-written tool code is miserable.

### Configuration warnings

Tool scripts can validate their own scene setup and surface problems as the yellow warning triangle in the Scene dock — the same mechanism built-in nodes use ("CollisionShape2D only serves to provide a shape…"). Implement `_get_configuration_warnings() -> PackedStringArray`; return an empty array when everything is fine:

```gdscript
@tool
class_name DropZone
extends Control

@export var room_path: NodePath:
	set(value):
		room_path = value
		update_configuration_warnings()   # re-evaluate when the setup changes

func _get_configuration_warnings() -> PackedStringArray:
	var warnings := PackedStringArray()
	if room_path.is_empty():
		warnings.append("DropZone needs 'room_path' pointing at the Room node.")
	if mouse_filter == MOUSE_FILTER_STOP:
		warnings.append("mouse_filter STOP will block HUD buttons — use PASS.")
	return warnings
```

The editor calls this when the scene loads and whenever you call `update_configuration_warnings()`. Cheap to write, and it converts tribal knowledge ("remember to set the path!") into machine-checked setup — exactly the kind of guard a team codebase accumulates.

> ✅ **Best practice** — Every reusable scene with a mandatory `@export` deserves a configuration warning. It is the closest thing Godot has to a compile-time check on scene wiring, and it fires *in the editor*, before anyone wastes a run discovering the missing reference.

### Editor-side hygiene for tool code

A few habits keep `@tool` code from biting the team. Print output from tool scripts lands in the editor's Output panel — prefix it (`print("[RoomGrid] ...")`) or it drowns among everyone else's noise. `EditorInterface` (the editor-services singleton: selection, edited scene root, filesystem dock) exists **only in the editor** — any reference to it in code that ships must sit behind `Engine.is_editor_hint()` *and* ideally behind `OS.has_feature("editor")` checks, or exports break. Editor-side structural edits from plugins should go through `EditorUndoRedoManager` so users can Ctrl+Z your tool's changes — bare mutations work but make the tool feel hostile.

Finally, two Node notifications exist specifically for tool scripts: `NOTIFICATION_EDITOR_PRE_SAVE` and `NOTIFICATION_EDITOR_POST_SAVE` fire around scene saves in the editor. The pre-save hook is the sanctioned place to strip transient preview nodes (spawned grid markers, debug visualizations) so they never pollute the `.tscn`; post-save is where you rebuild them:

```gdscript
@tool
extends Node2D

func _notification(what: int) -> void:
	match what:
		NOTIFICATION_EDITOR_PRE_SAVE:
			_clear_preview_markers()        # keep the saved file clean
		NOTIFICATION_EDITOR_POST_SAVE:
			_rebuild_preview_markers()      # restore the editing experience
```

---

## Scene organization for real projects

Everything so far concerned single scenes and pairs of scenes. Zoom out: a production project is dozens of scenes, scripts and asset folders, and its structure is a daily tax or a daily gift. The conventions below are the ones the Relax Room repository follows; they synthesize the official project-organization guide with what has worked in the field.

### Folder structure: by feature, not by type

```
res://
├── project.godot
├── assets/                  # imported art/audio, mirrored from the source-art repo
│   ├── characters/
│   ├── rooms/
│   └── ui/
├── scenes/                  # .tscn files, grouped by FEATURE
│   ├── main.tscn
│   ├── characters/
│   │   ├── character_base.tscn
│   │   └── male_old_character.tscn
│   ├── menu/
│   │   └── main_menu.tscn
│   ├── room/
│   │   ├── bed_black_1.tscn
│   │   └── window_1.tscn
│   └── ui/
│       └── auth_screen.tscn
├── scripts/                 # .gd files mirroring scenes/ layout
│   ├── main.gd
│   ├── autoload/            # SignalBus, SaveManager, ThemeService…
│   ├── components/          # reusable component nodes
│   ├── menu/
│   ├── rooms/
│   └── ui/
└── data/                    # JSON/Resource catalogs (decorations.json, …)
```

The organizing principle is **feature cohesion**: the things you edit together live together. A pure by-type layout (`all_scripts/`, `all_scenes/`) forces every feature change to touch four distant folders; a by-feature layout keeps the blast radius of "rework the menu" inside `menu/` directories. Whether scripts sit next to their scenes or in a mirrored `scripts/` tree is a team taste decision — Relax Room mirrors them — but *pick one and enforce it*.

Naming conventions, mechanical on purpose: `snake_case` for files and folders (`male_old_character.tscn` — avoids case-sensitivity surprises across Windows/Linux and in exports), `PascalCase` for node names and `class_name`s, and the scene root node named like the scene file (`main_menu.tscn` → root `MainMenu`). A file you cannot find in three seconds is a convention violation, not a search-skills problem.

### One scene, one responsibility

The single most load-bearing convention: **every scene answers to one sentence.** "The main menu." "One placeable decoration." "The authentication screen." When a scene's description needs "and" — "the room *and* the character *and* the HUD" — it is three scenes composed by a fourth. The payoffs compound: F6-testability (run any scene alone), merge-conflict isolation (one feature = one file), and honest dependency review (the composing scene's wiring code *is* the architecture).

The complementary structural rule, from the official scene-organization guide: the main scene is an **entry point that composes subsystems**, each swappable — a `Main` with `World` and `GUI` children, where "load a different level" means replacing the `World` child and nothing else. Ask of every node: *does it depend on its parent's existence?* If not, it can live anywhere — so put it where its feature lives, not where you happened to create it.

> ⚠️ **Pitfall** — Beware the "misc" folder and the "helpers" scene. Both are entropy attractors: every object without an obvious home lands there, and within months they are the largest, least understood parts of the project. If something has no home, that is a design smell to resolve *now* — invent the feature folder it belongs to, or question why it exists.

### Review checklist for a new feature scene

Scene structure is code and deserves review like code. The questions Relax Room reviewers ask of every new `.tscn` before merge — each one traceable to a section of this module:

1. **Does the scene run standalone (F6) without errors?** If not, it has hidden dependencies — find the upward grab or missing injection.
2. **Is the root type right?** `Node2D` for world objects, `Control` for UI, plain `Node` for pure logic. A `Control` root on a world object (or vice versa) fights the coordinate model forever.
3. **Is the root named like the file**, and are all nodes PascalCase with intention-revealing names? (`Sprite2D` as a name is fine for the only sprite; `Sprite2D2` never is.)
4. **Do all `../` paths and cross-scene `$` lookups justify themselves?** Expected answer: there are none; wiring is `@export`/`%`/signals.
5. **Are signals declared on the scene's root script** (its public API) rather than deep internals that outsiders would have to reach into?
6. **Does anything connect to an autoload?** Then `_exit_tree` disconnects it — non-negotiable, per the audit.
7. **Are `process_mode`, `process_priority`, collision layers/masks left at defaults** unless a comment says why not?
8. **Does the scene leak?** Instantiate + free it in a loop in a scratch scene; the Orphan Nodes monitor must return to baseline.
9. **Would a designer understand the dock?** The tree reads as a bill of parts and capabilities; mystery wrapper nodes carry a comment or a better name.

Nine questions, thirty seconds each once habitual — and they catch the majority of the troubleshooting table before it ships.

### Scenes under version control

`.tscn` is a deliberately human-readable text format — INI-like sections for nodes, properties and connections — precisely so that version control works on scenes. Working *with* the format instead of against it:

- **Diff scenes in review.** A `.tscn` diff showing `position = Vector2(640, 360)` → `(640, 420)` is reviewable; treat scene diffs as first-class code review material, not noise to skip.
- **Small scenes, few conflicts.** Git merges `.tscn` textually, with no understanding of node semantics — two branches touching the *same* scene routinely produce merges that parse but are wrong (duplicated node sections, dangling connections). The one-scene-one-responsibility rule is also a merge strategy: partition work so two people rarely edit one file.
- **When a scene merge happens anyway**, re-open the scene in the editor immediately (or *Scene → Reload Saved Scene*) — the editor is the only validator; a broken merge fails loudly there instead of at runtime on a teammate's machine.
- **Commit the sidecar files.** Godot tracks resources by UID; scripts and scenes carry `.uid` companions (Godot 4.4+) and `.import` files describe asset conversion. All of them belong in the repository — missing UID files cause "broken dependency" churn for everyone else.
- **Never commit `.godot/`.** It is a per-machine cache (imported binaries, editor state); ignoring it is the first line of every Godot `.gitignore`.
- **Expect noise lines and keep them out of PRs**: the editor rewrites `ext_resource` ids and property order opportunistically. A "format-only" scene save mixed into a logic PR doubles review cost — save scenes deliberately, commit them separately when the churn is cosmetic.

Build and CI implications of project layout continue in [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md).

---

## Case study: Relax Room scene architecture

> **Case study** — The sections below document the actual scene trees of the Relax Room desktop companion, preserved from the project's study notes and annotated with this module's vocabulary. Cross-reference: [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) walks the full codebase; [GAME_DEV_PLANNING.md](GAME_DEV_PLANNING.md) covers the planning that produced this structure.

### main.tscn — the main game scene

```
Main (Node2D) — scripts/main.gd
├── RoomBackground (Sprite2D)       → room.png, centered at (640, 360)
├── WallRect (ColorRect)            → wall overlay, top 40%, alpha 0.6
├── FloorRect (ColorRect)           → floor overlay, bottom 60%, alpha 0.6
├── Baseboard (ColorRect)           → 1 px separator line between wall and floor
├── Room (Node2D) — scripts/rooms/room_base.gd
│   ├── Decorations (Node2D)        → empty container; decorations added at runtime
│   ├── Character (CharacterBody2D) → instance of male_old_character.tscn
│   │   ├── CollisionShape2D        → CapsuleShape2D (radius 16, height 56)
│   │   └── AnimatedSprite2D        → 13 animations, scale (3, 3)
│   └── RoomBounds (StaticBody2D)
│       └── FloorBounds (CollisionPolygon2D) → walkable area
├── RoomGrid (Node2D) — scripts/rooms/room_grid.gd
│   └── (draws a 64 px grid via _draw(), visible only in edit mode)
└── UILayer (CanvasLayer, layer = 10)
    ├── DropZone (Control) — scripts/ui/drop_zone.gd
    │   └── anchors_preset: FULL_RECT, mouse_filter: PASS
    └── HUD (HBoxContainer)
        ├── DecoButton (Button)
        ├── SettingsButton (Button)
        └── ProfileButton (Button)
```

**Rendering flow (bottom to top)** — the Scene dock order *is* the painter's algorithm from [The SceneTree](#the-scenetree):

1. `RoomBackground` — the room image, scaled to fill the viewport
2. `WallRect` + `FloorRect` — semi-transparent color overlays for theming
3. `Baseboard` — decorative line at the wall/floor junction
4. `Room/Decorations` — decoration sprites
5. `Room/Character` — the character (above the decorations)
6. `RoomGrid` — visual grid (edit mode only)
7. `UILayer` (CanvasLayer 10) — HUD and panels above everything, camera-independent

Note how the module's concepts appear in miniature: the `UILayer` is the coarse stratum from [CanvasLayer and draw order](#canvaslayer-and-draw-order); `DropZone` uses `MOUSE_FILTER_PASS` so HUD buttons stay clickable; `Decorations` is an intentionally empty runtime container ([Creating and removing nodes at runtime](#creating-and-removing-nodes-at-runtime)); and `RoomGrid` is the `@tool`-style self-previewing node from [Tool scripts](#tool-scripts-and-editor-integration).

### main_menu.tscn — the main menu

```
MainMenu (Node2D) — scripts/menu/main_menu.gd
├── ForestBackground (Node2D) — scripts/rooms/window_background.gd
│   └── (8 parallax sprites created at runtime via _build_layers)
├── DimOverlay (ColorRect)    → dark semi-transparent overlay
├── LoadingScreen (ColorRect) → z_index 100, contains SubViewportContainer
├── MenuCharacter (Node2D) — scripts/menu/menu_character.gd
│   └── (sprite + timer created at runtime via walk_in())
└── UILayer (CanvasLayer, layer = 10)
    └── ButtonContainer (VBoxContainer)
        ├── TitleLabel — "Relax Room"
        ├── Spacer
        ├── NewGameBtn
        ├── LoadGameBtn
        ├── OptionsBtn
        ├── ProfileBtn
        └── QuitBtn
```

**Startup sequence:**

1. Loading screen visible (alpha = 1.0)
2. After 0.4 s, loading screen fades out (0.5 s)
3. `MenuCharacter.walk_in()` — walk animation from (-100, 530) to (640, 530)
4. Buttons fade in (0.3 s)

The staged timing runs on awaited SceneTree timers and tweens — with the pause caveats from [Process modes](#process-modes-pausing-and-priority) in mind: menu timers deliberately keep `process_always = true` since the menu itself is never "paused".

### Characters — instantiable scenes

All characters share one structure (via scene inheritance from a common base — the pattern from [Scene ownership and inheritance](#scene-ownership-and-inheritance)):

```
CharacterBody2D — scripts/rooms/character_controller.gd
├── CollisionShape2D
│   └── CapsuleShape2D (radius 16, height 56)
└── AnimatedSprite2D
    ├── texture_filter: NEAREST
    ├── scale: (3, 3) or (4, 4)
    └── SpriteFrames (13+ animations)
```

**Runtime character swap** (`room_base.gd`, lines 25-42) — a textbook instance-replacement sequence:

```gdscript
func _on_character_changed(character_id: String) -> void:
	var scene := load(scene_path) as PackedScene
	var old_pos := character_node.position        # preserve placement…
	var old_scale := character_node.scale         # …and size
	character_node.queue_free()                   # deferred removal of the old one
	var new_char := scene.instantiate()           # build the replacement
	new_char.position = old_pos                   # configure BEFORE adding
	new_char.scale = old_scale
	call_deferred("add_child", new_char)          # deferred add — handler is signal-driven
```

Every line maps to a rule from this module: `queue_free` (not `free`) because the swap is triggered from a `SignalBus` handler with the emission still on the stack; configuration happens in the orphan window before `add_child`; and the add itself is deferred because tree mutation from a signal callback is exactly the case [call_deferred exists for](#packedscene-and-instancing).

### Furniture — scenes without scripts

Beds, windows and doors are simple scenes with no logic:

```
bed_black_1 (StaticBody2D)
├── CollisionPolygon2D    → 8-point polygon for collision
└── Sprite2D              → sprite_bed_black1.png
```

These scenes live in `scenes/room/`, but in the running game decorations are created at runtime by `room_base.gd`, loading textures directly from the `decorations.json` catalog. The furniture `.tscn` files serve as reference/prototype — an honest example of the "scene as documentation" role: the tree encodes the intended collision setup even where the runtime path is data-driven.

### UI panels — built programmatically

The settings, profile and deco panels have no elaborate `.tscn` layouts. They are `PanelContainer`s constructed entirely in GDScript, following the [builder pattern shown earlier](#creating-and-removing-nodes-at-runtime):

```gdscript
# Simplified from the panels' shared pattern:
var panel := PanelContainer.new()
var margin := MarginContainer.new()
margin.add_theme_constant_override("margin_left", 12)
margin.add_theme_constant_override("margin_top", 8)
panel.add_child(margin)

var vbox := VBoxContainer.new()
vbox.add_theme_constant_override("separation", 8)
margin.add_child(vbox)

var label := Label.new()
label.text = "Settings"
label.add_theme_font_size_override("font_size", 13)
vbox.add_child(label)
```

**Why build UI in code?** For small panels with few controls, code is faster to write and easier to diff-review than a dedicated `.tscn`. For complex UI (many buttons, nested layouts), a `.tscn` wins — visual editing, designer access, anchor preview. The team's threshold: roughly a dozen controls, or any layout a non-programmer needs to touch.

### auth_screen.tscn — minimal layout

The authentication screen has a nearly empty `.tscn` (just a `Control` root) and builds ALL of its UI in code, in `auth_screen.gd`'s `_ready()`:

```
AuthScreen (Control) → z_index 100, fullscreen
  └── (all content — login form, registration, guest flow — created in _ready())
```

`z_index = 100` keeps the auth screen above the game world — and per the [draw-order precedence rules](#canvaslayer-and-draw-order), it works only because the screen shares the world's canvas layer; had it lived under a lower `CanvasLayer`, no z-index would have saved it. (Persistence and the account flow behind this screen: [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md).)

### The SignalBus cleanup audit

The project's signal audit found and fixed three cases (N-Q3, N-Q5, N-AR7) of the exact bug class described in [Communication patterns](#communication-patterns): scripts connecting to `SignalBus` (an autoload that outlives every scene) without disconnecting in `_exit_tree`. The node died, the bus kept a connection to a freed object, and the next emission errored. The pattern now enforced across the codebase:

```gdscript
# From room_base.gd — SignalBus cleanup, mandatory for every bus listener.
func _exit_tree() -> void:
	if SignalBus.character_changed.is_connected(_on_character_changed):
		SignalBus.character_changed.disconnect(_on_character_changed)
	if SignalBus.decoration_placed.is_connected(_on_decoration_placed):
		SignalBus.decoration_placed.disconnect(_on_decoration_placed)
```

When it is NOT needed: parent→child connections inside one scene (`$Timer.timeout.connect(...)`) — Godot cleans those up when the nodes are freed together. The rule targets *asymmetric lifetimes*: whenever the emitter outlives the listener, the listener disconnects itself on exit. See [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) for the full audit checklist.

### Concept map-back: Module 02 in the codebase

A closing index for revision — each core concept of this module, and where the Relax Room project exercises it:

| Module 02 concept | Where Relax Room uses it |
|---|---|
| Tree order as draw order | `main.tscn` dock order: background → room → grid → UILayer |
| CanvasLayer strata | `UILayer` (10) for HUD; modals/auth at 100 |
| `_ready` vs `_enter_tree` | Controllers cache `@onready` children; bus subscriptions in `_ready`, cleanup in `_exit_tree` |
| Deferred tree mutation | Character swap: `queue_free` + `call_deferred("add_child", …)` from a signal handler |
| PackedScene instancing | Characters instantiated from the roster; decorations spawned from catalog data |
| Scene inheritance | `character_base.tscn` → per-character variants overriding `SpriteFrames`/scale |
| Runtime node construction | Settings/profile/deco panels, auth screen UI, parallax layers, menu character |
| Empty runtime containers | `Room/Decorations` — structure reserved for code-spawned children |
| Call down, signal up | `main.gd` wires character/HUD/room; children never reach upward |
| Signal bus + `_exit_tree` discipline | `SignalBus` autoload; audit fixes N-Q3, N-Q5, N-AR7 |
| `mouse_filter` policy | `DropZone` full-rect Control on PASS to coexist with HUD buttons |
| Collision layers/masks | Walls layer 1, decorations layer 2; character masks 3 (or 1 in edit mode) |
| Y-sort for depth | `Room` sorting `Decorations` and `Character` as siblings |
| Tool-style editor aids | `RoomGrid` drawing its 64 px grid only in edit mode |

If you can point at each row in the running project — Remote tab open, this file beside it — Module 02 is done. [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) continues from exactly this table.

---

## Best practices

The consolidated production checklist. Each item links back to the section with the reasoning.

**Structure and composition**

1. **One scene, one responsibility.** Every `.tscn` answers to one sentence; composition scenes wire features together. ([Scene organization](#scene-organization-for-real-projects))
2. **Design scenes with no external dependencies.** A scene must run standalone under F6; anything it needs arrives via `@export`, `setup()`, or signals. ([Communication patterns](#communication-patterns))
3. **Prefer component nodes to inheritance towers.** Inheritance depth ≤ 2; cross-cutting capabilities become child components. ([Composition over inheritance](#composition-over-inheritance))
4. **Keep scene inheritance for same-structure variants only** (character roster, furniture families), one level deep. ([Scene ownership and inheritance](#scene-ownership-and-inheritance))

**Lifecycle and references**

5. **`@onready` + `$` for direct children, `%` for deep scene-internal nodes, `@export` across scenes.** Never `../..` paths. ([Node identity and lookup](#node-identity-and-lookup))
6. **`_ready` configures the scene itself; world interaction waits for an explicit `setup()`/`activate()` call.** ([Node lifecycle in depth](#node-lifecycle-in-depth))
7. **`queue_free()`, not `free()`** — always, unless you can prove nothing is iterating. Freeing is deferred for a reason. ([Creating and removing nodes](#creating-and-removing-nodes-at-runtime))
8. **Defer tree mutations from callbacks**: `add_child.call_deferred(...)`, `set_deferred("disabled", ...)`, or `await get_tree().process_frame`. ([PackedScene and instancing](#packedscene-and-instancing))
9. **Pair every `_exit_tree` teardown with `_enter_tree` setup** — reparenting triggers both; destruction-only logic checks `is_queued_for_deletion()` or uses `NOTIFICATION_PREDELETE`. ([Notifications](#notifications))

**Communication**

10. **Call down, signal up — no exceptions.** Siblings talk through their composing parent; global facts go through the SignalBus. ([Communication patterns](#communication-patterns))
11. **Disconnect from autoload signals in `_exit_tree`.** Asymmetric lifetimes (bus outlives listener) are the crash factory; the Relax Room audit (N-Q3, N-Q5, N-AR7) proves it. ([Case study](#case-study-relax-room-scene-architecture))
12. **Signals are past-tense facts** (`decoration_placed`), never remote commands (`update_hud`). ([Communication patterns](#communication-patterns))
13. **Document groups centrally** — a constants file with `const ENEMIES := &"enemies"` plus the expected member API. ([Groups in production](#groups-in-production))

**Rendering and processing**

14. **All UI under a `CanvasLayer`**; layers for coarse strata (0 world / 10 HUD / 100 modal), `z_index` for fine ordering within a stratum. ([CanvasLayer and draw order](#canvaslayer-and-draw-order))
15. **Set pause policy per branch, not per leaf** — one `process_mode` on the branch root, `INHERIT` below; SceneTree timers need explicit `process_always = false` to pause. ([Process modes](#process-modes-pausing-and-priority))
16. **Name collision layers in Project Settings; never mask `-1`.** ([The 2D node families](#the-2d-node-families))

**Tooling and hygiene**

17. **Watch the orphan monitor during development**; every deliberate orphan has an owner in code. ([Orphan nodes and leak detection](#orphan-nodes-and-leak-detection))
18. **Reusable scenes validate themselves** with `_get_configuration_warnings()`. ([Tool scripts](#tool-scripts-and-editor-integration))
19. **snake_case files, PascalCase nodes, feature-based folders** — mechanical conventions, enforced in review. ([Scene organization](#scene-organization-for-real-projects))

---

## Common errors & troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Invalid get index 'position' (on base: 'null instance')` in `_init` or a plain `var` initializer | `$Child` / `get_node` before the node entered the tree — plain initializers run at `_init` time | Move the lookup to `@onready` or `_ready` ([lifecycle](#node-lifecycle-in-depth)) |
| `get_tree()` returns `null` | Node not inside the tree (before `add_child`, or after `remove_child`) | Guard with `is_inside_tree()`; do tree work in `_enter_tree`/`_ready` |
| "Attempt to call function … on a previously freed instance" | Stored reference used after `free`/`queue_free`; or `free()` mid-signal-emission | Use `queue_free()`; owners of caches clear them on the node's `tree_exiting`; check `is_instance_valid` only as a last resort |
| Error "Parent node is busy setting up children / can't change state while flushing queries" | `add_child`/`remove_child`/`disabled` toggled inside a physics callback or physics-driven signal | `add_child.call_deferred(...)`, `set_deferred("disabled", ...)`, or `CONNECT_DEFERRED` on the signal |
| `_ready` never fires on a re-added node | `_ready` runs once per node by default | `request_ready()` before the next `add_child`, or move per-spawn logic to `_enter_tree` |
| Child data missing inside child's `_ready` | Parent injected dependencies too late — children ready before the parent finishes | Inject before `add_child` for runtime instances; use explicit `setup()` for editor-placed children |
| Pause menu frozen along with the game | Menu branch left on `PROCESS_MODE_INHERIT` | Set the menu branch root to `PROCESS_MODE_ALWAYS` ([process modes](#process-modes-pausing-and-priority)) |
| Timed gameplay event fires while paused | `create_timer()` defaults to `process_always = true` | Pass `false` as the second argument, or use a `Timer` node under a pausable branch |
| Buttons/HUD stopped responding to clicks | A full-screen `Control` above them with `mouse_filter = STOP` (often an overlay or drop zone) | Set the overlay to `MOUSE_FILTER_PASS` or `IGNORE` |
| Popup renders below the HUD despite huge `z_index` | Emitter and HUD are in different `CanvasLayer`s — z never crosses layers | Move the popup to a higher `layer` (e.g. 100), keep z for intra-layer ordering |
| UI zooms/pans with the game camera | UI not under a `CanvasLayer` | Parent all UI to a `CanvasLayer` (layer ≥ 10 by convention) |
| Node exists in Remote tree but does nothing (no `_process`, no input) | Processing disabled: `PROCESS_MODE_DISABLED` inherited, or `set_process(false)` | Audit `process_mode` up the ancestor chain; re-enable |
| "Cyclic dependency" on script load | Two scripts `preload` each other (directly or via scenes) | Switch one side to `load()` at call time or extract shared code into a third script |
| `instantiate()` crashes with argument error | Scene script's `_init` has parameters without defaults | Give every `_init` parameter a default value |
| Runtime-added nodes vanish when the scene is saved (tool code / level editor) | Nodes lack `owner`, so `pack()` skips them | Set `owner = edited_scene_root` (editor) or the branch root before `pack()` |
| Editor crashes or scenes corrupt after adding `@tool` | Gameplay logic (freeing, spawning, saving) executing in-editor | Gate with `Engine.is_editor_hint()`; develop first without `@tool` |
| "Orphan Nodes" monitor climbs during play | Instantiated nodes never added (early return) or removed without `free` | Audit spawn paths; every `remove_child` needs a stored owner or a `free` plan |
| Signal handler runs twice per event | Connected in both editor and code, or reconnected without guard | `if not sig.is_connected(cb): sig.connect(cb)`; pick editor *or* code wiring per signal |
| Next emission errors after a listener died | Listener connected to an autoload signal and never disconnected | Disconnect in `_exit_tree` — the SignalBus rule ([case study](#case-study-relax-room-scene-architecture)) |
| Child appears sheared/skewed when rotated | Non-uniform `scale` on an ancestor combining with child rotation | Keep ancestor scales uniform; apply non-uniform scale at the leaf that needs it |
| Object "teleports" by a fixed offset on drag | Local/global coordinate space mix-up | Convert explicitly with `to_local`/`to_global`; name variables by space ([2D families](#the-2d-node-families)) |
| Character pops in front of/behind furniture too early | Y-sort compares node *origins*, and sprite origins sit at the visual center | Offset sprites so origins are at the feet/floor-contact point ([y-sorting](#canvaslayer-and-draw-order)) |
| Character never sorts against decorations at all | Character and decorations are not under the same y-sorted parent | Make them siblings under one `y_sort_enabled` container |
| `%NodeName` fails with "Node not found" | Unique flag not set, or caller belongs to a different scene (different owner) | Enable "Access as Unique Name" on the node; `%` only resolves within the same scene |
| "Signal is not connected" error on disconnect | Disconnecting a connection that was never made (or already auto-removed) | Guard with `is_connected()` before `disconnect()` |
| Animation plays on a despawned/freed object's timer | `SceneTreeTimer` awaits survive the node | Use a child `Timer` node for node-bound waits ([Timer table](#the-2d-node-families)) |
| Camera zoom behaves inverted after a Godot 3 port | Godot 4 reversed zoom semantics: bigger = closer | Use `zoom = Vector2(2, 2)` to magnify; audit ported values |
| `get_node("Decoration")` returns the wrong instance | Sibling name collision auto-renamed the second spawn (`Decoration2`) | Assign explicit deterministic names at spawn, or hold references instead of paths |
| Await after `queue_free` resumes on a dead object | Coroutine outlived the node (SceneTree timer or long await) | Keep awaited choreography within one lifetime scope; re-validate with `is_instance_valid` at resumption |
| Two "unrelated" scenes break together after edits | Editable-children overrides coupling parent to child internals | Replace repeated overrides with `@export` configuration on the child scene |

---

## Exercises

Work these in a scratch project (`res://labs/` folder per lab). Each lab lists concrete acceptance criteria — treat them as the definition of done. Labs 1-3 are preserved (and expanded) from the original module.

### Lab 1 — Lifecycle tracer

Build a scene of 5 nested nodes (3 levels deep, at least two siblings). Attach a script to every node printing its name in `_init`, `_enter_tree`, `_ready` and `_exit_tree`. Run it, then remove and re-add the middle branch at runtime on a keypress.

**Acceptance criteria:**
- The printed order matches the prediction you wrote down *before* running (enter: parent-first; ready: children-first; exit: children-first).
- The re-added branch prints `_enter_tree` but **not** `_ready` — then, after you add `request_ready()`, it prints both.
- You can explain, in two sentences in a code comment, why `UILayer._enter_tree` precedes `Character._ready` in the module's example.

### Lab 2 — The free() race, reproduced and fixed

Create a scene where a `Timer.timeout` signal is connected to two handlers on different nodes; the first handler calls `free()` on the second handler's node. Observe the error. Fix it with `queue_free()` and verify both orderings of connections are safe.

**Acceptance criteria:**
- The `free()` version reliably produces a "previously freed instance" error with both connection orders (or you can explain why one order survives).
- The `queue_free()` version runs clean; `is_queued_for_deletion()` returns `true` inside the surviving handler.
- A comment documents *when* the actual free happens relative to the frame.

### Lab 3 — Runtime scene composition

Load three different `PackedScene`s (any small visual scenes), instantiate them in a 3×3 grid pattern, and connect a signal from each instance to one common callback that prints which instance fired.

**Acceptance criteria:**
- All 9 instances configure position **before** `add_child` (verify no first-frame flicker at origin).
- The common callback identifies the emitter via a bound argument, not `get_name()` parsing.
- Freeing the grid container with one `queue_free()` leaves the Orphan Nodes monitor at zero.

### Lab 4 — Path-proofing a scene

Take (or build) a scene where a script reaches a deep node via `get_node("Panel/Margin/VBox/Title")` and a sibling via `get_node("../HUD")`. Refactor: `%` unique name for the deep node, `@export` reference wired by the parent for the sibling.

**Acceptance criteria:**
- After the refactor, renaming `Margin` and moving `HUD` under a new wrapper node breaks **nothing** (run to prove it).
- The refactored scene runs standalone under F6 without errors (the exported reference is null-tolerant or asserted with a clear message).
- `grep -rn "\.\./" scripts/` over the lab returns zero hits.

### Lab 5 — Pause system with three policies

Build: a moving sprite (gameplay), an animated "PAUSED" banner (pause UI), and a wall-clock label updating every second (always-on). Wire a pause toggle on <kbd>Esc</kbd>.

**Acceptance criteria:**
- While paused: sprite stops, banner animates, clock keeps updating — using exactly one `process_mode` override per branch, everything else `INHERIT`.
- A `get_tree().create_timer(3.0)` "gameplay event" does **not** fire while paused (correct flag passed).
- Unpausing resumes the sprite with no position jump (hint: physics vs process delta).

### Lab 6 — Character swap, Relax Room style

Reimplement the case study's `_on_character_changed` flow with two character scenes of your own: a signal (from a button) triggers replacing the current character instance while preserving position and scale.

**Acceptance criteria:**
- The swap is triggered from a signal handler and produces zero errors/warnings — which forces `queue_free` + deferred `add_child`.
- Position and scale carry over exactly; the new instance's `_ready` runs after it enters the tree (prove with a print).
- Rapid-fire clicking the swap button (10+ times in a second) never crashes and never leaves two characters visible.

### Lab 7 — Component extraction

Start from a single script that makes a sprite (a) hover-glow, (b) despawn after 10 s, (c) emit a signal when clicked. Extract each capability into a reusable component node (`HoverGlowComponent`, `LifetimeComponent`, `ClickableComponent`) and attach all three to two *different* host scenes.

**Acceptance criteria:**
- The host scenes contain no capability code — only composition and wiring.
- Each component works when attached alone, and warns (configuration warning or `push_warning`) when its host lacks what it needs.
- Adding a third host takes under one minute and zero new code.

### Lab 8 — Leak hunt

Write a deliberately leaky spawner: 20% of spawned nodes take an early-return path that skips `add_child`; another 20% are `remove_child`ed into nowhere. Then instrument and fix it.

**Acceptance criteria:**
- A debug hotkey calling `Node.print_orphan_nodes()` shows the leaks accumulating; the Orphan Nodes monitor corroborates.
- After the fix (free-on-early-out + an owning pool array for the removed ones), the monitor stays flat over 1,000 spawns.
- A comment states the project's ownership rule for deliberate orphans in one sentence.

### Lab 9 — Theme broadcast three ways

Implement "the theme changed, everything recolors" three times over the same scene (a room with 6+ recolorable nodes scattered across branches): (a) via `propagate_call` from the room root, (b) via a `"themed"` group broadcast, (c) via a `SignalBus.theme_changed` signal.

**Acceptance criteria:**
- All three implementations produce identical visual results from the same trigger button.
- A short comment block ranks them for this use case and states *when each would win* (structure-scoped vs role-scoped vs subscription-scoped — the decision table from [Communication patterns](#communication-patterns)).
- The signal-bus variant survives a scene change without errors (listeners disconnect in `_exit_tree`) — prove it by switching scenes twice.

### Lab 10 — Modal stack

Build the modal manager from [CanvasLayer and draw order](#canvaslayer-and-draw-order): an autoload `CanvasLayer` (layer 100) with `push_modal()`, a dim overlay, and world pause. Test it with two stacked popups (a settings panel that opens an "unsaved changes" confirm on top).

**Acceptance criteria:**
- While any modal is open: the world is paused, clicks outside the modal hit the dim shield (not the game), and the modals themselves stay fully interactive (`PROCESS_MODE_ALWAYS`).
- Closing modals in any order (top-first, bottom-first via code, or a scene change killing both) leaves the stack consistent and unpauses exactly when the last one dies — driven by `tree_exiting`, not by close buttons.
- The dim overlay fades with a tween that runs *while paused* (check the tween's pause behavior).

### Stretch goal A — Mini scene-spawner tool

Write a `@tool` script that, in the editor, maintains N instances of an `@export var scene: PackedScene` as children (adding/removing as N changes in the Inspector), with `_get_configuration_warnings()` reporting a missing scene. Persist correctly on save.

**Acceptance criteria:** changing N in the Inspector updates children live; saved `.tscn` contains exactly N instances (owner set correctly); the warning triangle appears if `scene` is empty; the script never runs spawn logic at runtime (editor-hint guarded).

### Stretch goal B — Signal bus with lifecycle audit

Build a `SignalBus` autoload plus a `BusAuditor` debug autoload that, on demand, lists every current bus connection (`get_signal_connection_list`) and flags connections whose target objects are freed or outside the tree.

**Acceptance criteria:** the auditor catches a deliberately-planted "listener freed without disconnecting" bug; after adding `_exit_tree` cleanup to the listener, the audit comes back clean across three scene changes.

### Self-check questions

1. In what order do `_init`, `_enter_tree` and `_ready` run across a parent and two children — and which of the three repeats on re-entry?
2. `queue_free` vs `free`: describe the exact scenario where `free` crashes and `queue_free` does not.
3. What does `PackedScene.instantiate()` return, and what state is the branch in before `add_child`?
4. When do you choose a group over a stored reference — and what does `get_first_node_in_group` return when the group is empty?
5. Why must a listener to an autoload signal disconnect in `_exit_tree`, while a `$Timer.timeout` connection needs no cleanup?
6. A popup with `z_index = 4096` renders under the HUD. What is wrong, and what is the fix?
7. Which callback pair must stay symmetric for `reparent()` to be safe, and why?
8. Name the three broadcast mechanisms (structure, role, subscription) and the selection criterion for each.
9. What does `owner` control during `PackedScene.pack()`, and what happens to runtime-added nodes that never received one?
10. Your `@tool` script's spawned preview nodes appear in the editor but not in the saved file — what is missing, and which notification pair could strip/rebuild them around saves?
11. In what order are draw-order conflicts resolved between `CanvasLayer.layer`, `z_index` and sibling order — and which of the three can y-sort override?

---

## Further reading

**Official documentation** (verify against your pinned 4.5 docs where behavior is version-sensitive):

- [Nodes and scene instances — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/scripting/nodes_and_scene_instances.html) — the canonical tutorial for `get_node`, `$`, `%`, runtime instancing and freeing; the source for this module's lookup rules.
- [Node — class reference](https://docs.godotengine.org/en/stable/classes/class_node.html) — the full API: lifecycle virtuals, `NOTIFICATION_*` constants, `ProcessMode`, groups, `reparent`, `request_ready`. Read the notification list once, end to end.
- [SceneTree — class reference](https://docs.godotengine.org/en/stable/classes/class_scenetree.html) — everything behind `get_tree()`: scene changes, timers, group calls with flags, quit handling.
- [PackedScene — class reference](https://docs.godotengine.org/en/stable/classes/class_packedscene.html) — `instantiate`, `pack`, `can_instantiate` and the ownership-based serialization rules.
- [Scene organization — Best practices](https://docs.godotengine.org/en/stable/tutorials/best_practices/scene_organization.html) — the "scenes with no dependencies" doctrine and the five dependency-injection techniques this module's communication section builds on.
- [Node communication (Godot community docs section on signals)](https://docs.godotengine.org/en/stable/getting_started/step_by_step/signals.html) — signals from first principles, editor and code connection flows.
- [Running code in the editor (@tool)](https://docs.godotengine.org/en/stable/tutorials/plugins/running_code_in_the_editor.html) — tool scripts, `Engine.is_editor_hint()`, configuration warnings, editor-safety rules.
- [Pausing games and process mode](https://docs.godotengine.org/en/stable/tutorials/scripting/pausing_games.html) — the pause negotiation, with diagrams.
- [CanvasLayer — class reference](https://docs.godotengine.org/en/stable/classes/class_canvaslayer.html) and [Canvas layers tutorial](https://docs.godotengine.org/en/stable/tutorials/2d/canvas_layers.html) — layer semantics and camera independence.
- [Nodes and scenes — Getting started](https://docs.godotengine.org/en/stable/getting_started/step_by_step/nodes_and_scenes.html) — the conceptual introduction; worth a re-read after this module to see how much the same page now says.
- [Groups — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/scripting/groups.html) — editor workflow for group assignment plus the SceneTree call/notify API.
- [2D coordinate systems and 2D transforms](https://docs.godotengine.org/en/stable/tutorials/2d/2d_transforms.html) — the canvas transform pipeline behind local/global positions and CanvasLayer independence.

**Community:**

- [KidsCanCode — Godot 4 Recipes: Node communication](https://kidscancode.org/godot_recipes/4.x/basics/node_communication/) — the clearest short statement of "call down, signal up", with the sibling-via-parent wiring example this module adapts.
- [GDQuest — best practices on signals](https://www.gdquest.com/tutorial/godot/best-practices/signals/) — when signals help, when they tangle (signal bubbling), and the measured cost of emission (~2,300 emissions/ms — stop worrying).
- [GDQuest — Node essentials](https://www.gdquest.com/) — free guides and the node-essentials cheatsheets; good flashcard material for the 2D family tour.

**Course cross-links:** previous: [GODOT_ENGINE_STUDY.md](GODOT_ENGINE_STUDY.md) · next: [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) · related: [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) (Module 13 — signal bus in depth), [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md) (transforms and y-sort applied), [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) (the full Relax Room tree) · index: [00-SYLLABUS.md](00-SYLLABUS.md), [00-GLOSSARY.md](00-GLOSSARY.md).

---

## Glossary

| Term | Definition |
|---|---|
| **Node** | The atomic building block: one object with a name, optional script, at most one parent, ordered children. |
| **Scene** | A saved branch of nodes (`.tscn`/`.scn`); Godot's unit of composition, reuse and testing. |
| **SceneTree** | The `MainLoop` object containing the active node tree; drives processing, physics, input and rendering. Reached via `get_tree()`. |
| **root (Window)** | The tree's root viewport; ancestor of autoloads and the current scene. |
| **current_scene** | The `SceneTree` property holding the main scene's root; swapped by `change_scene_to_*`. |
| **Autoload** | A scene/script registered in Project Settings, instanced under `root` before the main scene; survives scene changes. |
| **Tree order** | Parent-before-children, siblings in dock order; governs draw order, processing order and UI focus. |
| **`_init`** | GDScript constructor; runs at `new()`/`instantiate()`, before any parent or tree exists. |
| **`_enter_tree`** | Callback on every tree entry; propagates parent-first (top-down). |
| **`_ready`** | Callback when the node's entire subtree has entered; propagates children-first (bottom-up); once per node unless `request_ready()`. |
| **`_exit_tree`** | Callback on every tree exit (including reparenting); children-first. |
| **`@onready`** | Annotation deferring a variable's initializer to just before `_ready` — the safe window for `$` lookups. |
| **Notification** | Low-level integer event (`NOTIFICATION_*`) delivered to `_notification()`; underlies all lifecycle callbacks. |
| **`NOTIFICATION_PREDELETE`** | The true destructor notification: last code to run before an object is freed. |
| **ProcessMode** | Per-node pause policy (`INHERIT`/`PAUSABLE`/`WHEN_PAUSED`/`ALWAYS`/`DISABLED`) negotiated against `SceneTree.paused`. |
| **process_priority** | Integer ordering of `_process` within a frame; lower runs earlier. |
| **NodePath** | A path of node names (`"Panel/Title"`, `"../Sibling"`, `"/root/Main"`) resolved by `get_node`. |
| **`$` / `%`** | Literal-path sugar for `get_node` / scene-unique-name lookup (requires `unique_name_in_owner`). |
| **PackedScene** | The `Resource` form of a saved scene; a factory whose `instantiate()` manufactures independent branches. |
| **instantiate()** | Builds the full node branch described by a `PackedScene`; contrast `ClassName.new()` (one bare node). |
| **owner** | The scene root a node was saved with; gates `pack()` serialization, `%` scope and `find_child(owned=true)`. |
| **Editable children** | Per-instance exposure of an instanced scene's internals; overrides stored in the parent scene. |
| **Scene inheritance** | A scene whose base is another scene; stores only deltas; base edits propagate. |
| **`queue_free()`** | Marks a branch for deletion at a safe end-of-frame point — the production default. |
| **`free()`** | Immediate destruction; unsafe while signals/physics still reference the node. |
| **`call_deferred` / `set_deferred`** | Queue a call/property-set for the end-of-frame flush; mandatory for tree/physics mutations from callbacks. |
| **`reparent()`** | Atomic move to a new parent, optionally preserving the global transform; fires exit+enter, not `_ready`. |
| **Orphan node** | A node alive in memory but outside the tree; deliberate (pools) or a leak — nodes are never reference-counted. |
| **Signal** | Typed, synchronous observer mechanism on objects; the "up" channel in *call down, signal up*. |
| **Signal bus** | An autoload declaring only signals, decoupling many-to-many, cross-scene events; see [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md). |
| **Group** | A `StringName` tag on nodes; queried/broadcast via `get_tree()` — identity by role, not by address. |
| **Component node** | A small child node encapsulating one reusable capability; the composition alternative to inheritance. |
| **CanvasLayer** | A node creating an independent 2D canvas with its own `layer` order and camera-independent transform. |
| **`@tool`** | Annotation making a script execute in the editor; paired with `Engine.is_editor_hint()` and configuration warnings. |
| **Viewport / SubViewport** | A render target and input-routing context; the root `Window` is one, and `SubViewport` nodes embed additional ones in the tree. |
| **Y-sort** | `CanvasItem.y_sort_enabled` — draws a container's children ordered by global Y for depth in top-down/isometric views. |
| **Instance ID** | Process-unique `int` from `get_instance_id()`; `instance_from_id()` resolves it or returns `null` — a reference that cannot dangle. |
| **Object pool** | Pre-instantiated, recycled set of scene instances held as deliberate orphans; pairs with `request_ready()`. |
| **Configuration warning** | Scene-dock warning produced by a `@tool` script's `_get_configuration_warnings()`; machine-checked scene wiring. |
| **Mediator** | The composing parent that wires sibling scenes together (signal→method), keeping the siblings mutually ignorant. |
| **SceneTreeTimer** | Nodeless one-shot timer from `get_tree().create_timer()`; survives its creator and ignores pause by default. |
| **`propagate_call()`** | Structure-scoped broadcast: invokes a method on a node and every descendant that defines it, children-first by default. |
| **`request_ready()`** | Re-arms a node's once-only `_ready` flag so the next tree entry fires it again — the pooling primitive. |

---

*Module 02 of the "Godot 4 in Production" course — Phase 1: Foundations. Previous: [GODOT_ENGINE_STUDY.md](GODOT_ENGINE_STUDY.md) · Next: [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md)*

