---
course: "Godot 4 in Production"
phase: "3 — Persistence and project structure"
module: "08"
title: "Database and Persistence — Save Systems, SQLite and Cloud Sync"
version: "Godot 4.5 / GDScript 2.0"
level: "Intermediate-Advanced"
prerequisites: [ "GODOT_ENGINE_STUDY.md", "SCENES_AND_NODES.md" ]
objectives:
  - "Choose the right persistence format (ConfigFile, JSON, binary Variant, SQLite) for a given data shape and justify the choice"
  - "Implement a crash-safe SaveManager autoload with dirty flags, autosave, atomic writes, backup rotation and checksums"
  - "Design and execute a chained save-migration pipeline (v1 → vN) that never loses user data"
  - "Operate SQLite from GDScript through godot-sqlite with bound parameters, transactions, WAL mode and a schema_version table"
  - "Explain why loading Resources or object-capable Variants from untrusted files is a code-execution risk, and pick safe alternatives"
  - "Assess local authentication options honestly — including why plain salted SHA-256 is weaker than PBKDF2 — and implement both in Godot"
  - "Design an offline-first sync queue targeting Supabase REST with row-level security, and write tests that corrupt saves on purpose"
tags: [godot, gdscript, persistence, sqlite, json, save-system, configfile, supabase, security, migrations, offline-first, wal]
---

# Database and Persistence — Save Systems, SQLite and Cloud Sync — Complete Guide

> **Module 08** · **Updated:** 2026-07-27 · **Version:** Godot 4.5 / GDScript 2.0

> ### Learning objectives
>
> **Prerequisites:** [Godot Engine Study](GODOT_ENGINE_STUDY.md), [Scenes and Nodes](SCENES_AND_NODES.md) — plus basic SQL (SELECT/INSERT/JOIN) and the autoload pattern from [Autoload Safety](AUTOLOAD_SAFETY.md).
>
> By the end of this module you will be able to:
> 1. Navigate Godot's virtual file system (`res://` vs `user://`) and know exactly where your data lives on Windows, Linux, macOS, Android and iOS.
> 2. Use the full `FileAccess` / `DirAccess` API surface: open modes, binary and text I/O, compression, encryption, and disciplined error handling.
> 3. Pick a persistence format per data shape — ConfigFile for settings, JSON for readable state, `store_var` for Variant fidelity, SQLite for relational data — using a decision table, not habit.
> 4. Build a production `SaveManager`: dirty flag, autosave timer, save slots, atomic temp-file-plus-rename writes, backup rotation, checksum-based corruption detection.
> 5. Version every save file from day one and run chained migrations (v1 → v2 → … → vN) with worked, testable code.
> 6. Run SQLite inside Godot via the godot-sqlite GDExtension: typed schema, CRUD wrappers, prepared statements, transactions, WAL mode, PRAGMAs, migration tables and backups.
> 7. Reason about local auth (guest mode, salted hashes, PBKDF2-style stretching with `Crypto`/`HashingContext`) and about cloud sync (Supabase REST, RLS, offline queues, conflict resolution) — including when *not* to build them.
>
> **Estimated time:** 8-10 hours reading · 10-14 hours labs
> **Level:** Intermediate-Advanced

## Guiding ideas

1. **A save system's first job is to never lose data — write to a temp file, then rename; the old save must survive every crash.**
2. **Schema versioning is mandatory from day one — every format change ships together with a migration, and old migrations are never deleted.**
3. **Pick the format by data shape, not by habit — ConfigFile for settings, JSON for human-readable state, SQLite for relations and queries, binary for Variant fidelity.**
4. **Never load Resources or object-capable Variants from untrusted files — a `.tres` or `get_var(true)` payload can execute arbitrary code.**
5. **Offline-first means local storage is the source of truth — the cloud is a replica that improves the experience, never a requirement to play.**
6. **Parameterized queries and transactions are correctness features, not optimizations — string-built SQL and per-row commits are bugs waiting to ship.**

## Concept map

```
                          ┌─────────────────────────────────┐
                          │   DATABASE & PERSISTENCE (M08)  │
                          └────────────────┬────────────────┘
                                           │
        ┌──────────────────┬───────────────┼────────────────┬──────────────────┐
        │                  │               │                │                  │
 ┌──────▼──────┐   ┌───────▼──────┐ ┌──────▼───────┐ ┌──────▼──────┐  ┌────────▼───────┐
 │ File system │   │ Save formats │ │ Save system  │ │   SQLite    │  │  Cloud & auth  │
 │             │   │              │ │ architecture │ │             │  │                │
 │ res://      │   │ ConfigFile   │ │ SaveManager  │ │ godot-sqlite│  │ local auth     │
 │ user://     │   │ JSON         │ │ dirty flag   │ │ schema      │  │ hashing (PBKDF2│
 │ FileAccess  │   │ store_var    │ │ autosave     │ │ bindings    │  │  vs SHA-256)   │
 │ DirAccess   │   │ Resource     │ │ save slots   │ │ transactions│  │ Supabase REST  │
 │ error codes │   │  (⚠ security)│ │ atomic write │ │ WAL / PRAGMA│  │ RLS policies   │
 │ encryption  │   │ decision     │ │ backups      │ │ migrations  │  │ sync queue     │
 │ compression │   │  table       │ │ checksums    │ │ backups     │  │ conflicts (LWW)│
 └──────┬──────┘   └───────┬──────┘ └──────┬───────┘ └──────┬──────┘  └────────┬───────┘
        │                  │               │                │                  │
        └──────────────────┴───────┬───────┴────────────────┴──────────────────┘
                                   │
                     ┌─────────────▼──────────────┐
                     │  CASE STUDY: RELAX ROOM    │
                     │  JSON session save (v5)    │
                     │  + SQLite mirror (9 tables)│
                     │  + AuthManager (local)     │
                     │  + planned Supabase sync   │
                     └─────────────┬──────────────┘
                                   │
                     ┌─────────────▼──────────────┐
                     │  TESTING PERSISTENCE       │
                     │  temp dirs · fixtures ·    │
                     │  deliberate corruption     │
                     └────────────────────────────┘
```

## Table of contents

1. [Overview — persistence in a desktop companion app](#1-overview--persistence-in-a-desktop-companion-app)
2. [The virtual file system — res:// vs user://](#2-the-virtual-file-system--res-vs-user)
3. [FileAccess — complete API tour](#3-fileaccess--complete-api-tour)
4. [DirAccess and I/O error handling](#4-diraccess-and-io-error-handling)
5. [Persistence options compared](#5-persistence-options-compared)
6. [ConfigFile — the settings recipe](#6-configfile--the-settings-recipe)
7. [JSON saves — serialization strategies](#7-json-saves--serialization-strategies)
8. [Binary and Resource saves — fidelity vs security](#8-binary-and-resource-saves--fidelity-vs-security)
9. [SaveManager architecture](#9-savemanager-architecture)
10. [Atomic writes, backups and corruption detection](#10-atomic-writes-backups-and-corruption-detection)
11. [Save versioning and migration pipelines](#11-save-versioning-and-migration-pipelines)
12. [SQLite with godot-sqlite — setup and core API](#12-sqlite-with-godot-sqlite--setup-and-core-api)
13. [Schema design — the Relax Room database](#13-schema-design--the-relax-room-database)
14. [Queries, bindings and transactions](#14-queries-bindings-and-transactions)
15. [Operating SQLite — WAL, PRAGMAs, migrations, backups](#15-operating-sqlite--wal-pragmas-migrations-backups)
16. [Case study — the JSON + SQLite hybrid](#16-case-study--the-json--sqlite-hybrid)
17. [Authentication for offline apps](#17-authentication-for-offline-apps)
18. [Cloud sync and Supabase](#18-cloud-sync-and-supabase)
19. [Testing persistence](#19-testing-persistence)
20. [Best practices](#best-practices)
21. [Common errors & troubleshooting](#common-errors--troubleshooting)
22. [Exercises](#exercises)
23. [Further reading](#further-reading)
24. [Glossary](#glossary)

---

## 1. Overview — persistence in a desktop companion app

Persistence is the part of your application that outlives the process. Everything else — scenes, nodes, signals, rendering — is rebuilt from scratch every time the user launches the app. The save system is the single component whose bugs are *permanent*: a rendering glitch disappears on restart, but a corrupted save file destroys hours (or months) of user investment, and no patch can bring the data back.

This module treats persistence as a first-class engineering discipline with four layers:

| Layer | Question it answers | Tools in Godot 4.5 |
|---|---|---|
| **Storage** | Where do bytes live, and how do I read/write them safely? | `FileAccess`, `DirAccess`, `user://` |
| **Format** | How is state encoded into bytes? | `ConfigFile`, `JSON`, `store_var`, SQLite, `Resource` |
| **Architecture** | Who decides *when* and *what* to save, and how do we survive crashes and version changes? | `SaveManager` autoload, atomic writes, migrations |
| **Distribution** | How does state move between devices and users? | Supabase REST, sync queues, conflict resolution |

### The running case study: Relax Room

Throughout this module the worked example is **Relax Room**, the course's desktop companion app: a small always-available cozy room the user decorates, with lo-fi music, a customizable character, and an inventory bought with in-app coins. Its persistence profile is typical of desktop companion software and quite different from a twitch action game:

- **Writes are small and frequent** — a decoration moved, a track changed, a window repositioned. This argues for dirty-flag batching, not save-on-every-change.
- **The app runs for hours in the background** — autosave must be cheap and must never hitch the UI.
- **Data is relational** — accounts own characters, characters own rooms, accounts own inventory items that reference a shop catalog. This argues for SQLite alongside a JSON session save.
- **It must work 100% offline** — cloud sync (Supabase) is a planned convenience for multi-device users, never a login wall.
- **Users may inspect or share files** — human-readable JSON is a feature; executing untrusted content is a hard no.

Relax Room therefore uses a **dual-persistence** design: a JSON session save (readable, versioned, atomic) plus an SQLite mirror (relational integrity, queries, the future sync substrate). Section [16](#16-case-study--the-json--sqlite-hybrid) dissects this hybrid in depth; everything before it builds the vocabulary to judge it.

> ✅ **Best practice** — Decide your persistence architecture *before* writing gameplay code. Retro-fitting versioned saves onto an app that has been writing ad-hoc dictionaries for six months is one of the most expensive refactors in game development, because every existing user file becomes a legacy format you must support forever.

### What "production quality" means for a save system

A checklist we will fully unpack across this module. A production save system:

1. **Never truncates the only copy** of user data (atomic write: temp file → rename, [§10](#10-atomic-writes-backups-and-corruption-detection)).
2. **Keeps at least one known-good backup** and can detect corruption before trusting a file (checksums, [§10](#10-atomic-writes-backups-and-corruption-detection)).
3. **Carries a schema version** in every file and migrates old versions forward, never crashing on a v1 file in a v5 world ([§11](#11-save-versioning-and-migration-pipelines)).
4. **Fails loudly in development, gracefully in production** — every I/O call's error is checked and logged ([§4](#4-diraccess-and-io-error-handling)).
5. **Treats external files as hostile** — no code execution paths from data ([§8](#8-binary-and-resource-saves--fidelity-vs-security)), no SQL built by string concatenation ([§14](#14-queries-bindings-and-transactions)).
6. **Is testable** — the whole pipeline runs against temp directories with deterministic fixtures, including deliberately corrupted files ([§19](#19-testing-persistence)).

---

## 2. The virtual file system — res:// vs user://

Godot abstracts platform file systems behind two URI-like prefixes. Understanding exactly what each one is — and what it becomes after export — prevents an entire category of "works in the editor, breaks in the build" bugs.

### 2.1 res:// — the project bundle

`res://` points to the project root: the folder containing `project.godot` in development, and the packed **PCK/ZIP bundle** (or embedded data in the executable) after export.

Key properties:

- **In the editor:** `res://` is the project directory on disk. It is readable *and writable* (the editor itself writes there), which is precisely what makes it a trap.
- **After export:** `res://` is read from the PCK archive. It is **read-only**. `FileAccess.open("res://foo.json", FileAccess.WRITE)` fails in an exported build even though it worked in development.
- **Import pipeline:** many assets (textures, audio) are *remapped* on export — the original file is replaced by an imported `.ctex`/compressed version. Plain data files (`.json`, `.cfg`, `.txt`, `.csv`) are only included if the export preset's *filters to export non-resource files* includes them (e.g. `*.json`). Forgetting this filter is the classic "my catalog JSON is missing in the exported build" bug.

Legitimate uses of `res://` for persistence work are **read-only catalogs**: item definitions, decoration lists, music playlists, localization tables — data authored by you, shipped with the app, never modified at runtime. Relax Room ships its shop catalog and decoration metadata as JSON under `res://data/`.

> ⚠️ **Pitfall** — Writing to `res://` during development *appears* to work, and the app then fails silently after export. Any code path that writes must target `user://`. Grep your project for `"res://"` next to `FileAccess.WRITE` before every release.

### 2.2 user:// — the writable user data directory

`user://` is the per-user, per-project writable directory. Godot guarantees it is writable on every supported platform, including exported builds and sandboxed platforms.

Default physical locations (project name taken from **Project Settings → Application → Config → Name**):

| Platform | Default `user://` location |
|---|---|
| **Windows** | `%APPDATA%\Godot\app_userdata\[project_name]` |
| **macOS** | `~/Library/Application Support/Godot/app_userdata/[project_name]` |
| **Linux** | `~/.local/share/godot/app_userdata/[project_name]` |
| **Android** | app-internal storage: `/data/data/[package.name]/files/` (sandboxed, removed on uninstall) |
| **iOS** | the app's sandboxed Documents/Library area |
| **Web** | a virtual filesystem persisted in IndexedDB (asynchronous flush — see pitfall below) |

Two project settings change the desktop layout:

- `application/config/use_custom_user_dir = true` moves data out of the shared `Godot/app_userdata` umbrella, e.g. Windows: `%APPDATA%\[project_name]`.
- `application/config/custom_user_dir_name` replaces `[project_name]` with a name you pick (useful to keep the folder stable if the display name changes, or to brand it: `%APPDATA%\RelaxRoom`).

```gdscript
# Where is user:// physically, right now, on this machine?
func print_storage_locations() -> void:
    print("user:// -> ", OS.get_user_data_dir())
    # e.g. C:/Users/alex/AppData/Roaming/Godot/app_userdata/Relax Room
    print("save    -> ", ProjectSettings.globalize_path("user://save_data.json"))
    print("res     -> ", ProjectSettings.globalize_path("res://data/catalog.json"))
    # globalize_path on res:// returns a real path in the editor,
    # but points inside the PCK after export - do NOT hand it to external tools.
```

`ProjectSettings.globalize_path()` converts a `user://` or `res://` path into an absolute OS path; `ProjectSettings.localize_path()` does the reverse. You need globalized paths for the `*_absolute` methods of `DirAccess` ([§4](#4-diraccess-and-io-error-handling)) and whenever you pass a path to something outside Godot (an OS file dialog, an external tool, SQLite's own backup API).

> ✅ **Best practice** — Ship a debug menu item (or console command) that calls `OS.shell_open(OS.get_user_data_dir())` to open the save folder in the OS file explorer. It turns "please send me your save file" support requests from a 10-step tutorial into one click. In the editor, **Project → Open User Data Folder** does the same.

### 2.3 Choosing custom_user_dir_name early

Renaming the project later *silently changes* the default `user://` location, orphaning every existing user's data. Relax Room pins the folder on day one:

```ini
; project.godot (excerpt)
[application]
config/name="Relax Room"
config/use_custom_user_dir=true
config/custom_user_dir_name="RelaxRoom"
```

With this configuration the data lives in `%APPDATA%\RelaxRoom` on Windows, `~/Library/Application Support/RelaxRoom` on macOS and `~/.local/share/RelaxRoom` on Linux — stable across project renames, easy to document for users, easy to target with backup tools.

> ⚠️ **Pitfall** — On the **Web export**, `user://` writes land in a virtual filesystem that is flushed to IndexedDB asynchronously. A user closing the tab immediately after your save may lose it. If you target web builds, keep saves small, save early, and treat web persistence as best-effort (or push state to a server). Relax Room is desktop-first precisely to avoid this class of constraint.

### 2.4 What lives where — the Relax Room layout

```
res://  (read-only after export - authored content)
  data/
    catalog_items.json        # shop catalog: id, name, price, category, sprite path
    catalog_music.json        # lo-fi playlist metadata
    catalog_themes.json       # room themes
  addons/godot-sqlite/        # GDExtension binaries + wrapper (§12)

user:// (writable - everything the user produces)
  save_data.json              # primary session save (v5 format, §11)
  save_data.backup.json       # last known-good save (§10)
  settings.cfg                # window/audio/locale settings via ConfigFile (§6)
  relax_room.db               # SQLite database (§12-15)
  relax_room.db-wal           # SQLite write-ahead log (§15) - never delete by hand
  relax_room.db-shm           # SQLite shared-memory index (§15)
  logs/
    app_2026-07-27.jsonl      # AppLogger output with rotation
  backups/
    save_data.2026-07-26.json # rotated dated backups (§10)
```

The rule that generates this layout: **authored content in `res://`, user-generated state in `user://`, and nothing else anywhere else.** Temporary files during atomic writes also live in `user://` (same volume as their destination — a requirement for atomic rename, [§10](#10-atomic-writes-backups-and-corruption-detection)).

---

## 3. FileAccess — complete API tour

`FileAccess` is Godot 4's file handle class (the successor of Godot 3's `File`). You never construct it with `.new()`; you obtain an instance from a static factory, and the instance closes its file automatically when it goes out of scope (it is `RefCounted`) — though explicit `close()` remains good manners and is required before another process (like SQLite's CLI) can touch the file on Windows.

### 3.1 Opening files — modes and factories

```gdscript
# The four open modes (FileAccess.ModeFlags)
var r  := FileAccess.open("user://save.json", FileAccess.READ)        # must exist
var w  := FileAccess.open("user://save.json", FileAccess.WRITE)       # create or TRUNCATE
var rw := FileAccess.open("user://save.json", FileAccess.READ_WRITE)  # must exist, no truncate
var wr := FileAccess.open("user://save.json", FileAccess.WRITE_READ)  # create or TRUNCATE, then readable
```

| Mode | Value | Creates if missing | Truncates | Cursor | Typical use |
|---|---|---|---|---|---|
| `READ` | 1 | no (fails) | no | start | loading |
| `WRITE` | 2 | yes | **yes** | start | writing a fresh file |
| `READ_WRITE` | 3 | no (fails) | no | start | in-place patching (rare) |
| `WRITE_READ` | 7 | yes | **yes** | start | write then verify in one handle |

`FileAccess.open()` returns `null` on failure; the reason is retrieved with the *static* `FileAccess.get_open_error()`:

```gdscript
var file := FileAccess.open("user://save.json", FileAccess.READ)
if file == null:
    var err := FileAccess.get_open_error()
    match err:
        ERR_FILE_NOT_FOUND:
            return {}                      # first launch - not an error
        _:
            push_error("Open failed: %s" % error_string(err))
            return {}
```

`error_string(err)` converts any `Error` enum value into a readable message — use it in every log line instead of printing raw integers.

Besides plain `open()`, three specialized factories exist:

```gdscript
# Transparent compression (both ends must agree on the mode):
var fc := FileAccess.open_compressed("user://big_save.bin",
        FileAccess.WRITE, FileAccess.COMPRESSION_ZSTD)

# Encryption with a raw 32-byte key:
var key: PackedByteArray = crypto.generate_random_bytes(32)
var fe := FileAccess.open_encrypted("user://vault.bin", FileAccess.WRITE, key)

# Encryption derived from a password string:
var fp := FileAccess.open_encrypted_with_pass("user://vault.bin",
        FileAccess.WRITE, "correct horse battery staple")
```

Compression modes: `COMPRESSION_FASTLZ` (0), `COMPRESSION_DEFLATE` (1), `COMPRESSION_ZSTD` (2, best general choice), `COMPRESSION_GZIP` (3), `COMPRESSION_BROTLI` (4, **decompression only** — you can read Brotli, not write it). A file written with `open_compressed` has a small Godot-specific header; it is *not* a standard `.zst`/`.gz` file that external tools can open directly, and it must be re-opened with the same mode to be read.

> ⚠️ **Pitfall** — `open_encrypted_with_pass` protects against *casual* file editing, not against a motivated attacker: the password is inside your shipped binary, and anyone with a debugger or a GDScript decompiler can recover it. Treat save encryption as **tamper deterrence** (discouraging cheating/casual editing), never as security for genuinely sensitive data. Do not store secrets you would not put in plain text on the user's machine.

### 3.2 Text I/O

```gdscript
# Writing text
var f := FileAccess.open("user://notes.txt", FileAccess.WRITE)
f.store_string("no newline appended")   # exact string, as-is
f.store_line("newline appended")        # string + "\n"
f.store_csv_line(["id", "name", "price"], ",")  # proper CSV quoting
f.close()

# Reading text
var g := FileAccess.open("user://notes.txt", FileAccess.READ)
var everything := g.get_as_text()       # whole file as one String
g.seek(0)
while not g.eof_reached():
    var line := g.get_line()            # one line, newline stripped
```

Convenience statics avoid the open/close dance entirely for whole-file reads:

```gdscript
var text  := FileAccess.get_file_as_string("user://save.json")
var bytes := FileAccess.get_file_as_bytes("user://save.bin")
# On failure both return empty - check FileAccess.get_open_error() to distinguish
# "empty file" from "missing file".
```

### 3.3 Binary I/O and endianness

```gdscript
var f := FileAccess.open("user://save.bin", FileAccess.WRITE)
f.store_8(1)                    # unsigned 8-bit
f.store_16(65535)               # unsigned 16-bit
f.store_32(4_000_000_000)       # unsigned 32-bit
f.store_64(-42)                 # 64-bit (the only one that round-trips negatives directly)
f.store_float(0.5)              # 32-bit IEEE float
f.store_double(0.123456789012)  # 64-bit IEEE float
f.store_pascal_string("length-prefixed text")
f.store_buffer(PackedByteArray([0xDE, 0xAD]))
f.close()

var g := FileAccess.open("user://save.bin", FileAccess.READ)
var a := g.get_8()
var b := g.get_16()
var c := g.get_32()
var d := g.get_64()             # signed round-trip works at 64-bit width
var e := g.get_float()
var h := g.get_double()
var s := g.get_pascal_string()
var buf := g.get_buffer(2)
```

Two subtleties that bite in real projects:

1. **Signedness:** `store_8/16/32` store *unsigned* values. Storing `-1` with `store_16` and reading it back gives `65535`. If you need negative numbers, either use `store_64`/`get_64` (full signed round-trip) or re-interpret manually.
2. **Endianness:** the `big_endian` property controls multi-byte order and **resets to the platform default every time you open a file** — set it *after* opening, on both the writer and the reader, if you need a fixed cross-platform byte order for a custom binary format:

```gdscript
var f := FileAccess.open("user://net_format.bin", FileAccess.WRITE)
f.big_endian = true   # must be re-set after every open
f.store_32(0xCAFEBABE)
```

For save files you fully control on one machine this rarely matters (all Godot desktop targets are little-endian), but the moment a file crosses machines or is written by another tool, pin the byte order explicitly.

### 3.4 store_var / get_var — Variant serialization

`store_var` writes any Variant (dictionaries, arrays, `Vector2`, `Color`, packed arrays, …) in Godot's binary serialization format; `get_var` reads it back with full type fidelity — the reason many teams choose binary saves ([§8](#8-binary-and-resource-saves--fidelity-vs-security)):

```gdscript
var f := FileAccess.open("user://state.bin", FileAccess.WRITE)
f.store_var({
    "pos": Vector2(120, 64),        # stays a Vector2 - no JSON-style type loss
    "tint": Color(1, 0.8, 0.6),
    "coins": 250,                    # stays an int
})
f.close()

var g := FileAccess.open("user://state.bin", FileAccess.READ)
var state: Dictionary = g.get_var()  # default: allow_objects = false
```

The second parameter is the security-critical one:

```gdscript
f.store_var(data, true)   # full_objects = true: serializes Object instances
g.get_var(true)           # allow_objects = true: DESERIALIZES Objects - danger
```

> ⚠️ **Pitfall** — The official documentation for `get_var` is explicit: with `allow_objects = true`, *deserialized objects can contain code which gets executed*. An attacker hand-crafts a file whose embedded Object carries a script, you `get_var(true)` it, and their code runs with your app's privileges. **Never** enable `allow_objects` on data that could have been produced or modified outside your app — and a save file on the user's disk is exactly that. Keep the default `false`; it still round-trips every non-Object type you need. The same warning applies to `bytes_to_var_with_objects()` and to loading `Resource` files ([§8](#8-binary-and-resource-saves--fidelity-vs-security)).

### 3.5 Position, size, flushing, hashes

```gdscript
f.get_length()        # file size in bytes
f.get_position()      # cursor offset
f.seek(128)           # absolute seek from start
f.seek_end(-16)       # seek relative to end (negative offset)
f.eof_reached()       # true only AFTER a read past the end
f.resize(1024)        # truncate or zero-extend to exact length
f.flush()             # push buffers to the OS now
f.close()             # flush + release the handle

FileAccess.file_exists("user://save.json")      # static existence check
FileAccess.get_modified_time("user://save.json") # Unix timestamp (static)
FileAccess.get_sha256("user://save.json")       # hex SHA-256 of the file (static)
FileAccess.get_md5("user://save.json")          # hex MD5 (static, non-cryptographic uses only)
```

`flush()` hands data to the OS but is not a hardware sync guarantee; `close()` flushes too. Calling `flush()` after every store call destroys performance — rely on `close()` at the end of a save, and on the atomic-write pattern ([§10](#10-atomic-writes-backups-and-corruption-detection)) for crash safety rather than on manual flushing.

`FileAccess.get_sha256()` is the building block for cheap corruption detection: hash the payload file after writing, store the hex digest alongside it, re-hash and compare on load ([§10.4](#10-atomic-writes-backups-and-corruption-detection)).

> ✅ **Best practice** — `eof_reached()` becomes `true` only *after* a read attempt past the last byte, which makes `while not f.eof_reached():` loops read one garbage iteration in some patterns. Prefer length-driven loops for binary formats (`while f.get_position() < f.get_length():`) and reserve `eof_reached()` for line-oriented text.

### 3.6 Compressed and encrypted saves in practice

The specialized factories from [§3.1](#3-fileaccess--complete-api-tour) become interesting once saves grow or once tamper-deterrence is a requirement. A decision guide first:

| Situation | Use | Don't use |
|---|---|---|
| Save < ~100 KB (Relax Room's case) | plain text — readability is worth more than bytes | compression (saves nothing you care about) |
| Save in the MB range, rarely inspected | `open_compressed` with `COMPRESSION_ZSTD` | hand-rolled zip pipelines |
| Deter casual save editing (cosmetic economy) | checksum ([§10.4](#10-atomic-writes-backups-and-corruption-detection)), maybe `open_encrypted_with_pass` | pretending it stops real attackers |
| Interop with external tools | plain JSON | Godot-header compressed files (not standard `.zst`) |

A compressed writer/reader is a two-line change from the plain version — the mode must match on both ends, and the atomic-write pattern ([§10.2](#10-atomic-writes-backups-and-corruption-detection)) wraps it unchanged because compression happens inside the file handle:

```gdscript
func write_compressed_save(path: String, document: Dictionary) -> Error:
    var f := FileAccess.open_compressed(path, FileAccess.WRITE, FileAccess.COMPRESSION_ZSTD)
    if f == null:
        return FileAccess.get_open_error()
    f.store_string(JSON.stringify(document))    # skip "\t" - nobody reads compressed bytes
    f.close()
    return OK

func read_compressed_save(path: String) -> Dictionary:
    var f := FileAccess.open_compressed(path, FileAccess.READ, FileAccess.COMPRESSION_ZSTD)
    if f == null:
        return {}
    var doc: Variant = JSON.parse_string(f.get_as_text())
    f.close()
    return doc if typeof(doc) == TYPE_DICTIONARY else {}
```

When you need compression on a buffer rather than a file — for example before inserting a large JSON payload into an SQLite BLOB column, or before an HTTP upload — `PackedByteArray` carries the same codecs directly:

```gdscript
var raw := JSON.stringify(document).to_utf8_buffer()
var packed := raw.compress(FileAccess.COMPRESSION_ZSTD)
# ... store `packed` (plus raw.size(), you need it to decompress) ...
var restored := packed.decompress(raw.size(), FileAccess.COMPRESSION_ZSTD)
```

Note that `decompress()` needs the *original* size — store it alongside the blob (a two-field envelope: `{"size": n, "zstd": bytes}`).

Encryption composes the same way, with two operational rules. First, `open_encrypted` wants a raw 32-byte key; `open_encrypted_with_pass` derives one from a password string — the latter is the practical choice when the "key" is baked into the binary anyway. Second, an encrypted file cannot be opened by `open()` and vice versa: version your decision. If v6 of your save becomes encrypted, the loader must try the encrypted open first and fall back to plain for v5-and-older files, then re-save encrypted — an ordinary migration, applied at the file-container level:

```gdscript
func open_save_any(path: String) -> FileAccess:
    var f := FileAccess.open_encrypted_with_pass(path, FileAccess.READ, SAVE_PASS)
    if f != null:
        return f                                   # v6+ container
    return FileAccess.open(path, FileAccess.READ)  # legacy plain container (v5-)
```

> ⚠️ **Pitfall** — Compression and whole-file encryption both destroy partial readability: a truncated plain JSON file often yields *some* salvageable text for support forensics, a truncated compressed/encrypted file yields nothing. If you adopt either, your backup rotation and checksum story ([§10](#10-atomic-writes-backups-and-corruption-detection)) stops being nice-to-have and becomes the only recovery path. Adopt them for a reason, not by default.

---

## 4. DirAccess and I/O error handling

### 4.1 DirAccess essentials

`DirAccess` manipulates directories and file metadata. Like `FileAccess` it has two usage styles: **static absolute methods** (one-shot operations, path passed each call) and an **instance API** (open a directory, then operate relative to it).

```gdscript
# --- Static style: quick one-shot operations ---
DirAccess.make_dir_recursive_absolute("user://backups/2026-07")
DirAccess.dir_exists_absolute("user://backups")
DirAccess.copy_absolute("user://save_data.json", "user://backups/save_copy.json")
DirAccess.rename_absolute("user://save.tmp", "user://save_data.json")  # atomic move (§10)
DirAccess.remove_absolute("user://old_file.json")   # deletes file OR empty dir - no recycle bin

# --- Instance style: listing and relative work ---
var dir := DirAccess.open("user://backups")
if dir == null:
    push_error("Cannot open backups dir: %s" % error_string(DirAccess.get_open_error()))
    return
for file_name in dir.get_files():          # Array of file names (not full paths)
    print("backup found: ", file_name)
for sub in dir.get_directories():          # subdirectory names
    print("subdir: ", sub)
```

The `*_absolute` statics accept `user://` and `res://` paths despite the name — "absolute" means "not relative to an opened instance". For paths *outside* the Godot sandbox (rare, e.g. exporting a user-selected backup location from a file dialog), globalize first:

```gdscript
var export_target: String = chosen_dir.path_join("relax_room_backup.json")  # from FileDialog
DirAccess.copy_absolute(
    ProjectSettings.globalize_path("user://save_data.json"),
    export_target)
```

For fine-grained iteration (filtering, skipping hidden files) use the iterator API:

```gdscript
func list_saves() -> Array[String]:
    var found: Array[String] = []
    var dir := DirAccess.open("user://")
    if dir == null:
        return found
    dir.list_dir_begin()
    var name := dir.get_next()
    while name != "":
        if not dir.current_is_dir() and name.ends_with(".json"):
            found.append(name)
        name = dir.get_next()
    dir.list_dir_end()
    return found
```

> ⚠️ **Pitfall** — `DirAccess.remove_absolute()` (and instance `remove()`) delete **permanently and immediately**; there is no undo and no recycle bin. When the thing being deleted is user data (a save slot, an account), prefer `OS.move_to_trash(ProjectSettings.globalize_path(path))` — it returns an `Error` and gives users a recovery path. Reserve hard deletion for your own temp files.

### 4.2 A disciplined error-handling pattern

Godot I/O methods report failures in two ways: factories return `null` (with the reason in `get_open_error()`), and operations return an `Error` enum (`OK == 0` on success). Production code checks **every** one of them. The temptation to skip checks is strongest exactly where failures are most likely: user machines with full disks, aggressive antivirus locking freshly-written files, cloud-synced roaming profiles, and permissions oddities you will never reproduce locally.

The pattern used across Relax Room — every persistence entry point returns a typed result and logs on failure, callers decide policy:

```gdscript
## Result of a persistence operation: check .ok before using .data.
class SaveResult:
    var ok: bool = false
    var error: Error = OK
    var message: String = ""
    var data: Variant = null

    static func success(value: Variant = null) -> SaveResult:
        var r := SaveResult.new()
        r.ok = true
        r.data = value
        return r

    static func failure(err: Error, msg: String) -> SaveResult:
        var r := SaveResult.new()
        r.error = err
        r.message = msg
        push_error("[persistence] %s (%s)" % [msg, error_string(err)])
        return r


func read_json_file(path: String) -> SaveResult:
    if not FileAccess.file_exists(path):
        return SaveResult.failure(ERR_FILE_NOT_FOUND, "Missing file: " + path)

    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        return SaveResult.failure(FileAccess.get_open_error(), "Cannot open: " + path)

    var text := file.get_as_text()
    file.close()

    var json := JSON.new()                       # instance form: precise error reporting
    var parse_err := json.parse(text)
    if parse_err != OK:
        return SaveResult.failure(parse_err,
            "JSON error in %s at line %d: %s" % [path, json.get_error_line(), json.get_error_message()])

    if typeof(json.data) != TYPE_DICTIONARY:
        return SaveResult.failure(ERR_INVALID_DATA, "Expected object at top level: " + path)

    return SaveResult.success(json.data)
```

Design points worth internalizing:

- **Missing file is not an error** at the policy level (first launch), but the *reader* still reports it distinctly so callers can branch: `ERR_FILE_NOT_FOUND` → build default state; any other error → try the backup ([§10](#10-atomic-writes-backups-and-corruption-detection)).
- **The instance `JSON.new()` + `parse()` form** is used instead of the static `JSON.parse_string()` because it exposes `get_error_line()` / `get_error_message()` — the difference between a useless log entry and a fixable bug report.
- **Type-check the top level.** `json.parse` happily returns arrays, numbers or strings; assuming `Dictionary` and calling `.get()` on a float is a runtime crash delivered by a corrupted file.
- **Log at the point of detection, decide at the point of policy.** The reader logs once with full context; callers do not re-log, they choose fallback behavior.

### 4.3 Error codes you will actually meet

| Error | Constant | Typical persistence cause |
|---|---|---|
| 0 | `OK` | success |
| 7 | `ERR_FILE_NOT_FOUND` | first launch; wrong path; export filter excluded a `res://` data file |
| 8 | `ERR_FILE_BAD_DRIVE` / bad path | malformed path string |
| 10 | `ERR_FILE_NO_PERMISSION` | writing to `res://` in an exported build; OS permissions; antivirus lock |
| 12 | `ERR_FILE_CANT_OPEN` | file locked by another process (Windows: rarely, your own unclosed handle) |
| 15 | `ERR_FILE_UNRECOGNIZED` | wrong open mode for encrypted/compressed file; not a Godot-written format |
| 16 | `ERR_FILE_CORRUPT` | truncated/garbled file — trigger backup restore ([§10](#10-atomic-writes-backups-and-corruption-detection)) |
| 18 | `ERR_FILE_EOF` | read past end — binary format/version mismatch |
| 43 | `ERR_PARSE_ERROR` | invalid JSON / malformed ConfigFile |
| 46 | `ERR_INVALID_DATA` | your own validation rejected the payload |

> ✅ **Best practice** — Route every persistence failure through one logging chokepoint (Relax Room uses its `AppLogger` autoload writing JSONL to `user://logs/`). When a user reports "my room reset itself", the log tells you *which* file failed, *which* error code, and *which* fallback ran — without asking them to reproduce anything.

### 4.4 Path hygiene

Persistence bugs love string-built paths. Four habits eliminate most of them:

```gdscript
# 1) Compose with path_join, never with "+" and hand-placed slashes:
var slot_save := SLOTS_ROOT.path_join("slot_02").path_join("save_data.json")

# 2) Decompose with the String path helpers:
slot_save.get_base_dir()      # "user://slots/slot_02"
slot_save.get_file()          # "save_data.json"
slot_save.get_extension()     # "json"

# 3) Sanitize anything user-typed before it becomes a file name:
func slot_file_name(user_label: String) -> String:
    var safe := user_label.validate_filename()    # strips / \ : * ? " < > | etc.
    return safe if not safe.is_empty() else "unnamed"

# 4) Constants for every persistent path, defined once, in the owning autoload.
#    A path literal appearing twice in the codebase is a future divergence bug.
```

Rule 3 is quietly a security rule: a profile named `../../save_data` must become a harmless file name, not a path traversal that overwrites another slot's data. `String.validate_filename()` handles the character-level dangers; pairing it with `path_join` onto a fixed base directory (never concatenating the raw input into the path) closes the traversal case entirely.

---

## 5. Persistence options compared

Godot offers five realistic persistence formats. None is "best"; each dominates for a particular data shape. This section gives you the decision framework the rest of the module keeps applying.

### 5.1 The decision table

| Criterion | ConfigFile (INI) | JSON | `store_var` binary | Resource (.tres/.res) | SQLite |
|---|---|---|---|---|---|
| Human-readable | yes | yes | no | .tres yes / .res no | via tools only |
| Type fidelity (Vector2, Color, int) | **full** (Variant text) | poor (float-only numbers, no engine types) | **full** | **full** | SQL types only |
| Relations / queries | no | no | no | no | **yes** (FK, JOIN, WHERE) |
| Diff/merge friendliness | good | good | none | medium | none |
| Concurrent access | no | no | no | no | **yes** (WAL) |
| Crash safety built-in | no | no | no | no | **yes** (journal/WAL) |
| Migration ergonomics | easy | easy | **hard** (binary layout) | medium | good (`schema_version`) |
| Safe with untrusted files | yes | yes | yes (`allow_objects=false`) | **NO — can execute code** | yes (data only) |
| Extra dependency | none | none | none | none | GDExtension plugin |
| Practical size sweet spot | < 100 KB | < ~10 MB | < ~50 MB | small | GB+ |
| Web export | yes | yes | yes | yes | limited (plugin build) |

### 5.2 When to use what

```
ConfigFile        →  settings: window, audio, locale, keybindings, small flags
JSON (user://)    →  session/game saves the user may inspect; export/share features
JSON (res://)     →  read-only authored catalogs shipped with the app
store_var binary  →  large or engine-type-heavy state where readability is not needed
Resource saves    →  authored content in the editor pipeline ONLY - never user-shared data
SQLite            →  relational user state, accounts, inventories, sync queues, logs
```

Three questions decide almost every case:

1. **Does the data have relationships or need querying?** Accounts→characters→rooms, "all items of category X", a sync queue drained in insertion order — SQLite. Flat snapshots — files.
2. **Will a human (user, tester, you at 2 a.m.) need to read it?** Settings and saves benefit enormously from being readable; choose ConfigFile/JSON and accept the type-fidelity tax ([§7.2](#7-json-saves--serialization-strategies)).
3. **Could the file arrive from outside your app?** Shared saves, mods, cloud downloads: the format must be inert data. JSON, ConfigFile values, `get_var(false)` and SQLite rows are inert; Resources and `get_var(true)` are not ([§8](#8-binary-and-resource-saves--fidelity-vs-security)).

> ✅ **Best practice** — It is normal — and healthy — for one app to use **several** formats simultaneously. Relax Room ships with all of: ConfigFile (`settings.cfg`), JSON catalogs in `res://`, a JSON session save in `user://`, and SQLite. What matters is that each piece of data has exactly **one authoritative home**, with any duplication (like the JSON↔SQLite mirror, [§16](#16-case-study--the-json--sqlite-hybrid)) explicitly designated as a derived copy with a defined reconciliation rule.

### 5.3 Worked decisions — three Relax Room datums

Applying the three questions to real data makes the framework concrete:

**Window position and volume.** No relations, no queries; a human may tweak it; tiny. → **ConfigFile** (`settings.cfg`, [§6](#6-configfile--the-settings-recipe)). Choosing SQLite here would mean opening a database connection to remember that the music was muted — technically fine, architecturally silly.

**Placed decorations in the room.** A list of `{item_id, position, scale, rotation}` records loaded and saved as one unit with the room; the user might legitimately want to inspect or share their layout; no cross-record queries. → **JSON document** inside the session save ([§7](#7-json-saves--serialization-strategies)) — and, mirrored, a JSON *column* in SQLite rather than a normalized table ([§13.3](#13-schema-design--the-relax-room-database)). Same reasoning, two layers.

**Owned items.** Relational by nature (account ↔ item ↔ catalog), queried ("do I own this?", "inventory count vs capacity"), constrained (no negative quantities, no duplicates), and the payload of future sync. → **SQLite** ([§12](#12-sqlite-with-godot-sqlite--setup-and-core-api)-[§15](#15-operating-sqlite--wal-pragmas-migrations-backups)), with the save file carrying a snapshot for readability.

The pattern to internalize: the *same app* lands on three different answers because the *data shapes* differ — and each answer would be wrong for one of the other datums.

### 5.4 A note on rolling your own format

Custom binary formats (hand-written `store_32` layouts) buy you nothing over `store_var` for save data except bugs: you re-implement type tags, string encoding, versioning and endianness that the Variant serializer already does correctly. The legitimate niches are interop with external tools and very hot append-only logs. For everything else in this course: don't.

---

## 6. ConfigFile — the settings recipe

`ConfigFile` reads and writes INI-style text files with a Godot twist: **values are full Variants** serialized as text. A `Vector2i` window size or a `Color` accent stored with `set_value` comes back as the same type — no manual conversion, which is exactly the ergonomics you want for settings.

```ini
; user://settings.cfg - written by ConfigFile.save()
[window]
size=Vector2i(1280, 720)
position=Vector2i(240, 120)
screen=0
mode=0

[audio]
master_volume=0.8
music_volume=0.65
sfx_volume=1.0
muted=false

[app]
locale="en"
autosave_seconds=60
```

### 6.1 API in one glance

```gdscript
var cfg := ConfigFile.new()

# Writing
cfg.set_value("audio", "master_volume", 0.8)     # section, key, Variant
var err := cfg.save("user://settings.cfg")       # returns Error - check it

# Reading (third argument = default when missing: ALWAYS pass it)
var load_err := cfg.load("user://settings.cfg")   # ERR_FILE_NOT_FOUND on first run - fine
var vol: float = cfg.get_value("audio", "master_volume", 0.8)

# Introspection & cleanup
cfg.has_section("audio")
cfg.has_section_key("audio", "muted")
cfg.get_sections()                 # PackedStringArray
cfg.get_section_keys("audio")
cfg.erase_section_key("audio", "obsolete_key")
cfg.erase_section("legacy")
cfg.clear()

# Text round-trip (useful in tests) and encrypted variants
cfg.encode_to_text()               # the file content as a String
cfg.parse(text)                    # load from a String instead of a file
cfg.save_encrypted_pass("user://settings.cfg", "pass")
cfg.load_encrypted_pass("user://settings.cfg", "pass")
```

Format caveats: section and key names must not contain spaces (anything after a space is ignored), and comments (`;`) survive parsing but are **discarded on save** — do not hand-maintain documentation inside a file your app rewrites.

### 6.2 The full SettingsManager recipe

The complete, production-shaped settings autoload used by Relax Room: typed defaults in one place, load-with-defaults (missing file is normal), apply-on-load, save-on-change with debounce, and window geometry captured at quit.

```gdscript
# settings_manager.gd - autoload "Settings"
extends Node

const PATH := "user://settings.cfg"

# Single source of truth for defaults - reading and resetting both use it.
const DEFAULTS := {
    "window": {
        "size": Vector2i(1280, 720),
        "position": Vector2i(-1, -1),          # -1,-1 = "let the OS place it"
        "screen": 0,
        "mode": Window.MODE_WINDOWED,
    },
    "audio": {
        "master_volume": 0.8, "music_volume": 0.65, "sfx_volume": 1.0, "muted": false,
    },
    "app": {
        "locale": "en", "autosave_seconds": 60,
    },
}

var _cfg := ConfigFile.new()
var _save_pending := false

func _ready() -> void:
    load_settings()
    apply_all()

func load_settings() -> void:
    var err := _cfg.load(PATH)
    if err != OK and err != ERR_FILE_NOT_FOUND:
        push_warning("settings.cfg unreadable (%s) - using defaults" % error_string(err))
        _cfg = ConfigFile.new()                 # corrupted file: start clean, do not crash

func get_setting(section: String, key: String) -> Variant:
    return _cfg.get_value(section, key, DEFAULTS[section][key])

func set_setting(section: String, key: String, value: Variant) -> void:
    _cfg.set_value(section, key, value)
    _queue_save()

func _queue_save() -> void:
    # Debounce: a volume slider emits dozens of changes per second;
    # write once, at the end of the frame.
    if _save_pending:
        return
    _save_pending = true
    _flush_deferred.call_deferred()

func _flush_deferred() -> void:
    _save_pending = false
    var err := _cfg.save(PATH)
    if err != OK:
        push_error("Cannot save settings: %s" % error_string(err))

# ---- Applying settings to the running app ----

func apply_all() -> void:
    apply_window()
    apply_audio()
    TranslationServer.set_locale(get_setting("app", "locale"))

func apply_window() -> void:
    var win := get_window()
    win.mode = get_setting("window", "mode")
    if win.mode == Window.MODE_WINDOWED:
        win.size = get_setting("window", "size")
        var pos: Vector2i = get_setting("window", "position")
        if pos != Vector2i(-1, -1):
            win.position = pos

func apply_audio() -> void:
    _set_bus_volume("Master", get_setting("audio", "master_volume"))
    _set_bus_volume("Music",  get_setting("audio", "music_volume"))
    _set_bus_volume("SFX",    get_setting("audio", "sfx_volume"))
    AudioServer.set_bus_mute(AudioServer.get_bus_index("Master"),
        get_setting("audio", "muted"))

func _set_bus_volume(bus_name: String, linear: float) -> void:
    var idx := AudioServer.get_bus_index(bus_name)
    if idx >= 0:
        AudioServer.set_bus_volume_db(idx, linear_to_db(clampf(linear, 0.0001, 1.0)))

# ---- Capturing window geometry at quit ----

func _notification(what: int) -> void:
    if what == NOTIFICATION_WM_CLOSE_REQUEST:
        var win := get_window()
        if win.mode == Window.MODE_WINDOWED:
            _cfg.set_value("window", "size", win.size)
            _cfg.set_value("window", "position", win.position)
        _cfg.set_value("window", "mode", win.mode)
        _cfg.save(PATH)     # synchronous on purpose: the app is quitting
```

Details that separate this from a toy example:

- **Volumes are stored linear (0-1), applied in dB** via `linear_to_db()`. Storing dB directly makes sliders unusable (perceptual scale) and defaults unreadable. The clamp floor avoids `linear_to_db(0)` → `-inf`.
- **Debounced saves** mean a slider drag costs one disk write, not sixty.
- **Window geometry is read back at close**, not tracked continuously, and only persisted for the windowed mode — restoring a maximized flag and a stale rectangle together is a classic bug.
- **A corrupted settings file is discarded silently.** Settings are cheap to rebuild; the correct fallback is defaults, not an error dialog. Contrast with the *save file*, where the fallback ladder is backup → older backup → fresh state, each step logged ([§10](#10-atomic-writes-backups-and-corruption-detection)).

> ⚠️ **Pitfall** — Restoring a saved window *position* blindly can place the window on a monitor that no longer exists (user unplugged the second display). Validate against `DisplayServer.get_screen_count()` / screen rects before applying, and fall back to OS placement when the saved position is off-screen.

### 6.3 Persisting rebindable controls

Keybindings are settings too, and even a companion app grows shortcuts (toggle always-on-top, next track, hide to tray). The tempting shortcut — storing `InputEventKey` objects directly as ConfigFile values — works mechanically (ConfigFile serializes Variants, including Resources, as text) but couples your settings file to engine serialization details and re-imports object data from an editable file, which is exactly the trust direction [§8](#8-binary-and-resource-saves--fidelity-vs-security) teaches you to avoid. Store plain data instead — the keycode and modifiers — and rebuild events on load:

```gdscript
const REBINDABLE := ["toggle_always_on_top", "music_next", "hide_to_tray"]

func save_bindings() -> void:
    for action in REBINDABLE:
        var events := InputMap.action_get_events(action)
        if events.is_empty():
            continue
        var ev := events[0]
        if ev is InputEventKey:
            _cfg.set_value("input", action, {
                "physical_keycode": ev.physical_keycode,
                "ctrl": ev.ctrl_pressed, "alt": ev.alt_pressed, "shift": ev.shift_pressed,
            })
    _queue_save()

func load_bindings() -> void:
    for action in REBINDABLE:
        var stored: Variant = _cfg.get_value("input", action, null)
        if typeof(stored) != TYPE_DICTIONARY:
            continue                       # keep the project-default binding
        var ev := InputEventKey.new()
        ev.physical_keycode = int(stored.get("physical_keycode", 0)) as Key
        ev.ctrl_pressed = bool(stored.get("ctrl", false))
        ev.alt_pressed = bool(stored.get("alt", false))
        ev.shift_pressed = bool(stored.get("shift", false))
        InputMap.action_erase_events(action)
        InputMap.action_add_event(action, ev)
```

Details that matter: use `physical_keycode` (position on the keyboard) rather than `keycode` so bindings survive layout switches (QWERTY/AZERTY); only rebind actions on your explicit allowlist, so a hand-edited file cannot clobber engine-internal `ui_*` actions; and treat "no stored value" as "project default", which means resetting a binding is just `erase_section_key`.

---

## 7. JSON saves — serialization strategies

JSON is the workhorse format for session saves in Relax Room and for authored catalogs: universally readable, diffable, debuggable with any text editor, and safe — parsing JSON can never execute code. Its cost is **type poverty**, and a robust save layer is mostly a disciplined answer to that cost.

### 7.1 The Godot JSON API

```gdscript
# Serialize: static, one-liner. "\t" = pretty-print with tabs (use "" in production
# for smaller files if humans rarely read them; Relax Room keeps "\t" on purpose).
var text := JSON.stringify(save_data, "\t")

# Parse, quick form: returns null on ANY error - fine for data you generated a line ago.
var data: Variant = JSON.parse_string(text)

# Parse, diagnostic form: keeps line numbers and messages - use for files from disk.
var json := JSON.new()
var err := json.parse(text)
if err != OK:
    push_error("line %d: %s" % [json.get_error_line(), json.get_error_message()])
else:
    var data2: Variant = json.data
```

`JSON.stringify(data, indent, sort_keys, full_precision)` — two optional flags matter more than they look:

- `sort_keys` (default `true`) makes output deterministic, which keeps diffs and checksums stable.
- `full_precision = true` prints floats with enough digits to round-trip exactly; without it, extreme values can drift a ULP across save/load cycles. For positions in a cozy room this is irrelevant; for accumulated simulation state it is not.

### 7.2 Type loss — what JSON does to your data

JSON has strings, booleans, null, arrays, objects and **one number type**. Godot's parser maps every JSON number to a `float` (64-bit), and every object key to a `String`:

| You store (Variant) | JSON text | You get back |
|---|---|---|
| `int` `250` | `250` | `float` `250.0` |
| `Vector2(3, 4)` | `"(3, 4)"` (stringified!) | `String` — **data loss** |
| `Color(1,0,0)` | `"(1, 0, 0, 1)"` | `String` — **data loss** |
| `Dictionary` int keys `{1: "a"}` | `{"1": "a"}` | `String` keys |
| `NAN` / `INF` | invalid JSON emitted | parse error on load |

Consequences you must design for:

```gdscript
# 1) Re-int your ints on load (comparison bugs otherwise: 3.0 == 3 is true,
#    but typed arrays, match statements and dictionary keys care).
var coins: int = int(data.get("coins", 0))

# 2) Engine types need an explicit convention. Relax Room uses {x,y} objects:
#    "position": {"x": 120.0, "y": 64.0}
```

### 7.3 to_dict / from_dict — the serialization convention

The scalable pattern: every persistent gameplay class owns its JSON shape via a `to_dict()` / `from_dict()` pair. Serialization knowledge lives *with* the data, defaults are applied in exactly one place, and the save manager composes documents without knowing any field names.

```gdscript
# decoration_state.gd - one placed decoration in the room
class_name DecorationState
extends RefCounted

var item_id: int = 0
var position := Vector2.ZERO
var scale := Vector2.ONE
var rotation_deg: float = 0.0
var flip_h: bool = false

func to_dict() -> Dictionary:
    return {
        "item_id": item_id,
        "position": {"x": position.x, "y": position.y},
        "scale": {"x": scale.x, "y": scale.y},
        "rotation_deg": rotation_deg,
        "flip_h": flip_h,
    }

static func from_dict(d: Dictionary) -> DecorationState:
    var s := DecorationState.new()
    s.item_id = int(d.get("item_id", 0))
    s.position = _vec2(d.get("position"), Vector2.ZERO)
    s.scale = _vec2(d.get("scale"), Vector2.ONE)
    s.rotation_deg = float(d.get("rotation_deg", 0.0))
    s.flip_h = bool(d.get("flip_h", false))
    return s

static func _vec2(v: Variant, fallback: Vector2) -> Vector2:
    if typeof(v) == TYPE_DICTIONARY and v.has("x") and v.has("y"):
        return Vector2(float(v.x), float(v.y))
    return fallback
```

Rules encoded in this small class, applicable to every persistent type:

1. **`from_dict` never trusts the input.** Every field goes through `get()` with a default plus an explicit cast; malformed sub-structures fall back instead of crashing. A save file is user-editable by definition — someone *will* hand-edit it, badly.
2. **`from_dict` is `static`** and returns a fresh instance: loading never mutates live state until the whole document parses successfully (no half-loaded rooms).
3. **Casts are explicit** (`int()`, `float()`, `bool()`) so JSON's float-only numbers and any hand-edited strings normalize at the boundary — the rest of the codebase sees clean types.
4. **The dictionary shape is the contract.** Renaming a field is a *format change* and belongs to a migration ([§11](#11-save-versioning-and-migration-pipelines)), not a silent edit.

An alternative for engine types is `var_to_str()` / `str_to_var()` — text round-trip with full Variant fidelity (`"Vector2(120, 64)"` comes back as a real `Vector2`). It is safe for the types you use in saves (it does not execute scripts), but the output is Godot-specific text inside your JSON strings, opaque to external tools and schema validators. Relax Room prefers explicit `{x, y}` objects: marginally more code, fully portable, self-describing. Pick one convention and never mix the two in one file.

### 7.4 The envelope — every save document's outer shape

Whatever the payload, wrap it in a stable envelope from day one:

```json
{
    "version": 5,
    "saved_at": "2026-07-27T18:42:11",
    "app_version": "1.3.0",
    "checksum": "9f2c1a…",
    "data": {
        "account":  { "display_name": "alex", "coins": 250 },
        "character":{ "name": "Mimi", "eye_color": 2, "hair_color": 1, "skin_color": 0, "stress_level": 10 },
        "room":     { "room_type": "cozy_studio", "theme": "modern", "decorations": [] },
        "music":    { "playlist": "lofi_rain", "track_index": 3, "position_sec": 42.5 },
        "inventory":{ "capacity": 50, "items": [ {"item_id": 12, "quantity": 1} ] }
    }
}
```

- `version` drives the migration pipeline ([§11](#11-save-versioning-and-migration-pipelines)). An integer, compared with `<`, incremented on **every** format change. Semantic versions ("5.0.0") add parsing complexity for zero benefit inside a save file.
- `saved_at` / `app_version` cost nothing and are gold in bug reports ("the corrupted file was written by 1.2.9 on July 3rd — that's the build with the truncation bug").
- `checksum` covers the `data` sub-document and gates loading ([§10.4](#10-atomic-writes-backups-and-corruption-detection)).
- `data` holds the actual state, composed from `to_dict()` calls.

### 7.6 Schema validation — trust nothing, reject early

`from_dict`'s per-field defensiveness ([§7.3](#7-json-saves--serialization-strategies)) handles *values*; a document-level validator handles *shape*, so structural problems are rejected in one place with one clear log line instead of surfacing as twenty scattered fallbacks:

```gdscript
# save_schema.gd - lightweight structural validation, no dependencies
class_name SaveSchema

const REQUIRED_SECTIONS := {
    # section name        → required keys with expected Variant types
    "account":  {"auth_uid": TYPE_STRING, "coins": TYPE_FLOAT},   # JSON numbers = float!
    "character":{"name": TYPE_STRING},
    "room":     {"room_type": TYPE_STRING, "decorations": TYPE_ARRAY},
    "inventory":{"capacity": TYPE_FLOAT, "items": TYPE_ARRAY},
}

static func validate(data: Dictionary) -> Array[String]:
    var problems: Array[String] = []
    for section_name in REQUIRED_SECTIONS:
        var section: Variant = data.get(section_name)
        if typeof(section) != TYPE_DICTIONARY:
            problems.append("missing/invalid section: " + section_name)
            continue
        for key in REQUIRED_SECTIONS[section_name]:
            var expected: int = REQUIRED_SECTIONS[section_name][key]
            if typeof(section.get(key)) != expected:
                problems.append("%s.%s: expected %s, got %s" % [section_name, key,
                    type_string(expected), type_string(typeof(section.get(key)))])
    return problems
```

The loader calls it between checksum and migration output ([§10.5](#10-atomic-writes-backups-and-corruption-detection)): an empty problems array proceeds; a non-empty one logs every line and moves to the next recovery candidate. Two design notes: expected types say `TYPE_FLOAT` for numeric fields because that is what JSON parsing *produces* (the `int()` normalization happens later, in `from_dict`); and the validator reports **all** problems, not just the first — a support log listing five type mismatches at once usually spells "hand-edited file" instantly, where five successive single-error reports would spell five support round-trips.

> ✅ **Best practice** — Keep catalogs (`res://data/*.json`) and user state (`user://save_data.json`) **referencing, not embedding**: the save stores `{"item_id": 12}`, never the item's name, price or sprite path. Duplication would make every catalog balance change a save-migration problem. The ID is the contract; look the rest up in the catalog at load time, and treat "unknown item_id" as a soft error (drop it, log it) so removing a catalog item never bricks old saves.

### 7.5 JSON Lines — append-only logs

One JSON *document* per file suits snapshots; **JSON Lines (JSONL)** — one compact JSON object per line — suits append-only streams: session logs, analytics events, the `AppLogger` output referenced throughout this module. Each line is independently parseable, so a truncated final line (crash mid-append) costs exactly one record, not the file.

Godot's `FileAccess` has **no append mode** — the idiom is open `READ_WRITE` (which does not truncate) and seek to the end:

```gdscript
# app_logger.gd (core) - JSONL with size-based rotation
const LOG_DIR := "user://logs"
const MAX_LOG_BYTES := 1_000_000
const MAX_LOG_FILES := 5

func _append_line(entry: Dictionary) -> void:
    DirAccess.make_dir_recursive_absolute(LOG_DIR)
    var path := LOG_DIR.path_join("app_%s.jsonl" % Time.get_date_string_from_system())
    var f: FileAccess
    if FileAccess.file_exists(path):
        f = FileAccess.open(path, FileAccess.READ_WRITE)   # no truncation
        if f != null:
            f.seek_end()                                    # append position
    else:
        f = FileAccess.open(path, FileAccess.WRITE)
    if f == null:
        return          # logging must NEVER crash the app - drop the line
    f.store_line(JSON.stringify(entry))                     # compact: no indent
    var oversize := f.get_length() > MAX_LOG_BYTES
    f.close()
    if oversize:
        _rotate(path)

func info(category: String, message: String) -> void:
    _append_line({
        "t": Time.get_datetime_string_from_system(),
        "lvl": "info", "cat": category, "msg": message,
    })
```

Reading a JSONL file is a per-line loop with per-line error tolerance — skip unparseable lines instead of aborting, which is the entire point of the format:

```gdscript
func read_log(path: String) -> Array[Dictionary]:
    var out: Array[Dictionary] = []
    var f := FileAccess.open(path, FileAccess.READ)
    if f == null:
        return out
    while not f.eof_reached():
        var line := f.get_line().strip_edges()
        if line.is_empty():
            continue
        var entry: Variant = JSON.parse_string(line)
        if typeof(entry) == TYPE_DICTIONARY:
            out.append(entry)          # bad lines are silently skipped by design
    return out
```

Note that the *save file* stays a single pretty-printed document: it is a snapshot with a checksum, not a stream. Use each shape for what it is good at.

---

## 8. Binary and Resource saves — fidelity vs security

Two more save strategies complete the format landscape: raw Variant binary via `store_var`, and Godot's own `Resource` system via `ResourceSaver`/`ResourceLoader`. Both offer perfect type fidelity. One of them can execute arbitrary code from a save file — this section is blunt about which, why, and what to do instead.

### 8.1 store_var saves — full fidelity, opaque bytes

A binary save is a one-liner per direction, and every non-Object Variant round-trips exactly — `int` stays `int`, `Vector2` stays `Vector2`, typed packed arrays keep their element types:

```gdscript
const BIN_SAVE := "user://save_data.bin"

func save_binary(state: Dictionary) -> Error:
    var f := FileAccess.open(BIN_SAVE, FileAccess.WRITE)
    if f == null:
        return FileAccess.get_open_error()
    f.store_var(state)          # full_objects stays false - ALWAYS, for saves
    f.close()
    return OK

func load_binary() -> Dictionary:
    var f := FileAccess.open(BIN_SAVE, FileAccess.READ)
    if f == null:
        return {}
    var v: Variant = f.get_var()   # allow_objects stays false - ALWAYS, for saves
    f.close()
    return v if typeof(v) == TYPE_DICTIONARY else {}
```

Strengths: no serialization conventions to design, no type-loss table to memorize, compact output, fast. Weaknesses that keep it out of the primary slot in this course's architecture:

- **Opacity.** You cannot eyeball a broken save, diff two saves, or hand a user instructions to fix one field. Debugging binary saves means writing tooling.
- **Versioning is riskier.** The format has no self-describing schema you can inspect before parsing; your migration code operates on the deserialized Dictionary, so gross structural changes are harder to detect early. (The envelope pattern of [§7.4](#7-json-saves--serialization-strategies) still applies: store `{"version": N, "data": …}` and migrate the Dictionary — versioning is *possible*, just less inspectable.)
- **Engine coupling.** The Variant binary format is Godot's; no external tool, server or script can read it without Godot.

The related helpers `var_to_bytes()` / `bytes_to_var()` produce the same encoding as a `PackedByteArray` in memory — useful for putting Variant blobs into SQLite BLOB columns or network messages. Their `*_with_objects` variants carry the same danger as `store_var(data, true)`:

> ⚠️ **Pitfall** — `get_var(true)`, `bytes_to_var_with_objects()` and `str_to_var` applied to Object-bearing text share one failure mode: **a serialized Object can carry a script, and deserializing it can run that script.** The engine documentation warns verbatim that deserialized objects "can contain code which gets executed" and must not be used with data from untrusted sources. A save file is untrusted the moment it leaves your process — users edit them, mod communities share them, cloud sync moves them between machines. For save data, the object-enabled forms are never worth it: model your state as plain data (Dictionaries, Arrays, scalars, engine value types) and keep the flags `false`.

### 8.2 Resource saves — the convenient trap

Godot can persist any `Resource` subclass with one call, and it looks like the perfect save system:

```gdscript
# save_game_resource.gd
class_name SaveGameResource
extends Resource

@export var version: int = 1
@export var coins: int = 0
@export var decorations: Array[Dictionary] = []
```

```gdscript
# Saving - text (.tres, debuggable) or binary (.res, compact):
var sg := SaveGameResource.new()
sg.coins = 250
var err := ResourceSaver.save(sg, "user://save.tres")   # Godot 4: resource first, then path

# Loading:
var loaded := ResourceLoader.load("user://save.tres") as SaveGameResource
if loaded != null:
    print(loaded.coins)
```

The appeal is real: `@export` fields serialize automatically, the editor inspector can open your saves, sub-resources nest, and type fidelity is total. For **authored content** — item definition resources, theme presets, anything created by you and shipped read-only inside the PCK — this is exactly the right tool, and the editor pipeline (inspector editing, resource pickers, `preload`) is built around it.

**For user save files it is a security hole.**

### 8.3 Why loading untrusted .tres/.res can execute code

A `.tres` file is not inert data. It is a description of engine objects to instantiate, and it can:

1. **Reference an external script** — `[ext_resource type="Script" path="res://anything.gd"]` — attaching any script in your project to the loaded object, or
2. **Embed a script inline** — a `[sub_resource type="GDScript"]` block whose `script/source` property contains full GDScript source. On load, that script is compiled and attached; its static initializers and `_init()` run when the object is instantiated during resource loading.

So "loading a save file" becomes "compiling and running whatever GDScript the file author chose to embed" — file deletion, data exfiltration, downloading payloads: anything your app's OS privileges allow. This is not theoretical; it is a well-known, demonstrated attack pattern against Godot games that load shared saves or mods as Resources, and the same class of issue as `get_var(true)` above. The engine does not sandbox loaded scripts, and **no `ResourceLoader` option disables script execution** — `CACHE_MODE_IGNORE` and friends control *caching*, not safety, and type hints or `as SaveGameResource` casts run *after* the resource (and any embedded script) has already been instantiated.

Threat-model the decision honestly:

| Scenario | Risk of Resource saves |
|---|---|
| Save never leaves the machine, user is trusted | low — but users still share saves on forums without asking you |
| Saves shared between users / cloud-synced / modding community exists | **high — assume exploitation** |
| Authored `.tres` shipped read-only in the PCK | none — you wrote it; this is the intended use |

Mitigations, in order of preference:

1. **Don't use Resource formats for user save data.** Serialize to JSON, ConfigFile, `store_var(false)` or SQLite — all inert. This is the Relax Room policy and the course recommendation: convenience lost is small once you have the `to_dict` convention of [§7.3](#7-json-saves--serialization-strategies).
2. If you must load third-party Resource files (a mod system), **treat it as executing third-party code**, because it is: isolate what mods can be, review/curate submissions, and say so in your security notes. Static "validation" by scanning the text for `sub_resource type="GDScript"` is brittle (binary `.res`, nested resources, `ext_resource` indirection) — do not present it to yourself as a security boundary.
3. Never accept `.tres`/`.res` through *any* untrusted channel into `ResourceLoader.load()` — including paths derived from user input pointing inside `user://`.

> ✅ **Best practice** — One sentence to remember in code review: **ResourceSaver is for content you author; it is not for state your users produce.** If a PR loads a Resource from `user://` or from a download, that is a security finding, not a style nit.

---

## 9. SaveManager architecture

Everything so far was mechanism. This section is policy: *who* saves, *when*, *what*, and how the pieces stay decoupled. The design shown is Relax Room's `SaveManager` autoload, generalized so you can lift it into any project.

### 9.1 Responsibilities and boundaries

```
                 gameplay systems (decoration, character, music, shop)
                        │            ▲
        state changes   │            │  loaded state (typed objects)
        via SignalBus   ▼            │
                 ┌──────────────────────────┐
                 │        SaveManager        │   autoload
                 │  - owns the save document │
                 │  - dirty flag + autosave  │
                 │  - slots / paths          │
                 │  - atomic write (§10)     │
                 │  - migrations (§11)       │
                 └──────┬───────────┬────────┘
                        │           │
                 JSON session   SignalBus.save_committed
                 file (user://)      │
                                     ▼
                            LocalDatabase autoload
                            (SQLite mirror, §12-16)
```

Boundaries that keep this maintainable:

- **Gameplay never touches disk.** Systems mutate in-memory state and announce it on the `SignalBus` (`decoration_placed`, `coins_changed`, `track_changed`, …). Only `SaveManager` performs file I/O for game state; only `Settings` ([§6](#6-configfile--the-settings-recipe)) touches `settings.cfg`; only `LocalDatabase` speaks SQL.
- **SaveManager subscribes, gameplay stays ignorant.** Adding a new persistent system means one new signal connection in `SaveManager`, zero changes in gameplay code.
- **The save document is composed, not accumulated.** At save time, `SaveManager` asks each system for a fresh `to_dict()` snapshot rather than patching a long-lived dictionary — eliminating the "stale sub-document" class of bugs.

### 9.2 Dirty flag + autosave timer

Writing on every change is wasteful (a decoration drag emits dozens of updates per second) and risky (more writes = more chances to be mid-write at crash time). The classic answer is a **dirty flag** drained by a timer:

```gdscript
# save_manager.gd - autoload "SaveManager" (core loop; write path in §10)
extends Node

const AUTOSAVE_SECONDS := 60.0

var _dirty := false
var _autosave_timer: Timer

func _ready() -> void:
    _autosave_timer = Timer.new()
    _autosave_timer.wait_time = AUTOSAVE_SECONDS
    _autosave_timer.one_shot = false
    _autosave_timer.timeout.connect(_on_autosave_tick)
    add_child(_autosave_timer)
    _autosave_timer.start()

    # Every state-changing signal funnels into mark_dirty:
    SignalBus.decoration_placed.connect(func(_id, _pos) -> void: mark_dirty())
    SignalBus.decoration_removed.connect(func(_id) -> void: mark_dirty())
    SignalBus.coins_changed.connect(func(_amount) -> void: mark_dirty())
    SignalBus.character_customized.connect(func() -> void: mark_dirty())
    SignalBus.track_changed.connect(func(_idx) -> void: mark_dirty())

func mark_dirty() -> void:
    _dirty = true

func _on_autosave_tick() -> void:
    if _dirty:
        save_game()          # §10 - atomic write path

func save_game() -> void:
    var document := _compose_document()      # envelope + to_dict() snapshots (§7.4)
    var result := _write_atomically(document)  # §10
    if result.ok:
        _dirty = false
        SignalBus.save_committed.emit(document)   # LocalDatabase mirrors from this (§16)
    # on failure _dirty stays true - the next tick retries automatically
```

Beyond the timer, three moments force an immediate save regardless of the flag:

```gdscript
func _notification(what: int) -> void:
    if what == NOTIFICATION_WM_CLOSE_REQUEST:      # user closes the window
        if _dirty:
            save_game()
    elif what == NOTIFICATION_APPLICATION_FOCUS_OUT:  # alt-tab: cheap insurance
        if _dirty:
            save_game()

# ...and explicit checkpoints from gameplay: purchases, account changes -
# anything the user would be angry to lose:
func checkpoint() -> void:
    if _dirty:
        save_game()
```

Note the retry-by-design: a failed save leaves `_dirty = true`, so the system self-heals on the next tick instead of needing bespoke retry logic. Pair it with a user-visible warning if failures persist (disk full is the common cause).

> ⚠️ **Pitfall** — Handling `NOTIFICATION_WM_CLOSE_REQUEST` is not bulletproof: it never fires on a crash, a `kill -9`, or a power cut, and on a normal quit your handler races the OS teardown if it starts *asynchronous* work. Keep the close-time save synchronous and small, and treat autosave — not quit-save — as the primary data-loss defense. If you set `get_tree().set_auto_accept_quit(false)` to control shutdown ordering yourself, you **must** call `get_tree().quit()` afterward, or the app becomes unclosable.

### 9.3 Save slots

A desktop companion usually has one implicit slot, but the slot mechanism costs little and pays for itself the first time QA asks to "try a fresh profile without deleting mine". Slots are directories, not filename suffixes — everything belonging to a profile (save, backups, screenshots) stays together and can be deleted or exported as a unit:

```gdscript
const SLOTS_ROOT := "user://slots"

var current_slot: int = 0

func slot_dir(slot: int) -> String:
    return "%s/slot_%02d" % [SLOTS_ROOT, slot]

func save_path(slot: int) -> String:
    return slot_dir(slot).path_join("save_data.json")

func ensure_slot(slot: int) -> Error:
    return DirAccess.make_dir_recursive_absolute(slot_dir(slot))

func list_slots() -> Array[Dictionary]:
    var out: Array[Dictionary] = []
    var dir := DirAccess.open(SLOTS_ROOT)
    if dir == null:
        return out
    for name in dir.get_directories():
        var meta_path := SLOTS_ROOT.path_join(name).path_join("save_data.json")
        if not FileAccess.file_exists(meta_path):
            continue
        # Read ONLY the envelope for the slot picker - cheap, no full migration:
        var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(meta_path))
        if typeof(doc) == TYPE_DICTIONARY:
            out.append({
                "slot": name,
                "saved_at": doc.get("saved_at", "?"),
                "version": int(doc.get("version", 0)),
                "display_name": doc.get("data", {}).get("account", {}).get("display_name", ""),
            })
    return out
```

The slot picker reads envelope metadata only — never run migrations or build gameplay state just to render a menu list. Full loading (with validation, checksum and migrations) happens once, when a slot is actually opened.

### 9.4 Autoload order — who may depend on whom

Autoload initialization order is declaration order in `project.godot`, and persistence autoloads are order-sensitive: you cannot mirror to a database that has not opened, or compose a save before knowing which account is active. Relax Room's order, with each entry depending only on entries above it:

| # | Autoload | Depends on | Persistence role |
|---|---|---|---|
| 1 | `SignalBus` | — | signal hub (31 signals: auth, save, room, audio, …) |
| 2 | `AppLogger` | — | JSONL logs in `user://logs/` with rotation |
| 3 | `Settings` | — | `settings.cfg` via ConfigFile ([§6](#6-configfile--the-settings-recipe)) |
| 4 | `LocalDatabase` | SignalBus | SQLite: schema, migrations, CRUD, sync queue ([§12-15](#12-sqlite-with-godot-sqlite--setup-and-core-api)) |
| 5 | `AuthManager` | LocalDatabase | local accounts: guest/login/register ([§17](#17-authentication-for-offline-apps)) |
| 6 | `GameManager` | SignalBus, AuthManager | `res://` catalogs, live game state |
| 7 | `SaveManager` | SignalBus, AuthManager, GameManager | JSON save, autosave, migrations |
| 8 | `AudioManager` | SignalBus, SaveManager | music state restored from save |

See [Autoload Safety](AUTOLOAD_SAFETY.md) for the general rules (no cyclic dependencies, `_ready` ordering, teardown); the persistence-specific addition is the **teardown mirror**: shutdown flushes in reverse order — `SaveManager` writes, then `LocalDatabase` closes the SQLite connection in its own `NOTIFICATION_WM_CLOSE_REQUEST` handler, which runs after `SaveManager`'s because notification order follows the scene tree.

### 9.5 Keeping saves off the frame

An autosave that hitches the app for 80 ms is felt immediately in a companion window playing music. Order the defenses by cost:

1. **Measure first.** A ≤100 KB JSON save — Relax Room's reality — costs well under a millisecond to stringify and single-digit milliseconds to write on any SSD. At that size, synchronous saving on the autosave tick is *correct*, and threading would be complexity without benefit.
2. **Split compose from write.** `_compose_document()` (pure CPU, main thread — it must read live state safely) and `_write_atomically()` (pure I/O, no game-state access) are already separate functions in this architecture. That separation is exactly what makes step 3 safe when you need it.
3. **Offload the I/O only.** Hand the *snapshot* — already composed, owned by nobody else — to a background task:

```gdscript
var _save_in_flight := false

func save_game_async() -> void:
    if _save_in_flight:
        mark_dirty()            # coalesce: current write finishes, next tick catches up
        return
    _save_in_flight = true
    var document := _compose_document()          # main thread: touches game state
    WorkerThreadPool.add_task(func() -> void:
        var result := _write_atomically(document)  # worker: touches ONLY the snapshot
        # Back to the main thread for state + signals:
        _on_async_save_done.call_deferred(result))

func _on_async_save_done(result: SaveResult) -> void:
    _save_in_flight = false
    if result.ok:
        _dirty = false
        SignalBus.save_committed.emit(result.data if result.data else {})
```

The three thread rules encoded here: the worker touches only data it exclusively owns (the snapshot Dictionary); results and signals re-enter the main thread via `call_deferred` (signal emission from worker threads is not safe in general); and a single in-flight flag serializes writes so two workers can never interleave temp-file renames. Keep the **quit-time** save synchronous regardless — a worker thread racing process teardown is how "saved on exit" becomes "usually saved on exit". And keep SQLite on the main thread: the `LocalDatabase` connection is not shared across threads in this architecture, which costs nothing because the mirror write is already downstream of `save_committed`.

---

## 10. Atomic writes, backups and corruption detection

This section is the heart of "never lose data". The enemy is the **partial write**: the process dies (crash, power cut, OS kill) while the save file is half-written, leaving bytes that parse as garbage — or worse, parse successfully into wrong state.

### 10.1 Why naive writing corrupts

```
Naive save:  FileAccess.open(SAVE_PATH, FileAccess.WRITE)   ← truncates to 0 bytes!
             store_string(json)                              ← writing...
             close()

Crash timeline:
  T0  open(WRITE)      → the ONLY copy of the save is now 0 bytes
  T1  store_string     → 50% of the bytes are on disk
  T2  ☠ CRASH          → file is truncated garbage; the user's data is GONE
```

The window is small, but autosave runs every minute for hours, on thousands of machines. Small windows multiplied by big exposure equal support tickets with the word "everything" in them.

### 10.2 The atomic write pattern — temp file + rename

Write the *new* file completely, next to the destination; only when it is safely on disk, atomically **rename** it over the old one. `DirAccess.rename_absolute()` maps to the OS rename/move-with-replace primitive, which on every desktop OS replaces the destination in effectively one step *when source and destination are on the same volume* — which is why the temp file lives in `user://`, never in a system temp directory that may be a different drive.

```gdscript
const SAVE_PATH   := "user://save_data.json"
const TEMP_PATH   := "user://save_data.json.tmp"
const BACKUP_PATH := "user://save_data.backup.json"

func _write_atomically(document: Dictionary) -> SaveResult:
    var json_string := JSON.stringify(document, "\t")

    # 1) Write the COMPLETE new save to a temp file.
    var file := FileAccess.open(TEMP_PATH, FileAccess.WRITE)
    if file == null:
        return SaveResult.failure(FileAccess.get_open_error(), "Cannot open temp save")
    file.store_string(json_string)
    file.flush()
    var write_err := file.get_error()
    file.close()
    if write_err != OK:
        DirAccess.remove_absolute(TEMP_PATH)
        return SaveResult.failure(write_err, "Write to temp save failed (disk full?)")

    # 2) Verify the temp file parses before promoting it (cheap paranoia).
    if JSON.parse_string(FileAccess.get_file_as_string(TEMP_PATH)) == null:
        DirAccess.remove_absolute(TEMP_PATH)
        return SaveResult.failure(ERR_FILE_CORRUPT, "Temp save failed verification")

    # 3) Demote the current save to backup (copy, so SAVE_PATH never vanishes).
    if FileAccess.file_exists(SAVE_PATH):
        var copy_err := DirAccess.copy_absolute(SAVE_PATH, BACKUP_PATH)
        if copy_err != OK:
            push_warning("Backup copy failed: %s - continuing" % error_string(copy_err))

    # 4) Atomically promote temp → primary. THE critical step.
    var ren := DirAccess.rename_absolute(TEMP_PATH, SAVE_PATH)
    if ren != OK:
        return SaveResult.failure(ren, "Rename temp→primary failed")

    return SaveResult.success()
```

Crash-safety audit of every instant:

| Crash during… | State on disk | Next launch loads |
|---|---|---|
| step 1 (temp writing) | primary intact, temp partial | primary — temp is ignored/overwritten |
| step 2 (verification) | primary intact, temp complete | primary |
| step 3 (backup copy) | primary intact, temp complete | primary |
| step 4 (rename) | either old primary or new primary — rename is atomic | whichever is there; both valid |

At no instant is the *only* copy of the data incomplete. That property — not any amount of testing — is what makes the pattern trustworthy.

> ⚠️ **Pitfall** — Do not "optimize" step 3 into a rename (`SAVE_PATH → BACKUP_PATH`, then `TEMP → SAVE_PATH`). Between the two renames there is a moment where `SAVE_PATH` does not exist; a crash there leaves no primary file, and your loader must then know to look for the backup. The copy-based version is a few milliseconds slower and strictly safer. Also resist `OS.move_to_trash()` here — it is for user-initiated deletions, not the hot save path.

### 10.3 Backup rotation

The single `.backup.json` protects against a corrupted *write*. It does not protect against corrupted *state* — a bug that writes valid-JSON-but-wrong data will happily propagate into the backup on the next save. Dated rotation adds a time dimension:

```gdscript
const BACKUP_DIR := "user://backups"
const MAX_ROTATED_BACKUPS := 7      # one per day, one week of history

func rotate_backup() -> void:
    if not FileAccess.file_exists(SAVE_PATH):
        return
    DirAccess.make_dir_recursive_absolute(BACKUP_DIR)

    var stamp := Time.get_date_string_from_system()        # "2026-07-27"
    var target := BACKUP_DIR.path_join("save_data.%s.json" % stamp)
    if FileAccess.file_exists(target):
        return                                             # one per day is enough
    DirAccess.copy_absolute(SAVE_PATH, target)

    # Prune oldest beyond the cap - names sort chronologically by construction.
    var dir := DirAccess.open(BACKUP_DIR)
    if dir == null:
        return
    var names := Array(dir.get_files())
    names.sort()
    while names.size() > MAX_ROTATED_BACKUPS:
        DirAccess.remove_absolute(BACKUP_DIR.path_join(names.pop_front()))
```

Call `rotate_backup()` once per session (first successful save after launch). Combined with the per-write backup, the recovery ladder becomes: primary → `.backup.json` → newest dated backup → … → fresh state, each rung attempted by the loader below.

### 10.4 Corruption detection — checksums

Parsing success is a weak health check: a truncated JSON file fails to parse (good, detectable), but a bit-flipped or hand-mangled one may parse into subtly wrong state. A checksum over the payload makes tampering and rot detectable *before* any state is built:

```gdscript
func _checksummed_envelope(data: Dictionary) -> Dictionary:
    # sort_keys=true (default) keeps stringify deterministic → stable checksum.
    var payload := JSON.stringify(data)
    return {
        "version": SAVE_VERSION,
        "saved_at": Time.get_datetime_string_from_system(),
        "app_version": ProjectSettings.get_setting("application/config/version", "dev"),
        "checksum": payload.sha256_text(),
        "data": data,
    }

func _verify_checksum(doc: Dictionary) -> bool:
    if not doc.has("checksum") or not doc.has("data"):
        return false
    var expected: String = doc["checksum"]
    var actual := JSON.stringify(doc["data"]).sha256_text()
    return actual == expected
```

Honest framing: SHA-256 here is an **integrity** check, not a **security** boundary — anyone editing the save can recompute the checksum (your app contains the algorithm). It reliably catches accidental corruption and lazy tampering, which is exactly its job. If you *want* tamper evidence against casual cheating, an HMAC with an in-binary key (`Crypto.hmac_digest`) raises the bar slightly; a determined user still extracts the key. Decide what you are defending against and document it — for Relax Room (single-player, cosmetic economy) the plain checksum is the right call.

### 10.5 The self-healing loader

```gdscript
func load_game() -> Dictionary:
    var candidates: Array[String] = [SAVE_PATH, BACKUP_PATH]
    for f in _list_rotated_backups_newest_first():
        candidates.append(f)

    for path in candidates:
        var result := read_json_file(path)        # §4.2 - typed result, logs internally
        if not result.ok:
            continue
        var doc: Dictionary = result.data
        if not _verify_checksum(doc):
            AppLogger.warn("save", "Checksum mismatch in %s - trying next candidate" % path)
            continue
        if path != SAVE_PATH:
            AppLogger.warn("save", "Recovered from %s" % path)
            SignalBus.save_recovered_from_backup.emit(path)
        return migrate(doc)                       # §11 - version pipeline

    AppLogger.warn("save", "No usable save found - starting fresh")
    return _default_document()
```

The user-facing rule: recovery is **loud in logs, quiet in UI**. A small "restored from backup (yesterday 18:42)" toast is helpful; a modal error dialog about checksums is not. And starting fresh is the *last* rung, never the response to the first parse error — that mistake (fresh-on-any-error) has erased more real-world save data than corruption itself.

### 10.6 Atomicity beyond one file

The temp-plus-rename pattern is per-file. Two adjacent cases need one extra idea each:

**Binary and compressed saves** use the identical pattern — nothing in [§10.2](#10-atomic-writes-backups-and-corruption-detection) assumed JSON. The only adjustment is step 2's verification: for a `store_var` save, "parses" becomes "`get_var()` returns the expected type"; for a compressed save, a successful `open_compressed` + read *is* the integrity check (the codec detects truncation).

**Multi-file saves** (a slot directory with `save_data.json` plus screenshots plus auxiliary files) cannot rely on directory renames — cross-platform, renaming a non-empty directory over another is not atomic and may simply fail. The robust pattern is a **manifest written last**:

```
slot_03/
  save_data.json        ← written atomically (its own temp+rename)
  thumbnail.png         ← written atomically
  MANIFEST.json         ← written LAST, atomically:
                          { "files": {"save_data.json": "<sha256>",
                                      "thumbnail.png": "<sha256>"},
                            "committed_at": "2026-07-27T18:42:11" }
```

The loader trusts a slot only if the manifest exists and every listed hash matches (`FileAccess.get_sha256`, [§3.5](#3-fileaccess--complete-api-tour)). A crash anywhere mid-update leaves either the old manifest (old slot state remains valid — new files are ignored as uncommitted) or no new manifest yet (same). The manifest's own write is one file — which the temp-plus-rename pattern already makes atomic. This is, at small scale, exactly how databases commit: data first, then a single atomic commit record. Relax Room does not need it (single-file save), but the first feature that adds a sidecar file — an exported room screenshot in the save slot — will.

---

## 11. Save versioning and migration pipelines

Your save format **will** change: new features add fields, refactors rename them, balance passes restructure whole sections. Users do not reinstall on your schedule — a file written by version 1 will meet code from version 9. Migrations are how that meeting goes well.

### 11.1 Rules of the game

1. **Every save carries an integer `version`** ([§7.4](#7-json-saves--serialization-strategies)). Bump it on *every* format change, however small.
2. **Migrations are incremental**: v1→v2, v2→v3, … chained. Never write v1→v5 jumps — the combinatorics explode and old paths rot untested.
3. **Migration code is append-only.** The v1→v2 function outlives v2 by years, because some user somewhere still has a v1 file. Deleting old migrations is deleting users' data with extra steps.
4. **Each step is a pure function** `Dictionary → Dictionary`: no I/O, no globals, no side effects. Purity is what makes steps unit-testable with fixture files ([§19](#19-testing-persistence)).
5. **New fields get sensible defaults** — the same defaults `from_dict` uses, sourced from one place.
6. **Migrated saves are written back immediately** after a successful load, so each file is migrated once, not on every launch.
7. **Files from the future** (version > current: user opened the save with a newer build, then downgraded) load best-effort with a warning — never delete or "fix" them downward.

### 11.2 The Relax Room migration history

The real chain from the project, one entry per shipped format change:

| Version | Shipped | Change |
|---|---|---|
| v1 | first release | account + room + character sections |
| v2 | music update | added `music` section (playlist, track, position) |
| v3 | shop update | added `inventory` section (capacity, items) |
| v4 | cleanup | **removed** obsolete fields `tools`, `therapeutic`, `xp`; renamed `char` → `character` |
| v5 | accounts update | added `account.auth_uid`, `account.created_at`; coins moved from root into `account` |

### 11.3 The pipeline — worked code

```gdscript
# save_migrations.gd - static, pure, append-only
class_name SaveMigrations

const CURRENT_VERSION := 5

## Entry point: takes any envelope, returns a CURRENT_VERSION envelope.
static func migrate(doc: Dictionary) -> Dictionary:
    var version := int(doc.get("version", 1))       # pre-versioning files count as v1

    if version > CURRENT_VERSION:
        push_warning("Save from the future (v%d > v%d) - loading best-effort" %
            [version, CURRENT_VERSION])
        return doc

    while version < CURRENT_VERSION:
        match version:
            1: doc = _v1_to_v2(doc)
            2: doc = _v2_to_v3(doc)
            3: doc = _v3_to_v4(doc)
            4: doc = _v4_to_v5(doc)
            _:
                push_error("No migration from v%d - keeping as-is" % version)
                return doc
        version = int(doc["version"])               # each step sets its own output version
    return doc

# --- v1 → v2: music section introduced ---
static func _v1_to_v2(doc: Dictionary) -> Dictionary:
    var data: Dictionary = doc.get("data", {})
    data["music"] = {
        "playlist": "lofi_default", "track_index": 0, "position_sec": 0.0,
    }
    doc["data"] = data
    doc["version"] = 2
    return doc

# --- v2 → v3: inventory section introduced ---
static func _v2_to_v3(doc: Dictionary) -> Dictionary:
    var data: Dictionary = doc.get("data", {})
    data["inventory"] = {"capacity": 50, "items": []}
    doc["data"] = data
    doc["version"] = 3
    return doc

# --- v3 → v4: drop dead fields, rename "char" → "character" ---
static func _v3_to_v4(doc: Dictionary) -> Dictionary:
    var data: Dictionary = doc.get("data", {})
    for dead in ["tools", "therapeutic", "xp"]:
        data.erase(dead)
    if data.has("char"):
        data["character"] = data["char"]
        data.erase("char")
    doc["data"] = data
    doc["version"] = 4
    return doc

# --- v4 → v5: account grows auth fields; coins move under account ---
static func _v4_to_v5(doc: Dictionary) -> Dictionary:
    var data: Dictionary = doc.get("data", {})
    var account: Dictionary = data.get("account", {})
    account["auth_uid"] = account.get("auth_uid", "local")
    account["created_at"] = account.get("created_at",
        Time.get_datetime_string_from_system())
    if data.has("coins"):                    # root-level coins → account.coins
        account["coins"] = int(data["coins"])
        data.erase("coins")
    account["coins"] = int(account.get("coins", 0))
    data["account"] = account
    doc["data"] = data
    doc["version"] = 5
    return doc
```

And the integration in the loader (after checksum, before `from_dict` construction):

```gdscript
func migrate(doc: Dictionary) -> Dictionary:
    var original_version := int(doc.get("version", 1))
    var migrated := SaveMigrations.migrate(doc)
    if int(migrated["version"]) != original_version:
        AppLogger.info("save", "Migrated save v%d → v%d" %
            [original_version, migrated["version"]])
        _write_atomically(migrated)          # persist once, immediately (§10.2)
    return migrated
```

> ⚠️ **Pitfall** — The checksum ([§10.4](#10-atomic-writes-backups-and-corruption-detection)) covers the *stored* `data`; migrations change `data` in memory. Verify the checksum against the file **as read**, run migrations, then recompute the checksum when writing the migrated document back. Verifying after migrating (or forgetting to recompute on write-back) makes every migrated save look corrupt on its second load — a bug that surfaces only in upgrade testing, which is exactly why [§19](#19-testing-persistence) keeps fixture files of every historical version.

> ✅ **Best practice** — Keep one **fixture save file per historical version** in the repo (`tests/fixtures/save_v1.json` … `save_v4.json`) plus a golden expected output. Your CI then proves, forever, that a day-one file still migrates cleanly to today's format. Write the v1 fixture *today* — you cannot regenerate it after the v1 writer is gone.

### 11.4 Forward compatibility — files from the future

Rule 7 ("load best-effort, never fix downward") deserves its mechanics spelled out, because downgrades genuinely happen: a beta build auto-updates, breaks, and the user rolls back — with their save already stamped v6 in a v5 world.

Three behaviors make the rollback survivable:

1. **Preserve unknown fields.** `from_dict` reads the keys it knows; the composing side must not *strip* the ones it doesn't. The cheapest implementation: when loading a future-versioned document, keep the original Dictionary around and merge your known-field updates into it at save time, so v6-only sections pass through v5 untouched. The alternative — compose-from-scratch, which [§9.1](#9-savemanager-architecture) rightly prefers for same-version operation — is what silently deletes the future data.
2. **Do not rewrite the version number.** A v6 file saved by a v5 app with `"version": 6` intact (plus preserved unknown fields) reopens perfectly after the user updates again. Stamping it v5 would trigger the v5→v6 migration on data that is already v6-shaped — the classic double-migration corruption.
3. **Warn once, visibly in logs, quietly in UI.** The user chose the rollback; your job is not to punish the choice but to leave the trail (`"loading v6 save with v5 build - best effort"`) that explains any oddities in the bug report that follows.

This is also the argument for **format freezes** near release: the last week before shipping is the wrong time for a casual field rename, because every beta tester's save becomes a migration test case you did not plan. Batch format changes early in a cycle; ship migrations with soak time.

---

## 12. SQLite with godot-sqlite — setup and core API

SQLite is an embedded relational database: a single file, no server, transactions with real ACID guarantees, and SQL. Godot has no built-in SQL support; the community-standard bridge is **godot-sqlite** by *2shady4u*, a GDExtension wrapping SQLite for Godot 4.x.

### 12.1 Installation

1. **AssetLib:** in the editor, AssetLib tab → search "godot-sqlite" → install. The plugin lands in `res://addons/godot-sqlite/` with prebuilt binaries per platform (`libgdsqlite.windows.x86_64.dll`, `.linux.x86_64.so`, `.macos.framework`, Android `.so`, iOS, and a WASM build with limitations).
2. **Manual:** download a release from the GitHub repository and copy the `addons/godot-sqlite` folder into your project.
3. Restart the editor. Because it is a GDExtension (not an editor plugin), there is nothing to enable in Project Settings — the `SQLite` class is available immediately in GDScript.
4. **Export:** verify the export template includes the `addons/godot-sqlite` folder and that you export for a platform with a shipped binary. Test the exported build early — a missing native library fails at runtime, not at export time.

Platform notes worth pinning: on **Android/iOS**, the database must live in `user://` (app-internal storage; sandboxed; removed on uninstall). On **Web**, support is limited and persistence semantics differ — for the desktop-companion scope of this course, treat SQLite as a desktop + mobile tool. A database shipped read-only inside the PCK (`res://`) works if you open it with `read_only = true`.

### 12.2 Opening a database

```gdscript
# local_database.gd - autoload "LocalDatabase" (skeleton; schema in §13)
extends Node

const DB_PATH := "user://relax_room.db"

var db: SQLite

func _ready() -> void:
    db = SQLite.new()
    db.path = DB_PATH
    db.foreign_keys = true            # enforce FK constraints (§13) - OFF by default in SQLite!
    db.verbosity_level = SQLite.NORMAL  # QUIET in release; VERBOSE while debugging

    if not db.open_db():
        push_error("DB open failed: " + db.error_message)
        SignalBus.database_unavailable.emit()
        return

    db.query("PRAGMA journal_mode = WAL;")   # §15.1
    _migrate_schema()                        # §15.3
    SignalBus.database_ready.emit()

func _notification(what: int) -> void:
    if what == NOTIFICATION_WM_CLOSE_REQUEST:
        if db != null:
            db.close_db()
```

API surface you will use constantly:

| Member | Purpose |
|---|---|
| `path: String` | database location; accepts `user://` and `res://` (a default `.db` extension is appended if none is given) |
| `foreign_keys: bool` | issues `PRAGMA foreign_keys = ON` at open — set it **before** `open_db()` |
| `read_only: bool` | open without write access (for `res://`-packed databases) |
| `verbosity_level: int` | `QUIET`/`NORMAL`/`VERBOSE`/`VERY_VERBOSE` console logging |
| `open_db() / close_db()` | connection lifecycle — open once at startup, close once at quit |
| `query(sql)` | execute one SQL string; returns `true`/`false` |
| `query_with_bindings(sql, params)` | execute with `?` placeholders bound from an Array — the **only** way user input touches SQL ([§14](#14-queries-bindings-and-transactions)) |
| `query_result: Array` | rows from the last SELECT, as an Array of Dictionaries (column name → value) |
| `error_message: String` | human-readable message from the last failed operation |
| `create_table(name, schema)` | convenience DDL from a Dictionary description |
| `insert_row / insert_rows / select_rows / update_rows / delete_rows` | convenience CRUD without hand-written SQL |
| `import_from_json / export_to_json` | whole-database JSON round-trip (handy for tests and debugging) |
| `backup_to(path) / restore_from(path)` | online backup via SQLite's backup API ([§15.4](#15-operating-sqlite--wal-pragmas-migrations-backups)) |

Connection discipline mirrors the original study notes and is worth restating as law: **open once in `_ready()`, close once at shutdown.** Opening per-query destroys performance (each open pays journal recovery, page-cache warmup, PRAGMA re-application) and defeats WAL.

```gdscript
# WRONG - do not open/close per operation
func get_data() -> Array:
    db.open_db()      # NO
    db.query("SELECT ...")
    db.close_db()     # NO
    return db.query_result
```

### 12.3 Reading results

```gdscript
db.query_with_bindings(
    "SELECT item_id, quantity FROM inventory WHERE account_id = ?;", [account_id])
for row in db.query_result:            # Array[Dictionary]
    var item_id: int = int(row["item_id"])
    var quantity: int = int(row["quantity"])
```

Two habits keep result handling robust: **cast every value** (SQLite is dynamically typed; INTEGER columns arrive as ints, but REAL/NULL and hand-edited databases can surprise you), and remember `query_result` is **replaced by the next query** — copy it (`var rows := db.query_result.duplicate()`) if you must query again while iterating. The plugin also exposes `query_result_by_reference` (no copy) for hot paths; prefer the value copy until profiling says otherwise.

> ⚠️ **Pitfall** — `SQLite.foreign_keys` matters more than it looks: in SQLite, foreign-key enforcement is **off by default** for historical reasons, and it is a per-connection setting. Forget it and every `REFERENCES ... ON DELETE CASCADE` in your schema silently does nothing: deleting an account leaves orphaned characters, rooms and inventory rows that resurface as ghosts after the next sync. Set `foreign_keys = true` before `open_db()`, and verify in tests with `PRAGMA foreign_keys;` (expect `1`).

### 12.4 Type mapping — GDScript ↔ SQLite

SQLite stores five storage classes; GDScript speaks Variants. The mapping is mostly obvious, and the three non-obvious rows cause all the bugs:

| GDScript | SQLite column | Notes |
|---|---|---|
| `int` | `INTEGER` | 64-bit both sides; round-trips exactly |
| `float` | `REAL` | 64-bit IEEE both sides |
| `String` | `TEXT` | UTF-8 both sides |
| `bool` | `INTEGER` (0/1) | **SQLite has no BOOL** — cast on read: `bool(row["muted"])` |
| `PackedByteArray` | `BLOB` | binary payloads (compressed JSON, images) |
| `null` | `NULL` | `row["col"]` is Godot `null`; guard before casting |
| `Vector2`, `Color`, … | — | **no engine types** — decompose to columns or JSON-encode ([§13.3](#13-schema-design--the-relax-room-database)) |
| timestamps | `TEXT` ISO-8601 UTC | `datetime('now')`; sorts and compares correctly as text |

The BLOB row enables a compact pattern for document-shaped payloads — the same `PackedByteArray.compress` trick from [§3.6](#3-fileaccess--complete-api-tour) feeding a bound parameter:

```gdscript
func store_room_snapshot(room_id: int, decorations: Array) -> bool:
    var raw := JSON.stringify(decorations).to_utf8_buffer()
    var packed := raw.compress(FileAccess.COMPRESSION_ZSTD)
    return execute("""
        UPDATE rooms SET decorations_blob = ?, decorations_raw_size = ?,
               updated_at = datetime('now')
        WHERE room_id = ?;""", [packed, raw.size(), room_id])
```

Relax Room keeps `decorations` as plain TEXT JSON instead — at its sizes, readability in a database browser beats the bytes saved. The BLOB variant earns its place when a document column crosses hundreds of kilobytes.

> ⚠️ **Pitfall** — SQLite's dynamic typing means a column *declared* `INTEGER` can still hold `'42'` (a TEXT value) if some code path binds a String — SQLite's type affinity converts when it can and stores the original type when it cannot. Symptoms surface far from the cause: comparisons that mysteriously fail, `ORDER BY` interleaving numbers and strings. Defense in two layers: always bind values with the intended Variant type (bind `int(x)`, not `str(x)`), and cast on every read ([§12.3](#12-sqlite-with-godot-sqlite--setup-and-core-api)). SQLite 3.37+ `STRICT` tables reject wrong-type writes outright — worth adopting if your bundled SQLite supports it.

---

## 13. Schema design — the Relax Room database

> **Case study.** This section documents the real Relax Room schema (9 tables). Naming note: the project's codebase is partly Italian — table `inventario` (inventory), lookup tables `categoria` (category) and `colore` (color) keep their original names here, matching the shipped code. The design generalizes: swap the names, keep the shapes.

### 13.1 Entity map

```
accounts (1) ──────< characters (1:1 today, 1:N ready)
    │                    │
    │                    └────< rooms (1:1 today)
    │
    └──────< inventario (1:N owned items)
                  │
                  └──> items >── shop      (FK: where it is sold)
                          │ └──> categoria (FK: item category)
                          └────> colore    (FK: color variant)

sync_queue   (stand-alone: offline operation log, §18)
schema_version (stand-alone: migration bookkeeping, §15.3)
```

Three groups with different lifecycles:

- **User state** (`accounts`, `characters`, `rooms`, `inventario`) — read-write, owned by the user, mirrored to the cloud when sync ships.
- **Catalog lookups** (`items`, `shop`, `categoria`, `colore`) — read-only at runtime, re-seeded from `res://` JSON catalogs at startup ([§16.2](#16-case-study--the-json--sqlite-hybrid)).
- **Infrastructure** (`sync_queue`, `schema_version`) — the app's own bookkeeping.

### 13.2 DDL — the nine tables

```sql
-- ============ user state ============
CREATE TABLE IF NOT EXISTS accounts (
    account_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    auth_uid      TEXT NOT NULL UNIQUE,          -- "local", "user_<name>", or Supabase UUID
    display_name  TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL DEFAULT '',      -- empty for guest accounts (§17)
    password_salt TEXT NOT NULL DEFAULT '',      -- per-user salt, hex (§17.3)
    coins         INTEGER NOT NULL DEFAULT 0 CHECK (coins >= 0),
    inv_capacity  INTEGER NOT NULL DEFAULT 50,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS characters (
    character_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id    INTEGER NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    name          TEXT NOT NULL DEFAULT '',
    gender        INTEGER NOT NULL DEFAULT 1,
    eye_color     INTEGER NOT NULL DEFAULT 0,
    hair_color    INTEGER NOT NULL DEFAULT 0,
    skin_color    INTEGER NOT NULL DEFAULT 0,
    stress_level  INTEGER NOT NULL DEFAULT 0 CHECK (stress_level BETWEEN 0 AND 100),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rooms (
    room_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id  INTEGER NOT NULL REFERENCES characters(character_id) ON DELETE CASCADE,
    room_type     TEXT NOT NULL DEFAULT 'cozy_studio',
    theme         TEXT NOT NULL DEFAULT 'modern',
    decorations   TEXT NOT NULL DEFAULT '[]',    -- JSON array (see 13.3)
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS inventario (
    inv_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id    INTEGER NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    item_id       INTEGER NOT NULL REFERENCES items(item_id),
    quantity      INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    acquired_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (account_id, item_id)                 -- stacking: one row per item type
);

-- ============ catalog lookups (seeded from res:// JSON) ============
CREATE TABLE IF NOT EXISTS categoria (
    categoria_id  INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS colore (
    colore_id     INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    hex           TEXT NOT NULL DEFAULT '#FFFFFF'
);

CREATE TABLE IF NOT EXISTS shop (
    shop_id       INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS items (
    item_id       INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    price         INTEGER NOT NULL DEFAULT 0 CHECK (price >= 0),
    shop_id       INTEGER REFERENCES shop(shop_id),
    categoria_id  INTEGER REFERENCES categoria(categoria_id),
    colore_id     INTEGER REFERENCES colore(colore_id),
    sprite_path   TEXT NOT NULL DEFAULT ''
);

-- ============ infrastructure ============
CREATE TABLE IF NOT EXISTS sync_queue (
    queue_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name    TEXT NOT NULL,
    operation     TEXT NOT NULL CHECK (operation IN ('upsert', 'delete')),
    payload       TEXT NOT NULL,                 -- JSON of the row (§18.2)
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    retry_count   INTEGER NOT NULL DEFAULT 0
);
-- schema_version is created by the migration runner itself (§15.3)
```

### 13.3 Design decisions worth stealing

**`auth_uid` as the stable identity.** The local integer `account_id` is meaningless outside this database file; `auth_uid` is the portable identity ("local" for the default guest, `user_<name>` for local registered accounts, a Supabase UUID after cloud linking, [§17-18](#17-authentication-for-offline-apps)). Every future sync payload keys on `auth_uid`, never on autoincrement IDs — autoincrements collide across devices.

**`decorations` as a JSON column.** Heresy? Deliberate trade-off. Placed decorations are a *document*: loaded and saved as one unit with the room, never queried individually ("find all rooms containing lamp #12" is not a feature). Normalizing them into a `placed_decorations` table would add JOIN complexity and migration surface for zero query benefit. The rule: **normalize what you query, document what you load whole.** If per-decoration queries ever become a feature, that is a schema migration ([§15.3](#15-operating-sqlite--wal-pragmas-migrations-backups)) — and SQLite's `json_each()` can bridge the gap meanwhile.

**`CHECK` constraints as the last line of defense.** `coins >= 0`, `quantity > 0`, `stress_level BETWEEN 0 AND 100`: the UI should prevent these, gameplay code should prevent these, and when both fail (they will), the database refuses the write instead of persisting impossible state. A failed `CHECK` in your logs is a gameplay bug report with a stack trace attached.

**`UNIQUE (account_id, item_id)`** turns "add item" into a natural upsert target ([§14.3](#14-queries-bindings-and-transactions)) and makes duplicate-row bugs structurally impossible instead of qa-detectable.

**Timestamps are TEXT in UTC** (`datetime('now')` is UTC by default). SQLite has no native datetime type; ISO-8601 strings sort correctly, read correctly in any tool, compare correctly against Supabase's `timestamptz` after normalization, and dodge every timezone bug except the ones you write yourself. Store UTC, convert to local time only for display.

**CASCADE topology.** `accounts → characters → rooms` and `accounts → inventario` cascade on delete, so account deletion ([§17.5](#17-authentication-for-offline-apps)) is one statement with no orphan sweep. Catalog references (`items` from `inventario`) deliberately do **not** cascade — deleting a catalog item must fail loudly if a user owns it, not silently vaporize a purchase.

> ✅ **Best practice** — The godot-sqlite `create_table()` convenience (Dictionary schema: `{"data_type": "int", "primary_key": true, "not_null": true, "auto_increment": true, "default": …, "foreign_key": "table.column"}`) is fine for prototypes, but production schemas outgrow it: `CHECK` constraints, composite `UNIQUE`, and expression defaults need raw DDL. Keep the full `CREATE TABLE` statements in one place (a `schema.gd` constant or a `res://data/schema.sql` you read and execute) so the schema is reviewable as SQL, diffable in PRs, and identical across dev machines.

### 13.4 Seeding catalogs from res:// JSON

The lookup tables ([§13.1](#13-schema-design--the-relax-room-database)) are re-seeded on every startup from the authored `res://` catalogs, inside one transaction. Re-seeding (rather than migrating catalog rows) keeps a single source of truth: ship a new catalog JSON, and the database reflects it on next launch with zero catalog-migration code.

```gdscript
# Inside LocalDatabase - called from _ready() after _migrate_schema()
func _seed_catalogs() -> void:
    var catalog: Variant = JSON.parse_string(
        FileAccess.get_file_as_string("res://data/catalog_items.json"))
    if typeof(catalog) != TYPE_DICTIONARY:
        push_error("catalog_items.json unreadable - keeping previous seed")
        return      # old seed stays: the app still works with last-known catalog

    db.query("BEGIN;")
    var ok := true
    for table in ["categoria", "colore", "shop"]:
        for row in catalog.get(table, []):
            ok = ok and execute(
                "INSERT OR REPLACE INTO %s VALUES (?, ?%s);" %
                    [table, ", ?" if table == "colore" else ""],
                row.values())    # table names from a literal list, never from data (§14.1)
    for item in catalog.get("items", []):
        ok = ok and execute("""
            INSERT OR REPLACE INTO items
                (item_id, name, price, shop_id, categoria_id, colore_id, sprite_path)
            VALUES (?, ?, ?, ?, ?, ?, ?);""", [
            int(item["id"]), item["name"], int(item["price"]),
            int(item["shop_id"]), int(item["categoria_id"]),
            int(item["colore_id"]), item["sprite_path"]])
    if ok:
        db.query("COMMIT;")
    else:
        db.query("ROLLBACK;")
        push_error("Catalog seed rolled back: " + db.error_message)
```

Two deliberate choices: `INSERT OR REPLACE` keyed on stable catalog IDs updates changed rows and adds new ones while never touching user tables; and **removed** catalog items are *not* deleted from the lookup tables if any `inventario` row references them (the non-cascading FK from [§13.3](#13-schema-design--the-relax-room-database) refuses) — a retired shop item silently disappears from the store UI but remains resolvable for users who own it. That is the correct end-of-life for purchasable content.

---

## 14. Queries, bindings and transactions

### 14.1 Parameterized queries — the only way in

SQL built by string interpolation is an injection vulnerability *and* an escaping bug factory (a display name containing `'` breaks the query even with a well-meaning user). Bound parameters fix both at once: the SQL text and the values travel separately, so values can never be parsed as SQL.

```gdscript
# DANGEROUS - never do this, not even "just for internal values"
var q := "SELECT * FROM accounts WHERE display_name = '%s';" % username
db.query(q)   # username = "'; DROP TABLE accounts; --" → catastrophe
              # username = "O'Hara"                      → syntax error, subtly broken app

# CORRECT - placeholders + bindings array, positional
db.query_with_bindings(
    "SELECT * FROM accounts WHERE display_name = ?;", [username])
```

"But this is a local, single-player database — who would inject *themselves*?" Two answers. First, injection is only half the point: binding also handles quoting, Unicode and NULLs correctly, which raw interpolation never will. Second, the moment sync ships ([§18](#18-cloud-sync-and-supabase)), remote data flows into these same queries — display names chosen on *another* device, payloads from a server. The habit must already be universal by then. Make it mechanical: **the only SQL string literals in the codebase contain `?` placeholders; `%` never appears near SQL.**

> ⚠️ **Pitfall** — Placeholders bind **values**, not identifiers. `"SELECT * FROM ? WHERE id = ?"` is invalid — table and column names cannot be parameters. When a table name must vary (the sync-queue replayer, [§18.2](#18-cloud-sync-and-supabase)), validate it against a hard-coded allowlist (`const SYNCABLE := ["accounts", "characters", "rooms", "inventario"]`) before splicing it into SQL. Never splice anything else.

### 14.2 A thin CRUD wrapper

Raw `query_with_bindings` everywhere invites copy-paste drift. Relax Room wraps the four shapes it actually uses — scalar read, row read, list read, write — in a dozen lines each, keeping errors and logging in one chokepoint:

```gdscript
# Inside LocalDatabase (continued from §12.2)

func fetch_one(sql: String, params: Array = []) -> Dictionary:
    if not db.query_with_bindings(sql, params):
        _log_db_error(sql)
        return {}
    return db.query_result[0] if db.query_result.size() > 0 else {}

func fetch_all(sql: String, params: Array = []) -> Array[Dictionary]:
    var out: Array[Dictionary] = []
    if not db.query_with_bindings(sql, params):
        _log_db_error(sql)
        return out
    for row in db.query_result:
        out.append(row)
    return out

func execute(sql: String, params: Array = []) -> bool:
    if not db.query_with_bindings(sql, params):
        _log_db_error(sql)
        return false
    return true

func _log_db_error(sql: String) -> void:
    AppLogger.error("db", "SQL failed: %s | error: %s" % [sql.left(120), db.error_message])
```

Domain methods then read like the domain, not like SQL plumbing:

```gdscript
func get_account(auth_uid: String) -> Dictionary:
    return fetch_one("SELECT * FROM accounts WHERE auth_uid = ?;", [auth_uid])

func add_coins(account_id: int, delta: int) -> bool:
    return execute("""
        UPDATE accounts
        SET coins = coins + ?, updated_at = datetime('now')
        WHERE account_id = ?;""", [delta, account_id])

func get_inventory(account_id: int) -> Array[Dictionary]:
    return fetch_all("""
        SELECT i.item_id, i.name, i.sprite_path, inv.quantity
        FROM inventario AS inv
        JOIN items AS i ON i.item_id = inv.item_id
        WHERE inv.account_id = ?
        ORDER BY inv.acquired_at;""", [account_id])
```

Note `add_coins` computes `coins = coins + ?` **in SQL**, not read-modify-write in GDScript — atomic at the statement level, and the `CHECK (coins >= 0)` constraint turns an overdraft into a clean failure you can surface as "not enough coins".

### 14.3 Upserts

SQLite's `ON CONFLICT` clause (available in every SQLite bundled with current godot-sqlite) makes "insert or update" one statement, keyed on any UNIQUE constraint:

```gdscript
func grant_item(account_id: int, item_id: int, quantity: int = 1) -> bool:
    return execute("""
        INSERT INTO inventario (account_id, item_id, quantity)
        VALUES (?, ?, ?)
        ON CONFLICT (account_id, item_id)
        DO UPDATE SET quantity = quantity + excluded.quantity;""",
        [account_id, item_id, quantity])
```

This is why [§13.3](#13-schema-design--the-relax-room-database) insisted on `UNIQUE (account_id, item_id)`: the constraint *is* the upsert key. The same pattern drives account upserts on save-mirroring ([§16.3](#16-case-study--the-json--sqlite-hybrid)) keyed on `auth_uid`.

### 14.4 Transactions — correctness first, speed second

Without an explicit transaction, **every statement is its own transaction** with its own commit and disk sync. That has two costs:

- **Correctness:** a save that writes account + character + 30 inventory rows as 32 auto-commits can be interrupted after 17 of them — leaving a torn, internally inconsistent database. Inside one transaction it is all-or-nothing.
- **Performance:** each auto-commit pays a sync. Batching 100 inserts into one transaction routinely yields 10-50× speedups.

```gdscript
func save_inventory(account_id: int, item_stacks: Array[Dictionary]) -> bool:
    db.query("BEGIN;")
    var ok := execute("DELETE FROM inventario WHERE account_id = ?;", [account_id])
    for stack in item_stacks:
        if not ok:
            break
        ok = execute("""
            INSERT INTO inventario (account_id, item_id, quantity)
            VALUES (?, ?, ?);""",
            [account_id, int(stack["item_id"]), int(stack["quantity"])])
    if ok:
        db.query("COMMIT;")
        return true
    db.query("ROLLBACK;")
    AppLogger.error("db", "save_inventory rolled back for account %d" % account_id)
    return false
```

Rules that keep transactions boring (boring is the goal):

1. **Every multi-statement write is wrapped.** The whole save-mirror ([§16.3](#16-case-study--the-json--sqlite-hybrid)) is one transaction: the database always contains a complete snapshot or the previous one, never a blend.
2. **Every `BEGIN` has exactly two exits** — `COMMIT` on full success, `ROLLBACK` on any failure. Early-`return` between `BEGIN` and `COMMIT` leaves the connection inside a transaction; every later write silently joins it and nothing persists until something else commits. Structure the code so exits are impossible to miss (single `ok` flag, one exit block, as above).
3. **Keep transactions short-lived.** Do the Dictionary massaging *before* `BEGIN`; the transaction wraps only the SQL. Long-open transactions grow the WAL and delay checkpoints ([§15.1](#15-operating-sqlite--wal-pragmas-migrations-backups)).
4. **Reads don't need explicit transactions** in this single-connection architecture; each SELECT sees a consistent snapshot.

> ✅ **Best practice** — Wrap the pattern once (`func in_transaction(work: Callable) -> bool` that begins, calls `work`, and commits/rolls back based on the return value) and forbid bare `BEGIN` elsewhere. When every transaction goes through one function, "did we roll back on that path?" stops being a code-review question.

### 14.5 Query patterns for app features

A grab-bag of shapes that recur in feature work, in their robust forms:

```gdscript
# Existence check - EXISTS stops at the first hit, COUNT(*) scans everything:
func owns_item(account_id: int, item_id: int) -> bool:
    var row := fetch_one("""
        SELECT EXISTS(
            SELECT 1 FROM inventario WHERE account_id = ? AND item_id = ?
        ) AS owned;""", [account_id, item_id])
    return int(row.get("owned", 0)) == 1

# Aggregates with GROUP BY - inventory summary for the UI:
func inventory_by_category(account_id: int) -> Array[Dictionary]:
    return fetch_all("""
        SELECT c.name AS category, COUNT(*) AS stacks, SUM(inv.quantity) AS total
        FROM inventario AS inv
        JOIN items     AS i ON i.item_id = inv.item_id
        JOIN categoria AS c ON c.categoria_id = i.categoria_id
        WHERE inv.account_id = ?
        GROUP BY c.categoria_id
        ORDER BY total DESC;""", [account_id])

# Guarded spend - the WHERE clause makes overdraft impossible even under races,
# and changes() tells you whether it happened:
func try_spend_coins(account_id: int, cost: int) -> bool:
    execute("""
        UPDATE accounts SET coins = coins - ?, updated_at = datetime('now')
        WHERE account_id = ? AND coins >= ?;""", [cost, account_id, cost])
    var row := fetch_one("SELECT changes() AS n;")
    return int(row.get("n", 0)) == 1
```

For **paging** (a shop list, a long log), prefer keyset pagination over `OFFSET` — `WHERE item_id > ? ORDER BY item_id LIMIT 50` stays fast at any depth, while `LIMIT 50 OFFSET 5000` re-scans 5,000 rows to throw them away. At Relax Room's scale both work; at any scale, the keyset form is the same amount of code, so build the habit on day one.

The `try_spend_coins` shape deserves a name — **compare-and-set in SQL**. The alternative (SELECT the balance, check in GDScript, UPDATE) has a time-of-check/time-of-use gap. In a single-threaded local app the gap is theoretical; the moment a second writer appears (a sync merge, a second window), it is a dupe-exploit. The SQL form is race-free under SQLite's serialized writes, costs nothing extra, and reads clearly.

---

## 15. Operating SQLite — WAL, PRAGMAs, migrations, backups

### 15.1 WAL mode — what those -wal and -shm files are

SQLite's default journal mode (`DELETE`) writes changes into the main file after copying original pages to a rollback journal; writers take an exclusive lock that blocks readers. **WAL (Write-Ahead Logging)** inverts this: committed changes are *appended* to a separate `-wal` file while the main database stays untouched; readers read the main file (plus the WAL index) concurrently.

```
relax_room.db        ← main database: pages, mostly stable
relax_room.db-wal    ← write-ahead log: committed changes, append-only
relax_room.db-shm    ← shared-memory index into the WAL (helps readers find pages)
```

Why Relax Room turns it on (`PRAGMA journal_mode = WAL;` once at open):

- **Readers never block the writer and vice versa** — the autosave mirror can commit while a UI query reads, with no stutter.
- **Fewer fsyncs, sequential appends** — commits are cheaper than in DELETE mode for our small-and-frequent write pattern.
- **The setting is persistent**: WAL is recorded in the database file itself, so it survives reopening. Setting it every open is harmless and self-documenting.

**Checkpointing** transfers WAL content back into the main file. It happens automatically when the WAL reaches ~1000 pages (~4 MB) and on the last connection's clean close. You can force it — useful right before copying the database file:

```gdscript
db.query("PRAGMA wal_checkpoint(TRUNCATE);")  # flush WAL into db, truncate WAL to zero
```

Modes: `PASSIVE` (checkpoint what it can without blocking), `FULL` (wait for readers, checkpoint everything), `RESTART`, `TRUNCATE` (as RESTART, plus truncates the WAL file). For a single-connection desktop app, `TRUNCATE` before backups is the only one you will ever call by hand.

> ⚠️ **Pitfall** — The `-wal` file **contains committed data** that may not be in the `.db` yet. Copying `relax_room.db` alone can capture a stale or even unreadable snapshot; deleting a `-wal` file by hand can *lose committed transactions or corrupt the database*. Rules: never touch `-wal`/`-shm` manually; if you copy the database file directly, checkpoint first (`wal_checkpoint(TRUNCATE)`) or copy all three files together; better, use `backup_to()` ([§15.4](#15-operating-sqlite--wal-pragmas-migrations-backups)) which handles all of it. Tell users the same if you document manual backup ("copy the whole folder").

### 15.2 PRAGMA essentials

PRAGMAs are per-connection (unless noted) — apply them right after `open_db()`:

| PRAGMA | Recommended | Why |
|---|---|---|
| `journal_mode = WAL` | yes (persistent) | concurrency + commit cost ([§15.1](#15-operating-sqlite--wal-pragmas-migrations-backups)) |
| `foreign_keys = ON` | yes (via `db.foreign_keys = true`) | FK enforcement is off by default ([§12.2](#12-sqlite-with-godot-sqlite--setup-and-core-api)) |
| `synchronous = NORMAL` | yes, with WAL | full durability-per-commit costs syncs; `NORMAL` in WAL keeps integrity on app crash, may lose the very last commits on *power* loss — the right trade for autosaved app state |
| `busy_timeout = 5000` | yes | on a locked database, retry for 5 s instead of failing instantly (antivirus, backup tools touch files on Windows) |
| `user_version` | optional | a free 32-bit integer in the header; lighter alternative to a `schema_version` table (we prefer the table — it can store history) |
| `integrity_check` | on demand | full-database self-check; run it when checksum-level paranoia is warranted (support tooling, [§19](#19-testing-persistence)) |

**Indices.** Primary keys and UNIQUE constraints are already indexed. Add explicit indices only for frequent lookups on *other* columns, and only when tables are big enough to matter — for Relax Room's row counts (one account, dozens of inventory rows) additional indices are pure overhead. The two that earn their keep as data grows:

```sql
CREATE INDEX IF NOT EXISTS idx_inventario_account ON inventario(account_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_created ON sync_queue(created_at);
```

Verify an index is used, not assumed: `EXPLAIN QUERY PLAN SELECT ...` should say `SEARCH ... USING INDEX`, not `SCAN`.

### 15.3 Schema migrations — the schema_version table

The save file has its migration pipeline ([§11](#11-save-versioning-and-migration-pipelines)); the database gets the same discipline with a version table and numbered, append-only, idempotent-by-bookkeeping migrations:

```gdscript
# Inside LocalDatabase - called once from _ready() after open (§12.2)

const MIGRATIONS: Array[Array] = [
    # [version, description, [statements...]]
    [1, "initial schema", []],   # v1 = the §13.2 DDL, run by _create_base_schema()
    [2, "inventory acquired_at", [
        "ALTER TABLE inventario ADD COLUMN acquired_at TEXT NOT NULL DEFAULT '';",
    ]],
    [3, "per-user password salt", [
        "ALTER TABLE accounts ADD COLUMN password_salt TEXT NOT NULL DEFAULT '';",
    ]],
    [4, "sync queue", [
        """CREATE TABLE IF NOT EXISTS sync_queue (
            queue_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name  TEXT NOT NULL,
            operation   TEXT NOT NULL CHECK (operation IN ('upsert', 'delete')),
            payload     TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            retry_count INTEGER NOT NULL DEFAULT 0
        );""",
    ]],
]

func _migrate_schema() -> void:
    db.query("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version    INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now')),
            note       TEXT NOT NULL DEFAULT ''
        );""")

    var row := fetch_one("SELECT MAX(version) AS v FROM schema_version;")
    var current := int(row.get("v", 0)) if row.get("v") != null else 0

    if current == 0:
        _create_base_schema()        # executes the full §13.2 DDL

    for migration in MIGRATIONS:
        var version: int = migration[0]
        var note: String = migration[1]
        var statements: Array = migration[2]
        if version <= current:
            continue
        db.query("BEGIN;")
        var ok := true
        for sql in statements:
            if not db.query(sql):
                ok = false
                break
        if ok:
            ok = execute("INSERT INTO schema_version (version, note) VALUES (?, ?);",
                [version, note])
        if ok:
            db.query("COMMIT;")
            AppLogger.info("db", "Schema migrated to v%d (%s)" % [version, note])
        else:
            db.query("ROLLBACK;")
            push_error("Schema migration v%d failed: %s" % [version, db.error_message])
            return    # stop: do not run later migrations on a failed base
```

The same laws as [§11](#11-save-versioning-and-migration-pipelines) apply — incremental, append-only, tested against old database fixtures — plus two SQLite specifics: `ALTER TABLE` is limited (add column: yes; drop/rename column: version-dependent — the portable fallback is create-new-table → copy → drop-old → rename, inside one transaction), and each migration transaction must contain *only* DDL/DML, never `PRAGMA journal_mode` changes.

### 15.4 Backups

Three layers, mirroring the JSON strategy ([§10.3](#10-atomic-writes-backups-and-corruption-detection)):

```gdscript
func backup_database() -> bool:
    DirAccess.make_dir_recursive_absolute("user://backups")
    var target := "user://backups/relax_room.%s.db" % Time.get_date_string_from_system()
    # backup_to uses SQLite's online backup API: consistent snapshot,
    # WAL handled, safe while the connection is open.
    if not db.backup_to(target):
        AppLogger.error("db", "backup_to failed: " + db.error_message)
        return false
    return true
```

1. **`backup_to()` daily**, rotated like the JSON backups — this is the trustworthy copy.
2. **`export_to_json()`** when preparing support bundles: a human-readable full dump, diffable and inspectable (and `import_from_json()` restores it — also the backbone of test fixtures, [§19](#19-testing-persistence)).
3. **The JSON save itself is a semantic backup** of the critical user state ([§16](#16-case-study--the-json--sqlite-hybrid)): if the database is lost entirely, the mirror rebuilds from the save.

### 15.5 Maintenance — integrity, size, vacuum

Three low-frequency chores round out database operations:

```gdscript
# 1) Self-check - run from the support/debug menu and in the corruption test suite:
func check_integrity() -> bool:
    db.query("PRAGMA integrity_check;")
    var verdict := ""
    if db.query_result.size() > 0:
        verdict = str(db.query_result[0].values()[0])
    if verdict != "ok":
        AppLogger.error("db", "integrity_check: " + verdict)
        return false
    return true

# 2) Size report - the honest number includes the WAL:
func database_size_bytes() -> int:
    var total := 0
    for suffix in ["", "-wal", "-shm"]:
        var path := ProjectSettings.globalize_path(DB_PATH + suffix)
        var f := FileAccess.open(path, FileAccess.READ)
        if f != null:
            total += f.get_length()
            f.close()
    return total

# 3) Reclaim space after mass deletion (account deletion, log pruning):
func vacuum() -> void:
    db.query("VACUUM;")     # rewrites the file compactly; needs free disk ≈ db size
```

SQLite never shrinks its file on DELETE — freed pages are reused, not returned to the OS. For a companion app's row counts this is irrelevant month to month, so do **not** schedule `VACUUM` routinely (it rewrites the whole file and invalidates the WAL's warm state); run it after the rare mass deletion, such as account removal ([§17.5](#17-authentication-for-offline-apps)). `integrity_check`, in contrast, earns a place both in the test suite and behind a "verify my data" support button — it is the database-level sibling of the save checksum.

---

## 16. Case study — the JSON + SQLite hybrid

> **Case study.** This section is Relax Room-specific by design: it shows one coherent, shipped answer to "which format?", built from every mechanism above. Treat it as a worked example to argue with, not a template to copy blindly.

### 16.1 The split and the reasons

```
res:// (read-only, shipped)          user:// (writable, user-owned)
┌────────────────────────┐           ┌─────────────────────────────────┐
│ catalog_items.json     │           │ save_data.json    ← source of   │
│ catalog_music.json     │  item_id  │   (envelope v5)     truth for   │
│ catalog_themes.json    │──refs────▶│                     session     │
└────────────────────────┘           │ relax_room.db     ← relational  │
     authored catalogs               │   (9 tables)        mirror +    │
                                     │                     sync base   │
                                     └─────────────────────────────────┘
```

**Catalogs live in `res://` as JSON** because they are authored content: versioned with the code in git, reviewed in PRs, diffed meaningfully, editable by a designer with a text editor, and automatically consistent with the build that ships them (a build's catalog can never be missing items its code expects). At startup, `GameManager` parses them once into typed in-memory structures; `LocalDatabase` seeds the lookup tables (`items`, `shop`, `categoria`, `colore`) from the same parse inside one transaction, so SQL joins against catalog data work locally.

**Session state lives in `user://save_data.json`** as the **source of truth**: human-readable (support and debugging), atomic-written ([§10](#10-atomic-writes-backups-and-corruption-detection)), versioned and migrated ([§11](#11-save-versioning-and-migration-pipelines)), checksummed. If every other store vanished, the save file alone reconstructs the user's world.

**Relational state lives in `user://relax_room.db`** as a **derived mirror** with three jobs: referential integrity checks that JSON cannot express (FK constraints catch dangling IDs, [§13](#13-schema-design--the-relax-room-database)), queryability (inventory joins, future statistics), and the substrate for cloud sync — the `sync_queue` is only meaningful next to the relational rows it describes ([§18](#18-cloud-sync-and-supabase)).

The reconciliation rule is one sentence, and it prevents every split-brain bug: **on conflict between save file and database, the save file wins; the database is rebuilt from it.** A derived copy with a defined rebuild rule is redundancy; two sources of truth is a fight.

### 16.2 The write path — from click to disk

```
User places a decoration
  │
  ├─ decoration_system.gd          updates the sprite, in-memory state
  ├─ SignalBus.decoration_placed   .emit(item_id, position)
  ├─ SaveManager                   appends DecorationState, mark_dirty()
  │
  └─ [autosave tick ≤60 s later, or checkpoint/quit]
       SaveManager.save_game()
         ├─ _compose_document()      envelope v5 from to_dict() snapshots  (§7)
         ├─ _write_atomically()      temp → verify → backup → rename      (§10)
         └─ SignalBus.save_committed.emit(document)
              │
              └─ LocalDatabase._on_save_committed(document)
                   BEGIN;
                     upsert account   (keyed on auth_uid)                 (§14.3)
                     upsert character
                     upsert room      (decorations as JSON column)        (§13.3)
                     replace inventory rows
                   COMMIT;                                                (§14.4)
```

Two properties to notice. The mirror is **event-driven but save-aligned**: the database updates when a save commits, not on every gameplay twitch — so both stores advance in lockstep and a crash between saves loses the same ≤60 seconds from both. And the mirror is **fed from the document**, not from live game state: whatever was atomically written is exactly what gets mirrored, so the two stores can never diverge by racing.

### 16.3 The mirror upsert

```gdscript
# Inside LocalDatabase
func _on_save_committed(doc: Dictionary) -> void:
    var data: Dictionary = doc.get("data", {})
    var account: Dictionary = data.get("account", {})
    var auth_uid: String = account.get("auth_uid", "local")

    db.query("BEGIN;")
    var ok := execute("""
        INSERT INTO accounts (auth_uid, display_name, coins)
        VALUES (?, ?, ?)
        ON CONFLICT (auth_uid) DO UPDATE SET
            display_name = excluded.display_name,
            coins        = excluded.coins,
            updated_at   = datetime('now');""",
        [auth_uid, account.get("display_name", ""), int(account.get("coins", 0))])

    var account_id := int(fetch_one(
        "SELECT account_id FROM accounts WHERE auth_uid = ?;", [auth_uid]
    ).get("account_id", 0))

    ok = ok and _upsert_character(account_id, data.get("character", {}))
    ok = ok and _upsert_room(account_id, data.get("room", {}))
    ok = ok and _replace_inventory(account_id, data.get("inventory", {}))

    if ok:
        db.query("COMMIT;")
    else:
        db.query("ROLLBACK;")
        AppLogger.error("db", "Mirror rolled back - save file remains authoritative")
```

A rolled-back mirror is logged but **not** treated as a save failure — the JSON commit already succeeded, the user's data is safe, and the mirror will catch up on the next save. This asymmetry is the practical payoff of declaring one source of truth.

### 16.4 When you would not build this

Honest scope check — the hybrid earns its complexity only because Relax Room needs *both* a shareable, debuggable session snapshot *and* relational queries plus a sync substrate. Simpler apps should choose simpler shapes:

| Your situation | Build instead |
|---|---|
| Settings + one small save, no relations, no sync plans | ConfigFile + one JSON save ([§6-7](#6-configfile--the-settings-recipe)) — stop there |
| Relational data, no need for a readable session file | SQLite only; `export_to_json()` covers debugging |
| Big binary state, nobody reads saves | `store_var` envelope + atomic write ([§8.1](#8-binary-and-resource-saves--fidelity-vs-security), [§10](#10-atomic-writes-backups-and-corruption-detection)) |
| Everything above plus sync | the hybrid, or SQLite-only with a JSON *export* feature |

---

## 17. Authentication for offline apps

Relax Room supports optional local accounts: a guest profile by default, an optional username+password to protect a profile on a shared machine, and a planned upgrade path to Supabase-backed cloud identity. This section builds that ladder and is deliberately honest about what local auth can and cannot promise.

### 17.1 The model ladder

| Model | Works offline | Cross-device | Friction | Real security level |
|---|---|---|---|---|
| Guest (anonymous) | yes | no | zero | none — and that's fine |
| Local username+password | yes | no | low | keeps honest people out; **not** resistant to disk access |
| Cloud email+password (Supabase Auth) | cached | yes | medium | real: server-side hashing, tokens, recovery |
| OAuth (Google/Discord) | cached | yes | low | real; adds provider dependency |

The threat-model sentence that governs every local-auth decision: **anyone who can read the app's files can, with effort, bypass local auth or crack weak hashes offline.** Local accounts are a *privacy convenience* (profiles on a family PC), not a security boundary. Say this in your docs; never imply otherwise to users.

### 17.2 Guest mode and account linking

Guest-first is non-negotiable for a companion app — the user must reach the room in zero clicks:

```
first launch → AuthManager creates account with auth_uid = "local"
             → full app, no prompts, everything persisted

"protect my profile" → user picks username+password
             → auth_uid becomes "user_<name>"; SAME account row, data kept
             → (future) link to Supabase → auth_uid becomes the cloud UUID
```

The invariant across every transition: **`auth_uid` changes, `account_id` does not** — every FK-linked row (character, room, inventory) survives untouched. Design the identity column for relabeling from day one and account linking is an UPDATE; design it as an immutable key and linking becomes a data-copying project.

### 17.3 Password hashing — the honest version

**Never store plaintext.** Beyond that, the quality ladder matters:

1. **Unsalted fast hash** (`password.sha256_text()`): broken — identical passwords share hashes, and precomputed tables crack common ones instantly.
2. **App-wide static salt** — the original Relax Room approach, preserved for the record:

```gdscript
# Historical AuthManager code (v1) - works, but assess it honestly:
const SALT := "MiniCozyRoom2026"

func _hash_password(password: String) -> String:
    return (SALT + password).sha256_text()
```

   *Honest assessment:* better than nothing — generic rainbow tables miss it. But the salt ships inside the binary (extractable in minutes), it is shared by all users (equal passwords still collide, one table cracks everyone), and SHA-256 is *designed to be fast* — a GPU tries billions of candidates per second against a stolen database. For a local cozy app the practical risk is low because the data being protected is a decorated room; the *pattern* is still the wrong one to learn.

3. **Per-user random salt + iterated hashing (PBKDF2 concept)** — the corrected v2, built from Godot's own crypto primitives. Unique salts kill shared-table attacks; thousands of HMAC iterations turn "billions of guesses per second" into "thousands", which is the entire point of a password-hashing function:

```gdscript
# auth_manager.gd (v2) - salted, iterated PBKDF2-HMAC-SHA256 (single 32-byte block)
const PBKDF2_ITERATIONS := 100_000

var _crypto := Crypto.new()

func _generate_salt() -> String:
    return _crypto.generate_random_bytes(16).hex_encode()   # CSPRNG, per account

func _hash_password(password: String, salt_hex: String) -> String:
    var pwd := password.to_utf8_buffer()
    var block := PackedByteArray(salt_hex.hex_decode())
    block.append_array(PackedByteArray([0, 0, 0, 1]))       # PBKDF2 INT(1), big-endian
    var u := _crypto.hmac_digest(HashingContext.HASH_SHA256, pwd, block)
    var result := u.duplicate()
    for _i in range(1, PBKDF2_ITERATIONS):
        u = _crypto.hmac_digest(HashingContext.HASH_SHA256, pwd, u)
        for j in result.size():
            result[j] = result[j] ^ u[j]
    return result.hex_encode()

func register(username: String, password: String) -> bool:
    var salt := _generate_salt()
    var hash := _hash_password(password, salt)
    return LocalDatabase.execute("""
        UPDATE accounts SET auth_uid = ?, display_name = ?,
               password_hash = ?, password_salt = ?, updated_at = datetime('now')
        WHERE auth_uid = 'local';""",
        ["user_" + username, username, hash, salt])

func verify_password(password: String, stored_hash: String, salt_hex: String) -> bool:
    var candidate := _hash_password(password, salt_hex)
    # Constant-time compare: don't leak match-length via timing.
    return _crypto.constant_time_compare(
        candidate.to_utf8_buffer(), stored_hash.to_utf8_buffer())
```

Implementation notes: `HashingContext` is the incremental-hashing API (`start(HashingContext.HASH_SHA256)` → `update(chunk)` → `finish()`), used here indirectly via `Crypto.hmac_digest`; 100k iterations cost ~a tenth of a second in a GDExtension-less GDScript loop — acceptable at login frequency, and tune the constant to your floor hardware. Real PBKDF2 with multi-block output adds block counters; one 32-byte block from SHA-256 is exactly one block, so this *is* PBKDF2-HMAC-SHA256 for our output size. If you later adopt a crypto GDExtension offering **Argon2id or bcrypt, prefer it** — memory-hard functions resist GPUs better than any iteration count. And the migration path is standard: store a `hash_version` column, verify old logins with the v1 scheme, immediately re-hash with v2 on success.

> ⚠️ **Pitfall** — Do not invent your own construction beyond this point ("I'll SHA-256 it 3 times with the username mixed in"). Password hashing is a solved problem with named, analyzed algorithms — PBKDF2, bcrypt, scrypt, Argon2. Every deviation you improvise has a cryptanalysis literature you have not read. Implement a named scheme or use a library; nothing in between.

### 17.4 Login flow and session state

```gdscript
signal auth_changed(auth_uid: String)   # actually lives on SignalBus

func login(username: String, password: String) -> bool:
    var row := LocalDatabase.fetch_one(
        "SELECT auth_uid, password_hash, password_salt FROM accounts WHERE auth_uid = ?;",
        ["user_" + username])
    if row.is_empty():
        return _fail_generic()          # same answer as wrong password - no user enumeration
    if not verify_password(password, row["password_hash"], row["password_salt"]):
        return _fail_generic()
    current_auth_uid = row["auth_uid"]
    SignalBus.auth_changed.emit(current_auth_uid)
    return true

func _fail_generic() -> bool:
    await get_tree().create_timer(0.5).timeout   # flat response time, cheap rate limit
    SignalBus.auth_failed.emit("Invalid username or password.")
    return false
```

Small choices with outsized value: one generic failure message (no "user not found" oracle), a flat small delay on failure (levels timing and rate-limits casual brute force), and all state changes announced via `SignalBus` so UI and `SaveManager` react without coupling.

### 17.5 Account deletion — GDPR-ish hygiene

Even a local-only app should delete cleanly; when sync arrives, this becomes a legal requirement rather than good manners:

```gdscript
func delete_account(auth_uid: String) -> bool:
    # 1) One CASCADE delete removes characters, rooms, inventory (§13.3 topology).
    var ok := LocalDatabase.execute(
        "DELETE FROM accounts WHERE auth_uid = ?;", [auth_uid])
    if not ok:
        return false
    # 2) Purge file artifacts: save, backups (they contain the same personal data).
    DirAccess.remove_absolute("user://save_data.json")
    DirAccess.remove_absolute("user://save_data.backup.json")
    _delete_rotated_backups()
    # 3) Queue cloud erasure for when sync is online (§18).
    LocalDatabase.execute("""
        INSERT INTO sync_queue (table_name, operation, payload)
        VALUES ('accounts', 'delete', ?);""",
        [JSON.stringify({"auth_uid": auth_uid})])
    # 4) Fresh guest state so the app remains usable.
    _create_guest_account()
    SignalBus.account_deleted.emit()
    return true
```

The often-forgotten step is **2**: deleting the database row while backups of the save file keep the display name and room forever is exactly the kind of gap data-protection reviews exist to catch. Delete the data everywhere you put it — which is also a strong argument for the disciplined file layout of [§2.4](#2-the-virtual-file-system--res-vs-user).

### 17.6 Sessions and "remember me"

Two session questions arrive with any auth feature, and both have wrong answers that look convenient:

**Local accounts.** "Remember me" means *remember which profile was active* — persist the `auth_uid` of the last session (in `settings.cfg` or a `last_session` table) and reopen that profile without a password prompt if the user opted in. It must **never** mean storing the password, in any encoding: base64 is not encryption, XOR with a constant is not encryption, and even real encryption with an in-binary key just moves the plaintext one `strings`-command away. If the user wants password-on-launch protection, they type the password; if they want convenience, you remember the *identity*, not the *credential*.

```gdscript
func try_resume_session() -> bool:
    if not Settings.get_setting("app", "remember_me"):
        return false
    var last_uid: String = Settings.get_setting("app", "last_auth_uid")
    if last_uid.is_empty() or last_uid == "local":
        return _open_guest()
    var row := LocalDatabase.fetch_one(
        "SELECT auth_uid, password_hash FROM accounts WHERE auth_uid = ?;", [last_uid])
    if row.is_empty():
        return _open_guest()
    if row["password_hash"] != "" and _profile_lock_enabled(last_uid):
        return false            # protected profile: show the login screen
    current_auth_uid = row["auth_uid"]
    SignalBus.auth_changed.emit(current_auth_uid)
    return true
```

**Cloud sessions.** Supabase logins return an `access_token` (short-lived JWT) and a `refresh_token` (long-lived). Persisting the refresh token *is* the standard way to stay signed in across launches — but a refresh token on disk is a bearer credential, so store it with the best protection the platform offers and full awareness of the limits: `FileAccess.open_encrypted_with_pass` raises the bar from "any text editor" to "someone who extracts the key from the binary" ([§3.1](#3-fileaccess--complete-api-tour)), and OS keychains (via a GDExtension) raise it properly where available. Always pair it with server-side hygiene: refresh-token rotation enabled in Supabase, and a visible "sign out of all devices" path for the user. Never persist the access token — it expires in minutes by design; refresh on launch instead.

---

## 18. Cloud sync and Supabase

> **Case study.** Cloud sync is Relax Room's *planned* Phase 4 — designed now, shipped later. Designing the local side first (identity, sync queue, timestamps) is precisely what makes the later cloud work incremental instead of a rewrite.

### 18.1 When NOT to build sync

Start with the veto checklist, because sync is the most expensive feature in this module and the easiest to regret:

- **No multi-device story?** A desktop companion used on one machine gains nothing. Ship a manual "export/import save" feature (zip `save_data.json`) and you have covered 90% of the need at 2% of the cost.
- **No appetite for operations?** Sync means a backend: keys, quotas, outages, GDPR data-processing duties, support tickets about "my rooms are different". This is a subscription of your attention, not a one-off feature.
- **Conflict semantics unclear?** If you cannot write down, in one paragraph, what happens when two devices edit the same room offline — you are not ready to implement it.

Relax Room proceeds because multi-device *is* the roadmap (desktop at work, desktop at home) and because the offline-first design keeps the blast radius small: **if Supabase is down or absent, nothing about the app changes.**

### 18.2 The offline-first sync queue (op log)

The design was already planted in [§13.2](#13-schema-design--the-relax-room-database): every local change that must reach the cloud is recorded as an *operation* in `sync_queue` — an append-only op log, drained when connectivity allows.

```
Local write path (always, online or not):
  save committed → mirror upserted (§16.3) → sync_queue row appended (same transaction)

Drain (on launch, on reconnect, then every few minutes):
  SELECT * FROM sync_queue ORDER BY queue_id LIMIT 20;
  for each op → HTTP upsert/delete to Supabase
    success → DELETE FROM sync_queue WHERE queue_id = ?;
    failure → retry_count += 1; keep in queue
  retry_count > 5 → park it: log, surface "sync paused" state, stop hammering
```

```gdscript
# sync_manager.gd - queue drain (HTTP plumbing in §18.4)
func drain_queue() -> void:
    if _draining or not _is_online or not AuthManager.has_cloud_session():
        return
    _draining = true
    var ops := LocalDatabase.fetch_all(
        "SELECT * FROM sync_queue ORDER BY queue_id LIMIT 20;")
    for op in ops:
        var ok := await _push_operation(op)          # §18.4
        if ok:
            LocalDatabase.execute(
                "DELETE FROM sync_queue WHERE queue_id = ?;", [int(op["queue_id"])])
        else:
            LocalDatabase.execute(
                "UPDATE sync_queue SET retry_count = retry_count + 1 WHERE queue_id = ?;",
                [int(op["queue_id"])])
            break            # network problem: stop the batch, back off (§18.5)
    _draining = false
```

Design properties that make op-log sync robust where "just upload the save file" is not:

- **Ordering is preserved** (`ORDER BY queue_id`): a rename followed by a delete replays as rename-then-delete, never the reverse.
- **The queue row is written in the same SQLite transaction as the mirror** — the op log can never claim something the database doesn't contain, or miss something it does.
- **Operations are upserts keyed on `auth_uid`** ([§13.3](#13-schema-design--the-relax-room-database)), so replaying an op twice is harmless (idempotent) — which forgives every crash-between-push-and-delete race without distributed-transactions heroics.

### 18.3 Conflict resolution

Two devices edit offline; both come online. Somebody must decide.

**Last-Write-Wins (LWW)** — every syncable row carries `updated_at`; on conflict the newer timestamp wins. This is Relax Room's choice, and it is the right one for a single-user cozy app: conflicts are rare (one human, two machines), the data is aesthetic rather than transactional, and losing the older of your own two edits is understandable. Requirements: timestamps in UTC everywhere ([§13.3](#13-schema-design--the-relax-room-database)), tolerance for client clock skew (compare with a few seconds of slack; consider the server's clock authoritative on write), and LWW applied **per section** (character / room / inventory), not per whole save — device A's music change should not clobber device B's decoration change.

**Field/segment merge** — LWW per smaller unit, merging non-overlapping edits. Better outcomes, meaningfully more code and more test surface. Adopt only if per-section LWW demonstrably loses user work.

**CRDTs / vector clocks** — principled concurrent-edit resolution for collaborative or competitive multi-user state. Out of scope for a single-user companion; know the term, skip the machinery.

One rule prevents the sync disaster stories: **the merge decision runs locally, and its output flows through the normal save path** (envelope → atomic write → mirror). Sync must never write directly into the database behind `SaveManager`'s back — that reintroduces the second source of truth that [§16.1](#16-case-study--the-json--sqlite-hybrid) banned.

### 18.4 Supabase from Godot via HTTPRequest

Supabase exposes Postgres through PostgREST: every table becomes a REST endpoint at `https://<project-ref>.supabase.co/rest/v1/<table>`, authenticated by an `apikey` header plus a user JWT in `Authorization`. No SDK required — Godot's `HTTPRequest` node covers it. (Community addons like `supabase-community/godot-engine.supabase` exist; Relax Room deliberately uses plain HTTP for zero dependencies and full error-handling control.)

```gdscript
# supabase_client.gd - minimal REST client
const SUPABASE_URL := "https://YOUR-PROJECT-REF.supabase.co"
const SUPABASE_ANON_KEY := "eyJ..."     # anon key: public BY DESIGN, safe only WITH RLS

var _access_token := ""                  # user JWT from login

func _headers() -> PackedStringArray:
    return PackedStringArray([
        "apikey: " + SUPABASE_ANON_KEY,
        "Authorization: Bearer " + (_access_token if _access_token else SUPABASE_ANON_KEY),
        "Content-Type: application/json",
        "Prefer: resolution=merge-duplicates",    # PostgREST upsert semantics
    ])

## Sign in with email+password → JWT (Supabase Auth REST endpoint).
func sign_in(email: String, password: String) -> bool:
    var http := HTTPRequest.new()
    add_child(http)
    var body := JSON.stringify({"email": email, "password": password})
    var err := http.request(
        SUPABASE_URL + "/auth/v1/token?grant_type=password",
        PackedStringArray(["apikey: " + SUPABASE_ANON_KEY, "Content-Type: application/json"]),
        HTTPClient.METHOD_POST, body)
    if err != OK:
        http.queue_free()
        return false
    var result: Array = await http.request_completed   # [result, code, headers, body]
    http.queue_free()
    if int(result[1]) != 200:
        return false
    var payload: Variant = JSON.parse_string(result[3].get_string_from_utf8())
    if typeof(payload) != TYPE_DICTIONARY or not payload.has("access_token"):
        return false
    _access_token = payload["access_token"]            # also store refresh_token + expiry
    return true

## Upsert one row into a table (drives §18.2's _push_operation for 'upsert' ops).
func upsert(table: String, row: Dictionary) -> bool:
    var http := HTTPRequest.new()
    add_child(http)
    var err := http.request(
        SUPABASE_URL + "/rest/v1/" + table,
        _headers(), HTTPClient.METHOD_POST, JSON.stringify(row))
    if err != OK:
        http.queue_free()
        return false
    var result: Array = await http.request_completed
    http.queue_free()
    return int(result[1]) in [200, 201, 204]
```

Practical notes: `HTTPRequest` is a node (add it to the tree; one request per node at a time — create per call or pool a few); `request_completed` delivers `(result, response_code, headers, body: PackedByteArray)`; JWTs expire, so persist the `refresh_token` and refresh proactively; and table names arriving from `sync_queue` rows must pass the allowlist check from [§14.1](#14-queries-bindings-and-transactions) before being spliced into a URL.

### 18.5 Row Level Security — why the anon key is publishable

The anon key ships inside your binary; extraction is trivial, and that is *by design*. Security comes from Postgres **Row Level Security**: policies evaluated on every query, keyed to the JWT's user id (`auth.uid()`), enforced server-side no matter what client sends the request.

```sql
-- Supabase dashboard: schema mirroring §13, RLS enforced
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "own_account" ON accounts
    FOR ALL
    USING (auth_uid = (SELECT auth.uid()::text))
    WITH CHECK (auth_uid = (SELECT auth.uid()::text));
-- child tables: policies via EXISTS against the owning account, as in the
-- project's Supabase schema draft (characters → accounts, rooms → characters)
```

With RLS on, a stolen anon key + someone else's flow yields *only that attacker's own rows*. Two iron rules: **every synced table has RLS enabled with both `USING` and `WITH CHECK`** (read *and* write filtered — forgetting `WITH CHECK` lets users write rows they cannot read), and **the `service_role` key never ships in a client** — it bypasses RLS entirely and belongs only in server-side contexts you control.

### 18.6 Rate limits and backoff

Free-tier Supabase enforces request quotas, and any server hiccup can turn a naive drain loop into a hammer. The standard answer is **exponential backoff with jitter**:

```gdscript
var _backoff_seconds := 1.0

func _on_push_failed() -> void:
    _backoff_seconds = minf(_backoff_seconds * 2.0, 300.0)     # 1,2,4,…,300 cap
    var jitter := randf_range(0.0, _backoff_seconds * 0.25)
    _retry_timer.start(_backoff_seconds + jitter)

func _on_push_succeeded() -> void:
    _backoff_seconds = 1.0
```

Respect `429` responses (honor a `Retry-After` header when present), drain in small batches (the `LIMIT 20` above), and remember the offline-first covenant: a fully saturated backoff state must be *invisible* in the app beyond a quiet "sync paused" indicator.

### 18.7 First-run pull — bootstrapping a second device

The queue handles ongoing pushes; a *new* device needs the opposite flow — pull everything once, then join normal operation:

```
login on fresh device
  │
  ├─ local state empty? ──── yes ──► PULL: GET each synced table, filtered by identity
  │                                    /rest/v1/accounts?select=*&auth_uid=eq.<uid>
  │                                    /rest/v1/characters?select=*   (RLS scopes rows)
  │                                    assemble rows → save envelope (§7.4)
  │                                    → SaveMigrations.migrate()      (cloud data can be old!)
  │                                    → atomic write → mirror         (normal path, §16.2)
  │
  └─ local GUEST data exists? ─────► decide explicitly, never silently:
       offer "keep this device's room" (push local up, LWW forward from here)
       or   "use my cloud room"       (archive local save to backups/, then pull)
```

Implementation notes: PostgREST filters use `column=eq.value` query parameters and `select=*` for column selection, and RLS ([§18.5](#18-cloud-sync-and-supabase)) already scopes every response to the authenticated user — the filters are for shape, not security. The pulled document goes through the **same** migration pipeline and the **same** atomic write path as any local load; cloud rows written by an older app version are just another old format, already handled by [§11](#11-save-versioning-and-migration-pipelines). And the guest-collision fork is a UX decision that must surface to the user — both silent choices (clobber local, clobber cloud) destroy someone's room, and support cannot tell you which one the user wanted after the fact.

---

## 19. Testing persistence

Persistence code is uniquely testable — pure functions over data, explicit I/O boundaries — and uniquely worth testing, because its failures destroy user data silently. Three techniques cover most of the risk.

### 19.1 Temp dirs — never test against real user data

Every test writes into a disposable directory, never the real `user://` roots the app uses:

```gdscript
# test_helpers.gd
static func make_test_dir() -> String:
    var dir := "user://_tests/%d_%d" % [Time.get_ticks_usec(), randi() % 10000]
    DirAccess.make_dir_recursive_absolute(dir)
    return dir

static func cleanup_test_dir(dir: String) -> void:
    var d := DirAccess.open(dir)
    if d == null:
        return
    for f in d.get_files():
        DirAccess.remove_absolute(dir.path_join(f))
    for sub in d.get_directories():
        cleanup_test_dir(dir.path_join(sub))
    DirAccess.remove_absolute(dir)
```

This requires the production classes to accept paths instead of hard-coding them — which is why `SaveManager` computes paths through overridable functions ([§9.3](#9-savemanager-architecture)) and `LocalDatabase` takes `DB_PATH` as a property it can be constructed around. Testability here is an architecture feature, not a test-file trick. With a framework like **GUT** (Godot Unit Test) or **gdUnit4**, `make_test_dir()` belongs in `before_each` and cleanup in `after_each`.

### 19.2 Deterministic fixtures

Checked-in fixture files make format guarantees executable:

```
tests/fixtures/
  save_v1.json          ← written by the real v1 build, frozen forever (§11)
  save_v2.json … save_v4.json
  save_v5_golden.json   ← expected output of migrating save_v1.json
  db_v1_export.json     ← LocalDatabase.export_to_json() of a v1 database
```

```gdscript
func test_v1_migrates_to_current() -> void:
    var v1: Dictionary = JSON.parse_string(
        FileAccess.get_file_as_string("res://tests/fixtures/save_v1.json"))
    var migrated := SaveMigrations.migrate(v1)
    assert_eq(int(migrated["version"]), SaveMigrations.CURRENT_VERSION)
    assert_true(migrated["data"].has("music"), "v1→v2 must add music")
    assert_true(migrated["data"].has("inventory"), "v2→v3 must add inventory")
    assert_false(migrated["data"].has("xp"), "v3→v4 must drop xp")
    assert_eq(migrated["data"]["account"].get("auth_uid", ""), "local")
```

Keep fixtures **deterministic**: fixed timestamps, fixed IDs, `JSON.stringify` with default `sort_keys` — so golden-file comparisons are byte-stable. For SQLite, `import_from_json()` rebuilds a known database state in a temp path in milliseconds, which makes even migration-runner tests fast.

### 19.3 Corrupting saves on purpose

The recovery ladder ([§10.5](#10-atomic-writes-backups-and-corruption-detection)) only counts as engineering if it is exercised. Corrupt files deliberately, in every way the field will:

```gdscript
func test_truncated_save_recovers_from_backup() -> void:
    var dir := TestHelpers.make_test_dir()
    var sm := TestableSaveManager.new(dir)
    sm.save_game_with(_fixture_state())            # writes primary + backup

    # Simulate a crash mid-write: truncate the primary to half its length.
    var path := sm.save_path()
    var full := FileAccess.get_file_as_string(path)
    var f := FileAccess.open(path, FileAccess.WRITE)
    f.store_string(full.left(full.length() / 2))
    f.close()

    var loaded := sm.load_game()
    assert_eq(int(loaded["data"]["account"]["coins"]), 250,
        "must recover full state from backup, not reset")
    TestHelpers.cleanup_test_dir(dir)

func test_checksum_rejects_tampered_data() -> void:
    var doc := _saved_fixture_doc()
    doc["data"]["account"]["coins"] = 999999       # tamper without recomputing checksum
    assert_false(SaveManager._verify_checksum(doc))

func test_garbage_bytes_do_not_crash_loader() -> void:
    var dir := TestHelpers.make_test_dir()
    var f := FileAccess.open(dir.path_join("save_data.json"), FileAccess.WRITE)
    f.store_buffer(Crypto.new().generate_random_bytes(512))   # pure noise
    f.close()
    var sm := TestableSaveManager.new(dir)
    var loaded := sm.load_game()                   # must not throw, must not hang
    assert_eq(int(loaded.get("version", 0)), SaveMigrations.CURRENT_VERSION)
    TestHelpers.cleanup_test_dir(dir)
```

The corruption test matrix worth automating: truncation at 0%/50%/99%, random byte noise, valid JSON of the wrong shape (top-level array; `"data"` a string), checksum mismatch, missing file, missing backup *and* primary, a future `version`, and — for SQLite — a zero-byte `.db` and a `.db` with a stale `-wal` sibling. Every row in that matrix is something a real user's disk will eventually produce; the test suite is where you meet it first, politely.

> ✅ **Best practice** — Add one *fuzz-lite* test that loops 100 random truncations/bit-flips of a valid save and asserts only two things: the loader never crashes, and it always returns either recovered state or clean defaults. It runs in milliseconds and has an uncanny record of finding the one unchecked `.get()` in a loader.

### 19.4 Running persistence tests headless

Persistence tests need no window, which makes them the cheapest CI job in a Godot project. A framework-free runner is one `SceneTree` script:

```gdscript
# tests/run_tests.gd - run with:  godot --headless -s tests/run_tests.gd
extends SceneTree

var _failures := 0

func _initialize() -> void:
    _run("truncated save recovers", test_truncated_save_recovers_from_backup)
    _run("checksum rejects tamper", test_checksum_rejects_tampered_data)
    _run("garbage does not crash", test_garbage_bytes_do_not_crash_loader)
    _run("v1 migrates to current", test_v1_migrates_to_current)
    print("---- %s ----" % ("FAILED (%d)" % _failures if _failures > 0 else "ALL PASSED"))
    quit(1 if _failures > 0 else 0)      # exit code is the CI contract

func _run(name: String, test: Callable) -> void:
    var before := _failures
    test.call()
    print("%s %s" % ["FAIL" if _failures > before else " ok ", name])

func expect(condition: bool, message: String) -> void:
    if not condition:
        _failures += 1
        printerr("  assertion failed: " + message)
```

```yaml
# .github/workflows/persistence.yml (excerpt)
- name: Run persistence tests
  run: godot --headless -s tests/run_tests.gd
```

Headless specifics worth knowing: `user://` in CI resolves under the runner's home directory — the temp-dir discipline of [§19.1](#19-testing-persistence) keeps runs hermetic anyway; godot-sqlite works headless (it is a GDExtension, no rendering involved) so the full migration-and-corruption matrix runs on every push; and `quit(exit_code)` is the entire integration contract with CI. When the suite outgrows this harness, GUT and gdUnit4 both ship command-line runners with the same exit-code behavior — the tests transfer, the runner upgrades. Wire the job in front of the export step (see [Build and Export](BUILD_AND_EXPORT.md)) so a save-system regression can never reach a shipped build.

---

## Best practices

A consolidated reference — each item links back to the section that justifies it.

### Files and formats

1. **Write only to `user://`; treat `res://` as read-only always** (it *is* read-only after export). Audit for `res://` + `WRITE` before every release. ([§2](#2-the-virtual-file-system--res-vs-user))
2. **Pin `custom_user_dir_name` on day one** so project renames never orphan user data. ([§2.3](#2-the-virtual-file-system--res-vs-user))
3. **Check every I/O result** — `null` from factories, `Error` from operations — and route failures through one logging chokepoint with `error_string()`. ([§4](#4-diraccess-and-io-error-handling))
4. **Choose formats by data shape**: ConfigFile for settings, JSON for readable state, `store_var(false)` for bulk fidelity, SQLite for relations. One authoritative home per datum. ([§5](#5-persistence-options-compared))
5. **Never load Resources or `get_var(true)` payloads from untrusted files** — both are code-execution vectors. ResourceSaver is for content you author, not state users produce. ([§8](#8-binary-and-resource-saves--fidelity-vs-security))
6. **Normalize what you query, document what you load whole** (the `decorations` JSON-column rule). ([§13.3](#13-schema-design--the-relax-room-database))

### Save system

7. **Atomic writes everywhere**: temp file → verify → backup copy → rename. Same volume, always. ([§10.2](#10-atomic-writes-backups-and-corruption-detection))
8. **Backup in layers**: per-write `.backup.json`, daily rotation with a cap, and a recovery ladder that tries every rung before starting fresh. ([§10.3](#10-atomic-writes-backups-and-corruption-detection), [§10.5](#10-atomic-writes-backups-and-corruption-detection))
9. **Checksum the payload** and be honest about what it defends against (corruption and casual tampering, not attackers). ([§10.4](#10-atomic-writes-backups-and-corruption-detection))
10. **Version from day one, migrate incrementally, keep migrations append-only and pure**, write back after migrating, keep a fixture per historical version. ([§11](#11-save-versioning-and-migration-pipelines))
11. **Dirty flag + autosave timer + explicit checkpoints**; failed saves keep the flag set and self-retry. Quit-save is insurance, autosave is the defense. ([§9.2](#9-savemanager-architecture))

### SQLite

12. **Open once, close once**; `foreign_keys = true` before `open_db()`; `journal_mode = WAL`, `synchronous = NORMAL`, `busy_timeout` at open. ([§12](#12-sqlite-with-godot-sqlite--setup-and-core-api), [§15.2](#15-operating-sqlite--wal-pragmas-migrations-backups))
13. **Bound parameters only** — no string interpolation near SQL, allowlists for identifiers. ([§14.1](#14-queries-bindings-and-transactions))
14. **Every multi-statement write is one transaction** with exactly two exits. ([§14.4](#14-queries-bindings-and-transactions))
15. **Never hand-touch `-wal`/`-shm`**; checkpoint before copying; prefer `backup_to()`. ([§15.1](#15-operating-sqlite--wal-pragmas-migrations-backups), [§15.4](#15-operating-sqlite--wal-pragmas-migrations-backups))
16. **`schema_version` table + numbered migrations**, same laws as save migrations. ([§15.3](#15-operating-sqlite--wal-pragmas-migrations-backups))

### Auth and cloud

17. **Local auth is a privacy convenience, not a security boundary** — say so. Per-user random salt + iterated hashing (PBKDF2 concept) minimum; named algorithms only; constant-time comparison. ([§17.3](#17-authentication-for-offline-apps))
18. **Guest-first, link-in-place**: `auth_uid` relabels, `account_id` never changes. ([§17.2](#17-authentication-for-offline-apps))
19. **Offline-first or don't bother**: local is the source of truth, sync replays an idempotent op log, merges flow through the normal save path, backoff with jitter on failure. ([§18](#18-cloud-sync-and-supabase))
20. **RLS on every synced table (`USING` + `WITH CHECK`); `service_role` key never in a client.** ([§18.5](#18-cloud-sync-and-supabase))
21. **Delete completely**: CASCADE topology + file artifacts + queued cloud erasure. ([§17.5](#17-authentication-for-offline-apps))

### Pre-release checklist (Relax Room ships against this list)

```
[ ] Atomic writes on every save path (temp → verify → backup → rename)
[ ] Backup rotation capped and tested; recovery ladder exercised by tests
[ ] Migration chain green from every fixture version (save v1..vN, db v1..vN)
[ ] PRAGMA foreign_keys ON verified (query returns 1); WAL active
[ ] No string-interpolated SQL (grep for '%' within 2 lines of 'query')
[ ] No ResourceLoader.load / get_var(true) reachable from user files
[ ] Connection opened once, closed in NOTIFICATION_WM_CLOSE_REQUEST
[ ] Corruption matrix tests pass (truncation, noise, tamper, missing files)
[ ] Export build tested: res:// catalogs included, user:// writes verified
[ ] Support path works: open-save-folder button, JSONL logs rotating
```

---

## Common errors & troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Save works in editor, silently lost in exported build | writing to `res://` (read-only after export) | write to `user://`; audit all write paths ([§2.1](#2-the-virtual-file-system--res-vs-user)) |
| Catalog JSON missing only in exported build | non-resource files not exported | add `*.json` to the export preset's non-resource filter ([§2.1](#2-the-virtual-file-system--res-vs-user)) |
| `FileAccess.open()` returns `null` | missing file, permissions, locked file | branch on `FileAccess.get_open_error()`; `ERR_FILE_NOT_FOUND` on first launch is normal ([§3.1](#3-fileaccess--complete-api-tour)) |
| Save resets to defaults after an update | loader treats parse/version errors as "start fresh" | recovery ladder + migrations; fresh state only as the last rung ([§10.5](#10-atomic-writes-backups-and-corruption-detection), [§11](#11-save-versioning-and-migration-pipelines)) |
| Numbers wrong after load (`3` became `3.0`, int keys became strings) | JSON type loss | explicit casts in `from_dict`; `{x,y}` conventions for vectors ([§7.2](#7-json-saves--serialization-strategies)) |
| Migrated save reported corrupt on second launch | checksum not recomputed when writing back the migrated document | verify checksum pre-migration, recompute post-migration ([§11.3](#11-save-versioning-and-migration-pipelines)) |
| `CASCADE` deletes do nothing; orphan rows accumulate | SQLite FK enforcement off by default | `db.foreign_keys = true` **before** `open_db()`; assert `PRAGMA foreign_keys;` = 1 ([§12.2](#12-sqlite-with-godot-sqlite--setup-and-core-api)) |
| Batch inserts extremely slow | one auto-commit (and disk sync) per statement | wrap in `BEGIN;` … `COMMIT;` — expect 10-50× ([§14.4](#14-queries-bindings-and-transactions)) |
| Writes stop persisting, no errors anywhere | an early `return` left a transaction open; later writes join it, nothing commits | two-exit transaction structure or a `in_transaction(Callable)` wrapper ([§14.4](#14-queries-bindings-and-transactions)) |
| Query with a name containing `'` crashes or misbehaves | string-interpolated SQL | `query_with_bindings` with `?` placeholders, everywhere ([§14.1](#14-queries-bindings-and-transactions)) |
| Database file copied to another machine is stale or unreadable | `-wal` file left behind or separated | `PRAGMA wal_checkpoint(TRUNCATE)` before copying, or `backup_to()` ([§15.1](#15-operating-sqlite--wal-pragmas-migrations-backups)) |
| `SQLite` class not found in exported build | GDExtension binary missing for the target platform | verify `addons/godot-sqlite` exports; test the built binary early ([§12.1](#12-sqlite-with-godot-sqlite--setup-and-core-api)) |
| Random `database is locked` on Windows | antivirus/backup tool touching the file; no busy timeout | `PRAGMA busy_timeout = 5000;` at open ([§15.2](#15-operating-sqlite--wal-pragmas-migrations-backups)) |
| Two users with the same password have identical hashes | static app-wide salt | per-user random salt + iterated hashing; migrate on next login ([§17.3](#17-authentication-for-offline-apps)) |
| Supabase returns other users' rows in testing (or writes fail mysteriously) | RLS disabled, or policy missing `WITH CHECK` | enable RLS on every synced table with both clauses; test with two accounts ([§18.5](#18-cloud-sync-and-supabase)) |
| Sync retries hammer the API after an outage | no backoff | exponential backoff with jitter, honor 429/`Retry-After` ([§18.6](#18-cloud-sync-and-supabase)) |
| Window restored off-screen after unplugging a monitor | saved position applied without validation | validate against current screen rects, else OS placement ([§6.2](#6-configfile--the-settings-recipe)) |
| App unclosable after adding quit handling | `set_auto_accept_quit(false)` without ever calling `get_tree().quit()` | always quit after the close-time save completes ([§9.2](#9-savemanager-architecture)) |

---

## Exercises

Labs build on each other; do them in order inside a scratch project. "Acceptance" is what you must demonstrate; "Stretch" is optional depth.

### Lab 1 — File system explorer (60-90 min)

Build a debug panel that shows: the physical `user://` path, every file in it with size + modified time (`DirAccess` + `FileAccess.get_modified_time`), and buttons to open the folder (`OS.shell_open`) and create/delete a test file with full error reporting via `error_string()`.
**Acceptance:** panel works in the editor **and in an exported build**; deleting a locked/missing file shows the correct error name instead of crashing.
**Stretch:** show each file's SHA-256 (`FileAccess.get_sha256`) and flag files that changed since the panel opened.

### Lab 2 — Settings that survive anything (90 min)

Implement the [§6.2](#6-configfile--the-settings-recipe) `Settings` autoload for window size/position/mode, three volume buses and locale. Then sabotage it: delete `settings.cfg`, replace it with garbage bytes, remove single keys by hand.
**Acceptance:** all three sabotages produce defaults + one log warning — never a crash, never a dialog; volume sliders write at most one file per gesture (prove it by logging writes).
**Stretch:** validate saved window position against `DisplayServer` screen rects and demonstrate recovery from a "monitor unplugged" scenario.

### Lab 3 — Atomic save under fire (2-3 h) *(original course lab, expanded)*

Implement `save_game(data)` with the full [§10.2](#10-atomic-writes-backups-and-corruption-detection) pattern (temp → verify → backup → rename) plus the [§10.5](#10-atomic-writes-backups-and-corruption-detection) recovery ladder. Write a harness that saves in a tight loop while a second script kills the process at random intervals (`OS.kill(OS.get_process_id())` from a timer, or an external `taskkill`/`kill -9` loop).
**Acceptance:** after 100 random-kill cycles, the loader always recovers a complete, checksum-valid state — zero data loss beyond the in-flight save; a written log proves which rung recovered each time.
**Stretch:** add dated backup rotation with a cap of 7 and a test that proves pruning never deletes the newest backup.

### Lab 4 — Migration chain v1 → v4 (2-3 h) *(original course lab, expanded)*

Author a v1 fixture save (5 flat keys), then design v2 (adds a nested section), v3 (renames a field), v4 (removes two fields, moves one into a subsection — 12+ keys total). Implement the [§11.3](#11-save-versioning-and-migration-pipelines) pipeline with one pure function per step.
**Acceptance:** fixture files for v1-v3 all migrate to byte-identical v4 golden output (deterministic stringify); a v5 "future" file loads best-effort with a warning; migration code passes a "no I/O, no globals" review.
**Stretch:** property-test with 50 randomized v1 documents — migrated output always validates against a v4 schema-checking function.

### Lab 5 — SQLite inventory with integrity (3-4 h)

Using godot-sqlite: create the `accounts`/`items`/`inventario` triangle from [§13.2](#13-schema-design--the-relax-room-database) with FKs, CHECKs and the stacking UNIQUE constraint. Write the CRUD wrapper ([§14.2](#14-queries-bindings-and-transactions)), the upsert `grant_item` ([§14.3](#14-queries-bindings-and-transactions)), and a bulk seed of 1,000 items.
**Acceptance:** seeding runs inside one transaction and demonstrably ≥10× faster than without (print both timings); deleting an account cascades inventory but a catalog-item delete with owners fails loudly; `coins` can never go negative (show the CHECK rejection being handled).
**Stretch:** add the `schema_version` runner ([§15.3](#15-operating-sqlite--wal-pragmas-migrations-backups)) and ship one real migration (new column) proven against a pre-migration fixture database.

### Lab 6 — Corruption test suite (2-3 h)

Build the [§19.3](#19-testing-persistence) matrix as an automated suite (GUT, gdUnit4, or a bare `SceneTree` script): truncations, random noise, wrong-shape JSON, checksum tamper, missing files, zero-byte `.db`, stale `-wal`.
**Acceptance:** every matrix row asserts "no crash + correct recovery rung"; the fuzz-lite loop (100 random mutations) passes; suite runs headless via `godot --headless -s`.
**Stretch:** wire it into CI (see [Build and Export](BUILD_AND_EXPORT.md)) so a failing corruption test blocks the export job.

### Lab 7 — Local auth done honestly (2-3 h)

Implement [§17](#17-authentication-for-offline-apps): guest-first startup, register/login with per-user salt + iterated PBKDF2-style hashing, constant-time verify, generic failures with flat timing, and full account deletion including file artifacts.
**Acceptance:** two accounts with identical passwords store different hashes; timing of "no such user" vs "wrong password" is indistinguishable (measure it); after deletion, a filesystem sweep finds zero traces of the display name.
**Stretch:** add `hash_version` and demonstrate transparent re-hash-on-login migration from the legacy static-salt scheme.

### Lab 8 — Offline sync queue against a mock server (4-6 h) *(original course stretch, expanded)*

Implement the [§18.2](#18-cloud-sync-and-supabase) op log and drain loop against a mock: either a real free-tier Supabase project with RLS policies, or a local HTTP stub (a 30-line Python/Node server) that randomly fails 30% of requests.
**Acceptance:** operations replay in order; a request that succeeds server-side but crashes client-side before the queue delete is replayed harmlessly (idempotence proven); backoff timings logged and capped; killing connectivity mid-drain leaves the app fully functional.
**Stretch:** two simulated devices editing offline, then syncing — per-section LWW resolves without losing the non-conflicting edits, and the merged result flows through the normal atomic save path.

### Lab 9 — Persistence CI gate (90 min)

Wrap Labs 3-6 into the [§19.4](#19-testing-persistence) headless runner and a CI workflow: tests first, export job second, export blocked on red.
**Acceptance:** a deliberately introduced bug (comment out the checksum recompute after migration, [§11.3](#11-save-versioning-and-migration-pipelines)) turns the pipeline red with a readable failure message; reverting turns it green — demonstrate both runs.
**Stretch:** publish the JSONL test log as a CI artifact and add a job-summary table of pass/fail per corruption-matrix row.

---

## Further reading

**Official documentation first** — everything else is commentary.

- **Godot Docs — Saving games** (`docs.godotengine.org/en/stable/tutorials/io/saving_games.html`) — the canonical tutorial: JSON-per-line saves, the Persist-group pattern, `store_var` guidance. Read it alongside [§7](#7-json-saves--serialization-strategies)-[§8](#8-binary-and-resource-saves--fidelity-vs-security) and note where this module goes further (atomicity, migrations, checksums).
- **Godot Docs — File paths in Godot projects / Data paths** (`docs.godotengine.org/en/stable/tutorials/io/data_paths.html`) — authoritative per-OS `user://` locations and the `use_custom_user_dir` settings. The source for [§2](#2-the-virtual-file-system--res-vs-user).
- **Godot Docs — class references: `FileAccess`, `DirAccess`, `ConfigFile`, `JSON`, `ResourceSaver`, `ResourceLoader`, `HashingContext`, `Crypto`, `HTTPRequest`** — keep these open while coding; the security warning on `FileAccess.get_var` is worth reading verbatim.
- **godot-sqlite — 2shady4u/godot-sqlite (GitHub + AssetLib)** — README covers the full API (`query_with_bindings`, `create_table` schema dictionaries, `backup_to`, `export_to_json`), platform binaries, and export notes. The wiki's install page resolves most "works in editor, fails in export" issues.
- **SQLite — Write-Ahead Logging** (`sqlite.org/wal.html`) — the primary source for [§15.1](#15-operating-sqlite--wal-pragmas-migrations-backups): checkpoint modes, WAL-file safety rules, when WAL is *not* appropriate (network filesystems).
- **SQLite — PRAGMA statements, "How To Corrupt Your Database"** (`sqlite.org/pragma.html`, `sqlite.org/howtocorrupt.html`) — the corruption paper is the best 30-minute read in this module's bibliography; most of [§15](#15-operating-sqlite--wal-pragmas-migrations-backups)'s warnings trace to it.
- **Supabase Docs — REST API, Auth, Row Level Security** (`supabase.com/docs`) — PostgREST endpoint conventions, JWT flows, and RLS policy patterns including `WITH CHECK`. Prototype policies in the dashboard's SQL editor with two test users before writing any client code.
- **OWASP Password Storage Cheat Sheet** — the authoritative, regularly updated ranking of password-hashing choices (Argon2id > scrypt/bcrypt > PBKDF2) with concrete parameters; the context for [§17.3](#17-authentication-for-offline-apps)'s honesty.
- **DB Browser for SQLite** (`sqlitebrowser.org`) — free GUI for opening `user://relax_room.db` during development: inspect tables, run ad-hoc SQL, watch the mirror update after each save. Close it before running the app on Windows to avoid file locks, and remember what you learned about `-wal` files before copying anything from its folder.
- **GUT / gdUnit4** (GitHub: `bitwes/Gut`, `MikeSchulze/gdUnit4`) — the two mature Godot 4 test frameworks; both run headless with CI-friendly exit codes when the [§19.4](#19-testing-persistence) hand-rolled runner outgrows itself.
- **Sibling modules:** [Project Deep Dive](PROJECT_DEEP_DIVE.md) walks the shipped Relax Room save code end-to-end; [Build and Export](BUILD_AND_EXPORT.md) covers where `user://` lands in packaged builds and export filters; [Desktop Companion Performance](DESKTOP_COMPANION_PERFORMANCE.md) covers keeping autosave off the frame budget; [Autoload Safety](AUTOLOAD_SAFETY.md) governs the singleton architecture all managers here rely on. The course-wide [Glossary](00-GLOSSARY.md) and [Exercises index](99-EXERCISES/README.md) collect terms and labs across modules.

---

## Glossary

| Term | Definition |
|---|---|
| **ACID** | Atomicity, Consistency, Isolation, Durability — the transaction guarantees SQLite provides and naive file writing does not. |
| **Atomic write** | Save pattern that writes a complete temp file and renames it over the old one, so no crash instant leaves the only copy incomplete ([§10.2](#10-atomic-writes-backups-and-corruption-detection)). |
| **Autoload** | Godot singleton node instantiated at startup; the natural home for `SaveManager`, `LocalDatabase`, `Settings` ([§9.4](#9-savemanager-architecture)). |
| **Backoff (exponential, with jitter)** | Retry policy that doubles the wait after each failure and randomizes it, preventing request hammering and thundering herds ([§18.6](#18-cloud-sync-and-supabase)). |
| **Bound parameter** | A `?` placeholder in SQL filled from a values array, keeping data from ever being parsed as SQL ([§14.1](#14-queries-bindings-and-transactions)). |
| **CHECK constraint** | Column/row rule enforced by the database (`coins >= 0`); the last line of defense against impossible state ([§13.3](#13-schema-design--the-relax-room-database)). |
| **Checkpoint (WAL)** | Transfer of committed changes from the `-wal` file back into the main database file ([§15.1](#15-operating-sqlite--wal-pragmas-migrations-backups)). |
| **Checksum** | Hash of a payload stored beside it; detects corruption and casual tampering, not attackers ([§10.4](#10-atomic-writes-backups-and-corruption-detection)). |
| **ConfigFile** | Godot's INI-style file class whose values are full Variants; the right tool for settings ([§6](#6-configfile--the-settings-recipe)). |
| **CRDT** | Conflict-free Replicated Data Type — principled merge machinery for collaborative state; overkill for single-user sync ([§18.3](#18-cloud-sync-and-supabase)). |
| **Dirty flag** | Boolean marking unsaved changes; drained by the autosave timer instead of saving on every change ([§9.2](#9-savemanager-architecture)). |
| **Envelope** | The stable outer shape of a save document: `version`, `saved_at`, `checksum`, `data` ([§7.4](#7-json-saves--serialization-strategies)). |
| **Foreign key (FK)** | Column referencing another table's key; enforcement is **off by default** in SQLite ([§12.2](#12-sqlite-with-godot-sqlite--setup-and-core-api)). |
| **GDExtension** | Godot's native-extension mechanism; how godot-sqlite embeds SQLite ([§12.1](#12-sqlite-with-godot-sqlite--setup-and-core-api)). |
| **Guest mode** | Zero-friction anonymous local account (`auth_uid = "local"`), upgradeable in place ([§17.2](#17-authentication-for-offline-apps)). |
| **HMAC** | Keyed hash (`Crypto.hmac_digest`); building block of PBKDF2 and of tamper-evident checksums ([§17.3](#17-authentication-for-offline-apps)). |
| **Idempotent operation** | Safe to apply twice with the same result — the property that lets a sync queue replay after crashes ([§18.2](#18-cloud-sync-and-supabase)). |
| **LWW (Last-Write-Wins)** | Conflict resolution by newest timestamp; applied per section in Relax Room ([§18.3](#18-cloud-sync-and-supabase)). |
| **Migration (chain)** | Ordered, append-only, incremental transformations upgrading old data formats (save v1→vN, `schema_version` for SQL) ([§11](#11-save-versioning-and-migration-pipelines), [§15.3](#15-operating-sqlite--wal-pragmas-migrations-backups)). |
| **Offline-first** | Architecture where local storage is the source of truth and the network is an optional replica ([§18](#18-cloud-sync-and-supabase)). |
| **Op log** | Append-only record of operations (the `sync_queue` table) replayed to reach the cloud ([§18.2](#18-cloud-sync-and-supabase)). |
| **PBKDF2** | Password-Based Key Derivation Function 2 — salted, iterated HMAC that makes password guessing slow by design ([§17.3](#17-authentication-for-offline-apps)). |
| **PRAGMA** | SQLite per-connection configuration statement (`journal_mode`, `foreign_keys`, `busy_timeout`) ([§15.2](#15-operating-sqlite--wal-pragmas-migrations-backups)). |
| **res:// / user://** | Godot's virtual paths: read-only project bundle vs per-user writable data directory ([§2](#2-the-virtual-file-system--res-vs-user)). |
| **ResourceSaver / ResourceLoader** | Godot APIs persisting `Resource` objects (`.tres`/`.res`); for authored content only — loading untrusted files can execute embedded scripts ([§8](#8-binary-and-resource-saves--fidelity-vs-security)). |
| **RLS (Row Level Security)** | Postgres per-row policies (`USING`/`WITH CHECK`) that make Supabase's public anon key safe ([§18.5](#18-cloud-sync-and-supabase)). |
| **Salt** | Per-user random value mixed into password hashing so equal passwords produce different hashes ([§17.3](#17-authentication-for-offline-apps)). |
| **store_var / get_var** | Binary Variant serialization on `FileAccess`; full type fidelity; the `objects` flags are a code-execution risk on untrusted data ([§3.4](#3-fileaccess--complete-api-tour)). |
| **Upsert** | Insert-or-update in one statement via `ON CONFLICT ... DO UPDATE`, keyed on a UNIQUE constraint ([§14.3](#14-queries-bindings-and-transactions)). |
| **WAL (Write-Ahead Logging)** | SQLite journal mode appending commits to a `-wal` file; readers and the writer stop blocking each other ([§15.1](#15-operating-sqlite--wal-pragmas-migrations-backups)). |

---

*Course "Godot 4 in Production" — Module 08 · Relax Room case study (IFTS Projectwork 2026)*
*Previous: [Autoload Safety](AUTOLOAD_SAFETY.md) · Next: [Project Deep Dive](PROJECT_DEEP_DIVE.md) · Index: [Syllabus](00-SYLLABUS.md)*

