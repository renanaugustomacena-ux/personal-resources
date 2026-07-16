# Tutorial Lab — DLQ, Parking Lot Pattern e Message Replay

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `22-dlq-parking-lot-pattern.md`
> **Livello:** intermediate → advanced
> **Tempo stimato:** 3-4 ore (lab completo)
> **Prerequisiti:** RabbitMQ base, Python aio-pika, concetto di idempotenza, Docker
> **Versioni di riferimento:** RabbitMQ 3.13-management · aio-pika 9.4.x · Python 3.11+

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Configurare Dead Letter Exchange (DLX) e Dead Letter Queue (DLQ) in RabbitMQ
2. Implementare il Parking Lot Pattern per messaggi non processabili
3. Costruire un CLI tool di replay per reinviare messaggi dalla DLQ
4. Distinguere errori transitori (retry) da permanenti (park)
5. Monitorare la DLQ con metriche e alert
6. Gestire message TTL e max-length per proteggere da overflow

---

## Lab Environment Setup

```bash
# Prerequisiti
python3 --version          # 3.11+
docker compose version     # 2.x

# Python deps
pip install aio-pika==9.4.3 click==8.1.7 rich==13.7.1 structlog==24.0.0

# Avvia RabbitMQ
cat > docker-compose-dlq.yml << 'EOF'
version: "3.9"
services:
  rabbitmq:
    image: rabbitmq:3.13-management-alpine
    container_name: rabbitmq-dlq-lab
    ports:
      - "5672:5672"    # AMQP
      - "15672:15672"  # Management UI
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS:-rabbitlab}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
volumes:
  rabbitmq_data:
EOF

docker compose -f docker-compose-dlq.yml up -d
sleep 10  # Attendi avvio RabbitMQ

# Struttura progetto
mkdir -p dlq-lab/{topology,producer,consumer,replay_tool,monitoring}
```

---

## Analogia Introduttiva

> **La DLQ è il cassetto "problemi da risolvere" in ufficio**:
> Quando una pratica non riesci a processarla
> (dati errati, sistema esterno down, logica incompatibile),
> non la butti — la metti in un cassetto separato (DLQ)
> con un'etichetta che dice perché non è stata processata.
>
> Il **Parking Lot** è quel cassetto con etichetta:
> "questo non lo processiamo ora, ma non vogliamo perderlo".
> Periodicamente, qualcuno guarda il cassetto e decide:
> - Reinviare (messaggio corretto, sistema ora up)
> - Analizzare manualmente (dati errati → fix nel sistema)
> - Archiviare (obsoleto, non serve più)
>
> Senza DLQ: messaggi falliti vengono scartati o
> bloccano la coda per sempre (loop di retry infinito).
> Con DLQ: sicurezza che nessun messaggio viene perso,
> e le analisi di root cause diventano possibili.

---

## Architettura del Sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FLOW MESSAGGI                                    │
│                                                                           │
│  Producer                                                                 │
│     │                                                                     │
│     ▼                                                                     │
│  Exchange "ordini" (topic)                                               │
│     │                                                                     │
│     ├──► Queue "ordini.processing" ──────────────────────────────────┐  │
│     │    TTL: 30min, max-length: 10000                                │  │
│     │    x-dead-letter-exchange: ordini.dlx                          │  │
│     │                                                                  │  │
│     │         Consumer ◄──────────────────────────────────────────── │  │
│     │              │                                                   │  │
│     │              │ success → ack                                     │  │
│     │              │ transient error → nack + requeue (max 3 retry)   │  │
│     │              │ permanent error → nack + NO requeue               │  │
│     │              │ TTL scaduto → automatic                          │  │
│     │              ▼                                                   │  │
│     │         DLX "ordini.dlx" (fanout)                              │  │
│     │              │                                                   │  │
│     │              └──► DLQ "ordini.dlq" ◄────── Parking Lot         │  │
│     │                     │                                            │  │
│     │                     │  x-death header: motivo + contatore       │  │
│     │                     │                                            │  │
│     │              ┌──────▼──────────────────────┐                   │  │
│     │              │   REPLAY TOOL (CLI)          │                   │  │
│     │              │                               │                   │  │
│     │              │ dlq-tool list                 │                   │  │
│     │              │ dlq-tool replay --filter ...  │                   │  │
│     │              │ dlq-tool purge --dry-run      │                   │  │
│     │              └──────────────────────────────┘                   │  │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                            Prometheus + Grafana
                         (messaggi in DLQ = alert!)
```

---

## PART A — Topology RabbitMQ

### A1 — Configurazione DLX/DLQ

```python
#!/usr/bin/env python3
# file: topology/setup_topology.py
"""
Crea la topology completa RabbitMQ con DLX e DLQ.
Idempotente: safe da eseguire più volte (passive=True controlla esistenza).

Struttura:
- Exchange principale: ordini (topic)
- Exchange DLX: ordini.dlx (fanout) — riceve messaggi "morti"
- Queue principale: ordini.processing — con x-dead-letter-exchange
- Queue DLQ: ordini.dlq — riceve messaggi dalla DLX
- Parking Lot Queue: ordini.parking_lot — messaggi permanentemente falliti
"""
from __future__ import annotations

import asyncio
import os
import logging
from typing import Any

import aio_pika
import aio_pika.abc

logger = logging.getLogger(__name__)

# ─── Costanti ──────────────────────────────────────────────────────────────────

EXCHANGE_MAIN = "ordini"
EXCHANGE_DLX = "ordini.dlx"

QUEUE_PROCESSING = "ordini.processing"
QUEUE_DLQ = "ordini.dlq"
QUEUE_PARKING_LOT = "ordini.parking_lot"

ROUTING_KEY_ORDINI = "ordini.#"  # Pattern wildcard topic


async def setup_topology(
    conn: aio_pika.abc.AbstractRobustConnection,
    message_ttl_ms: int = 1_800_000,  # 30 minuti
    max_length: int = 10_000,
    dlq_ttl_ms: int = 604_800_000,  # 7 giorni per messaggi in DLQ
) -> None:
    """
    Configura topology completa.
    
    Args:
        message_ttl_ms: TTL messaggi in coda principale (→ DLQ se scadono)
        max_length: Max messaggi in coda principale (→ DLQ se overflow)
        dlq_ttl_ms: TTL messaggi in DLQ prima di essere eliminati
    """
    async with conn.channel() as channel:
        # Prefetch: elabora un messaggio alla volta per worker
        await channel.set_qos(prefetch_count=1)
        
        # ─── Exchange principale (topic) ──────────────────────────────────
        exchange_main = await channel.declare_exchange(
            EXCHANGE_MAIN,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("Exchange '%s' dichiarato", EXCHANGE_MAIN)
        
        # ─── DLX (fanout) ─────────────────────────────────────────────────
        exchange_dlx = await channel.declare_exchange(
            EXCHANGE_DLX,
            aio_pika.ExchangeType.FANOUT,
            durable=True,
        )
        logger.info("DLX '%s' dichiarato", EXCHANGE_DLX)
        
        # ─── DLQ (riceve da DLX) ──────────────────────────────────────────
        dlq_args: dict[str, Any] = {
            "x-message-ttl": dlq_ttl_ms,
            "x-max-length": 50_000,
            "x-overflow": "reject-publish",  # Rifiuta invece di perdere
        }
        queue_dlq = await channel.declare_queue(
            QUEUE_DLQ,
            durable=True,
            arguments=dlq_args,
        )
        await queue_dlq.bind(exchange_dlx, routing_key="#")
        logger.info("DLQ '%s' dichiarata e bindata a DLX", QUEUE_DLQ)
        
        # ─── Parking Lot (fallimenti permanenti) ──────────────────────────
        queue_parking = await channel.declare_queue(
            QUEUE_PARKING_LOT,
            durable=True,
            arguments={"x-max-length": 100_000},
        )
        logger.info("Parking lot '%s' dichiarata", QUEUE_PARKING_LOT)
        
        # ─── Queue principale (con DLX configurata) ───────────────────────
        processing_args: dict[str, Any] = {
            # TTL: messaggio → DLQ se non consumato entro 30min
            "x-message-ttl": message_ttl_ms,
            # Max messaggi: se piena → DLQ
            "x-max-length": max_length,
            "x-overflow": "reject-publish",
            # DLX: dove mandare i messaggi "morti"
            "x-dead-letter-exchange": EXCHANGE_DLX,
            # Routing key per DLX (opzionale: default = routing key originale)
            "x-dead-letter-routing-key": "dlq.ordini",
            # Priorità: supporta priorità 0-10 (opzionale)
            # "x-max-priority": 10,
        }
        queue_processing = await channel.declare_queue(
            QUEUE_PROCESSING,
            durable=True,
            arguments=processing_args,
        )
        await queue_processing.bind(exchange_main, routing_key=ROUTING_KEY_ORDINI)
        logger.info("Queue '%s' dichiarata con DLX '%s'", QUEUE_PROCESSING, EXCHANGE_DLX)
        
        logger.info("Topology completa configurata!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        url = os.environ.get("RABBITMQ_URL", "amqp://admin:rabbitlab@localhost/")
        async with await aio_pika.connect_robust(url) as conn:
            await setup_topology(conn)
    
    asyncio.run(main())
```

---

## PART B — Consumer con DLQ Logic

### B1 — Consumer Intelligente

```python
#!/usr/bin/env python3
# file: consumer/worker.py
"""
Consumer che distingue errori transitori da permanenti.
- Transitorio (rete, DB temporaneamente down) → nack + requeue (max 3 volte)
- Permanente (dati invalidi, schema sbagliato) → nack + NO requeue → DLQ
- Successo → ack

Header x-death: RabbitMQ aggiunge automaticamente info sul "percorso mortale"
  - count: quante volte è già passato per DLQ
  - reason: rejected | expired | maxlen
  - queue: da quale queue
  - exchange: attraverso quale exchange
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
from typing import Optional

import aio_pika
import aio_pika.abc

from topology.setup_topology import (
    EXCHANGE_DLX, QUEUE_PARKING_LOT,
    setup_topology
)

logger = logging.getLogger(__name__)

# ─── Costanti ──────────────────────────────────────────────────────────────────

MAX_DELIVERY_COUNT = 3  # Massimi retry prima di mandare al Parking Lot


class TransitorioError(Exception):
    """Errore transitorio — il messaggio può essere ritentato."""


class PermanenteError(Exception):
    """Errore permanente — il messaggio va al Parking Lot, non al DLQ loop."""


# ─── Logica business ──────────────────────────────────────────────────────────

def elabora_ordine(payload: dict) -> dict:
    """
    Logica business — solleva eccezioni appropriate.
    
    CRITICO: classificare correttamente gli errori:
    - TransitorioError per problemi infrastrutturali temporanei
    - PermanenteError per dati invalidi o logica non recuperabile
    """
    import random
    
    # Validazione dati (sempre PermanenteError — non ha senso ritentare)
    if not payload.get("ordine_id"):
        raise PermanenteError("ordine_id mancante nel payload")
    if payload.get("importo", 0) <= 0:
        raise PermanenteError(f"importo invalido: {payload.get('importo')}")
    
    # Simula errore transitorio (30% probabilità)
    if random.random() < 0.3:
        raise TransitorioError("Database temporaneamente non raggiungibile")
    
    # Simula elaborazione reale
    return {
        "ordine_id": payload["ordine_id"],
        "stato": "elaborato",
        "transaction_id": f"TXN-{payload['ordine_id'][-6:]}",
    }


def estrai_delivery_count(message: aio_pika.abc.AbstractIncomingMessage) -> int:
    """
    Conta quante volte il messaggio è già stato rigettato.
    
    RabbitMQ aggiunge header x-death ogni volta che un messaggio passa per DLX.
    Struttura: lista di oggetti {count, reason, queue, exchange, time}
    """
    x_death = message.headers.get("x-death")
    if not x_death:
        return 0
    # x-death è una lista — somma i contatori (può passare per DLX più volte)
    if isinstance(x_death, list):
        return sum(entry.get("count", 1) for entry in x_death)
    return 1


async def parcheggia_messaggio(
    channel: aio_pika.abc.AbstractChannel,
    messaggio_originale: aio_pika.abc.AbstractIncomingMessage,
    motivo: str,
) -> None:
    """
    Manda un messaggio al Parking Lot con metadati di debug.
    Usato per errori permanenti o messaggi che hanno esaurito i retry.
    """
    payload_originale = json.loads(messaggio_originale.body)
    
    parking_payload = {
        "payload_originale": payload_originale,
        "motivo_parking": motivo,
        "routing_key_originale": messaggio_originale.routing_key,
        "timestamp_parcheggio": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "x_death_count": estrai_delivery_count(messaggio_originale),
    }
    
    exchange_default = await channel.get_exchange("")
    await exchange_default.publish(
        aio_pika.Message(
            body=json.dumps(parking_payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        ),
        routing_key=QUEUE_PARKING_LOT,
    )
    logger.warning(
        "Messaggio parcheggiato: ordine=%s motivo=%s",
        payload_originale.get("ordine_id", "?"), motivo
    )


# ─── Message handler ─────────────────────────────────────────────────────────

async def on_message(
    messaggio: aio_pika.abc.AbstractIncomingMessage,
    channel: aio_pika.abc.AbstractChannel,
) -> None:
    """
    Handler principale messaggi.
    
    Strategia ACK/NACK:
    - Successo:              ack() — RabbitMQ rimuove il messaggio
    - Errore transitorio
      + sotto soglia retry:  nack(requeue=True) — rimesso in coda
    - Errore transitorio
      + sopra soglia retry:  nack(requeue=False) → DLX → DLQ
    - Errore permanente:     nack(requeue=False) + park → Parking Lot
    """
    async with messaggio.process(requeue=False):  # requeue=False nel context manager default
        try:
            payload = json.loads(messaggio.body)
            delivery_count = estrai_delivery_count(messaggio)
            
            logger.info(
                "Processing messaggio: ordine=%s delivery_count=%d",
                payload.get("ordine_id", "?"), delivery_count
            )
            
            # Controlla se ha già superato il limite di retry
            if delivery_count >= MAX_DELIVERY_COUNT:
                await parcheggia_messaggio(
                    channel, messaggio,
                    f"Superati {MAX_DELIVERY_COUNT} tentativi"
                )
                # ack per rimuoverlo dalla DLQ (già parcheggiato)
                return
            
            try:
                result = elabora_ordine(payload)
                logger.info(
                    "Ordine elaborato: %s → %s",
                    payload.get("ordine_id"), result.get("transaction_id")
                )
                # ACK implicito nel context manager (nessun raise = successo)
            
            except TransitorioError as e:
                logger.warning(
                    "Errore transitorio (delivery %d/%d): %s",
                    delivery_count + 1, MAX_DELIVERY_COUNT, e
                )
                # NACK con requeue → torna in coda per retry
                await messaggio.nack(requeue=True)
                return  # Non fare ack
            
            except PermanenteError as e:
                logger.error(
                    "Errore permanente (no retry): %s — %s",
                    payload.get("ordine_id", "?"), e
                )
                # Park prima di nack
                await parcheggia_messaggio(channel, messaggio, str(e))
                # NACK senza requeue → va in DLQ (e poi noi l'abbiamo già parcheggiato)
                await messaggio.nack(requeue=False)
                return
        
        except json.JSONDecodeError as e:
            logger.error("Payload non valido (JSON): %s", e)
            await messaggio.nack(requeue=False)


# ─── Worker main ─────────────────────────────────────────────────────────────

async def run_worker(url: str, queue_name: str) -> None:
    """Esegue il consumer finché non riceve SIGTERM/SIGINT."""
    stop = asyncio.Event()
    loop = asyncio.get_event_loop()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    
    logger.info("Connessione a RabbitMQ: %s", url)
    
    async with await aio_pika.connect_robust(url) as conn:
        # Setup topology (idempotente)
        await setup_topology(conn)
        
        async with conn.channel() as channel:
            await channel.set_qos(prefetch_count=1)
            queue = await channel.declare_queue(queue_name, passive=True)
            
            logger.info("Worker pronto — in ascolto su '%s'", queue_name)
            
            async def handler(msg):
                await on_message(msg, channel)
            
            await queue.consume(handler)
            await stop.wait()
    
    logger.info("Worker fermato")


if __name__ == "__main__":
    from topology.setup_topology import QUEUE_PROCESSING
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    url = os.environ.get("RABBITMQ_URL", "amqp://admin:rabbitlab@localhost/")
    asyncio.run(run_worker(url, QUEUE_PROCESSING))
```

---

## PART C — Replay Tool CLI

### C1 — CLI per Replay Messaggi dalla DLQ

```python
#!/usr/bin/env python3
# file: replay_tool/dlq_tool.py
"""
CLI tool per gestione messaggi in DLQ e Parking Lot.

Comandi:
  dlq-tool list            → lista messaggi in DLQ/Parking Lot
  dlq-tool replay          → reinvia messaggi nel queue principale
  dlq-tool replay --filter ordine_id=ORD-001  → reinvia solo match
  dlq-tool purge           → cancella messaggi vecchi
  dlq-tool inspect <id>    → ispeziona singolo messaggio

Usa l'API HTTP di RabbitMQ (porta 15672) per leggere messaggi senza consumarli.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Optional

import aio_pika
import click
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
import httpx

console = Console()

RABBITMQ_API = os.environ.get("RABBITMQ_API", "http://localhost:15672")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS", "rabbitlab")
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://admin:rabbitlab@localhost/")


# ─── API Helper ───────────────────────────────────────────────────────────────

def api_get(path: str) -> dict:
    """Chiama RabbitMQ Management API."""
    with httpx.Client(base_url=RABBITMQ_API, auth=(RABBITMQ_USER, RABBITMQ_PASS)) as client:
        r = client.get(path)
        r.raise_for_status()
        return r.json()


def api_get_messages(queue: str, count: int = 100, requeue: bool = True) -> list[dict]:
    """
    Legge messaggi dalla coda senza consumarli definitivamente.
    requeue=True: messaggi restano in coda (safe per ispezione)
    requeue=False: messaggi vengono rimossi (per consume)
    """
    with httpx.Client(base_url=RABBITMQ_API, auth=(RABBITMQ_USER, RABBITMQ_PASS)) as client:
        r = client.post(
            f"/api/queues/%2F/{queue}/get",
            json={
                "count": count,
                "ackmode": "ack_requeue_true" if requeue else "ack_requeue_false",
                "encoding": "auto",
                "truncate": 50000,
            }
        )
        r.raise_for_status()
        return r.json()


# ─── CLI Commands ─────────────────────────────────────────────────────────────

@click.group()
@click.option("--queue", "-q", default="ordini.dlq", help="Nome della coda DLQ")
@click.pass_context
def cli(ctx, queue):
    """DLQ Tool — gestione messaggi Dead Letter Queue."""
    ctx.ensure_object(dict)
    ctx.obj["queue"] = queue


@cli.command()
@click.option("--limit", "-n", default=50, help="Numero max messaggi da mostrare")
@click.pass_context
def lista(ctx, limit):
    """Lista messaggi presenti nella DLQ."""
    queue = ctx.obj["queue"]
    
    try:
        # Info coda
        info = api_get(f"/api/queues/%2F/{queue}")
        console.print(f"\n[bold]Coda:[/bold] {queue}")
        console.print(f"[bold]Messaggi totali:[/bold] {info.get('messages', 0)}")
        console.print(f"[bold]Messaggi pronti:[/bold] {info.get('messages_ready', 0)}")
        
        messages = api_get_messages(queue, count=limit, requeue=True)
        
        if not messages:
            console.print("[yellow]Nessun messaggio in DLQ[/yellow]")
            return
        
        table = Table(title=f"Messaggi in {queue} (ultimi {min(limit, len(messages))})")
        table.add_column("Routing Key", style="cyan")
        table.add_column("Motivo", style="red")
        table.add_column("Retry Count", style="yellow", justify="right")
        table.add_column("Payload Preview", style="white")
        
        for msg in messages[:limit]:
            body_str = msg.get("payload", "")
            try:
                body = json.loads(body_str)
                preview = json.dumps(body, ensure_ascii=False)[:60] + "..."
            except json.JSONDecodeError:
                preview = body_str[:60] + "..."
            
            # Estrai x-death info
            headers = msg.get("properties", {}).get("headers", {})
            x_death = headers.get("x-death", [])
            motivo = x_death[0].get("reason", "sconosciuto") if x_death else "sconosciuto"
            retry_count = sum(d.get("count", 1) for d in x_death) if x_death else 0
            
            table.add_row(
                msg.get("routing_key", ""),
                motivo,
                str(retry_count),
                preview,
            )
        
        console.print(table)
    
    except httpx.HTTPError as e:
        console.print(f"[red]Errore API: {e}[/red]")
        raise click.Abort()


@cli.command()
@click.option("--filtro-ordine", help="Filtra per ordine_id specifico")
@click.option("--filtro-motivo", help="Filtra per motivo (rejected/expired/maxlen)")
@click.option("--dry-run", is_flag=True, help="Simula senza reinviare")
@click.option("--max", "max_msgs", default=100, help="Max messaggi da replayare")
@click.option("--target-exchange", default="ordini", help="Exchange destinazione")
@click.option("--target-key", default="ordini.nuovo", help="Routing key destinazione")
@click.pass_context
def replay(ctx, filtro_ordine, filtro_motivo, dry_run, max_msgs, target_exchange, target_key):
    """Reinvia messaggi dalla DLQ al queue principale."""
    queue = ctx.obj["queue"]
    
    if dry_run:
        console.print("[yellow]DRY RUN — nessun messaggio sarà reinviato[/yellow]")
    
    async def _replay():
        messages = api_get_messages(queue, count=max_msgs, requeue=not dry_run)
        
        replayati = 0
        saltati = 0
        errori = 0
        
        if dry_run:
            # In dry-run: ri-accodiamo (non consumiamo)
            messages = api_get_messages(queue, count=max_msgs, requeue=True)
        else:
            messages = api_get_messages(queue, count=max_msgs, requeue=False)
        
        async with await aio_pika.connect_robust(RABBITMQ_URL) as conn:
            async with conn.channel() as channel:
                exchange = await channel.declare_exchange(
                    target_exchange,
                    passive=True,  # Non crea — fallisce se non esiste
                )
                
                for msg in messages:
                    try:
                        body_str = msg.get("payload", "")
                        body = json.loads(body_str)
                        
                        # Filtri
                        if filtro_ordine and body.get("ordine_id") != filtro_ordine:
                            saltati += 1
                            continue
                        
                        headers = msg.get("properties", {}).get("headers", {})
                        x_death = headers.get("x-death", [])
                        motivo = x_death[0].get("reason", "") if x_death else ""
                        if filtro_motivo and motivo != filtro_motivo:
                            saltati += 1
                            continue
                        
                        if dry_run:
                            console.print(f"  [DRY] Replayerei: {body.get('ordine_id', '?')}")
                            replayati += 1
                            continue
                        
                        # Aggiungi header replay per tracciabilità
                        body["_replay"] = {
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "from_queue": queue,
                        }
                        
                        await exchange.publish(
                            aio_pika.Message(
                                body=json.dumps(body).encode(),
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                                content_type="application/json",
                            ),
                            routing_key=target_key,
                        )
                        replayati += 1
                        console.print(f"  ✓ Replayato: {body.get('ordine_id', '?')}")
                    
                    except Exception as e:
                        errori += 1
                        console.print(f"  [red]✗ Errore: {e}[/red]")
        
        console.print(f"\n[bold]Risultato:[/bold] {replayati} replayati, "
                      f"{saltati} saltati, {errori} errori")
    
    asyncio.run(_replay())


@cli.command()
@click.option("--eta-giorni", default=7, help="Cancella messaggi più vecchi di N giorni")
@click.option("--dry-run", is_flag=True, help="Simula senza cancellare")
@click.pass_context
def purge(ctx, eta_giorni, dry_run):
    """Cancella messaggi vecchi dalla DLQ (archiviati/obsoleti)."""
    queue = ctx.obj["queue"]
    
    if dry_run:
        console.print(f"[yellow]DRY RUN — simulazione purge messaggi > {eta_giorni}gg[/yellow]")
    
    # Leggi tutti i messaggi
    messages = api_get_messages(queue, count=10000, requeue=True)
    cutoff = time.time() - (eta_giorni * 86400)
    
    da_cancellare = 0
    for msg in messages:
        # Timestamp dalla proprietà timestamp o dai header x-death
        headers = msg.get("properties", {}).get("headers", {})
        x_death = headers.get("x-death", [{}])
        ts = x_death[0].get("time", time.time()) if x_death else time.time()
        if ts < cutoff:
            da_cancellare += 1
    
    if dry_run:
        console.print(f"  Messaggi da cancellare: {da_cancellare} (> {eta_giorni} giorni)")
        console.print(f"  Messaggi rimanenti: {len(messages) - da_cancellare}")
    else:
        console.print(f"[red]PURGE non ancora implementata — usa dry-run per vedere l'impatto[/red]")
        console.print("Per produzione: implementa cancellazione selettiva per timestamp")


if __name__ == "__main__":
    cli(obj={})
```

---

## PART D — Monitoring DLQ

### D1 — Prometheus Alert per DLQ

```python
#!/usr/bin/env python3
# file: monitoring/dlq_exporter.py
"""
Prometheus exporter per metriche DLQ.
Espone su :9101/metrics le metriche per Grafana alert.
"""
from __future__ import annotations

import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import httpx

RABBITMQ_API = os.environ.get("RABBITMQ_API", "http://localhost:15672")
AUTH = (
    os.environ.get("RABBITMQ_USER", "admin"),
    os.environ.get("RABBITMQ_PASS", "rabbitlab"),
)
QUEUES_DA_MONITORARE = ["ordini.dlq", "ordini.parking_lot", "ordini.processing"]


def fetch_queue_metrics() -> str:
    """Genera metriche Prometheus per le code monitorate."""
    metriche = []
    metriche.append("# HELP rabbitmq_queue_messages Messaggi in coda")
    metriche.append("# TYPE rabbitmq_queue_messages gauge")
    
    with httpx.Client(base_url=RABBITMQ_API, auth=AUTH) as client:
        for queue_name in QUEUES_DA_MONITORARE:
            try:
                r = client.get(f"/api/queues/%2F/{queue_name}", timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    msgs = data.get("messages", 0)
                    ready = data.get("messages_ready", 0)
                    unacked = data.get("messages_unacknowledged", 0)
                    rate = data.get("message_stats", {}).get("ack_details", {}).get("rate", 0)
                    
                    labels = f'queue="{queue_name}"'
                    metriche.append(f'rabbitmq_queue_messages{{{labels}}} {msgs}')
                    metriche.append(f'rabbitmq_queue_messages_ready{{{labels}}} {ready}')
                    metriche.append(f'rabbitmq_queue_messages_unacked{{{labels}}} {unacked}')
                    metriche.append(f'rabbitmq_queue_ack_rate{{{labels}}} {rate}')
            except Exception as e:
                metriche.append(f'# Error fetching {queue_name}: {e}')
    
    metriche.append(f"rabbitmq_exporter_scrape_time_seconds {time.time()}")
    return "\n".join(metriche) + "\n"


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            body = fetch_queue_metrics().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, *args):
        pass  # Silenzia i log HTTP del server


PROMETHEUS_ALERT_RULES = """
# file: alerting/dlq_alerts.yml
# Da aggiungere alla configurazione Prometheus

groups:
  - name: dlq_alerts
    rules:
      - alert: DLQMessaggiAltaMessa
        expr: rabbitmq_queue_messages{queue="ordini.dlq"} > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "DLQ ordini ha {{ $value }} messaggi"
          description: >
            La DLQ ordini.dlq contiene {{ $value }} messaggi.
            Verificare se ci sono errori sistemici nel consumer.
      
      - alert: DLQMessaggiCritici
        expr: rabbitmq_queue_messages{queue="ordini.dlq"} > 1000
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "DLQ CRITICA: {{ $value }} messaggi non processati"
          runbook_url: "https://wiki.interno/runbook/dlq-critica"
      
      - alert: ParkingLotInCrescita
        expr: rate(rabbitmq_queue_messages{queue="ordini.parking_lot"}[10m]) > 0
        labels:
          severity: warning
        annotations:
          summary: "Parking lot in crescita — errori permanenti in corso"
"""

if __name__ == "__main__":
    port = int(os.environ.get("EXPORTER_PORT", "9101"))
    server = HTTPServer(("0.0.0.0", port), MetricsHandler)
    print(f"DLQ Exporter su :{port}/metrics")
    print(f"Monitorando: {', '.join(QUEUES_DA_MONITORARE)}")
    print(PROMETHEUS_ALERT_RULES)
    server.serve_forever()
```

---

## Esercizi

### Esercizio 1 — Configura la Topology e Invia Messaggi (20 min)

```bash
# 1. Avvia RabbitMQ
docker compose -f docker-compose-dlq.yml up -d

# 2. Configura topology
python topology/setup_topology.py

# 3. Produci messaggi di test
python -c "
import asyncio, aio_pika, json, os

async def produce():
    url = 'amqp://admin:rabbitlab@localhost/'
    async with await aio_pika.connect_robust(url) as conn:
        async with conn.channel() as ch:
            ex = await ch.declare_exchange('ordini', passive=True)
            for i in range(10):
                msg = {'ordine_id': f'ORD-{i:03d}', 'importo': i * 10.0, 'valuta': 'EUR'}
                await ex.publish(
                    aio_pika.Message(json.dumps(msg).encode(), delivery_mode=2),
                    routing_key='ordini.nuovo'
                )
                print(f'Inviato ORD-{i:03d}')
asyncio.run(produce())
"

# 4. Avvia consumer
python consumer/worker.py &

# 5. Ispeziona DLQ dopo qualche secondo
python replay_tool/dlq_tool.py lista
```

### Esercizio 2 — Replay Selettivo (20 min)

```bash
# Invia un messaggio con errore permanente intenzionale
python -c "
import asyncio, aio_pika, json

async def produce():
    url = 'amqp://admin:rabbitlab@localhost/'
    async with await aio_pika.connect_robust(url) as conn:
        async with conn.channel() as ch:
            ex = await ch.declare_exchange('ordini', passive=True)
            # Messaggio senza ordine_id → errore permanente → parking lot
            msg = {'importo': 50.0}
            await ex.publish(
                aio_pika.Message(json.dumps(msg).encode(), delivery_mode=2),
                routing_key='ordini.nuovo'
            )
asyncio.run(produce())
"

# Verifica che sia nel parking lot
python replay_tool/dlq_tool.py -q ordini.parking_lot lista

# Replay messaggio in DLQ con dry-run prima
python replay_tool/dlq_tool.py replay --dry-run
python replay_tool/dlq_tool.py replay --filtro-motivo rejected
```

### Esercizio 3 — Alert Prometheus (15 min)

Configura `dlq_exporter.py` per esporre le metriche e verifica in Prometheus:
```bash
python monitoring/dlq_exporter.py &
curl http://localhost:9101/metrics | grep dlq
```

---

## Riferimenti

- RabbitMQ Dead Letter: https://www.rabbitmq.com/dlx.html
- aio-pika docs: https://aio-pika.readthedocs.io/
- Enterprise Messaging Patterns: Gregor Hohpe & Bobby Woolf
- Modulo sorgente: `22-dlq-parking-lot-pattern.md`
