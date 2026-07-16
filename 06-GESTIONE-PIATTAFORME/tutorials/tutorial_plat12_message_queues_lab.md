# Tutorial: Message Queues — RabbitMQ, Kafka e Event-Driven Architecture — Lab Pratico

> **Documento di riferimento:** `12-message-queues.md`
> **Dominio:** Gestione Piattaforme — Messaging e Architettura Event-Driven
> **Ambito:** Pattern di messaging (task queue, event log, pub/sub), RabbitMQ 4.x (exchanges, binding, DLQ, retry), Apache Kafka 3.8 (topic, partition, consumer group, Schema Registry, Kafka UI), idempotenza consumer, architettura event-driven, consumer lag e monitoring, confronto RabbitMQ vs Kafka vs NATS
> **Durata lab:** 7-8 ore
> **Livello:** Avanzato — richiede Python 3.10+ e conoscenza base concorrenza
> **Prerequisiti:** Docker Engine 29.x con Docker Compose, Python 3.10+ con pip, Java 21+ opzionale per strumenti Kafka nativi
> **Ambiente:** RabbitMQ 4.x + Kafka 3.8 + Zookeeper-free KRaft + Schema Registry via Docker Compose

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI MESSAGE QUEUES LAB ===
echo "=== CHECK PREREQUISITI ==="

docker --version && echo "[OK] Docker disponibile" || echo "[FAIL] Docker richiesto"
docker compose version && echo "[OK] Docker Compose disponibile" || echo "[FAIL] Compose richiesto"
python3 --version && echo "[OK] Python disponibile" || echo "[FAIL] Python 3.10+ richiesto"

# Installare librerie Python
pip3 install pika==1.3.2 confluent-kafka==2.6.1 2>/dev/null && \
  echo "[OK] Librerie Python installate" || \
  echo "[INFO] Installare: pip3 install pika confluent-kafka"

# Porte necessarie
for port in 5672 15672 9092 8082 9021; do
  ss -tlnp 2>/dev/null | grep -q ":${port} " && \
    echo "[WARN] Porta ${port} occupata" || echo "[OK] Porta ${port} libera"
done

echo ""
echo "=== SETUP DIRECTORY LAB ==="
mkdir -p ~/mq-lab/{rabbitmq,kafka,scripts,producers,consumers}
cd ~/mq-lab

echo "[OK] Directory lab: ~/mq-lab"
```

### Architettura del Lab

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   MESSAGE QUEUES LAB                                      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  RABBITMQ 4.x  :5672(AMQP) / :15672(UI)                        │    │
│  │                                                                  │    │
│  │  exchange:orders (direct)                                        │    │
│  │  ├── queue: orders.new  → consumer (elabora ordini)            │    │
│  │  ├── queue: orders.dlq  → Dead Letter Queue (falliti)          │    │
│  │  └── queue: orders.retry → coda retry con TTL                  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  APACHE KAFKA 3.8 KRaft (senza Zookeeper) :9092                 │    │
│  │                                                                  │    │
│  │  topic: order-events (3 partizioni, replication 1)             │    │
│  │  topic: payment-events (3 partizioni)                           │    │
│  │  Schema Registry :8082 (Avro schema validation)                 │    │
│  │  Kafka UI :9021 (monitoring, consumer group lag)                │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## PART A: FONDAMENTI — Pattern di Messaging

> I sistemi di messaggistica nascono da un'esigenza fondamentale: disaccoppiare
> chi produce dati da chi li consuma. Senza un intermediario (il broker),
> il servizio A deve chiamare direttamente il servizio B — e se B è giù,
> A deve aspettare o gestire l'errore. Con un broker, A pubblica il messaggio
> e torna subito al suo lavoro; B lo processerà quando sarà pronto.
> Questo rende i sistemi più resilient, scalabili e flessibili.

---

### Concetto A1: Task Queue vs Event Log vs Pub/Sub

```
TRE PATTERN FONDAMENTALI:

1. TASK QUEUE (lavoro da fare):
   - Un messaggio viene elaborato da UN solo consumer
   - Una volta elaborato, viene rimosso dalla coda
   - Esempio: "elabora questo ordine", "invia questa email"
   - Tecnologie: RabbitMQ, SQS, Celery
   - Garanzia: at-least-once (può essere elaborato 2+ volte in caso di crash)
   → IDEMPOTENZA CONSUMER OBBLIGATORIA

2. EVENT LOG (registro di eventi):
   - Gli eventi vengono conservati sul disco per un periodo configurabile
   - Più consumer possono leggere lo stesso evento in modo indipendente
   - Ogni consumer ricorda la propria posizione (offset)
   - Esempio: "ordine creato", "pagamento ricevuto" → audit trail, replay
   - Tecnologie: Kafka, Kinesis
   - Garanzia: at-least-once per consumer (offset committato dopo elaborazione)

3. PUB/SUB (pubblicazione-sottoscrizione):
   - Un publisher invia a un topic, tutti i subscriber ricevono una copia
   - I subscriber non si influenzano (se A elabora lentamente, B non aspetta)
   - Esempio: notifiche in tempo reale, cache invalidation
   - Tecnologie: RabbitMQ (fanout exchange), SNS, GCP Pub/Sub
   - Garanzia: fire-and-forget (no durabilità garantita senza subscriber attivo)

CONFRONTO TECNOLOGIE:

                    RabbitMQ        Kafka           NATS
Paradigma:          Task + Pub/Sub  Event Log       Sub/Sub leggero
Persistenza:        Su disco        Su disco (log)  Memoria (JetStream = disco)
Retention:          Finché non ack  Configurabile   TTL
Consumer:           Push (broker→)  Pull (consumer→) Push
Throughput:         ~100K msg/s     ~1M msg/s       ~2M msg/s
Latenza:            ~1ms            ~5-10ms         <1ms
Schema:             No (by default) Schema Registry No
Replay:             No              Sì (da offset)  Solo con JetStream
HA:                 Mirroring       Replication     Clustering
Complessità:        Media           Alta            Bassa

QUANDO USARE:
  RabbitMQ: task dispatch (email, notifiche, background jobs), routing complesso
  Kafka:    event sourcing, audit trail, stream processing, dati ad alto volume
  NATS:     IoT, gaming, microservizi leggeri, edge computing
```

---

## PART B: RABBITMQ — TASK QUEUE CON DLQ

### Esercizio B1: Setup RabbitMQ

```bash
cd ~/mq-lab

cat > compose-rabbitmq.yaml << 'EOF'
name: "mq-lab-rabbitmq"

networks:
  mq-net:
    driver: bridge

services:
  rabbitmq:
    image: rabbitmq:4.0-management-alpine
    container_name: rabbitmq
    hostname: rabbitmq-lab
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: rabbitmq-lab-2026
      RABBITMQ_DEFAULT_VHOST: /lab
    ports:
      - "5672:5672"    # AMQP
      - "15672:15672"  # UI management
    volumes:
      - ./rabbitmq/definitions.json:/etc/rabbitmq/definitions.json:ro
      - ./rabbitmq/rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf:ro
    networks: [mq-net]
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 15s
      timeout: 10s
      retries: 5
    restart: unless-stopped
EOF

mkdir -p rabbitmq

# Configurazione RabbitMQ
cat > rabbitmq/rabbitmq.conf << 'EOF'
# RabbitMQ 4.x configuration

# Rete
listeners.tcp.default = 5672

# Limiti
vm_memory_high_watermark.relative = 0.6    # alert a 60% RAM
disk_free_limit.relative = 1.0             # alert quando disco < 1× RAM

# Logging
log.console = true
log.console.level = info

# Persistence
queue_index_embed_msgs_below = 4096        # messaggi <4KB embedded nell'indice

# Management plugin
management.load_definitions = /etc/rabbitmq/definitions.json
EOF

# Definizioni pre-configurate (exchange, queue, binding)
cat > rabbitmq/definitions.json << 'EOF'
{
  "rabbit_version": "4.0.0",
  "vhosts": [{"name": "/lab"}],
  "users": [
    {
      "name": "admin",
      "password_hash": "",
      "hashing_algorithm": "rabbit_password_hashing_sha256",
      "tags": ["administrator"],
      "limits": {}
    }
  ],
  "permissions": [
    {"user": "admin", "vhost": "/lab", "configure": ".*", "write": ".*", "read": ".*"}
  ],
  "exchanges": [
    {
      "name": "orders",
      "vhost": "/lab",
      "type": "direct",
      "durable": true,
      "auto_delete": false
    },
    {
      "name": "dead-letter",
      "vhost": "/lab",
      "type": "direct",
      "durable": true,
      "auto_delete": false
    }
  ],
  "queues": [
    {
      "name": "orders.new",
      "vhost": "/lab",
      "durable": true,
      "arguments": {
        "x-dead-letter-exchange": "dead-letter",
        "x-dead-letter-routing-key": "orders.dlq",
        "x-message-ttl": 86400000,
        "x-max-length": 100000
      }
    },
    {
      "name": "orders.dlq",
      "vhost": "/lab",
      "durable": true,
      "arguments": {}
    },
    {
      "name": "orders.retry",
      "vhost": "/lab",
      "durable": true,
      "arguments": {
        "x-dead-letter-exchange": "orders",
        "x-dead-letter-routing-key": "orders.new",
        "x-message-ttl": 30000
      }
    }
  ],
  "bindings": [
    {"source": "orders", "vhost": "/lab", "destination": "orders.new", "destination_type": "queue", "routing_key": "orders.new"},
    {"source": "dead-letter", "vhost": "/lab", "destination": "orders.dlq", "destination_type": "queue", "routing_key": "orders.dlq"},
    {"source": "orders", "vhost": "/lab", "destination": "orders.retry", "destination_type": "queue", "routing_key": "orders.retry"}
  ]
}
EOF

docker compose -f compose-rabbitmq.yaml up -d

echo "Attendo RabbitMQ..."
until docker exec rabbitmq rabbitmq-diagnostics -q ping 2>/dev/null; do
  sleep 3
done

echo "[OK] RabbitMQ 4.x operativo"
echo "[INFO] UI Management: http://localhost:15672 (admin:rabbitmq-lab-2026)"
```

---

### Esercizio B2: Producer e Consumer con DLQ

```bash
# Producer: crea ordini e li pubblica su RabbitMQ
cat > producers/order_producer.py << 'PYTHON'
"""Producer: crea eventi ordine e li pubblica su RabbitMQ."""
import json
import time
import uuid
import random
import pika
from datetime import datetime

RABBITMQ_URL = "amqp://admin:rabbitmq-lab-2026@localhost:5672/%2Flab"

def get_connection():
    params = pika.URLParameters(RABBITMQ_URL)
    params.heartbeat = 60
    params.blocked_connection_timeout = 300
    return pika.BlockingConnection(params)

def publish_order(channel, order_data: dict):
    """Pubblica un ordine con proprietà di persistenza."""
    channel.basic_publish(
        exchange="orders",
        routing_key="orders.new",
        body=json.dumps(order_data).encode("utf-8"),
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent,   # persistente su disco
            content_type="application/json",
            message_id=str(uuid.uuid4()),                  # ID univoco per dedup
            timestamp=int(time.time()),
            headers={
                "retry_count": 0,
                "source": "order-service"
            }
        )
    )

if __name__ == "__main__":
    conn = get_connection()
    channel = conn.channel()
    channel.confirm_delivery()   # Publisher Confirms: garantisce che il broker ha ricevuto

    print("Pubblicando 10 ordini...")
    for i in range(10):
        order = {
            "order_id": str(uuid.uuid4()),
            "customer_id": f"CUST-{random.randint(1000, 9999)}",
            "items": [
                {"product": f"Prodotto-{random.randint(1, 50)}", "qty": random.randint(1, 5)}
            ],
            "total": round(random.uniform(10, 500), 2),
            "currency": "EUR",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Ogni 5° ordine ha dati invalidi (per testare DLQ)
        if i % 5 == 4:
            order["total"] = -99.99  # valore invalido → consumer rifiuterà
        
        try:
            publish_order(channel, order)
            print(f"  [OK] Ordine {i+1}: {order['order_id'][:8]}... totale={order['total']}")
        except Exception as e:
            print(f"  [FAIL] Ordine {i+1}: {e}")
    
    conn.close()
    print("\n[OK] 10 ordini pubblicati")
PYTHON

# Consumer: elabora ordini con retry e DLQ
cat > consumers/order_consumer.py << 'PYTHON'
"""
Consumer: elabora ordini da RabbitMQ.
Pattern: at-least-once + idempotenza + retry esponenziale + DLQ
"""
import json
import time
import pika
import hashlib
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
)
logger = logging.getLogger(__name__)

RABBITMQ_URL = "amqp://admin:rabbitmq-lab-2026@localhost:5672/%2Flab"
MAX_RETRIES = 3

# Idempotency store (in produzione: Redis o DB)
processed_orders = set()


def is_duplicate(order_id: str) -> bool:
    """Controlla se l'ordine è già stato elaborato."""
    return order_id in processed_orders


def mark_processed(order_id: str):
    """Segna l'ordine come elaborato."""
    processed_orders.add(order_id)


def validate_order(order: dict) -> tuple[bool, str]:
    """Valida i dati dell'ordine."""
    if order.get("total", 0) <= 0:
        return False, f"Totale invalido: {order.get('total')}"
    if not order.get("customer_id"):
        return False, "customer_id mancante"
    if not order.get("items"):
        return False, "items vuoto"
    return True, "ok"


def process_order(channel, method, properties, body):
    """Callback principale: elabora un singolo messaggio."""
    try:
        order = json.loads(body.decode("utf-8"))
        order_id = order.get("order_id", "unknown")
        headers = properties.headers or {}
        retry_count = headers.get("retry_count", 0)
        
        logger.info(f"Ricevuto ordine {order_id[:8]}... (retry={retry_count})")
        
        # ── Idempotency check ─────────────────────────────────────────
        if is_duplicate(order_id):
            logger.info(f"Ordine duplicato ignorato: {order_id[:8]}...")
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # ── Validazione ────────────────────────────────────────────────
        valid, reason = validate_order(order)
        if not valid:
            if retry_count >= MAX_RETRIES:
                # Mandare in DLQ: troppi tentativi
                logger.error(f"Ordine {order_id[:8]}... → DLQ dopo {retry_count} retry: {reason}")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            # Retry con backoff: manda a orders.retry (TTL 30s → ritorna a orders.new)
            logger.warning(f"Ordine invalido, retry {retry_count+1}/{MAX_RETRIES}: {reason}")
            new_headers = {**headers, "retry_count": retry_count + 1}
            channel.basic_publish(
                exchange="orders",
                routing_key="orders.retry",
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent,
                    headers=new_headers
                )
            )
            channel.basic_ack(delivery_tag=method.delivery_tag)  # ack del messaggio originale
            return
        
        # ── Elaborazione ───────────────────────────────────────────────
        # Simulare elaborazione reale (latenza variabile)
        time.sleep(0.1)
        mark_processed(order_id)
        
        logger.info(
            f"Ordine elaborato: id={order_id[:8]}... "
            f"customer={order['customer_id']} totale=€{order['total']}"
        )
        
        # ── ACK solo dopo elaborazione riuscita ───────────────────────
        channel.basic_ack(delivery_tag=method.delivery_tag)
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON invalido: {e}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    except Exception as e:
        logger.error(f"Errore inaspettato: {e}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


if __name__ == "__main__":
    params = pika.URLParameters(RABBITMQ_URL)
    conn = pika.BlockingConnection(params)
    channel = conn.channel()
    
    # Prefetch: processa max 5 messaggi alla volta (backpressure)
    channel.basic_qos(prefetch_count=5)
    
    channel.basic_consume(
        queue="orders.new",
        on_message_callback=process_order
    )
    
    logger.info("Consumer avviato — in ascolto su orders.new...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    
    conn.close()
    logger.info(f"Consumer fermato. Elaborati: {len(processed_orders)} ordini unici.")
PYTHON

# Test del sistema completo
echo "Avviando il consumer in background..."
python3 consumers/order_consumer.py &
CONSUMER_PID=$!
sleep 2

echo "Pubblicando ordini..."
python3 producers/order_producer.py

echo "Attendo elaborazione (5 secondi)..."
sleep 5

# Vedere quanti messaggi nella DLQ
curl -s -u admin:rabbitmq-lab-2026 \
  "http://localhost:15672/api/queues/%2Flab/orders.dlq" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(f'DLQ: {d.get(\"messages\",0)} messaggi non elaborabili')" \
  2>/dev/null || echo "[INFO] UI disponibile: http://localhost:15672"

kill $CONSUMER_PID 2>/dev/null
```

---

## PART C: APACHE KAFKA — EVENT LOG

### Esercizio C1: Setup Kafka KRaft (senza Zookeeper)

```bash
cd ~/mq-lab

cat > compose-kafka.yaml << 'EOF'
name: "mq-lab-kafka"

networks:
  kafka-net:
    driver: bridge

volumes:
  kafka-data:

services:
  # Kafka 3.8 KRaft: non richiede più Zookeeper (deprecato in 3.7, rimosso in 4.0)
  kafka:
    image: confluentinc/cp-kafka:7.7.0
    container_name: kafka
    hostname: kafka-1
    environment:
      # KRaft mode
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_CONTROLLER_QUORUM_VOTERS: "1@kafka-1:9093"
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"   # UUID fisso per lab
      
      # Performance
      KAFKA_NUM_PARTITIONS: 3
      KAFKA_DEFAULT_REPLICATION_FACTOR: 1
      KAFKA_MIN_INSYNC_REPLICAS: 1
      KAFKA_LOG_RETENTION_HOURS: 168         # 7 giorni
      KAFKA_LOG_SEGMENT_BYTES: 1073741824    # 1GB per segment
      KAFKA_LOG_RETENTION_CHECK_INTERVAL_MS: 300000
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "false"  # non creare topic automaticamente!
      
      # JVM
      KAFKA_HEAP_OPTS: "-Xmx1G -Xms1G"
    ports:
      - "9092:9092"
    volumes:
      - kafka-data:/var/lib/kafka/data
    networks: [kafka-net]
    healthcheck:
      test: kafka-broker-api-versions --bootstrap-server localhost:9092 || exit 1
      interval: 30s
      timeout: 10s
      retries: 5

  # Schema Registry: validazione Avro/Protobuf/JSON Schema
  schema-registry:
    image: confluentinc/cp-schema-registry:7.7.0
    container_name: schema-registry
    depends_on: [kafka]
    environment:
      SCHEMA_REGISTRY_HOST_NAME: schema-registry
      SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: kafka:9092
      SCHEMA_REGISTRY_LISTENERS: http://0.0.0.0:8082
    ports:
      - "8082:8082"
    networks: [kafka-net]

  # Kafka UI: monitoring visuale (consumer lag, topic, config)
  kafka-ui:
    image: provectuslabs/kafka-ui:v0.7.2
    container_name: kafka-ui
    depends_on: [kafka, schema-registry]
    environment:
      KAFKA_CLUSTERS_0_NAME: lab-cluster
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
      KAFKA_CLUSTERS_0_SCHEMAREGISTRY: http://schema-registry:8082
      DYNAMIC_CONFIG_ENABLED: "true"
    ports:
      - "9021:8080"
    networks: [kafka-net]
EOF

docker compose -f compose-kafka.yaml up -d

echo "Attendo Kafka KRaft (30-60 secondi)..."
until docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>/dev/null; do
  sleep 5
done

echo "[OK] Kafka KRaft 3.8 operativo"
echo "[INFO] Kafka UI: http://localhost:9021"

# Creare topic con configurazioni appropriate
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --create \
  --topic order-events \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000 \     # 7 giorni
  --config compression.type=lz4 \      # compressione lz4
  --config min.insync.replicas=1

docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --create \
  --topic payment-events \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=2592000000     # 30 giorni (dati finanziari = retention più lunga)

docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --create \
  --topic order-events.dlq \
  --partitions 1 \
  --replication-factor 1 \
  --config retention.ms=-1             # retention infinita per DLQ

echo "[OK] Topic creati: order-events, payment-events, order-events.dlq"

# Listare i topic
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

---

### Esercizio C2: Producer e Consumer Kafka con Avro

```bash
# Registrare lo schema Avro per gli eventi ordine
cat > kafka/order-event-schema.avsc << 'EOF'
{
  "type": "record",
  "name": "OrderEvent",
  "namespace": "com.azienda.events",
  "fields": [
    {"name": "order_id", "type": "string"},
    {"name": "event_type", "type": {"type": "enum", "name": "EventType",
      "symbols": ["ORDER_CREATED", "ORDER_CONFIRMED", "ORDER_SHIPPED", "ORDER_DELIVERED", "ORDER_CANCELLED"]}},
    {"name": "customer_id", "type": "string"},
    {"name": "total_amount", "type": "float"},
    {"name": "currency", "type": "string", "default": "EUR"},
    {"name": "timestamp_ms", "type": "long"},
    {"name": "metadata", "type": {"type": "map", "values": "string"}, "default": {}}
  ]
}
EOF

# Registrare lo schema nel Schema Registry
SCHEMA_JSON=$(cat kafka/order-event-schema.avsc | python3 -c "import json,sys; print(json.dumps({'schema': sys.stdin.read()}))")
curl -s -X POST \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "$SCHEMA_JSON" \
  "http://localhost:8082/subjects/order-events-value/versions" | python3 -m json.tool

echo "[OK] Schema Avro registrato"

# Producer Python con serializzazione JSON (semplificato per lab — Avro richiederebbe fastavro)
cat > producers/kafka_producer.py << 'PYTHON'
"""Producer Kafka: pubblica eventi ordine con configurazioni produzione."""
import json
import uuid
import time
import random
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "order-events"

# Configurazione producer ottimizzata per produzione
producer_config = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    
    # Acknowledgment: attendere ack da leader replica
    # acks=all significa minimo min.insync.replicas devono ackare
    "acks": "all",
    
    # Retry automatici in caso di errori transitori
    "retries": 5,
    "retry.backoff.ms": 300,
    
    # Batching: aumenta throughput raggruppando messaggi
    "batch.size": 65536,          # 64KB per batch
    "linger.ms": 10,              # aspetta 10ms per riempire il batch
    
    # Compressione (riduce bandwidth e storage)
    "compression.type": "lz4",
    
    # Idempotenza: garantisce exactly-once per producer
    # (combinato con acks=all e retries)
    "enable.idempotence": True,
    
    # Timeouts
    "message.timeout.ms": 30000,
    "request.timeout.ms": 10000,
}

def delivery_callback(err, msg):
    """Chiamata dopo ogni messaggio inviato."""
    if err:
        print(f"[FAIL] Messaggio fallito: {err}")
    else:
        print(f"  [OK] topic={msg.topic()} partition={msg.partition()} offset={msg.offset()}")

producer = Producer(producer_config)

EVENT_TYPES = ["ORDER_CREATED", "ORDER_CONFIRMED", "ORDER_SHIPPED", "ORDER_DELIVERED"]

print(f"Pubblicando 10 eventi su topic '{TOPIC}'...")
for i in range(10):
    event = {
        "order_id": str(uuid.uuid4()),
        "event_type": random.choice(EVENT_TYPES),
        "customer_id": f"CUST-{random.randint(1000, 9999)}",
        "total_amount": round(random.uniform(10, 500), 2),
        "currency": "EUR",
        "timestamp_ms": int(time.time() * 1000),
        "metadata": {"source": "order-service", "version": "1.2.0"}
    }
    
    # Chiave = customer_id garantisce che tutti gli eventi dello stesso cliente
    # vadano sulla stessa partizione (mantiene ordine cronologico per cliente)
    producer.produce(
        TOPIC,
        key=event["customer_id"],
        value=json.dumps(event).encode("utf-8"),
        callback=delivery_callback
    )
    
    # Flush ogni 5 messaggi (non ogni singolo — più efficiente)
    if i % 5 == 4:
        producer.flush()

producer.flush()  # flush finale
print(f"\n[OK] {i+1} eventi pubblicati")
PYTHON

# Consumer Kafka con gestione lag e DLQ
cat > consumers/kafka_consumer.py << 'PYTHON'
"""
Consumer Kafka: at-least-once con gestione manuale degli offset.
Pattern: poll → process → commit offset (dopo successo)
"""
import json
import time
import logging
from confluent_kafka import Consumer, Producer, KafkaError, KafkaException

logging.basicConfig(level=logging.INFO,
    format='{"time":"%(asctime)s","msg":"%(message)s"}')
logger = logging.getLogger(__name__)

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "order-events"
DLQ_TOPIC = "order-events.dlq"
GROUP_ID = "order-processor-v1"

consumer_config = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "group.id": GROUP_ID,
    
    # FONDAMENTALE: non committare automaticamente!
    # Auto-commit potrebbe perdere messaggi se il consumer crasha dopo il commit
    # ma prima dell'elaborazione.
    "enable.auto.commit": False,
    
    # Da dove partire se non c'è offset salvato
    "auto.offset.reset": "earliest",
    
    # Heartbeat per rilevare consumer morti
    "session.timeout.ms": 30000,
    "heartbeat.interval.ms": 3000,
    "max.poll.interval.ms": 300000,    # max tempo per elaborare un batch
}

dlq_producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})


def send_to_dlq(key: bytes, value: bytes, error_reason: str):
    """Manda messaggio fallito nella Dead Letter Queue."""
    dlq_producer.produce(
        DLQ_TOPIC,
        key=key,
        value=value,
        headers={"error_reason": error_reason, "original_topic": TOPIC}
    )
    dlq_producer.flush()


def process_event(event: dict) -> bool:
    """
    Elabora un singolo evento. Ritorna True se successo, False se retry.
    Raises: ValueError per errori permanenti → DLQ
    """
    event_type = event.get("event_type")
    order_id = event.get("order_id", "unknown")
    
    if event.get("total_amount", 0) < 0:
        raise ValueError(f"total_amount negativo: {event['total_amount']}")
    
    # Simulare elaborazione
    time.sleep(0.05)
    logger.info(f"Elaborato: {event_type} ordine={order_id[:8]}...")
    return True


consumer = Consumer(consumer_config)
consumer.subscribe([TOPIC])

logger.info(f"Consumer avviato: topic={TOPIC} group={GROUP_ID}")
messages_processed = 0

try:
    while messages_processed < 20:  # processa max 20 in lab
        msg = consumer.poll(timeout=3.0)
        
        if msg is None:
            continue
        
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                logger.info(f"Partizione {msg.partition()} completata")
            else:
                raise KafkaException(msg.error())
            continue
        
        try:
            event = json.loads(msg.value().decode("utf-8"))
            process_event(event)
            
            # Commit manuale: solo DOPO elaborazione riuscita
            consumer.commit(message=msg, asynchronous=False)
            messages_processed += 1
        
        except ValueError as e:
            # Errore permanente → DLQ
            logger.error(f"Errore permanente → DLQ: {e}")
            send_to_dlq(msg.key(), msg.value(), str(e))
            consumer.commit(message=msg, asynchronous=False)
            messages_processed += 1
        
        except Exception as e:
            # Errore transitorio → NON committare (verrà riprocessato)
            logger.error(f"Errore transitorio, no commit: {e}")

except KeyboardInterrupt:
    pass

finally:
    consumer.close()
    logger.info(f"Consumer fermato. Elaborati: {messages_processed} messaggi.")
PYTHON

# Eseguire il demo completo
python3 producers/kafka_producer.py &
sleep 2
python3 consumers/kafka_consumer.py

# Vedere il consumer lag (quanti messaggi non ancora elaborati)
docker exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group order-processor-v1 \
  --describe \
  2>/dev/null | head -20

echo "[INFO] Kafka UI per monitoring: http://localhost:9021"
```

---

## PART D: MONITORING CONSUMER LAG

### Esercizio D1: Metriche e Alerting

```bash
# Consumer Lag: la metrica più importante per i consumer Kafka
# Lag = (offset massimo del topic) - (offset committato dal consumer)
# Lag crescente = consumer non ce la fa

cat << 'LAG_GUIDE'
═══════════════════════════════════════════════════════════════
CONSUMER LAG — GUIDA AL MONITORING
═══════════════════════════════════════════════════════════════

METRICHE CHIAVE:
  consumer_lag          = messages in queue non ancora processati
  records_consumed_rate = rate di consumo (msg/s)
  commit_rate           = frequenza dei commit offset
  
  Lag ideale: < 1000 (per dati non critici)
  Lag critico: > 10000 (alert!)
  Lag crescente: consumer troppo lento o morto

COMANDI kafka-consumer-groups:
  # Stato tutti i consumer groups
  kafka-consumer-groups --bootstrap-server localhost:9092 --list
  
  # Lag per consumer group
  kafka-consumer-groups --bootstrap-server localhost:9092 \
    --group order-processor-v1 --describe
  
  # Output:
  # GROUP              TOPIC          PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
  # order-processor-v1 order-events   0          15              15              0
  # order-processor-v1 order-events   1          12              14              2  ← lag!
  # order-processor-v1 order-events   2          8               8               0
  
  # Reset offset (per re-processare tutto dall'inizio)
  kafka-consumer-groups --bootstrap-server localhost:9092 \
    --group order-processor-v1 --topic order-events \
    --reset-offsets --to-earliest --execute

PROMETHEUS METRICS (se esposti via JMX Exporter):
  # Lag totale di tutti i group-topic-partition
  kafka_consumer_fetch_manager_records_lag_sum

ALERT PROMETHEUS:
  - alert: KafkaConsumerHighLag
    expr: kafka_consumer_fetch_manager_records_lag_sum > 10000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Consumer lag alto: {{ $labels.group }} {{ $value }} messaggi in arretrato"
═══════════════════════════════════════════════════════════════
LAG_GUIDE

# Verificare lag attuale
docker exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group order-processor-v1 \
  --describe \
  2>/dev/null
```

---

## Conclusioni e Prossimi Passi

```
MESSAGE QUEUES — RIEPILOGO:

SCEGLIERE LA TECNOLOGIA:
  ✓ RabbitMQ: task queue (email, notifiche), routing complesso,
               ogni messaggio da un solo consumer
  ✓ Kafka: event log, audit trail, replay, alta volumetria,
            più consumer indipendenti sullo stesso evento
  ✓ NATS: IoT, gaming, messaggi effimeri, latenza < 1ms

RABBITMQ:
  ✓ Exchange tipi: direct, topic, fanout, headers
  ✓ DLQ (Dead Letter Queue): messaggi rifiutati → DLQ per ispezione
  ✓ Retry queue con TTL: rimanda il messaggio dopo N secondi
  ✓ basic_qos prefetch_count: controlla il backpressure
  ✓ Publisher Confirms: garantisce ricezione dal broker
  ✓ basic_ack dopo elaborazione riuscita (NON prima!)

KAFKA:
  ✓ KRaft (Kafka 3.4+): senza Zookeeper (rimosso in 4.0)
  ✓ Partizioni: unità di parallelismo (più partizioni = più consumer paralleli)
  ✓ Consumer group: i consumer nel gruppo si dividono le partizioni
  ✓ enable.auto.commit = false: commit manuale per at-least-once
  ✓ Schema Registry: validazione schema Avro/Protobuf
  ✓ enable.idempotence = true: exactly-once per producer
  ✓ Chiave messaggio: stesso customer → stessa partizione (ordine garantito)

IDEMPOTENZA (fondamentale!):
  "Exactly-once è impossibile nei sistemi distribuiti.
   At-least-once + idempotenza consumer = effective exactly-once."
  ✓ Dedup via message_id + Redis/DB
  ✓ Operazioni idempotenti: INSERT ... ON CONFLICT DO NOTHING
  ✓ Upsert invece di insert puro

DLQ — REGOLA AUREA:
  ✓ SEMPRE configurare una DLQ
  ✓ Senza DLQ: messaggi falliti = silently lost o blocked queue
  ✓ DLQ deve avere: retention lunga, alert su messaggi presenti
  ✓ Processo di riprocessamento DLQ: fix bug → replay DLQ

CONSUMER LAG:
  ✓ Metrica fondamentale per Kafka
  ✓ Lag crescente = consumer troppo lento o morto
  ✓ Alert su lag > soglia configurabile
  ✓ Soluzione: più consumer nel group (fino a N=partizioni)
```

**Prossimi tutorial:**
- `tutorial_plat13_sicurezza_piattaforme_lab.md` — Falco, OPA, Kyverno, gitleaks
- `tutorial_plat15_secrets_management_lab.md` — Vault, External Secrets Operator

```bash
# Pulizia lab
docker compose -f compose-rabbitmq.yaml down -v
docker compose -f compose-kafka.yaml down -v
rm -rf ~/mq-lab

echo "[OK] Lab Message Queues completato"
```

---

> **Nota versioni:** Tutorial validato con RabbitMQ 4.0.x (ottobre 2024), Kafka/Confluent Platform 7.7.x
> (corrispondente a Kafka 3.7.x/3.8.x), Schema Registry 7.7.x, Kafka UI 0.7.2.
> KRaft mode: stabile da Kafka 3.3 (KIP-833), Zookeeper rimosso definitivamente in Kafka 4.0 (2025).
> RabbitMQ 4.0 (ottobre 2024): Classic Queue Mirroring rimosso (usare Quorum Queues per HA).
> Confluent Platform 7.7 = Apache Kafka 3.7 — verificare compatibilità API se si usa Apache Kafka puro.
