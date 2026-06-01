# GDShader — Shaders in Godot 4

> **Course module:** Godot 4 in Production
> **Position:** Phase 5 — New modules · Module 12 (NEW)
> **Prerequisites:** Modules 03, 04; basic linear algebra (vec2/vec3/vec4); GLSL or HLSL exposure helpful.
> **Learning objectives:** GDShader syntax (canvas_item, spatial); built-ins (TIME, UV, COLOR); uniform vars; pixel-art shader recipes (CRT, scanline, dither); shader-vs-tween rule.
> **Estimated time:** 60-90 min reading · 240 min hands-on
> **Level:** competent → proficient
> **Last updated:** 2026-04-27
> **Pinned:** Godot 4.5 GDShader (variant of GLSL ES 3.0).

## Guiding ideas

1. **GDShader is GLSL-flavored, not GLSL exact.** Some keywords differ (`render_mode`, `shader_type`).
2. **canvas_item shaders for 2D, spatial for 3D.** No mixing.
3. **`TIME` built-in is your animation clock.** No need to pass uniform from script.
4. **Shader > tween for visual effects.** Tween animates property; shader animates pixel.
5. **Pixel-art needs care.** Don't break the crisp grid with bilinear filter; explicit `texture(SCREEN_TEXTURE, UV)` not free.

## Common recipes

### Outline (canvas_item)

```glsl
shader_type canvas_item;

uniform vec4 outline_color : source_color = vec4(1.0);
uniform float thickness : hint_range(0.0, 5.0) = 1.0;

void fragment() {
    vec2 px = TEXTURE_PIXEL_SIZE;
    float a = texture(TEXTURE, UV).a;
    float top    = texture(TEXTURE, UV + vec2(0.0, -px.y * thickness)).a;
    float bottom = texture(TEXTURE, UV + vec2(0.0,  px.y * thickness)).a;
    float left   = texture(TEXTURE, UV + vec2(-px.x * thickness, 0.0)).a;
    float right  = texture(TEXTURE, UV + vec2( px.x * thickness, 0.0)).a;
    float outline = step(0.01, top + bottom + left + right) * (1.0 - a);
    COLOR = mix(texture(TEXTURE, UV), outline_color, outline);
}
```

### CRT effect (scanline + curvature)

```glsl
shader_type canvas_item;

uniform float scanline_intensity : hint_range(0.0, 1.0) = 0.5;
uniform float scanline_count = 240.0;

void fragment() {
    vec4 base = texture(TEXTURE, UV);
    float scanline = sin(UV.y * scanline_count * 3.14159) * 0.5 + 0.5;
    base.rgb *= mix(1.0, scanline, scanline_intensity);
    COLOR = base;
}
```

### Dither

Implement Bayer matrix lookup; standard pixel-art trick.

## Exercises

1. **Lab — outline shader.** Apply outline shader to character; uniform-controllable color and thickness.
2. **Lab — animated shader via TIME.** Pulsing glow on hover; use `sin(TIME * speed)`.
3. **Stretch — CRT effect.** Combine scanline + screen curvature + RGB shift. Apply to viewport.

## Self-assessment

1. canvas_item vs spatial shader: scope.
2. `TIME` built-in: source.
3. Shader vs tween: criterion.
4. Pixel-art bilinear filter pitfall.
5. Texture sampling cost: cheap or expensive?

## Primary reading

- Godot — Shading language reference. https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/
- The Book of Shaders. https://thebookofshaders.com/
- Godot Shaders community. https://godotshaders.com/

## Cross-links

- Module 03 — `SPRITES_AND_TEXTURES.md`.
- Module 04 — `RENDERING_AND_VISUAL_LOGIC.md`.

## Local glossary

| Term | Definition |
|---|---|
| **GDShader** | Godot's shader language. |
| **`shader_type canvas_item`** | 2D shader. |
| **`shader_type spatial`** | 3D shader. |
| **`TIME`** | Built-in clock for animation. |
| **`UV`** | Texture coordinates. |
| **`COLOR`** | Output fragment color. |
| **`TEXTURE_PIXEL_SIZE`** | Pixel size on screen. |
| **Uniform** | Value set from GDScript, constant per draw. |
| **CRT effect** | Cathode-ray tube emulation effect. |
| **Bayer matrix** | Ordered dither pattern. |
