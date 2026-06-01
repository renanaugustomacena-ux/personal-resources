# SELinux e AppArmor: Mandatory Access Control — Guida Approfondita

> **Modulo 27** · **Aggiornamento:** 2026-04-27

> **Modulo del corso:** 02-LINUX-POWERUSER — Modulo 27
> **Prerequisiti:** Conoscenza avanzata della gestione utenti/permessi Unix (DAC), familiarità con systemd, gestione dei servizi, concetti base di kernel Linux (moduli, sysfs), esperienza con audit log e journalctl.
> **Obiettivi di apprendimento:**
> 1. Comprendere l'architettura interna di SELinux (LSM hooks, AVC, policy store) e AppArmor (LSM path-based, policy cache)
> 2. Configurare, gestire e diagnosticare policy SELinux (contesti, booleans, moduli custom, porte, MLS/MCS)
> 3. Creare, mantenere e debuggare profili AppArmor (enforce/complain, aa-genprof, regole dbus/mount/signal)
> 4. Applicare seccomp per il filtraggio delle syscall nei container e nei servizi
> 5. Integrare MAC con strumenti di compliance (lynis, aide, osquery)
> 6. Risolvere almeno 15 scenari di troubleshooting reali
> 7. Implementare hardening MAC completo per web server, database e container host
>
> **Tempo stimato:** 12-16 ore di studio + laboratorio
> **Livello:** Avanzato
> **Ultimo aggiornamento contenuti:** 2026-05-23
> **Versioni di riferimento:** SELinux policy 3.6+ (RHEL 9.x / Fedora 40+), AppArmor 4.x (Ubuntu 24.04+), kernel 6.x, Podman 5.x, Docker 27.x

## Idee guida
1. **SELinux (RHEL/Fedora) vs AppArmor (Ubuntu/Debian).**
2. **Permissive mode > enforcing in dev; reverse in prod.**
3. **`audit2allow` per generate policy from denials.**
4. **Monthly audit review + rule tuning.**


## Indice

- [Panoramica](#panoramica)
- [DAC vs MAC: Fondamenti](#dac-vs-mac-fondamenti)
- [SELinux: Architettura](#selinux-architettura)
  - [LSM Framework e Hook Interni](#lsm-framework-e-hook-interni)
  - [AVC — Access Vector Cache](#avc--access-vector-cache)
  - [Policy Store e Ciclo di Vita](#policy-store-e-ciclo-di-vita)
- [SELinux: Contesti e Label](#selinux-contesti-e-label)
- [SELinux: Policy e Booleans](#selinux-policy-e-booleans)
  - [Tipi di Policy: targeted, MLS, minimum](#tipi-di-policy-targeted-mls-minimum)
  - [MCS e MLS: Sicurezza Multi-Livello](#mcs-e-mls-sicurezza-multi-livello)
- [SELinux: Gestione con semanage](#selinux-gestione-con-semanage)
  - [Creazione di Moduli Custom Avanzati](#creazione-di-moduli-custom-avanzati)
- [SELinux: audit2allow e Troubleshooting](#selinux-audit2allow-e-troubleshooting)
  - [setroubleshoot e sealert](#setroubleshoot-e-sealert)
- [SELinux: Scenari Comuni](#selinux-scenari-comuni)
- [SELinux e Container](#selinux-e-container)
- [AppArmor: Architettura](#apparmor-architettura)
  - [Internals LSM Path-Based](#internals-lsm-path-based)
  - [Policy Cache e Parser](#policy-cache-e-parser)
- [AppArmor: Creazione e Gestione Profili](#apparmor-creazione-e-gestione-profili)
  - [Sintassi Avanzata dei Profili](#sintassi-avanzata-dei-profili)
- [AppArmor: aa-genprof e aa-logprof](#apparmor-aa-genprof-e-aa-logprof)
- [AppArmor e Container](#apparmor-e-container)
- [AppArmor: Debugging Avanzato](#apparmor-debugging-avanzato)
- [Confronto SELinux vs AppArmor](#confronto-selinux-vs-apparmor)
- [Confronto Esteso: SELinux vs AppArmor vs TOMOYO vs Smack](#confronto-esteso-selinux-vs-apparmor-vs-tomoyo-vs-smack)
- [Audit e Rollback Playbook](#audit-e-rollback-playbook)
- [seccomp: Filtraggio Syscall](#seccomp-filtraggio-syscall)
- [Integrazione con lynis, aide, osquery](#integrazione-con-lynis-aide-osquery)
- [Scenari di Hardening Reali](#scenari-di-hardening-reali)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Esercizi](#esercizi)
- [Auto-valutazione](#auto-valutazione)
- [Letture Primarie Consigliate](#letture-primarie-consigliate)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario Locale](#glossario-locale)
- [Riferimenti](#riferimenti)

---

## Panoramica

Il Mandatory Access Control (MAC) rappresenta un livello di sicurezza fondamentale per i sistemi Linux moderni, complementare al tradizionale Discretionary Access Control (DAC) dei permessi Unix. Mentre il DAC permette ai proprietari dei file di decidere chi può accedervi, il MAC impone politiche di sicurezza definite dall'amministratore di sistema che nemmeno l'utente root può aggirare.

SELinux (Security-Enhanced Linux) e AppArmor sono i due principali framework MAC per Linux. SELinux, sviluppato originariamente dalla NSA e adottato come default da Red Hat Enterprise Linux, Fedora e CentOS, implementa un modello di sicurezza basato su label (etichette) assegnate a ogni oggetto e soggetto del sistema. AppArmor, sviluppato originariamente da Novell e ora mantenuto da Canonical, implementa un modello basato su path (percorsi) ed è il default in Ubuntu, Debian e SUSE.

Questo documento fornisce una guida operativa completa per entrambi i framework, con enfasi sulla risoluzione dei problemi più comuni che un system administrator incontra quotidianamente. La tentazione di disabilitare SELinux o AppArmor al primo errore è una delle peggiori pratiche di sicurezza diffuse nel mondo Linux — questo documento mira a fornire le competenze per lavorare CON il MAC anziché contro di esso.

---

## DAC vs MAC: Fondamenti

### DAC (Discretionary Access Control)

Il modello di sicurezza tradizionale Unix basato su owner/group/other e permessi rwx:

```bash
# Il proprietario decide i permessi
chmod 644 /var/www/html/index.html
# Owner: rw-, Group: r--, Other: r--

# Root può TUTTO — questo è il problema fondamentale del DAC
# Se un attaccante ottiene root (o compromette un processo root),
# ha accesso completo a tutto il sistema
```

**Problema**: Un web server compromesso in esecuzione come root ha accesso a `/etc/shadow`, `/etc/ssh/`, il database, i file di tutti gli utenti. Il DAC non limita cosa un processo può fare in base al suo ruolo.

### MAC (Mandatory Access Control)

Il MAC aggiunge un livello di policy che limita cosa ogni processo può fare, indipendentemente dall'utente che lo esegue:

```
┌──────────────────────────────────────────────┐
│           Richiesta di accesso                │
│  (processo → file/socket/porta)               │
└──────────────┬───────────────────────────────┘
               │
     ┌─────────▼─────────┐
     │   DAC Check        │ ← Permessi Unix (rwx)
     │   (uid/gid based)  │
     └─────────┬─────────┘
               │ Permesso?
     ┌─────────▼─────────┐
     │   MAC Check        │ ← SELinux / AppArmor policy
     │   (policy based)   │
     └─────────┬─────────┘
               │ Permesso?
     ┌─────────▼─────────┐
     │   ACCESSO          │
     │   CONSENTITO        │
     └────────────────────┘
```

Entrambi i check devono passare. Il MAC può solo negare, mai concedere accesso che il DAC ha negato.

### Modelli MAC nel Kernel Linux

Il kernel Linux supporta i framework MAC tramite il **Linux Security Modules (LSM)** framework, un'interfaccia generica che permette a diversi moduli di sicurezza di inserire controlli di accesso nelle operazioni del kernel. A partire dal kernel 5.1+ è possibile impilare (stacking) più LSM minori insieme a un LSM maggiore.

```
┌─────────────────────────────────────────────────────────┐
│                    System Call Interface                  │
├─────────────────────────────────────────────────────────┤
│                    VFS / IPC / Net                        │
│                         │                                │
│              ┌──────────▼──────────┐                     │
│              │    LSM Hook Point   │                     │
│              │  security_inode_*   │                     │
│              │  security_file_*    │                     │
│              │  security_socket_*  │                     │
│              │  security_task_*    │                     │
│              │  security_cred_*    │                     │
│              └──────────┬──────────┘                     │
│                         │                                │
│          ┌──────────────┼──────────────┐                 │
│          │              │              │                  │
│    ┌─────▼─────┐  ┌─────▼─────┐ ┌─────▼─────┐          │
│    │  SELinux  │  │ AppArmor  │ │  Smack    │          │
│    │  TOMOYO   │  │ Yama      │ │ Landlock  │          │
│    └───────────┘  └───────────┘ └───────────┘          │
├─────────────────────────────────────────────────────────┤
│                    Hardware / CPU                         │
└─────────────────────────────────────────────────────────┘
```

I "major LSM" (SELinux, AppArmor, Smack, TOMOYO) sono mutuamente esclusivi: solo uno può essere attivo come LSM principale. I "minor LSM" (Yama, Landlock, LoadPin, SafeSetID, Lockdown) possono essere impilati insieme al major.

```bash
# Verifica quali LSM sono attivi
cat /sys/kernel/security/lsm
# Esempio RHEL: lockdown,capability,yama,selinux
# Esempio Ubuntu: landlock,lockdown,yama,integrity,apparmor

# Il parametro kernel lsm= controlla l'ordine
# In /etc/default/grub o /etc/kernel/cmdline:
# GRUB_CMDLINE_LINUX="... lsm=landlock,lockdown,yama,integrity,apparmor"
```

> **Fonte:** kernel.org, Documentation/admin-guide/LSM/ — consultato 2026-05-23.

---

## SELinux: Architettura

### Componenti

```
User Space:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  semanage    │  │  audit2allow │  │  restorecon  │
│  setsebool   │  │  sesearch    │  │  chcon       │
└──────────────┘  └──────────────┘  └──────────────┘

Kernel Space:
┌──────────────────────────────────────────────────┐
│              SELinux Security Server              │
│  ┌────────────┐  ┌──────────────┐               │
│  │  Policy DB │  │  AVC (Access │               │
│  │            │  │  Vector Cache)│               │
│  └────────────┘  └──────────────┘               │
├──────────────────────────────────────────────────┤
│              Linux Security Modules (LSM)        │
├──────────────────────────────────────────────────┤
│              Linux Kernel                         │
└──────────────────────────────────────────────────┘
```

### LSM Framework e Hook Interni

Il kernel Linux implementa circa 230 punti di hook LSM distribuiti nelle operazioni su file, socket, processi, IPC, chiavi di crittografia e operazioni di rete. Quando un processo tenta un'operazione (es. `open()` su un file), il kernel esegue prima i controlli DAC e poi invoca l'hook LSM corrispondente.

```
Processo chiama open("/var/www/html/index.html", O_RDONLY)
    │
    ▼
┌─────────────────────────┐
│ VFS: vfs_open()          │
│  → controllo DAC (rwx)   │
│  → hook: security_       │
│    inode_permission()     │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ SELinux:                 │
│  selinux_inode_          │
│    permission()          │
│                          │
│  1. Recupera contesto    │
│     soggetto (httpd_t)   │
│  2. Recupera contesto    │
│     oggetto              │
│     (httpd_sys_content_t)│
│  3. Cerca in AVC         │
│  4. Se miss → consulta   │
│     Security Server      │
│  5. Ritorna ALLOW/DENY   │
└─────────────────────────┘
```

Gli hook principali per categoria:

| Categoria | Hook LSM | Operazione |
|-----------|----------|------------|
| **File** | `security_inode_permission` | Accesso a inode (read/write/exec) |
| **File** | `security_inode_create` | Creazione file |
| **File** | `security_inode_link` | Creazione hard link |
| **File** | `security_inode_rename` | Rinomina file |
| **File** | `security_file_open` | Apertura file |
| **Socket** | `security_socket_create` | Creazione socket |
| **Socket** | `security_socket_bind` | Bind su porta |
| **Socket** | `security_socket_connect` | Connessione in uscita |
| **Socket** | `security_socket_listen` | Listen su porta |
| **Processo** | `security_task_create` | Fork/clone |
| **Processo** | `security_bprm_check` | Esecuzione binario (execve) |
| **Processo** | `security_task_kill` | Invio segnale |
| **IPC** | `security_msg_queue_msgsnd` | Invio messaggio IPC |
| **Chiavi** | `security_key_permission` | Accesso a keyring |

> **Fonte:** kernel.org, include/linux/lsm_hooks.h — consultato 2026-05-23.

### AVC — Access Vector Cache

L'AVC è una hash table nel kernel che memorizza le decisioni di accesso recenti per evitare di consultare il Security Server a ogni operazione. Ogni entry contiene la coppia (source_type, target_type, object_class) e il vettore di permessi (allow/deny).

```
┌───────────────────────────────────────────────────────┐
│                  AVC (kernel space)                    │
│                                                        │
│  Chiave: (source_type, target_type, class)            │
│  Valore: allowed_permissions bitmask                   │
│                                                        │
│  ┌──────────────────────────────────────────────┐     │
│  │ (httpd_t, httpd_sys_content_t, file)         │     │
│  │  → ALLOW: read, getattr, open, ioctl         │     │
│  │  → DENY:  write, append, create, unlink       │     │
│  ├──────────────────────────────────────────────┤     │
│  │ (httpd_t, httpd_log_t, file)                 │     │
│  │  → ALLOW: read, write, append, create, open   │     │
│  │  → DENY:  execute, unlink                      │     │
│  ├──────────────────────────────────────────────┤     │
│  │ (sshd_t, shadow_t, file)                     │     │
│  │  → ALLOW: read, getattr, open                 │     │
│  │  → DENY:  write, append                        │     │
│  └──────────────────────────────────────────────┘     │
│                                                        │
│  Statistiche:                                          │
│  - Hit ratio tipico: 99%+                              │
│  - Dimensione default: 512 slot, espandibile           │
│  - Flush automatico al reload della policy             │
└───────────────────────────────────────────────────────┘
```

```bash
# Statistiche AVC
cat /sys/fs/selinux/avc/cache_stats
# lookups  hits  misses  allocations  reclaims  frees
# 1254321  1253890  431  431  0  0

# Hash table stats
cat /sys/fs/selinux/avc/hash_stats
# entries: 312
# buckets used: 198/512

# Flush manuale dell'AVC (dopo cambio policy)
echo 1 > /sys/fs/selinux/avc/cache_threshold
# oppure semplicemente:
semodule -B   # rebuild + flush
```

> **Fonte:** SELinux Project Wiki, selinuxproject.org/page/NB_AVC — consultato 2026-05-23.

### Policy Store e Ciclo di Vita

La policy SELinux attraversa un ciclo di compilazione a più stadi prima di essere caricata nel kernel.

```
┌─────────────────────────────────────────────────────────────┐
│                  Ciclo di Vita della Policy                   │
│                                                              │
│  Sorgente (.te/.if/.fc)                                      │
│      │                                                       │
│      ▼  checkmodule -M -m -o                                 │
│  Modulo compilato (.mod)                                     │
│      │                                                       │
│      ▼  semodule_package -o                                  │
│  Pacchetto (.pp)                                             │
│      │                                                       │
│      ▼  semodule -i                                          │
│  Policy Store (/var/lib/selinux/<type>/)                     │
│      │                                                       │
│      ▼  semodule -B (build + load)                           │
│  Policy binaria (/etc/selinux/<type>/policy/policy.<ver>)    │
│      │                                                       │
│      ▼  load_policy / security_load_policy()                 │
│  Kernel (Security Server + AVC flush)                        │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Il policy store vive in:
ls /var/lib/selinux/targeted/
# active/  previous/  tmp/

# I moduli installati:
ls /var/lib/selinux/targeted/active/modules/400/
# my_httpd_fix/  ...

# La policy binaria caricata dal kernel:
ls /etc/selinux/targeted/policy/
# policy.33   (il numero è la versione del formato)

# Verifica versione max supportata dal kernel
cat /sys/fs/selinux/policyvers
# 33

# Ricostruisci la policy senza installare nuovi moduli
semodule -B
```

I file sorgente della policy sono suddivisi in tre componenti:

| File | Estensione | Scopo |
|------|-----------|-------|
| Type Enforcement | `.te` | Regole allow/deny, transizioni di tipo, attributi |
| File Contexts | `.fc` | Mapping percorso filesystem → contesto SELinux |
| Interface | `.if` | Macro riutilizzabili per interagire con il modulo |

### Modalità Operative

```bash
# Verifica modalità corrente
getenforce
# Enforcing  — policy attivamente applicata (produzione)
# Permissive — policy non applicata, solo logging (debug)
# Disabled   — SELinux completamente disabilitato

# Cambia modalità temporaneamente (fino al reboot)
setenforce 0   # Permissive
setenforce 1   # Enforcing

# Configurazione permanente: /etc/selinux/config
SELINUX=enforcing
SELINUXTYPE=targeted

# Stato dettagliato
sestatus
# SELinux status:                 enabled
# SELinuxfs mount:                /sys/fs/selinux
# SELinux root directory:         /etc/selinux
# Loaded policy name:             targeted
# Current mode:                   enforcing
# Mode from config file:          enforcing
# Policy MLS status:              enabled
# Policy deny_unknown status:     allowed
# Memory protection checking:     actual (secure)
# Max kernel policy version:      33
```

> **Attenzione critica:** Il passaggio da `disabled` a `enforcing` richiede un relabel completo del filesystem. Tutti gli inode creati mentre SELinux era disabilitato non hanno contesto. Dopo aver cambiato `/etc/selinux/config`, creare `/.autorelabel` e riavviare. Il primo boot sarà lento (proporzionale al numero di inode).

```bash
# Passaggio sicuro da disabled a enforcing
# 1. Modifica /etc/selinux/config → SELINUX=permissive (NON enforcing!)
# 2. Relabel
touch /.autorelabel
reboot
# 3. Verifica che non ci siano denial critici in permissive
ausearch -m avc --start today | audit2why | head -50
# 4. Solo se tutto OK → SELINUX=enforcing
# 5. Reboot finale
```

---

## SELinux: Contesti e Label

Ogni oggetto nel sistema (file, processo, porta, socket) ha un contesto SELinux composto da quattro campi:

```
user:role:type:level

Esempio: system_u:object_r:httpd_sys_content_t:s0
         │        │         │                  │
         │        │         │                  └── Livello MLS (Multi-Level Security)
         │        │         └── Tipo (il più importante!)
         │        └── Ruolo
         └── Utente SELinux
```

### Visualizzazione Contesti

```bash
# File
ls -Z /var/www/html/
# -rw-r--r--. root root system_u:object_r:httpd_sys_content_t:s0 index.html

# Processi
ps auxZ | grep httpd
# system_u:system_r:httpd_t:s0    root  1234  ... /usr/sbin/httpd

# Porte
semanage port -l | grep http
# http_port_t    tcp    80, 443, 488, 8008, 8009, 8443

# Utente corrente
id -Z
# unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023
```

### Utenti SELinux e Ruoli

La relazione tra utenti Linux, utenti SELinux e ruoli determina cosa un utente autenticato può fare nel sistema:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Utente Linux │ ──→ │ Utente SELinux│ ──→ │   Ruolo      │ ──→ │   Tipo       │
│ (john)       │     │ (staff_u)    │     │ (staff_r)    │     │ (staff_t)    │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                     │
                                                          ┌──────────▼──────────┐
                                                          │ Dominio di processo  │
                                                          │ (cosa può fare)      │
                                                          └─────────────────────┘
```

| Utente SELinux | Ruoli permessi | Uso tipico |
|---------------|----------------|------------|
| `unconfined_u` | `unconfined_r`, `system_r` | Utente non confinato (default) |
| `user_u` | `user_r` | Utente confinato, no sudo, no su |
| `staff_u` | `staff_r`, `sysadm_r` | Staff, può sudo verso ruoli confinati |
| `sysadm_u` | `sysadm_r` | Amministratore di sistema |
| `system_u` | `system_r` | Solo processi di sistema (nessun login) |
| `root` | `staff_r`, `sysadm_r`, `system_r`, `unconfined_r` | Utente root |

```bash
# Confinare utenti esistenti per hardening
# Mappa tutti i nuovi utenti a user_u (più restrittivo)
semanage login -m -s user_u -r s0 __default__

# Mappa un admin a staff_u (può fare sudo confinato)
semanage login -a -s staff_u admin_user

# Verifica mapping corrente
semanage login -l
# Login Name   SELinux User   MLS/MCS Range   Service
# __default__  user_u         s0              *
# admin_user   staff_u        s0-s0:c0.c1023  *
# root         unconfined_u   s0-s0:c0.c1023  *
```

### Type Enforcement

Il Type Enforcement è il cuore di SELinux nella policy `targeted`. Le regole definiscono quale tipo di processo può accedere a quale tipo di oggetto:

```
# Regola concettuale (non sintassi reale):
allow httpd_t httpd_sys_content_t:file { read getattr open };
#     │        │                        │
#     │        │                        └── Operazioni permesse
#     │        └── Tipo dell'oggetto (file)
#     └── Tipo del soggetto (processo)

# httpd (tipo httpd_t) può leggere file con tipo httpd_sys_content_t
# httpd NON può leggere file con tipo user_home_t (home degli utenti)
# httpd NON può leggere file con tipo shadow_t (/etc/shadow)
```

### Transizioni di Tipo

Le transizioni di tipo determinano automaticamente il dominio in cui un processo viene eseguito e il tipo che un file riceve alla creazione:

```bash
# Transizione di dominio: quando init (init_t) esegue /usr/sbin/httpd,
# il processo entra nel dominio httpd_t automaticamente
# type_transition init_t httpd_exec_t:process httpd_t;

# Transizione di file: quando httpd_t crea un file in /var/log/httpd/,
# il file riceve automaticamente il tipo httpd_log_t
# type_transition httpd_t httpd_log_t:file httpd_log_t;

# Verifica le transizioni di dominio per un eseguibile
sesearch -T -s init_t -t httpd_exec_t
# type_transition init_t httpd_exec_t:process httpd_t;

# Verifica quali tipi un dominio può creare
sesearch -T -s httpd_t -c file
```

### Modifica Contesti

```bash
# Cambia contesto temporaneamente (non sopravvive a restorecon/relabel)
chcon -t httpd_sys_content_t /var/www/custom/file.html

# Cambia contesto ricorsivamente
chcon -R -t httpd_sys_content_t /var/www/custom/

# Ripristina contesto dal database delle policy
restorecon -v /var/www/html/index.html

# Ripristina ricorsivamente
restorecon -Rv /var/www/

# Modifica permanente: definisci regola nel database
semanage fcontext -a -t httpd_sys_content_t "/srv/web(/.*)?"
restorecon -Rv /srv/web/

# Lista regole di contesto
semanage fcontext -l | grep "/var/www"

# Relabel completo del filesystem (dopo cambio policy o fix)
touch /.autorelabel
reboot
# oppure
fixfiles relabel
```

---

## SELinux: Policy e Booleans

### Tipi di Policy: targeted, MLS, minimum

SELinux fornisce tre tipi di policy, ognuno con un diverso livello di copertura:

```bash
# Configurata in /etc/selinux/config → SELINUXTYPE=
```

**targeted** (default su RHEL/Fedora):
- Solo i servizi di rete e i daemon sono confinati
- Gli utenti interattivi eseguono in `unconfined_t` (non confinati)
- ~400-500 moduli policy che coprono httpd, sshd, named, mysqld, etc.
- Migliore compromesso tra sicurezza e usabilità
- Approccio: default-allow per utenti, default-deny per servizi

**minimum**:
- Subset della policy targeted
- Solo un piccolo numero di servizi critici confinati
- Utile su sistemi embedded o con risorse limitate
- Stesso formato di targeted, moduli specifici attivabili con `semodule -e`

**MLS** (Multi-Level Security):
- Policy completa che confina TUTTI i processi e utenti
- Implementa la classificazione dei dati (Unclassified → Secret → Top Secret)
- Conforme a requisiti militari/governativi (Bell-LaPadula model)
- Molto complessa da gestire, richiede pianificazione accurata
- Usata per certificazioni Common Criteria (EAL4+)

```bash
# Cambiare tipo di policy (richiede relabel)
# 1. Installa la policy desiderata
dnf install selinux-policy-mls

# 2. Modifica /etc/selinux/config
# SELINUXTYPE=mls

# 3. Relabel e reboot
touch /.autorelabel
reboot

# ATTENZIONE: passare a MLS su un sistema esistente è un'operazione
# complessa. È consigliato partire da un'installazione pulita con MLS.
```

### Booleans

I boolean sono interruttori on/off che modificano il comportamento della policy senza riscriverla:

```bash
# Lista tutti i boolean
getsebool -a

# Lista boolean relativi a httpd
getsebool -a | grep httpd

# Esempi comuni:
getsebool httpd_can_network_connect      # httpd può connettersi alla rete
getsebool httpd_can_network_connect_db   # httpd può connettersi a DB
getsebool httpd_enable_homedirs          # httpd può servire home dir
getsebool httpd_use_nfs                  # httpd può usare NFS

# Modifica temporanea (fino al reboot)
setsebool httpd_can_network_connect on

# Modifica permanente
setsebool -P httpd_can_network_connect on

# Verifica quale boolean serve (cerca nel log)
ausearch -m avc --start recent | audit2why
# Spesso audit2why suggerisce il boolean da attivare
```

### Boolean Comuni per Servizi

```bash
# Web server (Apache/Nginx)
setsebool -P httpd_can_network_connect 1       # proxy verso backend
setsebool -P httpd_can_network_connect_db 1    # connessione database
setsebool -P httpd_can_sendmail 1              # invio email
setsebool -P httpd_use_nfs 1                   # uso NFS
setsebool -P httpd_enable_cgi 1                # CGI scripts

# Samba
setsebool -P samba_enable_home_dirs 1
setsebool -P samba_export_all_rw 1

# FTP
setsebool -P ftpd_full_access 1
setsebool -P ftpd_use_passive_mode 1

# NFS
setsebool -P nfs_export_all_rw 1
setsebool -P use_nfs_home_dirs 1

# Container
setsebool -P container_manage_cgroup 1
setsebool -P container_connect_any 1
```

### MCS e MLS: Sicurezza Multi-Livello

#### MCS — Multi-Category Security

MCS è una versione semplificata di MLS usata nella policy `targeted`. Assegna categorie (`c0`-`c1023`) ai processi e agli oggetti per creare isolamento orizzontale. È il meccanismo usato dai container runtime per isolare i container tra loro.

```
Formato livello MCS: s0:c<n>,c<m>

Esempi:
  s0               — nessuna categoria (default)
  s0:c0            — categoria 0
  s0:c0,c5         — categorie 0 e 5
  s0:c0.c1023      — tutte le categorie (unconfined)
```

```bash
# Verifica il range MCS di un processo
ps auxZ | grep httpd
# system_u:system_r:httpd_t:s0  ← s0 senza categorie

# Verifica il range MCS di un utente
id -Z
# unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023

# Assegna categoria a un file
chcat +c100,c200 /path/to/file
# oppure
chcon -l s0:c100,c200 /path/to/file

# Solo i processi con almeno le stesse categorie possono accedervi

# Container: Podman/Docker assegna automaticamente MCS casuali
# Container A: s0:c123,c456
# Container B: s0:c789,c012
# → A non può accedere ai file di B e viceversa
```

#### MLS — Multi-Level Security

MLS implementa il modello Bell-LaPadula per classificazione gerarchica dei dati:

```
Livelli di sensibilità (sensibilità crescente):
  s0 — Unclassified
  s1 — Confidential
  s2 — Secret
  s3 — Top Secret

Regole fondamentali (Bell-LaPadula):
  - No Read Up:   un processo a livello s1 NON può leggere file a s2
  - No Write Down: un processo a livello s2 NON può scrivere file a s1
                   (previene la declassificazione accidentale)

Esempio:
  Processo in s1 (Confidential):
    ✓ Può leggere file s0, s1
    ✗ Non può leggere file s2, s3
    ✓ Può scrivere file s1, s2, s3
    ✗ Non può scrivere file s0
```

```bash
# Su un sistema MLS, gestione livelli
# Crea un utente con clearance fino a Secret (s0-s2)
semanage login -a -s staff_u -r s0-s2 classified_user

# Assegna livello a un file
chcon -l s2:c0 /data/secret/document.pdf

# Verifica
ls -Z /data/secret/document.pdf
# ... s2:c0 document.pdf
```

> **Fonte:** NIST SP 800-123, "Guide to General Server Security", Sezione 5.3 — consultato 2026-05-23.

---

## SELinux: Gestione con semanage

`semanage` è lo strumento principale per la gestione persistente della policy SELinux.

### Gestione Contesti File

```bash
# Aggiungi regola di contesto per una directory custom
semanage fcontext -a -t httpd_sys_content_t "/opt/webapp(/.*)?"
restorecon -Rv /opt/webapp/

# Modifica regola esistente
semanage fcontext -m -t httpd_sys_rw_content_t "/opt/webapp/uploads(/.*)?"
restorecon -Rv /opt/webapp/uploads/

# Elimina regola
semanage fcontext -d "/opt/webapp(/.*)?"

# Lista tutte le regole custom (non quelle di default)
semanage fcontext -l -C
```

### Gestione Porte

```bash
# Visualizza associazione porte-tipi
semanage port -l | grep http
# http_port_t    tcp    80, 443, 488, 8008, 8009, 8443

# Aggiungi porta custom per httpd
semanage port -a -t http_port_t -p tcp 8080
semanage port -a -t http_port_t -p tcp 3000

# Per SSH su porta non standard
semanage port -a -t ssh_port_t -p tcp 2222

# Lista porte custom
semanage port -l -C

# Rimuovi associazione
semanage port -d -t http_port_t -p tcp 8080
```

### Gestione Utenti e Login

```bash
# Mapping utenti Linux → utenti SELinux
semanage login -l

# Mappa un utente Linux a un utente SELinux confinato
semanage login -a -s staff_u john

# Modifica il mapping di default per nuovi utenti
semanage login -m -s user_u -r s0 __default__

# Lista utenti SELinux
semanage user -l

# Utenti SELinux e loro ruoli:
# unconfined_u  — non confinato (default per utenti interattivi)
# staff_u       — può usare sudo con ruoli confinati
# user_u        — utente confinato, no sudo
# sysadm_u      — amministratore di sistema
# system_u      — processi di sistema
```

### Moduli Custom

```bash
# Lista moduli caricati
semodule -l

# Disabilita un modulo
semodule -d my_custom_module

# Abilita un modulo
semodule -e my_custom_module

# Rimuovi un modulo
semodule -r my_custom_module

# Installa modulo da file .pp
semodule -i my_module.pp
```

### Creazione di Moduli Custom Avanzati

Quando `audit2allow` non è sufficiente o si vuole un modulo ben strutturato, è necessario scrivere manualmente i file `.te`, `.fc` e `.if`.

#### Struttura del file .te (Type Enforcement)

```bash
# Esempio: modulo custom per un'applicazione "myapp" che ascolta su porta 9090,
# legge configurazione da /opt/myapp/etc/, scrive log in /var/log/myapp/,
# e si connette a PostgreSQL.

# --- myapp.te ---
policy_module(myapp, 1.0.0)

########################################
# Dichiarazioni
########################################

# Dichiara il tipo per il dominio del processo
type myapp_t;
type myapp_exec_t;
# Marca myapp_exec_t come entry point per myapp_t
init_daemon_domain(myapp_t, myapp_exec_t)

# Tipi per i file
type myapp_conf_t;
files_type(myapp_conf_t)

type myapp_log_t;
logging_log_file(myapp_log_t)

type myapp_var_run_t;
files_pid_file(myapp_var_run_t)

type myapp_port_t;
corenet_port(myapp_port_t)

########################################
# Regole di accesso
########################################

# Il processo può leggere la propria configurazione
allow myapp_t myapp_conf_t:dir list_dir_perms;
allow myapp_t myapp_conf_t:file read_file_perms;

# Il processo può scrivere i propri log
allow myapp_t myapp_log_t:dir { add_name write };
allow myapp_t myapp_log_t:file { create write append open getattr };

# PID file
allow myapp_t myapp_var_run_t:file manage_file_perms;
files_pid_filetrans(myapp_t, myapp_var_run_t, file)

# Rete: bind sulla porta custom
allow myapp_t myapp_port_t:tcp_socket name_bind;

# Rete: connessione a PostgreSQL
corenet_tcp_connect_postgresql_port(myapp_t)

# Risoluzione DNS
sysnet_dns_name_resolve(myapp_t)

# Lettura /etc per timezone, localtime, nsswitch
files_read_etc_files(myapp_t)

# Transizioni di file: quando myapp_t crea file in /var/log/myapp
logging_log_filetrans(myapp_t, myapp_log_t, file)
```

#### File Context (.fc)

```bash
# --- myapp.fc ---
/opt/myapp/bin/myapp    --    gen_context(system_u:object_r:myapp_exec_t, s0)
/opt/myapp/etc(/.*)?          gen_context(system_u:object_r:myapp_conf_t, s0)
/var/log/myapp(/.*)?          gen_context(system_u:object_r:myapp_log_t, s0)
/run/myapp\.pid         --    gen_context(system_u:object_r:myapp_var_run_t, s0)
```

#### Compilazione e Installazione

```bash
# Metodo 1: usando make con il Makefile della policy di riferimento
# (richiede selinux-policy-devel)
make -f /usr/share/selinux/devel/Makefile myapp.pp

# Metodo 2: manuale
checkmodule -M -m -o myapp.mod myapp.te
semodule_package -o myapp.pp -m myapp.mod -f myapp.fc

# Installa
semodule -i myapp.pp

# Registra la porta custom
semanage port -a -t myapp_port_t -p tcp 9090

# Applica i contesti
restorecon -Rv /opt/myapp/ /var/log/myapp/ /run/

# Verifica
semodule -l | grep myapp
ls -Z /opt/myapp/bin/myapp
ls -Z /var/log/myapp/
```

#### Ricerca nella Policy con sesearch

```bash
# Cerca regole allow per un tipo specifico
sesearch --allow -s httpd_t -t httpd_sys_content_t

# Cerca tutte le regole che permettono a httpd_t di fare network connect
sesearch --allow -s httpd_t -c tcp_socket -p name_connect

# Cerca regole condizionate da un boolean
sesearch --allow -b httpd_can_network_connect

# Cerca transizioni di tipo per un dominio
sesearch -T -s httpd_t

# Cerca regole dontaudit (dinieghi silenziosi, non loggati)
sesearch --dontaudit -s httpd_t

# Cerca interfacce disponibili per un tipo
seinfo -t httpd_t -x
```

---

## SELinux: audit2allow e Troubleshooting

### Analisi dei Dinieghi (AVC)

```bash
# Cerca dinieghi recenti nel audit log
ausearch -m avc --start recent

# Formato tipico di un AVC denial:
# type=AVC msg=audit(1712000000.123:456): avc:  denied  { read }
# for  pid=1234 comm="httpd" name="config.yml" dev="sda1" ino=987654
# scontext=system_u:system_r:httpd_t:s0
# tcontext=system_u:object_r:user_home_t:s0
# tclass=file permissive=0

# Interpretazione:
# Il processo httpd (tipo httpd_t) ha tentato di leggere (read)
# il file config.yml che ha tipo user_home_t
# L'accesso è stato negato

# Usa audit2why per spiegazione leggibile
ausearch -m avc --start recent | audit2why

# Output esempio:
# Was caused by:
#   Missing type enforcement (TE) allow rule.
#   You can use audit2allow to generate a loadable module to allow this access.
#
# oppure:
# Was caused by:
#   The boolean httpd_can_network_connect was set incorrectly.
#   Allow httpd to can network connect
#   setsebool -P httpd_can_network_connect 1
```

### Creazione Moduli con audit2allow

```bash
# Genera regola allow dal log
ausearch -m avc --start recent | audit2allow

# Genera un modulo compilabile
ausearch -m avc --start recent | audit2allow -M my_httpd_fix

# Questo crea:
# my_httpd_fix.te   — file sorgente della policy
# my_httpd_fix.pp   — modulo compilato

# Installa il modulo
semodule -i my_httpd_fix.pp

# ATTENZIONE: non usare audit2allow ciecamente!
# Prima verifica che il diniego sia legittimo:
# 1. Il processo DOVREBBE avere quell'accesso?
# 2. Il file ha il tipo corretto? (forse serve restorecon)
# 3. C'è un boolean che risolve?
# audit2allow è l'ultima risorsa, non la prima!
```

### Workflow di Troubleshooting SELinux

```bash
# Step 1: Identificare il problema
# Servizio che non funziona? Controlla se SELinux è la causa
setenforce 0    # metti in Permissive temporaneamente
# Se il servizio funziona → SELinux è la causa
setenforce 1    # rimetti in Enforcing

# Step 2: Trova il denial
ausearch -m avc -ts recent
# oppure
journalctl -t setroubleshoot --since "10 minutes ago"

# Step 3: Analizza con audit2why
ausearch -m avc -ts recent | audit2why

# Step 4: Risolvi (in ordine di preferenza)
# a) Ripristina contesto corretto
restorecon -Rv /path/to/files

# b) Imposta il contesto corretto
semanage fcontext -a -t correct_type "/path(/.*)?"
restorecon -Rv /path/

# c) Abilita il boolean suggerito
setsebool -P suggested_boolean on

# d) Aggiungi porta
semanage port -a -t type_port_t -p tcp PORT

# e) ULTIMO RESORT: crea modulo custom
ausearch -m avc | audit2allow -M fix
semodule -i fix.pp
```

### setroubleshoot e sealert

`setroubleshoot` è il framework di analisi automatica dei denial SELinux. Traduce i messaggi AVC criptici in spiegazioni leggibili con suggerimenti di risoluzione.

```bash
# Installazione (RHEL/Fedora)
dnf install setroubleshoot-server setroubleshoot-plugins

# Il daemon setroubleshootd analizza /var/log/audit/audit.log in tempo reale
# e scrive suggerimenti in /var/log/messages o journal

# Cerca suggerimenti recenti
journalctl -t setroubleshoot --since "1 hour ago"

# Output tipico:
# setroubleshoot: SELinux is preventing httpd from read access on the file
#   /opt/webapp/config.yml.
# For complete SELinux messages run: sealert -l <UUID>

# Visualizza dettagli completi con sealert
sealert -l <UUID>

# Output di sealert:
# SELinux is preventing httpd from read access on the file config.yml.
#
# ***** Plugin catchall_labels (83.8 confidence) suggests ******************
#
# If you want to allow httpd to have read access on the config.yml file
# Then you need to change the label on config.yml
# Do
# # semanage fcontext -a -t httpd_sys_content_t '/opt/webapp/config.yml'
# # restorecon -v '/opt/webapp/config.yml'
#
# ***** Plugin catchall (17.1 confidence) suggests ************************
#
# If you believe that httpd should be allowed read access on the config.yml
# Then you should report this as a bug.
# You can generate a local policy module to allow this access.
# Do
# # ausearch -c 'httpd' --raw | audit2allow -M my-httpd
# # semodule -X 300 -i my-httpd.pp

# Analizza TUTTI i dinieghi del log corrente
sealert -a /var/log/audit/audit.log

# Analisi in tempo reale dei log
tail -f /var/log/audit/audit.log | sealert -a -

# Configura notifiche desktop (se disponibile GUI)
# setroubleshoot mostra automaticamente popup GNOME per ogni denial
```

```bash
# Filtraggio avanzato con ausearch
# Dinieghi per un servizio specifico
ausearch -m avc -c httpd --start today

# Dinieghi per un file specifico
ausearch -m avc -f /opt/webapp/config.yml

# Dinieghi per un tipo specifico
ausearch -m avc | grep "scontext=.*httpd_t"

# Solo dinieghi (non successi)
ausearch -m avc --success no

# Formato raw per pipe verso audit2allow
ausearch -m avc --raw --start today | audit2allow -M fix_today
```

---

## SELinux: Scenari Comuni

### Scenario: Nginx serve file da directory custom

```bash
# Problema: Nginx restituisce 403 per file in /opt/webapp
# Il file esiste e i permessi Unix sono corretti

# Diagnosi
ls -Z /opt/webapp/
# -rw-r--r--. root root unconfined_u:object_r:usr_t:s0 index.html
# Tipo: usr_t — Nginx (httpd_t) non può leggere usr_t!

# Soluzione
semanage fcontext -a -t httpd_sys_content_t "/opt/webapp(/.*)?"
semanage fcontext -a -t httpd_sys_rw_content_t "/opt/webapp/uploads(/.*)?"
restorecon -Rv /opt/webapp/

# Verifica
ls -Z /opt/webapp/
# -rw-r--r--. root root system_u:object_r:httpd_sys_content_t:s0 index.html
```

### Scenario: Applicazione su porta non standard

```bash
# Problema: Node.js su porta 3000, Nginx reverse proxy riceve connection refused

# Diagnosi
ausearch -m avc | grep httpd | grep connect
# denied { name_connect } ... scontext=...httpd_t... tcontext=...unreserved_port_t

# Soluzione: due opzioni

# Opzione A: Abilita connessione generica
setsebool -P httpd_can_network_connect 1

# Opzione B: Aggiungi la porta al tipo http
semanage port -a -t http_port_t -p tcp 3000
```

### Scenario: Container che accede a volumi host

```bash
# Problema: Container Docker/Podman non può leggere volume montato

# Diagnosi
ausearch -m avc | grep container

# Soluzione per Podman
podman run -v /data:/data:Z myimage  # Z applica il contesto SELinux corretto

# Per Docker
chcon -Rt svirt_sandbox_file_t /data
# oppure
semanage fcontext -a -t svirt_sandbox_file_t "/data(/.*)?"
restorecon -Rv /data/
```

---

## SELinux e Container

I container runtime moderni si affidano a SELinux per fornire isolamento multi-layer. Comprendere l'interazione tra SELinux e i container è fondamentale per la sicurezza di un container host.

### Architettura SELinux per Container

```
┌──────────────────────────────────────────────────────────────┐
│                    Container Host (SELinux enforcing)          │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ Container A      │  │ Container B      │                   │
│  │ container_t      │  │ container_t      │                   │
│  │ s0:c100,c200     │  │ s0:c300,c400     │  ← MCS diverso   │
│  │                  │  │                  │                   │
│  │ /data/a/  ──────────── svirt_sandbox_  │                   │
│  │ s0:c100,c200     │  │ file_t           │                   │
│  │                  │  │ s0:c300,c400     │                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                               │
│  Container A NON può accedere ai file di Container B          │
│  perché le categorie MCS sono diverse                         │
│  (c100,c200 ≠ c300,c400)                                     │
└──────────────────────────────────────────────────────────────┘
```

### Tipi SELinux per Container

| Tipo | Descrizione |
|------|-------------|
| `container_t` | Dominio processo container standard |
| `container_init_t` | Dominio per container con systemd interno |
| `container_kvm_t` | Dominio per container KVM (kata containers) |
| `container_engine_t` | Dominio del container runtime (podman, docker) |
| `container_file_t` | File accessibili dai container |
| `container_var_lib_t` | File in `/var/lib/containers/` |
| `container_log_t` | Log dei container |
| `container_share_t` | File condivisi tra container |
| `container_ro_file_t` | File read-only per i container |
| `svirt_sandbox_file_t` | File scrivibili dal container (volumi) |

### Flag di Volume Podman/Docker

```bash
# :z — contesto condiviso (shared): tutti i container possono accedere
podman run -v /shared-data:/data:z myimage
# Applica container_share_t al volume
# ATTENZIONE: tutti i container sullo stesso host possono leggere/scrivere

# :Z — contesto privato (private): solo questo container può accedere
podman run -v /private-data:/data:Z myimage
# Applica svirt_sandbox_file_t con le categorie MCS del container
# Solo QUESTO container può accedere ai dati

# Senza flag: il container potrebbe non riuscire ad accedere al volume
# a meno che il contesto SELinux non sia già corretto

# Verifica contesti dopo montaggio
podman inspect --format '{{.MountLabel}}' <container_id>
# system_u:system_r:container_t:s0:c100,c200
```

### udica — Generazione Automatica di Policy per Container

`udica` (sviluppato da Red Hat) genera policy SELinux custom per container analizzando i loro file `inspect` e i log AVC.

```bash
# Installazione
dnf install udica

# Workflow:
# 1. Esegui il container con --security-opt label=disable (temporaneo!)
podman run --security-opt label=disable -v /data:/data:rw myapp

# 2. Ispeziona il container
podman inspect <container_id> > container.json

# 3. Genera la policy
udica -j container.json my_container_policy

# Output:
# Policy my_container_policy created with:
# allow process:
#   - tcp bind on port 8080
#   - read/write on /data
#
# To install:
#   semodule -i my_container_policy.cil
#
# To run container with this policy:
#   podman run --security-opt label=type:my_container_policy.process ...

# 4. Installa e usa
semodule -i my_container_policy.cil
podman run --security-opt label=type:my_container_policy.process \
    -v /data:/data:Z myapp
```

### SELinux e Docker

```bash
# Abilita SELinux per Docker (se non attivo)
# /etc/docker/daemon.json
{
    "selinux-enabled": true
}

# Riavvia Docker
systemctl restart docker

# Verifica
docker info | grep -i selinux
# Security Options: seccomp selinux

# Boolean comuni per container Docker
setsebool -P container_manage_cgroup 1    # container gestisce cgroups
setsebool -P container_connect_any 1      # container si connette a qualsiasi porta
```

> **Fonte:** Red Hat, "Using SELinux with container runtimes", access.redhat.com — consultato 2026-05-23.

---

## AppArmor: Architettura

AppArmor implementa il MAC utilizzando un modello basato sui percorsi dei file (path-based) anziché sulle etichette. Ogni programma confinato ha un profilo che definisce esattamente cosa può fare.

### Concetti Fondamentali

```
┌──────────────────────────────────────────────┐
│              AppArmor                         │
│                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Profile  │  │ Profile  │  │ Profile  │   │
│  │ /usr/bin │  │ /usr/sbin│  │ custom   │   │
│  │ /nginx   │  │ /sshd    │  │ /app     │   │
│  └──────────┘  └──────────┘  └──────────┘   │
│                                               │
│  Modalità:                                    │
│  - enforce  (applica il profilo)              │
│  - complain (solo log, non blocca)            │
│  - unconfined (nessun profilo)                │
└──────────────────────────────────────────────┘
```

### Internals LSM Path-Based

A differenza di SELinux che associa label a inode, AppArmor risolve i permessi in base al percorso del file al momento dell'accesso. Il kernel verifica il profilo del processo corrente e cerca nel profilo se il percorso richiesto è autorizzato.

```
Processo /usr/sbin/nginx chiama open("/var/www/html/index.html", O_RDONLY)
    │
    ▼
┌──────────────────────────────────────┐
│ VFS: vfs_open()                      │
│  → DAC check (permessi Unix)        │
│  → LSM hook: security_file_open()    │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ AppArmor: apparmor_file_open()       │
│                                       │
│ 1. Recupera il profilo attivo per il  │
│    processo (namespace + label)       │
│ 2. Calcola il percorso canonico del   │
│    file richiesto                     │
│ 3. Cerca nel profilo una regola che   │
│    matcha il percorso                 │
│ 4. Verifica che i permessi richiesti  │
│    (r) siano consentiti               │
│ 5. Se match → ALLOW                  │
│    Se no match → DENY + log          │
│    Se complain mode → ALLOW + log    │
└──────────────────────────────────────┘
```

**Implicazioni del modello path-based:**

| Aspetto | Conseguenza |
|---------|-------------|
| **Hard link** | Due percorsi diversi per lo stesso inode → le regole per un percorso non si applicano all'altro |
| **Rename** | Un file rinominato può entrare/uscire dall'ambito di una regola |
| **Mount bind** | Un bind mount crea un nuovo percorso → potenziale bypass se non coperto dal profilo |
| **Semplicità** | Le regole sono leggibili e intuitive: il percorso nel profilo corrisponde al percorso nel filesystem |
| **Chroot** | AppArmor risolve i percorsi dal punto di vista del namespace mount del processo |

### Policy Cache e Parser

AppArmor compila i profili in una rappresentazione binaria tramite `apparmor_parser`. Il cache accelera il caricamento al boot.

```bash
# Il parser compila i profili testuali in binario
apparmor_parser -r /etc/apparmor.d/usr.sbin.nginx

# Il cache viene salvato in:
ls /etc/apparmor.d/cache.d/
# usr.sbin.nginx  usr.sbin.sshd  ...

# oppure (sistemi più vecchi):
ls /etc/apparmor.d/cache/

# Pulire il cache e ricompilare tutto
apparmor_parser --cache-clear
systemctl restart apparmor

# Precompilare tutti i profili per velocizzare il boot
apparmor_parser --write-cache /etc/apparmor.d/*

# Verifica che il modulo kernel sia caricato
cat /sys/module/apparmor/parameters/enabled
# Y

# Versione della policy supportata
cat /sys/kernel/security/apparmor/features/policy/versions/v8
# yes (o il numero della versione supportata)
```

### Stato e Gestione

```bash
# Stato AppArmor
aa-status
# oppure
apparmor_status

# Output esempio:
# apparmor module is loaded.
# 47 profiles are loaded.
# 47 profiles are in enforce mode.
#    /snap/core/...
#    /usr/sbin/ntpd
#    /usr/sbin/sshd
# 0 profiles are in complain mode.
# 12 processes have profiles defined.
# 12 processes are in enforce mode.

# Cambia modalità di un profilo
aa-enforce /etc/apparmor.d/usr.sbin.nginx    # enforce
aa-complain /etc/apparmor.d/usr.sbin.nginx   # complain (debug)
aa-disable /etc/apparmor.d/usr.sbin.nginx    # disabilita

# Ricarica un profilo dopo modifica
apparmor_parser -r /etc/apparmor.d/usr.sbin.nginx

# Ricarica tutti i profili
systemctl reload apparmor
```

### Struttura di un Profilo

```bash
# /etc/apparmor.d/usr.sbin.nginx

#include <tunables/global>

/usr/sbin/nginx {
    # Include regole comuni
    #include <abstractions/base>
    #include <abstractions/nameservice>

    # Capabilities richieste
    capability net_bind_service,
    capability setuid,
    capability setgid,
    capability dac_override,

    # Accesso rete
    network inet stream,
    network inet6 stream,

    # File di configurazione (lettura)
    /etc/nginx/** r,
    /etc/ssl/** r,

    # Log (lettura/scrittura)
    /var/log/nginx/** rw,

    # Contenuti web (lettura)
    /var/www/** r,
    /srv/www/** r,

    # PID e socket
    /run/nginx.pid rw,
    /run/nginx/ r,

    # Tmp
    /tmp/** rw,

    # Binario (esecuzione)
    /usr/sbin/nginx mr,

    # Librerie condivise
    /usr/lib/** mr,
    /lib/** mr,

    # Profili per processi figli (worker)
    /usr/sbin/nginx ix,

    # Deny espliciti (defense in depth)
    deny /etc/shadow r,
    deny /etc/passwd w,
    deny /root/** rwx,
}
```

### Permessi nei Profili

| Permesso | Significato |
|----------|-------------|
| `r` | Read |
| `w` | Write |
| `a` | Append |
| `l` | Link |
| `k` | Lock |
| `m` | Memory map executable |
| `x` | Execute (con qualificatori) |
| `ix` | Execute — eredita il profilo del padre |
| `px` | Execute — usa il profilo dell'eseguibile |
| `Px` | Execute — profilo richiesto, fallisci se non esiste |
| `ux` | Execute — unconfined (nessun profilo) |
| `cx` | Execute — usa un profilo figlio definito localmente |

---

## AppArmor: Creazione e Gestione Profili

### Creazione Manuale

```bash
# Profilo per un'applicazione custom
cat > /etc/apparmor.d/opt.myapp.server <<'EOF'
#include <tunables/global>

/opt/myapp/server {
    #include <abstractions/base>
    #include <abstractions/nameservice>

    # Rete
    network inet stream,
    network inet6 stream,

    # Configurazione
    /opt/myapp/config/** r,
    /opt/myapp/config/ r,

    # Dati
    /opt/myapp/data/** rw,
    /opt/myapp/data/ r,

    # Log
    /var/log/myapp/** w,
    /var/log/myapp/ r,

    # PID
    /run/myapp.pid rw,

    # Binario e librerie
    /opt/myapp/server mr,
    /opt/myapp/lib/** mr,

    # Accesso sistema
    /proc/sys/net/** r,
    /sys/kernel/mm/transparent_hugepage/enabled r,

    # Temp
    owner /tmp/myapp-* rw,

    # Deny espliciti
    deny /etc/shadow r,
    deny /home/** rwx,
}
EOF

# Carica il profilo
apparmor_parser -r /etc/apparmor.d/opt.myapp.server

# Verifica
aa-status | grep myapp
```

### Abstractions

Le abstractions sono file di regole condivise incluse da più profili:

```bash
# Abstractions più comuni:
# /etc/apparmor.d/abstractions/base           — accesso base al sistema
# /etc/apparmor.d/abstractions/nameservice    — DNS, NSS, /etc/hosts
# /etc/apparmor.d/abstractions/openssl        — librerie SSL
# /etc/apparmor.d/abstractions/python         — runtime Python
# /etc/apparmor.d/abstractions/php            — runtime PHP

# Esempio di abstraction custom
cat > /etc/apparmor.d/abstractions/myapp-common <<'EOF'
    /opt/myapp/shared/** r,
    /var/log/myapp/** w,
    network inet stream,
EOF

# Uso in un profilo:
# /opt/myapp/worker {
#     #include <abstractions/myapp-common>
#     ...
# }
```

### Sintassi Avanzata dei Profili

#### Regole D-Bus

AppArmor può mediare l'accesso al bus di sistema D-Bus:

```bash
/usr/bin/myservice {
    # ...

    # Permetti di inviare segnali su D-Bus
    dbus send
        bus=system
        path=/org/freedesktop/NetworkManager
        interface=org.freedesktop.NetworkManager
        member=GetDevices
        peer=(name=org.freedesktop.NetworkManager, label=/usr/sbin/NetworkManager),

    # Permetti di possedere un nome sul bus
    dbus bind
        bus=system
        name=com.example.MyService,

    # Ricevi qualsiasi messaggio indirizzato a noi
    dbus receive
        bus=system
        path=/com/example/MyService/**,

    # Deny esplicito: nessun accesso al session bus
    deny dbus bus=session,
}
```

#### Regole Mount

```bash
/usr/bin/mycontainer {
    # ...

    # Permetti mount di tmpfs
    mount fstype=tmpfs options=(rw, nosuid, nodev) -> /tmp/,

    # Permetti bind mount
    mount options=(rw, bind) /data/ -> /container/data/,

    # Permetti umount
    umount /tmp/,

    # Permetti pivot_root (usato dai container runtime)
    pivot_root /newroot/ -> /oldroot/,

    # Deny mount di filesystem pericolosi
    deny mount fstype=debugfs,
    deny mount fstype=tracefs,
}
```

#### Regole Signal

```bash
/usr/sbin/myservice {
    # ...

    # Permetti di inviare SIGTERM ai propri figli
    signal send set=(term, kill) peer=/usr/sbin/myservice//worker,

    # Permetti di ricevere segnali da init/systemd
    signal receive set=(term, kill, hup) peer=unconfined,

    # Deny: non può inviare segnali ad altri servizi
    deny signal send peer=/usr/sbin/sshd,
}
```

#### Regole ptrace

```bash
/usr/bin/debugger {
    # Permetti ptrace solo sui propri processi
    ptrace read peer=@{profile_name},
    ptrace trace peer=@{profile_name},

    # Deny ptrace su altri profili
    deny ptrace peer=/**,
}
```

#### Regole Unix Socket

```bash
/usr/sbin/myservice {
    # Socket Unix named
    unix (create, listen, accept, connect, send, receive)
        type=stream
        addr=@/run/myservice.sock,

    # Socket Unix anonimo
    unix (create, send, receive) type=dgram,

    # Permetti connessione a socket di un altro profilo
    unix (connect, send, receive)
        type=stream
        peer=(label=/usr/sbin/other_service),
}
```

#### Profili Figli (Child Profiles / Hats)

```bash
/usr/sbin/apache2 {
    # ...

    # Profilo figlio per mod_php
    ^phphandler {
        #include <abstractions/php>
        /var/www/html/** r,
        /tmp/php* rw,
        deny /etc/shadow r,
        deny network,
    }

    # Il processo cambia hat con aa_change_hat()
    # Apache usa change_hat per isolare i moduli
}
```

#### Variabili e Tunables

```bash
# In /etc/apparmor.d/tunables/global:
@{HOME}=/home/*/ /root/
@{PROC}=/proc/
@{HOMEDIRS}=/home/
@{multiarch}=*-linux-gnu*

# Uso nei profili:
/usr/bin/myapp {
    owner @{HOME}/.config/myapp/** rw,
    @{PROC}/sys/net/core/somaxconn r,
    /usr/lib/@{multiarch}/libssl.so* mr,
}

# Definire variabili custom in /etc/apparmor.d/tunables/
# /etc/apparmor.d/tunables/myapp
@{MYAPP_DATA}=/opt/myapp/data /srv/myapp/data
# Poi nel profilo:
# #include <tunables/myapp>
# @{MYAPP_DATA}/** rw,
```

---

## AppArmor: aa-genprof e aa-logprof

### aa-genprof: Generazione Profili Semi-Automatica

`aa-genprof` è lo strumento interattivo per creare profili osservando il comportamento di un'applicazione:

```bash
# Step 1: Avvia la generazione
aa-genprof /opt/myapp/server

# L'output mostra:
# Setting /opt/myapp/server to complain mode.
# Please start the application to be profiled in another window and
# exercise its functionality now.
#
# Once completed, select the "Scan" option below for AppArmor to
# review the log entries.
#
# Profiling: /opt/myapp/server
#
# [(S)can system log for AppArmor events] / (F)inish

# Step 2: In un altro terminale, avvia e usa l'applicazione
# Esegui TUTTE le operazioni che l'app deve poter fare

# Step 3: Torna al terminale di aa-genprof e premi S (Scan)
# L'analisi mostra ogni accesso e chiede cosa fare:

# Profile:  /opt/myapp/server
# Path:     /etc/ssl/certs/ca-certificates.crt
# Mode:     r
#
# (A)llow / [(D)eny] / (I)gnore / (G)lob / Glob with (E)xtension /
# (N)ew / Dup / A(u)dit / (O)wner permissions off / Audi(t) - Loss /
# p(I)x / (U)nconfined / (C)hild / Deny (M)ap / Abo(r)t / (F)inish

# A = Permetti questo accesso
# D = Nega questo accesso
# G = Usa glob pattern (es: /etc/ssl/** r)
# I = Ignora per ora
# F = Finisci e salva

# Step 4: premi F per salvare
# Il profilo viene salvato in /etc/apparmor.d/ e messo in enforce
```

### aa-logprof: Aggiornamento Profili

Dopo che un profilo è attivo, `aa-logprof` analizza i nuovi denial per aggiornare il profilo:

```bash
# Analizza i log e proponi aggiornamenti
aa-logprof

# Mostra i denial non gestiti dal profilo attuale
# e chiede come gestirli (Allow/Deny/Glob...)

# Utile dopo:
# - Aggiornamento dell'applicazione
# - Nuove funzionalità
# - Cambio configurazione
```

### Workflow Pratico

```bash
# 1. Crea profilo in complain mode
aa-genprof /usr/sbin/myservice

# 2. Esercita tutte le funzionalità (in un altro terminale)
systemctl start myservice
# ... usa tutte le feature ...

# 3. Scan e configura le regole
# (nel terminale di aa-genprof)

# 4. Metti in enforce
aa-enforce /etc/apparmor.d/usr.sbin.myservice

# 5. Monitora per denial
journalctl -k | grep apparmor | grep DENIED

# 6. Se necessario, aggiorna il profilo
aa-logprof
# oppure
aa-complain /etc/apparmor.d/usr.sbin.myservice  # torna in complain
# ... riproduci il problema ...
aa-logprof
aa-enforce /etc/apparmor.d/usr.sbin.myservice
```

---

## AppArmor e Container

### Docker e AppArmor

Docker applica automaticamente un profilo AppArmor default (`docker-default`) a ogni container. Questo profilo limita le operazioni pericolose mantenendo la compatibilità con la maggior parte dei workload.

```bash
# Verifica il profilo default
docker inspect --format '{{.AppArmorProfile}}' <container_id>
# docker-default

# Il profilo docker-default si trova tipicamente a:
# /etc/apparmor.d/docker  (generato da Docker)

# Capacità bloccate dal profilo docker-default:
# - mount (no montaggio filesystem)
# - ptrace su altri container
# - Accesso a /proc/sysrq-trigger, /proc/kcore
# - Accesso a /sys/firmware/**
# - Caricamento moduli kernel

# Esegui un container con profilo custom
docker run --security-opt apparmor=my_custom_profile myimage

# Esegui un container SENZA AppArmor (sconsigliato in produzione)
docker run --security-opt apparmor=unconfined myimage
```

#### Creare un Profilo Custom per Docker

```bash
# /etc/apparmor.d/docker-myapp

#include <tunables/global>

profile docker-myapp flags=(attach_disconnected, mediate_deleted) {
    #include <abstractions/base>

    # Rete
    network inet stream,
    network inet6 stream,
    network inet dgram,    # DNS UDP

    # File nel container (overlay filesystem)
    # Il flag attach_disconnected è necessario per overlay2
    /** r,
    /app/** rw,
    /tmp/** rw,

    # Nega accesso a percorsi sensibili dell'host
    deny /proc/sysrq-trigger w,
    deny /proc/kcore r,
    deny /sys/firmware/** r,
    deny /sys/kernel/security/** r,

    # Capabilities
    capability net_bind_service,
    capability setuid,
    capability setgid,
    capability chown,
    capability dac_override,

    # Nega capabilities pericolose
    deny capability sys_admin,
    deny capability sys_rawio,
    deny capability sys_module,

    # Nega mount
    deny mount,

    # Nega ptrace su altri profili
    deny ptrace read peer=/**,
}

# Carica
apparmor_parser -r /etc/apparmor.d/docker-myapp

# Usa
docker run --security-opt apparmor=docker-myapp myimage
```

### LXC/LXD e AppArmor

LXC utilizza AppArmor in modo più esteso di Docker, con profili dedicati per ogni container:

```bash
# Profili LXD generati automaticamente
ls /etc/apparmor.d/lxd/
# lxd-<container_name>_<profile>

# Profilo default LXD include:
# - Accesso filesystem confinato dentro il rootfs del container
# - mount limitato (tmpfs, proc, sysfs — no altri filesystem)
# - ptrace solo sui propri processi
# - signal solo ai propri processi
# - Deny su /proc/kcore, /proc/sysrq-trigger

# AppArmor nesting: container che eseguono AppArmor internamente
# LXD supporta il nesting se abilitato:
lxc config set mycontainer security.nesting true
# Questo permette al container di caricare propri profili AppArmor

# Verifica profilo di un container LXD
lxc config get mycontainer raw.apparmor
```

> **Fonte:** Ubuntu Server Documentation, "LXD — Security", ubuntu.com/server/docs — consultato 2026-05-23.

---

## AppArmor: Debugging Avanzato

### aa-notify

`aa-notify` fornisce notifiche in tempo reale per i denial AppArmor:

```bash
# Installazione
apt install apparmor-notify

# Notifiche desktop in tempo reale
aa-notify -p -f /var/log/syslog &

# Mostra le ultime N notifiche
aa-notify -s 1 -v    # ultimo 1 giorno, verbose

# Mostra notifiche per un profilo specifico
aa-notify -s 1 -v --filter /usr/sbin/nginx

# Configura notifiche per utente (in ~/.apparmor/notify.cfg)
# [DEFAULT]
# show_notifications = yes
# show_severity = true
# severity_min = 5
```

### Analisi dei Log

```bash
# I denial AppArmor appaiono in diversi log a seconda della configurazione

# Kernel ring buffer (sempre disponibile)
dmesg | grep -i apparmor
# [  123.456] audit: type=1400 audit(1716500000.123:456):
#   apparmor="DENIED" operation="open" profile="/usr/sbin/nginx"
#   name="/etc/secret.conf" pid=1234 comm="nginx"
#   requested_mask="r" denied_mask="r" fsuid=0 ouid=0

# Syslog (Ubuntu/Debian)
grep "apparmor" /var/log/syslog | grep DENIED

# Journal
journalctl -k --grep="apparmor.*DENIED" --since "1 hour ago"

# Audit log (se auditd è installato)
ausearch -m apparmor --start recent

# Formato del messaggio denial:
# apparmor="DENIED"           — azione bloccata
# apparmor="ALLOWED"          — azione permessa (in complain mode)
# apparmor="AUDIT"            — azione auditata (regola audit)
# operation="open"            — operazione tentata
# profile="/usr/sbin/nginx"   — profilo che ha bloccato
# name="/etc/secret.conf"     — risorsa richiesta
# requested_mask="r"          — permesso richiesto
# denied_mask="r"             — permesso negato
```

### Debugging Strutturato

```bash
# 1. Verifica stato di tutti i profili
aa-status

# 2. Metti il profilo problematico in complain
aa-complain /etc/apparmor.d/usr.sbin.myservice

# 3. Riproduci il problema
systemctl restart myservice
# ... esercita la funzionalità che fallisce ...

# 4. Analizza TUTTI i denial (in complain mode non blocca, solo logga)
journalctl -k --grep="apparmor.*ALLOWED.*myservice" --since "5 min ago"

# 5. Per ogni denial, decidi se:
#    a) Aggiungere una regola al profilo
#    b) Usare un glob pattern
#    c) Includere un'abstraction
#    d) Lasciare il deny (se l'accesso non è necessario)

# 6. Usa aa-logprof per automatizzare l'analisi
aa-logprof

# 7. Rimetti in enforce
aa-enforce /etc/apparmor.d/usr.sbin.myservice

# 8. Verifica
systemctl restart myservice
# ... test funzionalità ...
journalctl -k --grep="apparmor.*DENIED.*myservice" --since "1 min ago"
```

---

## Confronto SELinux vs AppArmor

| Caratteristica | SELinux | AppArmor |
|---------------|---------|----------|
| **Modello** | Label-based (etichette) | Path-based (percorsi) |
| **Granularità** | Molto alta (ogni oggetto etichettato) | Alta (basata su percorsi filesystem) |
| **Complessità** | Alta | Moderata |
| **Curva di apprendimento** | Ripida | Più accessibile |
| **Default in** | RHEL, Fedora, CentOS, Rocky | Ubuntu, Debian, SUSE |
| **Copertura** | File, porte, processi, socket, IPC | File, rete, capabilities, mount |
| **Hard link** | Sicuro (label sul inode) | Potenziale bypass (path != inode) |
| **Performance** | Overhead minimo | Overhead minimo |
| **MLS/MCS** | Supporto completo | Non supportato |
| **Container** | Profondo (label per container) | Buono (profili per container) |
| **Tooling** | semanage, audit2allow, sestatus | aa-genprof, aa-logprof, aa-status |
| **Documentazione** | Estesa ma complessa | Chiara e accessibile |

### Quando Usare Quale

**Scegli SELinux quando:**
- Usi RHEL/CentOS/Fedora (è il default, non cambiare)
- Hai bisogno di MLS (Multi-Level Security) per classificazione dati
- Lavori con container (Podman/Docker con policy SELinux)
- L'ambiente richiede certificazioni di sicurezza (Common Criteria)
- Hai bisogno di protezione contro hard link exploit

**Scegli AppArmor quando:**
- Usi Ubuntu/Debian/SUSE (è il default, non cambiare)
- Vuoi creare profili rapidamente per applicazioni custom
- Il team ha meno esperienza con MAC
- L'applicazione ha percorsi filesystem prevedibili
- Preferisci un approccio incrementale (prima complain, poi enforce)

**Regola d'oro:** Usa il MAC che la tua distribuzione fornisce come default. Non ha senso installare SELinux su Ubuntu o AppArmor su RHEL — la distribuzione ha integrato e testato il proprio MAC in ogni aspetto del sistema.

---

## Confronto Esteso: SELinux vs AppArmor vs TOMOYO vs Smack

Oltre a SELinux e AppArmor, il kernel Linux supporta altri due LSM maggiori meno diffusi ma rilevanti in contesti specifici.

### TOMOYO Linux

TOMOYO (originariamente sviluppato da NTT Data, Giappone) usa un modello path-based come AppArmor ma con un approccio diverso: la policy viene appresa dal comportamento reale del sistema.

- **Approccio:** "learning mode" — il sistema osserva tutte le operazioni e genera automaticamente la policy
- **Punto di forza:** Analisi dei percorsi di esecuzione (execution history), include il call chain completo
- **Distribuzione default:** Nessuna major; disponibile come modulo kernel su tutte
- **Manutenzione:** Attiva ma con community ridotta

### Smack (Simplified Mandatory Access Control Kernel)

Smack è un MAC minimalista label-based, molto più semplice di SELinux. Progettato per sistemi embedded e IoT.

- **Approccio:** Label semplici (stringhe) su soggetti e oggetti, regole allow esplicite
- **Punto di forza:** Estrema semplicità, ideale per dispositivi embedded
- **Distribuzione default:** Tizen (Samsung), alcuni sistemi automotive (AGL — Automotive Grade Linux)
- **Manutenzione:** Attiva, usato in produzione nell'automotive e IoT

### Matrice Comparativa Completa

| Caratteristica | SELinux | AppArmor | TOMOYO | Smack |
|---------------|---------|----------|--------|-------|
| **Modello** | Label (inode) | Path | Path + execution history | Label (semplice) |
| **Complessità** | Alta | Moderata | Moderata | Bassa |
| **Granularità** | Molto alta | Alta | Alta | Moderata |
| **MLS/MCS** | Completo | No | No | Parziale |
| **Container** | Eccellente | Buono | Limitato | Limitato |
| **Learning mode** | No (ma audit2allow) | Complain | Sì (nativo) | No |
| **Policy language** | m4 macro + CIL | Testo profili | Testo semplice | Testo regole |
| **Hard link safety** | Sì (inode) | No (path) | No (path) | Sì (label) |
| **Network label** | Sì (netlabel, CIPSO) | No | No | Sì (netlabel) |
| **D-Bus mediation** | Sì | Sì | No | No |
| **Stacking** | Major (esclusivo) | Major (esclusivo) | Major (esclusivo) | Major (esclusivo) |
| **Distro default** | RHEL, Fedora, Rocky | Ubuntu, Debian, SUSE | Nessuna major | Tizen, AGL |
| **Certificazioni** | Common Criteria EAL4+ | No | No | No |
| **Tooling** | Ricco (semanage, sesearch, sealert) | Buono (aa-*, apparmor_parser) | Minimo (tomoyo-*) | Minimo (smackctl) |
| **Documentazione** | Estesa | Buona | Discreta | Minima |
| **Overhead kernel** | ~2-5% syscall | ~1-3% syscall | ~1-3% syscall | ~1% syscall |
| **Community** | Molto ampia | Ampia | Ridotta | Ridotta |

### Landlock — il Newcomer

A partire dal kernel 5.13, Landlock è un LSM minore non privilegiato che permette ai processi di auto-confinarsi senza bisogno di privilegi root. Non è un'alternativa a SELinux/AppArmor ma un complemento.

```bash
# Landlock è un minor LSM, può essere impilato con SELinux o AppArmor
cat /sys/kernel/security/lsm
# landlock,lockdown,yama,integrity,apparmor

# Un processo può auto-confinarsi:
# (pseudo-codice C)
# struct landlock_ruleset_attr attr = { .handled_access_fs = ... };
# int fd = landlock_create_ruleset(&attr, sizeof(attr), 0);
# landlock_add_rule(fd, LANDLOCK_RULE_PATH_BENEATH, &rule, 0);
# landlock_restrict_self(fd, 0);

# Verifica supporto Landlock
cat /sys/kernel/security/landlock/abi_version
# 4  (kernel 6.x)
```

> **Fonte:** kernel.org, Documentation/userspace-api/landlock.rst — consultato 2026-05-23.

---

## Audit e Rollback Playbook

### Cambio Modalità in Sicurezza

#### SELinux: da permissive a enforcing

```bash
# 1. PRIMA: audit completo dei denial accumulati
ausearch -m avc --start boot | audit2why | tee /root/selinux-audit-pre-enforce.log

# 2. Categorizza i denial:
#    - Contesto sbagliato → restorecon
#    - Boolean mancante → setsebool -P
#    - Porta non standard → semanage port
#    - Accesso legittimo senza regola → modulo custom
#    - Accesso non legittimo → lasciar bloccato (desiderato)

# 3. Risolvi tutti i denial legittimi PRIMA di passare a enforcing

# 4. Passa a enforcing
setenforce 1    # temporaneo per test
# Se tutto funziona:
sed -i 's/^SELINUX=permissive/SELINUX=enforcing/' /etc/selinux/config

# 5. Monitora per 48h
watch -n 60 'ausearch -m avc --start recent 2>/dev/null | wc -l'
```

#### AppArmor: da complain a enforce (batch)

```bash
# 1. Lista profili in complain
aa-status | grep complain

# 2. Per ogni profilo, verifica i denial loggati
for profile in $(aa-status --complaining); do
    echo "=== $profile ==="
    journalctl -k --grep="apparmor.*ALLOWED.*${profile##*/}" --since "7 days ago" | wc -l
done

# 3. Risolvi i denial con aa-logprof
aa-logprof

# 4. Passa a enforce uno alla volta, partendo dai meno critici
aa-enforce /etc/apparmor.d/usr.sbin.myservice

# 5. Monitora
journalctl -k --grep="apparmor.*DENIED" -f
```

### Backup e Restore delle Policy

#### SELinux

```bash
# Backup completo della configurazione SELinux
mkdir -p /root/selinux-backup-$(date +%Y%m%d)
BKDIR="/root/selinux-backup-$(date +%Y%m%d)"

# 1. Policy store
cp -a /var/lib/selinux/ "$BKDIR/var-lib-selinux/"

# 2. Configurazione
cp /etc/selinux/config "$BKDIR/config"

# 3. Customizzazioni (file context, port, boolean, login, user)
semanage export > "$BKDIR/semanage-export.conf"

# 4. Lista moduli custom
semodule -l | grep -v '^[a-z]' > "$BKDIR/custom-modules.list"

# 5. Boolean non-default
semanage boolean -l -C > "$BKDIR/custom-booleans.list"

# RESTORE:
# 1. Ripristina customizzazioni
semanage import < "$BKDIR/semanage-export.conf"

# 2. Reinstalla moduli custom
for pp in "$BKDIR"/modules/*.pp; do
    semodule -i "$pp"
done

# 3. Relabel
restorecon -Rv /
```

#### AppArmor

```bash
# Backup
BKDIR="/root/apparmor-backup-$(date +%Y%m%d)"
mkdir -p "$BKDIR"

# 1. Tutti i profili
cp -a /etc/apparmor.d/ "$BKDIR/apparmor.d/"

# 2. Tunables
cp -a /etc/apparmor.d/tunables/ "$BKDIR/tunables/"

# 3. Lista profili e stato
aa-status > "$BKDIR/aa-status.txt"

# RESTORE:
cp -a "$BKDIR/apparmor.d/"* /etc/apparmor.d/
systemctl restart apparmor
```

### Test in Permissive Prima di Enforcing

```bash
# Procedura per SELinux: testare un nuovo modulo
# 1. Metti il SINGOLO dominio in permissive (non l'intero sistema)
semanage permissive -a httpd_t
# Ora solo httpd_t è permissive, il resto del sistema è enforcing

# 2. Testa
systemctl restart httpd
# ... verifica tutte le funzionalità ...

# 3. Verifica che non ci siano denial
ausearch -m avc -ts recent | grep httpd_t

# 4. Rimuovi il dominio permissive
semanage permissive -d httpd_t

# 5. Lista domini attualmente in permissive
semanage permissive -l
```

---

## seccomp: Filtraggio Syscall

seccomp (Secure Computing Mode) limita le syscall che un processo può effettuare. Non è un LSM ma un complemento a SELinux/AppArmor che opera a livello di syscall anziché a livello di risorse.

### Architettura

```
┌──────────────────────────────────────────────┐
│                Processo                       │
│                                               │
│  Chiamata: write(fd, buf, len)                │
│      │                                        │
│      ▼                                        │
│  ┌────────────────────────┐                   │
│  │ seccomp-BPF filter     │                   │
│  │                        │                   │
│  │ write() → ALLOW        │                   │
│  │ read()  → ALLOW        │                   │
│  │ open()  → ALLOW        │                   │
│  │ mount() → KILL_PROCESS │                   │
│  │ ptrace()→ ERRNO(EPERM) │                   │
│  │ *       → LOG          │                   │
│  └────────────────────────┘                   │
│      │                                        │
│      ▼                                        │
│  Kernel esegue la syscall (se ALLOW)          │
└──────────────────────────────────────────────┘
```

Azioni possibili per ogni syscall:

| Azione | Comportamento |
|--------|---------------|
| `SCMP_ACT_ALLOW` | Permetti la syscall |
| `SCMP_ACT_KILL_PROCESS` | Termina il processo con SIGSYS |
| `SCMP_ACT_KILL_THREAD` | Termina il thread |
| `SCMP_ACT_TRAP` | Invia SIGSYS, il processo può gestirlo |
| `SCMP_ACT_ERRNO(errno)` | Ritorna un errore specifico |
| `SCMP_ACT_LOG` | Permetti ma logga |
| `SCMP_ACT_NOTIFY` | Invia al supervisore userspace (notify fd, kernel 5.0+) |

### seccomp per systemd

systemd supporta nativamente seccomp per i servizi:

```ini
# /etc/systemd/system/myservice.service.d/seccomp.conf
[Service]
# Allowlist: permetti solo queste syscall
SystemCallFilter=@basic-io @file-system @io-event @network-io @process @signal @timer
SystemCallFilter=~@mount @reboot @swap @raw-io @module @debug

# Architetture syscall permesse (blocca x86 su sistema x86_64)
SystemCallArchitectures=native

# Azione al deny
SystemCallErrorNumber=EPERM

# Gruppo di syscall predefiniti da systemd:
# @basic-io       — read, write, close, lseek, ...
# @file-system    — open, stat, chmod, mkdir, ...
# @io-event       — epoll, poll, select, ...
# @network-io     — socket, connect, bind, listen, ...
# @process        — fork, execve, wait, exit, ...
# @signal         — sigaction, kill, sigprocmask, ...
# @timer          — clock_gettime, nanosleep, ...
# @mount          — mount, umount, ...
# @privileged     — syscall che richiedono capabilities
# @raw-io         — ioperm, iopl, ...
```

### Generazione Profilo seccomp con strace

```bash
# 1. Traccia tutte le syscall usate dall'applicazione
strace -f -o /tmp/myapp.strace -e trace=all /opt/myapp/server &
# Esercita TUTTE le funzionalità dell'applicazione
# ...
kill %1

# 2. Estrai le syscall uniche
grep -oP '^\d+ +\K\w+(?=\()' /tmp/myapp.strace | sort -u > /tmp/myapp-syscalls.txt

# 3. Confronta con il profilo default OCI
# Le syscall nel profilo ma non nella lista → candidati per la rimozione
# Le syscall nella lista ma non nel profilo → devono essere aggiunte

# 4. Genera il profilo JSON OCI
cat > /tmp/myapp-seccomp.json << 'SECCOMP'
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "defaultErrnoRet": 1,
    "archMap": [
        {
            "architecture": "SCMP_ARCH_X86_64",
            "subArchitectures": ["SCMP_ARCH_X86", "SCMP_ARCH_X32"]
        }
    ],
    "syscalls": [
        {
            "names": [
                "accept4", "bind", "clone", "close", "connect",
                "dup2", "epoll_create1", "epoll_ctl", "epoll_wait",
                "execve", "exit_group", "fchmod", "fcntl", "fstat",
                "futex", "getpid", "getsockopt", "ioctl", "listen",
                "lseek", "mmap", "mprotect", "munmap", "nanosleep",
                "newfstatat", "open", "openat", "pipe2", "poll",
                "read", "recvfrom", "rt_sigaction", "rt_sigprocmask",
                "sendto", "setsockopt", "socket", "stat", "write"
            ],
            "action": "SCMP_ACT_ALLOW"
        }
    ]
}
SECCOMP
```

### Profilo seccomp Default OCI

Docker e Podman applicano un profilo seccomp default che blocca circa 44 syscall potenzialmente pericolose su ~330+ totali:

```bash
# Syscall bloccate dal profilo OCI default (selezione):
# - mount, umount2          — montaggio filesystem
# - reboot                  — riavvio sistema
# - swapon, swapoff         — gestione swap
# - init_module, delete_module — moduli kernel
# - settimeofday            — cambio clock
# - sethostname             — cambio hostname
# - keyctl                  — gestione chiavi kernel
# - add_key, request_key    — keyring
# - ptrace                  — debug (se non CAP_SYS_PTRACE)
# - personality             — cambio ABI
# - userfaultfd             — gestione page fault userspace

# Uso con Docker
docker run --security-opt seccomp=/path/to/custom.json myimage

# Disabilita seccomp (sconsigliato in produzione)
docker run --security-opt seccomp=unconfined myimage

# Uso con Podman
podman run --security-opt seccomp=/path/to/custom.json myimage

# Verifica profilo attivo
docker inspect --format '{{.HostConfig.SecurityOpt}}' <container>
```

### seccomp + SELinux/AppArmor: Difesa in Profondità

```
┌───────────────────────────────────────────────────────┐
│                  Richiesta: mount("/dev/sda1", "/mnt") │
│                                                        │
│  Layer 1: seccomp                                      │
│    → mount() è nella blocklist → KILL_PROCESS          │
│    (la richiesta non arriva nemmeno al kernel)          │
│                                                        │
│  Layer 2: SELinux/AppArmor (se seccomp avesse permesso)│
│    → Il tipo/profilo non permette mount → DENY + log   │
│                                                        │
│  Layer 3: DAC                                          │
│    → L'utente non ha CAP_SYS_ADMIN → EPERM             │
│                                                        │
│  Layer 4: Capabilities (se fosse root)                 │
│    → CAP_SYS_ADMIN non nel bounding set → EPERM        │
└───────────────────────────────────────────────────────┘
```

> **Fonte:** man seccomp(2), man seccomp_rule_add(3); OCI Runtime Specification, github.com/opencontainers/runtime-spec — consultato 2026-05-23.

---

## Integrazione con lynis, aide, osquery

### lynis — Audit di Sicurezza

lynis è uno strumento di auditing che verifica la configurazione MAC del sistema e segnala problemi.

```bash
# Installazione
# RHEL/Fedora:
dnf install lynis
# Ubuntu/Debian:
apt install lynis

# Esegui audit completo
lynis audit system

# Sezione MAC dell'output:
# [+] Security frameworks
# ------------------------------------
#   - Checking presence AppArmor             [ FOUND ]
#   - Checking AppArmor status               [ ENABLED ]
#   - Checking AppArmor profiles             [ 47 enforce, 0 complain, 0 kill ]
#
# oppure (RHEL):
#   - Checking presence SELinux              [ FOUND ]
#   - Checking SELinux status                [ ENABLED ]
#   - Checking SELinux mode                  [ ENFORCING ]

# Suggerimenti tipici di lynis per MAC:
# MACF-6208: No AppArmor profiles are in complain mode [OK]
# MACF-6234: Profiles loaded but not all processes are confined [WARNING]
# → Controlla quali servizi non hanno profilo AppArmor

# Filtra solo i risultati MAC
lynis audit system --tests-from-group "mac_frameworks"

# Report in formato macchina
lynis audit system --report-file /tmp/lynis-report.dat
grep "mac_framework" /tmp/lynis-report.dat

# Controllo periodico via cron
# /etc/cron.daily/lynis-audit:
#!/bin/bash
lynis audit system --cronjob --quiet \
    --report-file /var/log/lynis-report-$(date +\%Y\%m\%d).dat
```

### aide — File Integrity Monitoring

aide (Advanced Intrusion Detection Environment) monitora le modifiche ai file di configurazione MAC, rilevando alterazioni non autorizzate.

```bash
# Installazione
# RHEL: dnf install aide
# Ubuntu: apt install aide

# Configurazione per monitorare i file MAC
# /etc/aide/aide.conf (o /etc/aide.conf)

# Regole custom per SELinux
/etc/selinux/config CONTENT_EX
/etc/selinux/targeted/policy/ CONTENT_EX
/var/lib/selinux/ DATAONLY

# Regole custom per AppArmor
/etc/apparmor.d/ CONTENT_EX
/etc/apparmor.d/tunables/ CONTENT_EX
/etc/apparmor.d/abstractions/ CONTENT_EX
/etc/apparmor/parser.conf CONTENT_EX

# Inizializza il database
aide --init
mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Verifica integrità
aide --check

# Output in caso di modifica:
# File: /etc/apparmor.d/usr.sbin.nginx
#  SHA256   : old_hash != new_hash
#  Size     : 1234 != 1567
#  Mtime    : 2026-05-20 != 2026-05-23
#
# → Qualcuno ha modificato il profilo AppArmor di nginx!

# Aggiorna il database dopo modifiche legittime
aide --update
mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
```

### osquery — Query SQL sui Sistemi

osquery permette di interrogare lo stato MAC del sistema usando query SQL.

```bash
# Installazione: vedi osquery.io per il repository

# Query SELinux
osqueryi "SELECT * FROM selinux_settings;"
# key                    | value
# enforcing              | 1
# policyvers             | 33
# type                   | targeted

# Processi e contesti SELinux
osqueryi "SELECT pid, name, label FROM processes WHERE label != 'unconfined';"

# Verifica boolean non-default
osqueryi "
    SELECT name, value, description
    FROM selinux_settings
    WHERE name LIKE '%boolean%';
"

# Query AppArmor
osqueryi "SELECT * FROM apparmor_profiles;"
# name                        | mode       | attach
# /usr/sbin/nginx             | enforce    |
# /usr/sbin/sshd              | enforce    |

# Processi confinati da AppArmor
osqueryi "
    SELECT p.pid, p.name, p.cmdline, aa.mode
    FROM processes p
    JOIN apparmor_profiles aa ON p.name = aa.name
    WHERE aa.mode = 'enforce';
"

# Query pianificate per monitoraggio continuo
# In /etc/osquery/osquery.conf:
{
    "schedule": {
        "mac_check": {
            "query": "SELECT * FROM apparmor_profiles WHERE mode != 'enforce';",
            "interval": 3600,
            "description": "Profili AppArmor non in enforce"
        },
        "selinux_mode": {
            "query": "SELECT * FROM selinux_settings WHERE key='enforcing' AND value='0';",
            "interval": 300,
            "description": "SELinux non in enforcing"
        }
    }
}
```

### Integrazione CI/CD — Verifica MAC in Pipeline

```bash
# In una pipeline CI/CD (GitLab CI, GitHub Actions, Jenkins), e` fondamentale
# verificare che le policy MAC siano corrette PRIMA del deploy in produzione.

# Esempio: stage di verifica in GitLab CI
# .gitlab-ci.yml (estratto):
# mac_verification:
#   stage: security
#   script:
#     # Verifica che il profilo AppArmor compili senza errori
#     - apparmor_parser -p /etc/apparmor.d/usr.sbin.nginx
#     # Verifica che la policy SELinux custom compili
#     - checkmodule -M -m -o mymodule.mod mymodule.te
#     - semodule_package -o mymodule.pp -m mymodule.mod
#     # Dry-run del playbook Ansible di hardening
#     - ansible-playbook selinux-hardening.yml --check --diff
#   allow_failure: false
#   rules:
#     - changes:
#       - "security/apparmor/**"
#       - "security/selinux/**"

# Script standalone per pre-deploy check:
#!/bin/bash
set -euo pipefail

echo "=== Verifica profili AppArmor ==="
for profile in /etc/apparmor.d/local/*; do
    if apparmor_parser -p "$profile" 2>/dev/null; then
        echo "[OK] $profile"
    else
        echo "[FAIL] $profile — errore di compilazione"
        exit 1
    fi
done

echo "=== Verifica policy SELinux ==="
# Assicurarsi che non ci siano moduli in conflitto
semodule -l | sort > /tmp/selinux_modules_pre.txt
echo "Moduli SELinux attivi: $(wc -l < /tmp/selinux_modules_pre.txt)"

echo "=== Verifica contesti file ==="
# Cercare file con contesti errati (restorecon in dry-run)
restorecon -Rvn /var/www /var/log /etc 2>&1 | head -50
echo "=== Verifica completata ==="
```

---

## eBPF LSM e Runtime Security

### eBPF come Livello di Sicurezza

```
eBPF (extended Berkeley Packet Filter) e` diventato un meccanismo di sicurezza
runtime di prima classe a partire dal kernel 5.7+ con i BPF LSM hooks.
A differenza di SELinux e AppArmor, che lavorano con policy statiche, eBPF
permette di scrivere programmi di enforcement caricati dinamicamente nel kernel
senza modificare moduli o riavviare il sistema.

Architettura eBPF LSM:
                    ┌─────────────────────────┐
                    │    Spazio Utente         │
                    │  ┌─────────────────────┐ │
                    │  │ Tetragon / Falco    │ │
                    │  │ (policy engine)     │ │
                    │  └──────────┬──────────┘ │
                    └─────────────┼────────────┘
                                  │ bpf() syscall
                    ┌─────────────▼────────────┐
                    │    Kernel                 │
                    │  ┌─────────────────────┐ │
                    │  │  BPF LSM hooks      │ │
                    │  │  (bprm_check,       │ │
                    │  │   file_open,        │ │
                    │  │   socket_connect)   │ │
                    │  └──────────┬──────────┘ │
                    │  ┌──────────▼──────────┐ │
                    │  │  BPF Maps           │ │
                    │  │  (policy state,     │ │
                    │  │   audit buffer)     │ │
                    │  └─────────────────────┘ │
                    └──────────────────────────┘

Vantaggi rispetto a MAC tradizionale:
- Caricamento dinamico: nessun riavvio, nessun modulo kernel personalizzato
- Osservabilita` integrata: tracing + enforcement nella stessa infrastruttura
- Granularita` di processo: policy per singolo container, pod o binario
- Performance: verifica in-kernel senza context switch user/kernel
```

### Tetragon — Enforcement eBPF per Kubernetes

```bash
# Tetragon (by Cilium/Isovalent) e` il principale runtime security engine
# basato su eBPF. Si integra nativamente con Kubernetes.

# Installazione via Helm
helm repo add cilium https://helm.cilium.io
helm install tetragon cilium/tetragon -n kube-system

# Verificare che i pod siano running
kubectl get pods -n kube-system -l app.kubernetes.io/name=tetragon

# TracingPolicy: bloccare l'esecuzione di binari non autorizzati
# in tutti i pod di un namespace
cat <<'EOF' > restrict-exec.yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: restrict-shell-exec
spec:
  kprobes:
  - call: "security_bprm_check"
    syscall: false
    args:
    - index: 0
      type: "linux_binprm"
    selectors:
    - matchArgs:
      - index: 0
        operator: "Equal"
        values:
        - "/bin/bash"
        - "/bin/sh"
        - "/usr/bin/python3"
        - "/usr/bin/curl"
        - "/usr/bin/wget"
      matchNamespaces:
      - namespace: Production
        operator: In
      matchActions:
      - action: Sigkill
        rateLimit: "1/m"
EOF

kubectl apply -f restrict-exec.yaml

# Monitorare eventi in tempo reale
kubectl logs -n kube-system -l app.kubernetes.io/name=tetragon -f | \
    tetra getevents --output compact
# Esempio output:
# process nginx-pod /bin/bash SIGKILL "restrict-shell-exec"
```

### Falco — Runtime Threat Detection

```bash
# Falco (CNCF project) utilizza eBPF (o un kernel module) per rilevare
# comportamenti anomali a runtime. Non blocca (di default), ma segnala.

# Installazione su Ubuntu/Debian
curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | \
    gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] \
    https://download.falco.org/packages/deb stable main" | \
    tee /etc/apt/sources.list.d/falcosecurity.list
apt update && apt install -y falco

# Falco usa regole YAML. Esempio di regola custom:
# Rileva se un container scrive file in /etc
cat <<'EOF' >> /etc/falco/rules.d/custom-rules.yaml
- rule: Container Modifying /etc
  desc: Rileva scritture in /etc da processi containerizzati
  condition: >
    open_write and
    container and
    fd.name startswith /etc/ and
    not fd.name in (/etc/resolv.conf, /etc/hostname, /etc/hosts)
  output: >
    File in /etc modificato da container
    (user=%user.name command=%proc.cmdline file=%fd.name
    container_id=%container.id container_name=%container.name
    image=%container.image.repository)
  priority: WARNING
  tags: [filesystem, container]
EOF

# Riavviare e testare
systemctl restart falco
# In un container: touch /etc/test-falco
# Nei log di Falco:
# WARNING File in /etc modificato da container (user=root
#   command=touch /etc/test-falco container_id=abc123
#   container_name=test image=ubuntu)

# Falco puo` inviare alert a Slack, Teams, PagerDuty, webhook, ecc.
# tramite falcosidekick (companion project)
```

### Confronto eBPF vs MAC Tradizionale

```
Caratteristica      │ SELinux        │ AppArmor       │ eBPF LSM
────────────────────┼────────────────┼────────────────┼─────────────────
Kernel richiesto    │ Tutti          │ Tutti          │ 5.7+ (LSM hooks)
Modello policy      │ Tipo/Ruolo     │ Path-based     │ Programmatico
Caricamento policy  │ Richiede tools │ Richiede tools │ Dinamico (bpf())
Granularita`        │ Tipo di oggetto│ Path/capability│ Qualsiasi hook
Overhead            │ Basso          │ Molto basso    │ Variabile
Container-aware     │ Via label MCS  │ Via profilo    │ Nativo (cgroup)
Kubernetes-native   │ No             │ No             │ Si (Tetragon)
Curva apprendimento │ Alta           │ Media          │ Alta (per autori)
Distribuzione       │ RHEL, Fedora   │ Ubuntu, SUSE   │ Qualsiasi 5.7+
Caso d'uso ideale   │ Server mission │ Workstation,   │ Cloud-native,
                    │ critical       │ container host │ Kubernetes
```

---

## Automazione MAC con Ansible

### Playbook SELinux — Configurazione Completa

```yaml
# selinux-hardening.yml
# Configura SELinux in enforcing con boolean e contesti specifici per ogni ruolo

---
- name: Hardening SELinux su server RHEL/Rocky
  hosts: webservers
  become: true
  vars:
    selinux_state: enforcing
    selinux_policy: targeted
    web_root: /var/www/html
    custom_ports:
      - { port: 8443, proto: tcp, setype: http_port_t }
      - { port: 9090, proto: tcp, setype: http_port_t }
    selinux_booleans:
      - { name: httpd_can_network_connect, state: true, persistent: true }
      - { name: httpd_can_network_connect_db, state: true, persistent: true }
      - { name: httpd_use_nfs, state: false, persistent: true }
      - { name: httpd_execmem, state: false, persistent: true }

  tasks:
    - name: Installare dipendenze SELinux
      dnf:
        name:
          - policycoreutils-python-utils
          - selinux-policy-targeted
          - setroubleshoot-server
        state: present

    - name: Impostare SELinux in enforcing
      ansible.posix.selinux:
        state: "{{ selinux_state }}"
        policy: "{{ selinux_policy }}"
      register: selinux_result

    - name: Configurare boolean SELinux
      ansible.posix.seboolean:
        name: "{{ item.name }}"
        state: "{{ item.state }}"
        persistent: "{{ item.persistent }}"
      loop: "{{ selinux_booleans }}"

    - name: Aggiungere porte custom a SELinux
      community.general.seport:
        ports: "{{ item.port }}"
        proto: "{{ item.proto }}"
        setype: "{{ item.setype }}"
        state: present
      loop: "{{ custom_ports }}"

    - name: Impostare contesti file per web root
      community.general.sefcontext:
        target: "{{ web_root }}(/.*)?"
        setype: httpd_sys_content_t
        state: present
      notify: restorecon web root

    - name: Impostare contesto per directory scrivibili
      community.general.sefcontext:
        target: "{{ web_root }}/{{ item }}(/.*)?"
        setype: httpd_sys_rw_content_t
        state: present
      loop:
        - storage
        - cache
        - uploads
      notify: restorecon web root

    - name: Verificare stato SELinux
      command: sestatus
      register: sestatus_out
      changed_when: false

    - name: Mostrare stato SELinux
      debug:
        msg: "{{ sestatus_out.stdout_lines }}"

  handlers:
    - name: restorecon web root
      command: restorecon -Rv {{ web_root }}
```

### Playbook AppArmor — Profilo Custom

```yaml
# apparmor-hardening.yml
# Deploya profili AppArmor personalizzati e verifica enforcement

---
- name: Hardening AppArmor su server Ubuntu
  hosts: appservers
  become: true
  vars:
    apparmor_profiles_dir: /etc/apparmor.d
    custom_profiles:
      - name: usr.local.bin.myapp
        content: |
          #include <tunables/global>

          /usr/local/bin/myapp {
            #include <abstractions/base>
            #include <abstractions/nameservice>

            /usr/local/bin/myapp mr,
            /etc/myapp/** r,
            /var/log/myapp/** w,
            /var/lib/myapp/** rw,
            /tmp/myapp-* rw,

            network inet stream,
            network inet dgram,
            deny network raw,
            deny /proc/** w,
            deny /sys/** w,
          }

  tasks:
    - name: Installare AppArmor utilities
      apt:
        name:
          - apparmor-utils
          - apparmor-profiles
          - apparmor-profiles-extra
        state: present

    - name: Verificare che AppArmor sia attivo
      command: aa-enabled
      register: aa_status
      changed_when: false
      failed_when: aa_status.stdout != "Yes"

    - name: Deployare profili custom
      copy:
        content: "{{ item.content }}"
        dest: "{{ apparmor_profiles_dir }}/{{ item.name }}"
        owner: root
        group: root
        mode: "0644"
      loop: "{{ custom_profiles }}"
      notify: reload apparmor profiles

    - name: Mettere profili in enforce
      command: aa-enforce {{ apparmor_profiles_dir }}/{{ item.name }}
      loop: "{{ custom_profiles }}"
      changed_when: true

    - name: Verificare stato di tutti i profili
      command: aa-status
      register: aa_full_status
      changed_when: false

    - name: Controllare profili non in enforce
      shell: aa-status --json | python3 -c "
        import json, sys;
        d = json.load(sys.stdin);
        c = d.get('profiles', {}).get('complain', 0);
        print(f'Profili in complain: {c}');
        sys.exit(1 if c > 0 else 0)"
      register: complain_check
      changed_when: false
      failed_when: false

    - name: Avviso profili in complain mode
      debug:
        msg: "ATTENZIONE: {{ complain_check.stdout }} — valutare migrazione a enforce"
      when: complain_check.rc != 0

  handlers:
    - name: reload apparmor profiles
      command: apparmor_parser -r {{ apparmor_profiles_dir }}/{{ item.name }}
      loop: "{{ custom_profiles }}"
```

---

## Scenari di Hardening Reali

### Scenario 1: Hardening Web Server (Nginx + PHP-FPM)

```bash
# === SELinux (RHEL/Rocky) ===

# 1. Verifica che httpd_t sia in enforcing
sestatus
ps auxZ | grep nginx
# system_u:system_r:httpd_t:s0  nginx: master

# 2. Contesti file per document root custom
semanage fcontext -a -t httpd_sys_content_t "/var/www/mysite(/.*)?"
semanage fcontext -a -t httpd_sys_rw_content_t "/var/www/mysite/storage(/.*)?"
semanage fcontext -a -t httpd_sys_rw_content_t "/var/www/mysite/cache(/.*)?"
semanage fcontext -a -t httpd_log_t "/var/log/nginx/mysite(/.*)?"
restorecon -Rv /var/www/mysite/ /var/log/nginx/mysite/

# 3. Boolean per il caso d'uso
setsebool -P httpd_can_network_connect 1        # reverse proxy verso backend
setsebool -P httpd_can_network_connect_db 1     # connessione al DB
setsebool -P httpd_can_sendmail 1               # invio email (PHP mail())
setsebool -P httpd_execmem 0                    # DENY exec in memory

# 4. Porte non standard
semanage port -a -t http_port_t -p tcp 8443

# 5. Verifica: nessun denial
ausearch -m avc -ts recent | grep httpd

# === AppArmor (Ubuntu/Debian) ===

# Profilo completo per Nginx
cat > /etc/apparmor.d/usr.sbin.nginx << 'EOF'
#include <tunables/global>

/usr/sbin/nginx {
    #include <abstractions/base>
    #include <abstractions/nameservice>
    #include <abstractions/openssl>

    capability net_bind_service,
    capability setuid,
    capability setgid,
    capability dac_override,

    network inet stream,
    network inet6 stream,

    /etc/nginx/** r,
    /etc/ssl/** r,
    /etc/letsencrypt/** r,

    /var/www/mysite/** r,
    /var/www/mysite/storage/** rw,
    /var/www/mysite/cache/** rw,

    /var/log/nginx/** w,
    /var/log/nginx/ r,

    /run/nginx.pid rw,
    /run/nginx/ rw,

    /usr/sbin/nginx mr,
    /usr/sbin/nginx ix,

    /usr/lib/** mr,
    /usr/share/nginx/** r,

    # PHP-FPM unix socket
    /run/php/php*-fpm.sock rw,

    # Deny espliciti
    deny /etc/shadow r,
    deny /etc/passwd w,
    deny /root/** rwx,
    deny /home/** rwx,
    deny /proc/kcore r,
}
EOF

apparmor_parser -r /etc/apparmor.d/usr.sbin.nginx
```

### Scenario 2: Hardening Database Server (PostgreSQL)

```bash
# === SELinux ===

# PostgreSQL usa il tipo postgresql_t
ps auxZ | grep postgres
# system_u:system_r:postgresql_t:s0  postgres: ...

# Data directory custom
semanage fcontext -a -t postgresql_db_t "/data/pgdata(/.*)?"
semanage fcontext -a -t postgresql_log_t "/var/log/postgresql(/.*)?"
restorecon -Rv /data/pgdata/ /var/log/postgresql/

# Porta non standard (es. 5433)
semanage port -a -t postgresql_port_t -p tcp 5433

# Boolean
setsebool -P postgresql_can_rsync 0             # no rsync (ridurre superficie)
setsebool -P selinuxuser_postgresql_connect_enabled 1  # utenti confinati possono connettersi

# === AppArmor ===

cat > /etc/apparmor.d/usr.lib.postgresql.bin.postgres << 'EOF'
#include <tunables/global>

/usr/lib/postgresql/*/bin/postgres {
    #include <abstractions/base>
    #include <abstractions/nameservice>
    #include <abstractions/openssl>

    capability dac_override,
    capability dac_read_search,
    capability fowner,
    capability fsetid,
    capability setuid,
    capability setgid,

    network inet stream,
    network inet6 stream,
    network unix stream,

    /etc/postgresql/** r,
    /etc/ssl/** r,

    /var/lib/postgresql/** rwk,
    /data/pgdata/** rwk,

    /var/log/postgresql/** w,
    /run/postgresql/** rw,

    /usr/lib/postgresql/*/bin/* mr,
    /usr/lib/postgresql/*/lib/** mr,
    /usr/share/postgresql/** r,

    /proc/*/oom_score_adj rw,
    /dev/shm/** rwk,

    deny /etc/shadow r,
    deny /root/** rwx,
    deny /home/** rwx,
}
EOF

apparmor_parser -r /etc/apparmor.d/usr.lib.postgresql.bin.postgres
```

### Scenario 3: Hardening Container Host

```bash
# === SELinux (RHEL/Rocky con Podman) ===

# 1. SELinux DEVE essere enforcing
getenforce  # Enforcing

# 2. Boolean per container
setsebool -P container_manage_cgroup 1
setsebool -P container_use_devices 0          # deny accesso a /dev
setsebool -P container_connect_any 0          # deny connessione a porte arbitrarie

# 3. Storage dei container
semanage fcontext -a -t container_var_lib_t "/data/containers(/.*)?"
restorecon -Rv /data/containers/

# 4. Volumi: usa SEMPRE :Z o :z
podman run -v /data/app:/data:Z --name myapp myimage

# 5. Usa udica per policy custom
podman inspect myapp > myapp.json
udica -j myapp.json myapp_policy
semodule -i myapp_policy.cil

# 6. Container rootless (ulteriore isolamento)
# Il container runtime esegue nello user namespace
# → anche se un attaccante evade il container, è unprivileged

# === AppArmor (Ubuntu con Docker) ===

# 1. Verifica che Docker usi AppArmor
docker info | grep -i apparmor

# 2. Profili custom per ogni servizio container
# (vedi sezione "AppArmor e Container")

# 3. Limita capabilities
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myimage

# 4. seccomp profile custom
docker run --security-opt seccomp=/etc/docker/seccomp-strict.json myimage

# 5. Read-only filesystem
docker run --read-only --tmpfs /tmp:rw,noexec,nosuid myimage

# 6. No new privileges
docker run --security-opt no-new-privileges myimage
```

---

## Best Practices

1. **Mai disabilitare il MAC**: La soluzione a "SELinux/AppArmor blocca il mio servizio" non è mai disabilitarli. Trovare la causa e configurare correttamente è sempre possibile e sempre preferibile.

2. **Usa permissive/complain mode per il debugging**: Non serve passare da enforcing a disabled. Usa permissive mode (SELinux) o complain mode (AppArmor) per loggare i denial senza bloccarli.

3. **Controlla il contesto/profilo prima di cercare la regola**: L'80% dei problemi SELinux si risolve con `restorecon`. L'80% dei problemi AppArmor si risolve aggiungendo un path al profilo.

4. **Boolean prima di audit2allow**: In SELinux, prima cerca un boolean che risolva il problema. `audit2allow` è l'ultima risorsa e le regole generate dovrebbero essere sempre riviste manualmente.

5. **Profili minimali**: Un buon profilo MAC permette solo ciò che è strettamente necessario. Profili permissivi vanificano lo scopo del MAC.

6. **Testa in staging prima della produzione**: Applica nuovi profili o modifiche in un ambiente di test con traffico realistico prima di applicarli in produzione.

7. **Documenta le eccezioni**: Ogni modulo SELinux custom o regola AppArmor aggiunta manualmente deve essere documentata con la motivazione e la data.

8. **Monitora i log continuamente**: Configura alerting per i denial MAC in produzione. Un denial potrebbe indicare un attacco in corso o una misconfiguration.

9. **Aggiorna i profili dopo gli aggiornamenti software**: Un aggiornamento dell'applicazione potrebbe richiedere nuovi accessi. Testa con complain mode dopo ogni aggiornamento.

10. **Confina i servizi esposti a internet**: I servizi accessibili dall'esterno (web server, mail server, DNS) devono essere i primi ad avere profili MAC robusti.

11. **Per-domain permissive, non global**: In SELinux, usa `semanage permissive -a <tipo>` per rendere permissive un singolo dominio senza abbassare la sicurezza dell'intero sistema.

12. **Defense in depth**: Combina MAC (SELinux/AppArmor) con seccomp, capabilities dropping, namespaces, e cgroups. Nessun singolo layer è sufficiente.

13. **Audit regolare delle customizzazioni**: Ogni trimestre, rivedi le eccezioni aggiunte con `semanage export` o confrontando i profili AppArmor con i default del pacchetto.

14. **Automatizza con Configuration Management**: Gestisci policy SELinux e profili AppArmor tramite Ansible/Puppet/Salt. I moduli `ansible.posix.seboolean`, `ansible.posix.sefcontext`, e i template per i profili AppArmor sono maturi e testati.

---

## Troubleshooting

### Problema: SELinux blocca l'accesso ai file dopo uno spostamento

**Sintomi**: Un servizio non può leggere file che funzionavano prima, dopo averli spostati con `mv` da un'altra posizione.

**Causa**: `mv` preserva il contesto SELinux originale. Un file creato in `/home/user/` ha tipo `user_home_t`. Spostato in `/var/www/`, mantiene `user_home_t` anziché diventare `httpd_sys_content_t`.

**Soluzione**:
```bash
# Verifica contesto
ls -Z /var/www/html/file.html
# Se il tipo è sbagliato:
restorecon -Rv /var/www/html/
# Questo applica il contesto corretto basato sulle regole fcontext
```

### Problema: AppArmor blocca un'applicazione dopo aggiornamento

**Sintomi**: Il servizio non parte dopo un aggiornamento di pacchetto. `journalctl -k` mostra "apparmor=DENIED".

**Causa**: Il nuovo software accede a file o porte non previste dal profilo attuale.

**Soluzione**:
```bash
# Metti il profilo in complain
aa-complain /etc/apparmor.d/usr.sbin.myservice

# Avvia il servizio
systemctl start myservice

# Analizza e aggiorna il profilo
aa-logprof

# Rimetti in enforce
aa-enforce /etc/apparmor.d/usr.sbin.myservice
```

### Problema: SELinux impedisce al web server di connettersi al backend

**Sintomi**: Nginx restituisce 502 Bad Gateway quando tenta di fare proxy_pass verso un backend.

**Causa**: SELinux impedisce a httpd_t di stabilire connessioni di rete verso backend.

**Soluzione**:
```bash
# Verifica
ausearch -m avc | grep httpd | grep connect

# La soluzione più comune:
setsebool -P httpd_can_network_connect 1

# Se il backend è un database:
setsebool -P httpd_can_network_connect_db 1
```

### Problema: AppArmor DENIED per /proc o /sys

**Sintomi**: L'applicazione non riesce a leggere `/proc/meminfo` o `/sys/devices/...`.

**Causa**: Il profilo non include le abstractions necessarie o non ha regole per `/proc` e `/sys`.

**Soluzione**:
```bash
# Aggiungi al profilo le abstractions appropriate
# /etc/apparmor.d/opt.myapp
/opt/myapp {
    #include <abstractions/base>     # include accesso base a /proc
    /proc/meminfo r,
    /proc/sys/net/** r,
    /sys/devices/system/cpu/** r,
}

# Ricarica
apparmor_parser -r /etc/apparmor.d/opt.myapp
```

### Problema: SELinux e PostgreSQL su data directory custom

**Sintomi**: PostgreSQL non riesce ad avviarsi dopo aver spostato il data directory in `/data/pgdata/`.

**Causa**: La nuova directory non ha il contesto `postgresql_db_t`.

**Soluzione**:
```bash
semanage fcontext -a -t postgresql_db_t "/data/pgdata(/.*)?"
restorecon -Rv /data/pgdata/
systemctl start postgresql
```

### Problema: Container Podman non può scrivere in volume montato

**Sintomi**: Errori di permesso quando il container tenta di scrivere in un volume host, nonostante i permessi Unix siano corretti.

**Causa**: Il volume non ha il contesto SELinux corretto per l'accesso dal container.

**Soluzione**:
```bash
# Opzione 1: flag :Z (contesto privato per questo container)
podman run -v /data/app:/data:Z myimage

# Opzione 2: contesto manuale (utile per volumi condivisi)
semanage fcontext -a -t container_file_t "/data/app(/.*)?"
restorecon -Rv /data/app/
```

### Problema: SELinux blocca cron job

**Sintomi**: Cron job fallisce con "Permission denied" ma funziona se eseguito manualmente da shell.

**Causa**: Cron esegue i job nel dominio `crond_t` con il contesto dell'utente SELinux mappato. L'utente potrebbe avere un contesto diverso da quello usato nella shell interattiva.

**Soluzione**:
```bash
# Verifica il contesto del cron job
ausearch -m avc | grep crond

# Se il problema è il tipo dei file target:
restorecon -Rv /path/to/script/and/data/

# Se il problema è l'utente SELinux dell'utente cron:
semanage login -a -s unconfined_u cron_user
# oppure, preferibilmente, aggiungi le regole mancanti
```

### Problema: AppArmor e snap: conflitto profili

**Sintomi**: Un'applicazione snap non funziona o si blocca con denial AppArmor.

**Causa**: I profili snap generati automaticamente possono conflittuare con profili custom o con aggiornamenti del sistema.

**Soluzione**:
```bash
# Verifica il profilo dello snap
snap connections myapp
aa-status | grep snap

# Rigenera i profili snap
snap restart apparmor
# oppure
apparmor_parser -r /var/lib/snapd/apparmor/profiles/snap.*

# Se il problema persiste, verifica i denial
journalctl -k --grep="apparmor.*snap.*DENIED" --since "10 min ago"
```

### Problema: SELinux e NFS/CIFS home directories

**Sintomi**: Utenti con home directory su NFS non possono effettuare operazioni che funzionavano con home locali.

**Causa**: I file su NFS hanno il tipo `nfs_t`, non `user_home_t`. Le policy per i servizi potrebbero non permettere accesso a `nfs_t`.

**Soluzione**:
```bash
# Boolean specifici per NFS
setsebool -P use_nfs_home_dirs 1

# Per Samba/CIFS
setsebool -P use_samba_home_dirs 1

# Per httpd che serve da NFS
setsebool -P httpd_use_nfs 1
```

### Problema: AppArmor blocca scrittura in /tmp con namespace privato

**Sintomi**: Servizio systemd con `PrivateTmp=yes` non può scrivere in `/tmp`.

**Causa**: Con `PrivateTmp=yes`, systemd monta un namespace privato in `/tmp/systemd-private-XXX-SERVICE.service-XXX/tmp/`. Il profilo AppArmor potrebbe non coprire questo percorso.

**Soluzione**:
```bash
# Nel profilo AppArmor, usa owner + glob per il tmp privato
/usr/sbin/myservice {
    # ...
    owner /tmp/** rw,
    # Questo copre sia /tmp/ reale sia il namespace privato
    # perché AppArmor risolve dal namespace mount del processo
}
```

### Problema: SELinux denies dopo kernel o policy update

**Sintomi**: Dopo un aggiornamento del sistema, servizi precedentemente funzionanti generano AVC denial.

**Causa**: Aggiornamento della policy SELinux ha cambiato le regole. Oppure nuovi path/operazioni non coperti.

**Soluzione**:
```bash
# 1. Verifica la versione della policy
rpm -q selinux-policy-targeted

# 2. Controlla i denial
ausearch -m avc --start today | audit2why

# 3. Se è un bug nella policy, applica workaround temporaneo
# e segnala il bug a bugzilla.redhat.com

# 4. Se serve, ripristina la policy precedente (se salvata)
# oppure attendi il fix nel prossimo update
```

### Problema: AppArmor e MySQL/MariaDB con datadir custom

**Sintomi**: MySQL non accede al datadir personalizzato.

**Causa**: Il profilo default di MySQL include solo `/var/lib/mysql/`.

**Soluzione**:
```bash
# Aggiungi il percorso al profilo
# In /etc/apparmor.d/local/usr.sbin.mysqld (file override locale):
/data/mysql/ r,
/data/mysql/** rwk,

# Ricarica
apparmor_parser -r /etc/apparmor.d/usr.sbin.mysqld
systemctl restart mysql
```

### Problema: SELinux e sendmail/postfix relay

**Sintomi**: L'applicazione web non riesce a inviare email tramite la funzione `mail()` di PHP o il comando `sendmail`.

**Causa**: `httpd_t` non ha permesso di comunicare con `sendmail_t`.

**Soluzione**:
```bash
setsebool -P httpd_can_sendmail 1
```

### Problema: AVC flood — migliaia di denial per lo stesso accesso

**Sintomi**: Il log di audit si riempie con migliaia di denial identici, rallentando il sistema.

**Causa**: Un processo tenta ripetutamente un'operazione negata (es. polling su un file).

**Soluzione**:
```bash
# 1. Se l'accesso è legittimo → risolvi con boolean/fcontext/modulo

# 2. Se l'accesso NON è legittimo ma non vuoi il flood:
# Usa dontaudit per silenziare senza permettere
# Nel file .te del modulo custom:
# dontaudit httpd_t user_home_t:file read;

# 3. Rate limiting dell'audit
# /etc/audit/auditd.conf
# freq = 50          # flush ogni 50 record
# max_log_file = 50  # max 50 MB per file

# 4. Verifica che non ci siano dontaudit che mascherano problemi reali
semodule -DB   # Disabilita tutte le dontaudit (per debug temporaneo)
# ATTENZIONE: genererà molti log. Riabilita con:
semodule -B
```

### Problema: SELinux impedisce l'accesso a /dev/shm per shared memory

**Sintomi**: Applicazioni che usano shared memory POSIX (shm_open) falliscono con EACCES.

**Causa**: Il tipo del processo non ha permesso di accedere a `tmpfs_t` in `/dev/shm`.

**Soluzione**:
```bash
# Verifica il denial
ausearch -m avc | grep shm

# Nella maggior parte dei casi, serve un modulo custom:
# allow myapp_t tmpfs_t:file { read write create unlink open };

# Per PostgreSQL è un boolean noto:
setsebool -P postgresql_selinux_transmit_client_label 1
```

---

## Esercizi

### Esercizio 1: Confinare un'applicazione custom con SELinux

**Obiettivo:** Creare un modulo SELinux completo per un'applicazione web custom.

**Scenario:** L'applicazione `webapp` è installata in `/opt/webapp/`, ascolta sulla porta TCP 9090, scrive log in `/var/log/webapp/`, legge configurazione da `/opt/webapp/etc/`, e si connette a PostgreSQL sulla porta 5432.

**Passi:**
1. Scrivere il file `.te` con type declarations, transitions, e allow rules
2. Scrivere il file `.fc` con i file context
3. Compilare e installare il modulo
4. Registrare la porta con `semanage port`
5. Applicare i contesti con `restorecon`
6. Verificare con `sesearch` che le regole siano caricate
7. Avviare l'applicazione e verificare zero AVC denial con `ausearch`

**Hint:** Usare le macro `init_daemon_domain()`, `files_type()`, `logging_log_file()`, `corenet_tcp_connect_postgresql_port()` per semplificare il `.te`.

### Esercizio 2: Profilo AppArmor per un servizio Python

**Obiettivo:** Creare e raffinare un profilo AppArmor per un servizio Python Flask.

**Scenario:** Un servizio Flask in `/opt/flask-api/` usa un virtualenv in `/opt/flask-api/venv/`, si connette a Redis su localhost:6379, scrive in `/var/log/flask-api/`, e serve API REST sulla porta 5000.

**Passi:**
1. Creare un profilo iniziale con `aa-genprof`
2. Esercitare tutte le funzionalità dell'applicazione
3. Raffinare il profilo eliminando regole troppo permissive (glob eccessivi)
4. Aggiungere deny espliciti per risorse sensibili
5. Passare da complain a enforce
6. Aggiungere regole dbus se il servizio interagisce con systemd
7. Verificare con `aa-status` e `journalctl -k`

### Esercizio 3: seccomp Profile per Container

**Obiettivo:** Generare un profilo seccomp custom per un container di produzione.

**Passi:**
1. Eseguire il container con `--security-opt seccomp=unconfined` e `strace -f`
2. Estrarre le syscall uniche utilizzate
3. Creare un profilo JSON con solo le syscall necessarie e `SCMP_ACT_ERRNO` come default
4. Testare il container con il profilo custom
5. Confrontare il profilo custom con il default OCI e documentare le differenze
6. Verificare che il container funzioni completamente sotto il profilo restrittivo

### Esercizio 4: Audit MAC e Compliance Check

**Obiettivo:** Eseguire un audit completo della configurazione MAC di un sistema.

**Passi:**
1. Eseguire `lynis audit system` e analizzare la sezione MAC
2. Configurare aide per monitorare i file di configurazione MAC
3. Creare query osquery per monitoraggio continuo dello stato MAC
4. Generare un report che includa:
   - Stato MAC (enforcing/enabled)
   - Servizi non confinati
   - Customizzazioni (boolean non-default, moduli custom, profili custom)
   - Denial non risolti
5. Proporre remediation per ogni finding

---

## Auto-valutazione

**1. Qual è la differenza fondamentale tra il modello label-based di SELinux e il modello path-based di AppArmor? Quale conseguenza ha per la sicurezza degli hard link?**

> SELinux assegna etichette (contesti) agli inode: l'etichetta rimane associata al file indipendentemente dal percorso. AppArmor verifica le autorizzazioni in base al percorso del file. Per gli hard link: in SELinux, un hard link e il file originale condividono lo stesso inode e quindi la stessa etichetta — le regole si applicano uniformemente. In AppArmor, un hard link crea un secondo percorso per lo stesso inode, e se quel secondo percorso non è coperto dal profilo, potrebbe costituire un bypass. Per questo motivo SELinux è considerato più robusto contro gli attacchi basati su hard link.

**2. Descrivi il percorso di una decisione di accesso in SELinux, dall'invocazione della syscall alla risposta ALLOW/DENY.**

> 1) Il processo invoca una syscall (es. open()). 2) Il kernel esegue i controlli DAC standard. 3) Se DAC permette, il kernel invoca l'hook LSM corrispondente (es. security_inode_permission). 4) SELinux recupera il contesto del soggetto (dominio del processo, es. httpd_t) e del target (tipo del file, es. httpd_sys_content_t). 5) Cerca nella AVC (Access Vector Cache) una decisione già calcolata per la tupla (source_type, target_type, class). 6) Se AVC hit, ritorna la decisione cached. 7) Se AVC miss, consulta il Security Server che valuta la policy binaria in memoria. 8) Il risultato viene memorizzato nell'AVC per lookup futuri. 9) Se DENY, genera un messaggio AVC nel log di audit.

**3. Cosa succede se si sposta un file con `mv` da `/home/user/` a `/var/www/html/` su un sistema SELinux enforcing? Come si risolve?**

> `mv` preserva gli attributi estesi dell'inode, incluso il contesto SELinux. Il file mantiene il tipo `user_home_t` originale anziché acquisire `httpd_sys_content_t`. Il web server (httpd_t) non avrà permesso di leggere il file. Soluzione: `restorecon -v /var/www/html/file` per ripristinare il contesto basato sulle regole fcontext del database. Alternativa preventiva: usare `cp` (che crea un nuovo inode con contesto ereditato dalla directory destinazione) anziché `mv`.

**4. Spiega la differenza tra `setenforce 0` e `semanage permissive -a httpd_t`. Quale preferisci per il debugging e perché?**

> `setenforce 0` mette TUTTO il sistema in permissive mode: nessun dominio viene enforcement. `semanage permissive -a httpd_t` mette SOLO il dominio httpd_t in permissive, mentre tutti gli altri domini rimangono in enforcing. Per il debugging è fortemente preferibile il per-domain permissive perché: 1) mantiene la protezione su tutto il resto del sistema, 2) isola i denial al solo dominio in test, 3) è più granulare e produce log meno rumorosi.

**5. Come funziona l'isolamento MCS tra container Podman? Perché il container A non può leggere i file del container B?**

> Podman assegna automaticamente categorie MCS casuali a ogni container (es. Container A: s0:c123,c456, Container B: s0:c789,c012). I volumi montati con il flag :Z ricevono il contesto con le stesse categorie del container. SELinux verifica che il contesto del processo (con le sue categorie) domini le categorie dell'oggetto. Poiché c123,c456 != c789,c012, il container A non può accedere ai file etichettati con le categorie del container B, e viceversa.

**6. Qual è la differenza tra i flag `:z` e `:Z` nel montaggio di volumi Podman? Quando usare ciascuno?**

> `:z` applica il contesto `container_share_t`, permettendo a TUTTI i container sull'host di accedere al volume. Va usato per dati condivisi tra più container. `:Z` applica il contesto `svirt_sandbox_file_t` con le categorie MCS specifiche del container, creando un accesso esclusivo. Va usato per dati privati di un singolo container. Usare `:Z` su directory condivise causerebbe problemi perché cambierebbe le categorie MCS, invalidando l'accesso degli altri container.

**7. In un profilo AppArmor, qual è la differenza tra `ix`, `px`, `cx`, e `ux` come qualificatori di esecuzione?**

> `ix` (inherit execute): il processo figlio eredita il profilo del padre, eseguendo sotto le stesse restrizioni. `px` (profile execute): il processo figlio viene eseguito sotto il profilo definito per il suo eseguibile; se non esiste, l'esecuzione fallisce. `cx` (child execute): il processo figlio viene eseguito sotto un sub-profilo (hat) definito localmente nel profilo del padre. `ux` (unconfined execute): il processo figlio viene eseguito senza alcun profilo AppArmor — sconsigliato per la sicurezza. Per la sicurezza: preferire px > cx > ix > ux.

**8. Descrivi il rapporto tra seccomp, SELinux/AppArmor, e capabilities nella difesa in profondità di un container.**

> I tre meccanismi operano a livelli diversi e si complementano: seccomp filtra le syscall a livello di interfaccia kernel-userspace, bloccando intere classi di operazioni prima che raggiungano qualsiasi altro check. SELinux/AppArmor opera a livello di risorse (file, porte, processi), determinando quali oggetti specifici un processo confinato può accedere. Le capabilities (POSIX) suddividono i privilegi di root in unità granulari (es. CAP_NET_BIND_SERVICE), permettendo di rimuovere privilegi non necessari. In un container: seccomp blocca syscall come mount/reboot, il MAC blocca accesso a file/porte non autorizzati, e il dropping delle capabilities rimuove privilegi come CAP_SYS_ADMIN anche se il processo è root nel suo namespace.

---

## Letture Primarie Consigliate

1. **SELinux Project Wiki** — selinuxproject.org — Documentazione ufficiale del progetto SELinux, inclusa architettura, policy language reference, e guide per sviluppatori.

2. **Red Hat — "Using SELinux" (RHEL 9)** — access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/using_selinux/ — Guida operativa completa con esempi pratici per RHEL 9. Consultato 2026-05-23.

3. **SELinux Notebook** — github.com/SELinuxProject/selinux-notebook — Riferimento tecnico completo su policy language, oggetto/soggetto management, e internals.

4. **AppArmor Wiki** — gitlab.com/apparmor/apparmor/-/wikis/home — Documentazione ufficiale del progetto AppArmor, inclusa sintassi dei profili e guide per sviluppatori.

5. **Ubuntu Server Guide — AppArmor** — ubuntu.com/server/docs/apparmor — Guida pratica per la gestione di AppArmor su Ubuntu. Consultato 2026-05-23.

6. **NIST SP 800-123** — "Guide to General Server Security" — Sezioni su Mandatory Access Control e hardening del sistema operativo.

7. **kernel.org — LSM Documentation** — kernel.org/doc/html/latest/admin-guide/LSM/ — Documentazione kernel sullo stack Linux Security Modules, incluso stacking e API degli hook. Consultato 2026-05-23.

8. **man pages**: `selinux(8)`, `semanage(8)`, `restorecon(8)`, `audit2allow(1)`, `sesearch(1)`, `apparmor(7)`, `apparmor.d(5)`, `aa-genprof(8)`, `aa-logprof(8)`, `seccomp(2)`.

9. **OCI Runtime Specification** — github.com/opencontainers/runtime-spec — Specifica dei profili seccomp default per container OCI.

10. **Dan Walsh Blog** — danwalsh.livejournal.com — Blog del principal SELinux engineer di Red Hat, con troubleshooting e best practices reali.

---

## Collegamenti Incrociati

- **07-kernel.md** — Architettura kernel, LSM framework, namespaces, capabilities, eBPF per tracing dei denial MAC
- **14-containerizzazione.md** — Container security, namespaces, cgroups, Podman/Docker security options, rootless containers
- **15-SECURITY/** — Framework di sicurezza, hardening, compliance, auditing
- **08-firewall-iptables-nftables.md** — Regole di rete che complementano il MAC per il controllo del traffico
- **06-gestione-utenti-permessi.md** — DAC (permessi Unix), capabilities, ACL — prerequisiti per comprendere il MAC
- **22-systemd-avanzato.md** — Unit hardening con SystemCallFilter (seccomp), ProtectSystem, PrivateTmp
- **25-automazione-ansible.md** — Automazione della gestione SELinux/AppArmor con moduli Ansible

---

## Glossario Locale

| Termine | Definizione |
|---------|-------------|
| **AVC** | Access Vector Cache — cache nel kernel che memorizza le decisioni di accesso SELinux per evitare di consultare il Security Server a ogni operazione |
| **Bell-LaPadula** | Modello formale di sicurezza multi-livello: "no read up, no write down". Implementato da MLS in SELinux |
| **Boolean (SELinux)** | Interruttore on/off che modifica il comportamento della policy senza riscriverla |
| **CIL** | Common Intermediate Language — linguaggio intermedio di policy SELinux, più moderno del formato m4 |
| **Complain mode** | Modalità AppArmor che logga le violazioni senza bloccarle (equivalente di permissive in SELinux) |
| **DAC** | Discretionary Access Control — modello di sicurezza Unix basato su owner/group/other |
| **Domain** | In SELinux, il tipo assegnato a un processo (es. httpd_t). Determina cosa il processo può fare |
| **Enforcing** | Modalità SELinux/AppArmor che applica attivamente le policy, bloccando gli accessi non autorizzati |
| **fcontext** | File Context — regola nel database SELinux che mappa un pattern di percorso a un contesto SELinux |
| **Hat** | In AppArmor, un sub-profilo definito all'interno di un profilo padre, utilizzabile con change_hat() |
| **Landlock** | LSM minore non privilegiato (kernel 5.13+) che permette ai processi di auto-confinarsi |
| **LSM** | Linux Security Modules — framework nel kernel che fornisce hook per i moduli di sicurezza MAC |
| **MAC** | Mandatory Access Control — politiche di sicurezza imposte dall'amministratore che nemmeno root può aggirare |
| **MCS** | Multi-Category Security — classificazione orizzontale in SELinux, usata per l'isolamento dei container |
| **MLS** | Multi-Level Security — classificazione gerarchica dei dati (Unclassified → Top Secret) |
| **Permissive** | Modalità SELinux che logga le violazioni senza bloccarle |
| **Policy module** | Pacchetto compilato (.pp) contenente regole SELinux installabili con semodule |
| **Profile** | In AppArmor, file di configurazione che definisce le risorse accessibili a un programma |
| **seccomp** | Secure Computing Mode — meccanismo kernel per filtrare le syscall disponibili a un processo |
| **Security Server** | Componente kernel di SELinux che valuta le richieste di accesso contro la policy binaria |
| **Smack** | Simplified Mandatory Access Control Kernel — LSM label-based minimalista per sistemi embedded |
| **TOMOYO** | LSM path-based con learning mode nativo, sviluppato da NTT Data |
| **Type Enforcement** | Meccanismo principale di SELinux: regole allow che specificano quali tipi di processo possono accedere a quali tipi di oggetto |
| **udica** | Strumento Red Hat per generare automaticamente policy SELinux per container analizzando l'inspect |

---

## Riferimenti

- **SELinux Project**: https://selinuxproject.org/
- **Red Hat SELinux Guide**: https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/using_selinux/
- **SELinux Coloring Book**: https://people.redhat.com/duffy/selinux/selinux-coloring-book_A4-Stapled.pdf
- **AppArmor Wiki**: https://gitlab.com/apparmor/apparmor/-/wikis/home
- **Ubuntu AppArmor Guide**: https://ubuntu.com/server/docs/security-apparmor
- **Dan Walsh Blog (SELinux)**: https://danwalsh.livejournal.com/
- `man semanage`, `man restorecon`, `man audit2allow`
- `man apparmor`, `man aa-genprof`, `man aa-logprof`, `man apparmor.d`
