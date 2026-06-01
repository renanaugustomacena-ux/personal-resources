# Syllabus — Godot 4 in Production (Desktop Companion Focus)

> **Type:** formal course structure
> **Language:** English
> **Last updated:** 2026-04-27
> **Pinned versions:** Godot 4.5 (LTS reference); GDScript 2.0; export templates 4.5+; SQLite via Godot SQLite plugin or sqlite3 binary; Inno Setup 6.x for Windows installer.

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

## 4. Course structure (12 modules + meta + new)

### Phase 1 — Foundations
- Module 01 (renamed in scaffolding): `GODOT_ENGINE_STUDY.md` — engine architecture, GDScript, signals, autoload, performance basics.
- Module 02: `SCENES_AND_NODES.md` — scene tree, node lifecycle, PackedScene, instancing, signals.
- Module 03: `SPRITES_AND_TEXTURES.md` — Sprite2D, AtlasTexture, AnimatedSprite2D, pixel art import.

### Phase 2 — Visual systems
- Module 04: `RENDERING_AND_VISUAL_LOGIC.md` — z-ordering, _draw(), tweens, parallax, viewport, themes.
- Module 05: `TILES_AND_TILEMAPS.md` — TileMapLayer, TileSet, terrains, isometric tiles.
- Module 06: `VISUAL_SYSTEMS_SUMMARY.md` — synthesis of visual stack.
- Module 07: `ISOMETRIC_GAMES.md` — projection math, tile systems, depth sorting, famous games.

### Phase 3 — Persistence and project structure
- Module 08: `DATABASE_AND_PERSISTENCE.md` — SQLite, save patterns, sync, schema versioning.
- Module 09: `PROJECT_DEEP_DIVE.md` — Relax Room project architecture (case-study within course).
- Module 10: `GAME_DEV_PLANNING.md` — pre-modification checklist, version control, technical debt.

### Phase 4 — Production
- Module 11: `BUILD_AND_EXPORT.md` — compile, export, CI/CD, installer Windows + Android.

### Phase 5 — New modules (added in scaffolding pass)
- Module 12: `SHADERS_GDSHADER.md` (NEW) — GDShader syntax, built-ins, pixel-art recipes.
- Module 13: `AUTOLOAD_SAFETY.md` (NEW) — autoload init order, thread safety, init-time assertions.
- Module 14: `DESKTOP_COMPANION_PERFORMANCE.md` (NEW) — 15/60 FPS budget targets for desktop, profiler workflow.

### Phase 6 — Capstone
- `00-CAPSTONE.md` — desktop companion mini-project; full-cycle development, profile, export, ship.

## 5. Capstone

Design and ship a small desktop companion app (mini-game + utility, e.g., habit tracker with isometric room visualization, or focus timer with chibi character). Requirements: stable 60 FPS, save/load with v4.0.0 migration, Windows installer + Linux AppImage, primary reading citations in design notes.

## 6. Cadence

| Mode | Hours/week | Weeks |
|---|---|---|
| Full-time | 30-40 | 3-4 |
| Part-time | 8-10 | 12-16 |
| Self-paced | 4-6 | 24+ |

## 7. Notes on the original `Study Documents — Relax Room` README

The original README (preserved) targets the specific Relax Room project. This syllabus generalizes the course while keeping Relax Room as a running case study (`PROJECT_DEEP_DIVE.md`).
