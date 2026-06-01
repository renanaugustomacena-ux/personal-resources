# Database Replication — Conflict Resolution

## Quando Nascono i Conflitti

I conflitti di replica emergono esclusivamente in setup **multi-master** (più nodi accettano write simultaneamente). In setup single-primary, i conflitti sono impossibili per definizione — c'è un solo punto di scrittura.

Un conflitto si verifica quando due nodi modificano la stessa riga in modo incompatibile prima che la modifica di uno si propaghi all'altro.

```
t=0: Row {id=1, balance=1000} su entrambi i nodi

t=1: Node A: UPDATE accounts SET balance = 800 WHERE id = 1  (spesa di 200)
t=2: Node B: UPDATE accounts SET balance = 850 WHERE id = 1  (spesa di 150)

t=3: Node A riceve la write di Node B
     Conflitto: quale valore è quello "giusto"? 800, 850, o 650 (entrambe le spese)?
```

---

## Strategie di Risoluzione

### Last-Write-Wins (LWW)

Il valore con il timestamp più recente vince. Semplice da implementare, ma richiede orologi sincronizzati e può causare perdita di dati.

```sql
-- Galera: usa LWW basato su timestamp di certificazione
-- Il nodo che certifica per ultimo sovrascrive

-- PostgreSQL BDR: configurabile per tabella
ALTER TABLE accounts REPLICA IDENTITY FULL;
-- BDR usa il timestamp dell'ultima commit come discriminante

-- Implementazione manuale in applicazione
CREATE TABLE settings (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    node_id     INT  -- per distinguere in caso di parità di timestamp
);

-- Conflict handler: mantieni il valore più recente
CREATE OR REPLACE FUNCTION resolve_settings_conflict()
RETURNS void AS $$
BEGIN
    -- In un ambiente BDR, questa funzione viene chiamata automaticamente
    UPDATE settings s
    SET value = incoming.value, updated_at = incoming.updated_at
    FROM (VALUES ($1, $2, $3)) AS incoming(key, value, updated_at)
    WHERE s.key = incoming.key
      AND incoming.updated_at > s.updated_at;
END;
$$ LANGUAGE plpgsql;
```

**Problema**: se due scritture arrivano a 1ms di distanza, l'orologio del server determina il vincitore. Su WAN, gli orologi possono divergere di decine di millisecondi.

### Version Vectors / CRDTs

I **Conflict-free Replicated Data Types** (CRDT) sono strutture dati matematicamente progettate per convergere automaticamente senza conflitti.

**G-Counter** (solo increment, no decrement):

```python
class GCounter:
    """Grow-only counter che converge automaticamente."""
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.counts = {}  # {node_id: count}

    def increment(self, amount: int = 1):
        self.counts[self.node_id] = self.counts.get(self.node_id, 0) + amount

    def value(self) -> int:
        return sum(self.counts.values())

    def merge(self, other: 'GCounter') -> 'GCounter':
        """Merge deterministico: prende il max per ogni nodo."""
        result = GCounter(self.node_id)
        all_nodes = set(self.counts.keys()) | set(other.counts.keys())
        for node in all_nodes:
            result.counts[node] = max(
                self.counts.get(node, 0),
                other.counts.get(node, 0)
            )
        return result
```

**PN-Counter** (increment e decrement):

```python
class PNCounter:
    """Counter con operazioni positive (increment) e negative (decrement)."""
    def __init__(self, node_id: str):
        self.pos = GCounter(node_id)  # incrementi
        self.neg = GCounter(node_id)  # decrementi

    def increment(self, amount: int = 1):
        self.pos.increment(amount)

    def decrement(self, amount: int = 1):
        self.neg.increment(amount)

    def value(self) -> int:
        return self.pos.value() - self.neg.value()

    def merge(self, other: 'PNCounter') -> 'PNCounter':
        result = PNCounter(self.pos.node_id)
        result.pos = self.pos.merge(other.pos)
        result.neg = self.neg.merge(other.neg)
        return result
```

**Applicazione pratica in PostgreSQL** (CockroachDB, YugabyteDB lo fanno nativamente):

```sql
-- Simulare un G-Set (solo add) con tabelle
CREATE TABLE user_tags (
    user_id  BIGINT NOT NULL,
    tag      TEXT NOT NULL,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    added_by INT NOT NULL,  -- node_id
    PRIMARY KEY (user_id, tag)
);
-- INSERT ON CONFLICT DO NOTHING: converge automaticamente su tutti i nodi
INSERT INTO user_tags (user_id, tag, added_by)
VALUES (1001, 'premium', 1)
ON CONFLICT DO NOTHING;
```

### Applicazione Custom di Conflict Resolution

Per casi complessi, implementare la logica di business nel resolver:

```python
# Postgres BDR conflict handler custom
def resolve_inventory_conflict(local_row: dict, incoming_row: dict) -> dict:
    """
    Risolvi conflitti di inventario: la quantità più bassa vince
    (principio conservativo: meglio short-sell che over-sell).
    """
    return {
        **local_row,
        "quantity": min(local_row["quantity"], incoming_row["quantity"]),
        "last_modified": max(local_row["last_modified"], incoming_row["last_modified"]),
        "conflict_resolved": True,
        "resolution_strategy": "min_quantity"
    }

def resolve_order_status_conflict(local_row: dict, incoming_row: dict) -> dict:
    """
    Stato dell'ordine: segui una macchina a stati esplicita.
    pending < processing < shipped < delivered
    cancelled è terminale
    """
    STATUS_PRIORITY = {
        "pending": 0,
        "processing": 1,
        "shipped": 2,
        "delivered": 3,
        "cancelled": -1  # terminale, non può essere sovrascritto
    }

    local_priority = STATUS_PRIORITY.get(local_row["status"], 0)
    incoming_priority = STATUS_PRIORITY.get(incoming_row["status"], 0)

    if local_row["status"] == "cancelled":
        return local_row  # cancelled è irreversibile
    if incoming_row["status"] == "cancelled":
        return incoming_row  # cancellazione ha sempre priorità

    # Vince lo stato più avanzato nella pipeline
    if incoming_priority > local_priority:
        return {**local_row, "status": incoming_row["status"]}
    return local_row
```

---

## Prevenzione dei Conflitti: Design Patterns

Il modo migliore per gestire i conflitti è prevenirli con il design corretto.

### Partition delle Scritture

Assegna ogni entità a un nodo specifico. Solo quel nodo accetta write su quella entità.

```python
def get_write_node(entity_id: int, num_nodes: int) -> int:
    """Determina quale nodo è autoritativo per questa entità."""
    return entity_id % num_nodes

def write_order(order_id: int, data: dict):
    node = get_write_node(order_id, 3)
    nodes[node].execute("UPDATE orders SET ... WHERE id = ?", order_id, data)
```

**Problema**: non bilancia il carico se alcune entità sono molto più accedute di altre.

### Operazioni Commutative

Usare operazioni che producono lo stesso risultato indipendentemente dall'ordine.

```sql
-- Non commutativo: SET value = X (l'ultimo vince, ma potrebbe essere sbagliato)
UPDATE counters SET value = 10 WHERE id = 1;

-- Commutativo: incremento relativo (tutti gli incrementi contribuiscono)
UPDATE counters SET value = value + 5 WHERE id = 1;
-- Se arrivano due incrementi di +5 e +3 in qualsiasi ordine: risultato = +8
```

### Timestamp Ibrido Logico (HLC)

Combina wall clock e logical clock per ordinamento preciso su sistemi distribuiti:

```python
import time

class HybridLogicalClock:
    def __init__(self, node_id: int):
        self.physical_ms = 0  # wall clock in ms
        self.logical = 0      # logical clock
        self.node_id = node_id

    def now(self) -> tuple:
        """Genera un timestamp HLC."""
        wall = int(time.time() * 1000)
        if wall > self.physical_ms:
            self.physical_ms = wall
            self.logical = 0
        else:
            self.logical += 1
        return (self.physical_ms, self.logical, self.node_id)

    def update(self, remote_ts: tuple):
        """Aggiorna l'HLC con un timestamp remoto."""
        remote_phys, remote_log, _ = remote_ts
        wall = int(time.time() * 1000)
        new_phys = max(wall, self.physical_ms, remote_phys)
        if new_phys == self.physical_ms == remote_phys:
            self.logical = max(self.logical, remote_log) + 1
        elif new_phys == self.physical_ms:
            self.logical += 1
        elif new_phys == remote_phys:
            self.logical = remote_log + 1
        else:
            self.logical = 0
        self.physical_ms = new_phys
```

CockroachDB e YugabyteDB usano HLC internamente per ordinare le transazioni distribuite senza richiedere lock globali.

La conflict resolution è il problema più difficile nella replica multi-master. La soluzione più robusta è la prevenzione attraverso il design dell'applicazione — identificare le entità che richiedono consistenza forte e assicurarsi che vengano scritte su un singolo nodo autoritativo.
