# Tutorial Lab — Architettura Event-Driven: RabbitMQ, Kafka e Pattern Avanzati

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `16-event-driven-architecture-pratica.md`
> **Livello:** competent → proficient
> **Tempo stimato:** 6-8 ore (lab completo)
> **Prerequisiti:** Docker Compose, Python 3.11+, concetti messaging (queue, topic, consumer)
> **Versioni di riferimento:** RabbitMQ 3.13 · Apache Kafka 3.7 · Python 3.11+ · pika 1.3 · confluent-kafka 2.4

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Scegliere tra RabbitMQ e Kafka in base al caso d'uso (task queue vs event log)
2. Configurare RabbitMQ con exchange topic, DLQ, quorum queues e manual ack
3. Produrre e consumare messaggi Kafka con consumer groups e commit manuale degli offset
4. Implementare il pattern Outbox per garantire atomicità DB + evento
5. Progettare il pattern Saga per transazioni distribuite con compensation actions
6. Monitorare throughput, consumer lag e dead-letter con Prometheus + Grafana

---

## Lab Environment Setup

```yaml
# docker-compose.yml
version: "3.8"
services:
  # ── RabbitMQ ──────────────────────────────────────────────────────────────
  rabbitmq:
    image: rabbitmq:3.13-management-alpine
    container_name: rabbitmq
    restart: unless-stopped
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: rabbit_admin_password
      RABBITMQ_DEFAULT_VHOST: /
    ports:
      - "5672:5672"     # AMQP
      - "15672:15672"   # Management UI
      - "15692:15692"   # Prometheus metrics
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 15s
      timeout: 10s
      retries: 5

  # ── Apache Kafka (KRaft mode — senza Zookeeper) ──────────────────────────
  kafka:
    image: confluentinc/cp-kafka:7.7.0
    container_name: kafka
    restart: unless-stopped
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_DEFAULT_REPLICATION_FACTOR: 1
      KAFKA_MIN_IN_SYNC_REPLICAS: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "false"
      KAFKA_LOG_RETENTION_HOURS: 168      # 7 giorni
      KAFKA_LOG_SEGMENT_BYTES: 104857600  # 100MB per segment
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"
    ports:
      - "9092:9092"
    volumes:
      - kafka_data:/var/lib/kafka/data
    healthcheck:
      test: ["CMD-SHELL", "kafka-broker-api-versions --bootstrap-server localhost:9092"]
      interval: 20s
      timeout: 10s
      retries: 5

  # ── Kafka UI ─────────────────────────────────────────────────────────────
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kafka-ui
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
    depends_on:
      - kafka

  # ── PostgreSQL (per pattern Outbox) ───────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    container_name: postgres-events
    environment:
      POSTGRES_DB: orders_db
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  rabbitmq_data:
  kafka_data:
  postgres_data:
```

```bash
# Avvia infrastruttura
docker compose up -d

# Attendi che tutti i servizi siano healthy
docker compose ps

# Installa librerie Python
pip install pika==1.3.2 confluent-kafka==2.4.0 psycopg2-binary==2.9.9 \
            structlog==24.0.0 httpx==0.27.0

# Verifica RabbitMQ
curl -u admin:rabbit_admin_password http://localhost:15672/api/healthchecks/node
# Output: {"status":"ok"}

# Verifica Kafka
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 | head -5

# Crea topic Kafka necessari per il lab
docker exec kafka kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --topic orders.placed \
    --partitions 3 \
    --replication-factor 1

docker exec kafka kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --topic orders.placed.dlq \
    --partitions 1 \
    --replication-factor 1

docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

---

## Analogia Introduttiva

> **RabbitMQ è come un ufficio postale**:
> i pacchi (messaggi) vengono smistati dallo smistatore (exchange)
> in base all'indirizzo (routing key) e messi in casellari specifici (queue).
> Il postino (consumer) svuota il casellario, firma la ricevuta (ack),
> e se non può consegnare manda il pacco allo scomparto falliti (DLQ).
>
> **Kafka è come una rotativa di giornale**:
> ogni edizione (evento) viene pubblicata su una striscia di carta (log append-only)
> divisa in sezioni (partizioni). I lettori (consumer) leggono dalla striscia
> al loro ritmo (offset), segnando a quale numero di pagina sono arrivati.
> Il giornale esiste per 7 giorni (retention), anche dopo essere stato letto —
> puoi sempre tornare indietro e rileggere.

---

## Architettura del Lab

```
ARCHITETTURA LAB EVENT-DRIVEN:

   Producer       RabbitMQ                     Consumer
   ─────────     ──────────────────────────    ─────────────
   [App]────▶    Exchange "orders" (topic)
                     │
              routing_key: order.placed.italy.*
                     │
                     ▼
               Queue: orders.italy.processing
                     │         │ (reject/TTL)
                     │         ▼
               [Worker 1]  DLX Exchange "orders.dlx"
               [Worker 2]       │
               [Worker 3]       ▼
                           Queue: orders.italy.failed
                                │
                                ▼
                          [DLQ Inspector]


   Producer       Apache Kafka                 Consumer Group
   ─────────     ──────────────────────────    ─────────────
   [App]────▶    Topic: orders.placed (3 partitions)
                  │           │           │
                [P0]        [P1]        [P2]
                  │           │           │
              [Worker A]  [Worker B]  [Worker C]
```

---

## PART A — RabbitMQ: Exchange, Queue, DLQ

### A1 — Setup Topologia (Producer)

```python
#!/usr/bin/env python3
# file: rabbitmq_setup.py
"""
Crea tutta la topologia RabbitMQ necessaria per il lab:
- Exchange principale "orders" (topic)
- DLX exchange "orders.dlx"
- Queue con DLQ configurata
- Queue dead-letter
"""
import json
import time
from typing import Any

import pika
import structlog

logging = structlog.get_logger(__name__)

RABBITMQ_URL = "amqp://admin:rabbit_admin_password@localhost:5672/"


def setup_topology(channel: pika.channel.Channel) -> None:
    """Dichiara tutta la topologia in maniera idempotente."""

    # 1. Exchange principale (topic per routing flessibile)
    channel.exchange_declare(
        exchange="orders",
        exchange_type="topic",
        durable=True,
    )
    logging.info("exchange_declared", exchange="orders")

    # 2. DLX (Dead-Letter Exchange) per messaggi falliti
    channel.exchange_declare(
        exchange="orders.dlx",
        exchange_type="topic",
        durable=True,
    )
    logging.info("dlx_declared", exchange="orders.dlx")

    # 3. Queue principale per ordini italiani
    channel.queue_declare(
        queue="orders.italy.processing",
        durable=True,
        arguments={
            # DLX: messaggi rejected/TTL → orders.dlx
            "x-dead-letter-exchange": "orders.dlx",
            "x-dead-letter-routing-key": "orders.italy.failed",
            # TTL: messaggi non consumati dopo 24h vanno in DLQ
            "x-message-ttl": 86400000,  # 24 ore in ms
            # Limite dimensione (backpressure)
            "x-max-length": 100000,
            "x-overflow": "reject-publish",
            # Quorum queue (HA) — richiede cluster RabbitMQ
            # "x-queue-type": "quorum",
        },
    )

    # 4. Binding: orders exchange → queue (pattern topic)
    channel.queue_bind(
        queue="orders.italy.processing",
        exchange="orders",
        routing_key="order.placed.italy.#",  # matcha: order.placed.italy.b2b, order.placed.italy.b2c, ecc.
    )

    # 5. Dead-Letter Queue
    channel.queue_declare(
        queue="orders.italy.failed",
        durable=True,
        arguments={"x-message-ttl": 2592000000},  # 30 giorni in DLQ
    )
    channel.queue_bind(
        queue="orders.italy.failed",
        exchange="orders.dlx",
        routing_key="orders.italy.failed",
    )

    logging.info("topology_ready", queues=["orders.italy.processing", "orders.italy.failed"])


def get_channel() -> tuple[pika.BlockingConnection, pika.channel.Channel]:
    """Crea connessione e canale RabbitMQ con retry."""
    for attempt in range(5):
        try:
            conn = pika.BlockingConnection(
                pika.URLParameters(RABBITMQ_URL)
            )
            channel = conn.channel()
            channel.confirm_delivery()  # Publisher confirms
            return conn, channel
        except pika.exceptions.AMQPConnectionError:
            if attempt == 4:
                raise
            logging.warning("rabbitmq_not_ready", attempt=attempt + 1)
            time.sleep(5)
    raise RuntimeError("Impossibile connettersi a RabbitMQ")


if __name__ == "__main__":
    conn, channel = get_channel()
    try:
        setup_topology(channel)
        print("Topologia RabbitMQ configurata con successo")
    finally:
        conn.close()
```

### A2 — Producer con Publisher Confirms

```python
#!/usr/bin/env python3
# file: rabbitmq_producer.py
"""
Producer RabbitMQ con:
- Publisher confirms (garanzia consegna al broker)
- Messaggi persistent (delivery_mode=2)
- Routing key basata su contesto ordine
"""
import json
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Optional

import pika
import pika.exceptions
import structlog

from rabbitmq_setup import get_channel, setup_topology

logger = structlog.get_logger(__name__)


@dataclass
class Ordine:
    ordine_id: str
    cliente_id: str
    paese: str       # "italy", "germany", ecc.
    canale: str      # "b2b", "b2c"
    totale_eur: float
    items: list[dict]
    occurred_at: str


def pubblica_ordine(channel: pika.channel.Channel, ordine: Ordine) -> bool:
    """
    Pubblica un ordine sull'exchange RabbitMQ.
    Routing key: order.placed.<paese>.<canale>
    """
    routing_key = f"order.placed.{ordine.paese}.{ordine.canale}"
    event = {
        "type": "OrderPlaced",
        **asdict(ordine),
        "schema_version": "1",
    }

    log = logger.bind(
        ordine_id=ordine.ordine_id,
        routing_key=routing_key,
    )

    try:
        channel.basic_publish(
            exchange="orders",
            routing_key=routing_key,
            body=json.dumps(event).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,                    # persistent
                content_type="application/json",
                message_id=str(uuid.uuid4()),
                timestamp=int(time.time()),
                headers={
                    "schema_version": "1",
                    "correlation_id": ordine.ordine_id,
                },
            ),
            mandatory=True,
        )
        log.info("order_published")
        return True
    except pika.exceptions.UnroutableError:
        log.error("message_unroutable", hint="Nessuna queue legata a questa routing key")
        return False
    except pika.exceptions.NackError:
        log.error("message_nacked", hint="Broker ha rifiutato il messaggio (disco pieno?)")
        return False


if __name__ == "__main__":
    conn, channel = get_channel()
    try:
        setup_topology(channel)

        # Pubblica 10 ordini di test
        for i in range(10):
            ordine = Ordine(
                ordine_id=f"ORD-2026-{i:04d}",
                cliente_id=f"CUST-{i + 100}",
                paese="italy",
                canale="b2b" if i % 2 == 0 else "b2c",
                totale_eur=round(50 + i * 23.5, 2),
                items=[{"sku": f"SKU-{i}", "qty": i + 1}],
                occurred_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
            success = pubblica_ordine(channel, ordine)
            print(f"Ordine {ordine.ordine_id}: {'OK' if success else 'FALLITO'}")
    finally:
        conn.close()
```

### A3 — Consumer con Manual Ack e DLQ

```python
#!/usr/bin/env python3
# file: rabbitmq_consumer.py
"""
Consumer RabbitMQ con:
- Manual acknowledgement (non auto-ack)
- Prefetch count per backpressure
- Retry contatore (header x-death)
- Invio in DLQ dopo N retry
"""
import json
import random
import time

import pika
import structlog

from rabbitmq_setup import get_channel

logger = structlog.get_logger(__name__)

MAX_RETRY_COUNT = 3
PREFETCH_COUNT = 10


class TransientError(Exception):
    """Errore temporaneo — merita retry."""

class PermanentError(Exception):
    """Errore definitivo — va in DLQ immediatamente."""


def get_retry_count(properties: pika.BasicProperties) -> int:
    """Conta quante volte il messaggio è già stato rifiutato (x-death header)."""
    x_death = (properties.headers or {}).get("x-death", [])
    if not x_death:
        return 0
    return sum(entry.get("count", 0) for entry in x_death)


def processa_ordine(body: bytes, properties: pika.BasicProperties) -> None:
    """
    Elabora un ordine.
    Simula errori casuali per testare il meccanismo DLQ.
    """
    event = json.loads(body)
    ordine_id = event.get("ordine_id", "unknown")
    log = logger.bind(ordine_id=ordine_id)

    log.info("processing_order")

    # Simula errori per il lab
    roll = random.random()
    if roll < 0.1:
        raise PermanentError("Formato ordine non valido — schema non supportato")
    elif roll < 0.25:
        raise TransientError("Servizio downstream temporaneamente non disponibile")

    # Processing fittizio (100-500ms)
    time.sleep(random.uniform(0.1, 0.5))
    log.info("order_processed_ok", totale_eur=event.get("totale_eur"))


def on_message(
    channel: pika.channel.Channel,
    method: pika.spec.Basic.Deliver,
    properties: pika.BasicProperties,
    body: bytes,
) -> None:
    """Callback per ogni messaggio ricevuto dalla queue."""
    retry_count = get_retry_count(properties)
    log = logger.bind(
        delivery_tag=method.delivery_tag,
        retry_count=retry_count,
        routing_key=method.routing_key,
    )

    try:
        processa_ordine(body, properties)
        # ACK: messaggio elaborato con successo — rimosso dalla queue
        channel.basic_ack(delivery_tag=method.delivery_tag)
        log.info("message_acked")

    except TransientError as e:
        log.warning("transient_error", error=str(e), retry=retry_count)
        if retry_count < MAX_RETRY_COUNT:
            # NACK con requeue=True → rimesso in coda per retry
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        else:
            # Superato MAX_RETRY → NACK senza requeue → va in DLX/DLQ
            log.error("max_retry_exceeded_sending_to_dlq", error=str(e))
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except PermanentError as e:
        # NACK senza requeue → DLQ immediata
        log.error("permanent_error_sending_to_dlq", error=str(e))
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except Exception as e:
        # Errore non gestito → DLQ (evita loop infinito)
        log.exception("unexpected_error_sending_to_dlq", error=str(e))
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def avvia_consumer() -> None:
    """Avvia consumer bloccante."""
    conn, channel = get_channel()

    # Limita a N messaggi in-flight (backpressure)
    channel.basic_qos(prefetch_count=PREFETCH_COUNT)

    channel.basic_consume(
        queue="orders.italy.processing",
        on_message_callback=on_message,
        auto_ack=False,  # CRITICO: manual ack
    )

    logger.info("consumer_started", queue="orders.italy.processing", prefetch=PREFETCH_COUNT)
    print("Consumer avviato. Premi Ctrl+C per fermare.")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        conn.close()
        logger.info("consumer_stopped")


if __name__ == "__main__":
    avvia_consumer()
```

---

## PART B — Apache Kafka

### B1 — Producer Kafka con Idempotenza

```python
#!/usr/bin/env python3
# file: kafka_producer.py
"""
Producer Kafka production-grade:
- acks=all (garanzia durabilità)
- enable.idempotence=True (exactly-once semantics sul broker)
- Compressione lz4
- Partitioning per customer_id (ordering garantito per cliente)
"""
import json
import time
import uuid

import structlog
from confluent_kafka import Producer

logger = structlog.get_logger(__name__)

KAFKA_CONFIG = {
    "bootstrap.servers": "localhost:9092",
    "acks": "all",                  # Aspetta conferma da tutti gli ISR
    "enable.idempotence": True,     # Idempotenza producer (no duplicati su retry)
    "compression.type": "lz4",      # Compressione efficiente
    "linger.ms": 20,                # Batch window: aspetta 20ms per raggruppare messaggi
    "batch.size": 65536,            # Max batch: 64KB
    "retries": 2147483647,          # Retry infiniti (con backoff)
    "max.in.flight.requests.per.connection": 5,
}


def delivery_callback(err, msg) -> None:
    """Callback chiamata per ogni messaggio — successo o errore."""
    if err:
        logger.error("delivery_failed",
                     error=str(err),
                     topic=msg.topic())
    else:
        logger.debug("delivery_ok",
                     topic=msg.topic(),
                     partition=msg.partition(),
                     offset=msg.offset())


class OrdiniProducer:
    def __init__(self):
        self.producer = Producer(KAFKA_CONFIG)

    def pubblica_ordine_piazzato(self, ordine: dict) -> None:
        """
        Pubblica evento OrderPlaced su Kafka.
        Key = customer_id → garantisce ordering per cliente sulla stessa partizione.
        """
        event = {
            "type": "OrderPlaced",
            "event_id": str(uuid.uuid4()),
            "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            **ordine,
        }

        self.producer.produce(
            topic="orders.placed",
            key=ordine["customer_id"].encode("utf-8"),   # Partitioning key
            value=json.dumps(event).encode("utf-8"),
            headers={
                "schema_version": "1",
                "content_type": "application/json",
            },
            callback=delivery_callback,
        )
        # Poll per svuotare delivery callback queue (non blocca)
        self.producer.poll(0)
        logger.info("event_queued", order_id=ordine.get("order_id"))

    def flush(self, timeout: float = 10.0) -> int:
        """Flush tutti i messaggi pendenti. Ritorna numero messaggi non consegnati."""
        remaining = self.producer.flush(timeout)
        if remaining > 0:
            logger.error("producer_flush_incomplete", remaining=remaining)
        return remaining

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.flush()


if __name__ == "__main__":
    with OrdiniProducer() as producer:
        for i in range(50):
            customer_id = f"CUST-{(i % 10) + 1:03d}"  # 10 clienti diversi
            producer.pubblica_ordine_piazzato({
                "order_id": f"ORD-2026-{i:04d}",
                "customer_id": customer_id,
                "total_eur": round(29.99 + i * 15.5, 2),
                "items_count": (i % 5) + 1,
            })
        print(f"Pubblicati 50 ordini")
```

### B2 — Consumer Kafka con Commit Manuale

```python
#!/usr/bin/env python3
# file: kafka_consumer.py
"""
Consumer Kafka production-grade:
- Consumer group per load balancing automatico tra partizioni
- Commit manuale degli offset (no auto-commit che può perdere messaggi)
- Error handling con invio a DLQ
- Graceful shutdown su SIGTERM
"""
import json
import signal
import time
from typing import Optional

import structlog
from confluent_kafka import Consumer, KafkaError, KafkaException, Producer

logger = structlog.get_logger(__name__)

CONSUMER_CONFIG = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "orders-processor-v1",
    "auto.offset.reset": "earliest",   # Leggi dall'inizio se nessun offset committato
    "enable.auto.commit": False,        # CRITICO: commit manuale
    "max.poll.interval.ms": 300000,     # 5 minuti max tra poll (per job lunghi)
    "session.timeout.ms": 45000,        # 45s prima che broker consideri consumer morto
    "heartbeat.interval.ms": 3000,
}

DLQ_PRODUCER_CONFIG = {
    "bootstrap.servers": "localhost:9092",
    "acks": "1",
}


class TransientKafkaError(Exception):
    pass

class PermanentKafkaError(Exception):
    pass


class OrdiniConsumer:
    def __init__(self):
        self.consumer = Consumer(CONSUMER_CONFIG)
        self.dlq_producer = Producer(DLQ_PRODUCER_CONFIG)
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, *_) -> None:
        logger.info("shutdown_signal_received")
        self._running = False

    def processa_ordine(self, event: dict) -> None:
        """Elabora evento ordine. Solleva eccezioni in caso di errore."""
        order_id = event.get("order_id", "unknown")
        log = logger.bind(order_id=order_id)

        log.info("processing")
        # Simula processing (aggiornamento DB, chiamata API, ecc.)
        time.sleep(0.1)
        log.info("processed_ok")

    def invia_dlq(self, message, error_reason: str) -> None:
        """Invia messaggio fallito alla DLQ con metadati di errore."""
        dlq_message = {
            "original_value": message.value().decode("utf-8"),
            "original_topic": message.topic(),
            "original_partition": message.partition(),
            "original_offset": message.offset(),
            "error_reason": error_reason,
            "failed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        self.dlq_producer.produce(
            topic="orders.placed.dlq",
            key=message.key(),
            value=json.dumps(dlq_message).encode("utf-8"),
        )
        self.dlq_producer.poll(0)
        logger.warning("message_sent_to_dlq",
                       topic=message.topic(),
                       partition=message.partition(),
                       offset=message.offset())

    def run(self) -> None:
        """Loop principale del consumer."""
        self.consumer.subscribe(["orders.placed"])
        logger.info("consumer_started", topics=["orders.placed"])

        batch_size = 0
        last_commit = time.monotonic()
        COMMIT_INTERVAL_S = 5.0  # Commit ogni 5 secondi o ogni 100 messaggi

        while self._running:
            msg = self.consumer.poll(timeout=1.0)

            if msg is None:
                # Nessun messaggio disponibile — commit periodico se necessario
                if batch_size > 0 and (time.monotonic() - last_commit) > COMMIT_INTERVAL_S:
                    self.consumer.commit(asynchronous=False)
                    logger.debug("periodic_commit", messages=batch_size)
                    batch_size = 0
                    last_commit = time.monotonic()
                continue

            if msg.error():
                if msg.error().code() == KafkaError.PARTITION_EOF:
                    logger.debug("partition_eof",
                                 partition=msg.partition(),
                                 offset=msg.offset())
                    continue
                elif msg.error().code() == KafkaError._MAX_POLL_EXCEEDED:
                    logger.error("max_poll_exceeded_rebalancing")
                    break
                else:
                    raise KafkaException(msg.error())

            # Processa messaggio
            log = logger.bind(
                topic=msg.topic(),
                partition=msg.partition(),
                offset=msg.offset(),
                key=msg.key().decode("utf-8") if msg.key() else None,
            )

            try:
                event = json.loads(msg.value())
                self.processa_ordine(event)
                batch_size += 1

                # Commit ogni 100 messaggi o ogni COMMIT_INTERVAL_S secondi
                now = time.monotonic()
                if batch_size >= 100 or (now - last_commit) > COMMIT_INTERVAL_S:
                    self.consumer.commit(asynchronous=False)
                    log.debug("batch_committed", messages=batch_size)
                    batch_size = 0
                    last_commit = now

            except PermanentKafkaError as e:
                log.error("permanent_error_dlq", error=str(e))
                self.invia_dlq(msg, str(e))
                batch_size += 1  # Conta anche i messaggi mandati in DLQ

            except Exception as e:
                log.exception("unexpected_error_dlq", error=str(e))
                self.invia_dlq(msg, f"UnexpectedError: {type(e).__name__}: {str(e)}")
                batch_size += 1

        # Commit finale prima di uscire
        if batch_size > 0:
            self.consumer.commit(asynchronous=False)
            logger.info("final_commit", messages=batch_size)

        self.consumer.close()
        self.dlq_producer.flush()
        logger.info("consumer_stopped")


if __name__ == "__main__":
    OrdiniConsumer().run()
```

---

## PART C — Pattern Avanzati

### C1 — Outbox Pattern (Atomicità DB + Evento)

```
PROBLEMA SENZA OUTBOX:

  BEGIN TRANSACTION
    INSERT INTO orders (...)     ← DB ok
    commit transaction
  PUBLISH evento "OrderPlaced"   ← crash qui? evento perso!

SOLUZIONE OUTBOX:

  BEGIN TRANSACTION
    INSERT INTO orders (...)
    INSERT INTO outbox (event_type, payload)  ← tutto in una transazione
  COMMIT

  [Outbox Relay Service]:
    SELECT * FROM outbox WHERE status = 'pending' LIMIT 100
    FOR EACH event:
      PUBLISH a RabbitMQ/Kafka
      UPDATE outbox SET status = 'published'
```

```python
# file: outbox_pattern.py
"""
Implementazione Outbox Pattern con PostgreSQL.
Garantisce atomicità tra aggiornamento DB e pubblicazione evento.
"""
import json
import time
import uuid
from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.extras
import structlog

logger = structlog.get_logger(__name__)

DB_URL = "postgresql://app:app_password@localhost:5432/orders_db"


def init_outbox_table(conn) -> None:
    """Crea la tabella outbox se non esiste."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS outbox (
                id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                event_type  VARCHAR(100) NOT NULL,
                payload     JSONB NOT NULL,
                status      VARCHAR(20) DEFAULT 'pending',
                created_at  TIMESTAMPTZ DEFAULT now(),
                published_at TIMESTAMPTZ
            );
            CREATE INDEX IF NOT EXISTS outbox_status_idx ON outbox(status, created_at);

            CREATE TABLE IF NOT EXISTS orders (
                id          VARCHAR(50) PRIMARY KEY,
                customer_id VARCHAR(50) NOT NULL,
                total_eur   DECIMAL(10, 2) NOT NULL,
                status      VARCHAR(20) DEFAULT 'pending',
                created_at  TIMESTAMPTZ DEFAULT now()
            );
        """)
        conn.commit()
    logger.info("outbox_table_ready")


@contextmanager
def outbox_transaction(conn) -> Generator:
    """
    Context manager che garantisce atomicità tra ordine e evento outbox.
    """
    with conn:  # conn.commit() / conn.rollback() automatici
        yield conn


def crea_ordine_con_evento(
    conn,
    order_id: str,
    customer_id: str,
    total_eur: float,
) -> None:
    """
    Crea un ordine e pubblica l'evento nell'outbox in una singola transazione.
    Se uno dei due INSERT fallisce, entrambi vengono rollbackati.
    """
    with outbox_transaction(conn):
        with conn.cursor() as cur:
            # 1. Inserisci ordine
            cur.execute(
                "INSERT INTO orders (id, customer_id, total_eur) VALUES (%s, %s, %s)",
                (order_id, customer_id, total_eur)
            )

            # 2. Inserisci evento in outbox (stessa transazione!)
            event_payload = {
                "order_id": order_id,
                "customer_id": customer_id,
                "total_eur": float(total_eur),
                "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            cur.execute(
                "INSERT INTO outbox (event_type, payload) VALUES (%s, %s)",
                ("OrderPlaced", json.dumps(event_payload))
            )

    logger.info("order_and_event_created", order_id=order_id)


def outbox_relay(conn, publisher_fn) -> int:
    """
    Relay service: legge eventi pendenti dall'outbox e li pubblica.
    Deve girare come processo separato (o thread dedicato).
    Ritorna il numero di eventi pubblicati.
    """
    published = 0

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Lock per evitare che più relay processino lo stesso evento
        cur.execute("""
            SELECT id, event_type, payload
            FROM outbox
            WHERE status = 'pending'
            ORDER BY created_at
            LIMIT 100
            FOR UPDATE SKIP LOCKED
        """)
        events = cur.fetchall()

        for event in events:
            try:
                publisher_fn(event["event_type"], event["payload"])
                cur.execute(
                    "UPDATE outbox SET status='published', published_at=now() WHERE id=%s",
                    (event["id"],)
                )
                published += 1
                logger.info("event_relayed", event_type=event["event_type"], id=str(event["id"]))
            except Exception as e:
                logger.error("relay_failed", id=str(event["id"]), error=str(e))
                cur.execute(
                    "UPDATE outbox SET status='failed' WHERE id=%s",
                    (event["id"],)
                )

    conn.commit()
    return published


# Demo
if __name__ == "__main__":
    conn = psycopg2.connect(DB_URL)
    init_outbox_table(conn)

    # Crea ordini con garanzia atomica
    for i in range(5):
        crea_ordine_con_evento(
            conn,
            order_id=f"ORD-OUTBOX-{i:04d}",
            customer_id=f"CUST-{i + 1:03d}",
            total_eur=100.0 + i * 25.5,
        )

    # Simula relay (pubblica su RabbitMQ/Kafka)
    def mock_publisher(event_type: str, payload: dict) -> None:
        print(f"  → Pubblicato: {event_type} — {json.dumps(payload)[:60]}...")

    count = outbox_relay(conn, mock_publisher)
    print(f"Pubblicati {count} eventi dall'outbox")
    conn.close()
```

### C2 — Saga Pattern (Transazioni Distribuite)

```python
# file: saga_pattern.py
"""
Saga Pattern — Coreography-based.
Ogni step della saga è un evento; in caso di errore
viene pubblicato un evento di compensation.

Use case: ordine e-commerce con 4 step:
  1. Riserva inventario
  2. Addebita pagamento
  3. Crea spedizione
  4. Notifica cliente
Se il pagamento fallisce → compensation: libera inventario
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

import structlog

logger = structlog.get_logger(__name__)


class SagaState(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    COMPENSATING = "COMPENSATING"
    FAILED = "FAILED"


@dataclass
class SagaContext:
    saga_id: str
    order_id: str
    customer_id: str
    total_eur: float
    state: SagaState = SagaState.PENDING
    current_step: int = 0
    completed_steps: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class SagaStep:
    name: str
    execute: Callable[[SagaContext], bool]   # ritorna True se ok
    compensate: Callable[[SagaContext], None] # rollback


class OrderSaga:
    """
    Saga per l'elaborazione di un ordine.
    Steps: InventarioReservato → PagamentoAddebitato → SpedizioneCreata → ClienteNotificato
    """

    def __init__(self):
        self.steps: list[SagaStep] = [
            SagaStep(
                name="RiservaInventario",
                execute=self._riserva_inventario,
                compensate=self._libera_inventario,
            ),
            SagaStep(
                name="AddebitaPagamento",
                execute=self._addebita_pagamento,
                compensate=self._rimborsa_pagamento,
            ),
            SagaStep(
                name="CreaSpedizione",
                execute=self._crea_spedizione,
                compensate=self._annulla_spedizione,
            ),
            SagaStep(
                name="NotificaCliente",
                execute=self._notifica_cliente,
                compensate=lambda _: None,  # Notifica non è reversibile — skip
            ),
        ]

    def esegui(self, ctx: SagaContext) -> SagaState:
        """Esegui la saga step by step."""
        ctx.state = SagaState.IN_PROGRESS
        log = logger.bind(saga_id=ctx.saga_id, order_id=ctx.order_id)

        for i, step in enumerate(self.steps):
            ctx.current_step = i
            log.info("step_started", step=step.name)

            try:
                success = step.execute(ctx)
                if success:
                    ctx.completed_steps.append(step.name)
                    log.info("step_completed", step=step.name)
                else:
                    log.error("step_failed_compensation_needed", step=step.name)
                    ctx.errors.append(f"{step.name}: returned False")
                    return self._compensate(ctx, from_step=i - 1, log=log)
            except Exception as e:
                log.error("step_exception", step=step.name, error=str(e))
                ctx.errors.append(f"{step.name}: {e}")
                return self._compensate(ctx, from_step=i - 1, log=log)

        ctx.state = SagaState.COMPLETED
        log.info("saga_completed")
        return ctx.state

    def _compensate(self, ctx: SagaContext, from_step: int, log) -> SagaState:
        """Esegue compensation per tutti gli step già completati (in ordine inverso)."""
        ctx.state = SagaState.COMPENSATING
        log.warning("compensation_started", from_step=from_step)

        for i in range(from_step, -1, -1):
            step = self.steps[i]
            if step.name in ctx.completed_steps:
                try:
                    step.compensate(ctx)
                    log.info("compensation_step_ok", step=step.name)
                except Exception as e:
                    log.error("compensation_step_failed", step=step.name, error=str(e))
                    # In produzione: alert manuale — compensation fallita è critica

        ctx.state = SagaState.FAILED
        return ctx.state

    # ─── Steps ─────────────────────────────────────────────────────────────────

    def _riserva_inventario(self, ctx: SagaContext) -> bool:
        logger.info("riserving_inventory", order=ctx.order_id)
        time.sleep(0.05)  # Simula chiamata API magazzino
        return True  # Successo

    def _libera_inventario(self, ctx: SagaContext) -> None:
        logger.info("releasing_inventory", order=ctx.order_id)
        time.sleep(0.03)

    def _addebita_pagamento(self, ctx: SagaContext) -> bool:
        logger.info("charging_payment", order=ctx.order_id, amount=ctx.total_eur)
        time.sleep(0.1)
        # Simula fallimento per importi > €500
        if ctx.total_eur > 500:
            raise RuntimeError("Limite carta superato")
        return True

    def _rimborsa_pagamento(self, ctx: SagaContext) -> None:
        logger.info("refunding_payment", order=ctx.order_id)
        time.sleep(0.08)

    def _crea_spedizione(self, ctx: SagaContext) -> bool:
        logger.info("creating_shipment", order=ctx.order_id)
        time.sleep(0.07)
        return True

    def _annulla_spedizione(self, ctx: SagaContext) -> None:
        logger.info("cancelling_shipment", order=ctx.order_id)
        time.sleep(0.04)

    def _notifica_cliente(self, ctx: SagaContext) -> bool:
        logger.info("notifying_customer", customer=ctx.customer_id)
        return True


if __name__ == "__main__":
    import structlog
    structlog.configure()

    saga = OrderSaga()

    # Ordine normale — deve completarsi
    ctx1 = SagaContext(
        saga_id=str(uuid.uuid4())[:8],
        order_id="ORD-SAGA-001",
        customer_id="CUST-001",
        total_eur=150.00,
    )
    result1 = saga.esegui(ctx1)
    print(f"\nOrdine €150: {result1.value} — Steps: {ctx1.completed_steps}")

    # Ordine con importo alto — pagamento fallisce → compensation
    ctx2 = SagaContext(
        saga_id=str(uuid.uuid4())[:8],
        order_id="ORD-SAGA-002",
        customer_id="CUST-002",
        total_eur=750.00,
    )
    result2 = saga.esegui(ctx2)
    print(f"\nOrdine €750: {result2.value} — Errori: {ctx2.errors}")
    print(f"Step compensati: inventario liberato = {'RiservaInventario' in ctx2.completed_steps and 'AddebitaPagamento' not in ctx2.completed_steps}")
```

---

## PART D — Monitoring e Verifica

### D1 — Consumer Lag Monitor

```bash
# Monitora consumer lag Kafka (quanti messaggi in ritardo)
docker exec kafka kafka-consumer-groups \
    --bootstrap-server localhost:9092 \
    --describe \
    --group orders-processor-v1

# Output:
# TOPIC          PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG  CONSUMER-ID
# orders.placed  0          42              45              3    consumer-1
# orders.placed  1          38              38              0    consumer-2
# orders.placed  2          51              51              0    consumer-3
# LAG=0 su tutte le partizioni = consumer aggiornato
```

```python
# file: monitoring.py
"""Monitora consumer lag Kafka e RabbitMQ queue depths."""
import json
import httpx
import structlog

logger = structlog.get_logger("monitoring")

def check_rabbitmq_queues(base_url: str = "http://localhost:15672",
                           user: str = "admin", pwd: str = "rabbit_admin_password") -> dict:
    """Legge profondità code da RabbitMQ Management API."""
    with httpx.Client(base_url=base_url, auth=(user, pwd), timeout=10) as client:
        r = client.get("/api/queues/%2F")  # %2F = vhost /
        r.raise_for_status()
        queues = r.json()

    report = {}
    for q in queues:
        name = q["name"]
        messages = q.get("messages", 0)
        consumers = q.get("consumers", 0)
        report[name] = {"messages": messages, "consumers": consumers}

        if messages > 1000:
            logger.warning("queue_backlog_high", queue=name, messages=messages)
        if consumers == 0 and messages > 0:
            logger.error("queue_no_consumers", queue=name, messages=messages)

    return report

if __name__ == "__main__":
    import structlog
    structlog.configure()
    report = check_rabbitmq_queues()
    for queue, stats in report.items():
        print(f"  {queue:40s} messages={stats['messages']:6d} consumers={stats['consumers']}")
```

### D2 — Test del Lab Completo

```bash
# Terminal 1: Avvia consumer RabbitMQ
python3 rabbitmq_consumer.py

# Terminal 2: Avvia consumer Kafka
python3 kafka_consumer.py

# Terminal 3: Esegui producer + saga test
python3 rabbitmq_producer.py
python3 kafka_producer.py
python3 saga_pattern.py

# Terminal 4: Monitora
python3 monitoring.py

# Verifica RabbitMQ UI
open http://localhost:15672  # user: admin, pass: rabbit_admin_password

# Verifica Kafka UI
open http://localhost:8080   # Kafka UI

# Controlla DLQ RabbitMQ
curl -u admin:rabbit_admin_password \
    http://localhost:15672/api/queues/%2F/orders.italy.failed | python3 -m json.tool

# Controlla DLQ Kafka
docker exec kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic orders.placed.dlq \
    --from-beginning \
    --max-messages 10
```

---

## Cheat Sheet: Quando usare RabbitMQ vs Kafka

```
SCEGLI RABBITMQ QUANDO:
  ✓ Task queue (ogni messaggio elaborato da un solo consumer)
  ✓ Instradamento complesso (routing key, topic exchange, headers)
  ✓ Priority queue (messaggi urgenti prima degli altri)
  ✓ ACK per singolo messaggio (granularità alta)
  ✓ Latenza bassa per singolo messaggio (< 5ms tipica)
  ✓ Volume: < 50.000 msg/s
  Esempi: invio email, resize immagini, PDF generation, job scheduling

SCEGLI KAFKA QUANDO:
  ✓ Event log (ogni consumer legge tutto il topic indipendentemente)
  ✓ Replay storico (rielaborare eventi passati, nuovi consumer)
  ✓ Throughput estremo (1M+ msg/s per cluster)
  ✓ Retention lunga (giorni/mesi di dati)
  ✓ CDC (change data capture da database)
  ✓ Analytics e data pipeline
  Esempi: audit log, CDC, stream processing, event sourcing

ENTRAMBI NON SONO ADATTI QUANDO:
  ✗ Hai bisogno di query sui messaggi (usa database)
  ✗ Hai bisogno di risposta sincrona (usa gRPC/REST)
  ✗ Volume < 100 msg/ora (overkill — usa Redis o file)
```

---

## Riferimenti

- RabbitMQ Docs: https://www.rabbitmq.com/docs
- Kafka Docs: https://kafka.apache.org/documentation/
- pika (Python AMQP): https://pika.readthedocs.io/
- confluent-kafka-python: https://docs.confluent.io/kafka-clients/python/
- Saga Pattern: https://microservices.io/patterns/data/saga.html
- Outbox Pattern: https://microservices.io/patterns/data/transactional-outbox.html
- Modulo sorgente: `16-event-driven-architecture-pratica.md`
