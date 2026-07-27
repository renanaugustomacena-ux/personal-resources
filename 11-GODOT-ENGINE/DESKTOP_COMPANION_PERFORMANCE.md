---
course: "Godot 4 in Production"
phase: "5 — Specialized modules"
module: "14"
title: "Desktop Companion Performance — Frame Budgets, Idle Efficiency and Profiling"
version: "Godot 4.5 / GDScript 2.0"
level: "Advanced"
prerequisites: [ "GODOT_ENGINE_STUDY.md", "RENDERING_AND_VISUAL_LOGIC.md" ]
objectives:
  - "Define and defend numeric performance budgets for a desktop companion app (idle CPU, active FPS, RAM slope, battery impact)"
  - "Implement a production-grade adaptive FPS manager driven by focus, input activity and window state"
  - "Configure low processor usage mode, VSync modes and physics tick rate for minimal idle footprint"
  - "Profile CPU, GPU and memory with the Godot profiler, Monitors tab and custom Performance monitors"
  - "Hunt memory leaks (orphan nodes, tween and signal leaks) and run a 24-hour soak test with logged metrics"
  - "Integrate with the OS: tray icon via StatusIndicator, minimize-to-tray, window geometry persistence, single-instance guard"
  - "Verify in-engine numbers against OS-level tools (Task Manager, powercfg, htop) before declaring victory"
tags: [godot, gdscript, performance, profiling, fps-budget, low-power, desktop-app, vsync, memory-leaks, system-tray, optimization, soak-testing]
---

# Desktop Companion Performance — Frame Budgets, Idle Efficiency and Profiling — Complete Guide

> **Module 14** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Godot Engine Study](GODOT_ENGINE_STUDY.md), [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) · Recommended: [Autoload Safety](AUTOLOAD_SAFETY.md), [Shaders](SHADERS_GDSHADER.md)
>
> By the end of this module you will be able to:
> 1. Explain why a desktop companion's KPI is "unnoticeable while alive for 8 hours" and translate that into numeric budgets (idle ≤ 1% CPU, active 60 FPS, flat RAM over 24 h, near-zero battery impact).
> 2. Implement the 15/60 dual-FPS-budget model as a full adaptive `PerformanceManager` autoload reacting to focus, input and minimize events.
> 3. Choose and justify a VSync mode, a `low_processor_usage_mode` configuration and a physics tick rate for a mostly-idle app.
> 4. Run the Godot profiler and Monitors tab methodically: reproduce, measure, rank by self time, fix the top item, re-measure.
> 5. Build a metrics HUD and a CSV metrics logger using `Performance`, `RenderingServer.get_rendering_info()` and `FileAccess`, and validate results against OS tools.
> 6. Detect and fix the classic long-session leaks: orphan nodes, looping tweens, accumulating signal connections, unbounded caches.
> 7. Ship OS-integration features (tray icon, minimize-to-tray, always-on-top, geometry restore) without wrecking the power budget.
>
> **Estimated time:** 8–10 hours reading and labs · **Level:** Advanced

## Guiding ideas

1. **A desktop companion is judged by its absence: the best performance review is the user forgetting it is running.**
2. **Budgets are numbers, not adjectives — "fast" is not a spec; "idle ≤ 1% CPU on a 2020 laptop" is.**
3. **The 15/60 dual budget: 15 FPS (or less) when idle or unfocused, 60 FPS the instant the user interacts.**
4. **Profile before optimizing — "I think it's slow" is not data; the profiler shows truth.**
5. **Every wakeup costs battery: prefer events and timers over per-frame polling, always.**
6. **In-engine numbers lie about total footprint — the OS task manager has the final word.**

## Concept map

```
                        ┌──────────────────────────────────────┐
                        │   DESKTOP COMPANION PERFORMANCE      │
                        │   "unnoticeable for 8 hours"         │
                        └──────────────────┬───────────────────┘
                                           │
        ┌──────────────────┬───────────────┼────────────────┬──────────────────┐
        │                  │               │                │                  │
┌───────▼───────┐  ┌───────▼───────┐ ┌─────▼──────┐ ┌───────▼───────┐ ┌────────▼────────┐
│ FRAME PACING  │  │  OS / WINDOW  │ │ PROFILING  │ │    MEMORY     │ │  MEASUREMENT    │
│               │  │  INTEGRATION  │ │            │ │  DISCIPLINE   │ │  & VERIFICATION │
├───────────────┤  ├───────────────┤ ├────────────┤ ├───────────────┤ ├─────────────────┤
│ Engine.max_fps│  │ focus signals │ │ Profiler   │ │ orphan nodes  │ │ metrics HUD     │
│ VSync modes   │  │ minimize/tray │ │ Monitors   │ │ tween leaks   │ │ CSV logging     │
│ low_processor │  │ StatusIndica- │ │ custom     │ │ caches/weakref│ │ Task Manager    │
│ _usage_mode   │  │ tor (4.3+)    │ │ monitors   │ │ soak testing  │ │ powercfg / htop │
│ physics ticks │  │ always-on-top │ │ Visual     │ │ VRAM monitors │ │ before/after    │
│ set_process   │  │ transparency  │ │ Profiler   │ │ print_orphan_ │ │ benchmarks      │
│ discipline    │  │ DPI/geometry  │ │ (GPU)      │ │ nodes()       │ │                 │
└───────┬───────┘  └───────┬───────┘ └─────┬──────┘ └───────┬───────┘ └────────┬────────┘
        │                  │               │                │                  │
        └──────────────────┴───────────────┼────────────────┴──────────────────┘
                                           │
                        ┌──────────────────▼───────────────────┐
                        │  RELAX ROOM: PerformanceManager      │
                        │  ACTIVE 60 ─ IDLE 15 ─ HIDDEN 5 FPS  │
                        │  + shader gating + metrics logger    │
                        └──────────────────────────────────────┘
```

## Table of contents

1. [The Desktop-Companion Performance Philosophy](#1-the-desktop-companion-performance-philosophy)
2. [Defining Performance Budgets](#2-defining-performance-budgets)
3. [Anatomy of a Godot Frame](#3-anatomy-of-a-godot-frame)
4. [Frame Pacing with Engine.max_fps](#4-frame-pacing-with-enginemax_fps)
5. [VSync Strategies with DisplayServer](#5-vsync-strategies-with-displayserver)
6. [Low Processor Usage Mode](#6-low-processor-usage-mode)
7. [Physics Ticks and Process Discipline](#7-physics-ticks-and-process-discipline)
8. [Focus, Minimize and Throttling Policies](#8-focus-minimize-and-throttling-policies)
9. [Window Styling and Multi-Monitor Concerns](#9-window-styling-and-multi-monitor-concerns)
10. [System Tray Integration with StatusIndicator](#10-system-tray-integration-with-statusindicator)
11. [Profiling Workflow](#11-profiling-workflow)
12. [GDScript Micro-Costs and Offloading Work](#12-gdscript-micro-costs-and-offloading-work)
13. [GPU Optimization for Idle Scenes](#13-gpu-optimization-for-idle-scenes)
14. [Memory Discipline and Leak Hunting](#14-memory-discipline-and-leak-hunting)
15. [Startup Time and Background Loading](#15-startup-time-and-background-loading)
16. [Measuring Like an Engineer](#16-measuring-like-an-engineer)
17. [Case Study: Relax Room PerformanceManager](#17-case-study-relax-room-performancemanager)
18. [Best practices](#best-practices)
19. [Common errors & troubleshooting](#common-errors--troubleshooting)
20. [Exercises](#exercises)
21. [Further reading](#further-reading)
22. [Glossary](#glossary)

---

## 1. The Desktop-Companion Performance Philosophy

Almost everything written about game performance assumes a game: a fullscreen application that owns the machine for a bounded session, where the user *expects* the fans to spin and the battery to drain, and where the single KPI is "hit the target frame rate during the heaviest combat scene." A desktop companion — a pomodoro timer with an animated mascot, an ambient soundscape player like our running case study **Relax Room**, a stream overlay controller, a hardware monitor widget — inverts every one of those assumptions.

A companion app:

- **Runs for hours or days**, not for a 45-minute session. It is started at login and closed at shutdown, if ever.
- **Spends 95–99% of its life ignored.** The user is writing code, browsing, or in a meeting. The app is minimized, behind other windows, or sitting in a corner of a second monitor.
- **Shares the machine with the user's real work.** Every CPU cycle it burns is stolen from a compiler, a browser, a video call. Every megabyte of RAM it holds is a megabyte the OS cannot give to something the user actually cares about right now.
- **Is judged by its absence.** Nobody praises a companion app for being efficient. They notice — and uninstall — when the laptop fan spins up while "nothing" is running, when the battery estimate drops by an hour, or when the machine feels sluggish and Task Manager points the finger.

This produces a KPI that sounds paradoxical for a real-time engine: **"unnoticeable while alive for 8 hours."** Concretely, that decomposes into four measurable dimensions:

| Dimension | Game mindset | Companion mindset |
|---|---|---|
| **CPU** | "Use the whole core budget to hit 60 FPS" | "Idle ≤ 1% of one core; be invisible in Task Manager" |
| **RAM** | "Fits in the target platform's memory" | "Flat over 24 h — zero growth, no leaks, no unbounded caches" |
| **Battery / energy** | "Players plug in to play" | "Near-zero impact on the laptop battery estimate" |
| **Thermals / acoustics** | "Fans are expected" | "Must never be the reason the fan spins up" |

### 1.1 Why a game engine at all?

If the constraints are so un-game-like, why build a companion in Godot instead of a native UI toolkit? Because the engine gives us animated characters, shaders, particles, audio mixing, tweens and a scene system that would take months to replicate — and because, as this module demonstrates, Godot 4 exposes every knob needed to behave like a polite desktop citizen: `Engine.max_fps`, `OS.low_processor_usage_mode`, `DisplayServer` VSync and window control, `StatusIndicator` for the tray, and a `Performance` API for self-measurement. The engine defaults are tuned for games; **our job in this module is to systematically un-tune them.**

The mental model to internalize: a game engine is a loop that wakes up, simulates, and draws — typically 60+ times per second, forever. Every technique in this module is a variation on one question:

> **"Does this frame actually need to happen, and if so, how cheap can it be?"**

If nothing on screen changed and no input arrived, the perfect companion frame costs *zero*: no wakeup, no script execution, no draw call, no GPU submission. We will not always reach zero, but every section that follows — frame caps, VSync, low-processor mode, process discipline, shader gating — is a tool for getting closer to it.

### 1.2 The three lives of a companion

Throughout this module we model the app as a small state machine with three power states. This is the backbone of the Relax Room `PerformanceManager` (section 17):

```
        input / focus                 focus lost + grace period
   ┌──────────────────────┐      ┌─────────────────────────────┐
   │                      ▼      │                             ▼
┌──┴──────┐          ┌────────────┐                     ┌─────────────┐
│ ACTIVE  │◄─────────┤    IDLE    │────────────────────►│   HIDDEN    │
│ 60 FPS  │  input   │  15 FPS    │  minimized / tray   │  ≤ 5 FPS or │
│ full FX │          │  FX gated  │                     │  no redraw  │
└─────────┘          └────────────┘                     └─────────────┘
```

- **ACTIVE** — the window has focus and the user interacted recently. Full 60 FPS, all effects on. This state must feel *instant*; any lag when the user comes back is perceived as brokenness.
- **IDLE** — the window is visible but unfocused, or focused with no input for a grace period. 15 FPS, ambient animations only, expensive shaders gated.
- **HIDDEN** — minimized or in the tray. Nothing is visible, so almost nothing should run: FPS floor (or event-driven redraw only), audio continues if the app is an audio app, everything else sleeps.

> ✅ **Best practice** — Design the power states *first*, then make every subsystem (particles, shaders, timers, network refreshes) subscribe to state changes. Retro-fitting throttling onto a finished app means hunting down dozens of `_process` methods; designing for it means one signal.

### 1.3 What this module is not

This is not a generic "optimize your game" module. We will barely mention LOD, occlusion culling, mesh instancing or physics broadphase tuning — the standard 3D game toolkit — because a 2D companion app rarely needs them. Conversely, we go far deeper than game-oriented material ever does on idle efficiency, OS integration, soak testing and energy measurement, because that is where companion apps live or die. For draw-call fundamentals see [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md); for shader cost details see [Shaders](SHADERS_GDSHADER.md).

---

## 2. Defining Performance Budgets

"Make it fast" is not an engineering requirement; it is a wish. Professional performance work starts by writing down **budgets**: numeric targets, measured under defined conditions, on defined hardware. A budget converts arguments ("it feels fine to me") into pass/fail tests, and it tells you when to *stop* optimizing — an underrated feature, because optimization past the budget is wasted effort that usually costs code clarity.

### 2.1 The reference machine

A budget without hardware attached is meaningless: 1% CPU on a 16-core desktop is a different amount of work than 1% on a 2-core ultrabook. Pick a **reference machine** near the low end of your audience and state it in the budget document. For Relax Room:

> Reference: dual-core/four-thread ultrabook class laptop (~2020), integrated GPU, 8 GB RAM, Windows 10/11, on battery, balanced power plan.

Everything below is defined against that machine. On stronger hardware you will simply be even further under budget.

### 2.2 The Relax Room budget sheet

| Metric | State | Budget | How measured |
|---|---|---|---|
| Frame rate | ACTIVE | 60 FPS sustained, no drops > 1 frame during interaction | in-app HUD + profiler |
| Frame rate | IDLE | ≤ 15 FPS (cap), frame time irrelevant | `Engine.max_fps` + HUD |
| Frame rate | HIDDEN | ≤ 5 FPS or event-driven only | HUD log + Task Manager |
| CPU | IDLE | ≤ 1% of total CPU (Task Manager, 60 s average) | OS tools (section 16) |
| CPU | HIDDEN | ≤ 0.3% of total CPU | OS tools |
| RAM (working set) | any | ≤ 220 MB after warmup; **slope ≈ 0 over 24 h** (< 5 MB/24 h drift) | soak test (section 14) |
| VRAM | any | ≤ 150 MB | `RENDER_VIDEO_MEM_USED` |
| Startup to interactive | cold | ≤ 2.5 s on reference machine | stopwatch log (section 15) |
| Battery impact | IDLE 8 h | not in the OS "high energy use" list; ≤ 2% of battery drain attributable | powercfg / Activity Monitor |
| Orphan nodes | any | 0 after every scene transition | `OBJECT_ORPHAN_NODE_COUNT` |

Notice several things about this sheet. Each row has a **state** column — budgets differ per power state, which is the whole point of the dual-budget model. Each row names a **measurement method** — a budget you cannot measure is a slogan. And the RAM row budgets the *slope*, not just the value: a companion that grows 2 MB/hour is fine for a game session and catastrophic for a two-week uptime.

### 2.3 The 15/60 dual budget, expanded

The core idea preserved from the first edition of this module: a desktop companion does not have *one* FPS target, it has (at least) two.

- **60 FPS when interactive.** When the user hovers, clicks, drags or types, the app must respond with the same fluidity as any native application. 60 FPS gives a 16.6 ms frame budget — generous for a 2D UI scene, which is exactly why we can afford rich visuals *in this state only*.
- **15 FPS when idle.** When the window is visible but the user is elsewhere, ambient motion (a breathing mascot, drifting particles, a slow gradient) still reads as "alive" at 15 FPS. Film runs at 24; a fireplace loop at 15 is perfectly convincing in peripheral vision. The payoff is massive: 4× fewer wakeups, 4× fewer draws, roughly 4× less energy than 60 FPS for the same scene.

Why 15 and not 30? Because the visual difference between 15 and 30 FPS for *ambient* motion in *peripheral vision* is nearly invisible, while the energy difference is 2×. And why not 1 FPS? Because at 1 FPS, ambient motion visibly stutters and the app reads as frozen; 10–15 FPS is the empirical floor for "alive." Your app may choose different numbers — the discipline is that you choose them *per state*, write them down, and enforce them in code.

The 4.x-era extension to the original two budgets is the third state: **HIDDEN**. When the window is minimized or in the tray, no pixels reach the user, so even 15 FPS is 15 wasted redraws per second. The budget drops to a floor that exists only to keep timers and audio serviced — or to zero redraws with `low_processor_usage_mode` (section 6).

### 2.4 Frame-time arithmetic you should internalize

| FPS cap | Frame budget | Wakeups per hour | Relative energy (rough) |
|---|---|---|---|
| 60 | 16.6 ms | 216,000 | 1.0× |
| 30 | 33.3 ms | 108,000 | ~0.5× |
| 15 | 66.6 ms | 54,000 | ~0.25× |
| 5 | 200 ms | 18,000 | ~0.08× |
| event-driven | n/a | ~0 when static | ~0 |

The "relative energy" column is deliberately rough — real energy use is not linear in FPS because of fixed costs (audio mixing, OS timers) — but the order of magnitude is right, and it explains why the single highest-leverage action in this entire module is *capping FPS by state*. No amount of micro-optimizing GDScript inside a 60 FPS loop competes with simply not running the loop 45 times per second.

> ⚠️ **Pitfall** — Do not confuse *frame budget* with *achieved frame time*. At `Engine.max_fps = 15` your frame budget is 66 ms, but your scene might render in 2 ms and sleep the rest. That is the goal: cheap frames, far apart. A 60 ms frame *time* at 15 FPS would mean you are nearly saturating a core even while idle — the cap hides the problem from the FPS counter but not from the CPU meter.

### 2.5 Writing your own budget sheet

A repeatable recipe:

1. **Pick the reference machine** (section 2.1) and the power states your app needs (usually the three above; a stream overlay might add a RECORDING state).
2. **For each state, budget the four dimensions**: CPU %, FPS cap, RAM ceiling + slope, and any app-specific metric (audio underruns for Relax Room).
3. **Attach a measurement method to every row.** If a row has no method, delete the row or invent the method (section 16 gives you the tooling).
4. **Automate what you can.** The metrics CSV logger from section 16 plus a spreadsheet gives you slope charts for free; the soak-test plan from section 14 turns the RAM row into a scheduled, repeatable experiment.
5. **Re-run the sheet before every release.** Budgets are regression tests for the machine's resources.

> ✅ **Best practice** — Keep the budget sheet in the repository next to the code (e.g. `docs/perf_budget.md`) and update the "measured" column with each release tag. A budget nobody re-measures decays into fiction within three releases.

---

## 3. Anatomy of a Godot Frame

Before touching any knob, you need a precise model of what the engine does between two frames, because every optimization in this module targets a specific segment of this loop. A simplified but accurate picture of one main-loop iteration in Godot 4:

```
┌───────────────────────── one main-loop iteration ─────────────────────────┐
│                                                                           │
│  1. OS event pump        input events, window messages (focus, resize)    │
│  2. Physics step(s)      0..N fixed ticks: _physics_process(delta),       │
│                          physics servers, collision, at                   │
│                          Engine.physics_ticks_per_second (default 60)     │
│  3. Process step         _process(delta), timers, tweens, animation       │
│  4. Rendering            RenderingServer culls, batches, submits          │
│                          draw calls; GPU executes; present (VSync)        │
│  5. Sleep / pacing       until max_fps allows the next frame, or          │
│                          low_processor_usage_mode_sleep_usec              │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

Key consequences for a companion app:

**Process and render rate are coupled; physics is not.** `_process()` runs once per rendered frame, so capping `Engine.max_fps` directly reduces script and render work. But the physics loop ticks at its own fixed rate (`Engine.physics_ticks_per_second`, default 60) *regardless of the render cap*. Cap your app to 15 FPS and physics still ticks 60 times per second — a classic surprise we fix in section 7.

**Timers and tweens run in the process step.** A `Timer` node or `SceneTree.create_timer()` callback fires during step 3, so at 15 FPS a 0.1 s timer quantizes to ~66 ms granularity. For a companion this is almost always fine; just do not build UI logic that assumes millisecond timer precision under a low cap.

**Input arrives even between renders.** The OS event pump runs every iteration, so a capped app still receives input promptly — the latency ceiling for *reacting* is one frame interval. At 15 FPS that is up to 66 ms, which is precisely why the adaptive manager in section 4 jumps to 60 FPS *on the first input event*, not after some polling delay.

**Sleeping is where the savings are.** Steps 1–4 for a small 2D scene might cost 1–3 ms. At 60 FPS uncapped-but-vsynced, the engine does that work 60 times per second. At 15 FPS it does it 15 times and spends the remaining ~93% of wall-clock time in step 5, costing essentially nothing. The companion discipline is to maximize time in step 5 — or, with `low_processor_usage_mode`, to skip steps 2–4 entirely when nothing changed.

### 3.1 Where the milliseconds go in a real companion scene

Profiling a representative Relax Room frame (ACTIVE state, reference laptop) gives a distribution like this — yours will differ, but the shape is typical for 2D companion apps:

| Segment | Typical cost | Notes |
|---|---|---|
| Script `_process` (all nodes) | 0.4–1.2 ms | tooltips, animations, UI updates |
| Physics tick | 0.05–0.3 ms | near-zero if physics barely used |
| 2D rendering CPU (RenderingServer) | 0.5–1.5 ms | proportional to CanvasItem count |
| GPU render | 0.5–2.0 ms | shaders, overdraw, particles |
| Audio mixing (separate thread) | constant background | independent of FPS |
| **Total busy time** | **~1.5–5 ms** | out of a 16.6 ms budget |

Read that table again with companion eyes: even the *active* frame uses under a third of its budget. The performance problem of a companion app is almost never "we can't hit 60 FPS." It is that this cheap frame **repeats forever**. Five milliseconds of work 60 times a second is 30% of one core, continuously, for eight hours — enough to be very visible in Task Manager and on the battery meter. The lever is *frequency*, not *frame cost*; frame cost matters again in the profiler section when we shave the busy time itself.

> ✅ **Best practice** — When reasoning about any change, ask two questions in order: (1) does it reduce how *often* work happens? (2) does it reduce how *much* work happens each time? Question 1 usually wins by an order of magnitude.

### 3.2 Delta discipline under variable caps

Because this module's whole strategy is *changing the frame rate at runtime*, any code that implicitly assumes a fixed rate becomes a bug the moment the cap switches. The `delta` parameter exists precisely for this: at 60 FPS it is ~0.0167, at 15 FPS ~0.0667, and multiplication by `delta` keeps motion speed constant across states.

```gdscript
# WRONG: drifts 4x slower in IDLE (assumes 60 FPS).
_glow_phase += 0.02

# RIGHT: identical wall-clock speed in every power state.
_glow_phase += 1.2 * delta
```

Audit for naked per-frame increments (`+= constant` inside `_process`) before enabling the adaptive manager — with a fixed 60 FPS they were invisibly wrong; with 15/60 switching they become visibly wrong, and the bug report will blame the FPS manager rather than the increment. Tweens, `AnimationPlayer` and particle systems are already time-based and adapt automatically; only hand-rolled `_process` math needs the audit.

---

## 4. Frame Pacing with Engine.max_fps

`Engine.max_fps` is the single most important property in this module. From the class reference: *"The maximum number of frames that can be rendered every second (FPS). A value of 0 means the framerate is uncapped."* It is an `int`, defaults to `0`, can be set at runtime at any moment, and takes effect immediately. The project-settings mirror is `application/run/max_fps`.

```gdscript
Engine.max_fps = 60   # cap to 60 FPS
Engine.max_fps = 15   # cap to 15 FPS
Engine.max_fps = 0    # uncap (never ship this state in a companion)
```

Three interactions you must understand before building the manager:

1. **VSync caps too.** With VSync enabled or adaptive, the monitor refresh rate is an additional ceiling. The *effective* frame rate is the minimum of the two: `max_fps = 15` on a 144 Hz monitor renders at 15; `max_fps = 240` on a 60 Hz monitor with VSync renders at 60. Setting a cap *below* the refresh rate is exactly our idle strategy and works under every VSync mode.
2. **`max_fps = 0` plus `VSYNC_DISABLED` is a space heater.** With no cap and no VSync the loop spins as fast as the hardware allows — hundreds or thousands of FPS, 100% of a core, GPU at full tilt. This combination must never be reachable in a shipped companion.
3. **`Engine.time_scale` is not a throttle.** `time_scale` scales the in-game clock (timers, tweens, `delta`), but the loop still runs at full frequency — `time_scale = 0.1` renders just as many frames per second as `1.0` and saves *zero* CPU. It is a gameplay/juice tool, not a power tool. If you want fewer frames, cap FPS; if you want fewer physics ticks, lower the tick rate.

> ⚠️ **Pitfall** — Do not try to emulate a frame cap with `OS.delay_msec()` inside `_process()`. It blocks the main thread (input included), fights the engine's own pacing, and produces jittery frame times. `Engine.max_fps` exists precisely so you never do this.

### 4.1 The adaptive FPS manager

Here is the heart of the module: a production-shaped autoload that implements the three-state model from section 1.2. It preserves and extends the original module's `PerfManager` (which switched 60/15 on focus); this version adds an input-driven idle grace period, a HIDDEN state for minimization, and a signal other systems subscribe to.

```gdscript
# autoloads/performance_manager.gd
extends Node
## Adaptive frame pacing for a desktop companion.
## Registered as "Perf" in Project Settings → Globals → Autoload.
## See AUTOLOAD_SAFETY.md for autoload ordering and threading rules.

enum PowerState { ACTIVE, IDLE, HIDDEN }

signal power_state_changed(new_state: PowerState)

const FPS_ACTIVE: int = 60
const FPS_IDLE: int = 15
const FPS_HIDDEN: int = 5
## Seconds of no input (while focused) before dropping to IDLE.
const IDLE_GRACE_SEC: float = 12.0
## How often we poll for minimization (there is no minimize signal).
const MODE_POLL_SEC: float = 1.0

var state: PowerState = PowerState.ACTIVE:
    set(value):
        if state == value:
            return
        state = value
        _apply_state()
        power_state_changed.emit(state)

var _idle_timer: Timer
var _mode_poll_timer: Timer

func _ready() -> void:
    # The manager itself must keep running even if the tree is paused.
    process_mode = Node.PROCESS_MODE_ALWAYS

    var window: Window = get_window()
    window.focus_entered.connect(_on_focus_entered)
    window.focus_exited.connect(_on_focus_exited)

    _idle_timer = Timer.new()
    _idle_timer.one_shot = true
    _idle_timer.wait_time = IDLE_GRACE_SEC
    _idle_timer.timeout.connect(_on_idle_grace_elapsed)
    add_child(_idle_timer)

    _mode_poll_timer = Timer.new()
    _mode_poll_timer.wait_time = MODE_POLL_SEC
    _mode_poll_timer.timeout.connect(_poll_window_mode)
    add_child(_mode_poll_timer)
    _mode_poll_timer.start()

    state = PowerState.ACTIVE
    _apply_state()  # explicit first application (setter skipped: same value)

func _input(event: InputEvent) -> void:
    # Any real user input while visible promotes us to ACTIVE.
    if event is InputEventMouseMotion \
            or event is InputEventMouseButton \
            or event is InputEventKey:
        _register_activity()

func _register_activity() -> void:
    if state != PowerState.HIDDEN:
        state = PowerState.ACTIVE
        _idle_timer.start()  # restart the grace countdown

func _on_focus_entered() -> void:
    state = PowerState.ACTIVE
    _idle_timer.start()

func _on_focus_exited() -> void:
    # Unfocused but possibly still visible: IDLE, not HIDDEN.
    if state != PowerState.HIDDEN:
        state = PowerState.IDLE
        _idle_timer.stop()

func _on_idle_grace_elapsed() -> void:
    # Focused but untouched for IDLE_GRACE_SEC.
    if state == PowerState.ACTIVE:
        state = PowerState.IDLE

func _poll_window_mode() -> void:
    var minimized: bool = get_window().mode == Window.MODE_MINIMIZED
    if minimized and state != PowerState.HIDDEN:
        state = PowerState.HIDDEN
    elif not minimized and state == PowerState.HIDDEN:
        # Restored: focus signal may not fire if restored unfocused.
        state = PowerState.IDLE

func _apply_state() -> void:
    match state:
        PowerState.ACTIVE:
            Engine.max_fps = FPS_ACTIVE
        PowerState.IDLE:
            Engine.max_fps = FPS_IDLE
        PowerState.HIDDEN:
            Engine.max_fps = FPS_HIDDEN
```

Design notes worth dwelling on:

**The state is a property with a setter, and the setter deduplicates.** Focus events, input events and the poll timer can all fire in bursts; routing every transition through one setter guarantees `power_state_changed` is emitted exactly once per real change and `_apply_state()` never runs redundantly.

**Input promotion is instant; demotion is lazy.** Promotion to ACTIVE happens synchronously inside `_input()` — before this frame's `_process` even runs — so the very first mouse-move after an idle period is already handled at the new cap. Demotion uses a one-shot `Timer` (the grace period), because dropping to 15 FPS the instant the mouse stops moving would cause visible cap oscillation while the user reads the screen.

**Minimization is polled at 1 Hz, not per frame.** Godot's `Window` has focus signals but no dedicated "minimized" signal, so we check `Window.mode == Window.MODE_MINIMIZED` on a slow timer. One check per second is invisible in the profiler; a per-frame check in `_process` would be the exact polling anti-pattern this module preaches against. (You can additionally handle `Node.NOTIFICATION_APPLICATION_FOCUS_IN` / `NOTIFICATION_APPLICATION_FOCUS_OUT` in `_notification()` to detect the whole app losing focus to another application, which is a stronger idle hint than per-window focus.)

**Other systems subscribe; the manager does not micromanage.** The manager knows nothing about particles or shaders. Systems register themselves:

```gdscript
# In any node that owns expensive visuals:
func _ready() -> void:
    Perf.power_state_changed.connect(_on_power_state_changed)
    _on_power_state_changed(Perf.state)  # apply current state immediately

func _on_power_state_changed(new_state: Perf.PowerState) -> void:
    var active := new_state == Perf.PowerState.ACTIVE
    $AmbientParticles.emitting = active
    $Mascot/AnimationPlayer.speed_scale = 1.0 if active else 0.5
    ($Background.material as ShaderMaterial).set_shader_parameter(
        "animate", new_state != Perf.PowerState.HIDDEN)
```

> ⚠️ **Pitfall** — The original edition of this manager connected to `get_tree().get_root().window`. In Godot 4 the SceneTree root *is* a `Window`; the idiomatic accessor from any node is `get_window()` (or `get_tree().root`). Chasing a `.window` property on the root is a 3.x-ism that will fail.

> ✅ **Best practice** — Expose the FPS constants as project settings or a config resource rather than hard-coding, and log every state transition during development (`print_verbose` or your logger). When a tester reports "the app felt sluggish when I came back," the transition log tells you whether the manager misbehaved or something else did.

### 4.2 Choosing the numbers

- **ACTIVE = 60** matches typical desktop refresh and native-app feel. If you support 120/144 Hz users and your scene is trivially cheap, consider `DisplayServer.screen_get_refresh_rate()` (returns the refresh rate of a screen, or -1 if unknown) and cap to `mini(refresh, 120)` — but measure the energy cost first; doubling ACTIVE frames doubles ACTIVE power.
- **IDLE = 15** as argued in section 2.3. If your idle scene is completely static (a plain widget, no ambient motion), go lower — 10, 5 — or skip straight to event-driven rendering with low-processor mode (section 6).
- **HIDDEN = 5, not 0.** `max_fps` has no "zero frames" value (`0` means *uncapped*!). A floor of a few FPS keeps timers, tweens and audio-driving logic serviced with negligible cost. If you need true zero-redraw behavior, that is `low_processor_usage_mode` territory, or `get_tree().paused` if your app can genuinely stop (section 8).

> ⚠️ **Pitfall** — Never write `Engine.max_fps = 0` intending "pause everything." You just uncapped the framerate. This typo has shipped in real products; a code-review grep for `max_fps = 0` is worth adding to CI.

### 4.3 Making the manager testable

The power-state machine is the one piece of this app you *really* do not want to regress — a bug here silently doubles battery drain for every user. Its logic is pure state-transition code, which means it can be factored for testing: separate the *decision* (which state should we be in, given inputs) from the *application* (setting engine properties).

```gdscript
# power_policy.gd — a plain RefCounted, no engine side effects, fully testable.
class_name PowerPolicy
extends RefCounted

enum State { ACTIVE, IDLE, HIDDEN }

## Pure transition function: current state + observed facts -> next state.
static func next_state(current: State, focused: bool, minimized: bool,
        visible: bool, input_recent: bool) -> State:
    if minimized or not visible:
        return State.HIDDEN
    if focused and input_recent:
        return State.ACTIVE
    if focused and current == State.ACTIVE and input_recent:
        return State.ACTIVE
    return State.IDLE
```

The autoload then becomes a thin adapter: it gathers the facts (focus signals, the minimize poll, the grace timer collapsing into `input_recent`), calls `PowerPolicy.next_state()`, and applies the result. A test script — or a GUT/GdUnit4 suite if the project uses one — can now exhaustively table-test the policy without a window, a timer or a display server:

```gdscript
# test_power_policy.gd — run as a tool script or inside your test framework.
func test_policy_table() -> void:
    var S := PowerPolicy.State
    var cases: Array = [
        # [current, focused, minimized, visible, input_recent, expected]
        [S.ACTIVE, true,  false, true,  true,  S.ACTIVE],
        [S.ACTIVE, true,  false, true,  false, S.IDLE],    # grace elapsed
        [S.ACTIVE, false, false, true,  false, S.IDLE],    # focus lost
        [S.IDLE,   true,  false, true,  true,  S.ACTIVE],  # input promotes
        [S.IDLE,   false, true,  true,  false, S.HIDDEN],  # minimized
        [S.HIDDEN, false, false, false, false, S.HIDDEN],  # tray-hidden
        [S.HIDDEN, false, false, true,  false, S.IDLE],    # restored, unfocused
        [S.HIDDEN, true,  false, true,  true,  S.ACTIVE],  # restored + click
    ]
    for c: Array in cases:
        var got: PowerPolicy.State = PowerPolicy.next_state(c[0], c[1], c[2], c[3], c[4])
        assert(got == c[5], "policy(%s) => %s, expected %s" % [c, got, c[5]])
    print("power policy: %d cases passed" % cases.size())
```

This costs half an hour once and repays it on every refactor. The transition table also doubles as the specification you paste into a bug report when a platform's focus events behave oddly (they do — window managers are a zoo).

---

## 5. VSync Strategies with DisplayServer

Vertical synchronization decides *when* a rendered frame is handed to the display. In Godot 4 it is controlled per window at runtime through `DisplayServer.window_set_vsync_mode()` and configured at startup by the project setting `display/window/vsync/vsync_mode`. The four modes:

```gdscript
DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)  # 0
DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED)   # 1 (default)
DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ADAPTIVE)  # 2
DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_MAILBOX)   # 3
var mode := DisplayServer.window_get_vsync_mode()
```

| Mode | Behavior | Tearing | Latency | Companion verdict |
|---|---|---|---|---|
| `VSYNC_DISABLED` | Present immediately; framerate limited only by `Engine.max_fps` | Possible | Lowest | Acceptable *only* combined with a strict `max_fps` cap; saves the wait-for-blank but risks tearing |
| `VSYNC_ENABLED` | Present on vertical blank; framerate additionally limited by refresh rate | None | Moderate | **Default choice.** Predictable pacing, zero tearing, plays perfectly with low caps |
| `VSYNC_ADAPTIVE` | VSync on normally; turns off when FPS drops below refresh to reduce stutter | Possible under load | Moderate | Little benefit for a capped companion (we are *deliberately* below refresh, so it behaves like disabled at idle on some stacks); fine where supported |
| `VSYNC_MAILBOX` | Render continuously into a queue; newest frame shown at blank; no tearing | None | Low | **Avoid.** Designed for fast-paced games wanting low latency without tearing; keeps the GPU rendering frames that are thrown away — the opposite of idle efficiency |

Two subtleties from the documentation worth engraving:

1. **Under `VSYNC_ENABLED`/`VSYNC_ADAPTIVE`, the refresh rate is a ceiling "regardless of `Engine.max_fps`"** — meaning `max_fps` cannot push you *above* refresh, but a `max_fps` *below* refresh still applies. Our 15 FPS idle cap works identically under every mode.
2. **Not every mode is supported on every platform/driver.** Adaptive and mailbox depend on driver support (classically Vulkan-centric; adaptive maps to OpenGL's adaptive vsync where available); when unsupported, the engine falls back to a supported mode. Never assume the mode you requested is the mode you got — `window_get_vsync_mode()` tells the truth. There are also long-standing platform quirks around switching to/from mailbox at runtime; switch VSync modes rarely (at startup or on a settings change), not per power-state transition.

### 5.1 The companion policy

For Relax Room the policy is deliberately boring:

```gdscript
# Set once at startup. Power states change max_fps, never the vsync mode.
func _configure_vsync() -> void:
    DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED)
    if DisplayServer.window_get_vsync_mode() != DisplayServer.VSYNC_ENABLED:
        push_warning("VSync fallback active: %d" % DisplayServer.window_get_vsync_mode())
```

Rationale: `VSYNC_ENABLED` gives tear-free presentation and lets the compositor batch our presents efficiently; all dynamic throttling happens through `Engine.max_fps`, which is cheap, instant and universally supported. Keeping one knob dynamic (the cap) and one static (VSync) makes the system's behavior explainable in one sentence — a property you will appreciate at 2 a.m. when debugging a stutter report.

> ⚠️ **Pitfall** — Testing "which VSync mode is fastest" by watching the FPS counter with `max_fps = 0` tells you nothing useful for a companion and burns a laptop battery while you do it. The relevant experiment is frame-*pacing* consistency at your capped rates (section 16's CSV logger graphs frame intervals) and CPU% in Task Manager per mode.

### 5.2 Verifying pacing consistency

An FPS counter shows an average and hides the thing users feel: irregular frame *intervals*. A 15 FPS cap delivered as a steady 66-66-66 ms cadence looks calm; the same average delivered as 40-90-70-66 ms makes ambient motion visibly lumpy. A twenty-line recorder answers whether your cap + VSync combination paces cleanly on a given machine:

```gdscript
# debug/pacing_recorder.gd — attach anywhere; press the action to dump stats.
extends Node

const WINDOW: int = 600   # samples (~10 s at 60 FPS, ~40 s at 15)
var _intervals: PackedFloat64Array = PackedFloat64Array()
var _last_usec: int = 0

func _ready() -> void:
    _intervals.resize(WINDOW)
    _intervals.fill(0.0)
    _last_usec = Time.get_ticks_usec()

var _i: int = 0
func _process(_delta: float) -> void:
    var now := Time.get_ticks_usec()
    _intervals[_i % WINDOW] = float(now - _last_usec) / 1000.0  # ms
    _last_usec = now
    _i += 1

func _input(event: InputEvent) -> void:
    if event.is_action_pressed(&"dump_pacing"):
        var sorted := _intervals.duplicate()
        sorted.sort()
        var n := sorted.size()
        print("pacing ms — p50: %.1f  p95: %.1f  p99: %.1f  max: %.1f" % [
            sorted[n / 2], sorted[int(n * 0.95)], sorted[int(n * 0.99)],
            sorted[n - 1]])
```

Interpretation: p50 should sit at the cap's nominal interval (16.7 / 66.7 ms); a p99 within ~1.5× of p50 is clean pacing; a p99 several times p50 means hitches — go find them with the profiler (a hitch log threshold, as in section 12.7's best practice, tells you *when*; the profiler tells you *what*). Run the recorder per power state and per VSync mode on your worst target machine; keep the numbers with the budget sheet. This recorder is also the engine behind Exercise 3's histogram.

---

## 6. Low Processor Usage Mode

Frame caps make frames *less frequent*. Low processor usage mode goes further: it makes frames **conditional**. From the `OS` class reference: *"If true, the engine optimizes for low processor usage by only refreshing the screen if needed."* In this mode the engine skips redrawing entirely when nothing has changed — the render step simply does not happen — and sleeps between loop iterations. This is the same mechanism the Godot **editor itself** uses, which is why the editor of a full game engine can sit at ~0% CPU when you are not touching it. That fact alone should convince you the mechanism is production-grade.

Two knobs, available both as project settings and runtime `OS` properties:

| Project setting | Runtime property | Default | Meaning |
|---|---|---|---|
| `application/run/low_processor_mode` | `OS.low_processor_usage_mode` | `false` | Enable redraw-on-demand behavior |
| `application/run/low_processor_mode_sleep_usec` | `OS.low_processor_usage_mode_sleep_usec` | `6900` (µs) | Sleep between main-loop iterations while the mode is on |

```gdscript
# Runtime control — e.g. entering the HIDDEN state:
OS.low_processor_usage_mode = true
OS.low_processor_usage_mode_sleep_usec = 33000  # ~30 iterations/sec ceiling
```

### 6.1 What "if needed" means

A redraw is triggered when the engine knows something visual changed: a `CanvasItem` was modified (moved, re-textured, shown/hidden, its `queue_redraw()` called), an animation advanced, the window was resized or exposed, and so on. Continuous animation sources — `AnimationPlayer` mid-playback, emitting particles, an active `Tween`, a video — request redraws every frame and therefore *neutralize* the mode's savings while they run. Purely static frames request nothing, and the loop degenerates to: pump OS events → tick timers/scripts → sleep. CPU use approaches zero; GPU use *is* zero.

Note carefully what still runs: `_process()` and `_physics_process()` continue to execute each iteration — the mode suppresses *rendering*, not *logic*. If your `_process` does per-frame work, you keep paying for it. Low-processor mode composes with, and does not replace, the `set_process(false)` discipline of section 7.

### 6.2 Tuning the sleep

The sleep value bounds the main-loop iteration rate while the mode is active: `6900 µs ≈ 6.9 ms` of sleep yields a ceiling somewhere near 144 iterations/second (chosen so editor UI interactions stay fluid on high-refresh monitors). For a companion's HIDDEN state that is far more wakeups than needed:

| `sleep_usec` | Approx. max iterations/sec | Feel when a redraw *is* needed | Use case |
|---|---|---|---|
| 6900 (default) | ~140 | Perfectly fluid | Visible tool-style UI |
| 16000 | ~60 | Fluid | Visible, relaxed UI |
| 33000 | ~30 | Noticeable on drag operations | Unfocused/background |
| 66000 | ~15 | Sluggish for interaction | Hidden/tray, timers still fine |

The trade-off is honest: a large sleep means that when input *does* arrive, up to one sleep interval passes before the app reacts. That is why the value belongs to the power-state machine — small (or mode off entirely) when ACTIVE, large when HIDDEN.

> ⚠️ **Pitfall** — Raising `low_processor_mode_sleep_usec` globally and forgetting to lower it on activity makes the whole app feel laggy in a way profilers will *not* show: every function is fast, the app just wakes rarely. (The same class of complaint exists about the editor when people tune its equivalent setting too high.) Always pair the mode with an activity-driven restore path.

### 6.3 Event-driven companions: the mode as a primary strategy

For companions whose UI is genuinely static between interactions — a timer widget that changes once a second, a note-taker, a controller panel — `low_processor_usage_mode` can be enabled **permanently**, making the app event-driven like a native toolkit app:

```gdscript
# project.godot (or Project Settings UI):
# application/run/low_processor_mode = true
# application/run/low_processor_mode_sleep_usec = 16000
```

In this configuration the FPS counter becomes almost meaningless (frames happen only on change), and CPU at idle is effectively the cost of the sleep loop — typically a fraction of a percent. The clock digits repaint because updating a `Label.text` marks it dirty and requests exactly one redraw.

The catch, and the reason Relax Room does *not* run this way while visible: **any continuously animated element defeats it.** Relax Room's ambient scene (drifting particles, a shader-animated gradient, a breathing mascot) requests redraws constantly while visible, so in ACTIVE/IDLE states the FPS cap is the effective throttle. The strategy matrix:

| App style while visible | Primary throttle | Secondary |
|---|---|---|
| Static UI, changes on interaction | `low_processor_usage_mode` on always | modest `max_fps` cap as safety net |
| Ambient animation always visible | `max_fps` per power state (15/60) | mode on only when HIDDEN |
| Mixed (animated panel, static rest) | per-state cap + gating animations when idle | mode on when fully static |

Relax Room's `PerformanceManager` therefore enables the mode only on entering HIDDEN — where the window produces no visible pixels, redraw-on-demand trivially means "never redraw" — and disables it on restore:

```gdscript
func _apply_state() -> void:
    match state:
        PowerState.ACTIVE:
            Engine.max_fps = FPS_ACTIVE
            OS.low_processor_usage_mode = false
        PowerState.IDLE:
            Engine.max_fps = FPS_IDLE
            OS.low_processor_usage_mode = false
        PowerState.HIDDEN:
            Engine.max_fps = FPS_HIDDEN
            OS.low_processor_usage_mode = true
            OS.low_processor_usage_mode_sleep_usec = 66000
```

> ✅ **Best practice** — After wiring this up, *verify with the OS*, not the in-app HUD: minimize the app, wait 30 s, and watch its CPU column in Task Manager settle to ~0.0–0.1%. Section 16 formalizes this check. The in-engine FPS readout cannot distinguish "sleeping beautifully" from "not measuring."

> ⚠️ **Pitfall** — `Engine.time_scale` deserves a second warning here because people reach for it as an "idle mode": setting `time_scale = 0.1` when unfocused slows your animations to molasses *without saving any CPU* — the loop frequency is untouched. Slow-motion is an aesthetic, not a power plan.

### 6.4 Verifying redraw-on-demand actually engages

Because low-processor mode's savings depend on the *scene's* behavior, "I enabled the setting" proves nothing — one forgotten animated node silently reverts you to full-rate rendering. The engine provides the perfect verification counter pair: `Engine.get_process_frames()` increments every main-loop iteration *"regardless of whether the render loop is enabled"*, while `Engine.get_frames_drawn()` counts only frames actually rendered. Their ratio is your redraw-on-demand health meter:

```gdscript
# debug/redraw_meter.gd — sample on the 10 s heartbeat while HIDDEN.
var _last_process: int = 0
var _last_drawn: int = 0

func _on_heartbeat_tick_10s() -> void:
    var p := Engine.get_process_frames()
    var d := Engine.get_frames_drawn()
    var iters := p - _last_process
    var draws := d - _last_drawn
    _last_process = p
    _last_drawn = d
    if Perf.state == Perf.PowerState.HIDDEN and iters > 0:
        var ratio := float(draws) / float(iters)
        if ratio > 0.1:
            push_warning("HIDDEN but drawing %.0f%% of iterations — "
                % (ratio * 100.0)
                + "something is animating (TIME shader? particles? tween?)")
```

In a correctly configured HIDDEN state the draw count should be near zero between samples; every unexpected draw traces back to a redraw requester. Hunting order when the warning fires: TIME-driven shader materials (section 13.3), `GPUParticles2D.emitting`, running `AnimationPlayer`s and tweens (`get_tree().get_processed_tweens()`), then any custom `_draw` widget calling `queue_redraw()` on a timer. This ten-line meter has caught every "why is the tray app warm?" regression in Relax Room since it was added — cheap enough to leave in debug builds permanently.

---

## 7. Physics Ticks and Process Discipline

### 7.1 Right-sizing the physics tick rate

`Engine.physics_ticks_per_second` (project setting `physics/common/physics_ticks_per_second`, default `60`) sets the fixed rate of `_physics_process()` and the physics servers. As established in section 3, this rate is **independent of the render cap** — the engine will faithfully run 60 physics ticks per second inside your 15 FPS idle app, simulating collision for a scene that may contain two Area2Ds and a mascot.

Most companion apps use physics barely or not at all: perhaps an `Area2D` for hover detection, maybe a soft-body decoration. For these apps:

```gdscript
# At startup, before gameplay logic runs:
Engine.physics_ticks_per_second = 30   # or 10 for pure decoration physics
Engine.max_physics_steps_per_frame = 8 # default; rarely needs changing here
```

- Halving 60 → 30 halves the fixed simulation cost forever. For hover areas and cosmetic wobbles, 30 Hz is indistinguishable.
- If the app uses **no** physics nodes at all, the per-tick cost is already tiny (the servers early-out with zero active objects — see the `PHYSICS_2D_ACTIVE_OBJECTS` monitor), but `_physics_process()` callbacks you wrote still run at the tick rate. Move that logic to `_process` or timers and keep the tick rate low anyway; it costs one line.
- `Engine.max_physics_steps_per_frame` (default 8) matters in the opposite regime: it caps how many *catch-up* ticks can run in one rendered frame when rendering is slower than physics. With our low caps (15 FPS render, 30 Hz physics), each rendered frame runs ~2 catch-up ticks — well under 8, so defaults are fine. Just know the property exists before you crank tick rate up for some reason.

> ⚠️ **Pitfall** — Physics interpolation aside, moving visible nodes from `_physics_process` at 30 Hz while rendering at 60 FPS produces visible stepping. In a companion, drive *visuals* from `_process` or tweens, and reserve `_physics_process` for actual physics queries. The original module's advice "replace `_process` with `_physics_process` if rate-tolerant" made sense when both ran at 60; under a companion's asymmetric rates, prefer timers (below) over either.

### 7.2 The `set_process(false)` discipline

Every node that implements `_process()` or `_physics_process()` gets called *every* frame/tick, even if the method immediately returns. Godot auto-enables processing for any node whose script defines these methods. The discipline: **processing is opt-in per lifecycle phase, and off is the default state of mind.**

```gdscript
# A panel that only animates while visible on screen:
func _ready() -> void:
    visibility_changed.connect(_on_visibility_changed)
    _on_visibility_changed()

func _on_visibility_changed() -> void:
    var active := is_visible_in_tree()
    set_process(active)
    set_physics_process(active)
```

The full switchboard, all instant and cheap to toggle:

| Call | Disables |
|---|---|
| `set_process(false)` | `_process(delta)` |
| `set_physics_process(false)` | `_physics_process(delta)` |
| `set_process_input(false)` | `_input(event)` |
| `set_process_unhandled_input(false)` | `_unhandled_input(event)` |
| `set_process_internal(false)` | internal per-frame processing (rarely needed) |
| `node.process_mode = Node.PROCESS_MODE_DISABLED` | everything, including children's inherited processing |

`process_mode = PROCESS_MODE_DISABLED` is the sledgehammer: the node and its subtree stop processing entirely (it also affects pause behavior — see section 8.2). It is ideal for whole features that are dormant: Relax Room's settings panel subtree is `DISABLED` except while open.

> ✅ **Best practice** — Audit with the profiler, not with your eyes: the *Script Functions* view (section 11) lists every `_process` implementation that ran. In an idle companion, that list should be nearly empty. Each entry is either justified (the FPS manager's poll timer — actually a Timer, so not even there) or a bug.

### 7.3 Timers over polling

The single most common companion-app sin looks like this:

```gdscript
# BAD: wakes the script system 60 times/sec to check something that
# changes twice a day.
func _process(_delta: float) -> void:
    if Time.get_datetime_dict_from_system().hour >= 18:
        _switch_to_evening_theme()
```

Polling in `_process` costs you: a script VM entry per frame, the check itself, cache pollution — multiplied by every polling node, forever. The event-driven rewrite:

```gdscript
# GOOD: one wakeup per minute; zero per-frame cost.
func _ready() -> void:
    var timer := Timer.new()
    timer.wait_time = 60.0
    timer.timeout.connect(_check_evening_theme)
    add_child(timer)
    timer.start()

func _check_evening_theme() -> void:
    if Time.get_datetime_dict_from_system().hour >= 18:
        _switch_to_evening_theme()
```

Rules of thumb:

- **Anything that changes slower than the frame rate does not belong in `_process`.** Clock displays: 1 s timer. Config-file watching: 5 s timer. Server sync: 60 s timer plus jitter.
- **Prefer signals over timers when a signal exists.** `visibility_changed`, `focus_entered`, `resized`, `area_entered` — the engine already knows; do not re-derive it by sampling.
- **One shared heartbeat beats many private timers.** Ten features each running a 1 s `Timer` cause ten separate wakeup points scattered across the second. A single `Heartbeat` autoload with `tick_1s` / `tick_10s` signals batches them into one wakeup, which also batch-aligns CPU activity (better for OS power management):

```gdscript
# autoloads/heartbeat.gd
extends Node
## Central slow-tick provider; features subscribe instead of owning timers.

signal tick_1s
signal tick_10s

var _count: int = 0

func _ready() -> void:
    var t := Timer.new()
    t.wait_time = 1.0
    t.timeout.connect(_on_tick)
    add_child(t)
    t.start()

func _on_tick() -> void:
    _count += 1
    tick_1s.emit()
    if _count % 10 == 0:
        tick_10s.emit()
```

- **`SceneTree.create_timer()` is for one-shots**, not recurring work — see the pitfall below, preserved from this module's first edition because it ships in real code constantly.

> ⚠️ **Pitfall** — `get_tree().create_timer(1.0)` fires **once**. The original edition's metrics printer connected to a `create_timer` timeout expecting a per-second tick and silently printed a single line. For recurring work use a `Timer` node (`one_shot = false`, the default) or re-arm the scene-tree timer in the callback. Also note `create_timer`'s optional parameters — `create_timer(time, process_always := true, process_in_physics := false, ignore_time_scale := false)` — matter in section 8: a timer created with `process_always = false` freezes while the tree is paused.

---

## 8. Focus, Minimize and Throttling Policies

The adaptive manager in section 4 already consumes focus and minimize information; this section covers the detection surface completely and settles the biggest policy question: *pause or throttle?*

### 8.1 The detection surface

| Event | API | Notes |
|---|---|---|
| Window gained focus | `Window.focus_entered` signal | Root window: `get_window().focus_entered` |
| Window lost focus | `Window.focus_exited` signal | Fires when another window (yours or another app's) takes focus |
| Whole app lost focus | `Node.NOTIFICATION_APPLICATION_FOCUS_OUT` in `_notification()` | Distinguishes "user switched to another app" from "user opened our settings popup" |
| Whole app gained focus | `Node.NOTIFICATION_APPLICATION_FOCUS_IN` | Pair of the above |
| Per-window OS focus notifications | `Node.NOTIFICATION_WM_WINDOW_FOCUS_IN` / `_OUT` | Node-level alternative to the signals |
| Minimized / restored | poll `Window.mode == Window.MODE_MINIMIZED` (or `DisplayServer.window_get_mode()`) | No signal exists; poll at ~1 Hz |
| Window closed | `Window.close_requested` signal | Essential for minimize-to-tray (section 10) |
| Visibility of a control | `CanvasItem.visibility_changed` + `is_visible_in_tree()` | For throttling individual features |

A companion with popups (settings window, tray menu) should treat **application** focus as the idle trigger, not window focus: when the user moves from the main window to your settings window, `focus_exited` fires on the main window but the app as a whole is still being used. The `_notification()` handler slots into the manager beside the signal handlers:

```gdscript
func _notification(what: int) -> void:
    match what:
        NOTIFICATION_APPLICATION_FOCUS_OUT:
            if state == PowerState.ACTIVE:
                state = PowerState.IDLE
        NOTIFICATION_APPLICATION_FOCUS_IN:
            _register_activity()
```

### 8.2 `get_tree().paused` versus custom throttle

Godot offers a global pause: `get_tree().paused = true`. Whether a node keeps running while paused is decided by `Node.process_mode`:

| `process_mode` | While paused |
|---|---|
| `PROCESS_MODE_INHERIT` (default) | Follows parent (ultimately: pauses) |
| `PROCESS_MODE_PAUSABLE` | Stops |
| `PROCESS_MODE_WHEN_PAUSED` | Runs *only* while paused |
| `PROCESS_MODE_ALWAYS` | Always runs |
| `PROCESS_MODE_DISABLED` | Never runs |

Pausing stops `_process`, `_physics_process`, input handling, most timers and tweens for pausable nodes in one line — seductive for a HIDDEN state. But compare honestly:

| Criterion | `get_tree().paused = true` | Custom throttle (caps + state signal) |
|---|---|---|
| Implementation effort | One line + `process_mode` audit | The `PerformanceManager` (~100 lines) |
| CPU savings | Excellent (logic stops) — but the loop still spins at `max_fps` rendering a paused scene, so combine with a cap or low-processor mode anyway | Excellent, and tunable per subsystem |
| Audio | AudioStreamPlayers on pausable nodes **stop** — fatal for an ambient-sound app | Untouched unless you throttle it |
| Timers/tweens | Frozen (unless created `process_always = true` / node set to `ALWAYS`) — pomodoro countdowns must not freeze! | Keep running |
| Re-entry correctness | All-or-nothing; easy to forget one `ALWAYS` node and freeze the un-pause path itself | Gradual; each subsystem handles its own state |
| Hidden bugs | `process_mode` is inherited — a reparented node silently changes pause behavior | State is explicit at each subscriber |

The verdict for companions is almost always **custom throttle**: the things a companion must keep doing while hidden (play ambient audio, count down a timer, fire a notification at 25:00) are exactly the things `paused` freezes by default. Global pause shines in games (menus over gameplay); in a companion it is a foot-gun with one valid niche — a purely visual app with zero background responsibilities can pause its scene subtree when hidden and keep only the manager at `PROCESS_MODE_ALWAYS`.

> ⚠️ **Pitfall** — If you do use `paused`, remember the un-pause trigger must live on a node with `PROCESS_MODE_ALWAYS` and any timer involved must be created with `process_always = true`. Teams have shipped apps that pause on minimize and can never wake up because the wake-up logic paused itself.

### 8.3 Throttling beyond FPS

The power-state signal can throttle things the frame cap does not touch:

- **Network refresh cadence** — weather/RSS/status polling drops from every 60 s (ACTIVE) to every 15 min (HIDDEN).
- **Disk writes** — autosave every 30 s while ACTIVE, on-transition-to-HIDDEN once, then hourly. (Persistence patterns: [Database and Persistence](DATABASE_AND_PERSISTENCE.md).)
- **Audio mixing** — if the app plays no sound while hidden, stop streams entirely rather than playing silence; a playing `AudioStreamPlayer` keeps the audio thread mixing.
- **Animation** — `AnimationPlayer.pause()` / `speed_scale`, `GPUParticles2D.emitting = false`, shader gating (section 13).

```gdscript
# Example: network module subscribing to power states.
func _on_power_state_changed(new_state: Perf.PowerState) -> void:
    match new_state:
        Perf.PowerState.ACTIVE:
            _poll_timer.wait_time = 60.0
        Perf.PowerState.IDLE:
            _poll_timer.wait_time = 300.0
        Perf.PowerState.HIDDEN:
            _poll_timer.wait_time = 900.0
    _poll_timer.start()  # re-arm with new cadence
```

### 8.4 Per-feature visibility throttling

The power state is app-global; a second, finer layer throttles individual features by *their own* visibility, independent of the app state. A tabbed companion (Sounds / Timer / Stats tabs) should not process the Stats charts while the Sounds tab is open — even in ACTIVE state. The pattern is a small reusable helper:

```gdscript
# throttle_when_hidden.gd — attach to any subtree root that should sleep
# whenever it is not actually visible on screen.
extends Node

@export var also_disable_input: bool = true

func _ready() -> void:
    var parent := get_parent() as CanvasItem
    assert(parent != null, "ThrottleWhenHidden must be a child of a CanvasItem")
    parent.visibility_changed.connect(_sync.bind(parent))
    _sync(parent)

func _sync(target: CanvasItem) -> void:
    var on := target.is_visible_in_tree()
    target.set_process(on)
    target.set_physics_process(on)
    if also_disable_input:
        target.set_process_input(on)
        target.set_process_unhandled_input(on)
```

Drop this node under each tab's root and forget about it: switching tabs now automatically silences the hidden subtrees. Note the deliberate limitation — it toggles processing only on the subtree *root*; children with their own `_process` need the same treatment or a walk. For deep feature subtrees, prefer flipping the root's `process_mode`:

```gdscript
func _sync(target: CanvasItem) -> void:
    target.process_mode = (
        Node.PROCESS_MODE_INHERIT if target.is_visible_in_tree()
        else Node.PROCESS_MODE_DISABLED)   # disables the whole subtree
```

`PROCESS_MODE_DISABLED` propagates to every descendant, which is exactly right for a dormant tab — one property write silences fifty nodes. The two-layer summary:

| Layer | Trigger | Mechanism | Granularity |
|---|---|---|---|
| App power state | focus / input / minimize | `Engine.max_fps`, low-processor mode, `power_state_changed` subscribers | whole app |
| Feature visibility | `visibility_changed` | `set_process(false)` / `PROCESS_MODE_DISABLED` on subtree roots | per feature |

> ✅ **Best practice** — These layers compose multiplicatively: an app at 15 FPS whose hidden tabs are also process-disabled does 15 × (visible work only). When auditing, check both: the profiler's Script Functions view during idle with *each* tab active tells you whether the per-feature layer actually engages.

---

## 9. Window Styling and Multi-Monitor Concerns

Companion apps live *on the desktop*, not fullscreen, so window management is part of the performance story: some styling choices carry real GPU/compositor costs, and geometry mistakes read as bugs.

### 9.1 Always-on-top and borderless

Both are available as project settings (`display/window/size/always_on_top`, `display/window/size/borderless`) and runtime `Window` properties or `DisplayServer` flags:

```gdscript
var w := get_window()
w.always_on_top = true          # float above other windows
w.borderless = true             # no OS title bar / frame
w.unresizable = true            # fixed-size widget

# Equivalent low-level form:
DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, true)
DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, true)
```

Performance impact of these two is negligible; the cost is UX: a borderless window needs custom drag/resize handling (implement dragging by tracking mouse delta and setting `w.position`), and always-on-top must be a *user setting*, never a default — an uninvited always-on-top window is uninstall material.

Related flags worth knowing for widget-style companions: `WINDOW_FLAG_NO_FOCUS` (window never takes keyboard focus — for pure display widgets) and `WINDOW_FLAG_MOUSE_PASSTHROUGH` (clicks fall through to windows beneath — for overlay companions; pair with `DisplayServer.window_set_mouse_passthrough()` polygon regions for partial passthrough).

### 9.2 Per-pixel transparent windows — the pretty tax

The floating mascot with no window rectangle — just a character on the desktop — requires per-pixel transparency, a three-switch setup:

1. Project setting `display/window/per_pixel_transparency/allowed = true` (capability master switch),
2. Project setting `display/window/size/transparent = true` or runtime `get_window().transparent = true` (window framebuffer with alpha),
3. A transparent viewport background: `get_viewport().transparent_bg = true` (and no opaque background nodes).

```gdscript
func _enable_ghost_mode() -> void:
    get_window().transparent = true
    get_viewport().transparent_bg = true
    # WINDOW_FLAG_TRANSPARENT is the DisplayServer-level equivalent flag.
```

> ⚠️ **Pitfall** — Per-pixel transparency is the most expensive checkbox in this module. The window can no longer be treated as opaque by the OS compositor: every frame your app presents must be *composited* (alpha-blended) with everything behind it, on every desktop repaint, and certain platform fast paths (fullscreen optimizations, direct scan-out) are disabled. Expect measurably higher GPU/compositor load and battery draw versus an identical opaque window — the documentation itself warns the feature has a performance cost and should be used only when needed. Budget consequence: a transparent companion should be *small* (a 300×400 mascot window, not a 1080p canvas), should still cap FPS aggressively, and should re-verify the idle CPU/GPU budget *with transparency on*, because the compositor cost shows up in system processes (`dwm.exe` on Windows), not in your process — another reason in-engine numbers lie (section 16).

### 9.3 Multi-monitor and DPI

Users park companions on secondary monitors with different resolutions, refresh rates and DPI scales. The relevant `DisplayServer` surface:

```gdscript
var screens := DisplayServer.get_screen_count()
var current := get_window().current_screen
var dpi := DisplayServer.screen_get_dpi(current)            # e.g. 96, 144
var scale := DisplayServer.screen_get_scale(current)        # e.g. 1.0, 2.0 (platform support varies)
var hz := DisplayServer.screen_get_refresh_rate(current)    # -1.0 if unknown
var usable := DisplayServer.screen_get_usable_rect(current) # excludes taskbar/dock
```

Practical rules:

- **Never hard-code pixel sizes for UI**; use `Window.content_scale_factor` and the content-scale modes so the widget renders crisply at 150%/200% Windows scaling. Test at 100% and 200% minimum.
- **Refresh rate can differ per monitor** (60 Hz laptop panel + 144 Hz external). If you derive your ACTIVE cap from `screen_get_refresh_rate()`, re-query when `current_screen` changes, and handle the `-1` unknown case with a 60 fallback.
- **`screen_get_dpi`/`screen_get_scale` support varies by platform** (scale is primarily meaningful on macOS and Wayland). Treat them as hints, prefer the content-scale system for actual layout.

### 9.4 Saving and restoring window geometry

A companion that forgets its position feels broken. Persist geometry on exit (or on a debounced move/resize), restore on launch — *with validation*, because monitors disappear:

```gdscript
# window_geometry.gd — helper used by the main window.
const CFG_PATH := "user://window.cfg"

func save_geometry() -> void:
    var w := get_window()
    if w.mode != Window.MODE_WINDOWED:
        return  # never persist minimized/maximized raw geometry
    var cfg := ConfigFile.new()
    cfg.set_value("window", "position", w.position)
    cfg.set_value("window", "size", w.size)
    cfg.set_value("window", "screen", w.current_screen)
    cfg.save(CFG_PATH)

func restore_geometry() -> void:
    var cfg := ConfigFile.new()
    if cfg.load(CFG_PATH) != OK:
        return
    var w := get_window()
    var screen: int = cfg.get_value("window", "screen", 0)
    if screen >= DisplayServer.get_screen_count():
        screen = 0  # the monitor it was on is gone
    var usable := DisplayServer.screen_get_usable_rect(screen)
    var size: Vector2i = cfg.get_value("window", "size", w.size)
    var pos: Vector2i = cfg.get_value("window", "position", w.position)
    # Clamp so at least the title area is reachable.
    pos = pos.clamp(usable.position, usable.position + usable.size - Vector2i(64, 64))
    w.current_screen = screen
    w.size = size.clamp(Vector2i(200, 150), usable.size)
    w.position = pos
```

> ✅ **Best practice** — Restore geometry *before* showing meaningful content (first frames at the wrong position then jumping looks glitchy), and debounce saves — writing a config file on every pixel of a drag is a disk-thrash anti-pattern; save on `close_requested` and on a 2 s debounce after the last move.

---

## 10. System Tray Integration with StatusIndicator

Since Godot 4.3, the engine ships a dedicated node for notification-area icons: **`StatusIndicator`**. For a companion app the tray icon is not decoration — it is the enabling feature for the HIDDEN state: the app can leave the taskbar entirely and keep living at ≈0% CPU.

Platform reality first: per the class documentation, the status indicator is **implemented on macOS and Windows**. On Linux, tray support depends on the desktop environment and is not guaranteed — design so the tray is an enhancement, not a requirement (always provide a windowed path to every feature).

### 10.1 The node

| Member | Type | Purpose |
|---|---|---|
| `icon` | `Texture2D` | The tray image (supply crisp sizes; small, simple glyphs read best) |
| `tooltip` | `String` | Hover text |
| `menu` | `NodePath` | Path to a `PopupMenu` shown natively on click (needs native-menu support on the platform) |
| `visible` | `bool` | Show/hide the indicator |
| `pressed(mouse_button: int, mouse_position: Vector2i)` | signal | Click handler; *not emitted for clicks that open the assigned menu* |
| `get_rect()` | method | Indicator's screen rect (`Rect2`), empty if not visible |

### 10.2 Minimize-to-tray recipe

The complete pattern: intercept close, hide instead of quit, restore from the tray, quit only from the menu.

```gdscript
# main_window.gd — attached to the main scene root.
extends Control

@onready var _tray: StatusIndicator = $StatusIndicator
@onready var _tray_menu: PopupMenu = $TrayMenu

enum TrayItem { OPEN, PAUSE_SOUNDS, QUIT }

func _ready() -> void:
    # 1. Take over the close button: closing hides to tray instead of quitting.
    get_tree().set_auto_accept_quit(false)
    get_window().close_requested.connect(_on_close_requested)

    # 2. Build the native menu.
    _tray_menu.add_item("Open Relax Room", TrayItem.OPEN)
    _tray_menu.add_check_item("Pause sounds", TrayItem.PAUSE_SOUNDS)
    _tray_menu.add_separator()
    _tray_menu.add_item("Quit", TrayItem.QUIT)
    _tray_menu.id_pressed.connect(_on_tray_menu_pressed)

    _tray.tooltip = "Relax Room — running"
    _tray.menu = _tray_menu.get_path()
    _tray.pressed.connect(_on_tray_pressed)

func _on_close_requested() -> void:
    _hide_to_tray()

func _hide_to_tray() -> void:
    get_window().hide()
    # PerformanceManager sees no visible window → HIDDEN state applies.

func _restore_from_tray() -> void:
    var w := get_window()
    w.show()
    w.mode = Window.MODE_WINDOWED
    w.grab_focus()

func _on_tray_pressed(mouse_button: int, _pos: Vector2i) -> void:
    # Left-click toggles the window; the menu handles right-click natively.
    if mouse_button == MOUSE_BUTTON_LEFT:
        if get_window().visible:
            _hide_to_tray()
        else:
            _restore_from_tray()

func _on_tray_menu_pressed(id: int) -> void:
    match id:
        TrayItem.OPEN:
            _restore_from_tray()
        TrayItem.PAUSE_SOUNDS:
            var idx := _tray_menu.get_item_index(TrayItem.PAUSE_SOUNDS)
            var now_paused := not _tray_menu.is_item_checked(idx)
            _tray_menu.set_item_checked(idx, now_paused)
            Audio.set_ambient_paused(now_paused)  # app-specific autoload
        TrayItem.QUIT:
            _quit_for_real()

func _quit_for_real() -> void:
    # Flush saves before leaving (see DATABASE_AND_PERSISTENCE.md).
    Settings.flush()
    get_tree().quit()
```

Details that separate polished from janky:

- **`set_auto_accept_quit(false)` is mandatory** — without it the engine quits on the close button before your handler matters. Once set, *you* own every quit path; forgetting the `TrayItem.QUIT` branch makes the app unkillable except via task manager (users notice).
- **Hidden window vs minimized window:** `hide()` removes the taskbar presence entirely (true tray app); `Window.MODE_MINIMIZED` keeps the taskbar button. Pick one policy; supporting both confuses the state machine and users.
- **The `PerformanceManager` should treat "not visible" like minimized:** extend `_poll_window_mode()` to also check `not get_window().visible` → HIDDEN.

### 10.3 Single-instance guard

Launching a companion twice (autostart + manual launch, double double-click) must not produce two mascots and two audio streams. Godot has no built-in single-instance flag, so use the standard local-socket pattern: the first instance listens on a localhost port; later instances detect it, tell it to show itself, and exit.

```gdscript
# autoloads/single_instance.gd — register FIRST in the autoload order.
extends Node

const PORT: int = 53917  # any fixed uncommon port; make it configurable

var _server: TCPServer

func _ready() -> void:
    _server = TCPServer.new()
    var err := _server.listen(PORT, "127.0.0.1")
    if err != OK:
        _notify_primary_and_quit()
        return
    # We are the primary instance; poll for pings at low frequency.
    var t := Timer.new()
    t.wait_time = 0.5
    t.timeout.connect(_poll_peers)
    add_child(t)
    t.start()

func _notify_primary_and_quit() -> void:
    var peer := StreamPeerTCP.new()
    if peer.connect_to_host("127.0.0.1", PORT) == OK:
        # Give the connection a moment, then send the wake command.
        peer.poll()
        peer.put_utf8_string("SHOW")
    get_tree().quit()

func _poll_peers() -> void:
    while _server.is_connection_available():
        var peer := _server.take_connection()
        peer.poll()
        if peer.get_available_bytes() > 0:
            var msg := peer.get_utf8_string(peer.get_available_bytes())
            if msg.contains("SHOW"):
                get_tree().root.propagate_notification(
                    NOTIFICATION_APPLICATION_FOCUS_IN)
                get_window().show()
                get_window().grab_focus()
```

The 0.5 s poll costs nothing measurable and only exists in the primary instance. Alternative guards: a lock file with the PID (check staleness with `OS.is_process_running(pid)`) is simpler but cannot *activate* the first instance; the socket pattern gives you "clicking the icon again focuses the running app" — the behavior users actually expect.

> ⚠️ **Pitfall** — A fixed port can collide with another app. Handle `listen()` failure + failed connect as "port squatted by a stranger": fall back to running normally rather than silently quitting, or derive the port from a hash of the user data dir.

---

## 11. Profiling Workflow

Optimization without measurement is superstition. Godot's built-in tooling — the Profiler, the Visual Profiler, the Monitors tab and custom monitors — covers 90% of companion-app needs; the remaining 10% is OS-level verification (section 16).

### 11.1 The Profiler tab, step by step

The core loop, preserved and expanded from this module's first edition:

1. **Run the project from the editor** (profiling works over the debugger connection; it also works on exported debug builds attached remotely).
2. Open **Debugger → Profiler** and press **Start**.
3. **Reproduce the scenario you care about** — and for a companion, "scenario" includes *idle*: profile 60 seconds of doing nothing, because that is your app's real workload.
4. Press **Stop**. Click a frame in the graph to inspect it; the spike frames are the interesting ones for stutter, the *typical* frames for energy.
5. Sort the function list by **Self** time (a.k.a. self/exclusive time — time inside the function excluding its callees). Sorting by total time leads you to `_process` wrappers; sorting by self time leads you to culprits.
6. **Fix the top item. Re-measure. Repeat.** One change per measurement; two changes per measurement is how teams end up keeping a useless "optimization" for years.

The frame graph plots frame time (ms), physics time and idle time per frame. Two companion-specific reading skills:

- **A healthy idle profile at a 15 FPS cap** shows tall *frame intervals* (66 ms) but tiny *busy* time per frame (1–3 ms). If busy time is a large fraction of the interval even when idle, you have per-frame work to eliminate (section 7), not a frame-rate problem.
- **Script functions view during idle should be near-empty.** Every `_process` listed there while the app is untouched is a lead. This single view has paid for this module many times over.

> ⚠️ **Pitfall** — The profiler itself costs time, and running from the editor changes timings (debug builds, collision between editor and game for GPU). Use profiler numbers *relatively* (before vs after, function A vs B), never as absolute shipping numbers. Absolute claims come from release exports measured with OS tools.

### 11.2 The Visual Profiler and Video RAM tabs

The **Visual Profiler** tab records per-frame CPU and GPU rendering time, broken down by rendering stage — the tool for answering "is this frame CPU-bound or GPU-bound?" For companions the typical discovery is a GPU-cheap scene made GPU-expensive by one fullscreen shader or an unthrottled particle system; the stage breakdown points straight at it. The **Video RAM** tab lists textures and their sizes — your first stop when the VRAM budget row fails (that 4096×4096 background you "temporarily" imported uncompressed will be at the top).

### 11.3 The Monitors tab

**Debugger → Monitors** graphs engine counters over time while the game runs — no start/stop, always recording. The most useful for companions:

| Monitor | Enum (`Performance.`) | Watch for |
|---|---|---|
| FPS | `TIME_FPS` | Cap adherence per power state |
| Process time | `TIME_PROCESS` | Idle busy-time creep |
| Physics process time | `TIME_PHYSICS_PROCESS` | Cost of un-lowered tick rate |
| Static memory | `MEMORY_STATIC` | Long-session growth = leak |
| Peak static memory | `MEMORY_STATIC_MAX` | Spikes from loads |
| Objects | `OBJECT_COUNT` | Monotonic growth = object leak |
| Resources | `OBJECT_RESOURCE_COUNT` | Cache growth |
| Nodes | `OBJECT_NODE_COUNT` | Scene-transition hygiene |
| **Orphan nodes** | `OBJECT_ORPHAN_NODE_COUNT` | Should be 0; anything else is a leak (section 14) |
| Draw calls | `RENDER_TOTAL_DRAW_CALLS_IN_FRAME` | Batching regressions |
| Video memory | `RENDER_VIDEO_MEM_USED` | VRAM budget row |
| Texture memory | `RENDER_TEXTURE_MEM_USED` | Import-settings mistakes |

All of these are also queryable in code — `Performance.get_monitor(Performance.MEMORY_STATIC)` — which is how the HUD and CSV logger in section 16 work.

### 11.4 Custom monitors

`Performance.add_custom_monitor()` registers your own metric; it appears in the Monitors tab alongside the built-ins and is queryable via `get_custom_monitor()`. Signature: `add_custom_monitor(id: StringName, callable: Callable, arguments: Array = [], type: MonitorType = 0)` — a slash in the id creates a category in the UI.

```gdscript
# autoloads/performance_manager.gd (continued)
func _register_custom_monitors() -> void:
    Performance.add_custom_monitor("relax_room/power_state",
        func() -> int: return state)
    Performance.add_custom_monitor("relax_room/active_sounds",
        Audio.count_playing_streams)
    Performance.add_custom_monitor("relax_room/tween_count",
        func() -> int: return get_tree().get_processed_tweens().size())
```

The callable is invoked by the engine when the monitor is sampled and must return a number. Custom monitors turn app-specific invariants ("no more than 6 streams", "tween count returns to baseline after every transition") into *graphs you can watch*, which is how you catch the leak the day you write it instead of in the 24 h soak test.

> ✅ **Best practice** — Register custom monitors only in debug builds (`if OS.is_debug_build():`). They are cheap, but the callables run per sample and a shipped companion should not carry instrumentation the user cannot see. The CSV logger (section 16) is the shipping-grade instrumentation.

### 11.5 A worked example: the idle that wasn't

A realistic end-to-end hunt, condensed from a Relax Room development log, to make the workflow concrete.

**Symptom:** IDLE state (15 FPS cap) still shows 4% CPU in Task Manager on the reference laptop — budget says ≤ 1%.

**Step 1 — confirm in-engine.** Monitors tab: `TIME_FPS` correctly reads 15, so the cap holds. `TIME_PROCESS` reads ~11 ms — the busy time per frame is 11 ms out of a 66 ms interval. That ratio (17% duty cycle at 15 FPS) explains the CPU number. Diagnosis so far: frame *cost* problem, not frame *rate* problem (section 2.4's distinction, live).

**Step 2 — profile 60 idle seconds.** Profiler, sorted by self time, typical frame:

| Function | Calls/frame | Self time |
|---|---|---|
| `SoundBoard._process` | 1 | 4.9 ms |
| `WaveformWidget._draw` | 1 | 3.1 ms |
| `TooltipManager._process` | 1 | 1.4 ms |
| (engine + misc) | — | ~1.6 ms |

**Step 3 — read the code behind the top entry.** `SoundBoard._process` looped over 40 sound-tile Controls every frame updating volume-meter bars — even though in IDLE no meters are visible and volumes change only on user action. Classic polling. Fix: meters update from an `AudioServer`-driven timer at 10 Hz, only while their tab `is_visible_in_tree()` (section 8.4's throttle node). `_process` deleted outright.

**Step 4 — re-measure.** `TIME_PROCESS` drops to ~6 ms. Repeat: `WaveformWidget._draw` ran every frame because a stray `queue_redraw()` sat in a tween callback that looped. Fix: redraw only when the waveform data changes. `TooltipManager` polled the hovered control; replaced with `mouse_entered`/`mouse_exited` signals.

**Step 5 — end state.** `TIME_PROCESS` ~0.9 ms; Task Manager settles at 0.6–0.9% in IDLE. Budget met. Elapsed time for the whole hunt: under an hour, *because* the workflow was mechanical: confirm → profile → top item → fix → re-measure, never guessing.

The general lesson: in companion apps the profiler's top entries are rarely exotic — they are almost always a polling `_process`, an unconditional `_draw`, or an unthrottled widget, installed months earlier when the app was a prototype. The profiler exists to tell you *which* of your old sins is the expensive one.

---

## 12. GDScript Micro-Costs and Offloading Work

Frequency dominates (section 3), but once the loop runs as rarely as possible, the cost *per execution* is the next dial. GDScript is an interpreted language; in a long-running app, small per-call costs compound into measurable energy. The rules below are ordered by real-world payoff in companion codebases.

### 12.1 Type everything

Typed GDScript is not just documentation — the compiler emits faster instructions for typed code paths: typed variables avoid Variant boxing/checks, typed arrays skip element validation, and typed function signatures let calls skip argument conversion. In hot code (anything reachable from `_process`, `_input`, or a 1 s heartbeat) this is free performance:

```gdscript
# Untyped: every operation goes through Variant dispatch.
var speed = 100
func move(delta):
    position.x += speed * delta

# Typed: static dispatch, no boxing, and the editor catches errors.
var speed: float = 100.0
func move(delta: float) -> void:
    position.x += speed * delta
```

Project-wide discipline: enable `debug/gdscript/warnings/untyped_declaration` in Project Settings and treat the warning as an error in review. The whole codebase being typed also unlocks honest profiler numbers (untyped hot spots often masquerade as "engine overhead").

### 12.2 Allocate nothing per frame

Every `[]`, `{}`, `"a" + b`, `PackedVector2Array()` or lambda created in `_process` is a heap allocation that the reference-counting machinery must later reclaim. One allocation is nothing; 60 per second for 8 hours is 1.7 million allocations that fragment memory and burn cycles. Patterns:

```gdscript
# BAD: allocates a new array and three strings every frame.
func _process(_delta: float) -> void:
    var parts := ["FPS: ", str(Engine.get_frames_per_second())]
    $Label.text = "".join(parts)

# GOOD: no per-frame work at all — the label updates on a 1 s heartbeat,
# and only when the value actually changed.
var _last_fps: int = -1
func _on_heartbeat_tick_1s() -> void:
    var fps := int(Engine.get_frames_per_second())
    if fps != _last_fps:
        _last_fps = fps
        %FpsLabel.text = "FPS: %d" % fps
```

Reusable buffers for genuinely per-frame math:

```gdscript
var _points: PackedVector2Array = PackedVector2Array()

func _rebuild_wave(sample_count: int) -> void:
    _points.resize(sample_count)   # reuses capacity; no realloc if same size
    for i in sample_count:
        _points[i] = Vector2(float(i), _height_at(i))
```

> ⚠️ **Pitfall** — Setting `Label.text` (or any Control property) to the *same value* still marks work dirty in some paths and at minimum costs a string compare per call — but building the string first costs the allocation regardless. The "only when changed" guard must wrap the *string construction*, not just the assignment, as in the GOOD example above.

### 12.3 Cache node lookups

`get_node("Path/To/Node")` and `$Path/To/Node` walk the tree by name on every call. In `_ready`-time code, irrelevant; in per-frame code, a measurable tax. The idiom is `@onready` caching (or scene-unique names `%NodeName`, which are resolved via a cached map — still cache them in a variable for hot loops):

```gdscript
# BAD: tree walk 60×/sec.
func _process(delta: float) -> void:
    get_node("Mascot/Sprite2D").rotation += delta

# GOOD: resolved once.
@onready var _mascot_sprite: Sprite2D = $Mascot/Sprite2D
func _process(delta: float) -> void:
    _mascot_sprite.rotation += delta
```

### 12.4 Strings, StringNames, and signals

- Prefer `StringName` (`&"jump"`) for identifiers compared repeatedly (input actions, animation names, dictionary keys); comparison is pointer-fast versus character-wise for `String`.
- Build user-visible strings with `%` formatting or `String.format()` once per change, never per frame (the original module's advice — do not do `"Score: " + str(score)` in a hot loop — generalized).
- Signal emission cost is small (roughly a dynamic call per connection) and *events beat polling* by such a margin that signals are still the answer; just avoid designing signals that fire per frame with many listeners. A `power_state_changed` firing a few times per hour is free; a `progress_changed` firing 60×/s into eight listeners is a design smell — let listeners sample a property on their own cadence instead.
- Connections with `CONNECT_ONE_SHOT` self-disconnect — use them for "next time X happens" logic instead of manual disconnect bookkeeping (leak-prone; see section 14).

### 12.5 The price list: order-of-magnitude costs

Micro-optimization needs a sense of scale, or you will spend a day shaving something that costs nanoseconds while a disk write hides in the same loop. Approximate costs on a mid-range desktop CPU, release build — treat the *ratios* as the lesson, not the absolute numbers (measure your own with the harness below):

| Operation | Order of magnitude | Companion-app implication |
|---|---|---|
| Typed arithmetic, `Vector2` math | ~0.01–0.05 µs | Never the problem |
| Typed GDScript function call | ~0.1–0.3 µs | Fine even in hot loops |
| Untyped/Variant-heavy call | 2–4× the typed cost | Type your hot paths |
| `signal.emit()` per connection | ~0.3–1 µs | Free at event rates; a smell at per-frame rates × many listeners |
| Dictionary lookup (StringName key) | ~0.1–0.3 µs | Preferred key type |
| `String` concatenation (small) | ~0.5–2 µs + allocation | Gate behind change checks |
| `get_node()` with a 3-segment path | ~1–3 µs | `@onready`-cache in anything per-frame |
| `Node.new()` + `add_child()` | ~10–100 µs | Pool or reuse; never per frame |
| Scene `instantiate()` (small scene) | ~0.1–1 ms | Only on user action, or deferred |
| `FileAccess` small write + flush | ~0.1–5 ms (device-dependent) | Debounce; never per frame; offload if large |
| `load()` of a mid-size texture | ~1–50 ms | Preload at boot or background-load; never on a hot path |
| HTTP request round-trip | ~50–500 ms | Always async (`HTTPRequest`), always on a slow cadence |

Note the vertical span: the table covers *seven orders of magnitude*. The practical reading order is bottom-up — eliminate the millisecond-class items from recurring paths first (file writes, loads, instantiations), then the microsecond-class ones only if the profiler still points at them.

**Object pooling**, the standard fix for the `Node.new()` row when an effect genuinely recurs (notification toasts, floating "+1" labels):

```gdscript
# toast_pool.gd — fixed pool of reusable toast labels.
extends Node

const POOL_SIZE: int = 8
var _free: Array[Label] = []

func _ready() -> void:
    for i in POOL_SIZE:
        var l := Label.new()
        l.visible = false
        add_child(l)
        _free.append(l)

func show_toast(text: String, at: Vector2) -> void:
    if _free.is_empty():
        return  # drop rather than allocate; toasts are disposable
    var l: Label = _free.pop_back()
    l.text = text
    l.position = at
    l.visible = true
    var tw := l.create_tween()
    tw.tween_property(l, "position:y", at.y - 24.0, 0.8)
    tw.tween_property(l, "modulate:a", 0.0, 0.3)
    tw.finished.connect(func() -> void:
        l.modulate.a = 1.0   # reset state for next reuse
        l.visible = false
        _free.append(l), CONNECT_ONE_SHOT)
```

Pooling trades a little bookkeeping for zero steady-state allocation — worth it precisely when the profiler shows creation cost *or* the soak chart shows allocation churn; not worth it speculatively for things created once a minute.

### 12.6 Micro-benchmark harness

When two implementations compete, measure with `Time.get_ticks_usec()` on a release-mode export (debug builds distort GDScript timings):

```gdscript
func benchmark(label: String, iterations: int, f: Callable) -> void:
    var start := Time.get_ticks_usec()
    for i in iterations:
        f.call()
    var us := Time.get_ticks_usec() - start
    print("%s: %d iters in %d µs (%.3f µs/iter)"
        % [label, iterations, us, float(us) / float(iterations)])
```

Benchmark rules: warm up once before timing (JIT-less, but caches warm), run ≥ 100k iterations for sub-µs operations, compare medians of 5 runs, and only trust differences > 20% — GDScript timing noise is real.

### 12.7 Offloading: WorkerThreadPool and friends

Some work is legitimately heavy: parsing a big JSON settings file, scanning a music library, generating a waveform. On the main thread, 80 ms of work is a visible hitch — at 60 FPS that is five dropped frames, and in a companion it happens exactly when the user just clicked something. Offload it:

```gdscript
# Scanning the user's ambient-sound library without blocking the UI.
func rescan_library(dir_path: String) -> void:
    %ScanSpinner.visible = true
    var task_id := WorkerThreadPool.add_task(_scan_worker.bind(dir_path))
    # Poll completion from a timer, or block in a controlled place:
    _await_task(task_id)

func _scan_worker(dir_path: String) -> void:
    var found: PackedStringArray = PackedStringArray()
    for file in DirAccess.get_files_at(dir_path):
        if file.get_extension() in ["ogg", "wav", "mp3"]:
            found.append(dir_path.path_join(file))
    # NEVER touch nodes from a worker thread — hand results back:
    _apply_scan_results.call_deferred(found)

func _apply_scan_results(found: PackedStringArray) -> void:
    %ScanSpinner.visible = false
    Library.set_files(found)  # main thread again: safe

func _await_task(task_id: int) -> void:
    # Cheap completion check at 10 Hz; wait_for_task_completion would block.
    var t := Timer.new()
    t.wait_time = 0.1
    t.timeout.connect(func() -> void:
        if WorkerThreadPool.is_task_completed(task_id):
            WorkerThreadPool.wait_for_task_completion(task_id)  # returns instantly; releases the task
            t.queue_free())
    add_child(t)
    t.start()
```

The iron rules, in concert with [Autoload Safety](AUTOLOAD_SAFETY.md)'s threading section:

1. **Worker threads must not touch the SceneTree** (nodes, servers with thread-unsafe surfaces). Compute into plain data; marshal back with `call_deferred()`, which queues the call onto the main thread.
2. **`WorkerThreadPool` over raw `Thread`** for one-shot jobs: the pool reuses OS threads (thread creation is not cheap) and its size matches core count.
3. **Do not spawn threads to *poll*.** A thread that loops checking something is a busy CPU core wearing a disguise. Threads are for finite jobs; recurring cheap checks stay on main-thread timers.
4. **File IO for saves is usually fine on the main thread if small and rare** — a 2 KB config write is microseconds. Offload IO when it is large (library scans) or on a latency-critical path.

> ✅ **Best practice** — Instrument hitches before assuming them: log any `_process` delta above 2× the expected interval (`if delta > threshold: push_warning(...)`). If the log shows hitches whenever the settings save fires, *that* save is your offload candidate — not the ten other things you suspected.

---

## 13. GPU Optimization for Idle Scenes

A companion's GPU story has a twist: the GPU is extremely good at rendering our tiny scenes, so raw frame *rate* is never the issue — **keeping the GPU asleep** is. Discrete and integrated GPUs alike have aggressive low-power states they enter when idle; an app that submits work every 16 ms keeps waking them, and GPU wakeups are among the most battery-expensive things a background app can do. The FPS cap (fewer submissions) is again the first-order fix; this section covers the second-order ones.

### 13.1 Draw calls still matter — for CPU and energy

Each draw call costs CPU time in the rendering server and driver before the GPU sees it. The 2D renderer batches aggressively: consecutive `CanvasItem`s sharing texture and material render in one call; every texture switch, material change, or `z_index`/clipping boundary breaks the batch. The classic levers (detailed in [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) and [Sprites and Textures](SPRITES_AND_TEXTURES.md)):

- **Atlas your sprites** (the import system and `AtlasTexture` both work): one texture → unbroken batches → fewer calls. This was the original module's advice and it stands.
- **Fewer CanvasItems beat clever CanvasItems.** Every visible node has per-item overhead. A background assembled from 40 decorative `Sprite2D`s can often be one pre-composited texture. For dozens of identical repeated elements, `MultiMeshInstance2D` collapses them to one call.
- **Watch `RENDER_TOTAL_DRAW_CALLS_IN_FRAME`** in the Monitors tab while building scenes. For a companion scene, double digits is normal, low hundreds is acceptable, thousands means a Label-heavy UI or broken batching (note: text rendering contributes draw calls; a debug HUD full of labels inflates the number it is measuring — keep the HUD minimal).

### 13.2 Overdraw and transparency

Overdraw — shading the same pixel multiple times — is the quiet GPU tax of layered 2D scenes. Transparent pixels cannot be skipped by early-out optimizations: a fullscreen `ColorRect` at `modulate.a = 0.05` still costs a fullscreen blend. Companion-specific advice:

- Layered ambient backgrounds (sky + haze + glow + vignette) multiply fullscreen blends. Pre-composite static layers into one texture; keep only genuinely animated layers separate.
- An invisible Control with `modulate.a = 0.0` may still render depending on how it is hidden — set `visible = false` and it is skipped entirely (and remember section 7: also `set_process(false)`).
- Per-pixel window transparency (section 9.2) adds compositor-level overdraw on top of in-app overdraw; transparent companions should be small windows.

### 13.3 TIME-driven shaders keep the GPU awake

The single most companion-relevant shader fact: **a shader that animates via the built-in `TIME` uniform produces a different image every frame, so every frame must be rendered.** Your beautiful drifting-gradient background makes redraw-on-demand impossible and guarantees GPU work at whatever FPS the cap allows — even when the scene is otherwise static (this is why Relax Room cannot use `low_processor_usage_mode` while visible; see section 6.3).

The fix is *conditional animation*: gate time-driven effects behind a uniform the power-state machine controls.

```glsl
// background_gradient.gdshader
shader_type canvas_item;

uniform bool animate = true;
uniform float speed = 0.05;
uniform sampler2D gradient_tex;

void fragment() {
    float t = animate ? TIME * speed : 0.0;
    vec2 uv = UV + vec2(sin(t) * 0.02, t * 0.01);
    COLOR = texture(gradient_tex, uv);
}
```

```gdscript
# Subscriber (see section 4.1) freezes the shader when not ACTIVE:
func _on_power_state_changed(new_state: Perf.PowerState) -> void:
    var mat := $Background.material as ShaderMaterial
    mat.set_shader_parameter("animate", new_state == Perf.PowerState.ACTIVE)
```

With `animate = false` the shader output becomes constant; combined with an otherwise-static scene the renderer's output stops changing, and under low-processor mode redraws stop entirely. Freezing at `t = 0.0` snaps the effect; for polish, pass a frozen time value captured at transition instead of `0.0`.

The same reasoning applies to particles (`GPUParticles2D.emitting = false`, or `speed_scale = 0` to freeze mid-air), `AnimatedSprite2D` (`pause()`), and video players. Inventory every "always moving" element in your scene and give each an idle policy; the inventory is usually shorter than feared, and each unfrozen element is a permanent tax.

### 13.4 Effects, viewport scale, and the idle look

- **2D lighting, glow and screen-space effects** cost per-pixel work each frame. If your aesthetic needs glow while ACTIVE, consider disabling it (`WorldEnvironment` adjustments) in IDLE — at 15 FPS in peripheral vision, nobody sees the difference.
- **Viewport scaling:** rendering the scene at reduced resolution into a `SubViewport` and stretching is a blunt but effective idle trick for shader-heavy scenes — quarter-resolution at 15 FPS is ~1/16 the fragment work of full-res 60.
- Windows are usually small; do not ship a 4K-capable render path for a 400×600 widget. Fixed window size = fixed GPU budget.

### 13.5 Choosing the rendering method

Project setting `rendering/renderer/rendering_method` (restart required) selects among three pipelines, and for a 2D desktop companion the choice is meaningful:

| Method | Backend | Character | Companion fit |
|---|---|---|---|
| `forward_plus` | Vulkan (D3D12 where configured) | Full-featured 3D pipeline, highest baseline overhead | Overkill for 2D; larger VRAM/startup footprint |
| `mobile` | Vulkan | Leaner Forward renderer for mobile-class GPUs | Middle ground; still Vulkan baseline |
| `gl_compatibility` | OpenGL 3.3 / GLES 3 / WebGL 2 | Lowest baseline overhead, broadest hardware support | **Usually the right choice for a 2D companion** — lower idle overhead, runs on old iGPUs, faster startup |

The Compatibility renderer lacks Forward+'s advanced 3D features — which a 2D companion does not use — and in exchange gives a lighter runtime on exactly the weak integrated GPUs your users' office laptops have. Relax Room ships `gl_compatibility`. Validate your shaders under it early (a few high-end shader features differ; see [Shaders](SHADERS_GDSHADER.md)), and export-template implications in [Build and Export](BUILD_AND_EXPORT.md).

> ✅ **Best practice** — Decide the rendering method in week one, not week twenty. It shapes shader authoring, effect availability and testing hardware; switching late invalidates every performance number you have collected.

### 13.6 CanvasItem costs people forget

A grab-bag of 2D costs that repeatedly surprise companion developers, each small alone and meaningful in aggregate:

- **`_draw()` runs when redrawn, but `queue_redraw()` decides when.** A custom-drawn widget calling `queue_redraw()` in `_process` redraws every frame whether anything changed or not — the drawing equivalent of polling. Call `queue_redraw()` only from the code paths that change what is drawn (the worked example in section 11.5 caught exactly this).
- **`CanvasGroup`** renders its children into an intermediate buffer before compositing — convenient for group opacity, but it is an extra render target and a fullscreen-ish blend per group per frame. Use sparingly; for static groups, pre-composite.
- **`clip_contents` / clipping** on Controls introduces scissor/stencil work per clipped subtree. Cheap in moderation, not free in dozens of nested scroll containers.
- **2D lights and shadows**: every `Light2D`-family node multiplies fill cost over its covered area, and shadow-casting occluders add passes. An ambient companion wanting a "lamp glow" is almost always better served by a pre-baked glow sprite than a real `PointLight2D`.
- **Y-sorting** (`CanvasItem.y_sort_enabled`) re-sorts children by position; trivial for tens of items, but do not enable it on a container with hundreds of nodes out of habit — a companion's UI rarely needs it at all.
- **Fonts and text**: every glyph is geometry; a `RichTextLabel` with BBCode animations re-lays-out and redraws on change. Label-heavy dashboards should update text on timers, not per frame (section 12.2's change-guard), and outline/shadow font features multiply glyph draw cost.
- **`TextureRect` stretch vs pre-scaled assets**: scaling a 2048² texture down to a 200-pixel widget every frame wastes bandwidth and VRAM; import a right-sized asset instead ([Sprites and Textures](SPRITES_AND_TEXTURES.md) covers import-time resizing and compression).

None of these justify contortions in a scene that already meets budget — the Monitors tab decides. They matter when the GPU side of the Visual Profiler says the frame is more expensive than its pixel count suggests it should be.

---

## 14. Memory Discipline and Leak Hunting

A game leaking 1 MB/minute ships anyway — sessions end. A companion leaking 1 MB/minute has consumed 1.4 GB by tomorrow morning and *will* be noticed, swap-thrash the machine, and earn the review that kills the product. Memory flatness over time is a headline budget row (section 2.2), and this section is the toolkit for achieving it.

### 14.1 The measurement surface

| API | Returns | Use |
|---|---|---|
| `Performance.get_monitor(Performance.MEMORY_STATIC)` | Bytes of engine-allocated memory | The primary trend line |
| `Performance.get_monitor(Performance.MEMORY_STATIC_MAX)` | Peak since launch | Spike detection |
| `OS.get_static_memory_usage()` / `get_static_memory_peak_usage()` | Same data, OS-object surface | Non-debug availability nuances; use whichever you standardize on |
| `OS.get_memory_info()` | Dictionary with system-level info (physical, free, …) | Machine context in logs |
| `Performance.get_monitor(Performance.OBJECT_COUNT)` | Live Object instances | Object leaks (GDScript has no `ObjectDB` singleton — this monitor *is* your ObjectDB counter) |
| `Performance.get_monitor(Performance.OBJECT_NODE_COUNT)` | Live nodes in the tree | Scene hygiene |
| `Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)` | Nodes alive but **not in the tree** | The leak smoking gun |
| `Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT)` | Live resources | Cache growth |
| `Node.print_orphan_nodes()` (static) | Prints orphan nodes' instance IDs and names | Identifying *which* nodes leaked |
| `RENDER_VIDEO_MEM_USED` / `RENDER_TEXTURE_MEM_USED` / `RENDER_BUFFER_MEM_USED` monitors | VRAM byte counts | The VRAM budget row |

Note the important distinction: **engine static memory ≠ process working set.** `MEMORY_STATIC` tracks the engine's own allocations; the OS-visible footprint adds the executable, graphics driver allocations, audio buffers and thread stacks. Both matter: trend the engine number in-app (it isolates *your* leaks), and verify the process number in Task Manager (it is what users see). A flat `MEMORY_STATIC` with a climbing working set points at driver/GPU-side growth — often texture churn.

### 14.2 Orphan nodes: the classic Godot leak

Nodes are **not** reference-counted. `remove_child(node)` detaches a node but does not free it; if no code ever calls `node.free()`/`queue_free()`, it lives forever — updating, holding textures, connected to signals — as an *orphan*. Typical sources in companion code:

- Popups/panels created per use and removed but never freed ("I'll reuse it later" — and later never comes).
- Scene transitions that `remove_child` the old scene to keep it warm, without an ownership plan.
- Nodes created in unit-test-style tool scripts and forgotten.

Detection is mercifully easy:

```gdscript
# Debug hook — e.g. on a hidden hotkey or after every scene transition:
func _debug_check_orphans() -> void:
    var orphans := Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)
    if orphans > 0:
        push_warning("Orphan nodes: %d" % int(orphans))
        Node.print_orphan_nodes()   # prints instance IDs + node names/paths
```

Additionally, run the project with **verbose output** (`--verbose`) during development: on exit, the engine reports leaked instances/resources — a free end-of-session leak audit. The fix is an ownership rule: *every dynamically created node has exactly one owner responsible for `queue_free()`*, and detached-but-kept nodes are held in a named member (`_cached_panel`), never in a local that goes out of scope.

> ⚠️ **Pitfall** — `queue_free()` frees at the end of the current frame; `free()` is immediate. Signal callbacks that fire later in the same frame may still touch a queue-freed node — use `is_instance_valid(node)` guards in callbacks that can race a deletion, and prefer `queue_free()` (immediate `free()` during signal dispatch is a crash generator).

### 14.3 Tween, timer and signal leaks in long-lived apps

Three leak patterns that specifically bite apps which run for days:

**Looping tweens.** `create_tween().set_loops()` runs forever until killed. Create one per hover event without killing the previous and you accumulate live tweens — each ticking every frame, visible in `get_tree().get_processed_tweens().size()` (we registered it as a custom monitor in section 11.4). Discipline:

```gdscript
var _pulse: Tween

func _start_pulse() -> void:
    if _pulse and _pulse.is_valid():
        _pulse.kill()                       # kill the predecessor, always
    _pulse = create_tween().set_loops()
    _pulse.tween_property($Icon, "scale", Vector2.ONE * 1.08, 0.6)
    _pulse.tween_property($Icon, "scale", Vector2.ONE, 0.6)
```

Tweens are also bound to the node that created them (they stop when it leaves the tree) — create tweens from the node they animate, not from a long-lived autoload, so their lifetime is naturally bounded.

**Re-connecting signals.** Calling `connect()` on every open of a panel without a matching `disconnect()` stacks connections: after 50 opens, one emission runs the handler 50 times — a *logic* bug and a *memory* bug (connections keep Callables, which keep captured objects alive). Guard with `is_connected()`, connect once in `_ready`, or use `CONNECT_ONE_SHOT` for transient interest.

**Accumulating scene-tree timers.** `get_tree().create_timer()` in a hot path creates a new timer object each call; they self-free on timeout, but a burst (e.g. per input event) creates hundreds in flight. Re-arm one `Timer` node instead.

**Growing collections.** The humblest leak: an `Array` of "recent events", a `Dictionary` cache of thumbnails, a log string — appended forever, cleared never. Every long-lived collection needs a *bound* (ring buffer, LRU eviction, max size) declared at creation time. For caches of recreatable objects, hold `WeakRef`s so the cache never *keeps* anything alive:

```gdscript
var _thumb_cache: Dictionary = {}  # path -> WeakRef of ImageTexture

func get_thumb(path: String) -> ImageTexture:
    if _thumb_cache.has(path):
        var cached: ImageTexture = _thumb_cache[path].get_ref()
        if cached:
            return cached
    var tex := _make_thumb(path)
    _thumb_cache[path] = weakref(tex)
    return tex
```

### 14.4 Resource caching semantics

`load()`/`preload()` cache resources by path: loading the same path twice returns the same instance, and the cache holds it while referenced. This is a feature (no duplicate textures) with two sharp edges: (1) resources stay alive as long as *anything* references them — a lingering reference in a forgotten array keeps a 20 MB texture in VRAM; (2) `OBJECT_RESOURCE_COUNT` creeping up across scene transitions means references are accumulating somewhere. `ResourceLoader.load_threaded_request()`'s `cache_mode` parameter controls reuse/replacement behavior for background loads; the default (reuse) is right for companions.

### 14.5 The 24-hour soak test

The budget row "RAM slope ≈ 0 over 24 h" is verified by a **soak test** — the companion-app equivalent of a game's playtest. Methodology:

1. **Instrument:** enable the CSV metrics logger (section 16.2) at a 60 s sample interval: timestamp, power state, `MEMORY_STATIC`, `OBJECT_COUNT`, `OBJECT_NODE_COUNT`, `OBJECT_ORPHAN_NODE_COUNT`, `OBJECT_RESOURCE_COUNT`, FPS, VRAM.
2. **Script the life:** a soak test of pure idle only tests idle. Add a debug "life simulator" that, on a timer, randomly performs user-ish actions: open/close settings, switch soundscapes, hover things, minimize/restore. Real leaks live on the *transition* paths.
3. **Run 24 h on the reference machine**, release export, started from the OS (not the editor).
4. **Analyze the CSV:** plot memory and object counts vs time. Verdicts: **flat with plateaus** = healthy; **staircase up on every simulated action** = per-action leak (diff object counts across one action to localize); **slow constant ramp** = per-frame or per-timer leak (correlate slope with power state to find which loop).
5. **Localize:** reproduce the leaking action in the editor with the Monitors tab open, `print_orphan_nodes()` after each repetition, binary-search the action's code path.
6. **Fix, re-soak overnight, keep the CSVs** — the archive of soak charts per release is your memory-regression history.

> ✅ **Best practice** — Soak *before* every release, not once ever. Leaks regress silently: one refactor that swaps `queue_free()` for `remove_child()` undoes months of flatness, and only the soak chart will tell you.

### 14.6 Worked example: reading a staircase

To make the section 14.5 verdicts concrete, here is a condensed hunt through an actual staircase chart. The soak CSV, plotted, showed `mem_static_b` flat for stretches, then stepping up ~400 KB at irregular intervals; `objects` stepped in lockstep, `orphans` stayed 0. Interpretation: *not* a per-frame ramp (would be a smooth slope), *not* an orphan-node leak (counter clean) — something allocated per *event* and kept.

Correlating step timestamps with the life-simulator's action log (the simulator logs each action with a timestamp — do this, it turns charts into narratives) showed every step aligned with a "switch soundscape" action. Reproducing in the editor with the Monitors tab open confirmed: each switch added ~30 `OBJECT_COUNT` and ~25 `OBJECT_RESOURCE_COUNT`, never returning to baseline.

The code walk then took minutes: the soundscape switcher built a new `AudioStreamPlayer` per layer per switch and stored the *old* players in an array "for crossfade", which nothing ever cleared:

```gdscript
# The bug (simplified): _retiring grows forever.
_retiring.append(_current_players)   # keeps nodes AND their streams alive
_current_players = _build_players(new_scape)

# The fix: crossfade, then actually let go.
for p: AudioStreamPlayer in old_players:
    var tw := p.create_tween()
    tw.tween_property(p, "volume_db", -60.0, 2.0)
    tw.finished.connect(p.queue_free, CONNECT_ONE_SHOT)
```

Post-fix soak: steps gone, `objects` returns to baseline ±2 after every switch. Notice the division of labor across the toolkit: the **CSV chart** said "event-correlated retention", the **action log** said *which* event, the **Monitors tab** confirmed the reproduction, and only then did anyone read code. Leak hunts that start by reading code last hours; hunts that start with charts take minutes.

> ⚠️ **Pitfall** — When reproducing leaks in the editor, do each suspect action *several times*. Many systems legitimately allocate on first use (caches warming, first-time lazy inits) — a one-time bump after the first action is warmup, not a leak. The signature of a real leak is growth on the *Nth* repetition.

---

## 15. Startup Time and Background Loading

A companion launches at login. A slow launcher at login is a machine that feels slow *because of you* — and login storms (everything autostarting at once) amplify it. Startup budget for Relax Room: ≤ 2.5 s cold to interactive on the reference machine, with useful pixels far earlier.

### 15.1 Measure first

```gdscript
# First lines of the main scene's _ready:
func _ready() -> void:
    var startup_ms := Time.get_ticks_msec()   # ms since engine start
    print_verbose("Startup to main _ready: %d ms" % startup_ms)
```

`Time.get_ticks_msec()` counts from engine start, so its value in the first `_ready` approximates engine+project init cost. Add checkpoints (autoloads done, first frame drawn, heavy resources loaded) and log them; startup work is invisible precisely because nobody instruments it.

### 15.2 Cut the boot splash and boot weight

- `application/boot_splash/show_image = false` (or a tiny image with `application/boot_splash/bg_color` matched to your theme) — the default Godot splash costs a beat and screams "engine demo" instead of "desktop app".
- Autoloads run **before** the first scene, serially, in registration order — keep every autoload's `_ready` trivial ([Autoload Safety](AUTOLOAD_SAFETY.md) covers ordering); defer real work to after first frame.
- The biggest startup lever is *what the main scene preloads*: every `preload()` in a script attached to the boot path is paid before the window is useful.

### 15.3 Defer and background-load

Pattern one — **defer non-critical init past the first frame**:

```gdscript
func _ready() -> void:
    _build_minimal_ui()               # cheap: window appears now
    _late_init.call_deferred()        # runs after current frame's setup

func _late_init() -> void:
    _connect_online_services()
    _warm_thumbnail_cache()
```

Pattern two — **threaded scene loading with progress**, via `ResourceLoader`'s threaded API: `load_threaded_request(path, type_hint := "", use_sub_threads := false, cache_mode := 1)` starts the load on a background thread; `load_threaded_get_status(path, progress_out)` reports `THREAD_LOAD_IN_PROGRESS / _LOADED / _FAILED / _INVALID_RESOURCE` and fills a one-element array with completion ratio 0.0–1.0; `load_threaded_get(path)` returns the resource (blocking only if not yet done).

```gdscript
# loading_gate.gd — shows lightweight UI instantly, streams the heavy scene in.
extends Control

const MAIN_SCENE := "res://scenes/relax_room.tscn"
var _progress: Array = []

func _ready() -> void:
    ResourceLoader.load_threaded_request(MAIN_SCENE)
    set_process(true)

func _process(_delta: float) -> void:
    var status := ResourceLoader.load_threaded_get_status(MAIN_SCENE, _progress)
    match status:
        ResourceLoader.THREAD_LOAD_IN_PROGRESS:
            %ProgressBar.value = float(_progress[0]) * 100.0
        ResourceLoader.THREAD_LOAD_LOADED:
            set_process(false)
            var scene := ResourceLoader.load_threaded_get(MAIN_SCENE) as PackedScene
            get_tree().change_scene_to_packed(scene)
        ResourceLoader.THREAD_LOAD_FAILED, ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
            set_process(false)
            push_error("Failed to load main scene")
```

For a companion, the polished variant skips the progress bar: the *boot scene* is the minimal usable widget (clock, play button — interactive in well under a second), and the heavy ambient scene streams in behind it, fading in when ready. Startup then *feels* instant regardless of the true total.

> ⚠️ **Pitfall** — Polling `load_threaded_get_status` in `_process` is one of the few legitimate per-frame polls (it is temporary and drives visible progress), but remember to `set_process(false)` in **every** terminal branch — a forgotten failure branch leaves a per-frame poll running for the life of the app, quietly violating the idle budget you worked so hard for.

### 15.4 Autostart etiquette

Companions typically register themselves to start at login — which makes your startup cost part of the user's *login* experience, stacked on top of every other autostarting app. Etiquette rules:

- **Autostart must be opt-in** (a settings checkbox, default off) and reversible from the same place. Registration is platform-specific: on Windows, a `Run`-key registry entry or a Startup-folder shortcut created via `OS.execute()`/installer; on macOS, a Login Item; on Linux, a `.desktop` file in `~/.config/autostart`. Keep this logic in one platform-gated module and test *removal* as carefully as addition.
- **Start hidden when autostarted.** Pass a flag (`--autostart`) in the registered command line, read it with `OS.get_cmdline_args()` (or `get_cmdline_user_args()` for `--` separated args), and boot directly to the tray/HIDDEN state — nobody wants your window greeting them at login:

```gdscript
func _ready() -> void:
    var autostarted := "--autostart" in OS.get_cmdline_args()
    if autostarted:
        get_window().hide()          # straight to tray; Perf sees HIDDEN
    else:
        restore_geometry()           # normal launch: visible at last position
```

- **Be extra lazy at login.** During a login storm, disk and CPU are contended; the deferred-loading patterns of section 15.3 matter double here. An autostarted companion should reach its HIDDEN steady state in well under a second of CPU time and postpone *everything* nonessential (network refreshes, library scans) by a randomized 30–120 s so a dozen autostarting apps do not synchronize their thundering herds.
- **Respect the uninstall.** Autostart registration must be removed by your uninstaller/first-run-after-delete logic; orphaned autostart entries pointing at deleted executables are the kind of residue that earns bad reviews after the user has already left.

---

## 16. Measuring Like an Engineer

Everything so far gave you knobs; this section gives you the measurement practice that makes knob-turning honest. Three instruments: an in-app HUD (immediate feedback while developing), a CSV logger (trends over hours), and OS-level tools (ground truth).

### 16.1 The metrics HUD overlay

A debug-only `CanvasLayer` showing live vitals, toggled by a hotkey. It samples on a timer — a HUD that updates at 60 Hz measurably perturbs the thing it measures.

```gdscript
# debug/metrics_hud.gd — add to the main scene, or as an autoload in debug builds.
extends CanvasLayer

@onready var _label: Label = $Panel/Label
var _timer: Timer

func _ready() -> void:
    layer = 100
    visible = false
    _timer = Timer.new()
    _timer.wait_time = 0.5
    _timer.timeout.connect(_refresh)
    add_child(_timer)

func _input(event: InputEvent) -> void:
    if event.is_action_pressed(&"toggle_metrics_hud"):   # e.g. F3
        visible = not visible
        if visible:
            _timer.start()
            _refresh()
        else:
            _timer.stop()

func _refresh() -> void:
    var fps := Performance.get_monitor(Performance.TIME_FPS)
    var frame_ms := Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
    var mem_mb := Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0
    var vram_mb := Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0
    var nodes := int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
    var orphans := int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))
    # Draw calls from the rendering server (viewport-agnostic totals):
    var draws := RenderingServer.get_rendering_info(
        RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
    _label.text = "state: %s\nfps: %d  proc: %.2f ms\nmem: %.1f MB  vram: %.1f MB\nnodes: %d  orphans: %d\ndraws: %d" % [
        Perf.PowerState.keys()[Perf.state], int(fps), frame_ms,
        mem_mb, vram_mb, nodes, orphans, draws]
```

Notes: `RenderingServer.get_rendering_info()` also exposes `RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME`, `RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME`, `RENDERING_INFO_TEXTURE_MEM_USED`, `RENDERING_INFO_BUFFER_MEM_USED` and `RENDERING_INFO_VIDEO_MEM_USED`; be aware the counters can read 0 for the first frames after startup while the renderer warms up, so never assert on them at boot. `TIME_PROCESS` is the process-step time — pair it with `TIME_PHYSICS_PROCESS` if you keep physics enabled.

### 16.2 The CSV metrics logger

The soak test's data source: one row per sample interval, flushed periodically, written to `user://` (see [Database and Persistence](DATABASE_AND_PERSISTENCE.md) for path semantics).

```gdscript
# autoloads/metrics_logger.gd
extends Node
## Samples engine vitals to user://metrics/<session>.csv. Debug/soak builds only.

const SAMPLE_SEC: float = 60.0
const FLUSH_EVERY: int = 5

var _file: FileAccess
var _rows_since_flush: int = 0

func _ready() -> void:
    if not OS.is_debug_build() and not OS.has_environment("RELAX_SOAK"):
        queue_free()
        return
    DirAccess.make_dir_recursive_absolute("user://metrics")
    var session := Time.get_datetime_string_from_system().replace(":", "-")
    _file = FileAccess.open("user://metrics/%s.csv" % session, FileAccess.WRITE)
    _file.store_csv_line(PackedStringArray([
        "unix_time", "uptime_s", "power_state", "fps", "process_ms",
        "mem_static_b", "vram_b", "objects", "nodes", "orphans", "resources",
        "draw_calls"]))
    var t := Timer.new()
    t.wait_time = SAMPLE_SEC
    t.timeout.connect(_sample)
    add_child(t)
    t.start()
    _sample()  # first row immediately

func _sample() -> void:
    var row := PackedStringArray([
        str(Time.get_unix_time_from_system()),
        str(Time.get_ticks_msec() / 1000),
        str(Perf.state),
        str(int(Performance.get_monitor(Performance.TIME_FPS))),
        "%.3f" % (Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0),
        str(int(Performance.get_monitor(Performance.MEMORY_STATIC))),
        str(int(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED))),
        str(int(Performance.get_monitor(Performance.OBJECT_COUNT))),
        str(int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))),
        str(int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))),
        str(int(Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT))),
        str(RenderingServer.get_rendering_info(
            RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)),
    ])
    _file.store_csv_line(row)
    _rows_since_flush += 1
    if _rows_since_flush >= FLUSH_EVERY:
        _file.flush()   # survive crashes without per-row disk sync
        _rows_since_flush = 0
```

Analysis is any spreadsheet or a ten-line pandas script: plot `mem_static_b` and `objects` against `uptime_s`, color by `power_state`. The chart *is* the deliverable for the soak-test budget rows.

### 16.3 Before/after benchmark discipline

Optimization claims need a protocol, or they are anecdotes:

1. **Fix the scenario.** A written script ("launch → idle 5 min on desktop → interact 1 min → minimize 5 min") or, better, an automated driver scene that performs it.
2. **Fix the environment.** Same machine, power plan, plugged/unplugged state, closed background apps, release export. Note ambient temperature for thermal-sensitive laptops — seriously.
3. **Measure baseline ≥ 3 runs**, record medians of the metrics under test (CPU%, memory, frame intervals from the CSV).
4. **Apply exactly one change.**
5. **Re-run identically; compare medians; keep the raw CSVs.** Improvements under ~10% on noisy metrics (CPU%) need more runs before you believe them.
6. **Record the result** (commit message or perf log). Six months later, "why is this cache here?" has an answer with numbers.

### 16.4 OS-level verification: in-engine numbers lie

The engine reports what the engine knows. It does not see: driver threads, the compositor's cost of blending your transparent window, audio-stack overhead, OS timer pressure from your wakeups, or the GPU's power-state behavior. Final verdicts come from the OS:

**Windows** (primary desktop target for most companions):

- **Task Manager → Details**: add columns *CPU*, *Memory (active private working set)*, *Power usage*. Your idle companion should show 0.0–0.3% CPU and "Very low" power usage. Task Manager's CPU% is normalized to all cores — 1% here on an 8-core box is ~8% of one core, so the in-engine picture and this number differ by design.
- **`powercfg /energy /duration 60`** (admin shell): 60 s system energy trace with a report of top wakeup sources and timer-resolution offenders. If your app appears in the timer-resolution or wakeup sections while "idle", your caps/sleeps are not what you think.
- **Resource Monitor** (`resmon`): per-process disk activity — catches the config-file-write-per-frame class of bug instantly.

**macOS**: Activity Monitor's **Energy** tab (the "Energy Impact" column and the app-nap indicator) is brutally honest, and users look at it; `powermetrics` in a terminal for depth.

**Linux**: `htop` for CPU/RSS; `powertop` for wakeups-per-second attribution (your HIDDEN-state app should be far down the list); `intel_gpu_top`/`nvtop` for GPU residency.

The acceptance ritual for every release: run the shipped export through the section 2 budget sheet using *these* tools, on battery, and attach the numbers to the release notes. In-engine metrics guided the work; OS metrics sign it off.

> ⚠️ **Pitfall** — Measuring CPU% with the profiler open, the editor running, and the HUD at 60 Hz measures your instrumentation, not your app. Ground-truth runs are: release export, launched from the OS, all debug instrumentation off except the (timer-driven) CSV logger.

### 16.5 From CSV to verdict

The logger produces data; the budget needs verdicts. A 20-line Python script turns one into the other (any language works — the point is that analysis is *scripted*, so every soak is judged identically):

```python
# analyze_soak.py — usage: python analyze_soak.py metrics/2026-07-27.csv
import sys, csv

rows = list(csv.DictReader(open(sys.argv[1])))
hours = (int(rows[-1]["uptime_s"]) - int(rows[0]["uptime_s"])) / 3600.0
mem_mb = [int(r["mem_static_b"]) / 1048576.0 for r in rows]
warm = len(rows) // 10                      # skip warmup: first 10% of samples
drift = mem_mb[-1] - mem_mb[warm]
slope = drift / max(hours * 0.9, 0.01)      # MB per hour after warmup

orphan_max = max(int(r["orphans"]) for r in rows)
obj_first, obj_last = int(rows[warm]["objects"]), int(rows[-1]["objects"])

print(f"duration:      {hours:.1f} h  ({len(rows)} samples)")
print(f"mem after warm:{mem_mb[warm]:.1f} MB -> {mem_mb[-1]:.1f} MB "
      f"(drift {drift:+.1f} MB, {slope:+.2f} MB/h)")
print(f"objects:       {obj_first} -> {obj_last} ({obj_last - obj_first:+d})")
print(f"orphans max:   {orphan_max}")
print("VERDICT:", "PASS" if abs(drift) < 5 and orphan_max == 0 else "FAIL")
```

Wire the thresholds to your budget sheet, run it at the end of every soak, and paste its output into the release notes. For live OS-side collection on Windows during the same run, `typeperf` samples a process's counters to its own CSV, giving you the *working set* trend to place beside the engine's `MEMORY_STATIC` trend:

```powershell
# 60 s interval, 1440 samples = 24 h; run alongside the soak.
typeperf "\Process(RelaxRoom)\% Processor Time" `
         "\Process(RelaxRoom)\Working Set - Private" `
         -si 60 -sc 1440 -f CSV -o soak_os.csv
```

When the two trends disagree — engine flat, OS climbing — the growth is outside the engine's static allocator: driver/GPU memory (texture churn), audio buffers, or thread stacks. That diagnosis direction (which side of the boundary grows?) is exactly why you log both.

---

## 17. Case Study: Relax Room PerformanceManager

Everything in this module converges in Relax Room's `PerformanceManager` — the autoload (registered as `Perf`, first after `SingleInstance` in autoload order) that owns the app's entire power policy. This is the grown-up descendant of the 30-line `PerfManager` from this module's first edition, and its skeleton has appeared piecewise in sections 4, 6 and 11; here is the consolidated picture plus results.

### 17.1 Responsibilities and non-responsibilities

The manager **owns**: the power-state machine (ACTIVE/IDLE/HIDDEN), `Engine.max_fps`, `OS.low_processor_usage_mode(+_sleep_usec)`, the idle grace timer, the window-mode poll, custom monitors, and the `power_state_changed` signal. It deliberately does **not** own subsystem behavior: audio ducking, shader gating, particle pausing and network cadence live in their subsystems as subscribers (sections 4.1, 8.3, 13.3). This split keeps the manager ~150 lines forever and makes each subsystem's idle policy reviewable next to the subsystem.

```gdscript
# The consolidated _apply_state — the whole policy in one screen:
func _apply_state() -> void:
    match state:
        PowerState.ACTIVE:
            Engine.max_fps = FPS_ACTIVE                  # 60
            OS.low_processor_usage_mode = false
        PowerState.IDLE:
            Engine.max_fps = FPS_IDLE                    # 15
            OS.low_processor_usage_mode = false
        PowerState.HIDDEN:
            Engine.max_fps = FPS_HIDDEN                  # 5 (floor for timers/audio)
            OS.low_processor_usage_mode = true           # event-driven; window invisible
            OS.low_processor_usage_mode_sleep_usec = 66000
    print_verbose("[Perf] → %s" % PowerState.keys()[state])
```

Fixed complementary decisions made once at startup: `VSYNC_ENABLED` (section 5.1), `Engine.physics_ticks_per_second = 30` (hover Areas only — section 7.1), rendering method `gl_compatibility` (section 13.5), boot splash disabled with a minimal boot widget streaming the ambient scene (section 15.3).

### 17.2 Subscriber inventory

| Subsystem | ACTIVE | IDLE | HIDDEN |
|---|---|---|---|
| Ambient shader background | `animate = true` | `animate = false` (frozen) | frozen |
| Dust-mote GPUParticles2D | emitting | emitting, `speed_scale 0.5` | `emitting = false` |
| Mascot AnimationPlayer | full speed | `speed_scale 0.5` | paused |
| Soundscape audio | playing | playing | playing (it's the product!) |
| Tooltip system | live | `set_process(false)` | disabled |
| Weather accent (network) | poll 60 s | poll 300 s | poll 900 s |
| Autosave | 30 s debounced | on-transition + 10 min | on-transition + hourly |
| Metrics logger (soak builds) | 60 s samples | 60 s | 60 s (`PROCESS_MODE_ALWAYS` not needed — tree never pauses) |

Note the audio row: it is the reason Relax Room uses custom throttle, not `get_tree().paused` (section 8.2), and the reason HIDDEN keeps a 5 FPS floor rather than pausing outright — the audio-driving logic (crossfades, scheduled chimes) still needs occasional process time.

### 17.3 Measured results

Budget-sheet excerpt from the reference laptop (release export, battery, balanced plan; medians of 3 runs):

| Metric | Before module techniques | After | Budget | Status |
|---|---|---|---|---|
| CPU, ACTIVE (Task Manager) | 6–9% | 3–4% | — | informative |
| CPU, IDLE visible | 6–8% (uncapped 60) | 0.8–1.2% | ≤ 1% | pass (borderline, tracked) |
| CPU, HIDDEN (tray) | 5–7% | 0.0–0.1% | ≤ 0.3% | pass |
| RAM after 24 h soak | +210 MB (tween+orphan leaks) | +2 MB | < 5 MB | pass |
| VRAM | 190 MB (uncompressed bg) | 96 MB | ≤ 150 MB | pass |
| Startup to interactive | 3.9 s | 1.6 s | ≤ 2.5 s | pass |
| powercfg wakeup listing | present | absent | absent | pass |

The two biggest single wins, for the record: capping IDLE to 15 FPS (CPU ÷ ~6 while visible-idle) and enabling low-processor mode in HIDDEN (CPU → measurement noise). The 24 h RAM delta was three distinct bugs found by the soak chart: an unkilled looping tween on the play button, settings-panel orphans (removed, never freed), and an unbounded "recently played" array. Every one of them is an instance of a pattern named in section 14.3 — they always are.

> ✅ **Best practice** — Steal this structure wholesale for your own companion: a single `Perf` autoload with a state enum and a signal, subsystems subscribing locally, budgets in a sheet, a CSV logger for soaks, OS tools for sign-off. The specific numbers (60/15/5, 12 s grace, 30 Hz physics) are Relax Room's; the *architecture* is the takeaway.

### 17.4 The complete listing

The full autoload as shipped (minus logging noise), consolidating sections 4.1, 6.3, 8.1 and 11.4 into one reviewable file:

```gdscript
# autoloads/performance_manager.gd — registered as "Perf".
extends Node
## Owns the app's power policy: state machine, frame caps, low-processor
## mode, custom monitors. Subsystems subscribe to power_state_changed.

enum PowerState { ACTIVE, IDLE, HIDDEN }

signal power_state_changed(new_state: PowerState)

const FPS_ACTIVE: int = 60
const FPS_IDLE: int = 15
const FPS_HIDDEN: int = 5
const IDLE_GRACE_SEC: float = 12.0
const MODE_POLL_SEC: float = 1.0
const HIDDEN_SLEEP_USEC: int = 66000

var state: PowerState = PowerState.ACTIVE:
    set(value):
        if state == value:
            return
        state = value
        _apply_state()
        power_state_changed.emit(state)

var _idle_timer: Timer
var _mode_poll_timer: Timer

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS

    # Fixed, once-per-launch decisions (sections 5.1, 7.1):
    DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED)
    Engine.physics_ticks_per_second = 30

    var window: Window = get_window()
    window.focus_entered.connect(_on_focus_entered)
    window.focus_exited.connect(_on_focus_exited)

    _idle_timer = Timer.new()
    _idle_timer.one_shot = true
    _idle_timer.wait_time = IDLE_GRACE_SEC
    _idle_timer.timeout.connect(_on_idle_grace_elapsed)
    add_child(_idle_timer)

    _mode_poll_timer = Timer.new()
    _mode_poll_timer.wait_time = MODE_POLL_SEC
    _mode_poll_timer.timeout.connect(_poll_window_mode)
    add_child(_mode_poll_timer)
    _mode_poll_timer.start()

    if OS.is_debug_build():
        _register_custom_monitors()

    _apply_state()
    _idle_timer.start()

func _input(event: InputEvent) -> void:
    if event is InputEventMouseMotion \
            or event is InputEventMouseButton \
            or event is InputEventKey:
        _register_activity()

func _notification(what: int) -> void:
    match what:
        NOTIFICATION_APPLICATION_FOCUS_OUT:
            if state == PowerState.ACTIVE:
                state = PowerState.IDLE
        NOTIFICATION_APPLICATION_FOCUS_IN:
            _register_activity()

func _register_activity() -> void:
    if state != PowerState.HIDDEN:
        state = PowerState.ACTIVE
        _idle_timer.start()

func _on_focus_entered() -> void:
    state = PowerState.ACTIVE
    _idle_timer.start()

func _on_focus_exited() -> void:
    if state != PowerState.HIDDEN:
        state = PowerState.IDLE
        _idle_timer.stop()

func _on_idle_grace_elapsed() -> void:
    if state == PowerState.ACTIVE:
        state = PowerState.IDLE

func _poll_window_mode() -> void:
    var w: Window = get_window()
    var hidden: bool = w.mode == Window.MODE_MINIMIZED or not w.visible
    if hidden and state != PowerState.HIDDEN:
        state = PowerState.HIDDEN
    elif not hidden and state == PowerState.HIDDEN:
        state = PowerState.IDLE   # restored unfocused; focus signal upgrades

func _apply_state() -> void:
    match state:
        PowerState.ACTIVE:
            Engine.max_fps = FPS_ACTIVE
            OS.low_processor_usage_mode = false
        PowerState.IDLE:
            Engine.max_fps = FPS_IDLE
            OS.low_processor_usage_mode = false
        PowerState.HIDDEN:
            Engine.max_fps = FPS_HIDDEN
            OS.low_processor_usage_mode = true
            OS.low_processor_usage_mode_sleep_usec = HIDDEN_SLEEP_USEC
    print_verbose("[Perf] -> %s" % PowerState.keys()[state])

func _register_custom_monitors() -> void:
    Performance.add_custom_monitor("relax_room/power_state",
        func() -> int: return state)
    Performance.add_custom_monitor("relax_room/tween_count",
        func() -> int: return get_tree().get_processed_tweens().size())
```

Review checklist applied to this file in Relax Room's repo (and worth copying into yours): no `_process` method at all (everything is signals and slow timers); every constant surfaced at the top; the setter is the *only* writer of engine properties; debug-only instrumentation is fenced; and the file compiles standalone — no dependencies on other autoloads, so autoload ordering cannot break it ([Autoload Safety](AUTOLOAD_SAFETY.md)).

### 17.5 Knob quick-reference card

Every throttling API this module touched, in one table — the revision aid for the exercises and for real projects:

| Knob | Where | Effect | Companion default |
|---|---|---|---|
| `Engine.max_fps` | runtime | Caps rendered FPS (0 = uncapped) | 60 / 15 / 5 per state |
| `application/run/max_fps` | project setting | Startup value of the above | 60 |
| `DisplayServer.window_set_vsync_mode()` | runtime | Presentation sync: DISABLED / ENABLED / ADAPTIVE / MAILBOX | ENABLED, set once |
| `OS.low_processor_usage_mode` | runtime / `application/run/low_processor_mode` | Redraw only on change + sleep between iterations | on when HIDDEN (or always for static UIs) |
| `OS.low_processor_usage_mode_sleep_usec` | runtime / project setting | Sleep per iteration (default 6900 µs) | 66000 when HIDDEN |
| `Engine.physics_ticks_per_second` | runtime / `physics/common/...` | Fixed physics/`_physics_process` rate | 30 (or lower) |
| `Engine.max_physics_steps_per_frame` | runtime | Physics catch-up cap per rendered frame | default 8 |
| `Engine.time_scale` | runtime | Game-clock speed; **no CPU effect** | 1.0 — not a power tool |
| `set_process(false)` and siblings | per node | Disables per-frame callbacks | off unless justified |
| `Node.process_mode = PROCESS_MODE_DISABLED` | per subtree | Silences a whole subtree | dormant features/tabs |
| `get_tree().paused` | global | Freezes pausable nodes (audio/timers too!) | avoid; custom throttle |
| `GPUParticles2D.emitting` / `speed_scale` | per node | Particle gating | off when not ACTIVE |
| shader `animate` uniform (pattern) | per material | Freezes TIME-driven effects | false unless ACTIVE |
| `Window.mode` / `visible` | runtime | Minimize / hide-to-tray detection & control | poll at 1 Hz |
| `get_tree().set_auto_accept_quit(false)` | startup | You own the close button | set, with explicit Quit path |
| `rendering/renderer/rendering_method` | project setting (restart) | Forward+ / Mobile / Compatibility pipeline | `gl_compatibility` |
| `display/window/per_pixel_transparency/allowed` | project setting | Enables transparent windows (costly) | off unless the design demands it |
| `ResourceLoader.load_threaded_request()` | runtime | Background resource loading | heavy scenes at boot |
| `WorkerThreadPool.add_task()` | runtime | Offload finite CPU jobs | scans/parses > few ms |

---

## Best practices

**Budgets and process**

- Write numeric budgets per power state (CPU %, FPS, RAM slope, VRAM, startup) against a named reference machine, with a measurement method per row; re-measure every release.
- Profile before optimizing, change one thing per measurement, and keep raw before/after data next to the code.
- Treat the RAM *slope* as the budget, not the RAM value — companions are judged over days, not sessions.
- Sign off with OS tools (Task Manager, powercfg, Activity Monitor, htop/powertop) on a release export; in-engine numbers are for steering, not for verdicts.

**Frame pacing**

- Centralize all power policy in one autoload state machine with a `power_state_changed` signal; subsystems subscribe and own their local idle behavior.
- `Engine.max_fps` per state (e.g. 60/15/5) is the highest-leverage optimization in the entire module; implement it first.
- VSync stays static (`VSYNC_ENABLED`); the FPS cap is the dynamic knob. Avoid `VSYNC_MAILBOX` in companions; never allow `max_fps = 0` + `VSYNC_DISABLED`.
- Enable `OS.low_processor_usage_mode` whenever the window is hidden — and permanently if your visible UI is static between interactions; tune `low_processor_usage_mode_sleep_usec` per state.
- Lower `Engine.physics_ticks_per_second` (30 or less) when physics is decorative; remember the render cap does not slow physics.

**Code discipline**

- `set_process(false)` is the default state of mind: every `_process` implementation must justify its existence per power state; the profiler's Script Functions view during idle should be nearly empty.
- Timers and signals over polling, always; batch slow ticks through one Heartbeat autoload instead of many private timers.
- Type all GDScript, allocate nothing per frame, cache node lookups with `@onready`, gate string building behind change checks.
- Offload finite heavy jobs (scans, parses) to `WorkerThreadPool`; marshal results back with `call_deferred()`; never touch the tree from workers ([Autoload Safety](AUTOLOAD_SAFETY.md)).

**Rendering and memory**

- Gate every TIME-driven shader, particle system and looping animation behind the power state — anything that animates unconditionally keeps the GPU awake forever.
- Atlas textures, minimize CanvasItems, pre-composite static layers; watch `RENDER_TOTAL_DRAW_CALLS_IN_FRAME` while building scenes.
- Prefer the `gl_compatibility` renderer for 2D companions; decide in week one.
- Enforce node ownership (`queue_free()` responsibility), kill predecessor tweens, bound every long-lived collection, guard re-connections — and soak-test 24 h with the CSV logger before each release, checking `OBJECT_ORPHAN_NODE_COUNT` stays 0.
- Keep startup ≤ budget by deferring heavy loads (`call_deferred`, `ResourceLoader.load_threaded_request`) behind a minimal instantly-interactive boot widget.

**OS citizenship**

- Ship minimize-to-tray via `StatusIndicator` (4.3+) with `set_auto_accept_quit(false)` and an explicit Quit path; treat tray support as an enhancement (Linux DEs vary).
- Persist and validate window geometry against `screen_get_usable_rect()`; respect DPI via content scaling; make always-on-top a user choice.
- Guard against multiple instances with a localhost socket that focuses the primary instance.
- Per-pixel transparency is the most expensive checkbox in the module: small windows only, budgets re-verified with it enabled.

## Common errors & troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Laptop fans spin up while the app sits idle on the desktop | No idle FPS cap (running 60+ FPS forever), or `max_fps = 0` with `VSYNC_DISABLED` spinning the loop | Implement the power-state manager; cap IDLE to 15; verify with Task Manager, not the in-app FPS counter |
| App is "idle" but `powercfg /energy` lists it as a wakeup source | High-frequency timers, per-frame polling in `_process`, or a worker thread loop-polling | Audit Script Functions view during idle; convert polls to timers/signals; batch through a heartbeat; kill polling threads |
| Stutter or sluggishness after hours of uptime | Accumulating processed objects: leaked looping tweens, stacked signal connections running handlers N times, growing arrays scanned per tick | Watch the tween-count custom monitor and `OBJECT_COUNT` over time; kill predecessor tweens; guard `connect()` with `is_connected()`; bound collections |
| Memory climbs slowly forever (soak chart ramps) | Orphan nodes (`remove_child` without `free`), unbounded caches, resources held by forgotten references | `OBJECT_ORPHAN_NODE_COUNT` + `Node.print_orphan_nodes()`; ownership rule for dynamic nodes; WeakRef caches; run `--verbose` and read the exit leak report |
| Noticeable battery drain reported by users ("your app ate 15%") | Transparent window compositor cost, TIME-driven shaders never gated, VSYNC_MAILBOX rendering discarded frames, HIDDEN state never entered because tray/minimize detection failed | Re-verify each state's CPU/GPU on battery; gate shaders; use `VSYNC_ENABLED`; log state transitions and confirm HIDDEN is actually reached when minimized/hidden |
| App feels laggy though the profiler shows every function is fast | Over-aggressive `low_processor_usage_mode_sleep_usec`, or IDLE→ACTIVE promotion missing so interaction runs at 15 FPS | Lower sleep usec when visible; promote to ACTIVE synchronously in `_input()`; check the state-transition log while reproducing |
| Cap set to 15 but CPU still high while idle | Frame *cost* problem, not frame *rate*: heavy `_process` work each frame, physics still at 60 Hz, or audio/network churn | Profile busy time per frame; apply `set_process(false)` discipline; lower `physics_ticks_per_second`; check per-frame allocations |
| Closing the window quits the app instead of hiding to tray | `set_auto_accept_quit(false)` missing, so the engine auto-quits before `close_requested` logic matters | Call `get_tree().set_auto_accept_quit(false)` at startup; handle `close_requested` → hide; provide explicit Quit in the tray menu |
| App cannot be closed at all ("unkillable") | Auto-quit disabled but no code path calls `get_tree().quit()` | Every tray/menu Quit action must reach `get_tree().quit()`; test the full quit path in every release checklist |
| Tray icon missing on Linux | `StatusIndicator` implemented on Windows/macOS; Linux DE tray support varies | Feature-detect and fall back to normal window/taskbar behavior; never make tray the only route to a feature |
| App frozen after minimize, never recovers | `get_tree().paused = true` on minimize, with the unpause logic on a `PAUSABLE` node or a non-`process_always` timer | Custom throttle instead of pause; if pausing, keep the wake path on `PROCESS_MODE_ALWAYS` and timers with `process_always = true` |
| Draw-call/VRAM HUD reads 0 at startup | `RenderingServer.get_rendering_info()` counters need a few frames before reporting | Sample after the first frames; never assert on render info at boot |
| Metrics printer only ever logs one line | `get_tree().create_timer()` is one-shot; it does not repeat | Use a `Timer` node (default repeating) or re-arm in the callback |
| Restored window appears off-screen after undocking a laptop | Geometry restored onto a monitor that no longer exists | Validate saved screen index against `get_screen_count()`; clamp position into `screen_get_usable_rect()` |
| Second launch opens a second mascot and doubled audio | No single-instance guard | Localhost socket guard: second instance messages the first to focus, then quits |
| Transparent-window companion melts the GPU budget | Per-pixel transparency forces compositor blending every desktop repaint | Shrink the window, cap FPS harder, pre-composite layers — and re-measure with OS tools since the cost lands in the compositor process |

## Exercises

Lab 1–3 are preserved from this module's first edition, upgraded with acceptance criteria; 4–10 are new. Do them in order — later labs consume earlier labs' artifacts.

1. **Lab — Adaptive FPS manager.** Implement the three-state `PerformanceManager` (section 4.1) in your project: focus signals, input promotion, idle grace timer, minimize poll, `power_state_changed` signal.
   *Acceptance:* state transitions logged correctly through the sequence focus → 15 s untouched → mouse move → minimize → restore; `Engine.max_fps` verified 60/15/5 via the Monitors tab in each state; promotion to ACTIVE occurs on the first input event (no perceptible ramp-up).
   *Stretch:* add `NOTIFICATION_APPLICATION_FOCUS_OUT` handling and derive the ACTIVE cap from `DisplayServer.screen_get_refresh_rate()` with a 60 fallback.

2. **Lab — Profile a scene.** Profile your app's *idle* minute and one heavy interaction with the Profiler; sort by self time; optimize the top hotspot; re-measure.
   *Acceptance:* before/after profiler screenshots; the hotspot's self time reduced ≥ 30%; a one-paragraph writeup naming the cause (allocation, polling, lookup, shader…).
   *Stretch:* repeat with the Visual Profiler and classify your idle frame as CPU- or GPU-bound, with evidence.

3. **Lab — Frame-time histogram.** Record per-frame intervals for 60 s in each power state (accumulate `delta` samples into buckets); render a histogram (in-app with `draw_rect`, or export CSV and plot).
   *Acceptance:* three histograms; IDLE clusters tightly at ~66 ms; outliers beyond 2× the expected interval are identified and explained.
   *Stretch:* automate outlier attribution by logging the Script Functions active during any frame > 2× budget.

4. **Lab — Low-processor A/B power test.** Build a static-UI test scene. Run 10 minutes idle under (a) uncapped, (b) `max_fps = 15`, (c) `low_processor_usage_mode` with default sleep, (d) mode with 33000 µs sleep, measuring CPU% via Task Manager/htop for each.
   *Acceptance:* a four-row results table from a release export; (c)/(d) reach ~0% CPU; a paragraph explaining when (b) beats (c) for your real app.
   *Stretch:* add a TIME-driven shader to the scene and document how it changes the results; then gate it and re-measure.

5. **Lab — Tray companion.** Implement the full minimize-to-tray recipe (section 10.2): `StatusIndicator`, native menu, close-to-tray, left-click toggle, explicit Quit.
   *Acceptance:* closing hides to tray with the HIDDEN power state entered (verify ≤ 0.3% CPU in Task Manager); left-click restores focused at the saved geometry; Quit actually quits and flushes settings.
   *Stretch:* add the single-instance guard so a second launch focuses the tray-hidden primary instance.

6. **Lab — Leak hunt.** Deliberately introduce three leaks in a test scene (an unkilled `set_loops()` tween per button press, a panel removed but never freed, an unbounded event array). Find all three using only the Monitors tab, custom monitors and `print_orphan_nodes()`.
   *Acceptance:* a written hunt log: which monitor exposed each leak, how you localized it, the fix; `OBJECT_ORPHAN_NODE_COUNT` returns to 0 and tween count returns to baseline after fixes.
   *Stretch:* have a colleague (or your future self) plant an unknown leak and find it blind within 30 minutes.

7. **Lab — Overnight soak.** Wire the CSV metrics logger (section 16.2) plus a life-simulator timer performing random UI actions; run ≥ 12 h as a release export; chart memory, objects and orphans versus time.
   *Acceptance:* the chart, an interpretation (flat/staircase/ramp per section 14.5), and either "no leaks" with evidence or fixed leaks with before/after charts; RAM drift within your budget.
   *Stretch:* extend to a full 24 h including at least 8 h in HIDDEN, and verify state distribution from the CSV's `power_state` column.

8. **Lab — Startup budget.** Instrument startup checkpoints (section 15.1); then cut startup-to-interactive by ≥ 30% using boot-splash minimization, deferred init and `load_threaded_request` behind a minimal boot widget.
   *Acceptance:* checkpoint table before/after; the window accepts input within your budget; loading of the heavy scene visibly does not block the boot widget (spinner animates smoothly).
   *Stretch:* handle the `THREAD_LOAD_FAILED` path gracefully with a retry UI, and prove `set_process(false)` is reached in every terminal branch.

9. **Lab — Release sign-off.** Compose the full budget sheet for your app (section 2.5) and execute a complete OS-level verification pass (section 16.4) on a release export: Task Manager/htop CPU per state, powercfg energy report (or platform equivalent), memory after the soak, startup stopwatch.
   *Acceptance:* the filled-in sheet with pass/fail per row and tool screenshots; every fail has a filed issue with a hypothesis.
   *Stretch:* script the interactive scenario so the sign-off run is reproducible by someone who is not you.

10. **Lab — Policy under test.** Extract your manager's transition logic into a pure `PowerPolicy` class (section 4.3) and table-test it: every state × every combination of focused/minimized/visible/input-recent.
    *Acceptance:* the test script enumerates all reachable combinations, passes, and catches a deliberately introduced bug (swap two branch conditions and show the failing case); the autoload contains no transition logic outside the policy call.
    *Stretch:* add a property-style fuzz loop (random fact sequences) asserting two invariants: HIDDEN whenever `minimized or not visible`, and never ACTIVE without recent input or fresh focus.

**Self-check questions** (from the first edition, expanded — answer without looking):
1. What FPS does a desktop companion target when idle, and why that number rather than 30 or 1?
2. Name three `Performance.get_monitor()` monitors you would watch during a soak test and what each reveals.
3. Why does capping `Engine.max_fps` to 15 not reduce physics cost, and what does?
4. What exactly does `low_processor_usage_mode` skip, and which scene content silently defeats it?
5. When is `set_process(false)` preferable to deleting the `_process` method, and what tool proves nobody forgot one?
6. Why is `get_tree().paused` usually wrong for a companion's HIDDEN state? Name the two things it breaks for Relax Room.
7. What does `Engine.time_scale = 0.1` do to CPU usage, and why?

## Further reading

Official documentation first — these are the sources this module's API claims were verified against (Godot 4.5 era, July 2026):

- **Godot Docs — Performance section** (https://docs.godotengine.org/en/stable/tutorials/performance/index.html) — the umbrella for all optimization tutorials; skim everything once so you know what exists.
- **General optimization tips** (https://docs.godotengine.org/en/stable/tutorials/performance/general_optimization.html) — the measure-first philosophy, bottleneck thinking; this module's section 11 methodology in engine-official form.
- **CPU optimization** (https://docs.godotengine.org/en/stable/tutorials/performance/cpu_optimization.html) — profilers, servers, threads, GDScript costs; complements sections 11–12.
- **GPU optimization** (https://docs.godotengine.org/en/stable/tutorials/performance/gpu_optimization.html) — draw calls, fill rate, transparency; the 3D-leaning companion to section 13.
- **The Profiler** (https://docs.godotengine.org/en/stable/tutorials/scripting/debug/the_profiler.html) — official walkthrough of the tab this module's workflow lives in, including self-vs-total time semantics.
- **Custom performance monitors** (https://docs.godotengine.org/en/stable/tutorials/scripting/debug/custom_performance_monitors.html) — the tutorial behind section 11.4.
- **Performance class reference** (https://docs.godotengine.org/en/stable/classes/class_performance.html) — every monitor enum used in this module, plus `add_custom_monitor` signatures.
- **Engine class reference** (https://docs.godotengine.org/en/stable/classes/class_engine.html) — `max_fps`, `time_scale`, `physics_ticks_per_second`, `max_physics_steps_per_frame` authoritative semantics.
- **OS class reference** (https://docs.godotengine.org/en/stable/classes/class_os.html) — `low_processor_usage_mode`, `low_processor_usage_mode_sleep_usec` (default 6900 µs), memory queries.
- **DisplayServer class reference** (https://docs.godotengine.org/en/stable/classes/class_displayserver.html) — VSync modes, window flags/modes, screen queries; the OS-integration API surface of sections 5 and 9.
- **StatusIndicator class reference** (https://docs.godotengine.org/en/stable/classes/class_statusindicator.html) — tray icon node (4.3+), platform support statement, `pressed` signal.
- **Background loading** (https://docs.godotengine.org/en/stable/tutorials/io/background_loading.html) — `ResourceLoader.load_threaded_*` patterns behind section 15.3.
- **Using multiple threads** (https://docs.godotengine.org/en/stable/tutorials/performance/using_multiple_threads.html) — thread-safety rules that make section 12.7's iron laws official.
- **Sibling modules:** [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) (draw-call fundamentals), [Shaders](SHADERS_GDSHADER.md) (shader cost model), [Autoload Safety](AUTOLOAD_SAFETY.md) (autoload ordering, thread rules), [Sprites and Textures](SPRITES_AND_TEXTURES.md) (atlases, import settings), [Database and Persistence](DATABASE_AND_PERSISTENCE.md) (user:// paths, save cadence), [Build and Export](BUILD_AND_EXPORT.md) (release exports you must measure on).

## Glossary

| Term | Definition |
|---|---|
| **FPS budget** | Target frame rate per power state (e.g. 60 ACTIVE / 15 IDLE / 5 HIDDEN); a number, not a wish. |
| **Frame time** | Milliseconds per frame; 16.6 ms at 60 FPS, 66.6 ms at 15 FPS. Distinct from *busy time*, the fraction actually spent working. |
| **Frame pacing** | Controlling when frames happen (caps, VSync, sleeps) rather than how fast they compute. |
| **Power state** | App-level mode (ACTIVE/IDLE/HIDDEN) driving all throttling decisions through one state machine. |
| **Duty cycle** | Fraction of wall-clock time the CPU/GPU is busy on your behalf; the real target of idle optimization. |
| **Wakeup** | Any transition of the process from sleeping to running; each costs energy; counted by tools like powertop/powercfg. |
| **`Engine.max_fps`** | Runtime frame-rate cap; `0` means *uncapped* (never "paused"). |
| **VSync** | Synchronizing frame presentation to the display's vertical blank; modes: disabled, enabled, adaptive, mailbox (`DisplayServer.window_set_vsync_mode`) — mailbox keeps rendering discarded frames and is energy-hostile in companions. |
| **Low processor usage mode** | `OS.low_processor_usage_mode`: engine redraws only when something changed and sleeps between iterations (`low_processor_usage_mode_sleep_usec`, default 6900 µs); the editor's own idle strategy. |
| **Physics tick** | Fixed-rate simulation step (`Engine.physics_ticks_per_second`, default 60), independent of the render cap. |
| **`set_process(false)`** | Disables a node's `_process` callback; the per-node throttle underpinning process discipline. |
| **Polling** | Checking state on a schedule (worst: per frame) instead of reacting to events; the cardinal companion sin. |
| **Heartbeat** | A shared slow-tick autoload emitting `tick_1s`/`tick_10s` so features share one wakeup instead of owning private timers. |
| **`Performance.get_monitor()`** | Runtime metrics API (FPS, memory, objects, draw calls…); `add_custom_monitor()` adds app-specific gauges. |
| **Draw call** | One submission of geometry to the GPU; batches break on texture/material changes; monitor `RENDER_TOTAL_DRAW_CALLS_IN_FRAME`. |
| **Overdraw** | Shading the same pixel multiple times per frame; transparency forces it; layered fullscreen effects multiply it. |
| **Atlas** | Multiple images packed into one texture so consecutive sprites batch into one draw call. |
| **GPUParticles2D / CPUParticles2D** | GPU-simulated vs CPU-simulated particles; GPU scales better for many particles; both must be gated when idle. |
| **TIME-driven shader** | Shader animating via the `TIME` built-in; produces a new image every frame, defeating redraw-on-demand — gate behind a uniform. |
| **Orphan node** | A node alive but not in the scene tree (removed, never freed); the classic Godot leak; count via `OBJECT_ORPHAN_NODE_COUNT`, identify via `Node.print_orphan_nodes()`. |
| **Soak test** | Long-duration (12–24 h) run with logged metrics verifying flat memory and stable behavior over time; caches bounded via `weakref()` survive it (section 14.3). |
| **`WorkerThreadPool`** | Engine-managed thread pool for finite background jobs; results return to the main thread via `call_deferred()`. |
| **`StatusIndicator`** | Node (Godot 4.3+) creating a system-tray icon with tooltip, native menu and `pressed(mouse_button, mouse_position)` signal; implemented on Windows and macOS. |
| **Single-instance guard** | Startup mechanism (localhost socket or lock file) ensuring a second launch focuses the running instance instead of duplicating it. |
| **Working set** | OS-visible process memory; larger than the engine's `MEMORY_STATIC`; what users see in Task Manager. |

---

*Module 14 of "Godot 4 in Production" · Previous: [Autoload Safety](AUTOLOAD_SAFETY.md) · Course index: [00-INDEX](00-INDEX.md)*

