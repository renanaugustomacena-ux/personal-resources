# Godot Engine 4.x — Comprehensive Study Guide

> **Course module:** Godot 4 in Production
> **Position in path:** Phase 1 — Foundations · Module 01 (see `00-SYLLABUS.md` §4)
> **Prerequisites:** programming basics; familiarity with at least one game engine concept (scene, asset, runtime).
> **Learning objectives:** explain Godot architecture (scene tree, server-based rendering); GDScript 2.0 features; signals as primary event mechanism; autoload (singleton) pattern; profiler workflow; common pitfalls.
> **Estimated time:** 90-120 min reading · 240-360 min hands-on
> **Level:** novice → competent (Dreyfus 1 → 3)
> **Last updated:** 2026-04-27
> **Pinned versions:** Godot 4.5; GDScript 2.0.

## Guiding ideas

1. **Godot is server-architectured under the hood.** RenderingServer, PhysicsServer, AudioServer — your scene tree is a thin layer above servers. Knowing this explains performance characteristics.
2. **Signals decouple sender from receiver.** Prefer signals over direct method calls for cross-scene communication; node A doesn't need to know about node B.
3. **Autoload (singleton) is global state — use sparingly.** Every autoload is implicit coupling; document each one's role and init order.
4. **`Performance.get_monitor` is your friend.** 15 FPS budget for desktop companion (low-CPU mode), 60 FPS for active interaction. Profiler before "optimization".
5. **GDScript is fast enough until proven otherwise.** Profile first; only rewrite hot loops in C# or via GDExtension if profile justifies.

A deep study of the Godot Engine: how it works internally, the GDScript language, the scene system, signals, resources, rendering, audio, input, UI, and everything you need to master Godot 4.5 development.

---

## 1. What Is Godot Engine?

### Overview

Godot is a **free and open-source** game engine released under the MIT license. Unlike Unity or Unreal, Godot has:
- **No royalties** — You keep 100% of your revenue
- **No subscription** — Free forever
- **Full source code** — You can modify the engine itself
- **Lightweight** — The editor is ~40MB (Unity is ~2GB, Unreal is ~40GB)

### Brief History

| Year | Milestone |
|------|-----------|
| 2007 | Juan Linietsky and Ariel Manzur start developing Godot internally |
| 2014 | Open-sourced under MIT license (v1.0) |
| 2016 | Godot 2.0 — visual scripting, improved 2D |
| 2018 | Godot 3.0 — OpenGL ES 3.0 renderer, PBR, GDNative |
| 2023 | Godot 4.0 — Vulkan renderer, GDScript 2.0, complete rewrite |
| 2024 | Godot 4.3 — Stability improvements, .NET 8 |
| 2025 | Godot 4.5 — Our project's version. GL Compatibility improvements, performance |

### Why Godot for Relax Room?

1. **2D-first design** — Godot's 2D engine is native, not a layer on top of 3D (unlike Unity)
2. **Pixel art friendly** — Built-in nearest-neighbor filtering, pixel-perfect rendering
3. **Lightweight** — Perfect for a desktop companion that runs alongside other apps
4. **GDScript** — Python-like scripting language, beginner-friendly
5. **Signal system** — Built-in observer pattern, ideal for decoupled architecture
6. **Free** — No licensing cost for an academic project

---

## 2. Engine Architecture

### The Layer Cake

Godot is built in layers. Understanding these layers helps you understand why things work the way they do:

```
┌─────────────────────────────────────────────┐
│           YOUR GAME (GDScript)              │  ← You write code here
├─────────────────────────────────────────────┤
│           SCENE SYSTEM                      │  ← Nodes, Scenes, SceneTree
│           (High-level API)                  │
├─────────────────────────────────────────────┤
│           SERVERS                           │  ← Low-level engines
│  RenderingServer │ PhysicsServer2D/3D       │
│  AudioServer     │ NavigationServer2D/3D    │
│  DisplayServer   │ InputMap                 │
├─────────────────────────────────────────────┤
│           CORE                              │  ← Memory, math, IO
│  Object │ Variant │ StringName │ Callable   │
├─────────────────────────────────────────────┤
│           OS LAYER                          │  ← Platform abstraction
│  Windows │ macOS │ Linux │ Web │ Android    │
└─────────────────────────────────────────────┘
```

### Servers: The Real Engine

The **scene system** (Nodes, Scenes) is actually optional — it's a convenience layer built on top of **Servers**. The Servers are the real engine:

| Server | Responsibility |
|--------|----------------|
| `RenderingServer` | All graphics: sprites, viewports, canvas items, materials, shaders |
| `PhysicsServer2D` | 2D collision detection, rigid bodies, areas, raycasting |
| `PhysicsServer3D` | 3D physics (not used in our project) |
| `AudioServer` | Audio buses, effects, mixing, volume control |
| `DisplayServer` | Windows, monitors, screen info, clipboard, mouse cursor |
| `NavigationServer2D` | Pathfinding, navigation meshes, avoidance |
| `InputMap` | Keyboard/mouse/gamepad mapping to logical actions |

**Why this matters:** When you create a `Sprite2D` node, it's really just a convenient wrapper that calls `RenderingServer` functions internally. You could bypass nodes entirely and talk to servers directly (for maximum performance), but nodes make development much easier.

### The Main Loop

Every frame, Godot runs a main loop:

```
┌─────────────────────────────────────────────┐
│                 MAIN LOOP                    │
│                                              │
│  1. Process Input Events                     │
│     → _input() and _unhandled_input()        │
│                                              │
│  2. Physics Step (fixed timestep, 60 Hz)     │
│     → _physics_process(delta)                │
│     → PhysicsServer2D.step()                 │
│     → Collision detection & resolution       │
│                                              │
│  3. Idle Step (variable timestep)            │
│     → _process(delta)                        │
│     → Tween updates                          │
│     → Timer updates                          │
│                                              │
│  4. Rendering                                │
│     → RenderingServer draws everything       │
│     → Canvas layers sorted by z_index        │
│     → Viewport compositing                   │
│                                              │
│  5. Swap Buffers                             │
│     → Display the rendered frame             │
└─────────────────────────────────────────────┘
```

The `SceneTree` is Godot's implementation of `MainLoop`. It handles all the node lifecycle management, signal dispatching, and group processing automatically.

---

## 3. The Node System

### Everything Is a Node

In Godot, **everything** in your game is a Node. A Node is the smallest building block:

```
Node (base class)
├── Can have a name
├── Can have children (tree structure)
├── Has lifecycle callbacks (_ready, _process, etc.)
├── Can be in groups
├── Can be paused/unpaused
└── Can process every frame or every physics tick
```

### The Node Hierarchy

```
Node
├── CanvasItem (anything that draws in 2D)
│   ├── Node2D (2D game objects)
│   │   ├── Sprite2D
│   │   ├── AnimatedSprite2D
│   │   ├── CharacterBody2D
│   │   ├── RigidBody2D
│   │   ├── StaticBody2D
│   │   ├── Area2D
│   │   ├── Camera2D
│   │   ├── TileMapLayer
│   │   └── ...
│   │
│   └── Control (UI elements)
│       ├── Button
│       ├── Label
│       ├── TextEdit
│       ├── HSlider
│       ├── PanelContainer
│       ├── VBoxContainer
│       ├── HBoxContainer
│       ├── ScrollContainer
│       └── ...
│
├── Node3D (3D objects — not used in our project)
│
└── Other base types
    ├── Timer
    ├── AudioStreamPlayer
    ├── HTTPRequest
    └── AnimationPlayer
```

### Key Node Types Used in Relax Room

| Node Type | What It Does | Where We Use It |
|-----------|-------------|-----------------|
| `Node2D` | Base for 2D game objects | Room, character, decorations |
| `Sprite2D` | Displays a texture | Background layers, decorations |
| `AnimatedSprite2D` | Displays animated sprites | Character walk/idle |
| `CharacterBody2D` | Physics body with `move_and_slide()` | Player character |
| `StaticBody2D` | Immovable collision body | Room boundaries |
| `CollisionShape2D` | Defines collision area | Character hitbox, room walls |
| `PanelContainer` | UI panel with background | All 4 panels |
| `VBoxContainer` | Vertical layout | Panel contents |
| `HBoxContainer` | Horizontal layout | Transport controls, volume row |
| `Button` | Clickable button | HUD, menu, transport |
| `Label` | Text display | Track name, titles |
| `HSlider` | Horizontal slider | Volume control |
| `CheckButton` | Toggle switch | Ambience toggles |
| `ScrollContainer` | Scrollable area | Ambience list, shop grid |
| `CanvasLayer` | Independent rendering layer | UI overlay (layer=10) |
| `AudioStreamPlayer` | Plays audio | Music player (dual players) |
| `Timer` | Fires after delay | Menu character animation |
| `ColorRect` | Colored rectangle | Wall, floor, baseboard |
| `Control` | Base UI node | DropZone overlay |

---

## 4. The Scene System

### What Is a Scene?

A Scene is a **reusable tree of nodes** saved as a `.tscn` file. Think of it as a template:

```
Scene file: main_menu.tscn
│
├── MainMenu (Node2D)
│   ├── ForestBackground (Node2D)
│   ├── MenuCharacter (Node2D)
│   ├── LoadingScreen (ColorRect)
│   └── UILayer (CanvasLayer)
│       └── ButtonContainer (VBoxContainer)
│           ├── NuovaPartitaBtn (Button)
│           ├── CaricaPartitaBtn (Button)
│           ├── OpzioniBtn (Button)
│           └── EsciBtn (Button)
```

**Analogy:** If nodes are LEGO bricks, scenes are pre-built LEGO sets. You can make a "car" set once, then stamp out 10 copies.

### Scene Instancing

You can put scenes inside other scenes:

```gdscript
# Method 1: preload (compile-time, cached)
var character_scene := preload("res://scenes/female-character.tscn")

# Method 2: load (runtime, not cached)
var character_scene := load("res://scenes/female-character.tscn")

# Create an instance (like pressing "duplicate" on a template)
var character := character_scene.instantiate()

# Add to the tree so it becomes active
add_child(character)
```

**preload vs load:**
| | `preload()` | `load()` |
|--|------------|---------|
| When | At script compile time | At runtime when the line executes |
| Speed | Instant (already in memory) | May cause a brief stall |
| Use for | Things you always need | Things you might need conditionally |
| Syntax | `preload("res://...")` — path must be literal | `load(path_variable)` — path can be dynamic |

### The Scene Tree

When your game runs, all active scenes form a single tree called the **SceneTree**:

```
SceneTree
└── root (Window)
    ├── SignalBus (Autoload)
    ├── AppLogger (Autoload)
    ├── GameManager (Autoload)
    ├── SaveManager (Autoload)
    ├── LocalDatabase (Autoload)
    ├── AudioManager (Autoload)
    ├── SupabaseClient (Autoload)
    ├── PerformanceManager (Autoload)
    │
    └── Main (current scene)
        ├── WallRect
        ├── FloorRect
        ├── Room
        │   ├── Decorations
        │   └── Character (instanced scene)
        └── UILayer
            ├── DropZone
            └── HUD
```

### Scene Lifecycle

Every node goes through a lifecycle when entering and leaving the tree:

```
┌─────────────────────┐
│ Node Created         │  var node = Node.new()
│ (not in tree yet)    │  — exists in memory but doesn't process
└─────────┬───────────┘
          │ add_child(node)
          ▼
┌─────────────────────┐
│ _enter_tree()        │  Called when node enters the SceneTree
│                      │  — The node is now in the tree
│                      │  — Children may not be ready yet
└─────────┬───────────┘
          │ (after all children enter)
          ▼
┌─────────────────────┐
│ _ready()             │  Called ONCE when node AND all children are ready
│                      │  — Safe to access children: $ChildName
│                      │  — Connect signals here
│                      │  — Initialize state here
│                      │  — @onready vars are set just before this
└─────────┬───────────┘
          │ (every frame)
          ▼
┌─────────────────────┐
│ _process(delta)      │  Called every frame (60 FPS = 60 times/sec)
│ _physics_process()   │  Called at fixed rate (60 Hz default)
│ _input(event)        │  Called for every input event
└─────────┬───────────┘
          │ remove_child(node) or queue_free()
          ▼
┌─────────────────────┐
│ _exit_tree()         │  Called when node leaves the SceneTree
│                      │  — Disconnect signals here
│                      │  — Clean up resources
│                      │  — Stop timers/tweens
└─────────┬───────────┘
          │ queue_free()
          ▼
┌─────────────────────┐
│ Node Freed           │  Memory is released
│                      │  — Happens at end of frame (not immediately)
└─────────────────────┘
```

### _process vs _physics_process

```
_process(delta):
  - Called every RENDERED frame
  - delta varies (0.016s at 60fps, 0.033s at 30fps)
  - Use for: visual updates, animations, UI, non-physics movement
  - Our project: parallax background, tween animations

_physics_process(delta):
  - Called at FIXED intervals (60 Hz default, configurable)
  - delta is always the same (0.01666s at 60 Hz)
  - Use for: physics, collision, CharacterBody2D.move_and_slide()
  - Our project: character movement (WASD)
```

**Why the distinction?** If your game drops to 30 FPS, `_physics_process` still runs 60 times per second (it runs multiple times per frame to catch up). This ensures physics is deterministic regardless of frame rate. `_process` only runs once per rendered frame.

---

## 5. GDScript Language

### What Is GDScript?

GDScript is Godot's built-in scripting language. It's designed specifically for game development:

- **Python-like syntax** — Indentation-based, readable
- **Tightly integrated** — Direct access to all engine APIs
- **Gradually typed** — Optional static typing (recommended)
- **Compiled to bytecode** — Not interpreted line-by-line like Python

### Basic Syntax

```gdscript
# This is a comment

## This is a documentation comment (shown in editor tooltips)

# Every .gd file is a class
extends Node2D            # Inheritance
class_name MyClassName     # Optional: register a global class name

# Constants
const MAX_SPEED := 200.0
const GRAVITY := 9.8

# Enums
enum Direction { UP, DOWN, LEFT, RIGHT }
enum State { IDLE, WALKING, RUNNING }

# Member variables
var health: int = 100                    # Explicitly typed
var speed := 150.0                       # Type inferred from value (:=)
var name: String                         # Typed, default is ""
var position_data: Dictionary = {}       # Typed Dictionary
var items: Array[String] = []            # Typed Array (Godot 4+)

# Exported variables (editable in the Inspector)
@export var max_health: int = 100
@export var damage: float = 10.0
@export_range(0, 100) var volume: int = 50
@export_file("*.json") var config_path: String
@export_enum("Easy", "Normal", "Hard") var difficulty: int

# @onready — initialized just before _ready()
@onready var sprite: Sprite2D = $Sprite2D
@onready var anim: AnimatedSprite2D = $AnimatedSprite2D
@onready var collision: CollisionShape2D = $CollisionShape2D
```

### Variables and Types

```gdscript
# Basic types
var integer: int = 42
var floating: float = 3.14
var boolean: bool = true
var text: String = "Hello"
var nothing = null                  # null type

# Godot-specific types
var vec2: Vector2 = Vector2(100, 200)       # 2D position/direction
var vec2i: Vector2i = Vector2i(10, 20)      # Integer vector (pixels)
var vec3: Vector3 = Vector3(1, 2, 3)        # 3D (not used in 2D games)
var color: Color = Color(1, 0, 0, 1)        # RGBA (red)
var color2: Color = Color.RED               # Named color
var rect: Rect2 = Rect2(0, 0, 100, 50)     # Rectangle (x, y, w, h)
var transform: Transform2D                   # 2D transformation matrix

# Collections
var array: Array = [1, "two", 3.0]          # Dynamic array (any type)
var typed_array: Array[int] = [1, 2, 3]     # Typed array (Godot 4+)
var dict: Dictionary = {"key": "value"}      # Hash map
var packed_str: PackedStringArray = ["a", "b"]  # Memory-efficient

# Resources
var texture: Texture2D                       # Image data
var scene: PackedScene                       # Scene template
var audio: AudioStream                       # Sound/music data
```

### Functions

```gdscript
# Basic function
func greet(name: String) -> void:
    print("Hello, " + name)

# Function with return value
func add(a: float, b: float) -> float:
    return a + b

# Default parameters
func create_enemy(type: String = "goblin", level: int = 1) -> void:
    pass

# Static function (can be called without an instance)
static func calculate_damage(attack: float, defense: float) -> float:
    return maxf(attack - defense, 0.0)

# Lambda (anonymous function)
var double := func(x: int) -> int: return x * 2
var result := double.call(5)  # result = 10

# Lambdas are commonly used with signals:
button.pressed.connect(func(): print("Button clicked!"))
```

### Control Flow

```gdscript
# If/elif/else
if health <= 0:
    die()
elif health < 25:
    show_warning()
else:
    continue_playing()

# Match (like switch/case but more powerful)
match direction:
    Direction.UP:
        velocity.y = -speed
    Direction.DOWN:
        velocity.y = speed
    Direction.LEFT, Direction.RIGHT:
        # Multiple values in one branch
        velocity.x = speed if direction == Direction.RIGHT else -speed
    _:
        # Default case (underscore)
        velocity = Vector2.ZERO

# For loops
for i in range(10):           # 0 to 9
    print(i)

for item in inventory:         # Iterate array
    print(item)

for key in dict:               # Iterate dictionary keys
    print(key, " = ", dict[key])

for i in 5:                    # Shorthand for range(5)
    print(i)

# While loop
while health > 0:
    take_damage(1)
```

### Annotations

Annotations are Godot 4's replacement for keywords like `export` and `onready` from Godot 3:

```gdscript
# @export — Makes variable editable in Inspector
@export var speed: float = 100.0

# @export with hints
@export_range(0, 100, 1) var health: int = 100      # Slider, min/max/step
@export_enum("Warrior", "Mage", "Rogue") var class_type: int
@export_file("*.json") var data_path: String          # File picker
@export_dir var save_directory: String                 # Directory picker
@export_multiline var description: String              # Multi-line text box
@export_color_no_alpha var tint: Color                 # Color without alpha
@export_group("Movement")                              # Group in Inspector
@export var walk_speed: float = 100.0
@export var run_speed: float = 200.0

# @onready — Variable is set just before _ready() is called
@onready var label: Label = $UI/Label
@onready var sprite := $Sprite2D as Sprite2D

# @tool — Script runs in the editor (not just at runtime)
@tool
extends Node2D

# @icon — Custom icon for the node in the editor
@icon("res://icons/custom.svg")
extends Node
```

### Static Typing

Godot 4 encourages static typing for better performance and editor support:

```gdscript
# Untyped (works but not recommended)
var speed = 100
func get_name():
    return "Player"

# Typed (recommended)
var speed: float = 100.0
func get_name() -> String:
    return "Player"

# Inferred typing (use := to infer from the value)
var speed := 100.0          # Inferred as float
var name := "Player"        # Inferred as String
var pos := Vector2.ZERO     # Inferred as Vector2

# Why use static typing?
# 1. Editor autocomplete works better
# 2. Errors are caught at compile time, not runtime
# 3. Slight performance improvement (GDScript can optimize)
# 4. Code is more readable and self-documenting
```

### Signals

Signals are Godot's implementation of the **Observer pattern**:

```gdscript
# Declaring a signal
signal health_changed(new_health: int)
signal died
signal item_collected(item_id: String, amount: int)

# Emitting a signal
func take_damage(amount: int) -> void:
    health -= amount
    health_changed.emit(health)  # Notify all listeners
    if health <= 0:
        died.emit()

# Connecting to a signal (in another script)
func _ready() -> void:
    # Method reference connection (recommended)
    player.health_changed.connect(_on_health_changed)
    player.died.connect(_on_player_died)

    # Lambda connection (for simple reactions)
    button.pressed.connect(func(): print("Clicked!"))

    # One-shot connection (disconnects after first emission)
    player.died.connect(_on_died, CONNECT_ONE_SHOT)

# Signal handler
func _on_health_changed(new_health: int) -> void:
    health_bar.value = new_health

# Disconnecting (important in _exit_tree!)
func _exit_tree() -> void:
    if player.health_changed.is_connected(_on_health_changed):
        player.health_changed.disconnect(_on_health_changed)
```

### The Signal Bus Pattern

Instead of connecting signals directly between nodes (which creates tight coupling), Relax Room uses a **Signal Bus** — a global autoload that holds all signals:

```gdscript
# signal_bus.gd (Autoload)
extends Node

# Any script can emit these, any script can listen
signal room_changed(room_id: String, theme: String)
signal decoration_placed(item_id: String, position: Vector2)
signal save_requested

# --------------------
# room_base.gd (emits)
func place_decoration(id: String, pos: Vector2) -> void:
    SignalBus.decoration_placed.emit(id, pos)

# --------------------
# save_manager.gd (listens)
func _ready() -> void:
    SignalBus.decoration_placed.connect(_on_decoration_placed)

func _on_decoration_placed(id: String, pos: Vector2) -> void:
    _save_decoration(id, pos)
```

**Benefits:**
- Components don't need references to each other
- Components can be added/removed without breaking other components
- Testing is easier (you can emit signals manually)
- Clear overview of all events in one file

---

## 6. The Resource System

### Nodes vs Resources

| | Nodes | Resources |
|--|-------|-----------|
| Purpose | Game objects in the scene tree | Data containers |
| Lifecycle | Created, added to tree, freed | Loaded into memory, shared |
| Instances | Each node is unique | Resources can be shared between nodes |
| Memory | Freed with `queue_free()` | Reference-counted (auto-freed) |
| Examples | Sprite2D, Button, Timer | Texture2D, AudioStream, PackedScene |

### Loading Resources

```gdscript
# preload — at compile time (must use literal string)
const ICON := preload("res://assets/icon.png")

# load — at runtime (can use variables)
var texture := load("res://assets/" + filename) as Texture2D

# ResourceLoader — async loading (won't freeze the game)
ResourceLoader.load_threaded_request("res://scenes/big_level.tscn")
# ... later ...
var scene = ResourceLoader.load_threaded_get("res://scenes/big_level.tscn")
```

### Resource Paths

```
res://  → Project root (read-only after export)
         Used for: game assets, scenes, scripts, data files
         Example: res://assets/sprites/character.png

user:// → User data directory (read-write)
         Used for: save files, settings, logs, imported tracks
         Windows: %APPDATA%/Godot/app_userdata/Relax Room/
         Linux:   ~/.local/share/godot/app_userdata/Relax Room/
         macOS:   ~/Library/Application Support/Godot/app_userdata/Relax Room/
```

### Custom Resources

You can create your own Resource types for structured data:

```gdscript
# decoration_data.gd
class_name DecorationData
extends Resource

@export var id: String
@export var name: String
@export var category: String
@export var sprite_path: String
@export var scale: float = 1.0
@export var placement: String = "floor"

# Our project uses JSON dictionaries instead, but custom Resources
# are great for editor-heavy workflows where you want Inspector editing
```

---

## 7. File I/O

### FileAccess

```gdscript
# Writing a file
func save_json(path: String, data: Dictionary) -> void:
    var file := FileAccess.open(path, FileAccess.WRITE)
    if file == null:
        push_error("Cannot write to: %s (error: %s)" % [path, FileAccess.get_open_error()])
        return
    file.store_string(JSON.stringify(data, "\t"))
    # file is auto-closed when it goes out of scope (reference counting)

# Reading a file
func load_json(path: String) -> Dictionary:
    if not FileAccess.file_exists(path):
        return {}
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        return {}
    var text := file.get_as_text()
    var json := JSON.new()
    if json.parse(text) != OK:
        push_error("JSON parse error: %s" % json.get_error_message())
        return {}
    return json.data if json.data is Dictionary else {}
```

### DirAccess

```gdscript
# List files in a directory
func list_files(path: String) -> PackedStringArray:
    var dir := DirAccess.open(path)
    if dir == null:
        return PackedStringArray()
    var files: PackedStringArray = []
    dir.list_dir_begin()
    var filename := dir.get_next()
    while filename != "":
        if not dir.current_is_dir():
            files.append(filename)
        filename = dir.get_next()
    return files

# Create directories
DirAccess.make_dir_recursive_absolute("user://saves/backup")

# Check existence
DirAccess.dir_exists_absolute("user://saves")
FileAccess.file_exists("user://save_data.json")
```

---

## 8. The Input System

### Input Map

Godot uses an **action-based** input system. You define named actions, then check for them in code:

```
# In project.godot [input] section or via Project Settings → Input Map:
toggle_music = Spacebar
move_left = A, Left Arrow
move_right = D, Right Arrow
move_up = W, Up Arrow
move_down = S, Down Arrow
```

```gdscript
# Checking input in code
func _physics_process(delta: float) -> void:
    var direction := Vector2.ZERO
    direction.x = Input.get_axis("move_left", "move_right")
    direction.y = Input.get_axis("move_up", "move_down")
    velocity = direction.normalized() * speed
    move_and_slide()
```

### Input Processing Order

```
1. _input(event)              ← First chance to handle input
   └── If not handled (set_input_as_handled()):
2. _gui_input(event)          ← UI Controls get the event
   └── If not handled:
3. _shortcut_input(event)     ← Shortcut processing
   └── If not handled:
4. _unhandled_key_input(event) ← Key-only fallback
   └── If not handled:
5. _unhandled_input(event)    ← Final fallback
```

**Rule of thumb:**
- Use `_input()` for global shortcuts (pause menu, debug keys)
- Use `_unhandled_input()` for gameplay input (movement, actions)
- This way, UI buttons consume clicks before they reach gameplay code

### InputEvent Hierarchy

```
InputEvent (base)
├── InputEventKey           ← Keyboard
├── InputEventMouseButton   ← Mouse clicks
├── InputEventMouseMotion   ← Mouse movement
├── InputEventJoypadButton  ← Gamepad buttons
├── InputEventJoypadMotion  ← Gamepad sticks/triggers
├── InputEventScreenTouch   ← Touch screen
├── InputEventScreenDrag    ← Touch drag
└── InputEventAction        ← Generated from Input Map
```

---

## 9. The UI System (Control Nodes)

### Layout System

Godot's UI uses a system of **anchors**, **margins/offsets**, and **containers**:

```
Anchors: Where the control is "pinned" relative to its parent
  (0,0) ─────────── (1,0)
    │                   │
    │     Control       │
    │                   │
  (0,1) ─────────── (1,1)

Example: Full screen overlay
  anchor_left = 0, anchor_top = 0
  anchor_right = 1, anchor_bottom = 1
  → Control stretches to fill parent

Example: Bottom-right corner
  anchor_left = 1, anchor_top = 1
  anchor_right = 1, anchor_bottom = 1
  → Control sits in bottom-right corner
```

### Container Nodes

Containers automatically arrange their children:

| Container | Layout | Use Case |
|-----------|--------|----------|
| `VBoxContainer` | Vertical stack | Panel contents, menu buttons |
| `HBoxContainer` | Horizontal row | Transport controls, volume slider |
| `GridContainer` | Grid | Shop item grid |
| `MarginContainer` | Adds padding | Panel outer margins |
| `ScrollContainer` | Scrollable area | Long lists, ambience toggles |
| `CenterContainer` | Centers child | Centered labels |
| `PanelContainer` | Panel with StyleBox | Panel backgrounds |

### Size Flags

```gdscript
# How a control behaves inside a container:
control.size_flags_horizontal = Control.SIZE_EXPAND_FILL
# SIZE_FILL        → Fill available space (no expand)
# SIZE_EXPAND      → Request extra space
# SIZE_EXPAND_FILL → Request extra space AND fill it
# SIZE_SHRINK_CENTER → Shrink to minimum, center in space
# SIZE_SHRINK_END    → Shrink to minimum, align to end
```

### Building UI in Code (Our Approach)

Relax Room builds most UI programmatically instead of using the visual editor:

```gdscript
# From music_panel.gd
func _build_ui() -> void:
    var margin := MarginContainer.new()
    margin.add_theme_constant_override("margin_left", 12)
    add_child(margin)

    var vbox := VBoxContainer.new()
    vbox.add_theme_constant_override("separation", 8)
    margin.add_child(vbox)

    var title := Label.new()
    title.text = "Music Player"
    title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    vbox.add_child(title)

    # ... more UI elements
```

**Why code instead of .tscn?** Because the shop panel and decoration panel are **catalog-driven** — they build their contents dynamically from JSON data. Using .tscn files would require knowing the exact layout at design time.

---

## 10. The Audio System

### Audio Architecture

```
AudioStreamPlayer (plays audio)
         │
         ▼
    AudioBus (processes audio)
    ┌──────────────────────┐
    │ Bus: "Master"        │
    │  Volume: 0 dB        │
    │  Effects: none       │
    ├──────────────────────┤
    │ Bus: "Music"         │
    │  Volume: -6 dB       │
    │  Effects: Reverb      │
    ├──────────────────────┤
    │ Bus: "Ambience"      │
    │  Volume: -3 dB       │
    │  Effects: none       │
    └──────────────────────┘
         │
         ▼
    Hardware Output (speakers/headphones)
```

### AudioStreamPlayer

```gdscript
var player := AudioStreamPlayer.new()
player.stream = load("res://audio/music/track_01.wav")
player.bus = "Music"           # Route to Music bus
player.volume_db = 0.0         # 0 dB = full volume, -80 dB = silence
add_child(player)
player.play()

# Volume conversion:
# Linear (0.0 to 1.0) → dB
var db := linear_to_db(0.5)    # = -6.02 dB
var linear := db_to_linear(-6) # = ~0.5
```

### Crossfade System (Our Implementation)

```gdscript
# AudioManager uses two players for seamless transitions:
var _player_a: AudioStreamPlayer  # Currently playing
var _player_b: AudioStreamPlayer  # Standby

func crossfade_to(stream: AudioStream) -> void:
    _player_b.stream = stream
    _player_b.play()

    var tween := create_tween()
    tween.set_parallel(true)
    tween.tween_property(_player_a, "volume_db", -80.0, 1.0)
    tween.tween_property(_player_b, "volume_db", 0.0, 1.0)
    tween.chain().tween_callback(_swap_players)

func _swap_players() -> void:
    var temp := _player_a
    _player_a = _player_b
    _player_b = temp
    _player_b.stop()
```

---

## 11. Autoloads (Singletons)

### What Are Autoloads?

Autoloads are scripts (or scenes) that:
1. Are loaded **automatically** when the game starts
2. Persist **across scene changes** (never destroyed)
3. Are accessible **globally** by their name
4. Load in the **order listed** in project.godot

```
# project.godot
[autoload]
SignalBus="*res://scripts/autoload/signal_bus.gd"
AppLogger="*res://scripts/autoload/logger.gd"
GameManager="*res://scripts/autoload/game_manager.gd"
```

The `*` prefix means "create a Node instance" (not just load the script).

### When to Use Autoloads

| Use Autoload For | Don't Use Autoload For |
|------------------|----------------------|
| Global state (current room, character) | Per-instance data |
| Cross-scene communication (SignalBus) | Things that should reset per scene |
| Systems that persist (audio, saves) | UI panels (create/destroy per use) |
| Logging, analytics | Temporary computations |

### Accessing Autoloads

```gdscript
# Direct access by name (the most common way)
GameManager.current_room_id
SaveManager.load_game()
SignalBus.room_changed.emit("cozy_studio", "modern")

# Alternative: get_node
get_node("/root/GameManager")

# These are equivalent because autoloads are direct children of root
```

### Initialization Order Matters

```
1. SignalBus      ← No dependencies (pure signal declarations)
2. AppLogger      ← Uses SignalBus (for nothing critical at init)
3. GameManager    ← Loads JSON catalogs, needs AppLogger
4. SaveManager    ← Loads save file, needs GameManager to update
5. LocalDatabase  ← Opens SQLite, needs SaveManager to know what to store
6. AudioManager   ← Needs GameManager (tracks catalog) + SaveManager (state)
7. SupabaseClient ← Optional, needs SaveManager for sync
8. PerfManager    ← Needs SaveManager (window position)
```

If you swap the order (e.g., AudioManager before GameManager), AudioManager's `_ready()` would try to read `GameManager.tracks_catalog` before GameManager has loaded it → crash or empty data.

---

## 12. Tweens

### What Is a Tween?

A Tween smoothly **interpolates** a value from A to B over time:

```gdscript
# Fade a panel in (alpha 0 → 1 over 0.3 seconds)
var tween := create_tween()
tween.tween_property(panel, "modulate:a", 1.0, 0.3)

# Move a character to a position
tween.tween_property(character, "position", Vector2(500, 300), 1.0)

# Chain animations (one after another)
var tween := create_tween()
tween.tween_property(sprite, "position:x", 500.0, 0.5)  # First: move right
tween.tween_property(sprite, "modulate:a", 0.0, 0.3)     # Then: fade out
tween.tween_callback(sprite.queue_free)                    # Then: remove

# Parallel animations (at the same time)
var tween := create_tween()
tween.set_parallel(true)
tween.tween_property(sprite, "position:x", 500.0, 0.5)
tween.tween_property(sprite, "modulate:a", 0.0, 0.5)
```

### Easing and Transitions

```gdscript
# Transition type: how the value changes over time
tween.set_trans(Tween.TRANS_SINE)    # Smooth sine curve
tween.set_trans(Tween.TRANS_BOUNCE)  # Bouncy effect
tween.set_trans(Tween.TRANS_ELASTIC) # Springy overshoot
tween.set_trans(Tween.TRANS_LINEAR)  # Constant speed

# Ease type: acceleration profile
tween.set_ease(Tween.EASE_IN)       # Slow start, fast end
tween.set_ease(Tween.EASE_OUT)      # Fast start, slow end
tween.set_ease(Tween.EASE_IN_OUT)   # Slow start and end
```

**Godot 4 change:** Tweens are created with `create_tween()` (not `Tween.new()`). They're bound to the node that created them and auto-freed when done.

---

## 13. Timers

### Timer Node

```gdscript
# Create a timer
var timer := Timer.new()
timer.wait_time = 2.0           # Seconds
timer.one_shot = true           # Fire once (false = repeating)
timer.autostart = false         # Don't start automatically
timer.timeout.connect(_on_timer_timeout)
add_child(timer)
timer.start()

func _on_timer_timeout() -> void:
    print("2 seconds have passed!")

# Quick one-shot timer
get_tree().create_timer(1.5).timeout.connect(func():
    print("1.5 seconds later!")
)
```

### Timer vs Tween

| | Timer | Tween |
|--|-------|-------|
| Purpose | Wait, then do something | Smoothly change a value |
| Repeating | Yes (`one_shot = false`) | No (but can loop) |
| Use for | Delays, cooldowns, intervals | Animations, transitions |
| Our project | Menu character frame animation | Panel fade in/out, crossfade |

---

## 14. Common Patterns in Godot

### The Dirty Flag Pattern

Used in SaveManager to avoid saving every frame:

```gdscript
var _dirty: bool = false

func mark_dirty() -> void:
    _dirty = true

func _on_auto_save_timer_timeout() -> void:
    if _dirty:
        save_game()
        _dirty = false
```

### The State Machine Pattern

For managing game states or character states:

```gdscript
enum State { IDLE, WALKING, RUNNING, JUMPING }
var current_state: State = State.IDLE

func _physics_process(delta: float) -> void:
    match current_state:
        State.IDLE:
            _process_idle(delta)
        State.WALKING:
            _process_walking(delta)
        State.RUNNING:
            _process_running(delta)
```

### The call_deferred Pattern

When you need to do something after the current frame:

```gdscript
# Problem: modifying the scene tree during a signal callback
# Solution: defer the modification to the end of the frame
func _on_enemy_died() -> void:
    enemy.queue_free()                    # OK: queue_free is already deferred
    call_deferred("_spawn_loot")          # Defer custom logic
    remove_child.call_deferred(enemy)     # Defer node removal

# Why? Godot may be iterating over the node list when the signal fires.
# Modifying the list during iteration = crash.
```

### The Group Pattern

Groups are like tags for nodes:

```gdscript
# Add to group
add_to_group("enemies")
add_to_group("damageable")

# Find all nodes in a group
var enemies := get_tree().get_nodes_in_group("enemies")

# Call a method on all nodes in a group
get_tree().call_group("enemies", "take_damage", 10)

# Check membership
if is_in_group("enemies"):
    print("I'm an enemy!")
```

---

## 15. Godot 4.x Changes from 3.x

If you encounter Godot 3 tutorials online, here are the key differences:

| Godot 3 | Godot 4 | Notes |
|---------|---------|-------|
| `export var x` | `@export var x` | Annotations replace keywords |
| `onready var x` | `@onready var x` | Same |
| `yield(get_tree(), "idle_frame")` | `await get_tree().process_frame` | `yield` → `await` |
| `connect("signal", obj, "method")` | `signal.connect(method)` | Callable-based connections |
| `emit_signal("name", args)` | `signal.emit(args)` | Direct emission |
| `var tween = Tween.new()` | `var tween = create_tween()` | Tweens are node-bound |
| `KinematicBody2D` | `CharacterBody2D` | Renamed |
| `move_and_slide(vel, up)` | `velocity = vel; move_and_slide()` | Velocity is a property now |
| `PoolStringArray` | `PackedStringArray` | Renamed |
| `OS.get_screen_size()` | `DisplayServer.screen_get_size()` | OS split into DisplayServer |
| `VisualServer` | `RenderingServer` | Renamed |
| `$Timer.start()` | Same | No change |
| `.tscn` format | Same but updated | Not backward compatible |
| GDScript untyped | GDScript optionally typed | Static typing recommended |
| `tool` keyword | `@tool` annotation | Same functionality |
| `master`/`puppet` | `@rpc` annotation | Networking reworked |

---

## 16. Performance Tips

### Do's

```gdscript
# DO: Cache node references
@onready var sprite := $Sprite2D  # Looked up once in _ready

# DO: Use StringName for frequent comparisons
const MY_ACTION := &"jump"  # StringName literal, faster than String

# DO: Object pooling for frequently created/destroyed nodes
var _bullet_pool: Array[Node2D] = []

# DO: Use typed arrays and variables
var enemies: Array[Enemy] = []  # Faster iteration than untyped Array

# DO: Disconnect signals in _exit_tree
func _exit_tree() -> void:
    SignalBus.room_changed.disconnect(_on_room_changed)
```

### Don'ts

```gdscript
# DON'T: Look up nodes every frame
func _process(delta: float) -> void:
    $Sprite2D.position += Vector2(1, 0)  # $ does a lookup every frame!

# DON'T: Create objects in _process
func _process(delta: float) -> void:
    var vec := Vector2(x, y)  # Allocates memory every frame (minor)
    var dict := {"key": val}  # Worse: Dictionary allocation every frame

# DON'T: Use string concatenation in hot loops
func _process(delta: float) -> void:
    var msg := "Health: " + str(health) + " / " + str(max_health)  # Slow
    # Better: use format strings
    var msg := "Health: %d / %d" % [health, max_health]

# DON'T: Forget to free nodes (memory leak!)
var popup := PopupPanel.new()
add_child(popup)
# ... later, remove_child(popup) without queue_free() → leaked!
```

### The _process Burden

Every node with `_process()` or `_physics_process()` costs CPU time, even if the function body is empty (the engine still has to call it). For nodes that don't need per-frame updates:

```gdscript
# Disable processing when not needed
set_process(false)
set_physics_process(false)

# Re-enable when needed
set_process(true)
```

---

## 17. Debugging in Godot

### Built-in Tools

| Tool | How to Access | What It Does |
|------|---------------|--------------|
| Remote Scene Tree | Debugger → Remote | View the live scene tree while running |
| Print to Console | `print()`, `push_warning()`, `push_error()` | Output messages |
| Breakpoints | Click left margin in script editor | Pause execution |
| Step Through | F10 (Over), F11 (Into), Shift+F11 (Out) | Step through code |
| Performance Monitor | Debugger → Monitors | FPS, memory, draw calls, physics |
| Profiler | Debugger → Profiler | Per-function timing |

### Debugging Techniques

```gdscript
# Print debugging (simple but effective)
print("Current state: ", current_state)
print("Position: ", position, " Velocity: ", velocity)

# Warnings (yellow in output)
push_warning("This shouldn't happen but isn't critical")

# Errors (red in output, with stack trace)
push_error("Something went very wrong!")

# Assertions (crash with message if condition is false)
assert(health >= 0, "Health cannot be negative!")

# Conditional breakpoint (in script editor)
# Click the left margin to set a breakpoint, then right-click for conditions
```

---

## 18. Project Settings That Matter

### Key Settings for Relax Room

```ini
[application]
config/name = "Relax Room"
run/main_scene = "res://scenes/menu/main_menu.tscn"

[display]
window/size/viewport_width = 1280
window/size/viewport_height = 720
window/stretch/mode = "canvas_items"      # UI scales with window
window/per_pixel_transparency/allowed = true  # Transparent window support

[rendering]
textures/canvas_textures/default_texture_filter = 0  # NEAREST (pixel art)
renderer/rendering_method = "gl_compatibility"        # OpenGL 3.3

[gui]
theme/custom = "res://assets/ui/cozy_theme.tres"      # Global UI theme
```

### Rendering Methods

| Method | API | GPU Requirement | Features | Our Choice |
|--------|-----|-----------------|----------|------------|
| Forward+ | Vulkan | Modern GPU | All features | No — overkill |
| Mobile | Vulkan | Mid-range GPU | Most features | No — still too heavy |
| GL Compatibility | OpenGL 3.3 | Any GPU | Basic features | **Yes** — wide support |

---

## 19. Troubleshooting Godot — Errori Comuni e Soluzioni

Errori che incontrerete spesso durante lo sviluppo con Godot 4 e come risolverli.

### "Node not found: NodeName"

**Causa**: State cercando un nodo che non esiste nell'albero della scena, oppure il percorso e' sbagliato.

**Soluzioni**:

1. Verificate il percorso nel pannello Scene (il nome deve corrispondere esattamente, case-sensitive)
2. Se usate `$Path/To/Node`, controllate che il nodo genitore sia corretto
3. Se il nodo viene creato dinamicamente, potrebbe non esistere ancora in `_ready()` — usate `call_deferred()`
4. Usate il **Remote Scene Tree** (pannello "Remote" durante il gameplay) per vedere i nodi effettivamente presenti

### "Cyclic reference detected"

**Causa**: Due script si riferiscono l'uno all'altro con `preload()` o `class_name`, creando un ciclo.

**Soluzioni**:

1. Sostituite `preload()` con `load()` in uno dei due script (load e' lazy, rompe il ciclo)
2. Usate i segnali invece di riferimenti diretti tra classi
3. Estraete l'interfaccia comune in un terzo script

### "Invalid get index 'property' (on base: 'Nil')"

**Causa**: State accedendo a una proprieta' di un oggetto che e' `null`. Tipico quando un nodo e' stato distrutto con `queue_free()` ma una variabile punta ancora ad esso.

**Soluzioni**:

1. Controllate con `if node != null and is_instance_valid(node):`
2. Impostate la variabile a `null` dopo `queue_free()` del nodo
3. Verificate che il nodo non sia stato liberato da un altro script

### "Cannot convert argument X from 'Type' to 'OtherType'"

**Causa**: State passando un valore del tipo sbagliato a una funzione. Tipico con `int` vs `float`, `String` vs `StringName`, o `Resource` vs il tipo specifico.

**Soluzioni**:

1. Usate cast espliciti: `value as float`, `str(value)`, `int(value)`
2. Per risorse, verificate il tipo: `if resource is Texture2D:`
3. Aggiungete type hints ovunque per far emergere questi errori prima

### "res://path/file.ext: No such file or directory"

**Causa**: Il percorso della risorsa e' sbagliato, il file e' stato spostato, o c'e' un typo.

**Soluzioni**:

1. Verificate che il file esista esattamente a quel percorso (case-sensitive su Linux!)
2. Dopo aver spostato file, usate "Reimport" nel pannello FileSystem di Godot
3. Cercate nel progetto con `Ctrl+Shift+F` per trovare tutti i riferimenti al vecchio percorso

---

## 20. Suggerimenti di Produttivita' nell'Editor Godot

### Shortcut Fondamentali

| Shortcut | Azione |
| -------- | ------ |
| `F1` | Apre la documentazione integrata (cerca classe o funzione) |
| `F5` | Avvia il gioco |
| `F6` | Avvia la scena corrente (senza passare dal menu) |
| `F8` | Ferma il gioco |
| `Ctrl+Shift+F` | Cerca testo in tutti i file del progetto |
| `Ctrl+D` | Duplica la riga corrente nello script editor |
| `Ctrl+K` | Commenta/decommenta la selezione |
| `Ctrl+.` | Autocomplete (suggerimenti codice) |
| `Ctrl+Click` su un tipo | Vai alla definizione (apre lo script/classe) |

### Remote Inspector (Debug in Tempo Reale)

Durante il gameplay (`F5`), potete ispezionare lo stato del gioco in tempo reale:

1. **Pannello "Remote"**: mostra l'albero dei nodi del gioco in esecuzione. Potete selezionare qualsiasi nodo e vederne le proprieta' attuali nell'Inspector
2. **Pannello "Debugger"**: mostra stack trace, variabili locali, breakpoint
3. **Performance Monitor**: `Debugger → Monitors` mostra FPS, draw calls, physics ticks, memoria

### print() vs push_warning() vs push_error()

```gdscript
# Per debug temporaneo (rimuovere prima del commit!)
print("Valore: ", variabile)

# Per avvisi non critici (restano nel codice, visibili nel pannello Output)
push_warning("Texture non trovata, uso placeholder")

# Per errori gravi (visibili in rosso nel pannello Output)
push_error("File di salvataggio corrotto: " + file_path)
```

**Regola del progetto**: niente `print()` nel codice committato. Usate `AppLogger` per logging strutturato:

```gdscript
AppLogger.info("NomeClasse", "Messaggio", {"chiave": valore})
AppLogger.warn("NomeClasse", "Qualcosa di strano", {"dettagli": info})
AppLogger.error("NomeClasse", "Qualcosa di rotto", {"errore": msg})
```

---

## 21. Confronto con Altri Game Engine

Per capire meglio Godot, e' utile confrontarlo con i suoi concorrenti principali.

| Aspetto | Godot 4 | Unity | Unreal Engine |
| ------- | ------- | ----- | ------------- |
| **Linguaggio** | GDScript, C#, C++ | C# | C++, Blueprints |
| **Licenza** | MIT (completamente gratuito e open source) | Gratuito fino a soglia ricavi, poi royalty | Gratuito fino a $1M ricavi, poi 5% royalty |
| **Dimensione editor** | ~100 MB | ~5-10 GB | ~30-50 GB |
| **Ideale per** | 2D, pixel art, prototipi, giochi indie | 2D e 3D, mobile, AR/VR | AAA 3D, fotorealismo, open world |
| **Scene system** | Albero di nodi (Node), composizione | GameObject + Component | Actor + Component |
| **Build 2D** | Eccellente (nativo, performante) | Buono (ma nato per 3D) | Possibile ma non ideale |
| **Curva apprendimento** | Bassa (GDScript simile a Python) | Media (C# potente ma verboso) | Alta (C++ complesso, Blueprints visuali) |
| **Community** | In crescita rapida, open source | Enorme, matura | Enorme, professionale |
| **Export Web** | Supportato (HTML5) | Supportato (WebGL) | Limitato |
| **Mobile** | Supportato | Eccellente | Possibile ma pesante |

### Perche' Godot per Relax Room?

1. **Pixel art 2D nativo**: Godot ha supporto first-class per il 2D, non e' un "adattamento" del 3D
2. **Leggerezza**: L'editor e' 100 MB, il gioco esportato pesa pochi MB — ideale per un desktop companion
3. **GDScript**: Simile a Python, facile da imparare per studenti IFTS senza esperienza C#/C++
4. **Open source**: Nessun costo di licenza, nessun vincolo legale, codice ispezionabile
5. **Esportazione multipiattaforma**: Windows, Linux, macOS, Web da un unico progetto

---

*Study document for Relax Room — IFTS Projectwork 2026*
*Author: Renan Augusto Macena (System Architect & Project Supervisor)*

---

## Exercises

1. **Lab — autoload + signals.** Create a small project with a global GameState autoload that broadcasts a `level_changed` signal; multiple scenes connect and react.
2. **Lab — profile a workload.** Build a scene with 1000 sprites moving via `_process`; profile with `Performance.MONITORS`. Record FPS, draw calls, idle time. Optimize one bottleneck.
3. **Stretch — GDExtension hello world.** Compile a small GDExtension in C++ that exposes a `compute_heavy_thing()` function; benchmark vs GDScript equivalent.

## Self-assessment

1. What is the difference between a Node and a Resource?
2. Explain server-based rendering in two sentences.
3. When prefer signal over direct call?
4. Autoload init order: how is it determined?
5. Where to find the profiler in the Godot editor?

## Primary reading

- Godot — Engine architecture overview. https://docs.godotengine.org/en/stable/contributing/development/core_and_modules/godot_internals.html
- Godot — GDScript reference. https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/
- Godot — Performance optimization. https://docs.godotengine.org/en/stable/tutorials/performance/

## Cross-links

- Module 02 — `SCENES_AND_NODES.md`: scene tree details.
- Module 13 — `AUTOLOAD_SAFETY.md` (NEW): deep dive autoload.
- Module 14 — `DESKTOP_COMPANION_PERFORMANCE.md` (NEW): profile workflow.

## Local glossary

| Term | Definition |
|---|---|
| **Scene** | Reusable composition of nodes; saved as `.tscn`. |
| **Node** | Building block of a scene. |
| **Signal** | Event emitted by node, listened by others. |
| **Autoload** | Globally accessible singleton scene/script. |
| **Resource** | Reusable data asset (`.tres`, `.res`). |
| **GDScript** | Godot's primary scripting language. |
| **PackedScene** | Serialized scene used for instancing. |
| **`_process` / `_physics_process`** | Per-frame / fixed-rate callbacks. |
| **`Performance.get_monitor`** | Built-in metrics API. |
| **Server architecture** | RenderingServer, PhysicsServer, AudioServer. |
