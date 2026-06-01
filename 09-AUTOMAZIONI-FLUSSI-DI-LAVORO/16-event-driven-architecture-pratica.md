---
corso: "Automazioni e Flussi di Lavoro"
fase: "5 — Pattern Avanzati"
modulo: 16
titolo: "Architettura Event-Driven per Automazioni — Pratica con RabbitMQ e Kafka"
versione: "RabbitMQ 3.13/4.x, Kafka 3.x/4.x"
livello: "competent → proficient"
prerequisiti:
  - "Modulo 04, 15"
  - "Concetti messaging (queue, topic, partition, consumer group)"
obiettivi:
  - "Scegliere tra RabbitMQ e Kafka in base a requisiti di task queue vs event log"
  - "Implementare pattern producer-consumer con acknowledgment manuale e retry"
  - "Configurare Dead Letter Queue per gestione errori e failure analysis"
  - "Progettare strategie di ordering, partitioning e backpressure per sistemi ad alto throughput"
  - "Applicare il pattern Saga per transazioni distribuite con compensation actions"
tag: [event-driven, rabbitmq, kafka, messaging, dlq, saga, producer-consumer, architettura]
---

# Architettura Event-Driven per Automazioni — Pratica con RabbitMQ e Kafka

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 4 — Pattern di affidabilita · Modulo 16
> **Prerequisiti:** Modulo 04, 15; messaging concepts (queue, topic, partition, consumer group).
> **Obiettivi:** scegliere RabbitMQ vs Kafka; pattern producer-consumer; DLQ; ordering; backpressure.
> **Tempo:** lettura 90 min · lab 360 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-24
> **Versioni:** RabbitMQ 3.13/4.x, Kafka 3.x/4.x.

## Idee guida

1. **RabbitMQ per task queue, Kafka per event log.** Use case diversi.
2. **Acknowledgment manuale > auto-ack.** Auto-ack perde messaggi su crash worker.
3. **DLQ (Dead Letter Queue) e mandatory.** Messaggi che falliscono N volte vanno in DLQ per analisi.
4. **Ordering richiede partition affinity.** In Kafka, messaggi stessa key vanno alla stessa partition.
5. **Backpressure: prefetch limit, consumer scaling, rate limit.**

---

## Indice

- [Panoramica](#panoramica)
- [Concetti Fondamentali](#concetti-fondamentali)
- [Event-Driven vs Request/Response](#event-driven-vs-requestresponse)
- [Pattern Event-Driven Fondamentali](#pattern-event-driven-fondamentali)
- [Pub/Sub vs Point-to-Point Queue](#pubsub-vs-point-to-point-queue)
- [RabbitMQ Deep Dive](#rabbitmq-deep-dive)
- [Apache Kafka Deep Dive](#apache-kafka-deep-dive)
- [Redis Streams come Alternativa Lightweight](#redis-streams-come-alternativa-lightweight)
- [Confronto RabbitMQ vs Kafka vs NATS vs Redis Streams](#confronto-rabbitmq-vs-kafka-vs-nats-vs-redis-streams)
- [Schema Registry e Schema Evolution](#schema-registry-e-schema-evolution)
- [Event Schema Design e CloudEvents](#event-schema-design-e-cloudevents)
- [Outbox Pattern e CDC con Debezium](#outbox-pattern-e-cdc-con-debezium)
- [Saga Pattern per Workflow Long-Running](#saga-pattern-per-workflow-long-running)
- [Idempotency Consumer-Side](#idempotency-consumer-side)
- [Retry, DLQ e Parking Lot Pattern](#retry-dlq-e-parking-lot-pattern)
- [Monitoring e Observability](#monitoring-e-observability)
- [Esempio: Pipeline Ordini E-commerce PMI](#esempio-pipeline-ordini-e-commerce-pmi)
- [Esempio: CDC Postgres → Kafka → Warehouse](#esempio-cdc-postgres--kafka--warehouse)
- [Esempio: Integrazione SDI Fatturazione Elettronica](#esempio-integrazione-sdi-fatturazione-elettronica)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

L'architettura event-driven (EDA) è un paradigma di progettazione in cui i componenti del sistema comunicano attraverso eventi — fatti immutabili che descrivono qualcosa che è accaduto nel passato — anziché tramite chiamate sincrone richiesta/risposta. Un evento è tipicamente strutturato come `OrderPlaced`, `PaymentReceived`, `InvoiceIssued`, e viene pubblicato su un message broker che si occupa di consegnarlo a tutti i consumatori interessati. Questa separazione tra produttore e consumatore — il primo non conosce chi riceverà l'evento e quando, il secondo non conosce chi lo ha generato — è il cardine del decoupling che rende EDA particolarmente adatta a sistemi distribuiti complessi, microservizi, pipeline di automazione e integrazioni B2B.

Nel contesto delle automazioni, l'event-driven architecture risolve problemi che le pipeline batch o le chiamate API sincrone faticano a gestire: integrazione di sistemi eterogenei con cadenze diverse (un ERP che esporta ogni notte vs un e-commerce che riceve ordini in real-time), workflow long-running che attraversano più servizi e più giorni (onboarding cliente, ciclo ordine-spedizione-fattura), fan-out di eventi a molti consumatori (un singolo evento "fattura emessa" deve aggiornare CRM, contabilità, sistema di reportistica e notificare il cliente). Le piattaforme low-code come n8n e Make supportano nativamente i webhook ma diventano fragili quando il volume cresce o quando serve garantire che nessun evento venga perso; in questi scenari, un message broker dedicato come RabbitMQ o Kafka diventa indispensabile.

Questa guida copre i pattern fondamentali dell'event-driven architecture, le caratteristiche operative dei principali message broker open source — RabbitMQ, Apache Kafka, NATS e Redis Streams — e fornisce esempi concreti calati nel contesto italiano: pipeline ordini per PMI e-commerce, change data capture da PostgreSQL verso un data warehouse, integrazione con il Sistema di Interscambio (SDI) per la fatturazione elettronica B2B. L'obiettivo è fornire le chiavi decisionali per scegliere tecnologia e pattern in funzione del volume, delle garanzie di consegna richieste e della complessità operativa che il team può sostenere.

---

## Concetti Fondamentali

Un **evento** è un record immutabile di qualcosa che è già accaduto. La differenza con un comando è semantica ma cruciale: un comando è un'intenzione (`PlaceOrder`), un evento è un fatto (`OrderPlaced`). I comandi sono diretti a un destinatario specifico e possono essere rifiutati; gli eventi sono pubblicati per chiunque sia interessato e non possono essere "annullati" — al massimo si genera un evento di compensazione (`OrderCancelled`).

Un **message broker** è il middleware che riceve gli eventi dai produttori, li persiste e li consegna ai consumatori. I broker si distinguono per modello di consegna (queue vs log), garanzie di ordering, durabilità, throughput e modello di consumo (push vs pull).

Una **queue** è una struttura FIFO in cui ogni messaggio viene consumato da un solo consumer (competing consumers). Un **topic** in modello pub/sub permette invece a più consumer di ricevere lo stesso messaggio. Kafka usa il termine "topic" anche per code partizionate persistenti, dove ogni partizione è un log append-only e i consumer mantengono un offset di lettura.

Le **delivery semantics** sono tre: at-most-once (il messaggio può essere perso ma non duplicato), at-least-once (il messaggio non viene perso ma può essere duplicato), exactly-once (il messaggio viene consegnato esattamente una volta). Quest'ultima è la più costosa e in pratica si ottiene combinando at-least-once con idempotency consumer-side, come vedremo più avanti.

L'**event sourcing** è un pattern in cui lo stato dell'applicazione non è memorizzato come uno snapshot corrente in un database relazionale, ma come la sequenza ordinata di tutti gli eventi che lo hanno modificato. Lo stato corrente si ottiene rigiocando gli eventi (replay). Il vantaggio è una audit trail completa e la possibilità di derivare nuove proiezioni dello stato da eventi storici; lo svantaggio è la complessità operativa e di evoluzione dello schema.

---

## Event-Driven vs Request/Response

Nell'approccio request/response (REST, gRPC sincrono, RPC), il chiamante invia una richiesta e attende una risposta. Questo modello è semplice da ragionare, è naturale per operazioni con risultato immediato (lookup, validazione, calcolo) e ha garanzie di consistency forti perché chi chiama sa subito se l'operazione è andata a buon fine.

I limiti emergono quando i sistemi crescono. Un endpoint REST che a sua volta chiama tre servizi downstream introduce un grafo di dipendenze sincrono: se uno dei tre è lento, l'intera richiesta è lenta; se uno è giù, la richiesta fallisce. La latenza dell'utente finale è la somma delle latenze dei downstream, e la resilienza è il prodotto delle disponibilità (un servizio al 99,9% chiamato in serie con altri tre al 99,9% dà 99,6% complessivo). Inoltre, ogni nuovo consumatore di un dato richiede una modifica al produttore per essere chiamato.

Nell'approccio event-driven, il produttore pubblica un evento e termina. I consumer lo elaborano in modo asincrono, in parallelo, ognuno con il proprio ritmo e i propri retry. Aggiungere un nuovo consumer non richiede modifiche al produttore. La latenza percepita dall'utente è quella della pubblicazione, non della catena completa. La resilienza migliora perché un consumer down non blocca il produttore — gli eventi si accumulano nel broker e vengono processati appena il consumer torna disponibile.

I trade-off non sono trascurabili. **Eventual consistency** significa che dopo la pubblicazione di un evento c'è un intervallo (millisecondi o secondi) in cui le proiezioni downstream non sono ancora aggiornate; un'interfaccia utente ingenua potrebbe mostrare dati stantii. **Debugging distribuito** è più complesso: un singolo workflow può attraversare cinque servizi e tre broker, e ricostruire la sequenza richiede tracing distribuito (OpenTelemetry, correlation ID propagati in ogni messaggio). **Ordering** non è garantito globalmente in nessun broker scalabile — Kafka garantisce l'ordine solo all'interno di una partizione, RabbitMQ solo all'interno di una singola queue con un singolo consumer.

La scelta non è binaria. La maggior parte dei sistemi reali combina entrambi gli approcci: REST/gRPC per query sincrone e per comandi che richiedono validazione immediata, eventi per propagare cambiamenti di stato e attivare workflow downstream.

---

## Pattern Event-Driven Fondamentali

### Event Notification

Il pattern più semplice. Il produttore pubblica un evento minimale che contiene solo l'identificatore della risorsa cambiata e il tipo di evento, senza payload pesante. I consumer interessati devono fare una chiamata di ritorno (callback API) al produttore o a un servizio terzo per recuperare lo stato completo della risorsa.

```json
{
  "type": "OrderUpdated",
  "orderId": "ORD-2026-04-22-7281",
  "occurredAt": "2026-04-22T14:32:18Z"
}
```

Vantaggi: payload piccolo, evento sempre coerente con lo stato corrente (il consumer legge la fonte di verità), schema dell'evento minimale e stabile. Svantaggi: ogni consumer genera traffico di lettura sul produttore, il quale diventa un single point of failure per l'arricchimento dei dati. Adatto quando i consumer sono pochi e quando il volume di eventi è basso.

### Event-Carried State Transfer

Il produttore include nell'evento l'intero stato (o uno snapshot significativo) della risorsa cambiata. I consumer non hanno bisogno di chiamare back il produttore: hanno tutto quello che serve nell'evento.

```json
{
  "type": "OrderPlaced",
  "orderId": "ORD-2026-04-22-7281",
  "occurredAt": "2026-04-22T14:32:18Z",
  "customer": {"id": "CUST-449", "vatNumber": "IT01234567890"},
  "items": [
    {"sku": "ABC-001", "qty": 3, "unitPriceEur": 19.90},
    {"sku": "DEF-002", "qty": 1, "unitPriceEur": 49.00}
  ],
  "totalEur": 108.70,
  "shippingAddress": {"street": "Via Verdi 12", "city": "Verona", "zip": "37100"}
}
```

Vantaggi: consumer disaccoppiati dal produttore (possono evolvere il modello dati indipendentemente, possono restare offline temporaneamente senza perdere informazioni). Svantaggi: payload più pesanti, schema più complesso da evolvere, possibilità di stato stantio se il consumer processa l'evento molto dopo. È il pattern più usato in pratica per integrazioni cross-team.

### Event Sourcing

Lo stato dell'aggregato non è memorizzato direttamente, ma derivato dalla sequenza di eventi. Per ricostruire lo stato di un ordine, si applicano in sequenza tutti i suoi eventi: `OrderCreated`, `ItemAdded`, `ItemRemoved`, `DiscountApplied`, `PaymentReceived`, `OrderShipped`. Lo stato corrente è il fold di questa sequenza.

Vantaggi: audit trail completa per definizione, possibilità di tornare indietro nel tempo (rebuild di proiezioni alternative), naturale time-travel debugging. Svantaggi: complessità di evoluzione degli eventi (un evento storico non può essere modificato — al più si introduce un nuovo tipo di evento e si gestisce la migrazione nella logica di replay), performance di lettura che richiede snapshot periodici, curva di apprendimento ripida per il team. EventStoreDB e Marten sono le implementazioni più mature.

### CQRS (Command Query Responsibility Segregation)

Separa il modello di scrittura dal modello di lettura. I comandi modificano lo stato (e tipicamente generano eventi), le query leggono da proiezioni ottimizzate per il consumo. CQRS è spesso (ma non necessariamente) abbinato a event sourcing: gli eventi prodotti dal lato write alimentano le proiezioni del lato read.

In una pipeline ordini, il modello write potrebbe essere normalizzato in PostgreSQL per garantire integrità; le proiezioni read potrebbero essere tabelle denormalizzate in Elasticsearch per ricerca testuale, viste materialiste per dashboard, o documenti in MongoDB per le API mobile. Ogni proiezione è aggiornata da un consumer dedicato che ascolta gli eventi.

---

## Pub/Sub vs Point-to-Point Queue

Il modello **point-to-point queue** (competing consumers) ha un produttore che invia un messaggio in coda e N consumer che leggono dalla stessa coda. Ogni messaggio viene consegnato a un solo consumer. Aggiungere consumer aumenta il throughput totale (load balancing automatico). Tipico per workload di processamento (resize immagini, generazione PDF, invio email): il messaggio non interessa a nessun altro, basta che qualcuno lo elabori.

Il modello **publish/subscribe** ha un produttore che pubblica su un topic e N subscriber che ricevono ognuno una copia del messaggio. Tipico per propagazione di eventi: `InvoiceIssued` deve essere ricevuto da CRM, contabilità, sistema di archiviazione, notifica cliente — quattro consumer logicamente distinti, ognuno con la propria logica.

RabbitMQ supporta entrambi i modelli tramite le sue exchange (vedremo). Kafka supporta nativamente il pub/sub con consumer group: ogni partizione di un topic viene consumata da un solo consumer all'interno dello stesso consumer group, ma più consumer group leggono indipendentemente lo stesso topic — quindi un topic Kafka è simultaneamente queue (all'interno di un group) e pub/sub (tra group diversi).

La regola pratica: usa queue quando il messaggio rappresenta un task da eseguire una sola volta; usa pub/sub quando il messaggio rappresenta un evento che potrebbe interessare a più stakeholder, anche futuri.

---

## RabbitMQ Deep Dive

RabbitMQ è un message broker basato sul protocollo AMQP 0-9-1, scritto in Erlang, maturo (rilasciato nel 2007), con un modello molto flessibile basato su exchange, binding e queue. È il broker di riferimento per workload con messaggi piccoli, instradamento complesso, requisiti di latenza bassa per messaggio singolo.

### Modello Concettuale

Un produttore non pubblica direttamente in una queue: pubblica in un'**exchange** con una **routing key**. L'exchange decide, in base ai propri **binding**, in quali queue copiare il messaggio. Questa indirezione è la fonte della flessibilità di RabbitMQ.

### Tipi di Exchange

- **Direct exchange**: il messaggio va nelle queue il cui binding key matcha esattamente la routing key. Utile per instradamento puntuale (es. routing key `invoice.italy.b2b` finisce in una queue specifica).
- **Topic exchange**: il binding key supporta wildcard (`*` per una parola, `#` per zero o più parole separate da `.`). Una queue legata a `invoice.italy.*` riceve `invoice.italy.b2b` e `invoice.italy.b2c` ma non `invoice.germany.b2b`. È il tipo più usato in pratica.
- **Fanout exchange**: ignora la routing key, copia il messaggio in tutte le queue legate. Equivalente a un broadcast pub/sub.
- **Headers exchange**: routing basato su header del messaggio anziché routing key. Raramente usato.

### Queue Durable vs Transient, Persistent vs Transient

Una queue **durable** sopravvive a un riavvio del broker; una **transient** viene cancellata. I messaggi pubblicati con `delivery_mode=2` (persistent) vengono scritti su disco; quelli con `delivery_mode=1` restano in memoria. Per durabilità end-to-end servono entrambe: queue durable + messaggi persistent + publisher confirms abilitati.

```python
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='rabbitmq.internal',
        credentials=pika.PlainCredentials('appuser', 'secret-from-env'),
        heartbeat=600,
        blocked_connection_timeout=300,
    )
)
channel = connection.channel()

channel.confirm_delivery()

channel.exchange_declare(
    exchange='orders',
    exchange_type='topic',
    durable=True,
)

channel.queue_declare(
    queue='orders.italy.processing',
    durable=True,
    arguments={
        'x-message-ttl': 86400000,
        'x-dead-letter-exchange': 'orders.dlx',
        'x-dead-letter-routing-key': 'orders.italy.failed',
        'x-max-length': 100000,
        'x-overflow': 'reject-publish',
    },
)

channel.queue_bind(
    queue='orders.italy.processing',
    exchange='orders',
    routing_key='order.placed.italy.*',
)

try:
    channel.basic_publish(
        exchange='orders',
        routing_key='order.placed.italy.b2b',
        body=b'{"orderId":"ORD-2026-04-22-7281","totalEur":108.70}',
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type='application/json',
            message_id='msg-7281',
            timestamp=int(time.time()),
            headers={'schema_version': '2'},
        ),
        mandatory=True,
    )
except pika.exceptions.UnroutableError:
    logger.error('Messaggio non routato — nessuna queue collegata')
```

### Acknowledgement Manuale

Di default, RabbitMQ usa auto-ack: il messaggio viene rimosso dalla queue appena consegnato al consumer. Se il consumer crasha durante l'elaborazione, il messaggio è perso. In produzione si usa **manual ack**: il consumer chiama `basic_ack` solo dopo aver completato l'elaborazione. Se crasha prima, RabbitMQ rileva la disconnessione e ridelibera il messaggio.

```python
def callback(ch, method, properties, body):
    try:
        process_order(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except TransientError:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    except PermanentError:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

channel.basic_qos(prefetch_count=10)
channel.basic_consume(
    queue='orders.italy.processing',
    on_message_callback=callback,
    auto_ack=False,
)
channel.start_consuming()
```

### Prefetch Count

`basic_qos(prefetch_count=N)` limita il numero di messaggi non-ack che un consumer può tenere contemporaneamente. Un valore troppo alto satura la memoria del consumer e crea hot spot (un consumer riceve molti messaggi mentre altri sono inattivi). Un valore troppo basso riduce throughput. Il punto ottimale dipende dal tempo medio di elaborazione: per task brevi (< 100ms) `prefetch_count=100-200` è ragionevole; per task lunghi (secondi/minuti) `prefetch_count=1-10`.

### Dead-Letter Exchange (DLX)

Quando un messaggio viene rejected senza requeue, scade per TTL, o supera il limite di lunghezza della queue, RabbitMQ può inoltrarlo automaticamente a un'exchange dedicata (DLX). Da lì il messaggio finisce in una **dead-letter queue** dove può essere analizzato manualmente o reinviato dopo correzione del bug.

```python
channel.exchange_declare(exchange='orders.dlx', exchange_type='topic', durable=True)
channel.queue_declare(queue='orders.italy.failed', durable=True)
channel.queue_bind(queue='orders.italy.failed', exchange='orders.dlx', routing_key='orders.italy.failed')
```

### TTL e Priority Queue

`x-message-ttl` imposta una scadenza in millisecondi sui messaggi. `x-max-priority` (range 1-255, raccomandato 1-10) abilita queue prioritarie: messaggi con priority più alta vengono consegnati prima.

### Quorum Queues per HA

Le quorum queue, introdotte in RabbitMQ 3.8, sostituiscono le vecchie classic mirrored queue per scenari high-availability. Implementano consenso Raft tra 3 o 5 nodi del cluster: la scrittura è considerata committed quando la maggioranza dei nodi l'ha persistita. Sopravvivono al crash di una minoranza di nodi senza perdita dati.

```python
channel.queue_declare(
    queue='orders.italy.processing',
    durable=True,
    arguments={'x-queue-type': 'quorum'},
)
```

### RabbitMQ Streams

Dalla 3.9, RabbitMQ supporta le **streams** — un nuovo tipo di queue append-only persistente, simile a Kafka, ottimizzata per fan-out massivo e replay storico. Le stream permettono a più consumer di leggere dalla stessa stream con offset indipendenti, sostenendo throughput nell'ordine di milioni di messaggi al secondo per nodo. Sono la risposta di RabbitMQ ai workload tipicamente Kafka, mantenendo l'ecosistema AMQP.

---

## Apache Kafka Deep Dive

Kafka, originariamente sviluppato da LinkedIn e poi donato alla Apache Foundation, è progettato per throughput estremo (milioni di messaggi al secondo per cluster), retention lunga (giorni o anni), replay storico. È il broker dominante per pipeline di event streaming, change data capture, ingestion in data lake e data warehouse.

### Modello Concettuale

Un **broker** Kafka è un nodo del cluster. Un **topic** è una stream logica di eventi, suddivisa in **partition** — log append-only ognuno gestito da un broker leader. Ogni partition è replicata su N broker (replication factor), e in ogni momento solo uno è il leader (gestisce read/write), gli altri sono replica passive (ISR, In-Sync Replica).

### Partitioning e Ordering

L'ordering è garantito solo all'interno di una partizione. La partizione di destinazione di un evento è determinata dalla key del messaggio: `partition = hash(key) % num_partitions`. Eventi con la stessa key finiscono nella stessa partizione e vengono consumati in ordine. Per pipeline ordini, la key tipica è il customer ID o l'order ID — questo garantisce che tutti gli eventi relativi a un ordine arrivino in sequenza al consumer.

### Consumer Group e Offset

Un **consumer group** è un insieme di consumer che condividono il consumo di un topic: ogni partizione viene assegnata a uno e un solo consumer del group. Se ci sono più consumer che partizioni, alcuni restano idle. L'**offset** è la posizione di lettura del consumer in una partizione — è committato periodicamente (auto-commit ogni 5s di default, o manualmente per maggiore controllo).

```python
from confluent_kafka import Producer, Consumer, KafkaError
import json

producer = Producer({
    'bootstrap.servers': 'kafka-1:9092,kafka-2:9092,kafka-3:9092',
    'acks': 'all',
    'enable.idempotence': True,
    'compression.type': 'lz4',
    'linger.ms': 20,
    'batch.size': 32768,
})

def delivery_report(err, msg):
    if err:
        logger.error(f'Delivery failed: {err}')
    else:
        logger.debug(f'Delivered to {msg.topic()}[{msg.partition()}]@{msg.offset()}')

event = {
    'type': 'OrderPlaced',
    'orderId': 'ORD-2026-04-22-7281',
    'occurredAt': '2026-04-22T14:32:18Z',
    'totalEur': 108.70,
}

producer.produce(
    topic='orders.placed',
    key='CUST-449'.encode('utf-8'),
    value=json.dumps(event).encode('utf-8'),
    headers=[('schema_version', b'2')],
    on_delivery=delivery_report,
)
producer.flush(timeout=10)
```

```python
consumer = Consumer({
    'bootstrap.servers': 'kafka-1:9092,kafka-2:9092,kafka-3:9092',
    'group.id': 'order-fulfillment-service',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False,
    'isolation.level': 'read_committed',
    'max.poll.interval.ms': 300000,
})
consumer.subscribe(['orders.placed'])

try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            logger.error(f'Consumer error: {msg.error()}')
            continue
        try:
            event = json.loads(msg.value())
            process_order(event)
            consumer.commit(message=msg, asynchronous=False)
        except Exception as exc:
            logger.exception('Errore processing — non commit, retry al prossimo poll')
finally:
    consumer.close()
```

### Retention: Time-Based vs Log Compaction

Ogni topic ha una policy di retention. **Time-based retention** (`retention.ms`) cancella segmenti del log più vecchi di N ms — tipico per eventi (es. `retention.ms=604800000` = 7 giorni). **Log compaction** (`cleanup.policy=compact`) mantiene solo l'ultimo valore per ogni key — utile per topic che rappresentano stato corrente di entità (es. profili utente, configurazioni). Si possono combinare entrambe (`cleanup.policy=compact,delete`).

### Kafka Connect

Framework integrato per pipeline di ingestion ed export senza scrivere codice. Connettori sorgente leggono da sistemi esterni (Postgres CDC tramite Debezium, MongoDB, Salesforce, S3) e scrivono su topic Kafka; connettori sink fanno l'opposto (Elasticsearch, Snowflake, BigQuery, JDBC). Si configurano via REST API o file properties.

### Kafka Streams e ksqlDB

**Kafka Streams** è una libreria JVM per stream processing in-process: filtri, aggregazioni, join tra topic, stato locale persistente in RocksDB. **ksqlDB** è un layer SQL sopra Kafka Streams che permette di esprimere trasformazioni come query SQL continue. Adatti per analytics in real-time, deduplica, arricchimento, finestre temporali.

---

## Redis Streams come Alternativa Lightweight

Redis Streams (introdotti in Redis 5.0) sono una struttura dati append-only, simile a Kafka in modello ma molto più leggera operativamente. Un singolo Redis può sostenere centinaia di migliaia di messaggi al secondo, con latenza sub-millisecondo. Adatto per workload medio-piccoli dove introdurre Kafka sarebbe overkill.

```bash
# Append a stream
XADD orders:placed * orderId ORD-2026-04-22-7281 totalEur 108.70

# Crea consumer group
XGROUP CREATE orders:placed fulfillment $ MKSTREAM

# Consumer reads (blocking with timeout)
XREADGROUP GROUP fulfillment consumer-1 COUNT 10 BLOCK 5000 STREAMS orders:placed >

# Ack del messaggio
XACK orders:placed fulfillment 1745329938517-0
```

```python
import redis

r = redis.Redis(host='redis', port=6379, decode_responses=True)

r.xadd('orders:placed', {
    'orderId': 'ORD-2026-04-22-7281',
    'totalEur': '108.70',
    'occurredAt': '2026-04-22T14:32:18Z',
})

try:
    r.xgroup_create('orders:placed', 'fulfillment', id='$', mkstream=True)
except redis.exceptions.ResponseError:
    pass

while True:
    response = r.xreadgroup(
        groupname='fulfillment',
        consumername='consumer-1',
        streams={'orders:placed': '>'},
        count=10,
        block=5000,
    )
    if not response:
        continue
    for stream_name, messages in response:
        for msg_id, fields in messages:
            try:
                process_order(fields)
                r.xack(stream_name, 'fulfillment', msg_id)
            except Exception:
                logger.exception('Processing failed — sarà riprocessato')
```

I messaggi non-ack restano in pending list (PEL) per consumer; comandi `XPENDING` e `XCLAIM` permettono di reclaim messaggi orfani da consumer crashati. Manca il fan-out a consumer group multipli con offset indipendenti che Kafka offre nativamente, ma per pattern queue + competing consumer è perfettamente adeguato.

---

## Confronto RabbitMQ vs Kafka vs NATS vs Redis Streams

| Caratteristica | RabbitMQ | Kafka | NATS JetStream | Redis Streams |
|---|---|---|---|---|
| Modello | Queue + Exchange | Distributed log | Subject-based pub/sub | In-memory append log |
| Throughput single-node | 50k msg/s | 1M+ msg/s | 1M+ msg/s | 100k msg/s |
| Latenza tipica | 1-10ms | 5-20ms | <1ms | <1ms |
| Retention | Fino ad ack | Configurabile (giorni/anni) | Configurabile | Limitata da memoria |
| Replay storico | No (con plugin) | Sì nativo | Sì | Limitato |
| Routing flessibile | Sì (exchange tipi) | No (solo partition by key) | Sì (subject hierarchy) | No |
| Operational complexity | Media | Alta (Zookeeper/KRaft) | Bassa | Bassissima |
| Ecosistema connettori | Buono | Eccellente (Connect) | In crescita | Limitato |
| Use case ideale | Microservizi, RPC async, instradamento complesso | Event streaming, CDC, analytics | Edge, IoT, microservizi cloud-native | Sostituto leggero di Kafka per PMI |

Decisione architettonica pratica:

- **Sotto 1000 msg/s, retention < 1 ora, instradamento semplice**: Redis Streams. Risparmio operativo enorme.
- **Microservizi con instradamento complesso, RPC asincrono, < 100k msg/s**: RabbitMQ. Flessibilità AMQP imbattibile.
- **Event streaming, CDC, integrazioni cross-team, retention lunga, > 100k msg/s**: Kafka. Lo standard de facto.
- **Edge computing, IoT, ambienti cloud-native con leaf node**: NATS JetStream. Footprint minuscolo, leaf node nativi.

---

## Schema Registry e Schema Evolution

Quando produttori e consumer evolvono indipendentemente, il rischio è che un produttore introduca un campo nuovo o cambi tipo a un campo esistente, e i consumer crashino sul deserialize. Lo **schema registry** centralizza la definizione degli schemi (Avro, Protobuf, JSON Schema), assegna un ID univoco a ogni versione, e applica regole di compatibilità ad ogni nuova registrazione.

Le regole di compatibilità più comuni:

- **Backward compatible**: nuovi consumer possono leggere vecchi messaggi. Modifiche permesse: aggiungere campi opzionali, rimuovere campi opzionali. Vietato: aggiungere campi obbligatori, rimuovere campi obbligatori, cambiare tipo.
- **Forward compatible**: vecchi consumer possono leggere nuovi messaggi (ignorando campi nuovi). Specchio della backward.
- **Full compatible**: backward + forward. La regola più stringente — permette deploy indipendenti di produttori e consumer.

Confluent Schema Registry è il riferimento per Kafka. Memorizza schemi Avro/Protobuf/JSON Schema, espone REST API, integra con i serializer/deserializer Kafka.

```python
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka import Producer

schema_str = """
{
  "type": "record",
  "name": "OrderPlaced",
  "namespace": "it.example.orders",
  "fields": [
    {"name": "orderId", "type": "string"},
    {"name": "occurredAt", "type": {"type": "long", "logicalType": "timestamp-millis"}},
    {"name": "totalEur", "type": {"type": "bytes", "logicalType": "decimal", "precision": 12, "scale": 2}},
    {"name": "vatNumber", "type": ["null", "string"], "default": null}
  ]
}
"""

sr_client = SchemaRegistryClient({'url': 'http://schema-registry:8081'})
avro_serializer = AvroSerializer(sr_client, schema_str)

producer = Producer({'bootstrap.servers': 'kafka-1:9092'})
producer.produce(
    topic='orders.placed',
    key='CUST-449'.encode(),
    value=avro_serializer({'orderId': 'ORD-7281', 'occurredAt': 1745329938517, 'totalEur': b'\\x2A\\x6E', 'vatNumber': 'IT01234567890'}, None),
)
producer.flush()
```

Avro è preferito per il binary encoding compatto e l'ottima gestione di schema evolution. Protobuf è buono ma più verboso nella definizione. JSON Schema è leggibile ma più pesante on-the-wire.

---

## Event Schema Design e CloudEvents

CloudEvents è una specifica CNCF per standardizzare metadata di eventi cross-platform. Definisce attributi obbligatori (`id`, `source`, `specversion`, `type`) e opzionali (`time`, `subject`, `datacontenttype`), lasciando libertà sul payload.

```json
{
  "specversion": "1.0",
  "type": "it.example.orders.OrderPlaced.v2",
  "source": "/orders/web-shop",
  "id": "evt-2026-04-22-7281-abc",
  "time": "2026-04-22T14:32:18.517Z",
  "datacontenttype": "application/json",
  "subject": "ORD-2026-04-22-7281",
  "data": {
    "orderId": "ORD-2026-04-22-7281",
    "totalEur": 108.70,
    "customerId": "CUST-449"
  }
}
```

**Linee guida pratiche per il naming**:

- Type in formato `<dominio>.<aggregato>.<evento>.<versione>`: `it.example.invoices.InvoiceIssued.v3`.
- Naming al passato (`OrderPlaced`, non `PlaceOrder`).
- Versioning esplicito nel type quando si introducono breaking change.
- ID univoco generato dal produttore (UUIDv7 o ULID per ordering naturale per tempo).
- Source URI che identifica il sistema produttore.

---

## Outbox Pattern e CDC con Debezium

Un problema classico: come garantire che la scrittura nel database e la pubblicazione dell'evento sul broker siano atomiche? Se prima si scrive nel DB e poi si pubblica e il publish fallisce, l'evento è perso. Se prima si pubblica e poi si scrive e la scrittura fallisce, l'evento esiste senza supporto nel DB.

L'**outbox pattern** risolve scrivendo evento e dato di business nella stessa transazione DB, in due tabelle. Un processo separato (relay) legge la tabella outbox e pubblica gli eventi sul broker, marcandoli come pubblicati. Se il relay crasha, al riavvio riprende dalla riga non ancora pubblicata.

```sql
BEGIN;

INSERT INTO orders (id, customer_id, total_eur, created_at)
VALUES ('ORD-2026-04-22-7281', 'CUST-449', 108.70, NOW());

INSERT INTO outbox_events (id, aggregate_type, aggregate_id, event_type, payload, created_at)
VALUES (
  gen_random_uuid(),
  'Order',
  'ORD-2026-04-22-7281',
  'OrderPlaced',
  '{"orderId":"ORD-2026-04-22-7281","totalEur":108.70}',
  NOW()
);

COMMIT;
```

Il relay può essere un cron polling (`SELECT * FROM outbox_events WHERE published_at IS NULL ORDER BY created_at LIMIT 100`), ma il pattern moderno usa **CDC (Change Data Capture)** con Debezium: Debezium legge il WAL di PostgreSQL (logical replication) o il binlog di MySQL e pubblica automaticamente i cambiamenti come eventi Kafka. La tabella outbox diventa il "topic logico" dell'aggregato, e Debezium gestisce la trasformazione tramite l'**Outbox Event Router** SMT (Single Message Transform) che indirizza ogni riga al topic Kafka appropriato in base alla colonna `aggregate_type`.

```yaml
name: outbox-connector
config:
  connector.class: io.debezium.connector.postgresql.PostgresConnector
  database.hostname: postgres-primary
  database.port: 5432
  database.user: debezium
  database.password: ${DEBEZIUM_PASSWORD}
  database.dbname: orders_db
  topic.prefix: orders-cdc
  table.include.list: public.outbox_events
  plugin.name: pgoutput
  transforms: outbox
  transforms.outbox.type: io.debezium.transforms.outbox.EventRouter
  transforms.outbox.route.by.field: aggregate_type
  transforms.outbox.route.topic.replacement: ${routedByValue}.events
```

---

## Saga Pattern per Workflow Long-Running

Una saga è una sequenza di transazioni locali coordinate da eventi, con compensazioni in caso di fallimento. Esempio: un ordine richiede di riservare l'inventario, processare il pagamento, schedulare la spedizione. Se il pagamento fallisce dopo la riserva inventario, serve liberare l'inventario (compensazione).

Due varianti:

- **Choreography**: ogni servizio ascolta gli eventi e decide cosa fare. Nessun coordinator centrale. Flessibile ma difficile da debuggare quando i servizi sono molti.
- **Orchestration**: un orchestrator dedicato (es. Temporal, Camunda, AWS Step Functions) coordina la sequenza chiamando esplicitamente ogni servizio. Più chiaro, più facile osservare lo stato della saga, ma introduce un single point of decisione.

Per workflow oltre 5-6 step o con pattern di retry/compensazione complessi, l'orchestration è di norma la scelta migliore. Temporal è il framework open source più maturo per workflow distribuiti durabili.

---

## Idempotency Consumer-Side

In un sistema at-least-once (la norma), un consumer può ricevere lo stesso messaggio più volte. La soluzione è rendere l'elaborazione idempotente: applicarla N volte produce lo stesso risultato di applicarla una volta.

Tecnica più semplice: deduplica via message ID + Redis SET con TTL.

```python
import redis

r = redis.Redis()
DEDUP_TTL_SECONDS = 7 * 24 * 3600

def process_with_idempotency(message_id: str, body: dict) -> None:
    if not r.set(f'processed:{message_id}', '1', nx=True, ex=DEDUP_TTL_SECONDS):
        logger.info(f'Messaggio {message_id} già processato — skip')
        return
    try:
        process_business_logic(body)
    except Exception:
        r.delete(f'processed:{message_id}')
        raise
```

Il TTL deve essere maggiore della massima latenza di redelivery del broker (in pratica 7 giorni è ampiamente sufficiente). Per workload critici, usare una tabella DB anziché Redis garantisce persistenza forte.

---

## Retry, DLQ e Parking Lot Pattern

Una strategia retry robusta combina:

1. **Retry immediato** (max 3 tentativi) per errori transitori (timeout, connection reset).
2. **Backoff esponenziale** per errori che richiedono tempo (rate limit, downstream lento).
3. **Dead-letter queue** dopo N tentativi falliti.
4. **Parking lot** per intervento manuale: una queue separata da DLQ dove finiscono i messaggi che hanno fallito anche dopo replay automatico — necessitano analisi umana.

In RabbitMQ, retry con delay si implementa con il plugin **rabbitmq_delayed_message_exchange** o con un pattern di queue intermedie con TTL diversi (5s, 30s, 5min) e DLX a cascata.

In Kafka, il pattern standard è retry topic separati: `orders.placed` → `orders.placed.retry.5s` → `orders.placed.retry.30s` → `orders.placed.retry.5min` → `orders.placed.dlq`. Ogni retry topic ha un consumer che attende il delay e ritenta.

---

## Monitoring e Observability

Metriche essenziali per RabbitMQ:

- Queue depth (`rabbitmq_queue_messages`): allarmare se cresce monotonicamente — segno di consumer down o lento.
- Publish rate vs deliver rate.
- Unacked messages.
- Connection count, channel count.
- Memory e disk usage del broker.

Esporre via `rabbitmq_prometheus` plugin (built-in da 3.8), scrape Prometheus, dashboard Grafana standard ID 10991.

Metriche essenziali per Kafka:

- Consumer lag per group/topic/partition (`kafka_consumer_lag`): la metrica regina, allarmare se supera soglia in funzione del SLA.
- Under-replicated partitions (deve essere 0).
- Request latency 99th percentile.
- Disk usage per broker.
- ISR shrink rate.

Esporre via JMX exporter, scrape Prometheus. Per consumer lag specifico, usare `kafka_exporter` o `kminion`.

---

## Esempio: Pipeline Ordini E-commerce PMI

Pipeline per una PMI italiana che vende online B2B/B2C, integrata con magazzino, corriere e fatturazione SDI:

```
[Web shop] --HTTP--> [Order Service]
                          |
                          v
                    [outbox table]  --Debezium--> [Kafka: orders.placed]
                                                       |
                  +------------------------+-----------+-----------+----------------+
                  v                        v                       v                v
         [payment-service]        [inventory-service]   [shipping-scheduler]  [invoice-issuer]
                  |                        |                       |                |
                  v                        v                       v                v
        [Kafka: payment.requested] [Kafka: inventory.reserved] [Kafka: shipping.scheduled] [Kafka: invoice.issued]
                  |                                                                         |
                  v                                                                         v
            [Stripe webhook]                                                          [SDI gateway]
```

Ogni servizio è un microservizio consumer Kafka. Saga implicita coordinata da eventi: se `payment.failed` viene pubblicato, l'inventory-service ascolta e libera la riserva (`inventory.released`). L'invoice-issuer attende `payment.captured` E `shipping.scheduled` (state machine locale) prima di emettere fattura.

---

## Esempio: CDC Postgres → Kafka → Warehouse

Replica continua del database operazionale verso Snowflake/BigQuery per analytics:

```
[PostgreSQL primary] --logical replication--> [Debezium connector] --> [Kafka: cdc.public.orders, cdc.public.customers, ...]
                                                                              |
                                                                              v
                                                                   [Kafka Connect Snowflake Sink]
                                                                              |
                                                                              v
                                                                       [Snowflake stage tables]
                                                                              |
                                                                              v
                                                                   [dbt models per fact/dim]
```

Vantaggi rispetto a ETL batch notturno: latenza analytics ridotta da 24h a minuti, carico sul DB operazionale costante (logical replication è leggero) anziché picchi notturni di full table scan, possibilità di replay storico semplicemente ripartendo da offset Kafka.

---

## Esempio: Integrazione SDI Fatturazione Elettronica

Il Sistema di Interscambio italiano per la fatturazione elettronica B2B/PA accetta XML FatturaPA via SdICoop (web service) o PEC. La comunicazione è asincrona: si invia il file, si riceve dopo minuti/ore una notifica di esito (Ricevuta di Consegna, Notifica di Mancata Consegna, Notifica di Scarto).

Architettura event-driven robusta:

```
[invoice-issuer] --pubblica--> [Kafka: invoice.tobesent]
                                       |
                                       v
                              [sdi-uploader consumer]
                                       |
                                       v
                              [SDI SdICoop endpoint]
                                       |
                                       v
                              [Kafka: invoice.uploaded]
                                       |
                                       v
                              [sdi-poller / inbox PEC]
                                       |
                                       v
                              [Kafka: invoice.delivered | invoice.rejected]
                                       |
                                       v
                              [Notification service + accounting update]
```

Ogni step è retryable con backoff. La queue `invoice.tobesent` è la "fonte di verità" — se l'uploader crasha, riprende esattamente da dove si era fermato. Le notifiche SDI possono arrivare ore dopo l'invio: il poller/inbox-PEC consumer rimane in ascolto continuo, correlando le ricevute al file originale tramite il `progressivo invio`.

---

## Best Practices

- **Idempotency da subito**: ogni consumer deve essere idempotente. È molto più difficile aggiungerla retroattivamente.
- **Schema versioning esplicito**: includi `schema_version` o version nel type CloudEvent. Prepara i consumer a gestire più versioni in parallelo.
- **Outbox pattern non opzionale** quando devi pubblicare eventi correlati a scritture DB. Senza, prima o poi avrai inconsistency.
- **Correlation ID propagato**: ogni evento porta un correlation ID che attraversa tutta la pipeline. OpenTelemetry instrumentation per tracing distribuito.
- **DLQ con monitoring + runbook**: una DLQ senza alert e senza procedura di reprocess è solo un cimitero di messaggi.
- **Capacity planning per consumer lag**: dimensiona consumer in modo che possano smaltire un picco 3x in un'ora.
- **Test di chaos**: kill periodici di consumer in staging per verificare resilienza.
- **Naming consistency**: definisci convenzioni di naming dei topic/queue all'inizio e sii rigoroso. Refactoring di topic name in produzione è doloroso.

---

## Troubleshooting

**Consumer lag che cresce**: prima ipotesi è consumer down — verifica readiness/liveness. Seconda ipotesi è consumer lento — profila il processing. Terza è hot partition (key distribuita male) — verifica la distribuzione delle key.

**Messaggi nella DLQ**: ispeziona il payload, riproduci in staging, identifica root cause (bug consumer, schema breaking change, downstream giù), fixa, replay manuale (script di consumer dalla DLQ con flag idempotency).

**Duplicate evidenti in downstream**: probabilmente l'idempotency layer non funziona. Verifica TTL del dedup store, verifica che il message ID sia veramente univoco e generato dal produttore (non dal broker).

**Out-of-order events**: in Kafka, controlla che la key sia consistente. In RabbitMQ, ricorda che con prefetch > 1 e più consumer l'ordering è perso. Usa key consistente o accetta out-of-order e ordina applicativamente per timestamp.

**RabbitMQ memory alarm**: il broker si autoprotegge bloccando i publisher. Aumenta memoria disponibile, riduci queue length con `x-max-length`, abilita lazy queue (`x-queue-mode=lazy`) per spillare su disco prima.

**Kafka under-replicated partitions**: un broker è giù o lento. Verifica health del broker, network tra broker, disk pressure. Non fare modifiche alla replication factor sotto carico.

**Consumer che si disconnette ripetutamente dal group**: prima verifica `session.timeout.ms` — se il processing di un batch impiega piu tempo del session timeout, il broker considera il consumer morto e lo rimuove dal group, causando rebalance continui. Soluzione: aumentare `session.timeout.ms` e `max.poll.interval.ms`, oppure ridurre `max.poll.records`.

**Messaggi "stuck" nella queue RabbitMQ (ready ma non consumed)**: i consumer sono connessi ma non stanno consumando. Cause: (1) prefetch pieno — ogni consumer ha `prefetch_count` messaggi unacked e non ne riceve altri finché non fa ack. Soluzione: verificare che il processing non sia bloccato, ridurre `prefetch_count`, o aggiungere consumer. (2) Queue con `x-max-priority` e messaggi a priorità bassa bloccati da messaggi ad alta priorità mai consumati.

**Errore "Message too large" in Kafka**: il messaggio supera `message.max.bytes` del broker o `max.request.size` del producer. Soluzione: (1) aumentare il limite (non raccomandato oltre 10 MB). (2) Meglio: inviare i dati grandi su object storage (S3, MinIO) e pubblicare solo il riferimento (URL/key) nell'evento — pattern "claim check".

**Schema Registry che rifiuta l'evoluzione dello schema**: il nuovo schema viola le regole di compatibilità configurate (BACKWARD, FORWARD, FULL). Soluzione: (1) verificare quale campo causa l'incompatibilità con `curl -X POST .../compatibility/subjects/{subject}/versions/latest`. (2) Se il breaking change è intenzionale, creare un nuovo subject (topic) anziché forzare la compatibilità. (3) Usare FULL_TRANSITIVE per massima sicurezza.

**Redis Streams che crescono senza limite**: a differenza di Kafka che ha retention policy nativa, Redis Streams crescono finché non si fa TRIM esplicito. Soluzione: usare `XADD` con `MAXLEN ~1000000` o `MINID` per limitare automaticamente. Implementare un cron job che esegue `XTRIM` periodicamente.

**Consumer lag alto solo su alcune partizioni (hot partition)**: la key di partizione è distribuita male — pochi valori concentrano il traffico. Soluzione: (1) scegliere una key con cardinalità alta e distribuzione uniforme. (2) Se la key è vincolata dal dominio (es. customer_id con pochi clienti grandi), usare un salted key: `customer_id + random_suffix` — accettando che l'ordinamento per customer sia rilassato.

**Debezium connector in stato FAILED**: cause comuni: (1) slot di replicazione PostgreSQL eliminato → ricreare slot e riavviare connector. (2) WAL retention insufficiente → aumentare `wal_keep_size` in PostgreSQL. (3) Schema change non compatibile → verificare `schema.history.internal.kafka.topic` e la politica di evoluzione schema.

**Consumer che riprocessa messaggi già elaborati dopo rebalance**: durante un rebalance, i consumer perdono le partizioni assegnate e le riacquisiscono. Se l'offset non era stato committato, i messaggi vengono rielaborati. Soluzione: (1) committare offset frequentemente (`enable.auto.commit=true` con `auto.commit.interval.ms` basso, o commit sincrono dopo ogni batch). (2) Implementare idempotency lato consumer per tollerare il replay.

**Messaggi nella DLQ senza contesto sufficiente per il debug**: la DLQ contiene il payload originale ma non il motivo del fallimento. Soluzione: quando si pubblica nella DLQ, aggiungere header/metadata con: `original_topic`, `failure_reason`, `stack_trace` (troncato), `attempt_count`, `failed_at` (timestamp ISO). Questi metadata rendono il triage e il replay molto piu efficienti.

---

## Anti-pattern Event-Driven

### 1. Event Monolite (God Event)

**Problema**: un singolo tipo di evento contiene TUTTI i dati dell'entità (ordine completo con 50+ campi, inclusi dati del cliente, prodotti, spedizione, pagamento).

**Conseguenza**: accoppiamento forte — ogni consumer deve parsare un payload enorme di cui usa il 5%. Ogni modifica allo schema richiede coordinamento con tutti i consumer. Banda sprecata.

**Soluzione**: decomporre in eventi specifici e leggeri: `order.created` (ID, timestamp, customer_id, total), `order.items_added` (order_id, items[]), `payment.received` (order_id, amount, method). Ogni consumer sottoscrive solo gli eventi rilevanti.

### 2. Usare Evento come RPC Mascherato

**Problema**: pubblicare un evento `ProcessOrderCommand` e attendere un evento `OrderProcessedResponse` — essenzialmente una request/response sincrona mascherata da asincrona.

**Conseguenza**: complessità senza beneficio. Timeout difficili da gestire, nessun vantaggio di disaccoppiamento reale, debugging più difficile.

**Soluzione**: se il flusso è richiesta-risposta, usare HTTP/gRPC. Usare eventi per notifiche asincrone genuine dove il produttore non ha bisogno di sapere chi o quando processerà l'evento.

### 3. Assenza di Schema Versioning

**Problema**: pubblicare eventi senza schema formale, evolvendo il formato ad hoc.

**Conseguenza**: consumer che si rompono silenziosamente quando un campo viene rinominato, rimosso, o cambia tipo. Debugging doloroso perché l'errore si manifesta lontano dalla causa.

**Soluzione**: adottare Schema Registry con Avro, Protobuf o JSON Schema. Definire policy di compatibilità (BACKWARD come minimo). Ogni evento ha un `schema_version` esplicito.

### 4. Polling del Database come Event Source

**Problema**: anziché usare CDC o Outbox pattern, un consumer esegue polling continuo sul database: `SELECT * FROM orders WHERE updated_at > last_check`.

**Conseguenza**: carico sul database, latenza alta (dipende dall'intervallo di polling), possibilità di perdere aggiornamenti che avvengono tra due poll, nessuna garanzia di ordinamento.

**Soluzione**: implementare Outbox pattern (tabella `outbox` con INSERT atomico nella stessa transazione) + CDC con Debezium. Se CDC non è disponibile, come minimo usare un trigger DB che scrive nella tabella outbox.

### 5. Consumer Senza Idempotency

**Problema**: consumer che assume di ricevere ogni messaggio esattamente una volta.

**Conseguenza**: in qualsiasi sistema distribuito, la consegna "at-least-once" è la norma. Senza idempotency: ordini duplicati, pagamenti doppi, email inviate più volte.

**Soluzione**: ogni consumer deve implementare idempotency. Pattern: (1) store idempotency key (message_id) in un set con TTL (Redis), (2) prima di processare, verificare se il message_id è già stato visto, (3) se già visto, skip. Costo basso, protezione alta.

### 6. Topic/Queue per Consumer (anziché per Dominio)

**Problema**: creare un topic dedicato per ogni consumer — `orders-for-warehouse`, `orders-for-billing`, `orders-for-analytics`.

**Conseguenza**: duplicazione di eventi, proliferazione di topic, difficoltà ad aggiungere nuovi consumer (serve un nuovo topic e un nuovo producer o un fork).

**Soluzione**: usare topic per dominio (`orders.events`) e consumer group per fan-out. Ogni consumer sottoscrive lo stesso topic con il proprio consumer group. Aggiungere un nuovo consumer richiede solo un nuovo group, nessuna modifica al producer.

### 7. Nessun Monitoring del Consumer Lag

**Problema**: consumer in esecuzione ma nessuno monitora se stanno tenendo il passo con il producer.

**Conseguenza**: il lag cresce silenziosamente per giorni/settimane. Quando qualcuno lo nota, ci sono milioni di messaggi arretrati e il recovery richiede ore o giorni.

**Soluzione**: monitorare `consumer_lag` per ogni consumer group e partizione. Soglie di allarme: warning a lag > 1000, critical a lag > 10000 (adattare al throughput). Dashboard con trend per identificare degradi graduali.

### 8. Retention Infinita senza Compaction

**Problema**: configurare retention infinita su un topic Kafka senza log compaction, pensando di avere un event store gratuito.

**Conseguenza**: il disco si riempie. Le query "dall'inizio" richiedono ore. Il costo storage cresce linearmente senza limite.

**Soluzione**: (1) Per event sourcing reale, usare un event store dedicato (EventStoreDB, Axon). (2) Per Kafka, usare `cleanup.policy=compact` per topic dove serve lo stato corrente (log compaction mantiene solo l'ultimo valore per chiave). (3) Per topic transazionali, configurare retention finita (es. 7 giorni) e archiviare in cold storage.

### 9. Ignorare Backpressure

**Problema**: producer che pubblica a velocità costante senza verificare se i consumer riescono a tenere il passo.

**Conseguenza**: lag crescente, OOM del broker, messaggi persi se le queue raggiungono `x-max-length`.

**Soluzione**: implementare backpressure: (1) RabbitMQ: publisher confirms + monitoring queue depth → rallentare se queue > soglia. (2) Kafka: monitorare `buffer.memory` del producer → se pieno, il producer blocca automaticamente (configurabile con `max.block.ms`). (3) Application-level: circuit breaker sul producer basato sul consumer lag.

### 10. Accoppiamento Temporale tra Produttore e Consumer

**Problema**: il produttore assume che il consumer elabori l'evento "immediatamente" e progetta il sistema di conseguenza.

**Conseguenza**: se il consumer ha un ritardo (downtime, lag, maintenance), il produttore o il flusso business si rompe.

**Soluzione**: progettare per eventuale consistenza. Il produttore pubblica e dimentica. Il consumer elabora quando può. Se serve un vincolo temporale (es. "l'ordine deve essere confermato entro 5 minuti"), implementarlo come business logic nel consumer (con timer/deadline), non come assunzione sull'infrastruttura.

---

## Sicurezza per Architetture Event-Driven

### Autenticazione e Autorizzazione del Broker

#### RabbitMQ

```
# rabbitmq.conf — autenticazione e autorizzazione
auth_mechanisms.1 = PLAIN
auth_mechanisms.2 = AMQPLAIN

# Utenti e permessi
rabbitmqctl add_user app_producer S3cureP@ssw0rd
rabbitmqctl set_permissions -p /production app_producer "^$" "^orders\\..*" "^$"
#                                                       configure  write     read
# Il producer può solo scrivere su exchange orders.*, non leggere né configurare

rabbitmqctl add_user app_consumer S3cureP@ssw0rd2
rabbitmqctl set_permissions -p /production app_consumer "^$" "^$" "^orders\\..*"
#                                                       configure  write  read
# Il consumer può solo leggere da queue orders.*, non scrivere né configurare
```

**TLS per connessioni**:

```
# rabbitmq.conf — TLS
listeners.ssl.default = 5671
ssl_options.cacertfile = /path/to/ca_certificate.pem
ssl_options.certfile   = /path/to/server_certificate.pem
ssl_options.keyfile    = /path/to/server_key.pem
ssl_options.verify     = verify_peer
ssl_options.fail_if_no_peer_cert = true
```

#### Kafka

```properties
# server.properties — SASL/SSL
listeners=SASL_SSL://0.0.0.0:9093
security.inter.broker.protocol=SASL_SSL
sasl.mechanism.inter.broker.protocol=SCRAM-SHA-512
sasl.enabled.mechanisms=SCRAM-SHA-512

ssl.keystore.location=/var/kafka/ssl/kafka.keystore.jks
ssl.keystore.password=${KEYSTORE_PASSWORD}
ssl.truststore.location=/var/kafka/ssl/kafka.truststore.jks
ssl.truststore.password=${TRUSTSTORE_PASSWORD}
ssl.client.auth=required
```

**ACL per topic**:

```bash
# Producer può scrivere solo su topic orders.*
kafka-acls.sh --bootstrap-server localhost:9093 \
  --add --allow-principal User:order-service \
  --producer --topic 'orders.' --resource-pattern-type prefixed

# Consumer può leggere solo da topic orders.* con il proprio group
kafka-acls.sh --bootstrap-server localhost:9093 \
  --add --allow-principal User:warehouse-service \
  --consumer --topic 'orders.' --resource-pattern-type prefixed \
  --group warehouse-consumer-group
```

### Crittografia dei Payload

Per dati sensibili (PII, dati finanziari), crittografare il payload dell'evento oltre al TLS del trasporto:

```python
# Envelope encryption per eventi sensibili
from cryptography.fernet import Fernet
import json
import base64

class EventEncryptor:
    def __init__(self, master_key: bytes):
        self.master_key = master_key

    def encrypt_event(self, event: dict, sensitive_fields: list[str]) -> dict:
        """Cripta solo i campi sensibili, lascia metadata in chiaro."""
        data_key = Fernet.generate_key()
        f = Fernet(data_key)

        encrypted_event = dict(event)
        for field in sensitive_fields:
            if field in encrypted_event:
                value = json.dumps(encrypted_event[field]).encode()
                encrypted_event[field] = f.encrypt(value).decode()

        # Cripta la data key con la master key
        master_f = Fernet(self.master_key)
        encrypted_data_key = master_f.encrypt(data_key).decode()

        encrypted_event['_encryption'] = {
            'encrypted_data_key': encrypted_data_key,
            'encrypted_fields': sensitive_fields,
            'algorithm': 'Fernet (AES-128-CBC + HMAC-SHA256)'
        }
        return encrypted_event
```

### Audit Trail per Eventi

Ogni evento in un sistema critico deve essere tracciabile:

```json
{
  "event_id": "evt_20260522_abc123",
  "type": "order.payment.received",
  "source": "payment-service",
  "timestamp": "2026-05-22T14:30:00Z",
  "correlation_id": "corr_xyz789",
  "causation_id": "evt_20260522_def456",
  "actor": {
    "type": "service",
    "id": "payment-service-v2.3.1",
    "ip": "10.0.1.42"
  },
  "data": { "order_id": "ord_123", "amount": 99.99, "currency": "EUR" },
  "metadata": {
    "schema_version": "2.1",
    "environment": "production",
    "region": "eu-west-1"
  }
}
```

Campi critici per audit: `correlation_id` (tracciamento end-to-end), `causation_id` (quale evento ha causato questo), `actor` (chi ha prodotto l'evento), `timestamp` (UTC ISO 8601).

---

## Strategie di Backpressure

### Backpressure Lato Consumer

```
STRATEGIE:
┌─────────────────────────────────────────────────────────┐
│ 1. RATE LIMITING                                         │
│    Consumer processa max N msg/sec                       │
│    Pro: semplice. Contro: spreca capacità in bassa load │
│                                                          │
│ 2. ADAPTIVE BATCHING                                     │
│    Batch size si adatta al consumer lag                  │
│    Lag basso → batch piccoli (bassa latenza)             │
│    Lag alto → batch grandi (alto throughput)             │
│                                                          │
│ 3. CIRCUIT BREAKER su downstream                         │
│    Se il DB/API target è lento/giù → stop consuming      │
│    Evita di riempire memory con messaggi unacked         │
│                                                          │
│ 4. LOAD SHEDDING                                         │
│    Se lag > soglia critica → scarta messaggi a bassa     │
│    priorità, processa solo quelli critici                │
└─────────────────────────────────────────────────────────┘
```

### Backpressure Lato Broker

**RabbitMQ**:
- `x-max-length`: limite massimo messaggi in queue → messaggi in eccesso vanno in DLQ o vengono scartati (policy: `reject-publish` o `drop-head`)
- `x-overflow: reject-publish`: il broker rifiuta nuovi publish quando la queue è piena → il producer riceve un NACK e può rallentare
- Memory alarm: quando la memoria del broker supera la soglia (`vm_memory_high_watermark`), TUTTI i publisher vengono bloccati

**Kafka**:
- `buffer.memory` del producer: se il buffer è pieno, `send()` blocca fino a `max.block.ms` → backpressure naturale
- Quota per client: `kafka-configs.sh --alter --add-config 'producer_byte_rate=1048576'` → limita il throughput per producer
- `fetch.max.bytes` e `max.partition.fetch.bytes` del consumer: controlla quanti dati il consumer riceve per fetch

### Pattern: Backpressure con Feedback Loop

```python
# Consumer con backpressure adattiva
import time

class AdaptiveConsumer:
    def __init__(self, consumer, target_lag=1000):
        self.consumer = consumer
        self.target_lag = target_lag
        self.batch_size = 100
        self.sleep_ms = 0

    def consume_loop(self):
        while True:
            current_lag = self.get_consumer_lag()

            if current_lag > self.target_lag * 3:
                # Lag critico: massimizza throughput
                self.batch_size = 1000
                self.sleep_ms = 0
            elif current_lag > self.target_lag:
                # Lag alto: aumenta batch
                self.batch_size = min(self.batch_size * 2, 1000)
                self.sleep_ms = 0
            elif current_lag < self.target_lag * 0.1:
                # Lag minimo: riduci batch, aggiungi pausa
                self.batch_size = max(self.batch_size // 2, 10)
                self.sleep_ms = 100
            else:
                # Lag normale: mantieni parametri
                pass

            messages = self.consumer.poll(
                timeout_ms=1000,
                max_records=self.batch_size
            )
            self.process_batch(messages)

            if self.sleep_ms > 0:
                time.sleep(self.sleep_ms / 1000)
```

---

## Ottimizzazione Costi per Broker

### Costi Infrastrutturali per Broker

| Componente | RabbitMQ | Kafka | Redis Streams | NATS JetStream |
|---|---|---|---|---|
| **RAM minima per nodo** | 2 GB | 4 GB | 1 GB | 512 MB |
| **Disco** | Basso (transient) | Alto (retention) | Medio (AOF/RDB) | Basso |
| **CPU** | Basso | Medio-Alto | Basso | Basso |
| **Nodi minimi (HA)** | 3 (quorum) | 3 broker + 3 ZK | 3 (sentinel/cluster) | 3 (cluster) |
| **Costo cloud indicativo** | €150-300/mese | €300-600/mese | €100-200/mese | €80-150/mese |
| **Managed service** | CloudAMQP | Confluent Cloud | Redis Cloud | Synadia Cloud |

### Strategie di Risparmio

1. **Right-sizing**: monitorare l'utilizzo effettivo e ridimensionare. Un cluster Kafka con 3 broker da 32 GB RAM che usa il 10% della CPU spreca risorse.

2. **Tiered storage (Kafka)**: spostare i dati storici su object storage (S3) anziché tenerli su disco locale. Confluent Tiered Storage o Kafka KRaft con tiered storage riducono i costi disco del 60-80%.

3. **Lazy queues (RabbitMQ)**: per queue con messaggi grandi o retention lunga, `x-queue-mode=lazy` spilla i messaggi su disco anziché tenerli in RAM. Riduce l'uso di memoria del 90% per queue di grandi dimensioni.

4. **Compaction per topic stateful**: usare `cleanup.policy=compact` per topic che rappresentano stato corrente (es. `user.profiles`). Mantiene solo l'ultimo valore per chiave, riducendo lo storage.

5. **TTL aggressivo**: configurare `x-message-ttl` (RabbitMQ) o `retention.ms` (Kafka) al minimo necessario. Se i consumer elaborano entro minuti, una retention di 7 giorni è spesso eccessiva — 24-48 ore possono bastare.

6. **Batching producer-side**: inviare messaggi in batch (`batch.size`, `linger.ms` in Kafka) riduce l'overhead di rete e I/O del broker. Migliora il throughput senza costi aggiuntivi.

### Managed vs Self-Hosted: Decisione

```
Managed (Confluent, CloudAMQP, ecc.)
  Pro: zero ops, SLA, scaling automatico, patching
  Contro: costo 3-5x vs self-hosted, vendor lock-in, meno controllo

Self-hosted (VM/container)
  Pro: costo inferiore, controllo totale, nessun lock-in
  Contro: richiede competenze ops, patching, monitoring, backup

REGOLA PRATICA:
  - Team < 5 dev senza ops dedicato → managed
  - Throughput < 10k msg/sec → managed (costo ragionevole)
  - Throughput > 100k msg/sec → self-hosted (risparmio significativo)
  - Requisiti data residency stringenti → self-hosted
  - Startup in fase iniziale → managed (focus su prodotto, non infra)
```

---

## Ricette di Integrazione Avanzate

### Ricetta: Real-time Fraud Detection Pipeline

```
[Kafka: transactions.raw]
        │
        v
[Fraud Scorer Consumer]
  - Arricchisce con dati storici (Redis lookup)
  - Applica regole ML scoring
  - Score > soglia → [Kafka: transactions.suspicious]
  - Score OK → [Kafka: transactions.approved]
        │                           │
        v                           v
[Alert Consumer]             [Ledger Consumer]
  - Slack #fraud-alerts        - Aggiorna saldo
  - Blocca carta (API bank)   - Aggiorna report
  - Crea ticket investigation
```

### Ricetta: Multi-Region Event Replication

Per sistemi che devono operare in più regioni con bassa latenza:

```
Regione EU                          Regione US
┌─────────────┐                    ┌─────────────┐
│ Kafka EU    │ ←── MirrorMaker ──→│ Kafka US    │
│ (primary)   │     2 / Cluster   │ (replica)   │
│             │     Linking        │             │
│ Topic:      │                    │ Topic:      │
│ orders.eu   │                    │ orders.us   │
│ orders.us   │ (replicated)       │ orders.eu   │ (replicated)
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       v                                  v
[Consumer EU]                       [Consumer US]
  processa orders.eu                  processa orders.us
  + read-only orders.us              + read-only orders.eu
```

**Attenzione**: la replicazione cross-region introduce latenza (50-200ms tra EU-US). Non usare per operazioni che richiedono consistenza forte — accettare eventual consistency.

### Ricetta: IoT Telemetry Pipeline con Downsampling

```
[MQTT Broker: dispositivi IoT]
        │ (migliaia di msg/sec)
        v
[Kafka: iot.telemetry.raw] (retention: 24h, 12 partitions)
        │
        ├─→ [Real-time Consumer]
        │     Allarmi immediati (temperatura > soglia)
        │     → [Kafka: iot.alerts] → [PagerDuty/SMS]
        │
        ├─→ [Downsampling Consumer]
        │     Aggrega per minuto (media, min, max)
        │     → [Kafka: iot.telemetry.1min]
        │     → [TimescaleDB: metriche_1min]
        │
        └─→ [Archival Consumer]
              Ogni 6h, comprimi e archivia
              → [S3: raw-telemetry/YYYY/MM/DD/HH/]
              (retention S3: 1 anno, Glacier: 7 anni)
```

---

## FAQ — Domande Frequenti Event-Driven Architecture

### 1. Quando devo usare RabbitMQ e quando Kafka?

**RabbitMQ**: task queue (distribuzione lavoro tra worker), routing complesso (exchange direct/topic/fanout/headers), messaggi transitori con ack, RPC asincrono, protocolli multipli (AMQP, MQTT, STOMP). **Kafka**: event log (replay, audit), streaming ad alto throughput, event sourcing, CDC, aggregazioni real-time. Regola pratica: se il messaggio è un "comando" da eseguire → RabbitMQ. Se è un "fatto" da registrare → Kafka.

### 2. Cosa significa "exactly-once" delivery e quando è realmente possibile?

"Exactly-once" significa che ogni messaggio viene elaborato esattamente una volta, senza duplicati e senza perdite. In un sistema distribuito, è impossibile da garantire a livello di protocollo. Kafka offre "exactly-once semantics" (EOS) tramite transazioni idempotenti producer + read-committed consumer, ma solo all'interno dell'ecosistema Kafka. In pratica, la strategia migliore è "at-least-once delivery" + idempotency lato consumer.

### 3. Come dimensiono il numero di partizioni Kafka?

Regola iniziale: `partitions = max(target_throughput / throughput_per_partition, consumer_count)`. Throughput per partizione: ~10 MB/sec in write, ~20 MB/sec in read. Esempio: per 100 MB/sec di write e 10 consumer → `max(100/10, 10) = 10 partizioni`. Attenzione: aumentare le partizioni è facile, ridurle è impossibile senza ricreare il topic. Partire con un valore conservativo (es. 12) e scalare.

### 4. Quando usare log compaction vs time-based retention?

**Time-based retention** (`retention.ms`): per eventi transazionali dove serve la storia recente (ordini, transazioni, log). Dopo il periodo di retention, i messaggi vengono eliminati. **Log compaction** (`cleanup.policy=compact`): per topic che rappresentano lo stato corrente di un'entità (profili utente, configurazioni, inventario). Mantiene solo l'ultimo valore per ogni chiave. Combinare entrambi: `compact,delete` con `min.compaction.lag.ms` per avere compaction + pulizia degli antichi.

### 5. Come gestisco il replay di eventi in produzione?

(1) Per replay da Kafka: resettare l'offset del consumer group alla posizione desiderata: `kafka-consumer-groups.sh --reset-offsets --to-datetime '2026-05-01T00:00:00.000' --execute`. (2) Per replay da DLQ: script dedicato che legge dalla DLQ e ripubblica sul topic originale, rispettando il rate limit. (3) Prerequisito: il consumer DEVE essere idempotente, altrimenti il replay causa duplicati.

### 6. Cos'e la "poison pill" e come la gestisco?

Un messaggio che causa un errore fatale nel consumer ad ogni tentativo di elaborazione (es. JSON malformato, schema incompatibile, bug nel consumer). Il consumer si blocca, riprova all'infinito, e non avanza mai. Soluzione: (1) limitare i retry per messaggio (es. max 3). (2) Dopo N fallimenti, spostare il messaggio nella DLQ. (3) Il consumer avanza al messaggio successivo. (4) Alert sulla DLQ + runbook per investigare.

### 7. Event sourcing vs event notification: quale scegliere?

**Event notification**: "è successo qualcosa, agisci se ti interessa" (es. `order.created`). Il consumer deve fare query per ottenere i dettagli. Accoppiamento basso, ma richiede API per il dettaglio. **Event sourcing**: lo stato dell'applicazione è derivato dalla sequenza completa di eventi. Ogni evento contiene tutti i dati necessari per ricostruire lo stato. Più complesso, ma offre audit trail completo, time travel, e debugging potente. Scegliere event notification per la maggior parte dei casi; event sourcing solo quando serve audit trail, time travel, o undo/redo.

### 8. Come testo un sistema event-driven in locale?

(1) **Docker Compose**: definire broker, Schema Registry, e consumer in un `docker-compose.yml`. (2) **Testcontainers**: per test di integrazione, creare container effimeri del broker. (3) **Embedded broker**: RabbitMQ ha `rabbitmq-mock`, Kafka ha `EmbeddedKafka` (Spring) o `confluent-kafka-python` con `AdminClient` su broker locale. (4) **Contract testing**: verificare che i producer e consumer concordino sullo schema senza bisogno di un broker reale.

### 9. Come gestisco gli eventi cross-boundary (tra microservizi di team diversi)?

(1) **Definire un contratto esplicito**: schema Avro/Protobuf nel Schema Registry, con owner chiaramente definito. (2) **Backward compatibility obbligatoria**: chi modifica lo schema deve mantenere la compatibilità all'indietro. (3) **Versioning del topic**: per breaking change, creare un nuovo topic (v2) e deprecare il vecchio con periodo di migrazione. (4) **Event catalog**: documentare tutti gli eventi pubblicati, il loro schema, l'owner, e i consumer noti.

### 10. Qual e la differenza tra CDC e Outbox pattern?

**CDC (Change Data Capture)**: cattura le modifiche al database leggendo il transaction log (WAL in PostgreSQL, binlog in MySQL). Non richiede modifiche al codice applicativo. Tool: Debezium. **Outbox pattern**: l'applicazione scrive esplicitamente una riga nella tabella `outbox` nella stessa transazione del dato principale. Un processo separato (poller o CDC sulla tabella outbox) legge e pubblica gli eventi. Il CDC è più trasparente ma cattura TUTTE le modifiche (anche quelle interne); l'Outbox è più esplicito — pubblica solo gli eventi che il dominio vuole rendere visibili.

### 11. Come gestisco la migrazione da un broker a un altro (es. RabbitMQ → Kafka)?

(1) **Dual write temporaneo**: il producer pubblica su entrambi i broker durante il periodo di migrazione. (2) I consumer migrano uno alla volta dal vecchio al nuovo broker. (3) Quando tutti i consumer sono migrati, disattivare il dual write. (4) Alternativa: usare un bridge (es. Kafka Connect con source connector RabbitMQ) per leggere da RabbitMQ e scrivere su Kafka.

### 12. Come implemento un timeout su una saga distribuita?

(1) Quando la saga inizia, pubblicare un "deadline event" su un topic di scheduling con timestamp futuro. (2) Un servizio di scheduling (o Kafka Streams con windowing) monitora le deadline. (3) Se la saga non completa entro il timeout, il servizio pubblica un `saga.timed_out` event che attiva la compensazione. (4) Alternativa: usare un orchestratore di saga con timer integrato (es. Temporal, Camunda).

### 13. Redis Streams vs Kafka per volumi bassi (< 1000 msg/sec)?

Per volumi bassi, Redis Streams è spesso preferibile: (1) latenza inferiore (sub-millisecondo vs millisecondi). (2) Infrastruttura più leggera (Redis è già presente in molte architetture). (3) Operativamente più semplice (nessun ZooKeeper/KRaft). (4) Limitazioni: no consumer group sofisticati come Kafka, no retention policy nativa, no compaction. Per volumi bassi con requisiti semplici, Redis Streams. Per crescita prevista o requisiti avanzati, iniziare con Kafka.

### 14. Come gestisco gli schemi in un sistema senza Schema Registry?

(1) Includere `schema_version` nel payload di ogni evento. (2) I consumer devono gestire N versioni in parallelo (pattern "multi-version consumer"). (3) Documentare gli schemi in un repository Git condiviso. (4) Validare lo schema lato consumer prima del processing. Funziona per sistemi piccoli; con più di 10 tipi di evento o 5 team, investire in un Schema Registry.

### 15. Come faccio capacity planning per un cluster Kafka?

Formula base:
```
Broker: max(
  throughput_totale / throughput_per_broker,
  3  # minimo per HA
)

Partizioni per topic: max(
  throughput_topic / throughput_per_partizione,
  consumer_count_max_previsto
)

Disco per broker:
  throughput_medio_MB_sec × retention_secondi × replication_factor / num_broker

RAM per broker:
  ~4 GB base + page cache (25% del dataset attivo)
```

Esempio: 50 MB/sec ingestion, retention 7 giorni, replication factor 3, 5 broker:
`50 × 86400 × 7 × 3 / 5 = ~18 TB per broker`. Con compressione (snappy): ~9 TB.

---

## Osservabilita per Sistemi Event-Driven

### Le Tre Colonne dell'Osservabilita

```
METRICHE                    LOG                         TRACE
(numeri aggregati)          (eventi discreti)           (flusso end-to-end)
┌─────────────────┐        ┌─────────────────┐         ┌─────────────────┐
│ consumer_lag     │        │ Structured JSON  │         │ correlation_id   │
│ msg_rate_in/out  │        │ per evento       │         │ attraversa tutti │
│ error_rate       │        │ processato/fallito│        │ i servizi        │
│ processing_time  │        │                  │         │                  │
│ queue_depth      │        │ Include:         │         │ OpenTelemetry    │
│ replication_lag  │        │ - event_id       │         │ + Jaeger/Zipkin  │
│                  │        │ - processing_ms  │         │                  │
│ Prometheus/      │        │ - outcome        │         │ Visualizza il    │
│ Grafana          │        │ - error (if any) │         │ percorso di un   │
│                  │        │                  │         │ evento attraverso│
│                  │        │ ELK / Loki       │         │ N servizi        │
└─────────────────┘        └─────────────────┘         └─────────────────┘
```

### Metriche Essenziali per Broker

| Metrica | RabbitMQ | Kafka | Soglia Allarme |
|---|---|---|---|
| Messaggi in coda | `queue_messages_ready` | `consumer_lag` | > 10.000 |
| Throughput in | `message_publish_rate` | `bytes_in_per_sec` | Trend crescente anomalo |
| Throughput out | `message_deliver_rate` | `bytes_out_per_sec` | < throughput_in per > 30 min |
| Errori consumer | custom metric | custom metric | > 1% del totale |
| Latenza processing | custom metric | custom metric | p99 > 5 × p50 |
| Disco utilizzato | `disk_free` | `log_size` | > 80% capacità |
| Connessioni attive | `connections` | `active_connections` | Drop improvviso |

### Dashboard Template

```
┌────────────────────────────────────────────────────┐
│ EVENT-DRIVEN SYSTEM — DASHBOARD OPERATIVO          │
├────────────────────┬───────────────────────────────┤
│ CONSUMER LAG       │ ████████░░ 8.234 msg          │
│ (ultime 4h)        │ [grafico trend]               │
├────────────────────┼───────────────────────────────┤
│ THROUGHPUT         │ IN:  12.340 msg/sec            │
│                    │ OUT: 12.100 msg/sec            │
│                    │ DELTA: +240 msg/sec            │
├────────────────────┼───────────────────────────────┤
│ ERROR RATE         │ 0.02% (ultimi 15 min)          │
│                    │ DLQ: 3 nuovi messaggi          │
├────────────────────┼───────────────────────────────┤
│ P99 LATENCY        │ Processing: 45ms               │
│                    │ End-to-end: 120ms              │
├────────────────────┼───────────────────────────────┤
│ BROKER HEALTH      │ RabbitMQ: ✓ 3/3 nodi          │
│                    │ Disco: 42% utilizzato          │
│                    │ RAM: 61% utilizzata            │
├────────────────────┼───────────────────────────────┤
│ TOP 5 TOPIC        │ orders.events: 4.500 msg/sec   │
│ (per throughput)   │ payments.events: 3.200 msg/sec │
│                    │ inventory.updates: 2.100 msg/s │
│                    │ notifications: 1.800 msg/sec   │
│                    │ audit.log: 740 msg/sec         │
└────────────────────┴───────────────────────────────┘
```

### Tracing Distribuito per Eventi

Ogni evento deve propagare il contesto di tracciamento:

```python
# Producer: iniettare trace context nell'evento
from opentelemetry import trace
from opentelemetry.propagate import inject

tracer = trace.get_tracer("order-service")

def publish_order_event(order: dict):
    with tracer.start_as_current_span("publish_order_created") as span:
        headers = {}
        inject(headers)  # inietta traceparent, tracestate

        event = {
            "type": "order.created",
            "data": order,
            "metadata": {
                "traceparent": headers.get("traceparent"),
                "tracestate": headers.get("tracestate"),
                "correlation_id": order["order_id"]
            }
        }
        # publish to broker con headers
        producer.send("orders.events", value=event, headers=list(headers.items()))
        span.set_attribute("order.id", order["order_id"])
```

```python
# Consumer: estrarre trace context e continuare la traccia
from opentelemetry.propagate import extract

def process_order_event(message):
    ctx = extract(dict(message.headers()))
    with tracer.start_as_current_span(
        "process_order_created",
        context=ctx
    ) as span:
        order = message.value()["data"]
        span.set_attribute("order.id", order["order_id"])
        # processing...
```

Il risultato: in Jaeger/Zipkin si vede una traccia unica che attraversa producer → broker → consumer → downstream services, con timing preciso per ogni hop.

### Alerting per Sistemi Event-Driven

Regole di alerting raccomandate:

| Allarme | Condizione | Severita | Azione |
|---|---|---|---|
| Consumer down | Consumer group senza membri attivi | CRITICAL | Riavviare consumer, verifica deploy |
| Lag critico | Lag > 100.000 per > 10 min | CRITICAL | Scale out consumer, verifica bottleneck |
| DLQ crescente | > 10 nuovi msg DLQ in 1h | HIGH | Investigare causa, fix + replay |
| Broker disco pieno | Disco > 90% | CRITICAL | Ridurre retention, aggiungere disco |
| Throughput anomalo | Throughput < 10% della media | HIGH | Verifica producer, rete, broker |
| Replicazione fallita | ISR < replication.factor | HIGH | Verifica broker lento/down |
| Schema rejection | > 0 per 5 min | MEDIUM | Verifica producer, schema evolution |

---

## Pattern di Testing per Sistemi Event-Driven

### Test di Integrazione con Testcontainers

```python
# Test di integrazione con RabbitMQ in container Docker
import pytest
from testcontainers.rabbitmq import RabbitMqContainer

@pytest.fixture(scope="module")
def rabbitmq():
    with RabbitMqContainer("rabbitmq:3.13-management") as rabbit:
        yield rabbit

def test_order_event_processing(rabbitmq):
    connection_url = rabbitmq.get_connection_url()

    # Setup
    producer = create_producer(connection_url)
    consumer = create_consumer(connection_url, queue="orders")

    # Arrange
    order_event = {
        "type": "order.created",
        "data": {"order_id": "test-001", "amount": 99.99}
    }

    # Act
    producer.publish("orders.exchange", order_event)
    result = consumer.consume_one(timeout=5)

    # Assert
    assert result is not None
    assert result["data"]["order_id"] == "test-001"
```

### Contract Testing tra Producer e Consumer

Verificare che producer e consumer concordino sullo schema senza bisogno di un broker reale:

```python
# contract_test.py
import json
import jsonschema

ORDER_CREATED_SCHEMA = {
    "type": "object",
    "required": ["type", "data", "metadata"],
    "properties": {
        "type": {"const": "order.created"},
        "data": {
            "type": "object",
            "required": ["order_id", "customer_id", "amount", "currency"],
            "properties": {
                "order_id": {"type": "string"},
                "customer_id": {"type": "string"},
                "amount": {"type": "number", "minimum": 0},
                "currency": {"type": "string", "pattern": "^[A-Z]{3}$"}
            }
        },
        "metadata": {
            "type": "object",
            "required": ["schema_version", "timestamp"],
        }
    }
}

def test_producer_output_matches_contract():
    """Il producer genera eventi conformi al contratto."""
    event = produce_order_created_event(order_id="o1", customer_id="c1", amount=50.0)
    jsonschema.validate(event, ORDER_CREATED_SCHEMA)

def test_consumer_handles_contract_event():
    """Il consumer elabora correttamente eventi conformi al contratto."""
    event = {
        "type": "order.created",
        "data": {"order_id": "o1", "customer_id": "c1", "amount": 50.0, "currency": "EUR"},
        "metadata": {"schema_version": "1.0", "timestamp": "2026-05-22T10:00:00Z"}
    }
    result = consumer_process(event)
    assert result.success is True
```

### Chaos Testing

Scenari di chaos da testare periodicamente in staging:

1. **Kill consumer random**: verificare che i messaggi vengano redistribuiti agli altri consumer del group.
2. **Network partition**: simulare partizione di rete tra producer e broker — verificare retry e nessuna perdita.
3. **Broker restart**: riavviare un nodo broker sotto carico — verificare che il cluster continui a funzionare.
4. **DLQ flood**: inviare 1000 messaggi malformati — verificare che il consumer non si blocchi e che la DLQ funzioni.
5. **Disk full**: simulare disco pieno sul broker — verificare allarmi e comportamento del producer (backpressure o errore).
6. **Clock skew**: spostare l'orologio di un nodo — verificare che timestamp e ordering funzionino correttamente.

---

## Riferimenti

- RabbitMQ Documentation: https://www.rabbitmq.com/documentation.html
- Apache Kafka Documentation: https://kafka.apache.org/documentation/
- Confluent Schema Registry: https://docs.confluent.io/platform/current/schema-registry/index.html
- Debezium: https://debezium.io/documentation/
- CloudEvents Specification: https://github.com/cloudevents/spec
- NATS JetStream: https://docs.nats.io/nats-concepts/jetstream
- Redis Streams: https://redis.io/docs/data-types/streams/
- Microservices Patterns (Chris Richardson) — capitoli su Saga e Event Sourcing
- Designing Event-Driven Systems (Ben Stopford) — O'Reilly free ebook
- Enterprise Integration Patterns (Gregor Hohpe) — il classico di riferimento
- Sistema di Interscambio (Agenzia delle Entrate): https://www.fatturapa.gov.it/

---

## Letture e Riferimenti

### Documentazione ufficiale

- RabbitMQ — Tutorials (Hello World, Work Queues, Pub/Sub): https://www.rabbitmq.com/tutorials (consultato: 2026-05-24)
- RabbitMQ — Dead Letter Exchanges: https://www.rabbitmq.com/docs/dlx (consultato: 2026-05-24)
- Apache Kafka — Producer and Consumer Configs: https://kafka.apache.org/documentation/#configuration (consultato: 2026-05-24)
- Confluent — Kafka Exactly-Once Semantics: https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/ (consultato: 2026-05-24)
- CloudEvents Specification — Primer: https://github.com/cloudevents/spec/blob/main/cloudevents/primer.md (consultato: 2026-05-24)
- Debezium — Change Data Capture Tutorial: https://debezium.io/documentation/reference/stable/tutorial.html (consultato: 2026-05-24)

### Libri

- **"Designing Data-Intensive Applications"** — Martin Kleppmann (O'Reilly). Capitoli su stream processing, message brokers e architetture event-driven — il riferimento fondamentale.
- **"Enterprise Integration Patterns"** — Gregor Hohpe, Bobby Woolf (Addison-Wesley). Catalogo dei pattern di messaging (routing, transformation, dead letter channel) su cui si basa tutta l'architettura event-driven moderna.

---

## Esercizi

1. **Lab — RabbitMQ task queue.** Producer Python invia 1000 task; 5 worker consumano con ack manuale + retry exponential; DLQ per failure.
2. **Lab — Kafka event log.** Topic con 3 partition; producer scrive eventi con key (user_id); 3 consumer in stesso group consumano in parallelo.
3. **Stretch — pattern saga.** Implementa saga distribuita 3-step (order → payment → ship) con compensation actions.

## Auto-valutazione

1. RabbitMQ vs Kafka: criteri di scelta.
2. Auto-ack vs manual ack: rischio.
3. DLQ: come popolarla?
4. Partition key: a cosa serve?
5. Backpressure: 3 strategie.

## Collegamenti incrociati

- Modulo 22 (NEW) — `22-dlq-parking-lot-pattern.md`: DLQ deep dive.
- Modulo 23 (NEW) — `23-osservabilita-workflow-otel.md`: tracing eventi.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Event-driven architecture** | Architettura basata su eventi async. |
| **Producer** | Componente che emette eventi. |
| **Consumer** | Componente che processa eventi. |
| **Queue** | Buffer FIFO (RabbitMQ). |
| **Topic** | Canale broadcast (Kafka). |
| **Partition** | Sotto-divisione di topic per parallelizzazione. |
| **Consumer group** | Insieme consumer che condividono lavoro. |
| **DLQ** | Dead Letter Queue. |
| **Ack manuale** | Worker conferma elaborazione, no auto. |
| **Backpressure** | Meccanismo per limitare carico downstream. |
| **Saga pattern** | Distributed transaction con compensation. |
