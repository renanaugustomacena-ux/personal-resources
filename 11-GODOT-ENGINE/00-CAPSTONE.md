---
course: "Godot 4 in Production"
file-role: "Capstone project specification — final assessed project"
version: "Godot 4.5 / GDScript 2.0"
updated: 2026-07-27
tags: [godot, capstone, project-spec, desktop-companion, isometric, assessment]
---

# Capstone — Godot 4 in Production

> **Updated:** 2026-07-27

> **Position:** Final project for the course
> **Prerequisites:** Modules 01-14 complete; Labs 01-03 from [99-EXERCISES/README.md](99-EXERCISES/README.md)
> **Time:** 30-60 hours over 4-6 weeks
> **Level:** proficient (Dreyfus 4)

## Contents

1. [Overview & rationale](#1-overview--rationale)
2. [Learning outcomes mapped to modules](#2-learning-outcomes-mapped-to-modules)
3. [Project variants](#3-project-variants)
4. [Functional requirements](#4-functional-requirements)
5. [Non-functional requirements](#5-non-functional-requirements)
6. [Milestone plan](#6-milestone-plan)
7. [Architecture constraints](#7-architecture-constraints)
8. [Testing & verification requirements](#8-testing--verification-requirements)
9. [Grading rubric](#9-grading-rubric)
10. [Deliverables & submission checklist](#10-deliverables--submission-checklist)
11. [Stretch goals](#11-stretch-goals)
12. [FAQ](#12-faq)
13. [Final review questions](#13-final-review-questions)
14. [Appendix A — Architecture document template](#appendix-a--architecture-document-template)
15. [Appendix B — Performance report template](#appendix-b--performance-report-template)
16. [Appendix C — Demo video shot list](#appendix-c--demo-video-shot-list)
17. [Appendix D — Manual test checklist seed](#appendix-d--manual-test-checklist-seed)

---

## 1. Overview & rationale

Design, build, and **ship** a small-to-medium desktop companion app in Godot 4.5. "Ship" is the operative word: the capstone is not judged on how clever the code is in the editor, but on whether a stranger can download an installer, run the app for a week, close it mid-save, update to a new version, and lose nothing.

The capstone forces every pattern from the course to coexist in one artifact:

- **Scene composition and signals** carry the architecture (Modules 01-02).
- **Sprites, tiles, and isometric math** carry the visuals (Modules 03-07).
- **Versioned, atomic persistence** carries the user's trust (Module 08).
- **Planning, testing, and version control** carry you through weeks 2-6 when motivation dips (Module 10).
- **Profiling and export discipline** carry the app onto other people's machines (Modules 11, 14).
- **Shaders and autoload safety** provide the polish and the robustness that separate "student project" from "production" (Modules 12-13).

A desktop companion is deliberately chosen over a game demo: it must behave like a good desktop citizen (near-zero idle CPU, tray icon, graceful shutdown), which makes performance and lifecycle requirements *measurable* instead of aesthetic.

The reference implementation style is the course case study **Relax Room** ([PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md)). Your project must not be a clone of it, but it should be recognizable as a sibling.

## 2. Learning outcomes mapped to modules

On completion you can demonstrate, with evidence in the submitted repository:

| # | Outcome (you can…) | Evidence expected | Module(s) |
|---|---|---|---|
| LO-1 | Structure an app as composable PackedScenes with clean lifecycles | Scene diagram + no `get_node("../../..")` traversals | [SCENES_AND_NODES.md](SCENES_AND_NODES.md) |
| LO-2 | Use signals (incl. a signal bus) as the primary decoupling mechanism | Signal map in architecture doc; UI never calls gameplay directly | 02, [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) |
| LO-3 | Keep a disciplined, safe autoload layer | ≤ 4 autoloads, init-order safe, init-time assertions | [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) |
| LO-4 | Import and animate pixel-art sprites correctly | Nearest filtering, no texture bleeding, SpriteFrames animations | [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) |
| LO-5 | Build an isometric (2:1 dimetric) space with correct depth sorting | TileMapLayer stack, Y-sort with `y_sort_origin`, no popping props | [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md), [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md) |
| LO-6 | Apply rendering/visual logic deliberately | z-index policy, tweens for feedback, CanvasLayer HUD | [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md), [VISUAL_SYSTEMS_SUMMARY.md](VISUAL_SYSTEMS_SUMMARY.md) |
| LO-7 | Write at least one purposeful canvas_item shader | `.gdshader` file + before/after screenshots | [SHADERS_GDSHADER.md](SHADERS_GDSHADER.md) |
| LO-8 | Implement atomic, versioned save/load with a migration chain | temp+rename writes; migration tests from ≥ 2 old schemas | [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md) |
| LO-9 | Plan, track, and de-risk work over multiple weeks | Milestone log, pre-modification checklists in PRs/commits | [GAME_DEV_PLANNING.md](GAME_DEV_PLANNING.md) |
| LO-10 | Profile and hit explicit performance budgets | Performance report with monitor numbers pre/post | [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) |
| LO-11 | Export, sign(-ready), and package for ≥ 2 platforms | Windows installer + Linux AppImage artifacts from CI | [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md) |
| LO-12 | Explain your engine-dependency risk posture | Engine-risk section in the architecture doc | [99-CASE-STUDY/godot-funding-2024-fork-redot.md](99-CASE-STUDY/godot-funding-2024-fork-redot.md) |

## 3. Project variants

Pick **one** base idea and **one** scope tier. The three base ideas below are inherited from the original capstone brief; you may propose an adaptation, but it must be approved against the FR/NFR lists before Milestone 1.

### Base ideas

1. **Habit tracker with isometric room.** The user tracks daily habits; each completed habit "decorates" a virtual isometric room (a tree planted, a plant grown, a lamp lit). The room *is* the progress visualization.
2. **Focus timer with chibi character.** A pomodoro-style timer; a chibi character animates based on focus state (working, on break, celebrating, asleep after hours). Optional overlay mode keeps the chibi on the desktop.
3. **Mini-game companion.** A small turn-based puzzle (e.g., daily 5-minute tile puzzle) that saves progress, streaks, and statistics, and ships with an installer.

### Scope tiers

| Dimension | **Minimal** (pass-oriented) | **Standard** (recommended) | **Ambitious** (distinction-oriented) |
|---|---|---|---|
| Scenes | 5 scenes | 8-10 scenes | 10+ scenes, incl. settings & onboarding |
| World | Static iso room image + Y-sorted props | TileMapLayer iso room, 1 room | Multi-room or editable/decoratable room |
| Character | Idle + 1 action animation | Idle/walk/action FSM | FSM + pathfinding (AStarGrid2D) + reactions |
| Persistence | JSON, schema v1→v2 migration | JSON or SQLite, 2-step migration chain, backup rotation | SQLite, 3-step chain, export/import of user data |
| FPS policy | Stable 60 active | 60 active / 15 idle adaptive | 60 / 15 / tray-throttled, focus-aware audio |
| Shader | One recipe shader (outline or fade) | Two purposeful shaders | Screen-space effect + per-instance uniforms |
| Export | Windows installer | + Linux AppImage, via CI | + Android APK or macOS notarization dry-run |
| Testing | Manual checklist + smoke test in CI | + unit tests for migrations & core logic | + integration tests, headless save/load round-trip in CI |
| Documentation | README + run instructions | + architecture doc + performance report | + full project deep dive mirroring Module 09 |

> The original requirements table ("Minimum / Excellence") maps onto **Minimal** and **Ambitious**; **Standard** is the calibrated middle most students should target.

## 4. Functional requirements

Applies to every variant unless marked with a tier. "App" = your capstone.

| ID | Requirement |
|---|---|
| FR-01 | The app presents an isometric (or Y-sorted 2D) room as its primary view, rendered from sprites/tiles authored at a consistent scale. |
| FR-02 | An animated character (or equivalent focal actor) exists with at least two states and signal-observable state changes. |
| FR-03 | The user can perform the core utility action (check a habit / start a focus session / play a round) in ≤ 2 interactions from launch. |
| FR-04 | Every completed core action produces visible feedback in the room within 1 second (animation, tween, decoration change, or shader effect). |
| FR-05 | All user state (progress, settings, room state) persists across restarts without any user action ("save on change" or on a bounded autosave interval). |
| FR-06 | Saves are written atomically (temp file + flush + rename). Killing the process at any moment never corrupts the last good save. |
| FR-07 | Save files carry an explicit schema version; the app silently migrates any supported old version to current on load, via a stepwise migration chain. |
| FR-08 | On unsupported/corrupt save data the app degrades gracefully: it backs up the bad file, starts from a valid state, and informs the user — it never crashes. |
| FR-09 | A settings surface exists covering at minimum: audio volume(s), window behavior, and FPS/idle policy visibility. Settings persist separately from game saves (`ConfigFile` acceptable). |
| FR-10 | The app handles `NOTIFICATION_WM_CLOSE_REQUEST`: it flushes pending state and exits cleanly (no lost progress on window close). |
| FR-11 | The app is fully functional offline (offline-first). Any network feature (Standard+ optional) must be an additive layer that fails silently into local-only mode. |
| FR-12 | *(Standard+)* The app minimizes to the system tray (`StatusIndicator`) with restore and quit menu items. |
| FR-13 | *(Standard+)* Time-based features (streaks, sessions) compute correctly across midnight boundaries and system clock changes backward ≤ 1 hour (document your policy). |
| FR-14 | *(Ambitious)* The user can modify the room (place/remove at least 3 decoration types) and the layout persists. |
| FR-15 | At least one canvas_item shader is used for a functional purpose (hover outline, focus dim, day/night tint) — not decoration for its own sake. |
| FR-16 | The app displays its own semantic version (About box, title bar, or settings) matching the Git tag and installer version. |
| FR-17 | All user-facing strings pass through `tr()` with at least the English locale file present (i18n-ready, translation itself not required). |
| FR-18 | Interactive Controls have accessibility descriptions (Godot 4.5 accessibility properties) and full keyboard focus traversal. |

## 5. Non-functional requirements

Every NFR must be *demonstrated* in the performance report or CI, not asserted.

| ID | Requirement | Verification |
|---|---|---|
| NFR-01 | **60 FPS active:** stable 60 FPS (frame time ≤ 16.6 ms, no spike > 33 ms during normal interaction) on the reference machine documented in your report. | Profiler capture + Monitors screenshot |
| NFR-02 | **≤ 1% CPU idle:** with the window unfocused/idle, average CPU ≤ 1% of one core over 5 minutes (via `Engine.max_fps` throttle + `low_processor_usage_mode` + disabled processing). | OS process monitor capture |
| NFR-03 | **Idle FPS policy:** rendered FPS drops to ≤ 15 within 10 s of inactivity and restores to 60 within 1 frame of interaction. | On-screen FPS monitor demo in video |
| NFR-04 | **Cold start ≤ 3 s** from process launch to interactive main scene on the reference machine. | Timed runs (n ≥ 5, report median) |
| NFR-05 | **Memory:** static memory stable over a 2-hour soak (< 5% drift); zero orphan nodes reported at exit. | Monitors graph + `--verbose` exit log |
| NFR-06 | **Save durability:** 20 randomized kill-during-save trials produce zero corrupted/unloadable states. | Scripted test, log in repo |
| NFR-07 | **Save migration:** loading fixture saves of the two previous schema versions yields correct current-state data. | Unit tests in CI |
| NFR-08 | **Installer:** Windows Inno Setup installer installs, creates shortcuts, runs, and uninstalls cleanly (no leftover files except `user://` data; uninstaller asks about user data). | Manual checklist + video |
| NFR-09 | **Second platform:** Linux AppImage (or approved alternative) runs on a distro you did not develop on. | Video or tester sign-off |
| NFR-10 | **CI green:** lint (`gdformat --check`, `gdlint`), `--check-only` parse, and the test suite pass headless on every commit on `main`. | CI badge/history |
| NFR-11 | **Binary size** ≤ 150 MB installed (Standard); document what dominates if you exceed it. | Installer + installed-size numbers |
| NFR-12 | **Crash-free demo:** the 5-minute demo video is a single uncut run with no errors visible in the debugger. | Video |

## 6. Milestone plan

Eight milestones over 4-6 weeks. Each has **deliverables** (artifacts that exist) and **acceptance criteria** (checks that pass). Do not start a milestone before the previous one's criteria pass — descoping (moving a feature from Standard to a stretch goal) is always preferable to skipping acceptance.

### M0 — Pitch & plan (~2 h)
- **Deliverables:** 1-page pitch (idea, tier, MoSCoW-scoped feature list), empty repo with `.gitignore`, CI skeleton running `--check-only` on push, reference-machine spec written down.
- **Acceptance:** pitch names its FR/NFR deviations (if any); CI is green on the empty project; milestone dates are in the README.

### M1 — Walking skeleton (~4-6 h)
- **Deliverables:** main scene loads a placeholder room and character; signal bus autoload + one end-to-end signal (button → bus → room reacts); window close handled.
- **Acceptance:** app runs from a headless export (`--headless --export-release` succeeds); "signals up, calls down" holds; zero orphan nodes at exit.

### M2 — Core loop (~6-10 h)
- **Deliverables:** the core utility action works end-to-end (FR-03, FR-04) with placeholder art; character FSM with 2+ states; input via InputMap actions only.
- **Acceptance:** a first-time user can perform the core action unaided within 30 seconds; FSM transitions logged/observable; manual test checklist v1 exists.

### M3 — Persistence (~6-10 h)
- **Deliverables:** atomic save/load (FR-05..FR-08), schema v1; then an intentional v2 change with migration; kill-during-save test script; backup rotation (Standard+).
- **Acceptance:** NFR-06 trials pass; migration unit tests green in CI; deleting the save directory yields a clean first-run.

### M4 — World & visuals (~8-12 h)
- **Deliverables:** real iso room (TileMapLayer stack for Standard+), final character animations, depth sorting correct, HUD on CanvasLayer, one functional shader (FR-15), feedback tweens.
- **Acceptance:** walk the character behind/in front of every prop with no sorting errors; nearest filtering verified at 2× zoom (no bleeding/shimmer); shader has an in-app purpose.

### M5 — Desktop citizenship & performance (~6-8 h)
- **Deliverables:** adaptive FPS policy, tray mode (Standard+), settings surface (FR-09), soak-test script, first full performance report draft (pre-optimization numbers).
- **Acceptance:** NFR-01..NFR-05 measured (even if not yet all passing — failures become M6 work items with hypotheses).

### M6 — Optimization & hardening (~4-8 h)
- **Deliverables:** profiler-driven fixes for every failed NFR; final performance report with pre/post tables; error-path passes (corrupt save, missing audio device, read-only disk).
- **Acceptance:** all NFR-01..NFR-07 pass on the reference machine; report explains each fix with monitor evidence, not vibes.

### M7 — Export, packaging & CI (~4-6 h)
- **Deliverables:** Inno Setup installer, Linux AppImage, CI release job on tag (`v*`) attaching both artifacts; version stamped in-app (FR-16).
- **Acceptance:** NFR-08..NFR-10 pass; a clean VM (or second machine) installs and runs both artifacts.

### M8 — Release & post-mortem (~3-4 h)
- **Deliverables:** tag `v1.0`; architecture document; demo video (≤ 5 min); lessons-learned page; submission checklist completed.
- **Acceptance:** every item in [§10](#10-deliverables--submission-checklist) checked; a peer (or you, after 48 h away) can follow the README from clone to running installer.

### Suggested weekly cadence (part-time, 6 weeks)

| Week | Milestones | Watch out for |
|---|---|---|
| 1 | M0 + M1 | Over-designing the pitch; a walking skeleton beats a perfect plan |
| 2 | M2 | Art rabbit holes — placeholders are mandatory until M4 |
| 3 | M3 | "It saves on my machine" — the kill-test script is the milestone |
| 4 | M4 | Depth-sorting whack-a-mole: fix the sort-origin convention once, globally |
| 5 | M5 + M6 | Optimizing before measuring; every fix needs a before number |
| 6 | M7 + M8 | Installer surprises on clean machines — leave two evenings of slack |

### Risk register (pre-filled — extend with your own)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Art takes 3× longer than planned | High | Schedule | CC0/licensed asset packs allowed; art quality is only part of one 15% criterion |
| Migration chain designed after the fact | Medium | Rubric (20%) | Introduce schema v2 *deliberately* in M3, while the codebase is small |
| Idle CPU won't go under 1% | Medium | NFR-02 | Start from `low_processor_usage_mode` + max_fps early (M5), not as a final patch |
| Export works, installer doesn't | Medium | NFR-08 | Build the `.iss` script in M1's CI skeleton with a dummy build; iterate all course long |
| Scope creep via "one more decoration" | High | All | MoSCoW list from M0 is contractual; new ideas go to the stretch-goal parking lot |
| Single reference machine dies | Low | Evidence | Commit raw monitor logs continuously, not only the final report |

## 7. Architecture constraints

These are graded under "Architecture" and audited in the code review:

1. **Autoload budget: maximum 4** (recommended: `EventBus`, `SaveManager`, `Settings`, plus one project-specific). Each autoload's reason-to-exist is documented in the architecture doc. See [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md).
2. **Init-order safety:** no autoload references another autoload in `_init()`/`_enter_tree()`; cross-autoload wiring happens in `_ready()` or later, with init-time assertions guarding assumptions.
3. **Signal bus for cross-feature events** — gameplay, persistence, and UI communicate through bus signals; direct references only within a scene's own subtree ("signals up, calls down").
4. **No logic in UI scripts:** Controls translate clicks into bus signals/actions and render state; they never mutate saves or game rules.
5. **Atomic saves only:** every write to `user://` game state goes through one save module implementing temp + flush + rename. No scattered `FileAccess.open()` calls.
6. **Typed public surface:** exported variables, public functions, and signal parameters are statically typed.
7. **Scene contracts:** every scene runs standalone (F6) without crashing — use init-time assertions with helpful messages for required context.
8. **No `get_parent()` chains upward** for logic; a node never assumes what its parent is beyond its documented contract.
9. **Text formats everywhere:** `.tscn`/`.tres`/`.gdshader` committed; `.godot/` ignored; `.uid` files committed.
10. **One honest hack allowed:** you may take one documented shortcut (logged as technical debt with a payoff plan) — practicing *visible* debt is part of the course.

## 8. Testing & verification requirements

| Layer | Minimum (all tiers) | Standard+ |
|---|---|---|
| Static | `--check-only` + `gdlint`/`gdformat --check` in CI | same, blocking merge |
| Unit | Migration chain functions; core domain logic (streak math, timer state) | + save serialization round-trip; iso/grid math helpers |
| Integration | Manual checklist (versioned in repo, dated runs) | Headless save→load→assert scenario via GUT or GdUnit4 in CI |
| Smoke | App boots headless and exits 0 in CI | + main scene instantiation test for every scene file |
| Destructive | Kill-during-save script (NFR-06) | + corrupt-save fixtures, read-only `user://` handling |
| Soak | 2-hour monitored run before submission | scripted soak with metric log committed |

Framework choice (GUT vs. GdUnit4) is free; justify it in one sentence in the architecture doc. Tests must run headless in CI — a test that only runs inside the editor does not count.

## 9. Grading rubric

Weights preserved from the original brief. **Pass:** ≥ 70%. **Distinction:** ≥ 90%. Each criterion scores 0-100 and is multiplied by its weight.

| Criterion | Weight | Excellent (90-100) | Adequate (70) | Poor (< 50) |
|---|---|---|---|---|
| **Architecture** | 20% | Signal bus + ≤ 4 disciplined autoloads; scenes standalone-runnable; constraints §7 all hold; debt logged deliberately | Scenes connect sensibly; signals used for most cross-feature talk; minor constraint violations, acknowledged | Spaghetti of `get_node` paths; autoload sprawl; UI mutating game state; undocumented hacks |
| **Persistence** | 20% | Atomic writes proven by kill tests; ≥ 2-step migration chain with tests; graceful corrupt-save handling; (SQLite done well, if chosen) | JSON saves with version field and one working migration; atomic pattern present; basic error handling | Saves corruptible by crash; no versioning; load errors crash the app |
| **Visuals** | 15% | Polished iso room with flawless depth sorting; purposeful shaders; cohesive art scale & filtering; juicy, restrained feedback | Sprites and room work; occasional sorting/bleeding artifacts; shader present | Placeholder-quality output; broken sorting; filtering/bleeding artifacts throughout |
| **Performance** | 15% | All NFR-01..05 pass with headroom; adaptive 15/60 with focus awareness; report shows hypothesis→measure→fix loops | 60 FPS active and a working idle throttle; report has real numbers pre/post | No profiling evidence; idle CPU high; spikes during normal use |
| **Export** | 15% | CI builds installer + AppImage on tag; installs/uninstalls cleanly on fresh machines; version stamped everywhere consistently | Windows installer works; second platform exported manually | Only editor runs; broken installer; version chaos |
| **Documentation** | 10% | Architecture doc a peer could maintain from; performance report; honest lessons-learned; README from clone to install | README + run instructions + brief architecture notes | Missing or stale docs |
| **Testing** | 5% | CI-run unit + integration + destructive tests; checklist runs dated | Manual checklist + smoke test + migration unit tests | No systematic testing |

## 10. Deliverables & submission checklist

Deliverables (unchanged in substance from the original brief):

1. **Source code in Git**, tagged release `v1.0`, CI history green.
2. **Architecture document** (3-5 pages), mirroring the style of [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md): scene diagram, signal map, autoload inventory, save-format spec, engine-risk note.
3. **Performance report**: reference machine, budgets, pre/post optimization numbers per NFR.
4. **Export artifacts**: Windows installer + at least one other platform, attached to the tagged release.
5. **Demo video (≤ 5 min)**: uncut walkthrough of the core loop, idle throttle, kill-during-save recovery, and install.
6. **Lessons learned (1 page)**: what worked, what didn't, what you would do differently.

Submission checklist — every box checked before you submit:

- [ ] `git clone` + README instructions reach a running editor project in ≤ 10 minutes
- [ ] `main` is green in CI; tag `v1.0` exists and built the release artifacts
- [ ] All FRs for your tier demonstrably met (map them in the README to where/how)
- [ ] NFR evidence table complete in the performance report
- [ ] Fresh-machine install test done (VM counts) for the Windows installer
- [ ] Kill-during-save log committed; migration fixtures + tests committed
- [ ] Zero errors/warnings in the debugger during the demo-video run
- [ ] Architecture doc's signal map matches the code (spot-check three signals)
- [ ] Technical-debt register present (even if it has one honest entry)
- [ ] Video ≤ 5 min, uncut, shows version number on screen at least once

## 11. Stretch goals

Only after all acceptance criteria pass — each is designed to deepen one module without destabilizing the rest:

- **Cloud sync (Module 08):** opt-in Supabase backup with last-write-wins conflict policy and full offline fallback.
- **Overlay mode (Module 14):** borderless transparent always-on-top chibi with mouse passthrough outside its silhouette.
- **Day/night ambience (Module 12):** global-uniform-driven tint + window light shader keyed to local time.
- **Room editor (Modules 05/07):** drag-and-drop decoration placement with grid snapping and occupancy validation.
- **Android build (Module 11):** touch-adapted layout, APK in CI, input abstraction audit.
- **Localization:** ship a real second language end-to-end, including font fallback.
- **Auto-update check:** version manifest fetch with graceful offline behavior (display-only; no self-patching).

## 12. FAQ

**Can I use C# instead of GDScript?** No. The course assesses GDScript 2.0 idioms; mixing languages also complicates the export/CI rubric lines. (Your architecture doc may note where C# or GDExtension *would* pay off.)

**Can I use 3D or a non-isometric 2D style?** Top-down/side 2D with Y-sorted depth is acceptable at a small rubric cost under Visuals; full 3D is out of scope — the visual rubric line assumes the 2D pipeline taught in Modules 03-07.

**Can I reuse code from the course modules and exercises?** Yes, encouraged — with attribution comments. Third-party assets are fine if licensed and credited; third-party *systems* (a complete save plugin, a complete state-machine addon) void the corresponding rubric line unless agreed beforehand.

**Do I need SQLite?** No — JSON with a proper migration chain fully satisfies Standard. Choose SQLite when your data is relational (logs, statistics queries); choosing it *and* using it badly scores worse than clean JSON.

**What is the "reference machine"?** Any real machine you name in the performance report (CPU, RAM, GPU, OS). NFRs are measured there. Don't pick your fastest machine: mid-range hardware makes your numbers credible.

**What if I can't reach 60 FPS?** Diagnose CPU- vs GPU-bound first ([DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md)). If a documented investigation shows a hardware-bound cause with a principled mitigation, graders weigh the process heavily — silent failure weighs against you.

**Is multiplayer/networking allowed?** Only the optional sync stretch goal. Real-time networking is out of scope and eats capstone weeks for zero rubric benefit.

**How is plagiarism handled?** Your demo video + a 15-minute code walkthrough conversation must show you can explain and modify any file on request.

**Can I change tier mid-project?** Downward, yes — descoping Standard → Minimal at any milestone is a legitimate planning decision if logged with reasons in the milestone notes. Upward only before M3: persistence and performance requirements compound, and late upgrades reliably sink schedules.

**My idea needs a feature no module covers (e.g., webcam, global hotkeys). Allowed?** Allowed if it's additive: the app must still meet every FR/NFR with the feature removed. Budget research time separately and expect no rubric credit for the extra feature itself — credit comes from how cleanly it integrates.

**How "finished" must the art be?** Coherent beats beautiful. Consistent tile size, palette, and outline convention with licensed/CC0 assets scores better than mixed-style original art. The Visuals criterion rewards *correct rendering decisions*, which you control regardless of drawing skill.

### Review session flow (what to expect)

The capstone review is a 45-60 minute session:

1. **Demo (10 min):** your video, or live if you prefer — same shot list either way.
2. **Evidence walk (15 min):** you drive — CI history, performance report numbers, kill-test log, migration tests.
3. **Code walkthrough (15 min):** reviewer picks 2-3 files; you explain design, then make one small live change (e.g., add a field to the save schema) to demonstrate ownership.
4. **Questions (10 min):** the review questions below, plus anything raised during the walk.
5. **Scoring:** rubric filled in during the session; you receive the completed table with per-criterion notes.

## 13. Final review questions

Prepare spoken answers — these close the capstone review (preserved from the original brief):

1. What was the hardest design decision and how did you resolve it?
2. Which course module was most impactful?
3. What would you do differently?
4. Is your save system truly robust to crashes? How do you *know*?
5. Have you tested rollback to a previous save?

And two added for the production focus:

6. Show the profiler evidence behind one optimization you shipped — and one you decided *not* to ship.
7. If Godot 4.6 broke one API you depend on, which would hurt most, and what is your migration plan?

---

## Appendix A — Architecture document template

Copy this outline into `docs/ARCHITECTURE.md` in your capstone repo; 3-5 pages total. Mirror the tone of [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md): explain *why*, not just *what*.

```
1. Overview (½ page)
   - One paragraph: what the app is, for whom, chosen variant & tier.
   - One paragraph: the three most important architectural decisions and
     the alternative each one rejected.

2. Scene composition (½-1 page)
   - Tree diagram of top-level scenes (Mermaid or ASCII).
   - For each reusable scene: its contract (inputs it needs, signals it
     emits, whether it runs standalone).

3. Signal map (½ page — table)
   | Signal (bus) | Emitted by | Consumed by | Payload | Why a signal? |

4. Autoload inventory (¼ page — table)
   | Autoload | Responsibility (one line) | Depends on | Why it must be global |
   - Statement of init-order assumptions and where they are asserted.

5. Save format specification (1 page)
   - Current schema (fields, types, example file).
   - Version history table: version | introduced in app version | change |
     migration function.
   - Atomicity mechanism and where it lives in code.
   - Corruption/unknown-version policy.

6. Performance architecture (¼ page)
   - FPS governor states and transitions; what is disabled in each state.

7. Engine-risk note (¼ page — LO-12)
   - Engine version pinned and why; upgrade policy; result of the
     engine-risk checklist from the case study, in 5-8 bullet points.

8. Technical-debt register (¼ page — table)
   | # | Debt | Cost today | Cost if ignored | Planned payoff |
```

## Appendix B — Performance report template

Copy into `docs/PERFORMANCE.md`. Numbers without machine context are noise — the reference machine section is mandatory.

```
1. Reference machine
   CPU / RAM / GPU / OS / monitor Hz / power profile (laptops: on AC).
   Godot version + renderer backend (Forward+/Mobile/Compatibility).

2. Budgets (from NFR-01..NFR-05)
   | Metric | Budget | Measured (idle) | Measured (active) | Pass? |
   | Frame time avg / p95 | ≤16.6 ms / ≤33 ms | | | |
   | CPU idle (5 min avg) | ≤1% of one core | | | |
   | Idle FPS | ≤15 within 10 s | | | |
   | Cold start (median of 5) | ≤3 s | | | |
   | Static memory drift (2 h) | <5% | | | |
   | Orphan nodes at exit | 0 | | | |

3. Optimization log (one entry per intervention)
   ### <date> — <symptom>
   - Hypothesis:
   - Measurement before (monitor/profiler evidence, attach screenshot path):
   - Change:
   - Measurement after:
   - Verdict (kept / reverted / follow-up):

4. Rejected optimizations
   - <optimization> — why it wasn't worth it (evidence).

5. Soak test
   - Script used, duration, metric log path, anomalies.
```

## Appendix C — Demo video shot list

≤ 5 minutes, one uncut run, debugger visible or FPS HUD on. Suggested timing:

| # | ~Time | Shot | Proves |
|---|---|---|---|
| 1 | 0:00-0:20 | Launch from installed build; version visible | FR-16, NFR-04 |
| 2 | 0:20-1:20 | Core loop performed twice, room feedback shown | FR-03, FR-04 |
| 3 | 1:20-1:50 | Character FSM states + one shader effect in context | FR-02, FR-15 |
| 4 | 1:50-2:30 | Settings changed, app restarted, everything persisted | FR-05, FR-09 |
| 5 | 2:30-3:10 | Kill the process mid-save (script), relaunch, state intact | FR-06, NFR-06 |
| 6 | 3:10-3:40 | Old-schema fixture save loads and migrates | FR-07 |
| 7 | 3:40-4:10 | Idle: FPS HUD drops to ≤15, OS monitor shows ~0% CPU; interact to restore | NFR-02, NFR-03 |
| 8 | 4:10-4:40 | Tray minimize/restore (Standard+) and clean close | FR-10, FR-12 |
| 9 | 4:40-5:00 | Uninstall runs; user-data prompt shown | NFR-08 |

## Appendix D — Manual test checklist seed

Version this file and date every run. Extend per feature; never delete a row that once caught a bug.

- [ ] Fresh install, first run: onboarding/defaults correct, save dir created
- [ ] Core action works with mouse only; again with keyboard only
- [ ] Window close during active session: nothing lost on next start
- [ ] Save dir deleted while app closed: clean first-run, no crash
- [ ] Save file replaced with garbage bytes: backup + graceful recovery (FR-08)
- [ ] System clock moved back 1 h: streak/session policy behaves as documented (FR-13)
- [ ] Audio device unplugged mid-session: no crash, sane fallback
- [ ] 200% display scaling: UI readable, nothing clipped (HiDPI)
- [ ] Two instances launched: second either focuses first or handles the lock explicitly
- [ ] Uninstall → reinstall: user data preserved (per your installer policy)

---

*Back to [00-SYLLABUS.md](00-SYLLABUS.md) · Practice first in [99-EXERCISES/README.md](99-EXERCISES/README.md) · Terminology in [00-GLOSSARY.md](00-GLOSSARY.md)*
