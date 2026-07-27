---
course: "Godot 4 in Production"
phase: "3 — Persistence and project structure"
module: "10"
title: "Game Dev Planning — Workflow, Version Control, Testing and Technical Debt"
version: "Godot 4.5 / GDScript 2.0"
level: "Intermediate"
prerequisites: [ "GODOT_ENGINE_STUDY.md", "PROJECT_DEEP_DIVE.md" ]
objectives:
  - "Write a one-page GDD-lite and a MoSCoW-prioritized milestone map before opening the editor"
  - "Apply the pre-modification checklist (blast radius, read-before-write, reproduce-before-fix) to every change"
  - "Configure Git for a Godot 4 project: correct .gitignore, .gitattributes with LFS, scene-conflict avoidance"
  - "Set up gdlint and gdformat locally and in CI, and run GUT or GdUnit4 tests headless with godot --headless"
  - "Diagnose the five classic Godot debt smells (god node, mega-script, signal spaghetti, autoload abuse, scene tangles) and apply the matching refactor recipe"
  - "Maintain a technical debt register and an ADR log for a small team"
  - "Run a sustainable solo/small-team process: kanban, definition of done, weekly review, honest estimation"
tags: [godot, gdscript, planning, version-control, git, testing, gut, gdunit4, refactoring, technical-debt, ci, project-management]
---

# Game Dev Planning — Workflow, Version Control, Testing and Technical Debt — Complete Guide

> **Module 10** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Godot Engine Study](GODOT_ENGINE_STUDY.md), [Project Deep Dive](PROJECT_DEEP_DIVE.md); Git basics (clone, branch, commit, merge).
>
> By the end of this module you will be able to:
> 1. Plan a feature before coding it: one-page GDD-lite, vertical slice definition, MoSCoW priorities, and a milestone map with honest (×2-3) estimates.
> 2. Run every code change through the pre-modification checklist: name the change, map its blast radius, read before writing, reproduce before fixing, and prepare the rollback path.
> 3. Configure version control for a Godot 4 project: ignore `.godot/`, commit `.import` files, track binaries with Git LFS, and prevent `.tscn` merge disasters with scene-ownership workflows.
> 4. Enforce code quality with the official GDScript style guide, `gdlint`/`gdformat` from godot-gdscript-toolkit, and typing discipline as a bug-prevention tool.
> 5. Write and run automated tests with GUT or GdUnit4 — unit tests for logic, scene tests, signal assertions, doubles and stubs — headless via `godot --headless`, plus manual test plans and soak tests for a desktop companion app.
> 6. Identify technical debt in scenes and scripts, apply refactor recipes (extract scene, extract component node, introduce signal bus, kill global state), and track debt in a register.
> 7. Manage a solo or small-team project without burning out: minimal kanban, definition of done, weekly review ritual, ADRs, and clean asset handoff with artists and audio designers.
>
> **Estimated time:** 6-8 hours reading · 4-6 hours labs · **Level:** Intermediate

## Guiding ideas

1. **The cheapest bug is the one you never write — ten minutes of planning beats ten hours of debugging.**
2. **Scope is the only variable a solo developer truly controls — cut features, never cut sleep.**
3. **Version control is a game-design tool: if you can revert fearlessly, you can experiment fearlessly.**
4. **Test the logic, play the feel — automate data transformations and save round-trips, playtest everything the player touches.**
5. **Technical debt is a loan, not a sin — track it in a register, pay interest consciously, never let it compound in silence.**
6. **Process exists to protect the game and the team — the moment a ritual stops paying rent, delete it.**

## Concept map

```
                        ┌──────────────────────────────────────┐
                        │   GAME DEV PLANNING (Module 10)      │
                        └──────────────────┬───────────────────┘
                                           │
        ┌──────────────────┬───────────────┼────────────────┬──────────────────┐
        │                  │               │                │                  │
 ┌──────▼──────┐   ┌───────▼──────┐ ┌──────▼───────┐ ┌──────▼───────┐ ┌───────▼────────┐
 │  PLAN       │   │  VERSION     │ │  QUALITY &   │ │  REFACTOR &  │ │  MANAGE        │
 │  BEFORE     │   │  CONTROL     │ │  TESTING     │ │  TECH DEBT   │ │  THE PROJECT   │
 │  CODE       │   │  FOR GODOT   │ │              │ │              │ │                │
 └──────┬──────┘   └───────┬──────┘ └──────┬───────┘ └──────┬───────┘ └───────┬────────┘
        │                  │               │                │                 │
  ┌─────┴──────┐    ┌──────┴───────┐ ┌─────┴────────┐ ┌─────┴────────┐ ┌──────┴───────┐
  │ GDD-lite   │    │ .gitignore   │ │ style guide  │ │ god node     │ │ kanban       │
  │ vertical   │    │ (.godot/!)   │ │ gdlint       │ │ mega-script  │ │ definition   │
  │ slice      │    │ .import: yes │ │ gdformat     │ │ signal       │ │ of done      │
  │ MoSCoW     │    │ LFS binaries │ │ typing       │ │ spaghetti    │ │ weekly       │
  │ milestones │    │ .tscn merge  │ │ code review  │ │ autoload     │ │ review       │
  │ ×2-3 rule  │    │ strategy     │ │ GUT/GdUnit4  │ │ abuse        │ │ burnout      │
  │ playtest   │    │ scene        │ │ headless CI  │ │ recipes:     │ │ guardrails   │
  │ cadence    │    │ ownership    │ │ soak tests   │ │ extract,     │ │ ADRs, docs   │
  │ pre-mod    │    │ branching    │ │ manual test  │ │ signal bus,  │ │ asset        │
  │ checklist  │    │ tagging      │ │ plans        │ │ strangler    │ │ handoff      │
  └────────────┘    └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                                           │
                              ┌────────────▼─────────────┐
                              │  CASE STUDY: RELAX ROOM  │
                              │  audit history · roles   │
                              │  workflow · debt ledger  │
                              └──────────────────────────┘
```

## Table of contents

1. [Why planning beats debugging](#why-planning-beats-debugging)
2. [GDD-lite: the one-page design document](#gdd-lite-the-one-page-design-document)
3. [Vertical slices, milestones and scope control](#vertical-slices-milestones-and-scope-control)
4. [The pre-modification checklist](#the-pre-modification-checklist)
5. [Version control for Godot projects](#version-control-for-godot-projects)
6. [Scene merges and team workflows](#scene-merges-and-team-workflows)
7. [Branching models, commits and tagging](#branching-models-commits-and-tagging)
8. [Code quality: style guide, gdlint and gdformat](#code-quality-style-guide-gdlint-and-gdformat)
9. [Typing discipline and code review](#typing-discipline-and-code-review)
10. [Testing in Godot 4: the landscape](#testing-in-godot-4-the-landscape)
11. [Writing tests with GUT and GdUnit4](#writing-tests-with-gut-and-gdunit4)
12. [Manual testing, debug tools and soak testing](#manual-testing-debug-tools-and-soak-testing)
13. [Continuous integration overview](#continuous-integration-overview)
14. [Refactoring recipes for Godot](#refactoring-recipes-for-godot)
15. [Technical debt management](#technical-debt-management)
16. [The mistake catalogue](#the-mistake-catalogue)
17. [Project management for solo and small teams](#project-management-for-solo-and-small-teams)
18. [Documentation, releases and maintenance](#documentation-releases-and-maintenance)
19. [Case study: Relax Room in production](#case-study-relax-room-in-production)
20. [Best practices](#best-practices)
21. [Common errors & troubleshooting](#common-errors--troubleshooting)
22. [Exercises](#exercises)
23. [Further reading](#further-reading)
24. [Glossary](#glossary)

---

## Why planning beats debugging

Game development has a reputation for chaos: shifting requirements, "I'll know it when I feel it" design targets, and codebases that grow organically until nobody dares touch them. The reputation is deserved — but the chaos is optional. Most of it comes from a single root cause: **writing code before understanding the problem**.

This module is the process backbone of the course. Everything else — scenes, autoloads, persistence, rendering — tells you *how* to build; this module tells you *how to keep building six months from now* without the project collapsing under its own weight. The techniques here are deliberately lightweight. You are not a 200-person studio; you are a solo developer or a team of three to five building a desktop companion app. Heavy process would kill your project just as surely as no process. The goal is the minimum discipline that keeps the maximum freedom.

### The cost-escalation curve

The most expensive bug is the one that could have been avoided by thinking for ten minutes before writing code. This is not a slogan; it is one of the oldest and most replicated findings in software engineering. Barry Boehm's cost-escalation model (1981) measured how the cost of fixing a defect grows with the phase in which it is discovered:

```
Cost of fixing the same defect, by phase discovered:

  During planning:      $1     (change a note in the design doc)
  During development:   $10    (rewrite code you just wrote)
  During testing:       $100   (find it, fix it, retest everything around it)
  After release:        $1000  (hotfix, user complaints, corrupted saves,
                                reputation damage, refund requests)
```

The exact multipliers vary by study, but the shape of the curve never does: **cost grows by roughly an order of magnitude per phase**. For games there is an extra multiplier the classic literature does not capture: a shipped bug in a game does not just cost engineering time — it costs *trust*. A companion app that corrupts a save file once loses the user forever, because the entire value proposition of a companion app is "this thing quietly works while I do something else."

### What "planning" means at our scale

Planning does not mean Gantt charts and requirements documents. For a small Godot project it means exactly four artifacts, each of which fits on a single page or in a single file:

| Artifact | Question it answers | Where it lives |
|---|---|---|
| **GDD-lite** | What are we building and for whom? | `docs/DESIGN.md` (one page, versioned) |
| **Milestone map** | In what order, and when is each part "real"? | `docs/MILESTONES.md` or the kanban board |
| **Pre-modification checklist** | Is this specific change safe to make right now? | Printed next to the monitor; in your head after a month |
| **Debt register** | What shortcuts have we taken and what do they cost? | `docs/TECH_DEBT.md` |

Everything else in this module — version control discipline, testing, refactoring — exists to make those four artifacts *true*. A milestone map you cannot trust is worse than no map, and the only way to keep it trustworthy is a codebase you can change without fear.

> ✅ **Best practice** — Timebox planning. For a task under one day of work, plan for 10-15 minutes. For a week-long feature, plan for an hour. If planning takes longer than 20% of the estimated implementation time, you are procrastinating with extra steps — start building the vertical slice and let reality correct the plan.

> ⚠️ **Pitfall** — The opposite failure exists too: *analysis paralysis*, where the design document grows for weeks while the project contains zero scenes. A plan that has never collided with a running build is fiction. Write the one-pager, build the slice, then revise the one-pager. Iterate between paper and editor; never stay on one side for more than a few days.

### The iceberg model

Players see perhaps 10% of what you build. The other 90% — save systems, error handling, signal cleanup, data migration, the CI pipeline — is invisible when it works and catastrophic when it does not:

```
What players see (10%):
┌───────────────────────────────────────────┐
│   Cozy room, cute character, relaxing     │
│   music, satisfying decoration placement  │
└───────────────────────────────────────────┘
                    ___
                   / | \
                  /  |  \
What developers build (90%):
                /    |    \
               / Save system \
              /  Error handling \
             /  Signal lifecycle   \
            /  Data migration chains \
           /  Performance budget        \
          /  CI / headless test pipeline  \
         /  Database schema                 \
        /  Window focus / pause semantics     \
       /  Asset import pipeline                 \
      /  Memory management                        \
     /______________________________________________\
```

Planning is mostly about the submerged part. Nobody needs a process document to remember to make the character cute; everybody needs one to remember that changing the save format requires a migration function, a round-trip test and a version bump — *before* the change ships, not after the first corrupted-save bug report.

### Course position

This module sits at the hinge of the course. Modules 01-09 taught the engine: scenes and nodes ([SCENES_AND_NODES.md](SCENES_AND_NODES.md)), autoload architecture ([AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md)), persistence ([DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md)), and the running Relax Room case study ([PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md)). Module 11 ([BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md)) will take the project out the door with export templates and CI release builds. This module supplies the connective tissue: the workflow that lets a small team keep shipping without the codebase rotting between releases.

---

## GDD-lite: the one-page design document

The traditional Game Design Document — 80 pages of speculative detail written before a single prototype exists — is dead, and deservedly so. Nobody reads it, nobody updates it, and by week three it describes a game that no longer exists. What replaced it in small-team practice is the **GDD-lite**: a single page that states the *invariants* of the project — the things that, if they changed, would make it a different game — and deliberately refuses to specify anything else.

### Why one page

A one-page document has three properties an 80-page document can never have:

1. **It gets read.** Every team member (and every future-you returning after a two-week break) can re-read it in three minutes before making a scope decision.
2. **It gets updated.** Updating one page after a design pivot takes five minutes, so it actually happens. The document stays true.
3. **It forces prioritization.** If everything fits on one page, you must decide what matters. The act of cutting is the act of designing.

### The template

Copy this into `docs/DESIGN.md` for any small project. Every field is mandatory; every field has a hard length limit.

```markdown
# <Project Name> — GDD-lite
Version: <n>  ·  Last updated: <date>  ·  Owner: <name>

## Pitch (1 sentence)
<Genre + fantasy + platform. If you need a second sentence, the idea
 is not clear yet.>

## Player & context (2-3 sentences)
<Who plays this, when, for how long per session, doing what else at
 the same time?>

## Core loop (3-5 bullet steps)
1. <verb> ...
2. <verb> ...
3. <verb> ... (loops back to 1)

## Pillars (exactly 3)
- <Pillar 1 — a quality every feature must serve>
- <Pillar 2>
- <Pillar 3>

## Must / Should / Could / Won't  (MoSCoW — see Module 10 §3)
MUST:   <the 3-6 features without which there is no game>
SHOULD: <features the first release wants but could ship without>
COULD:  <nice-to-haves, only if time remains>
WON'T:  <explicitly rejected ideas — the most important list>

## Technical constraints (bullets)
- Engine/version: Godot 4.5, GDScript 2.0
- Platforms: <e.g. Windows/Linux desktop>
- Performance budget: <fps focused / fps unfocused, RAM, startup time>
- Save format & compatibility promise: <e.g. JSON, migrations forever>

## Success criteria (measurable, 2-4 bullets)
- <e.g. "A new user decorates their first room within 5 minutes
   without a tutorial">
```

### Worked example — Relax Room *(case study)*

> **Case study — Relax Room.** The following is the actual GDD-lite of the course's running project, reconstructed from its design history. Note how much it *refuses* to say.

```markdown
# Relax Room — GDD-lite
Version: 4  ·  Last updated: 2026-04  ·  Owner: Renan

## Pitch
A desktop companion app where you decorate a cozy pixel-art room,
pick a character to inhabit it, and play ambient music while you
work or study.

## Player & context
Students and remote workers, 18-35, who keep the app open in a
corner of the screen (or behind other windows) during multi-hour
work sessions. Interaction bursts of 1-3 minutes; passive presence
for hours.

## Core loop
1. Open the app; the room, character and last playlist resume.
2. Occasionally interact: place/move decorations, change track,
   pet the cat.
3. Earn soft currency passively; spend it in the shop on new
   decorations.
4. Return tomorrow; everything is exactly as you left it.

## Pillars
- Calm: nothing flashes, nothing demands, nothing punishes.
- Persistence: the room NEVER forgets — losing a save is a
  critical bug, not an inconvenience.
- Lightness: near-zero resource cost when unfocused; the app is a
  guest on the user's machine.

## MoSCoW
MUST:   room + themes, character selection, decoration placement
        with grid snap, music player, save/load, shop with soft
        currency.
SHOULD: cat companion, multiple rooms, settings panel (volume,
        autosave interval).
COULD:  seasonal decoration sets, day/night ambient shift.
WON'T:  multiplayer, accounts/social features, mobile port,
        mini-games, notifications that interrupt the user.

## Technical constraints
- Godot 4.5 / GDScript 2.0, desktop only (Windows first).
- 60 FPS focused, throttled when unfocused; < 200 MB RAM;
  < 3 s cold start.
- JSON save with versioned migration chain (v1 → current, forever).

## Success criteria
- First-session decoration placed within 5 minutes, no tutorial.
- Zero save-loss bug reports across a release cycle.
- CPU usage below 1% when the window is unfocused.
```

The **WON'T list is the load-bearing wall** of this document. Every "wouldn't it be cool if…" conversation in the project's history ended in one of two ways: the idea served a pillar and entered COULD, or it collided with the WON'T list and died in thirty seconds instead of thirty days. Multiplayer alone — rejected in the WON'T list on day one — would have consumed the entire team for a semester and violated all three pillars.

> ✅ **Best practice** — Version the GDD-lite in Git next to the code, and bump its version number on every substantive change. When someone asks "why doesn't the app have notifications?", `git log docs/DESIGN.md` answers with the date and the reasoning. The document's history *is* the project's design history.

> ⚠️ **Pitfall** — A GDD-lite without measurable success criteria degenerates into vibes. "The game should feel relaxing" cannot fail, so it cannot guide. "CPU below 1% unfocused" can fail, so it forces the pause/focus work that actually delivers the relaxing feel. Write at least one criterion you could genuinely miss.

---

## Vertical slices, milestones and scope control

### Vertical slice thinking

A **vertical slice** is a thin, fully playable cross-section of the game: one path through the core loop, built to near-final quality, touching every layer of the stack — input, gameplay, UI, audio, persistence. It is the opposite of the **horizontal layer** approach ("first I'll build the whole save system, then the whole UI framework, then…"), which produces months of work with nothing playable.

```
HORIZONTAL layers (risky):            VERTICAL slice (safe):

  ┌──────────────────────────┐          ┌────┬─────────────────────┐
  │ UI framework (weeks 1-3) │          │ ░░ │                     │
  ├──────────────────────────┤          │ ░░ │   rest of the game  │
  │ Save system (weeks 4-6)  │          │ ░░ │   (built later,     │
  ├──────────────────────────┤          │ ░░ │    slice by slice)  │
  │ Audio engine (weeks 7-8) │          │ ░░ │                     │
  ├──────────────────────────┤          │ ░░ │                     │
  │ Gameplay?? (week 9+...)  │          │ ░░ │                     │
  └──────────────────────────┘          └────┴─────────────────────┘
  Playable: week 9 at best.            ░░ = ONE room, ONE character,
  Integration risk: everything         THREE decorations, ONE track,
  meets everything at the end.         save/load of exactly that.
                                       Playable: week 1-2.
```

The slice answers the questions that kill projects, and answers them early:

- **Is the core loop actually fun/pleasant?** If decorating one room with three items feels flat, no amount of content (more rooms, more items) will fix it. Content multiplies a feeling; it never creates one.
- **Does the architecture hold end to end?** The slice forces every system to talk to every other system once — signals, saves, UI, audio — while the codebase is still small enough to restructure in a day.
- **What does "done" cost?** After one slice you know your real velocity: how long "one decoration, art to shipped" takes. Every estimate afterward stands on measured ground instead of optimism.

For Relax Room, the first vertical slice was: *one room, one character, three placeable decorations with grid snap, one music track, save and reload of exactly that state*. It took two weeks. The shop, the currency, the second character, the cat, the themes — all of it came later, and every one of those features slotted into an architecture the slice had already proven.

> ✅ **Best practice** — Define the slice in writing before building it, and include persistence from day one. A slice that does not save and reload is a demo, not a slice — save/load is where architectures actually break, and discovering that in week 2 costs a refactor; discovering it in month 4 costs a rewrite. See [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md).

### MoSCoW prioritization

MoSCoW — **M**ust, **S**hould, **C**ould, **W**on't — is the lightest prioritization scheme that still works, which makes it the right one for a small team. The rules that keep it honest:

| Category | Definition | Discipline rule |
|---|---|---|
| **Must** | Without this, there is no product. | Maximum 6 items. If you have 10 "musts", you have 4 lies. |
| **Should** | The release wants this, but could ship without it, embarrassed. | Each item names the Must it supports. |
| **Could** | Genuinely optional polish. | Never scheduled — pulled in only when a milestone finishes early. |
| **Won't** | Explicitly rejected (for this release or forever). | Written down *with the reason*, so the argument never repeats. |

The categories are per-release, not per-project: after shipping 1.0, the next cycle re-runs MoSCoW from scratch, and yesterday's Won't may become tomorrow's Should. What never changes is the discipline: **new ideas enter the list, not the sprint.** When inspiration strikes mid-week ("what if the cat reacted to the music?!"), it gets one line in the Could column and you go back to what you were doing. The idea will still be good on Monday; most of the time, it will visibly *not* be good on Monday, which is the point.

### Milestone maps

A milestone map is MoSCoW stretched over time. Each milestone is a named, *demonstrable* state of the game — not a percentage, not a list of tasks, but something you could put in front of a stranger:

```
M0  "Slice"        (wk 1-2)  One room/character/track; 3 decorations;
                             save + reload works.               [MUST]
M1  "Livable"      (wk 3-5)  Full decoration catalog loads from JSON;
                             shop buys/places; currency persists. [MUST]
M2  "Companion"    (wk 6-8)  Unfocused throttling; autosave; window
                             position remembered; music resumes.  [MUST]
M3  "Cozy"         (wk 9-11) Second room + themes; cat; settings
                             panel; save migration v1→v2 tested. [SHOULD]
M4  "Ship 1.0"     (wk 12-14) Export pipeline, crash-free soak test
                             (8 h), itch.io page, versioned build. [MUST]
                             → deep dive in BUILD_AND_EXPORT.md
```

Three properties make a milestone map useful instead of decorative:

1. **Every milestone is playable.** "Refactor the audio system" is not a milestone; it is a task inside one. If you cannot demo it, it does not close.
2. **Musts front-load; Shoulds live late.** When (not if) the schedule slips, you cut from the end of the map — and the end is where the cuttable things already are.
3. **Dates are honest ranges, revised at every close.** A milestone map that still shows January's dates in April is a museum piece.

### Scope control: the companion-app philosophy

The single most common cause of dead hobby projects is not lack of skill — it is scope. The "companion app" framing of this course is itself a scope-control decision, and it generalizes: **choose a product category whose minimum viable version is small.** A desktop companion has no levels to design, no difficulty curve to balance, no content treadmill; its core promise (be pleasant, be persistent, be light) is achievable by one person in one semester. An RPG's minimum viable version is a year of work *before* you learn whether anyone wants it.

Practical scope-control rules for solo and small-team work:

- **The feature budget is a number.** Decide "1.0 ships with at most N features" and treat N as fixed. New idea in? An old idea goes to the next release. Trading is allowed; growing is not.
- **Every feature pays rent forever.** A feature is not just its build cost — it is its test cost, its save-format cost, its interaction cost with every future feature. The shop panel costs a week to build and then appears in every regression pass, every save migration and every UI refactor, forever. Evaluate features at lifetime cost.
- **Kill features that fight the pillars.** Relax Room's WON'T list rejected notifications because a companion that interrupts violates *Calm* — even though notifications are cheap to build. Cheap-but-wrong is still wrong.
- **Prefer depth over breadth in content.** Ten decorations with placement polish (snap, rotate, layering feedback) beat forty decorations that plop. Content breadth is the easiest thing to add later and the most tempting thing to add too early.

### Estimation honesty: the ×2-3 rule

Software estimation research and thirty years of postmortems agree: developers systematically estimate the *typing time* of the happy path and forget everything else — integration, edge cases, art wrangling, the save-format change, the bug the feature reveals in older code, the playtest that sends it back. The correction is not to estimate harder; it is to apply a measured multiplier.

**The rule:** produce your gut estimate, then multiply by 2 for familiar work and by 3 for anything involving a system you have not built before. Do this openly and without shame.

```
Gut feeling                     Honest schedule entry
"The shop panel is 2 days"  →   4-6 days   (UI is never 2 days)
"Save migration, half a day" →  1-1.5 days (write it + test the chain)
"Just add cat animations"    →  3-6 days   (first time syncing
                                            AnimationPlayer to state?
                                            ×3 applies)
```

Then close the loop: **record actuals.** A simple log turns your personal multiplier from folklore into data within a month:

```markdown
# docs/ESTIMATES.md — append one row per finished card
| Card                    | Gut  | Scheduled (×) | Actual | Notes                |
|-------------------------|------|---------------|--------|----------------------|
| shop panel: purchase UI | 2 d  | 4 d (×2)      | 5 d    | FileDialog detour    |
| save migration v2       | 0.5 d| 1 d (×2)      | 1 d    | fixture test caught 1|
| cat idle animations     | 2 d  | 6 d (×3)      | 4 d    | ×3 was generous      |
| focus throttling        | 1 d  | 3 d (×3)      | 6 d    | OS sleep = new system|
```

Most developers discover two things within a month of logging: their true multiplier is embarrassingly stable, and the *outliers* cluster — always the tasks that touched a system they had never built before (the `focus throttling` row above). Both discoveries transform milestone maps from fiction into forecasts: the multiplier calibrates ordinary cards, and "is this a first-time system?" becomes the explicit question that decides between ×2 and ×3. Review the log at every milestone close, next to the map it feeds.

> ⚠️ **Pitfall** — Do not "fix" a slipping milestone by working nights. Overtime at week 6 is a loan against week 8 taken at predatory interest: velocity drops, bug rates rise, and the schedule ends up *later* than if you had cut a Should instead. The milestone map has a designated crumple zone — use it. Scope is the variable; health is not.

### Playtesting cadence

Playtesting is planning's feedback loop, and it needs a *cadence* — a fixed rhythm, not "when it feels ready" (it never feels ready):

| Cadence | Who plays | What you learn | Cost |
|---|---|---|---|
| **Daily** (5 min) | You | Does the build run? Does the loop still feel right after today's changes? | Free — it is your smoke test |
| **Per milestone** | The team + 1-2 outsiders | Does the milestone's promise hold for someone who did not build it? | An hour of watching, silently |
| **Per release** | 5-8 strangers | First-session experience, onboarding, the success criteria from the GDD-lite | Half a day, structured notes |

The iron rule of watching a playtest: **do not talk.** The moment you explain ("oh, you have to click the shop icon first"), you have destroyed the data. Write down where they stumble, what they never find, when they smile, when they check their phone. Structure the notes so sessions compare across testers and across builds:

```markdown
# Playtest notes — build v0.3.0 · tester P4 · 2026-07-14 · 25 min
FIRST 5 MIN (unprompted): found decorations at 1:40; tried to DRAG the
  shop items directly into the room (twice) before finding "buy" — friction
STUMBLES: volume slider assumed to be under the music panel, is in settings
NEVER FOUND: character switcher (session ended without it)
DELIGHT: laughed when the cat stretched (3:12); screenshotted the room
QUOTES (verbatim): "wait, did it save my room? oh nice, it did"
TASK RESULT: GDD-lite criterion "first decoration < 5 min" → PASS (1:40)
FOLLOW-UP QUESTIONS (asked AFTER, never during): would you keep it
  open while working? what would you remove?
```

Aggregate after 4-5 sessions, not after each one — a single tester's stumble is an anecdote; the same stumble in four sessions is a design bug with a priority. The drag-to-buy note above, repeated across testers, is how a "shop UX rework" card earns its way into a milestone over the builder's objection that "it's obvious."

For a companion app, add a cadence the genre demands: leave the build running on a teammate's machine for a full workday and interview them at the end — *did you notice it? did it annoy you? did it survive your laptop's sleep cycle?* That last question finds more companion-app bugs than any unit test.

---

## The pre-modification checklist

Planning the project is strategy; planning a *change* is tactics, and it is where daily discipline lives or dies. The pre-modification checklist is this module's oldest artifact, preserved from the project's earliest process document and expanded with three principles that deserve names: **blast radius**, **read before writing**, and **reproduce before fixing**.

### The checklist

**Before changing ANY code**, answer these questions — in writing for non-trivial changes, in your head for one-liners (but honestly, even then):

```
□ 1. WHAT exactly am I changing?
     Write a one-sentence description. If the sentence contains
     "and", it is two changes — split them.

□ 2. WHY am I changing it?
     Bug fix? New feature? Refactor? Performance? Pick ONE.
     A commit that fixes a bug AND refactors is a commit that
     cannot be reviewed and cannot be safely reverted.

□ 3. WHERE does this code connect to other code? (BLAST RADIUS)
     What signals does it emit or listen to?
     What functions does it call, and who calls it?
     What scenes instantiate it, what autoloads does it touch?
     What files reference it? (Ctrl+Shift+F is your friend.)

□ 4. WHAT could break?
     List 3 concrete things that might go wrong.
     If you cannot think of any, you do not understand the code
     well enough yet — go back to step 3.

□ 5. HOW will I verify it works?
     Write the test steps BEFORE making the change.
     "Run the app and click around" is NOT a test plan.

□ 6. CAN I revert easily?
     Did I commit my current work first?
     Am I on a feature branch?
     If either answer is no, STOP and fix that first.
```

### Blast radius: understanding what a change touches

Every change has a **blast radius**: the set of code, scenes, data and saved state whose behavior can differ after the change. In an ordinary program the radius is mostly visible in the call graph. In a Godot project it hides in four extra places, which is why step 3 deserves its own discipline:

1. **Signal connections.** A change to what `SignalBus.decoration_placed` carries silently affects every listener — and `connect()` calls are scattered across the codebase. Search for the signal name, not the function name.
2. **Scene instantiation.** A script edit changes behavior in *every* scene that instantiates the scene it belongs to, including scenes you have not opened this month. Search for the `.tscn` filename.
3. **Exported variables.** Renaming or retyping an `@export` silently orphans the values stored in every `.tscn` that set it. The scene file keeps the old property; the script no longer reads it; nothing errors. This is a classic invisible break.
4. **Saved data.** Any change to what gets serialized touches every existing save file in the wild. The blast radius of a save-format change is *your entire user base's disk*.

A useful habit: before editing a file, spend two minutes producing a "radius note" — three lines listing inbound (who uses this), outbound (what this uses), and persisted (what this writes). For `room_base.gd` in Relax Room a radius note looks like:

```
INBOUND:  instanced by main.tscn; menu preloads it for transitions
OUTBOUND: connects to SignalBus (character_changed, decoration_placed,
          load_completed); calls SaveManager.request_save()
PERSISTED: writes decoration positions into the save dict ("decorations")
```

Two minutes of radius note routinely converts "quick change" into "oh — this needs a migration and a test," which is exactly the conversion that saves releases.

### Read before writing

The second principle: **never edit code you have not read in its current form** — not the form you remember, the form on disk today. Memory of code decays fast, and teammates (or last month's you) change things. Concretely:

- Read the *whole function* you are editing, not just the lines you plan to touch. Half of "mystery regressions" are edits that violated an invariant established four lines above the edit.
- Read the `_ready()`/`_exit_tree()` pair of any node script you touch — lifecycle assumptions live there, and in Godot they are where cleanup bugs breed (see the signal-disconnection entries in the [mistake catalogue](#the-mistake-catalogue)).
- Skim the scene file (in the editor, or the `.tscn` in a text view) for the node the script drives: exported values set in the scene override script defaults, and editing a default that the scene overrides does nothing — a ten-second check that saves an hour of confusion.

### Reproduce before fixing

The third principle applies to every bug fix: **a bug you cannot reproduce is a bug you cannot verify fixing.** The workflow:

1. **Make it happen on demand.** Find the exact steps, data, and timing. "Sometimes the music stops" is a report; "the music stops when you change rooms during the crossfade" is a bug.
2. **Shrink the reproduction.** Remove steps until removing anything more makes the bug vanish. The minimal repro usually *names the cause* — if the crossfade step is required, the bug lives in the tween lifecycle.
3. **Write the repro into the test plan** from checklist step 5, and where feasible into an automated test that fails before your fix and passes after (see [Writing tests with GUT and GdUnit4](#writing-tests-with-gut-and-gdunit4)).
4. Only now, fix it.

Fixing without reproducing produces the most demoralizing category of bug report: "still happening in the new version." You did not fix the bug; you changed code near where you imagined the bug was, and shipped your imagination.

### Worked example *(case study — Relax Room)*

> **Case study — Relax Room.** The checklist as actually filled in for a real change from the project's audit cycle (finding A1: signals never disconnected).

**Task:** add `_exit_tree()` to `room_base.gd` to disconnect signals.

```
1. WHAT: Add an _exit_tree() function that disconnects the three
   SignalBus connections made in _ready().
2. WHY: Bug fix — signal connections survive scene changes and stack
   up on every room switch (audit finding A1).
3. WHERE (blast radius): room_base.gd connects to 3 SignalBus signals
   in _ready(): character_changed, decoration_placed, load_completed.
   Inbound: main.tscn instantiates rooms; menu triggers room swaps.
   Persisted: none — pure lifecycle change.
4. WHAT COULD BREAK:
   - Typo in a signal name → disconnect fails silently, leak remains.
   - Forgetting one of the three signals → partial fix that LOOKS done.
   - Disconnecting a never-connected signal (early exit path) → error;
     guard with is_connected().
5. HOW TO VERIFY:
   - Switch rooms back and forth 5 times.
   - Console must show zero "already connected" warnings.
   - Remote tab: no orphaned nodes; connection count on SignalBus
     stays constant across switches.
6. REVERT: Current work committed; on branch feature/exit-tree-fix. Yes.
```

Total cost of filling this in: four minutes. It caught, in item 4, the `is_connected()` guard that the first draft of the fix lacked — which would have shipped a new error to fix the old leak.

### The complete modification workflow

The checklist is step one of a larger loop. Preserved from this module's original process document, here is the full workflow for making *any* change to the codebase — the checklist, version control (§5-7), testing (§10-13) and review (§9) composed into one picture:

```
┌──────────────────────────────────────────────────────────┐
│                 MODIFICATION WORKFLOW                    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1. UNDERSTAND                                           │
│     ├── Read the relevant code (current form, not memory)│
│     ├── Trace signal connections (search the signal name)│
│     ├── Check the audit report / debt register for       │
│     │   related known issues                             │
│     └── Answer the Pre-Modification Checklist            │
│                                                          │
│  2. PREPARE                                              │
│     ├── Pull latest changes from the trunk               │
│     ├── Create a feature branch: git checkout -b feat/x  │
│     ├── Confirm the test suite passes BEFORE you start   │
│     │   (a red baseline poisons every later conclusion)  │
│     └── Commit current state — clean rollback point      │
│                                                          │
│  3. IMPLEMENT                                            │
│     ├── Make the smallest possible change                │
│     ├── Test after each logical step (F5 + suite)        │
│     ├── Commit each working step (one intention each)    │
│     └── Write/update tests for the new behavior          │
│                                                          │
│  4. VERIFY                                               │
│     ├── Run the full suite headless                      │
│     ├── Run the game and follow YOUR test plan (step 5   │
│     │   of the checklist — written before coding)        │
│     ├── Output panel: zero new warnings or errors        │
│     └── Remote tree: no leaked nodes, no stale signal    │
│         connections after a scene switch                 │
│                                                          │
│  5. SUBMIT                                               │
│     ├── Push the branch; open a PR with description      │
│     │   (+ the filled checklist, for risky changes)      │
│     ├── Justify every scene file in the diff (§6)        │
│     └── Request review; address feedback with new        │
│         commits, not force-pushes over history           │
│                                                          │
│  6. MERGE                                                │
│     ├── Review approved + CI green (both required)       │
│     ├── Merge to the trunk; delete the branch            │
│     └── Watch the post-merge CI run — a merge is not     │
│         done until main is proven green                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

Steps 1-2 are minutes, not ceremony — and they are precisely the minutes that the cost-escalation curve in §1 repays at 10:1. The workflow's deeper effect is psychological: because every step ends in a committed, verified state, *interruption is always safe*. A solo developer who can stop mid-feature on Tuesday and resume confidently on Saturday has solved the hardest scheduling problem hobby projects have.

> ✅ **Best practice** — For any change touching persistence or signals, the checklist is mandatory, written, and kept (paste it into the PR description). For cosmetic changes, run it mentally. The skill you are training is not form-filling; it is *reflexively seeing the blast radius* — after a few dozen written repetitions, the written form becomes optional because the habit has become permanent.

---

## Version control for Godot projects

Version control is not an administrative chore bolted onto game development — it is a *design tool*. A developer who can revert any experiment in ten seconds experiments constantly; a developer whose only undo is Ctrl+Z hoards a fragile working state and fears their own project. Everything in this section serves that one goal: **make reverting so cheap that trying things becomes free.**

Godot is unusually friendly to version control among game engines: scenes (`.tscn`) and resources (`.tres`) are text by default, the project file is text, and the engine deliberately aims to generate "mostly readable and mergeable files." But Godot 4 also has sharp edges that generic Git knowledge does not cover — the `.godot/` cache folder, the `.import` metadata files, and the fragility of scene merges. Get these right on day one; retrofitting them onto a repository with history is miserable.

### The .gitignore for Godot 4

The single most important fact in this section: **Godot 4 keeps its per-machine cache in the `.godot/` folder, and that folder must never be committed.** It contains imported asset artifacts, compiled shader caches, the global script class cache and editor metadata — all of it regenerable, all of it machine-specific, much of it binary, and some of it changing on every editor launch. Committing it bloats the repository, generates permanent merge conflicts, and can corrupt teammates' editors.

The canonical minimal `.gitignore` for a Godot 4.1+ project, per the official documentation:

```gitignore
# Godot 4 — per-machine cache and generated data. NEVER commit.
.godot/

# Binary translations imported from CSV (regenerated on import).
*.translation

# --- Project-specific additions (typical) ---

# Exported builds
build/
export/
*.exe
*.pck

# OS noise
.DS_Store
Thumbs.db

# Secrets and local config
.env
*.local.cfg

# Local databases / test saves (Relax Room keeps dev saves out)
*.db
test_saves/
```

Since Godot 4.1, the Project Manager can generate `.gitignore` and `.gitattributes` for you when creating a project (the "Version Control Metadata: Git" option) — use it, then extend with the project-specific block.

A note on tooling: an official **Godot Git plugin** exists (installable from the Asset Library) that surfaces diffs, staging and commits inside the editor's Version Control dock — as of this writing it is the only built-in VCS integration option. It is pleasant for solo work; teams generally live in the terminal or a dedicated Git client anyway, because reviews, LFS and conflict resolution happen there. Either way the *repository rules* in this section are identical — the plugin is a viewport onto Git, not a different workflow.

### What to commit — the .import question

The most common Godot version-control confusion, answered precisely:

| Path | Commit? | Why |
|---|---|---|
| `*.import` files (next to each asset) | **YES** | Text metadata storing *how* to import the asset — compression, filters, mipmaps, the importer chosen. Without them, every teammate's machine re-imports with defaults and your carefully tuned settings vanish. |
| `.godot/` (includes `.godot/imported/`) | **NO** | The *results* of importing — machine-generated binary artifacts. Regenerated from the asset + its `.import` file on first open. |
| `.tscn`, `.tres`, `.gd`, `.gdshader` | **YES** | Your actual project. All text. |
| `project.godot`, `export_presets.cfg` | **YES** (presets: minus secrets) | Project settings are text and shared. If export presets contain signing credentials, split them out — see [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md). |
| Source art (`.psd`, `.aseprite`, `.blend1`) | Usually **NO** (or a separate LFS-backed assets repo) | Working files are huge and change constantly; commit the exported `.png`/`.wav` the game actually loads, keep sources in shared storage with its own history. |
| Exported builds | **NO** | Builds are artifacts of tags, produced by CI — see [Continuous integration overview](#continuous-integration-overview). |

The mental model: **commit inputs and recipes, ignore outputs.** The `.png` and its `.import` file are inputs and recipe; `.godot/imported/*.ctex` is output. A fresh clone plus one editor launch must reconstruct everything ignored.

> ⚠️ **Pitfall** — `git add .` after creating a project *before* writing `.gitignore` is how `.godot/` ends up in history. Removing it later requires `git rm -r --cached .godot/` plus a commit — and the blobs stay in history forever unless you rewrite it. Write the `.gitignore` in the very first commit, before anything else.

> ⚠️ **Pitfall** — Deleting an asset without deleting its `.import` file leaves an orphan that confuses both Git status and teammates. Move/delete assets *inside the Godot editor's FileSystem dock*, which handles the `.import` file and fixes `res://` references in scenes; a plain file-manager delete does neither.

### Binary assets and Git LFS

Git stores every version of every file. For text this is nearly free (deltas compress beautifully); for binary assets it is catastrophic:

```
The arithmetic of naive binary storage:

  40 MB of sprites and audio  ×  50 revisions over the project
  = up to 2 GB of repository that every clone downloads, forever.

The same history under Git LFS:

  Repository stores 50 tiny text pointers per file;
  clone downloads only the CURRENT version of each binary (~40 MB).
```

**Git LFS (Large File Storage)** replaces tracked binaries with text pointers in Git while storing content on an LFS server (GitHub, GitLab and most forges include LFS storage with quotas). The official Godot documentation recommends setting up LFS *before* your first commit of binary assets — migrating existing history into LFS is possible (`git lfs migrate`) but rewrites history.

Setup, once per machine and once per repository:

```bash
# Once per machine
git lfs install

# Once per repository — track by extension (writes .gitattributes)
git lfs track "*.png" "*.jpg" "*.webp"
git lfs track "*.wav" "*.ogg" "*.mp3"
git lfs track "*.ttf" "*.otf"
git lfs track "*.glb" "*.blend"

# The .gitattributes file this generates IS the configuration — commit it.
git add .gitattributes
git commit -m "chore: track binary assets with Git LFS"
```

The resulting `.gitattributes` also lets you mark Godot's *binary* resource formats, should any appear, and declare merge behavior for scene files (next section):

```gitattributes
# Binary assets → LFS
*.png filter=lfs diff=lfs merge=lfs -text
*.wav filter=lfs diff=lfs merge=lfs -text
*.ogg filter=lfs diff=lfs merge=lfs -text
*.ttf filter=lfs diff=lfs merge=lfs -text

# Godot binary resources (if ever used) → LFS too
*.scn  filter=lfs diff=lfs merge=lfs -text
*.res  filter=lfs diff=lfs merge=lfs -text

# Godot text formats: treat as text, but never auto-merge scenes
*.tscn text eol=lf merge=binary
*.tres text eol=lf merge=binary
*.gd   text eol=lf
```

That `merge=binary` line on `.tscn`/`.tres` is a deliberate, opinionated choice explained in the next section: it forces Git to *stop pretending it can merge scenes* and surface the conflict to a human immediately.

> ✅ **Best practice** — For a small project like Relax Room (pixel art, short audio loops, total assets under ~100 MB), plain Git without LFS is survivable — pixel-art PNGs are tiny. Adopt LFS anyway if the repository lives on a forge with clone-size limits, if audio grows past a handful of tracks, or the moment anyone says the words "high-resolution" or "video". The cost of adopting LFS early is one command; the cost of adopting it late is a history rewrite.

---

## Scene merges and team workflows

### Why scene files merge badly

A `.tscn` file is text, and Git will happily line-merge it. This is a trap. The format is a serialized graph — node declarations, resource headers with *positional indices*, and connection records:

```
[gd_scene load_steps=4 format=3 uid="uid://cx1nv download"]

[ext_resource type="Script" path="res://scripts/rooms/room_base.gd" id="1_a2bc4"]
[ext_resource type="Texture2D" path="res://assets/sprites/sofa.png" id="2_x8yz1"]

[node name="Room" type="Node2D"]
script = ExtResource("1_a2bc4")

[node name="Sofa" type="Sprite2D" parent="."]
position = Vector2(212, 388)
texture = ExtResource("2_x8yz1")

[connection signal="pressed" from="UI/ShopButton" to="." method="_on_shop_pressed"]
```

Two developers each add a node to the same scene. Both diffs are clean insertions; Git merges them without a textual conflict — and the result can be a scene where `load_steps` is wrong, two `ext_resource` entries share an id, or a node references a parent path the other branch renamed. The file is *syntactically merged and semantically corrupt*, and you discover it when Godot fails to open the scene. **A textually successful merge of a .tscn is not evidence of a correct merge.**

This is why the `.gitattributes` above declares `merge=binary` for scenes: it converts silent corruption into an honest conflict ("both modified: main.tscn — choose one"), which a human resolves by taking one side and *re-applying* the other side's change in the editor. Re-doing two minutes of editor work beats debugging a corrupt scene graph every single time.

### Scene ownership: the workflow that prevents conflicts

Since scene merges cannot be trusted, the professional answer is to make them *rare* through workflow rather than tooling:

1. **One scene, one owner per task.** Before starting work, claim the scenes you will touch ("today I'm in `music_panel.tscn` and its script") in the team channel or on the kanban card. Two people never edit the same scene in the same window of time. This is the single highest-value rule in Godot team practice.
2. **Many small scenes beat one big scene.** A `main.tscn` containing the whole game is a permanent conflict magnet. Decompose aggressively into sub-scenes ([SCENES_AND_NODES.md](SCENES_AND_NODES.md)): if the shop panel is `shop_panel.tscn`, the shop developer and the room developer never collide. Scene granularity is *also* a team-scalability decision.
3. **Logic in scripts, structure in scenes.** A `.gd` file merges like any source code — well. Every behavior you move from scene-embedded configuration into a script shrinks the unmergeable surface. Keep scenes as thin structure + wiring; keep decisions in code.
4. **Merge trunk into your branch daily.** Scene conflicts grow with divergence time. A branch that rebases or merges from the trunk every morning meets one small conflict at a time, in code you both still remember; a two-week branch meets an archaeology project.
5. **Only edit scenes in the Godot editor.** Hand-editing `.tscn` in a text editor invites id collisions and count mismatches. The one exception: *reading* scene diffs, which is a skill worth having —

### Reading a scene diff

Reviewing a PR that touches scenes means reading `.tscn` diffs. They are more legible than they look; you are checking five things:

```diff
 [node name="Sofa" type="Sprite2D" parent="."]
-position = Vector2(212, 388)
+position = Vector2(212, 402)
+rotation = 0.087
```

- **Property changes** (like the above): usually intentional editor tweaks. Ask: did the author *mean* to move the sofa 14 px, or did they nudge it accidentally while testing? Accidental scene touches are the most common noise in Godot PRs.
- **`ext_resource` additions/removals:** new dependencies of the scene. A removed `ext_resource` still referenced below = broken scene.
- **Node renames** (`name="..."`): blast radius! Any `$Path/To/Node` or `get_node()` string in scripts, and any `[connection ...]` line, that used the old name silently breaks.
- **`[connection ...]` lines:** signal wiring added or removed in the editor. Verify each against the script — a deleted connection line is a feature that stops firing with no error at all.
- **`uid="uid://..."` churn:** Godot assigns stable UIDs to resources; spurious UID changes usually mean a file was deleted and recreated rather than moved, which breaks references elsewhere.

> ✅ **Best practice** — Before committing, run `git diff --stat` and *justify every scene file in the list*. If `settings_panel.tscn` appears in a commit about the shop, you almost certainly opened it, nudged something, and saved reflexively. `git checkout -- path/to/scene.tscn` (or `git restore`) discards the accidental touch. A commit's scene list should read like its description.

### Communication rules for shared repositories

The remaining conflict sources are social, and so are their fixes — preserved from this module's original workflow rules and still true:

```
1. ANNOUNCE     "I'm working on audio_manager.gd and music_panel.tscn
                 today" — one chat line prevents one merge conflict.
2. SMALL COMMITS Merge frequently; never let a branch diverge > 2-3 days.
3. FILE OWNERSHIP One person per file per task window.
4. NO DRIVE-BY REFORMATTING Don't reformat files you aren't changing —
                 it turns a 5-line diff into a 500-line review.
5. RESOLVE TOGETHER When a real conflict happens: read BOTH versions,
                 understand BOTH intents, combine manually, then TEST.
                 Never resolve by reflex-picking "mine" or "theirs".
```

---

## Branching models, commits and tagging

### Choosing a branching model

Branching models exist on a spectrum from "everyone on main" to full GitFlow. The right choice depends on project lifetime and team size — and choosing too much model is as harmful as choosing too little:

| Model | Shape | Right for | Wrong for |
|---|---|---|---|
| **Trunk-based** | Everyone commits to `main`; work is small and continuous; broken `main` is fixed within minutes | Game jams, solo prototypes, the vertical-slice phase | Teams that can't test before pushing; anything with releases to protect |
| **Feature branches** (GitHub flow) | `main` always works; every change is a short-lived branch + PR + review + merge | Small teams (2-6), long-lived projects — **the course default** | 48-hour jams (review overhead eats the jam) |
| **GitFlow (full)** | `develop` + `main` + release branches + hotfix branches | Studios juggling multiple supported releases simultaneously | Small teams — the ceremony outweighs the safety |

For a game jam: trunk-based, commit every 30-60 minutes, and tag the last known-good build before any risky experiment (`git tag jam-hour-30-works`) so the final hour is never spent bisecting. For Relax Room and projects like it: feature branches with a lightweight review, plus release tags on `main`.

```
Feature-branch flow (course default):

main ───●───────●───────────●──────────●────▶  always releasable
         \     / \         /          /
          \   /   \       /          /
   feature/exit-tree  feature/shop-panel   hotfix/save-crash
     (1-3 days max)     (1-3 days max)       (hours)
```

Two rules make the model work regardless of which you chose:

1. **`main` is sacred.** It builds, it runs, its tests pass — *always*. Anyone can demo from `main` at any moment. The instant `main` breaks, fixing it outranks all feature work, because a broken main multiplies: every branch cut from it inherits the breakage.
2. **Branches are short-lived.** A feature branch is a workspace, not a home. If a feature genuinely needs two weeks, slice it into independently mergeable stages (add the data model → merge; add the UI → merge; wire them → merge), each of which leaves `main` working. Long-lived branches are where merge disasters incubate.

### Commit message conventions

Preserved and formalized from the original module — the project uses **Conventional Commits** style:

```
<type>: <what changed and why>

Good:
  feat: add _exit_tree() to room_base.gd for signal cleanup
  fix: resolve FileDialog memory leak in music_panel.gd (audit A7)
  refactor: extract catalog loading from GameManager into CatalogLoader
  docs: add ADR-0003 on JSON-over-SQLite save decision
  test: add round-trip tests for SaveManager migration chain
  chore: add gdlint/gdformat to pre-commit and CI

Bad:
  "fixed stuff"        "updates"        "WIP"
  "asdfgh"             "changed some things"
```

| Type | When to use |
|---|---|
| `feat` | New feature or player-visible functionality |
| `fix` | Bug fix (reference the issue/audit id when one exists) |
| `refactor` | Restructuring with **no behavior change** |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `chore` | Build, CI, dependencies, tooling |
| `style` | Formatting/whitespace only (ideally: only ever gdformat commits) |

The discipline encoded here is more valuable than the format: **one type per commit means one intention per commit.** A commit that is `feat` *and* `refactor` cannot be reverted without collateral damage, and cannot be reviewed without untangling. When you notice mid-feature that a refactor is needed, stash the feature, commit the refactor separately, unstash, continue.

The golden rules, preserved:

```
1. COMMIT OFTEN — small, focused commits are easy to review and revert
2. PULL BEFORE PUSH — always
3. NEVER COMMIT SECRETS — no passwords, API keys, .env files;
   once pushed, a secret is COMPROMISED (history is forever) — rotate it
4. WRITE MEANINGFUL MESSAGES — your future self is the audience
5. ONE LOGICAL CHANGE PER COMMIT — "everything I did this week" is
   not a commit, it's a hostage situation
6. NEVER FORCE-PUSH main — ever, for any reason
7. REVIEW BEFORE MERGING — even your own code, even solo (read the
   full diff on the PR page; you will catch something)
```

### The pre-commit checklist

Preserved (and translated) from the project's original working rules — the concrete, print-it-out companion to the commit conventions above. Before every `git commit`:

```text
CODE
[ ] gdlint scripts/ runs clean?
[ ] gdformat --check scripts/ runs clean?
[ ] F5: the game starts with ZERO red errors in the Output panel?
[ ] Type hints complete on everything I touched? (vars, params, returns)

DATA
[ ] If I edited a JSON catalog (characters, decorations, rooms, tracks):
    - commas valid? (last entry of an object has NO trailing comma)
    - every sprite_path exists? (res://assets/sprites/...)
    - structure matches the other entries? (same fields, same types)

GIT
[ ] Commit message follows <type>: <what and why>?
[ ] No sensitive files staged? (.env, *.db, credentials)
[ ] No .godot/ staged? (git status — if present: git reset HEAD .godot/)
[ ] I re-read the full diff (git diff --staged) before committing?

SIGNALS
[ ] Every connect() I added in _ready() has its disconnect()
    in _exit_tree() (or CONNECT_ONE_SHOT)?
[ ] Every new signal I emit is declared on its proper owner
    (local signal vs signal_bus.gd)?
```

Most of these lines are automatable — and should be: the CODE block becomes the pre-commit hook from §8, the `.godot/` line becomes the `.gitignore` from §5, the JSON block becomes the validating loader from §17. The checklist's printed form is the *transition tool*: it teaches the habits while the automation is being built, and afterward it shrinks to the lines only a human can check (did I re-read the diff?).

### Tagging builds

Every build that leaves your machine gets a tag — an immutable, human-named bookmark in history:

```bash
# Annotated tags (with message) — always, for releases:
git tag -a v0.3.0 -m "Milestone M2 'Companion': focus throttling + autosave"
git push origin v0.3.0

# List and inspect:
git tag -l "v*"
git show v0.3.0
```

Why this matters more in games than in most software: a playtester reports "the cat freezes after the shop opens" against *the build they have*, not against today's `main`. With tags, `git checkout v0.3.0` puts you inside exactly the code they are running; without tags you are debugging a ghost. Tags are also what CI builds from — a tag push is the standard trigger for the release pipeline ([BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md)) — and what changelogs are generated between (`git log v0.2.0..v0.3.0 --oneline`).

Name tags with SemVer (`v<major>.<minor>.<patch>` — semantics in [Documentation, releases and maintenance](#documentation-releases-and-maintenance)), plus freeform tags for jam checkpoints and experiments.

> ✅ **Best practice** — Adopt the release checklist habit *now*, at v0.x: tag → CI builds from the tag → the tagged commit's changelog entry is already written. If a release requires remembering manual steps, a release will eventually ship with one forgotten. Checklists beat memory; automation beats checklists.

---

## Code quality: style guide, gdlint and gdformat

Code style is not aesthetics — it is *load reduction*. A codebase with one consistent style lets every reader spend zero cycles on "how is this written" and all of them on "what does this do." The way to get consistency is never discipline (discipline runs out) but tooling: a formatter that makes style a non-decision and a linter that catches smells before review does.

### The official GDScript style guide, distilled

The Godot documentation ships an official GDScript style guide; the built-in editor and `gdformat` both follow it. The rules you will actually use daily:

| Element | Convention | Example |
|---|---|---|
| Files and folders | `snake_case` | `music_panel.gd`, `room_base.tscn` |
| Classes (`class_name`) | `PascalCase` | `class_name SaveManager` |
| Node names (in scenes) | `PascalCase` | `ShopButton`, `MusicPanel` |
| Functions and variables | `snake_case` | `func load_catalog()`, `var track_index` |
| Private members | `_leading_underscore` | `var _cache`, `func _rebuild()` |
| Signals | `snake_case`, **past tense** | `signal decoration_placed(id)` |
| Constants | `CONSTANT_CASE` | `const MAX_DECORATIONS := 200` |
| Enums | `PascalCase` name, `CONSTANT_CASE` members | `enum TrackState { STOPPED, PLAYING }` |
| Indentation | Tabs (editor default) | — |
| Line length | 100 columns guideline | — |

The file/folder `snake_case` rule is not cosmetic. Godot's virtual filesystem is case-sensitive even on Windows/macOS whose disks are not — a scene loading `res://Assets/Sofa.png` while the file is `assets/sofa.png` *works in the editor on Windows and breaks in the exported build*. All-lowercase naming makes the mismatch impossible. This is the official rationale, and it is one of those rules that costs nothing to follow and a release-day evening to violate.

Ordering inside a script (the style guide's canonical layout — `gdlint` enforces it):

```gdscript
class_name ShopPanel
extends PanelContainer
## Shop UI: lists the decoration catalog and emits purchase intents.
## (This ## doc comment appears in the editor help — see §18.)

signal purchase_requested(item_id: String)          # 1. signals
enum Tab { FURNITURE, PLANTS, AUDIO }               # 2. enums
const MAX_VISIBLE_ITEMS := 24                       # 3. constants
@export var start_tab: Tab = Tab.FURNITURE          # 4. exports
var _catalog: Array[Dictionary] = []                # 5. public, then private vars
@onready var _item_list: ItemList = %ItemList       # 6. @onready vars

func _ready() -> void: ...                          # 7. built-in overrides
func open_at(tab: Tab) -> void: ...                 # 8. public methods
func _rebuild_list() -> void: ...                   # 9. private methods
func _on_item_activated(index: int) -> void: ...    # 10. signal handlers
```

### godot-gdscript-toolkit: gdlint and gdformat

The community-standard tooling is **godot-gdscript-toolkit** (`gdtoolkit`, by Scony) — an independent Python package providing a GDScript parser, a linter (`gdlint`) and a formatter (`gdformat`). Install the Godot-4 line:

```bash
pip install "gdtoolkit==4.*"        # or: pipx install "gdtoolkit==4.*"

gdlint scripts/                     # lint a directory tree
gdformat scripts/                   # format in place
gdformat --check scripts/           # exit non-zero if anything WOULD change
                                    #   (this is the CI mode)
```

`gdlint` performs static analysis against configurable rules: naming conventions (all the tables above), function/file length limits, unused arguments, expression-not-assigned mistakes, ordering violations, and more. Configuration lives in a `gdlintrc`/`.gdlintrc` YAML file at the project root — `gdlint` searches upward from the working directory and uses the first one found:

```yaml
# .gdlintrc — Relax Room settings (start from defaults; loosen sparingly)
max-line-length: 100
max-file-lines: 600          # a script pushing this limit is a debt smell (§15)
max-public-methods: 20
function-name: "(_?[a-z][a-z0-9]*(_[a-z0-9]+)*|_on_[A-Za-z0-9]+(_[a-z0-9]+)*)"
disable:
  - class-definitions-order   # only if you have a documented reason!
```

`gdformat` is deliberately non-configurable in spirit (line length aside): like `black` in the Python world, its value is *ending formatting debates permanently*. You will dislike two or three of its choices for a week; then you will stop seeing formatting at all, which was the goal.

### Wiring the tools into the workflow

Tools that must be remembered get forgotten. Wire them into the three places code passes through:

**1. On save (editor/IDE).** The VS Code godot-tools ecosystem and editor plugins can run gdformat on save; even without that, a shell alias (`alias gdf='gdformat scripts/'`) run before committing does the job.

**2. Pre-commit hook.** The gdtoolkit repo ships pre-commit hooks; with the [pre-commit](https://pre-commit.com) framework:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Scony/godot-gdscript-toolkit
    rev: "4.3.2"            # pin the version your team installed
    hooks:
      - id: gdlint
      - id: gdformat
```

```bash
pip install pre-commit && pre-commit install
# from now on, every `git commit` lints and formats staged .gd files
```

**3. CI.** A lint job needs no Godot at all — it is pure Python, so it runs in seconds on any runner:

```yaml
# .github/workflows/ci.yml (lint job — full pipeline in §13)
lint:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.12" }
    - run: pip install "gdtoolkit==4.*"
    - run: gdlint scripts/
    - run: gdformat --check scripts/
```

> ⚠️ **Pitfall** — Introducing `gdformat` into an existing codebase creates one giant whitespace commit. Do it as a **single, isolated `style:` commit with zero logic changes**, announced to the team, with all open branches merged first. A format commit tangled with feature changes poisons `git blame` and makes that PR unreviewable. (Configure `git blame` to skip it afterward: put the commit hash in `.git-blame-ignore-revs` and set `blame.ignoreRevsFile`.)

> ✅ **Best practice** — Treat *warnings as errors* inside Godot too: Project Settings → `debug/gdscript/warnings` lets you escalate warnings (unused signals, shadowed variables, integer division, unsafe calls) so they fail loudly during development. The project rule from the original module still stands: **zero warnings in the Output panel during gameplay** — every warning is either fixed or explicitly acknowledged in code with a reason.

---

## Typing discipline and code review

### Static typing as bug prevention

GDScript 2.0 is optionally typed, and the option is not cosmetic. Typed GDScript catches a class of bugs at *parse time* that untyped code ships to users, gives the editor real autocompletion (which prevents the typo-in-string-API class of bugs), self-documents intent, and — as a bonus — runs faster, since the engine can skip runtime type checks and use typed instructions.

```gdscript
# UNTYPED — three latent bugs, all invisible until runtime:
var price = catalog[id]["price"]       # is price int? float? String?!
func apply_discount(p, pct):
    return p - p * pct / 100           # pct as 0.2 or 20? Nobody knows.

# TYPED — the same bugs become red squiggles before you even run:
var price: int = catalog[id]["price"]
func apply_discount(price: int, percent: float) -> int:
    return roundi(price * (1.0 - percent / 100.0))
```

The course's typing rules, in priority order:

1. **Every function signature is fully typed** — parameters and return, `-> void` included. Signatures are contracts; contracts in writing.
2. **Every `var` at class level is typed** — explicitly (`var hp: int = 10`) or via inference on an unambiguous literal (`var hp := 10`). Use `:=` only when the right-hand side makes the type obvious to a *reader*, not just to the compiler.
3. **Type your arrays**: `var decorations: Array[Decoration] = []` turns "why is there a String in here" from a 2 a.m. mystery into a compile error.
4. **Avoid `Variant` leaks at boundaries.** Data arriving from JSON or SQLite is untyped by nature ([DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md)); convert and validate it *at the loading edge*, so the rest of the codebase lives in a fully typed world.
5. **Prefer typed node references**: `@onready var _list: ItemList = %ItemList` — with the type stated, a scene rename that breaks the path fails loudly at load instead of `null`-ing silently until first use.

> ✅ **Best practice** — Enable Project Settings → `debug/gdscript/warnings/untyped_declaration` (and consider `unsafe_method_access`) early in a project's life. Retrofitting types onto 5,000 untyped lines is a week; keeping a typed codebase typed is free.

### Code review for Godot projects

Code review at small-team scale is not bureaucracy — it is the cheapest bug-finding tool you have (cheaper than testing: no code needs writing) and the only reliable knowledge-spreading tool (after reviewing the shop panel, a second person can maintain the shop panel). Solo developers review too: reading your own full diff on the PR page, one context switch away from the editor where you wrote it, reliably surfaces debug prints, dead code and accidental scene touches.

What makes reviewing *Godot* projects different is that half the change is not in scripts. The course review checklist:

```
GODOT CODE REVIEW CHECKLIST

Scripts (.gd):
□ Signatures and class-level vars fully typed?
□ Every connect() has a disconnect() path (_exit_tree or one-shot)?
□ No get_node() with fragile absolute paths ("/root/Main/...")?
□ No load()/preload() inside _process()?
□ Magic numbers promoted to named constants?
□ Errors handled at I/O edges (FileAccess/JSON/DB return checks)?

Scenes (.tscn diffs — see §6):
□ Every scene file in the diff justified by the PR description?
□ ext_resource adds/removes match intentional dependency changes?
□ Node renames: were $paths and [connection] lines updated?
□ No accidental property nudges (position drift, modulate resets)?

Signals & architecture:
□ New signals declared on the right owner (local vs SignalBus)?
□ Signal names past tense, payloads typed?
□ No new autoload that could have been a scene-local node? (AUTOLOAD_SAFETY.md)

Data & persistence:
□ Save-format change ⇒ migration + round-trip test present?
□ JSON catalog edits keep schema consistent with existing entries?

Process:
□ Commit messages typed (feat/fix/refactor/...), one intention each?
□ Tests updated/added for changed logic?
□ Pre-modification checklist answers in the PR description (for risky changes)?
```

What "reviewing the signal wiring" looks like in practice — the checklist's most Godot-specific line, applied to a real-shaped diff:

```diff
 [node name="ShopButton" type="Button" parent="UI"]
 text = "Shop"

-[connection signal="pressed" from="UI/ShopButton" to="." method="_on_shop_pressed"]
+[connection signal="pressed" from="UI/ShopButton" to="." method="_on_shop_toggled"]
```

```diff
 func _on_shop_pressed() -> void:
-    _shop_panel.visible = true
+func _on_shop_toggled() -> void:
+    _shop_panel.visible = not _shop_panel.visible
```

The reviewer's questions write themselves once you know to pair the two diffs: the scene connection and the script method changed *together* — good (a rename in only one file is the silent breakage from §6). But: does anything else call `_on_shop_pressed` by name (`call`, `Callable(self, "..."` strings survive renames unnoticed)? Does a second scene instance connect to the old method? Is toggle-on-press what the card actually asked for, or did behavior change inside a "rename" commit? Sixty seconds of paired reading; three classes of bug screened.

Review culture rules, preserved from the original module and worth restating: review the code, never the person; correctness and clarity outrank style preference (the formatter owns style now); every merge gets at least one review, even when it is your own second read; and a review that only says "LGTM" on a 400-line diff is a skipped review with extra steps — big diffs get either real time or a request to split.

---

## Testing in Godot 4: the landscape

"Games can't be unit tested" is a myth kept alive by studios that don't, and disproven daily by studios that do. The truth is narrower: *some parts* of a game resist automation (feel, fun, aesthetics), while others — data transformations, save/load, economy math, state machines — are ordinary software that tests beautifully. Strategy: **automate the automatable, spend the freed-up human attention on feel.**

### The testing pyramid, game edition

```
        ┌──────────────────────────────────────┐
        │        MANUAL PLAYTESTING            │  Slowest, most expensive,
        │  "Play it. Try to break it. Watch    │  irreplaceable for feel,
        │   a stranger play it."               │  UX and fun. (§12)
        ├──────────────────────────────────────┤
        │        SCENE / INTEGRATION TESTS     │  Instantiate real scenes,
        │  "Does placing a decoration emit     │  simulate input, await
        │   the signal, update the room AND    │  signals. Medium speed.
        │   survive a save/load round-trip?"   │  (§11)
        ├──────────────────────────────────────┤
        │        UNIT TESTS                    │  Milliseconds each. Pure
        │  "snap_to_grid(Vector2(15,7)) ==     │  logic, no scene tree
        │   Vector2(16,8)?"                    │  needed. The wide base.
        └──────────────────────────────────────┘
```

The pyramid's proportions are the message: many fast unit tests, fewer scene tests, a deliberate cadence of manual passes. Inverting it (all manual, no automation) means every release re-tests everything by hand — which means, in practice, that nothing is re-tested and regressions ship.

### What to test — and what not to

Preserved from the original module, because it is the highest-value list in this section:

```
ALWAYS automate:
  ✓ Data transformations (snap_to_grid, coordinate conversions, formatting)
  ✓ Save/load round-trips (save → load → every field matches)
  ✓ Migration chains (v1 save file → current version, no data loss)
  ✓ Economy/business logic (prices, currency earn rates, purchase gates)
  ✓ Edge cases (empty arrays, missing keys, boundary values, malformed JSON)
  ✓ State machines (track player states, shop tab logic)
  ✓ Regression tests for every bug you fix (the bug's repro, automated)

DON'T automate:
  ✗ Engine internals (Button.pressed fires — Godot tests Godot)
  ✗ Trivial getters/setters
  ✗ Visual appearance ("is the button blue?") — screenshots + eyes
  ✗ Third-party libraries (SQLite works — trust, or you own its test suite)
  ✗ Feel ("is placing decorations satisfying?") — humans only
```

The last "always" line deserves emphasis: **every fixed bug becomes a test.** You already built the reproduction while fixing it (§4); encoding it costs ten minutes and guarantees this particular bug can never return unnoticed. A test suite grown this way is automatically weighted toward the code that actually breaks.

### The autoload problem

One structural obstacle deserves naming before the frameworks do, because it shapes what is testable at all: **autoloads are global state, and global state is test poison.** An autoload initialized once per Godot process carries residue between tests — the wallet a purchase test charged is still charged when the next test runs, the signal a previous suite connected still fires. Three mitigations, in order of preference:

1. **Extract the logic; test the class, not the singleton.** `SaveManager` the autoload should be a thin lifetime wrapper around a `SaveLogic`/`ShopLogic` class that tests instantiate fresh (`ShopLogic.new()` in every §11 example is this pattern). The autoload is wiring; wiring gets scene tests, logic gets unit tests.
2. **Give stateful autoloads a `reset_for_test()`** that restores pristine state, called from `before_each`. Honest but smelly — the method exists only for tests, and forgetting to call it produces order-dependent failures that pass alone and fail in suite (the classic symptom from §14.5).
3. **Inject autoload dependencies** so tests can pass doubles instead of touching the real singleton at all (§11's doubles section). This is the same move [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) recommends for architecture reasons; testability and decoupling are the same property seen from two sides.

If a piece of code cannot be tested without booting half the game, that is not a testing problem — it is an architecture finding, and it belongs in the debt register (§15).

### GUT vs GdUnit4

Godot 4 has two mature, actively maintained testing frameworks. Both are free, MIT-licensed, installed as `addons/`, and CI-capable. The course uses **GUT** in examples for its lower ceremony, but both are excellent — this table is current as of mid-2026:

| | **GUT** (Godot Unit Test) | **GdUnit4** |
|---|---|---|
| Godot support | 9.x line for Godot 4.x (legacy 7.4.x for Godot 3) | v5/v6 lines for Godot 4.x (4.5+ on current releases) |
| Test style | `extends GutTest`; xUnit-flavored `assert_eq`, `assert_true`, ... | `extends GdUnitTestSuite`; fluent `assert_that(x).is_equal(y)` |
| Doubles/stubs/spies | Full & partial doubles, stubbing, spies | Mocking + spying, argument matchers |
| Signal testing | `watch_signals()` + `assert_signal_emitted()` | `assert_signal(obj).is_emitted("name")` with await support |
| Scene/input simulation | Scene instantiation helpers; input via `InputSender` class | Dedicated **Scene Runner**: simulated frames, mouse, keyboard, touch, actions |
| Parameterized tests | Yes | Yes (+ fuzzing: generated random inputs) |
| Flaky-test handling | — | Built-in retry policy for known-flaky tests |
| In-editor UI | Dock panel + VS Code extension | Embedded inspector panel |
| CLI / CI | `gut_cmdln.gd`, JUnit XML export, `.gutconfig.json` | `GdUnitCmdTool` / `runtest` scripts, JUnit XML + HTML reports, official GitHub Action |
| Personality | Minimal ceremony, quick start | More features, more structure |

Selection heuristics: choose **GUT** for a first test suite, small projects, and tutorials-to-production continuity; choose **GdUnit4** when you want its Scene Runner for heavy input-simulation tests, C# support (`gdUnit4Net` with IDE test adapters), or fluent-assertion style. Do not choose both in one project — one framework, adopted fully, beats two adopted halfway.

> ⚠️ **Pitfall** — Addon frameworks track engine releases; a Godot upgrade can break your test addon until its compatible release lands. Pin both: the engine version in the GDD-lite's technical constraints, the framework version in your README's setup section, and upgrade them *together, deliberately*, as a `chore:` commit that runs the full suite. (Relax Room learned this the hard way — see the case study in §19.)

---

## Writing tests with GUT and GdUnit4

### Installing a framework

Both frameworks install the same way: **AssetLib inside the editor** (search "GUT" or "GdUnit4", install, enable in Project Settings → Plugins, restart the editor), or manually by copying the release's `addons/gut/` or `addons/gdUnit4/` folder into your project. Commit the addon folder — the test framework is part of the project, and CI needs it in the repository. Conventional layout:

```
res://
├── addons/gut/            # the framework (committed)
├── scripts/               # production code
├── tests/
│   ├── unit/              # pure-logic tests, no scene tree needed
│   │   ├── test_helpers.gd
│   │   ├── test_save_migrations.gd
│   │   └── test_shop_economy.gd
│   └── integration/       # scene tests
│       ├── test_room_placement.gd
│       └── test_music_panel.gd
└── .gutconfig.json        # CLI defaults (dirs, exit behavior)
```

Keep `tests/` out of exported builds: export presets exclude it (an `export_presets.cfg` filter, or a dedicated exclusion — details in [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md)). Shipping your test suite to players is only embarrassing; shipping test *doubles* that shadow real classes is a bug.

### Unit tests for pure logic

The foundational example, in both dialects — a grid-snapping helper of the kind every placement system owns:

```gdscript
# scripts/utils/helpers.gd
class_name Helpers

const GRID_SIZE := 8.0

static func snap_to_grid(pos: Vector2) -> Vector2:
    return (pos / GRID_SIZE).round() * GRID_SIZE

static func array_to_vec2(a: Array) -> Vector2:
    if a.size() < 2:
        return Vector2.ZERO
    return Vector2(float(a[0]), float(a[1]))
```

```gdscript
# tests/unit/test_helpers.gd — GUT style
extends GutTest

func test_snap_rounds_to_nearest_cell() -> void:
    assert_eq(Helpers.snap_to_grid(Vector2(15, 7)), Vector2(16, 8))

func test_snap_leaves_exact_values_alone() -> void:
    assert_eq(Helpers.snap_to_grid(Vector2(16, 8)), Vector2(16, 8))

func test_array_to_vec2_happy_path() -> void:
    assert_eq(Helpers.array_to_vec2([100.0, 200.0]), Vector2(100, 200))

func test_array_to_vec2_empty_is_zero() -> void:
    assert_eq(Helpers.array_to_vec2([]), Vector2.ZERO)

# Parameterized: one test, a table of cases
func test_snap_cases(p: Array = use_parameters([
    [Vector2(0, 0), Vector2(0, 0)],
    [Vector2(3.9, 3.9), Vector2(0, 0)],
    [Vector2(4, 4), Vector2(8, 8)],       # .5 cells round up
    [Vector2(-5, -5), Vector2(-8, -8)],   # negative space works too
])) -> void:
    assert_eq(Helpers.snap_to_grid(p[0]), p[1])
```

```gdscript
# tests/unit/test_helpers.gd — the same in GdUnit4's fluent style
extends GdUnitTestSuite

func test_snap_rounds_to_nearest_cell() -> void:
    assert_that(Helpers.snap_to_grid(Vector2(15, 7))).is_equal(Vector2(16, 8))

func test_array_to_vec2_empty_is_zero() -> void:
    assert_that(Helpers.array_to_vec2([])).is_equal(Vector2.ZERO)
```

Note what makes this code *testable*: `Helpers` is a `class_name` with static, pure functions — no scene tree, no autoload access, no I/O. Testability is an architecture property before it is a test-writing skill. The single best refactor for a hard-to-test codebase is extracting decision logic into pure functions and leaving nodes as thin shells that call them (§14).

### Test structure: naming, AAA and fixtures

Tests are code, and unmaintainable tests get deleted the first week they inconvenience anyone — so structure them for a reader who is *not* you, six months out.

**Naming:** a test's name is its failure message. `test_snap` tells a red CI run nothing; `test_snap_rounds_half_cell_up` tells it everything. The pattern worth standardizing: `test_<unit>_<scenario>_<expectation>` — long names are free, mystery failures are not.

**AAA — Arrange, Act, Assert.** Every test body reads as three visually separated blocks: set the stage, do the one thing, check the outcomes. One *Act* per test; when you feel the urge for a second one, that is a second test asking to exist:

```gdscript
func test_purchase_deducts_price_from_wallet() -> void:
    # Arrange
    var shop := ShopLogic.new()
    shop.wallet_coins = 100
    # Act
    shop.try_purchase("plant_fern", 40)
    # Assert
    assert_eq(shop.wallet_coins, 60)
```

**Setup and teardown.** Both frameworks provide per-test and per-suite hooks — shared *Arrange* code moves there, and cleanup becomes automatic instead of hopeful:

```gdscript
# GUT
extends GutTest

var _shop: ShopLogic

func before_each() -> void:            # fresh state for EVERY test —
    _shop = ShopLogic.new()            # tests must never share mutable
    _shop.wallet_coins = 100           # state or order-dependence creeps in

func after_each() -> void:
    _shop.free()                       # or autofree(_shop) in before_each

func before_all() -> void:             # once per suite: expensive setup
    pass                               # (load a big fixture catalog, etc.)
```

GdUnit4's equivalents are `before()`, `after()`, `before_test()`, `after_test()`; its `auto_free()` wrapper ties an object's lifetime to the test automatically. Whichever framework: **leaked nodes in tests are real leaks** — GUT prints an orphan report after the run, and a suite that finishes with orphans is failing even when it is green.

**Awaiting time and signals.** Game code is asynchronous — tweens run, timers fire, signals arrive later. Tests must await, with bounded patience:

```gdscript
# GUT — wait helpers (all awaitable, all bounded):
await wait_frames(3)                       # let _ready/layout settle
await wait_seconds(0.3)                    # tween mid-flight checks
await wait_for_signal(shop.restocked, 2)   # signal OR 2 s timeout → fail

# GdUnit4 — the assertion itself awaits, with a timeout:
await assert_signal(shop).wait_until(2000).is_emitted("restocked")
```

The timeout is the important part: an unbounded await turns one broken signal into a CI job that hangs for an hour. Time-scaled waits (`Engine.time_scale`) can accelerate slow tween logic under test, but prefer the §12 approach — inject the clock — wherever the logic allows it.

### The highest-value test in this course: save round-trips

For a persistence-centered app, this test family outranks all others. Structure: build state → serialize → deserialize → compare field by field. And migrations get a *chain* test with fixture files:

```gdscript
# tests/unit/test_save_migrations.gd — GUT
extends GutTest

func test_round_trip_preserves_decorations() -> void:
    var original := {
        "version": "4.0.0",
        "room": {"id": "default", "theme": "sakura"},
        "decorations": [{"id": "sofa_red", "pos": [212.0, 388.0]}],
        "wallet": {"coins": 140},
    }
    var text := JSON.stringify(original)
    var restored: Dictionary = JSON.parse_string(text)
    assert_eq(restored["decorations"][0]["id"], "sofa_red")
    assert_eq(Helpers.array_to_vec2(restored["decorations"][0]["pos"]),
            Vector2(212, 388))

func test_v1_fixture_migrates_to_current_without_loss() -> void:
    # tests/fixtures/save_v1.json is a REAL v1 file, frozen forever.
    var file := FileAccess.open("res://tests/fixtures/save_v1.json",
            FileAccess.READ)
    assert_not_null(file, "fixture must exist")
    var old: Dictionary = JSON.parse_string(file.get_as_text())
    var migrated := SaveManager.migrate_to_current(old)
    assert_eq(migrated["version"], SaveManager.CURRENT_VERSION)
    assert_true(migrated.has("wallet"), "v3 added wallet with defaults")
    assert_false(migrated.has("tools"), "v2 removed deprecated 'tools'")
    # The invariant that matters most: user content survived.
    assert_eq(migrated["decorations"].size(), old["decorations"].size())
```

Freeze one fixture file per historical save version and never edit them — they are your users' real disks in miniature. Every future migration change must pass every historical fixture. This one habit is the difference between "the update ate my room" and never hearing about migrations at all.

### Signal assertion patterns

Signals are Godot's connective tissue, so test seams follow signal seams. Assert both *that* a signal fired and *what it carried*:

```gdscript
# GUT — watch_signals() records everything the object emits
extends GutTest

func test_purchase_emits_with_item_id() -> void:
    var shop := ShopLogic.new()          # pure logic class, not the UI
    shop.wallet_coins = 100
    watch_signals(shop)

    shop.try_purchase("plant_fern", 40)

    assert_signal_emitted(shop, "purchase_succeeded")
    assert_signal_emitted_with_parameters(
            shop, "purchase_succeeded", ["plant_fern"])
    assert_signal_not_emitted(shop, "purchase_failed")

func test_insufficient_funds_fails_without_side_effects() -> void:
    var shop := ShopLogic.new()
    shop.wallet_coins = 10
    watch_signals(shop)

    shop.try_purchase("plant_fern", 40)

    assert_signal_emitted(shop, "purchase_failed")
    assert_eq(shop.wallet_coins, 10, "failed purchase must not charge")
```

```gdscript
# GdUnit4 — awaitable signal assertions (great for async flows)
extends GdUnitTestSuite

func test_purchase_emits_with_item_id() -> void:
    var shop := auto_free(ShopLogic.new())
    shop.wallet_coins = 100
    shop.try_purchase("plant_fern", 40)
    await assert_signal(shop).is_emitted("purchase_succeeded", ["plant_fern"])
```

Two patterns worth copying: **test the negative signal too** (`assert_signal_not_emitted`) — signal bugs are as often "fired when it shouldn't" as the reverse; and **assert state alongside signals** — a signal is an announcement, and announcements can lie about the state they describe.

### Doubles and stubs: isolating the unit

A unit test for `ShopLogic` must not depend on the real `SaveManager` writing real files. Test doubles replace collaborators with controllable stand-ins:

```gdscript
# GUT — doubling and stubbing an autoload-shaped dependency
extends GutTest

func test_room_requests_save_after_placement() -> void:
    # double() builds a subclass whose methods do nothing (recordable);
    # stub() scripts specific return values.
    var fake_save = double(SaveService).new()
    stub(fake_save, "request_save").to_return(true)

    var room := RoomLogic.new(fake_save)     # injected, not hardwired!
    room.place_decoration("sofa_red", Vector2(212, 388))

    assert_called(fake_save, "request_save")
    assert_call_count(fake_save, "request_save", 1)
```

The load-bearing line is the constructor: `RoomLogic.new(fake_save)`. Doubles only help if dependencies are *injectable* — which is precisely why autoload references hardcoded throughout a codebase make it untestable ([AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) makes the same argument from the architecture side). The refactor is mechanical: accept the dependency as a constructor/setter argument, default it to the real autoload in production, pass the double in tests.

Restraint rule: **stub what you own, assert what matters.** A test with five doubles and seven `assert_called`s is testing its own wiring, not behavior; it will break on every refactor while catching no bugs. Prefer real collaborators when they are cheap and pure (use the real `Helpers`), double only what is slow, stateful or external (files, DB, time, network).

### Scene tests

Integration tests instantiate real scenes and drive them. In GUT, `add_child_autofree()` manages lifecycle; in GdUnit4 the Scene Runner simulates frames and input:

```gdscript
# tests/integration/test_music_panel.gd — GUT
extends GutTest

func test_panel_populates_track_list_from_catalog() -> void:
    var panel: MusicPanel = add_child_autofree(
            preload("res://scenes/ui/music_panel.tscn").instantiate())
    await wait_frames(2)      # let _ready() and layout settle

    assert_gt(panel.track_count(), 0, "catalog should not be empty")
    assert_eq(panel.track_count(), panel.get_node("%TrackList").item_count)

func test_play_button_emits_toggle() -> void:
    var panel: MusicPanel = add_child_autofree(
            preload("res://scenes/ui/music_panel.tscn").instantiate())
    await wait_frames(2)
    watch_signals(panel)

    panel.get_node("%PlayButton").pressed.emit()   # simulate the press

    assert_signal_emitted(panel, "play_pause_toggled")
```

```gdscript
# GdUnit4 Scene Runner — real input simulation, frame by frame
extends GdUnitTestSuite

func test_click_play_toggles_playback() -> void:
    var runner := scene_runner("res://scenes/ui/music_panel.tscn")
    await runner.simulate_frames(2)
    runner.set_mouse_position(runner.scene().get_node("%PlayButton")
            .get_global_rect().get_center())
    runner.simulate_mouse_button_pressed(MOUSE_BUTTON_LEFT)
    await runner.simulate_frames(1)
    await assert_signal(runner.scene()).is_emitted("play_pause_toggled")
```

Scene tests are slower and more brittle than unit tests (they break when node paths change) — that is the pyramid speaking. Write them for the wiring that unit tests cannot see: does the scene *assemble*, do its nodes exist, do editor-made signal connections still connect. A dozen scene smoke tests ("every scene in `scenes/ui/` instantiates without errors") catch an outsized share of refactoring accidents:

```gdscript
func test_all_ui_scenes_instantiate() -> void:
    for path in [
        "res://scenes/ui/music_panel.tscn",
        "res://scenes/ui/deco_panel.tscn",
        "res://scenes/ui/settings_panel.tscn",
        "res://scenes/ui/shop_panel.tscn",
    ]:
        var scene := load(path)
        assert_not_null(scene, path + " failed to load")
        add_child_autofree(scene.instantiate())
        await wait_frames(1)
        # Passing bar: no script errors, no missing-node crashes.
```

### Headless test runs

Tests that only run inside the editor die of friction. Both frameworks run from the command line with `--headless` (no window, no GPU — works on any machine and any CI runner):

```bash
# GUT — via its command-line script:
godot --headless --path . -d -s addons/gut/gut_cmdln.gd \
      -gdir=res://tests -ginclude_subdirs -gexit \
      -gjunit_xml_file=test_results.xml

# ...or with defaults in res://.gutconfig.json ({"dirs":["res://tests"],
#    "include_subdirs":true, "should_exit":true}):
godot --headless --path . -d -s addons/gut/gut_cmdln.gd

# GdUnit4 — via its command tool (runtest wrapper scripts ship with it):
godot --headless --path . -s res://addons/gdUnit4/bin/GdUnitCmdTool.gd \
      --add res://tests --continue
```

Exit code `0` means all green, non-zero means failures — which is exactly the contract CI needs. Run the headless suite locally before every push; it is your last pre-CI checkpoint and takes seconds.

> ⚠️ **Pitfall** — First headless run on a fresh clone (or CI runner) *must import the project first*: the `.godot/` cache does not exist yet, so scripts and scenes have no imported resources to load against, and tests fail with bewildering resource errors. Warm the cache with `godot --headless --import --path .` (Godot 4.4+; earlier 4.x used a timed editor run) before invoking the test tool. This same step opens §13's caching opportunity.

---

## Manual testing, debug tools and soak testing

### Manual test plans

Automation covers logic; humans cover experience — but *unstructured* human testing ("I clicked around, seems fine") covers nothing twice. A manual test plan is a short, versioned script of passes that a human runs before a release. Keep it in `docs/TEST_PLAN.md`, one block per feature, each step a checkbox with an expected result:

```markdown
## TP-03 — Music player (runs: pre-release, ~6 min)
□ Open app → last-played track name shown, NOT auto-playing   [Calm pillar]
□ Press play → audio starts within 0.5 s; button shows pause icon
□ Switch track while playing → crossfade, no gap, no double audio
□ Set volume 0 → silence; relaunch app → volume STILL 0 (persisted)
□ Unplug/replug headphones (OS device change) → playback survives
□ Minimize 5 min while playing → audio continues, CPU < 3%
□ Close app during playback, relaunch → track + position restored

## TP-05 — Save integrity (runs: pre-release + after ANY save change)
□ Decorate, quit via window X → relaunch: room identical
□ Decorate, kill process in Task Manager → relaunch: room identical
  (autosave interval is the max acceptable loss)
□ Copy a v1 fixture save into user://, launch → migrated, nothing lost
□ Corrupt save.json (truncate half) → app starts with a fresh room +
  visible notice; corrupted file is backed up, NOT overwritten silently
```

Rules of the genre: expected results are concrete (numbers, not vibes); every plan block states *when* it runs (per release? after touching its system?); the whole pre-release pass must fit in under an hour or it will be skipped under deadline pressure — and each release, look at what the automation now covers and delete those lines from the manual plan. The manual plan should shrink as the suite grows.

### Debug cheats and a debug console

Manual testing at human speed is throttled by the game's own pacing: testing the shop requires coins, coins require passive earn time. Debug cheats collapse that loop. The minimum kit, guarded so it can never ship active:

```gdscript
# scripts/systems/debug_tools.gd — autoload, whole file inert in release
extends Node

func _ready() -> void:
    if not OS.is_debug_build():
        set_process_unhandled_input(false)
        return

func _unhandled_input(event: InputEvent) -> void:
    if not (event is InputEventKey and event.pressed):
        return
    match event.keycode:
        KEY_F6:  SignalBus.debug_grant_coins.emit(1000)
        KEY_F7:  SaveManager.save_now()                # force autosave path
        KEY_F8:  SaveManager.reload_from_disk()        # round-trip live
        KEY_F9:  get_tree().reload_current_scene()     # lifecycle stressor
        KEY_F10: _toggle_time_scale()                  # 10x passive earning

func _toggle_time_scale() -> void:
    Engine.time_scale = 10.0 if is_equal_approx(Engine.time_scale, 1.0) else 1.0
```

`OS.is_debug_build()` returns `false` in release-template exports, so the guard is structural, not procedural. F9 deserves a highlight: *instant scene reload is a lifecycle-bug detector* — every reconnect-without-disconnect, every leaked node, every static that should have been reset announces itself after a few F9 presses. It is the manual analogue of the audit that produced Relax Room's finding A1.

For anything richer than hotkeys, build a minimal in-game console — a `LineEdit` over a scrollback label, mapping command strings to the same debug signals. The core is smaller than it sounds:

```gdscript
# scripts/systems/debug_console.gd — attach to a CanvasLayer scene
# toggled with F12 (debug builds only, same guard as above).
extends CanvasLayer

@onready var _input: LineEdit = %CommandInput
@onready var _log: RichTextLabel = %Scrollback

var _commands := {
    "give":      func(a: PackedStringArray) -> String:
                     SignalBus.debug_grant_coins.emit(int(a[1]) if a.size() > 1 else 100)
                     return "granted",
    "goto":      func(a: PackedStringArray) -> String:
                     SignalBus.room_change_requested.emit(a[1])
                     return "room → " + a[1],
    "timescale": func(a: PackedStringArray) -> String:
                     Engine.time_scale = float(a[1])
                     return "timescale = " + a[1],
    "save":      func(_a: PackedStringArray) -> String:
                     return "saved" if SaveManager.save_now() else "SAVE FAILED",
    "orphans":   func(_a: PackedStringArray) -> String:
                     return str(Performance.get_monitor(
                             Performance.OBJECT_ORPHAN_NODE_COUNT)),
}

func _ready() -> void:
    visible = false
    _input.text_submitted.connect(_on_submitted)

func _on_submitted(line: String) -> void:
    var parts := line.strip_edges().split(" ")
    _input.clear()
    if parts.is_empty() or not _commands.has(parts[0]):
        _log.append_text("[color=red]unknown: %s[/color]\n" % line)
        return
    _log.append_text("> %s\n%s\n" % [line, _commands[parts[0]].call(parts)])
```

Note that the console owns *zero* game logic — every command emits the same signals or calls the same service methods the real UI uses, which means console commands exercise production code paths, not parallel debug ones. The console's real value is **reproducibility**: a bug report can say "run `goto sakura`, `timescale 10`, then click the cat" — a reproduction script that a hotkey sequence cannot express and that pastes directly into checklist step 5. If you would rather not maintain even this much, mature community console addons exist (M6 applies: tool addon, low risk) — the architecture rule stays the same either way: commands announce, owners act.

### Simulation and soak testing for companion apps

A companion app's defining trait is *time*: it runs for eight hours while the user works, sleeps their laptop, unplugs a monitor, switches audio devices. Ten-minute test sessions structurally cannot find eight-hour bugs — slow memory leaks, drift in passive-earning math, autosave timers interacting with OS sleep. Two techniques close the gap:

**Soak testing** — run the real app for a long time under light scripted stress, and measure. A debug-build autoload can drive it:

```gdscript
# soak_driver.gd — only active with --soak on the command line
extends Node

var _actions := 0

func _ready() -> void:
    if not "--soak" in OS.get_cmdline_user_args():
        queue_free()
        return
    var timer := Timer.new()
    timer.wait_time = 7.0
    timer.timeout.connect(_random_action)
    add_child(timer)
    timer.start()

func _random_action() -> void:
    _actions += 1
    match randi() % 4:
        0: SignalBus.debug_place_random_decoration.emit()
        1: SignalBus.track_change_requested.emit(randi() % 8)
        2: SaveManager.save_now()
        3: get_tree().reload_current_scene()        # the lifecycle stressor
    if _actions % 100 == 0:
        print("[soak] actions=%d  mem=%.1f MB  nodes=%d  orphans=%d" % [
            _actions,
            Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0,
            Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
            Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT),
        ])
```

Launch with `godot --path . -- --soak`, leave it overnight, read the log in the morning. The verdict is in the *trend*: static memory and node count must plateau — a line that climbs 2 MB/hour is a leak that would have surfaced as "the app gets slow after a few days" one month post-release. Orphan-node count growing means `queue_free()` is being missed somewhere. Pass criteria belong in the release checklist: e.g. *8-hour soak, memory plateau within 10%, zero errors, final save loads clean.* Pair the soak with the performance-budget assertions from [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md).

**Simulation testing** — for time-dependent *logic*, don't wait for real time: make time an input. If passive earning reads a clock service instead of `Time.get_unix_time_from_system()` directly, a unit test can hand it "27 hours passed" and assert the earn math, the offline cap, and the clock-set-backward case in milliseconds. The refactor that enables this (inject the clock) is the same inject-your-dependencies move as §11's doubles — testability keeps being an architecture property.

---

## Continuous integration overview

CI is the roommate who checks that the stove is off: every push, a clean machine clones the repository and proves the project still lints, imports, tests and builds — catching "works on my machine" at the earliest possible moment. This section gives the shape; the full release pipeline (export templates, signing, itch.io/Steam upload, matrix builds per platform) is Module 11's territory — see [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md).

The canonical Godot CI pipeline has four stages, fast-to-slow, so cheap failures cut off expensive stages:

```
 lint (~20 s)          import (~1-3 min)        test (~1-5 min)        build (per-platform)
┌──────────────┐      ┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│ gdlint       │  →   │ godot          │  →   │ godot          │  →   │ godot          │
│ gdformat     │      │ --headless     │      │ --headless     │      │ --headless     │
│ --check      │      │ --import       │      │ gut_cmdln.gd   │      │ --export-      │
│ (no Godot    │      │ (warms .godot/ │      │ (JUnit XML →   │      │ release ...    │
│  needed!)    │      │  cache)        │      │  CI test tab)  │      │ (Module 11)    │
└──────────────┘      └────────────────┘      └────────────────┘      └────────────────┘
```

A working minimal GitHub Actions example (lint job shown in §8; here the test job):

```yaml
# .github/workflows/ci.yml — test stage
test:
  runs-on: ubuntu-latest
  needs: lint
  steps:
    - uses: actions/checkout@v4
      with: { lfs: true }                    # pull LFS binaries too
    - name: Install Godot headless
      run: |
        curl -sSLo godot.zip \
          https://github.com/godotengine/godot/releases/download/4.5-stable/Godot_v4.5-stable_linux.x86_64.zip
        unzip -q godot.zip && mv Godot_v4.5-stable_linux.x86_64 godot
    - name: Cache imported assets
      uses: actions/cache@v4
      with:
        path: .godot/
        key: godot-cache-${{ hashFiles('**/*.import', 'project.godot') }}
    - name: Import project (warm cache)
      run: ./godot --headless --import --path .
    - name: Run tests
      run: |
        ./godot --headless --path . -d -s addons/gut/gut_cmdln.gd \
          -gdir=res://tests -ginclude_subdirs -gexit \
          -gjunit_xml_file=test_results.xml
    - uses: actions/upload-artifact@v4
      if: always()
      with: { name: test-results, path: test_results.xml }
```

The three Godot-specific ideas to retain (each detailed in Module 11):

1. **Pin the engine version** in the workflow (4.5-stable above) exactly as the project pins it — a CI that silently tests on a newer Godot than the team runs is testing a different project. Community actions (e.g. setup-godot actions on the Marketplace, or container images like barichello/godot-ci) trade the manual download for a maintained wrapper; either is fine, pinned.
2. **Cache `.godot/`** keyed on the `.import` files and `project.godot` — import is the slow step, and its inputs are exactly those files, so the cache key invalidates precisely when re-import is needed.
3. **Matrix builds come later.** Windows/Linux/macOS export in parallel is a one-stanza change (`strategy: matrix:`) once the single-platform pipeline is green. Resist building the matrix before the pipeline earns it.

> ✅ **Best practice** — CI must be *required*: configure branch protection so PRs cannot merge red. An advisory CI that the team can override "just this once" decays into background noise within a month. The entire value is the guarantee; a guarantee with exceptions is a suggestion.

---

## Refactoring recipes for Godot

Refactoring is restructuring code **without changing behavior** — same inputs, same outputs, same signals, better insides. The definition is strict on purpose: the moment behavior changes, you are doing feature work or bug fixing under a misleading name, and you lose the refactorer's one superpower — the ability to verify, at every step, that nothing observable moved.

### When to refactor (and when not to)

```
Refactor when:
  ✓ You're about to add a feature and the current shape makes it hard
    ("make the change easy, then make the easy change" — Kent Beck)
  ✓ The same pattern appears for the 3rd time → extract it (Rule of Three)
  ✓ A function no longer fits on one screen / a script passes ~600 lines
  ✓ You wrote it last month and can no longer explain it
  ✓ A bug hunt took hours BECAUSE of the structure — fix the structure

Don't refactor when:
  ✗ "It works but I'd have written it differently" (style ≠ debt)
  ✗ You're inside a deadline — log it in the debt register instead (§15)
  ✗ The code has no tests and you can't add even a characterization test
  ✗ Teammates have open branches touching the same files (coordinate first!)
  ✗ You're actually rewriting (be honest — a rewrite needs a plan, not a
    refactor's safety patter)
```

### The safe loop

```
1. COMMIT the current state          (clean baseline — reverting is Plan A)
2. PIN behavior with tests           (even one coarse "characterization"
                                      test: current input → current output)
3. ONE small mechanical change
4. RUN tests + F5                    (identical behavior? scene loads? no
                                      new warnings?)
5. COMMIT with refactor: message
6. REPEAT from 3 — or STOP at any green step; a half-done refactor that's
   all-green is fine, a big-bang one that's half-broken is not.

NEVER refactor and change behavior in the same commit.
```

### Recipe 1 — Extract Function (the workhorse)

**Smell:** a function that narrates its own structure with comment headers ("# build the data… # write the file… # update UI").

```gdscript
# BEFORE — one 60-line function, three jobs
func process_save() -> void:
    var data := {}
    data["version"] = "4.0.0"
    data["room"] = {"id": current_room_id, "theme": current_theme}
    data["decorations"] = []
    for deco in decorations:
        data["decorations"].append({"id": deco.id, "pos": deco.position})
    var file := FileAccess.open("user://save.json", FileAccess.WRITE)
    file.store_string(JSON.stringify(data))
    # ... 40 more lines of UI feedback and error paths

# AFTER — the function becomes a table of contents
func process_save() -> void:
    var data := _build_save_data()
    _write_save_file(data)
    _notify_save_result(data)

func _build_save_data() -> Dictionary:
    return {
        "version": SAVE_VERSION,
        "room": {"id": current_room_id, "theme": current_theme},
        "decorations": _serialize_decorations(),
    }
```

Each extraction is one loop iteration: extract, test, commit. Note the bonus: `_build_save_data()` is now a *pure* function — instantly unit-testable (§11), which the original never was.

### Recipe 2 — Extract Scene

**Smell:** one scene grown monstrous — `main.tscn` holding room, four UI panels, audio players and popup dialogs in a single tree; every feature touches it; every merge conflicts on it (§6).

**Recipe:** in the editor, right-click the subtree's root node → **Save Branch as Scene** → `shop_panel.tscn`. The parent now holds an instance; the subtree lives in its own file with its own script. Then — the step people skip — *sever the tendrils*: any `$"../.."` reaching out of the new scene, any outside node reaching in by deep path, must become an exported `NodePath`, a signal, or a SignalBus event. A scene you cannot instantiate alone in an empty test scene is not yet extracted; it is relocated.

**Payoff:** unit of reuse, unit of testing (scene tests target it directly), unit of *ownership* (one dev can own `shop_panel.tscn` without merge collisions), and faster editor loads.

### Recipe 3 — Extract Component Node

**Smell:** the **mega-script** / **god node** — `character.gd` at 900 lines doing movement, animation, mood, inventory and audio. Inheritance ("make `CharacterBase` bigger") multiplies the problem; composition divides it.

```
BEFORE:  Character (CharacterBody2D)          AFTER:  Character (CharacterBody2D)
           └── character.gd  (900 lines,               ├── Movement    (Node, movement.gd  ~120)
               does EVERYTHING)                        ├── MoodMeter   (Node, mood.gd      ~90)
                                                       ├── AnimDriver  (Node, anim.gd      ~110)
                                                       └── Reactions   (Node, reactions.gd ~80)
```

Each child is a self-contained behavior with a narrow contract: it exports what it needs (`@export var body: CharacterBody2D`), emits signals for what it discovers (`mood_changed`), and never reaches into siblings. The parent script shrinks to wiring. This is Godot's native answer to ECS-style composition — nodes *are* the component system — and the recipe is incremental: extract one responsibility per loop iteration, test, commit. After the second component, the remaining 700 lines suddenly look like four more obvious components; the first cut is the hard one.

### Recipe 4 — Introduce Signal Bus

**Smell:** **signal spaghetti** — UI panels holding direct references to each other (`get_node("../MusicPanel").refresh()`), nodes connecting to signals of siblings found by fragile paths, every scene knowing every other scene's internal layout.

**Recipe:** one autoload, `signal_bus.gd`, declaring project-wide *events* (past tense, typed payloads); emitters announce, listeners subscribe, neither knows the other exists:

```gdscript
# signal_bus.gd (autoload "SignalBus")
extends Node
signal decoration_placed(id: String, position: Vector2)
signal track_changed(index: int)
signal wallet_changed(coins: int)
signal room_changed(room_id: String)
```

Migration is incremental (perfect strangler-fig material, below): pick one direct coupling, replace it with an event, delete the `get_node` chain, test, commit, repeat.

**The counterweight — do not over-apply.** A bus with sixty signals where every conversation is global is a *different* smell (the "signal storm": one emit triggers another, which triggers three more, and causality becomes unreadable). The rule of altitude: **local conversations stay local** (a button talking to its own panel uses a plain signal connection), **cross-scene announcements ride the bus**. And every bus subscription pairs with an unsubscription in `_exit_tree()` — the bus outlives the listeners, which is exactly how the A1 leak class is born.

### Recipe 5 — Kill Global State

**Smell:** **autoload abuse** — mutable flags on singletons (`Globals.is_shop_open`, `Globals.current_room`, `Globals.tmp_selected_item`) that any script anywhere can read *and write*. Symptoms: bugs that depend on the order panels were opened; tests that pass alone and fail in a suite; "it fixes itself after restart."

**Recipe,** per variable (worst offender first):

1. **Find the true owner.** `is_shop_open` belongs to the shop panel; `current_room` to the room manager. Move the variable there, private.
2. **Writers become requests.** Outsiders that used to set the flag now emit an intent (`SignalBus.shop_toggle_requested.emit()`); the owner decides.
3. **Readers become listeners.** Outsiders that polled the flag now cache their own copy from the owner's announcement (`shop_visibility_changed`).
4. If several nodes genuinely share persistent state (the wallet), keep it in *one* dedicated autoload with a **method-and-signal API** — `WalletService.spend(40) -> bool`, `wallet_changed` — and a private variable. Global *services* are fine; global *variables* are the debt. ([AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) is this recipe expanded to module length.)

### Recipe 6 — Extract Resource (hardcode → data)

**Smell:** tuning data living as literals in scripts — shop prices in `shop_panel.gd`, character stats in `character.gd`, theme colors in `room_base.gd`. Every balance tweak is a code change, a review, a re-test; designers (or the designer-half of your brain) cannot iterate without touching logic.

**Recipe:** promote the data into a custom `Resource` — Godot's native serializable data class — and let the Inspector become the editing UI:

```gdscript
# scripts/data/decoration_def.gd
class_name DecorationDef
extends Resource
## One catalog entry. Edit instances as .tres files in data/decorations/ —
## the Inspector is the editor; no code changes for new content.

@export var id: String
@export var display_name: String
@export var category: String = "furniture"
@export var price: int = 10
@export var sprite: Texture2D
@export var footprint: Vector2i = Vector2i(1, 1)   # grid cells
```

Create instances as `.tres` files (FileSystem dock → New Resource → DecorationDef); load them in bulk at startup; the shop, the placement system and the save code all consume `DecorationDef` instead of raw dictionaries. What the extraction buys:

- **Typed data end-to-end** — a `price` typo is a parse error in a `.tres`, not a `Variant` surprise at checkout (§9's boundary rule, solved at the source).
- **Text-format diffs** — `.tres` files diff and review like code: `price = 10 → 12` is a one-line balance commit any reviewer understands.
- **Editor tooling for free** — drag the sprite in, see it; `@export_range` gives sliders; invalid states become impossible to author.
- **Content = data** — adding a decoration is a `.tres` + sprite commit with zero logic risk, which is exactly the property the Relax Room catalog rule (§19) demands.

Choose `.tres` resources when content is edited *in the editor* by the team; keep JSON catalogs when content must be editable outside Godot, diff-reviewed by non-developers, or generated by scripts — Relax Room uses JSON for exactly those reasons, with the §17 validating loader supplying the type safety that `.tres` would have given natively. Either way, the refactor direction is identical: **decisions in code, numbers in data.**

### Strangler fig: refactoring a live game

Big-bang rewrites kill shipped projects: three weeks on a `rewrite/` branch means three weeks of divergence from a `main` that players' bug reports still target, ending in the mother of all merges. The **strangler-fig pattern** (Fowler's name, from the tree that grows around its host until the host is gone) replaces a system *in place, in slices, while it keeps shipping*:

1. **Grow the new alongside the old.** New `SaveServiceV2` lands behind a feature flag or a narrow interface; the old one still runs production.
2. **Route one slice at a time.** Reads go through V2 first while writes still hit V1; then writes; then migrations. Each slice merges to `main`, releasable.
3. **Strangle.** When nothing calls the old system — a `grep` proves it — delete it in a joyous `refactor:` commit.

The releases keep flowing throughout, and each slice's blast radius stays small enough for the §4 checklist to actually hold it. For save systems specifically, run old and new in parallel for one release (write both, read old, *compare and log divergences*) before cutting over — free integration testing on real users' data shapes, with zero risk to their rooms.

> ⚠️ **Pitfall** — "Refactoring" that deletes the old system in commit 1 and promises the new one by commit 40 is a rewrite wearing a refactor's clothes. The tell: is `main` releasable after every commit? If not, stop and re-slice.

---

## Technical debt management

Technical debt is the gap between the code you have and the code the current requirements deserve — every shortcut, workaround, missing test and "TODO: temporary" that lets you ship sooner at the cost of moving slower later. The financial metaphor is precise: debt is a *tool*. Borrowing (shipping the milestone with a hardcoded catalog) is often correct; what ruins projects is not debt but **unmanaged** debt — loans nobody wrote down, compounding silently until every feature costs double and nobody remembers why.

### The debt quadrant

Martin Fowler's quadrant separates debt worth taking from debt that is just damage:

```
                    DELIBERATE                    INADVERTENT
             ┌──────────────────────────┬──────────────────────────┐
   RECKLESS  │ "No time for tests,      │ "What's a signal bus?"   │
             │  just ship it"           │ (didn't know better)     │
             │ → damage, not strategy   │ → the price of learning  │
             ├──────────────────────────┼──────────────────────────┤
   PRUDENT   │ "Ship with JSON catalog  │ "NOW we see how the save │
             │  now; DB migration slice │  system should have been │
             │  is scheduled next"      │  designed"               │
             │ → healthy debt: LOGGED   │ → normal; refactor when  │
             │                          │   you touch it next      │
             └──────────────────────────┴──────────────────────────┘
```

Prudent-deliberate debt with a register entry is engineering. Reckless-deliberate debt is self-sabotage on a schedule. Inadvertent debt is unavoidable — you are always smarter at month six than at week one — and the response is the Boy-Scout rule (leave code slightly better than found) plus honest refactor slices, not shame.

### Godot-specific debt smells

Generic smells (long functions, duplication, dead code) apply, but Godot projects grow five debts of their own — the same five the recipes in §14 target:

| Smell | You know you have it when… | Recipe |
|---|---|---|
| **God node** | One node's script coordinates half the game; every feature PR touches it | Extract Component Node (§14.3) |
| **Mega-script** | `gdlint`'s `max-file-lines` screams; scrolling has geography ("the audio part is near the bottom") | Extract Function, then Component |
| **Signal spaghetti** | Tracing one event means reading six files; `get_node("../..")` chains | Introduce Signal Bus (§14.4) |
| **Autoload abuse** | Bugs depend on panel-open order; tests only pass in isolation | Kill Global State (§14.5) |
| **Scene tangle** | One `.tscn` in every merge conflict; editor takes seconds to open it | Extract Scene (§14.2) |

Add the two data-side debts every persistence-heavy app risks: **save-format lock-in** (fields nobody dares rename because migrations are scary — the fix is the fixture-tested migration chain of §11) and **catalog drift** (JSON data whose implicit schema exists only in the loader's crash behavior — the fix is a validating loader that rejects malformed entries loudly at startup).

### The debt register

Track debt where you track code — a `docs/TECH_DEBT.md` table, one row per loan:

```markdown
# Technical Debt Register — Relax Room
| ID  | Description                              | Interest (cost of NOT fixing)         | Sev | Effort | Taken      | Plan        |
|-----|------------------------------------------|---------------------------------------|-----|--------|------------|-------------|
| D-01| 12 scripts connect() without _exit_tree  | Leaked handlers, errors on room swap  | HIGH| 2 d    | v0.2 (A1)  | next slice  |
| D-02| characters table PK = account_id         | Blocks multi-character feature        | MED | 3 d    | v0.1 (C3)  | before M3   |
| D-03| Logger flushes synchronously per line    | Frame hitches when log is chatty      | MED | 0.5 d  | v0.3 (A12) | with perf pass |
| D-04| Shop prices hardcoded in shop_panel.gd   | Every balance tweak = code change     | LOW | 0.5 d  | v0.2       | opportunistic |
| D-05| No fixture test for v1→v2 save migration | Silent data loss risk on old saves    | HIGH| 0.5 d  | v0.2       | THIS WEEK   |
```

The column that changes behavior is **Interest**: not "the code is ugly" but *what it costs while unfixed*. Interest is what lets you rank D-05 (silent data loss) above D-02 (blocked future feature) above D-04 (annoyance) without arguing taste. Severity trades against Effort exactly like the priority matrix in §17.

Operating rules that keep the register alive rather than decorative:

- **Logging is free and mandatory.** Taking a shortcut costs one table row, written in the same PR that takes the shortcut. `# TODO` comments in code are pointers *to* register entries (`# TODO(D-04)`), never the register itself — grep-able, but unrankable and unbudgeted.
- **Budget a fixed debt share.** Reserve roughly 15-20% of each milestone for register items — one debt slice per week, or one "fix-it Friday". Not a separate "refactor milestone" (it will be cut; it is always cut) but a standing tax.
- **Review at every milestone close.** Re-rank, close what got fixed, and *delete* entries whose interest turned out to be zero — debt in code you never touch again is a loan that never comes due, and fixing it is pure cost.
- **Interest spikes reprioritize.** The moment a feature lands on top of a debt item ("multi-character" lands on D-02), that item's interest jumps from "future" to "now" and it moves to the front — pay before you build on the flaw (*refactor before feature: pay debt before borrowing more*, as this module's oldest guiding idea puts it).

> ✅ **Best practice** — Relax Room's `AUDIT_REPORT.md` (see §19) is this register at larger scale: A-series (architecture) and C-series (correctness) findings, each with severity and a recommended fix, referenced from commits ("fix: resolve A1 — …"). The naming convention is the glue — a commit that cites a register ID closes the loop between the loan and its repayment, in history, forever.

---

## The mistake catalogue

Every mistake below has been made by essentially every game developer, this course's authors enthusiastically included. The catalogue preserves the original module's list and extends it; treat it as a pre-flight inspection — skim the bold lines before starting any new system.

### M1 — Coding before planning

```
Symptom: "I'll just start and figure it out as I go"
Result:  Dead ends, spaghetti, the third rewrite of the same feature
Fix:     The 20% rule (§1) — ten minutes of GDD-lite/checklist per task.
         A 5-minute paper sketch of the shop panel's states saves the
         afternoon of rebuilding it around the state you forgot.
```

### M2 — Tight coupling / fragile paths

```gdscript
# BAD — everything knows everything; breaks when ANY ancestor renames:
func _on_play() -> void:
    var audio = get_node("/root/Main/AudioStreams/Player1")   # fragile
    audio.play()
    get_node("/root/Main/UILayer/HUD/StatusLabel").text = "Playing"  # why?!
    SaveManager.settings["last_played"] = Time.get_ticks_msec()  # reach-in

# GOOD — announce; owners react (see §14.4):
func _on_play() -> void:
    SignalBus.track_play_pause_toggled.emit(true)
    # AudioManager plays (it listens). SaveManager persists (it listens).
    # HUD updates itself (it listens). This script knows NONE of them.
```

### M3 — Premature optimization

```
Symptom: Object pools, threading and micro-optimized loops in week 2 —
         for a game whose whole scene renders in 0.4 ms
Result:  Complexity debt paid daily, performance gain nobody can measure
Fix:     Set the performance BUDGET early (§2: 60 FPS focused, <200 MB,
         <1% CPU unfocused) but OPTIMIZE only against profiler evidence.
         Budget early, optimize late. The profiler, not intuition, names
         the hot path — details in DESKTOP_COMPANION_PERFORMANCE.md.
```

The inverse mistake is real too: *ignoring* performance until release week ("it runs fine on my machine"). The budget + a monthly profiler pass is the middle path.

### M4 — Premature generalization

```
Symptom: An InventorySystem<T> supporting stacking, nesting and network
         sync — for a game with 3 decorations and no inventory UI
Result:  You maintain a framework; the game needed a Dictionary
Fix:     YAGNI + Rule of Three. Build for today's requirements; the
         3rd concrete use case teaches you the RIGHT abstraction —
         the 0th use case can only teach you a guess.
```

### M5 — Tutorial-copy architecture

```
Symptom: The project is five tutorials stapled together: this YouTuber's
         save system, that one's state machine, a third's audio manager —
         each with its own conventions, none aware of the others
Result:  Three save paths, two signal styles, integration seams that leak
Fix:     Tutorials teach TECHNIQUES, not architecture. After following
         one, RE-IMPLEMENT the idea in your project's own conventions
         (typed, linted, bus-wired, tested) — never paste. If you can't
         re-implement it, you weren't done learning it.
```

### M6 — Asset-store dependency risk

```
Symptom: Core systems depend on a $15 addon last updated two Godot
         versions ago, by an author who has moved on
Result:  Engine upgrade blocked; bug unfixable; license terms unclear
Fix:     For each dependency ask: (1) Could we patch it ourselves?
         (source readable, license permits?)  (2) Could we replace it in
         a week?  (3) Is it pinned + committed (addons/ in the repo)?
         Addons for TOOLS (test framework, console) are low-risk;
         addons inside the GAME's core loop are architecture decisions —
         record them as ADRs (§18).
```

### M7 — Feature creep

```
Symptom: "While I'm in this file, let me also add..."
Result:  Never-ending development, an unstable pile of half-features
Fix:     The idea goes to the COULD list (§3), you go back to the card
         you claimed. Relax Room's core is Room + Character + Decorations
         + Music; every idea is measured against that core and the
         pillars. The WON'T list is a wall — lean on it.
```

### M8 — Hardcoding and magic numbers

```gdscript
# BAD:                                # GOOD:
if position.y > 432:                  const FLOOR_Y := 432.0
    velocity.x = 150                  const WALK_SPEED := 150.0
    if health < 20:                   const LOW_HEALTH := 20
        modulate = Color(1, 0, 0)     const DAMAGE_COLOR := Color.RED
```

The constant's *name* is the documentation; the follow-up move is promoting tuning values to `@export` (designers tweak in the Inspector) or to data files (the shop prices in D-04's register entry).

### M9 — Not disconnecting signals

```gdscript
# BAD — connect in _ready, never disconnect; after a scene swap the
# bus holds a reference to a freed object:
func _ready() -> void:
    SignalBus.room_changed.connect(_on_room_changed)

# GOOD — every subscription has an unsubscription:
func _exit_tree() -> void:
    if SignalBus.room_changed.is_connected(_on_room_changed):
        SignalBus.room_changed.disconnect(_on_room_changed)

# ALSO GOOD — one-shot connections auto-disconnect after firing:
SignalBus.load_completed.connect(_on_first_load, CONNECT_ONE_SHOT)
```

This is the single most common Godot lifecycle bug — common enough that Relax Room's audit (A1) found **12 scripts** needing the fix, and common enough to earn its own checklist line, its own debt-register row (D-01), and the F9 reload stress test in §12.

### M10 — Save-format lock-in

```
Symptom: "We can't rename that field, old saves have it" — schema fear
Result:  The save dict accretes dead fields and misnomers forever;
         eventually someone breaks old saves "just this once"
Fix:     Version every save from v1 (a "version" field costs nothing).
         Migration chain + frozen fixtures (§11) make schema change
         ROUTINE instead of terrifying. The promise to users is
         "your data survives", not "our schema is immortal".
```

### M11 — Ignoring pause/focus semantics (companion-app special)

```
Symptom: The app runs full-tilt at 60 FPS while minimized; music
         stutters when the OS suspends the laptop; autosave timer
         "catches up" with 40 rapid saves after sleep
Result:  Fans spin, users notice Task Manager, the Calm pillar dies
Fix:     Focus/pause behavior is a FEATURE with requirements, not an
         edge case: throttle on focus loss, handle NOTIFICATION_
         APPLICATION_FOCUS_IN/OUT, make timers wall-clock-aware after
         sleep, and TEST it (TP-03's minimize line; the workday soak).
         Full treatment in DESKTOP_COMPANION_PERFORMANCE.md.
```

### M12 — "It works" as a quality bar

```
Symptom: Untested happy path ships; the demo gods are kind, once
Result:  Every edge case is discovered by a user, at scale, in reviews
Fix:     "Works" is the entry bar. The exit bar is the Definition of
         Done (§17): typed, linted, tested, reviewed, documented,
         debt logged. Slower per feature; faster per project.
```

---

## Project management for solo and small teams

Formal Scrum for a five-person game team is cosplay: standups nobody needs, story points nobody calibrates, a Scrum Master nobody can spare. But *zero* process fails differently — silent duplicated work, features 90% done forever, and one exhausted person carrying the invisible coordination load. The right amount is small, boring and non-negotiable: a board, a definition of done, and a weekly rhythm.

### Minimal kanban

Three to five columns, physical or digital (GitHub Projects, Trello — the cheapest thing everyone will actually open):

```
BACKLOG            TODO (this week)   DOING (≤1/person)  REVIEW      DONE
────────────       ───────────────    ────────────────   ────────    ────────
shop filters       cat idle anim      exit-tree fix      shop panel  save v2
seasonal sets      TP-03 exec         (Renan)            PR #41      migration
day/night mood     soak run 8h                           (Cristian)  gdlint CI
(the COULD list    (pulled Monday,
 lives here)        sized ≤2 days each)
```

The rules are the system; the board is just where the rules become visible:

1. **WIP limit: one DOING card per person.** The moment two cards are "in progress", both are actually stalled. Finishing beats starting — always. A blocked card goes back to TODO with a note, it does not haunt DOING for a week.
2. **Cards are ≤2 days.** Anything bigger gets split until it isn't ("shop panel" → data model / UI layout / purchase flow / persistence). Small cards make progress visible and make the weekly review honest.
3. **Cards name their scenes.** "music_panel.tscn + music_panel.gd" on the card *is* the scene-ownership claim from §6 — the board doubles as the conflict-avoidance ledger.
4. **The backlog is allowed to be huge; TODO is not.** Monday's planning pulls a week of cards, and that's the week. Mid-week arrivals go to BACKLOG unless they are literal fires.

### Definition of done

"Done" is the most dangerous word in software. A shared, written definition removes the ambiguity that lets 90%-done features pile up:

```
DEFINITION OF DONE — a card may enter DONE only if:
□ Behavior matches the card (and the GDD-lite, if player-facing)
□ Typed, gdlint/gdformat clean (CI green)
□ Tests: new logic covered; full suite passes headless
□ Manual pass: the feature's TEST_PLAN block executed
□ Reviewed: PR approved (or solo: full self-review of the diff)
□ Docs touched if behavior changed (README/TEST_PLAN/ADR as applicable)
□ Debt taken? → register row exists (§15)
□ Merged to main; branch deleted
```

The list is deliberately mechanical — done-ness should be checkable by anyone, including the author at 6 p.m. wanting very badly for the card to be done.

### The weekly review ritual

One meeting per week, 30-45 minutes, always the same shape. It replaces daily standups (a chat message covers those: "yesterday / today / blocked?") and provides the project's heartbeat:

```
WEEKLY REVIEW (Monday, 30-45 min)
1. DEMO (10-15 min)   Everything that reached DONE runs on screen —
                      main branch, not feature branches. No slides, the
                      build. (This is why main stays sacred, §7.)
2. BOARD  (10 min)    Close finished cards; pull next week's TODO;
                      re-rank backlog if priorities moved.
3. HEALTH (5 min)     Milestone map still true? (Re-date it honestly —
                      ×2-3 rule, §3.) Debt register: anything's interest
                      spiking? CI still green and required?
4. ONE IMPROVEMENT (5 min)  The lightest retrospective that works:
                      name ONE thing to change about how we work this
                      week. One. Write it down; check it next Monday.
```

The demo discipline deserves emphasis: demoing from `main` weekly is the most honest project status report that exists. It cannot be gamed by optimistic percentages — either the cat animates on screen or it does not.

### Burnout guardrails

Solo and small-team game development has a documented burnout problem, and hobby projects are *more* vulnerable, not less — there is no boss to blame, so the whip is internal. Guardrails that keep a long project sustainable:

- **Scope is the release valve** (§3). Schedule pressure is relieved by cutting Shoulds, never by adding nights. Crunch "works" for one week and then quietly costs three.
- **Track velocity, not hours.** The estimate log from §3 tells you what a sustainable week produces. Plans built on that number survive; plans built on your best-ever week are pre-broken promises.
- **Protect one no-project day per week.** Fully off. The project will still be there; the counterintuitive, robust finding is that the week's *output* rarely drops — error rates fall enough to pay for the day.
- **Ship something small often.** Morale in long projects starves between releases; a monthly tagged build to three friends beats a someday-launch to everyone. Momentum is a resource — budget for it.
- **Watch for the tells** in yourself and teammates: dreading the editor, rewriting working systems for the third time (procrasti-refactoring), vanishing from chat. The intervention is scope and rest, not pep.

### Working with artists and audio designers

The moment a team includes non-programmers, the repository needs conventions that neither side has to think about — asset handoff fails on ambiguity, not on skill:

```
ASSET HANDOFF CONVENTIONS (docs/ASSETS.md — one page, agreed once)

Formats     sprites: PNG (pixel art: no AA, transparent bg)
            audio: OGG Vorbis (music loops), WAV (short SFX)
Naming      snake_case, categorized:  deco_sofa_red.png,
            char_female_idle_01.png, sfx_click.wav, mus_rain_loop.ogg
            (lowercase ALWAYS — the export case-sensitivity trap, §8)
Specs       decorations: 64×64 or 64×128 px, pivot bottom-center;
            music loops: seamless, -14 LUFS integrated, ≤3 MB
Delivery    drop into assets/incoming/ via the shared drive OR a PR;
            an INTEGRATOR (one named person) moves files into place
            IN THE GODOT EDITOR (imports + .import commits, §5),
            adds the catalog JSON entry, and closes the card
Source      .aseprite/.psd/.flp live in the shared drive, NOT the repo
            (or an LFS-backed assets repo) — repo carries game-ready
            exports only
Review      art review happens on a BUILD (F5), not on the raw PNG —
            palette and scale read differently in-game
```

The single named **integrator** role is the load-bearing convention: assets enter the project through one person who runs the editor import, updates the catalog (the "everything goes through the catalog" rule from Relax Room's workflow — §19), and owns the resulting commit. Everyone else is freed from Git-for-artists training, and the repository is freed from half-imported assets.

> ✅ **Best practice** — Give content creators a *validating* build: if the catalog loader (§15) prints "deco_sofa_red.png: missing pivot / wrong size 65×64" at startup, artists self-serve their own QA and the integrator's job becomes a rubber stamp. An hour of loader validation code buys months of not being the human error message.

### Perspective: how studios run the same loop

Preserved from this module's original notes — the same workflow at two scales, to calibrate how much of "professional process" is actually load-bearing. The AAA pipeline, simplified:

```
Game Director decides on a feature
        │
        ▼
Producer creates the task (Jira/Linear)
  · user story · acceptance criteria · estimate
        │
        ▼
Lead assigns to a developer
  · technical design doc if the blast radius is large
        │
        ▼
Developer implements on a feature branch
  · daily commits · unit + integration tests
        │
        ▼
Code review (peer + lead)
  · meets acceptance criteria? · performance impact? · edge cases?
        │
        ▼
QA testing
  · dedicated testers · regression passes · bugs filed and triaged
        │
        ▼
Merge to development branch
        │
        ▼
Nightly build + automated test farm
  · all platforms compiled · results waiting in the morning
        │
        ▼
Release branch cut → feature freeze → fixes only → certification
        │
        ▼
Ship
```

And the indie pipeline that this module's process actually is:

```
Idea discussed in team chat
        │
        ▼
One-paragraph note on the kanban card
  · "decoration rotation" · rough mockup · acceptance line
        │
        ▼
Developer claims the card (and its scenes)
  · branch · implement · tests · self-review
        │
        ▼
Async review on the forge  +  CI green
        │
        ▼
Merge → weekly demo from main → tag when the milestone closes
```

Read the two diagrams column by column and the insight falls out: **every AAA stage exists in the indie flow — compressed, not deleted.** The producer's acceptance criteria became a line on the card; QA's regression pass became the test suite plus TEST_PLAN blocks; the nightly build farm became one CI workflow; certification became the release checklist. Team size changed the *cost* of each stage, never its necessity. When your project grows, you scale stages up individually — you never discover a missing one, because the checklist-shaped hole a missing stage leaves (untested merges, unreviewed scenes, unreproducible builds) hurts at every team size. That is also the honest argument for learning this process at student scale: the five-person version costs almost nothing and transfers whole.

---

## Documentation, releases and maintenance

### The documentation map

A small project needs few documents — but each with one job, one owner and a staleness policy, or they rot into the worst outcome: documentation that *lies*. The full map this module has assembled, in one table:

| Document | Answers | Updated when | Staleness cost if wrong |
|---|---|---|---|
| `README.md` | How do I run and contribute to this? | Setup or process changes | New contributor loses a day; you, after a break, lose an evening |
| `docs/DESIGN.md` (GDD-lite, §2) | What are we building? What did we refuse to build? | Any scope decision | Scope creep re-litigates settled arguments |
| `docs/MILESTONES.md` (§3) | What's next and roughly when? | Every milestone close | Schedule becomes fiction; trust erodes |
| `docs/TEST_PLAN.md` (§12) | What does a human check before release? | Feature changes; automation absorbing lines | Regressions ship in "tested" releases |
| `docs/TECH_DEBT.md` (§15) | What shortcuts are we paying interest on? | The same PR that takes/pays a shortcut | Debt compounds invisibly |
| `docs/adr/` (below) | Why is it built this way? | Expensive decisions, at decision time | Architecture gets "fixed" back into rejected options |
| `docs/ASSETS.md` (§17) | How does content get in? | Pipeline/convention changes | Assets arrive unusable; integrator becomes a bottleneck |
| `CHANGELOG.md` | What changed for users? | At merge time (`[Unreleased]` section) | Release notes archaeology; support answers wrong questions |
| `##` doc comments (below) | What is this class/signal's contract? | With the code, same commit | Editor help lies, which is worse than absent |

The rule binding the table together: **documentation updates ride the same commit as the change they describe** — a save-format PR touches the migration code, its test, its fixture, the TEST_PLAN block and the changelog line together, or the DoD (§17) refuses it. Documentation that has its own separate "later" is documentation that has a funeral.

### The README

The README is the project's front door, and its audience is a competent stranger — including future-you after two months away. One page, current, testable (its setup steps either work or they don't):

```markdown
# Relax Room
One-paragraph pitch (from the GDD-lite).

## Setup
- Godot 4.5-stable (pinned — other versions untested)
- Clone; open project.godot; first import takes ~1 min
- Tests: GUT 9.x (bundled in addons/) — run headless:
  godot --headless --path . -d -s addons/gut/gut_cmdln.gd

## Project map
scenes/    scene files (one feature = one scene, §6)
scripts/   autoload/ rooms/ ui/ systems/ utils/
data/      JSON catalogs — content enters HERE (see docs/ASSETS.md)
docs/      DESIGN.md TEST_PLAN.md TECH_DEBT.md adr/

## Process
Branch → PR → review → green CI → merge. See docs/ and this course's
GAME_DEV_PLANNING module for the full workflow.
```

### Architecture Decision Records

An ADR is one page that captures a decision *and its why* at the moment it was made — the context, the options weighed, the trade-offs accepted. Six months later, "why JSON and not SQLite for saves?" has a dated answer instead of a shrug, and newcomers can read the project's reasoning instead of reverse-engineering it. Numbered files in `docs/adr/`:

```markdown
# ADR-0003 — Saves are versioned JSON, not SQLite
Date: 2026-02-10 · Status: Accepted · Owner: Renan

## Context
Save data is one document (room, decorations, wallet, settings),
read once at startup, written on autosave. The team already runs
SQLite for the account DB (see DATABASE_AND_PERSISTENCE.md).

## Options
1. SQLite table(s) — transactional, queryable, but schema migrations
   for a document shape are ceremony without benefit.
2. Versioned JSON document + migration chain — human-readable saves
   (debuggable by email attachment!), trivial fixtures for tests,
   matches the "one document" access pattern.

## Decision
Option 2. version field from v1; migration functions per version;
frozen fixture per historical version in tests/fixtures/.

## Consequences
+ Round-trip and migration tests are trivial (module 10 §11).
+ Users can back up a single file.
- No partial writes → write-temp-then-rename for atomicity.
- Revisit IF save size exceeds ~1 MB or queries emerge (ADR would
  be superseded, not edited).
```

Write an ADR whenever a decision is expensive to reverse or sure to be questioned: engine/version pins, save formats, the signal-bus adoption, a core-loop addon (M6), the LFS setup. Statuses flow `Proposed → Accepted → Superseded by ADR-NNNN` — ADRs are never edited into lies; they are superseded, preserving the historical record.

### Inline documentation: ## comments

GDScript has first-class doc comments: `##` lines above a class, member or signal become real documentation — shown in the editor's Help (F1), in Inspector tooltips for exported variables, and indexed for every script with a `class_name`:

```gdscript
class_name SaveManager
extends Node
## Owns the save lifecycle: autosave scheduling, atomic writes,
## and the version migration chain.
##
## Saves are versioned JSON documents (see ADR-0003). All writes go
## through [method save_now]; direct FileAccess writes are forbidden.
## @tutorial(Persistence module): res://docs/persistence.md

## Emitted after a save is durably on disk. [param path] is the
## absolute user:// path written.
signal save_completed(path: String)

## Current on-disk schema version. Bump ONLY together with a new
## migration function and a frozen fixture (module 10 §11).
const CURRENT_VERSION := "4.0.0"

## Autosave interval in seconds. Clamped to [code][15, 600][/code].
@export var autosave_interval: float = 30.0

## Serializes state and writes atomically (temp file + rename).
## Returns [code]false[/code] if the write failed; callers must
## surface this to the user — silent save failure is a critical bug.
func save_now() -> bool:
    ...
```

The conventions that make this worth the keystrokes: document the *contract* (what callers may rely on), not the implementation; `##` on every signal (what it means, when it fires, what the payload is — signals are the API most in need of docs and least likely to have them); `@deprecated` / `@experimental` tags where they apply; and members starting with `_` stay undocumented-private unless deliberately surfaced. Plain `#` comments still exist for implementation notes — and there, the old rule stands: **comment the why, never the what** (`health -= 10  # fall damage: 10/floor, max 3 floors`).

### Versioning and changelogs

**Semantic Versioning**, adapted to a game where the public API is the save file and the player's expectations:

```
MAJOR.MINOR.PATCH
  MAJOR  breaking change for the USER — save not auto-migratable
         (aspire to: never), OS support dropped, core loop changed
  MINOR  new features, new content — saves migrate forward
  PATCH  fixes only

1.0.0 first public release        1.2.0 inventory system
1.1.0 sakura theme + cat          1.2.1 fixed crash on room switch
2.0.0 (avoid: means a save-compatibility break you chose)
```

Keep `CHANGELOG.md` in Keep-a-Changelog format, written *as you merge* (an `## [Unreleased]` section collects lines; releasing = renaming it to the version + date). Written-at-release changelogs are archaeology; written-at-merge changelogs are free:

```markdown
## [1.2.1] — 2026-07-20
### Fixed
- Crash when switching rooms with an active decoration drag
- Music not resuming after the settings panel closed

## [1.2.0] — 2026-07-05
### Added
- "Sakura" room theme; volume tooltip shows percentage
### Changed
- Autosave interval default 60 s → 30 s (data-safety)
```

### Hotfixes and the maintenance rhythm

When a critical bug ships (and one will):

```
1. Branch from the TAG the users have:  git checkout -b hotfix/save-crash v1.2.0
2. Reproduce (§4!) → minimal fix → the repro becomes a regression test
3. Full test suite + the affected TEST_PLAN blocks — a hotfix that
   breaks something else is a catastrophe squared
4. Merge to main; tag v1.2.1; CI builds from the tag (BUILD_AND_EXPORT.md)
5. Post-mortem, blameless, 15 min: which check would have caught this?
   Add it (test, lint rule, checklist line, TP block) — the bug's real
   fix is the PROCESS patch, the code patch is just first aid.
```

Post-release, the project enters maintenance rhythm: the register and backlog absorb incoming reports through the same board, the weekly review keeps running (shorter), and every user-reported bug follows the same law as internal ones — *reproduce, test, fix, regression-proof*. The pre-1.0 process does not get replaced by a post-1.0 process; that continuity is why this module insisted on cheap, sustainable habits from day one.

---

## Case study: Relax Room in production

> **Case study — Relax Room.** This section collects the project-specific material preserved from earlier revisions of this module: the team's actual workflow, its audit history, and the anti-patterns its process rules were written in response to. Everything here is the *applied* form of §§1-18.

### Team and roles

Relax Room is built by a five-person student team (IFTS Projectwork 2026) with an explicit ownership model — the §6 scene-ownership workflow institutionalized:

```
main ─────────────────────────────────────────────── releases (tagged)
  │
  ├── Renan ─────────── team lead / system architect branch
  │     ├── feature/exit-tree-fix ──┐ short-lived feature branches,
  │     ├── feature/db-redesign ────┤ merged back to Renan after review;
  │     └── ...                     ┘ Renan → main at milestone closes
  ├── Cristian ──────── Cristian's feature work
  └── Elia ──────────── Elia's feature work
```

Roles: Renan — architecture, audit, releases (and integrator, §17); Cristian and Elia — feature development with per-scene ownership; art and audio contributors deliver through the `assets/incoming/` handoff convention. Reviews are asynchronous on the forge; every merge to a shared branch gets at least one review; commit messages follow §7's conventions and cite audit IDs (`fix: resolve A1 — add _exit_tree to room_base`).

### The audit history

The project's defining process artifact is `AUDIT_REPORT.md` — a full-codebase review performed at the v0.x midpoint, producing numbered findings in two series (the §15 debt register at production scale):

| Series | Meaning | Emblematic findings |
|---|---|---|
| **A** (Architecture) | Structural issues | **A1**: 12 scripts `connect()` in `_ready()` with no `_exit_tree()` disconnect — the M9 leak, at scale. **A12**: logger flushes synchronously per line — frame hitches. |
| **C** (Correctness) | Bugs and data issues | **C3**: `characters` table uses `account_id` as primary key — silently blocks the planned multi-character feature. |

Each finding carries severity and a recommended fix; commits close findings by ID; the weekly review re-ranks what remains. The audit's deepest lesson was not any single finding but the *shape* of them: nearly every A-series item was an instance of the five Godot debt smells (§15), which is precisely why this module teaches those smells by name.

### Testing history: the GdUnit4 episode

The project's testing stack has its own instructive history. The team adopted GdUnit4 early and wrote its first suites with it (fluent asserts over `Helpers`, the migration chain, shop economy). Mid-project, a Godot minor upgrade landed while the pinned addon release lagged behind it, breaking the suite at exactly the wrong week — and, worse, the addon had been upgraded *ad hoc* rather than as a pinned, deliberate `chore:` commit. An earlier revision of this very module recorded the team's frustrated verdict of that moment: "GdUnit4 removed — use play-mode + manual + headless export validation."

With distance, the honest post-mortem is more precise than the verdict: **the failure was pin discipline, not the framework** — GdUnit4 remains actively maintained and fully supports Godot 4.5, as does GUT. The stack that emerged from the episode: GUT 9.x (pinned, committed in `addons/`, upgraded only in lockstep with engine bumps), the §12 manual test plans, F9-reload and soak passes for lifecycle bugs, and headless CI runs as the merge gate. The episode is preserved here because its lesson generalizes — it is pitfall M6 and the §10 pinning warning, experienced live: *every addon in the critical path is a dependency you must be able to pin, patch or replace.*

### Project-specific anti-patterns (the house rules)

Four rules written in the project's own scar tissue, preserved from the original module:

**1. Never edit `project.godot` by hand.** The file is Godot's, not yours; a stray edit can corrupt project settings. All changes go through Project → Project Settings in the editor. Sole tolerated exception: reviewing the `[autoload]` section in diffs, where order matters ([AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md)).

**2. Everything enters through the catalog.** An asset that is not in the JSON catalog does not exist, no matter what is on disk:

```
WRONG: copy sprite into assets/ → load("res://assets/sprites/new_chair.png")
RIGHT: sprite → assets/sprites/decorations/ → entry in data/decorations.json
       (id, name, category, price, sprite_path) → the game discovers it
       via GameManager's catalog. One registry, validated at startup (§17).
```

**3. `.godot/` never reaches a commit.** It is in `.gitignore` (§5), but `git add -A` plus a hand-edited ignore file has snuck it into staging before. House rule: `git status` before every commit; if `.godot/` appears, `git reset HEAD .godot/` and investigate why.

**4. Zero warnings during gameplay.** Yellow warnings are not decorative: `Unused signal` means dead wiring or a missed listener; `Integer division` means a truncation bug in waiting; `never used` variables are dead code. Every warning is fixed or explicitly suppressed at the specific line with a reason — the Output panel stays clean so that *new* warnings are impossible to miss (§8).

### The blocked-developer protocol

Preserved from the original module — the team's standing answer to "I'm stuck", tuned so that asking for help is structured rather than shameful:

1. **Read the error, actually.** Godot's Output panel gives file, line and description (`res://scripts/rooms/room_base.gd:142 — Invalid call. Nonexistent function 'get_character' in base 'Nil'`). Copy it *whole* — the details are the diagnosis (that `Nil` says the object was freed or never assigned; the line number says where).
2. **Reproduce it** (§4): exact steps, always-or-sometimes, data-dependent?
3. **Isolate it**: temporary `print()` breadcrumbs (or the debugger's breakpoints) to bisect the failing step — "prints 1 and 2 but not 3" localizes the fault to one call.
4. **Search before asking**: F1 in-editor docs on the class; Ctrl+Shift+F for prior art in the project; the error string + "godot 4" on the web.
5. **Ask with context** — after ~30 focused minutes, using the template:

```text
PROBLEM:  [one line]
ERROR:    [full paste from the Output panel]
FILE:     [path:line]
TRIED:    [what you already ruled out]
CONTEXT:  [what you were doing when it broke]
```

The 30-minute mark is calibrated, not arbitrary: under it, most blocks self-resolve and interruptions cost the team more than they save; past it, solo persistence is usually ego, and the template turns the ask into a two-minute answer. The asker documents the solution wherever the next person will look (a comment, the TEST_PLAN, an ADR if it was architectural).

---

## Best practices

The module in one page — each line is expanded in the section cited:

1. **Plan in artifacts, not vibes** (§1-2): a one-page GDD-lite with a ruthless WON'T list, versioned in Git next to the code.
2. **Slice vertically** (§3): the first build touches every layer — input to save file — at tiny scope. Persistence is in the slice, not after it.
3. **Estimate, then multiply by 2-3, then record actuals** (§3): milestone maps are forecasts only if they are fed measurements.
4. **Run the pre-modification checklist** (§4): blast radius mapped, code read in its current form, bug reproduced before "fixed", rollback path confirmed.
5. **`.gitignore` `.godot/`; commit `.import`; LFS the binaries** (§5): commit inputs and recipes, ignore outputs.
6. **Treat `.tscn` merges as conflicts by default** (§6): `merge=binary` in `.gitattributes`, scene ownership on the kanban card, many small scenes.
7. **Keep `main` sacred and branches short** (§7): always releasable, tagged at every build that leaves the machine, conventional commit messages with one intention each.
8. **Make style a non-decision** (§8): `gdformat` on save/pre-commit, `gdlint` in CI, official style guide naming — all-lowercase filenames forever.
9. **Type everything at the boundaries** (§9): full signatures, typed arrays, Variant quarantined at the JSON/DB edge; review scenes and signals, not just scripts.
10. **Automate logic, playtest feel** (§10-12): unit tests for transformations and round-trips, one regression test per fixed bug, frozen fixtures per save version, manual plans for experience, soak tests for companion-app time bugs.
11. **Run everything headless in CI and make it required** (§13): lint → import (cached `.godot/`) → test → build, pinned engine version, red means no merge.
12. **Refactor in green steps; log debt you don't pay** (§14-15): the five Godot smells map to five recipes; the register turns shortcuts into scheduled loans; strangler-fig for anything live.
13. **Process stays small and rhythmic** (§17): WIP limit 1, cards ≤2 days, weekly demo from `main`, one improvement per week, scope — never sleep — as the release valve.
14. **Write the why down** (§18): ADRs for expensive decisions, `##` doc comments on every public contract and signal, changelog written at merge time.

---

## Common errors & troubleshooting

Process failures, like code failures, have symptoms, causes and fixes:

| Symptom | Likely cause | Fix |
|---|---|---|
| Repository is gigabytes; clones take forever | `.godot/` or raw binaries committed to history | Add `.godot/` to `.gitignore`, `git rm -r --cached .godot/`; move binaries to LFS (`git lfs migrate` for history); §5 |
| Teammate's editor re-imports everything with wrong settings | `.import` files not committed (over-aggressive ignore) | Commit `*.import`; they are text recipes, only `.godot/` is generated output; §5 |
| Scene opens broken/corrupt after a merge with no Git conflict | Git line-merged a `.tscn` — textual success, semantic corruption | Set `*.tscn merge=binary` in `.gitattributes`; resolve by taking one side and re-applying the other in the editor; adopt scene ownership; §6 |
| Same scene conflicts in every single PR | One mega-scene owned by everyone | Extract sub-scenes (§14.2); ownership per card (§17); logic into scripts (§6) |
| Exported build can't find assets that work in-editor | Filename case mismatch (`Sofa.png` vs `sofa.png`) — editor forgives, export doesn't | All-lowercase `snake_case` files always; fix names in the editor's FileSystem dock so references update; §8 |
| "Works on my machine", breaks on teammate's/CI | Uncommitted local files, unpinned engine version, or `.godot/`-cache dependence | Fresh-clone test; pin Godot version in README + CI; `godot --headless --import` as CI's first Godot step; §13 |
| CI tests fail with resource-load errors that pass locally | Test job ran before the import step warmed `.godot/` on the clean runner | Run `godot --headless --import --path .` before the test tool; cache `.godot/` keyed on `*.import`; §13 |
| Test suite broke after upgrading Godot | Test addon version lags the engine; upgrade was ad hoc | Pin framework + engine together; upgrade both in one deliberate `chore:` commit with the suite green before merge; §10, §19 |
| Feature "done" for three weeks, never shipped | No definition of done; 90% features accumulate | Adopt the DoD checklist (§17); WIP limit 1; cards ≤2 days |
| Ever-growing TODO list, release date slipping monthly | Scope creep — ideas entering the sprint instead of the backlog | MoSCoW with a hard Must-count; new ideas go to COULD; cut Shoulds, not sleep; §3 |
| `main` is broken and nobody can demo | Direct pushes, merges without CI, or "I'll fix it tomorrow" | Branch protection + required CI; broken-main outranks all feature work; §7 |
| The same bug keeps coming back release after release | Fixed without a reproduction; no regression test | Reproduce → shrink → encode as a test → then fix; every fixed bug becomes a test; §4, §11 |
| Random errors on scene switch; handlers fire on freed objects | Signals connected in `_ready()` never disconnected (the A1/M9 class) | Pair every `connect()` with `_exit_tree()` disconnect or `CONNECT_ONE_SHOT`; F9-reload stress test; §12, §16 |
| App slow/leaky only after hours of running | Slow leak or timer drift — invisible at ten-minute test scale | Overnight soak run with memory/node/orphan trend logging; plateau or it doesn't ship; §12 |
| Old save files lose data after update | Migration written without fixtures; schema changed casually | Frozen fixture per historical version; migration chain tests in CI; version field from v1; §11, §16 |
| Update ships and users report corrupted saves during crash | Non-atomic save writes (partial file on kill) | Write temp file then rename; corruption test in TEST_PLAN (kill the process mid-save); §12, §18 |
| Teammate sees tiny text files where sprites should be | LFS not installed on their machine — they cloned pointers, not content | `git lfs install` once per machine, then `git lfs pull`; add the requirement to the README setup block; §5 |
| Scene references break after renaming/moving an asset | File moved in the OS file manager, not the editor — `res://` paths and the `.import` file left behind | Always move/rename in the FileSystem dock (it rewrites references); repair by re-assigning the resource in the Inspector; §5 |
| Exported `@export` values silently reset after a script change | Renamed/retyped export orphaned the values stored in `.tscn` files | Treat export renames as blast-radius events: grep scenes for the old property, re-set values, note it in the PR; §4 |
| Review queue jams; PRs sit for days | Diffs too large to review honestly | Cards ≤2 days (§17); split refactor from feature commits (§7); reviewer asks for a split instead of skimming |

---

## Exercises

Each lab states acceptance criteria — done means all boxes check. Labs 1-3 preserve and extend this module's original exercise set.

### Lab 1 — The checklist habit *(original exercise, expanded)*

Apply the §4 pre-modification checklist, in writing, to your next **three real changes** in any Godot project (course project or your own).

**Acceptance criteria:**
- Three filled-in checklists exist (PR descriptions or `docs/checklists/`), each with a concrete blast-radius note (inbound/outbound/persisted).
- At least one checklist's "WHAT COULD BREAK" item names something you then verified or guarded — quote it.
- Each change was made on a branch with a clean committed baseline.

**Stretch:** for one change, deliberately write the verification steps *before* touching code, then log how the plan differed from what you actually had to test.

### Lab 2 — Repository surgery

Take a Godot 4 project (create a small one if needed) and give it production-grade version control.

**Acceptance criteria:**
- `.gitignore` excludes `.godot/` and build outputs; `git status` on a fresh editor launch shows nothing generated.
- `*.import` files are tracked; a teammate's fresh clone (or a second local clone) opens with identical import settings.
- `.gitattributes` routes binaries to LFS and sets `merge=binary` for `.tscn`/`.tres`; `git lfs ls-files` lists your assets.
- History demonstrates conventional commits: at least one each of `feat:`, `fix:`, `refactor:`, `chore:`, plus an annotated tag `v0.1.0`.

**Stretch:** simulate the scene-merge disaster — two branches editing the same scene — and resolve it via the take-one-side-and-reapply workflow; write down how long the reapply took versus how long debugging a corrupt merge would have.

### Lab 3 — Debt register bootstrap *(original exercise, expanded)*

Audit a project you own (or the course project) and start its `docs/TECH_DEBT.md`.

**Acceptance criteria:**
- At least 6 entries in the §15 table format, each with a concrete *Interest* column (what it costs while unfixed — no "code is ugly").
- Each entry classified against the five Godot smells (or data-side debts) where applicable.
- Entries ranked; the top one has a scheduled plan; at least one entry is deliberately marked "won't fix" with the reason.

**Stretch:** pay off the top entry as a proper refactor (green-step loop, `refactor:` commits citing the debt ID) and close the register row in the same PR. Review the register again after one month.

### Lab 4 — First test suite, headless

Install GUT or GdUnit4 in a project containing at least one pure-logic class (extract one if needed — that's part of the lab).

**Acceptance criteria:**
- ≥8 unit tests across ≥2 suites: happy paths, edge cases (empty/boundary/malformed input), and one parameterized test.
- One signal test asserting both emission-with-payload and a negative (`not_emitted`) case.
- One test uses a double/stub to isolate a dependency, which required making that dependency injectable — show the before/after constructor.
- The suite runs green headless from a terminal (`godot --headless ...`), exit code checked.

**Stretch:** add one scene smoke test ("every scene in `scenes/ui/` instantiates cleanly") and make it catch a deliberately broken node path.

### Lab 5 — Save round-trip fortress

Harden a save system (build a minimal one if you lack one: room + items + wallet as JSON).

**Acceptance criteria:**
- Round-trip test: build state → save → load → field-by-field equality.
- A schema change (add one field, rename one) implemented as a migration function; a *frozen fixture* of the old format lives in `tests/fixtures/` and the chain test proves no data loss.
- A corruption test: truncated save file → app starts fresh with a visible notice, and the corrupt file is backed up, not overwritten.
- All of it green headless.

**Stretch:** make writes atomic (temp + rename) and prove it with a TEST_PLAN entry executed while killing the process mid-save.

### Lab 6 — CI from zero

Wire the previous two labs into a pipeline on your forge of choice.

**Acceptance criteria:**
- Jobs: `lint` (gdlint + gdformat --check, no Godot), `test` (pinned headless Godot: import step, then the suite, JUnit XML uploaded as an artifact).
- `.godot/` cached with a key derived from `*.import` + `project.godot`; a log line proves a cache hit on the second run.
- Branch protection: a PR with a failing test is demonstrably unmergeable (screenshot or log).

**Stretch:** add a build job producing a Windows or Linux export on tag push — then compare your solution with [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md)'s full pipeline.

### Lab 7 — The refactor gauntlet

Find (or construct) a god node: one script ≥300 lines doing at least three jobs.

**Acceptance criteria:**
- A characterization test pins current behavior before any change.
- The script is decomposed via Extract Function → Extract Component Node (or Extract Scene where structure demands); each step is a separate green `refactor:` commit — history shows ≥5 of them.
- No behavior change: the characterization test never went red, and a manual pass confirms identical behavior.
- Final layout: parent script is wiring only; each component has one responsibility and communicates by signals/exports.

**Stretch:** migrate one cross-scene coupling onto a SignalBus strangler-fig style — old path deleted only after `grep` proves nothing uses it.

### Lab 8 — Plan a real (small) game

Produce the full planning kit for a game you could actually build in 4-6 weeks.

**Acceptance criteria:**
- GDD-lite per the §2 template — every field, every length limit, ≥4 entries in WON'T with reasons.
- Milestone map: 4-6 demonstrable milestones, Musts front-loaded, dates as ranges after applying your ×2-3 multiplier (state the multiplier).
- A kanban board seeded with M0's cards, all ≤2 days, scenes named per card.
- One ADR recording your engine/format/architecture choice of highest regret-potential.

**Stretch:** build M0 (the vertical slice — persistence included), then write a one-page postmortem: which estimates held, what the slice disproved in the plan, what the GDD-lite v2 changes.

### Lab 9 — Soak the companion

For a desktop-companion-style project (Relax Room or your own), prove it survives time.

**Acceptance criteria:**
- A `--soak` driver (per §12) performing randomized actions including scene reloads and saves, logging memory / node count / orphan count every N actions.
- An ≥4-hour run whose log shows plateaued memory and node counts (graph or table in the lab report) and zero errors.
- The final save from the run loads cleanly.
- One focus-semantics check from TP-03 executed (minimize 5+ min: CPU throttled, audio intact).

**Stretch:** inject a deliberate leak (a `connect()` without disconnect), show the soak log *detecting* it as a trend, then fix and re-run.

### Lab 10 — Process postmortem

After ≥2 weeks of applying this module's workflow to real work, write a blameless postmortem of your own process.

**Acceptance criteria:**
- Evidence cited from artifacts, not memory: kanban history, estimate-vs-actual log, debt register deltas, CI pass rates.
- Three sections: *what worked* (keep), *what didn't* (change — one concrete change per item), *what surprised* (investigate).
- One process patch actually applied (a new DoD line, a deleted ritual, a changed WIP limit) and scheduled for review at a named date.

**Stretch:** read one published game postmortem (Further reading below) and add a section comparing their top failure mode to your closest near-miss.

---

## Further reading

Official documentation first, then tools, then the craft literature.

### Official Godot documentation

- **Version Control Systems** (Godot docs → Best practices) — the authoritative word on `.gitignore` for Godot 4 (`.godot/`, `*.translation`), the generated `.gitignore`/`.gitattributes` option in the Project Manager, and Git LFS setup with example attributes. Source for §5. — https://docs.godotengine.org/en/stable/tutorials/best_practices/version_control_systems.html
- **Project organization** (Best practices) — directory layout, the case-sensitivity rationale behind snake_case filenames, `.gdignore`. Source for §8's naming table. — https://docs.godotengine.org/en/stable/tutorials/best_practices/project_organization.html
- **GDScript style guide** — the full naming/ordering/formatting reference that `gdformat` implements. — https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_styleguide.html
- **GDScript documentation comments** — `##` syntax, `@tutorial`/`@deprecated`/`@experimental`, BBCode tags (`[param]`, `[method]`), editor-help integration. Source for §18. — https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_documentation_comments.html
- **Static typing in GDScript** — the typed-GDScript reference behind §9, including the safe-line/unsafe-line distinction and performance notes.
- **Command line tutorial** — `--headless`, `--import`, `--export-release` and friends; the vocabulary of §12-13.

### Tools

- **GUT — Godot Unit Test** (github.com/bitwes/Gut; docs at gut.readthedocs.io) — the framework used in this module's examples; the Command-Line page documents `gut_cmdln.gd`, `-gdir/-gexit/-gjunit_xml_file` and `.gutconfig.json`.
- **GdUnit4** (github.com/MikeSchulze/gdUnit4) — the fluent-assertion alternative: Scene Runner input simulation, fuzzing, flaky-retry, official GitHub Action, C# support via gdUnit4Net.
- **godot-gdscript-toolkit** (github.com/Scony/godot-gdscript-toolkit) — `gdlint`/`gdformat`/`gdparse`; wiki documents every lint rule and the `gdlintrc` format; ships pre-commit hooks. Install: `pip install "gdtoolkit==4.*"`.
- **Git LFS** (git-lfs.com) — pointers, tracking, `git lfs migrate` for retrofitting history.
- **pre-commit** (pre-commit.com) — the hook framework wiring §8's tools into every commit.
- **Keep a Changelog** (keepachangelog.com) and **Semantic Versioning** (semver.org) — the two small standards behind §18's release hygiene.
- **Conventional Commits** (conventionalcommits.org) — the commit-message convention formalized in §7.

### The craft

- **Martin Fowler — *Refactoring* (2nd ed.)** and his online writings on the **Technical Debt Quadrant** and the **StranglerFigApplication** — the vocabulary of §14-15 comes from here; the catalog format makes recipes look-up-able mid-work.
- **Kent Beck — "make the change easy, then make the easy change"** — the one-line philosophy of preparatory refactoring.
- **Steve McConnell — *Code Complete* / *Software Estimation*** — the research grounding for the cost-escalation curve (§1) and the ×2-3 estimation correction (§3).
- **Fred Brooks — *The Mythical Man-Month*** — why adding people late makes projects later; the deep argument for small teams and honest schedules.
- **Game postmortems** — the *Game Developer* (formerly Gamasutra) postmortem archive and GDC's "Failure Workshop" talks; decades of "what went right / what went wrong" from real teams. The recurring lesson across hundreds of them is this module's §3 in the wild: scope, scope, scope.
- **Derek Yu — "Finishing a Game"** (derekyu.com) — the classic essay on why finishing is a skill, from the developer of Spelunky; pairs exactly with the vertical-slice and scope-control sections.

### Sibling modules

- [GODOT_ENGINE_STUDY.md](GODOT_ENGINE_STUDY.md) — engine foundations (prerequisite).
- [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) — the Relax Room codebase this module's case study governs (prerequisite).
- [SCENES_AND_NODES.md](SCENES_AND_NODES.md) — scene composition, the structural basis of §6 and §14.
- [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) — the architecture case against global state; §14.5 in module form.
- [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md) — the save/migration systems that §11's tests protect.
- [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) — budgets, throttling and focus semantics behind §12's soak tests and M11.
- [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md) — Module 11: export presets, release CI, matrix builds — where §13's pipeline grows up.

---

## Glossary

| Term | Definition |
|---|---|
| **ADR (Architecture Decision Record)** | One-page dated record of a significant decision: context, options, choice, consequences. Superseded, never rewritten. |
| **Blast radius** | Everything whose behavior can differ after a change — callers, signal listeners, instantiating scenes, exported values, saved data. Mapped in checklist step 3. |
| **Characterization test** | A test pinning current behavior (right or wrong) before refactoring, so "no behavior change" is verifiable. |
| **Conventional Commits** | Commit-message convention `type: description` (feat/fix/refactor/docs/test/chore/style); one intention per commit. |
| **Definition of done** | The team's written checklist a task must pass to count as finished — typed, linted, tested, reviewed, documented, merged. |
| **Doc comment (`##`)** | GDScript comment syntax whose content becomes editor-help documentation for classes, members and signals; supports `[param]`-style BBCode and `@deprecated`/`@experimental`. |
| **Double (test double)** | A controllable stand-in (via GUT `double()`/GdUnit4 mocks) replacing a real collaborator so a unit can be tested in isolation. |
| **Fixture** | Frozen test data — e.g. a real v1 save file kept forever in `tests/fixtures/` so migration tests run against history, not memory. |
| **GDD-lite** | One-page game design document stating pitch, audience, core loop, pillars, MoSCoW lists, technical constraints and measurable success criteria. |
| **gdformat / gdlint** | Formatter and linter for GDScript from godot-gdscript-toolkit (`pip install "gdtoolkit==4.*"`); run on save, pre-commit and CI. |
| **GdUnit4** | Actively maintained Godot 4 testing framework: fluent assertions, Scene Runner input simulation, mocking, fuzzing, CLI + GitHub Action. |
| **God node / mega-script** | A node/script that has accreted half the game's coordination; the primary Godot debt smell, cured by component extraction. |
| **GUT (Godot Unit Test)** | Godot 4 testing framework used in this module's examples: xUnit-style asserts, doubles/stubs/spies, `watch_signals`, headless CLI via `gut_cmdln.gd`. |
| **Headless run** | Executing Godot without window or GPU (`godot --headless`) — for imports, tests and builds on CI runners. |
| **Kanban (minimal)** | Board-based workflow: backlog → todo → doing (WIP limit 1) → review → done; cards ≤2 days and naming their scenes. |
| **LFS (Git Large File Storage)** | Git extension storing binaries outside normal history as pointers; configured via `.gitattributes`, essential for asset-heavy repos. |
| **Milestone map** | Ordered list of named, demonstrable game states with honest date ranges; the schedule form of MoSCoW. |
| **MoSCoW** | Prioritization into Must / Should / Could / Won't — with hard limits on Must and written reasons on Won't. |
| **Pre-modification checklist** | The six questions (§4) answered before changing code: what, why, blast radius, breakage risks, verification plan, rollback path. |
| **Regression test** | An automated test encoding a fixed bug's reproduction, guaranteeing that bug cannot silently return. |
| **Scene ownership** | Team workflow assigning each `.tscn` to exactly one developer per task window, because scene files cannot be safely merged. |
| **SemVer** | `MAJOR.MINOR.PATCH` versioning; in games, MAJOR maps to user-breaking changes such as non-migratable saves. |
| **Signal bus** | An autoload declaring project-wide events so emitters and listeners decouple; global announcements only — local conversations stay local. |
| **Signal spaghetti** | Coupling smell: cross-scene `get_node("../..")` chains and untraceable event flows; cured by a signal bus plus disconnection discipline. |
| **Soak test** | Running the real app for hours under light scripted stress while logging memory/node/orphan trends; the only test that finds slow leaks and timer drift. |
| **Strangler fig** | Replacing a live system slice by slice alongside the old one — `main` stays releasable throughout — until the old system is provably unused and deleted. |
| **Technical debt register** | The tracked table of shortcuts: description, *interest* (cost while unfixed), severity, effort, plan. Logged in the same PR that takes the shortcut. |
| **Vertical slice** | A thin, fully playable cross-section of the game touching every layer at near-final quality; the first milestone and the architecture's proof. |
| **WIP limit** | Maximum simultaneous in-progress items (here: one per person); finishing beats starting. |
| **×2-3 rule** | Estimation correction: multiply gut estimates by 2 (familiar work) or 3 (unfamiliar), then log actuals to calibrate your personal multiplier. |

---

*Study document for the "Godot 4 in Production" course — Module 10 · Running case study: Relax Room (IFTS Projectwork 2026)*
*Author: Renan Augusto Macena (System Architect & Project Supervisor)*

