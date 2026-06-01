# Game Development Planning & Best Practices

> **Course module:** Godot 4 in Production
> **Position:** Phase 3 · Module 10
> **Prerequisites:** Modules 01-09; basic project management awareness.
> **Learning objectives:** pre-modification checklist; version control discipline; testing strategy (note: GdUnit4 removed, use play-mode + manual + headless export validation); refactoring patterns; technical debt tracking.
> **Estimated time:** 45-60 min reading · 120 min hands-on
> **Level:** competent
> **Last updated:** 2026-04-27
> **Note:** GdUnit4 testing framework was deprecated/removed; document current approaches.

## Guiding ideas

1. **Pre-modification checklist saves headaches.** "Did you commit before this experiment?" — yes or rollback impossible.
2. **Tests for game code: play-mode + manual + export validation.** No formal unit tests in mainstream Godot anymore.
3. **Technical debt is OK if tracked.** Untracked debt becomes legacy permanente.
4. **Refactoring before feature: pay debt before borrowing more.**

A comprehensive guide to planning modifications, avoiding common mistakes, managing technical debt, and running a successful game development project — from first commit to post-release maintenance.

---

## 1. The Golden Rule: Plan Before You Code

### Why Planning Matters

The most expensive bug is one that could have been avoided by thinking for 10 minutes before writing code.

```
Cost of fixing a bug:

  During Planning:     $1   (change a note)
  During Development:  $10  (rewrite code)
  During Testing:      $100 (find, fix, retest)
  After Release:       $1000 (hotfix, user complaints, reputation damage)

This ratio is well-documented in software engineering literature
(Barry Boehm's cost escalation model, 1981 — still relevant today).
```

### The Pre-Modification Checklist

**Before changing ANY code**, answer these questions:

```
□ 1. WHAT exactly am I changing?
     Write a one-sentence description.

□ 2. WHY am I changing it?
     Bug fix? New feature? Refactor? Performance?

□ 3. WHERE does this code connect to other code?
     What signals does it emit/listen to?
     What functions does it call?
     What files import/reference it?

□ 4. WHAT could break?
     List 3 things that might go wrong.
     If you can't think of any, you don't understand the code well enough.

□ 5. HOW will I verify it works?
     Write the test steps BEFORE making the change.
     "Run the app and click around" is NOT a test plan.

□ 6. CAN I revert easily?
     Did I commit my current work first?
     Am I on a feature branch?
```

### Real Example from Our Project

**Task:** Add `_exit_tree()` to `room_base.gd` to disconnect signals.

```
1. WHAT: Add _exit_tree() function with signal disconnections
2. WHY: Bug fix — signals stay connected after scene change (A1 in audit)
3. WHERE: room_base.gd connects to 3 SignalBus signals in _ready():
   - character_changed
   - decoration_placed
   - load_completed
4. WHAT COULD BREAK:
   - Typo in signal name → disconnect fails silently
   - Forgetting one signal → partial fix
   - Calling disconnect on already-disconnected signal → error
5. HOW TO VERIFY:
   - Change rooms back and forth 5 times
   - Check console for "signal already connected" warnings
   - Verify no orphaned signal handlers in Remote debugger
6. REVERT: Yes, committed before starting. On feature branch.
```

---

## 2. Version Control Best Practices

### Branching Strategy

For small teams (like ours), use a simplified GitFlow:

```
main ─────────────────────────────────────────────────── production
  │
  ├── Renan ──────────────────────────── team lead branch
  │     │
  │     ├── feature/exit-tree-fix ──── short-lived feature branch
  │     │      └── (merged back to Renan)
  │     │
  │     ├── feature/db-redesign ────── another feature
  │     │      └── (merged back to Renan)
  │     │
  │     └── (periodically merge Renan → main for releases)
  │
  ├── Cristian ── Cristian's work
  └── Elia ────── Elia's work
```

### Commit Message Conventions

```
Good commit messages:

  feat: add _exit_tree() to room_base.gd for signal cleanup
  fix: resolve FileDialog memory leak in music_panel.gd
  refactor: extract catalog loading into separate function
  docs: update AUDIT_REPORT with Section 16
  test: add unit tests for SaveManager migration chain
  chore: update CI pipeline to include test directory

Bad commit messages:

  "fixed stuff"
  "updates"
  "WIP"
  "asdfgh"
  "changed some things"
```

Format: `<type>: <what changed and why>`

| Type | When to Use |
|------|-------------|
| `feat` | New feature or functionality |
| `fix` | Bug fix |
| `refactor` | Code restructuring (no behavior change) |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `chore` | Build, CI, dependencies, tooling |
| `style` | Formatting, whitespace (no logic change) |

### The Golden Rules of Git

```
1. COMMIT OFTEN — Small, focused commits are easier to review and revert
2. PULL BEFORE PUSH — Always git pull before git push
3. NEVER COMMIT SECRETS — No passwords, API keys, .env files
4. WRITE MEANINGFUL MESSAGES — Your future self will thank you
5. ONE FEATURE PER BRANCH — Don't mix unrelated changes
6. DON'T FORCE PUSH main — Ever. For any reason.
7. REVIEW BEFORE MERGING — Even if it's your own code
```

### Handling Binary Assets in Git

Game projects have binary files (images, audio, fonts) that Git handles poorly:

```
Problem: Git stores full copies of binary files.
  100 MB of sprites × 50 revisions = 5 GB repository

Solutions:

1. Git LFS (Large File Storage)
   - Stores large files on a separate server
   - Git tracks pointers, not the full files
   - Setup: git lfs install && git lfs track "*.png" "*.wav"

2. .gitignore for generated files
   - Don't track .import files (Godot regenerates them)
   - Don't track __pycache__, .godot/imported/

3. Asset management convention
   - Keep source files (PSD, Aseprite) outside the repo
   - Only commit final exported sprites
```

### Merge Conflict Prevention

```
Prevention strategies:

1. Communicate: "I'm working on audio_manager.gd today"
2. Small commits: Merge frequently, don't let branches diverge
3. File ownership: One person per file when possible
4. Avoid reformatting: Don't reformat files you're not changing
5. .tscn conflicts: Only edit scenes in Godot (not text editor)
   Godot's .tscn format is text-based but fragile

When conflicts happen:
1. Don't panic
2. Read BOTH versions carefully
3. Understand what each change intended
4. Combine them manually (don't just pick "mine" or "theirs")
5. Test after resolving
```

---

## 3. Code Architecture Patterns

### Signal-Driven Architecture (Our Approach)

```
Component A ──emit──→ SignalBus ──notify──→ Component B
                                          → Component C
                                          → Component D

Benefits:
+ Components are decoupled (don't know about each other)
+ Easy to add new listeners without modifying emitters
+ Clean testing (emit signals manually)

Risks:
- "Invisible" connections (hard to trace without reading all connect() calls)
- Signal storms (one signal triggers another, which triggers another...)
- Memory leaks if signals aren't disconnected (_exit_tree!)
```

### Entity-Component System (ECS)

Used by some game engines (Unity, Bevy), not native to Godot:

```
Traditional OOP (Godot style):
  class Character extends CharacterBody2D:
    - has health
    - has movement
    - has animation
    - has inventory
    (One big class that does everything)

ECS:
  Entity: just an ID (no logic)
  Components: pure data (HealthComponent, PositionComponent)
  Systems: pure logic (MovementSystem, RenderSystem)

  Character = Entity #42
    + HealthComponent(hp=100)
    + PositionComponent(x=50, y=100)
    + SpriteComponent(texture="player.png")

  MovementSystem processes ALL entities with PositionComponent
  RenderSystem processes ALL entities with SpriteComponent
```

Godot doesn't use ECS natively, but the **Node composition** pattern achieves similar benefits:

```gdscript
# Instead of one giant character script, compose with child nodes:
CharacterBody2D
├── HealthComponent (Node, health.gd)
├── MovementComponent (Node, movement.gd)
├── AnimationComponent (Node, animation.gd)
└── InventoryComponent (Node, inventory.gd)

# Each component is independent and reusable
```

### Service Locator Pattern (Our Autoloads)

Our Autoloads act as a Service Locator — any script can access global services by name:

```gdscript
# Any script, anywhere in the tree:
SaveManager.save_game()      # Access the save service
AudioManager.play()          # Access the audio service
AppLogger.info("tag", "msg") # Access the logging service

# Benefits: Simple, direct access
# Risks: Global state can be hard to test
#        Hidden dependencies (not clear from function signature)
```

---

## 4. Testing in Game Development

### Types of Tests

```
┌─────────────────────────────────────────┐
│              Manual Playtesting          │  ← Slowest, most expensive
│    "Play the game and try to break it"  │     but catches UX issues
├─────────────────────────────────────────┤
│           Integration Tests              │  ← Test multiple systems together
│    "Does saving + loading preserve       │     Medium speed
│     decoration positions?"               │
├─────────────────────────────────────────┤
│              Unit Tests                  │  ← Fastest, cheapest
│    "Does snap_to_grid(15) return 16?"   │     Tests one function in isolation
└─────────────────────────────────────────┘
     Testing Pyramid — more at the bottom
```

### GdUnit4 (Our Testing Framework)

```gdscript
# test_helpers.gd
extends GdUnitTestSuite

func test_snap_to_grid_rounds_up() -> void:
    var result := Helpers.snap_to_grid(Vector2(15, 7))
    assert_that(result).is_equal(Vector2(16, 8))

func test_snap_to_grid_exact_values() -> void:
    var result := Helpers.snap_to_grid(Vector2(16, 8))
    assert_that(result).is_equal(Vector2(16, 8))

func test_array_to_vec2_valid() -> void:
    var result := Helpers.array_to_vec2([100.0, 200.0])
    assert_that(result).is_equal(Vector2(100, 200))

func test_array_to_vec2_empty() -> void:
    var result := Helpers.array_to_vec2([])
    assert_that(result).is_equal(Vector2.ZERO)
```

### What to Test (and What Not To)

```
ALWAYS test:
  ✓ Data transformations (snap_to_grid, coordinate conversion)
  ✓ Save/load round-trips (save → load → data matches)
  ✓ Migration chains (v1 save → v4 save without data loss)
  ✓ Edge cases (empty arrays, null values, boundary conditions)
  ✓ Business logic (does the shop calculate prices correctly?)

DON'T test:
  ✗ Engine internals (does Button.pressed signal work?)
  ✗ Trivial getters/setters (does get_name() return the name?)
  ✗ Visual appearance (is the button blue?) — use screenshots
  ✗ Third-party libraries (does SQLite work?) — trust the library
```

### Running Tests in CI/CD

```yaml
# .github/workflows/ci.yml
- name: Run GdUnit4 Tests
  run: |
    godot --headless \
      --path v1 \
      -s addons/gdUnit4/bin/GdUnitCmdTool.gd \
      --add "res://tests/" \
      --verbose
```

---

## 5. Common Beginner Mistakes

### Mistake 1: Not Planning Before Coding

```
Symptom: "I'll just start coding and figure it out"
Result:  Spaghetti code, dead ends, complete rewrites

Fix: Spend 20% of task time planning, 80% coding.
     Even a 5-minute sketch on paper saves hours.
```

### Mistake 2: Spaghetti Code / Tight Coupling

```gdscript
# BAD: Everything knows about everything
# music_panel.gd
func _on_play() -> void:
    var audio = get_node("/root/Main/AudioStreams/Player1")  # Fragile path!
    audio.play()
    get_node("/root/Main/UILayer/HUD/StatusLabel").text = "Playing"  # Why?!
    SaveManager.settings["last_played"] = Time.get_ticks_msec()  # Direct access!

# GOOD: Communicate through signals
func _on_play() -> void:
    SignalBus.track_play_pause_toggled.emit(true)
    # AudioManager handles playback (it listens to the signal)
    # SaveManager handles persistence (it listens too)
    # HUD updates itself (if it listens)
```

### Mistake 3: Ignoring Performance Until Too Late

```
Symptom: "It runs fine on my PC"
Result:  10 FPS on release, users complain, too late to fix

Fix: Profile regularly. Use Godot's built-in Profiler.
     Set a performance budget early:
     - Desktop companion: must run at 60 FPS focused, 15 FPS background
     - Must use < 200 MB RAM
     - Must start in < 3 seconds
```

### Mistake 4: Feature Creep

```
Symptom: "While I'm at it, let me also add..."
Result:  Never-ending development, unstable features, exhausted team

Fix: Use a strict feature list with priorities.
     For each idea ask: "Does this serve the core experience?"
     If no, add it to "Future Ideas" and move on.

Relax Room core: Room + Character + Decorations + Music
Everything else is secondary.
```

### Mistake 5: Not Using Version Control Properly

```
Symptom: "I'll commit when it's done"
Result:  Massive commits, impossible to revert, lost work

Fix: Commit every meaningful change.
     A commit should be: "one logical change that works"
     Not: "everything I did this week"
```

### Mistake 6: Hardcoding Values

```gdscript
# BAD: Magic numbers everywhere
func _process(delta: float) -> void:
    if position.y > 432:              # What's 432?
        velocity.x = 150              # Why 150?
        if health < 20:               # Is 20 the threshold?
            modulate = Color(1, 0, 0)  # Why red?

# GOOD: Named constants
const FLOOR_Y := 432.0
const WALK_SPEED := 150.0
const LOW_HEALTH_THRESHOLD := 20
const DAMAGE_COLOR := Color.RED

func _process(delta: float) -> void:
    if position.y > FLOOR_Y:
        velocity.x = WALK_SPEED
        if health < LOW_HEALTH_THRESHOLD:
            modulate = DAMAGE_COLOR
```

### Mistake 7: Not Disconnecting Signals

```gdscript
# BAD: Connect in _ready, never disconnect
func _ready() -> void:
    SignalBus.room_changed.connect(_on_room_changed)
    # When this node is freed, the signal still points to a dead object!
    # Result: errors, crashes, or silent memory leaks

# GOOD: Always disconnect in _exit_tree
func _exit_tree() -> void:
    if SignalBus.room_changed.is_connected(_on_room_changed):
        SignalBus.room_changed.disconnect(_on_room_changed)
```

This is such a common bug in our project that the audit report (A1) lists **12 scripts** that need `_exit_tree()` additions.

### Mistake 8: Not Documenting

```
Symptom: "The code is self-documenting"
Result:  Three months later, nobody (including you) understands the code

Fix: Document the WHY, not the WHAT.
     The code tells you WHAT it does. Comments tell you WHY.

# BAD comment (says WHAT):
health -= 10  # Subtract 10 from health

# GOOD comment (says WHY):
health -= 10  # Fall damage: 10 per floor height (max 3 floors = 30)
```

---

## 6. Refactoring Safely

### When to Refactor

```
Refactor when:
  ✓ You're about to add a feature and the current code makes it hard
  ✓ You've found a pattern repeated 3+ times → extract a function
  ✓ A function is longer than 50 lines → break it into smaller ones
  ✓ You don't understand code you wrote last month → simplify it

Don't refactor when:
  ✗ "The code works but I don't like the style"
  ✗ You're on a deadline
  ✗ You haven't written tests for the code
  ✗ Multiple team members are working on the same file
```

### The Refactoring Workflow

```
1. COMMIT current state (clean baseline to revert to)
2. WRITE TESTS for the current behavior (if not already)
3. MAKE ONE SMALL CHANGE
4. RUN TESTS — do they still pass?
5. COMMIT the change
6. REPEAT from step 3

Never refactor AND add features in the same commit.
```

### Safe Refactoring Patterns

```gdscript
# Pattern: Extract Function
# BEFORE (long function):
func process_save() -> void:
    var data := {}
    data["version"] = "4.0.0"
    data["room"] = {"id": current_room_id, "theme": current_theme}
    data["decorations"] = []
    for deco in decorations:
        data["decorations"].append({"id": deco.id, "pos": deco.position})
    var file := FileAccess.open("user://save.json", FileAccess.WRITE)
    file.store_string(JSON.stringify(data))
    # ... 40 more lines

# AFTER (extracted):
func process_save() -> void:
    var data := _build_save_data()
    _write_save_file(data)

func _build_save_data() -> Dictionary:
    return {
        "version": "4.0.0",
        "room": {"id": current_room_id, "theme": current_theme},
        "decorations": _serialize_decorations(),
    }
```

---

## 7. Technical Debt Management

### What Is Technical Debt?

Technical debt is the gap between "how the code is" and "how the code should be":

```
Clean code ────────────────── Actual code
     ↑                            ↑
     │                            │
  No debt                    Technical debt
                              (shortcuts, workarounds,
                               missing tests, TODO comments)
```

### Types of Technical Debt

| Type | Example from Our Project | Priority |
|------|--------------------------|----------|
| **Bugs** (must fix) | Missing _exit_tree() in 12 scripts (A1) | High |
| **Architecture** (should fix) | Characters table uses account_id as PK (C3) | Medium |
| **Performance** (could fix) | Logger synchronous flush (A12) | Medium |
| **Code quality** (nice to fix) | Magic numbers in some scripts | Low |
| **Documentation** (ongoing) | Missing inline comments | Low |

### Tracking Technical Debt

Our `AUDIT_REPORT.md` serves as a technical debt tracker:
- **A-series** (Architecture): Structural issues
- **C-series** (Correctness): Bugs and data issues
- Each item has severity and recommended fix

### When to Pay Off Debt

```
The Technical Debt Quadrant (Martin Fowler):

              Deliberate          Inadvertent
            ┌────────────────┬────────────────┐
  Reckless  │ "We don't have │ "What's a      │
            │  time for tests"│  signal bus?"  │
            ├────────────────┼────────────────┤
  Prudent   │ "Ship now, fix │ "Now we know   │
            │  the DB schema  │  how signals   │
            │  next sprint"   │  should work"  │
            └────────────────┴────────────────┘

Prudent+Deliberate = acceptable (plan to pay it off)
Reckless+Inadvertent = dangerous (you're learning the hard way)
```

---

## 8. Project Management for Small Teams

### Lightweight Agile for 5 People

Formal Scrum is overkill for a 5-person team. Use a lightweight version:

```
Weekly Cycle:

  Monday:   Quick planning (30 min)
            - What did we do last week?
            - What will we do this week?
            - Any blockers?

  Tue-Fri:  Work on tasks
            - Each person has 2-3 tasks for the week
            - Daily check-in via chat (not a meeting)
            - "Done" means tested and committed

  Friday:   Review (30 min)
            - Demo what was built
            - Quick code review
            - Update task board
```

### Task Prioritization

```
Priority Matrix:

              HIGH IMPACT        LOW IMPACT
            ┌────────────────┬────────────────┐
  EASY      │ DO FIRST        │ DO IF TIME     │
            │ Fix signal      │ Add more       │
            │ disconnects     │ music tracks   │
            ├────────────────┼────────────────┤
  HARD      │ DO SECOND       │ DON'T DO       │
            │ Redesign DB     │ Full Supabase   │
            │ schema          │ social features │
            └────────────────┴────────────────┘
```

### Communication Practices

```
For our team:

1. Code Reviews
   - Every merge request gets at least 1 review
   - Reviewer checks: does it work? Is it readable? Any bugs?
   - Not about style preferences — focus on correctness

2. Commit Messages
   - Follow conventional commits (feat/fix/refactor/docs)
   - Reference audit report items: "fix: resolve A1 — add _exit_tree to room_base"

3. Documentation
   - Update README when adding features
   - Comment non-obvious code
   - Keep AUDIT_REPORT as the living technical reference

4. When Stuck
   - Try for 30 minutes on your own
   - Then ask a teammate
   - Share your screen, explain what you tried
   - Document the solution for future reference
```

---

## 9. Post-Release Maintenance

### Versioning

Use **Semantic Versioning** (SemVer):

```
MAJOR.MINOR.PATCH

  MAJOR: Breaking changes (old saves won't work, API changed)
  MINOR: New features (backward compatible)
  PATCH: Bug fixes (backward compatible)

Examples:
  1.0.0 → First public release
  1.1.0 → Added new room themes
  1.1.1 → Fixed crash when switching rooms
  1.2.0 → Added inventory system
  2.0.0 → Redesigned save format (migration required)
```

### Save File Compatibility

```
The Save Migration Chain (our approach):

  v1.0.0 → v2.0.0 → v3.0.0 → v4.0.0

  Each version has a migration function:
  func _migrate_v3_to_v4(data: Dictionary) -> Dictionary:
      # Add new fields with defaults
      if "inventory" not in data:
          data["inventory"] = {"coins": 0, "items": []}
      # Remove deprecated fields
      data.erase("tools")
      data.erase("therapeutic")
      # Update version
      data["version"] = "4.0.0"
      return data

Benefits:
  - Users never lose their save data
  - New features have sensible defaults
  - Deprecated data is cleaned up
```

### Changelog Best Practices

```markdown
# Changelog

## [1.2.0] — 2026-04-15
### Added
- New "Sakura" room theme with cherry blossom colors
- Volume slider now shows percentage tooltip

### Fixed
- Fixed crash when switching rooms with active decorations
- Fixed music not resuming after closing settings panel

### Changed
- Reduced auto-save interval from 60s to 30s for better data safety
```

### Hotfix Process

```
When a critical bug is found in production:

1. Create hotfix branch from main: git checkout -b hotfix/crash-on-load main
2. Fix the bug (minimal change)
3. Test thoroughly
4. Merge to main AND to development branch
5. Tag a new patch version: git tag v1.1.1
6. Deploy immediately
```

---

## 10. Godot-Specific Best Practices

### Scene Organization

```
scenes/
├── menu/
│   └── main_menu.tscn     ← Menu scene
├── main/
│   └── main.tscn           ← Room scene (gameplay)
├── ui/
│   ├── music_panel.tscn
│   ├── deco_panel.tscn
│   ├── settings_panel.tscn
│   └── shop_panel.tscn
├── female-character.tscn    ← Character scenes
├── male-character.tscn
└── cat_void.tscn

scripts/
├── autoload/                ← Global singletons
├── rooms/                   ← Room-related logic
├── menu/                    ← Menu-related logic
├── ui/                      ← Panel scripts
├── systems/                 ← System scripts
└── utils/                   ← Utility functions

data/                        ← JSON catalogs (no scripts)
assets/                      ← Art, audio, fonts (no scripts)
```

### Signal Naming Conventions

```gdscript
# Godot convention: past tense for events that happened
signal health_changed(new_value: int)     # ✓ Something changed
signal player_died                         # ✓ Something happened
signal item_collected(item: String)        # ✓ Past tense

# Request signals: "requested" suffix
signal save_requested                      # ✓ Someone wants a save
signal track_changed(index: int)           # ✓ Track was changed

# Avoid imperative signals:
signal change_health(value: int)           # ✗ Sounds like a command
signal die                                 # ✗ Ambiguous
```

### Node Referencing

```gdscript
# GOOD: @onready (safe, evaluated at _ready time)
@onready var sprite := $Sprite2D

# GOOD: Find dynamically when needed
var panel := find_child("MusicPanel")

# BAD: Absolute paths (fragile, breaks when tree changes)
var sprite := get_node("/root/Main/Room/Character/Sprite2D")

# BAD: $ in _process (lookup every frame)
func _process(delta: float) -> void:
    $Sprite2D.rotation += delta  # Slow! Cache with @onready
```

### Resource Management

```gdscript
# DO: Preload resources used immediately
const CLICK_SOUND := preload("res://audio/sfx/click.wav")

# DO: Load resources on demand for conditional use
func _show_special_effect() -> void:
    var effect := load("res://effects/sparkle.tscn")
    add_child(effect.instantiate())

# DON'T: Load the same resource repeatedly
func _process(delta: float) -> void:
    var tex := load("res://icon.png")  # Loaded every frame! (cached by engine but wasteful)

# DON'T: Keep large resources in memory when not needed
# Use queue_free() or set to null when done
```

---

## 11. The Complete Modification Workflow

Putting it all together — here's the full workflow for making any change to the codebase:

```
┌─────────────────────────────────────────────────────────┐
│                MODIFICATION WORKFLOW                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. UNDERSTAND                                           │
│     ├── Read the relevant code                           │
│     ├── Trace signal connections                         │
│     ├── Check the audit report for related issues        │
│     └── Answer the Pre-Modification Checklist            │
│                                                          │
│  2. PREPARE                                              │
│     ├── Pull latest changes: git pull upstream Renan     │
│     ├── Create feature branch: git checkout -b feature/x │
│     ├── Make sure tests pass: run GdUnit4                │
│     └── Commit current state (clean baseline)            │
│                                                          │
│  3. IMPLEMENT                                            │
│     ├── Make the smallest possible change                │
│     ├── Test after each logical step                     │
│     ├── Commit each working step                         │
│     └── Write/update tests for new code                  │
│                                                          │
│  4. VERIFY                                               │
│     ├── Run all tests: gdUnit4 test suite                │
│     ├── Run the game: F5 in Godot                        │
│     ├── Follow your test plan from step 1                │
│     ├── Check console for warnings/errors                │
│     └── Check Remote Scene Tree for signal leaks         │
│                                                          │
│  5. SUBMIT                                               │
│     ├── Push your branch: git push                       │
│     ├── Create a Pull Request with description           │
│     ├── Request review from a teammate                   │
│     └── Address review feedback                          │
│                                                          │
│  6. MERGE                                                │
│     ├── Reviewer approves                                │
│     ├── Merge to team branch (Renan)                     │
│     ├── Delete feature branch                            │
│     └── Verify CI pipeline passes                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 12. Case Study: How Professional Studios Handle Changes

### AAA Studio Pipeline (simplified)

```
Game Director decides on a feature
         │
         ▼
Producer creates task in Jira/Linear
  - User story, acceptance criteria, time estimate
         │
         ▼
Lead Programmer assigns to developer
  - Technical design document (if complex)
         │
         ▼
Developer implements on feature branch
  - Daily commits
  - Unit tests
  - Integration tests
         │
         ▼
Code Review (peer + lead)
  - Does it meet acceptance criteria?
  - Performance impact?
  - Edge cases handled?
         │
         ▼
QA Testing
  - Dedicated testers play through the feature
  - Regression testing (did old features break?)
  - Bug reports filed in tracking system
         │
         ▼
Merge to development branch
         │
         ▼
Nightly build + automated testing
  - Build server compiles for all platforms
  - Automated tests run overnight
  - Results emailed to team in the morning
         │
         ▼
Release branch cut
  - Feature freeze (no new features)
  - Bug fixes only
  - Certification testing (console requirements)
         │
         ▼
Ship 🚀
```

### Indie Studio Pipeline (more relevant to us)

```
Idea discussed in team chat
         │
         ▼
Quick design note in issue tracker
  - "Add decoration rotation feature"
  - Rough mockup or description
         │
         ▼
Developer picks it up
  - Creates branch
  - Implements + tests
  - Self-review
         │
         ▼
Team review (async, on GitHub)
         │
         ▼
Merge + deploy
```

---

## 13. Mental Models for Game Development

### The Iceberg Model

```
What players see (10%):
┌─────────────────────────────────────┐
│  Pretty graphics, smooth gameplay,  │
│  fun music, satisfying interactions │
└─────────────────────────────────────┘
                  ___
                 / | \
                /  |  \
What devs build (90%):
              /    |    \
             / Save sys  \
            /  Error hdlg  \
           /  Performance    \
          /  Signal cleanup    \
         /  Data migration       \
        /  CI/CD pipeline          \
       /  Database schema            \
      /  Input handling                \
     /  Memory management                \
    /  Asset pipeline                      \
   /_________________________________________\
```

### The "Rule of Three"

```
First time:  Just do it (write the code)
Second time: Note the duplication, but don't refactor yet
Third time:  NOW extract a reusable function/pattern

Why? Premature abstraction is worse than duplication.
You need 3 examples to understand what the right abstraction is.
```

### YAGNI — You Aren't Gonna Need It

```
"But what if we need to support 100 rooms?"
"What if we need multiplayer?"
"What if we need a plugin system?"

If you don't need it TODAY, don't build it today.
Build what you need NOW. Refactor when requirements change.

Our project: We built for 4 rooms and 118 decorations.
If we need 1000 decorations later, THEN we optimize.
```

---

## 13. Checklist Pre-Commit per il Progetto

Prima di ogni `git commit`, verificate questi punti. Stampate questa lista e tenetela accanto al monitor.

```text
CODICE
[ ] Ho eseguito gdlint v1/scripts/ senza errori?
[ ] Ho eseguito gdformat --check v1/scripts/ senza errori?
[ ] Ho premuto F5 e il gioco parte senza errori rossi nel pannello Output?
[ ] I miei type hints sono completi? (variabili, parametri, return type)

DATI
[ ] Se ho modificato un file JSON (characters, decorations, rooms, tracks):
    - Le virgole sono corrette? (ultima voce di un oggetto NON ha virgola)
    - I percorsi sprite esistono? (res://assets/sprites/...)
    - Ho mantenuto la struttura esistente? (stessi campi degli altri oggetti)

GIT
[ ] Il messaggio di commit e' in italiano e descrive COSA e PERCHE'?
[ ] Non sto committando file sensibili? (.env, .db, credenziali)
[ ] Non sto committando la cartella .godot/ ? (e' nel .gitignore)
[ ] Ho fatto git diff per rivedere le modifiche prima del commit?

SEGNALI
[ ] Se ho aggiunto un connect() in _ready(), ho il corrispondente
    disconnect() in _exit_tree()?
[ ] Se emetto un nuovo segnale, l'ho dichiarato in signal_bus.gd?
```

---

## 14. Come Gestire un Blocco Tecnico

Quando incontrate un problema che non riuscite a risolvere, seguite questi 5 passi:

### Passo 1: Leggete l'Errore (Davvero)

Il pannello Output di Godot mostra errori con informazioni precise:

```text
res://scripts/rooms/room_base.gd:142 - Invalid call. Nonexistent function 'get_character' in base 'Nil'.
         ^^^^^^^^^^^^^^^^^^^^^^^^ ^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         File e riga esatti        |    Descrizione del problema
                                   Numero di riga
```

Copiate l'errore INTERO. Non riassumete — i dettagli contano.

### Passo 2: Riproducete il Problema

Se non riuscite a far accadere l'errore in modo prevedibile, non potete confermarne la risoluzione. Annotate:

- Quali passi esatti causano l'errore?
- Succede sempre o solo a volte?
- Succede solo con certi dati (un personaggio specifico, una decorazione specifica)?

### Passo 3: Isolate il Problema

Usate `print()` temporanei per restringere il punto esatto:

```gdscript
func _problematic_function(data: Dictionary) -> void:
    print("1 - Entrato nella funzione")  # Questo appare?
    var result := process(data)
    print("2 - Process completato: ", result)  # E questo?
    apply(result)
    print("3 - Apply completato")  # E questo?
```

Se vedete "1" e "2" ma non "3", il problema e' in `apply()`.

### Passo 4: Cercate Prima di Chiedere

1. **F1 in Godot**: apre la documentazione integrata della classe/funzione
2. **Ctrl+Shift+F**: cerca nel progetto se qualcun altro ha risolto lo stesso problema
3. **Google**: "godot 4 + messaggio di errore" — spesso il primo risultato su Reddit o GitHub risolve

### Passo 5: Chiedete Aiuto con Contesto

Se dopo 20 minuti non avete risolto, chiedete. Ma fornite SEMPRE:

- L'errore esatto (copia-incolla dal pannello Output)
- Il file e la riga dove si verifica
- Cosa stavate cercando di fare
- Cosa avete gia' provato

**Template messaggio**:

```text
PROBLEMA: [descrizione breve]
ERRORE: [copia-incolla errore dal pannello Output]
FILE: [percorso:riga]
HO PROVATO: [lista di cose provate]
CONTESTO: [cosa stavo facendo quando e' successo]
```

---

## 15. Anti-Pattern Specifici del Progetto Relax Room

Errori comuni che abbiamo visto (o rischiamo di vedere) in questo progetto specifico.

### Modificare project.godot a Mano

Il file `project.godot` e' gestito da Godot. Modificarlo con un editor di testo puo' corrompere il progetto.

**Regola**: Usate SEMPRE le impostazioni del progetto (`Project → Project Settings`) nell'editor Godot. L'unica eccezione e' la sezione `[autoload]` durante il setup iniziale.

### Aggiungere Asset senza Passare dal Catalogo

```text
SBAGLIATO:
1. Copio uno sprite in assets/sprites/
2. Lo carico direttamente nel codice con load("res://assets/sprites/nuova_sedia.png")

CORRETTO:
1. Copio lo sprite in assets/sprites/decorations/
2. Aggiungo una voce in data/decorations.json con id, nome, categoria, sprite_path
3. Il gioco lo trova automaticamente tramite GameManager.decoration_catalog
```

Il catalogo JSON e' il "registro" ufficiale dei contenuti. Se un asset non e' nel catalogo, per il gioco non esiste.

### Committare la Cartella .godot/

La cartella `.godot/` contiene cache importate, shader compilati, e file temporanei specifici della vostra macchina. E' gia' nel `.gitignore` — ma se fate `git add .` o `git add -A` potreste includerla per errore.

**Verificate sempre**: `git status` prima di `git commit`. Se vedete file `.godot/`, rimuoveteli dallo staging:

```bash
git reset HEAD .godot/
```

### Ignorare gli Warning del Pannello Output

Warning gialli NON sono "informazioni decorative". Ogni warning e' un potenziale bug:

- `Unused signal "nome_segnale"` → avete dichiarato un segnale che nessuno ascolta
- `The local variable "x" is declared but never used` → codice morto, rimuovetelo
- `Integer division` → state dividendo interi e perdendo la parte decimale

**Regola del progetto**: Zero warning nel pannello Output durante il gameplay. Ogni warning va o risolto o convertito in un `push_warning()` esplicito con motivazione.

---

*Study document for Relax Room — IFTS Projectwork 2026*
*Author: Renan Augusto Macena (System Architect & Project Supervisor)*

---

## Exercises

1. **Lab — pre-modification checklist application.** Apply the checklist to your next 3 commits.
2. **Lab — manual test harness.** Create a headless Godot export + script-driven test runner for save/load.
3. **Stretch — technical debt tracker.** Maintain a `TECH_DEBT.md` file; review monthly.

## Cross-links

- Module 11 — `BUILD_AND_EXPORT.md`: export validation.
- Module 09 — `PROJECT_DEEP_DIVE.md`: Relax Room project applies these.

## Local glossary

| Term | Definition |
|---|---|
| **Pre-modification checklist** | Steps before changing prod code. |
| **Technical debt** | Code shortcuts taken to ship. |
| **Refactoring** | Restructuring code without behavior change. |
| **Headless export** | Game exported without rendering for tests. |
| **GdUnit4** | Deprecated testing framework. |
