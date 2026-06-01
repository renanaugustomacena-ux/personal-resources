---
corso: "GitHub e Git Actions"
fase: "2 — Configurazione Git"
modulo: "09"
titolo: "Git LFS, Submodules e Strategie Monorepo"
versione: "Git 2.47+ / Git LFS 3.5+"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01 — Fondamenti Git"
  - "07 — Git Internals: Oggetti e Refs"
  - "11 — Gitignore, Gitattributes e Configurazione"
obiettivi:
  - "Configurare e gestire Git LFS per file binari di grandi dimensioni"
  - "Utilizzare submodules e subtree per composizione di repository"
  - "Implementare sparse-checkout e partial clone per repository di grandi dimensioni"
  - "Valutare e adottare strategie monorepo con Nx, Turborepo o Bazel"
  - "Gestire Git worktree per lavoro parallelo su branch multipli"
tag: [git, lfs, submodules, subtree, monorepo, sparse-checkout, worktree, nx, bazel, scalar]
---

# Git LFS, Submodules e Strategie Monorepo — Guida Approfondita

> **Modulo 09** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Fondamenti Git](01-fondamenti-git.md), [Git Internals](07-git-interni-oggetti-refs.md), [Gitignore e Configurazione](11-gitignore-gitattributes-config.md)
>
> Al termine di questo modulo saprai:
> 1. Configurare e gestire Git LFS per file binari di grandi dimensioni
> 2. Utilizzare submodules e subtree per composizione di repository
> 3. Implementare sparse-checkout e partial clone per repository enormi
> 4. Valutare e adottare strategie monorepo con Nx, Turborepo o Bazel
> 5. Gestire Git worktree per lavoro parallelo su branch multipli
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **Git LFS per binary > 100MB.** GitHub charge bandwidth.
2. **Submodules: legacy ma alive. Subtree alternative.**
3. **Monorepo > polyrepo per code sharing.** Trade-off CI complexity.
4. **Bazel/Nx per build incrementale in monorepo.**


## Indice
- [Panoramica](#panoramica)
- [Git LFS: Large File Storage](#git-lfs-large-file-storage)
- [Git Submodules](#git-submodules)
- [Git Subtree](#git-subtree)
- [Alternative a Submodules e Subtree](#alternative-a-submodules-e-subtree)
- [Sparse-Checkout e Partial Clone](#sparse-checkout-e-partial-clone)
- [Strategie Monorepo](#strategie-monorepo)
- [CI/CD per Monorepo](#cicd-per-monorepo)
- [CODEOWNERS per Monorepo](#codeowners-per-monorepo)
- [Git Worktrees](#git-worktrees)
- [Scalar: Gestione di Repository Enormi](#scalar-gestione-di-repository-enormi)
- [Git Bundle: Trasferimento Offline](#git-bundle-trasferimento-offline)
- [Riferimento Comandi Completo](#riferimento-comandi-completo)
- [Anti-Pattern](#anti-pattern)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Riferimenti](#riferimenti)

---

## Panoramica

La gestione di repository di grandi dimensioni, con file binari pesanti, dipendenze tra progetti multipli o architetture monorepo, richiede strumenti e strategie avanzate che vanno oltre l'uso base di Git. Questa guida esplora le tecniche fondamentali per affrontare queste sfide: Git LFS per file binari di grandi dimensioni, submodules e subtree per la composizione di repository, sparse-checkout e partial clone per l'efficienza su repository enormi, strategie monorepo con tool come Nx, Turborepo e Bazel, e worktrees per il lavoro parallelo su più branch.

Comprendere quando e come usare ciascuno di questi strumenti è cruciale per mantenere un workflow efficiente in progetti di qualsiasi scala. La scelta sbagliata può portare a tempi di clone proibitivi, complicazioni nella CI/CD, difficoltà nella gestione delle dipendenze e frustrazione generalizzata nel team.

---

## Git LFS: Large File Storage

### Cos'è Git LFS

Git Large File Storage (LFS) è un'estensione di Git che sostituisce file di grandi dimensioni (immagini, video, dataset, modelli ML, binari compilati) con puntatori leggeri all'interno del repository Git, memorizzando il contenuto effettivo su un server separato. Questo mantiene il repository Git snello e veloce, anche quando il progetto include file di grandi dimensioni.

```bash
# Installazione
# macOS
brew install git-lfs

# Ubuntu/Debian
sudo apt install git-lfs

# Windows (incluso in Git for Windows)
# Oppure: choco install git-lfs

# Inizializzazione (una volta per utente)
git lfs install
# Updated git hooks.
# Git LFS initialized.
```

### Configurazione del Tracking

```bash
# Tracciare file per estensione
git lfs track "*.psd"
git lfs track "*.zip"
git lfs track "*.mp4"
git lfs track "*.bin"
git lfs track "*.h5"        # Modelli Keras/TensorFlow
git lfs track "*.onnx"      # Modelli ONNX
git lfs track "*.parquet"   # Dataset

# Tracciare file per directory
git lfs track "assets/videos/**"
git lfs track "data/raw/**"

# Tracciare un file specifico
git lfs track "models/production-model.bin"

# Visualizzare i pattern tracciati
git lfs track
# Listing tracked patterns
#     *.psd (.gitattributes)
#     *.zip (.gitattributes)

# I pattern vengono salvati in .gitattributes
cat .gitattributes
# *.psd filter=lfs diff=lfs merge=lfs -text
# *.zip filter=lfs diff=lfs merge=lfs -text
```

Il file `.gitattributes` è fondamentale e **deve essere committato** nel repository. È il meccanismo che comunica a tutti i clone quali file devono essere gestiti da LFS.

```bash
# IMPORTANTE: Committare .gitattributes
git add .gitattributes
git commit -m "chore: configurare Git LFS per file binari"
```

### Architettura di Git LFS

```
┌─────────────────────────────────────────────────────────────────────┐
│                      GIT LFS ARCHITECTURE                           │
│                                                                     │
│  Sviluppatore                                                       │
│  ┌──────────────┐    git add     ┌─────────────────────────────┐   │
│  │  large.psd   │──────────────►│  Clean Filter (LFS)         │   │
│  │  (50 MB)     │               │  1. Calcola SHA-256          │   │
│  └──────────────┘               │  2. Salva in .git/lfs/       │   │
│                                 │  3. Crea pointer file        │   │
│                                 └──────────┬──────────────────┘   │
│                                            │                       │
│                                 ┌──────────▼──────────────────┐   │
│                                 │  Pointer File (150 bytes)   │   │
│                                 │  version https://git-lfs... │   │
│                                 │  oid sha256:4d7a21...       │   │
│                                 │  size 52428800              │   │
│                                 └──────────┬──────────────────┘   │
│                                            │ git commit + push     │
│                   ┌────────────────────────┼────────────────────┐  │
│                   │                        │                    │  │
│          ┌────────▼─────────┐    ┌─────────▼────────────┐      │  │
│          │  Git Remote      │    │  LFS Server           │      │  │
│          │  (pointer files) │    │  (contenuto reale)    │      │  │
│          │  ~150 bytes each │    │  50 MB per versione   │      │  │
│          └────────┬─────────┘    └─────────┬────────────┘      │  │
│                   │                        │                    │  │
│                   │ git clone / checkout   │ git lfs pull       │  │
│                   │                        │                    │  │
│                   │  ┌─────────────────────▼────────────┐      │  │
│                   └──►  Smudge Filter (LFS)             │      │  │
│                      │  1. Legge pointer file           │      │  │
│                      │  2. Scarica contenuto da LFS     │      │  │
│                      │  3. Sostituisce con file reale   │      │  │
│                      └──────────────────────────────────┘      │  │
│                                                                │  │
└────────────────────────────────────────────────────────────────────┘
```

### Come Funziona Internamente

Quando un file tracciato da LFS viene aggiunto al repository, Git LFS:

1. Calcola l'hash SHA-256 del contenuto del file
2. Memorizza il contenuto nel store LFS locale (`.git/lfs/objects/`)
3. Crea un **pointer file** leggero che viene committato nel repository Git

```bash
# Contenuto di un pointer file LFS
git show HEAD:assets/logo.psd
# version https://git-lfs.github.com/spec/v1
# oid sha256:4d7a214614ab2935c943f9e0ff69d22eadbb8f32b1258daaa5e2ca24d17e2393
# size 12345678

# Visualizzare i file LFS nel repository
git lfs ls-files
# a1b2c3d4e5 * assets/logo.psd
# f6g7h8i9j0 * data/training-set.zip

# Stato dettagliato
git lfs status
```

### Migrazione di File Esistenti a LFS

Se file grandi sono già stati committati nella cronologia senza LFS, è possibile migrarli retroattivamente:

```bash
# Analizzare la cronologia per trovare file grandi
git lfs migrate info --everything
# migrate: Examining commits: 100% (500/500), done.
# *.zip   200 MB   15 files
# *.psd   150 MB   8 files
# *.mp4   500 MB   3 files

# Migrare file specifici in LFS (RISCRIVE LA CRONOLOGIA)
git lfs migrate import --include="*.psd,*.zip,*.mp4" --everything

# Migrare solo i nuovi commit (non riscrive la cronologia)
git lfs migrate import --include="*.psd" --no-rewrite

# Dopo la migrazione, forzare il push
git push --force-with-lease --all
git push --force-with-lease --tags

# Verificare la migrazione
git lfs ls-files --all
```

### Operazioni Quotidiane

```bash
# Clone con LFS (automatico se git lfs install è stato eseguito)
git clone https://github.com/org/repo.git

# Clone senza scaricare i file LFS (utile in CI)
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/org/repo.git
# Scaricare i file LFS selettivamente dopo
cd repo
git lfs pull --include="assets/needed-file.psd"

# Fetch e pull dei file LFS
git lfs fetch          # Scarica gli oggetti LFS
git lfs pull           # Scarica e applica gli oggetti LFS
git lfs fetch --all    # Scarica tutti gli oggetti LFS di tutti i branch

# Prune dei file LFS non necessari
git lfs prune          # Rimuove i file LFS locali non referenziati
git lfs prune --dry-run  # Mostra cosa verrebbe rimosso

# Informazioni sullo storage
git lfs env
```

### LFS e Storage Server

Git LFS necessita di un server per memorizzare i file. Le piattaforme principali includono il supporto nativo:

| Piattaforma | Storage Incluso | Bandwidth Inclusa |
|-------------|----------------|-------------------|
| GitHub Free | 1 GB | 1 GB/mese |
| GitHub Pro | 2 GB | 2 GB/mese |
| GitLab Free | 5 GB | 10 GB/mese |
| Bitbucket | 1 GB | 5 GB/mese |

```bash
# Verificare l'uso dello storage LFS su GitHub
gh api user | jq '.disk_usage'

# Configurare un server LFS personalizzato
git config lfs.url https://lfs.mycompany.com/org/repo
```

### File Locking: Editing Esclusivo per Asset Binari

Git LFS supporta un meccanismo di **file locking** progettato specificamente per file binari che non possono essere mergiati automaticamente (immagini PSD, scene Unity, mappe di gioco, modelli 3D). Il locking previene conflitti distruttivi: un solo utente alla volta può modificare un file bloccato, mentre gli altri lo vedono in sola lettura.

#### Configurare il Locking

Per abilitare il locking automatico su determinati file, si utilizza l'attributo `lockable` nel file `.gitattributes`:

```bash
# Rendere i file PSD lockable per default
# Il flag "lockable" rende il file read-only nel working tree
# finché non viene esplicitamente bloccato
echo "*.psd filter=lfs diff=lfs merge=lfs -text lockable" >> .gitattributes
echo "*.fbx filter=lfs diff=lfs merge=lfs -text lockable" >> .gitattributes
echo "*.unity filter=lfs diff=lfs merge=lfs -text lockable" >> .gitattributes
echo "*.uasset filter=lfs diff=lfs merge=lfs -text lockable" >> .gitattributes

git add .gitattributes
git commit -m "chore: configurare file locking per asset binari"
```

Quando un file è marcato come `lockable`, Git LFS lo imposta come **read-only** nel filesystem locale. Per modificarlo, lo sviluppatore deve prima acquisire il lock:

```bash
# Acquisire il lock su un file
git lfs lock assets/characters/hero.psd
# Locked assets/characters/hero.psd

# Ora il file è scrivibile localmente
# e nessun altro può acquisire lo stesso lock

# Visualizzare tutti i lock attivi nel repository
git lfs locks
# ID    Path                            Owner           Locked At
# 38    assets/characters/hero.psd      mario@team.com  2026-05-20 14:30:00

# Visualizzare i propri lock
git lfs locks --local

# Verificare lo stato dei lock rispetto al remote
git lfs locks --verify

# Dopo aver completato le modifiche
git add assets/characters/hero.psd
git commit -m "feat: aggiornare modello personaggio"
git push

# Rilasciare il lock
git lfs unlock assets/characters/hero.psd
# Unlocked assets/characters/hero.psd

# Rilasciare il lock tramite ID
git lfs unlock --id=38
```

#### Workflow Completo per Game Development

Nel contesto dello sviluppo di videogiochi, il file locking è particolarmente critico. Un workflow tipico per un team di artisti e sviluppatori segue questo ciclo:

```
┌──────────────────────────────────────────────────────────────────────┐
│              FILE LOCKING WORKFLOW — GAME DEVELOPMENT                │
│                                                                      │
│  Artista A                         Artista B                         │
│  ┌────────────┐                    ┌────────────┐                    │
│  │ git pull    │                    │ git pull    │                    │
│  │ git lfs lock│                    │ git lfs lock│                    │
│  │  hero.psd   │                    │  hero.psd   │                    │
│  │  ✅ OK      │                    │  ❌ RIFIUTATO│                   │
│  └─────┬──────┘                    │  "Locked by │                    │
│        │                           │   Artista A" │                    │
│        ▼                           └──────┬──────┘                    │
│  ┌────────────┐                           │                           │
│  │ Modifica   │                    ┌──────▼──────┐                    │
│  │ hero.psd   │                    │ Lavora su   │                    │
│  │ localmente │                    │ altri asset │                    │
│  └─────┬──────┘                    │ non bloccati│                    │
│        │                           └──────┬──────┘                    │
│        ▼                                  │                           │
│  ┌────────────┐                           │                           │
│  │ git add    │                           │                           │
│  │ git commit │                           │                           │
│  │ git push   │                           │                           │
│  └─────┬──────┘                           │                           │
│        │                                  │                           │
│        ▼                                  │                           │
│  ┌────────────┐                    ┌──────▼──────┐                    │
│  │ git lfs    │                    │ git lfs lock│                    │
│  │  unlock    │                    │  hero.psd   │                    │
│  │  hero.psd  │                    │  ✅ OK      │                    │
│  │  ✅ OK     │                    └─────────────┘                    │
│  └────────────┘                                                      │
│                                                                      │
│  Tipi di file comunemente bloccati nello sviluppo di giochi:        │
│  • .psd / .kra / .xcf     — Texture e concept art                   │
│  • .fbx / .blend / .obj   — Modelli 3D                              │
│  • .unity / .prefab       — Scene e prefab Unity                    │
│  • .uasset / .umap        — Asset e mappe Unreal Engine             │
│  • .wav / .ogg            — Audio master                            │
│  • .fmod / .wwise         — Progetti audio middleware               │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

Secondo survey dell'industria del game development (2025), i team che adottano workflow strutturati con file locking riportano una riduzione del 65% dei bug critici dovuti a conflitti su asset binari e un miglioramento del 47% nella velocità di delivery delle feature.

#### Gestione dei Lock Stale

Un problema comune è rappresentato dai lock "stale" — lock acquisiti da utenti che si sono dimenticati di rilasciarli, che sono in vacanza, o che hanno lasciato il team:

```bash
# Forzare lo sblocco di un file (richiede permessi admin)
git lfs unlock assets/old-scene.unity --force

# Script per identificare lock più vecchi di N giorni
git lfs locks --json | jq '
  [.[] | select(
    (now - (.locked_at | fromdateiso8601)) > (7 * 24 * 3600)
  )] | .[] | "\(.path) locked by \(.owner.name) since \(.locked_at)"
'
```

### Server LFS Personalizzati e Self-Hosting

Quando i limiti delle piattaforme cloud non sono sufficienti — per ragioni di costo, conformità normativa (GDPR, data residency), o semplicemente per la scala del progetto — è possibile configurare un server LFS self-hosted.

#### Implementazioni Open Source del Server LFS

Esistono diverse implementazioni open source del protocollo Git LFS Batch API:

| Implementazione | Linguaggio | Backend Storage | Note |
|----------------|------------|-----------------|------|
| **giftless** | Python 3 | S3, Azure Blob, GCS, locale | Modulare, pluggable, mantenuto attivamente |
| **Estranged.Lfs** | C# (.NET) | AWS Lambda + S3 | Serverless, costo zero a riposo |
| **lfs-server-go** | Go | S3, Azure, GCS, locale | Multi-backend, maturo |
| **rudolfs** | Rust | S3, locale | Leggero, performante |
| **git-lfs-s3-proxy** | Node.js | S3 | Proxy leggero, Batch API |

```bash
# Esempio: configurare giftless come server LFS
pip install giftless

# giftless.yaml — configurazione del server
cat > giftless.yaml << 'EOF'
AUTH_PROVIDERS:
  - giftless.auth.allow_anon:read_write

TRANSFER_ADAPTERS:
  basic:
    factory: giftless.transfer.basic_streaming:factory
    options:
      storage_class: giftless.storage.amazon_s3:AmazonS3Storage
      storage_options:
        bucket_name: my-lfs-bucket
        region: eu-west-1
EOF

# Avviare il server
giftless --config giftless.yaml

# Configurare il repository per usare il server custom
git config lfs.url https://lfs.mycompany.com/org/repo
```

#### Storage Object S3-Compatible

Con l'evoluzione dell'ecosistema object storage nel 2025-2026, MinIO è entrato in "maintenance mode" e nuove alternative sono emerse per lo storage S3-compatible self-hosted:

- **Garage**: raccomandato come successore di MinIO per deployment self-hosted. Un singolo binario Go senza dipendenze esterne (Docker, Kubernetes), ottimizzato per deployment distribuiti su hardware modesto
- **SeaweedFS**: sistema di storage distribuito per blob, oggetti e file, adatto a data lake e workload ad alta intensità
- **RustFS**: focalizzato su performance raw e ottimizzazione per data lake, AI e workload Big Data

```bash
# Esempio con Garage come backend LFS
# 1. Installare e configurare Garage
curl -fsSL https://garagehq.deuxfleurs.fr/install.sh | sh
garage server -c /etc/garage.toml

# 2. Creare un bucket per LFS
garage bucket create my-lfs-storage
garage key create lfs-service-account
garage bucket allow my-lfs-storage --read --write --key lfs-service-account

# 3. Configurare il server LFS per usare Garage come backend S3
# (nel file di configurazione del server LFS)
# endpoint: http://garage.internal:3900
# bucket: my-lfs-storage
# access_key: <key_id>
# secret_key: <secret_key>
```

#### Configurazione `.lfsconfig` per il Team

Per centralizzare la configurazione LFS e assicurarsi che tutto il team usi lo stesso server, si utilizza il file `.lfsconfig` nella root del repository:

```ini
# .lfsconfig — committato nel repository
[lfs]
    url = https://lfs.mycompany.com/org/repo
    locksverify = true
    # Timeout per operazioni di rete (secondi)
    activitytimeout = 30
    # Numero di upload/download paralleli
    concurrenttransfers = 8

[lfs "transfer"]
    maxretries = 5
    maxretrydelay = 10

[lfs "extension.sha256"]
    # Abilita il clean/smudge filter con SHA-256
    priority = 2
    oid = sha256
```

```bash
# Committare la configurazione
git add .lfsconfig
git commit -m "chore: centralizzare configurazione LFS per il team"
```

### LFS in CI/CD: Ottimizzazione della Bandwidth

In ambienti CI/CD, scaricare tutti i file LFS ad ogni build è uno spreco di bandwidth e tempo. Le strategie di ottimizzazione includono:

```bash
# Strategia 1: Skip totale di LFS nella CI (se i file non servono per il build)
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/org/repo.git
cd repo
# Eseguire build, lint, test — nessun file LFS scaricato

# Strategia 2: Fetch selettivo — solo i file necessari
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/org/repo.git
cd repo
git lfs pull --include="assets/icons/**"     # Solo le icone per il build
git lfs pull --exclude="*.mp4,*.wav"         # Escludi video e audio

# Strategia 3: Fetch con filtro per dimensione
git lfs fetch --recent   # Solo file modificati di recente

# Strategia 4: Cache LFS nella CI
# Configurare la CI per cachare .git/lfs/objects/ tra i run
# In GitHub Actions:
# - uses: actions/cache@v4
#   with:
#     path: .git/lfs
#     key: lfs-${{ hashFiles('.lfsconfig') }}-${{ github.sha }}
#     restore-keys: lfs-${{ hashFiles('.lfsconfig') }}-
```

Un workflow GitHub Actions ottimizzato per repository con LFS:

```yaml
# .github/workflows/build.yml
name: Build con LFS ottimizzato
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout senza LFS
        uses: actions/checkout@v4
        with:
          lfs: false  # Non scaricare file LFS durante il checkout

      - name: Cache LFS
        uses: actions/cache@v4
        with:
          path: .git/lfs
          key: lfs-${{ hashFiles('.lfsconfig') }}-${{ github.ref }}
          restore-keys: |
            lfs-${{ hashFiles('.lfsconfig') }}-

      - name: Fetch LFS selettivo
        run: |
          git lfs install --skip-smudge
          git lfs pull --include="assets/icons/**,assets/fonts/**"
          # Solo gli asset necessari per il build

      - name: Build
        run: npm run build
```

### Transfer Adapter Personalizzati

Git LFS supporta **transfer adapter** personalizzati che permettono di implementare protocolli di trasferimento custom. Questo è utile quando si vuole integrare LFS con sistemi di storage non standard o aggiungere funzionalità come compressione, crittografia o deduplica:

```bash
# Configurare un transfer adapter personalizzato
git config lfs.customtransfer.my-adapter.path /usr/local/bin/my-lfs-adapter
git config lfs.customtransfer.my-adapter.args "--config /etc/lfs-adapter.conf"
git config lfs.customtransfer.my-adapter.concurrent true
git config lfs.customtransfer.my-adapter.direction "both"

# L'adapter deve implementare il protocollo stdin/stdout di LFS:
# 1. Riceve eventi JSON su stdin (init, upload, download, terminate)
# 2. Risponde con eventi JSON su stdout (complete, progress)
```

Casi d'uso per transfer adapter personalizzati:
- **Compressione**: comprimere i file prima del trasferimento per ridurre la bandwidth
- **Crittografia**: crittografare i file LFS at-rest e in-transit per conformità normativa
- **Deduplica cross-repository**: condividere lo storage LFS tra più repository
- **Mirroring**: replicare automaticamente i file LFS su più datacenter
- **Throttling**: limitare la bandwidth usata dai trasferimenti LFS per non saturare la rete

### Git LFS 3.x: Evoluzioni Recenti (2025-2026)

Le release della serie Git LFS 3.x hanno introdotto miglioramenti significativi in termini di performance, compatibilità e funzionalità. La serie 3.5+ - 3.7+ rappresenta un salto di maturità per lo strumento, con ottimizzazioni che impattano sia gli sviluppatori individuali sia le pipeline CI/CD su larga scala.

#### Performance di Migrazione

Le versioni recenti introducono una **cache in-memory configurabile** per il pattern matching dei path dei file. Quando si esegue `git lfs migrate` su repository con cronologie lunghe (centinaia di migliaia di commit), Git LFS deve valutare ogni file nella cronologia contro i pattern definiti in `.gitattributes`. La cache riduce significativamente il tempo necessario per queste operazioni, evitando la rivalutazione ripetuta degli stessi pattern:

```bash
# Migrazione con le versioni recenti: significativamente più veloce
# grazie alla cache interna di pattern matching
git lfs migrate info --everything --above=5mb
# La cache evita la rivalutazione ripetuta dei pattern su file ricorrenti

# Forzare il re-download degli oggetti LFS (utile per troubleshooting)
git lfs fetch --all --force
# Le versioni recenti supportano --force per invalidare la cache locale

# Output JSON per integrazione con tool esterni
git lfs fetch --json
# Produce output strutturato con URL e metadati HTTP per ogni oggetto
# Utile per pipeline CI che necessitano di logging dettagliato
```

#### Compatibilità e Robustezza

Le versioni 3.6+ e 3.7+ migliorano la gestione degli errori di rete e la compatibilità cross-platform:

- **Retry su HTTP 429**: Git LFS ora gestisce correttamente tutte le risposte HTTP 429 (Too Many Requests), rispettando l'header `Retry-After` del server. Questo è critico per ambienti con rate limiting aggressivo (GitHub API, server LFS custom dietro CDN).
- **Supporto .netrc su Windows**: Git LFS utilizza gli stessi file `.netrc` di Git e curl su Windows, semplificando la configurazione dell'autenticazione in ambienti enterprise.
- **Symlink per lo storage oggetti**: È ora possibile usare symlink per la directory di storage degli oggetti Git durante le migrazioni LFS, permettendo di eseguire migrazioni su filesystem temporanei senza copiare gli oggetti.
- **Certificati CA su macOS**: Risolti problemi di verifica TLS quando sono configurati certificati CA custom, eliminando errori spurii durante i trasferimenti.

#### Supporto Piattaforme Estese

La serie 3.7.x è la prima per cui vengono forniti pacchetti e supporto per distribuzioni Linux basate su **RHEL 10** (Red Hat Enterprise Linux 10), come Rocky Linux 10 e AlmaLinux 10. Questo amplia la compatibilità in ambienti enterprise che richiedono distribuzioni Linux certificate.

```bash
# Verificare la versione installata
git lfs version
# git-lfs/3.7.x (GitHub; linux amd64; go 1.23.x)

# Aggiornare Git LFS alla versione più recente
# Ubuntu/Debian
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
sudo apt install git-lfs

# macOS
brew upgrade git-lfs

# Verificare che gli hook siano aggiornati alla versione corrente
git lfs install --force
```

### LFS e File Locking: Limitazioni Conosciute e Workaround

Il file locking di Git LFS, pur essendo fondamentale per il workflow con file binari, presenta limitazioni strutturali che è importante conoscere per evitare problemi in produzione:

1. **Lock basato su path, non su contenuto**: Il lock opera sul path del file, non sul suo contenuto. Se un file viene rinominato o spostato, il lock originale non segue il file. Bisogna sbloccare il vecchio path e bloccare il nuovo.

2. **Lock cross-branch**: I lock sono globali nel repository — un file bloccato su un branch è bloccato su **tutti** i branch. Questo significa che `git merge` fallisce se tenta di modificare un file con lock attivo posseduto da un altro utente, anche se la modifica è upstream. Il workaround è coordinare con il team per sbloccare prima del merge.

3. **Nessun lock gerarchico**: Non è possibile bloccare un'intera directory. Ogni file deve essere bloccato individualmente. Per workflow dove un artista lavora su un'intera scena con dozzine di file, questo richiede script di automazione:

```bash
# Script per bloccare tutti i file di una scena
find assets/scenes/level-01/ -name "*.unity" -o -name "*.prefab" \
  -o -name "*.asset" | while read file; do
    git lfs lock "$file"
done

# Script per sbloccare tutti i propri lock
git lfs locks --local --json | jq -r '.[].path' | while read file; do
    git lfs unlock "$file"
done
```

4. **Confronto con Perforce**: Il file locking di Git LFS è meno robusto del meccanismo di exclusive checkout di Perforce (p4 edit), che i team di game development conoscono bene. Per team che migrano da Perforce a Git, le differenze nel modello di locking sono una fonte comune di frustrazione. Tool come **Anchorpoint** e **PlasticSCM** (ora Unity Version Control) offrono layer aggiuntivi sopra Git LFS che forniscono un'esperienza di locking più simile a Perforce.

---

## Git Submodules

### Cos'è un Submodule

Un Git submodule è un repository Git annidato all'interno di un altro repository. Il repository padre traccia un commit specifico del submodule, non il suo contenuto. Questo permette di includere e gestire repository esterni come dipendenze, mantenendo storie separate.

### Come Funzionano Internamente i Submodules

```
┌──────────────────────────────────────────────────────────────┐
│                SUBMODULE REFERENCE CHAIN                      │
│                                                              │
│  Repository Padre (progetto/)                                │
│  ┌────────────────────────────┐                              │
│  │  .gitmodules               │                              │
│  │  ├─ submodule "libs/lib"   │                              │
│  │  │  path = libs/lib        │  Configurazione              │
│  │  │  url = https://...      │  (committata)                │
│  │  └─ branch = main          │                              │
│  │                            │                              │
│  │  Index (gitlink)           │                              │
│  │  ├─ libs/lib → abc1234     │  Commit specifico           │
│  │  │  (mode: 160000)         │  tracciato dal padre        │
│  │  └─ tipo: "commit" object  │                              │
│  │                            │                              │
│  │  .git/modules/libs/lib/    │                              │
│  │  └─ (repository Git del    │  Clone locale del           │
│  │     submodule, completo)   │  submodule                  │
│  └────────────────────────────┘                              │
│                                                              │
│  Quando fai "git submodule update":                         │
│  1. Legge .gitmodules per la URL                            │
│  2. Legge l'index per il commit target (abc1234)            │
│  3. Clone/fetch nel .git/modules/                           │
│  4. Checkout di abc1234 nel worktree (libs/lib/)            │
│  5. Il submodule è in stato DETACHED HEAD                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Aggiungere un Submodule

```bash
# Aggiungere un submodule
git submodule add https://github.com/org/libreria.git libs/libreria

# Questo crea:
# - Una entry in .gitmodules
# - Una entry nell'index (gitlink) che punta al commit specifico
# - Un clone del repository in libs/libreria/

cat .gitmodules
# [submodule "libs/libreria"]
#     path = libs/libreria
#     url = https://github.com/org/libreria.git

# Aggiungere con branch specifico
git submodule add -b main https://github.com/org/libreria.git libs/libreria

# Committare l'aggiunta del submodule
git add .gitmodules libs/libreria
git commit -m "chore: aggiungere libreria come submodule"
```

### Clonare un Repository con Submodules

```bash
# Metodo 1: Clone con inizializzazione automatica
git clone --recurse-submodules https://github.com/org/progetto.git

# Metodo 2: Inizializzare dopo il clone
git clone https://github.com/org/progetto.git
cd progetto
git submodule init
git submodule update

# Shortcut per init + update
git submodule update --init

# Con submodules annidati (ricorsivo)
git submodule update --init --recursive

# Configurare il clone ricorsivo come default
git config --global submodule.recurse true
```

### Aggiornare i Submodules

```bash
# Aggiornare un submodule al commit più recente del suo branch
cd libs/libreria
git fetch origin
git checkout main
git pull origin main
cd ../..

# Oppure dal repository padre
git submodule update --remote libs/libreria

# Aggiornare tutti i submodules
git submodule update --remote

# Dopo l'aggiornamento, committare il nuovo riferimento
git add libs/libreria
git commit -m "chore: aggiornare libreria al commit più recente"

# Aggiornare con merge (invece di checkout)
git submodule update --remote --merge

# Aggiornare con rebase
git submodule update --remote --rebase
```

### Workflow con Submodules

```bash
# Vedere lo stato dei submodules
git submodule status
# +a1b2c3d libs/libreria (v1.2.0-3-ga1b2c3d)
# Il + indica che il submodule non è al commit atteso

# Eseguire un comando in tutti i submodules
git submodule foreach 'git status'
git submodule foreach 'git pull origin main'
git submodule foreach --recursive 'git clean -fd'

# Deinizializzare un submodule (mantiene la directory)
git submodule deinit libs/libreria

# Rimuovere completamente un submodule
git submodule deinit libs/libreria
git rm libs/libreria
rm -rf .git/modules/libs/libreria
git commit -m "chore: rimuovere submodule libreria"
```

### Pitfalls Comuni dei Submodules

1. **Detached HEAD**: I submodules sono sempre in stato detached HEAD dopo `git submodule update`. Per lavorare nel submodule, è necessario fare checkout di un branch.

```bash
cd libs/libreria
git checkout main   # Passare dal detached HEAD al branch
# Ora è possibile fare commit e push nel submodule
```

2. **Dimenticare di pushare il submodule**: Se si committano modifiche nel submodule e nel progetto padre senza pushare prima il submodule, altri sviluppatori non potranno clonare il commit referenziato.

```bash
# Push con verifica dei submodules
git push --recurse-submodules=check  # Fallisce se i submodules non sono pushati
git push --recurse-submodules=on-demand  # Pusha automaticamente i submodules
```

3. **Conflitti sulle reference dei submodules**: Quando due branch modificano la reference a un submodule diversamente.

---

## Git Subtree

### Cos'è Git Subtree

Git subtree è un'alternativa ai submodules che integra il codice di un repository esterno direttamente nel repository principale. A differenza dei submodules, non richiede comandi speciali per il clone o l'aggiornamento — il codice è semplicemente parte del repository.

### Aggiungere un Subtree

```bash
# Aggiungere un remote per il repository esterno
git remote add libreria https://github.com/org/libreria.git

# Aggiungere il subtree (con squash per comprimere la cronologia)
git subtree add --prefix=libs/libreria libreria main --squash

# Senza squash (preserva tutta la cronologia)
git subtree add --prefix=libs/libreria libreria main
```

### Aggiornare un Subtree

```bash
# Pull delle modifiche dal repository esterno
git subtree pull --prefix=libs/libreria libreria main --squash

# Push delle modifiche locali al repository esterno
git subtree push --prefix=libs/libreria libreria main
```

### Split: Estrarre un Subtree

Il comando `split` estrae la cronologia di una sottodirectory in un branch separato, utile per pubblicare una parte del repository come progetto indipendente:

```bash
# Estrarre la cronologia di una directory
git subtree split --prefix=libs/libreria -b libreria-standalone

# Pushare il branch estratto a un repository separato
git push libreria libreria-standalone:main
```

### Subtree vs Submodule: Confronto

| Aspetto | Submodule | Subtree |
|---------|-----------|---------|
| Clone | Richiede `--recurse-submodules` | Clone normale |
| Complessità | Alta (stato detached HEAD, init/update) | Bassa (codice integrato) |
| Cronologia | Separata | Integrata (o squashata) |
| Dimensione repo | Piccola (solo reference) | Più grande (include il codice) |
| Push upstream | Facile (push nel submodule) | `git subtree push` |
| Workflow CI | Richiede configurazione speciale | Funziona nativamente |
| Versioning | Commit specifico referenziato | Merge/squash nella cronologia |

---

## Alternative a Submodules e Subtree

Oltre ai submodules e subtree nativi di Git, l'ecosistema ha prodotto strumenti alternativi che risolvono problemi simili con approcci diversi. La scelta dipende dal workflow del team, dalla frequenza di aggiornamento delle dipendenze e dalla complessità che il team è disposto a gestire.

### Git Subrepo

**Git subrepo** è un plugin Git che mantiene l'intero workflow all'interno di un singolo repository, evitando i problemi del detached HEAD tipici dei submodules e rendendo gli aggiornamenti più prevedibili. Il codice del sub-progetto viene incorporato direttamente nel repository padre (simile a subtree), ma con metadati più puliti e un workflow semplificato:

```bash
# Installazione di git-subrepo
git clone https://github.com/ingydotnet/git-subrepo /opt/git-subrepo
echo 'source /opt/git-subrepo/.rc' >> ~/.bashrc

# Clonare un repository esterno come subrepo
git subrepo clone https://github.com/org/libreria.git libs/libreria

# Aggiornare il subrepo (pull delle modifiche upstream)
git subrepo pull libs/libreria

# Pushare modifiche locali al repository upstream
git subrepo push libs/libreria

# Visualizzare lo stato
git subrepo status
```

A differenza dei submodules, `git subrepo` non richiede comandi speciali durante il clone — il codice è già presente nel repository. A differenza di subtree, il suo formato di metadati (file `.gitrepo`) è più leggero e le operazioni di push/pull sono più intuitive.

### Josh (Just One Single History)

**Josh** è un proxy Git trasparente che permette di lavorare con sottodirectory di un repository come se fossero repository indipendenti, senza duplicazione. Josh può fare tutto ciò che fanno i submodules, ma in modo più veloce e semplice:

```bash
# Esempio: clonare solo una sottodirectory di un monorepo
# tramite Josh proxy
git clone https://josh.example.com/org/monorepo.git:/apps/frontend.git frontend-solo

# Lavorare normalmente nel repository "virtuale"
cd frontend-solo
echo "nuova feature" > feature.js
git add . && git commit -m "feat: nuova feature"

# Il push viene tradotto da Josh nella posizione corretta del monorepo
git push origin main
```

Josh opera come un proxy tra il client Git e il server Git originale, traducendo i path in tempo reale. Non modifica il repository originale e non aggiunge metadati. Il vantaggio principale è che permette workflow polyrepo su una struttura monorepo, il meglio di entrambi i mondi.

### Automazione degli Aggiornamenti con Dependabot e Renovate

Per i team che usano submodules, l'aggiornamento manuale è una fonte di ritardi e dimenticanze. **Dependabot** (integrato in GitHub) e **Renovate** (open source, multi-piattaforma) automatizzano gli aggiornamenti creando pull request quando il submodule upstream pubblica nuovi commit:

```yaml
# .github/dependabot.yml — Aggiornamento automatico dei submodules
version: 2
updates:
  - package-ecosystem: "gitsubmodule"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Europe/Rome"
    commit-message:
      prefix: "chore"
      include: "scope"
    labels:
      - "dependencies"
      - "submodule-update"
    reviewers:
      - "team-platform"
```

```json
// renovate.json — Alternativa con Renovate
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "gitSubmodules": {
    "enabled": true
  },
  "packageRules": [
    {
      "matchManagers": ["git-submodules"],
      "schedule": ["before 10am on monday"],
      "automerge": false,
      "labels": ["submodule-update"]
    }
  ]
}
```

### Sicurezza dei Submodules: Verificare le URL

I submodules rappresentano un vettore di attacco se le URL non vengono verificate. Un attaccante che riesce a modificare `.gitmodules` può redirigere il clone verso un repository malevolo. Misure di mitigazione:

```bash
# Restringere i protocolli consentiti per il clone dei submodules
git config --global protocol.allow never
git config --global protocol.https.allow always
git config --global protocol.ssh.allow always
# Blocca protocolli non sicuri come file://, git://, ext::

# Verificare le URL dei submodules prima di init/update
git submodule--helper resolve-relative-url > /dev/null 2>&1 || echo "URL sospetta"

# Abilitare la verifica delle firme sui commit dei submodules
git config --global submodule.fetchJobs 4
git config --global diff.submodule log

# Audit: controllare tutte le URL dei submodules
git config -f .gitmodules --get-regexp '\.url$'
```

### Confronto Completo delle Alternative

| Aspetto | Submodule | Subtree | Subrepo | Josh | Package Manager |
|---------|-----------|---------|---------|------|-----------------|
| Clone semplice | No | Si | Si | Si | Si |
| Push upstream | Facile | Complesso | Facile | Trasparente | N/A |
| Dimensione repo | Minima | Grande | Grande | Minima | Minima |
| Metadati extra | `.gitmodules` | Nessuno | `.gitrepo` | Nessuno | `package.json` etc. |
| Curva apprendimento | Alta | Media | Bassa | Bassa | Nota |
| Versioning preciso | Si | No | Si | Si | Si |
| Adatto a frequenti update | No | No | Si | Si | Si |
| Maturo/stabile | Si | Si | Medio | Medio | Si |

La raccomandazione generale nel 2025-2026 è: se la dipendenza è un **pacchetto pubblicato** (npm, PyPI, Maven, crates.io), usare il package manager nativo. Se è **codice condiviso non pubblicato** all'interno della stessa organizzazione, considerare un monorepo. Submodules e subtree hanno ancora il loro posto per scenari specifici come vendor code, fork personalizzati, o integrazione di repository legacy dove un package manager non è praticabile.

---

## Sparse-Checkout e Partial Clone

### Sparse-Checkout

Lo sparse-checkout permette di lavorare con solo un sottoinsieme dei file del repository. È essenziale per monorepo di grandi dimensioni dove ogni sviluppatore lavora solo su una porzione del codice.

```bash
# Abilitare sparse-checkout (cone mode, raccomandato)
git sparse-checkout init --cone

# Specificare le directory da includere
git sparse-checkout set apps/frontend libs/shared

# Aggiungere directory
git sparse-checkout add apps/api

# Visualizzare la configurazione
git sparse-checkout list
# apps/frontend
# apps/api
# libs/shared

# Disabilitare sparse-checkout (scaricare tutti i file)
git sparse-checkout disable
```

Il cone mode (predefinito da Git 2.37) usa un modello semplificato basato su directory, significativamente più performante del pattern matching generico:

```bash
# Cone mode: specifica directory complete
git sparse-checkout set src/app src/libs

# Non-cone mode (pattern generici, più lento)
git sparse-checkout init --no-cone
git sparse-checkout set '*.md' 'src/**/*.ts' '!src/**/*.test.ts'
```

### Partial Clone

Il partial clone (introdotto in Git 2.22) permette di clonare un repository senza scaricare tutti gli oggetti. Gli oggetti mancanti vengono scaricati on-demand quando necessario.

```bash
# Clone senza blob (scarica blob on-demand)
git clone --filter=blob:none https://github.com/org/monorepo.git

# Clone senza blob grandi (scarica solo blob < 1MB)
git clone --filter=blob:limit=1m https://github.com/org/monorepo.git

# Clone senza tree (scarica tree on-demand) — più aggressivo
git clone --filter=tree:0 https://github.com/org/monorepo.git

# Combinare partial clone con sparse-checkout
git clone --filter=blob:none --sparse https://github.com/org/monorepo.git
cd monorepo
git sparse-checkout set apps/frontend libs/shared
```

### Treeless Clone

Il treeless clone (`--filter=tree:0`) è il più aggressivo: non scarica nessun tree object durante il clone. È ideale per CI/CD dove si lavora solo con il checkout corrente.

```bash
# Clone treeless per CI
git clone --filter=tree:0 --single-branch https://github.com/org/repo.git

# Questo scarica solo i commit e gli oggetti necessari per il checkout
# Drasticamente più veloce per repository grandi
```

### Sparse-Index: Ottimizzazione dell'Index per Monorepo

Lo **sparse-index** è un'ottimizzazione introdotta a partire da Git 2.32 che riduce drasticamente le dimensioni dell'index (il file `.git/index`) nei repository con sparse-checkout attivo. Normalmente, l'index contiene un'entry per **ogni** file tracciato nel repository, anche quelli esclusi dallo sparse-checkout. In un monorepo con milioni di file, questo significa un index di centinaia di MB che deve essere letto e scritto ad ogni operazione `git status`, `git add`, `git commit`.

Con lo sparse-index abilitato, Git sostituisce le entry dei file fuori dal cono sparse con **entry di directory** compresse. Invece di elencare ogni singolo file nella directory `apps/backend/`, l'index memorizza una singola entry per l'intera directory. Questo riduce l'index da potenzialmente milioni di entry a poche migliaia, con miglioramenti drammatici nelle performance:

```bash
# Abilitare sparse-index durante l'inizializzazione
git sparse-checkout init --cone --sparse-index

# Oppure abilitarlo su un repository esistente con sparse-checkout
git sparse-checkout set --sparse-index apps/frontend libs/shared

# Verificare che lo sparse-index sia attivo
git config core.sparseCheckoutCone
# true

# Disabilitare lo sparse-index (torna all'index completo)
git sparse-checkout init --cone --no-sparse-index
```

I benchmark di GitHub sul repository interno di Microsoft mostrano miglioramenti significativi: `git status` passa da 3-5 secondi a meno di 0.5 secondi, `git add` e `git commit` beneficiano di riduzioni simili. L'impatto è proporzionale alla differenza tra il numero totale di file nel repository e il numero di file nel cono sparse.

### Workflow Combinato: Partial Clone + Sparse-Checkout + Sparse-Index

La combinazione di partial clone, sparse-checkout in cone mode e sparse-index rappresenta la configurazione ottimale per lavorare su monorepo di grandi dimensioni. Questo workflow minimizza sia il trasferimento di rete che l'uso di disco e memoria locale, permettendo a uno sviluppatore di iniziare a lavorare in pochi secondi anche su un repository con milioni di file:

```bash
# PASSO 1: Clone parziale senza blob
# Scarica solo i metadati (commit, tree), nessun contenuto di file
git clone --filter=blob:none --sparse https://github.com/org/mega-monorepo.git
cd mega-monorepo

# PASSO 2: Configurare sparse-checkout con sparse-index
# Materializza solo le directory su cui si lavora
git sparse-checkout init --cone --sparse-index
git sparse-checkout set apps/my-app libs/shared libs/ui-components

# PASSO 3: Verificare il risultato
ls apps/           # Solo my-app è presente
ls libs/           # Solo shared e ui-components
git sparse-checkout list
# apps/my-app
# libs/shared
# libs/ui-components

# PASSO 4: Lavorare normalmente
# Git scarica i blob on-demand quando necessario
git log --oneline apps/my-app/    # I blob per il diff vengono scaricati al volo
git blame apps/my-app/src/main.ts # Il blob viene scaricato per questo file

# PASSO 5: Espandere il cono se serve un'altra directory
git sparse-checkout add apps/admin-panel
# I blob di apps/admin-panel vengono scaricati on-demand

# PASSO 6: Pre-fetch per lavorare offline
# Se si prevede di lavorare senza rete, scaricare esplicitamente i blob
git lfs fetch --include="apps/my-app/**"
```

```
┌────────────────────────────────────────────────────────────────────┐
│         PARTIAL CLONE + SPARSE-CHECKOUT + SPARSE-INDEX             │
│                                                                    │
│  Repository Remoto (500K file, 50 GB)                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  apps/frontend/  apps/backend/  apps/mobile/  apps/admin/   │  │
│  │  libs/shared/    libs/auth/     libs/ui/      libs/utils/   │  │
│  │  tools/          docs/          infra/        scripts/      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Clone Locale (solo metadati + cono sparse)                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  .git/                                                      │  │
│  │  ├── objects/   ← solo commit + tree + blob on-demand       │  │
│  │  └── index     ← sparse-index (poche K entry, non 500K)    │  │
│  │                                                              │  │
│  │  apps/frontend/ ← file presenti, blob scaricati             │  │
│  │  libs/shared/   ← file presenti, blob scaricati             │  │
│  │                                                              │  │
│  │  (tutto il resto: NON materializzato nel working tree)      │  │
│  │  (blob scaricati on-demand solo quando servono per log,     │  │
│  │   diff, blame, ecc.)                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Risultato:                                                        │
│  • Clone: ~10 secondi (vs 30+ minuti per clone completo)          │
│  • Disco: ~500 MB (vs 50 GB)                                      │
│  • git status: <0.5s (vs 5-10s senza sparse-index)                │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

Questo approccio è raccomandato da GitHub e Microsoft come la configurazione standard per sviluppatori che lavorano su monorepo di grandi dimensioni. Scalar automatizza questa configurazione: `scalar clone` è equivalente a eseguire manualmente tutti i passi sopra descritti, con l'aggiunta della manutenzione schedulata in background.

---

## Strategie Monorepo

### Cos'è un Monorepo

Un monorepo è un singolo repository che contiene il codice di più progetti, librerie o servizi. Aziende come Google, Meta, Microsoft e Uber usano monorepo su scala enorme. I vantaggi includono la condivisione semplificata del codice, refactoring atomici cross-progetto e un singolo punto di verità per le dipendenze.

### Nx

**Nx** è un sistema di build intelligente progettato per monorepo JavaScript/TypeScript. Offre caching distribuito, esecuzione parallela dei task e analisi delle dipendenze.

```bash
# Creare un nuovo workspace Nx
npx create-nx-workspace@latest myorg

# Struttura tipica di un workspace Nx
myorg/
├── apps/
│   ├── frontend/          # Applicazione React/Angular/Vue
│   ├── api/               # Server Node.js
│   └── mobile/            # React Native
├── libs/
│   ├── shared/
│   │   ├── ui/            # Componenti UI condivisi
│   │   ├── utils/         # Utility condivise
│   │   └── types/         # Tipi TypeScript condivisi
│   ├── frontend/
│   │   └── feature-auth/  # Feature specifica del frontend
│   └── api/
│       └── data-access/   # Layer dati dell'API
├── tools/                  # Script e generatori personalizzati
├── nx.json                 # Configurazione Nx
├── package.json
└── tsconfig.base.json
```

```json
// nx.json
{
  "targetDefaults": {
    "build": {
      "dependsOn": ["^build"],
      "cache": true
    },
    "test": {
      "cache": true
    },
    "lint": {
      "cache": true
    }
  },
  "namedInputs": {
    "default": ["{projectRoot}/**/*"],
    "production": ["default", "!{projectRoot}/**/*.spec.ts"]
  },
  "defaultBase": "main"
}
```

```bash
# Comandi Nx
nx build frontend              # Build di un progetto specifico
nx test api                    # Test di un progetto specifico
nx affected --target=build     # Build solo dei progetti affected
nx affected --target=test      # Test solo dei progetti affected
nx graph                       # Visualizzare il grafo delle dipendenze

# Esecuzione parallela
nx run-many --target=build --all --parallel=5

# Cache distribuita con Nx Cloud
nx connect-to-nx-cloud
```

#### Nx Crystal Plugins e Task Inferiti

A partire da Nx 18, il sistema **Project Crystal** permette ai plugin di **inferire automaticamente** i task dalla configurazione degli strumenti del progetto, eliminando la necessità di definire manualmente ogni target in `project.json`. Per esempio, se un progetto ha un file `vite.config.ts`, il plugin `@nx/vite` registra automaticamente i target `build`, `serve`, `test` e `preview`:

```json
// project.json — con Crystal, i target vengono inferiti
// Non serve più definire manualmente:
{
  "name": "frontend",
  "sourceRoot": "apps/frontend/src",
  "projectType": "application"
  // I target build, serve, test, lint sono INFERITI
  // dai rispettivi file di configurazione (vite.config.ts, etc.)
}
```

```bash
# Visualizzare i target inferiti per un progetto
nx show project frontend --web

# Ogni target mostra una "technology label"
# (Playwright, Cypress, Vite, Webpack, etc.)
# per identificare rapidamente quale strumento lo gestisce
```

#### Nx 21+: Task Continui e Terminal UI

In Nx 21 (2026), i **continuous task** permettono di gestire processi long-running (come dev server) come dipendenze di altri task. Un task marcato come `"continuous": true` non blocca i task dipendenti in attesa della sua terminazione:

```json
// nx.json — configurazione task continui
{
  "targetDefaults": {
    "e2e": {
      "dependsOn": ["serve"],
      "cache": true
    },
    "serve": {
      "continuous": true  // Non attende che serve termini
    }
  }
}
```

La nuova **Terminal UI** di Nx 21 fornisce una dashboard interattiva nel terminale per monitorare l'esecuzione dei task in parallelo, il progresso dei build e i cache hit in tempo reale.

#### Distributed Task Execution (Nx Agents)

Nx Agents distribuisce l'esecuzione dei task su più macchine CI in modo intelligente. Nel 2025-2026, il sistema include il **resource tracking** che registra l'uso di CPU e RAM per ogni task, permettendo di determinare in tempo reale se un agente ha capacità per altri task:

```yaml
# .github/workflows/ci.yml — Nx Agents con GitHub Actions
name: CI
on: push

jobs:
  main:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: nrwl/nx-set-shas@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: npx nx-cloud start-ci-run --distribute-on="5 linux-medium-js"
      - run: npx nx affected -t lint test build e2e-ci
```

Il sistema analizza automaticamente il profilo di risorse di ogni task (build pesante vs lint leggero) e assegna i task agli agenti in modo da minimizzare il tempo di idle e massimizzare l'utilizzo hardware, riducendo i tempi CI senza aggiungere macchine.

### Turborepo

**Turborepo** è un sistema di build ad alte performance per monorepo JavaScript/TypeScript, acquisito da Vercel. È più semplice di Nx ma estremamente efficace per il caching e l'esecuzione parallela.

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**", "!.next/cache/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "inputs": ["src/**/*.tsx", "src/**/*.ts", "test/**/*.ts"]
    },
    "lint": {
      "dependsOn": ["^build"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

```bash
# Comandi Turborepo
turbo build                    # Build di tutti i pacchetti
turbo test --filter=frontend   # Test di un pacchetto specifico
turbo build --filter=...[HEAD~1]  # Build dei pacchetti modificati
turbo build --dry-run          # Mostra cosa verrebbe eseguito
```

#### Turborepo Boundaries (Sperimentale, 2025-2026)

Le **Boundaries** sono un meccanismo per imporre regole architetturali su quali pacchetti possono dipendere da quali altri, prevenendo dipendenze accidentali che violano la struttura del monorepo:

```json
// turbo.json — con boundaries
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "globalPassThroughEnv": ["NODE_ENV", "CI"],
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**", "!.next/cache/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "inputs": ["src/**/*.tsx", "src/**/*.ts", "test/**/*.ts"]
    },
    "lint": {},
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

> **Nota**: a partire da Turborepo 2.x, la chiave `pipeline` è stata rinominata in `tasks`. La configurazione sopra utilizza lo schema aggiornato.

#### Remote Caching con Vercel

Turborepo offre remote caching integrato con Vercel, disponibile gratuitamente su tutti i piani, anche senza fare hosting su Vercel. Il caching remoto permette di condividere gli artefatti di build tra sviluppatori e CI, riducendo drasticamente i tempi di build (tipicamente 60-80% su cache hit):

```bash
# Collegare il workspace a Vercel per il remote caching
npx turbo login
npx turbo link

# Da questo momento, ogni build cachea gli artefatti su Vercel
turbo build
# >>> FULL TURBO: build completo, artefatti caricati

turbo build
# >>> cache hit, artefatti scaricati da remote, istantaneo

# Verificare lo stato della cache
turbo build --summarize
# Mostra hit/miss ratio per ogni pacchetto
```

Per ambienti enterprise che non possono usare Vercel, è possibile configurare un server di cache custom usando il **Vercel Remote Cache SDK** (open source) o implementazioni terze:

```bash
# Configurare un server di cache custom
# turbo.json
# "remoteCache": {
#   "signature": true,
#   "enabled": true,
#   "apiUrl": "https://cache.mycompany.com"
# }
```

#### Composable Configuration

Turborepo supporta configurazioni composabili: ogni pacchetto nel workspace può avere il proprio `turbo.json` che estende o sovrascrive la configurazione root. Questo è particolarmente utile quando pacchetti diversi hanno esigenze di build diverse:

```json
// packages/docs/turbo.json — configurazione specifica per il pacchetto docs
{
  "extends": ["//"],
  "tasks": {
    "build": {
      "outputs": ["dist/**", ".docusaurus/**"]
    }
  }
}
```

### Bazel

**Bazel** (sviluppato da Google) è un sistema di build multilingua estremamente potente per monorepo di qualsiasi dimensione. Supporta Java, C++, Python, Go, JavaScript e molti altri linguaggi.

```python
# BUILD file (Bazel)
load("@rules_java//java:defs.bzl", "java_library", "java_test")

java_library(
    name = "auth-service",
    srcs = glob(["src/main/java/**/*.java"]),
    deps = [
        "//libs/common:utils",
        "//libs/security:crypto",
        "@maven//:com_google_guava_guava",
    ],
    visibility = ["//apps:__subpackages__"],
)

java_test(
    name = "auth-service-test",
    srcs = glob(["src/test/java/**/*.java"]),
    deps = [
        ":auth-service",
        "@maven//:junit_junit",
    ],
)
```

```bash
# Comandi Bazel
bazel build //apps/api:server           # Build di un target specifico
bazel test //...                         # Test di tutto
bazel query "deps(//apps/api:server)"    # Analisi delle dipendenze
bazel build //... --config=remote-cache  # Con cache remota
```

### Confronto degli Strumenti

| Aspetto | Nx | Turborepo | Bazel |
|---------|-----|-----------|-------|
| Linguaggi | JS/TS (primario) | JS/TS | Multi-linguaggio |
| Curva di apprendimento | Media | Bassa | Alta |
| Caching | Locale + Cloud | Locale + Remote | Locale + Remote |
| Scalabilità | Grande | Grande | Enorme |
| Generatori di codice | Sì (integrati) | No | Sì (rules) |
| Analisi dipendenze | Automatica | Basata su package.json | Esplicita (BUILD files) |
| Adozione incrementale | Facile | Molto facile | Complessa |

---

## CI/CD per Monorepo

La gestione della CI/CD in un monorepo è una delle sfide più critiche che i team devono affrontare. Senza una strategia ottimizzata, ogni push potrebbe attivare il build e il test di **tutti** i progetti nel repository, anche quando solo uno è stato modificato. Questo porta a tempi di CI proibitivi, costi elevati per i runner e feedback lento per gli sviluppatori. Le strategie di ottimizzazione si basano su tre pilastri fondamentali: **affected project detection**, **caching intelligente** e **parallelismo distribuito**.

### Affected Project Detection

L'affected project detection è il meccanismo che analizza il grafo delle dipendenze del monorepo per determinare quali progetti sono impattati da un dato commit. Invece di ricompilare e testare tutto, il sistema identifica solo i progetti che dipendono direttamente o transitivamente dai file modificati. Secondo benchmark del 2025-2026, l'affected-only execution è la singola ottimizzazione con il maggiore impatto: eseguire il build di 4 pacchetti su 45 batte qualsiasi strategia di caching in termini di tempo risparmiato.

Ogni tool di monorepo implementa questa analisi in modo diverso:

```bash
# Nx: affected analysis basata sul grafo delle dipendenze
# Confronta HEAD con il branch base (tipicamente main)
npx nx affected --target=build --base=origin/main --head=HEAD
npx nx affected --target=test --base=origin/main --head=HEAD
npx nx affected --target=lint --base=origin/main --head=HEAD

# Turborepo: filter con range di commit
turbo build --filter=...[origin/main...HEAD]
turbo test --filter=...[origin/main...HEAD]

# Bazel: query per analizzare le dipendenze inverse
# Identifica tutti i target che dipendono dai file modificati
bazel query "rdeps(//..., set($(git diff --name-only origin/main...HEAD)))" \
  | xargs bazel test
```

### Caching Remoto e Condiviso

Il caching remoto permette di condividere gli artefatti di build tra tutti gli sviluppatori e i runner CI. Quando un developer esegue il build di un pacchetto localmente, l'artefatto viene caricato su un server di cache. Quando la CI o un altro developer esegue lo stesso build con gli stessi input, l'artefatto viene scaricato istantaneamente dalla cache invece di essere ricompilato.

L'impatto è significativo: team reali riportano riduzioni del tempo CI da 20 minuti a 2 minuti grazie alla combinazione di affected detection e remote caching, con risparmi fino al 60-80% sui tempi di build complessivi.

```bash
# Nx Cloud: caching distribuito integrato
npx nx connect-to-nx-cloud
# Da questo momento, ogni task cachea gli artefatti su Nx Cloud
npx nx affected --target=build
# I task già eseguiti con gli stessi input vengono recuperati dalla cache

# Turborepo + Vercel: remote caching gratuito
npx turbo login
npx turbo link
turbo build --summarize   # Mostra hit/miss ratio per pacchetto

# Bazel: Remote Execution e Remote Caching
# .bazelrc
# build --remote_cache=grpcs://cache.mycompany.com
# build --remote_executor=grpcs://executor.mycompany.com
```

### GitHub Actions: Workflow Ottimizzato per Monorepo

Un workflow CI efficiente per monorepo in GitHub Actions combina path-based filtering, affected detection e caching degli artefatti. Il pattern più comune prevede un job iniziale che determina quali progetti sono cambiati, seguito da job paralleli per ogni progetto affected:

```yaml
# .github/workflows/ci-monorepo.yml
name: CI Monorepo
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # Job 1: Determinare i progetti affected
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.filter.outputs.frontend }}
      backend: ${{ steps.filter.outputs.backend }}
      shared: ${{ steps.filter.outputs.shared }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # Necessario per il confronto con main
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            frontend:
              - 'apps/frontend/**'
              - 'libs/shared/**'
            backend:
              - 'apps/backend/**'
              - 'libs/shared/**'
            shared:
              - 'libs/shared/**'

  # Job 2: Build e test condizionali
  build-frontend:
    needs: detect-changes
    if: needs.detect-changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm nx build frontend
      - run: pnpm nx test frontend

  build-backend:
    needs: detect-changes
    if: needs.detect-changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm nx build backend
      - run: pnpm nx test backend
```

### Strategia con Dynamic Matrix

Per monorepo con molti pacchetti, una dynamic matrix genera automaticamente job paralleli in base ai progetti affected, evitando la necessità di definire esplicitamente ogni combinazione:

```yaml
# .github/workflows/ci-dynamic.yml
name: CI Dynamic Matrix
on: pull_request

jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      projects: ${{ steps.affected.outputs.projects }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: nrwl/nx-set-shas@v4
      - id: affected
        run: |
          PROJECTS=$(npx nx show projects --affected --json)
          echo "projects=$PROJECTS" >> $GITHUB_OUTPUT

  ci:
    needs: detect
    if: needs.detect.outputs.projects != '[]'
    strategy:
      matrix:
        project: ${{ fromJson(needs.detect.outputs.projects) }}
      fail-fast: false
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm nx build ${{ matrix.project }}
      - run: pnpm nx test ${{ matrix.project }}
```

### Confronto delle Strategie CI per Monorepo

| Strategia | Complessità | Riduzione Tempo CI | Costo Infrastruttura |
|-----------|------------|-------------------|---------------------|
| Nessuna ottimizzazione | Nulla | 0% (baseline) | Alto |
| Path-based filtering (dorny/paths-filter) | Bassa | 30-50% | Medio |
| Affected detection (Nx/Turborepo) | Media | 60-80% | Medio-Basso |
| Remote caching | Media | 70-85% | Basso (cache hit) |
| Affected + Remote cache + Parallelismo | Alta | 85-95% | Basso |
| Distributed execution (Nx Agents, Bazel RBE) | Alta | 90-97% | Variabile |

### Best Practices per CI Monorepo

1. **Pinnare il base SHA**: L'affected detection dinamica può competere con i merge su main. Usare `nrwl/nx-set-shas` o equivalenti per determinare il base SHA corretto.
2. **Cache a livello di modulo**: Cacheare i risultati di test per ogni pacchetto individualmente, non l'intero workspace.
3. **Fail-fast selettivo**: Disabilitare `fail-fast` nella matrix per non bloccare i risultati degli altri pacchetti quando uno fallisce.
4. **Artefatti immutabili**: Ogni artefatto di build deve essere riproducibile dato lo stesso set di input. Bazel lo garantisce per design; Nx e Turborepo lo raggiungono tramite il content-hash degli input.
5. **Monitorare il cache hit ratio**: Un cache hit ratio sotto il 60% indica problemi nella configurazione degli input hash o nella definizione degli output.

---

## CODEOWNERS per Monorepo

Il file `CODEOWNERS` è particolarmente importante nei monorepo, dove aree diverse del codice appartengono a team diversi. GitHub utilizza CODEOWNERS per assegnare automaticamente i reviewer alle pull request in base ai file modificati. In un monorepo, una configurazione CODEOWNERS ben progettata garantisce che ogni modifica venga revisionata dal team competente, senza richiedere intervento manuale.

### Struttura del File CODEOWNERS

Il file `CODEOWNERS` si trova nella root del repository (o nella directory `.github/`) e utilizza un formato simile a `.gitignore` per associare path a owner (utenti GitHub o team):

```bash
# .github/CODEOWNERS — Esempio per un monorepo

# Default: il team platform è owner di tutto ciò che non ha un owner specifico
* @org/team-platform

# Applicazioni — ogni team possiede la propria app
/apps/frontend/               @org/team-frontend
/apps/backend/                @org/team-backend
/apps/mobile/                 @org/team-mobile
/apps/admin-dashboard/        @org/team-internal-tools

# Librerie condivise — il team platform e il team architettura
/libs/shared/ui/              @org/team-frontend @org/team-design-system
/libs/shared/utils/           @org/team-platform
/libs/shared/types/           @org/team-platform
/libs/shared/auth/            @org/team-security

# Infrastruttura e CI/CD
/.github/                     @org/team-devops
/infrastructure/              @org/team-devops
/terraform/                   @org/team-devops

# Configurazione del monorepo — richiede approvazione del team architettura
/nx.json                      @org/team-architecture
/turbo.json                   @org/team-architecture
/tsconfig.base.json           @org/team-architecture
/package.json                 @org/team-architecture

# Documentazione
/docs/                        @org/team-docs

# Sicurezza — qualsiasi modifica a file sensibili richiede review di sicurezza
**/auth/**                    @org/team-security
**/security/**                @org/team-security
**/*secret*                   @org/team-security
**/*credential*               @org/team-security
```

### Regole di Priorità

Le regole in CODEOWNERS seguono l'ordine di priorità: **l'ultima regola che matcha vince**. Questo significa che le regole più specifiche devono essere posizionate dopo quelle più generali:

```bash
# Ordine corretto: dal più generale al più specifico
# 1. Default catch-all
* @org/team-platform

# 2. Regole per directory ampie
/apps/                @org/team-leads

# 3. Regole per directory specifiche (QUESTA VINCE per /apps/frontend/)
/apps/frontend/       @org/team-frontend
```

### Protezione dei Branch con CODEOWNERS

Per rendere le review CODEOWNERS obbligatorie, è necessario configurare le branch protection rules in GitHub:

1. Navigare a **Settings → Branches → Branch protection rules**
2. Selezionare il branch (es. `main`)
3. Abilitare **"Require pull request reviews before merging"**
4. Abilitare **"Require review from Code Owners"**
5. Impostare il numero minimo di approvazioni richieste

Con questa configurazione, una PR che modifica file in `/apps/frontend/` non potrà essere mergiata finché almeno un membro di `@org/team-frontend` non l'avrà approvata. Questo garantisce che le modifiche vengano sempre revisionate dal team con la competenza specifica su quella area del codice.

### Pattern Avanzati per CODEOWNERS

```bash
# Richiedere review di più team per aree critiche
/libs/shared/auth/    @org/team-security @org/team-backend @org/team-architecture

# Usare utenti individuali per aree ad alta responsabilità
/apps/payments/       @mario-rossi @lucia-bianchi @org/team-security

# Pattern per tipi di file specifici in qualsiasi directory
**/*.sql              @org/team-dba
**/*.proto            @org/team-platform
**/Dockerfile         @org/team-devops
**/*.tf               @org/team-devops

# Escludere file di test dal review obbligatorio
# (non supportato nativamente, ma gestibile con rulesets GitHub)
```

### Verificare la Configurazione CODEOWNERS

```bash
# Verificare chi è owner di un file specifico
# (non c'è un comando git nativo, ma si può usare l'API GitHub)
gh api repos/{owner}/{repo}/codeowners/errors
# Mostra eventuali errori nella configurazione CODEOWNERS

# Script per verificare localmente quale regola matcha un file
grep -n "apps/frontend" .github/CODEOWNERS
```

### CODEOWNERS e Monorepo: Considerazioni Pratiche

- **Aggiornare CODEOWNERS ad ogni nuovo progetto**: Quando si aggiunge una nuova app o libreria al monorepo, aggiungere immediatamente la regola CODEOWNERS corrispondente.
- **Evitare owner troppo ampi**: Se un singolo team è owner di troppi path, diventa un bottleneck per le review. Suddividere la responsabilità.
- **Automatizzare la validazione**: Usare un hook pre-commit o una check CI che verifica che tutti i percorsi principali del monorepo abbiano un CODEOWNERS entry.
- **Combinare con i Rulesets GitHub**: Dalla fine del 2024, GitHub supporta i Rulesets come meccanismo più flessibile delle branch protection rules, permettendo regole condizionali basate su path, team e contesto della PR.

---

## Git Worktrees

### Cos'è un Worktree

Git worktree permette di avere più working directory collegate allo stesso repository. Invece di fare stash e switch di branch, si può semplicemente aprire una nuova working directory su un branch diverso.

```bash
# Creare un nuovo worktree su un branch esistente
git worktree add ../progetto-hotfix hotfix/critical-bug

# Creare un nuovo worktree con un nuovo branch
git worktree add -b feature/nuova-feature ../progetto-feature main

# Creare un worktree in stato detached HEAD
git worktree add --detach ../progetto-review abc1234

# Listare tutti i worktrees
git worktree list
# /home/utente/progetto           a1b2c3d [main]
# /home/utente/progetto-hotfix    d4e5f6g [hotfix/critical-bug]
# /home/utente/progetto-feature   h7i8j9k [feature/nuova-feature]

# Rimuovere un worktree
git worktree remove ../progetto-hotfix

# Pulire worktrees rimossi manualmente
git worktree prune
```

### Casi d'Uso

1. **Hotfix urgenti**: Lavorare su un hotfix senza interrompere il lavoro corrente
2. **Code review**: Fare checkout di una PR in un worktree separato per la review
3. **Build paralleli**: Eseguire build di branch diversi contemporaneamente
4. **Confronto visivo**: Aprire due versioni del codice fianco a fianco nell'editor

```bash
# Workflow tipico: hotfix urgente
# Sto lavorando su feature/nuova-ui
git worktree add ../hotfix hotfix/security-patch
cd ../hotfix
# Correggere il bug, committare, pushare
git add -A && git commit -m "fix: correggere vulnerabilità XSS"
git push origin hotfix/security-patch
cd ../progetto
git worktree remove ../hotfix
```

### Limitazioni

- Non è possibile avere due worktrees sullo stesso branch
- I worktrees condividono l'object database e i riferimenti
- Le operazioni di GC e repack influenzano tutti i worktrees

---

## Scalar: Gestione di Repository Enormi

### Cos'è Scalar

**Scalar** è uno strumento sviluppato da Microsoft (incluso in Git dalla versione 2.38) per gestire repository Git di dimensioni enormi. È nato dall'esperienza di Microsoft nel gestire il repository di Windows (oltre 300 GB di codice sorgente). Scalar configura automaticamente le ottimizzazioni di Git per repository di grandi dimensioni.

```bash
# Registrare un repository con Scalar
scalar register

# Clonare un repository con le ottimizzazioni Scalar
scalar clone https://github.com/org/huge-repo.git

# Questo configura automaticamente:
# - Partial clone (--filter=blob:none)
# - Sparse-checkout
# - Maintenance schedulata (fetch, gc, commit-graph)
# - File system monitor (fsmonitor)
# - Multi-pack index
```

### Funzionalità Principali

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCALAR OPTIMIZATIONS                          │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  PARTIAL CLONE   │  │  SPARSE-CHECKOUT  │  │  MAINTENANCE  │  │
│  │  blob:none       │  │  Cone mode        │  │  Schedulata   │  │
│  │  (on-demand      │  │  (solo directory  │  │  (background  │  │
│  │   download)      │  │   necessarie)     │  │   gc, fetch,  │  │
│  │                  │  │                   │  │   pack)       │  │
│  └─────────────────┘  └──────────────────┘  └───────────────┘  │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  FSMONITOR       │  │  COMMIT-GRAPH     │  │  MULTI-PACK   │  │
│  │  (filesystem     │  │  (accelera        │  │  INDEX        │  │
│  │   watcher per    │  │   git log,        │  │  (riduce I/O  │  │
│  │   status rapido) │  │   merge-base)     │  │   su packfile)│  │
│  └─────────────────┘  └──────────────────┘  └───────────────┘  │
│                                                                  │
│  Risultato: operazioni come git status, git log, git checkout   │
│  sono ordini di grandezza più veloci su repository enormi.      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Maintenance Schedulata

```bash
# Scalar configura automaticamente la manutenzione in background
# Equivalente a:
git maintenance start

# Task di manutenzione:
# - gc: garbage collection incrementale
# - commit-graph: aggiorna il commit-graph (accelera traversal)
# - prefetch: scarica oggetti in background
# - loose-objects: compatta oggetti loose
# - incremental-repack: ottimizza i packfile
# - pack-refs: compatta i riferimenti

# Verificare la configurazione
git maintenance run --task=gc
git maintenance run --task=commit-graph
git maintenance run --task=prefetch

# Fermare la manutenzione schedulata
git maintenance unregister
```

### Da VFS for Git a Scalar: L'Evoluzione Storica

Scalar è il risultato dell'evoluzione del progetto **VFS for Git** (Virtual File System for Git, originariamente chiamato GVFS). VFS for Git virtualizzava il filesystem sotto il repository Git, intercettando le chiamate al filesystem e scaricando i file on-demand in modo trasparente per l'utente e per Git stesso. Questo approccio ha permesso a Microsoft di gestire il repository di Windows (oltre 300 GB di codice sorgente, 3.5 milioni di file), ma richiedeva un driver a livello kernel e funzionava solo su Windows.

Con l'evoluzione di Git (partial clone, sparse-checkout, fsmonitor, commit-graph), le funzionalità che prima richiedevano la virtualizzazione del filesystem sono state integrate direttamente nel core di Git. Scalar è nato come "thin shell" attorno a queste feature native, eliminando la necessità di un driver kernel e diventando cross-platform (Windows, macOS, Linux).

Per i nuovi deployment, Microsoft raccomanda fortemente Scalar invece di VFS for Git. VFS for Git è in modalità di manutenzione dal 2022 e non riceve nuove funzionalità. Scalar, al contrario, è integrato in Git dalla versione 2.38 e rappresenta il futuro della gestione di repository di grandi dimensioni.

| Aspetto | VFS for Git | Scalar |
|---------|-------------|--------|
| Meccanismo | Driver filesystem kernel | Feature native di Git |
| Piattaforme | Solo Windows | Windows, macOS, Linux |
| Dipendenze | Driver GVFS, .NET | Solo Git 2.38+ |
| Stato | Manutenzione | Sviluppo attivo, integrato in Git |
| Setup | Complesso | `scalar clone <url>` |
| Performance | Eccellente (virtualizzazione) | Eccellente (ottimizzazioni native) |

### Configurazioni Manuali Equivalenti a Scalar

Se non si vuole usare Scalar direttamente, si possono configurare le stesse ottimizzazioni manualmente:

```bash
# Abilitare il filesystem monitor (accelera git status)
git config core.fsmonitor true
git config core.untrackedcache true

# Abilitare il commit-graph
git config fetch.writeCommitGraph true
git config core.commitGraph true

# Abilitare il multi-pack index
git config core.multiPackIndex true

# Configurare partial clone
git config remote.origin.promisor true
git config remote.origin.partialclonefilter "blob:none"

# Avviare la manutenzione schedulata
git maintenance start
```

---

## Git Bundle: Trasferimento Offline

### Cos'è un Git Bundle

Un **Git bundle** è un file che contiene una porzione (o la totalità) di un repository Git in formato portabile. È progettato per scenari dove il trasferimento di rete standard (push/pull via HTTPS o SSH) non è disponibile o praticabile: reti air-gapped, ambienti con restrizioni di rete stringenti, seeding di mirror, o semplicemente per trasferire un repository su un supporto fisico (chiavetta USB, hard disk esterno).

Il bundle contiene gli oggetti Git (commit, tree, blob) e i riferimenti (branch, tag), ed è a tutti gli effetti un file che può essere usato come remote per le operazioni di fetch e clone.

### Creare un Bundle

```bash
# Bundle completo: tutto il repository
git bundle create repo-completo.bundle --all
# Crea un file contenente tutti i branch, tag e la cronologia completa

# Bundle di un singolo branch
git bundle create main-branch.bundle main
# Solo il branch main e la sua cronologia

# Bundle incrementale: solo i commit dopo un certo punto
# Utile per aggiornamenti periodici in ambienti offline
git bundle create aggiornamento.bundle main ^v2.0.0
# Solo i commit su main dopo il tag v2.0.0

# Bundle con un range di commit specifico
git bundle create delta.bundle abc1234..HEAD
# Solo i commit tra abc1234 e HEAD

# Bundle con più branch e tag
git bundle create multi.bundle main develop --tags
```

### Verificare un Bundle

Prima di usare un bundle, è buona pratica verificarne l'integrità e la compatibilità con il repository destinazione:

```bash
# Verificare l'integrità del bundle
git bundle verify repo-completo.bundle
# The bundle contains 150 refs
# The bundle contains this ref:
#   abc1234 refs/heads/main
# The bundle records a complete history.

# Se il bundle è incrementale, la verifica controlla che il repository
# destinazione abbia i prerequisiti necessari
git bundle verify aggiornamento.bundle
# The bundle requires these 2 refs:
#   def5678 commit message...
# repo-completo.bundle is okay

# Elencare i riferimenti contenuti nel bundle
git bundle list-heads repo-completo.bundle
# abc1234 refs/heads/main
# def5678 refs/heads/develop
# ghi9012 refs/tags/v2.0.0
```

### Usare un Bundle

```bash
# Clonare da un bundle (come se fosse un remote)
git clone repo-completo.bundle progetto-locale
cd progetto-locale

# Dopo il clone, aggiungere il remote reale e rimuovere il bundle
git remote set-url origin https://github.com/org/repo.git

# Fetch da un bundle (aggiornamento incrementale)
# 1. Copiare il bundle aggiornamento nel filesystem
# 2. Aggiungere come remote temporaneo
git remote add bundle-update /percorso/aggiornamento.bundle
git fetch bundle-update
git merge bundle-update/main
git remote remove bundle-update

# Oppure, fetch diretto senza aggiungere un remote
git fetch /percorso/aggiornamento.bundle main:refs/remotes/bundle/main
git merge bundle/main
```

### Casi d'Uso Reali

1. **Reti air-gapped**: Ambienti militari, governativi o industriali senza accesso a Internet. Il repository viene aggiornato trasferendo bundle su supporti fisici verificati.

2. **Seeding di mirror**: Per inizializzare un mirror Git interno senza trasferire tutto il repository via rete. Il bundle viene trasferito una volta su supporto fisico, poi gli aggiornamenti successivi avvengono via rete.

3. **Backup verificabile**: Un bundle è un backup portabile e verificabile (`git bundle verify`) del repository. Può essere criptato e archiviato su storage offline.

4. **Onboarding di sviluppatori remoti**: In regioni con connettività limitata, un bundle del repository può essere spedito su supporto fisico, evitando clone via rete di repository molto grandi.

```
┌────────────────────────────────────────────────────────────────┐
│               GIT BUNDLE WORKFLOW — AIR-GAPPED                  │
│                                                                 │
│  Rete Connessa                   Rete Air-Gapped                │
│  ┌───────────────┐               ┌───────────────┐             │
│  │  git bundle   │  USB/Disco    │  git clone     │             │
│  │  create       │──────────────►│  bundle.file   │             │
│  │  --all        │               │                │             │
│  └───────┬───────┘               └───────┬───────┘             │
│          │                               │                      │
│          │ Settimana dopo                │ Lavoro offline       │
│          │                               │                      │
│  ┌───────▼───────┐               ┌───────▼───────┐             │
│  │  git bundle   │  USB/Disco    │  git fetch     │             │
│  │  create       │──────────────►│  delta.bundle  │             │
│  │  main ^v2.0   │               │  git merge     │             │
│  │  (incrementale│               │                │             │
│  └───────────────┘               └───────────────┘             │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Riferimento Comandi Completo

### Opzioni Complete di `git lfs`

| Sottocomando | Descrizione |
|-------------|-------------|
| `install` | Inizializza Git LFS per l'utente |
| `track <pattern>` | Traccia file per pattern (aggiunge a .gitattributes) |
| `untrack <pattern>` | Smette di tracciare file per pattern |
| `ls-files` | Elenca i file tracciati da LFS |
| `ls-files --all` | Elenca tutti i file LFS in tutti i branch |
| `status` | Mostra lo stato dei file LFS |
| `fetch` | Scarica gli oggetti LFS dal remote |
| `fetch --all` | Scarica tutti gli oggetti LFS di tutti i branch |
| `fetch --include=<pattern>` | Scarica solo file che matchano il pattern |
| `fetch --exclude=<pattern>` | Esclude file dal download |
| `pull` | Scarica e applica gli oggetti LFS |
| `push` | Carica gli oggetti LFS sul remote |
| `push --all` | Carica tutti gli oggetti LFS |
| `push --dry-run` | Mostra cosa verrebbe caricato |
| `prune` | Rimuove file LFS locali non referenziati |
| `prune --dry-run` | Mostra cosa verrebbe rimosso |
| `migrate info` | Analizza la cronologia per file grandi |
| `migrate import --include=<pat>` | Migra file esistenti a LFS |
| `migrate import --no-rewrite` | Migra senza riscrivere la cronologia |
| `migrate export --include=<pat>` | Rimuove file da LFS (torna a Git normale) |
| `env` | Mostra la configurazione LFS corrente |
| `logs last` | Mostra l'ultimo errore LFS |
| `lock <file>` | Blocca un file per editing esclusivo |
| `unlock <file>` | Sblocca un file |
| `locks` | Elenca i lock attivi |

### Opzioni Complete di `git submodule`

| Sottocomando | Descrizione |
|-------------|-------------|
| `add [-b <branch>] <url> [<path>]` | Aggiunge un submodule |
| `init [<path>]` | Inizializza le entry del submodule nell'index |
| `update [--init] [--recursive]` | Aggiorna i submodules al commit registrato |
| `update --remote` | Aggiorna al commit più recente del branch remoto |
| `update --merge` | Merge le modifiche remote nel submodule |
| `update --rebase` | Rebase le modifiche locali del submodule |
| `status [--recursive]` | Mostra lo stato dei submodules |
| `foreach [--recursive] <cmd>` | Esegue un comando in ogni submodule |
| `sync [--recursive]` | Sincronizza le URL dei submodules |
| `deinit [-f] <path>` | Deinizializza un submodule |
| `absorbgitdirs` | Sposta .git dei submodules in .git/modules/ |
| `set-branch -b <branch> <path>` | Cambia il branch tracciato |
| `set-url <path> <url>` | Cambia la URL del submodule |
| `summary` | Mostra un riassunto delle modifiche ai submodules |

### Opzioni Complete di `git sparse-checkout`

| Sottocomando | Descrizione |
|-------------|-------------|
| `init [--cone]` | Inizializza sparse-checkout (cone mode raccomandato) |
| `init --no-cone` | Inizializza con pattern generici (più lento) |
| `set <dir1> <dir2> ...` | Imposta le directory incluse (sostituisce) |
| `add <dir>` | Aggiunge una directory alle incluse |
| `list` | Mostra le directory incluse |
| `disable` | Disabilita sparse-checkout (scarica tutti i file) |
| `reapply` | Riapplica le regole dopo una modifica manuale |
| `check-rules` | Verifica se un path è incluso nelle regole |

### Opzioni Complete di `git worktree`

| Sottocomando | Descrizione |
|-------------|-------------|
| `add <path> [<branch>]` | Crea un nuovo worktree |
| `add -b <branch> <path> [<start>]` | Crea un nuovo worktree con un nuovo branch |
| `add --detach <path> <commit>` | Crea un worktree in detached HEAD |
| `list [--porcelain]` | Elenca tutti i worktrees |
| `move <worktree> <new-path>` | Sposta un worktree |
| `remove <worktree>` | Rimuove un worktree |
| `prune [--dry-run]` | Pulisce worktrees rimossi manualmente |
| `lock <worktree> [--reason=<str>]` | Impedisce la rimozione di un worktree |
| `unlock <worktree>` | Sblocca un worktree |
| `repair` | Ripara i link tra worktree e repository |

---

## Anti-Pattern

### 1. Tracciare File Che Cambiano Frequentemente con LFS

LFS è ottimale per file binari grandi che cambiano raramente (release binary, asset di design). Ogni versione di un file LFS occupa storage aggiuntivo sul server. Un file che cambia ad ogni commit (es. database SQLite, file di log) consuma rapidamente la quota.

```bash
# SBAGLIATO: tracciare un file che cambia ogni commit
git lfs track "db/development.sqlite3"    # Ogni commit = nuova versione su LFS

# CORRETTO: tracciare file binari stabili
git lfs track "assets/fonts/*.woff2"      # Font cambiano raramente
git lfs track "models/v*.onnx"            # Modelli ML con versioning
```

### 2. Submodules Annidati a 3+ Livelli di Profondità

I submodules annidati (submodule dentro un submodule dentro un submodule) creano una cascata di `--recursive` in ogni operazione. I tempi di clone, init e update crescono esponenzialmente. I conflitti di versione tra livelli diventano quasi impossibili da gestire.

```bash
# SBAGLIATO: nidificazione profonda
# progetto/ → sub-A/ → sub-B/ → sub-C/
git submodule update --init --recursive
# 3 livelli di ricorsione, ogni livello moltiplica la complessità

# CORRETTO: massimo 1 livello di submodules
# O meglio: usare un package manager (npm, pip) per le dipendenze
```

### 3. Monorepo Senza Build Tool Dedicato

Un monorepo senza Nx, Turborepo, Bazel o equivalente forza la ricompilazione e il re-test di **tutto** ad ogni modifica. La CI diventa insostenibilmente lenta e gli sviluppatori perdono fiducia nel sistema.

```bash
# SBAGLIATO: npm run build && npm test in un monorepo di 50 pacchetti
# Tempo: 45 minuti per ogni PR

# CORRETTO: usare affected analysis
npx nx affected --target=build    # Solo i pacchetti impattati
turbo build --filter=...[HEAD~1]  # Solo ciò che è cambiato
```

### 4. Non Committare `.gitattributes` con LFS

Se `.gitattributes` non è committato, gli altri sviluppatori non sapranno quali file devono essere gestiti da LFS. I file grandi verranno committati normalmente nel repository Git, vanificando l'intero scopo di LFS.

```bash
# SBAGLIATO: configurare LFS localmente senza committare
git lfs track "*.psd"
# .gitattributes modificato ma non committato

# CORRETTO: committare immediatamente
git lfs track "*.psd"
git add .gitattributes
git commit -m "chore: configurare Git LFS per file PSD"
```

### 5. Usare `git subtree` per Dipendenze che Cambiano Frequentemente

Ogni `git subtree pull` crea un merge commit che inquina la cronologia del repository principale. Per dipendenze attive con release frequenti, un package manager è più appropriato.

```bash
# SBAGLIATO: subtree per una libreria con release settimanali
git subtree pull --prefix=libs/active-lib upstream main --squash
# Merge commit ogni settimana, cronologia inquinata

# CORRETTO: usare un package manager
npm install @org/active-lib    # Aggiornamenti gestiti tramite lockfile
```

### 6. Clone Completo in CI/CD per Repository Grandi

Clonare l'intero repository con tutta la cronologia in ogni run della CI è uno spreco di tempo e banda. Per repository grandi, può significare minuti di attesa inutile.

```bash
# SBAGLIATO: clone completo in CI
git clone https://github.com/org/huge-repo.git

# CORRETTO: clone ottimizzato per CI
git clone --depth 1 --single-branch https://github.com/org/huge-repo.git
# Oppure con partial clone
git clone --filter=blob:none --sparse https://github.com/org/huge-repo.git
cd huge-repo
git sparse-checkout set apps/$APP_NAME libs/shared
```

### 7. Worktree Dimenticati che Accumulano Spazio

I worktrees condividono l'object database ma hanno ciascuno una propria working directory. Worktrees dimenticati accumulano file e occupano spazio disco, bloccano branch (un branch non può essere checked out in due worktrees), e impediscono il garbage collection efficiente.

```bash
# Verificare worktrees attivi
git worktree list

# Pulire worktrees rimossi manualmente
git worktree prune
```

### 8. Usare LFS Senza Verificare i Limiti di Storage della Piattaforma

GitHub Free include solo 1 GB di storage LFS e 1 GB di bandwidth al mese. Superare questi limiti blocca i push LFS e richiede l'acquisto di data pack aggiuntivi.

### 9. Mescolare Submodules e Subtree nello Stesso Progetto

Usare contemporaneamente submodules e subtrees per diverse dipendenze confonde il team. Ogni membro deve conoscere due workflow diversi e sapere quale si applica a quale dipendenza. Standardizzare su un approccio.

### 10. Non Configurare Sparse-Checkout in Monorepo per Sviluppatori

In un monorepo da 50+ GB, ogni sviluppatore che lavora su una singola app non ha bisogno di tutto il codice. Senza sparse-checkout, il clone iniziale richiede tempi e spazio proibitivi.

---

## Best Practices

### Git LFS

1. **Definire i pattern LFS all'inizio del progetto**: Migrare file esistenti a LFS è costoso (riscrive la cronologia). Meglio configurare LFS fin dal primo commit.

2. **Non tracciare file che cambiano frequentemente**: LFS è ottimale per file binari che cambiano raramente. File che cambiano ad ogni commit consumano rapidamente lo storage.

3. **Usare `.lfsconfig` per configurazione team**: Centralizzare la configurazione LFS nel repository.

4. **Monitorare l'uso dello storage**: Verificare regolarmente il consumo di storage LFS, specialmente su piattaforme con limiti.

### Submodules

1. **Preferire subtree per dipendenze semplici**: I submodules aggiungono complessità significativa. Per dipendenze che non cambiano frequentemente, subtree è più semplice.

2. **Documentare il workflow**: I submodules hanno un workflow non intuitivo. Documentare chiaramente i comandi necessari per il setup e l'aggiornamento.

3. **Automatizzare gli aggiornamenti**: Usare Dependabot o Renovate per automatizzare gli aggiornamenti dei submodules.

4. **Configurare `submodule.recurse`**: Per evitare dimenticanze nei checkout e pull.

### Monorepo

1. **Iniziare con una struttura chiara**: Definire la struttura delle directory (apps/, libs/, tools/) prima di iniziare lo sviluppo.

2. **Usare un tool di build appropriato**: Non gestire un monorepo senza uno strumento dedicato (Nx, Turborepo, Bazel).

3. **Implementare affected analysis**: Eseguire build e test solo dei progetti impattati dalle modifiche.

4. **Configurare CODEOWNERS**: Definire chiaramente chi è responsabile di ogni area del monorepo.

---

## Troubleshooting

### 1. LFS: File Non Scaricati (Pointer File al Posto del Contenuto)

```bash
# Sintomo: i file LFS contengono solo il pointer
cat large-file.bin
# version https://git-lfs.github.com/spec/v1
# oid sha256:...

# Soluzione 1: pull di tutti i file LFS
git lfs pull

# Soluzione 2: fetch e checkout separati
git lfs fetch --include="path/to/file"
git lfs checkout

# Soluzione 3: se git lfs install non è stato eseguito
git lfs install
git lfs pull

# Soluzione 4: verificare che gli hook LFS siano installati
git lfs install --force
# Reinstalla gli hook smudge/clean
```

### 2. Submodule: Directory Vuota dopo Clone

```bash
# Sintomo: la directory del submodule è vuota
ls libs/libreria/
# (vuoto)

# Soluzione
git submodule update --init --recursive

# Se il clone è stato fatto senza --recurse-submodules:
git submodule init
git submodule update

# Per il futuro, clonare sempre con:
git clone --recurse-submodules https://github.com/org/project.git
```

### 3. Monorepo: CI Troppo Lenta

```bash
# Usare partial clone e sparse-checkout nella CI
git clone --filter=blob:none --sparse $REPO_URL
cd repo
git sparse-checkout set apps/$APP_NAME libs/shared

# Usare affected analysis
npx nx affected --target=test --base=origin/main --head=HEAD

# Per Turborepo
turbo test --filter=...[origin/main...HEAD]

# Per Bazel
bazel test //... --test_tag_filters=-slow
```

### 4. Worktree: Branch Già in Uso

```bash
# Errore: fatal: 'main' is already checked out at '/path/to/worktree'
# Non è possibile avere due worktrees sullo stesso branch

# Soluzione 1: creare un nuovo branch
git worktree add ../nuovo-worktree -b work-copy main

# Soluzione 2: usare detached HEAD
git worktree add --detach ../review-worktree abc1234

# Soluzione 3: rimuovere il worktree vecchio
git worktree remove ../vecchio-worktree
```

### 5. LFS: Bandwidth Exceeded (GitHub)

```bash
# Sintomo: "Client error: https://lfs.github.com/.../objects/..."
# "Bandwidth limit exceeded"

# Diagnosi: verificare l'uso della bandwidth
# GitHub → Settings → Billing → Git LFS Data

# Soluzione 1: acquistare data pack aggiuntivi
# GitHub → Settings → Billing → Git LFS Data → Add more data

# Soluzione 2: ridurre la bandwidth
# Usare GIT_LFS_SKIP_SMUDGE=1 per cloni CI
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/org/repo.git
# Scaricare solo i file necessari
git lfs pull --include="assets/needed-only.psd"

# Soluzione 3: self-hosting del LFS server
git config lfs.url https://lfs.mycompany.com/org/repo
```

### 6. LFS: File Lock Conflict

```bash
# Sintomo: "Lock failed: already locked by user@example.com"
# Causa: un altro utente ha bloccato il file per editing esclusivo

# Diagnosi: vedere chi ha il lock
git lfs locks
# path/to/file.psd    user@example.com    ID:12345

# Soluzione 1: chiedere all'utente di sbloccare
# (comunicazione diretta)

# Soluzione 2: forzare lo sblocco (richiede permessi)
git lfs unlock path/to/file.psd --force

# Soluzione 3: verificare lock stale (utente non più attivo)
git lfs locks --verify
```

### 7. Submodule: Detached HEAD Dopo Update

```bash
# Sintomo: dopo git submodule update, il submodule è in detached HEAD
# Causa: il submodule viene sempre portato al commit esatto referenziato

# Soluzione: fare checkout di un branch nel submodule
cd libs/libreria
git checkout main
git pull origin main

# Per il futuro: usare --merge o --rebase
git submodule update --remote --merge
# Oppure
git submodule update --remote --rebase
```

### 8. Submodule: Push del Progetto Padre Senza Push del Submodule

```bash
# Sintomo: altri sviluppatori non possono clonare perché il commit
# referenziato dal submodule non esiste sul remote

# Diagnosi
git push --recurse-submodules=check
# fatal: submodule 'libs/libreria' has local changes not pushed to origin

# Soluzione: pushare prima il submodule
git push --recurse-submodules=on-demand
# Pusha automaticamente i submodules prima del progetto padre

# Configurare come default
git config push.recurseSubmodules on-demand
```

### 9. Subtree: Merge Conflict durante Pull

```bash
# Sintomo: conflitti durante git subtree pull
# Causa: le modifiche locali nella directory del subtree
# confliggono con le modifiche upstream

# Soluzione 1: risolvere i conflitti manualmente
git subtree pull --prefix=libs/libreria upstream main --squash
# Risolvere i conflitti come in un merge normale
git add .
git commit

# Soluzione 2: accettare la versione upstream
git checkout --theirs -- libs/libreria/
git add libs/libreria/
git commit
```

### 10. Sparse-Checkout Non Rispetta i Pattern

```bash
# Sintomo: file che dovrebbero essere esclusi appaiono ancora
# Cause possibili:
# 1. File già tracciati prima dell'abilitazione di sparse-checkout
# 2. Pattern sbagliati

# Diagnosi
git sparse-checkout list
git sparse-checkout check-rules -- path/to/file.js

# Soluzione 1: riapplicare le regole
git sparse-checkout reapply

# Soluzione 2: disabilitare e riabilitare
git sparse-checkout disable
git sparse-checkout set apps/frontend libs/shared
```

### 11. LFS: Migrazione Causa Repository Corrotto

```bash
# Sintomo: dopo git lfs migrate, il repository ha problemi
# Causa: la migrazione riscrive la cronologia e può corrompere
# se interrotta

# Soluzione: partire da un clone fresco
git clone --mirror https://github.com/org/repo.git repo-backup.git

# Eseguire la migrazione sul backup
cd repo-backup.git
git lfs migrate import --include="*.psd,*.zip" --everything

# Verificare l'integrità
git fsck

# Se tutto ok, pushare
git push --force --all
git push --force --tags
```

### 12. Worktree: File Mancanti dopo Checkout

```bash
# Sintomo: il worktree non ha tutti i file
# Causa: sparse-checkout è attivo e le regole escludono file

# Diagnosi
git sparse-checkout list

# Soluzione: disabilitare sparse-checkout nel worktree
cd ../worktree-path
git sparse-checkout disable

# Oppure aggiungere le directory necessarie
git sparse-checkout add path/to/needed/dir
```

### 13. Submodule: URL Cambiata

```bash
# Sintomo: submodule update fallisce perché la URL del remote è cambiata
# (es. migrazione da GitHub a GitLab)

# Soluzione 1: aggiornare .gitmodules
git config -f .gitmodules submodule.libs/libreria.url https://gitlab.com/org/libreria.git

# Sincronizzare le URL
git submodule sync --recursive

# Aggiornare
git submodule update --init --recursive

# Committare la modifica
git add .gitmodules
git commit -m "chore: aggiornare URL submodule dopo migrazione"
```

### 14. LFS: Smudge Filter Error durante Checkout

```bash
# Sintomo: "Error downloading object: ... Smudge error"
# Causa: il server LFS non è raggiungibile o il file non esiste

# Diagnosi
git lfs logs last

# Soluzione 1: verificare la connettività
git lfs env

# Soluzione 2: scaricare manualmente
git lfs fetch --include="path/to/file"
git lfs checkout

# Soluzione 3: se il file è stato rimosso dal server LFS
# (non recuperabile — i file LFS eliminati dal server sono persi)
# Contattare l'amministratore del server LFS
```

### 15. Monorepo: `git status` Troppo Lento

```bash
# Sintomo: git status impiega 10+ secondi in un monorepo grande
# Causa: Git deve scansionare tutti i file nella working directory

# Soluzione 1: abilitare fsmonitor
git config core.fsmonitor true
git config core.untrackedcache true

# Soluzione 2: usare sparse-checkout per ridurre i file
git sparse-checkout set apps/my-app libs/shared

# Soluzione 3: usare Scalar
scalar register

# Soluzione 4: abilitare il commit-graph
git config fetch.writeCommitGraph true
git maintenance start
```

### 16. LFS: File Troppo Grande per il Push

```bash
# Sintomo: "this exceeds GitHub's file size limit of 100.00 MB"
# Causa: il file non era tracciato da LFS prima del commit

# Soluzione: migrare il file a LFS
git lfs migrate import --include="path/to/large-file.bin"
# Questo riscrive la cronologia!
git push --force-with-lease

# Se il file è già stato pushato senza LFS:
# Usare BFG Repo-Cleaner o git filter-repo per rimuoverlo dalla cronologia
# Poi riconfigurare LFS e ri-committare
```

### 17. Submodule: Conflitto sulla Reference del Submodule

```bash
# Sintomo: durante un merge, conflitto sulla reference del submodule
# Causa: due branch hanno aggiornato il submodule a commit diversi

# Il conflitto appare come:
# CONFLICT (submodule): Merge conflict in libs/libreria

# Soluzione: scegliere quale versione del submodule usare
git checkout --ours -- libs/libreria     # Nostra versione
# Oppure
git checkout --theirs -- libs/libreria   # Loro versione

# Poi aggiornare il submodule
cd libs/libreria
git checkout <commit-desiderato>
cd ../..
git add libs/libreria
git merge --continue
```

---

## FAQ

### 1. Quando devo usare Git LFS vs Git normale?

Git LFS per file binari > 10-50 MB che non beneficiano del diff di Git (immagini, video, modelli ML, archivi compressi). Git normale per tutto il resto: codice sorgente, configurazioni, documentazione testuale. La regola pratica: se `git diff` su un file produce output leggibile, non serve LFS.

### 2. Posso usare Git LFS con repository pubblici gratuiti su GitHub?

Sì, ma con limiti: 1 GB di storage e 1 GB di bandwidth al mese per GitHub Free. Il bandwidth viene consumato ad ogni clone e pull. Per progetti open source con molti clone, i limiti si raggiungono rapidamente. Considerare alternative come hosting dei file su un CDN esterno con link nel README.

### 3. Submodules o Subtree: quale scegliere?

**Submodules** quando: il repository esterno ha vita propria, viene aggiornato indipendentemente, e si vuole tracciare un commit specifico. **Subtree** quando: si vuole integrare il codice senza complessità aggiuntiva, il team non è familiare con i submodules, o la dipendenza cambia raramente. In entrambi i casi, valutare se un package manager (npm, pip, Maven) non sia la soluzione migliore.

### 4. Monorepo o polyrepo: quando usare ciascuno?

**Monorepo** quando: c'è molto codice condiviso, i refactoring cross-progetto sono frequenti, e si vuole un singolo punto di verità per le dipendenze. **Polyrepo** quando: i progetti sono veramente indipendenti, team diversi hanno cicli di release diversi, e la complessità della build non giustifica un monorepo. Aziende come Google e Meta usano monorepo; molte startup preferiscono polyrepo per semplicità iniziale.

### 5. Come migro un file già committato nella cronologia verso LFS?

```bash
# Analizzare cosa migrare
git lfs migrate info --everything --above=10mb

# Migrare (RISCRIVE LA CRONOLOGIA)
git lfs migrate import --include="*.psd,*.zip" --everything

# Dopo la migrazione, tutti devono ri-clonare o fare:
git fetch --all
git reset --hard origin/main
```

### 6. Come rimuovo completamente un submodule?

```bash
# Passo 1: deinizializzare
git submodule deinit -f libs/libreria

# Passo 2: rimuovere dall'index e dal filesystem
git rm -f libs/libreria

# Passo 3: rimuovere la directory dei moduli
rm -rf .git/modules/libs/libreria

# Passo 4: committare
git commit -m "chore: rimuovere submodule libreria"
```

### 7. Nx vs Turborepo: quale scegliere per un monorepo JavaScript?

**Nx**: più completo, con generatori di codice, analisi dipendenze automatica, plugin ecosystem, e supporto multi-linguaggio. Curva di apprendimento media. **Turborepo**: più semplice, focalizzato su caching e parallelismo, integrazione nativa con Vercel. Curva di apprendimento bassa. Per team piccoli/medi: Turborepo. Per team grandi con necessità di standardizzazione: Nx.

### 8. Come funziona il file locking in Git LFS?

Git LFS supporta il file locking per prevenire conflitti su file binari (non mergiabili). Un utente blocca un file prima di modificarlo; gli altri ricevono un avviso se tentano di modificare lo stesso file. I lock sono gestiti dal server LFS (non da Git). Non tutte le piattaforme supportano il locking (GitHub lo supporta, GitLab pure).

```bash
git lfs lock path/to/design.psd
# Modifica il file...
git add path/to/design.psd
git commit -m "chore: aggiornare design"
git lfs unlock path/to/design.psd
```

### 9. Sparse-checkout influisce sulla cronologia Git?

No. Lo sparse-checkout è puramente un filtro sulla working directory. La cronologia completa è disponibile per tutte le operazioni (`git log`, `git blame`, `git diff`). Solo i file nella working directory sono limitati. Questo significa che `git status` è più veloce, ma `git log --all -- path/to/excluded/file` funziona ancora.

### 10. Posso usare worktrees con submodules?

Sì, ma con cautela. Ogni worktree ha la propria working directory ma condivide l'object database. I submodules in worktrees separati possono avere stati diversi (diverso commit checked out). Usare `git submodule update --init --recursive` in ogni worktree dopo la creazione.

### 11. Come posso verificare lo storage LFS usato su GitHub?

Via web: Settings -> Billing -> Git LFS Data. Via API:
```bash
gh api user --jq '.disk_usage'
# Per organizzazioni
gh api orgs/{org}/settings/billing/shared-storage
```

### 12. Git subtree è built-in o un'estensione?

`git subtree` è incluso in Git come script contrib, ma non è parte del core. È disponibile di default in quasi tutte le distribuzioni di Git. Tuttavia, non ha la stessa documentazione e manutenzione delle feature core. La sintassi è stabile e affidabile per l'uso in produzione.

### 13. Come posso fare partial clone di un solo branch?

```bash
git clone --filter=blob:none --single-branch -b main https://github.com/org/repo.git
# --filter=blob:none: non scarica i blob
# --single-branch: solo il branch specificato
# Combinati: il clone più leggero possibile
```

### 14. Posso convertire un repository polyrepo in monorepo mantenendo la cronologia?

Sì, usando `git subtree add` o `git merge --allow-unrelated-histories`:
```bash
# Aggiungere repo-A come subdirectory
git remote add repo-a https://github.com/org/repo-a.git
git fetch repo-a
git subtree add --prefix=apps/app-a repo-a main
# La cronologia di repo-A è preservata nella subdirectory
```

### 15. Git LFS e i branch: ogni branch ha la sua copia dei file?

No. Git LFS usa content-addressable storage basato su SHA-256. Se lo stesso file (stesso contenuto) appare in branch diversi, è memorizzato una sola volta sul server LFS. Solo i pointer file (pochi byte) sono duplicati nei diversi commit. Tuttavia, versioni diverse dello stesso file (contenuto diverso) occupano ciascuna il proprio spazio.

### 16. Come gestisco le dipendenze di build in un monorepo Bazel?

Bazel richiede che tutte le dipendenze siano dichiarate esplicitamente nei file `BUILD`. Non c'è auto-detection. Questo è sia il punto di forza (build deterministiche) che il punto debole (manutenzione dei BUILD file). Strumenti come `gazelle` (per Go/Proto) e `rules_jvm_external` (per Java) automatizzano la generazione dei BUILD file.

---

## Riferimenti

- **Git LFS Documentation**: https://git-lfs.com
- **Git Documentation — git-submodule**: https://git-scm.com/docs/git-submodule
- **Git Documentation — git-subtree**: https://git-scm.com/docs/git-subtree
- **Git Documentation — git-sparse-checkout**: https://git-scm.com/docs/git-sparse-checkout
- **Git Documentation — git-worktree**: https://git-scm.com/docs/git-worktree
- **Nx Documentation**: https://nx.dev
- **Turborepo Documentation**: https://turbo.build/repo
- **Bazel Documentation**: https://bazel.build
- **GitHub — Git LFS Pricing**: https://docs.github.com/en/repositories/working-with-files/managing-large-files
- **Microsoft — Scaling Git**: https://devblogs.microsoft.com/devops/introducing-scalar/

---

## Esercizi

### Esercizio 1: Configurare Git LFS per un Progetto

```bash
# Obiettivo: configurare LFS e osservare il comportamento con file binari

# 1. Creare un repository e inizializzare LFS:
git init lfs-lab && cd lfs-lab
git lfs install

# 2. Tracciare file binari:
git lfs track "*.png" "*.jpg" "*.zip" "*.pdf"
cat .gitattributes  # Osservare le regole generate

# 3. Aggiungere file di test:
dd if=/dev/urandom of=image.png bs=1M count=5
git add .gitattributes image.png
git commit -m "feat: add LFS-tracked image"

# 4. Verificare che il file è gestito da LFS:
git lfs ls-files
git cat-file -p HEAD:image.png  # Deve mostrare il pointer, non il contenuto

# 5. Verificare le dimensioni:
git count-objects -vH  # Il .git/ è piccolo
ls -lh image.png       # Il file di lavoro è 5MB

# 6. Migrare un file già committato a LFS:
echo "plain text" > doc.pdf
git add doc.pdf && git commit -m "add pdf without LFS"
git lfs migrate import --include="*.pdf" --everything
git lfs ls-files  # Ora anche doc.pdf è in LFS
```

### Esercizio 2: Submodules — Aggiunta, Aggiornamento e Rimozione

```bash
# Obiettivo: gestire il ciclo di vita completo di un submodule

# 1. Creare il repository "libreria" (sarà il submodule):
git init /tmp/libreria && cd /tmp/libreria
echo "v1.0" > lib.txt && git add . && git commit -m "lib v1.0"

# 2. Creare il repository principale e aggiungere il submodule:
git init /tmp/progetto && cd /tmp/progetto
echo "app" > app.txt && git add . && git commit -m "init app"
git submodule add /tmp/libreria libs/libreria
git commit -m "feat: add libreria submodule"

# 3. Verificare lo stato:
cat .gitmodules
git submodule status

# 4. Simulare un aggiornamento della libreria:
cd /tmp/libreria
echo "v2.0" > lib.txt && git commit -am "lib v2.0"

# 5. Aggiornare il submodule nel progetto:
cd /tmp/progetto
git submodule update --remote libs/libreria
git diff  # Mostra il cambio di hash del submodule
git commit -am "chore: update libreria to v2.0"

# 6. Rimuovere il submodule:
git submodule deinit libs/libreria
git rm libs/libreria
rm -rf .git/modules/libs/libreria
git commit -m "chore: remove libreria submodule"
```

### Esercizio 3: Sparse-Checkout per Repository Grandi

```bash
# Obiettivo: clonare parzialmente un repository e lavorare su una sottodirectory

# 1. Creare un repository con struttura complessa:
git init /tmp/monorepo && cd /tmp/monorepo
mkdir -p apps/frontend apps/backend libs/shared libs/utils docs
echo "fe" > apps/frontend/app.js
echo "be" > apps/backend/server.py
echo "shared" > libs/shared/lib.ts
echo "utils" > libs/utils/helpers.ts
echo "docs" > docs/README.md
git add . && git commit -m "init monorepo"

# 2. Clone con sparse-checkout (solo apps/frontend):
git clone --filter=blob:none --sparse /tmp/monorepo /tmp/frontend-only
cd /tmp/frontend-only
git sparse-checkout set apps/frontend

# 3. Verificare:
ls -R          # Solo apps/frontend è presente
du -sh .git/   # .git/ è minimale

# 4. Aggiungere un altro path:
git sparse-checkout add libs/shared
ls libs/shared/  # Ora è disponibile

# 5. Visualizzare la configurazione:
git sparse-checkout list

# 6. Tornare al clone completo:
git sparse-checkout disable
ls -R  # Tutti i file sono presenti
```

### Esercizio 4: Git Worktree per Lavoro Parallelo

```bash
# Obiettivo: lavorare su due branch simultaneamente con worktree

# 1. Creare un repository:
git init /tmp/worktree-lab && cd /tmp/worktree-lab
echo "v1" > app.txt && git add . && git commit -m "init"
git checkout -b develop
echo "dev" >> app.txt && git commit -am "dev: change"
git checkout main

# 2. Creare un worktree per il branch develop:
git worktree add ../worktree-develop develop

# 3. Lavorare in parallelo:
# Terminale 1: /tmp/worktree-lab (main)
echo "main fix" >> app.txt && git commit -am "fix: main fix"

# Terminale 2: /tmp/worktree-develop (develop)
cd /tmp/worktree-develop
echo "dev feature" >> app.txt && git commit -am "feat: dev feature"

# 4. Verificare lo stato:
cd /tmp/worktree-lab
git worktree list  # Mostra entrambi i worktree

# 5. Rimuovere il worktree:
git worktree remove ../worktree-develop
git worktree prune
```

### Esercizio 5: Monorepo con Nx — Setup e Build Incrementale

```bash
# Obiettivo: creare un monorepo con Nx e osservare il build incrementale

# 1. Creare un workspace Nx:
npx create-nx-workspace@latest mono-lab --preset=ts
cd mono-lab

# 2. Generare due librerie:
npx nx generate @nx/js:library shared-utils
npx nx generate @nx/js:library api-client

# 3. Aggiungere una dipendenza tra le librerie:
# In api-client, importare shared-utils

# 4. Eseguire il build:
npx nx build api-client    # Build di api-client e le sue dipendenze
npx nx build api-client    # Seconda volta: cache hit, istantaneo

# 5. Visualizzare il grafo delle dipendenze:
npx nx graph

# 6. Affected: modificare solo shared-utils e osservare:
npx nx affected --target=build  # Rebuilda solo shared-utils e api-client
npx nx affected --target=test   # Testa solo i progetti affetti
```

---

## Letture consigliate

- **Git LFS Documentation** — https://git-lfs.com (consultato: 2026-05-24). Documentazione ufficiale di Git Large File Storage con guida all'installazione e alla migrazione.

- **Git Pro Book — Submodules** — https://git-scm.com/book/en/v2/Git-Tools-Submodules (consultato: 2026-05-24). Capitolo ufficiale sui submodules con workflow per progetti composti.

- **Nx Documentation** — https://nx.dev/getting-started/intro (consultato: 2026-05-24). Guida introduttiva a Nx per monorepo con build incrementale e caching distribuito.

- **Turborepo Documentation** — https://turbo.build/repo/docs (consultato: 2026-05-24). Documentazione di Turborepo, alternativa a Nx per monorepo JavaScript/TypeScript.

- **Bazel Documentation** — https://bazel.build/start (consultato: 2026-05-24). Sistema di build di Google per monorepo multi-linguaggio con build ermetiche e riproducibili.

- **"Scaling Git at Microsoft" (DevBlogs)** — https://devblogs.microsoft.com/devops/the-largest-git-repo-on-the-planet/ (consultato: 2026-05-24). Case study sulla gestione del monorepo Windows con VFS for Git e Scalar.

---

## Riferimenti Incrociati

| Argomento | Modulo | File |
|-----------|--------|------|
| Fondamenti Git: oggetti, staging, commit | 01 | [01-fondamenti-git.md](01-fondamenti-git.md) |
| Git Internals: blob, tree, packfile | 07 | [07-git-interni-oggetti-refs.md](07-git-interni-oggetti-refs.md) |
| Gitignore e Gitattributes: regole per LFS tracking | 11 | [11-gitignore-gitattributes-config.md](11-gitignore-gitattributes-config.md) |
| GitHub Repository Management: settings, protezioni | 12 | [12-github-repository-management.md](12-github-repository-management.md) |
| GitHub Actions CI/CD: build monorepo in pipeline | 19 | [19-github-actions-ci-cd-ricette.md](19-github-actions-ci-cd-ricette.md) |
| GitHub Actions Avanzate: matrix, caching | 18 | [18-github-actions-avanzate.md](18-github-actions-avanzate.md) |
| DevOps completo con GitHub | 24 | [24-devops-completo-con-github.md](24-devops-completo-con-github.md) |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **Git LFS** | Git Large File Storage — estensione di Git che memorizza file binari di grandi dimensioni su un server separato, mantenendo nel repository solo pointer leggeri. |
| **LFS pointer** | File di testo piccolo (~130 byte) che Git memorizza al posto del file binario reale. Contiene la versione LFS, l'hash SHA-256 e la dimensione del file originale. |
| **submodule** | Meccanismo Git per includere un repository esterno come sottodirectory di un altro repository. Il repository padre traccia un commit specifico del submodule. |
| **subtree** | Alternativa ai submodules che copia il codice del repository esterno direttamente nella directory del progetto, fondendone la cronologia. Non richiede comandi speciali per il clone. |
| **sparse-checkout** | Funzionalità Git che permette di materializzare nel working tree solo un sottoinsieme dei file del repository. Utile per monorepo di grandi dimensioni. |
| **partial clone** | Modalità di clone (`--filter=blob:none`) che scarica solo i metadati (commit, tree) senza i blob. I file vengono scaricati on-demand al checkout. |
| **monorepo** | Strategia di organizzazione del codice in cui molteplici progetti, librerie e servizi risiedono in un unico repository Git. |
| **polyrepo** | Strategia alternativa al monorepo in cui ogni progetto o servizio ha il proprio repository Git separato. |
| **worktree** | Funzionalità Git che permette di avere più working tree collegati allo stesso repository `.git`, ognuno su un branch diverso. |
| **Nx** | Framework per monorepo che fornisce build incrementale, caching locale e remoto, analisi delle dipendenze e generatori di codice. Supporta JavaScript/TypeScript e altri linguaggi. |
| **Turborepo** | Strumento di build per monorepo JavaScript/TypeScript di Vercel. Offre caching e parallelismo con configurazione minimale. |
| **Bazel** | Sistema di build open-source di Google per monorepo multi-linguaggio. Garantisce build ermetiche, deterministiche e incrementali. |
| **Scalar** | Strumento Microsoft (ora integrato in Git) per la gestione di repository di grandi dimensioni. Abilita automaticamente sparse-checkout, partial clone e manutenzione programmata. |
| **delta encoding** | Tecnica di compressione usata nei packfile Git che memorizza solo le differenze tra oggetti simili, riducendo drasticamente lo spazio disco e la banda di trasferimento. |
