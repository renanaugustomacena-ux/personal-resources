# Tutorial Linux 02 — Shell Mastery: Bash, Pipeline, Job Control, Scripting

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** bash avanzato, redirezione, pipeline, expansion, scripting robusto, job control
> **Prerequisiti:** `tutorial_linux_01_filesystem.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Shell Mastery
│
├── Bash fundamentals
│   ├── Variabili e expansion
│   ├── Quotatura: ", ', \
│   ├── Brace expansion {a,b,c}
│   └── Globbing: *, ?, [abc]
│
├── Redirezione e pipeline
│   ├── >, >>, 2>, 2>&1, &>
│   ├── < (stdin), <<EOF (heredoc)
│   ├── | pipe, |& (stderr+stdout)
│   └── tee, xargs, parallel
│
├── Scripting robusto
│   ├── set -euo pipefail
│   ├── Funzioni e return codes
│   ├── Gestione errori trap
│   ├── Argomenti: $1, $@, getopts
│   └── Array associativi
│
├── Job Control
│   ├── & background
│   ├── Ctrl+Z / fg / bg
│   ├── jobs, kill, nohup
│   └── disown, screen, tmux
│
└── Strumenti avanzati
    ├── awk — elaborazione colonne
    ├── sed — sostituzione stream
    ├── sort, uniq, cut, paste
    └── xargs — costruire comandi
```

---

# Parte A — Bash avanzato

---

## A1. Variabili e parameter expansion

```bash
# Assegnamento (no spazi!)
NOME="Mario"
ETA=30
LISTA=(a b c d)

# Expansion base
echo "$NOME"           # Mario
echo "${NOME}"         # Mario (parentesi esplicite — uso consigliato)
echo "${NOME}Rossi"    # MarioRossi

# Default values
echo "${VARIABILE:-default}"       # usa "default" se VARIABILE non impostata
echo "${VARIABILE:=default}"       # imposta e usa "default" se non impostata
echo "${VARIABILE:?errore msg}"    # esce con errore se non impostata

# Manipolazione stringhe
PERCORSO="/home/mario/documenti/file.txt"
echo "${PERCORSO##*/}"    # file.txt (rimuove prefisso più lungo)
echo "${PERCORSO%/*}"     # /home/mario/documenti (rimuove suffisso)
echo "${PERCORSO%.txt}"   # /home/mario/documenti/file (rimuove .txt)
echo "${#PERCORSO}"       # 37 (lunghezza)
echo "${PERCORSO/mario/anna}"   # sostituisce prima occorrenza
echo "${PERCORSO//a/A}"        # sostituisce tutte le occorrenze

# Substring
echo "${PERCORSO:6:5}"   # mario (posizione:lunghezza)
echo "${PERCORSO^^}"     # UPPERCASE
echo "${PERCORSO,,}"     # lowercase

# Array
echo "${LISTA[0]}"       # a
echo "${LISTA[@]}"       # a b c d
echo "${#LISTA[@]}"      # 4 (numero elementi)
echo "${LISTA[@]:1:2}"   # b c (slice)

# Array associativo (bash 4+)
declare -A CONFIG
CONFIG[host]="localhost"
CONFIG[porta]=5432
echo "${CONFIG[host]}"
for chiave in "${!CONFIG[@]}"; do
    echo "$chiave = ${CONFIG[$chiave]}"
done
```

> **Analogia:** Le variabili bash con `${}` sono come le clausole di un contratto — le parentesi graffe rendono espliciti i confini del nome. `${NOME:-default}` è la clausola "in mancanza di": "usa questo valore se il primo non esiste". Una volta capita la sintassi, le expansion sono potentissime per elaborare percorsi e stringhe senza invocare programmi esterni.

---

## A2. Redirezione

```bash
# stdout (fd 1)
echo "OK" > /tmp/out.txt       # sovrascrive
echo "OK" >> /tmp/out.txt      # appende

# stderr (fd 2)
ls /non-esiste 2> /tmp/err.txt
ls /non-esiste 2>/dev/null     # scarica stderr

# stdout + stderr
ls /non-esiste &> /tmp/all.txt       # bash 4+
ls /non-esiste > /tmp/all.txt 2>&1   # POSIX equivalente

# stdin da file
mysql -u root < /tmp/dump.sql

# heredoc — blocco multiriga come stdin
cat << 'EOF' > /etc/motd
Benvenuto nel server di produzione.
Modifiche non autorizzate sono vietate.
EOF
# Nota: 'EOF' con apici previene l'expansion delle variabili

# herestring
grep "pattern" <<< "stringa da cercare"

# Pipe
ps aux | grep nginx | awk '{print $2}'   # PID di nginx

# tee — duplica output (file + stdout)
comando | tee /tmp/log.txt               # stdout + file
comando | tee -a /tmp/log.txt            # append

# Process substitution
diff <(ls dir1) <(ls dir2)   # confronta directory
while read linea; do
    echo "$linea"
done < <(grep -r "pattern" /etc/)
```

---

# Parte B — Scripting robusto

---

## B1. Script professionale con gestione errori

```bash
#!/usr/bin/env bash
# backup.sh — Esempio di script robusto

# Opzioni di sicurezza SEMPRE presenti
set -euo pipefail
# -e: exit su qualsiasi errore
# -u: tratta variabili non impostate come errori
# -o pipefail: una pipe fallisce se uno step fallisce

# Costanti
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "$0")"
readonly LOG_FILE="/var/log/${SCRIPT_NAME%.sh}.log"
readonly TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# Logging
log() {
    local livello="${1:-INFO}"
    local messaggio="$2"
    echo "[${TIMESTAMP}] [${livello}] ${messaggio}" | tee -a "$LOG_FILE"
}

log_info()  { log "INFO"  "$1"; }
log_warn()  { log "WARN"  "$1"; }
log_error() { log "ERROR" "$1" >&2; }

# Cleanup su uscita
cleanup() {
    local exit_code=$?
    log_info "Pulizia in corso (exit code: $exit_code)"
    rm -f /tmp/backup_$$.tmp 2>/dev/null || true
    exit "$exit_code"
}
trap cleanup EXIT
trap 'log_error "Segnale INT ricevuto"; exit 130' INT
trap 'log_error "Segnale TERM ricevuto"; exit 143' TERM

# Verifica prerequisiti
verifica_dipendenze() {
    local -a dipendenze=("rsync" "tar" "gzip")
    local mancanti=()
    for cmd in "${dipendenze[@]}"; do
        if ! command -v "$cmd" &>/dev/null; then
            mancanti+=("$cmd")
        fi
    done
    if [[ ${#mancanti[@]} -gt 0 ]]; then
        log_error "Dipendenze mancanti: ${mancanti[*]}"
        return 1
    fi
}

# Parsing argomenti
uso() {
    cat << EOF
Uso: $SCRIPT_NAME [opzioni] <sorgente> <destinazione>

Opzioni:
  -c, --comprimi     Comprimi con gzip
  -v, --verbose      Output dettagliato
  -n, --dry-run      Simula senza eseguire
  -h, --help         Mostra questo aiuto

Esempi:
  $SCRIPT_NAME -cv /home/mario /backup/mario
  $SCRIPT_NAME --dry-run /var/www /mnt/nas/www
EOF
}

COMPRIMI=false
VERBOSE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -c|--comprimi) COMPRIMI=true; shift ;;
        -v|--verbose)  VERBOSE=true; shift ;;
        -n|--dry-run)  DRY_RUN=true; shift ;;
        -h|--help)     uso; exit 0 ;;
        --)            shift; break ;;
        -*)            log_error "Opzione sconosciuta: $1"; uso; exit 1 ;;
        *)             break ;;
    esac
done

[[ $# -lt 2 ]] && { log_error "Mancano sorgente e destinazione"; uso; exit 1; }

SORGENTE="$1"
DESTINAZIONE="$2"

# Validazione input
[[ -d "$SORGENTE" ]] || { log_error "Sorgente non trovata: $SORGENTE"; exit 1; }
[[ -d "$DESTINAZIONE" ]] || mkdir -p "$DESTINAZIONE"

# Funzione principale
esegui_backup() {
    local sorgente="$1"
    local destinazione="$2"

    log_info "Avvio backup: $sorgente → $destinazione"

    local rsync_opts=(-av --delete --stats)
    $DRY_RUN && rsync_opts+=(--dry-run)
    $VERBOSE || rsync_opts=(-a --delete)

    if ! rsync "${rsync_opts[@]}" "$sorgente/" "$destinazione/"; then
        log_error "rsync fallito"
        return 1
    fi

    if $COMPRIMI; then
        local archivio="${destinazione}/backup_${TIMESTAMP}.tar.gz"
        log_info "Compressione: $archivio"
        tar czf "$archivio" -C "$(dirname "$destinazione")" "$(basename "$destinazione")"
    fi

    log_info "Backup completato con successo"
}

main() {
    verifica_dipendenze
    esegui_backup "$SORGENTE" "$DESTINAZIONE"
}

main "$@"
```

---

# Parte C — Strumenti fondamentali

---

## C1. awk per elaborazione dati

```bash
# awk: ogni riga è divisa in campi ($1, $2, ..., $NF)
# Pattern predefiniti: BEGIN (prima di qualsiasi riga), END (dopo tutto)

# Stampa colonne
ps aux | awk '{print $1, $2, $11}'   # user, PID, comando

# Somma colonna
ls -l | awk '{sum += $5} END {print "Totale:", sum, "bytes"}'

# Filtra per pattern
awk '/nginx|apache/{print}' /var/log/syslog

# Awk con separatore personalizzato
awk -F: '{print $1}' /etc/passwd   # stampa usernames

# Calcoli su CSV
awk -F',' 'NR>1 {sum+=$3; count++} END {print "Media:", sum/count}' dati.csv

# Programma awk completo
awk '
BEGIN {
    FS=":"       # separatore input
    OFS="\t"     # separatore output
    print "Username", "Shell"
}
$3 >= 1000 {    # solo UID >= 1000 (utenti normali)
    print $1, $7
}
END {
    print "---"
    print "Totale utenti:", NR
}
' /etc/passwd
```

---

## C2. sed per trasformazioni stream

```bash
# sed: stream editor — elabora riga per riga

# Sostituzione
sed 's/vecchio/nuovo/' file.txt            # prima occorrenza per riga
sed 's/vecchio/nuovo/g' file.txt           # tutte le occorrenze
sed 's/vecchio/nuovo/gi' file.txt          # case insensitive
sed -i 's/localhost/10.0.0.5/g' config.cfg # in-place (modifica il file)
sed -i.bak 's/localhost/10.0.0.5/g' config.cfg  # con backup

# Eliminare righe
sed '/^#/d' config.cfg          # rimuovi commenti
sed '/^$/d' file.txt            # rimuovi righe vuote
sed '5d' file.txt               # elimina riga 5
sed '5,10d' file.txt            # elimina righe 5-10

# Inserire testo
sed '5i\Nuova riga inserita' file.txt     # inserisci prima di riga 5
sed '5a\Nuova riga aggiunta' file.txt     # aggiungi dopo riga 5

# Elaborazione avanzata
# Rimuovi spazi iniziali e finali
sed 's/^[[:space:]]*//;s/[[:space:]]*$//' file.txt

# Aggiungi prefisso a ogni riga
sed 's/^/[INFO] /' /var/log/app.log

# Estrai range di righe
sed -n '100,200p' file.log    # stampa righe 100-200
sed -n '/START/,/END/p' file  # stampa tra pattern
```

---

## C3. Job control

```bash
# Lancia in background
lungo_processo &
PID=$!
echo "Avviato con PID $PID"

# Lista job in background
jobs -l

# Porta in foreground
fg %1      # job numero 1
fg %lungo  # job che inizia con "lungo"

# Metti in pausa (Ctrl+Z) poi background
# Ctrl+Z
bg %1

# nohup — sopravvive alla disconnessione
nohup lungo_processo &>> /var/log/processo.log &

# disown — rimuovi job dalla shell corrente (non lo ferma)
lungo_processo &
disown %1

# kill con segnali
kill -SIGTERM $PID    # chiusura elegante
kill -SIGKILL $PID    # forza chiusura (non gestibile)
kill -SIGHUP $PID     # ricarica configurazione (per molti daemon)
kill -l               # lista segnali

# Aspetta completamento
wait $PID
echo "Exit code: $?"

# Lancia N processi in parallelo con limite
MAX_PARALLEL=4
contatore=0
for file in *.csv; do
    elabora_file "$file" &
    contatore=$((contatore + 1))
    if [[ $contatore -ge $MAX_PARALLEL ]]; then
        wait -n   # bash 5.1+: aspetta UN qualsiasi job
        contatore=$((contatore - 1))
    fi
done
wait   # aspetta tutti i rimanenti
```

---

# Parte D — xargs e parallel

---

## D1. xargs e GNU parallel

```bash
# xargs — costruisce e lancia comandi con argomenti
find . -name "*.log" | xargs gzip          # comprimi tutti i .log
find . -name "*.log" | xargs -P4 gzip      # 4 processi in parallelo
find . -name "*.tmp" | xargs rm -f         # elimina tutti i .tmp

# xargs con input contenente spazi
find . -name "*.txt" -print0 | xargs -0 wc -l   # -print0/-0 per spazi

# xargs con placeholder
find . -name "*.jpg" | xargs -I{} convert {} {}.webp   # rinomina

# GNU parallel (pip install parallel o apt install parallel)
# Più potente di xargs per parallelismo
parallel gzip ::: *.log                    # comprimi in parallelo
parallel -j4 echo {} ::: a b c d          # 4 job max
cat url_list.txt | parallel curl -O        # scarica URL in parallelo

# Esempio reale: ridimensiona immagini
ls *.jpg | parallel -j8 convert {} -resize 50% small/{}
```

---

# Parte E — Riepilogo

## Shebang e best practice script

```bash
#!/usr/bin/env bash    # portabile — usa bash nel PATH
# NON usare #!/bin/bash — non funziona su macOS e alcuni sistemi

set -euo pipefail     # SEMPRE le prime righe dello script

# Pattern consigliati
[[ -z "$VAR" ]] && { echo "VAR non impostata"; exit 1; }
command -v curl &>/dev/null || { echo "curl non trovato"; exit 1; }
readonly TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
```

## Quick reference

| Espressione | Significato |
|---|---|
| `$?` | Exit code ultimo comando |
| `$$` | PID processo corrente |
| `$!` | PID ultimo background job |
| `$#` | Numero argomenti |
| `$@` | Tutti gli argomenti (array) |
| `$*` | Tutti gli argomenti (stringa) |
| `${VAR:-def}` | Usa "def" se VAR non impostata |
| `${#VAR}` | Lunghezza di VAR |
| `${VAR##*/}` | Basename (rimuove path) |
| `${VAR%.*}` | Rimuove estensione |

## Prossimi passi

- `tutorial_linux_03_gestione_pacchetti.md` — apt, dnf, pacman, snap
- `tutorial_linux_04_systemd.md` — gestire servizi con systemd
