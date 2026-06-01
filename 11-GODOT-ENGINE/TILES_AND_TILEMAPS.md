# TileMap, TileSet e Terreni — Godot 4.6

> **Modulo del corso:** Godot 4 in Production
> **Posizione:** Fase 2 — Visual systems · Modulo 05
> **Prerequisiti:** Modulo 03 (sprites/textures); concetti grid-based.
> **Obiettivi:** TileMapLayer (4.4+ replacement di TileMap), TileSet, atlas sources, terrains/autotiling, isometric tiles, collisioni.
> **Tempo:** lettura 45 min · lab 180 min
> **Livello:** competent
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni:** Godot 4.4+ usa `TileMapLayer` (TileMap deprecato).

## Idee guida

1. **TileMapLayer (4.4+) > TileMap.** Multi-layer nativo, performance migliore, API piu pulita.
2. **TileSet riusabile fra layer.** Stesso TileSet -> stessa palette -> coerenza.
3. **Terrains automatizzano autotiling.** Definisci terrain (es. "grass"), tool genera tile transitions.
4. **Isometric tiles richiedono y-sort.** Non confondere con orthogonal.
5. **Collisione su tile: `physics_layer` in TileSet.** Una volta configurato, ogni tile e collidable per default.

> Documento di studio per il team Relax Room.
> Il nostro progetto attualmente NON usa TileMap, ma questa conoscenza
> e' fondamentale per capire come funzionano i giochi 2D in Godot
> e per eventuali sviluppi futuri (stanze modulari, editor livelli).

---

## 1. Concetti Chiave

### 1.1 Cos'e' un TileMap?

Un **TileMap** e' un sistema per costruire livelli 2D usando piccole immagini ripetute (tile). Invece di creare un'unica immagine grande per ogni stanza, si disegna una griglia di tessere riusabili.

**Vantaggi rispetto a una singola immagine:**
- Memoria: 1 tile da 16x16 riutilizzato 1000 volte occupa molto meno di un'immagine 1280x720
- Modularita': puoi modificare singole parti del livello senza ridisegnare tutto
- Collisioni: ogni tile puo' avere la propria shape di collisione
- Varianti: facile creare temi diversi cambiando il TileSet
- Editor visuale: Godot ha un potente editor tile integrato

**Quando NON serve un TileMap:**
- Sfondi fissi che non cambiano (come il nostro `room.png`)
- Sprite uniche non ripetibili (personaggi, UI)
- Quando la stanza e' un singolo artwork artistico

### 1.2 TileSet — La Collezione di Tessere

Un `TileSet` e' la risorsa che definisce quali tile sono disponibili. Si crea da un'immagine atlas (spritesheet) suddivisa in una griglia regolare.

**Creazione di un TileSet:**
1. Crea una risorsa `TileSet` (.tres)
2. Imposta la dimensione delle tile: es. `tile_size = Vector2i(16, 16)` o `(32, 32)`
3. Aggiungi una **Atlas Source**: un'immagine contenente tutte le tile in griglia
4. Godot suddivide automaticamente l'immagine in tile individuali

**Esempio di atlas:**
```
┌────┬────┬────┬────┐
│ 0,0│ 1,0│ 2,0│ 3,0│  ← Riga 0: pavimenti (legno, pietra, erba, sabbia)
├────┼────┼────┼────┤
│ 0,1│ 1,1│ 2,1│ 3,1│  ← Riga 1: muri (mattoni, pietra, legno, metallo)
├────┼────┼────┼────┤
│ 0,2│ 1,2│ 2,2│ 3,2│  ← Riga 2: decorazioni (finestra, porta, quadro, pianta)
└────┴────┴────┴────┘
Ogni cella e' una tile (es. 16x16 pixel)
```

### 1.3 TileMapLayer — Il Nodo per Disegnare

In Godot 4.x, ogni **layer** di tile e' un nodo separato: `TileMapLayer`.

```
Stanza (Node2D)
├── PavimentoLayer (TileMapLayer)   → Layer 0: pavimento
├── MuriLayer (TileMapLayer)        → Layer 1: muri e ostacoli
├── DecorazioniLayer (TileMapLayer) → Layer 2: decorazioni sopra
└── Character (CharacterBody2D)
```

**Proprieta' principali:**
```gdscript
var layer := TileMapLayer.new()
layer.tile_set = preload("res://data/tileset.tres")  # Il TileSet da usare
layer.z_index = 0              # Ordine di disegno
layer.visible = true           # Visibilita'
layer.collision_visibility_mode = 1  # 0=nascondi, 1=mostra in editor
```

**Piazzare tile da codice:**
```gdscript
# set_cell(coordinate_griglia, source_id, coordinate_atlas, tile_alternativo)
layer.set_cell(Vector2i(5, 3), 0, Vector2i(0, 0))  # Piazza tile (0,0) alla cella (5,3)
layer.set_cell(Vector2i(6, 3), 0, Vector2i(1, 0))  # Piazza tile (1,0) alla cella (6,3)

# Rimuovere una tile
layer.set_cell(Vector2i(5, 3), -1)  # source_id = -1 cancella

# Ottenere info su una tile
var data := layer.get_cell_tile_data(Vector2i(5, 3))
if data != null:
    print("Tile trovata!")

# Ottenere tutte le celle occupate
var used := layer.get_used_cells()  # Array[Vector2i]
print("Celle occupate: ", used.size())
```

### 1.4 Forme di Tile

Godot supporta diverse forme di tile:

| Forma | tile_shape | Uso |
|-------|-----------|-----|
| **Quadrata** | TILE_SHAPE_SQUARE | Top-down classico, platformer |
| **Isometrica** | TILE_SHAPE_ISOMETRIC | Vista isometrica (il nostro stile!) |
| **Mezza offset** | TILE_SHAPE_HALF_OFFSET_SQUARE | Griglie esagonali simulate |

**Configurazione isometrica:**
```gdscript
# Nel TileSet
tile_set.tile_shape = TileSet.TILE_SHAPE_ISOMETRIC
tile_set.tile_size = Vector2i(64, 32)  # Larghezza x Altezza del diamante
```

L'isometrica trasforma la griglia rettangolare in una griglia a diamante:
```
      ╱╲
    ╱    ╲
  ╱   0,0  ╲
  ╲        ╱╲
    ╲    ╱    ╲
      ╲╱  1,0  ╲
      ╱╲        ╱
    ╱    ╲    ╱
  ╱  0,1  ╲╱
  ╲        ╱
    ╲    ╱
      ╲╱
```

### 1.5 Terreni — Autotiling

I **terreni** sono il sistema di Godot per collegare automaticamente le tile tra loro. Quando piazzi una tile "erba" accanto a una tile "pietra", il sistema sceglie automaticamente la tile di bordo corretta.

**Tipi di connessione:**

| Tipo | Come funziona | Tile necessarie |
|------|--------------|-----------------|
| **Match Corners + Sides** | Controlla angoli E lati | 47 tile (piena copertura) |
| **Match Corners** | Solo angoli | 16 tile |
| **Match Sides** | Solo lati | 16 tile |

**Setup:**
1. Nel TileSet, crea un **Terrain Set** (es. "Pavimento")
2. Aggiungi **Terreni** al set (es. "Legno", "Pietra", "Erba")
3. Per ogni tile, marca quali lati/angoli appartengono a quale terreno
4. Nell'editor, usa lo strumento "Paint Terrain" per disegnare (Godot sceglie le tile automaticamente)

```gdscript
# Da codice: piazzare con terrain
layer.set_cells_terrain_connect(
    [Vector2i(0, 0), Vector2i(1, 0), Vector2i(2, 0)],  # Celle da riempire
    0,    # Terrain set index
    0     # Terrain index (es. 0 = "Legno")
)
```

### 1.6 Collisioni sulle Tile

Ogni tile puo' avere la propria forma di collisione:

**Setup nell'editor:**
1. Nel TileSet, vai al tab "Physics Layers"
2. Aggiungi un Physics Layer
3. Seleziona una tile e disegna il poligono di collisione
4. Le tile di muro avranno collisione piena, le tile di pavimento nessuna

**Da codice, controllare la collisione di una tile:**
```gdscript
var tile_data := layer.get_cell_tile_data(Vector2i(5, 3))
if tile_data != null:
    # Controlla se ha un body di collisione
    var polygon_count := tile_data.get_collision_polygons_count(0)  # Layer 0
    if polygon_count > 0:
        print("Questa tile ha collisione!")
```

### 1.7 Navigazione e Occlusione

Oltre alle collisioni, le tile supportano:

- **Navigation Layers**: Definiscono dove gli NPC possono camminare (per pathfinding A*)
- **Occlusion Layers**: Definiscono zone che bloccano la luce (per LightOccluder2D)

Questi sono utili per giochi piu' avanzati con pathfinding o illuminazione 2D.

---

## 2. Confronto con il Nostro Approccio Attuale

### 2.1 Come Funziona Ora (Senza TileMap)

Il nostro gioco usa un approccio **basato su sprite singole**:

```
RoomBackground (Sprite2D)    → room.png (180x155, scalato a ~720x620)
├── WallRect (ColorRect)     → Overlay colore muro (hex da rooms.json)
├── FloorRect (ColorRect)    → Overlay colore pavimento
└── Decorations (Node2D)     → Sprite2D individuali create runtime
    ├── bed_black_1 (Sprite2D) → sprite_bed_black1.png, scale 3.0
    ├── plant_5 (Sprite2D)     → sc_indoor_plants_w_pot_4.png, scale 6.0
    └── ... (altre decorazioni)
```

**I temi** sono overlay ColorRect semi-trasparenti (`alpha = 0.6`) sopra l'immagine base della stanza, con colori definiti in `rooms.json`:
```json
"themes": [
    { "id": "modern",  "wall_color": "2a2535", "floor_color": "3d3347" },
    { "id": "natural", "wall_color": "2d3025", "floor_color": "3a4230" },
    { "id": "pink",    "wall_color": "352530", "floor_color": "453540" }
]
```

### 2.2 Come Sarebbe con TileMap

Con un approccio TileMap, la stanza potrebbe essere costruita cosi':

```
Room (Node2D)
├── FloorLayer (TileMapLayer)      → Tile pavimento 32x32 con texture legno
├── WallLayer (TileMapLayer)       → Tile muro con collisione
├── FurnitureLayer (TileMapLayer)  → Mobili piazzati come tile
└── Character (CharacterBody2D)
```

**Vantaggi per il nostro progetto:**
- Stanze con layout diversi (non solo una stanza rettangolare)
- Collisioni automatiche per muro (ogni tile muro ha CollisionPolygon)
- Piu' facile aggiungere nuove stanze con layout diversi

**Svantaggi per il nostro progetto:**
- La stanza attuale e' un singolo artwork artistico → un TileMap lo renderebbe "a blocchi"
- Il sistema di decorazioni drag-and-drop funziona gia' bene con sprite libere
- Richiederebbe creare un tileset di muri/pavimenti coerente

### 2.3 Riferimento Esistente — Virtual Joystick Example

Il plugin virtual_joystick nel nostro progetto include un esempio che USA TileMapLayer:

```
addons/virtual_joystick/example/main_game/main_game.tscn
├── Parallax2D
│   └── Tiles (Node2D)
│       ├── Floor (TileMapLayer)        → Pavimento con terreni
│       └── Decorations (TileMapLayer)  → Decorazioni tilemap
└── Player (CharacterBody2D)
```

Questo e' un buon riferimento pratico da studiare dentro il nostro stesso repo.

---

## 3. Esercizi Pratici (Opzionali)

### Esercizio 1: TileSet Base
1. Crea una nuova scena `test_tilemap.tscn`
2. Aggiungi un nodo `TileMapLayer`
3. Crea un TileSet con `tile_size = Vector2i(32, 32)`
4. Usa una delle nostre immagini pavimento (`floor_mess*.png`) come atlas source
5. Piazza qualche tile nell'editor

### Esercizio 2: Collisioni
1. Aggiungi un Physics Layer al TileSet
2. Disegna collisione piena sulle tile di muro
3. Aggiungi un CharacterBody2D e verifica che non possa attraversare i muri

### Esercizio 3: Terrain Autotiling
1. Crea un terrain set con 2 terreni (pavimento, muro)
2. Marca le tile con i bordi corretti
3. Usa lo strumento Paint Terrain per disegnare — osserva come le tile di bordo vengono scelte automaticamente

---

## 4. Riferimenti

- [Using TileSets — Godot 4.6 Docs](https://docs.godotengine.org/en/4.6/tutorials/2d/using_tilesets.html)
- [Using TileMaps](https://docs.godotengine.org/en/4.6/tutorials/2d/using_tilemaps.html)
- [TileMapLayer Class](https://docs.godotengine.org/en/4.6/classes/class_tilemaplayer.html)
- [TileSet Class](https://docs.godotengine.org/en/4.6/classes/class_tileset.html)
- [Isometric TileMap Tutorial](https://docs.godotengine.org/en/4.6/tutorials/2d/using_tilemaps.html#isometric-tilemaps)
- [TileMap Navigation](https://docs.godotengine.org/en/4.6/tutorials/navigation/navigation_using_tilemaps.html)

---

## Esercizi

1. **Lab — TileMapLayer isometric.** Crea TileMapLayer 32x16 isometric con TileSet di base; verifica y-sort.
2. **Lab — terrains autotiling.** Definisci 2 terrains (grass, dirt); usa terrain brush per disegnare; observe automatic transition.
3. **Stretch — pathfinding su TileMapLayer.** Setup navigation TileSet, character che pathfinds su tile.

## Auto-valutazione

1. TileMapLayer vs TileMap (4.3 vs 4.4+).
2. Terrain: a cosa serve?
3. Isometric tile: dimensione tipica?
4. Physics layer in TileSet: come configurare?

## Collegamenti incrociati

- Modulo 04 — `RENDERING_AND_VISUAL_LOGIC.md`: y-sort.
- Modulo 07 — `ISOMETRIC_GAMES.md`.

## Glossario locale

| Termine | Definizione |
|---|---|
| **TileMap** | Nodo deprecato (4.3-); replaced da TileMapLayer. |
| **TileMapLayer** | Nodo Godot 4.4+ per griglia tile. |
| **TileSet** | Resource con palette di tile. |
| **Atlas source** | Source di tile da spritesheet. |
| **Terrain** | Insieme di tile con auto-transition. |
| **Autotiling** | Tool che genera transitions auto. |
| **Physics layer** | Layer collision per tile. |
| **Isometric** | Proiezione 2.5D con angle 30 gradi. |
