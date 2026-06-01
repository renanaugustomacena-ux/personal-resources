# Glossary — Godot 4 in Production

> Aggregate of local glossaries from all modules. Last updated 2026-04-27.

## A-G

| Term | Definition |
|---|---|
| **AAB** | Android App Bundle. |
| **APK** | Android Package. |
| **AppImage** | Linux portable single-file binary. |
| **Atlas source** | Tile source from spritesheet. |
| **AtlasTexture** | Texture region from a larger atlas. |
| **AnimatedSprite2D** | Node for sprite-frame animation. |
| **AnimationPlayer** | Node for keyframed property animation. |
| **Autoload** | Globally accessible singleton. |
| **Autotiling** | Auto-generation of tile transitions. |
| **Bayer matrix** | Ordered dither pattern. |
| **CanvasLayer** | Layer composed on top of viewport. |
| **canvas_item shader** | 2D shader. |
| **Cartesian-to-iso** | Coordinate transform. |
| **CharacterBody2D** | Kinematic body for character control. |
| **CI/CD** | Continuous Integration / Deployment. |
| **Code signing** | Cryptographic signature on binary. |
| **`COLOR`** | Output fragment color in shader. |
| **CRT effect** | Cathode-ray tube emulation. |
| **Custom `_draw()`** | Custom 2D drawing callback. |
| **Dependency injection** | Pass dependencies to constructor. |
| **Depth sorting** | Determining draw order. |
| **Dimetric** | Two-axis-scale projection variant. |
| **`Engine.max_fps`** | Cap frame rate runtime. |
| **Export template** | Godot binary used to package per platform. |
| **FPS budget** | Target frame rate per scenario. |
| **Frame time** | ms per frame. |
| **GdUnit4** | Deprecated testing framework. |
| **GDExtension** | Native extension API for Godot 4. |
| **GDScript** | Godot's primary scripting language. |
| **GDShader** | Godot's shader language. |
| **GPUParticles2D** | GPU-accelerated particles. |
| **Group** | Tag for nodes; query via `get_nodes_in_group`. |

## H-O

| Term | Definition |
|---|---|
| **Headless export** | Game exported without rendering for tests. |
| **Inno Setup** | Windows installer creator. |
| **`instantiate()`** | Create instance from PackedScene. |
| **Init order** | Alphabetical sequence of autoloads. |
| **Init-time assertion** | `assert()` in `_ready` to catch misconfig. |
| **Isometric** | 2D projection mimicking 3D at fixed angle. |
| **`_init`/`_enter_tree`/`_ready`** | Node lifecycle callbacks. |
| **Linear filter** | Bilinear interpolation; smooth. |
| **Migration chain** | Sequence v1 → vN of save schema. |
| **`modulate`** | Tint color applicable to Sprite2D/Control. |
| **Nearest filter** | No interpolation; pixel art. |
| **Node** | Building block of a scene. |
| **Notarization** | Apple cert verification for macOS apps. |
| **Offline-first** | App functions without network. |
| **`owner`** | Property for scene serialization. |

## P-T

| Term | Definition |
|---|---|
| **PackedScene** | Serialized scene used for instancing. |
| **ParallaxBackground** | Background scrolling at different speeds. |
| **`Performance.get_monitor`** | Built-in metrics API. |
| **Physics layer** | Layer collision for tile or body. |
| **Pre-modification checklist** | Steps before changing prod code. |
| **`_process` / `_physics_process`** | Per-frame / fixed-rate callbacks. |
| **`queue_free()`** | Mark node for deferred deletion. |
| **`queue_redraw()`** | Force `_draw()` on next frame. |
| **Refactoring** | Restructuring code without behavior change. |
| **Repeat (import)** | Texture wrap setting. |
| **Resource** | Reusable data asset. |
| **ResourceLoader / ResourceSaver** | Godot APIs for resource I/O. |
| **Scanline shader** | CRT-like pattern overlay. |
| **Scene** | Composition of nodes saved as `.tscn`. |
| **Scene tree** | Runtime hierarchy. |
| **Schema versioning** | Tracking version of save data. |
| **Server architecture** | RenderingServer/PhysicsServer/AudioServer. |
| **`set_process(false)`** | Disable `_process` on a node. |
| **Signal** | Event emitted by node. |
| **spatial shader** | 3D shader. |
| **Sprite2D** | Node for static image. |
| **Spritesheet** | Single image with multiple frames. |
| **SpriteFrames** | Resource with frame collections. |
| **SQLite** | Embedded SQL database. |
| **Supabase** | Open-source Firebase alternative. |
| **Technical debt** | Code shortcuts taken to ship. |
| **Terrain** | Set of tiles with auto-transition. |
| **Texture bleeding** | Pixel of adjacent frame leaking. |
| **Theme** | Resource for UI Control coherence. |
| **TileMap** | Deprecated; use TileMapLayer. |
| **TileMapLayer** | Godot 4.4+ tile grid node. |
| **TileSet** | Resource with palette of tiles. |
| **`TIME`** | Built-in shader clock. |
| **Tween** | Property interpolation over time. |

## U-Z

| Term | Definition |
|---|---|
| **Uniform** | Shader value set from script. |
| **`UV`** | Texture coordinates in shader. |
| **VirtIO** | Standard for paravirtualized I/O (game-irrelevant; appears for context only). |
| **Viewport** | Render target. |
| **Y-sort** | Auto-sort by Y position. |
| **Z-index** | Manual vertical render ordering. |
