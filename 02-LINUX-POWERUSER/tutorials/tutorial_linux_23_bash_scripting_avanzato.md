# Tutorial Linux 23 — Bash Scripting Avanzato: Template, Testing, CI

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** scripting avanzato, testing bash, idempotenza, CI, shellcheck
> **Prerequisiti:** `tutorial_linux_02_shell_mastery.md`
> **Durata stimata:** 12-16 ore

---

## Mappa concettuale

```
Bash Scripting Avanzato
│
├── Pattern professionali
│   ├── Template robusto
│   ├── Idempotenza
│   ├── Locking (flock)
│   └── Rollback automatico
│
├── Testing
│   ├── bats-core — framework test bash
│   ├── Mocking comandi
│   └── Test con fixture
│
├── Qualità
│   ├── ShellCheck — static analysis
│   ├── shellharden — sicurezza
│   └── shfmt — formattazione
│
├── Pattern avanzati
│   ├── Named pipe / Process substitution
│   ├── Coprocess
│   └── Trap avanzato
│
└── CI/CD per script
    ├── GitHub Actions per bash
    └── Test in container
```

---

# Parte A — Template professionale

---

## A1. Script template completo

```bash
#!/usr/bin/env bash
# ============================================================
# NOME: deploy.sh
# SCOPO: Deploy applicazione con rollback automatico
# VERSIONE: 2.0.0
# UTILIZZO: ./deploy.sh [--env ENV] [--tag TAG] [--dry-run]
# ============================================================

# ---- Safety ------------------------------------------------
set -euo pipefail
IFS=$'\n\t'    # Internal Field Separator sicuro (no word splitting su spazi)

# ---- Costanti ----------------------------------------------
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "$0")"
readonly LOG_FILE="/var/log/deploy.log"
readonly LOCK_FILE="/tmp/${SCRIPT_NAME%.sh}.lock"
readonly DEPLOY_DIR="/opt/app"
readonly BACKUP_DIR="/opt/app-backup"
readonly TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# ---- Variabili configurabili (con default) -----------------
ENV="${ENV:-production}"
TAG="${TAG:-latest}"
DRY_RUN=false
VERBOSE=false

# ---- Logging -----------------------------------------------
readonly COLOR_RESET='\033[0m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'

_log() {
    local level="$1"
    local color="$2"
    shift 2
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*"
    # Stderr per errori, stdout per il resto
    if [[ "$level" == "ERROR" ]]; then
        printf "${color}%s${COLOR_RESET}\n" "$msg" >&2
        echo "$msg" >> "$LOG_FILE"
    else
        printf "${color}%s${COLOR_RESET}\n" "$msg"
        echo "$msg" >> "$LOG_FILE"
    fi
}

log_info()  { _log "INFO"    "$COLOR_BLUE"   "$@"; }
log_ok()    { _log "OK"      "$COLOR_GREEN"  "$@"; }
log_warn()  { _log "WARN"    "$COLOR_YELLOW" "$@"; }
log_error() { _log "ERROR"   "$COLOR_RED"    "$@"; }
log_debug() { $VERBOSE && _log "DEBUG" "$COLOR_RESET" "$@" || true; }

# ---- Cleanup e trap ----------------------------------------
CLEANUP_TASKS=()

cleanup() {
    local exit_code=$?
    log_info "Pulizia in corso (exit: $exit_code)"
    for task in "${CLEANUP_TASKS[@]:-}"; do
        log_debug "Eseguo: $task"
        eval "$task" 2>/dev/null || true
    done
    rm -f "$LOCK_FILE"
    exit "$exit_code"
}

trap cleanup EXIT
trap 'log_error "SIGINT ricevuto"; exit 130' INT
trap 'log_error "SIGTERM ricevuto"; exit 143' TERM

# ---- Locking -----------------------------------------------
acquisisci_lock() {
    exec 9>"$LOCK_FILE"
    if ! flock -n 9; then
        log_error "Un'altra istanza è in esecuzione (lock: $LOCK_FILE)"
        exit 1
    fi
}

# ---- Prerequisiti ------------------------------------------
verifica_prerequisiti() {
    local -a richiesti=("docker" "git" "curl" "jq")
    local mancanti=()

    for cmd in "${richiesti[@]}"; do
        command -v "$cmd" &>/dev/null || mancanti+=("$cmd")
    done

    [[ ${#mancanti[@]} -eq 0 ]] || {
        log_error "Prerequisiti mancanti: ${mancanti[*]}"
        exit 1
    }

    # Verifica versione minima
    local docker_version
    docker_version=$(docker --version | grep -oP '\d+\.\d+' | head -1)
    local major=${docker_version%%.*}
    [[ "$major" -ge 20 ]] || { log_error "Docker >= 20 richiesto (trovato: $docker_version)"; exit 1; }
}

# ---- Parsing argomenti -------------------------------------
uso() {
    cat << EOF
Uso: $SCRIPT_NAME [OPZIONI]

Opzioni:
  -e, --env ENV       Ambiente target (default: production)
  -t, --tag TAG       Tag Docker da deployare (default: latest)
  -n, --dry-run       Simula senza eseguire
  -v, --verbose       Output dettagliato
  -h, --help          Mostra questo messaggio

Esempi:
  $SCRIPT_NAME --env staging --tag v1.2.3
  $SCRIPT_NAME --dry-run --tag main
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -e|--env)     ENV="$2";    shift 2 ;;
        -t|--tag)     TAG="$2";    shift 2 ;;
        -n|--dry-run) DRY_RUN=true; shift ;;
        -v|--verbose) VERBOSE=true; shift ;;
        -h|--help)    uso; exit 0 ;;
        --)           shift; break ;;
        -*)           log_error "Opzione sconosciuta: $1"; uso; exit 1 ;;
        *)            log_error "Argomento inatteso: $1"; uso; exit 1 ;;
    esac
done

# ---- Funzioni deploy ---------------------------------------
esegui() {
    if $DRY_RUN; then
        log_info "[DRY-RUN] $*"
    else
        log_debug "Eseguo: $*"
        eval "$@"
    fi
}

crea_backup() {
    log_info "Creazione backup..."
    local backup_path="$BACKUP_DIR/$TIMESTAMP"
    esegui "mkdir -p '$backup_path'"
    esegui "cp -a '$DEPLOY_DIR/.' '$backup_path/'"
    CLEANUP_TASKS+=("log_info 'Backup disponibile in: $backup_path'")
    log_ok "Backup creato: $backup_path"
}

rollback() {
    local backup_path="$BACKUP_DIR/$TIMESTAMP"
    if [[ -d "$backup_path" ]]; then
        log_warn "Avvio rollback..."
        esegui "rsync -a --delete '$backup_path/' '$DEPLOY_DIR/'"
        esegui "systemctl restart mia-app"
        log_ok "Rollback completato"
    else
        log_error "Nessun backup disponibile per rollback"
    fi
}

deploy() {
    log_info "Deploy di mia-app:$TAG su $ENV"

    crea_backup

    # Pull immagine
    esegui "docker pull mia-org/mia-app:$TAG"

    # Aggiorna con zero-downtime (rolling)
    esegui "docker service update --image mia-org/mia-app:$TAG mia-app-service" || {
        log_error "Deploy fallito, avvio rollback..."
        rollback
        exit 1
    }

    # Verifica health
    local max_wait=60
    local wait=0
    while [[ $wait -lt $max_wait ]]; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            log_ok "Deploy completato! App healthy."
            return 0
        fi
        sleep 5
        wait=$((wait + 5))
        log_info "Attendo health check... ($wait/${max_wait}s)"
    done

    log_error "Health check fallito dopo ${max_wait}s, rollback..."
    rollback
    exit 1
}

# ---- Main --------------------------------------------------
main() {
    acquisisci_lock
    verifica_prerequisiti

    log_info "=== Deploy avviato ==="
    log_info "Ambiente: $ENV | Tag: $TAG | Dry-run: $DRY_RUN"

    deploy

    log_ok "=== Deploy completato con successo ==="
}

main "$@"
```

---

# Parte B — Testing con bats-core

---

## B1. Test automatici per script bash

```bash
# Installazione bats-core
git clone https://github.com/bats-core/bats-core.git
cd bats-core && ./install.sh /usr/local

# Struttura test
mkdir -p tests/fixtures tests/helpers

# tests/deploy.bats
cat > tests/deploy.bats << 'EOF'
#!/usr/bin/env bats

# Carica helpers
load 'helpers/mock'

# Setup: eseguito prima di ogni test
setup() {
    export TEST_DIR="$(mktemp -d)"
    export DEPLOY_DIR="$TEST_DIR/app"
    export BACKUP_DIR="$TEST_DIR/backup"
    mkdir -p "$DEPLOY_DIR" "$BACKUP_DIR"
    echo "file di test" > "$DEPLOY_DIR/app.conf"
}

# Teardown: eseguito dopo ogni test
teardown() {
    rm -rf "$TEST_DIR"
    unmock_all
}

@test "script richiede sudo se non root" {
    run bash deploy.sh --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Uso:"* ]]
}

@test "fallisce con ENV non valido" {
    run bash deploy.sh --env ""
    [ "$status" -ne 0 ]
}

@test "dry-run non esegue comandi reali" {
    mock docker "echo 'DOCKER MOCKED'"
    run bash deploy.sh --dry-run --tag v1.0.0
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY-RUN"* ]]
    assert_not_called docker pull
}

@test "rollback ripristina backup" {
    # Crea stato iniziale
    echo "versione-vecchia" > "$DEPLOY_DIR/app.conf"
    
    # Crea backup manuale
    TIMESTAMP="20240115_120000"
    mkdir -p "$BACKUP_DIR/$TIMESTAMP"
    cp "$DEPLOY_DIR/app.conf" "$BACKUP_DIR/$TIMESTAMP/"
    
    # Modifica file (simula deploy fallito)
    echo "versione-nuova" > "$DEPLOY_DIR/app.conf"
    
    # Esegui rollback
    run bash -c "source deploy.sh && rollback"
    [ "$status" -eq 0 ]
    
    # Verifica ripristino
    [ "$(cat "$DEPLOY_DIR/app.conf")" = "versione-vecchia" ]
}
EOF

# Esegui test
bats tests/deploy.bats
bats tests/   # tutti i test nella directory
bats --tap tests/   # TAP format per CI
```

---

# Parte C — Qualità e sicurezza

---

## C1. ShellCheck e shfmt

```bash
# ShellCheck — static analysis
apt install shellcheck
pip install shellcheck-py   # alternativa

# Controlla uno script
shellcheck script.sh

# Errori comuni che ShellCheck trova:
# SC2086: quote variable: "$VAR" non $VAR
# SC2046: quote command substitution: "$(cmd)" non $(cmd)
# SC2164: use "cd ... || exit"
# SC2181: use "if cmd; then" non "cmd; if [ $? -eq 0 ]"

# Integrazione CI
cat > .github/workflows/bash-lint.yml << 'EOF'
name: Lint Bash

on: [push, pull_request]

jobs:
  shellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: ShellCheck
        uses: ludeeus/action-shellcheck@master
        with:
          scandir: './scripts'
          severity: warning
EOF

# shfmt — formattazione consistente
snap install shfmt
# oppure
go install mvdan.cc/sh/v3/cmd/shfmt@latest

# Formatta in-place
shfmt -w -i 4 -bn -ci script.sh
# -i 4: 4 spazi
# -bn: binary op at start of line
# -ci: indent case branches

# Verifica senza modificare
shfmt -d script.sh    # diff
```

---

# Parte D — Pattern avanzati

---

## D1. Named pipe e coprocessi

```bash
# Named pipe (FIFO) — comunicazione tra processi
mkfifo /tmp/mia-pipe

# Produttore in background
produttore() {
    for i in {1..10}; do
        echo "dato $i"
        sleep 0.1
    done
} > /tmp/mia-pipe &

# Consumatore
while IFS= read -r riga; do
    echo "Elaboro: $riga"
done < /tmp/mia-pipe

rm /tmp/mia-pipe

# Coprocesso (bash 4+) — processo con stdin/stdout collegati
coproc mio_proc { python3 -c "
import sys
for line in sys.stdin:
    result = int(line.strip()) * 2
    print(result)
    sys.stdout.flush()
"; }

# Invia dati al coprocesso
for n in 5 10 15; do
    echo "$n" >&"${mio_proc[1]}"
    read -r risultato <&"${mio_proc[0]}"
    echo "$n * 2 = $risultato"
done

# Chiudi
exec "${mio_proc[1]}">&-
wait "$mio_proc_PID"
```

---

## D2. Idempotenza

```bash
# Funzioni idempotenti: eseguirle N volte = stesso risultato di 1 volta

# NON idempotente:
echo "mario ALL=(ALL) ALL" >> /etc/sudoers   # aggiunge ogni volta!

# Idempotente:
if ! grep -q "^mario ALL=" /etc/sudoers; then
    echo "mario ALL=(ALL) ALL" >> /etc/sudoers
fi

# Pattern idempotente per file
ensure_line() {
    local file="$1"
    local line="$2"
    grep -qxF "$line" "$file" 2>/dev/null || echo "$line" >> "$file"
}

ensure_line /etc/hosts "10.0.0.5  server.interno"
ensure_line /etc/hosts "10.0.0.6  backup.interno"

# Directory idempotente
mkdir -p /opt/app   # -p: non fallisce se esiste

# Symlink idempotente
ln -sf /opt/app-v2.0 /opt/app   # -f: sovrascrive se esiste

# Servizio idempotente
systemctl is-enabled --quiet nginx || systemctl enable nginx
systemctl is-active  --quiet nginx || systemctl start nginx
```

---

# Parte E — Riepilogo

## Checklist script professionale

```bash
#!/usr/bin/env bash        # ✓ Shebang portabile
set -euo pipefail          # ✓ Fail-fast
IFS=$'\n\t'               # ✓ IFS sicuro
readonly SCRIPT_DIR="..."  # ✓ Costanti readonly
log_info/log_error()       # ✓ Logging strutturato
trap cleanup EXIT          # ✓ Cleanup garantito
flock -n                   # ✓ Prevenzione sovrapposizione
while case/shift           # ✓ Parsing argomenti robusto
dry-run mode               # ✓ Testabilità
idempotente                # ✓ Sicuro da rieseguire
shellcheck pass            # ✓ Nessun warning
bats tests                 # ✓ Test automatici
```

## Prossimi passi

- `tutorial_linux_24_iptables_nftables.md` — firewall avanzato
- `tutorial_linux_02_shell_mastery.md` — fondamentali bash
