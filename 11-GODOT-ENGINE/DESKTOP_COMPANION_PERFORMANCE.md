# Desktop Companion Performance — 15/60 FPS Budgets and Profiler Workflow

> **Course module:** Godot 4 in Production
> **Position:** Phase 5 — New modules · Module 14 (NEW)
> **Prerequisites:** Modules 01, 04; concept of frame time, draw call.
> **Learning objectives:** define FPS budgets for desktop companion (idle 15 FPS, active 60 FPS); use profiler effectively; identify draw-call hotspots; reduce CPU/GPU load when idle.
> **Estimated time:** 60 min reading · 240 min hands-on
> **Level:** proficient (Dreyfus 4)
> **Last updated:** 2026-04-27

## Guiding ideas

1. **Desktop companion ≠ AAA game.** Different priorities: small footprint, long-run battery friendly, clear when active vs idle.
2. **15 FPS budget when idle (window minimized, alt-tabbed).** Set `Engine.max_fps = 15` via low-power signal.
3. **60 FPS budget when interactive (focus, hovering, clicking).** Set `Engine.max_fps = 60` on focus.
4. **Profile before optimizing.** "I think it's slow" = no data. Profiler shows truth.
5. **Common hotspots in companion apps: tooltip update on hover, particle systems, unnecessary `_process`.**

## FPS adaptive code

```gdscript
# autoloads/PerfManager.gd
extends Node

const FPS_ACTIVE := 60
const FPS_IDLE := 15

func _ready() -> void:
    get_tree().get_root().window.focus_entered.connect(_on_focus)
    get_tree().get_root().window.focus_exited.connect(_on_unfocus)
    Engine.max_fps = FPS_ACTIVE

func _on_focus() -> void:
    Engine.max_fps = FPS_ACTIVE

func _on_unfocus() -> void:
    Engine.max_fps = FPS_IDLE
```

## Profiler workflow

1. Run game in editor.
2. Open `Debugger` panel → `Profiler` tab.
3. Start profile.
4. Reproduce slow scenario (e.g., scene transition).
5. Stop profile; sort by `self time` (excluding children).
6. Identify top 3 functions; optimize.

## Common optimizations

- **Replace `_process` with `_physics_process` if rate-tolerant.** Fixed 60 Hz vs variable.
- **Reduce particle count.** GPUParticles2D > CPUParticles2D for many particles.
- **Atlas textures.** Reduces draw calls.
- **Disable processing on hidden nodes.** `set_process(false)` when offscreen.
- **Avoid string formatting in hot loops.** "Score: " + str(score) every frame is wasteful; use `_to_string` lazily.

## Performance monitor

```gdscript
# Print metrics every second
func _ready() -> void:
    var timer := get_tree().create_timer(1.0)
    timer.timeout.connect(_print_perf)

func _print_perf() -> void:
    print("FPS: ", Engine.get_frames_per_second())
    print("Draw calls: ", Performance.get_monitor(Performance.RENDER_2D_DRAW_CALLS_IN_FRAME))
    print("Mem static: ", Performance.get_monitor(Performance.MEMORY_STATIC) / 1e6, " MB")
```

## Exercises

1. **Lab — FPS adaptive.** Implement focus-aware FPS switching in your project.
2. **Lab — profile a scene.** Profile a specific scene; identify top hotspot; optimize; remeasure.
3. **Stretch — frame time histogram.** Record frame times for 60s; plot histogram; identify outliers.

## Self-assessment

1. Desktop companion idle FPS target?
2. `Performance.get_monitor`: 3 useful monitors.
3. `_process` vs `_physics_process`: when each.
4. Atlas texture: performance benefit.
5. `set_process(false)`: when use it.

## Primary reading

- Godot — Performance optimization. https://docs.godotengine.org/en/stable/tutorials/performance/
- Godot — Frame profiler. https://docs.godotengine.org/en/stable/tutorials/scripting/debug/the_profiler.html

## Cross-links

- Module 01 — `GODOT_ENGINE_STUDY.md`.
- Module 04 — `RENDERING_AND_VISUAL_LOGIC.md`: draw calls.

## Local glossary

| Term | Definition |
|---|---|
| **FPS budget** | Target frame rate per scenario. |
| **Frame time** | ms per frame; 16.6ms @ 60 FPS. |
| **Draw call** | One submission to GPU. |
| **`Engine.max_fps`** | Cap frame rate. |
| **`Performance.get_monitor`** | API for runtime metrics. |
| **GPUParticles2D** | GPU-accelerated particles. |
| **CPUParticles2D** | CPU-driven particles. |
| **`set_process(false)`** | Disable `_process` on a node. |
