---
course: "Godot 4 in Production"
phase: "4 — Production"
module: "11"
title: "Build and Export — Templates, Platforms, Installers and CI/CD"
version: "Godot 4.5 / GDScript 2.0"
level: "Intermediate-Advanced"
prerequisites: [ "GAME_DEV_PLANNING.md" ]
objectives:
  - "Explain the Godot export model (editor + export templates + PCK) and enforce template/editor version matching"
  - "Author and maintain export_presets.cfg for multiple platforms while keeping credentials out of version control"
  - "Produce distributable builds for Windows, Linux, macOS, Android and Web, including installers and signed packages"
  - "Build a professional Windows installer with Inno Setup 6, including silent-install and upgrade-in-place support"
  - "Automate headless exports from the command line and in a GitHub Actions CI/CD pipeline with artifacts and tagged releases"
  - "Ship patches, DLC and mods via external PCK loading, and evaluate PCK encryption honestly"
  - "Apply a release-engineering discipline: semantic versioning, changelogs, pre-release checklists and file-size budgets"
tags: [godot, export, build, pck, inno-setup, ci-cd, github-actions, android, codesigning, appimage, notarization, release]
---

# Build and Export — Templates, Platforms, Installers and CI/CD — Complete Guide

> **Module 11** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Game Dev Planning](GAME_DEV_PLANNING.md), [Godot Engine Study](GODOT_ENGINE_STUDY.md), [Database & Persistence](DATABASE_AND_PERSISTENCE.md) (for the GDExtension export notes)
>
> By the end of this module you will be able to:
> 1. Describe exactly what happens between "Export Project" and a playable binary: template selection, resource remapping, PCK packing and embedding.
> 2. Configure export presets per platform and per release channel (dev / staging / release) and keep secrets out of the repository.
> 3. Export, package and distribute builds for Windows (with an Inno Setup 6 installer), Linux (AppImage), macOS (signed and notarized), Android (APK/AAB) and Web.
> 4. Drive the whole pipeline headless: `godot --headless --import` + `--export-release` in scripts and in GitHub Actions, with export matrix, artifact upload and release-on-tag.
> 5. Deliver patches and DLC as external PCKs with `ProjectSettings.load_resource_pack()`, and explain what PCK encryption does and does not protect.
> 6. Run a pre-release checklist covering versioning, licensing, signing, size optimization and save compatibility.
>
> **Estimated time:** 10-14 hours reading + labs · **Level:** Intermediate-Advanced

## Guiding ideas

1. **The export template IS the engine — its version must match the editor exactly.** Godot 4.5 templates ≠ 4.4 ≠ 4.6; a mismatch is the number-one beginner export failure.
2. **Your game is data, not code: everything you wrote ships inside a PCK that a runtime binary reads.** Understand the PCK and you understand exports, patches, DLC and mods at once.
3. **`export_presets.cfg` belongs in version control; `.godot/export_credentials.cfg` and keystores never do.** Reproducible builds require the first; security requires the second.
4. **If a build is not produced by a script, it does not exist.** Manual editor exports are for experiments; releases come from `--headless` CLI runs, ideally in CI.
5. **Signing and notarization are user-experience features, not bureaucracy.** SmartScreen and Gatekeeper decide whether players ever reach your main menu.
6. **Optimize size and friction last, but budget them first.** A 40 MB installer that installs in one click beats a 300 MB zip with a scary warning.

## Concept map

```
                              ┌──────────────────────────────────┐
                              │   BUILD & EXPORT (Module 11)     │
                              └────────────────┬─────────────────┘
                                               │
          ┌────────────────────┬───────────────┼────────────────┬─────────────────────┐
          │                    │               │                │                     │
 ┌────────▼────────┐  ┌────────▼───────┐ ┌─────▼──────┐  ┌──────▼───────┐  ┌──────────▼─────────┐
 │ EXPORT SYSTEM   │  │ PCK & PATCHES  │ │ PLATFORMS  │  │ AUTOMATION   │  │ RELEASE            │
 │                 │  │                │ │            │  │              │  │ ENGINEERING        │
 │ templates       │  │ virtual FS     │ │ Windows    │  │ CLI headless │  │                    │
 │ version match   │  │ .godot/imported│ │ + InnoSetup│  │ --import     │  │ semver             │
 │ presets .cfg    │  │ load_resource_ │ │ Linux      │  │ --export-*   │  │ changelog          │
 │ credentials     │  │   pack()       │ │ + AppImage │  │ GitHub       │  │ pre-release        │
 │ resource modes  │  │ patches / DLC  │ │ macOS      │  │  Actions     │  │  checklist         │
 │ include/exclude │  │ mods           │ │ + notarize │  │ export matrix│  │ size budget        │
 │ feature tags    │  │ encryption     │ │ Android    │  │ artifacts    │  │ distribution       │
 │ custom builds   │  │ GDScript       │ │ + keystore │  │ release tags │  │ (Steam/itch/GOG)   │
 │ (SCons)         │  │  tokens        │ │ Web (COOP/ │  │ version      │  │ crash reporting    │
 │                 │  │                │ │  COEP)     │  │  stamping    │  │                    │
 └────────┬────────┘  └────────┬───────┘ └─────┬──────┘  └──────┬───────┘  └──────────┬─────────┘
          │                    │               │                │                     │
          └────────────────────┴───────┬───────┴────────────────┴─────────────────────┘
                                       │
                        ┌──────────────▼───────────────┐
                        │ CASE STUDY: RELAX ROOM       │
                        │ installer · pipeline ·       │
                        │ release history              │
                        └──────────────────────────────┘
```

## Table of contents

1. [Overview — from source code to player](#1-overview--from-source-code-to-player)
2. [How Godot builds work — editor vs export templates](#2-how-godot-builds-work--editor-vs-export-templates)
3. [Export templates — install, verify, version matching](#3-export-templates--install-verify-version-matching)
4. [Custom export templates — SCons overview](#4-custom-export-templates--scons-overview)
5. [Export presets deep dive — export_presets.cfg anatomy](#5-export-presets-deep-dive--export_presetscfg-anatomy)
6. [Resource export modes, filters and feature tags](#6-resource-export-modes-filters-and-feature-tags)
7. [PCK internals — the packed virtual filesystem](#7-pck-internals--the-packed-virtual-filesystem)
8. [Patches, DLC and mods — loading external PCKs](#8-patches-dlc-and-mods--loading-external-pcks)
9. [PCK encryption and the GDScript compilation reality](#9-pck-encryption-and-the-gdscript-compilation-reality)
10. [Windows export](#10-windows-export)
11. [Windows installer with Inno Setup 6](#11-windows-installer-with-inno-setup-6)
12. [Linux export — AppImage, Flatpak, Steam runtime](#12-linux-export--appimage-flatpak-steam-runtime)
13. [macOS export — signing and notarization](#13-macos-export--signing-and-notarization)
14. [Android export — SDK, keystores, APK/AAB](#14-android-export--sdk-keystores-apkaab)
15. [Web export — an honest assessment](#15-web-export--an-honest-assessment)
16. [Headless builds and CLI automation](#16-headless-builds-and-cli-automation)
17. [CI/CD with GitHub Actions](#17-cicd-with-github-actions)
18. [Release engineering — versioning, changelogs, crash reporting](#18-release-engineering--versioning-changelogs-crash-reporting)
19. [File-size optimization](#19-file-size-optimization)
20. [Distribution platforms](#20-distribution-platforms)
21. [Case study — Relax Room release pipeline](#21-case-study--relax-room-release-pipeline)
22. [Best practices](#best-practices)
23. [Common errors & troubleshooting](#common-errors--troubleshooting)
24. [Exercises](#exercises)
25. [Further reading](#further-reading)
26. [Glossary](#glossary)

---

## 1. Overview — from source code to player

Everything before this module produced a *project*: a folder full of `.gd` scripts, `.tscn` scenes, textures, audio and a `project.godot` file that only the Godot editor knows how to open. Everything in this module turns that project into a *product*: a file (or a small set of files) that a person with no Godot installation, no Git client and no patience can download, double-click and enjoy.

That transformation is called **exporting** in Godot terminology, and it deserves a full module for three reasons.

First, exporting is where most "works on my machine" disasters are born. The editor is forgiving: it hot-reloads scripts, tolerates case-mismatched paths on Windows, and always has every resource available. An exported build is not forgiving. It contains only what your export preset said to include, resolves paths exactly as written, and runs on machines with drivers, locales and antivirus products you have never seen. A project that has never been exported is a project that has never been tested.

Second, exporting is a genuinely multi-disciplinary skill. In one module you will touch build systems (SCons), package formats (PCK, APK, AAB, AppImage, `.app` bundles), operating-system trust mechanisms (Authenticode, Gatekeeper, Play signing), installer authoring (Inno Setup), and automation (shell scripting, GitHub Actions). None of these is hard in isolation; the craft is in wiring them into one reproducible pipeline.

Third, exporting is where your relationship with players becomes concrete. Version numbers, changelogs, patch sizes, installer polish, whether a scary "unknown publisher" dialog appears — these are the parts of your work players actually see before they see your game. Release engineering *is* user experience.

### The pipeline at a glance

The full journey from a commit to a player's screen looks like this. Every section of this module zooms into one box.

```
  git push / tag v1.2.0
        │
        ▼
  ┌─────────────────────────────┐
  │ CI (GitHub Actions)         │  §17
  │  lint → test → import       │
  └──────────────┬──────────────┘
                 ▼
  ┌─────────────────────────────┐
  │ godot --headless            │  §16
  │   --export-release <preset> │
  └──────────────┬──────────────┘
                 ▼
  ┌─────────────────────────────┐
  │ Export system               │  §2-§6
  │  preset + template + PCK    │
  └──────────────┬──────────────┘
                 ▼
  ┌──────────────────────────────────────────────────────────┐
  │ Platform packaging                          §10-§15      │
  │  .exe + Inno Setup │ AppImage │ .app + notarize │ AAB    │
  └──────────────┬───────────────────────────────────────────┘
                 ▼
  ┌─────────────────────────────┐
  │ Distribution                │  §20
  │  itch.io / Steam / direct   │
  └──────────────┬──────────────┘
                 ▼
             Player 🎮
```

### Where this module sits in the course

This is Module 11, the second half of Phase 4 (Production). [GAME_DEV_PLANNING.md](GAME_DEV_PLANNING.md) covered the process side — milestones, testing strategy, scope control. This module covers the artifact side: how the thing you planned actually leaves your machine. The [capstone](00-CAPSTONE.md) requires a shippable build produced by a scripted pipeline, so treat the labs here as capstone preparation, not optional extras.

Throughout the module, the running case study is **Relax Room**, the desktop companion app built across this course (executable name `MiniCozyRoom` for historical reasons — the project was renamed mid-development, a release-engineering lesson in itself, see §21). Case-study material is always in clearly marked subsections; the rest of the module applies to any Godot 4.x project.

### How to study this module

The module is long because the territory is wide, not because every reader needs every section immediately. Three sensible paths:

- **First-export path (2-3 h):** §1-§3, §5-§7, §10, then Lab 1 and Lab 2. You will understand what you are shipping and have shipped something.
- **Release-week path (4-6 h):** add §11, §16-§18 and the troubleshooting table; run Labs 4-6. This is the minimum bar for the [capstone](00-CAPSTONE.md)'s shippable-build requirement.
- **Full production literacy (the rest):** §4, §8-§9, §12-§15, §19-§21 as your platforms and ambitions demand — each platform section is self-contained by design and safe to defer until that platform is real for you.

Whichever path: do the labs. Export knowledge that has never produced an artifact is trivia; the acceptance criteria exist to force the artifact.

> ✅ **Best practice** — Export early. Do your first Windows export in week one of a project, not week before release. Every export-only bug you find early (a missing `.json` in the filters, a case-sensitive path, a GDExtension binary absent for a platform) is an hour saved during crunch.

---

## 2. How Godot builds work — editor vs export templates

### Two binaries, one engine

The single most clarifying fact about Godot's build model is this: **the Godot editor and an exported game are the same engine compiled twice with different switches**.

- The **editor binary** (`Godot_v4.5-stable_win64.exe` or similar) is the engine compiled *with* the editor: scene dock, inspector, script editor, importers, debugger. It is what you develop in.
- An **export template** is the engine compiled *without* the editor: just the runtime — renderer, physics, audio, GDScript VM, scene loader. It cannot open `.godot` projects, edit scenes or import assets. It can do exactly one thing: locate a PCK (packed resource file), mount it as its filesystem, and run the main scene defined inside.

When you press *Export Project*, Godot does **not** compile anything in the traditional sense. It:

1. takes the pre-compiled export template for the target platform,
2. packs your project's (already imported) resources into a PCK,
3. attaches the PCK to the template — embedded inside the executable or as a sidecar file,
4. applies platform-specific dressing: icon, version metadata, `Info.plist`, `AndroidManifest.xml`, code signature.

This is why exporting a large project takes seconds, not minutes: there is no C++ compilation happening on your machine. It is also why the template version must match the editor version *exactly* — the PCK format, resource binary format and script token format all evolve with the engine, and a 4.4 template reading a 4.5 PCK is undefined behavior at best (§3).

```
  EDITOR BINARY                        EXPORT TEMPLATE
  ┌───────────────────────────┐        ┌───────────────────────────┐
  │ Scene editor / Inspector  │        │                           │
  │ Importers (PNG→CTEX, …)   │        │      (none of this)       │
  │ Debugger / Profiler       │        │                           │
  │ ───────────────────────── │        │ ───────────────────────── │
  │ Renderer                  │        │ Renderer                  │
  │ Physics                   │  same  │ Physics                   │
  │ Audio                     │  core  │ Audio                     │
  │ GDScript VM               │ ─────► │ GDScript VM               │
  │ Scene/Resource loader     │        │ Scene/Resource loader     │
  └───────────────────────────┘        └────────────┬──────────────┘
                                                    │ + your PCK
                                                    ▼
                                             Shippable game
```

### What "compilation" means for GDScript

Students coming from C++ or Rust often ask where the compile step is. The honest answer for GDScript in Godot 4.x:

```
COMPILED AHEAD-OF-TIME (C, C++, Rust):
  source → machine code per platform
  Used by: the ENGINE itself (and your GDExtensions).

GDSCRIPT IN GODOT 4.x:
  source (.gd) → tokenized/compiled in-memory at LOAD time by the GDScript VM
  At EXPORT time you choose (per preset, §6):
    · Text                       → ship .gd source as-is
    · Binary tokens              → ship a tokenized binary form (.gdc)
    · Compressed binary tokens   → same, compressed (the default)
  Tokens load faster and are not human-readable, but they are NOT
  machine code and NOT strong obfuscation (§9).

C# IN GODOT 4.x (.NET edition):
  source → IL assemblies (DLLs) → shipped next to/inside the build,
  executed by the bundled .NET runtime. Not covered further here.
```

So the export step performs *packaging and tokenization*, not native compilation of your game logic. The engine that interprets those tokens was compiled months earlier on Godot's build servers — or on yours, if you build custom templates (§4).

### The export process, step by step

The same transformation, traced through a concrete project tree:

```
Your project (what Git sees):              After "Export Project":
├── scripts/*.gd          ─────────────►  tokenized .gdc (or text, per preset)
├── scenes/*.tscn         ─────────────►  packed as-is or binary .scn
├── assets/sprites/*.png  ──(already──►   .godot/imported/*.ctex payloads
├── assets/audio/*.wav        imported)   + .remap redirection entries
├── data/*.json           ─────────────►  verbatim (IF include filter says so)
├── addons/*/bin/*.dll    ─────────────►  copied NEXT TO the exe (not packed)
├── tests/, docs/, *.md   ─────────────►  dropped (exclude filters)
└── project.godot         ─────────────►  project.binary
                                              │
                                              ▼  all of the above
                                       MiniCozyRoom.pck
                                              │
        export template (§3) ──────┐          │
        icon + version metadata ───┤          │
        code signature (§10) ──────┼──────────┤
                                   ▼          ▼
                          MiniCozyRoom.exe [+ .pck sidecar or embedded]
```

Final shapes per platform, for orientation before the platform sections:

| Platform | Shipped artifact(s) |
|---|---|
| Windows | `Game.exe` (+ `Game.pck` unless embedded, + GDExtension DLLs) |
| Linux | `Game.x86_64` (+ `.pck`, + `.so` files) → usually wrapped in AppImage/tar.gz |
| macOS | `Game.app` bundle (binary + pck + frameworks inside) → `.dmg`/`.zip` |
| Android | `Game.apk` or `Game.aab` (everything inside, signed) |
| Web | `game.html` + `.js` + `.wasm` + `.pck` (+ PWA files) |

Keep this table in mind whenever a later section says "artifact": it is always one of these five shapes plus platform dressing.

### The import pipeline is part of the build

A subtlety that bites every CI pipeline eventually: the assets in your repository are **not** the assets that ship. When you drop `couch.png` into the project, the editor's import pipeline converts it into a compressed, GPU-ready format stored under `.godot/imported/` (e.g. `couch.png-<md5>.ctex`), and writes a small `couch.png.import` metadata file next to the original. At runtime — editor or export — the engine loads the *imported* artifact, not your PNG.

Consequences:

- The `.godot/` directory is a **cache**. It is gitignored, and on a fresh clone it does not exist. Exporting without first regenerating it produces broken builds or hard failures — hence `godot --headless --import` as the first CI step (§16).
- The `*.import` files **are** committed. They record your import settings (compression mode, filters, mipmaps). Losing them means re-importing with defaults.
- What goes into the PCK is the remapped imported resource plus a `.remap` entry telling the loader "when someone asks for `res://couch.png`, hand them `res://.godot/imported/couch.png-<md5>.ctex`". This is why naive include filters like `*.png` in the exclude list can *break* nothing (the PNG wasn't shipping anyway) while excluding `*.import` breaks everything (§7).

> ⚠️ **Pitfall** — "The export worked on my machine but CI produces a build that instantly crashes with missing resources." Ninety percent of the time the CI job skipped the import step or ran it with a mismatched Godot version, leaving `.godot/imported/` empty or stale. Always run `--import` (or use `--export-release`, but on a warmed cache — see §16 for the exact ordering).

### Debug template vs release template

Every platform ships two template flavors, and every export preset picks one:

| | Debug template | Release template |
|---|---|---|
| Optimization | Lower (faster engine builds, some checks on) | Full (`production=yes` class optimizations) |
| Debugger support | Yes — connects back to the editor, remote scene tree, breakpoints | No |
| `OS.is_debug_build()` | `true` | `false` |
| Feature tags | `debug` | `release` |
| Crash output | Verbose errors, script backtraces | Minimal |
| File size | Larger | Smaller |
| Use for | Internal testing, device deploys, reproducing bugs | Everything players touch |

Two habits worth forming now:

1. Gate developer-only behavior on `OS.is_debug_build()` rather than editor checks, so it survives into debug exports but never into releases:

```gdscript
func _ready() -> void:
    if OS.is_debug_build():
        # Visible FPS overlay and verbose logging in debug exports only.
        _debug_overlay.visible = true
        AppLogger.set_level(AppLogger.Level.DEBUG)
```

2. When a bug appears *only* in exported builds, export **debug** first. You keep the export-specific environment (PCK filesystem, release-style paths) but regain error messages and the remote debugger. Jumping straight to a release export to debug is self-sabotage.

---

## 3. Export templates — install, verify, version matching

### The version-matching law

Export templates are versioned with the *full* engine version string, including status: `4.5.stable`, `4.5.1.stable`, `4.6.beta2`. The editor will only use templates whose version string matches its own exactly.

```
Editor 4.5.stable   + templates 4.5.stable    → ✓ works
Editor 4.5.stable   + templates 4.4.stable    → ✗ "No export template found"
Editor 4.5.1.stable + templates 4.5.stable    → ✗ (patch releases count too)
Editor 4.6.dev (custom build) + any official  → ✗ (needs custom templates, §4)
```

This is not pedantry: the template is the engine that will *read* the PCK your editor *writes*. Binary scene format, imported texture format, GDScript token format — all are only guaranteed compatible within the same version. The mismatch error is a feature.

> ⚠️ **Pitfall** — Upgrading the editor (say 4.5 → 4.5.1) and forgetting templates. Everything in the editor works, then the first export fails with "No export template found at expected path". Symptom looks scary; fix is a five-minute download. Pin BOTH the editor and template versions in your project README and CI configuration, and upgrade them in the same commit.

### Installing official templates

Three equivalent routes:

1. **In-editor (simplest):** `Editor → Manage Export Templates… → Download and Install`. Downloads the `.tpz` archive (~500-900 MB — it contains *every* platform, both debug and release) and unpacks it to the user-wide template directory.
2. **Manual:** download `Godot_v4.5-stable_export_templates.tpz` from the official download page or GitHub releases, then `Manage Export Templates… → Install from File`. Necessary on air-gapped machines or when the in-editor download is blocked by a proxy.
3. **Scripted (CI):** download the `.tpz` (it is a renamed ZIP), extract, and place the contents where Godot expects them:

```bash
# Linux CI runner — install templates for 4.5.stable
GODOT_VERSION=4.5
wget -q "https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_export_templates.tpz"
mkdir -p ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable
unzip -q Godot_v${GODOT_VERSION}-stable_export_templates.tpz
mv templates/* ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable/
```

Template locations per OS (the `<version>` folder name must match the editor's version string):

| OS | Path |
|---|---|
| Windows | `%APPDATA%\Godot\export_templates\<version>\` |
| Linux | `~/.local/share/godot/export_templates/<version>/` |
| macOS | `~/Library/Application Support/Godot/export_templates/<version>/` |

Inside you will find files like `windows_release_x86_64.exe`, `linux_release.x86_64`, `macos.zip`, `android_release.apk`, `web_nothreads_release.zip` — one pre-compiled engine per platform/flavor/architecture.

Two practical notes on the template manager: it can install **individual platforms** rather than the full archive (the in-editor dialog lets you pick — useful on metered connections; a Windows-only workflow needs ~200 MB, not 800), and it also handles **removal** of stale versions — template folders for engines you no longer use are pure disk weight, and a yearly prune of `export_templates/` recovering several GB is normal. CI, by contrast, should install only the platforms its matrix actually exports (the §17 raw-download variant can extract selectively with `unzip templates/windows* templates/linux*`).

### Verifying downloads

Official releases publish SHA-512 checksums alongside the binaries. For a pipeline you will run hundreds of times, verify once and cache:

```bash
# Verify the templates archive against the published checksum file
wget -q "https://github.com/godotengine/godot/releases/download/4.5-stable/SHA512-SUMS.txt"
sha512sum --check --ignore-missing SHA512-SUMS.txt
# → Godot_v4.5-stable_export_templates.tpz: OK
```

> ✅ **Best practice** — In CI, cache the extracted templates keyed on the version string (see the `actions/cache` step in §17). Re-downloading 800 MB per build is slow, wastes bandwidth of a free project (Godot's), and adds a network failure mode to every release.

### One template, many games

Note what template installation is *not*: it is not per-project. Templates live in your user profile and are shared by every project you export with that editor version. `export_presets.cfg` (per-project, §5) references them implicitly through the editor version; you never write a template path into a preset unless you are using **custom** templates, which is the next section.

### Managing multiple engine versions side by side

Because templates key on the exact version string, nothing stops you from keeping several editor+template pairs installed — and once you maintain more than one project, you will. A layout that has survived years of course projects:

```
C:\Godot\
├── 4.4.1\Godot_v4.4.1-stable_win64.exe      ← legacy project A
├── 4.5\Godot_v4.5-stable_win64.exe          ← current course version
└── 4.6-beta\ ...                            ← evaluation only, never for releases
%APPDATA%\Godot\export_templates\
├── 4.4.1.stable\
└── 4.5.stable\                              ← templates coexist happily
```

Discipline that makes this safe:

- **The project pins the version, not the machine.** Record `Godot 4.5-stable` in the project README and in CI; the person, not the shortcut, is the weak link. A wrong-version editor will *open* the project (after an upgrade prompt you must refuse!) and quietly re-import everything in the new format.
- **Never let an editor upgrade a project casually.** Godot's "this project was created with an older version" dialog is a one-way door: after conversion, older editors and templates are no longer valid. Upgrades are a planned commit — editor, templates, CI version, and a full export test in one change (see the checklist in §18).
- **Self-contained mode** for the truly cautious: placing a file named `._sc_` (Windows) or `_sc_` next to the editor binary makes that editor store its settings — including export templates — in its own folder instead of the user profile. Each engine version becomes a fully portable, isolated toolbox; this is also the cleanest way to put an exact editor+templates bundle on a USB stick or a build server image.
- Version-manager tools exist in the ecosystem (godotenv and friends); they automate exactly this layout. Use one or use folders — but never "whatever godot.exe was on PATH".

> ⚠️ **Pitfall** — CI has its *own* copy of this problem: a workflow that installs "latest stable" instead of a pinned version will one day silently export your 4.5 project with a 4.6 editor, convert formats in a throwaway container, and ship the result. Always pin the full version string in the workflow env (§17 does), and assert it at runtime with `godot --version`.

---

## 4. Custom export templates — SCons overview

The official templates are one-size-fits-all: every module compiled in, every renderer available, no encryption key. For most projects — including Relax Room — they are exactly right, and you should skip custom templates until you have a concrete reason. The three legitimate reasons:

1. **PCK encryption.** The AES-256 key that decrypts your PCK must be *compiled into* the engine binary; official templates contain no key, therefore encrypted exports require custom templates (§9).
2. **Smaller binaries.** Disabling unused engine modules (3D, navigation, XR, particular importers) can shave 10-40% off the runtime. Relevant for web builds where every megabyte is startup latency, and for embedded targets.
3. **Engine patches or custom modules.** If you maintain a C++ module or need a cherry-picked engine fix before the next release.

### The build system in five lines

Godot compiles with **SCons**, a Python-based build system. Building a release template for Windows on a machine with Visual Studio or MinGW installed:

```bash
# Clone the exact tag matching your editor
git clone -b 4.5-stable --depth 1 https://github.com/godotengine/godot.git
cd godot

# Release export template, 64-bit Windows, full optimization
scons platform=windows target=template_release arch=x86_64 production=yes

# Debug template as well (you want both)
scons platform=windows target=template_debug arch=x86_64
```

Key variables you will actually use:

| SCons option | Meaning |
|---|---|
| `platform=` | `windows`, `linuxbsd`, `macos`, `android`, `web`, `ios` |
| `target=` | `editor`, `template_release`, `template_debug` |
| `arch=` | `x86_64`, `x86_32`, `arm64`, `wasm32`, … |
| `production=yes` | Enables LTO and settings matching official builds |
| `optimize=size` | Favor small binaries (web) over speed |
| `module_X_enabled=no` | Strip module X (e.g. `module_openxr_enabled=no`) |
| `disable_3d=yes` | Remove the entire 3D engine (2D-only games) |
| `SCRIPT_AES256_ENCRYPTION_KEY` | env var: bake the PCK encryption key in (§9) |

A `custom.py` file in the source root can pin these so builds stay reproducible:

```python
# custom.py — 2D desktop-companion template profile
platform = "windows"
target = "template_release"
arch = "x86_64"
production = "yes"
disable_3d = "yes"
module_openxr_enabled = "no"
module_mobile_vr_enabled = "no"
module_camera_enabled = "no"
```

After building, either install the resulting binaries into the version folder from §3 (replacing official ones), or — cleaner — point the export preset's **Custom Template → Release / Debug** fields at the files. The second approach lets official and custom templates coexist.

Expect a full template build to take 10-40 minutes per platform depending on hardware; budget CI time accordingly, or build templates once, store them as versioned artifacts, and reuse until the engine version changes.

Cross-compilation reality check, since teams always ask: **Windows templates from Linux** works well (MinGW toolchain — the official Windows templates are built this way); **web templates** build anywhere Emscripten runs; **macOS templates from non-Mac** is possible (osxcross) but painful enough that the practical answer is a macOS runner or official templates; **Android templates** need the same SDK/NDK stack as §14 regardless of host. For a small team the efficient split is: custom-build only the platforms that need it (usually just your §9 encryption targets or the web size-optimized build), official templates for everything else — custom templates are a per-platform recurring cost, not a lifestyle.

> ⚠️ **Pitfall** — Building custom templates from `master` while your editor is a stable release. The version strings will not match and, worse, formats may genuinely differ. Always build from the tag that matches your editor (`4.5-stable`), and if you patch the engine, patch and rebuild *both* editor and templates.

> ✅ **Best practice** — Treat custom templates like any other dependency: build them from a pinned tag in a dedicated CI job, checksum the outputs, and record the SCons command line in the repository. "Where did this template binary come from?" must never be an open question during release week.

---

## 5. Export presets deep dive — export_presets.cfg anatomy

An **export preset** is a named bundle of answers to every question the export dialog asks: which platform, which template flavor, what to include, how to sign, where to write the output. Presets are created in `Project → Export → Add…` and stored in `export_presets.cfg` at the project root — a plain INI-style text file that you should read at least once in your life, because CI, code review and merge conflicts all happen at the file level, not the dialog level.

### Anatomy of export_presets.cfg

A trimmed real-world example with two presets:

```ini
[preset.0]

name="Windows Release"
platform="Windows Desktop"
runnable=true
advanced_options=false
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter="*.json"
exclude_filter="tests/*,docs/*,*.md"
export_path="build/windows/MiniCozyRoom.exe"
patches=PackedStringArray()
encryption_include_filters=""
encryption_exclude_filters=""
seed=0
encrypt_pck=false
encrypt_directory=false
script_export_mode=2

[preset.0.options]

custom_template/debug=""
custom_template/release=""
debug/export_console_wrapper=1
binary_format/embed_pck=true
texture_format/s3tc_bptc=true
texture_format/etc2_astc=false
binary_format/architecture="x86_64"
codesign/enable=false
application/modify_resources=true
application/icon="res://icon.ico"
application/file_version="1.4.2.0"
application/product_version="1.4.2.0"
application/company_name="IFTS Projectwork Team"
application/product_name="Relax Room"
application/file_description="Relax Room desktop companion"
application/copyright="© 2026 IFTS Projectwork Team"

[preset.1]

name="Windows Dev"
platform="Windows Desktop"
runnable=true
custom_features="dev_tools"
export_filter="all_resources"
export_path="build/dev/MiniCozyRoom_dev.exe"
script_export_mode=2

[preset.1.options]

binary_format/embed_pck=true
debug/export_console_wrapper=1
```

Reading guide:

- **`[preset.N]`** — one block per preset, in dialog order. `name` is what you pass to `--export-release "<name>"` on the CLI, so keep names stable and script-friendly (no trailing spaces; quotes handle inner spaces).
- **`runnable`** — marks the preset used by the editor's "Remote deploy / run exported" conveniences; one runnable preset per platform.
- **`export_filter` / `include_filter` / `exclude_filter`** — the resource selection system, dissected in §6.
- **`custom_features`** — comma-separated custom feature tags baked into this preset's builds (§6).
- **`script_export_mode`** — GDScript shipping format: `0` text, `1` binary tokens, `2` compressed binary tokens (default; §9).
- **`export_path`** — relative to the project; pre-filling it is required for CLI exports without repeating the path.
- **`[preset.N.options]`** — platform-specific knobs; Windows shows `application/*` version metadata (applied via rcedit, §10), Android would show `keystore/*`, `permissions/*`, etc.

### Credentials: what never enters the repository

Godot splits export configuration across two files precisely so you can commit one and ignore the other:

| File | Contents | VCS? |
|---|---|---|
| `export_presets.cfg` | Platform choices, filters, paths, feature tags, metadata | **Commit it** — the build recipe |
| `.godot/export_credentials.cfg` | Keystore passwords, signing identities, PCK encryption keys | **Never** — lives in the gitignored `.godot/` cache |

Sensitive fields you type into the export dialog (Android release-keystore password, macOS notarization credentials, the encryption key) land in `export_credentials.cfg`, not in `export_presets.cfg`. Two operational consequences:

1. **New machine, new clone → credentials are gone.** The presets will load but signing/encryption fields are empty. Either re-enter them or provision them via environment variables in CI:

```bash
# Environment overrides read by the exporter (examples)
GODOT_SCRIPT_ENCRYPTION_KEY=...              # PCK/script encryption key
GODOT_ANDROID_KEYSTORE_RELEASE_PATH=...      # release keystore location
GODOT_ANDROID_KEYSTORE_RELEASE_USER=...
GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD=...
GODOT_WINDOWS_CODESIGN_IDENTITY=...
GODOT_WINDOWS_CODESIGN_PASSWORD=...
```

   In GitHub Actions these come from repository **Secrets**, never from the YAML itself (§17).

2. **Audit your history once.** Godot 3 and very early presets stored some of these fields inline in `export_presets.cfg`. If your project is old, grep the Git history for `keystore` and `password`; a leaked release-keystore password is a rotate-everything event.

> ⚠️ **Pitfall** — Adding `export_presets.cfg` to `.gitignore` "because it contains passwords". In Godot 4 it does not — and ignoring it means every teammate and every CI runner silently exports with *their own* divergent settings, which is how one machine ships with `embed_pck=true` and another without. Commit the presets; ignore the credentials (already ignored via `.godot/`).

### Preset-per-channel patterns

Mature projects keep more presets than platforms. A useful minimal set for a desktop app:

| Preset | Template | Feature tags | Purpose |
|---|---|---|---|
| `Windows Dev` | debug | `dev_tools` | Daily testing; console wrapper on; verbose logging |
| `Windows Staging` | release | `staging` | Release binary pointed at staging backend/services |
| `Windows Release` | release | — | The shippable artifact; signing enabled |
| `Linux Release` | release | — | AppImage source (§12) |
| `Web Demo` | release | `demo` | Feature-limited browser build |

The channel differences should live in *feature tags + configuration*, never in divergent code copies:

```gdscript
# autoload/env.gd — resolve the backend endpoint per channel
func api_base_url() -> String:
    if OS.has_feature("staging"):
        return "https://staging.api.relaxroom.app"
    if OS.has_feature("dev_tools"):
        return "http://localhost:54321"
    return "https://api.relaxroom.app"
```

> ✅ **Best practice** — Review `export_presets.cfg` diffs like code. A one-line change (`encrypt_pck`, an exclude filter, an architecture) alters what every future build contains. Presets edited "temporarily" in the dialog and committed by accident are a classic source of mystery regressions.

### Case study — Relax Room presets

Relax Room ships with five committed presets: `Windows Dev`, `Windows Release`, `Linux Release`, `Web Demo`, `Android Internal`. Decisions worth recording:

- `include_filter="*.json"` on every preset — the room/decoration catalogs are data files, not resources, and would otherwise be silently dropped (this exact bug cost an afternoon in v0.3: the exported build booted to an empty room because `rooms.json` never shipped).
- `exclude_filter="tests/*,docs/*,*.md"` keeps GdUnit4 suites and documentation out of the PCK.
- `Windows Dev` sets `custom_features="dev_tools"` which unlocks the in-app debug panel and hot-reloads the decoration catalog from disk instead of the PCK.
- The Web preset keeps SQLite-dependent features off via the built-in `web` tag rather than a custom one — platform truth should come from platform tags.

### A second dialect: what an Android preset looks like

Platform sections of `export_presets.cfg` differ enough that reading a second one is worth the page space. The (credential-free) Android preset from the case study:

```ini
[preset.4]

name="Android Internal"
platform="Android"
runnable=true
custom_features=""
export_filter="all_resources"
include_filter="*.json"
exclude_filter="tests/*,docs/*,*.md"
export_path="build/android/RelaxRoom.apk"
script_export_mode=2

[preset.4.options]

gradle_build/use_gradle_build=false
gradle_build/export_format=0              ; 0 = APK, 1 = AAB (needs gradle)
architectures/armeabi-v7a=false
architectures/arm64-v8a=true
architectures/x86_64=false
package/unique_name="com.iftsteam.relaxroom"
package/name="Relax Room"
version/code=10402                        ; derived: 1*10000 + 4*100 + 2
version/name="1.4.2"
launcher_icons/main_192x192="res://art/android/icon_legacy.png"
launcher_icons/adaptive_foreground_432x432="res://art/android/icon_fg.png"
launcher_icons/adaptive_background_432x432="res://art/android/icon_bg.png"
graphics/opengl_debug=false
screen/immersive_mode=true
permissions/internet=true
; NOTE: keystore/* fields exist in the dialog but their VALUES live in
; .godot/export_credentials.cfg — this committed file stays clean.
```

Observe the pattern that generalizes to every platform: identity fields you freeze forever (`package/unique_name`), version fields CI stamps (`version/code`, `version/name`), capability toggles you minimize (`permissions/*`, architectures), and asset slots you fill once (icons). When you meet a new platform's preset, sort its options into those four buckets and the configuration stops feeling arbitrary.

### Validating presets in CI

Presets rot: someone flips a flag to debug something and commits it; a rename breaks the CLI contract; a new data folder never gets an include filter. Because `export_presets.cfg` is plain INI, a thirty-line check keeps the recipe honest — run it before any export job (§17):

```python
#!/usr/bin/env python3
# tools/check_presets.py — fail CI when preset invariants break
import configparser, sys, pathlib

EXPECTED = {          # preset name -> (platform, must_have_filter)
    "Windows Release": ("Windows Desktop", "*.json"),
    "Windows Dev":     ("Windows Desktop", "*.json"),
    "Linux Release":   ("Linux/X11",       "*.json"),
    "Web Demo":        ("Web",             "*.json"),
    "Android Internal":("Android",         "*.json"),
}

cfg = configparser.ConfigParser()
cfg.read(pathlib.Path("v1/export_presets.cfg"), encoding="utf-8")
found, errors = {}, []

for section in cfg.sections():
    if section.count(".") == 1:                     # [preset.N], not .options
        name = cfg[section]["name"].strip('"')
        found[name] = section
        platform = cfg[section]["platform"].strip('"')
        want = EXPECTED.get(name)
        if want is None:
            errors.append(f"Unexpected preset: {name}")
            continue
        if platform != want[0]:
            errors.append(f"{name}: platform {platform!r} != {want[0]!r}")
        if want[1] not in cfg[section].get("include_filter", ""):
            errors.append(f"{name}: include_filter missing {want[1]!r}")
        for key, val in cfg[section].items():
            if "password" in key and val.strip('"'):
                errors.append(f"{name}: credential-looking value in {key}!")

for name in EXPECTED:
    if name not in found:
        errors.append(f"Missing preset: {name}")

if errors:
    print("Preset check FAILED:\n  " + "\n  ".join(errors))
    sys.exit(1)
print(f"Preset check OK ({len(found)} presets)")
```

The credential scan at the end is a tripwire, not a guarantee — but it has caught one real accident per year on average, which is exactly what tripwires are for.

---

## 6. Resource export modes, filters and feature tags

### The five export modes

The *Resources* tab of every preset starts with one radio choice — which resources form the base set:

| Mode | Behavior | Use when |
|---|---|---|
| **Export all resources in the project** | Everything recognized as a resource ships | Default; small/medium projects; safest |
| **Export selected scenes (and dependencies)** | You tick scenes; Godot walks their dependency graphs | Demo builds from a subset of scenes |
| **Export selected resources (and dependencies)** | Same, at resource granularity | Fine-grained control; higher maintenance |
| **Export all resources except resources checked below** | Blacklist model | Excluding a large dev-only folder |
| **Export as dedicated server** | Strips visual/audio data, replacing resources with placeholders | Headless multiplayer servers |

Dependency walking is exact but literal: it follows `preload()`, exported `PackedScene`/`Resource` properties and scene references. It cannot see strings. `load("res://rooms/" + room_id + ".tscn")` is invisible to the dependency scanner — with a "selected scenes" mode, those rooms silently vanish from the build.

> ⚠️ **Pitfall** — Dynamic `load()` paths plus "Export selected scenes" is the classic invisible-content bug: works in editor (all files present), breaks in export (dependency graph never reached those files). Either stay on "Export all resources", or keep a `preload_manifest.gd` that statically references dynamic content, or add the folders to the include filter.

Files and folders whose names start with `.` are always excluded (this keeps `.git/`, `.github/` and `.godot/` sources out); the *imported artifacts* under `.godot/imported/` are handled specially and do ship (§7).

### Dedicated server mode in two paragraphs

The fifth mode deserves its own note even in a desktop-focused course, because it demonstrates the export system's real power: the same project, exported twice, can be two *different programs*. "Export as dedicated server" strips visual and audio resources, substituting lightweight placeholder resources that keep scene structure valid — a `Sprite2D` still instantiates, its texture is just a stub. Combined with a headless Linux template, the result is a small binary suitable for cloud game servers, which shares every line of gameplay logic with the client build.

Even if you never ship a multiplayer server, the technique transfers: a "server-like" export with the `dedicated_server` feature tag is also how teams build fast-booting CI smoke-test binaries and headless simulation/balancing tools from the same project. If you go down this road, pair it with explicit code gates (`if OS.has_feature("dedicated_server")`) around anything that touches rendering or audio players.

### Include and exclude filters: non-resource files

Godot only packs what it recognizes as resources. Plain data files — `.json`, `.csv`, `.txt`, `.sql`, custom formats — are **not** resources and are dropped unless you list them in **Filters to export non-resource files/folders**:

```
include_filter:  *.json, data/*.csv, licenses/*
exclude_filter:  tests/*, docs/*, *.md, *.blend, *.psd, *.wav.bak
```

Rules of engagement:

- Patterns are comma-separated globs matched against `res://`-relative paths; `*` matches within and across path separators for simple patterns like `*.json`, and directory patterns like `tests/*` prune whole subtrees.
- Exclude wins where both match.
- The filters exist for *files*, not for saving space on imported resources — excluding `*.png` does not shrink the build, because the PNG was never shipping; its imported `.ctex` was (§7).
- Source-asset droppings (`.blend`, `.psd`, `.kra`, exports from DAWs) should ideally not live inside the project folder at all; the exclude filter is the second line of defense.

Verify what actually shipped rather than trusting your mental model. Two options: export as ZIP instead of PCK and open it in any archiver, or list a PCK from a script:

```gdscript
# tools/list_pck.gd — run with: godot --headless -s tools/list_pck.gd -- game.pck
extends SceneTree

func _init() -> void:
    var args := OS.get_cmdline_user_args()
    if args.is_empty():
        push_error("usage: godot --headless -s tools/list_pck.gd -- <file.pck>")
        quit(1); return
    if not ProjectSettings.load_resource_pack(args[0], false):
        push_error("Could not open pack: " + args[0])
        quit(1); return
    _walk("res://")
    quit(0)

func _walk(dir_path: String) -> void:
    var dir := DirAccess.open(dir_path)
    if dir == null: return
    dir.list_dir_begin()
    var entry := dir.get_next()
    while entry != "":
        var full := dir_path.path_join(entry)
        if dir.current_is_dir():
            _walk(full)
        else:
            print(full)
        entry = dir.get_next()
```

### Feature tags: one codebase, many builds

Every Godot build carries a set of **feature tags** — strings queryable at runtime with `OS.has_feature()` and usable in project settings *overrides*. They come from three sources:

1. **Platform/system tags** (automatic): `windows`, `linuxbsd`, `macos`, `android`, `ios`, `web`, plus traits like `mobile`, `pc`, `x86_64`, `arm64`, `double` (double-precision builds).
2. **Build-type tags** (automatic): `debug` or `release`, `editor` or `template` — note that running in the editor always reports `editor` *and* `debug`.
3. **Custom tags** (yours): the `custom_features` field of the preset — `demo`, `steam`, `staging`, `dev_tools`, `kiosk`…

The built-in tags you will actually branch on, in one table:

| Tag | True when | Typical use |
|---|---|---|
| `windows` / `linuxbsd` / `macos` | That desktop OS | Path conventions, platform integrations |
| `android` / `ios` | That mobile OS | Touch UI, lifecycle handling |
| `web` | Browser build | Disable filesystem/OS features (§15) |
| `mobile` / `pc` | Device class | Input defaults, UI density |
| `debug` / `release` | Template flavor (editor counts as debug) | Logging levels, cheats |
| `editor` / `template` | Running in editor vs any export | Tool code, dev-only scenes |
| `x86_64` / `arm64` etc. | CPU architecture | Rarely needed in scripts |
| `dedicated_server` | Server-mode export | Headless gates (see above) |

Runtime branching:

```gdscript
func _on_import_music_pressed() -> void:
    # Relax Room: the music-import dialog cannot work in a browser sandbox.
    if OS.has_feature("web"):
        AppLogger.warn("MusicPanel", "File import not supported on web builds")
        _show_toast(tr("MUSIC_IMPORT_UNAVAILABLE_WEB"))
        return
    _open_native_file_dialog()

func _is_demo() -> bool:
    return OS.has_feature("demo")
```

Feature tags also drive **project-setting overrides**: any setting can carry per-feature values (`application/config/name.web`, `rendering/textures/vram_compression/import_etc2_astc.mobile`, and so on) — the most specific matching feature wins at load time. This is how one project ships different window settings on desktop vs a fixed canvas on web without a line of script.

> ✅ **Best practice** — Use *platform* tags for platform truth and *custom* tags for product truth. `if OS.has_feature("web")` for sandbox limits; `if OS.has_feature("demo")` for content gating. Never invent a custom tag that duplicates a built-in one (`win`, `desktop`) — six months later nobody remembers which spelling is real. The full built-in list lives in the official *Feature tags* documentation page.

> ⚠️ **Pitfall** — Testing feature-tag logic only in the editor. The editor's tag set (`editor`, `debug`, your OS) differs from every export. `OS.has_feature("template")` is `false` in-editor and `true` in all exports — if a code path must differ between the two, test it in an actual export, not by pressing F5 and hoping.

### Project-setting overrides in depth

Because overrides are the least-known half of the feature-tag system, a concrete tour. Any key in `project.godot` may appear multiple times with feature suffixes; at startup the engine picks the most specific match for the running build's tag set:

```ini
# project.godot excerpts — one project, per-build behavior
[application]
config/name="Relax Room"
config/name.web="Relax Room (Browser Demo)"

[display]
window/size/viewport_width=1280
window/size/viewport_width.web=960
window/stretch/mode="disabled"
window/stretch/mode.web="canvas_items"

[rendering]
textures/vram_compression/import_etc2_astc=false
textures/vram_compression/import_etc2_astc.mobile=true

[debug]
file_logging/enable_file_logging=false
file_logging/enable_file_logging.release=true   ; log to user://logs in releases
```

Three properties of the mechanism worth internalizing:

1. **Overrides are resolved at load, not at export** — every build carries all variants; the tag set active in that binary selects one. This means a single PCK can serve multiple templates correctly (useful with `--main-pack` testing across platforms).
2. **Custom tags participate** — a `demo` preset can override `application/config/name.demo` with zero code.
3. **They do not cascade at runtime**: `ProjectSettings.get_setting()` returns the resolved value; changing tags after boot changes nothing. Feature tags are a *build-time identity*, not a runtime switch — if you need runtime switching, that is ordinary configuration, not tags.

There is also a separate, older mechanism worth one sentence: `override.cfg` placed next to the executable overrides project settings at boot *without* re-exporting — handy for QA experiments ("try this window mode") and occasionally for server ops, but never ship one to players, because it is plain text and overrides *anything*.

---

## 7. PCK internals — the packed virtual filesystem

### What a PCK is

A `.pck` file is Godot's archive format: a flat, indexed container holding every file of your exported project, mounted at runtime as the read-only `res://` filesystem. No compression by default (files are read directly with an offset table, which keeps loading fast), optional per-file encryption (§9), and a small header carrying the format version and engine version that wrote it.

```
MiniCozyRoom.pck (conceptual layout)
┌───────────────────────────────────────────────┐
│ Header: magic "GDPC", pack format version,    │
│         engine version, flags, file count     │
├───────────────────────────────────────────────┤
│ Index: for each file →                        │
│   path ("res://scripts/room.gdc")             │
│   offset, size, MD5, flags (encrypted?)       │
├───────────────────────────────────────────────┤
│ File data blobs, back to back                 │
│   .godot/imported/couch.png-9f3a….ctex        │
│   scripts/autoload/signal_bus.gdc             │
│   scenes/main_room.tscn (or .scn binary)      │
│   data/rooms.json                             │
│   couch.png.import + .remap entries           │
│   project.binary  (compiled project.godot)    │
└───────────────────────────────────────────────┘
```

Notable residents:

- **`project.binary`** — your `project.godot`, converted to a binary settings blob. The runtime reads main scene, autoloads, input map and rendering settings from here.
- **Remapped imports** — the real texture/audio payloads under `.godot/imported/`, plus lightweight `.remap` files so `load("res://couch.png")` transparently resolves to the imported artifact. Your original PNGs and WAVs are *not* in the PCK (with default import settings); their optimized descendants are.
- **Script files** — as `.gd` text or tokenized `.gdc` depending on the preset's script export mode (§9).
- **Non-resource files** — whatever survived your include/exclude filters, byte-identical to the originals.

The engine can also mount **ZIP** archives with identical semantics (`--export-pack` writes whichever extension you ask for). ZIP trades speed for compression and archive-tool compatibility; note the practical caveat that a bare game binary auto-detects a *PCK* sidecar by name, while a ZIP pack generally needs an explicit `--main-pack my_game.zip` argument — which is why PCK remains the default for shipping and ZIP shines for inspection and mod distribution.

### Embedded vs sidecar

Per preset, the PCK either travels inside the executable (`binary_format/embed_pck=true`) or next to it:

| | Embedded | Sidecar (`game.exe` + `game.pck`) |
|---|---|---|
| Distribution | Single file — friendly for direct downloads | Two files that must stay together |
| Patching | Replace the whole executable | Replace only the PCK (engine untouched) |
| Code signing | One signature covers everything | Signature covers the exe; PCK swaps don't invalidate it |
| Antivirus heuristics | Occasionally twitchier (big self-contained exe) | Usually calmer |
| Size limits | Embedding supported up to ~3.89 GB executables | PCK effectively unlimited |

For installer-based distribution (§11) the sidecar layout is usually better: the installer already bundles files, and future patches can ship a PCK alone. For casual "download one file from itch.io" distribution, embed.

### How the runtime finds its pack

Startup resolution order of a template binary, simplified: an embedded PCK wins if present; otherwise the binary looks for a sidecar pack matching its own name (`MiniCozyRoom.exe` → `MiniCozyRoom.pck`) in its directory; command-line `--main-pack path/to/file.pck` overrides everything. If nothing is found you get the infamous *"Error: Couldn't load project data at path '.'"* — see the troubleshooting table.

```powershell
# Windows: run an arbitrary pack with a bare template binary (handy for QA)
.\windows_release_x86_64.exe --main-pack .\build\MiniCozyRoom.pck
```

This decomposition — dumb engine binary + all-content pack — is the mental model that makes the next section (patches, DLC, mods) almost trivial.

### Inspecting and diffing packs in practice

Trust, but list. Three inspection workflows in ascending effort:

**1. Export a ZIP twin.** Add a second export path with `.zip` to the same preset during debugging; open it in any archiver. Fastest way to answer "did my JSON ship?" — but remember the ZIP is a *re-export*, not a view of the PCK you already made.

**2. Script the listing** (the §6 lister). Combine with `FileAccess.get_md5()` to build a manifest, and diff manifests across releases to see exactly what a patch will need:

```gdscript
# tools/manifest_pck.gd — print "md5  size  path" for every file in a pack
# usage: godot --headless -s tools/manifest_pck.gd -- game.pck > manifest.txt
extends SceneTree

func _init() -> void:
    var args := OS.get_cmdline_user_args()
    if args.is_empty() or not ProjectSettings.load_resource_pack(args[0], false):
        push_error("cannot open pack"); quit(1); return
    _emit("res://")
    quit(0)

func _emit(dir_path: String) -> void:
    var dir := DirAccess.open(dir_path)
    if dir == null: return
    dir.list_dir_begin()
    var e := dir.get_next()
    while e != "":
        var full := dir_path.path_join(e)
        if dir.current_is_dir():
            _emit(full)
        else:
            var f := FileAccess.open(full, FileAccess.READ)
            var size := f.get_length() if f else -1
            print("%s  %10d  %s" % [FileAccess.get_md5(full), size, full])
        e = dir.get_next()
```

```powershell
# Release ritual: diff this release's manifest against the last
godot --headless -s tools/manifest_pck.gd -- build\v1.4.2.pck > m142.txt
godot --headless -s tools/manifest_pck.gd -- build\v1.4.1.pck > m141.txt
git diff --no-index m141.txt m142.txt   # what actually changed?
```

**3. Third-party PCK explorers** exist (GUI unpackers, `godotpcktool`-style CLIs). They are fine for inspecting *your own* packs; their existence is also Exhibit A in the §9 discussion about what unencrypted packs reveal to players.

> ✅ **Best practice** — Archive the manifest with every release artifact (it is a two-line CI step). Six months later, "was the old font inside 1.2.0?" becomes a `grep`, not an archaeology dig through installer downloads.

### Loading behavior worth knowing before you rely on it

Three runtime facts that surprise people the week they start doing dynamic content:

- `ResourceLoader.exists("res://x.tres")` respects mounted packs and remaps — use it, rather than `FileAccess.file_exists()`, to probe for *resources* (the latter checks raw paths and misses remapped imports).
- Loading is cached: `load()` returns the cached instance if the resource is already in memory, which is precisely why late-mounted patches don't retroactively fix loaded scenes (§8). `ResourceLoader.load(..., CACHE_MODE_IGNORE)` exists for tools, not as a patch workaround.
- `DirAccess.open("res://")` walks the union of everything mounted — the basis of both the lister above and of content-discovery systems ("scan res://rooms/ for room definitions"), which therefore automatically see DLC packs. Design your catalogs to *scan*, and DLC integration becomes free.

### `res://` vs `user://` after export

In the editor, `res://` is your project folder and writable; in an export it is the PCK and **read-only**. Anything the game writes — saves, settings, downloaded content, logs — must go to `user://`, which maps to a per-app directory in the OS user profile:

| Platform | `user://` resolves to (default) |
|---|---|
| Windows | `%APPDATA%\Godot\app_userdata\<ProjectName>\` |
| Linux | `~/.local/share/godot/app_userdata/<ProjectName>/` |
| macOS | `~/Library/Application Support/Godot/app_userdata/<ProjectName>/` |
| Android | app-private internal storage |
| Web | browser IndexedDB (persistence needs cookies/site-data allowed) |

Set `application/config/use_custom_user_dir` and `custom_user_dir_name` in project settings if you want `%APPDATA%\RelaxRoom\` instead of the Godot-namespaced default — decide *before* first release, because changing it later orphans every player's save data (or forces you to write migration code that checks both paths).

> ⚠️ **Pitfall** — Code that writes to `res://` (level editors, "save settings next to the exe" habits from other engines). It works in the editor, then fails silently or loudly in exports. Audit with a project-wide search for `FileAccess.open("res://` with write flags before first export. The one legitimate read/write escape hatch is absolute OS paths via `OS.get_executable_path().get_base_dir()` for genuinely portable apps — and even that breaks under `Program Files` (non-writable without elevation).

### Case study — Relax Room pack layout

Relax Room ships sidecar-style on Windows (`MiniCozyRoom.exe` + `MiniCozyRoom.pck`) precisely because its update cadence is content-heavy: new decoration packs and room themes change the PCK weekly during events while the engine binary changes only on engine upgrades. The Inno Setup upgrade installer (§11) marks the PCK `ignoreversion`, so a patch release re-copies 25 MB of PCK and leaves the 60 MB engine binary cached in the download. The SQLite database and user decorations live in `user://` (`%APPDATA%\Godot\app_userdata\Relax Room\relax.db`), which the uninstaller deliberately leaves behind unless the player ticks "Remove my saved rooms".

---

## 8. Patches, DLC and mods — loading external PCKs

The engine does not care how many packs are mounted. At startup it mounts the main PCK; at any time afterward, GDScript can mount more:

```gdscript
# Returns true on success. Files in the pack appear under res://
var ok := ProjectSettings.load_resource_pack("user://dlc/winter_pack.pck")
```

`load_resource_pack(path: String, replace_files: bool = true, offset: int = 0)` has one crucial default: **`replace_files = true` means files in the new pack override same-path files already mounted**. That single flag is the difference between the three use cases:

| Use case | `replace_files` | Pack contents | Trust level |
|---|---|---|---|
| **Patch** | `true` (want overrides) | Changed files only, same paths as base game | You made it |
| **DLC** | either | New files under a namespaced folder (`res://dlc/winter/…`) | You made it |
| **Mod** | `false` (protect base files) | Third-party content, ideally data-only | Untrusted |

### Building a patch or DLC pack

Any export preset can produce a pack-only artifact: `Project → Export → Export PCK/ZIP`, or headless:

```bash
godot --headless --export-pack "Windows Release" build/patch_1_4_3.pck
```

For patches you do not want the *whole* project re-exported — Godot 4.x presets have a **Patches** tab for exactly this: register the base pack(s) of your shipped release, enable *Export as Patch*, and the exporter emits only resources that changed relative to the base. The result is a small pack you ship next to the game and mount at startup:

```gdscript
# autoload/patch_loader.gd — mount all patches, sorted, before any gameplay scene loads
const PATCH_DIR := "user://patches"

func _init() -> void:
    # _init of an early autoload: patches must be mounted BEFORE other
    # scenes/resources referencing patched files are loaded (see pitfall below).
    var dir := DirAccess.open(PATCH_DIR)
    if dir == null:
        return
    var packs: Array[String] = []
    for f in dir.get_files():
        if f.get_extension() == "pck":
            packs.append(PATCH_DIR.path_join(f))
    packs.sort()  # patch_001.pck, patch_002.pck… later wins
    for p in packs:
        if ProjectSettings.load_resource_pack(p):
            print("Mounted patch: ", p)
        else:
            push_warning("Failed to mount patch: " + p)
```

> ⚠️ **Pitfall** — Mounting packs too late. Resources already loaded (or `preload()`ed by an already-loaded script — and `preload` runs at script load time) keep their old data; the override only affects *future* loads. Mount patches in the `_init()` of your first autoload, before the main scene instantiates. If your title screen is `preload`ed anywhere in an autoload chain, the patched title screen will never appear.

Also remember `take_over_path()`-style subtleties in reverse: a patch can override `.remap`ped imported resources only if the patch was exported by the same engine version with the file re-imported — which the Patches tab handles for you, and hand-rolled packs often get wrong. Prefer the official patch export over DIY file-picking.

### Mods: the honest version

A mod is a PCK you did not author, mounted into your engine. Design constraints that follow:

- **Load with `replace_files = false`** so mods cannot silently replace your scripts or UI scenes.
- **Namespace by convention**: require mods to place content under `res://mods/<mod_id>/` and reject packs that touch anything else (walk the pack after mounting with the lister from §6 and unmount-by-restart if it violates the contract — there is no unmount API, which is itself a design input: validate *before* shipping a session that used the pack).
- **Scripts in mods execute with full engine privileges.** GDScript has no sandbox: a mod script can call `OS.execute()`, read the filesystem, and phone home. If you accept script mods, you accept arbitrary code execution and should say so to players; if that is unacceptable, restrict mods to data + assets and drive behavior from your own systems reading their JSON.
- Document engine-version coupling: packs written by 4.5 tooling are for 4.5 runtimes. After you upgrade the engine, old community packs may fail to load — announce pack-format breaks in release notes like any other API break.

```gdscript
# Data-only mod ingestion sketch (Relax Room decoration packs)
func load_decoration_mod(pck_path: String) -> bool:
    if not ProjectSettings.load_resource_pack(pck_path, false):
        return false
    var manifest_path := "res://mods/%s/manifest.json" % pck_path.get_file().get_basename()
    if not FileAccess.file_exists(manifest_path):
        push_warning("Mod rejected: no manifest at " + manifest_path)
        return false
    var manifest: Dictionary = JSON.parse_string(
        FileAccess.get_file_as_string(manifest_path))
    return DecorationCatalog.register_pack(manifest)
```

> ✅ **Best practice** — Ship your *own* content as DLC packs early even if you never sell DLC: it forces the loading order, path-namespacing and version-stamping discipline that patches and mods need, while everything is still under your control. Relax Room's seasonal "Winter Room" pack was internal DLC for exactly this reason.

### Integrity and version-stamping of external packs

A pack you download at runtime is an input from the network; treat it like one. Minimal hardening that costs an afternoon:

1. **Hash before mounting.** Publish the SHA-256 next to the pack (in your update JSON, §11); verify on disk before `load_resource_pack()` ever sees it:

```gdscript
# autoload/pack_verifier.gd
func verify_and_mount(pck_path: String, expected_sha256: String) -> bool:
    var ctx := HashingContext.new()
    if ctx.start(HashingContext.HASH_SHA256) != OK:
        return false
    var f := FileAccess.open(pck_path, FileAccess.READ)
    if f == null:
        return false
    while not f.eof_reached():
        ctx.update(f.get_buffer(1 << 20))       # 1 MiB chunks
    var digest := ctx.finish().hex_encode()
    if digest != expected_sha256.to_lower():
        push_warning("Pack rejected — hash mismatch: " + pck_path)
        DirAccess.remove_absolute(pck_path)      # quarantine, don't retry forever
        return false
    return ProjectSettings.load_resource_pack(pck_path, false)
```

2. **Stamp packs with their target version.** A manifest file inside every pack (`res://patches/<id>/manifest.json` with `{"for_version": "1.4.x", "created": "...", "engine": "4.5"}`) lets the loader refuse packs built for another release instead of crashing later in mysterious ways. Refusal UX beats corruption UX every time.

3. **Order is part of the contract.** The §8 loader sorts by filename; therefore patch filenames are versioned (`patch_0001.pck`). Document this for yourself — an unordered patch directory "works" until two patches touch the same file and the winner depends on filesystem enumeration order, which differs across OSes.

The limits are the same as §9's: a determined local user can bypass all of this — it defends against corruption, truncated downloads and stale CDNs, not against the machine's owner. That is the correct and sufficient goal.

### End-to-end: downloading and installing a content pack

The pieces assembled into the flow Relax Room uses for seasonal packs — server manifest, download, verify, mount, register:

```gdscript
# autoload/content_store.gd — minimal but production-shaped
const MANIFEST_URL := "https://cdn.relaxroom.app/packs/manifest.json"
const PACK_DIR := "user://packs"

signal pack_installed(pack_id: String)
signal pack_failed(pack_id: String, reason: String)

var _http: HTTPRequest

func _ready() -> void:
    _http = HTTPRequest.new()
    add_child(_http)
    DirAccess.make_dir_recursive_absolute(PACK_DIR)

func install_pack(entry: Dictionary) -> void:
    # entry from the manifest: { "id": "winter_2026", "url": "...",
    #   "sha256": "...", "for_version": "1.4", "size": 8123456 }
    var running: String = ProjectSettings.get_setting(
        "application/config/version", "0.0.0")
    if not running.begins_with(entry["for_version"]):
        pack_failed.emit(entry["id"], "needs game %s" % entry["for_version"])
        return
    var dest := PACK_DIR.path_join(entry["id"] + ".pck")
    _http.download_file = dest
    _http.request_completed.connect(
        _on_downloaded.bind(entry, dest), CONNECT_ONE_SHOT)
    var err := _http.request(entry["url"])
    if err != OK:
        pack_failed.emit(entry["id"], "request error %d" % err)

func _on_downloaded(_r: int, code: int, _h: PackedStringArray,
        _b: PackedByteArray, entry: Dictionary, dest: String) -> void:
    if code != 200:
        pack_failed.emit(entry["id"], "HTTP %d" % code)
        return
    # PackVerifier from earlier in this section: hash, then mount no-replace
    if not PackVerifier.verify_and_mount(dest, entry["sha256"]):
        pack_failed.emit(entry["id"], "verification failed")
        return
    # Content catalogs scan res:// (§7) — a rescan picks up the new pack
    DecorationCatalog.rescan()
    pack_installed.emit(entry["id"])
```

On next boot, the §8 patch loader mounts everything already in `user://packs/` — download-time and boot-time paths share the verifier, so a pack that passed once cannot rot silently (re-verify at mount if you are paranoid; it is one extra hash per boot). The deliberate omissions — resume, retry with backoff, disk-space checks — are exactly the §11 auto-updater lessons again: add them when a metric, not an instinct, says so.

---

## 9. PCK encryption and the GDScript compilation reality

Two questions arrive together from every team shipping their first commercial Godot build: "can players read our scripts?" and "can we stop them?". Precise answers, in order.

### What ships, by script export mode

The preset's *Script Export Mode* (`script_export_mode` in `export_presets.cfg`) controls the format of GDScript in the pack:

| Mode | Value | What ships | Readability |
|---|---|---|---|
| Text | 0 | Your `.gd` files verbatim | Fully readable, comments included |
| Binary tokens | 1 | Tokenized stream (`.gdc`) | Not text, but mechanically reversible |
| Compressed binary tokens | 2 (default) | Tokenized + compressed | Same, smaller |

Godot 4's binary tokens are a *tokenization*, not a compilation: identifiers, string literals and structure are preserved (they must be, for the VM to run them). Public tooling exists that reconstructs compilable — if comment-free — source from token streams. Treat binary tokens as a fast-loading transport format with mild opportunistic obfuscation, nothing more.

> ⚠️ **Pitfall** — A handful of reflection-heavy addons have broken under binary token export (they read scripts as text at runtime). If an addon misbehaves *only in exports*, test with Script Export Mode = Text before blaming your own code; then report/patch the addon rather than shipping text sources forever.

### What PCK encryption actually does

With encryption enabled, the exporter AES-256-CBC-encrypts the PCK index and the files matching your encryption filters, using a 256-bit key you provide. The runtime must decrypt them — therefore **the key must live inside the engine binary**, which official templates cannot do. The full recipe:

```bash
# 1. Generate a key (64 hex chars) — do this ONCE, store in a password manager
openssl rand -hex 32
# → e.g. aeb1bc56b45b5[...]f8d316

# 2. Compile BOTH templates with the key baked in (§4)
#    (Windows PowerShell)
$env:SCRIPT_AES256_ENCRYPTION_KEY = "aeb1bc56...f8d316"
scons platform=windows target=template_release arch=x86_64 production=yes
scons platform=windows target=template_debug   arch=x86_64

# 3. In the export preset: point Custom Template at these binaries,
#    tick Encrypt PCK (+ optionally Encrypt Index, filters for which files),
#    and paste the SAME key into the Encryption Key field
#    (stored in .godot/export_credentials.cfg — never committed; or
#     provide it via the GODOT_SCRIPT_ENCRYPTION_KEY env var in CI).
```

Threat-model honesty, which you owe your producer:

```
PCK encryption PREVENTS                 PCK encryption DOES NOT PREVENT
──────────────────────────              ────────────────────────────────
Casual unpacking with generic           A determined attacker extracting the
 PCK tools                               AES key FROM YOUR SHIPPED BINARY
Asset rips by non-technical users        (it must be there for the game to run)
Trivial script reading                  Memory dumping at runtime
Accidental spoiler mining               Screen/audio capture of assets
                                        Cheating via memory editors
                                        Determined reverse engineering
```

Encryption raises the effort floor from "download a tool" to "read a writeup"; it does not create secrecy. Anything genuinely secret — API keys, server credentials, monetization logic — must live server-side, never in the PCK, encrypted or not. Budget accordingly: for a cozy desktop companion like Relax Room, the team decided plain compressed tokens were enough and spent the custom-template effort on binary size instead. For a competitive multiplayer title, encrypt *and* assume it will be broken.

> ✅ **Best practice** — If you do encrypt: one key per product line (not per release — or old patches stop mounting), key generated once, stored in a team password manager and CI secret store, never in Git, never in chat. Losing the key means losing the ability to build compatible templates; leaking it means the encryption is decorative. And re-measure load times — decryption is cheap but not free on low-end disks.

### An encryption-enabled CI lane, sketched

If the decision lands on "encrypt", the pipeline changes in exactly three places relative to §17 — worth seeing to appreciate the ongoing cost:

```yaml
  # (1) A separate, rarely-run workflow builds and caches the custom templates
  build-templates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { repository: godotengine/godot, ref: 4.5-stable }
      - name: Build encrypted Linux templates
        env:
          SCRIPT_AES256_ENCRYPTION_KEY: ${{ secrets.PCK_KEY }}
        run: |
          scons platform=linuxbsd target=template_release arch=x86_64 production=yes
          scons platform=linuxbsd target=template_debug   arch=x86_64
      - uses: actions/upload-artifact@v4
        with: { name: templates-linux-encrypted, path: bin/, retention-days: 90 }

  # (2) Export jobs download those templates and point presets at them
  #     (custom_template/release paths in export_presets.cfg), and
  # (3) provide the key to the exporter:
  #        env: { GODOT_SCRIPT_ENCRYPTION_KEY: "${{ secrets.PCK_KEY }}" }
```

Multiply that template job by every platform you ship, re-run it on every engine upgrade, and keep its artifacts under the same protection as the key itself (an encrypted-template binary is a decryption oracle). This overhead is the honest price tag to weigh against §9's threat model — and why "encrypt because we can" is the wrong default and "encrypt because we priced it" is fine.

---

## 10. Windows export

Windows is the largest desktop audience and, for this course's desktop-companion focus, the primary target. The exporter itself is simple; the ecosystem around it (metadata, signing, SmartScreen, installers) is where the craft lives.

### Baseline export

`Project → Export → Add… → Windows Desktop`. The essential choices:

- **Architecture**: `x86_64` (default and correct for almost everyone), `x86_32` (legacy machines only), `arm64` (Windows-on-ARM laptops — a growing but still small audience; consider offering it as a separate download rather than skipping it).
- **Embed PCK**: single-file `.exe` vs `.exe + .pck` — trade-offs in §7. For the installer flow below, keep them separate.
- **Export path**: point at a `build/windows/` folder *outside* `res://`, or exclude it, or every export gets slower and dirtier as previous builds are scanned as project files.

Result sizes for a 2D project on official templates: roughly 55-75 MB engine binary plus your PCK. Do not panic-compare with a 5 MB SDL game — you are shipping a full engine; §19 covers what is actually trimmable.

### Your first Windows export, as a verification ritual

The mechanical walkthrough — worth following literally once, then encoding into the §16 script and the §18 checklist:

```
1. Project → Export → Add… → Windows Desktop
2. Export Path: a folder OUTSIDE the project
   (e.g. C:\Users\you\Builds\RelaxRoom\) — or gitignore + exclude build/
3. Architecture x86_64; Embed PCK per your §7 decision
4. "Export Project…" (untick "Export With Debug" for a release-flavor test)
5. Close the editor. Yes, really — you are testing the build, not the session.
6. Double-click the exe in Explorer and verify, minimum:
   [ ] Launches to the main menu without a console flash or error dialog
   [ ] Window title, icon and taskbar icon are yours, not Godot's
   [ ] A full gameplay loop works (Relax Room: place decoration → move it)
   [ ] Quit and relaunch: state persisted (saves went to user://, §7)
   [ ] Data-driven content present (open a catalog-driven panel — proves
       your *.json include filter, §6)
   [ ] Task Manager while idle: CPU where you expect it
7. Copy the folder to another machine (or clean VM) with no Godot installed;
   repeat step 6. THIS is the real test — your dev machine proves nothing
   about redistributables, drivers, or files that only exist locally.
```

Every line of that checklist exists because some project failed it. The ritual takes six minutes; each platform section below has an equivalent, and §18 aggregates them.

### Icon and version metadata (rcedit)

Windows executables carry an icon and a version-info block visible in Explorer's *Properties → Details* — and inspected by everything from SmartScreen heuristics to corporate allowlists. Godot edits these into the exported exe using **rcedit**, a small open-source tool you install once:

1. Download `rcedit-x64.exe` (github.com/electron/rcedit, releases page).
2. `Editor → Editor Settings → Export → Windows → rcedit`: set the path.
3. In the preset, fill **Application** section: icon (`.ico`), file/product version (`1.4.2.0` — four numeric fields), product name, company, description, copyright.

The `.ico` should contain 16, 32, 48, 64, 128 and 256 px layers; the project's SVG/PNG icon is auto-converted if you set nothing, but a hand-made ICO renders crisper at small sizes. ImageMagick one-liner:

```powershell
magick icon_256.png -define icon:auto-resize=16,32,48,64,128,256 icon.ico
```

> ⚠️ **Pitfall** — rcedit not configured (or Wine missing when exporting for Windows *from* Linux/macOS, where rcedit runs under Wine) does not fail the export: Godot just skips metadata and you ship an exe with the default Godot icon and empty version info. CI exports are especially prone to this because nobody eyeballs the artifact. Add a post-export check to your pipeline that reads the version resource and fails on mismatch.

### Code signing, SmartScreen, and the truth about certificates

An unsigned executable downloaded from the internet triggers Microsoft Defender SmartScreen: *"Windows protected your PC"*, with *Run anyway* hidden behind *More info*. What actually influences this:

- **No signature** — warning for every user until your file hash accumulates reputation (which resets every release, because the hash changes).
- **OV certificate** (organization-validated, ~$100-400/yr) — signature identifies you, but reputation still builds per-certificate over weeks; early downloads may still warn.
- **EV certificate** (extended-validation, hardware-token/cloud-HSM based, ~$250-700/yr) — historically granted near-immediate SmartScreen reputation; still the fastest route to a clean install experience.
- **Distribution via stores** (Steam, itch launcher, Microsoft Store) — the store's trust chain applies; players rarely see SmartScreen at all. For hobby and early-indie distribution this is the pragmatic answer.

Signing mechanics with the Windows SDK's `signtool` (Godot can also invoke it automatically — Editor Settings → Export → Windows → *Sign Tool*, plus the preset's *Codesign* section; on Linux/macOS use `osslsigncode`):

```powershell
# Sign with a PFX (OV) — timestamp server is NOT optional:
# without it the signature dies with the certificate's expiry.
signtool sign /f relaxroom.pfx /p $env:CERT_PASSWORD `
  /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 `
  .\build\windows\MiniCozyRoom.exe

# Verify
signtool verify /pa /v .\build\windows\MiniCozyRoom.exe
```

Sign **after** any rcedit-style binary modification (Godot orders this correctly when it drives both) and sign the *installer* too (§11) — an unsigned installer wrapping a signed exe still warns.

> ✅ **Best practice** — Decide your signing posture per-channel: releases signed, dev builds unsigned. Keep the certificate/token out of developer laptops; CI signs via a secrets-provisioned step. And never let a certificate expire mid-release-cycle — calendar it like a domain renewal.

### Console wrapper and logs

GUI Windows apps have no stdout. Godot's Windows export offers a **console wrapper** option (`debug/export_console_wrapper`): alongside `MiniCozyRoom.exe` it emits `MiniCozyRoom.console.exe`, which runs the same game with an attached console for logs. Ship it in dev/staging channels; exclude it from the player-facing installer, and rely on file logging (`user://logs/`, configured via project settings `debug/file_logging/enable_file_logging`) for release diagnostics.

### DLLs and runtime dependencies

The Godot 4 runtime is impressively self-contained — no Visual C++ Redistributable requirement for the engine itself. The dependency issues you will actually meet:

- **GDExtension DLLs** (e.g. `libgdsqlite.windows.template_release.x86_64.dll` for Relax Room's SQLite): the `.gdextension` file and the referenced DLLs must survive export filters. Missing platform binaries fail at startup with `Can't open dynamic library`.
- **ANGLE/D3D12 auxiliary DLLs** in some rendering configurations must sit next to the exe when not statically built; if you enable the D3D12 backend, follow its docs for `dxil.dll` placement.
- **OpenSSL, ffmpeg, etc.** from third-party addons: same rule — the addon's docs list the files; verify presence in the export directory in your release checklist.

### Desktop polish details players notice

Small settings, disproportionate perceived quality — all in project settings, all verified in the exported build, not in the editor:

| Setting | Where | Why it matters in exports |
|---|---|---|
| Boot splash image + background color | `application/boot_splash/*` | The first 1-3 seconds of your app; default is the Godot logo on grey, which reads as "unfinished" |
| Window title | `application/config/name` (+ overrides, §6) | Taskbar, Alt-Tab, screenshots |
| Icon set in-project | `application/config/icon` + Windows `.ico` (§10 above) | Taskbar/Explorer coherence — Windows shows the *exe* icon, so rcedit config is what wins here |
| Low-processor mode | `application/run/low_processor_mode` | For a desktop companion, idling at 1-3% CPU instead of a game loop's 15% is the difference between "always open" and "closed after a day" — see [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) |
| Single-instance guard | (code — check a `user://` lockfile or named pipe at boot) | Double-launching from an installer shortcut is common; two instances fighting over the SQLite database is not a bug report you want |

### The portable-mode pattern

Some Windows users explicitly want "no installer, no AppData — keep everything in the folder". Supporting both layouts from one binary is a small amount of code and a nice differentiator for a desktop tool:

```gdscript
# autoload/paths.gd — resolve the data directory once at boot
var data_dir: String

func _init() -> void:
    var exe_dir := OS.get_executable_path().get_base_dir()
    if FileAccess.file_exists(exe_dir.path_join("portable.txt")):
        # Portable mode: data lives next to the exe (fails under Program Files
        # by design — installer installs never contain portable.txt).
        data_dir = exe_dir.path_join("data")
        DirAccess.make_dir_recursive_absolute(data_dir)
    else:
        data_dir = OS.get_user_data_dir()   # the resolved user:// path
```

The portable zip artifact (§21) ships `portable.txt`; the installer does not. One binary, two distribution philosophies, zero forked builds — the same feature-tag-free technique also makes USB-stick QA copies self-contained.

### Case study — Relax Room on Windows

Relax Room ships three Windows artifacts per release: `Setup_RelaxRoom_<ver>.exe` (Inno Setup, the recommended download), a portable `.zip` (sidecar exe+pck, for USB-stick users — with file logging on by default because those users cannot be asked for consoles), and `MiniCozyRoom.console.exe` inside the staging channel only. Version metadata is stamped by CI from the Git tag (§17), so Explorer's *Details* tab is the ground truth when triaging "which build are you on?" support tickets.

---

## 11. Windows installer with Inno Setup 6

A zip is not a product. An installer sets expectations: shortcuts appear, an uninstaller registers, upgrades find the previous copy, and antivirus heuristics relax slightly. For Godot indies on Windows the field has one dominant free answer: **Inno Setup 6** (jrsoftware.org) — scriptable, mature, Unicode, actively maintained.

For due diligence, the alternatives and why this module commits to Inno:

| | Inno Setup 6 | NSIS | MSI (WiX) |
|---|---|---|---|
| Cost / license | Free | Free | Free |
| Authoring model | Declarative INI-like `.iss` + Pascal scripting for edge cases | Imperative script language | XML, steep learning curve |
| Wizard polish | Modern out of the box | Dated default UI, skinnable with effort | OS-native |
| Silent install | Built-in flags (below) | Built-in | msiexec standard |
| Upgrade-in-place | AppId mechanism, straightforward | Manual registry bookkeeping | Product/upgrade codes, powerful, verbose |
| Enterprise/GPO deploy | No (exe) | No | **Yes** — the one reason to choose MSI |
| Fit for a Godot indie | **Best default** | Fine if already known | Only for corporate-desktop distribution |

### Toolchain

- Install Inno Setup 6; the GUI *Compiler* is for authoring, the CLI `ISCC.exe` for automation:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\RelaxRoom.iss /DAppVersion=1.4.2
```

- On Linux CI, Inno runs under Wine — proven in practice, slightly fiddly to provision; many teams simply run the installer job on a `windows-latest` GitHub Actions runner instead (§17), which needs no Wine at all. Recent runner images ship Inno Setup preinstalled; otherwise `choco install innosetup` is one line.

### The annotated Relax Room script

The complete production `.iss`, kept in `installer/RelaxRoom.iss` in the repository. Every decision is commented — read it top to bottom once, then keep it as your project template.

```iss
; ============================================================
; Relax Room — Inno Setup 6 script
; Compile: ISCC.exe RelaxRoom.iss /DAppVersion=1.4.2
; ============================================================

#ifndef AppVersion
  #define AppVersion "0.0.0-dev"   ; CI passes the real version
#endif
#define AppName      "Relax Room"
#define AppExeName   "MiniCozyRoom.exe"
#define AppPublisher "IFTS Projectwork Team"

[Setup]
; AppId is THE identity of the installation. Never change it between
; versions or upgrades will install side-by-side instead of in place.
; Generate once (Tools -> Generate GUID in the Inno IDE) and freeze it.
AppId={{8B1F41E6-4C0A-4E1B-9D0A-2F5C7E1A9B33}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://relaxroom.example.app
AppSupportURL=https://relaxroom.example.app/support

; Per-user install: no UAC prompt, lands under {localappdata}\Programs.
; This suits a desktop companion; switch to admin+{autopf} for
; machine-wide installs (then installer must be elevated).
PrivilegesRequired=lowest
DefaultDirName={autopf}\RelaxRoom
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; Upgrade-in-place niceties
CloseApplications=yes            ; ask running app to close before upgrade
RestartApplications=no
UsePreviousAppDir=yes            ; reuse the dir the user chose last time

; Output artifact
OutputDir=..\build\installer
OutputBaseFilename=Setup_RelaxRoom_{#AppVersion}
SetupIconFile=..\art\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}

; Compression: lzma2/max is the sweet spot; 'ultra64' saves a few MB
; more at a large compile-time cost.
Compression=lzma2/max
SolidCompression=yes

; Modern look on 4K displays
WizardStyle=modern

; Refuse to run on unsupported Windows (Godot 4 needs 10+)
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
; Unchecked by default — desktop icons are the user's choice, not yours.
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
  GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
; Optional file association for .relaxroom scene-share files
Name: "assoc"; Description: "Associate .relaxroom files"; Flags: unchecked

[Files]
; The exported build. 'ignoreversion' forces overwrite on upgrade even
; though Godot binaries carry version resources; the PCK has none anyway.
Source: "..\build\windows\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\build\windows\MiniCozyRoom.pck"; DestDir: "{app}"; Flags: ignoreversion
; GDExtension binaries travel outside the PCK
Source: "..\build\windows\*.dll"; DestDir: "{app}"; Flags: ignoreversion
; Player-facing docs
Source: "..\CHANGELOG.md"; DestDir: "{app}"; DestName: "CHANGELOG.txt"; Flags: ignoreversion
Source: "..\LICENSES\THIRD_PARTY.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Changelog"; Filename: "{app}\CHANGELOG.txt"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; File association (only when the task is chosen). HKA = HKCU for
; per-user installs, HKLM for admin installs — matches PrivilegesRequired.
Root: HKA; Subkey: "Software\Classes\.relaxroom"; ValueType: string; \
  ValueData: "RelaxRoomFile"; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\RelaxRoomFile"; ValueType: string; \
  ValueData: "Relax Room shared scene"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\RelaxRoomFile\DefaultIcon"; ValueType: string; \
  ValueData: "{app}\{#AppExeName},0"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\RelaxRoomFile\shell\open\command"; \
  ValueType: string; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc

[Run]
; Offer to launch after install; skipped in silent mode.
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean runtime droppings inside {app} only. NEVER touch user:// here —
; save data outlives the app unless the player explicitly opts in.
Type: filesandordirs; Name: "{app}\logs"

[Code]
{ Optional: offer save-data removal on uninstall, defaulting to KEEP. }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  SaveDir: string;
begin
  if CurUninstallStep = usPostUninstall then begin
    SaveDir := ExpandConstant('{userappdata}') + '\Godot\app_userdata\Relax Room';
    if DirExists(SaveDir) then
      if MsgBox('Remove your saved rooms and settings as well?',
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DelTree(SaveDir, True, True, True);
  end;
end;
```

### Silent installation and enterprise-friendliness

Every Inno installer automatically supports silent flags — worth documenting for power users and IT departments:

| Flag | Effect |
|---|---|
| `/SILENT` | No wizard; progress window only |
| `/VERYSILENT` | Nothing shown at all |
| `/SUPPRESSMSGBOXES` | Auto-answer dialogs (combine with a silent flag) |
| `/NORESTART` | Never reboot automatically |
| `/DIR="C:\Games\RelaxRoom"` | Override install directory |
| `/TASKS="desktopicon"` / `/MERGETASKS="!desktopicon"` | Pre-select / deselect tasks |
| `/LOG` | Write a setup log to `%TEMP%` |
| `/CURRENTUSER` · `/ALLUSERS` | Force per-user vs per-machine mode |

```powershell
# Fully unattended upgrade, used by Relax Room's self-updater:
Setup_RelaxRoom_1.4.2.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

### Versioning and upgrade-in-place

The contract that makes upgrades boring (the goal):

1. **`AppId` constant forever** — Inno finds the existing install by AppId, reuses its directory (`UsePreviousAppDir`), replaces files, updates the uninstaller entry. Change the AppId and you get two entries in *Apps & features* and two copies on disk.
2. **`AppVersion` from CI** — passed with `/DAppVersion=` from the Git tag; never hand-edited (drift between exe metadata, installer version and in-game About screen is amateur hour; single source of truth in §18).
3. **`ignoreversion` on game files** — Godot's PCK carries no Windows version resource, so without this flag "file exists, version equal" logic can skip stale files.
4. **Never delete user data on upgrade**, and on *uninstall* only with explicit consent (the `[Code]` section above).
5. **Guard against accidental downgrades** — a player running an old installer over a new install (mirrors serve stale files more often than you'd think) should be warned, not silently reverted:

```iss
[Code]
function InitializeSetup(): Boolean;
var
  Installed: string;
begin
  Result := True;
  if RegQueryStringValue(HKA,
      'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1',
      'DisplayVersion', Installed) then
    if CompareStr(Installed, '{#AppVersion}') > 0 then
      Result := MsgBox('Version ' + Installed + ' is already installed. ' +
        'Install older version {#AppVersion} anyway?',
        mbConfirmation, MB_YESNO) = IDYES;
end;
```

   (String comparison is fine while every segment stays single-digit; parse numerically past `.9` — or better, never let a stale mirror exist: §17's single artifact source.)

### Auto-update approaches for indie desktop apps

Ranked by effort:

1. **Store-managed (zero effort):** distribute via itch.io (players use the itch app, delta updates included) or Steam (depot diffing). The correct default.
2. **Notify-only:** on startup, fetch `https://…/latest.json` (version + download URL + SHA-256), compare against the running version, show a "1.5 is available" toast linking to the download. One HTTP request, no installer logic, works with plain Inno. This is what Relax Room ships.
3. **Self-updating:** download the new installer, verify its hash, run it with `/VERYSILENT` on next quit. Feasible with the script above (`CloseApplications=yes` handles the file-lock dance) but you now own download resume, hash verification, rollback and signature checking. Adopt only when metrics show notify-only losing too many users mid-funnel.

> ⚠️ **Pitfall** — Testing installers only on your dev machine, where previous versions, registry leftovers and your user profile hide bugs. Test in a fresh Windows VM (or Windows Sandbox): clean install → launch → upgrade over it → uninstall → verify what remains. Every release. It takes eight minutes and catches the classics: missing DLL, shortcut to nowhere, uninstaller leaving the association behind.

> ✅ **Best practice** — Sign the installer with the same certificate as the game exe, and give the installer its own line in the pre-release checklist (§18). Players meet `Setup_….exe` before they meet your game; it is a first impression with an error budget of zero.

### The portable zip, produced in the same breath

Since §21's release matrix ships a portable zip alongside the installer, script both from the same staged files so they can never diverge:

```powershell
# tools/package_windows.ps1 — installer + portable zip from one staging dir
param([Parameter(Mandatory)][string]$Version)
$ErrorActionPreference = "Stop"
$stage = "build\windows"                 # output of the Godot export (§16)

# 1. Installer
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" `
    installer\RelaxRoom.iss /DAppVersion=$Version
if ($LASTEXITCODE -ne 0) { throw "ISCC failed" }

# 2. Portable zip: same files + the portable-mode marker (§10)
$portable = "build\portable\RelaxRoom-$Version-portable"
New-Item -ItemType Directory -Force $portable | Out-Null
Copy-Item "$stage\*" $portable -Recurse
Set-Content "$portable\portable.txt" "This file keeps all data in .\data — delete it to use standard Windows profiles."
Set-Content "$portable\README.txt" @"
Relax Room $Version (portable)
Run MiniCozyRoom.exe. Your rooms are saved in the 'data' folder next to it.
Windows may show a SmartScreen warning for downloaded unsigned software:
choose 'More info' -> 'Run anyway'. Installer version available at ...
"@
Compress-Archive "$portable\*" "build\portable\RelaxRoom-$Version-portable.zip" -Force
```

Note the README's honesty about SmartScreen: if you ship unsigned (§10), *tell* users what they will see and why. A one-paragraph explanation converts a scary dialog into an informed choice; silence converts it into a deleted download.

### Localizing the installer

Relax Room's installer ships English and Italian (`[Languages]` in the script). Three details beyond listing `.isl` files:

- Custom strings go in `[CustomMessages]` with per-language variants; reference them as `{cm:Name}`:

```iss
[CustomMessages]
english.KeepSaves=Remove your saved rooms and settings as well?
italian.KeepSaves=Rimuovere anche le stanze salvate e le impostazioni?
```

- The wizard auto-selects the UI language from Windows unless you show the language dialog; for a two-language app, auto-select is friendlier.
- Language coverage should match the *game's* locale list (see the localization notes in [GAME_DEV_PLANNING.md](GAME_DEV_PLANNING.md)) — an Italian installer for an English-only game over-promises.

---

## 12. Linux export — AppImage, Flatpak, Steam runtime

Linux players are few but disproportionately valuable: they file the best bug reports, they buy on principle, and the Steam Deck made "Linux support" quietly mainstream. Godot's Linux story is also the smoothest of all platforms — the same `linuxbsd` export you test in CI is the one players run.

### Baseline Linux export

`Project → Export → Add… → Linux/X11`. Architectures: `x86_64` (default), `arm64` (Raspberry Pi 4+, ARM laptops), plus 32-bit variants you can ignore in 2026. Output is `MiniCozyRoom.x86_64` plus a sidecar `.pck` (or embedded).

Two Unix facts that surprise Windows-based teams:

1. **Executable bit.** Files zipped on Windows lose the execute permission; a player downloading your zip gets *"Permission denied"*. Fixes: package on Linux (CI does this naturally), use `tar.gz` instead of zip (preserves modes), or document `chmod +x MiniCozyRoom.x86_64`. AppImage packaging (below) sidesteps the issue since the AppImage itself is the only file needing the bit — and every tutorial covers that.
2. **Filesystem case-sensitivity.** `res://Assets/Couch.png` and `res://assets/couch.png` are the same file on Windows/macOS default filesystems and *different* files on Linux. Godot's `res://` layer is consistent, but preloads written with wrong case, files referenced from JSON catalogs, and `user://` paths built by string concatenation will break only on Linux. Add a CI lint that verifies every path literal in your data files exists with exact case (cheap: run the check on the Linux runner where the mismatch actually errors).

Compatibility across distributions is mostly a **glibc floor**: binaries link against the glibc of the machine (or container) that built the *templates* — official templates are built on an old baseline precisely so they run on old distros. Your own custom templates inherit whatever your build box has; build them in an old-baseline container if you distribute widely.

### AppImage packaging walkthrough

An AppImage is a self-mounting filesystem image: one file, `chmod +x`, run — no install, no root, no dependency resolution. It is the closest Linux equivalent to "just an exe" and the friendliest default for indie distribution outside stores.

Structure you must produce (an `AppDir`), then compress with `appimagetool`:

```bash
#!/usr/bin/env bash
# tools/make_appimage.sh — run after the Linux export
set -euo pipefail
VERSION="${1:?usage: make_appimage.sh <version>}"
APPDIR=build/RelaxRoom.AppDir

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# 1. Game files
cp build/linux/MiniCozyRoom.x86_64 "$APPDIR/usr/bin/"
cp build/linux/MiniCozyRoom.pck    "$APPDIR/usr/bin/"
cp build/linux/*.so                "$APPDIR/usr/bin/" 2>/dev/null || true
chmod +x "$APPDIR/usr/bin/MiniCozyRoom.x86_64"

# 2. Desktop entry (also used by menus if the user integrates the AppImage)
cat > "$APPDIR/relaxroom.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Relax Room
Comment=A cozy desktop companion
Exec=MiniCozyRoom.x86_64
Icon=relaxroom
Categories=Game;Amusement;
Terminal=false
EOF

# 3. Icon (top level name must match Icon= key)
cp art/icon_256.png "$APPDIR/relaxroom.png"
cp art/icon_256.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/relaxroom.png"

# 4. AppRun — entry point; keep it dumb
cat > "$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/MiniCozyRoom.x86_64" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# 5. Pack it
appimagetool "$APPDIR" "build/RelaxRoom-${VERSION}-x86_64.AppImage"
```

Notes: `appimagetool` is itself distributed as an AppImage; on container CI without FUSE, run it with `--appimage-extract-and-run`. Godot's runtime is self-contained enough that you rarely need to bundle extra `.so` libraries beyond GDExtensions — resist the AppImage-community habit of shipping half a distro.

### The .desktop file outside AppImage

If you ship a plain tarball, include the `.desktop` file anyway with installation instructions (`~/.local/share/applications/`), or your app has no menu entry, no icon in docks, and no file-manager association. The `Categories=` line determines menu placement; validate with `desktop-file-validate`.

The tarball itself, done right (permissions preserved, top-level folder, validation baked in):

```bash
# tools/make_tarball.sh — the non-AppImage Linux artifact
set -euo pipefail
VERSION="${1:?}"
STAGE="RelaxRoom-${VERSION}-linux-x86_64"
rm -rf "build/$STAGE" && mkdir -p "build/$STAGE"
cp build/linux/MiniCozyRoom.x86_64 build/linux/MiniCozyRoom.pck "build/$STAGE/"
cp packaging/relaxroom.desktop packaging/icon_256.png "build/$STAGE/"
cp packaging/README-linux.txt "build/$STAGE/README.txt"
chmod +x "build/$STAGE/MiniCozyRoom.x86_64"
desktop-file-validate "build/$STAGE/relaxroom.desktop"   # fail early, not in a bug report
tar -C build -czf "build/${STAGE}.tar.gz" "$STAGE"       # tar preserves the exec bit
```

### Flatpak and Steam Runtime, briefly

- **Flatpak/Flathub** is the Linux app store with real discovery. Packaging means writing a manifest (JSON/YAML) that downloads your release artifact and installs it into a sandbox; Godot games use the `org.freedesktop.Platform` runtime, and the sandbox mostly Just Works because Godot writes only to `user://` (mapped into the sandbox's XDG dirs). Costs: a review process, sandbox portals for anything exotic (global hotkeys — relevant to desktop companions! — need the portal API), and a second distribution channel to keep updated. Worth it once the direct-download channel is stable.
- **Steam** ships its own runtime (a fixed library environment, currently Sniper for new titles). Godot binaries are compatible out of the box; upload via `steamcmd` and mark the depot for the runtime. Steam Deck verification adds UI/controller requirements orthogonal to exporting.

A Flatpak manifest, to make "more complex setup" concrete — this is most of one for a Godot game (the rest is metainfo/screenshots for the Flathub listing):

```yaml
# app.relaxroom.RelaxRoom.yml — Flatpak manifest sketch
app-id: app.relaxroom.RelaxRoom
runtime: org.freedesktop.Platform
runtime-version: "24.08"
sdk: org.freedesktop.Sdk
command: relaxroom
finish-args:
  - --socket=wayland
  - --socket=fallback-x11
  - --device=dri            # GPU access
  - --socket=pulseaudio
  # NOTE: no --filesystem access — user:// maps to the sandbox's XDG dirs,
  # which is exactly why Godot apps sandbox cleanly.
modules:
  - name: relaxroom
    buildsystem: simple
    build-commands:
      - install -Dm755 MiniCozyRoom.x86_64 /app/bin/relaxroom-bin
      - install -Dm644 MiniCozyRoom.pck /app/bin/MiniCozyRoom.pck
      - install -Dm755 relaxroom.sh /app/bin/relaxroom
      - install -Dm644 relaxroom.desktop /app/share/applications/app.relaxroom.RelaxRoom.desktop
      - install -Dm644 icon_256.png /app/share/icons/hicolor/256x256/apps/app.relaxroom.RelaxRoom.png
    sources:
      - type: file
        url: https://github.com/.../v1.4.2/RelaxRoom-linux.zip
        sha256: <release artifact hash — §18's manifest again>
```

### Autostart and tray integration for desktop companions

A companion app wants to be *present* — launched at login, living in the tray. On Linux this is another `.desktop` file, in a different directory:

```bash
# Installed to ~/.config/autostart/ (per-user login autostart, XDG standard)
cat > ~/.config/autostart/relaxroom.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Relax Room
Exec=/path/to/MiniCozyRoom.x86_64 --minimized
X-GNOME-Autostart-enabled=true
EOF
```

Offer it as an in-app toggle that writes/removes the file — never install autostart silently; it is the fastest way to an uninstall. (Windows equivalent: a `Run`-key registry value or Startup-folder shortcut, which the Inno script can create behind an unchecked `[Tasks]` entry; the same consent rule applies.) Tray icons themselves come from Godot's `StatusIndicator` node on supporting desktops — test per distro, tray support on Linux is famously uneven; the Flatpak sandbox additionally needs the StatusNotifier talk permission.

> ✅ **Best practice** — Whatever the packaging, test on a distro you do not develop on (Ubuntu dev → test Fedora VM). Library assumptions, theme fonts, Wayland-vs-X11 quirks (Godot 4.5 defaults to Wayland where available — test both; `--display-driver x11` forces the fallback) surface only across that gap.

> ⚠️ **Pitfall** — Shipping only an AppImage built on a bleeding-edge distro with custom templates: it will refuse to start on older glibc systems with a cryptic `version GLIBC_2.38 not found`. Official templates avoid this; custom template builders must pin an old build container (the reason distributions like `debian:11` remain popular as build baselines years after release).

---

## 13. macOS export — signing and notarization

macOS is the platform where distribution policy dominates engineering. The export itself is two clicks; getting the result to *open* on someone else's Mac without scary dialogs is the actual work. Understand the trust ladder first, then automate your chosen rung.

### The .app bundle

Godot exports a **Universal 2** binary — one `.app` containing both `x86_64` (Intel) and `arm64` (Apple Silicon) slices; no separate downloads needed. Wrapper formats: `.zip` (exportable from any OS), `.dmg` (the classic drag-to-Applications disk image; only produced when exporting *from* macOS), or a bare `.app`.

```
MiniCozyRoom.app/
└── Contents/
    ├── Info.plist            ← bundle id, version, category, min OS
    ├── MacOS/
    │   └── MiniCozyRoom      ← universal binary (engine)
    ├── Resources/
    │   ├── MiniCozyRoom.pck
    │   └── icon.icns
    ├── Frameworks/           ← GDExtension .dylib/.framework files
    └── _CodeSignature/       ← created by signing
```

The **bundle identifier** (`com.iftsteam.relaxroom` — reverse-DNS, alphanumeric/hyphen/period) is the app's identity for Gatekeeper, preferences and notarization; freeze it like Inno's AppId.

> ⚠️ **Pitfall** — Exporting a `.zip` from Windows, unzipping on macOS, and the app won't start: Windows zips drop the executable bit, exactly as in §12. Fix on a Mac/Linux shell: `chmod +x MiniCozyRoom.app/Contents/MacOS/*` (and `Contents/Helpers/*` if present), then re-zip *on that machine* with `ditto -c -k --keepParent`. Better: let CI's macOS runner produce the zip.

### The trust ladder

| Rung | What you do | What the player sees |
|---|---|---|
| 0. Unsigned/ad-hoc, direct download | Export with `Built-in (ad-hoc only)` signing | *"…is damaged and can't be opened"* or unidentified-developer block; player must right-click → Open, or `xattr -cr` the app, or approve in System Settings → Privacy & Security |
| 1. Developer ID signed | $99/yr Apple Developer; sign with a *Developer ID Application* cert | Warning reduced but downloads are still quarantined pending… |
| 2. …Notarized + stapled | Upload to Apple's automated scan (notarytool), staple the ticket | Opens normally. This is the bar for public distribution |
| 3. Mac App Store | Different cert type + App Sandbox + review | Store distribution |

Rung 0 is genuinely acceptable for playtesters and jam builds if you document the right-click→Open dance (the quarantine flag `com.apple.quarantine` is applied by browsers; files copied via `scp`/USB skip it entirely — why "works from my USB stick" proves nothing). Public releases should be rung 2.

### Signing and notarization workflow (rung 2)

Prerequisites: Apple Developer Program membership, a *Developer ID Application* certificate in your keychain (create via Xcode → Settings → Accounts), and Xcode command-line tools.

Godot automates most of this from the export dialog on macOS: set *Code Signing → Codesign* to `Xcode codesign`, identity to your certificate name, and *Notarization → notarytool* with an App Store Connect API key or Apple-ID app-specific password. For pipeline literacy, the manual equivalent:

```bash
# 1. Sign (hardened runtime is REQUIRED for notarization; Godot's export
#    enables the needed entitlements — disable the Debugging entitlement
#    ("allow-jit"/get-task-allow family) for release, or notarization fails)
codesign --force --deep --options runtime --timestamp \
  --sign "Developer ID Application: IFTS Projectwork Team (TEAMID123)" \
  MiniCozyRoom.app

# 2. Zip for submission
ditto -c -k --keepParent MiniCozyRoom.app MiniCozyRoom.zip

# 3. Notarize (store credentials once with `xcrun notarytool store-credentials`)
xcrun notarytool submit MiniCozyRoom.zip \
  --keychain-profile "relaxroom-notary" --wait
# --wait blocks until Accepted/Invalid; typical wall time: 1-15 minutes

# 4. Inspect failures when Invalid
xcrun notarytool log <submission-id> --keychain-profile "relaxroom-notary"

# 5. Staple the ticket INTO the app so offline machines can verify
xcrun stapler staple MiniCozyRoom.app

# 6. Verify like a player's Mac would
spctl --assess --type execute --verbose MiniCozyRoom.app
# → accepted, source=Notarized Developer ID
```

Then package the stapled app into your distribution `.dmg`/`.zip`. Common notarization rejections: debugging entitlement left on, un-signed nested GDExtension dylibs (sign *inside-out*: dylibs first, then the app — Godot's exporter handles bundled extensions when driven from the editor), missing secure timestamp, or SDK-too-old templates after an Apple policy tightening (upgrade Godot patch releases).

The classic drag-to-Applications disk image, from the stapled app:

```bash
# 7. Package as DMG (macOS only; UDZO = compressed read-only image)
hdiutil create -volname "Relax Room" -srcfolder MiniCozyRoom.app \
  -ov -format UDZO RelaxRoom-1.4.2.dmg

# Optional polish: a staging folder containing the .app plus an
# /Applications symlink gives the familiar "drag here" layout:
mkdir -p dmg_stage && cp -R MiniCozyRoom.app dmg_stage/
ln -s /Applications dmg_stage/Applications
hdiutil create -volname "Relax Room" -srcfolder dmg_stage \
  -ov -format UDZO RelaxRoom-1.4.2.dmg

# The DMG itself can (and for tidiness should) be signed too:
codesign --sign "Developer ID Application: …" --timestamp RelaxRoom-1.4.2.dmg
```

And the platform's condensed release ritual, mirroring §10's Windows walkthrough:

```
macOS packaging checklist
[ ] Bundle identifier frozen; version strings CI-stamped in Info.plist
[ ] Universal binary confirmed: lipo -archs Contents/MacOS/MiniCozyRoom
    → x86_64 arm64
[ ] Signed with hardened runtime; debugging entitlement OFF
[ ] Notarized (Accepted) and STAPLED — verify offline with
    spctl --assess after disconnecting from network once
[ ] DMG/zip built from the stapled app (staple first, package second)
[ ] Downloaded-copy test on a second Mac/account (quarantine real)
[ ] user:// save-compat spot check if upgrading (same rules as §18)
```

**No Mac at all?** Godot supports signing/notarizing from Windows/Linux via **rcodesign** (a Rust reimplementation: set its path in Editor Settings → Export → macOS, use a PKCS#12 cert + App Store Connect API key). It works and is CI-friendly; a real macOS runner (§17) still gives you the ability to *launch* the result, which rcodesign cannot.

> ✅ **Best practice** — Notarization is an upload-and-wait step with rare multi-hour tail latency at Apple's side; put it in CI with `--wait`, but never as a blocking step of the same job that produces other platforms' artifacts. Isolate it so a slow Apple day doesn't hostage your whole release.

> ⚠️ **Pitfall** — Testing only on your own Mac, where your developer certificate and previously-granted permissions mask everything. The honest test: upload the final artifact somewhere, download it in Safari on a different user account (or a friend's Mac), and open it. Quarantine is applied at download; anything else is a simulation.

### Info.plist and entitlements quick reference

The export dialog writes these for you, but release engineers read what they ship. The keys that matter, and where Godot's preset fields land:

| Info.plist key | Preset source | Notes |
|---|---|---|
| `CFBundleIdentifier` | Application → Bundle Identifier | Frozen forever (Gatekeeper, prefs, notarization identity) |
| `CFBundleShortVersionString` | Application → Short Version | Human version (`1.4.2`) — CI-stamped |
| `CFBundleVersion` | Application → Version | Build number; must increase for App Store |
| `LSMinimumSystemVersion` | Application → Min macOS Version | Players below it get a clean "requires macOS X" instead of a crash |
| `LSApplicationCategoryType` | Application → App Category | Required for App Store, good hygiene elsewhere |
| `NSHumanReadableCopyright` | Application → Copyright | Shows in Finder's Get Info |

Entitlements (the hardened-runtime permission list baked into the signature) worth knowing by name: `com.apple.security.cs.allow-jit` and friends (disable for release — notarization), `com.apple.security.device.audio-input` (only if you record — triggers a mic-permission prompt with your usage string), `com.apple.security.app-sandbox` (mandatory App Store, optional Developer ID). Godot's export dialog exposes each as a checkbox; the discipline is the same as Android permissions — minimum set, reviewed at release, because every entitlement is attack surface and every permission prompt is churn.

### A note on iOS

iOS export exists and works (Godot emits an Xcode project you archive and upload), but everything compounds: macOS + Xcode required, Apple Developer membership, provisioning profiles per device for testing, App Store review as the only distribution channel, and the same Compatibility-renderer/web-adjacent constraints on plugins. For this course's desktop-companion scope it is out of budget; the transferable knowledge is that the *pipeline shape* is identical — preset → headless export of the Xcode project → `xcodebuild archive` → `notarytool`-equivalent (App Store Connect upload) in a macOS CI job. If a future project needs iOS, you will recognize every step.

---

## 14. Android export — SDK, keystores, APK/AAB

Android is the most setup-heavy export target: a Java toolchain, the Android SDK, signing keystores and store policy all gate your first build. The good news: once configured, Godot's one-click deploy makes Android iteration *faster* than desktop. Do the setup once, document it, and enjoy.

### Toolchain setup

Requirements as of Godot 4.5 (check the official *Exporting for Android* page when versions drift):

| Component | Version | Notes |
|---|---|---|
| OpenJDK | **17** | Newer works, 17 is the recommended/tested baseline. Not 8, not 11. |
| Android SDK Platform-Tools | 35+ | Provides `adb` |
| Android SDK Build-Tools | 35.x | |
| SDK Platform | android-35 | Target API level; Play requires staying current |
| NDK + CMake | r28x / 3.10.x | Only needed for **gradle builds** (below) |

Install via Android Studio (easiest; its SDK Manager handles all of the above) or headless via `sdkmanager`:

```bash
# Headless SDK provisioning (CI or minimal machines)
sdkmanager --sdk_root="$ANDROID_HOME" \
  "platform-tools" "build-tools;35.0.1" "platforms;android-35" \
  "cmdline-tools;latest"
```

Then in Godot: `Editor → Editor Settings → Export → Android` — set **Java SDK Path** (the JDK 17 root) and **Android SDK Path** (the folder containing `platform-tools/adb`). The export dialog turns its error icons green when paths are right.

### Keystores: the part you cannot undo

Android packages are identified by signature. Two keystores exist in your life:

- **Debug keystore** — for development installs. Godot can generate/use a standard one; devices accept it; Play does not.
- **Release keystore** — signs what you publish. **The key alias inside it is your app's identity forever.** Lose it and — unless you enrolled in Play App Signing, below — you can never update your app again; a new keystore means a new app listing, zero installed base, reviews gone.

```bash
# Create the release keystore ONCE. Answer the prompts truthfully;
# validity must outlive your app (10000 days ≈ 27 years).
keytool -v -genkey -keystore relaxroom-release.keystore \
  -alias relaxroom -keyalg RSA -keysize 2048 -validity 10000

# Inspect it later (you will forget the alias — everyone does)
keytool -list -v -keystore relaxroom-release.keystore
```

Backup strategy, non-negotiable:

```
relaxroom-release.keystore  +  its two passwords (store & key)
  ├── Team password manager (primary)
  ├── Encrypted offline copy (USB in a drawer that isn't your office)
  └── CI secret store (base64-encoded, §17)
NEVER in: Git, Slack/Discord, email, screenshots, "temp" folders.
Add to .gitignore TODAY:  *.keystore  *.jks
```

**Play App Signing** (default for new Play Console apps) has Google hold the *app signing key* while you sign uploads with an *upload key* — lose the upload key and Google can reset it. Enroll; it converts a company-ending mistake into a support ticket. You still protect the upload keystore with the same discipline.

In the export preset, fill `Keystore → Debug/Release`, `…User` (the alias) and `…Password` fields — all of which land in `.godot/export_credentials.cfg` (§5), or come from `GODOT_ANDROID_KEYSTORE_*` environment variables in CI.

### APK vs AAB

| | APK | AAB (Android App Bundle) |
|---|---|---|
| Installable directly? | Yes (`adb install`, sideload) | No — Play generates device-optimized APKs from it |
| Google Play | Legacy only | **Required** for all new apps since August 2021 |
| itch.io / F-Droid / direct | ✓ the format to use | ✗ |
| Godot requirement | Standard export | **Gradle build required** |
| Size delivered to user | Full fat | Split per ABI/density/language — smaller |

Practical rule: develop and test with APKs; produce an AAB only in the Play-release lane of your pipeline.

### Gradle builds: when the default template isn't enough

The standard Android export wraps your PCK in a prebuilt APK template — fast and sufficient for most games. A **gradle build** (`Options → Gradle Build → Use Gradle Build` in the preset, after `Project → Install Android Build Template…`) compiles a real Android project in `android/build/` instead. You need it when:

- exporting **AAB** (always requires gradle),
- using Android plugins (play services, ads, notifications, editor plugins v2),
- customizing `AndroidManifest.xml`/resources beyond what the preset exposes,
- integrating product flavors or your own Java/Kotlin code.

Gradle builds are slower (first build downloads the Gradle world) and add the NDK/CMake requirements — hence "when needed", not "by default".

Housekeeping once gradle is on: the `android/` directory created by *Install Android Build Template* is generated tooling — commit the pristine template if you customize its manifest (so customizations are reviewable), but gitignore `android/build/` outputs and Gradle caches; and re-run the template install after every editor upgrade, because the template version-pairs with the engine exactly like export templates do (a mismatch produces gradle errors that look like your fault and are not).

### Preset essentials

- **Package → Unique Name**: `com.iftsteam.relaxroom` — same freeze-forever rule as bundle IDs.
- **Version → Code**: integer, must strictly increase every Play upload; **Version → Name**: the human string (`1.4.2`). CI stamps both (§17).
- **Architectures**: `arm64-v8a` on (required by Play), `armeabi-v7a` optional for very old devices, x86 flavors only for emulators/ChromeOS.
- **Permissions**: request the minimum. A cozy companion app needs `INTERNET` (if it syncs) and nothing else; every extra permission is a store-listing red flag and review question.
- **Icons**: adaptive icon foreground/background layers (432×432 within a 108dp safe zone) plus legacy 192×192 — the preset has explicit slots; missing ones fall back to the Godot robot, which is an embarrassing thing to discover in the Play listing. Design constraints that matter: the launcher masks your layers into circles/squircles/rounded squares per device, so keep all meaningful content inside the central ~66% of the foreground and give the background a full-bleed solid or subtle texture — a desktop icon with edge-to-edge detail gets decapitated by the mask. Test with Android Studio's Asset Studio preview or simply install on two devices with different launcher shapes.

### One-click deploy and device testing

Enable *Developer options → USB debugging* on a device, plug it in, and the Android icon in the editor's top-right deploys, installs and launches your game with the debugger attached — `print()` output and errors stream back to the editor. This loop (edit → one click → running on the phone in ~15 s) is the payoff for the toolchain slog. CLI equivalents:

```bash
adb devices                          # is the device authorized?
adb install -r MiniCozyRoom.apk      # -r = reinstall keeping data
adb logcat -s godot                  # engine log stream from the device
adb shell run-as com.iftsteam.relaxroom ls files/   # inspect user:// (debug builds)
```

### Play Console flow, minimally

1. One-time developer registration ($25).
2. Create the app; complete the *App content* declarations (privacy policy URL — mandatory; data-safety form; content rating questionnaire via IARC; target audience).
3. Upload the AAB to **Internal testing** first (available to your testers in minutes), promote through Closed/Open testing to Production. New personal accounts face a mandatory closed-testing period before production — plan weeks, not days.
4. Each subsequent upload: bump `version/code`, tag, let CI build and sign, upload.

The Play release lane as a checklist, complementing §18's general one:

```
FIRST RELEASE ONLY
[ ] Package name final (frozen forever); Play App Signing enrolled
[ ] Store listing: descriptions, screenshots per form factor, feature graphic
[ ] Privacy policy URL live; Data-safety form matches what the app DOES
[ ] Content rating questionnaire (IARC) completed
[ ] Closed-testing requirement satisfied (new accounts)

EVERY RELEASE
[ ] version/code strictly greater than every previous upload
[ ] AAB built by CI from the tag, signed with the upload key
[ ] Release notes per locale pasted from the changelog (§18)
[ ] Rollout staged (e.g. 20% → 100%) — Play supports it natively; use it
[ ] Pre-launch report reviewed (Play runs the build on real devices — free QA)
```

> ⚠️ **Pitfall** — "App not installed" / `INSTALL_FAILED_UPDATE_INCOMPATIBLE` on a device that already has the game: the installed copy is signed with a different key (debug vs release, or another machine's debug keystore). `adb uninstall com.iftsteam.relaxroom` and retry. The same signature rule is *why* the release keystore is sacred (see backup strategy above).

> ✅ **Best practice** — Keep a `docs/android_setup.md` in the repo recording exact JDK/SDK versions and editor-settings paths. Android is the platform where "new teammate can't build" costs a day; the doc reduces it to thirty minutes.

### Permissions, storage and lifecycle notes

Concrete guidance the preset's long permission checklist doesn't give you:

- **`INTERNET`** — the only permission Relax Room requests, and only in builds where cloud sync ships. Request-at-need beats request-at-install everywhere.
- **Storage permissions are usually a smell** in Godot 4: `user://` maps to app-private internal storage (`/data/data/<package>/files/`), needs *no* permission, survives updates, and is removed on uninstall. You need `READ_MEDIA_*`/SAF only to touch the user's shared files (e.g. importing their music — which Relax Room's Android build simply disables via feature detection instead).
- **The SQLite database works unchanged**: godot-sqlite ships `arm64` binaries and the `user://relax.db` path resolves into the sandbox — the persistence layer from [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md) required zero Android-specific code.
- **Lifecycle**: Android pauses you aggressively. Wire `NOTIFICATION_APPLICATION_PAUSED` to flush saves immediately — "I switched apps and lost my room" is the mobile equivalent of the uninstaller-ate-my-saves bug (§11).

```gdscript
func _notification(what: int) -> void:
    match what:
        NOTIFICATION_APPLICATION_PAUSED:      # Android/iOS: may be killed after this
            SaveManager.flush_now()
        NOTIFICATION_WM_CLOSE_REQUEST:        # Desktop window close
            SaveManager.flush_now()
            get_tree().quit()
```

### adb field guide

The ten commands that cover a release week of device debugging:

```bash
adb devices -l                        # connected? authorized? which model?
adb install -r build/RelaxRoom.apk    # (re)install keeping app data
adb uninstall com.iftsteam.relaxroom  # nuke it (signature conflicts, §pitfall)
adb logcat -s godot                   # only Godot's log stream
adb logcat -c && adb logcat > boot.log  # clean capture of one repro
adb shell am start -n com.iftsteam.relaxroom/.GodotApp   # launch from CLI
adb shell am force-stop com.iftsteam.relaxroom           # kill it
adb shell run-as com.iftsteam.relaxroom ls files/        # inspect user:// (debug)
adb pull /sdcard/Download/report.txt                     # grab files off device
adb shell dumpsys battery unplug      # test on-battery behavior while cabled
```

Wireless debugging (`adb pair` / `adb connect` on Android 11+) frees the USB port and, more importantly, lets you test cable-free scenarios — a companion app's typical resting state.

---

## 15. Web export — an honest assessment

The web export produces genuinely magical demos — your Godot game in a browser tab, no install — and genuinely painful production surprises. This section is the honest brief for deciding *whether* to ship web, then doing it right.

### What the export produces

`Project → Export → Add… → Web` emits an HTML shell plus `MiniCozyRoom.js`, `MiniCozyRoom.wasm` (the engine, compiled to WebAssembly), `MiniCozyRoom.pck`, service-worker/PWA files if enabled. Godot 4's web renderer targets **WebGL 2.0 via the Compatibility rendering method only** — Forward+/Mobile (Vulkan) do not run in browsers. If your project isn't on the Compatibility renderer, the web build will look different or not run; Relax Room chose Compatibility from day one partly for this reason ([RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md)).

### The threads decision and the header tax

WebAssembly threads require `SharedArrayBuffer`, which browsers only enable under **cross-origin isolation** — your hosting must send two HTTP headers on the page:

```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

Since 4.3, Godot's default web export is **single-threaded (Thread Support off)** — slower in CPU-bound scenes but: no headers required, hostable on any static file host, and *much* better compatibility, notably with Safari on iOS and macOS. Decision table:

| | Threads OFF (default) | Threads ON |
|---|---|---|
| Hosting | Any static host | Must control response headers |
| itch.io | ✓ (has a SharedArrayBuffer toggle too) | ✓ with the toggle enabled |
| GitHub Pages | ✓ | ✗ (cannot set headers) — unless you use the PWA workaround |
| iOS Safari | Works (best available) | Historically problematic |
| Performance | Adequate for 2D/light 3D | Better under CPU load |

The **PWA workaround**: enabling *Progressive Web App* in the preset installs a service worker that simulates the isolation headers client-side — it can make threads work on header-less hosts, at the cost of service-worker cache-invalidation headaches (players "still seeing the old build" is almost always this; document a hard-refresh/unregister step for yourself).

The PWA option is also a *feature* independent of the header trick: it emits a web manifest (name, icons, display mode) and offline caching, letting players "install" the game from the browser to their home screen/desktop and relaunch it without a network. For a demo this is mostly free polish — fill in the PWA icon slots (144/180/512 px) and the offline-page option in the preset, and budget one QA pass for the update-propagation behavior, because the same service worker that enables offline play is the one that serves stale builds when you forget it exists.

### Limits you must design around

- **No C# web export** in Godot 4.x — GDScript projects only.
- **Audio**: since 4.3 the default web playback is the low-latency "Sample" path via Web Audio; `AudioEffect`s are unsupported there — switch `Audio → General → Default Playback Type.web` to "Stream" if your mix depends on bus effects, accepting latency. All audio starts only after a user gesture (browser autoplay policy): design a "click to start" screen.
- **`user://` is IndexedDB**: persistence works but is at the mercy of browser site-data settings and eviction; offer an export-save-to-file button for anything precious.
- **Filesystem/OS access**: none — no native file dialogs (Web File API via JavaScript bridge only), no `OS.execute`, no window management. Feature-tag such code paths (`OS.has_feature("web")`, §6).
- **GDExtensions** must ship a `wasm32` binary — most (including godot-sqlite) do not, or do so experimentally. Relax Room's web demo therefore runs the JSON persistence path only ([DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md)).
- **Size = startup time**: the wasm engine is tens of MB; served with gzip it roughly quarters, Brotli better still — configure compression on the host, and consider a size-optimized custom template (§4) for a serious web product.

### Serving and testing locally

Browsers refuse `file://` — you need HTTP even locally. Fastest options: the editor's **Run in Browser** button (the remote-debug icon after installing web templates — it serves with correct headers automatically), or a tiny server:

```powershell
# Threads OFF build: any static server is fine
python -m http.server 8060 --directory build\web
# then browse to http://localhost:8060/MiniCozyRoom.html
```

For threads-ON builds your local server must send the COOP/COEP headers (the editor's Run in Browser does; plain `http.server` does not — use Godot's `serve.py` helper or any configurable server).

### When web builds make sense

✓ Jam entries and prototypes (zero-install feedback), marketing demos of a desktop game ("try 5 minutes in the browser, buy the full version"), genuinely small 2D games, educational embeds.
✗ As the *only* SKU of a content-heavy game, anything needing native integrations (tray icons, global hotkeys — the entire desktop-companion genre), or projects unwilling to maintain a second persistence/audio path.

Relax Room ships web as a **feature-limited demo** — §21 — and that framing (demo, not port) dissolved most of the pain: SQLite off, import off, three rooms only, one honest banner saying so.

> ⚠️ **Pitfall** — Blank page after deploy with a console error mentioning `SharedArrayBuffer` or cross-origin isolation: your build has Thread Support on but the host sends no COOP/COEP headers. Either re-export with threads off, enable the host's isolation support (itch has a checkbox), or enable the PWA workaround. This single mismatch accounts for the majority of "web export is broken" posts.

> ✅ **Best practice** — Treat the web build as its own product with its own preset, feature flags, QA pass (Chrome + Firefox + one Safari), and size budget. "Also exported for web" with desktop assumptions intact is how you earn one-star jam comments from iPhone users.

### Customizing the shell and talking to the page

The exported HTML file is a generated shell — editing it directly is futile (regenerated every export). The supported customization points:

- **Head Include** (preset → HTML → Head Include): inject analytics, fonts, or meta tags into the generated page.
- **Custom HTML Shell** (preset → HTML → Custom HTML Shell): replace the whole page with your own template containing the engine-start placeholders — the route for branded loaders and itch-page-perfect canvas sizing. Keep your shell in `res://web/shell.html` under version control; it is part of the build recipe.
- **JavaScriptBridge** for runtime page interaction:

```gdscript
# Web-only: open the full-game store page from the demo's buy button
func _on_buy_pressed() -> void:
    if OS.has_feature("web"):
        JavaScriptBridge.eval("window.open('https://ifts-team.itch.io/relax-room','_blank')")

# Read a query parameter (e.g. ?room=zen for marketing deep links)
func _get_query_param(name: String) -> String:
    if not OS.has_feature("web"):
        return ""
    return str(JavaScriptBridge.eval(
        "new URLSearchParams(window.location.search).get('%s') || ''" % name))
```

`JavaScriptBridge.eval()` runs in the page's context — the same mechanism supports clipboard access, fullscreen requests and download-a-file flows (`user://` save export, §15's advice). Guard every call behind the `web` feature tag; the singleton exists only there.

### Web deploy checklist (condensed)

```
[ ] Threads OFF unless the host provably sends COOP/COEP
[ ] Gzip/Brotli enabled on .wasm/.pck (check response headers, not assumptions)
[ ] "Click to start" gate before any audio
[ ] Cache-busting strategy for updates (versioned paths or SW cache bump)
[ ] Tested: Chrome, Firefox, Safari (one Apple device minimum)
[ ] Feature-gated: file dialogs, SQLite, window management, OS.execute
[ ] itch: "This file will be played in the browser" + viewport dimensions set
```

---

## 16. Headless builds and CLI automation

Everything the export dialog does, the binary does from a terminal. This is the load-bearing section of the module: scripted exports are what make CI (§17), reproducibility and "release = run one command" possible.

### The core incantation

```bash
godot --headless --path /abs/path/to/project --import
godot --headless --path /abs/path/to/project \
      --export-release "Windows Release" build/windows/MiniCozyRoom.exe
```

Flag by flag:

- **`--headless`** — no window, no GPU, dummy audio. Mandatory on servers; harmless locally. (Equivalent to `--display-driver headless --audio-driver Dummy`.)
- **`--path <dir>`** — the directory containing `project.godot`. Prefer this over `cd`-ing around; note the *export output* path is then resolved relative to the project, not your shell's cwd.
- **`--import`** — start the editor logic, import all resources (populating `.godot/imported/`), quit. On a fresh clone this is the step that turns source assets into loadable ones (§2). It implies `--editor --quit`.
- **`--export-release "<preset name>" [path]`** — export using the named preset with the release template. The preset name must match `export_presets.cfg` exactly (case, spaces). The path argument must include the file name and extension; omit it to use the preset's stored `export_path`.
- **`--export-debug`** — same with debug templates (and it implies `--import`, as does `--export-pack`).
- **`--export-pack "<preset>" out.pck`** — pack only, no executable (§8).

The export *destination directory must exist* — Godot will not `mkdir -p` for you; your script does that. And quote preset names always; `Windows Release` unquoted becomes two arguments and an inscrutable error.

> ⚠️ **Pitfall** — Relying on `--export-release` to also import. In practice a cold cache plus certain importers (notably anything triggering shader/asset processing that expects more editor lifetime) produces flaky, order-dependent failures. The boring, always-correct sequence is two invocations: `--import` first, then export. Idempotent, cacheable, debuggable.

### Exit codes and failure detection

`godot` returns `0` on success and non-zero on failures — but historically some import/export error paths have been *softer* than a build system wants (warnings that should be errors, partial failures with exit 0). Defensive scripting:

```bash
#!/usr/bin/env bash
# tools/build_all.sh — local release build, Linux/macOS/WSL/Git Bash
set -euo pipefail

GODOT="${GODOT_BIN:-godot}"          # allow overriding the binary
PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$PROJECT/build"
VERSION="${1:?usage: build_all.sh <version>}"

echo "==> Engine: $($GODOT --version)"

echo "==> Import"
"$GODOT" --headless --path "$PROJECT" --import

declare -A TARGETS=(
  ["Windows Release"]="windows/MiniCozyRoom.exe"
  ["Linux Release"]="linux/MiniCozyRoom.x86_64"
  ["Web Demo"]="web/MiniCozyRoom.html"
)

for preset in "${!TARGETS[@]}"; do
  out="$BUILD/${TARGETS[$preset]}"
  mkdir -p "$(dirname "$out")"
  echo "==> Export: $preset -> $out"
  "$GODOT" --headless --path "$PROJECT" --export-release "$preset" "$out"
  # Belt and braces: exit code AND artifact existence AND non-trivial size
  [[ -s "$out" ]] || { echo "FATAL: missing artifact $out"; exit 1; }
done

echo "==> OK — built version $VERSION"
```

The PowerShell twin, because this course's primary dev environment is Windows:

```powershell
# tools/build_all.ps1
param([Parameter(Mandatory)][string]$Version)
$ErrorActionPreference = "Stop"
$Godot   = $env:GODOT_BIN; if (-not $Godot) { $Godot = "godot" }
$Project = Split-Path $PSScriptRoot -Parent

& $Godot --version
& $Godot --headless --path $Project --import
if ($LASTEXITCODE -ne 0) { throw "Import failed ($LASTEXITCODE)" }

$targets = @{
  "Windows Release" = "build\windows\MiniCozyRoom.exe"
  "Web Demo"        = "build\web\MiniCozyRoom.html"
}
foreach ($preset in $targets.Keys) {
  $out = Join-Path $Project $targets[$preset]
  New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null
  & $Godot --headless --path $Project --export-release $preset $out
  if ($LASTEXITCODE -ne 0) { throw "Export '$preset' failed ($LASTEXITCODE)" }
  if (-not (Test-Path $out) -or (Get-Item $out).Length -lt 1MB) {
    throw "Artifact missing or suspiciously small: $out"
  }
}
Write-Host "OK — built version $Version"
```

Also useful in pipelines: `--version` (assert the engine before doing anything — a wrong-version Godot on PATH is a silent build-corruption machine), `-s script.gd` (run a `SceneTree`-derived script — the PCK lister in §6, test runners, asset validators), and `--quit-after N` for smoke tests ("does the exported build boot?" — run the export with `--quit-after 2` in a virtual framebuffer and check the exit code).

A boot smoke test in full, because it is the highest-value fifteen lines in this module — it catches missing GDExtensions, broken autoloads and absent data files in seconds, before any human downloads an artifact:

```bash
# tools/smoke_test.sh — boot the exported Linux build headless-ish for 3 frames
set -euo pipefail
BUILD="${1:?usage: smoke_test.sh <path-to-binary>}"
chmod +x "$BUILD"

# xvfb provides a virtual display; the exported build is NOT headless-capable
# by itself (templates need a display driver unless exported as dedicated server)
timeout 60 xvfb-run --auto-servernum "$BUILD" --quit-after 3 --verbose \
  > smoke.log 2>&1 || { echo "BOOT FAILED — tail of log:"; tail -30 smoke.log; exit 1; }

# Belt and braces: scan the log for script errors that didn't kill the process
if grep -E "SCRIPT ERROR|Cannot open|Failed loading resource" smoke.log; then
  echo "Boot completed but errors were logged"; exit 1
fi
echo "Smoke test OK"
```

Autoload design determines how much this test can see: fail-fast autoloads that `push_error` and quit on missing dependencies ([AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md)) turn "boots but broken" into "fails loudly in CI", which is the entire point.

The Windows-runner variant needs no virtual display (runners have a desktop session) but does need the console-wrapper trick to capture output, since GUI exes detach from stdout (§10):

```powershell
# tools/smoke_test.ps1 — boot the Windows export for 3 frames on windows-latest
param([Parameter(Mandatory)][string]$ExePath)
$console = $ExePath -replace "\.exe$", ".console.exe"
$bin = if (Test-Path $console) { $console } else { $ExePath }
$p = Start-Process -FilePath $bin -ArgumentList "--quit-after","3","--verbose" `
     -RedirectStandardOutput smoke.log -RedirectStandardError smoke.err `
     -PassThru -NoNewWindow
if (-not $p.WaitForExit(60000)) { $p.Kill(); throw "Boot timed out" }
if ($p.ExitCode -ne 0) { Get-Content smoke.log -Tail 30; throw "Boot failed ($($p.ExitCode))" }
if (Select-String -Path smoke.log,smoke.err -Pattern "SCRIPT ERROR|Cannot open" -Quiet) {
    throw "Boot completed with logged errors"
}
Write-Host "Smoke test OK"
```

Ship the console wrapper in the *dev/staging* export used by CI and exclude it from the player installer — the same artifact split §10 recommended, now earning its keep.

### Exit codes and log conventions, summarized

| Signal | Meaning in a build pipeline | Your script's response |
|---|---|---|
| exit `0` | Command believes it succeeded | Trust but verify: artifact exists + size floor |
| exit non-zero | Import/export/script failure | Fail the job; print the last 30 log lines |
| `SCRIPT ERROR:` in output | GDScript runtime error (may not change exit code in soft paths) | Grep for it; treat as failure in smoke tests |
| `ERROR:`/`WARNING:` at import | Broken/missing source assets | Fail on ERROR; budget WARNINGs (track count, fail on increase) |
| Artifact present but tiny | Export "succeeded" without template/PCK content | Size floors per artifact type (exe > 40 MB, pck > your known floor) |

The WARNING-count budget deserves a sentence: import warnings accumulate silently in healthy projects until one of them is the bug. Recording the count per build (`grep -c "WARNING:" import.log`) and failing when it *rises* costs nothing and converts entropy into a review comment at the PR that introduced it.

### Reproducible builds

"Reproducible" here means: two runs from the same commit produce functionally identical artifacts, and *any team machine or runner produces what the release machine produces*. The checklist:

1. **Pin the engine**: the exact editor version and templates are recorded (README + CI config) and asserted at build start (`godot --version` vs expected string).
2. **Pin the inputs**: presets committed, `.import` files committed, no machine-local editor overrides affecting export (audit `Editor Settings → Export` paths — rcedit/signtool locations belong in per-machine setup docs, their *versions* in the repo).
3. **Clean-room rule**: CI builds from a fresh clone + fresh import — never from a long-lived working directory. If a build "only works" on the machine with the warm `.godot/` cache, you have a latent broken release.
4. **One version source**: the Git tag drives every version string (§17/§18); no hand-edited numbers anywhere.
5. Accept that *byte*-identical output is not the goal (timestamps and signing are inherently variable); *behavioral* identity is.

> ✅ **Best practice** — Even as a solo developer, run releases only through the script, and run the script periodically on a machine that is not yours (or a fresh VM). The pipeline is a tested product like the game; a release process exercised for the first time on release day has a 100% historical failure rate in this course's projects.

---

## 17. CI/CD with GitHub Actions

Continuous integration for a Godot project has two distinct jobs-of-work: **verification** on every push (lint, test — established in [GAME_DEV_PLANNING.md](GAME_DEV_PLANNING.md)) and **delivery** on tags (export everything, package, publish). This section builds the full workflow, explains each choice, and flags the sharp edges.

### Getting Godot onto a runner

Three viable strategies:

| Strategy | How | Trade-off |
|---|---|---|
| Setup action | e.g. `chickensoft-games/setup-godot` — installs editor+templates, caches | Simplest YAML; depends on a third-party action |
| Container image | `container: barichello/godot-ci:4.5` (the godot-ci project) — Godot + templates preinstalled | Fast, hermetic; Linux jobs only |
| Raw download | `wget` the editor zip + templates `.tpz`, place per §3 | No dependencies, most transparent; most YAML |

All three are legitimate; the workflow below uses the raw download for the export job (so you *see* the mechanics once) — swap in a setup action freely afterward.

### The complete release workflow

`.github/workflows/release.yml` — verification on every push/PR, delivery on `v*` tags:

```yaml
name: Build & Release

on:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:

env:
  GODOT_VERSION: "4.5"
  PROJECT_DIR: "v1"          # Relax Room keeps the project in v1/
  APP_NAME: "MiniCozyRoom"

jobs:
  # ── 1. VERIFY ────────────────────────────────────────────────
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install "gdtoolkit==4.*"
      - run: gdlint ${{ env.PROJECT_DIR }}/scripts/
      - run: gdformat --check ${{ env.PROJECT_DIR }}/scripts/

  test:
    runs-on: ubuntu-latest
    container:
      image: barichello/godot-ci:4.5
    steps:
      - uses: actions/checkout@v4
      - name: Import resources
        run: godot --headless --path ${{ env.PROJECT_DIR }} --import
      - name: Run GdUnit4 suite
        run: |
          godot --headless --path ${{ env.PROJECT_DIR }} \
            -s addons/gdUnit4/bin/GdUnitCmdTool.gd --add "res://tests/" -c
      # Test strategy and suite layout: see GAME_DEV_PLANNING.md

  # ── 2. EXPORT MATRIX (tags only) ─────────────────────────────
  export:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: [quality, test]
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false                # one platform failing shouldn't hide others
      matrix:
        include:
          - preset: "Windows Release"
            out: "windows/MiniCozyRoom.exe"
            artifact: "windows"
          - preset: "Linux Release"
            out: "linux/MiniCozyRoom.x86_64"
            artifact: "linux"
          - preset: "Web Demo"
            out: "web/index.html"
            artifact: "web"
    steps:
      - uses: actions/checkout@v4

      - name: Cache Godot + templates
        id: godot-cache
        uses: actions/cache@v4
        with:
          path: |
            ~/godot-bin
            ~/.local/share/godot/export_templates
          key: godot-${{ env.GODOT_VERSION }}-stable

      - name: Install Godot + export templates
        if: steps.godot-cache.outputs.cache-hit != 'true'
        run: |
          set -e
          BASE="https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable"
          mkdir -p ~/godot-bin
          wget -q "$BASE/Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip"
          unzip -q Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip
          mv Godot_v${GODOT_VERSION}-stable_linux.x86_64 ~/godot-bin/godot
          wget -q "$BASE/Godot_v${GODOT_VERSION}-stable_export_templates.tpz"
          mkdir -p ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable
          unzip -q Godot_v${GODOT_VERSION}-stable_export_templates.tpz
          mv templates/* ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable/

      - name: Stamp version from tag into project settings
        run: |
          VERSION="${GITHUB_REF_NAME#v}"        # v1.4.2 -> 1.4.2
          ~/godot-bin/godot --headless --path ${{ env.PROJECT_DIR }} \
            -s tools/stamp_version.gd -- "$VERSION"
          echo "VERSION=$VERSION" >> "$GITHUB_ENV"

      - name: Import resources
        run: ~/godot-bin/godot --headless --path ${{ env.PROJECT_DIR }} --import

      - name: Export ${{ matrix.preset }}
        run: |
          mkdir -p build/$(dirname "${{ matrix.out }}")
          ~/godot-bin/godot --headless --path ${{ env.PROJECT_DIR }} \
            --export-release "${{ matrix.preset }}" \
            "$GITHUB_WORKSPACE/build/${{ matrix.out }}"
          test -s "$GITHUB_WORKSPACE/build/${{ matrix.out }}"

      - uses: actions/upload-artifact@v4
        with:
          name: ${{ env.APP_NAME }}-${{ matrix.artifact }}-${{ env.VERSION }}
          path: build/${{ matrix.artifact }}
          if-no-files-found: error

  # ── 3. WINDOWS INSTALLER (needs a Windows runner for Inno) ──
  installer:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: export
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          pattern: "*-windows-*"
          merge-multiple: true
          path: build/windows
      - name: Compile Inno Setup installer
        shell: pwsh
        run: |
          $version = "${env:GITHUB_REF_NAME}".TrimStart("v")
          & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" `
            installer\RelaxRoom.iss /DAppVersion=$version
      - uses: actions/upload-artifact@v4
        with:
          name: installer-windows
          path: build/installer/*.exe

  # ── 4. RELEASE ON TAG ────────────────────────────────────────
  release:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: [export, installer]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/download-artifact@v4
        with: { path: dist }
      - name: Zip platform folders
        run: |
          cd dist
          for d in */ ; do (cd "$d" && zip -qr "../${d%/}.zip" .) ; done
      - uses: softprops/action-gh-release@v2
        with:
          files: dist/*.zip
          generate_release_notes: true
          draft: true          # human presses the final button (§18 checklist)
```

### Version stamping from the tag

The single-source-of-truth rule made executable — the tag is the version, and a tiny tool script writes it into `project.godot` before import/export so `ProjectSettings` carries it at runtime:

```gdscript
# tools/stamp_version.gd
# Usage: godot --headless --path . -s tools/stamp_version.gd -- 1.4.2
extends SceneTree

func _init() -> void:
    var args := OS.get_cmdline_user_args()
    if args.is_empty():
        push_error("stamp_version.gd: missing version argument")
        quit(1); return
    var version: String = args[0]
    ProjectSettings.set_setting("application/config/version", version)
    var err := ProjectSettings.save()
    if err != OK:
        push_error("Could not save project settings: %s" % err)
        quit(1); return
    print("Stamped version: ", version)
    quit(0)
```

```gdscript
# Anywhere in the game (About screen, log header, crash reports):
var version: String = ProjectSettings.get_setting("application/config/version", "0.0.0-dev")
```

And the consuming end — the About-screen widget that closes the loop and doubles as the support team's best friend:

```gdscript
# ui/about_version_label.gd — attach to a Label in the About/settings scene
extends Label

func _ready() -> void:
    var version: String = ProjectSettings.get_setting(
        "application/config/version", "0.0.0-dev")
    var channel := "release"
    if OS.has_feature("dev_tools"): channel = "dev"
    elif OS.has_feature("staging"): channel = "staging"
    elif OS.has_feature("demo"):    channel = "demo"
    var flavor := "debug" if OS.is_debug_build() else "release"
    text = "v%s (%s, %s, %s)" % [version, channel, OS.get_name(), flavor]
    # e.g. "v1.4.2 (release, Windows, release)" — one screenshot from a
    # player answers the first three triage questions.
```

The same `$VERSION` feeds the Windows preset's `application/file_version` (sed/`--script` edit if you want Explorer metadata in lockstep), the Inno `/DAppVersion`, and the artifact names — one tag, five consistent surfaces.

### Secrets in the pipeline

Signing keys and keystores enter CI exactly one way: repository **Settings → Secrets**, injected as env vars, decoded at job start, never echoed:

```yaml
      - name: Provision Android release keystore
        env:
          KEYSTORE_B64: ${{ secrets.ANDROID_KEYSTORE_BASE64 }}
        run: |
          echo "$KEYSTORE_B64" | base64 -d > /tmp/release.keystore
      - name: Export AAB
        env:
          GODOT_ANDROID_KEYSTORE_RELEASE_PATH: /tmp/release.keystore
          GODOT_ANDROID_KEYSTORE_RELEASE_USER: ${{ secrets.ANDROID_KEYSTORE_USER }}
          GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD: ${{ secrets.ANDROID_KEYSTORE_PASSWORD }}
        run: |
          ~/godot-bin/godot --headless --path ${{ env.PROJECT_DIR }} \
            --export-release "Android Play" build/android/RelaxRoom.aab
```

The complete Android job, since its container needs differ from the desktop matrix (JDK + SDK provisioning is the whole game):

```yaml
  export-android:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: [quality, test]
    runs-on: ubuntu-latest
    container:
      image: barichello/godot-ci:4.5     # ships Godot + templates + Android SDK
    steps:
      - uses: actions/checkout@v4
      - name: Provision release keystore from secrets
        env:
          KEYSTORE_B64: ${{ secrets.ANDROID_KEYSTORE_BASE64 }}
        run: echo "$KEYSTORE_B64" | base64 -d > /tmp/release.keystore
      - name: Stamp version + version code from tag
        run: |
          VERSION="${GITHUB_REF_NAME#v}"
          IFS=. read -r MA MI PA <<< "$VERSION"
          CODE=$((MA*10000 + MI*100 + PA))
          godot --headless --path ${{ env.PROJECT_DIR }} \
            -s tools/stamp_version.gd -- "$VERSION" "$CODE"
      - name: Import + export AAB
        env:
          GODOT_ANDROID_KEYSTORE_RELEASE_PATH: /tmp/release.keystore
          GODOT_ANDROID_KEYSTORE_RELEASE_USER: ${{ secrets.ANDROID_KEYSTORE_USER }}
          GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD: ${{ secrets.ANDROID_KEYSTORE_PASSWORD }}
        run: |
          godot --headless --path ${{ env.PROJECT_DIR }} --import
          mkdir -p build/android
          godot --headless --path ${{ env.PROJECT_DIR }} \
            --export-release "Android Play" \
            "$GITHUB_WORKSPACE/build/android/RelaxRoom.aab"
          test -s "$GITHUB_WORKSPACE/build/android/RelaxRoom.aab"
      - uses: actions/upload-artifact@v4
        with: { name: android-aab, path: build/android, if-no-files-found: error }
```

(The `stamp_version.gd` from earlier grows a second argument writing the derived code into the preset — a three-line extension left as part of Lab 6.) A macOS lane follows the same pattern on `runs-on: macos-latest` with the editor's official macOS binary, the §13 signing/notarization steps driven by keychain-profile secrets, and — per §13's advice — isolated from the other platforms so Apple's latency never blocks them.

> ⚠️ **Pitfall** — Cache poisoning: caching `.godot/` between runs *feels* like a huge import-time win and works — until an engine upgrade or import-setting change leaves stale artifacts that export "successfully" into a broken build. If you cache the import directory, key the cache on engine version + a hash of all `*.import` files, and be ready to nuke it as debugging step one. Caching only the *engine + templates* (as above) is the safe 90% of the win.

> ⚠️ **Pitfall** — Testing tag builds for the first time on release day. Tag-gated jobs (`if: startsWith(github.ref, 'refs/tags/')`) are exactly the jobs that never ran on your PRs. Push `v0.0.1-rc1`-style throwaway tags to a test branch periodically, or add a `workflow_dispatch` trigger so the delivery lane can be rehearsed on demand.

> ✅ **Best practice** — Keep `draft: true` on the release step. CI produces and attaches everything; a human reads the checklist (§18), spot-checks one artifact per platform, edits the generated notes, and presses publish. Full automation of the *last* step buys seconds and sells you a class of irreversible mistakes.

### Publishing to itch.io from the same workflow

Once the human publishes the GitHub release, a final job (or a manually-dispatched one) pushes channels to itch with butler — the delivery loop closed end to end:

```yaml
  itch:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: release
    runs-on: ubuntu-latest
    environment: production        # require manual approval in repo settings
    steps:
      - uses: actions/download-artifact@v4
        with: { path: dist }
      - name: Install butler
        run: |
          curl -sL https://broth.itch.zone/butler/linux-amd64/LATEST/archive/default -o butler.zip
          unzip -q butler.zip && chmod +x butler
      - name: Push channels
        env:
          BUTLER_API_KEY: ${{ secrets.BUTLER_API_KEY }}
        run: |
          VERSION="${GITHUB_REF_NAME#v}"
          ./butler push dist/*windows* ifts-team/relax-room:windows --userversion "$VERSION"
          ./butler push dist/*linux*   ifts-team/relax-room:linux   --userversion "$VERSION"
          ./butler push dist/*web*     ifts-team/relax-room:web-demo --userversion "$VERSION"
```

The `environment: production` line is GitHub's built-in manual gate — the YAML equivalent of the draft-release philosophy, applied to the store push.

### Nightly builds and pipeline hygiene

Two additions worth their YAML once a team exceeds one person:

```yaml
on:
  schedule:
    - cron: "0 2 * * *"        # nightly at 02:00 UTC: full export matrix
  workflow_dispatch:            # and on-demand rehearsals of the tag lane
    inputs:
      version:
        description: "Version to stamp (rehearsal only)"
        default: "0.0.0-nightly"

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: true      # a re-pushed tag must not race its own build
```

The nightly's job is *drift detection*: it exports everything and runs the smoke tests even when nobody tagged, so "the export lane broke three weeks ago" becomes "the export lane broke last night". Morning routine: nightly green — carry on; nightly red — fix before feature work, because a broken pipeline silently converts every future release into an emergency. This is the indie-scaled version of the studio build-farm discipline: same principle, one runner instead of forty:

```
Studio scale                              Indie scale (this module)
┌─────────┐ ┌─────────┐ ┌─────────┐       ┌──────────────────────────┐
│ Windows │ │  macOS  │ │  Linux  │       │ GitHub-hosted runners     │
│ builder │ │ builder │ │ builder │  ═══  │ ubuntu / windows / macos  │
└────┬────┘ └────┬────┘ └────┬────┘       │ (matrix, §17)             │
     └─────┬─────┴─────┬─────┘            └────────────┬─────────────┘
     ┌─────▼─────┐ ┌───▼──────┐                 ┌──────▼──────┐
     │ artifact  │ │ QA team  │           ═══   │ GH artifacts│
     │ storage   │ │ downloads│                 │ + checklist │
     │ (S3/GCS)  │ │ nightly  │                 │  human (§18)│
     └───────────┘ └──────────┘                 └─────────────┘
```

The economics differ; the invariants don't: every platform built from clean state on every cycle, artifacts stored addressably, and a human consuming the result daily. When your team grows, you scale the boxes, not the shape.

> ✅ **Best practice** — Post the nightly's status somewhere humans look (Discord webhook, badge in the README). An unwatched nightly is a log file, not a practice.

---

## 18. Release engineering — versioning, changelogs, crash reporting

Exporting produces builds; *releasing* produces trust. This section collects the process disciplines that separate "I uploaded a zip" from "version 1.4.2 shipped".

### Semantic versioning for games

SemVer (`MAJOR.MINOR.PATCH`) was designed for libraries with API consumers. Games have different consumers — players and their save files — so reinterpret the contract:

```
MAJOR  — the experience or its data contract changed incompatibly:
         save-format break requiring migration, redesigned core loop,
         "the 2.0 update" as a marketing beat.
MINOR  — new content or features, saves compatible:
         new rooms, new systems, new platform.
PATCH  — fixes only. A player should never fear a patch.

Pre-release: 1.5.0-beta.2, 1.5.0-rc.1  → opt-in channels only
Dev builds:  stamp as 0.0.0-dev or <lasttag>+<git-sha> so mislabeled
             builds identify themselves in bug reports
```

Rules that earn their keep:

- **The save-compatibility promise is the versioning promise.** Decide and document: which version-jumps guarantee automatic save migration? (Relax Room: any MINOR/PATCH; MAJOR ships a migration or a clearly-communicated reset. Migration chains live in `save_manager.gd` — see [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md).)
- **Android `version/code`** is a separate monotonic integer; derive it (e.g. `MAJOR*10000 + MINOR*100 + PATCH`) so it can never move backward.
- **Tag = version = truth** (§17). If it isn't tagged, it isn't a version; if a player has it, it had a tag.

### Changelogs players can read

Keep two audiences separate:

- `CHANGELOG.md` (repo, Keep-a-Changelog format): every change, grouped Added/Changed/Fixed, developer-precise.
- Release notes (store page, in-game "what's new"): the five things a player will feel, in player language, gratitude for reported bugs included by name/handle when permitted.

```markdown
## [1.4.2] — 2026-07-27
### Fixed
- Decorations no longer disappear when placed during an autosave (#142 — thanks @plantlover)
- Music panel: import button correctly disabled on web builds
### Changed
- Installer keeps saved rooms by default on uninstall; removal is now opt-in
```

Generate the *skeleton* from Conventional-Commit history if you like (`generate_release_notes: true` in §17 drafts it), but a human rewrites the player-facing version, always.

### Cadence: trains beat heroics

A small team's sustainable rhythm is a **release train**: a fixed cadence (Relax Room: minor release every 6-8 weeks, patches as needed) that departs on schedule with whatever features are *finished*. The alternative — releasing "when the big feature is done" — couples every fix to your riskiest work item and turns each release into an event. Trains also give the §18 checklist a natural home (run it per departure), keep the §17 pipeline warm (rehearsed at least every cycle), and make players' update expectations predictable. Features that miss the train catch the next one; nothing is rushed aboard. The single discipline that makes trains work: `main` is always releasable, enforced by the same CI gates that guard tags — which is why verification runs on every push, not just on release day.

### Crash reporting options for indie desktop apps

Godot has no built-in crash telemetry; your realistic ladder:

1. **File logging** (free, offline-friendly): enable `debug/file_logging/enable_file_logging`; logs land under `user://logs/`. Add an in-app "Report a problem" button that opens the log folder and your issue tracker. This is Relax Room's shipped solution — appropriate for a privacy-sensitive companion app.
2. **Structured self-reporting**: on clean-exit failure detection (a `crashed` flag file cleared on graceful shutdown), next launch offers to send the last log to your endpoint. Requires consent UI and a privacy-policy line (GDPR: logs are personal data if they can identify a user). The detection half is ten lines and worth having even without the reporting half — it powers a "recover from last session?" UX too:

```gdscript
# autoload/session_sentinel.gd — first autoload, so it runs before a crash can
const FLAG := "user://session.lock"

func _init() -> void:
    if FileAccess.file_exists(FLAG):
        # Previous session did not exit cleanly.
        GameState.last_session_crashed = true   # consumed by main menu
    FileAccess.open(FLAG, FileAccess.WRITE).store_string(
        Time.get_datetime_string_from_system())

func mark_clean_exit() -> void:                 # call from quit handlers
    DirAccess.remove_absolute(FLAG)
```
3. **Hosted services**: Sentry (official Godot SDK exists), BugSplat, Backtrace — engine-level native crash capture with symbolication. Costs money and a privacy review; worth it at real player volume. Symbolicating engine crashes requires the debug symbols of your exact templates — official builds publish them; custom templates: archive your own (§4).

Whatever the tier: **stamp every log/report with the version** (§17's stamped setting) and the platform feature tags — the two facts that turn "it crashed" into a searchable bucket.

### The hotfix protocol

Sooner or later a release ships a must-fix-today bug. Decide the protocol *before* you need it, because release-day judgment is the worst judgment:

1. **Branch from the tag, not from main.** `git checkout -b hotfix/1.4.3 v1.4.2` — main has three weeks of unreviewed features you must not ship under pressure.
2. **Fix, test the fix and the checklist's artifact-sanity block only** — a hotfix re-runs the short list, not the full campaign; that is what makes it fast *and* safe.
3. **Tag `v1.4.3`, let the standard pipeline build it.** No hand-built binaries, ever — the whole point of §16-17 is that the emergency path *is* the normal path.
4. **Cherry-pick the fix back to main** immediately (the forgotten back-port resurrects the bug in 1.5.0 — a genre classic).
5. **Post-mortem one paragraph** in the changelog dev section: what escaped, which checklist line or test would have caught it, and add that line/test.

### Legal readiness: licenses, credits, privacy, ratings

Release engineering has a paperwork lane that blocks shipping just as hard as a broken build. The four documents, and when they bite:

**Third-party licenses.** Every asset and library in the build carries one. The working table for typical indie inputs:

| License | Sell the game? | Credit required? | Copyleft obligations? |
|---|---|---|---|
| MIT / Apache-2.0 (Godot itself, most addons) | ✓ | ✓ include license text | None |
| CC0 (much of Kenney's work) | ✓ | Not required (still polite) | None |
| CC-BY | ✓ | ✓ attribution as specified | None |
| CC-BY-SA | ✓ | ✓ | Derivatives share-alike — dangerous for baked-in art |
| GPL (code) | ✓ | ✓ | **Your whole game's source** — avoid in assets/addons unless that is your model |
| "Free for non-commercial" | ✗ for a paid game | per terms | Read every word before the asset enters the repo |

Operationalize it: a `LICENSES/` folder in the repo with one file per dependency, a `THIRD_PARTY.txt` aggregated at build time and shipped by the installer (§11's `[Files]` already does), and an in-game credits screen — Godot gives you the engine's own license text via `Engine.get_license_text()` to display, which is part of Godot's MIT attribution expectation. Gate: **no asset enters `res://` without its license landing in `LICENSES/` in the same commit.** Retroactive license archaeology before a launch is misery.

**Credits screen.** Beyond obligation, it is culture: engine, addons (godot-sqlite by 2shady4u, MIT), asset authors (Kenney CC0, music sources), testers. Relax Room renders it from `data/credits.json` so the §18 checklist line "credits current?" is a data diff, not a scene edit.

**Privacy.** If any build transmits any user data (cloud sync, crash reports, analytics — §18's tier 2+), you owe: a privacy policy URL (required by Play Console regardless, §14), consent before first transmission, a deletion path, and data minimization. GDPR applies to EU users wherever you are based. The offline-only build of a companion app collects nothing and needs none of this — which is itself an architecture argument (see the local-first stance in [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md)).

**Age ratings.** Free self-assessment via IARC covers Play and most storefronts; Steam has its own questionnaire; PEGI/ESRB formal certification is paid and console-relevant only. A no-violence, no-chat, no-purchases companion app rates E/PEGI-3 in ten minutes — do it once per major content change, keep the certificate IDs in the release notes template.

### The pre-release checklist

The full Relax Room checklist, evolved across its releases — adapt, don't adopt blindly. Run it against the *draft release artifacts* (§17), not your dev machine.

```
VERSIONING
[ ] Git tag matches intended version; CHANGELOG entry exists
[ ] In-game About shows the version; Explorer Details shows it (Windows)
[ ] Android version/code incremented (if shipping Android)
[ ] Save migration from previous release verified with a REAL old save

ARTIFACT SANITY (per platform)
[ ] Fresh-machine install/unzip → launches to main menu
[ ] Sidecar files present (PCK, GDExtension dlls/sos)
[ ] Windows: signed? SmartScreen behavior checked on a clean VM
[ ] macOS: notarized + stapled; downloaded-copy opens (not USB-copied!)
[ ] Linux: executable bit survives the archive; runs on a non-dev distro
[ ] Web: loads in Chrome/Firefox/Safari; correct headers or threads-off

CONTENT & CONFIG
[ ] Export filters: data files (*.json) present — open one in the shipped build
[ ] No debug leftovers: dev_tools tag off, console wrapper excluded,
    verbose logging off, test scenes unreachable
[ ] Credits/licenses screen current (new assets since last release?)
[ ] Privacy policy current (any new data collection?)

INSTALLER (Windows)
[ ] Clean install → launch → uninstall leaves no orphan entries
[ ] Upgrade over previous version in place; saves intact after upgrade
[ ] Silent install works: /VERYSILENT /SUPPRESSMSGBOXES /NORESTART

PROCESS
[ ] All CI jobs green on the tag; artifacts downloaded from CI, not built locally
[ ] Release notes written for players; draft release reviewed
[ ] Rollback plan: previous installer/build still downloadable
[ ] Post-publish smoke test scheduled (download the PUBLIC link and run it)
```

> ✅ **Best practice** — Checklists shrink through automation, not through skipping. Every release, pick one manual line and turn it into a CI assertion (artifact-size floor, version-metadata check, a headless `--quit-after 2` boot test). The checklist that never shrinks is a checklist people will eventually skim.

---

## 19. File-size optimization

Size is a proxy for respect: download time, disk footprint, patch bandwidth, web startup. Budget it like performance — measure first, fix the biggest line items, re-measure.

### Know your build's anatomy

Before optimizing, attribute. Export a ZIP variant of the pack (or list the PCK with §6's script plus sizes) and sort:

```
Typical 2D desktop build anatomy (Relax Room v1.0, before optimization):
  Engine binary (template)        62 MB   ← fixed unless custom templates
  Textures (imported .ctex)       31 MB   ← biggest owned lever
  Audio                           38 MB   ← WAV music: the classic mistake
  Fonts                            9 MB   ← full CJK font shipped for 2 labels
  Scripts/scenes/data              3 MB   ← never worth optimizing
  GDExtension binaries             4 MB
                                 ─────
                                 147 MB  → after this section: 74 MB
```

### Audio: the cheapest 50 MB you'll ever save

| Format | 1 min stereo | Decode cost | Use for |
|---|---|---|---|
| WAV (PCM) | ~10 MB | none | Short SFX (<5 s), UI ticks |
| Ogg Vorbis q5-6 | ~1.2 MB | low | Music, ambience, anything long |
| MP3 | ~1 MB | low | Supported, but prefer Ogg in Godot |

```bash
# Batch-convert music WAV → OGG q6, keeping originals out of the project
for f in raw_audio/music/*.wav; do
  ffmpeg -i "$f" -c:a libvorbis -q:a 6 "v1/assets/audio/music/$(basename "${f%.wav}").ogg"
done
```

Keep WAV *sources* outside `res://` (or excluded); import the OGGs. Loop points survive via the import panel's loop settings.

### Textures: compression is an import decision

Texture memory/disk format is set per-file in the **Import** dock (defaults per-project), and the right answer is content-dependent:

| Content | Compress mode | Why |
|---|---|---|
| Pixel art, UI, crisp 2D | **Lossless** | VRAM compression (S3TC/ETC2) smears exactly the pixels you drew |
| Large painterly 2D, 3D textures | **VRAM Compressed** | 4-6× smaller on disk and in VRAM |
| Photos/screenshots in-app | Lossy (WebP quality slider) | Big wins, invisible at reasonable quality |

Supporting habits: author at the resolution you display (a 4096² source for a 256² prop ships 256² only if you set the import `size limit` — set it); mipmaps off for pure 2D (they cost ~33% extra); trim transparent borders and atlas small sprites ([SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md)). For exports serving both desktop and mobile, the preset's texture-format toggles (`s3tc_bptc` vs `etc2_astc`) decide which compressed variants ship — shipping both doubles compressed-texture payload; per-platform presets ship one each.

Import settings are versioned per-file in the committed `.import` sidecars, which makes them reviewable — a pixel-art project's typical entry, so you recognize a wrong one in a diff:

```ini
# couch.png.import (excerpt) — the settings that matter for size/quality
[params]
compress/mode=0                 ; 0 = Lossless (pixel art), 2 = VRAM Compressed
compress/high_quality=false
mipmaps/generate=false          ; 2D: off
process/size_limit=0            ; cap oversized sources (0 = none)
detect_3d/compress_to=0         ; NEVER auto-flip 2D art to VRAM compression
```

`detect_3d` deserves the callout: by default, using a texture in a 3D context silently re-imports it VRAM-compressed — correct for 3D, ruinous for UI art that brushed against a 3D preview once. Pin it to disabled for 2D projects via the project-wide import defaults (Project Settings → Import Defaults).

### Fonts, features, and the engine itself

- **Fonts**: a full Noto CJK weighs more than your codebase. Subset fonts to the glyph ranges you render (the Import dock supports preloading/subsetting configuration), or ship system-font fallback for user-generated text.
- **Unused engine features**: the honest big lever is custom templates (§4) — `disable_3d`, dropped modules — worth 10-30 MB on desktop and transformative on web. The export dialog alone does not strip engine code.
- **PCK-side trimming**: exclude filters for docs/tests (§6); delete orphan assets — find them with the editor's *Orphan Resource Explorer* (Project → Tools) before every major release.
- **Compression at the edges**: installer LZMA2 (§11) roughly halves the download regardless of the above; web hosts should serve wasm/pck with gzip or Brotli precompression (§15).

> ⚠️ **Pitfall** — Optimizing by *deleting from the filesystem* while scenes still reference the paths: exports then fail at runtime with load errors the editor never showed (its cache still had them). After any asset purge: close editor, delete `.godot/`, reopen, fix every red error in the Output panel, *then* export. The [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) module's fail-fast loading patterns pay off exactly here.

### Per-platform size budgets

Set budgets per artifact and let CI enforce the ceiling (a one-line size assertion per §16). Relax Room's current budgets, with the reasoning that produced them:

| Artifact | Budget | Why this number |
|---|---|---|
| Windows installer | ≤ 55 MB | Impulse-download threshold on typical connections; LZMA2 gets ~45% off the raw payload |
| Windows portable zip | ≤ 90 MB | Uncompressed-ish; competes only with itself |
| Linux AppImage | ≤ 95 MB | AppImage's internal squashfs compresses; parity with Windows payload |
| Web demo (transfer size) | ≤ 30 MB | ~10 s on a mediocre connection before first frame; every MB is measurable funnel loss |
| Android APK | ≤ 60 MB | Play's over-the-air comfort zone; AAB splits reduce delivered size further |

Two habits keep budgets honest: measure *transfer* size for web (post-compression, from the browser's network tab, not `ls`), and re-baseline budgets deliberately in a PR when content genuinely grows — a budget silently raised to make CI green is a budget deleted.

---

## 20. Distribution platforms

The build is done; someone has to host, deliver, and update it. Comparison of the venues that matter to an indie desktop project:

| | itch.io | Steam | GOG | Direct (your site) |
|---|---|---|---|---|
| Cost of entry | Free | $100/app (recoupable) | Free (curated — must be accepted) | Hosting only |
| Revenue share | You choose (default 10%) | 30/70 | 30/70 | 0 |
| Updates | Butler delta patches | Depot diffing, branches | Galaxy pipeline | You build it (§11) |
| Trust/warnings | itch app smooths it | Steam client = trusted | Galaxy = trusted | SmartScreen/Gatekeeper yours to solve |
| Best for | Jams, demos, early releases | Scale, wishlists, reviews | DRM-free audience | Full control, B2B, patrons |

### itch.io + butler: the reference indie loop

Butler is itch's CLI uploader — delta uploads, channels, versioning — and slots directly into §17's release job:

```bash
# Channels map to platform tags on the itch page
butler push build/windows  ifts-team/relax-room:windows --userversion "$VERSION"
butler push build/linux    ifts-team/relax-room:linux   --userversion "$VERSION"
butler push build/web      ifts-team/relax-room:web-demo --userversion "$VERSION"
butler status ifts-team/relax-room
```

Authentication in CI via the `BUTLER_API_KEY` secret. The web channel, marked "playable in browser", gives you hosted web builds with the SharedArrayBuffer toggle available in the page settings (§15).

Page-setup details that repeatedly trip Godot uploads: the browser-play channel wants a **zip whose root contains `index.html`** (name your exported HTML file `index.html` in the preset's export path, as §17's matrix does); set the embed viewport to your project's design resolution rather than the default; and for downloadable channels, mark platform tags on each channel so the itch app offers the right build per OS. Butler's `--userversion` string is what players see in the itch app's version history — pass the same tag-derived version as everywhere else (§18's single-source rule reaching one more surface).

### Steam in one paragraph

Register on Steamworks, pay the app fee, and your build pipeline gains one step: `steamcmd +login <builder account> +run_app_build app_build.vdf` uploading a content depot per platform. Real Steam work is *not* the upload — it's store assets, wishlists-before-launch marketing, achievements/cloud-save integration (a GDExtension such as GodotSteam), Deck verification, and review-velocity planning. Treat "we should be on Steam" as a product decision with a months-long runway, not an export preset.

The build-config VDF, for pipeline completeness — it is the Steam analogue of §17's matrix entry, and slots into the same post-release job as butler:

```
"AppBuild"
{
    "AppID"       "123456"
    "Desc"        "v1.4.2 — automated build"
    "ContentRoot" "..\build\"
    "BuildOutput" "..\steam_output\"
    "Depots"
    {
        "123457"    // Windows depot
        {
            "FileMapping" { "LocalPath" "windows\*"  "DepotPath" "." "recursive" "1" }
        }
        "123458"    // Linux depot
        {
            "FileMapping" { "LocalPath" "linux\*"    "DepotPath" "." "recursive" "1" }
        }
    }
    "SetLive" "beta"    // never straight to default: promote after smoke test
}
```

`"SetLive" "beta"` encodes the staged-rollout discipline: builds land on a beta branch, someone smoke-tests through the actual Steam client, then the branch is promoted in the Steamworks dashboard. Depot diffing means players download only changed files — the platform equivalent of butler's deltas and §8's patch packs.

### GOG and direct sales, one honest paragraph each

**GOG** is curated (pitch first, acceptance not guaranteed), strictly DRM-free, standard revenue split, optional Galaxy SDK for achievements/cloud saves. Its audience is smaller but loyal and offline-friendly — a natural fit for a local-first companion app *if* accepted; the build requirement is simply your §10/§12 artifacts with an installer, which you already have.

**Direct sales** (your site + a payment/key provider) maximize margin and ownership and transfer every remaining responsibility to you: hosting bandwidth, §11's auto-update problem in full, tax/VAT handling via the merchant-of-record, refunds, and the complete trust burden of §10's SmartScreen reality — unsigned direct downloads convert measurably worse. The usual indie sequencing: itch first (zero friction), Steam when marketing runway exists, direct/GOG as additive channels once the pipeline makes multi-channel publishing a YAML stanza rather than a weekend.

### Delta updates across channels, unified

A closing synthesis, because the same idea has now appeared five times wearing different costumes:

| Channel | Delta mechanism | Your work |
|---|---|---|
| itch.io | butler's binary diffing | `butler push` (§17) |
| Steam | depot content diffing | `steamcmd` upload |
| Self-hosted installer | Inno re-copies changed files; download is full-size | §11's notify-only updater; optional §8 patch PCKs to shrink downloads |
| Patch PCKs | you ship only changed resources | Patches tab export + mount-at-boot loader (§8) |
| Android | Play serves per-device splits from the AAB | Upload AAB, bump `version/code` |

The strategic takeaway: platform stores have already built excellent delta pipelines — use theirs. Build your own (patch PCKs + updater) only for the direct-distribution slice of your audience, and only when its size justifies the moving parts.

### Choosing the first channel: a decision tree

```
Is the project a jam entry / prototype / free demo?
 ├─ yes → itch.io (browser channel if web-viable, §15) — done today
 └─ no  → Is it a commercial game with marketing runway (6+ months)?
      ├─ yes → Steam page NOW for wishlists; itch for demo builds;
      │        release on both; GOG pitch after traction
      └─ no  → Is it a tool/companion app for a specific community?
           ├─ yes → Direct download (installer + portable, §10-11)
           │        + itch as the low-friction mirror; Flathub for
           │        the Linux audience once stable (§12)
           └─ no  → Ship on itch first anyway. A channel you can
                    fully operate this week beats the ideal channel
                    you'll configure someday. Migrating later is a
                    YAML stanza (§17), not a rewrite.
```

Relax Room followed the tool branch: direct installer as the flagship artifact, itch as mirror and web-demo host, Flathub on the roadmap. The branch you take changes which sections of this module are on your critical path — which is exactly why §1's reading guide exists.

> ✅ **Best practice** — Whatever the platform, keep the *canonical* artifact in your own storage (the GitHub Release from §17). Store pipelines transform and re-host; when a player bug arrives "from Steam", you must be able to fetch the exact bytes they ran.

---

## 21. Case study — Relax Room release pipeline

Everything above, assembled into one project's real decisions. Relax Room is the course's desktop companion app: 2D, Compatibility renderer, GDScript-only game code, one GDExtension (godot-sqlite), JSON-primary persistence with SQLite underneath, developed on Windows in Godot 4.5. Executable name `MiniCozyRoom` — see "release history" for why.

### Platform strategy

| Channel | Artifact | Status | Rationale |
|---|---|---|---|
| Windows (primary) | Inno Setup installer + portable zip | Shipping | The desktop-companion audience lives here |
| Linux | AppImage | Shipping | CI already exports Linux for tests; AppImage cost one script (§12) |
| Web | Feature-limited browser demo on itch.io | Shipping | Marketing funnel: "try in browser → download full" |
| Android | Internal testing track | Experimental | Companion-on-phone appeal; SQLite + touch UI already work |
| macOS | On hold | — | No team Mac + $99/yr + notarization: parked until demand is measured |
| iOS | Not planned | — | — |

The parked-macOS row is a deliberate lesson: a platform is a *recurring* cost (certs, QA per release, platform-specific bugs), and "the exporter supports it" is not a reason to ship it.

### GDExtension discipline (godot-sqlite)

The single most export-sensitive dependency. Working rules:

- `addons/godot-sqlite/` binaries for every shipped platform are checked into the repo at the version pinned in `addons/README`; a CI step asserts the `.gdextension` file lists a library for every export preset's platform before any export runs.
- Web has no wasm SQLite binary → the web preset relies on the runtime fallback (`OS.has_feature("web")` → JSON persistence only) which was designed in [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md) — the export constraint shaped the architecture, not vice versa.
- Every platform's release-candidate build runs the same 20-second smoke script: boot → create room → place decoration → quit → relaunch → assert persistence. Catches missing native binaries instantly, because SQLite init fails loudly at boot.

### The pipeline as shipped

```
push/PR:            gdlint + gdformat + GdUnit4 suite (ubuntu container)
tag v*:             stamp version → import → export matrix
                    (Windows exe+pck, Linux x86_64, Web) → artifacts
                    windows-latest: ISCC → Setup_RelaxRoom_<ver>.exe
                    make_appimage.sh → RelaxRoom-<ver>-x86_64.AppImage
                    draft GitHub Release with all artifacts
human:              checklist (§18) against downloaded artifacts →
                    publish release → butler push to itch channels
```

Total wall time tag→draft: ~11 minutes, of which template download is zero (cached) and the Windows runner spin-up is the longest single wait.

### The pipeline as files

Because "the pipeline" is easy to imagine as CI magic, the inventory of what it actually is — thirteen version-controlled files, each owned like code:

```
.github/workflows/release.yml     the §17 workflow (verify + deliver lanes)
v1/export_presets.cfg             five presets — the build recipe (§5)
v1/tools/stamp_version.gd         tag → ProjectSettings (§17)
v1/tools/check_presets.py         preset invariants gate (§5)
v1/tools/manifest_pck.gd          pack manifest for release archaeology (§7)
v1/tools/smoke_test.sh            xvfb boot test (§16)
tools/build_all.ps1               local mirror of the CI export lane (§16)
tools/package_windows.ps1         installer + portable zip (§11)
tools/make_appimage.sh            Linux packaging (§12)
tools/make_tarball.sh             Linux alt packaging (§12)
installer/RelaxRoom.iss           Inno Setup script (§11)
docs/android_setup.md             toolchain pinning (§14)
docs/RELEASE_CHECKLIST.md         the §18 checklist, versioned like everything
```

Everything a new maintainer needs to ship a release is in that list plus the secrets store — which is the actual definition of a pipeline being "owned by the repo, not by a person". The capstone requires you to produce the equivalent inventory for your own project; most students discover two or three steps living only in their shell history, which is precisely the exercise's point.

### Release history — the lessons ledger

| Version | What happened | What it taught (and where it lives now) |
|---|---|---|
| v0.1.0 | First manual export ever, week 6. Boot to empty room: `rooms.json` missing | Non-resource files need include filters (§6); "export early" (§1) |
| v0.2.0 | Linux zip: "Permission denied" reports | Executable bit / archive formats (§12); CI packages Linux, never Windows |
| v0.3.0 | Windows build 147 MB; itch upload cap pain | Size audit ritual (§19): WAV→OGG −34 MB, font subset −8 MB |
| v0.3.1 | First Inno installer; upgrade created second install | AppId had been regenerated; frozen forever since (§11) |
| v0.4.0 | **Rename**: "Mini Cozy Room" → "Relax Room" for the store page. Exe/PCK names kept as `MiniCozyRoom` | Renaming display names is cheap; renaming artifact names breaks upgrade-in-place, shortcuts and the user-dir path — display name and artifact identity are separate decisions (§7, §11) |
| v0.5.0 | First tag-triggered CI release; workflow failed on the tag (never tested) | Rehearsal tags + `workflow_dispatch` (§17) |
| v1.0.0 | Public launch on itch: installer, portable, AppImage, web demo | The checklist was born the night before; it has 9 items then, 24 now (§18) |
| v1.1.0 | Save-migration bug for v0.5 saves found by a player, not QA | "Migrate a REAL old save" checklist line; old-save corpus kept in repo test fixtures |
| v1.4.2 | Current. Boring release. | Boring is the goal. |

### What would change at 10× scale

Honest limits of the current setup, recorded for the capstone discussion: no code signing yet (SmartScreen warnings are eaten as a cost — first revenue pays for an OV cert); no crash telemetry (file logs + a report button); macOS unshipped; and the human-gated release step would need a staged-rollout mechanism (itch channels or Steam betas) before the player count makes a bad release expensive. None of these are architecture changes — the §17 pipeline grows steps, it doesn't get replaced. That is what "production-ready" means in practice: the next requirement is an addition, not a rewrite.

---

## Best practices

The module's judgment calls, condensed:

1. **Export in week one, then continuously.** Every platform you claim to support gets exported and booted at least weekly (CI makes this free). Export-only bugs age terribly.
2. **Match versions ruthlessly.** Editor version = template version = version pinned in CI = version in the README. Upgrade all four in one commit.
3. **Commit the recipe, never the secrets.** `export_presets.cfg`, `*.import`, installer scripts, build scripts in Git; credentials file, keystores, certificates, encryption keys in secret stores. Grep history once for past leaks.
4. **Two-step headless builds**: `--import` then `--export-release`, output dir pre-created, artifact existence + size asserted after. Never trust exit codes alone.
5. **One version source**: the Git tag drives project settings, exe metadata, installer version, artifact names and the About screen. Hand-edited version numbers are always eventually wrong.
6. **Feature-tag your channels** (`dev_tools`, `staging`, `demo`) instead of forking code or presets-with-divergent-logic; platform truth from platform tags only.
7. **Respect the trust systems** — sign what you can afford, notarize for macOS public releases, keep Android keystores backed up like the company asset they are, and when unsigned, *document* the warnings players will see instead of pretending they don't exist.
8. **User data outlives the app**: writes only to `user://`, uninstallers keep saves by default, upgrades never touch them, save migration tested with real old saves each release.
9. **Optimize size with a ledger, not vibes**: attribute bytes (engine / textures / audio / fonts), fix the top line item, re-measure. Audio format and font subsetting are the usual jackpots.
10. **Keep a human at the very end.** CI builds, packages and drafts; a person runs the checklist and presses publish. Automate everything except accountability.

### One-page quick reference

The commands and paths this module keeps reaching for — bookmark-grade:

```bash
# ── Engine & templates ─────────────────────────────────────────
godot --version                                   # assert before building
# Templates live in:
#   Win:   %APPDATA%\Godot\export_templates\<version>\
#   Linux: ~/.local/share/godot/export_templates/<version>/
#   macOS: ~/Library/Application Support/Godot/export_templates/<version>/

# ── Headless build (the two-step, always) ──────────────────────
godot --headless --path . --import
godot --headless --path . --export-release "Windows Release" build/win/Game.exe
godot --headless --path . --export-debug   "Windows Dev"     build/dev/Game.exe
godot --headless --path . --export-pack    "Windows Release" build/patch.pck

# ── Run tools & tests ──────────────────────────────────────────
godot --headless --path . -s tools/stamp_version.gd -- 1.4.2
godot --headless --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd --add "res://tests/" -c

# ── Packs at runtime ───────────────────────────────────────────
# ProjectSettings.load_resource_pack(path, replace_files := true) -> bool
# Test any pack against a bare template:
./windows_release_x86_64.exe --main-pack Game.pck

# ── Windows packaging ──────────────────────────────────────────
ISCC.exe installer/App.iss /DAppVersion=1.4.2
Setup_App_1.4.2.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
signtool sign /f cert.pfx /p *** /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 App.exe

# ── Linux packaging ────────────────────────────────────────────
chmod +x Game.x86_64
appimagetool App.AppDir App-1.4.2-x86_64.AppImage

# ── macOS trust chain ──────────────────────────────────────────
codesign --force --deep --options runtime --timestamp --sign "Developer ID Application: …" App.app
xcrun notarytool submit App.zip --keychain-profile prof --wait
xcrun stapler staple App.app && spctl --assess --type execute --verbose App.app

# ── Android ────────────────────────────────────────────────────
keytool -v -genkey -keystore release.keystore -alias app -keyalg RSA -validity 10000
adb install -r App.apk && adb logcat -s godot

# ── Delivery ───────────────────────────────────────────────────
butler push build/windows user/game:windows --userversion 1.4.2
steamcmd +login builder +run_app_build app_build.vdf +quit
```

Secrets map (what lives where — never in Git): PCK key → password manager + CI secret · Android keystore + passwords → password manager + base64 CI secret · Windows PFX/token → CI signing step only · Apple notary credentials → keychain profile / CI secret · `BUTLER_API_KEY` → CI secret · everything else → `export_presets.cfg`, committed.

---

## Common errors & troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "No export template found" in export dialog | Templates missing or version-mismatched with the editor (incl. patch releases) | `Editor → Manage Export Templates → Download and Install`; verify folder name matches `godot --version` string exactly (§3) |
| Export button greyed / preset shows error icon | Missing platform prerequisite (rcedit path, Android SDK/JDK path, templates) | Open the preset — the dialog names the missing piece; set paths in Editor Settings → Export (§10, §14) |
| Exported game opens to blank/empty content that worked in editor | Non-resource data files (`.json`, `.csv`) not in include filters; or dynamic `load()` paths pruned by "selected scenes" mode | Add include filters; prefer "Export all resources"; verify with a PCK listing (§6) |
| Build crashes at boot only when exported | Stale/absent import cache (CI skipped `--import`); or GDExtension binary missing for the platform | Run `--headless --import` before export on a clean clone; check `.gdextension` platform entries and shipped dlls/sos (§2, §16, §21) |
| `Error: Couldn't load project data at path '.'` when launching the exe | Template binary can't find a PCK: sidecar renamed/missing, or embed off when you assumed on | Keep `game.exe` + `game.pck` names matched and together, or re-export with `embed_pck=true`; `--main-pack` to test (§7) |
| Works on Windows, "file not found" on Linux only | Path case mismatch (`Assets/` vs `assets/`) — Linux is case-sensitive | Fix path literals; add a Linux CI job that boots the build; lint data-file paths for exact case (§12) |
| Linux/macOS binary won't start: "Permission denied" | Executable bit stripped by zip created on Windows | Package on Linux/macOS CI; use tar.gz; document `chmod +x`; AppImage sidesteps it (§12, §13) |
| macOS: "app is damaged and can't be opened" | Unsigned/un-notarized quarantined download, or exec bit lost in transit | For testers: right-click → Open or `xattr -cr App.app`. For releases: Developer ID + notarytool + staple (§13) |
| Windows SmartScreen blocks every release anew | Unsigned exe/installer — hash reputation resets each build | Sign exe *and* installer with timestamp; consider EV for instant reputation; or distribute via store/launcher (§10) |
| `Can't open dynamic library` / missing DLL on players' machines | GDExtension DLL excluded by filters or not shipped next to exe; or addon's extra runtime DLLs absent | Ship all addon binaries; assert their presence post-export in CI; check the addon's dependency list (§10) |
| Android: export fails with SDK/JDK errors | Wrong JDK (not 17), SDK paths unset, missing build-tools/platform | Install OpenJDK 17 + SDK components; set both paths in Editor Settings → Export → Android (§14) |
| Android: "App not installed" / `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | Installed copy signed with a different key (debug vs release) | `adb uninstall <package>` then reinstall; keep one debug keystore across the team (§14) |
| Play Console rejects upload | APK instead of AAB; or `version/code` not incremented | Enable gradle build, export AAB; bump version code every upload (§14) |
| Can't update published app ever again | Release keystore lost and Play App Signing not enrolled | Prevention only: enroll App Signing, triple-backup keystore + passwords (§14) |
| Web: blank page, console mentions SharedArrayBuffer/cross-origin | Threads-ON build on a host without COOP/COEP headers | Re-export threads OFF; or enable host isolation headers / itch toggle; or PWA workaround (§15) |
| Web: old version keeps loading after update | Service worker cache serving stale build | Bump/clear SW cache; hard-refresh + unregister worker in DevTools; version your deploy paths (§15) |
| Web: no sound until user clicks | Browser autoplay policy | Gate audio start behind a "click to begin" interaction — by design, not a bug (§15) |
| CI: export job fails `Invalid export preset name` | Preset name typo/case drift between YAML and `export_presets.cfg` | Copy the exact string; treat preset names as API — rename via PR only (§16) |
| CI: succeeded but artifact is broken/tiny | Soft failures behind exit 0; wrong-version Godot on PATH | Assert `godot --version`, artifact existence + minimum size, add a headless boot smoke test (§16, §17) |
| Installer upgrade creates a second copy | Inno `AppId` changed between releases | Freeze `AppId` forever; ship a migration installer that detects both if already shipped wrong (§11) |
| Uninstall deleted a player's saves | Uninstaller deleting `user://` unconditionally | Never touch user data by default; opt-in removal dialog only (§11, §18) |
| Exported exe has the Godot icon / empty version info | rcedit unset (or Wine missing when exporting for Windows from Linux/macOS) — export continues without metadata | Configure rcedit in Editor Settings; add a CI assertion on the version resource (§10) |
| Windows Defender/AV quarantines your fresh build | Unsigned, low-reputation, brand-new hash — heuristic false positive | Sign with timestamp; distribute via store; submit false-positive reports; never ask users to disable AV (§10) |
| Patch PCK mounts but old content still shows | Resources already loaded/preloaded before the mount | Mount in first autoload `_init()`; audit preload chains (§8) |
| Encrypted export runs on your machine, fails elsewhere | Exported with official templates while encryption enabled, or key mismatch between template and preset | Custom templates compiled with the same key are mandatory; verify with a clean-machine boot (§9) |
| Emoji/CJK text renders as boxes in export only | ICU data or font subsetting stripped what the editor had | Keep ICU data in templates; check font subset ranges against real content (§3, §19) |
| Text looks wrong only in release template | A `debug`-gated code path (or `editor` tag assumption) altered layout/logging | Diff behavior debug vs release export; audit `OS.is_debug_build()` branches (§2, §6) |
| `--export-release` writes nothing, exit 0, empty folder | Output directory didn't exist, or preset `export_path` empty and no path argument | Pre-create directories; always pass the explicit output path; assert artifact after (§16) |
| AppImage won't run on older distro: `GLIBC_x.yz not found` | Custom template built on a new-glibc machine | Build templates in an old-baseline container; or use official templates (§12) |

---

## Exercises

Each lab states acceptance criteria — the lab is done when every box ticks, not when it "basically works". Stretch goals are optional extensions in the same direction. Use any small Godot 4.5 project (or your Relax Room coursework build) as the subject.

### Lab 1 — First export, dissected

Export your project for Windows twice: once with embedded PCK, once sidecar. Then export a ZIP pack of the same preset and open it in an archiver.

**Acceptance criteria**
- [ ] Both Windows variants launch on your machine from a folder outside the project.
- [ ] You can name three files inside the pack that you did *not* author directly (e.g. a `.ctex`, a `.remap`, `project.binary`) and explain each in one sentence.
- [ ] A `.json` data file of your project is confirmed present in the pack (add the include filter if it wasn't — and note that it wasn't).

**Stretch** — Launch the raw export template binary from your templates folder with `--main-pack your_game.pck` and explain what this proves about the engine/content split.

### Lab 2 — Preset hygiene and channels

Create `Dev`, `Staging` and `Release` presets for one platform, differentiated only by custom feature tags and template flavor. Add a visible in-game marker (corner label) that reports the channel and `OS.is_debug_build()`.

**Acceptance criteria**
- [ ] `export_presets.cfg` diff shows the three presets; no credentials appear anywhere in the diff.
- [ ] The channel label is correct in all three exports and shows nothing in the Release build.
- [ ] A teammate (or a fresh clone) can export all three with zero manual dialog edits.

**Stretch** — Wire one project-setting override keyed on a custom feature tag (e.g. a different window title in Staging) and verify it in the export.

### Lab 3 — Patch and DLC packs

Ship v1 of a tiny game (base PCK). Change one texture and one script, then produce a patch PCK using the preset's Patches tab; separately produce a namespaced DLC pack that adds new content under `res://dlc/`.

**Acceptance criteria**
- [ ] Base build without patch shows old content; with patch file present in `user://patches/`, the same binary shows new content.
- [ ] Patch pack is at least 10× smaller than the base pack.
- [ ] DLC loads with `replace_files = false` and cannot override a base-game file (prove it by trying).
- [ ] Packs mounted in an autoload `_init()`; you can explain in two sentences why `_ready()` was too late.

**Stretch** — Write a mod manifest validator that rejects a pack containing files outside its namespace.

### Lab 4 — Inno Setup installer (from the original module, expanded)

Build a Windows installer for your export: custom icon, license page, per-user install, optional desktop shortcut, changelog shipped, uninstaller that preserves save data by default.

**Acceptance criteria**
- [ ] In a clean Windows VM/Sandbox: install → launch from Start Menu shortcut → play → uninstall; *Apps & features* shows correct name, version, publisher, icon throughout.
- [ ] Upgrade test: install v1.0.0, then run a v1.0.1 installer built with the same AppId — one entry remains, files updated in place, saves intact.
- [ ] `Setup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART` completes with no visible UI and a working install.
- [ ] Version passed via `/DAppVersion=` — no version string hand-written in the `.iss`.

**Stretch** — Add the opt-in "remove my save data" uninstall dialog from §11 and prove both paths in the VM.

### Lab 5 — Headless build script

Write `build_all` (PowerShell or bash) that: asserts the Godot version, imports, exports Windows + Linux + Web from a *fresh clone*, and fails loudly on any missing/undersized artifact.

**Acceptance criteria**
- [ ] Running on a clone with no `.godot/` directory succeeds end-to-end.
- [ ] Sabotage test A: rename a preset — script fails with a readable error, non-zero exit.
- [ ] Sabotage test B: point `GODOT_BIN` at a 4.4 binary — script refuses before exporting anything.
- [ ] Total script runtime and artifact sizes are printed as a summary table.

**Stretch** — Add a smoke test: launch the Linux export headless with `--quit-after 2` and treat non-zero exit as build failure.

### Lab 6 — GitHub Actions delivery pipeline (from the original module, expanded)

Implement §17 for your project: quality + test on push; on `v*` tags an export matrix, artifact upload, and a draft GitHub Release with generated notes.

**Acceptance criteria**
- [ ] A pushed rehearsal tag (e.g. `v0.0.1-rc1`) produces a draft release with Windows, Linux and Web zips attached.
- [ ] Template/engine cache hit confirmed on the second run (compare job durations in the Actions log).
- [ ] The in-game About screen of a downloaded artifact shows the tag's version — stamped by CI, not committed.
- [ ] No secret value appears in any log line (check the raw logs deliberately).

**Stretch** — Add the `windows-latest` Inno job from §17 so the draft release includes `Setup_<App>_<ver>.exe`.

### Lab 7 — Size audit

Produce a before/after size ledger for your project: attribute the build's bytes to engine / textures / audio / fonts / other, then apply at least two optimizations from §19.

**Acceptance criteria**
- [ ] A table in your lab notes shows per-category bytes before and after, with method of measurement stated.
- [ ] Total shipped size reduced by ≥25% *or* a written argument why your project is already near its floor.
- [ ] Visual/audio spot-check confirms no perceptible quality regression (pixel-art crispness, music artifacts).

**Stretch** — Build a size-optimized custom web template (`optimize=size`, `disable_3d` if applicable) and measure wasm download delta.

### Lab 8 — macOS notarization (stretch lab, from the original module)

Requires Mac access + Apple Developer membership (or do the rcodesign variant with a borrowed certificate in a dry-run). Sign, notarize, staple and verify a macOS export.

**Acceptance criteria**
- [ ] `spctl --assess --type execute` reports the app accepted, source Notarized Developer ID.
- [ ] The artifact downloaded through a browser on a second Mac/account opens with no warning dialog.
- [ ] A written run-book (10 lines max) your future self can follow, including where credentials live.

**Stretch** — Script the whole rung-2 flow into the CI pipeline on a `macos-latest` runner, gated to tags.

### Lab 9 — Legal and licensing audit

Run a full third-party audit of your project as if release were Friday: inventory every asset and addon, resolve every license, produce the shippable artifacts.

**Acceptance criteria**
- [ ] A `LICENSES/` folder exists with one entry per dependency (engine included), and a generated `THIRD_PARTY.txt` aggregate.
- [ ] An in-game credits screen lists engine (via `Engine.get_license_text()` or equivalent attribution), addons and asset authors, driven by a data file.
- [ ] At least one asset's license was actually *checked against its source page* (not folklore) and the finding recorded — most audits discover one surprise.
- [ ] A one-line repo policy exists (README or CONTRIBUTING): no asset without a license entry in the same commit.

**Stretch** — Write the privacy-policy paragraph your project would need if crash reporting (§18 tier 2) shipped, and identify exactly which data fields it would transmit.

### Self-assessment

Answer without looking, then verify against the sections in parentheses:

1. Why must export template versions match the editor exactly, and what error do you get when they don't? (§2-3)
2. Which file holds keystore passwords, and why is it safe that `export_presets.cfg` is committed? (§5)
3. A texture's PNG is excluded by filter yet still renders in the export — explain. (§6-7)
4. Why must patch PCKs be mounted in an autoload's `_init()`? (§8)
5. What does PCK encryption require that official templates cannot provide, and what attack does it *not* stop? (§9)
6. Inno Setup: which single constant must never change between releases, and what breaks if it does? (§11)
7. AAB vs APK: which requires gradle builds, and which channels take which? (§14)
8. Your web build is blank and the console mentions SharedArrayBuffer — list the three fixes in order of preference. (§15)
9. Give the two-command headless build sequence and why one command is not enough. (§16)
10. Where does the version number originate in a disciplined pipeline, and name four surfaces it must reach. (§17-18)

---

## Further reading

Official documentation first — these are the pages this module was verified against (Godot 4.x / stable channel):

- **[Exporting projects — Godot Docs](https://docs.godotengine.org/en/stable/tutorials/export/exporting_projects.html)** — The canonical overview: templates, presets, resource options, `export_presets.cfg` vs the credentials file, PCK vs ZIP, command-line exporting. Read it once fully; it resolves most forum questions pre-emptively.
- **[Exporting for Windows](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_windows.html)** / **[Linux](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_linux.html)** / **[macOS](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_macos.html)** / **[Android](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_android.html)** / **[Web](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html)** — The per-platform truth for tool versions, signing options and environment-variable overrides. Versions drift; these pages are the tie-breaker over any tutorial (including this one).
- **[Exporting packs, patches, and mods](https://docs.godotengine.org/en/stable/tutorials/export/exporting_pcks.html)** — `load_resource_pack`, override semantics, the patch-export workflow. Short and load-bearing for §8.
- **[Command line tutorial](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html)** — Every flag used in §16 (`--headless`, `--import`, `--export-*`, `-s`), plus path-resolution rules.
- **[Feature tags](https://docs.godotengine.org/en/stable/tutorials/export/feature_tags.html)** — The complete built-in tag list and project-setting override mechanics for §6.
- **[Compiling with PCK encryption key](https://docs.godotengine.org/en/stable/engine_details/development/compiling/compiling_with_script_encryption_key.html)** + **[Introduction to the buildsystem](https://docs.godotengine.org/en/stable/engine_details/development/compiling/introduction_to_the_buildsystem.html)** — Custom templates and the encryption recipe behind §4/§9, including `SCRIPT_AES256_ENCRYPTION_KEY`.
- **[Inno Setup documentation](https://jrsoftware.org/ishelp/)** — Terse but complete; the *Setup Command Line Parameters* page documents every silent-install flag in §11, and the `[Setup]` directive reference explains each line of the case-study script.
- **[godot-ci (abarichello/godot-ci)](https://github.com/abarichello/godot-ci)** — Maintained Docker images + reference GitHub Actions/GitLab CI workflows for Godot exports, including itch.io butler deployment and base64 keystore handling. Read its workflow file next to §17's and note the deltas.
- **[itch.io butler documentation](https://itch.io/docs/butler/)** — Channels, delta pushes, `--userversion`, CI authentication; the reference indie delivery loop of §20.
- **[Google Play: Play App Signing help](https://support.google.com/googleplay/android-developer/answer/9842756)** — Why enrolling converts keystore loss from fatal to recoverable; pair with §14's backup doctrine.
- **[Apple: Notarizing macOS software before distribution](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)** — First-party notarytool workflow and hardened-runtime requirements backing §13.

Sibling modules: process and testing in [GAME_DEV_PLANNING.md](GAME_DEV_PLANNING.md) · persistence/GDExtension architecture in [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md) · renderer choice consequences in [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) · asset/import pipeline in [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) · startup robustness in [AUTOLOAD_SAFETY.md](AUTOLOAD_SAFETY.md) · runtime performance budgets in [DESKTOP_COMPANION_PERFORMANCE.md](DESKTOP_COMPANION_PERFORMANCE.md) · the shippable-build requirement in [00-CAPSTONE.md](00-CAPSTONE.md).

---

## Glossary

| Term | Definition |
|---|---|
| **Export template** | Pre-compiled Godot engine runtime (no editor) for one platform/flavor; combined with your PCK it becomes the shipped game. Version must match the editor exactly. |
| **Export preset** | Named per-platform export configuration (filters, tags, metadata, signing) stored in `export_presets.cfg`. |
| **`export_presets.cfg`** | Committed project file holding all non-secret export configuration; the build recipe. |
| **`export_credentials.cfg`** | Gitignored file under `.godot/` holding passwords, signing identities and encryption keys entered in the export dialog. |
| **PCK** | Godot's packed resource archive; mounted at runtime as the read-only `res://` filesystem. Embedded in the executable or shipped as a sidecar file. |
| **`load_resource_pack()`** | `ProjectSettings` method mounting an external PCK/ZIP at runtime; `replace_files` controls whether it may override existing paths (patches yes, mods no). |
| **Remap** | Tiny entry shipped in the PCK redirecting a source path (`res://x.png`) to its imported artifact (`.godot/imported/x.png-<md5>.ctex`). |
| **Import cache (`.godot/`)** | Machine-local directory of imported artifacts; regenerated by `--import`; never committed, required before export. |
| **Feature tag** | String queryable via `OS.has_feature()` and usable in setting overrides; built-in (platform, `debug`/`release`) or custom per preset (`demo`, `staging`). |
| **Script export mode** | Preset choice of GDScript shipping format: text, binary tokens, or compressed binary tokens (default). Tokens are obfuscation-light, not security. |
| **PCK encryption** | AES-256 encryption of pack contents; requires custom templates compiled with the key. Raises extraction effort; cannot hide the key from the binary itself. |
| **SCons** | Godot's Python-based build system, used to compile editors and custom export templates (`platform=`, `target=`, `production=yes`). |
| **Headless mode** | `--headless`: engine without display/audio drivers; the mode CI uses for `--import` and `--export-*`. |
| **rcedit** | Tool Godot invokes to write the icon and version-info resource into exported Windows executables. |
| **Code signing** | Cryptographic signature identifying the publisher of a binary (signtool/Authenticode on Windows, codesign on macOS); prerequisite for reputation systems. |
| **SmartScreen** | Windows download-reputation gate; warns on unsigned or low-reputation executables. EV certificates and store distribution are the practical mitigations. |
| **Inno Setup** | Free scriptable Windows installer system; `.iss` scripts compiled by `ISCC.exe`; supports silent installs and upgrade-in-place keyed on a frozen `AppId`. |
| **AppId (Inno)** | GUID identifying an installed product across versions; changing it splits installs. |
| **AppImage** | Single-file, no-install Linux distribution format built from an AppDir with `appimagetool`. |
| **`.desktop` file** | Freedesktop metadata giving a Linux app its menu entry, icon and categories. |
| **Notarization** | Apple's automated malware scan of Developer-ID-signed software (`notarytool`); stapled ticket lets Gatekeeper open downloads without warnings. |
| **Gatekeeper** | macOS launch gate enforcing signing/notarization policy on quarantined downloads. |
| **Universal binary** | Single macOS executable containing x86_64 and arm64 slices; Godot's default macOS export. |
| **Keystore** | Java-format store of Android signing keys. The release keystore (or Play upload key) is the app's permanent identity — backup is existential. |
| **APK / AAB** | Installable Android package vs Play-required App Bundle (device-optimized delivery; needs gradle build in Godot). |
| **Gradle build** | Full Android project build path in Godot exports; required for AAB, plugins and manifest customization. |
| **COOP/COEP** | HTTP headers (`Cross-Origin-Opener-Policy` / `-Embedder-Policy`) enabling cross-origin isolation, required for `SharedArrayBuffer` and thus threaded web builds. |
| **butler** | itch.io's CLI uploader with delta patches and channels; the standard indie delivery tool. |
| **Semantic versioning** | `MAJOR.MINOR.PATCH` scheme; in games, MAJOR tracks experience/save-contract breaks and PATCH must always be safe to take. |
| **Reproducible build** | A build any clean machine can regenerate behaviorally identically from a tag: pinned engine, committed recipe, scripted steps, single version source. |
| **`override.cfg`** | Plain-text file next to an exported binary that overrides project settings at boot; a QA/ops tool, never shipped to players. |
| **AppDir** | The staged directory structure (`AppRun`, `.desktop`, `usr/bin/…`) that `appimagetool` compresses into an AppImage. |
| **xvfb** | X virtual framebuffer; provides a fake display so exported (non-headless) builds can boot in CI smoke tests. |
| **VDF** | Valve Data Format; the `app_build.vdf` script that drives `steamcmd` depot uploads. |
| **ICU data** | Unicode support tables bundled with templates; required for emoji and complex scripts (CJK, Thai, etc.) to render in exports. |
| **IARC** | International Age Rating Coalition — the free questionnaire that yields age ratings for Play and most digital storefronts. |
| **Release train** | Fixed-cadence release schedule that ships whatever is finished, decoupling fixes from feature risk. |

---

*Course: **Godot 4 in Production** — Module 11 of Phase 4 (Production). Case study: Relax Room (IFTS Projectwork 2026, author Renan Augusto Macena — System Architect & Project Supervisor). Verified against Godot 4.5 stable documentation, 2026-07-27.*

