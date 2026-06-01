---
corso: "Gestione Piattaforme e DevOps"
fase: "3 — Containerizzazione e Orchestrazione"
modulo: 6
titolo: "Docker Avanzato"
versione: "Docker 27.x / BuildKit 0.17"
livello: "Avanzato"
prerequisiti: ["05-kubernetes", "04-infrastructure-as-code"]
obiettivi:
  - "Progettare Dockerfile multi-stage ottimizzati con BuildKit mount cache e target distroless"
  - "Costruire immagini multi-architettura (amd64/arm64) con buildx e manifest list"
  - "Implementare una strategia completa di sicurezza container: rootless, read-only fs, SBOM, scan CVE"
  - "Gestire networking overlay e storage persistente in scenari di produzione Docker"
  - "Integrare Docker nelle pipeline CI/CD con registry privati, signing e supply-chain hygiene"
tag: [docker, buildkit, multi-stage, distroless, container-security, sbom, trivy, buildx]
---

# Docker Avanzato

> **Modulo 06** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Progettare Dockerfile multi-stage ottimizzati con BuildKit mount cache e target distroless
> 2. Costruire immagini multi-architettura (amd64/arm64) con buildx e manifest list
> 3. Implementare una strategia completa di sicurezza container: rootless, read-only fs, SBOM, scan CVE
> 4. Gestire networking overlay e storage persistente in scenari di produzione Docker
> 5. Integrare Docker nelle pipeline CI/CD con registry privati, signing e supply-chain hygiene
>
> **Prerequisiti:** [Kubernetes](05-kubernetes.md) · [Infrastructure as Code](04-infrastructure-as-code.md)
> **Tempo stimato:** 8-10 ore · **Livello:** Avanzato

## Idee guida

1. **BuildKit `--mount=type=cache` accelera build 10x.**
2. **Multi-arch buildx: amd64+arm64 single image.**
3. **Distroless > Alpine > Ubuntu per security/size.**
4. **SBOM via syft + scan via trivy = supply-chain hygiene.**


## Panoramica dell'Architettura Docker

Docker utilizza un'architettura client-server composta da diversi componenti fondamentali che collaborano per gestire il ciclo di vita dei container. Comprendere questa architettura in profondità è essenziale per sfruttare Docker in scenari di produzione complessi.

### Docker Daemon (dockerd)

Il **Docker daemon** (`dockerd`) è il processo persistente che gestisce gli oggetti Docker: immagini, container, network e volumi. Il daemon ascolta le richieste tramite l'API REST di Docker e può comunicare con altri daemon per gestire servizi distribuiti. Il daemon non costruisce direttamente i container, ma delega queste operazioni ai componenti sottostanti.

```bash
# Verificare lo stato del daemon
sudo systemctl status docker

# Configurazione del daemon tramite /etc/docker/daemon.json
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-address-pools": [
    {"base": "172.20.0.0/16", "size": 24}
  ]
}
```

### Docker Client

Il **Docker client** (`docker`) è l'interfaccia principale utilizzata dagli utenti per interagire con Docker. Quando si esegue un comando come `docker run`, il client invia queste istruzioni al daemon tramite l'API REST. Il client può comunicare con più daemon contemporaneamente, permettendo la gestione di ambienti remoti. La comunicazione avviene tramite socket Unix (`/var/run/docker.sock`) in locale, oppure tramite TCP per connessioni remote. È possibile configurare il client per puntare a daemon diversi attraverso la variabile d'ambiente `DOCKER_HOST`.

```bash
# Connessione a un daemon remoto via TCP
export DOCKER_HOST=tcp://192.168.1.100:2376

# Connessione con TLS
export DOCKER_HOST=tcp://192.168.1.100:2376
export DOCKER_TLS_VERIFY=1
export DOCKER_CERT_PATH=~/.docker/certs

# Utilizzare Docker context per gestire più ambienti
docker context create production --docker "host=tcp://prod-server:2376,ca=ca.pem,cert=cert.pem,key=key.pem"
docker context use production
```

### Container Runtime: containerd e runc

**containerd** è il runtime ad alto livello che gestisce il ciclo di vita completo dei container: download delle immagini, gestione dello storage, esecuzione e supervisione dei container, rete di basso livello. Opera come daemon indipendente e implementa le specifiche OCI (Open Container Initiative).

**runc** è il runtime a basso livello che crea ed esegue effettivamente i container secondo le specifiche OCI. Interagisce direttamente con le funzionalità del kernel Linux come namespaces e cgroups per isolare i processi.

```
Client (docker CLI) → Docker Daemon (dockerd) → containerd → runc → Container
                                                      ↓
                                                  Registry (pull/push immagini)
```

### Docker Registry

Il **registry** è un servizio di storage e distribuzione delle immagini Docker. Docker Hub è il registry pubblico predefinito, ma è possibile configurare registry privati per ambienti aziendali. Il daemon comunica con il registry per operazioni di `pull` e `push` delle immagini. Le immagini vengono trasferite come layer compressi, e il registry supporta la deduplicazione dei layer condivisi tra immagini diverse, ottimizzando lo storage e la banda di rete.

### Flusso di Esecuzione di un Container

Quando si esegue `docker run`, il flusso attraversa l'intera catena dei componenti. Il client invia la richiesta al daemon, che verifica la presenza dell'immagine localmente. Se l'immagine non è disponibile, il daemon la scarica dal registry. Successivamente, il daemon istruisce containerd a preparare il container: creazione del filesystem root a partire dai layer dell'immagine, configurazione dei namespaces (PID, network, mount, UTS, IPC, user) e dei cgroups per l'isolamento delle risorse. Infine, containerd delega a runc la creazione effettiva del processo isolato nel container. Questo flusso multi-layer garantisce separazione delle responsabilità e permette di sostituire singoli componenti senza impattare il resto dello stack.

---

## Dockerfile Avanzato

### Multi-Stage Builds

I multi-stage build rappresentano una delle tecniche più potenti per ottimizzare le immagini Docker. Consentono di utilizzare più istruzioni `FROM` in un singolo Dockerfile, separando l'ambiente di build dall'ambiente di runtime. Questo approccio riduce drasticamente la dimensione finale dell'immagine eliminando dipendenze di compilazione, strumenti di sviluppo e file intermedi.

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS production
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
ENTRYPOINT ["node"]
CMD ["dist/main.js"]
```

Per applicazioni Go, i multi-stage build sono particolarmente efficaci poiché il binario compilato non richiede dipendenze runtime:

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/server ./cmd/server

FROM scratch
COPY --from=builder /app/server /server
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
EXPOSE 8080
ENTRYPOINT ["/server"]
```

### Ottimizzazione del Layer Caching

Ogni istruzione nel Dockerfile crea un layer nell'immagine. Docker utilizza una cache per evitare di ricostruire layer che non sono cambiati. L'ordine delle istruzioni è fondamentale per sfruttare efficacemente la cache:

```dockerfile
# ERRATO: invalida la cache ad ogni modifica del codice
COPY . .
RUN npm install

# CORRETTO: le dipendenze vengono reinstallate solo se package.json cambia
COPY package*.json ./
RUN npm ci
COPY . .
```

Le best practice per il caching includono: posizionare le istruzioni che cambiano meno frequentemente in alto nel Dockerfile, raggruppare comandi `RUN` correlati con `&&` per ridurre il numero di layer, e utilizzare `--mount=type=cache` con BuildKit per cache persistenti.

```dockerfile
# Utilizzo di BuildKit mount cache per dipendenze
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### .dockerignore

Il file `.dockerignore` funziona in modo analogo a `.gitignore` e impedisce che file non necessari vengano inclusi nel build context. Questo accelera il processo di build e riduce la dimensione dell'immagine.

```dockerignore
# Dipendenze
node_modules/
vendor/

# Controllo versione
.git
.gitignore

# Ambienti di sviluppo
.env
.env.local
docker-compose*.yml
Dockerfile*

# Build artifacts
dist/
build/
*.log

# IDE e editor
.vscode/
.idea/
*.swp
```

### ARG vs ENV

`ARG` e `ENV` sono entrambe variabili, ma con scope e persistenza diversi. `ARG` è disponibile solo durante il build e non persiste nel container finale. `ENV` è disponibile sia durante il build sia nel container in esecuzione.

```dockerfile
# ARG: variabili di build-time
ARG NODE_VERSION=20
ARG BUILD_DATE
FROM node:${NODE_VERSION}-alpine

# ENV: variabili di runtime (persistono nel container)
ENV NODE_ENV=production
ENV APP_PORT=3000

# Combinazione: passare un ARG come ENV
ARG API_VERSION=v1
ENV API_VERSION=${API_VERSION}
```

```bash
# Override di ARG durante il build
docker build --build-arg NODE_VERSION=18 --build-arg BUILD_DATE=$(date -u +%Y%m%d) .
```

### COPY vs ADD

`COPY` esegue una copia diretta di file dal build context al filesystem dell'immagine. `ADD` ha funzionalità aggiuntive: può estrarre automaticamente archivi tar e supporta URL remoti. La best practice è utilizzare sempre `COPY` a meno che non serva specificamente l'estrazione automatica di `ADD`.

```dockerfile
# COPY: preferito nella maggior parte dei casi
COPY package.json ./
COPY src/ ./src/

# ADD: utile solo per estrarre archivi locali
ADD rootfs.tar.gz /

# ERRATO: non usare ADD per download (preferire curl/wget per controllare il processo)
# ADD https://example.com/file.tar.gz /tmp/
```

### ENTRYPOINT vs CMD

`ENTRYPOINT` definisce il comando principale del container che non può essere facilmente sovrascritto. `CMD` fornisce argomenti predefiniti per `ENTRYPOINT` o un comando predefinito che può essere sovrascritto. L'interazione tra i due è fondamentale per creare immagini flessibili.

```dockerfile
# Pattern consigliato: ENTRYPOINT + CMD
ENTRYPOINT ["python", "app.py"]
CMD ["--port", "8080"]

# L'utente può sovrascrivere solo gli argomenti CMD:
# docker run myimage --port 9090

# ENTRYPOINT con script di inizializzazione
COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["start"]
```

Esempio di entrypoint script:

```bash
#!/bin/sh
set -e

# Operazioni di inizializzazione
echo "Avvio con configurazione: $NODE_ENV"

# Eseguire migrazioni se necessario
if [ "$RUN_MIGRATIONS" = "true" ]; then
    npm run migrate
fi

exec "$@"
```

### HEALTHCHECK

L'istruzione `HEALTHCHECK` permette a Docker di verificare periodicamente lo stato del container. Questo è fondamentale per l'orchestrazione e il load balancing, poiché Docker può rilevare container in stato di errore anche se il processo principale è ancora attivo. I parametri configurabili sono: `--interval` (frequenza del controllo), `--timeout` (tempo massimo di attesa per la risposta), `--start-period` (tempo di grazia all'avvio prima di considerare i fallimenti), e `--retries` (numero di fallimenti consecutivi prima di dichiarare il container unhealthy).

```dockerfile
# Health check per applicazione web
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Health check per applicazione che non ha curl installato
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Health check per database PostgreSQL
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD pg_isready -U postgres || exit 1
```

I possibili stati risultanti sono: `starting` (durante lo start-period), `healthy` (il comando di check ha restituito exit code 0), e `unhealthy` (il numero massimo di retry è stato superato). Gli orchestratori possono reagire automaticamente allo stato unhealthy riavviando il container o rimuovendolo dal pool di load balancing.

### Non-Root USER

Eseguire container come utente non-root è una best practice di sicurezza fondamentale. Riduce la superficie di attacco nel caso in cui un processo nel container venga compromesso. Se un attaccante riesce a sfruttare una vulnerabilità nell'applicazione containerizzata, i danni saranno limitati ai permessi dell'utente non privilegiato, impedendo modifiche al sistema operativo del container e riducendo il rischio di escape verso l'host.

```dockerfile
# Su immagini basate su Debian/Ubuntu
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Su immagini Alpine
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Assicurarsi che i file copiati abbiano i permessi corretti
COPY --chown=appuser:appgroup ./dist /app/dist
```

Quando si utilizza l'istruzione `USER`, tutte le istruzioni successive (`RUN`, `CMD`, `ENTRYPOINT`) verranno eseguite con quell'utente. È importante posizionare `USER` dopo le operazioni che richiedono privilegi di root, come l'installazione di pacchetti o la creazione di directory.

### Best Practice per Immagini Leggere

Utilizzare immagini base minimali (`alpine`, `slim`, `distroless`), eliminare cache dei package manager dopo l'installazione, combinare comandi `RUN` correlati e sfruttare multi-stage builds. L'immagine `scratch` è l'opzione più leggera per binari statici compilati.

```dockerfile
# Esempio con distroless per Java
FROM eclipse-temurin:21-jdk AS builder
WORKDIR /app
COPY . .
RUN ./gradlew bootJar

FROM gcr.io/distroless/java21-debian12
COPY --from=builder /app/build/libs/app.jar /app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

---

## Docker Compose

### Sintassi compose.yaml v2

Docker Compose v2 utilizza il file `compose.yaml` (nome preferito rispetto a `docker-compose.yml`) e implementa la specifica Compose come plugin integrato nel CLI Docker. La versione del file non viene più dichiarata esplicitamente nel documento.

```yaml
# compose.yaml - Non serve più "version:"
name: my-application

services:
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
      args:
        NODE_ENV: production
    image: myapp/api:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/mydb
    depends_on:
      db:
        condition: service_healthy
    networks:
      - backend
    volumes:
      - api-data:/app/data
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          cpus: "0.25"
          memory: 128M

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - db-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

networks:
  backend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16

volumes:
  api-data:
  db-data:
    driver: local
```

### Services, Networks e Volumes

I **services** definiscono i container dell'applicazione con la loro configurazione completa. Ogni servizio può specificare l'immagine da usare, la build configuration, le variabili d'ambiente, le porte esposte, le dipendenze e i vincoli di risorse.

Le **networks** definiscono reti isolate per la comunicazione tra servizi. Docker Compose crea automaticamente una rete di default per ogni progetto, ma è possibile definire reti personalizzate per segmentare il traffico.

I **volumes** definiscono storage persistente che sopravvive al ciclo di vita dei container. I volumi possono essere named volumes (gestiti da Docker), bind mounts (directory dell'host) o tmpfs mounts (memoria volatile).

### depends_on con Healthcheck

La direttiva `depends_on` con la condizione `service_healthy` garantisce che un servizio venga avviato solo quando le sue dipendenze sono effettivamente pronte, non semplicemente avviate.

```yaml
services:
  app:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      migrations:
        condition: service_completed_successfully
```

### Profiles

I profiles permettono di avviare selettivamente gruppi di servizi, rendendo il file Compose utilizzabile per diversi scenari senza dover mantenere file separati.

```yaml
services:
  api:
    # Nessun profilo: avviato sempre
    image: myapp/api:latest

  debug-tools:
    profiles:
      - debug
    image: nicolaka/netshoot
    command: sleep infinity

  monitoring:
    profiles:
      - monitoring
    image: prom/prometheus:latest

  test-db:
    profiles:
      - testing
    image: postgres:16-alpine
```

```bash
# Avviare solo i servizi senza profilo
docker compose up

# Avviare includendo i servizi del profilo "debug"
docker compose --profile debug up

# Avviare più profili contemporaneamente
docker compose --profile debug --profile monitoring up
```

### Environment Files

Docker Compose supporta file `.env` per gestire variabili d'ambiente in modo centralizzato, separando la configurazione dal codice.

```yaml
services:
  api:
    env_file:
      - .env
      - .env.local  # Override locale, ignorato da git
    environment:
      - NODE_ENV=production  # Override esplicito
```

```bash
# .env
DATABASE_HOST=db
DATABASE_PORT=5432
REDIS_URL=redis://cache:6379
API_KEY=default-key
```

### Override Files e Configurazioni Dev vs Prod

Il sistema di override permette di sovrapporre configurazioni specifiche per ambiente. Docker Compose carica automaticamente `compose.yaml` e, se presente, `compose.override.yaml`.

```yaml
# compose.yaml - Configurazione base
services:
  api:
    image: myapp/api:latest
    networks:
      - backend

# compose.override.yaml - Sviluppo (caricato automaticamente)
services:
  api:
    build:
      context: ./api
    volumes:
      - ./api/src:/app/src  # Hot reload
    ports:
      - "3000:3000"
      - "9229:9229"  # Debug port
    environment:
      - NODE_ENV=development

# compose.prod.yaml - Produzione (caricato esplicitamente)
services:
  api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: "2.0"
          memory: 1G
    environment:
      - NODE_ENV=production
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
```

```bash
# Sviluppo (usa compose.yaml + compose.override.yaml automaticamente)
docker compose up

# Produzione (sovrascrive con file specifico)
docker compose -f compose.yaml -f compose.prod.yaml up -d
```

---

## Networking Docker

### Tipi di Network

Docker offre diversi driver di rete, ciascuno progettato per casi d'uso specifici.

**Bridge** (default): Rete isolata sul singolo host. I container sulla stessa bridge network possono comunicare tra loro. È il driver predefinito quando si crea un container senza specificare una rete.

**Host**: Il container condivide direttamente lo stack di rete dell'host, eliminando l'isolamento di rete ma offrendo prestazioni massime. Non è necessario il port mapping.

**None**: Disabilita completamente la rete del container. Utile per container che elaborano dati senza necessità di comunicazione di rete.

**Overlay**: Permette la comunicazione tra container su host diversi, fondamentale per Docker Swarm e ambienti distribuiti. Utilizza VXLAN per l'incapsulamento del traffico.

```bash
# Creare reti con driver specifici
docker network create --driver bridge app-network
docker network create --driver overlay --attachable swarm-network
docker network create --driver host host-network
```

### Custom Bridge Network

Le reti bridge personalizzate offrono vantaggi significativi rispetto alla rete bridge predefinita: risoluzione DNS automatica per nome del container, migliore isolamento, e configurazione personalizzabile delle subnet.

```bash
# Creare una rete bridge personalizzata con subnet specifica
docker network create \
  --driver bridge \
  --subnet 172.25.0.0/16 \
  --gateway 172.25.0.1 \
  --ip-range 172.25.1.0/24 \
  --opt com.docker.network.bridge.name=br-custom \
  my-custom-network

# Connettere un container alla rete con IP statico
docker run -d --name api \
  --network my-custom-network \
  --ip 172.25.1.10 \
  myapp/api:latest

# Connettere un container esistente a una seconda rete
docker network connect backend-network api
```

### Risoluzione DNS

All'interno di una rete bridge personalizzata, Docker fornisce un server DNS integrato che risolve i nomi dei container. Ogni container può raggiungere gli altri utilizzando il nome del servizio (in Docker Compose) o il nome del container come hostname.

```bash
# Da un container nella stessa rete, è possibile risolvere per nome
ping api        # Risolve all'IP del container "api"
curl http://db:5432   # Risolve al container "db"
```

In Docker Compose, il DNS risolve automaticamente i nomi dei servizi. Questo permette di configurare le applicazioni con hostname stabili invece di indirizzi IP variabili.

### Port Mapping

Il port mapping mappa le porte del container alle porte dell'host, rendendo i servizi accessibili dall'esterno.

```bash
# Sintassi: -p host_port:container_port
docker run -d -p 8080:80 nginx                  # Mappa porta 80 a 8080
docker run -d -p 127.0.0.1:8080:80 nginx        # Solo localhost
docker run -d -p 8080:80/tcp -p 8080:80/udp nginx  # Protocollo specifico
docker run -d -P nginx                           # Porte casuali per tutte le EXPOSE
```

### Macvlan

Il driver **macvlan** permette di assegnare un indirizzo MAC diretto ai container, facendoli apparire come dispositivi fisici sulla rete. Questo è utile per applicazioni legacy che necessitano di essere direttamente raggiungibili sulla rete LAN.

```bash
docker network create -d macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  -o parent=eth0 \
  macvlan-net

docker run -d --name legacy-app \
  --network macvlan-net \
  --ip 192.168.1.100 \
  legacy-app:latest
```

---

## Storage Docker

### Tipi di Storage

Docker supporta tre meccanismi principali di storage per i dati dei container.

**Named Volumes**: Gestiti interamente da Docker, archiviati in `/var/lib/docker/volumes/`. Sono la soluzione preferita per la persistenza dei dati in produzione poiché offrono portabilità e gestione centralizzata.

```bash
# Creare e utilizzare un named volume
docker volume create pgdata
docker run -d --name postgres \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16-alpine

# Ispezionare un volume
docker volume inspect pgdata
```

**Bind Mounts**: Montano una directory specifica dell'host nel container. Ideali per lo sviluppo locale dove si desidera il live reload del codice sorgente.

```bash
# Bind mount per sviluppo
docker run -d --name dev-api \
  -v $(pwd)/src:/app/src:ro \
  -v $(pwd)/config:/app/config \
  myapp/api:dev
```

**tmpfs Mounts**: Storage in memoria volatile che non persiste dopo l'arresto del container. Utile per dati sensibili temporanei come secret o cache di sessione.

```bash
docker run -d --name secure-app \
  --tmpfs /app/tmp:rw,size=100m,mode=1777 \
  --tmpfs /run/secrets:ro,size=1m \
  myapp:latest
```

### Volume Drivers

I volume driver permettono di utilizzare backend di storage remoti o specializzati. Esistono driver per NFS, AWS EBS, Azure File Storage e altri sistemi.

```bash
# Volume con driver NFS
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.1.50,rw,nfsvers=4 \
  --opt device=:/export/data \
  nfs-data

# Utilizzo in compose.yaml
volumes:
  shared-data:
    driver: local
    driver_opts:
      type: nfs
      o: "addr=192.168.1.50,rw,nfsvers=4"
      device: ":/export/data"
```

### Backup dei Volumi

Il backup dei volumi Docker è un'operazione critica per la protezione dei dati. La strategia più comune utilizza un container temporaneo per accedere al volume e creare un archivio.

```bash
# Backup di un volume
docker run --rm \
  -v pgdata:/source:ro \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/pgdata-$(date +%Y%m%d-%H%M%S).tar.gz -C /source .

# Restore di un volume
docker run --rm \
  -v pgdata:/target \
  -v $(pwd)/backups:/backup:ro \
  alpine sh -c "cd /target && tar xzf /backup/pgdata-20240115-120000.tar.gz"
```

### Pattern di Persistenza dei Dati

Per i database in produzione, è fondamentale utilizzare named volumes con backup regolari. Per i file di configurazione, i bind mount in sola lettura (`:ro`) garantiscono che il container non possa modificare accidentalmente la configurazione dell'host. Per le cache applicative, i tmpfs mount offrono prestazioni elevate senza impatto sullo storage persistente.

```yaml
services:
  db:
    image: postgres:16-alpine
    volumes:
      - db-data:/var/lib/postgresql/data        # Dati persistenti
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro  # Config read-only
    tmpfs:
      - /tmp:size=256m                           # Cache volatile
```

---

## Registry

### Docker Hub e GitHub Container Registry (GHCR)

Docker Hub rimane il registry pubblico più diffuso, con milioni di immagini disponibili. GitHub Container Registry (GHCR) si integra nativamente con GitHub Actions e supporta la gestione dei permessi tramite il sistema di autorizzazione di GitHub.

```bash
# Login a Docker Hub
docker login

# Login a GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Push su GHCR
docker tag myapp:latest ghcr.io/username/myapp:latest
docker push ghcr.io/username/myapp:latest
```

### Registry Privato con Harbor

Harbor è una soluzione open-source per registry privati che offre funzionalità enterprise: vulnerability scanning, policy di replica, gestione dei ruoli, audit logging e conformità.

```yaml
# Installazione Harbor tramite Helm (semplificata)
# harbor-values.yaml
expose:
  type: ingress
  tls:
    enabled: true
    certSource: secret
  ingress:
    hosts:
      core: registry.example.com
persistence:
  enabled: true
  persistentVolumeClaim:
    registry:
      size: 100Gi
    database:
      size: 10Gi
trivy:
  enabled: true
```

### Strategia di Tagging Semver

Una strategia di tagging coerente basata su semantic versioning è essenziale per la tracciabilità e il rollback delle release.

```bash
# Strategia di tagging raccomandata
docker tag myapp:build-${CI_COMMIT_SHA} myapp:1.2.3
docker tag myapp:build-${CI_COMMIT_SHA} myapp:1.2
docker tag myapp:build-${CI_COMMIT_SHA} myapp:1
docker tag myapp:build-${CI_COMMIT_SHA} myapp:latest

# Tags aggiuntivi per tracciabilità
docker tag myapp:build-${CI_COMMIT_SHA} myapp:sha-${CI_COMMIT_SHA:0:8}
docker tag myapp:build-${CI_COMMIT_SHA} myapp:build-${CI_PIPELINE_ID}
```

La convenzione prevede che `latest` punti sempre all'ultima release stabile, i tag `major.minor.patch` siano immutabili, e i tag `major.minor` e `major` puntino all'ultima patch della rispettiva versione.

### Scanning con Trivy

Trivy è uno scanner di vulnerabilità completo per immagini Docker, filesystem e repository. Si integra facilmente nelle pipeline CI/CD per bloccare il deployment di immagini con vulnerabilità critiche.

```bash
# Scansione di un'immagine locale
trivy image myapp:latest

# Scansione con severità specifica e formato strutturato
trivy image --severity HIGH,CRITICAL --format json --output report.json myapp:latest

# Scansione con exit code per pipeline CI (fallisce se trova vulnerabilità critiche)
trivy image --exit-code 1 --severity CRITICAL myapp:latest

# Scansione di un Dockerfile per misconfigurations
trivy config ./Dockerfile
```

---

## Sicurezza Docker

### Rootless Docker

Docker rootless permette di eseguire il daemon Docker e i container senza privilegi di root, riducendo significativamente la superficie di attacco. In caso di escape dal container, l'attaccante otterrebbe solo i privilegi di un utente non-root.

```bash
# Installazione rootless Docker
dockerd-rootless-setuptool.sh install

# Verificare la modalità rootless
docker info --format '{{.SecurityOptions}}'

# Configurazione del socket utente
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock
```

### Read-Only Filesystem

Montare il filesystem del container in sola lettura impedisce modifiche non autorizzate ai file del sistema. Le directory che necessitano di scrittura possono essere montate specificamente come tmpfs.

```bash
docker run -d --name secure-api \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  --tmpfs /var/run:rw,size=10m \
  myapp/api:latest
```

### Capability Dropping

Linux capabilities permettono un controllo granulare dei privilegi. Rimuovere tutte le capabilities e aggiungere solo quelle strettamente necessarie implementa il principio del minimo privilegio.

```bash
# Rimuovere tutte le capabilities e aggiungere solo quelle necessarie
docker run -d \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --cap-add CHOWN \
  --cap-add SETUID \
  --cap-add SETGID \
  myapp/api:latest
```

In Docker Compose:

```yaml
services:
  api:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
```

### Profili Seccomp

Seccomp (Secure Computing Mode) filtra le system call che un container può effettuare. Docker applica un profilo seccomp predefinito che blocca circa 44 system call pericolose, ma è possibile creare profili personalizzati per un isolamento più stretto.

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "fstat",
                "mmap", "mprotect", "munmap", "brk", "exit_group"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

```bash
docker run --security-opt seccomp=custom-profile.json myapp:latest
```

### AppArmor

AppArmor fornisce un livello aggiuntivo di controllo degli accessi obbligatorio (MAC). Docker carica automaticamente un profilo AppArmor predefinito (`docker-default`) che limita le operazioni del container.

```bash
# Verificare il profilo AppArmor attivo
docker inspect --format='{{.HostConfig.SecurityOpt}}' container_name

# Eseguire con un profilo AppArmor personalizzato
docker run --security-opt apparmor=my-custom-profile myapp:latest

# Disabilitare AppArmor (sconsigliato in produzione)
docker run --security-opt apparmor=unconfined myapp:latest
```

### Docker Content Trust (DCT)

DCT utilizza firme digitali per verificare l'integrità e la provenienza delle immagini Docker. Quando abilitato, Docker verifica le firme prima di eseguire pull o run di immagini.

```bash
# Abilitare DCT globalmente
export DOCKER_CONTENT_TRUST=1

# Firmare e pushare un'immagine
docker push myregistry.example.com/myapp:1.0.0
# Docker chiederà una passphrase per la chiave di firma

# Verificare le firme di un'immagine
docker trust inspect --pretty myregistry.example.com/myapp:1.0.0
```

### Image Scanning e CIS Benchmark

L'image scanning dovrebbe essere integrato nella pipeline CI/CD come gate obbligatorio. Il CIS Docker Benchmark fornisce una checklist completa di sicurezza per la configurazione dell'host Docker, del daemon, delle immagini e dei container.

```bash
# Eseguire Docker Bench Security (basato su CIS Benchmark)
docker run --rm --net host --pid host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /etc:/etc:ro \
  -v /usr/lib/systemd:/usr/lib/systemd:ro \
  -v /var/lib/docker:/var/lib/docker:ro \
  docker/docker-bench-security

# Scansione integrata con Scout
docker scout cves myapp:latest
docker scout recommendations myapp:latest
```

---

## Orchestrazione

### Docker Swarm

Docker Swarm è la soluzione di orchestrazione nativa integrata in Docker. Trasforma un gruppo di host Docker in un singolo cluster virtuale, gestendo deployment, scaling, load balancing e service discovery.

```bash
# Inizializzare lo Swarm
docker swarm init --advertise-addr 192.168.1.10

# Aggiungere worker nodes
docker swarm join-token worker

# Creare un servizio
docker service create \
  --name api \
  --replicas 3 \
  --publish published=8080,target=3000 \
  --update-delay 10s \
  --update-parallelism 1 \
  --rollback-parallelism 1 \
  --rollback-monitor 30s \
  myapp/api:latest

# Scaling del servizio
docker service scale api=5

# Rolling update
docker service update --image myapp/api:v2 api
```

Stack deployment con file Compose:

```yaml
# stack.yaml
services:
  api:
    image: myapp/api:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      rollback_config:
        parallelism: 1
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      placement:
        constraints:
          - node.role == worker
          - node.labels.zone == eu-west-1a
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
    networks:
      - app-network

networks:
  app-network:
    driver: overlay
    encrypted: true
```

```bash
docker stack deploy -c stack.yaml myapp
```

### Confronto con Kubernetes

Docker Swarm e Kubernetes risolvono problemi simili ma con filosofie diverse. Swarm è integrato in Docker, più semplice da configurare e ideale per ambienti medio-piccoli. Kubernetes offre un ecosistema più ricco, maggiore flessibilità, auto-scaling avanzato e un modello dichiarativo più sofisticato, rendendolo la scelta standard per ambienti enterprise e cloud-native su larga scala.

| Caratteristica | Docker Swarm | Kubernetes |
|---|---|---|
| Setup | Semplice (integrato in Docker) | Complesso (cluster dedicato) |
| Curva di apprendimento | Bassa | Alta |
| Scaling | Manuale o basato su regole semplici | Horizontal Pod Autoscaler, VPA, KEDA |
| Networking | Overlay nativo | CNI plugin (Calico, Cilium, Flannel) |
| Service Discovery | DNS integrato | CoreDNS + Service objects |
| Storage | Volume driver limitati | CSI drivers, StorageClass, PV/PVC |
| Ecosistema | Limitato | Vastissimo (Helm, Operators, CRDs) |
| Adatto per | Piccoli/medi deployment | Enterprise, microservizi complessi |

---

## Performance

### Limiti di Risorse CPU e Memoria

Configurare limiti di risorse è essenziale per prevenire che un singolo container monopolizzi le risorse dell'host e per garantire un comportamento prevedibile in produzione.

```bash
# Limiti CPU e memoria via CLI
docker run -d \
  --cpus="1.5" \
  --cpu-shares=512 \
  --memory=512m \
  --memory-swap=1g \
  --memory-reservation=256m \
  --pids-limit=100 \
  myapp:latest
```

```yaml
# In Docker Compose
services:
  api:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 256M
    # Alternativa legacy (non-Swarm)
    mem_limit: 1g
    cpus: 2.0
```

### Logging Drivers

Docker supporta diversi driver di logging per gestire l'output dei container. La scelta del driver influisce sulle prestazioni e sulla capacità di analisi dei log.

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3",
    "compress": "true"
  }
}
```

I driver principali includono: `json-file` (default, locale), `syslog` (integrazione con syslog dell'host), `journald` (integrazione con systemd), `fluentd` (forwarding a Fluentd/Fluent Bit), `gelf` (Graylog Extended Log Format), e `awslogs` (AWS CloudWatch). Per ambienti ad alto throughput, il driver `local` ottimizzato offre prestazioni migliori di `json-file`.

```yaml
services:
  api:
    logging:
      driver: fluentd
      options:
        fluentd-address: "localhost:24224"
        fluentd-async: "true"
        tag: "docker.{{.Name}}"
```

### Storage Driver overlay2

`overlay2` è lo storage driver raccomandato per la maggior parte degli ambienti. Utilizza OverlayFS per gestire i layer delle immagini in modo efficiente, con prestazioni eccellenti sia in lettura che in scrittura.

```bash
# Verificare lo storage driver attivo
docker info | grep "Storage Driver"

# Configurazione ottimizzata in daemon.json
{
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}
```

### Build Cache e BuildKit

BuildKit è il builder di nuova generazione che offre miglioramenti significativi: build paralleli, mount cache, secret sicuri durante il build e output strutturato.

```bash
# Abilitare BuildKit
export DOCKER_BUILDKIT=1

# Build con cache esportabile
docker buildx build \
  --cache-from type=registry,ref=myregistry.com/myapp:buildcache \
  --cache-to type=registry,ref=myregistry.com/myapp:buildcache,mode=max \
  -t myapp:latest .

# Utilizzare mount cache nel Dockerfile
# syntax=docker/dockerfile:1
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production
COPY . .
RUN npm run build
```

---

## Monitoraggio Container

### cAdvisor

cAdvisor (Container Advisor) è uno strumento open-source di Google che raccoglie metriche di utilizzo delle risorse e caratteristiche prestazionali dei container in esecuzione. Espone le metriche in formato Prometheus, rendendolo ideale come source per dashboard Grafana.

```yaml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "8081:8080"
    privileged: true
    devices:
      - /dev/kmsg
```

### Prometheus e Node Exporter

Prometheus raccoglie metriche dai target configurati tramite scraping HTTP. In combinazione con cAdvisor e Node Exporter, fornisce una visione completa delle metriche sia a livello container sia a livello host.

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=30d"

  node-exporter:
    image: prom/node-exporter:latest
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - "--path.procfs=/host/proc"
      - "--path.rootfs=/rootfs"
      - "--path.sysfs=/host/sys"
    pid: host
```

Configurazione Prometheus per lo scraping:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "cadvisor"
    static_configs:
      - targets: ["cadvisor:8080"]

  - job_name: "node-exporter"
    static_configs:
      - targets: ["node-exporter:9100"]

  - job_name: "docker"
    static_configs:
      - targets: ["host.docker.internal:9323"]
```

### Metriche dei Container e Health Check

Le metriche fondamentali da monitorare per ogni container includono: utilizzo CPU e memoria, I/O su disco e rete, numero di restart, stato degli health check e tempo di uptime.

```bash
# Monitorare le risorse in tempo reale
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Verificare lo stato degli health check
docker inspect --format='{{json .State.Health}}' container_name | jq .
```

Per implementare alerting basato sugli health check:

```yaml
# Alert rule per Prometheus (Alertmanager)
groups:
  - name: container_alerts
    rules:
      - alert: ContainerUnhealthy
        expr: engine_daemon_health_checks_failed_total > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container unhealthy"

      - alert: ContainerHighCPU
        expr: rate(container_cpu_usage_seconds_total[5m]) > 0.8
        for: 10m
        labels:
          severity: critical
```

---

## Docker in CI/CD

### GitHub Actions con docker/build-push-action

L'action `docker/build-push-action` è lo standard per build e push di immagini Docker nelle pipeline GitHub Actions. Supporta multi-platform build, caching avanzato e integrazione con diversi registry.

```yaml
# .github/workflows/docker-publish.yml
name: Build and Push Docker Image

on:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata (tags, labels)
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha,prefix=sha-
            type=ref,event=branch
            type=ref,event=pr

      - name: Build and push Docker image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64
```

### Layer Caching in CI

Il caching dei layer nelle pipeline CI riduce significativamente i tempi di build. Le strategie principali includono GitHub Actions cache, registry cache e cache locale.

```yaml
# Cache con GitHub Actions (GHA)
- uses: docker/build-push-action@v6
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max

# Cache su registry esterno
- uses: docker/build-push-action@v6
  with:
    cache-from: type=registry,ref=ghcr.io/org/app:buildcache
    cache-to: type=registry,ref=ghcr.io/org/app:buildcache,mode=max

# Cache locale (utile per runner self-hosted)
- uses: docker/build-push-action@v6
  with:
    cache-from: type=local,src=/tmp/.buildx-cache
    cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max
```

### Multi-Platform Builds con Buildx

Docker Buildx permette di creare immagini per architetture multiple (amd64, arm64, armv7) in un singolo comando. Questo è fondamentale per supportare ambienti eterogenei e deployment su piattaforme diverse come AWS Graviton, Apple Silicon o dispositivi IoT.

```bash
# Creare un builder multi-piattaforma
docker buildx create --name multiplatform --use --bootstrap

# Build multi-piattaforma con push diretto al registry
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag ghcr.io/org/myapp:latest \
  --push .

# Ispezionare un'immagine multi-piattaforma
docker buildx imagetools inspect ghcr.io/org/myapp:latest
```

Nel Dockerfile, è possibile utilizzare variabili automatiche per adattare il build all'architettura target:

```dockerfile
FROM --platform=$BUILDPLATFORM golang:1.22-alpine AS builder
ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH

WORKDIR /app
COPY . .
RUN GOOS=${TARGETOS} GOARCH=${TARGETARCH} go build -o /app/server

FROM alpine:3.19
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]
```

### Testcontainers

Testcontainers è una libreria che permette di avviare container Docker come dipendenze durante l'esecuzione dei test. Elimina la necessità di servizi mock fornendo istanze reali di database, message broker e altri servizi.

```java
// Esempio Java con JUnit 5
@Testcontainers
class UserRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Test
    void shouldPersistUser() {
        // Test con database PostgreSQL reale
    }
}
```

```python
# Esempio Python con pytest
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="module")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres

def test_database_connection(postgres_container):
    connection_url = postgres_container.get_connection_url()
    # Test con database PostgreSQL reale
    assert connection_url is not None
```

---

## Best Practices

Le seguenti dieci best practice rappresentano le linee guida fondamentali per l'utilizzo efficace di Docker in ambienti di produzione.

### 1. Utilizzare Immagini Base Specifiche e Minimali

Evitare il tag `latest` e preferire tag specifici con versione. Utilizzare varianti `alpine`, `slim` o `distroless` per ridurre la superficie di attacco e la dimensione dell'immagine. Un'immagine più piccola significa meno vulnerabilità potenziali, tempi di pull più rapidi e minor utilizzo di banda e storage.

```dockerfile
# Evitare
FROM python:latest

# Preferire
FROM python:3.12-slim-bookworm
```

### 2. Implementare Multi-Stage Builds

Separare l'ambiente di build dall'ambiente di runtime. Questo elimina compilatori, header di sviluppo e dipendenze di build dall'immagine finale, riducendo la dimensione anche del 90% in alcuni casi.

### 3. Eseguire Come Utente Non-Root

Creare un utente dedicato nel Dockerfile e utilizzare l'istruzione `USER` per eseguire l'applicazione con privilegi minimi. Questo limita l'impatto di eventuali vulnerabilità di escape dal container e rispetta il principio del minimo privilegio.

### 4. Scansionare le Immagini per Vulnerabilità

Integrare strumenti come Trivy, Snyk o Docker Scout nella pipeline CI/CD per identificare vulnerabilità note nelle dipendenze e nell'immagine base. Bloccare automaticamente il deployment di immagini con vulnerabilità critiche non risolte.

### 5. Un Processo per Container

Ogni container dovrebbe eseguire un singolo processo o servizio con una responsabilità specifica. Questo facilita lo scaling orizzontale, il monitoraggio, il debugging e rispetta i principi dei microservizi. Se servono più processi, utilizzare Docker Compose per orchestrare container separati.

### 6. Utilizzare .dockerignore

Escludere dal build context file non necessari come `.git`, `node_modules`, file di log e credenziali. Questo accelera il build, riduce il rischio di includere dati sensibili e previene l'invalidazione non necessaria della cache.

### 7. Implementare Health Check

Definire `HEALTHCHECK` in ogni Dockerfile di produzione per permettere a Docker e agli orchestratori di verificare lo stato effettivo dell'applicazione. Configurare intervalli appropriati e condizioni di fallimento per abilitare il self-healing automatico.

### 8. Gestire i Secret in Modo Sicuro

Non includere mai secret (password, API key, certificati) nelle immagini Docker o nelle variabili d'ambiente del Dockerfile. Utilizzare Docker secrets, mount di file temporanei, o soluzioni dedicate come HashiCorp Vault per iniettare i secret a runtime.

```dockerfile
# ERRATO: secret nel Dockerfile
ENV API_KEY=sk-12345

# CORRETTO: utilizzare BuildKit secrets
RUN --mount=type=secret,id=api_key \
    cat /run/secrets/api_key > /app/.env
```

### 9. Configurare Limiti di Risorse

Definire sempre limiti di CPU e memoria per ogni container in produzione. Questo previene che un container malfunzionante consumi tutte le risorse dell'host, causando un effetto a catena su tutti gli altri servizi. Configurare anche i `restart_policy` appropriati per garantire la resilienza.

### 10. Applicare Labeling e Tagging Coerente

Utilizzare label standardizzate (seguendo le convenzioni OCI) per tracciare build date, version, VCS reference e maintainer. Implementare una strategia di tagging semver coerente e non affidarsi mai esclusivamente al tag `latest`.

```dockerfile
LABEL org.opencontainers.image.title="My Application"
LABEL org.opencontainers.image.version="1.2.3"
LABEL org.opencontainers.image.created="2026-03-28T10:00:00Z"
LABEL org.opencontainers.image.source="https://github.com/org/repo"
LABEL org.opencontainers.image.description="Production API service"
```

---

## BuildKit Avanzato

BuildKit è il motore di build di nuova generazione che ha rivoluzionato il processo di costruzione delle immagini Docker. A partire da Docker 23.0, BuildKit è il builder predefinito, ma le sue funzionalità avanzate meritano un approfondimento dedicato che va oltre l'uso basilare delle mount cache già introdotto nelle sezioni precedenti.

### Cache Mounts Avanzati

Le cache mounts di BuildKit permettono di persistere directory di cache tra build successive, eliminando il download ripetuto di dipendenze. Esistono diversi tipi di mount, ciascuno con semantica specifica.

**`type=cache`** — Directory cache persistente tra build. Il contenuto sopravvive ai singoli build e viene condiviso tra build concorrenti. Il parametro `sharing` controlla il comportamento in caso di accesso concorrente: `shared` (default, accesso simultaneo), `private` (copia privata per ogni build), `locked` (accesso serializzato con lock esclusivo).

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

# Cache persistente per pip con sharing locked per evitare corruzione
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install --user -r requirements.txt

# Cache per apt-get con identificatore univoco
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*
```

**`type=bind`** — Monta file o directory dal build context in sola lettura (default) o lettura-scrittura. A differenza di `COPY`, non crea un layer, riducendo la dimensione dell'immagine quando i file servono solo temporaneamente durante il build.

```dockerfile
# Bind mount per evitare COPY di file temporanei
RUN --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=package-lock.json,target=package-lock.json \
    --mount=type=cache,target=/root/.npm \
    npm ci --only=production
```

**`type=tmpfs`** — Monta un filesystem temporaneo in memoria. Utile per operazioni che producono file temporanei pesanti che non devono persistere nel layer finale.

```dockerfile
# tmpfs per compilazione con file temporanei pesanti
RUN --mount=type=tmpfs,target=/tmp/build \
    gcc -o /app/server main.c -L/tmp/build
```

Per applicazioni multi-linguaggio, è possibile combinare più cache mounts in un singolo `RUN` per ottimizzare contemporaneamente diversi gestori di pacchetti:

```dockerfile
FROM node:20-alpine

RUN --mount=type=cache,target=/root/.npm,id=npm-cache \
    --mount=type=cache,target=/root/.cache/yarn,id=yarn-cache \
    --mount=type=cache,target=/app/.next/cache,id=nextjs-cache \
    npm ci && npm run build
```

### SSH Forwarding nel Build

BuildKit supporta il forwarding dell'agente SSH durante il build, permettendo di clonare repository privati senza esporre chiavi SSH nell'immagine. Questo è fondamentale per build che dipendono da moduli privati su GitHub, GitLab o Bitbucket.

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:1.22-alpine AS builder
WORKDIR /app

# Configurare git per usare SSH invece di HTTPS
RUN apk add --no-cache git openssh-client && \
    mkdir -p /root/.ssh && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts

# Clonare repository privati usando l'agente SSH dell'host
RUN --mount=type=ssh \
    git clone git@github.com:org/private-module.git /app/deps/private-module

# Scaricare moduli Go privati usando l'agente SSH
RUN --mount=type=ssh \
    GOPRIVATE=github.com/org/* go mod download

COPY . .
RUN CGO_ENABLED=0 go build -o /app/server
```

Per utilizzare SSH forwarding durante il build, è necessario passare il socket SSH come argomento:

```bash
# Build con SSH agent forwarding
docker buildx build --ssh default=$SSH_AUTH_SOCK -t myapp:latest .

# Per chiavi SSH specifiche (non dall'agent)
docker buildx build --ssh default=~/.ssh/id_ed25519 -t myapp:latest .

# Per repository privati npm con SSH
docker buildx build \
  --ssh default=$SSH_AUTH_SOCK \
  --secret id=npmrc,src=$HOME/.npmrc \
  -t myapp:latest .
```

La chiave SSH non viene mai scritta in un layer dell'immagine. Il mount `type=ssh` rende disponibile il socket dell'agente SSH solo durante l'esecuzione del comando `RUN` specifico, eliminando il rischio di leak delle credenziali.

### Secret Mounts

I secret mounts permettono di iniettare dati sensibili durante il build senza includerli nei layer dell'immagine. Questo è il metodo consigliato per gestire token, credenziali di registry e chiavi API durante la fase di build.

```dockerfile
# syntax=docker/dockerfile:1

FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./

# Utilizzare un token npm privato senza esporlo nei layer
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci --only=production

# Utilizzare credenziali per un registry privato
RUN --mount=type=secret,id=pip_conf,target=/etc/pip.conf \
    pip install -r requirements.txt

# Accedere a un secret come variabile d'ambiente
RUN --mount=type=secret,id=api_token \
    export API_TOKEN=$(cat /run/secrets/api_token) && \
    ./configure --token="$API_TOKEN"
```

```bash
# Passare i secret durante il build
docker buildx build \
  --secret id=npmrc,src=$HOME/.npmrc \
  --secret id=api_token,env=MY_API_TOKEN \
  -t myapp:latest .
```

### Heredocs nei Dockerfile

A partire dalla sintassi `docker/dockerfile:1.4`, BuildKit supporta gli heredoc (here-documents) nei Dockerfile. Questa funzionalità permette di scrivere script multi-linea inline e creare file direttamente nel Dockerfile senza concatenare comandi con `&&` e `\`.

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.12-slim

# Creare file di configurazione inline con heredoc
COPY <<EOF /app/config.yaml
server:
  host: 0.0.0.0
  port: 8080
  workers: 4
logging:
  level: info
  format: json
EOF

# Script multi-linea senza concatenazione
RUN <<EOF
apt-get update
apt-get install -y --no-install-recommends \
  build-essential \
  libpq-dev \
  curl
rm -rf /var/lib/apt/lists/*
EOF

# Heredoc con interprete specifico
RUN <<PYTHON python3
import json
import os

config = {
    "database": os.environ.get("DB_URL", "sqlite:///app.db"),
    "debug": False
}

with open("/app/settings.json", "w") as f:
    json.dump(config, f, indent=2)

print("Configuration generated")
PYTHON

# Multipli heredoc in una singola istruzione COPY
COPY <<entrypoint.sh /usr/local/bin/entrypoint.sh
#!/bin/sh
set -e
echo "Starting application..."
exec "$@"
entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]
```

Gli heredoc eliminano la necessità di file di script esterni per operazioni semplici, riducendo il numero di file nel build context e migliorando la leggibilità del Dockerfile. Tuttavia, per script complessi è ancora preferibile utilizzare file separati per facilitare il testing e la manutenzione.

### Build Multi-Piattaforma con QEMU

Docker Buildx utilizza QEMU per emulare architetture diverse da quella dell'host, permettendo di costruire immagini per ARM su macchine x86_64 e viceversa. Questo è fondamentale per supportare AWS Graviton (arm64), Apple Silicon (arm64), Raspberry Pi (arm/v7), e dispositivi IoT.

```bash
# Registrare gli handler QEMU per l'emulazione cross-platform
docker run --privileged --rm tonistiigi/binfmt --install all

# Verificare le piattaforme supportate
docker buildx ls

# Creare un builder dedicato con supporto multi-piattaforma
docker buildx create \
  --name multi-builder \
  --driver docker-container \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --use --bootstrap

# Build con emulazione QEMU
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ghcr.io/org/myapp:latest \
  --push .
```

L'emulazione QEMU introduce un overhead prestazionale significativo (da 5x a 20x più lento rispetto ai build nativi) per operazioni CPU-intensive come la compilazione. Per mitigare questo problema, esistono strategie avanzate:

**Cross-compilation nativa** — Per linguaggi che supportano la cross-compilation (Go, Rust, Zig), è possibile compilare nativamente sull'architettura dell'host e copiare il binario nell'immagine target:

```dockerfile
# syntax=docker/dockerfile:1

# Stage di build: esegue SEMPRE sull'architettura dell'host (nativa, veloce)
FROM --platform=$BUILDPLATFORM golang:1.22-alpine AS builder

ARG TARGETOS
ARG TARGETARCH

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .

# Cross-compilazione nativa: Go compila per l'architettura target
# senza emulazione QEMU — molto più veloce
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -ldflags="-s -w" -o /app/server ./cmd/server

# Stage runtime: usa l'architettura target
FROM alpine:3.20
RUN apk --no-cache add ca-certificates tzdata
COPY --from=builder /app/server /usr/local/bin/server
USER 65534:65534
ENTRYPOINT ["server"]
```

**Builder farm con nodi nativi** — Per build ad alte prestazioni, è possibile configurare un cluster di builder con nodi per ogni architettura:

```bash
# Creare builder con nodi remoti per ogni architettura
docker buildx create --name farm --platform linux/amd64 \
  --node amd64-node ssh://builder-amd64.internal

docker buildx create --name farm --append --platform linux/arm64 \
  --node arm64-node ssh://builder-arm64.internal

docker buildx use farm

# Ogni architettura compila nativamente sul proprio nodo
docker buildx build --platform linux/amd64,linux/arm64 \
  --tag myregistry.com/app:latest --push .
```

### Build Cache Avanzata con Backend Remoti

BuildKit supporta diversi backend per la cache di build, permettendo la condivisione della cache tra diverse macchine CI e sviluppatori:

```bash
# Cache su registry OCI (consigliato per CI/CD)
docker buildx build \
  --cache-from type=registry,ref=ghcr.io/org/app:buildcache \
  --cache-to type=registry,ref=ghcr.io/org/app:buildcache,mode=max \
  -t myapp:latest .

# Cache su S3 (per team con infrastruttura AWS)
docker buildx build \
  --cache-from type=s3,region=eu-west-1,bucket=build-cache,name=myapp \
  --cache-to type=s3,region=eu-west-1,bucket=build-cache,name=myapp,mode=max \
  -t myapp:latest .

# Cache su Azure Blob Storage
docker buildx build \
  --cache-from type=azblob,account_url=https://myaccount.blob.core.windows.net,name=myapp \
  --cache-to type=azblob,account_url=https://myaccount.blob.core.windows.net,name=myapp,mode=max \
  -t myapp:latest .

# Cache locale con export/import (utile per self-hosted runners)
docker buildx build \
  --cache-from type=local,src=/tmp/buildcache \
  --cache-to type=local,dest=/tmp/buildcache,mode=max \
  -t myapp:latest .
```

Il parametro `mode=max` esporta la cache di tutti gli stage intermedi, non solo dello stage finale. Questo aumenta la dimensione della cache ma massimizza i cache hit nei build successivi, particolarmente utile quando gli stage intermedi contengono operazioni costose come la compilazione di dipendenze.

---

## Docker Compose v2 Avanzato

Docker Compose v2 è stato riscritto in Go come plugin del CLI Docker (`docker compose` senza trattino), sostituendo la versione Python originale (`docker-compose`). La specifica Compose v5.0.0 (rilasciata a fine 2025) introduce funzionalità avanzate per lo sviluppo locale e il deployment in produzione.

### Profiles Avanzati

I profiles permettono di definire gruppi di servizi attivabili selettivamente. Questa funzionalità è stata introdotta nelle sezioni precedenti, ma esistono pattern avanzati per gestire ambienti complessi con dipendenze condizionali tra profili.

```yaml
# compose.yaml — Profili avanzati con dipendenze
name: microservices-platform

services:
  # Servizio core — sempre attivo (nessun profilo)
  api:
    build: ./api
    ports:
      - "3000:3000"
    depends_on:
      db:
        condition: service_healthy

  # Database — sempre attivo
  db:
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 5s
      timeout: 3s
      retries: 5

  # Worker per elaborazione asincrona
  worker:
    profiles: ["workers"]
    build: ./worker
    depends_on:
      - api
      - redis

  # Redis — necessario solo quando i workers sono attivi
  redis:
    profiles: ["workers"]
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  # Stack di debug
  debug-proxy:
    profiles: ["debug"]
    image: mitmproxy/mitmproxy:latest
    command: mitmweb --web-host 0.0.0.0
    ports:
      - "8081:8081"

  # Stack di osservabilità
  prometheus:
    profiles: ["observability"]
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro

  grafana:
    profiles: ["observability"]
    image: grafana/grafana:latest
    depends_on:
      - prometheus
    ports:
      - "3001:3000"

  # Testing — database isolato per i test
  test-db:
    profiles: ["testing"]
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: test_db
    tmpfs:
      - /var/lib/postgresql/data

  # Load testing
  k6:
    profiles: ["loadtest"]
    image: grafana/k6:latest
    volumes:
      - ./tests/load:/scripts:ro
    command: run /scripts/scenario.js
```

```bash
# Ambiente di sviluppo con workers e debug
docker compose --profile workers --profile debug up

# Ambiente di test con database isolato
docker compose --profile testing up

# Ambiente di produzione con osservabilità
docker compose --profile workers --profile observability up -d

# Eseguire load test una tantum
docker compose run --rm --profile loadtest k6
```

I profili possono anche essere attivati tramite variabile d'ambiente `COMPOSE_PROFILES`, utile per l'integrazione con script CI/CD:

```bash
export COMPOSE_PROFILES=workers,observability
docker compose up -d
```

### Watch Mode e Develop

La direttiva `develop` (precedentemente `x-develop`) con `watch` permette di monitorare i file locali e reagire automaticamente alle modifiche durante lo sviluppo. Questa funzionalità elimina la necessità di riavviare manualmente i container dopo ogni modifica al codice.

Esistono tre azioni possibili quando un file cambia:

- **`sync`** — Sincronizza il file modificato direttamente nel container in esecuzione, senza ricostruire l'immagine. Ideale per file interpretati (HTML, CSS, JS, Python).
- **`rebuild`** — Ricostruisce e ricrea il container. Necessario quando cambiano file che richiedono una fase di compilazione (Dockerfile, dipendenze).
- **`sync+restart`** — Sincronizza il file e riavvia il servizio nel container. Utile per file di configurazione che richiedono il riavvio del processo applicativo.

```yaml
services:
  frontend:
    build:
      context: ./frontend
      target: development
    ports:
      - "5173:5173"
    develop:
      watch:
        # Sincronizzazione hot-reload per file sorgente
        - action: sync
          path: ./frontend/src
          target: /app/src
          ignore:
            - "**/*.test.ts"
            - "**/*.spec.ts"
            - "__tests__/"

        # Rebuild completo quando cambiano le dipendenze
        - action: rebuild
          path: ./frontend/package.json

        # Rebuild quando il Dockerfile cambia
        - action: rebuild
          path: ./frontend/Dockerfile

        # Sync + restart per file di configurazione
        - action: sync+restart
          path: ./frontend/vite.config.ts
          target: /app/vite.config.ts

  api:
    build:
      context: ./api
      target: development
    ports:
      - "3000:3000"
    develop:
      watch:
        # Sync sorgenti Python (hot-reload via uvicorn --reload)
        - action: sync
          path: ./api/src
          target: /app/src
          ignore:
            - "**/__pycache__/"
            - "**/*.pyc"

        # Sync + restart per cambi alla configurazione
        - action: sync+restart
          path: ./api/config
          target: /app/config

        # Rebuild per dipendenze
        - action: rebuild
          path: ./api/requirements.txt

        # Rebuild per cambi al Dockerfile
        - action: rebuild
          path: ./api/Dockerfile
```

```bash
# Avviare in modalità watch (monitora e reagisce ai cambiamenti)
docker compose watch

# Watch con output dei log
docker compose watch --no-up
docker compose up --watch

# Watch con profili specifici
docker compose --profile debug watch
```

A partire dalla versione Compose 2.30.0, è disponibile il parametro `initial_sync: true` che sincronizza tutti i file dal percorso `path` al container immediatamente all'avvio, prima di iniziare il monitoraggio dei cambiamenti. Questo garantisce che il container parta sempre con il codice più aggiornato.

### Include: Composizione Modulare

La direttiva `include` permette di suddividere configurazioni Compose complesse in file modulari riutilizzabili. Questo è fondamentale per architetture a microservizi dove ogni team gestisce il proprio file Compose.

```yaml
# compose.yaml — File principale che include moduli
name: ecommerce-platform

include:
  # Include di un file Compose locale
  - path: ./services/auth/compose.yaml
    project_directory: ./services/auth
    env_file: ./services/auth/.env

  # Include di un file Compose da un sottomodulo git
  - path: ./services/payments/compose.yaml
    project_directory: ./services/payments

  # Include condizionale con override
  - path: ./infra/monitoring/compose.yaml

services:
  gateway:
    build: ./gateway
    ports:
      - "8080:8080"
    depends_on:
      - auth-service    # Definito in services/auth/compose.yaml
      - payment-service # Definito in services/payments/compose.yaml
```

```yaml
# services/auth/compose.yaml — Modulo autonomo
services:
  auth-service:
    build: .
    environment:
      - JWT_SECRET=${JWT_SECRET}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
      interval: 10s
      timeout: 3s
      retries: 3

  auth-db:
    image: postgres:16-alpine
    volumes:
      - auth-data:/var/lib/postgresql/data

volumes:
  auth-data:
```

**Nota di sicurezza:** La CVE-2025-62725 ha rivelato una vulnerabilità di path traversal quando `include` viene usato con artefatti OCI. Aggiornare a Docker Compose v2.40.2 o superiore per la correzione.

### Secrets in Compose

Docker Compose supporta la gestione dei secret per evitare l'inclusione di credenziali in chiaro nei file di configurazione:

```yaml
services:
  api:
    image: myapp/api:latest
    secrets:
      - db_password
      - api_key
    environment:
      # Riferimento al secret montato come file
      DB_PASSWORD_FILE: /run/secrets/db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt  # Da file locale
  api_key:
    environment: API_KEY_VALUE       # Da variabile d'ambiente
```

I secret vengono montati come file in `/run/secrets/<nome>` all'interno del container, in un tmpfs che non persiste su disco.

---

## Sicurezza Runtime dei Container — Approfondimento

La sicurezza dei container opera su più livelli del kernel Linux. Questa sezione approfondisce i meccanismi di isolamento e hardening introdotti nelle sezioni precedenti con configurazioni avanzate e pattern di produzione.

### Seccomp: Profili Personalizzati in Profondità

Il profilo seccomp predefinito di Docker blocca circa 44 system call pericolose su oltre 300 disponibili nel kernel Linux. Per workload sensibili, è necessario creare profili personalizzati che adottano un approccio allowlist (default deny, consentire solo ciò che serve).

La creazione di un profilo seccomp personalizzato richiede l'analisi delle system call effettivamente utilizzate dall'applicazione:

```bash
# Tracciare le system call di un'applicazione con strace
strace -c -f -p $(docker inspect --format '{{.State.Pid}}' mycontainer) 2>&1

# Alternativa: utilizzare OCI seccomp-bpf per generare profili automaticamente
# L'output mostra quali syscall vengono effettivamente invocate
docker run --rm --security-opt seccomp=unconfined \
  --security-opt systempaths=unconfined \
  myapp:latest 2>&1 | grep "syscall"
```

Un profilo seccomp robusto per un'applicazione web Node.js:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "architectures": [
    "SCMP_ARCH_X86_64",
    "SCMP_ARCH_AARCH64"
  ],
  "syscalls": [
    {
      "names": [
        "accept", "accept4", "access", "arch_prctl", "bind",
        "brk", "capget", "capset", "chdir", "chmod", "chown",
        "clock_getres", "clock_gettime", "clock_nanosleep",
        "clone", "close", "connect", "copy_file_range",
        "dup", "dup2", "dup3", "epoll_create", "epoll_create1",
        "epoll_ctl", "epoll_pwait", "epoll_wait", "eventfd",
        "eventfd2", "execve", "exit", "exit_group",
        "faccessat", "faccessat2", "fadvise64", "fallocate",
        "fchmod", "fchmodat", "fchown", "fchownat",
        "fcntl", "fdatasync", "flock", "fstat", "fstatfs",
        "fsync", "ftruncate", "futex", "getcwd",
        "getdents", "getdents64", "getegid", "geteuid",
        "getgid", "getgroups", "getpeername", "getpgrp",
        "getpid", "getppid", "getpriority", "getrandom",
        "getresgid", "getresuid", "getrlimit", "getrusage",
        "getsockname", "getsockopt", "gettid", "gettimeofday",
        "getuid", "inotify_add_watch", "inotify_init",
        "inotify_init1", "inotify_rm_watch", "ioctl",
        "kill", "lchown", "lgetxattr", "link", "linkat",
        "listen", "lseek", "lstat", "madvise", "membarrier",
        "memfd_create", "mincore", "mkdir", "mkdirat",
        "mmap", "mprotect", "mremap", "msync", "munmap",
        "nanosleep", "newfstatat", "open", "openat",
        "pipe", "pipe2", "poll", "ppoll", "prctl",
        "pread64", "preadv", "prlimit64", "pwrite64",
        "pwritev", "read", "readlink", "readlinkat",
        "readv", "recvfrom", "recvmmsg", "recvmsg",
        "rename", "renameat", "renameat2", "restart_syscall",
        "rmdir", "rseq", "rt_sigaction", "rt_sigprocmask",
        "rt_sigreturn", "sched_getaffinity", "sched_yield",
        "select", "sendfile", "sendmmsg", "sendmsg",
        "sendto", "set_robust_list", "set_tid_address",
        "setgid", "setgroups", "setitimer", "setpgid",
        "setrlimit", "setsid", "setsockopt", "setuid",
        "shutdown", "sigaltstack", "socket", "socketpair",
        "splice", "stat", "statfs", "statx", "symlink",
        "symlinkat", "sysinfo", "tgkill", "timer_create",
        "timer_delete", "timer_getoverrun", "timer_gettime",
        "timer_settime", "timerfd_create", "timerfd_gettime",
        "timerfd_settime", "tkill", "truncate", "umask",
        "uname", "unlink", "unlinkat", "utimensat",
        "wait4", "waitid", "write", "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["clone"],
      "action": "SCMP_ACT_ALLOW",
      "args": [
        {
          "index": 0,
          "value": 2114060288,
          "op": "SCMP_CMP_MASKED_EQ"
        }
      ]
    }
  ]
}
```

```bash
# Applicare il profilo personalizzato
docker run --security-opt seccomp=nodejs-profile.json myapp:latest

# In Docker Compose
# services:
#   api:
#     security_opt:
#       - seccomp:./security/nodejs-seccomp.json
```

### AppArmor: Profili Personalizzati

AppArmor implementa il Mandatory Access Control (MAC) a livello kernel, limitando le operazioni che un processo può effettuare indipendentemente dai permessi Unix tradizionali. Docker applica il profilo `docker-default` che offre protezione di base, ma per workload critici è necessario creare profili restrittivi specifici.

```
# /etc/apparmor.d/docker-webapp — Profilo AppArmor personalizzato
#include <tunables/global>

profile docker-webapp flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  # Negare accesso a informazioni sensibili dell'host
  deny /proc/*/mem r,
  deny /proc/sysrq-trigger rw,
  deny /proc/kcore r,
  deny /sys/firmware/** r,

  # Permettere accesso solo alle directory dell'applicazione
  /app/** r,
  /app/data/** rw,
  /app/logs/** w,
  /tmp/** rw,

  # Networking: permettere solo TCP/UDP
  network inet stream,
  network inet dgram,
  network inet6 stream,
  network inet6 dgram,

  # Negare raw socket (impedisce packet sniffing)
  deny network raw,
  deny network packet,

  # Permettere l'esecuzione solo dei binari necessari
  /usr/local/bin/node ix,
  /usr/bin/node ix,
  deny /bin/sh x,
  deny /bin/bash x,
  deny /bin/dash x,

  # Impedire mount e umount
  deny mount,
  deny umount,

  # Impedire ptrace (anti-debugging)
  deny ptrace,

  # Impedire l'accesso a device speciali
  deny /dev/** rw,
  /dev/null rw,
  /dev/urandom r,
  /dev/zero r,
}
```

```bash
# Caricare il profilo AppArmor
sudo apparmor_parser -r /etc/apparmor.d/docker-webapp

# Eseguire il container con il profilo personalizzato
docker run --security-opt apparmor=docker-webapp myapp:latest

# Verificare che il profilo sia attivo
aa-status | grep docker-webapp
```

### Capabilities Linux: Guida Dettagliata

Le Linux capabilities suddividono i privilegi di root in unità granulari. Docker per default assegna un sottoinsieme di 14 capabilities ai container. Per un hardening rigoroso, è necessario comprendere ogni capability e valutarne la necessità.

| Capability | Descrizione | Necessaria per |
|---|---|---|
| `NET_BIND_SERVICE` | Bind a porte < 1024 | Web server su porta 80/443 |
| `CHOWN` | Cambiare proprietario dei file | Setup iniziale dei permessi |
| `SETUID` / `SETGID` | Cambiare UID/GID del processo | Processi che cambiano utente |
| `DAC_OVERRIDE` | Ignorare permessi file | Accesso a file con permessi restrittivi |
| `FOWNER` | Operazioni su file indipendentemente dal proprietario | Gestione file di altri utenti |
| `KILL` | Inviare segnali a processi | Process manager (supervisord, tini) |
| `NET_RAW` | Socket raw e packet | Ping, strumenti di diagnostica rete |
| `SYS_CHROOT` | Usare chroot | Processi che cambiano root directory |
| `MKNOD` | Creare file speciali | Raramente necessario nei container |
| `AUDIT_WRITE` | Scrivere nel log di audit | Logging di audit |
| `SETFCAP` | Impostare capabilities sui file | Quasi mai necessario |

La strategia di hardening raccomandata è drop all + add back:

```yaml
# compose.yaml — Configurazione hardened
services:
  web:
    image: myapp/web:latest
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Solo se serve porta < 1024
    security_opt:
      - no-new-privileges:true  # Impedisce escalation via setuid
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=64m
      - /var/run:rw,noexec,nosuid,size=8m
    user: "1000:1000"
```

La flag `no-new-privileges` è particolarmente critica: impedisce che un processo nel container possa acquisire nuovi privilegi tramite binari setuid/setgid, anche se questi sono presenti nel filesystem. Questo blocca un vettore di attacco comune per l'escalation dei privilegi.

### Rootless Mode: Architettura e Limitazioni

Docker rootless esegue il daemon Docker (`dockerd`) e tutti i container come utente non privilegiato, utilizzando user namespaces per mappare l'UID 0 del container su un UID non privilegiato sull'host. Questo riduce la superficie di attacco del 60-80% rispetto alla modalità tradizionale con root.

```bash
# Installazione di Docker rootless
# Prerequisiti: uidmap, dbus-user-session, fuse-overlayfs
sudo apt-get install -y uidmap dbus-user-session fuse-overlayfs slirp4netns

# Installare Docker rootless
dockerd-rootless-setuptool.sh install

# Configurare le variabili d'ambiente (aggiungere a .bashrc)
export PATH=/home/$(whoami)/bin:$PATH
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock

# Verificare che Docker sia in modalità rootless
docker info 2>/dev/null | grep -i "rootless\|security"

# Configurare il servizio systemd per l'avvio automatico
systemctl --user enable docker
loginctl enable-linger $(whoami)
```

Limitazioni note della modalità rootless:

- **Porte privilegiate**: impossibile fare bind su porte < 1024 senza configurazione aggiuntiva (`sysctl net.ipv4.ip_unprivileged_port_start=0`)
- **Networking**: limitazioni con i driver macvlan e ipvlan; il networking utilizza `slirp4netns` o `pasta` come sostituti del bridge nativo
- **Storage**: overlay2 richiede il kernel 5.11+ con supporto `fuse-overlayfs` abilitato; per kernel più vecchi, viene usato `fuse-overlayfs` con prestazioni ridotte
- **cgroups v2**: necessario per il controllo delle risorse; cgroups v1 non è supportato in rootless mode
- **Ping**: richiede la configurazione di `net.ipv4.ping_group_range`

Nel 2025, ricerche di sicurezza di Qualys hanno evidenziato tre metodi per aggirare le restrizioni dei namespace non privilegiati su Ubuntu, dimostrando che rootless Docker deve essere parte di una strategia di difesa in profondità e non l'unica misura di sicurezza.

---

## Ottimizzazione delle Immagini — Pattern Avanzati

L'ottimizzazione delle immagini Docker ha un impatto diretto su sicurezza (meno componenti = meno CVE), prestazioni di deployment (immagini più piccole = pull più rapidi) e costi di storage nei registry. Questa sezione approfondisce i pattern avanzati per ottenere immagini minimali.

### Gerarchia delle Immagini Base

La scelta dell'immagine base determina il profilo di sicurezza e la dimensione dell'immagine finale. La gerarchia dal più grande al più piccolo:

| Immagine Base | Dimensione Tipica | Shell | Package Manager | Caso d'Uso |
|---|---|---|---|---|
| `ubuntu:24.04` | ~75 MB | Sì | apt | Sviluppo, debug |
| `debian:bookworm-slim` | ~50 MB | Sì | apt | Compromesso tra dimensione e utilità |
| `alpine:3.20` | ~7 MB | Sì (busybox) | apk | Produzione generica |
| `gcr.io/distroless/base` | ~20 MB | No | No | Produzione hardened |
| `gcr.io/distroless/static` | ~2 MB | No | No | Binari statici (Go, Rust) |
| `cgr.dev/chainguard/static` | ~2 MB | No | No | Alternativa con SBOM integrato |
| `scratch` | 0 bytes | No | No | Binari statici puri |

### Pattern Distroless

Le immagini distroless di Google contengono solo il runtime dell'applicazione (CA certificates, timezone data, librerie dinamiche base) senza shell, package manager o utility di sistema. Questo impedisce l'esecuzione di comandi interattivi in caso di compromissione del container.

```dockerfile
# Pattern distroless per applicazione Java
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /app
COPY . .
RUN ./gradlew bootJar --no-daemon

FROM gcr.io/distroless/java21-debian12:nonroot
COPY --from=builder /app/build/libs/app.jar /app.jar
EXPOSE 8080
ENTRYPOINT ["java", \
  "-XX:+UseContainerSupport", \
  "-XX:MaxRAMPercentage=75.0", \
  "-XX:+ExitOnOutOfMemoryError", \
  "-jar", "/app.jar"]
```

```dockerfile
# Pattern distroless per applicazione Python
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
COPY . .

FROM gcr.io/distroless/python3-debian12:nonroot
COPY --from=builder /root/.local/lib/python3.12/site-packages /usr/lib/python3.12/
COPY --from=builder /app /app
WORKDIR /app
ENTRYPOINT ["python3", "main.py"]
```

La variante `:nonroot` delle immagini distroless esegue automaticamente come utente non-root (UID 65534), eliminando la necessità di istruzioni `USER` nel Dockerfile.

### Pattern Scratch

L'immagine `scratch` è letteralmente un filesystem vuoto (0 bytes). È utilizzabile solo con binari linkati staticamente che non dipendono da librerie condivise del sistema operativo.

```dockerfile
# Pattern scratch per Go (compilazione statica)
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-s -w -extldflags '-static'" \
    -tags netgo,osusergo \
    -o /server ./cmd/server

FROM scratch
# Copiare certificati CA per connessioni TLS
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
# Copiare timezone data per time.LoadLocation()
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
# Copiare passwd per user lookup
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /server /server

USER 65534:65534
EXPOSE 8080
ENTRYPOINT ["/server"]
```

```dockerfile
# Pattern scratch per Rust (compilazione statica con musl)
FROM rust:1.79-alpine AS builder
RUN apk add --no-cache musl-dev
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
# Cache delle dipendenze
RUN mkdir src && echo "fn main() {}" > src/main.rs && \
    cargo build --release --target x86_64-unknown-linux-musl && \
    rm -rf src

COPY src/ src/
RUN cargo build --release --target x86_64-unknown-linux-musl

FROM scratch
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /app/target/x86_64-unknown-linux-musl/release/myapp /myapp
USER 65534:65534
ENTRYPOINT ["/myapp"]
```

### Chainguard Images

Le Chainguard Images sono un'alternativa moderna alle distroless di Google. Offrono immagini minimali con SBOM integrato, scansione continua delle vulnerabilità e aggiornamenti frequenti. Ogni immagine viene ricostruita quotidianamente con le ultime patch di sicurezza.

```dockerfile
# Chainguard per Node.js
FROM cgr.dev/chainguard/node:latest AS runtime
COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/node_modules /app/node_modules
WORKDIR /app
ENTRYPOINT ["node", "dist/main.js"]

# Chainguard per Python
FROM cgr.dev/chainguard/python:latest
COPY --from=builder /app /app
WORKDIR /app
ENTRYPOINT ["python3", "main.py"]
```

### Analisi e Riduzione della Dimensione

Strumenti come `dive` permettono di analizzare layer per layer il contenuto di un'immagine Docker, identificando file non necessari e opportunità di ottimizzazione:

```bash
# Analizzare i layer di un'immagine con dive
dive myapp:latest

# Confronto dimensioni immagini
docker images --format "{{.Repository}}:{{.Tag}}\t{{.Size}}" | sort -k2 -h

# Esportare e analizzare il contenuto di un'immagine
docker save myapp:latest | tar -tf - | head -50

# Verificare che non ci siano file sensibili inclusi
docker history --no-trunc myapp:latest
```

---

## Networking Docker — Deep Dive

### Architettura del Networking Docker

Il networking Docker si basa sul Container Network Model (CNM), che definisce tre componenti fondamentali: **Sandbox** (configurazione di rete isolata per ogni container, implementata tramite Linux network namespaces), **Endpoint** (interfaccia di rete virtuale che connette una Sandbox a una Network), e **Network** (gruppo di endpoint che possono comunicare direttamente tra loro).

```
┌─────────────────────────────────────────────────────┐
│                    Host Network Stack               │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Container│  │ Container│  │ Container│         │
│  │ Sandbox  │  │ Sandbox  │  │ Sandbox  │         │
│  │   eth0   │  │   eth0   │  │ eth0 eth1│         │
│  └────┬─────┘  └────┬─────┘  └──┬───┬───┘         │
│       │ veth         │ veth      │   │              │
│  ┌────┴──────────────┴──────────┴─┐ │              │
│  │        Bridge: br-custom       │ │              │
│  │        172.25.0.0/16           │ │              │
│  └────────────────────────────────┘ │              │
│                              ┌──────┴───────────┐  │
│                              │  Bridge: br-db   │  │
│                              │  172.26.0.0/16   │  │
│                              └──────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Custom Bridge Networks Avanzate

Le reti bridge personalizzate offrono funzionalità avanzate rispetto alla bridge predefinita (`docker0`): DNS automatico, isolamento completo, e configurazione granulare delle subnet.

```bash
# Creare una rete bridge con opzioni avanzate
docker network create \
  --driver bridge \
  --subnet 172.25.0.0/24 \
  --gateway 172.25.0.1 \
  --ip-range 172.25.0.128/25 \
  --aux-address "reserved1=172.25.0.2" \
  --aux-address "reserved2=172.25.0.3" \
  --opt com.docker.network.bridge.name=br-app \
  --opt com.docker.network.bridge.enable_icc=true \
  --opt com.docker.network.bridge.enable_ip_masquerade=true \
  --opt com.docker.network.driver.mtu=1500 \
  --label project=myapp \
  app-network

# Creare rete con DHCP pool ristretto
docker network create \
  --driver bridge \
  --subnet 10.10.0.0/16 \
  --ip-range 10.10.1.0/24 \
  --gateway 10.10.0.1 \
  internal-network

# Rete interna (nessun accesso esterno)
docker network create \
  --driver bridge \
  --internal \
  --subnet 192.168.100.0/24 \
  isolated-network
```

La flag `--internal` crea una rete senza accesso al mondo esterno, ideale per database e servizi backend che non devono mai comunicare direttamente con internet.

### IPvlan

Il driver **ipvlan** è simile a macvlan ma non assegna MAC address univoci ai container. Tutti i container condividono il MAC address dell'interfaccia parent. Questo è utile in ambienti dove il numero di MAC address è limitato (switch con port security, reti wireless, ambienti cloud con restrizioni MAC).

IPvlan opera in due modalità:

- **L2 (Layer 2)**: I container sono sullo stesso segmento di rete dell'host. Il traffico viene commutato a livello data-link. Simile a macvlan ma con MAC condiviso.
- **L3 (Layer 3)**: I container hanno subnet diverse e il traffico viene instradato a livello IP. Non c'è broadcast/multicast tra container e host.

```bash
# IPvlan L2: container sullo stesso segmento di rete
docker network create -d ipvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  -o parent=eth0 \
  -o ipvlan_mode=l2 \
  ipvlan-l2-net

# IPvlan L3: container con subnet dedicata, routing IP
docker network create -d ipvlan \
  --subnet=10.0.1.0/24 \
  -o parent=eth0 \
  -o ipvlan_mode=l3 \
  ipvlan-l3-net

# Collegare un container alla rete ipvlan con IP statico
docker run -d --name service-a \
  --network ipvlan-l2-net \
  --ip 192.168.1.50 \
  myapp:latest
```

| Caratteristica | Macvlan | IPvlan L2 | IPvlan L3 |
|---|---|---|---|
| MAC address | Unico per container | Condiviso con parent | Condiviso con parent |
| Broadcast/ARP | Sì | Sì | No |
| Routing | Switch L2 | Switch L2 | Routing L3 |
| Performance | Elevata | Elevata | Elevata |
| Caso d'uso | Apparecchi fisici virtuali | Ambienti con limite MAC | Segmentazione multi-subnet |

### Integrazione con Service Mesh

In architetture a microservizi, i service mesh (Istio, Linkerd, Consul Connect) operano come sidecar proxy all'interno di ogni container, gestendo mTLS, load balancing, circuit breaking e osservabilità. L'integrazione con Docker avviene a livello di networking:

```yaml
# compose.yaml — Simulazione service mesh con Envoy sidecar
services:
  api:
    build: ./api
    network_mode: "service:api-proxy"  # Condivide lo stack di rete con il proxy

  api-proxy:
    image: envoyproxy/envoy:v1.31-latest
    volumes:
      - ./envoy/envoy.yaml:/etc/envoy/envoy.yaml:ro
    ports:
      - "8080:8080"   # Ingress
      - "9901:9901"   # Admin
    networks:
      - mesh-network

  backend:
    build: ./backend
    network_mode: "service:backend-proxy"

  backend-proxy:
    image: envoyproxy/envoy:v1.31-latest
    volumes:
      - ./envoy/backend-envoy.yaml:/etc/envoy/envoy.yaml:ro
    networks:
      - mesh-network

networks:
  mesh-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.30.0.0/16
```

Con `network_mode: "service:<altro_servizio>"`, il container dell'applicazione condivide lo stack di rete del sidecar proxy, permettendo la comunicazione tra i due tramite `localhost`. Tutto il traffico in uscita dall'applicazione passa attraverso il proxy Envoy, che applica le policy del service mesh.

---

## Storage Driver e Plugin di Volume

### Overlay2: Architettura Interna

`overlay2` è lo storage driver predefinito e raccomandato per Docker. Utilizza il filesystem OverlayFS del kernel Linux per implementare il meccanismo di layer delle immagini Docker mediante la sovrapposizione di directory.

OverlayFS opera con tre directory fondamentali:

- **lowerdir**: Directory in sola lettura che contengono i layer dell'immagine (impilati dal basso verso l'alto)
- **upperdir**: Directory in lettura-scrittura per le modifiche del container (il layer del container)
- **merged**: Vista unificata che combina lowerdir e upperdir, presentando un filesystem coerente al container
- **workdir**: Directory di lavoro interna usata da OverlayFS per operazioni atomiche

```bash
# Esaminare la struttura overlay2 di un container in esecuzione
docker inspect --format='{{.GraphDriver.Data}}' mycontainer

# Output tipico:
# map[LowerDir:/var/lib/docker/overlay2/abc123/diff:/var/lib/docker/overlay2/def456/diff
#     MergedDir:/var/lib/docker/overlay2/xyz789/merged
#     UpperDir:/var/lib/docker/overlay2/xyz789/diff
#     WorkDir:/var/lib/docker/overlay2/xyz789/work]

# Visualizzare le modifiche nel layer del container (upperdir)
ls -la /var/lib/docker/overlay2/xyz789/diff/

# Analizzare l'utilizzo dello storage
docker system df -v
```

Quando un container modifica un file esistente in un lowerdir, overlay2 esegue una operazione di **copy-up**: il file viene copiato dal lowerdir all'upperdir prima della modifica. Questo ha implicazioni prestazionali: la prima scrittura a un file esistente è più lenta a causa della copia, ma le scritture successive sono veloci perché operano direttamente nell'upperdir.

```json
{
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.size=10G"
  ]
}
```

Il parametro `overlay2.size` impone un limite sulla dimensione massima del layer scrivibile di ogni container, prevenendo che un container riempia il disco dell'host.

### Volume Plugin Avanzati

Oltre ai driver di volume integrati, Docker supporta plugin di terze parti che estendono le capacità di storage con backend distribuiti, crittografati o cloud-native.

```bash
# Plugin REX-Ray per storage cloud (AWS EBS, Azure Disk, GCE PD)
docker plugin install rexray/ebs EBS_ACCESSKEY=... EBS_SECRETKEY=...
docker volume create -d rexray/ebs --opt size=100 ebs-data

# Plugin local-persist per volumi con percorso personalizzato
docker volume create -d local-persist \
  -o mountpoint=/data/app-storage app-data

# Plugin GlusterFS per storage distribuito
docker volume create -d glusterfs \
  --opt servers=node1,node2,node3 \
  --opt volname=docker-volumes \
  gluster-data
```

```yaml
# compose.yaml — Volume con driver NFS avanzato
volumes:
  shared-assets:
    driver: local
    driver_opts:
      type: nfs
      o: "addr=nfs.internal,rw,nfsvers=4.1,hard,timeo=600,retrans=2,rsize=1048576,wsize=1048576"
      device: ":/exports/assets"

  cifs-share:
    driver: local
    driver_opts:
      type: cifs
      o: "addr=fileserver.internal,username=${CIFS_USER},password=${CIFS_PASS},vers=3.0"
      device: "//fileserver.internal/docker-data"
```

---

## Confronto Orchestratori: Swarm vs Kubernetes vs Nomad

La scelta dell'orchestratore dipende dalla complessità del workload, dalle competenze del team e dai requisiti di scala. Questa sezione fornisce un confronto approfondito che va oltre la tabella introduttiva presente nelle sezioni precedenti.

### Docker Swarm: Semplicità e Integrazione Nativa

Docker Swarm è la soluzione di orchestrazione integrata in Docker Engine. Il suo vantaggio principale è la curva di apprendimento quasi piatta per chi già conosce Docker e Docker Compose. Un'analisi comparativa del 2024 ha dimostrato che Swarm raggiunge tempi di risposta applicativi comparabili a Kubernetes con il 40-60% in meno di consumo risorse per cluster sotto i 20 nodi.

**Punti di forza:** Setup in un singolo comando (`docker swarm init`), riutilizzo della sintassi Compose per lo stack deployment, rete overlay cifrata integrata, rolling update e rollback nativi, overhead operativo minimo.

**Limitazioni:** Auto-scaling assente (solo scaling manuale), nessun supporto CRD (Custom Resource Definitions), ecosistema di plugin limitato, community ridotta rispetto a Kubernetes, nessun supporto per workload non-container.

```bash
# Deployment completo su Swarm in 3 comandi
docker swarm init --advertise-addr 192.168.1.10
docker stack deploy -c compose.yaml myapp
docker service scale myapp_api=5
```

### Kubernetes: Ecosistema Enterprise

Kubernetes (K8s) è lo standard de facto per l'orchestrazione di container su scala enterprise, adottato da oltre l'80% delle aziende Fortune 500. Supporta fino a 5.000 nodi per cluster con self-healing automatico, auto-scaling orizzontale (HPA), verticale (VPA) e basato su eventi (KEDA).

**Punti di forza:** Ecosistema vastissimo (Helm, Operators, CRDs, Service Mesh), auto-scaling avanzato, supporto multi-cloud nativo, gestione dichiarativa con riconciliazione continua, storage dinamico tramite CSI, networking flessibile tramite CNI plugin.

**Limitazioni:** Complessità operativa elevata, curva di apprendimento ripida, overhead di risorse significativo per cluster piccoli, richiede competenze specializzate per la gestione.

### HashiCorp Nomad: Flessibilità Multi-Workload

Nomad è un orchestratore leggero di HashiCorp che gestisce container Docker, macchine virtuali, binari nativi e workload batch con un singolo binario. Aziende come Target, eBay, Roblox e Trivago utilizzano Nomad in produzione.

**Punti di forza:** Architettura a singolo binario, supporta container e non-container (Java JAR, batch jobs, VM), integrazione nativa con HashiCorp Vault e Consul, scalabilità fino a 10.000 nodi e 1 milione di task per cluster, complessità operativa contenuta.

**Limitazioni:** Ecosistema più ristretto di Kubernetes, community più piccola, meno integrazioni cloud-native, richiede Consul per service discovery avanzato e Vault per secret management.

| Dimensione | Docker Swarm | Kubernetes | Nomad |
|---|---|---|---|
| Nodi cluster | ≤ 20 ideale | Fino a 5.000 | Fino a 10.000 |
| Tipo workload | Solo container | Principalmente container | Container + VM + batch + binari |
| Auto-scaling | No (solo manuale) | HPA, VPA, KEDA | Autoscaler plugin |
| Setup time | Minuti | Ore/Giorni | Ore |
| Overhead operativo | Minimo | Alto | Medio |
| Costo team | 1 DevOps | 2-3 specialisti K8s | 1-2 DevOps |
| Job mercato (2025) | Limitato | 10x rispetto agli altri | In crescita |
| Secret management | Docker secrets | K8s Secrets / External | Vault nativo |
| Service mesh | No (manuale) | Istio, Linkerd, Cilium | Consul Connect |

**Raccomandazioni:**

- **Startup / team piccoli (< 10 servizi):** Docker Swarm. Minimo overhead, rapido da configurare, sufficiente per la maggior parte delle applicazioni web.
- **Enterprise / microservizi complessi (> 50 servizi):** Kubernetes. L'ecosistema e la community giustificano la complessità.
- **Workload eterogenei (container + VM + batch):** Nomad. L'unico orchestratore che gestisce nativamente workload non-container.
- **Percorso di crescita:** Iniziare con Swarm, migrare a K8s o Nomad quando le limitazioni diventano reali, non speculative.

---

## Docker in Produzione — Configurazioni Avanzate

### Logging Drivers Approfondimento

Il logging driver determina come Docker gestisce l'output (stdout/stderr) dei container. La scelta del driver ha impatto diretto sulle prestazioni, sulla persistenza dei log e sulla capacità di analisi centralizzata.

**`json-file`** (default): Scrive i log come file JSON sul disco dell'host. Senza limiti configurati, i log crescono indefinitamente fino a esaurire lo spazio disco. In produzione è obbligatorio configurare rotazione e limiti:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3",
    "compress": "true",
    "labels": "environment,service",
    "tag": "{{.ImageName}}/{{.Name}}/{{.ID}}"
  }
}
```

**`local`** (raccomandato): Driver ottimizzato introdotto in Docker 20.10. Offre prestazioni migliori di `json-file` con rotazione integrata e compressione automatica. Non richiede configurazione manuale di `max-size`/`max-file`:

```json
{
  "log-driver": "local",
  "log-opts": {
    "max-size": "10m",
    "max-file": "5"
  }
}
```

**`fluentd`** / **`fluent-bit`**: Per logging centralizzato in deployment con decine di host e centinaia di container. I log vengono inviati a un collettore che li inoltra a Elasticsearch, Loki o altri backend:

```yaml
services:
  api:
    logging:
      driver: fluentd
      options:
        fluentd-address: "tcp://fluentd.internal:24224"
        fluentd-async: "true"
        fluentd-retry-wait: "1s"
        fluentd-max-retries: "30"
        tag: "docker.{{.Name}}.{{.ID}}"
        labels: "environment,version"

  fluent-bit:
    image: fluent/fluent-bit:latest
    volumes:
      - ./fluent-bit/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf:ro
    ports:
      - "24224:24224"
```

**`journald`**: Integrazione con systemd journal. Ideale per host Linux che utilizzano già journald per la gestione centralizzata dei log di sistema:

```yaml
services:
  api:
    logging:
      driver: journald
      options:
        tag: "myapp-api"
```

### Health Check Avanzati

I health check verificano lo stato funzionale dell'applicazione, non solo che il processo sia attivo. Un health check efficace testa le dipendenze critiche dell'applicazione:

```dockerfile
# Health check multi-dipendenza con script personalizzato
COPY healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
  CMD ["/usr/local/bin/healthcheck.sh"]
```

```bash
#!/bin/sh
# healthcheck.sh — Verifica lo stato dell'applicazione e delle dipendenze

# Verificare che l'endpoint di salute risponda
if ! wget --no-verbose --tries=1 --spider http://localhost:8080/health 2>/dev/null; then
  echo "FAIL: API endpoint non raggiungibile"
  exit 1
fi

# Verificare la connessione al database (opzionale, per servizi con DB)
if [ -n "$DATABASE_URL" ]; then
  if ! pg_isready -h db -U app -q 2>/dev/null; then
    echo "WARN: Database non raggiungibile"
    # exit 1  # Decommentare se il DB è critico
  fi
fi

# Verificare spazio disco disponibile
DISK_USAGE=$(df /app/data 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%')
if [ "${DISK_USAGE:-0}" -gt 90 ]; then
  echo "WARN: Disco quasi pieno (${DISK_USAGE}%)"
  exit 1
fi

echo "OK"
exit 0
```

I health check influenzano il comportamento di Docker in modo significativo: un container `unhealthy` non viene automaticamente riavviato da Docker standalone (serve un orchestratore), ma la condizione `service_healthy` in `depends_on` attende che il container raggiunga lo stato healthy prima di avviare i servizi dipendenti.

### Resource Limits e cgroups

I limiti di risorse in Docker sono implementati tramite Linux cgroups (control groups). Configurare limiti appropriati è essenziale per prevenire l'effetto "noisy neighbor" e garantire prestazioni prevedibili.

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: "2.0"          # Max 2 CPU core
          memory: 1G           # Max 1 GB RAM
          pids: 256            # Max 256 processi/thread
        reservations:
          cpus: "0.5"          # Garantiti 0.5 CPU
          memory: 256M         # Garantiti 256 MB RAM

    # Limiti aggiuntivi non disponibili in deploy.resources
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
      nproc:
        soft: 4096
        hard: 8192

    # OOM (Out of Memory) policy
    oom_score_adj: 100         # Priorità di kill in caso di OOM (-1000 a 1000)
    # oom_kill_disable: false  # Non disabilitare mai l'OOM killer in produzione

    # Storage limit per il layer scrivibile
    storage_opt:
      size: "5G"
```

```bash
# Verificare i limiti di un container in esecuzione
docker inspect --format='{{.HostConfig.Memory}}' mycontainer
docker inspect --format='{{.HostConfig.NanoCpus}}' mycontainer

# Monitorare l'utilizzo rispetto ai limiti
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.PIDs}}"

# Verificare i cgroup di un container
cat /sys/fs/cgroup/docker/$(docker inspect --format='{{.Id}}' mycontainer)/memory.max
```

### Restart Policies

Le restart policies determinano il comportamento di Docker quando un container termina. La scelta della policy dipende dal tipo di servizio e dall'ambiente di deployment.

| Policy | Comportamento | Caso d'Uso |
|---|---|---|
| `no` | Non riavviare mai | Container one-shot, task batch |
| `on-failure[:max]` | Riavvia solo su exit code ≠ 0 | Script, worker con errori recuperabili |
| `always` | Riavvia sempre, anche dopo stop manuale + riavvio Docker | Servizi critici senza manutenzione pianificata |
| `unless-stopped` | Come `always`, ma rispetta lo stop manuale | Servizi di produzione con finestre di manutenzione |

```yaml
services:
  # Servizio web: riavvio automatico tranne durante manutenzione
  api:
    restart: unless-stopped

  # Worker con limite di tentativi per evitare crash loop infiniti
  worker:
    restart: "on-failure:5"

  # Database: sempre attivo, anche dopo riavvio del daemon
  db:
    restart: always

  # Migration: esegui una volta e termina
  migrate:
    restart: "no"
    depends_on:
      db:
        condition: service_healthy
```

La combinazione di restart policy con health check e resource limits forma la triade della resilienza in produzione: il container viene riavviato se crasha (restart policy), viene dichiarato unhealthy se non funziona correttamente (health check) e non può consumare risorse illimitate (resource limits).

### Init Process e Gestione dei Segnali

I container Docker non hanno un processo init tradizionale. Il processo specificato in `ENTRYPOINT` viene eseguito come PID 1, il che significa che deve gestire correttamente i segnali Unix (SIGTERM, SIGINT) e il reaping dei processi zombie. L'opzione `--init` di Docker inietta `tini` come PID 1 per gestire questi aspetti:

```yaml
services:
  api:
    init: true  # Inietta tini come PID 1
    stop_grace_period: 30s
    stop_signal: SIGTERM
```

```bash
# Equivalente via CLI
docker run --init --stop-timeout 30 myapp:latest
```

Senza `--init`, un'applicazione che genera processi figli (fork) può accumulare processi zombie, poiché PID 1 in un container non esegue automaticamente `wait()` sui processi terminati.

---

## Alternative a Docker Desktop

Docker Desktop ha introdotto una licenza commerciale a pagamento per aziende con più di 250 dipendenti o fatturato superiore a 10 milioni USD. Questo ha stimolato lo sviluppo di alternative open-source e commerciali.

### Podman e Podman Desktop

**Podman** è il motore container di Red Hat, progettato come sostituto drop-in di Docker con architettura fondamentalmente diversa: daemonless (nessun processo daemon centrale) e rootless per default.

```bash
# Installazione Podman su Ubuntu/Debian
sudo apt-get install -y podman

# I comandi sono compatibili con Docker
podman run -d --name webserver -p 8080:80 nginx:alpine
podman build -t myapp:latest .
podman compose up -d  # Richiede podman-compose o il plugin compose

# Generare systemd unit da un container Podman
podman generate systemd --new --name webserver > ~/.config/systemd/user/webserver.service
systemctl --user enable --now webserver

# Impostare alias per compatibilità totale
alias docker=podman
```

**Vantaggi:** Nessun daemon (riduce single point of failure), rootless per default, compatibilità con Kubernetes (genera/consuma YAML K8s), pods nativi (raggruppamento di container come in K8s), licenza open-source senza restrizioni commerciali.

**Limitazioni:** Docker Compose richiede `podman-compose` (Python) o il plugin Compose, alcune incompatibilità con Docker API in edge case, il supporto macOS/Windows richiede una VM (come Docker Desktop), l'integrazione IDE è meno matura.

### Colima

**Colima** (Container on Lima) è un runtime container leggero per macOS e Linux. Utilizza Lima per gestire una VM Linux e supporta Docker, containerd e Kubernetes.

```bash
# Installazione su macOS via Homebrew
brew install colima docker

# Avvio con configurazione personalizzata
colima start \
  --cpu 4 \
  --memory 8 \
  --disk 60 \
  --arch aarch64 \
  --vm-type vz \
  --vz-rosetta  # Emulazione x86_64 su Apple Silicon

# Colima utilizza il socket Docker standard
docker ps  # Funziona direttamente

# Profili multipli per ambienti diversi
colima start --profile k8s --kubernetes
colima start --profile dev --cpu 2 --memory 4
```

**Vantaggi:** Consumo RAM circa 400 MB idle (vs 2+ GB di Docker Desktop su M1), interfaccia CLI minimale, supporto Kubernetes opzionale tramite k3s, completamente gratuito e open-source, compatibilità piena con Docker CLI.

**Limitazioni:** Solo macOS e Linux (nessun supporto Windows), nessuna GUI nativa, configurazione iniziale richiede familiarità con il terminale.

### OrbStack

**OrbStack** è un'alternativa commerciale a Docker Desktop esclusiva per macOS, ottimizzata per prestazioni e integrazione nativa con il sistema operativo.

```bash
# Installazione su macOS
brew install orbstack

# OrbStack espone il socket Docker standard
docker ps  # Funziona immediatamente

# Gestione risorse e macchine virtuali Linux
orb create ubuntu dev-machine
orb shell dev-machine
```

**Vantaggi:** Consumo RAM 4.5x inferiore a Docker Desktop, avvio istantaneo dei container, integrazione Finder nativa, gestione VM Linux integrata, supporto Kubernetes incluso.

**Limitazioni:** Solo macOS, licenza commerciale (gratuito per uso personale), vendor lock-in, nessuna versione Linux o Windows.

### Rancher Desktop

**Rancher Desktop** di SUSE è un'alternativa open-source multi-piattaforma che integra containerd e k3s (distribuzione leggera di Kubernetes).

**Vantaggi:** Multi-piattaforma (macOS, Windows, Linux), Kubernetes integrato (k3s), completamente gratuito e open-source, scelta del runtime (dockerd o containerd).

**Limitazioni:** Consumo risorse paragonabile a Docker Desktop, interfaccia GUI meno raffinata, aggiornamenti meno frequenti.

| Alternativa | Piattaforme | Daemon | Licenza | RAM Idle | K8s Integrato |
|---|---|---|---|---|---|
| Docker Desktop | macOS, Windows, Linux | dockerd | Commerciale (>250 dip.) | ~2 GB | Sì |
| Podman Desktop | macOS, Windows, Linux | Daemonless | Open Source (Apache 2.0) | ~800 MB | Parziale (pods) |
| Colima | macOS, Linux | dockerd/containerd | Open Source (MIT) | ~400 MB | Sì (k3s) |
| OrbStack | macOS | dockerd | Commerciale | ~450 MB | Sì |
| Rancher Desktop | macOS, Windows, Linux | dockerd/containerd | Open Source (Apache 2.0) | ~1.8 GB | Sì (k3s) |

---

## Standard OCI e containerd

### Open Container Initiative (OCI)

L'Open Container Initiative è un progetto della Linux Foundation che definisce gli standard aperti per i container. Gli standard OCI garantiscono l'interoperabilità tra diversi runtime, builder e registry, impedendo il vendor lock-in.

OCI definisce tre specifiche fondamentali:

**OCI Runtime Specification** — Definisce come eseguire un container a partire da un bundle di filesystem. Specifica il formato del file di configurazione (`config.json`) che descrive il processo da eseguire, i namespaces, i cgroups, le capabilities e i mount. `runc` è l'implementazione di riferimento.

**OCI Image Specification** — Definisce il formato delle immagini container come una serie di layer (changeset di filesystem) più un manifesto e una configurazione JSON. Questo standard permette di costruire immagini con qualsiasi tool (Docker, Buildah, kaniko) ed eseguirle con qualsiasi runtime conforme.

**OCI Distribution Specification** — Definisce il protocollo per la distribuzione delle immagini tramite registry HTTP. La versione 1.1.0 (febbraio 2024) ha introdotto la **Referrers API**, che permette di allegare artefatti (firme, SBOM, risultati di scansione vulnerabilità) a un'immagine specifica tramite il suo digest:

```bash
# Verificare gli artefatti associati a un'immagine via Referrers API
# GET /v2/<name>/referrers/<digest>
curl -s https://registry.example.com/v2/myapp/referrers/sha256:abc123... \
  -H "Accept: application/vnd.oci.image.index.v1+json" | jq .

# Aggiungere una SBOM come artefatto allegato
oras attach registry.example.com/myapp:latest \
  --artifact-type "application/spdx+json" \
  sbom.spdx.json

# Verificare gli artefatti allegati
oras discover registry.example.com/myapp:latest
```

### containerd come Runtime Indipendente

containerd è il runtime container di alto livello che gestisce il ciclo di vita completo dei container indipendentemente da Docker. È utilizzato da Kubernetes (tramite CRI), Docker Engine e altri sistemi di orchestrazione.

```bash
# Interagire direttamente con containerd tramite ctr
sudo ctr images pull docker.io/library/nginx:alpine
sudo ctr containers create docker.io/library/nginx:alpine web
sudo ctr tasks start web

# nerdctl: CLI compatibile con Docker per containerd
nerdctl run -d --name webserver -p 8080:80 nginx:alpine
nerdctl build -t myapp:latest .
nerdctl compose up -d
```

`nerdctl` è il CLI di containerd che fornisce compatibilità drop-in con i comandi Docker. Supporta funzionalità esclusive come image encryption, lazy pulling (stargz/nydus) e rootless mode nativo senza configurazione aggiuntiva.

```bash
# Funzionalità esclusive di nerdctl
# Lazy pulling: scarica solo i layer necessari al momento dell'avvio
nerdctl --snapshotter=stargz run ghcr.io/stargz-containers/python:3.12-esgz

# Image encryption: crittografia dei layer con chiavi GPG
nerdctl image encrypt --recipient=jwe:pubkey.pem myapp:latest myapp:encrypted

# Rootless mode nativo
containerd-rootless-setuptool.sh install
nerdctl run -d --name test nginx:alpine
```

---

## Firma delle Immagini e Supply-Chain Security

### Docker Content Trust (DCT) — Stato Attuale

DCT (basato su Notary v1 e il framework TUF — The Update Framework) è il sistema di firma nativo di Docker. Tuttavia, è considerato in fase di deprecazione: Azure Container Registry ha iniziato la deprecazione di DCT a marzo 2025, con rimozione completa prevista per marzo 2028. Per nuovi progetti, è raccomandato migrare a Cosign o Notation.

```bash
# DCT è ancora disponibile ma sconsigliato per nuovi progetti
export DOCKER_CONTENT_TRUST=1
docker push registry.example.com/myapp:1.0.0
# Viene richiesta la passphrase per la chiave di firma

docker trust inspect --pretty registry.example.com/myapp:1.0.0
docker trust revoke registry.example.com/myapp:1.0.0
```

### Cosign (Sigstore)

Cosign è lo strumento di firma container del progetto Sigstore, mantenuto dall'OpenSSF (Open Source Security Foundation). Dalla versione 2.0 (febbraio 2024), la firma keyless è una funzionalità pienamente supportata per ambienti CI/CD.

**Firma con chiave** — Modello tradizionale con keypair generato localmente:

```bash
# Generare una keypair
cosign generate-key-pair

# Firmare un'immagine con il digest (mai con il tag mutabile)
cosign sign --key cosign.key registry.example.com/myapp@sha256:abc123...

# Verificare la firma
cosign verify --key cosign.pub registry.example.com/myapp@sha256:abc123...
```

**Firma keyless** — Non richiede gestione manuale delle chiavi. Utilizza identità OIDC (GitHub, GitLab, Google) e un transparency log (Rekor) per garantire la tracciabilità:

```bash
# Firma keyless in CI/CD (usa OIDC del provider CI)
cosign sign registry.example.com/myapp@sha256:abc123...
# Cosign ottiene un certificato temporaneo da Fulcio,
# firma l'immagine e registra la firma su Rekor

# Verificare la firma keyless con identità specifica
cosign verify \
  --certificate-identity "https://github.com/org/repo/.github/workflows/build.yaml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  registry.example.com/myapp@sha256:abc123...
```

**Allegare e verificare SBOM:**

```bash
# Generare SBOM con syft
syft registry.example.com/myapp:latest -o spdx-json > sbom.spdx.json

# Allegare SBOM come artefatto firmato
cosign attach sbom --sbom sbom.spdx.json registry.example.com/myapp@sha256:abc123...

# Firmare l'SBOM allegata
cosign sign --attachment sbom registry.example.com/myapp@sha256:abc123...

# Verificare SBOM firmata
cosign verify --attachment sbom --key cosign.pub registry.example.com/myapp@sha256:abc123...
```

### Notation (Notary v2)

Notation è il CLI del progetto Notary v2, che costruisce la catena di fiducia su certificati X.509 (lo stesso meccanismo di HTTPS) anziché su TUF. Questo approccio si integra con le PKI enterprise esistenti.

```bash
# Installare il plugin AWS Signer per Notation
notation plugin install com.amazonaws.signer.notation.plugin

# Firmare un'immagine con certificato X.509
notation sign \
  --signature-format cose \
  --id "arn:aws:signer:eu-west-1:123456789:signing-profile/MyProfile" \
  --plugin "com.amazonaws.signer.notation.plugin" \
  registry.example.com/myapp@sha256:abc123...

# Configurare la trust policy
cat > ~/.config/notation/trustpolicy.json << 'EOF'
{
  "version": "1.0",
  "trustPolicies": [
    {
      "name": "production-images",
      "registryScopes": ["registry.example.com/myapp"],
      "signatureVerification": {
        "level": "strict"
      },
      "trustStores": ["ca:production-ca"],
      "trustedIdentities": [
        "x509.subject: C=IT, O=MyOrg, CN=image-signer"
      ]
    }
  ]
}
EOF

# Verificare la firma
notation verify registry.example.com/myapp@sha256:abc123...
```

| Caratteristica | DCT (Notary v1) | Cosign (Sigstore) | Notation (Notary v2) |
|---|---|---|---|
| Framework di trust | TUF | Sigstore (Fulcio + Rekor) | X.509 PKI |
| Firma keyless | No | Sì (OIDC) | No |
| Transparency log | No | Sì (Rekor) | Opzionale |
| Integrazione CI/CD | Limitata | Eccellente | Buona |
| Stato (2025) | Deprecazione in corso | Standard de facto | In crescita (enterprise) |
| OCI Referrers API | No | Sì | Sì |
| Multi-registry | Limitato | Qualsiasi OCI-conforme | Qualsiasi OCI-conforme |

---

## Docker Bench for Security — Audit Automatizzato

Docker Bench for Security è uno script open-source che verifica automaticamente la conformità della configurazione Docker rispetto al CIS (Center for Internet Security) Docker Benchmark. L'audit copre oltre 100 raccomandazioni di sicurezza organizzate in sette categorie.

### Struttura dell'Audit CIS

Le sette sezioni dell'audit CIS Docker Benchmark:

1. **Host Configuration** — Configurazione del kernel, partizioni separate per `/var/lib/docker`, auditing di file Docker
2. **Docker Daemon Configuration** — Logging, live restore, TLS, user namespace remapping, profili seccomp/AppArmor predefiniti
3. **Docker Daemon Configuration Files** — Permessi dei file di configurazione, ownership del socket Docker
4. **Container Images and Build Files** — Utente non-root, istruzioni HEALTHCHECK, assenza di credenziali hardcoded
5. **Container Runtime** — Capabilities, profili di sicurezza, limiti risorse, read-only filesystem
6. **Docker Security Operations** — Processi di patching, vulnerability scanning, incident response
7. **Docker Swarm Configuration** — Crittografia overlay, rotazione certificati, configurazione manager

### Esecuzione dell'Audit

```bash
# Esecuzione standard di Docker Bench
docker run --rm --net host --pid host --userns host --cap-add audit_control \
  -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
  -v /var/lib/docker:/var/lib/docker:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /usr/lib/systemd:/usr/lib/systemd:ro \
  -v /etc:/etc:ro \
  --label docker_bench_security \
  docker/docker-bench-security

# Esecuzione con output JSON per integrazione in pipeline
docker run --rm --net host --pid host --userns host --cap-add audit_control \
  -v /var/lib/docker:/var/lib/docker:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /etc:/etc:ro \
  -v $(pwd)/results:/results \
  docker/docker-bench-security -l /results/bench-$(date +%Y%m%d).json

# Esecuzione selettiva per sezione specifica
docker run --rm --net host --pid host --userns host --cap-add audit_control \
  -v /var/lib/docker:/var/lib/docker:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /etc:/etc:ro \
  docker/docker-bench-security -c container_runtime
```

### Interpretazione dei Risultati

L'output dell'audit utilizza tre livelli di severità:

- **[PASS]** — La configurazione è conforme alla raccomandazione CIS
- **[WARN]** — La configurazione non è conforme e richiede attenzione
- **[INFO]** — Informazione che richiede valutazione manuale
- **[NOTE]** — Nota informativa senza implicazioni di sicurezza

```bash
# Esempio di output tipico
# [PASS] 2.1  - Ensure network traffic is restricted between containers on the default bridge
# [WARN] 2.2  - Ensure the logging level is set to 'info'
# [WARN] 2.3  - Ensure Docker is allowed to make changes to iptables
# [PASS] 2.4  - Ensure insecure registries are not used
# [WARN] 4.1  - Ensure that a user for the container has been created
# [WARN] 5.1  - Ensure that, if applicable, an AppArmor Profile is enabled
# [WARN] 5.2  - Ensure that, if applicable, SELinux security options are set
# [PASS] 5.3  - Ensure that Linux kernel capabilities are restricted within containers
```

### Automazione dell'Audit in CI/CD

Per mantenere la conformità nel tempo, l'audit Docker Bench dovrebbe essere eseguito regolarmente come parte della pipeline CI/CD o come job schedulato:

```yaml
# .github/workflows/docker-security-audit.yml
name: Docker Security Audit

on:
  schedule:
    - cron: "0 6 * * 1"  # Ogni lunedì alle 06:00 UTC
  workflow_dispatch:

jobs:
  audit:
    runs-on: self-hosted
    steps:
      - name: Run Docker Bench for Security
        run: |
          docker run --rm --net host --pid host --userns host \
            --cap-add audit_control \
            -v /var/lib/docker:/var/lib/docker:ro \
            -v /var/run/docker.sock:/var/run/docker.sock:ro \
            -v /etc:/etc:ro \
            -v ${{ github.workspace }}/results:/results \
            docker/docker-bench-security \
            -l /results/bench-report.json

      - name: Parse and check results
        run: |
          WARNS=$(grep -c "\[WARN\]" results/bench-report.json || true)
          echo "Warnings found: $WARNS"
          if [ "$WARNS" -gt 10 ]; then
            echo "::error::Too many security warnings ($WARNS)"
            exit 1
          fi

      - name: Upload audit results
        uses: actions/upload-artifact@v4
        with:
          name: docker-bench-results
          path: results/
```

### CIS Benchmark con InSpec

Per audit più granulari e compliance-as-code, il profilo InSpec del CIS Docker Benchmark permette di integrare i controlli di sicurezza direttamente nel codice dell'infrastruttura:

```bash
# Eseguire l'audit CIS Docker con InSpec
inspec exec https://github.com/dev-sec/cis-docker-benchmark \
  --reporter json:cis-report.json cli

# Con target remoto
inspec exec https://github.com/dev-sec/cis-docker-benchmark \
  -t ssh://admin@docker-host.internal \
  --reporter json:cis-report.json
```

---

## Debugging e Troubleshooting Avanzato dei Container

La capacità di diagnosticare e risolvere problemi nei container in produzione è una competenza fondamentale per qualsiasi ingegnere DevOps. A differenza dei server tradizionali, i container presentano sfide uniche: filesystem effimeri, namespaces isolati, processi PID 1 con comportamenti specifici e networking virtualizzato.

### Ispezione dei Container in Esecuzione

Il primo strumento di diagnostica è `docker inspect`, che restituisce la configurazione completa del container in formato JSON. Combinato con `jq`, permette di estrarre informazioni specifiche rapidamente:

```bash
# Indirizzo IP del container
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' myapp

# Stato di salute corrente
docker inspect --format='{{json .State.Health}}' myapp | jq .

# Bind mount e volumi
docker inspect -f '{{json .Mounts}}' myapp | jq '.[] | {Source, Destination, RW}'

# Variabili d'ambiente (ATTENZIONE: può esporre segreti)
docker inspect -f '{{json .Config.Env}}' myapp | jq .

# PID del processo nel namespace host
docker inspect -f '{{.State.Pid}}' myapp
```

### Debug senza Shell nel Container

Molte immagini di produzione (distroless, scratch) non contengono shell o strumenti diagnostici. In questi casi, si possono usare tecniche alternative:

```bash
# Container di debug effimero con accesso al namespace di rete
docker run --rm -it --network container:myapp nicolaka/netshoot

# Accesso al namespace dei processi
docker run --rm -it --pid container:myapp busybox ps aux

# Container di debug con accesso al filesystem (read-only)
docker run --rm -it \
  --volumes-from myapp:ro \
  alpine sh

# nsenter dal host per entrare nei namespace del container
PID=$(docker inspect -f '{{.State.Pid}}' myapp)
sudo nsenter -t $PID -n -m -p -- /bin/sh
```

A partire da Docker Engine 25.0, il comando `docker debug` (sperimentale) fornisce un meccanismo nativo per iniettare una shell temporanea in container senza shell:

```bash
docker debug myapp
# Installa automaticamente una shell e strumenti diagnostici
# in un layer temporaneo che non modifica l'immagine
```

### Analisi dei Log e degli Eventi

Oltre ai log del container, il sistema degli eventi Docker fornisce informazioni cruciali sulle transizioni di stato:

```bash
# Stream eventi in tempo reale filtrati per tipo
docker events --filter type=container --filter event=die \
  --format '{{.Time}} {{.Actor.Attributes.name}} exitCode={{.Actor.Attributes.exitCode}}'

# Log con timestamp e follow per multipli container
docker compose logs -f --timestamps --tail=100 app worker

# Analisi dei crash: ultimi log prima del riavvio
docker logs --since 2m --until 1m myapp 2>&1 | tail -50
```

### Diagnostica di Rete

I problemi di rete nei container sono tra i più insidiosi da diagnosticare. Strumenti e tecniche specifiche includono:

```bash
# Verifica connettività DNS dal container
docker exec myapp nslookup api-service
docker exec myapp cat /etc/resolv.conf

# Tracciamento connessioni TCP con ss
docker exec myapp ss -tlnp

# Cattura pacchetti su interfaccia container dall'host
PID=$(docker inspect -f '{{.State.Pid}}' myapp)
sudo nsenter -t $PID -n -- tcpdump -i eth0 -nn port 8080 -w /tmp/capture.pcap

# Verifica regole iptables per il container
sudo iptables -t nat -L DOCKER -n --line-numbers
```

### Diagnostica delle Risorse e Performance

Quando un container mostra problemi di performance, è necessario analizzare l'utilizzo delle risorse a livello granulare:

```bash
# Statistiche real-time con formato personalizzato
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.BlockIO}}\t{{.PIDs}}"

# Dettaglio cgroup per il container
CONTAINER_ID=$(docker inspect -f '{{.Id}}' myapp)
cat /sys/fs/cgroup/system.slice/docker-${CONTAINER_ID}.scope/memory.current
cat /sys/fs/cgroup/system.slice/docker-${CONTAINER_ID}.scope/cpu.stat

# Profiling con perf dall'host
PID=$(docker inspect -f '{{.State.Pid}}' myapp)
sudo perf top -p $PID

# Tracciamento syscall con strace
sudo strace -fp $PID -c -S calls 2>&1 | head -30
```

### Pattern di Debugging in Produzione

In ambienti di produzione, il debugging deve essere non intrusivo e limitato nel tempo:

1. **Sidecar di diagnostica**: Aggiungere temporaneamente un container sidecar con strumenti di debug nella stessa rete e namespace PID del container problematico.

2. **Core dump automatici**: Configurare il kernel per salvare i core dump dei processi containerizzati:

```bash
# Configurazione host per core dump
echo '/tmp/core.%e.%p.%t' | sudo tee /proc/sys/kernel/core_pattern
# Nel container, assicurarsi che ulimit sia configurato
docker run --ulimit core=-1 myapp
```

3. **Ephemeral debug container** (Kubernetes): In contesti Kubernetes, utilizzare `kubectl debug` per creare container effimeri:

```bash
kubectl debug -it pod/myapp --image=nicolaka/netshoot --target=app
```

4. **Distributed tracing**: Integrare OpenTelemetry o Jaeger per tracciare le richieste attraverso i container senza necessità di accesso diretto:

```yaml
services:
  app:
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
      - OTEL_SERVICE_NAME=myapp
  jaeger:
    image: jaegertracing/all-in-one:1.57
    ports:
      - "16686:16686"  # UI
      - "4317:4317"    # OTLP gRPC
```

### Checklist di Troubleshooting

Quando un container non si avvia o crasha ripetutamente, seguire questa sequenza diagnostica sistematica:

| Step | Comando | Cosa verificare |
|------|---------|-----------------|
| 1 | `docker ps -a` | Stato e exit code del container |
| 2 | `docker logs <id>` | Messaggi di errore dell'applicazione |
| 3 | `docker inspect <id>` | Configurazione, mount, rete, health |
| 4 | `docker events --since 10m` | Sequenza di eventi (OOM, restart) |
| 5 | `docker stats` | Consumo risorse (CPU, memoria, I/O) |
| 6 | `docker exec <id> sh` | Accesso interattivo (se disponibile) |
| 7 | `docker run --entrypoint sh <img>` | Avvio senza entrypoint per debug |

Exit code comuni e significato:

| Exit Code | Significato | Causa probabile |
|-----------|-------------|-----------------|
| 0 | Uscita normale | Processo completato |
| 1 | Errore generico | Errore applicativo |
| 126 | Non eseguibile | Permessi o formato binario |
| 127 | Comando non trovato | PATH o binario mancante |
| 137 | SIGKILL (9) | OOM killer o `docker kill` |
| 139 | SIGSEGV (11) | Segmentation fault |
| 143 | SIGTERM (15) | `docker stop` (graceful) |

---

## Riepilogo

Docker è uno strumento potente che richiede una conoscenza approfondita per essere utilizzato efficacemente in ambienti di produzione. I concetti chiave trattati in questa guida coprono l'intera gamma delle competenze necessarie: dall'architettura interna del runtime alla creazione di Dockerfile ottimizzati, dalla gestione del networking e dello storage alla sicurezza, dal monitoraggio all'integrazione nelle pipeline CI/CD. La padronanza di queste tecniche permette di costruire infrastrutture containerizzate robuste, sicure, performanti e manutenibili nel tempo.

---

## Esercizi

1. **Dockerfile multi-stage con cache mount** — Partendo da un progetto Node.js o Python, scrivere un Dockerfile multi-stage che utilizzi `--mount=type=cache` per le dipendenze e produca un'immagine finale distroless. Misurare la differenza di tempo di build con e senza cache mount su 5 build consecutive.

2. **Build multi-architettura con buildx** — Configurare un builder `docker buildx` che produca un'immagine manifest list per `linux/amd64` e `linux/arm64`. Pushare su un registry locale (Harbor o registry:2), verificare con `docker manifest inspect` che entrambe le architetture siano presenti.

3. **Supply-chain security pipeline** — Creare uno script che esegua in sequenza: build dell'immagine, generazione SBOM con `syft`, scan vulnerabilità con `trivy`, firma dell'immagine con `cosign`. Bloccare il push al registry se `trivy` rileva vulnerabilità CRITICAL.

4. **Networking e service discovery** — Utilizzando Docker Compose, configurare tre servizi su due reti overlay separate con un servizio gateway che funge da ponte. Verificare l'isolamento di rete e implementare health check applicativi HTTP per ogni servizio.

5. **Hardening container in produzione** — Prendere un'immagine Docker esistente e applicare le 10 best practice di sicurezza: utente non-root, filesystem read-only, capabilities droppate, seccomp profile, limiti di risorse, label OCI. Validare con `docker-bench-security` e documentare i risultati.

---

## Letture e Riferimenti

### Documentazione ufficiale

- Docker Documentation — Multi-stage builds: <https://docs.docker.com/build/building/multi-stage/> (consultato: 2026-05-24)
- Docker Documentation — BuildKit: <https://docs.docker.com/build/buildkit/> (consultato: 2026-05-24)
- Docker Documentation — Security best practices: <https://docs.docker.com/develop/security-best-practices/> (consultato: 2026-05-24)
- Trivy — Container image scanner: <https://aquasecurity.github.io/trivy/> (consultato: 2026-05-24)
- Syft — SBOM generation: <https://github.com/anchore/syft> (consultato: 2026-05-24)
- OCI Image Spec — Annotations: <https://github.com/opencontainers/image-spec/blob/main/annotations.md> (consultato: 2026-05-24)
- Distroless images — GoogleContainerTools: <https://github.com/GoogleContainerTools/distroless> (consultato: 2026-05-24)

### Libri

- Stoneman, E. — *Docker in Action* (2a ed.), Manning, 2024
- Rice, L. — *Container Security*, O'Reilly, 2020
- McKendrick, R. — *Mastering Docker* (5a ed.), Packt, 2024

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione con questo modulo |
|--------|--------|-----------------------------|
| [05-kubernetes](05-kubernetes.md) | Kubernetes | Orchestrazione dei container Docker in cluster |
| [07-ci-cd](07-ci-cd.md) | CI/CD — Piattaforme e Pipeline | Build e push immagini Docker nelle pipeline |
| [08-monitoring-observability](08-monitoring-observability.md) | Monitoring e Observability | Monitoraggio dei container e dei daemon Docker |
| [13-sicurezza-piattaforme](13-sicurezza-piattaforme.md) | Sicurezza Piattaforme | Hardening container e runtime security |
| [15-secrets-management](15-secrets-management.md) | Secrets Management | Gestione secret nei build e nei container |
| [20-supply-chain-slsa-cosign](20-supply-chain-slsa-cosign.md) | Supply Chain, SLSA e Cosign | Firma immagini, SBOM e attestation SLSA |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **BuildKit** | Motore di build di nuova generazione per Docker che supporta build paralleli, mount cache e secret sicuri durante la costruzione delle immagini |
| **Multi-stage build** | Tecnica Dockerfile che utilizza più fasi di build per separare l'ambiente di compilazione da quello di runtime, riducendo la dimensione dell'immagine finale |
| **Distroless** | Immagini container minimali che contengono solo l'applicazione e le sue dipendenze runtime, senza shell, package manager o altri strumenti di sistema |
| **SBOM** | Software Bill of Materials — inventario completo di tutti i componenti, librerie e dipendenze contenuti in un'immagine container |
| **Buildx** | Plugin CLI Docker per la costruzione di immagini multi-piattaforma utilizzando builder remoti o emulazione QEMU |
| **Manifest list** | Struttura OCI che raggruppa più immagini per architetture diverse sotto un unico tag, consentendo il pull automatico dell'immagine corretta |
| **Layer caching** | Meccanismo di Docker che riutilizza i layer di build precedenti quando le istruzioni e il contesto non sono cambiati |
| **Rootless mode** | Modalità di esecuzione del daemon Docker senza privilegi root, riducendo la superficie di attacco |
| **Seccomp profile** | Profilo di sicurezza del kernel Linux che limita le system call disponibili per un container |
| **OCI** | Open Container Initiative — standard aperto per i formati di immagini container e runtime |
| **Health check** | Istruzione Dockerfile o configurazione Compose che verifica periodicamente lo stato di salute di un container |
| **Overlay network** | Rete virtuale Docker che consente la comunicazione tra container su host diversi in un cluster Swarm o Compose |
| **Image digest** | Hash SHA256 che identifica univocamente un'immagine container, garantendo l'immutabilità rispetto ai tag mutabili |
| **Init process** | Processo PID 1 all'interno del container che gestisce i segnali e il reaping dei processi zombie (es. tini, dumb-init) |
