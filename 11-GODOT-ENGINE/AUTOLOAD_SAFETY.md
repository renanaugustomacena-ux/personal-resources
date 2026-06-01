# Autoload Safety — Init Order, Thread Safety, Assertions

> **Course module:** Godot 4 in Production
> **Position:** Phase 5 — New modules · Module 13 (NEW)
> **Prerequisites:** Modules 01-02; concept of singleton in OOP.
> **Learning objectives:** autoload init order; thread safety constraints; init-time assertions; alternatives (DI, sceneless utility classes); patterns for testing autoload-heavy code.
> **Estimated time:** 30-45 min reading · 90 min hands-on
> **Level:** competent → proficient
> **Last updated:** 2026-04-27

## Guiding ideas

1. **Autoload = global state. Use sparingly.** Each new autoload is a coupling point.
2. **Init order: alphabetical by node name in Project Settings.** Document dependencies; assert prerequisites.
3. **Autoloads are NOT thread-safe by default.** GDScript is single-threaded mostly; carefully document any thread access.
4. **Init-time assertions catch missing config.** `assert(api_key != "")` at autoload init prevents silent prod failures.
5. **Alternatives: DI via constructor injection, or scene-local manager.** Often better than autoload.

## Patterns

### Init-time assertions

```gdscript
# autoloads/Config.gd
extends Node

@export var api_url: String = ""
@export var api_key: String = ""

func _ready() -> void:
    assert(api_url != "", "Config.api_url must be set in inspector")
    assert(api_key != "", "Config.api_key must be set via env (CI export)")
    print("[Config] initialized: ", api_url)
```

### Dependency on other autoload

```gdscript
# autoloads/SaveManager.gd
extends Node

func _ready() -> void:
    # Config autoload comes first alphabetically; ok to access here
    assert(Config.api_url != "")
    load_save_file()
```

### Testing autoload code

- Autoload is hard to mock. Prefer making logic-heavy code in plain `RefCounted` classes; autoload becomes thin wrapper.
- Or: replace autoload at runtime via `add_child` of mock instance + remove original.

## Exercises

1. **Lab — autoload graph.** Map all autoloads in your project; draw dependency graph; verify alphabetical order matches.
2. **Lab — assert + recovery.** Add init-time assertions; deliberately misconfigure; verify clear error vs silent failure.
3. **Stretch — refactor.** Take one autoload, extract its logic to plain class, autoload becomes thin proxy.

## Self-assessment

1. Autoload init order: how determined?
2. Why autoload != thread-safe?
3. Init-time assertion: example.
4. When autoload alternatives are better.

## Primary reading

- Godot — Singletons (Autoload). https://docs.godotengine.org/en/stable/tutorials/scripting/singletons_autoload.html

## Cross-links

- Module 01 — `GODOT_ENGINE_STUDY.md`.
- Module 09 — `PROJECT_DEEP_DIVE.md`: Relax Room autoload graph.

## Local glossary

| Term | Definition |
|---|---|
| **Autoload** | Globally accessible singleton in Godot. |
| **Init order** | Alphabetical sequence at startup. |
| **Init-time assertion** | `assert()` in `_ready` to catch misconfig. |
| **Dependency injection** | Pass dependencies as constructor params. |
| **Thread-safe** | Safe to call from multiple threads concurrently. |
