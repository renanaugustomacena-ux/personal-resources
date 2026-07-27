# Syllabus — Godot 4 in Production (Desktop Companion Focus)

> **Type:** formal course structure
> **Language:** English
> **Last updated:** 2026-07-27
> **Pinned versions:** Godot 4.5 (LTS reference); GDScript 2.0; export templates 4.5+; SQLite via Godot SQLite plugin or sqlite3 binary; Inno Setup 6.x for Windows installer.
> **Domain size:** ~40,600 lines across 14 modules + 5 meta files + 2 auxiliary folders.

## 1. Course identity

**"Godot 4.5 in Production"** — desktop companion application focus (small-to-medium scope projects with offline persistence, light isometric/2D rendering, autoload-driven architecture, single-developer maintainability).

**Target competence:** competent → proficient (Dreyfus 3 → 4). Capable of shipping a production-quality desktop companion with: scene composition, signal-driven architecture, save/load with versioning, atomic JSON or SQLite persistence, Inno Setup installer, profiler-validated 60 FPS, accessibility basics.

## 2. Prerequisites

- Programming basics in any language (variables, functions, OOP).
- File system and process basics.
- Familiarity with at least one IDE/editor.
- Math: basic vectors and trigonometry (for isometric).

## 3. Learning objectives

1. Compose game scenes from PackedScenes with proper instancing and lifecycle.
2. Use signals as the primary event/communication mechanism (favoring decoupling over direct calls).
3. Implement autoload (singleton) pattern for global state with thread-safety considerations.
4. Apply isometric projection math, depth sorting, and tile-based design.
5. Implement save/load systems with atomic writes (temp + rename), version migration, and ResourceLoader/Saver patterns.
6. Profile performance (`Performance.get_monitor`, profiler), achieve consistent 60 FPS, identify draw-call hotspots.
7. Build and export multiplatform: Windows (Inno Setup), Linux (AppImage), macOS (notarization considerations), Android (APK/AAB).
8. Manage technical debt and refactoring with version control.

## 4. Course structure (14 modules + meta)

Every module follows a consistent professional format: YAML frontmatter, learning objectives, guiding ideas, ASCII concept map, deep content sections with typed GDScript 2.0 examples and API tables, best practices, troubleshooting table, exercises with acceptance criteria, annotated further reading, and a local glossary.

### Phase 1 — Foundations
- **Module 01** (~3,570 lines): `GODOT_ENGINE_STUDY.md` — Engine architecture, GDScript 2.0 deep dive, signals, autoloads, resources, input, UI, audio, tweens, physics, performance basics, debugging, editor productivity.
- **Module 02** (~2,825 lines): `SCENES_AND_NODES.md` — SceneTree, node lifecycle (_init → _ready ordering), PackedScene instancing, runtime creation/removal, communication patterns, composition vs inheritance, tool scripts.
- **Module 03** (~2,500 lines): `SPRITES_AND_TEXTURES.md` — Texture2D family, import pipeline, pixel-art configuration, Sprite2D, AtlasTexture, AnimatedSprite2D, AnimationPlayer, nine-patch, VRAM budgeting.

### Phase 2 — Visual systems
- **Module 04** (~3,060 lines): `RENDERING_AND_VISUAL_LOGIC.md` — Draw order (z_index, Y-sort, CanvasLayer), 2D transforms, custom _draw(), viewports, modulate, tweens deep dive, Parallax2D, 2D lighting, UI theming.
- **Module 05** (~2,995 lines): `TILES_AND_TILEMAPS.md` — TileSet anatomy, TileMapLayer (4.3+), terrains/autotiling, physics/navigation/occlusion on tiles, custom data layers, scripting, procedural generation, isometric modes.
- **Module 06** (~2,015 lines): `VISUAL_SYSTEMS_SUMMARY.md` — Decision trees, master comparison tables, frame pipeline story, particle essentials, 25 recipe index, performance cheat-sheet.
- **Module 07** (~2,705 lines): `ISOMETRIC_GAMES.md` — Axonometric taxonomy, projection math with matrices, coordinate systems, picking, depth sorting strategies, movement, pathfinding (AStarGrid2D), camera, pixel-art craft, famous-games analysis.

### Phase 3 — Persistence and project structure
- **Module 08** (~3,130 lines): `DATABASE_AND_PERSISTENCE.md` — FileAccess/DirAccess, persistence options decision table, JSON saves, Resource saves (security risks), SaveManager architecture, atomic writes, versioning/migrations, godot-sqlite, JSON+SQLite hybrid, authentication, Supabase cloud sync.
- **Module 09** (~2,000 lines): `PROJECT_DEEP_DIVE.md` — Relax Room architecture case study: SignalBus (31 signals), 8-autoload chain analysis, catalog-driven design, save round-trips, AuthManager security critique, offline-first sync, one-person maintainability.
- **Module 10** (~2,820 lines): `GAME_DEV_PLANNING.md` — GDD-lite, vertical slices, pre-modification checklist, Git for Godot (.gitignore, scene merges, LFS), gdlint/gdformat, GUT vs GdUnit4 testing, CI overview, refactoring recipes, technical debt, solo project management.

### Phase 4 — Production
- **Module 11** (~3,415 lines): `BUILD_AND_EXPORT.md` — Export templates, presets, PCK internals/encryption, Windows (Inno Setup 6), Linux (AppImage), macOS (notarization), Android (keystores, AAB), Web, headless CLI builds, GitHub Actions CI/CD, release engineering, size optimization.

### Phase 5 — Specialized modules
- **Module 12** (~2,710 lines): `SHADERS_GDSHADER.md` — GDShader language, canvas_item built-ins, uniforms (instance/global), screen-reading, 16 shader recipes (outline, dissolve, CRT, palette swap, Bayer dither, etc.), visual shaders, performance, pixel-art craft.
- **Module 13** (~2,420 lines): `AUTOLOAD_SAFETY.md` — Autoload mechanics, initialization order, abuse debate, 6 alternatives (decision table), signal bus safety, threading (Thread/Mutex/WorkerThreadPool), await/coroutines, scene reload persistence, testing, memory.
- **Module 14** (~2,310 lines): `DESKTOP_COMPANION_PERFORMANCE.md` — 15/60 FPS dual budget, Engine.max_fps adaptive manager, VSync, low_processor_usage_mode, focus/minimize throttling, StatusIndicator tray, CPU/GPU/memory optimization, startup, metrics HUD, 24h soak testing.

### Phase 6 — Capstone
- `00-CAPSTONE.md` (~445 lines) — Desktop companion mini-project: 3 scope tiers (minimal/standard/ambitious), FR/NFR requirements, 9 milestones, architecture constraints, grading rubric, submission checklist.

## 5. Meta files

| File | Purpose | Lines |
|---|---|---|
| `00-INDEX.md` | Course index with line counts | ~50 |
| `00-BIBLIOGRAPHY.md` | Annotated bibliography (8 sections, verified URLs) | ~240 |
| `00-GLOSSARY.md` | Course-wide glossary (290+ terms, 14 themed sections) | ~525 |
| `99-EXERCISES/README.md` | Exercise catalogue (38 drills + integration labs + debugging scenarios) | ~420 |
| `99-CASE-STUDY/godot-funding-2024-fork-redot.md` | Godot/Redot fork case study (verified timeline, stakeholder analysis) | ~250 |

## 6. Cadence

| Mode | Hours/week | Weeks |
|---|---|---|
| Full-time | 30-40 | 3-4 |
| Part-time | 8-10 | 12-16 |
| Self-paced | 4-6 | 24+ |

## 7. Document format standard

Every module follows the format established by the Python domain (`04-PROGRAMMAZIONE-PYTHON`):
1. YAML frontmatter (course, phase, module, title, version, level, prerequisites, objectives, tags)
2. Title with version/date banner
3. Learning objectives blockquote with prerequisites, outcomes, time estimate
4. Guiding ideas (4-6 bold one-line principles)
5. ASCII concept map
6. Numbered table of contents
7. Deep content sections with prose, typed GDScript 2.0 examples, tables, pitfall/best-practice callouts
8. Consolidated best practices
9. Common errors & troubleshooting table (Symptom | Likely cause | Fix)
10. Exercises with acceptance criteria and stretch goals
11. Annotated further reading (official docs first)
12. Local glossary table

## 8. Notes on the original `Study Documents — Relax Room` README

The original README (preserved at `README.md`) targets the specific Relax Room project. This syllabus generalizes the course while keeping Relax Room as a running case study (`PROJECT_DEEP_DIVE.md`). The quick-reference cards in the README (autoload order, signal domains, file paths) remain the authoritative source for project-specific facts.
