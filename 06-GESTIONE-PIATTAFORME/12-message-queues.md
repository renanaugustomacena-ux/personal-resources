---
corso: "Gestione Piattaforme e DevOps"
fase: "5 — Dati e Messaging"
modulo: 12
titolo: "Message Queues e Event-Driven Architecture"
versione: "Kafka 3.8 · RabbitMQ 4.1 · NATS 2.11"
livello: "Avanzato"
prerequisiti:
  - "05-kubernetes.md"
  - "08-monitoring-observability.md"
  - "11-database-management.md"
obiettivi:
  - "Distinguere i pattern di messaging (task queue, event log, pub/sub) e selezionare la tecnologia appropriata"
  - "Configurare Kafka, RabbitMQ e NATS in alta disponibilita con replication e partitioning"
  - "Implementare consumer idempotenti, dead-letter queue e strategie di retry"
  - "Progettare architetture event-driven con schema registry ed event sourcing"
  - "Monitorare broker e consumer con metriche di lag, throughput e latenza"
tag: [kafka, rabbitmq, nats, event-driven, dlq, idempotency, schema-registry, pub-sub]
---

# Message Queues e Event-Driven Architecture — Documentazione Completa

> **Modulo 12** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Distinguere i pattern di messaging (task queue, event log, pub/sub) e selezionare la tecnologia appropriata
> 2. Configurare Kafka, RabbitMQ e NATS in alta disponibilita con replication e partitioning
> 3. Implementare consumer idempotenti, dead-letter queue e strategie di retry
> 4. Progettare architetture event-driven con schema registry ed event sourcing
> 5. Monitorare broker e consumer con metriche di lag, throughput e latenza
>
> **Prerequisiti:** [Kubernetes](05-kubernetes.md) · [Monitoring e Observability](08-monitoring-observability.md) · [Database Management](11-database-management.md)
> **Tempo stimato:** 8-12 ore · **Livello:** Avanzato

## Idee guida

1. **RabbitMQ task queue, Kafka event log.** Use case diversi.
2. **DLQ mandatory.** Senza, messaggi failed perdersi silently.
3. **Idempotency consumer-side.** Producer puo retry; consumer dedup.
4. **Exactly-once impossibile distributed; at-least-once + idempotency = effective once.**


## Indice

1. [Panoramica e Concetti Fondamentali](#1-panoramica-e-concetti-fondamentali)
2. [RabbitMQ](#2-rabbitmq)
3. [RabbitMQ — Configurazione Avanzata](#3-rabbitmq--configurazione-avanzata)
4. [Apache Kafka](#4-apache-kafka)
5. [Kafka — Operazioni e Ecosystem](#5-kafka--operazioni-e-ecosystem)
6. [NATS](#6-nats)
7. [Cloud Messaging Services](#7-cloud-messaging-services)
8. [Event-Driven Architecture](#8-event-driven-architecture)
9. [Stream Processing](#9-stream-processing)
10. [Performance e Tuning](#10-performance-e-tuning)
11. [Monitoring e Troubleshooting](#11-monitoring-e-troubleshooting)
12. [Best Practices](#12-best-practices)
13. [Broker Alternativi](#13-broker-alternativi)

---

## 1. Panoramica e Concetti Fondamentali

### Cos'e un Message Queue

Un message queue e un componente di middleware che consente la comunicazione asincrona tra servizi disaccoppiati. Il producer inserisce messaggi in una coda e il consumer li preleva in modo indipendente, eliminando la necessita di accoppiamento temporale diretto.

### Messaging Patterns

**Point-to-Point (Queue):**
Un singolo messaggio viene consumato da esattamente un consumer. Piu consumer possono competere per i messaggi (competing consumers pattern), ma ogni messaggio e processato una sola volta. Questo pattern e ideale per work distribution e task processing.

**Publish/Subscribe (Pub/Sub):**
Un messaggio pubblicato su un topic viene consegnato a tutti i subscriber attivi. Ogni subscriber riceve una copia indipendente del messaggio. E il pattern dominante per event notification e broadcasting.

**Request/Reply:**
Il producer invia un messaggio e attende una risposta su una coda temporanea (reply-to queue). Il correlation ID collega la richiesta alla risposta corrispondente. Utile per RPC asincrono.

### Message Queue vs Event Stream

| Caratteristica | Message Queue | Event Stream |
|---|---|---|
| Consumo | Distruttivo (il messaggio viene rimosso) | Non distruttivo (l'evento rimane nel log) |
| Replay | Non supportato nativamente | Supportato tramite offset reset |
| Consumer model | Competing consumers | Consumer groups con partizioni |
| Ordinamento | FIFO per coda | Per partizione |
| Retention | Fino al consumo | Time-based o size-based |
| Esempio | RabbitMQ, SQS | Kafka, Kinesis, Pulsar |

### Architettura del Message Broker

Un message broker funge da intermediario tra producer e consumer. I componenti principali includono:

- **Connection manager:** gestisce le connessioni TCP/TLS dai client
- **Protocol handler:** implementa il protocollo di messaging (AMQP, MQTT, STOMP)
- **Routing engine:** determina la destinazione dei messaggi in base a regole, exchange type o topic
- **Storage engine:** persiste i messaggi su disco o in memoria
- **Delivery engine:** gestisce il dispatching ai consumer con acknowledgment tracking

### Garanzie di Consegna

**At-most-once:** il messaggio viene inviato una sola volta senza conferma. Se il consumer fallisce, il messaggio e perso. Massimo throughput, minima garanzia. Adatto per metriche non critiche o telemetria dove la perdita occasionale e accettabile.

**At-least-once:** il broker ritrasmette il messaggio finche non riceve un acknowledgment dal consumer. Il messaggio puo essere consegnato piu volte in caso di fallimento prima dell'ack. Richiede che il consumer sia idempotente.

**Exactly-once:** semantica piu complessa, richiede coordinamento tra producer, broker e consumer. Implementata tramite transazioni (Kafka transactional API) o deduplicazione lato consumer. Ha un costo significativo in termini di latenza e throughput.

### Ordering Guarantees

L'ordinamento totale (total ordering) e garantito solo all'interno di una singola partizione o coda. Per ottenere ordinamento tra messaggi correlati si usa una partition key (ad esempio l'ID utente), assicurando che tutti i messaggi con la stessa chiave vadano nella stessa partizione.

L'ordinamento globale su piu partizioni non e garantito e richiede pattern aggiuntivi (sequence numbers, vector clocks).

### Dead Letter Queues (DLQ)

Una dead letter queue raccoglie messaggi che non possono essere processati con successo:

- Messaggi rifiutati esplicitamente dal consumer (nack/reject)
- Messaggi che superano il numero massimo di tentativi (max retries)
- Messaggi scaduti per TTL (time-to-live)
- Messaggi che non corrispondono a nessun routing

La DLQ consente di analizzare e riprovare i messaggi falliti senza bloccare la coda principale. E fondamentale monitorare la profondita della DLQ e configurare alerting.

### Backpressure

Il backpressure e un meccanismo per prevenire il sovraccarico del sistema quando i consumer non riescono a tenere il passo con i producer. Strategie comuni:

- **Prefetch limit:** limitare il numero di messaggi non-acknowledged per consumer
- **Flow control:** il broker rallenta o blocca i producer quando la memoria supera una soglia
- **Rate limiting:** limitare il rate di pubblicazione lato producer
- **Bounded queues:** impostare un max-length sulla coda, scartando o rifiutando messaggi in eccesso

### Idempotenza dei Consumatori

Un consumer idempotente produce lo stesso risultato indipendentemente dal numero di volte che processa lo stesso messaggio. Tecniche di implementazione:

- **Deduplication table:** memorizzare il message ID in un database e verificarlo prima dell'elaborazione
- **Idempotency key:** utilizzare una chiave unica nel messaggio per operazioni upsert
- **Conditional writes:** utilizzare version number o ETag per evitare scritture duplicate
- **Idempotent operations:** progettare le operazioni stesse come idempotenti (SET vs INCREMENT)

### Saga Pattern per Transazioni Distribuite

Il saga pattern gestisce transazioni distribuite decomponendole in una sequenza di transazioni locali, ciascuna con una compensating transaction in caso di fallimento.

**Orchestration-based saga:** un orchestratore centrale coordina la sequenza di step, invocando ogni servizio e gestendo le compensazioni in caso di errore.

**Choreography-based saga:** ogni servizio pubblica eventi e reagisce agli eventi degli altri. Non c'e un coordinatore centrale; la logica di flusso e distribuita.

```
# Esempio concettuale di saga per un ordine e-commerce
1. OrderService: crea ordine (stato=PENDING)
2. PaymentService: addebita pagamento
   - Compensazione: rimborso pagamento
3. InventoryService: riserva stock
   - Compensazione: rilascia stock
4. ShippingService: avvia spedizione
   - Compensazione: annulla spedizione
5. OrderService: conferma ordine (stato=CONFIRMED)
```

---

## 2. RabbitMQ

### Architettura AMQP 0-9-1

RabbitMQ implementa il protocollo AMQP 0-9-1 (Advanced Message Queuing Protocol). Il protocollo definisce un modello di messaging programmabile con entita di routing (exchange) e storage (queue).

Il flusso dei messaggi segue il percorso: **Producer -> Connection -> Channel -> Exchange -> Binding -> Queue -> Channel -> Connection -> Consumer**.

### Componenti Fondamentali

**Connection:** una connessione TCP persistente tra il client e il broker RabbitMQ. Ogni connessione gestisce l'handshake AMQP, l'autenticazione e il TLS. E costosa da creare e deve essere riutilizzata.

**Channel:** un canale virtuale multiplex su una singola connessione TCP. Le operazioni AMQP avvengono su un channel. Un'applicazione usa tipicamente un channel per thread.

**Exchange:** il componente di routing che riceve i messaggi dal producer e li instrada verso una o piu code in base al tipo di exchange e al routing key.

**Queue:** il buffer che memorizza i messaggi fino al consumo. Puo essere durable (sopravvive al restart), exclusive (usata solo dalla connessione che l'ha dichiarata), auto-delete (rimossa quando l'ultimo consumer si disconnette).

**Binding:** la regola che collega un exchange a una queue tramite un binding key. Il matching tra routing key e binding key dipende dal tipo di exchange.

### Tipi di Exchange

**Direct Exchange:** routing esatto. Il messaggio e instradato alla coda il cui binding key corrisponde esattamente al routing key del messaggio. Utilizzato per task routing.

**Topic Exchange:** routing pattern-based. Il binding key supporta wildcard: `*` corrisponde a una singola parola, `#` corrisponde a zero o piu parole separate da `.`. Esempio: `order.*.created` matcha `order.eu.created`.

**Fanout Exchange:** broadcast. Il messaggio e inviato a tutte le code collegate all'exchange, ignorando il routing key. Ideale per notifiche broadcast.

**Headers Exchange:** routing basato sugli header del messaggio invece che sul routing key. L'argomento `x-match` specifica se tutti (`all`) o almeno uno (`any`) degli header devono corrispondere.

### Prefetch e QoS

Il prefetch count limita il numero di messaggi non-acknowledged che il broker invia a un consumer. Controlla il parallelismo lato consumer e previene il sovraccarico.

```bash
# rabbitmq.conf — impostazione globale del prefetch
consumer_timeout = 1800000
channel_max = 2047
```

```python
# Python con pika — impostazione del prefetch per canale
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)
channel = connection.channel()
channel.basic_qos(prefetch_count=10)  # max 10 messaggi non-acked per consumer
```

### Acknowledgment

**Manual acknowledgment:** il consumer conferma esplicitamente l'elaborazione del messaggio. Se il consumer fallisce prima dell'ack, il messaggio viene riconsegnato a un altro consumer.

**Auto acknowledgment:** il broker considera il messaggio consegnato appena lo invia al consumer. Se il consumer fallisce, il messaggio e perso. Solo per scenari non critici.

```python
# Manual ack con pika
def callback(ch, method, properties, body):
    try:
        process_message(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        # Rifiuta e ricoda il messaggio
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

channel.basic_consume(
    queue='task_queue',
    on_message_callback=callback,
    auto_ack=False  # Manual ack abilitato
)
```

### Publisher Confirms

Il publisher confirms e un meccanismo in cui il broker conferma al producer che ha ricevuto e persistito il messaggio. Essenziale per garantire che i messaggi non vengano persi.

```python
# Abilitare publisher confirms
channel.confirm_delivery()

try:
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body='messaggio importante',
        properties=pika.BasicProperties(
            delivery_mode=2,  # Messaggio persistente
        )
    )
    print("Messaggio confermato dal broker")
except pika.exceptions.UnroutableError:
    print("Messaggio non instradabile")
```

### Clustering

RabbitMQ supporta clustering per alta disponibilita e scalabilita. I nodi di un cluster condividono utenti, vhost, exchange, binding e code.

**Disc nodes:** persistono i metadati su disco. Almeno un disc node e richiesto nel cluster.

**RAM nodes:** mantengono i metadati solo in memoria per prestazioni superiori. Utili per nodi transienti.

```bash
# Aggiungere un nodo al cluster
rabbitmqctl stop_app
rabbitmqctl reset
rabbitmqctl join_cluster rabbit@node1
rabbitmqctl start_app

# Verificare lo stato del cluster
rabbitmqctl cluster_status
```

### Quorum Queues (Raft-based)

Le quorum queues sono il tipo di coda replicata raccomandato da RabbitMQ 3.8+. Basate sull'algoritmo di consenso Raft, offrono garanzie di durabilita e consistenza superiori alle classic mirrored queues.

```bash
# Dichiarare una quorum queue via CLI
rabbitmqadmin declare queue name=orders durable=true \
  arguments='{"x-queue-type": "quorum"}'
```

```python
# Dichiarare una quorum queue via pika
channel.queue_declare(
    queue='orders',
    durable=True,
    arguments={'x-queue-type': 'quorum'}
)
```

Le classic mirrored queues (`ha-mode`, `ha-params`) sono deprecate a partire da RabbitMQ 4.x e verranno rimosse. Migrare alle quorum queues per nuove installazioni.

### RabbitMQ 4.x — Novita Principali

RabbitMQ 4.x introduce cambiamenti strutturali significativi che influenzano l'architettura del cluster, le garanzie di durabilita e le capacita operative del broker.

**Rimozione delle Classic Mirrored Queues:** a partire dalla versione 4.0, il mirroring classico delle code e stato completamente rimosso. Le quorum queues e gli stream sono le uniche tipologie di code replicate supportate. Tutti i deployment esistenti che utilizzano `ha-mode` o `ha-params` devono migrare prima dell'upgrade. La migrazione richiede la creazione di nuove quorum queues, lo spostamento dei consumer e dei producer, e la successiva eliminazione delle code classiche.

**Khepri Metadata Store (RabbitMQ 4.3+):** Khepri sostituisce completamente Mnesia come metadata store. Basato anch'esso su Raft, Khepri semplifica la gestione dei metadati del cluster (exchange, code, binding, utenti, permessi) e allinea la semantica di consistenza del control plane con quella delle quorum queues. La disponibilita del cluster dipende ora dalla presenza di una maggioranza di nodi online. Il recovery dopo un network partition e piu prevedibile e deterministico rispetto a Mnesia, eliminando i problemi di split-brain che affliggevano le versioni precedenti.

**Priorita Strict nelle Quorum Queues (4.3+):** le quorum queues supportano fino a 32 livelli di priorita strict. A differenza delle priority queues classiche (che usavano code separate interne), la nuova implementazione gestisce le priorita direttamente nel log Raft, garantendo la persistenza e la replicazione delle priorita.

```python
# Dichiarare una quorum queue con priorita strict (RabbitMQ 4.3+)
channel.queue_declare(
    queue='tasks.priority',
    durable=True,
    arguments={
        'x-queue-type': 'quorum',
        'x-max-priority': 32  # Supporto fino a 32 livelli
    }
)
```

**Delayed Retry con Backoff (4.3+):** le quorum queues integrano nativamente un meccanismo di delayed retry con backoff esponenziale. Quando un messaggio viene rifiutato (nack senza requeue), la coda lo mette in attesa internamente per un periodo calcolato con la formula: `min(min_delay × delivery_count, max_delay)`. Questo elimina la necessita di implementare retry exchange esterni con TTL, semplificando significativamente la topologia.

```bash
# Configurare delayed retry via policy
rabbitmqctl set_policy delayed-retry "^app\\..*" \
  '{"dead-letter-strategy": "at-least-once", \
    "delivery-limit": 5, \
    "redelivery-delay": {"min": 5000, "max": 60000}}' \
  --apply-to queues
```

Con questa configurazione, il primo retry avviene dopo 5 secondi, il secondo dopo 10, il terzo dopo 15, fino a un massimo di 60 secondi. Dopo 5 tentativi il messaggio e inviato alla DLQ.

**Consumer Timeout nelle Quorum Queues (4.3+):** il timeout per i consumer e ora gestito direttamente dalla quorum queue stessa. Se un consumer mantiene un messaggio non-acknowledged oltre il timeout configurato, il messaggio viene automaticamente restituito alla coda e reso disponibile per altri consumer. Questo previene situazioni in cui un consumer bloccato impedisce l'elaborazione dei messaggi.

**Ottimizzazione Memoria (4.3+):** una nuova rappresentazione compatta dei riferimenti ai messaggi dimezza l'overhead di memoria per messaggio fino a 32 KiB. Per code che contengono milioni di messaggi di piccole dimensioni, questo riduce significativamente la pressione sulla RAM senza alcuna modifica di configurazione.

### RabbitMQ Streams

Gli stream sono un tipo di coda introdotto in RabbitMQ 3.9 e consolidato nella serie 4.x. A differenza delle code tradizionali (dove il messaggio e rimosso dopo il consumo), gli stream mantengono un log append-only simile a Kafka, consentendo il replay e il consumo da parte di piu consumer indipendenti.

**Caratteristiche principali:**
- **Log append-only:** i messaggi non vengono eliminati al consumo ma rimangono nel log fino alla scadenza della retention
- **Offset tracking:** ogni consumer traccia il proprio offset, consentendo replay e riprocessamento
- **Fan-out efficiente:** piu consumer leggono lo stesso stream senza duplicazione dei dati
- **Alta velocita:** ottimizzati per throughput elevato con scritture sequenziali su disco
- **Protocollo dedicato:** il protocollo stream (porta 5552) offre prestazioni superiori rispetto ad AMQP per scenari di streaming

```bash
# Abilitare il plugin stream
rabbitmq-plugins enable rabbitmq_stream

# Dichiarare uno stream via CLI
rabbitmqadmin declare queue name=events.stream durable=true \
  arguments='{"x-queue-type": "stream", "x-max-length-bytes": 10737418240, "x-max-age": "7D"}'
```

```python
# Python — consumer stream con offset tracking
# Utilizzo del protocollo AMQP 0-9-1 (alternativa al protocollo stream nativo)
channel.queue_declare(
    queue='events.stream',
    durable=True,
    arguments={
        'x-queue-type': 'stream',
        'x-max-length-bytes': 10 * 1024 * 1024 * 1024,  # 10 GB
        'x-max-age': '7D'                                # 7 giorni retention
    }
)

# Consumare da un offset specifico
channel.basic_consume(
    queue='events.stream',
    on_message_callback=callback,
    arguments={'x-stream-offset': 'first'}  # 'first', 'last', 'next', offset numerico, timestamp
)
```

**Quando usare gli Stream vs le Quorum Queues:**

| Scenario | Quorum Queues | Streams |
|---|---|---|
| Task distribution (competing consumers) | Si | No |
| Fan-out a piu consumer indipendenti | No (serve un exchange) | Si |
| Replay e riprocessamento | No | Si |
| Ordinamento per consumer | FIFO | Per offset |
| Throughput elevato (100K+ msg/s) | Medio | Alto |
| Retention a lungo termine | No (consumo distruttivo) | Si |

### Federation e Shovel

**Federation:** connette exchange o code tra broker indipendenti (anche geograficamente distribuiti). I messaggi vengono copiati dal broker upstream a quello downstream on-demand. Utile per topologie multi-datacenter.

**Shovel:** un worker che consuma messaggi da una sorgente e li pubblica su una destinazione. Piu semplice della federation ma meno dinamico. Utile per migrazioni e bridging tra cluster.

```bash
# Abilitare il plugin federation
rabbitmq-plugins enable rabbitmq_federation
rabbitmq-plugins enable rabbitmq_federation_management

# Configurare un upstream
rabbitmqctl set_parameter federation-upstream my-upstream \
  '{"uri":"amqp://user:pass@remote-host","expires":3600000}'
```

### Comandi CLI Essenziali

```bash
# Gestione del nodo
rabbitmqctl status
rabbitmqctl environment
rabbitmq-diagnostics check_running
rabbitmq-diagnostics check_port_connectivity
rabbitmq-diagnostics memory_breakdown

# Gestione delle code
rabbitmqctl list_queues name messages consumers memory
rabbitmqctl list_queues name messages_ready messages_unacknowledged
rabbitmqctl purge_queue <queue_name>

# Gestione degli exchange
rabbitmqctl list_exchanges name type durable auto_delete

# Gestione dei binding
rabbitmqctl list_bindings source_name destination_name routing_key

# Gestione delle connessioni e dei canali
rabbitmqctl list_connections user peer_host peer_port state
rabbitmqctl list_channels connection channel_number consumer_count messages_unacknowledged

# Management UI
rabbitmq-plugins enable rabbitmq_management
# Accessibile su http://localhost:15672 (guest/guest in dev)
```

---

## 3. RabbitMQ — Configurazione Avanzata

### Vhost Management

I virtual host (vhost) forniscono isolamento logico all'interno di un singolo broker. Ogni vhost ha il proprio set di exchange, code, binding e permessi.

```bash
# Creare un vhost
rabbitmqctl add_vhost /production
rabbitmqctl add_vhost /staging

# Elencare i vhost
rabbitmqctl list_vhosts name tracing

# Eliminare un vhost (elimina tutte le risorse associate)
rabbitmqctl delete_vhost /staging
```

### Utenti e Permessi

```bash
# Creare un utente
rabbitmqctl add_user app_user SecureP@ssw0rd

# Impostare i tag (ruoli)
rabbitmqctl set_user_tags app_user monitoring
# Tag disponibili: management, policymaker, monitoring, administrator

# Impostare i permessi su un vhost
# Formato: set_permissions -p <vhost> <user> <configure> <write> <read>
rabbitmqctl set_permissions -p /production app_user "^app\\..*" "^app\\..*" "^(app\\.|amq\\.).*"

# Elencare i permessi
rabbitmqctl list_user_permissions app_user
rabbitmqctl list_permissions -p /production

# Eliminare l'utente guest in produzione
rabbitmqctl delete_user guest
```

### Configurazione TLS

```ini
# rabbitmq.conf — configurazione TLS completa
listeners.ssl.default = 5671
ssl_options.cacertfile = /etc/rabbitmq/ssl/ca_certificate.pem
ssl_options.certfile   = /etc/rabbitmq/ssl/server_certificate.pem
ssl_options.keyfile    = /etc/rabbitmq/ssl/server_key.pem
ssl_options.verify     = verify_peer
ssl_options.fail_if_no_peer_cert = true
ssl_options.versions.1 = tlsv1.3
ssl_options.versions.2 = tlsv1.2

# Disabilitare listener TCP non-TLS in produzione
listeners.tcp = none

# Management UI su HTTPS
management.ssl.port       = 15671
management.ssl.cacertfile  = /etc/rabbitmq/ssl/ca_certificate.pem
management.ssl.certfile    = /etc/rabbitmq/ssl/server_certificate.pem
management.ssl.keyfile     = /etc/rabbitmq/ssl/server_key.pem
```

### Message e Queue TTL

```ini
# rabbitmq.conf — TTL globale per i messaggi (30 minuti)
# Applicabile a tutte le code senza TTL specifico
# consumer_timeout = 1800000

# Policy per impostare TTL su code specifiche
```

```bash
# Impostare un message TTL di 60 secondi via policy
rabbitmqctl set_policy ttl-60s "^temp\\..*" \
  '{"message-ttl": 60000}' --apply-to queues

# Queue TTL: la coda viene eliminata dopo 30 minuti di inattivita
rabbitmqctl set_policy queue-ttl "^ephemeral\\..*" \
  '{"expires": 1800000}' --apply-to queues
```

### Max Length e Dead Letter Exchange

```bash
# Limitare la lunghezza della coda a 10000 messaggi
rabbitmqctl set_policy max-length "^bounded\\..*" \
  '{"max-length": 10000, "overflow": "reject-publish"}' --apply-to queues

# Overflow strategies: drop-head (default), reject-publish, reject-publish-dlx

# Configurare Dead Letter Exchange
rabbitmqctl set_policy dlx "^app\\..*" \
  '{"dead-letter-exchange": "dlx.exchange", "dead-letter-routing-key": "dlx.routing"}' \
  --apply-to queues
```

```python
# Dichiarare queue con DLX inline
channel.queue_declare(
    queue='app.orders',
    durable=True,
    arguments={
        'x-dead-letter-exchange': 'dlx.exchange',
        'x-dead-letter-routing-key': 'dlx.failed',
        'x-message-ttl': 300000,       # 5 minuti TTL
        'x-max-length': 50000,         # Max 50K messaggi
        'x-queue-type': 'quorum'       # Quorum queue
    }
)
```

### Lazy Queues

Le lazy queues memorizzano i messaggi su disco il prima possibile, riducendo l'utilizzo di RAM. Utili per code con milioni di messaggi o consumer lenti.

```bash
rabbitmqctl set_policy lazy "^archive\\..*" \
  '{"queue-mode": "lazy"}' --apply-to queues
```

Nota: nelle quorum queues il comportamento lazy e gestito automaticamente e non richiede configurazione separata.

### Priority Queues

```python
# Dichiarare una coda con supporto per le priorita (max 10 livelli)
channel.queue_declare(
    queue='tasks.priority',
    durable=True,
    arguments={'x-max-priority': 10}
)

# Pubblicare un messaggio con priorita alta
channel.basic_publish(
    exchange='',
    routing_key='tasks.priority',
    body='urgent task',
    properties=pika.BasicProperties(
        priority=9,
        delivery_mode=2
    )
)
```

### Memory e Disk Alarms

```ini
# rabbitmq.conf — configurazione degli allarmi
# Memory alarm: si attiva quando RabbitMQ usa piu del 40% della RAM
vm_memory_high_watermark.relative = 0.4
# Oppure in valore assoluto
# vm_memory_high_watermark.absolute = 2GB

# Paging: inizia a scrivere messaggi su disco al 50% del watermark
vm_memory_high_watermark_paging_ratio = 0.5

# Disk alarm: si attiva quando lo spazio libero scende sotto la soglia
disk_free_limit.relative = 1.5
# Oppure in valore assoluto
# disk_free_limit.absolute = 5GB
```

### Docker Deployment

```yaml
# docker-compose.yml — RabbitMQ con management UI
version: '3.8'
services:
  rabbitmq:
    image: rabbitmq:3.13-management
    hostname: rabbitmq-node1
    container_name: rabbitmq
    ports:
      - "5672:5672"     # AMQP
      - "15672:15672"   # Management UI
      - "5671:5671"     # AMQPS (TLS)
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: "${RABBITMQ_PASSWORD}"
      RABBITMQ_DEFAULT_VHOST: /production
      RABBITMQ_ERLANG_COOKIE: "${ERLANG_COOKIE}"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
      - ./rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf:ro
      - ./definitions.json:/etc/rabbitmq/definitions.json:ro
      - ./ssl:/etc/rabbitmq/ssl:ro
    healthcheck:
      test: rabbitmq-diagnostics check_port_connectivity
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'

volumes:
  rabbitmq_data:
    driver: local
```

### Kubernetes Operator

Il RabbitMQ Cluster Operator per Kubernetes gestisce il lifecycle dei cluster RabbitMQ.

```yaml
# rabbitmq-cluster.yaml — CRD per il Cluster Operator
apiVersion: rabbitmq.com/v1beta1
kind: RabbitmqCluster
metadata:
  name: production-rabbitmq
  namespace: messaging
spec:
  replicas: 3
  image: rabbitmq:3.13-management
  resources:
    requests:
      cpu: "1"
      memory: 2Gi
    limits:
      cpu: "2"
      memory: 4Gi
  persistence:
    storageClassName: fast-ssd
    storage: 50Gi
  rabbitmq:
    additionalConfig: |
      vm_memory_high_watermark.relative = 0.4
      disk_free_limit.relative = 1.5
      cluster_partition_handling = pause_minority
      default_user = admin
      default_pass = CHANGEME
      consumer_timeout = 3600000
    additionalPlugins:
      - rabbitmq_management
      - rabbitmq_prometheus
      - rabbitmq_shovel
      - rabbitmq_shovel_management
  tls:
    secretName: rabbitmq-tls-secret
  override:
    statefulSet:
      spec:
        template:
          spec:
            topologySpreadConstraints:
              - maxSkew: 1
                topologyKey: topology.kubernetes.io/zone
                whenUnsatisfiable: DoNotSchedule
```

### Configurazione Completa rabbitmq.conf di Produzione

```ini
# rabbitmq.conf — configurazione di produzione completa

# Networking
listeners.tcp.default = 5672
listeners.ssl.default = 5671
num_acceptors.tcp = 10
num_acceptors.ssl = 10
handshake_timeout = 10000

# TLS
ssl_options.cacertfile = /etc/rabbitmq/ssl/ca.pem
ssl_options.certfile   = /etc/rabbitmq/ssl/cert.pem
ssl_options.keyfile    = /etc/rabbitmq/ssl/key.pem
ssl_options.verify     = verify_peer
ssl_options.fail_if_no_peer_cert = true
ssl_options.versions.1 = tlsv1.3

# Memory e Disk
vm_memory_high_watermark.relative = 0.4
vm_memory_high_watermark_paging_ratio = 0.5
disk_free_limit.relative = 1.5

# Clustering
cluster_partition_handling = pause_minority
cluster_formation.peer_discovery_backend = rabbit_peer_discovery_k8s
cluster_formation.k8s.host = kubernetes.default.svc.cluster.local
cluster_formation.k8s.address_type = hostname
cluster_formation.node_cleanup.only_log_warning = true

# Channel e Connection
channel_max = 2047
heartbeat = 60
consumer_timeout = 1800000

# Management
management.tcp.port = 15672
management.cors.allow_origins.1 = https://monitoring.example.com
management.sample_retention_policies.global.minute = 5
management.sample_retention_policies.global.hour = 60

# Logging
log.file.level = info
log.console = true
log.console.level = warning

# Default queue type
default_queue_type = quorum
```

---

## 4. Apache Kafka

### Architettura

Apache Kafka e una piattaforma di event streaming distribuita progettata per throughput elevato, durabilita e scalabilita orizzontale. A differenza di un message broker tradizionale, Kafka persiste i messaggi in un log immutabile e append-only.

**Broker:** un singolo server Kafka. Un cluster Kafka e composto da piu broker. Ogni broker gestisce un sottoinsieme di partizioni e serve le richieste dei client.

**Cluster:** l'insieme dei broker che cooperano. Il cluster elegge un controller che gestisce le operazioni amministrative (assegnazione delle partizioni, rilevamento dei guasti).

**Controller:** il broker eletto come coordinatore del cluster. In modalita KRaft (Kafka Raft), il controller e un nodo dedicato che gestisce i metadati senza dipendenza da ZooKeeper.

### Concetti Chiave

**Topic:** il canale logico a cui i producer pubblicano e da cui i consumer leggono. Un topic e identificato da un nome e configurato con un numero di partizioni e un replication factor.

**Partition:** l'unita di parallelismo di un topic. Ogni partizione e un log ordinato e immutabile. I messaggi all'interno di una partizione hanno un offset sequenziale unico.

**Offset:** l'identificatore numerico progressivo di ogni messaggio all'interno di una partizione. I consumer tracciano il proprio offset per sapere quali messaggi hanno gia processato.

**Segment:** la partizione e suddivisa in segmenti (file) sul filesystem. Ogni segmento ha un file `.log` (dati), un file `.index` (offset-to-position) e un file `.timeindex` (timestamp-to-offset).

**Log:** la struttura dati fondamentale di Kafka. E un append-only log dove ogni record e immutabile una volta scritto. La retention policy determina per quanto tempo i dati rimangono.

### Producer

Il producer pubblica messaggi su topic Kafka. Le configurazioni principali controllano durabilita, throughput e ordinamento.

**Partitioner:** determina a quale partizione inviare il messaggio. Se il messaggio ha una key, si usa il murmurhash della key modulo il numero di partizioni (sticky partitioner dal 2.4+). Senza key, si usa il round-robin o lo sticky batching.

**Batching:** il producer accumula messaggi in batch prima di inviarli, riducendo le chiamate di rete. `batch.size` (byte) e `linger.ms` (tempo massimo di attesa) controllano il batching.

**Compression:** i messaggi possono essere compressi a livello di batch. I codec supportati sono `gzip`, `snappy`, `lz4`, `zstd`. La compressione riduce il traffico di rete e l'uso di disco.

**acks:** controlla la durabilita.
- `acks=0`: il producer non attende conferma (massimo throughput, rischio perdita)
- `acks=1`: il producer attende la conferma dal leader della partizione
- `acks=all` (o `acks=-1`): il producer attende la conferma da tutti i replica in-sync

**Idempotent producer:** abilitando `enable.idempotence=true`, il producer assegna un sequence number a ogni messaggio per partizione. Il broker scarta i duplicati. Richiede `acks=all` e `max.in.flight.requests.per.connection <= 5`.

**Transactional producer:** consente di pubblicare messaggi su piu partizioni in modo atomico. Utile per pattern read-process-write con exactly-once semantics.

```java
// Producer Java con idempotenza e transazioni
Properties props = new Properties();
props.put("bootstrap.servers", "kafka1:9092,kafka2:9092,kafka3:9092");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("acks", "all");
props.put("enable.idempotence", "true");
props.put("transactional.id", "order-processor-1");
props.put("batch.size", "32768");          // 32 KB
props.put("linger.ms", "20");             // Attendi 20ms per accumulare batch
props.put("compression.type", "zstd");
props.put("max.in.flight.requests.per.connection", "5");

KafkaProducer<String, String> producer = new KafkaProducer<>(props);
producer.initTransactions();

try {
    producer.beginTransaction();
    producer.send(new ProducerRecord<>("orders", orderId, orderJson));
    producer.send(new ProducerRecord<>("audit-log", orderId, auditJson));
    producer.commitTransaction();
} catch (ProducerFencedException | OutOfOrderSequenceException e) {
    producer.close();
} catch (KafkaException e) {
    producer.abortTransaction();
}
```

### Consumer

**Consumer group:** un insieme di consumer che cooperano per consumare un topic. Ogni partizione e assegnata a esattamente un consumer del gruppo. Piu consumer che partizioni lasciano consumer inattivi.

**Partition assignment:** strategie di assegnazione: `RangeAssignor`, `RoundRobinAssignor`, `StickyAssignor`, `CooperativeStickyAssignor`. Il CooperativeStickyAssignor minimizza le ri-assegnazioni durante il rebalancing.

**Offset management:** i consumer committano periodicamente gli offset processati nel topic interno `__consumer_offsets`. Auto-commit (`enable.auto.commit=true`) committa periodicamente; il commit manuale offre controllo preciso.

**Rebalancing:** avviene quando un consumer si unisce o lascia il gruppo, o quando cambiano le partizioni. Il `group.coordinator` gestisce il protocollo di rebalancing. Il rebalancing causa un breve stop del consumo.

```python
# Consumer Python con confluent-kafka
from confluent_kafka import Consumer, KafkaError

conf = {
    'bootstrap.servers': 'kafka1:9092,kafka2:9092',
    'group.id': 'order-processor',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False,
    'max.poll.interval.ms': 300000,
    'session.timeout.ms': 45000,
    'partition.assignment.strategy': 'cooperative-sticky'
}

consumer = Consumer(conf)
consumer.subscribe(['orders'])

try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            raise KafkaException(msg.error())

        process_order(msg.value().decode('utf-8'))
        consumer.commit(message=msg)
finally:
    consumer.close()
```

### ZooKeeper vs KRaft

**ZooKeeper (legacy):** gestisce i metadati del cluster, l'elezione del controller, la configurazione dei topic. Richiede un ensemble separato di nodi ZooKeeper (tipicamente 3 o 5). Deprecato da Kafka 3.3, rimosso in Kafka 4.0.

**KRaft (Kafka Raft Metadata):** sostituisce ZooKeeper con un quorum interno di controller basato sul protocollo Raft. I metadati sono gestiti in un topic interno `@metadata`. Riduce la complessita operativa e migliora i tempi di failover.

```properties
# server.properties — configurazione KRaft
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@kafka1:9093,2@kafka2:9093,3@kafka3:9093
controller.listener.names=CONTROLLER
listeners=PLAINTEXT://:9092,CONTROLLER://:9093
log.dirs=/var/kafka-logs
cluster.id=MkU3OEVBNTcwNTJENDM2Qg
```

### Configurazione server.properties Essenziale

```properties
# server.properties — configurazione broker di produzione

# Identita del broker
broker.id=1
# Per KRaft: node.id=1 e process.roles=broker,controller

# Listener
listeners=PLAINTEXT://0.0.0.0:9092,SSL://0.0.0.0:9093
advertised.listeners=PLAINTEXT://kafka1.example.com:9092,SSL://kafka1.example.com:9093
listener.security.protocol.map=PLAINTEXT:PLAINTEXT,SSL:SSL

# Log e storage
log.dirs=/data/kafka-logs
num.partitions=6
default.replication.factor=3
min.insync.replicas=2
log.retention.hours=168          # 7 giorni
log.retention.bytes=-1           # Nessun limite per dimensione
log.segment.bytes=1073741824     # 1 GB per segmento
log.cleanup.policy=delete

# Replication
num.replica.fetchers=4
replica.lag.time.max.ms=30000
unclean.leader.election.enable=false

# Network e I/O
num.network.threads=8
num.io.threads=16
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600

# Compression
compression.type=producer        # Rispetta la compressione del producer

# Transaction
transaction.state.log.replication.factor=3
transaction.state.log.min.isr=2

# Group coordinator
group.initial.rebalance.delay.ms=3000
offsets.topic.replication.factor=3
```

### Comandi kafka-*

```bash
# Gestione dei topic
kafka-topics.sh --bootstrap-server kafka1:9092 --create \
  --topic orders --partitions 12 --replication-factor 3 \
  --config min.insync.replicas=2 \
  --config retention.ms=604800000

kafka-topics.sh --bootstrap-server kafka1:9092 --list
kafka-topics.sh --bootstrap-server kafka1:9092 --describe --topic orders

# Modificare la configurazione di un topic
kafka-configs.sh --bootstrap-server kafka1:9092 \
  --alter --entity-type topics --entity-name orders \
  --add-config retention.ms=259200000

# Aumentare le partizioni (non e possibile ridurle)
kafka-topics.sh --bootstrap-server kafka1:9092 \
  --alter --topic orders --partitions 24

# Console producer e consumer per debug
kafka-console-producer.sh --bootstrap-server kafka1:9092 \
  --topic orders --property key.separator=: --property parse.key=true

kafka-console-consumer.sh --bootstrap-server kafka1:9092 \
  --topic orders --group debug-consumer --from-beginning

# Gestione dei consumer group
kafka-consumer-groups.sh --bootstrap-server kafka1:9092 --list
kafka-consumer-groups.sh --bootstrap-server kafka1:9092 \
  --describe --group order-processor

# Reset degli offset
kafka-consumer-groups.sh --bootstrap-server kafka1:9092 \
  --group order-processor --topic orders \
  --reset-offsets --to-earliest --execute
```

---

## 5. Kafka — Operazioni e Ecosystem

### Topic Configurazione Avanzata

**Replication factor:** il numero di copie di ogni partizione distribuite tra i broker. Un replication factor di 3 tollera la perdita di 2 broker (con `min.insync.replicas=2`, tollera la perdita di 1 broker per le scritture).

**min.insync.replicas:** il numero minimo di replica che devono confermare la scrittura quando `acks=all`. Se il numero di ISR scende sotto questa soglia, il broker rifiuta le scritture con `NotEnoughReplicasException`.

**Cleanup policy:**
- `delete`: i segmenti piu vecchi della retention vengono eliminati
- `compact`: mantiene solo l'ultimo valore per ogni chiave (log compaction)
- `compact,delete`: combina entrambe le strategie

```bash
# Topic con log compaction per state store
kafka-topics.sh --bootstrap-server kafka1:9092 --create \
  --topic user-profiles --partitions 6 --replication-factor 3 \
  --config cleanup.policy=compact \
  --config min.cleanable.dirty.ratio=0.5 \
  --config delete.retention.ms=86400000 \
  --config segment.ms=604800000
```

### Kafka Connect

Kafka Connect e un framework per integrare Kafka con sistemi esterni tramite connettori riutilizzabili.

**Source connector:** importa dati da un sistema esterno (database, file, API) verso topic Kafka.

**Sink connector:** esporta dati da topic Kafka verso un sistema esterno (database, storage, search engine).

**Single Message Transforms (SMT):** trasformazioni leggere applicate a ogni messaggio nel pipeline Connect, senza richiedere codice custom.

```json
{
  "name": "postgres-source",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres.example.com",
    "database.port": "5432",
    "database.user": "debezium",
    "database.password": "${env:POSTGRES_PASSWORD}",
    "database.dbname": "orders_db",
    "database.server.name": "prod-postgres",
    "table.include.list": "public.orders,public.order_items",
    "plugin.name": "pgoutput",
    "slot.name": "debezium_orders",
    "publication.name": "dbz_orders_pub",
    "topic.prefix": "cdc",
    "key.converter": "io.confluent.connect.avro.AvroConverter",
    "key.converter.schema.registry.url": "http://schema-registry:8081",
    "value.converter": "io.confluent.connect.avro.AvroConverter",
    "value.converter.schema.registry.url": "http://schema-registry:8081",
    "transforms": "route,unwrap",
    "transforms.route.type": "org.apache.kafka.connect.transforms.RegexRouter",
    "transforms.route.regex": "cdc\\.public\\.(.*)",
    "transforms.route.replacement": "db.$1",
    "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
    "transforms.unwrap.add.fields": "op,ts_ms"
  }
}
```

```bash
# Gestione connettori via REST API
curl -X POST http://connect:8083/connectors \
  -H "Content-Type: application/json" \
  -d @postgres-source.json

curl http://connect:8083/connectors
curl http://connect:8083/connectors/postgres-source/status
curl -X PUT http://connect:8083/connectors/postgres-source/pause
curl -X PUT http://connect:8083/connectors/postgres-source/resume
curl -X DELETE http://connect:8083/connectors/postgres-source
```

### Kafka Streams

Kafka Streams e una libreria client per costruire applicazioni di stream processing. Non richiede un cluster separato; l'applicazione stessa e il processor.

**Topology:** il grafo di elaborazione composto da source, processor e sink nodes.

**State stores:** archivi locali (RocksDB o in-memory) per operazioni stateful (aggregazioni, join). Kafka Streams effettua backup automatico degli state stores su changelog topics.

```java
// Kafka Streams — esempio di word count con exactly-once
Properties props = new Properties();
props.put(StreamsConfig.APPLICATION_ID_CONFIG, "word-count-app");
props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka1:9092");
props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, "exactly_once_v2");
props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());

StreamsBuilder builder = new StreamsBuilder();
KStream<String, String> textLines = builder.stream("text-input");

KTable<String, Long> wordCounts = textLines
    .flatMapValues(value -> Arrays.asList(value.toLowerCase().split("\\W+")))
    .groupBy((key, word) -> word)
    .count(Materialized.as("word-counts-store"));

wordCounts.toStream().to("word-count-output",
    Produced.with(Serdes.String(), Serdes.Long()));

KafkaStreams streams = new KafkaStreams(builder.build(), props);
streams.start();
```

### Schema Registry

Lo Schema Registry gestisce la compatibilita degli schemi dei messaggi Kafka. Supporta Avro, Protobuf e JSON Schema.

**Compatibility modes:**
- `BACKWARD`: il nuovo schema puo leggere dati scritti con lo schema precedente
- `FORWARD`: lo schema precedente puo leggere dati scritti con il nuovo schema
- `FULL`: sia backward che forward compatibile
- `NONE`: nessun controllo di compatibilita
- Varianti `*_TRANSITIVE`: verificano la compatibilita con tutte le versioni, non solo l'ultima

```bash
# Registrare uno schema
curl -X POST http://schema-registry:8081/subjects/orders-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"schemaType": "AVRO", "schema": "{\"type\":\"record\",\"name\":\"Order\",\"fields\":[{\"name\":\"id\",\"type\":\"string\"},{\"name\":\"amount\",\"type\":\"double\"},{\"name\":\"status\",\"type\":{\"type\":\"enum\",\"name\":\"Status\",\"symbols\":[\"PENDING\",\"CONFIRMED\",\"SHIPPED\"]}}]}"}'

# Verificare la compatibilita prima di registrare
curl -X POST http://schema-registry:8081/compatibility/subjects/orders-value/versions/latest \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"schemaType": "AVRO", "schema": "..."}'

# Impostare la modalita di compatibilita
curl -X PUT http://schema-registry:8081/config/orders-value \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"compatibility": "FULL_TRANSITIVE"}'

# Elencare gli schemi
curl http://schema-registry:8081/subjects
curl http://schema-registry:8081/subjects/orders-value/versions
```

### MirrorMaker 2

MirrorMaker 2 (MM2) replica topic tra cluster Kafka per scenari multi-datacenter. Basato su Kafka Connect.

```properties
# mm2.properties — configurazione MirrorMaker 2
clusters = dc1, dc2
dc1.bootstrap.servers = kafka-dc1-1:9092,kafka-dc1-2:9092
dc2.bootstrap.servers = kafka-dc2-1:9092,kafka-dc2-2:9092

dc1->dc2.enabled = true
dc1->dc2.topics = orders.*, payments.*

# Replication policy
replication.policy.class = org.apache.kafka.connect.mirror.DefaultReplicationPolicy
replication.policy.separator = .

# Sync consumer group offsets
sync.group.offsets.enabled = true
sync.group.offsets.interval.seconds = 10
emit.heartbeats.interval.seconds = 5
emit.checkpoints.interval.seconds = 10

# Replication factor nel cluster di destinazione
replication.factor = 3
```

### Kafka su Kubernetes (Strimzi)

```yaml
# kafka-cluster.yaml — Strimzi Kafka CRD
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: production-kafka
  namespace: messaging
spec:
  kafka:
    version: 3.7.0
    replicas: 3
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
      - name: external
        port: 9094
        type: loadbalancer
        tls: true
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2
      num.partitions: 6
      log.retention.hours: 168
      auto.create.topics.enable: false
    storage:
      type: jbod
      volumes:
        - id: 0
          type: persistent-claim
          size: 100Gi
          class: fast-ssd
          deleteClaim: false
    resources:
      requests:
        memory: 4Gi
        cpu: "2"
      limits:
        memory: 8Gi
        cpu: "4"
  zookeeper:
    replicas: 3
    storage:
      type: persistent-claim
      size: 20Gi
      class: fast-ssd
    resources:
      requests:
        memory: 1Gi
        cpu: "0.5"
  entityOperator:
    topicOperator: {}
    userOperator: {}
```

### Tiered Storage (KIP-405)

Il Tiered Storage (KIP-405) e una funzionalita introdotta in Kafka 3.6 (early access) e portata a GA nelle versioni successive, che consente di separare lo storage locale del broker dallo storage remoto a lungo termine. I segmenti di log piu vecchi vengono automaticamente spostati su object store (S3, GCS, Azure Blob Storage, HDFS), riducendo drasticamente i costi di storage e consentendo retention praticamente illimitata senza aumentare la capacita disco dei broker.

**Architettura a due livelli:**
- **Local tier:** i dischi locali dei broker conservano i segmenti attivi e quelli recenti. Le operazioni di lettura e scrittura ad alta frequenza avvengono su questo livello.
- **Remote tier:** lo storage remoto conserva i segmenti completati. Le letture da segmenti remoti avvengono on-demand quando un consumer richiede dati piu vecchi del retention locale.

```
Flusso dei dati con Tiered Storage:

Producer --> Broker (segmento attivo su disco locale)
                |
                v  (segmento completato)
            Upload al Remote Storage (S3/GCS/Azure Blob)
                |
                v
Consumer <-- Broker (legge dal locale se recente, dal remoto se vecchio)
```

**Configurazione broker:**

```properties
# server.properties — abilitare tiered storage
remote.log.storage.system.enable=true

# Plugin per il remote storage (esempio: S3)
remote.log.storage.manager.class.name=org.apache.kafka.server.log.remote.storage.s3.S3RemoteLogStorageManager
remote.log.storage.manager.class.path=/opt/kafka/libs/kafka-remote-storage-s3-*.jar

# Configurazione S3
s3.bucket.name=kafka-tiered-storage-prod
s3.region=eu-west-1

# Plugin per i metadati del remote log
remote.log.metadata.manager.class.name=org.apache.kafka.server.log.remote.metadata.storage.TopicBasedRemoteLogMetadataManager
remote.log.metadata.common.client.prefix=rlm_
rlmm.config.remote.log.metadata.topic.replication.factor=3
```

**Configurazione a livello di topic:**

```bash
# Abilitare tiered storage su un topic specifico
kafka-configs.sh --bootstrap-server kafka1:9092 \
  --alter --entity-type topics --entity-name orders \
  --add-config remote.storage.enable=true

# Impostare la retention locale a 24 ore e la retention remota a 90 giorni
kafka-configs.sh --bootstrap-server kafka1:9092 \
  --alter --entity-type topics --entity-name orders \
  --add-config local.retention.ms=86400000,retention.ms=7776000000
```

Con il tiered storage, `retention.ms` e `retention.bytes` si riferiscono alla durata totale dei dati (locale + remoto), mentre `local.retention.ms` e `local.retention.bytes` controllano quanto a lungo i dati rimangono sui dischi locali del broker. Il consumer non richiede alcuna modifica: la lettura dal remote tier e trasparente.

**Vantaggi operativi:**
- Riduzione dei costi di storage del 60-80% spostando dati storici su object store economico
- Retention praticamente illimitata senza provisioning di dischi aggiuntivi
- Rebalancing piu veloce: solo i dati locali vengono spostati tra broker
- Separazione tra hot data (locale, bassa latenza) e cold data (remoto, alto volume)

### Kafka 4.0 e la Rimozione di ZooKeeper

Kafka 4.0 segna l'eliminazione definitiva di Apache ZooKeeper come dipendenza esterna. La modalita KRaft (Kafka Raft), introdotta come preview in Kafka 2.8 e dichiarata production-ready in Kafka 3.3, diventa l'unico meccanismo di gestione dei metadati.

**Impatto operativo della rimozione di ZooKeeper:**
- Eliminazione di un componente infrastrutturale separato (tipicamente 3-5 nodi ZooKeeper)
- Riduzione della complessita di deployment e monitoring (un solo sistema da gestire)
- Failover del controller piu rapido (secondi vs minuti con ZooKeeper)
- Gestione dei metadati 30-40% piu veloce grazie al protocollo Raft interno
- Scalabilita migliorata del numero di partizioni per cluster (oltre 1 milione di partizioni)

**Migrazione da ZooKeeper a KRaft:**

```bash
# Passo 1: Generare un nuovo cluster ID (se non esistente)
kafka-storage.sh random-uuid

# Passo 2: Formattare i log directory per KRaft
kafka-storage.sh format -t <cluster-id> -c server.properties

# Passo 3: Avviare il broker in modalita KRaft
# Il server.properties deve contenere:
# process.roles=broker,controller (nodo combinato)
# oppure process.roles=controller (nodo controller dedicato)
# controller.quorum.voters=1@host1:9093,2@host2:9093,3@host3:9093
```

Per cluster di grandi dimensioni (oltre 20 broker), si raccomanda l'uso di controller dedicati (nodi con `process.roles=controller`) separati dai broker, per isolare il carico del quorum Raft dal traffico dati dei client.

**Novita aggiuntive di Kafka 4.0:**
- **Share Groups (KIP-932):** un nuovo tipo di consumer group che consente a piu consumer di condividere il consumo di una partizione, simile al competing consumers pattern di RabbitMQ. I messaggi sono distribuiti individualmente ai consumer del gruppo, senza il vincolo di assegnazione partizione-consumer. Questo rende Kafka competitivo negli scenari di work distribution tradizionalmente dominati dai message queue classici.
- **Compressed record headers:** gli header dei record possono essere compressi insieme al payload, riducendo l'overhead per messaggi con molti header.
- **Improved consumer rebalancing:** il protocollo di rebalancing e stato ottimizzato per ridurre i tempi di stop-the-world durante l'ingresso e l'uscita dei consumer dal gruppo.

---

## 6. NATS

### Architettura

NATS e un sistema di messaging ad alte prestazioni progettato per semplicita, performance e resilienza. L'architettura comprende tre componenti principali:

**Core NATS:** il layer di messaging base. Fornisce pub/sub, request/reply e queue groups con semantica at-most-once. I messaggi non vengono persistiti; se nessun subscriber e connesso, il messaggio e perso.

**JetStream:** il layer di persistenza costruito sopra Core NATS. Fornisce at-least-once e exactly-once delivery, replay, key-value store e object store.

**NATS Clustering:** i server NATS formano un mesh full-mesh. Ogni server mantiene una connessione con tutti gli altri. Il routing dei messaggi e automatico e trasparente ai client.

### Pattern di Messaging

**Pub/Sub:** il producer pubblica su un subject e tutti i subscriber connessi ricevono il messaggio. I subject supportano wildcards: `*` per un singolo token, `>` per uno o piu token.

```bash
# Pubblicare un messaggio
nats pub orders.created '{"id": "ord-123", "total": 99.90}'

# Sottoscrivere a un subject
nats sub "orders.*"
nats sub "orders.>"
```

**Request/Reply:** il client invia una richiesta e attende una risposta su un subject temporaneo (inbox).

```bash
# Servizio che risponde alle richieste
nats reply "service.lookup" "result: found"

# Client che invia una richiesta
nats request "service.lookup" "query: user-123" --timeout 5s
```

**Queue Groups:** i subscriber con lo stesso queue group name competono per i messaggi. Ogni messaggio e consegnato a un solo membro del gruppo. Equivalente al competing consumers pattern.

```bash
# Due consumer nello stesso queue group
nats sub "orders.process" --queue workers
nats sub "orders.process" --queue workers
# Ogni messaggio va a uno solo dei due
```

### JetStream

JetStream aggiunge persistenza, replay e garanzie di consegna a NATS.

**Stream:** una collezione persistente di messaggi. Uno stream cattura messaggi da uno o piu subject e li memorizza.

**Consumer:** un client che legge messaggi da uno stream. I consumer possono essere durable (persistono l'avanzamento) o ephemeral.

```bash
# Creare uno stream
nats stream add ORDERS \
  --subjects "orders.*" \
  --storage file \
  --replicas 3 \
  --retention limits \
  --max-msgs 1000000 \
  --max-bytes 10GB \
  --max-age 7d \
  --discard old \
  --dupe-window 2m

# Elencare gli stream
nats stream ls
nats stream info ORDERS

# Creare un consumer durable
nats consumer add ORDERS order-processor \
  --filter "orders.created" \
  --ack explicit \
  --deliver all \
  --max-deliver 5 \
  --max-pending 1000 \
  --wait 30s

# Consumare messaggi
nats consumer next ORDERS order-processor --count 10
```

**Key-Value Store:** un key-value store distribuito costruito sopra JetStream.

```bash
# Creare un bucket KV
nats kv add USER_SESSIONS --replicas 3 --ttl 24h --max-value-size 1MB

# Operazioni CRUD
nats kv put USER_SESSIONS user-123 '{"token": "abc", "role": "admin"}'
nats kv get USER_SESSIONS user-123
nats kv del USER_SESSIONS user-123

# Watch per cambiamenti
nats kv watch USER_SESSIONS
```

**Object Store:** per memorizzare oggetti di grandi dimensioni (file, blob) in modo distribuito.

```bash
# Creare un object store
nats object add ARTIFACTS --replicas 3 --max-bucket-size 50GB

# Upload e download
nats object put ARTIFACTS ./build-artifact.tar.gz
nats object get ARTIFACTS build-artifact.tar.gz -o ./downloaded.tar.gz
```

### Accounts e Multi-tenancy

NATS supporta multi-tenancy nativo tramite il sistema di accounts. Ogni account ha il proprio spazio di subject isolato.

```bash
# Generare una chiave operator
nsc add operator MyOrg

# Creare account isolati
nsc add account TeamA
nsc add account TeamB

# Creare utenti per account
nsc add user --account TeamA --name service-a
nsc add user --account TeamB --name service-b

# Configurare import/export tra account per la comunicazione cross-tenant
nsc add export --account TeamA --name "orders" --subject "orders.>"
nsc add import --account TeamB --name "orders" --src-account TeamA --remote-subject "orders.>"
```

### Security

```bash
# Generare NKey per autenticazione
nsc generate nkey --user
# Output: seed (SUAM...) e public key (UA...)

# Configurazione TLS del server
# nats-server.conf
tls {
  cert_file: "/etc/nats/certs/server.crt"
  key_file:  "/etc/nats/certs/server.key"
  ca_file:   "/etc/nats/certs/ca.crt"
  verify:    true
  timeout:   5
}

authorization {
  users = [
    { user: "admin", password: "$2a$11$...", permissions: { publish: ">", subscribe: ">" } }
    { user: "reader", password: "$2a$11$...", permissions: { publish: { deny: ">" }, subscribe: ">" } }
  ]
}
```

### Confronto NATS vs RabbitMQ vs Kafka

| Caratteristica | NATS | RabbitMQ | Kafka |
|---|---|---|---|
| Protocollo | NATS Protocol (testo) | AMQP 0-9-1 | Kafka Protocol (binario) |
| Latenza | Ultra-bassa (<1ms) | Bassa (1-5ms) | Media (5-20ms) |
| Throughput | Alto | Medio | Molto alto |
| Persistenza | JetStream (opzionale) | Sempre (durable queues) | Sempre (log) |
| Ordering | Per subject | Per queue | Per partizione |
| Consumer model | Push/Pull | Push | Pull |
| Replay | Si (JetStream) | No | Si (offset reset) |
| Complessita operativa | Molto bassa | Media | Alta |
| Ecosystem | Minimo | Medio | Molto ricco |

### NATS — Deployment di Produzione

Un deployment NATS di produzione richiede almeno 3 server (o 5 per requisiti di affidabilita elevata) a causa dell'uso di Raft come algoritmo di consenso per JetStream. L'uso di un numero dispari e essenziale affinche l'algoritmo possa raggiungere la maggioranza.

**Configurazione cluster di produzione:**

```hcl
# nats-server.conf — configurazione di produzione
server_name: nats-1
listen: 0.0.0.0:4222

jetstream {
  store_dir: /data/nats/jetstream
  max_mem: 2G
  max_file: 50G
  unique_tag: az:eu-west-1a  # Previene la collocazione nella stessa AZ
}

cluster {
  name: production
  listen: 0.0.0.0:6222
  routes: [
    nats-route://nats-1:6222
    nats-route://nats-2:6222
    nats-route://nats-3:6222
  ]
}

# Leafnode per connessione da edge/IoT
leafnodes {
  listen: 0.0.0.0:7422
}

# Logging
log_file: /var/log/nats/nats.log
log_size_limit: 100MB
max_traced_msg_len: 256

# Limiti connessione
max_connections: 65536
max_payload: 1MB
write_deadline: 10s
```

**Leafnodes per architetture edge:** i leafnode sono nodi NATS che si connettono a un cluster centrale tramite una singola connessione. I messaggi sono instradati automaticamente tra il leafnode e il cluster. Questo pattern e ideale per architetture edge/IoT dove nodi periferici devono comunicare con un cluster centrale senza formare un full-mesh.

```
                    ┌─────────────────────┐
                    │   NATS Cluster       │
                    │   (3-5 nodi core)    │
                    └──┬──────┬──────┬─────┘
                       │      │      │
                ┌──────┘      │      └──────┐
                │             │             │
           ┌────┴────┐  ┌────┴────┐  ┌─────┴───┐
           │Leafnode  │  │Leafnode  │  │Leafnode │
           │Edge EU   │  │Edge US   │  │Edge APAC│
           └─────────┘  └─────────┘  └─────────┘
```

**NATS su Kubernetes con Helm:**

```bash
# Installare il NATS Helm chart
helm repo add nats https://nats-io.github.io/k8s/helm/charts/
helm repo update

helm install nats nats/nats --namespace messaging --create-namespace \
  --set config.jetstream.enabled=true \
  --set config.jetstream.fileStore.pvc.size=50Gi \
  --set config.jetstream.fileStore.pvc.storageClassName=fast-ssd \
  --set config.cluster.enabled=true \
  --set config.cluster.replicas=3 \
  --set podTemplate.topologySpreadConstraints[0].maxSkew=1 \
  --set podTemplate.topologySpreadConstraints[0].topologyKey=topology.kubernetes.io/zone \
  --set podTemplate.topologySpreadConstraints[0].whenUnsatisfiable=DoNotSchedule

# Verificare lo stato del cluster
kubectl exec -n messaging nats-0 -- nats server report jetstream
kubectl exec -n messaging nats-0 -- nats server report connections
```

L'immagine NATS e estremamente leggera (sotto i 20 MB) con startup quasi istantaneo, zero dipendenze esterne e clustering nativo che funziona immediatamente con il networking dei container. Questo la rende particolarmente adatta per ambienti edge e IoT dove le risorse sono limitate.

---

## 7. Cloud Messaging Services

### AWS SQS (Simple Queue Service)

**Standard Queue:** throughput illimitato, consegna at-least-once, ordinamento best-effort (non garantito). Adatto alla maggior parte dei casi d'uso.

**FIFO Queue:** throughput limitato a 3000 messaggi/secondo con batching (300 senza), consegna exactly-once, ordinamento garantito per message group. Il nome della coda deve terminare con `.fifo`.

```bash
# Creare una coda Standard
aws sqs create-queue --queue-name orders-queue \
  --attributes '{
    "VisibilityTimeout": "60",
    "MessageRetentionPeriod": "1209600",
    "ReceiveMessageWaitTimeSeconds": "20"
  }'

# Creare una coda FIFO con DLQ
aws sqs create-queue --queue-name orders-queue.fifo \
  --attributes '{
    "FifoQueue": "true",
    "ContentBasedDeduplication": "true",
    "DeduplicationScope": "messageGroup",
    "FifoThroughputLimit": "perMessageGroupId",
    "VisibilityTimeout": "60",
    "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:eu-west-1:123456:orders-dlq.fifo\",\"maxReceiveCount\":\"3\"}"
  }'

# Inviare messaggi
aws sqs send-message --queue-url https://sqs.eu-west-1.amazonaws.com/123456/orders-queue \
  --message-body '{"orderId": "123"}' \
  --message-attributes '{"EventType": {"DataType": "String", "StringValue": "OrderCreated"}}'

# Ricevere messaggi con long polling
aws sqs receive-message --queue-url https://sqs.eu-west-1.amazonaws.com/123456/orders-queue \
  --max-number-of-messages 10 --wait-time-seconds 20

# Eliminare un messaggio dopo l'elaborazione
aws sqs delete-message --queue-url ... --receipt-handle <handle>
```

**Visibility Timeout:** il periodo durante il quale un messaggio ricevuto e invisibile ad altri consumer. Se il consumer non elimina il messaggio entro il timeout, il messaggio diventa nuovamente visibile e viene riconsegnato.

**Long Polling:** il consumer attende fino a `WaitTimeSeconds` (max 20s) per un messaggio, riducendo le chiamate vuote e i costi.

### AWS SNS (Simple Notification Service)

SNS e un servizio pub/sub gestito. I topic distribuiscono messaggi a piu subscriber.

```bash
# Creare un topic
aws sns create-topic --name order-events

# Sottoscrivere una coda SQS
aws sns subscribe --topic-arn arn:aws:sns:eu-west-1:123456:order-events \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:eu-west-1:123456:orders-queue

# Sottoscrivere con filtro
aws sns subscribe --topic-arn arn:aws:sns:eu-west-1:123456:order-events \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:eu-west-1:123456:priority-queue \
  --attributes '{"FilterPolicy": "{\"eventType\": [\"OrderCreated\"], \"priority\": [{\"numeric\": [\">\", 5]}]}"}'

# Pubblicare un messaggio
aws sns publish --topic-arn arn:aws:sns:eu-west-1:123456:order-events \
  --message '{"orderId": "123"}' \
  --message-attributes '{"eventType": {"DataType": "String", "StringValue": "OrderCreated"}}'
```

### AWS EventBridge

EventBridge e un bus eventi serverless per event-driven architecture. Supporta routing basato su regole, schema registry e integrazioni native con servizi AWS.

```bash
# Creare un event bus custom
aws events create-event-bus --name ecommerce-events

# Creare una regola di routing
aws events put-rule --name order-created-rule \
  --event-bus-name ecommerce-events \
  --event-pattern '{
    "source": ["com.ecommerce.orders"],
    "detail-type": ["OrderCreated"],
    "detail": {
      "amount": [{"numeric": [">", 100]}]
    }
  }'

# Aggiungere un target (Lambda, SQS, Step Functions, etc.)
aws events put-targets --rule order-created-rule \
  --event-bus-name ecommerce-events \
  --targets '[{"Id": "sqs-target", "Arn": "arn:aws:sqs:eu-west-1:123456:high-value-orders"}]'
```

### AWS Kinesis

**Data Streams:** streaming in tempo reale con shard come unita di parallelismo. Ogni shard gestisce 1MB/s in ingresso e 2MB/s in uscita.

```bash
# Creare uno stream
aws kinesis create-stream --stream-name click-events --shard-count 4

# Scrivere un record
aws kinesis put-record --stream-name click-events \
  --partition-key user-123 \
  --data $(echo '{"event": "click"}' | base64)
```

**Firehose:** servizio di delivery che carica stream su S3, Redshift, OpenSearch o HTTP endpoint senza codice consumer.

### Azure Service Bus

Azure Service Bus offre code e topic con supporto per sessioni, transazioni e consegna schedulata.

```bash
# Creare un namespace
az servicebus namespace create --name ecommerce-sb \
  --resource-group messaging --sku Premium --capacity 1

# Creare una coda con sessioni
az servicebus queue create --name orders \
  --namespace-name ecommerce-sb --resource-group messaging \
  --enable-session true --max-delivery-count 10 \
  --default-message-time-to-live P7D --lock-duration PT1M \
  --dead-lettering-on-message-expiration true

# Creare un topic con subscription
az servicebus topic create --name order-events \
  --namespace-name ecommerce-sb --resource-group messaging

az servicebus topic subscription create --name analytics-sub \
  --namespace-name ecommerce-sb --resource-group messaging \
  --topic-name order-events --max-delivery-count 5

# Aggiungere un filtro SQL alla subscription
az servicebus topic subscription rule create --name high-value-filter \
  --namespace-name ecommerce-sb --resource-group messaging \
  --topic-name order-events --subscription-name analytics-sub \
  --filter-sql-expression "amount > 100 AND region = 'EU'"
```

### Novita AWS 2025-2026

Le piattaforme di messaging serverless AWS hanno ricevuto aggiornamenti significativi:

**Payload size aumentato a 1 MB:** a partire dal 2025, SQS, SNS, EventBridge e Lambda supportano payload fino a 1 MB (precedentemente 256 KB). L'aumento e applicato automaticamente a tutte le code e bus eventi esistenti e nuovi, eliminando la necessita del pattern di claim check per messaggi di dimensioni medie.

**SQS Provisioned Mode:** il provisioned mode per le Event Source Mapping di Lambda sostituisce il polling incrementale con una flotta di poller dedicati always-warm, che scalano al numero massimo di poller in secondi anziche minuti durante i burst di carico. Questo riduce drasticamente la latenza di elaborazione per workload con pattern di traffico spiky.

**EventBridge Fair Queue Targets:** EventBridge supporta ora SQS fair queues come target diretto, consentendo l'elaborazione equa dei messaggi tra tenant diversi in architetture multi-tenant.

**EventBridge Schema Discovery e Replay:** le capacita native di schema discovery e replay eventi semplificano il debugging e l'archiviazione degli eventi. Lo schema registry integrato cattura automaticamente la struttura degli eventi che transitano sul bus.

### Azure Event Hubs

Event Hubs e il servizio di streaming di Azure, compatibile con il protocollo Kafka. Supporta milioni di eventi al secondo con throughput unita (TU) come modello di scaling per il tier Standard, e processing unita (PU) per il tier Premium.

**Compatibilita Kafka:** Event Hubs espone un endpoint compatibile con il protocollo Kafka, consentendo l'uso di producer e consumer Kafka standard senza modifiche al codice. I topic Kafka corrispondono agli Event Hub, e i consumer group funzionano come in Kafka nativo.

```bash
# Creare un Event Hub con 32 partizioni
az eventhubs eventhub create --name orders-stream \
  --namespace-name ecommerce-eh --resource-group messaging \
  --partition-count 32 --message-retention 7

# Creare un consumer group
az eventhubs eventhub consumer-group create --name analytics-cg \
  --namespace-name ecommerce-eh --resource-group messaging \
  --eventhub-name orders-stream

# Capture — archiviazione automatica su Blob Storage
az eventhubs eventhub update --name orders-stream \
  --namespace-name ecommerce-eh --resource-group messaging \
  --enable-capture true --capture-interval 300 \
  --capture-size-limit 314572800 \
  --destination-name EventHubArchive.AzureBlockBlob \
  --storage-account orderstorage \
  --blob-container eventhub-archive
```

```properties
# Configurazione client Kafka per connessione a Event Hubs
bootstrap.servers=ecommerce-eh.servicebus.windows.net:9093
security.protocol=SASL_SSL
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required \
  username="$ConnectionString" \
  password="Endpoint=sb://ecommerce-eh.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=<key>";
```

### Azure Event Grid

Event Grid e un servizio di routing eventi serverless, ottimizzato per eventi a basso volume e alta fanout. Supporta nativamente lo standard CloudEvents 1.0 e si integra con oltre 20 servizi Azure come sorgenti di eventi.

```bash
# Creare un topic Event Grid
az eventgrid topic create --name order-events \
  --resource-group messaging --location westeurope \
  --input-schema cloudeventschemav1_0

# Creare una subscription con filtro
az eventgrid event-subscription create --name high-value-orders \
  --source-resource-id /subscriptions/<sub>/resourceGroups/messaging/providers/Microsoft.EventGrid/topics/order-events \
  --endpoint https://api.example.com/webhooks/orders \
  --event-delivery-schema cloudeventschemav1_0 \
  --advanced-filter data.amount NumberGreaterThan 500
```

**Event Grid Namespaces (2025+):** la nuova modalita namespace introduce il supporto per MQTT v5 e v3.1.1, abilitando scenari IoT con milioni di dispositivi connessi. I namespace supportano anche il pull delivery model, in cui il consumer estrae gli eventi dal broker anziche riceverli tramite webhook push.

### GCP Pub/Sub

Google Cloud Pub/Sub e un servizio di messaging globale con consegna at-least-once e ordinamento per ordering key.

```bash
# Creare un topic
gcloud pubsub topics create order-events

# Creare un subscription pull
gcloud pubsub subscriptions create order-processor \
  --topic=order-events \
  --ack-deadline=60 \
  --message-retention-duration=7d \
  --enable-exactly-once-delivery \
  --dead-letter-topic=projects/myproject/topics/order-events-dlq \
  --max-delivery-attempts=5

# Creare un subscription con ordering
gcloud pubsub subscriptions create ordered-processor \
  --topic=order-events \
  --enable-message-ordering

# Pubblicare un messaggio
gcloud pubsub topics publish order-events \
  --message='{"orderId": "123"}' \
  --attribute=eventType=OrderCreated \
  --ordering-key=customer-456

# Ricevere messaggi
gcloud pubsub subscriptions pull order-processor --limit=10 --auto-ack
```

### Confronto Cross-Cloud

| Caratteristica | AWS SQS/SNS | Azure Service Bus | GCP Pub/Sub |
|---|---|---|---|
| Coda | SQS | Queue | Subscription (pull) |
| Pub/Sub | SNS + SQS | Topic + Subscription | Topic + Subscription |
| Ordering | FIFO queue | Sessions | Ordering key |
| Exactly-once | FIFO dedup | Duplicate detection | Subscription flag |
| DLQ | Si | Si | Si |
| Max message size | 256 KB (SQS) | 256 KB (Standard), 100 MB (Premium) | 10 MB |
| Retention | 14 giorni max | Illimitata | 31 giorni max |
| Event routing | EventBridge | Event Grid | Eventarc |
| Streaming | Kinesis | Event Hubs | Pub/Sub + Dataflow |
| Kafka compatibile | MSK | Event Hubs (protocol) | No |

---

## 8. Event-Driven Architecture

### Pattern Fondamentali

**Event Notification:** un servizio pubblica un evento quando qualcosa di significativo accade. Gli altri servizi reagiscono all'evento. L'evento contiene solo le informazioni minime (tipo e ID). I servizi interessati interrogano il servizio sorgente per i dettagli.

Vantaggio: disaccoppiamento massimo. Svantaggio: richiede chiamate aggiuntive per ottenere i dettagli.

**Event-Carried State Transfer:** l'evento trasporta tutti i dati necessari affinche i consumer possano reagire senza interrogare il servizio sorgente. Ogni consumer mantiene una copia locale dei dati di cui ha bisogno.

Vantaggio: elimina le dipendenze runtime. Svantaggio: duplicazione dei dati, eventuale inconsistenza.

**Event Sourcing:** lo stato di un'entita e derivato dalla sequenza completa di eventi che lo hanno modificato. Non si memorizza lo stato corrente ma la storia completa degli eventi. Lo stato attuale viene ricostruito tramite replay della sequenza.

```python
# Esempio concettuale di event sourcing per un conto bancario
class BankAccount:
    def __init__(self, account_id):
        self.account_id = account_id
        self.balance = 0
        self.events = []

    def apply_event(self, event):
        if event['type'] == 'AccountOpened':
            self.balance = event['initial_balance']
        elif event['type'] == 'MoneyDeposited':
            self.balance += event['amount']
        elif event['type'] == 'MoneyWithdrawn':
            self.balance -= event['amount']
        self.events.append(event)

    def rebuild_from_events(self, events):
        self.balance = 0
        self.events = []
        for event in events:
            self.apply_event(event)
```

**CQRS (Command Query Responsibility Segregation):** separa il modello di scrittura (command) dal modello di lettura (query). Le scritture generano eventi, i modelli di lettura sono proiezioni ottimizzate per query specifiche.

CQRS e spesso combinato con event sourcing: i comandi producono eventi, gli eventi aggiornano le proiezioni di lettura.

### Domain Events

Un domain event rappresenta qualcosa di significativo che e accaduto nel dominio di business. Caratteristiche:

- **Immutabile:** una volta creato non puo essere modificato
- **Passato:** descrive qualcosa che e gia accaduto (`OrderCreated`, non `CreateOrder`)
- **Significativo:** ha valore di business, non e un dettaglio tecnico
- **Auto-descrittivo:** contiene tutte le informazioni necessarie per la comprensione

### Event Schema Design e Versioning

```json
{
  "eventId": "evt-550e8400-e29b-41d4-a716-446655440000",
  "eventType": "com.ecommerce.orders.v2.OrderCreated",
  "source": "order-service",
  "specversion": "1.0",
  "time": "2026-04-11T10:30:00Z",
  "datacontenttype": "application/json",
  "subject": "orders/ord-123",
  "data": {
    "orderId": "ord-123",
    "customerId": "cust-456",
    "items": [
      {"productId": "prod-789", "quantity": 2, "unitPrice": 29.99}
    ],
    "totalAmount": 59.98,
    "currency": "EUR",
    "shippingAddress": {
      "country": "IT",
      "city": "Roma",
      "postalCode": "00100"
    }
  },
  "metadata": {
    "correlationId": "corr-abc-123",
    "causationId": "cmd-create-order-456",
    "userId": "user-789",
    "schemaVersion": 2
  }
}
```

Strategie di versioning degli schema:

- **Additive changes:** aggiungere campi opzionali e backward-compatible
- **Schema version in event type:** `OrderCreated.v2` coesiste con `OrderCreated.v1`
- **Upcasting:** trasformazione automatica degli eventi vecchi nel formato nuovo al momento del replay
- **Lazy migration:** i consumer gestiscono piu versioni dello schema

### Event Store

Un event store e un database ottimizzato per l'append di eventi e il replay per entita.

Requisiti chiave:
- Append-only con ordinamento garantito per stream
- Concurrency control (optimistic locking tramite expected version)
- Proiezioni e sottoscrizioni a stream di eventi
- Snapshot per ottimizzare il replay di stream lunghi

Implementazioni: EventStoreDB, Marten (PostgreSQL), Axon Server, implementazione custom su PostgreSQL/Kafka.

### Saga Pattern Dettagliato

**Orchestration-based saga:** un servizio orchestratore mantiene lo stato della saga e coordina i passi. L'orchestratore sa quale servizio chiamare dopo e gestisce le compensazioni.

Vantaggio: logica centralizzata, piu facile da comprendere e debuggare.
Svantaggio: l'orchestratore diventa un single point of failure logico e un possibile collo di bottiglia.

**Choreography-based saga:** ogni servizio reagisce agli eventi pubblicati dagli altri. Non c'e un coordinatore centrale.

Vantaggio: nessun coordinatore centrale, massimo disaccoppiamento.
Svantaggio: flusso distribuito, piu difficile da tracciare e debuggare. Rischio di dipendenze cicliche.

### Compensating Transactions

Ogni passo della saga deve avere una compensating transaction che annulla l'effetto in caso di fallimento successivo. Le compensazioni devono essere idempotenti.

```
Passo 1: ReserveInventory -> CompensateInventory (rilascia)
Passo 2: ChargePayment    -> RefundPayment (rimborsa)
Passo 3: CreateShipment   -> CancelShipment (annulla)

Se il Passo 3 fallisce:
  -> CompensateInventory (Passo 1)
  -> RefundPayment (Passo 2)
```

### Eventual Consistency

Nei sistemi event-driven, la consistenza tra servizi e eventuale, non immediata. I dati tra servizi diversi convergono verso la consistenza nel tempo. Le letture possono restituire dati obsoleti temporaneamente.

Strategie di mitigazione:
- **Causal consistency:** propagare token di causalita per garantire che le letture successive vedano almeno gli effetti delle proprie scritture
- **Read-your-writes:** dopo una scrittura, leggere dalla stessa replica
- **UI optimistic update:** aggiornare l'interfaccia prima della conferma dal backend, con rollback in caso di errore

### Transactional Outbox Pattern

Il Transactional Outbox Pattern risolve il problema del dual write: quando un servizio deve aggiornare il proprio database e pubblicare un evento sul message broker in modo atomico. Eseguire le due operazioni separatamente introduce un rischio di inconsistenza — il database potrebbe essere aggiornato ma l'evento non pubblicato (o viceversa).

**Meccanismo:** invece di pubblicare direttamente sul broker, il servizio inserisce l'evento in una tabella `outbox` all'interno della stessa transazione database che modifica i dati di business. Un componente separato (outbox relay o CDC connector) legge la tabella outbox e pubblica gli eventi sul broker.

```sql
-- Schema della tabella outbox
CREATE TABLE outbox (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type  VARCHAR(255) NOT NULL,    -- es. 'Order'
    aggregate_id    VARCHAR(255) NOT NULL,    -- es. 'ord-123'
    event_type      VARCHAR(255) NOT NULL,    -- es. 'OrderCreated'
    payload         JSONB NOT NULL,           -- corpo dell'evento
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at    TIMESTAMPTZ,              -- NULL finche non pubblicato
    INDEX idx_outbox_unpublished (published_at) WHERE published_at IS NULL
);
```

```python
# Transazione atomica: salva dati + scrive nell'outbox
def create_order(db, order_data):
    with db.begin():
        # Operazione di business
        order = db.execute(
            "INSERT INTO orders (id, customer_id, total) VALUES (%s, %s, %s) RETURNING id",
            (order_data['id'], order_data['customer_id'], order_data['total'])
        ).fetchone()

        # Scrittura nell'outbox nella stessa transazione
        db.execute(
            """INSERT INTO outbox (aggregate_type, aggregate_id, event_type, payload)
               VALUES ('Order', %s, 'OrderCreated', %s)""",
            (order.id, json.dumps({
                'orderId': order.id,
                'customerId': order_data['customer_id'],
                'total': order_data['total'],
                'timestamp': datetime.utcnow().isoformat()
            }))
        )
    # Il commit e atomico: o entrambe le operazioni vanno a buon fine, o nessuna
```

**Outbox Relay (polling):** un processo separato interroga periodicamente la tabella outbox per gli eventi non pubblicati, li invia al broker e aggiorna il campo `published_at`. Questo approccio e semplice ma introduce latenza e carico sul database.

**Outbox via CDC (Debezium):** un connettore CDC cattura i cambiamenti alla tabella outbox tramite il WAL del database e li pubblica direttamente su Kafka. Questo approccio elimina il polling, riduce la latenza e non aggiunge carico di query al database.

```json
{
  "name": "outbox-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "debezium",
    "database.password": "${env:DB_PASSWORD}",
    "database.dbname": "orders",
    "table.include.list": "public.outbox",
    "transforms": "outbox",
    "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
    "transforms.outbox.table.fields.additional.placement": "event_type:header:eventType",
    "transforms.outbox.route.by.field": "aggregate_type",
    "transforms.outbox.route.topic.replacement": "events.${routedByValue}"
  }
}
```

### Inbox Pattern

L'Inbox Pattern e il complemento consumer-side dell'Outbox Pattern. Risolve il problema della deduplicazione lato consumer: poiche l'Outbox garantisce at-least-once delivery, il consumer potrebbe ricevere lo stesso evento piu volte.

**Meccanismo:** il consumer salva l'identificatore dell'evento in una tabella `inbox` nella stessa transazione che applica gli effetti collaterali. Se l'identificatore esiste gia, il consumer ignora il messaggio. Questo garantisce exactly-once processing al confine consumer-database.

```sql
-- Schema della tabella inbox
CREATE TABLE inbox (
    event_id      UUID PRIMARY KEY,
    event_type    VARCHAR(255) NOT NULL,
    received_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at  TIMESTAMPTZ
);
```

```python
def handle_event(db, event):
    event_id = event['eventId']
    with db.begin():
        # Tentativo di inserimento nell'inbox (idempotente)
        result = db.execute(
            "INSERT INTO inbox (event_id, event_type) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING event_id",
            (event_id, event['eventType'])
        ).fetchone()

        if result is None:
            return  # Evento gia processato, skip

        # Applicare gli effetti collaterali
        apply_business_logic(db, event['data'])

        # Marcare come processato
        db.execute("UPDATE inbox SET processed_at = NOW() WHERE event_id = %s", (event_id,))
```

### Anti-Pattern nelle Architetture Event-Driven

**Distributed Monolith:** il anti-pattern piu comune. Si verifica quando i servizi vengono scomposti dal monolite ma rimangono strettamente accoppiati — condividono tabelle di database, richiedono deployment sincronizzato o comunicano in modo eccessivamente chatty tramite il broker. Il risultato e tutta la complessita operativa di un sistema distribuito senza i benefici di indipendenza e scalabilita.

**Event Schema senza Validazione:** pubblicare eventi senza validazione dello schema espone il sistema a errori di tipo, typos e payload malformati che causano comportamenti imprevedibili nei consumer. La soluzione e l'adozione di un Schema Registry con controlli di compatibilita automatici.

**God Events:** eventi che trasportano troppi dati di troppi domini diversi. Un singolo evento `OrderEvent` che contiene dati di ordine, pagamento, inventario e spedizione accoppia tutti i consumer a tutti i domini. La soluzione e decomposere in eventi di dominio specifici (`OrderCreated`, `PaymentProcessed`, `InventoryReserved`).

**Temporal Coupling nascosto:** un servizio pubblica un evento e un altro reagisce, ma il consumer assume implicitamente che l'evento arrivi entro un certo tempo. Se il broker e lento o il consumer e in ritardo, la logica si rompe. La soluzione e progettare i consumer per essere resilienti a ritardi arbitrari e non assumere mai tempistiche di delivery.

**Mancanza di Observability:** senza distributed tracing e correlation ID propagati attraverso il broker, il debugging di flussi event-driven diventa estremamente difficile. Ogni evento deve trasportare `correlationId` e `causationId` per ricostruire la catena di causalita.

**Over-eventing:** pubblicare un evento per ogni micro-cambiamento di stato (campo singolo aggiornato) genera un volume eccessivo di messaggi e sovraccarica i consumer. Raggruppare le modifiche in eventi di dominio significativi con granularita appropriata.

---

## 9. Stream Processing

### Apache Kafka Streams

Kafka Streams e una libreria per costruire applicazioni di stream processing come applicazioni Java/Scala standard, senza la necessita di un cluster separato.

Caratteristiche principali:
- Elaborazione record-by-record con bassa latenza
- Supporto per operazioni stateless (filter, map, flatMap) e stateful (aggregate, join, windowing)
- State stores locali (RocksDB) con changelog topics per fault tolerance
- Exactly-once processing semantics (EOS v2)

### Apache Flink

Apache Flink e un framework distribuito per stream e batch processing. A differenza di Kafka Streams, richiede un cluster dedicato ma offre funzionalita piu avanzate.

```java
// Flink — esempio di conteggio eventi per finestra temporale
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.enableCheckpointing(60000, CheckpointingMode.EXACTLY_ONCE);

KafkaSource<String> source = KafkaSource.<String>builder()
    .setBootstrapServers("kafka1:9092")
    .setTopics("click-events")
    .setGroupId("click-analytics")
    .setStartingOffsets(OffsetsInitializer.committedOffsets(OffsetResetStrategy.EARLIEST))
    .setValueOnlyDeserializer(new SimpleStringSchema())
    .build();

DataStream<String> clicks = env.fromSource(source, WatermarkStrategy
    .forBoundedOutOfOrderness(Duration.ofSeconds(10))
    .withTimestampAssigner((event, timestamp) -> extractTimestamp(event)),
    "Kafka Source");

clicks
    .map(json -> parseClickEvent(json))
    .keyBy(event -> event.getPageId())
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .aggregate(new ClickCountAggregator())
    .addSink(new ElasticsearchSink<>(elasticsearchConfig));

env.execute("Click Analytics Pipeline");
```

### Windowing

Il windowing raggruppa gli eventi in finestre temporali per operazioni di aggregazione.

**Tumbling window:** finestre fisse non sovrapposte di durata identica. Ogni evento appartiene a esattamente una finestra. Esempio: conteggio eventi ogni 5 minuti.

**Hopping window (sliding con step fisso):** finestre di durata fissa che avanzano di un passo (hop) definito. Le finestre si sovrappongono se hop < durata. Esempio: finestra di 10 minuti che avanza ogni 5 minuti.

**Sliding window:** finestre che si attivano quando due eventi distano meno della durata della finestra. Ogni evento puo appartenere a piu finestre. Usato tipicamente per join tra stream.

**Session window:** finestre definite dall'inattivita. Una sessione si chiude quando non arrivano eventi per un periodo (gap) definito. Ideale per raggruppare l'attivita utente.

```
Tumbling (5 min):  |-------|-------|-------|
Hopping (10/5):    |-----------|
                        |-----------|
                             |-----------|
Session (gap 2min): |--eventi--| gap |--eventi--|
```

### Watermarks e Late Arrivals

I watermarks sono un meccanismo per gestire l'event-time processing in presenza di eventi fuori ordine. Un watermark con timestamp T indica che tutti gli eventi con timestamp <= T sono presumibilmente arrivati.

**Bounded out-of-orderness:** il watermark e generato con un ritardo fisso rispetto all'evento con il timestamp piu recente visto. Ad esempio, con un ritardo di 10 secondi, il watermark a t e `max_event_time - 10s`.

**Late arrivals:** eventi che arrivano dopo che il watermark ha superato il loro timestamp.

Strategie per i late arrivals:
- **Drop:** scartare gli eventi in ritardo (semplice ma perde dati)
- **Side output:** inviare gli eventi in ritardo a un canale laterale per processamento separato
- **Allowed lateness:** mantenere le finestre aperte per un periodo aggiuntivo dopo la chiusura nominale

### State Management

Le operazioni stateful richiedono la gestione di stato persistente. I framework di stream processing offrono:

- **State backends:** RocksDB (su disco, per stato grande), heap (in memoria, per stato piccolo)
- **Checkpointing:** snapshot periodici dello stato per fault tolerance. In caso di fallimento, lo stato viene ripristinato dall'ultimo checkpoint
- **Changelog topics:** Kafka Streams salva le modifiche allo stato in topic di changelog per il recovery

### Exactly-Once Semantics

L'exactly-once nel stream processing richiede coordinamento tra sorgente, processing e sink:

1. **Source:** i messaggi sono letti da un punto noto (offset Kafka)
2. **Processing:** le operazioni stateful sono atomiche con il commit dell'offset
3. **Sink:** le scritture sono idempotenti o transazionali

In Kafka Streams, EOS v2 (`exactly_once_v2`) utilizza transazioni Kafka per legare offset commit e state store updates in un'unica transazione atomica.

### Stream-Table Duality

Uno stream puo essere visto come il changelog di una tabella e una tabella puo essere vista come lo snapshot di uno stream ad un punto nel tempo.

- **Stream -> Table:** applicando tutti gli eventi dello stream in ordine si ottiene lo stato attuale (la tabella)
- **Table -> Stream:** registrando ogni modifica alla tabella si ottiene uno stream di cambiamenti

Questo concetto e fondamentale per i join stream-table in Kafka Streams e per la comprensione del log compaction.

### Change Data Capture (CDC) con Debezium

Debezium cattura le modifiche ai dati in un database e le pubblica come eventi su Kafka. Supporta PostgreSQL, MySQL, MongoDB, SQL Server e altri.

```json
{
  "name": "postgres-cdc",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "debezium",
    "database.password": "${env:DB_PASSWORD}",
    "database.dbname": "ecommerce",
    "database.server.name": "prod",
    "table.include.list": "public.orders,public.customers",
    "plugin.name": "pgoutput",
    "slot.name": "debezium_slot",
    "publication.name": "dbz_publication",
    "topic.prefix": "cdc",
    "snapshot.mode": "initial",
    "tombstones.on.delete": true,
    "key.converter": "io.confluent.connect.avro.AvroConverter",
    "key.converter.schema.registry.url": "http://schema-registry:8081",
    "value.converter": "io.confluent.connect.avro.AvroConverter",
    "value.converter.schema.registry.url": "http://schema-registry:8081"
  }
}
```

I cambiamenti vengono emessi come eventi con le sezioni `before` e `after`, l'operazione (`c`=create, `u`=update, `d`=delete, `r`=read per lo snapshot) e i metadati della sorgente.

---

## 10. Performance e Tuning

### Throughput vs Latency Trade-offs

Non e possibile ottimizzare simultaneamente per throughput massimo e latenza minima. Le scelte progettuali implicano compromessi:

| Parametro | Throughput elevato | Latenza bassa |
|---|---|---|
| Batching | Batch grandi (32-128 KB) | Batch piccoli o singoli record |
| Linger.ms (Kafka) | 20-100ms | 0ms |
| Compression | Abilitata (zstd, lz4) | Disabilitata o lz4 |
| Acks (Kafka) | `acks=1` | `acks=1` (vs `all` per durabilita) |
| Prefetch (RabbitMQ) | Alto (100-250) | Basso (1-10) |
| Numero partizioni | Molte (piu parallelismo) | Meno rilevante |

### Batching Strategies

Il batching riduce l'overhead per-messaggio raggruppando piu messaggi in un singolo invio di rete.

**Producer-side batching (Kafka):**
- `batch.size`: dimensione massima del batch in byte (default 16384, consigliato 32768-131072 per throughput)
- `linger.ms`: tempo massimo di attesa per accumulare il batch (default 0, consigliato 5-50 per throughput)
- Il batch e inviato quando si raggiunge `batch.size` O scade `linger.ms`, il primo dei due

**Consumer-side batching:**
- Processare messaggi in micro-batch invece che singolarmente
- Utilizzare bulk write verso database (batch INSERT/UPSERT)
- Bilanciare la dimensione del batch con il rischio di ri-processamento in caso di fallimento

### Compression

| Codec | Rapporto | Velocita compressione | Velocita decompressione | CPU | Uso consigliato |
|---|---|---|---|---|---|
| gzip | Ottimo | Lenta | Media | Alto | Archiviazione, dati testuali |
| snappy | Buono | Veloce | Molto veloce | Basso | General purpose |
| lz4 | Buono | Molto veloce | Molto veloce | Molto basso | Latenza bassa, throughput alto |
| zstd | Eccellente | Veloce | Veloce | Medio | Miglior rapporto qualita/velocita |

Raccomandazione: `zstd` per il miglior compromesso compressione/performance, `lz4` quando la latenza e critica.

### Partition Count Optimization

Il numero di partizioni influenza direttamente il parallelismo e la scalabilita:

- **Troppo poche partizioni:** limitano il parallelismo dei consumer. Se i consumer sono piu delle partizioni, alcuni rimangono inattivi.
- **Troppe partizioni:** aumentano l'overhead dei metadati, il tempo di failover del leader, l'utilizzo di memoria del broker e i file descriptor aperti.

Regola pratica per Kafka:
- Partizioni >= numero massimo previsto di consumer nel gruppo
- Per topic ad alto throughput: iniziare con 6-12 partizioni per broker
- Prevedere la crescita: e possibile aumentare le partizioni ma non ridurle
- Considerare che ogni partizione usa circa 1-10 MB di memoria sul broker

### Consumer Scaling

- Il numero massimo di consumer attivi in un gruppo e uguale al numero di partizioni
- Aggiungere consumer oltre il numero di partizioni non aumenta il parallelismo
- Il rebalancing durante lo scaling causa brevi interruzioni del consumo
- Utilizzare `CooperativeStickyAssignor` per minimizzare l'impatto del rebalancing
- Valutare il throughput per consumer prima di aggiungere istanze

### Backpressure Handling

```
# Strategia di backpressure a piu livelli

1. Consumer-level: ridurre il prefetch/max.poll.records
   Kafka: max.poll.records=100 (default 500)
   RabbitMQ: basic_qos(prefetch_count=10)

2. Application-level: bounded queue interna
   Usare un thread pool con coda limitata
   Rifiutare nuovi messaggi quando la coda interna e piena

3. Broker-level: bounded queue/topic
   RabbitMQ: x-max-length + overflow=reject-publish
   Kafka: la retention gestisce implicitamente la dimensione

4. Producer-level: circuit breaker
   Fermare la produzione quando il consumer lag supera una soglia
   Riprendere quando il lag rientra nella normalita
```

### Connection Pooling

Per RabbitMQ, riutilizzare le connessioni TCP e creare channel separati per thread. Non creare una connessione per richiesta.

Per Kafka, il `KafkaProducer` e thread-safe e deve essere condiviso. Il `KafkaConsumer` non e thread-safe e richiede un'istanza per thread.

### Serialization Format Comparison

| Formato | Dimensione | Velocita serializzazione | Schema evolution | Human readable | Ecosystem |
|---|---|---|---|---|---|
| JSON | Grande | Lenta | Manuale | Si | Universale |
| Avro | Piccolo | Veloce | Schema Registry | No | Kafka-centric |
| Protobuf | Piccolo | Molto veloce | Built-in (proto files) | No | Cross-platform |
| MessagePack | Medio | Veloce | No | No | Leggero |

Raccomandazione: Avro con Schema Registry per ecosistemi Kafka; Protobuf per sistemi cross-platform con requisiti di performance.

---

## 11. Monitoring e Troubleshooting

### Metriche Chiave

**Consumer lag:** la differenza tra l'offset piu recente nella partizione e l'offset committato dal consumer. Un lag crescente indica che il consumer non riesce a tenere il passo con il producer.

**Throughput:** messaggi/secondo (o byte/secondo) in ingresso e in uscita per topic, coda o broker. Monitorare sia il lato producer che il lato consumer.

**Latency:** il tempo tra la pubblicazione e il consumo di un messaggio. Distinguere tra publish latency (producer -> broker) e end-to-end latency (producer -> consumer processing complete).

**Queue depth:** il numero di messaggi in attesa nella coda. Un trend crescente indica un problema di capacita del consumer.

### Monitoring RabbitMQ

**Management API:**

```bash
# Stato generale del nodo
curl -u admin:password http://localhost:15672/api/overview

# Elenco delle code con metriche
curl -u admin:password http://localhost:15672/api/queues

# Metriche di una coda specifica
curl -u admin:password http://localhost:15672/api/queues/%2Fproduction/orders

# Connessioni attive
curl -u admin:password http://localhost:15672/api/connections
```

**Prometheus plugin:**

```bash
# Abilitare il plugin Prometheus
rabbitmq-plugins enable rabbitmq_prometheus

# Metriche disponibili su http://localhost:15692/metrics
# Metriche chiave:
# rabbitmq_queue_messages               - messaggi totali per coda
# rabbitmq_queue_messages_ready         - messaggi pronti per il consumo
# rabbitmq_queue_messages_unacked       - messaggi in elaborazione
# rabbitmq_queue_consumers              - consumer attivi per coda
# rabbitmq_channel_messages_published   - messaggi pubblicati per canale
# rabbitmq_channel_messages_delivered   - messaggi consegnati per canale
# rabbitmq_node_mem_used                - memoria utilizzata
# rabbitmq_node_disk_free               - spazio disco libero
```

```yaml
# prometheus.yml — scrape configuration per RabbitMQ
scrape_configs:
  - job_name: 'rabbitmq'
    scrape_interval: 15s
    static_configs:
      - targets: ['rabbitmq:15692']
    metrics_path: /metrics
```

### Monitoring Kafka

**JMX Metrics:**

```bash
# Abilitare JMX sul broker
export KAFKA_JMX_OPTS="-Dcom.sun.management.jmxremote \
  -Dcom.sun.management.jmxremote.port=9999 \
  -Dcom.sun.management.jmxremote.authenticate=false \
  -Dcom.sun.management.jmxremote.ssl=false"
```

Metriche JMX critiche:
- `kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec` — messaggi in ingresso/sec
- `kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec` — byte in ingresso/sec
- `kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions` — partizioni sotto-replicate (dovrebbe essere 0)
- `kafka.server:type=ReplicaManager,name=IsrShrinksPerSec` — restringimenti ISR
- `kafka.controller:type=KafkaController,name=ActiveControllerCount` — controller attivo (1 per cluster)
- `kafka.server:type=BrokerTopicMetrics,name=TotalProduceRequestsPerSec` — richieste produce/sec
- `kafka.network:type=RequestMetrics,name=RequestQueueTimeMs` — tempo in coda delle richieste

**Burrow per consumer lag:**

Burrow e uno strumento dedicato al monitoraggio del consumer lag in Kafka. Valuta il trend del lag e classifica lo stato del consumer.

```bash
# Verificare lo stato di un consumer group via Burrow
curl http://burrow:8000/v3/kafka/production/consumer/order-processor/status

# Risposta tipica
{
  "status": "OK",          # OK, WARNING, ERR, STOP
  "complete": true,
  "partitions": [
    {"topic": "orders", "partition": 0, "status": "OK", "lag": 15},
    {"topic": "orders", "partition": 1, "status": "OK", "lag": 8}
  ],
  "totallag": 23
}
```

### Alerting

```yaml
# Alerting rules per Prometheus (alerts.yml)
groups:
  - name: messaging_alerts
    rules:
      # RabbitMQ — coda che cresce
      - alert: RabbitMQQueueGrowing
        expr: increase(rabbitmq_queue_messages[5m]) > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "La coda {{ $labels.queue }} sta crescendo"
          description: "La coda ha accumulato {{ $value }} messaggi negli ultimi 5 minuti"

      # RabbitMQ — DLQ non vuota
      - alert: RabbitMQDeadLetterMessages
        expr: rabbitmq_queue_messages{queue=~".*dlq.*|.*dead.*"} > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Messaggi nella DLQ {{ $labels.queue }}"

      # Kafka — consumer lag elevato
      - alert: KafkaConsumerLagHigh
        expr: kafka_consumer_group_lag > 10000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Consumer lag elevato per {{ $labels.consumergroup }}"
          description: "Lag: {{ $value }} per il topic {{ $labels.topic }}"

      # Kafka — partizioni sotto-replicate
      - alert: KafkaUnderReplicatedPartitions
        expr: kafka_server_replicamanager_underreplicatedpartitions > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Partizioni sotto-replicate sul broker {{ $labels.instance }}"

      # Kafka — nessun controller attivo
      - alert: KafkaNoActiveController
        expr: sum(kafka_controller_kafkacontroller_activecontrollercount) != 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Cluster Kafka senza controller attivo"
```

### Distributed Tracing con OpenTelemetry

I message queue introducono una sfida specifica per il distributed tracing: il disaccoppiamento temporale tra producer e consumer rende impossibile tracciare il flusso di un messaggio senza propagazione esplicita del contesto di trace.

**Context Propagation:** il principio fondamentale e l'embedding del trace context (trace ID, span ID, baggage) negli header o nelle proprieta del messaggio. Il producer inietta il contesto prima di pubblicare; il consumer lo estrae e lo usa per creare uno span figlio, collegando la catena di elaborazione.

```python
# Producer — iniettare il contesto di trace negli header del messaggio
from opentelemetry import trace, context
from opentelemetry.propagators import inject

tracer = trace.get_tracer("order-service")

def publish_order_event(producer, order):
    with tracer.start_as_current_span("publish_order_created") as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.destination.name", "orders")
        span.set_attribute("messaging.operation.type", "publish")

        # Iniettare il contesto nei header Kafka
        headers = {}
        inject(headers)
        kafka_headers = [(k, v.encode()) for k, v in headers.items()]

        producer.produce(
            topic='orders',
            key=order['id'],
            value=json.dumps(order),
            headers=kafka_headers
        )
```

```python
# Consumer — estrarre il contesto e creare uno span figlio
from opentelemetry.propagators import extract

def process_message(msg):
    # Estrarre il contesto dagli header del messaggio
    headers_dict = {k: v.decode() for k, v in msg.headers() or []}
    ctx = extract(headers_dict)

    with tracer.start_as_current_span(
        "process_order_created",
        context=ctx,
        kind=trace.SpanKind.CONSUMER
    ) as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.destination.name", "orders")
        span.set_attribute("messaging.operation.type", "process")
        span.set_attribute("messaging.kafka.consumer.group", "order-processor")
        span.set_attribute("messaging.message.id", msg.key())

        handle_order(json.loads(msg.value()))
```

**Semantic Conventions per il Messaging:** OpenTelemetry definisce convenzioni semantiche standard per gli attributi degli span di messaging, garantendo interoperabilita tra strumenti di observability:

| Attributo | Descrizione | Esempio |
|---|---|---|
| `messaging.system` | Nome del sistema di messaging | `kafka`, `rabbitmq`, `nats` |
| `messaging.destination.name` | Topic o coda di destinazione | `orders` |
| `messaging.operation.type` | Tipo di operazione | `publish`, `process`, `receive` |
| `messaging.message.id` | ID univoco del messaggio | `msg-abc-123` |
| `messaging.kafka.consumer.group` | Consumer group (Kafka) | `order-processor` |
| `messaging.kafka.message.offset` | Offset del messaggio | `42567` |

**Strumentazione automatica:** per la maggior parte dei client (confluent-kafka, pika, nats.py), esistono librerie di auto-instrumentation OpenTelemetry che intercettano automaticamente le operazioni di publish e consume, iniettando e estraendo il trace context senza modifiche al codice applicativo.

```bash
# Installare l'auto-instrumentation per Kafka (Python)
pip install opentelemetry-instrumentation-confluent-kafka

# Per RabbitMQ/pika
pip install opentelemetry-instrumentation-pika
```

**Grafana + Tempo per la visualizzazione:** configurare Grafana con Tempo come backend di tracing consente di visualizzare i flussi di messaggi attraverso producer, broker e consumer, con la possibilita di correlare le trace con i log (Loki) e le metriche (Prometheus/Mimir).

### Problemi Comuni e Risoluzione

**Consumer lag crescente:**
- Cause: consumer troppo lento, troppi pochi consumer, errori nel processing, GC pauses
- Diagnosi: verificare il throughput del consumer, controllare i log per errori, monitorare CPU e memoria
- Risoluzione: aumentare il numero di consumer (fino al numero di partizioni), ottimizzare il processing, aumentare il batch size, ridurre l'elaborazione per messaggio

**Message accumulation (RabbitMQ):**
- Cause: consumer disconnesso, consumer lento, prefetch troppo alto con elaborazione lenta
- Diagnosi: `rabbitmqctl list_queues name messages consumers`, verificare il numero di consumer attivi
- Risoluzione: riavviare i consumer, ridurre il prefetch, aggiungere consumer, verificare le connessioni

**Rebalancing storms (Kafka):**
- Cause: consumer instabili che entrano e escono dal gruppo, `session.timeout.ms` troppo basso, `max.poll.interval.ms` troppo basso
- Diagnosi: cercare nei log del broker "JoinGroup" e "LeaveGroup" frequenti
- Risoluzione: aumentare `session.timeout.ms` (45-60s), `max.poll.interval.ms` (5-10min), usare `CooperativeStickyAssignor`, ridurre il processing time per batch

**Split brain (RabbitMQ cluster):**
- Cause: network partition tra i nodi del cluster
- Diagnosi: `rabbitmqctl cluster_status`, verificare `partitions` non vuoto
- Risoluzione: configurare `cluster_partition_handling = pause_minority`, risolvere il problema di rete, riavviare i nodi in minoranza

### Disaster Recovery

- **RabbitMQ:** quorum queues con 3+ nodi, lazy queues per durabilita, shovel per cross-datacenter replication, backup periodico delle definizioni (`rabbitmqadmin export definitions.json`)
- **Kafka:** replication factor >= 3, `min.insync.replicas = 2`, `unclean.leader.election.enable = false`, MirrorMaker 2 per cross-datacenter, backup dei consumer group offsets

```bash
# Esportare le definizioni RabbitMQ per backup
rabbitmqadmin export definitions.json

# Importare le definizioni per il recovery
rabbitmqadmin import definitions.json

# Kafka — verificare lo stato delle partizioni
kafka-topics.sh --bootstrap-server kafka1:9092 --describe --under-replicated-partitions
kafka-topics.sh --bootstrap-server kafka1:9092 --describe --unavailable-partitions
```

---

## 12. Best Practices

### Message Design

**Messaggi piccoli:** mantenere i messaggi sotto i 1 MB. Per dati grandi, usare il claim check pattern: memorizzare il payload in un object store (S3, MinIO) e inviare solo il riferimento nel messaggio.

**Auto-descrittivi:** ogni messaggio deve includere tipo, versione, timestamp, source e correlation ID. Seguire lo standard CloudEvents per l'envelope.

**Versionati:** includere sempre la versione dello schema nel messaggio. Usare schema evolution backward-compatible (aggiungere campi opzionali, non rimuovere o rinominare campi esistenti).

```json
{
  "specversion": "1.0",
  "type": "com.ecommerce.order.created.v2",
  "source": "/services/order-service",
  "id": "evt-unique-id",
  "time": "2026-04-11T10:00:00Z",
  "datacontenttype": "application/json",
  "data": { }
}
```

### Topic e Queue Naming Conventions

Adottare una convenzione di naming consistente:

```
# Pattern consigliato
<domain>.<entity>.<action>

# Esempi
ecommerce.orders.created
ecommerce.orders.updated
ecommerce.payments.processed
ecommerce.inventory.reserved

# Per ambienti
dev.ecommerce.orders.created
prod.ecommerce.orders.created

# Per DLQ
ecommerce.orders.created.dlq

# Evitare
orders          # Troppo generico
order-created   # Non strutturato
OrderCreated    # CamelCase non convenzionale per topic
```

### Idempotent Processing

Ogni consumer deve essere progettato per gestire messaggi duplicati senza effetti collaterali:

```python
# Pattern di deduplicazione con database
import hashlib

def process_message(message, db):
    message_id = message['eventId']

    # Verificare se il messaggio e gia stato processato
    if db.execute("SELECT 1 FROM processed_messages WHERE id = %s", (message_id,)).fetchone():
        return  # Gia processato, ignorare

    # Processare il messaggio in una transazione
    with db.begin():
        handle_business_logic(message)
        db.execute(
            "INSERT INTO processed_messages (id, processed_at) VALUES (%s, NOW())",
            (message_id,)
        )
    # Il commit della transazione include sia il business logic che il tracking
```

### Poison Message Handling

Un poison message e un messaggio che causa ripetutamente un errore nel consumer, bloccando l'elaborazione.

Strategie di gestione:
1. **Retry con backoff:** ritentare N volte con delay esponenziale
2. **DLQ:** dopo N tentativi, spostare il messaggio in una dead letter queue
3. **Parking lot:** memorizzare il messaggio in un database per analisi manuale
4. **Circuit breaker:** se troppi messaggi consecutivi falliscono, fermare il consumer e allertare

```python
# Gestione poison messages con retry e DLQ
MAX_RETRIES = 3

def consume_with_retry(message, channel):
    retry_count = message.headers.get('x-retry-count', 0)

    try:
        process_message(message.body)
        channel.basic_ack(delivery_tag=message.delivery_tag)
    except RecoverableError:
        if retry_count < MAX_RETRIES:
            # Ripubblica con retry count incrementato e delay
            headers = {'x-retry-count': retry_count + 1}
            channel.basic_publish(
                exchange='retry-exchange',
                routing_key=message.routing_key,
                body=message.body,
                properties=pika.BasicProperties(
                    headers=headers,
                    expiration=str(2 ** retry_count * 1000)  # Backoff esponenziale
                )
            )
        else:
            # Invia alla DLQ
            channel.basic_publish(
                exchange='dlx-exchange',
                routing_key='dlq.' + message.routing_key,
                body=message.body,
                properties=pika.BasicProperties(headers={'x-original-error': str(e)})
            )
        channel.basic_ack(delivery_tag=message.delivery_tag)
    except FatalError:
        # Errore non recuperabile, invia direttamente alla DLQ
        channel.basic_publish(
            exchange='dlx-exchange',
            routing_key='dlq.' + message.routing_key,
            body=message.body
        )
        channel.basic_ack(delivery_tag=message.delivery_tag)
```

### Schema Evolution

Regole per l'evoluzione degli schema senza breaking changes:

- **Aggiungere campi:** sempre con un valore di default. I consumer vecchi ignorano i campi sconosciuti
- **Rimuovere campi:** mai direttamente. Marcare come deprecated, smettere di popolarli, rimuovere dopo un periodo di migrazione
- **Rinominare campi:** mai. Aggiungere il campo con il nuovo nome, mantenere il vecchio con lo stesso valore
- **Cambiare il tipo:** mai. Creare una nuova versione dello schema
- **Aggiungere valori a un enum:** ammesso in Avro con `FORWARD` compatibility

### Testing Event-Driven Systems

**In-memory brokers:** per test unitari, usare implementazioni in-memory del broker per eliminare la dipendenza dall'infrastruttura.

**Testcontainers:** per test di integrazione, lanciare container Docker effimeri di RabbitMQ, Kafka o NATS.

```python
# Test di integrazione con testcontainers (Python)
from testcontainers.kafka import KafkaContainer

def test_order_processing():
    with KafkaContainer("confluentinc/cp-kafka:7.6.0") as kafka:
        bootstrap_servers = kafka.get_bootstrap_server()

        # Configurare producer e consumer con il broker del container
        producer = create_producer(bootstrap_servers)
        consumer = create_consumer(bootstrap_servers, "test-group")

        # Inviare un messaggio di test
        producer.send("orders", key="ord-1", value={"amount": 99.99})
        producer.flush()

        # Verificare che il consumer lo processi correttamente
        messages = consume_messages(consumer, timeout=10)
        assert len(messages) == 1
        assert messages[0]["amount"] == 99.99
```

```java
// Test di integrazione con Testcontainers (Java)
@Testcontainers
class KafkaIntegrationTest {
    @Container
    static KafkaContainer kafka = new KafkaContainer(
        DockerImageName.parse("confluentinc/cp-kafka:7.6.0")
    );

    @Test
    void shouldProcessOrderEvent() {
        String bootstrapServers = kafka.getBootstrapServers();
        // ... configurare producer/consumer e verificare il comportamento
    }
}
```

### Contract Testing per Eventi

Verificare che producer e consumer concordino sullo schema degli eventi:

- Utilizzare Pact o Spring Cloud Contract per definire contratti sugli eventi
- Il producer verifica di produrre eventi conformi al contratto
- Il consumer verifica di poter processare gli eventi del contratto
- I contratti sono versionati e condivisi tramite un broker centralizzato

### Capacity Planning

Fattori da considerare per il dimensionamento:

- **Throughput:** messaggi/secondo attesi in peak e in media
- **Dimensione messaggi:** dimensione media e massima dei messaggi
- **Retention:** per quanto tempo i messaggi devono essere conservati
- **Replication:** fattore di replicazione (moltiplica lo storage)
- **Consumer count:** numero di consumer group e consumer per gruppo

```
# Calcolo storage Kafka di esempio
messaggi/sec: 10.000
dimensione media: 1 KB
retention: 7 giorni
replication factor: 3

Storage giornaliero = 10.000 * 1 KB * 86.400 = ~864 GB/giorno (prima della compressione)
Con compressione zstd (rapporto ~4x): ~216 GB/giorno
Con replicazione: 216 * 3 = ~648 GB/giorno
Storage 7 giorni: ~4.5 TB

Aggiungere 20-30% di margine: ~5.5-6 TB
```

### Security

**Encryption:**
- TLS per la comunicazione in transito (client-broker, broker-broker)
- Encryption at rest per i dati su disco (filesystem encryption o cloud-managed encryption)
- Non criptare i singoli messaggi a livello applicativo a meno che non sia richiesto compliance specifico

**Authentication:**
- Kafka: SASL/PLAIN, SASL/SCRAM-SHA-256/512, SASL/GSSAPI (Kerberos), mTLS
- RabbitMQ: username/password, LDAP, x509 certificates
- NATS: NKey, JWT, TLS client certificates

**Authorization:**
- Kafka ACLs: permessi per topic, gruppo, cluster (read, write, create, delete, alter, describe)
- RabbitMQ: permessi per vhost (configure, write, read) con regex patterns
- NATS: permessi per subject tramite account JWT

```bash
# Kafka — creare un ACL
kafka-acls.sh --bootstrap-server kafka1:9092 \
  --add --allow-principal User:order-service \
  --operation Read --operation Write \
  --topic orders --group order-processor

# Kafka — elencare gli ACL
kafka-acls.sh --bootstrap-server kafka1:9092 --list --topic orders
```

**Network isolation:**
- Posizionare i broker in subnet private
- Utilizzare security groups/firewall per limitare l'accesso alle porte del broker
- Separare il traffico di management dal traffico dati
- Utilizzare VPN o private link per l'accesso cross-network

---

## 13. Broker Alternativi

### Redpanda

Redpanda e una piattaforma di streaming dati scritta in C++ che fornisce compatibilita completa con l'API e il protocollo Kafka, eliminando la necessita della JVM. Progettata per hardware moderno, Redpanda utilizza un'architettura thread-per-core (basata su Seastar, lo stesso framework di ScyllaDB) che massimizza l'utilizzo delle risorse hardware con zero-copy reads e memory-mapped storage.

**Architettura:**
- **Singolo binario:** Redpanda esegue come un singolo processo senza dipendenze esterne. Non richiede ZooKeeper, Raft e gestito internamente per i metadati e la replicazione.
- **Schema Registry integrato:** ogni nodo include uno schema registry compatibile con Confluent Schema Registry, eliminando un componente infrastrutturale separato. Gli schemi sono replicati via Raft senza dipendenze esterne.
- **Thread-per-core:** ogni core della CPU gestisce un sottoinsieme dedicato di partizioni, eliminando la contesa tra thread e riducendo le latency spikes tipiche delle applicazioni JVM (GC pauses).

**Vantaggi rispetto a Kafka:**
- Latenza p99 significativamente inferiore grazie all'eliminazione delle GC pauses della JVM
- Complessita operativa ridotta: un singolo binario vs Kafka + ZooKeeper/KRaft + Schema Registry
- Footprint di risorse inferiore: 10x meno memoria e CPU per lo stesso throughput in scenari mid-scale
- Startup in secondi vs minuti per Kafka

**Limitazioni:**
- Ecosystem piu piccolo: meno connettori, meno strumenti di terze parti
- Community piu giovane e meno documentazione rispetto a Kafka
- Il modello di licensing (Business Source License per le versioni recenti) puo essere restrittivo per alcuni usi
- Per cluster di dimensioni molto grandi (centinaia di broker, milioni di partizioni), Kafka resta piu testato in produzione

```yaml
# docker-compose.yml — Redpanda cluster a 3 nodi
version: '3.8'
services:
  redpanda-1:
    image: docker.redpanda.com/redpandadata/redpanda:v24.3.1
    command:
      - redpanda start
      - --smp 2
      - --memory 2G
      - --reserve-memory 0M
      - --overprovisioned
      - --node-id 0
      - --kafka-addr PLAINTEXT://0.0.0.0:29092,OUTSIDE://0.0.0.0:9092
      - --advertise-kafka-addr PLAINTEXT://redpanda-1:29092,OUTSIDE://localhost:9092
      - --pandaproxy-addr PLAINTEXT://0.0.0.0:28082,OUTSIDE://0.0.0.0:8082
      - --advertise-pandaproxy-addr PLAINTEXT://redpanda-1:28082,OUTSIDE://localhost:8082
      - --rpc-addr 0.0.0.0:33145
      - --advertise-rpc-addr redpanda-1:33145
    ports:
      - "9092:9092"
      - "8082:8082"    # HTTP Proxy (REST API Kafka-compatibile)
      - "8081:8081"    # Schema Registry
    volumes:
      - redpanda-1:/var/lib/redpanda/data

volumes:
  redpanda-1:
```

```bash
# Comandi rpk (CLI di Redpanda, compatibile con i concetti Kafka)
rpk topic create orders --partitions 6 --replicas 3
rpk topic produce orders
rpk topic consume orders --group test-group
rpk cluster info
rpk cluster health
```

**Quando scegliere Redpanda:**
- Workload che richiedono latenza sub-millisecondo con throughput elevato e predittivo
- Team con risorse operative limitate che cercano semplicita di deployment e gestione
- Ambienti con vincoli di risorse hardware (edge computing, test locali, ambienti di sviluppo)
- Progetti greenfield che necessitano di compatibilita Kafka senza l'overhead della JVM e senza GC pauses

### Apache Pulsar

Apache Pulsar e una piattaforma di messaging e streaming distribuita che separa architetturalmente il compute (broker) dallo storage (Apache BookKeeper). Questa separazione consente di scalare indipendentemente la capacita di elaborazione e quella di storage.

**Architettura a livelli:**
- **Broker:** nodi stateless che gestiscono le connessioni dei client, il routing dei messaggi e il protocollo. Poiche non mantengono stato locale, possono essere aggiunti o rimossi senza ribilanciamento dei dati.
- **BookKeeper (Bookie):** nodi di storage che gestiscono la persistenza dei dati. I messaggi sono scritti in frammenti (ledger) distribuiti tra piu bookies.
- **Coordination (Oxia/ZooKeeper):** servizio di coordinamento per i metadati del cluster. Pulsar 4.0 introduce Oxia, un servizio di coordinamento purpose-built che sostituisce ZooKeeper e risolve i limiti di scalabilita per ambienti con milioni di topic.

```
                ┌─────────────────────────────┐
                │         Client SDK           │
                └──────────┬──────────────────┘
                           │
                ┌──────────┴──────────────────┐
                │     Broker (stateless)       │
                │  Routing, protocol, caching  │
                └──────────┬──────────────────┘
                           │
                ┌──────────┴──────────────────┐
                │   BookKeeper (storage)       │
                │   Ledger, journal, write-    │
                │   ahead log distribuito      │
                └─────────────────────────────┘
```

**Multi-tenancy nativo:** Pulsar supporta multi-tenancy come funzionalita di primo livello. I tenant sono isolati con namespace, policy di retention, quote di throughput e permessi indipendenti. Ogni tenant puo avere limiti configurabili su storage, rate di produzione e numero di topic.

```bash
# Creare un tenant e un namespace
bin/pulsar-admin tenants create ecommerce \
  --admin-roles admin-role \
  --allowed-clusters production

bin/pulsar-admin namespaces create ecommerce/orders \
  --bundles 16

# Configurare le policy del namespace
bin/pulsar-admin namespaces set-retention ecommerce/orders \
  --size 50G --time 7d

bin/pulsar-admin namespaces set-message-ttl ecommerce/orders \
  --messageTTL 86400

# Rate limiting per namespace
bin/pulsar-admin namespaces set-publish-rate ecommerce/orders \
  --msg-publish-rate 10000 --byte-publish-rate 104857600
```

**Subscription Modes:** Pulsar offre quattro modalita di subscription che coprono sia gli scenari di streaming che quelli di queuing:

| Modalita | Comportamento | Equivalente |
|---|---|---|
| **Exclusive** | Un solo consumer per subscription | — |
| **Failover** | Un consumer attivo, gli altri in standby | Kafka consumer group (1 partition) |
| **Shared** | Messaggi distribuiti round-robin tra consumer | RabbitMQ competing consumers |
| **Key_Shared** | Messaggi con la stessa chiave al medesimo consumer | Kafka partition key routing |

La modalita **Shared** e particolarmente significativa: consente il pattern competing consumers senza il vincolo di partizioni di Kafka. Piu consumer possono processare messaggi dalla stessa subscription in parallelo, con i messaggi distribuiti individualmente.

**Geo-replication:** Pulsar supporta nativamente la replicazione geografica tra cluster. I messaggi pubblicati in un cluster vengono replicati automaticamente ai cluster configurati come peer.

```bash
# Abilitare la geo-replication per un namespace
bin/pulsar-admin namespaces set-clusters ecommerce/orders \
  --clusters cluster-eu,cluster-us,cluster-apac
```

**Quando scegliere Pulsar:**
- Architetture cloud-native che richiedono scaling indipendente di compute e storage
- Piattaforme multi-tenant (SaaS, Messaging-as-a-Service)
- Scenari che richiedono sia queuing (Shared subscription) che streaming (Exclusive/Failover)
- Requisiti di geo-replication nativa tra datacenter
- Ambienti con milioni di topic (Oxia risolve i limiti di scalabilita di ZooKeeper)

**Limitazioni:**
- Complessita operativa elevata: tre componenti da gestire (Broker, BookKeeper, Oxia/ZK)
- Community piu piccola di Kafka, meno connettori e integrazioni disponibili
- Curva di apprendimento ripida per chi proviene dall'ecosistema Kafka
- Il throughput grezzo per singola partizione e inferiore a Kafka in benchmark sintetici

### Confronto Complessivo dei Broker

| Caratteristica | Kafka | RabbitMQ | NATS | Redpanda | Pulsar |
|---|---|---|---|---|---|
| Linguaggio | Java/Scala | Erlang | Go | C++ | Java |
| Modello principale | Event log | Message queue | Pub/sub | Event log | Ibrido (log+queue) |
| Persistenza | Sempre | Configurabile | JetStream | Sempre | Sempre (BookKeeper) |
| Latenza p99 | 5-20ms | 1-5ms | <1ms | 1-5ms | 5-15ms |
| Throughput max | Molto alto | Medio | Alto | Molto alto | Alto |
| Multi-tenancy | ACL-based | Vhost | Account | ACL-based | Nativo (tenant) |
| Geo-replication | MirrorMaker 2 | Federation | Leafnode/Gateway | Redpanda Connect | Nativa |
| Compute-storage | Accoppiati | Accoppiati | Accoppiati | Accoppiati | Separati |
| Complessita ops | Alta | Media | Bassa | Bassa | Molto alta |
| Ecosystem | Molto ricco | Ricco | Minimo | Medio (compat. Kafka) | Medio |
| Licensing | Apache 2.0 | MPL 2.0 | Apache 2.0 | BSL (community edition) | Apache 2.0 |

---

## Esercizi

### Esercizio 1 — RabbitMQ con Dead-Letter Queue

Configurare un exchange RabbitMQ con una coda principale e una dead-letter queue (DLQ). Pubblicare messaggi che simulano errori di processing. Verificare che i messaggi falliti finiscano nella DLQ dopo il numero massimo di retry. Implementare un consumer che processi la DLQ per analisi.

### Esercizio 2 — Kafka Producer e Consumer Idempotente

Creare un topic Kafka con 3 partizioni e replication factor 2. Implementare un producer che invii ordini e un consumer idempotente che utilizzi un registro di deduplicazione (tabella DB o set in-memory) per garantire il processing exactly-once semantics.

### Esercizio 3 — Schema Registry e Compatibilita

Configurare Confluent Schema Registry con un topic Kafka. Registrare uno schema Avro per un evento. Evolvere lo schema aggiungendo un campo opzionale e verificare la compatibilita backward. Tentare una modifica breaking e osservare il rifiuto.

### Esercizio 4 — Monitoring del Consumer Lag

Configurare il monitoring del consumer lag Kafka con Prometheus e Grafana. Simulare un consumer lento e osservare il lag crescere. Implementare alerting quando il lag supera una soglia critica. Scalare i consumer e verificare il recupero del lag.

### Esercizio 5 — Event-Driven Saga Pattern

Implementare una saga coreografata per un flusso ordine-pagamento-spedizione usando tre topic Kafka. Ogni servizio pubblica eventi di successo o compensazione. Simulare il fallimento del servizio di pagamento e verificare che la compensazione annulli correttamente l'ordine.

### Esercizio 6 — Transactional Outbox con Debezium

Implementare il Transactional Outbox Pattern per un servizio ordini. Creare la tabella `outbox` in PostgreSQL. Implementare la logica di business che scrive nella tabella ordini e nella tabella outbox nella stessa transazione. Configurare un connettore Debezium con `EventRouter` SMT per pubblicare gli eventi su Kafka. Verificare che la creazione di un ordine produca un evento sul topic `events.Order` con il payload corretto. Simulare il fallimento del broker dopo la scrittura nel database e verificare che l'evento venga pubblicato al ripristino del broker.

### Esercizio 7 — Confronto Latenza tra Broker

Eseguire un benchmark comparativo di latenza tra Kafka, RabbitMQ e Redpanda utilizzando gli stessi parametri: messaggi da 1 KB, batch di 1 messaggio (latenza singola), 1 producer e 1 consumer. Misurare la latenza end-to-end (publish-to-consume) al p50, p95 e p99 per ciascun broker. Utilizzare i tool di benchmarking nativi di ogni piattaforma (`kafka-producer-perf-test.sh`, `rabbitmq-perf-test`, `rpk topic produce` con timing). Documentare i risultati e le configurazioni utilizzate. Ripetere il test con batch di 100 messaggi e confrontare l'impatto sul throughput.

### Esercizio 8 — OpenTelemetry Tracing su Kafka

Configurare un pipeline di tre servizi (order-service, payment-service, notification-service) connessi tramite topic Kafka. Implementare la propagazione del trace context OpenTelemetry tramite gli header dei messaggi Kafka. Utilizzare Jaeger o Tempo come backend di tracing e Grafana per la visualizzazione. Verificare che una singola richiesta di creazione ordine produca una trace end-to-end che attraversa tutti e tre i servizi, con span separati per publish e consume su ogni topic.

---

## Letture e Riferimenti

### Documentazione ufficiale

- Apache Kafka Documentation — <https://kafka.apache.org/documentation/> (consultato: 2026-05-24)
- RabbitMQ Documentation — <https://www.rabbitmq.com/docs> (consultato: 2026-05-24)
- NATS Documentation — <https://docs.nats.io/> (consultato: 2026-05-24)
- Confluent Schema Registry — <https://docs.confluent.io/platform/current/schema-registry/> (consultato: 2026-05-24)
- CloudEvents Specification — <https://cloudevents.io/> (consultato: 2026-05-24)

### Documentazione aggiuntiva

- Redpanda Documentation — <https://docs.redpanda.com/> (consultato: 2026-05-24)
- Apache Pulsar Documentation — <https://pulsar.apache.org/docs/> (consultato: 2026-05-24)
- RabbitMQ 4.3 Release Blog — <https://www.rabbitmq.com/blog/2026/04/23/rabbitmq-4.3-release> (consultato: 2026-05-24)
- Kafka Tiered Storage (KIP-405) — <https://kafka.apache.org/41/operations/tiered-storage/> (consultato: 2026-05-24)
- OpenTelemetry Messaging Semantic Conventions — <https://opentelemetry.io/docs/specs/semconv/messaging/> (consultato: 2026-05-24)
- Debezium Outbox Event Router — <https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html> (consultato: 2026-05-24)

### Libri consigliati

- Kleppmann M., *Designing Data-Intensive Applications*, O'Reilly, 2017
- Narkhede N., Shapira G., Palino T., *Kafka: The Definitive Guide*, O'Reilly, 2021
- Stopford B., *Designing Event-Driven Systems*, O'Reilly, 2018
- Siriwardena P., Dias K., *Microservices Security in Action*, Manning, 2020
- Newman S., *Building Microservices*, 2nd Edition, O'Reilly, 2021

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione con Message Queues |
|--------|--------|------------------------------|
| [05](05-kubernetes.md) | Kubernetes | Deployment di broker Kafka/RabbitMQ su K8s con StatefulSet e PVC |
| [08](08-monitoring-observability.md) | Monitoring e Observability | Consumer lag, throughput, metriche JMX, distributed tracing |
| [09](09-service-mesh.md) | Service Mesh | mTLS tra servizi e broker, traffic management |
| [11](11-database-management.md) | Database Management | CDC (Change Data Capture), outbox pattern, deduplicazione |
| [13](13-sicurezza-piattaforme.md) | Sicurezza delle Piattaforme | ACL broker, encryption in transit, SASL authentication |
| [14](14-infrastructure-as-code.md) | Infrastructure as Code | Provisioning automatico di cluster Kafka/RabbitMQ con Terraform, Pulumi |
| [16](16-api-gateway.md) | API Gateway | Event-driven API, webhook delivery, async request processing |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **Message broker** | Middleware che riceve, instrada e consegna messaggi tra producer e consumer |
| **Topic** | Canale logico di comunicazione in cui i messaggi vengono pubblicati e da cui vengono consumati |
| **Partizione** | Suddivisione di un topic Kafka che consente parallelismo nella lettura e nella scrittura |
| **Consumer group** | Insieme di consumer che si dividono il carico di lettura delle partizioni di un topic |
| **Dead-letter queue (DLQ)** | Coda separata in cui vengono inviati i messaggi che non possono essere processati dopo i retry |
| **Idempotenza** | Proprieta di un'operazione che produce lo stesso risultato anche se eseguita piu volte |
| **Consumer lag** | Distanza tra l'ultimo messaggio prodotto e l'ultimo messaggio consumato in una partizione |
| **Schema Registry** | Servizio centralizzato che gestisce e valida gli schemi dei messaggi per garantire compatibilita |
| **Event sourcing** | Pattern in cui lo stato del sistema e ricostruito da una sequenza immutabile di eventi |
| **Saga** | Pattern di coordinamento di transazioni distribuite tramite sequenza di transazioni locali con compensazione |
| **Offset** | Identificatore numerico univoco di un messaggio all'interno di una partizione Kafka |
| **Backpressure** | Meccanismo per rallentare i producer quando i consumer non riescono a tenere il passo |
| **At-least-once delivery** | Garanzia che ogni messaggio viene consegnato almeno una volta, con possibili duplicati |
| **Change Data Capture (CDC)** | Tecnica per intercettare le modifiche a un database e pubblicarle come eventi su un topic |
| **Tiered Storage** | Architettura di storage a due livelli (locale + remoto) che sposta i segmenti di log vecchi su object store economico |
| **Outbox Pattern** | Pattern in cui gli eventi vengono scritti in una tabella outbox nella stessa transazione dei dati di business, poi pubblicati sul broker da un relay separato |
| **Inbox Pattern** | Pattern consumer-side che registra gli ID degli eventi processati per garantire la deduplicazione e l'exactly-once processing |
| **KRaft** | Kafka Raft Metadata mode, il meccanismo di gestione dei metadati interno a Kafka che sostituisce ZooKeeper |
| **Leafnode** | Nodo NATS che si connette a un cluster centrale tramite una singola connessione per instradamento automatico dei messaggi, ideale per architetture edge |
| **Redpanda** | Piattaforma di streaming dati scritta in C++ compatibile con l'API Kafka, senza dipendenza dalla JVM |
| **Apache Pulsar** | Piattaforma di messaging e streaming con separazione architetturale tra compute (broker) e storage (BookKeeper) |
| **Khepri** | Metadata store basato su Raft introdotto in RabbitMQ 4.3 che sostituisce Mnesia per la gestione dei metadati del cluster |
| **Share Groups** | Nuovo tipo di consumer group in Kafka 4.0 che consente a piu consumer di condividere il consumo di una singola partizione |
| **Context Propagation** | Tecnica di distributed tracing che propaga trace ID e span ID attraverso gli header dei messaggi per mantenere la continuita della trace |
| **Stream (RabbitMQ)** | Tipo di coda RabbitMQ basata su log append-only che supporta replay, offset tracking e fan-out efficiente |
