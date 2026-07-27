---
course: "Godot 4 in Production"
file-role: "Exercise catalogue — per-module drills, integration labs, and debugging scenarios"
version: "Godot 4.5 / GDScript 2.0"
updated: 2026-07-27
tags: [godot, exercises, labs, practice, debugging-scenarios, ci-cd]
---

# 99-EXERCISES — Exercise Catalogue

> **Updated:** 2026-07-27

Practice material for the whole course: short per-module drills, three cross-module **integration labs** (the original Labs 01-03, expanded), and **scenario debugging** exercises where you diagnose a broken project from symptoms (the original Scenarios 01-04, expanded). Complete the drills for a module right after studying it; do the labs before starting the [capstone](../00-CAPSTONE.md).

## Contents

- [How to work these exercises](#how-to-work-these-exercises)
- [Difficulty legend](#difficulty-legend)
- [Per-module exercises (01-14)](#per-module-exercises)
- [Integration labs (01-03)](#integration-labs)
- [Scenario debugging (01-04)](#scenario-debugging)

## How to work these exercises

1. **One project per module, one Git repo overall.** Create `exercises/<module>/` folders inside a single Godot project; commit after every exercise with a message naming it (`ex03.2: atlas without bleeding`). Your history becomes your progress log.
2. **Read the acceptance criteria first.** They tell you what "done" means; work backwards from them.
3. **Try 20-30 minutes before opening a hint.** Hints are collapsed on purpose. Struggling first is the mechanism by which this sticks.
4. **Verify against docs, not memory.** Every API you use should be checked once against the [class reference](https://docs.godotengine.org/en/stable/classes/index.html) — building the docs habit is a hidden goal of every exercise.
5. **Timebox.** Estimated times assume the module was studied. If you exceed 2× the estimate, stop, read the hint, finish, and note in the commit what blocked you.
6. **No copy-paste from module examples.** Retype. Muscle memory for GDScript syntax is cheap to build now and expensive to lack later.

## Difficulty legend

| Mark | Meaning | Typical time |
|---|---|---|
| ● | Warm-up — direct application of one concept | 15-30 min |
| ●● | Core — combines 2-3 concepts, some design freedom | 30-75 min |
| ●●● | Challenge — open-ended, multiple valid solutions, production constraints | 1-3 h |

## Progress tracker

Copy into your exercises repo README and tick as you commit. Minimum bar before starting the capstone: **all ● and ●● drills, at least one ●●● drill, Labs 01-03, and two scenarios.**

| Module | Drills | Done | Module | Drills | Done |
|---|---|---|---|---|---|
| 01 Engine core | 01.1 · 01.2 · 01.3 | ☐ ☐ ☐ | 08 Persistence | 08.1 · 08.2 · 08.3 | ☐ ☐ ☐ |
| 02 Scenes & nodes | 02.1 · 02.2 · 02.3 | ☐ ☐ ☐ | 09 Project deep dive | 09.1 · 09.2 | ☐ ☐ |
| 03 Sprites | 03.1 · 03.2 · 03.3 | ☐ ☐ ☐ | 10 Planning | 10.1 · 10.2 | ☐ ☐ |
| 04 Rendering | 04.1 · 04.2 · 04.3 | ☐ ☐ ☐ | 11 Build & export | 11.1 · 11.2 · 11.3 | ☐ ☐ ☐ |
| 05 Tiles | 05.1 · 05.2 · 05.3 | ☐ ☐ ☐ | 12 Shaders | 12.1 · 12.2 · 12.3 | ☐ ☐ ☐ |
| 06 Visual synthesis | 06.1 · 06.2 | ☐ ☐ | 13 Autoload safety | 13.1 · 13.2 | ☐ ☐ |
| 07 Isometric | 07.1 · 07.2 · 07.3 | ☐ ☐ ☐ | 14 Performance | 14.1 · 14.2 · 14.3 | ☐ ☐ ☐ |

| Integration labs | Done | Scenarios | Done |
|---|---|---|---|
| Lab 01 — Mini companion full cycle | ☐ | Scenario 01 — Crash on old save | ☐ |
| Lab 02 — Iso tile mini-game | ☐ | Scenario 02 — FPS cliff on zoom | ☐ |
| Lab 03 — CI/CD pipeline | ☐ | Scenario 03 — Autoload init order | ☐ |
| | | Scenario 04 — Android export fails | ☐ |

---

## Per-module exercises

### Module 01 — [GODOT_ENGINE_STUDY.md](../GODOT_ENGINE_STUDY.md)

**Ex 01.1 — Lifecycle logger** ● (20 min)
- **Goal:** Internalize the node lifecycle order.
- **Setup:** Scene: `Root(Node)` → `A(Node)` → `B(Node)` (B child of A), plus one autoload.
- **Steps:** Print from `_init`, `_enter_tree`, `_ready`, and first `_process` of every node and the autoload, with `name` prefix. Predict the full output order on paper *before* running.
- **Acceptance:** Your written prediction matches the console exactly, including the autoload's position and the children-before-parent `_ready` order.
<details><summary>Hints</summary>

- Autoloads enter the tree before the main scene.
- `_enter_tree` is parent-first; `_ready` is child-first. `_process` order follows tree order.
</details>

**Ex 01.2 — Typed vs untyped micro-benchmark** ●● (45 min)
- **Goal:** Measure what static typing buys at runtime.
- **Setup:** Empty scene with one script; use `Time.get_ticks_usec()`.
- **Steps:** Implement the same hot loop (e.g., 1M `Vector2` accumulations through a helper function) twice: fully untyped and fully typed (`-> Vector2`, typed args, typed locals). Run each 5×, report median.
- **Acceptance:** A committed table of numbers plus a 3-sentence conclusion; the typed version should be measurably faster — explain why (variant boxing, dispatch).
<details><summary>Hints</summary>

- Run in an exported release build too — editor timings mislead.
- Keep the work inside a function; top-level loops optimize differently.
</details>

**Ex 01.3 — Server peek** ●● (40 min)
- **Goal:** See the node/server split with your own eyes.
- **Steps:** Draw a textured quad using only `RenderingServer` calls (`canvas_item_create`, `canvas_item_add_texture_rect`) with no Sprite2D. Then toggle its visibility from a Timer.
- **Acceptance:** Texture renders and blinks; a comment block explains what `Sprite2D` was doing for you.
<details><summary>Hints</summary>

- Parent your canvas item to `get_canvas_item()` of any CanvasItem, or to the viewport's canvas.
</details>

### Module 02 — [SCENES_AND_NODES.md](../SCENES_AND_NODES.md)

**Ex 02.1 — Reusable alert scene** ●● (45 min)
- **Goal:** Build a scene with a clean contract: signals up, calls down.
- **Steps:** Create `Alert.tscn` (panel + message label + OK button) with `show_alert(text: String)` and signal `dismissed`. Instance it from two different host scenes.
- **Acceptance:** `Alert.tscn` runs standalone (F6) without errors; hosts never reach inside it (`$Alert/Panel/Label` forbidden); both hosts react to `dismissed`.
<details><summary>Hints</summary>

- Use `%` scene-unique names internally.
- Standalone-run safety: guard demo behavior with `if get_parent() == get_tree().root`.
</details>

**Ex 02.2 — Spawner with `owner` round-trip** ●● (60 min)
- **Goal:** Understand instancing and serialization.
- **Steps:** Button spawns numbered `Collectible.tscn` instances at random `Marker2D`s. A "Save layout" button packs the current arrangement with `PackedScene.pack()` to `user://layout.tscn`; a "Load" button restores it.
- **Acceptance:** Saved file reopened in the editor shows all collectibles; loading at runtime reproduces positions; no orphan nodes at exit.
<details><summary>Hints</summary>

- Spawned nodes only serialize if `child.owner = layout_root` is set.
</details>

**Ex 02.3 — Signal bus starter** ● (30 min)
- **Goal:** Create the bus you will reuse all course.
- **Steps:** Autoload `EventBus` declaring `item_collected(id: StringName)` and `day_passed`. Emit from one scene, react in a sibling scene with no direct reference between them.
- **Acceptance:** Deleting either scene from the tree at runtime causes zero errors in the other (disconnect discipline or bound-object safety).

### Module 03 — [SPRITES_AND_TEXTURES.md](../SPRITES_AND_TEXTURES.md)

**Ex 03.1 — Pixel-art import audit** ● (25 min)
- **Goal:** Correct import settings, proven at zoom.
- **Steps:** Import a 32×32 pixel-art sprite; show it at 1×, 4×, and rotated 30°. Fix filtering (nearest), mipmaps, and project stretch settings until all three views are crisp.
- **Acceptance:** Screenshot trio committed; a checklist comment lists every setting you changed and why.

**Ex 03.2 — Atlas without bleeding** ●● (45 min)
- **Goal:** Build a spritesheet pipeline immune to texture bleeding.
- **Steps:** Pack 4 frames into one sheet twice: tightly packed, then with 2 px extruded padding. Animate both via `AnimatedSprite2D` under linear filtering and slight camera zoom; observe edge artifacts; then fix properly for pixel art.
- **Acceptance:** You can produce the bleeding artifact on demand and explain the two independent fixes (padding vs. nearest+snapping).

**Ex 03.3 — Chibi mini-rig** ●● (60 min)
- **Goal:** SpriteFrames + AnimationPlayer division of labor.
- **Steps:** Chibi with `idle`, `walk`, `wave` in SpriteFrames; an `AnimationPlayer` "celebrate" track that hops the chibi (position), tints it (modulate), and calls `wave` via method track.
- **Acceptance:** `celebrate` composes frame animation and property animation without fighting; interrupting it mid-way leaves no stuck tint/offset (use RESET track).

### Module 04 — [RENDERING_AND_VISUAL_LOGIC.md](../RENDERING_AND_VISUAL_LOGIC.md)

**Ex 04.1 — Layer sandwich** ● (30 min)
- **Goal:** Prove you control draw order at every level.
- **Steps:** Compose: parallax sky (`Parallax2D`), world sprites (z-index bands), HUD (`CanvasLayer`). Add a debug key cycling one sprite through z-index -1/0/+1 relative to a sibling.
- **Acceptance:** One-paragraph comment ranks all ordering mechanisms (tree order, z_index, CanvasLayer) by precedence, verified by the demo.

**Ex 04.2 — `_draw()` progress ring** ●● (45 min)
- **Goal:** Custom drawing with redraw discipline.
- **Steps:** Node2D drawing a circular progress arc (`draw_arc`) fed by a 0-100 property; call `queue_redraw()` only on change. Add a monitor label showing draw-call count.
- **Acceptance:** Arc animates smoothly via a Tween; setting the same value twice triggers no redraw (log proves it).

**Ex 04.3 — Juice pass** ●● (50 min)
- **Goal:** Tween literacy.
- **Steps:** A button "collect" makes a coin fly to the HUD counter: scale pop (BACK/OUT), curved position tween (parallel), counter punch on arrival, all chained in one `create_tween()` call graph.
- **Acceptance:** Spamming the button spawns independent, non-interfering tweens; no `await` deadlocks; total effect < 0.6 s.

### Module 05 — [TILES_AND_TILEMAPS.md](../TILES_AND_TILEMAPS.md)

**Ex 05.1 — Three-layer room** ●● (60 min)
- **Goal:** TileMapLayer stack with physics.
- **Steps:** Build floor/walls/props as three `TileMapLayer`s over one `TileSet` with a physics layer on walls. Drive a `CharacterBody2D` around; props layer is Y-sorted.
- **Acceptance:** Character collides with walls only; walks behind and in front of a tall prop correctly; layers reorder cleanly in the inspector.

**Ex 05.2 — Terrain painting** ●● (45 min)
- **Goal:** Terrains (autotiling) with peering bits.
- **Steps:** Author a 16-tile grass/path terrain set; paint a winding path; then place 5 path cells *from code* with `set_cells_terrain_connect()`.
- **Acceptance:** Hand-painted and code-painted paths produce identical transitions; no "wrong corner" tiles anywhere.
<details><summary>Hints</summary>

- Most bad transitions are one missing peering bit on a corner tile — audit bits, not painting.
</details>

**Ex 05.3 — Custom data gameplay** ●● (40 min)
- **Goal:** Tiles as data carriers.
- **Steps:** Add custom data layer `walk_cost: int`; water = 0 (blocked), grass 1, mud 3. Character's speed reads the tile under it via `local_to_map` + `get_cell_tile_data()`.
- **Acceptance:** Speed visibly changes per surface; stepping toward water is refused before moving (predict target cell, don't correct after).

### Module 06 — [VISUAL_SYSTEMS_SUMMARY.md](../VISUAL_SYSTEMS_SUMMARY.md)

**Ex 06.1 — Visual-stack decision memo** ● (30 min)
- **Goal:** Synthesis: choose the right tool per job.
- **Steps:** For six briefs (HUD element, tall iso prop, rain overlay, minimap, damage flash, background hills), write a one-line tool choice (node/layer/shader/tween) and a one-line rejection of the runner-up.
- **Acceptance:** Choices are consistent with Modules 03-05 guidance; a peer (or you, next week) can't find a cheaper alternative for more than one row.

**Ex 06.2 — Frankenscene refactor** ●●● (90 min)
- **Goal:** Apply the whole visual stack critically.
- **Steps:** Take Ex 04.1 + Ex 05.1 outputs and merge them into a single cohesive scene; document every z-index/Y-sort/CanvasLayer decision inline; then delete one unnecessary mechanism you find.
- **Acceptance:** Rendering is unchanged after the deletion — proving the mechanism was redundant — and the scene diagram in comments matches reality.

### Module 07 — [ISOMETRIC_GAMES.md](../ISOMETRIC_GAMES.md)

**Ex 07.1 — Iso math on paper, then in code** ●● (45 min)
- **Goal:** Own the cartesian↔iso transform.
- **Steps:** Implement `cart_to_iso()` / `iso_to_cart()` as a static helper class for 64×32 tiles; unit-test 6 hand-computed cases (include negatives); then render a 5×5 diamond grid of markers using it.
- **Acceptance:** Tests green; clicking a tile (inverse transform on mouse pos) highlights the mathematically correct cell every time.

**Ex 07.2 — Depth-sort torture chamber** ●● (60 min)
- **Goal:** Y-sort + `y_sort_origin` mastery.
- **Steps:** Iso scene with: tall tree (2-cell base), thin lamppost, flying bird (must always render above), rug (must always render below). Character walks among them.
- **Acceptance:** No sorting error from any direction of approach; bird/rug solved via z-index bands, tree/lamp via sort origin — a comment explains why each tool was chosen.

**Ex 07.3 — Grid pathfinding** ●●● (90 min)
- **Goal:** `AStarGrid2D` on an iso map.
- **Steps:** Sync an `AStarGrid2D` with your 05.3 map (blocked = water); click a cell to path the chibi there, walking cell-centers via `map_to_local()`; mud cells cost extra (weight scale).
- **Acceptance:** Paths avoid water, prefer grass over mud when cheaper, and the chibi's depth sorting stays correct while moving.

### Module 08 — [DATABASE_AND_PERSISTENCE.md](../DATABASE_AND_PERSISTENCE.md)

**Ex 08.1 — Atomic save kata** ●● (45 min)
- **Goal:** The temp+rename pattern, proven hostile.
- **Steps:** `SaveManager.save_dict(data)` writing JSON via temp file + `flush()` + rename. Write a test harness that saves 200 times while a second script kills the process at random delays (or simulate by aborting between steps).
- **Acceptance:** After any interruption, `load()` returns either the previous or the new state — never an error, never a mix. Log committed.

**Ex 08.2 — Migration chain v1→v3** ●● (60 min)
- **Goal:** Stepwise schema migrations.
- **Steps:** v1 `{score}`; v2 adds `streak` (default 0); v3 renames `score`→`points` and adds `history: []`. Implement `migrate_v1_v2`, `migrate_v2_v3`; loader routes any version through the chain. Commit fixture files for v1 and v2.
- **Acceptance:** Unit tests load both fixtures into identical v3 structures; unknown future version (v99) triggers the graceful-refusal path, not a crash.

**Ex 08.3 — SQLite session log** ●●● (90 min)
- **Goal:** godot-sqlite with real SQL hygiene.
- **Steps:** Table `sessions(id, started_at, minutes, kind)`; insert via prepared statements with bindings; queries: total minutes this week, best streak of consecutive days; wrap multi-inserts in a transaction; set `PRAGMA user_version = 1` and WAL mode.
- **Acceptance:** Queries verified against hand-computed fixtures; injection attempt (`kind = "x'); DROP TABLE sessions;--"`) is stored harmlessly as text.

### Module 09 — [PROJECT_DEEP_DIVE.md](../PROJECT_DEEP_DIVE.md)

**Ex 09.1 — Architecture archaeology** ●● (60 min)
- **Goal:** Read a real architecture the way Module 09 dissects Relax Room.
- **Steps:** Diagram the Relax Room module's described architecture: autoloads, signal map, save flow. Then mark two seams where you would extend it (new decoration type; weekly report screen) without touching core files.
- **Acceptance:** Diagram matches the module text; the two extensions are additive (list exactly which new files/signals they need).

**Ex 09.2 — Feature slice, Relax-Room-style** ●●● (2-3 h)
- **Goal:** Implement one vertical feature under the case study's conventions.
- **Steps:** Add a "watering can" interaction to your Ex 05/07 room: action in InputMap → bus signal → chibi walks to plant (pathfinding) → animation → room state mutated → autosaved atomically.
- **Acceptance:** No new autoloads; every cross-system hop goes through the bus; killing the app right after watering preserves the watered state.

### Module 10 — [GAME_DEV_PLANNING.md](../GAME_DEV_PLANNING.md)

**Ex 10.1 — Pre-modification checklist rehearsal** ● (30 min)
- **Goal:** Practice the ritual on a harmless change.
- **Steps:** Pick any earlier exercise; before renaming its main scene's root node, run the full checklist: reproduce current behavior, list dependents (`grep` for the node path/name), plan rollback, then change, then verify.
- **Acceptance:** Checklist run committed as a markdown note beside the change; nothing broke — or the note documents what broke and how the checklist caught it late.

**Ex 10.2 — Debt register & test seed** ●● (45 min)
- **Goal:** Make technical debt visible and pin one behavior with a test.
- **Steps:** Audit your exercises repo; log 5 real debts (hardcoded path, missing type, copy-paste) with cost/payoff estimates. Fix exactly one — the one with the best ratio — and add a GUT or GdUnit4 test pinning the fixed behavior.
- **Acceptance:** `DEBT.md` committed; test runs headless (`godot --headless -s <runner>`) and fails if you revert the fix.

### Module 11 — [BUILD_AND_EXPORT.md](../BUILD_AND_EXPORT.md)

**Ex 11.1 — First clean export** ●● (60 min)
- **Goal:** Export presets done right.
- **Steps:** Export your Ex 09.2 slice for Windows (release), with icon via rcedit, version metadata, and a resource filter excluding `exercises/` folders you don't ship. Run it on a machine/VM without Godot.
- **Acceptance:** Binary runs from a path with spaces and writes saves to `user://`; PCK contains no excluded assets (verify by size or listing).

**Ex 11.2 — Inno Setup installer** ●● (75 min)
- **Steps:** Write an `.iss` script: install dir, Start-menu shortcut, license page, uninstaller that asks before deleting `user://` data; version pulled from one shared constant with the project.
- **Acceptance:** Install → run → uninstall leaves the machine clean; reinstalling over an existing install preserves user data.

**Ex 11.3 — Tag-triggered release pipeline** ●●● (2 h)
- **Goal:** The original Lab 03, now as a module drill.
- **Steps:** GitHub Actions: on push — `gdformat --check`, `gdlint`, `godot --headless --check-only`; on tag `v*` — export Windows + Linux in a godot-ci container, upload artifacts, create a Release. (Slack/webhook notification optional.)
- **Acceptance:** A pushed tag produces downloadable artifacts with the tag's version stamped in-app; a lint error on a branch fails the run.

### Module 12 — [SHADERS_GDSHADER.md](../SHADERS_GDSHADER.md)

**Ex 12.1 — Uniform playground** ● (30 min)
- **Steps:** canvas_item shader with `hint_range` uniforms for brightness/contrast/saturation applied to a sprite; a debug UI of three sliders driving them via `set_shader_parameter()`.
- **Acceptance:** Sliders work at runtime; material is `resource_local_to_scene` so two instances can differ.

**Ex 12.2 — Outline + palette swap** ●● (60 min)
- **Steps:** One shader: alpha-edge outline (using `TEXTURE_PIXEL_SIZE`) toggled by a hover signal, plus a 4-color palette swap driven by a gradient uniform. Apply to the chibi.
- **Acceptance:** Outline hugs the silhouette at any zoom (no box), palette variants switch live, and disabling both uniforms renders the original sprite bit-identically.

**Ex 12.3 — Screen-space rain on glass** ●●● (90 min)
- **Steps:** Fullscreen `ColorRect` shader using `hint_screen_texture` + `SCREEN_UV`: subtle refraction wobble + scanline-free vignette; expose intensity as a global uniform driven by app state (raining/not).
- **Acceptance:** Effect costs < 0.5 ms GPU on your machine (Visual Profiler evidence); intensity animates smoothly from code without touching the material directly.

### Module 13 — [AUTOLOAD_SAFETY.md](../AUTOLOAD_SAFETY.md)

**Ex 13.1 — Init-order minefield** ●● (45 min)
- **Goal:** Reproduce and fix ordering bugs deliberately.
- **Steps:** Create autoloads `Config` and `SaveManager` where SaveManager reads `Config.save_path` in `_ready()`. Break it by reordering the autoload list; observe; then fix twice: (a) ordering + init-time assertion documenting the dependency, (b) lazy access pattern that tolerates any order.
- **Acceptance:** Both fixes survive list reordering; the assertion message names the dependency and the fix ("SaveManager requires Config above it in Project Settings › Autoload").

**Ex 13.2 — Thread-safe save queue** ●●● (2 h)
- **Steps:** Move Ex 08.1 serialization onto `WorkerThreadPool`: main thread enqueues snapshots (Mutex-guarded), worker serializes and atomically writes, completion reported back via `call_deferred` bus emit. Add a thread-guard assertion on every tree-touching method.
- **Acceptance:** 1000 rapid saves cause no data races (validate with a checksum field), UI never hitches > 1 frame, and the guard assertion catches a deliberate wrong-thread call in a test.

### Module 14 — [DESKTOP_COMPANION_PERFORMANCE.md](../DESKTOP_COMPANION_PERFORMANCE.md)

**Ex 14.1 — Perf HUD** ●● (45 min)
- **Steps:** Overlay (CanvasLayer) showing FPS, frame time, static memory, draw calls, orphan nodes via `Performance.get_monitor()`, refreshed twice per second, toggled by an InputMap action.
- **Acceptance:** HUD itself adds < 0.1 ms frame time (measure with it on/off); values match the editor Monitors tab.

**Ex 14.2 — 15/60 adaptive governor** ●●● (90 min)
- **Steps:** Autoload watching input activity and window focus notifications: active → `Engine.max_fps = 60`; idle 10 s or unfocused → 15 + `low_processor_usage_mode`; tray-hidden → 5 with processing disabled on the room subtree. Log transitions on the bus.
- **Acceptance:** OS process monitor shows ≤ 1% CPU idle; interaction restores 60 FPS within one frame; state machine has no flapping (hysteresis).

**Ex 14.3 — Find the planted hotspot** ●● (60 min)
- **Steps:** Add this deliberately bad node to your room: a `_process` loop string-concatenating a log, 400 offscreen animated sprites, and a per-frame `queue_redraw()` ring. Profile, rank the three costs with evidence, fix in cost order.
- **Acceptance:** Before/after profiler screenshots per fix; final frame time within 10% of the pre-sabotage baseline.

---

## Integration labs

The original Labs 01-03, expanded. Each assumes all module drills for its prerequisites are done. These are dress rehearsals for the [capstone](../00-CAPSTONE.md) — same standards, smaller scope.

### Lab 01 — Mini desktop companion, full cycle ●●● (6-10 h)

*Prerequisites: Modules 01-04, 08, 11, 13, 14.*

Build, ship, and post-mortem a minimal companion app (this is the original Lab 01, with acceptance criteria added):

1. Single-window app with an isometric room background (static image acceptable here).
2. Animated chibi character with idle/walk/wave (SpriteFrames + simple FSM).
3. Save/load with v1 schema; then ship a v2 (add one field) with a real migration; keep a v1 fixture to prove it forever.
4. Export Windows installer (Inno Setup) + Linux AppImage.
5. Profile: 60 FPS active, ≤ 15 FPS idle via your governor from Ex 14.2.
6. Document: README + screenshots + performance metrics table.

**Acceptance:** a fresh machine goes from installer download to waving chibi in < 2 minutes; kill-during-save trials pass; post-mortem (½ page) names one thing you will do differently in the capstone.

### Lab 02 — Isometric tile-based mini-game ●●● (6-10 h)

*Prerequisites: Modules 05, 07, 12; Lab 01 recommended.*

Build a 2-room iso game (original Lab 02, expanded):

1. `TileMapLayer` stack with a custom `TileSet`, terrains for ground transitions, physics layer on walls.
2. Character pathfinds via `AStarGrid2D` (or NavigationAgent2D — justify the choice in a comment).
3. Persistent world state: a door unlocked in room A stays unlocked across room changes *and* restarts (bus signal → room state → atomic save).
4. Shaders: outline on hover for interactables; fade-out/in shader or tween transition between rooms.

**Acceptance:** no depth-sorting error in either room from any approach angle; room transition < 200 ms with no shader-compilation hitch on second entry; save file survives schema inspection (documented format).

### Lab 03 — CI/CD pipeline ●● (3-5 h)

*Prerequisites: Module 11; a project from Lab 01/02 to build.*

GitHub Actions workflow (original Lab 03, expanded):

1. On push to any branch: `gdformat --check` + `gdlint`, then `godot --headless --check-only` for parse errors.
2. On push to `main`: additionally run the headless test suite (GUT/GdUnit4) — a red test blocks.
3. On tag push (`v*`): export Windows + Linux + Android (debug keystore) in a godot-ci container matrix.
4. Upload artifacts to the run and attach them to a GitHub Release; job summary lists artifact sizes.
5. Notify a Slack/Discord webhook on completion with status and version (optional if you have no webhook).

**Acceptance:** a deliberately broken script fails step 1 in < 2 min; a tag builds all three artifacts; the Android APK installs on a device/emulator; secrets (keystore passwords) live in repo secrets, never in `export_presets.cfg`.

---

## Scenario debugging

Broken-project exercises: read **Symptoms** only, form hypotheses, write your diagnosis and fix plan, *then* open the spoiler. Practice the diagnostic discipline of [GAME_DEV_PLANNING.md](../GAME_DEV_PLANNING.md): reproduce → isolate → hypothesize → verify → fix → pin with a test. (Scenarios 01-04 preserved from the original catalogue, expanded.)

### Scenario 01 — Crash on loading an old save ●●

**Symptoms:** After updating the app, players report a crash on startup. Log: `Invalid access to property 'streak' ... expected Dictionary, got Nil`. Fresh installs are fine. Deleting the save "fixes" it (and players are furious).

**Your task:** Write the root-cause hypothesis, the immediate hotfix, and the structural fix that prevents the class of bug. What test do you add so it can never ship again?

<details><summary>Diagnosis & fix (spoiler)</summary>

**Root cause:** The new version reads fields introduced in schema v2 from v1 files; there is no schema version check and no migration — fields are accessed without defaults.

**Hotfix:** Defensive `dict.get("streak", 0)` on the crashing reads; never crash on missing keys.

**Structural fix:** Schema version written in every save; a v1→v2 migration function supplying defaults; loader routes through the chain ([DATABASE_AND_PERSISTENCE.md](../DATABASE_AND_PERSISTENCE.md)); v1 fixture file + unit test pinned in CI. Also: back up the old file before migrating.
</details>

### Scenario 02 — FPS cliff on zoom out ●●

**Symptoms:** 60 FPS at default zoom; zooming the camera out 2× drops to ~15 FPS. GPU usage spikes; script time in the profiler barely changes. It's worse in decorated rooms.

**Your task:** Which monitors do you check first? Name three candidate causes and the one-line experiment that separates them.

<details><summary>Diagnosis & fix (spoiler)</summary>

**Root cause:** Zooming out multiplies visible content: draw calls explode (unbatched unique textures) and every particle system in the room is now on-screen and simulated at full rate.

**Separating experiments:** watch `RENDER_TOTAL_DRAW_CALLS_IN_FRAME` while zooming (draw-call growth); hide the particles layer (particle cost); switch to a solid-color material project-wide (fill-rate/overdraw).

**Fix:** atlas the decoration textures to restore batching; gate offscreen/decor particles with `VisibleOnScreenEnabler2D` or zoom-based LOD (fewer particles when zoomed out); cap zoom to the range you actually profiled. See [DESKTOP_COMPANION_PERFORMANCE.md](../DESKTOP_COMPANION_PERFORMANCE.md).
</details>

### Scenario 03 — Autoload works on your machine only ●●

**Symptoms:** `SaveManager._ready()` intermittently errors with `Config.api_url == ""` — but only in exported builds on one teammate's machine, never in your editor. The autoload list shows `SaveManager` above `Config`.

**Your task:** Explain why it's intermittent-looking, list two fixes and their trade-offs, and state which one the course mandates.

<details><summary>Diagnosis & fix (spoiler)</summary>

**Root cause:** Autoloads initialize in Project Settings list order; `SaveManager` sits above `Config`, so it runs first and reads an unset value. It "worked" where a stale editor cache or different timing masked it — order was always wrong.

**Fixes:** (a) reorder the list so `Config` is first **plus** an init-time assertion documenting the dependency (course-mandated: fail fast, loudly, at startup — [AUTOLOAD_SAFETY.md](../AUTOLOAD_SAFETY.md)); (b) make `SaveManager` resolve config lazily / `await` a `config_ready` bus signal — more resilient, more code, hides the dependency. Renaming to `AAA_Config` is a hack: order is set by the list, and the name lies about intent.
</details>

### Scenario 04 — Android export fails after engine upgrade ●●

**Symptoms:** After upgrading the project Godot 4.4 → 4.5, Windows and Linux exports pass, but Android fails in CI with a Java/Gradle error wall. Locally, the editor's Android export dialog shows no obvious red fields.

**Your task:** List the version-matrix suspects in the order you'd check them, and the CI change that stops this recurring at every upgrade.

<details><summary>Diagnosis & fix (spoiler)</summary>

**Root cause:** Export templates and the Android toolchain must match the new engine: 4.4 templates can't serve a 4.5 editor, and the required JDK/SDK/build-tools versions shifted with the upgrade.

**Check order:** (1) export templates version == editor version (re-download 4.5 templates); (2) JDK version required by Godot 4.5; (3) Android SDK/build-tools/NDK versions against the 4.5 docs; (4) if using custom Gradle templates, regenerate them — old ones pin old plugin versions.

**CI fix:** pin the godot-ci image tag to the exact engine version and install templates in the image; add a canary job that runs a debug Android export on a schedule, so toolchain drift fails loudly *before* release day. See [BUILD_AND_EXPORT.md](../BUILD_AND_EXPORT.md).
</details>

---

*Next: apply everything in the [capstone](../00-CAPSTONE.md). Terminology: [00-GLOSSARY.md](../00-GLOSSARY.md).*
