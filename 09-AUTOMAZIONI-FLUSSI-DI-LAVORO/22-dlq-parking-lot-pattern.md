---
corso: "Automazioni e Flussi di Lavoro"
fase: "5 — Pattern Avanzati"
modulo: 22
titolo: "Dead Letter Queue (DLQ) e Parking Lot Pattern"
versione: "AWS SQS, RabbitMQ 3.x, Kafka 3.x"
livello: "proficient"
prerequisiti: ["Modulo 16 — Event-Driven Architecture", "Modulo 17 — Retry e Idempotency"]
obiettivi:
  - "Progettare DLQ e parking lot per workflow e messaging con policy di retry e TTL configurabili"
  - "Implementare alerting automatico su DLQ con soglie e notifiche per intervento operativo"
  - "Configurare replay sicuro dei messaggi dalla DLQ alla coda principale dopo root-cause fix"
  - "Distinguere poison message da errori transitori e applicare routing differenziato"
  - "Integrare DLQ pattern su AWS SQS, RabbitMQ DLX e Kafka DLT con monitoring OTel"
tag: [dlq, parking-lot, dead-letter, replay, poison-message, messaging, rabbitmq, kafka, sqs]
---

# Dead Letter Queue (DLQ) e Parking Lot Pattern

> **Obiettivi di apprendimento**
> 1. Progettare DLQ e parking lot per workflow e messaging con policy di retry e TTL configurabili
> 2. Implementare alerting automatico su DLQ con soglie e notifiche per intervento operativo
> 3. Configurare replay sicuro dei messaggi dalla DLQ alla coda principale dopo root-cause fix
> 4. Distinguere poison message da errori transitori e applicare routing differenziato
> 5. Integrare DLQ pattern su AWS SQS, RabbitMQ DLX e Kafka DLT con monitoring OTel

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 4 — Pattern di affidabilita · Modulo 22 (nuovo)
> **Prerequisiti:** Moduli 16, 17.
> **Obiettivi:** disegnare DLQ + parking lot per workflow + messaging; alerting + retry policy + replay.
> **Tempo:** lettura 45 min · lab 180 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-24

---

## Indice

1. [Idee guida](#idee-guida)
2. [Parte teorica — Dead Letter Queue](#parte-teorica--dead-letter-queue)
3. [Parking Lot Pattern](#parking-lot-pattern)
4. [Implementazione RabbitMQ](#implementazione-rabbitmq)
5. [Implementazione Kafka](#implementazione-kafka)
6. [AWS SQS DLQ](#aws-sqs-dlq)
7. [Azure Service Bus DLQ](#azure-service-bus-dlq)
8. [Poison Message Handling](#poison-message-handling)
9. [Retry Strategies](#retry-strategies)
10. [Circuit Breaker Integration](#circuit-breaker-integration)
11. [Monitoring e Alerting](#monitoring-e-alerting)
12. [Operational Playbook — DLQ Processing](#operational-playbook--dlq-processing)
13. [Reprocessing Workflows](#reprocessing-workflows)
14. [Data Loss Prevention](#data-loss-prevention)
15. [DLQ nelle piattaforme workflow](#dlq-nelle-piattaforme-workflow)
16. [Esempi di codice Python](#esempi-di-codice-python)
17. [Esercizi](#esercizi)
18. [Troubleshooting — 20 problemi comuni](#troubleshooting--20-problemi-comuni)
19. [FAQ — 20 domande e risposte](#faq--20-domande-e-risposte)
20. [Auto-valutazione](#auto-valutazione)
21. [Letture primarie consigliate](#letture-primarie-consigliate)
22. [Collegamenti incrociati](#collegamenti-incrociati)
23. [Glossario locale](#glossario-locale)

---

## Idee guida

1. **DLQ = mailbox per messaggi falliti.** Mai cancellare automaticamente; conservare per analisi.
2. **Parking lot = mailbox per messaggi sconosciuti.** Caso edge non gestito → parcheggia, non perdere.
3. **DLQ alerting > 0 = signal di problema sistemico.** Soglia da definire per ambiente.
4. **Replay tooling: poter ri-iniettare DLQ items dopo fix.** Senza replay, fix codice + DLQ items persi.
5. **Zero data loss come principio architetturale.** Ogni messaggio deve avere un destino tracciabile: successo, DLQ o parking lot.
6. **Separazione failure domain.** DLQ per errori tecnici prevedibili, parking lot per anomalie strutturali.

---

## Parte teorica — Dead Letter Queue

### Cos'e una Dead Letter Queue

Una Dead Letter Queue (DLQ) e una coda secondaria in cui vengono spostati i messaggi che non possono essere elaborati con successo dalla coda principale. Il termine "dead letter" deriva dal servizio postale: le lettere non recapitabili finiscono in un ufficio dedicato.

In un sistema di messaging, un messaggio diventa "dead letter" quando:

- Il consumer ha tentato l'elaborazione N volte senza successo (max retry exceeded).
- Il messaggio e scaduto (TTL expired).
- Il messaggio e stato rifiutato esplicitamente dal consumer (nack/reject senza requeue).
- La coda di destinazione non esiste o ha raggiunto la capacita massima.

### Flusso architetturale base

```
Producer
   │
   ▼
┌──────────────┐
│  Main Queue   │
└──────┬───────┘
       │
       ▼
┌──────────────┐     fail (retry 1)      ┌──────────────┐
│   Consumer    │ ──────────────────────► │  Main Queue   │
└──────┬───────┘                         └──────────────┘
       │
       │ fail (retry N = max)
       ▼
┌──────────────┐
│     DLQ       │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│  Alert + Manual Review    │
│  Dashboard operativo      │
└──────┬───────────────────┘
       │ (dopo fix)
       ▼
┌──────────────┐
│  Replay Tool  │ ──► Main Queue
└──────────────┘
```

### Quando un messaggio fallisce

I fallimenti si classificano in tre categorie:

| Categoria | Esempio | Azione corretta |
|---|---|---|
| **Transient** | Timeout database, 503 esterno | Retry con backoff |
| **Persistent** | Bug nel consumer, schema invalido | DLQ dopo max retry |
| **Structural** | Event type sconosciuto, formato ignoto | Parking lot |

La distinzione e critica: un retry infinito su un errore persistente spreca risorse e blocca il consumer. Un invio diretto a DLQ di un errore transient perde messaggi elaborabili.

### Retry vs DLQ: la decisione

```
Messaggio ricevuto
       │
       ▼
  Elaborazione
       │
       ├── Successo → ACK
       │
       └── Fallimento
              │
              ▼
        Errore transient?
              │
              ├── Si → retry_count < max?
              │         │
              │         ├── Si → Delay + Retry
              │         └── No → DLQ
              │
              └── No → Errore classificabile?
                        │
                        ├── Si (persistent) → DLQ
                        └── No (sconosciuto) → Parking Lot
```

### Proprieta fondamentali della DLQ

1. **Persistenza:** i messaggi nella DLQ devono sopravvivere al restart del broker.
2. **Metadati arricchiti:** ogni messaggio DLQ deve portare informazioni aggiuntive — motivo del fallimento, numero di retry, timestamp originale, stack trace.
3. **Isolamento:** la DLQ non deve influenzare le performance della coda principale.
4. **Retention:** definire retention esplicita (giorni/settimane), non infinita.
5. **Accessibilita:** deve essere monitorabile, interrogabile e replay-able.

### Header DLQ raccomandati

Ogni messaggio spostato nella DLQ dovrebbe includere:

```json
{
  "x-original-queue": "orders.process",
  "x-death-reason": "rejected",
  "x-death-count": 3,
  "x-first-death-timestamp": "2026-05-22T10:15:33Z",
  "x-last-death-timestamp": "2026-05-22T10:17:45Z",
  "x-original-routing-key": "orders.new",
  "x-exception-type": "ValueError",
  "x-exception-message": "campo 'amount' non numerico",
  "x-consumer-id": "worker-03",
  "x-original-message-id": "msg-a1b2c3d4"
}
```

---

## Parking Lot Pattern

### Definizione

Il Parking Lot Pattern e un pattern complementare alla DLQ. Mentre la DLQ raccoglie messaggi che hanno fallito l'elaborazione dopo N tentativi, il parking lot raccoglie messaggi che il sistema **non sa come elaborare**.

Differenza chiave:

| Aspetto | DLQ | Parking Lot |
|---|---|---|
| **Causa** | Errore durante elaborazione | Messaggio non classificabile |
| **Retry utile?** | Si, dopo fix del bug | No, serve intervento umano |
| **Esempio** | NullPointerException nel consumer | Webhook con `event_type: "unknown_v3"` |
| **Azione** | Fix codice → replay | Analisi → aggiornamento schema → replay |
| **Automazione** | Retry automatico possibile | Sempre manuale |

### Architettura con parking lot

```
Producer
   │
   ▼
┌──────────────┐
│  Main Queue   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Router /     │
│  Classifier   │
└──────┬───────┘
       │
       ├── Tipo noto → Consumer specifico
       │         │
       │         ├── Successo → ACK
       │         └── Fallimento → DLQ
       │
       └── Tipo sconosciuto → Parking Lot
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  Alert + Manual   │
                        │  Investigation    │
                        └──────────────────┘
```

### Casi d'uso del parking lot

1. **Schema evolution:** un producer aggiorna il formato dei messaggi prima che il consumer sia aggiornato.
2. **Webhook sconosciuti:** servizio esterno invia un nuovo tipo di evento non previsto.
3. **Messaggi corrotti:** payload non deserializzabile (encoding errato, JSON malformato).
4. **Versioning mismatch:** messaggio con version header non supportata.
5. **Feature flag mismatch:** messaggio per feature non ancora attiva nell'ambiente.
6. **Multi-tenant routing:** messaggio per tenant non configurato nel sistema.

### Implementazione parking lot

```python
import json
from datetime import datetime, timezone
from typing import Any

class ParkingLotRouter:
    """
    Router che classifica messaggi e li instrada alla coda
    appropriata oppure al parking lot.
    """

    def __init__(
        self,
        known_types: set[str],
        main_handler,
        parking_lot_publisher,
        alert_service,
    ):
        self._known_types = frozenset(known_types)
        self._main_handler = main_handler
        self._parking_lot = parking_lot_publisher
        self._alert = alert_service

    def route(self, message: dict[str, Any]) -> str:
        event_type = message.get("event_type")

        if event_type is None:
            self._send_to_parking_lot(
                message, reason="missing_event_type"
            )
            return "parking_lot"

        if event_type not in self._known_types:
            self._send_to_parking_lot(
                message, reason=f"unknown_event_type:{event_type}"
            )
            return "parking_lot"

        try:
            self._main_handler.process(message)
            return "processed"
        except Exception as exc:
            # Errore durante elaborazione → flusso DLQ standard
            raise

    def _send_to_parking_lot(
        self, message: dict[str, Any], reason: str
    ) -> None:
        envelope = {
            "original_message": message,
            "parking_lot_reason": reason,
            "parked_at": datetime.now(timezone.utc).isoformat(),
            "source_queue": message.get("_source_queue", "unknown"),
        }
        self._parking_lot.publish(envelope)
        self._alert.notify(
            level="warning",
            title="Messaggio in parking lot",
            detail=reason,
        )
```

---

## Implementazione RabbitMQ

### Dead Letter Exchange (DLX)

RabbitMQ implementa la DLQ tramite il concetto di **Dead Letter Exchange (DLX)**. Quando un messaggio diventa "dead letter", viene pubblicato su un exchange dedicato che lo instrada alla DLQ.

Un messaggio diventa dead letter in RabbitMQ quando:

1. Viene rifiutato con `basic.nack` o `basic.reject` con `requeue=false`.
2. Il TTL del messaggio scade.
3. La coda raggiunge la lunghezza massima (`x-max-length`).

### Configurazione coda con DLX

```python
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost")
)
channel = connection.channel()

# 1. Dichiarare il Dead Letter Exchange
channel.exchange_declare(
    exchange="dlx.exchange",
    exchange_type="direct",
    durable=True,
)

# 2. Dichiarare la Dead Letter Queue
channel.queue_declare(
    queue="orders.dlq",
    durable=True,
    arguments={
        "x-message-ttl": 604800000,  # 7 giorni retention
    },
)

# 3. Bind DLQ al DLX
channel.queue_bind(
    queue="orders.dlq",
    exchange="dlx.exchange",
    routing_key="orders.dead",
)

# 4. Dichiarare la coda principale con DLX configurato
channel.queue_declare(
    queue="orders.process",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "dlx.exchange",
        "x-dead-letter-routing-key": "orders.dead",
        "x-message-ttl": 300000,  # 5 min TTL messaggi
        "x-max-length": 100000,   # max 100k messaggi
    },
)

# 5. Bind coda principale
channel.exchange_declare(
    exchange="orders.exchange",
    exchange_type="direct",
    durable=True,
)
channel.queue_bind(
    queue="orders.process",
    exchange="orders.exchange",
    routing_key="orders.new",
)
```

### Consumer con retry e DLQ

```python
import json
import pika
import traceback
from datetime import datetime, timezone

MAX_RETRIES = 3

def on_message(channel, method, properties, body):
    """Consumer che implementa retry con conteggio e DLQ."""
    headers = properties.headers or {}
    retry_count = headers.get("x-retry-count", 0)
    message_id = properties.message_id or "unknown"

    try:
        payload = json.loads(body)
        process_order(payload)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[OK] Messaggio {message_id} elaborato")

    except TransientError as exc:
        # Errore temporaneo → retry se sotto il limite
        if retry_count < MAX_RETRIES:
            # Pubblica sulla stessa coda con retry incrementato
            new_headers = {
                **headers,
                "x-retry-count": retry_count + 1,
                "x-last-error": str(exc),
                "x-last-retry-at": datetime.now(timezone.utc).isoformat(),
            }
            channel.basic_publish(
                exchange="orders.exchange",
                routing_key="orders.new",
                body=body,
                properties=pika.BasicProperties(
                    headers=new_headers,
                    delivery_mode=2,  # persistent
                    message_id=message_id,
                ),
            )
            channel.basic_ack(delivery_tag=method.delivery_tag)
            print(
                f"[RETRY {retry_count + 1}/{MAX_RETRIES}] "
                f"Messaggio {message_id}: {exc}"
            )
        else:
            # Max retry raggiunto → reject → DLX → DLQ
            channel.basic_nack(
                delivery_tag=method.delivery_tag, requeue=False
            )
            print(
                f"[DLQ] Messaggio {message_id} "
                f"dopo {MAX_RETRIES} retry: {exc}"
            )

    except PersistentError:
        # Errore permanente → DLQ diretto, retry inutile
        channel.basic_nack(
            delivery_tag=method.delivery_tag, requeue=False
        )
        print(f"[DLQ] Messaggio {message_id} errore permanente")

    except Exception as exc:
        # Errore sconosciuto → DLQ per sicurezza
        channel.basic_nack(
            delivery_tag=method.delivery_tag, requeue=False
        )
        print(
            f"[DLQ] Messaggio {message_id} "
            f"errore non classificato: {exc}"
        )


# Setup consumer
channel.basic_qos(prefetch_count=10)
channel.basic_consume(
    queue="orders.process", on_message_callback=on_message
)
channel.start_consuming()
```

### TTL e scadenza messaggi

RabbitMQ supporta TTL a due livelli:

1. **Per-queue TTL** (`x-message-ttl`): tutti i messaggi nella coda scadono dopo il tempo configurato.
2. **Per-message TTL** (`expiration` property): TTL individuale per messaggio.

```python
# TTL per messaggio singolo
channel.basic_publish(
    exchange="orders.exchange",
    routing_key="orders.new",
    body=json.dumps(payload),
    properties=pika.BasicProperties(
        expiration="60000",  # 60 secondi
        delivery_mode=2,
    ),
)
```

Quando il TTL scade e la coda ha un DLX configurato, il messaggio viene spostato automaticamente nella DLQ.

### Delayed retry con TTL e DLX

Implementare retry con delay usando code intermedie con TTL:

```python
def setup_delayed_retry(channel, base_queue: str, delays: list[int]):
    """
    Crea code di retry con delay crescente.
    delays = [5000, 30000, 120000] → 5s, 30s, 2min
    """
    for i, delay_ms in enumerate(delays):
        retry_queue = f"{base_queue}.retry.{i}"
        channel.queue_declare(
            queue=retry_queue,
            durable=True,
            arguments={
                "x-message-ttl": delay_ms,
                "x-dead-letter-exchange": "orders.exchange",
                "x-dead-letter-routing-key": "orders.new",
                # Quando il TTL scade, il messaggio torna
                # alla coda principale via DLX
            },
        )

# Uso: code retry.0 (5s), retry.1 (30s), retry.2 (2min)
# Dopo retry.2, se fallisce ancora → DLQ finale
```

### Architettura RabbitMQ completa con DLQ

```
                    orders.exchange
                         │
                         ▼
              ┌─────────────────────┐
              │   orders.process     │  ◄── x-dead-letter-exchange: dlx.exchange
              └─────────┬───────────┘
                        │
                        ▼
                    Consumer
                   /    │    \
                  /     │     \
            success   transient  persistent
               │      error      error
               │        │          │
              ACK       │        NACK
                        │     (requeue=false)
                        ▼          │
              ┌──────────────┐     │
              │ retry queue  │     │
              │ (con TTL)    │     │
              └──────┬───────┘     │
                     │             │
                TTL scade          │
                     │             │
                     ▼             ▼
              orders.process   dlx.exchange
              (retry)              │
                                   ▼
                          ┌──────────────┐
                          │  orders.dlq   │
                          └──────────────┘
```

---

## Implementazione Kafka

### Dead Letter Topic (DLT)

Kafka non ha una DLQ nativa come RabbitMQ o SQS. Il pattern DLQ in Kafka si implementa con un **Dead Letter Topic (DLT)** — un topic dedicato dove il consumer pubblica i messaggi che non riesce a elaborare.

### Convenzioni di naming

```
Topic principale:     orders.events
Dead Letter Topic:    orders.events.DLT
Retry Topic (opt):    orders.events.retry-1
                      orders.events.retry-2
Parking Lot Topic:    orders.events.parking-lot
```

### Consumer con DLT — Python (confluent-kafka)

```python
import json
import traceback
from datetime import datetime, timezone
from confluent_kafka import Consumer, Producer, KafkaError

MAX_RETRIES = 3

consumer_config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "order-processor",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
    "max.poll.interval.ms": 300000,
}

producer_config = {
    "bootstrap.servers": "localhost:9092",
    "acks": "all",
    "retries": 3,
}

consumer = Consumer(consumer_config)
producer = Producer(producer_config)
consumer.subscribe(["orders.events"])

MAIN_TOPIC = "orders.events"
DLT_TOPIC = "orders.events.DLT"
PARKING_LOT_TOPIC = "orders.events.parking-lot"


def send_to_dlt(
    original_msg, error: Exception, retry_count: int
) -> None:
    """Pubblica messaggio nel Dead Letter Topic con metadati."""
    dlt_headers = [
        ("x-original-topic", MAIN_TOPIC.encode()),
        ("x-original-partition", str(original_msg.partition()).encode()),
        ("x-original-offset", str(original_msg.offset()).encode()),
        ("x-original-timestamp", str(original_msg.timestamp()[1]).encode()),
        ("x-error-type", type(error).__name__.encode()),
        ("x-error-message", str(error)[:500].encode()),
        ("x-retry-count", str(retry_count).encode()),
        (
            "x-dead-letter-at",
            datetime.now(timezone.utc).isoformat().encode(),
        ),
    ]
    producer.produce(
        topic=DLT_TOPIC,
        key=original_msg.key(),
        value=original_msg.value(),
        headers=dlt_headers,
    )
    producer.flush()


def send_to_parking_lot(
    original_msg, reason: str
) -> None:
    """Pubblica messaggio nel parking lot topic."""
    headers = [
        ("x-original-topic", MAIN_TOPIC.encode()),
        ("x-parking-reason", reason.encode()),
        (
            "x-parked-at",
            datetime.now(timezone.utc).isoformat().encode(),
        ),
    ]
    producer.produce(
        topic=PARKING_LOT_TOPIC,
        key=original_msg.key(),
        value=original_msg.value(),
        headers=headers,
    )
    producer.flush()


def process_messages():
    """Loop principale di consumo con gestione DLT e parking lot."""
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            print(f"Errore consumer: {msg.error()}")
            continue

        headers = dict(msg.headers() or [])
        retry_count = int(
            headers.get("x-retry-count", b"0").decode()
        )

        try:
            payload = json.loads(msg.value().decode())
            event_type = payload.get("event_type")

            if event_type not in KNOWN_EVENT_TYPES:
                send_to_parking_lot(
                    msg, f"unknown_event_type:{event_type}"
                )
                consumer.commit(message=msg)
                continue

            process_event(payload)
            consumer.commit(message=msg)

        except TransientError as exc:
            if retry_count < MAX_RETRIES:
                # Re-pubblica con retry count incrementato
                new_headers = [
                    ("x-retry-count", str(retry_count + 1).encode()),
                    ("x-last-error", str(exc)[:500].encode()),
                ]
                producer.produce(
                    topic=MAIN_TOPIC,
                    key=msg.key(),
                    value=msg.value(),
                    headers=new_headers,
                )
                producer.flush()
            else:
                send_to_dlt(msg, exc, retry_count)
            consumer.commit(message=msg)

        except Exception as exc:
            send_to_dlt(msg, exc, retry_count)
            consumer.commit(message=msg)


process_messages()
```

### Spring Kafka DLT (riferimento Java)

Spring Kafka fornisce supporto nativo per DLT tramite `DefaultErrorHandler` e `DeadLetterPublishingRecoverer`:

```
// Concetto (pseudocodice)
@RetryableTopic(
    attempts = 3,
    backoff = @Backoff(delay = 5000, multiplier = 2),
    dltTopicSuffix = ".DLT"
)
@KafkaListener(topics = "orders.events")
void process(OrderEvent event) { ... }
```

Spring crea automaticamente topic di retry con delay e un DLT finale.

### Retention DLT

Configurare retention per il DLT separatamente dal topic principale:

```bash
# Topic principale: 7 giorni
kafka-configs.sh --alter --entity-type topics \
    --entity-name orders.events \
    --add-config retention.ms=604800000

# DLT: 30 giorni (piu tempo per analisi)
kafka-configs.sh --alter --entity-type topics \
    --entity-name orders.events.DLT \
    --add-config retention.ms=2592000000
```

---

## AWS SQS DLQ

### RedrivePolicy

AWS SQS ha supporto nativo per DLQ tramite la `RedrivePolicy`. Ogni coda SQS puo avere una DLQ associata.

```json
{
  "RedrivePolicy": {
    "deadLetterTargetArn": "arn:aws:sqs:eu-west-1:123456789:orders-dlq",
    "maxReceiveCount": 3
  }
}
```

Il parametro `maxReceiveCount` indica dopo quanti tentativi di receive falliti il messaggio viene spostato nella DLQ.

### Setup con boto3

```python
import boto3
import json

sqs = boto3.client("sqs", region_name="eu-west-1")

# 1. Creare la DLQ
dlq_response = sqs.create_queue(
    QueueName="orders-dlq",
    Attributes={
        "MessageRetentionPeriod": str(14 * 24 * 3600),  # 14 giorni
        "VisibilityTimeout": "60",
    },
)
dlq_url = dlq_response["QueueUrl"]

# Ottenere ARN della DLQ
dlq_attrs = sqs.get_queue_attributes(
    QueueUrl=dlq_url, AttributeNames=["QueueArn"]
)
dlq_arn = dlq_attrs["Attributes"]["QueueArn"]

# 2. Creare la coda principale con RedrivePolicy
main_response = sqs.create_queue(
    QueueName="orders-main",
    Attributes={
        "VisibilityTimeout": "30",
        "MessageRetentionPeriod": str(7 * 24 * 3600),  # 7 giorni
        "RedrivePolicy": json.dumps(
            {
                "deadLetterTargetArn": dlq_arn,
                "maxReceiveCount": 3,
            }
        ),
    },
)
main_url = main_response["QueueUrl"]
```

### Consumer SQS con gestione DLQ

```python
import json
import boto3
from datetime import datetime, timezone

sqs = boto3.client("sqs", region_name="eu-west-1")
QUEUE_URL = "https://sqs.eu-west-1.amazonaws.com/123456789/orders-main"


def poll_and_process():
    """Polling loop SQS con gestione errori."""
    while True:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,  # long polling
            AttributeNames=["All"],
            MessageAttributeNames=["All"],
        )

        messages = response.get("Messages", [])
        for msg in messages:
            receipt_handle = msg["ReceiptHandle"]
            receive_count = int(
                msg["Attributes"].get("ApproximateReceiveCount", "1")
            )

            try:
                body = json.loads(msg["Body"])
                process_order(body)

                # Successo → cancella messaggio
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=receipt_handle,
                )

            except TransientError:
                # Non cancellare → SQS fara retry dopo
                # VisibilityTimeout. Dopo maxReceiveCount → DLQ
                print(
                    f"Retry {receive_count}/3 "
                    f"per msg {msg['MessageId']}"
                )

            except PersistentError:
                # Errore permanente: lascia che SQS lo muova in DLQ
                # dopo maxReceiveCount, oppure forza con
                # change_message_visibility a 0 per accelerare
                sqs.change_message_visibility(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=receipt_handle,
                    VisibilityTimeout=0,
                )
```

### RedriveAllowPolicy (SQS → DLQ replay)

AWS SQS supporta il replay nativo dalla DLQ alla coda sorgente tramite `StartMessageMoveTask`:

```python
# Replay DLQ → coda principale
sqs.start_message_move_task(
    SourceArn=dlq_arn,
    DestinationArn=main_queue_arn,
    MaxNumberOfMessagesPerSecond=50,  # rate limiting
)
```

---

## Azure Service Bus DLQ

### DLQ nativo

Azure Service Bus fornisce una DLQ nativa per ogni coda e subscription. La DLQ e una sub-coda con path `<queue>/$DeadLetterQueue`.

Un messaggio finisce nella DLQ quando:

1. `MaxDeliveryCount` viene raggiunto (default: 10).
2. Il messaggio scade (TTL).
3. Il consumer chiama esplicitamente `dead_letter()`.

### Configurazione Python

```python
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.servicebus.management import ServiceBusAdministrationClient

# Configurare la coda con DLQ
admin_client = ServiceBusAdministrationClient.from_connection_string(
    conn_str
)
admin_client.create_queue(
    queue_name="orders",
    max_delivery_count=5,  # max retry prima di DLQ
    default_message_time_to_live="P7D",  # 7 giorni TTL
    dead_lettering_on_message_expiration=True,
    lock_duration="PT30S",  # 30 secondi lock
)

# Consumer con dead lettering esplicito
client = ServiceBusClient.from_connection_string(conn_str)
with client.get_queue_receiver(queue_name="orders") as receiver:
    for msg in receiver:
        try:
            payload = json.loads(str(msg))
            process_order(payload)
            receiver.complete_message(msg)
        except PersistentError as exc:
            # Invia esplicitamente a DLQ con motivo
            receiver.dead_letter_message(
                msg,
                reason="PersistentProcessingError",
                error_description=str(exc),
            )
        except TransientError:
            # Rilascia il lock, Service Bus fara retry
            receiver.abandon_message(msg)

# Leggere dalla DLQ
with client.get_queue_receiver(
    queue_name="orders",
    sub_queue="deadletter",
) as dlq_receiver:
    for msg in dlq_receiver:
        print(f"DLQ msg: {msg}")
        print(f"  Reason: {msg.dead_letter_reason}")
        print(f"  Error: {msg.dead_letter_error_description}")
        # Analisi e replay manuale
```

---

## Poison Message Handling

### Cos'e un poison message

Un poison message e un messaggio che causa consistentemente il fallimento del consumer. Puo essere:

- Payload con formato invalido (JSON malformato, encoding sbagliato).
- Dati che violano invarianti del dominio (importo negativo, data nel futuro).
- Messaggio troppo grande per il consumer.
- Messaggio che causa un'eccezione non gestita (null reference, division by zero).
- Messaggio con dipendenze mancanti (riferimento a entita inesistente).

### Strategie di gestione

```python
import json
import hashlib
from datetime import datetime, timezone
from typing import Any

class PoisonMessageHandler:
    """
    Gestore centralizzato per poison message.
    Classifica, arricchisce e instrada messaggi problematici.
    """

    def __init__(self, dlq_publisher, parking_lot_publisher, metrics):
        self._dlq = dlq_publisher
        self._parking_lot = parking_lot_publisher
        self._metrics = metrics
        self._poison_registry: dict[str, int] = {}

    def classify_and_route(
        self,
        message: bytes,
        error: Exception,
        retry_count: int,
        max_retries: int,
    ) -> str:
        """
        Classifica il messaggio e lo instrada alla destinazione corretta.
        Ritorna: 'retry', 'dlq', 'parking_lot'
        """
        msg_hash = hashlib.sha256(message).hexdigest()[:16]

        # Rilevamento poison message ricorrente
        self._poison_registry[msg_hash] = (
            self._poison_registry.get(msg_hash, 0) + 1
        )

        # Se lo stesso messaggio fallisce ripetutamente in poco tempo,
        # e un poison message — DLQ diretto
        if self._poison_registry[msg_hash] > max_retries:
            self._metrics.increment("poison_message.detected")
            return self._send_to_dlq(
                message, error, "poison_message_detected"
            )

        # Classificazione errore
        if self._is_deserialization_error(error):
            return self._send_to_parking_lot(
                message, "deserialization_failed", error
            )

        if self._is_schema_error(error):
            return self._send_to_parking_lot(
                message, "schema_validation_failed", error
            )

        if self._is_transient_error(error) and retry_count < max_retries:
            return "retry"

        return self._send_to_dlq(
            message, error, "max_retries_exceeded"
        )

    def _is_deserialization_error(self, error: Exception) -> bool:
        return isinstance(
            error, (json.JSONDecodeError, UnicodeDecodeError)
        )

    def _is_schema_error(self, error: Exception) -> bool:
        return isinstance(error, (KeyError, TypeError, ValueError))

    def _is_transient_error(self, error: Exception) -> bool:
        return isinstance(
            error, (TimeoutError, ConnectionError, OSError)
        )

    def _send_to_dlq(
        self, message: bytes, error: Exception, reason: str
    ) -> str:
        envelope = {
            "original_message_b64": message.hex(),
            "reason": reason,
            "error_type": type(error).__name__,
            "error_message": str(error)[:1000],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._dlq.publish(json.dumps(envelope).encode())
        self._metrics.increment("dlq.messages_sent")
        return "dlq"

    def _send_to_parking_lot(
        self, message: bytes, reason: str, error: Exception
    ) -> str:
        envelope = {
            "original_message_b64": message.hex(),
            "reason": reason,
            "error_type": type(error).__name__,
            "error_message": str(error)[:1000],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._parking_lot.publish(json.dumps(envelope).encode())
        self._metrics.increment("parking_lot.messages_sent")
        return "parking_lot"
```

### Pattern: circuit breaker per poison message detection

Se lo stesso tipo di errore si verifica su N messaggi consecutivi, potrebbe indicare un problema sistemico piuttosto che un singolo poison message. In questo caso, il consumer dovrebbe fermarsi e attivare un alert:

```python
class PoisonCircuitBreaker:
    """
    Se N messaggi consecutivi falliscono con lo stesso errore,
    ferma il consumer e alerta.
    """

    def __init__(self, threshold: int = 5, alert_service=None):
        self._threshold = threshold
        self._consecutive_failures = 0
        self._last_error_type: str | None = None
        self._alert = alert_service

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._last_error_type = None

    def record_failure(self, error: Exception) -> bool:
        """
        Ritorna True se il circuit breaker e aperto
        (consumer deve fermarsi).
        """
        error_type = type(error).__name__
        if error_type == self._last_error_type:
            self._consecutive_failures += 1
        else:
            self._consecutive_failures = 1
            self._last_error_type = error_type

        if self._consecutive_failures >= self._threshold:
            if self._alert:
                self._alert.critical(
                    f"Circuit breaker aperto: {self._consecutive_failures} "
                    f"fallimenti consecutivi ({error_type})"
                )
            return True
        return False
```

---

## Retry Strategies

### Panoramica strategie di retry

| Strategia | Delay | Uso tipico | Pro | Contro |
|---|---|---|---|---|
| **Immediate** | 0 | Glitch istantaneo | Veloce | Puo sovraccaricare |
| **Fixed delay** | Costante (es. 5s) | Servizio con recovery noto | Prevedibile | Non adattivo |
| **Linear backoff** | N * base | Carico medio | Graduale | Lento per alti retry |
| **Exponential backoff** | base * 2^N | Servizi sotto carico | Anti-thundering herd | Delay lungo |
| **Exp. backoff + jitter** | (base * 2^N) + random | Standard raccomandato | Distribuisce carico | Imprevedibile |
| **Capped exponential** | min(base * 2^N, cap) | Produzione | Bounded | Richiede tuning cap |

### Implementazione Python

```python
import random
import time
from dataclasses import dataclass
from typing import Callable, Any

@dataclass(frozen=True)
class RetryConfig:
    """Configurazione immutabile per retry."""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    jitter: bool = True
    backoff_multiplier: float = 2.0
    retryable_exceptions: tuple[type[Exception], ...] = (
        TimeoutError,
        ConnectionError,
        OSError,
    )


def calculate_delay(config: RetryConfig, attempt: int) -> float:
    """Calcola il delay per il tentativo N."""
    # Exponential backoff
    delay = config.base_delay_seconds * (
        config.backoff_multiplier ** attempt
    )
    # Cap
    delay = min(delay, config.max_delay_seconds)
    # Jitter: random tra 0 e delay calcolato
    if config.jitter:
        delay = random.uniform(0, delay)
    return delay


def retry_with_dlq(
    func: Callable[..., Any],
    args: tuple,
    config: RetryConfig,
    dlq_handler: Callable[[bytes, Exception, int], None],
    message: bytes,
) -> Any:
    """
    Esegue func con retry. Dopo max_retries, invia a DLQ.
    """
    last_error: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            return func(*args)
        except config.retryable_exceptions as exc:
            last_error = exc
            if attempt < config.max_retries:
                delay = calculate_delay(config, attempt)
                print(
                    f"Retry {attempt + 1}/{config.max_retries} "
                    f"tra {delay:.2f}s: {exc}"
                )
                time.sleep(delay)
            else:
                print(
                    f"Max retry raggiunto ({config.max_retries}). "
                    f"Invio a DLQ."
                )
                dlq_handler(message, exc, config.max_retries)
                raise
        except Exception as exc:
            # Errore non retryable → DLQ diretto
            dlq_handler(message, exc, attempt)
            raise
```

### Delayed retry con code intermedie (RabbitMQ)

```
Tentativo 1: immediate
Tentativo 2: delay 5s   → retry-queue-5s  (TTL=5000ms → DLX → main)
Tentativo 3: delay 30s  → retry-queue-30s (TTL=30000ms → DLX → main)
Tentativo 4: delay 2min → retry-queue-2m  (TTL=120000ms → DLX → main)
Fallimento:  → DLQ finale
```

### Retry con Kafka — consumer pause/resume

In Kafka, il retry con delay puo essere implementato usando il pattern `pause/resume`:

```python
from confluent_kafka import Consumer

def retry_with_pause(consumer, topic, delay_seconds):
    """
    Pausa il consumer per delay_seconds prima di riprovare.
    Utile per errori transient che richiedono un cooldown.
    """
    partitions = consumer.assignment()
    consumer.pause(partitions)
    time.sleep(delay_seconds)
    consumer.resume(partitions)
```

Alternativa piu scalabile: topic di retry dedicati con timestamp header. Il consumer del retry topic controlla il timestamp e attende prima di elaborare.

---

## Circuit Breaker Integration

### DLQ + Circuit Breaker

Il circuit breaker protegge il sistema quando una dipendenza esterna e degradata. Integrato con DLQ, il pattern diventa:

```
Consumer riceve messaggio
       │
       ▼
Circuit breaker chiuso?
       │
       ├── Si → Elabora
       │         │
       │         ├── Successo → ACK, reset failure count
       │         └── Fallimento → Incrementa failure count
       │                          │
       │                    threshold raggiunto?
       │                          │
       │                          ├── Si → Apri circuit breaker
       │                          │         + Alert
       │                          └── No → Retry/DLQ standard
       │
       └── No (breaker aperto)
                  │
                  ▼
            Tempo half-open?
                  │
                  ├── No → NACK con requeue (o delay)
                  │         + Non conta come retry
                  └── Si → Prova 1 messaggio
                            │
                            ├── Successo → Chiudi breaker
                            └── Fallimento → Riapri breaker
```

### Implementazione

```python
import time
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock

class CircuitState(Enum):
    CLOSED = "closed"       # Normale, tutto funziona
    OPEN = "open"           # Fallimenti sopra soglia, stop
    HALF_OPEN = "half_open" # Test singolo messaggio

@dataclass
class CircuitBreaker:
    """
    Circuit breaker per consumer con integrazione DLQ.
    """
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 60.0
    half_open_max_calls: int = 1

    _state: CircuitState = field(
        default=CircuitState.CLOSED, init=False
    )
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _half_open_calls: int = field(default=0, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                elapsed = time.monotonic() - self._last_failure_time
                if elapsed >= self.recovery_timeout_seconds:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
            return self._state

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN

    def allow_request(self) -> bool:
        current = self.state
        if current == CircuitState.CLOSED:
            return True
        if current == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
            return False
        return False  # OPEN
```

---

## Monitoring e Alerting

### Metriche chiave per DLQ

| Metrica | Tipo | Alert threshold | Descrizione |
|---|---|---|---|
| `dlq.depth` | Gauge | > 0 (warn), > 100 (critical) | Messaggi nella DLQ |
| `dlq.rate` | Counter | > 10/min | Messaggi/min in DLQ |
| `dlq.oldest_message_age` | Gauge | > 1h (warn), > 24h (crit) | Eta del messaggio piu vecchio |
| `dlq.reprocessed` | Counter | — | Messaggi replay riusciti |
| `dlq.reprocess_failed` | Counter | > 0 | Messaggi replay falliti |
| `parking_lot.depth` | Gauge | > 0 | Messaggi nel parking lot |
| `main_queue.depth` | Gauge | > 10000 | Accumulo coda principale |
| `consumer.error_rate` | Rate | > 5% | Percentuale elaborazioni fallite |
| `circuit_breaker.state` | State | open | Stato circuit breaker |
| `retry.count` | Histogram | — | Distribuzione retry per messaggio |

### Dashboard operativa

```
┌─────────────────────────────────────────────────────────┐
│              DLQ Operations Dashboard                     │
├─────────────────┬───────────────────┬────────────────────┤
│  DLQ Depth      │  Parking Lot      │  Error Rate        │
│  ████████ 47    │  ██ 3             │  ██░░░ 2.1%        │
│                 │                   │                    │
│  Oldest: 4h     │  Oldest: 12h      │  Target: <1%       │
├─────────────────┴───────────────────┴────────────────────┤
│  DLQ Rate (last 24h)                                      │
│  ▁▂▁▁▁▁▁█████▃▂▁▁▁▁▁▁▁▁▁▁                               │
│  Spike at 11:00 - deploy v2.4.1                           │
├──────────────────────────────────────────────────────────┤
│  Top Error Types                                          │
│  1. TimeoutError (23 msgs)     → DB connection pool       │
│  2. ValidationError (15 msgs)  → Schema v3 mismatch       │
│  3. KeyError (9 msgs)          → Missing 'amount' field   │
├──────────────────────────────────────────────────────────┤
│  Circuit Breaker Status                                   │
│  orders-consumer: CLOSED  ✓                               │
│  payment-consumer: HALF_OPEN  ⚠                           │
│  notification-consumer: CLOSED  ✓                         │
└──────────────────────────────────────────────────────────┘
```

### Alerting con Prometheus/Grafana

```yaml
# prometheus_rules.yml
groups:
  - name: dlq_alerts
    rules:
      - alert: DLQDepthWarning
        expr: dlq_depth > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "DLQ contiene {{ $value }} messaggi"
          description: "La DLQ {{ $labels.queue }} ha messaggi non elaborati da 5+ minuti"

      - alert: DLQDepthCritical
        expr: dlq_depth > 100
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "DLQ critica: {{ $value }} messaggi"
          runbook: "https://wiki.internal/runbooks/dlq-critical"

      - alert: DLQOldestMessageAge
        expr: dlq_oldest_message_age_seconds > 86400
        labels:
          severity: critical
        annotations:
          summary: "DLQ ha messaggi vecchi di {{ $value | humanizeDuration }}"

      - alert: ParkingLotNotEmpty
        expr: parking_lot_depth > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Parking lot contiene {{ $value }} messaggi"
          description: "Messaggi non classificabili richiedono intervento manuale"
```

### Metriche Python con prometheus_client

```python
from prometheus_client import Counter, Gauge, Histogram

dlq_messages_total = Counter(
    "dlq_messages_total",
    "Messaggi totali inviati alla DLQ",
    ["queue", "error_type"],
)

dlq_depth = Gauge(
    "dlq_depth",
    "Numero messaggi nella DLQ",
    ["queue"],
)

dlq_oldest_age = Gauge(
    "dlq_oldest_message_age_seconds",
    "Eta in secondi del messaggio DLQ piu vecchio",
    ["queue"],
)

parking_lot_depth = Gauge(
    "parking_lot_depth",
    "Numero messaggi nel parking lot",
    ["queue"],
)

retry_count_histogram = Histogram(
    "message_retry_count",
    "Distribuzione numero di retry per messaggio",
    ["queue"],
    buckets=[0, 1, 2, 3, 5, 10],
)

reprocess_total = Counter(
    "dlq_reprocess_total",
    "Messaggi DLQ rielaborati",
    ["queue", "outcome"],  # outcome: success, failure
)
```

---

## Operational Playbook — DLQ Processing

### Playbook 1: DLQ depth > 0 (Warning)

```
TRIGGER: dlq_depth > 0 per 5+ minuti

STEP 1 — Triage
  - Controllare dashboard: quanti messaggi? Da quanto tempo?
  - Identificare error_type predominante.
  - Correlazione temporale: coincide con deploy, incidente, o cambio configurazione?

STEP 2 — Classificazione
  A) Errore transient risolto (es. DB era down, ora e up)
     → Replay immediato della DLQ.
  B) Bug nel consumer
     → Fix codice → deploy fix → replay DLQ.
  C) Dati invalidi da un producer specifico
     → Notificare team producer → decidere: fix dati + replay, o scartare.
  D) Schema evolution non backward compatible
     → Deploy consumer aggiornato → replay.

STEP 3 — Replay
  - Usare replay tool (CLI o UI).
  - Monitorare: i messaggi vengono elaborati con successo?
  - Se replay fallisce ancora → investigare ulteriormente.

STEP 4 — Post-mortem
  - Documentare causa, impatto, azioni correttive.
  - Aggiornare alert threshold se necessario.
  - Aggiungere test per il caso specifico.
```

### Playbook 2: DLQ depth crescita rapida (Critical)

```
TRIGGER: dlq_rate > 50/min O dlq_depth > 100

STEP 1 — Contenimento immediato
  - Verificare se il consumer sta funzionando.
  - Verificare dipendenze esterne (DB, API, rete).
  - Se dipendenza down → attivare circuit breaker manualmente.

STEP 2 — Fermare l'emorragia
  - Se il problema e nel consumer: rollback al deploy precedente.
  - Se il problema e nei dati: fermare il producer se possibile.
  - Se il problema e infrastrutturale: escalation a ops/SRE.

STEP 3 — Risoluzione
  - Fix root cause.
  - Deploy fix.
  - Replay DLQ gradualmente (rate limited).

STEP 4 — Validazione
  - Monitorare per 30 min: nessun nuovo messaggio in DLQ?
  - Tutti i messaggi DLQ elaborati con successo?
  - Metriche business: dati mancanti? Ordini persi?
```

### Playbook 3: Parking lot non vuoto

```
TRIGGER: parking_lot_depth > 0

STEP 1 — Analisi messaggi
  - Esaminare i messaggi: che tipo sono? Da dove vengono?
  - Identificare pattern: stesso producer? Stesso event_type?

STEP 2 — Azione
  A) Nuovo event_type da producer aggiornato
     → Aggiornare consumer per gestire il nuovo tipo.
     → Deploy → replay parking lot.
  B) Messaggio corrotto/malformato
     → Notificare il producer.
     → Scartare il messaggio dopo documentazione.
  C) Bug nel router/classificatore
     → Fix router → replay parking lot.

STEP 3 — Prevenzione
  - Aggiungere schema validation al producer.
  - Contract testing tra producer e consumer.
  - Schema registry per evoluzione controllata.
```

---

## Reprocessing Workflows

### CLI Replay Tool

```python
#!/usr/bin/env python3
"""
DLQ Replay Tool — CLI per gestire messaggi nella Dead Letter Queue.

Uso:
  python dlq_replay.py list --queue orders.dlq
  python dlq_replay.py inspect --queue orders.dlq --msg-id abc123
  python dlq_replay.py replay --queue orders.dlq --target orders.process
  python dlq_replay.py replay --queue orders.dlq --msg-id abc123
  python dlq_replay.py discard --queue orders.dlq --msg-id abc123 --reason "dati test"
"""

import argparse
import json
import pika
from datetime import datetime, timezone
from typing import Any


class DLQReplayTool:
    def __init__(self, host: str = "localhost"):
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host)
        )
        self._channel = self._connection.channel()

    def list_messages(
        self, queue: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Elenca messaggi nella DLQ senza rimuoverli."""
        messages = []
        for _ in range(limit):
            method, properties, body = self._channel.basic_get(
                queue=queue, auto_ack=False
            )
            if method is None:
                break
            messages.append(
                {
                    "delivery_tag": method.delivery_tag,
                    "message_id": properties.message_id,
                    "headers": properties.headers,
                    "timestamp": properties.timestamp,
                    "body_preview": body[:200].decode(
                        errors="replace"
                    ),
                    "body_size": len(body),
                }
            )
            # Nack con requeue per non perdere il messaggio
            self._channel.basic_nack(
                delivery_tag=method.delivery_tag, requeue=True
            )
        return messages

    def replay_single(
        self, queue: str, target_queue: str, message_id: str
    ) -> bool:
        """Replay di un singolo messaggio dalla DLQ."""
        while True:
            method, properties, body = self._channel.basic_get(
                queue=queue, auto_ack=False
            )
            if method is None:
                print(f"Messaggio {message_id} non trovato")
                return False

            if properties.message_id == message_id:
                # Pubblica nella coda target
                replay_headers = {
                    **(properties.headers or {}),
                    "x-replayed-from": queue,
                    "x-replayed-at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "x-retry-count": 0,  # Reset retry
                }
                self._channel.basic_publish(
                    exchange="",
                    routing_key=target_queue,
                    body=body,
                    properties=pika.BasicProperties(
                        headers=replay_headers,
                        delivery_mode=2,
                        message_id=properties.message_id,
                    ),
                )
                self._channel.basic_ack(
                    delivery_tag=method.delivery_tag
                )
                print(
                    f"Replayed: {message_id} → {target_queue}"
                )
                return True
            else:
                self._channel.basic_nack(
                    delivery_tag=method.delivery_tag, requeue=True
                )

    def replay_all(
        self,
        queue: str,
        target_queue: str,
        rate_limit: int = 10,
    ) -> dict[str, int]:
        """Replay di tutti i messaggi con rate limiting."""
        stats = {"replayed": 0, "failed": 0}
        while True:
            method, properties, body = self._channel.basic_get(
                queue=queue, auto_ack=False
            )
            if method is None:
                break

            try:
                replay_headers = {
                    **(properties.headers or {}),
                    "x-replayed-from": queue,
                    "x-replayed-at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "x-retry-count": 0,
                }
                self._channel.basic_publish(
                    exchange="",
                    routing_key=target_queue,
                    body=body,
                    properties=pika.BasicProperties(
                        headers=replay_headers,
                        delivery_mode=2,
                        message_id=properties.message_id,
                    ),
                )
                self._channel.basic_ack(
                    delivery_tag=method.delivery_tag
                )
                stats["replayed"] += 1
            except Exception as exc:
                self._channel.basic_nack(
                    delivery_tag=method.delivery_tag, requeue=True
                )
                stats["failed"] += 1
                print(f"Errore replay: {exc}")

            # Rate limiting
            if stats["replayed"] % rate_limit == 0:
                import time
                time.sleep(1)

        return stats

    def discard(
        self, queue: str, message_id: str, reason: str
    ) -> bool:
        """
        Scarta un messaggio dalla DLQ con motivo documentato.
        Il messaggio viene loggato prima della rimozione.
        """
        while True:
            method, properties, body = self._channel.basic_get(
                queue=queue, auto_ack=False
            )
            if method is None:
                return False

            if properties.message_id == message_id:
                # Log prima di scartare (audit trail)
                discard_record = {
                    "action": "dlq_discard",
                    "message_id": message_id,
                    "queue": queue,
                    "reason": reason,
                    "discarded_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "body_hash": __import__("hashlib").sha256(
                        body
                    ).hexdigest(),
                }
                print(f"DISCARD LOG: {json.dumps(discard_record)}")

                self._channel.basic_ack(
                    delivery_tag=method.delivery_tag
                )
                return True
            else:
                self._channel.basic_nack(
                    delivery_tag=method.delivery_tag, requeue=True
                )

    def close(self) -> None:
        self._connection.close()
```

### Workflow di reprocessing sicuro

```
                        ┌─────────────────┐
                        │   DLQ Messages    │
                        └────────┬─────────┘
                                 │
                          ┌──────┴──────┐
                          │   Triage     │
                          │   (manuale)  │
                          └──────┬──────┘
                                 │
               ┌─────────────────┼─────────────────┐
               │                 │                 │
          ┌────┴────┐      ┌────┴────┐       ┌────┴────┐
          │ Replay   │      │ Fix +   │       │ Discard  │
          │ diretto  │      │ Replay  │       │ + Log    │
          └────┬────┘      └────┬────┘       └─────────┘
               │                │
               ▼                ▼
         ┌──────────┐    ┌──────────┐
         │ Main      │    │ Staging   │ ← Test prima
         │ Queue     │    │ Queue     │   del replay prod
         └──────────┘    └──────────┘
```

---

## Data Loss Prevention

### Principi

1. **Nessun messaggio puo essere perso silenziosamente.** Ogni messaggio ha un destino tracciabile.
2. **DLQ mai con auto-purge.** Retention esplicita, mai eliminazione automatica.
3. **Backup DLQ.** Snapshot periodici della DLQ per recovery.
4. **Audit trail per ogni operazione DLQ.** Replay, discard, modifica = loggato.
5. **Idempotenza nel consumer.** Il replay non deve causare duplicati.

### Checklist data loss prevention

```
Pre-produzione:
  □ DLQ configurata per ogni coda
  □ Parking lot configurato per messaggi non classificabili
  □ Retention DLQ >= 14 giorni
  □ Alerting DLQ depth > 0
  □ Replay tool funzionante e testato
  □ Consumer idempotente (replay sicuro)
  □ Backup/snapshot DLQ automatico

Runtime:
  □ Monitoring DLQ depth attivo
  □ Alert su DLQ non silenziate
  □ Playbook DLQ documentato e accessibile
  □ Rotazione on-call conosce procedura DLQ

Post-incidente:
  □ Tutti i messaggi DLQ contabilizzati
  □ Replay completato o messaggi scartati con motivo
  □ Root cause analizzata
  □ Test aggiunto per il caso specifico
```

### Pattern: DLQ shadow copy

Per sicurezza aggiuntiva, ogni messaggio che entra nella DLQ viene anche scritto in uno storage permanente (S3, database) come backup:

```python
import json
import boto3
from datetime import datetime, timezone

s3 = boto3.client("s3")
DLQ_BACKUP_BUCKET = "dlq-backup"


def backup_dlq_message(
    queue_name: str,
    message_id: str,
    body: bytes,
    headers: dict,
) -> str:
    """Backup messaggio DLQ su S3."""
    now = datetime.now(timezone.utc)
    key = (
        f"{queue_name}/{now.strftime('%Y/%m/%d')}/"
        f"{message_id}.json"
    )
    record = {
        "message_id": message_id,
        "queue": queue_name,
        "body": body.decode(errors="replace"),
        "headers": headers,
        "backed_up_at": now.isoformat(),
    }
    s3.put_object(
        Bucket=DLQ_BACKUP_BUCKET,
        Key=key,
        Body=json.dumps(record).encode(),
        ContentType="application/json",
    )
    return f"s3://{DLQ_BACKUP_BUCKET}/{key}"
```

---

## DLQ nelle piattaforme workflow

### n8n

n8n non ha una DLQ nativa, ma il pattern si implementa con:

1. **Error Workflow:** un workflow separato triggerato quando il workflow principale fallisce.
2. **Data Store / Postgres:** salvare i dati falliti per replay manuale.
3. **Webhook per replay:** esporre un endpoint che ri-esegue i dati falliti.

```
Workflow principale
       │
       ├── Successo → continua
       │
       └── Errore → Error Trigger (workflow separato)
                         │
                         ├── Salva in Postgres (tabella dlq_items)
                         ├── Invia alert (Slack/email)
                         └── Log strutturato
```

### Make (ex Integromat)

- **Error Handler module:** collegato a ogni scenario come fallback.
- **Data Store:** utilizzabile come DLQ persistente.
- **Webhook custom:** per replay via API.

```
Scenario Make
  Module 1 → Module 2 → Module 3
       │          │          │
       └──────────┴──────────┘
                  │
           Error Handler
                  │
           ├── Data Store (insert record con errore)
           ├── Slack notification
           └── Log
```

### Zapier

Zapier ha capacita DLQ limitate:

- **Zap History:** mostra le esecuzioni fallite con dati.
- **Replay:** possibile dalla UI per singole esecuzioni.
- **Limitazione:** nessuna DLQ programmabile; per workflow critici, integrare con tool esterno.

### Apache Airflow

- **Task retry:** configurabile per task (`retries`, `retry_delay`, `retry_exponential_backoff`).
- **Callback:** `on_failure_callback` per gestione custom.
- **Dead letter:** implementabile come task separato che raccoglie dati falliti.

```python
# Airflow DAG con retry e DLQ
from airflow.decorators import dag, task
from datetime import timedelta

@dag(schedule="@hourly")
def order_processing():

    @task(
        retries=3,
        retry_delay=timedelta(seconds=30),
        retry_exponential_backoff=True,
        max_retry_delay=timedelta(minutes=10),
        on_failure_callback=send_to_dlq,
    )
    def process_orders():
        # elaborazione
        pass

    process_orders()
```

---

## Esempi di codice Python

### Esempio completo: consumer RabbitMQ con DLQ, parking lot, circuit breaker

```python
#!/usr/bin/env python3
"""
Consumer RabbitMQ completo con:
- DLQ per errori dopo max retry
- Parking lot per messaggi non classificabili
- Circuit breaker per protezione da cascading failure
- Metriche Prometheus
- Logging strutturato
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import pika
from prometheus_client import Counter, Gauge, start_http_server


# --- Configurazione ---

@dataclass(frozen=True)
class ConsumerConfig:
    rabbitmq_host: str = "localhost"
    main_queue: str = "orders.process"
    dlq_queue: str = "orders.dlq"
    parking_lot_queue: str = "orders.parking-lot"
    max_retries: int = 3
    prefetch_count: int = 10
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


# --- Metriche ---

messages_processed = Counter(
    "consumer_messages_processed_total",
    "Messaggi elaborati con successo",
    ["queue"],
)
messages_failed = Counter(
    "consumer_messages_failed_total",
    "Messaggi falliti",
    ["queue", "error_type"],
)
messages_dlq = Counter(
    "consumer_messages_dlq_total",
    "Messaggi inviati alla DLQ",
    ["queue"],
)
messages_parking_lot = Counter(
    "consumer_messages_parking_lot_total",
    "Messaggi inviati al parking lot",
    ["queue"],
)
circuit_breaker_state = Gauge(
    "consumer_circuit_breaker_state",
    "Stato circuit breaker (0=closed, 1=half_open, 2=open)",
    ["queue"],
)

# --- Logger ---

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)


# --- Circuit Breaker ---

class CBState(Enum):
    CLOSED = 0
    HALF_OPEN = 1
    OPEN = 2


@dataclass
class SimpleCircuitBreaker:
    threshold: int = 5
    timeout: float = 60.0
    _state: CBState = field(default=CBState.CLOSED, init=False)
    _failures: int = field(default=0, init=False)
    _last_fail: float = field(default=0.0, init=False)

    @property
    def state(self) -> CBState:
        if self._state == CBState.OPEN:
            if time.monotonic() - self._last_fail >= self.timeout:
                self._state = CBState.HALF_OPEN
        return self._state

    def success(self) -> None:
        self._failures = 0
        self._state = CBState.CLOSED

    def failure(self) -> None:
        self._failures += 1
        self._last_fail = time.monotonic()
        if self._failures >= self.threshold:
            self._state = CBState.OPEN

    def can_proceed(self) -> bool:
        return self.state != CBState.OPEN


# --- Tipi di errore ---

class TransientError(Exception):
    pass

class PersistentError(Exception):
    pass

class UnknownEventError(Exception):
    pass


# --- Consumer ---

KNOWN_EVENT_TYPES = frozenset({
    "order.created",
    "order.updated",
    "order.cancelled",
    "order.refunded",
})


def process_event(payload: dict[str, Any]) -> None:
    """Logica di business — elabora l'evento."""
    event_type = payload["event_type"]
    order_id = payload.get("order_id", "unknown")
    logger.info(f"Elaborazione {event_type} per ordine {order_id}")
    # ... logica reale qui ...


def run_consumer(config: ConsumerConfig) -> None:
    """Avvia il consumer con tutte le protezioni."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config.rabbitmq_host)
    )
    channel = connection.channel()
    cb = SimpleCircuitBreaker(
        threshold=config.circuit_breaker_threshold,
        timeout=config.circuit_breaker_timeout,
    )

    def on_message(ch, method, properties, body):
        headers = properties.headers or {}
        retry_count = headers.get("x-retry-count", 0)
        msg_id = properties.message_id or "unknown"

        # Circuit breaker check
        if not cb.can_proceed():
            circuit_breaker_state.labels(
                queue=config.main_queue
            ).set(CBState.OPEN.value)
            logger.warning(
                f"Circuit breaker OPEN — nack con requeue: {msg_id}"
            )
            ch.basic_nack(
                delivery_tag=method.delivery_tag, requeue=True
            )
            time.sleep(5)  # Back-pressure
            return

        try:
            payload = json.loads(body)
            event_type = payload.get("event_type")

            # Parking lot: tipo sconosciuto
            if event_type not in KNOWN_EVENT_TYPES:
                _to_parking_lot(
                    ch, method, body, config,
                    f"unknown_event_type:{event_type}",
                )
                return

            process_event(payload)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            messages_processed.labels(
                queue=config.main_queue
            ).inc()
            cb.success()
            circuit_breaker_state.labels(
                queue=config.main_queue
            ).set(CBState.CLOSED.value)

        except json.JSONDecodeError:
            _to_parking_lot(
                ch, method, body, config,
                "json_decode_error",
            )

        except TransientError as exc:
            cb.failure()
            if retry_count < config.max_retries:
                _retry(ch, method, body, headers, config, retry_count)
            else:
                _to_dlq(ch, method, body, config, exc, retry_count)

        except PersistentError as exc:
            _to_dlq(ch, method, body, config, exc, retry_count)

        except Exception as exc:
            cb.failure()
            _to_dlq(ch, method, body, config, exc, retry_count)

    def _retry(ch, method, body, headers, config, retry_count):
        new_headers = {
            **headers,
            "x-retry-count": retry_count + 1,
            "x-last-retry-at": datetime.now(timezone.utc).isoformat(),
        }
        ch.basic_publish(
            exchange="",
            routing_key=config.main_queue,
            body=body,
            properties=pika.BasicProperties(
                headers=new_headers, delivery_mode=2,
            ),
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(
            f"Retry {retry_count + 1}/{config.max_retries}"
        )

    def _to_dlq(ch, method, body, config, exc, retry_count):
        dlq_headers = {
            "x-original-queue": config.main_queue,
            "x-error-type": type(exc).__name__,
            "x-error-message": str(exc)[:500],
            "x-retry-count": retry_count,
            "x-dead-letter-at": datetime.now(timezone.utc).isoformat(),
        }
        ch.basic_publish(
            exchange="",
            routing_key=config.dlq_queue,
            body=body,
            properties=pika.BasicProperties(
                headers=dlq_headers, delivery_mode=2,
            ),
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        messages_dlq.labels(queue=config.main_queue).inc()
        messages_failed.labels(
            queue=config.main_queue,
            error_type=type(exc).__name__,
        ).inc()
        logger.warning(f"Messaggio inviato a DLQ: {exc}")

    def _to_parking_lot(ch, method, body, config, reason):
        pl_headers = {
            "x-original-queue": config.main_queue,
            "x-parking-reason": reason,
            "x-parked-at": datetime.now(timezone.utc).isoformat(),
        }
        ch.basic_publish(
            exchange="",
            routing_key=config.parking_lot_queue,
            body=body,
            properties=pika.BasicProperties(
                headers=pl_headers, delivery_mode=2,
            ),
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        messages_parking_lot.labels(queue=config.main_queue).inc()
        logger.warning(f"Messaggio in parking lot: {reason}")

    channel.basic_qos(prefetch_count=config.prefetch_count)
    channel.basic_consume(
        queue=config.main_queue, on_message_callback=on_message
    )

    logger.info(f"Consumer avviato su {config.main_queue}")
    start_http_server(8000)  # Prometheus metrics
    channel.start_consuming()


if __name__ == "__main__":
    run_consumer(ConsumerConfig())
```

---

## Esercizi

### Esercizio 1 — Lab: RabbitMQ DLQ (90 min)

Configura un sistema RabbitMQ con:

1. Coda principale `orders.process` con DLX configurato.
2. DLQ `orders.dlq` con retention 7 giorni.
3. Consumer Python che:
   - Elabora messaggi JSON con campo `order_id`.
   - Simula errori casuali (30% failure rate).
   - Retry fino a 3 volte con delay crescente.
   - Dopo 3 retry → DLQ.
4. Producer che invia 50 messaggi di test.
5. Verifica che i messaggi falliti finiscano nella DLQ con header corretti.

### Esercizio 2 — Lab: Replay Tool CLI (60 min)

Implementa un CLI tool che:

1. `list` — elenca messaggi nella DLQ con preview del contenuto.
2. `inspect <msg-id>` — mostra dettagli completi di un messaggio.
3. `replay <msg-id>` — re-inietta un singolo messaggio nella coda principale.
4. `replay-all` — re-inietta tutti i messaggi con rate limiting.
5. `discard <msg-id> --reason "..."` — rimuove un messaggio con motivo loggato.

### Esercizio 3 — Lab: Parking Lot (60 min)

1. Aggiungi al consumer dell'Esercizio 1 un parking lot per messaggi con `event_type` sconosciuto.
2. Invia 10 messaggi con `event_type` valido e 5 con tipo sconosciuto.
3. Verifica che i messaggi sconosciuti finiscano nel parking lot, non nella DLQ.
4. Implementa alert quando il parking lot non e vuoto.

### Esercizio 4 — Lab: Monitoring Dashboard (60 min)

1. Aggiungi metriche Prometheus al consumer (depth, rate, error_type).
2. Configura Grafana con dashboard che mostra:
   - DLQ depth nel tempo.
   - Error rate per tipo.
   - Parking lot depth.
3. Configura alert Prometheus per DLQ > 0 e parking lot > 0.

### Esercizio 5 — Stretch: n8n Error Workflow (avanzato)

1. Workflow principale n8n che elabora webhook.
2. Error workflow che:
   - Salva dati falliti in PostgreSQL (tabella `dlq_items`).
   - Invia notifica Slack.
   - Espone webhook per replay manuale.
3. UI semplice (o CLI) per visualizzare e replay items dalla tabella `dlq_items`.

---

## Troubleshooting — 20 problemi comuni

### Problema 1: messaggi scompaiono senza finire in DLQ

**Sintomo:** il producer invia messaggi, il consumer non li elabora, ma la DLQ e vuota.

**Cause possibili:**
- DLX non configurato sulla coda principale.
- La DLQ o la coda DLX non esistono.
- Il consumer fa `basic_ack` anche in caso di errore (ack prematuro).
- TTL della coda impostato troppo basso senza DLX.

**Soluzione:** verificare la configurazione della coda con `rabbitmqctl list_queues name arguments`. Controllare che `x-dead-letter-exchange` sia presente. Verificare il codice consumer: l'ack deve avvenire solo dopo elaborazione riuscita.

---

### Problema 2: messaggi in loop infinito tra coda e DLQ

**Sintomo:** un messaggio rimbalza continuamente tra la coda principale e la DLQ.

**Cause possibili:**
- La DLQ ha un DLX che punta alla coda principale (ciclo).
- Il replay tool non resetta il retry count.
- Il consumer non incrementa il retry count.

**Soluzione:** la DLQ non deve mai avere un DLX che punta alla coda principale. Il replay tool deve resettare `x-retry-count` a 0 quando re-inietta. Verificare con `rabbitmqctl list_queues name arguments` che la DLQ non abbia `x-dead-letter-exchange`.

---

### Problema 3: DLQ cresce senza controllo dopo deploy

**Sintomo:** dopo un deploy, la DLQ accumula centinaia di messaggi in pochi minuti.

**Cause possibili:**
- Bug nel nuovo deploy che causa fallimento su tutti i messaggi.
- Schema change non backward compatible.
- Dipendenza esterna non disponibile nel nuovo deploy.

**Soluzione:** rollback immediato al deploy precedente. Analizzare i messaggi DLQ per identificare il pattern. Fix del bug → nuovo deploy → replay DLQ.

---

### Problema 4: replay DLQ causa duplicati

**Sintomo:** dopo il replay, gli stessi dati appaiono due volte nel database.

**Cause possibili:**
- Consumer non idempotente.
- Il messaggio era stato parzialmente elaborato prima del fallimento.

**Soluzione:** implementare idempotenza nel consumer usando un idempotency key (message_id o hash del payload). Prima di elaborare, verificare se il messaggio e gia stato processato.

---

### Problema 5: consumer lento per messaggi DLQ

**Sintomo:** il consumer si rallenta significativamente quando la DLQ contiene molti messaggi.

**Cause possibili:**
- Consumer processa dalla DLQ e dalla coda principale sullo stesso thread.
- Retry delay troppo lungo blocca il consumer.
- Prefetch troppo alto su coda con messaggi problematici.

**Soluzione:** consumer separato per la DLQ. Non usare lo stesso consumer per coda principale e DLQ. Implementare retry con code dedicate (non sleep nel consumer).

---

### Problema 6: TTL scade prima che il consumer possa elaborare

**Sintomo:** messaggi finiscono nella DLQ per TTL expired, non per errore di elaborazione.

**Cause possibili:**
- TTL troppo aggressivo rispetto al throughput del consumer.
- Consumer troppo lento (bottleneck su dipendenza esterna).
- Spike di traffico che supera la capacita del consumer.

**Soluzione:** aumentare TTL o rimuoverlo se non necessario. Scalare il consumer (piu istanze). Monitorare queue depth vs consumer throughput.

---

### Problema 7: metriche DLQ inaccurate

**Sintomo:** la dashboard mostra depth DLQ diverso dal valore reale.

**Cause possibili:**
- Polling delle metriche troppo infrequente.
- Metriche calcolate dal consumer ma il consumer e fermo.
- Coda con messaggi unacknowledged che non vengono contati.

**Soluzione:** usare le metriche native del broker (RabbitMQ Management API, CloudWatch per SQS). Non fare affidamento su metriche calcolate dal consumer.

---

### Problema 8: DLQ piena (capacity reached)

**Sintomo:** nuovi messaggi DLQ vengono droppati perche la DLQ ha raggiunto `x-max-length`.

**Cause possibili:**
- DLQ con `x-max-length` troppo basso.
- Nessun processo di cleanup/replay automatico.
- Incidente prolungato che genera molti messaggi DLQ.

**Soluzione:** DLQ non dovrebbe avere `x-max-length` — o se lo ha, deve essere molto alto (milioni). Implementare backup automatico su storage esterno (S3). Alert quando DLQ depth supera l'80% della capacita.

---

### Problema 9: parking lot misto con messaggi DLQ

**Sintomo:** messaggi che dovrebbero andare in DLQ finiscono nel parking lot e viceversa.

**Cause possibili:**
- Classificazione errori incorretta nel consumer.
- Eccezioni non classificate correttamente (catch generico prima di catch specifico).

**Soluzione:** rivedere l'ordine dei blocchi except nel consumer. Le eccezioni specifiche (TransientError, PersistentError) devono essere catturate prima di Exception generica. Testare con messaggi di ogni tipo.

---

### Problema 10: replay parziale — alcuni messaggi falliscono di nuovo

**Sintomo:** dopo replay DLQ, alcuni messaggi vanno di nuovo nella DLQ.

**Cause possibili:**
- Fix incompleto — non tutti i casi sono coperti.
- Dati nel messaggio dipendono da stato esterno cambiato (es. utente cancellato).
- Race condition durante il replay.

**Soluzione:** replay in staging prima di produzione. Analizzare i messaggi che falliscono di nuovo — pattern diverso? Implementare replay selettivo per tipo di errore.

---

### Problema 11: circuit breaker si apre troppo presto

**Sintomo:** il circuit breaker si apre dopo pochi errori, fermando il consumer anche per errori sporadici.

**Cause possibili:**
- Threshold troppo basso.
- Il circuit breaker conta tutti gli errori, inclusi quelli non sistemici.

**Soluzione:** aumentare il threshold. Contare solo errori di tipo specifico (es. ConnectionError, TimeoutError) nel circuit breaker, non errori di validazione dati.

---

### Problema 12: messaggi DLQ senza metadati utili

**Sintomo:** i messaggi nella DLQ non hanno informazioni sufficienti per diagnosticare il problema.

**Cause possibili:**
- Il consumer non arricchisce i messaggi con header di errore.
- RabbitMQ DLX non aggiunge automaticamente tutti i dettagli.

**Soluzione:** arricchire sempre i messaggi DLQ con header: `x-error-type`, `x-error-message`, `x-original-queue`, `x-retry-count`, `x-stack-trace`.

---

### Problema 13: DLQ su Kafka con consumer group offset issue

**Sintomo:** dopo replay dal DLT, il consumer non riceve i messaggi ripubblicati.

**Cause possibili:**
- Consumer group offset gia avanti rispetto ai messaggi ripubblicati.
- Topic DLT con retention scaduta.
- Consumer con `auto.offset.reset=latest` che salta i messaggi vecchi.

**Soluzione:** per replay Kafka, pubblicare i messaggi nel topic principale (non DLT). Verificare `auto.offset.reset` del consumer. Monitorare consumer lag.

---

### Problema 14: messaggi DLQ non deserializzabili

**Sintomo:** il replay tool non riesce a leggere i messaggi nella DLQ.

**Cause possibili:**
- Encoding cambiato tra versioni del producer.
- Compressione applicata al messaggio originale.
- Schema evolution senza backward compatibility.

**Soluzione:** la DLQ deve conservare il messaggio esattamente come ricevuto (byte per byte). Il replay tool deve gestire multipli encoding. Implementare schema registry per evoluzione controllata.

---

### Problema 15: AWS SQS DLQ non riceve messaggi

**Sintomo:** il consumer SQS fallisce ma i messaggi non appaiono nella DLQ.

**Cause possibili:**
- `RedrivePolicy` non configurata.
- `maxReceiveCount` troppo alto.
- Il consumer cancella il messaggio prima di elaborarlo (ack prematuro).
- DLQ in un'altra regione o account.

**Soluzione:** verificare `RedrivePolicy` con `GetQueueAttributes`. Assicurarsi che `delete_message` avvenga solo dopo elaborazione riuscita. DLQ deve essere nella stessa regione e account della coda sorgente.

---

### Problema 16: alert DLQ troppo rumorosi

**Sintomo:** alert continui per DLQ > 0, anche per 1-2 messaggi sporadici.

**Cause possibili:**
- Threshold troppo sensibile.
- Nessun filtro per errori attesi/noti.

**Soluzione:** alert con soglia e durata: "DLQ > 10 per 15 minuti" anziche "DLQ > 0". Creare alert separati per warning (> 0 per 5 min) e critical (> 100 per 2 min). Supprimere alert noti con label specifiche.

---

### Problema 17: DLQ depth non diminuisce dopo replay

**Sintomo:** il replay tool riporta successo, ma la DLQ depth rimane invariata.

**Cause possibili:**
- Il replay tool legge ma non fa ack dei messaggi DLQ.
- Nuovi messaggi arrivano nella DLQ durante il replay.
- Consumer non connesso alla DLQ corretta.

**Soluzione:** verificare che il replay tool faccia `basic_ack` dopo aver ripubblicato. Monitorare la rate di ingresso DLQ durante il replay. Verificare la connessione alla DLQ corretta.

---

### Problema 18: Azure Service Bus DLQ con messaggi locked

**Sintomo:** messaggi nella DLQ di Azure Service Bus non sono accessibili.

**Cause possibili:**
- Un altro consumer ha un lock attivo sui messaggi.
- Lock duration troppo lunga.
- Session-enabled queue con sessione non rilasciata.

**Soluzione:** attendere che il lock scada (`lock_duration`). Usare `renew_message_lock()` se serve piu tempo per l'analisi. Per queue session-enabled, usare session receiver.

---

### Problema 19: performance degradata con DLQ molto grande

**Sintomo:** il broker rallenta quando la DLQ contiene milioni di messaggi.

**Cause possibili:**
- DLQ senza retention — messaggi accumulati per mesi.
- DLQ indicizzata in modo non efficiente.

**Soluzione:** implementare retention sulla DLQ (es. 30 giorni). Archiviare messaggi vecchi su storage esterno prima della scadenza. Monitorare la dimensione della DLQ come metrica operativa.

---

### Problema 20: messaggi persi durante migrazione DLQ tra broker

**Sintomo:** durante la migrazione da un broker all'altro, alcuni messaggi DLQ non vengono trasferiti.

**Cause possibili:**
- Script di migrazione non gestisce tutti i formati.
- Messaggi con header non standard persi nella conversione.
- Rate limiting della migrazione troppo aggressivo.

**Soluzione:** conteggio pre-migrazione e post-migrazione per verifica. Backup completo della DLQ sorgente prima della migrazione. Migrazione con checksum per ogni messaggio. Test di migrazione in staging con dati reali.

---

## FAQ — 20 domande e risposte

### 1. Qual e la differenza tra DLQ e parking lot?

La DLQ raccoglie messaggi che hanno fallito l'elaborazione dopo N tentativi. Il consumer sa come gestirli ma l'elaborazione fallisce (bug, dipendenza down, dati invalidi). Il parking lot raccoglie messaggi che il sistema non sa come gestire — il tipo e sconosciuto, il formato e inatteso, non c'e un handler registrato. La DLQ puo beneficiare di retry automatico dopo un fix; il parking lot richiede sempre intervento umano per capire cosa fare con il messaggio.

### 2. Quanti retry prima di spostare in DLQ?

Dipende dal contesto. Regola pratica: 3-5 retry per errori transient, 0 retry per errori permanenti. Per servizi con SLA stretto, 3 retry con exponential backoff (1s, 5s, 30s). Per batch processing notturno, 5-10 retry con delay piu lunghi (1min, 5min, 30min). Misurare il tasso di successo per retry number e calibrare.

### 3. La DLQ deve avere un TTL?

Si. Una DLQ senza TTL accumula messaggi indefinitamente. Retention raccomandata: 14-30 giorni. Messaggi piu vecchi vengono archiviati su storage permanente (S3) prima della scadenza. Il TTL della DLQ deve essere significativamente piu lungo di quello della coda principale.

### 4. Come gestire DLQ in ambiente multi-tenant?

Opzioni: (A) Una DLQ per tenant — isolamento totale ma overhead di gestione. (B) Una DLQ condivisa con header `x-tenant-id` — piu semplice ma richiede filtri nel replay tool. (C) DLQ partizionata per tenant (Kafka). Scegliere in base al numero di tenant e ai requisiti di isolamento.

### 5. DLQ e idempotenza: come si collegano?

Il replay DLQ puo causare duplicati se il consumer non e idempotente. Implementare idempotenza con: (A) Idempotency key nel messaggio (message_id o hash payload). (B) Tabella di deduplicazione nel database. (C) Upsert anziche insert. Senza idempotenza, ogni replay e potenzialmente pericoloso.

### 6. Come testare il meccanismo DLQ?

Test necessari: (A) Unit test: consumer rejecta il messaggio dopo N retry. (B) Integration test: messaggio finisce effettivamente nella DLQ con header corretti. (C) E2E test: replay dalla DLQ funziona e il messaggio viene elaborato. (D) Chaos test: uccidi la dipendenza esterna e verifica che i messaggi vadano in DLQ senza perdita.

### 7. DLQ per webhook: come implementare?

Per webhook in ingresso: (A) Salvare il webhook raw in un buffer/database. (B) Elaborare in modo asincrono. (C) Se fallisce, seguire il pattern DLQ standard. (D) Esporre un endpoint di health check per il provider. Per webhook in uscita: (A) Code di retry con exponential backoff. (B) Dopo N fallimenti, DLQ + notifica all'admin. (C) Metriche sul delivery rate.

### 8. Posso usare un database come DLQ?

Si, e un pattern comune per workflow platform senza DLQ nativa. Tabella `dlq_items` con colonne: id, queue_source, payload, error_type, error_message, retry_count, created_at, status (pending/replayed/discarded). Pro: query flessibili, UI di gestione semplice. Contro: non ha le garanzie di ordering e delivery di un message broker.

### 9. Come gestire DLQ in microservizi con saga pattern?

In un saga, se uno step fallisce e il messaggio va in DLQ, la saga rimane in stato inconsistente. Opzioni: (A) Compensating transaction automatica per gli step precedenti. (B) DLQ-aware saga coordinator che monitora le DLQ di ogni servizio. (C) Timeout sulla saga che triggera compensazione se lo step non completa entro N minuti.

### 10. DLQ e GDPR: ci sono implicazioni?

Si. I messaggi nella DLQ possono contenere PII. Implicazioni: (A) La DLQ e soggetta alla stessa retention policy dei dati personali. (B) "Right to be forgotten" si applica anche ai messaggi DLQ. (C) Pseudonimizzare i dati PII prima di inviarli alla DLQ. (D) La DLQ deve essere protetta con gli stessi controlli di accesso dei dati di produzione.

### 11. Come dimensionare la DLQ?

Regola pratica: DLQ capacity = main queue capacity * expected_failure_rate * max_retention_days. Per una coda che processa 100k messaggi/giorno con 1% failure rate e 14 giorni retention: 100000 * 0.01 * 14 = 14000 messaggi max nella DLQ. Aggiungere margine per spike (3-5x).

### 12. DLQ e observability: come correlare?

Ogni messaggio DLQ deve includere `trace_id` e `correlation_id` dal messaggio originale. Questo permette di: (A) Cercare in Jaeger/Tempo la trace completa del messaggio fallito. (B) Correlare l'errore con log e metriche dello stesso periodo. (C) Capire il contesto completo del fallimento (quale step, quale dipendenza, quale richiesta originale).

### 13. Quando usare DLQ vs quando droppare il messaggio?

Mai droppare in produzione senza logging. Scenari accettabili per drop: (A) Messaggi di test/debug in ambiente non-prod. (B) Messaggi duplicati gia elaborati (idempotency check). (C) Messaggi con TTL business scaduto (es. notifica per evento passato). Anche nel drop, loggare il messaggio e il motivo.

### 14. Come migrare da un sistema senza DLQ a uno con DLQ?

Step: (A) Aggiungere DLQ alla configurazione del broker (non richiede downtime). (B) Aggiornare il consumer per gestire retry count e reject. (C) Deployare monitoring e alerting per DLQ. (D) Implementare replay tool. (E) Testare in staging con messaggi che causano errori noti. (F) Deploy in produzione.

### 15. DLQ per messaggi batch: come gestire?

Se un messaggio contiene un batch di 100 items e 1 item fallisce: (A) Inviare l'intero batch in DLQ → semplice ma spreca elaborazione. (B) Splittare il batch e inviare solo l'item fallito → efficiente ma complesso. (C) Pattern raccomandato: consumer elabora item per item, il batch intero va in DLQ solo se la maggioranza degli item fallisce. Altrimenti, logga gli item falliti e continua.

### 16. Come gestire DLQ in architettura serverless?

AWS Lambda + SQS: DLQ nativa con `RedrivePolicy`. Lambda + EventBridge: `DeadLetterConfig` su ogni regola. Lambda + Kinesis: `BisectBatchOnFunctionError` + `MaximumRetryAttempts`. Azure Functions: DLQ nativa per Service Bus e Storage Queue. Serverless aggiunge complessita per il replay — servono Lambda separate per il reprocessing.

### 17. Circuit breaker si apre: cosa succede ai messaggi?

Quando il circuit breaker si apre, il consumer smette di elaborare. I messaggi nella coda rimangono li (non vengono consumati). Non contano come retry e non vanno in DLQ. Quando il circuit breaker si chiude (dopo recovery della dipendenza), il consumer riprende l'elaborazione normale. Nessun messaggio perso.

### 18. Come gestire DLQ cross-region?

Pattern: DLQ locale per ogni region + replicazione asincrona verso una DLQ centralizzata per analisi. Non spostare messaggi DLQ cross-region per il replay — replay locale per ogni region. La DLQ centralizzata serve solo per monitoring e reporting aggregati.

### 19. Parking lot: quando svuotarlo?

Il parking lot va svuotato quando: (A) Il team ha analizzato i messaggi e capito il pattern. (B) Il consumer e stato aggiornato per gestire il nuovo tipo (→ replay). (C) I messaggi sono stati confermati come irrilevanti (→ discard con motivo). Mai svuotare il parking lot senza analisi. Ogni messaggio deve avere un destino documentato.

### 20. DLQ best practices riassunto?

(A) Una DLQ per coda, non una DLQ condivisa per tutte le code. (B) Retention 14-30 giorni con backup. (C) Alert su depth > 0 (warning) e > 100 (critical). (D) Replay tool pronto e testato prima di andare in produzione. (E) Consumer idempotente per replay sicuro. (F) Metadati ricchi nei messaggi DLQ. (G) Monitoring separato per DLQ e parking lot. (H) Playbook documentato per ogni scenario. (I) Test del meccanismo DLQ nel CI/CD. (J) Circuit breaker integrato per protezione da cascading failure.

---

## Auto-valutazione

1. DLQ vs parking lot: differenza e quando usare ciascuno.
2. DLQ alerting threshold: come definire per ambiente.
3. Replay tooling: feature minimi necessari.
4. Senza DLQ, cosa rischi in produzione?
5. Exponential backoff con jitter: perche il jitter e importante?
6. Circuit breaker + DLQ: come interagiscono?
7. Idempotenza: perche e essenziale per il replay?
8. RabbitMQ DLX: come configurare con routing key.
9. Kafka DLT: differenze rispetto alla DLQ nativa di RabbitMQ.
10. Poison message: come rilevare e gestire.

---

## Letture primarie consigliate

- AWS SQS — Dead-letter queues. https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
- RabbitMQ — Dead Letter Exchanges. https://www.rabbitmq.com/dlx.html
- Enterprise Integration Patterns — Dead Letter Channel. https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html
- Confluent — Dead Letter Queue for Kafka Connect. https://docs.confluent.io/platform/current/connect/concepts.html#dead-letter-queue
- Azure Service Bus — Dead-letter queues. https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues
- Marc Brooker — Exponential Backoff and Jitter. https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/

---

## Collegamenti incrociati

- Modulo 16 — `16-event-driven-architecture-pratica.md`.
- Modulo 17 — `17-retry-idempotency-pattern.md`.
- Modulo 23 — `23-osservabilita-workflow-otel.md` (monitoring DLQ con OTel).
- Modulo 24 — `24-audit-logging-compliance.md` (audit trail per operazioni DLQ).

---

## Glossario locale

| Termine | Definizione |
|---|---|
| **DLQ** | Dead Letter Queue — coda per messaggi falliti dopo max retry. |
| **DLX** | Dead Letter Exchange — exchange RabbitMQ per routing a DLQ. |
| **DLT** | Dead Letter Topic — topic Kafka equivalente a DLQ. |
| **Parking lot** | Coda per messaggi non classificabili/gestibili. |
| **Replay** | Re-iniezione di messaggi DLQ nella coda principale dopo fix. |
| **RedrivePolicy** | Configurazione AWS SQS per DLQ (maxReceiveCount + target ARN). |
| **Poison message** | Messaggio che causa fallimento consistente del consumer. |
| **Circuit breaker** | Pattern che interrompe l'elaborazione quando le failure superano una soglia. |
| **Exponential backoff** | Strategia di retry con delay che raddoppia ad ogni tentativo. |
| **Jitter** | Componente random aggiunta al delay per evitare thundering herd. |
| **Thundering herd** | Tutti i retry si risvegliano contemporaneamente, sovraccaricando il sistema. |
| **Schema evolution** | Aggiornamento del contratto eventi con backward/forward compatibility. |
| **Idempotenza** | Proprieta per cui l'elaborazione multipla dello stesso messaggio produce lo stesso risultato. |
| **Nack** | Negative acknowledgment — segnala fallimento elaborazione al broker. |
| **TTL** | Time To Live — tempo massimo prima che un messaggio scada. |
| **Prefetch** | Numero di messaggi che il broker invia al consumer prima di ricevere ack. |
| **Shadow copy** | Backup dei messaggi DLQ su storage permanente esterno. |
| **WORM** | Write Once Read Many — storage immutabile. |
