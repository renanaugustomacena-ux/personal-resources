# Tutorial Linux 09 — Gestione Processi: ps, pgrep, strace, lsof, Segnali

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** ciclo di vita processi, ps, pgrep/pkill, strace, lsof, segnali Unix
> **Prerequisiti:** `tutorial_linux_08_performance.md`
> **Durata stimata:** 10-12 ore

---

## Mappa concettuale

```
Gestione Processi
│
├── Ciclo vita processo
│   ├── fork() → exec() → exit()
│   ├── Stato: R, S, D, Z, T
│   └── PPID, PID, session, pgroup
│
├── Ispezione processi
│   ├── ps — snapshot processi
│   ├── pgrep / pkill — ricerca per nome
│   ├── pstree — gerarchia processi
│   └── pidof — PID di un programma
│
├── Segnali Unix
│   ├── SIGTERM (15) — chiusura elegante
│   ├── SIGKILL (9) — forza terminazione
│   ├── SIGHUP (1) — ricarica config
│   └── SIGUSR1/2 — custom app
│
├── strace — syscall tracing
│   ├── -p PID attach
│   ├── -e trace=open,read,write
│   └── -c count summary
│
└── lsof — file aperti
    ├── -p PID
    ├── -i :porta
    └── -u utente
```

---

# Parte A — Ciclo di vita dei processi

---

## A1. Stati di un processo

```bash
# Stati in ps (colonna STAT / S)
# R = Running / Runnable (in esecuzione o in coda CPU)
# S = Sleeping interrompibile (attende evento, risponde a segnali)
# D = Sleeping non interrompibile (attende I/O disco — non killabile!)
# Z = Zombie (terminato, processo padre non ha letto exit code)
# T = Stopped (Ctrl+Z o SIGSTOP)
# I = Idle (kernel thread inattivo)

# Prefissi:
# < = alta priorità (nice negativo)
# N = bassa priorità (nice positivo)
# L = pagine locked in RAM
# s = session leader
# l = multi-threaded
# + = in foreground del terminale

# Esempio: "Ssl" = Sleeping, session leader, multi-threaded
```

---

## A2. ps: snapshot processi

```bash
# Tutti i processi del sistema
ps aux
# USER       PID %CPU %MEM    VSZ   RSS TTY  STAT  START   TIME COMMAND

# Formato BSD vs UNIX
ps aux          # BSD: tutti i processi, formato esteso
ps -ef          # UNIX: tutti i processi, formato completo
ps -eo pid,ppid,user,%cpu,%mem,stat,start,cmd  # custom

# Filtrare
ps aux | grep nginx                   # cerca nginx
ps -u www-data                        # processi dell'utente www-data
ps -U root -u root u                  # processi root in formato u

# Ordinamento
ps aux --sort=-%cpu | head -20        # top CPU consumers
ps aux --sort=-%mem | head -20        # top RAM consumers
ps aux --sort=-rss | head -20         # top RSS

# Gerarchia
ps -ef --forest                       # ASCII tree
ps axjf                               # altro formato tree

# Info specifica
ps -p 1234 -o pid,ppid,user,%cpu,%mem,cmd
ps -p 1234,5678,9012 -o pid,cmd       # multipli PID

# Processi zombie
ps aux | awk '$8=="Z"{print}'
```

> **Analogia:** Un processo Linux è come un contratto di lavoro: nasce con `fork()` (viene assunto dalla copia del padre), poi con `exec()` diventa qualcosa di diverso (cambia mansione). Quando finisce, lascia un "certificato di terminazione" (exit code) che il padre deve raccogliere. Se il padre non raccoglie, il processo rimane come "zombie" — occupando solo una riga nella tabella dei processi, senza consumare CPU o RAM, aspettando che qualcuno registri la sua uscita.

---

## A3. pgrep e pkill

```bash
# pgrep — trova PID per nome
pgrep nginx                    # PID di tutti i processi nginx
pgrep -l nginx                 # PID + nome
pgrep -a nginx                 # PID + command line completa
pgrep -u www-data              # processi dell'utente www-data
pgrep -P 1234                  # figli del processo 1234

# pkill — invia segnale per nome
pkill nginx                    # SIGTERM a tutti i processi nginx
pkill -9 nginx                 # SIGKILL
pkill -HUP nginx               # SIGHUP (reload)
pkill -u mario firefox         # kill firefox dell'utente mario

# killall — alternativa a pkill
killall nginx
killall -9 nginx

# pidof — PID di un programma specifico
pidof nginx
pidof sshd

# pstree — albero processi
pstree                         # tutto il sistema
pstree -p                      # con PID
pstree -p 1234                 # sottoalbero di 1234
pstree -u                      # mostra utente
```

---

# Parte B — Segnali Unix

---

## B1. Segnali comuni

```bash
# Lista segnali
kill -l
# 1) SIGHUP    2) SIGINT    3) SIGQUIT   9) SIGKILL
# 15) SIGTERM  17) SIGCHLD  18) SIGCONT  19) SIGSTOP

# Invio segnali
kill -15 1234           # SIGTERM (elegante)
kill -9 1234            # SIGKILL (forza, non gestibile)
kill -1 1234            # SIGHUP (reload config)
kill -STOP 1234         # pausa processo
kill -CONT 1234         # riprendi processo
kill -USR1 1234         # segnale custom (dipende dall'app)

# Gerarchia kill:
# 1. kill -15 (dai tempo di chiudere)
# 2. Aspetta 5-10 secondi
# 3. kill -9 solo se non risponde (lascia file temp aperti)

# Invia a gruppo di processi (negativo = PGID)
kill -15 -1234          # tutti i processi nel gruppo 1234

# Python: gestione segnali
# import signal, sys
# def handler(sig, frame):
#     print("SIGTERM ricevuto, pulizia...")
#     sys.exit(0)
# signal.signal(signal.SIGTERM, handler)

# Bash: gestione segnali
trap 'echo "Script interrotto"; exit 1' SIGTERM SIGINT
```

---

# Parte C — strace: tracing syscall

---

## C1. strace per debugging

```bash
# Trace tutte le syscall
strace ls

# Attach a processo esistente
strace -p $(pgrep nginx)

# Filtra per tipo di syscall
strace -e trace=open,openat,read,write ls   # solo I/O
strace -e trace=network curl https://google.com   # solo rete
strace -e trace=signal kill -HUP 1234       # solo segnali

# Statistiche (summary)
strace -c ls -la /usr/bin
# % time     seconds  usecs/call     calls    errors syscall
# 35.25    0.000282           4        64           read
# 28.30    0.000227          11        20        14  openat
# Mostra quali syscall costano di più

# Output su file
strace -o /tmp/trace.txt -p 1234

# Trace con timestamp
strace -t -p 1234          # ora assoluta
strace -r -p 1234          # tempo relativo dalla syscall precedente
strace -T -p 1234          # durata di ogni syscall

# Trace figli (fork)
strace -f nginx            # segui processi figli

# Caso d'uso: processo si blocca
strace -p $(pgrep app-bloccata) -e trace=all 2>&1 | head -20
# Se vedi: read(5, ...  e si ferma → attende dati su fd 5
# lsof -p PID | grep "^app.*5u" → scopri quale file è fd 5
```

---

# Parte D — lsof: file aperti

---

## D1. lsof per diagnostica

```bash
# Lista tutti i file aperti
lsof | head -50
lsof | wc -l       # quanti file aperti in totale

# Per un processo
lsof -p 1234               # file aperti da processo 1234
lsof -p 1234 | grep REG    # solo file regolari
lsof -p 1234 | grep SOCK   # solo socket

# Per un utente
lsof -u mario              # file aperti dall'utente mario
lsof -u ^root              # tutti TRANNE root

# Per un file specifico
lsof /var/log/nginx/access.log    # chi ha aperto questo file?
lsof /dev/sda1                     # chi usa questo disco?

# Porte di rete
lsof -i                    # tutte le connessioni di rete
lsof -i :80                # chi ascolta su porta 80
lsof -i :5432              # PostgreSQL
lsof -i TCP                # solo TCP
lsof -i TCP:80             # TCP sulla porta 80
lsof -i @192.168.1.50      # connessioni verso questo IP

# Processo che usa un file (utile per "device busy")
fuser /mount/punto         # mostra PID che usa il mount
fuser -v -m /mount/punto   # verbose
fuser -k /mount/punto      # kill tutti che lo usano (ATTENZIONE!)

# Eliminare file "fantasma" (occupano spazio ma non esistono)
# Accade quando un processo ha il file aperto ma è stato rm
lsof | grep "(deleted)"
# Per liberare spazio: /proc/PID/fd/N → truncate o kill il processo
```

---

# Parte E — Riepilogo

## Workflow debugging processo bloccato

```bash
# 1. Trova il processo
pgrep -a nome-processo
ps aux | grep nome-processo

# 2. Controlla lo stato
ps -p PID -o stat,wchan   # stato e dove è bloccato

# 3. Qual è l'ultima syscall?
strace -p PID 2>&1 | head -5

# 4. Quali file/socket ha aperti?
lsof -p PID

# 5. Quanto memoria usa?
cat /proc/PID/status | grep VmRSS

# 6. Decidi: SIGTERM → aspetta → SIGKILL
kill -15 PID && sleep 5 && kill -9 PID 2>/dev/null
```

## Segnali in breve

| Segnale | Numero | Gestibile | Uso |
|---|---|---|---|
| SIGHUP | 1 | Sì | Reload configurazione |
| SIGINT | 2 | Sì | Ctrl+C interattivo |
| SIGQUIT | 3 | Sì | Ctrl+\\ con core dump |
| SIGKILL | 9 | **No** | Termina immediatamente |
| SIGTERM | 15 | Sì | Chiudi elegantemente |
| SIGSTOP | 19 | **No** | Pausa |
| SIGCONT | 18 | Sì | Riprendi da STOP |
| SIGUSR1 | 10 | Sì | Custom app-defined |

## Prossimi passi

- `tutorial_linux_10_ssh_avanzato.md` — SSH tunneling e chiavi
- `tutorial_linux_22_troubleshooting.md` — diagnostica sistema completa
