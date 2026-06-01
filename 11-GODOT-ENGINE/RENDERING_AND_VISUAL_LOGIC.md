# Rendering 2D, Disegno e Animazione — Godot 4.6

> **Modulo del corso:** Godot 4 in Production
> **Posizione:** Fase 2 — Visual systems · Modulo 04
> **Prerequisiti:** Moduli 01-03; matrix transform basics.
> **Obiettivi:** z-index/y-sort; `_draw()` custom rendering; tween animations; viewport/CanvasLayer; parallax; theme system; modulate.
> **Tempo:** lettura 60 min · lab 180 min
> **Livello:** competent
> **Ultimo aggiornamento:** 2026-04-27
> **Note Godot 4.5:** alcuni esempi sono validi anche per 4.6.

## Idee guida

1. **z-index < y-sort per isometric.** y-sort ordina automatic per posizione Y; z-index manuale.
2. **`_draw()` per primitive custom; non per game logic.** Run nel render pass; chiamare `queue_redraw()` quando dati cambiano.
3. **Tween > AnimationPlayer per transitions semplici.** API piu compatta; auto-cleanup.
4. **CanvasLayer per UI fisso (HUD, menu).** Si compone su top del viewport, no parallax.
5. **Parallax tramite `ParallaxBackground` o ParallaxLayer.** Velocita scaling per layer.

> Documento di studio per il team Relax Room.
> Copre il rendering 2D, disegno custom, z-ordering, tweens,
> viewport, temi e parallasse — con riferimenti al nostro codice.

---

## 1. Concetti Chiave

### 1.1 CanvasItem — La Base del Rendering 2D

Tutti i nodi visibili in 2D (Sprite2D, Control, Label, ColorRect...) ereditano da `CanvasItem`. Questo fornisce:

| Proprieta' | Tipo | Effetto |
|------------|------|---------|
| `visible` | bool | Mostra/nasconde il nodo e tutti i figli |
| `modulate` | Color | Moltiplica colore del nodo E dei figli |
| `self_modulate` | Color | Moltiplica colore SOLO del nodo (non i figli) |
| `z_index` | int | Ordine di disegno (-4096 a 4096) |
| `z_as_relative` | bool | Se z_index e' relativo al padre |

**`modulate` vs `self_modulate`:**
```gdscript
# modulate: colora il nodo E tutti i figli
sprite.modulate = Color(1, 0, 0, 0.5)  # Rosso semi-trasparente per tutto

# self_modulate: colora SOLO il nodo
sprite.self_modulate = Color(1, 0, 0, 0.5)  # Solo questa sprite rossa

# L'alpha di modulate si moltiplica:
# padre.modulate.a = 0.5  +  figlio.modulate.a = 0.5  →  figlio visibile al 25%
```

### 1.2 Z-Index — Ordine di Disegno

Il `z_index` controlla quale nodo viene disegnato sopra quale:

```
z_index = -1  → Dietro (es. sfondo)
z_index =  0  → Default
z_index =  1  → Davanti
z_index = 100 → Molto in primo piano (es. auth screen)
```

**`z_as_relative = true` (default):** Il z_index si somma a quello del padre.
```
Padre (z_index = 5)
└── Figlio (z_index = 2, z_as_relative = true)
    → Z effettivo: 5 + 2 = 7
```

**CanvasLayer sovrascrive il z_index:** I nodi dentro un CanvasLayer sono su un layer separato. `layer = 10` e' SEMPRE sopra `layer = 0`, indipendentemente dal z_index.

### 1.3 Custom Drawing — _draw()

Ogni `CanvasItem` puo' disegnare forme primitive sovrascrivendo `_draw()`:

```gdscript
extends Node2D

func _draw() -> void:
    # Linea
    draw_line(Vector2(0, 0), Vector2(100, 0), Color.WHITE, 1.0)

    # Rettangolo pieno
    draw_rect(Rect2(10, 10, 50, 30), Color.RED)

    # Rettangolo bordo
    draw_rect(Rect2(10, 10, 50, 30), Color.GREEN, false, 2.0)

    # Cerchio
    draw_circle(Vector2(50, 50), 20.0, Color.BLUE)

    # Texture
    var tex := preload("res://icon.svg")
    draw_texture(tex, Vector2(100, 0))

    # Stringa di testo
    var font := ThemeDB.fallback_font
    draw_string(font, Vector2(0, 80), "Hello!", HORIZONTAL_ALIGNMENT_LEFT, -1, 16)

# IMPORTANTE: _draw() viene chiamato UNA VOLTA e il risultato viene cachato.
# Per ridisegnare, chiama:
func _qualcosa_cambiato() -> void:
    queue_redraw()  # Forza richiamata di _draw() al prossimo frame
```

**`queue_redraw()`** e' fondamentale: `_draw()` non viene chiamato ogni frame automaticamente. Viene chiamato solo quando necessario (primo rendering, resize, o dopo `queue_redraw()`).

### 1.4 Tweens in Godot 4

I **Tween** sono il modo principale per animare proprieta' nel tempo. In Godot 4 si creano con `create_tween()`.

**Sintassi base:**
```gdscript
# Crea un tween legato a questo nodo
var tween := create_tween()

# Anima una proprieta'
tween.tween_property(sprite, "modulate:a", 0.0, 0.5)
#                     nodo    proprieta'    valore_finale  durata

# Concatena azioni (eseguite in sequenza):
tween.tween_property(sprite, "position", Vector2(100, 0), 1.0)
tween.tween_callback(func(): print("Arrivato!"))
tween.tween_interval(0.5)  # Pausa 0.5 secondi
tween.tween_property(sprite, "modulate:a", 0.0, 0.3)
```

**Easing — Curve di Animazione:**

| Ease | Trans | Effetto | Quando usare |
|------|-------|---------|-------------|
| `EASE_IN` | `TRANS_QUAD` | Lento → veloce | Accelerazione |
| `EASE_OUT` | `TRANS_QUAD` | Veloce → lento | Decelerazione (naturale) |
| `EASE_IN_OUT` | `TRANS_QUAD` | Lento → veloce → lento | Transizioni fluide |
| `EASE_OUT` | `TRANS_LINEAR` | Velocita' costante | Countdown, barre |
| `EASE_OUT` | `TRANS_CUBIC` | Forte decelerazione | Menu, pannelli |
| `EASE_OUT` | `TRANS_ELASTIC` | Effetto molla | Notifiche, badge |
| `EASE_OUT` | `TRANS_BOUNCE` | Effetto rimbalzo | Oggetti che cadono |

```gdscript
var tween := create_tween()
tween.set_ease(Tween.EASE_OUT)
tween.set_trans(Tween.TRANS_QUAD)
tween.tween_property(self, "position", target_pos, 2.0)
```

**Ciclo di vita del Tween in Godot 4:**
- `create_tween()` su un nodo → il tween e' **legato** a quel nodo
- Quando il nodo esce dall'albero → il tween viene **automaticamente killato**
- Per killare un tween anticipatamente: `tween.kill()`

**Attenzione — lezione dal nostro audit (N-Q1, N-Q2):**
Anche se Godot 4 uccide i tween quando il nodo viene distrutto, ci sono due casi problematici:
1. **Tween non salvato in variabile**: Se crei un tween locale (`var tween := create_tween()`) e non lo salvi come membro della classe, non puoi killarlo anticipatamente se serve (es. l'utente chiude un pannello durante il fade-in).
2. **Chiamate multiple**: Se `walk_in()` viene chiamato due volte, il primo tween continua in parallelo col secondo.

**Best practice:** Salva i tween come variabili membro e killa il precedente prima di crearne uno nuovo:
```gdscript
var _tween: Tween

func fade_in() -> void:
    if _tween:
        _tween.kill()           # Killa il tween precedente
    _tween = create_tween()
    _tween.tween_property(self, "modulate:a", 1.0, 0.3)
```

### 1.5 Viewport e Camera2D

Il **Viewport** e' la "finestra" attraverso cui il giocatore vede il gioco.

**Configurazione del nostro progetto (`project.godot`):**
```ini
display/window/size/viewport_width=1280
display/window/size/viewport_height=720
display/window/stretch/mode="canvas_items"
```

- **viewport_width/height**: Risoluzione logica del gioco (1280x720)
- **stretch/mode = "canvas_items"**: Scala il contenuto per adattarsi alla finestra reale, mantenendo il rapporto d'aspetto

**Camera2D:**
```gdscript
var camera := Camera2D.new()
camera.zoom = Vector2(3.6, 3.6)   # Ingrandisci 3.6x (pixel art)
camera.position_smoothing_enabled = true
camera.position_smoothing_speed = 10.0  # Velocita' inseguimento
```

Il **zoom** della Camera2D e' fondamentale per pixel art: un singolo pixel di 1x1 diventa 3.6x3.6 sullo schermo, creando l'effetto "retro" con pixel grandi.

### 1.6 Sistema Theme

Godot ha un sistema **Theme** per stilizzare tutti i nodi Control (Button, Label, Panel, etc.) in modo coerente.

**Come funziona:**
1. Un file `.tres` definisce stili per ogni tipo di Control
2. Si assegna come tema globale in `project.godot` → `gui/theme/custom`
3. Ogni nodo puo' sovrascrivere singoli valori con `add_theme_*_override()`

**StyleBox — I "CSS" di Godot:**

Ogni stato di un Control ha uno StyleBox (come un CSS box model):

```
Button:
  ├── normal   → StyleBoxTexture (sfondo beige)
  ├── hover    → StyleBoxTexture (sfondo chiaro)
  ├── pressed  → StyleBoxTexture (sfondo scuro)
  └── disabled → StyleBoxTexture (sfondo grigio)
```

**StyleBoxTexture (9-Slice):**

Il 9-Slice divide una texture in 9 zone. Gli angoli restano fissi, i bordi si allungano, il centro si espande:
```
┌───┬─────────┬───┐
│ A │    B    │ C │  ← Angoli (A,C,G,I) fissi
├───┼─────────┼───┤     Bordi (B,D,F,H) allungati
│ D │    E    │ F │     Centro (E) espanso
├───┼─────────┼───┤
│ G │    H    │ I │
└───┴─────────┴───┘
```

Questo permette di creare pannelli, bottoni e cornici di qualsiasi dimensione da una singola piccola texture.

---

## 2. Nel Nostro Progetto

### 2.1 Theming della Stanza — ColorRect Overlays

`scripts/main.gd` (linee 50-65) applica il tema colore della stanza:

```gdscript
const OVERLAY_ALPHA := 0.6

func _apply_theme(room_id: String, theme_id: String) -> void:
    var colors := GameManager.get_theme_colors(room_id, theme_id)

    # Muro: 40% superiore dello schermo
    var wall_color := Color(wall_hex)    # Es. Color("2a2535") → viola scuro
    wall_color.a = OVERLAY_ALPHA         # 60% opacita'
    _wall_rect.color = wall_color

    # Pavimento: 60% inferiore
    var floor_color := Color(floor_hex)
    floor_color.a = OVERLAY_ALPHA
    _floor_rect.color = floor_color

    # Battiscopa: 10% piu' chiaro del muro
    _baseboard.color = Color(wall_hex).lightened(0.1)
```

**Come Color() interpreta le stringhe hex:**
```gdscript
Color("2a2535")  → R=0.165, G=0.145, B=0.208  (viola scuro)
Color("3d3347")  → R=0.239, G=0.200, B=0.278  (viola leggermente piu' chiaro)
```

**Layout delle zone:**
```
0px   ┌─────────────────────────┐
      │         MURO             │  ← WallRect (40%)
      │     (wall_color, a=0.6)  │
288px ├─────────────────────────┤  ← Baseboard (1px)
      │       PAVIMENTO          │  ← FloorRect (60%)
      │    (floor_color, a=0.6)  │
720px └─────────────────────────┘
      0px                    1280px
```

### 2.2 Parallasse del Menu — Mouse Tracking

`scripts/rooms/window_background.gd` crea un effetto di profondita' con 8 layer di foresta che si muovono in base alla posizione del mouse:

```gdscript
# Linee 5-7 — Costanti
const PARALLAX_STRENGTH := 8.0    # Pixel di spostamento massimo
const SCALE_FACTOR := 1.38        # 1280 / 928 per riempire il viewport

# Linee 44-54 — Creazione layer (in _build_layers)
for i in valid_count:
    var sprite := Sprite2D.new()
    sprite.texture = valid_textures[i]
    sprite.centered = false
    sprite.scale = Vector2(SCALE_FACTOR, SCALE_FACTOR)
    sprite.position.y = -505.0
    sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
    _parallax_factors.append(float(i) / float(valid_count))  # 0.0 → 1.0

# Linee 57-71 — Aggiornamento parallasse (ogni frame)
func _update_parallax() -> void:
    var mouse := get_viewport().get_mouse_position()
    var center := vp_size * 0.5
    var offset := (mouse - center) / center    # Normalizzato: -1.0 a +1.0

    for i in _layers.size():
        var shift := offset * PARALLAX_STRENGTH * _parallax_factors[i]
        _layers[i].position.x = -shift.x
```

**Come funziona la profondita':**
- Layer 0 (sfondo lontano): `parallax_factor = 0.0` → non si muove
- Layer 4 (mezzo): `parallax_factor = 0.5` → si muove 4px
- Layer 7 (primo piano): `parallax_factor = 1.0` → si muove 8px

Questo crea l'illusione che gli alberi lontani siano fermi mentre quelli vicini si muovono, simulando la profondita'.

### 2.3 Griglia di Piazzamento — Custom _draw()

`scripts/rooms/room_grid.gd` disegna una griglia guida usando `_draw()`:

```gdscript
# Costanti
const CELL_SIZE := 64                          # 64px per cella
const GRID_COLOR := Color(1.0, 1.0, 1.0, 0.12)  # Bianco al 12% opacita'
const WALL_ZONE_RATIO := 0.4                   # 40% = muro
const ROOM_LEFT := 280.0                       # Bordo sinistro della stanza
const ROOM_RIGHT := 1000.0                     # Bordo destro
const ROOM_BOTTOM := 670.0                     # Bordo inferiore

func _draw() -> void:
    if not visible:
        return
    var floor_top := vp.y * WALL_ZONE_RATIO    # 720 * 0.4 = 288px

    # Linee verticali
    var x := ROOM_LEFT                          # Da 280
    while x <= ROOM_RIGHT:                      # A 1000
        draw_line(Vector2(x, floor_top), Vector2(x, ROOM_BOTTOM), GRID_COLOR)
        x += CELL_SIZE                          # Ogni 64px

    # Linee orizzontali
    var y := floor_top                          # Da 288
    while y <= ROOM_BOTTOM:                     # A 670
        draw_line(Vector2(ROOM_LEFT, y), Vector2(ROOM_RIGHT, y), GRID_COLOR)
        y += CELL_SIZE
```

**Visibilita' controllata da segnale:**
```gdscript
func _on_decoration_mode_changed(active: bool) -> void:
    visible = active       # Mostra/nasconde la griglia
    queue_redraw()         # Forza il ridisegno
```

La griglia appare solo in "edit mode" quando il giocatore vuole piazzare/spostare decorazioni.

### 2.4 Animazioni Pannelli — Fade con Tween

`scripts/ui/panel_manager.gd` gestisce l'apertura/chiusura dei pannelli con fade:

```gdscript
# Apertura: fade in da trasparente a opaco
_current_panel.modulate.a = 0.0              # Inizia trasparente
_ui_layer.add_child(_current_panel)          # Aggiunge alla scena
_tween = create_tween()
_tween.tween_property(_current_panel, "modulate:a", 1.0, 0.3)  # 0→1 in 0.3s

# Chiusura: fade out + distruzione
_tween = create_tween()
_tween.tween_property(closing_panel, "modulate:a", 0.0, 0.3)   # 1→0 in 0.3s
_tween.tween_callback(closing_panel.queue_free)                  # Poi distruggi
```

**Nota:** `"modulate:a"` accede direttamente al canale alpha della proprieta' `modulate`. E' equivalente a `modulate = Color(r, g, b, nuovo_alpha)`.

### 2.5 Transizione Scene — Loading Screen Fade

`scripts/menu/main_menu.gd` gestisce la sequenza intro del menu:

```gdscript
# Sequenza intro:
_intro_tween = create_tween()
_intro_tween.tween_interval(0.4)            # 1. Pausa 0.4s (loading visible)
_intro_tween.tween_property(                # 2. Fade out loading screen
    _loading_screen, "modulate:a", 0.0, 0.5  #    1.0 → 0.0 in 0.5s
)
_intro_tween.tween_callback(                # 3. Nasconde loading screen
    _loading_screen.set_visible.bind(false)
)
_intro_tween.tween_callback(                # 4. Avvia walk-in personaggio
    _menu_character.walk_in
)

# Walk-in personaggio (menu_character.gd linee 61-65):
var tween := create_tween()
tween.set_ease(Tween.EASE_OUT)              # Decelerazione naturale
tween.set_trans(Tween.TRANS_QUAD)           # Curva quadratica
tween.tween_property(self, "position",
    Vector2(640, 530), 2.0)                 # Da (-100,530) a (640,530) in 2s
tween.tween_callback(_on_walk_finished)     # Segnala completamento
```

### 2.6 Popup Decorazioni — CanvasLayer Dinamico

`scripts/rooms/decoration_system.gd` (linee 80-137) crea popup interattivi:

```gdscript
# Layer 100 = sopra tutto (anche sopra UILayer che e' 10)
_popup_layer = CanvasLayer.new()
_popup_layer.layer = 100
get_tree().root.add_child(_popup_layer)

# Conversione posizione mondo → schermo
var screen_pos := get_canvas_transform() * global_position
#                  matrice trasformazione    posizione nel mondo
# get_canvas_transform() include: camera zoom, offset, viewport stretch

# Posizionamento centrato sopra la decorazione
_popup.position = Vector2(
    screen_pos.x + tex_size.x * canvas_scale.x * 0.5 - 50,  # Centrato
    screen_pos.y - 36                                          # 36px sopra
)
```

**Perche' CanvasLayer per i popup?** Perche' i bottoni (`Button`) nel popup devono ricevere input GUI. Senza CanvasLayer, i click potrebbero essere intercettati dal `DropZone` (che ha `mouse_filter = PASS`).

### 2.7 cozy_theme.tres — Il Nostro Tema UI

Il file `assets/ui/cozy_theme.tres` definisce lo stile per tutti i Control:

**Fonte:** Kenney Pixel UI Pack — stile "Ancient" (beige/marrone)

**Struttura:**
```
Button:
  ├── normal  → StyleBoxTexture (brown, 9-slice, 5px margins)
  ├── hover   → StyleBoxTexture (tan, 9-slice)
  └── pressed → StyleBoxTexture (grey, 9-slice)

PanelContainer:
  └── panel   → StyleBoxTexture (brown background, 9-slice)

HSlider:
  ├── slider  → StyleBoxTexture (grey, 9-slice)
  └── grabber → StyleBoxTexture (tan, 9-slice)

Label:
  └── font_color → Color(tan/cream)
```

**Override per singolo nodo:**
```gdscript
# Cambiare il colore del testo di un singolo bottone
delete_btn.add_theme_color_override("font_color", Color(0.9, 0.3, 0.3))

# Cambiare la dimensione del font di una singola label
label.add_theme_font_size_override("font_size", 13)

# Aggiungere spazio interno a un contenitore
margin.add_theme_constant_override("margin_left", 12)
```

---

## 3. Costanti di Rendering del Progetto

Tabella riepilogativa dei valori chiave usati nel rendering:

| Costante | Valore | File | Descrizione |
|----------|--------|------|-------------|
| Viewport | 1280 x 720 | project.godot | Risoluzione logica |
| Stretch mode | canvas_items | project.godot | Scala per adattarsi alla finestra |
| Clear color | #1f1c2e | project.godot | Viola scuro di sfondo |
| Default filter | 0 (Nearest) | project.godot | Pixel art netto |
| OVERLAY_ALPHA | 0.6 | main.gd:5 | Trasparenza overlay stanza |
| CELL_SIZE | 64 | room_grid.gd:5 | Dimensione cella griglia |
| ROOM_LEFT | 280 | room_grid.gd:9 | Bordo sinistro stanza |
| ROOM_RIGHT | 1000 | room_grid.gd:10 | Bordo destro stanza |
| ROOM_BOTTOM | 670 | room_grid.gd:11 | Bordo inferiore stanza |
| WALL_ZONE_RATIO | 0.4 | room_grid.gd:7 | 40% muro, 60% pavimento |
| PARALLAX_STRENGTH | 8.0 | window_background.gd:5 | Movimento parallasse |
| PANEL_TWEEN_DURATION | 0.3 | constants.gd | Durata fade pannelli |
| FADE_DURATION | 0.5 | constants.gd | Durata fade scene |
| Character scale | 3.0 (in-game) / 4.0 (menu) | *.tscn, menu_character.gd | Upscaling personaggio |
| Furniture scale | 3.0 | decorations.json | Scala mobili |
| Plants scale | 6.0 | decorations.json | Scala piante |
| Pet scale | 4.0 | decorations.json | Scala animali |

---

## 4. Best Practice

1. **z_index per layering semplice, CanvasLayer per separazione forte**: Usa z_index per ordinare elementi nello stesso "mondo". Usa CanvasLayer per UI che non deve essere influenzata dalla camera.

2. **`queue_redraw()` dopo modifiche visuali**: Se usi `_draw()`, ricorda che non viene richiamato automaticamente. Chiama `queue_redraw()` quando i dati cambiano.

3. **Tween su `create_tween()`**: Crea sempre tween con `create_tween()` (legati al nodo). NON usare `get_tree().create_tween()` a meno che non vuoi un tween globale.

4. **Kill tween prima di crearne uno nuovo**: Se un pannello sta gia' facendo fade-in e l'utente lo chiude, killa il tween vecchio prima di creare quello di fade-out.

5. **`get_canvas_transform()` per coordinate schermo**: Quando devi posizionare UI nel mondo (come i popup delle decorazioni), usa questa matrice per convertire posizioni mondo → schermo.

6. **Parallasse con fattori normalizzati**: Layer piu' lontani = fattore piu' basso = meno movimento. Normalizza i fattori tra 0.0 e 1.0 per facile controllo.

7. **ColorRect per overlay**: Per cambiare il colore/atmosfera di una zona, un ColorRect semi-trasparente e' piu' efficiente di ri-renderizzare le texture.

---

## 5. Riferimenti

- [Custom Drawing in 2D — Godot 4.6 Docs](https://docs.godotengine.org/en/4.6/tutorials/2d/custom_drawing_in_2d.html)
- [CanvasItem Class](https://docs.godotengine.org/en/4.6/classes/class_canvasitem.html)
- [Tween Class](https://docs.godotengine.org/en/4.6/classes/class_tween.html)
- [CanvasLayer](https://docs.godotengine.org/en/4.6/classes/class_canvaslayer.html)
- [Camera2D](https://docs.godotengine.org/en/4.6/classes/class_camera2d.html)
- [Theme System](https://docs.godotengine.org/en/4.6/tutorials/ui/gui_using_theme_editor.html)
- [Viewports](https://docs.godotengine.org/en/4.6/tutorials/rendering/viewports.html)
- [Multiple Resolutions](https://docs.godotengine.org/en/4.6/tutorials/rendering/multiple_resolutions.html)

---

## Esercizi

1. **Lab — y-sort isometric.** Crea scena isometrica con N character; verifica y-sort ordini correttamente per overlapping.
2. **Lab — tween chain.** Tween che fade-in + move + scale in sequence; usa `parallel()` e `chain()`.
3. **Stretch — custom `_draw` healthbar.** Disegna healthbar via `_draw()` con gradient + animation.

## Auto-valutazione

1. y-sort vs z-index: quando uno o l'altro?
2. `_draw()`: quando viene chiamato? Come forzare redraw?
3. Tween cleanup: chi lo gestisce?
4. CanvasLayer: a cosa serve?

## Collegamenti incrociati

- Modulo 03 — `SPRITES_AND_TEXTURES.md`.
- Modulo 07 — `ISOMETRIC_GAMES.md`.
- Modulo 12 — `SHADERS_GDSHADER.md` (NEW).

## Glossario locale

| Termine | Definizione |
|---|---|
| **z-index** | Ordering manuale verticale rendering. |
| **y-sort** | Ordering automatico per posizione Y. |
| **`_draw()`** | Callback per disegno custom. |
| **`queue_redraw()`** | Forza nuova chiamata `_draw()`. |
| **Tween** | Interpolation property over time. |
| **CanvasLayer** | Layer che si compone su top del viewport. |
| **ParallaxBackground** | Background che scrolla a velocita differenti. |
| **`modulate`** | Tint color applicabile a Sprite2D/Control. |
| **Theme** | Resource per coerenza UI Control nodes. |
