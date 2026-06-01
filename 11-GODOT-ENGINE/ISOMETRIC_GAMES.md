# Isometric Game Development — Comprehensive Study Guide

> **Course module:** Godot 4 in Production
> **Position:** Phase 2 — Visual systems · Module 07
> **Prerequisites:** Modules 03-05; trigonometry basics, 2D matrices.
> **Learning objectives:** isometric projection math (cartesian ↔ iso transform); depth sorting (y-sort + manual hacks); tile-based design; pixel-art constraints; reference games (Civilization, Diablo, SimCity).
> **Estimated time:** 60-90 min reading · 240 min hands-on
> **Level:** competent → proficient
> **Last updated:** 2026-04-27

## Guiding ideas

1. **Isometric is 2D pretending to be 3D.** Math is matrix multiplication: 30° rotation + scale Y by 0.5.
2. **Depth sorting is the hard part.** y-sort works for simple cases; complex with multi-tile entities or staircases.
3. **Pixel-perfect isometric is mathematically impossible.** Accept tiny rendering artifacts; Nearest filter helps.
4. **Tile size canonical: 32x16 or 64x32 (2:1).** Exception: Diablo II used true isometric 4:3 angle.
5. **Famous games: SimCity (true iso), Diablo (dimetric ~63°), Civilization (orthogonal+iso art).** Studio scelte per genre.

A deep study of isometric projection, coordinate systems, depth sorting, tile-based design, and how to build isometric games in Godot 4.x — with references to how Relax Room applies these concepts.

---

## 1. What Is Isometric Projection?

### The Three Main Projections

When representing a 3D world on a 2D screen, there are three common approaches:

```
PERSPECTIVE               ORTHOGRAPHIC              ISOMETRIC
(realistic depth)         (no depth distortion)     (angled orthographic)

    /\                    ┌────────────┐             ◇
   /  \                   │            │            / \
  /    \                  │            │           /   \
 /      \                 │            │          /     \
/________\                └────────────┘         ◇       ◇
                                                  \     /
Objects get smaller         All same size          \   /
as they go back             regardless of           \ /
                            distance                 ◇

Used in: FPS, 3D games     Used in: 2D platformers  Used in: Strategy, RPGs,
(Minecraft, Portal)        (Mario, Celeste)         sims (SimCity, Diablo)
```

### True Isometric vs Dimetric

**True isometric** projects all three axes at exactly 120° apart, resulting in angles of approximately 30° from horizontal:

```
True Isometric (30°):        Dimetric / "2:1" (26.57°):
      ↑ Y                         ↑ Y
     / \                          / \
    /30° \30°                    /    \
   /      \                     / 26.57°\
  X        Z                   X         Z

   Pixel ratio: ~1.73:1          Pixel ratio: exactly 2:1
   Hard to draw pixel-perfect    Perfect for pixel art!
```

**The 2:1 dimetric projection** (often called "isometric" in games) moves 2 pixels horizontally for every 1 pixel vertically. This is the standard for pixel art isometric games because it maps perfectly to pixel grids — no anti-aliasing needed.

### The Math

Converting between Cartesian (world) coordinates and screen (isometric) coordinates:

```
World-to-Screen (Cartesian → Isometric):
  screen_x = (world_x - world_y) * (tile_width / 2)
  screen_y = (world_x + world_y) * (tile_height / 2)

Screen-to-World (Isometric → Cartesian):
  world_x = (screen_x / (tile_width / 2) + screen_y / (tile_height / 2)) / 2
  world_y = (screen_y / (tile_height / 2) - screen_x / (tile_width / 2)) / 2
```

In GDScript:

```gdscript
const TILE_WIDTH := 64
const TILE_HEIGHT := 32

func world_to_screen(world_pos: Vector2) -> Vector2:
    return Vector2(
        (world_pos.x - world_pos.y) * (TILE_WIDTH / 2.0),
        (world_pos.x + world_pos.y) * (TILE_HEIGHT / 2.0)
    )

func screen_to_world(screen_pos: Vector2) -> Vector2:
    var half_w := TILE_WIDTH / 2.0
    var half_h := TILE_HEIGHT / 2.0
    return Vector2(
        (screen_pos.x / half_w + screen_pos.y / half_h) / 2.0,
        (screen_pos.y / half_h - screen_pos.x / half_w) / 2.0
    )
```

---

## 2. Tile-Based Isometric Games

### Diamond Layout vs Staggered Layout

There are two ways to arrange isometric tiles:

```
DIAMOND LAYOUT:                    STAGGERED LAYOUT:
(rotated 45°)                      (offset rows)

        ◇                         ◇ ◇ ◇ ◇
       ◇ ◇                         ◇ ◇ ◇
      ◇ ◇ ◇                       ◇ ◇ ◇ ◇
       ◇ ◇                         ◇ ◇ ◇
        ◇                         ◇ ◇ ◇ ◇

World origin at top               World origin at top-left
Natural for open maps              Natural for rectangular maps
Used in: Age of Empires           Used in: most 2D platformers
```

### Tile Dimensions

Standard isometric tile sizes follow the 2:1 ratio:

| Size | Common Use | Example Games |
|------|-----------|---------------|
| 32×16 | Small/retro games | Classic era |
| 64×32 | Standard indie | Most common |
| 128×64 | High-detail | Modern pixel art |
| 256×128 | HD isometric | Strategy games |

### Rendering Order (The Painter's Algorithm)

In isometric view, tiles must be drawn **back-to-front** (far tiles first, near tiles last) so that closer tiles correctly overlap distant ones:

```
Drawing order for diamond layout:
Row 0:    ◇           ← Draw first (furthest)
Row 1:   ◇ ◇
Row 2:  ◇ ◇ ◇
Row 3:   ◇ ◇
Row 4:    ◇           ← Draw last (nearest)

For each row: draw left to right
```

```gdscript
# Simple rendering order for diamond tiles
func draw_tiles() -> void:
    # Draw from top-left to bottom-right
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            var screen_pos := world_to_screen(Vector2(x, y))
            draw_tile(tiles[y][x], screen_pos)
```

---

## 3. Depth Sorting / Z-Order

### The Fundamental Challenge

Depth sorting is the **hardest problem** in isometric games. Since everything is rendered in 2D, the engine doesn't know which objects are "in front" — you have to tell it.

```
Problem:                        Solution:
  ┌──┐                          Draw furthest first,
  │  │  ← This box should       nearest last.
  │  │    be BEHIND the tree
  └──┘                          Objects with higher Y
   🌳  ← Tree is in front      are drawn last (on top).
```

### Y-Sort

The simplest and most common approach: **sort by Y position**. Objects lower on the screen (higher Y value) are drawn on top:

```gdscript
# In Godot 4.x, enable Y-Sort on the parent Node2D:
# In Inspector: CanvasItem → Y Sort Enabled = true

# Or in code:
parent_node.y_sort_enabled = true

# How it works:
# Object A at y=100 → drawn first (behind)
# Object B at y=200 → drawn second (in front)
```

```
Without Y-Sort:                With Y-Sort:

  Character                      Tree
    🧑                            🌳
    🌳                            🧑
  Tree                          Character

  (Character drawn on top       (Tree drawn first because
   even though behind tree)      it has lower Y position)
```

### Z-Index

For objects that Y-Sort can't handle (e.g., always-on-top UI, background layers):

```gdscript
# Z-Index: manual draw order within the same parent
sprite.z_index = 5          # Higher = drawn on top
sprite.z_as_relative = true # Relative to parent's z_index

# Typical z_index strategy:
# -10: Background (sky, parallax layers)
#   0: Ground tiles
#   1: Ground decorations (rugs, shadows)
#   5: Objects (furniture, walls)
#  10: Characters
#  20: Overhead objects (ceiling fans, hanging lamps)
#  50: UI elements
```

### Advanced Sorting: Multi-Axis

For complex scenes where Y-sort alone isn't enough (e.g., tall objects that should overlap differently depending on the viewer's position):

```gdscript
# Sort by Y first, then by X for objects at the same Y
func _compare_depth(a: Node2D, b: Node2D) -> bool:
    if a.position.y != b.position.y:
        return a.position.y < b.position.y
    return a.position.x < b.position.x
```

### Dealing with Tall Objects

Tall objects (like walls or bookshelves) need special handling because their bottom is at one Y level but they visually extend upward:

```
Problem: A wall at y=100 is sorted by y=100,
but it visually goes from y=0 to y=100.
A character at y=80 should be BEHIND the wall,
but Y-sort puts the character behind (lower Y).

Solutions:
1. Sort by the BOTTOM of each object (foot position)
2. Use the origin point at the base of tall sprites
3. Split tall objects into base + top layers
```

In Godot, the sprite's `offset` property and the node's `position` determine sorting:

```gdscript
# Place origin at the BASE of the sprite, not the center
sprite.centered = false  # Origin at top-left
sprite.offset.y = -sprite.texture.get_height()  # Shift sprite up
# Now position.y represents the base (foot) of the object
```

---

## 4. Isometric in Godot 4.x

### TileMapLayer (Godot 4.3+)

Godot 4 has built-in isometric tile map support:

```
In the TileSet resource:
  Tile Shape: Isometric
  Tile Layout: Diamond
  Tile Offset Axis: Horizontal
  Tile Size: 64×32 (or your chosen dimensions)
```

```gdscript
# Accessing tiles programmatically
var tilemap: TileMapLayer = $TileMapLayer

# Set a tile at grid coordinates
tilemap.set_cell(Vector2i(5, 3), source_id, atlas_coords)

# Get the tile at a screen position
var grid_pos := tilemap.local_to_map(screen_position)
var tile_data := tilemap.get_cell_tile_data(grid_pos)

# Convert between grid and screen coordinates
var screen_pos := tilemap.map_to_local(Vector2i(5, 3))
var grid_pos := tilemap.local_to_map(screen_pos)
```

### Y-Sort in Godot

```gdscript
# Method 1: Enable on parent node
var room := Node2D.new()
room.y_sort_enabled = true

# All children will be sorted by their Y position
# Lower Y → drawn first (behind)
# Higher Y → drawn last (in front)

# Method 2: Custom sort with CanvasItem.z_index
sprite.z_index = 10  # Manual override
```

### Custom Isometric without TileMap

Relax Room doesn't use TileMap — it uses a **room-based** approach where each room is a flat 2D scene with decorations placed via drag-and-drop. But the isometric concepts still apply:

```
Our approach:
┌─────────────────────────────────┐
│ Wall Zone (top 40%)             │  ← Wall decorations go here
│  [paintings] [clock] [shelf]    │
├─────────────────────────────────┤  ← Baseboard divider
│ Floor Zone (bottom 60%)         │  ← Floor decorations go here
│  [desk] [chair] [plant]        │
│           🧑 Character          │
│  [rug]        [lamp]           │
└─────────────────────────────────┘

Depth sorting:
- Items lower on screen → drawn on top (Y-sort)
- Character sorts with decorations based on Y position
- Wall items always behind floor items
```

---

## 5. Character Movement in Isometric

### 8-Directional Movement

In isometric games, the visual directions don't match the input directions:

```
            Input (WASD/Arrows):           Visual (Screen):
                   W/↑                          ↗
                    │                          /
            A/← ───┼─── D/→               ←──◇──→
                    │                          \
                   S/↓                          ↙

The "up" direction on screen is actually up-right in isometric.
```

Standard 8-direction mapping for isometric:

```gdscript
# For true isometric movement, rotate input by 45°
func get_iso_direction() -> Vector2:
    var input := Vector2.ZERO
    input.x = Input.get_axis("move_left", "move_right")
    input.y = Input.get_axis("move_up", "move_down")

    # Rotate 45° for isometric
    var iso_direction := Vector2(
        input.x - input.y,
        (input.x + input.y) * 0.5
    )
    return iso_direction.normalized()
```

### Our Project's Approach

Relax Room uses `CharacterBody2D` with simple 2D movement (not rotated isometric) because the rooms are flat 2D views with a slight perspective feel, not true isometric grids:

```gdscript
# character_controller.gd (simplified concept)
func _physics_process(delta: float) -> void:
    var direction := Vector2.ZERO
    direction.x = Input.get_axis("move_left", "move_right")
    direction.y = Input.get_axis("move_up", "move_down")

    if direction.length() > 0:
        velocity = direction.normalized() * SPEED
        _update_animation(direction)
    else:
        velocity = Vector2.ZERO
        _play_idle()

    move_and_slide()
```

### Animation Directions

For 8-directional sprite animation:

```
Direction → Animation Name:
  ↑   (0, -1) → walk_up
  ↗  (1, -1)  → walk_up_right
  →   (1, 0)  → walk_right
  ↘  (1, 1)   → walk_down_right
  ↓   (0, 1)  → walk_down
  ↙  (-1, 1)  → walk_down_left
  ←  (-1, 0)  → walk_left (or flip walk_right)
  ↖  (-1, -1) → walk_up_left (or flip walk_up_right)
```

Many isometric games only draw 5 directions and **horizontally flip** to get the other 3:

```
Actually drawn:    walk_up, walk_up_right, walk_right,
                   walk_down_right, walk_down

Flipped:           walk_up_left = flip(walk_up_right)
                   walk_left = flip(walk_right)
                   walk_down_left = flip(walk_down_right)
```

```gdscript
func _update_animation(direction: Vector2) -> void:
    if abs(direction.x) > abs(direction.y):
        # Moving horizontally
        sprite.play("walk_right")
        sprite.flip_h = direction.x < 0  # Flip for left
    else:
        if direction.y < 0:
            sprite.play("walk_up")
        else:
            sprite.play("walk_down")
```

### Pathfinding in Isometric

For click-to-move or AI movement, you need pathfinding:

```gdscript
# Using Godot's built-in A* pathfinding
var astar := AStarGrid2D.new()

func setup_navigation() -> void:
    astar.region = Rect2i(0, 0, MAP_WIDTH, MAP_HEIGHT)
    astar.cell_size = Vector2(TILE_WIDTH, TILE_HEIGHT)
    astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ALL_PASSABLE
    astar.update()

    # Mark obstacles
    for y in MAP_HEIGHT:
        for x in MAP_WIDTH:
            if is_obstacle(x, y):
                astar.set_point_solid(Vector2i(x, y), true)

func find_path(from: Vector2i, to: Vector2i) -> PackedVector2Array:
    return astar.get_point_path(from, to)
```

---

## 6. Pixel Art for Isometric Games

### Tile Creation Guidelines

```
Standard isometric tile (64×32):

          ╱╲              1. Start with the diamond outline
         ╱  ╲             2. Every edge is exactly 2:1 (2 pixels right, 1 up)
        ╱    ╲            3. Fill with base color
       ╱      ╲           4. Add shading (top-right = light, bottom-left = dark)
      ╱        ╲          5. Add texture detail
       ╲      ╱           6. NO anti-aliasing (nearest neighbor rendering)
        ╲    ╱
         ╲  ╱
          ╲╱

Width = 64 pixels
Height = 32 pixels
Ratio = exactly 2:1
```

### Color and Lighting

```
Standard isometric light source: top-right

    Light ☀️ →↘
    ┌───┐
    │Top│ ← Brightest face
    ├───┤
    │Frt│ ← Medium brightness
    └───┘
     Side → Darkest face (left side)

Color palette tip:
  Base color:    hsl(120, 50%, 50%)  ← Green
  Light face:    hsl(120, 45%, 65%)  ← +15% lightness
  Dark face:     hsl(120, 55%, 35%)  ← -15% lightness
  Outline:       hsl(120, 60%, 20%)  ← Very dark
```

### Sprite Creation for Characters

```
Front-facing (most common):
  - Character faces screen (toward bottom-right in isometric)
  - Height: 1.5-2x tile height
  - Feet at base of sprite (origin at bottom for Y-sort)

Walk cycle (4-8 frames per direction):
  Frame 1: Idle/Contact (feet together)
  Frame 2: Step 1 (left foot forward)
  Frame 3: Pass (feet cross)
  Frame 4: Step 2 (right foot forward)
  Frame 5: Pass (back to frame 1)

For 8 directions: 5 unique directions × 4-8 frames = 20-40 sprites
(Other 3 directions are horizontally flipped)
```

### Texture Filtering for Pixel Art

**Critical setting** for any pixel art game:

```gdscript
# Project-wide setting (project.godot):
rendering/textures/canvas_textures/default_texture_filter = 0  # NEAREST

# Per-sprite override (if needed):
sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

# Why?
# NEAREST:  Each pixel is a crisp square → clean pixel art
# LINEAR:   Pixels are blurred/smoothed → mushy, wrong for pixel art
```

---

## 7. Camera in Isometric Games

### Following the Player

```gdscript
# Using Camera2D
var camera := Camera2D.new()
camera.zoom = Vector2(2, 2)        # 2x zoom for pixel art
camera.position_smoothing_enabled = true
camera.position_smoothing_speed = 5.0
player.add_child(camera)           # Attach to player → follows automatically

# Or update manually:
func _process(delta: float) -> void:
    camera.position = camera.position.lerp(player.position, 5.0 * delta)
```

### Camera Bounds

Prevent the camera from showing outside the map:

```gdscript
camera.limit_left = 0
camera.limit_top = 0
camera.limit_right = MAP_WIDTH * TILE_WIDTH
camera.limit_bottom = MAP_HEIGHT * TILE_HEIGHT
camera.limit_smoothed = true  # Smooth transition at limits
```

### Zoom for Desktop Companions

Relax Room doesn't use Camera2D because the viewport is the entire room — there's no scrolling. The window size IS the camera view:

```
┌──────── 1280 × 720 ────────┐
│  The entire room fits in    │
│  the viewport. No camera    │
│  needed.                    │
│                             │
│  Characters walk within     │
│  room bounds (StaticBody2D) │
└─────────────────────────────┘
```

---

## 8. Famous Isometric Games (History)

### Timeline and Techniques

| Year | Game | Innovation |
|------|------|-----------|
| 1981 | **Zaxxon** (Sega) | First isometric arcade game |
| 1989 | **SimCity** (Maxis) | Isometric city building, tile-based |
| 1993 | **Ultima VII** (Origin) | Large isometric RPG world |
| 1996 | **Diablo** (Blizzard) | Real-time isometric action RPG, lighting |
| 1997 | **Age of Empires** (Ensemble) | Isometric RTS, terrain height |
| 1997 | **Fallout** (Interplay) | Isometric RPG, hex grid |
| 1998 | **StarCraft** (Blizzard) | Isometric RTS, competitive multiplayer |
| 2000 | **The Sims** (Maxis) | Isometric life simulation, room decoration |
| 2000 | **Diablo II** (Blizzard) | Refined isometric action, massive scale |
| 2006 | **Habbo Hotel** | Isometric social room decoration |
| 2012 | **FTL** (Subset Games) | Isometric spaceship management |
| 2014 | **Transistor** (Supergiant) | Modern isometric action, art style |
| 2017 | **Into the Breach** (Subset) | Isometric tactics, perfect information |
| 2018 | **Hades** (Supergiant) | Isometric roguelike, fluid combat |
| 2020 | **Disco Elysium** (ZA/UM) | Isometric RPG, narrative-driven |
| 2023 | **Baldur's Gate 3** (Larian) | Isometric/perspective hybrid RPG |

### Techniques from Famous Games

**The Sims (2000)** — Most relevant to Relax Room:
- Room-based decoration system
- Object placement with grid snapping
- Character needs and interactions
- Wall/floor/object layering

**Habbo Hotel (2006)** — Virtual room decoration:
- Isometric pixel art rooms
- Furniture placement and customization
- Social features
- Catalog-driven content system (exactly like our `decorations.json`)

**Stardew Valley (2016)** — While not strictly isometric (it's top-down with slight perspective), it demonstrates:
- Pixel art consistency
- Room decoration mechanics
- Day/night cycle
- Lo-fi aesthetic

---

## 9. Common Challenges in Isometric Development

### Wall Occlusion

When a character walks behind a wall, the wall should partially hide the character:

```
Wrong:                      Correct:
  ┌──────┐                    ┌──────┐
  │ WALL │  🧑                │ WALL │
  └──────┘                    └──┤🧑├┘  ← Character partially behind wall
                                │  │
                                └──┘

Solutions:
1. Alpha mask on wall (reveal character behind)
2. Wall becomes transparent when character is behind it
3. Wall has "near" and "far" halves (split rendering)
4. Outline shader shows character silhouette through walls
```

### Multi-Level Buildings

```
Level 2:   ┌─────┐
           │     │
           └──┬──┘
Level 1:   ┌──┴──┐
           │     │
           └─────┘

Challenge: How to show both levels? How to let characters move between levels?

Solutions:
1. Toggle level visibility (button to switch floors)
2. Transparency — upper floor becomes semi-transparent when character is on lower floor
3. Cutaway view — remove the near wall of the current floor
4. Separate camera views per floor
```

### Mouse Picking (Clicking on Isometric Objects)

Translating a mouse click position to the correct isometric tile:

```gdscript
# Which tile did the player click on?
func get_clicked_tile(mouse_pos: Vector2) -> Vector2i:
    # Convert screen position to world coordinates
    var world := screen_to_world(mouse_pos)
    # Round to nearest tile
    return Vector2i(roundi(world.x), roundi(world.y))

# For objects (not tiles), use Area2D with collision shapes
# Godot handles this automatically with input_event signal
```

### Large Objects Spanning Multiple Tiles

A table that covers 2×3 tiles:

```
Solution 1: Single sprite
  - Place at origin tile
  - Set z_index based on front-most tile
  - Collision shape covers all tiles

Solution 2: Split into tiles
  - Each tile-sized piece renders separately
  - Proper per-tile depth sorting
  - More complex but handles occlusion perfectly
```

---

## 10. Room-Based vs Open World Isometric

### Comparison

| Feature | Room-Based | Open World |
|---------|-----------|------------|
| Map Size | Fixed (one screen) | Large, scrollable |
| Camera | Static or minimal pan | Follows player |
| Loading | Instant (small scenes) | Streaming/chunking |
| Depth Sort | Simple (Y-sort) | Complex (multi-axis) |
| Memory | Low | High (visible tiles) |
| Complexity | Beginner-friendly | Advanced |
| Examples | The Sims rooms, Habbo | Diablo, Age of Empires |
| **Our project** | **Room-based** | — |

### Why Room-Based Works for Relax Room

1. **Desktop companion** — The app sits in a small window, a single room fills it
2. **Decoration focus** — Players customize one room at a time
3. **Performance** — No tile streaming, no camera management, minimal GPU
4. **Simplicity** — Easier to develop and maintain for a small team

### Room Transitions

When the player changes rooms:

```gdscript
# Our approach:
func change_room(room_id: String, theme: String) -> void:
    # 1. Clear current decorations
    for child in decorations_node.get_children():
        child.queue_free()

    # 2. Update wall/floor colors from theme palette
    var colors := GameManager.get_theme_colors(room_id, theme)
    wall_rect.color = Color(colors.get("wall", "#2a2a3e"))
    floor_rect.color = Color(colors.get("floor", "#3a3a4e"))

    # 3. Re-instantiate decorations from save data
    for deco_data in SaveManager.decorations:
        _spawn_decoration(deco_data)

    # 4. Update character position
    character.position = Vector2(640, 500)
```

---

## 11. Performance Considerations

### Culling Off-Screen Tiles

For large open-world isometric maps:

```gdscript
# Only render tiles visible on screen
func _draw_visible_tiles() -> void:
    var viewport_rect := get_viewport_rect()
    var cam_pos := camera.global_position

    # Calculate visible tile range
    var top_left := screen_to_world(cam_pos - viewport_rect.size / 2)
    var bottom_right := screen_to_world(cam_pos + viewport_rect.size / 2)

    # Add margin for tall tiles
    var margin := 3

    for y in range(int(top_left.y) - margin, int(bottom_right.y) + margin):
        for x in range(int(top_left.x) - margin, int(bottom_right.x) + margin):
            if is_valid_tile(x, y):
                draw_tile(x, y)
```

### Texture Atlases

Instead of loading hundreds of individual sprite files, combine them into atlases:

```
Individual files (slow):         Atlas (fast):
┌──┐ ┌──┐ ┌──┐ ┌──┐             ┌──────────────┐
│🪑│ │🌱│ │💡│ │📦│ ...100      │🪑🌱💡📦...  │ 1 file
└──┘ └──┘ └──┘ └──┘  files       │🖼️🎸🛋️🪞...  │ 1 draw call
                                  └──────────────┘
100 draw calls                   → Fewer draw calls
100 file loads                   → 1 file load
```

Godot handles this automatically with **TextureRegion** and the **Import** system, but for maximum performance, use a spritesheet tool (TexturePacker, Aseprite export).

### Batch Draw Calls

Godot's 2D renderer batches draw calls automatically when:
1. Same material/shader
2. Same texture (or atlas)
3. Same blend mode
4. Same CanvasItem settings

**Tip:** Keep all floor tiles in one atlas, all wall tiles in another, all decorations grouped → fewer draw call breaks.

---

## 12. Isometric Design Principles

### Visual Clarity

```
Good isometric design:
1. Clear silhouettes — Each object is recognizable at small scale
2. Consistent lighting — Light always from the same direction (top-right)
3. Readable tiles — Floor, wall, and object tiles are visually distinct
4. Color coding — Categories have color themes (wood = brown, metal = gray)
5. Consistent scale — All objects follow the same pixel-per-meter ratio
```

### Grid Snapping

For decoration placement:

```gdscript
# Snap to a grid for clean placement
const GRID_SIZE := 8  # Pixels

func snap_to_grid(position: Vector2) -> Vector2:
    return Vector2(
        snapped(position.x, GRID_SIZE),
        snapped(position.y, GRID_SIZE)
    )
```

Relax Room uses grid snapping in the `Helpers.snap_to_grid()` function to ensure decorations align cleanly.

### Overlap Prevention

```gdscript
# From drop_zone.gd — prevent decorations from stacking
const OVERLAP_THRESHOLD := 0.5  # 50% overlap maximum

func _has_overlap(new_rect: Rect2) -> bool:
    for deco_data in SaveManager.decorations:
        var existing_rect := _get_decoration_rect(deco_data)
        var intersection := new_rect.intersection(existing_rect)
        if intersection.has_area():
            var overlap_ratio := intersection.get_area() / \
                minf(new_rect.get_area(), existing_rect.get_area())
            if overlap_ratio > OVERLAP_THRESHOLD:
                return true
    return false
```

---

## 13. Applying Isometric Concepts to Relax Room

### Current Architecture

Relax Room uses a **simplified isometric-inspired** approach:

```
┌─────────────────────────────────┐
│         Wall Zone               │
│   (2D flat, no perspective)     │
│   Decorations: paintings,       │
│   shelves, clocks               │
├─────────────────────────────────┤
│         Floor Zone              │
│   (2D flat, slight perspective) │
│   Decorations: desks, chairs,   │
│   plants, rugs                  │
│   Character walks with Y-sort   │
└─────────────────────────────────┘
```

### Where Isometric Concepts Apply

Even though Relax Room isn't a tile-based isometric game, these concepts are directly relevant:

| Concept | How We Apply It |
|---------|----------------|
| Depth sorting | Y-sort for decorations and character |
| Wall/floor zones | WALL_ZONE_RATIO = 0.4 separates placement areas |
| Grid snapping | `Helpers.snap_to_grid()` for clean placement |
| Overlap prevention | `_has_overlap()` in drop_zone.gd |
| Sprite origins | Decorations positioned from top-left corner |
| Consistent scale | `scale` field in decorations.json per item |
| Parallax depth | 8-layer parallax in window_background.gd |

### Future Isometric Enhancements

If Relax Room evolves toward a more isometric look:

1. **Isometric room view** — Diamond-shaped room instead of rectangle
2. **3/4 view furniture** — Sprites drawn in isometric perspective
3. **Multi-level rooms** — Loft beds, stairs, split-level rooms
4. **Outdoor areas** — Garden with isometric path tiles
5. **True tile-based floor** — Using Godot's TileMapLayer for floor decoration

---

## 14. Esercizi Pratici

Tre esercizi per verificare la comprensione dei concetti isometrici. Provate a risolverli su carta prima di verificare al computer.

### Esercizio 1: Conversione Coordinate

Data una posizione schermo `(640, 360)` (centro del viewport 1280x720), calcolate le coordinate isometriche corrispondenti usando le formule:

```text
tile_x = (screen_x / tile_width + screen_y / tile_height) / 2
tile_y = (screen_y / tile_height - screen_x / tile_width) / 2
```

Con `tile_width = 64` e `tile_height = 32`:
- `tile_x = (640/64 + 360/32) / 2 = (10 + 11.25) / 2 = 10.625`
- `tile_y = (360/32 - 640/64) / 2 = (11.25 - 10) / 2 = 0.625`

**Domanda**: se la stanza e' una griglia 10x10, questa posizione e' valida? *(Risposta: si', tile (10, 0) e' l'angolo destro della griglia)*

### Esercizio 2: Ordine di Disegno (Y-Sort)

Date queste 4 decorazioni con posizioni isometriche:
- Letto: `(2, 3)`
- Scrivania: `(4, 1)`
- Pianta: `(2, 5)`
- Sedia: `(4, 3)`

In quale ordine devono essere disegnate perche' la sovrapposizione sia corretta? *(Suggerimento: in vista isometrica, gli oggetti con `y` maggiore sono "davanti" e devono essere disegnati dopo)*

**Risposta**: Scrivania (y=1) → Letto (y=3) e Sedia (y=3, ma x=4 > 2) → Pianta (y=5). In Godot, `Y-Sort` gestisce questo automaticamente basandosi sulla `position.y` di ogni nodo.

### Esercizio 3: Progettare il Layout di una Stanza

Disegnate su carta una stanza isometrica 8x6 con:
- Un letto nell'angolo in alto a destra (2x1 tiles)
- Una scrivania lungo la parete sinistra (1x2 tiles)
- Una pianta in ogni angolo visibile (1x1 tile)

Quali posizioni tile assegnereste a ogni oggetto? Considerate che gli oggetti piu' grandi di 1x1 occupano piu' celle e il punto di ancoraggio e' la cella in basso a sinistra dell'oggetto.

---

## 15. Strumenti per Pixel Art Isometrica

### Editor Consigliati

| Strumento | Tipo | Prezzo | Ideale per |
|-----------|------|--------|------------|
| **Aseprite** | Pixel art editor | $20 (o compilare gratis da sorgente) | Animazioni sprite sheet, palette, onion skinning |
| **Piskel** | Pixel art editor (web) | Gratuito | Prototipi veloci, sprite semplici, accessibile da browser |
| **Pyxel Edit** | Tile map editor | $9 | Tileset isometrici, tile animation, auto-tiling |
| **Tiled** | Map editor | Gratuito (open source) | Level design, mappe isometriche, esportazione JSON |
| **GIMP** | Image editor | Gratuito (open source) | Post-processing, batch resize, palette editing |

### Consigli per Sprite Isometrici

1. **Usate una griglia guida**: Create un template con la griglia isometrica (diamante 64x32) e disegnateci sopra
2. **Angolo 30 gradi**: Le linee orizzontali isometriche hanno un rapporto 2:1 (ogni 2 pixel orizzontali, 1 pixel verticale)
3. **Ombre consistenti**: Decidete una direzione della luce (es. alto-sinistra) e mantenetela per tutti gli oggetti
4. **Palette limitata**: Usate massimo 16-32 colori per mantenere coerenza visiva
5. **Outline**: Per oggetti piccoli, un contorno di 1px aiuta la leggibilita'
6. **Test nel gioco**: Importate lo sprite in Godot appena possibile per verificare scale e posizionamento

---

## 16. Giochi Famosi: Tecniche Isometriche nel Dettaglio

### Stardew Valley — "Finta" Isometrica

Stardew Valley NON e' tecnicamente isometrico — usa una vista top-down con prospettiva leggermente inclinata. Ma molti lo percepiscono come isometrico per via di:
- **Profondita' simulata**: gli oggetti in basso sono "davanti" (Y-Sort)
- **Ombre proiettate**: danno l'illusione di tridimensionalita'
- **Proporzioni personaggio**: il personaggio e' disegnato come visto da un angolo leggermente elevato

**Lezione per Relax Room**: Non serve un sistema isometrico "puro" per dare l'illusione di profondita'. Il nostro progetto usa lo stesso approccio di Stardew Valley.

### Habbo Hotel — Isometrico Classico

Habbo Hotel e' un esempio perfetto di isometrico 2:1 con pixel art:
- Griglia diamante rigorosa (ogni tile e' un diamante)
- Sprite dei mobili disegnati con la stessa angolazione
- Sistema di profondita' basato sulla posizione nella griglia
- Stanze personalizzabili (la stessa idea di Relax Room!)

**Lezione per Relax Room**: Il nostro sistema di decorazioni segue lo stesso principio di Habbo — posizionamento su griglia con snap.

### Unpacking — Isometrico Narrativo

Unpacking usa la vista isometrica per raccontare una storia attraverso gli oggetti:
- Ogni oggetto ha una posizione "naturale" suggerita
- Il giocatore scopre la personalita' del personaggio tramite i suoi oggetti
- La griglia e' nascosta ma presente (snap gentile)

**Lezione per Relax Room**: La personalizzazione della stanza NON e' solo estetica — racconta qualcosa dell'utente. Questo e' il motivo per cui il gioco salva la posizione esatta di ogni decorazione.

---

*Study document for Relax Room — IFTS Projectwork 2026*
*Author: Renan Augusto Macena (System Architect & Project Supervisor)*

---

## Exercises

1. **Lab — cartesian-to-iso transform.** Implement Python or GDScript function that converts (cart_x, cart_y) → (iso_x, iso_y). Test on grid 8x8.
2. **Lab — character moving on iso grid.** CharacterBody2D walks on iso tile grid; uses cartesian coords internally, renders iso.
3. **Stretch — y-sort with multi-tile actor.** Actor occupies 2x2 tiles; resolve sorting correctly when overlapping single-tile decoration.

## Self-assessment

1. Iso angle: typical degrees?
2. Tile aspect ratio: why 2:1?
3. Depth sorting: y-sort limitation example.
4. Diablo vs SimCity: difference in projection.

## Cross-links

- Module 04 — `RENDERING_AND_VISUAL_LOGIC.md`: y-sort.
- Module 05 — `TILES_AND_TILEMAPS.md`: iso TileMapLayer.

## Local glossary

| Term | Definition |
|---|---|
| **Isometric** | 2D projection mimicking 3D at fixed angle (~30°). |
| **Dimetric** | Variation with two scaling axes (Diablo). |
| **Cartesian-to-iso transform** | Math conversion from grid to screen. |
| **Depth sorting** | Determining draw order. |
| **y-sort** | Auto-sort by Y position. |
| **2:1 tile** | 32x16 or 64x32; standard iso. |
