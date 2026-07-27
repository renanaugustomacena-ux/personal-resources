---
course: "Godot 4 in Production"
phase: "3 — Persistence and project structure"
module: "09"
title: "Project Deep Dive — Relax Room Architecture Case Study"
version: "Godot 4.5 / GDScript 2.0"
level: "Intermediate"
prerequisites:
  - "SCENES_AND_NODES.md"
  - "DATABASE_AND_PERSISTENCE.md"
objectives:
  - "Map the complete Relax Room architecture: the 8-entry autoload chain, the 31 SignalBus signals in 9 domains, the catalog-driven data layer and the three persistence layers"
  - "Trace a full signal flow from user input to persisted state, naming every emitter and listener along the path"
  - "Justify the autoload initialization order and predict which subsystems break under any given reordering"
  - "Evaluate the catalog-driven JSON content system for schema discipline, validation strategy and moddability"
  - "Walk a complete save round-trip: dirty flag, 60-second autosave, atomic JSON write with backup, SQLite mirror"
  - "Critique the SHA-256 authentication design against industry password-storage standards and propose a stronger replacement"
  - "Extract the transferable patterns (event bus, data-driven content, offline-first persistence) and apply them to a project of your own"
tags: [godot, architecture, case-study, signal-bus, autoload, observer-pattern, data-driven, offline-first, persistence, sqlite, authentication, maintainability]
---

# Project Deep Dive — Relax Room Architecture Case Study — Complete Guide

> **Module 09** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Scenes and Nodes](SCENES_AND_NODES.md), [Database and Persistence](DATABASE_AND_PERSISTENCE.md) — and ideally the whole Phase 1-2 sequence listed in the [reading order](README.md).
>
> By the end of this module you will be able to:
> 1. Draw the complete Relax Room architecture from memory: scenes, the 8-entry autoload chain, the SignalBus with its 31 signals in 9 domains, the JSON catalogs and the persistence stack.
> 2. Trace any user action from input event to persisted state, naming every signal, emitter and listener along the path.
> 3. Explain *why* each autoload sits where it does in the initialization order, and predict exactly what breaks under a reordering.
> 4. Analyze the catalog-driven content system: its schema conventions, its validation posture and what it would take to make it moddable.
> 5. Walk the full save round-trip — dirty flag, autosave timer, atomic write, backup file, SQLite mirror — and identify its failure modes.
> 6. Critique the project's SHA-256 authentication with a proper threat model and propose the industry-standard alternative.
> 7. Reuse the three big transferable patterns (event bus, data-driven content, offline-first) in a project that is not Relax Room.
>
> **Estimated time:** 6-8 hours (reading + exercises) · **Level:** Intermediate

## Guiding ideas

1. **Real architecture is a ledger of trade-offs — read the decisions, not just the code.**
2. **One event bus, 31 signals, zero direct cross-references between systems: decoupling is a discipline, not an accident.**
3. **Initialization order *is* architecture: the autoload chain is the dependency graph written down.**
4. **Content lives in data, behavior lives in code — the catalog is the contract between the two.**
5. **The local file is the source of truth; the network is an optimization, not a requirement.**
6. **Design for the one person who will maintain this in a year. That person is probably you, with none of today's context.**

## Concept map

```
                            ┌───────────────────────────────┐
                            │   RELAX ROOM (Godot 4.5)      │
                            │   desktop companion, 2D,      │
                            │   pixel art, offline-first    │
                            └───────────────┬───────────────┘
                                            │
          ┌─────────────────────────────────┼─────────────────────────────────┐
          │                                 │                                 │
┌─────────▼──────────┐          ┌───────────▼────────────┐        ┌───────────▼──────────┐
│  SCENES (.tscn)    │          │  AUTOLOADS (8)         │        │  DATA (v1/data/)     │
│                    │          │  1 SignalBus           │        │                      │
│  v1/scenes/menu/   │          │  2 AppLogger           │        │  characters.json     │
│   main menu +      │          │  3 LocalDatabase       │        │  decorations.json    │
│   auth screen      │          │  4 AuthManager         │        │   (69 items,         │
│  v1/scenes/main/   │          │  5 GameManager         │        │    11 categories)    │
│   the room         │          │  6 SaveManager         │        │  rooms.json          │
│  v1/scenes/ui/     │          │  7 AudioManager        │        │  tracks.json         │
│   panels           │          │  8 PerformanceManager  │        │                      │
└─────────┬──────────┘          └───────────┬────────────┘        └───────────┬──────────┘
          │                                 │                                 │
          │            listens / emits      │      loads catalogs at startup  │
          └────────────────┬────────────────┴────────────────┬────────────────┘
                           │                                 │
                  ┌────────▼─────────────────────────────────▼───┐
                  │              SIGNAL BUS                      │
                  │   31 signals in 9 domains:                   │
                  │   Room(4) Decorations(5) Character(2)        │
                  │   Audio(4) UI(2) Auth(5) System(6)           │
                  │   Settings(1) Sync(2)                        │
                  │                                              │
                  │   The only sanctioned channel between        │
                  │   systems. No direct cross-calls.            │
                  └────────────────────┬─────────────────────────┘
                                       │
                  ┌────────────────────▼─────────────────────────┐
                  │              PERSISTENCE                     │
                  │                                              │
                  │  user://save_data.json      (primary, v5.0.0)│
                  │  user://save_data.backup.json (last good)    │
                  │  user://cozy_room.db  (SQLite mirror,        │
                  │                        9 tables, WAL mode)   │
                  │      └── sync_queue table ──► Supabase cloud │
                  │                               (Phase 4, not  │
                  │                                yet active)   │
                  └──────────────────────────────────────────────┘
```

## Table of contents

1. [Why Study a Real Codebase](#1-why-study-a-real-codebase)
2. [Project Vision and Scope Discipline](#2-project-vision-and-scope-discipline)
3. [Architecture at a Glance](#3-architecture-at-a-glance)
4. [The SignalBus: Observer Meets Mediator](#4-the-signalbus-observer-meets-mediator)
5. [Autoload Chain: Initialization Order as Architecture](#5-autoload-chain-initialization-order-as-architecture)
6. [Catalog-Driven Content Design](#6-catalog-driven-content-design)
7. [Scene Hierarchy: Menu and Room](#7-scene-hierarchy-menu-and-room)
8. [PanelManager and the UI Lifecycle](#8-panelmanager-and-the-ui-lifecycle)
9. [The Save System: Dirty Flags and Round Trips](#9-the-save-system-dirty-flags-and-round-trips)
10. [Versioned Saves and the Migration Chain](#10-versioned-saves-and-the-migration-chain)
11. [Offline-First Persistence: JSON, SQLite, Sync Queue](#11-offline-first-persistence-json-sqlite-sync-queue)
12. [AuthManager: Guest, Registered, Deleted](#12-authmanager-guest-registered-deleted)
13. [Performance Posture](#13-performance-posture)
14. [One-Person Maintainability](#14-one-person-maintainability)
15. [File Layout Conventions](#15-file-layout-conventions)
16. [Best Practices](#16-best-practices)
17. [Common Errors & Troubleshooting](#17-common-errors--troubleshooting)
18. [Exercises](#18-exercises)
19. [Further Reading](#19-further-reading)
20. [Glossary](#20-glossary)

---

## 1. Why Study a Real Codebase

Every other module in this course teaches a mechanism: how signals work, how scenes instance, how SQLite persists. This module teaches something no isolated mechanism can: **how decisions compose**. Relax Room is a real, shipping-grade IFTS 2026 projectwork — a desktop companion app built in Godot 4.5 — and this document is a guided autopsy of its architecture.

Tutorial code is contrived by design. It exists to demonstrate exactly one thing, so it can afford to ignore everything else: error handling, initialization order, save migration, memory hygiene, licensing. Production code cannot ignore anything. When you read Relax Room's architecture, you are reading a record of collisions between competing goods — simplicity versus flexibility, speed of iteration versus safety, features versus maintainability — and the trade-offs someone actually chose.

### How this module is organized

Each architectural area gets three layers of treatment, and it is worth being conscious of which layer you are reading at any moment:

| Layer | What it contains | Epistemic status |
|-------|------------------|------------------|
| **The facts** | What the project actually does, per its own documentation | Documented — verifiable against the project |
| **The why** | Trade-off analysis: what was gained, what was paid | Reasoned from the facts |
| **Generalized lesson** | The transferable industry pattern behind the decision | General software-engineering knowledge |

Code snippets in this module come in two flavors. A few are reproduced from the project's own study documentation. Most are marked **ILLUSTRATIVE**: they show the *shape* of a mechanism in valid Godot 4.5 / GDScript 2.0, but are written for teaching and are not verbatim project code. Never quote an illustrative snippet as if it were the project source.

> ✅ **Best practice** — When studying any real codebase, keep the same three-layer separation in your notes: *what it does*, *why it does it*, *what transfers*. The first layer expires with the project; the third layer is yours forever.

### How to work through this module

A suggested pass structure, matching the estimated 6-8 hours:

1. **First pass (60-90 min):** read Sections 1-5 linearly — vision, big picture, bus, chain. Stop and reproduce the concept map and the autoload chain from memory before continuing; everything later leans on them.
2. **Second pass (2-3 h):** Sections 6-12, the systems. After each section, answer its "what does this decision buy / cost / assume" trio in your own words — one sentence each is enough.
3. **Third pass (60 min):** Sections 13-17 — posture, maintainability, layout, the imitate/reconsider lists, the troubleshooting table. These consolidate; read them with the earlier sections' details still warm.
4. **Exercises (2-3 h):** at minimum, Exercise 1 (trace), Exercise 3 (reordering), and Exercise 4 (design-within). These three cover the module's three skills: reading flows, reasoning about order, and extending without breaking.

### The case-study method

Architecture cannot be learned purely from pattern catalogs, for the same reason medicine cannot be learned purely from anatomy textbooks: patterns in isolation are clean, and real systems are not. The case-study method — dominant in business and law education, underused in software — forces you to confront a system where every decision constrains every other decision.

Concretely, as you read this module you should keep asking three questions that professional reviewers ask in architecture reviews:

1. **What does this decision buy?** (the benefit that motivated it)
2. **What does this decision cost?** (the flexibility, performance or simplicity given up)
3. **What would have to change for this decision to become wrong?** (the load-bearing assumptions)

The third question is the most valuable and the least asked. Relax Room's architecture is excellent *for a small offline desktop companion maintained by a tiny team*. Several of its choices — a single global event bus, dual-write persistence, code-built UI — would be questionable at 10× the scope. Part of becoming an architect is learning to attach a *validity domain* to every pattern you admire.

---

## 2. Project Vision and Scope Discipline

### The facts: what Relax Room is

Relax Room is a **desktop companion** — a small, always-running application designed to sit in the corner of your screen while you study or work. Think of a digital aquarium, but instead of fish you get a cozy pixel-art room with a character, lo-fi music, and decorations you place yourself.

The desktop companion genre is niche but well established. The project's own documentation cites its inspirations: **Shimeji** (characters that walk on your desktop), **Desktop Goose** (a goose that interferes with your work), **Spirit** on Steam (a desktop virtual pet), and above all **Lo-fi Girl**, the iconic studying animation. Relax Room takes the "lo-fi study atmosphere" concept and makes it interactive: instead of watching someone else's loop, you customize your own room, choose your character, and play your own music.

The target audience is students and remote workers who want a calming digital presence during focused work. That audience definition directly produces four documented product requirements:

- **Unobtrusive** — 60 FPS when the window is focused, throttled to 15 FPS in the background.
- **Offline-first** — everything works with no internet connection at all.
- **Lightweight** — minimal CPU/GPU/battery usage; it must coexist with the user's real work.
- **Customizable** — your room, your decorations, your music.

And four documented design pillars sit above every feature decision:

1. **Relaxation** — everything should feel calm and cozy.
2. **Personalization** — the room should feel like *your* space.
3. **Low friction** — it should "just work" without configuration.
4. **Pixel-art aesthetic** — a consistent, nostalgic visual style.

### The facts: what the project's history shows about scope

A vision statement is cheap; what proves scope discipline is the record of what got **removed**. Relax Room's own documentation trail preserves several contractions:

| What changed | Before | After |
|--------------|--------|-------|
| Decoration catalog | 118 decorations in 14 categories (earlier documentation) | **69 decorations in 11 categories** (current quick reference) |
| Save schema (v3 → v4 migration) | contained `tools`, `therapeutic`, `xp`, `streak`, `currency`, `unlocks` sections | replaced by a single `inventory` section (`coins`, `capacita`, `items`), preserving coins |
| Cloud sync | SupabaseClient present as an autoload in the earlier documented chain | deferred to **Phase 4**; the current 8-entry chain has no cloud client, only a local `sync_queue` |
| Automated tests | GdUnit4 test suite | removed (March 2026); GdUnit4 no longer installed |

Read that table slowly, because it is the most honest artifact in the whole project. The v3 → v4 save migration is particularly telling: fields named `xp`, `streak` and `therapeutic` imply the project once flirted with gamification and wellness-tracking features. Those were cut. What survived is exactly what the four pillars predict: a room, a character, music, decorations, coins.

### The facts: the shipped content inventory

Scope also has a positive face: what the project *does* ship. The documented content inventory:

| Category | Count | Format | Source |
|----------|-------|--------|--------|
| Rooms | 4 (10 themes) | JSON + color palettes | Custom |
| Decorations | 69 (11 categories) | PNG sprites | CC0 / free commercial |
| Characters | 3 playable | Spritesheets (PNG) | CC0 |
| Music | 2 tracks | WAV | Mixkit (free) |
| Ambience | Configurable set | WAV | Mixkit (free) |
| UI | Full pixel UI kit | PNG | Kenney (CC0) |
| Backgrounds | 8-layer forest parallax | PNG | Eder Muniz |
| Pets | 1 (Void Cat) | PNG | CC0 |

Every asset's license terms are documented in `v1/assets/README.md`, and the project restricts itself to three license classes: **CC0** (public domain, no restrictions), **free for commercial use** (with or without credit), and assets that may not be redistributed raw but may ship inside a product. No GPL or copyleft assets appear anywhere — a deliberate firewall against license contamination in a distributable executable.

Read as a scope document, the inventory is eloquent. Two music tracks is not a music library; it is a proof that the music *system* (crossfade, playlists, shuffle — Section 7) works, with the catalog ready to grow by data alone. One pet is not a pet system; it is a charming outlier kept because it cost nearly nothing. The asymmetry — 69 decorations against 2 tracks — maps exactly onto the product's center of gravity: decoration is the core loop, music is ambience. A scope-disciplined inventory is *deliberately lopsided* toward the pillar features.

### The facts: one project, two masters

Relax Room is an **IFTS academic projectwork**, and its documentation is explicit that it serves two purposes at once: it must be a *real product* (working, polished, distributable) and a *learning platform* covering the breadth of software engineering the course examines. The documented topic map runs from architecture (signal-driven design, singletons, separation of concerns) through database design (schema, foreign keys, migrations), API integration, CI/CD (GitHub Actions, linting — the project glossary names `gdlint`/`gdformat` in the pipeline), version control, testing, security (secret scanning, `.env` management, input validation), performance, UX, persistence, and team management (roles, code review, documentation).

The documented topic map, in full:

| Topic | Where in the project |
|-------|----------------------|
| Software architecture | Signal-driven design, singleton pattern, separation of concerns |
| Database design | SQLite schema, foreign keys, migrations |
| API integration | Supabase REST client, HTTP pooling, auth tokens (Phase 4 territory) |
| CI/CD | GitHub Actions, linting, automated checks |
| Version control | Git, branching, collaborative workflow |
| Testing | GdUnit4, unit tests, TDD (suite removed March 2026 — Section 14) |
| Security | Secret scanning, `.env` management, input validation |
| Performance | FPS capping, memory-leak prevention, profiling |
| User experience | Pixel-art consistency, audio design, smooth transitions |
| Data persistence | JSON saves, versioned migrations, backup/restore |
| Team management | Role assignment, code review, documentation |

The dual mandate explains several choices that a pure product would simplify away. A pure desktop toy does not need a SQLite mirror *and* a JSON save (Section 11) — but a course that examines relational databases does. It does not need a documented audit report — but a course that teaches code review does. The lesson for reading *any* codebase: identify all the masters a project serves before judging its complexity. What looks like overengineering against one goal is often exactly-right engineering against a second, unstated one.

### The why: vision as a rejection filter

The purpose of a vision statement is not inspiration — it is **rejection**. "Relaxation, personalization, low friction, pixel art" sounds like marketing until you notice what it forbids:

- *Relaxation* forbids streaks, XP and daily-login pressure — which is precisely why the v4 migration deleted `xp` and `streak`. A streak counter is a guilt mechanism; guilt is the opposite of the product.
- *Low friction* forbids mandatory accounts — which is why AuthManager has a guest mode (Section 12) and why cloud sync is optional and deferred.
- *Lightweight/unobtrusive* forbids a fancy renderer — which is why the project runs on the GL Compatibility backend and throttles background FPS (Section 13).
- *Pixel-art aesthetic* forbids mixing asset styles — which is why the content inventory documents the license and source of every asset pack rather than grabbing whatever looks good.

Notice the direction of causality: the pillars came first, the deletions followed. Scope discipline is not the ability to say no in the abstract; it is a **written standard that makes specific features arguable**. When someone proposes a leaderboard, you do not argue taste — you point at pillar 1.

There is also a harder-nosed reading of the same history. This is an academic projectwork with a deadline and, in practice, one system architect responsible for the whole codebase. 118 decorations in 14 categories is a content-maintenance surface 70% larger than 69 in 11 — every item needs a sprite, a catalog entry, a license check, and placement testing. Cutting the catalog was not an artistic decision; it was a maintenance-budget decision (Section 14 returns to this).

> ⚠️ **Pitfall** — The test-suite removal (March 2026) is scope discipline's dark side. Cutting *content* reduces surface area with little risk; cutting *verification* reduces effort now at the price of risk forever. Treat these as different categories even when the schedule pressure feels identical. Section 16 revisits this as a "reconsider" item.

### Generalized lesson: scope is a budget, not a backlog

Industry post-mortems are remarkably consistent on this point: projects rarely die from building their core badly; they die from building too much around the core. The transferable technique from Relax Room is threefold:

1. **Write pillars that forbid things.** A pillar that nothing conflicts with is decoration. Test each pillar by asking "what popular feature does this rule out?" — if the answer is "nothing", rewrite it.
2. **Let the save schema tell the truth.** Your persistence format is a confession of your actual scope. If your save file has sections for features you half-built, your scope is out of control. Relax Room's v4 schema cleanup was scope control performed *at the data layer*, which is where it becomes real.
3. **Record deletions.** The migration chain (Section 10) means every cut feature left a fossil. That record is what allows a document like this one to reconstruct the reasoning. In your own projects, a `CHANGELOG` entry for every removal costs a minute and preserves the argument forever.

How you would apply this elsewhere: before adding any feature to your own game, write the save-file diff it implies *first*. If you are not willing to migrate and maintain those fields for the life of the project, you are not willing to build the feature — you just don't know it yet.

---

## 3. Architecture at a Glance

### The facts: three planes plus a bus

Relax Room's architecture separates into three planes, with a fourth element — the SignalBus — connecting them:

1. **The scene plane** (`v1/scenes/`) — what the player sees. A main-menu scene (with its auth screen), the main room scene, and the UI panel scenes. Scenes hold nodes, scripts on those nodes handle input and rendering, and *nothing else*.
2. **The autoload plane** (`v1/scripts/autoload/` plus `v1/scripts/systems/`) — eight singletons that hold state and coordinate systems: SignalBus, AppLogger, LocalDatabase, AuthManager, GameManager, SaveManager, AudioManager, PerformanceManager. They exist before any scene loads and survive every scene change.
3. **The data plane** (`v1/data/` and `user://`) — read-only JSON catalogs that define *what content exists* (characters, decorations, rooms, tracks), and writable persistence that records *what the player did* (`user://save_data.json`, its backup, and the SQLite database `user://cozy_room.db`).

The **SignalBus** is the only sanctioned channel between systems: 31 signals grouped in 9 domains. The project's core architectural rule, stated in its own documentation, is that **no component directly calls another component's logic** — systems announce events on the bus and whoever cares reacts.

A second architectural rule follows from the first: **state flows downward, events flow upward**. Autoloads own canonical state (GameManager owns the catalogs and current selections, SaveManager owns the persisted snapshot, AudioManager owns playback state). Scenes read that state to draw themselves, and report player actions as signals. A scene never mutates an autoload's internals directly — the project's documented anti-pattern list explicitly forbids writing `SaveManager.game_data["settings"]["volume"] = 0.5` in favor of emitting `settings_updated` and letting SaveManager react.

### The facts: the project by the numbers

Before diving into any single area, load the key figures into working memory. They function as a mental checksum — whenever your model of the system produces different numbers, your model is wrong somewhere:

| Number | Meaning |
|-------:|---------|
| **8** | autoloads in the initialization chain |
| **31** | SignalBus signals |
| **9** | signal domains |
| **9** | SQLite tables in `user://cozy_room.db` (WAL mode) |
| **v5.0.0** | current save-format version |
| **69 / 11** | decorations / categories in the catalog |
| **4 / 10** | rooms / themes |
| **3** | playable characters |
| **2** | music tracks (plus a configurable ambience set) |
| **60 / 15** | FPS focused / unfocused |
| **64 px** | decoration snap grid |
| **60 s** | autosave interval (when dirty) |
| **1280×720** | design viewport |
| **24** | scripts analyzed by the project's v2.0.0 technical audit (1 April 2026) |

### The facts: the architecture moved under its own documentation

Comparing the project's earlier deep-dive documentation with its current quick-reference cards reveals that the architecture itself evolved:

| Aspect | Earlier documented state | Current documented state |
|--------|--------------------------|--------------------------|
| Signals | 21 signals in 7 domains | **31 signals in 9 domains** |
| Autoload chain | 8 entries including a `SupabaseClient` autoload at position 7 | 8 entries with **AuthManager at position 4** and no cloud client; cloud sync deferred to Phase 4 |
| Save format | v4.0.0 | **v5.0.0** |
| SQLite tables | 7 | **9** |
| Decorations | 118 in 14 categories | **69 in 11 categories** |

Two additions (the Decorations editing domain and the Sync domain, plus a much richer Auth domain) account for the signal growth; the sync queue and auth storage plausibly account for the table growth. The important meta-lesson: **architecture documents have versions too**, and a document that disagrees with the code is worse than no document. Relax Room handles this by keeping a compact quick-reference card (autoload order, signal domains, file paths) in its study README — small enough to actually keep current — alongside longer prose documents like this one.

### The why: why this shape and not another

This is, recognizably, a **hub-and-spoke** architecture: many independent systems, one shared communication hub, one shared data layer. Alternative shapes were available:

- **Direct references** (each system holds references to the systems it talks to): simplest to trace, but produces an N×N coupling web. With 8 singletons and a dozen scene scripts, that web is already unmanageable — removing any one system breaks every system that referenced it.
- **Layered calls** (UI → application layer → data layer, classic three-tier): great for request/response software, awkward for games where events originate everywhere (input, timers, focus changes, audio finishing) and interested parties are scattered.
- **Full ECS** (entity-component-system): designed for thousands of homogeneous entities needing cache-friendly iteration. Relax Room has one character, tens of decorations and four panels — ECS would be architecture cosplay here.

Hub-and-spoke with an event bus fits because the app is *event-shaped*: almost everything that happens is a small, discrete, user-triggered event (placed a decoration, changed a track, toggled a panel) with one to three interested parties. The bus makes those parties independent, which is what allows the project's documented claim that systems can be added or removed without touching existing code.

> ✅ **Best practice** — Choose the architecture that matches the *shape of your events and data*, not the one with the best conference talks. The correct question is never "is an event bus good?" but "is my app event-shaped, and are my events small and discrete?"

### Generalized lesson: architecture as communication topology

Strip away Godot specifics and Relax Room's big picture is a pattern you will meet everywhere: **components + broker + shared store**. Frontend apps with a state container and an action dispatcher; microservice fleets around a message broker; desktop apps around a notification center — all are the same topology at different scales. What varies is the delivery guarantee (in-process synchronous here; queued and persistent in a message broker) and the failure model. When you meet a new codebase, your first archaeology question should be topological: *how do parts find out that something happened?* Answer that, and half the architecture is understood.

---

## 4. The SignalBus: Observer Meets Mediator

### The facts: one autoload, 31 signals, 9 domains

`SignalBus` is the first autoload in the chain (`v1/scripts/autoload/signal_bus.gd`). It has no dependencies, holds no game state, and contains essentially nothing but signal declarations. Every cross-system communication in the app travels through it. The current inventory is 31 signals in 9 domains:

| Domain | Count | Signals |
|--------|------:|---------|
| **Room** | 4 | `room_changed`, `decoration_placed`, `decoration_removed`, `decoration_moved` |
| **Decorations** (edit mode) | 5 | `decoration_mode_changed`, `decoration_selected`, `decoration_deselected`, `decoration_rotated`, `decoration_scaled` |
| **Character** | 2 | `character_changed`, `outfit_changed` |
| **Audio** | 4 | `track_changed`, `track_play_pause`, `ambience_toggled`, `volume_changed` |
| **UI** | 2 | `panel_opened`, `panel_closed` |
| **Auth** | 5 | `auth_state_changed`, `auth_error`, `account_created`, `account_deleted`, `character_deleted` |
| **System** | 6 | `save_requested`, `save_completed`, `load_completed`, `save_to_database_requested`, `settings_updated`, `music_state_updated` |
| **Settings** | 1 | `language_changed` |
| **Sync** | 2 | `sync_started`, `sync_completed` |

The project's own metaphor for the bus is worth preserving: an office where every employee walks to a colleague's desk to ask for things breaks down the moment someone is on vacation — the visitor crashes into an empty desk. An office intercom does not care who is present: you announce what happened, and whoever is listening reacts. If nobody is listening, nothing bad happens. The SignalBus is the intercom.

In Godot terms, an autoload full of signal declarations looks like this (**ILLUSTRATIVE** — the shape, not the project file):

```gdscript
## signal_bus.gd — ILLUSTRATIVE shape of a signal-bus autoload
extends Node

# Room domain
signal room_changed(room_id: String)
signal decoration_placed(item_data: Dictionary, position: Vector2)
signal decoration_removed(decoration_id: String)
signal decoration_moved(decoration_id: String, new_position: Vector2)

# System domain
signal save_requested
signal save_completed
signal load_completed

# ...no functions, no state. Declarations only.
```

Producers emit — `SignalBus.decoration_placed.emit(item_data, snapped_pos)` — and consumers subscribe in `_ready()`:

```gdscript
## ILLUSTRATIVE — a consumer subscribing to the bus
func _ready() -> void:
    SignalBus.decoration_placed.connect(_on_decoration_placed)
    SignalBus.load_completed.connect(_on_load_completed)
```

### The pattern: observer, mediator, or both?

Textbooks would file this under two different Gang-of-Four patterns, and the interesting truth is that SignalBus is deliberately *between* them:

- **Observer** — a subject maintains a list of observers and notifies them. Godot's built-in `signal` mechanism *is* the observer pattern: each signal keeps its list of `Callable`s and invokes them synchronously on `emit()`. But in plain observer, consumers must hold a reference to the concrete subject to subscribe — the coupling survives, just inverted.
- **Mediator** — colleagues never talk to each other; every interaction routes through a central coordinator that *contains the interaction logic*. Full mediator centralizes intelligence — the coordinator decides who is told what, in what order.

SignalBus is an **event bus**: mediator's topology (everything routes through one hub) with observer's dumbness (the hub decides nothing). This hybrid is exactly what you want for a game of this size, and it is worth understanding why each half was chosen:

- Mediator's *topology* is kept because it solves discovery: producers and consumers only need to know one global name, `SignalBus`, rather than each other. A panel deep in the UI tree and an autoload can rendezvous without either knowing the other exists.
- Mediator's *intelligence* is discarded because centralizing interaction logic makes the hub a god object — every feature change would edit the same file, and the hub becomes the most merge-conflicted, most fragile script in the project. A bus that is only declarations essentially never has bugs.

The cost, documented candidly by the project itself, is **indirection**: to answer "who reacts to `decoration_placed`?" you must search the codebase for `decoration_placed.connect`. Control flow that used to be a function call you could ctrl-click is now a distributed conversation. This is the fundamental event-bus trade: coupling is minimized, *traceability is taxed*. Mitigations exist (naming discipline, a signal inventory table like the one above, grep-friendly connect syntax), but the tax can only be reduced, never eliminated.

### Analysis: naming — events, not commands (with one deliberate exception)

Look at the 31 names again with a grammarian's eye. Nearly all are **past-tense facts**: `decoration_placed`, `track_changed`, `account_created`, `save_completed`. This is event-bus naming discipline at its best: a signal describes *something that already happened*, and the emitter neither knows nor cares what happens next. Past-tense naming keeps the emitter honest — you cannot secretly command a specific receiver if your vocabulary only lets you announce history.

Two signals break the tense rule, and the break is meaningful: `save_requested` and `save_to_database_requested`. These are **command-shaped events** — "someone wants a save to happen." The project routes even *commands* through the bus rather than calling `SaveManager.save_game()` directly, which buys the same decoupling (any script can request a save without importing SaveManager's API) at the price of a semantic wrinkle: a request implies an expected handler. If nobody listens to `decoration_placed`, nothing is wrong; if nobody listens to `save_requested`, the app silently stops saving. Requests on a bus therefore need exactly one owner, and that ownership must be documented — here, SaveManager owns `save_requested` and LocalDatabase owns `save_to_database_requested`.

The `_requested` suffix convention makes this distinction visible in the name itself. That is the transferable trick: **let naming carry semantics**. In this vocabulary:

| Suffix pattern | Semantics | Contract |
|----------------|-----------|----------|
| `*_changed`, `*_placed`, `*_completed`, `*_created`, `*_deleted` | fact notification | zero or many listeners; emitter indifferent |
| `*_requested` | command routed via bus | exactly one owning handler; must be documented |
| `*_toggled` | fact notification of a boolean flip | listener must read the new state from the payload, not guess |

One genuine naming wart is preserved in the project's own documentation history: the play/pause signal appears as `track_play_pause_toggled` in the earlier document and as `track_play_pause` in the current quick-reference card. A one-word drift seems trivial until you remember the traceability tax: everyone hunting for listeners greps for the name. If the docs and code disagree on the name, the grep fails silently. The lesson is not "be more careful" (nobody sustains care); it is **generate reference lists from code** — a 20-line editor script can dump every signal declared on the bus, and a generated table cannot drift.

> ⚠️ **Pitfall** — On a shared bus, renaming a signal is an API break with invisible blast radius: `connect` sites fail loudly at runtime, but *documentation, tests and teammates' mental models* fail silently. Rename bus signals with the same ceremony you would use for a public API: search all connect/emit sites, update the inventory table, note it in the changelog.

### Analysis: granularity — five signals for one feature, one signal for five features

The Decorations domain and the Settings/System domains sit at opposite ends of the granularity spectrum, and comparing them teaches more about API design than any abstract rule.

**Fine-grained:** decoration *editing* gets five dedicated signals — `decoration_mode_changed`, `decoration_selected`, `decoration_deselected`, `decoration_rotated`, `decoration_scaled` — on top of the Room domain's placement trio. Why so many? Because decoration editing is the core gameplay loop, and its events have *different audiences*: the room's visual layer cares about rotation and scale; the save system cares that anything changed; the UI cares about selection state to show/hide manipulation handles. Merging these into one `decoration_edited(kind: String, ...)` signal would force every listener to switch on `kind` and receive events it doesn't want — the coupling would sneak back in through the payload.

**Coarse-grained:** settings changes travel as a single `settings_updated` signal carrying a dictionary (the documented replacement for directly poking `SaveManager.game_data`). One signal, arbitrary payload. Why is coarse right here? Because settings listeners overwhelmingly want *the same thing* — "re-read your relevant settings" — and because adding a signal per setting (`master_volume_changed`, `language_changed`, `window_mode_changed`, ...) would triple the bus for zero decoupling benefit. Note the project *does* split out `language_changed` and `volume_changed` — the two settings whose consumers are numerous and specialized (every label; every audio player). That is granularity chosen by *audience*, not by symmetry.

The rule that falls out of Relax Room's choices:

> ✅ **Best practice** — Granularity follows audience. Split a signal when different listeners want different subsets of the events. Merge signals when all listeners would react identically. Never split or merge for aesthetic symmetry of the inventory table.

### Analysis: coupling — what the bus actually buys, measured

"Decoupling" deserves to be more than a slogan, so make it concrete. Without a bus, the documented decoration-placement flow (Section 9 walks it fully) would require the drop zone to hold references to the decoration renderer *and* the save system; the save system to be known by every mutating script; the audio panel to reach into AudioManager; and so on. Every producer would name every consumer: coupling grows multiplicatively with features.

With the bus, each script's coupling surface is: **SignalBus, plus the autoloads whose *state* it legitimately reads** (e.g., a shop panel reads `GameManager` catalogs). Producers have fan-out zero — `DropZone` emits `decoration_placed` and is done. Consumers have fan-in one — `SaveManager` connects to the handful of signals that dirty the save. Adding a feature means adding *connections*, never *modifications*: the project's documentation makes exactly this claim — features can be added or removed without touching existing code — and the claim is credible precisely because emitters cannot name receivers.

Three second-order consequences deserve attention:

1. **Lifetime safety.** In the intercom metaphor, nobody crashes into an empty desk. Concretely: Godot automatically disconnects a signal connection when the *listening object* is freed, so a panel that connected in `_ready()` and was later `queue_free()`d does not leave a dangling callback on the bus. The one leak-shaped exception: connections whose target is a lambda capturing a long-lived object, or connections made *to* an object that outlives the emitter's expectations. The bus, being an autoload, outlives everything — which is exactly why listeners' auto-cleanup matters so much.
2. **Testability.** A system whose only inbound API is bus signals can be tested by emitting signals at it; a system whose only outbound effect is bus signals can be tested by connecting a probe. No mocks of concrete collaborators needed. (Bitter irony, documented: the project removed its GdUnit4 suite in March 2026 — the architecture is highly testable and currently untested. Section 14.)
3. **Ordering opacity.** When several listeners connect to one signal, Godot invokes them synchronously in connection order — which is *initialization* order, which is autoload order plus scene-tree timing. The project never relies on listener order (each handler is self-contained), and that is the only sane policy: the moment handler B depends on handler A having run first, you have hidden sequential coupling that the bus topology actively conceals.

> ⚠️ **Pitfall** — The bus makes *bad* coupling easy too. Nothing stops a script from emitting `save_requested` from inside a handler for `save_completed`, creating an emit cycle; nothing stops twenty scripts from abusing `settings_updated` as a general-purpose RPC channel. A bus enforces *how* systems talk, not *whether what they say is sensible*. Architecture review still has a job.

### Analysis: connection hygiene — the mechanics that keep a bus safe

The bus's architectural virtues assume its mechanical use stays disciplined. The Godot 4.x idioms worth internalizing (**ILLUSTRATIVE** throughout):

```gdscript
# 1. Connect in _ready(), never _init() — ordering guarantees (Section 5).
func _ready() -> void:
    SignalBus.volume_changed.connect(_on_volume_changed)

# 2. Guard against double connection when a connect path can re-run
#    (Godot 4 errors on duplicate connections of the same Callable):
    if not SignalBus.track_changed.is_connected(_on_track_changed):
        SignalBus.track_changed.connect(_on_track_changed)

# 3. One-shot listeners for one-time events (auto-disconnects after firing):
    SignalBus.load_completed.connect(_on_first_load, CONNECT_ONE_SHOT)

# 4. Deferred delivery when a handler would mutate what an emitter iterates
#    (runs at idle time instead of mid-emission):
    SignalBus.decoration_removed.connect(_on_removed, CONNECT_DEFERRED)

# 5. Bind extra context at connect time instead of storing it in a field:
    SignalBus.panel_opened.connect(_on_panel_opened.bind("shop"))
```

Three hygiene rules complete the picture. **Prefer method references to lambdas for long-lived connections** — a named method is greppable (the traceability tax again) and is auto-disconnected when its object is freed, while an anonymous lambda is neither searchable nor obviously owned. **Let typed signal parameters do contract enforcement** — declaring `signal decoration_placed(item_data: Dictionary, position: Vector2)` turns a wrong-shaped emit into an immediate error instead of a silent listener misfire. **Never `await` inside a bus handler casually** — a suspended handler makes one listener's completion invisible to the emitter and interleaves in ways synchronous reasoning no longer covers; if a handler needs async work, have it schedule that work and return.

### Analysis: reading the nine domains as subsystem contracts

The domain grouping is not just table formatting — each domain is effectively the *published interface* of one subsystem, and reading them one by one recovers the whole application's behavior. This is the payoff of a disciplined bus: the signal inventory doubles as an architecture summary.

**Room (4)** is the persistent world model's changelog: `room_changed` (a different room or theme was selected) plus the placement trio `decoration_placed` / `decoration_removed` / `decoration_moved`. Every signal in this domain corresponds to something the save file must remember — this is the domain whose every emission ultimately sets the dirty flag (Section 9). Its producers are the interaction layer (drop zone, decoration drag logic); its consumers are the renderer and SaveManager.

**Decorations (5)** is the *editing session*: `decoration_mode_changed` gates an edit mode on and off, `decoration_selected` / `decoration_deselected` track which item has the player's attention, `decoration_rotated` / `decoration_scaled` report manipulations. Note the subtle split between this domain and Room: Room announces changes to *the room*; Decorations announces changes to *the editing interaction*. Selection, in particular, is pure session state — no save file should ever record what was selected. The two manipulation signals raise a sharper question: the documented v4.0.0 save format stores only `item_id`, `position` and `z_index` per placed decoration, with no rotation or scale fields, while these signals belong to the newer 31-signal inventory. Whether v5.0.0 persists rotation/scale is not recorded in the documents this module draws on — a perfect example of a question the signal inventory lets you *formulate precisely* before opening the code to answer it (Exercise 2 sends you there).

**Character (2)** — `character_changed`, `outfit_changed` — models avatar identity as two orthogonal axes: who you are and what you wear. Keeping them separate means an outfit listener (a sprite refresher) need not re-run full character setup, and vice versa.

**Audio (4)** is granularity-by-audience in its purest form: which track (`track_changed`), whether it plays (`track_play_pause`), the ambience toggles (`ambience_toggled`), and loudness (`volume_changed`) are four independent axes of audio state, each with different listeners — the crossfade engine, the play button's icon, the ambience mixers, every volume-respecting player. One merged `audio_changed` signal would force all of them to parse a compound payload for the one axis they care about.

**UI (2)** is remarkable for its *smallness*: of all the clicks, hovers, tabs and scrolls a UI generates, exactly two facts are global — a panel opened, a panel closed. Everything else stays local inside the panel scripts. This is the discipline most bus architectures lose first: the moment button-level events reach the global bus, the bus becomes a keylogger and every listener drowns in noise. The rule Relax Room embodies: **an event belongs on the bus only if a system outside its producer's subtree legitimately cares.**

**Auth (5)** packages an identity state machine (`auth_state_changed`), a separate failure channel (`auth_error`), and a data lifecycle (`account_created`, `account_deleted`, `character_deleted`) — Section 12 reads it in full.

**System (6)** is the persistence spine, and the only domain with request/response structure: the command `save_requested` and its completion fact `save_completed`; the boot beacon `load_completed` (the signal the whole startup sequence converges on — Section 5); the mirror trigger `save_to_database_requested`; and two coarse state broadcasts, `settings_updated` and `music_state_updated`.

**Settings (1)** — `language_changed` — is the lone setting promoted out of `settings_updated`, because its audience is uniquely wide and specialized: every piece of visible text. Promoting exactly the signals whose audiences demand it, and no more, is the granularity principle applied with restraint.

**Sync (2)** — `sync_started`, `sync_completed` — is the most interesting domain because *nothing currently emits it*: the cloud layer is Phase 4 (Section 11). These are **reserved seams**: API surface declared ahead of the feature so that UI (a sync spinner, a "last synced" label) and persistence logic can be written against a stable contract before the network code exists. Two unused signals cost nothing; a retrofitted contract costs every call site.

Summarizing the walk as an ownership matrix — which subsystem *speaks* each domain, and which primarily *listens* (design reading, derived from the documented responsibilities):

| Domain | Primary speakers | Primary listeners |
|--------|------------------|-------------------|
| Room | DropZone, decoration interaction scripts | Room renderer, SaveManager |
| Decorations | Edit-mode interaction scripts | Selection UI, room renderer |
| Character | Character selection UI | Room scene, SaveManager |
| Audio | Music panel, AudioManager | AudioManager, play/pause UI, SaveManager |
| UI | PanelManager | Input/pause logic, anything panel-aware |
| Auth | AuthManager | Menu/auth UI, SaveManager, profile UI |
| System | SaveManager (facts), any script (requests) | SaveManager, LocalDatabase, all state-restorers |
| Settings | Settings panel | Every label (`language_changed`), audio players |
| Sync | *(reserved — Phase 4 sync worker)* | *(reserved — sync UI, persistence)* |

A final structural read: tally producers and consumers across domains and the traffic pattern becomes visible. SaveManager is the system's great **fan-in point** — most Room, Character, Audio and Settings facts converge on it to dirty the save. The boot's `load_completed` is the great **fan-out moment** — one emission triggers restoration across AudioManager, PerformanceManager, GameManager and the scene layer. Interaction scripts like the drop zone are pure producers; panels are mixed (produce facts, consume state broadcasts). Sketching this traffic map for any bus-based codebase — which signals converge, which explode — tells you where the risk lives: fan-in points need the most testing, fan-out moments need the most ordering care.

### Generalized lesson: the event bus beyond Godot

The pattern family here is ancient and everywhere. Robert Nystrom's *Game Programming Patterns* treats the queued variant as the **Event Queue** — "an asynchronous observer": something happened, record it, let interested parties respond later. GUI frameworks are built on event loops; Android/iOS apps use notification centers and broadcast systems; backend fleets use message brokers (RabbitMQ, Kafka) where the "bus" gains persistence, delivery guarantees and consumer groups; Martin Fowler catalogs the same idea between services as *event notification*. Relax Room's bus is the smallest member of the family: **in-process, synchronous, unqueued**. Know what changes as you scale up the family tree:

| Property | SignalBus (in-process) | Queued in-game bus | Message broker (distributed) |
|----------|------------------------|--------------------|------------------------------|
| Delivery | synchronous, same frame | deferred (next frame/tick) | asynchronous, over network |
| Ordering | connection order | queue order | per-partition at best |
| Failure mode | listener error surfaces immediately in-frame | error surfaces later, harder to attribute | retries, dead-letter queues, duplicates |
| Cost | ~zero | small (queue + copy) | serialization, latency, infrastructure |
| When to prefer | few listeners, cheap handlers | expensive handlers, burst smoothing, replay/logging | separate processes/machines |

Two mature judgments to carry away. First, **synchronous is a feature at small scale**: when `decoration_placed` is emitted, every consequence has fully happened by the next line — no "eventually consistent" reasoning, no frame-later bugs. Give that up only when a real problem (frame spikes from expensive handlers, need for replay) forces you to. Second, **the bus is a public API**: its 31 signals are the project's true interface between systems, more so than any class. Version it, inventory it, and review changes to it with corresponding seriousness — which is exactly why the project's quick-reference card lists all 31 signals by domain.

How you would apply this elsewhere: start any Godot project of non-trivial size with a `SignalBus` autoload and the naming table above; add a signal only when a producer and consumer genuinely must not know each other; and keep a generated inventory. If you find yourself with hundreds of signals or handlers that must run in order, that is the signal (pun intended) to graduate to a queued bus or to give the noisy subsystem its own local mediator.

---

## 5. Autoload Chain: Initialization Order as Architecture

### The facts: eight entries, one legal order

Autoloads are Godot's global singletons: nodes registered in `project.godot` that the engine instantiates *before the main scene*, in declaration order, and that persist across every scene change. Relax Room registers eight, and the project's quick-reference card documents both the order and the reason for it — each entry's dependencies point strictly *backwards*:

```text
1. SignalBus          ← no dependencies (loaded first)
2. AppLogger          ← no dependencies
3. LocalDatabase      ← uses SignalBus, AppLogger
4. AuthManager        ← uses LocalDatabase, SignalBus
5. GameManager        ← uses SignalBus, AuthManager
6. SaveManager        ← uses SignalBus, AuthManager, GameManager
7. AudioManager       ← uses SignalBus, GameManager, SaveManager
8. PerformanceManager ← uses SignalBus, SaveManager
```

A small accounting nuance worth resolving before it confuses you: the file-layout card says `v1/scripts/autoload/` contains **7 singletons**, yet the chain has **8 entries**. Both are true — `PerformanceManager` lives in `v1/scripts/systems/` rather than the autoload folder. Godot does not require an autoload's script to live in any particular directory; registration in `project.godot` is what makes something an autoload. The folder placement is a *classification* statement (PerformanceManager is a "system" that happens to need global lifetime), and the discrepancy is a nice reminder that the authoritative list of autoloads is always `project.godot`, never a folder listing.

### The facts: what "order" means mechanically in Godot

Three engine guarantees make the chain meaningful:

1. Autoloads are added to the scene tree (as children of the root viewport) in declaration order, so their `_enter_tree()` and `_ready()` callbacks run in that order, each autoload fully readying before the next.
2. All autoloads complete `_ready()` **before the main scene's** `_ready()` runs. Scene scripts may therefore assume every autoload is initialized.
3. In any autoload's `_ready()`, all *earlier* autoloads are fully initialized; all *later* ones exist as script globals but have not run `_ready()` yet.

Guarantee 3 is the load-bearing one, and it explains the project's documented anti-pattern about `_init()` (reproduced from the project's study material):

```gdscript
# WRONG — other autoloads may not be ready
func _init() -> void:
    SignalBus.room_changed.connect(_on_room)  # SignalBus might not exist yet!

# CORRECT — _ready() guarantees all earlier autoloads are ready
func _ready() -> void:
    SignalBus.room_changed.connect(_on_room)
```

`_init()` runs at object construction, before the node enters the tree — at that moment even earlier autoloads may not be reachable through their global names. `_ready()` is the earliest point with ordering guarantees. (For the full lifecycle treatment, see [Scenes and Nodes](SCENES_AND_NODES.md) and the dedicated [Autoload Safety](AUTOLOAD_SAFETY.md) module.)

### The facts: the documented boot sequence, end to end

The chain's purpose is to make the following documented startup sequence deterministic:

```
            ┌──────────────┐
            │  APP STARTS  │
            └──────┬───────┘
                   ▼
            ┌──────────────────────┐
            │ Autoloads initialize │
            │ in declared order    │
            └──────┬───────────────┘
                   ▼
            ┌──────────────────────────┐
            │ GameManager loads the    │
            │ JSON catalogs: rooms,    │
            │ decorations, characters, │
            │ tracks                   │
            └──────┬───────────────────┘
                   ▼
            ┌──────────────────────────┐
            │ SaveManager loads        │
            │ save_data.json           │
            │ (migrating if needed)    │
            │ and updates GameManager  │
            │ state                    │
            └──────┬───────────────────┘
                   ▼
            ┌──────────────────────────┐
            │ load_completed emitted   │
            └──────┬───────────────────┘
        ┌──────────┼──────────────────┐
        ▼          ▼                  ▼
 AudioManager  PerformanceManager  GameManager
 restores      restores window     emits room_changed,
 music state,  position            character_changed
 starts music
                   │
                   ▼
            ┌──────────────────────────┐
            │ main menu scene          │
            │ (player sees the menu)   │
            └──────┬───────────────────┘
                   │  player starts / loads a game
                   ▼
            ┌──────────────────────────┐
            │ room scene:              │
            │ room + character + HUD   │
            └──────────────────────────┘
```

Read the sequence against the chain and every arrow is explained: catalogs before save (the save references catalog IDs), save before restoration (there must be state to restore), `load_completed` as the rendezvous point that converts *initialization order* into *event order*, and only then a scene for the player. Note also what the sequence implies about scene independence: by the time `main_menu` exists, every autoload is a settled fact — which is why scene scripts may freely reference `GameManager` or `SignalBus` in their `_ready()` without defensive checks.

### Analysis: reading the chain as a topological sort

The chain is a **topological sort of the dependency graph** — and drawing the graph makes the design decisions visible:

```
   SignalBus     AppLogger
      │  ▲          ▲
      │  └───┐      │
      ▼      │      │
  LocalDatabase ────┘        (LocalDatabase uses SignalBus + AppLogger)
      │
      ▼
  AuthManager ◄──── SignalBus (uses LocalDatabase + SignalBus)
      │
      ▼
  GameManager       (uses SignalBus + AuthManager)
      │
      ▼
  SaveManager       (uses SignalBus + AuthManager + GameManager)
      │      │
      ▼      ▼
AudioManager PerformanceManager
(uses GameManager   (uses SignalBus
 + SaveManager       + SaveManager)
 + SignalBus)
```

Observations a reviewer would write in the margin:

- **The two roots are infrastructure.** SignalBus (communication) and AppLogger (observability) depend on nothing and everything may depend on them. Putting logging second means every subsequent autoload can log its own initialization — which is precisely when initialization bugs need logging.
- **Storage precedes identity precedes content precedes state.** LocalDatabase (3) must open before AuthManager (4) can look up accounts; AuthManager must know *who is playing* before GameManager (5) sets up content and before SaveManager (6) can load *that user's* save. This ordering encodes a genuine domain rule: **whose data is it?** is a question that must be answerable before any data is loaded.
- **Consumers of restored state come last.** AudioManager (7) needs GameManager's track catalog *and* SaveManager's restored music state (which track, playing or paused) to resume where the player left off. PerformanceManager (8) needs SaveManager's restored settings (e.g., the saved window position) before it can apply them. Both are pure downstream consumers — nothing depends on them, so they close the chain.
- **The graph is a DAG with depth 6 and no cycles.** No autoload depends on a later one. The moment you are tempted to make GameManager call into AudioManager, the bus absorbs the temptation: GameManager emits, AudioManager listens, and the *initialization* graph stays acyclic even though the *runtime* communication graph is rich.

### Analysis: what breaks under each reordering

The strongest way to prove an order matters is to break it mentally, entry by entry. This is also Exercise 3.

| Illegal reordering | First failure | Failure character |
|--------------------|---------------|-------------------|
| SignalBus anywhere but first | The next autoload that calls `SignalBus.<signal>.connect(...)` in `_ready()` dies on a nil global | Immediate, loud crash at boot — the "good" kind of failure |
| AppLogger after LocalDatabase | LocalDatabase's startup (opening `cozy_room.db`, WAL setup, table creation) runs unlogged; a corrupt-DB failure at first launch becomes undiagnosable | **Silent** degradation — the worst kind: nothing crashes, evidence just never exists |
| AuthManager before LocalDatabase | Auth cannot read the accounts storage during its own `_ready()`; guest/registered resolution happens against a database that isn't open | Crash or, worse, auth "succeeds" into an empty state and the wrong profile loads |
| SaveManager before GameManager | The save file references catalog IDs (`current_room_id`, decoration `item_id`s, track indexes) that cannot be resolved because catalogs aren't loaded; restored state dangles | Partial boot: app runs but the room is empty / defaults everywhere — data *looks* lost |
| AudioManager before SaveManager | Music starts from defaults, then restored state arrives with nobody re-reading it — the saved track/volume silently ignored | Papercut bug users report as "it forgets my music" |
| PerformanceManager before SaveManager | Window position/settings restore has nothing to apply; window opens at defaults | Cosmetic — which is why PerformanceManager is safe to keep last |

The failure *characters* matter more than the specific rows. Ordering bugs come in three grades — loud crash, silent data loss, cosmetic papercut — and a good chain design pushes as many potential failures as possible toward the loud end (fail fast) and orders the fragile, data-touching systems early so their failures happen before user-visible state exists.

> ⚠️ **Pitfall** — The subtlest ordering hazard isn't in the chain itself but in *signal emission at boot*. If GameManager emits `room_changed` from its `_ready()`, autoloads later in the chain haven't connected yet (they connect in their own `_ready()`), and scene scripts *definitely* haven't. Emitting during `_ready()` therefore reaches only earlier-loading listeners. The project's documented boot sequence handles this correctly: it is **SaveManager's `load_completed`** — emitted after the whole chain is up — that triggers AudioManager, PerformanceManager and the scene layer to restore state, rather than each system broadcasting blindly during its own `_ready()`. A boot-completion signal is the standard cure for boot-time emission races.

### Analysis: enforcing the chain — beyond convention

The chain lives in `project.godot`, which the engine executes — but nothing stops a future edit from reordering it by accident, and the resulting failures range from loud to silent (see the table above). Two cheap hardening techniques close that gap. The first is a **boot assertion**: each autoload states its own dependencies as executable checks, converting every silent-reorder failure into a loud, labeled one:

```gdscript
## ILLUSTRATIVE — dependency assertions at the top of an autoload's _ready()
func _ready() -> void:
    assert(SignalBus != null, "AuthManager requires SignalBus earlier in the autoload order")
    assert(LocalDatabase.is_open(), "AuthManager requires LocalDatabase opened first")
    # ...actual initialization follows
```

Assertions compile out of release builds, so the cost is zero for players and the payoff — a named contract at the exact failure point — lands where it matters, in development. The second technique is documenting the order *next to the mechanism*: a comment block in `project.godot`'s `[autoload]` section (or the quick-reference card the project actually keeps) that states each entry's dependencies, so the person editing the order is looking at the reasons while they edit.

Worth knowing as a contrast: larger Godot projects sometimes abandon autoload-order-as-initialization entirely and use an **orchestrator** — a boot scene whose script explicitly initializes services in code (`await database.open()`, then `auth.resolve_identity()`, then...), gaining async steps, progress UI, and failure handling at the cost of writing the sequencing by hand. Relax Room's needs (fast local boot, no network in the path) don't justify that machinery; the declaration order plus a completion signal is the right-sized solution. Know both shapes and pick by boot complexity.

### The why: why singletons at all?

Godot's autoload mechanism is the engine's blessed singleton implementation, and singletons have a deservedly mixed reputation — global state, hidden dependencies, test unfriendliness. Why does this architecture lean on eight of them and get away with it?

Because each autoload here satisfies the two classical criteria for a *justified* singleton: (1) the concept is genuinely unique per process — there is one event bus, one open database, one authenticated user, one audio pipeline, one performance governor; and (2) the lifetime genuinely spans all scenes — a scene change from menu to room must not silence the music or close the database. Where the criteria don't hold, the project notably does *not* use an autoload: `PanelManager` (Section 8) manages panels *within* the room scene, so it is created by the scene, not registered globally. That restraint — "global lifetime only for global concepts" — is the discipline that separates an autoload architecture from an autoload dumping ground.

The remaining singleton cost, hidden dependencies, is paid down in two ways: the bus rule (systems communicate via signals, so autoloads rarely call each other's methods) and the documented dependency card (the chain above), which makes the hidden dependencies un-hidden.

### Generalized lesson: initialization as a first-class design artifact

Every nontrivial system — game, server, mobile app — has a boot sequence, and most teams let it accrete instead of designing it. The transferable practice from Relax Room is to treat startup as an explicitly ordered dependency graph and to *write it down next to the code that enforces it*. In other ecosystems the same idea appears as dependency-injection containers resolving construction order automatically (Spring, .NET Host), as `systemd` unit dependencies, as Kubernetes init containers, or as an app-delegate checklist. The bar to clear is the same everywhere:

1. **The order is derivable** — each component's dependencies are stated, so the sequence isn't folklore.
2. **The order is enforced** — the mechanism (here, `project.godot` autoload order) actually runs it that way; a comment cannot drift from a config that the engine executes.
3. **Boot completion is signaled** — downstream consumers key off an explicit "system is up" event (`load_completed`) rather than racing the boot.
4. **Failures at boot are loud and logged** — which is why observability (AppLogger) loads second, not last.

How you would apply this elsewhere: in any new Godot project, before writing your third autoload, draw the dependency DAG on paper and re-order `project.godot` to match a topological sort. If you cannot draw the DAG without cycles, your autoloads are entangled and the bus (or a merge of responsibilities) should fix it *before* the boot bugs arrive.

---

## 6. Catalog-Driven Content Design

### The facts: four catalogs define all content

Every piece of game content — rooms, decorations, characters, music tracks — is defined in JSON files under `v1/data/`, not hardcoded in scripts. At startup, GameManager (autoload 5) loads each file into an in-memory catalog:

```
v1/data/rooms.json        ─────►  GameManager.rooms_catalog
v1/data/decorations.json  ─────►  GameManager.decorations_catalog
v1/data/characters.json   ─────►  GameManager.characters_catalog
v1/data/tracks.json       ─────►  GameManager.tracks_catalog
```

The current inventory: **69 decorations in 11 categories** (`decorations.json`), a character catalog with sprites and animation metadata (`characters.json`), a room catalog of themes and color palettes (`rooms.json`), and the music track list (`tracks.json`). A documented sample entry from `decorations.json`:

```json
{
  "id": "lamp_desk_01",
  "name": "Desk Lamp",
  "category": "accessories",
  "sprite_path": "res://assets/sprites/decorations/...",
  "scale": 6.0,
  "placement": "floor"
}
```

The UI is built *from* these catalogs at runtime: the shop panel reads `decorations_catalog` and generates its item grid dynamically — one button per entry, grouped by `category`. When the player drags an item into the room, the drop logic reads `sprite_path` and `scale` to construct the sprite, and `placement` to validate the drop zone (wall items on the wall region, floor items on the floor region). Adding a decoration to the game is therefore a two-step, zero-code operation: add a JSON entry, drop a sprite file in the assets folder.

### Analysis: the schema conventions, field by field

The sample entry is only six fields, but each encodes a real design convention worth naming:

| Field | Convention it encodes | What it buys |
|-------|----------------------|--------------|
| `id` | **Stable, human-readable, machine-oriented key** (`lamp_desk_01`) — never displayed, never translated, never renamed | Save files and the SQLite mirror reference decorations by `id`; display names can change freely without breaking saves. The `_01` suffix leaves room for variants |
| `name` | **Display string, separate from identity** | Localizable (the bus even has `language_changed`); marketing can rename items with zero data migration |
| `category` | **Flat single-category taxonomy** (11 categories) | Drives shop grouping with trivial code; the flatness is a scope decision — no tag system, no hierarchy, because 69 items don't need one |
| `sprite_path` | **Indirection to the asset, `res://`-rooted** | The catalog is the single place that binds content identity to asset location; moving art means editing data, not code |
| `scale` | **Per-item presentation parameter in data** | Art assets need not be pre-scaled to a uniform size; the catalog adapts each sprite to the room's pixel grid |
| `placement` | **Behavioral rule expressed as data** (`floor` vs wall) | Drop validation reads the rule; a designer can reclassify an item without touching validation code |

The deepest of these is the **id/name split**. The moment persisted data (saves, database rows) references content, content identity becomes an API with backward-compatibility obligations. Relax Room gets this right from the first field: `item_id` in the save file's decorations array (Section 10's format shows it) points to `id` in the catalog. The project's documented anti-pattern list drives the same point from the code side — logic must key off catalog data, not display strings:

```gdscript
# WRONG — breaks if the character is renamed
if character_name == "male_brown_hair":
    speed = 120

# CORRECT — read from the catalog, with a default
var char_data: Dictionary = GameManager.character_catalog.get(character_id, {})
var speed: int = char_data.get("speed", Constants.DEFAULT_SPEED)
```

Note the second half of that documented snippet: `.get()` with a fallback to a named constant. That is the project's validation posture in miniature — **fail-soft with defaults** at every read site, rather than fail-fast schema validation at load time.

### Analysis: the validation trade-off — fail-soft vs fail-fast

Catalog data is code that nobody compiles, so *something* must stand in for the compiler. There are two schools:

- **Fail-fast**: validate the whole catalog at load time against a schema (required fields, types, value ranges, referential rules like "sprite_path exists"), refuse to boot on violations. Errors surface at development time, at the cost of writing and maintaining a validator.
- **Fail-soft**: read defensively at each use site (`.get(key, default)`), so a malformed entry degrades gracefully — a decoration with a broken scale renders at the default rather than crashing the room. Errors surface late, sometimes as visual oddities, but a typo in one of 69 entries can never take down the app.

Relax Room's documented posture is fail-soft, and for this project it is defensible: catalogs ship inside the game (`res://`), authored by the same tiny team that writes the code, so malformed data is caught by the author seeing a wrong-looking room within minutes. The calculus flips the moment *anyone else* authors catalog data — modders, a content designer, a second team — because fail-soft then converts their typos into mystery bugs reported weeks later. The mature endpoint most studios reach is both: a fail-fast validation pass in development/CI (even a 50-line GDScript that walks the catalog and asserts required fields) plus fail-soft reads in production as a last line of defense.

```gdscript
## ILLUSTRATIVE — a minimal fail-fast catalog check, run at startup in debug builds
const REQUIRED_FIELDS: Array[String] = ["id", "name", "category", "sprite_path", "scale", "placement"]

func validate_decorations(catalog: Array) -> PackedStringArray:
    var errors := PackedStringArray()
    var seen_ids := {}
    for entry: Dictionary in catalog:
        for field in REQUIRED_FIELDS:
            if not entry.has(field):
                errors.append("%s: missing '%s'" % [entry.get("id", "<no id>"), field])
        var id: String = entry.get("id", "")
        if seen_ids.has(id):
            errors.append("duplicate id '%s'" % id)
        seen_ids[id] = true
        if not ResourceLoader.exists(entry.get("sprite_path", "")):
            errors.append("%s: sprite not found" % id)
    return errors
```

> ✅ **Best practice** — Decide your validation posture *per audience*, not per project. Data authored by the code's own authors can be fail-soft; data authored by anyone else must be fail-fast, with error messages good enough that the author can fix it without reading your source.

### Analysis: a schema deserves a spec, even a small one

The decorations schema currently lives implicitly — in the example entries and in the code that reads them. That is workable at one author; the step up, cheap and worth taking before any second author arrives, is an explicit **schema card** per catalog. Based strictly on the documented fields:

```text
decorations.json — schema card (fields per documented example)
──────────────────────────────────────────────────────────────
id           string   REQUIRED  stable key; never rename after first release;
                                referenced by saves (item_id) and the DB mirror
name         string   REQUIRED  display only; localizable; free to change
category     string   REQUIRED  one of the 11 catalog categories; drives shop grouping
sprite_path  string   REQUIRED  res:// path; must resolve to an existing texture
scale        float    REQUIRED  presentation multiplier applied at spawn
placement    string   REQUIRED  "floor" | "wall"; enforced by DropZone validation
```

Ten minutes per catalog, and it becomes the reference for the validation pass (above), the contract for any future mod support (below), and the onboarding document for the next content author. The industry-grade version of the same idea is a machine-readable [JSON Schema](https://json-schema.org/) file per catalog, which editors can validate against as you type — heavier, and justified exactly when the authorship circle widens.

### Analysis: moddability — the door the catalog leaves open

Catalog-driven design is the single biggest determinant of whether a game is moddable, and Relax Room sits one step short of the threshold. Everything about the content pipeline is mod-shaped: content is data, data is JSON (a format every text editor opens), IDs are stable, the UI builds itself from whatever the catalog contains. What keeps it non-moddable today is a single fact: the catalogs live in `res://`, which is packed inside the exported binary — players cannot edit them.

The generalized upgrade path (a design discussion, not a project fact) is the standard **override-directory pattern**: at startup, after loading `res://data/decorations.json`, check for `user://mods/decorations.json` and merge entries by `id` — user entries adding new items or overriding shipped ones. Sprite paths in user catalogs would point into `user://mods/` and load via `Image.load_from_file()` + `ImageTexture.create_from_image()` (runtime loading, since `load()` on `res://` paths only sees packed resources). The entire mod system would be perhaps a hundred lines — *because* the catalog architecture already did the hard part. Compare the cost of retrofitting moddability onto hardcoded content: every item constant, every `match` on item names, every hand-built shop button would need rework.

Industry experience is unambiguous about the payoff: games with healthy mod ecosystems live far beyond their content budget, and data-driven content pipelines are the enabling investment. Even if Relax Room never ships mod support, the same property pays off internally — the 118→69 catalog contraction (Section 2) was possible *as a data edit*, no code review required.

The loader side of the contract is deliberately boring — one function per catalog, one place where the file format is known (**ILLUSTRATIVE**):

```gdscript
## ILLUSTRATIVE — the catalog-loader shape inside a GameManager
var decorations_catalog: Array = []

func _load_catalog(path: String) -> Array:
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        AppLogger_log_error("catalog missing: %s" % path)
        return []
    var parsed: Variant = JSON.parse_string(file.get_as_text())
    if parsed == null or not parsed is Array:
        AppLogger_log_error("catalog malformed: %s" % path)
        return []
    return parsed

func _ready() -> void:
    decorations_catalog = _load_catalog("res://data/decorations.json")
    # rooms, characters, tracks follow the same one-liner shape
```

Note the two failure branches return an empty catalog and log, rather than crashing — the fail-soft posture again, applied at the load boundary. A debug-build call into the validator from the previous snippet would complete the picture.

### The why: iteration speed is the real product

It is tempting to file catalogs under "clean code", but the industrial motivation is more concrete: **iteration speed**. Data-driven design became standard in the industry precisely because rebuilding and redeploying a game to tweak content is ruinously slow, and because it lets non-programmers author content safely. For Relax Room the numbers are small but the principle is identical: 69 decorations hand-coded as scenes or constants would make every content tweak a code change, every code change a review, every review a delay. As data, the marginal cost of a content change approaches the cost of typing it.

There is a boundary to respect, and the project respects it: **content in data, behavior in code**. The catalog says a lamp exists, where its sprite is, and that it belongs on the floor; the *rules* of dragging, snapping, overlap rejection and saving live in GDScript. Projects that blur this line — embedding scripts or expression languages inside their data files — eventually rebuild a worse programming language inside JSON. If a catalog field starts wanting an `if`, that logic belongs back in code, selected by a data flag.

### Generalized lesson: the catalog is a contract

Strip the Godot away and the pattern is: **an inventory of typed records, keyed by stable IDs, that code interprets but never enumerates**. You will meet it as product catalogs in e-commerce, feature-flag configs, level definitions, card databases in CCGs, and CMS content models. The transferable checklist:

1. Stable ID, separate from display name, never reused after deletion.
2. Every persisted reference points at the ID, so content renames are free and content *deletions* are explicit migrations (what happens to a save referencing a removed decoration? Section 10's migration chain is the answer).
3. A single loader owns parsing and (ideally) validation; everything else consumes the in-memory catalog, never the file.
4. The UI enumerates the catalog; the catalog never enumerates the UI.
5. Decide deliberately where the files live, because that decision *is* your moddability policy.

---

## 7. Scene Hierarchy: Menu and Room

### The facts: the main menu tree

The project's documented main-menu scene (`v1/scenes/menu/`):

```
MainMenu (Node2D)
│
├── ForestBackground (Node2D, window_background.gd)
│   └── 8 Sprite2D layers with parallax scrolling —
│       each layer moves at a different speed,
│       creating the illusion of depth
│
├── MenuCharacter (Node2D, menu_character.gd)
│   └── Sprite2D playing a walk-in animation:
│       a randomly selected character walks across the screen
│       (Timer for frame animation + Tween for movement)
│
├── LoadingScreen (ColorRect)
│   └── Full-screen overlay that fades out once loading completes
│
└── UILayer (CanvasLayer, layer = 10)
    └── ButtonContainer (VBoxContainer)
        ├── NuovaPartitaBtn   → starts a new game
        ├── CaricaPartitaBtn  → loads the saved game
        ├── OpzioniBtn        → opens settings
        └── EsciBtn           → quits
```

The menu tree also hosts the entry point to the auth screen (the menu scripts folder, `v1/scripts/menu/`, is documented as containing "main menu, auth screen, walk-in character") — authentication is a menu-plane concern, resolved before the room ever loads.

### The facts: the room (gameplay) tree

```
Main (Node2D, main.gd)
│
├── WallRect  (ColorRect) ── top 40% of the screen
├── FloorRect (ColorRect) ── bottom 60% of the screen
├── Baseboard (ColorRect) ── 2px horizontal divider
│
│     The room is NOT a pre-made image. It is built from two
│     colored rectangles whose colors come from the theme
│     palette in rooms.json
│
├── Room (Node2D, room_base.gd)
│   ├── Decorations (Node2D)
│   │   └── [dynamically spawned Sprite2D nodes]
│   │       each carrying decoration_system.gd for drag interaction
│   ├── Character (CharacterBody2D)
│   │   └── instanced from the character scene;
│   │       character_controller.gd handles WASD movement,
│   │       AnimatedSprite2D plays walk/idle animations
│   └── RoomBounds (StaticBody2D)
│       └── 4 CollisionShape2D forming invisible walls
│           that keep the character on screen
│
├── UILayer (CanvasLayer, layer = 10)
│   ├── DropZone (Control, full rect)
│   │   └── drag-and-drop target for decorations:
│   │       validates placement (wall vs floor zones),
│   │       rejects excessive overlap with existing items
│   └── HUD (HBoxContainer)
│       ├── MusicButton    → toggles the music panel
│       ├── DecoButton     → toggles the decoration panel
│       ├── SettingsButton → toggles the settings panel
│       └── ShopButton     → toggles the shop panel
│
├── PanelManager (Node, created programmatically)
│   └── owns the panel lifecycle (Section 8)
│
└── AudioStreams (Node)
    └── container for AudioStreamPlayer nodes
```

### Analysis: what the trees teach about composition

**The room is procedural, not painted.** The most surprising documented fact in the gameplay tree: the room itself is two `ColorRect`s and a 2-pixel baseboard, tinted from the palette in `rooms.json`. No room artwork exists at all. Weigh the trade: what was given up is artistic ceiling — a hand-painted room will always look richer than two flat rectangles. What was bought is that *every room theme is a data entry* — 4 rooms with 10 themes, per the content inventory, at the cost of a few color values each — plus perfect consistency with the catalog-driven philosophy (Section 6) and zero texture memory for the largest visual element in the app. For a product whose pillar is "personalization", many cheap themes beat one expensive painting. This is the kind of decision that looks like laziness and is actually strategy — and it is reversible: because theming flows from `rooms.json`, a future artist could add a `background_texture` field without disturbing the architecture. (The project's [Tiles and Tilemaps](TILES_AND_TILEMAPS.md) module explicitly compares this approach with a TileMap-based room it chose not to build.)

**Physics only where physics pays.** The character is a `CharacterBody2D` — Godot's kinematic body for *script-driven* movement — rather than a `RigidBody2D`, because a cozy room character must go exactly where input says, not where a physics solver settles. `move_and_slide()` gives collision response against `RoomBounds` for free. And `RoomBounds` itself is the smallest possible use of the physics server: four static collision shapes as invisible walls. No decoration has a collider; overlap rejection for decorations is done geometrically in the DropZone, not with physics queries. The pattern: **each subsystem is engaged at the minimum level that solves the problem**.

**The UI lives on a `CanvasLayer` (layer 10) in both scenes.** A `CanvasLayer` renders its children in screen space, immune to any camera or world transform, and the explicit `layer = 10` puts UI decisively above world content. Both scenes use the same layer number — a small convention, but conventions repeated across scenes are how a codebase stays predictable. The DropZone — a full-rect `Control` on the UI layer — is a subtle piece of design: drag-and-drop is *UI-plane* interaction that produces *world-plane* consequences, and the scene tree mirrors that by hosting the validator in the UI layer while the spawned decoration sprites land in `Room/Decorations`.

**Dynamic children are quarantined under dedicated containers.** Spawned decorations go under `Decorations (Node2D)`; audio players under `AudioStreams (Node)`; panels under the UI layer, managed by PanelManager. Nothing dynamic is ever a direct child of the scene root. This container discipline is what keeps programmatic node creation manageable: cleanup is "free the container's children", z-ordering is scoped per container, and a glance at the remote scene tree during debugging tells you instantly which subsystem spawned what.

> ✅ **Best practice** — Reserve a named container node for every category of runtime-spawned children. `get_tree().current_scene.add_child(thing)` is how scene trees decay into soup.

**Menu polish is architecture-free.** The menu's parallax background (8 sprite layers at different scroll speeds) and the walk-in character (random character choice, Timer-driven frames, Tween-driven movement) are pure presentation: they read the character catalog but write nothing, emit nothing, and persist nothing. Keeping delight features consequence-free means they can be modified — or cut — without any architectural review. See [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) for the parallax and tween mechanics.

### Inside the room: the decoration interaction loop

The decoration system is the core gameplay mechanic, and its documented interaction grammar is worth studying as UX-as-architecture:

```
Player opens the shop panel
        │
        ▼
Shop builds its grid from decorations_catalog
(each item shows sprite, name, category)
        │
        ▼
Player drags an item from the shop
        │
        ▼
DropZone._can_drop_data() validates continuously during the drag:
  - is the drag payload valid?
  - is the position in the correct zone (wall items on wall, floor on floor)?
  - does it overlap too much with existing decorations?
        │
        ▼
DropZone._drop_data() places the item:
  - creates a Sprite2D with the decoration's texture
  - attaches decoration_system.gd for interaction
  - emits decoration_placed
  - SaveManager records the change
        │
        ▼
In the room, thereafter:
  - left-click + drag  → move the decoration
  - right-click        → remove it
  - both actions trigger a save
```

Two design readings. First, the **input grammar is two gestures** — drag to move, right-click to remove — with no context menus, no confirmation dialogs, no mode toggles required for the basic loop. That is the "low friction" pillar implemented at the interaction level: the cost of experimenting with your room is as close to zero as a mouse allows. The richer manipulations (rotation, scale, selection) arrive through the Decorations signal domain's edit mode (`decoration_mode_changed` gates them), keeping the advanced grammar out of the basic gesture set. Layered input grammars — trivial core, opt-in depth — are how companion software stays calm.

Second, the **validation is native to the engine's drag-and-drop contract**. Godot's Control-based `_can_drop_data()` / `_drop_data()` pair gives the DropZone a continuous veto during the drag (the cursor itself can show validity) and a single commit point on release. Placement rules — zone matching against the catalog's `placement` field, overlap rejection — live in exactly one script, on the boundary, before any event is emitted. The wall/floor zone check is also a quiet piece of data-code cooperation: the *rule* ("wall items go on walls") is code; *which* items are wall items is catalog data (Section 6). Reclassifying a decoration never touches the validator.

On the receiving side of `decoration_placed`, the renderer's job is a direct transcription of the catalog contract (**ILLUSTRATIVE**):

```gdscript
## ILLUSTRATIVE — the decoration-spawn shape on the listener side
func _on_decoration_placed(item_data: Dictionary, pos: Vector2) -> void:
    var sprite := Sprite2D.new()
    sprite.texture = load(item_data.get("sprite_path", ""))
    sprite.position = pos                                  # already snapped at source
    sprite.scale = Vector2.ONE * float(item_data.get("scale", 1.0))
    sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
    sprite.set_script(preload("res://scripts/rooms/decoration_system.gd"))
    _decorations_container.add_child(sprite)               # quarantined container
    _placed_decorations.append(sprite)                     # tracked for cleanup
```

Every line echoes an earlier section: the position arrives pre-snapped (canonicalize once — Section 9), the scale and sprite path come from catalog data (Section 6), the nearest filter keeps the pixels crisp (Section 13), and the new node lands in its dedicated container, tracked for `_exit_tree()` cleanup — the documented memory-leak critical point.

### Inside the room: character movement in four lines of design

The documented movement system is deliberately minimal: WASD/arrow input becomes a direction vector, `velocity = direction * SPEED`, `move_and_slide()` resolves collisions against `RoomBounds`, and an `_update_animation()` step maps the direction vector to one of 8 directional animations, using horizontal flipping to halve the sprite work for left/right symmetry.

The instructive part is what is *absent*: no acceleration curves, no pathfinding, no physics forces, no jump. A cozy room character is a presence, not a platformer protagonist — movement exists so the room feels inhabited, and every omitted feature is friction that stayed unshipped. The horizontal-flip trick, meanwhile, is a classic pixel-art economy: 8 logical directions from a smaller set of authored animations, with `flip_h` covering the mirrored half. Multiply that saving across 3 playable characters and the spritesheet budget shrinks visibly (see [Sprites and Textures](SPRITES_AND_TEXTURES.md) for the frame mechanics).

### Inside the room: the audio pipeline and the crossfade

AudioManager (autoload 7) implements the documented **dual-player crossfade**:

```
Player A ────────╲
                  ╲──── output
Player B ────────╱
                 ╱
        crossfade Tween

Changing tracks:
1. the new track loads into the INACTIVE player
2. a Tween fades the active player's volume down to -80 dB
3. simultaneously the inactive player's volume fades up
4. when the tween completes, active/inactive references swap
```

This is double buffering, transplanted to audio: two `AudioStreamPlayer`s alternate between "front" (audible) and "back" (loading) roles, so a track change is a smooth handoff instead of a gap. The -80 dB floor is the idiomatic Godot "silence" — the volume scale is logarithmic decibels, where -80 dB is effectively inaudible — and tweening in dB space keeps the fade perceptually even. The reference swap at the end is the pattern's one bug magnet: if a second track change arrives mid-fade, the naive implementation fades the wrong player or leaks a running tween — the same animation-vs-lifetime discipline the panel system needs (Section 8). Robust implementations kill the in-flight tween before starting a new fade.

**Ambience runs on a separate, simpler architecture**: multiple independent `AudioStreamPlayer` nodes (rain, thunder, birds — per the documented examples), each toggled individually from the music panel via `ambience_toggled`, all playable simultaneously. No crossfade needed, because ambience layers are *additive* — the design insight being that music and ambience have different mixing semantics (exclusive vs additive) and therefore deserve different machinery rather than one generalized system. The `AudioStreams` container node in the room tree quarantines all of it, per the container discipline above.

### Generalized lesson: a scene is a component with a public shape

Transferable rules visible in these two trees: name nodes by role (`DropZone`, `RoomBounds`, `UILayer`), not by type; give every plane of the app (world, UI, audio, dynamic content) its own subtree; keep screen-space UI on `CanvasLayer`s with project-wide layer conventions; and let each scene be *self-describing* — a reader who has never seen the code can reconstruct most of the app's behavior from the tree plus node names, which is exactly what you just did. In React/Vue terms, a Godot scene is a component: its tree is the render output, its script is the controller, and its signals are its emitted events. Design scene boundaries the way you would design component APIs — around ownership of state, not around visual grouping.

---

## 8. PanelManager and the UI Lifecycle

### The facts: one manager, four panels, one open at a time

The four in-room panels — Music, Decorations, Settings, Shop — share a single documented lifecycle owned by `PanelManager` (a plain `Node` created programmatically by the room scene, living in `v1/scripts/ui/` alongside the panel scripts):

```
HUD button click
       │
       ▼
PanelManager.toggle_panel(name)
       │
       ├── Is another panel open?
       │      YES → close it (fade out + queue_free)
       │
       ├── Is THIS panel already open?
       │      YES → close it (toggle behavior)
       │
       └── Open the requested panel:
             1. instantiate the panel scene
             2. set modulate.a = 0 (transparent)
             3. add it to UILayer
             4. tween alpha 0 → 1
             5. emit panel_opened
```

Three documented policies define the system: **only one panel open at a time**; **fade transitions via Tween**; and **panels are instantiated and destroyed, not hidden**. Each panel is a `PanelContainer` whose contents are built programmatically in a `_build_ui()` function rather than authored as `.tscn` content — a deliberate choice, per the project docs, so that panels can build themselves from catalogs (the shop panel generates its grid from `decorations_catalog`). The bus signals `panel_opened` / `panel_closed` announce lifecycle changes to anyone interested, and the documented anti-pattern list forbids creating panels outside the manager:

```gdscript
# WRONG — creates a "wild" panel PanelManager doesn't know about
var panel = preload("res://scenes/ui/settings.tscn").instantiate()
add_child(panel)

# CORRECT — only PanelManager manages panels
SignalBus.panel_opened.emit("settings")
# PanelManager reacts to the signal and creates the panel
```

### Analysis: instantiate-and-destroy vs hide — the real trade-off

Whether to destroy closed UI or merely hide it is one of the classic small decisions that reveals a team's priorities. Weigh Relax Room's choice:

| Dimension | Destroy on close (chosen) | Hide on close |
|-----------|---------------------------|---------------|
| Memory | Only the open panel exists — matters for an always-running companion app | All panels resident forever |
| State staleness | Impossible: every open rebuilds from current catalogs and save state | Panel shows stale data unless every panel subscribes to every relevant change signal |
| Reopen latency | Pay instantiation + `_build_ui()` each open | Instant |
| Lifecycle bugs | Narrow window: bugs concentrate in open/close edges (tweens outliving nodes) | Broad surface: hidden panels still process, hold connections, leak listeners |
| Transient UI state (scroll position, selected tab) | Lost on close | Preserved |

For four lightweight panels in a memory-conscious app, destroy-on-close is the right side of every row that matters. The stale-state row is the decisive one and deserves emphasis: a *hidden* shop panel would need to listen for catalog and coin changes to stay correct, multiplying bus connections; a *rebuilt* shop panel is correct by construction. Rebuild-on-open is the UI equivalent of "stateless request handling" — correctness through regeneration rather than through synchronization. The known cost, transient UI state loss, is negligible for panels this small; the moment a panel grows tabs and scroll positions worth preserving, the design would need a small "remember my state" dictionary handed to `_build_ui()` — an extension, not a rewrite.

The **exclusive-panel policy** (one open at a time) is likewise a product decision wearing an engineering hat: it eliminates the entire class of panel-stacking problems — z-order wars, focus ambiguity, two panels editing the same state — and matches the calm, low-friction product pillars. Window-manager UIs are for tools; modal-ish exclusive surfaces are for companions.

The **wild panel prohibition** is the manager's real payload. The invariants "at most one panel" and "every open is announced on the bus" are only true if *every* code path goes through the manager. One rogue `instantiate()` breaks both silently. This is the Manager pattern's essence: an invariant is only as strong as the narrowest chokepoint that enforces it.

> ⚠️ **Pitfall** — Fade-out plus `queue_free()` is a classic tween-lifetime trap. The close animation must complete *before* the node dies, so the free must be sequenced after the tween (e.g., `tween.finished` → `queue_free()`); and a panel force-closed mid-fade-in needs its running tween killed first, or the dying tween writes to a freed node. The project's own glossary flags exactly this discipline ("a Tween must always be tracked and killed in `_exit_tree`"). Whenever an animation and a lifetime overlap, one must own the other.

The whole documented policy compresses into a readable skeleton (**ILLUSTRATIVE**):

```gdscript
## ILLUSTRATIVE — the PanelManager shape implied by the documented lifecycle
extends Node

var _current_panel: Control = null
var _current_name: String = ""

func toggle_panel(panel_name: String) -> void:
    var reopening_same := (panel_name == _current_name)
    if _current_panel != null:
        _close_current()                    # exclusive policy: at most one panel
    if reopening_same:
        return                              # toggle behavior: second press closes
    _open(panel_name)

func _open(panel_name: String) -> void:
    var panel: Control = _panel_scene(panel_name).instantiate()
    panel.modulate.a = 0.0                  # start transparent
    _ui_layer().add_child(panel)
    create_tween().tween_property(panel, "modulate:a", 1.0, 0.2)
    _current_panel = panel
    _current_name = panel_name
    SignalBus.panel_opened.emit(panel_name)

func _close_current() -> void:
    var closing := _current_panel
    var closing_name := _current_name
    _current_panel = null
    _current_name = ""
    var tween := create_tween()
    tween.tween_property(closing, "modulate:a", 0.0, 0.2)
    tween.finished.connect(closing.queue_free)   # free only after the fade
    SignalBus.panel_closed.emit(closing_name)
```

Read the sequencing details as the analysis above predicted: the manager clears its own references *before* the fade-out starts (so a rapid re-open cannot grab a dying panel), and `queue_free()` is chained to `tween.finished` (the animation owns the lifetime). Those two lines are where naive implementations of this pattern break.

### Analysis: code-built UI — the contrarian choice

Building panel contents in `_build_ui()` instead of `.tscn` files runs against the grain of Godot culture, where the editor is the UI tool. The project's stated reason is coherent: panels are *catalog projections* — the shop's grid is `decorations_catalog` rendered as buttons — and generated content wants generating code, not a static scene that would be mostly placeholder anyway. Code-built UI also diffs cleanly in git (`.tscn` diffs are notoriously noisy) and cannot drift out of sync with the data it displays.

The honest costs: no visual preview without running the game, no designer-friendly editing, and layout tweaking (margins, anchors) through code is slower than dragging in the editor. The industry-standard middle path, worth knowing even though this project chose purity: author the static *frame* of a panel as a `.tscn` (background, title, close button, an empty `GridContainer`) and generate only the dynamic *content* into it. Frame-in-scene, content-in-code keeps the designer loop for the 80% that is static and the generative power for the 20% that is data-driven. For a solo-maintained project with no dedicated UI designer, though, all-code is a defensible simplification — one authoring workflow instead of two.

### Generalized lesson: every UI needs a lifecycle owner

Under the names *modal manager*, *navigation controller*, *router*, or *screen stack*, every mature UI codebase contains a PanelManager: a single object that owns which surfaces exist, enforces the transition policy, and announces changes as events. The failure mode it prevents is universal — surfaces spawned ad hoc from wherever, until no one can answer "what is on screen right now?". When you build one, copy Relax Room's three load-bearing properties: a **single chokepoint** (all opens/closes flow through it), an **explicit policy** (exclusive here; a stack or tabs elsewhere), and **lifecycle events on the bus** so other systems (input handling, pause logic, tutorials, analytics) can react without the manager knowing they exist.

---

## 9. The Save System: Dirty Flags and Round Trips

### The facts: the full documented round trip

The project documentation traces the complete path from a player action to persisted state. It is reproduced here — walking this trace until you can reconstruct it from memory is the single highest-value exercise in this module:

```text
USER: drags an item from the inventory panel into the room

1. InventoryPanel._on_item_drag_started(item_data)
   └── creates a drag preview (TextureRect with the item's sprite),
       temporarily added to the scene

2. DropZone._can_drop_data(position, data) → true
   └── checks the dragged data is valid (has item_id, sprite_path)
   └── checks the position falls inside the room's grid

3. DropZone._drop_data(position, data)
   └── computes the snapped position: Helpers.snap_to_grid(position)  → 64px grid
   └── emits: SignalBus.decoration_placed.emit(item_data, snapped_pos)

4. SignalBus.decoration_placed → listeners react:

   4a. DecorationSystem._on_decoration_placed(item_data, pos)
       └── creates a Sprite2D for the decoration
       └── sets position, scale, texture
       └── adds the node to the scene (child of the decorations container)
       └── updates the internal _placed_decorations array

   4b. SaveManager._on_decoration_placed(item_data, pos)
       └── sets _is_dirty = true  ("there are unsaved changes")

5. The auto-save timer (every 60 seconds) checks _is_dirty
   └── _is_dirty is true → calls save_game()

6. SaveManager.save_game()
   └── serializes ALL game state into a Dictionary
   └── writes JSON to user://save_data.json (atomic write with backup)
   └── writes to SQLite via LocalDatabase.save_room_state()
   └── sets _is_dirty = false
   └── emits: SignalBus.save_completed.emit()
```

Supporting documented facts: the save is **versioned** (currently v5.0.0 — Section 10); the JSON write is **atomic with a backup** — `user://save_data.backup.json` holds the last known-good save; quitting without saving does not lose data, because SaveManager hooks the engine's close notification (`_notification()`) to flush; and the SQLite mirror write is triggered via the `save_to_database_requested` signal. The project docs also flag the trace's three critical points: a `snap_to_grid()` rounding error puts decorations off-grid (step 3); a missing `_exit_tree()` in DecorationSystem leaks memory (step 4a); and a JSON-succeeds/SQLite-fails divergence leaves the two stores inconsistent (step 6).

### Analysis: reading the trace like an architect

**Steps 1-3 are the UI plane doing all validation before any state changes.** `_can_drop_data()` runs continuously during the drag (Godot calls it as the pointer moves) and is the *gatekeeper*: invalid payloads and out-of-zone positions never generate an event at all. By the time `decoration_placed` is emitted, the event is a *fact* — every listener may trust it without re-validating. This "validate at the boundary, trust inside" shape is precisely how good HTTP services treat request validation, and it is the reason listener 4a can be so simple.

**Step 3's snap-then-emit ordering is load-bearing.** The position is snapped to the 64px grid *before* emission, so every listener receives the same canonical coordinates. Snap inside each listener instead, and the renderer and the save file could round differently — the class of tiny divergence that surfaces months later as "my lamp moved one pixel after reload". Canonicalize once, at the source, before the fact is announced.

**Step 4's two listeners never meet.** The renderer (4a) and the persistence marker (4b) both react to the same signal, in either order, sharing nothing. You could delete SaveManager entirely and placement would still render; delete DecorationSystem and placement would still persist. That independence is the bus dividend of Section 4, made concrete.

**Steps 4b-5 are the dirty-flag pattern, and the flag is doing quiet economics.** Placing ten decorations in a minute produces ten `_is_dirty = true` writes (nine redundant, all nearly free) and *one* actual save when the 60-second timer fires. The pattern decouples *change frequency* from *write frequency*: user actions are bursty; disk writes are batched. The trade is bounded loss — a crash (not a quit: quit flushes via `_notification()`) can lose up to 60 seconds of changes. That number is a product decision disguised as a constant: for a room decorator, losing a minute is mildly annoying; for a roguelike's permadeath ledger it would be unacceptable, and the interval would shrink or go event-driven (save immediately on rare-but-precious events, batch the rest).

**Step 6 is a fan-out write with an ordering policy.** JSON first (the source of truth), then the SQLite mirror, then — only after both — `_is_dirty = false` and `save_completed`. Clearing the flag *before* the writes would be the fatal version: a write failure after a cleared flag means the system believes it is clean while the disk disagrees, and the autosave loop will never retry. Flag-clearing last makes the loop self-healing: a failed save leaves `_is_dirty` set, so the next timer tick tries again.

> ⚠️ **Pitfall** — The documented divergence risk at step 6 (JSON succeeds, SQLite fails, or vice versa) is the standing tax of every dual-write design. Relax Room contains it by hierarchy — JSON is *the* source of truth and SQLite is a rebuildable mirror — so the correct recovery from any divergence is always "regenerate the mirror from the JSON", never a merge. If your two stores are ever *peers*, dual-write without a transaction spanning both is a data-corruption generator. Section 11 develops this fully.

### Analysis: the whole discipline fits in one small shape

Pull the documented pieces together — dirty flag, autosave timer, quit hook, ordered writes — and the entire save discipline is expressible in a compact skeleton. This is the shape to internalize (**ILLUSTRATIVE** — the pattern, not the project file):

```gdscript
## ILLUSTRATIVE — the SaveManager shape implied by the documented behavior
extends Node

var _is_dirty := false

func _ready() -> void:
    # every state-mutating fact on the bus marks the save dirty
    SignalBus.decoration_placed.connect(func(_d, _p): _is_dirty = true)
    SignalBus.decoration_removed.connect(func(_id): _is_dirty = true)
    SignalBus.settings_updated.connect(func(_s): _is_dirty = true)
    # ...every other mutating signal

    var timer := Timer.new()          # the 60-second autosave pulse
    timer.wait_time = 60.0
    timer.timeout.connect(_on_autosave_tick)
    add_child(timer)
    timer.start()

func _on_autosave_tick() -> void:
    if _is_dirty:
        save_game()

func _notification(what: int) -> void:
    # the quit hook: flush before the window closes, so quitting loses nothing
    if what == NOTIFICATION_WM_CLOSE_REQUEST and _is_dirty:
        save_game()

func save_game() -> void:
    var snapshot := _serialize_all_state()          # one Dictionary, whole truth
    if _write_json_atomically(snapshot) != OK:
        return                                       # flag stays set → retry next tick
    SignalBus.save_to_database_requested.emit()      # SQLite mirror follows the primary
    _is_dirty = false                                # cleared LAST, only on success
    SignalBus.save_completed.emit()
```

Every line placement encodes a rule from the analysis above: connections in `_ready()`, the flag set by facts and cleared only after a successful write, JSON before mirror, completion announced last. When you write your own SaveManager, get this 40-line spine right first — features can hang off a correct spine, but no feature survives a wrong one.

### Analysis: the atomic write, and why the backup exists

A naive `FileAccess.open(path, WRITE)` truncates the file first and writes after — crash between those two moments, and the save is *gone*, not merely stale. The documented pattern (glossaried by the project as **Atomic Write**) is write-to-temp-then-rename: the real file is replaced only by an already-complete file, and a crash at any instant leaves either the old save or the new save on disk, never a torn half of one. Layered on top, `user://save_data.backup.json` keeps the previous known-good save even if the *content* (not the write) is bad — a serialization bug that produces syntactically valid but semantically broken JSON survives an atomic rename just fine, and the backup is the only rung left on that ladder.

```gdscript
## ILLUSTRATIVE — the atomic-write-with-backup shape
func write_save_atomically(path: String, payload: Dictionary) -> Error:
    var tmp_path := path + ".tmp"
    var f := FileAccess.open(tmp_path, FileAccess.WRITE)
    if f == null:
        return FileAccess.get_open_error()
    f.store_string(JSON.stringify(payload, "  "))
    f.close()
    # keep the previous good save as the backup, then promote the temp file
    if FileAccess.file_exists(path):
        DirAccess.copy_absolute(path, path.replace(".json", ".backup.json"))
    return DirAccess.rename_absolute(tmp_path, path)
```

The load side mirrors the ladder: try `save_data.json`; on parse failure, fall back to the backup; on double failure, start fresh rather than crash. A save system's quality is measured almost entirely by its behavior on the *bad* days.

### Generalized lesson: the dirty flag is everywhere

Nystrom catalogs **Dirty Flag** as a core optimization pattern — defer derived work until the underlying data changed *and* the result is needed — and once you know its face you see it everywhere: document editors' unsaved-changes dot, browser layout invalidation, game-engine transform caching, `git status` itself. The three design questions are always the same, and Relax Room answers each explicitly: **who sets the flag** (every state-mutating signal handler), **who clears it** (only the successful completion of `save_game()`), and **who observes it** (the 60s timer and the quit hook). When you build one, write those three answers as comments next to the flag; every dirty-flag bug in history is one of those three answers being violated by a code path someone forgot.

---

## 10. Versioned Saves and the Migration Chain

### The facts: a versioned format with a chained history

Every Relax Room save file carries its schema version as data. The project documentation preserves a complete example of the **v4.0.0** format, worth reading field by field because most of this document's threads converge in it:

```json
{
  "version": "4.0.0",
  "last_saved": "2026-03-21T15:30:00",
  "settings": {
    "language": "en",
    "display_mode": "windowed",
    "master_volume": 0.8,
    "music_volume": 0.6,
    "ambience_volume": 0.4,
    "window_pos_x": 100,
    "window_pos_y": 200
  },
  "room": {
    "current_room_id": "cozy_studio",
    "current_theme": "modern",
    "decorations": [
      {
        "item_id": "lamp_desk_01",
        "position": {"x": 400, "y": 500},
        "z_index": 5
      }
    ]
  },
  "character": {
    "character_id": "female_red_shirt",
    "outfit_id": "",
    "data": {
      "nome": "My Character",
      "genere": true,
      "livello_stress": 0
    }
  },
  "music": {
    "current_track_index": 0,
    "playlist_mode": "shuffle",
    "active_ambience": ["rain_light"]
  },
  "inventory": {
    "coins": 150,
    "capacita": 50,
    "items": [
      {"item_id": "plant_01", "quantity": 1}
    ]
  }
}
```

The documented migration history:

```
v1.0.0 → v2.0.0 → v3.0.0 → v4.0.0 → v5.0.0 (current)

v3 → v4 (the documented delta):
  - Removed: tools, therapeutic, xp, streak, currency, unlocks
  - Added:   inventory with coins, capacita, items
  - Preserved: coins carried over from the old currency section
```

Migrations are **chained**: the loader applies each step in sequence, so a v1.0.0 save from the project's earliest days passes through every migration and arrives at the current format. The current version is **v5.0.0** per the project's quick-reference card; the v4→v5 field delta is not recorded in the two documents this module draws on, so it is deliberately not described here — the *principle* (one more chained step) is what matters.

### Analysis: what the format itself teaches

- **The version is the first field, and it is a string with semver shape.** Major-version bumps have historically tracked breaking reshapes (v3→v4 restructured whole sections). A save loader's very first act must be reading this field — every other byte's meaning depends on it.
- **`last_saved` is an ISO 8601 timestamp.** Sortable as a string, unambiguous across locales, and exactly what a future cloud-sync layer needs for "which copy is newer" (Section 11). Choosing the boring standard format is the win.
- **Every content reference is an ID, never a name.** `current_room_id: "cozy_studio"`, `item_id: "lamp_desk_01"`, `character_id: "female_red_shirt"` — the catalog contract of Section 6, honored by the persistence layer. Display names appear nowhere in the save.
- **Decorations persist position and `z_index`, not sprite paths or scales.** The save records *the player's choices*; the catalog records *what things are*. Reload joins the two by `item_id`. This split is why art can be re-scaled or re-pathed in a patch without touching anyone's save.
- **The Italian field names (`nome`, `genere`, `livello_stress`, `capacita`) are fossils.** An Italian-language IFTS team's earliest schema decisions, now locked in by compatibility: renaming a persisted key is a migration, and cosmetic renames rarely justify one. Every long-lived schema accumulates these; the professional response is a documented glossary, not a churn of renames. (`livello_stress` — stress level — also fossilizes the cut wellness-feature direction of Section 2.)
- **`z_index` in the save hints at depth sorting** — the room draws decorations in a stable, player-visible order that must survive reload; see [Isometric Games](ISOMETRIC_GAMES.md) for why depth order is a first-class concern in room-based rendering.

### Analysis: why chained micro-migrations beat direct jumps

The alternative to a chain is direct migration: N versions require N-1 handwritten "old→current" converters, and every new version invalidates all of them. The chain needs exactly **one new step per version**, each written while the previous format is still fresh in the author's mind, and each older step already proven by use. The cost is that ancient saves take multiple hops — irrelevant at these sizes — and that the chain must be *tested* end-to-end, which is precisely what a fixture folder of one save file per historical version is for (see Exercise 8; note the project's test removal makes this a real gap).

```gdscript
## ILLUSTRATIVE — the chained-migration loader shape
func migrate(data: Dictionary) -> Dictionary:
    var version: String = data.get("version", "1.0.0")
    if version < "2.0.0": data = _migrate_1_to_2(data)
    if version < "3.0.0": data = _migrate_2_to_3(data)
    if version < "4.0.0": data = _migrate_3_to_4(data)
    if version < "5.0.0": data = _migrate_4_to_5(data)
    data["version"] = CURRENT_SAVE_VERSION
    return data
```

And a single step, using the documented v3→v4 delta as the concrete example:

```gdscript
## ILLUSTRATIVE — the documented v3→v4 delta expressed as one chained step
func _migrate_3_to_4(data: Dictionary) -> Dictionary:
    # preserve what has value: coins survive the currency section's deletion
    var coins: int = data.get("currency", {}).get("coins", 0)
    # delete what does not: the abandoned gamification/wellness sections
    for legacy_key in ["tools", "therapeutic", "xp", "streak", "currency", "unlocks"]:
        data.erase(legacy_key)
    # add the replacement structure
    data["inventory"] = {"coins": coins, "capacita": 50, "items": []}
    return data
```

The v3→v4 delta also demonstrates the two humane properties of a good destructive migration: **preserve what has value** (coins were carried from the deleted `currency` section — the player's earned wealth survived the feature's death) and **delete what does not** (nobody's `streak` was worth keeping in a product that renounced streaks). A migration is where engineering ethics gets concrete: it is the player's data, not yours.

> ✅ **Best practice** — Write the migration *in the same commit* that changes the schema, and never edit a shipped migration — append a new one. Shipped migrations are history, and history is append-only. This is exactly the discipline of database migration tools (Flyway, Alembic, Rails), applied to a JSON file.

### Generalized lesson: every persisted format is a contract with your past self

The moment version 1.0 reaches one real user, your save format becomes an API whose only client is *the past*. The transferable checklist: version every persisted artifact from day one (adding a version field retroactively is itself a migration — the awkward kind); prefer chained migrations written contemporaneously; keep one fixture per historical version and run the chain over all of them in CI; and treat "unknown newer version" explicitly (refuse loudly or back up and attempt — never silently truncate). Teams that skip this pay in the worst currency available: corrupted user data and support tickets that cannot be reproduced.

---

## 11. Offline-First Persistence: JSON, SQLite, Sync Queue

### The facts: three layers, one source of truth

Relax Room's persistence stack, per the project documentation:

```
Layer 1: JSON file (PRIMARY — the source of truth)
├── user://save_data.json — human-readable, versioned (v5.0.0), always works offline
├── user://save_data.backup.json — last known-good copy
├── auto-save every 60 seconds when dirty
└── flush on quit via _notification()

Layer 2: SQLite database (MIRROR)
├── user://cozy_room.db — structured relational data
├── 9 tables mirroring and structuring the app's data
├── WAL (write-ahead logging) mode
├── foreign keys for integrity
├── written via the save_to_database_requested signal
└── contains the sync_queue table

Layer 3: Supabase (CLOUD — planned, Phase 4)
├── PostgreSQL over a REST API
├── not present in the current autoload chain
└── the sync_queue exists to feed it when it arrives
```

The **sync queue** is a SQLite table that records operations performed offline, queuing them for replay against the cloud once connectivity exists; the bus reserves the `sync_started` / `sync_completed` signals for that lifecycle. The project's own glossary defines offline-first operationally: *the game works offline with JSON + SQLite; Supabase is planned for cloud sync (Phase 4)*.

### Analysis: why two local stores is not redundancy theater

A fair challenge: the JSON file already persists everything — why maintain a SQLite mirror at all? The project's documentation gives a layered answer worth unpacking:

1. **Different read patterns.** The JSON save is a *snapshot* — loaded whole at boot, written whole on save. SQLite is a *query surface* — relational lookups, aggregation, per-row updates. An inventory query ("how many items of category X does this account own?") is a `SELECT` in SQLite and a hand-rolled loop over nested dictionaries in JSON. As data grows relational — accounts owning characters owning inventories, per the AuthManager design — foreign-keyed tables with integrity enforcement earn their keep.
2. **Different failure envelopes.** A human can open, read, and hand-repair JSON with a text editor — that property has rescued more shipped games than any framework. SQLite offers transactional writes and WAL crash safety. Each store covers the other's weakness.
3. **The mirror is the cloud on-ramp.** Layer 3 is PostgreSQL — relational. Data already shaped into 9 relational tables locally is a straight mapping to cloud tables; a nested JSON blob is not. The mirror is the schema rehearsal for Phase 4, and the sync queue lives *inside it* because queue entries must commit atomically alongside the data changes they describe.

WAL mode deserves its sentence: write-ahead logging appends changes to a side journal (`.db-wal`) and folds them into the main file later, so readers never block on writers and a mid-write crash loses only the un-checkpointed tail — never the database. For a 60-second background-write cadence in an app that must never hitch the UI (performance pillar!), WAL is the correct default. [Database and Persistence](DATABASE_AND_PERSISTENCE.md) covers the mechanics in depth.

> ⚠️ **Pitfall** — Dual-store designs die by *ambiguity of authority*, not by having two stores. The one non-negotiable rule, which Relax Room states in writing: **JSON is primary**. Every reconciliation, every recovery, every "which one do I believe?" resolves in one direction. The documented step-6 divergence risk (Section 9) is survivable *only because* this rule exists. If you cannot say in one sentence which store wins, you do not have redundancy — you have a race condition with a schema.

### Analysis: why an embedded database, and not a server

The project's own FAQ addresses a question every database-trained student asks: why SQLite and not MySQL/PostgreSQL? The answer generalizes far beyond this app. SQLite is an **embedded** database: it lives in a single file in the user's data directory, inside the application's process — no server to install, no daemon to keep running, no port, no credentials, no configuration. For a desktop companion that must work offline and start in seconds, every property of a server database is a liability: an always-on process contradicts "lightweight", a setup step contradicts "low friction", and a network protocol contradicts "offline-first". The FAQ also names the boundary honestly: the moment the product needed many simultaneous remote users, an embedded file would stop sufficing — which is exactly the role the optional PostgreSQL layer (Supabase) is reserved for.

The general rule: **embedded databases for single-user local state, server databases for shared concurrent state** — and the decision is about *deployment topology*, not SQL dialect. SQLite is likely the most widely deployed database on Earth precisely because most software is, like Relax Room, one user talking to their own data.

### Analysis: offline-first as an inversion, and the sync queue's quiet sophistication

Offline-first is not "has a cache". It is an inversion of the client-server default: **the local store is the authoritative database; the network is an optimization layer**. Reads never wait on a network; writes commit locally and immediately; synchronization is a background concern that the UI never blocks on. Relax Room is structurally pure offline-first — the current build has *no network layer at all*, which is the genre-correct choice for a companion app whose pillar is "it just works": no spinner, no login wall, no degraded mode, because offline *is* the primary mode rather than the fallback.

What elevates the design is building the **sync queue before the sync**. When Phase 4 arrives, the hard problem will not be calling a REST API — it will be answering "what happened locally while we were offline?" A journal of offline operations, captured transactionally at write time, is the only reliable answer; reconstructing intent after the fact by diffing states is guesswork. By placing `sync_queue` in the schema and `sync_started`/`sync_completed` on the bus *now*, the architecture reserves the seams so that cloud sync becomes an additive feature — a new autoload that drains the queue and emits the signals — rather than a rewrite of the persistence layer.

```gdscript
## ILLUSTRATIVE — the operation-journal idea behind a sync queue
# Alongside each local write, one queue row is committed in the same transaction:
# { op: "decoration_placed", payload: {item_id, position}, ts: "2026-07-27T10:15:00Z" }
# A future sync worker drains rows in order against the cloud API,
# deleting each row only after the server acknowledges it.
```

The eventual drain loop is equally standard — the queue's whole value is that this future worker stays trivial (**ILLUSTRATIVE**, Phase 4 shape):

```gdscript
## ILLUSTRATIVE — a sync worker draining the queue when connectivity exists
func drain_sync_queue() -> void:
    SignalBus.sync_started.emit()
    while true:
        var op: Dictionary = _local_db_next_queued_operation()
        if op.is_empty():
            break
        var ok: bool = await _push_to_cloud(op)     # REST call to the cloud API
        if not ok:
            break                                    # stop; row stays queued for retry
        _local_db_delete_queued_operation(op.id)     # remove ONLY after acknowledgment
    SignalBus.sync_completed.emit()
```

The one load-bearing line is the deletion: a queue row dies only after the server acknowledges the operation. Delete-then-push loses operations on failure; push-without-delete duplicates them — which is also why real sync protocols make operations *idempotent* (safe to replay), typically by shipping an operation ID the server deduplicates on.

The deferred hard problem — deliberately out of scope until Phase 4 — is **conflict resolution**: the same account making offline changes on two machines produces divergent journals, and someone must decide (last-write-wins by timestamp? per-field merge? user prompt?). Deferring it is correct sequencing; the `last_saved` timestamp and per-operation `ts` fields are the raw material any policy will need.

### Generalized lesson: local-first is an architecture, not a feature flag

The mobile and web industries converged on the same blueprint this project follows: a local database as the on-device source of truth, a UI that reads only from it, a background sync engine decoupled from the UI, and an operation queue for offline writes. You will meet it as Android's offline-first guidance, as sync frameworks like RxDB or PowerSync, and as the "local-first software" movement's manifesto. The portable design sequence: (1) name the single source of truth in writing; (2) make every UI read local-only; (3) journal writes transactionally; (4) sync in the background with explicit lifecycle events; (5) choose a conflict policy *before* the first two-device user finds it for you. Relax Room has executed steps 1-4 and consciously scheduled step 5 — which is precisely the right shape for a project that may never need it.

---

## 12. AuthManager: Guest, Registered, Deleted

### The facts: local identity, three flows

`AuthManager` is autoload 4, dependent on LocalDatabase and SignalBus. The project documentation defines its scope in one line: it handles **guest mode**, **username + password authentication with SHA-256**, and **account deletion**. Its bus vocabulary is the five-signal Auth domain — `auth_state_changed`, `auth_error`, `account_created`, `account_deleted`, `character_deleted` — and the auth screen lives in the menu plane (`v1/scripts/menu/`), resolved before the room scene loads. Identity is a *local* concern: accounts live in the SQLite database on the user's machine; no network is involved.

Reading the architecture around those facts:

- **Guest mode is the low-friction default.** A companion app whose pillar is "just works" cannot demand registration at first launch; guest mode means the room, saves and music all function with zero ceremony. Registration exists for what it actually provides: named local profiles on a shared machine, and — come Phase 4 — an identity to attach cloud sync to.
- **The signal vocabulary is state-machine-shaped.** `auth_state_changed` (not `user_logged_in` + `user_logged_out`) models auth as one state with transitions — guest → registered, signed-in → signed-out — which is the cleaner abstraction: listeners re-read the current state rather than tracking paired events. `auth_error` separates the failure channel from the state channel, so UI error toasts don't masquerade as state transitions.
- **Deletion is granular and first-class.** `account_deleted` and `character_deleted` are distinct signals: a user can delete a character without deleting the account. That an academic project treats deletion as a designed flow — with its own signals, therefore its own listeners cleaning up dependent state — rather than an afterthought is notable; deletion is the flow most real products discover they never designed until a GDPR request arrives.
- **The chain position is forced.** AuthManager must follow LocalDatabase (accounts are rows) and precede GameManager and SaveManager (Section 5): *whose* save to load is unanswerable before identity resolves. Auth-before-content is not an ideology here; it is a data dependency.

### Analysis: walking the three flows through the bus

The Auth domain's five signals let us reconstruct how each documented flow travels the architecture. (The *flows* — guest, registration, deletion — are documented; the listener sets described here are design reading, not quoted code.)

**Guest flow.** First launch, or an explicit "play as guest": AuthManager resolves identity to a guest profile and `auth_state_changed` announces it. Everything downstream in the chain — GameManager, SaveManager — proceeds against the guest identity; the menu UI reflects the anonymous state (no profile name, an invitation to register rather than a wall). The whole point is what *doesn't* happen: no form, no error path, no network. Guest is not a degraded mode; it is the default mode.

**Registration flow.** Username and password submitted on the auth screen; AuthManager validates and writes the account through LocalDatabase. Success emits `account_created` (a data-lifecycle fact — a new account row exists) and `auth_state_changed` (an identity fact — the current player is now this account). Failure — taken username, bad input — emits `auth_error`, and only the auth screen reacts, because errors are UI concerns, not state transitions. The two-signal separation on success matters for listener economy: a future cloud layer cares that an account was *created* (something to sync); the HUD only cares *who is playing now*.

**Deletion flows.** `character_deleted` and `account_deleted` are separate facts because they are separate scopes of destruction: removing one character (and, presumably, its dependent state) versus removing the whole account. Any listener holding state keyed to the deleted entity — loaded saves, cached profile UI — reacts by cleaning up. Broadcasting deletion as a bus fact, rather than burying it in a manager method, is what allows cleanup responsibilities to stay distributed: AuthManager deletes the rows it owns and announces; every other owner of dependent state deletes its own. Centralized announcement, decentralized cleanup — the bus pattern's answer to cascading deletes above the database layer (below it, SQLite's foreign keys do the same job relationally).

### The security critique: SHA-256 is the wrong tool, and knowing why matters

Here this module must do what the course promised: treat the real project honestly. Storing passwords hashed with **plain SHA-256 is not an acceptable password-storage design**, and every reader should be able to articulate exactly why:

1. **SHA-256 is fast — that is its disqualification.** It is a general-purpose cryptographic hash engineered for throughput; commodity GPUs compute billions of SHA-256 hashes per second. An attacker with the hash of a typical human password brute-forces or dictionary-attacks it in seconds to hours. Password hashing needs functions engineered to be *slow and memory-hard*.
2. **Without per-password salts, identical passwords produce identical hashes**, enabling rainbow-table lookups and revealing which users share passwords. (The project docs record "SHA-256" without specifying salting; a fair audit must therefore flag both the fast-hash problem, which salting does not fix, and the salt question, which it might.)
3. **The industry answer is settled, not exotic.** OWASP's password-storage guidance: **Argon2id** first choice, scrypt or bcrypt as established alternatives, PBKDF2 with a high iteration count where FIPS compliance demands it. All are salted by construction and cost-tunable so hardware progress can be answered with a parameter bump.

Now the equally important other half of an honest audit — the **threat model**. This is a local, offline application: the hashes live in `user://cozy_room.db` on the user's own machine. There is no server to breach, no password database to exfiltrate at scale, and an attacker with local file access has largely won already (they can read the save data directly). Within *this* threat model, password auth is best understood as **profile separation on a shared computer** — closer to a lock on a diary than a bank vault — and SHA-256's weakness has limited practical blast radius. The design is wrong in a way that currently injures little.

But architecture is judged by its trajectory, and this is where the critique gets teeth: **Phase 4 changes the threat model**. The moment identity syncs to a cloud service, password verification and storage move to server territory, credentials transit networks, and a breach exposes every user — plus the users who (statistically, many will) reused this password elsewhere. The migration path is fortunately standard: Supabase-class platforms ship managed auth with proper hashing, so the correct Phase 4 move is to *delete* local password verification in favor of the platform's, not to harden SHA-256. And locally, an upgrade can be done without resetting anyone: verify against the old hash once, and on success immediately re-hash the password with the strong algorithm — the classic **hash-upgrade-on-login** pattern.

> ⚠️ **Pitfall** — "It's just a school project / it's only local" is how weak crypto ships to production: threat models change and code outlives its assumptions, so the cheap discipline is to use the boring correct primitive from day one. The inverse pitfall is real too: hand-rolling an Argon2 integration badly (static salt, home-grown comparison, secrets in logs) can be worse than the honest SHA-256 it replaces. The actual rule: **never design your own auth when a maintained implementation is reachable** — and when it isn't, copy OWASP's cheat sheet literally.

### Analysis: what the fix looks like in practice

The critique earns its keep only if the remedy is concrete. The upgrade has two moving parts. Structurally, verification gains a *legacy branch* that heals itself (**ILLUSTRATIVE** — pattern shape; the strong hash would come from a maintained addon or, in Phase 4, the auth platform, never hand-rolled):

```gdscript
## ILLUSTRATIVE — hash-upgrade-on-login inside a verify function
func verify_password(account: Dictionary, password: String) -> bool:
    if account.hash_scheme == "sha256":                # legacy branch
        if _sha256_hex(password) != account.password_hash:
            return false
        # correct password proven — immediately upgrade the stored hash
        account.password_hash = _strong_hash(password)  # Argon2id via addon/platform
        account.hash_scheme = "argon2id"
        _persist_account(account)
        return true
    return _strong_verify(password, account.password_hash)
```

Two details carry the design. The account record needs a `hash_scheme` field (a one-row-at-a-time migration, performed at login, rather than a big-bang rehash — which is impossible anyway, since only the user knows the password). And the legacy branch must eventually *expire*: after a chosen period, remaining SHA-256 accounts get a forced reset rather than indefinite legacy support. Operationally, the Phase 4 rule is even simpler: when a managed auth platform enters the picture, local password verification should be *deleted in its favor*, not run in parallel — two auth systems is how inconsistencies become vulnerabilities.

### Generalized lesson: identity is a dependency, not a feature

Three transferable conclusions. First, **auth sits early in every dependency chain** — Relax Room's autoload order rediscovered what every backend framework encodes as auth middleware running before handlers: identity gates data. Second, **model auth as a state machine with a separate error channel**; paired login/logout events drift, state-change events don't. Third, **guest-first onboarding with optional upgrade** is the friction-correct pattern for any product whose core value doesn't require identity — let the user experience value first, and make registration the door to *additional* value (sync, profiles), not the toll booth in front of all of it. And when you critique any system's security — including your own — always write the threat model down first; a vulnerability only means something relative to who attacks, with what access, for what prize.

---

## 13. Performance Posture

### The facts: a governor, a budget, and a renderer choice

Relax Room's performance story is owned by `PerformanceManager` — the eighth and final autoload, living in `v1/scripts/systems/` — and rests on three documented decisions:

1. **Focus-based FPS throttling.** 60 FPS while the window is focused; **15 FPS** when unfocused, driven by the viewport's focus signals. The documented rationale is existential for the genre: a desktop companion that burned 60 FPS in the background would drain laptop batteries and steal cycles from the user's actual work — the app would be fired from its own job description.

```
┌─────────────────────┐      ┌─────────────────────┐
│  Window focused     │      │  Window unfocused   │
│  Engine.max_fps=60  │      │  Engine.max_fps=15  │
│  full interaction   │      │  minimal updates    │
│  smooth animation   │      │  battery friendly   │
└──────────┬──────────┘      └──────────┬──────────┘
           └──── focus_entered / focus_exited ────┘
```

2. **The GL Compatibility renderer.** Of Godot 4's three backends (Forward+, Mobile, Compatibility), the project chose the OpenGL-based Compatibility renderer: a 2D pixel-art app needs none of Forward+'s lighting arsenal, Compatibility runs on ~15 years of hardware including weak integrated GPUs, minimizes graphics overhead alongside other running applications, and is the required backend for a web export. Maximum reach, minimum footprint — the pillar list, translated into a dropdown choice.
3. **Pixel-art rendering settings.** The documented configuration:

```
project.godot:
  rendering/textures/canvas_textures/default_texture_filter = 0   (Nearest)
  display/window/size/viewport_width  = 1280
  display/window/size/viewport_height = 720
  display/window/stretch/mode = "canvas_items"

per-sprite:
  texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
```

Nearest-neighbor filtering picks the closest texel with no interpolation — a pixel stays a crisp square — where linear filtering would average neighbors into a blurred smudge. Combined with the fixed 1280×720 design resolution and `canvas_items` stretch (UI and world scale together, cleanly), the pixel-art look costs *nothing at runtime*: it is entirely a sampling configuration, no shaders involved. [Sprites and Textures](SPRITES_AND_TEXTURES.md) covers the mechanics in depth.

PerformanceManager's position in the chain is itself a fact worth re-reading: it depends on SaveManager because performance-adjacent state — the documented example is the saved window position — must be restored before the governor applies it. Nothing depends on PerformanceManager; it is a pure leaf.

The governor's core mechanism is small enough to show whole (**ILLUSTRATIVE** — the documented behavior as minimal code):

```gdscript
## ILLUSTRATIVE — focus-based FPS throttling
func _ready() -> void:
    get_window().focus_entered.connect(func() -> void: Engine.max_fps = 60)
    get_window().focus_exited.connect(func() -> void: Engine.max_fps = 15)
```

That a product-defining behavior fits in four lines is the point, not a dismissal: the *decision* (which numbers, which trigger, who owns it) is the engineering; the code is clerical. Note also what capping `Engine.max_fps` does and does not do — it throttles the render/process loop wholesale, which is exactly right when *everything* should slow down together; per-system throttling (pausing only animations, only particles) would be the tool if some subsystem needed to stay hot.

### Analysis: performance as a product requirement, not an optimization

The deep lesson is *where* performance lives in this project: in the **requirements**, stated as numbers (60/15), owned by a named component, from day one. Contrast the industry's default failure mode — performance as a panic phase before shipping, with profiling sessions hunting mystery costs across an unbudgeted codebase. Relax Room inverts this: because "unobtrusive" is a pillar, the budget came first and the architecture accommodated it (Compatibility renderer, throttling governor, ColorRect rooms costing no texture memory, panels destroyed when closed).

The throttling design also shows a subtlety: FPS capping is the *right lever* for this genre because a 2D app's cost scales almost linearly with frames rendered — halving FPS roughly halves GPU/CPU spend, and 15 FPS keeps animations alive (a dead-frozen companion would feel broken) while cutting ~75% of the budget. Alternative levers (pausing the tree, disabling processing per-node) save more but cost liveness; the governor picks the cheapest lever that preserves the product feel. A dedicated module, [Desktop Companion Performance](DESKTOP_COMPANION_PERFORMANCE.md), develops the full posture.

> ✅ **Best practice** — Give performance a number and an owner. "Should be fast" produces nothing; "≤15 FPS unfocused, owned by PerformanceManager" produces a testable contract and a place where every future performance decision naturally lands.

### Generalized lesson: budgets beat heroics

Every serious performance culture — game studios with per-frame millisecond budgets per subsystem, web teams with performance budgets in CI, mobile teams with battery drain gates — converges on the same shape Relax Room instantiates in miniature: numeric targets set at design time, a component that owns enforcement, and architecture choices made *under* the budget rather than optimized *toward* it afterwards. When you start your own project, write the budget in the first week: target FPS (foreground *and* background — most desktop tools forget the second number), memory ceiling, startup time. Cheap to write down, transformative as a constraint.

---

## 14. One-Person Maintainability

### The facts: the bus factor of this project is approximately one

Relax Room is an IFTS 2026 projectwork whose documentation is signed by a single System Architect & Project Supervisor. Whatever the wider team contributed, the architecture is explicitly built to be *held in one head* — and the study documents you are reading are part of that architecture. The documented evidence of a maintainability-first posture:

- A **quick-reference card set** in the study README: the 8-entry autoload order with dependencies, all 31 signals grouped by domain, and the important file paths — the whole architecture on one screen.
- A **documentation suite with a prescribed reading order** (ten study modules, from this deep dive through build & export), mapping documents to exam topics — plus a developer reference (`TECHNICAL_GUIDE.md`) and per-team-member operational guides in a `guide/` folder, so each role has a runbook rather than tribal knowledge.
- An **audit culture**: the project's `AUDIT_REPORT.md` records a technical audit v2.0.0 dated 1 April 2026 — 23 sections, 24 scripts analyzed. Auditing your own codebase and writing the findings down is rare even in industry.
- **Convention density**: one bus, one panel manager, one save path, one catalog loader, named containers, a documented anti-pattern list. Fewer distinct ideas to remember means less context to reload after six months away.
- And one honest debit: the **GdUnit4 test suite was removed in March 2026**. The safety net that most directly substitutes for a second maintainer is currently absent.

### Analysis: what "maintainable by one person" concretely means

"Maintainability" is usually hand-waved; this project lets us define it operationally. A codebase is one-person-maintainable when *the person with zero recent context* — you, next year — can answer the following questions quickly, and Relax Room has a designed answer for each:

| Question after six months away | The project's answer | Cost when the answer is missing |
|-------------------------------|----------------------|--------------------------------|
| "What talks to what?" | grep `SignalBus.` — every cross-system interaction surfaces; the signal card is the index | Reading every file to rebuild the interaction graph |
| "What starts when, and why?" | The autoload dependency card; order enforced by `project.godot` | Boot-order bugs debugged by trial and error |
| "Where is the state?" | Autoloads own canonical state; scenes render it | State scattered across scenes, duplicated and drifting |
| "What content exists?" | Four JSON catalogs, human-readable | Content archaeology across scripts and scenes |
| "What did the player's data look like over time?" | The versioned save + migration chain is executable history | Un-loadable old saves, support tickets |
| "What was decided, and why?" | The study docs and audit report record the trade-offs | Re-litigating every decision from scratch |
| "Did I just break something?" | **Gap: no test suite since March 2026** | Manual regression passes, or shipped breakage |

Two deeper observations. First, most rows are answered by *structure*, not documentation: the bus makes interactions greppable, the chain makes boot order executable, the catalogs make content legible. Structure cannot go stale; prose can. The project leans on documents where structure cannot reach (rationale, history) and on structure everywhere else — which is the right division of labor. Second, the one structural gap (tests) is exactly the row where a solo maintainer is weakest: a team catches regressions in review; a soloist's only reviewers are tests and time. The architecture is, ironically, unusually *testable* — bus-driven systems can be probed by emitting signals at them (Section 4) — making the missing suite a matter of investment, not possibility. That removal was recorded with a date, at least, keeping even the debt legible.

> ⚠️ **Pitfall** — Solo maintainability is often confused with minimalism ("fewer files = simpler"). The real currency is **rediscoverability**: how fast can cold context be rebuilt? Eight well-named autoloads with a documented order beat three cleverly merged god objects every time. Optimize for the reader you will become, not the writer you are.

### Analysis: the week-one plan this architecture makes possible

A useful thought experiment: suppose a competent Godot developer inherited Relax Room tomorrow, alone. The architecture's maintainability claims become concrete as an onboarding sequence that the project's own artifacts support:

1. **Day 1 — the card and the map.** Read the quick-reference card (autoload order, 31 signals, file paths), then this deep dive. Outcome: the topology is in memory before any code is opened.
2. **Day 2 — the spine.** Read the eight autoload scripts in chain order, checking each against its documented dependencies. Outcome: boot understood end to end, including `load_completed` as the rendezvous.
3. **Day 3 — the traffic.** Grep every `SignalBus.` emit and connect; annotate the signal table with actual producers/consumers (Exercise 2 formalizes this). Outcome: the real interaction graph, verified rather than believed.
4. **Day 4 — the data.** Read the four catalogs and a real `save_data.json` side by side; trace one decoration from catalog entry to save entry. Outcome: the content and persistence contracts internalized.
5. **Day 5 — controlled contact.** Make one throwaway change per plane — add a catalog decoration (data), log a bus signal (communication), tweak a panel fade (UI) — and revert them. Outcome: confidence that the mental model predicts the system's behavior.

Five days to safe productivity, alone, is an aggressive claim for any real codebase — and each step leans on a *designed* property: the card exists, the chain order is documented, the bus is greppable, the data is readable. Run the same experiment against a hypothetical version of this app with direct cross-references, hardcoded content and an unversioned binary save, and week one becomes month one. Maintainability is precisely this difference, made of specific artifacts.

### Generalized lesson: design for your future amnesiac self

The industry name for this concern is the **bus factor** — how many people can be hit by a bus before the project stalls — and solo projects start at the minimum. The transferable program, in priority order: (1) make architecture greppable — central seams like an event bus turn "what connects to what" into a search; (2) keep one small quick-reference card per system and let long prose decay gracefully; (3) let executable artifacts (config-enforced ordering, migrations, tests) carry as much truth as possible, because they cannot drift silently; (4) date your decisions, including the regrettable ones — a dated debt is a plan, an undated one is a surprise; (5) audit yourself on a calendar, because no one else will. The uncomfortable truth this project demonstrates from both sides: documentation is a maintainability *supplement*, tests are a maintainability *organ*. You can live without one of them. Briefly.

---

## 15. File Layout Conventions

### The facts: the documented tree

```text
Code:
  v1/scripts/autoload/       — 7 singletons (SignalBus, AuthManager, SaveManager, ...)
  v1/scripts/rooms/          — room logic, decorations, characters, background
  v1/scripts/menu/           — main menu, auth screen, walk-in character
  v1/scripts/ui/             — UI panels, PanelManager, drop zone, profile
  v1/scripts/utils/          — Constants, Helpers
  v1/scripts/systems/        — PerformanceManager

Data:
  v1/data/characters.json    — character catalog (sprites, animations)
  v1/data/decorations.json   — 69 decorations in 11 categories
  v1/data/rooms.json         — room catalog (themes, colors)
  v1/data/tracks.json        — music track catalog

Scenes:
  v1/scenes/main/            — the main scene (gameplay room)
  v1/scenes/menu/            — the main menu
  v1/scenes/ui/              — UI panel scenes (.tscn)

User data (runtime, outside the project):
  user://cozy_room.db          — SQLite (9 tables, WAL mode)
  user://save_data.json        — JSON save, v5.0.0
  user://save_data.backup.json — last known-good save backup
```

Asset licensing is documented per-pack in `v1/assets/README.md`; the content inventory records only CC0 and free-for-commercial-use assets (Kenney UI kit, Mixkit audio, Eder Muniz backgrounds, CC0 sprites and characters), with no GPL or copyleft assets — avoiding license contamination in a distributable product.

### Analysis: what the layout encodes

- **Top-level split by artifact kind (`scripts/`, `scenes/`, `data/`, `assets/`), second level by feature (`rooms/`, `menu/`, `ui/`).** Kind-first fits this project because its planes genuinely have different audiences and rules: `data/` is the designer-editable surface, `scenes/` the editor-authored surface, `scripts/` the code-reviewed surface. Feature-first (all of a feature's scripts+scenes+data in one folder) is the stronger convention for larger games where features come and go as units; at 24 scripts, kind-first with feature subfolders is the lower-overhead choice.
- **`autoload/` vs `systems/` is a semantic distinction, not a technical one** (Section 5): the folder claims PerformanceManager is conceptually "a system", while `project.godot` makes it an autoload like the others. Layout communicates intent; registration confers behavior. Know which is which.
- **`utils/` is fenced to two names — `Constants` and `Helpers`.** Every project needs a junk drawer; the discipline is keeping it *small and boring* (pure functions like `snap_to_grid()`, named constants like `DEFAULT_SPEED`). The moment a "util" holds state or knows about game concepts, it is a system wearing a disguise and belongs in a real folder.
- **`user://` is not part of the project tree — and that is the point.** Godot separates the read-only packaged project (`res://`) from the per-user writable directory (`user://`). Everything the player generates lives in `user://`; everything shipped lives in `res://`. This boundary is also the moddability line of Section 6 and the reason saves survive reinstalls.
- **The `v1/` root prefix versions the whole project tree** — a heavyweight but unambiguous way to leave room for a future clean-slate `v2/` without archaeology in git history alone.

> ✅ **Best practice** — Whatever layout you choose, make it *predictable enough to guess*: a newcomer told "there's a panel manager" should find `v1/scripts/ui/` on the first try — and here, they would. Prediction success rate is the only layout metric that matters.

### Generalized lesson: layout is the first documentation anyone reads

A file tree is read hundreds of times more often than any README. The transferable rules: choose kind-first or feature-first deliberately and stay consistent; quarantine generated/user data outside the source tree; fence the junk drawer; and treat licensing metadata as part of the layout (a per-pack license README next to the assets it covers, as this project does, is worth more than a compliance spreadsheet nobody opens).

---

## 16. Best Practices

What to **imitate** from Relax Room's architecture, and what to **reconsider** — because a case study that only admires teaches nothing.

### Imitate

1. **Start with a SignalBus and a naming convention.** Past-tense facts, `_requested` commands with exactly one documented owner, granularity chosen by audience (Section 4). Keep a generated signal inventory.
2. **Write the autoload chain as a dependency card and keep `project.godot` sorted topologically.** Infrastructure first (bus, logger), storage before identity, identity before content, consumers of restored state last, and a boot-completion signal (`load_completed`) instead of boot-time broadcasting (Section 5).
3. **Put all content in ID-keyed catalogs; keep behavior in code.** Stable IDs, id/name split, presentation parameters in data, UI generated from the catalog (Section 6).
4. **Persist through one chokepoint with a dirty flag, atomic writes, and a backup file.** Set on every mutation, clear only after *all* writes succeed, flush on quit via `_notification()` (Section 9).
5. **Version every persisted format from day one and migrate in chained steps written contemporaneously** (Section 10).
6. **Name your source of truth in writing.** Dual stores are fine; ambiguous authority is fatal (Section 11).
7. **Build the sync queue before the sync.** Journal offline operations transactionally now; bolt the network on later as an additive feature (Section 11).
8. **Give every UI surface a lifecycle owner** with a single chokepoint, an explicit policy, and lifecycle events on the bus (Section 8).
9. **Set numeric performance budgets with a named owner at design time** — including the background number (Section 13).
10. **Document per-asset licenses next to the assets**, and refuse copyleft contamination in distributable products (Section 15).
11. **Date your decisions, audit yourself on a calendar, and keep a one-screen quick-reference card current** (Section 14).

### A starter checklist for a new project in this style

The imitation list, converted into the order you would actually execute it in a fresh Godot 4.5 project:

- [ ] Create `SignalBus` (declarations only) and `AppLogger`; register them as autoloads 1 and 2.
- [ ] Write the signal naming table (facts past-tense, `_requested` commands with one owner) into the project README before the third signal exists.
- [ ] Add remaining autoloads one at a time, each with a stated dependency list; keep `project.godot` topologically sorted; assert dependencies in debug builds.
- [ ] Establish `load_completed` (or equivalent) as the boot rendezvous before any system restores state.
- [ ] Create `data/` catalogs with `id`/`name` split from the first entry; write the schema card the same day.
- [ ] Build SaveManager's 40-line spine (dirty flag, timer, quit hook, atomic write, backup) before the first feature that needs saving.
- [ ] Put `"version"` in the save format in the first commit that writes it; create the migrations file in the same commit.
- [ ] Decide and write down the source-of-truth rule the day a second store appears.
- [ ] Give every UI surface a lifecycle owner before the second surface exists.
- [ ] Write the performance budget (foreground *and* background numbers) in week one; name its owning component.
- [ ] Record every asset's license on arrival, in a README next to the assets.
- [ ] Keep one quick-reference card current per subsystem; date every decision, especially the regrettable ones.

### Reconsider

1. **Plain SHA-256 password hashing.** Wrong primitive for password storage; adopt Argon2id/bcrypt/scrypt via a maintained implementation, or delegate to platform auth in Phase 4, with hash-upgrade-on-login for existing users (Section 12).
2. **Living without a test suite.** The March 2026 removal traded permanent risk for temporary velocity; the bus-driven architecture is unusually cheap to test, so the debt is voluntary. Reinstating even a thin suite over the save/migration path would buy the most safety per line (Sections 9, 10, 14).
3. **Dual-write without a reconciliation routine.** The JSON-primary rule contains the divergence risk, but a "rebuild mirror from JSON" repair function (run on detected mismatch, or on demand) would close the loop the docs themselves flag (Section 9, step 6).
4. **All-code panel UI as an absolute.** Catalog-driven grids justify code generation; static panel frames would be cheaper to iterate as `.tscn`. Frame-in-scene, content-in-code is the scalable compromise (Section 8).
5. **Fail-soft-only catalog validation.** Right for today's authorship model; add a fail-fast debug/CI validation pass before any second content author — human or modder — touches the JSON (Section 6).
6. **Hand-maintained signal documentation.** The `track_play_pause` naming drift shows the cost; generate the inventory from the bus script instead (Section 4).

---

## 17. Common Errors & Troubleshooting

Oriented to *architectural* mistakes — the ones this design prevents when respected and invites when violated.

| Symptom | Likely architectural cause | Fix |
|---------|---------------------------|-----|
| Crash at boot: nil instance on a global name inside an autoload's `_ready()` | Autoload order violates the dependency chain (e.g., a manager registered before SignalBus), or initialization done in `_init()` instead of `_ready()` | Restore the documented 8-entry order in `project.godot`; move all cross-autoload access to `_ready()` (Section 5) |
| A signal is emitted but "nothing happens" | Listener never connected (typo'd signal name; connect code path not reached), or listener's node was freed | grep for both `emit` and `connect` sites of that exact name; check the signal inventory for naming drift (Section 4) |
| State restored from save is silently ignored (music restarts from defaults, window position lost) | A consumer of restored state runs before SaveManager in the chain, or restores in its own `_ready()` instead of on `load_completed` | Key all state restoration off `load_completed`, never off boot order alone (Section 5) |
| Boot-time signal reaches some listeners but not others | Emission during an autoload's `_ready()`, before later autoloads/scenes have connected | Emit a completion signal after the chain is up; connect early, emit late (Section 5) |
| Two sources disagree about current state (UI shows one value, save file another) | A script mutated another autoload's state directly instead of emitting the corresponding signal | Enforce the bus rule; the documented anti-pattern list forbids `SaveManager.game_data[...] = x` style writes (Section 3) |
| Changes lost after a crash (but not after a normal quit) | Dirty-flag window: crash occurred inside the 60s autosave interval | Expected loss envelope by design; shrink the interval or save eventually on precious events if the product demands it (Section 9) |
| Save file corrupted after a crash during save | Atomic-write pattern bypassed (direct overwrite of `save_data.json`) | Always write temp-then-rename with the backup promotion step; restore from `save_data.backup.json` (Section 9) |
| Old save loads with missing/duplicated fields | A schema change shipped without its migration step, or a shipped migration was edited | One new chained migration per version, append-only; test the chain against one fixture per historical version (Section 10) |
| JSON and SQLite disagree | Dual-write partial failure (step-6 divergence) | JSON is the source of truth by written rule; rebuild the mirror from JSON, never merge (Sections 9, 11) |
| Duplicate or "stuck" UI panels; two panels open at once | A panel instantiated outside PanelManager ("wild panel"), or fade-out tween raced `queue_free()` | Route every open/close through the manager; sequence free after `tween.finished`, kill running tweens before force-close (Section 8) |
| Decoration appears off the 64px grid, or reloads one cell away | Position canonicalized per-listener instead of once at the source; `snap_to_grid()` rounding bug (documented critical point) | Snap before emitting `decoration_placed`, so renderer and save receive identical coordinates (Section 9) |
| Memory grows during long sessions with much decorating | Spawned nodes without cleanup — the documented missing-`_exit_tree()` risk in DecorationSystem; tweens outliving nodes | Track spawned children under their container and free them with it; kill tweens in `_exit_tree()` (Sections 7, 8) |
| Renamed content breaks existing saves | Catalog `id` changed (identity), when only `name` (display) should change | IDs are immutable once persisted; renames touch `name` only — deletions require a migration decision (Sections 6, 10) |
| App hot on battery while in background | FPS governor bypassed or focus signals not reaching PerformanceManager | Verify the 60/15 focus-based throttle; the background number is the product contract (Section 13) |

### Design smells: trouble before it becomes a symptom

The table above catches failures; these earlier warning signs deserve a review comment the day they appear:

| Smell | Why it is a smell | The drift it predicts |
|-------|-------------------|----------------------|
| A signal name in present/imperative tense (`open_shop`) | The bus is becoming an RPC mechanism | Emitters start assuming specific receivers; decoupling quietly dies |
| A second script connects to a `_requested` signal | Commands now have two owners | Double-execution bugs; save written twice, panels opened twice |
| An autoload reads a *later* autoload in `_ready()` | The dependency DAG has grown a forward edge | Boot works today by luck; breaks on the next reorder |
| A scene script writing `SomeManager.some_field = x` | The bus rule has its first exception | State divergence between UI and persistence |
| A catalog entry field that only one item uses | Schema growing by special case | The catalog becomes untyped soup; validation impossible |
| Button-level events appearing on the global bus | The UI domain is losing its smallness | Listener noise; every system re-filtering events it never wanted |
| A `util` that holds state or knows game concepts | A system hiding in the junk drawer | Invisible coupling with no documented dependencies |
| "Temporary" direct call between systems with a TODO | The exception that outlives the rule | The next reader copies it; the architecture erodes by precedent |

---

## 18. Exercises

Analysis exercises, not coding katas: each asks you to *reason inside* the documented architecture. Work on paper or in a design doc first; touch code only where an exercise says so. Acceptance criteria are written so you can self-grade.

### Exercise 1 — Trace a signal flow: the volume slider

**Task.** The player opens the settings panel and drags the master-volume slider. Write the complete numbered trace, in the style of Section 9's decoration trace, from the input event to the moment the new volume is (a) audible, (b) persisted in `user://save_data.json`, and (c) mirrored to SQLite. Use only documented signals (`volume_changed`, `settings_updated`, `save_requested`, `save_completed`, `save_to_database_requested`) and documented mechanisms (dirty flag, 60-second autosave, quit-flush via `_notification()`).

**Acceptance criteria:**
- Every step names an emitter, a signal (or a direct intra-system call), and a listener.
- The trace identifies exactly where `_is_dirty` becomes true, and *why the audible change and the persisted change happen at different times*.
- The trace states what is lost if the app crashes 10 seconds after the drag, and why a normal quit loses nothing.
- The trace never contains a scene script writing another autoload's variables directly.

### Exercise 2 — The signal traffic map

**Task.** Build a table of all 31 signals with three columns: plausible producer(s), plausible consumer(s), and traffic character (fact / command / broadcast / reserved). Then mark the fan-in hotspot and the fan-out hotspot identified in Section 4, and add one signal of your own reasoning for each. Finally, formulate — precisely, as a checkable question — whether decoration rotation and scale survive a save/load round-trip in v5.0.0, and (if you have project access) answer it from `save_manager.gd` and the v5 format.

**Acceptance criteria:**
- All 31 signals appear; the two Sync signals are correctly marked *reserved* (no current emitter).
- Every `_requested` signal names exactly one owning handler.
- Each hotspot carries a one-sentence risk note ("this is where testing/ordering care concentrates because ...").
- The rotation/scale question is phrased so that reading one function could answer it.

### Exercise 3 — Two reordering post-mortems

**Task.** Choose two illegal autoload orderings from Section 5's table — one with a *silent* failure character and one with a *loud* one. For each, write a short incident report as if the reordering had shipped: title, first failing call at boot, failure grade (crash / silent data issue / cosmetic), the user-visible symptom, how long it would plausibly take to detect, and the one-line prevention.

**Acceptance criteria:**
- The first failing call is specific ("AuthManager reads accounts in `_ready()` while `cozy_room.db` is not yet open"), not generic ("things break").
- The silent case's report explains *why* nothing crashed.
- Each prevention names an enforcement mechanism (chain order in `project.godot`, `load_completed` keying, a boot assertion), not "be careful".

### Exercise 4 — Design a feature inside the architecture: the pet system

**Task.** The content inventory ships one pet (Void Cat) as an asset with no system behind it. Design — on paper — a pet feature that fits this architecture: a pet walks around the room, can be adopted/dismissed from a panel, and persists. Specify: the catalog file and entry schema; the new SignalBus signals with their domain assignment; the owner of pet state; the save-schema v6 delta and its chained migration; and which *existing* scripts change.

**Acceptance criteria:**
- The catalog entry follows the documented conventions: stable `id`, display `name` separate, `sprite_path` indirection, presentation parameters in data.
- New signals follow the naming table (past-tense facts; any command uses `_requested` with one documented owner) and land in a sensible domain (existing or new — justify).
- The migration is one chained step, versioned, preserving all existing player data.
- The list of modified existing scripts is short and justified — a bus architecture should absorb the feature mostly by *addition*; every modification you need is worth one sentence of explanation.
- No scene script mutates an autoload's internals; no autoload gains a dependency on a *later* autoload.

### Exercise 5 — The auth redesign memo

**Task.** Write a one-page security memo on AuthManager. Part 1: the threat model of the *current* app (attacker, access, prize) and what SHA-256 password storage actually risks within it. Part 2: the Phase 4 threat model (cloud sync) and why it invalidates Part 1's comfort. Part 3: your recommendation — algorithm choice with parameters rationale, the hash-upgrade-on-login migration for existing local users, and the build-vs-delegate decision for the cloud era.

**Acceptance criteria:**
- Both threat models name attacker capability and payoff concretely; the local model honestly acknowledges its limited blast radius.
- The recommendation cites the OWASP ordering (Argon2id first; bcrypt/scrypt/PBKDF2 alternatives) and explains *why fast hashes disqualify themselves*.
- The migration path resets zero passwords.
- The memo answers "why not just harden SHA-256 with more rounds?" correctly (iterated general-purpose hashes are inferior to memory-hard designs; and hand-rolling is the real risk).

### Exercise 6 — The save recovery runbook

**Task.** Write the load-time decision ladder for SaveManager as a runbook: what happens on (a) `save_data.json` missing, (b) parse failure, (c) parse success but semantic corruption (fields missing/nonsensical), (d) a version *newer* than the app knows, (e) JSON/SQLite divergence detected. Use the documented assets: the backup file, the migration chain, the JSON-is-primary rule.

**Acceptance criteria:**
- Every branch ends in a defined state (loaded / loaded-from-backup / fresh start) and never a crash.
- The backup file is promoted in exactly one branch, and the runbook states when the *backup itself* gets overwritten (only by a verified-good save).
- Divergence resolution rebuilds the mirror from JSON — the runbook never merges mirror data back into the primary.
- The newer-version branch does something explicit and non-destructive (refuse with a message, or back up before attempting), with a sentence defending your choice.

### Exercise 7 — The moddability spike

**Task.** Design (do not build) mod support for decorations along Section 6's override-directory sketch: `user://mods/decorations.json` merged over the shipped catalog. Specify merge semantics, validation posture for mod data, sprite loading for unpacked files, and — the hard part — save-file behavior when a save references a modded decoration and the mod is later removed.

**Acceptance criteria:**
- Merge is by `id`, with stated precedence and a stated policy for malformed mod entries (fail-fast with author-readable errors — justify why fail-soft is wrong for this audience).
- The design notes that `load()` cannot read loose user files and names the runtime-loading path instead.
- The missing-mod-decoration policy is explicit (skip and warn / placeholder sprite / strip on save — any is defensible, silence is not) and preserves the rest of the save.
- One paragraph estimates what this feature would have cost if content were hardcoded, using Section 6's analysis.

### Exercise 8 — The test reinstatement plan

**Task.** The test suite was removed in March 2026. Propose the first five tests to reinstate, ordered by risk-per-line-of-test. Draw candidates from the documented critical points: the migration chain, the atomic write + backup promotion, `Helpers.snap_to_grid()`, the dirty-flag lifecycle (set / clear-on-success-only / observe), and catalog validation.

**Acceptance criteria:**
- Each of the five names a concrete first test case ("loading a v1.0.0 fixture yields a valid v5.0.0 dictionary with coins preserved"), not a topic.
- Each is justified by a documented failure mode or critical point from this module.
- The ordering argument weighs blast radius (user data loss ranks above visual bugs) against test cost.
- At least one test exploits the bus architecture's testability: probing a system purely by emitting signals at it and observing emitted signals back.

### Self-check: the project's own study questions

Before the exercises above, the project's study material poses seven questions of its own — answer them without looking, then verify against the indicated files (translated here; file pointers as documented):

1. **How many signals does the SignalBus have?** List at least 10 with their purpose. *(Verify: `scripts/autoload/signal_bus.gd`)*
2. **In what order do the autoloads load, and why does the order matter?** *(Verify: `project.godot`, `[autoload]` section)*
3. **What happens if you quit without saving manually — is data lost?** *(Verify: `scripts/autoload/save_manager.gd`, the `_notification()` function)*
4. **Why do decorations carry a placement-type field, and what would happen if a wall item were placed on the floor?** *(Verify: `data/decorations.json`, `scripts/rooms/decoration_system.gd`)*
5. **How many tables does the SQLite database have, and what is each PRIMARY KEY?** *(Verify: `scripts/autoload/local_database.gd`, `_create_tables()`)*
6. **How does the game know which character to show at startup?** Trace the flow from save to render. *(Verify: `save_manager.gd` → `game_manager.gd` → `room_base.gd`)*
7. **What would break if you removed SignalBus from the project?** *(Reasoning: consider every `SignalBus.*.connect()` in the codebase)*

If this module did its job, questions 1-3 and 7 should now feel almost insultingly easy — and questions 4-6 should feel like *precise* questions you know exactly where to answer.

---

## 19. Further Reading

Pattern literature, engine documentation, and the industry sources behind this module's generalized sections — annotated so you know *why* to open each.

A note on evidentiary weight before the list: the **project facts** in this module come exclusively from the Relax Room study documentation itself (this repository's project documents and quick-reference cards); the sources below inform only the *generalized* commentary — the industry patterns, their history and their trade-offs. Keep the two layers separate in your citations too: when you write about the project, cite the project; when you write about the pattern, cite the literature.

### Pattern literature

- **Robert Nystrom — *Game Programming Patterns*** (free online: [gameprogrammingpatterns.com](https://gameprogrammingpatterns.com/)). The single most relevant book to this module. Read *Observer* (the mechanism under Godot signals), *[Event Queue](https://gameprogrammingpatterns.com/event-queue.html)* (the queued elder sibling of the SignalBus — "an asynchronous observer"), *Singleton* (the honest costs of what autoloads are), and *Dirty Flag* (Section 9's pattern, with the graphics-engine origin story).
- **Gamma, Helm, Johnson, Vlissides — *Design Patterns* (GoF, 1994).** The primary source for *Observer* and *Mediator*; Section 4's argument that an event bus is mediator-topology-with-observer-dumbness reads best with both original definitions fresh. Skim the intent sections; the C++ is period furniture.
- **Martin Fowler — [What do you mean by "Event-Driven"?](https://martinfowler.com/articles/201701-event-driven.html)** Disentangles event notification, event-carried state transfer, and event sourcing. Relax Room's bus is *event notification*; knowing the siblings tells you what you would reach for next (the sync queue is one step toward event sourcing).
- **[Event Bus pattern overview](https://ducmanhphan.github.io/2020-06-06-Event-Bus-pattern/)** — a compact treatment of the bus's structure, benefits and drawbacks in the same terms Section 4 uses (decoupling gained, traceability taxed).

### Godot documentation (docs.godotengine.org, 4.x)

- **Signals (step-by-step + `Signal` class reference).** The connection model, typed signal parameters, `Callable` binding, and connect flags — the mechanics every SignalBus decision sits on.
- **Singletons (Autoload).** The official statement of load order and lifetime — the two guarantees Section 5's chain is built from.
- **Data paths (`res://` vs `user://`).** The boundary that is simultaneously the save-location rule, the moddability line, and the reinstall-survival guarantee.
- **`FileAccess` / `DirAccess` class references.** The primitives under the atomic-write pattern.
- **`CanvasLayer`, `CharacterBody2D`, drag-and-drop in `Control`.** The engine contracts behind Sections 7's trees and the DropZone.

### Data-driven and content design

- **Cornell CS3152 — [Data-Driven Design lecture](https://www.cs.cornell.edu/courses/cs3152/2014sp/lectures/14-DataDriven.pdf).** A rigorous course treatment of why content belongs in data: iteration speed, designer empowerment, and the code/data boundary Section 6 draws.
- **GameDev.net — [How to make your games moddable](https://gamedev.net/blogs/entry/2270892-how-to-make-your-games-moddable/).** Practical mod-enablement patterns; read against Section 6's override-directory sketch.
- **[Data-driven design in everyday software](https://dev.to/methodox/data-driven-design-leveraging-lessons-from-game-development-in-everyday-software-5512)** — the same pattern exported from games to general software, useful for seeing the catalog contract without the game context.

### Offline-first and persistence

- **[Local-first software](https://www.inkandswitch.com/local-first/) (Ink & Switch).** The movement's founding essay: seven ideals for software where the local copy is primary. Relax Room satisfies most of them by construction.
- **[The Complete Guide to Offline-First Architecture in Android](https://www.droidcon.com/2025/12/16/the-complete-guide-to-offline-first-architecture-in-android/)** — the mobile industry's canonical blueprint (local DB as source of truth, background sync engine, operation queue); Section 11's five-step sequence in production form.
- **[RxDB — Why local-first is the future](https://rxdb.info/articles/local-first-future.html)** — the web-stack perspective, including honest limitations (conflicts, storage quotas) that map onto Phase 4's deferred decisions.
- **SQLite — [Write-Ahead Logging](https://www.sqlite.org/wal.html).** The primary source on WAL: what the `-wal` file is, checkpointing, and the concurrency properties Section 11 leans on.

### Security

- **OWASP — [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).** The industry-standard answer Section 12 cites: Argon2id first, bcrypt/scrypt/PBKDF2 alternatives, with current parameter recommendations. Read before touching any auth code, ever.
- **OWASP — Threat Modeling resources.** The discipline behind Section 12's insistence that a vulnerability only means something relative to attacker, access and prize.

### Siblings in this course

- [Scenes and Nodes](SCENES_AND_NODES.md) — lifecycle and tree mechanics under Sections 5 and 7.
- [Database and Persistence](DATABASE_AND_PERSISTENCE.md) — SQLite, save patterns, auth and Supabase in implementation depth.
- [Autoload Safety](AUTOLOAD_SAFETY.md) — the failure modes of Section 5, expanded.
- [Game Dev Planning](GAME_DEV_PLANNING.md) — the change-management culture around this architecture.
- [Desktop Companion Performance](DESKTOP_COMPANION_PERFORMANCE.md) — Section 13 at full depth.
- [Build and Export](BUILD_AND_EXPORT.md) — how this architecture reaches players.
- [00-CAPSTONE](00-CAPSTONE.md) — the capstone project modeled on Relax Room's scope.

---

## 20. Glossary

| Term | Definition |
|------|------------|
| **Atomic write** | Safe-save pattern: write the full payload to a temporary file, then rename over the target. A crash at any instant leaves either the old or the new file intact, never a torn hybrid. Relax Room pairs it with a promoted backup (`save_data.backup.json`). |
| **Autoload** | A Godot singleton: a script/scene registered in `project.godot`, instanced before the main scene in declaration order, globally reachable by name, persistent across scene changes. Relax Room registers eight. |
| **Bus factor** | The number of people whose loss would stall a project. Solo-maintained projects sit at the minimum, which is why Section 14's rediscoverability techniques exist. |
| **Canonicalization** | Converting a value to its single authoritative form once, at the source, before distribution — e.g., snapping a drop position to the 64px grid *before* emitting `decoration_placed`, so every listener receives identical coordinates. |
| **Catalog-driven design** | Defining game content as ID-keyed data records (here: four JSON catalogs) that code interprets but never enumerates; the UI and gameplay build themselves from the catalog. |
| **Chained migration** | Save-format upgrading as a sequence of single-version steps (v1→v2→…→v5), each written when its schema change ships; ancient saves replay the whole chain. |
| **CharacterBody2D** | Godot's kinematic 2D body for script-driven movement with collision response (`move_and_slide()`); chosen over `RigidBody2D` when control must beat physics realism. |
| **Crossfade** | Audio transition where the outgoing track fades down (here to -80 dB) while the incoming fades up on a second player, then roles swap; the audio form of double buffering. |
| **Dirty flag** | A boolean recording "state changed since last save". Set by every mutating handler, cleared only after all writes succeed, observed by the autosave timer and quit hook. Decouples change frequency from write frequency. |
| **Dual-write** | Writing the same logical state to two stores (JSON + SQLite) outside one transaction. Survivable only under a written source-of-truth rule; the divergence risk is its permanent tax. |
| **Embedded database** | A database living as a file inside the app's process (SQLite) — no server, no configuration, no network. The correct topology for single-user local state. |
| **Event bus** | A central hub through which decoupled components communicate by publishing and subscribing to events: mediator's topology with observer's dumbness. `SignalBus` is an in-process, synchronous instance. |
| **Fail-fast / fail-soft** | Opposed validation postures: reject bad data loudly at load time vs degrade gracefully with defaults at read time. Choose per data-author audience (Section 6). |
| **Fan-in / fan-out** | Of a signal or component: how many sources converge on it / how many targets one emission reaches. Fan-in hotspots (SaveManager) concentrate testing needs; fan-out moments (`load_completed`) concentrate ordering care. |
| **Guest mode** | Frictionless anonymous identity: full app function without registration, with account creation as an upgrade path rather than a gate. |
| **Idempotent operation** | An operation safe to apply more than once with the same result — the property sync protocols demand of queued operations so that retries after unacknowledged pushes cannot duplicate effects. |
| **Hash-upgrade-on-login** | Migration pattern for password stores: verify against the legacy hash once, then immediately re-hash with the stronger algorithm — upgrading users without a reset. |
| **Mediator pattern** | GoF pattern where colleagues interact only through a central coordinator that owns the interaction logic. The SignalBus borrows its topology but deliberately not its intelligence. |
| **Observer pattern** | GoF pattern where subjects notify subscribed observers of events. Godot's `signal` is a language-level observer implementation. |
| **Offline-first** | Architecture inversion: the local store is the authoritative database, all reads/writes are local, and network sync is a background optimization. Relax Room is offline-first with the network layer deferred entirely to Phase 4. |
| **PanelManager** | The project's UI lifecycle owner: single chokepoint for opening/closing panels, exclusive-panel policy, fade transitions, instantiate-and-destroy lifecycle, lifecycle events on the bus. |
| **Reserved seam** | API surface declared before its feature exists (the Sync signals, the sync queue) so future functionality arrives additively against a stable contract. |
| **Salt** | Per-password random value mixed into the hash so identical passwords yield different digests, defeating rainbow tables. Necessary but not sufficient — a salted fast hash is still a fast hash. |
| **Source of truth** | The store that wins every disagreement, named in writing. Here: `save_data.json` is primary; SQLite is a rebuildable mirror. |
| **Sync queue** | A local table journaling operations performed offline, drained against the cloud when connectivity returns; captured transactionally alongside the writes it describes. |
| **Topological sort** | An ordering of a dependency graph in which every node follows its dependencies — exactly what a correct autoload declaration order is. |
| **WAL (write-ahead logging)** | SQLite journal mode appending changes to a side log before folding them into the main file: readers don't block on writers, and crashes lose only the un-checkpointed tail. |

---

## Cross-links

- Previous in the course: [Database and Persistence](DATABASE_AND_PERSISTENCE.md) · [Scenes and Nodes](SCENES_AND_NODES.md)
- Deepens sections of this module: [Autoload Safety](AUTOLOAD_SAFETY.md) (Section 5) · [Rendering and Visual Logic](RENDERING_AND_VISUAL_LOGIC.md) (Section 7) · [Sprites and Textures](SPRITES_AND_TEXTURES.md) (Sections 7, 13) · [Tiles and Tilemaps](TILES_AND_TILEMAPS.md) (Section 7) · [Isometric Games](ISOMETRIC_GAMES.md) (Section 10) · [Desktop Companion Performance](DESKTOP_COMPANION_PERFORMANCE.md) (Section 13) · [Game Dev Planning](GAME_DEV_PLANNING.md) (Sections 2, 14) · [Build and Export](BUILD_AND_EXPORT.md) (Section 15)
- Next steps: [00-CAPSTONE](00-CAPSTONE.md) — the capstone brief modeled on Relax Room's scope · [00-GLOSSARY](00-GLOSSARY.md) — the course-wide glossary
- Project quick-reference cards (autoload order, signal domains, file paths): [README](README.md)

### Where to go next

If this module worked, you now hold a complete production architecture in your head — which is precisely the moment to stress-test it. Three suggested continuations, in increasing ambition:

1. **Verify one claim against the code.** Pick any single documented fact analyzed here (the dirty-flag clear ordering, the exclusive-panel policy, a signal's listener set) and confirm it in the project source. Nothing builds architectural judgment faster than checking documentation against reality — including finding the places where they disagree.
2. **Run the capstone.** [00-CAPSTONE](00-CAPSTONE.md) asks you to build a project at Relax Room's scope. Use Section 16's starter checklist as your first-week plan and this module as your running design reviewer.
3. **Write your own deep dive.** For any project you have already built, produce a document with this module's structure: facts, trade-offs, generalized lessons, imitate/reconsider. The gaps you cannot fill are your architecture's undocumented decisions — and now you know what it costs to leave them that way.

---

*Study document for Relax Room — IFTS Projectwork 2026.*
*Project author: Renan Augusto Macena (System Architect & Project Supervisor).*
*This module documents and analyzes the project as recorded in its own study documentation; illustrative code is marked as such and is not project source.*

*End of Module 09 — next: [00-CAPSTONE](00-CAPSTONE.md).*





