# Utenti e Gruppi Linux — Guida Completa

> **Modulo 12** · **Aggiornamento:** 2026-05-24

## Idee guida
1. **`/etc/passwd` + `/etc/shadow` + `/etc/group` + `/etc/gshadow` — la quadriade dei database locali.**
2. **PAM modulare: `/etc/pam.d/` per ogni servizio, stack configurabile con control flag precisi.**
3. **sudo via `/etc/sudoers.d/` per granularità; `visudo` obbligatorio per la sintassi.**
4. **LDAP/SSSD per centralized auth in enterprise; `realmd` per join AD semplificato.**
5. **polkit per autorizzazioni desktop/systemd: policy action + rules JavaScript.**
6. **User namespaces per container rootless: `subuid`/`subgid` mappano UID interni → esterni.**
7. **Principio del minimo privilegio: utenti di servizio con `nologin`, `DynamicUser=`, `CapabilityBoundingSet=`.**
8. **Auditing continuo: `last`, `lastlog`, `faillog`, `wtmp`/`btmp`, `aureport` per tracciabilità.**


## Indice

- [Panoramica](#panoramica)
- [Database Utenti: /etc/passwd](#database-utenti-etcpasswd)
- [Database Password: /etc/shadow](#database-password-etcshadow)
- [Database Gruppi: /etc/group e /etc/gshadow](#database-gruppi-etcgroup-e-etcgshadow)
- [Gestione Utenti](#gestione-utenti)
- [Gestione Gruppi](#gestione-gruppi)
- [Password Policy e Aging](#password-policy-e-aging)
- [PAM — Pluggable Authentication Modules](#pam--pluggable-authentication-modules)
- [NSSwitch e Name Resolution](#nsswitch-e-name-resolution)
- [LDAP Client e SSSD](#ldap-client-e-sssd)
- [Integrazione Active Directory](#integrazione-active-directory)
- [Centralizzazione Autenticazione](#centralizzazione-autenticazione)
- [sudo — Deep Dive](#sudo--deep-dive)
- [polkit — Authorization Framework](#polkit--authorization-framework)
- [User Namespaces e Container Rootless](#user-namespaces-e-container-rootless)
- [systemd-homed — Home Directory Moderne](#systemd-homed--home-directory-moderne)
- [Login Management e Limiti](#login-management-e-limiti)
- [Ambiente Utente e /etc/skel](#ambiente-utente-e-etcskel)
- [Account di Servizio](#account-di-servizio)
- [Auditing Account](#auditing-account)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Panoramica

La gestione utenti e gruppi è la base del modello di sicurezza Linux. Ogni processo gira con un UID/GID che determina i suoi permessi. Il kernel non conosce nomi utente — opera esclusivamente su numeri UID e GID. La risoluzione nome→numero avviene in userspace tramite la libreria C (glibc) che consulta i database configurati in `/etc/nsswitch.conf`.

I file `/etc/passwd`, `/etc/shadow`, `/etc/group` e `/etc/gshadow` sono i database locali. In ambienti enterprise l'autenticazione è centralizzata via LDAP, Active Directory o FreeIPA tramite SSSD, ma i file locali rimangono sempre il fallback.

### UID e GID — Concetti Fondamentali

```
UID 0          → root (superutente, unico con bypass kernel su tutti i controlli)
UID 1-999      → utenti di sistema/servizio (range configurabile in /etc/login.defs)
UID 1000+      → utenti normali (interattivi)
UID 65534      → nobody (utente senza privilegi, usato per NFS squashing e fallback)

GID segue la stessa logica:
GID 0          → root group
GID 1-999      → gruppi di sistema
GID 1000+      → gruppi utente
```

Ogni processo ha un **effective UID** (eUID), un **real UID** (rUID) e un **saved UID** (sUID). Normalmente sono identici, ma meccanismi come setuid cambiano l'eUID mantenendo il rUID originale:

```bash
# Vedere gli ID di un processo
cat /proc/self/status | grep -E '^(Uid|Gid)'
# Uid:  1000  1000  1000  1000    (real, effective, saved, filesystem)
# Gid:  1000  1000  1000  1000

# I gruppi supplementari del processo corrente
id
# uid=1000(admin) gid=1000(admin) groups=1000(admin),27(sudo),999(docker)

cat /proc/self/status | grep Groups
# Groups: 27 999 1000
```

---

## Database Utenti: /etc/passwd

Il file `/etc/passwd` è il database primario degli utenti. È leggibile da tutti (permessi `644`) perché molti programmi necessitano della risoluzione UID→nome.

### Formato dei Campi

```
username:x:UID:GID:GECOS:home_directory:login_shell
```

| Campo | Descrizione | Esempio | Note |
|-------|-------------|---------|------|
| `username` | Nome di login | `admin` | Max 32 char, minuscole + cifre + underscore + trattino. Non iniziare con trattino o cifra (convezione, non requisito kernel) |
| `x` | Placeholder password | `x` | Indica che l'hash è in `/etc/shadow`. Un campo vuoto significa nessuna password (login senza password). Una `*` blocca il login via password |
| `UID` | User ID numerico | `1000` | 0 = root. Il kernel usa solo questo numero, mai il nome |
| `GID` | Primary Group ID | `1000` | GID del gruppo primario. Deve esistere in `/etc/group` |
| `GECOS` | Informazioni utente | `Admin User,,,` | Campo libero; per convenzione: nome completo, stanza, telefono lavoro, telefono casa, altro. Separati da virgola. Usato da `finger` e `chfn` |
| `home_directory` | Home directory | `/home/admin` | Directory di lavoro al login. Se non esiste, il login può fallire (dipende dalla configurazione PAM) |
| `login_shell` | Shell di login | `/bin/bash` | Deve essere elencata in `/etc/shells` per gli utenti normali. Per account di servizio: `/usr/sbin/nologin` o `/bin/false` |

### Esempi Commentati

```bash
# Superutente — UID 0 = bypass di tutti i controlli del kernel
root:x:0:0:root:/root:/bin/bash

# Utente normale con home standard
admin:x:1000:1000:Admin User:/home/admin:/bin/bash

# Utente di servizio — nologin impedisce accesso interattivo
nginx:x:101:101:nginx web server:/var/www:/usr/sbin/nologin

# Utente nobody — fallback senza privilegi
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin

# Utente con campo GECOS completo
mario:x:1001:1001:Mario Rossi,Ufficio 42,0612345678,:/home/mario:/bin/bash
```

### Comandi per Interrogare /etc/passwd

```bash
# Leggere un utente specifico (dal file locale)
grep '^admin:' /etc/passwd

# Leggere un utente da TUTTI i database configurati (locale + LDAP + SSSD ecc.)
getent passwd admin

# Contare gli utenti con shell di login attiva
grep -c '/bin/bash\|/bin/zsh\|/bin/fish' /etc/passwd

# Trovare utenti con UID 0 (dovrebbe essere solo root)
awk -F: '$3 == 0 {print $1}' /etc/passwd

# Elencare tutti gli utenti di sistema (UID < 1000)
awk -F: '$3 < 1000 {printf "%-20s UID=%-6s Shell=%s\n", $1, $3, $7}' /etc/passwd

# Modificare campo GECOS
sudo chfn -f "Mario Rossi" -r "Ufficio 42" -w "0612345678" mario
chfn                                    # Modifica i propri dati (senza sudo)
```

---

## Database Password: /etc/shadow

Il file `/etc/shadow` contiene gli hash delle password e le policy di aging. È leggibile solo da root (permessi `640`, gruppo `shadow`).

### Formato dei Campi

```
username:password_hash:lastchange:min:max:warn:inactive:expire:reserved
```

| Campo | Descrizione | Esempio | Note |
|-------|-------------|---------|------|
| `username` | Nome utente | `admin` | Deve corrispondere a un record in `/etc/passwd` |
| `password_hash` | Hash della password | `$6$rounds=5000$salt$hash...` | Vedi tabella algoritmi sotto. `!` o `!!` = account bloccato. `*` = nessun login via password (mai impostata). Campo vuoto = nessuna password richiesta |
| `lastchange` | Ultimo cambio password | `19500` | Giorni dal 1 gennaio 1970 (epoch). `0` = l'utente deve cambiare password al prossimo login |
| `min` | Giorni minimi tra cambi | `0` | L'utente non può cambiare password prima che siano trascorsi questi giorni. `0` = nessun vincolo |
| `max` | Giorni massimi di validità | `99999` | La password scade dopo questo numero di giorni. `99999` = praticamente mai |
| `warn` | Giorni di avviso | `7` | Quanti giorni prima della scadenza il sistema avvisa l'utente al login |
| `inactive` | Giorni di grazia | `` (vuoto) | Dopo la scadenza, l'utente ha ancora questi giorni per cambiare la password. Dopo, l'account è disabilitato. Vuoto = nessun periodo di grazia |
| `expire` | Data scadenza account | `` (vuoto) | Giorni dall'epoch in cui l'account scade completamente (indipendentemente dalla password). Vuoto = mai |
| `reserved` | Riservato | `` | Non usato attualmente |

### Algoritmi di Hash Password

```
Prefisso    Algoritmo        Note
──────────────────────────────────────────────────────────────
$1$         MD5              Obsoleto, non usare
$5$         SHA-256          Accettabile, preferire yescrypt
$6$         SHA-512          Ancora diffuso, default su sistemi meno recenti
$y$         yescrypt         Default su Debian 12+, Ubuntu 22.04+, Fedora 35+
$2b$        bcrypt           Usato da alcuni BSD e configurazioni specifiche
```

Il formato completo di un hash SHA-512 è: `$6$rounds=N$salt$hash` dove `rounds` è il costo computazionale (default 5000, aumentabile per rallentare il bruteforce).

Yescrypt (`$y$`) è il default moderno — è memory-hard, il che lo rende resistente ad attacchi con GPU e ASIC.

```bash
# Vedere quale algoritmo è in uso
sudo grep '^admin:' /etc/shadow | cut -d: -f2 | cut -d'$' -f2
# Output: "6" (SHA-512) oppure "y" (yescrypt)

# Configurare l'algoritmo in /etc/login.defs
# ENCRYPT_METHOD YESCRYPT
# YESCRYPT_COST_FACTOR 5

# Oppure tramite PAM — vedere la sezione PAM

# Generare un hash manualmente (utile per Ansible, script)
# mkpasswd è il metodo raccomandato (pacchetto whois su Debian/Ubuntu)
mkpasswd -m yescrypt 'password'
mkpasswd -m sha-512 'password'
# NOTA: il modulo Python "crypt" è stato rimosso in Python 3.13.
# Usare mkpasswd o openssl per generare hash da script.
openssl passwd -6 'password'         # SHA-512 (openssl >= 1.1.1)
```

### Manipolazione Diretta (Emergenza)

```bash
# Rimuovere la password (login senza password — PERICOLOSO, solo emergenza)
sudo passwd -d username

# Bloccare/sbloccare tramite manipolazione diretta
# passwd -l aggiunge '!' davanti all'hash
# passwd -u rimuove il '!'
sudo passwd -l username              # Blocca
sudo passwd -u username              # Sblocca

# Stato password
sudo passwd -S username
# admin P 01/15/2026 0 99999 7 -1
# P = password impostata, L = locked, NP = no password
```

---

## Database Gruppi: /etc/group e /etc/gshadow

### /etc/group — Formato

```
groupname:password:GID:member_list
```

| Campo | Descrizione | Esempio | Note |
|-------|-------------|---------|------|
| `groupname` | Nome del gruppo | `developers` | Max 32 caratteri |
| `password` | Password di gruppo | `x` | `x` = hash in `/etc/gshadow`. Raramente usato — serve per `newgrp` senza essere membro |
| `GID` | Group ID numerico | `2000` | Univoco nel sistema |
| `member_list` | Lista membri | `user1,user2` | Utenti separati da virgola. NON include utenti che hanno questo come gruppo primario (quelli sono in `/etc/passwd`) |

```bash
# Esempi
root:x:0:
sudo:x:27:admin,user1
docker:x:999:admin,deploy
developers:x:2000:admin,mario,lucia
```

### Gruppo Primario vs Supplementari

```
Gruppo primario:      definito in /etc/passwd (campo GID)
                      → usato come GID per i file creati dall'utente
                      → NON appare nella member_list di /etc/group
                      → ogni utente ne ha esattamente uno

Gruppi supplementari: definiti in /etc/group (campo member_list)
                      → l'utente può averne da 0 a NGROUPS_MAX (tipicamente 65536)
                      → determinano permessi aggiuntivi
                      → le modifiche richiedono re-login per avere effetto
```

```bash
# Vedere gruppo primario e supplementari
id admin
# uid=1000(admin) gid=1000(admin) groups=1000(admin),27(sudo),999(docker)
#                 ^^^^^^^^^^^^^^^^                   ^^^^^^^^^^^^^^^^^^^^^^^
#                 gruppo primario                    gruppi supplementari

# Cambiare temporaneamente il gruppo primario (apre una subshell)
newgrp developers
# I file creati in questa subshell avranno GID = developers
touch test_file
ls -l test_file
# -rw-r--r-- 1 admin developers 0 ...
exit                              # Torna al gruppo primario originale
```

### /etc/gshadow — Formato

```
groupname:password_hash:admins:members
```

| Campo | Descrizione | Esempio | Note |
|-------|-------------|---------|------|
| `groupname` | Nome del gruppo | `developers` | Corrisponde a `/etc/group` |
| `password_hash` | Hash password gruppo | `!` | `!` o `!!` = nessuna password. Se impostata, `newgrp` la chiede a chi non è membro |
| `admins` | Amministratori del gruppo | `admin` | Possono aggiungere/rimuovere membri con `gpasswd` senza sudo |
| `members` | Membri del gruppo | `admin,mario` | Duplica `/etc/group`, deve essere coerente |

```bash
# Visualizzare gshadow (richiede root)
sudo cat /etc/gshadow | grep developers
# developers:!:admin:admin,mario,lucia

# Impostare un admin per il gruppo (può gestire membri senza sudo)
sudo gpasswd -A admin developers

# Impostare una password di gruppo (per newgrp senza membership)
sudo gpasswd developers            # Chiede la nuova password
```

---

## Gestione Utenti

### useradd — Creare Utenti

```bash
# Sintassi
useradd [opzioni] username

# Opzioni principali
# -m, --create-home         Crea la home directory (copia da /etc/skel)
# -M, --no-create-home      NON creare home (override del default)
# -d, --home-dir DIR        Home directory custom (default: /home/username)
# -s, --shell SHELL         Shell di login (default: /bin/bash o da /etc/default/useradd)
# -c, --comment COMMENT     Campo GECOS (nome completo)
# -g, --gid GROUP           Gruppo primario (nome o GID)
# -G, --groups GR1,GR2      Gruppi supplementari (separati da virgola)
# -u, --uid UID             UID specifico
# -o, --non-unique          Permette UID duplicato (raro, usare con cautela)
# -e, --expiredate DATE     Data scadenza account (YYYY-MM-DD)
# -f, --inactive DAYS       Giorni inattività dopo scadenza password prima di disabilitazione
# -r, --system              Crea un utente di sistema (UID nel range SYS_UID_MIN-SYS_UID_MAX)
# -k, --skel DIR            Directory skel alternativa (default: /etc/skel)
# -K, --key KEY=VALUE       Override dei default di /etc/login.defs
# -p, --password HASH       Hash password (NON la password in chiaro! Visibile in ps)
# -l, --no-log-init         Non aggiungere a lastlog e faillog
# -b, --base-dir DIR        Directory base per la home (default: /home)
# -D, --defaults            Mostra/modifica i default di useradd

# ESEMPI PRATICI

# Utente standard con home e shell bash
sudo useradd -m -s /bin/bash -c "Mario Rossi" mario
sudo passwd mario                   # Imposta password interattivamente

# Utente con gruppi supplementari e scadenza
sudo useradd -m -s /bin/bash -G sudo,docker -c "Admin User" admin \
  -e 2027-01-01

# Utente di sistema (per servizio/daemon)
sudo useradd -r -s /usr/sbin/nologin -d /var/lib/myapp -c "MyApp Service" myapp

# Utente con UID specifico e home custom
sudo useradd -m -u 2000 -d /opt/developer -s /bin/zsh -c "Dev User" devuser

# Utente con override dei default di login.defs
sudo useradd -m -s /bin/bash -K PASS_MAX_DAYS=60 -K UMASK=027 secureuser

# Alternativa interattiva (Debian/Ubuntu) — crea home, chiede password, più user-friendly
sudo adduser username

# Vedere i default attuali di useradd
useradd -D
# GROUP=100
# HOME=/home
# INACTIVE=-1
# EXPIRE=
# SHELL=/bin/bash
# SKEL=/etc/skel
# CREATE_MAIL_SPOOL=no

# I default sono in /etc/default/useradd
```

### usermod — Modificare Utenti

```bash
# Sintassi
usermod [opzioni] username

# ATTENZIONE CRITICA: -G senza -a SOVRASCRIVE tutti i gruppi supplementari!
# Usare SEMPRE -aG per aggiungere a un gruppo.

# Opzioni principali
# -a, --append             Da usare con -G: aggiunge ai gruppi invece di sovrascrivere
# -G, --groups GR1,GR2     Gruppi supplementari (PERICOLOSO senza -a!)
# -g, --gid GROUP          Cambia gruppo primario
# -s, --shell SHELL        Cambia shell di login
# -l, --login NEW_NAME     Rinomina l'utente (NON rinomina home né gruppo)
# -d, --home DIR           Cambia home directory
# -m, --move-home          Da usare con -d: sposta i file nella nuova home
# -c, --comment COMMENT    Cambia campo GECOS
# -u, --uid UID            Cambia UID
# -o, --non-unique         Permette UID duplicato
# -L, --lock               Blocca password (aggiunge ! davanti all'hash)
# -U, --unlock             Sblocca password (rimuove !)
# -e, --expiredate DATE    Cambia data scadenza account
# -f, --inactive DAYS      Cambia giorni inattività
# -p, --password HASH      Cambia hash password

# ESEMPI PRATICI

# Aggiungere a un gruppo supplementare (SEMPRE con -a!)
sudo usermod -aG docker mario
sudo usermod -aG sudo,docker mario  # Multipli gruppi

# ⚠️  ERRORE COMUNE E PERICOLOSO:
# sudo usermod -G docker mario
# → Rimuove mario da TUTTI gli altri gruppi supplementari (sudo, ecc.)!

# Cambiare shell
sudo usermod -s /bin/zsh mario

# Rinominare utente (attenzione: home e gruppo rimangono con il vecchio nome)
sudo usermod -l mario_new mario_old
sudo usermod -d /home/mario_new -m mario_new   # Rinominare anche la home
sudo groupmod -n mario_new mario_old            # Rinominare anche il gruppo primario

# Bloccare/sbloccare account
sudo usermod -L mario                # Blocca (prefisso ! alla password hash)
sudo usermod -U mario                # Sblocca

# Cambiare UID (poi aggiornare i file di proprietà)
sudo usermod -u 2000 mario
sudo find / -user 1000 -exec chown -h 2000 {} \;   # Aggiornare file con vecchio UID

# Impostare scadenza account
sudo usermod -e 2026-12-31 mario
sudo usermod -e "" mario             # Rimuovere la scadenza
```

### userdel — Eliminare Utenti

```bash
# Sintassi
userdel [opzioni] username

# Opzioni
# -r, --remove          Rimuovi home directory e mail spool
# -f, --force           Forza eliminazione anche se l'utente è loggato
#                       e rimuovi home anche se usata da altri utenti (PERICOLOSO)
# -Z, --selinux-user    Rimuovi mappatura utente SELinux

# Eliminazione standard (mantiene home per archivio)
sudo userdel mario

# Eliminazione completa
sudo userdel -r mario

# Eliminazione forzata (utente ancora connesso — usare con cautela)
sudo userdel -f mario

# Alternativa Debian/Ubuntu (più sicura, chiede conferma)
sudo deluser --remove-home mario

# PROCEDURA CONSIGLIATA per eliminare un utente:
# 1. Verificare processi attivi
ps -u mario
# 2. Terminare la sessione
sudo loginctl terminate-user mario
# 3. Verificare cron job e at job
sudo crontab -l -u mario
# 4. Archiviare la home (opzionale)
sudo tar czf /backup/mario-home-$(date +%Y%m%d).tar.gz /home/mario
# 5. Eliminare
sudo userdel -r mario
# 6. Verificare file orfani nel sistema
sudo find / -nouser -o -nogroup 2>/dev/null
```

### Shell di Login Speciali

```bash
# Shell per utenti di servizio (no login interattivo)
/usr/sbin/nologin                   # Mostra messaggio "This account is currently
                                    # not available." e chiude la connessione
/bin/false                          # Exit immediato con codice 1, nessun messaggio

# /usr/sbin/nologin è preferibile: fornisce un feedback chiaro
# Il messaggio è personalizzabile in /etc/nologin.txt

# Cambiare la propria shell
chsh -s /bin/zsh                    # La nuova shell deve essere in /etc/shells

# Cambiare shell di un altro utente
sudo chsh -s /usr/sbin/nologin serviceuser

# /etc/shells — lista delle shell di login valide
cat /etc/shells
# /bin/sh
# /bin/bash
# /bin/zsh
# /usr/bin/fish
# NOTA: /usr/sbin/nologin e /bin/false NON sono in /etc/shells
# perché non sono shell di login valide per gli utenti normali

# Comandi informativi
id username                         # UID, GID, gruppi
whoami                              # Username corrente
who                                 # Chi è connesso
w                                   # Chi è connesso + cosa fa
last                                # Storico login
lastlog                             # Ultimo login per ogni utente
finger username                     # Info utente (se installato)
getent passwd username              # Cerca in tutti i database (locale + LDAP + SSSD)
```

---

## Gestione Gruppi

### groupadd — Creare Gruppi

```bash
# Sintassi
groupadd [opzioni] groupname

# Opzioni principali
# -g, --gid GID           GID specifico
# -o, --non-unique        Permette GID duplicato
# -r, --system            Crea un gruppo di sistema (GID nel range SYS_GID_MIN-SYS_GID_MAX)
# -K, --key KEY=VALUE     Override dei default di /etc/login.defs
# -f, --force             Esci con successo se il gruppo esiste già (non genera errore)
# -p, --password HASH     Hash password di gruppo

# Esempi
sudo groupadd developers
sudo groupadd -g 2000 devops
sudo groupadd -r myapp-service       # Gruppo di sistema
```

### groupmod — Modificare Gruppi

```bash
# Sintassi
groupmod [opzioni] groupname

# Opzioni
# -n, --new-name NEWNAME    Rinomina il gruppo
# -g, --gid GID             Cambia GID
# -o, --non-unique          Permette GID duplicato
# -p, --password HASH       Cambia hash password gruppo

# Esempi
sudo groupmod -n devops developers     # Rinomina
sudo groupmod -g 2001 devops           # Cambia GID

# Dopo aver cambiato il GID, aggiornare i file:
sudo find / -group 2000 -exec chgrp 2001 {} \;
```

### groupdel — Eliminare Gruppi

```bash
# Sintassi
groupdel [opzioni] groupname

# Opzioni
# -f, --force              Forza eliminazione anche se è gruppo primario di un utente
#                          (PERICOLOSO — lascia l'utente con un GID numerico orfano)

# REGOLA: non si può eliminare un gruppo se è il gruppo primario di un utente
sudo groupdel developers
# groupdel: cannot remove the primary group of user 'mario'
# → Prima cambiare il gruppo primario di mario: sudo usermod -g altrogruppo mario
```

### gpasswd — Gestione Membri Gruppo

```bash
# gpasswd è il comando dedicato alla gestione dei membri di gruppo

# Aggiungere un membro
sudo gpasswd -a mario developers

# Rimuovere un membro
sudo gpasswd -d mario developers

# Impostare la lista completa dei membri (sovrascrive!)
sudo gpasswd -M mario,lucia,paolo developers

# Impostare un amministratore di gruppo (può gestire membri senza sudo)
sudo gpasswd -A admin developers

# Impostare password di gruppo (per newgrp senza membership)
sudo gpasswd developers             # Chiede la nuova password interattivamente

# Rimuovere password di gruppo
sudo gpasswd -r developers

# Equivalente con usermod (solo aggiunta)
sudo usermod -aG developers mario    # -a = APPEND (senza -a, sovrascrive!)
```

### Comandi Informativi sui Gruppi

```bash
# Gruppi di un utente
groups mario                        # developers sudo docker

# Dettagli di un gruppo
getent group developers             # developers:x:2000:mario,lucia

# Tutti i gruppi (primario + supplementari) con ID numerici
id mario
# uid=1001(mario) gid=1001(mario) groups=1001(mario),2000(developers),27(sudo)

# Elencare tutti i gruppi del sistema
getent group | sort

# Trovare gruppi vuoti (nessun membro nella member_list)
awk -F: '$4 == "" {print $1, $3}' /etc/group
```

---

## Password Policy e Aging

### chage — Gestione Aging Password

```bash
# VISUALIZZARE POLICY UTENTE
sudo chage -l mario
# Last password change                           : May 15, 2026
# Password expires                               : Aug 13, 2026
# Password inactive                              : Aug 20, 2026
# Account expires                                : never
# Minimum number of days between password change  : 7
# Maximum number of days between password change  : 90
# Number of days of warning before password expires: 14

# IMPOSTARE POLICY
sudo chage -M 90 mario            # Password scade dopo 90 giorni
sudo chage -m 7 mario             # Minimo 7 giorni tra un cambio e l'altro
sudo chage -W 14 mario            # Avviso 14 giorni prima della scadenza
sudo chage -I 7 mario             # 7 giorni di grazia dopo scadenza password
sudo chage -E 2027-01-01 mario    # Account scade il 01/01/2027
sudo chage -d 0 mario             # Forza cambio password al prossimo login
sudo chage -E -1 mario            # Rimuovi scadenza account
sudo chage -M -1 mario            # Password non scade mai (valore -1)

# IMPOSTAZIONE INTERATTIVA (chiede ogni campo uno per uno)
sudo chage mario
```

### passwd — Gestione Password

```bash
# Cambiare la propria password
passwd

# Cambiare la password di un altro utente (richiede root)
sudo passwd mario

# Bloccare un account (aggiunge ! davanti all'hash in /etc/shadow)
sudo passwd -l mario

# Sbloccare un account
sudo passwd -u mario

# Rimuovere la password (login senza password — PERICOLOSO)
sudo passwd -d mario

# Mostrare lo stato della password
sudo passwd -S mario
# mario P 05/15/2026 7 90 14 7
# Campi: username, stato (P/L/NP), ultimo cambio, min, max, warn, inactive
# P = password set, L = locked, NP = no password

# Forzare scadenza della password (equivale a chage -d 0)
sudo passwd -e mario

# Impostare il numero minimo/massimo di giorni
sudo passwd -n 7 mario             # min days
sudo passwd -x 90 mario            # max days
sudo passwd -w 14 mario            # warning days
sudo passwd -i 7 mario             # inactive days
```

### /etc/login.defs — Default di Sistema

```bash
# /etc/login.defs — configurazione globale per la creazione utenti e policy password
# Letto da useradd, userdel, usermod, passwd, login e altri

# Password aging default per nuovi utenti
PASS_MAX_DAYS   90                  # Scadenza ogni 90 giorni
PASS_MIN_DAYS   7                   # Min 7 giorni tra cambi
PASS_WARN_AGE   14                  # Avviso 14 giorni prima
PASS_MIN_LEN    8                   # Lunghezza minima (ignorato se PAM pwquality attivo)

# Algoritmo di hash
ENCRYPT_METHOD  YESCRYPT            # O SHA512 su sistemi meno recenti
YESCRYPT_COST_FACTOR 5              # Costo computazionale yescrypt (1-11)
# SHA_CRYPT_MIN_ROUNDS 5000        # Per SHA-512
# SHA_CRYPT_MAX_ROUNDS 10000

# UID/GID range
UID_MIN         1000                # Primo UID per utenti normali
UID_MAX         60000
GID_MIN         1000
GID_MAX         60000
SYS_UID_MIN     100                 # Range per utenti di sistema
SYS_UID_MAX     999
SYS_GID_MIN     100
SYS_GID_MAX     999

# Home directory
CREATE_HOME     yes                 # Crea home di default con useradd
UMASK           077                 # Permessi home = 700 (rwx------)
HOME_MODE       0700                # Alternativa a UMASK (più recente)

# Mail
MAIL_DIR        /var/mail           # Directory mail spool
# MAIL_FILE     .mail               # File mail nella home

# Logging
LOG_OK_LOGINS   no                  # Logga anche i login riusciti
FAILLOG_ENAB    yes                 # Abilita faillog

# Varie
USERGROUPS_ENAB yes                 # Crea un gruppo omonimo per ogni utente
DEFAULT_HOME    yes                 # Permetti login anche se la home non esiste
ENV_PATH        PATH=/usr/local/bin:/usr/bin:/bin
ENV_SUPATH      PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

### Complessità Password — pam_pwquality

```bash
# pam_pwquality sostituisce il vecchio pam_cracklib per il controllo della
# complessità delle password. Configurazione in /etc/security/pwquality.conf

# Installazione (se non presente)
sudo apt install libpam-pwquality    # Debian/Ubuntu
sudo dnf install libpwquality        # Fedora/RHEL

# /etc/security/pwquality.conf
minlen = 12                          # Lunghezza minima (default: 8)
dcredit = -1                         # Almeno 1 cifra (valori negativi = richiesti)
ucredit = -1                         # Almeno 1 maiuscola
lcredit = -1                         # Almeno 1 minuscola
ocredit = -1                         # Almeno 1 carattere speciale
minclass = 3                         # Almeno 3 classi diverse (maiuscola, minuscola, cifra, speciale)
maxrepeat = 3                        # Max 3 caratteri uguali consecutivi
maxclassrepeat = 4                   # Max 4 caratteri della stessa classe consecutivi
gecoscheck = 1                       # Rifiuta password che contengono parole del campo GECOS
dictcheck = 1                        # Controlla contro dizionario (cracklib)
usercheck = 1                        # Rifiuta password che contengono il nome utente
enforcing = 1                        # Enforce (0 = solo warning)
enforce_for_root = 1                 # Anche root deve rispettare le regole
retry = 3                            # Tentativi prima di fallire
difok = 5                            # Minimo 5 caratteri diversi dalla vecchia password
maxsequence = 3                      # Max 3 caratteri in sequenza (abc, 123)
badwords = password admin root       # Parole proibite

# La configurazione PAM che attiva pwquality è in /etc/pam.d/common-password:
# password  requisite  pam_pwquality.so retry=3
# password  [success=1 default=ignore]  pam_unix.so obscure use_authtok try_first_pass yescrypt
```

---

## PAM — Pluggable Authentication Modules

PAM è il framework che gestisce autenticazione, autorizzazione, gestione password e configurazione sessione in Linux. Ogni servizio (login, ssh, sudo, su, passwd...) ha il proprio file di configurazione PAM in `/etc/pam.d/`.

### Architettura PAM

```
                    Applicazione (login, sshd, sudo, su...)
                          │
                          ▼
                   Libreria PAM (libpam)
                          │
                          ▼
              File di configurazione (/etc/pam.d/servizio)
                          │
                ┌─────────┼─────────┐
                ▼         ▼         ▼
            modulo1    modulo2    modulo3    ← /lib/x86_64-linux-gnu/security/
            (pam_unix) (pam_deny) (pam_env)
```

### Tipi di Modulo

PAM organizza i moduli in quattro categorie funzionali:

| Tipo | Funzione | Esempio |
|------|----------|---------|
| `auth` | Verifica l'identità dell'utente (password, token, biometria) | `pam_unix.so` verifica la password contro `/etc/shadow` |
| `account` | Verifica se l'account è autorizzato ad accedere (scadenza, orari, restrizioni) | `pam_nologin.so` blocca tutti se `/etc/nologin` esiste |
| `password` | Gestisce il cambio password (complessità, aggiornamento hash) | `pam_pwquality.so` controlla la complessità |
| `session` | Configura l'ambiente della sessione (mount home, limiti, logging) | `pam_limits.so` applica i limiti da `/etc/security/limits.conf` |

### Control Flag

Il control flag determina come il risultato del modulo influenza lo stack:

| Flag | Comportamento | Uso tipico |
|------|---------------|------------|
| `required` | Deve avere successo. In caso di fallimento, lo stack continua ma alla fine fallisce | La maggior parte dei moduli |
| `requisite` | Deve avere successo. In caso di fallimento, lo stack si interrompe IMMEDIATAMENTE | Controllo complessità password |
| `sufficient` | Se ha successo e nessun `required` precedente ha fallito, lo stack si interrompe con successo | Autenticazione alternativa (SSSD) |
| `optional` | Il risultato è ignorato, a meno che sia l'unico modulo nello stack | `pam_motd.so` per il messaggio del giorno |
| `include` | Include un altro file di configurazione PAM | `@include common-auth` |
| `substack` | Come `include` ma un fallimento non si propaga allo stack genitore | Isolamento |

### Sintassi di Configurazione

```
tipo    control_flag    modulo.so    [argomenti]
```

### File di Configurazione Tipici

```bash
# /etc/pam.d/common-auth — autenticazione condivisa da tutti i servizi
auth    [success=2 default=ignore]  pam_unix.so nullok
auth    [success=1 default=ignore]  pam_sss.so use_first_pass
auth    requisite                   pam_deny.so
auth    required                    pam_permit.so
auth    optional                    pam_cap.so
# Logica: prova pam_unix (password locale). Se OK, salta 2 moduli (→ pam_permit).
# Se fallisce, prova pam_sss (SSSD/LDAP). Se OK, salta 1 (→ pam_permit).
# Se entrambi falliscono, pam_deny blocca tutto.

# /etc/pam.d/common-account — controllo autorizzazione
account [success=1 new_authtok_reqd=done default=ignore]  pam_unix.so
account requisite                   pam_deny.so
account required                    pam_permit.so
account sufficient                  pam_localuser.so
account [default=bad success=ok user_unknown=ignore]  pam_sss.so

# /etc/pam.d/common-password — gestione cambio password
password  requisite                 pam_pwquality.so retry=3
password  [success=2 default=ignore]  pam_unix.so obscure use_authtok try_first_pass yescrypt
password  sufficient                pam_sss.so use_authtok
password  requisite                 pam_deny.so
password  required                  pam_permit.so

# /etc/pam.d/common-session — configurazione sessione
session  [default=1]               pam_permit.so
session  requisite                 pam_deny.so
session  required                  pam_permit.so
session  optional                  pam_umask.so
session  required                  pam_unix.so
session  optional                  pam_sss.so
session  optional                  pam_systemd.so
session  optional                  pam_mkhomedir.so umask=0077 skel=/etc/skel
```

### Moduli PAM Comuni

| Modulo | Tipo | Funzione |
|--------|------|----------|
| `pam_unix.so` | auth, account, password, session | Autenticazione standard contro `/etc/shadow` |
| `pam_sss.so` | auth, account, password, session | Autenticazione via SSSD (LDAP/AD) |
| `pam_deny.so` | tutti | Nega sempre l'accesso. Usato come fallback di sicurezza |
| `pam_permit.so` | tutti | Permette sempre. Usato come terminatore dello stack |
| `pam_pwquality.so` | password | Controlla complessità password |
| `pam_faillock.so` | auth, account | Blocca l'account dopo N tentativi falliti |
| `pam_limits.so` | session | Applica limiti da `/etc/security/limits.conf` |
| `pam_mkhomedir.so` | session | Crea automaticamente la home directory al primo login |
| `pam_nologin.so` | auth, account | Blocca login non-root se `/etc/nologin` esiste |
| `pam_securetty.so` | auth | Limita login root ai terminali in `/etc/securetty` |
| `pam_motd.so` | session | Mostra il Message Of The Day |
| `pam_env.so` | auth, session | Imposta variabili d'ambiente da `/etc/environment` e `/etc/security/pam_env.conf` |
| `pam_systemd.so` | session | Registra la sessione con systemd-logind |
| `pam_cap.so` | auth | Assegna capability Linux agli utenti |
| `pam_access.so` | account | Controllo accesso basato su `/etc/security/access.conf` |
| `pam_time.so` | account | Restrizioni di accesso basate su orario (`/etc/security/time.conf`) |
| `pam_tally2.so` | auth, account | Vecchio contatore tentativi falliti (sostituito da `pam_faillock`) |

### pam_faillock — Blocco dopo Tentativi Falliti

```bash
# /etc/security/faillock.conf
deny = 5                            # Blocca dopo 5 tentativi falliti
fail_interval = 900                 # Nell'arco di 15 minuti (900 secondi)
unlock_time = 600                   # Sblocca dopo 10 minuti (0 = sblocco manuale)
even_deny_root = true               # Blocca anche root
root_unlock_time = 60               # Root si sblocca dopo 60 secondi

# In /etc/pam.d/common-auth, aggiungere PRIMA di pam_unix:
auth    required    pam_faillock.so preauth
# e DOPO pam_unix:
auth    [default=die]  pam_faillock.so authfail
auth    sufficient     pam_faillock.so authsucc

# Comandi amministrativi
faillock --user mario                # Vedere lo stato del blocco
faillock --user mario --reset        # Sbloccare manualmente
```

### pam_access — Controllo Accesso

```bash
# /etc/security/access.conf
# Formato: +/-  :  utenti  :  origini

# Permetti solo il gruppo sysadmin da qualsiasi origine
+ : (sysadmin) : ALL

# Nega root su tutti i terminali tranne console
- : root : ALL EXCEPT LOCAL

# Permetti utente specifico solo da rete interna
+ : deploy : 10.0.0.0/8
- : deploy : ALL

# In /etc/pam.d/sshd o common-account:
account  required  pam_access.so accessfile=/etc/security/access.conf
```

### pam_time — Restrizioni Orarie

```bash
# /etc/security/time.conf
# Formato: servizio;terminali;utenti;orari

# Login SSH permesso solo in orario lavorativo (lun-ven 08-18)
sshd;*;*;Wk0800-1800

# Login su console locale sempre permesso per root
login;tty*;root;Al0000-2400

# In /etc/pam.d/sshd:
account  required  pam_time.so
```

### Sintassi Avanzata dei Control Flag

Oltre ai flag semplici (`required`, `requisite`, `sufficient`, `optional`), PAM supporta una sintassi estesa con coppie `value=action` racchiuse tra parentesi quadre. Questa forma offre controllo granulare su cosa accade in base al risultato del modulo.

```bash
# Formato esteso:
# tipo  [value1=action1 value2=action2 ...]  modulo.so  [argomenti]

# Valori di ritorno possibili del modulo:
# success        → autenticazione riuscita
# new_authtok_reqd → nuova password richiesta
# default        → tutti i valori non specificati esplicitamente
# ignore         → ignora il risultato del modulo
# user_unknown   → l'utente non esiste nel database di questo modulo
# auth_err       → errore di autenticazione
# acct_expired   → account scaduto
# perm_denied    → permesso negato

# Azioni possibili:
# ignore   → non influenza il risultato finale
# ok       → se nessun modulo precedente ha fallito, il risultato è OK
# done     → come ok, ma lo stack si interrompe immediatamente (successo)
# bad      → segnala un fallimento
# die      → come bad, ma lo stack si interrompe immediatamente (fallimento)
# reset    → azzera lo stato corrente e riprende la valutazione
# N        → salta i prossimi N moduli nello stack

# ESEMPIO REALE — /etc/pam.d/common-auth su Debian/Ubuntu:
auth  [success=2 default=ignore]  pam_unix.so nullok
auth  [success=1 default=ignore]  pam_sss.so use_first_pass
auth  requisite                   pam_deny.so
auth  required                    pam_permit.so

# Walkthrough dell'esecuzione:
# 1. pam_unix.so tenta l'autenticazione locale (/etc/shadow)
#    → Se SUCCESS: salta 2 moduli → arriva a pam_permit.so → SUCCESSO
#    → Se fallisce (default=ignore): continua al prossimo modulo
# 2. pam_sss.so tenta l'autenticazione SSSD (LDAP/AD)
#    → Se SUCCESS: salta 1 modulo → arriva a pam_permit.so → SUCCESSO
#    → Se fallisce (default=ignore): continua al prossimo modulo
# 3. pam_deny.so → nega SEMPRE (requisite = stop immediato)
# 4. pam_permit.so → raggiunto solo se un modulo precedente ha avuto successo
#    → Segna il risultato finale come OK

# EQUIVALENZA tra flag semplici e sintassi estesa:
# required    = [success=ok new_authtok_reqd=ok default=bad]
# requisite   = [success=ok new_authtok_reqd=ok default=die]
# sufficient  = [success=done new_authtok_reqd=done default=ignore]
# optional    = [success=ok new_authtok_reqd=ok default=ignore]
```

### PAM Multi-Factor Authentication (MFA)

PAM supporta l'autenticazione a più fattori tramite la composizione di moduli nello stack `auth`. Il modulo `pam_google_authenticator` aggiunge TOTP (Time-based One-Time Password) come secondo fattore.

```bash
# Installazione del modulo Google Authenticator PAM
sudo apt install libpam-google-authenticator       # Debian/Ubuntu
sudo dnf install google-authenticator               # Fedora/RHEL

# Configurazione per utente (ogni utente deve eseguirlo)
google-authenticator
# Risponde alle domande:
# - Time-based tokens? → y
# - Update .google_authenticator? → y
# - Disallow reuse? → y
# - Rate limiting? → y
# Genera: QR code, codice segreto, codici di recupero (da salvare offline)

# Configurazione PAM per SSH con MFA
# /etc/pam.d/sshd — aggiungere DOPO pam_unix.so:
auth    required    pam_google_authenticator.so nullok
# nullok: permette il login a chi non ha ancora configurato l'authenticator
# Rimuovere nullok dopo che tutti gli utenti lo hanno configurato

# In /etc/ssh/sshd_config:
# ChallengeResponseAuthentication yes     # Necessario per il prompt TOTP
# AuthenticationMethods keyboard-interactive
# KbdInteractiveAuthentication yes        # Sintassi OpenSSH 8.7+
# Poi: sudo systemctl restart sshd

# MFA condizionale: saltare TOTP per account di servizio
# Usare pam_succeed_if per condizioni
auth  [success=1 default=ignore]  pam_succeed_if.so user ingroup svc-accounts
auth  required                    pam_google_authenticator.so
# Se l'utente è nel gruppo svc-accounts, salta 1 modulo (il TOTP)
# Altrimenti, pam_google_authenticator è required

# pam_succeed_if — condizioni utili:
auth  required  pam_succeed_if.so uid >= 1000       # Solo utenti normali
auth  required  pam_succeed_if.so user notingroup nopasswd  # Escludi un gruppo
```

### pam_faildelay — Ritardo dopo Fallimenti

```bash
# pam_faildelay introduce un ritardo dopo tentativi di autenticazione falliti
# Utile per rallentare attacchi bruteforce locali

# In /etc/pam.d/common-auth o nel file del servizio:
auth  optional  pam_faildelay.so delay=3000000
# delay in microsecondi: 3000000 = 3 secondi
# Il ritardo è randomizzato fino al valore specificato (anti-timing)

# Combinare con pam_faillock per una difesa stratificata:
# 1. pam_faildelay → ritardo dopo ogni fallimento (rallenta bruteforce)
# 2. pam_faillock → blocco dopo N fallimenti (ferma bruteforce)
```

### Creare File di Configurazione PAM Personalizzati

```bash
# Ogni servizio può avere il proprio file in /etc/pam.d/
# Il nome del file corrisponde al nome del servizio PAM

# Esempio: servizio PAM personalizzato per un'applicazione interna
# /etc/pam.d/myapp
auth      required    pam_unix.so
auth      required    pam_google_authenticator.so
account   required    pam_unix.so
account   required    pam_access.so accessfile=/etc/security/myapp-access.conf
session   required    pam_limits.so
session   optional    pam_env.so

# Ordine consigliato nello stack auth:
# 1. pam_faillock.so preauth         (pre-check blocco)
# 2. pam_unix.so / pam_sss.so        (verifica credenziali)
# 3. pam_faillock.so authfail        (registra fallimento)
# 4. pam_google_authenticator.so     (secondo fattore, se MFA)
# 5. pam_faillock.so authsucc        (reset contatore successo)

# REGOLA D'ORO: mantenere SEMPRE una sessione root aperta
# prima di modificare QUALSIASI file in /etc/pam.d/
# Un errore può bloccare TUTTI i login, incluso root.
```

### pamtester — Test Sicuro delle Configurazioni

```bash
# pamtester permette di testare la configurazione PAM senza fare un login reale
sudo apt install pamtester                           # Debian/Ubuntu

# Sintassi: pamtester <servizio> <utente> <operazione>
pamtester login mario authenticate
# Chiede la password e restituisce il risultato PAM

pamtester sshd mario authenticate
pamtester sudo mario authenticate

# Operazioni disponibili:
# authenticate   → testa lo stack auth
# acct_mgmt      → testa lo stack account
# chauthtok      → testa lo stack password
# open_session   → testa lo stack session

# WORKFLOW SICURO per modifiche PAM:
# 1. Aprire una sessione root separata (TTY o altro terminale)
# 2. Modificare il file PAM
# 3. Testare con pamtester
# 4. Testare con un login reale su un secondo terminale
# 5. Solo se tutto funziona, chiudere la sessione root di backup
```

---

## NSSwitch e Name Resolution

### /etc/nsswitch.conf

NSS (Name Service Switch) determina l'ordine in cui il sistema consulta i database per risolvere utenti, gruppi, host e altri servizi di naming. Ogni riga definisce un database e le sue fonti, consultate da sinistra a destra.

```bash
# /etc/nsswitch.conf — configurazione standard (solo locale)
passwd:     files systemd           # Prima /etc/passwd, poi systemd-userdbd
group:      files systemd           # Prima /etc/group, poi systemd
shadow:     files                   # Solo /etc/shadow (sensibile, non via rete)
hosts:      files dns               # Prima /etc/hosts, poi DNS
networks:   files
services:   db files
protocols:  db files
ethers:     db files
rpc:        db files

# Con SSSD (ambiente enterprise con LDAP/AD):
passwd:     files sss               # files prima (utenti locali), poi SSSD (remoti)
group:      files sss
shadow:     files sss
sudoers:    files sss               # sudo rules anche da LDAP/AD
hosts:      files dns
automount:  files sss               # Automount da directory service

# Con LDAP diretto (senza SSSD — meno comune):
passwd:     files ldap
group:      files ldap
shadow:     files ldap

# Status actions (opzionali, dopo ogni fonte)
passwd:     files [NOTFOUND=return] sss
# Se files non trova l'utente, NON consultare sss. Utile se si vuole
# che gli utenti locali mascherino quelli remoti e viceversa.
```

### Fonti Disponibili

| Fonte | Descrizione | Pacchetto |
|-------|-------------|-----------|
| `files` | File locali (`/etc/passwd`, `/etc/group`, ecc.) | glibc (sempre disponibile) |
| `sss` | SSSD (System Security Services Daemon) | `sssd` |
| `ldap` | LDAP diretto (nslcd) | `libnss-ldapd` |
| `systemd` | systemd-userdbd (DynamicUser, nss-systemd) | systemd |
| `dns` | DNS per la risoluzione host | glibc |
| `mdns` | mDNS/Avahi per `.local` | `libnss-mdns` |
| `mymachines` | Container systemd-machined | systemd |
| `resolve` | systemd-resolved | systemd |
| `nis` | NIS/YP (legacy) | `libnss-nis` |
| `winbind` | Samba/Winbind per AD | `libnss-winbind` |

### getent — Interrogare NSS

```bash
# getent interroga TUTTI i database configurati in nsswitch.conf
# (non solo i file locali come grep /etc/passwd)

getent passwd                       # TUTTI gli utenti (locali + remoti)
getent passwd mario                 # Utente specifico
getent passwd 1001                  # Utente per UID
getent group developers             # Gruppo specifico
getent group 2000                   # Gruppo per GID
getent hosts example.com            # Risoluzione host (come farebbe un'applicazione)
getent shadow mario                 # Hash password (richiede root)
getent services ssh                 # Porta servizio

# Se getent passwd mario non restituisce nulla ma grep /etc/passwd sì:
# → nsswitch.conf non include "files" o è configurato male
# Se getent mostra l'utente ma login fallisce:
# → problema in PAM, non in NSS
```

---

## LDAP Client e SSSD

### SSSD (System Security Services Daemon)

SSSD è il metodo moderno per integrare Linux con directory service (LDAP, Active Directory, FreeIPA). Gestisce: autenticazione, autorizzazione, cache offline, sudo centralizzato.

```bash
# Installazione
sudo apt install sssd sssd-ldap sssd-tools      # Debian/Ubuntu
sudo dnf install sssd sssd-ldap sssd-tools       # Fedora/RHEL

# /etc/sssd/sssd.conf — configurazione completa
[sssd]
services = nss, pam, sudo                        # Servizi forniti
domains = example.com                            # Domini configurati
config_file_version = 2                          # Sempre 2

[nss]
filter_groups = root                             # Non risolvere root via SSSD
filter_users = root                              # Non risolvere root via SSSD
reconnection_retries = 3                         # Tentativi di riconnessione

[pam]
offline_credentials_expiration = 7               # Cache credenziali per 7 giorni
offline_failed_login_attempts = 3                # Max 3 tentativi offline
offline_failed_login_delay = 5                   # Delay dopo fallimento offline

[domain/example.com]
# Provider identità e autenticazione
id_provider = ldap                               # Fonte identità: ldap
auth_provider = ldap                             # Autenticazione: ldap
chpass_provider = ldap                           # Cambio password via LDAP
access_provider = ldap                           # Controllo accesso
sudo_provider = ldap                             # Regole sudo da LDAP

# Connessione LDAP
ldap_uri = ldaps://ldap.example.com              # URI del server (ldaps = TLS)
ldap_backup_uri = ldaps://ldap2.example.com      # Server di backup
ldap_search_base = dc=example,dc=com             # Base di ricerca

# TLS
ldap_tls_reqcert = demand                        # Richiede certificato valido
ldap_tls_cacert = /etc/ssl/certs/ca-certificates.crt

# Schema e attributi (per LDAP standard, non AD)
ldap_schema = rfc2307bis                         # O "rfc2307" per NIS schema
ldap_user_search_base = ou=users,dc=example,dc=com
ldap_group_search_base = ou=groups,dc=example,dc=com
ldap_user_object_class = posixAccount
ldap_user_name = uid
ldap_user_uid_number = uidNumber
ldap_user_gid_number = gidNumber
ldap_group_object_class = posixGroup
ldap_group_name = cn
ldap_group_gid_number = gidNumber

# Cache
cache_credentials = true                         # Cache per login offline
entry_cache_timeout = 300                        # Cache entry per 5 minuti
ldap_enumeration_refresh_timeout = 300

# UID/GID mapping (se non definiti in LDAP)
ldap_id_mapping = false                          # true = SSSD genera UID/GID da SID (usato con AD)
min_id = 1000                                    # UID/GID minimo da SSSD
max_id = 60000

# Home directory e shell
fallback_homedir = /home/%u                      # %u = username, %d = domain
default_shell = /bin/bash
override_homedir = /home/%u                      # Forza il formato home

# Sudo
ldap_sudo_search_base = ou=sudoers,dc=example,dc=com

# Permessi file — OBBLIGATORI
# sssd.conf DEVE avere permessi 600, altrimenti sssd si rifiuta di partire
sudo chmod 600 /etc/sssd/sssd.conf
sudo chown root:root /etc/sssd/sssd.conf
sudo systemctl enable --now sssd

# Verificare che SSSD funzioni
sudo sssctl domain-status example.com
getent passwd ldap_user
id ldap_user
```

### nslcd — Alternativa Leggera

```bash
# nslcd è un'alternativa più semplice a SSSD per ambienti solo LDAP
# (senza AD, senza cache offline sofisticata)
sudo apt install libnss-ldapd libpam-ldapd nslcd

# /etc/nslcd.conf
uri ldaps://ldap.example.com
base dc=example,dc=com
ssl on
tls_reqcert demand
tls_cacertfile /etc/ssl/certs/ca-certificates.crt

# nsswitch.conf per nslcd
passwd: files ldap
group:  files ldap
shadow: files ldap

sudo systemctl enable --now nslcd
```

### Comandi Diagnostica SSSD

```bash
# Stato del dominio
sudo sssctl domain-status example.com

# Svuotare la cache (risolvere problemi di dati stale)
sudo sss_cache -E                   # Invalida TUTTA la cache
sudo sss_cache -u mario             # Invalida un utente specifico
sudo sss_cache -g developers        # Invalida un gruppo specifico

# Debug — aumentare il livello di log
# In sssd.conf, nella sezione [domain/...]:
# debug_level = 6                   # 0-9 (6+ è molto verboso)
sudo systemctl restart sssd
sudo journalctl -u sssd -f          # Seguire i log in tempo reale

# Verificare la configurazione
sudo sssctl config-check

# Lista utenti/gruppi dalla cache
sudo sssctl user-show mario
sudo sssctl group-show developers
```

### Troubleshooting Avanzato SSSD

La diagnostica SSSD richiede un approccio strutturato. Le cause più comuni di fallimento sono errori DNS, clock skew Kerberos, mismatch certificati TLS e cache corrotta. SSSD mantiene i propri database di cache in `/var/lib/sss/db/` — comprendere la struttura è essenziale.

```bash
# STRATEGIA DI DEBUG — escalation progressiva del livello di log
# Livello 0-2: solo errori fatali
# Livello 3:   errori e fallimenti operativi (buon punto di partenza)
# Livello 6:   tracciamento dettagliato (primo livello veramente utile per debug)
# Livello 7-9: dump completo inclusi dati sensibili (solo in ambienti di test)

# Impostare debug_level nella sezione del dominio E nelle sezioni dei servizi:
[sssd]
debug_level = 6

[nss]
debug_level = 6

[pam]
debug_level = 6

[domain/example.com]
debug_level = 6

# Dopo la modifica:
sudo systemctl restart sssd
sudo journalctl -u sssd -f --no-pager

# I log sono anche in /var/log/sssd/:
# /var/log/sssd/sssd.log              → processo principale
# /var/log/sssd/sssd_nss.log          → servizio NSS
# /var/log/sssd/sssd_pam.log          → servizio PAM
# /var/log/sssd/sssd_example.com.log  → dominio specifico
```

```bash
# STRUTTURA DELLA CACHE — /var/lib/sss/db/
ls -la /var/lib/sss/db/
# cache_example.com.ldb     → cache utenti/gruppi/sudo (database LDB)
# ccache_EXAMPLE.COM        → cache ticket Kerberos
# sssd.ldb                  → configurazione interna SSSD
# timestamps_example.com.ldb → timestamp di validità cache

# Svuotare la cache selettivamente
sudo sss_cache -u mario                      # Invalida un utente
sudo sss_cache -g developers                 # Invalida un gruppo
sudo sss_cache -E                            # Invalida TUTTO

# Svuotamento completo (quando sss_cache non basta)
sudo systemctl stop sssd
sudo rm -f /var/lib/sss/db/*
sudo systemctl start sssd
# ATTENZIONE: elimina anche le credenziali offline
```

```bash
# FAILURE MODE COMUNI E DIAGNOSTICA

# 1. Clock skew Kerberos — "Clock skew too great"
# Kerberos ha una tolleranza massima di 5 minuti
timedatectl status                           # Verificare sincronizzazione NTP
chronyc tracking                             # O ntpstat su sistemi con ntpd
# Fix: sudo systemctl enable --now chronyd
# Fix: sudo chronyc makestep                 # Forza sincronizzazione immediata

# 2. DNS SRV records mancanti — SSSD non trova il server
dig _ldap._tcp.example.com SRV
dig _kerberos._tcp.example.com SRV
# Se vuoti: configurare ldap_uri manualmente in sssd.conf
# invece di affidarsi alla scoperta DNS automatica

# 3. Mismatch certificato TLS — "Peer's certificate issuer is not recognized"
# Verificare il certificato del server LDAP:
openssl s_client -connect ldap.example.com:636 -showcerts </dev/null 2>&1 | \
  openssl x509 -noout -subject -issuer -dates
# Fix: aggiungere la CA corretta in ldap_tls_cacert di sssd.conf
# Fix: aggiornare il bundle CA di sistema:
sudo update-ca-certificates                  # Debian/Ubuntu
sudo update-ca-trust                         # RHEL/Fedora

# 4. Permessi sssd.conf errati — SSSD non parte
# sssd.conf DEVE essere 0600 e owned da root:root
ls -la /etc/sssd/sssd.conf
# Se errati: sudo chmod 0600 /etc/sssd/sssd.conf && sudo chown root:root /etc/sssd/sssd.conf
```

```bash
# sss_override — sovrascritture locali degli attributi SSSD
# Permette di modificare attributi (nome, shell, home, GID) localmente
# senza toccare il directory service

# Sovrascrivere la shell di un utente LDAP
sudo sss_override user-add mario@example.com --shell=/bin/zsh

# Sovrascrivere la home directory
sudo sss_override user-add mario@example.com --home=/home/custom_mario

# Sovrascrivere il GID
sudo sss_override user-add mario@example.com --gid=2000

# Listare tutte le sovrascritture
sudo sss_override user-list

# Rimuovere una sovrascrittura
sudo sss_override user-del mario@example.com

# Dopo ogni modifica:
sudo sss_cache -E
sudo systemctl restart sssd

# Esportare/importare sovrascritture (migrazione tra server)
sudo sss_override user-export /tmp/overrides.csv
sudo sss_override user-import /tmp/overrides.csv
```

---

## Integrazione Active Directory

### Prerequisiti e Scoperta

```bash
# Installazione pacchetti necessari
sudo apt install sssd realmd adcli packagekit samba-common-bin \
  krb5-user libpam-sss libnss-sss                # Debian/Ubuntu
sudo dnf install sssd realmd adcli samba-common-tools \
  krb5-workstation oddjob oddjob-mkhomedir        # Fedora/RHEL

# Prerequisiti di rete:
# - DNS deve risolvere il dominio AD (i record SRV sono fondamentali)
# - Porte: 389 (LDAP), 636 (LDAPS), 88 (Kerberos), 464 (kpasswd), 3268 (GC)
# - Orario sincronizzato con il DC (Kerberos ha tolleranza max 5 minuti)

# Scoperta dominio
realm discover example.com
# example.com
#   type: kerberos
#   realm-name: EXAMPLE.COM
#   domain-name: example.com
#   configured: no
#   server-software: active-directory
#   client-software: sssd
#   required-package: sssd-tools
#   required-package: sssd
#   required-package: adcli
#   required-package: samba-common-bin
```

### Join al Dominio

```bash
# Join al dominio (crea computer account in AD)
sudo realm join example.com -U administrator
# → Chiede la password dell'amministratore AD

# Join con OU specifica
sudo realm join example.com -U administrator \
  --computer-ou="OU=Linux Servers,DC=example,DC=com"

# Verificare il join
realm list
# example.com
#   type: kerberos
#   realm-name: EXAMPLE.COM
#   domain-name: example.com
#   configured: kerberos-member
#   login-formats: %U@example.com
#   ...

# Testare la risoluzione utente
id administrator@example.com
getent passwd administrator@example.com

# Login SSH con utente AD
ssh mario.rossi@example.com@linux-server

# Kerberos — ottenere un ticket
kinit mario.rossi@EXAMPLE.COM
klist                               # Vedere i ticket attivi
kdestroy                            # Distruggere i ticket
```

### Configurazione Post-Join

```bash
# /etc/sssd/sssd.conf viene creato automaticamente da realm
# Personalizzazioni comuni:

[domain/example.com]
# Login con nome breve invece di user@domain.com
use_fully_qualified_names = false

# Home directory
fallback_homedir = /home/%u
# alternative: /home/%d/%u  (separare per dominio in multi-domain)

# Shell di default
default_shell = /bin/bash

# Controllo accesso — permettere solo gruppi specifici
access_provider = simple
simple_allow_groups = Domain Admins, IT Staff, Linux Users
# simple_allow_users = mario.rossi    # Singoli utenti

# GPO (Group Policy Object) mapping — sperimentale
ad_gpo_access_control = enforcing    # enforcing, permissive, disabled
ad_gpo_map_interactive = +gdm-password   # Mappa servizi a GPO

# Cache
entry_cache_timeout = 300

# Dopo le modifiche:
sudo systemctl restart sssd
sudo sss_cache -E
```

### Controllo Accesso con realm

```bash
# Permettere login a tutti gli utenti del dominio
sudo realm permit --all

# Negare login a tutti
sudo realm deny --all

# Permettere solo gruppi specifici
sudo realm permit -g "Domain Admins" "IT Staff"

# Permettere utenti specifici
sudo realm permit mario.rossi@example.com

# Uscire dal dominio
sudo realm leave example.com
```

---

## Centralizzazione Autenticazione

### FreeIPA (Alternativa Open Source ad Active Directory)

```bash
# FreeIPA fornisce: LDAP + Kerberos + DNS + CA + sudo centralizzato + HBAC
# È l'equivalente open source di Active Directory per ambienti Linux-only

# Installazione client
sudo apt install freeipa-client          # Debian/Ubuntu
sudo dnf install freeipa-client          # Fedora/RHEL

# Enrollment
sudo ipa-client-install --domain=example.com \
  --server=ipa.example.com \
  --realm=EXAMPLE.COM \
  --principal admin \
  --mkhomedir                            # Crea home automaticamente al primo login

# FreeIPA gestisce automaticamente: SSSD, Kerberos, DNS, sudo centralizzato, HBAC

# HBAC (Host-Based Access Control)
# Regole che determinano chi può accedere a quale server con quale servizio
# Gestite centralmente dalla web UI di FreeIPA o via ipa CLI

# Esempio: creare regola HBAC
ipa hbacrule-add allow_developers_on_devservers
ipa hbacrule-add-user allow_developers_on_devservers --groups=developers
ipa hbacrule-add-host allow_developers_on_devservers --hostgroups=dev_servers
ipa hbacrule-add-service allow_developers_on_devservers --hbacsvcs=sshd
```

### sudo Centralizzato con SSSD

```bash
# In sssd.conf, abilitare sudo:
[sssd]
services = nss, pam, sudo

[domain/example.com]
sudo_provider = ldap
ldap_sudo_search_base = ou=sudoers,dc=example,dc=com

# In /etc/nsswitch.conf:
sudoers: files sss
# → Prima consulta /etc/sudoers (locale), poi SSSD (remoto)
# Le regole sudo vengono gestite centralmente nel directory service
# Con FreeIPA: dalla web UI in Policy → Sudo
# Con LDAP: negli oggetti sudoRole nell'OU sudoers

# Verificare le regole sudo dall'SSSD
sudo -l -U mario                     # Mostra le regole sudo di mario
```

### FreeIPA — Trust Cross-Forest con Active Directory

In ambienti misti Linux/Windows, FreeIPA può stabilire un trust cross-forest con Active Directory. Questo permette agli utenti AD di accedere ai sistemi Linux gestiti da FreeIPA senza una seconda coppia di credenziali, mantenendo la gestione delle policy HBAC e sudo nel dominio FreeIPA.

```bash
# PREREQUISITI per il trust cross-forest
# 1. FreeIPA server con DNS integrato
# 2. Forwarder DNS bidirezionale tra IPA e AD
# 3. Orario sincronizzato (max 5 minuti di differenza)
# 4. Porte: 88/464 (Kerberos), 389/636 (LDAP), 135 (MS-RPC), 1024-65535 (RPC)

# Installare il componente trust sul server IPA
sudo dnf install ipa-server-trust-ad

# Configurare il trust
ipa-adtrust-install --add-sids --add-agents
# Genera SID per tutti gli utenti IPA e configura Samba per il trust

# Stabilire il trust
ipa trust-add ad.example.com \
  --type=ad \
  --admin=Administrator \
  --password
# → Crea un trust forest bidirezionale (one-way possibile con --range-type)

# Verificare il trust
ipa trust-show ad.example.com
ipa trustdomain-find ad.example.com

# Risolvere utenti AD dal dominio IPA
id administrator@ad.example.com
getent passwd mario.rossi@ad.example.com
```

```bash
# HBAC AVANZATO — regole granulari per utenti AD e IPA
# FreeIPA permette di creare gruppi esterni che contengono gruppi AD

# Creare un gruppo esterno (contiene il gruppo AD)
ipa group-add ad_developers --external

# Mappare il gruppo AD al gruppo esterno
ipa group-add-member ad_developers --external "AD\\Domain Developers"

# Creare un gruppo POSIX che contiene il gruppo esterno
ipa group-add developers_posix
ipa group-add-member developers_posix --groups=ad_developers

# Ora usare il gruppo POSIX nelle regole HBAC
ipa hbacrule-add allow_ad_devs_ssh
ipa hbacrule-add-user allow_ad_devs_ssh --groups=developers_posix
ipa hbacrule-add-host allow_ad_devs_ssh --hostgroups=dev_servers
ipa hbacrule-add-service allow_ad_devs_ssh --hbacsvcs=sshd

# Regole sudo centralizzate per utenti AD
ipa sudorule-add ad_devs_restart_services
ipa sudorule-add-user ad_devs_restart_services --groups=developers_posix
ipa sudorule-add-host ad_devs_restart_services --hostgroups=dev_servers
ipa sudorule-add-allow-command ad_devs_restart_services \
  --sudocmds="/usr/bin/systemctl restart *"
ipa sudorule-add-runasuser ad_devs_restart_services --users=root
```

```bash
# AUTENTICAZIONE CON SMART CARD E CERTIFICATI
# FreeIPA include una CA integrata e supporta autenticazione via certificato X.509

# Abilitare l'autenticazione con certificato per un utente
ipa user-mod mario --certificate="$(cat mario_cert.pem | base64 -w0)"

# Configurare SSSD per accettare certificati
# In sssd.conf [domain/example.com]:
# pam_cert_auth = true
# pam_cert_db_path = /etc/sssd/pki/sssd_auth_ca_db.pem

# In /etc/pam.d/common-auth, aggiungere:
auth  sufficient  pam_sss.so allow_missing_name try_cert_auth

# Mappatura certificato → utente tramite regole di matching
ipa certmaprule-add email_match \
  --maprule='(userCertificate;binary={cert!bin})' \
  --matchrule='<ISSUER>CN=Example CA' \
  --domain=example.com

# Questo è il flusso usato anche per l'autenticazione con smart card
# (PKCS#11) dove il certificato risiede su una smart card fisica
```

---

## sudo — Deep Dive

### Fondamentali

sudo (superuser do) permette a utenti autorizzati di eseguire comandi come root (o altro utente) secondo le regole definite in `/etc/sudoers`. È il meccanismo primario per l'escalation controllata dei privilegi.

```bash
# Uso base
sudo comando                        # Esegui come root
sudo -u postgres psql                # Esegui come altro utente
sudo -i                              # Shell di login come root
sudo -s                              # Shell non-login come root
sudo -l                              # Mostra le proprie regole sudo
sudo -l -U mario                     # Mostra le regole di mario (richiede root)
sudo -v                              # Rinnova il timestamp (estende la sessione sudo)
sudo -k                              # Invalida il timestamp (richiede password al prossimo uso)
sudo -K                              # Rimuove completamente il timestamp
sudo -b comando                      # Esegui in background
sudo -e /etc/hosts                   # Edita file (usa $EDITOR, sicuro — copia temporanea)
```

### Sintassi /etc/sudoers

```bash
# REGOLA FONDAMENTALE: MAI editare /etc/sudoers direttamente!
# Usare SEMPRE visudo che valida la sintassi prima di salvare.
sudo visudo                          # Edita /etc/sudoers
sudo visudo -f /etc/sudoers.d/devops # Edita un file drop-in

# Formato di una regola sudoers:
# CHI    DOVE=(COME_CHI)    COSA
# user   host=(runas_user)  command

# Esempi:
root    ALL=(ALL:ALL) ALL
# root può eseguire QUALSIASI comando su QUALSIASI host come QUALSIASI utente/gruppo

%sudo   ALL=(ALL:ALL) ALL
# Tutti i membri del gruppo sudo possono fare tutto (% = gruppo)

mario   ALL=(ALL) /usr/bin/apt, /usr/bin/systemctl
# mario può eseguire solo apt e systemctl come root

deploy  ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart myapp
# deploy può riavviare myapp senza inserire la password

%devops ALL=(ALL) NOPASSWD: ALL
# Il gruppo devops può eseguire tutto senza password (da usare con cautela)
```

### Alias in sudoers

```bash
# User_Alias — raggruppare utenti
User_Alias ADMINS = mario, lucia, paolo
User_Alias DEPLOYERS = deploy, ci-runner

# Runas_Alias — utenti target
Runas_Alias WEBUSERS = www-data, nginx
Runas_Alias DBUSERS = postgres, mysql

# Host_Alias — raggruppare host
Host_Alias WEBSERVERS = web1, web2, web3
Host_Alias DBSERVERS = db1, db2

# Cmnd_Alias — raggruppare comandi
Cmnd_Alias SERVICES = /usr/bin/systemctl start *, /usr/bin/systemctl stop *, \
                       /usr/bin/systemctl restart *, /usr/bin/systemctl status *
Cmnd_Alias PACKAGES = /usr/bin/apt update, /usr/bin/apt upgrade, \
                       /usr/bin/apt install *
Cmnd_Alias SHELLS = /bin/bash, /bin/sh, /bin/zsh
Cmnd_Alias NETWORKING = /usr/bin/ip, /usr/sbin/iptables, /usr/sbin/nft

# Usare gli alias nelle regole
ADMINS    ALL=(ALL) ALL
DEPLOYERS WEBSERVERS=(ALL) NOPASSWD: SERVICES
DEPLOYERS DBSERVERS=(DBUSERS) NOPASSWD: /usr/bin/psql

# Negare comandi specifici (! = negazione)
mario     ALL=(ALL) ALL, !SHELLS
# mario può fare tutto TRANNE aprire shell come root
# ATTENZIONE: le negazioni sono facilmente aggirabili (sudo cp /bin/bash /tmp/sh)
# Non sono un meccanismo di sicurezza robusto — usarle come guardrail, non come firewall
```

### Defaults in sudoers

```bash
# Defaults globali
Defaults    env_reset                  # Pulisci l'ambiente (sicurezza)
Defaults    mail_badpass               # Invia mail per password errate
Defaults    secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults    logfile="/var/log/sudo.log" # File di log dedicato
Defaults    log_input                   # Logga stdin
Defaults    log_output                  # Logga stdout/stderr
Defaults    iolog_dir="/var/log/sudo-io" # Directory per I/O log
Defaults    passwd_tries=3             # Tentativi password
Defaults    passwd_timeout=5           # Timeout prompt password (minuti)
Defaults    timestamp_timeout=15       # Durata sessione sudo (minuti, 0 = chiedi sempre)
Defaults    insults                    # Messaggi sarcastici per password errate
Defaults    requiretty                 # Richiedi un terminale (blocca script remoti)
Defaults    use_pty                    # Usa un pseudo-terminale

# Defaults per utente specifico
Defaults:deploy  !requiretty           # deploy non richiede terminale (per CI/CD)
Defaults:deploy  timestamp_timeout=0   # Chiedi sempre la password

# Defaults per comando
Defaults!/usr/bin/apt  log_output      # Logga output di apt

# Variabili d'ambiente da preservare
Defaults    env_keep += "LANG LC_ALL EDITOR VISUAL"
Defaults    env_keep += "HTTP_PROXY HTTPS_PROXY NO_PROXY"
```

### Directory /etc/sudoers.d/

```bash
# Best practice: usare file drop-in in /etc/sudoers.d/ invece di
# modificare /etc/sudoers direttamente

# /etc/sudoers deve contenere questa riga (solitamente già presente):
# @includedir /etc/sudoers.d
# NOTA: @includedir è la sintassi moderna; #includedir è quella legacy (il # NON è un commento qui)

# Creare file drop-in
sudo visudo -f /etc/sudoers.d/10-admins
# ADMINS = mario, lucia
# ADMINS ALL=(ALL) ALL

sudo visudo -f /etc/sudoers.d/20-deploy
# deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart myapp

sudo visudo -f /etc/sudoers.d/90-monitoring
# nagios ALL=(ALL) NOPASSWD: /usr/lib/nagios/plugins/*

# Convenzione di naming: prefisso numerico per controllare l'ordine di caricamento
# I file NON devono contenere "." o "~" nel nome (vengono ignorati!)
# Permessi: 440 (r--r-----)
```

### Logging e Auditing sudo

```bash
# Log standard — tutti i comandi sudo in auth.log / secure
sudo grep 'sudo' /var/log/auth.log       # Debian/Ubuntu
sudo grep 'sudo' /var/log/secure          # RHEL/CentOS
sudo journalctl -t sudo                   # Con systemd

# Formato tipico del log:
# May 22 10:15:30 server sudo: mario : TTY=pts/0 ; PWD=/home/mario ;
#   USER=root ; COMMAND=/usr/bin/apt update

# Log dedicato
# In sudoers: Defaults logfile="/var/log/sudo.log"

# I/O logging (registra input/output completo)
# In sudoers:
# Defaults log_input, log_output
# Defaults iolog_dir="/var/log/sudo-io/%{user}"
# Replay:
sudo sudoreplay -l                        # Lista sessioni
sudo sudoreplay -l user mario             # Sessioni di mario
sudo sudoreplay <session_id>              # Replay di una sessione

# Reportistica
sudo grep 'COMMAND' /var/log/auth.log | awk '{print $6, $NF}' | sort | uniq -c | sort -rn
```

### Hardening sudo — Checklist di Sicurezza

sudo è un binario SUID — la superficie d'attacco è intrinsecamente ampia. Un hardening sistematico riduce il rischio di privilege escalation e movimenti laterali.

```bash
# CHECKLIST HARDENING SUDO

# 1. Pulire l'ambiente — impedire l'iniezione di variabili
Defaults    env_reset                         # Azzera tutte le variabili d'ambiente
Defaults    env_file="/etc/environment"        # Carica solo da file controllato
Defaults    env_keep -= "HOME"                 # Non preservare HOME dell'utente chiamante
Defaults    secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# 2. Isolamento terminale — prevenire TTY hijacking
Defaults    requiretty                        # Richiede un terminale (blocca esecuzione remota)
Defaults    use_pty                           # Esegui in uno pseudo-terminale separato
# use_pty impedisce a processi figli di intercettare il terminale genitore

# 3. Logging completo
Defaults    logfile="/var/log/sudo.log"
Defaults    log_input, log_output
Defaults    iolog_dir="/var/log/sudo-io/%{user}"
Defaults    log_year, log_host                # Includi anno e hostname nel log
Defaults    syslog=auth                       # Invia anche a syslog

# 4. Timeout aggressivi
Defaults    timestamp_timeout=5               # Sessione sudo dura 5 minuti (non 15)
Defaults    passwd_timeout=2                  # 2 minuti per inserire la password
Defaults    passwd_tries=3                    # Max 3 tentativi password

# 5. Limitare l'escalation
Defaults    target_session_attrs="*"
Defaults    !root_sudo                        # root non può usare sudo (controverso, valutare)
Defaults    runas_default=root                # Default esplicito

# 6. Digest verification — comandi con checksum
# Verificare che il binario eseguito sia quello atteso (anti-PATH injection)
mario ALL=(root) sha256:b5bb9d8014a0f9b1d61e21e796d78dcc... /usr/bin/systemctl restart nginx
# Il comando viene eseguito solo se l'hash SHA-256 del binario corrisponde

# Come calcolare il digest:
sha256sum /usr/bin/systemctl
# Inserire l'output nel sudoers con prefisso sha256:

# 7. Limitare i comandi con argomenti precisi
deploy ALL=(root) NOPASSWD: /usr/bin/systemctl restart nginx
# NON usare: /usr/bin/systemctl *    ← troppo permissivo
# NON usare: /usr/bin/systemctl restart *  ← ancora troppo ampio

# 8. Negare shell e editor (guardrail, non sicurezza assoluta)
Cmnd_Alias DANGER = /bin/bash, /bin/sh, /bin/zsh, /usr/bin/vi, \
                     /usr/bin/vim, /usr/bin/nano, /usr/bin/less, \
                     /usr/bin/more, /usr/bin/env, /usr/bin/python3
deploy ALL=(ALL) ALL, !DANGER
# NOTA: facilmente aggirabile (sudo cp /bin/bash /tmp/x && sudo /tmp/x)
# Usare whitelist di comandi specifici piuttosto che blacklist
```

### run0 — Alternativa systemd a sudo (systemd 256+)

A partire da systemd 256, `run0` è una nuova interfaccia per l'esecuzione di comandi privilegiati. A differenza di sudo, `run0` non è un binario SUID — non necessita di bit setuid, eliminando un'intera classe di vulnerabilità. Internamente, `run0` è un link simbolico a `systemd-run` che ne modifica il comportamento predefinito.

```bash
# Architettura di run0:
#   1. L'utente invoca run0
#   2. run0 invia una richiesta al service manager di sistema (PID 1)
#   3. Il service manager consulta polkit per l'autorizzazione
#   4. polkit chiede l'autenticazione all'utente (via agente TTY o GUI)
#   5. Se autorizzato, il service manager avvia il comando in uno scope transient
#   6. run0 alloca un nuovo PTY e trasferisce I/O tra il PTY originale e quello nuovo

# Vantaggi rispetto a sudo:
# - Nessun binario SUID nel sistema
# - L'autorizzazione passa per polkit (framework dedicato)
# - Il comando gira in un cgroup scope separato (isolamento)
# - L'ambiente è completamente pulito per default
# - Il PTY separato previene TTY hijacking

# Uso base
run0 comando                         # Equivale a sudo comando
run0 -u postgres psql                # Esegui come altro utente
run0 --background apt update         # Esegui in background

# Shell interattiva come root
run0 bash                            # Shell root in PTY separato

# Specificare una unit description (visibile in systemd-cgls)
run0 --description="Deploy nginx" systemctl restart nginx

# Proprietà aggiuntive del servizio transient
run0 --property=MemoryMax=512M comando    # Limita memoria
run0 --property=CPUQuota=50% comando      # Limita CPU

# run0 colora il terminale per indicare che si opera come root:
# sfondo leggermente rosato come promemoria visivo

# Configurazione polkit per run0
# /etc/polkit-1/rules.d/50-run0-devops.rules
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.systemd1.manage-units" &&
        subject.isInGroup("devops") &&
        subject.active && subject.local) {
        return polkit.Result.AUTH_SELF;
    }
});

# REQUISITI:
# - systemd >= 256 (Fedora 41+, Ubuntu 24.10+, Debian trixie/sid)
# - polkit configurato con regole appropriate
# - Agente polkit disponibile (pkttyagent per TTY, gnome-polkit-agent per GUI)

# Verificare la versione di systemd
systemctl --version | head -1
```

### doas — Alternativa Minimalista da OpenBSD

`doas` è l'alternativa a sudo creata per OpenBSD da Ted Unangst. La sua filosofia è la semplicità radicale: un file di configurazione lineare, una codebase minimale e una superficie d'attacco ridotta.

```bash
# Installazione
sudo apt install doas                # Debian/Ubuntu (opendoas)
sudo dnf install doas                # Fedora/RHEL

# /etc/doas.conf — configurazione
# Sintassi: permit|deny [options] identity [as target] [cmd command [args ...]]

# Permettere a un utente di eseguire come root
permit mario

# Permettere senza password
permit nopass mario

# Permettere solo comandi specifici
permit mario cmd /usr/bin/apt
permit mario cmd /usr/bin/systemctl args restart nginx

# Persistere l'autenticazione (simile a timestamp_timeout di sudo)
permit persist mario

# Mantenere variabili d'ambiente
permit setenv { PATH HOME EDITOR } mario

# Negare l'esecuzione di shell
deny mario cmd /bin/sh
deny mario cmd /bin/bash

# Permettere a un gruppo intero
permit :wheel
permit nopass :deploy cmd /usr/bin/systemctl args restart myapp

# Eseguire come altro utente
permit mario as postgres cmd /usr/bin/psql

# Uso
doas comando                         # Come sudo comando
doas -u postgres psql                # Come sudo -u postgres psql
doas -s                              # Shell root

# CONFRONTO sudo vs doas vs run0:
# ┌─────────────┬──────────────┬──────────────┬──────────────┐
# │             │ sudo         │ doas         │ run0         │
# ├─────────────┼──────────────┼──────────────┼──────────────┤
# │ Binario SUID│ Sì           │ Sì           │ No           │
# │ Codebase    │ ~200K LOC    │ ~1K LOC      │ systemd-run  │
# │ Config      │ sudoers      │ doas.conf    │ polkit rules │
# │ CVE storici │ Numerosi     │ Pochi        │ Nessuno (*)  │
# │ Logging     │ Completo     │ Minimale     │ journald     │
# │ I/O replay  │ Sì           │ No           │ No           │
# │ Alias       │ Sì           │ No           │ No           │
# │ LDAP/AD     │ Sì (SSSD)    │ No           │ No           │
# └─────────────┴──────────────┴──────────────┴──────────────┘
# (*) run0 è nuovo; le future CVE dipenderanno da polkit e systemd

# RACCOMANDAZIONE:
# - Enterprise con LDAP/AD: sudo (unico con integrazione directory)
# - Server standalone, bassa complessità: doas (meno superficie d'attacco)
# - Sistemi con systemd 256+, forward-looking: run0 (nessun SUID)
# - Defense in depth: sudo hardened + polkit per le operazioni desktop
```

---

## polkit — Authorization Framework

polkit (precedentemente PolicyKit) è il framework di autorizzazione usato da systemd, D-Bus e molte applicazioni desktop per controllare l'accesso a operazioni privilegiate senza dare accesso root completo.

### Architettura

```
Applicazione (es. gnome-disks, systemctl, NetworkManager)
      │
      ▼
Agente polkit (richiede autenticazione all'utente via GUI o TTY)
      │
      ▼
polkitd (demone) ← consulta:
      │              - /usr/share/polkit-1/actions/*.policy   (azioni definite)
      │              - /etc/polkit-1/rules.d/*.rules          (regole locali)
      │              - /usr/share/polkit-1/rules.d/*.rules    (regole di sistema)
      ▼
Decisione: yes | no | auth_self | auth_admin | auth_self_keep | auth_admin_keep
```

### Concetti Chiave

```
Action:    Un'operazione identificata da un ID (es. org.freedesktop.systemd1.manage-units)
Subject:   Chi richiede l'azione (utente, sessione, processo)
Result:    yes (permesso), no (negato), auth_self (chiedi password utente),
           auth_admin (chiedi password admin), *_keep (ricorda per la sessione)
```

### File Policy — Definizione Azioni

```xml
<!-- /usr/share/polkit-1/actions/org.freedesktop.systemd1.policy -->
<!-- Questi file DEFINISCONO le azioni disponibili e i default -->
<?xml version="1.0" encoding="UTF-8"?>
<policyconfig>
  <action id="org.freedesktop.systemd1.manage-units">
    <description>Manage system services</description>
    <message>Authentication is required to manage system services.</message>
    <defaults>
      <allow_any>auth_admin</allow_any>
      <allow_inactive>auth_admin</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
  </action>
</policyconfig>
```

### File Rules — Personalizzazione

```javascript
// /etc/polkit-1/rules.d/10-allow-devops-systemctl.rules
// I file .rules usano JavaScript per logica condizionale
// Eseguiti in ordine alfabetico; il primo match vince

polkit.addRule(function(action, subject) {
    // Permettere ai membri di "devops" di gestire i servizi systemd
    if (action.id == "org.freedesktop.systemd1.manage-units" &&
        subject.isInGroup("devops")) {
        return polkit.Result.YES;
    }
});

// Permettere a utenti specifici di montare dischi senza password
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.udisks2.filesystem-mount-system" &&
        subject.user == "mario") {
        return polkit.Result.YES;
    }
});

// Log di tutte le decisioni polkit
polkit.addRule(function(action, subject) {
    polkit.log("action=" + action.id + " user=" + subject.user);
    // Non restituire nulla = non influenzare la decisione
});
```

### pkexec — Eseguire Comandi con polkit

```bash
# pkexec è l'equivalente di sudo ma basato su polkit
pkexec /usr/bin/apt update           # Chiede autenticazione via polkit

# Per applicazioni grafiche
pkexec gedit /etc/hosts

# pkexec ha bisogno di un file .policy corrispondente per funzionare.
# Per comandi arbitrari, sudo è più pratico.
# polkit eccelle per autorizzazioni granulari di servizi D-Bus.

# Diagnostica polkit
pkaction                             # Lista tutte le azioni polkit definite
pkaction --verbose --action-id org.freedesktop.systemd1.manage-units
pkcheck --action-id org.freedesktop.systemd1.manage-units --process $$
```

### Hardening e Sicurezza polkit

polkit ha una storia di vulnerabilità critiche. La comprensione delle CVE passate e delle mitigazioni è essenziale per un hardening efficace.

```bash
# CVE RILEVANTI — lezioni apprese

# CVE-2021-4034 (PwnKit) — CVSS 7.8
# Vulnerabilità in pkexec presente da oltre 12 anni. Un attacco locale poteva
# ottenere root tramite una manipolazione degli argomenti (argc=0).
# Impatto: qualsiasi utente locale poteva diventare root.
# Fix: aggiornare polkit. Mitigazione temporanea:
# chmod 0755 /usr/bin/pkexec    (rimuove il bit SUID)
# NOTA: nelle versioni recenti di polkit, il bit SUID su pkexec è stato rimosso.
# L'autorizzazione passa ora attraverso un servizio IPC socket-activated.

# CVE-2021-3560 — CVSS 7.8
# Race condition nell'elaborazione delle richieste D-Bus.
# Un attaccante poteva creare un account amministratore senza autenticazione
# inviando una richiesta D-Bus e terminandola a metà.
# Fix: aggiornare polkit >= 0.120.

# CVE-2025-7519 — CVSS 7.1
# Out-of-bounds write nell'elaborazione di file XML policy con 32 o più
# elementi annidati. Può causare corruzione di memoria, crash o code execution.
# Impatto: attaccante locale senza privilegi.
# Fix: applicare le patch distribuite dai vendor (upstream 0.126 non ancora patchato).
# Mitigazione: verificare che i file .policy in /usr/share/polkit-1/actions/
# non contengano strutture XML profondamente annidate da fonti non attendibili.
```

```bash
# HARDENING polkit — best practices operative

# 1. Verificare che pkexec non abbia SUID su sistemi moderni
ls -la /usr/bin/pkexec
# Su polkit 122+ con systemd, il SUID non è più necessario
# Se presente: coordinare con il team per la rimozione

# 2. Limitare le regole JavaScript — principio del minimo privilegio
# /etc/polkit-1/rules.d/ — solo file strettamente necessari
# Ogni regola deve avere una giustificazione documentata
# Auditare periodicamente:
ls -la /etc/polkit-1/rules.d/
ls -la /usr/share/polkit-1/rules.d/

# 3. Regole con restrizioni orarie e di sessione
# /etc/polkit-1/rules.d/20-time-restricted.rules
polkit.addRule(function(action, subject) {
    var now = new Date();
    var hour = now.getHours();
    // Operazioni systemd solo in orario lavorativo (8-18)
    if (action.id.indexOf("org.freedesktop.systemd1") === 0 &&
        (hour < 8 || hour >= 18) &&
        !subject.isInGroup("oncall")) {
        polkit.log("DENIED outside hours: " + action.id +
                   " user=" + subject.user + " hour=" + hour);
        return polkit.Result.NO;
    }
});

# 4. Logging di tutte le decisioni polkit (audit trail)
# /etc/polkit-1/rules.d/00-log-all.rules
polkit.addRule(function(action, subject) {
    polkit.log("polkit: action=" + action.id +
               " user=" + subject.user +
               " active=" + subject.active +
               " local=" + subject.local);
    // Non restituire nulla = non influenza la decisione
});
# I log finiscono in /var/log/auth.log o journalctl -t polkitd

# 5. Negare esplicitamente operazioni non necessarie
# /etc/polkit-1/rules.d/90-deny-dangerous.rules
polkit.addRule(function(action, subject) {
    var dangerous = [
        "org.freedesktop.login1.power-off",
        "org.freedesktop.login1.reboot",
        "org.freedesktop.login1.halt"
    ];
    if (dangerous.indexOf(action.id) >= 0 &&
        !subject.isInGroup("sysadmin")) {
        return polkit.Result.NO;
    }
});
```

---

## User Namespaces e Container Rootless

I user namespace del kernel Linux permettono di mappare UID/GID all'interno di un namespace separato, consentendo processi che sono "root" nel namespace ma unprivileged nel host.

### Concetti Base

```bash
# Verificare se i user namespace unprivileged sono abilitati
sysctl kernel.unprivileged_userns_clone
# 1 = abilitati (default su Ubuntu, Debian)
# 0 = disabilitati (alcune distro conservative)

# Abilitare (se necessario)
sudo sysctl -w kernel.unprivileged_userns_clone=1
# Persistente in /etc/sysctl.d/99-userns.conf:
# kernel.unprivileged_userns_clone = 1

# Creare un user namespace manualmente
unshare --user --map-root-user bash
# Dentro il namespace: UID 0 (root), ma nel host rimane l'UID originale
id                                   # uid=0(root) gid=0(root)
# Ma: touch /root/test → Permission denied (non è il vero root)
exit
```

### /etc/subuid e /etc/subgid

Per container rootless (Podman, Docker rootless), servono range di UID/GID subordinati:

```bash
# /etc/subuid — range di UID subordinati
# formato: username:start_uid:count
mario:100000:65536
lucia:165536:65536

# /etc/subgid — range di GID subordinati (stessa sintassi)
mario:100000:65536
lucia:165536:65536

# Significato: mario può usare gli UID da 100000 a 165535 (65536 UID)
# all'interno dei suoi container rootless

# Creare le entry (se non esistono)
sudo usermod --add-subuids 100000-165535 mario
sudo usermod --add-subgids 100000-165535 mario

# Oppure manualmente con:
echo "mario:100000:65536" | sudo tee -a /etc/subuid
echo "mario:100000:65536" | sudo tee -a /etc/subgid

# Verificare
grep mario /etc/subuid /etc/subgid
```

### Podman Rootless

```bash
# Podman è progettato per container rootless fin dall'inizio
# Richiede: user namespace abilitati + subuid/subgid configurati

# Installare podman
sudo apt install podman

# Verificare la configurazione (come utente normale, NON root)
podman info | grep -A5 idMappings
# uidmap: [{0 1000 1}, {1 100000 65536}]
# → UID 0 nel container = UID 1000 nel host (l'utente corrente)
# → UID 1-65536 nel container = UID 100000-165536 nel host

podman unshare cat /proc/self/uid_map
# 0       1000          1
# 1       100000        65536

# Eseguire un container rootless
podman run --rm -it alpine id
# uid=0(root) gid=0(root)   ← root nel container, non nel host!
```

### Docker Rootless

```bash
# Docker rootless mode richiede configurazione aggiuntiva
# rispetto a Podman (che è rootless by default)

# Prerequisiti
sudo apt install docker-ce uidmap dbus-user-session

# Installare Docker rootless
dockerd-rootless-setuptool.sh install

# Impostare variabili d'ambiente (~/.bashrc)
export PATH=/usr/bin:$PATH
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock

# Verificare
docker context use rootless
docker run --rm hello-world
```

### Sicurezza dei User Namespaces — Avvertenze Critiche

I user namespaces sono uno strumento potente per l'isolamento, ma non sono un confine di sicurezza assoluto. Il loro abuso ha facilitato decine di CVE del kernel tra il 2020 e il 2025.

```bash
# IL PROBLEMA: superficie d'attacco ampliata
# I user namespace unprivileged permettono a qualsiasi utente di esporre
# interfacce kernel normalmente riservate a root (netfilter, overlayfs, ecc.)
# Statistiche 2020-2025:
# - 40+ CVE del kernel dove i user namespace hanno abilitato l'exploit
# - 43% concentrati in netfilter/nf_tables
# - Il resto distribuito tra overlayfs, networking stack e altri sottosistemi

# QUALYS 2025 — bypass delle restrizioni Ubuntu
# Qualys ha dimostrato tre metodi per aggirare le restrizioni di Ubuntu
# sugli unprivileged user namespace, ottenendo piene capability amministrative.
# Colpisce Ubuntu 24.04+ con AppArmor namespace restriction.

# MITIGAZIONI

# 1. Disabilitare gli unprivileged user namespace se non servono
sudo sysctl -w kernel.unprivileged_userns_clone=0
# Persistente:
echo "kernel.unprivileged_userns_clone = 0" | sudo tee /etc/sysctl.d/90-no-userns.conf

# ATTENZIONE: questo rompe i container rootless, browsers sandboxed (Chrome/Firefox),
# Flatpak, e altre applicazioni che dipendono da user namespace

# 2. AppArmor restriction (Ubuntu 24.04+)
# Ubuntu restringe i user namespace con profili AppArmor
# Il parametro kernel:
sudo sysctl kernel.apparmor_restrict_unprivileged_userns
# 1 = ristretto (default su Ubuntu 24.04+)
# Le applicazioni che necessitano di user namespace devono avere un profilo
# AppArmor che lo permette esplicitamente

# 3. Seccomp-based restriction (alternativa)
# Filtrare le syscall unshare/clone con flag CLONE_NEWUSER
# Usato da systemd con RestrictNamespaces= nelle unit dei servizi

# 4. Kubernetes 1.33+ — user namespace per i Pod
# A partire da Kubernetes 1.33, il supporto user namespace è GA (stabile)
# Ogni Pod può mappare UID/GID in un namespace dedicato
# Configurazione nel PodSpec:
# spec:
#   hostUsers: false          # Abilita user namespace per il Pod
# Il kubelet mappa automaticamente gli UID del Pod a range non privilegiati sull'host

# 5. Monitoraggio — rilevare abuso di user namespace
# Auditare la creazione di user namespace:
sudo auditctl -a always,exit -F arch=b64 -S clone -S clone3 -S unshare \
  -F a0\&0x10000000 -k userns_create
# Dove 0x10000000 = CLONE_NEWUSER

sudo ausearch -k userns_create --interpret
```

---

## systemd-homed — Home Directory Moderne

`systemd-homed` è un servizio introdotto in systemd 245 per la gestione moderna delle home directory. Ogni utente diventa un'entità autocontenuta: le informazioni dell'account e la home directory cifrata sono raggruppate in un singolo file o directory che il sistema monta solo quando necessario.

### Architettura e Concetti

```
┌──────────────────────────────────────────────────────────────────┐
│                    systemd-homed                                  │
│                         │                                         │
│    ┌────────────────────┼────────────────────┐                   │
│    ▼                    ▼                    ▼                   │
│  JSON User          Storage              Cifratura              │
│  Record             Backend              Backend                │
│  (~/.identity)                                                   │
│                    ┌─────────┐          ┌─────────┐             │
│                    │directory│          │  nessuna │             │
│                    │ luks    │          │  fscrypt │             │
│                    │ subvol  │          │  LUKS2   │             │
│                    │ fscrypt │          └─────────┘             │
│                    │ cifs    │                                    │
│                    └─────────┘                                   │
│                                                                  │
│    Chiave: password utente / FIDO2 / PKCS#11 / recovery key     │
└──────────────────────────────────────────────────────────────────┘

# Differenza fondamentale rispetto alla gestione tradizionale:
# Tradizionale: /etc/passwd + /etc/shadow + /home/user (separati)
# systemd-homed: JSON User Record + home cifrata (tutto in un pacchetto)
#
# L'utente NON appare in /etc/passwd (gestito da nss-systemd)
# La home è montata al login e smontata al logout
```

### Meccanismi di Storage

| Storage | File/Directory | Cifratura | Portabilità | Uso consigliato |
|---------|---------------|-----------|-------------|-----------------|
| `directory` | `/home/user` (dir normale) | Nessuna | Bassa | Test, sviluppo |
| `luks` | `/home/user.home` (immagine) | LUKS2 + ext4/btrfs/xfs | Alta | Laptop, workstation |
| `fscrypt` | `/home/user` (dir cifrata) | fscrypt kernel | Media | Server, filesystem esistente |
| `subvolume` | Subvolume btrfs | Opzionale (fscrypt) | Media | Sistemi btrfs |
| `cifs` | Share di rete CIFS | Dipende dal server | Alta | Ambienti enterprise |

### homectl — Gestione Utenti con systemd-homed

```bash
# PREREQUISITI
# systemd >= 245 (idealmente >= 254 per funzionalità mature)
# Il servizio systemd-homed deve essere abilitato:
sudo systemctl enable --now systemd-homed

# CREARE UTENTI

# Utente con home directory cifrata LUKS2
homectl create mario --storage=luks --shell=/bin/bash
# Chiede la password interattivamente
# Crea: /home/mario.home (immagine LUKS2, filesystem ext4 interno)
# Dimensione default: 256M-32G (cresce automaticamente se possibile)

# Utente con LUKS2 e filesystem btrfs, dimensione esplicita
homectl create lucia --storage=luks --fs-type=btrfs --disk-size=10G

# Utente con cifratura fscrypt (più leggero, usa il filesystem host)
homectl create paolo --storage=fscrypt

# Utente con autenticazione FIDO2 (chiave di sicurezza hardware)
homectl create admin --storage=luks --fido2-device=auto

# Utente con recovery key (codice di emergenza stampabile)
homectl create admin --storage=luks --recovery-key=yes
# Genera un codice di recupero da conservare offline

# Utente con directory semplice (senza cifratura)
homectl create testuser --storage=directory

# ISPEZIONARE UTENTI
homectl inspect mario
# Mostra: JSON User Record completo con storage type, UID, GID,
# dimensione disco, stato di cifratura, ultimo login, ecc.

homectl list
# Lista tutti gli utenti gestiti da systemd-homed

# MODIFICARE UTENTI
homectl update mario --shell=/bin/zsh           # Cambia shell
homectl update mario --real-name="Mario Rossi"  # Cambia nome completo
homectl update mario --disk-size=20G            # Ridimensiona (solo LUKS)
homectl update mario --enforce-password-policy=true

# CAMBIARE PASSWORD
homectl passwd mario
# Importante: per LUKS, la password è anche la chiave di cifratura
# Cambiare password = re-cifrare la master key del volume

# ATTIVARE/DISATTIVARE (montare/smontare la home)
homectl activate mario                          # Monta la home (chiede password)
homectl deactivate mario                        # Smonta la home (dati inaccessibili)

# RIMUOVERE UTENTE
homectl remove mario                            # Elimina utente E la home cifrata

# BLOCCO/SBLOCCO (sospensione)
homectl lock mario                              # Smonta la home (es. sospensione sistema)
homectl unlock mario                            # Rimonta (chiede password)
```

### Portabilità delle Home Directory

```bash
# IL VANTAGGIO CHIAVE di systemd-homed con LUKS:
# La home è un singolo file immagine, portabile tra macchine

# Workflow di portabilità:
# 1. Sull'host sorgente — copiare l'immagine
homectl deactivate mario                         # Smonta la home
cp /home/mario.home /media/usb/mario.home        # Copia su USB

# 2. Sull'host destinazione — importare
cp /media/usb/mario.home /home/mario.home
# Il JSON User Record è DENTRO l'immagine (~/.identity)
# systemd-homed lo rileva automaticamente al prossimo login

# 3. Oppure su chiavetta USB come home portabile
homectl create mario --storage=luks --image-path=/media/usb/mario.home
# L'utente può portare la sua home su qualsiasi macchina con systemd-homed

# NOTA: il JSON User Record contiene una firma crittografica
# per garantire l'autenticità dei metadati
```

### Integrazione PAM e Limitazioni

```bash
# PAM — systemd-homed si integra tramite pam_systemd_home.so
# Configurazione automatica in /etc/pam.d/ durante l'installazione

# Riga tipica in /etc/pam.d/system-auth o common-auth:
auth      sufficient  pam_systemd_home.so
account   sufficient  pam_systemd_home.so
password  sufficient  pam_systemd_home.so
session   optional    pam_systemd_home.so

# pam_systemd_home gestisce:
# - Autenticazione (verifica la password contro il volume LUKS/fscrypt)
# - Montaggio automatico della home al login
# - Smontaggio automatico al logout
# - Applicazione delle policy password

# LIMITAZIONI IMPORTANTI:
# 1. Incompatibilità con useradd/usermod/userdel tradizionali
#    Gli utenti systemd-homed NON sono in /etc/passwd
#    Usare SOLO homectl per gestirli
#
# 2. NFS e network storage
#    Le home LUKS non funzionano bene con NFS (il file immagine è grande)
#    Per ambienti con NFS, usare storage=cifs o la gestione tradizionale
#
# 3. Cifratura at rest, non at wire
#    LUKS protegge i dati quando il sistema è spento
#    Quando l'utente è loggato, la home è montata e accessibile
#
# 4. Backup — l'immagine LUKS è un blob opaco
#    Per backup incrementali, serve montare l'immagine e fare backup interno
#    Oppure usare storage=fscrypt che lavora su file individuali
#
# 5. Maturità — systemd-homed è relativamente recente
#    Non tutte le distribuzioni lo abilitano di default
#    Testare in ambienti non-production prima dell'adozione
#
# 6. UID allocation
#    systemd-homed assegna UID nel range 60001-60513 per default
#    Può entrare in conflitto con utenti esistenti se non coordinato

# QUANDO USARE systemd-homed:
# ✓ Laptop aziendali (cifratura portabile della home)
# ✓ Workstation con utenti multipli (isolamento forte)
# ✓ Ambienti dove la portabilità dell'account è importante
# ✗ Server in produzione con NFS
# ✗ Ambienti con gestione centralizzata LDAP/AD (usare SSSD)
# ✗ Container e server headless minimalisti
```

---

## Login Management e Limiti

### /etc/login.defs

Già trattato nella sezione Password Policy. Contiene i default per la creazione utenti, algoritmi di hash, range UID/GID e UMASK.

### /etc/securetty — Terminali Sicuri per Root

```bash
# /etc/securetty elenca i terminali da cui root può eseguire il login diretto
# Su sistemi moderni con systemd, questo file potrebbe non esistere
# (il controllo è delegato a PAM e pam_securetty)

# Contenuto tipico:
console
tty1
tty2
tty3
tty4
tty5
tty6
# Se il file è vuoto: root non può fare login diretto da nessun terminale
# Se il file non esiste: nessuna restrizione (dipende dalla distro)

# Per bloccare il login root diretto su tutti i terminali (best practice):
# 1. Svuotare /etc/securetty
sudo truncate -s 0 /etc/securetty
# 2. O assicurarsi che pam_securetty sia in /etc/pam.d/login:
#    auth required pam_securetty.so

# NOTA: questo NON blocca su/sudo, solo il login diretto
```

### /etc/security/limits.conf — Limiti Risorse

```bash
# limits.conf definisce limiti per utente/gruppo sulle risorse di sistema
# Applicato dal modulo PAM pam_limits.so (deve essere in /etc/pam.d/common-session)

# Formato:
# <dominio>    <tipo>    <elemento>    <valore>
# dominio: username, @groupname, * (tutti)
# tipo: soft (default, l'utente può aumentare fino a hard), hard (massimo assoluto)

# /etc/security/limits.conf — esempi pratici

# Limiti processi
*               soft    nproc           4096         # Max processi per utente (soft)
*               hard    nproc           8192         # Max processi per utente (hard)

# Limiti file aperti
*               soft    nofile          65536        # File aperti (soft)
*               hard    nofile          131072       # File aperti (hard)
@developers     soft    nofile          8192         # Override per gruppo

# Limiti memoria
@students       hard    as              1048576      # Max address space (KB) = 1GB
@students       hard    memlock         65536        # Max locked memory (KB)

# Core dump
*               hard    core            0            # Disabilita core dump per tutti
@developers     soft    core            unlimited    # Ma permettili ai developer

# Dimensione file
@students       hard    fsize           1048576      # Max file size (KB) = 1GB

# CPU time
@students       hard    cpu             60           # Max 60 minuti CPU per sessione

# Login simultanei
@students       hard    maxlogins       2            # Max 2 login simultanei
deploy          hard    maxlogins       1            # Solo 1 login per deploy

# Priorità nice
@realtime       -       nice            -20          # Può usare nice fino a -20
*               -       nice            0            # Default: solo nice >= 0

# Priorità real-time
@audio          -       rtprio          99           # Real-time priority per audio
@audio          -       memlock         unlimited    # Lock memory per audio

# Per file drop-in (preferibili):
# /etc/security/limits.d/90-custom.conf

# Verificare i limiti correnti
ulimit -a                            # Nella shell corrente
cat /proc/self/limits                # Limiti del processo corrente
cat /proc/$(pgrep -u mario bash)/limits  # Limiti di un processo specifico

# Applicare senza re-login (solo soft limit, nella sessione corrente)
ulimit -n 65536                      # File aperti
ulimit -u 8192                       # Processi
```

### /etc/security/access.conf — Controllo Accesso Login

```bash
# Controlla chi può accedere da dove. Usato con pam_access.so.
# Formato: +/- : utenti : origini

# Permettere solo admin da remoto
+ : (sysadmin) : ALL
- : ALL : ALL EXCEPT LOCAL

# Vedere la sezione PAM per la configurazione del modulo
```

### /etc/nologin — Blocco Login Globale

```bash
# Se il file /etc/nologin esiste, NESSUN utente (tranne root) può fare login
# Il contenuto del file viene mostrato come messaggio

# Creare (manutenzione)
echo "Sistema in manutenzione. Ripristino previsto alle 14:00." | sudo tee /etc/nologin

# Rimuovere (fine manutenzione)
sudo rm /etc/nologin

# Il modulo PAM responsabile è pam_nologin.so
# In /etc/pam.d/login e /etc/pam.d/sshd:
# account required pam_nologin.so
```

---

## Ambiente Utente e /etc/skel

### /etc/skel — Template Home Directory

```bash
# /etc/skel contiene i file copiati nella home directory di ogni nuovo utente
# creato con useradd -m o adduser

ls -la /etc/skel/
# .bash_logout
# .bashrc
# .profile

# Personalizzare skel per gli utenti futuri
sudo cp /etc/skel/.bashrc /etc/skel/.bashrc.bak

# Aggiungere file personalizzati che ogni nuovo utente riceverà
sudo cp /path/to/custom.bashrc /etc/skel/.bashrc
sudo mkdir -p /etc/skel/.ssh
sudo touch /etc/skel/.ssh/authorized_keys
sudo chmod 700 /etc/skel/.ssh
sudo chmod 600 /etc/skel/.ssh/authorized_keys

# Skel alternativo per useradd
sudo useradd -m -k /etc/skel-developers username   # Usa skel alternativo

# NOTA: le modifiche a skel NON si applicano retroattivamente agli utenti esistenti
```

### File di Inizializzazione Shell

```bash
# Ordine di esecuzione per bash login shell:
# 1. /etc/profile                   (globale, login shell)
# 2. /etc/profile.d/*.sh            (drop-in globali)
# 3. ~/.bash_profile O ~/.bash_login O ~/.profile  (utente, il primo trovato)
# 4. ~/.bashrc                      (invocato da .bash_profile tipicamente)

# Ordine per bash non-login shell (es. terminale in GUI):
# 1. /etc/bash.bashrc               (globale, Debian/Ubuntu)
# 2. ~/.bashrc                      (utente)

# Ordine al logout:
# 1. ~/.bash_logout
# 2. /etc/bash.bash_logout          (se esiste)

# /etc/profile — configurazione globale di login
# NON editare direttamente — usare file drop-in in /etc/profile.d/

# /etc/profile.d/custom-env.sh
export EDITOR=vim
export VISUAL=vim
export HISTSIZE=10000
export HISTFILESIZE=20000
export HISTCONTROL=ignoreboth:erasedups
export HISTTIMEFORMAT="%Y-%m-%d %H:%M:%S  "

# /etc/environment — variabili d'ambiente globali (lette da PAM, non è uno script)
# Formato: KEY=value (senza export, senza espansione variabili)
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
LANG="it_IT.UTF-8"

# ~/.bashrc — configurazione utente per shell interattive
# Alias, prompt, funzioni, PATH personalizzato

# ~/.profile — configurazione utente per login shell
# Variabili d'ambiente, avvio agenti (ssh-agent, gpg-agent)
```

### Cambiare Shell di Default

```bash
# Vedere le shell disponibili
cat /etc/shells

# Cambiare la propria shell
chsh -s /bin/zsh

# Cambiare la shell di un altro utente (richiede root)
sudo chsh -s /bin/zsh mario

# Installare una shell e aggiungerla a /etc/shells
sudo apt install zsh
# L'installazione la aggiunge automaticamente a /etc/shells

# Se necessario aggiungere manualmente:
echo "/usr/local/bin/fish" | sudo tee -a /etc/shells
```

---

## Account di Servizio

Gli account di servizio (daemon account) sono utenti creati per eseguire servizi specifici, isolando i processi e limitando i danni in caso di compromissione.

### Creare Account di Servizio

```bash
# Utente di sistema con useradd
sudo useradd -r \                    # -r = utente di sistema (UID nel range 100-999)
  -s /usr/sbin/nologin \             # Nessun login interattivo
  -d /var/lib/myapp \                # Home directory (per file di stato)
  -M \                               # NON creare la home (la creeremo manualmente)
  -c "MyApp Service Account" \       # Commento descrittivo
  myapp

# Creare la home manualmente con permessi restrittivi
sudo mkdir -p /var/lib/myapp
sudo chown myapp:myapp /var/lib/myapp
sudo chmod 750 /var/lib/myapp

# Con adduser (Debian/Ubuntu) — più verboso ma equivalente
sudo adduser --system --group --home /var/lib/myapp \
  --no-create-home --shell /usr/sbin/nologin myapp
```

### DynamicUser= in systemd

```bash
# systemd può creare utenti dinamici per i servizi senza toccare /etc/passwd
# L'utente esiste solo finché il servizio è attivo

# /etc/systemd/system/myapp.service
[Service]
DynamicUser=yes                      # Crea utente temporaneo
StateDirectory=myapp                 # → /var/lib/myapp (owned dall'utente dinamico)
CacheDirectory=myapp                 # → /var/cache/myapp
LogsDirectory=myapp                  # → /var/log/myapp
ProtectSystem=strict                 # Filesystem read-only
ProtectHome=true                     # /home inaccessibile
PrivateTmp=true                      # /tmp isolato
NoNewPrivileges=true                 # No escalation
ExecStart=/usr/local/bin/myapp

# Vantaggi di DynamicUser:
# - Nessuna entry permanente in /etc/passwd
# - Isolamento automatico del filesystem
# - L'utente non può essere usato per login
# - UID allocato dal range systemd (61184-65519)
```

### Convenzioni per Account di Servizio

```bash
# Pattern comuni per servizi noti:
# Servizio     Utente       Home                   Shell
# nginx        www-data     /var/www               /usr/sbin/nologin
# PostgreSQL   postgres     /var/lib/postgresql     /bin/bash (necessaria per psql)
# MySQL        mysql        /var/lib/mysql          /bin/false
# Redis        redis        /var/lib/redis          /usr/sbin/nologin
# Elasticsearch elasticsearch /usr/share/elasticsearch /bin/false

# Regole:
# 1. Ogni servizio ha il proprio utente (isolamento)
# 2. Shell = /usr/sbin/nologin o /bin/false
# 3. Home = directory dei dati del servizio
# 4. Nessuna password impostata
# 5. In systemd: User= nella sezione [Service]

# Verificare che un servizio giri con il proprio utente
ps -eo user,pid,comm | grep nginx
# www-data  1234 nginx
# www-data  1235 nginx
```

---

## Auditing Account

### last — Storico Login

```bash
# last legge /var/log/wtmp (login riusciti) e mostra lo storico
last                                 # Ultimi login
last -n 20                           # Ultimi 20 login
last -a                              # Mostra hostname nell'ultima colonna
last -i                              # Mostra IP invece di hostname
last -F                              # Timestamp completo
last -x                              # Mostra shutdown e runlevel
last mario                           # Login di mario
last reboot                          # Storico dei reboot
last -s 2026-05-01 -t 2026-05-22    # Range di date

# Output tipico:
# mario    pts/0    192.168.1.50   Thu May 22 09:30   still logged in
# admin    pts/1    10.0.0.5       Wed May 21 14:22 - 17:45  (03:23)
# reboot   system boot  6.17.0-29-generic Thu May 22 08:00   still running
```

### lastb — Tentativi Falliti

```bash
# lastb legge /var/log/btmp (tentativi falliti)
sudo lastb                           # Richiede root
sudo lastb -n 20                     # Ultimi 20 fallimenti
sudo lastb mario                     # Fallimenti per mario
sudo lastb -i                        # Con IP

# Output tipico:
# root     ssh:notty    185.234.xx.xx  Thu May 22 03:42 - 03:42  (00:00)
# admin    ssh:notty    45.33.xx.xx    Wed May 21 22:15 - 22:15  (00:00)
# Un volume elevato da IP sconosciuti indica un attacco bruteforce
```

### lastlog — Ultimo Login per Utente

```bash
# lastlog mostra l'ultimo login di OGNI utente del sistema
lastlog                              # Tutti gli utenti
lastlog -u mario                     # Utente specifico
lastlog -b 30                        # Utenti che NON hanno fatto login negli ultimi 30 giorni
lastlog -t 7                         # Utenti che HANNO fatto login negli ultimi 7 giorni

# Utenti con "Never logged in" e shell attiva → candidati per rimozione
lastlog -b 90 | grep -v 'Never logged in' | grep '/bin/bash'
```

### faillog — Contatore Fallimenti

```bash
# faillog gestisce il contatore dei login falliti (da /var/log/faillog)
sudo faillog -a                      # Mostra tutti gli utenti
sudo faillog -u mario                # Utente specifico

# Impostare il massimo di fallimenti prima del blocco
sudo faillog -m 5 -u mario          # Max 5 tentativi per mario
sudo faillog -m 5                    # Max 5 per tutti

# Resettare il contatore
sudo faillog -r -u mario            # Reset per mario
sudo faillog -r                      # Reset per tutti

# NOTA: pam_faillock ha largamente sostituito faillog su sistemi moderni
# Vedere la sezione PAM → pam_faillock
```

### wtmp e btmp — File di Log

```bash
# /var/log/wtmp   — login riusciti (letto da last)
# /var/log/btmp   — tentativi falliti (letto da lastb)
# Sono file binari, non leggibili con cat/less

# Dimensione e rotazione
ls -la /var/log/wtmp /var/log/btmp
# Rotazione gestita da logrotate (/etc/logrotate.conf o /etc/logrotate.d/wtmp)

# Se i file sono corrotti o mancanti, ricrearli:
sudo truncate -s 0 /var/log/wtmp
sudo truncate -s 0 /var/log/btmp
sudo chmod 664 /var/log/wtmp
sudo chmod 600 /var/log/btmp
sudo chown root:utmp /var/log/wtmp
sudo chown root:utmp /var/log/btmp

# Audit avanzato con auditd
sudo aureport --auth                  # Report autenticazione
sudo aureport --auth --summary        # Sommario
sudo aureport --login                 # Report login
sudo aureport --login --failed        # Solo login falliti
sudo ausearch -m USER_LOGIN -ts today # Login di oggi
```

### Script di Audit Utenti

```bash
#!/bin/bash
# audit-users.sh — report sullo stato degli utenti del sistema

echo "=== AUDIT UTENTI — $(date -I) ==="

echo -e "\n--- Utenti con shell di login attiva ---"
awk -F: '$7 !~ /(nologin|false|sync|shutdown|halt)/ {printf "%-20s UID=%-6s Shell=%s\n", $1, $3, $7}' /etc/passwd

echo -e "\n--- Utenti con UID 0 (dovrebbe essere solo root) ---"
awk -F: '$3 == 0 {print $1}' /etc/passwd

echo -e "\n--- Account bloccati ---"
sudo awk -F: '$2 ~ /^!/ {print $1}' /etc/shadow

echo -e "\n--- Account senza password ---"
sudo awk -F: '($2 == "" || $2 == "!") {print $1}' /etc/shadow

echo -e "\n--- Utenti mai loggati (con shell attiva) ---"
lastlog -b 99999 | grep -v 'Never\|Username' 2>/dev/null
comm -23 \
  <(awk -F: '$7 !~ /(nologin|false)/ {print $1}' /etc/passwd | sort) \
  <(last | awk '{print $1}' | sort -u) | head -20

echo -e "\n--- Password scadute ---"
while IFS=: read -r user _; do
    expire_info=$(sudo chage -l "$user" 2>/dev/null | grep "Password expires" | cut -d: -f2 | xargs)
    if [[ "$expire_info" != "never" && "$expire_info" != "" ]]; then
        expire_epoch=$(date -d "$expire_info" +%s 2>/dev/null)
        now_epoch=$(date +%s)
        if [[ -n "$expire_epoch" && "$expire_epoch" -lt "$now_epoch" ]]; then
            echo "  $user — scaduta il $expire_info"
        fi
    fi
done < <(awk -F: '$7 !~ /(nologin|false)/ {print $1":"$7}' /etc/passwd)

echo -e "\n--- File orfani (UID/GID senza utente/gruppo) ---"
sudo find /home /var /tmp -nouser -o -nogroup 2>/dev/null | head -20

echo -e "\n--- Sessioni attive ---"
who -u
```

---

## Best Practices

### Gestione Utenti

1. **UID/GID coerenti**: in ambienti multi-server, mantenere UID/GID consistenti. Un UID diverso per lo stesso utente su server diversi causa problemi con NFS e permessi. Usare un directory service centralizzato (LDAP/AD/FreeIPA) per garantire la coerenza.

2. **Centralizzare l'autenticazione**: in ambienti con più di 5 server, usare SSSD + LDAP/AD/FreeIPA. La gestione utenti locale su ogni server non scala. Mantenere solo utenti locali di emergenza (es. un admin locale con password forte in cassaforte).

3. **Gruppi per i permessi**: assegnare permessi ai gruppi, non ai singoli utenti. Aggiungere/rimuovere utenti dai gruppi è più gestibile. Creare gruppi funzionali (`web-deploy`, `db-admin`, `log-viewer`) piuttosto che usare nomi generici.

4. **`usermod -aG` con la -a**: dimenticare `-a` (append) sovrascrive tutti i gruppi supplementari dell'utente. Errore comune e pericoloso. Verificare sempre con `id username` dopo la modifica.

5. **Utenti di servizio senza shell**: ogni servizio con il proprio utente (`User=` in systemd) con shell `/usr/sbin/nologin`. Usare `DynamicUser=yes` dove possibile.

6. **Password policy**: enforce via PAM (`pam_pwquality`) e `chage`. Lunghezza minima 12+ caratteri, scadenza 90 giorni, lock dopo 5 tentativi falliti. Le policy locali sono un backup — centralizzare dove possibile.

7. **Audit periodico**: verificare regolarmente gli utenti con `lastlog` (utenti mai loggati = probabilmente da rimuovere) e `awk` su `/etc/passwd` per utenti con shell attiva non necessaria. Schedulare lo script di audit settimanalmente.

### sudo e Privilegi

8. **Drop-in `/etc/sudoers.d/`**: mai editare `/etc/sudoers` direttamente. Usare file drop-in numerati (`10-admins`, `20-deploy`, `90-monitoring`) per chiarezza e gestibilità.

9. **NOPASSWD con parsimonia**: `NOPASSWD` solo per automazione (CI/CD, monitoring) e solo per comandi specifici, mai `NOPASSWD: ALL`. Loggare sempre con `log_input, log_output`.

10. **Principio del minimo privilegio**: dare accesso solo a ciò che serve. Preferire `Cmnd_Alias` specifici a `ALL`. Usare polkit per autorizzazioni granulari al posto di sudo dove appropriato.

### Sicurezza

11. **Bloccare root diretto**: disabilitare login root via SSH (`PermitRootLogin no` in `sshd_config`) e su console (`/etc/securetty` vuoto). Usare sudo per l'escalation.

12. **pam_faillock**: configurare il blocco dopo 5 tentativi falliti con sblocco automatico dopo 10-30 minuti. Applicare anche a root (`even_deny_root`).

13. **Monitorare btmp**: controllare regolarmente `sudo lastb` per tentativi di accesso non autorizzati. Un volume elevato indica attacchi bruteforce — implementare fail2ban o firewall.

14. **File orfani**: dopo l'eliminazione di un utente, cercare file con UID/GID orfano (`find / -nouser -o -nogroup`) e assegnarli o rimuoverli.

15. **Separare ambienti**: utenti diversi per sviluppo, staging e produzione. Mai condividere credenziali tra ambienti.

---

## Troubleshooting

**1. "Authentication failure" per utente locale**
→ (1) Verificare che la password sia impostata: `sudo passwd -S username`. Se `L` = bloccato, sbloccare con `sudo passwd -u username`. Se `NP` = nessuna password, impostarne una con `sudo passwd username`. (2) Controllare `/etc/shadow`: l'hash deve iniziare con `$6$`, `$y$` o simile, non con `!` o `*`. (3) Verificare che la shell sia in `/etc/shells`. (4) Controllare PAM: `sudo grep -r pam_deny /etc/pam.d/` per moduli mal posizionati.

**2. "Authentication failure" per utente LDAP/AD**
→ (1) `getent passwd username` funziona? Se no: SSSD non sta risolvendo. `sudo systemctl status sssd`. (2) `sudo sssctl domain-status example.com`. (3) Cache corrotta: `sudo sss_cache -E` per svuotare. (4) `sudo journalctl -u sssd` per errori. (5) Kerberos: `kinit username@REALM` per testare l'autenticazione separatamente.

**3. "User not known to the underlying authentication module"**
→ L'utente non esiste in nessun database configurato in `nsswitch.conf`. Verificare: `/etc/passwd` (locale), `getent passwd` (tutti i database), `realm list` (dominio AD). Se SSSD: `sudo sssctl user-show username`.

**4. "Utente non può cambiare password"**
→ `sudo chage -l username` per verificare policy. Se `Minimum number of days` > 0 e il cambio è troppo recente, l'utente deve attendere. Se LDAP/AD: la policy password è gestita centralmente. Verificare anche `pam_pwquality` — la nuova password potrebbe non soddisfare i requisiti di complessità.

**5. "usermod: user X is currently used by process Y"**
→ Non si può modificare un utente mentre ha processi attivi. `loginctl terminate-user username` per terminare la sessione, oppure operare quando l'utente non è connesso. Per forzare: `sudo usermod -f ...` (ma può causare problemi).

**6. "username is not in the sudoers file. This incident will be reported."**
→ L'utente non ha permessi sudo. (1) Verificare: `groups username` — deve includere `sudo` (Debian/Ubuntu) o `wheel` (RHEL/Fedora). (2) Aggiungere: `sudo usermod -aG sudo username`. (3) Se l'utente è nel gruppo ma ancora fallisce: fare logout/login (i gruppi si aggiornano solo alla creazione della sessione). (4) Verificare `/etc/sudoers` e `/etc/sudoers.d/` per regole specifiche.

**7. Account bloccato vs password scaduta vs account scaduto**
→ Tre situazioni diverse con sintomi simili: (1) **Account bloccato** (`passwd -l`): `sudo passwd -S username` mostra `L`. Fix: `sudo passwd -u username`. (2) **Password scaduta** (`chage -M`): `sudo chage -l username` mostra una data passata. Fix: l'utente deve cambiare password o `sudo chage -d $(date +%Y-%m-%d) username`. (3) **Account scaduto** (`chage -E`): impossibile fare login. Fix: `sudo chage -E -1 username` per rimuovere la scadenza. (4) **pam_faillock**: troppi tentativi falliti. Fix: `sudo faillock --user username --reset`.

**8. Home directory mancante dopo login LDAP**
→ Se l'utente LDAP/AD si autentica ma la home non esiste: (1) Aggiungere `pam_mkhomedir` in `/etc/pam.d/common-session`: `session optional pam_mkhomedir.so umask=0077 skel=/etc/skel`. (2) Oppure con `oddjob-mkhomedir` (RHEL): `sudo systemctl enable --now oddjobd`. (3) Verificare che `fallback_homedir` sia impostato in `sssd.conf`.

**9. Modifiche ai gruppi non hanno effetto**
→ Le modifiche ai gruppi supplementari (`usermod -aG`) richiedono che l'utente faccia logout e login. I processi già in esecuzione mantengono i vecchi gruppi. Workaround senza logout: `newgrp groupname` (apre una subshell con il nuovo gruppo). Verificare con `id` (mostra i gruppi della sessione corrente) vs `getent group` (mostra i gruppi nel database).

**10. UID collision — due utenti con lo stesso UID**
→ Se due utenti hanno lo stesso UID, il kernel li considera lo stesso utente. I file di uno sono accessibili dall'altro. Diagnostica: `awk -F: '{print $3}' /etc/passwd | sort -n | uniq -d` per trovare duplicati. Fix: cambiare l'UID di uno dei due con `sudo usermod -u NUOVO_UID username` e aggiornare i file: `sudo find / -user VECCHIO_UID -exec chown NUOVO_UID {} \;`.

**11. `/etc/nologin` blocca tutti i login**
→ Se esiste il file `/etc/nologin`, solo root può fare login. Tutti gli altri vedono il contenuto del file e vengono disconnessi. Fix: `sudo rm /etc/nologin`. Causa comune: dimenticato dopo una manutenzione, oppure creato da `shutdown -h +10` (che crea `/etc/nologin` 5 minuti prima dello shutdown).

**12. polkit — "Not authorized" per operazioni systemd/dischi**
→ (1) Verificare l'azione: `pkaction | grep systemd`. (2) Verificare le regole: `ls /etc/polkit-1/rules.d/`. (3) Creare una regola in `/etc/polkit-1/rules.d/` per autorizzare il gruppo/utente. (4) Verificare che `polkitd` sia attivo: `systemctl status polkit`.

**13. subuid/subgid non configurati — container rootless non partono**
→ Errore tipico: `cannot set up uid map` o `newuidmap: ... not allowed`. Fix: (1) Verificare `/etc/subuid` e `/etc/subgid` per l'utente. (2) Aggiungere: `sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 username`. (3) Verificare che `/usr/bin/newuidmap` e `/usr/bin/newgidmap` abbiano il setuid bit: `ls -l /usr/bin/newuidmap`. (4) Verificare `kernel.unprivileged_userns_clone=1`.

**14. Shell non in /etc/shells — chsh rifiuta il cambio**
→ `chsh` richiede che la shell sia elencata in `/etc/shells`. Fix: `echo "/usr/local/bin/fish" | sudo tee -a /etc/shells`. Per utenti di servizio, `/usr/sbin/nologin` non deve essere in `/etc/shells` (è corretto così).

**15. limits.conf non si applica — processo supera i limiti**
→ (1) Verificare che `pam_limits.so` sia in `/etc/pam.d/common-session`. (2) Per servizi systemd, `limits.conf` NON si applica — usare `LimitNOFILE=` etc. nel file unit. (3) I limiti si applicano solo alle nuove sessioni, non ai processi già in esecuzione. (4) Verificare con `cat /proc/PID/limits`.

**16. PAM misconfiguration — nessuno può più fare login**
→ Situazione critica. Se `pam_deny.so` è in posizione `required` all'inizio dello stack, blocca tutti. (1) Se hai accesso fisico: avviare in recovery mode / single user. (2) Montare il filesystem e correggere `/etc/pam.d/common-auth`. (3) Mantenere SEMPRE una sessione root aperta prima di modificare PAM. (4) Testare con `pamtester` prima di applicare: `pamtester login username authenticate`.

**17. SSSD cache stale — utente rimosso da AD ma ancora può fare login**
→ La cache offline di SSSD mantiene le credenziali per `offline_credentials_expiration` giorni. (1) Invalidare la cache: `sudo sss_cache -E`. (2) Riavviare SSSD: `sudo systemctl restart sssd`. (3) Se persiste: rimuovere i file di cache in `/var/lib/sss/db/` e riavviare.

---

## FAQ

**Q1: Qual è la differenza tra `useradd` e `adduser`?**
`useradd` è il comando low-level (disponibile su tutte le distro). Crea l'utente con le opzioni specificate, nulla di più. `adduser` (Debian/Ubuntu) è un wrapper interattivo: crea home, copia skel, chiede password e informazioni GECOS. Su RHEL/Fedora, `adduser` è un symlink a `useradd`. Regola: in script, usare `useradd` con opzioni esplicite. Interattivamente, `adduser` è più comodo.

**Q2: Come resettare la password di root se è stata dimenticata?**
(1) Riavviare il sistema. (2) Nel bootloader GRUB, premere `e` sulla voce di boot. (3) Aggiungere `init=/bin/bash` alla riga `linux`. (4) Premere Ctrl+X per avviare. (5) Il sistema parte con una shell root senza password. (6) Rimontare il filesystem in lettura/scrittura: `mount -o remount,rw /`. (7) Cambiare la password: `passwd root`. (8) Sincronizzare e riavviare: `sync && exec /sbin/init`. **NOTA**: questo richiede accesso fisico alla macchina e un bootloader non protetto — il che evidenzia l'importanza di proteggere GRUB con password.

**Q3: Un utente è nel gruppo `sudo` ma non può usare sudo. Perché?**
I gruppi supplementari vengono caricati all'avvio della sessione. Se l'utente è stato aggiunto al gruppo dopo il login, deve fare logout e login. Workaround senza logout: `newgrp sudo` oppure `su - username`. Verificare con `id` che il gruppo sia effettivamente nella sessione.

**Q4: Come impedire a un utente di fare login SSH ma permettergli SCP/SFTP?**
Impostare la shell a `/usr/sbin/nologin` non basta — blocca anche SCP/SFTP. Usare il sottosistema SFTP interno di SSH in `sshd_config`: `Match User sftpuser` + `ForceCommand internal-sftp` + `ChrootDirectory /home/sftpuser`. Oppure usare `rssh` o `scponly` come shell restricted.

**Q5: Come verificare quali file appartengono a un utente?**
`find / -user username 2>/dev/null` per trovare tutti i file. Per file orfani dopo l'eliminazione dell'utente: `find / -nouser 2>/dev/null`. Per volume: `find /home/username -type f | wc -l` e `du -sh /home/username`.

**Q6: Qual è la differenza tra `passwd -l` e `usermod -L`?**
Sono equivalenti — entrambi aggiungono `!` davanti all'hash della password in `/etc/shadow`. L'utente non può più fare login con password, ma può ancora fare login con chiave SSH. Per bloccare completamente: `sudo chage -E 0 username` (scade l'account) oppure `sudo usermod -s /usr/sbin/nologin username` (rimuove la shell).

**Q7: Come gestire gli utenti su NFS?**
NFS mappa gli accessi in base a UID/GID numerici, non ai nomi. Se l'utente `mario` ha UID 1000 sul client e UID 1001 sul server NFS, i permessi saranno sbagliati. Soluzioni: (1) Centralizzare con LDAP/SSSD per UID coerenti. (2) Usare NFSv4 con Kerberos per l'autenticazione basata su nomi. (3) Usare `id_mapping` (NFSv4).

**Q8: Cos'è il "UPG" (User Private Group)?**
Configurato da `USERGROUPS_ENAB yes` in `/etc/login.defs`. Ogni nuovo utente ottiene un gruppo primario con lo stesso nome e GID (es. utente `mario` GID 1001, gruppo `mario` GID 1001). Questo permette di usare umask `002` (file group-writable) in sicurezza, perché il gruppo primario contiene solo l'utente stesso.

**Q9: Come limitare i comandi che un utente può eseguire via sudo?**
In sudoers: `mario ALL=(root) /usr/bin/systemctl restart nginx, /usr/bin/journalctl -u nginx`. Mario può solo riavviare nginx e leggerne i log. **Attenzione**: le negazioni (`!`) sono facilmente aggirabili. Usare una whitelist di comandi specifici piuttosto che `ALL` con negazioni.

**Q10: Come funziona `pam_mkhomedir` e quando usarlo?**
`pam_mkhomedir` crea automaticamente la home directory al primo login dell'utente, copiando il contenuto di `/etc/skel`. È essenziale per utenti LDAP/AD che non hanno una home locale. Configurare in `/etc/pam.d/common-session`: `session optional pam_mkhomedir.so umask=0077 skel=/etc/skel`.

**Q11: Posso avere due utenti con lo stesso UID?**
Tecnicamente sì (con `useradd -o`), ma è quasi sempre un errore. Il kernel non distingue i due utenti — hanno gli stessi permessi su file e processi. L'unico uso legittimo è un alias per root (UID 0) come utente di emergenza, ma è sconsigliato. Usare sudo.

**Q12: Come migrare gli utenti da un server a un altro?**
(1) Copiare le righe rilevanti da `/etc/passwd`, `/etc/shadow`, `/etc/group`, `/etc/gshadow` (attenzione a non sovrascrivere utenti di sistema). (2) Copiare le home directory preservando permessi: `rsync -avz --numeric-ids /home/ dest:/home/`. (3) Verificare UID/GID coerenti. (4) Soluzione migliore: centralizzare con LDAP/SSSD, dove la migrazione è automatica.

**Q13: Come configurare l'accesso SSH solo con chiave per un utente?**
Non è una configurazione utente ma di SSH. In `/etc/ssh/sshd_config`: `Match User mario` + `PasswordAuthentication no`. L'utente deve avere la chiave pubblica in `~/.ssh/authorized_keys` con permessi corretti (700 per `.ssh/`, 600 per `authorized_keys`).

**Q14: Cos'è `nobody` e perché esiste?**
`nobody` (UID 65534) è un utente senza privilegi usato come fallback. NFS usa `nobody` per lo "squashing" — quando un client tenta di accedere come root, il server mappa l'accesso a `nobody`. Anche alcuni servizi usano `nobody` come utente non privilegiato, ma la best practice moderna è creare un utente di servizio dedicato.

**Q15: Come posso vedere tutti i login falliti in tempo reale?**
`sudo journalctl -f -t sshd | grep -i 'failed\|invalid'` per SSH. Per tutti i servizi PAM: `sudo journalctl -f | grep -i 'authentication failure'`. Per un report: `sudo lastb -i | head -50`. Per azione automatica contro il bruteforce: installare e configurare `fail2ban`.

**Q16: Come applicare i limiti di `limits.conf` ai servizi systemd?**
`limits.conf` (via `pam_limits.so`) si applica solo alle sessioni PAM (login SSH, su, sudo). I servizi systemd non passano da PAM per i limiti — usare le direttive `Limit*` nel file unit: `LimitNOFILE=65536`, `LimitNPROC=4096`, `LimitMEMLOCK=infinity`. Per override: `sudo systemctl edit myservice` e aggiungere nella sezione `[Service]`.
