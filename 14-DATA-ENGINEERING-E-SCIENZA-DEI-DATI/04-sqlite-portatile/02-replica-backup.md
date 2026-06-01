# SQLite: Replica, Backup e Disaster Recovery

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 2.0.0  
> Stato: expanded

## Skip list
- [x] Bozza iniziale
- [ ] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Backup Methods
2. Online Backup API
3. SQLite Replication Solutions
4. Database Replication Tools
5. Backup Strategies
6. Disaster Recovery
7. WAL-Based Backup Techniques
8. Incremental Backup
9. Backup Verification
10. Production Backup Patterns

---

## 1. Backup Methods

### 1.1 CLI .backup Command

La CLI di SQLite offre il comando `.backup` per backup online:

```bash
# Backup completo del database corrente
sqlite3 mydb.db ".backup backup.db"

# Backup verso stdout (per piping)
sqlite3 mydb.db ".backup stdout" > backup.sql

# Backup verso file compresso
sqlite3 mydb.db ".backup stdout" | gzip > backup.db.gz

# Backup di database specifico quando sono attaccati più DB
sqlite3 mydb.db ".backup main backup.db"

# Backup con recovery su errore
sqlite3 mydb.db ".backup" backup.db
```

Il comando `.backup` usa l'API di backup interna che:
- Acquisisce un lock di lettura sul database source
- Copia pagina per pagina in modo consistente
- Rilascia i lock automaticamente al completamento
- Funziona mentre altre connessioni stanno scrivendo

### 1.2 File-Based Backup

```bash
# Per backup consistenti con WAL:
# 1. Primo: checkpoint per forzare scritture da WAL a main file
sqlite3 mydb.db "PRAGMA wal_checkpoint(TRUNCATE);"

# 2. Copiare i file (metodo base)
cp mydb.db mydb_backup.db
cp mydb.db-wal mydb_backup.db-wal  # se esiste
cp mydb.db-shm mydb_backup.db-shm  # se esiste

# 3. Alternativa: usare rsync con --inplace
rsync --inplace mydb.db mydb_backup.db
```

**Nota importante**: La copia dei file senza checkpoint può produrre un backup inconsistente se ci sono operazioni in corso. Il WAL contiene modifiche non ancora compattate nel main file.

### 1.3 SQL Dump Export

```bash
# Export completo schema + dati
sqlite3 mydb.db ".dump" > backup.sql

# Export solo schema
sqlite3 mydb.db ".schema" > schema.sql

# Export solo dati (INSERT statements)
sqlite3 mydb.db "SELECT 'INSERT INTO ' || quote(name) || ' VALUES(' || ..." > data.sql

# Export con formattazione personalizzata
sqlite3 -header -column mydb.db "SELECT * FROM users LIMIT 5"
```

Il formato `.dump` produce SQL che può essere:
- Re-importato con `sqlite3 newdb.db < backup.sql`
- Editato manualmente per modifiche
- Versionato in git come text file
- Compresso per storage efficiente

### 1.4 Backup Modes Comparison

| Metodo | Consistency | Tempo | Lock | Usage |
|--------|-------------|-------|------|-------|
| .backup | Full | Medio | Read | CLI backup |
| File copy + checkpoint | Full | Vario | Minimo | Automated script |
| .dump | Full | Lento | Read | Export/Migration |
| rsync | Parziale | Vario | Nessuno | Quick backup |

---

## 2. Online Backup API

### 2.1 Backup API Overview

L'API di backup di SQLite permette backup programmatici con controllo fine:

```c
#include <sqlite3.h>
#include <stdio.h>

int main() {
    sqlite3 *source = NULL;
    sqlite3 *dest = NULL;
    sqlite3_backup *backup = NULL;
    int rc;
    
    // Aprire database sorgente
    rc = sqlite3_open("source.db", &source);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Cannot open source: %s\n", sqlite3_errmsg(source));
        return 1;
    }
    
    // Aprire database destinazione
    rc = sqlite3_open("backup.db", &dest);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Cannot open dest: %s\n", sqlite3_errmsg(dest));
        sqlite3_close(source);
        return 1;
    }
    
    // Inizializzare backup
    backup = sqlite3_backup_init(dest, "main", source, "main");
    if (backup == NULL) {
        fprintf(stderr, "Backup init failed: %s\n", sqlite3_errmsg(dest));
        sqlite3_close(source);
        sqlite3_close(dest);
        return 1;
    }
    
    // Eseguire backup (step copia N pagine)
    // -1 significa "copia tutto"
    do {
        rc = sqlite3_backup_step(backup, -1);
        printf("Backup step: %d, remaining: %d\n", 
               rc, sqlite3_backup_remaining(backup));
    } while (rc == SQLITE_BUSY || rc == SQLITE_LOCKED);
    
    if (rc != SQLITE_DONE) {
        fprintf(stderr, "Backup failed: %s\n", sqlite3_errmsg(dest));
    } else {
        printf("Backup completed successfully\n");
    }
    
    // Finalizzare backup
    sqlite3_backup_finish(backup);
    
    // Chiudere connessioni
    sqlite3_close(source);
    sqlite3_close(dest);
    
    return rc == SQLITE_DONE ? 0 : 1;
}
```

### 2.2 Incremental Backup API

Per backup grandi, è possibile fare backup incrementali:

```c
// Backup incrementale: copia N pagine per chiamata
sqlite3_backup *backup = sqlite3_backup_init(dest, "main", source, "main");

// Copia 100 pagine per step (utile per UI progress)
int rc;
do {
    rc = sqlite3_backup_step(backup, 100);
    // Aggiornare progress bar
    printf("Progress: %d%%\n", 
           100 - (sqlite3_backup_remaining(backup) * 100 / total_pages));
    
    // Permittere other operations tra step
    if (rc == SQLITE_BUSY) {
        sqlite3_sleep(100);  // Wait and retry
    }
} while (rc == SQLITE_BUSY || rc == SQLITE_LOCKED);

// Per riprendere backup interrotto:
// Semplicemente ricreare backup con stesso source/dest
// sqlite3 resuming where left off automaticamente
```

### 2.3 Backup with Progress Callback

```c
// Callback per monitorare progresso
int backup_callback(void *param, int total, int remaining) {
    int *progress = (int*)param;
    *progress = 100 - (remaining * 100 / total);
    printf("Progress: %d%%\n", *progress);
    return 0;  // 0 = continua, 1 = abort
}

// Registrare progress handler
// (Nota: SQLite non ha callback nativo, implementare con loop)
```

### 2.4 Backup Multiple Databases

```c
// Backup di tutti gli attached databases
const char *dbs[] = {"main", "db1", "db2"};
int n = sizeof(dbs) / sizeof(dbs[0]);

for (int i = 0; i < n; i++) {
    sqlite3_backup *backup = sqlite3_backup_init(dest, dbs[i], source, dbs[i]);
    if (backup) {
        sqlite3_backup_step(backup, -1);
        sqlite3_backup_finish(backup);
    }
}
```

### 2.5 Error Handling

```c
// Gestione completa errori
sqlite3_backup *backup = sqlite3_backup_init(dest, "main", source, "main");
if (!backup) {
    printf("Error: %s\n", sqlite3_errmsg(dest));
    return;
}

int rc;
while ((rc = sqlite3_backup_step(backup, -1)) == SQLITE_BUSY ||
       rc == SQLITE_LOCKED) {
    // Attendere e riprovare
    sqlite3_sleep(100);
}

if (rc != SQLITE_DONE) {
    printf("Backup failed at page %d: %s\n",
           sqlite3_backup_remaining(backup),
           sqlite3_errmsg(dest));
}

// Verificare integrità dopo backup
int rc = sqlite3_exec(dest, "PRAGMA integrity_check", callback, NULL, &err);
if (rc != SQLITE_OK) {
    printf("Integrity check: %s\n", err);
    sqlite3_free(err);
}
```

---

## 3. SQLite Replication Solutions

### 3.1 Replication Concepts

SQLite non ha replica nativa come MySQL/PostgreSQL. Tuttavia esistono pattern per implementare replica:

**Sfide uniche di SQLite:**
- Single-writer: solo una transazione writer alla volta
- File-based: il database è un singolo file
- Embedded: non c'è server centrale

**Soluzioni disponibili:**
- WAL-based streaming replication
- Trigger-based replication
- Application-level replication
- External tools (rqlite, crate, dqlite)

### 3.2 WAL-Based Replication

```c
// Pattern: watchers seguono il WAL
// 1. Reader apre database in READ_ONLY
// 2. Periodicamente checks WAL file per nuovi frames
// 3. Applica modifiche al proprio replica

typedef struct {
    char wal_path[256];
    long last_checkpoint;
    sqlite3 *local_db;
} replica_state;

// Poll loop per replica
void *replica_thread(void *arg) {
    replica_state *state = (replica_state*)arg;
    
    while (!shutdown) {
        // Check for WAL changes
        long current_size = get_file_size(state->wal_path);
        if (current_size > state->last_checkpoint) {
            // Nuovi dati nel WAL
            apply_wal_changes(state->local_db, 
                             state->last_checkpoint, 
                             current_size);
            state->last_checkpoint = current_size;
        }
        sleep(100);  // Poll interval
    }
    return NULL;
}
```

### 3.3 Trigger-Based Replication

```c
// Creare trigger per loggare modifiche
// 1. Tabella di log
CREATE TABLE changes_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,  -- INSERT, UPDATE, DELETE
    row_id INTEGER,
    old_data TEXT,
    new_data TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

// 2. Trigger per ogni tabella da replicare
CREATE TRIGGER log_users_insert AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO changes_log (table_name, operation, row_id, new_data)
    VALUES ('users', 'INSERT', NEW.id, json(NEW));
END;

CREATE TRIGGER log_users_update AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    INSERT INTO changes_log (table_name, operation, row_id, old_data, new_data)
    VALUES ('users', 'UPDATE', OLD.id, json(OLD), json(NEW));
END;

CREATE TRIGGER log_users_delete AFTER DELETE ON users
FOR EACH ROW
BEGIN
    INSERT INTO changes_log (table_name, operation, row_id, old_data)
    VALUES ('users', 'DELETE', OLD.id, json(OLD));
END;
```

### 3.4 Application-Level Replication

```c
// Pattern: master-scattered writes
typedef enum { MASTER, REPLICA } node_role;

typedef struct {
    char *db_path;
    node_role role;
    int sync_interval_ms;
    char *master_url;
} node_config;

// Sync con master
int sync_with_master(node_config *config) {
    if (config->role != REPLICA) return 0;
    
    // Fetch changes from master
    char *changes_url;
    asprintf(&changes_url, "%s/changes?since=%ld", 
             config->master_url, last_sync_time);
    
    char *response = http_get(changes_url);
    json *changes = json_parse(response);
    
    // Apply locally
    sqlite3_exec(config->db_path, "BEGIN", NULL, NULL, NULL);
    for (each change in changes) {
        apply_change(config->db_path, change);
    }
    sqlite3_exec(config->db_path, "COMMIT", NULL, NULL, NULL);
    
    last_sync_time = current_time();
    free(response);
    return 0;
}
```

### 3.5 Third-Party Replication Systems

| Tool | Type | Description |
|------|------|-------------|
| **rqlite** | Raft consensus | SQLite with replication and fault-tolerance |
| **dqlite** | C library | Distributed SQLite using raft |
| **CrateDB** | SQL database | SQLite-compatible with clustering |
| **SpatiaLite** | Spatial extension | SQLite with GIS extensions |
| **SQLCipher** | Encrypted | Encrypted SQLite for security |

---

## 4. Database Replication Tools

### 4.1 rqlite

rqlite replica SQLite usando il protocollo Raft per consenso:

```bash
# Avviare nodo rqlite
rqlite -node-id 1 -http-addr localhost:4001 -raft-addr localhost:4002

# In un altro terminale, aggiungere al cluster
rqlite -node-id 2 -http-addr localhost:4003 -raft-addr localhost:4004 \
  -join localhost:4001

# Connect e query
curl -X POST localhost:4001/db/execute \
  -H "Content-Type: application/json" \
  -d '{"sql": "CREATE TABLE users (id TEXT PRIMARY KEY, name TEXT)"}'

curl localhost:4001/db/query -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM users"}'
```

**Caratteristiche:**
- Replica synchrona con consenso Raft
- Failover automatico
- Read scalability (followers)
- Scrittura attraverso leader

### 4.2 dqlite

dqlite è una libreria C per SQLite distribuito:

```c
#include <dqlite.h>

int main() {
    dqlite *db;
    dqlite_node *node;
    
    // Initialize node
    dqlite_node_init(&node, 1, "127.0.0.1", 8080);
    
    // Join cluster
    dqlite_node_join(node, "127.0.0.1", 8081);
    
    // Open database
    dqlite_open(&db, node, "mydb");
    
    // Now it's replicated!
    dqlite_exec(db, "CREATE TABLE t(id INTEGER PRIMARY KEY)");
    dqlite_close(db);
    
    return 0;
}
```

### 4.3 Custom Replication Pattern

```python
import sqlite3
import threading
import time
import hashlib

class SQLiteReplica:
    """Pattern per replica SQLite-based"""
    
    def __init__(self, master_path, replica_path):
        self.master_path = master_path
        self.replica_path = replica_path
        self.running = False
        self.last_sync = 0
        
    def sync(self):
        """Sincronizza replica con master"""
        master_conn = sqlite3.connect(self.master_path, readonly=True)
        replica_conn = sqlite3.connect(self.replica_path)
        
        # Get master state
        master_cursor = master_conn.cursor()
        master_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = [row[0] for row in master_cursor.fetchall()]
        
        for table in tables:
            # Get current data
            master_cursor.execute(f"SELECT * FROM {table}")
            rows = master_cursor.fetchall()
            
            # Get column names
            names = [desc[0] for desc in master_cursor.description]
            
            # Replace in replica
            replica_conn.execute(f"DELETE FROM {table}")
            replica_conn.executemany(
                f"INSERT INTO {table} VALUES ({','.join(['?']*len(names))})",
                rows
            )
        
        replica_conn.commit()
        master_conn.close()
        replica_conn.close()
        
    def start(self, interval=5):
        """Start sync thread"""
        self.running = True
        thread = threading.Thread(target=self._sync_loop, args=(interval,))
        thread.daemon = True
        thread.start()
        
    def _sync_loop(self, interval):
        while self.running:
            try:
                self.sync()
            except Exception as e:
                print(f"Sync error: {e}")
            time.sleep(interval)
    
    def stop(self):
        self.running = False
```

---

## 5. Backup Strategies

### 5.1 Backup Pyramid

```python
# Implementare backup pyramid
class BackupPyramid:
    """Schema di backup: hourly + daily + weekly + monthly"""
    
    def __init__(self, db_path, backup_dir):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.schedule = {
            'hourly': 24,      # Ultime 24 ore
            'daily': 7,        # Ultimi 7 giorni
            'weekly': 4,       # Ultime 4 settimane
            'monthly': 12      # Ultimi 12 mesi
        }
    
    def rotate_backups(self):
        """Gestisce rotazione backup secondo policy"""
        now = datetime.now()
        
        # Hourly: crea backup ogni ora
        hourly_name = f"backup_{now.strftime('%Y%m%d_%H%M%S')}.db"
        self._create_backup(hourly_name)
        self._cleanup('hourly', 24)  # Keep 24 hourly
        
        # Daily: backup a mezzanotte
        if now.hour == 0:
            daily_name = f"backup_daily_{now.strftime('%Y%m%d')}.db"
            self._create_backup(daily_name)
            self._cleanup('daily', 7)
        
        # Weekly: backup domenica
        if now.weekday() == 0 and now.hour == 0:
            weekly_name = f"backup_weekly_{now.strftime('%Y%W')}.db"
            self._create_backup(weekly_name)
            self._cleanup('weekly', 4)
    
    def _create_backup(self, name):
        import shutil
        dest = os.path.join(self.backup_dir, name)
        shutil.copy2(self.db_path, dest)
        # Anche WAL se esiste
        wal = self.db_path + "-wal"
        if os.path.exists(wal):
            shutil.copy2(wal, dest + "-wal")
    
    def _cleanup(self, tier, keep):
        """Rimuove backup più vecchi di tier"""
        # Implementare logica di retention
        pass
```

### 5.2 Incremental Backup Pattern

```python
# Backup incrementale basato su change tracking
class IncrementalBackup:
    """Backup che salva solo le differenze"""
    
    def __init__(self, db_path, backup_dir):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.last_backup_time = 0
        self.changelog = os.path.join(backup_dir, "changes.log")
    
    def create_incremental(self):
        """Crea backup incrementale"""
        # Leggere ultima posizione di backup
        if os.path.exists(self.changelog):
            with open(self.changelog) as f:
                self.last_backup_time = float(f.read())
        
        # Aprire database e leggere solo record nuovi
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Per ogni tabella con timestamp
        cursor.execute("""
            SELECT * FROM events 
            WHERE created_at > ?
        """, (self.last_backup_time,))
        
        new_rows = cursor.fetchall()
        
        # Salvare in file incrementale
        inc_file = os.path.join(
            self.backup_dir, 
            f"inc_{int(time.time())}.json"
        )
        
        with open(inc_file, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'rows': new_rows
            }, f)
        
        # Aggiornare changelog
        with open(self.changelog, 'w') as f:
            f.write(str(time.time()))
        
        conn.close()
        return len(new_rows)
    
    def restore_incremental(self, backup_files):
        """Ripristina da backup incrementali"""
        conn = sqlite3.connect(self.db_path)
        
        for inc_file in sorted(backup_files):
            with open(inc_file) as f:
                data = json.load(f)
                # Apply changes
                for row in data['rows']:
                    # Inserire record
                    pass
        
        conn.commit()
        conn.close()
```

### 5.3 Cloud Backup Pattern

```python
import boto3
import gzip
import shutil

class CloudBackup:
    """Backup automatico verso S3"""
    
    def __init__(self, db_path, bucket, prefix="backups"):
        self.db_path = db_path
        self.bucket = bucket
        self.prefix = prefix
        self.s3 = boto3.client('s3')
    
    def backup_to_s3(self):
        """Crea backup e carica su S3"""
        # Checkpoint prima di backup
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
        
        # Comprimere database
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        compressed = f"/tmp/backup_{timestamp}.gz"
        
        with open(self.db_path, 'rb') as f_in:
            with gzip.open(compressed, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Upload a S3
        key = f"{prefix}/db_{timestamp}.db.gz"
        self.s3.upload_file(compressed, self.bucket, key)
        
        # Cleanup locale
        os.remove(compressed)
        
        return key
    
    def list_backups(self):
        """Lista backup su S3"""
        response = self.s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix=self.prefix
        )
        return [obj['Key'] for obj in response.get('Contents', [])]
    
    def restore_from_s3(self, key):
        """Ripristina da S3"""
        # Download
        local = f"/tmp/restore_{int(time.time())}.db.gz"
        self.s3.download_file(self.bucket, key, local)
        
        # Decomprimere
        restored = self.db_path  # sovrascrive
        with gzip.open(local, 'rb') as f_in:
            with open(restored, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        os.remove(local)
```

---

## 6. Disaster Recovery

### 6.1 Recovery Procedures

```python
def disaster_recovery_procedure(db_path, backup_dir):
    """
    Procedura di disaster recovery per SQLite
    """
    print("=== Starting Disaster Recovery ===")
    
    # 1. Valutare danno
    print("1. Assessing damage...")
    if not os.path.exists(db_path):
        print("   Database file missing completely")
        has_db = False
    else:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("SELECT 1")
            print("   Database accessible")
            has_db = True
        except:
            print("   Database corrupted")
            has_db = False
        finally:
            conn.close()
    
    # 2. Trovare backup più recente valido
    print("2. Finding valid backup...")
    backups = sorted([
        f for f in os.listdir(backup_dir) 
        if f.endswith('.db')
    ])
    
    if not backups:
        print("   ERROR: No backups available!")
        return False
    
    # Provare ogni backup
    valid_backup = None
    for backup in reversed(backups):
        backup_path = os.path.join(backup_dir, backup)
        try:
            conn = sqlite3.connect(backup_path)
            conn.execute("PRAGMA integrity_check")
            conn.close()
            valid_backup = backup_path
            print(f"   Found valid backup: {backup}")
            break
        except:
            continue
    
    if not valid_backup:
        print("   ERROR: No valid backup found!")
        return False
    
    # 3. Restore
    print("3. Restoring database...")
    if has_db:
        # Rimuovere file corrotto
        os.remove(db_path)
        wal = db_path + "-wal"
        if os.path.exists(wal):
            os.remove(wal)
    
    shutil.copy2(valid_backup, db_path)
    
    # Copiare anche WAL se esiste
    wal_backup = valid_backup + "-wal"
    if os.path.exists(wal_backup):
        shutil.copy2(wal_backup, db_path + "-wal")
    
    print("4. Verifying restored database...")
    conn = sqlite3.connect(db_path)
    result = conn.execute("PRAGMA integrity_check").fetchone()
    conn.close()
    
    if result[0] == "ok":
        print("   ✓ Recovery successful!")
        return True
    else:
        print(f"   ✗ Integrity issues: {result[0]}")
        return False
```

### 6.2 Point-in-Time Recovery

```sql
-- Per PITR con SQLite, servono log delle transazioni
-- Abilitare WAL e mantenere WAL file storici

-- Setup per recovery:
PRAGMA journal_mode = WAL;
PRAGMA wal_autocheckpoint = 1000;

-- Per recovery:
-- 1. Identificare timestamp del recovery point
-- 2. Determinare WAL file necessari
-- 3. Applicare WAL fino al punto desiderato

-- Non esiste recovery automatico, serve implementazione custom
```

### 6.3 Corruption Recovery

```python
def recover_corrupted_db(db_path):
    """
    Tentare recovery da database corrotto
    """
    # Metodo 1: recover data da tabelle
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Per ogni tabella, tentare SELECT
    tables = cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table'
    """).fetchall()
    
    recovered_data = {}
    for (table,) in tables:
        try:
            rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
            recovered_data[table] = rows
            print(f"✓ Recovered {len(rows)} rows from {table}")
        except Exception as e:
            print(f"✗ Failed to recover {table}: {e}")
    
    conn.close()
    
    # Metodo 2: usando sqlite3_analyzer
    # $ sqlite3_analyzer corrupted.db
    
    # Metodo 3: CLI recovery
    # $ .recover
    # $ .mode insert
    # $ .output recovery.sql
    # $ SELECT * FROM table;
    
    return recovered_data
```

---

## 7. WAL-Based Backup Techniques

### 7.1 WAL Structure for Backup

```python
import struct

class WALBackup:
    """Backup tecniche basate su WAL"""
    
    WAL_FRAME_SIZE = 32 + 4096  # header + page
    
    def read_wal_header(self, wal_path):
        """Leggere header WAL"""
        with open(wal_path, 'rb') as f:
            magic = struct.unpack('>I', f.read(4))[0]
            # Salt iniziale del WAL
            # Frame count
            # Checkpoint frame
            
        return {
            'magic': magic,
            'valid': magic == 0x377f0682  # WAL magic
        }
    
    def extract_wal_frames(self, wal_path):
        """Estrai frame dal WAL per backup"""
        frames = []
        offset = 0
        
        with open(wal_path, 'rb') as f:
            while True:
                f.seek(offset)
                header = f.read(32)
                if len(header) < 32:
                    break
                
                frame_num = struct.unpack('>I', header[0:4])[0]
                page_size = struct.unpack('>I', header[4:8])[0]
                salt = header[8:16]
                checksum = header[16:32]
                
                page_data = f.read(page_size)
                
                frames.append({
                    'frame': frame_num,
                    'size': page_size,
                    'data': page_data
                })
                
                offset += 32 + page_size
        
        return frames
    
    def apply_wal_to_backup(self, db_path, wal_path):
        """Applicare WAL a backup esistente"""
        # Usare sqlite3_wal_checkpoint_v2
        # o ricostruire manualmente
        
        pass
```

### 7.2 Live WAL Backup

```python
class LiveWALBackup:
    """
    Backup del WAL mentre database è attivo.
    Utile per PITR e replica.
    """
    
    def __init__(self, db_path, backup_dir):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.last_offset = 0
    
    def backup_wal_changes(self):
        """Copia solo nuovi frame dal WAL"""
        wal_path = self.db_path + "-wal"
        
        if not os.path.exists(wal_path):
            return
        
        # Leggere dimensione attuale
        current_size = os.path.getsize(wal_path)
        
        if current_size <= self.last_offset:
            # Nessun nuovo dato
            return
        
        # Copiare solo nuovi bytes
        new_data = None
        with open(wal_path, 'rb') as f:
            f.seek(self.last_offset)
            new_data = f.read()
        
        # Salvare chunk
        chunk_file = os.path.join(
            self.backup_dir,
            f"wal_chunk_{int(time.time())}.bin"
        )
        with open(chunk_file, 'wb') as f:
            f.write(new_data)
        
        self.last_offset = current_size
        
        return len(new_data)
    
    def restore_from_wal_chunks(self, chunks, target_db):
        """Ricostruire database da chunks WAL"""
        # Concatenare chunks
        # Applicare a database base
        pass
```

---

## 8. Incremental Backup

### 8.1 Change Tracking

```python
class IncrementalBackupManager:
    """
    Sistema di backup incrementale con change tracking
    """
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.tracking_file = db_path + ".changes"
        self._init_tracking()
    
    def _init_tracking(self):
        """Inizializza file di tracking"""
        if not os.path.exists(self.tracking_file):
            # Iniziale: registra tutti i record come "backuppati"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            changes = []
            for table in self._get_tables():
                # Prendere tutti i record
                cursor.execute(f"SELECT rowid, MAX(rowid) FROM {table}")
                max_rowid = cursor.fetchone()[1]
                if max_rowid:
                    changes.append((table, max_rowid, time.time()))
            
            conn.close()
            
            # Salvare stato
            with open(self.tracking_file, 'w') as f:
                json.dump(changes, f)
    
    def _get_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    
    def get_changes_since_last_backup(self):
        """Trova record modificati dopo ultimo backup"""
        with open(self.tracking_file) as f:
            last_state = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        all_changes = []
        for table, last_rowid in last_state:
            # Nuovi record (rowid maggiore)
            cursor.execute(
                f"SELECT rowid, * FROM {table} WHERE rowid > ?",
                (last_rowid,)
            )
            new_rows = cursor.fetchall()
            
            for row in new_rows:
                all_changes.append({
                    'table': table,
                    'op': 'INSERT',
                    'data': row[1:]  # skip rowid
                })
        
        conn.close()
        return all_changes
    
    def mark_backup_complete(self):
        """Aggiorna stato dopo backup"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        new_state = []
        for table in self._get_tables():
            cursor.execute(f"SELECT MAX(rowid) FROM {table}")
            max_rowid = cursor.fetchone()[0] or 0
            new_state.append((table, max_rowid))
        
        conn.close()
        
        with open(self.tracking_file, 'w') as f:
            json.dump(new_state, f)
```

### 8.2 LSN-Based Incremental

```sql
-- Simulare LSN (Log Sequence Number) con changelog
-- Creare changelog table

CREATE TABLE _changelog (
    lsn INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    row_id INTEGER,
    before_data TEXT,
    after_data TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    synced BOOLEAN DEFAULT 0
);

-- Trigger per popolare changelog
CREATE TRIGGER track_users_changes AFTER INSERT ON users
FOR EACH ROW
WHEN NEW.id IS NOT NULL
BEGIN
    INSERT INTO _changelog (table_name, operation, row_id, after_data)
    VALUES ('users', 'INSERT', NEW.id, json(NEW));
END;

-- Query per changes non sincronizzate
SELECT * FROM _changelog WHERE synced = 0 ORDER BY lsn;

-- Dopo sync, marcare come sincronizzato
UPDATE _changelog SET synced = 1 WHERE lsn <= ?;
```

---

## 9. Backup Verification

### 9.1 Integrity Checks

```python
def verify_backup_integrity(backup_path):
    """
    Verifica integrità backup SQLite
    """
    issues = []
    
    # 1. Check se file è leggibile
    try:
        conn = sqlite3.connect(backup_path, readonly=True)
    except Exception as e:
        return {'valid': False, 'issues': [f"Cannot open: {e}"]}
    
    # 2. PRAGMA integrity_check
    result = conn.execute("PRAGMA integrity_check").fetchone()
    if result[0] != 'ok':
        issues.append(f"Integrity check failed: {result[0]}")
    
    # 3. Quick check su ogni tabella
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        try:
            # Contare righe
            count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            
            # Verificare non ci siano righe vuote
            nulls = cursor.execute(f"""
                SELECT COUNT(*) FROM {table} 
                WHERE rowid IS NULL
            """).fetchone()[0]
            
            if nulls > 0:
                issues.append(f"Table {table} has {nulls} rows with NULL rowid")
                
        except Exception as e:
            issues.append(f"Error checking {table}: {e}")
    
    # 4. Check foreign keys se abilitati
    fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk_check:
        issues.append(f"Foreign key violations: {fk_check}")
    
    # 5. Verify page count
    page_count = conn.execute("PRAGMA page_count").fetchone()[0]
    freelist = conn.execute("PRAGMA freelist_count").fetchone()[0]
    if freelist > page_count * 0.5:
        issues.append(f"High freelist: {freelist}/{page_count} pages")
    
    conn.close()
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'page_count': page_count
    }
```

### 9.2 Data Validation

```python
def validate_backup_data(original_path, backup_path):
    """
    Valida che i dati nel backup corrispondano all'originale
    """
    original = sqlite3.connect(original_path, readonly=True)
    backup = sqlite3.connect(backup_path, readonly=True)
    
    orig_cursor = original.cursor()
    back_cursor = backup.cursor()
    
    # Get tables
    orig_cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table'
    """)
    
    differences = []
    
    for (table,) in orig_cursor.fetchall():
        # Count rows
        orig_count = orig_cursor.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
        
        back_count = back_cursor.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
        
        if orig_count != back_count:
            differences.append(
                f"Table {table}: orig={orig_count}, backup={back_count}"
            )
            continue
        
        # Sample rows per confronto
        orig_cursor.execute(f"SELECT * FROM {table} LIMIT 100")
        for row in orig_cursor.fetchall():
            back_cursor.execute(
                f"SELECT * FROM {table} WHERE rowid = ?",
                (row[0],)
            )
            back_row = back_cursor.fetchone()
            if back_row != row:
                differences.append(f"Row mismatch in {table} id={row[0]}")
    
    original.close()
    backup.close()
    
    return {
        'valid': len(differences) == 0,
        'differences': differences
    }
```

### 9.3 Automated Verification Pipeline

```python
class BackupVerificationPipeline:
    """
    Pipeline automatizzato per verifica backup
    """
    
    def __init__(self, backup_dir):
        self.backup_dir = backup_dir
    
    def verify_latest_backup(self):
        """Verifica backup più recente"""
        backups = sorted(
            [f for f in os.listdir(self.backup_dir) if f.endswith('.db')],
            reverse=True
        )
        
        if not backups:
            return {'error': 'No backups found'}
        
        latest = os.path.join(self.backup_dir, backups[0])
        
        # Step 1: Integrity check
        print("1. Running integrity check...")
        integrity = verify_backup_integrity(latest)
        
        # Step 2: Data validation (solo se integrity OK)
        data_valid = {'valid': True}
        if integrity['valid']:
            print("2. Validating data...")
            # Assumiamo original sia disponibile
            original = latest.replace('backup_', '').replace('.db', '_orig.db')
            if os.path.exists(original):
                data_valid = validate_backup_data(original, latest)
        
        # Step 3: Generare report
        report = {
            'backup': backups[0],
            'timestamp': os.path.getmtime(latest),
            'integrity': integrity,
            'data': data_valid,
            'status': 'PASS' if integrity['valid'] and data_valid['valid'] else 'FAIL'
        }
        
        return report
```

---

## 10. Production Backup Patterns

### 10.1 Scheduled Backup Service

```python
import schedule
import time
import logging

class SQLiteBackupService:
    """
    Servizio di backup per produzione
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('backup')
        self._setup_logging()
    
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('backup.log'),
                logging.StreamHandler()
            ]
        )
    
    def start(self):
        """Avvia scheduler backup"""
        # Backup ogni ora
        schedule.every().hour.do(self.hourly_backup)
        
        # Backup giornaliero a mezzanotte
        schedule.every().day.at("00:00").do(self.daily_backup)
        
        # Backup settimanale domenica notte
        schedule.every().sunday.at("02:00").do(self.weekly_backup)
        
        self.logger.info("Backup service started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def hourly_backup(self):
        """Backup orario - conservare ultime 24 ore"""
        self.logger.info("Starting hourly backup")
        backup = FileBackup(self.config['db_path'], self.config['backup_dir'])
        backup.create(prefix='hourly')
        self._cleanup_old_backups('hourly', 24)
    
    def daily_backup(self):
        """Backup giornaliero - conservare 7 giorni"""
        self.logger.info("Starting daily backup")
        backup = FileBackup(self.config['db_path'], self.config['backup_dir'])
        backup.create(prefix='daily')
        self._cleanup_old_backups('daily', 7)
    
    def weekly_backup(self):
        """Backup settimanale - conservare 4 settimane"""
        self.logger.info("Starting weekly backup")
        backup = FileBackup(self.config['db_path'], self.config['backup_dir'])
        backup.create(prefix='weekly')
        self._cleanup_old_backups('weekly', 4)
    
    def _cleanup_old_backups(self, prefix, keep):
        """Rimuove backup vecchi"""
        backups = sorted(
            [f for f in os.listdir(self.config['backup_dir']) 
             if f.startswith(prefix)],
            reverse=True
        )
        
        for old in backups[keep:]:
            path = os.path.join(self.config['backup_dir'], old)
            os.remove(path)
            self.logger.info(f"Removed old backup: {old}")
```

### 10.2 Backup Monitoring

```python
class BackupMonitor:
    """
    Monitora health dei backup
    """
    
    def __init__(self, config):
        self.config = config
        self.metrics = {
            'last_backup_time': None,
            'last_backup_size': None,
            'backup_failures': 0,
            'consecutive_failures': 0
        }
    
    def check_health(self):
        """Verifica health del sistema backup"""
        issues = []
        
        # Check se backup recente esiste
        if self.metrics['last_backup_time']:
            age = time.time() - self.metrics['last_backup_time']
            if age > self.config['max_age_hours'] * 3600:
                issues.append(f"Backup too old: {age/3600:.1f} hours")
        
        # Check frequenza fallimenti
        if self.metrics['consecutive_failures'] >= 3:
            issues.append("Multiple consecutive failures")
        
        # Check spazio disponibile
        import shutil
        stat = shutil.disk_usage(self.config['backup_dir'])
        if stat.free < self.config['min_free_space']:
            issues.append(f"Low disk space: {stat.free / 1e9:.1f}GB free")
        
        return {
            'healthy': len(issues) == 0,
            'issues': issues,
            'metrics': self.metrics
        }
```

### 10.3 Complete Backup Strategy Document

```python
# Riassunto strategia di backup per produzione:

"""
Backup Strategy per SQLite in Produzione
==========================================

1. Frequenza:
   - Full backup: ogni ora
   - Retention: 24 hourly + 7 daily + 4 weekly

2. Technology:
   - WAL mode attivo per point-in-time capability
   - Checkpoint ogni 15 minuti
   - Backup via .backup API (consistente)

3. Monitoring:
   - Integrity check dopo ogni backup
   - Alert se backup più vecchio di 4 ore
   - Dashboard con backup age e size

4. Disaster Recovery:
   - RTO target: 1 ora
   - RPO target: 15 minuti (WAL-based)
   - Test recovery mensile

5. Off-site:
   - Copia giornaliera verso cloud storage
   - Retention cloud: 30 giorni

6. Rotation:
   - Tiered retention ( hourly -> daily -> weekly )
   - Delete automatico dopo retention period
   - Verify prima di delete
"""
```

---

*Questo documento fa parte del modulo 04 "SQLite Portatile" della Data Encyclopedia.*