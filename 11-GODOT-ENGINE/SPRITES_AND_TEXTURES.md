# Sprite, Texture e Animazioni — Godot 4.6

> **Modulo del corso:** Godot 4 in Production
> **Posizione:** Fase 1 — Foundations · Modulo 03
> **Prerequisiti:** Modulo 02; concetti pixel art (DPI, MIP, filtering).
> **Obiettivi:** Sprite2D, AtlasTexture, AnimatedSprite2D, SpriteFrames; texture filtering pixel-art (`Nearest`); spritesheet layout; import settings.
> **Tempo:** lettura 45 min · lab 120-180 min
> **Livello:** novice → competent
> **Ultimo aggiornamento:** 2026-04-27

## Idee guida

1. **Pixel art = `Nearest` filter, non `Linear`.** Linear sfoca; Nearest preserva crisp edges.
2. **AtlasTexture > N file separati.** Riduce file count, abilita batching.
3. **AnimatedSprite2D vs AnimationPlayer: sprite frame vs property tween.** Sprite per character idle/walk, AnimationPlayer per cutscene complex.
4. **Import `Repeat = Disabled` per spritesheet.** Evita bleeding tra frame adiacenti.

> Documento di studio per il team Relax Room.
> Copre i fondamenti delle sprite, texture e animazioni in Godot 4.6,
> con riferimenti diretti al nostro codice sorgente.

---

## 1. Concetti Chiave

### 1.1 Sprite2D

Il nodo base per mostrare un'immagine 2D nella scena.

**Proprieta' principali:**

| Proprieta' | Tipo | Descrizione |
|------------|------|-------------|
| `texture` | Texture2D | L'immagine da mostrare |
| `centered` | bool | Se `true`, l'origine e' al centro della texture. Se `false`, e' in alto a sinistra |
| `offset` | Vector2 | Spostamento visuale rispetto all'origine del nodo |
| `flip_h` / `flip_v` | bool | Specchia la sprite orizzontalmente / verticalmente |
| `hframes` / `vframes` | int | Divide la texture in una griglia di frame (colonne / righe) |
| `frame` | int | Quale frame della griglia mostrare (indice da 0) |
| `texture_filter` | enum | Filtro di rendering (NEAREST per pixel art, LINEAR per grafica smooth) |

**Esempio — creare una sprite via codice:**
```gdscript
var sprite := Sprite2D.new()
sprite.texture = load("res://assets/room/room.png")
sprite.centered = true
sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
sprite.scale = Vector2(4.0, 4.0)
add_child(sprite)
```

**hframes/vframes — Sprite Sheet senza AnimatedSprite2D:**

Quando una texture contiene piu' frame in una griglia, puoi usare `hframes` e `vframes` per suddividerla:

```gdscript
# Spritesheet con 4 frame orizzontali, 1 riga
sprite.hframes = 4
sprite.vframes = 1
sprite.frame = 0  # Mostra il primo frame

# Per animare manualmente, cambia frame nel tempo:
sprite.frame = (sprite.frame + 1) % sprite.hframes
```

Questo e' utile quando vuoi controllare l'animazione manualmente (es. con un Timer) senza usare AnimatedSprite2D.

### 1.2 texture_filter — Pixel Art vs Grafica Smooth

Il filtro della texture determina come i pixel vengono interpolati durante lo zoom:

| Filtro | Effetto | Quando usare |
|--------|---------|--------------|
| `TEXTURE_FILTER_NEAREST` | Pixel netti, nessun blending | **Pixel art** (il nostro caso) |
| `TEXTURE_FILTER_LINEAR` | Pixel sfumati, anti-aliasing | Grafica HD, fotorealistico |
| `TEXTURE_FILTER_PARENT_NODE` | Eredita dal nodo padre | Default |

**Regola fondamentale:** Per pixel art, usa SEMPRE `TEXTURE_FILTER_NEAREST`. In caso contrario i pixel piccoli diventeranno sfocati quando scalati (es. da 32x32 a 128x128).

Il nostro progetto imposta il filtro globale in `project.godot`:
```
rendering/textures/canvas_textures/default_texture_filter = 0  # Nearest
```

Ma ogni sprite puo' sovrascrivere il filtro individualmente via codice.

### 1.3 AtlasTexture

Un `AtlasTexture` e' una "finestra" su una texture piu' grande. Invece di avere 100 file PNG separati, puoi avere un singolo spritesheet e ritagliare regioni specifiche.

**Proprieta':**
- `atlas` (Texture2D) — la texture sorgente (il foglio completo)
- `region` (Rect2) — il rettangolo da ritagliare: `Rect2(x, y, larghezza, altezza)`

**Esempio concettuale:**
```gdscript
# Spritesheet: 128x32 pixel, 4 frame da 32x32
var atlas_tex := AtlasTexture.new()
atlas_tex.atlas = load("res://assets/charachters/male/old/male_idle/male_idle_down.png")
atlas_tex.region = Rect2(0, 0, 32, 32)    # Primo frame
# atlas_tex.region = Rect2(32, 0, 32, 32)  # Secondo frame
# atlas_tex.region = Rect2(64, 0, 32, 32)  # Terzo frame
# atlas_tex.region = Rect2(96, 0, 32, 32)  # Quarto frame
```

Godot usa internamente AtlasTexture nei file `.tscn` per definire i frame delle SpriteFrames.

### 1.4 AnimatedSprite2D e SpriteFrames

`AnimatedSprite2D` e' il nodo dedicato alle animazioni sprite. Usa una risorsa `SpriteFrames` che contiene una o piu' animazioni nominate, ciascuna con i propri frame.

**Struttura gerarchica:**
```
AnimatedSprite2D
  └── sprite_frames: SpriteFrames
        ├── "idle_down"    → [frame0, frame1, frame2, frame3]  @ 5 fps
        ├── "walk_side"    → [frame0, frame1, frame2, frame3]  @ 5 fps
        ├── "rotate"       → [frame0..frame7]                  @ 3 fps
        └── ... (altre animazioni)
```

**Controllo da codice:**
```gdscript
@onready var anim: AnimatedSprite2D = $AnimatedSprite2D

# Riprodurre un'animazione
anim.play("walk_down")

# Fermare l'animazione
anim.stop()

# Controllare quale animazione sta suonando
if anim.animation == "idle_down":
    anim.play("walk_down")

# Specchiare orizzontalmente (es. camminata a sinistra)
anim.flip_h = true
```

**SpriteFrames — come si definisce in .tscn:**

Ogni frame di un'animazione e' un AtlasTexture con la regione specifica:
```
# Esempio dal nostro male-old-character.tscn (semplificato)
[sub_resource type="AtlasTexture"]
atlas = ExtResource("male_idle_down.png")  # Spritesheet 128x32
region = Rect2(0, 0, 32, 32)              # Frame 0

[sub_resource type="AtlasTexture"]
atlas = ExtResource("male_idle_down.png")
region = Rect2(32, 0, 32, 32)             # Frame 1
# ... e cosi' via per tutti i frame
```

### 1.5 AnimatedSprite2D vs Sprite2D + hframes — Quando usare quale

| Criterio | AnimatedSprite2D | Sprite2D + hframes |
|----------|-----------------|-------------------|
| **Animazioni multiple** | Supporta N animazioni nominate | Solo 1 griglia alla volta |
| **Controllo** | `play("nome")`, autoplay, loop | Manuale via Timer + `frame` |
| **Performance** | Leggero overhead per gestione frame | Minimale |
| **Flessibilita'** | Velocita' diverse per animazione | Stessa velocita' per tutti i frame |
| **Quando usare** | Personaggi con molte animazioni | Animazioni semplici, effetti, UI |

### 1.6 Impostazioni di Import delle Texture

Ogni file `.png` importato in Godot genera un file `.import` con le impostazioni di conversione.

**Le nostre impostazioni standard (pixel art):**
```ini
importer="texture"
type="CompressedTexture2D"

[params]
compress/mode=0              # 0 = NESSUNA COMPRESSIONE (preserva pixel art)
compress/high_quality=false
mipmaps/generate=false       # No mipmap (non serve per 2D pixel art)
process/fix_alpha_border=true  # Corregge artefatti sui bordi trasparenti
```

**Perche' queste impostazioni?**
- `compress/mode=0` — La compressione (es. VRAM) modifica i colori e introduce artefatti. Per pixel art vogliamo pixel perfetti.
- `mipmaps/generate=false` — I mipmap creano versioni ridotte della texture per rendering a distanza. In un gioco 2D top-down non servono e sprechiamo solo VRAM.
- `fix_alpha_border=true` — Quando una sprite ha bordi trasparenti, il filtraggio lineare puo' "mescolare" pixel trasparenti con quelli opachi, creando una riga scura. Questo fix previene il problema.

---

## 2. Nel Nostro Progetto

### 2.1 Sistema Personaggio — 8 Direzioni

Il nostro personaggio principale (`male_old`) ha **16 animazioni** organizzate in 8 direzioni:

**Struttura degli spritesheet:**
```
assets/charachters/male/old/
├── male_idle/
│   ├── male_idle_down.png          # 128x32 (4 frame di 32x32)
│   ├── male_idle_down_side.png
│   ├── male_idle_down_side_sx.png
│   ├── male_idle_side.png
│   ├── male_idle_side_sx.png
│   ├── male_idle_up.png
│   ├── male_idle_up_side.png
│   └── male_idle_up_side_sx.png
├── male_walk/   (stessa struttura)
├── male_interact/  (stessa struttura)
└── male_rotate/
    └── male_rotate.png             # 256x32 (8 frame di 32x32)
```

Ogni strip e' larga 128px con 4 frame da 32x32. L'eccezione e' `rotate` che ha 8 frame (256x32).

**Come funziona nel .tscn (`scenes/male-old-character.tscn`):**

Il nodo `AnimatedSprite2D` ha:
- `texture_filter = 0` (Nearest)
- `scale = Vector2(3, 3)` — i 32px diventano 96px sullo schermo
- `SpriteFrames` con tutte le 16 animazioni, ciascuna usando `AtlasTexture` regions:
  - **idle** (5): idle_down, idle_side, idle_up, idle_vertical_down, idle_vertical_up
  - **walk** (5): walk_down, walk_side, walk_up, walk_side_down, walk_side_up
  - **interact** (5): interact_down, interact_side, interact_up, interact_vertical_down, interact_vertical_up
  - **rotate** (1): 8 frame a 3.0 fps (tutte le altre sono a 5.0 fps)

**Come viene controllato (`scripts/rooms/character_controller.gd`):**

```gdscript
# Linea 10 — riferimento al nodo AnimatedSprite2D
@onready var _anim: AnimatedSprite2D = $AnimatedSprite2D

# Linee 48-62 — selezione animazione basata sulla direzione
var abs_x := absf(direction.x)
var abs_y := absf(direction.y)
if abs_x > abs_y * DIRECTION_THRESHOLD:   # Movimento prevalentemente laterale
    _anim.flip_h = direction.x < 0        # Specchia per camminata a sinistra
    anim_name = "walk_side"
elif abs_y > abs_x * DIRECTION_THRESHOLD:  # Movimento prevalentemente verticale
    anim_name = "walk_down" if direction.y > 0 else "walk_up"
elif direction.y > 0:                      # Diagonale in basso
    _anim.flip_h = direction.x < 0
    anim_name = "walk_side_down"
else:                                      # Diagonale in alto
    _anim.flip_h = direction.x < 0
    anim_name = "walk_side_up"
```

**Il trucco del `DIRECTION_THRESHOLD` (1.2):** Crea una "zona morta" che rende piu' facile camminare dritto. Se il joystick e' leggermente diagonale, viene interpretato come rettilineo.

### 2.2 MenuCharacter — Animazione Manuale con Sprite2D

Nella schermata del menu, il personaggio cammina da sinistra a destra usando un approccio diverso: `Sprite2D` + `hframes` + `Timer` (`scripts/menu/menu_character.gd`).

```gdscript
# Linee 41-49 — Creazione sprite con griglia di frame
_sprite = Sprite2D.new()
_sprite.texture = load(char_data["walk_path"])  # male_walk_side.png (128x32)
_sprite.hframes = 4       # 4 colonne
_sprite.vframes = 1       # 1 riga
_sprite.frame = 0         # Primo frame
_sprite.flip_h = false
_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
_sprite.scale = Vector2(4.0, 4.0)  # 32px → 128px

# Linee 55-59 — Timer per ciclo frame
_frame_timer = Timer.new()
_frame_timer.wait_time = FRAME_INTERVAL  # 0.15 secondi (≈6.67 fps)
_frame_timer.timeout.connect(_next_frame)

# Linee 68-70 — Avanzamento frame
func _next_frame() -> void:
    _current_frame = (_current_frame + 1) % _hframes  # 0→1→2→3→0→1...
    _sprite.frame = _walk_row * _hframes + _current_frame
```

**Perche' non usare AnimatedSprite2D qui?** Perche' serve una sola animazione (walk_side) per una breve sequenza. Creare un intero SpriteFrames per 4 frame sarebbe eccessivo.

### 2.3 Decorazioni — Sprite Dinamiche da Codice

Le decorazioni vengono create runtime in `scripts/rooms/room_base.gd`:

```gdscript
# Linee 96-104 — Creazione sprite decorazione
var sprite := Sprite2D.new()
sprite.centered = false                              # Origine in alto a sinistra
sprite.texture = load(sprite_path) as Texture2D      # Da decorations.json
sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
sprite.scale = Vector2(item_scale, item_scale)       # Da JSON: 3.0/6.0/4.0
sprite.position = pos                                # Posizione nel mondo
sprite.rotation_degrees = rot                        # 0/90/180/270
sprite.flip_h = flipped                              # Specchiato o no
```

**`centered = false`** e' cruciale: il punto di origine e' in alto a sinistra della texture, non al centro. Questo rende piu' facile il posizionamento grid-based (snap a griglia di 64px).

**Scale per categoria (da `decorations.json`):**
- Mobili (letti, scrivanie, sedie, armadi): `item_scale = 3.0`
- Piante (con e senza vaso): `item_scale = 6.0`
- Animali (Void Cat): `item_scale = 4.0`

### 2.4 Loading Screen — AnimatedSprite2D in Scena

La schermata di caricamento (`scenes/menu/loading_screen.tscn`) usa AnimatedSprite2D:

```
background (Sprite2D) → loading/background.png
├── Camera2D (zoom: 3.6x)
├── characters (AnimatedSprite2D)
│   ├── animation: "loading" (4 frame, 5.0 fps)
│   ├── autoplay: "loading"
│   └── scale: (1.65625, 1.65625)
├── bar (Sprite2D) → loading/loading_base_bar.png
└── title (AnimatedSprite2D)
    ├── animation: "default" (4 frame, 5.0 fps)
    └── scale: (0.90625, 0.90625)
```

Il `Camera2D` con zoom 3.6x ingrandisce tutto per l'effetto pixel art.

---

## 3. Best Practice per Pixel Art

1. **Filtro texture**: Sempre `TEXTURE_FILTER_NEAREST`. Impostalo globale in `project.godot` E per sicurezza per ogni sprite creata via codice.

2. **Dimensioni sprite**: Mantieni potenze di 2 dove possibile (16, 32, 64, 128). Non e' obbligatorio ma migliora le performance GPU.

3. **Spritesheet layout**: Usa strip orizzontali (hframes) per animazioni semplici, grid (hframes × vframes) per set complessi. Il nostro standard e' 4 frame per strip da 128x32.

4. **Scale uniformi**: Scala sempre con `Vector2(n, n)` (stessa scala X e Y) per evitare distorsione pixel.

5. **`centered = false` per placement grid-based**: Quando le sprite devono allinearsi a una griglia, usa `centered = false` cosi' la posizione corrisponde all'angolo in alto a sinistra.

6. **Import settings**: Non modificare le impostazioni di import a mano. Il default del progetto (`compress/mode=0`, no mipmap) va bene per tutto il pixel art.

7. **AtlasTexture vs file separati**: Per i personaggi, strip da 128x32 con AtlasTexture regions. Per decorazioni/mobili, file singoli sono piu' semplici da gestire.

---

## 4. Riferimenti

- [Sprite2D — Godot 4.6 Docs](https://docs.godotengine.org/en/4.6/classes/class_sprite2d.html)
- [AnimatedSprite2D](https://docs.godotengine.org/en/4.6/classes/class_animatedsprite2d.html)
- [SpriteFrames](https://docs.godotengine.org/en/4.6/classes/class_spriteframes.html)
- [AtlasTexture](https://docs.godotengine.org/en/4.6/classes/class_atlastexture.html)
- [2D Sprite Animation Tutorial](https://docs.godotengine.org/en/4.6/tutorials/2d/2d_sprite_animation.html)
- [Importing Images](https://docs.godotengine.org/en/4.6/tutorials/assets_pipeline/importing_images.html)

---

## Esercizi

1. **Lab — character animation.** SpriteFrames con 4 animazioni (idle, walk, run, jump) da spritesheet 32x32 px; AnimatedSprite2D + state machine.
2. **Lab — atlas optimization.** Misura draw call con 100 sprite singoli vs atlas; mostra differenza con profiler.
3. **Stretch — pixel art shader.** Implementa shader che fa scanline o CRT effect senza rovinare crisp pixel.

## Auto-valutazione

1. Filter `Nearest` vs `Linear`: quando uno o l'altro?
2. AtlasTexture: vantaggio principale.
3. AnimatedSprite2D vs AnimationPlayer: criterio di scelta.
4. Repeat import setting: cosa fa?

## Collegamenti incrociati

- Modulo 04 — `RENDERING_AND_VISUAL_LOGIC.md`: tween e modulate.
- Modulo 12 — `SHADERS_GDSHADER.md` (NEW): shader pixel-art.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Sprite2D** | Nodo per immagine statica. |
| **AnimatedSprite2D** | Nodo per sprite frames animate. |
| **AtlasTexture** | Texture region da una piu grande (atlas). |
| **SpriteFrames** | Resource con frame multipli per animazione. |
| **`Nearest` filter** | No interpolation; pixel art. |
| **`Linear` filter** | Bilinear interpolation; smooth. |
| **Spritesheet** | Singola immagine con frame multipli a griglia. |
| **Texture bleeding** | Pixel di frame adiacente che bleed. |
