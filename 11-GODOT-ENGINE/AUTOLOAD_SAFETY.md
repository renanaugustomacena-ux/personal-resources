---
course: "Godot 4 in Production"
phase: "5 — Specialized modules"
module: "13"
title: "Autoload Safety — Singletons, Initialization Order and Thread Safety"
version: "Godot 4.5 / GDScript 2.0"
level: "Advanced"
prerequisites:
  - "GODOT_ENGINE_STUDY.md"
  - "SCENES_AND_NODES.md"
objectives:
  - "Explain exactly how Godot registers, instantiates and orders autoloads at startup"
  - "Design and defend an autoload dependency graph, applying two-phase init and init-time assertions"
  - "Recognize autoload abuse and select the right alternative (static members, Resources, DI, scene-scoped managers)"
  - "Implement a typed signal bus with a documented contract and debuggable signal flow"
  - "Write thread-safe background work with Thread, Mutex, Semaphore and WorkerThreadPool, bridging results via call_deferred"
  - "Control autoload state across scene reloads and pause states with reset protocols and process_mode"
  - "Refactor an autoload into a testable RefCounted core plus a thin node shell"
tags: [godot, autoload, singleton, threads, mutex, semaphore, call-deferred, signal-bus, initialization, worker-thread-pool, testing, lifecycle]
---

# Autoload Safety — Singletons, Initialization Order and Thread Safety — Complete Guide

> **Module 13** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Godot Engine Study](GODOT_ENGINE_STUDY.md), [Scenes and Nodes](SCENES_AND_NODES.md) · Recommended: [Project Deep Dive](PROJECT_DEEP_DIVE.md) for the Relax Room architecture referenced throughout.
>
> By the end of this module you will be able to:
> 1. Describe the full autoload startup sequence — `_init` → `_enter_tree` → `_ready`, one autoload at a time, in Project Settings list order, all before the main scene exists.
> 2. Read and hand-edit the `[autoload]` section of `project.godot`, including the meaning of the `*` prefix.
> 3. Draw the dependency graph of the Relax Room 8-autoload chain and predict exactly what breaks under any reordering.
> 4. Apply two-phase initialization, init-time assertions and an `InitGuard` pattern to make startup failures loud, early and diagnosable.
> 5. Argue both sides of the "autoloads considered harmful" debate and justify, per system, whether it belongs in global scope.
> 6. Move blocking work (SQLite writes, file IO, HTTP) off the main thread safely, using `Mutex`-guarded queues and `call_deferred` hand-offs, without ever touching the scene tree from a worker thread.
> 7. Keep autoload state sane across `reload_current_scene()`, pausing, and application quit — including a save-on-close handler for `NOTIFICATION_WM_CLOSE_REQUEST`.
>
> **Estimated time:** 6-8 hours reading · 4-6 hours labs · **Level:** Advanced

## Guiding ideas

1. **An autoload is not magic — it is a plain `Node` parented under `/root` before your main scene loads.** Everything else follows from that.
2. **Autoload = global mutable state. Every new autoload is a coupling point; use sparingly and document why it exists.**
3. **Initialization order is the Project Settings list order, top to bottom — not alphabetical.** Depend only on autoloads listed *above* you, and assert it.
4. **Autoloads are not thread-safe by default.** The main thread owns the scene tree; worker threads talk back only through `call_deferred` / `set_deferred`.
5. **Fail at startup, not at minute 40.** Init-time assertions and explicit two-phase init turn silent corruption into a red line in the debugger.
6. **Autoloads persist across scene changes and reloads.** Design an explicit `reset()` protocol or state will leak between sessions.

## Concept map

```
                       ┌────────────────────────────────────────┐
                       │      AUTOLOAD SAFETY (Module 13)       │
                       └───────────────────┬────────────────────┘
                                           │
        ┌──────────────────┬───────────────┼────────────────┬──────────────────┐
        │                  │               │                │                  │
┌───────▼───────┐  ┌───────▼───────┐ ┌─────▼──────┐ ┌───────▼───────┐ ┌────────▼────────┐
│ WHAT THEY ARE │  │  INIT ORDER   │ │ DESIGN &   │ │ THREAD SAFETY │ │   LIFECYCLE     │
│               │  │               │ │ ALTERNATIVES│ │               │ │                 │
│ /root children│  │ list order    │ │ abuse signs│ │ main thread   │ │ scene reload    │
│ before main   │  │ _init/_enter/ │ │ static var │ │ owns tree     │ │ (they persist!) │
│ scene         │  │ _ready chain  │ │ Resources  │ │ Thread/Mutex/ │ │ pausing &       │
│ [autoload] in │  │ two-phase init│ │ DI, scene- │ │ Semaphore     │ │ process_mode    │
│ project.godot │  │ assertions    │ │ scoped mgrs│ │ WorkerThread- │ │ reset() protocol│
│ * = enabled   │  │ InitGuard     │ │ service    │ │ Pool          │ │ exit cleanup    │
│ name access   │  │ dependency    │ │ locator    │ │ call_deferred │ │ WM_CLOSE_REQUEST│
│ vs get_node   │  │ graph         │ │ signal bus │ │ bridge        │ │ weakref caches  │
└───────┬───────┘  └───────┬───────┘ └─────┬──────┘ └───────┬───────┘ └────────┬────────┘
        │                  │               │                │                  │
        └──────────────────┴───────┬───────┴────────────────┴──────────────────┘
                                   │
                   ┌───────────────▼─────────────────┐
                   │  CASE STUDY: RELAX ROOM         │
                   │  SignalBus → AppLogger →        │
                   │  LocalDatabase → AuthManager →  │
                   │  GameManager → SaveManager →    │
                   │  AudioManager → PerformanceMgr  │
                   │  (8 autoloads, 31 signals)      │
                   └───────────────┬─────────────────┘
                                   │
                   ┌───────────────▼─────────────────┐
                   │  TESTABILITY                    │
                   │  RefCounted core + thin shell   │
                   │  GUT / GdUnit4 doubles          │
                   └─────────────────────────────────┘
```

## Table of contents

1. [Overview: What Autoloads Really Are](#1-overview-what-autoloads-really-are)
2. [Anatomy of the autoload Section and Access Patterns](#2-anatomy-of-the-autoload-section-and-access-patterns)
3. [Initialization Order Deep Dive](#3-initialization-order-deep-dive)
4. [Case Study: The Relax Room Autoload Chain](#4-case-study-the-relax-room-autoload-chain)
5. [Explicit Initialization Patterns](#5-explicit-initialization-patterns)
6. [The Case Against Autoload Abuse](#6-the-case-against-autoload-abuse)
7. [Alternatives to Autoloads, Compared](#7-alternatives-to-autoloads-compared)
8. [The Signal Bus Pattern Done Safely](#8-the-signal-bus-pattern-done-safely)
9. [Godot's Threading Model](#9-godots-threading-model)
10. [Thread, Mutex and Semaphore in Practice](#10-thread-mutex-and-semaphore-in-practice)
11. [call_deferred and set_deferred: The Safe Bridge](#11-call_deferred-and-set_deferred-the-safe-bridge)
12. [WorkerThreadPool and Background Work in a Companion App](#12-workerthreadpool-and-background-work-in-a-companion-app)
13. [Async Without Threads: await and Coroutines](#13-async-without-threads-await-and-coroutines)
14. [Autoloads and Scene Reload](#14-autoloads-and-scene-reload)
15. [Autoloads and Pausing](#15-autoloads-and-pausing)
16. [Testing Autoload-Heavy Codebases](#16-testing-autoload-heavy-codebases)
17. [Memory and Lifecycle](#17-memory-and-lifecycle)
18. [Best practices](#best-practices)
19. [Common errors & troubleshooting](#common-errors--troubleshooting)
20. [Exercises](#exercises)
21. [Further reading](#further-reading)
22. [Glossary](#glossary)

---

## 1. Overview: What Autoloads Really Are

Every Godot project that grows beyond a prototype eventually reaches the same question: *where do I put the things that must exist everywhere, all the time?* The music that keeps playing across scene changes. The logger that must capture the very first error. The database connection that every panel reads from. Godot's answer is the **autoload** — and it is simultaneously the most convenient and the most dangerous feature in the engine's scripting toolbox.

This module is called "Autoload Safety" for a reason. Autoloads are not hard to *use*; they are hard to use *without slowly poisoning your architecture*. The failure modes are not dramatic crashes on day one — they are null references at startup six months in, state that leaks between play sessions, save files written from the wrong thread, and a codebase where "who can touch this variable?" has the answer "literally everyone."

### 1.1 The mechanical truth

Strip away the terminology and an autoload is exactly this:

> **An autoload is a `Node` (or the root of an instantiated scene) that the engine creates and adds as a child of the root `Window` (`/root`) during startup, *before* the main scene is instantiated, and never removes until the application quits.**

That single sentence contains almost everything that matters in this module:

- **"a Node"** — autoloads participate in the scene tree like any other node. They receive `_enter_tree()`, `_ready()`, `_process()`, `_notification()`. They can own children, timers, tweens. They are *not* a special engine object.
- **"child of the root Window"** — they live at a stable, well-known path: `/root/SignalBus`, `/root/SaveManager`. The root's children are: all autoloads first (in registration order), then the current scene as the *last* child.
- **"before the main scene"** — by the time any node of your main scene runs `_ready()`, every autoload has already completed its own `_ready()`. This is the ordering guarantee your gameplay code silently relies on.
- **"never removed until quit"** — scene changes, `reload_current_scene()`, going back to the main menu: none of these touch autoloads. Their state persists. This is their superpower and their curse (Section 14 and 17).

> ⚠️ **Pitfall** — Never call `free()` or `queue_free()` on an autoload at runtime. The engine assumes autoloads exist for the process lifetime; freeing one leaves a dangling global binding and the official documentation warns the engine will crash. If you need to "turn off" an autoload, give it an `enabled` flag or a `stop()` method — do not destroy the node.

### 1.2 "Singleton" is a nickname, not a guarantee

The Godot community (and the Project Settings UI itself) calls autoloads "singletons," but be precise about what that means, because it is *weaker* than the GoF Singleton pattern you know from OOP theory:

| Property | Classic Singleton (GoF) | Godot autoload |
|---|---|---|
| Single instance enforced by the class | Yes — private constructor, static accessor | **No** — nothing stops `SignalBus.new()` or instantiating the scene again |
| Global access point | Yes (static `get_instance()`) | Yes (registered global name) |
| Lazy construction | Usually (created on first access) | **No** — constructed eagerly at startup |
| Lifetime | Process lifetime | Process lifetime (until `SceneTree` teardown) |
| Subclassable / replaceable | Painful | Trivially — it's just a node with a script |

The official docs put it plainly: an autoload is *not necessarily* a singleton — "autoload" describes an automatic loading mechanism, not an instantiation constraint. Nothing prevents a colleague from writing `var second_bus := SignalBus.new()` (where `SignalBus` here would be a `class_name`, not the global) and wiring half the UI to a private copy of your event bus. If true single-instance semantics matter, you enforce them yourself:

```gdscript
# autoloads/signal_bus.gd
extends Node
## Global event bus. MUST exist exactly once, as the /root/SignalBus autoload.

func _enter_tree() -> void:
    # Defensive single-instance check: the registered autoload is always
    # the node at /root/SignalBus. If *we* are not that node, someone
    # instantiated this script manually — refuse to exist.
    var registered := get_node_or_null("/root/SignalBus")
    if registered != null and registered != self:
        push_error("Duplicate SignalBus instantiated manually. Use the autoload.")
        queue_free()
```

This guard is cheap and has caught real bugs in team projects: a `.tscn` accidentally saved with an embedded manager instance, a test scene that instanced a manager "temporarily" and shipped that way.

### 1.3 Autoload scripts vs autoload scenes

The Project Settings dialog accepts two kinds of paths, and the difference matters more than it looks:

**Script autoload (`.gd`)** — Godot creates a plain `Node`, attaches your script to it, names the node after your autoload entry. Your script must therefore `extends Node` (or a `Node` subclass). If you write `extends RefCounted` in an autoload script, registration fails: the engine needs a node it can parent under root.

**Scene autoload (`.tscn`)** — Godot instantiates the whole `PackedScene` and adds its *root* under `/root` with the autoload name. This is the right choice when the manager genuinely needs a node subtree: an `AudioManager` that owns a pool of `AudioStreamPlayer` children, a debug overlay with a `CanvasLayer` and labels, a manager that wants pre-configured `Timer` children set up visually in the editor.

```text
Script autoload:                     Scene autoload:
/root                                /root
 └─ AudioManager (Node + script)      └─ AudioManager (scene root + script)
                                          ├─ MusicPlayerA (AudioStreamPlayer)
                                          ├─ MusicPlayerB (AudioStreamPlayer)
                                          ├─ SfxPool (Node)
                                          │   ├─ Sfx1 (AudioStreamPlayer)
                                          │   └─ Sfx2 (AudioStreamPlayer)
                                          └─ FadeTimer (Timer)
```

Relax Room's `AudioManager` is exactly this second case: crossfading between two music players requires two `AudioStreamPlayer` nodes and a tween — a scene autoload keeps that wiring declarative instead of building it in `_ready()`.

> ✅ **Best practice** — Default to script autoloads. Promote to a scene autoload only when the manager needs a real node subtree. A scene autoload with a single root node and no children is just a script autoload with an extra file to maintain.

### 1.4 Where autoloads sit in the tree — and why the order of `/root`'s children matters

Run any project and evaluate `get_tree().root.get_children()` — for Relax Room you would see:

```text
/root (Window)
 ├─ SignalBus            ← autoload #1
 ├─ AppLogger            ← autoload #2
 ├─ LocalDatabase        ← autoload #3
 ├─ AuthManager          ← autoload #4
 ├─ GameManager          ← autoload #5
 ├─ SaveManager          ← autoload #6
 ├─ AudioManager         ← autoload #7
 ├─ PerformanceManager   ← autoload #8
 └─ Main                 ← current scene (always LAST child of root)
```

Two practical consequences:

1. **`get_tree().current_scene` is the last child of root.** Code that iterates `root.get_children()` and assumes "everything here is a gameplay scene" will happily iterate your managers. Filter explicitly.
2. **Tree order = processing order.** `_process()` and `_physics_process()` run in tree order, so all autoloads process *before* the current scene each frame (for the default process priority). If `PerformanceManager` samples FPS in `_process()`, it observes the frame state *before* the main scene's processing of that frame — usually fine, occasionally surprising.

### 1.5 What this module builds toward

The module walks a deliberate arc:

- **Sections 2-5** make startup deterministic: registration anatomy, exact init order, the Relax Room chain as a worked dependency graph, and patterns (two-phase init, assertions, `InitGuard`) that convert "it usually works" into "it provably works or fails loudly."
- **Sections 6-8** are architectural judgment: when globals hurt, what the alternatives cost, and how to run a signal bus without drowning in signal spaghetti.
- **Sections 9-13** are concurrency: the threading model, the primitives, the `call_deferred` bridge, `WorkerThreadPool`, and the await-based alternative that avoids threads entirely.
- **Sections 14-17** are lifecycle: reload semantics, pausing, testing seams, and memory hygiene up to the final save-on-quit handler.

Keep the Relax Room chain in your head throughout. It is a real, production-shaped example: eight autoloads is *a lot* — near the upper bound of what a disciplined team should tolerate — and precisely because it is large, it demonstrates every failure mode this module teaches you to prevent.

---

## 2. Anatomy of the [autoload] Section and Access Patterns

### 2.1 Registering an autoload in the editor

The supported workflow is **Project → Project Settings → Globals → Autoload** (in earlier 4.x the tab was directly labeled "Autoload"; since 4.3 it lives under "Globals" together with Shader Globals). For each entry you provide:

- **Path** — a `res://` path to a `.gd` script or `.tscn` scene.
- **Node Name** — the global name. This becomes both the node's `name` under `/root` and (if enabled) a script-accessible global identifier. It must be a valid identifier and must not collide with an engine class name (`Input`, `Time`, `OS`…) or a `class_name` in your project.
- **Enable checkbox (the "singleton" flag)** — when checked, the name is registered as a global variable visible to every script. When unchecked, the node is still created and added under `/root`, but you must reach it with `get_node("/root/Name")`.
- **Up/down arrows** — reorder entries. This is not cosmetic: **list order is initialization order** (Section 3).

### 2.2 What actually lands in project.godot

The editor UI is a thin veneer over a plain-text section in `project.godot`. Relax Room's section looks like this:

```ini
[autoload]

SignalBus="*res://v1/scripts/autoload/signal_bus.gd"
AppLogger="*res://v1/scripts/autoload/app_logger.gd"
LocalDatabase="*res://v1/scripts/autoload/local_database.gd"
AuthManager="*res://v1/scripts/autoload/auth_manager.gd"
GameManager="*res://v1/scripts/autoload/game_manager.gd"
SaveManager="*res://v1/scripts/autoload/save_manager.gd"
AudioManager="*res://v1/scripts/autoload/audio_manager.gd"
PerformanceManager="*res://v1/scripts/systems/performance_manager.gd"
```

Dissecting one line — `SignalBus="*res://v1/scripts/autoload/signal_bus.gd"`:

| Fragment | Meaning |
|---|---|
| `SignalBus` | Global name; the node under `/root` will be named `SignalBus`. |
| `=` | Standard `ConfigFile` key/value assignment. |
| `*` | The **enable flag**. With `*`, the name is bound as a script-global variable (you can write `SignalBus.room_changed.emit(...)` anywhere). Without `*`, the node still loads but no global name is bound. |
| `res://...signal_bus.gd` | Script path → engine creates a `Node` and attaches this script. A `.tscn` path would instantiate the scene instead. |

Because it is plain text, the `[autoload]` section is *diffable and reviewable*. This has an underrated team consequence: **autoload order changes show up in code review.** A pull request that swaps two lines in `[autoload]` deserves the same scrutiny as a schema migration — it changes program startup semantics. In Relax Room's repository history, exactly one such diff (moving `SaveManager` above `GameManager` "to fix a null") was caught in review; it would have silently broken `SaveManager._ready()`'s read of `GameManager.current_room`.

> ⚠️ **Pitfall** — Merge conflicts in `project.godot` are a classic way to *lose an autoload* or *scramble order*. After resolving any conflict touching `[autoload]`, re-open Project Settings and verify the list visually, then run the project and watch the startup log. A dropped `SignalBus` line produces a wall of "Identifier not declared in the current scope" parse errors at startup — confusing until you know to check the section first.

### 2.3 Access patterns: four ways to reach an autoload

**A. Direct global name (the default):**

```gdscript
func _on_track_button_pressed(track_id: String) -> void:
    AudioManager.play_track(track_id)
    SignalBus.track_changed.emit(track_id)
```

Zero ceremony, full autocomplete, and — if the autoload script has no `class_name` — the identifier is resolved at parse time against the global registry. This is the pattern for 95% of call sites.

**B. `get_node()` with the absolute path:**

```gdscript
var audio := get_node("/root/AudioManager") as AudioManager
```

Equivalent at runtime, strictly worse ergonomically for normal code. It exists for three legitimate cases: (1) the enable flag is off, so no global name is bound; (2) code that must run where the global name is not available (tool scripts, some editor contexts); (3) *dynamic* lookup where the name arrives as data.

**C. `get_node_or_null()` — the defensive probe:**

```gdscript
var perf := get_node_or_null("/root/PerformanceManager")
if perf != null:
    perf.begin_sample("room_load")
```

This is the correct pattern in *library-ish* code that should degrade gracefully when a manager is absent — for example, a reusable UI panel you share between projects, or test scenes that boot without the full autoload roster. Direct global-name access hard-fails at parse time in a project where the autoload is not registered; `get_node_or_null` fails soft at runtime.

**D. Injected reference (the testable option):**

```gdscript
# room_controller.gd
var _save_manager: Node  # injected; defaults to the autoload

func _ready() -> void:
    if _save_manager == null:
        _save_manager = SaveManager  # fall back to the global
```

Here the class *prefers* an injected collaborator and only falls back to the global. Section 16 builds this into a full testing strategy.

| Pattern | Fails when missing | Testable | Use for |
|---|---|---|---|
| Global name | Parse/compile time | Poorly | Normal project code |
| `get_node("/root/X")` | Runtime error | Poorly | Disabled-flag or dynamic lookup |
| `get_node_or_null("/root/X")` | Soft (`null`) | Moderately | Optional/shared components |
| Injected + fallback | Never (injected in tests) | Well | Logic you unit-test |

### 2.4 The name collision rules

Three namespaces can collide with an autoload name, and Godot resolves them with different outcomes:

1. **Engine singletons** (`Input`, `OS`, `Time`, `Engine`, `RenderingServer`…) — you cannot register an autoload with these names; the editor rejects it.
2. **Global classes** (`class_name`) — an autoload and a `class_name` cannot share an identifier. A common convention conflict: you write `class_name SaveManager` inside the very script registered as the `SaveManager` autoload. Godot refuses this ("hides a global script class"). The convention that avoids it: autoload scripts get **no** `class_name`, or a distinct one (`class_name SaveManagerService` while the autoload is `SaveManager`). Relax Room uses the no-`class_name` convention for all eight.
3. **Local variables/parameters** — a local `var signal_bus` shadows nothing (different identifier case), but a local named exactly `SignalBus` *does* shadow the global inside that scope. The style guide answer: locals are `snake_case`, autoloads are `PascalCase`, so collisions never occur in idiomatic code.

> ✅ **Best practice** — Name autoloads `PascalCase`, file names `snake_case` (`SignalBus` ↔ `signal_bus.gd`), and give autoload scripts a `##` doc comment on line one stating: what the manager owns, which autoloads it may call (its *upstream* dependencies), and which signals it emits. That header is the manager's contract, and Section 4 shows how review enforces it.

### 2.5 Autoloads, tool scripts and the editor

A boundary that bites everyone exactly once: **project autoloads exist in the *running project*, not inside the editor process.** When the editor executes your `@tool` scripts (drawing gizmos, reacting to inspector edits), those scripts run in the *editor's* scene tree — where `/root` contains editor plumbing, not your manager roster. Consequences:

- A `@tool` script that references `SignalBus` or `SaveManager` by global name will error the moment its editor-side code path touches the identifier — the global resolves against a tree where the node does not exist.
- The defensive shape for scripts that live in both worlds is to gate every manager touch behind `Engine.is_editor_hint()`:

```gdscript
@tool
extends Node2D

func _ready() -> void:
    if Engine.is_editor_hint():
        return                      # editor context: no autoloads, draw preview only
    SignalBus.decoration_placed.connect(_on_placed)   # game context: safe
```

- Editor plugins get their own registration API: `EditorPlugin.add_autoload_singleton(name, path)` adds an entry to the project's `[autoload]` section when the plugin is enabled, and `remove_autoload_singleton(name)` removes it on disable. This is how addons like state-machine libraries or analytics SDKs install their managers without asking users to edit Project Settings by hand. If your team ships internal addons, prefer this API to documentation that says "now add three autoloads manually" — installations stop drifting.
- Reading the roster *as data* works in any context: `ProjectSettings.get_setting("autoload/SignalBus")` returns the `"*res://…"` string, and iterating `ProjectSettings.get_property_list()` for names starting with `autoload/` enumerates the whole section. Lab 1's CI check is built on exactly this.

> ⚠️ **Pitfall** — An autoload script marked `@tool` *does* get executed by the editor in some paths (e.g. when the editor loads it for documentation or a plugin instantiates it). Keep autoload `_init` side-effect-free (Section 3.3's rule pays off again) so an editor-context instantiation can never open files or spin threads from within the editor process.

---

## 3. Initialization Order Deep Dive

Autoload bugs cluster at two moments: startup and shutdown. This section makes startup fully deterministic in your head, because "I think `_ready` runs about here" is exactly the level of confidence that produces the 1-in-20-runs null crash.

### 3.1 The rule: list order, top to bottom

**Autoloads initialize in the order they appear in the Project Settings list (equivalently: line order in the `[autoload]` section), top to bottom.** You reorder them with the up/down arrows in the editor, and the engine adds them to the tree in exactly that sequence.

> ⚠️ **Pitfall** — A persistent myth (which appeared in the first edition of this very module) claims autoload order is *alphabetical by node name*. It is not, in any Godot 4.x release. The myth survives because many projects happen to add autoloads in near-alphabetical order, so the wrong mental model keeps predicting the right result — until the day someone registers `ZIndexManager` that `AppLogger` depends on, alphabetizes the list "for tidiness," and startup explodes. Order is *positional and intentional*. Treat the list as a topologically sorted dependency graph, not a phone book.

### 3.2 The precise startup sequence

When you launch a project (F5 / exported binary), the engine performs, in order:

1. Core initialization: servers (rendering, physics, audio), `ProjectSettings` loaded, the root `Window` created.
2. **For each autoload entry, top to bottom, one at a time:**
   a. The script is loaded (or the `PackedScene` instantiated).
   b. The object is constructed → **`_init()`** runs. The node is *not* in the tree yet; `get_tree()` returns `null` here.
   c. The node is added as a child of `/root` → **`_enter_tree()`** runs.
   d. Because the tree is already active and the node has no un-ready children (script autoloads) — or after its own scene's children ready (scene autoloads) — **`_ready()`** runs *immediately*, before the next autoload is even constructed.
3. Only after **all** autoloads have completed `_ready()`, the main scene is instantiated and added as the last child of `/root`; its nodes ready bottom-up as usual.

The crucial subtlety is 2d: autoloads do **not** all enter the tree and then ready as a batch. Each one completes its full `_init` → `_enter_tree` → `_ready` cycle *before the next autoload begins to exist*. For Relax Room:

```text
SignalBus._init
SignalBus._enter_tree
SignalBus._ready            ← SignalBus fully alive; AppLogger not yet constructed
AppLogger._init
AppLogger._enter_tree
AppLogger._ready            ← may freely use SignalBus
LocalDatabase._init
LocalDatabase._enter_tree
LocalDatabase._ready        ← may freely use SignalBus, AppLogger
...
PerformanceManager._ready   ← may use all seven above
Main scene instantiated
  (deepest children _ready first)
Main._ready                 ← ALL autoloads guaranteed ready
```

For a **scene autoload**, the same holds with one addition: within that autoload's own subtree, normal bottom-up readiness applies (children `_ready` before the autoload root's `_ready`). So `AudioManager`'s `AudioStreamPlayer` children are ready when `AudioManager._ready()` runs — which is why its `@onready var music_a: AudioStreamPlayer = $MusicPlayerA` is safe.

### 3.3 What you may safely do in each callback

| Callback | In tree? | Earlier autoloads usable? | Later autoloads usable? | Safe work |
|---|---|---|---|---|
| `_init()` | No (`get_tree()` is null) | Constructed and ready, but avoid — see below | **No** (don't exist) | Set defaults, build pure-data structures, compile regexes |
| `_enter_tree()` | Yes | Yes (fully ready) | **No** | Register with parents, connect to earlier autoloads' signals |
| `_ready()` | Yes | Yes (fully ready) | **No** | Everything: load config, open DB, connect signals, start timers |
| First frame (`process_frame` await / `_process`) | Yes | Yes | **Yes** (all ready) | Cross-autoload work needing *later* siblings |

Two rules worth engraving:

> ✅ **Best practice** — **Depend only upward.** An autoload may reference autoloads listed *above* it, in `_enter_tree` or `_ready`. It must never touch one listed *below* it during its own initialization — that identifier resolves, but the node does not exist yet, so the call raises "Invalid access on a null instance" (or `get_node_or_null` returns null). If a *downward* dependency is genuinely required at startup, it belongs in phase 2 of two-phase init (Section 5.2), or your order is wrong.

> ⚠️ **Pitfall** — Avoid touching other autoloads in `_init()` even when technically possible. `_init` runs during object construction with no tree context; code there is hard to reason about, breaks when the class is instantiated in tests, and encourages hidden coupling before the node even exists as a tree citizen. Keep `_init` pure: no side effects beyond the object's own fields.

### 3.4 "Ready before the main scene" — the load-bearing guarantee

Why does the engine bother sequencing autoloads *before* the main scene rather than alongside it? Because the entire ecosystem of gameplay code leans on this promise:

```gdscript
# Any node in any gameplay scene can write, without ceremony:
func _ready() -> void:
    SignalBus.panel_opened.connect(_on_panel_opened)
    var volume: float = SaveManager.get_setting("music_volume", 0.8)
    AudioManager.set_music_volume(volume)
```

No null checks, no "is the manager up yet?" polling, no initialization races — the guarantee "all autoloads are fully ready before any gameplay `_ready` runs" makes managers *unconditionally available* from gameplay's perspective. This is the strongest argument *for* autoloads (Section 6 will supply the arguments against): the engine gives you a two-stage boot for free — platform layer, then game layer.

The guarantee has a boundary, though. It covers *readiness of the nodes*, not *completion of asynchronous work they started*. If `LocalDatabase._ready()` kicks off a background migration thread and returns immediately, the main scene's `_ready` runs with a `LocalDatabase` that is ready-the-node but not ready-the-service. The gap between those two notions of "ready" is precisely what Section 5's explicit init patterns close.

### 3.5 Dependency graphs: order is a topological sort

Model each autoload as a graph node and each "A uses B during init" as an edge A → B. Startup is safe **iff** the `[autoload]` list is a valid topological order of that graph: every edge points *upward* in the list. Three properties follow:

1. **Cycles are unresolvable by ordering.** If `GameManager._ready()` needs `SaveManager` and `SaveManager._ready()` needs `GameManager`, no list order works. Cycles must be broken structurally: move one direction of the dependency to phase 2 (deferred), or route it through signals (A emits, B reacts later), or merge/split responsibilities. A dependency cycle between managers is always a design smell worth a whiteboard session.
2. **Multiple valid orders usually exist.** Independent managers (`SignalBus` and `AppLogger` in Relax Room — neither uses the other) may appear in either order. Pick one, document *why*, and freeze it.
3. **The graph is documentation.** A drawn autoload dependency graph — like the quick-reference card in this repo's [README](README.md) — is the single highest-value diagram a Godot project can maintain. It answers "can I reorder?", "where do I insert the new manager?", and "what breaks if X fails to init?" at a glance.

### 3.6 Verifying order empirically

Trust but verify — a five-line trace makes the real order visible in the output panel:

```gdscript
# Shared snippet at the top of every autoload's _ready():
func _ready() -> void:
    print("[boot %d] %s ready" % [Time.get_ticks_msec(), name])
```

Expected Relax Room output (timestamps illustrative):

```text
[boot 312] SignalBus ready
[boot 314] AppLogger ready
[boot 471] LocalDatabase ready      ← the 150 ms gap: opening SQLite + WAL checkpoint
[boot 476] AuthManager ready
[boot 480] GameManager ready
[boot 522] SaveManager ready        ← JSON save parsed here
[boot 543] AudioManager ready
[boot 545] PerformanceManager ready
[boot 601] Main ready
```

This trace doubles as a **startup budget profiler**: any manager whose gap balloons is doing too much synchronous work in `_ready()` — a prompt to move it behind a loading phase or a background task (Section 12). For a desktop companion app that users launch at login, keeping the autoload chain under ~250 ms is a real UX requirement, not gold-plating.

### 3.7 After startup: per-frame ordering and process_priority

Initialization order is a one-time event; *processing* order repeats every frame, and it follows the same tree order — all autoloads' `_process` callbacks run before the current scene's (given equal priorities). Usually irrelevant; occasionally load-bearing:

- `PerformanceManager` sampling frame time in `_process` measures the state *before* the scene's work for that frame. To sample **after** everything, raise its `process_priority` — nodes process in ascending priority order, so a higher number runs later:

```gdscript
# performance_manager.gd
func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    process_priority = 100                # run AFTER default-priority (0) nodes
    process_physics_priority = 100        # same lever for _physics_process
```

- Conversely, a manager that must act before anything else each frame (input recording, a frame-scoped cache reset) takes a negative priority.
- Priorities order callbacks *within* the frame; they have **no effect on startup order** — that remains the `[autoload]` list alone. Don't reach for `process_priority` to fix an init-order bug; it cannot.

The general rule: rely on tree order for the common case, state priorities explicitly (with a comment) for the exceptional case, and never build logic that silently assumes "my `_process` ran before yours" without one of the two making it true.

---

## 4. Case Study: The Relax Room Autoload Chain

Theory becomes judgment when applied to a real chain. Relax Room ships eight autoloads; here is the registered order and the declared upstream dependencies (from the [README](README.md) quick-reference card, cross-checked against the scripts):

```text
Order  Autoload            Depends on (upstream)
─────  ──────────────────  ───────────────────────────────────────
 1     SignalBus           — (none)
 2     AppLogger           — (none)
 3     LocalDatabase       SignalBus, AppLogger
 4     AuthManager         LocalDatabase, SignalBus
 5     GameManager         SignalBus, AuthManager
 6     SaveManager         SignalBus, AuthManager, GameManager
 7     AudioManager        SignalBus, GameManager, SaveManager
 8     PerformanceManager  SignalBus, SaveManager
```

As a graph (arrows point at the dependency — every arrow must point upward in the list):

```text
            ┌───────────┐        ┌───────────┐
            │ SignalBus │        │ AppLogger │
            └─────▲─────┘        └─────▲─────┘
                  │ ┌──────────────────┘
            ┌─────┴─┴───────┐
            │ LocalDatabase │
            └───────▲───────┘
                    │
            ┌───────┴───────┐
            │  AuthManager  │◄──────────────┐
            └───────▲───────┘               │
                    │                       │
            ┌───────┴───────┐               │
            │  GameManager  │◄────────┐     │
            └───────▲───────┘         │     │
                    │           ┌─────┴─────┴─┐
                    ├───────────│ SaveManager │◄──────────────┐
                    │           └───────▲─────┘               │
            ┌───────┴───────┐           │           ┌─────────┴─────────┐
            │ AudioManager  │───────────┘           │ PerformanceManager│
            └───────────────┘                       └───────────────────┘
   (SignalBus edges from nodes 3-8 omitted for legibility — everyone uses the bus)
```

### 4.1 Why each position is where it is

**1. SignalBus first — the zero-dependency substrate.** The bus declares signals and nothing else (Section 8). It has no upstream needs and *everything* downstream needs it, so it must be first. Any manager's `_ready()` may safely run `SignalBus.save_completed.connect(...)`.

**2. AppLogger second — observe everything, depend on nothing.** The logger writes to file/console and deliberately avoids using the bus for its own operation (a logger that needs the bus cannot log a bus failure). It sits second so that *from autoload 3 onward, every startup step can be logged*. Note the subtle choice: `SignalBus` and `AppLogger` are mutually independent, so order 1↔2 could be swapped without breakage — but the frozen convention "bus, then logger, then everyone" removes the ambiguity that invites casual reordering.

**3. LocalDatabase third — storage before anyone needs storage.** Opens `user://cozy_room.db`, enables WAL mode, runs migrations. Uses `AppLogger` to record migration steps and `SignalBus` to announce readiness. Everything identity- and save-related sits below it.

**4. AuthManager fourth.** Reads the accounts table from `LocalDatabase` to restore the last session (guest or username+SHA-256). Emits `auth_state_changed` on the bus.

**5. GameManager fifth.** Global game state (current room, decoration mode, character) keyed to the authenticated profile — hence below `AuthManager`.

**6. SaveManager sixth.** Loads `user://save_data.json` for the authenticated user, populates `GameManager`'s state, owns the dirty flag. Needs `AuthManager` (whose save?) and `GameManager` (state to hydrate).

**7. AudioManager seventh.** Restores volume/track preferences from `SaveManager`, reacts to `GameManager` room changes for ambience. It is *below* both of its data sources.

**8. PerformanceManager last.** Samples FPS, applies the performance profile stored in settings (via `SaveManager`). Being a pure observer with one upstream data read, last place is natural: it watches a fully-booted system.

### 4.2 Reordering thought experiments — what exactly breaks

This is the exam-grade exercise: for each illegal reorder, predict the *first observable failure*.

| Reorder | First failure | Failure class |
|---|---|---|
| `SignalBus` moved below `LocalDatabase` | `LocalDatabase._ready()` calls `SignalBus.<signal>.connect(...)` → "Invalid access on a null instance" — instant crash at startup | Loud, immediate — the *good* kind of failure |
| `AuthManager` above `LocalDatabase` | `AuthManager._ready()` queries the DB → null instance crash; or, with a defensive `get_node_or_null`, auth silently starts with *no restored session* and every user boots as a fresh guest | The defensive variant is **worse**: silent data-facing misbehavior |
| `SaveManager` above `GameManager` | `SaveManager` hydrates state into a `GameManager` that doesn't exist → crash; if written "tolerantly," the save loads into nothing and the first autosave **overwrites the user's file with defaults** | Catastrophic-if-silent: user data loss |
| `AudioManager` above `SaveManager` | Volume prefs read before they are loaded → audio plays at default volume until something re-emits `settings_updated` | Cosmetic, but erodes trust ("my settings reset randomly") |
| `PerformanceManager` first | Its settings read fails/nulls; FPS sampling still works | Mild — evidence its coupling is low |
| Alphabetical sort of the whole list (`AppLogger, AudioManager, AuthManager, GameManager, LocalDatabase, PerformanceManager, SaveManager, SignalBus`) | `AudioManager` (#2) touches `SaveManager` → crash on the very first frame of startup | Total — and the classic "I tidied the list" incident |

Three lessons generalize from the table:

1. **Crashes at startup are the best failure mode available.** Every row where a "tolerant" rewrite converts a crash into silent misbehavior gets *more* dangerous, not less. This is the philosophical foundation of Section 5's assertions: make wrong order *loud*.
2. **The severity gradient follows the data.** Reorders near the storage layer threaten user data; reorders near the presentation layer threaten polish. Review effort should distribute accordingly.
3. **Eight autoloads is the ceiling, not the target.** The chain works because each manager's upstream set is small, documented, and acyclic. The moment someone proposes autoload #9, the first question is not "where in the list?" but "does this need to be global at all?" (Section 6).

### 4.3 The chain's one deliberate cycle-avoidance

Notice what is *absent*: `LocalDatabase` never calls `SaveManager`, even though saves eventually land in SQLite. Instead, `SaveManager` emits `save_to_database_requested` on the bus, and `LocalDatabase` — connected upward, which is always safe — performs the write. The dependency *data flows downward, control flows upward via signals*. This inversion is the standard trick for keeping an autoload graph acyclic, and you will use it every time two managers "obviously need each other."

### 4.4 A worked decision: proposing autoload #9

To make Section 6's "burden of proof" concrete before we get there, walk the process for a plausible feature request: *desktop toast notifications* ("track changed", "saved", "friend online" in the future cloud phase). Someone proposes a `NotificationManager` autoload. The review runs the checklist:

1. **Is the scope whole-application?** Yes, borderline: toasts must appear over *any* scene, must survive scene changes mid-animation, and render above everything (their own `CanvasLayer`). A scene-scoped manager would die mid-toast on room change. Global scope is genuine, not convenient.
2. **What is the upstream set?** It listens to bus signals (`track_changed`, `save_completed`) and reads one setting (`notifications_enabled` via `SaveManager`). Upstream: `SignalBus`, `SaveManager`. It emits nothing anyone depends on at init.
3. **Where in the list?** Below `SaveManager` (its data source), and its relationship to `AudioManager`/`PerformanceManager` is nonexistent — so any position from 7 to 9 is *valid*; convention says append at the end unless a dependency forces otherwise. Final answer: position 9, after `PerformanceManager`.
4. **What is the reset story?** `reset()` clears the toast queue and dismisses visible toasts. One line in the protocol (Section 14.2), declared in the PR.
5. **Why not an alternative?** A `Resource` can't own a `CanvasLayer`; static funcs can't animate; scene-scoped dies mid-toast. The alternatives genuinely lose. Approved.

The resulting diff — reviewable in ten seconds precisely because the process wrote its reasoning down:

```ini
[autoload]
 ...
 PerformanceManager="*res://v1/scripts/systems/performance_manager.gd"
+NotificationManager="*res://v1/scripts/autoload/notification_manager.gd"
```

Contrast the anti-pattern version of the same request: `NotificationManager` lands at position 3 "so it can catch early events," acquires a `current_user_name` field "since it's handy," and two sprints later three systems read user state from the *notification* manager. Position in the list is architecture; make every insertion carry its paragraph.

---

## 5. Explicit Initialization Patterns

Godot's ordering guarantee covers node readiness. Production systems need more: *service* readiness, verified configuration, and diagnosable failure. These patterns close the gap. They cost ~40 lines per manager and repay it the first time startup fails on a machine that isn't yours.

### 5.1 Init-time assertions: fail at the door

The cheapest safety upgrade: every autoload's `_ready()` opens by asserting its world is sane — its config present, its upstream managers in the expected state.

```gdscript
# autoloads/local_database.gd
extends Node
## Owns user://cozy_room.db (SQLite, WAL). Upstream: SignalBus, AppLogger.

const DB_PATH := "user://cozy_room.db"
const REQUIRED_TABLES: Array[String] = [
    "accounts", "saves", "settings", "sync_queue",
]

var _db: SQLite  # from the godot-sqlite addon

func _ready() -> void:
    # 1. Upstream sanity — these MUST be above us in the [autoload] list.
    assert(get_node_or_null("/root/SignalBus") != null,
        "LocalDatabase requires SignalBus above it in the autoload order")
    assert(get_node_or_null("/root/AppLogger") != null,
        "LocalDatabase requires AppLogger above it in the autoload order")

    # 2. Environment sanity.
    _db = SQLite.new()
    _db.path = DB_PATH
    var opened := _db.open_db()
    if not opened:
        push_error("[LocalDatabase] cannot open %s — falling back to in-memory DB" % DB_PATH)
        _open_fallback_memory_db()
        return

    # 3. Schema sanity.
    for table in REQUIRED_TABLES:
        assert(_table_exists(table),
            "Missing table '%s' — migration failure?" % table)

    AppLogger.info("LocalDatabase ready (WAL=%s)" % str(_is_wal_enabled()))
```

The division of labor between the two failure tools is deliberate:

| Tool | Debug builds | Release builds | Use for |
|---|---|---|---|
| `assert(cond, msg)` | Halts with a debugger break | **Compiled out entirely** — condition not even evaluated | Programmer errors: wrong order, broken invariants, impossible states |
| `push_error(msg)` (+ recovery) | Red entry in Errors tab, execution continues | Logged; execution continues | Environment errors: missing file, locked DB, bad JSON — anything a *user's machine* can cause |

> ⚠️ **Pitfall** — Because `assert` vanishes in release exports, never put side effects inside one: `assert(_db.open_db())` opens the database in the editor and **never opens it in the shipped build**. Compute the effect into a variable, then assert the variable. This bug ships to production every week somewhere in the world.

> ✅ **Best practice** — Assert *order* explicitly, as above, in every autoload with upstream dependencies. The message names the missing manager and the fix ("above it in the autoload order"). Six months later, the teammate who reordered the list gets a sentence-long diagnosis instead of a null-instance stack trace.

### 5.2 Two-phase initialization: register, then start

The single most valuable structural pattern in this module. The problem it solves: `_ready()` conflates two jobs — *existing* (fields set, signals connected, cheap and infallible) and *starting* (open DB, parse saves, restore session — slow and fallible). Conflated, they force every manager to be fully operational before the next manager even exists, which makes downward data flows impossible and puts all slow work on the pre-first-frame critical path.

The fix: `_ready()` does phase 1 only. A boot orchestrator drives phase 2 explicitly.

```gdscript
# Phase 1 (per manager): _ready() — cheap, infallible, order-safe.
# autoloads/save_manager.gd
extends Node

signal started  # phase-2 completion, for anything that must sequence after us

var _is_started := false

func _ready() -> void:
    # Connect upward only. No file IO. No reads from other managers' state.
    SignalBus.save_requested.connect(_on_save_requested)
    SignalBus.auth_state_changed.connect(_on_auth_state_changed)

# Phase 2: called by the Boot orchestrator, in an order IT controls.
func start() -> int:  # returns Error-style code
    if _is_started:
        return OK
    var result := _load_save_file_for(AuthManager.current_profile_id())
    if result != OK:
        push_error("[SaveManager] save load failed (%d) — starting from defaults" % result)
        _state = _default_state()
    _is_started = true
    started.emit()
    return OK
```

```gdscript
# The orchestrator — either the last autoload, or (better) the boot scene.
# boot.gd — main scene root; shows the loading UI while phase 2 runs.
extends Control

func _ready() -> void:
    var boot_order: Array[Node] = [
        LocalDatabase, AuthManager, GameManager,
        SaveManager, AudioManager, PerformanceManager,
    ]
    for manager in boot_order:
        var err: int = manager.start()
        if err != OK:
            _show_boot_error(manager.name, err)
            return
        await get_tree().process_frame  # keep the loading UI responsive
    get_tree().change_scene_to_file("res://v1/scenes/main/main.tscn")
```

What two-phase init buys, concretely:

- **The engine's list order stops being load-bearing for slow work.** Phase 1 is trivially order-safe (connect-upward only); phase 2 order lives in *one reviewable array* in `boot.gd` instead of being smeared across eight `_ready()` functions.
- **Failure becomes a UI state, not a crash.** A locked database on a user's machine produces a "Could not start — is another copy running?" dialog instead of a frozen white window.
- **Startup can be async.** Each `start()` may internally await threads (Section 12); the boot scene animates a progress bar meanwhile. The engine's synchronous autoload phase stays under a few milliseconds.
- **Tests boot subsets.** A test can call `LocalDatabase.start()` alone against a temp DB without dragging seven other managers through their startup.

### 5.3 The InitGuard pattern: making phase discipline enforceable

Two-phase init introduces a new failure mode: someone calls a phase-2 API before `start()`. An `InitGuard` makes that mistake loud and standardized instead of an obscure null somewhere downstream:

```gdscript
# shared/init_guard.gd
class_name InitGuard
extends RefCounted
## Tracks a manager's lifecycle phase and turns early access into a
## precise, named error instead of a downstream null crash.

enum Phase { CREATED, READY, STARTED, STOPPED }

var _phase: Phase = Phase.CREATED
var _owner_name: String

func _init(owner_name: String) -> void:
    _owner_name = owner_name

func mark_ready() -> void:
    assert(_phase == Phase.CREATED, "%s: mark_ready() out of order" % _owner_name)
    _phase = Phase.READY

func mark_started() -> void:
    assert(_phase == Phase.READY, "%s: start() before _ready()?" % _owner_name)
    _phase = Phase.STARTED

func mark_stopped() -> void:
    _phase = Phase.STOPPED

func require_started(api_name: String) -> bool:
    if _phase == Phase.STARTED:
        return true
    push_error("%s.%s() called in phase %s — call start() first (boot order bug?)"
        % [_owner_name, api_name, Phase.keys()[_phase]])
    return false
```

Usage inside a manager:

```gdscript
# autoloads/save_manager.gd (continued)
var _guard := InitGuard.new("SaveManager")

func _ready() -> void:
    _guard.mark_ready()
    # ... phase-1 wiring ...

func start() -> int:
    # ... phase-2 work ...
    _guard.mark_started()
    return OK

func save_now() -> void:
    if not _guard.require_started("save_now"):
        return  # refuse quietly-but-loudly: error logged, no corrupt write
    _write_save_atomic()
```

The error message is the point. Compare the debugging sessions: *"Invalid access on a null instance in save_manager.gd:214"* versus *"SaveManager.save_now() called in phase READY — call start() first (boot order bug?)"*. The second one is a diagnosis; the first is homework. As a `RefCounted`, `InitGuard` is also trivially unit-testable and adds no tree overhead.

### 5.4 Lazy access vs eager init

The last design axis: *when* does expensive state come into existence?

**Eager** (everything in `start()`): predictable memory profile, all failures surface at boot, first use of every feature is instant. Cost: slower boot, and you pay for features the session never touches.

**Lazy** (on first access):

```gdscript
var _catalog: Dictionary = {}

func get_decoration_catalog() -> Dictionary:
    if _catalog.is_empty():
        _catalog = _load_catalog_json("res://v1/data/decorations.json")
    return _catalog
```

Faster boot, pay-per-use. Costs: the first caller eats a hitch (a JSON parse mid-frame is a visible stutter); failures surface at arbitrary gameplay moments instead of at boot; and lazy accessors that touch *other managers* quietly re-introduce hidden ordering dependencies — the very disease this module treats.

> ✅ **Best practice** — For a desktop companion app, the boot scene *is* the loading screen, so: eager-init everything the first interactive screen needs (auth session, settings, current room, music prefs) inside phase 2 behind the progress bar; lazy-load bulky rarely-used data (full decoration catalog, alternate room art) with an *async* warm-up kicked off after boot (`WorkerThreadPool`, Section 12) so the hitch never lands on a user interaction. Reserve raw lazy accessors for cheap, self-contained data with no cross-manager reads.

---

## 6. The Case Against Autoload Abuse

Autoloads are the most-warned-against feature in Godot architecture writing, and the warnings come from the top: the engine's own best-practices documentation dedicates a page ("Autoloads versus regular nodes") to talking you *out* of reaching for them, and educators like GDQuest echo the theme — singletons are powerful, controversial, and the quiet reason many prototypes become unchangeable. This section takes the criticism seriously, then lands on a balanced rule you can actually apply in review.

### 6.1 What global mutable state actually costs

**Cost 1 — The debugging domain explodes.** The official docs' audio example makes it concrete: once a global `Sound.play()` exists, *any code anywhere* can call it with wrong data, so when a sound bug appears, the search space is the whole project. Generalized: a bug in autoload state can originate at every one of its call sites. With `grep -c` returning 140 references to `GameManager` across a project, "who set `current_room` to null?" is a 140-suspect investigation. Compare a scene-scoped manager whose state can only be touched by its own subtree: the suspect list is one scene.

**Cost 2 — Hidden dependencies.** A scene that uses `SaveManager` inside one buried function *looks* self-contained: its exported variables and signals declare nothing about the dependency. Instantiate that scene in another project, a test, or a tool context, and it breaks in a way its public interface never advertised. Autoload access is invisible coupling — the class lies about its requirements.

**Cost 3 — Testability collapses by default.** You cannot construct the system under test with a fake `SaveManager` when the reference is a hard global name resolved at parse time. Every test of every class that touches an autoload becomes an integration test with the real manager — real file IO, real DB, real audio — unless you build seams deliberately (Section 16).

**Cost 4 — Reload and reset bugs.** Scene-local state dies with the scene; autoload state survives everything short of quitting (Section 14). Every autoload field is a little landmine of "left over from the previous session/screen/user" unless a reset protocol exists. The classic: log out, log back in as a different user, and the room still shows the previous user's decorations because `GameManager` was never told to forget.

**Cost 5 — Centralized responsibility and contention.** One object owns a system for the whole game, so it accretes features, its API bloats, every teammate edits the same file (merge conflicts), and its `_process` runs always, everywhere, whether relevant or not.

### 6.2 Symptoms of autoload spaghetti — a review checklist

Diagnose by symptom, not by count. Any two of these appearing together is the signal to stop adding and start extracting:

- **Autoload count creeping past ~8-10**, with recent additions justified as "it was easiest."
- **Downward or cyclic dependencies** — manager A reaches into manager B *below* it in the list, or two managers reference each other and "it works because of a deferred call somewhere."
- **Gameplay logic in managers** — `GameManager` contains `if decoration.category == "plants"` branching. Global managers should coordinate; the moment they contain per-feature rules, every feature change edits a global file.
- **Managers as variable buckets** — an autoload with 30 public fields and no methods enforcing invariants: not a manager, a global scratchpad.
- **Signal bus bypass** — systems calling each other's methods directly *and* the bus existing "for the other cases." The architecture has two communication styles and neither is enforced.
- **"Temporary" globals that survived** — `TempFixManager`, added during a jam week, load-bearing for two years.
- **Fear of the reorder** — nobody on the team will touch the `[autoload]` list because nobody can predict what breaks. (Section 4.2's table is the antidote: make the predictions explicit.)

### 6.3 The balanced verdict: what genuinely belongs global

The criticism is real, and yet Relax Room ships eight autoloads with a clear conscience. The resolution is a scope test, straight from the engine docs' own criterion — autoloads suit *systems with wide scope that manage their own information without invading other objects' data*:

**Deserves to be an autoload** (whole-application scope, one per process, must outlive scenes):

- **A signal bus** — pure declarations, no state to corrupt; the decoupling layer everything else stands on (Section 8).
- **Logging** — must exist before everything and after everything; inherently process-wide.
- **Settings/config** — one settings store per app is the *correct* cardinality, not a compromise.
- **Audio direction** — music must survive scene changes by definition; a crossfade cannot be scene-local.
- **Persistence & auth session** — the save file and login are per-process facts.
- **Performance/diagnostics** — observers of the whole process.

**Does not deserve to be an autoload** (scoped to a scene, level, screen, or feature):

- **Per-level/per-room state** — current puzzle state, spawned decorations' runtime data: dies with the room, so it should *live* in the room. Making it global creates the reset problem for zero benefit.
- **UI flow within one screen** — a `PanelManager` coordinating panels of the main scene belongs *in* the main scene (as in Relax Room — note it is a plain class, not autoload #9).
- **Anything needed "by two or three scenes"** — that is what scene composition, exported references and signals are for; two consumers is not "wide scope."
- **Pure function libraries** — `Helpers.snap_to_grid()` needs no node and no state: static functions on a `class_name` (Section 7.1), not an autoload.

> ✅ **Best practice** — Institutionalize the burden of proof: a PR adding an autoload must state (1) why the scope is genuinely whole-application, (2) its upstream dependencies and position in the list, (3) its reset story (Section 14), and (4) why a Section 7 alternative doesn't fit. If the paragraph is hard to write, the autoload is wrong. (Section 4.4 walks a worked example of this review.)

### 6.4 A refactor narrative: shrinking a God-manager

Extraction is easier to believe with a before/after. Suppose `GameManager` has accreted decoration rules — a symptom from the checklist above (gameplay logic in a manager):

```gdscript
# BEFORE — game_manager.gd (autoload): global file, per-feature rules.
func can_place(decoration: Dictionary, room_id: String) -> bool:
    if decoration["category"] == "plants" and room_id == "bathroom":
        return decoration["size"] <= 2         # plants rule
    if decoration["premium"] and not AuthManager.is_premium():
        return false                           # monetization rule
    return _placed_count(decoration["id"]) < decoration["max_per_room"]
```

Every new decoration rule edits the global manager; every test of a rule boots the world. The extraction: rules become a `RefCounted` policy object owned by the *room scene*, constructed with plain data:

```gdscript
# AFTER — rooms/placement_policy.gd: pure, scene-owned, trivially testable.
class_name PlacementPolicy
extends RefCounted

var _room_id: String
var _is_premium_user: bool

func _init(room_id: String, is_premium_user: bool) -> void:
    _room_id = room_id
    _is_premium_user = is_premium_user

func can_place(decoration: Dictionary, placed_count: int) -> bool:
    if decoration["category"] == "plants" and _room_id == "bathroom":
        return decoration["size"] <= 2
    if decoration["premium"] and not _is_premium_user:
        return false
    return placed_count < decoration["max_per_room"]
```

```gdscript
# room_controller.gd builds it at room entry — the ONLY point touching globals:
func _enter_room(room_id: String) -> void:
    _policy = PlacementPolicy.new(room_id, AuthManager.is_premium())
```

`GameManager` shrinks back to coordination (current room, mode flags); rules live beside the feature they govern; the global-touching surface collapses to one constructor call at a natural boundary. Repeat this move each time a manager grows an `if` about a specific feature, and the autoload roster stays a set of *thin coordinators* instead of a distributed God object. Section 16 turns the same move into the testing strategy.

---

## 7. Alternatives to Autoloads, Compared

"Don't overuse autoloads" is empty advice without a toolbox. Here are the six alternatives, each with working code, what it's for, and what it costs.

### 7.1 Static members on class_name scripts (Godot 4.1+)

GDScript supports `static func` since forever and **`static var` since 4.1** — which quietly removed the most common *legitimate* reason small projects had for autoloads: shared helpers and counters.

```gdscript
# utils/helpers.gd
class_name Helpers
## Pure functions. No node, no autoload entry, no [autoload] line.

const GRID_SIZE := 64

static func snap_to_grid(pos: Vector2) -> Vector2:
    return (pos / GRID_SIZE).floor() * GRID_SIZE

static func format_duration(seconds: float) -> String:
    return "%d:%02d" % [int(seconds) / 60, int(seconds) % 60]
```

```gdscript
# utils/id_gen.gd
class_name IdGen
## Static state shared by ALL users of the class — no instance required.

static var _next_id: int = 1

static func next() -> int:
    var id := _next_id
    _next_id += 1
    return id
```

Call sites: `Helpers.snap_to_grid(drop_pos)`, `IdGen.next()` — the ergonomics of an autoload with none of the tree presence. **Use for:** pure utility libraries, constants, simple shared counters/caches. **Cannot do:** anything nodal — no `_process`, no signals-as-instance-members wired at startup, no timers, no tree callbacks. **Caveat:** `static var` is *still global mutable state* — it shares Section 6's testing and reset costs (a static cache survives scene reloads exactly like an autoload field, and there is no `_exit_tree` to clean it). Godot offers `static func _static_init()` for one-time static setup; there is no static teardown.

### 7.2 Custom Resources as shared state

A `Resource` subclass holds data; whoever loads the same `.tres` path shares the same instance (resources are cached by path). This gives *shared observable state without any global name*:

```gdscript
# data/session_settings.gd
class_name SessionSettings
extends Resource

signal changed

@export var music_volume: float = 0.8:
    set(v):
        music_volume = clampf(v, 0.0, 1.0)
        changed.emit()
@export var language: String = "en":
    set(v):
        language = v
        changed.emit()
```

```gdscript
# Any node that needs settings declares the dependency in its interface:
@export var settings: SessionSettings

func _ready() -> void:
    settings.changed.connect(_apply_settings)
    _apply_settings()
```

Each consumer scene exports the slot and the *same* `session_settings.tres` is assigned in the inspector. The dependency is now **visible** (it's in the scene file), **swappable** (tests assign a fresh `SessionSettings.new()`), and **reactive** (the `changed` signal). **Use for:** settings, tuning data, shared game-state blobs, anything designers should edit. **Costs:** no behavior/coordination (it's data, not a manager); the cached-by-path sharing is implicit and surprises newcomers; and mutable shared resources need the same reset discipline as any shared state.

### 7.3 Dependency injection via exported nodes

The scene tree *is* a DI container if you let it be. A child declares what it needs; the parent scene supplies it:

```gdscript
# rooms/decoration_placer.gd
extends Node2D
## Places decorations. Everything I need is handed to me — I reach for no globals.

@export var room: RoomController          # assigned in the room scene
@export var catalog: DecorationCatalog    # a Resource
@export var audio_player: AudioStreamPlayer

func place(decoration_id: String, pos: Vector2) -> void:
    var snapped := Helpers.snap_to_grid(pos)
    room.add_decoration(decoration_id, snapped)
    audio_player.play()
```

**Use for:** any component you want reusable or unit-testable — the test instantiates it, assigns fakes to the three slots, done. **Costs:** wiring effort (every consumer's scene must fill the slots — `@export` + inspector keeps this cheap); and injection reaches its limits across *scene boundaries* (a deep child needing something from three scenes up), which is exactly the hole signals and the bus fill.

### 7.4 Scene-scoped managers

The manager pattern, minus the global. The main scene owns its coordinators as ordinary children:

```text
Main (main.tscn)
 ├─ PanelManager        ← plain Node + script; coordinates THIS scene's panels
 ├─ RoomController
 └─ UI
     └─ ... panels ...
```

`PanelManager` (a real Relax Room class, deliberately *not* autoload #9) is findable by its siblings (`%PanelManager` with a unique name, or exported references), fully alive while the scene runs — and **automatically freed and rebuilt on scene reload**, which makes the entire reset problem of Section 14 vanish for its state. **Use for:** any coordination whose lifetime equals a scene's lifetime. **Costs:** none, really — this should be the *default*, with autoloads as the exception for state that must outlive scenes.

### 7.5 Service locator: injection ergonomics over an autoload substrate

A halfway house used by larger teams: *one* autoload, a registry, and everything else resolved through it:

```gdscript
# autoloads/services.gd
extends Node
## The only autoload. Managers register here; consumers resolve by name.

var _registry: Dictionary = {}  # StringName -> Object

func register(service_name: StringName, service: Object) -> void:
    assert(not _registry.has(service_name), "Duplicate service: %s" % service_name)
    _registry[service_name] = service

func unregister(service_name: StringName) -> void:
    _registry.erase(service_name)

func resolve(service_name: StringName) -> Object:
    assert(_registry.has(service_name),
        "Service '%s' not registered — boot order or missing register()" % service_name)
    return _registry[service_name]
```

```gdscript
# Consumer:
var save_service: SaveService = Services.resolve(&"save") as SaveService
```

The win is **substitutability**: tests call `Services.register(&"save", FakeSaveService.new())` and every consumer transparently gets the fake — no parse-time hard binding to a concrete global. The costs are honest: it's still global state one level removed; name-based resolution trades compile-time identifier checking for runtime lookup (typos surface at run, mitigated by `StringName` constants); and it adds a layer of indirection every reader must learn. **Use when** testability across a large codebase matters more than maximal simplicity; **skip** in small projects where eight greppable global names are clearer than a registry.

### 7.6 Composition: making managers out of parts

Orthogonal to all of the above: whatever owns the behavior, build it from small components rather than one monolith. Relax Room's `SaveManager` composes a `SaveSerializer` (RefCounted — versioned JSON in/out), an `AtomicFileWriter` (RefCounted — temp-file + rename), and a `DirtyTracker` — the autoload is 80 lines of coordination over three testable parts. Composition doesn't remove the global; it shrinks what the global *is*, which pays off directly in Section 16.

### 7.7 Decision table

| Need | Reach for | Not |
|---|---|---|
| Pure helper functions, constants | `class_name` + `static func` | Autoload |
| Shared editable data (settings, tuning) | Custom `Resource` (+ `changed` signal) | Autoload with 30 fields |
| Component needs collaborators | `@export` injection | Reaching up with globals |
| Coordination within one scene | Scene-scoped manager child | Autoload |
| Cross-scene *events* | Signal bus (one autoload) | Direct manager-to-manager calls |
| State that must outlive scenes (audio, session, saves) | A real autoload, built per Sections 5 & 16 | Scene-local hacks with `process_mode` tricks |
| Large team + heavy testing | Service locator over one autoload | 12 hard-bound globals |
| Simple shared counter/cache | `static var` (mind reset!) | Autoload |

### 7.8 Migration guide: demoting an existing autoload

Deciding an autoload shouldn't exist is easy; removing one that 60 call sites depend on is surgery. The staged, low-risk procedure:

1. **Census.** `grep -rn "TheManager\." --include="*.gd"` (and search `.tscn` files for connections). Classify each call site: pure-function use (→ static), data read (→ Resource/injection), event notification (→ bus signal), coordination (→ scene-scoped manager).
2. **Build the replacement beside the autoload**, not instead of it: the `class_name` statics, the `.tres` settings resource, the scene-local manager — whichever Section 7 target the census chose. Both now exist; nothing is broken.
3. **Turn the autoload into a shim.** Its methods delegate to the replacement, each tagged with a deprecation comment (and optionally `push_warning` in debug builds so remaining call sites announce themselves at runtime):

```gdscript
# the_manager.gd — TEMPORARY SHIM, delete when call sites reach zero.
func snap(pos: Vector2) -> Vector2:
    if OS.is_debug_build():
        push_warning("TheManager.snap is deprecated — use Helpers.snap_to_grid")
    return Helpers.snap_to_grid(pos)
```

4. **Migrate call sites in reviewable batches** (by folder or feature), running the game/tests after each batch — never one 400-file commit.
5. **Delete**: remove the `[autoload]` line last, in its own commit, after a full-project grep returns zero. The parse-time nature of global names now works *for* you — any missed call site fails loudly at startup, not silently at runtime.

The same staging works in reverse (promoting a scene-scoped manager to autoload when scope genuinely grew) — and in both directions, the shim step is what keeps the team unblocked mid-migration.

---

## 8. The Signal Bus Pattern Done Safely

The signal bus (a.k.a. event bus / global observer) is the one autoload pattern nearly everyone endorses — *when done with discipline*. Relax Room's `SignalBus` carries 31 signals across 8 domains and remains maintainable; this section is the discipline that keeps it so.

### 8.1 What the bus is, and the two rules

A signal bus is an autoload that **declares signals and does nothing else**. Emitters fire events into it; listeners connect to it; neither knows the other exists.

```gdscript
# autoloads/signal_bus.gd
extends Node
## Global event bus — DECLARATIONS ONLY. See docs/signal_contract.md.
## Rule 1: no state, no logic, no _process — nothing here can be "wrong".
## Rule 2: signals are FACTS that happened, not commands to someone.

# ── Room domain ─────────────────────────────────────────────
signal room_changed(room_id: String)
signal decoration_placed(decoration_id: String, grid_pos: Vector2)
signal decoration_removed(instance_id: int)
signal decoration_moved(instance_id: int, grid_pos: Vector2)

# ── System domain ───────────────────────────────────────────
signal save_requested()
signal save_completed(success: bool)
signal load_completed()
signal settings_updated(settings: Dictionary)

# ── Auth domain ─────────────────────────────────────────────
signal auth_state_changed(is_authenticated: bool, profile_id: String)
signal auth_error(code: int, message: String)
# ... (31 total — full inventory in README.md quick-reference)
```

**Rule 1 — declarations only** is what makes the bus a *safe* global: with no state, there is nothing to corrupt, nothing to reset, no ordering hazard beyond "exists first." The moment someone adds `var last_room_id` to the bus "for convenience," it stops being a bus and becomes a state manager with 31 doors.

**Rule 2 — facts, not commands** governs naming: `decoration_placed` (past-tense fact) rather than `place_decoration` (imperative command). Facts have any number of listeners, including zero; commands imply one obligated executor, and a "command" with an unknown executor is just a method call wearing a disguise. The gray zone is request signals — `save_requested` — which are legitimate *when the contract documents exactly one handler* (SaveManager). Suffix them `_requested` so the special case is visible.

### 8.2 Typed declarations and the contract document

GDScript 2.0 allows typed signal parameters — use them always: `signal volume_changed(bus_name: String, linear: float)` gives the editor and reviewers real information, and mismatched emits become diagnosable instead of silently shipping a Variant surprise.

But typing is not a contract. For each signal, three questions need a written answer: *who emits, who listens, what do the parameters mean (units, nullability)?* Keep the answer next to the declaration or in one contract file:

```gdscript
## Emitted by: SaveManager (after every atomic write attempt).
## Listened by: UI/SaveIndicator (toast), AppLogger (audit), LocalDatabase (sync queue).
## success=false means the WRITE failed; the in-memory state is still valid.
signal save_completed(success: bool)
```

Ten seconds to write; saves an hour precisely when someone asks "can I remove this signal?" — the answer is `grep` plus the contract, not archaeology.

> ⚠️ **Pitfall** — **Signal storms.** A emits, listener B mutates state and emits, C reacts and emits — and a single decoration placement fans out into 14 cascaded events, occasionally cycling (`settings_updated` → apply → `settings_updated`…). Symptoms: mysterious double-execution, stack overflows via re-entrant emission, frame spikes on "simple" actions. Containment: listeners should *update themselves*, not re-broadcast interpretations of what they heard; guard re-entrancy on the few hubs that must re-emit (`if _is_applying: return`); and keep bus signals coarse-grained facts (one user action ≈ one signal), not per-field change notifications — that finer granularity is what Resource `changed` signals (7.2) are for.

### 8.3 Connection hygiene

Nodes that connect to an autoload's signals must respect their *own* lifetime, not the bus's:

```gdscript
func _ready() -> void:
    SignalBus.room_changed.connect(_on_room_changed)

func _exit_tree() -> void:
    # Not strictly required — Godot auto-disconnects freed objects — but
    # explicit disconnection makes lifetime visible and protects against
    # the node being REMOVED-but-not-freed and reacting from limbo.
    if SignalBus.room_changed.is_connected(_on_room_changed):
        SignalBus.room_changed.disconnect(_on_room_changed)
```

For fire-and-forget listeners, prefer flags over manual bookkeeping: `SignalBus.save_completed.connect(_on_first_save, CONNECT_ONE_SHOT)` disconnects itself after one delivery. And when a listener may be freed mid-frame while emissions are in flight, connect with `CONNECT_DEFERRED` so delivery happens at idle time when the tree is stable — the same message-queue machinery as `call_deferred` (Section 11).

The full flag set, for reference (combine with `|`):

| `ConnectFlags` | Effect | Reach for it when |
|---|---|---|
| *(none, default)* | Immediate, synchronous delivery on emit | The normal case — keep it unless a problem forces a flag |
| `CONNECT_DEFERRED` | Delivery queued to idle time via the MessageQueue | Listener mutates the tree, or may be freed mid-frame; boot-time emissions racing `_ready` |
| `CONNECT_ONE_SHOT` | Auto-disconnect after first delivery | "First save", "next frame only" listeners — replaces manual disconnect bookkeeping |
| `CONNECT_PERSIST` | Connection serialized into the `.tscn` | Editor-made connections; rarely set from code |
| `CONNECT_REFERENCE_COUNTED` | Same connect can be made N times, needs N disconnects | Plugin/framework code with idempotent-connect needs; rare in app code |

> ⚠️ **Pitfall** — Deferred delivery changes *ordering* observably: a `CONNECT_DEFERRED` listener sees the world as it is at flush time, after every synchronous listener already ran and possibly mutated state. If two listeners of the same signal have an order dependency between them, that dependency is a design bug — fix it by merging them or chaining explicitly, not by tuning flags until it happens to work.

### 8.4 Debugging signal flow

The decoupling you bought has a price: control flow is no longer readable top-to-bottom. Tooling recovers it.

**Runtime introspection.** Every `Object` can enumerate its wiring:

```gdscript
# Debug console command: dump the bus wiring.
func dump_bus() -> void:
    for sig_info in SignalBus.get_signal_list():
        var sig_name: String = sig_info["name"]
        var conns := SignalBus.get_signal_connection_list(sig_name)
        if conns.is_empty():
            print("  %s  → (no listeners!)" % sig_name)   # dead signal? typo'd connect?
            continue
        for c in conns:
            var cb: Callable = c["callable"]
            print("  %s  → %s.%s" % [sig_name, cb.get_object(), cb.get_method()])
```

`get_signal_connection_list()` returns one dictionary per connection (keys: `signal`, `callable`, `flags`); the inverse view, `get_incoming_connections()` on a *listener*, answers "what is wired into me?". Two smells this dump exposes instantly: signals with zero listeners (dead code, or an emitter shouting into the void because a listener misspelled its connect) and signals with *suspiciously many* listeners (a storm amplifier).

**A tracing bus for development builds:**

```gdscript
# In SignalBus._ready() — dev builds only:
func _ready() -> void:
    if OS.is_debug_build():
        for sig_info in get_signal_list():
            var sig_name: String = sig_info["name"]
            # Variadic-safe trace: bind the name, accept up to 2 payload args.
            connect(sig_name, _trace.bind(sig_name), CONNECT_DEFERRED)

func _trace(a = null, b = null, sig_name: String = "?") -> void:
    AppLogger.debug("[bus] %s (%s, %s)" % [sig_name, str(a), str(b)])
```

One log line per event turns "why did the volume change twice?" from a mystery into a timestamped narrative. (Bound arguments arrive *after* emitted ones — hence the trailing `sig_name` parameter.)

**Editor tooling.** The Node dock's Signals tab shows editor-made connections (with the ⚡ icon on connected nodes), and while the game runs, the debugger's remote tree lets you select `/root/SignalBus` and inspect it live. Note that *code-made* connections don't appear in the editor's Signals tab — which is exactly why the runtime dump above earns its place in your debug console.

> ✅ **Best practice** — Budget the bus. When a new signal is proposed, ask: is this a whole-app fact (bus), a scene-internal event (local signal between siblings), or a data change (Resource `changed`)? Relax Room's 31 signals pass this test; a bus with 150 signals is the observer-pattern version of the God object, and its `grep` surface makes every change a project-wide event.

### 8.5 A worked domain: the volume-change flow end-to-end

One complete flow, from slider to disk, shows every rule of this section operating together. The requirement: the settings panel changes music volume; audio applies it live; the preference persists; the panel also reflects changes made *elsewhere* (a future hotkey).

```gdscript
# signal_bus.gd — the fact, typed and contracted:
## Emitted by: whoever changes a volume (SettingsPanel today; hotkeys later).
## Listened by: AudioManager (applies), SaveManager (persists), SettingsPanel (reflects).
## 'linear' is 0.0-1.0 linear energy, NOT decibels — convert at the audio edge only.
signal volume_changed(bus_name: String, linear: float)
```

```gdscript
# ui/settings_panel.gd — the emitter (and a listener of its own fact):
func _on_music_slider_value_changed(value: float) -> void:
    SignalBus.volume_changed.emit("Music", value)

func _ready() -> void:
    # Reflect external changes; the guard stops the feedback loop when the
    # emission we caused comes back around to our own slider:
    SignalBus.volume_changed.connect(_on_volume_changed_externally)

func _on_volume_changed_externally(bus_name: String, linear: float) -> void:
    if bus_name != "Music" or is_equal_approx(_music_slider.value, linear):
        return                      # re-entrancy guard: our own echo — ignore
    _music_slider.set_value_no_signal(linear)   # reflect WITHOUT re-emitting
```

```gdscript
# audio_manager.gd — a listener; decibel conversion stays at the audio edge:
func _on_volume_changed(bus_name: String, linear: float) -> void:
    var idx := AudioServer.get_bus_index(bus_name)
    AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(linear, 0.0001)))

# save_manager.gd — another listener; persistence is ITS interpretation:
func _on_volume_changed(bus_name: String, linear: float) -> void:
    _logic.set_value("volume/" + bus_name.to_lower(), linear)   # sets dirty flag
```

Observations worth generalizing: the emitter knows *nothing* about audio buses or save files; each listener applies its own domain's interpretation and **re-broadcasts nothing** (no storm); `set_value_no_signal()` is the UI-side re-entrancy tool that breaks echo loops without flags; and the unit comment in the contract ("linear, NOT decibels") is the kind of one-liner that prevents the classic half-volume-everywhere bug when a second emitter appears. When the hotkey feature arrives, it is one `emit` call — every listener works unchanged. That is the bus earning its place as a global.

---

## 9. Godot's Threading Model

Everything so far concerned *when* code runs at startup. The second half of "autoload safety" concerns *which thread* code runs on — because autoloads, as the natural home of file IO, database writes and network calls, are exactly where threads enter a Godot project, and where they cause the least-reproducible bugs of your career if the model isn't clear.

### 9.1 The main thread owns the SceneTree

Godot's contract, stated bluntly in the official threading documentation:

> **Interacting with the active scene tree from another thread is NOT thread-safe.** Accessing objects or data from multiple threads "is not always supported (if you do it, it will cause unexpected behaviors or crashes)."

The main thread runs the game loop: input dispatch, `_process`/`_physics_process` callbacks, signal emission delivery, node lifecycle, UI. The scene tree — every node in it, including all eight of your autoloads — belongs to that thread. A worker thread that calls `label.text = "done"`, `add_child(...)`, `queue_free()`, or emits a signal whose listeners touch nodes is corrupting engine state that is concurrently being read and written by the main loop. Sometimes it works. Sometimes it crashes three minutes later in unrelated rendering code. That "sometimes" is the defining misery of data races: they are not reliably reproducible, so they resist every debugging habit you have.

In Godot 4, node methods called from the wrong thread often (not always) fail loudly with:

```text
ERROR: Caller thread can't call this function in this node (/root/SaveManager).
Use call_deferred() or call_thread_group() instead.
```

Treat that error as a *gift* — it is the engine catching a race before it corrupts memory — and treat its advice as the law: results cross back to the main thread via `call_deferred` (Section 11), never by direct access.

### 9.2 What IS safe off the main thread

The engine is not monolithically single-threaded — the safe list is substantial, and it happens to cover exactly what a companion app wants to offload:

| Safe from worker threads | Notes |
|---|---|
| Pure GDScript computation | Your own math, parsing, data transforms — always safe on data you own |
| `FileAccess` / `DirAccess` on your own files | File IO is the canonical thread job; don't share one open `FileAccess` across threads |
| SQLite via addon, HTTP via `HTTPClient` | Blocking IO belongs off-main; one connection per thread |
| `ResourceLoader.load()` / threaded loading | Loading resources in threads is supported; `load_threaded_request()` exists precisely for this |
| Most low-level **servers** (`RenderingServer`, `PhysicsServer2D/3D`, `AudioServer`, `NavigationServer2D/3D`) | Thread-safe by design (navigation queries run in parallel; rendering/physics have separate-thread modes with caveats) |
| Reading/writing *elements* of Arrays/Dictionaries | Safe as element access — but **resizing/adding/removing needs a Mutex** |
| `Mutex`, `Semaphore`, `Thread`, `WorkerThreadPool` APIs themselves | They exist for this |

| NOT safe from worker threads | Consequence |
|---|---|
| Any node in the active scene tree | The error above, or silent corruption |
| Emitting signals with main-thread listeners | Listener code runs on *your* thread, touching nodes |
| `AStar2D/3D/Grid2D` shared across threads | Documented data corruption |
| Modifying a `Resource` shared with the main thread | Races; build a copy, hand it over |
| GPU-touching operations (texture creation, image upload) | Stalls via forced RenderingServer sync |

One structurally important nuance: **building node subtrees *outside* the tree is safe.** A worker thread may construct a whole detached hierarchy — `var card := preload("res://card.tscn").instantiate()`, set its properties, build children — as long as nothing is attached to the live tree until the hand-off: `get_tree().root.add_child.call_deferred(card)`. Construct off-thread, attach on-main. That one idiom covers most "I need threads for content" cases.

### 9.3 The decision ladder

Threads are the *last* resort, not the first. For any "this blocks the frame" problem, climb this ladder and stop at the first rung that works:

1. **Do less work** — cache the parse, index the lookup, don't re-scan the catalog every frame.
2. **Spread work across frames** — an await-based coroutine chewing a chunk per frame (Section 13). No threads, no races, good enough for surprisingly much.
3. **Use the engine's built-in async** — `ResourceLoader.load_threaded_request()` for scenes/assets; the engine's threads, your zero risk.
4. **`WorkerThreadPool` task** — for genuinely CPU/IO-heavy one-shot jobs (Section 12). Pool management is the engine's problem.
5. **A dedicated long-lived `Thread`** — only for a persistent worker with its own loop and queue (a DB writer that lives for the session, Section 10.4). Maximum control, maximum responsibility.

> ⚠️ **Pitfall** — Thread creation itself is expensive — the docs single out Windows especially. Spawning a fresh `Thread` per save operation means paying creation cost per save *and* risking overlapping writers. Long-lived worker + queue, or the pool. Never thread-per-task.

### 9.4 Platform notes for threading code

Threading behavior is the least portable part of your project; three platform realities to design around *before* they surprise you in an export:

- **Web exports:** browser threads require `SharedArrayBuffer`, which browsers only enable on **cross-origin isolated** pages (the site must serve COOP/COEP headers). The web export preset exposes a thread-support option, and itch.io-style hosts vary in header support. Design consequence: gate thread usage on `OS.has_feature("threads")` and keep a frame-spread coroutine fallback (Section 13.1) for the code paths that must also run in a no-threads build. A companion app is desktop-first, but the settings/room-preview slice of Relax Room has a web demo on the roadmap — the fallback costs little if designed in early.
- **Windows:** thread creation is notably more expensive than on Unix-likes — reinforcing "create at load time, reuse forever." A start-per-click `Thread` that felt fine on a Linux dev box becomes measurable jank on the Windows machines your users actually run.
- **Mobile (Android export):** the OS suspends backgrounded apps at unpredictable moments; a worker mid-write can be frozen for hours or killed. Listen for `NOTIFICATION_APPLICATION_PAUSED` and flush queues *then* — the mobile sibling of Section 17.3's close handler. Atomic writes (temp + rename) stop a mid-suspension kill from corrupting the save.
- **Headless/CI (`--headless`):** threads work normally, but total run time is bounded by the job — a forgotten `wait_to_finish()` that would hang a desktop app forever hangs a CI job until its timeout, billing you for the privilege. The shutdown discipline of 10.4 is what makes your test jobs terminate.

---

## 10. Thread, Mutex and Semaphore in Practice

### 10.1 Thread lifecycle: start, monitor, always join

The `Thread` class in Godot 4 (exact signatures from the class reference):

```text
start(callable: Callable, priority: Priority = PRIORITY_NORMAL) -> Error
wait_to_finish() -> Variant       # blocks until the function ends; returns its return value
is_started() -> bool              # start() was called successfully
is_alive() -> bool                # the function is still executing right now
get_id() -> String                # engine-assigned thread id
# enum Priority { PRIORITY_LOW = 0, PRIORITY_NORMAL = 1, PRIORITY_HIGH = 2 }
```

Minimal correct usage inside an autoload:

```gdscript
extends Node

var _thread: Thread

func start_export(catalog: Dictionary) -> void:
    if _thread != null and _thread.is_started():
        push_warning("Export already running")
        return
    _thread = Thread.new()
    # PASS DATA IN by bind — duplicate so the worker owns its copy outright.
    var err := _thread.start(_export_worker.bind(catalog.duplicate(true)))
    if err != OK:
        push_error("Thread start failed: %d" % err)

func _export_worker(catalog: Dictionary) -> int:   # runs OFF the main thread
    var file := FileAccess.open("user://catalog_export.json", FileAccess.WRITE)
    if file == null:
        return FileAccess.get_open_error()
    file.store_string(JSON.stringify(catalog, "  "))
    file.close()
    # Signal completion — DEFERRED, so the main thread runs the handler (Sec. 11):
    _on_export_done.call_deferred(OK)
    return OK

func _on_export_done(result: int) -> void:         # runs ON the main thread
    _thread.wait_to_finish()                       # instant: worker already ended
    SignalBus.save_completed.emit(result == OK)

func _exit_tree() -> void:
    if _thread != null and _thread.is_started():
        _thread.wait_to_finish()                   # NEVER let a started thread dangle
```

The three rules encoded there:

1. **Every started thread must be joined.** The class reference is explicit about disposal: a `Thread` must not be destroyed while holding locked Mutexes or waiting on Semaphores, and `wait_to_finish()` should have been called. Skipping the join risks leaks and platform-dependent teardown crashes — hence the `_exit_tree` backstop.
2. **`wait_to_finish()` blocks the caller.** Call it on the main thread only when you know the worker is done (as above, from the completion callback — the join is then instantaneous and merely collects the return value) — or you have reinvented the freeze you were avoiding.
3. **`is_alive()` is for polling, not synchronization.** `if not _thread.is_alive(): use_results()` without a join is a race; `is_alive()` answers "still running?" for progress UI, and only `wait_to_finish()` establishes "finished, results visible."

### 10.2 Mutex: mutual exclusion for shared state

A `Mutex` guarantees one thread at a time inside the guarded region: `lock()` blocks until available, `unlock()` releases, `try_lock() -> bool` attempts without blocking. Godot's mutexes are re-entrant for the *same* thread (it may lock again; unlock as many times).

```gdscript
var _stats_mutex := Mutex.new()
var _stats: Dictionary = {"writes": 0, "errors": 0}   # shared: worker writes, UI reads

func _worker_record_write(ok: bool) -> void:          # worker thread
    _stats_mutex.lock()
    _stats["writes"] += 1
    if not ok:
        _stats["errors"] += 1
    _stats_mutex.unlock()

func get_stats_snapshot() -> Dictionary:              # main thread
    _stats_mutex.lock()
    var snapshot := _stats.duplicate()
    _stats_mutex.unlock()
    return snapshot                                   # caller gets a COPY, races impossible
```

Discipline points, each purchased with someone's lost weekend:

- **Guard the data, not the code.** Every access — reads included — to `_stats` goes through the mutex. A lock that protects writes while reads go bare is not protection.
- **Hold locks briefly; never call out while holding.** Locking is costly (the docs warn to minimize frequency and duration), and calling arbitrary code (signals! logging that takes its own lock!) while holding a mutex is how deadlocks are built.
- **Hand out copies, not references.** Returning `_stats` itself would let the caller read it unlocked later. `duplicate()` ends the sharing at the boundary.
- **Prefer message passing over shared state.** The best mutex is the one you didn't need because the thread *owns* its data and communicates by queue (next pattern).

### 10.3 Semaphore: signaling "work exists"

Where a mutex says *only one at a time*, a semaphore counts permits: `wait()` blocks until the count is positive then decrements; `post()` increments, waking a waiter; `try_wait() -> bool` is the non-blocking probe. Its canonical role: letting a worker *sleep* until there is something to do — the docs' own suspended-worker example — instead of burning a core polling.

### 10.4 The guarded queue: the one threading pattern to memorize

Producer-consumer with `Mutex` + `Semaphore` is the backbone of every serious "background writer" in a Godot app. Relax Room's database write-behind, in full:

```gdscript
# autoloads/db_write_queue.gd  (owned by LocalDatabase in Relax Room)
extends Node
## Single long-lived writer thread. Main thread enqueues; worker drains.
## SQLite happens ONLY on the worker; results return via call_deferred.

var _thread: Thread
var _queue_mutex := Mutex.new()
var _work_sema := Semaphore.new()
var _queue: Array[Dictionary] = []        # each: {sql: String, params: Array}
var _should_exit := false                 # guarded by _queue_mutex

func _ready() -> void:
    _thread = Thread.new()
    _thread.start(_writer_loop)

# ── Producer side (main thread) ─────────────────────────────
func enqueue_write(sql: String, params: Array = []) -> void:
    _queue_mutex.lock()
    _queue.push_back({"sql": sql, "params": params})
    _queue_mutex.unlock()
    _work_sema.post()                     # wake the worker: one unit of work

# ── Consumer side (worker thread) ───────────────────────────
func _writer_loop() -> void:
    var db := SQLite.new()                # the WORKER's own connection
    db.path = LocalDatabase.DB_PATH
    db.open_db()
    while true:
        _work_sema.wait()                 # sleep until work (or shutdown) posted
        _queue_mutex.lock()
        if _should_exit and _queue.is_empty():
            _queue_mutex.unlock()
            break
        var job: Dictionary = _queue.pop_front()
        _queue_mutex.unlock()             # ← unlock BEFORE the slow part
        var ok := db.query_with_bindings(job["sql"], job["params"])
        if not ok:
            _report_error.call_deferred(job["sql"], db.error_message)
    db.close_db()

func _report_error(sql: String, message: String) -> void:   # main thread
    AppLogger.error("[DBQueue] write failed: %s — %s" % [sql, message])
    SignalBus.save_completed.emit(false)

# ── Shutdown (main thread, e.g. from _exit_tree) ────────────
func shutdown_blocking() -> void:
    _queue_mutex.lock()
    _should_exit = true
    _queue_mutex.unlock()
    _work_sema.post()                     # wake the worker so it can see the flag
    _thread.wait_to_finish()              # drains remaining queue, then exits
```

Read the shape, because every correct variant shares it:

- **The mutex guards only the queue**, and is released *before* the expensive DB call — lock hold times stay microscopic, the producer never stalls behind a slow write.
- **The semaphore's count mirrors queue length** — one `post()` per enqueue, one `wait()` per dequeue. No polling loop, no `OS.delay_msec` hack; an idle worker costs nothing, which *matters* in a companion app whose selling point is negligible background footprint.
- **The worker owns its own SQLite connection.** Nothing about the DB handle is shared, so nothing about the DB needs locking. (WAL mode is what lets this writer coexist with the main thread's read connection.)
- **Shutdown is a message, not a murder.** Set the flag under the lock, post the semaphore so the sleeping worker wakes to observe it, join. The queue drains before exit — enqueued saves are never dropped.

> ⚠️ **Pitfall** — **Deadlock by construction.** The classic recipes: (a) thread A locks mutex 1 then wants 2, thread B locks 2 then wants 1 — always acquire multiple locks in one global order; (b) `wait_to_finish()` on a worker that is blocked waiting for something only the caller would provide (a semaphore the main thread was supposed to post, a deferred call that can't run because the main thread is blocked *in the join*) — never join a thread that can be waiting on you; (c) emitting a signal or logging inside a locked region, where a listener re-enters and re-locks. When the app freezes solid rather than crashing, you built one of these.

### 10.5 Synchronization smells, annotated

Five patterns that pass casual review and fail in production — train your eye on the shape:

```gdscript
# SMELL 1 — check-then-act across the lock boundary:
if _queue.is_empty():          # checked WITHOUT the lock...
    _mutex.lock()              # ...state may have changed by now
    ...
# FIX: the check belongs INSIDE the locked region.

# SMELL 2 — "it's just an int, ints are atomic":
_write_count += 1              # read-modify-write: three steps, racy from two threads
# FIX: GDScript has no atomics — even counters shared across threads take the mutex.

# SMELL 3 — locking around the slow thing:
_mutex.lock()
var result := db.query(sql)    # 40 ms inside the lock: every producer now stalls
_mutex.unlock()
# FIX: pop the job under the lock, run the query outside it (Section 10.4's shape).

# SMELL 4 — returning the guarded object:
func get_queue() -> Array: return _queue     # caller iterates it unlocked, later
# FIX: return duplicates/snapshots; the lock's guarantees end at the return.

# SMELL 5 — one mutex, many meanings:
# _big_lock guards the queue AND the stats AND the config → every subsystem
# contends with every other; deadlock surface grows with each new caller.
# FIX: one mutex per independently-consistent piece of data, each documented.
```

If a code review can point at a shared variable and nobody can answer "which mutex guards this, and is it held at *every* access?", the answer is already "there is a race" — the only question is the date of the incident.

---

## 11. call_deferred and set_deferred: The Safe Bridge

### 11.1 What deferral actually does

`Object.call_deferred(method, ...)`, `Callable.call_deferred(...)` and `Object.set_deferred(property, value)` do not run anything where they are called. They append a message to the engine's internal **MessageQueue**, which the **main thread** flushes at a defined safe point of the frame (idle time — after processing, when the tree is not mid-mutation). Two distinct superpowers follow from that one mechanism:

1. **Thread bridge.** A worker thread may enqueue; the *execution* happens on the main thread. This is the officially sanctioned way for background work to touch the tree — the docs' own idiom: `node.add_child.call_deferred(child_node)`.
2. **Same-thread timing escape.** Even pure main-thread code uses deferral to escape "you can't do that *right now*" moments: freeing a body during physics callback resolution, reparenting during tree traversal, changing focus mid-input. "Do this, but at a safe moment later this frame."

```gdscript
# The two syntaxes — prefer the Callable form (typo-checked at parse time):
_on_export_done.call_deferred(OK)                 # Callable.call_deferred(args)
call_deferred("_on_export_done", OK)              # StringName form — runtime lookup

# Property variant:
progress_bar.set_deferred("value", 0.75)          # assignment happens at idle time
```

### 11.2 Rules of the bridge

- **Arguments are captured at enqueue time, executed later.** Pass *values* (or objects the receiver will own). Passing a reference the worker keeps mutating hands the race right through the bridge — `duplicate()` payloads at the boundary, same rule as Section 10.2.
- **Deferred calls are fire-and-forget.** No return value reaches the caller; if the worker needs an answer back, that answer travels as another message (or the worker blocks on its own semaphore that the main-thread handler posts).
- **Ordering is FIFO** among deferred calls, but everything waits for the flush: a deferred call made during `_ready()` runs after the *entire* current tree operation completes — which is exactly why `add_child.call_deferred` fixes "parent is busy setting up children" errors during scene initialization.
- **The flush needs a live main loop.** A deferred call enqueued while the main thread is blocked (in `wait_to_finish()`, say) executes only after the block ends — see the deadlock recipe in Section 10.4. And messages enqueued in the same frame the target is freed are dropped with a debugger warning; pair deferral with `is_instance_valid()` checks in handlers that might outlive their targets.

> ✅ **Best practice** — Design worker code so `call_deferred` appears exactly once per job: at the *completion boundary*, invoking a single main-thread `_on_x_done(result)` handler. Workers that sprinkle a dozen deferred UI pokes throughout their body are scattering their main-thread re-entry points; one boundary function keeps the thread-hand-off auditable at a glance.

### 11.3 Emitting signals from workers — the composed idiom

Signals are main-thread creatures (their listeners touch nodes), so a worker never calls `SignalBus.save_completed.emit(true)` directly. It defers the emission — `Signal.emit` is itself accessible as a bound method via `emit_signal`, but clearest is deferring your own wrapper:

```gdscript
# Worker thread:
_emit_save_completed.call_deferred(true)

# Main thread:
func _emit_save_completed(success: bool) -> void:
    SignalBus.save_completed.emit(success)
```

Every listener then runs on the main thread with full tree access, blissfully unaware a thread was ever involved. The bus stays a main-thread-only object — write that into its contract header.

### 11.4 Worked example: progress reporting without flooding the queue

A worker that reports progress naively defers *per item* — thousands of messages, each a main-thread hop, turning the progress bar itself into the frame hitch. Coalesce at the worker side; hand over at most a few updates per second:

```gdscript
# Worker thread — imports N catalog entries, reports coalesced progress:
func _import_worker(entries: Array) -> void:
    var last_report_msec := 0
    for i in entries.size():
        _import_one(entries[i])                       # off-tree work only
        var now := Time.get_ticks_msec()
        if now - last_report_msec >= 100:             # ≤10 updates/second
            last_report_msec = now
            _report_progress.call_deferred(i + 1, entries.size())
    _report_progress.call_deferred(entries.size(), entries.size())  # final 100%
    _on_import_done.call_deferred()

# Main thread:
func _report_progress(done: int, total: int) -> void:
    # set_deferred would ALSO work here, but we are already on the main
    # thread inside a deferred call — direct assignment is correct and clear:
    _progress_bar.value = float(done) / float(total)
    _progress_label.text = "%d / %d" % [done, total]
```

Three details carry the pattern: the *worker* owns the throttle (the main thread never sees the flood, rather than seeing it and dropping it); the final 100% report is unconditional (never let rounding or throttling strand the bar at 97%); and the completion path is still a single boundary function per Section 11.2's best practice. The same coalescing applies to any chatty worker→main traffic — log lines, per-row DB results, sync statuses: batch into an `Array`, defer the batch.

---

## 12. WorkerThreadPool and Background Work in a Companion App

### 12.1 The pool: threads without thread management

Managing long-lived `Thread` objects is justified for persistent workers (the DB queue). For *one-shot* jobs — "hash this password," "parse this 2 MB JSON," "thumbnail these images" — the engine ships a better tool: **`WorkerThreadPool`**, a singleton with a pre-allocated pool of worker threads sized to the machine. You submit callables; it schedules them; you avoid creation cost (Section 9.3's Windows warning) and thread-count explosions.

The API (exact signatures from the class reference):

```text
add_task(action: Callable, high_priority := false, description := "") -> int   # task id
add_group_task(action: Callable, elements: int, tasks_needed := -1,
               high_priority := false, description := "") -> int               # group id
is_task_completed(task_id) -> bool          wait_for_task_completion(task_id) -> Error
is_group_task_completed(group_id) -> bool   wait_for_group_task_completion(group_id) -> void
get_group_processed_element_count(group_id) -> int
```

**Single task — the completion-flag pattern.** The one wrinkle: `wait_for_task_completion()` *blocks*, so calling it eagerly on the main thread recreates the freeze. The clean shape polls the flag or (simpler) lets the task announce itself via the Section 11 bridge:

```gdscript
func hash_password_async(password: String, salt: String) -> void:
    WorkerThreadPool.add_task(_hash_job.bind(password, salt), false, "auth: pbkdf2")

func _hash_job(password: String, salt: String) -> void:      # pool thread
    var ctx := HashingContext.new()                          # crypto is pure math: thread-safe
    var digest := _pbkdf2_sha256(ctx, password, salt, 100_000)
    _on_hash_done.call_deferred(digest)

func _on_hash_done(digest: PackedByteArray) -> void:         # main thread
    AuthManager.complete_login(digest)
```

**The mandatory wait.** The docs are strict: *every* task must eventually be waited for so the pool can reclaim its bookkeeping — even if you know it finished. The pattern above therefore stores the task id and calls `wait_for_task_completion(id)` inside `_on_hash_done` (instantaneous by then), or in a periodic sweep. Skipping the wait leaks task records for the session's lifetime. Corollary from the reference: waiting on a task *from inside another pool task* can return `ERR_BUSY` on circular dependency — don't build task graphs by blocking; chain via completion callbacks instead.

**Group tasks — data parallelism in one line.** `add_group_task(callable, elements)` calls your callable with each index `0..elements-1`, distributed across the pool — the docs' example is per-enemy AI processing; a companion-app example is regenerating 69 decoration thumbnails:

```gdscript
var group_id := WorkerThreadPool.add_group_task(
    _regen_thumbnail, decoration_ids.size(), -1, false, "thumbnails")
# Progress for the UI, polled from _process:
var done := WorkerThreadPool.get_group_processed_element_count(group_id)
```

Each `_regen_thumbnail(index: int)` must be independent (no shared mutable state without a mutex) and each must not touch the tree — the same laws as always; the pool changes scheduling, not safety rules.

> ⚠️ **Pitfall** — The pool is shared with the engine and sized to the CPU. Submitting *blocking* IO (a 3-second HTTP call) occupies a pool thread that engine subsystems and your other tasks want; submitting *trivial* work (docs' warning) spends more on scheduling than the job. Pool = substantial CPU-bound or short IO-bound one-shots. Long-blocking or persistent loops = dedicated `Thread`.

### 12.2 When threads are worth it in a desktop companion

A companion app's constraint is inverted from a game's: not "hit 16 ms with heavy simulation" but "stay imperceptible for hours." The threading budget follows:

| Workload | Verdict | Tool |
|---|---|---|
| SQLite writes (saves, sync queue) | **Yes — the flagship case.** A WAL checkpoint or contended write can spike tens of ms; users feel a hitch while *decorating in the background of a work call* | Dedicated writer thread + guarded queue (10.4) |
| Save-file JSON serialize + atomic write | **Yes** at Relax Room's v5 save size; serialization of a big dict mid-frame is a visible stutter | Serialize on worker, atomic temp-file rename on worker, `save_completed` via bridge |
| HTTP / cloud sync (Supabase, Phase 4) | **Yes, but** — prefer `HTTPRequest` node first: it already does its work internally threaded and delivers a signal on the main thread. Hand-rolled `HTTPClient` on a thread only for streaming/custom needs | `HTTPRequest` (no code!), else Thread |
| Password hashing (SHA-256 iterations) | **Yes** — deliberate key-stretching must not freeze the login UI | `WorkerThreadPool.add_task` |
| Loading room scenes/art | **Yes — engine-provided.** `ResourceLoader.load_threaded_request(path)` then poll `load_threaded_get_status()` and collect with `load_threaded_get()` | Built-in threaded loader |
| Decoration placement, UI, tweens, crossfades | **No.** Microseconds of main-thread work; threading adds risk for nothing | Main thread |
| Log writing | **Borderline** — buffered `FileAccess.flush()` on a timer is usually enough; thread it only if profiling says so | Buffer first |

The last row generalizes into the golden rule of this entire half of the module:

> ✅ **Best practice** — **Profile before threading.** Every thread you add imports Sections 9-11's entire risk catalog into your project. Add one only when the profiler shows a main-thread stall you cannot cache, defer, or chunk away — and when you do, copy a *whole known-good pattern* (guarded queue, pool task with completion bridge) rather than improvising synchronization. Threading bugs are the only category where "it seems to work" carries almost zero evidence of correctness.

### 12.3 The built-in threaded loader: zero-risk async for assets

Before writing any thread for *asset* loading, use the machinery the engine already ships — `ResourceLoader`'s threaded API gives you background loading with progress, entirely on engine-managed threads:

```gdscript
# room_preloader.gd — swap rooms without a hitch.
var _pending_path := ""

func preload_room(scene_path: String) -> void:
    var err := ResourceLoader.load_threaded_request(scene_path)
    if err != OK:
        push_error("Preload request failed for %s (%d)" % [scene_path, err])
        return
    _pending_path = scene_path
    set_process(true)                    # poll status once per frame

func _process(_delta: float) -> void:
    var progress: Array = []
    match ResourceLoader.load_threaded_get_status(_pending_path, progress):
        ResourceLoader.THREAD_LOAD_IN_PROGRESS:
            SignalBus.settings_updated.emit({"room_load_progress": progress[0]})
        ResourceLoader.THREAD_LOAD_LOADED:
            set_process(false)
            var packed: PackedScene = ResourceLoader.load_threaded_get(_pending_path)
            _swap_to(packed.instantiate())          # main thread: attach is safe here
        ResourceLoader.THREAD_LOAD_FAILED, ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
            set_process(false)
            push_error("Room load failed: " + _pending_path)
```

The API contract: `load_threaded_request(path)` starts the background load; `load_threaded_get_status(path, progress)` reports `THREAD_LOAD_IN_PROGRESS / LOADED / FAILED / INVALID_RESOURCE` and fills `progress[0]` with a 0-1 fraction; `load_threaded_get(path)` collects the resource (blocking briefly if called early — poll the status first to keep it hitch-free). No mutexes, no joins, no tree-safety analysis: the engine's threads do the parsing, and your code only ever runs on the main thread. For scene/texture/audio loading this obsoletes hand-rolled loader threads entirely — reserve your own threads for the things the engine has no loader for: your SQLite, your HTTP, your file formats.

---

## 13. Async Without Threads: await and Coroutines

Most "async" needs in a Godot app are not parallelism needs at all — they are *sequencing* needs: wait for a signal, wait a beat, spread work over frames. GDScript's `await` covers all of these with zero threads, zero mutexes, zero races — everything stays on the main thread, just *paused and resumed*.

### 13.1 The mechanics

`await` suspends the current function until its operand completes, then resumes *in place*:

```gdscript
# Await a signal — resumes when it fires; yields the signal's arguments:
var success: bool = await SignalBus.save_completed

# Await a one-shot timer:
await get_tree().create_timer(0.5).timeout

# Await the next frame:
await get_tree().process_frame

# Await another coroutine (any function containing await):
await AudioManager.crossfade_to(track_id)
```

A function containing `await` becomes a **coroutine**: calling it returns control to the caller at the first suspension, and the remainder runs later, on the main thread, when the awaited thing completes. This is cooperative concurrency: only one piece of code runs at a time, and suspension points are *visible in the source* — which is why coroutine bugs are debuggable in ways thread bugs never are.

> ⚠️ **Pitfall** — **Coroutines and worker threads do not mix.** `await` belongs to main-thread code: signal delivery and the resumption machinery run through the main loop, so a function executing on a `Thread` must stay *synchronous* end to end. A worker that needs to wait for something sleeps on a `Semaphore` (Section 10.3) — that is the thread world's `await`. If you find yourself wanting `await get_tree().process_frame` inside a thread function, the code is on the wrong side of the Section 9.3 ladder.

Frame-spreading, the honest alternative to threads for medium-size work:

```gdscript
# Import 69 decorations without ever blocking a frame — no threads involved.
func import_catalog_gently(entries: Array) -> void:
    const BUDGET_MSEC := 4          # leave the rest of the frame for the app
    var frame_start := Time.get_ticks_msec()
    for entry in entries:
        _import_one(entry)          # main thread: free to touch nodes, no races!
        if Time.get_ticks_msec() - frame_start > BUDGET_MSEC:
            await get_tree().process_frame
            frame_start = Time.get_ticks_msec()
    SignalBus.load_completed.emit()
```

### 13.2 Resumption safety — the questions to ask at every await

The suspended function is, in effect, an object floating in memory waiting for a wake-up call. Between suspension and resumption, *the world changes*. Three questions, in descending order of pain caused by not asking them:

**1. Does my node still exist when I resume?** If the awaiting node is freed while suspended, the resumed code runs against a corpse (for lambdas/detached continuations) or never resumes (the coroutine dies with its object — usually the merciful outcome). In *autoloads* the node itself is immortal, but the things it captured may not be:

```gdscript
# In an autoload — the AUTOLOAD survives the await; will 'panel' ?
func flash_panel(panel: Control) -> void:
    panel.modulate = Color.YELLOW
    await get_tree().create_timer(1.0).timeout
    if not is_instance_valid(panel):    # scene may have changed during that second
        return
    panel.modulate = Color.WHITE
```

Every await in an autoload that holds a reference into the *current scene* needs the `is_instance_valid` recheck on resumption — the current scene is exactly the part of the tree that dies while autoloads live on.

**2. Is my state still true when I resume?** The await let every other system run: the user logged out, the room changed, another save started. Re-validate assumptions, or gate re-entrancy outright:

```gdscript
var _save_in_flight := false

func save_with_animation() -> void:
    if _save_in_flight:
        return                       # re-entrancy guard: user mashed Ctrl+S
    _save_in_flight = true
    SignalBus.save_requested.emit()
    var ok: bool = await SignalBus.save_completed
    _save_in_flight = false
    _show_toast("Saved" if ok else "Save failed")
```

**3. Will the signal I'm awaiting definitely fire?** `await some_signal` with a signal that never comes is a silent forever-leak of the suspended state. Await only signals with guaranteed emission on every code path (including error paths — this is why `save_completed(success: bool)` fires on failure too, rather than a separate `save_failed` that would strand awaiters), or race a timeout:

```gdscript
# Timeout-guarded await (works because awaiting a signal that already fired
# is impossible — so we funnel both outcomes through one locally-owned signal):
signal _sync_result(ok: bool)

func sync_with_timeout(seconds: float) -> bool:
    SignalBus.sync_completed.connect(func(): _sync_result.emit(true),
        CONNECT_ONE_SHOT)
    get_tree().create_timer(seconds).timeout.connect(
        func(): _sync_result.emit(false), CONNECT_ONE_SHOT)
    return await _sync_result
```

### 13.3 Awaiting across scene changes and pauses

Two engine behaviors interact with suspended autoload coroutines in ways worth knowing cold:

- **`SceneTree` timers and pause.** `get_tree().create_timer(1.0)` by default *ignores pause* — pass `create_timer(1.0, false)` to make it pause-respecting (`process_always = false`). An autoload coroutine that awaits a default SceneTree timer will happily resume *while the game is paused* and start mutating scene state that the pause was supposed to freeze. Decide per await: should this delay tick during pause? (Section 15 completes the pause picture.)
- **Scene changes don't cancel autoload coroutines.** `change_scene_to_file()` frees the old scene and instantiates the new one, but a suspended coroutine in an autoload keeps right on waiting, then resumes in a world where its captured nodes are gone (question 1) and its assumptions are stale (question 2). There is no built-in "cancel my coroutines" — the idiom is an epoch counter: bump `_scene_epoch` on every `room_changed`, capture it before the await, and abandon on mismatch after resumption (`if epoch != _scene_epoch: return`).

> ✅ **Best practice** — Choose by problem shape: **await** for sequencing and waiting (its natural habitat — UI flows, crossfades, boot phases); **frame-spreading await** for medium CPU work on tree-touching data; **threads/pool** only for blocking IO and heavy CPU on *non-tree* data. The best concurrency model is the one with the fewest simultaneously-true facts to hold in your head — and await is dramatically cheaper cognitively than threads.

### 13.4 Worked example: awaiting HTTP in an autoload

The future cloud-sync phase makes this concrete: an `HTTPRequest` node owned by an autoload, driven by `await`. No threads appear in *your* code — `HTTPRequest` performs its transfer internally and delivers a signal on the main thread — and because the autoload owns the node, the flow survives scene changes by construction:

```gdscript
# Part of a sync-capable autoload. HTTPRequest child added in _ready().
var _http: HTTPRequest

func _ready() -> void:
    _http = HTTPRequest.new()
    _http.timeout = 10.0                 # NEVER await a request with no timeout
    add_child(_http)                     # child of the AUTOLOAD → survives scenes

func fetch_profile(profile_id: String) -> Dictionary:
    var err := _http.request(Constants.API_BASE + "/profiles/" + profile_id)
    if err != OK:
        push_error("Request setup failed: %d" % err)
        return {}
    # Awaiting a multi-argument signal yields an Array of its arguments:
    var response: Array = await _http.request_completed
    var result: int = response[0]        # HTTPRequest.Result
    var code: int = response[1]          # HTTP status
    var body: PackedByteArray = response[3]
    if result != HTTPRequest.RESULT_SUCCESS or code != 200:
        SignalBus.sync_completed.emit()  # contract: fires on failure too (§13.2)
        return {}
    var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
    return parsed if parsed is Dictionary else {}
```

Apply the Section 13.2 questions and watch them all resolve favorably: the awaiting object is the autoload (immortal — question 1 passes without `is_instance_valid` gymnastics as long as the *result* is state, not scene nodes); one `HTTPRequest` handles one request at a time, so a `_request_in_flight` guard (question 2) belongs in the real version; and `timeout` plus the fires-on-failure signal contract guarantee resumption (question 3). This is the template for every "talk to a server from a manager" feature: engine-internal threading, await-shaped code, main-thread simplicity.

---

## 14. Autoloads and Scene Reload

### 14.1 The persistence semantics, precisely

What actually happens on the common "restart" paths:

| Action | Current scene | Autoloads | Static vars / cached Resources |
|---|---|---|---|
| `get_tree().change_scene_to_file(path)` | Freed, replaced | **Untouched — state persists** | Untouched |
| `get_tree().reload_current_scene()` | Freed, re-instantiated fresh | **Untouched — state persists** | Untouched |
| F5 / relaunch the executable | Fresh | Fresh (`_init` → `_ready` chain re-runs) | Fresh |
| Quit → OS relaunch | Fresh | Fresh | Fresh |

The middle column is the trap. `reload_current_scene()` *feels* like "restart the game," and every scene-local variable indeed comes back pristine — but every autoload field, every `static var`, every cached `.tres` keeps its value. The game only *mostly* restarts.

**Symptoms of state leakage** (all real bug-report shapes): restart the session and the score/decorations from last round are still there; log out and the next guest sees the previous user's room (an `AuthManager`/`GameManager` reset gap — for a persistence app this is a privacy bug, not a polish bug); a `_save_in_flight` flag stuck `true` from a save interrupted by reload, so saving never works again this session; tweens or timers inside an autoload still animating labels that no longer exist.

### 14.2 The reset protocol

Since the engine will not reset autoloads, you need a *convention* that does — explicitly, centrally, and observably. One signal, one method name, one owner:

```gdscript
# In SignalBus:  signal session_reset()
# In every stateful autoload — the reset() convention:

# game_manager.gd
func reset() -> void:
    current_room_id = Constants.DEFAULT_ROOM
    decoration_mode = false
    selected_decoration = null
    # NOTE: does NOT touch _ready()-established wiring — connections stay.

# save_manager.gd
func reset() -> void:
    if _save_in_flight:
        push_warning("[SaveManager] reset during save — letting write finish")
    _state = _default_state()
    _dirty = false
```

```gdscript
# The orchestrator — GameManager owns session flow in Relax Room:
func start_new_session(profile_id: String) -> void:
    # Order matters exactly like boot order — reset upstream-first:
    for manager in [GameManager, SaveManager, AudioManager, PerformanceManager]:
        manager.reset()
    SignalBus.session_reset.emit()      # scene-side listeners clear THEIR caches
    SaveManager.load_profile(profile_id)
    get_tree().reload_current_scene()
```

Design points that separate a working protocol from a decorative one:

- **`reset()` restores *state*, not *wiring*.** Signal connections, child nodes, the DB handle — phase-1/phase-2 products (Section 5.2) survive reset. Reset returns the manager to "just started, nothing loaded," not to "just constructed." (If you adopted two-phase init, `reset()` ≈ "back to just-after-`start()` with default data.")
- **Reset order mirrors boot order** — same dependency graph, same topological logic.
- **The signal lets non-autoloads participate** — the scene's `PanelManager` closes panels, caches clear — without the orchestrator knowing they exist.
- **Write the checklist into review:** any PR adding a stateful field to an autoload must touch that autoload's `reset()` (or document why the field is session-independent). This is the single habit that prevents leakage bugs from *accumulating*.

> ⚠️ **Pitfall** — `static var` state (Section 7.1) is invisible to this protocol unless you remember it: statics live on the *script*, not the node, so no autoload `reset()` will find them by accident. Keep a `SomeClass.reset_static()` and call it from the orchestrator — or better, don't cache session state in statics at all.

### 14.3 Editor quirks: F6 and hot-reload

Two editor-only behaviors that regularly masquerade as autoload bugs:

- **Running the current scene (F6)** boots the *full* autoload roster (autoloads load for any scene run) — but your test scene isn't the main scene, so the boot orchestrator may never run, and managers sit in phase-1 limbo. If your `InitGuard` (5.3) errors with "called in phase READY" only under F6, that's the guard working as designed: either give the test scene a mini-boot (`await` a `TestBoot.start_minimum()`), or make the manager APIs used by test scenes phase-tolerant deliberately.
- **Script hot-reload** (saving a script while the game runs) recompiles and swaps the script *in place* on the live autoload node. Exported/simple state is preserved where possible, but lambdas, connections made with now-recompiled callables, and in-flight coroutines can behave oddly — a known sharp edge (there are long-standing engine issues around hot-reloading scripts with threads and deferred lambda calls). Treat live-edit of autoload scripts as a convenience for tweaking *values*, and restart the run after editing autoload *logic* — 10 seconds of relaunch versus 30 minutes chasing a ghost that exists only in the hot-reloaded session.

### 14.4 Postmortem walkthrough: the logout leak

To cement the protocol, here is the anatomy of the archetypal leak bug, reconstructed the way you would actually encounter it:

**Report:** "Logged out of my account, my sister logged in as guest, and her room had *my* decorations for a second, then they saved into *her* file."

**Timeline:** (1) User A decorates; `GameManager.placed_decorations` holds 12 entries, `SaveManager._dirty = true`. (2) Logout → `AuthManager` clears the session and emits `auth_state_changed(false, "")` — but nothing listened for the purpose of *state clearing*; the team assumed scene change handles it. (3) `change_scene_to_file("menu.tscn")` frees the room scene — the *visuals* die, so it looks clean. (4) Guest login; `reload` into the room scene. (5) The new room's `_ready()` renders from `GameManager.placed_decorations` — still holding A's 12 entries. (6) `SaveManager`'s autosave timer fires (`_dirty` never cleared) and writes A's decorations into the guest profile.

**The two-line diagnosis:** autoloads outlive scenes (step 5's stale render) and flags are state too (step 6's misdirected write). **The fix** is precisely Section 14.2: `start_new_session()` resets `GameManager` and `SaveManager` in order and broadcasts `session_reset` *before* profile load — after which step 5 renders an empty room and step 6 has nothing dirty to write. **The regression test** (layer 3 of Section 16's pyramid): boot → decorate as A → logout → login as B → assert B's `GameManager` state empty and B's save file untouched. Every stateful-autoload project has this bug exactly once; the protocol decides whether it also has it twice.

---

## 15. Autoloads and Pausing

### 15.1 How pause propagates

`get_tree().paused = true` suspends processing tree-wide, but per-node behavior is governed by `process_mode` (Node property, `ProcessMode` enum):

| `process_mode` | While paused | Typical use |
|---|---|---|
| `PROCESS_MODE_INHERIT` (default) | Follows parent → effectively pauses (root inherits pausable behavior) | Ordinary gameplay nodes |
| `PROCESS_MODE_PAUSABLE` | Stops | Explicitly pause-bound nodes |
| `PROCESS_MODE_WHEN_PAUSED` | Runs **only** while paused | Pause-menu UI, "paused" animations |
| `PROCESS_MODE_ALWAYS` | Runs regardless | Managers, music, background services |
| `PROCESS_MODE_DISABLED` | Never runs | Deactivated subtrees |

Paused nodes stop receiving `_process`, `_physics_process`, `_input` and friends — but they still exist, signals still connect, and *direct method calls still work*. Pause stops the engine *pushing* callbacks; it does not freeze objects.

### 15.2 The autoload default is wrong for managers

Autoloads are children of root with default `PROCESS_MODE_INHERIT` — meaning **a paused tree pauses your managers too**. For most of the Relax Room roster that outcome is exactly wrong: pause is a UI state, but saves must still flush, music must keep playing (it's a relaxation app — pausing the ambience *is* the bug), performance sampling should keep observing, and the sync queue should keep draining.

```gdscript
# First line of _ready() in every manager that must run while paused:
func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    # ...
```

Decide per manager, not by blanket rule — the roster's verdicts:

| Autoload | `process_mode` | Why |
|---|---|---|
| SignalBus | ALWAYS (moot — no `_process`) | Emissions are direct calls; pause-irrelevant either way |
| AppLogger | ALWAYS | Must log during pause; flush timer must tick |
| LocalDatabase | ALWAYS | Write-behind queue must drain during pause |
| AuthManager | ALWAYS | Session timeout logic shouldn't freeze with the UI |
| GameManager | ALWAYS — it *owns* pause | See below |
| SaveManager | ALWAYS | Autosave timer must fire during a long pause |
| AudioManager | ALWAYS | Music through pause is a product requirement |
| PerformanceManager | ALWAYS | Observing "paused" frames is part of its job |

That table's uniformity is typical: *managers overwhelmingly want ALWAYS* — which is why forgetting the line produces the classic bug family: "autosave never triggers if the settings panel is open," "crossfade freezes mid-fade when pausing."

**Someone must own the pause state itself.** An ALWAYS-mode manager is the natural owner, since it keeps running either way:

```gdscript
# game_manager.gd
func set_paused(paused: bool) -> void:
    get_tree().paused = paused
    SignalBus.settings_updated.emit({"paused": paused})   # or a dedicated signal
```

### 15.3 Timers and tweens owned by autoloads

- **`Timer` nodes** parented under an autoload inherit its `process_mode` — under an ALWAYS manager they tick through pause. Right for autosave; *wrong* for anything meant to respect pause — set the child Timer's own `process_mode = PROCESS_MODE_PAUSABLE` to opt it back in.
- **SceneTree timers** (`create_timer`) don't live under any node: pause behavior comes from the `process_always` argument (Section 13.3). Default is *ignore pause*.
- **Tweens** created by an autoload (`create_tween()`) are bound to that node — by default a tween pauses with its bound node, so tweens made by ALWAYS-mode managers run through pause. `AudioManager`'s crossfade tween therefore glides on while paused (correct); use `tween.set_pause_mode(Tween.TWEEN_PAUSE_STOP)` on any autoload tween that animates *pausable scene content*, or it will animate nodes whose own processing is frozen — visually eerie and occasionally state-corrupting.

> ⚠️ **Pitfall** — Mixed-mode chains: an ALWAYS autoload awaits a default SceneTree timer (ignores pause), then calls into a PAUSABLE scene node's method. Every step was "correct" locally; the composite resumes during pause and mutates frozen UI. When pause bugs appear, audit the whole chain — the mode that matters is the *weakest link's*, and direct calls bypass pause entirely.

---

## 16. Testing Autoload-Heavy Codebases

Testing is where autoload costs (Section 6.1, cost 3) present the bill. The global name is resolved at parse time, the real manager boots with the test runner, and suddenly a "unit" test of score logic performs real SQLite IO. This section builds the escape hatches, cheapest first.

### 16.1 The root problem, stated exactly

```gdscript
# room_controller.gd — as commonly written:
func place_decoration(id: String, pos: Vector2) -> void:
    if not AuthManager.is_authenticated():        # hard global — can't fake
        return
    GameManager.add_decoration(id, pos)           # hard global — can't fake
    SaveManager.mark_dirty()                      # hard global — real file IO looms
    SignalBus.decoration_placed.emit(id, pos)     # hard global
```

Four parse-time bindings to live singletons. A GdUnit4/GUT test scene that instantiates `RoomController` gets all four *for real* — the autoloads start with the test runner (test frameworks run inside a normal Godot process, so the `[autoload]` roster boots first, as always). You cannot construct the unit in isolation because its collaborators are ambient.

### 16.2 Seam 1 — the hexagonal split: RefCounted core, thin node shell

The highest-leverage refactor in this module, and the pattern the original edition of this file recommended in one line — here it is in full. Split every manager into **pure logic** (a `RefCounted` class: no tree, no globals, constructor-injected dependencies) and a **thin autoload shell** (owns the node-ness: signals wiring, timers, the global name):

```gdscript
# save/save_logic.gd — THE CORE. No extends Node, no autoload refs, no IO.
class_name SaveLogic
extends RefCounted

var _writer            # duck-typed: anything with write_atomic(path, text) -> int
var _clock             # anything with now_unix() -> int
var _state: Dictionary = {}
var dirty := false

func _init(writer, clock) -> void:
    _writer = writer
    _clock = clock

func set_value(key: String, value: Variant) -> void:
    _state[key] = value
    dirty = true

func save_if_dirty(path: String) -> int:
    if not dirty:
        return OK
    _state["saved_at"] = _clock.now_unix()
    var err: int = _writer.write_atomic(path, JSON.stringify(_state, "  "))
    if err == OK:
        dirty = false
    return err
```

```gdscript
# autoloads/save_manager.gd — THE SHELL. All tree/global concerns; ~40 lines.
extends Node

var _logic: SaveLogic

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    _logic = SaveLogic.new(AtomicFileWriter.new(), SystemClock.new())
    SignalBus.save_requested.connect(_on_save_requested)
    $AutosaveTimer.timeout.connect(_on_save_requested)

func mark_dirty() -> void:
    _logic.dirty = true

func _on_save_requested() -> void:
    var err := _logic.save_if_dirty(Constants.SAVE_PATH)
    SignalBus.save_completed.emit(err == OK)
```

Now the interesting logic tests **without any autoload, tree, or file**:

```gdscript
# test/unit/test_save_logic.gd  (GdUnit4 flavor; GUT is analogous)
extends GdUnitTestSuite

class FakeWriter:
    var writes: Array[String] = []
    var next_error: int = OK
    func write_atomic(_path: String, text: String) -> int:
        if next_error != OK: return next_error
        writes.append(text)
        return OK

class FakeClock:
    var t := 1_753_000_000
    func now_unix() -> int: return t

func test_save_skipped_when_clean() -> void:
    var logic := SaveLogic.new(FakeWriter.new(), FakeClock.new())
    assert_int(logic.save_if_dirty("ignored")).is_equal(OK)

func test_dirty_cleared_only_on_successful_write() -> void:
    var w := FakeWriter.new()
    var logic := SaveLogic.new(w, FakeClock.new())
    logic.set_value("room", "sunset")
    w.next_error = ERR_FILE_CANT_WRITE
    logic.save_if_dirty("ignored")
    assert_bool(logic.dirty).is_true()      # failed write must NOT clear dirty
```

These tests run in milliseconds, in parallel, with zero environmental setup — because the *core* never knew it lived in a game. The shell still deserves a few integration tests, but the ratio flips: hundreds of core tests, a handful of shell tests.

### 16.3 Seam 2 — swapping autoloads at runtime in integration tests

For tests of code you *can't* refactor yet, replace the manager node itself before the scene under test loads. The autoload is just a child of `/root` with a known name — so substitute it:

```gdscript
# Test helper: replace /root/SaveManager with a stub for this test's duration.
func swap_autoload(autoload_name: String, stub: Node) -> Node:
    var root := get_tree().root
    var original := root.get_node(autoload_name)
    original.name = autoload_name + "_original"     # step aside, keep alive
    stub.name = autoload_name
    root.add_child(stub)
    return original                                  # restore in teardown!

func restore_autoload(autoload_name: String, original: Node) -> void:
    var stub := get_tree().root.get_node(autoload_name)
    stub.queue_free()
    original.name = autoload_name
```

Honest caveats, because this seam is sharp: node-path lookups (`get_node("/root/SaveManager")`) now hit the stub, **but the parse-time global name may still reference the original object** depending on binding — which is precisely why direct-global-name code is the hardest to test, and why the injected-with-fallback access pattern (Section 2.3-D) and the service locator (7.5) exist. Restore in `after_test`/teardown *always*, or you've leaked a stub into every subsequent test — the classic "tests pass alone, fail in suite" generator.

Framework support narrows the pain: **GUT** can create doubles/partial doubles of your classes and even documented doubling of engine singletons (`Input`, `Time`, `OS`) with stubbing and spying; **GdUnit4** ships mocks and spies plus a scene runner for driving scenes under test. Neither makes hard-bound *project* globals painless — the frameworks' own guidance converges on the same conclusion as this module: design the seam in (16.2), don't fight the binding (16.3) forever.

### 16.4 Seam 3 — test-mode flags for the unavoidable

Some managers are infrastructural enough that tests want them *present but inert* — the logger, the performance sampler. Give them an environment-controlled quiet mode, set before the roster boots:

```gdscript
# app_logger.gd
func _ready() -> void:
    if OS.get_environment("RELAX_TEST_MODE") == "1":
        _sink = MemorySink.new()      # tests can assert on log lines!
        return
    _sink = FileSink.new(LOG_PATH)
```

A CI job exports `RELAX_TEST_MODE=1` and the whole roster boots side-effect-free. This is a blunt instrument — prefer it only for cross-cutting infrastructure, not as an alternative to real seams for domain logic.

### 16.5 Framework sketches: the same test in GUT, and wiring tests with the scene runner

The 16.2 unit test translated to **GUT** — mechanically different, philosophically identical:

```gdscript
# test/unit/test_save_logic_gut.gd
extends GutTest

func test_dirty_cleared_only_on_successful_write() -> void:
    var w := FakeWriter.new()
    var logic := SaveLogic.new(w, FakeClock.new())
    logic.set_value("room", "sunset")
    w.next_error = ERR_FILE_CANT_WRITE
    logic.save_if_dirty("ignored")
    assert_true(logic.dirty, "failed write must not clear the dirty flag")

func test_writer_called_once_per_dirty_save() -> void:
    # GUT's doubles shine when you'd rather verify INTERACTIONS than build fakes:
    var writer_double = double(AtomicFileWriter).new()
    stub(writer_double, "write_atomic").to_return(OK)
    var logic := SaveLogic.new(writer_double, FakeClock.new())
    logic.set_value("k", 1)
    logic.save_if_dirty("p")
    logic.save_if_dirty("p")                    # clean now — must not write again
    assert_called(writer_double, "write_atomic")
    assert_call_count(writer_double, "write_atomic", 1)
```

And a **GdUnit4 scene-runner** wiring test for layer 2 of the pyramid — verifying the *shell and scene* react to bus traffic, with the heavy managers stubbed via the 16.3 swap:

```gdscript
# test/integration/test_save_indicator.gd
extends GdUnitTestSuite

func test_toast_appears_on_save_completed() -> void:
    var runner := scene_runner("res://v1/scenes/ui/save_indicator.tscn")
    SignalBus.save_completed.emit(true)          # drive the wiring, not the logic
    await runner.simulate_frames(2)              # let deferred UI updates land
    var toast: Label = runner.get_property("_toast_label")
    assert_str(toast.text).contains("Saved")
```

The division of labor stays sharp: interaction verification (doubles, spies) for shells and wiring; state verification (plain fakes) for cores; the scene runner only ever drives *signals and frames*, never re-tests the logic the core tests already own.

> ✅ **Best practice** — The testing pyramid for an autoload-heavy project: (1) **most tests** target `RefCounted` cores with constructor-injected fakes — no engine anything; (2) **some tests** boot scenes against stubbed/swapped managers to verify wiring; (3) **few tests** run the true full roster end-to-end (boot → decorate → save → reload → assert persistence). If layer 1 is thin and layer 3 is thick, the architecture — not the test suite — is what needs work.

---

## 17. Memory and Lifecycle

### 17.1 Autoloads never die — so their garbage never dies either

A gameplay node's memory mistakes are self-limiting: the scene is freed, its subtree goes with it. An autoload has no such absolution — **whatever an autoload accumulates, it keeps until process exit.** The leak patterns are predictable:

- **Ever-growing collections.** `AppLogger`'s in-memory ring of recent lines, `PerformanceManager`'s samples array, an undo history, a "recently placed decorations" list — any `append` without a corresponding trim grows for the entire session. In a companion app designed to run for *eight hours in the background*, a leak that would be invisible in a 20-minute game session becomes hundreds of MB. Cap everything: ring buffers, `if arr.size() > MAX: arr = arr.slice(-MAX)`.
- **References to dead scenes.** An autoload that stored `var last_selected: Node2D` keeps that reference after the scene died. With `Node` (not RefCounted) the object is truly freed — the reference becomes invalid, and touching it is the "previously freed instance" error. The check is `is_instance_valid()`; the cure is not storing scene nodes in autoloads at all (store IDs/data, resolve to nodes on demand), or weak references (below).
- **Signal connections from freed objects** are auto-cleaned by the engine, but *Callable captures* in `Array[Callable]` job queues, tween references, and lambda captures are not — a queued callable holding a strong reference to a `RefCounted` keeps it alive forever; holding a freed `Node` makes the callable a landmine.
- **Orphan nodes** created by autoloads but never parented (`Node.new()` kept in a var, or `instantiate()` without `add_child`) are invisible to tree teardown. The debugger's **Monitors → Object → Orphan Nodes** counter and `print_orphan_nodes()` in a debug console exist for exactly this audit — a companion app should hold a flat orphan count over hours.

### 17.2 weakref for caches

When an autoload legitimately caches objects whose lifetime *belongs to someone else*, hold them weakly so the cache never becomes the reason memory can't be reclaimed:

```gdscript
# performance_manager.gd — tracks live panels WITHOUT keeping them alive.
var _watched: Dictionary = {}    # instance_id (int) -> WeakRef

func watch(panel: Control) -> void:
    _watched[panel.get_instance_id()] = weakref(panel)

func sample_panels() -> void:
    for id in _watched.keys():
        var wr: WeakRef = _watched[id]
        var panel: Object = wr.get_ref()      # null if freed — never a crash
        if panel == null:
            _watched.erase(id)                # self-cleaning cache
            continue
        _sample_one(panel as Control)
```

`weakref(obj)` returns a `WeakRef` whose `get_ref()` yields the object or `null` once it's gone — for `RefCounted` targets it also doesn't count toward the refcount, so the cache never *prevents* reclamation. The sweep-on-access pattern above keeps the dictionary from accumulating tombstones.

### 17.3 Exit: the last responsibility

Shutdown is startup's mirror, and autoloads see it twice:

**`_exit_tree()` — the teardown hook.** At quit, the tree tears down and autoloads exit in **reverse registration order** (last in, first out — the tree removes children accordingly) — so `PerformanceManager` exits first and `SignalBus` last, meaning each manager can still reach its *upstream* dependencies during its own teardown, symmetric with boot. Use it to join threads (10.4's `shutdown_blocking()`), flush buffers, close the DB.

**`NOTIFICATION_WM_CLOSE_REQUEST` — the save-on-close moment.** When the user clicks the window's X, the engine (with default `auto_accept_quit`) quits promptly — `_exit_tree` runs, but anything *asynchronous* may not get its chance. For an app whose core promise is "your room is always saved," take manual control:

```gdscript
# save_manager.gd — guaranteeing the final save.
func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    get_tree().set_auto_accept_quit(false)     # X now sends the notification ONLY

func _notification(what: int) -> void:
    if what == NOTIFICATION_WM_CLOSE_REQUEST:
        _final_save_and_quit()

func _final_save_and_quit() -> void:
    if _dirty:
        var err := _logic.save_if_dirty(Constants.SAVE_PATH)   # synchronous, atomic
        if err != OK:
            AppLogger.error("[SaveManager] final save failed: %d" % err)
    LocalDatabase.shutdown_blocking()          # drain the write queue (joins thread)
    AppLogger.flush()
    get_tree().quit()                          # NOW we actually exit
```

Rules of the close handler: it must be **fast** (users notice a close that takes seconds — atomic-write the JSON, drain the queue, go), it must be **unconditional about quitting** (never leave a path where the app eats the close and stays open — that's a bug report titled "can't close the app"), and exactly **one autoload owns it** (two managers both calling `set_auto_accept_quit(false)` and both quitting is a race to see whose cleanup gets skipped). On desktop, also note `NOTIFICATION_APPLICATION_FOCUS_OUT` as the natural autosave trigger for a companion app — save when the user alt-tabs away, and the close handler usually finds nothing dirty.

### 17.4 Worked example: a bounded, flush-disciplined logger

`AppLogger` is the autoload most likely to leak by a thousand appends — and the complete antidote fits in a page. Bounded memory, batched IO, pause-proof flushing, exit-safe:

```gdscript
# autoloads/app_logger.gd
extends Node
## Upstream: none (autoload #2). Bounded ring in memory, batched file writes.

const MAX_MEMORY_LINES := 500          # debug-console tail; hard cap
const FLUSH_INTERVAL := 5.0            # seconds between disk flushes

var _ring: Array[String] = []          # last MAX_MEMORY_LINES, for dump_state()
var _pending: PackedStringArray = []   # not yet on disk
var _file: FileAccess

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS       # log during pause, obviously
    _file = FileAccess.open("user://app.log", FileAccess.WRITE)
    var t := Timer.new()
    t.wait_time = FLUSH_INTERVAL
    t.timeout.connect(flush)
    add_child(t)                                  # inherits ALWAYS: ticks in pause
    t.start()

func info(msg: String) -> void: _log("INFO", msg)
func error(msg: String) -> void:
    _log("ERROR", msg)
    flush()                                       # errors hit disk IMMEDIATELY

func _log(level: String, msg: String) -> void:
    var line := "%s [%s] %s" % [Time.get_datetime_string_from_system(), level, msg]
    _ring.append(line)
    if _ring.size() > MAX_MEMORY_LINES:
        _ring = _ring.slice(-MAX_MEMORY_LINES)    # the cap that prevents the leak
    _pending.append(line)

func flush() -> void:
    if _file == null or _pending.is_empty():
        return
    for line in _pending:
        _file.store_line(line)
    _file.flush()                                 # actually reach the OS
    _pending.clear()

func _exit_tree() -> void:
    flush()                                       # the backstop: nothing pending at exit
```

Every Section 17 rule appears in miniature: the cap (17.1), a flush timer that survives pause (15.3), errors flushed eagerly so a crash immediately after still leaves evidence, and the `_exit_tree` backstop that pairs with `SaveManager`'s close handler (17.3) — which calls `AppLogger.flush()` explicitly *before* `quit()`, because by `_exit_tree` time you want the flush to find nothing left to do.

> ✅ **Best practice** — Write each manager's lifecycle as a symmetric story: `_ready` (wire) → `start()` (acquire) → session (`reset()` between users) → `shutdown` (release, reverse order) → `_exit_tree` (backstop asserts: thread joined? queue empty? file closed?). If releasing a resource has no designated line in that story, that resource leaks by default — autoloads never get the scene-death amnesty.

---

## Best practices

The module's discipline, compressed into a review-ready checklist:

**Registration & order**
1. Treat the `[autoload]` list as a topologically-sorted dependency graph; every dependency points *upward*. Document the graph (README quick-reference card) and keep it current.
2. Review any diff touching `[autoload]` like a schema migration; after `project.godot` merge conflicts, re-verify the section visually and by running.
3. Name autoloads `PascalCase`, files `snake_case`; no `class_name` inside autoload scripts; a `##` contract header on line one (owns / upstream / emits).
4. Default to script autoloads; scene autoloads only for real node subtrees (AudioManager's player pool).

**Initialization**
5. `_init` pure; `_enter_tree`/`_ready` connect upward only; assert upstream presence with named, actionable messages.
6. Two-phase init for anything slow or fallible: `_ready` wires, `start()` works, one boot orchestrator owns phase-2 order and failure UI.
7. Never put side effects inside `assert()` — it is compiled out of release builds. Assert programmer errors; `push_error` + recover for environment errors.
8. Keep the synchronous autoload chain under ~250 ms; move the rest behind the boot scene's progress bar.

**Architecture**
9. Burden of proof on every new autoload: whole-app scope? upstream set? reset story? why not a Section 7 alternative? Eight is a ceiling, not a target.
10. Static funcs for pure helpers; Resources for shared data; `@export` injection for components; scene-scoped managers for scene-lifetime coordination; the bus for cross-scene facts.
11. Bus rules: declarations only, typed parameters, past-tense fact names (`_requested` suffix for the documented command exceptions), contract comments, storm audits via the connection dump.

**Threads**
12. Climb the ladder — cache, frame-spread, engine async, `WorkerThreadPool`, dedicated `Thread` — and stop at the first rung that works. Profile first.
13. Workers never touch the tree; results cross via `call_deferred` at a single completion boundary; payloads are `duplicate()`d at the hand-off.
14. Every started `Thread` gets joined; every pool task gets waited; every worker has a shutdown message, not a murder.
15. Mutex guards data (reads included), held briefly, never across calls out; semaphores put idle workers to sleep — no polling loops in a companion app.

**Lifecycle**
16. Every stateful autoload implements `reset()`; the orchestrator calls them in boot order on session change; PRs adding state must touch `reset()`.
17. Set `process_mode = PROCESS_MODE_ALWAYS` deliberately on managers; audit pause behavior across whole chains (timers, tweens, awaits).
18. Cap every collection an autoload appends to; hold other-owned objects via `weakref`; watch the orphan-node monitor on long sessions.
19. One autoload owns `NOTIFICATION_WM_CLOSE_REQUEST`: fast synchronous save, drain queues, `quit()` unconditionally.
20. Structure managers as `RefCounted` core + thin shell; most tests hit the core with fakes, few tests hit the full roster.

---

## Common errors & troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Invalid access on a null instance" during startup, naming an autoload | Depending *downward*: touching an autoload listed below you during `_init`/`_enter_tree`/`_ready` | Reorder the `[autoload]` list so dependencies are above; add the Section 5.1 upstream assertions so the next occurrence self-diagnoses |
| "Identifier 'X' not declared in the current scope" all over the project | Autoload entry missing (merge conflict ate the line) or enable flag (`*`) lost; or name collides with a `class_name` | Check `[autoload]` in `project.godot`; restore the line/`*`; rename the colliding `class_name` |
| Works from the main scene, crashes when running a scene with F6 | Boot orchestrator never ran; managers stuck in phase 1 | Give test scenes a mini-boot, or make the touched APIs phase-tolerant; the `InitGuard` message tells you which call came early |
| Same startup crash but only on *some* machines / only in exported builds | Side effect inside `assert()` (stripped in release), or env-dependent init (missing file, locked DB) treated as programmer error | Move effects out of asserts; convert environment failures to `push_error` + recovery path; test release exports |
| Settings/audio revert to defaults until something re-triggers them | Order: consumer autoload readied before its data source loaded (e.g. AudioManager above SaveManager) | Fix order; or move the read to phase 2 / a `settings_updated` listener |
| Previous user's/session's state visible after logout or restart | No `reset()` protocol; autoloads (and `static var`s) persist through `reload_current_scene()` | Implement the Section 14.2 reset convention; include statics; enforce "new state field ⇒ reset() touched" in review |
| "Caller thread can't call this function in this node" | Worker thread touched a tree node or emitted a signal with node-touching listeners | Route through `call_deferred`/`set_deferred` at the completion boundary; build off-tree, attach on-main |
| Random crashes/corruption minutes after background work ran, often in unrelated code | Silent data race: shared Array/Dictionary resized without a mutex, shared Resource mutated cross-thread | Guard shared structures with `Mutex` (all accesses); prefer message passing with `duplicate()`d payloads |
| App freezes solid (not a crash) when saving/quitting | Deadlock: `wait_to_finish()` on a worker blocked on something only the caller provides; or lock-order inversion; or emit inside a locked region | Join only after completion signal; global lock ordering; never call out (signals/logging) while holding a mutex; shutdown = flag + `post()` + join |
| Background worker burns CPU while idle (companion app fans up) | Polling loop (`while true` + check) instead of blocking | Sleep the worker on a `Semaphore`; `post()` per enqueued job (Section 10.4) |
| `wait_for_task_completion()` returns `ERR_BUSY` | Waiting on a pool task from inside another pool task with circular dependency | Chain tasks via completion callbacks (`call_deferred`), don't block task-on-task |
| Autosave/music/crossfade freezes whenever a pause-style panel opens | Managers left on default `PROCESS_MODE_INHERIT`, paused with the tree | `process_mode = PROCESS_MODE_ALWAYS` on the manager; re-audit its child Timers and tweens per Section 15.3 |
| Coroutine in an autoload crashes with "previously freed instance" after a scene change | `await` resumed after `change_scene_to_file` freed the captured nodes | `is_instance_valid()` recheck after every await that holds scene references; epoch counter to abandon stale continuations |
| An awaited operation never completes; feature silently dead until restart | Awaiting a signal that doesn't fire on error paths; or an in-flight flag never cleared after an interrupted operation | Guarantee emission on all paths (`save_completed(false)`); clear flags in `reset()`; timeout-race long awaits |
| Memory grows over hours; Orphan Nodes monitor climbs | Uncapped collections in autoloads; strong refs to dead scenes; unparented nodes | Ring-buffer/caps; store IDs not nodes, or `weakref`; audit with `print_orphan_nodes()` |
| Save file occasionally truncated/corrupt after a crash or forced close | Non-atomic write, or quit path skipping the flush | Atomic temp-file + rename writer; own `NOTIFICATION_WM_CLOSE_REQUEST` with `set_auto_accept_quit(false)` and a synchronous final save |
| Engine crash at quit referencing an autoload | Autoload was `free()`d/`queue_free()`d at runtime; or a started `Thread` never joined | Never free autoloads (use an `enabled` flag); join all threads in `_exit_tree` |
| A bus signal emitted during boot is never received | Emitter autoload ran before the listener autoload (or scene) connected — emissions are not queued for future listeners | Don't emit facts during autoload `_ready`; emit from phase 2 after the orchestrator confirms listeners exist, or have late joiners *pull* current state instead of waiting for a past event |
| Scene-autoload's `@onready` child reference is null | The autoload was registered as a *script* path while the code assumes the scene's children; or the child was renamed in the `.tscn` | Register the `.tscn` (not the `.gd`) in `[autoload]`; prefer `%UniqueName` references over path-brittle `$Child/Sub` |
| `start()` runs twice (double boot) after adding a retry/reload path | Boot orchestrator re-entered without idempotence | Keep the `if _is_started: return OK` guard from Section 5.2 in every `start()`; make `reset()` (not a second `start()`) the session-restart path |
| Tool script or editor plugin errors with "Identifier not declared" on a manager name | Autoloads don't exist in the editor's tree; `@tool` code touched a global | Gate with `Engine.is_editor_hint()`; read `ProjectSettings.get_setting("autoload/...")` if you only need the registration data (Section 2.5) |

---

## Exercises

Labs 1-3 preserve (and deepen) the original module's exercises; 4-10 extend into this edition's territory. Each lab lists acceptance criteria — treat them as a definition of done, not a suggestion.

### Lab 1 — The autoload graph *(original lab, upgraded)*
Map every autoload in your project (or Relax Room's eight). Draw the dependency graph; verify the `[autoload]` list is a valid topological order — noting this means checking *list position*, not alphabetical order.
**Acceptance criteria:** a diagram (ASCII is fine) with every init-time dependency as an upward edge; a one-line justification of each autoload's position; at least one documented pair of independent autoloads whose order is conventional, not required.
**Stretch:** write a `--headless` boot script that `print`s the ready-order trace (Section 3.6) and diff it against your diagram in CI.

### Lab 2 — Assert and recover *(original lab, upgraded)*
Add init-time assertions to two autoloads: upstream-presence asserts plus one config/schema assert each. Deliberately misconfigure (reorder the list; delete a config file) and observe the failures.
**Acceptance criteria:** wrong order produces a named, actionable message in ≤1 s; the *environment* failure (missing file) does **not** use `assert` — it `push_error`s and recovers; a release export still handles the environment failure (proving no side effects lived in asserts).
**Stretch:** add the `InitGuard` (5.3) to one manager and demonstrate the "called in phase READY" diagnosis under F6.

### Lab 3 — The hexagonal refactor *(original stretch, now a full lab)*
Take one logic-heavy autoload and split it: `RefCounted` core with constructor-injected collaborators + thin node shell (Section 16.2).
**Acceptance criteria:** the core file contains no autoload names, no `extends Node`, no direct file IO; ≥5 unit tests run against the core with fakes (including one failure-path test, e.g. dirty-flag preserved on failed write); the shell is under ~60 lines; the app behaves identically.
**Stretch:** measure test-suite runtime before/after; report the ratio.

### Lab 4 — Break the chain on purpose
Fork your project settings and enact three reorderings from Section 4.2's table (or their analogs in your project). For each, *predict in writing* the first observable failure, then run and compare.
**Acceptance criteria:** three written predictions with failure class (loud crash / silent misbehavior / cosmetic); actual results recorded; at least one mismatch analyzed (why did reality differ?).
**Stretch:** convert the worst *silent* failure into a *loud* one with a single assertion, and prove it.

### Lab 5 — Two-phase boot with a loading screen
Introduce a boot scene that drives phase-2 `start()` across your managers in an explicit array, with a progress bar and an error panel.
**Acceptance criteria:** engine-phase (`_ready`) work per autoload is trivially fast; boot order lives in exactly one reviewable place; a simulated `start()` failure (return `ERR_CANT_OPEN`) shows the error UI instead of crashing; total boot including UI stays under your budget.
**Stretch:** make one `start()` internally async (thread or `WorkerThreadPool`) with the progress bar advancing during it.

### Lab 6 — The guarded queue
Implement the Section 10.4 producer-consumer writer (SQLite, or plain file appends if no DB addon): main thread enqueues, one long-lived worker drains, semaphore-slept when idle.
**Acceptance criteria:** UI thread never blocks on a write (prove with a frame-time overlay while spamming writes); CPU is ~0% when idle (no polling); `shutdown_blocking()` drains the queue — kill the app mid-burst and verify nothing enqueued was lost; all worker→main communication goes through `call_deferred`.
**Stretch:** inject a failing write and verify the error surfaces on the main thread via the bus without crashing the worker loop.

### Lab 7 — Signal bus audit
Run the connection-dump tool (8.4) against your bus. Produce the wiring table: signal → emitters (grep) → listeners (dump).
**Acceptance criteria:** every signal has ≥1 listener or a removal ticket; every signal has a contract comment (emits/listens/params); at least one storm risk identified and either refuted or guarded (re-entrancy flag); naming pass done (facts past-tense, commands `_requested`).
**Stretch:** add the dev-build tracing bus and capture one user action's full event narrative as a log excerpt.

### Lab 8 — Reset protocol and the leak hunt
Implement `reset()` across your stateful autoloads plus the `session_reset` broadcast; then hunt leaks: play, `reload_current_scene()`, and inspect.
**Acceptance criteria:** a written per-manager list of what `reset()` clears *and deliberately keeps* (wiring, handles); after logout→login as another profile, zero fields observably leak (write the checklist of fields you verified); one `static var` included in the protocol or eliminated; Orphan Nodes count flat across five reload cycles.
**Stretch:** add a debug console command `dump_state()` per manager and diff its output pre/post reset automatically.

### Lab 9 — Save-on-close, end to end
Own the quit path: `set_auto_accept_quit(false)`, `NOTIFICATION_WM_CLOSE_REQUEST` handler with synchronous final save, queue drain, `quit()`.
**Acceptance criteria:** clicking X with dirty state produces a valid save (verify by relaunching); close-to-gone stays under 500 ms; no path exists where the app refuses to close; a second manager attempting to own the notification is detected (assert or review rule).
**Stretch:** add `NOTIFICATION_APPLICATION_FOCUS_OUT` autosave and show the close handler then usually finds a clean state.

### Lab 10 — Resumption safety under fire
Write an autoload coroutine that awaits a 2-second SceneTree timer and then modifies a node in the current scene. Trigger it, then immediately `change_scene_to_file()` — and watch it fail. Now harden it.
**Acceptance criteria:** the naive version demonstrably errors (or silently no-ops) on resumption; the hardened version applies all three Section 13.2 questions — `is_instance_valid()` recheck, an epoch counter abandoning stale continuations, and a documented answer to "does my awaited signal always fire?"; a pause-interaction check: the timer's `process_always` choice is deliberate and written down.
**Stretch:** build the timeout-race helper (13.2, question 3) as a reusable utility and adopt it at two call sites.

### Self-assessment
Answer without looking, then verify against the sections:
1. Exactly which callbacks has autoload #4 completed when autoload #5's `_init` runs? *(§3.2)*
2. How is autoload init order determined — and what is the widespread wrong answer? *(§3.1)*
3. Why is an autoload not thread-safe by default, and what is the one sanctioned bridge back to the main thread? *(§9, §11)*
4. Give an init-time assertion that names its own fix, and explain why its condition must be side-effect-free. *(§5.1)*
5. Name three alternatives to a new autoload and the situation where each wins. *(§7)*
6. What persists across `reload_current_scene()`, and what protocol compensates? *(§14)*
7. Why does a semaphore-based worker beat a polling worker in a desktop companion app specifically? *(§10.4, §12.2)*

---

## Further reading

Official documentation first — these are the primary sources this module was verified against (all Godot 4.x, stable channel):

- **Godot Docs — Singletons (Autoload)** — <https://docs.godotengine.org/en/stable/tutorials/scripting/singletons_autoload.html> — The canonical reference for registration, the Globals UI, load-before-main-scene semantics, list ordering, and the do-not-free warning. Read it once fully; most autoload folklore is a distortion of this page.
- **Godot Docs — Autoloads versus regular nodes** — <https://docs.godotengine.org/en/stable/tutorials/best_practices/autoloads_versus_internal_nodes.html> — The engine's own case *against* over-globalizing, built on the audio-manager example; source of the "wide scope" criterion and the static-function alternative. The best 10-minute read in this module's bibliography.
- **Godot Docs — Using multiple threads** — <https://docs.godotengine.org/en/stable/tutorials/performance/using_multiple_threads.html> — Thread/Mutex/Semaphore fundamentals, the suspended-worker example, thread-creation cost warnings. Pair with the next entry; neither is complete alone.
- **Godot Docs — Thread-safe APIs** — <https://docs.godotengine.org/en/stable/tutorials/performance/thread_safe_apis.html> — The authoritative safe/unsafe list: scene-tree interaction rules, `call_deferred` idioms, servers, arrays/dictionaries, AStar caveats. The page to re-check *every time* before threading against an engine API.
- **Godot Class Reference — `Thread`, `Mutex`, `Semaphore`** — <https://docs.godotengine.org/en/stable/classes/class_thread.html> — Exact signatures and the disposal rules (join before destruction, no locked mutexes) that Section 10 encodes.
- **Godot Class Reference — `WorkerThreadPool`** — <https://docs.godotengine.org/en/stable/classes/class_workerthreadpool.html> — Task and group-task APIs, the mandatory-wait rule, `ERR_BUSY` circular-wait caveat, and the docs' own guidance on when the pool hurts.
- **Godot Docs — Pausing games and process mode** — <https://docs.godotengine.org/en/stable/tutorials/scripting/pausing_games.html> — The `process_mode` matrix underlying Section 15.
- **GDQuest — Glossary: Autoload / Singleton** — <https://www.gdquest.com/library/glossary/autoload/> — Community-standard framing of the autoload-vs-singleton distinction and measured "use for whole-game systems only" guidance; a good link to hand a teammate who wants the short version.
- **GUT documentation — Doubling (including singletons)** — <https://gut.readthedocs.io/> — Doubles, partial doubles, stubbing and spying for Godot 4, including the documented approach to doubling engine singletons; relevant to Section 16.3's limits.
- **GdUnit4 — Embedded testing framework for Godot 4** — <https://github.com/godot-gdunit-labs/gdUnit4> — Mocking, spies, and the scene runner used in Section 16's examples.
- **In this repo:** [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) (the Relax Room architecture this module dissects), [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md) (WAL, atomic writes — the payloads our worker threads carry), [GAME_DEV_PLANNING.md](GAME_DEV_PLANNING.md) (testing strategy context), [SCENES_AND_NODES.md](SCENES_AND_NODES.md) (node lifecycle prerequisites), and the [README](README.md) quick-reference card (the canonical autoload-order table).

---

## Glossary

| Term | Definition |
|---|---|
| **Autoload** | A node (script-backed or scene) the engine adds under `/root` before the main scene, registered in Project Settings and persisting until quit. Godot's "singleton" mechanism — by convenience, not enforcement. |
| **Singleton (pattern)** | OOP pattern enforcing one instance with global access. Autoloads provide the access but not the enforcement — nothing stops manual instantiation. |
| **`[autoload]` section** | The plain-text block in `project.godot` holding `Name="*res://path"` entries; line order is initialization order; `*` marks the global name as enabled. |
| **Initialization order** | The top-to-bottom Project Settings list order in which autoloads are constructed and readied — each completing `_init` → `_enter_tree` → `_ready` before the next begins. Not alphabetical. A safe list is a topological order of the manager dependency graph. |
| **Two-phase initialization** | Splitting managers into a cheap infallible `_ready()` (wire) and an explicit `start()` (acquire/load) driven by a boot orchestrator that owns phase-2 order and failure handling. |
| **InitGuard** | A small `RefCounted` tracking a manager's lifecycle phase (CREATED/READY/STARTED/STOPPED) and converting early API calls into precise named errors. |
| **Init-time assertion** | An `assert()` in startup code verifying order, config or schema so misconfiguration fails loudly at boot. Stripped from release builds — never give it side effects. |
| **Signal bus** | An autoload consisting solely of signal declarations; emitters and listeners decouple through it. Safe as a global precisely because it is stateless. |
| **Signal storm** | Cascading re-emission where one event triggers listeners that emit further events, fanning out or cycling; contained by facts-not-commands design and re-entrancy guards. |
| **Service locator** | A single registry autoload through which services are registered and resolved by name — trading compile-time binding for runtime substitutability (tests inject fakes). |
| **Dependency injection** | Supplying a component's collaborators from outside (constructor args, `@export` slots) instead of the component reaching for globals — the foundation of testable seams. |
| **Main thread** | The thread running the game loop and owning the `SceneTree`. All node access, signal delivery to node listeners, and UI belong to it. |
| **Data race** | Two threads accessing the same data with at least one write and no synchronization; produces intermittent, unreproducible corruption — the defining threading hazard. |
| **`Mutex`** | Mutual-exclusion lock (`lock`/`unlock`/`try_lock`) ensuring one thread at a time inside a guarded region. Guard the data, hold briefly, never call out while holding. |
| **`Semaphore`** | Counting synchronization primitive (`wait`/`post`/`try_wait`); canonically used to sleep a worker until work exists — the zero-CPU idle pattern. |
| **Guarded queue** | Producer-consumer pattern: mutex-protected queue + semaphore wake-ups + a long-lived worker thread; the backbone of background writers (DB, files). |
| **`call_deferred` / `set_deferred`** | Enqueue a call/assignment on the engine's MessageQueue for execution by the main thread at idle time — both the sanctioned worker→main bridge and a same-thread timing escape. |
| **`WorkerThreadPool`** | Engine-managed thread pool for one-shot tasks (`add_task`) and data-parallel group tasks (`add_group_task`); every task must eventually be waited for. |
| **Coroutine (`await`)** | A function suspended at `await` (signal/timer/coroutine) and resumed later on the main thread; cooperative concurrency with visible suspension points and no data races. |
| **Resumption safety** | The discipline of re-validating the world after every `await`: captured nodes may be freed (`is_instance_valid`), state stale (re-check/epoch counters), the awaited signal may never fire (timeout race). |
| **`process_mode`** | Per-node pause behavior (`INHERIT`/`PAUSABLE`/`WHEN_PAUSED`/`ALWAYS`/`DISABLED`). Managers almost always want `PROCESS_MODE_ALWAYS`, set deliberately in `_ready()`. |
| **Reset protocol** | The `reset()`-plus-broadcast convention returning persistent autoload state to session defaults, in boot order, since scene reloads never touch autoloads. |
| **`WeakRef`** | A non-owning reference created by `weakref()`; `get_ref()` yields the object or `null` after it's freed — the correct way for autoload caches to track objects they don't own. |
| **`NOTIFICATION_WM_CLOSE_REQUEST`** | The window-close notification; with `set_auto_accept_quit(false)`, one designated autoload intercepts it to perform the final synchronous save and queue drain before `quit()`. |
| **Hexagonal split (core + shell)** | Structuring a manager as a pure `RefCounted` core with injected collaborators plus a thin autoload shell owning tree concerns — the pattern that makes autoload-heavy codebases unit-testable. |

---

*Module 13 of "Godot 4 in Production" · Previous: [SCENES_AND_NODES.md](SCENES_AND_NODES.md) foundations · Case study throughout: [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) · Persistence internals: [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md)*

