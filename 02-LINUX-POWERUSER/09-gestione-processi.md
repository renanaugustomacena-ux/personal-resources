# Gestione Processi Linux — Guida Completa

> **Modulo 09** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **PID 1 e systemd; init script legacy.**
2. **cgroups v2 default; v1 legacy.**
3. **OOM killer score: `oom_score_adj` per protect critical.**
4. **`htop` > `top` per usability; `btm`/`bottom` modern alternative.**
5. **fork()+exec() è la base di TUTTO in Unix; capirlo bene sblocca il resto.**
6. **I namespace sono il fondamento dei container; processi isolati, non VM.**
7. **strace è il debugger universale: quando non capisci cosa succede, traccia le syscall.**
8. **Ogni processo vive in /proc/[pid]; leggere quel filesystem è leggere il kernel.**


## Indice

- [Panoramica](#panoramica)
- [Ciclo di Vita dei Processi](#ciclo-di-vita-dei-processi)
  - [fork() — Creazione di un Processo](#fork--creazione-di-un-processo)
  - [exec() — Sostituzione dell'Immagine](#exec--sostituzione-dellimmagine)
  - [wait() e waitpid() — Raccolta Exit Status](#wait-e-waitpid--raccolta-exit-status)
  - [_exit() vs exit() — Terminazione](#_exit-vs-exit--terminazione)
  - [Processi Zombie](#processi-zombie)
  - [Processi Orfani](#processi-orfani)
  - [Copy-on-Write (COW)](#copy-on-write-cow)
- [Stati dei Processi](#stati-dei-processi)
  - [R — Running/Runnable](#r--runningrunnable)
  - [S — Interruptible Sleep](#s--interruptible-sleep)
  - [D — Uninterruptible Sleep](#d--uninterruptible-sleep)
  - [T — Stopped](#t--stopped)
  - [Z — Zombie](#z--zombie)
  - [X — Dead](#x--dead)
  - [Diagnosi dei Processi in Stato D](#diagnosi-dei-processi-in-stato-d)
- [Il Filesystem /proc/\[pid\]](#il-filesystem-procpid)
  - [status — Stato del Processo](#status--stato-del-processo)
  - [stat — Statistiche Raw](#stat--statistiche-raw)
  - [maps — Mappatura Memoria](#maps--mappatura-memoria)
  - [fd — File Descriptor](#fd--file-descriptor)
  - [environ — Variabili d'Ambiente](#environ--variabili-dambiente)
  - [cmdline — Linea di Comando](#cmdline--linea-di-comando)
  - [limits — Limiti Risorse](#limits--limiti-risorse)
  - [oom_score e oom_score_adj](#oom_score-e-oom_score_adj)
  - [cgroup — Appartenenza cgroup](#cgroup--appartenenza-cgroup)
  - [io — Statistiche I/O](#io--statistiche-io)
  - [smaps — Memoria Dettagliata](#smaps--memoria-dettagliata)
  - [stack — Stack del Kernel](#stack--stack-del-kernel)
  - [wchan — Wait Channel](#wchan--wait-channel)
  - [ns — Namespace](#ns--namespace)
- [Processi: Fondamenti, PID, PPID](#processi-fondamenti-pid-ppid)
- [Segnali — Deep Dive](#segnali--deep-dive)
  - [Tutti i 31 Segnali Standard](#tutti-i-31-segnali-standard)
  - [Segnali Real-Time](#segnali-real-time)
  - [signal() vs sigaction()](#signal-vs-sigaction)
  - [Signal Masking](#signal-masking)
  - [Comandi kill, killall, pkill](#comandi-kill-killall-pkill)
  - [Gestione Segnali nello Scripting](#gestione-segnali-nello-scripting)
- [Priorita: nice e renice](#priorità-nice-e-renice)
- [Scheduling — Internals](#scheduling--internals)
  - [CFS — Completely Fair Scheduler](#cfs--completely-fair-scheduler)
  - [nice e renice — Priorita Utente](#nice-e-renice--priorità-utente)
  - [ionice — Priorita I/O](#ionice--priorità-io)
  - [chrt — Scheduling Real-Time](#chrt--scheduling-real-time)
  - [SCHED_FIFO, SCHED_RR, SCHED_DEADLINE](#sched_fifo-sched_rr-sched_deadline)
  - [CPU Affinity — taskset](#cpu-affinity--taskset)
- [cgroups v2](#cgroups-v2)
  - [Architettura cgroups v2](#architettura-cgroups-v2)
  - [Controller CPU](#controller-cpu)
  - [Controller Memory](#controller-memory)
  - [Controller IO](#controller-io)
  - [Integrazione systemd](#integrazione-systemd)
  - [Delegazione cgroup](#delegazione-cgroup)
- [Namespace Linux](#namespace-linux)
  - [PID Namespace](#pid-namespace)
  - [Network Namespace](#network-namespace)
  - [Mount Namespace](#mount-namespace)
  - [UTS Namespace](#uts-namespace)
  - [IPC Namespace](#ipc-namespace)
  - [User Namespace](#user-namespace)
  - [Cgroup Namespace](#cgroup-namespace)
  - [Come i Namespace Abilitano i Container](#come-i-namespace-abilitano-i-container)
- [Comunicazione tra Processi (IPC)](#comunicazione-tra-processi-ipc)
  - [Pipe e Named Pipe (FIFO)](#pipe-e-named-pipe-fifo)
  - [Unix Domain Socket](#unix-domain-socket)
  - [Shared Memory](#shared-memory)
  - [Semafori](#semafori)
  - [Code di Messaggi](#code-di-messaggi)
- [Monitoraggio Processi](#monitoraggio-processi)
  - [ps — Process Status](#ps--process-status)
  - [top e htop](#top-e-htop)
  - [atop — Analisi Storica](#atop--analisi-storica)
  - [pstree — Albero Processi](#pstree--albero-processi)
  - [pidstat — Statistiche per PID](#pidstat--statistiche-per-pid)
  - [Analisi /proc in Tempo Reale](#analisi-proc-in-tempo-reale)
- [Background, Foreground e Jobs](#background-foreground-e-jobs)
  - [Gestione Job nella Shell](#gestione-job-nella-shell)
  - [nohup e disown](#nohup-e-disown)
  - [Screen e tmux](#screen-e-tmux)
  - [Servizi systemd](#servizi-systemd)
- [System Call e strace](#system-call-e-strace)
  - [strace — Deep Dive](#strace--deep-dive)
  - [Syscall Comuni per Debugging](#syscall-comuni-per-debugging)
  - [ltrace — Library Calls](#ltrace--library-calls)
- [Sicurezza dei Processi](#sicurezza-dei-processi)
  - [Capabilities Linux](#capabilities-linux)
  - [Seccomp Filters](#seccomp-filters)
  - [AppArmor e SELinux](#apparmor-e-selinux)
  - [Limiti di Risorse (ulimit)](#limiti-di-risorse-ulimit)
- [Cron e Crontab](#cron-e-crontab)
- [at e batch](#at-e-batch)
- [systemd Timers](#systemd-timers)
- [Best Practices](#best-practices)
- [Troubleshooting — 25 Problemi Comuni](#troubleshooting--25-problemi-comuni)
- [FAQ — 18 Domande e Risposte](#faq--18-domande-e-risposte)
- [Esercizi Pratici con Soluzioni](#esercizi-pratici-con-soluzioni)
- [Workflow: Metodologia Sistematica di Debug Processi](#workflow-metodologia-sistematica-di-debug-processi)

---

## Panoramica

Un processo è un'istanza di un programma in esecuzione. Ogni processo ha un PID (Process ID) univoco, uno stato, un proprietario, una priorità e risorse allocate. La gestione dei processi — monitoraggio, controllo, schedulazione — è una delle attività quotidiane dell'amministratore Linux. Dalla diagnosi di un servizio che consuma troppa CPU alla schedulazione di attività automatiche con cron: padroneggiare i processi è fondamentale.

Un processo non è un programma: un programma è un file su disco (un eseguibile ELF), un processo è quell'eseguibile caricato in memoria con il proprio spazio di indirizzamento, i propri file descriptor, le proprie credenziali. Dallo stesso programma possono derivare centinaia di processi (es. un web server con worker processes).

Il kernel mantiene per ogni processo una struttura `task_struct` (~6 KB nella versione corrente del kernel), che contiene tutto ciò che il kernel deve sapere: stato, credenziali, limiti risorse, segnali pendenti, puntatori alla memoria, informazioni di scheduling, accounting. Questa struttura è la "carta d'identità" del processo nel kernel.

---

## Ciclo di Vita dei Processi

### fork() — Creazione di un Processo

La system call `fork()` è il meccanismo fondamentale di creazione processi in Unix/Linux. Crea una copia (quasi) esatta del processo chiamante.

```
Processo Padre (PID 100)
    │
    ├── fork() ──────────────────────────┐
    │                                     │
    │   fork() ritorna PID del figlio     │   fork() ritorna 0
    │   (es. 101) al padre               │   al processo figlio
    │                                     │
    ▼                                     ▼
Padre (PID 100)                   Figlio (PID 101)
continua esecuzione               copia del padre
```

Dopo `fork()`:
- Il figlio ottiene una copia dello spazio di indirizzamento del padre
- Il figlio eredita: file descriptor aperti, variabili d'ambiente, working directory, UID/GID, signal handlers, limiti risorse
- Il figlio NON eredita: PID (ne ottiene uno nuovo), lock di file, timer, segnali pendenti
- Il valore di ritorno distingue padre (riceve PID del figlio) da figlio (riceve 0)

```c
/* Esempio concettuale in C */
pid_t pid = fork();

if (pid < 0) {
    /* Errore: fork fallita (troppi processi, memoria esaurita) */
    perror("fork");
    exit(1);
} else if (pid == 0) {
    /* Codice eseguito dal processo FIGLIO */
    printf("Sono il figlio, PID: %d, PPID: %d\n", getpid(), getppid());
} else {
    /* Codice eseguito dal processo PADRE */
    printf("Sono il padre, PID: %d, figlio: %d\n", getpid(), pid);
    wait(NULL);  /* Attendi che il figlio termini */
}
```

```bash
# Dimostrare fork in bash — ogni subshell è un fork
echo "Shell PID: $$"
(echo "Subshell PID: $BASHPID, PPID: $PPID")
```

### exec() — Sostituzione dell'Immagine

La famiglia `exec()` (execve, execl, execp, execvp, ...) sostituisce l'immagine del processo corrente con un nuovo programma. Non crea un nuovo processo: lo stesso PID esegue un programma diverso.

```
Processo (PID 101)                Processo (PID 101)
  Immagine: bash         exec()    Immagine: /usr/bin/ls
  Codice bash in RAM  ──────────>  Codice ls in RAM
  Stack bash                       Stack ls (nuovo)
  Heap bash                        Heap ls (nuovo)
  File desc ereditati              File desc ereditati (se non CLOEXEC)
```

Il pattern fork()+exec() è fondamentale:
1. Il padre fa `fork()` → crea il figlio
2. Il figlio fa `exec()` → sostituisce se stesso con il nuovo programma
3. Il padre fa `wait()` → attende la terminazione del figlio

Questo è ciò che succede ogni volta che si esegue un comando nella shell:

```bash
# Quando digiti "ls -la", la shell internamente fa:
# 1. fork() → crea un processo figlio
# 2. nel figlio: exec("/usr/bin/ls", ["ls", "-la"]) → sostituisce bash con ls
# 3. nel padre: wait() → aspetta che ls termini
# 4. ls termina, il padre (bash) riprende e mostra il prompt
```

### wait() e waitpid() — Raccolta Exit Status

Quando un processo figlio termina, il kernel mantiene la sua entry nella process table finché il padre non chiama `wait()` o `waitpid()` per raccogliere l'exit status. Senza questa raccolta, il figlio diventa uno zombie.

```c
/* wait() bloccante — aspetta qualsiasi figlio */
int status;
pid_t child = wait(&status);

if (WIFEXITED(status)) {
    printf("Figlio %d uscito con codice %d\n", child, WEXITSTATUS(status));
} else if (WIFSIGNALED(status)) {
    printf("Figlio %d ucciso dal segnale %d\n", child, WTERMSIG(status));
}

/* waitpid() — aspetta un figlio specifico, supporta WNOHANG */
pid_t result = waitpid(child_pid, &status, WNOHANG);
/* WNOHANG: non bloccare, ritorna 0 se il figlio non è ancora terminato */
```

```bash
# In bash, $? è l'exit status dell'ultimo comando (raccolto automaticamente)
ls /nonexistent 2>/dev/null
echo "Exit status: $?"   # 2 (errore)

# wait builtin — aspetta un processo in background
sleep 10 &
BGPID=$!
wait $BGPID
echo "sleep terminato con exit status: $?"
```

### _exit() vs exit() — Terminazione

- `_exit(status)` — system call: termina immediatamente il processo. Non esegue atexit handlers, non fa flush dei buffer stdio, non chiama i distruttori C++.
- `exit(status)` — funzione C library: chiama gli atexit handlers registrati, fa flush di tutti gli stream stdio, poi chiama `_exit()`.

```
exit(0)
  ├── atexit handlers (in ordine LIFO)
  ├── fclose() su tutti gli stream stdio
  ├── tmpfile() cleanup
  └── _exit(0) ← system call vera
        ├── chiude tutti i file descriptor
        ├── rilascia memoria
        ├── invia SIGCHLD al padre
        └── processo diventa zombie fino a wait()
```

```bash
# In bash, l'exit status è 0-255
exit 0      # Successo
exit 1      # Errore generico
exit 127    # Comando non trovato
exit 126    # Permesso negato
exit 128+N  # Terminato dal segnale N (es. 137 = 128+9 = SIGKILL)
```

### Processi Zombie

Un processo zombie (stato Z) è un processo che ha terminato l'esecuzione ma la cui entry nella process table non è stata ancora rimossa perché il padre non ha chiamato `wait()`.

```
Figlio termina                    Padre non chiama wait()
     │                                   │
     ▼                                   ▼
Diventa Zombie (Z)                Entry rimane nella process table
  - Non consuma CPU               - Consuma solo un PID slot
  - Non consuma memoria           - Visibile in ps come <defunct>
  - Non ha codice in RAM          - Non eliminabile con SIGKILL
  - Ha solo la entry in task_struct
```

```bash
# Creare un zombie per dimostrazione didattica
bash -c 'sleep 60 & exec sleep 300'
# Il processo sleep 60 terminerà e diventerà zombie
# perché il padre (sleep 300) non fa wait()

# Identificare zombie
ps aux | awk '$8 ~ /Z/'
ps -eo pid,ppid,stat,comm | grep -w Z

# Contare zombie
awk '/^Zombie:/ {print $2}' /proc/loadavg    # No, non è qui
grep -c ' Z ' <(ps aux)

# Risolvere zombie:
# 1. Inviare SIGCHLD al padre
kill -SIGCHLD <PPID>

# 2. Se non funziona, il padre ha un bug — terminare il padre
kill <PPID>
# I figli zombie saranno adottati da PID 1 (systemd) che chiamerà wait()

# 3. Se il padre è un servizio critico: segnalare il bug, aggiornare il software
```

### Processi Orfani

Un processo orfano è un processo il cui padre è terminato. Il kernel riassegna automaticamente questi processi a PID 1 (systemd/init), che diventa il nuovo padre e si occupa di chiamare `wait()` quando terminano.

```
Padre (PID 100) ──fork()──> Figlio (PID 101)
      │                           │
      ▼                           │ (ancora in esecuzione)
  Padre termina                   │
                                  ▼
                          Figlio adottato da PID 1 (systemd)
                          PPID diventa 1
```

```bash
# Creare un orfano per dimostrazione
bash -c '(sleep 120 &); exit'
# La subshell termina, sleep 120 diventa orfano adottato da PID 1

# Verificare
ps -eo pid,ppid,comm | grep sleep
# Il PPID sarà 1 (systemd)
```

A differenza degli zombie, i processi orfani non sono un problema: systemd/init li gestisce correttamente. Sono un meccanismo di design, non un bug.

### Copy-on-Write (COW)

Quando `fork()` crea un figlio, il kernel non copia fisicamente tutta la memoria del padre. Usa il meccanismo Copy-on-Write: padre e figlio condividono le stesse pagine fisiche di memoria, marcate come read-only. Solo quando uno dei due tenta di scrivere su una pagina, il kernel ne crea una copia privata.

```
Dopo fork() — COW:
┌─────────────────────────┐
│   Pagine Fisiche        │
│  ┌─────┬─────┬─────┐   │
│  │ Pag1│ Pag2│ Pag3│   │  ← condivise, read-only
│  └──┬──┴──┬──┴──┬──┘   │
│     │     │     │       │
│  ┌──┴──┐┌─┴──┐┌─┴──┐   │
│  │Padre││Padre││Padre│  │  Page table padre
│  └─────┘└────┘└─────┘   │
│  ┌──┴──┐┌─┴──┐┌─┴──┐   │
│  │Figl.││Figl.││Figl.│  │  Page table figlio
│  └─────┘└────┘└─────┘   │
└─────────────────────────┘

Dopo che il figlio scrive su Pag2:
┌─────────────────────────┐
│   Pagine Fisiche        │
│  ┌─────┬─────┬─────┐   │
│  │ Pag1│ Pag2│ Pag3│   │  ← Pag1, Pag3 ancora condivise
│  └──┬──┴──┬──┴──┬──┘   │
│     │     │     │       │
│     │  ┌──┴──┐  │       │
│     │  │Pag2'│  │       │  ← copia privata del figlio
│     │  └─────┘  │       │
└─────────────────────────┘
```

Vantaggi del COW:
- `fork()` è veloce anche per processi con GB di memoria
- Processi che fanno fork()+exec() non copiano quasi nulla (exec() rimpiazza tutto)
- Riduce drasticamente l'uso di memoria per processi che condividono molto codice

---

## Stati dei Processi

### R — Running/Runnable

Il processo è in esecuzione su una CPU (running) oppure è in coda pronto per l'esecuzione (runnable). Solo un processo per CPU core può essere in stato running in un dato momento.

```bash
# Processi in stato R
ps -eo pid,stat,comm | grep '^.*R'
# Un sistema sano ha pochi processi R simultanei (≈ numero di core)
# Molti processi R = CPU contention
```

### S — Interruptible Sleep

Il processo è in attesa di un evento (I/O, timer, segnale, input utente). Può essere svegliato da un segnale. Questo è lo stato più comune per la maggior parte dei processi.

```bash
# La maggior parte dei processi in un sistema idle sono in stato S
ps -eo stat | sort | uniq -c | sort -rn
# Output tipico: centinaia di S, pochi R, zero o pochi Z
```

### D — Uninterruptible Sleep

Il processo è in attesa di I/O e NON può essere interrotto da segnali, nemmeno SIGKILL. Questo stato esiste per garantire la consistenza dei dati durante operazioni di I/O critiche.

```bash
# Processi in stato D — potenziale problema
ps -eo pid,stat,wchan,comm | grep '^.*D'

# Cause comuni:
# - Disco lento o guasto
# - NFS mount non raggiungibile
# - Operazioni su dispositivi a blocchi
# - Bug nel driver del kernel

# Un processo D non può essere ucciso — bisogna risolvere il problema I/O sottostante
```

### T — Stopped

Il processo è stato fermato, tipicamente da SIGSTOP, SIGTSTP (Ctrl+Z), o da un debugger (ptrace).

```bash
# Processi fermati
ps -eo pid,stat,comm | grep '^.*T'

# Riprendere un processo fermato
kill -SIGCONT <PID>
```

### Z — Zombie

Processo terminato il cui padre non ha ancora raccolto l'exit status con `wait()`. Vedi la sezione [Processi Zombie](#processi-zombie).

### X — Dead

Stato transitorio: il processo è stato completamente rimosso. Non dovrebbe mai apparire in `ps` perché è istantaneo. Se lo vedi, probabilmente c'è un bug nel kernel o nel tool di monitoraggio.

### Diagnosi dei Processi in Stato D

I processi in stato D (uninterruptible sleep) sono i più problematici: non possono essere uccisi con SIGKILL. Ecco la metodologia di diagnosi:

```bash
# 1. Identificare processi D
ps -eo pid,stat,wchan:30,comm | awk '$2 ~ /D/'

# 2. Controllare il wait channel (su cosa è bloccato)
cat /proc/<PID>/wchan
# Valori comuni:
# "nfs_wait_bit_killable" → NFS hang
# "blkdev_issue_flush"    → disco lento/guasto
# "io_schedule"           → I/O generico
# "rpc_wait_bit_killable" → RPC bloccato

# 3. Controllare lo stack del kernel
cat /proc/<PID>/stack
# Mostra la call stack nel kernel — indica esattamente dove è bloccato

# 4. Controllare dmesg per errori I/O
dmesg | grep -iE "error|fault|timeout|hung|blocked"

# 5. Controllare lo stato dei dischi
iostat -x 1 3
# %util vicino a 100% indica disco saturo

# 6. Controllare mount NFS
mount -t nfs
# Se c'è un NFS mount, verificare la raggiungibilità del server
showmount -e <nfs-server>

# 7. Il kernel logga processi bloccati per più di 120 secondi:
# "INFO: task <nome>:<pid> blocked for more than 120 seconds."
# Controllare: sysctl kernel.hung_task_timeout_secs

# Soluzione: risolvere il problema I/O sottostante
# - Disco guasto → sostituire
# - NFS hang → riparare/rimontare (mount -o remount,soft)
# - Driver bug → aggiornare kernel
```

---

## Il Filesystem /proc/[pid]

Il filesystem `/proc` è un filesystem virtuale (procfs) che espone informazioni del kernel in formato leggibile. Per ogni processo esiste una directory `/proc/[pid]/` con decine di file e sottodirectory.

```bash
# Struttura di /proc/[pid]/
ls -la /proc/self/    # self è un symlink al processo corrente
# File principali:
# cmdline    — Linea di comando
# comm       — Nome del comando (troncato a 16 char)
# cwd        — Symlink alla working directory
# environ    — Variabili d'ambiente
# exe        — Symlink all'eseguibile
# fd/        — Directory dei file descriptor
# fdinfo/    — Info su ogni file descriptor
# io         — Statistiche I/O
# limits     — Limiti risorse
# maps       — Mappatura memoria
# mem        — Memoria del processo (accesso diretto)
# mountinfo  — Info sui mount
# net/       — Statistiche di rete
# ns/        — Namespace (symlink)
# oom_adj    — OOM adjustment (deprecato)
# oom_score  — Score OOM killer
# oom_score_adj — OOM adjustment (-1000 a 1000)
# root       — Symlink alla root directory
# smaps      — Memoria dettagliata per mappatura
# stack      — Stack del kernel
# stat       — Statistiche raw (una riga)
# statm      — Statistiche memoria (compatte)
# status     — Stato leggibile
# task/      — Thread del processo
# wchan      — Wait channel nel kernel
```

### status — Stato del Processo

Il file più leggibile e informativo per un'analisi rapida del processo.

```bash
cat /proc/1/status
# Output tipico (campi principali):
# Name:    systemd               ← nome del comando
# Umask:   0000                  ← umask corrente
# State:   S (sleeping)          ← stato del processo
# Tgid:    1                     ← Thread Group ID (= PID per processi a thread singolo)
# Ngid:    0                     ← NUMA Group ID
# Pid:     1                     ← PID
# PPid:    0                     ← PID del padre (0 per init)
# TracerPid: 0                   ← PID del tracer (debugger), 0 se non tracciato
# Uid:     0  0  0  0            ← Real, Effective, Saved, Filesystem UID
# Gid:     0  0  0  0            ← Real, Effective, Saved, Filesystem GID
# FDSize:  256                   ← slot nella tabella FD
# Groups:                        ← gruppi supplementari
# NStgid:  1                     ← PID nel namespace corrente
# VmPeak:  235232 kB             ← picco di memoria virtuale
# VmSize:  170564 kB             ← memoria virtuale corrente
# VmLck:   0 kB                  ← memoria locked
# VmPin:   0 kB                  ← memoria pinned
# VmHWM:   13456 kB              ← picco di RSS (Resident Set Size)
# VmRSS:   13456 kB              ← RSS corrente (memoria fisica)
# RssAnon: 5200 kB               ← RSS anonimo (heap, stack)
# RssFile: 8256 kB               ← RSS file (librerie mappate)
# RssShmem: 0 kB                 ← RSS shared memory
# VmData:  20480 kB              ← dimensione segmento dati
# VmStk:   1024 kB               ← dimensione stack
# VmExe:   1440 kB               ← dimensione segmento testo
# VmLib:   9600 kB               ← librerie condivise
# VmPTE:   128 kB                ← page table entries
# Threads: 1                     ← numero di thread
# SigQ:    0/62767               ← segnali in coda / massimo
# SigPnd:  0000000000000000      ← segnali pendenti (thread)
# ShdPnd:  0000000000000000      ← segnali pendenti (processo)
# SigBlk:  7be3c0fe28014a03      ← segnali bloccati (maschera)
# SigIgn:  0000000000001000      ← segnali ignorati
# SigCgt:  00000001800004ec      ← segnali con handler registrato
# CapInh:  0000000000000000      ← capabilities ereditabili
# CapPrm:  000001ffffffffff      ← capabilities permesse
# CapEff:  000001ffffffffff      ← capabilities effettive
# CapBnd:  000001ffffffffff      ← capabilities bounding set
# CapAmb:  0000000000000000      ← capabilities ambient
# Seccomp: 0                     ← 0=disabilitato, 1=strict, 2=filter
# Cpus_allowed: ff               ← maschera CPU consentite
# Voluntary_ctxt_switches: 1234  ← context switch volontari
# Nonvoluntary_ctxt_switches: 56 ← context switch involontari
```

```bash
# Analisi rapida da script
# Memoria RSS di un processo (in kB)
awk '/VmRSS/ {print $2}' /proc/<PID>/status

# Numero di thread
awk '/Threads/ {print $2}' /proc/<PID>/status

# Stato
awk '/State/ {print $2}' /proc/<PID>/status

# UID effettivo
awk '/Uid/ {print $3}' /proc/<PID>/status
```

### stat — Statistiche Raw

Una singola riga con 52 campi separati da spazio. Usato da tool come `top`, `ps`, `htop` per estrarre dati in modo efficiente.

```bash
cat /proc/self/stat
# Campi principali (posizione):
# 1:  PID
# 2:  (comm) — nome comando tra parentesi
# 3:  state — singolo carattere (R, S, D, Z, T, ...)
# 4:  ppid — PID del padre
# 5:  pgrp — process group
# 6:  session — session ID
# 7:  tty_nr — terminale
# 10: minflt — minor page fault (pagina in memoria, non nel TLB)
# 12: majflt — major page fault (pagina su disco, caricata in RAM)
# 14: utime — tempo CPU in user mode (in clock ticks)
# 15: stime — tempo CPU in kernel mode
# 19: nice — nice value
# 20: num_threads — numero di thread
# 22: starttime — tempo di avvio (in clock ticks dal boot)
# 23: vsize — memoria virtuale in byte
# 24: rss — resident set size in pagine

# Calcolare il tempo CPU di un processo in secondi
CLK_TCK=$(getconf CLK_TCK)   # tipicamente 100
read _ _ _ _ _ _ _ _ _ _ _ _ _ utime stime < /proc/<PID>/stat
echo "CPU time: $(( (utime + stime) / CLK_TCK )) secondi"
```

### maps — Mappatura Memoria

Mostra tutte le regioni di memoria virtuale del processo: codice, librerie, heap, stack, file mappati.

```bash
cat /proc/self/maps
# Formato:
# indirizzo        perms offset  dev   inode  pathname
# 55a000000000-55a000001000 r--p 00000000 08:02 1234 /usr/bin/bash
# 55a000001000-55a000050000 r-xp 00001000 08:02 1234 /usr/bin/bash  ← codice
# 55a000050000-55a000060000 r--p 00050000 08:02 1234 /usr/bin/bash  ← read-only data
# 55a000060000-55a000063000 rw-p 00060000 08:02 1234 /usr/bin/bash  ← dati rw
# 55a000200000-55a000400000 rw-p 00000000 00:00 0    [heap]
# 7f0000000000-7f0000200000 r--p 00000000 08:02 5678 /lib/x86_64-linux-gnu/libc.so.6
# ...
# 7ffff0000000-7ffff0021000 rw-p 00000000 00:00 0    [stack]
# 7ffff0300000-7ffff0302000 r--p 00000000 00:00 0    [vvar]
# 7ffff0302000-7ffff0304000 r-xp 00000000 00:00 0    [vdso]

# Permessi:
# r = read, w = write, x = execute, p = private (COW), s = shared

# Cercare librerie caricate da un processo
grep '\.so' /proc/<PID>/maps

# Cercare regioni di memoria scrivibili ed eseguibili (sospette per sicurezza)
grep 'rwx' /proc/<PID>/maps
```

### fd — File Descriptor

Directory che contiene un symlink per ogni file descriptor aperto dal processo.

```bash
ls -la /proc/<PID>/fd/
# 0 -> /dev/pts/1     ← stdin
# 1 -> /dev/pts/1     ← stdout
# 2 -> /dev/pts/1     ← stderr
# 3 -> /var/log/app.log
# 4 -> socket:[12345]
# 5 -> pipe:[67890]
# 6 -> anon_inode:[eventpoll]   ← epoll fd

# Contare file descriptor aperti
ls /proc/<PID>/fd/ | wc -l

# Controllare il tipo di un fd specifico
readlink /proc/<PID>/fd/3

# Trovare processi con troppi fd aperti (possibile file descriptor leak)
for pid in /proc/[0-9]*/; do
    count=$(ls "$pid/fd/" 2>/dev/null | wc -l)
    if [ "$count" -gt 1000 ]; then
        comm=$(cat "$pid/comm" 2>/dev/null)
        echo "PID ${pid##/proc/}: $count fd ($comm)"
    fi
done

# Info dettagliate su un fd
cat /proc/<PID>/fdinfo/3
# pos:    0          ← posizione nel file
# flags:  0100002    ← flag di apertura (O_RDWR | O_CLOEXEC)
# mnt_id: 25         ← mount ID
```

### environ — Variabili d'Ambiente

Contiene tutte le variabili d'ambiente del processo, separate da byte null (\0).

```bash
# Leggere le variabili d'ambiente di un processo
cat /proc/<PID>/environ | tr '\0' '\n'

# Cercare una variabile specifica
cat /proc/<PID>/environ | tr '\0' '\n' | grep '^PATH='
cat /proc/<PID>/environ | tr '\0' '\n' | grep '^HOME='

# Nota: le variabili sono quelle impostate all'avvio del processo.
# Modifiche successive (es. export VAR=val nel processo) non si riflettono qui.

# Utilissimo per capire come è stato avviato un processo:
# - Quale PATH usa?
# - Ha variabili custom (DATABASE_URL, API_KEY)?
# - È in un virtualenv (VIRTUAL_ENV)?
```

### cmdline — Linea di Comando

Contiene gli argomenti passati al processo, separati da byte null.

```bash
# Linea di comando completa
cat /proc/<PID>/cmdline | tr '\0' ' '
echo  # aggiungere newline

# Utile per distinguere processi con lo stesso nome:
# ps mostra "python" ma cmdline mostra "python /usr/local/bin/gunicorn --workers 4"

# Nota: i processi possono modificare argv[] (es. prctl(PR_SET_NAME))
# Quindi cmdline può non corrispondere a quello che ps mostra
```

### limits — Limiti Risorse

Mostra i limiti di risorse (ulimit) effettivi del processo.

```bash
cat /proc/<PID>/limits
# Limit                     Soft Limit   Hard Limit   Units
# Max cpu time              unlimited    unlimited    seconds
# Max file size             unlimited    unlimited    bytes
# Max data size             unlimited    unlimited    bytes
# Max stack size            8388608      unlimited    bytes       ← 8 MB
# Max core file size        0            unlimited    bytes       ← core dump disabilitato
# Max resident set          unlimited    unlimited    bytes
# Max processes             62767        62767        processes
# Max open files            1024         1048576      files       ← soft=1024!
# Max locked memory         8388608      8388608      bytes       ← 8 MB
# Max address space         unlimited    unlimited    bytes
# Max file locks            unlimited    unlimited    locks
# Max pending signals       62767        62767        signals
# Max msgqueue size         819200       819200       bytes
# Max nice priority         0            0
# Max realtime priority     0            0
# Max realtime timeout      unlimited    unlimited    us

# NOTA CRITICA: "Max open files" soft limit = 1024 è il default
# Molte applicazioni (database, web server) necessitano di aumentarlo
# Vedere la sezione ulimit per come modificarlo
```

### oom_score e oom_score_adj

L'OOM (Out-of-Memory) killer interviene quando il sistema esaurisce la memoria. Uccide il processo con il punteggio OOM più alto.

```bash
# oom_score: punteggio calcolato dal kernel (0-1000+)
# Più alto = più probabilità di essere ucciso
cat /proc/<PID>/oom_score

# oom_score_adj: regolazione manuale (-1000 a 1000)
# -1000 = mai ucciso dall'OOM killer
# 0     = default
# 1000  = ucciso per primo
cat /proc/<PID>/oom_score_adj

# Proteggere un processo critico dall'OOM killer
echo -1000 | sudo tee /proc/<PID>/oom_score_adj

# Marcare un processo come sacrificabile
echo 500 | sudo tee /proc/<PID>/oom_score_adj

# In systemd (persistente):
# [Service]
# OOMScoreAdjust=-1000

# Fattori che influenzano oom_score:
# - Uso di memoria RSS (più RAM = score più alto)
# - oom_score_adj
# - Processi root hanno un leggero bonus (meno probabile)
# - Processi di lunga durata hanno un leggero bonus

# Controllare quale processo sarebbe ucciso per primo
for pid in /proc/[0-9]*/; do
    score=$(cat "$pid/oom_score" 2>/dev/null)
    comm=$(cat "$pid/comm" 2>/dev/null)
    [ -n "$score" ] && echo "$score $pid $comm"
done | sort -rn | head -10
```

### cgroup — Appartenenza cgroup

```bash
# Mostra la gerarchia cgroup del processo
cat /proc/<PID>/cgroup
# Output cgroups v2 (unified):
# 0::/user.slice/user-1000.slice/session-2.scope
# Output cgroups v1 (legacy):
# 12:memory:/user.slice/user-1000.slice
# 11:cpu,cpuacct:/user.slice/user-1000.slice
# ...
```

### io — Statistiche I/O

```bash
cat /proc/<PID>/io
# rchar:     1234567   ← byte letti (include cache)
# wchar:     2345678   ← byte scritti (include cache)
# syscr:     456       ← numero di read syscall
# syscw:     789       ← numero di write syscall
# read_bytes:  123456  ← byte effettivamente letti da disco
# write_bytes: 234567  ← byte effettivamente scritti su disco
# cancelled_write_bytes: 0

# Per trovare il processo che fa più I/O su disco:
for pid in /proc/[0-9]*/; do
    rb=$(awk '/read_bytes/ {print $2}' "$pid/io" 2>/dev/null)
    wb=$(awk '/write_bytes/ {print $2}' "$pid/io" 2>/dev/null)
    comm=$(cat "$pid/comm" 2>/dev/null)
    [ -n "$rb" ] && echo "$((rb + wb)) ${pid##/proc/} $comm"
done | sort -rn | head -10
```

### smaps — Memoria Dettagliata

Versione dettagliata di `maps` con informazioni sulla memoria per ogni regione.

```bash
# smaps è grande — usare smaps_rollup per un sommario
cat /proc/<PID>/smaps_rollup
# Rss:            13456 kB   ← memoria fisica
# Pss:            10234 kB   ← Proportional Set Size (RSS / n_condivisori)
# Shared_Clean:    5000 kB   ← condivisa e non modificata
# Shared_Dirty:     200 kB   ← condivisa e modificata
# Private_Clean:   3000 kB   ← privata e non modificata
# Private_Dirty:   5256 kB   ← privata e modificata
# Swap:               0 kB   ← in swap
# SwapPss:            0 kB   ← swap proporzionale

# PSS (Proportional Set Size) è la metrica più utile:
# Se una libreria è condivisa da 10 processi, ogni processo
# "possiede" 1/10 della memoria di quella libreria
```

### stack — Stack del Kernel

```bash
# Mostra lo stack trace del kernel per il processo
sudo cat /proc/<PID>/stack
# [<ffffffff811234>] futex_wait_queue_me+0xc0/0x120
# [<ffffffff811240>] futex_wait+0x100/0x240
# [<ffffffff811250>] do_futex+0x80/0x500
# [<ffffffff811260>] sys_futex+0x70/0x150

# Utilissimo per capire cosa sta facendo un processo bloccato
# Specialmente per processi in stato D (uninterruptible sleep)
```

### wchan — Wait Channel

```bash
# Su cosa sta aspettando il processo
cat /proc/<PID>/wchan
# Valori comuni:
# do_wait           → wait() su un processo figlio
# poll_schedule_timeout → poll/select/epoll
# futex_wait_queue_me → mutex/condvar
# ep_poll           → epoll_wait
# pipe_read         → lettura da pipe
# unix_stream_read_generic → lettura da unix socket
# io_schedule       → I/O disco

# Nessun output (vuoto o "0") = processo in esecuzione (stato R)
```

### ns — Namespace

```bash
# Symlink ai namespace del processo
ls -la /proc/<PID>/ns/
# cgroup -> cgroup:[4026531835]
# ipc    -> ipc:[4026531839]
# mnt    -> mnt:[4026531841]
# net    -> net:[4026532008]
# pid    -> pid:[4026531836]
# pid_for_children -> pid_for_children:[4026531836]
# user   -> user:[4026531837]
# uts    -> uts:[4026531838]

# I numeri tra parentesi sono inode del namespace
# Processi nello stesso namespace hanno lo stesso numero
# Entrare nel namespace di un altro processo:
sudo nsenter --target <PID> --mount --uts --ipc --net --pid -- /bin/bash
```

---

## Processi: Fondamenti, PID, PPID

### Ciclo di Vita

```
fork() → exec() → [running] → exit()
                     ↕
              [sleeping/stopped]

Stati dei processi (colonna STAT in ps):
  R  Running / Runnable (in esecuzione o in coda CPU)
  S  Sleeping (interruptible, in attesa di evento)
  D  Uninterruptible sleep (tipicamente I/O disco)
  T  Stopped (fermato da segnale o debugger)
  Z  Zombie (terminato ma il padre non ha letto l'exit status)
  I  Idle (kernel thread)

Suffissi STAT:
  < = alta priorità     N = bassa priorità
  s = session leader     l = multi-threaded
  + = foreground process group
```

### Comandi ps

```bash
# Visualizzare processi
ps aux                              # Tutti i processi (stile BSD)
ps -ef                              # Tutti i processi (stile POSIX)
ps -eo pid,ppid,user,%cpu,%mem,stat,start,time,comm --sort=-%cpu  # Custom
ps -eo pid,ppid,user,%mem,rss,comm --sort=-rss | head -20  # Top memoria

# Albero processi
ps axjf                             # Albero (forest)
pstree                              # Albero compatto
pstree -p                           # Con PID
pstree -u user                      # Processi di un utente

# Processi specifici
ps -p 1234                          # Per PID
ps -u root                          # Per utente
ps -C nginx                        # Per nome comando

# Informazioni processo dal /proc
cat /proc/PID/status                # Stato completo
cat /proc/PID/cmdline | tr '\0' ' ' # Linea di comando
cat /proc/PID/environ | tr '\0' '\n' # Variabili d'ambiente
ls -la /proc/PID/fd/               # File descriptor aperti
cat /proc/PID/limits               # Limiti risorse
ls -la /proc/PID/cwd               # Working directory
ls -la /proc/PID/exe               # Eseguibile
```

### Relazioni tra Processi

```bash
# PID 1 = systemd (init), padre di tutti i processi
# PPID = Parent PID
# PGID = Process Group ID (gruppo di processi, es. pipeline)
# SID = Session ID (sessione, tipicamente il terminale)

# Orfani: se il padre muore, il processo viene adottato da PID 1 (systemd)
# Zombie: il processo è terminato ma il padre non ha chiamato wait()
#         visibili come <defunct> in ps, stato Z

# Trovare zombie
ps aux | awk '$8=="Z"'
# Il padre del zombie (PPID) è responsabile — segnalare il bug al padre
```

---

## Segnali — Deep Dive

I segnali sono notifiche asincrone inviate a un processo. Sono il meccanismo fondamentale di comunicazione tra kernel e processi, e tra processi.

### Tutti i 31 Segnali Standard

| Num | Nome | Default | Descrizione |
|-----|------|---------|-------------|
| 1 | SIGHUP | Termina | Hangup — terminale chiuso. Usato dai daemon per reload config |
| 2 | SIGINT | Termina | Interrupt (Ctrl+C) |
| 3 | SIGQUIT | Core dump | Quit (Ctrl+\\) — termina con core dump |
| 4 | SIGILL | Core dump | Istruzione illegale (CPU instruction non valida) |
| 5 | SIGTRAP | Core dump | Trap — usato dai debugger (breakpoint) |
| 6 | SIGABRT | Core dump | Abort — chiamato da abort() per errori fatali |
| 7 | SIGBUS | Core dump | Bus error — accesso a memoria con allineamento errato |
| 8 | SIGFPE | Core dump | Floating Point Exception — divisione per zero, overflow |
| 9 | SIGKILL | Termina | Kill forzato — NON intercettabile, NON ignorabile |
| 10 | SIGUSR1 | Termina | User-defined 1 — uso libero per l'applicazione |
| 11 | SIGSEGV | Core dump | Segmentation Fault — accesso a memoria non valida |
| 12 | SIGUSR2 | Termina | User-defined 2 — uso libero per l'applicazione |
| 13 | SIGPIPE | Termina | Pipe rotta — scrittura su pipe senza lettore |
| 14 | SIGALRM | Termina | Alarm — timer scaduto (da alarm() o setitimer()) |
| 15 | SIGTERM | Termina | Terminazione gentile — default di kill. Intercettabile |
| 16 | SIGSTKFLT | Termina | Stack fault (obsoleto, non usato su Linux moderno) |
| 17 | SIGCHLD | Ignora | Child changed — figlio terminato o fermato |
| 18 | SIGCONT | Continua | Riprendi processo fermato |
| 19 | SIGSTOP | Ferma | Stop forzato — NON intercettabile, NON ignorabile |
| 20 | SIGTSTP | Ferma | Stop da terminale (Ctrl+Z) — intercettabile |
| 21 | SIGTTIN | Ferma | Background process tenta di leggere dal terminale |
| 22 | SIGTTOU | Ferma | Background process tenta di scrivere sul terminale |
| 23 | SIGURG | Ignora | Urgent data su socket (out-of-band) |
| 24 | SIGXCPU | Core dump | CPU time limit exceeded |
| 25 | SIGXFSZ | Core dump | File size limit exceeded |
| 26 | SIGVTALRM | Termina | Virtual alarm (timer di tempo CPU virtuale) |
| 27 | SIGPROF | Termina | Profiling timer |
| 28 | SIGWINCH | Ignora | Window size changed (resize terminale) |
| 29 | SIGIO/SIGPOLL | Termina | I/O now possible / Pollable event |
| 30 | SIGPWR | Termina | Power failure (UPS) |
| 31 | SIGSYS | Core dump | Bad system call (syscall non valida, usato da seccomp) |

```bash
# Elencare tutti i segnali disponibili
kill -l

# Segnali NON intercettabili e NON ignorabili:
# SIGKILL (9) e SIGSTOP (19) — il kernel li gestisce direttamente
# Non possono avere handler custom, non possono essere bloccati

# Lista segnali con numeri
kill -l | tr ' ' '\n' | nl

# Usi comuni di segnali custom:
# SIGUSR1 per nginx: riapertura dei log file
kill -USR1 $(cat /var/run/nginx.pid)

# SIGHUP per molti daemon: ricarica configurazione
kill -HUP $(pidof sshd)

# SIGQUIT per Java: thread dump (non termina il processo!)
kill -QUIT <java_pid>

# SIGUSR2 per gunicorn: graceful restart
kill -USR2 $(cat /var/run/gunicorn.pid)
```

### Segnali Real-Time

I segnali standard (1-31) hanno limitazioni: non sono accodati (se invii SIGUSR1 due volte mentre è bloccato, ne arriva uno solo) e non portano dati. I segnali real-time (SIGRTMIN a SIGRTMAX, tipicamente 34-64) risolvono questi problemi.

```bash
# Range segnali real-time
echo "SIGRTMIN=$(kill -l SIGRTMIN 2>/dev/null || echo 34)"
echo "SIGRTMAX=$(kill -l SIGRTMAX 2>/dev/null || echo 64)"

# Proprietà dei segnali real-time:
# 1. Sono accodati: invii multipli = consegne multiple
# 2. Portano dati: siginfo_t include si_value (int o pointer)
# 3. Ordinamento garantito: numeri più bassi hanno priorità più alta
# 4. SIGRTMIN+0 < SIGRTMIN+1 < ... (ordine di consegna)

# Inviare un segnale real-time
kill -SIGRTMIN+2 <PID>
kill -36 <PID>              # Se SIGRTMIN=34, allora SIGRTMIN+2=36

# systemd usa segnali real-time per il controllo di unit:
# SIGRTMIN+3: systemd-logind, richiesta poweroff
```

### signal() vs sigaction()

Due interfacce per registrare signal handler. `sigaction()` è quella corretta da usare; `signal()` ha comportamento non portabile.

```c
/* signal() — DEPRECATO per codice nuovo */
/* Problemi:
 * - Comportamento diverso tra Unix e Linux
 * - Su alcuni sistemi, l'handler viene resettato dopo la prima invocazione
 * - Race condition tra consegna del segnale e ri-registrazione dell'handler
 */
signal(SIGTERM, my_handler);  /* NON usare in codice nuovo */

/* sigaction() — CORRETTO */
struct sigaction sa;
sa.sa_handler = my_handler;        /* oppure sa.sa_sigaction per SA_SIGINFO */
sigemptyset(&sa.sa_mask);          /* nessun segnale bloccato durante l'handler */
sa.sa_flags = SA_RESTART;          /* riavvia syscall interrotte */
/* sa.sa_flags |= SA_SIGINFO;      per ricevere info extra (siginfo_t) */
/* sa.sa_flags |= SA_NOCLDSTOP;    SIGCHLD solo per terminazione, non per stop */

if (sigaction(SIGTERM, &sa, NULL) == -1) {
    perror("sigaction");
    exit(1);
}

/* SA_RESTART è importante: senza, una read() interrotta da un segnale
 * ritorna EINTR e il programma deve ri-tentare manualmente */
```

### Signal Masking

Un processo può bloccare (mascherare) la consegna di segnali. I segnali bloccati rimangono pendenti e vengono consegnati quando sbloccati.

```c
/* Bloccare SIGINT durante una sezione critica */
sigset_t block_set, old_set;
sigemptyset(&block_set);
sigaddset(&block_set, SIGINT);
sigaddset(&block_set, SIGTERM);

/* Blocca SIGINT e SIGTERM */
sigprocmask(SIG_BLOCK, &block_set, &old_set);

/* ... sezione critica: SIGINT/SIGTERM sono pendenti, non consegnati ... */

/* Sblocca — i segnali pendenti vengono consegnati ora */
sigprocmask(SIG_SETMASK, &old_set, NULL);

/* In un thread: usare pthread_sigmask() al posto di sigprocmask() */
```

```bash
# Verificare i segnali bloccati/pendenti/ignorati di un processo
grep Sig /proc/<PID>/status
# SigPnd: 0000000000000000  ← segnali pendenti (thread)
# ShdPnd: 0000000000000000  ← segnali pendenti (processo/shared)
# SigBlk: 7be3c0fe28014a03  ← segnali bloccati
# SigIgn: 0000000000001000  ← segnali ignorati
# SigCgt: 00000001800004ec  ← segnali con handler

# Decodificare la maschera (es. SigBlk):
python3 -c "
mask = 0x7be3c0fe28014a03
import signal
for i in range(1, 65):
    if mask & (1 << (i-1)):
        try:
            name = signal.Signals(i).name
        except (ValueError, AttributeError):
            name = f'RT_{i}'
        print(f'  Segnale {i}: {name} [BLOCCATO]')
"
```

### Comandi kill, killall, pkill

```bash
# Inviare segnali
kill PID                            # SIGTERM (default, terminazione gentile)
kill -15 PID                        # SIGTERM esplicito
kill -9 PID                         # SIGKILL (terminazione forzata, ultimo resort)
kill -1 PID                         # SIGHUP (reload configurazione per molti demoni)

# Per nome
killall nginx                       # SIGTERM a tutti i processi "nginx"
killall -9 nginx                    # SIGKILL a tutti
pkill nginx                         # Pattern matching (anche nome parziale)
pkill -f "python script.py"         # Match su intera linea di comando
pkill -u user                       # Tutti i processi dell'utente

# Ordine corretto per terminare un processo:
# 1. kill PID (SIGTERM) — dà tempo per cleanup
# 2. Aspettare qualche secondo
# 3. kill -9 PID (SIGKILL) — solo se SIGTERM non funziona

# Segnali multipli
kill -0 PID                         # Verifica se il processo esiste (no segnale)

# kill a un gruppo di processi (processo group leader e tutti i suoi membri)
kill -SIGTERM -<PGID>               # Nota il segno meno davanti al PGID

# Terminare tutti i processi di un utente (PERICOLOSO)
pkill -9 -u <username>

# Trovare e uccidere con un solo comando
pkill -9 -f "python.*myscript"      # Regex sulla cmdline completa
```

### Gestione Segnali nello Scripting

```bash
#!/bin/bash
# Trap: gestire segnali nel proprio script
cleanup() {
    echo "Pulizia in corso..."
    rm -f /tmp/myapp.lock
    exit 0
}

trap cleanup SIGTERM SIGINT         # Esegui cleanup su TERM e INT
trap "" SIGHUP                      # Ignora SIGHUP
trap cleanup EXIT                   # Esegui cleanup all'uscita (qualsiasi)

echo $$ > /tmp/myapp.pid            # Salva il proprio PID
while true; do
    # ... lavoro ...
    sleep 1
done
```

```bash
#!/bin/bash
# Esempio avanzato: gestire segnali in uno script con processi figli

PIDS=()

cleanup() {
    echo "Terminazione processi figli..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null
    done
    wait
    rm -f /tmp/myapp.lock
    echo "Cleanup completato."
    exit 0
}

trap cleanup SIGTERM SIGINT EXIT

# Avviare worker in background
for i in {1..4}; do
    (
        trap "" SIGINT     # i figli ignorano SIGINT (lo gestisce il padre)
        while true; do
            echo "Worker $i attivo"
            sleep 5
        done
    ) &
    PIDS+=($!)
done

echo "Padre PID: $$, Figli: ${PIDS[*]}"
wait

# Trap avanzati:
# trap 'echo "SIGHUP ricevuto, reload config"; source /etc/myapp.conf' HUP
# trap 'echo "SIGUSR1: incremento log level"; LOG_LEVEL=$((LOG_LEVEL+1))' USR1
# trap 'echo "SIGUSR2: dump stato"; dump_state > /tmp/myapp.state' USR2
```

---

## Priorità: nice e renice

Linux usa una scala di priorità da -20 (massima) a 19 (minima). Il default è 0. Solo root può impostare priorità negative.

```bash
# Avviare un processo con priorità specifica
nice -n 10 ./backup.sh              # Bassa priorità (10)
nice -n -5 ./critical-task          # Alta priorità (-5, richiede root)
nice -n 19 ./background-job         # Minima priorità

# Cambiare priorità a processo esistente
renice 10 -p 1234                   # Cambia PID 1234 a priorità 10
sudo renice -5 -p 1234             # Priorità alta (richiede root)
renice 15 -u username              # Tutti i processi dell'utente
renice 10 -g groupname             # Tutti i processi del gruppo

# Verificare
ps -eo pid,ni,comm --sort=ni       # Lista con nice value
top                                 # Colonna NI
```

### Scheduler Real-Time

```bash
# Per processi con requisiti real-time
# SCHED_FIFO: first-in-first-out real-time
# SCHED_RR: round-robin real-time

chrt -f 50 ./realtime-app           # FIFO con priorità 50
chrt -r 50 ./realtime-app           # Round-robin con priorità 50
chrt -p PID                         # Mostra policy corrente
sudo chrt -f -p 50 PID             # Cambia policy a processo esistente
```

---

## Scheduling — Internals

### CFS — Completely Fair Scheduler

Il CFS (Completely Fair Scheduler) è lo scheduler di default del kernel Linux dal 2.6.23 (2007). Il principio è semplice: dare a ogni processo una quota equa di CPU proporzionale al suo peso (determinato dal nice value).

```
Concetto chiave: vruntime (virtual runtime)

Ogni processo ha un contatore vruntime che traccia quanto tempo CPU "virtuale"
ha consumato. Il CFS sceglie sempre il processo con il vruntime più basso
(quello che ha usato meno CPU rispetto alla sua quota).

vruntime cresce più lentamente per processi con nice negativo (alta priorità)
e più velocemente per processi con nice positivo (bassa priorità).

Implementazione: Red-Black Tree
┌─────────────────────────────┐
│        Red-Black Tree       │
│         (ordinato per       │
│          vruntime)          │
│                             │
│    ┌───┐                    │
│    │ 50│ ← nodo con vruntime più basso (prossimo da eseguire)
│    └─┬─┘                    │
│   ┌──┴──┐                   │
│   │     │                   │
│ ┌─┴─┐ ┌─┴─┐                │
│ │100│ │200│                 │
│ └───┘ └───┘                 │
└─────────────────────────────┘

Il nodo più a sinistra (vruntime minimo) è il prossimo processo da schedulare.
Inserimento/rimozione: O(log n).
```

```bash
# Parametri CFS tunable (per esperti):
# /proc/sys/kernel/sched_min_granularity_ns
#   Tempo minimo che un processo può eseguire prima di essere preempted
#   Default: 750000 (0.75 ms) — valori più alti = meno context switch

# /proc/sys/kernel/sched_latency_ns
#   Periodo di scheduling — il tempo entro cui ogni processo runnable
#   dovrebbe eseguire almeno una volta
#   Default: 6000000 (6 ms)

# /proc/sys/kernel/sched_wakeup_granularity_ns
#   Soglia per preemptare un processo corrente quando se ne sveglia uno
#   con vruntime più basso. Più alto = meno preemption = più throughput
#   Default: 1000000 (1 ms)

# Visualizzare i parametri
sysctl kernel.sched_min_granularity_ns
sysctl kernel.sched_latency_ns

# Nota: dal kernel 6.6, EEVDF (Earliest Eligible Virtual Deadline First)
# ha sostituito CFS come scheduler di default. Il concetto di vruntime
# e nice value rimane valido; EEVDF aggiunge deadline per migliore latenza.
```

Relazione tra nice value e peso nel CFS:

```
Nice Value    Peso      % CPU (2 processi)
-20           88761     ~95% vs nice 0
-10            9548     ~91% vs nice 0
 -5            3121     ~76% vs nice 0
  0            1024     ~50% vs nice 0
  5             335     ~24% vs nice 0
 10             110     ~10% vs nice 0
 19              15     ~1.5% vs nice 0

Ogni livello di nice = ~1.25x differenza di peso.
Da nice 0 a nice 1: il peso scende da 1024 a 820 (~-20%).
```

### nice e renice — Priorità Utente

```bash
# Relazione tra nice e priority interna del kernel:
# priority = 120 + nice
# Range priority: 100 (nice -20) a 139 (nice 19)
# Le priority 0-99 sono riservate per scheduling real-time

# Mostrare nice value e priority
ps -eo pid,ni,pri,comm --sort=-pri | head -20

# Chi può cambiare nice value?
# - Qualsiasi utente può AUMENTARE il nice (abbassare priorità)
# - Solo root può DIMINUIRE il nice (alzare priorità, nice negativo)
# - L'hard limit di nice è configurabile in /etc/security/limits.conf

# Configurare limiti nice per utente
# /etc/security/limits.conf:
# username  hard  nice  -10
# @devgroup soft  nice  -5

# Autonice in bash: rendere il processo corrente a bassa priorità
renice -n 19 -p $$ >/dev/null 2>&1
```

### ionice — Priorità I/O

`ionice` controlla la classe e la priorità di I/O di un processo nello scheduler I/O del kernel.

```bash
# Classi I/O (CFQ scheduler):
# 0 = none (usa il default della classe best-effort)
# 1 = Realtime  — accesso I/O prioritario, 8 livelli (0-7, 0=massimo)
# 2 = Best-effort — default, 8 livelli (0-7)
# 3 = Idle — I/O solo quando nessun altro processo fa I/O

# Avviare un processo con classe I/O
ionice -c 3 ./backup.sh             # Idle — non impatta altri processi
ionice -c 2 -n 7 ./batch-job        # Best-effort, bassa priorità
ionice -c 1 -n 0 ./database         # Realtime, massima priorità (root)

# Cambiare classe I/O a processo esistente
ionice -c 3 -p <PID>                # Sposta a idle

# Combinare nice e ionice per task in background
nice -n 19 ionice -c 3 rsync -av /src /dst

# Verificare classe I/O corrente
ionice -p <PID>
# Output: best-effort: prio 4

# Nota: con lo scheduler mq-deadline o none (NVMe), ionice ha effetto limitato.
# Verificare lo scheduler in uso:
cat /sys/block/sda/queue/scheduler
# [mq-deadline] none
```

### chrt — Scheduling Real-Time

```bash
# Policy di scheduling disponibili:
# SCHED_OTHER (0)     — default, CFS/EEVDF, nice values
# SCHED_FIFO  (1)     — real-time FIFO, priorità 1-99
# SCHED_RR    (2)     — real-time round-robin, priorità 1-99
# SCHED_BATCH (3)     — batch processing, ottimizzato per throughput
# SCHED_IDLE  (5)     — priorità minima assoluta
# SCHED_DEADLINE (6)  — deadline-based, più recente

# Mostrare la policy corrente
chrt -p <PID>
# pid 1234's current scheduling policy: SCHED_OTHER
# pid 1234's current scheduling priority: 0

# Impostare SCHED_FIFO con priorità 50
sudo chrt -f 50 ./myapp
sudo chrt -f -p 50 <PID>           # Su processo esistente

# SCHED_RR con priorità 25
sudo chrt -r 25 ./myapp

# SCHED_BATCH
chrt -b 0 ./batch-process

# SCHED_IDLE
chrt -i 0 ./idle-process

# Limiti di priorità real-time
chrt --max
# SCHED_OTHER min/max priority  : 0/0
# SCHED_FIFO  min/max priority  : 1/99
# SCHED_RR    min/max priority  : 1/99
# SCHED_BATCH min/max priority  : 0/0
# SCHED_IDLE  min/max priority  : 0/0
# SCHED_DEADLINE min/max priority : 0/0
```

### SCHED_FIFO, SCHED_RR, SCHED_DEADLINE

```
SCHED_FIFO (First-In, First-Out Real-Time):
─────────────────────────────────────────
- Priorità fissa (1-99): nessun time-slicing
- Un processo FIFO esegue finché:
  1. Si blocca volontariamente (I/O, sleep, yield)
  2. Viene preemptato da un processo con priorità più alta
  3. Termina
- PERICOLO: un processo FIFO con priorità alta che non si blocca
  mai può AFFAMARE tutti gli altri processi, inclusa la shell!

SCHED_RR (Round-Robin Real-Time):
─────────────────────────────────
- Come FIFO, ma con time-slice
- Processi con la stessa priorità si alternano (round-robin)
- Il time-slice default: 100 ms (leggibile da /proc/sys/kernel/sched_rr_timeslice_ms)
- Più sicuro di FIFO: un processo non può monopolizzare una CPU

SCHED_DEADLINE:
───────────────
- Il più avanzato: basato su tre parametri:
  - runtime:  tempo di esecuzione garantito per periodo
  - deadline: tempo entro cui il runtime deve completare
  - period:   intervallo di ripetizione
- Esempio: "Ho bisogno di 10ms di CPU ogni 30ms, completati entro 20ms"
  sudo chrt -d --sched-runtime 10000000 --sched-deadline 20000000 \
            --sched-period 30000000 0 ./rt-app
- Ha la priorità più alta di tutti: preempta FIFO e RR
- Auto-throttling: se il processo supera il suo runtime, viene sospeso
```

```bash
# ATTENZIONE: scheduling real-time senza limiti può rendere il sistema inutilizzabile

# Protezione: riservare CPU per processi non-RT
# /proc/sys/kernel/sched_rt_period_us   = 1000000 (1 secondo)
# /proc/sys/kernel/sched_rt_runtime_us  = 950000  (950 ms)
# → processi RT possono usare max 95% del periodo. Il 5% è riservato.

sysctl kernel.sched_rt_runtime_us
# -1 = nessun limite (pericoloso)

# Per sistemi audio/video real-time:
# Aggiungere l'utente al gruppo realtime e configurare /etc/security/limits.conf:
# @audio   -  rtprio     95
# @audio   -  memlock    unlimited
```

### CPU Affinity — taskset

Lega un processo a CPU specifiche. Utile per isolare carichi, ridurre context switch, migliorare cache locality.

```bash
# Mostrare l'affinità CPU corrente
taskset -p <PID>
# pid 1234's current affinity mask: ff   (tutte le 8 CPU)

# Avviare un processo su CPU specifiche
taskset -c 0,1 ./myapp              # Solo CPU 0 e 1
taskset -c 0-3 ./myapp              # CPU da 0 a 3
taskset 0x03 ./myapp                # Maschera: CPU 0 e 1 (bit 0 e 1)

# Cambiare affinità a processo esistente
taskset -p -c 2,3 <PID>             # Sposta su CPU 2 e 3

# Esempio pratico: isolare un database su CPU dedicate
# 1. Identificare le CPU NUMA-aware
numactl --hardware
# 2. Legare il database alle CPU del nodo NUMA corretto
taskset -c 0-7 /usr/bin/postgres

# Isolare CPU dal kernel scheduler (kernel boot parameter):
# isolcpus=4,5,6,7
# Queste CPU non riceveranno processi automaticamente,
# solo quelli esplicitamente assegnati con taskset/cgroup
```

---

## cgroups v2

I cgroups (control groups) sono un meccanismo del kernel per organizzare processi in gruppi gerarchici e applicare limiti di risorse, accounting e controllo.

### Architettura cgroups v2

```
cgroups v1 vs v2:
─────────────────
v1: Multiple gerarchie, un controller per gerarchia
    /sys/fs/cgroup/cpu/
    /sys/fs/cgroup/memory/
    /sys/fs/cgroup/blkio/
    Problema: un processo poteva essere in cgroup diversi per controller diversi

v2: Gerarchia unificata, tutti i controller in un'unica struttura
    /sys/fs/cgroup/
    ├── cgroup.controllers           ← controller disponibili
    ├── cgroup.subtree_control       ← controller attivi per i figli
    ├── user.slice/                  ← sessioni utente
    │   └── user-1000.slice/
    │       └── session-2.scope/
    ├── system.slice/                ← servizi systemd
    │   ├── nginx.service/
    │   └── postgresql.service/
    └── init.scope/                  ← PID 1 (systemd)
```

```bash
# Verificare la versione cgroups in uso
stat -fc %T /sys/fs/cgroup/
# cgroup2fs → v2
# tmpfs     → v1 (o ibrido)

mount | grep cgroup
# cgroup2 on /sys/fs/cgroup type cgroup2 (rw,nosuid,nodev,noexec,relatime)

# Controller disponibili
cat /sys/fs/cgroup/cgroup.controllers
# cpu cpuset io memory hugetlb pids rdma misc

# Controller attivati per i sotto-cgroup
cat /sys/fs/cgroup/cgroup.subtree_control
# cpu cpuset io memory pids

# Vedere in quale cgroup si trova un processo
cat /proc/<PID>/cgroup
# 0::/user.slice/user-1000.slice/session-2.scope

# Processi in un cgroup
cat /sys/fs/cgroup/system.slice/nginx.service/cgroup.procs
```

### Controller CPU

```bash
# File del controller CPU nel cgroup:
# cpu.max          — limite di utilizzo CPU
# cpu.weight       — peso relativo (1-10000, default 100)
# cpu.weight.nice  — peso derivato dal nice value
# cpu.stat         — statistiche CPU
# cpu.pressure     — PSI (Pressure Stall Information)

# Limitare un servizio al 50% di 1 CPU
# Formato: $QUOTA $PERIOD (in microsecondi)
echo "50000 100000" | sudo tee /sys/fs/cgroup/system.slice/myservice/cpu.max
# 50000/100000 = 50% di 1 CPU

# Limitare al 200% (2 CPU intere)
echo "200000 100000" | sudo tee /sys/fs/cgroup/system.slice/myservice/cpu.max

# Nessun limite
echo "max 100000" | sudo tee /sys/fs/cgroup/system.slice/myservice/cpu.max

# Peso relativo (per distribuzione equa sotto contention)
echo 50 | sudo tee /sys/fs/cgroup/system.slice/myservice/cpu.weight
# Default 100. Un cgroup con peso 200 riceve il doppio di CPU rispetto a uno con peso 100

# Via systemd (metodo preferito):
sudo systemctl set-property myservice.service CPUQuota=50%
sudo systemctl set-property myservice.service CPUWeight=50

# In unit file:
# [Service]
# CPUQuota=150%         # max 1.5 CPU
# CPUWeight=200         # peso relativo
# AllowedCPUs=0-3       # CPU consentite (cpuset)

# Leggere statistiche
cat /sys/fs/cgroup/system.slice/myservice/cpu.stat
# usage_usec 1234567    ← tempo CPU totale in microsecondi
# user_usec  1000000    ← tempo user space
# system_usec 234567    ← tempo kernel
# nr_periods 1000       ← periodi di enforcement
# nr_throttled 50       ← periodi in cui il cgroup è stato throttled
# throttled_usec 500000 ← tempo totale di throttling
```

### Controller Memory

```bash
# File principali:
# memory.current     — uso corrente (byte)
# memory.max         — hard limit (OOM kill se superato)
# memory.high        — soft limit (rallentamento, reclaim aggressivo)
# memory.low         — protezione best-effort (non reclaim sotto questa soglia)
# memory.min         — protezione hard (mai reclaim sotto questa soglia)
# memory.swap.max    — limite swap
# memory.stat        — statistiche dettagliate
# memory.events      — contatori di eventi (max, high, oom, oom_kill)
# memory.pressure    — PSI

# Hard limit a 512 MB
echo 536870912 | sudo tee /sys/fs/cgroup/system.slice/myservice/memory.max

# Soft limit a 256 MB (il processo viene rallentato sopra questa soglia)
echo 268435456 | sudo tee /sys/fs/cgroup/system.slice/myservice/memory.high

# Protezione: almeno 128 MB garantiti
echo 134217728 | sudo tee /sys/fs/cgroup/system.slice/myservice/memory.low

# Disabilitare swap per il cgroup
echo 0 | sudo tee /sys/fs/cgroup/system.slice/myservice/memory.swap.max

# Via systemd:
sudo systemctl set-property myservice.service MemoryMax=512M
sudo systemctl set-property myservice.service MemoryHigh=256M

# In unit file:
# [Service]
# MemoryMax=512M
# MemoryHigh=256M
# MemorySwapMax=0
# MemoryLow=128M

# Monitorare uso memoria
cat /sys/fs/cgroup/system.slice/myservice/memory.current
# 234567890 (byte)

# Eventi OOM
cat /sys/fs/cgroup/system.slice/myservice/memory.events
# low 0
# high 3        ← 3 volte ha superato memory.high
# max 1         ← 1 volta ha superato memory.max
# oom 1         ← 1 volta l'OOM killer ha agito
# oom_kill 1    ← 1 processo ucciso
```

### Controller IO

```bash
# File principali:
# io.max       — limiti di I/O per dispositivo (IOPS e bandwidth)
# io.weight    — peso relativo per dispositivo
# io.stat      — statistiche I/O per dispositivo
# io.pressure  — PSI

# Formato io.max: MAJOR:MINOR type=limit
# Trovare major:minor del dispositivo
lsblk -d -o NAME,MAJ:MIN
# sda  8:0

# Limitare la bandwidth di scrittura a 10 MB/s su sda
echo "8:0 wbps=10485760" | sudo tee /sys/fs/cgroup/system.slice/myservice/io.max

# Limitare IOPS di lettura a 1000 su sda
echo "8:0 riops=1000" | sudo tee /sys/fs/cgroup/system.slice/myservice/io.max

# Limiti multipli sulla stessa riga
echo "8:0 rbps=52428800 wbps=10485760 riops=5000 wiops=1000" | sudo tee \
    /sys/fs/cgroup/system.slice/myservice/io.max

# Via systemd:
# [Service]
# IOWriteBandwidthMax=/dev/sda 10M
# IOReadBandwidthMax=/dev/sda 50M
# IOWeight=50

# Peso I/O relativo (1-10000, default 100)
echo "8:0 200" | sudo tee /sys/fs/cgroup/system.slice/myservice/io.weight

# Statistiche
cat /sys/fs/cgroup/system.slice/myservice/io.stat
# 8:0 rbytes=1234567 wbytes=2345678 rios=456 wios=789 dbytes=0 dios=0
```

### Integrazione systemd

systemd è il "gestore" principale dei cgroups v2 nei sistemi moderni. Ogni servizio vive nel proprio cgroup.

```bash
# La gerarchia systemd:
# /sys/fs/cgroup/
# ├── init.scope/           → PID 1 (systemd)
# ├── system.slice/         → servizi di sistema
# │   ├── nginx.service/
# │   ├── sshd.service/
# │   └── postgresql.service/
# ├── user.slice/           → sessioni utente
# │   └── user-1000.slice/
# │       └── session-2.scope/
# │           └── app.slice/
# └── machine.slice/        → VM e container

# Mostrare la gerarchia cgroup con systemd
systemd-cgls
# O solo un sottoalbero
systemd-cgls /system.slice

# Risorse di un servizio
systemd-cgtop
# Control Group         Tasks   %CPU   Memory  Input/s Output/s
# /                       234    5.2   1.2G        -       -
# /system.slice            78    3.1   800M        -       -
# /system.slice/nginx      4     0.8   50M         -       -

# Impostare limiti via systemd
sudo systemctl set-property nginx.service \
    CPUQuota=200% \
    MemoryMax=1G \
    MemoryHigh=768M \
    IOWeight=200 \
    TasksMax=512

# I set-property sono persistenti (scritti in /etc/systemd/system/nginx.service.d/override.conf)
# Per limiti temporanei (fino al reboot):
sudo systemctl set-property --runtime nginx.service MemoryMax=1G

# In unit file:
# [Service]
# CPUQuota=200%
# MemoryMax=1G
# MemoryHigh=768M
# MemorySwapMax=256M
# IOWeight=200
# TasksMax=512
# OOMScoreAdjust=-500
# Slice=system-critical.slice     # Spostare in uno slice custom
```

### Delegazione cgroup

La delegazione permette a un processo non-root di gestire il proprio sotto-albero cgroup. Fondamentale per container runtime e session manager.

```bash
# systemd delega automaticamente un cgroup a ogni utente:
# /sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/

# Controllare la delegazione
cat /sys/fs/cgroup/user.slice/user-1000.slice/cgroup.controllers
# cpu memory pids

# Per delegare esplicitamente (es. per un container runtime unprivileged):
# [Service]
# Delegate=yes
# O selettivo:
# Delegate=cpu memory pids io

# Il processo del servizio può creare sotto-cgroup e spostare processi:
mkdir /sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/myapp
echo $$ > /sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/myapp/cgroup.procs
echo "+cpu +memory" > /sys/fs/cgroup/.../myapp/cgroup.subtree_control
```

---

## Namespace Linux

I namespace sono il meccanismo del kernel che permette l'isolamento delle risorse. Ogni namespace fornisce a un processo una visione privata di un certo aspetto del sistema. I namespace sono il fondamento tecnologico dei container.

### PID Namespace

Isola l'albero dei PID. Un processo nel proprio PID namespace vede se stesso come PID 1 e non vede i processi degli altri namespace.

```bash
# Creare un nuovo PID namespace
sudo unshare --pid --fork --mount-proc bash
# Ora siamo in un nuovo PID namespace
ps aux
# Solo i processi di questo namespace sono visibili
# Il primo processo è PID 1

# PID namespace è gerarchico:
# - Il padre vede i PID dei figli (con PID diversi)
# - I figli non vedono i processi del padre
#
# Processo nel namespace padre: PID 12345
# Lo stesso processo nel suo namespace: PID 1

# Verificare il namespace
ls -la /proc/self/ns/pid
# pid:[4026532008]  ← numero diverso dal namespace iniziale

# Un container Docker è essenzialmente:
# PID namespace + mount namespace + network namespace + ...
```

### Network Namespace

Isola lo stack di rete: interfacce, routing table, iptables, socket.

```bash
# Creare un network namespace con ip
sudo ip netns add myns

# Eseguire un comando nel namespace
sudo ip netns exec myns ip link
# 1: lo: <LOOPBACK> state DOWN     ← solo loopback, nessuna interfaccia

# Creare una coppia veth (virtual ethernet) per connettere namespace
sudo ip link add veth0 type veth peer name veth1
sudo ip link set veth1 netns myns

# Configurare le interfacce
sudo ip addr add 10.0.0.1/24 dev veth0
sudo ip link set veth0 up
sudo ip netns exec myns ip addr add 10.0.0.2/24 dev veth1
sudo ip netns exec myns ip link set veth1 up
sudo ip netns exec myns ip link set lo up

# Test connettività
sudo ip netns exec myns ping -c 1 10.0.0.1

# Lista namespace di rete
ip netns list

# Eliminare
sudo ip netns delete myns

# Ogni container Docker ha il proprio network namespace
# con veth pair che lo connette al bridge docker0
```

### Mount Namespace

Isola i mount point. Un processo nel proprio mount namespace può montare/smontare filesystem senza influire sugli altri.

```bash
# Creare un mount namespace
sudo unshare --mount bash

# Ora possiamo montare filesystem che solo noi vediamo
mount -t tmpfs tmpfs /tmp/private
echo "dati segreti" > /tmp/private/data

# All'uscita, /tmp/private/data non esiste per gli altri processi

# Pivot root: cambiare la root del namespace (usato dai container)
# 1. Preparare il nuovo root filesystem
# 2. mount --bind /path/to/newroot /path/to/newroot
# 3. cd /path/to/newroot
# 4. pivot_root . old_root
# 5. umount old_root e rimuovere
```

### UTS Namespace

Isola hostname e domainname. Ogni namespace ha il proprio hostname.

```bash
# Creare un UTS namespace
sudo unshare --uts bash
hostname container-1
hostname
# container-1

# All'uscita, l'hostname originale non è cambiato
# I container usano questo per avere il proprio hostname
```

### IPC Namespace

Isola le risorse IPC System V (shared memory, semafori, code di messaggi) e le code di messaggi POSIX.

```bash
# Creare un IPC namespace
sudo unshare --ipc bash

# Le risorse IPC create qui non sono visibili all'esterno
ipcs  # mostra solo le risorse di questo namespace

# Previene che processi in container diversi interferiscano
# tramite shared memory o semafori
```

### User Namespace

Isola UID e GID. Un processo può essere root (UID 0) nel suo user namespace ma mappato a un utente non privilegiato all'esterno. Fondamentale per container rootless.

```bash
# Creare un user namespace (non richiede root!)
unshare --user --map-root-user bash
whoami
# root (nel namespace)
# Ma dall'esterno, il processo gira con il nostro UID originale

# Mappatura UID:
cat /proc/self/uid_map
#        0       1000          1
# (UID 0 nel namespace = UID 1000 nell'host)

# Questa è la base dei container rootless (Podman, rootless Docker):
# Il container vede root, ma nell'host è un utente normale
# → Nessun rischio di escalation se il container viene compromesso
```

### Cgroup Namespace

Isola la vista dei cgroup. Un processo nel proprio cgroup namespace vede il proprio cgroup come root della gerarchia.

```bash
# Verificare il cgroup namespace
ls -la /proc/self/ns/cgroup

# In un container:
cat /proc/self/cgroup
# 0::/   ← vede se stesso come root del cgroup
# Nell'host, lo stesso processo sarebbe:
# 0::/system.slice/docker-abc123.scope
```

### Come i Namespace Abilitano i Container

```
Un container Linux è la combinazione di:

┌─────────────────────────────────────────────────┐
│ Container                                        │
│                                                  │
│  PID Namespace     → albero PID isolato          │
│  Network Namespace → stack di rete privato       │
│  Mount Namespace   → filesystem privato          │
│  UTS Namespace     → hostname privato            │
│  IPC Namespace     → IPC isolato                 │
│  User Namespace    → UID/GID mappati             │
│  Cgroup Namespace  → vista cgroup isolata        │
│                                                  │
│  + cgroups         → limiti di risorse           │
│  + seccomp         → filtro syscall              │
│  + capabilities    → permessi granulari          │
│  + AppArmor/SELinux → MAC                        │
│  + overlay FS      → filesystem layered          │
│                                                  │
└─────────────────────────────────────────────────┘

Docker/Podman/containerd usano queste primitive del kernel.
Non c'è magia: un container è un processo con namespace isolati.

# Esempio: creare un "mini-container" a mano
sudo unshare --pid --fork --mount-proc --net --uts --ipc \
    --mount --user --map-root-user \
    /bin/bash

# Ora siamo in un ambiente isolato come un container primitivo
```

```bash
# Entrare nel namespace di un container Docker
CONTAINER_PID=$(docker inspect --format '{{.State.Pid}}' mycontainer)
sudo nsenter --target $CONTAINER_PID --mount --uts --ipc --net --pid bash
# Ora siamo "dentro" il container con accesso pieno

# Comparare namespace di due processi
ls -la /proc/1/ns/        # PID 1 (host)
ls -la /proc/$CONTAINER_PID/ns/   # processo nel container
# I numeri degli inode saranno diversi per i namespace isolati
```

---

## Comunicazione tra Processi (IPC)

### Pipe e Named Pipe (FIFO)

```bash
# Pipe anonima: collega stdout di un processo a stdin di un altro
ls -la | grep "\.conf" | wc -l

# Internamente:
# 1. La shell crea una pipe (coppia di fd: read_end, write_end)
# 2. fork() per ogni comando nella pipeline
# 3. Ogni processo redirige stdin/stdout sui fd della pipe
# 4. I dati fluiscono attraverso un buffer nel kernel (64 KB default)

# Verificare la dimensione del buffer pipe
cat /proc/sys/fs/pipe-max-size
# 1048576 (1 MB max)

# Named pipe (FIFO): pipe con un nome nel filesystem
mkfifo /tmp/myfifo

# Terminale 1: il lettore blocca finché non ci sono dati
cat /tmp/myfifo

# Terminale 2: lo scrittore invia dati
echo "hello" > /tmp/myfifo

# Named pipe sono utili per IPC tra processi non correlati
# (le pipe anonime funzionano solo tra padre-figlio)

# Rimuovere
rm /tmp/myfifo

# Esempio pratico: logging via named pipe
mkfifo /tmp/logpipe
# In background: lettore che processa i log
while read line < /tmp/logpipe; do
    echo "$(date -Is) $line" >> /var/log/myapp.log
done &
# L'applicazione scrive sulla pipe
echo "Applicazione avviata" > /tmp/logpipe
```

### Unix Domain Socket

Socket locali per comunicazione bidirezionale ad alta performance tra processi sullo stesso host.

```bash
# Trovare socket Unix in uso
ss -xlp
# o
find /run -name "*.sock" -o -name "*.socket" 2>/dev/null
# /run/docker.sock
# /run/dbus/system_bus_socket
# /run/user/1000/bus

# Tipi di Unix socket:
# SOCK_STREAM — orientato alla connessione (come TCP), affidabile, ordinato
# SOCK_DGRAM  — datagrammi (come UDP), affidabile su Unix domain
# SOCK_SEQPACKET — sequenziale, orientato ai messaggi

# Vantaggi rispetto a TCP/IP su localhost:
# - Nessun overhead di rete (no TCP stack)
# - Supporta il passaggio di file descriptor tra processi
# - Supporta credenziali del peer (SO_PEERCRED)
# - ~2x più veloce di TCP loopback

# Verificare chi è in ascolto su un socket
ss -xlp | grep docker.sock
# u_str LISTEN 0 4096 /run/docker.sock 12345 * 0 users:(("dockerd",pid=1234,fd=5))

# Esempio con socat (tool tuttofare per socket):
# Server
socat UNIX-LISTEN:/tmp/mysocket,fork EXEC:/bin/cat
# Client
echo "test" | socat - UNIX-CONNECT:/tmp/mysocket

# Testare la connettività a un socket Unix
socat - UNIX-CONNECT:/run/docker.sock <<< 'GET /version HTTP/1.0\r\n'
```

### Shared Memory

Segmenti di memoria condivisi tra processi. Il metodo IPC più veloce: nessun copia di dati, accesso diretto.

```bash
# Shared memory POSIX (preferito)
# Risiede in /dev/shm/ (tmpfs montato in RAM)
ls -la /dev/shm/
# -rw------- 1 postgres postgres 56000000 May 22 10:00 PostgreSQL.1234567

df -h /dev/shm
# tmpfs      3.9G   56M  3.8G   2% /dev/shm

# Shared memory System V (legacy)
ipcs -m
# ------ Shared Memory Segments --------
# key        shmid      owner      perms      bytes      nattach
# 0x01020304 12345      postgres   600        56000000   5

# Dettagli
ipcs -m -i 12345

# Rimuovere (attenzione: il processo potrebbe crashare)
ipcrm -m 12345

# Limitare la dimensione di /dev/shm
# In /etc/fstab: tmpfs /dev/shm tmpfs defaults,size=2G 0 0

# NOTA: la shared memory richiede sincronizzazione (semafori o mutex)
# per evitare race condition. Non usare senza meccanismi di locking.
```

### Semafori

Meccanismo di sincronizzazione per controllare l'accesso a risorse condivise.

```bash
# Semafori POSIX (named)
# Creati come file in /dev/shm/sem.*

# Semafori System V
ipcs -s
# ------ Semaphore Arrays --------
# key        semid      owner      perms      nsems

# Rimuovere
ipcrm -s <semid>

# Esempio pratico: flock come semaforo binario in bash
# Solo un'istanza alla volta
exec 9>/tmp/myapp.lock
if ! flock -n 9; then
    echo "Un'altra istanza è in esecuzione"
    exit 1
fi
# ... lavoro ...
# Il lock viene rilasciato automaticamente all'uscita
```

### Code di Messaggi

Permettono ai processi di scambiare messaggi strutturati.

```bash
# Code POSIX
# Montate in /dev/mqueue/
ls /dev/mqueue/

# Code System V
ipcs -q
# ------ Message Queues --------
# key        msqid      owner      perms      used-bytes   messages

# Sommario di tutti gli IPC
ipcs -a

# Rimuovere una coda
ipcrm -q <msqid>

# Limiti IPC del kernel
sysctl -a | grep -E "kernel\.(msg|shm|sem)"
# kernel.msgmax = 8192          ← max dimensione singolo messaggio
# kernel.msgmnb = 16384         ← max byte per coda
# kernel.msgmni = 32000         ← max numero di code
# kernel.shmmax = 18446744073709551615  ← max dimensione singolo segmento
# kernel.shmmni = 4096          ← max numero di segmenti
# kernel.sem = 32000 1024000000 500 32000  ← limiti semafori
```

---

## Monitoraggio Processi

### ps — Process Status

```bash
# Formati più utili per diagnosi:

# Top 10 per CPU
ps -eo pid,ppid,user,%cpu,%mem,stat,start,time,comm --sort=-%cpu | head -11

# Top 10 per memoria (RSS reale, non virtuale)
ps -eo pid,ppid,user,rss,vsz,%mem,comm --sort=-rss | head -11

# Processi con più thread
ps -eo pid,nlwp,comm --sort=-nlwp | head -11

# Processi più vecchi (long-running)
ps -eo pid,etime,comm --sort=-etime | head -11

# Processi di un utente specifico con dettagli
ps -u www-data -o pid,ppid,%cpu,%mem,stat,start,time,comm

# Processi con file descriptor aperti (stima)
for pid in $(ps -eo pid --no-headers); do
    count=$(ls /proc/$pid/fd 2>/dev/null | wc -l)
    if [ "$count" -gt 100 ]; then
        comm=$(cat /proc/$pid/comm 2>/dev/null)
        echo "$count $pid $comm"
    fi
done | sort -rn | head -10

# Thread di un processo specifico
ps -T -p <PID> -o spid,comm,%cpu,stat

# Formato wide (linea di comando non troncata)
ps auxww | grep nginx
```

### top e htop

```bash
# top — comandi interattivi principali:
# 1       → mostra CPU per core
# M       → ordina per memoria
# P       → ordina per CPU
# T       → ordina per tempo CPU cumulativo
# c       → mostra linea di comando completa
# V       → mostra albero processi (forest)
# H       → mostra thread
# u       → filtra per utente
# f       → scegli campi da visualizzare
# k       → invia segnale (kill)
# r       → cambia nice (renice)
# W       → salva configurazione
# q       → esci

# top non interattivo (per scripting/logging):
top -b -n 1 -o %CPU | head -20    # batch mode, 1 iterazione, ordina per CPU

# htop — vantaggi su top:
# - Interfaccia colorata e leggibile
# - Scroll verticale e orizzontale
# - Mouse support
# - Filtri, ricerca, ordinamento intuitivi
# - Tree view built-in
# - Setup interattivo (F2)
# - Strace/ltrace integrato (s per strace)

# htop tasti principali:
# F1        → help
# F2        → setup
# F3        → search
# F4        → filter
# F5        → tree view
# F6        → sort by
# F9        → kill
# F10       → quit
# Space     → tag processo
# U         → untag tutti
# s         → strace del processo selezionato
# l         → lsof del processo selezionato
# t         → tree view toggle

# Installazione htop
# Debian/Ubuntu: sudo apt install htop
# RHEL/Fedora:   sudo dnf install htop
# Arch:          sudo pacman -S htop

# Alternativa moderna: btm (bottom)
# cargo install bottom   oppure pacchetto della distro
# btm — interfaccia TUI con grafici, supporta mouse, widget configurabili
```

### atop — Analisi Storica

`atop` registra campioni di attività di sistema a intervalli regolari, permettendo analisi post-mortem.

```bash
# Installazione
# Debian/Ubuntu: sudo apt install atop
# RHEL/Fedora:   sudo dnf install atop

# Il servizio atop salva snapshot ogni 600 secondi in /var/log/atop/
systemctl status atop

# Visualizzare registrazioni storiche
atop -r /var/log/atop/atop_20260522
# t/T → avanti/indietro nel tempo
# m   → memoria
# d   → disco
# n   → network
# c   → linea di comando

# Leggere un intervallo specifico
atop -r /var/log/atop/atop_20260522 -b 14:00 -e 15:00

# atop in real-time
atop 1    # aggiorna ogni 1 secondo

# Caratteristiche uniche di atop:
# - Mostra processi che sono terminati tra un campione e l'altro
# - Accounting per disco per processo
# - PSI (Pressure Stall Information) integrato
# - Evidenzia in rosso le risorse sotto stress
```

### pstree — Albero Processi

```bash
# Albero completo
pstree

# Con PID
pstree -p

# Con argomenti
pstree -a

# Solo per un utente
pstree -u www-data

# Da un PID specifico (sottoalbero)
pstree -p 1234

# Con thread
pstree -t

# Compatto (unisci rami identici)
pstree -c
# systemd─┬─agetty
#          ├─3*[nginx───nginx]     ← 3 worker identici compressi
#          └─sshd───sshd───bash
```

### pidstat — Statistiche per PID

Parte del pacchetto `sysstat`. Fornisce statistiche dettagliate per singolo PID.

```bash
# CPU per processo (ogni 1 secondo, 5 campioni)
pidstat 1 5

# Memoria per processo
pidstat -r 1 5

# I/O per processo
pidstat -d 1 5

# Context switch per processo
pidstat -w 1 5

# Thread di un processo specifico
pidstat -t -p <PID> 1 5

# Tutto insieme per un processo
pidstat -urd -p <PID> 1

# Filtrare per nome
pidstat -C "nginx" 1
```

### Analisi /proc in Tempo Reale

```bash
# Script di monitoraggio personalizzato per un processo
monitor_proc() {
    local pid=$1
    if [ ! -d "/proc/$pid" ]; then
        echo "Processo $pid non trovato"
        return 1
    fi

    local comm=$(cat /proc/$pid/comm)
    echo "=== Monitoraggio $comm (PID $pid) ==="

    while [ -d "/proc/$pid" ]; do
        local rss=$(awk '/VmRSS/ {print $2}' /proc/$pid/status 2>/dev/null)
        local threads=$(awk '/Threads/ {print $2}' /proc/$pid/status 2>/dev/null)
        local fds=$(ls /proc/$pid/fd 2>/dev/null | wc -l)
        local state=$(awk '/State/ {print $2}' /proc/$pid/status 2>/dev/null)

        printf "%s | RSS: %s kB | Threads: %s | FDs: %s | State: %s\n" \
            "$(date +%H:%M:%S)" "$rss" "$threads" "$fds" "$state"
        sleep 2
    done
    echo "Processo terminato."
}

# Uso: monitor_proc 1234
```

---

## Background, Foreground e Jobs

### Gestione Job nella Shell

```bash
# Avviare in background
./long-task.sh &                    # & = background
[1] 12345                           # [job number] PID

# Ctrl+Z → sospende il processo corrente (SIGTSTP)
# Il processo è "stopped", non terminato

# Gestione job
jobs                                # Lista job nella shell corrente
jobs -l                             # Con PID
fg                                  # Riporta l'ultimo job in foreground
fg %1                               # Job specifico in foreground
bg                                  # Riprendi l'ultimo job in background
bg %2                               # Job specifico in background

# Terminare job
kill %1                             # Termina job 1

# Disown (scollega il job dalla shell)
disown %1                           # Il job sopravvive alla chiusura della shell
disown -a                           # Disown tutti i job

# nohup (immune a SIGHUP, sopravvive alla chiusura del terminale)
nohup ./long-task.sh &              # Output in nohup.out
nohup ./long-task.sh > output.log 2>&1 &   # Output personalizzato
```

### nohup e disown

```bash
# Differenza tra nohup e disown:

# nohup: da usare PRIMA di avviare il processo
# - Ignora SIGHUP (il processo sopravvive alla chiusura del terminale)
# - Redirige stdout/stderr in nohup.out se non rediretto
# - NON rimuove il job dalla job table della shell
nohup ./script.sh > /var/log/script.log 2>&1 &

# disown: da usare DOPO che il processo è già in background
# - Rimuove il job dalla job table della shell
# - Il processo non riceverà SIGHUP alla chiusura della shell
# - NON redirige l'output
./script.sh &
disown %1

# Best practice: usare entrambi per sicurezza
nohup ./script.sh > /var/log/script.log 2>&1 &
disown

# Per processi importanti, preferire tmux/screen o servizi systemd
```

### Screen e tmux

```bash
# tmux (più moderno)
tmux new -s session_name            # Nuova sessione
# Ctrl+B, D = detach
tmux ls                             # Lista sessioni
tmux attach -t session_name         # Riattacca

# tmux avanzato:
tmux new -s dev                     # Nuova sessione "dev"
# Ctrl+B, c      → nuova finestra
# Ctrl+B, n      → finestra successiva
# Ctrl+B, p      → finestra precedente
# Ctrl+B, %      → split verticale
# Ctrl+B, "      → split orizzontale
# Ctrl+B, z      → zoom panel
# Ctrl+B, [      → scroll mode (q per uscire)
# Ctrl+B, :      → command mode

# Inviare comandi a una sessione tmux da fuori
tmux send-keys -t dev "ls -la" Enter

# Sessione con script di setup
tmux new-session -d -s monitoring
tmux send-keys -t monitoring "htop" Enter
tmux split-window -h -t monitoring
tmux send-keys -t monitoring "watch -n 1 'ss -tlnp'" Enter
tmux attach -t monitoring

# screen (legacy)
screen -S session_name
# Ctrl+A, D = detach
screen -ls
screen -r session_name

# screen con logging
screen -L -S session_name           # Log in screenlog.0
```

### Servizi systemd

Per processi che devono sopravvivere a reboot e riavviarsi automaticamente.

```bash
# Creare un servizio systemd personalizzato
# /etc/systemd/system/myapp.service
# [Unit]
# Description=My Application
# After=network.target
#
# [Service]
# Type=simple
# User=appuser
# Group=appgroup
# WorkingDirectory=/opt/myapp
# ExecStart=/opt/myapp/bin/start.sh
# ExecStop=/opt/myapp/bin/stop.sh
# ExecReload=/bin/kill -HUP $MAINPID
# Restart=on-failure
# RestartSec=5
# StandardOutput=journal
# StandardError=journal
# SyslogIdentifier=myapp
#
# # Limiti risorse (cgroup):
# MemoryMax=512M
# CPUQuota=200%
# TasksMax=100
#
# # Hardening sicurezza:
# NoNewPrivileges=true
# ProtectSystem=strict
# ProtectHome=true
# PrivateTmp=true
# ReadOnlyPaths=/etc
#
# [Install]
# WantedBy=multi-user.target

# Gestione
sudo systemctl daemon-reload
sudo systemctl enable myapp.service
sudo systemctl start myapp.service
sudo systemctl status myapp.service
journalctl -u myapp.service -f      # Log in tempo reale
```

---

## System Call e strace

### strace — Deep Dive

`strace` intercetta e registra le system call fatte da un processo. È il tool di debugging universale: quando non capisci cosa sta succedendo, traccia le syscall.

```bash
# Tracciare un comando
strace ls /tmp

# Tracciare un processo esistente
sudo strace -p <PID>

# Output su file (consigliato — l'output è verboso)
strace -o /tmp/trace.log -p <PID>

# Seguire i processi figli (fork)
strace -f -o /tmp/trace.log -p <PID>

# Filtrare per tipo di syscall (MOLTO utile)
strace -e trace=open,read,write ls /tmp          # Solo I/O file
strace -e trace=network curl http://example.com   # Solo rete
strace -e trace=process bash -c 'ls'              # Solo gestione processi
strace -e trace=signal kill -TERM $$              # Solo segnali
strace -e trace=memory malloc_test                 # Solo memoria

# Categorie di filtri:
# trace=file      → open, stat, chmod, unlink, ...
# trace=process   → fork, exec, wait, exit, ...
# trace=network   → socket, bind, connect, send, recv, ...
# trace=signal    → kill, sigaction, sigprocmask, ...
# trace=ipc       → shmget, semget, msgget, ...
# trace=memory    → mmap, mprotect, brk, ...
# trace=desc      → read, write, close, dup, ...

# Statistiche (senza output dettagliato)
strace -c ls /tmp
# % time     seconds  usecs/call     calls    errors syscall
# ------ ----------- ----------- --------- --------- ----------------
#  42.86    0.000060          10         6           mmap
#  21.43    0.000030           5         6         3 openat
#  14.29    0.000020           5         4           close
# ...

# Timestamp relativo (ms tra syscall consecutive)
strace -r -e trace=open ls /tmp

# Timestamp assoluto
strace -t -e trace=open ls /tmp      # HH:MM:SS
strace -tt -e trace=open ls /tmp     # HH:MM:SS.microsec

# Stringhe lunghe (default: troncate a 32 chars)
strace -s 1024 -e trace=write ./app  # Mostra fino a 1024 chars

# Decodificare argomenti (path, flag, etc.)
strace -yy -e trace=open ls /tmp
# openat(AT_FDCWD</tmp>, "/tmp", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY) = 3</tmp>
```

### Syscall Comuni per Debugging

```bash
# Scenario: "Il processo non riesce ad aprire un file"
strace -e trace=openat,access ./app 2>&1 | grep -i error
# openat(AT_FDCWD, "/etc/app.conf", O_RDONLY) = -1 ENOENT (No such file or directory)
# → Il file non esiste

# Scenario: "Il processo è lento"
strace -c -p <PID>
# Ctrl+C dopo qualche secondo per vedere le statistiche
# Se la maggior parte del tempo è in read/write → I/O bound
# Se è in futex/nanosleep → in attesa di lock/timer
# Se è in poll/epoll_wait → in attesa di eventi

# Scenario: "Il processo consuma troppi file descriptor"
strace -e trace=openat,close -p <PID>
# Cercare openat() senza corrispondente close() → fd leak

# Scenario: "Problemi di connessione di rete"
strace -e trace=network -p <PID>
# connect(3, {sa_family=AF_INET, sin_port=htons(5432), sin_addr=inet_addr("10.0.0.5")}, 16) = -1 ETIMEDOUT
# → Timeout di connessione al database

# Scenario: "Permission denied ma non capisco perché"
strace -e trace=openat,access,stat ./app
# openat(AT_FDCWD, "/var/lib/app/data", O_WRONLY) = -1 EACCES (Permission denied)
# → Controllare permessi di /var/lib/app/data

# Syscall comuni e loro significato:
# openat()     → apertura file
# read()       → lettura dati
# write()      → scrittura dati
# close()      → chiusura file descriptor
# stat()/fstat() → metadati file
# mmap()       → mappatura file in memoria
# brk()        → espansione heap
# fork()/clone() → creazione processo/thread
# execve()     → esecuzione nuovo programma
# wait4()      → attesa figlio
# connect()    → connessione socket
# bind()       → binding socket
# accept()     → accettazione connessione
# sendto()     → invio dati socket
# recvfrom()   → ricezione dati socket
# poll()/epoll_wait() → multiplexing I/O
# futex()      → lock/unlock mutex userspace
# nanosleep()  → sleep
# ioctl()      → operazioni device-specific
```

### ltrace — Library Calls

`ltrace` intercetta le chiamate alle librerie condivise (es. libc). Complementare a strace.

```bash
# Tracciare chiamate a librerie
ltrace ls /tmp

# Filtrare per libreria
ltrace -l /lib/x86_64-linux-gnu/libpthread.so.0 ./app

# Combinare con strace per il quadro completo:
# strace → cosa chiede il processo al kernel (syscall)
# ltrace → cosa chiede il processo alle librerie (es. malloc, free, printf)

# Nota: ltrace non funziona bene con binari compilati con PIE e ASLR
# Su sistemi moderni, strace è generalmente più affidabile
```

---

## Sicurezza dei Processi

### Capabilities Linux

Le capabilities dividono i privilegi di root in unità granulari. Invece di dare root (tutti i poteri) a un binario, si possono assegnare solo le capabilities necessarie.

```bash
# Elencare tutte le capabilities
capsh --print

# Capabilities comuni:
# CAP_NET_BIND_SERVICE → bind a porte < 1024 senza root
# CAP_NET_RAW          → uso di raw socket (ping, tcpdump)
# CAP_NET_ADMIN        → configurazione di rete
# CAP_SYS_PTRACE       → strace/debug altri processi
# CAP_SYS_ADMIN        → catch-all admin (mount, sethostname, ...)
# CAP_DAC_OVERRIDE     → bypass permessi file (lettura/scrittura)
# CAP_DAC_READ_SEARCH  → bypass permessi file (lettura)
# CAP_CHOWN            → cambiare proprietario file
# CAP_KILL             → inviare segnali a processi di altri utenti
# CAP_SETUID/SETGID    → cambiare UID/GID
# CAP_SYS_TIME         → impostare l'orologio di sistema
# CAP_AUDIT_WRITE      → scrivere record di audit

# Assegnare capability a un binario (al posto di setuid)
sudo setcap 'cap_net_bind_service=+ep' /usr/bin/myapp
# +e = effective, +p = permitted
# Ora myapp può fare bind su porta 80 senza root

# Verificare le capabilities di un file
getcap /usr/bin/myapp
# /usr/bin/myapp cap_net_bind_service=ep

# Capabilities di un processo
cat /proc/<PID>/status | grep -i cap
# O più leggibile:
getpcaps <PID>

# Rimuovere capabilities
sudo setcap -r /usr/bin/myapp

# Capabilities in un container Docker:
# docker run --cap-add=NET_BIND_SERVICE --cap-drop=ALL myimage
# → Solo la capability specifica, non root pieno

# In systemd:
# [Service]
# CapabilityBoundingSet=CAP_NET_BIND_SERVICE
# AmbientCapabilities=CAP_NET_BIND_SERVICE
# User=appuser   ← esegue come utente non-root con la capability
```

### Seccomp Filters

Seccomp (Secure Computing) limita le system call che un processo può eseguire. Se un processo tenta una syscall non permessa, viene ucciso con SIGSYS.

```bash
# Verificare se seccomp è attivo per un processo
grep Seccomp /proc/<PID>/status
# Seccomp:     0   → disabilitato
# Seccomp:     1   → strict (solo read, write, exit, sigreturn)
# Seccomp:     2   → filter (BPF filter personalizzato)
# Seccomp_filters: 1  → numero di filtri attivi

# Docker usa seccomp per default: blocca ~44 syscall pericolose
# (es. mount, reboot, swapon, kexec_load, ...)

# systemd supporta seccomp:
# [Service]
# SystemCallFilter=@system-service      ← gruppo predefinito
# SystemCallFilter=~@privileged         ← nega syscall privilegiate
# SystemCallErrorNumber=EPERM           ← ritorna errore invece di uccidere

# Gruppi di syscall predefiniti da systemd:
# @basic-io       → read, write, lseek, ...
# @file-system    → open, stat, chmod, ...
# @io-event       → poll, epoll, select, ...
# @ipc            → shmget, semget, ...
# @network-io     → socket, bind, connect, ...
# @process        → fork, exec, wait, ...
# @signal         → kill, sigaction, ...
# @system-service → set ragionevole per un servizio
# @privileged     → mount, reboot, swapon, ...

# Esempio: servizio web hardened
# [Service]
# SystemCallFilter=@system-service @network-io
# SystemCallFilter=~@privileged @resources
# SystemCallErrorNumber=EPERM
# SystemCallArchitectures=native        ← solo syscall dell'arch nativa
```

### AppArmor e SELinux

MAC (Mandatory Access Control): limiti di accesso definiti dal sistema, non dall'utente.

```bash
# AppArmor (default su Ubuntu/Debian/SUSE)
# Stato
sudo aa-status
# 45 profiles loaded.
# 37 in enforce mode.
# 8 in complain mode.

# Profili in /etc/apparmor.d/
ls /etc/apparmor.d/

# Mettere un profilo in complain mode (logga ma non blocca)
sudo aa-complain /etc/apparmor.d/usr.sbin.nginx

# Mettere in enforce mode (blocca le violazioni)
sudo aa-enforce /etc/apparmor.d/usr.sbin.nginx

# Generare un profilo automaticamente
sudo aa-genprof /path/to/myapp
# Avviare l'app in un altro terminale, poi premere S (scan) e F (finish)

# SELinux (default su RHEL/Fedora/CentOS)
# Stato
getenforce
# Enforcing, Permissive, o Disabled

# Contesto di sicurezza di un processo
ps -eZ | grep nginx
# system_u:system_r:httpd_t:s0  1234 ? 00:00:01 nginx

# Contesto di un file
ls -Z /var/www/html/
# system_u:object_r:httpd_sys_content_t:s0 index.html

# Verificare violazioni (AVC deny)
ausearch -m AVC -ts recent
sealert -a /var/log/audit/audit.log    # Suggerimenti di fix
```

### Limiti di Risorse (ulimit)

```bash
# Mostrare tutti i limiti della sessione corrente
ulimit -a
# core file size          (blocks, -c) 0           ← no core dump
# data seg size           (kbytes, -d) unlimited
# scheduling priority             (-e) 0
# file size               (blocks, -f) unlimited
# pending signals                 (-i) 62767
# max locked memory       (kbytes, -l) 8192        ← 8 MB
# max memory size         (kbytes, -m) unlimited
# open files                      (-n) 1024        ← CRITICO!
# pipe size            (512 bytes, -p) 8
# POSIX message queues     (bytes, -q) 819200
# real-time priority              (-r) 0
# stack size              (kbytes, -s) 8192         ← 8 MB
# cpu time               (seconds, -t) unlimited
# max user processes              (-u) 62767
# virtual memory          (kbytes, -v) unlimited
# file locks                      (-x) unlimited

# Limiti soft (utente può aumentare fino all'hard limit)
ulimit -Sn                            # Soft limit open files
# 1024

# Limiti hard (solo root può aumentare)
ulimit -Hn                            # Hard limit open files
# 1048576

# Cambiare per la sessione corrente
ulimit -n 65536                       # Open files (solo se < hard limit)

# Configurazione permanente: /etc/security/limits.conf
# <domain>  <type>  <item>   <value>
# *         soft    nofile   65536
# *         hard    nofile   131072
# @dbadmin  soft    nofile   131072
# @dbadmin  hard    nofile   262144
# postgres  soft    nproc    65536
# *         soft    core     0           ← disabilita core dump

# Per servizi systemd (sovrascrive limits.conf):
# [Service]
# LimitNOFILE=65536
# LimitNPROC=65536
# LimitCORE=infinity

# Controllare i limiti effettivi di un processo
cat /proc/<PID>/limits

# ATTENZIONE: "Max open files" = 1024 è troppo basso per:
# - Database (PostgreSQL, MySQL, MongoDB)
# - Web server ad alto traffico (nginx, Apache)
# - Application server (Node.js, Java)
# Aumentare sempre per processi server!
```

---

## Cron e Crontab

Cron è il sistema di schedulazione task più usato in Linux. Esegue comandi a intervalli regolari definiti dall'utente.

### Formato Crontab

```
┌───────────── minuto (0-59)
│ ┌───────────── ora (0-23)
│ │ ┌───────────── giorno del mese (1-31)
│ │ │ ┌───────────── mese (1-12)
│ │ │ │ ┌───────────── giorno della settimana (0-7, 0 e 7 = domenica)
│ │ │ │ │
* * * * *  comando
```

### Gestione Crontab

```bash
crontab -e                          # Modifica crontab personale
crontab -l                          # Lista crontab personale
crontab -r                          # Rimuovi crontab personale
sudo crontab -e -u username        # Modifica crontab di un altro utente
```

### Esempi

```bash
# Ogni 5 minuti
*/5 * * * *  /usr/local/bin/check-service.sh

# Ogni ora al minuto 0
0 * * * *  /usr/local/bin/hourly-task.sh

# Ogni giorno alle 2:30
30 2 * * *  /usr/local/bin/daily-backup.sh

# Ogni lunedì alle 9:00
0 9 * * 1  /usr/local/bin/weekly-report.sh

# Primo del mese alle 0:00
0 0 1 * *  /usr/local/bin/monthly-cleanup.sh

# Ogni giorno lavorativo (lun-ven) alle 8:00
0 8 * * 1-5  /usr/local/bin/workday-task.sh

# Due volte al giorno (8:00 e 20:00)
0 8,20 * * *  /usr/local/bin/twice-daily.sh

# Al reboot
@reboot  /usr/local/bin/startup-task.sh

# Shortcut
@hourly    = 0 * * * *
@daily     = 0 0 * * *
@weekly    = 0 0 * * 0
@monthly   = 0 0 1 * *
@yearly    = 0 0 1 1 *
```

### Buone Pratiche Cron

```bash
# 1. Output e logging
30 2 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1

# 2. Lock per evitare sovrapposizioni
30 2 * * * flock -n /tmp/backup.lock /usr/local/bin/backup.sh

# 3. PATH esplicito (cron ha un PATH minimale)
PATH=/usr/local/bin:/usr/bin:/bin
30 2 * * * backup.sh

# 4. Variabili d'ambiente
SHELL=/bin/bash
MAILTO=admin@example.com            # Email con output
HOME=/home/user

# File di sistema
/etc/crontab                        # Crontab di sistema (con campo utente)
/etc/cron.d/                        # Crontab drop-in
/etc/cron.daily/                    # Script eseguiti giornalmente
/etc/cron.weekly/                   # Script eseguiti settimanalmente
/etc/cron.monthly/                  # Script eseguiti mensilmente
/etc/cron.hourly/                   # Script eseguiti ogni ora

# Controllo accesso
/etc/cron.allow                     # Utenti autorizzati (se esiste, solo questi)
/etc/cron.deny                      # Utenti bloccati
```

---

## at e batch

### at (esecuzione one-time)

```bash
# Eseguire un comando a un orario specifico (una sola volta)
at 14:30                            # Alle 14:30 di oggi
at 14:30 tomorrow                   # Domani alle 14:30
at now + 2 hours                    # Tra 2 ore
at now + 30 minutes                 # Tra 30 minuti
at midnight                         # A mezzanotte
at noon Dec 25                      # Natale a mezzogiorno

# Comandi interattivi (termina con Ctrl+D)
at 02:00
> /usr/local/bin/maintenance.sh
> echo "Manutenzione completata" | mail -s "Maint" admin@example.com
> <Ctrl+D>

# Da pipe
echo "/usr/local/bin/task.sh" | at 14:30

# Gestione
atq                                 # Lista job in attesa
atrm 3                              # Rimuovi job #3

# Controllo accesso
/etc/at.allow
/etc/at.deny
```

### batch

```bash
# batch esegue quando il load average scende sotto 1.5 (configurabile)
batch
> /usr/local/bin/heavy-task.sh
> <Ctrl+D>

# Ideale per task pesanti che devono aspettare un momento di basso carico
```

---

## systemd Timers

I timer systemd sono l'alternativa moderna a cron. Offrono logging integrato (journald), dipendenze, timer persistenti (recuperano esecuzioni mancate), e resource control via cgroup.

```bash
# Struttura: servono 2 file per ogni timer:
# 1. Il .timer (quando eseguire)
# 2. Il .service (cosa eseguire)

# /etc/systemd/system/backup.timer
# [Unit]
# Description=Daily Backup Timer
#
# [Timer]
# OnCalendar=*-*-* 02:30:00        # Ogni giorno alle 2:30
# Persistent=true                   # Esegui al boot se mancata
# RandomizedDelaySec=300            # Ritardo random fino a 5 min (evita thundering herd)
# AccuracySec=60                    # Precisione 1 minuto (default)
#
# [Install]
# WantedBy=timers.target

# /etc/systemd/system/backup.service
# [Unit]
# Description=Daily Backup
#
# [Service]
# Type=oneshot
# ExecStart=/usr/local/bin/backup.sh
# User=backup
# Group=backup
# MemoryMax=512M
# CPUQuota=50%
# StandardOutput=journal

# Gestione
sudo systemctl daemon-reload
sudo systemctl enable --now backup.timer

# Stato di tutti i timer
systemctl list-timers --all

# Formato OnCalendar:
# OnCalendar=hourly                 # Ogni ora
# OnCalendar=daily                  # Ogni giorno a mezzanotte
# OnCalendar=weekly                 # Ogni lunedì a mezzanotte
# OnCalendar=*-*-* 06:00:00         # Ogni giorno alle 6:00
# OnCalendar=Mon..Fri *-*-* 08:00   # Lun-Ven alle 8:00
# OnCalendar=*-*-1 00:00:00         # Primo del mese
# OnCalendar=*-*-* *:00/15:00       # Ogni 15 minuti

# Timer monotono (dall'avvio o dall'attivazione):
# OnBootSec=5min                    # 5 min dopo il boot
# OnUnitActiveSec=1h                # 1 ora dopo l'ultima attivazione
# OnStartupSec=30s                  # 30 sec dopo l'avvio di systemd

# Verificare la prossima esecuzione
systemctl status backup.timer

# Eseguire manualmente il servizio (test)
sudo systemctl start backup.service

# Log
journalctl -u backup.service --since today

# Vantaggi su cron:
# - Logging centralizzato in journald
# - Resource control (CPU, memoria, I/O via cgroup)
# - Dipendenze (After=, Requires=)
# - Persistent=true → recupera esecuzioni mancate
# - RandomizedDelaySec → evita thundering herd
# - Sandboxing (ProtectSystem, PrivateTmp, etc.)
```

---

## Best Practices

1. **SIGTERM prima di SIGKILL**: sempre `kill PID` prima di `kill -9 PID`. SIGTERM permette al processo di fare cleanup (chiudere file, rilasciare lock, salvare stato). SIGKILL è l'ultimo resort
2. **flock per cron job**: usare `flock -n lockfile command` per evitare che un cron job si sovrapponga alla sua istanza precedente
3. **Output di cron**: sempre redirigere stdout e stderr (`>> /var/log/job.log 2>&1`). Altrimenti l'output finisce in email locale o si perde
4. **Monitorare i zombie**: processi zombie consumano PID ma non risorse. Se sono molti, il processo padre ha un bug (non chiama `wait()`). Identificare e correggere il padre
5. **nice per task non critici**: backup, compilazioni, report → `nice -n 19` per non impattare i servizi di produzione
6. **Preferire systemd timer a cron**: per nuove schedulazioni, i timer systemd offrono logging (journald), dipendenze, persistent, resource control. Cron resta valido per semplicità
7. **ulimit PRIMA di avviare il servizio**: i limiti sono ereditati dal padre. Impostarli nel .service file o in limits.conf, non dopo l'avvio
8. **Monitorare oom_score_adj**: proteggere database e servizi critici con `-1000`, marcare processi sacrificabili con valori positivi
9. **ionice per I/O pesante**: backup, rsync, compilazioni → `ionice -c 3` (idle) per non saturare il disco
10. **cgroups per isolamento**: usare MemoryMax, CPUQuota, IOWeight per impedire che un servizio affami gli altri
11. **strace per debugging**: quando un processo ha un comportamento inspiegabile, `strace -p <PID>` rivela cosa sta facendo
12. **Capabilities invece di setuid**: assegnare solo le capabilities necessarie invece di dare root pieno
13. **Seccomp per servizi esposti**: limitare le syscall disponibili per ridurre la superficie di attacco
14. **ProcessRealTime con cautela**: SCHED_FIFO/RR possono rendere il sistema inutilizzabile se mal configurati. Usare sempre `sched_rt_runtime_us` come safety net

---

## Troubleshooting — 25 Problemi Comuni

**1. "Processo non risponde a kill"** → `kill -9 PID` come ultimo resort. Se anche SIGKILL non funziona: il processo è in stato D (uninterruptible sleep), tipicamente bloccato su I/O. Il problema è hardware (disco guasto, NFS hang). Verificare `dmesg` per errori I/O.

**2. "Troppi processi zombie"** → `ps aux | awk '$8=="Z"'` per listarli. Il problema è nel processo padre (PPID). `kill -SIGCHLD PPID` potrebbe sbloccare il padre. Se persiste: bug nel software padre, segnalare/aggiornare.

**3. "Cron job non viene eseguito"** → Checklist: (1) `crontab -l` mostra il job? (2) Il PATH è corretto? Cron usa un PATH minimale. (3) Permessi del script? (4) Log: `grep CRON /var/log/syslog`. (5) L'utente è in `/etc/cron.deny`? (6) Il servizio cron è attivo? `systemctl status cron`.

**4. "Processo consuma troppa memoria"** → `ps aux --sort=-%mem | head`. Se è un memory leak: il RSS cresce continuamente nel tempo. Soluzioni temporanee: restart del processo, impostare `MemoryMax` in systemd. Soluzione permanente: correggere il bug nel software.

**5. "OOM Killer ha ucciso il mio processo"** → Controllare: `dmesg | grep -i oom` e `journalctl -k | grep -i oom`. Mostra quale processo è stato ucciso e perché. Soluzioni: (1) Aumentare RAM. (2) Configurare `oom_score_adj` per proteggere processi critici. (3) Impostare `MemoryMax` via cgroup per contenere processi ingordi. (4) Controllare `vm.overcommit_memory`: 0=default, 1=sempre (pericoloso), 2=mai overcommit.

**6. "Fork bomb — sistema bloccato"** → Una fork bomb crea processi esponenzialmente: `:(){ :|:& };:`. Prevenzione: limitare `nproc` in `/etc/security/limits.conf`. Recupero: se riesci a ottenere una shell, `killall -9 -u <utente>`. Se il sistema è completamente bloccato: SysRq (Alt+SysRq+e per SIGTERM a tutti, Alt+SysRq+i per SIGKILL a tutti).

```bash
# Prevenzione fork bomb:
# /etc/security/limits.conf
# * soft nproc 4096
# * hard nproc 8192
```

**7. "Processo usa 100% CPU"** → `top` o `htop` per identificare. `strace -c -p <PID>` per capire cosa fa. Se è un loop infinito: controllare i log, debuggare o terminare. Se è legittimo (compilazione, encoding): `renice 19 -p <PID>` per ridurre l'impatto.

**8. "File descriptor leak"** → Il processo apre file/socket/pipe ma non li chiude. `ls /proc/<PID>/fd/ | wc -l` mostra il conteggio. Se cresce continuamente: fd leak. `lsof -p <PID>` per vedere cosa è aperto. Soluzione temporanea: restart. Soluzione permanente: fix del codice.

**9. "Too many open files"** → `ulimit -n` mostra il limite (default 1024). Aumentare: per la sessione `ulimit -n 65536`, permanente in `/etc/security/limits.conf` o nel .service systemd con `LimitNOFILE=65536`.

**10. "Processo in stato D non uccidibile"** → Vedi [Diagnosi dei Processi in Stato D](#diagnosi-dei-processi-in-stato-d). Controllare `cat /proc/<PID>/wchan` e `dmesg`. Risolvere il problema I/O sottostante.

**11. "Processo non scrive i log"** → Controllare: (1) `strace -e trace=write -p <PID>` per vedere se scrive. (2) `ls -la /proc/<PID>/fd/1` per stdout. (3) Il processo potrebbe scrivere su un buffer non flushato. (4) Verificare che il log path esista e abbia permessi corretti.

**12. "Processo non trova una libreria"** → `ldd /path/to/binary` per mostrare le dipendenze. `strace -e trace=openat ./binary 2>&1 | grep 'lib.*\.so'` per vedere dove cerca. `ldconfig -v` per aggiornare la cache delle librerie. Aggiungere il path in `/etc/ld.so.conf.d/`.

**13. "Processi orfani che non vengono raccolti"** → Su sistemi con subreaper (PR_SET_CHILD_SUBREAPER), il processo subreaper è responsabile. Se il subreaper non chiama `wait()`, gli orfani restano zombie. Controllare con `prctl(PR_GET_CHILD_SUBREAPER)`.

**14. "Processo avviato ma termina subito"** → `systemctl status <service>` per vedere l'exit code. `journalctl -u <service> -n 50` per i log. `strace -f -o /tmp/trace.log /path/to/binary` per tracciare le syscall. Exit code comuni: 1=errore generico, 126=permesso negato, 127=comando non trovato, 139=segfault (128+11).

**15. "SIGPIPE uccide il processo"** → Un processo che scrive su una pipe/socket il cui lettore ha chiuso riceve SIGPIPE. Per ignorarlo: `trap '' PIPE` in bash, `signal(SIGPIPE, SIG_IGN)` in C, o usare `MSG_NOSIGNAL` flag su `send()`.

**16. "Processo consuma troppa banda I/O"** → `iotop` per identificare. `ionice -c 3 -p <PID>` per relegare a idle I/O. Per limitare: cgroup IO controller con `io.max`. In systemd: `IOWriteBandwidthMax=/dev/sda 10M`.

**17. "Processo genera troppi thread"** → `ps -T -p <PID> | wc -l` per contare. Limitare: `TasksMax=100` in systemd, o `pids.max` nel cgroup. Diagnosticare: perché genera tanti thread? Possibile thread pool non limitato.

**18. "Processo bloccato su un lock (deadlock)"** → `strace -p <PID>` mostra `futex(... FUTEX_WAIT ...)` in loop. Per Java: `jstack <PID>` o `kill -QUIT <PID>` (thread dump su stderr). Per Python: `py-spy dump --pid <PID>`.

**19. "Context switch eccessivi"** → `pidstat -w -p <PID> 1` per monitorare. Voluntary=il processo cede la CPU (I/O wait). Involuntary=il scheduler toglie la CPU (CPU contention). Tanti involuntary = troppi processi per poche CPU.

**20. "Processo non riesce a fare bind su porta"** → Tre cause: (1) `EADDRINUSE` → la porta è già in uso: `ss -tlnp | grep :80`. (2) `EACCES` → serve root o `CAP_NET_BIND_SERVICE` per porte < 1024. (3) `EADDRNOTAVAIL` → IP non assegnato all'interfaccia.

**21. "Processo si riavvia in loop"** → `systemctl status <service>` mostra quanti restart. `journalctl -u <service> --since '1 hour ago'` per i crash. Verificare `Restart=` policy nel .service. Se Restart=always e il processo crashha subito: `RestartSec=5` per rallentare i restart. `StartLimitIntervalSec` e `StartLimitBurst` per bloccare dopo troppi tentativi.

**22. "Processo usa più CPU di quella allocata via cgroup"** → Verificare: `cat /sys/fs/cgroup/.../cpu.max`. Se il formato è `max 100000`, non c'è limite. La CPU quota si applica per-core: `200000 100000` = 200% = 2 core. Controllare `cpu.stat` per `nr_throttled`.

**23. "Swap thrashing — sistema lentissimo"** → `vmstat 1` mostra `si`/`so` (swap in/out). `swapon --show` per vedere l'uso. Soluzioni: (1) `sysctl vm.swappiness=10` per ridurre la propensione allo swap. (2) Identificare il processo ingordo: `ps aux --sort=-rss`. (3) Aggiungere RAM. (4) Limitare con `MemoryMax` nei cgroup.

**24. "Processo non risponde a SIGTERM"** → Il processo sta ignorando SIGTERM o ha un handler che non termina. Verificare: `grep SigIgn /proc/<PID>/status` e decodificare il bitmask. Se il bit 14 (SIGTERM, bit 15 in base 0) è settato, SIGTERM è ignorato. Usare `kill -9` come ultimo resort.

**25. "Load average alto ma CPU idle"** → Load average include processi in stato D (I/O wait). `vmstat 1` mostra `wa` (I/O wait %). `iostat -x 1` mostra %util dei dischi. Se i dischi sono saturi: risolvere il collo di bottiglia I/O. Se è NFS: controllare la connettività al server.

---

## FAQ — 18 Domande e Risposte

**Q1: Qual è la differenza tra processo e thread?**
Un processo ha il proprio spazio di indirizzamento (memoria isolata). Un thread condivide lo spazio di indirizzamento con altri thread nello stesso processo. Su Linux, thread e processi sono entrambi implementati come `task_struct`; la differenza è quante risorse condividono. `clone()` con `CLONE_VM | CLONE_FS | CLONE_FILES` crea un thread; senza quei flag, crea un processo.

**Q2: Come faccio a sapere perché un processo è stato ucciso?**
Controllare: (1) `dmesg | grep -i "killed process"` per OOM killer. (2) `journalctl -k | grep -i oom` per OOM. (3) `ausearch -m ANOM_ABEND` per crash. (4) `coredumpctl list` per core dump (se abilitati). (5) L'exit code: 128+N significa ucciso dal segnale N (es. 137=SIGKILL, 139=SIGSEGV, 143=SIGTERM).

**Q3: Qual è la differenza tra RSS e VSZ?**
VSZ (Virtual Size) è la memoria virtuale totale del processo: include memoria allocata ma non usata, librerie mappate, stack. RSS (Resident Set Size) è la memoria fisica effettivamente in RAM. RSS è la metrica utile per capire l'uso reale di memoria. PSS (Proportional Set Size) è la metrica più precisa: divide la memoria condivisa tra tutti i processi che la condividono.

**Q4: Posso cambiare le variabili d'ambiente di un processo in esecuzione?**
No, non direttamente. `/proc/<PID>/environ` è read-only e mostra le variabili al momento dell'avvio. Per cambiare il comportamento di un processo: inviare un segnale (es. SIGHUP per reload config), usare un meccanismo di configurazione del processo (API, file di config), oppure riavviarlo con le nuove variabili.

**Q5: Qual è la differenza tra kill, killall e pkill?**
`kill <PID>` invia un segnale a un PID specifico. `killall <nome>` invia a tutti i processi con quel nome esatto. `pkill <pattern>` usa pattern matching (regex) sul nome o sulla linea di comando (`pkill -f`). Attenzione: `killall` su Solaris uccide TUTTI i processi (non per nome). Su Linux è sicuro.

**Q6: Come proteggo un processo dall'OOM killer?**
`echo -1000 | sudo tee /proc/<PID>/oom_score_adj`. Per servizi systemd: `OOMScoreAdjust=-1000` nel .service file. ATTENZIONE: proteggere un processo significa che l'OOM killer ucciderà un altro processo. Non proteggere tutto: qualcosa DEVE poter essere ucciso quando la memoria finisce.

**Q7: Quando devo usare SCHED_FIFO vs SCHED_RR?**
SCHED_FIFO per task che devono completare il prima possibile senza time-slicing (es. interrupt handler in user space). SCHED_RR quando vuoi real-time ma con equità tra processi della stessa priorità (es. multiple istanze di un player audio). SCHED_DEADLINE per workload periodici con requisiti stretti (es. controllo industriale).

**Q8: Come rilevo un memory leak?**
Monitorare RSS nel tempo: `while true; do awk '/VmRSS/ {print $2}' /proc/<PID>/status; sleep 60; done | tee /tmp/rss.log`. Se RSS cresce monotonicamente senza mai scendere, c'è un leak. Tool avanzati: `valgrind --leak-check=full ./app` (C/C++), `py-spy` per Python, `async-profiler` per Java.

**Q9: Cosa sono i context switch e perché importano?**
Un context switch è quando il kernel salva lo stato di un processo e carica quello di un altro. Ha un costo: 1-10 microsecondi + cache miss. Tanti context switch = overhead. Voluntary (il processo cede la CPU per I/O) sono normali. Involuntary (il scheduler toglie la CPU) indicano CPU contention. Monitorare con `pidstat -w`.

**Q10: Come funziona l'ereditarietà dei segnali in fork()?**
Il figlio eredita la disposizione dei segnali dal padre: handler registrati, segnali ignorati, maschera di segnali. I segnali pendenti NON sono ereditati (il figlio parte con zero segnali pendenti). Dopo `exec()`, tutti gli handler vengono resettati a default (perché il codice dell'handler non esiste più), ma i segnali ignorati restano ignorati.

**Q11: Perché il load average ha tre numeri?**
I tre numeri rappresentano la media esponenziale dei processi in coda (R) + processi in I/O wait (D) negli ultimi 1, 5 e 15 minuti. Utile per capire il trend: load_1 >> load_15 = carico in crescita. load_1 << load_15 = carico in diminuzione. Un load average uguale al numero di CPU core indica saturazione.

**Q12: Come faccio un graceful shutdown di un servizio?**
(1) `kill <PID>` (SIGTERM) → il processo fa cleanup. (2) Aspettare `TimeoutStopSec` (default 90s in systemd). (3) Se non termina, `kill -9 <PID>` (SIGKILL). systemd fa questo automaticamente con `systemctl stop`. Per un servizio che accetta connessioni: smettere di accettare nuove connessioni, completare quelle in corso, poi terminare.

**Q13: Cosa sono le SysRq e quando servono?**
Magic SysRq keys sono comandi di emergenza direttamente al kernel, funzionano anche quando il sistema è completamente bloccato. Alt+SysRq+B = reboot immediato. Alt+SysRq+E = SIGTERM a tutti. Alt+SysRq+I = SIGKILL a tutti. Alt+SysRq+S = sync dischi. La sequenza di shutdown sicuro: REISUB (unRaw, tErminate, kIll, Sync, Unmount, reBoot).

**Q14: Come monitorare i processi di un container dall'host?**
I processi container sono visibili dall'host con PID diversi. `docker top <container>` mostra i processi. Dall'host: `ps aux | grep` o usare il PID del container (`docker inspect --format '{{.State.Pid}}' <container>`). I file in `/proc/<container_pid>/` sono accessibili dall'host.

**Q15: Qual è la differenza tra setsid, nohup e disown?**
`nohup` ignora SIGHUP e redirige l'output. `disown` rimuove il job dalla shell. `setsid` crea una nuova sessione, scollegando completamente il processo dal terminale. Per un daemon robusto: `setsid` è il più pulito, ma per uso interattivo `nohup ... &; disown` è pratico.

**Q16: Come funziona /proc/sys/vm/overcommit_memory?**
0 (default) = il kernel usa euristiche per decidere se accettare allocazioni. 1 = accetta sempre (pericoloso: OOM killer più probabile). 2 = non overcommittare: la somma delle allocazioni non può superare swap + RAM * overcommit_ratio%. Per database e sistemi critici: 2 è più sicuro (fallisce malloc() invece di invocare OOM killer).

**Q17: Come trovo i processi che ascoltano su una porta specifica?**
`ss -tlnp | grep :8080` o `lsof -i :8080`. Per UDP: `ss -ulnp | grep :5353`. Per tutti i socket (TCP+UDP+Unix): `ss -lnp`. Il flag `-p` mostra il processo (richiede root per processi di altri utenti).

**Q18: Cosa succede ai processi quando si fa suspend/hibernate?**
Tutti i processi vengono congelati (SIGSTOP equivalente) dal kernel. I timer (alarm, setitimer) vengono sospesi. Al resume, tutti i processi riprendono. I timer vengono ricalcolati. Le connessioni di rete potrebbero essere interrotte (TCP timeout). I processi non si accorgono del suspend (a meno che controllino il tempo trascorso).

---

## Esercizi Pratici con Soluzioni

### Esercizio 1: Analizzare un processo specifico

**Obiettivo**: Raccogliere tutte le informazioni su un processo in esecuzione.

```bash
# Avviare un processo di test
sleep 3600 &
PID=$!

# Esercizio: per il PID ottenuto, trovare:
# 1. La linea di comando completa
# 2. Lo stato del processo
# 3. La memoria RSS
# 4. I file descriptor aperti
# 5. Il cgroup di appartenenza
# 6. Le capabilities
# 7. I limiti di risorse
# 8. In quale namespace si trova
```

**Soluzione:**

```bash
PID=$(pgrep -f "sleep 3600")

echo "=== 1. Linea di comando ==="
cat /proc/$PID/cmdline | tr '\0' ' '
echo

echo "=== 2. Stato ==="
awk '/State/ {print}' /proc/$PID/status

echo "=== 3. Memoria RSS ==="
awk '/VmRSS/ {print $2, $3}' /proc/$PID/status

echo "=== 4. File descriptor ==="
ls -la /proc/$PID/fd/

echo "=== 5. Cgroup ==="
cat /proc/$PID/cgroup

echo "=== 6. Capabilities ==="
grep -i cap /proc/$PID/status

echo "=== 7. Limiti ==="
cat /proc/$PID/limits

echo "=== 8. Namespace ==="
ls -la /proc/$PID/ns/

# Cleanup
kill $PID
```

### Esercizio 2: Gestire segnali in uno script

**Obiettivo**: Scrivere uno script che gestisca SIGTERM, SIGINT, SIGUSR1 e SIGUSR2.

```bash
# Esercizio: creare uno script che:
# - Su SIGTERM/SIGINT: fa cleanup e termina
# - Su SIGUSR1: incrementa un contatore e lo logga
# - Su SIGUSR2: scrive lo stato corrente in un file
# - Logga il PID all'avvio
```

**Soluzione:**

```bash
#!/bin/bash
COUNTER=0
STATEFILE="/tmp/myapp_state"
LOGFILE="/tmp/myapp.log"

log() { echo "$(date -Is) $1" >> "$LOGFILE"; }

cleanup() {
    log "Terminazione. Contatore finale: $COUNTER"
    rm -f /tmp/myapp.pid
    exit 0
}

increment() {
    COUNTER=$((COUNTER + 1))
    log "SIGUSR1: contatore incrementato a $COUNTER"
}

dump_state() {
    {
        echo "PID: $$"
        echo "Contatore: $COUNTER"
        echo "Uptime: $(ps -o etime= -p $$)"
        echo "Memoria RSS: $(awk '/VmRSS/ {print $2, $3}' /proc/$$/status)"
        echo "FD aperti: $(ls /proc/$$/fd/ | wc -l)"
    } > "$STATEFILE"
    log "SIGUSR2: stato scritto in $STATEFILE"
}

trap cleanup SIGTERM SIGINT EXIT
trap increment SIGUSR1
trap dump_state SIGUSR2

echo $$ > /tmp/myapp.pid
log "Avvio. PID: $$"

while true; do
    sleep 1
done

# Test:
# Terminal 1: bash esercizio2.sh
# Terminal 2: kill -USR1 $(cat /tmp/myapp.pid)   # incrementa
# Terminal 2: kill -USR2 $(cat /tmp/myapp.pid)   # dump stato
# Terminal 2: cat /tmp/myapp_state
# Terminal 2: kill $(cat /tmp/myapp.pid)          # termina
```

### Esercizio 3: Creare e gestire cgroup manualmente

**Obiettivo**: Creare un cgroup v2 custom, limitare memoria e CPU, spostare un processo.

```bash
# Esercizio: creare un cgroup con:
# - Limite memoria 50 MB
# - Limite CPU 25% di 1 core
# - Spostare un processo stress nel cgroup
# - Monitorare l'uso delle risorse
```

**Soluzione:**

```bash
# 1. Creare il cgroup
sudo mkdir -p /sys/fs/cgroup/exercise

# 2. Abilitare controller
echo "+cpu +memory" | sudo tee /sys/fs/cgroup/cgroup.subtree_control

# 3. Impostare limiti
echo 52428800 | sudo tee /sys/fs/cgroup/exercise/memory.max        # 50 MB
echo "25000 100000" | sudo tee /sys/fs/cgroup/exercise/cpu.max     # 25%

# 4. Avviare un processo e spostarlo nel cgroup
stress --vm 1 --vm-bytes 30M --cpu 1 &
STRESS_PID=$!
echo $STRESS_PID | sudo tee /sys/fs/cgroup/exercise/cgroup.procs

# 5. Monitorare
echo "=== Uso memoria ==="
cat /sys/fs/cgroup/exercise/memory.current
echo "=== Statistiche CPU ==="
cat /sys/fs/cgroup/exercise/cpu.stat
echo "=== Processi nel cgroup ==="
cat /sys/fs/cgroup/exercise/cgroup.procs

# 6. Cleanup
kill $STRESS_PID
sudo rmdir /sys/fs/cgroup/exercise
```

### Esercizio 4: Debug con strace

**Obiettivo**: Usare strace per diagnosticare perché un programma fallisce.

```bash
# Esercizio: un programma tenta di leggere /etc/myapp.conf
# ma il file non esiste. Usare strace per trovare il problema.
```

**Soluzione:**

```bash
# Creare un programma di test che fallisce
cat > /tmp/test_app.sh << 'SCRIPT'
#!/bin/bash
CONFIG=$(cat /etc/myapp.conf 2>/dev/null)
if [ -z "$CONFIG" ]; then
    echo "Errore: configurazione non trovata"
    exit 1
fi
echo "Config: $CONFIG"
SCRIPT
chmod +x /tmp/test_app.sh

# Diagnosi con strace
strace -e trace=openat,access /tmp/test_app.sh 2>&1 | grep myapp
# openat(AT_FDCWD, "/etc/myapp.conf", O_RDONLY) = -1 ENOENT (No such file or directory)
# → Il file /etc/myapp.conf non esiste

# Soluzione:
echo "key=value" | sudo tee /etc/myapp.conf
/tmp/test_app.sh
# Config: key=value

# Cleanup
sudo rm /etc/myapp.conf /tmp/test_app.sh
```

### Esercizio 5: Monitorare zombie e orfani

**Obiettivo**: Creare processi zombie e orfani, identificarli, risolverli.

```bash
# Esercizio: creare processi zombie e orfani,
# listarli, diagnosticarli, risolverli
```

**Soluzione:**

```bash
# Creare un processo zombie
# Il padre non chiama wait(), il figlio diventa zombie
bash -c '
    /bin/sleep 1 &          # figlio che termina dopo 1 secondo
    sleep 30                 # padre rimane vivo senza wait()
' &
PARENT=$!

echo "Padre: $PARENT"
sleep 2  # aspettare che il figlio termini

# Verificare
echo "=== Zombie ==="
ps -eo pid,ppid,stat,comm | grep -w Z
# Il zombie avrà PPID = $PARENT

echo "=== Albero del padre ==="
pstree -p $PARENT

# Risolvere: uccidere il padre (PID 1 raccoglierà il figlio zombie)
kill $PARENT
sleep 1
echo "=== Dopo aver ucciso il padre ==="
ps -eo pid,ppid,stat,comm | grep -w Z
# Nessun zombie

# Creare un processo orfano
bash -c '(sleep 60 &); exit'
sleep 1
echo "=== Orfani (PPID=1) ==="
ps -eo pid,ppid,comm | awk '$2 == 1 && $3 == "sleep"'

# Cleanup
pkill -f "sleep 60"
```

### Esercizio 6: Namespace per isolamento

**Obiettivo**: Creare un ambiente isolato usando i namespace.

```bash
# Esercizio: creare un processo con PID namespace separato
# e verificare l'isolamento
```

**Soluzione:**

```bash
# Creare un PID namespace isolato
echo "=== PID namespace host ==="
echo "PID nel host: $$"
ps aux | wc -l

echo "=== Creazione PID namespace ==="
sudo unshare --pid --fork --mount-proc bash -c '
    echo "PID nel namespace: $$"
    echo "Processi visibili:"
    ps aux
    echo "Totale processi: $(ps aux | wc -l)"
    echo "PID 1 (in questo namespace):"
    cat /proc/1/comm
'
# Nel namespace, ci saranno solo 2-3 processi
# PID 1 sarà "bash", non "systemd"
```

### Esercizio 7: Creare un servizio systemd con limiti

**Obiettivo**: Creare un servizio hardened con limiti di risorse e sicurezza.

```bash
# Esercizio: creare un servizio systemd che:
# - Esegue uno script
# - Ha limiti di memoria (100M), CPU (50%), file descriptor (1024)
# - È protetto dall'OOM killer
# - Ha hardening di sicurezza
# - Si riavvia in caso di crash
```

**Soluzione:**

```bash
# Creare lo script
sudo tee /usr/local/bin/exercise-service.sh << 'SCRIPT'
#!/bin/bash
echo "Servizio avviato, PID: $$"
while true; do
    echo "$(date -Is) Heartbeat PID $$"
    sleep 10
done
SCRIPT
sudo chmod +x /usr/local/bin/exercise-service.sh

# Creare il service file
sudo tee /etc/systemd/system/exercise.service << 'SERVICE'
[Unit]
Description=Exercise Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/exercise-service.sh
Restart=on-failure
RestartSec=5

# Limiti risorse
MemoryMax=100M
MemoryHigh=80M
CPUQuota=50%
LimitNOFILE=1024
TasksMax=10
OOMScoreAdjust=-500

# Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true

[Install]
WantedBy=multi-user.target
SERVICE

# Attivare
sudo systemctl daemon-reload
sudo systemctl start exercise.service
sudo systemctl status exercise.service

# Verificare i limiti
PID=$(systemctl show exercise.service --property=MainPID --value)
cat /proc/$PID/limits | grep "Max open files"
cat /proc/$PID/cgroup

# Verificare il cgroup
CGROUP_PATH=$(cat /proc/$PID/cgroup | cut -d: -f3)
cat /sys/fs/cgroup${CGROUP_PATH}/memory.max
cat /sys/fs/cgroup${CGROUP_PATH}/cpu.max

# Cleanup
sudo systemctl stop exercise.service
sudo systemctl disable exercise.service
sudo rm /etc/systemd/system/exercise.service /usr/local/bin/exercise-service.sh
sudo systemctl daemon-reload
```

---

## Workflow: Metodologia Sistematica di Debug Processi

Quando un processo ha un problema, segui questo workflow sistematico:

```
FASE 1: IDENTIFICAZIONE
────────────────────────
                          ┌─────────────────────┐
                          │ Quale processo?      │
                          │ - PID, nome, utente  │
                          └──────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                 │
            ┌───────▼──────┐ ┌──────▼───────┐ ┌──────▼───────┐
            │ ps aux       │ │ top / htop   │ │ pstree -p    │
            │ ps -eo ...   │ │ (interattivo)│ │ (relazioni)  │
            └───────┬──────┘ └──────┬───────┘ └──────┬───────┘
                    └────────────────┼────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │ PID identificato     │
                          └──────────┬──────────┘
                                     │

FASE 2: RACCOLTA INFORMAZIONI
──────────────────────────────
                                     │
               ┌─────────────────────┼─────────────────────┐
               │                     │                      │
    ┌──────────▼─────────┐ ┌────────▼────────┐ ┌──────────▼──────────┐
    │ /proc/<PID>/status │ │ /proc/<PID>/fd  │ │ /proc/<PID>/stack   │
    │ stato, memoria,    │ │ file descriptor │ │ (se in stato D)     │
    │ thread, segnali    │ │ aperti          │ │                     │
    └──────────┬─────────┘ └────────┬────────┘ └──────────┬──────────┘
               │                     │                      │
    ┌──────────▼─────────┐ ┌────────▼────────┐ ┌──────────▼──────────┐
    │ /proc/<PID>/limits │ │ /proc/<PID>/io  │ │ /proc/<PID>/maps    │
    │ limiti risorse     │ │ statistiche I/O │ │ mappatura memoria   │
    └──────────┬─────────┘ └────────┬────────┘ └──────────┬──────────┘
               └─────────────────────┼─────────────────────┘
                                     │

FASE 3: DIAGNOSI
─────────────────
                                     │
                          ┌──────────▼──────────┐
                          │ Qual è il sintomo?   │
                          └──────────┬──────────┘
                                     │
          ┌──────────┬───────────┬───┼───┬───────────┬──────────┐
          │          │           │       │           │          │
   ┌──────▼─────┐┌──▼────┐┌────▼───┐┌──▼────┐┌────▼────┐┌────▼────┐
   │ CPU 100%   ││Memoria││Stato D ││Zombie ││Lento   ││Non     │
   │            ││  alta ││        ││       ││        ││avvia   │
   └──────┬─────┘└──┬────┘└────┬───┘└──┬────┘└────┬────┘└────┬────┘
          │         │          │       │          │          │
          ▼         ▼          ▼       ▼          ▼          ▼
   strace -c   smaps_rollup  wchan  ps zombie  strace -r   strace
   perf top    /proc/PID/io  stack  kill PPID  pidstat     journalctl
   pidstat     valgrind      dmesg             iotop       systemctl
```

```bash
# Script di diagnosi rapida per un processo
diagnose_process() {
    local pid=$1

    if [ ! -d "/proc/$pid" ]; then
        echo "ERRORE: Processo $pid non trovato"
        return 1
    fi

    local comm=$(cat /proc/$pid/comm 2>/dev/null)
    echo "╔══════════════════════════════════════════════"
    echo "║ DIAGNOSI PROCESSO: $comm (PID $pid)"
    echo "╠══════════════════════════════════════════════"

    # Stato
    local state=$(awk '/State/ {print $2, $3}' /proc/$pid/status)
    echo "║ Stato:     $state"

    # Memoria
    local rss=$(awk '/VmRSS/ {print $2, $3}' /proc/$pid/status 2>/dev/null)
    local vsz=$(awk '/VmSize/ {print $2, $3}' /proc/$pid/status 2>/dev/null)
    echo "║ RSS:       ${rss:-N/A}"
    echo "║ VSZ:       ${vsz:-N/A}"

    # Thread
    local threads=$(awk '/Threads/ {print $2}' /proc/$pid/status)
    echo "║ Thread:    $threads"

    # File descriptor
    local fds=$(ls /proc/$pid/fd/ 2>/dev/null | wc -l)
    local fd_limit=$(awk '/Max open files/ {print $4}' /proc/$pid/limits)
    echo "║ FD:        $fds / $fd_limit"

    # CPU time
    local cputime=$(ps -o time= -p $pid 2>/dev/null)
    echo "║ CPU Time:  $cputime"

    # Uptime
    local etime=$(ps -o etime= -p $pid 2>/dev/null)
    echo "║ Uptime:    $etime"

    # OOM score
    local oom=$(cat /proc/$pid/oom_score 2>/dev/null)
    local oom_adj=$(cat /proc/$pid/oom_score_adj 2>/dev/null)
    echo "║ OOM Score: $oom (adj: $oom_adj)"

    # Context switch
    local vol=$(awk '/voluntary_ctxt_switches/ {print $2}' /proc/$pid/status)
    local invol=$(awk '/nonvoluntary_ctxt_switches/ {print $2}' /proc/$pid/status)
    echo "║ Ctx Switch: vol=$vol invol=$invol"

    # Segnali pendenti
    local sigpnd=$(awk '/SigPnd/ {print $2}' /proc/$pid/status)
    echo "║ SigPnd:    $sigpnd"

    # Cgroup
    local cgroup=$(cat /proc/$pid/cgroup 2>/dev/null | head -1)
    echo "║ Cgroup:    $cgroup"

    # Wait channel (se in sleep)
    local wchan=$(cat /proc/$pid/wchan 2>/dev/null)
    if [ -n "$wchan" ] && [ "$wchan" != "0" ]; then
        echo "║ WChan:     $wchan"
    fi

    # Alerting
    echo "╠══════════════════════════════════════════════"
    echo "║ ALERT:"

    # Troppi FD
    if [ "$fds" -gt "$((fd_limit * 80 / 100))" ] 2>/dev/null; then
        echo "║ ⚠ FD al ${fds}/${fd_limit} (>80%)"
    fi

    # Zombie
    if echo "$state" | grep -q "Z"; then
        local ppid=$(awk '/PPid/ {print $2}' /proc/$pid/status)
        echo "║ ⚠ ZOMBIE — padre PID $ppid"
    fi

    # Stato D
    if echo "$state" | grep -q "D"; then
        echo "║ ⚠ UNINTERRUPTIBLE SLEEP — possibile I/O hang"
        echo "║   wchan: $(cat /proc/$pid/wchan 2>/dev/null)"
        echo "║   Controllare: dmesg | grep -i error"
    fi

    # RSS alto (>1GB)
    local rss_kb=$(awk '/VmRSS/ {print $2}' /proc/$pid/status 2>/dev/null)
    if [ "${rss_kb:-0}" -gt 1048576 ] 2>/dev/null; then
        echo "║ ⚠ RSS > 1 GB ($rss)"
    fi

    echo "╚══════════════════════════════════════════════"
}

# Uso: diagnose_process <PID>
# diagnose_process $(pidof nginx)
```

```bash
# Workflow completo di debug:

# PASSO 1: Identificare il processo problematico
ps -eo pid,ppid,user,%cpu,%mem,stat,etime,comm --sort=-%cpu | head -20
# O per memoria:
ps -eo pid,ppid,user,%cpu,%mem,stat,etime,comm --sort=-%mem | head -20

# PASSO 2: Raccolta rapida
PID=<pid_problematico>
cat /proc/$PID/status
cat /proc/$PID/limits
ls /proc/$PID/fd/ | wc -l
cat /proc/$PID/io

# PASSO 3: Comportamento real-time
# CPU/memoria nel tempo:
pidstat -rud -p $PID 1 10

# PASSO 4: Cosa sta facendo (syscall)
sudo strace -c -p $PID
# Dopo 10 secondi, Ctrl+C per il sommario

# PASSO 5: Se è un problema di I/O
sudo iotop -p $PID
iostat -x 1 3

# PASSO 6: Se è un problema di rete
ss -tnp | grep $PID
sudo strace -e trace=network -p $PID

# PASSO 7: Se è un problema di lock/deadlock
sudo strace -e trace=futex -p $PID
# Per Java: jstack $PID
# Per Python: py-spy dump --pid $PID

# PASSO 8: Se è un crash
coredumpctl list
dmesg | tail -50
journalctl -u <service> --since '1 hour ago'

# PASSO 9: Azione correttiva
# - Troppa CPU: renice 19 -p $PID
# - Troppa memoria: MemoryMax via cgroup/systemd
# - Troppo I/O: ionice -c 3 -p $PID
# - Processo rotto: kill $PID (SIGTERM, poi SIGKILL)
# - OOM: oom_score_adj per proteggere critici
# - Zombie: kill PPID o kill -SIGCHLD PPID
```
