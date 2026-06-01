# Shell Mastery — Guida Completa

> **Modulo 02** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **Bash > zsh per scripting (compatibility); zsh > bash per interactive.**
2. **`set -euo pipefail` in ogni script.**
3. **POSIX shell sintassi se script deve girare ovunque.**
4. **`shellcheck` mandatory in CI.**


## Indice

- [Panoramica](#panoramica)
- [Shell Internals: Come Bash Parsa i Comandi](#shell-internals-come-bash-parsa-i-comandi)
- [Bash: Fondamenti e Configurazione](#bash-fondamenti-e-configurazione)
- [Editing della Riga di Comando e Readline](#editing-della-riga-di-comando-e-readline)
- [Variabili, Espansioni e Quoting](#variabili-espansioni-e-quoting)
- [Espansione Parametri Avanzata](#espansione-parametri-avanzata)
- [Pipe, Redirezioni e Processi](#pipe-redirezioni-e-processi)
- [I/O Avanzato: File Descriptor, exec e Named Pipes](#io-avanzato-file-descriptor-exec-e-named-pipes)
- [Process Substitution](#process-substitution)
- [Here Documents e Here Strings](#here-documents-e-here-strings)
- [Condizioni, Cicli e Funzioni](#condizioni-cicli-e-funzioni)
- [Test Avanzati: \[\[ \]\] vs \[ \]](#test-avanzati--vs-)
- [Array: Indicizzati e Associativi](#array-indicizzati-e-associativi)
- [Bash Scripting Avanzato](#bash-scripting-avanzato)
- [Shell Options: set e shopt in Dettaglio](#shell-options-set-e-shopt-in-dettaglio)
- [Trap Handling e Cleanup Patterns](#trap-handling-e-cleanup-patterns)
- [Coprocessi](#coprocessi)
- [Job Control Approfondito](#job-control-approfondito)
- [Text Processing: grep, sed, awk — Deep Dive](#text-processing-grep-sed-awk--deep-dive)
- [Regex e Pattern Matching — Masterclass](#regex-e-pattern-matching--masterclass)
- [Tmux — Deep Dive](#tmux--deep-dive)
- [Shell Debugging](#shell-debugging)
- [Zsh e Fish](#zsh-e-fish)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Esercizi Pratici](#esercizi-pratici)

---

## Panoramica

La shell è l'interfaccia tra l'utente e il kernel Linux. Padroneggiare la shell significa poter automatizzare qualsiasi operazione, processare dati complessi, gestire sistemi remoti e risolvere problemi in tempo reale. Bash è lo standard, Zsh e Fish sono alternative potenti. Questo modulo copre dalla configurazione base allo scripting avanzato, inclusi gli strumenti fondamentali di text processing.

Questo documento va oltre la superficie: copre i meccanismi interni del parser di Bash, la gestione avanzata dei file descriptor, il debugging sistematico, le trappole più comuni e le tecniche professionali che separano un utente competente da un power user.

---

## Shell Internals: Come Bash Parsa i Comandi

Comprendere l'ordine in cui Bash processa l'input è fondamentale per prevedere il comportamento degli script e diagnosticare bug sottili. Ogni riga inserita attraversa una pipeline di trasformazioni prima dell'esecuzione.

### Pipeline di Parsing

Bash processa l'input in quest'ordine preciso:

```
1. Lettura input (read)
2. Tokenizzazione (breaking into words and operators)
3. Parsing (analisi sintattica, costruzione albero comandi)
4. Espansioni (in ordine specifico — vedi sotto)
5. Quote removal
6. Redirezioni
7. Esecuzione del comando
```

### Ordine delle Espansioni

L'ordine è cruciale — ogni passo opera sull'output del precedente:

```
1. Brace expansion          {a,b,c}  →  a b c
2. Tilde expansion           ~  →  /home/user
3. Parameter expansion       $var  ${var}
4. Command substitution      $(cmd)  `cmd`
5. Arithmetic expansion      $((expr))
6. Word splitting            (su risultati non quotati delle espansioni 3-5)
7. Pathname expansion        (globbing: *, ?, [...])
8. Quote removal             (rimuove quote che non sono state espanse)
```

Esempio che illustra l'ordine:

```bash
# Brace expansion avviene PRIMA di parameter expansion:
var="hello"
echo ${var}{1,2,3}
# NON funziona come ci si aspetterebbe — brace expansion non vede $var
# Output: hello{1,2,3}  (brace expansion gia' avvenuta prima di $var)

# Corretto:
echo "${var}1" "${var}2" "${var}3"

# Brace expansion crea parole PRIMA che $var venga espanso:
echo {$var,world}
# Step 1 (brace): $var world
# Step 2 (param): hello world
```

### Word Splitting

Il word splitting avviene SOLO sui risultati non quotati di parameter expansion, command substitution e arithmetic expansion. La variabile `IFS` (Internal Field Separator) controlla quali caratteri fungono da separatori.

```bash
# IFS di default: spazio, tab, newline
echo "$IFS" | cat -A
# Output:  ^I$  (spazio, tab, newline)

# Word splitting in azione — PERICOLOSO senza quote:
filename="file con spazi.txt"
ls $filename        # Bash vede: ls file con spazi.txt  (3 argomenti!)
ls "$filename"      # Bash vede: ls "file con spazi.txt"  (1 argomento)

# IFS personalizzato per parsing CSV:
line="campo1,campo2,campo3"
IFS=',' read -r a b c <<< "$line"
echo "$a"    # campo1
echo "$b"    # campo2
echo "$c"    # campo3

# Ripristinare IFS:
OLD_IFS="$IFS"
IFS=':'
# ... operazioni ...
IFS="$OLD_IFS"

# Oppure usare un subshell per isolare la modifica:
(
    IFS=':'
    read -ra parts <<< "$PATH"
    printf '%s\n' "${parts[@]}"
)
# IFS originale invariato qui fuori
```

### Globbing (Pathname Expansion)

Il globbing avviene dopo il word splitting ed espande i pattern nei nomi di file corrispondenti.

```bash
# Pattern base:
*           # Qualsiasi sequenza (eccetto / e file che iniziano con .)
?           # Qualsiasi singolo carattere
[abc]       # a, b, o c
[a-z]       # Range
[!abc]      # Negazione (anche [^abc] in Bash)

# Globbing esteso (shopt -s extglob):
?(pattern)  # 0 o 1 occorrenza del pattern
*(pattern)  # 0 o piu' occorrenze
+(pattern)  # 1 o piu' occorrenze
@(pattern)  # Esattamente 1 occorrenza
!(pattern)  # Tutto tranne il pattern

# Esempi con extglob:
shopt -s extglob
ls !(*.log)              # Tutto tranne i .log
rm !(keep_this.txt)      # Cancella tutto tranne keep_this.txt
ls @(*.jpg|*.png)        # Solo .jpg e .png
ls ?(report)*.pdf        # report*.pdf o *.pdf

# Globstar (shopt -s globstar):
ls **/*.py               # Tutti i .py ricorsivamente
ls **/*.{js,ts}          # Tutti i .js e .ts ricorsivamente (brace + glob)

# ATTENZIONE: se un glob non matcha niente:
shopt -s nullglob        # Pattern non matchato → stringa vuota
shopt -s failglob        # Pattern non matchato → errore
# Default: il pattern resta letterale (es. *.xyz → "*.xyz")
```

### Command Substitution: Ordine di Esecuzione

```bash
# $() e' preferibile a `` per leggibilita' e annidamento:
result=$(echo $(date +%Y)-$(hostname))

# Il comando dentro $() viene eseguito in una SUBSHELL:
x=10
y=$(x=20; echo $x)
echo "$x"    # 10 — la subshell non modifica la shell padre
echo "$y"    # 20

# I trailing newlines vengono RIMOSSI da command substitution:
output=$(printf "hello\n\n\n")
echo "$output"    # "hello" — le newline finali sono sparite

# Workaround per preservare newline finali:
output=$(printf "hello\n\n\n"; echo x)
output="${output%x}"
```

---

## Bash: Fondamenti e Configurazione

### File di Configurazione

```bash
# ORDINE DI CARICAMENTO:

# Login shell (SSH, login console):
# 1. /etc/profile (globale)
# 2. ~/.bash_profile (utente) — se esiste, i successivi non vengono letti
#    OPPURE ~/.bash_login
#    OPPURE ~/.profile

# Non-login interactive (terminale in GUI):
# 1. /etc/bash.bashrc (globale, Debian/Ubuntu)
# 2. ~/.bashrc (utente)

# BEST PRACTICE: mettere tutto in ~/.bashrc e fare source da ~/.bash_profile:
# ~/.bash_profile:
#   if [ -f ~/.bashrc ]; then source ~/.bashrc; fi
```

Dettaglio aggiuntivo sui tipi di shell:

```bash
# Verificare il tipo di shell corrente:
# Login shell?
shopt -q login_shell && echo "login" || echo "non-login"

# Interactive?
[[ $- == *i* ]] && echo "interactive" || echo "non-interactive"

# Shell di uno script cron:
# - non-interactive
# - non-login
# - NON legge .bashrc ne' .bash_profile
# - environment minimale: solo le variabili del crontab

# Shell invocata con bash -l:
# - login shell (legge .bash_profile)

# Shell invocata con bash -c "comando":
# - non-interactive, non-login
# - NON legge nessun file di configurazione

# /etc/environment:
# - Letto da PAM, non da Bash
# - Formato KEY=value (non supporta espansioni)
# - Disponibile a tutti i processi dopo il login
```

### Personalizzazione del Prompt

```bash
# PS1 controlla il prompt. Escape sequences:
# \u = username, \h = hostname, \w = working dir, \$ = $ o # (root)
# Colori ANSI: \[\033[COLORm\] ... \[\033[0m\]

# Prompt informativo con colori
PS1='\[\033[01;32m\]\u@\h\[\033[0m\]:\[\033[01;34m\]\w\[\033[0m\]\$ '

# Prompt con git branch (aggiungere a .bashrc)
parse_git_branch() { git branch 2>/dev/null | grep '*' | sed 's/* //'; }
PS1='\u@\h:\w $(__git_ps1 "(%s)") \$ '

# Prompt multilinea con informazioni complete:
PS1='\n\[\033[1;33m\][\D{%F %T}]\[\033[0m\] '    # Data/ora
PS1+='\[\033[1;32m\]\u@\h\[\033[0m\]:'             # user@host
PS1+='\[\033[1;34m\]\w\[\033[0m\]'                  # directory
PS1+=' $(parse_git_branch)'                          # git branch
PS1+='\n\$ '                                         # nuova riga + prompt

# PS2: prompt di continuazione (default "> ")
PS2='... '

# PS3: prompt per select
PS3='Scegli un opzione: '

# PS4: prefisso per debug (set -x) — vedi sezione Shell Debugging
PS4='+${BASH_SOURCE[0]}:${LINENO}: ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'
```

### History e Opzioni

```bash
# ~/.bashrc — configurazione history
HISTSIZE=50000                    # Righe in memoria
HISTFILESIZE=100000               # Righe nel file
HISTCONTROL=ignoreboth            # Ignora duplicati e comandi con spazio iniziale
HISTTIMEFORMAT='%F %T '          # Timestamp nella history
shopt -s histappend               # Append, non sovrascrivere

# Opzioni utili
shopt -s cdspell                  # Corregge errori di battitura in cd
shopt -s globstar                 # ** matcha ricorsivamente
shopt -s checkwinsize             # Aggiorna LINES/COLUMNS dopo resize
set -o vi                         # Vi mode per editing riga di comando
# set -o emacs                    # Emacs mode (default)
```

Dettaglio su `HISTCONTROL`:

```bash
# HISTCONTROL accetta valori separati da ':'
HISTCONTROL=ignorespace           # Ignora comandi che iniziano con spazio
HISTCONTROL=ignoredups            # Ignora duplicati consecutivi
HISTCONTROL=ignoreboth            # Combinazione dei precedenti
HISTCONTROL=erasedups             # Rimuove TUTTE le occorrenze precedenti

# HISTIGNORE: pattern da non salvare
HISTIGNORE='ls:ll:cd:pwd:clear:history'
HISTIGNORE='&:ls:ll:[bf]g:exit'   # & = duplicati, poi comandi specifici

# Condividere history tra terminali in tempo reale:
PROMPT_COMMAND='history -a; history -c; history -r'
# -a: append nuovi comandi al file
# -c: clear history in memoria
# -r: rileggi dal file

# History expansion (! commands):
!!          # Ultimo comando
!$          # Ultimo argomento dell'ultimo comando
!^          # Primo argomento dell'ultimo comando
!42         # Comando numero 42 dalla history
!-3         # Terzultimo comando
!ssh        # Ultimo comando che inizia con "ssh"
!?pattern   # Ultimo comando che contiene "pattern"
^old^new    # Ripeti ultimo comando sostituendo old con new

# Ricerca interattiva:
# Ctrl+R    Ricerca all'indietro nella history
# Ctrl+S    Ricerca in avanti (potrebbe richiedere: stty -ixon)
# Ctrl+G    Annulla ricerca
```

---

## Editing della Riga di Comando e Readline

Bash utilizza la libreria GNU Readline per l'editing della riga di comando. La configurazione avviene tramite `~/.inputrc` o il comando `bind`.

### Keybinding Emacs Mode (default)

```bash
# Movimento:
Ctrl+A      # Inizio riga
Ctrl+E      # Fine riga
Ctrl+F      # Avanti un carattere
Ctrl+B      # Indietro un carattere
Alt+F       # Avanti una parola
Alt+B       # Indietro una parola

# Editing:
Ctrl+D      # Cancella carattere sotto il cursore (o EOF se riga vuota)
Ctrl+H      # Backspace
Ctrl+W      # Cancella parola precedente
Alt+D       # Cancella parola successiva
Ctrl+K      # Cancella dal cursore alla fine della riga (kill)
Ctrl+U      # Cancella dal cursore all'inizio della riga
Ctrl+Y      # Incolla l'ultimo testo cancellato (yank)
Alt+Y       # Cicla tra i testi cancellati (yank-pop)
Ctrl+T      # Scambia il carattere prima del cursore con quello sotto
Alt+T       # Scambia la parola corrente con la precedente
Alt+U       # Maiuscolo dalla posizione corrente alla fine della parola
Alt+L       # Minuscolo dalla posizione corrente alla fine della parola

# Controllo:
Ctrl+L      # Clear screen (mantiene la riga corrente)
Ctrl+C      # Interrompi (SIGINT)
Ctrl+Z      # Sospendi (SIGTSTP)
Ctrl+D      # Logout / EOF
Ctrl+_      # Undo
```

### Keybinding Vi Mode

```bash
set -o vi   # Attiva vi mode

# Partenza in insert mode. ESC per entrare in command mode.

# Insert mode:
# Identico a emacs mode per i tasti base (Ctrl+A, Ctrl+E, etc.)

# Command mode (dopo ESC):
h/l         # Sinistra/destra
w/b         # Avanti/indietro una parola
0/$         # Inizio/fine riga
x           # Cancella carattere
dw          # Cancella parola
dd          # Cancella riga
cw          # Change word
cc          # Change line
yy          # Copia riga
p           # Incolla
/pattern    # Ricerca nella history
n/N         # Match successivo/precedente
```

### Configurazione ~/.inputrc

```bash
# ~/.inputrc — configurazione readline

# Case-insensitive completion:
set completion-ignore-case on

# Mostra tutti i completamenti subito (senza doppio TAB):
set show-all-if-ambiguous on

# Colora i completamenti per tipo (directory, file, eseguibile):
set colored-stats on

# Mostra il tipo di file nei completamenti (/ per dir, * per exec):
set visible-stats on

# Completa parole parziali:
set show-all-if-unmodified on

# Tronca i nomi comuni nel completamento:
set completion-prefix-display-length 3

# Keybinding personalizzati:
"\e[A": history-search-backward    # Freccia su: ricerca nella history
"\e[B": history-search-forward     # Freccia giu': ricerca nella history

# Inserisci l'ultimo argomento con Alt+.
"\e.": yank-last-arg

# Esempio: remap Ctrl+P e Ctrl+N per ricerca history:
"\C-p": history-search-backward
"\C-n": history-search-forward
```

### Comandi bind

```bash
# Visualizzare i binding correnti:
bind -P                          # Tutti i binding
bind -P | grep 'search'         # Filtra

# Visualizzare le variabili readline:
bind -v

# Impostare un binding dalla shell:
bind '"\C-x\C-r": re-read-init-file'    # Ctrl+X Ctrl+R: rileggi inputrc
bind 'set completion-ignore-case on'      # Imposta variabile
```

---

## Variabili, Espansioni e Quoting

```bash
# VARIABILI
nome="valore"                     # Assegnamento (NO spazi intorno a =)
echo "$nome"                      # Espansione variabile
echo "${nome}_suffisso"           # Con delimitatori espliciti
readonly CONST="immutabile"       # Variabile readonly
export VAR="visibile ai figli"    # Esporta nell'environment

# VARIABILI SPECIALI
$0     # Nome dello script
$1-$9  # Argomenti posizionali
$#     # Numero di argomenti
$@     # Tutti gli argomenti (come lista)
$*     # Tutti gli argomenti (come singola stringa)
$?     # Exit code dell'ultimo comando
$$     # PID della shell corrente
$!     # PID dell'ultimo processo in background

# ESPANSIONI
${var:-default}      # Se var è vuota/non definita, usa "default"
${var:=default}      # Se var è vuota, assegna "default" e usa
${var:+altvalue}     # Se var è definita, usa "altvalue"
${var:?error msg}    # Se var è vuota, errore e exit

${#var}              # Lunghezza della stringa
${var#pattern}       # Rimuove match più corto dall'inizio
${var##pattern}      # Rimuove match più lungo dall'inizio
${var%pattern}       # Rimuove match più corto dalla fine
${var%%pattern}      # Rimuove match più lungo dalla fine
${var/old/new}       # Sostituisce prima occorrenza
${var//old/new}      # Sostituisce tutte le occorrenze
${var^^}             # Tutto maiuscolo
${var,,}             # Tutto minuscolo

# QUOTING
echo "con $espansione e spazi"       # Double quote: espande $var
echo 'senza espansione letterale'    # Single quote: tutto letterale
echo "path: $(pwd)"                  # Command substitution
echo "calcolo: $((2 + 3))"         # Arithmetic expansion

# COMMAND SUBSTITUTION
files=$(ls /etc/)                    # Output di ls in variabile
count=$(wc -l < file.txt)           # Conta righe
```

### Differenza tra $@ e $*

```bash
# $@ vs $* — fondamentale per gestire argomenti con spazi

set -- "arg uno" "arg due" "arg tre"

# $* senza quote: word splitting standard
for a in $*; do echo "[$a]"; done
# [arg] [uno] [arg] [due] [arg] [tre]   — 6 iterazioni!

# "$*" con quote: tutto come UNA singola stringa (separato da $IFS[0])
for a in "$*"; do echo "[$a]"; done
# [arg uno arg due arg tre]              — 1 iterazione

# $@ senza quote: identico a $* senza quote
for a in $@; do echo "[$a]"; done
# [arg] [uno] [arg] [due] [arg] [tre]   — 6 iterazioni

# "$@" con quote: ogni argomento come elemento SEPARATO (CORRETTO)
for a in "$@"; do echo "[$a]"; done
# [arg uno] [arg due] [arg tre]          — 3 iterazioni

# REGOLA: usare SEMPRE "$@" per passare argomenti
```

### Quoting in Profondita'

```bash
# Dollar-quoting per caratteri speciali:
echo $'testo\ncon\tnewline\te\ttab'
echo $'single quote: \' dentro dollar-quoting'

# Annidamento di quote:
echo "Lui disse: 'ciao'"            # Single dentro double
echo 'Lui disse: "ciao"'            # Double dentro single
echo "Lui disse: \"ciao\""          # Double escaped dentro double
echo "Path: '$(pwd)'"               # Command substitution con single

# Quote e array:
arr=("elemento uno" "elemento due")
echo "${arr[@]}"                     # Preserva gli spazi

# ATTENZIONE al word splitting nelle assegnazioni:
var=$(echo "hello world")            # Assegnamento: NO word splitting
echo $var                            # Espansione: SI' word splitting (ma qui ok)
echo "$var"                          # SEMPRE quotare nelle espansioni
```

---

## Espansione Parametri Avanzata

Questa sezione approfondisce ogni forma di espansione con esempi pratici reali.

### Valori di Default e Assegnamento

```bash
# ${var:-default} — usa default se var e' vuota o non definita
# (non modifica var)
unset nome
echo "${nome:-utente_anonimo}"    # "utente_anonimo"
echo "$nome"                       # "" — nome resta vuota

# ${var:=default} — assegna default se var e' vuota o non definita
# (modifica var)
unset db_host
echo "${db_host:=localhost}"       # "localhost"
echo "$db_host"                     # "localhost" — ora e' assegnata

# NOTA: NON funziona con $1, $2, ecc. (parametri posizionali non assegnabili)
# ${1:=default}  → errore!

# ${var:+altvalue} — usa altvalue SOLO se var e' definita e non vuota
verbose=""
echo "${verbose:+--verbose}"       # "" — verbose e' vuota
verbose="yes"
echo "${verbose:+--verbose}"       # "--verbose"

# Uso pratico: costruire comandi condizionalmente:
cmd="rsync -av"
cmd+=" ${DRY_RUN:+--dry-run}"
cmd+=" ${EXCLUDE:+--exclude=$EXCLUDE}"
cmd+=" $SRC $DST"

# ${var:?error_msg} — errore e exit se var e' vuota o non definita
DB_NAME="${DB_NAME:?'Variabile DB_NAME non definita. Uso: export DB_NAME=mydb'}"
# Se DB_NAME e' vuota: "bash: DB_NAME: Variabile DB_NAME non definita..."

# DIFFERENZA TRA : e senza :
# Senza : → controlla solo se la variabile e' DEFINITA (anche se vuota)
var=""
echo "${var-default}"    # "" — var e' definita (anche se vuota)
echo "${var:-default}"   # "default" — var e' definita ma VUOTA
```

### Estrazione e Slicing

```bash
# ${var:offset} — sottostringa dall'offset alla fine
text="Hello, World!"
echo "${text:7}"           # "World!"

# ${var:offset:length} — sottostringa con lunghezza specifica
echo "${text:0:5}"         # "Hello"
echo "${text:7:5}"         # "World"

# Offset negativo (dallo fine) — ATTENZIONE allo spazio prima del -
echo "${text: -6}"         # "orld!"
echo "${text: -6:3}"       # "orl"
# Senza lo spazio, ${text:-6} sarebbe interpretato come default value!

# Slicing su array:
arr=(a b c d e f g)
echo "${arr[@]:2:3}"       # c d e  (3 elementi dall'indice 2)
echo "${arr[@]: -3}"       # e f g  (ultimi 3 elementi)
```

### Rimozione Pattern (# e %)

```bash
# ${var#pattern}  — rimuove il match PIU' CORTO dall'INIZIO
# ${var##pattern} — rimuove il match PIU' LUNGO dall'INIZIO
# ${var%pattern}  — rimuove il match PIU' CORTO dalla FINE
# ${var%%pattern} — rimuove il match PIU' LUNGO dalla FINE

# Mnemonico: # e' a sinistra di $ sulla tastiera US → rimuove dall'inizio
#             % e' a destra → rimuove dalla fine

filepath="/home/user/documents/report.final.txt"

# Estrarre il nome del file:
echo "${filepath##*/}"          # "report.final.txt"  (rimuove tutto fino a /)

# Estrarre la directory:
echo "${filepath%/*}"           # "/home/user/documents"

# Estrarre l'estensione:
echo "${filepath##*.}"          # "txt"  (rimuove fino all'ultimo .)

# Estrarre il nome senza estensione:
filename="${filepath##*/}"       # "report.final.txt"
echo "${filename%.*}"            # "report.final"  (rimuove dalla fine fino al primo .)
echo "${filename%%.*}"           # "report"  (rimuove dalla fine fino all'ultimo .)

# Uso pratico: rinominare file in batch
for f in *.jpeg; do
    mv "$f" "${f%.jpeg}.jpg"
done

# Rimuovere prefisso da path:
full="/var/log/nginx/access.log"
echo "${full#/var/log/}"         # "nginx/access.log"

# Manipolazione URL:
url="https://example.com/path/to/resource?query=1"
echo "${url%%://*}"              # "https"  (protocollo)
echo "${url#*://}"               # "example.com/path/to/resource?query=1"
temp="${url#*://}"
echo "${temp%%/*}"               # "example.com"  (hostname)
echo "${temp#*/}"                # "path/to/resource?query=1"  (path+query)
```

### Sostituzione Pattern

```bash
# ${var/pattern/replacement}  — prima occorrenza
# ${var//pattern/replacement} — TUTTE le occorrenze
# ${var/#pattern/replacement} — solo se pattern e' all'INIZIO
# ${var/%pattern/replacement} — solo se pattern e' alla FINE

text="foo bar foo baz foo"
echo "${text/foo/FOO}"        # "FOO bar foo baz foo"  (prima)
echo "${text//foo/FOO}"       # "FOO bar FOO baz FOO"  (tutte)

# Sostituzione all'inizio/fine:
path="/usr/local/bin"
echo "${path/#\/usr/\/opt}"   # "/opt/local/bin"
echo "${path/%bin/sbin}"      # "/usr/local/sbin"

# Rimuovere un pattern (sostituzione con stringa vuota):
csv="campo1,campo2,campo3"
echo "${csv//,/ }"             # "campo1 campo2 campo3"

# Case manipulation:
nome="mario rossi"
echo "${nome^}"               # "Mario rossi"  (prima lettera maiuscola)
echo "${nome^^}"              # "MARIO ROSSI"  (tutto maiuscolo)
nome="MARIO ROSSI"
echo "${nome,}"               # "mARIO ROSSI"  (prima lettera minuscola)
echo "${nome,,}"              # "mario rossi"  (tutto minuscolo)

# Case manipulation con pattern:
echo "${nome^^[aeiou]}"       # Maiuscolo solo le vocali
```

### Indirezione e Operatori Speciali

```bash
# Indirezione: ${!prefix} — il valore della variabile il cui nome e' in prefix
var_name="USER"
echo "${!var_name}"            # Equivalente a echo "$USER"

# Lista variabili con prefisso:
MYAPP_HOST="localhost"
MYAPP_PORT="8080"
MYAPP_DB="postgres"
echo "${!MYAPP_@}"             # "MYAPP_DB MYAPP_HOST MYAPP_PORT"
echo "${!MYAPP_*}"             # Stessa cosa

# Utile per iterare su variabili di configurazione:
for var in ${!MYAPP_@}; do
    echo "$var = ${!var}"
done

# Trasformazione (Bash 5.1+):
var="hello world"
echo "${var@U}"                # "HELLO WORLD"  (uppercase)
echo "${var@L}"                # "hello world"  (lowercase)
echo "${var@Q}"                # "'hello world'" (quoted per riuso in shell)
echo "${var@E}"                # Espande sequenze di escape
echo "${var@A}"                # "var='hello world'" (assignment form)
```

---

## Pipe, Redirezioni e Processi

```bash
# REDIREZIONI
command > file          # stdout a file (sovrascrive)
command >> file         # stdout a file (append)
command 2> file         # stderr a file
command 2>&1           # stderr a stdout
command &> file         # stdout + stderr a file
command < file          # stdin da file
command <<EOF           # Here document
testo qui
EOF

# PIPE
command1 | command2     # stdout di cmd1 → stdin di cmd2
command1 |& command2    # stdout + stderr → stdin di cmd2

# ESEMPI PRATICI
# Top 10 processi per memoria
ps aux --sort=-%mem | head -11

# Contare file per tipo in una directory
find /var/log -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn

# Log in real-time filtrato
tail -f /var/log/syslog | grep --line-buffered "error"

# Processare CSV
cat data.csv | cut -d',' -f2,4 | sort -t',' -k2 -n | head -20

# PROCESSI IN BACKGROUND
command &               # Esegui in background
jobs                    # Lista job in background
fg %1                   # Porta job 1 in foreground
bg %1                   # Riprendi job 1 in background
Ctrl+Z                  # Sospendi processo corrente
nohup command &         # Continua dopo logout
disown %1               # Disassocia job dalla shell
```

### Pipe e Subshell — La Trappola Classica

```bash
# ATTENZIONE: in Bash, ogni comando in una pipe gira in una SUBSHELL.
# Le variabili modificate in una subshell NON sono visibili nella shell padre.

count=0
cat file.txt | while read -r line; do
    ((count++))
done
echo "$count"    # 0! — count e' stato incrementato nella subshell della pipe

# SOLUZIONI:

# 1. Redirezione al posto della pipe:
count=0
while read -r line; do
    ((count++))
done < file.txt
echo "$count"    # Valore corretto

# 2. Process substitution:
count=0
while read -r line; do
    ((count++))
done < <(grep "pattern" file.txt)
echo "$count"    # Valore corretto

# 3. lastpipe (Bash 4.2+):
shopt -s lastpipe
set +m                   # Disabilita job control (necessario)
count=0
cat file.txt | while read -r line; do
    ((count++))
done
echo "$count"            # Valore corretto — l'ultimo comando della pipe
                          # gira nella shell corrente

# 4. PIPESTATUS — exit code di ogni comando nella pipe:
false | true | false
echo "${PIPESTATUS[0]}"  # 1  (false)
echo "${PIPESTATUS[1]}"  # 0  (true)
echo "${PIPESTATUS[2]}"  # 1  (false)
echo "${PIPESTATUS[@]}"  # 1 0 1
```

---

## I/O Avanzato: File Descriptor, exec e Named Pipes

### File Descriptor Oltre 0, 1, 2

```bash
# I file descriptor standard:
# 0 = stdin
# 1 = stdout
# 2 = stderr
# 3-9 = disponibili per l'utente (Bash supporta fino a ~1024)

# Aprire un file descriptor per LETTURA:
exec 3< /etc/passwd
while IFS= read -r line <&3; do
    echo "$line"
done
exec 3<&-                # Chiudere il file descriptor 3

# Aprire un file descriptor per SCRITTURA:
exec 4> /tmp/output.log
echo "log entry 1" >&4
echo "log entry 2" >&4
exec 4>&-                # Chiudere il file descriptor 4

# Aprire un file descriptor per APPEND:
exec 5>> /tmp/output.log
echo "log entry 3" >&5
exec 5>&-

# Aprire un file descriptor per LETTURA E SCRITTURA:
exec 6<> /tmp/data.txt
read -r first_line <&6
echo "nuova riga" >&6
exec 6>&-

# Duplicare file descriptor:
exec 7>&1                # fd 7 diventa una copia di stdout
echo "va a stdout" >&7
exec 7>&-
```

### exec per Redirezione Permanente

```bash
# exec senza comando: redirige per il RESTO dello script

# Redirigere TUTTO lo stdout a un file:
exec > /tmp/script_output.log
echo "Questo va nel file"
echo "Anche questo"

# Redirigere stdout E stderr a un file:
exec > /tmp/script.log 2>&1
echo "stdout qui"
echo "stderr qui" >&2

# Pattern: salvare e ripristinare stdout
exec 3>&1                    # Salva stdout originale in fd 3
exec > /tmp/log.txt          # Redirige stdout al file
echo "va nel file"
exec 1>&3                    # Ripristina stdout originale
exec 3>&-                    # Chiudi fd 3
echo "va al terminale"

# Pattern: log su file E terminale con tee via fd:
exec 3>&1 4>&2
exec > >(tee -a /tmp/stdout.log) 2> >(tee -a /tmp/stderr.log >&2)
echo "visibile e loggato"
echo "errore visibile e loggato" >&2
exec 1>&3 2>&4               # Ripristina
exec 3>&- 4>&-               # Chiudi

# Redirigere solo stderr di una sezione:
{
    comando_che_potrebbe_fallire
    altro_comando
} 2>> /tmp/errori.log
```

### Named Pipes (FIFO)

```bash
# mkfifo crea una named pipe (un file speciale nel filesystem)
# Due processi possono comunicare tramite una named pipe:
# uno scrive, l'altro legge. La pipe BLOCCA finche' entrambi i lati non sono aperti.

mkfifo /tmp/my_pipe

# Terminale 1 (producer):
echo "messaggio dal producer" > /tmp/my_pipe   # Blocca finche' qualcuno legge

# Terminale 2 (consumer):
cat /tmp/my_pipe                                # Legge e sblocca il producer

# Cleanup:
rm /tmp/my_pipe

# Esempio pratico: progress reporting
mkfifo /tmp/progress_pipe

# Worker in background scrive il progresso:
(
    for i in $(seq 1 100); do
        echo "$i"
        sleep 0.1
    done > /tmp/progress_pipe
) &

# Main script legge e mostra il progresso:
while read -r pct < /tmp/progress_pipe; do
    printf '\rProgresso: %d%%' "$pct"
done
echo
rm /tmp/progress_pipe

# Esempio: multiplexare output di piu' fonti:
mkfifo /tmp/mux_pipe
tail -f /var/log/syslog > /tmp/mux_pipe &
tail -f /var/log/auth.log > /tmp/mux_pipe &
cat /tmp/mux_pipe    # Legge da entrambe le fonti
```

---

## Process Substitution

La process substitution `<()` e `>()` crea file descriptor temporanei che appaiono come file al comando che li riceve. Disponibile in Bash e Zsh (non in shell POSIX pure).

```bash
# <(command) — l'output del comando appare come un file leggibile
# >(command) — un file scrivibile il cui contenuto va allo stdin del comando

# Confrontare output di due comandi (gia' visto sopra, ma approfondiamo):
diff <(ls /dir1/) <(ls /dir2/)

# Confrontare file ordinati senza creare file temporanei:
diff <(sort file1.txt) <(sort file2.txt)

# Confrontare output remoto:
diff <(ssh server1 cat /etc/config) <(ssh server2 cat /etc/config)

# Passare output filtrato a un comando che vuole un FILE, non stdin:
# paste vuole file come argomenti:
paste <(cut -f1 data.tsv) <(cut -f3 data.tsv)

# comm richiede file ordinati — process substitution evita i temporanei:
comm -13 <(sort file1.txt) <(sort file2.txt)   # Righe solo in file2

# Leggere da piu' fonti contemporaneamente:
while IFS= read -r line1 <&3 && IFS= read -r line2 <&4; do
    echo "File1: $line1 | File2: $line2"
done 3< <(cat file1.txt) 4< <(cat file2.txt)

# >() — scrivere a un processo come se fosse un file:
# Salvare stdout e stderr in file diversi, mantenendo l'output a schermo:
command > >(tee stdout.log) 2> >(tee stderr.log >&2)

# Loggare con timestamp automatico:
exec > >(while IFS= read -r line; do
    printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$line"
done >> /tmp/script.log)

# Verificare se il path generato e' effettivamente un fd:
echo <(true)    # Stampa qualcosa come /dev/fd/63
```

---

## Here Documents e Here Strings

### Here Documents (<<)

```bash
# Sintassi base: <<DELIMITATORE ... DELIMITATORE
# Il delimitatore puo' essere qualsiasi parola (EOF, END, MARKER, ecc.)

cat <<EOF
Questo e' un here document.
Supporta espansione di variabili: $USER
E command substitution: $(date)
Le "quote" non hanno bisogno di escape.
EOF

# DELIMITATORE QUOTATO: disabilita tutte le espansioni
cat <<'EOF'
Questo e' letterale.
$USER non viene espanso.
$(date) nemmeno.
Utile per generare script o codice.
EOF

# TAB STRIPPING con <<-
# Rimuove i TAB (non gli spazi) dall'inizio di ogni riga E dal delimitatore.
# Permette di indentare il here document con il codice circostante.
if true; then
	cat <<-EOF
	Questo testo e' indentato con tab.
	I tab iniziali vengono rimossi nell'output.
	EOF
fi

# Here document come input a un comando:
mysql -u root -p <<EOF
SELECT * FROM users WHERE active = 1;
SHOW TABLES;
EOF

# Here document in una variabile:
read -r -d '' SQL_QUERY <<'EOF'
SELECT u.name, u.email, o.total
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.created_at > NOW() - INTERVAL 30 DAY
ORDER BY o.total DESC
LIMIT 10;
EOF
echo "$SQL_QUERY"

# Here document a un file:
cat > /tmp/config.ini <<EOF
[database]
host=${DB_HOST:-localhost}
port=${DB_PORT:-5432}
name=${DB_NAME:-myapp}
EOF

# Here document con sudo:
sudo tee /etc/myapp/config.conf > /dev/null <<'EOF'
# Configurazione generata
setting1 = value1
setting2 = value2
EOF

# Here document con pipe:
cat <<EOF | grep "importante"
riga normale
riga importante
altra riga
riga importante due
EOF

# Here document multipli nello stesso script:
{
    cat <<EOF1
Prima sezione.
EOF1
    cat <<EOF2
Seconda sezione.
EOF2
} > /tmp/output.txt
```

### Here Strings (<<<)

```bash
# <<< passa una stringa come stdin a un comando
# Piu' concisa di echo "..." | comando

# Base:
grep "pattern" <<< "stringa da cercare con pattern dentro"

# Con variabile:
line="campo1:campo2:campo3"
IFS=':' read -r a b c <<< "$line"
echo "$a $b $c"    # campo1 campo2 campo3

# Contare parole in una stringa:
wc -w <<< "cinque parole in questa frase"    # 5

# bc per calcoli:
result=$(bc <<< "scale=2; 100 / 3")
echo "$result"    # 33.33

# Confronto con pipe — here string e' piu' efficiente (niente subshell):
echo "$var" | read -r valore    # valore nella subshell! Perso.
read -r valore <<< "$var"       # valore nella shell corrente. Preservato.
```

---

## Condizioni, Cicli e Funzioni

```bash
# IF-THEN-ELSE
if [[ -f "/etc/passwd" ]]; then
    echo "File esiste"
elif [[ -d "/tmp" ]]; then
    echo "Directory esiste"
else
    echo "Nulla trovato"
fi

# TEST CONDIZIONI (dentro [[ ]])
# File: -f (file), -d (dir), -e (esiste), -r (leggibile), -w (scrivibile), -x (eseguibile)
# Stringa: -z (vuota), -n (non vuota), == (uguale), != (diversa)
# Numeri: -eq, -ne, -gt, -lt, -ge, -le
# Logici: && (AND), || (OR), ! (NOT)

# FOR LOOP
for file in /var/log/*.log; do
    echo "Processing: $file"
    wc -l "$file"
done

for i in {1..10}; do echo "$i"; done

for ((i=0; i<10; i++)); do echo "$i"; done

# WHILE LOOP
while read -r line; do
    echo "Riga: $line"
done < file.txt

# Loop infinito con condizione di uscita
while true; do
    check_service || break
    sleep 60
done

# CASE
case "$1" in
    start)   start_service ;;
    stop)    stop_service ;;
    restart) stop_service; start_service ;;
    *)       echo "Usage: $0 {start|stop|restart}" ;;
esac

# FUNZIONI
backup_db() {
    local db_name="${1:?'Database name required'}"
    local backup_dir="${2:-/backup}"
    local timestamp=$(date +%Y%m%d_%H%M%S)

    mysqldump "$db_name" > "${backup_dir}/${db_name}_${timestamp}.sql"
    return $?
}
# Chiamata: backup_db mydb /mnt/backup
```

### Funzioni Avanzate

```bash
# Le funzioni in Bash possono restituire solo un exit code (0-255).
# Per restituire dati, usare stdout o variabili globali/nameref.

# Pattern: restituire dati via stdout
get_ip() {
    hostname -I | awk '{print $1}'
}
my_ip=$(get_ip)

# Pattern: nameref (Bash 4.3+) — permette alla funzione di scrivere
# in una variabile del chiamante senza usare globali
parse_version() {
    local -n result_ref=$1      # nameref alla variabile del chiamante
    local version_string="$2"
    local IFS='.'
    read -r -a result_ref <<< "$version_string"
}
declare -a version_parts
parse_version version_parts "3.14.159"
echo "${version_parts[0]}"     # 3
echo "${version_parts[1]}"     # 14
echo "${version_parts[2]}"     # 159

# Variabili locali:
# 'local' limita lo scope alla funzione e alle funzioni chiamate da essa
# (dynamic scoping, NON lexical scoping come in Python/JS)
outer() {
    local x=10
    inner
}
inner() {
    echo "$x"    # 10! — inner vede la variabile local di outer
}

# Pattern: funzione con validazione
safe_mkdir() {
    local dir="${1:?'Directory path required'}"
    if [[ -d "$dir" ]]; then
        return 0
    fi
    if ! mkdir -p "$dir" 2>/dev/null; then
        echo "ERRORE: impossibile creare $dir" >&2
        return 1
    fi
}

# Pattern: funzione che accetta stdin O argomenti
process_input() {
    local input
    if [[ $# -gt 0 ]]; then
        input="$1"
    else
        input=$(cat)    # Leggi da stdin
    fi
    echo "${input^^}"   # Uppercase
}
process_input "hello"             # Da argomento
echo "world" | process_input      # Da pipe
```

### Select

```bash
# select — menu interattivo
PS3="Seleziona database: "
select db in "production" "staging" "development" "quit"; do
    case "$db" in
        production)  echo "ATTENZIONE: ambiente di produzione!"; break ;;
        staging)     echo "Connessione a staging..."; break ;;
        development) echo "Connessione a development..."; break ;;
        quit)        exit 0 ;;
        *)           echo "Opzione non valida" ;;
    esac
done
```

---

## Test Avanzati: [[ ]] vs [ ]

### Differenze Fondamentali

```bash
# [ ] e' un COMANDO (alias di 'test'). Soggetto a word splitting e globbing.
# [[ ]] e' una KEYWORD di Bash. Parsing speciale, piu' potente e sicuro.

# PROBLEMA CON [ ]:
file="nome con spazi.txt"
[ -f $file ]         # ERRORE: word splitting → [ -f nome con spazi.txt ]
[ -f "$file" ]       # OK ma bisogna ricordarsi di quotare SEMPRE

# [[ ]] gestisce automaticamente:
[[ -f $file ]]       # OK anche senza quote (ma quotare e' comunque buona pratica)

# [[ ]] supporta && e || direttamente:
[[ -f file && -r file ]]     # OK
[ -f file && -r file ]       # ERRORE SINTATTICO
[ -f file -a -r file ]       # Funziona ma -a e' deprecato

# [[ ]] supporta ( ) per raggruppamento senza escape:
[[ ( -f file || -d file ) && -r file ]]
[ \( -f file -o -d file \) -a -r file ]    # Necessario escape
```

### Pattern Matching con [[ ]]

```bash
# == e != supportano glob pattern in [[ ]]
file="report_2026_Q1.pdf"

[[ "$file" == *.pdf ]]         && echo "E' un PDF"
[[ "$file" == report_* ]]     && echo "E' un report"
[[ "$file" != *.tmp ]]        && echo "Non e' un file temporaneo"

# ATTENZIONE: il pattern NON deve essere quotato
pattern="*.pdf"
[[ "$file" == $pattern ]]      # OK — glob matching
[[ "$file" == "$pattern" ]]    # SBAGLIATO — confronto letterale con "*.pdf"
```

### Regex Matching con =~

```bash
# [[ string =~ regex ]] — usa Extended Regular Expressions (ERE)
# Il match e' parziale (non deve matchare l'intera stringa)

email="utente@example.com"
if [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "Email valida"
fi

# Cattura dei gruppi con BASH_REMATCH:
version="nginx/1.25.3"
if [[ "$version" =~ ([a-z]+)/([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
    echo "Software: ${BASH_REMATCH[1]}"    # nginx
    echo "Major:    ${BASH_REMATCH[2]}"    # 1
    echo "Minor:    ${BASH_REMATCH[3]}"    # 25
    echo "Patch:    ${BASH_REMATCH[4]}"    # 3
fi

# Regex in variabile (necessario per pattern con spazi o caratteri speciali):
date_regex='^([0-9]{4})-([0-9]{2})-([0-9]{2})$'
if [[ "2026-05-22" =~ $date_regex ]]; then
    echo "Anno:  ${BASH_REMATCH[1]}"
    echo "Mese:  ${BASH_REMATCH[2]}"
    echo "Giorno: ${BASH_REMATCH[3]}"
fi

# Validare un indirizzo IPv4:
ipv4_regex='^([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})$'
ip="192.168.1.100"
if [[ "$ip" =~ $ipv4_regex ]]; then
    valid=true
    for i in 1 2 3 4; do
        [[ ${BASH_REMATCH[$i]} -gt 255 ]] && valid=false
    done
    $valid && echo "IPv4 valido" || echo "Ottetto fuori range"
fi
```

### Confronti Numerici

```bash
# In [[ ]], == confronta STRINGHE, non numeri!
[[ 01 == 1 ]]    # Falso! "01" != "1" come stringa

# Per confronti numerici usare gli operatori dedicati:
[[ 01 -eq 1 ]]   # Vero! 01 == 1 come numero

# Oppure usare (( )) per aritmetica:
(( 01 == 1 ))    # Vero
(( x > 5 ))      # Le variabili non richiedono $ in (( ))

# Confronto di versioni (non banale):
version_gte() {
    printf '%s\n%s' "$1" "$2" | sort -V -C
}
version_gte "3.14" "3.9" && echo "3.14 >= 3.9"   # Vero
```

---

## Array: Indicizzati e Associativi

### Array Indicizzati

```bash
# Dichiarazione:
declare -a fruits=("mela" "pera" "banana" "arancia")
# Oppure:
files=(*.txt)                    # Glob expansion
nums=({1..10})                   # Brace expansion

# Accesso:
echo "${fruits[0]}"              # mela (primo elemento)
echo "${fruits[-1]}"             # arancia (ultimo elemento, Bash 4.3+)
echo "${fruits[@]}"              # Tutti gli elementi
echo "${#fruits[@]}"             # Numero di elementi: 4

# Aggiungere elementi:
fruits+=("kiwi")                 # Append
fruits[10]="mango"               # Indice sparso (gli indici 5-9 non esistono)

# Rimuovere elementi:
unset 'fruits[1]'                # Rimuove pera (l'array diventa sparso!)
# NOTA: gli indici NON vengono rinumerati dopo unset

# Iterazione CORRETTA:
for fruit in "${fruits[@]}"; do
    echo "$fruit"
done

# Iterazione con indice:
for i in "${!fruits[@]}"; do
    echo "fruits[$i] = ${fruits[$i]}"
done

# Slicing:
echo "${fruits[@]:1:2}"          # 2 elementi dall'indice 1

# Lunghezza di un singolo elemento:
echo "${#fruits[0]}"             # Lunghezza della stringa "mela" = 4

# Cercare in un array:
if [[ " ${fruits[*]} " == *" banana "* ]]; then
    echo "banana trovata"
fi

# Copiare un array:
declare -a fruits_copy=("${fruits[@]}")

# Array da output di comando:
readarray -t lines < file.txt          # Bash 4+
# Oppure:
mapfile -t lines < file.txt            # Sinonimo di readarray
# Oppure (compatibile Bash 3):
IFS=$'\n' read -r -d '' -a lines < file.txt

# Ordinare un array:
IFS=$'\n' sorted=($(sort <<< "${fruits[*]}")); unset IFS

# Filtrare un array:
declare -a text_files=()
for f in "${files[@]}"; do
    [[ -f "$f" && -s "$f" ]] && text_files+=("$f")
done

# Unire un array in stringa:
joined=$(IFS=','; echo "${fruits[*]}")   # "mela,banana,arancia,kiwi,mango"

# Stringa a array:
IFS=',' read -r -a parts <<< "$joined"
```

### Array Associativi (Hash)

```bash
# Dichiarazione (OBBLIGATORIO declare -A):
declare -A config
config[host]="192.168.1.1"
config[port]="22"
config[user]="admin"
config[protocol]="ssh"

# Oppure dichiarazione inline:
declare -A colors=(
    [red]="#FF0000"
    [green]="#00FF00"
    [blue]="#0000FF"
    [white]="#FFFFFF"
)

# Accesso:
echo "${config[host]}"            # 192.168.1.1
echo "${config[host]}:${config[port]}"

# Tutte le chiavi:
echo "${!config[@]}"              # host port user protocol (ordine non garantito)

# Tutti i valori:
echo "${config[@]}"

# Numero di elementi:
echo "${#config[@]}"              # 4

# Iterazione:
for key in "${!config[@]}"; do
    echo "$key = ${config[$key]}"
done

# Verificare se una chiave esiste:
if [[ -v config[host] ]]; then
    echo "host e' definito"
fi

# Rimuovere una chiave:
unset 'config[protocol]'

# Uso pratico: contare occorrenze
declare -A word_count
while read -r word; do
    ((word_count[$word]++))
done < <(tr ' ' '\n' < file.txt)

for word in "${!word_count[@]}"; do
    printf '%4d %s\n' "${word_count[$word]}" "$word"
done | sort -rn

# Uso pratico: lookup table per configurazione
declare -A env_config=(
    [production_db]="prod-db.example.com"
    [staging_db]="staging-db.example.com"
    [production_port]="5432"
    [staging_port]="5433"
)
env="${DEPLOY_ENV:-staging}"
db_host="${env_config[${env}_db]}"
db_port="${env_config[${env}_port]}"
```

---

## Bash Scripting Avanzato

```bash
#!/bin/bash
set -euo pipefail    # FONDAMENTALE per script robusti
# -e: exit su errore
# -u: errore su variabile non definita
# -o pipefail: errore se qualsiasi comando nella pipe fallisce

# TRAP: eseguire cleanup su exit/errore
cleanup() {
    rm -f "$TMPFILE"
    echo "Cleanup completato"
}
trap cleanup EXIT ERR

# FILE TEMPORANEI SICURI
TMPFILE=$(mktemp /tmp/script.XXXXXX)

# PARSING ARGOMENTI con getopts
while getopts "vf:o:" opt; do
    case "$opt" in
        v) VERBOSE=1 ;;
        f) INPUT_FILE="$OPTARG" ;;
        o) OUTPUT_FILE="$OPTARG" ;;
        *) echo "Usage: $0 [-v] -f input -o output" >&2; exit 1 ;;
    esac
done

# LOGGING
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"; }
log "Script avviato"

# ARRAY
declare -a files=("file1" "file2" "file3")
echo "${files[0]}"          # Primo elemento
echo "${files[@]}"          # Tutti gli elementi
echo "${#files[@]}"         # Numero di elementi

# ARRAY ASSOCIATIVO
declare -A config
config[host]="192.168.1.1"
config[port]="22"
echo "${config[host]}:${config[port]}"

# PROCESS SUBSTITUTION
diff <(ls /dir1/) <(ls /dir2/)    # Confronta output di due comandi
```

### Parsing Argomenti Complesso con getopt

```bash
# getopts (builtin): solo opzioni corte
# getopt (comando esterno GNU): opzioni corte E lunghe

# Pattern robusto con getopt:
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] <input_file>

Options:
  -h, --help            Mostra questo help
  -v, --verbose         Abilita output verboso
  -o, --output FILE     File di output (default: stdout)
  -n, --num NUM         Numero di iterazioni (default: 1)
  -d, --dry-run         Esegui senza modifiche
EOF
    exit "${1:-0}"
}

# Parsing con getopt (GNU):
OPTS=$(getopt -o hvo:n:d \
    --long help,verbose,output:,num:,dry-run \
    -n "$(basename "$0")" -- "$@") || usage 1

eval set -- "$OPTS"

VERBOSE=0
OUTPUT="/dev/stdout"
NUM=1
DRY_RUN=0

while true; do
    case "$1" in
        -h|--help)    usage 0 ;;
        -v|--verbose) VERBOSE=1; shift ;;
        -o|--output)  OUTPUT="$2"; shift 2 ;;
        -n|--num)     NUM="$2"; shift 2 ;;
        -d|--dry-run) DRY_RUN=1; shift ;;
        --)           shift; break ;;
        *)            echo "Errore interno" >&2; exit 1 ;;
    esac
done

# Argomenti rimanenti (dopo --):
if [[ $# -lt 1 ]]; then
    echo "ERRORE: input_file richiesto" >&2
    usage 1
fi
INPUT_FILE="$1"
```

### Template di Script Robusto

```bash
#!/bin/bash
# Descrizione: [scopo dello script]
# Uso: script.sh [-v] [-o output] <input>
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# Colori (solo se il terminale li supporta):
if [[ -t 1 ]]; then
    readonly RED=$'\033[0;31m'
    readonly GREEN=$'\033[0;32m'
    readonly YELLOW=$'\033[1;33m'
    readonly NC=$'\033[0m'    # No Color
else
    readonly RED='' GREEN='' YELLOW='' NC=''
fi

log_info()  { echo "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo "${YELLOW}[WARN]${NC}  $*" >&2; }
log_error() { echo "${RED}[ERROR]${NC} $*" >&2; }
die()       { log_error "$@"; exit 1; }

cleanup() {
    local exit_code=$?
    # Rimuovere file temporanei
    rm -rf "${TMPDIR:-}"
    exit "$exit_code"
}
trap cleanup EXIT

TMPDIR=$(mktemp -d "/tmp/${SCRIPT_NAME}.XXXXXX")

main() {
    # Logica principale qui
    log_info "Avvio in ${TMPDIR}"
    # ...
}

main "$@"
```

---

## Shell Options: set e shopt in Dettaglio

### set — Opzioni POSIX

```bash
# set -e (errexit): exit immediato se un comando fallisce
# ECCEZIONI dove -e NON causa l'exit:
#   - Comandi in condizione if/while/until
#   - Comandi prima di && o ||
#   - Comandi in una pipe (tranne l'ultimo, a meno di pipefail)
#   - Comandi in subshell con ( )
#   - Comandi in command substitution $(...)
set -e
false                    # Script termina qui
echo "Non raggiunto"

# PROBLEMA con set -e:
set -e
count=$(grep -c "pattern" file.txt)   # Se grep non trova nulla, exit code 1
                                        # Ma in command substitution, -e viene
                                        # ignorato! count=0, script continua.
grep -c "pattern" file.txt             # Qui invece -e causa l'exit!
# Soluzione:
count=$(grep -c "pattern" file.txt || true)

# set -u (nounset): errore se si usa una variabile non definita
set -u
echo "$variabile_inesistente"    # Errore: unbound variable
# ECCEZIONE: ${var:-default} non causa errore anche con -u

# set -o pipefail: il codice di uscita della pipe e' quello del primo
# comando che fallisce (invece dell'ultimo)
set -o pipefail
false | true | true
echo $?    # 1 (senza pipefail sarebbe 0)

# set -x (xtrace): stampa ogni comando prima dell'esecuzione
set -x
echo "debug"     # Output: + echo debug \n debug
set +x           # Disabilita

# set -f (noglob): disabilita il globbing
set -f
echo *.txt       # Stampa letteralmente "*.txt"
set +f           # Riabilita

# set -C (noclobber): impedisce di sovrascrivere file esistenti con >
set -C
echo "data" > file_esistente    # Errore: cannot overwrite existing file
echo "data" >| file_esistente   # >| forza la sovrascrittura

# set -o posix: modalita' POSIX strict
# set -o emacs / set -o vi: modalita' editing riga di comando

# Vedere tutte le opzioni correnti:
echo "$-"        # himBHs = le opzioni attive
set -o           # Lista completa con stato on/off
```

### shopt — Opzioni Bash-specifiche

```bash
# shopt -s OPZIONE    Abilita
# shopt -u OPZIONE    Disabilita
# shopt -q OPZIONE    Query (per uso in script, exit code)
# shopt               Mostra tutte le opzioni

# Le piu' utili:

shopt -s autocd          # Digitare un nome di directory → cd automatico
shopt -s cdspell         # Corregge errori di battitura in cd
shopt -s dirspell        # Corregge errori nel completamento di directory
shopt -s dotglob         # * include i file nascosti (.file)
shopt -s extglob         # Pattern estesi: ?(pat), *(pat), +(pat), @(pat), !(pat)
shopt -s failglob        # Glob senza match → errore (invece di lasciare il pattern)
shopt -s globstar        # ** matcha ricorsivamente nelle directory
shopt -s histappend      # Append alla history (non sovrascrivere)
shopt -s histreedit      # Permette di rieditare una sostituzione history fallita
shopt -s histverify      # Mostra il risultato di ! espansioni prima di eseguire
shopt -s nocaseglob      # Globbing case-insensitive
shopt -s nocasematch     # case/[[ ]] pattern matching case-insensitive
shopt -s nullglob        # Glob senza match → stringa vuota (non il pattern)
shopt -s checkwinsize    # Aggiorna LINES/COLUMNS dopo ogni comando

# Uso in script:
if shopt -q globstar; then
    echo "globstar e' attivo"
fi

# Combinare shopt con extglob per pattern avanzati:
shopt -s extglob
rm -v !(*.log|*.txt)     # Rimuovi tutto tranne .log e .txt
ls +(ab|cd)*.txt         # File che iniziano con "ab" o "cd" e finiscono con .txt
```

---

## Trap Handling e Cleanup Patterns

### Segnali Principali

```bash
# Segnale      Numero    Descrizione
# SIGHUP       1         Terminale chiuso / disconnessione
# SIGINT       2         Ctrl+C
# SIGQUIT      3         Ctrl+\  (con core dump)
# SIGKILL      9         Kill forzato (NON catturabile)
# SIGTERM      15        Terminazione "gentile" (default di kill)
# SIGSTOP      19        Stop forzato (NON catturabile)
# SIGTSTP      20        Ctrl+Z
# SIGCHLD      17        Figlio terminato
# SIGUSR1      10        User-defined 1
# SIGUSR2      12        User-defined 2

# Pseudo-segnali Bash (non sono veri segnali):
# EXIT         Eseguito quando lo script termina (qualsiasi motivo)
# ERR          Eseguito quando un comando fallisce (con set -e)
# DEBUG        Eseguito PRIMA di ogni comando
# RETURN       Eseguito al return da una funzione o source
```

### Pattern di Trap

```bash
# Pattern 1: Cleanup base con EXIT
tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT
# Lo script puo' terminare in qualsiasi modo — il cleanup avverra' sempre

# Pattern 2: Cleanup complesso con funzione
cleanup() {
    local exit_code=$?
    echo "Cleanup in corso..." >&2
    rm -rf "${WORK_DIR:-}"
    [[ -n "${PID:-}" ]] && kill "$PID" 2>/dev/null
    exit "$exit_code"    # Preserva l'exit code originale
}
trap cleanup EXIT

# Pattern 3: Gestione SIGINT per pulizia interattiva
trap 'echo -e "\nInterrotto. Pulizia..."; cleanup; exit 130' INT

# Pattern 4: Lock file per evitare esecuzioni concorrenti
LOCKFILE="/var/run/myscript.lock"
acquire_lock() {
    if ! mkdir "$LOCKFILE" 2>/dev/null; then
        echo "Script gia' in esecuzione (lockfile: $LOCKFILE)" >&2
        exit 1
    fi
    trap 'rm -rf "$LOCKFILE"' EXIT
}
acquire_lock

# Pattern 5: ERR trap per logging errori
on_error() {
    local exit_code=$?
    local line_no=$1
    echo "ERRORE alla riga $line_no (exit code: $exit_code)" >&2
    echo "Comando: ${BASH_COMMAND}" >&2
}
trap 'on_error ${LINENO}' ERR

# Pattern 6: DEBUG trap per tracing personalizzato
trace() {
    echo "[TRACE] ${BASH_SOURCE[1]}:${BASH_LINENO[0]} ${BASH_COMMAND}" >> /tmp/trace.log
}
trap trace DEBUG

# Pattern 7: RETURN trap per profiling funzioni
time_function() {
    echo "Funzione ${FUNCNAME[1]} completata in ${SECONDS}s"
}
# Dentro una funzione:
my_function() {
    local SECONDS=0
    trap time_function RETURN
    # ... logica ...
}

# Pattern 8: Trap multipli (concatenamento)
# Un nuovo trap SOSTITUISCE il precedente per lo stesso segnale.
# Per concatenare, salvare il trap precedente:
existing_trap=$(trap -p EXIT)
trap "nuovo_cleanup; ${existing_trap:-}" EXIT

# Pattern 9: Ignorare un segnale temporaneamente
trap '' INT              # Ignora Ctrl+C
critical_operation       # Non puo' essere interrotta
trap - INT               # Ripristina il comportamento default

# Vedere i trap attivi:
trap -p                  # Tutti
trap -p EXIT             # Solo EXIT
```

---

## Coprocessi

I coprocessi permettono a uno script di lanciare un processo in background e comunicare con esso bidirezionalmente tramite file descriptor.

```bash
# Sintassi base:
coproc NOME { comando; }

# Bash crea due file descriptor:
# ${NOME[0]} — leggi dall'output del coprocesso (stdout del coprocesso)
# ${NOME[1]} — scrivi all'input del coprocesso (stdin del coprocesso)
# $NOME_PID  — PID del coprocesso

# Esempio semplice:
coproc BC { bc -l; }
echo "scale=4; 22/7" >&"${BC[1]}"
read -r result <&"${BC[0]}"
echo "22/7 = $result"    # 3.1428

echo "sqrt(2)" >&"${BC[1]}"
read -r result <&"${BC[0]}"
echo "sqrt(2) = $result"   # 1.41421356237309504880

# Chiudere il coprocesso:
exec {BC[1]}>&-         # Chiudi stdin del coprocesso
wait "$BC_PID"          # Attendi la terminazione

# Esempio: coprocesso come server di calcolo
coproc CALC {
    while IFS= read -r expr; do
        echo "$expr" | bc -l 2>/dev/null || echo "ERRORE"
    done
}

calculate() {
    echo "$1" >&"${CALC[1]}"
    read -r result <&"${CALC[0]}"
    echo "$result"
}

calculate "2^10"           # 1024
calculate "s(3.14159/2)"   # ~1 (seno di pi/2)

exec {CALC[1]}>&-
wait "$CALC_PID"

# Esempio: coprocesso per interazione con un database
coproc SQLITE {
    sqlite3 -separator '|' /tmp/test.db
}

echo "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT);" >&"${SQLITE[1]}"
echo "INSERT INTO users VALUES (1, 'Mario');" >&"${SQLITE[1]}"
echo "SELECT * FROM users;" >&"${SQLITE[1]}"
read -r row <&"${SQLITE[0]}"
echo "Riga: $row"

echo ".quit" >&"${SQLITE[1]}"
wait "$SQLITE_PID"

# LIMITAZIONI:
# - Solo UN coprocesso senza nome alla volta (con nome si possono avere piu')
# - I file descriptor vengono chiusi quando il coprocesso termina
# - Il coprocesso gira in una subshell (non puo' modificare variabili della shell padre)
```

---

## Job Control Approfondito

```bash
# Job control gestisce i processi avviati dalla shell interattiva.
# Abilitato di default nelle shell interattive, disabilitato negli script.

# FONDAMENTALI:
command &               # Avvia in background (job)
Ctrl+Z                  # Sospendi il processo foreground (SIGTSTP)
jobs                    # Lista tutti i job
jobs -l                 # Con PID
jobs -p                 # Solo PID
fg %n                   # Porta job n in foreground
fg                      # Porta l'ultimo job in foreground
bg %n                   # Riprendi job n in background
bg                      # Riprendi l'ultimo job sospeso

# IDENTIFICAZIONE DEI JOB:
%1                      # Job numero 1
%+  o %%                # Job corrente (ultimo sospeso/in background)
%-                      # Job precedente
%string                 # Job il cui comando inizia con "string"
%?string                # Job il cui comando contiene "string"

# STATO DEI JOB:
# Running    — in esecuzione in background
# Stopped    — sospeso (Ctrl+Z o SIGSTOP)
# Done       — completato
# Terminated — terminato da un segnale

# WAIT — attendere uno o piu' job
command1 &
pid1=$!
command2 &
pid2=$!
wait "$pid1" "$pid2"    # Attendi entrambi
echo "Entrambi completati"

# wait -n (Bash 4.3+): attendi il PRIMO che termina
command_a &
command_b &
command_c &
wait -n                 # Ritorna quando uno qualsiasi termina
echo "Almeno uno completato"

# NOHUP — protegge il processo da SIGHUP (chiusura terminale)
nohup long_running_command &
# Output va in nohup.out se stdout non e' rediretto

# DISOWN — rimuove il job dalla job table della shell
long_command &
disown %1               # Shell non inviera' SIGHUP a questo processo
disown -h %1            # Marca per non ricevere SIGHUP ma resta nella job table
disown -a               # Disown tutti i job

# SETSID — avvia il processo in una nuova sessione
setsid long_command &   # Completamente indipendente dalla shell

# DIFFERENZE:
# nohup: ignora SIGHUP, redirige output
# disown: rimuove dalla job table della shell
# setsid: nuova sessione, nuovo process group
# Combinare per massima resilienza:
nohup setsid command > /dev/null 2>&1 &
disown

# Pattern: esecuzione parallela con limite di concorrenza
max_jobs=4
for file in /data/*.csv; do
    process_file "$file" &
    # Se abbiamo raggiunto il limite, attendi che uno finisca
    while [[ $(jobs -r -p | wc -l) -ge $max_jobs ]]; do
        wait -n
    done
done
wait    # Attendi tutti i rimanenti

# Pattern: timeout per un comando
timeout 30 long_command    # Termina dopo 30 secondi (coreutils)
# Oppure manualmente:
(
    sleep 30
    kill $$ 2>/dev/null
) &
watchdog_pid=$!
long_command
kill "$watchdog_pid" 2>/dev/null
```

---

## Text Processing: grep, sed, awk — Deep Dive

### grep: Ricerca Pattern

```bash
# GREP — ricerca pattern
grep "error" /var/log/syslog         # Cerca "error"
grep -i "error" file                 # Case-insensitive
grep -r "TODO" /src/                 # Ricorsivo
grep -n "pattern" file               # Mostra numeri di riga
grep -c "pattern" file               # Conta occorrenze
grep -v "debug" file                 # Inverti match (escludi debug)
grep -E "error|warning|critical" file  # Extended regex (OR)
grep -l "pattern" *.log              # Solo nomi file con match
grep -A3 -B2 "error" file           # 3 righe dopo, 2 prima

# Modalita' regex di grep:
# grep (BRE — Basic Regular Expressions):
#   . * ^ $ [ ] \( \) \{ \} \1-\9
#   + ? | ( ) devono essere escaped: \+ \? \| \( \)
grep 'error\|warning' file          # BRE: \| per OR
grep 'ab\+c' file                   # BRE: \+ per "1 o piu'"

# grep -E (ERE — Extended Regular Expressions):
#   . * ^ $ [ ] ( ) { } + ? |
#   NON serve escape per + ? | ( ) { }
grep -E 'error|warning' file        # ERE: | diretto
grep -E 'ab+c' file                 # ERE: + diretto

# grep -P (PCRE — Perl Compatible Regular Expressions):
#   Tutto ERE + lookahead, lookbehind, \d, \w, \s, ecc.
grep -P '\d{3}-\d{4}' file          # \d = digit
grep -P '\berror\b' file            # \b = word boundary
grep -P '(?<=user=)\w+' file        # Lookbehind: parola dopo "user="
grep -P '(?=.*error)(?=.*fatal)' f   # Lookahead: riga con entrambi

# grep -F (fgrep — stringa fissa, nessuna regex):
grep -F '*.txt' file                 # Cerca letteralmente "*.txt"
grep -F -f patterns.txt data.txt    # Cerca tutte le stringhe da un file

# Opzioni avanzate:
grep -o 'pattern' file               # Stampa SOLO la parte matchata
grep -w 'error' file                 # Match solo parola intera
grep -m 5 'pattern' file             # Ferma dopo 5 match
grep --color=always 'pat' file       # Colora i match
grep -Z 'pattern' file               # Output con null separator (per xargs -0)
grep -R --include='*.py' 'import' .  # Ricorsivo solo in file .py

# Esempi pratici avanzati:
# Trovare righe che matchano TUTTI i pattern (AND):
grep 'error' file | grep 'critical' | grep 'database'
# Oppure con PCRE lookahead:
grep -P '(?=.*error)(?=.*critical)(?=.*database)' file

# Estrarre indirizzi IP da un log:
grep -oP '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}' access.log

# Contare errori per tipo:
grep -oP 'ERROR:\s*\K\w+' app.log | sort | uniq -c | sort -rn
```

### sed: Stream Editor

```bash
# SED — stream editor
sed 's/vecchio/nuovo/' file          # Sostituisci prima occorrenza per riga
sed 's/vecchio/nuovo/g' file         # Sostituisci tutte le occorrenze
sed -i 's/vecchio/nuovo/g' file      # Modifica in-place
sed -n '10,20p' file                 # Stampa righe 10-20
sed '/pattern/d' file                # Cancella righe con pattern
sed '5i\testo inserito' file         # Inserisci alla riga 5
sed -n '/START/,/END/p' file         # Stampa blocco tra START e END

# INDIRIZZI (specificano DOVE applicare i comandi):
sed '5s/a/b/'                        # Solo riga 5
sed '5,10s/a/b/'                     # Righe 5-10
sed '5,$s/a/b/'                      # Dalla riga 5 alla fine
sed '/pattern/s/a/b/'                # Righe che contengono "pattern"
sed '/start/,/end/s/a/b/'            # Range definito da pattern
sed '0~2s/a/b/'                      # Ogni 2 righe (pari) — GNU sed
sed '1~2s/a/b/'                      # Ogni 2 righe (dispari) — GNU sed
sed '5!s/a/b/'                       # Tutte TRANNE riga 5

# COMANDI sed:
# s/old/new/flags  — sostituzione
# d                — cancella riga
# p                — stampa riga (usare con -n)
# i\text           — inserisci prima della riga
# a\text           — aggiungi dopo la riga
# c\text           — sostituisci l'intera riga
# y/abc/xyz/       — translittera (come tr)
# q                — quit (ferma l'elaborazione)
# r filename       — leggi e inserisci il contenuto del file
# w filename       — scrivi la riga matchata nel file

# Flag di sostituzione:
# g    — tutte le occorrenze nella riga
# I    — case-insensitive (GNU sed)
# p    — stampa la riga se c'e' stata sostituzione
# w    — scrivi la riga modificata in un file
# N    — sostituisci solo la N-esima occorrenza
sed 's/old/new/2'                    # Solo la seconda occorrenza
sed 's/old/new/gI'                   # Tutte, case-insensitive

# Delimitatori alternativi (utile con path):
sed 's|/usr/local|/opt|g'
sed 's#http://#https://#g'

# HOLD SPACE e PATTERN SPACE:
# sed ha due buffer:
#   pattern space — la riga corrente in elaborazione
#   hold space   — buffer ausiliario (inizia vuoto)
#
# Comandi per manipolarli:
# h    — copia pattern space → hold space
# H    — AGGIUNGI pattern space → hold space
# g    — copia hold space → pattern space
# G    — AGGIUNGI hold space → pattern space
# x    — scambia pattern space e hold space

# Esempio: invertire l'ordine delle righe (come tac):
sed -n '1!G;h;$p' file

# Spiegazione:
# 1!G  — per tutte le righe TRANNE la prima: aggiungi hold al pattern
# h    — copia pattern nello hold
# $p   — all'ultima riga: stampa

# Esempio: unire coppie di righe:
sed 'N;s/\n/ /' file
# N — aggiungi la prossima riga al pattern space (con \n tra le due)
# s/\n/ / — sostituisci il newline con spazio

# Esempio: stampare solo le righe tra due pattern (esclusi):
sed -n '/START/,/END/{/START/d;/END/d;p}' file

# Esempio: eliminare righe vuote consecutive (squeeze blank lines):
sed '/^$/N;/^\n$/d' file

# Esempio: aggiungere numero di riga:
sed '=' file | sed 'N;s/\n/\t/'

# sed multi-command:
sed -e 's/foo/bar/g' -e 's/baz/qux/g' file
# Oppure con punto e virgola (GNU sed):
sed 's/foo/bar/g;s/baz/qux/g' file
# Oppure con blocco:
sed '{
    s/foo/bar/g
    s/baz/qux/g
    /comment/d
}' file

# sed con gruppi di cattura:
echo "2026-05-22" | sed -E 's/([0-9]{4})-([0-9]{2})-([0-9]{2})/\3\/\2\/\1/'
# Output: 22/05/2026

# NOTA: -E = ERE (come grep -E). Senza -E, usare \( \) per i gruppi.
```

### awk: Linguaggio di Programmazione per Testo

```bash
# AWK — processamento colonnare
awk '{print $1, $3}' file            # Stampa colonne 1 e 3
awk -F: '{print $1}' /etc/passwd     # Delimitatore ':'
awk '$3 > 100' file                  # Righe dove colonna 3 > 100
awk '{sum+=$1} END{print sum}' file  # Somma colonna 1
awk 'NR==5,NR==10' file              # Righe 5-10

# VARIABILI PREDEFINITE:
# NR    — numero riga corrente (globale)
# NF    — numero di campi nella riga corrente
# $0    — l'intera riga corrente
# $1-$N — singoli campi
# FS    — Field Separator (input)
# OFS   — Output Field Separator
# RS    — Record Separator (default: newline)
# ORS   — Output Record Separator
# FILENAME — nome del file corrente
# FNR   — numero riga nel file corrente (resettato per ogni file)

# STRUTTURA DI UN PROGRAMMA AWK:
awk '
    BEGIN { azione_iniziale }
    /pattern/ { azione_per_riga }
    END { azione_finale }
' file

# Esempio: report con intestazione e totale
awk -F: '
    BEGIN {
        printf "%-20s %-6s %s\n", "UTENTE", "UID", "SHELL"
        print "----------------------------------------"
    }
    $3 >= 1000 && $7 !~ /nologin|false/ {
        printf "%-20s %-6d %s\n", $1, $3, $7
        count++
    }
    END {
        print "----------------------------------------"
        printf "Totale utenti attivi: %d\n", count
    }
' /etc/passwd

# ARRAY ASSOCIATIVI IN AWK:
# Contare occorrenze:
awk '{count[$1]++} END {for (k in count) print count[k], k}' file | sort -rn

# Sommare per categoria:
awk -F, '{total[$2] += $3} END {for (cat in total) print cat, total[cat]}' sales.csv

# Array multidimensionali (simulati):
awk '{data[$1,$2] = $3} END {for (key in data) print key, data[key]}' file

# FUNZIONI PREDEFINITE:
# Stringhe: length(), substr(), index(), split(), sub(), gsub(), match(), tolower(), toupper(), sprintf()
# Matematiche: sin(), cos(), sqrt(), exp(), log(), int(), rand(), srand()
# I/O: getline, system(), print, printf

# sub() e gsub():
awk '{sub(/vecchio/, "nuovo"); print}' file     # Prima occorrenza
awk '{gsub(/vecchio/, "nuovo"); print}' file    # Tutte

# split():
awk '{n = split($0, parts, ":"); for (i=1; i<=n; i++) print parts[i]}' file

# getline — leggere da file o comandi:
awk '{
    while ((getline line < "other_file.txt") > 0) {
        print line
    }
    close("other_file.txt")
}' input.txt

# getline da un comando:
awk '{
    cmd = "date +%s"
    cmd | getline timestamp
    close(cmd)
    print timestamp, $0
}' file

# FUNZIONI DEFINITE DALL'UTENTE:
awk '
    function max(a, b) { return (a > b) ? a : b }
    function min(a, b) { return (a < b) ? a : b }
    function trim(s)   { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
    { print max($1, $2), min($1, $2), trim($3) }
' file

# Esempio complesso: analisi log Apache
awk '
    {
        ip = $1
        status = $9
        bytes = $10
        url = $7

        hits[ip]++
        if (status >= 400) errors[ip]++
        if (bytes != "-") traffic[ip] += bytes
    }
    END {
        printf "%-18s %8s %8s %12s\n", "IP", "Hits", "Errors", "Traffic(MB)"
        for (ip in hits) {
            printf "%-18s %8d %8d %12.2f\n",
                ip, hits[ip], errors[ip]+0, traffic[ip]/1024/1024
        }
    }
' access.log | sort -t$'\t' -k2 -rn | head -20

# COMBINAZIONI POTENTI
# Top 10 IP per accessi (access log Apache/Nginx)
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10

# Spazio disco usato per directory, ordinato
du -sh /var/*/ 2>/dev/null | sort -rh | head -10

# Utenti con shell di login
awk -F: '$7 !~ /nologin|false/ {print $1, $7}' /etc/passwd

# Sostituire in tutti i file di configurazione
find /etc -name "*.conf" -exec sed -i 's/old_value/new_value/g' {} \;
```

### Strumenti Complementari

```bash
# cut — estrarre colonne
cut -d: -f1,3 /etc/passwd           # Campi 1 e 3, delimitatore ':'
cut -c1-10 file                      # Caratteri 1-10

# tr — translitterazione
tr 'a-z' 'A-Z' < file               # Minuscolo → maiuscolo
tr -d '\r' < windows.txt             # Rimuovere carriage return
tr -s ' '                            # Squeeze: spazi multipli → singolo

# sort + uniq — combinazione classica
sort file | uniq -c | sort -rn       # Conta e ordina per frequenza
sort -t, -k3 -n file                 # Ordina per terzo campo numerico

# paste — unire file fianco a fianco
paste file1 file2                    # Colonne affiancate con tab
paste -d',' -s file                  # Tutte le righe in una riga, separate da virgola

# column — formattazione tabellare
column -t -s, file.csv               # Allinea colonne CSV

# tee — duplica output
command | tee output.log             # Stdout + file
command | tee -a output.log          # Stdout + append file
command | tee >(grep error > err.log) >(grep warn > warn.log) > /dev/null

# xargs — costruire comandi da stdin
find . -name "*.tmp" -print0 | xargs -0 rm -f
echo "a b c" | xargs -n1 echo       # Un argomento per invocazione
cat urls.txt | xargs -P4 -I{} curl -sO {}   # 4 download paralleli
```

---

## Regex e Pattern Matching — Masterclass

```bash
# REGEX BASE (grep, sed senza -E)
.       # Qualsiasi carattere singolo
^       # Inizio riga
$       # Fine riga
*       # 0 o più del precedente
[]      # Character class [abc], [a-z], [0-9]
[^]     # Negazione [^abc] = non a,b,c
\       # Escape carattere speciale

# REGEX ESTESE (grep -E, egrep, awk)
+       # 1 o più del precedente
?       # 0 o 1 del precedente
{n}     # Esattamente n ripetizioni
{n,m}   # Da n a m ripetizioni
|       # OR
()      # Raggruppamento

# ESEMPI PRATICI
grep -E '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' file  # IP address
grep -E '^\s*#' file                    # Righe di commento
grep -E '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' file   # Email

# GLOB (shell pattern matching, non regex)
ls *.txt              # Tutti i .txt
ls file?.txt          # file1.txt, fileA.txt
ls file[0-9].txt      # file0.txt ... file9.txt
ls **/*.py            # Ricorsivo (con shopt -s globstar)
```

### Character Classes POSIX e Shorthand

```bash
# Character classes POSIX (dentro [...]):
[:alnum:]    # Alfanumerici: [a-zA-Z0-9]
[:alpha:]    # Lettere: [a-zA-Z]
[:digit:]    # Cifre: [0-9]
[:lower:]    # Minuscole: [a-z]
[:upper:]    # Maiuscole: [A-Z]
[:space:]    # Spazi: [ \t\n\r\f\v]
[:blank:]    # Spazio e tab: [ \t]
[:punct:]    # Punteggiatura
[:print:]    # Stampabili (include spazio)
[:graph:]    # Stampabili (esclude spazio)
[:cntrl:]    # Caratteri di controllo
[:xdigit:]   # Esadecimali: [0-9a-fA-F]

# Uso: DOPPIA parentesi quadra
grep '[[:upper:]]' file              # Righe con almeno una maiuscola
grep '^[[:space:]]*$' file           # Righe vuote o solo spazi
grep '[[:digit:]]\{3\}' file         # Tre cifre consecutive (BRE)

# Shorthand PCRE (grep -P):
\d   # Digit [0-9]           \D  # Non-digit
\w   # Word  [a-zA-Z0-9_]    \W  # Non-word
\s   # Space [ \t\n\r\f\v]   \S  # Non-space
\b   # Word boundary          \B  # Non-word-boundary
```

### Anchors e Boundaries

```bash
# Anchors:
^        # Inizio riga (o stringa in modalita' multilinea)
$        # Fine riga
\b       # Word boundary (PCRE / ERE in alcune implementazioni)
\B       # Non-word-boundary
\<       # Inizio parola (GNU grep/sed)
\>       # Fine parola (GNU grep/sed)
\A       # Inizio stringa assoluto (PCRE)
\Z       # Fine stringa assoluto (PCRE, prima dell'ultimo \n)
\z       # Fine stringa assoluto (PCRE, dopo l'ultimo \n)

# Esempi:
grep '\berror\b' file                # "error" come parola intera
grep '\<error\>' file                # Stesso risultato (GNU)
grep -w 'error' file                 # Stesso risultato (opzione grep)
grep -P '^\d+$' file                 # Righe composte solo da cifre
```

### Quantificatori

```bash
# Quantificatori greedy (matchano il PIU' possibile):
*        # 0 o piu'
+        # 1 o piu'
?        # 0 o 1
{n}      # Esattamente n
{n,}     # n o piu'
{n,m}    # Da n a m

# Quantificatori lazy (matchano il MENO possibile — PCRE):
*?       # 0 o piu' (lazy)
+?       # 1 o piu' (lazy)
??       # 0 o 1 (lazy)
{n,m}?   # Da n a m (lazy)

# Esempio greedy vs lazy:
echo '<b>bold</b> and <i>italic</i>' | grep -oP '<.*>'
# Output: <b>bold</b> and <i>italic</i>   (greedy: match piu' lungo)

echo '<b>bold</b> and <i>italic</i>' | grep -oP '<.*?>'
# Output: <b>  </b>  <i>  </i>             (lazy: match piu' corti)

# Quantificatori possessivi (PCRE, non backtrackano):
*+       # 0 o piu' (possessive)
++       # 1 o piu' (possessive)
# Piu' efficienti quando sai che il backtracking non servira'.
```

### Gruppi e Backreference

```bash
# Gruppi di cattura:
echo "2026-05-22" | grep -oP '(\d{4})-(\d{2})-(\d{2})'

# Backreference (riferimento a un gruppo catturato):
# \1, \2, ... in BRE/ERE (sed, grep)
# $1, $2, ... in PCRE replacement

# Trovare parole duplicate:
grep -P '\b(\w+)\s+\1\b' file       # "the the", "is is", ecc.

# sed con backreference:
echo "Mario Rossi" | sed -E 's/^(\w+) (\w+)$/\2, \1/'
# Output: Rossi, Mario

# Gruppi non catturanti (PCRE) — non creano backreference:
grep -P '(?:error|warning): (.+)' file
# (?:...) non salva il match, (.) si' → \1 e' il messaggio, non error/warning

# Gruppi con nome (PCRE):
grep -P '(?<year>\d{4})-(?<month>\d{2})-(?<day>\d{2})' file
# In sostituzione: ${year}, ${month}, ${day}
echo "2026-05-22" | perl -pe 's/(?<y>\d{4})-(?<m>\d{2})-(?<d>\d{2})/$+{d}\/$+{m}\/$+{y}/'
```

### Lookahead e Lookbehind (PCRE)

```bash
# Asserzioni lookaround: matchano una POSIZIONE, non consumano caratteri.

# Lookahead positivo: (?=pattern)  — "seguito da pattern"
grep -P '\d+(?= euro)' file         # Cifre seguite da " euro"
# "100 euro" → matcha "100"

# Lookahead negativo: (?!pattern)  — "NON seguito da pattern"
grep -P '\d+(?! euro)' file         # Cifre NON seguite da " euro"

# Lookbehind positivo: (?<=pattern) — "preceduto da pattern"
grep -P '(?<=prezzo: )\d+' file     # Cifre precedute da "prezzo: "
# "prezzo: 100" → matcha "100"

# Lookbehind negativo: (?<!pattern) — "NON preceduto da pattern"
grep -P '(?<!un)known' file         # "known" non preceduto da "un"

# Esempio: estrarre valori da key=value senza catturare la chiave
grep -oP '(?<=password=)\S+' config.txt

# Esempio: trovare funzioni non precedute da commento
grep -P '(?<!#.*)def \w+' script.py

# LIMITAZIONE: i lookbehind devono avere lunghezza fissa nella maggior parte
# delle implementazioni. \K e' un'alternativa piu' flessibile in PCRE:
grep -oP 'user=\K\w+' file          # \K resetta l'inizio del match
# "user=mario" → matcha "mario" (come lookbehind ma senza limiti di lunghezza)
```

---

## Tmux — Deep Dive

```bash
# TMUX — terminal multiplexer
tmux                              # Nuova sessione
tmux new -s nome                  # Nuova sessione con nome
tmux ls                           # Lista sessioni
tmux attach -t nome               # Riconnetti a sessione
tmux kill-session -t nome         # Termina sessione

# COMANDI TMUX (prefix: Ctrl+b)
Ctrl+b c          # Nuova finestra
Ctrl+b n/p        # Finestra successiva/precedente
Ctrl+b %          # Split verticale
Ctrl+b "          # Split orizzontale
Ctrl+b arrow      # Naviga tra pane
Ctrl+b d          # Detach (torna alla shell, sessione resta attiva)
Ctrl+b z          # Zoom pane (toggle fullscreen)
Ctrl+b [          # Scroll mode (q per uscire)
Ctrl+b :resize-pane -D 10  # Ridimensiona pane

# ~/.tmux.conf — configurazione
set -g mouse on                   # Abilita mouse
set -g history-limit 50000        # History più grande
set -g base-index 1               # Finestre da 1 (non 0)
set -g default-terminal "screen-256color"
bind r source-file ~/.tmux.conf   # Prefix+r ricarica config
```

### Gestione Sessioni e Windows

```bash
# Sessioni:
tmux new-session -d -s dev         # Crea sessione detached
tmux new-session -d -s dev -n editor  # Con finestra chiamata "editor"
tmux rename-session -t 0 main     # Rinomina sessione
tmux switch-client -t dev         # Passa a un'altra sessione
tmux kill-server                   # Termina TUTTE le sessioni

# Dentro tmux (dopo il prefix Ctrl+b):
:new-session -s nome              # Nuova sessione dal command mode
s                                  # Lista sessioni interattiva
$                                  # Rinomina sessione corrente
(  )                               # Sessione precedente/successiva

# Finestre:
Ctrl+b c                          # Nuova finestra
Ctrl+b ,                          # Rinomina finestra
Ctrl+b w                          # Lista finestre interattiva
Ctrl+b 0-9                        # Vai alla finestra N
Ctrl+b &                          # Chiudi finestra (con conferma)
Ctrl+b f                          # Trova finestra per nome

# Pane:
Ctrl+b %                          # Split verticale
Ctrl+b "                          # Split orizzontale
Ctrl+b o                          # Prossimo pane
Ctrl+b ;                          # Ultimo pane attivo
Ctrl+b q                          # Mostra numeri pane (premi il numero per selezionare)
Ctrl+b x                          # Chiudi pane corrente
Ctrl+b {  }                       # Sposta pane sinistra/destra
Ctrl+b !                          # Converti pane in finestra
Ctrl+b space                      # Cambia layout

# Ridimensionare pane:
Ctrl+b :resize-pane -U 5          # Su di 5 righe
Ctrl+b :resize-pane -D 5          # Giu' di 5 righe
Ctrl+b :resize-pane -L 10         # Sinistra di 10 colonne
Ctrl+b :resize-pane -R 10         # Destra di 10 colonne
# Con mouse (se abilitato): trascina il bordo
```

### Copy Mode e Scroll

```bash
# Ctrl+b [ — entra in copy mode (scroll, ricerca, selezione)
# q — esci dal copy mode

# In copy mode (emacs keys di default):
# Ctrl+S      Cerca avanti
# Ctrl+R      Cerca indietro
# Space       Inizia selezione
# Enter       Copia selezione
# Ctrl+b ]    Incolla

# Per vi keys in copy mode:
set-window-option -g mode-keys vi

# In copy mode (vi keys):
# /           Cerca avanti
# ?           Cerca indietro
# v           Inizia selezione (con bind personalizzato)
# y           Copia (con bind personalizzato)

# Bind per vi-style copy:
# bind-key -T copy-mode-vi v send-keys -X begin-selection
# bind-key -T copy-mode-vi y send-keys -X copy-pipe-and-cancel "xclip -selection clipboard"
```

### Scripting Tmux

```bash
# Creare un ambiente di sviluppo completo con uno script:

#!/bin/bash
SESSION="dev"

# Crea la sessione se non esiste
tmux has-session -t "$SESSION" 2>/dev/null && {
    tmux attach -t "$SESSION"
    exit 0
}

tmux new-session -d -s "$SESSION" -n "editor" -c ~/progetto

# Finestra 1: editor
tmux send-keys -t "$SESSION:editor" 'vim .' C-m

# Finestra 2: server
tmux new-window -t "$SESSION" -n "server" -c ~/progetto
tmux send-keys -t "$SESSION:server" 'npm run dev' C-m

# Finestra 3: terminali affiancati
tmux new-window -t "$SESSION" -n "term" -c ~/progetto
tmux split-window -h -t "$SESSION:term" -c ~/progetto
tmux split-window -v -t "$SESSION:term.1" -c ~/progetto

# Finestra 4: log
tmux new-window -t "$SESSION" -n "logs" -c ~/progetto
tmux send-keys -t "$SESSION:logs" 'tail -f /var/log/syslog' C-m

# Seleziona la prima finestra
tmux select-window -t "$SESSION:editor"

# Attach
tmux attach -t "$SESSION"
```

### Configurazione Avanzata ~/.tmux.conf

```bash
# ~/.tmux.conf

# Prefix: cambio da Ctrl+b a Ctrl+a (opinionale, stile screen)
# unbind C-b
# set -g prefix C-a
# bind C-a send-prefix

# True color
set -g default-terminal "tmux-256color"
set -ag terminal-overrides ",xterm-256color:RGB"

# Tempi
set -sg escape-time 0              # Nessun ritardo dopo ESC
set -g display-time 4000           # Messaggi visibili 4 secondi
set -g history-limit 50000         # Buffer di scroll grande

# Indici
set -g base-index 1                # Finestre da 1
setw -g pane-base-index 1          # Pane da 1
set -g renumber-windows on         # Rinumera dopo chiusura

# Mouse
set -g mouse on

# Vi mode
setw -g mode-keys vi
set -g status-keys vi

# Split intuitivi
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
unbind '"'
unbind %

# Nuova finestra nel path corrente
bind c new-window -c "#{pane_current_path}"

# Navigazione pane stile vim
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Ridimensionamento pane
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5

# Ricarica configurazione
bind r source-file ~/.tmux.conf \; display "Configurazione ricaricata"

# Status bar
set -g status-position top
set -g status-interval 5
set -g status-left-length 40
set -g status-right-length 60
set -g status-left '#[fg=green]#S #[fg=yellow]#I:#P '
set -g status-right '#[fg=cyan]%H:%M #[fg=white]%d-%b-%Y'
```

### Plugin Tmux (TPM)

```bash
# TPM — Tmux Plugin Manager
# Installazione:
# git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

# In ~/.tmux.conf:
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-sensible'       # Impostazioni ragionevoli
set -g @plugin 'tmux-plugins/tmux-resurrect'       # Salva/ripristina sessioni
set -g @plugin 'tmux-plugins/tmux-continuum'       # Auto-save sessioni
set -g @plugin 'tmux-plugins/tmux-yank'            # Copia negli appunti di sistema

# Configurazione tmux-resurrect:
set -g @resurrect-capture-pane-contents 'on'
set -g @resurrect-strategy-vim 'session'

# Configurazione tmux-continuum:
set -g @continuum-restore 'on'
set -g @continuum-save-interval '15'               # Salva ogni 15 minuti

# Inizializzazione TPM (deve essere l'ultima riga):
run '~/.tmux/plugins/tpm/tpm'

# Installare plugin: prefix + I
# Aggiornare plugin: prefix + U
# Rimuovere plugin: prefix + Alt+u
```

---

## Shell Debugging

### set -x e PS4

```bash
# set -x (xtrace): stampa ogni comando prima dell'esecuzione
# Ogni riga debug e' prefissata da PS4 (default: "+ ")

set -x
echo "hello"
# Output:
# + echo hello
# hello
set +x

# PS4 personalizzato per debugging informativo:
export PS4='+${BASH_SOURCE[0]##*/}:${LINENO}: ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'
# Output: +script.sh:42: my_function(): echo hello

# Abilitare debug solo per una sezione:
set -x
  codice_da_debuggare
set +x

# Abilitare debug solo per una subshell:
(
    set -x
    codice_da_debuggare
)

# Debug output a un file (senza inquinare stderr):
exec 19>/tmp/debug.log
BASH_XTRACEFD=19
set -x
# ... debug ...
set +x
exec 19>&-

# Abilitare dal comando:
bash -x script.sh              # Debug dall'inizio
bash -xv script.sh             # -v: stampa anche le righe prima dell'espansione
```

### Tecniche di Debugging

```bash
# 1. Echo strategico:
debug() {
    [[ "${DEBUG:-0}" == "1" ]] && echo "[DEBUG] $*" >&2
}
# Uso: DEBUG=1 ./script.sh

# 2. Stampa variabili con declare -p:
declare -p var                   # Mostra tipo, attributi e valore
declare -p arr                   # Mostra array con tutti gli elementi
# Output: declare -a arr=([0]="a" [1]="b" [2]="c")

# 3. Tracing con trap DEBUG:
trap 'echo "[TRACE] $BASH_COMMAND (line $LINENO)"' DEBUG
# Stampa OGNI comando prima dell'esecuzione

# 4. Stack trace su errore:
stacktrace() {
    local i=0
    echo "=== Stack trace ===" >&2
    while caller $i; do
        ((i++))
    done 2>/dev/null >&2
    echo "===================" >&2
}
trap 'stacktrace' ERR

# 5. caller builtin:
caller 0        # Riga e file del chiamante corrente
caller 1        # Riga e file del chiamante del chiamante
# Output: 42 my_function script.sh

# 6. Variabili di debug Bash:
echo "BASH_SOURCE: ${BASH_SOURCE[*]}"    # Stack dei file source
echo "FUNCNAME:    ${FUNCNAME[*]}"       # Stack delle funzioni
echo "BASH_LINENO: ${BASH_LINENO[*]}"    # Stack dei numeri di riga
echo "LINENO:      $LINENO"              # Riga corrente
echo "BASH_COMMAND: $BASH_COMMAND"       # Comando in esecuzione

# 7. Verificare la sintassi senza eseguire:
bash -n script.sh               # Controlla solo la sintassi

# 8. shellcheck — analisi statica:
shellcheck script.sh            # Trova bug, bad practice, portabilita'
shellcheck -s bash script.sh    # Specifica la shell
shellcheck -e SC2086 script.sh  # Escludi un warning specifico
# SC2086: "Double quote to prevent globbing and word splitting"
```

### bashdb — Debugger Interattivo

```bash
# Installazione:
# sudo apt install bashdb    # Debian/Ubuntu

# Uso:
bashdb script.sh

# Comandi principali (simili a gdb):
# n (next)      — esegui la prossima riga
# s (step)      — entra nella funzione
# c (continue)  — continua l'esecuzione
# b N           — breakpoint alla riga N
# p expr        — stampa il valore di expr
# x expr        — esamina (come declare -p)
# l             — lista il codice sorgente
# bt            — backtrace (stack trace)
# q             — esci

# Breakpoint condizionale:
# b 42 if x > 10     — ferma alla riga 42 solo se x > 10
```

---

## Zsh e Fish

### Zsh

```bash
# Installare e configurare Zsh
sudo apt install zsh
chsh -s $(which zsh)              # Imposta come shell di default

# Oh-My-Zsh (framework di configurazione)
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# ~/.zshrc — plugin essenziali
plugins=(git docker kubectl zsh-autosuggestions zsh-syntax-highlighting)

# Zsh-autosuggestions: suggerisce comandi dalla history
# Zsh-syntax-highlighting: colora i comandi validi/invalidi

# Feature esclusive Zsh:
# - Globbing avanzato: ls **/*(.) → solo file ricorsivi
# - Auto-cd: digita una directory → cd automatico
# - Spell correction: "gti status" → "git status? [nyae]"
# - Right-side prompt: RPROMPT mostra info a destra
```

### Differenze Zsh vs Bash per Scripting

```bash
# Gli array in Zsh partono da 1 (non 0 come in Bash):
arr=(a b c)
echo "${arr[1]}"    # Zsh: "a"   Bash: errore o vuoto (arr[0] = "a" in Bash)

# Zsh non fa word splitting di default sulle espansioni:
var="a b c"
for x in $var; do echo "$x"; done
# Zsh: una iterazione ("a b c")
# Bash: tre iterazioni ("a", "b", "c")

# Globbing avanzato Zsh (qualifiers):
ls *(.)              # Solo file regolari
ls *(/)              # Solo directory
ls *(.m-1)           # File modificati nelle ultime 24h
ls *(Lk+100)         # File > 100KB
ls *(om[1,5])        # 5 file piu' recenti
```

### Fish

```bash
# Fish shell: user-friendly out of the box
sudo apt install fish
# Autosuggestions, syntax highlighting, completions avanzate
# Sintassi diversa da Bash (non POSIX-compatible)
# Ideale per uso interattivo, meno per scripting di sistema
```

---

## Best Practices

1. **`set -euo pipefail` in ogni script**: previene errori silenziosi
2. **Quotare sempre le variabili**: `"$var"` non `$var` — previene word splitting e globbing
3. **Usare `[[ ]]` non `[ ]`**: meno gotcha, supporta regex e globbing
4. **Trap per cleanup**: ogni script che crea file temporanei deve avere `trap cleanup EXIT`
5. **Logging**: ogni script non banale deve loggare con timestamp
6. **ShellCheck**: `shellcheck script.sh` per trovare errori e bad practice prima di eseguire
7. **Tmux su ogni server remoto**: mai lavorare su SSH senza tmux — previene la perdita del lavoro su disconnessione
8. **Usare `readonly` per costanti**: `readonly MAX_RETRIES=3` previene modifiche accidentali
9. **Usare `local` nelle funzioni**: previene inquinamento del namespace globale
10. **Evitare eval**: quasi sempre esiste un'alternativa piu' sicura
11. **Preferire `$(cmd)` a `` `cmd` ``**: annidabile, leggibile, meno errori
12. **Non parsare l'output di `ls`**: usare glob o `find -print0 | while read -r -d ''`
13. **Gestire nomi file con spazi**: quotare sempre, usare `"$@"`, usare `-print0`/`-0`
14. **Usare `mktemp` per file temporanei**: `mktemp /tmp/script.XXXXXX` è sicuro, `/tmp/miofile` no
15. **Script idempotenti**: lo script puo' essere eseguito piu' volte senza effetti collaterali

---

## Troubleshooting

**"Lo script funziona interattivamente ma non in cron"** → Cron ha un environment minimale. Cause: PATH non include il binario, variabili d'ambiente mancanti. Fix: usare path assoluti, definire PATH nello script, `source /etc/profile` all'inizio.

**"Lo script si blocca leggendo un file"** → Il file potrebbe non avere newline finale. Usare `while IFS= read -r line || [[ -n "$line" ]]` per gestire l'ultima riga senza newline.

**"Errori con spazi nei nomi file"** → Non quotare le variabili: `for f in $files` espande male. Fix: `for f in "${files[@]}"` oppure `find ... -print0 | while IFS= read -r -d '' file`.

**"sed non funziona con path contenenti /"** → Usare un delimitatore diverso: `sed "s|/old/path|/new/path|g"` (pipe `|` anziché slash).

**"La variabile nel while-loop con pipe non viene aggiornata"** → Ogni comando in una pipe gira in una subshell. Le variabili modificate nella subshell non sono visibili nel processo padre. Fix: usare redirezione (`while ... done < file`) o process substitution (`while ... done < <(cmd)`).

**"set -e non cattura l'errore in command substitution"** → `var=$(false)` causa l'exit, ma `var=$(false) || true` no. Inoltre, `local var=$(false)` non causa l'exit perche' `local` restituisce 0. Fix: separare dichiarazione e assegnamento: `local var; var=$(false)`.

**"Lo script termina con 'unbound variable' in una condizione"** → Con `set -u`, testare una variabile che potrebbe non esistere causa errore. Fix: usare `${var:-}` oppure `${var+x}` per il test.

**"Differenza tra `2>&1 >file` e `>file 2>&1`"** → Le redirezioni sono processate da sinistra a destra. `2>&1 >file`: prima stderr va dove stdout andava (terminale), poi stdout va al file. Risultato: stderr al terminale, stdout al file. `>file 2>&1`: prima stdout va al file, poi stderr va dove stdout va (file). Risultato: entrambi al file.

**"getopts non funziona dopo argomenti posizionali"** → `getopts` si ferma al primo argomento non-opzione. Fix: mettere le opzioni PRIMA degli argomenti posizionali, oppure usare `getopt` (GNU) che permette riordino.

**"Il mio script Bash funziona ma shellcheck mostra errori"** → Shellcheck è quasi sempre corretto. I warning piu' comuni: SC2086 (quotare variabili), SC2046 (quotare command substitution), SC2006 (usare $() invece di backtick). Fix: seguire i suggerimenti di shellcheck — ogni warning previene un bug potenziale.

**"Lo script non trova i comandi dopo aver cambiato PATH"** → `export PATH` propaga ai processi figli ma non alle shell gia' aperte. Fix: `hash -r` per resettare la cache degli eseguibili nella shell corrente, oppure riaprire il terminale.

**"Here document non espande le variabili"** → Il delimitatore è quotato: `<<'EOF'` disabilita le espansioni. Fix: usare `<<EOF` senza quote per abilitare l'espansione di variabili.

**"L'array ha buchi dopo unset"** → `unset 'arr[3]'` rimuove l'elemento ma NON rinumera gli indici. L'array diventa sparso. Fix: ricostruire l'array `arr=("${arr[@]}")` oppure iterare con `"${arr[@]}"` invece di indici sequenziali.

**"Lo script funziona con bash ma non con sh"** → `sh` potrebbe essere dash (Debian/Ubuntu), che non supporta `[[ ]]`, array, `{1..10}`, `<()`, ecc. Fix: usare `#!/bin/bash` nello shebang, non `#!/bin/sh`. Se serve compatibilita' POSIX, evitare le bashisms.

**"Il comando in background non scrive nel file di log"** → stdout potrebbe essere bufferizzato. Fix: `stdbuf -oL command &` per line-buffered output, oppure usare `script -c command log.txt` per forzare un pseudo-terminale.

**"Il processo zombie non va via con kill"** → Un processo zombie è gia' terminato; sta aspettando che il padre chiami `wait()`. Fix: `kill` non funziona — uccidere il processo PADRE, oppure attendere che il padre faccia wait. `kill -SIGCHLD <ppid>` puo' sollecitare il padre.

**"read -r non legge correttamente le righe con backslash"** → Senza `-r`, read interpreta `\` come escape. Con `-r`, le legge letteralmente. Se ancora non funziona, verificare che `IFS` non sia stato modificato: `IFS= read -r line` preserva spazi iniziali/finali.

**"Lo script crea file con ^M (carriage return)"** → Il file sorgente ha line endings Windows (CRLF). Fix: `dos2unix script.sh` oppure `sed -i 's/\r$//' script.sh`. Aggiungere `#!/bin/bash` senza BOM.

**"trap EXIT non esegue il cleanup quando uso kill -9"** → SIGKILL (9) e SIGSTOP (19) non possono essere catturati da trap. Non esiste workaround. Fix: non usare `kill -9` a meno che sia necessario; preferire `kill -TERM` (15) che permette il cleanup.

**"Il completamento tab non funziona per il mio script"** → Bash non ha completamenti personalizzati di default. Fix: creare un file di completamento con `complete -F _my_function my_command` e metterlo in `/etc/bash_completion.d/` o source da `.bashrc`.

**"Lo script è lentissimo con molti file"** → Probabile uso di comandi esterni in un loop stretto (fork per ogni iterazione). Fix: preferire costrutti builtin (`[[ ]]` vs `test`, `${var//pat/repl}` vs `sed`, `read` vs `cat`) e strumenti che processano tutto in un passo (awk, sed su file intero).

---

## FAQ

**D1: Qual è la differenza tra `.bash_profile` e `.bashrc`?**
R: `.bash_profile` viene letto dalle login shell (SSH, console, `bash -l`). `.bashrc` viene letto dalle shell interattive non-login (nuovo terminale in GUI). Best practice: mettere tutta la configurazione in `.bashrc` e fare `source ~/.bashrc` da `.bash_profile`.

**D2: Perche' `set -e` non ferma lo script quando il comando fallisce in un if?**
R: Per design. `set -e` non si applica ai comandi il cui exit status è testato esplicitamente: `if cmd`, `cmd && other`, `cmd || other`, `while cmd`. Questo è intenzionale — altrimenti non potresti scrivere condizioni.

**D3: Quando usare `[ ]` e quando `[[ ]]`?**
R: Usare sempre `[[ ]]` in Bash. È piu' sicuro (niente word splitting), supporta `&&`/`||` direttamente, supporta regex (`=~`), supporta pattern matching. Usare `[ ]` solo in script POSIX che devono girare con `sh`.

**D4: Come si passa un array come argomento a una funzione?**
R: Gli array non si passano direttamente. Opzioni: (1) passare gli elementi: `func "${arr[@]}"` e riceverli con `"$@"`; (2) passare il nome e usare nameref: `local -n ref=$1`; (3) passare come stringa delimitata.

**D5: Perche' `local var=$(false)` non causa un errore con `set -e`?**
R: Perche' `local` è un comando e il suo exit code (sempre 0) sovrascrive quello di `$(false)`. Fix: separare: `local var; var=$(false)`.

**D6: Come eseguo un comando su piu' file trovati da find?**
R: Opzioni sicure (gestiscono spazi nei nomi): `find . -name '*.txt' -exec cmd {} \;` (un file alla volta), `find . -name '*.txt' -exec cmd {} +` (batch), `find . -name '*.txt' -print0 | xargs -0 cmd` (con xargs).

**D7: Qual è la differenza tra `source script.sh` e `./script.sh`?**
R: `source` (o `.`) esegue lo script nella shell CORRENTE — le variabili, funzioni e cd modificano la shell attuale. `./script.sh` esegue in una NUOVA shell (subshell) — nulla viene propagato alla shell padre (eccetto l'exit code).

**D8: Come faccio a fare il debug di uno script che fallisce silenziosamente?**
R: (1) Aggiungi `set -euo pipefail` all'inizio. (2) Aggiungi `set -x` per il trace. (3) Imposta un PS4 informativo. (4) Usa `trap 'echo "Errore alla riga $LINENO" >&2' ERR`. (5) Esegui con `shellcheck` per analisi statica.

**D9: `$RANDOM` è sicuro per generare password?**
R: Assolutamente no. `$RANDOM` genera numeri a 15 bit (0-32767) con un PRNG prevedibile. Per generare password/token sicuri: `openssl rand -base64 32` oppure `head -c 32 /dev/urandom | base64`.

**D10: Come gestisco i segnali in uno script che esegue processi figli?**
R: Usa trap per catturare il segnale e propagarlo: `trap 'kill -- -$$' INT TERM` uccide l'intero process group. In alternativa, `trap 'kill $(jobs -p) 2>/dev/null' EXIT` uccide i job in background al termine.

**D11: Perche' `echo` si comporta diversamente su sistemi diversi?**
R: `echo` non è portabile. Il flag `-e` (interpreta escape) non è POSIX. Su alcuni sistemi echo di default interpreta `\n`, su altri no. Fix: usare `printf '%s\n' "$var"` per output portabile.

**D12: Come posso eseguire operazioni aritmetiche con decimali in Bash?**
R: Bash supporta solo aritmetica intera con `$(( ))`. Per decimali: `bc -l <<< "scale=4; 22/7"` oppure `awk "BEGIN {printf \"%.4f\n\", 22/7}"`.

**D13: Qual è il modo piu' sicuro per creare file temporanei?**
R: `mktemp` con un template: `tmp=$(mktemp /tmp/myscript.XXXXXX)`. Per directory: `tmpdir=$(mktemp -d)`. Accoppiare sempre con `trap 'rm -rf "$tmpdir"' EXIT`.

**D14: Come posso rendere uno script eseguibile e aggiungerlo al PATH?**
R: (1) `chmod +x script.sh`. (2) Mettilo in `~/.local/bin/` (spesso gia' nel PATH), oppure crea la directory e aggiungi a PATH in `.bashrc`: `export PATH="$HOME/.local/bin:$PATH"`.

**D15: Perche' il mio alias non funziona in uno script?**
R: Gli alias sono disabilitati di default negli script non-interattivi. Fix: `shopt -s expand_aliases` all'inizio dello script. Ma è meglio usare funzioni al posto degli alias negli script.

**D16: Come faccio parsing di JSON in Bash?**
R: Non farlo con sed/awk — usa `jq`. Esempi: `jq '.key' file.json`, `jq -r '.items[] | .name' file.json`. Per verificare la validita': `jq empty file.json`.

**D17: Come posso limitare la concorrenza di job in background?**
R: Pattern con `wait -n` (Bash 4.3+): lancia fino a N job, poi `wait -n` per attendere che uno finisca prima di lanciarne un altro. In alternativa, `xargs -P N` o GNU `parallel`.

**D18: Qual è la differenza tra `exec cmd` e `cmd`?**
R: `exec cmd` SOSTITUISCE il processo shell corrente con `cmd` — la shell non esiste piu'. `cmd` lancia `cmd` come processo figlio — la shell attende e continua. Usa `exec` alla fine di wrapper script per risparmiare un processo.

**D19: Come testo se un comando esiste prima di usarlo?**
R: `command -v cmd >/dev/null 2>&1` oppure `type cmd >/dev/null 2>&1`. NON usare `which` — non è portabile e non gestisce builtin/alias.

**D20: Come si scrive uno script che funziona sia su macOS che su Linux?**
R: (1) Usa `#!/usr/bin/env bash` nello shebang. (2) Evita le estensioni GNU-only di sed, grep, date. (3) Testa con `shellcheck -s bash`. (4) Per `sed -i`: su macOS serve `sed -i ''`, su Linux `sed -i`. Fix: `sed -i.bak '...' file && rm file.bak` funziona su entrambi.

**D21: Come gestisco la configurazione dello script (parametri, environment)?**
R: Pattern consigliato in ordine di precedenza (dal piu' alto al piu' basso): (1) argomenti CLI, (2) variabili d'ambiente, (3) file di configurazione, (4) valori di default nel codice. Usare `${VAR:-default}` per i default e `getopts`/`getopt` per gli argomenti.

**D22: Che differenza c'e' tra `&&` e `;` tra comandi?**
R: `cmd1 && cmd2`: esegui cmd2 SOLO se cmd1 ha successo (exit 0). `cmd1 ; cmd2`: esegui cmd2 SEMPRE, indipendentemente dall'exit code di cmd1. Con `set -e`, `;` causa l'exit se cmd1 fallisce; `&&` no (perche' l'errore è "testato").

---

## Esercizi Pratici

### Esercizio 1: Analizzatore di Log

**Obiettivo:** Scrivi uno script che analizzi un file di log e produca un report con: numero totale di righe, conteggio per livello (ERROR, WARN, INFO), le 5 righe di errore piu' recenti.

```bash
# Soluzione:

#!/bin/bash
set -euo pipefail

log_file="${1:?'Uso: $0 <log_file>'}"

[[ -f "$log_file" ]] || { echo "File non trovato: $log_file" >&2; exit 1; }

total=$(wc -l < "$log_file")
errors=$(grep -c 'ERROR' "$log_file" || true)
warnings=$(grep -c 'WARN' "$log_file" || true)
infos=$(grep -c 'INFO' "$log_file" || true)

cat <<EOF
=== Report Log: $log_file ===
Righe totali: $total
ERROR: $errors
WARN:  $warnings
INFO:  $infos

--- Ultimi 5 errori ---
EOF

grep 'ERROR' "$log_file" | tail -5

echo "=== Fine report ==="
```

### Esercizio 2: Batch Rename con Espansione Parametri

**Obiettivo:** Rinomina tutti i file `.jpeg` in `.jpg` e tutti i file con spazi nel nome, sostituendo gli spazi con underscore. Usa solo espansione parametri Bash, niente sed/awk.

```bash
# Soluzione:

#!/bin/bash
set -euo pipefail

dir="${1:-.}"

# Rinomina .jpeg → .jpg
for f in "$dir"/*.jpeg; do
    [[ -e "$f" ]] || continue    # Proteggi se il glob non matcha
    mv -n "$f" "${f%.jpeg}.jpg"
    echo "Rinominato: $f → ${f%.jpeg}.jpg"
done

# Sostituisci spazi con underscore
for f in "$dir"/*\ *; do
    [[ -e "$f" ]] || continue
    new_name="${f// /_}"
    mv -n "$f" "$new_name"
    echo "Rinominato: $f → $new_name"
done
```

### Esercizio 3: Monitor di Sistema con Trap

**Obiettivo:** Scrivi uno script che monitora CPU e memoria ogni 5 secondi, logga su file, e fa cleanup corretto con Ctrl+C (rimuove file temporanei, stampa un riassunto).

```bash
# Soluzione:

#!/bin/bash
set -euo pipefail

readonly LOGFILE=$(mktemp /tmp/monitor.XXXXXX.log)
readonly PIDFILE=$(mktemp /tmp/monitor.XXXXXX.pid)
iterations=0

cleanup() {
    local exit_code=$?
    echo ""
    echo "=== Riassunto ==="
    echo "Iterazioni completate: $iterations"
    echo "Log salvato in: $LOGFILE"
    rm -f "$PIDFILE"
    exit "$exit_code"
}

trap cleanup EXIT INT TERM

echo $$ > "$PIDFILE"
echo "Monitor avviato (PID $$). Log: $LOGFILE"
echo "Premi Ctrl+C per terminare."

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    cpu=$(top -bn1 | grep '%Cpu' | awk '{print 100 - $8}')
    mem=$(free -m | awk 'NR==2{printf "%.1f", $3/$2*100}')
    echo "[$timestamp] CPU: ${cpu}% | MEM: ${mem}%" | tee -a "$LOGFILE"
    ((iterations++))
    sleep 5
done
```

### Esercizio 4: Parser CSV con Array Associativi

**Obiettivo:** Leggi un file CSV (nome,dipartimento,stipendio) e calcola: stipendio medio per dipartimento, dipartimento con lo stipendio piu' alto, numero di dipendenti per dipartimento.

```bash
# Soluzione:

#!/bin/bash
set -euo pipefail

csv_file="${1:?'Uso: $0 <file.csv>'}"
[[ -f "$csv_file" ]] || { echo "File non trovato: $csv_file" >&2; exit 1; }

declare -A dept_total dept_count

# Salta l'intestazione (NR>1 equivalente)
first_line=true
while IFS=',' read -r nome dipartimento stipendio; do
    if $first_line; then
        first_line=false
        continue
    fi
    stipendio="${stipendio//[^0-9]/}"    # Rimuovi caratteri non numerici
    dept_total[$dipartimento]=$(( ${dept_total[$dipartimento]:-0} + stipendio ))
    dept_count[$dipartimento]=$(( ${dept_count[$dipartimento]:-0} + 1 ))
done < "$csv_file"

max_avg=0
max_dept=""

printf "%-20s %10s %10s %12s\n" "DIPARTIMENTO" "DIPENDENTI" "TOTALE" "MEDIA"
printf '%.0s-' {1..55}; echo

for dept in "${!dept_total[@]}"; do
    total=${dept_total[$dept]}
    count=${dept_count[$dept]}
    avg=$((total / count))
    printf "%-20s %10d %10d %12d\n" "$dept" "$count" "$total" "$avg"
    if ((avg > max_avg)); then
        max_avg=$avg
        max_dept=$dept
    fi
done

echo ""
echo "Dipartimento con stipendio medio piu' alto: $max_dept ($max_avg)"
```

### Esercizio 5: Esecuzione Parallela con Limite di Concorrenza

**Obiettivo:** Scarica una lista di URL da un file, con massimo 4 download simultanei. Logga successi e fallimenti. Usa solo Bash (nessun `xargs -P` o `parallel`).

```bash
# Soluzione:

#!/bin/bash
set -euo pipefail

url_file="${1:?'Uso: $0 <file_url>'}"
max_parallel=4
success=0
failure=0

download() {
    local url="$1"
    local filename
    filename=$(basename "$url")
    if curl -sfSL -o "/tmp/downloads/$filename" "$url" 2>/dev/null; then
        echo "[OK]   $url"
        return 0
    else
        echo "[FAIL] $url" >&2
        return 1
    fi
}

mkdir -p /tmp/downloads

while IFS= read -r url; do
    [[ -z "$url" || "$url" == \#* ]] && continue    # Salta vuote e commenti

    download "$url" && ((success++)) || ((failure++)) &

    # Limite concorrenza
    while (( $(jobs -r -p | wc -l) >= max_parallel )); do
        wait -n 2>/dev/null || true
    done
done < "$url_file"

wait    # Attendi tutti i rimanenti

echo ""
echo "Completato. Successi: $success | Fallimenti: $failure"
```

### Esercizio 6: Diff Interattivo tra Directory

**Obiettivo:** Confronta due directory e mostra: file presenti solo nella prima, file presenti solo nella seconda, file presenti in entrambe ma diversi. Usa process substitution.

```bash
# Soluzione:

#!/bin/bash
set -euo pipefail

dir1="${1:?'Uso: $0 <dir1> <dir2>'}"
dir2="${2:?'Uso: $0 <dir1> <dir2>'}"

[[ -d "$dir1" ]] || { echo "Non e' una directory: $dir1" >&2; exit 1; }
[[ -d "$dir2" ]] || { echo "Non e' una directory: $dir2" >&2; exit 1; }

echo "=== File solo in $dir1 ==="
comm -23 <(cd "$dir1" && find . -type f | sort) \
         <(cd "$dir2" && find . -type f | sort)

echo ""
echo "=== File solo in $dir2 ==="
comm -13 <(cd "$dir1" && find . -type f | sort) \
         <(cd "$dir2" && find . -type f | sort)

echo ""
echo "=== File presenti in entrambi ma diversi ==="
comm -12 <(cd "$dir1" && find . -type f | sort) \
         <(cd "$dir2" && find . -type f | sort) |
while IFS= read -r file; do
    if ! diff -q "$dir1/$file" "$dir2/$file" >/dev/null 2>&1; then
        echo "  MODIFICATO: $file"
    fi
done
```

### Esercizio 7: Wrapper Script con getopts

**Obiettivo:** Crea un wrapper per `rsync` che accetta opzioni personalizzate: `--dry-run`, `--verbose`, `--exclude PATTERN`, `--delete`. Deve loggare le operazioni e supportare `--help`.

```bash
# Soluzione:

#!/bin/bash
set -euo pipefail

readonly LOGFILE="/tmp/sync_$(date +%Y%m%d_%H%M%S).log"

usage() {
    cat <<EOF
Uso: $(basename "$0") [OPZIONI] <sorgente> <destinazione>

Opzioni:
  -h, --help            Mostra questo help
  -v, --verbose         Output verboso
  -n, --dry-run         Simula senza modificare
  -d, --delete          Elimina file extra nella destinazione
  -e, --exclude PATTERN Escludi pattern (ripetibile)
EOF
    exit "${1:-0}"
}

OPTS=$(getopt -o hvnde: \
    --long help,verbose,dry-run,delete,exclude: \
    -n "$(basename "$0")" -- "$@") || usage 1

eval set -- "$OPTS"

VERBOSE=0
DRY_RUN=0
DELETE=0
declare -a EXCLUDES=()

while true; do
    case "$1" in
        -h|--help)    usage 0 ;;
        -v|--verbose) VERBOSE=1; shift ;;
        -n|--dry-run) DRY_RUN=1; shift ;;
        -d|--delete)  DELETE=1; shift ;;
        -e|--exclude) EXCLUDES+=("--exclude=$2"); shift 2 ;;
        --)           shift; break ;;
    esac
done

[[ $# -ge 2 ]] || { echo "ERRORE: sorgente e destinazione richiesti" >&2; usage 1; }

SRC="$1"
DST="$2"

rsync_opts=("-a" "--progress")
((VERBOSE)) && rsync_opts+=("--verbose")
((DRY_RUN)) && rsync_opts+=("--dry-run")
((DELETE))  && rsync_opts+=("--delete")
rsync_opts+=("${EXCLUDES[@]}")

echo "[$(date)] rsync ${rsync_opts[*]} $SRC $DST" | tee -a "$LOGFILE"
rsync "${rsync_opts[@]}" "$SRC" "$DST" 2>&1 | tee -a "$LOGFILE"
echo "[$(date)] Completato. Log: $LOGFILE"
```

### Esercizio 8: Named Pipe per IPC

**Obiettivo:** Crea un "server" e un "client" che comunicano tramite una named pipe. Il server accetta comandi (`uptime`, `disk`, `mem`, `quit`) e restituisce l'output.

```bash
# Soluzione — server.sh:

#!/bin/bash
set -euo pipefail

readonly PIPE_IN="/tmp/cmd_pipe"
readonly PIPE_OUT="/tmp/result_pipe"

cleanup() {
    rm -f "$PIPE_IN" "$PIPE_OUT"
    echo "Server terminato."
}
trap cleanup EXIT

mkfifo "$PIPE_IN" "$PIPE_OUT"
echo "Server in ascolto..."

while true; do
    if read -r cmd < "$PIPE_IN"; then
        case "$cmd" in
            uptime) uptime > "$PIPE_OUT" ;;
            disk)   df -h / > "$PIPE_OUT" ;;
            mem)    free -h > "$PIPE_OUT" ;;
            quit)   echo "Arrivederci" > "$PIPE_OUT"; break ;;
            *)      echo "Comando sconosciuto: $cmd" > "$PIPE_OUT" ;;
        esac
    fi
done

# Soluzione — client.sh:

#!/bin/bash
set -euo pipefail

readonly PIPE_IN="/tmp/cmd_pipe"
readonly PIPE_OUT="/tmp/result_pipe"

[[ -p "$PIPE_IN" ]] || { echo "Server non avviato" >&2; exit 1; }

cmd="${1:?'Uso: $0 <uptime|disk|mem|quit>'}"
echo "$cmd" > "$PIPE_IN"
cat "$PIPE_OUT"
```

### Esercizio 9: Analizzatore di Testo con awk

**Obiettivo:** Scrivi un programma awk che analizza un file di testo e produce: conteggio parole totale, le 10 parole piu' frequenti (escludendo le stop words), lunghezza media delle frasi (frasi separate da `.`).

```bash
# Soluzione:

#!/bin/bash
set -euo pipefail

input_file="${1:?'Uso: $0 <file_testo>'}"

awk '
BEGIN {
    # Stop words da ignorare
    split("il lo la i gli le un uno una di da in con su per tra fra a e o ma che non si", sw, " ")
    for (w in sw) stop[sw[w]] = 1
    total_words = 0
    sentence_count = 0
    words_in_sentence = 0
}
{
    # Conta frasi (punti)
    n = gsub(/\./, ".", $0)
    sentence_count += n

    # Processa parole
    for (i = 1; i <= NF; i++) {
        word = tolower($i)
        gsub(/[^a-zA-Zaeiou]/, "", word)    # Rimuovi punteggiatura
        if (length(word) < 2) continue
        total_words++
        words_in_sentence++

        if (!(word in stop)) {
            freq[word]++
        }
    }
}
END {
    if (sentence_count == 0) sentence_count = 1
    printf "Parole totali: %d\n", total_words
    printf "Frasi: %d\n", sentence_count
    printf "Lunghezza media frase: %.1f parole\n", total_words / sentence_count
    printf "\nTop 10 parole (escluse stop words):\n"
    printf "%-20s %s\n", "PAROLA", "FREQUENZA"

    # Ordinamento: copia in array temporaneo per sort
    PROCINFO["sorted_in"] = "@val_num_desc"
    n = 0
    for (word in freq) {
        if (++n > 10) break
        printf "%-20s %d\n", word, freq[word]
    }
}
' "$input_file"
```

### Esercizio 10: Script di Deployment con Tutte le Tecniche

**Obiettivo:** Scrivi uno script di deployment che: parsa argomenti complessi, usa lock file, gestisce trap e segnali, logga con timestamp, esegue operazioni in parallelo con limite di concorrenza, verifica prerequisiti, usa array associativi per la configurazione.

```bash
# Soluzione:

#!/bin/bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly LOCKFILE="/var/run/${SCRIPT_NAME}.lock"
readonly LOGDIR="/var/log/deploy"
readonly LOGFILE="${LOGDIR}/deploy_$(date +%Y%m%d_%H%M%S).log"

# Colori
if [[ -t 1 ]]; then
    readonly R=$'\033[31m' G=$'\033[32m' Y=$'\033[33m' B=$'\033[34m' N=$'\033[0m'
else
    readonly R='' G='' Y='' B='' N=''
fi

log()   { printf '%s [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" "$2" | tee -a "$LOGFILE"; }
info()  { log "${G}INFO${N}" "$1"; }
warn()  { log "${Y}WARN${N}" "$1" >&2; }
error() { log "${R}ERROR${N}" "$1" >&2; }
die()   { error "$1"; exit 1; }

# Configurazione per ambiente
declare -A SERVERS DEPLOY_PATHS HEALTH_URLS
SERVERS[staging]="staging-01 staging-02"
SERVERS[production]="prod-01 prod-02 prod-03 prod-04"
DEPLOY_PATHS[staging]="/opt/app/staging"
DEPLOY_PATHS[production]="/opt/app/production"
HEALTH_URLS[staging]="http://staging.example.com/health"
HEALTH_URLS[production]="http://example.com/health"

# Lock
acquire_lock() {
    if ! mkdir "$LOCKFILE" 2>/dev/null; then
        die "Deploy gia' in esecuzione (lock: $LOCKFILE)"
    fi
    info "Lock acquisito: $LOCKFILE"
}

# Cleanup
cleanup() {
    local exit_code=$?
    rm -rf "$LOCKFILE" 2>/dev/null || true
    if ((exit_code == 0)); then
        info "Deploy completato con successo"
    else
        error "Deploy fallito (exit code: $exit_code)"
    fi
}
trap cleanup EXIT
trap 'error "Interrotto (SIGINT)"; exit 130' INT
trap 'error "Terminato (SIGTERM)"; exit 143' TERM

# Prerequisiti
check_prerequisites() {
    local missing=()
    for cmd in rsync ssh curl jq; do
        command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
    done
    if ((${#missing[@]} > 0)); then
        die "Comandi mancanti: ${missing[*]}"
    fi
    info "Prerequisiti verificati"
}

# Deploy a un singolo server
deploy_to_server() {
    local server="$1" env="$2" artifact="$3"
    local deploy_path="${DEPLOY_PATHS[$env]}"
    info "Deploy su $server..."
    if ssh "$server" "mkdir -p $deploy_path" && \
       rsync -az "$artifact" "$server:$deploy_path/"; then
        info "Deploy su $server completato"
        return 0
    else
        error "Deploy su $server FALLITO"
        return 1
    fi
}

# Health check
health_check() {
    local url="$1" retries=5 delay=3
    for ((i=1; i<=retries; i++)); do
        if curl -sf "$url" >/dev/null 2>&1; then
            info "Health check OK ($url)"
            return 0
        fi
        warn "Health check fallito (tentativo $i/$retries)"
        sleep "$delay"
    done
    return 1
}

# Parsing argomenti
usage() {
    cat <<EOF
Uso: $SCRIPT_NAME [OPZIONI] <ambiente> <artifact>

Ambienti: staging, production
Opzioni:
  -h, --help         Help
  -n, --dry-run      Simula
  -p, --parallel N   Concorrenza (default: 2)
  -s, --skip-health  Salta health check
EOF
    exit "${1:-0}"
}

OPTS=$(getopt -o hnp:s --long help,dry-run,parallel:,skip-health \
    -n "$SCRIPT_NAME" -- "$@") || usage 1
eval set -- "$OPTS"

DRY_RUN=0
PARALLEL=2
SKIP_HEALTH=0

while true; do
    case "$1" in
        -h|--help)      usage 0 ;;
        -n|--dry-run)   DRY_RUN=1; shift ;;
        -p|--parallel)  PARALLEL="$2"; shift 2 ;;
        -s|--skip-health) SKIP_HEALTH=1; shift ;;
        --)             shift; break ;;
    esac
done

ENV="${1:?$(usage 1)}"
ARTIFACT="${2:?$(usage 1)}"

[[ -v SERVERS[$ENV] ]] || die "Ambiente sconosciuto: $ENV"
[[ -e "$ARTIFACT" ]]   || die "Artifact non trovato: $ARTIFACT"

# Main
main() {
    mkdir -p "$LOGDIR"
    acquire_lock
    check_prerequisites

    info "Deploy ambiente: $ENV"
    info "Artifact: $ARTIFACT"
    info "Server: ${SERVERS[$ENV]}"
    info "Concorrenza: $PARALLEL"
    ((DRY_RUN)) && info "*** MODALITA' DRY-RUN ***"

    local success=0 failure=0

    read -r -a server_list <<< "${SERVERS[$ENV]}"

    for server in "${server_list[@]}"; do
        if ((DRY_RUN)); then
            info "[DRY-RUN] deploy_to_server $server $ENV $ARTIFACT"
            ((success++))
        else
            deploy_to_server "$server" "$ENV" "$ARTIFACT" && ((success++)) || ((failure++)) &
            while (( $(jobs -r -p | wc -l) >= PARALLEL )); do
                wait -n 2>/dev/null || true
            done
        fi
    done
    wait

    info "Risultati: $success successi, $failure fallimenti"
    ((failure > 0)) && die "$failure server hanno fallito il deploy"

    if ((!SKIP_HEALTH && !DRY_RUN)); then
        health_check "${HEALTH_URLS[$ENV]}" || die "Health check fallito!"
    fi
}

main
```
