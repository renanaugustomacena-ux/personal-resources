# Study Documents — Relax Room

Reference documents for understanding the project, Godot Engine, game development practices, and the build process.

---

## Documents

| Document | Topics Covered | Size |
|----------|---------------|------|
| [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) | Project vision, architecture, signal-driven design, data flow, scene hierarchies, save system, content inventory | ~600 lines |
| [GODOT_ENGINE_STUDY.md](GODOT_ENGINE_STUDY.md) | Engine architecture, GDScript language, scene system, signals, resources, UI, audio, autoloads, tweens, performance, debugging | ~800 lines |
| [ISOMETRIC_GAMES.md](ISOMETRIC_GAMES.md) | Isometric projection math, tile systems, depth sorting, character movement, pixel art, camera, famous games, room-based design | ~700 lines |
| [GAME_DEV_PLANNING.md](GAME_DEV_PLANNING.md) | Pre-modification checklist, version control, architecture patterns, testing, common mistakes, refactoring, technical debt, project management | ~750 lines |
| [BUILD_AND_EXPORT.md](BUILD_AND_EXPORT.md) | Compilation, Godot export system, platform builds, CI/CD, Inno Setup installer, Android APK/AAB, checklist pre-release | ~1000 lines |
| [DATABASE_AND_PERSISTENCE.md](DATABASE_AND_PERSISTENCE.md) | SQLite best practices, save system patterns, autenticazione, Supabase, sync offline-first, schema PostgreSQL | ~450 lines |
| [SPRITES_AND_TEXTURES.md](SPRITES_AND_TEXTURES.md) | Sprite2D, AtlasTexture, SpriteFrames, AnimatedSprite2D, texture filtering, pixel art import, spritesheet layout | ~400 lines |
| [SCENES_AND_NODES.md](SCENES_AND_NODES.md) | Scene tree, ciclo di vita nodi, PackedScene, instancing, CanvasLayer, collision layers, tipi di nodo 2D | ~450 lines |
| [TILES_AND_TILEMAPS.md](TILES_AND_TILEMAPS.md) | TileMapLayer, TileSet, atlas sources, terrains/autotiling, isometrica, collisioni su tile, confronto col nostro approccio | ~350 lines |
| [RENDERING_AND_VISUAL_LOGIC.md](RENDERING_AND_VISUAL_LOGIC.md) | Z-ordering, custom _draw(), tweens, parallasse, viewport, temi UI, modulate, costanti di rendering del progetto | ~500 lines |

## Suggested Reading Order

1. **PROJECT_DEEP_DIVE.md** — Start here to understand what we're building and why
2. **GODOT_ENGINE_STUDY.md** — Learn the engine that powers our project
3. **SPRITES_AND_TEXTURES.md** — Understand how sprites, textures and animations work
4. **SCENES_AND_NODES.md** — Master scene composition and node lifecycle
5. **RENDERING_AND_VISUAL_LOGIC.md** — Learn 2D rendering, tweens, parallax and theming
6. **TILES_AND_TILEMAPS.md** — Understand tilemaps (not used yet, but essential knowledge)
7. **ISOMETRIC_GAMES.md** — Understand the game genre and rendering techniques
8. **DATABASE_AND_PERSISTENCE.md** — Understand data persistence, auth, and cloud sync
9. **GAME_DEV_PLANNING.md** — Learn how to plan changes without breaking things
10. **BUILD_AND_EXPORT.md** — Understand how the game reaches players (export, installer, Android)

## Glossario Rapido del Progetto

Termini specifici di Relax Room che troverete nei documenti e nel codice:

| Termine | Significato |
|---------|-------------|
| **SignalBus** | Autoload che fa da "centralino" per tutti i segnali globali del gioco. Ogni comunicazione tra sistemi passa da qui |
| **Catalog-Driven** | Approccio in cui il contenuto del gioco (stanze, decorazioni, personaggi) e' definito in file JSON, non nel codice |
| **Offline-First** | Il gioco funziona offline con JSON + SQLite. Supabase previsto per cloud sync (Fase 4) |
| **Desktop Companion** | Genere di applicazione progettata per restare aperta a lungo in sottofondo, con consumo minimo di risorse |
| **WAL (Write-Ahead Logging)** | Modalita' di SQLite che scrive prima in un journal (.db-wal) e poi nel database. Piu' sicuro e veloce |
| **Dirty Flag** | Flag booleano che indica "ci sono modifiche non salvate". SaveManager salva solo quando il flag e' attivo |
| **Crossfade** | Transizione audio graduale: una traccia si abbassa mentre la nuova sale. Gestita da AudioManager |
| **Tween** | Oggetto Godot che interpola valori nel tempo (animazioni, transizioni, fade). Va sempre tracciato e ucciso in _exit_tree |
| **_exit_tree()** | Funzione callback di Godot chiamata quando un nodo sta per essere rimosso dall'albero. Usata per pulizia risorse |
| **queue_free()** | Metodo Godot per distruggere un nodo alla fine del frame corrente (non immediatamente) |
| **Autoload** | Script caricato automaticamente da Godot all'avvio del gioco, accessibile ovunque come singleton globale |
| **GdUnit4** | Framework di testing per Godot 4. Non installato — i test sono stati rimossi (marzo 2026) |
| **AuthManager** | Autoload che gestisce l'autenticazione: guest mode, username+password con SHA-256, eliminazione account |
| **Atomic Write** | Pattern di scrittura sicura: scrivi su file temp, poi rinomina. Previene corruzione se il gioco crasha |
| **Sync Queue** | Tabella SQLite che accoda operazioni offline per sincronizzarle quando torna la connessione |
| **Inno Setup** | Tool gratuito per creare installer .exe professionali per Windows con wizard, shortcut e uninstaller |
| **Keystore** | File che identifica l'app Android. Necessario per firmare APK/AAB. Non perdere mai il release keystore |
| **gdlint / gdformat** | Strumenti di linting e formattazione automatica per GDScript. Eseguiti nella pipeline CI |
| **PanelManager** | Classe che gestisce il ciclo di vita di tutti i pannelli UI (apertura, chiusura, animazioni) |
| **Snap to Grid** | Le decorazioni si posizionano su una griglia di 64px. `Helpers.snap_to_grid()` arrotonda la posizione |

## Quick Reference Cards

### Ordine Autoload (chi dipende da chi)

```text
1. SignalBus          ← nessuna dipendenza (caricato per primo)
2. AppLogger          ← nessuna dipendenza
3. LocalDatabase      ← usa SignalBus, AppLogger
4. AuthManager        ← usa LocalDatabase, SignalBus
5. GameManager        ← usa SignalBus, AuthManager
6. SaveManager        ← usa SignalBus, AuthManager, GameManager
7. AudioManager       ← usa SignalBus, GameManager, SaveManager
8. PerformanceManager ← usa SignalBus, SaveManager
```

### Domini dei Segnali SignalBus (31 segnali)

```text
STANZA (4)                  AUDIO (4)                SISTEMA (6)
- room_changed              - track_changed          - save_requested
- decoration_placed         - track_play_pause       - save_completed
- decoration_removed        - ambience_toggled       - load_completed
- decoration_moved          - volume_changed         - save_to_database_requested
                                                     - settings_updated
DECORAZIONI (5)             UI (2)                   - music_state_updated
- decoration_mode_changed   - panel_opened
- decoration_selected       - panel_closed           SETTINGS (1)
- decoration_deselected                              - language_changed
- decoration_rotated        AUTH (5)
- decoration_scaled         - auth_state_changed     SYNC (2)
                            - auth_error             - sync_started
CHARACTER (2)               - account_created        - sync_completed
- character_changed         - account_deleted
- outfit_changed            - character_deleted
```

### Percorsi File Importanti

```text
Codice:
  v1/scripts/autoload/       — 7 Singleton (SignalBus, AuthManager, SaveManager, ecc.)
  v1/scripts/rooms/          — Logica stanza, decorazioni, personaggi, sfondo
  v1/scripts/menu/           — Menu principale, auth screen, walk-in character
  v1/scripts/ui/             — Pannelli UI, PanelManager, drop zone, profilo
  v1/scripts/utils/          — Constants, Helpers
  v1/scripts/systems/        — PerformanceManager

Dati:
  v1/data/characters.json    — Catalogo personaggi (sprite, animazioni)
  v1/data/decorations.json   — 69 decorazioni in 11 categorie
  v1/data/rooms.json         — Catalogo stanze (temi, colori)
  v1/data/tracks.json        — Catalogo tracce musicali

Scene:
  v1/scenes/main/            — Scena principale (stanza di gioco)
  v1/scenes/menu/            — Menu principale
  v1/scenes/ui/              — Scene dei pannelli UI (.tscn)

Database:
  user://cozy_room.db        — SQLite (9 tabelle, WAL mode)
  user://save_data.json      — Save JSON v5.0.0
  user://save_data.backup.json — Backup ultimo save valido
```

## Mappa Documenti ↔ Argomenti d'Esame

Per prepararvi all'esame, ecco quali documenti coprono quali potenziali argomenti:

| Argomento d'Esame | Documento Principale | Sezioni Chiave |
|--------------------|---------------------|----------------|
| Architettura software | PROJECT_DEEP_DIVE.md | Sez. 2 (Architecture), Sez. 5 (Singletons) |
| Pattern di design (Singleton, Observer) | PROJECT_DEEP_DIVE.md + GODOT_ENGINE_STUDY.md | Sez. 2 + Sez. 6 (Signals) |
| Database relazionali (SQL, PK, FK) | DATABASE_AND_PERSISTENCE.md | Sez. 2 (SQLite), Sez. 6 (Schema) |
| Persistenza dati e salvataggi | DATABASE_AND_PERSISTENCE.md | Sez. 3 (Save Patterns), Sez. 1 (Confronto) |
| Autenticazione e sicurezza | DATABASE_AND_PERSISTENCE.md | Sez. 4 (Auth), Sez. 5 (Supabase, RLS) |
| Testing e qualita' del software | GAME_DEV_PLANNING.md | Sez. 5 (Testing), Sez. 6 (Common Mistakes) |
| CI/CD e automazione | BUILD_AND_EXPORT.md + GUIDA_CRISTIAN_CICD.md | Sez. 8 (CI/CD) + Task 1-2 |
| Versionamento (Git) | GAME_DEV_PLANNING.md | Sez. 3 (Version Control), Sez. 4 (Commit Workflow) |
| Prestazioni e ottimizzazione | GODOT_ENGINE_STUDY.md | Sez. 16 (Performance), Sez. 17 (Debugging) |
| Progettazione interfacce utente | GODOT_ENGINE_STUDY.md | Sez. 10-11 (UI, Themes) |
| Gestione progetto e lavoro in team | GAME_DEV_PLANNING.md | Sez. 8-9 (Quality vs Scope, Pipeline) |
| Export e distribuzione software | BUILD_AND_EXPORT.md | Sez. 3-7 (Export), Sez. 16-18 (Inno Setup, Android, Checklist) |
| Grafica 2D e proiezione isometrica | ISOMETRIC_GAMES.md | Tutto il documento |
| Sprite, texture e animazioni 2D | SPRITES_AND_TEXTURES.md | Sez. 1 (Concetti), Sez. 2 (Nel Progetto) |
| Composizione scene e nodi Godot | SCENES_AND_NODES.md | Sez. 1 (Concetti), Sez. 2 (Le nostre scene) |
| TileMap e level design | TILES_AND_TILEMAPS.md | Sez. 1 (TileSet, Terrain), Sez. 2 (Confronto) |
| Rendering 2D, animazione e temi | RENDERING_AND_VISUAL_LOGIC.md | Sez. 1-2 (Tween, parallax, z-index) |

## Related Resources

- [../guide/](../guide/) — Operational guides for each team member
- [../AUDIT_REPORT.md](../AUDIT_REPORT.md) — Technical audit v2.0.0 (1 April 2026 — 23 sections, 24 scripts analyzed)
- [../TECHNICAL_GUIDE.md](../TECHNICAL_GUIDE.md) — Developer reference

---

*IFTS Projectwork 2026 — Renan Augusto Macena (System Architect & Project Supervisor)*
