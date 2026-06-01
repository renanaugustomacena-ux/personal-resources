# Capstone — Godot 4 in Production

> **Position:** Final project for the course
> **Prerequisites:** Modules 01-14 complete; Lab 01-03 from `99-EXERCISES/`.
> **Time:** 30-60 hours over 4-6 weeks
> **Level:** proficient (Dreyfus 4)
> **Last updated:** 2026-04-27

## Brief

Design, build, and ship a small-to-medium desktop companion app in Godot 4.5. Apply every pattern from the course: scene composition, signals, autoload (sparingly), isometric rendering, save/load with versioning, profiler optimization, multi-platform export with installer.

## Project ideas (pick or adapt)

1. **Habit tracker with isometric room.** User tracks daily habits; each habit "decorates" a virtual isometric room (tree planted, plant grown).
2. **Focus timer with chibi character.** Pomodoro timer; chibi character animates based on focus state.
3. **Mini-game companion.** Small turn-based puzzle; saves progress; ships with installer.

## Requirements

| Category | Minimum | Excellence |
|---|---|---|
| Scope | 5 scenes | 10+ scenes |
| FPS budget | Stable 60 FPS active | Adaptive 15/60 |
| Save system | JSON + versioning | SQLite + migration |
| Visuals | Sprites + simple animation | Custom shader + iso |
| Export | Windows installer | + Linux AppImage + Android |
| Tests | Manual checklist | Headless export validation |
| Documentation | README + run instructions | Full project deep dive |
| Profiler | Profiled once | Profiled every iteration |

## Deliverables

1. **Source code in Git.** Tagged release v1.0.
2. **Architecture document (3-5 pagine).** Mirror style of `PROJECT_DEEP_DIVE.md`.
3. **Performance report.** Pre/post optimization numbers.
4. **Export artifacts.** Windows installer + at least one other platform.
5. **Demo video (5 min).** Walkthrough features.
6. **Lessons learned (1 pagina).** What worked, what didn't, what to do differently.

## Rubric

| Category | Weight | Excellence | Minimum |
|---|---|---|---|
| Architecture | 20% | Signals + autoload disciplined | Scenes connect |
| Visuals | 15% | Custom shader + iso polished | Sprites work |
| Persistence | 20% | SQLite + migration chain | JSON saves |
| Performance | 15% | Adaptive FPS, profiled | 60 FPS active |
| Export | 15% | Multi-platform with installer | Windows works |
| Documentation | 10% | Architecture + README + lessons | README exists |
| Testing | 5% | Headless validation | Manual checklist |

**Pass:** ≥ 70%. **Distinction:** ≥ 90%.

## Final review questions

1. What was the hardest design decision and how did you resolve it?
2. Which course module was most impactful?
3. What would you do differently?
4. Is your save system truly robust to crashes?
5. Have you tested rollback to a previous save?
