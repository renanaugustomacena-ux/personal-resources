# Database e Persistenza nei Giochi — Studio per Relax Room

> **Modulo del corso:** Godot 4 in Production
> **Posizione:** Fase 3 — Persistence · Modulo 08
> **Prerequisiti:** Moduli 01-02; SQL basics; concetti di transactional integrity.
> **Obiettivi:** SQLite usage; save format JSON con atomic write (temp + rename); ResourceLoader/Saver; schema versioning + migration v4.0.0; Supabase per cloud sync offline-first.
> **Tempo:** lettura 60 min · lab 240 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-04-27

## Idee guida

1. **Atomic save = mai corrompi save file.** Write a `.tmp`, then `os.rename` (or `OS.move_to_trash`) atomically.
2. **Schema versioning mandatory dal day 1.** v4.0.0 migration chain: leggi `version` field, applica migration N→N+1.
3. **JSON save vs SQLite save: trade-off.** JSON = human-readable, easy debug. SQLite = transactions, query, scale.
4. **ResourceLoader/Saver per Godot Resources.** Type-safe + integrated with editor; less flexible than raw file.
5. **Cloud sync offline-first: local SQLite + sync periodic.** Mai online-only se UX e single-player.

Guida completa su come i giochi gestiscono dati persistenti: database, salvataggi,
autenticazione, cloud sync. Con focus su Godot 4, SQLite, JSON e Supabase.

---

## 1. Opzioni di Persistenza per Giochi Godot

### Confronto Formati

```
                    JSON              SQLite              Godot Resource (.tres)
                    ─────             ──────              ──────────────────────
Leggibilita'        Ottima            Solo via SQL        Media (formato testo)
Performance         Buona per         Eccellente per      Buona per
                    piccoli file      grandi dataset      singole risorse
Relazioni           No (flat)         Si (FK, JOIN)       No (singolo file)
Query               No                Si (SELECT, WHERE)  No
Concorrenza         No                Si (WAL mode)       No
Portabilita'        Universale        File .db            Solo Godot
Dimensione max      ~10 MB pratico    Terabyte            ~1 MB pratico
Crash safety        Nessuna           WAL + journal       Nessuna
Mobile              Si                Si (user://)        Si
Web export          Si                Dipende (GDExt)     Si
```

### Quando Usare Cosa

```
JSON (file di testo):
  ✓ Salvataggi di gioco (stato sessione, impostazioni)
  ✓ Cataloghi statici (decorazioni, personaggi, stanze)
  ✓ Configurazione utente
  ✓ Dati che l'utente potrebbe voler modificare manualmente
  ✗ Dati relazionali complessi
  ✗ Query frequenti su grandi dataset

SQLite (database relazionale):
  ✓ Account utente con password hash
  ✓ Inventario con relazioni (FK → account)
  ✓ Dati che richiedono query (cerca per ID, filtra per tipo)
  ✓ Integrita' referenziale (CASCADE delete)
  ✓ Sync queue per operazioni offline
  ✗ Dati molto semplici (overkill per un contatore)
  ✗ Web export senza GDExtension

Godot Resource (.tres/.res):
  ✓ Risorse di gioco (sprite, materiali, temi)
  ✓ Configurazioni statiche dell'engine
  ✗ Dati utente (non sicuro — puo' eseguire codice)
  ✗ Dati dinamici a runtime
```

### Il Pattern Dual-Persistence (il nostro approccio)

```
                     ┌──────────────┐
                     │  Game State  │
                     │  (in memory) │
                     └──────┬───────┘
                            │
                     ┌──────┴───────┐
                     │ SaveManager  │
                     │  (dirty flag │
                     │   + timer)   │
                     └──────┬───────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────┴───────┐       ┌───────┴───────┐
        │   JSON File   │       │    SQLite     │
        │  (primario)   │       │   (mirror)    │
        │               │       │               │
        │ - Settings    │       │ - Accounts    │
        │ - Room state  │       │ - Characters  │
        │ - Character   │       │ - Inventory   │
        │ - Music       │       │ - Rooms       │
        │ - Inventory   │       │ - Sync queue  │
        └───────────────┘       └───────────────┘

Perche' entrambi?
  JSON → Leggibile, facile da debuggare, source of truth per sessione
  SQLite → Integrita' relazionale, query veloci, base per cloud sync
```

---

## 2. SQLite Best Practices per Giochi

### 2.1 Transazioni (la singola ottimizzazione piu' importante)

Senza transazione, ogni statement SQLite fa un commit automatico con sync su disco.
Con una transazione, tutti gli statement vengono scritti in memoria e committati insieme.

```
SENZA transazione (10 INSERT):
  INSERT → sync disco → INSERT → sync disco → ... (10 sync = lento)

CON transazione (10 INSERT):
  BEGIN → INSERT → INSERT → ... → COMMIT → sync disco (1 sync = veloce)

Speedup tipico: 10x - 50x per operazioni batch
```

```gdscript
# SBAGLIATO — ogni INSERT e' un commit separato
func save_items(items: Array) -> void:
    db.query("DELETE FROM inventario WHERE account_id = 1;")
    for item in items:
        db.query_with_bindings(
            "INSERT INTO inventario (account_id, item_id) VALUES (?, ?);",
            [1, item.id]
        )

# CORRETTO — tutto in una transazione
func save_items(items: Array) -> void:
    db.query("BEGIN TRANSACTION;")
    db.query("DELETE FROM inventario WHERE account_id = 1;")
    for item in items:
        db.query_with_bindings(
            "INSERT INTO inventario (account_id, item_id) VALUES (?, ?);",
            [1, item.id]
        )
    db.query("COMMIT;")
```

### 2.2 WAL Mode (Write-Ahead Logging)

```
Modalita' journal di SQLite:

DELETE (default):
  - Scrive su journal file → modifica DB → cancella journal
  - Lock esclusivo durante la scrittura (blocca i lettori)
  - Sicuro ma lento

WAL (Write-Ahead Log):
  - Scrive su file .db-wal → lettori leggono dal DB originale
  - Lettori NON bloccati durante la scrittura
  - Piu' veloce per pattern read-heavy (il nostro caso)
  - Crea file .db-wal e .db-shm accanto al database

Attivazione (una volta, all'apertura):
  PRAGMA journal_mode = WAL;

Note importanti:
  - I file -wal e -shm devono stare nella stessa cartella del .db
  - Se copi il database, copia anche -wal e -shm
  - Oppure prima chiama: PRAGMA wal_checkpoint(FULL);
  - Su Android, user:// e' la cartella interna dell'app (OK per WAL)
```

### 2.3 Query Parametrizzate (Sicurezza)

```gdscript
# PERICOLOSO — SQL injection possibile
var query := "SELECT * FROM accounts WHERE display_name = '%s';" % username
db.query(query)  # Se username = "'; DROP TABLE accounts; --" → disastro

# SICURO — parametri escaped automaticamente
db.query_with_bindings(
    "SELECT * FROM accounts WHERE display_name = ?;",
    [username]
)
```

### 2.4 Indexing

```sql
-- Per tabelle piccole (<1000 righe): gli indici non servono
-- Le Primary Key hanno gia' un indice automatico

-- Se mai servisse (grandi dataset):
CREATE INDEX IF NOT EXISTS idx_inventario_account
    ON inventario(account_id);

CREATE INDEX IF NOT EXISTS idx_sync_queue_created
    ON sync_queue(created_at);

-- Il nostro gioco: tabelle piccole, indici non necessari
-- Ma buono saperlo per progetti piu' grandi
```

### 2.5 Connection Management

```gdscript
# CORRETTO — apri una volta, chiudi alla fine
func _ready() -> void:
    db = SQLite.new()
    db.path = "user://cozy_room"
    db.open_db()

func _notification(what: int) -> void:
    if what == NOTIFICATION_WM_CLOSE_REQUEST:
        db.close_db()

# SBAGLIATO — non aprire/chiudere per ogni query
func get_data():
    db.open_db()    # NO! Distrugge le performance
    db.query(...)
    db.close_db()   # NO! E perde i benefici del WAL
```

### 2.6 Migrazione Schema

```
Pattern per aggiornare lo schema senza perdere dati:

1. Controlla se la colonna/tabella esiste
2. Se manca, aggiungila con ALTER TABLE o CREATE TABLE
3. Non cancellare MAI tabelle con dati utente

Esempio — aggiungere colonna:
  IF NOT EXISTS → CREATE TABLE (per nuove tabelle)
  ALTER TABLE → ADD COLUMN (per nuove colonne, con DEFAULT)

Il nostro approccio:
  - _create_tables() definisce lo schema completo
  - _run_migrations() corregge schema vecchi
  - Ogni migrazione controlla prima se e' necessaria
  - Le migrazioni sono idempotenti (possono runnare piu' volte)
```

### 2.7 godot-sqlite su Diverse Piattaforme

```
Piattaforma    Binario                                      Note
───────────    ───────                                      ────
Windows        libgdsqlite.windows.x86_64.dll               Funziona
Linux          libgdsqlite.linux.x86_64.so                  Funziona
macOS          libgdsqlite.macos.framework/                 Universal (arm64+x86)
Android        libgdsqlite.android.arm64.so                 user:// → app internal
iOS            libgodot-cpp.ios.xcframework/                Necessita build
Web/WASM       libgdsqlite.web.wasm32.wasm                  Supporto limitato

Percorso database:
  user:// → directory dati dell'utente, scrivibile su tutte le piattaforme
  res://  → SOLO lettura dopo export (embedded nel PCK)

Su Android: user:// mappa a /data/data/com.app.name/files/
  - Scrivibile dall'app
  - Non accessibile da altre app (sandboxed)
  - Cancellato se l'app viene disinstallata
```

---

## 3. Save System — Pattern e Best Practices

### 3.1 Dirty Flag Pattern

```
Invece di salvare ad ogni modifica, il gioco marca i dati come "sporchi"
e salva solo periodicamente.

Flusso:
  1. Utente piazza decorazione → _mark_dirty()
  2. Timer 60 secondi → controlla dirty flag
  3. Se dirty=true → save_game() → dirty=false
  4. Se dirty=false → skip (niente da salvare)

Vantaggi:
  - Meno scritture su disco (performance)
  - Meno usura SSD/flash (longevita')
  - Salvataggio raggruppato (piu' efficiente)
```

### 3.2 Atomic Writes (Prevenzione Corruzione)

```
PROBLEMA: Se il gioco crasha DURANTE la scrittura del file save,
il file risulta parziale e corrotto → dati persi.

Esempio timeline di un crash:
  T0: Apri file per scrittura (file vecchio cancellato/troncato)
  T1: Scrivi 50% dei dati
  T2: CRASH! → file contiene solo 50% dei dati → corrotto

SOLUZIONE: Write-to-temp, then rename (atomic write)
  T0: Scrivi su file TEMPORANEO (save_data.tmp.json)
  T1: Scrittura completata → file temp e' integro
  T2: Copia file esistente su backup (save_data.backup.json)
  T3: Rinomina temp → primary (operazione atomica del filesystem)

Anche se il gioco crasha:
  - Durante T0-T1: file originale e' ancora integro
  - Durante T2: sia originale che temp sono integri
  - Durante T3: se il rename fallisce, originale e' ancora li'
```

```gdscript
# Pattern atomic write in GDScript
const SAVE_PATH := "user://save_data.json"
const TEMP_PATH := "user://save_data.tmp.json"
const BACKUP_PATH := "user://save_data.backup.json"

func save_game() -> void:
    var json_string := JSON.stringify(save_data, "\t")

    # 1. Scrivi su file temporaneo
    var file := FileAccess.open(TEMP_PATH, FileAccess.WRITE)
    if file == null:
        push_error("Cannot write temp save file")
        return
    file.store_string(json_string)
    file.close()

    # 2. Backup del file esistente
    if FileAccess.file_exists(SAVE_PATH):
        DirAccess.copy_absolute(
            ProjectSettings.globalize_path(SAVE_PATH),
            ProjectSettings.globalize_path(BACKUP_PATH)
        )

    # 3. Rinomina temp → primary (atomico)
    DirAccess.rename_absolute(
        ProjectSettings.globalize_path(TEMP_PATH),
        ProjectSettings.globalize_path(SAVE_PATH)
    )
```

### 3.3 Versioning e Migrazione Save

```
Ogni aggiornamento del gioco puo' cambiare il formato del save.
La catena di migrazione garantisce compatibilita' retroattiva.

Save v1.0.0 (marzo 2026 — primo formato)
  └→ v2.0.0 (aggiunta sezione music)
      └→ v3.0.0 (aggiunta sezione inventory)
          └→ v4.0.0 (rimossi campi obsoleti: tools, therapeutic, xp)
              └→ v5.0.0 (aggiunta sezione account)

Regole:
  1. MAI cancellare codice di migrazione vecchio
     (un utente potrebbe avere un save v1.0.0)
  2. Ogni migrazione e' incrementale (v1→v2, v2→v3, non v1→v5)
  3. Default sensati per nuovi campi
  4. Forward-compatible: se version > attuale, carica comunque
```

### 3.4 Backup Strategy

```
Il nostro approccio a 3 livelli:

1. Auto-backup (ogni save):
   save_data.json → save_data.backup.json
   Il backup contiene SEMPRE l'ultimo save valido

2. Atomic write (prevenzione):
   Scrivi su .tmp, poi rinomina
   Previene corruzione durante il crash

3. SQLite mirror (ridondanza):
   I dati critici (account, personaggio, inventario)
   sono duplicati nel database SQLite
   Se il JSON si corrompe, il DB ha ancora i dati
```

---

## 4. Autenticazione per Giochi Indie

### 4.1 Modelli di Autenticazione

```
Guest Mode (anonimo):
  - Nessun dato richiesto all'utente
  - Dati salvati solo localmente
  - auth_uid = "local" o UUID generato
  - Pro: frizione zero, gioco immediato
  - Contro: dati persi se si cambia dispositivo

Username + Password (locale):
  - Username unico + password hashata
  - Dati nel database locale
  - Pro: semplice, funziona offline
  - Contro: non cross-device senza cloud

Email + Password (cloud):
  - Gestito da servizio auth (Supabase, Firebase)
  - Token JWT per sessioni
  - Pro: cross-device, recupero password
  - Contro: richiede connessione internet, GDPR

OAuth (Google, Discord, etc.):
  - Autenticazione delegata al provider
  - Pro: nessuna password da gestire
  - Contro: dipendenza da servizio esterno, complessita'
```

### 4.2 Password Hashing (Sicurezza)

```
MAI salvare password in chiaro. Sempre hashare.

Livelli di sicurezza:

1. MD5 (OBSOLETO — non usare mai)
   Veloce da craccare, collisioni note

2. SHA-256 (il nostro approccio attuale)
   Hash = SHA256(salt + password)
   Pro: veloce, built-in in GDScript
   Contro: veloce = brute force piu' facile

3. bcrypt / Argon2 (gold standard)
   Hash = bcrypt(password, cost_factor)
   Pro: lento per design (anti-brute force)
   Contro: non disponibile nativamente in GDScript

Per il nostro progetto:
  - SHA-256 con salt e' sufficiente per un gioco locale
  - Se passiamo a Supabase, l'hashing lo gestisce il server
  - Il salt "MiniCozyRoom2026" rende gli hash unici per la nostra app
```

```gdscript
# Il nostro approccio
const SALT := "MiniCozyRoom2026"

func _hash_password(password: String) -> String:
    return (SALT + password).sha256_text()

# Confronto
func verify_password(password: String, stored_hash: String) -> bool:
    return _hash_password(password) == stored_hash
```

### 4.3 Flusso Guest → Account Linking

```
1. Utente gioca come Guest
   - auth_uid = "local"
   - Dati salvati localmente
   - Tutto funziona offline

2. Utente decide di creare account
   - Inserisce username + password
   - auth_uid cambia da "local" a "user_username"
   - Dati locali preservati (stesso account_id)
   - Se Supabase attivo: push dati al cloud

3. Utente accede da altro dispositivo
   - Login con username + password
   - Pull dati dal cloud
   - Stesso account, diverso dispositivo
```

---

## 5. Supabase per Giochi Godot — Preparazione Fase 4

### 5.1 Cos'e' Supabase

```
Supabase = "Firebase open-source"

Servizi inclusi:
  - Auth: Registrazione, login, JWT, OAuth providers
  - Database: PostgreSQL con API REST automatica (PostgREST)
  - Storage: File upload (immagini, avatar)
  - Realtime: WebSocket per aggiornamenti live
  - Edge Functions: Serverless functions (Deno)

Per il nostro gioco servono:
  ✓ Auth (email/password, guest→account linking)
  ✓ Database (sync dati gioco tra dispositivi)
  ✗ Storage (non abbiamo file utente da caricare)
  ✗ Realtime (gioco single-player, no multiplayer)
  ✗ Edge Functions (logica tutta client-side)
```

### 5.2 Addon per Godot

```
Opzione 1: supabase-community/godot-engine.supabase
  - Addon ufficiale della community Supabase
  - Supporta Auth, Database, Realtime, Storage
  - Godot 4 compatible
  - Usato in progetti reali (todo list, chat)

Opzione 2: Overvault-64/Supabase-Godot-API
  - Piu' leggero, focus su API essenziali
  - Buono per progetti semplici

Opzione 3: HTTPRequest nativo di Godot
  - Nessun addon, chiamate REST dirette
  - Massimo controllo, minima dipendenza
  - Piu' codice da scrivere

Raccomandazione per noi:
  Opzione 3 (HTTPRequest nativo) perche':
  - Evitiamo dipendenze da addon di terze parti
  - Il nostro caso e' semplice (poche API)
  - Massimo controllo sulla gestione errori
  - Gia' avevamo un SupabaseClient prima (possiamo riusare l'architettura)
```

### 5.3 Architettura Offline-First

```
Il principio fondamentale: il gioco deve SEMPRE funzionare offline.
Il cloud e' un bonus, non un requisito.

         ┌─────────────────┐
         │  Gioco (client)  │
         └────────┬─────────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
     │   OFFLINE  │   ONLINE   │
     │            │            │
  ┌──┴───┐  ┌────┴────┐  ┌────┴────┐
  │ JSON │  │ SQLite  │  │Supabase │
  │ save │  │   DB    │  │ (cloud) │
  └──────┘  └─────────┘  └─────────┘
     ↑           ↑             ↑
  session     account       sync
   state       data         backup

Flusso:
  1. Gioco salva SEMPRE su JSON + SQLite (locale)
  2. Se online E autenticato → push su Supabase
  3. Se push fallisce → accoda in sync_queue
  4. Al prossimo avvio online → processa sync_queue
  5. Al login da nuovo dispositivo → pull da Supabase
```

### 5.4 Sync Queue (Coda Offline)

```
Tabella sync_queue nel database locale:

queue_id | table_name | operation | payload        | created_at | retry_count
---------|------------|-----------|----------------|------------|------------
1        | characters | upsert    | {"nome":"..."}| 2026-03-30 | 0
2        | rooms      | upsert    | {"theme":...} | 2026-03-30 | 0

Quando il gioco torna online:
  1. SELECT * FROM sync_queue ORDER BY created_at
  2. Per ogni entry: invia a Supabase
  3. Se successo: DELETE FROM sync_queue WHERE queue_id = ?
  4. Se fallisce: retry_count += 1 (max 5 tentativi)
```

### 5.5 Conflict Resolution

```
Se l'utente gioca su 2 dispositivi offline e poi entrambi vanno online:

Strategia: "Last Write Wins" (basata su timestamp)

  Dispositivo A salva alle 14:00 → updated_at = "2026-03-30 14:00"
  Dispositivo B salva alle 15:00 → updated_at = "2026-03-30 15:00"

  Al sync: B vince (timestamp piu' recente)

Per un gioco cozy single-player, questa strategia e' sufficiente.
Giochi multiplayer competitivi richiedono CRDT o vector clocks (non il nostro caso).
```

### 5.6 Row Level Security (RLS)

```
Supabase usa PostgreSQL RLS per garantire che ogni utente
possa accedere SOLO ai propri dati.

-- Esempio policy: utente vede solo i suoi personaggi
CREATE POLICY "users_own_characters" ON characters
    FOR ALL
    USING (auth_uid = auth.uid());

-- Con RLS attivo + anon key nel client:
  - Anche se un hacker intercetta la key, puo' leggere solo i SUOI dati
  - Non puo' leggere/modificare dati di altri utenti

Regola: MAI usare la service_role key nel client.
  - anon key → nel gioco (client-side, con RLS)
  - service_role key → solo server-side (Edge Functions, admin)
```

### 5.7 Schema PostgreSQL per Supabase (Preparazione)

```sql
-- Schema allineato al nostro SQLite locale
-- Da creare nella dashboard Supabase quando saremo pronti

CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    auth_uid UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT DEFAULT '',
    coins INTEGER DEFAULT 0,
    inventario_capacita INTEGER DEFAULT 50,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE characters (
    character_id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(account_id) ON DELETE CASCADE,
    nome TEXT DEFAULT '',
    genere INTEGER DEFAULT 1,
    colore_occhi INTEGER DEFAULT 0,
    colore_capelli INTEGER DEFAULT 0,
    colore_pelle INTEGER DEFAULT 0,
    livello_stress INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE rooms (
    room_id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(character_id) ON DELETE CASCADE,
    room_type TEXT DEFAULT 'cozy_studio',
    theme TEXT DEFAULT 'modern',
    decorations JSONB DEFAULT '[]',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS policies
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE characters ENABLE ROW LEVEL SECURITY;
ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;

CREATE POLICY "own_data" ON accounts FOR ALL
    USING (auth_uid = auth.uid());
CREATE POLICY "own_characters" ON characters FOR ALL
    USING (account_id IN (
        SELECT account_id FROM accounts WHERE auth_uid = auth.uid()
    ));
CREATE POLICY "own_rooms" ON rooms FOR ALL
    USING (character_id IN (
        SELECT character_id FROM characters WHERE account_id IN (
            SELECT account_id FROM accounts WHERE auth_uid = auth.uid()
        )
    ));
```

---

## 6. Il Nostro Sistema — Relax Room

### 6.1 Architettura Completa

```
                        ┌─────────────┐
                        │  SignalBus   │  31 segnali
                        │  (hub)      │  (auth, save, room, audio, ...)
                        └──────┬──────┘
                               │
    ┌──────────────────────────┼──────────────────────────┐
    │                          │                          │
┌───┴────┐              ┌──────┴──────┐            ┌──────┴──────┐
│  Auth  │              │    Save     │            │    Local    │
│Manager │              │  Manager    │            │  Database   │
│        │              │             │            │             │
│ guest  │              │ JSON v5.0.0 │            │ SQLite WAL  │
│ login  │──────────────│ auto-save   │────────────│ 9 tabelle   │
│ register│  auth_uid   │ dirty flag  │ save signal│ FK cascade  │
└────────┘              │ migrations  │            │ param query │
                        │ atomic write│            │ transactions│
                        └─────────────┘            └─────────────┘
```

### 6.2 Autoload Order e Dipendenze

```
#  Autoload          Dipende da           Responsabilita'
─  ────────          ──────────           ───────────────
1  SignalBus         (nessuna)            Hub segnali globali
2  AppLogger         (nessuna)            Logging JSONL con rotation
3  LocalDatabase     SignalBus            SQLite: schema, CRUD, sync queue
4  AuthManager       LocalDatabase        Auth locale: guest/login/register
5  GameManager       SignalBus, Auth      Cataloghi JSON, stato gioco
6  SaveManager       SignalBus, Auth,     JSON save v5.0.0, auto-save 60s
                     GameManager
7  AudioManager      SignalBus, Game,     Musica lo-fi, crossfade, playlist
                     SaveManager
8  PerformanceManager SignalBus, Save     FPS cap 60/15, posizione finestra
```

### 6.3 Flusso Dati — Dal Click al Disco

```
Utente piazza decorazione
  │
  ├→ decoration_system.gd: aggiorna posizione sprite
  │
  ├→ SignalBus.decoration_placed.emit(item_id, position)
  │
  ├→ SaveManager._on_decoration_placed():
  │     decorations.append({item_id, position, scale, rotation, flip_h})
  │     _mark_dirty()
  │
  └→ [60 secondi dopo, o al cambio scena]
       │
       SaveManager.save_game():
         │
         ├→ 1. JSON.stringify(save_data)
         ├→ 2. FileAccess.open(TEMP_PATH, WRITE)
         ├→ 3. file.store_string(json_string)
         ├→ 4. DirAccess.copy (SAVE_PATH → BACKUP_PATH)
         ├→ 5. DirAccess.rename (TEMP_PATH → SAVE_PATH)
         │
         └→ SignalBus.save_to_database_requested.emit(save_data)
              │
              LocalDatabase._on_save_requested(data):
                ├→ BEGIN TRANSACTION
                ├→ upsert_account(auth_uid, data)
                ├→ upsert_character(account_id, data)
                ├→ _save_inventory(account_id, data)
                └→ COMMIT
```

### 6.4 Tabelle e Relazioni

```
accounts (1)
  │
  ├──< characters (1:1 per ora, espandibile a 1:N)
  │      │
  │      └──< rooms (1:1 per ora)
  │
  └──< inventario (1:N items)

Lookup tables (read-only):
  items ──> shop (FK)
  items ──> categoria (FK)
  items ──> colore (FK)

Utility:
  sync_queue (indipendente, coda operazioni offline)

CASCADE delete:
  DELETE account → elimina characters → elimina rooms
  DELETE account → elimina inventario
  DELETE character → elimina rooms
```

---

## 7. Checklist Stabilita' Database

### Prima di ogni release

```
[ ] Transazioni: tutte le operazioni batch sono wrappate in BEGIN/COMMIT
[ ] Atomic writes: save su temp file, poi rename
[ ] Backup: save_data.backup.json creato ad ogni salvataggio
[ ] Migrazioni: catena completa v1→v5 testata con save vecchi
[ ] Foreign keys: PRAGMA foreign_keys = ON attivo
[ ] WAL mode: PRAGMA journal_mode = WAL attivo
[ ] Parameterized queries: nessuna string interpolation in SQL
[ ] Connection: apertura singola in _ready(), chiusura in _notification()
[ ] Error handling: errori DB loggati, gioco non crasha
[ ] Android: path usa user:// (non res://)
```

---

*Study document for Relax Room — IFTS Projectwork 2026*
*Author: Renan Augusto Macena (System Architect & Project Supervisor)*

---

## Esercizi

1. **Lab — atomic save in Godot.** Implementa `save_game(data)` che scrive a `save.tmp` poi rename. Test su power-loss simulation (kill -9 mid-write).
2. **Lab — migration v1 → v4.** Save file v1 con 5 chiavi → v4 con 12 chiavi + nested struct. Implementa migration chain leggibile.
3. **Stretch — Supabase sync.** Local SQLite per stato, sync con Supabase quando online; merge bidirezionale con conflict resolution.

## Auto-valutazione

1. Atomic save: come implementare in Godot?
2. Schema versioning: campo minimo nello save.
3. JSON vs SQLite save: criteri di scelta.
4. Migration chain: design pattern.

## Collegamenti incrociati

- Modulo 09 — `PROJECT_DEEP_DIVE.md`: how Relax Room saves.
- Modulo 11 — `BUILD_AND_EXPORT.md`: where save lives post-export.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Atomic save** | Write atomico via temp file + rename. |
| **Schema versioning** | Tracking version dello schema dati. |
| **Migration chain** | Sequenza di trasformazioni v1 → vN. |
| **ResourceLoader** | Godot API per caricare resource. |
| **ResourceSaver** | Godot API per salvare resource. |
| **EditorScript** | Script GDScript eseguibile da editor. |
| **Offline-first** | App funziona senza rete, sync quando disponibile. |
| **SQLite** | Embedded SQL database. |
| **Supabase** | Open-source Firebase alternative. |
