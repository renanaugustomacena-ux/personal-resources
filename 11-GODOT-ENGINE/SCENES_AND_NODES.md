# Scene, Nodi e Composizione — Godot 4.6

> **Modulo del corso:** Godot 4 in Production
> **Posizione:** Fase 1 — Foundations · Modulo 02 (vedi `00-SYLLABUS.md` §4)
> **Prerequisiti:** Modulo 01 (Godot Engine Study).
> **Obiettivi:** scene tree, ciclo di vita nodi (`_ready` vs `_enter_tree` vs `_init`), PackedScene, instancing, deferred-signal patterns, `queue_free` vs `free`.
> **Tempo:** lettura 60-90 min · lab 180 min
> **Livello:** novice → competent
> **Ultimo aggiornamento:** 2026-04-27

## Idee guida

1. **`_init` → `_enter_tree` → `_ready` ordine fisso.** `_ready` quando l'intero subtree e nel scene tree; usalo per signal connect.
2. **`queue_free()` defer-deletes; `free()` immediato.** Usa quasi sempre `queue_free` per evitare race con segnali in-flight.
3. **Instancing PackedScene: `instantiate()` crea copia, `add_child` la attacca.** Ricorda `owner = ` per persistenza scene.
4. **Group ≠ array: scopri nodi per ruolo, non per riferimento.** `get_tree().get_nodes_in_group("enemies")`.

> Documento di studio per il team Relax Room.
> Copre la struttura delle scene, il ciclo di vita dei nodi, instancing e
> i pattern usati nel nostro progetto.

---

## 1. Concetti Chiave

### 1.1 Scene Tree — L'Albero dei Nodi

In Godot, tutto e' un **nodo**. I nodi formano un albero gerarchico dove ogni nodo ha un solo padre e zero o piu' figli. La radice dell'albero e' lo **SceneTree**.

```
SceneTree (root: Window)
  └── Main (Node2D)            ← la nostra scena principale
      ├── RoomBackground (Sprite2D)
      ├── Room (Node2D)
      │   ├── Decorations (Node2D)
      │   └── Character (CharacterBody2D)
      └── UILayer (CanvasLayer)
          └── HUD (HBoxContainer)
```

**Regole fondamentali:**
- Ogni nodo puo' avere UN SOLO padre
- I figli ereditano la trasformazione del padre (posizione, rotazione, scala)
- I figli ereditano `modulate` (colore/trasparenza) dal padre
- Rimuovere un padre rimuove tutti i figli (ricorsivamente)

### 1.2 Ciclo di Vita dei Nodi

Ogni nodo attraversa queste fasi, nell'ordine:

```
_init()          → Costruttore. Chiamato quando il nodo viene creato (new() o instantiate())
    ↓
_enter_tree()    → Il nodo e' stato aggiunto all'albero (add_child). Puo' accedere a get_tree()
    ↓
_ready()         → Tutti i figli sono pronti. Accesso sicuro a @onready var, $NomeNodo
    ↓
_process(delta)      → Chiamato ogni frame (60fps). Per logica di gioco, UI
_physics_process(delta) → Chiamato a rate fisso (default 60Hz). Per movimento, collisioni
    ↓
_exit_tree()     → Il nodo sta per uscire dall'albero. Pulizia: disconnetti segnali
    ↓
queue_free()     → Segna il nodo per la distruzione (a fine frame). Tutti i figli vengono distrutti.
```

**Errore comune:** Accedere a `$NomeNodo` in `_init()` fallisce perche' il nodo non e' ancora nell'albero. Usa `_ready()` o `@onready var`.

**`@onready`** — variabile inizializzata quando `_ready()` viene chiamato:
```gdscript
# CORRETTO — il nodo esiste quando _ready() e' chiamato
@onready var _anim: AnimatedSprite2D = $AnimatedSprite2D

# SBAGLIATO — $AnimatedSprite2D non esiste ancora in fase di dichiarazione
var _anim: AnimatedSprite2D = $AnimatedSprite2D  # ERRORE!
```

### 1.3 PackedScene e Instancing

Una **PackedScene** e' una scena salvata su disco (file `.tscn` o `.scn`). Puo' essere caricata e istanziata multiple volte.

```gdscript
# Caricare una scena da disco
var scene := load("res://scenes/male-old-character.tscn") as PackedScene

# Creare un'istanza (copia) della scena
var character := scene.instantiate()

# Aggiungere all'albero
add_child(character)

# Per operazioni sicure durante il frame corrente
call_deferred("add_child", character)
```

**`instantiate()` vs `new()`:**
- `scene.instantiate()` — Crea un nodo completo con tutta la gerarchia della scena
- `Sprite2D.new()` — Crea un singolo nodo vuoto

**`call_deferred("add_child", node)`** — Aggiunge il nodo alla fine del frame corrente. Necessario quando si fa add_child durante una callback che sta iterando sull'albero (es. dentro `_process` o una callback di segnale).

### 1.4 Tipi di Nodo per Giochi 2D

| Nodo | Uso | Note |
|------|-----|------|
| **Node2D** | Contenitore generico 2D | Ha position, rotation, scale. Nessun rendering. |
| **Sprite2D** | Mostra un'immagine | Vedi SPRITES_AND_TEXTURES.md |
| **AnimatedSprite2D** | Sprite con animazioni | SpriteFrames, play(), stop() |
| **CharacterBody2D** | Personaggi che si muovono | move_and_slide(), collision |
| **StaticBody2D** | Oggetti solidi immobili | Muri, mobili, ostacoli |
| **Area2D** | Rilevamento zone | Trigger, aree danno, pickup |
| **CollisionShape2D** | Forma di collisione | Figlia di Body2D/Area2D |
| **CollisionPolygon2D** | Collisione poligonale | Per forme irregolari |
| **Camera2D** | Telecamera 2D | Zoom, limiti, smoothing |
| **CanvasLayer** | Layer di rendering separato | Per UI sopra il gioco |
| **Control** | Base per UI | Ancoraggi, margini, temi |
| **ColorRect** | Rettangolo colorato | Overlay, sfondi, separatori |
| **Timer** | Timer a singolo colpo o ripetuto | timeout signal |

### 1.5 CanvasLayer — Separare UI dal Gioco

Un `CanvasLayer` crea un layer di rendering separato. I suoi figli NON sono influenzati dalla camera o dalla trasformazione del gioco.

```gdscript
# I figli del CanvasLayer appaiono sempre alla stessa posizione sullo schermo,
# indipendentemente dallo zoom della camera o dalla posizione del mondo.

# Esempio: layer 10 per UI, layer 100 per popup
var ui_layer := CanvasLayer.new()
ui_layer.layer = 10        # Sopra il gioco (default = 0)
add_child(ui_layer)

# I layer piu' alti vengono renderizzati sopra
# layer 0 = mondo di gioco
# layer 10 = HUD, bottoni
# layer 100 = popup, modale
```

**Regola pratica:** Layer < 0 = dietro al gioco, Layer 0 = gioco, Layer > 0 = sopra il gioco.

### 1.6 Control Nodes — UI

I nodi `Control` sono la base del sistema UI di Godot. Funzionano con **ancoraggi** e **margini**.

**Ancoraggi (anchors):** Definiscono dove il nodo si "aggancia" al padre.
```
anchors_preset = 15  →  FULL_RECT (riempi tutto il padre)
anchors_preset = 8   →  CENTER (centrato)
```

**mouse_filter:** Come il nodo gestisce gli eventi mouse:
```gdscript
MOUSE_FILTER_STOP = 0   # Intercetta e BLOCCA l'evento (non passa ai nodi sotto)
MOUSE_FILTER_PASS = 1   # Intercetta ma PASSA l'evento ai nodi sotto
MOUSE_FILTER_IGNORE = 2 # IGNORA completamente gli eventi mouse
```

### 1.7 Collision Layer e Mask

Il sistema di collisione usa **layer** (su quale livello SONO) e **mask** (con quali livelli INTERAGISCO):

```
Layer 1 = Muri della stanza (StaticBody2D del pavimento)
Layer 2 = Decorazioni (StaticBody2D delle decorazioni)

CharacterBody2D:
  collision_layer = 0  (il personaggio non e' un ostacolo per altri)
  collision_mask = 3   (collide con layer 1 E 2, cioe' muri + decorazioni)
  collision_mask = 1   (solo muri, in edit mode)
```

`collision_mask = 3` significa: layer 1 (bit 0) + layer 2 (bit 1) = 1 + 2 = 3 in binario (11).

---

## 2. Nel Nostro Progetto

### 2.1 main.tscn — La Scena Principale del Gioco

```
Main (Node2D) — scripts/main.gd
├── RoomBackground (Sprite2D)       → room.png, centrato a (640, 360)
├── WallRect (ColorRect)            → Overlay muro, 40% superiore, alpha 0.6
├── FloorRect (ColorRect)           → Overlay pavimento, 60% inferiore, alpha 0.6
├── Baseboard (ColorRect)           → Linea 1px di separazione muro/pavimento
├── Room (Node2D) — scripts/rooms/room_base.gd
│   ├── Decorations (Node2D)        → Container vuoto, le decorazioni vengono aggiunte runtime
│   ├── Character (CharacterBody2D) → Istanza di male-old-character.tscn
│   │   ├── CollisionShape2D        → CapsuleShape2D (raggio 16, altezza 56)
│   │   └── AnimatedSprite2D        → 13 animazioni, scale (3, 3)
│   └── RoomBounds (StaticBody2D)
│       └── FloorBounds (CollisionPolygon2D) → Area calpestabile
├── RoomGrid (Node2D) — scripts/rooms/room_grid.gd
│   └── (disegna griglia 64px via _draw(), visibile solo in edit mode)
└── UILayer (CanvasLayer, layer=10)
    ├── DropZone (Control) — scripts/ui/drop_zone.gd
    │   └── anchors_preset: FULL_RECT, mouse_filter: PASS
    └── HUD (HBoxContainer)
        ├── DecoButton (Button)
        ├── SettingsButton (Button)
        └── ProfileButton (Button)
```

**Flusso di rendering (dal basso verso l'alto):**
1. `RoomBackground` — L'immagine della stanza, scalata per riempire il viewport
2. `WallRect` + `FloorRect` — Overlay colorati semi-trasparenti per il tema
3. `Baseboard` — Linea decorativa alla giunzione muro/pavimento
4. `Room/Decorations` — Le sprite delle decorazioni
5. `Room/Character` — Il personaggio (sopra le decorazioni)
6. `RoomGrid` — Griglia visuale (solo in edit mode)
7. `UILayer` (CanvasLayer 10) — HUD e pannelli sopra tutto

### 2.2 main_menu.tscn — Il Menu Principale

```
MainMenu (Node2D) — scripts/menu/main_menu.gd
├── ForestBackground (Node2D) — scripts/rooms/window_background.gd
│   └── (8 sprite parallasse create runtime via _build_layers)
├── DimOverlay (ColorRect)    → Overlay scuro semi-trasparente
├── LoadingScreen (ColorRect) → z_index: 100, contiene SubViewportContainer
├── MenuCharacter (Node2D) — scripts/menu/menu_character.gd
│   └── (sprite + timer creati runtime via walk_in())
└── UILayer (CanvasLayer, layer=10)
    └── ButtonContainer (VBoxContainer)
        ├── TitleLabel — "Relax Room"
        ├── Spacer
        ├── NuovaPartitaBtn
        ├── CaricaPartitaBtn
        ├── OpzioniBtn
        ├── ProfiloBtn
        └── EsciBtn
```

**Sequenza di avvio:**
1. Loading screen visibile (alpha = 1.0)
2. Dopo 0.4s, fade out della loading screen (0.5s)
3. `MenuCharacter.walk_in()` — animazione camminata da (-100, 530) a (640, 530)
4. Fade in dei bottoni (0.3s)

### 2.3 Personaggi — Scene Istanziabili

Tutti i personaggi seguono la stessa struttura:

```
CharacterBody2D — scripts/rooms/character_controller.gd
├── CollisionShape2D
│   └── CapsuleShape2D (raggio: 16, altezza: 56)
└── AnimatedSprite2D
    ├── texture_filter: NEAREST
    ├── scale: (3, 3) o (4, 4)
    └── SpriteFrames (13+ animazioni)
```

**Scambio personaggio runtime** (`room_base.gd` linee 25-42):
```gdscript
func _on_character_changed(character_id: String) -> void:
    var scene := load(scene_path) as PackedScene
    var old_pos := character_node.position       # Salva posizione
    var old_scale := character_node.scale         # Salva scala
    character_node.queue_free()                   # Rimuovi vecchio
    var new_char := scene.instantiate()           # Crea nuovo
    new_char.position = old_pos                   # Ripristina posizione
    new_char.scale = old_scale                    # Ripristina scala
    call_deferred("add_child", new_char)          # Aggiungi sicuro
```

### 2.4 Mobili — Scene Senza Script

Letti, finestre e porte sono scene semplici senza logica:

```
bed_black_1 (StaticBody2D)
├── CollisionPolygon2D    → Poligono a 8 punti per collisione
└── Sprite2D              → sprite_bed_black1.png
```

Queste scene esistono nella cartella `scenes/room/` ma nel gioco le decorazioni vengono create runtime via `room_base.gd` caricando direttamente le texture da `decorations.json`. Le scene `.tscn` dei mobili servono come riferimento/prototipo.

### 2.5 Pannelli UI — Creati Programmaticamente

I pannelli (settings, profile, deco) NON hanno layout .tscn complessi. Sono `PanelContainer` costruiti interamente via GDScript:

```gdscript
# Esempio semplificato dal pattern dei nostri pannelli
var panel := PanelContainer.new()
var margin := MarginContainer.new()
margin.add_theme_constant_override("margin_left", 12)
margin.add_theme_constant_override("margin_top", 8)
panel.add_child(margin)

var vbox := VBoxContainer.new()
vbox.add_theme_constant_override("separation", 8)
margin.add_child(vbox)

var label := Label.new()
label.text = "Impostazioni"
label.add_theme_font_size_override("font_size", 13)
vbox.add_child(label)
```

**Perche' costruire UI via codice?** Per pannelli semplici con pochi controlli, e' piu' veloce e piu' facile da mantenere rispetto a un file .tscn dedicato. Per UI complesse (molti bottoni, layout nested), un .tscn sarebbe piu' appropriato.

### 2.6 auth_screen.tscn — Layout Minimo

La schermata di autenticazione ha un `.tscn` quasi vuoto (solo un `Control` root) e costruisce TUTTA la UI via codice in `auth_screen.gd`:

```
AuthScreen (Control) → z_index: 100, fullscreen
  └── (tutto il contenuto — form login, registrazione, guest — creato in _ready())
```

**z_index: 100** assicura che l'auth screen appaia sopra tutto il gioco.

---

## 3. Best Practice

1. **Una scena, una responsabilita'**: Ogni scena `.tscn` dovrebbe rappresentare un concetto (un personaggio, un mobile, un pannello UI). Non mettere tutto in una sola scena.

2. **`call_deferred` per add/remove durante callback**: Se stai aggiungendo/rimuovendo nodi durante `_process`, `_physics_process`, o una callback di segnale, usa `call_deferred("add_child", node)` per evitare crash.

3. **`queue_free()` non `free()`**: Usa sempre `queue_free()` che aspetta la fine del frame. `free()` rimuove immediatamente e puo' causare crash se altri nodi hanno riferimenti.

4. **`@onready` per riferimenti a figli**: Non accedere mai a `$NomeNodo` fuori da `_ready()` o da funzioni chiamate dopo `_ready()`.

5. **Disconnetti i segnali in `_exit_tree()`**: Per segnali globali (SignalBus), disconnetti esplicitamente. Per segnali padre-figlio, Godot li pulisce automaticamente.

   **Esempio reale dal nostro codice** (pattern usato in tutti gli autoload e script con segnali globali):
   ```gdscript
   # Da room_base.gd — pulizia segnali SignalBus
   func _exit_tree() -> void:
       if SignalBus.character_changed.is_connected(_on_character_changed):
           SignalBus.character_changed.disconnect(_on_character_changed)
       if SignalBus.decoration_placed.is_connected(_on_decoration_placed):
           SignalBus.decoration_placed.disconnect(_on_decoration_placed)
   ```

   **Perche'?** Se il nodo viene distrutto ma SignalBus (un autoload) sopravvive, il segnale punta a un oggetto morto → crash. L'audit ha trovato e risolto 3 casi simili (N-Q3, N-Q5, N-AR7).

   **Quando NON serve:** Connessioni padre→figlio (es. `$Timer.timeout.connect(...)`) vengono pulite automaticamente da Godot quando il padre viene distrutto.

6. **CanvasLayer per UI**: Metti TUTTA la UI in un CanvasLayer cosi' non e' influenzata dalla camera o dalla posizione del mondo.

7. **Collision layer logici**: Definisci layer chiari (1=muri, 2=decorazioni, 4=trigger, ecc.) e documentali. Evita di usare `collision_mask = -1` (collide con tutto).

---

## 4. Riferimenti

- [Scene Tree — Godot 4.6 Docs](https://docs.godotengine.org/en/4.6/getting_started/step_by_step/scene_tree.html)
- [Nodes and Scenes](https://docs.godotengine.org/en/4.6/getting_started/step_by_step/nodes_and_scenes.html)
- [Node Lifecycle](https://docs.godotengine.org/en/4.6/tutorials/scripting/node_notification.html)
- [CanvasLayer](https://docs.godotengine.org/en/4.6/classes/class_canvaslayer.html)
- [CharacterBody2D](https://docs.godotengine.org/en/4.6/classes/class_characterbody2d.html)
- [Control Nodes](https://docs.godotengine.org/en/4.6/tutorials/ui/index.html)
- [Physics Layers](https://docs.godotengine.org/en/4.6/tutorials/physics/physics_introduction.html)

---

## Esercizi

1. **Lab — ciclo di vita.** Crea scena con 5 nodi annidati; print `_init`/`_enter_tree`/`_ready` di ognuno; verifica ordine.
2. **Lab — `queue_free` vs `free` race.** Scena con timer + signal connect a node; `free()` durante emit; osserva crash. Replica con `queue_free` no crash.
3. **Stretch — runtime scene composition.** Carica 3 PackedScene, istanzia in pattern (grid 3x3), attacca signal a callback comune.

## Auto-valutazione

1. Ordine `_init`, `_enter_tree`, `_ready`?
2. `queue_free` vs `free`: quando crash con `free`?
3. PackedScene `instantiate`: cosa restituisce?
4. Group: quando usarli vs riferimento diretto?

## Collegamenti incrociati

- Modulo 01 — `GODOT_ENGINE_STUDY.md`.
- Modulo 13 — `AUTOLOAD_SAFETY.md` (NEW).

## Glossario locale

| Termine | Definizione |
|---|---|
| **Scene tree** | Albero gerarchico di nodi runtime. |
| **PackedScene** | Scene serializzata, base per instancing. |
| **`instantiate()`** | Crea istanza PackedScene. |
| **`_init`/`_enter_tree`/`_ready`** | Callback ordine ciclo vita. |
| **`queue_free()`** | Marca nodo per deletion deferred. |
| **`free()`** | Deletion immediata; rischiosa con signal in-flight. |
| **Group** | Tag per nodi; query via `get_nodes_in_group`. |
| **`owner`** | Property per scene serialization. |
