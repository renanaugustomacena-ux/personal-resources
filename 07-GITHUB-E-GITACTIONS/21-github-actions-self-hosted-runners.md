---
corso: "GitHub e Git Actions"
fase: "4 — GitHub Actions"
modulo: 21
titolo: "GitHub Actions Self-Hosted Runners: Guida Approfondita"
versione: "Actions Runner 2.311 / ARC 0.9"
livello: "Avanzato"
prerequisiti: ["GitHub Actions Avanzate (modulo 18)", "Docker e container", "Linux administration base"]
obiettivi:
  - "Installare e configurare self-hosted runner su Linux, Windows e macOS con registrazione sicura"
  - "Implementare runner ephemeral per eliminare contaminazione tra job"
  - "Configurare autoscaling con Actions Runner Controller (ARC) su Kubernetes"
  - "Applicare best practice di sicurezza: isolamento, runner groups, label-based routing"
  - "Progettare un'architettura ibrida GitHub-hosted + self-hosted con monitoraggio proattivo"
tag: [github-actions, self-hosted-runners, arc, kubernetes, ephemeral, runner-groups, docker, autoscaling, sicurezza, monitoring]
---

# 21 — GitHub Actions Self-Hosted Runners: Guida Approfondita

> **Modulo 21** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al termine di questo modulo sarai in grado di:
>
> 1. Installare e configurare self-hosted runner su Linux, Windows e macOS con registrazione sicura
> 2. Implementare runner ephemeral per eliminare contaminazione tra job
> 3. Configurare autoscaling con Actions Runner Controller (ARC) su Kubernetes
> 4. Applicare best practice di sicurezza: isolamento, runner groups, label-based routing
> 5. Progettare un'architettura ibrida GitHub-hosted + self-hosted con monitoraggio proattivo

## Idee guida
1. **ARC (Actions Runner Controller) per ephemeral runner K8s.**
2. **`pull_request_target` e antipattern security.** Use `pull_request` + manual approval.
3. **Container sandbox: non riusare runner tra job di repo diversi.**
4. **Secret masking validation: test echo secret in log, must be `***`.**


## Indice

1. [Introduzione](#introduzione)
2. [Perché Usare Self-Hosted Runners](#perché-usare-self-hosted-runners)
3. [Architettura dei Self-Hosted Runners](#architettura-dei-self-hosted-runners)
4. [Installazione su Linux](#installazione-su-linux)
5. [Installazione su Windows](#installazione-su-windows)
6. [Installazione su macOS](#installazione-su-macos)
7. [Configurazione come Servizio systemd](#configurazione-come-servizio-systemd)
8. [Runner Groups e Labels](#runner-groups-e-labels)
9. [Docker-in-Docker su Self-Hosted Runners](#docker-in-docker-su-self-hosted-runners)
10. [Autoscaling dei Runners](#autoscaling-dei-runners)
11. [Runners Ephemeral](#runners-ephemeral)
12. [Actions Runner Controller su Kubernetes](#actions-runner-controller-su-kubernetes)
13. [Security Hardening](#security-hardening)
14. [Monitoraggio e Osservabilità](#monitoraggio-e-osservabilità)
15. [Troubleshooting](#troubleshooting)
16. [Confronto Costi: GitHub-Hosted vs Self-Hosted](#confronto-costi)
17. [Best Practice](#best-practice)
18. [ARC Moderno: Architettura gha-runner-scale-set](#arc-moderno-architettura-gha-runner-scale-set)
19. [Container Mode in ARC: Kubernetes, DinD, Kubernetes-Novolume](#container-mode-in-arc)
20. [JIT Runner Registration e Token Lifecycle](#jit-runner-registration-e-token-lifecycle)
21. [Multilabel Support e Routing Avanzato (ARC 0.14+)](#multilabel-support-e-routing-avanzato)
22. [GPU Runners: Configurazione NVIDIA e CUDA](#gpu-runners-configurazione-nvidia-e-cuda)
23. [ARM64 Runners e Build Multi-Architettura](#arm64-runners-e-build-multi-architettura)
24. [Larger Runners GitHub-Hosted](#larger-runners-github-hosted)
25. [Autoscaling Avanzato: Webhook vs Percentage-Based](#autoscaling-avanzato-webhook-vs-percentage-based)
26. [Scale-to-Zero e Ottimizzazione dei Costi](#scale-to-zero-e-ottimizzazione-dei-costi)
27. [Spot Instances e Preemptible VMs per Runner](#spot-instances-e-preemptible-vms-per-runner)
28. [OIDC Authentication dai Runner ai Cloud Provider](#oidc-authentication-dai-runner-ai-cloud-provider)
29. [Supply Chain Security: Lezioni dagli Attacchi 2025-2026](#supply-chain-security-lezioni-dagli-attacchi)
30. [Security Hardening Avanzato](#security-hardening-avanzato)
31. [Osservabilità con Prometheus, Grafana e OpenTelemetry](#osservabilità-con-prometheus-grafana-e-opentelemetry)
32. [Infrastructure as Code per Runner](#infrastructure-as-code-per-runner)
33. [Pricing 2026 e Impatto Economico](#pricing-2026-e-impatto-economico)
34. [Riepilogo](#riepilogo)

---

## Introduzione

I GitHub-hosted runners sono comodi e richiedono zero manutenzione, ma hanno limitazioni significative: hardware fisso (2 CPU, 7 GB RAM per Linux), costo che scala linearmente con l'uso, nessun accesso a risorse di rete private, e impossibilità di usare hardware specializzato come GPU. I self-hosted runners risolvono tutti questi problemi, al costo di una complessità operativa aggiuntiva.

Un self-hosted runner è un'applicazione leggera che si registra con GitHub, riceve i job dei workflow, li esegue sulla macchina locale, e riporta i risultati a GitHub. L'applicazione è open source, disponibile su https://github.com/actions/runner, e supporta Linux, Windows e macOS su architetture x64 e ARM64.

Questa guida copre ogni aspetto dei self-hosted runners, dalla semplice installazione su una singola macchina fino all'autoscaling su Kubernetes con centinaia di runner ephemeral. L'obiettivo è fornire le conoscenze necessarie per costruire un'infrastruttura di CI/CD robusta, sicura e scalabile.

I self-hosted runners possono essere registrati a tre livelli: repository (disponibili solo per un singolo repository), organizzazione (disponibili per tutti i repository dell'organizzazione), e enterprise (disponibili per tutte le organizzazioni dell'enterprise). Il livello di registrazione influenza la gestione, la sicurezza e la scalabilità.

---

## Perché Usare Self-Hosted Runners

### Motivazioni Principali

#### 1. Costi

I GitHub-hosted runners hanno un costo per minuto che si accumula rapidamente per team con molte pipeline:

| Runner Type | Costo/minuto | Costo per 1000 ore/mese |
|------------|-------------|------------------------|
| GitHub-hosted Linux | $0.008 | $480 |
| GitHub-hosted Windows | $0.016 | $960 |
| GitHub-hosted macOS | $0.08 | $4,800 |
| Self-hosted (hardware proprio) | Costo fisso hardware | ~$50-200/mese ammortizzato |
| Self-hosted (cloud VM) | Costo VM | Variabile, tipicamente 40-70% in meno |

Per un team che usa 2000+ ore/mese di CI, il passaggio a self-hosted può ridurre i costi del 60-80%.

#### 2. Performance

I GitHub-hosted runners offrono hardware standardizzato e non particolarmente potente. Con i self-hosted runners si può scegliere hardware ottimale per il proprio workload:

```
GitHub-hosted (standard):
  CPU: 2 core
  RAM: 7 GB
  Storage: 14 GB SSD
  Rete: ~1 Gbps (condivisa)

Self-hosted (esempio server dedicato):
  CPU: 32 core AMD EPYC
  RAM: 128 GB
  Storage: 2 TB NVMe
  Rete: 10 Gbps dedicata
```

Un progetto Java che richiede 15 minuti su GitHub-hosted potrebbe completarsi in 3 minuti su un self-hosted runner con più core e RAM.

#### 3. Accesso a Risorse Private

I self-hosted runners operano all'interno della propria rete, il che significa:

- Accesso diretto a database interni senza esporre porte su Internet
- Accesso a registri Docker privati senza autenticazione esterna
- Connessione a servizi interni (LDAP, NFS, API interne)
- Nessun bisogno di VPN o tunnel per raggiungere l'infrastruttura

#### 4. Hardware Specializzato

Alcuni workload richiedono hardware non disponibile su GitHub-hosted:

- **GPU**: Training ML, test CUDA, rendering
- **ARM**: Build per Raspberry Pi, Apple Silicon nativo
- **FPGA**: Test hardware
- **Alta memoria**: Analisi di dataset grandi, compilazione di progetti enormi
- **Macchine specifiche**: Test su hardware fisico (embedded, IoT)

#### 5. Controllo sull'Ambiente

Con i self-hosted runners si ha pieno controllo su:

- Versione del sistema operativo e patch
- Software preinstallato e versioni
- Configurazione di rete e firewall
- Certificati e trust store
- Cache persistente tra le esecuzioni
- Volumi condivisi e storage

---

## Architettura dei Self-Hosted Runners

### Come Funziona la Comunicazione

```
┌──────────────────┐         HTTPS (long poll)        ┌─────────────────┐
│  GitHub Actions   │◄───────────────────────────────►│  Self-Hosted     │
│  Service          │         (porta 443 outbound)     │  Runner App      │
│                   │                                  │                  │
│  - Queue jobs     │         Nessuna porta inbound    │  - Poll for jobs │
│  - Store results  │         richiesta!               │  - Execute jobs  │
│  - Manage state   │                                  │  - Report status │
└──────────────────┘                                  └─────────────────┘
                                                             │
                                                             ▼
                                                      ┌─────────────────┐
                                                      │  Worker Process  │
                                                      │  (uno per job)   │
                                                      │                  │
                                                      │  - Clone repo    │
                                                      │  - Run steps     │
                                                      │  - Upload logs   │
                                                      └─────────────────┘
```

Punti chiave dell'architettura:

1. **Comunicazione outbound-only**: Il runner si connette a GitHub, non il contrario. Non serve aprire porte inbound nel firewall.
2. **Long polling**: Il runner mantiene una connessione HTTPS persistente verso GitHub e riceve notifiche quando un job è disponibile.
3. **Processo worker isolato**: Ogni job viene eseguito in un processo separato per isolamento.
4. **Auto-update**: Il runner si aggiorna automaticamente quando GitHub rilascia nuove versioni.

### Requisiti di Rete

Il runner deve poter raggiungere i seguenti domini su HTTPS (porta 443):

```
github.com
api.github.com
*.actions.githubusercontent.com
ghcr.io (se si usa GitHub Container Registry)
*.blob.core.windows.net (per il download di strumenti)
objects.githubusercontent.com
*.actions.githubusercontent.com
```

Se il runner è dietro un proxy:

```bash
# Configurare il proxy per il runner
export http_proxy=http://proxy.azienda.com:8080
export https_proxy=http://proxy.azienda.com:8080
export no_proxy=localhost,127.0.0.1,.internal.azienda.com

# Oppure nel file .env del runner
echo "http_proxy=http://proxy.azienda.com:8080" >> .env
echo "https_proxy=http://proxy.azienda.com:8080" >> .env
echo "no_proxy=localhost,127.0.0.1" >> .env
```

---

## Installazione su Linux

### Prerequisiti

```bash
# Requisiti minimi
# - Linux x64 o ARM64
# - .NET 6.0 runtime (bundled con il runner)
# - Git 2.18+
# - Almeno 2 GB RAM libera
# - Almeno 10 GB storage libero

# Pacchetti necessari su Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
  curl \
  jq \
  git \
  libicu-dev \
  libssl-dev \
  lsb-release

# Su RHEL/CentOS/Fedora
sudo dnf install -y \
  curl \
  jq \
  git \
  libicu \
  openssl-libs
```

### Download e Installazione

```bash
# Creare un utente dedicato per il runner (sicurezza)
sudo useradd -m -s /bin/bash github-runner
sudo usermod -aG docker github-runner  # Se serve Docker

# Creare la directory di installazione
sudo mkdir -p /opt/actions-runner
sudo chown github-runner:github-runner /opt/actions-runner

# Passare all'utente runner
sudo su - github-runner
cd /opt/actions-runner

# Scaricare l'ultima versione del runner
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/^v//')
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz \
  -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Verificare l'integrità (opzionale ma raccomandato)
echo "<SHA256_HASH>  actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" | sha256sum -c

# Estrarre
tar xzf actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
```

### Registrazione del Runner

Per registrare un runner serve un token che si ottiene da GitHub:

```bash
# Ottenere il token via CLI (per un repository)
TOKEN=$(gh api repos/{owner}/{repo}/actions/runners/registration-token \
  --method POST -q '.token')

# Ottenere il token per un'organizzazione
TOKEN=$(gh api orgs/{org}/actions/runners/registration-token \
  --method POST -q '.token')

# Configurare il runner
./config.sh \
  --url https://github.com/{owner}/{repo} \
  --token "$TOKEN" \
  --name "linux-runner-01" \
  --labels "linux,x64,docker,production" \
  --work "_work" \
  --runnergroup "Default" \
  --replace

# Output tipico:
# -----------------------------------------------
# |        ____ _ _   _   _       _     _        |
# |       / ___(_) |_| | | |_   _| |__ | |       |
# |      | |  _| | __| |_| | | | | '_ \| |       |
# |      | |_| | | |_|  _  | |_| | |_) |_|       |
# |       \____|_|\__|_| |_|\__,_|_.__/(_)       |
# |                                               |
# |         Self-hosted runner registration       |
# -----------------------------------------------
#
# √ Settings Saved.

# Avviare il runner manualmente (per test)
./run.sh

# Output:
# √ Connected to GitHub
# Current runner version: '2.xxx.x'
# Listening for Jobs
```

### Script di Installazione Automatica

```bash
#!/bin/bash
# install-runner.sh - Script per installazione automatica di un self-hosted runner

set -euo pipefail

# Configurazione
GITHUB_URL="${GITHUB_URL:?'Impostare GITHUB_URL (es. https://github.com/org/repo)'}"
RUNNER_TOKEN="${RUNNER_TOKEN:?'Impostare RUNNER_TOKEN'}"
RUNNER_NAME="${RUNNER_NAME:-$(hostname)}"
RUNNER_LABELS="${RUNNER_LABELS:-linux,x64}"
RUNNER_GROUP="${RUNNER_GROUP:-Default}"
RUNNER_DIR="/opt/actions-runner"
RUNNER_USER="github-runner"

echo "=== Installazione GitHub Actions Self-Hosted Runner ==="
echo "URL: $GITHUB_URL"
echo "Nome: $RUNNER_NAME"
echo "Labels: $RUNNER_LABELS"

# Creare utente
if ! id "$RUNNER_USER" &>/dev/null; then
  sudo useradd -m -s /bin/bash "$RUNNER_USER"
  echo "Utente $RUNNER_USER creato"
fi

# Installare dipendenze
sudo apt-get update -qq
sudo apt-get install -y -qq curl jq git libicu-dev

# Scaricare runner
sudo mkdir -p "$RUNNER_DIR"
sudo chown "$RUNNER_USER:$RUNNER_USER" "$RUNNER_DIR"

RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest \
  | jq -r '.tag_name' | sed 's/^v//')

cd "$RUNNER_DIR"
sudo -u "$RUNNER_USER" curl -sL \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" \
  | sudo -u "$RUNNER_USER" tar xz

# Configurare runner
sudo -u "$RUNNER_USER" ./config.sh \
  --url "$GITHUB_URL" \
  --token "$RUNNER_TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "$RUNNER_LABELS" \
  --runnergroup "$RUNNER_GROUP" \
  --work "_work" \
  --replace \
  --unattended

# Installare come servizio
sudo ./svc.sh install "$RUNNER_USER"
sudo ./svc.sh start

echo "=== Runner installato e avviato come servizio ==="
sudo ./svc.sh status
```

---

## Installazione su Windows

### Prerequisiti Windows

```powershell
# Windows 10/11 o Windows Server 2019+
# PowerShell 5.1+
# Git for Windows
# .NET 6.0 Runtime (bundled)

# Verificare PowerShell
$PSVersionTable.PSVersion

# Installare Git (se necessario)
winget install --id Git.Git -e --source winget
```

### Installazione

```powershell
# Creare directory
New-Item -ItemType Directory -Path "C:\actions-runner" -Force
Set-Location "C:\actions-runner"

# Scaricare il runner
$version = (Invoke-RestMethod -Uri "https://api.github.com/repos/actions/runner/releases/latest").tag_name.TrimStart('v')
$url = "https://github.com/actions/runner/releases/download/v$version/actions-runner-win-x64-$version.zip"
Invoke-WebRequest -Uri $url -OutFile "actions-runner.zip"

# Estrarre
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory("$PWD\actions-runner.zip", "$PWD")

# Configurare
.\config.cmd --url https://github.com/{owner}/{repo} `
  --token "RUNNER_TOKEN" `
  --name "windows-runner-01" `
  --labels "windows,x64,dotnet" `
  --runnergroup "Default" `
  --work "_work" `
  --replace

# Installare come servizio Windows
.\svc.cmd install
.\svc.cmd start

# Verificare lo stato
.\svc.cmd status
Get-Service "actions.runner.*"
```

### Configurazione Servizio Windows Avanzata

```powershell
# Configurare il servizio per eseguire come utente specifico
$serviceName = (Get-Service "actions.runner.*").Name
$credential = Get-Credential -Message "Inserire le credenziali per il servizio runner"

Set-Service -Name $serviceName `
  -Credential $credential `
  -StartupType Automatic

# Configurare recovery automatico
sc.exe failure $serviceName reset=86400 actions=restart/60000/restart/60000/restart/60000

# Aggiungere variabili d'ambiente per il servizio
[Environment]::SetEnvironmentVariable("ACTIONS_RUNNER_PRINT_LOG_TO_STDOUT", "1", "Machine")
```

---

## Installazione su macOS

### Installazione su macOS (Intel e Apple Silicon)

```bash
# Determinare l'architettura
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
  RUNNER_ARCH="osx-arm64"
else
  RUNNER_ARCH="osx-x64"
fi

# Creare directory
mkdir -p ~/actions-runner && cd ~/actions-runner

# Scaricare
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/^v//')
curl -o actions-runner.tar.gz -L \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"

# Estrarre
tar xzf actions-runner.tar.gz

# Configurare
./config.sh \
  --url https://github.com/{owner}/{repo} \
  --token "RUNNER_TOKEN" \
  --name "macos-runner-01" \
  --labels "macos,${ARCH},xcode" \
  --work "_work"
```

### Configurazione come LaunchDaemon su macOS

```bash
# Installare come servizio (usa launchd internamente)
sudo ./svc.sh install

# Il file plist viene creato in /Library/LaunchDaemons/
# Personalizzare se necessario:
sudo cat /Library/LaunchDaemons/actions.runner.*.plist

# Avviare
sudo ./svc.sh start

# Verificare
sudo ./svc.sh status
launchctl list | grep actions.runner
```

Per build iOS/macOS che richiedono accesso all'interfaccia grafica (Xcode UI tests), il runner deve essere eseguito come LaunchAgent anziché LaunchDaemon:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.github.actions.runner</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/ci/actions-runner/runsvc.sh</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/Users/ci/actions-runner</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/tmp/actions-runner.stdout.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/actions-runner.stderr.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
</dict>
</plist>
```

```bash
# Installare come LaunchAgent (per l'utente corrente)
cp com.github.actions.runner.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.github.actions.runner.plist
```

---

## Configurazione come Servizio systemd

Per ambienti Linux di produzione, il runner deve essere configurato come servizio systemd con proper hardening.

### Unit File systemd Base

```ini
# /etc/systemd/system/github-runner.service
[Unit]
Description=GitHub Actions Self-Hosted Runner
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=simple
User=github-runner
Group=github-runner
WorkingDirectory=/opt/actions-runner
ExecStart=/opt/actions-runner/runsvc.sh
Restart=always
RestartSec=10
KillMode=process
KillSignal=SIGTERM
TimeoutStopSec=60

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=github-runner

# Limiti risorse
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

### Unit File con Security Hardening

```ini
# /etc/systemd/system/github-runner.service
[Unit]
Description=GitHub Actions Self-Hosted Runner (Hardened)
After=network-online.target
Wants=network-online.target
Documentation=https://docs.github.com/en/actions/hosting-your-own-runners

[Service]
Type=simple
User=github-runner
Group=github-runner
WorkingDirectory=/opt/actions-runner
ExecStart=/opt/actions-runner/runsvc.sh
Restart=always
RestartSec=10
KillMode=process
KillSignal=SIGTERM
TimeoutStopSec=60

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=github-runner

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/opt/actions-runner
ReadWritePaths=/tmp
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes
RestrictRealtime=yes
RestrictNamespaces=yes
LockPersonality=yes
SystemCallArchitectures=native

# Limiti risorse
LimitNOFILE=65536
LimitNPROC=4096
MemoryMax=8G
CPUQuota=400%
TasksMax=512

# Ambiente
Environment="RUNNER_ALLOW_RUNASROOT=0"
Environment="DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1"

[Install]
WantedBy=multi-user.target
```

### Gestione del Servizio

```bash
# Abilitare e avviare il servizio
sudo systemctl daemon-reload
sudo systemctl enable github-runner.service
sudo systemctl start github-runner.service

# Verificare lo stato
sudo systemctl status github-runner.service

# Output tipico:
# ● github-runner.service - GitHub Actions Self-Hosted Runner
#      Loaded: loaded (/etc/systemd/system/github-runner.service; enabled)
#      Active: active (running) since ...
#    Main PID: 12345 (Runner.Listener)
#      Memory: 150.2M
#      CGroup: /system.slice/github-runner.service
#              └─12345 /opt/actions-runner/bin/Runner.Listener

# Consultare i log
sudo journalctl -u github-runner.service -f
sudo journalctl -u github-runner.service --since "1 hour ago"
sudo journalctl -u github-runner.service --no-pager -n 100

# Riavviare
sudo systemctl restart github-runner.service

# Fermare
sudo systemctl stop github-runner.service
```

### Multipli Runner sulla Stessa Macchina

Per eseguire più runner sulla stessa macchina (uno per core, ad esempio):

```bash
#!/bin/bash
# setup-multi-runner.sh

NUM_RUNNERS=4
BASE_DIR="/opt/actions-runners"
GITHUB_URL="https://github.com/org/repo"

for i in $(seq 1 $NUM_RUNNERS); do
  RUNNER_DIR="${BASE_DIR}/runner-${i}"
  RUNNER_NAME="$(hostname)-runner-${i}"

  echo "=== Configurazione runner $i ==="

  # Creare directory
  sudo mkdir -p "$RUNNER_DIR"
  sudo chown github-runner:github-runner "$RUNNER_DIR"

  # Copiare i file del runner
  sudo -u github-runner cp -r /opt/actions-runner-template/* "$RUNNER_DIR/"

  # Ottenere token
  TOKEN=$(gh api repos/{owner}/{repo}/actions/runners/registration-token \
    --method POST -q '.token')

  # Configurare
  cd "$RUNNER_DIR"
  sudo -u github-runner ./config.sh \
    --url "$GITHUB_URL" \
    --token "$TOKEN" \
    --name "$RUNNER_NAME" \
    --labels "linux,x64,docker" \
    --work "_work" \
    --replace \
    --unattended

  # Creare unit file systemd
  cat > /etc/systemd/system/github-runner-${i}.service << EOF
[Unit]
Description=GitHub Actions Runner ${i}
After=network-online.target

[Service]
Type=simple
User=github-runner
WorkingDirectory=${RUNNER_DIR}
ExecStart=${RUNNER_DIR}/runsvc.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

  sudo systemctl daemon-reload
  sudo systemctl enable github-runner-${i}.service
  sudo systemctl start github-runner-${i}.service
done

echo "=== $NUM_RUNNERS runner configurati e avviati ==="
```

---

## Runner Groups e Labels

### Labels

Le labels permettono di indirizzare i job a runner specifici. Ogni runner ha tre label automatiche (sistema operativo, architettura, `self-hosted`) più labels personalizzate.

```yaml
# Workflow che usa labels specifiche
name: Build con Label

on: push

jobs:
  build-linux:
    runs-on: [self-hosted, linux, x64, docker]
    steps:
      - run: echo "Eseguito su un runner Linux con Docker"

  build-windows:
    runs-on: [self-hosted, windows, x64, dotnet]
    steps:
      - run: echo "Eseguito su un runner Windows con .NET"

  build-macos:
    runs-on: [self-hosted, macos, arm64, xcode]
    steps:
      - run: echo "Eseguito su un runner macOS con Xcode"

  gpu-training:
    runs-on: [self-hosted, linux, gpu, cuda-12]
    steps:
      - run: nvidia-smi
      - run: echo "Eseguito su un runner con GPU CUDA 12"

  high-memory:
    runs-on: [self-hosted, linux, high-memory]
    steps:
      - run: free -h
      - run: echo "Eseguito su un runner con alta memoria"
```

### Gestione Labels via API

```bash
# Aggiungere labels a un runner esistente
RUNNER_ID=123
gh api repos/{owner}/{repo}/actions/runners/${RUNNER_ID}/labels \
  --method POST \
  --input - << 'EOF'
{
  "labels": ["docker", "gpu", "cuda-12"]
}
EOF

# Rimuovere una label
gh api repos/{owner}/{repo}/actions/runners/${RUNNER_ID}/labels/gpu \
  --method DELETE

# Elencare tutti i runner con le loro labels
gh api repos/{owner}/{repo}/actions/runners \
  --jq '.runners[] | {id: .id, name: .name, status: .status, labels: [.labels[].name]}'

# Output:
# {
#   "id": 123,
#   "name": "linux-runner-01",
#   "status": "online",
#   "labels": ["self-hosted", "linux", "x64", "docker", "production"]
# }
```

### Runner Groups

I runner groups permettono di controllare quali repository possono usare quali runner, utile per separare ambienti di produzione e sviluppo.

```bash
# Creare un runner group (livello organizzazione)
gh api orgs/{org}/actions/runner-groups \
  --method POST \
  --input - << 'EOF'
{
  "name": "production-runners",
  "visibility": "selected",
  "selected_repository_ids": [123, 456, 789],
  "allows_public_repositories": false,
  "restricted_to_workflows": true,
  "selected_workflows": [
    "org/repo/.github/workflows/deploy-prod.yml@refs/heads/main"
  ]
}
EOF

# Elencare i runner groups
gh api orgs/{org}/actions/runner-groups \
  --jq '.runner_groups[] | {id: .id, name: .name, visibility: .visibility}'

# Aggiungere un runner a un group
gh api orgs/{org}/actions/runner-groups/{group_id}/runners \
  --method PUT \
  --input - << 'EOF'
{
  "runners": [1, 2, 3]
}
EOF
```

---

## Docker-in-Docker su Self-Hosted Runners

Molti workflow CI/CD richiedono Docker per costruire immagini, eseguire test in container, o deployare. Sui self-hosted runners ci sono diverse strategie per abilitare Docker.

### Approccio 1: Docker Socket Bind Mount

Il modo più semplice è dare al runner accesso al Docker daemon dell'host:

```bash
# Aggiungere l'utente runner al gruppo docker
sudo usermod -aG docker github-runner

# Verificare
sudo -u github-runner docker info
```

```yaml
# Workflow che usa Docker direttamente
name: Build Docker Image

on: push

jobs:
  build:
    runs-on: [self-hosted, linux, docker]
    steps:
      - uses: actions/checkout@v4

      - name: Build immagine
        run: docker build -t myapp:${{ github.sha }} .

      - name: Push al registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker push myapp:${{ github.sha }}
```

**Attenzione sicurezza**: L'accesso al Docker socket equivale a root sull'host. Usare questo approccio solo con runner dedicati e isolati.

### Approccio 2: Docker-in-Docker (DinD)

Per maggiore isolamento, eseguire il runner stesso in un container Docker con DinD:

```dockerfile
# Dockerfile per runner con Docker-in-Docker
FROM ubuntu:22.04

# Installare dipendenze
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    git \
    sudo \
    libicu-dev \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Creare utente runner
RUN useradd -m -s /bin/bash runner && \
    usermod -aG sudo runner && \
    echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Installare il runner
ARG RUNNER_VERSION=2.314.1
RUN mkdir /home/runner/actions-runner && \
    cd /home/runner/actions-runner && \
    curl -sL "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" \
    | tar xz && \
    chown -R runner:runner /home/runner/actions-runner

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER runner
WORKDIR /home/runner/actions-runner

ENTRYPOINT ["/entrypoint.sh"]
```

```bash
#!/bin/bash
# entrypoint.sh

# Avviare Docker daemon in background
sudo dockerd &

# Attendere che Docker sia pronto
echo "Attesa avvio Docker daemon..."
while ! docker info > /dev/null 2>&1; do
  sleep 1
done
echo "Docker daemon pronto"

# Configurare il runner
./config.sh \
  --url "${GITHUB_URL}" \
  --token "${RUNNER_TOKEN}" \
  --name "${RUNNER_NAME:-$(hostname)}" \
  --labels "${RUNNER_LABELS:-linux,x64,docker}" \
  --ephemeral \
  --unattended \
  --replace

# Avviare il runner
./run.sh
```

```bash
# Eseguire il runner con Docker-in-Docker
docker run -d \
  --name github-runner \
  --privileged \
  -e GITHUB_URL="https://github.com/org/repo" \
  -e RUNNER_TOKEN="XXXXX" \
  -e RUNNER_NAME="dind-runner-01" \
  -e RUNNER_LABELS="linux,x64,docker,dind" \
  github-runner:latest
```

### Approccio 3: Rootless Docker (Più Sicuro)

```bash
# Installare Docker rootless
curl -fsSL https://get.docker.com/rootless | sh

# Configurare per l'utente runner
loginctl enable-linger github-runner
sudo -u github-runner bash << 'EOF'
export PATH=$HOME/bin:$PATH
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock
dockerd-rootless &
EOF
```

### Docker Compose nei Workflow

```yaml
name: Integration Tests

on: pull_request

jobs:
  test:
    runs-on: [self-hosted, linux, docker]
    steps:
      - uses: actions/checkout@v4

      - name: Avviare servizi con docker-compose
        run: |
          docker compose -f docker-compose.test.yml up -d
          # Attendere che i servizi siano pronti
          docker compose -f docker-compose.test.yml exec -T app ./wait-for-it.sh db:5432 -- echo "DB pronto"

      - name: Eseguire test di integrazione
        run: |
          docker compose -f docker-compose.test.yml exec -T app npm run test:integration

      - name: Raccogliere log in caso di fallimento
        if: failure()
        run: |
          docker compose -f docker-compose.test.yml logs > docker-logs.txt
          cat docker-logs.txt

      - name: Pulizia
        if: always()
        run: |
          docker compose -f docker-compose.test.yml down -v
          docker system prune -f
```

---

## Autoscaling dei Runners

### Perché Autoscaling

In un team con carichi di CI/CD variabili, avere un numero fisso di runner è inefficiente: troppi runner significano costi inutili durante i periodi calmi, troppo pochi causano code e rallentamenti durante i picchi (es. dopo un merge su main che triggerà tutti i workflow).

### Approccio con Webhook + Cloud API

```python
#!/usr/bin/env python3
# autoscaler.py - Autoscaler basato su webhook GitHub

import json
import subprocess
import time
from flask import Flask, request
from threading import Thread

app = Flask(__name__)

# Configurazione
MAX_RUNNERS = 10
MIN_RUNNERS = 1
CLOUD_PROVIDER = "aws"  # o "gcp", "azure"

active_runners = {}

def create_runner(runner_id: str):
    """Creare una nuova VM con runner preconfigurato."""
    if CLOUD_PROVIDER == "aws":
        result = subprocess.run([
            "aws", "ec2", "run-instances",
            "--image-id", "ami-0123456789abcdef0",  # AMI con runner preinstallato
            "--instance-type", "c5.2xlarge",
            "--count", "1",
            "--key-name", "ci-runner-key",
            "--security-group-ids", "sg-runner",
            "--subnet-id", "subnet-private",
            "--tag-specifications", f"ResourceType=instance,Tags=[{{Key=Name,Value=runner-{runner_id}}}]",
            "--user-data", f"""#!/bin/bash
cd /opt/actions-runner
TOKEN=$(curl -s -X POST \
  -H "Authorization: token ${{GITHUB_PAT}}" \
  https://api.github.com/repos/org/repo/actions/runners/registration-token \
  | jq -r '.token')
./config.sh --url https://github.com/org/repo --token $TOKEN --name runner-{runner_id} --ephemeral --unattended
./run.sh
# La VM si auto-termina dopo il job grazie a --ephemeral
aws ec2 terminate-instances --instance-ids $(curl -s http://169.254.169.254/latest/meta-data/instance-id)
"""
        ], capture_output=True, text=True)
        return result.returncode == 0

def destroy_runner(instance_id: str):
    """Terminare una VM runner."""
    subprocess.run([
        "aws", "ec2", "terminate-instances",
        "--instance-ids", instance_id
    ])

@app.route("/webhook", methods=["POST"])
def webhook():
    event = request.headers.get("X-GitHub-Event")
    payload = request.json

    if event == "workflow_job":
        action = payload["action"]

        if action == "queued":
            runner_count = len(active_runners)
            if runner_count < MAX_RUNNERS:
                runner_id = f"auto-{int(time.time())}"
                Thread(target=create_runner, args=(runner_id,)).start()
                print(f"Scaling up: creating runner {runner_id}")

        elif action == "completed":
            runner_name = payload.get("workflow_job", {}).get("runner_name", "")
            if runner_name in active_runners:
                Thread(target=destroy_runner, args=(active_runners[runner_name],)).start()
                del active_runners[runner_name]
                print(f"Scaling down: destroying runner {runner_name}")

    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

---

## Runners Ephemeral

I runner ephemeral sono runner che eseguono un singolo job e poi si de-registrano automaticamente. Questo approccio offre massima sicurezza e pulizia, poiché ogni job ha un ambiente completamente pulito.

```bash
# Registrare un runner come ephemeral
./config.sh \
  --url https://github.com/org/repo \
  --token "$TOKEN" \
  --name "ephemeral-runner-$(date +%s)" \
  --labels "linux,x64,ephemeral" \
  --ephemeral \
  --unattended

# Il runner eseguirà un solo job e poi si fermerà
./run.sh
# Dopo il job: "Runner listener exited with return code 0"
# Il runner è ora deregistrato da GitHub
```

### Script per Runner Ephemeral Continuo

```bash
#!/bin/bash
# run-ephemeral-loop.sh
# Esegue runner ephemeral in loop, creando un nuovo runner per ogni job

set -euo pipefail

GITHUB_URL="${GITHUB_URL:?}"
RUNNER_DIR="/opt/actions-runner"
RUNNER_LABELS="${RUNNER_LABELS:-linux,x64,ephemeral}"

cleanup() {
  echo "Pulizia ambiente..."
  cd "$RUNNER_DIR"
  # Pulire la work directory
  rm -rf _work/*
  # Pulire cache temporanee
  rm -rf /tmp/runner-*
  # Pulire immagini Docker non usate
  docker system prune -af --volumes 2>/dev/null || true
}

while true; do
  echo "=== Avvio nuovo runner ephemeral: $(date) ==="

  # Ottenere nuovo token
  TOKEN=$(curl -s -X POST \
    -H "Authorization: token ${GITHUB_PAT}" \
    -H "Accept: application/vnd.github.v3+json" \
    "${GITHUB_URL}/actions/runners/registration-token" \
    | jq -r '.token')

  if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "Errore: impossibile ottenere il token. Retry in 30 secondi..."
    sleep 30
    continue
  fi

  cd "$RUNNER_DIR"

  # Configurare
  ./config.sh \
    --url "$GITHUB_URL" \
    --token "$TOKEN" \
    --name "ephemeral-$(hostname)-$(date +%s)" \
    --labels "$RUNNER_LABELS" \
    --ephemeral \
    --unattended \
    --replace 2>/dev/null || true

  # Eseguire (blocca fino al completamento del job o timeout)
  ./run.sh || true

  # Pulizia
  cleanup

  echo "=== Runner ephemeral completato. Riavvio... ==="
  sleep 5
done
```

---

## Actions Runner Controller su Kubernetes

L'Actions Runner Controller (ARC) è il modo ufficiale per eseguire self-hosted runners su Kubernetes con autoscaling.

### Installazione con Helm

```bash
# Aggiungere il repository Helm
helm repo add actions-runner-controller \
  https://actions-runner-controller.github.io/actions-runner-controller
helm repo update

# Creare namespace
kubectl create namespace actions-runner-system

# Creare secret per l'autenticazione GitHub
# Opzione 1: Personal Access Token
kubectl create secret generic controller-manager \
  -n actions-runner-system \
  --from-literal=github_token=ghp_xxxxxxxxxxxxxxxxxxxx

# Opzione 2: GitHub App (raccomandato per produzione)
kubectl create secret generic controller-manager \
  -n actions-runner-system \
  --from-literal=github_app_id=12345 \
  --from-literal=github_app_installation_id=67890 \
  --from-file=github_app_private_key=app-private-key.pem

# Installare il controller
helm install actions-runner-controller \
  actions-runner-controller/actions-runner-controller \
  -n actions-runner-system \
  --set syncPeriod=1m \
  --set authSecret.create=false \
  --set authSecret.name=controller-manager
```

### Configurazione RunnerDeployment

```yaml
# runner-deployment.yaml
apiVersion: actions.summerwind.dev/v1alpha1
kind: RunnerDeployment
metadata:
  name: main-runners
  namespace: actions-runner-system
spec:
  replicas: 3
  template:
    spec:
      repository: org/repo
      # Oppure per l'intera organizzazione:
      # organization: org
      labels:
        - linux
        - x64
        - kubernetes
      group: production-runners
      ephemeral: true
      dockerEnabled: true
      dockerdWithinRunnerContainer: true
      image: summerwind/actions-runner-dind:latest
      resources:
        limits:
          cpu: "4"
          memory: "8Gi"
        requests:
          cpu: "2"
          memory: "4Gi"
      volumeMounts:
        - name: work
          mountPath: /runner/_work
      volumes:
        - name: work
          emptyDir:
            sizeLimit: 50Gi
      env:
        - name: RUNNER_FEATURE_FLAG_ONCE
          value: "true"
```

### HorizontalRunnerAutoscaler

```yaml
# autoscaler.yaml
apiVersion: actions.summerwind.dev/v1alpha1
kind: HorizontalRunnerAutoscaler
metadata:
  name: main-runners-autoscaler
  namespace: actions-runner-system
spec:
  scaleTargetRef:
    kind: RunnerDeployment
    name: main-runners
  minReplicas: 1
  maxReplicas: 20
  scaleDownDelaySecondsAfterScaleOut: 300
  metrics:
    - type: TotalNumberOfQueuedAndInProgressWorkflowRuns
      repositoryNames:
        - org/repo
  scaleUpTriggers:
    - amount: 1
      duration: "5m"
      githubEvent:
        workflowJob: {}
```

### Runner Personalizzato con Tool Preinstallati

```dockerfile
# Dockerfile.custom-runner
FROM summerwind/actions-runner-dind:latest

# Installare tool aggiuntivi
RUN sudo apt-get update && sudo apt-get install -y \
    python3 \
    python3-pip \
    nodejs \
    npm \
    openjdk-17-jdk \
    maven \
    gradle \
    kubectl \
    helm \
    terraform \
    && sudo rm -rf /var/lib/apt/lists/*

# Installare tool Go
RUN curl -sL https://go.dev/dl/go1.22.0.linux-amd64.tar.gz | sudo tar -C /usr/local -xz
ENV PATH=$PATH:/usr/local/go/bin

# Installare tool Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH=$PATH:/home/runner/.cargo/bin

# Pre-scaricare immagini Docker comuni per velocizzare le build
RUN docker pull node:20-alpine && \
    docker pull python:3.12-slim && \
    docker pull postgres:16-alpine && \
    docker pull redis:7-alpine
```

```yaml
# Usare l'immagine personalizzata
apiVersion: actions.summerwind.dev/v1alpha1
kind: RunnerDeployment
metadata:
  name: custom-runners
spec:
  replicas: 2
  template:
    spec:
      repository: org/repo
      image: ghcr.io/org/custom-runner:latest
      labels:
        - linux
        - custom-tools
        - kubernetes
```

---

## Security Hardening

### Principi di Sicurezza per Self-Hosted Runners

I self-hosted runners introducono rischi di sicurezza significativi, specialmente per repository pubblici. Un workflow malevolo (da una PR) potrebbe eseguire codice arbitrario sulla macchina del runner, accedendo a segreti, rete interna, e potenzialmente altre risorse.

**Regola fondamentale**: Non usare MAI self-hosted runners per repository pubblici senza protezioni adeguate.

### Isolamento di Rete

```
┌─────────────────────────────────────────┐
│                 VPC/VLAN                 │
│                                         │
│  ┌───────────────┐   ┌──────────────┐  │
│  │ Runner Subnet  │   │ App Subnet   │  │
│  │ 10.0.1.0/24   │   │ 10.0.2.0/24  │  │
│  │               │   │              │  │
│  │ ┌───────────┐ │   │ ┌──────────┐ │  │
│  │ │ Runner 1  │ │──►│ │ Registry │ │  │
│  │ └───────────┘ │   │ └──────────┘ │  │
│  │ ┌───────────┐ │   │              │  │
│  │ │ Runner 2  │ │   │              │  │
│  │ └───────────┘ │   │              │  │
│  └───────┬───────┘   └──────────────┘  │
│          │                              │
│  ┌───────▼───────┐                     │
│  │ NAT Gateway   │ ──► Internet        │
│  │ (solo outbound)│    (solo GitHub)    │
│  └───────────────┘                     │
│                                         │
└─────────────────────────────────────────┘
```

```bash
# Regole firewall (iptables) per un runner isolato
# Permettere solo traffico outbound verso GitHub
iptables -A OUTPUT -p tcp --dport 443 -d api.github.com -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -d github.com -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -d *.actions.githubusercontent.com -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -d ghcr.io -j ACCEPT

# Permettere DNS
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# Permettere accesso al registry interno
iptables -A OUTPUT -p tcp --dport 5000 -d 10.0.2.10 -j ACCEPT

# Bloccare tutto il resto
iptables -A OUTPUT -j DROP
```

### Pulizia dell'Ambiente tra i Job

```bash
#!/bin/bash
# cleanup-between-jobs.sh
# Da eseguire come hook post-job

echo "=== Pulizia post-job ==="

# Pulire la work directory
rm -rf /opt/actions-runner/_work/*

# Pulire file temporanei
rm -rf /tmp/* /var/tmp/*

# Pulire cache npm/pip/maven
rm -rf ~/.npm ~/.cache/pip ~/.m2/repository

# Pulire Docker
docker system prune -af --volumes 2>/dev/null || true

# Pulire processi orfani
pkill -u github-runner -f "node|python|java" 2>/dev/null || true

# Reset variabili d'ambiente
unset $(env | grep -oP '^RUNNER_TOOL_CACHE|^GITHUB_' | cut -d= -f1) 2>/dev/null || true

# Verificare che non ci siano credenziali residue
if [ -f ~/.docker/config.json ]; then
  echo '{}' > ~/.docker/config.json
fi

echo "=== Pulizia completata ==="
```

### Limitare i Workflow che Possono Usare i Runner

```yaml
# In un runner group, limitare ai workflow specifici:
# - Solo workflow dal branch main
# - Solo workflow specifici

# Via API
gh api orgs/{org}/actions/runner-groups/{group_id} \
  --method PATCH \
  --input - << 'EOF'
{
  "restricted_to_workflows": true,
  "selected_workflows": [
    "org/repo/.github/workflows/deploy.yml@refs/heads/main",
    "org/repo/.github/workflows/release.yml@refs/heads/main"
  ]
}
EOF
```

### Workflow con `pull_request_target` Sicuro

```yaml
# PERICOLOSO - Non fare questo con self-hosted runners!
# on: pull_request  <-- esegue il codice della PR, che potrebbe essere malevolo

# SICURO per self-hosted runners
on:
  pull_request_target:  # Esegue il codice del branch base, non della PR
    types: [labeled]

jobs:
  test:
    if: contains(github.event.pull_request.labels.*.name, 'safe-to-test')
    runs-on: [self-hosted, linux]
    steps:
      # Checkout del codice base (sicuro)
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          # Solo dopo che un maintainer ha aggiunto il label "safe-to-test"
```

---

## Monitoraggio e Osservabilità

### Script di Health Check

```bash
#!/bin/bash
# health-check.sh - Monitoraggio salute dei runner

RUNNERS_API="https://api.github.com/repos/{owner}/{repo}/actions/runners"
ALERT_WEBHOOK="${SLACK_WEBHOOK:-}"

# Ottenere stato dei runner
RUNNERS=$(curl -s \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  "$RUNNERS_API")

TOTAL=$(echo "$RUNNERS" | jq '.total_count')
ONLINE=$(echo "$RUNNERS" | jq '[.runners[] | select(.status == "online")] | length')
OFFLINE=$(echo "$RUNNERS" | jq '[.runners[] | select(.status == "offline")] | length')
BUSY=$(echo "$RUNNERS" | jq '[.runners[] | select(.busy == true)] | length')

echo "=== Stato Runner: $(date) ==="
echo "Totale: $TOTAL"
echo "Online: $ONLINE"
echo "Offline: $OFFLINE"
echo "Occupati: $BUSY"
echo "Disponibili: $((ONLINE - BUSY))"

# Alert se troppi runner offline
if [ "$OFFLINE" -gt 0 ]; then
  OFFLINE_NAMES=$(echo "$RUNNERS" | jq -r '.runners[] | select(.status == "offline") | .name')
  echo "ALERT: Runner offline: $OFFLINE_NAMES"

  if [ -n "$ALERT_WEBHOOK" ]; then
    curl -s -X POST "$ALERT_WEBHOOK" \
      -H "Content-Type: application/json" \
      -d "{\"text\": \"⚠️ $OFFLINE runner offline: $OFFLINE_NAMES\"}"
  fi
fi

# Alert se tutti i runner sono occupati
if [ "$ONLINE" -eq "$BUSY" ] && [ "$ONLINE" -gt 0 ]; then
  echo "ALERT: Tutti i runner sono occupati! I job saranno in coda."
fi

# Controllare risorse di sistema
echo ""
echo "=== Risorse Sistema ==="
echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}')% utilizzata"
echo "RAM: $(free -h | awk '/Mem:/ {print $3 "/" $2}')"
echo "Disco: $(df -h /opt/actions-runner | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')"
echo "Docker images: $(docker images | wc -l) immagini, $(docker system df --format '{{.Size}}' | head -1)"
```

### Prometheus Metrics con Node Exporter

```yaml
# prometheus.yml - Configurazione Prometheus per monitorare i runner
scrape_configs:
  - job_name: 'github-runner-nodes'
    static_configs:
      - targets:
        - 'runner-01:9100'
        - 'runner-02:9100'
        - 'runner-03:9100'
    relabel_configs:
      - source_labels: [__address__]
        target_label: runner_name

  - job_name: 'github-runner-custom'
    static_configs:
      - targets:
        - 'runner-01:9090'
        - 'runner-02:9090'
        - 'runner-03:9090'
```

### Dashboard Grafana (Query PromQL)

```
# CPU utilization per runner
100 - (avg by (runner_name) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage per runner
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk usage per runner
100 - ((node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100)

# Network traffic
rate(node_network_receive_bytes_total{device="eth0"}[5m])
rate(node_network_transmit_bytes_total{device="eth0"}[5m])
```

### GitHub Actions Workflow per Monitoraggio

```yaml
# .github/workflows/monitor-runners.yml
name: Monitor Runners

on:
  schedule:
    - cron: '*/15 * * * *'  # Ogni 15 minuti
  workflow_dispatch:

jobs:
  check-runners:
    runs-on: ubuntu-latest  # Usare GitHub-hosted per il monitoraggio!
    steps:
      - name: Controllare stato runner
        run: |
          RUNNERS=$(gh api repos/${{ github.repository }}/actions/runners)

          TOTAL=$(echo "$RUNNERS" | jq '.total_count')
          ONLINE=$(echo "$RUNNERS" | jq '[.runners[] | select(.status == "online")] | length')
          OFFLINE=$(echo "$RUNNERS" | jq '[.runners[] | select(.status == "offline")] | length')

          echo "## Runner Status" >> $GITHUB_STEP_SUMMARY
          echo "| Metrica | Valore |" >> $GITHUB_STEP_SUMMARY
          echo "|---------|--------|" >> $GITHUB_STEP_SUMMARY
          echo "| Totale | $TOTAL |" >> $GITHUB_STEP_SUMMARY
          echo "| Online | $ONLINE |" >> $GITHUB_STEP_SUMMARY
          echo "| Offline | $OFFLINE |" >> $GITHUB_STEP_SUMMARY

          if [ "$OFFLINE" -gt 0 ]; then
            echo ""
            echo "### Runner Offline" >> $GITHUB_STEP_SUMMARY
            echo "$RUNNERS" | jq -r '.runners[] | select(.status == "offline") | "- \(.name) (last seen: \(.labels | map(.name) | join(", ")))"' >> $GITHUB_STEP_SUMMARY
            exit 1
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Notificare se ci sono problemi
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "⚠️ Runner offline rilevati! Controllare: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Troubleshooting

### Problema: Runner Offline

```bash
# 1. Verificare che il servizio sia in esecuzione
sudo systemctl status github-runner.service

# Se il servizio è fermo:
sudo journalctl -u github-runner.service -n 50 --no-pager

# 2. Verificare la connettività di rete
curl -s -o /dev/null -w "%{http_code}" https://api.github.com
# Deve restituire 200

# Testare tutti gli endpoint necessari
for domain in github.com api.github.com codeload.githubusercontent.com; do
  echo -n "$domain: "
  curl -s -o /dev/null -w "%{http_code}" "https://$domain"
  echo ""
done

# 3. Verificare che il token non sia scaduto
# I token di registrazione scadono dopo 1 ora
# Se necessario, ri-registrare il runner:
./config.sh remove --token "$OLD_TOKEN"
TOKEN=$(gh api repos/{owner}/{repo}/actions/runners/registration-token --method POST -q '.token')
./config.sh --url https://github.com/org/repo --token "$TOKEN" --name "runner-01" --replace --unattended

# 4. Verificare i permessi del filesystem
ls -la /opt/actions-runner/
# Tutti i file devono essere di proprietà dell'utente runner

# 5. Verificare lo spazio su disco
df -h /opt/actions-runner/
# Se lo spazio è esaurito, pulire:
rm -rf /opt/actions-runner/_work/*
docker system prune -af --volumes
```

### Problema: Job in Coda Troppo a Lungo

```bash
# Verificare quanti job sono in coda
gh api repos/{owner}/{repo}/actions/runs \
  --jq '[.workflow_runs[] | select(.status == "queued")] | length'

# Verificare quanti runner sono disponibili
gh api repos/{owner}/{repo}/actions/runners \
  --jq '{
    online: [.runners[] | select(.status == "online")] | length,
    busy: [.runners[] | select(.busy == true)] | length,
    available: [.runners[] | select(.status == "online" and .busy == false)] | length
  }'

# Verificare che le labels matchino
# Un job con runs-on: [self-hosted, linux, gpu] non girerà su un runner
# che ha solo le labels [self-hosted, linux, x64]
gh api repos/{owner}/{repo}/actions/runners \
  --jq '.runners[] | {name: .name, status: .status, labels: [.labels[].name]}'
```

### Problema: Errori di Permessi

```bash
# Errore: "Permission denied" durante il clone
# Verificare che Git sia configurato correttamente
sudo -u github-runner git config --global --list

# Errore: "Permission denied" per Docker
# Verificare appartenenza al gruppo docker
groups github-runner
# Se docker non è presente:
sudo usermod -aG docker github-runner
sudo systemctl restart github-runner.service

# Errore: "EACCES" su file nella work directory
# Reset permessi
sudo chown -R github-runner:github-runner /opt/actions-runner/_work
```

### Problema: Runner Lento

```bash
# 1. Controllare carico CPU
top -bn1 | head -20

# 2. Controllare I/O disco
iostat -x 1 5

# 3. Controllare se Docker sta consumando troppo spazio
docker system df
docker system df -v

# 4. Controllare se ci sono processi zombie da job precedenti
ps aux | grep -E "defunct|zombie"

# 5. Analizzare i tempi dei job
# Usare il GitHub Actions timing nella UI per identificare gli step lenti

# 6. Verificare se il runner sta facendo troppi download
# Le actions vengono scaricate ad ogni job; usare tool cache:
# In .github/workflows:
# - uses: actions/setup-node@v4
#   with:
#     node-version: '20'
#     cache: 'npm'  # <-- Cache delle dipendenze
```

---

## Confronto Costi

### Scenario: Team di 10 Sviluppatori

Assunzioni: 50 PR/settimana, media 10 minuti per pipeline, 3 pipeline per PR (lint, test, build).

```
Minuti CI/settimana: 50 × 3 × 10 = 1,500 minuti
Minuti CI/mese: 1,500 × 4 = 6,000 minuti = 100 ore

=== GitHub-Hosted ===
Linux: 6,000 min × $0.008/min = $48/mese
Se anche Windows: + 2,000 min × $0.016/min = +$32/mese
Se anche macOS: + 1,000 min × $0.08/min = +$80/mese
Totale stimato: $48 - $160/mese

=== Self-Hosted (Cloud VM) ===
2 × c5.xlarge (4 vCPU, 8 GB) on-demand:
  2 × $0.17/ora × 730 ore/mese = $248/mese

2 × c5.xlarge con Reserved Instance (1 anno):
  2 × $0.10/ora × 730 ore/mese = $146/mese

2 × c5.xlarge Spot Instance (media):
  2 × $0.05/ora × 730 ore/mese = $73/mese

=== Self-Hosted (Hardware Proprio) ===
1 × Server dedicato (32 core, 64 GB RAM):
  Costo hardware: ~$2,000 (ammortizzato su 3 anni = $55/mese)
  Elettricità: ~$30/mese
  Manutenzione: ~$20/mese
  Totale: ~$105/mese
  Ma: prestazioni ~8x superiori ai GitHub-hosted
```

### Quando Conviene il Self-Hosted

| Scenario | GitHub-Hosted | Self-Hosted |
|----------|:------------:|:-----------:|
| < 2,000 min/mese Linux | Migliore | Non conviene |
| > 10,000 min/mese Linux | Costoso | Molto conveniente |
| Build macOS (iOS) | Molto costoso | Molto conveniente |
| Necessità di GPU | Non disponibile | Unica opzione |
| Accesso rete privata | Impossibile | Necessario |
| Team < 5 sviluppatori | Migliore | Overhead eccessivo |
| Team > 20 sviluppatori | Costoso | Conveniente |
| Requisiti compliance | Limitato | Pieno controllo |

---

## Best Practice

### 1. Usare Runner Ephemeral Dove Possibile

Runner ephemeral forniscono un ambiente pulito per ogni job, eliminando problemi di stato residuo e migliorando la sicurezza. Ogni job inizia da zero.

### 2. Separare Runner per Ambiente

Non usare gli stessi runner per sviluppo e produzione. Un runner che ha accesso alle credenziali di produzione non deve eseguire codice da PR non reviewate.

### 3. Mantenere i Runner Aggiornati

Il runner si aggiorna automaticamente, ma il sistema operativo e i tool installati no:

```bash
# Cron job per aggiornamenti automatici
# /etc/cron.d/runner-updates
0 3 * * 0 root apt-get update && apt-get upgrade -y && systemctl restart github-runner
```

### 4. Implementare Cache Persistente

```yaml
# Usare cache actions per velocizzare le build
- uses: actions/cache@v4
  with:
    path: |
      ~/.npm
      ~/.cache/pip
      ~/.m2/repository
    key: ${{ runner.os }}-deps-${{ hashFiles('**/package-lock.json', '**/requirements.txt') }}
```

### 5. Monitorare e Alertare

Non assumere che i runner funzionino. Implementare monitoraggio proattivo e alerting per:
- Runner offline
- Spazio disco basso
- CPU/RAM al limite
- Job in coda per troppo tempo
- Errori ricorrenti nei workflow

### 6. Documentare la Configurazione

Trattare la configurazione dei runner come Infrastructure as Code. Usare script di provisioning (Ansible, Terraform, Packer) per poter ricreare un runner in minuti.

---

## ARC Moderno: Architettura gha-runner-scale-set

A partire dal 2024, GitHub ha consolidato l'architettura ufficiale di ARC attorno al concetto di **Runner Scale Set**, abbandonando progressivamente i vecchi CRD (`RunnerDeployment`, `HorizontalRunnerAutoscaler`) a favore di un sistema a due chart Helm basato su immagini OCI. L'architettura moderna risolve problemi critici di rate-limiting delle API GitHub e migliora la sicurezza eliminando la necessità di passare PAT ai pod runner.

### Architettura a Due Chart

Il sistema moderno si compone di due chart Helm indipendenti:

1. **gha-runner-scale-set-controller**: Il controller che gestisce il ciclo di vita di tutti i runner scale set nel cluster. Si installa una sola volta per cluster.
2. **gha-runner-scale-set**: Definisce un singolo scale set di runner. Si installa una volta per ogni combinazione di repository/organizzazione e configurazione runner desiderata.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                            │
│                                                                 │
│  ┌──────────────────────────────┐                               │
│  │ Namespace: arc-systems       │                               │
│  │                              │                               │
│  │  ┌────────────────────────┐  │                               │
│  │  │ ARC Controller Manager │  │                               │
│  │  │ (gha-runner-scale-set  │  │                               │
│  │  │  -controller)          │  │                               │
│  │  └───────────┬────────────┘  │                               │
│  │              │               │                               │
│  └──────────────┼───────────────┘                               │
│                 │ gestisce                                       │
│  ┌──────────────┼───────────────┐  ┌──────────────────────────┐ │
│  │ Namespace: arc-runners       │  │ GitHub Actions Service   │ │
│  │              │               │  │                          │ │
│  │  ┌───────────▼────────────┐  │  │  ┌────────────────────┐ │ │
│  │  │ Listener Pod           │◄─┼──┼──│ Job Queue          │ │ │
│  │  │ (HTTPS long poll)      │  │  │  └────────────────────┘ │ │
│  │  └───────────┬────────────┘  │  │                          │ │
│  │              │ scala         │  └──────────────────────────┘ │
│  │  ┌───────────▼────────────┐  │                               │
│  │  │ EphemeralRunnerSet     │  │                               │
│  │  │                        │  │                               │
│  │  │  ┌──────┐ ┌──────┐    │  │                               │
│  │  │  │Pod R1│ │Pod R2│... │  │                               │
│  │  │  └──────┘ └──────┘    │  │                               │
│  │  └────────────────────────┘  │                               │
│  │                              │                               │
│  └──────────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

### Flusso di Comunicazione Dettagliato

1. Il **Listener Pod** stabilisce una connessione HTTPS long-poll con il GitHub Actions Service.
2. Quando un job viene accodato e corrisponde al scale set, il Listener riceve un messaggio `Job Available`.
3. Il Listener verifica di poter scalare (non superare `maxRunners`) e usa le Kubernetes API per aggiornare il conteggio `desiredReplicas` sull'`EphemeralRunnerSet`.
4. L'`EphemeralRunner Controller` crea i pod runner e richiede un **JIT (Just-in-Time) configuration token** per ciascuno.
5. Il pod runner si registra usando il JIT token, esegue il job, e si termina automaticamente.
6. Il controller pulisce le risorse Kubernetes residue.

### Installazione del Controller (Chart 1)

```bash
# Installare il controller ARC (una volta per cluster)
NAMESPACE_CONTROLLER="arc-systems"

helm install arc \
  --namespace "${NAMESPACE_CONTROLLER}" \
  --create-namespace \
  --set image.tag="0.14.0" \
  --set metrics.controllerManagerAddr=":8080" \
  --set metrics.listenerAddr=":8080" \
  --set metrics.listenerEndpoint="/metrics" \
  --set flags.logLevel="info" \
  --set flags.logFormat="json" \
  --set flags.updateStrategy="eventual" \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller
```

### Installazione del Runner Scale Set (Chart 2)

```bash
# Creare il secret per l'autenticazione GitHub App (raccomandato)
kubectl create namespace arc-runners

kubectl create secret generic github-app-secret \
  -n arc-runners \
  --from-literal=github_app_id="12345" \
  --from-literal=github_app_installation_id="67890" \
  --from-file=github_app_private_key=private-key.pem

# Installare un runner scale set
helm install arc-runner-set \
  --namespace arc-runners \
  --set githubConfigUrl="https://github.com/myorg" \
  --set githubConfigSecret="github-app-secret" \
  --set minRunners=1 \
  --set maxRunners=20 \
  --set runnerScaleSetName="arc-linux-runners" \
  --set containerMode.type="dind" \
  --set template.spec.containers[0].name="runner" \
  --set template.spec.containers[0].image="ghcr.io/actions/actions-runner:latest" \
  --set template.spec.containers[0].resources.requests.cpu="2" \
  --set template.spec.containers[0].resources.requests.memory="4Gi" \
  --set template.spec.containers[0].resources.limits.cpu="4" \
  --set template.spec.containers[0].resources.limits.memory="8Gi" \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
```

### Cronologia Rilasci ARC 2025-2026

Le versioni recenti di ARC hanno introdotto miglioramenti significativi in resilienza, portabilità e sicurezza:

**ARC 0.12.0 (giugno 2025):** Retry automatico dei pod falliti fino a cinque tentativi con accodamento delle installazioni di runner ephemeral, migliorando la resilienza durante gli eventi di scale-down dei nodi. Aggiunto il supporto per il recupero di secret da vault esterni (ad esempio HashiCorp Vault, AWS Secrets Manager) in aggiunta ai Kubernetes Secret tradizionali, permettendo il recupero dinamico e sicuro di credenziali sensibili come PAT e credenziali GitHub App senza esporle direttamente nei manifest.

**ARC 0.13.0 (ottobre 2025):** Introdotti i container lifecycle hook che permettono di salvare e ripristinare il file system del job tra i pod, eliminando la necessità di volumi ReadWriteMany (RWX). Questo migliora la portabilità e le prestazioni sfruttando lo storage locale anziché volumi condivisi. Aggiunto il supporto per il networking dual-stack (IPv4/IPv6) per i runner e i servizi del controller, abilitando l'uso di IPv6 sui cluster compatibili con fallback trasparente su IPv4. Il supporto per Red Hat OpenShift è ora in disponibilità generale (GA), ampliando la compatibilità con le piattaforme enterprise.

**ARC 0.14.0 (marzo 2026):** Oltre al supporto multilabel già descritto, questa versione introduce il meccanismo di arresto dell'autoscaling basato sull'exit code 7. Quando un runner esce con codice 7 (configurazione obsoleta), il controller disattiva completamente l'autoscaling per quel runner set, impedendo il provisioning di runner con configurazione stale mentre il rollout della nuova configurazione è in corso. Aggiunte anche le annotazioni e label Kubernetes personalizzate per le risorse gestite internamente da ARC (role, role binding, service account, listener pod).

### Values.yaml Completo per Produzione

```yaml
# values-production.yaml per gha-runner-scale-set
githubConfigUrl: "https://github.com/myorg"
githubConfigSecret: "github-app-secret"

runnerScaleSetName: "production-linux"

minRunners: 2
maxRunners: 30

# Gruppo runner (livello organizzazione)
runnerGroup: "production"

# Container mode: dind, kubernetes, kubernetes-novolume
containerMode:
  type: "dind"

template:
  spec:
    # Tollerazioni per nodi dedicati ai runner
    tolerations:
      - key: "runner"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
    # Affinità per nodi spot
    affinity:
      nodeAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
          nodeSelectorTerms:
            - matchExpressions:
                - key: "node-role"
                  operator: "In"
                  values: ["ci-runner"]
    # Init container per setup
    initContainers:
      - name: setup-tools
        image: ghcr.io/myorg/runner-setup:latest
        command: ["sh", "-c", "cp -r /tools/* /opt/tools/"]
        volumeMounts:
          - name: tools
            mountPath: /opt/tools
    containers:
      - name: runner
        image: ghcr.io/actions/actions-runner:latest
        env:
          - name: ACTIONS_RUNNER_REQUIRE_JOB_CONTAINER
            value: "false"
          - name: RUNNER_GRACEFUL_STOP_TIMEOUT
            value: "15"
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
            ephemeral-storage: "20Gi"
          limits:
            cpu: "4"
            memory: "8Gi"
            ephemeral-storage: "50Gi"
        volumeMounts:
          - name: work
            mountPath: /home/runner/_work
          - name: tools
            mountPath: /opt/tools
    volumes:
      - name: work
        emptyDir:
          sizeLimit: 50Gi
      - name: tools
        emptyDir: {}
    # Security context del pod
    securityContext:
      fsGroup: 1001
      runAsUser: 1001
      runAsNonRoot: true

# Risorse per il Listener Pod
listenerTemplate:
  spec:
    containers:
      - name: listener
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"

# Annotazioni e label personalizzate (ARC 0.14+)
resource:
  all:
    metadata:
      labels:
        app.kubernetes.io/part-of: "ci-infrastructure"
        team: "platform-engineering"
      annotations:
        prometheus.io/scrape: "true"
```

### Utilizzo nei Workflow

```yaml
# Workflow che usa il runner scale set
name: Build con ARC
on: push

jobs:
  build:
    # Il nome deve corrispondere a runnerScaleSetName
    runs-on: production-linux
    steps:
      - uses: actions/checkout@v4
      - run: echo "Eseguito su ARC runner scale set"
```

---

## Container Mode in ARC

ARC supporta tre modalità operative per i container runner, ciascuna con compromessi diversi in termini di sicurezza, flessibilità e complessità.

### Modalità 1: Docker-in-Docker (DinD)

La modalità DinD esegue un daemon Docker completo all'interno del pod runner. Il pod contiene due container: il runner stesso e un sidecar `dind` (Docker-in-Docker).

```yaml
# values-dind.yaml
containerMode:
  type: "dind"

template:
  spec:
    containers:
      - name: runner
        image: ghcr.io/actions/actions-runner:latest
        command: ["/home/runner/run.sh"]
        env:
          - name: DOCKER_HOST
            value: "unix:///var/run/docker.sock"
        volumeMounts:
          - name: docker-sock
            mountPath: /var/run/docker.sock
      - name: dind
        image: docker:dind
        securityContext:
          privileged: true
        volumeMounts:
          - name: docker-sock
            mountPath: /var/run/docker.sock
          - name: dind-storage
            mountPath: /var/lib/docker
    volumes:
      - name: docker-sock
        emptyDir: {}
      - name: dind-storage
        emptyDir:
          sizeLimit: 100Gi
```

**Vantaggi**: Supporto completo a `docker build`, `docker compose`, esecuzione di container service nei workflow. Compatibilità massima con workflow esistenti.

**Svantaggi**: Richiede `privileged: true` per il sidecar DinD, il che è un rischio di sicurezza significativo. Il daemon Docker consuma risorse aggiuntive.

### Modalità 2: Kubernetes Mode

La modalità Kubernetes usa le API Kubernetes direttamente per creare i container richiesti dal job, senza bisogno di un daemon Docker. Il runner coordina la creazione di container per job, service e step tramite le API K8s.

```yaml
# values-kubernetes-mode.yaml
containerMode:
  type: "kubernetes"
  kubernetesModeWorkVolumeClaim:
    accessModes: ["ReadWriteOnce"]
    storageClassName: "gp3-csi"
    resources:
      requests:
        storage: "50Gi"

template:
  spec:
    containers:
      - name: runner
        image: ghcr.io/actions/actions-runner:latest
        env:
          - name: ACTIONS_RUNNER_CONTAINER_HOOKS
            value: /home/runner/k8s/index.js
          - name: ACTIONS_RUNNER_POD_NAME
            valueFrom:
              fieldRef:
                fieldPath: metadata.name
          - name: ACTIONS_RUNNER_REQUIRE_JOB_CONTAINER
            value: "true"
        resources:
          requests:
            cpu: "1"
            memory: "2Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
        volumeMounts:
          - name: work
            mountPath: /home/runner/_work
    volumes:
      - name: work
        ephemeral:
          volumeClaimTemplate:
            spec:
              accessModes: ["ReadWriteOnce"]
              storageClassName: "gp3-csi"
              resources:
                requests:
                  storage: 50Gi
```

**Vantaggi**: Non richiede `privileged: true`. Migliore isolamento di sicurezza. I container dei job vengono creati nativamente come pod Kubernetes.

**Svantaggi**: Non supporta `docker build` nativamente. Richiede storage dinamico (PVC). I workflow devono usare container job (`container:` nel YAML del workflow).

### Modalità 3: Kubernetes-Novolume

Variante della modalità Kubernetes che usa lifecycle hook del container anziché volumi persistenti per la comunicazione tra runner e container job.

```yaml
# values-kubernetes-novolume.yaml
containerMode:
  type: "kubernetes-novolume"

template:
  spec:
    containers:
      - name: runner
        image: ghcr.io/actions/actions-runner:latest
        securityContext:
          runAsUser: 0  # Richiesto per lifecycle hooks
        env:
          - name: ACTIONS_RUNNER_CONTAINER_HOOKS
            value: /home/runner/k8s/index.js
          - name: ACTIONS_RUNNER_POD_NAME
            valueFrom:
              fieldRef:
                fieldPath: metadata.name
```

**Vantaggi**: Non richiede provisioner di volumi persistenti. Configurazione più semplice per ambienti con storage limitato.

**Svantaggi**: Richiede esecuzione come root per i lifecycle hook. Meno isolamento rispetto alla modalità Kubernetes standard.

### Tabella Comparativa delle Modalità

| Caratteristica | DinD | Kubernetes | Kubernetes-Novolume |
|---|---|---|---|
| `docker build` | Si | No | No |
| `docker compose` | Si | No | No |
| Privileged | Si (sidecar) | No | No |
| Root richiesto | No | No | Si |
| PVC richiesto | No | Si | No |
| Container job | Si | Si | Si |
| Service container | Si | Si (K8s native) | Si (K8s native) |
| Sicurezza | Bassa | Alta | Media |
| Complessità | Media | Alta | Media |

---

## JIT Runner Registration e Token Lifecycle

La registrazione Just-in-Time (JIT) è il meccanismo moderno per registrare runner ephemeral senza token di lunga durata. Elimina la necessità di passare PAT (Personal Access Token) ai pod runner, riducendo drasticamente la superficie di attacco.

### Come Funziona il JIT

```
┌───────────────┐    1. Richiede JIT config    ┌──────────────────┐
│ ARC Controller │──────────────────────────────►│ GitHub Actions   │
│                │    token per nuovo runner     │ Service          │
│                │◄──────────────────────────────│                  │
│                │    2. Risponde con            │                  │
│                │    encoded JIT config         │                  │
└───────┬───────┘                               └──────────────────┘
        │
        │ 3. Passa JIT config
        │    al pod runner
        ▼
┌───────────────┐    4. Si registra con         ┌──────────────────┐
│ Runner Pod     │    il JIT config token       │ GitHub Actions   │
│                │──────────────────────────────►│ Service          │
│                │                               │                  │
│                │    5. Riceve il job           │                  │
│                │◄──────────────────────────────│                  │
│                │                               │                  │
│                │    6. Esegue, termina         │                  │
└───────────────┘                               └──────────────────┘
```

### Caratteristiche del JIT Token

- **Durata**: Il JIT configuration token scade dopo 1 ora se non utilizzato.
- **Uso singolo**: Ogni token può registrare un solo runner.
- **Nessun segreto persistente**: Il runner non ha bisogno di un PAT o di credenziali GitHub App. Il controller gestisce tutto.
- **Retry**: Se il pod fallisce, il controller EphemeralRunner riprova fino a 5 volte. Dopo 24 ore, il GitHub Actions Service disassegna il job.

### Registrazione JIT via REST API (senza ARC)

Per chi non usa ARC ma vuole comunque sfruttare la registrazione JIT:

```bash
# Creare un runner JIT per un repository
RESPONSE=$(curl -s -X POST \
  -H "Authorization: token ${GITHUB_PAT}" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/${OWNER}/${REPO}/actions/runners/generate-jitconfig" \
  -d '{
    "name": "jit-runner-'"$(date +%s)"'",
    "runner_group_id": 1,
    "labels": ["self-hosted", "linux", "x64"],
    "work_folder": "_work"
  }')

# Estrarre il runner ID e l'encoded JIT config
RUNNER_ID=$(echo "$RESPONSE" | jq -r '.runner.id')
ENCODED_JIT_CONFIG=$(echo "$RESPONSE" | jq -r '.encoded_jit_config')

echo "Runner ID: $RUNNER_ID"
echo "JIT Config: $ENCODED_JIT_CONFIG"

# Avviare il runner con il JIT config
./run.sh --jitconfig "$ENCODED_JIT_CONFIG"
```

```bash
# Stessa cosa per un'organizzazione
RESPONSE=$(curl -s -X POST \
  -H "Authorization: token ${GITHUB_PAT}" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/orgs/${ORG}/actions/runners/generate-jitconfig" \
  -d '{
    "name": "jit-runner-org-'"$(date +%s)"'",
    "runner_group_id": 2,
    "labels": ["self-hosted", "linux", "x64", "production"],
    "work_folder": "_work"
  }')

ENCODED_JIT_CONFIG=$(echo "$RESPONSE" | jq -r '.encoded_jit_config')
./run.sh --jitconfig "$ENCODED_JIT_CONFIG"
```

### Confronto: Token di Registrazione vs JIT

| Aspetto | Registration Token | JIT Config |
|---|---|---|
| Durata | 1 ora | 1 ora |
| Richiede PAT nel runner | Si (per ottenere il token) | No |
| Multi-uso | Si (più runner dallo stesso token) | No (un runner per token) |
| Sicurezza | Media | Alta |
| Complessità setup | Bassa | Media |
| Raccomandato per ARC | No | Si (default) |
| Raccomandato per VM | Si | Si (preferito) |

---

## Multilabel Support e Routing Avanzato

A partire da ARC 0.14.0 (marzo 2026), un singolo runner scale set può avere **più label**, eliminando la necessità di creare scale set separati per ogni combinazione di attributi.

### Prima di ARC 0.14.0

```yaml
# PRIMA: servivano scale set separati per ogni combinazione
# Scale set 1: linux + x64
# Scale set 2: linux + x64 + gpu
# Scale set 3: linux + arm64
# Scale set 4: linux + x64 + high-memory
# = 4 installazioni Helm separate
```

### Dopo ARC 0.14.0

```yaml
# DOPO: un solo scale set con più label
# values-multilabel.yaml
githubConfigUrl: "https://github.com/myorg"
githubConfigSecret: "github-app-secret"

runnerScaleSetName: "gpu-runners"

# Più label per un singolo scale set
labels:
  - "self-hosted"
  - "linux"
  - "x64"
  - "gpu"
  - "cuda-12"
  - "high-memory"

minRunners: 0
maxRunners: 10
```

```yaml
# Workflow che targetizza runner con combinazione di label
jobs:
  train-model:
    runs-on: [self-hosted, linux, gpu, cuda-12]
    steps:
      - run: nvidia-smi && echo "GPU disponibile"

  build-standard:
    runs-on: [self-hosted, linux, x64]
    steps:
      - run: echo "Build standard"
```

### Routing Avanzato con Runner Groups

Il routing avanzato combina runner groups (livello organizzazione/enterprise) con label (livello scale set) per un controllo granulare:

```bash
# Creare un runner group con restrizioni di workflow
gh api orgs/myorg/actions/runner-groups \
  --method POST \
  -f name="production-deploy" \
  -f visibility="selected" \
  -F allows_public_repositories=false \
  -F restricted_to_workflows=true \
  -f selected_workflows[]="myorg/myapp/.github/workflows/deploy.yml@refs/heads/main" \
  -f selected_workflows[]="myorg/myapp/.github/workflows/release.yml@refs/tags/*"

# Assegnare il runner scale set al group
# Nel values.yaml:
# runnerGroup: "production-deploy"
```

### Strategia di Routing per Ambienti

```
┌─────────────────────────────────────────────────────────────┐
│                  Organizzazione GitHub                       │
│                                                             │
│  Runner Group: "development"                                │
│  ├── Scale Set: dev-linux     [linux, x64, dev]             │
│  ├── Scale Set: dev-arm       [linux, arm64, dev]           │
│  └── Repo access: tutti i repo                              │
│                                                             │
│  Runner Group: "staging"                                    │
│  ├── Scale Set: stg-linux     [linux, x64, staging]         │
│  └── Repo access: app-*, infra-*                            │
│                                                             │
│  Runner Group: "production"                                 │
│  ├── Scale Set: prod-linux    [linux, x64, production]      │
│  ├── Scale Set: prod-gpu      [linux, gpu, production]      │
│  └── Repo access: solo deploy repo, solo workflow deploy    │
│      su refs/heads/main                                     │
│                                                             │
│  Runner Group: "shared"                                     │
│  ├── Scale Set: shared-build  [linux, x64, build]           │
│  └── Repo access: tutti i repo privati                      │
└─────────────────────────────────────────────────────────────┘
```

---

## GPU Runners: Configurazione NVIDIA e CUDA

L'esecuzione di workload GPU (training ML, inferenza, rendering, test CUDA) richiede configurazione specifica sia a livello di nodo Kubernetes che di runner.

### Prerequisiti del Nodo

```bash
# 1. Installare i driver NVIDIA sul nodo
sudo apt-get update
sudo apt-get install -y nvidia-driver-550

# 2. Installare NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 3. Configurare il runtime containerd per GPU
sudo nvidia-ctk runtime configure --runtime=containerd
sudo systemctl restart containerd

# 4. Installare il NVIDIA Device Plugin per Kubernetes
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.16.0/deployments/static/nvidia-device-plugin.yml

# 5. Verificare che le GPU siano visibili
kubectl get nodes -o json | jq '.items[].status.capacity["nvidia.com/gpu"]'
```

### Dockerfile per Runner GPU

```dockerfile
# Dockerfile.gpu-runner
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

# Evitare prompt interattivi
ENV DEBIAN_FRONTEND=noninteractive

# Installare dipendenze base
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    git \
    sudo \
    libicu-dev \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Installare tool ML comuni
RUN pip3 install --no-cache-dir \
    torch \
    torchvision \
    transformers \
    numpy \
    scikit-learn

# Creare utente runner
RUN useradd -m -s /bin/bash runner && \
    echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Scaricare e installare GitHub Actions Runner
ARG RUNNER_VERSION=2.321.0
RUN mkdir -p /home/runner/actions-runner && \
    cd /home/runner/actions-runner && \
    curl -sL "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" \
    | tar xz && \
    chown -R runner:runner /home/runner/actions-runner && \
    /home/runner/actions-runner/bin/installdependencies.sh

# Verificare GPU al boot
COPY gpu-entrypoint.sh /gpu-entrypoint.sh
RUN chmod +x /gpu-entrypoint.sh

USER runner
WORKDIR /home/runner/actions-runner

ENTRYPOINT ["/gpu-entrypoint.sh"]
```

```bash
#!/bin/bash
# gpu-entrypoint.sh

set -euo pipefail

# Verificare che la GPU sia accessibile
echo "=== Verifica GPU ==="
if command -v nvidia-smi &>/dev/null; then
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    echo "GPU verificata con successo"
else
    echo "ATTENZIONE: nvidia-smi non disponibile. I job GPU potrebbero fallire."
fi

# Configurare e avviare il runner
if [ -n "${ENCODED_JIT_CONFIG:-}" ]; then
    # Modalità JIT
    ./run.sh --jitconfig "${ENCODED_JIT_CONFIG}"
elif [ -n "${RUNNER_TOKEN:-}" ]; then
    # Modalità token di registrazione
    ./config.sh \
        --url "${GITHUB_URL}" \
        --token "${RUNNER_TOKEN}" \
        --name "${RUNNER_NAME:-gpu-runner-$(hostname)}" \
        --labels "${RUNNER_LABELS:-self-hosted,linux,x64,gpu,cuda-12}" \
        --ephemeral \
        --unattended \
        --replace
    ./run.sh
else
    echo "ERRORE: Né ENCODED_JIT_CONFIG né RUNNER_TOKEN sono impostati"
    exit 1
fi
```

### Scale Set ARC per GPU

```yaml
# values-gpu-runners.yaml
githubConfigUrl: "https://github.com/myorg"
githubConfigSecret: "github-app-secret"

runnerScaleSetName: "gpu-cuda12"

labels:
  - "self-hosted"
  - "linux"
  - "x64"
  - "gpu"
  - "cuda-12"

minRunners: 0
maxRunners: 4

containerMode:
  type: "dind"

template:
  spec:
    tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
    nodeSelector:
      accelerator: "nvidia-a100"
    runtimeClassName: "nvidia"
    containers:
      - name: runner
        image: ghcr.io/myorg/gpu-runner:cuda-12.4
        env:
          - name: NVIDIA_VISIBLE_DEVICES
            value: "all"
          - name: NVIDIA_DRIVER_CAPABILITIES
            value: "compute,utility"
        resources:
          requests:
            cpu: "4"
            memory: "16Gi"
            nvidia.com/gpu: "1"
          limits:
            cpu: "8"
            memory: "32Gi"
            nvidia.com/gpu: "1"
```

### Workflow GPU

```yaml
name: ML Training Pipeline
on:
  push:
    paths: ["models/**", "training/**"]

jobs:
  train:
    runs-on: [self-hosted, linux, gpu, cuda-12]
    timeout-minutes: 120
    steps:
      - uses: actions/checkout@v4

      - name: Verificare GPU
        run: |
          nvidia-smi
          python3 -c "import torch; print(f'CUDA disponibile: {torch.cuda.is_available()}')"
          python3 -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"

      - name: Training modello
        run: |
          python3 training/train.py \
            --epochs 50 \
            --batch-size 64 \
            --learning-rate 0.001 \
            --output models/output/

      - name: Upload modello
        uses: actions/upload-artifact@v4
        with:
          name: trained-model
          path: models/output/
```

---

## ARM64 Runners e Build Multi-Architettura

I runner ARM64 sono essenziali per build native su architettura ARM, comuni per deploy su AWS Graviton, Apple Silicon, Raspberry Pi, e dispositivi IoT.

### Self-Hosted ARM64 Runner su Bare Metal

```bash
# Su una macchina ARM64 (es. Apple Silicon Mac, AWS Graviton, Ampere Altra)
ARCH="arm64"

mkdir -p ~/actions-runner && cd ~/actions-runner

RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest \
  | jq -r '.tag_name' | sed 's/^v//')

curl -sL \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-arm64-${RUNNER_VERSION}.tar.gz" \
  | tar xz

./config.sh \
  --url "https://github.com/myorg" \
  --token "${RUNNER_TOKEN}" \
  --name "arm64-runner-01" \
  --labels "self-hosted,linux,arm64,graviton" \
  --ephemeral \
  --unattended

./run.sh
```

### Dockerfile Multi-Architettura per Runner

```dockerfile
# Dockerfile.multiarch-runner
# Supporta sia x64 che arm64
FROM --platform=$TARGETPLATFORM ubuntu:22.04

ARG TARGETARCH
ARG RUNNER_VERSION=2.321.0

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl jq git sudo libicu-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash runner && \
    echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Scaricare la versione corretta per l'architettura
RUN RUNNER_ARCH="" && \
    case "${TARGETARCH}" in \
      amd64) RUNNER_ARCH="x64" ;; \
      arm64) RUNNER_ARCH="arm64" ;; \
      *) echo "Architettura non supportata: ${TARGETARCH}" && exit 1 ;; \
    esac && \
    mkdir -p /home/runner/actions-runner && \
    cd /home/runner/actions-runner && \
    curl -sL \
      "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz" \
    | tar xz && \
    chown -R runner:runner /home/runner/actions-runner && \
    /home/runner/actions-runner/bin/installdependencies.sh

USER runner
WORKDIR /home/runner/actions-runner

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

```bash
# Build multi-architettura con buildx
docker buildx create --name multiarch --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ghcr.io/myorg/actions-runner:latest \
  --tag ghcr.io/myorg/actions-runner:2.321.0 \
  --push \
  -f Dockerfile.multiarch-runner .
```

### Workflow Multi-Architettura con Matrix

```yaml
name: Multi-Arch Build
on: push

jobs:
  build:
    strategy:
      matrix:
        include:
          - arch: x64
            runner: [self-hosted, linux, x64]
            platform: linux/amd64
          - arch: arm64
            runner: [self-hosted, linux, arm64]
            platform: linux/arm64
    runs-on: ${{ matrix.runner }}
    steps:
      - uses: actions/checkout@v4

      - name: Build nativa ${{ matrix.arch }}
        run: |
          echo "Build nativa su $(uname -m)"
          docker build \
            --tag myapp:${{ github.sha }}-${{ matrix.arch }} \
            .

      - name: Push immagine
        run: |
          docker push myapp:${{ github.sha }}-${{ matrix.arch }}

  manifest:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Creare manifest multi-arch
        run: |
          docker manifest create myapp:${{ github.sha }} \
            myapp:${{ github.sha }}-x64 \
            myapp:${{ github.sha }}-arm64
          docker manifest push myapp:${{ github.sha }}
```

---

## Larger Runners GitHub-Hosted

GitHub offre runner gestiti con specifiche hardware superiori ai runner standard, disponibili per piani Team e Enterprise Cloud. Questi runner eliminano la necessità di gestire infrastruttura self-hosted per workload che richiedono semplicemente più risorse.

### Configurazioni Disponibili (2026)

| Sistema Operativo | vCPU | RAM | Storage | GPU | Architettura |
|---|---|---|---|---|---|
| Ubuntu Linux | 2-64 | 8-256 GB | 75-2040 GB SSD | No | x64, arm64 |
| Ubuntu Linux GPU | 4 | 16-56 GB | 176 GB SSD | T4/A10G | x64 |
| Windows | 2-64 | 8-256 GB | 75-2040 GB SSD | No | x64, arm64 |
| macOS (M-series) | 3-12 core | 7-30 GB | 14 GB SSD | GPU Metal | arm64 |
| macOS (Intel) | 12 core | 30 GB | 14 GB SSD | No | x64 |

### Costi Larger Runners

```
Linux larger runners:
  4 vCPU:  $0.016/min
  8 vCPU:  $0.032/min
  16 vCPU: $0.064/min
  32 vCPU: $0.128/min
  64 vCPU: $0.256/min

Linux GPU runners:
  T4 GPU:   $0.07/min
  A10G GPU: variabile

macOS (M-series):
  3 core (M1): $0.12/min
  6 core (M2 Pro): $0.24/min
  12 core (M2 Max): $0.48/min

Windows larger runners:
  Circa 2x il costo Linux equivalente
```

### Quando Larger Runner vs Self-Hosted

| Scenario | Larger Runner | Self-Hosted |
|---|---|---|
| Burst temporaneo di risorse | Migliore | Overprovisioning |
| Costo prevedibile fisso | Costo variabile | Migliore |
| Zero manutenzione | Migliore | Overhead operativo |
| Accesso rete privata | Non disponibile | Necessario |
| Hardware custom (FPGA, ecc.) | Non disponibile | Unica opzione |
| Latenza di avvio | ~20-40s | Dipende dalla configurazione |
| Requisiti compliance | Limitato | Pieno controllo |

---

## Autoscaling Avanzato: Webhook vs Percentage-Based

L'autoscaling dei runner può essere implementato con diverse strategie, ciascuna con compromessi in termini di reattività, costo e complessità.

### Strategia 1: Webhook-Based (Raccomandato)

L'autoscaling basato su webhook è il metodo più reattivo. Un server webhook riceve eventi `workflow_job` da GitHub e scala i runner immediatamente.

```yaml
# HorizontalRunnerAutoscaler con webhook (ARC legacy)
apiVersion: actions.summerwind.dev/v1alpha1
kind: HorizontalRunnerAutoscaler
metadata:
  name: webhook-autoscaler
spec:
  scaleTargetRef:
    kind: RunnerDeployment
    name: main-runners
  minReplicas: 0
  maxReplicas: 30
  scaleDownDelaySecondsAfterScaleOut: 300
  scaleUpTriggers:
    - amount: 1
      duration: "5m"
      githubEvent:
        workflowJob: {}
```

Per l'ARC moderno (scale set), l'autoscaling basato su webhook è integrato direttamente nella comunicazione Listener-GitHub:

```yaml
# ARC moderno: l'autoscaling è nativo
# Il Listener Pod riceve Job Available via HTTPS long-poll
# Non serve configurare webhook separato
githubConfigUrl: "https://github.com/myorg"
githubConfigSecret: "github-app-secret"

minRunners: 0     # Scale-to-zero quando non ci sono job
maxRunners: 30    # Limite superiore

# Il Listener scala automaticamente in base ai job in coda
```

**Latenza di scaling**: tipicamente 10-30 secondi dal momento in cui il job è accodato alla creazione del pod runner.

### Strategia 2: Percentage-Based

Lo scaling basato sulla percentuale di runner occupati è utile quando si vuole mantenere un buffer di runner pronti:

```yaml
# HorizontalRunnerAutoscaler con percentuale (ARC legacy)
apiVersion: actions.summerwind.dev/v1alpha1
kind: HorizontalRunnerAutoscaler
metadata:
  name: percentage-autoscaler
spec:
  scaleTargetRef:
    kind: RunnerDeployment
    name: main-runners
  minReplicas: 2
  maxReplicas: 30
  metrics:
    - type: PercentageRunnersBusy
      scaleUpThreshold: "0.75"     # Scala su quando 75% è occupato
      scaleDownThreshold: "0.25"   # Scala giù quando solo 25% è occupato
      scaleUpFactor: "2.0"         # Raddoppia i runner
      scaleDownFactor: "0.5"       # Dimezza i runner
      scaleUpAdjustment: 2         # Aggiungi almeno 2
      scaleDownAdjustment: 1       # Rimuovi almeno 1
```

**Esempio di comportamento**:
- 10 runner attivi, 8 occupati (80% > soglia 75%) → scala a 20 runner (fattore 2.0)
- 20 runner attivi, 3 occupati (15% < soglia 25%) → scala a 10 runner (fattore 0.5)

### Strategia 3: Scheduled Scaling

Per carichi prevedibili (ore di lavoro), si può combinare l'autoscaling con scaling schedulato:

```yaml
# CronJob per scale-up durante le ore di lavoro
apiVersion: batch/v1
kind: CronJob
metadata:
  name: warmup-runners
  namespace: arc-runners
spec:
  schedule: "0 8 * * 1-5"  # Lunedì-Venerdì alle 8:00
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: scale-up
              image: bitnami/kubectl:latest
              command:
                - /bin/sh
                - -c
                - |
                  kubectl patch autoscalingrunnerset arc-runner-set \
                    -n arc-runners \
                    --type=merge \
                    -p '{"spec":{"minRunners":5}}'
          restartPolicy: OnFailure

---
# CronJob per scale-down fuori orario
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scaledown-runners
  namespace: arc-runners
spec:
  schedule: "0 20 * * 1-5"  # Lunedì-Venerdì alle 20:00
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: scale-down
              image: bitnami/kubectl:latest
              command:
                - /bin/sh
                - -c
                - |
                  kubectl patch autoscalingrunnerset arc-runner-set \
                    -n arc-runners \
                    --type=merge \
                    -p '{"spec":{"minRunners":0}}'
          restartPolicy: OnFailure
```

### Confronto Strategie di Autoscaling

| Strategia | Reattività | Costo | Complessità | Uso Ideale |
|---|---|---|---|---|
| Webhook/Long-poll | Alta (10-30s) | Basso | Bassa | Default per ARC |
| Percentage-based | Media (1-5min) | Medio | Media | Buffer di warm runner |
| Scheduled | Nessuna (fisso) | Variabile | Bassa | Carichi prevedibili |
| Combinato | Alta | Ottimizzato | Alta | Produzione enterprise |

---

## Scale-to-Zero e Ottimizzazione dei Costi

La capacità di scalare a zero runner quando non ci sono job in coda è fondamentale per ottimizzare i costi, specialmente con runner su cloud.

### Configurazione Scale-to-Zero con ARC

```yaml
# values-scale-to-zero.yaml
githubConfigUrl: "https://github.com/myorg"
githubConfigSecret: "github-app-secret"

runnerScaleSetName: "cost-optimized"

minRunners: 0    # Zero runner in idle
maxRunners: 20

# Il Listener Pod rimane attivo anche con 0 runner
# Consuma circa 100-200 MB di RAM
listenerTemplate:
  spec:
    containers:
      - name: listener
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"
```

### Impatto sulla Latenza

Con scale-to-zero, il primo job dopo un periodo di inattività subisce una latenza aggiuntiva:

```
Latenza totale primo job:
  Listener riceve Job Available:     ~1-3 secondi
  Controller crea EphemeralRunner:   ~1-2 secondi
  Kubernetes schedula il pod:        ~2-5 secondi
  Pull immagine container:           ~5-30 secondi (cache-dipendente)
  Runner si registra via JIT:        ~2-5 secondi
  ────────────────────────────────────────────────
  Totale cold-start:                 ~10-45 secondi

Con minRunners >= 1 (warm pool):
  Runner già pronto:                 ~1-3 secondi
```

### Strategie per Ridurre il Cold-Start

```yaml
# 1. Pre-pull immagini sui nodi con DaemonSet
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: runner-image-prepull
  namespace: arc-runners
spec:
  selector:
    matchLabels:
      app: runner-prepull
  template:
    metadata:
      labels:
        app: runner-prepull
    spec:
      initContainers:
        - name: prepull-runner
          image: ghcr.io/actions/actions-runner:latest
          command: ["sh", "-c", "echo 'Immagine scaricata'"]
        - name: prepull-dind
          image: docker:dind
          command: ["sh", "-c", "echo 'Immagine DinD scaricata'"]
      containers:
        - name: pause
          image: registry.k8s.io/pause:3.9
          resources:
            requests:
              cpu: "1m"
              memory: "1Mi"
      tolerations:
        - key: "runner"
          operator: "Exists"
```

```yaml
# 2. Usare Karpenter con provisioner dedicato per startup rapido
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: ci-runners
spec:
  template:
    metadata:
      labels:
        node-role: ci-runner
    spec:
      requirements:
        - key: "kubernetes.io/arch"
          operator: In
          values: ["amd64"]
        - key: "karpenter.sh/capacity-type"
          operator: In
          values: ["spot", "on-demand"]
        - key: "node.kubernetes.io/instance-type"
          operator: In
          values: ["m6a.xlarge", "m6i.xlarge", "c6a.xlarge", "c6i.xlarge"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: ci-runner-class
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 60s
  limits:
    cpu: "200"
    memory: "400Gi"
```

---

## Spot Instances e Preemptible VMs per Runner

L'uso di istanze spot (AWS), preemptible (GCP), o spot VM (Azure) per i runner CI/CD può ridurre i costi del 70-90% rispetto alle istanze on-demand, sfruttando il fatto che i job CI sono intrinsecamente transitori e ripetibili.

### AWS: Runner su Spot Instances con Karpenter

```yaml
# EC2NodeClass per runner spot
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: ci-runner-class
spec:
  amiSelectorTerms:
    - alias: "al2023@latest"
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: "my-cluster"
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: "my-cluster"
  # Optimizzazione: storage locale NVMe per build veloci
  instanceStorePolicy: RAID0
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs:
        volumeSize: 100Gi
        volumeType: gp3
        iops: 5000
        throughput: 250
        deleteOnTermination: true
  userData: |
    #!/bin/bash
    # Pre-configurare il nodo per i runner
    systemctl enable --now containerd
```

### Gestione dell'Interruzione Spot

```yaml
# Workflow resiliente a interruzioni spot
name: Build Resiliente
on: push

jobs:
  build:
    runs-on: [self-hosted, linux, x64]
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4

      - name: Restore cache build
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            build/
          key: build-${{ runner.os }}-${{ hashFiles('**/*.gradle*') }}
          restore-keys: |
            build-${{ runner.os }}-

      - name: Build con checkpoint
        run: |
          # Build incrementale - se l'istanza spot viene interrotta,
          # il job viene riaccodato e riparte dalla cache
          ./gradlew build --build-cache

      - name: Salvataggio cache
        uses: actions/cache/save@v4
        if: always()
        with:
          path: |
            ~/.gradle/caches
            build/
          key: build-${{ runner.os }}-${{ hashFiles('**/*.gradle*') }}
```

### GCP: Preemptible VMs

```bash
# Creare un managed instance group con VM preemptibili per i runner
gcloud compute instance-templates create runner-template \
  --machine-type=n2-standard-8 \
  --preemptible \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-ssd \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --metadata-from-file=startup-script=runner-startup.sh \
  --service-account=runner-sa@myproject.iam.gserviceaccount.com \
  --scopes=cloud-platform \
  --tags=ci-runner

gcloud compute instance-groups managed create runner-mig \
  --template=runner-template \
  --size=0 \
  --zone=us-central1-a \
  --target-size=0
```

### Stima Costi con Spot

```
=== Confronto Costi Mensili (8 runner, 730 ore/mese) ===

AWS EC2 (c6i.xlarge - 4 vCPU, 8 GB RAM):
  On-Demand:  8 × $0.17/ora × 730h = $993/mese
  Spot:       8 × $0.051/ora × 730h = $298/mese  (-70%)

GCP (n2-standard-4 - 4 vCPU, 16 GB RAM):
  On-Demand:  8 × $0.19/ora × 730h = $1,110/mese
  Preemptible: 8 × $0.04/ora × 730h = $234/mese  (-79%)

Azure (D4s_v5 - 4 vCPU, 16 GB RAM):
  On-Demand:  8 × $0.192/ora × 730h = $1,121/mese
  Spot:       8 × $0.038/ora × 730h = $222/mese   (-80%)

Con scale-to-zero (media 10 ore/giorno di uso effettivo):
  AWS Spot:   8 × $0.051/ora × 300h = $122/mese   (-88% vs on-demand)
  GCP Preempt: 8 × $0.04/ora × 300h = $96/mese    (-91% vs on-demand)
```

---

## OIDC Authentication dai Runner ai Cloud Provider

L'uso di OpenID Connect (OIDC) elimina la necessità di archiviare credenziali cloud di lunga durata come secret dei workflow. Il runner ottiene un token OIDC dal provider GitHub OIDC e lo scambia con credenziali temporanee dal cloud provider.

### Come Funziona

```
┌──────────────┐   1. Richiede OIDC token   ┌──────────────────┐
│ Workflow Job  │───────────────────────────►│ GitHub OIDC       │
│ (sul runner)  │                            │ Provider          │
│               │◄───────────────────────────│                   │
│               │   2. JWT con claims:       │ Token claims:     │
│               │   - repo, branch, env      │ - sub             │
│               │   - runner_environment     │ - aud             │
│               │                            │ - ref             │
└───────┬──────┘                            └──────────────────┘
        │
        │ 3. Presenta JWT al cloud
        ▼
┌──────────────┐   4. Verifica JWT e         ┌──────────────────┐
│ Cloud         │   emette credenziali       │ Cloud Provider   │
│ (AWS STS /    │   temporanee (15min-1h)    │ Identity Service │
│  GCP WIF /    │◄───────────────────────────│                   │
│  Azure AD)    │                            │                   │
└──────────────┘                            └──────────────────┘
```

### Configurazione per AWS

```yaml
# Workflow con OIDC per AWS (funziona su self-hosted e GitHub-hosted)
name: Deploy AWS con OIDC
on:
  push:
    branches: [main]

permissions:
  id-token: write   # Necessario per richiedere il token OIDC
  contents: read

jobs:
  deploy:
    runs-on: [self-hosted, linux, production]
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Configurare credenziali AWS via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActions-Deploy
          aws-region: eu-west-1
          # Nessun access key o secret — tutto via OIDC

      - name: Deploy
        run: |
          aws sts get-caller-identity  # Verifica identità
          aws ecs update-service --cluster prod --service myapp --force-new-deployment
```

```json
// Trust policy IAM per il ruolo AWS
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:myorg/myapp:environment:production"
        }
      }
    }
  ]
}
```

### Claim OIDC Specifici per Self-Hosted Runner

Il token OIDC generato su un self-hosted runner include il claim `runner_environment` con valore `self-hosted`, che può essere usato nelle policy di trust per distinguere i runner:

```json
{
  "sub": "repo:myorg/myapp:environment:production",
  "aud": "sts.amazonaws.com",
  "ref": "refs/heads/main",
  "repository": "myorg/myapp",
  "runner_environment": "self-hosted",
  "enterprise": "my-enterprise"
}
```

---

## Supply Chain Security: Lezioni dagli Attacchi 2025-2026

Gli attacchi alla supply chain dei GitHub Actions hanno avuto un impatto significativo tra il 2025 e il 2026, dimostrando che la sicurezza dei self-hosted runner è strettamente legata alla sicurezza delle Actions utilizzate nei workflow.

### Caso Studio: tj-actions/changed-files (CVE-2025-30066, marzo 2025)

**Catena dell'attacco**:
1. L'attaccante ha compromesso il progetto `reviewdog/action-setup` inserendo un backdoor.
2. Il backdoor ha propagato attraverso la dipendenza `tj-actions/eslint-changed-files`.
3. Tramite un PAT compromesso del bot `@tj-actions-bot`, l'attaccante ha ottenuto accesso privilegiato al repository `tj-actions/changed-files`.
4. L'attaccante ha modificato i tag git esistenti, iniettando un payload che esportava le variabili d'ambiente (inclusi i secret) nei log del workflow.
5. Oltre 23.000 repository sono stati potenzialmente esposti, con 218 repository che hanno effettivamente avuto secret esposti nei log.

**Impatto su self-hosted runner**: Su un runner persistente (non ephemeral), l'attaccante avrebbe potuto non solo leggere i secret ma anche installare backdoor persistenti, compromettere future esecuzioni, e accedere alla rete interna.

### Caso Studio: Attacco Pull Request Target (2026)

Nel 2026, una campagna di sei settimane ha preso di mira repository che usavano il trigger `pull_request_target`, compromettendo secret da almeno 50 repository. L'attacco sfruttava il fatto che `pull_request_target` esegue codice dal branch base ma con l'evento della PR, permettendo l'esecuzione di codice malevolo con accesso ai secret del repository.

### Mitigazioni Obbligatorie per Self-Hosted Runner

```yaml
# 1. SEMPRE pinnare le Actions al SHA del commit, MAI al tag
# SBAGLIATO: vulnerabile a tag tampering
- uses: actions/checkout@v4

# CORRETTO: pinnato al commit SHA
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1

# 2. Usare Dependabot per aggiornare i SHA
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    # Dependabot aggiornerà automaticamente i SHA
    # e creerà PR per la revisione
```

```yaml
# 3. Limitare i permessi del GITHUB_TOKEN (principio del minimo privilegio)
permissions:
  contents: read      # Solo lettura del repository
  # NON impostare 'write' a meno che non sia strettamente necessario

# 4. Non usare pull_request_target con checkout del codice della PR
# PERICOLOSO:
on: pull_request_target
# ...
- uses: actions/checkout@SHA
  with:
    ref: ${{ github.event.pull_request.head.sha }}  # Esegue codice non fidato!

# SICURO: usare pull_request e richiedere approvazione manuale
on: pull_request
# ...
jobs:
  test:
    if: github.event.pull_request.author_association == 'MEMBER'
    runs-on: [self-hosted, linux]
```

```bash
# 5. Verificare l'integrità delle Actions prima dell'uso
# Script per controllare che i SHA siano validi
#!/bin/bash
# verify-actions.sh

grep -rn "uses:" .github/workflows/ | while IFS= read -r line; do
  ACTION=$(echo "$line" | grep -oP 'uses:\s*\K[^@]+@\S+')
  if echo "$ACTION" | grep -qP '@v\d'; then
    FILE=$(echo "$line" | cut -d: -f1)
    LINE_NUM=$(echo "$line" | cut -d: -f2)
    echo "ATTENZIONE: Action non pinnata al SHA in ${FILE}:${LINE_NUM}: ${ACTION}"
  fi
done
```

### Checklist Sicurezza Supply Chain per Runner

- [ ] Tutte le Actions pinnate al commit SHA, non al tag
- [ ] Dependabot configurato per `github-actions` ecosystem
- [ ] Runner ephemeral per ogni job (nessuna persistenza tra job)
- [ ] `pull_request_target` non usato, o usato solo con checkout del branch base
- [ ] `GITHUB_TOKEN` con permessi minimi (`permissions:` esplicito in ogni workflow)
- [ ] Runner groups con restrizioni di workflow e repository
- [ ] Audit periodico delle Actions usate (`gh api repos/ORG/REPO/actions/workflows`)
- [ ] Nessun PAT di lunga durata; preferire GitHub App o OIDC
- [ ] Workflow approval richiesta per contributori esterni
- [ ] Network egress limitato sui runner (solo domini necessari)

---

## Security Hardening Avanzato

Oltre alle basi trattate nella sezione precedente, il hardening avanzato comprende tecniche di isolamento a livello di kernel, analisi dei rischi specifici dei runner, e implementazione di policy di sicurezza a livello di cluster Kubernetes.

### Isolamento con gVisor (runsc)

gVisor è un kernel applicativo che intercetta le system call dei container, fornendo un livello di isolamento superiore a quello dei container standard:

```yaml
# RuntimeClass per gVisor
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc

---
# Runner con gVisor
# values-gvisor.yaml
template:
  spec:
    runtimeClassName: gvisor
    containers:
      - name: runner
        image: ghcr.io/actions/actions-runner:latest
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
```

### Network Policy per Runner Isolati

```yaml
# NetworkPolicy: runner possono solo raggiungere GitHub e il registry interno
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: runner-egress-policy
  namespace: arc-runners
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/part-of: "ci-infrastructure"
  policyTypes:
    - Egress
    - Ingress
  ingress: []  # Nessun traffico inbound
  egress:
    # DNS
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    # GitHub API e servizi
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - protocol: TCP
          port: 443
    # Registry interno
    - to:
        - namespaceSelector:
            matchLabels:
              name: registry
      ports:
        - protocol: TCP
          port: 5000
```

### Pod Security Standards

```yaml
# Applicare Pod Security Standards al namespace dei runner
apiVersion: v1
kind: Namespace
metadata:
  name: arc-runners
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**Nota**: La modalità DinD richiede `privileged: true`, che è incompatibile con il profilo `restricted`. In questo caso usare il profilo `baseline` o preferire la modalità Kubernetes.

### Audit Log dei Runner

```bash
#!/bin/bash
# audit-runner-activity.sh
# Audit delle attività dei runner per rilevare comportamenti sospetti

GITHUB_ORG="myorg"
OUTPUT_FILE="runner-audit-$(date +%Y%m%d).json"

echo "=== Audit Runner $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$OUTPUT_FILE"

# 1. Elencare tutti i runner e il loro stato
gh api "orgs/${GITHUB_ORG}/actions/runners" \
  --paginate \
  --jq '.runners[] | {
    id: .id,
    name: .name,
    os: .os,
    status: .status,
    busy: .busy,
    labels: [.labels[].name]
  }' | tee -a "$OUTPUT_FILE"

# 2. Controllare i runner groups e le loro restrizioni
gh api "orgs/${GITHUB_ORG}/actions/runner-groups" \
  --jq '.runner_groups[] | {
    id: .id,
    name: .name,
    visibility: .visibility,
    allows_public_repos: .allows_public_repositories,
    restricted_to_workflows: .restricted_to_workflows,
    selected_workflows: .selected_workflows
  }' | tee -a "$OUTPUT_FILE"

# 3. Verificare che nessun runner group permetta repository pubblici
UNSAFE_GROUPS=$(gh api "orgs/${GITHUB_ORG}/actions/runner-groups" \
  --jq '[.runner_groups[] | select(.allows_public_repositories == true)] | length')

if [ "$UNSAFE_GROUPS" -gt 0 ]; then
  echo "CRITICO: ${UNSAFE_GROUPS} runner groups permettono repository pubblici!" | tee -a "$OUTPUT_FILE"
fi

# 4. Controllare i workflow run recenti per anomalie
gh api "orgs/${GITHUB_ORG}/actions/runners" \
  --jq '.runners[] | select(.status == "offline") | .name' | while read -r runner_name; do
  echo "ATTENZIONE: Runner offline: ${runner_name}" | tee -a "$OUTPUT_FILE"
done
```

---

## Osservabilità con Prometheus, Grafana e OpenTelemetry

L'ARC moderno espone metriche native che possono essere consumate da Prometheus per una visibilità completa sul comportamento dei runner.

### Abilitazione Metriche in ARC

```bash
# Installare il controller con metriche abilitate
helm upgrade --install arc \
  --namespace arc-systems \
  --set metrics.controllerManagerAddr=":8080" \
  --set metrics.listenerAddr=":8080" \
  --set metrics.listenerEndpoint="/metrics" \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller
```

### ServiceMonitor per Prometheus Operator

```yaml
# ServiceMonitor per il Controller Manager
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: arc-controller-metrics
  namespace: arc-systems
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: gha-runner-scale-set-controller
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics

---
# ServiceMonitor per il Listener
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: arc-listener-metrics
  namespace: arc-runners
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      actions.github.com/scale-set-name: production-linux
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics
```

### Metriche Chiave Esposte da ARC

```
# Metriche del Controller
arc_controller_pending_ephemeral_runners      # Runner in attesa di creazione
arc_controller_running_ephemeral_runners      # Runner in esecuzione
arc_controller_failed_ephemeral_runners       # Runner falliti
arc_controller_assigned_jobs                  # Job assegnati
arc_controller_started_jobs_total             # Job avviati (counter)
arc_controller_completed_jobs_total           # Job completati (counter)

# Metriche del Listener
arc_listener_available_jobs                   # Job disponibili in coda
arc_listener_acquired_jobs                    # Job acquisiti
arc_listener_desired_runners                  # Runner desiderati
arc_listener_idle_runners                     # Runner in idle
arc_listener_registered_runners               # Runner registrati
```

### Dashboard Grafana: Query PromQL Avanzate

```
# Tasso di completamento job (ultimi 5 minuti)
rate(arc_controller_completed_jobs_total[5m])

# Tempo medio di attesa in coda
histogram_quantile(0.95,
  rate(arc_controller_job_queue_duration_seconds_bucket[15m])
)

# Efficienza runner: rapporto busy/totali
arc_listener_registered_runners - arc_listener_idle_runners
/
arc_listener_registered_runners

# Alert: job in coda per più di 5 minuti
arc_listener_available_jobs > 0
and
time() - arc_listener_available_jobs_timestamp > 300

# Tasso di fallimento runner
rate(arc_controller_failed_ephemeral_runners[1h])
/
rate(arc_controller_started_jobs_total[1h])
```

### Alerting con PrometheusRule

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: arc-runner-alerts
  namespace: monitoring
spec:
  groups:
    - name: arc.runners
      rules:
        - alert: ARCRunnerJobsStuck
          expr: arc_listener_available_jobs > 0
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "Job in coda da più di 10 minuti"
            description: "{{ $value }} job in attesa nel scale set {{ $labels.scale_set_name }}"

        - alert: ARCRunnerHighFailureRate
          expr: |
            rate(arc_controller_failed_ephemeral_runners[30m])
            / rate(arc_controller_started_jobs_total[30m]) > 0.1
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Tasso di fallimento runner superiore al 10%"
            description: "{{ $value | humanizePercentage }} dei runner stanno fallendo"

        - alert: ARCListenerDown
          expr: up{job="arc-listener"} == 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Listener ARC non raggiungibile"
            description: "Il Listener Pod per {{ $labels.scale_set_name }} non risponde"

        - alert: ARCRunnerScaleSetAtMax
          expr: |
            arc_listener_registered_runners >= arc_listener_max_runners
          for: 15m
          labels:
            severity: warning
          annotations:
            summary: "Scale set al limite massimo di runner"
            description: "Il scale set {{ $labels.scale_set_name }} è al massimo ({{ $value }} runner)"
```

### OpenTelemetry per Tracing dei Workflow

```yaml
# Workflow con tracing OpenTelemetry
name: Build con Tracing
on: push

env:
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector.monitoring:4318"
  OTEL_SERVICE_NAME: "github-actions-ci"

jobs:
  build:
    runs-on: [self-hosted, linux]
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11

      - name: Inizio trace
        run: |
          TRACE_ID=$(openssl rand -hex 16)
          SPAN_ID=$(openssl rand -hex 8)
          echo "TRACE_ID=${TRACE_ID}" >> $GITHUB_ENV
          echo "SPAN_ID=${SPAN_ID}" >> $GITHUB_ENV
          echo "Build trace: ${TRACE_ID}"

      - name: Build con trace context
        run: |
          TRACEPARENT="00-${TRACE_ID}-${SPAN_ID}-01"
          # Propagare il context ai servizi downstream
          make build TRACEPARENT="${TRACEPARENT}"
```

---

## Infrastructure as Code per Runner

L'infrastruttura dei runner deve essere gestita come codice per garantire riproducibilità, auditabilità e disaster recovery rapido.

### Terraform: AWS con ASG e Spot

```hcl
# terraform/modules/github-runner/main.tf

variable "github_org" {
  type        = string
  description = "Organizzazione GitHub"
}

variable "runner_count" {
  type        = number
  default     = 2
  description = "Numero di runner"
}

variable "instance_type" {
  type        = string
  default     = "c6i.xlarge"
  description = "Tipo istanza EC2"
}

# AMI personalizzata con runner preinstallato (via Packer)
data "aws_ami" "runner" {
  most_recent = true
  owners      = ["self"]
  filter {
    name   = "name"
    values = ["github-runner-*"]
  }
}

# Launch template
resource "aws_launch_template" "runner" {
  name_prefix   = "github-runner-"
  image_id      = data.aws_ami.runner.id
  instance_type = var.instance_type

  vpc_security_group_ids = [aws_security_group.runner.id]

  iam_instance_profile {
    name = aws_iam_instance_profile.runner.name
  }

  user_data = base64encode(templatefile("${path.module}/userdata.sh.tpl", {
    github_org    = var.github_org
    runner_labels = "linux,x64,aws,spot"
  }))

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = 100
      volume_type           = "gp3"
      iops                  = 5000
      throughput            = 250
      delete_on_termination = true
      encrypted             = true
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name    = "github-runner"
      Role    = "ci-runner"
      Managed = "terraform"
    }
  }
}

# Auto Scaling Group con mixed instances (spot + on-demand)
resource "aws_autoscaling_group" "runner" {
  name                = "github-runners"
  desired_capacity    = var.runner_count
  min_size            = 0
  max_size            = var.runner_count * 3
  vpc_zone_identifier = var.private_subnet_ids

  mixed_instances_policy {
    instances_distribution {
      on_demand_base_capacity                  = 1
      on_demand_percentage_above_base_capacity = 0
      spot_allocation_strategy                 = "capacity-optimized"
    }

    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.runner.id
        version            = "$Latest"
      }

      override {
        instance_type = "c6i.xlarge"
      }
      override {
        instance_type = "c6a.xlarge"
      }
      override {
        instance_type = "c5.xlarge"
      }
      override {
        instance_type = "m6i.xlarge"
      }
    }
  }

  tag {
    key                 = "Name"
    value               = "github-runner"
    propagate_at_launch = true
  }
}

# Security group: solo egress verso GitHub
resource "aws_security_group" "runner" {
  name_prefix = "github-runner-"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS verso GitHub e registry"
  }

  egress {
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = [var.vpc_cidr]
    description = "DNS interno"
  }

  # Nessuna regola ingress
}
```

### Packer: Immagine AMI per Runner

```hcl
# packer/github-runner.pkr.hcl

packer {
  required_plugins {
    amazon = {
      version = ">= 1.3.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

variable "runner_version" {
  type    = string
  default = "2.321.0"
}

source "amazon-ebs" "runner" {
  ami_name      = "github-runner-${var.runner_version}-{{timestamp}}"
  instance_type = "c6i.large"
  region        = "eu-west-1"

  source_ami_filter {
    filters = {
      name                = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["099720109477"]  # Canonical
  }

  ssh_username = "ubuntu"
}

build {
  sources = ["source.amazon-ebs.runner"]

  # Installare dipendenze
  provisioner "shell" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get install -y curl jq git libicu-dev docker.io",
      "sudo systemctl enable docker",
      "sudo useradd -m -s /bin/bash github-runner",
      "sudo usermod -aG docker github-runner",
    ]
  }

  # Installare il runner
  provisioner "shell" {
    inline = [
      "sudo mkdir -p /opt/actions-runner",
      "sudo chown github-runner:github-runner /opt/actions-runner",
      "cd /opt/actions-runner",
      "sudo -u github-runner curl -sL https://github.com/actions/runner/releases/download/v${var.runner_version}/actions-runner-linux-x64-${var.runner_version}.tar.gz | sudo -u github-runner tar xz",
      "sudo /opt/actions-runner/bin/installdependencies.sh",
    ]
  }

  # Pre-pull immagini Docker comuni
  provisioner "shell" {
    inline = [
      "sudo docker pull node:20-alpine",
      "sudo docker pull python:3.12-slim",
      "sudo docker pull postgres:16-alpine",
      "sudo docker pull redis:7-alpine",
      "sudo docker pull docker:dind",
    ]
  }

  # Installare script di avvio
  provisioner "file" {
    source      = "scripts/runner-startup.sh"
    destination = "/tmp/runner-startup.sh"
  }

  provisioner "shell" {
    inline = [
      "sudo mv /tmp/runner-startup.sh /opt/actions-runner/startup.sh",
      "sudo chmod +x /opt/actions-runner/startup.sh",
      "sudo chown github-runner:github-runner /opt/actions-runner/startup.sh",
    ]
  }

  # Hardening di sicurezza
  provisioner "shell" {
    inline = [
      "sudo apt-get autoremove -y",
      "sudo apt-get clean",
      "sudo rm -rf /var/lib/apt/lists/*",
      "sudo truncate -s 0 /var/log/*.log",
      "sudo rm -rf /tmp/*",
    ]
  }
}
```

### Ansible: Configurazione Runner Fleet

```yaml
# ansible/playbooks/setup-runners.yml
---
- name: Configurare GitHub Actions Self-Hosted Runner
  hosts: runners
  become: yes
  vars:
    runner_version: "2.321.0"
    runner_user: "github-runner"
    runner_dir: "/opt/actions-runner"
    github_org: "myorg"

  tasks:
    - name: Creare utente runner
      user:
        name: "{{ runner_user }}"
        shell: /bin/bash
        groups: docker
        append: yes

    - name: Creare directory runner
      file:
        path: "{{ runner_dir }}"
        state: directory
        owner: "{{ runner_user }}"
        group: "{{ runner_user }}"
        mode: "0755"

    - name: Scaricare runner
      get_url:
        url: "https://github.com/actions/runner/releases/download/v{{ runner_version }}/actions-runner-linux-{{ ansible_architecture | replace('x86_64', 'x64') | replace('aarch64', 'arm64') }}-{{ runner_version }}.tar.gz"
        dest: "/tmp/actions-runner.tar.gz"
        checksum: "sha256:{{ runner_checksum }}"

    - name: Estrarre runner
      unarchive:
        src: "/tmp/actions-runner.tar.gz"
        dest: "{{ runner_dir }}"
        remote_src: yes
        owner: "{{ runner_user }}"
        group: "{{ runner_user }}"

    - name: Installare dipendenze runner
      command: "{{ runner_dir }}/bin/installdependencies.sh"

    - name: Configurare systemd service hardened
      template:
        src: templates/github-runner.service.j2
        dest: /etc/systemd/system/github-runner.service
        mode: "0644"
      notify: restart runner

    - name: Abilitare e avviare servizio
      systemd:
        name: github-runner
        enabled: yes
        state: started
        daemon_reload: yes

  handlers:
    - name: restart runner
      systemd:
        name: github-runner
        state: restarted
```

---

## Pricing 2026 e Impatto Economico

A partire da marzo 2026, GitHub ha introdotto un **costo piattaforma di $0.002 per minuto** per l'uso di self-hosted runner nei repository privati e interni. Questo rappresenta un cambiamento significativo nel modello di costo, dato che precedentemente l'uso di self-hosted runner era completamente gratuito.

### Cosa Include il Costo Piattaforma

Il costo di $0.002/min copre l'utilizzo dell'infrastruttura GitHub per:
- Orchestrazione dei job (accodamento, routing, assegnazione)
- Gestione dei log e degli artefatti
- Iniezione e masking dei secret
- Servizio OIDC
- API di gestione runner

**Questo costo si applica anche se il runner gira su hardware di proprietà.**

### Impatto Economico per Scenari Tipici

```
=== Scenario 1: Startup (5 sviluppatori, 3.000 min/mese) ===
Costo piattaforma: 3.000 × $0.002 = $6/mese
Impatto: trascurabile

=== Scenario 2: Team Medio (20 sviluppatori, 30.000 min/mese) ===
Costo piattaforma: 30.000 × $0.002 = $60/mese
Impatto: modesto, ma da considerare nel budget

=== Scenario 3: Enterprise (200 sviluppatori, 500.000 min/mese) ===
Costo piattaforma: 500.000 × $0.002 = $1.000/mese
Impatto: significativo, richiede ottimizzazione

=== Scenario 4: CI Intensivo (monorepo, 2.000.000 min/mese) ===
Costo piattaforma: 2.000.000 × $0.002 = $4.000/mese
Impatto: rilevante, motivazione per ottimizzare la durata dei job
```

### Strategie di Mitigazione dei Costi

1. **Ottimizzare la durata dei job**: Ogni minuto risparmiato risparmia $0.002. Cache aggressiva, build incrementali, parallelismo.
2. **Eliminare job non necessari**: Audit dei workflow per rimuovere step ridondanti o workflow che girano senza produrre valore.
3. **Path filtering**: Usare `paths:` nei trigger per eseguire workflow solo quando i file rilevanti cambiano.
4. **Concurrency groups**: Cancellare automaticamente le esecuzioni precedenti quando arriva un nuovo push.

```yaml
# Ottimizzazioni per ridurre i minuti
name: Build Ottimizzato
on:
  push:
    paths:
      - "src/**"       # Solo se il codice sorgente cambia
      - "package.json"
    branches: [main, develop]

concurrency:
  group: build-${{ github.ref }}
  cancel-in-progress: true  # Cancella build precedenti sullo stesso branch

jobs:
  build:
    runs-on: [self-hosted, linux]
    timeout-minutes: 15  # Hard limit per prevenire job runaway
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
        with:
          fetch-depth: 0  # O 1 se non serve la history completa

      - name: Cache dipendenze
        uses: actions/cache@v4
        with:
          path: node_modules
          key: deps-${{ hashFiles('package-lock.json') }}

      - name: Build (solo se necessario)
        run: |
          # Skip build se solo i test sono cambiati
          CHANGED=$(git diff --name-only HEAD~1 HEAD | grep -v test/ || true)
          if [ -n "$CHANGED" ]; then
            npm run build
          else
            echo "Skip build: solo file di test modificati"
          fi
```

### Confronto Economico Aggiornato (2026)

```
=== 30.000 min/mese, team di 20 sviluppatori ===

GitHub-Hosted Linux Standard:
  30.000 × $0.008 = $240/mese

Self-Hosted su Hardware Proprio:
  Hardware ammortizzato:  $80/mese
  Elettricità + rete:     $40/mese
  Costo piattaforma:      $60/mese  (NUOVO)
  Manutenzione:           $30/mese
  Totale:                 $210/mese  (12% risparmio)

Self-Hosted su AWS Spot:
  EC2 Spot:               $120/mese
  Costo piattaforma:      $60/mese  (NUOVO)
  Totale:                 $180/mese  (25% risparmio)

Self-Hosted su ARC + Spot con scale-to-zero:
  EC2 Spot (uso effettivo): $50/mese
  ARC/K8s overhead:         $30/mese
  Costo piattaforma:        $60/mese  (NUOVO)
  Totale:                   $140/mese  (42% risparmio)
```

Il costo piattaforma riduce il vantaggio economico dei self-hosted runner, rendendo la decisione più dipendente da fattori non-costo (accesso rete privata, hardware specializzato, compliance, performance) piuttosto che dal puro risparmio.

---

## Riepilogo

I self-hosted runners sono uno strumento potente per team che necessitano di maggiore controllo, performance o accesso a risorse private rispetto ai GitHub-hosted runners. Tuttavia, introducono una responsabilità operativa significativa: installazione, manutenzione, sicurezza, monitoraggio, e scaling diventano compiti del team.

La scelta tra GitHub-hosted e self-hosted non è binaria. Molti team usano un approccio ibrido: GitHub-hosted per i job standard (lint, test unitari) e self-hosted per i job che lo richiedono (build Docker, test di integrazione con servizi interni, deploy, GPU). Questo approccio offre il meglio di entrambi i mondi: zero manutenzione per il grosso del lavoro e pieno controllo dove necessario.

Per team che iniziano con i self-hosted runners, il consiglio è partire semplici: un singolo runner Linux come servizio systemd, con pulizia automatica e monitoraggio base. Quando il carico cresce, passare a runner ephemeral e poi, se necessario, a Kubernetes con l'Actions Runner Controller per l'autoscaling.

L'ecosistema si è evoluto significativamente tra il 2025 e il 2026. L'ARC moderno con architettura a due chart Helm, JIT token, multilabel support (ARC 0.14+), e metriche Prometheus native ha reso la gestione dei runner su Kubernetes significativamente più matura. Allo stesso tempo, gli attacchi alla supply chain (tj-actions, reviewdog) hanno evidenziato l'importanza critica di pinnare le Actions al SHA, usare runner ephemeral, e limitare i permessi dei workflow. Il nuovo costo piattaforma di $0.002/min introdotto nel 2026 richiede ai team di valutare attentamente il rapporto costo-beneficio e di ottimizzare la durata dei job per massimizzare il valore dell'infrastruttura self-hosted.

---

## Esercizi Pratici

### Esercizio 1: Self-Hosted Runner Linux con systemd

Installa e configura un self-hosted runner su una VM Linux:

```bash
# 1. Creare una VM Ubuntu 22.04 (o usare una VM esistente)
# 2. Scaricare il runner:
#    mkdir actions-runner && cd actions-runner
#    curl -o runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/...
#    tar xzf runner.tar.gz
# 3. Registrare il runner:
#    ./config.sh --url https://github.com/org/repo --token <TOKEN> \
#      --name "linux-dev-01" --labels "linux,x64,dev" --work "_work"
# 4. Installare come servizio systemd:
#    sudo ./svc.sh install && sudo ./svc.sh start
# 5. Verificare: sudo ./svc.sh status
# 6. Creare un workflow che usa il runner:
#    runs-on: [self-hosted, linux, dev]
# 7. Eseguire il workflow e verificare che giri sul runner locale

# Verifica:
# - Il runner appare in Settings > Actions > Runners con status "Idle"
# - Il workflow gira con successo sul self-hosted runner
# - I log del runner mostrano l'esecuzione del job
```

**Criteri di successo:** runner registrato, workflow eseguito, log visibili.

### Esercizio 2: Runner Ephemeral con Auto-Cleanup

Configura un runner che si auto-distrugge dopo ogni job:

```bash
# 1. Registrare il runner con --ephemeral:
#    ./config.sh --url https://github.com/org/repo --token <TOKEN> \
#      --name "ephemeral-01" --labels "ephemeral" --ephemeral
# 2. Creare uno script di loop che:
#    a. Ottiene un nuovo token di registrazione via API
#    b. Configura il runner
#    c. Esegue il runner (./run.sh)
#    d. Dopo il job, pulisce la directory di lavoro
#    e. Ripete dal punto (a)
# 3. Testare: eseguire 3 workflow consecutivi
# 4. Verificare che ogni job inizia con un ambiente pulito:
#    - Nessun file residuo dal job precedente
#    - Nessun processo orfano
#    - Nessuna variabile d'ambiente contaminata

# Script di verifica:
# ls -la _work/ dopo ogni job → deve essere vuoto all'inizio
```

### Esercizio 3: Runner Docker Containerizzato

Costruisci un runner self-hosted come container Docker:

```dockerfile
# 1. Creare il Dockerfile:
#    - Base: ubuntu:22.04
#    - Installare: curl, jq, git, docker-cli, nodejs, python3
#    - Creare utente non-root "runner"
#    - Scaricare e installare il runner
#    - ENTRYPOINT: script che configura e avvia il runner
# 2. Creare entrypoint.sh:
#    - Leggere GITHUB_URL e GITHUB_TOKEN da environment
#    - Configurare il runner con --ephemeral
#    - Avviare con ./run.sh
#    - Pulire alla terminazione (trap SIGTERM)
# 3. Buildare e avviare:
#    docker build -t gh-runner .
#    docker run -e GITHUB_URL=... -e GITHUB_TOKEN=... gh-runner
# 4. Verificare che il runner appaia su GitHub e accetti job
```

### Esercizio 4: Autoscaling con ARC su Kubernetes

Configura Actions Runner Controller per scaling automatico:

```bash
# 1. Prerequisiti: cluster Kubernetes funzionante (minikube o kind per test)
# 2. Installare ARC via Helm:
#    helm install arc --namespace arc-systems --create-namespace \
#      oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller
# 3. Creare un runner scale set:
#    helm install arc-runner-set --namespace arc-runners --create-namespace \
#      --set githubConfigUrl="https://github.com/org" \
#      --set githubConfigSecret.github_token="ghp_xxx" \
#      --set maxRunners=5 --set minRunners=0 \
#      oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
# 4. Testare l'autoscaling:
#    - Eseguire 1 workflow → 1 pod runner creato
#    - Eseguire 5 workflow simultanei → fino a 5 pod
#    - Attendere completamento → pod terminati, minRunners attivi
# 5. Monitorare: kubectl get pods -n arc-runners -w
```

### Esercizio 5: Architettura Ibrida con Monitoring

Progetta un'architettura ibrida GitHub-hosted + self-hosted con monitoraggio:

```yaml
# 1. Definire la strategia:
#    - GitHub-hosted: lint, unit test, code scanning (job standard)
#    - Self-hosted: integration test con DB interno, build Docker, deploy
# 2. Creare un workflow che usa entrambi:
#    Job lint: runs-on: ubuntu-latest (GitHub-hosted)
#    Job integration-test: runs-on: [self-hosted, linux, internal-network]
#    Job deploy: runs-on: [self-hosted, linux, production]
# 3. Configurare monitoraggio con script cron:
#    - Controllare stato runner ogni 5 minuti via API:
#      gh api orgs/{org}/actions/runners --jq '.runners[] | {name, status}'
#    - Alert su Slack se un runner è offline da più di 10 minuti
# 4. Aggiungere dashboard con metriche:
#    - Numero di job completati per runner
#    - Tempo medio di esecuzione
#    - Percentuale di fallimenti
# 5. Documentare la configurazione come Infrastructure as Code
```

---

## Letture Consigliate

- **Libro**: "Learning GitHub Actions" di Brent Laster, O'Reilly Media, 2024 — capitolo dedicato ai self-hosted runners e ARC
- **GitHub Docs**: "Hosting your own runners" — https://docs.github.com/en/actions/hosting-your-own-runners (consultato: 2026-05-24)
- **GitHub Blog**: "Scaling GitHub Actions with ARC" — https://github.blog/changelog/2023-09-19-github-actions-actions-runner-controller-general-availability/ (consultato: 2026-05-24)
- **ARC Documentation**: https://github.com/actions/actions-runner-controller/blob/master/docs/README.md (consultato: 2026-05-24)
- **Kubernetes Documentation**: "Running a container runtime" — https://kubernetes.io/docs/concepts/containers/ (consultato: 2026-05-24)
- **GitHub Security Guide**: "Security hardening for self-hosted runners" — https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions#hardening-for-self-hosted-runners (consultato: 2026-05-24)

---

## Collegamenti Incrociati

| Modulo | Collegamento | Relazione |
|--------|-------------|-----------|
| 18 | [18-github-actions-avanzate.md](18-github-actions-avanzate.md) | Actions avanzate — runner labels, environments, matrix strategy |
| 04 | [04-github-actions.md](04-github-actions.md) | Fondamenti Actions — concetti base di runner e workflow |
| 19 | [19-github-actions-ci-cd-ricette.md](19-github-actions-ci-cd-ricette.md) | Ricette CI/CD — pipeline che beneficiano di self-hosted runners |
| 24 | [24-devops-completo-con-github.md](24-devops-completo-con-github.md) | Pipeline DevOps — architettura ibrida con runners |
| 16 | [16-github-security-scanning.md](16-github-security-scanning.md) | Security — rischi di sicurezza dei self-hosted runners |
| 17 | [17-github-actions-workflow-sintassi.md](17-github-actions-workflow-sintassi.md) | Sintassi workflow — runs-on e label selection |
| 26 | [26-oidc-cloud-credentials.md](26-oidc-cloud-credentials.md) | OIDC — autenticazione sicura dai runner ai cloud provider |
| 22 | [22-github-copilot-codespaces-enterprise.md](22-github-copilot-codespaces-enterprise.md) | Enterprise — runner groups e policy organizzative |
| 09 | [09-git-lfs-submodules-monorepo.md](09-git-lfs-submodules-monorepo.md) | Git LFS — runner con accesso a storage per file grandi |

---

## Glossario Locale

| Termine | Definizione |
|---------|------------|
| **ARC (Actions Runner Controller)** | Controller Kubernetes che gestisce l'autoscaling dei self-hosted runner come pod effimeri |
| **Autoscaling** | Capacità di creare e distruggere runner automaticamente in base al carico di job in coda |
| **Ephemeral runner** | Runner configurato con `--ephemeral` che si deregistra dopo aver completato un singolo job |
| **GitHub-hosted runner** | Runner gestito da GitHub (ubuntu-latest, windows-latest, macos-latest) con ambiente preconfigurato |
| **Helm chart** | Package Kubernetes usato per installare ARC e configurare runner scale set |
| **Job queue** | Coda dei job in attesa di un runner disponibile con le label corrispondenti |
| **Label** | Etichetta assegnata a un runner per il routing dei job (es. `linux`, `gpu`, `production`) |
| **Runner group** | Raggruppamento di runner a livello di organizzazione/enterprise con restrizioni di accesso per repository |
| **Runner registration token** | Token temporaneo usato per registrare un runner con un repository o organizzazione |
| **Runner scale set** | Definizione ARC che specifica minRunners, maxRunners, immagine container e configurazione |
| **Self-hosted runner** | Runner installato e gestito dall'utente su infrastruttura propria (bare metal, VM, container) |
| **systemd service** | Servizio Linux che gestisce il ciclo di vita del runner (avvio automatico, restart, log) |
| **Work directory** | Directory `_work/` dove il runner clona i repository e esegue i job |
