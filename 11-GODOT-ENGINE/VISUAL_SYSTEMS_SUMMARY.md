# Come Funziona la Grafica di Relax Room

> **Modulo del corso:** Godot 4 in Production
> **Posizione:** Fase 2 — Visual systems · Modulo 06 (sintesi)
> **Prerequisiti:** Moduli 02, 03, 04, 05.
> **Obiettivi:** sintesi del visual stack del progetto Relax Room come case-study; come pezzi si combinano end-to-end.
> **Tempo:** lettura 30 min
> **Livello:** competent
> **Ultimo aggiornamento:** 2026-04-27

## Idee guida

1. **Sintesi e dove vedi il sistema, non i pezzi.** I moduli precedenti spiegano un componente; questo mostra come si combinano.
2. **Relax Room sceglie semplicita.** No TileMap, sprites individuali, manual y-sort: trade-off cosciente.

> Riassunto applicato al progetto dei 4 documenti visuali:
> SPRITES_AND_TEXTURES, SCENES_AND_NODES, TILES_AND_TILEMAPS, RENDERING_AND_VISUAL_LOGIC.
>
> Scritto per essere comprensibile anche senza esperienza con Godot.
> Ogni concetto e' spiegato con analogie e collegato al nostro codice reale.

---

## Indice

1. [Il Grande Quadro — Come il gioco mostra le cose sullo schermo](#1-il-grande-quadro)
2. [Sprite — Le immagini del gioco](#2-sprite--le-immagini-del-gioco)
3. [Animazioni — Come le immagini prendono vita](#3-animazioni--come-le-immagini-prendono-vita)
4. [Scene e Nodi — L'albero genealogico del gioco](#4-scene-e-nodi--lalbero-genealogico-del-gioco)
5. [La Stanza — Come costruiamo il mondo](#5-la-stanza--come-costruiamo-il-mondo)
6. [Rendering — L'ordine in cui le cose vengono dipinte](#6-rendering--lordine-in-cui-le-cose-vengono-dipinte)
7. [Tween — Le animazioni fluide](#7-tween--le-animazioni-fluide)
8. [Temi e Stile — L'aspetto dei bottoni e pannelli](#8-temi-e-stile--laspetto-dei-bottoni-e-pannelli)
9. [TileMap — Un sistema che non usiamo (ancora)](#9-tilemap--un-sistema-che-non-usiamo-ancora)
10. [Mappa Completa — Dove vive ogni concetto nel codice](#10-mappa-completa)

---

## 1. Il Grande Quadro

### L'analogia del teatro

Immagina il nostro gioco come un **teatro**:

```
PALCOSCENICO (Viewport 1280x720)
┌─────────────────────────────────────────────┐
│                                             │
│   FONDALE (room.png)                        │  ← Lo sfondo dipinto
│   ┌─────────────────────────────────────┐   │
│   │  GELATINE COLORATE (ColorRect)      │   │  ← Filtri di colore sopra
│   │  ┌─────────────────────────────┐    │   │
│   │  │  OGGETTI DI SCENA           │    │   │  ← Mobili, piante, gatto
│   │  │  (Sprite decorazioni)       │    │   │
│   │  │        🧑 ATTORE             │    │   │  ← Il personaggio
│   │  └─────────────────────────────┘    │   │
│   └─────────────────────────────────────┘   │
│                                             │
│   ┌─VETRO TRASPARENTE──────────────────┐    │  ← CanvasLayer (UI)
│   │  [Bottoni]  [HUD]  [Pannelli]      │    │     Sempre davanti
│   └────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

**In termini tecnici:**
- **Palcoscenico** = il Viewport (1280x720 pixel, definito in `project.godot`)
- **Fondale** = `RoomBackground` (Sprite2D con `room.png`)
- **Gelatine colorate** = `WallRect` e `FloorRect` (ColorRect semi-trasparenti)
- **Oggetti di scena** = decorazioni (Sprite2D create da `room_base.gd`)
- **Attore** = il personaggio (CharacterBody2D con AnimatedSprite2D)
- **Vetro trasparente** = `CanvasLayer` layer=10 (la UI sta qui, sempre visibile)

### Il flusso in una frase

Il gioco carica un'immagine di sfondo, ci mette dei filtri colorati sopra per il tema, piazza i mobili come adesivi, anima il personaggio come un flipbook, e mostra i bottoni su un vetro davanti a tutto.

---

## 2. Sprite — Le immagini del gioco

### Cos'e' una Sprite?

Una **Sprite** e' un'immagine mostrata sullo schermo. Pensala come un **adesivo** che puoi attaccare, spostare, ruotare e ingrandire.

In Godot, il nodo si chiama `Sprite2D`.

### Le sprite nel nostro progetto

Usiamo le sprite per **tre cose diverse**, ciascuna con un approccio diverso:

#### A) Lo sfondo della stanza — "Il poster sul muro"

```
room.png (180 x 155 pixel, piccolissima!)
    ↓ scalata 4x
Sullo schermo: ~720 x 620 pixel
```

E' come avere una foto piccola e ingrandirla. Per evitare che diventi sfocata, usiamo il filtro **NEAREST** (che mantiene i pixel netti invece di sfumarli). Questo e' il trucco fondamentale della **pixel art**: ingrandire senza sfumare.

**Analogia:** Immagina di fotocopiare un disegno al 400%. Con una fotocopiatrice normale, diventa sfocato (filtro LINEAR). Con la nostra fotocopiatrice magica (filtro NEAREST), ogni pixel rimane un quadratino perfetto.

**Dove nel codice:** `project.godot` imposta il filtro globale a NEAREST:
```
rendering/textures/canvas_textures/default_texture_filter = 0
```

#### B) Le decorazioni — "Gli adesivi sulla parete"

I mobili, le piante e gli animali vengono creati **a runtime** (cioe' mentre il gioco gira, non a mano nell'editor). Lo script `scripts/rooms/room_base.gd` legge il file `data/decorations.json` e per ogni decorazione:

1. Crea un adesivo (`Sprite2D.new()`)
2. Carica l'immagine dal percorso nel JSON (`load(sprite_path)`)
3. Lo ingrandisce (`scale = Vector2(3.0, 3.0)` per i mobili)
4. Lo posiziona sulla griglia (`position = pos`)
5. Lo attacca alla scena (`add_child(sprite)`)

**Dettaglio importante — l'origine dell'adesivo:**

Per default, Godot considera il "punto di aggancio" di una sprite al suo centro. Ma noi usiamo `centered = false` per le decorazioni, cosi' il punto di aggancio e' l'angolo in alto a sinistra.

**Perche'?** Perche' i mobili si piazzano su una **griglia di 64px**. Se il punto di aggancio fosse al centro, calcolare la posizione sulla griglia sarebbe un incubo matematico. Con l'angolo in alto a sinistra, e' semplicissimo: posizione = casella della griglia.

**Analogia:** Immagina di incollare adesivi su un quaderno a quadretti. E' molto piu' facile allinearli se li incolli partendo dall'angolo in alto a sinistra di una casella, piuttosto che cercando di centrare ogni adesivo su un incrocio.

**Scale per tipo** (da `decorations.json`):

| Tipo | item_scale | Esempio |
|------|-----------|---------|
| Mobili (letti, scrivanie, sedie, armadi) | 3.0 | Un pixel diventa 3x3 |
| Piante (con e senza vaso) | 6.0 | Un pixel diventa 6x6 |
| Animali (Void Cat) | 4.0 | Un pixel diventa 4x4 |

Le piante hanno scale doppia rispetto ai mobili perche' le immagini originali sono piu' piccole (dettaglio piu' fine).

#### C) Il personaggio — "L'attore animato"

Il personaggio non e' una semplice Sprite2D ma un `AnimatedSprite2D` (vedi sezione 3). E' l'unico elemento che si muove autonomamente nella stanza.

### AtlasTexture — Ritagliare un foglio di adesivi

Un `AtlasTexture` e' come avere un **foglio di adesivi** e ritagliarne uno specifico.

**Analogia:** Hai un foglio con 4 adesivi in fila. Invece di separare fisicamente i 4 adesivi, dici a Godot: "Prendi il foglio, e mostrami solo il rettangolo da pixel 0 a pixel 32" (primo adesivo), oppure "da pixel 32 a pixel 64" (secondo adesivo).

```
Foglio: male_idle_down.png (128 x 32 pixel)
┌────────┬────────┬────────┬────────┐
│ Frame 0│ Frame 1│ Frame 2│ Frame 3│
│ (0,0)  │(32,0)  │(64,0)  │(96,0)  │
│ 32x32  │ 32x32  │ 32x32  │ 32x32  │
└────────┴────────┴────────┴────────┘

AtlasTexture per Frame 0: region = Rect2(0, 0, 32, 32)
AtlasTexture per Frame 1: region = Rect2(32, 0, 32, 32)
AtlasTexture per Frame 2: region = Rect2(64, 0, 32, 32)
AtlasTexture per Frame 3: region = Rect2(96, 0, 32, 32)
```

Questo e' esattamente come sono definite le animazioni nel file `scenes/male-old-character.tscn`.

### Impostazioni di importazione — Perche' i PNG non vengono usati direttamente

Quando aggiungi un file `.png` al progetto, Godot lo **converte** in un formato interno. Le impostazioni di conversione sono nel file `.import` che appare accanto al PNG.

Per la pixel art, le nostre impostazioni sono:

| Impostazione | Valore | Perche' |
|-------------|--------|---------|
| compress/mode | 0 (nessuna) | La compressione cambierebbe i colori dei pixel |
| mipmaps/generate | false | I mipmap servono per 3D, non per pixel art 2D |
| fix_alpha_border | true | Evita righe scure sui bordi trasparenti |

**Analogia:** E' come salvare una foto. Se usi JPG (compresso), i colori cambiano leggermente — ok per foto, terribile per pixel art dove ogni pixel conta. Noi "salviamo in PNG" (nessuna compressione) per mantenere ogni pixel identico all'originale.

---

## 3. Animazioni — Come le immagini prendono vita

### Il principio del flipbook

Un'animazione non e' altro che **tante immagini mostrate velocemente una dopo l'altra**, come un flipbook (quei quadernetti dove disegni su ogni pagina e poi le sfogli velocemente per creare l'illusione del movimento).

Nel nostro gioco ci sono **due modi** per fare animazioni:

### Metodo 1: AnimatedSprite2D — "Il proiettore di diapositive automatico"

Usato per il **personaggio nella stanza** (16 animazioni diverse).

`AnimatedSprite2D` e' un nodo che contiene una risorsa `SpriteFrames`. Questa risorsa e' come un **album di diapositive organizzato per categorie**:

```
SpriteFrames (l'album):
├── "idle_down"        → 4 diapositive, proiettate a 5 fps
├── "idle_side"        → 4 diapositive, proiettate a 5 fps
├── "idle_up"          → 4 diapositive, proiettate a 5 fps
├── "idle_vertical_down" → 4 diapositive
├── "idle_vertical_up"   → 4 diapositive
├── "walk_down"        → 4 diapositive, proiettate a 5 fps
├── "walk_side"        → 4 diapositive
├── "walk_up"          → 4 diapositive
├── "walk_side_down"   → 4 diapositive
├── "walk_side_up"     → 4 diapositive
├── "interact_down"    → 4 diapositive
├── "interact_side"    → 4 diapositive
├── "interact_up"      → 4 diapositive
├── "interact_vertical_down" → 4 diapositive
├── "interact_vertical_up"   → 4 diapositive
└── "rotate"           → 8 diapositive, proiettate a 3 fps (piu' lenta)
```

**Come funziona nel codice** (`character_controller.gd`):

Il controller legge la direzione del joystick e dice al proiettore quale categoria mostrare:

```
Joystick punta a destra?     → anim.play("walk_side"), flip_h = false
Joystick punta a sinistra?   → anim.play("walk_side"), flip_h = true   ← SPECCHIATO!
Joystick punta in basso?     → anim.play("walk_down")
Joystick punta in alto?      → anim.play("walk_up")
Joystick in basso-destra?    → anim.play("walk_side_down"), flip_h = false
Joystick fermo?              → anim.play("idle_down")  (o l'ultima direzione)
```

**Il trucco del DIRECTION_THRESHOLD (1.2):**

Se il joystick punta a 5 gradi dalla linea verticale, non vuoi che il personaggio cammini in diagonale — vuoi che cammini dritto. Il DIRECTION_THRESHOLD crea una **zona di tolleranza**: se il movimento e' "quasi dritto", viene interpretato come dritto.

**Analogia:** E' come quando guidi una macchina. Se il volante e' leggermente storto, la macchina va comunque dritta grazie al "gioco" dello sterzo. Senza tolleranza, la macchina zigzagherebbe ad ogni micro-movimento.

**Il trucco del `flip_h`:**

Invece di avere sprite separate per "cammina a destra" e "cammina a sinistra", abbiamo solo "cammina di lato" e la specchiamo orizzontalmente per l'altra direzione. Questo dimezza il numero di sprite necessarie.

**Analogia:** E' come guardare qualcuno allo specchio — si muove identicamente ma nella direzione opposta.

### Metodo 2: Sprite2D + Timer — "Il flipbook manuale"

Usato per il **personaggio nel menu** (una sola animazione: camminata laterale).

Invece di usare il proiettore automatico (AnimatedSprite2D), qui sfogliamo le pagine a mano con un timer:

```
Timer scatta ogni 0.15 secondi
    ↓
frame = (frame + 1) % 4      ← Passa al frame successivo, torna a 0 dopo il 3
    ↓
La sprite mostra il frame corrente
    ↓
0 → 1 → 2 → 3 → 0 → 1 → 2 → 3 → ...  (ciclo infinito)
```

**Perche' non usare AnimatedSprite2D anche qui?** Perche' serve una sola animazione di 4 frame per pochi secondi. Creare un intero album di diapositive per 4 immagini sarebbe come comprare un proiettore per guardare 4 foto — meglio sfogliarle a mano.

**Dove nel codice:** `scripts/menu/menu_character.gd`

### Metodo a confronto

| | AnimatedSprite2D | Sprite2D + Timer |
|---|---|---|
| **Quando usare** | Molte animazioni diverse | Una sola animazione semplice |
| **Nel nostro progetto** | Personaggio nella stanza (16 anim.) | Personaggio nel menu (1 anim.) |
| **Controllo** | `play("nome_animazione")` | Cambio manuale di `frame` |
| **Velocita'** | Ogni animazione puo' avere fps diversi | Una sola velocita' per tutti i frame |

---

## 4. Scene e Nodi — L'albero genealogico del gioco

### L'analogia dell'albero genealogico

In Godot, tutto e' organizzato come un **albero genealogico**. Ogni elemento (nodo) ha un genitore e puo' avere dei figli. I figli ereditano le caratteristiche del genitore.

```
Nonno (posizione: 100, 100)
├── Padre (posizione: 50, 0)      ← posizione REALE: 150, 100
│   ├── Figlio A (posizione: 10, 0)  ← posizione REALE: 160, 100
│   └── Figlio B (posizione: 0, 20)  ← posizione REALE: 150, 120
└── Zio (posizione: -50, 0)       ← posizione REALE: 50, 100
```

**Cosa viene ereditato:**
- **Posizione**: la posizione del figlio e' relativa al padre. Se il padre si muove, i figli si muovono con lui.
- **Scala**: se il padre e' scalato 2x, anche i figli appaiono 2x.
- **Trasparenza** (`modulate`): se il padre e' semi-trasparente, i figli lo sono anche.
- **Visibilita'**: se il padre e' nascosto, i figli sono nascosti.
- **Distruzione**: se il padre viene distrutto, tutti i figli vengono distrutti.

**Analogia:** E' come una famiglia in un'auto. Se l'auto (padre) si muove, tutti i passeggeri (figli) si muovono. Se l'auto va in un tunnel buio (visibilita' = false), nessuno nell'auto e' visibile.

### Il ciclo di vita — La vita di un nodo dalla nascita alla morte

Ogni nodo attraversa queste fasi, sempre nello stesso ordine:

```
1. NASCITA      _init()         "Sono stato creato"
                                (come un neonato: esiste ma non e' ancora in casa)

2. ARRIVO       _enter_tree()   "Mi hanno messo nell'albero"
                                (come entrare in casa per la prima volta)

3. PRONTO       _ready()        "Tutti i miei figli sono pronti"
                                (la famiglia e' completa, posso iniziare a lavorare)

4. VITA         _process(delta)          "Mi aggiorno ogni frame" (~60 volte/secondo)
                _physics_process(delta)  "Mi aggiorno per la fisica" (rate fisso)

5. USCITA       _exit_tree()    "Sto per essere rimosso dall'albero"
                                (come il momento prima di uscire di casa — fai pulizia)

6. MORTE        queue_free()    "Distruggimi alla fine di questo frame"
```

**Regole importanti:**
- **Non accedere ai figli prima di `_ready()`!** Sarebbe come chiedere al figlio di fare qualcosa prima che sia nato.
- **Usa `@onready var`** per dichiarare riferimenti ai figli — Godot li risolve automaticamente quando `_ready()` viene chiamato.
- **Disconnetti i segnali globali in `_exit_tree()`!** Se il nodo muore ma SignalBus (che vive per sempre) ha ancora il suo numero di telefono, quando chiama trova un morto → crash.

**Esempio reale dal nostro codice:**
```gdscript
# room_base.gd — CORRETTO: pulizia segnali prima di morire
func _exit_tree() -> void:
    if SignalBus.character_changed.is_connected(_on_character_changed):
        SignalBus.character_changed.disconnect(_on_character_changed)
```

**Quando NON serve disconnettere:** Connessioni padre → figlio (tipo `$Timer.timeout.connect(...)`) vengono pulite automaticamente da Godot quando il padre muore. E' come un walkie-talkie che si spegne quando butti via la radio.

### PackedScene — Lo stampo per i biscotti

Una **PackedScene** (file `.tscn`) e' come uno **stampo per biscotti**. Lo crei una volta, e poi puoi sfornare quante copie vuoi.

```gdscript
# Carica lo stampo
var stampo := load("res://scenes/male-old-character.tscn") as PackedScene

# Sforna un biscotto (istanza)
var personaggio := stampo.instantiate()

# Mettilo nel piatto (aggiungilo alla scena)
add_child(personaggio)
```

**`call_deferred("add_child", nodo)`** — A volte non puoi aggiungere un figlio immediatamente (es. stai iterando sull'albero). `call_deferred` dice a Godot: "aggiungilo alla fine di questo frame, quando e' sicuro".

**Analogia:** E' come chiedere a qualcuno di sedersi a tavola — se i piatti si stanno ancora spostando, aspetti che si fermino prima di sederti.

### Tipi di nodo usati nel progetto

| Nodo | Analogia | Dove lo usiamo |
|------|----------|---------------|
| **Node2D** | Scatola vuota per raggruppare cose | `Room`, `Decorations`, `ForestBackground` |
| **Sprite2D** | Adesivo / Foto | Sfondo stanza, decorazioni, layer parallasse |
| **AnimatedSprite2D** | Flipbook automatico | Personaggio, loading screen |
| **CharacterBody2D** | Attore che cammina e collide con i muri | Personaggio giocabile |
| **StaticBody2D** | Muro immovibile | Bordi stanza, mobili (collisione) |
| **CollisionShape2D** | La "sagoma" invisibile per le collisioni | Dentro al personaggio (capsula) |
| **CollisionPolygon2D** | Sagoma irregolare per le collisioni | Dentro ai mobili (poligono a 8 punti) |
| **CanvasLayer** | Vetro trasparente sopra tutto | UILayer (bottoni, pannelli) |
| **ColorRect** | Foglio di carta colorata | Overlay muro/pavimento, dim overlay menu |
| **Camera2D** | Telecamera che inquadra la scena | Loading screen (zoom 3.6x) |
| **Control** | Base per gli elementi UI | Bottoni, pannelli, label |
| **Timer** | Sveglia che suona dopo X secondi | Animazione menu character |

---

## 5. La Stanza — Come costruiamo il mondo

### La scena principale (main.tscn) — Strato per strato

La stanza di gioco e' costruita come un **panino a strati**. Ogni strato si sovrappone al precedente:

```
STRATO 7 ──── UILayer (CanvasLayer, layer=10)
               Bottoni, HUD, pannelli.
               Su un vetro separato: non si muove con la camera.

STRATO 6 ──── RoomGrid (Node2D, custom _draw)
               Griglia a 64px. Visibile solo quando piazzi decorazioni.

STRATO 5 ──── Character (CharacterBody2D)
               Il personaggio che cammini.
               Scala 3x → 32px diventano 96px.

STRATO 4 ──── Decorations (Node2D)
               Letti, scrivanie, piante, gatto.
               Sprite create a runtime da room_base.gd.

STRATO 3 ──── RoomBounds (StaticBody2D)
               Muri invisibili. Il personaggio non puo' uscire.

STRATO 2 ──── Baseboard (ColorRect)
               Linea di 1 pixel tra muro e pavimento.

STRATO 1 ──── WallRect + FloorRect (ColorRect)
               Filtri colorati semi-trasparenti (alpha 0.6).
               I colori vengono da rooms.json.

STRATO 0 ──── RoomBackground (Sprite2D)
               L'immagine base della stanza: room.png.
```

**Flusso completo quando il gioco parte:**

1. `main.gd` carica la stanza dal salvataggio
2. Piazza `room.png` come sfondo
3. Legge il tema da `rooms.json` e colora `WallRect` e `FloorRect`
4. `room_base.gd` legge le decorazioni salvate e le crea come Sprite2D
5. Istanzia il personaggio dalla PackedScene
6. Mostra la UI su CanvasLayer

### Le zone della stanza — I numeri che contano

```
0px                                                          1280px
 ┌──────────────────────────────────────────────────────────────┐
 │                         MURO (40%)                           │
 │                  wall_color, alpha 0.6                       │
 │                                                              │
 ├──────────────────── 288px ───────────────────────────────────┤ ← Battiscopa
 │                                                              │
 │    280px ┌────────────────────────────┐ 1000px               │
 │          │                            │                      │
 │          │    ZONA PAVIMENTO (60%)    │                      │
 │          │    floor_color, alpha 0.6  │                      │
 │          │                            │                      │
 │          │    Griglia: 64px per cella │                      │
 │          │    Qui stanno i mobili     │                      │
 │          │    e il personaggio        │                      │
 │          │                            │                      │
 │          └────────────────────────────┘ 670px                │
 │                                                              │
 └──────────────────────────────────────────────────────────────┘
                                                               720px
```

**Costanti chiave:**
- **WALL_ZONE_RATIO = 0.4** → il 40% superiore e' muro, il 60% e' pavimento
- **ROOM_LEFT = 280, ROOM_RIGHT = 1000** → la stanza non occupa tutta la larghezza
- **ROOM_BOTTOM = 670** → un margine in basso
- **CELL_SIZE = 64** → ogni casella della griglia e' 64x64 pixel
- **OVERLAY_ALPHA = 0.6** → i filtri colorati sono al 60% di opacita'

### I temi — Come cambiare colore alla stanza

Il tema della stanza funziona come mettere delle **gelatine colorate** sopra una lampadina. L'immagine base (room.png) rimane sempre la stessa — cambiano solo i filtri colorati sopra.

```
rooms.json definisce 3 temi:
  "modern"  → muro: viola scuro (#2a2535), pavimento: viola medio (#3d3347)
  "natural" → muro: verde scuro (#2d3025), pavimento: verde medio (#3a4230)
  "pink"    → muro: rosa scuro (#352530), pavimento: rosa medio (#453540)
```

**Analogia:** E' come avere una stanza bianca e cambiare il colore delle tende. La struttura della stanza non cambia, ma l'atmosfera si'.

### Le collisioni — I muri invisibili

Il personaggio non puo' camminare fuori dalla stanza grazie al sistema di **collisioni** a livelli:

```
Layer 1 = Muri della stanza (StaticBody2D con CollisionPolygon2D)
Layer 2 = Decorazioni (StaticBody2D dei mobili)

Personaggio:
  collision_layer = 0  → "Non sono un ostacolo per nessuno"
  collision_mask = 3   → "Collido con layer 1 E layer 2" (muri + mobili)
  collision_mask = 1   → "Collido solo con layer 1" (solo muri, in edit mode)
```

**Perche' la maschera cambia?** In modalita' normale, il personaggio non puo' attraversare i mobili. In modalita' "piazza decorazioni" (edit mode), il personaggio deve poter passare attraverso i mobili per muoverli.

**Analogia:** E' come se il personaggio avesse degli occhiali speciali. Con gli occhiali normali, vede sia i muri che i mobili e li evita. Con gli occhiali "edit mode", vede solo i muri e attraversa i mobili come un fantasma.

### Il menu principale (main_menu.tscn) — La sequenza di apertura

```
SCHERMO LOADING (visibile, alpha=1.0)
        ↓ pausa 0.4s
        ↓ fade out 0.5s (alpha 1.0 → 0.0)
SFONDO FORESTA (8 layer parallasse)
        ↓ personaggio entra da sinistra
        ↓ cammina per 2 secondi (da x=-100 a x=640)
BOTTONI (appaiono con fade in 0.3s)
        ↓ il giocatore puo' interagire
```

**La parallasse — l'illusione di profondita':**

Lo sfondo del menu ha 8 layer di foresta sovrapposti. Quando muovi il mouse, i layer si spostano a velocita' diverse:

```
Layer 0 (montagne lontane)  → non si muove
Layer 1                     → si muove 1px
Layer 2                     → si muove 2px
Layer 3                     → si muove 3px
...
Layer 7 (alberi vicini)     → si muove 8px
```

**Analogia:** Guarda fuori dal finestrino di un treno. Le montagne lontane sembrano ferme, le colline si muovono lentamente, gli alberi vicini al binario sfrecchiano. Stesso principio applicato al mouse.

**Dove nel codice:** `scripts/rooms/window_background.gd`

---

## 6. Rendering — L'ordine in cui le cose vengono dipinte

### Il pittore e i layer

Il rendering 2D funziona come un **pittore che dipinge su tele sovrapposte**. Cio' che viene dipinto per ultimo appare sopra tutto il resto.

Ci sono **due sistemi** per controllare l'ordine:

#### Sistema 1: z_index — "L'ordine sulla stessa tela"

Ogni nodo ha un `z_index`. Numeri piu' alti = disegnati sopra.

```
z_index = -1  → Sfondo
z_index =  0  → Default (la maggior parte delle cose)
z_index =  1  → Sopra il default
z_index = 100 → Molto in alto (es. schermata di login)
```

`z_as_relative = true` (il default) significa che il z_index del figlio si somma a quello del padre. Come un bambino su un ascensore: se il piano del padre sale, il bambino sale con lui.

#### Sistema 2: CanvasLayer — "Tele separate"

Un `CanvasLayer` crea una **tela completamente separata**. I nodi su layer diversi non si influenzano mai.

```
CanvasLayer layer=0   → Il mondo di gioco (default)
CanvasLayer layer=10  → UILayer: bottoni, HUD
CanvasLayer layer=100 → Popup decorazioni, auth screen
```

**La differenza fondamentale:** z_index riordina gli elementi sulla stessa tela. CanvasLayer crea tele diverse. Un nodo su CanvasLayer 10 sara' SEMPRE sopra tutto cio' che sta su CanvasLayer 0, indipendentemente dal z_index.

**Analogia:** z_index e' come riordinare i fogli su una scrivania. CanvasLayer e' come avere scrivanie separate a piani diversi — la scrivania al piano 10 sara' sempre sopra quella al piano 0, non importa come riordini i fogli su ciascuna.

### modulate — Il colore moltiplicatore

`modulate` e' un colore che viene **moltiplicato** per i pixel del nodo. E' il modo principale per:

- **Rendere trasparente**: `modulate.a = 0.5` → 50% trasparente
- **Colorare**: `modulate = Color(1, 0, 0)` → tutto diventa rosso
- **Nascondere con fade**: anima `modulate.a` da 1.0 a 0.0

**Regola della moltiplicazione:**
```
Padre: modulate.a = 0.5 (50% trasparente)
Figlio: modulate.a = 0.5 (50% trasparente)
Risultato del figlio sullo schermo: 0.5 × 0.5 = 0.25 (25% visibile!)
```

Se vuoi colorare SOLO un nodo senza influenzare i figli, usa `self_modulate` al posto di `modulate`.

### Custom _draw() — Disegnare a mano

Godot permette di disegnare forme direttamente sullo schermo sovrascrivendo la funzione `_draw()`. Nel nostro progetto, la **griglia di piazzamento** usa questo metodo.

```
scripts/rooms/room_grid.gd:

_draw() disegna:
- Linee verticali ogni 64px (da x=280 a x=1000)
- Linee orizzontali ogni 64px (da y=288 a y=670)
- Colore: bianco al 12% di opacita' (quasi invisibile, ma utile come guida)
```

**Regola importante:** `_draw()` viene chiamato UNA SOLA VOLTA e il risultato viene salvato in memoria (cachato). Se qualcosa cambia e vuoi ridisegnare, devi chiamare `queue_redraw()`.

**Analogia:** E' come disegnare un quadro. Non lo ridipingi ogni secondo — lo dipingi una volta e lo appendi. Se vuoi cambiarlo, devi ridipingerlo esplicitamente.

**Dove nel codice:** Quando il giocatore entra/esce dalla modalita' decorazioni, il segnale `decoration_mode_changed` chiama `queue_redraw()` per mostrare/nascondere la griglia.

---

## 7. Tween — Le animazioni fluide

### Cos'e' un Tween?

Un **Tween** interpola un valore da A a B nel tempo. E' il modo in cui creiamo tutte le transizioni fluide del gioco.

**Analogia:** Immagina un cursore di volume. Un Tween lo muove gradualmente da "silenzio" a "massimo" in 0.5 secondi, invece di saltare istantaneamente. Puoi applicare lo stesso concetto a posizione, trasparenza, colore, scala — qualsiasi numero.

### Dove li usiamo

| Dove | Cosa anima | Durata | File |
|------|-----------|--------|------|
| Apertura pannelli | Trasparenza 0 → 1 | 0.3s | panel_manager.gd |
| Chiusura pannelli | Trasparenza 1 → 0, poi distruggi | 0.3s | panel_manager.gd |
| Fade out loading screen | Trasparenza 1 → 0 | 0.5s | main_menu.gd |
| Walk-in personaggio menu | Posizione x: -100 → 640 | 2.0s | menu_character.gd |
| Fade in bottoni menu | Trasparenza 0 → 1 | 0.3s | main_menu.gd |

### Le curve — Come si muove il valore

Non tutti i movimenti sono uguali. Un oggetto che rallenta alla fine sembra piu' naturale di uno che si ferma di colpo.

```
EASE_OUT + TRANS_QUAD (il nostro preferito):
  Veloce all'inizio, rallenta alla fine.
  Come una palla lanciata: parte veloce, decelera per attrito.

  Velocita'
  ▲
  █████
  ████████
  ██████████
  ████████████
  ██████████████
  ████████████████     ← rallenta gradualmente
  ──────────────────▶ Tempo

EASE_IN + TRANS_QUAD:
  Lento all'inizio, accelera alla fine.
  Come una macchina che parte: lenta, poi veloce.

LINEAR (nessuna curva):
  Velocita' costante.
  Come un nastro trasportatore.
```

**Dove nel codice:**
```gdscript
# menu_character.gd — il personaggio entra con decelerazione naturale
tween.set_ease(Tween.EASE_OUT)       # Rallenta alla fine
tween.set_trans(Tween.TRANS_QUAD)    # Curva quadratica (morbida)
tween.tween_property(self, "position", Vector2(640, 530), 2.0)
```

### Ciclo di vita del Tween — Attenzione ai duplicati!

**Regola 1:** Un Tween creato con `create_tween()` e' legato al nodo che lo crea. Quando il nodo viene distrutto, il tween muore con lui. Non serve pulizia manuale.

**Regola 2 (dal nostro audit!):** Se chiami una funzione che crea un tween DUE VOLTE, avrai DUE tween che animano la stessa cosa in parallelo — risultato imprevedibile!

**La soluzione — salva e killa:**
```gdscript
var _tween: Tween       # Variabile di classe (persiste)

func fade_in() -> void:
    if _tween:
        _tween.kill()   # Uccidi il vecchio tween se esiste
    _tween = create_tween()
    _tween.tween_property(self, "modulate:a", 1.0, 0.3)
```

**Analogia:** E' come avere un solo telecomando per il volume. Se qualcuno sta gia' alzando il volume (tween 1) e tu premi "abbassa" (tween 2), i due comandi si contraddicono. Devi prima fermare il primo, poi dare il secondo.

### Concatenare azioni in sequenza

I tween possono fare cose in sequenza, come una catena di montaggio:

```gdscript
var tween := create_tween()
tween.tween_interval(0.4)                              # 1. Aspetta 0.4s
tween.tween_property(loading, "modulate:a", 0.0, 0.5)  # 2. Fade out loading
tween.tween_callback(loading.set_visible.bind(false))   # 3. Nascondi loading
tween.tween_callback(character.walk_in)                 # 4. Fai entrare il personaggio
```

Ogni azione inizia quando la precedente finisce. E' la sequenza intro del menu.

---

## 8. Temi e Stile — L'aspetto dei bottoni e pannelli

### Il sistema Theme di Godot

Godot ha un sistema per dare un **aspetto coerente** a tutti gli elementi UI (bottoni, label, pannelli, slider). Funziona come i CSS per le pagine web.

Il nostro tema si chiama `cozy_theme.tres` e usa texture dal **Kenney Pixel UI Pack** (stile medievale/antico, tonalita' beige/marrone).

### 9-Slice — Il trucco per scalare le cornici

Un bottone puo' essere largo 100px o 500px, ma il bordo deve restare sempre della stessa dimensione. Il **9-Slice** risolve questo problema tagliando la texture in 9 pezzi:

```
┌───┬─────────────────┬───┐
│ A │        B        │ C │   A, C, G, I = angoli → restano fissi
├───┼─────────────────┼───┤   B, H = bordi orizzontali → si allungano in larghezza
│ D │        E        │ F │   D, F = bordi verticali → si allungano in altezza
├───┼─────────────────┼───┤   E = centro → si espande in entrambe le direzioni
│ G │        H        │ I │
└───┴─────────────────┴───┘

Bottone piccolo:        Bottone grande:
┌─┬──┬─┐               ┌─┬──────────────────┬─┐
│A│B │C│               │A│        B         │C│
├─┼──┼─┤               ├─┼──────────────────┼─┤
│D│E │F│               │D│        E         │F│
├─┼──┼─┤               ├─┼──────────────────┼─┤
│G│H │I│               │G│        H         │I│
└─┴──┴─┘               └─┴──────────────────┴─┘
Gli angoli sono identici! Solo il centro e i bordi cambiano dimensione.
```

**Analogia:** E' come una cornice per quadri. Se compri un quadro piu' grande, gli angoli della cornice restano uguali — si allungano solo i lati. Stessa idea.

### Stili per stato

Ogni bottone ha un aspetto diverso per ogni stato:

```
cozy_theme.tres:
  Button:
    ├── normal   → Sfondo marrone (stato di riposo)
    ├── hover    → Sfondo beige chiaro (il mouse e' sopra)
    ├── pressed  → Sfondo grigio (il bottone e' premuto)
    └── disabled → Sfondo grigio spento (non cliccabile)
```

### Pannelli creati via codice

I nostri pannelli UI (impostazioni, profilo, decorazioni) NON hanno un file `.tscn` con il layout. Vengono costruiti **interamente via codice** in GDScript.

**Perche'?** Per pannelli semplici con pochi elementi, scrivere il codice e' piu' veloce e facile da mantenere che creare un file `.tscn` nell'editor. Se i pannelli diventassero piu' complessi (molti bottoni, layout annidati), sarebbe meglio usare `.tscn`.

**Analogia:** E' come arredare una stanza. Per mettere un tavolo e due sedie, basta farlo a mano. Per arredare un intero appartamento, meglio usare un software di design (l'editor .tscn).

**Override per singoli elementi:**
```gdscript
# Cambiare il colore del testo di un bottone "Elimina" in rosso
delete_btn.add_theme_color_override("font_color", Color(0.9, 0.3, 0.3))
```

---

## 9. TileMap — Un sistema che non usiamo (ancora)

### Cosa sono le TileMap?

Immagina di costruire una stanza usando **piastrelle** (tile) invece di un poster unico. Ogni piastrella e' piccola (es. 32x32 pixel) e puo' essere riutilizzata.

**Analogia del LEGO vs del poster:**
- **Il nostro approccio attuale (poster):** La stanza e' un'unica immagine artistica. Bella, ma non modificabile pezzo per pezzo.
- **L'approccio TileMap (LEGO):** La stanza e' costruita con mattoncini riusabili. Meno artistica, ma puoi cambiare ogni mattoncino singolarmente.

### Perche' non le usiamo?

| Motivo | Spiegazione |
|--------|------------|
| La stanza e' un artwork unico | Il nostro `room.png` e' un disegno artistico che perderebbe personalita' se scomposto in tile |
| Le decorazioni funzionano gia' bene | Il drag-and-drop con Sprite2D libere e' flessibile |
| Non abbiamo bisogno di layout multipli | Una sola stanza rettangolare, non serve costruire livelli diversi |

### Quando potrebbero servirci?

- **Stanze con layout diversi** (ad L, con balcone, a piu' piani)
- **Editor di livelli** per il giocatore (come in un sim)
- **Collisioni automatiche** per muro (ogni tile muro ha la sua collisione)

### I concetti chiave (per cultura generale)

**TileSet** = la scatola di mattoncini LEGO (l'insieme di piastrelle disponibili)
**TileMapLayer** = il piano dove piazzi i mattoncini (ogni layer e' un nodo separato)
**Terrain/Autotiling** = il sistema che sceglie automaticamente i pezzi di bordo giusti

```
Senza autotiling:         Con autotiling:
█ █ █ █                   ╔═══╗
█       █                 ║   ║
█       █                 ║   ║
█ █ █ █                   ╚═══╝
(devi piazzare ogni        (Godot sceglie automaticamente
 pezzo di bordo a mano)    i bordi, gli angoli, ecc.)
```

**Riferimento nel nostro repo:** Il plugin `addons/virtual_joystick/example/` contiene un esempio funzionante con TileMapLayer. Utile per studiare senza creare nulla da zero.

---

## 10. Mappa Completa

### Dove vive ogni concetto nel nostro codice

```
SPRITE E TEXTURE
├── project.godot                    → Filtro globale NEAREST
├── scripts/rooms/room_base.gd      → Crea decorazioni (Sprite2D)
├── scripts/menu/menu_character.gd   → Animazione manuale (Sprite2D + hframes)
├── scenes/male-old-character.tscn   → SpriteFrames con 16 animazioni
├── data/decorations.json            → 69 decorazioni: sprite_path, item_scale
└── data/characters.json             → Percorsi spritesheet per ogni personaggio

SCENE E NODI
├── scenes/main/main.tscn           → Scena principale (stanza gioco)
├── scenes/menu/main_menu.tscn      → Menu principale
├── scenes/male-old-character.tscn  → Personaggio (CharacterBody2D)
├── scenes/room/*.tscn              → Mobili (StaticBody2D senza script)
└── scenes/menu/loading_screen.tscn → Loading screen (AnimatedSprite2D)

RENDERING E ANIMAZIONE
├── scripts/main.gd                  → Theming stanza (ColorRect overlay)
├── scripts/rooms/room_grid.gd       → Griglia custom _draw() 64px
├── scripts/rooms/window_background.gd → Parallasse 8 layer
├── scripts/ui/panel_manager.gd      → Fade tween pannelli (0.3s)
├── scripts/menu/main_menu.gd        → Sequenza intro (loading → walk-in → bottoni)
├── scripts/rooms/decoration_system.gd → Popup su CanvasLayer(100)
├── scripts/rooms/character_controller.gd → Selezione animazione 8 direzioni
└── assets/ui/cozy_theme.tres        → Tema UI 9-slice (Kenney Ancient)

DATI
├── data/rooms.json                  → Temi stanza (colori muro/pavimento)
├── data/decorations.json            → Catalogo decorazioni (69 items)
├── data/characters.json             → Catalogo personaggi
└── data/tracks.json                 → Catalogo tracce musicali
```

### Costanti numeriche importanti

| Costante | Valore | Significato |
|----------|--------|------------|
| Viewport | 1280 x 720 | Risoluzione del gioco |
| Stretch mode | canvas_items | Scala per adattarsi alla finestra |
| Clear color | #1f1c2e | Viola scuro di sfondo |
| Default filter | NEAREST | Pixel netti (no sfocatura) |
| OVERLAY_ALPHA | 0.6 | Opacita' filtri colorati stanza |
| CELL_SIZE | 64 px | Dimensione casella griglia |
| ROOM_LEFT | 280 px | Bordo sinistro zona giocabile |
| ROOM_RIGHT | 1000 px | Bordo destro zona giocabile |
| ROOM_BOTTOM | 670 px | Bordo inferiore zona giocabile |
| WALL_ZONE_RATIO | 0.4 | 40% muro, 60% pavimento |
| PARALLAX_STRENGTH | 8.0 | Max spostamento parallasse (pixel) |
| Character scale (gioco) | 3.0x | 32px → 96px |
| Character scale (menu) | 4.0x | 32px → 128px |
| Furniture scale | 3.0x | Mobili |
| Plants scale | 6.0x | Piante (immagini originali piu' piccole) |
| Pet scale | 4.0x | Animali |
| Panel fade | 0.3s | Durata apertura/chiusura pannelli |
| Scene fade | 0.5s | Durata transizione loading screen |
| Walk-in duration | 2.0s | Durata camminata personaggio nel menu |
| Grid opacity | 12% | Visibilita' griglia (bianco quasi invisibile) |
| Animation FPS | 5.0 | Frame per secondo (tutte tranne rotate) |
| Rotate FPS | 3.0 | Frame per secondo (solo rotate) |
| CanvasLayer UI | 10 | Layer per bottoni e HUD |
| CanvasLayer Popup | 100 | Layer per popup e auth screen |
| Collision layer muri | 1 | Bit 0 |
| Collision layer decorazioni | 2 | Bit 1 |

---

## Come Leggere i Documenti Originali

Questo riassunto copre tutti e 4 i documenti. Se vuoi approfondire un argomento specifico:

| Argomento | Documento completo | Sezioni chiave |
|-----------|--------------------|----------------|
| Sprite2D, texture, filtri, importazione | [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) | Sez. 1.1-1.6 (teoria), Sez. 2 (nel progetto) |
| AnimatedSprite2D, SpriteFrames, AtlasTexture | [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) | Sez. 1.3-1.4 |
| Albero scene, ciclo vita nodi, PackedScene | [SCENES_AND_NODES.md](SCENES_AND_NODES.md) | Sez. 1.1-1.3 |
| Tipi di nodo, CanvasLayer, collision layers | [SCENES_AND_NODES.md](SCENES_AND_NODES.md) | Sez. 1.4-1.7 |
| Struttura main.tscn e main_menu.tscn | [SCENES_AND_NODES.md](SCENES_AND_NODES.md) | Sez. 2.1-2.2 |
| z_index, modulate, _draw(), queue_redraw | [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) | Sez. 1.1-1.3 |
| Tween, easing, ciclo di vita, concatenamento | [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) | Sez. 1.4 |
| Viewport, Camera2D, sistema Theme | [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) | Sez. 1.5-1.6 |
| Parallasse, griglia, popup, theming stanza | [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) | Sez. 2.1-2.7 |
| TileSet, TileMapLayer, Terreni, Autotiling | [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md) | Sez. 1.1-1.7 |
| Confronto TileMap vs nostro approccio | [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md) | Sez. 2.1-2.2 |

---

*IFTS Projectwork 2026 — Relax Room Team*

---

## Esercizi

1. **Reflective writing.** Spiega in 1 pagina come i 4 sistemi visuali (sprite, scene, tile, rendering) collaborano nel tuo progetto preferito.

## Collegamenti incrociati

- Moduli 02-05 (visual stack).
- Modulo 09 — `PROJECT_DEEP_DIVE.md`: case study Relax Room.

## Glossario locale

Vedi `00-GLOSSARY.md` (composizione di SPRITES, SCENES, TILES, RENDERING).
