# Tutorial Linux 12 — Utenti e Gruppi: useradd, usermod, PAM, LDAP

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** gestione utenti/gruppi, PAM, password policy, LDAP/AD integration
> **Prerequisiti:** `tutorial_linux_11_sicurezza.md`
> **Durata stimata:** 10-12 ore

---

## Mappa concettuale

```
Utenti e Gruppi
│
├── File di sistema
│   ├── /etc/passwd — account utenti
│   ├── /etc/shadow — password hashate
│   ├── /etc/group — definizione gruppi
│   └── /etc/gshadow — password gruppi
│
├── Gestione utenti
│   ├── useradd / adduser
│   ├── usermod — modifica
│   ├── userdel — elimina
│   └── passwd — gestione password
│
├── Gestione gruppi
│   ├── groupadd / groupmod / groupdel
│   └── gpasswd — gestione membership
│
├── PAM (Pluggable Authentication)
│   ├── /etc/pam.d/
│   ├── pam_pwquality — complessità password
│   └── pam_faillock — lock account
│
└── Directory Services
    ├── LDAP (sssd)
    ├── Active Directory (realm)
    └── Kerberos
```

---

# Parte A — Struttura utenti Linux

---

## A1. File /etc/passwd e /etc/shadow

```bash
# /etc/passwd — formato: nome:x:UID:GID:GECOS:home:shell
# x = password in /etc/shadow
# UID 0 = root
# UID 1-999 = system accounts
# UID 1000+ = utenti normali

cat /etc/passwd | head -5
# root:x:0:0:root:/root:/bin/bash
# daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
# www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin

# /etc/shadow — formato: nome:hash:lastchange:min:max:warn:inactive:expire
# lastchange = giorni dal 1970-01-01
# min = giorni minimi prima di cambiare password
# max = giorni massimi (scadenza)
# warn = giorni di warning prima della scadenza
# inactive = giorni dopo scadenza prima di bloccare
# expire = data di scadenza account (vuoto = mai)

# Hash: $6$ = SHA-512, $5$ = SHA-256, $2b$ = bcrypt
sudo cat /etc/shadow | grep mario
# mario:$6$salt$hash...:19000:0:90:7:::

# /etc/group — formato: nome:x:GID:membri
cat /etc/group | grep sudo
# sudo:x:27:mario,anna

# getent — interroga NSS (anche LDAP)
getent passwd mario      # info utente
getent group sudo        # info gruppo
getent passwd            # tutti gli utenti
```

> **Analogia:** `/etc/passwd` è come il registro aziendale delle persone: nome, badge (UID), reparto (GID), nome completo, ufficio (home), e mansione (shell). `/etc/shadow` è la cassaforte HR dove sono conservate le password (hashate, non in chiaro) — solo root può leggerla. I gruppi sono come i team: puoi appartenere a più team con diversi accessi.

---

## A2. Creare e gestire utenti

```bash
# useradd — low level
useradd -m -s /bin/bash -c "Mario Rossi" -G sudo,www-data mario
# -m: crea home directory
# -s: shell
# -c: commento/nome completo
# -G: gruppi aggiuntivi (separati da virgola)

# adduser — high level (interattivo, Debian/Ubuntu)
adduser mario              # wizard interattivo
adduser mario sudo         # aggiungi mario al gruppo sudo

# Imposta password
passwd mario               # interattivo
echo "mario:nuovapassword" | chpasswd   # non interattivo (scripting)
echo "nuovapassword" | passwd --stdin mario   # RHEL

# usermod — modifica utente esistente
usermod -l nuovonome mario            # rinomina login
usermod -s /bin/zsh mario            # cambia shell
usermod -d /home/nuovo mario         # cambia home
usermod -G sudo,devs mario           # sostituisce tutti i gruppi secondari
usermod -aG sudo mario               # AGGIUNGI al gruppo (senza -a cancella gli altri!)
usermod -L mario                     # Lock account (disabilita password)
usermod -U mario                     # Unlock account
usermod -e 2024-12-31 mario          # scadenza account
usermod -e "" mario                  # rimuovi scadenza

# userdel
userdel mario                        # rimuove utente, lascia home
userdel -r mario                     # rimuove utente E home E mail spool

# Password aging
chage -l mario                       # vedi politica password
chage -M 90 mario                    # scadenza max 90 giorni
chage -m 7 mario                     # minimo 7 giorni prima di cambiare
chage -W 14 mario                    # avvisa 14 giorni prima
chage -E 2024-12-31 mario            # scadenza account

# Account di servizio (no home, no shell)
useradd --system --no-create-home --shell /usr/sbin/nologin --comment "App Service" appuser
```

---

## A3. Gestione gruppi

```bash
# Crea gruppo
groupadd devs
groupadd -g 1500 devs    # con GID specifico

# Modifica gruppo
groupmod -n sviluppatori devs   # rinomina
groupmod -g 1501 devs           # cambia GID

# Aggiungi/rimuovi membro
gpasswd -a mario devs           # aggiungi mario
gpasswd -d mario devs           # rimuovi mario
gpasswd -M mario,anna devs      # imposta lista completa

# Gestione gpasswd (password gruppo)
gpasswd devs                    # imposta password gruppo
newgrp devs                     # cambia gruppo primario temporaneamente

# Visualizza membership
groups mario                    # tutti i gruppi di mario
id mario                        # uid, gid, groups

# Lista utenti di un gruppo
getent group devs
grep "^devs:" /etc/group        # alternativa
```

---

# Parte B — PAM (Pluggable Authentication Modules)

---

## B1. Policy password con pam_pwquality

```bash
# Installa
apt install libpam-pwquality

# Configura /etc/security/pwquality.conf
cat > /etc/security/pwquality.conf << 'EOF'
# Lunghezza minima
minlen = 12

# Complessità (numero di classi: upper, lower, digit, other)
minclass = 3

# Caratteri uguali consecutivi
maxrepeat = 3

# Non contenere il nome utente
usercheck = 1

# Verifica dizionario
dictcheck = 1

# Lunghezza credito (riduci minlen per ogni classe presente)
# -1 = nessun credito
lcredit = -1      # almeno 1 minuscolo
ucredit = -1      # almeno 1 maiuscolo
dcredit = -1      # almeno 1 cifra
ocredit = -1      # almeno 1 speciale
EOF

# /etc/pam.d/common-password (Debian/Ubuntu)
# Verifica che questa riga esista:
grep pam_pwquality /etc/pam.d/common-password
# password requisite pam_pwquality.so retry=3
```

---

## B2. Lock account con pam_faillock

```bash
# /etc/security/faillock.conf
cat > /etc/security/faillock.conf << 'EOF'
# Lock dopo 5 tentativi falliti
deny = 5
# Finestra di tempo: 5 minuti
fail_interval = 300
# Lock per 30 minuti
unlock_time = 1800
# Conta anche tentativo root
even_deny_root = true
# Ammetti root dopo
root_unlock_time = 60
EOF

# /etc/pam.d/common-auth — aggiungi faillock
# Prima della riga di autenticazione:
# auth required pam_faillock.so preauth silent
# auth [success=1 default=bad] pam_unix.so
# auth [default=die] pam_faillock.so authfail
# auth sufficient pam_faillock.so authsucc

# Controlla stato lock
faillock --user mario

# Sblocca manualmente
faillock --user mario --reset

# pam_tally2 (alternativa, più vecchia)
pam_tally2 --user mario --reset
```

---

## B3. pam_limits (ulimit)

```bash
# /etc/security/limits.conf
# Limita risorse per utente/gruppo
cat >> /etc/security/limits.conf << 'EOF'
# Database user: molti file aperti
postgres   soft   nofile   65536
postgres   hard   nofile   65536

# Web app: limita processi
www-data   soft   nproc    512
www-data   hard   nproc    512

# Sviluppatori: core dump abilitato
@devs      soft   core     unlimited

# Sicurezza: nessun core dump per utenti normali
*          soft   core     0
*          hard   core     0
EOF

# /etc/security/limits.d/ — file separati
cat > /etc/security/limits.d/90-postgres.conf << 'EOF'
postgres soft nofile 65536
postgres hard nofile 65536
EOF

# Verifica limits correnti
ulimit -a              # tutti i limiti della shell corrente
ulimit -n              # solo file descriptor
su - postgres -c "ulimit -a"  # limiti dell'utente postgres
```

---

# Parte C — Directory Services (LDAP/AD)

---

## C1. Integrazione Active Directory con sssd

```bash
# Installa pacchetti
apt install sssd sssd-tools realmd oddjob oddjob-mkhomedir \
    adcli samba-common-bin krb5-user libpam-sss libnss-sss

# Esplora il dominio
realm discover DOMINIO.AZIENDA.IT

# Unisci al dominio AD
realm join --user=administrator DOMINIO.AZIENDA.IT
# Inserisce password admin AD

# Verifica
realm list
id mario@DOMINIO.AZIENDA.IT

# /etc/sssd/sssd.conf
cat > /etc/sssd/sssd.conf << 'EOF'
[sssd]
services = nss, pam
domains = DOMINIO.AZIENDA.IT

[domain/DOMINIO.AZIENDA.IT]
id_provider = ad
access_provider = ad
auth_provider = ad
chpass_provider = ad

ad_domain = DOMINIO.AZIENDA.IT
krb5_realm = DOMINIO.AZIENDA.IT
realmd_tags = manages-system joined-with-adcli
cache_credentials = True

# Usa nome corto (senza dominio)
use_fully_qualified_names = False

# Crea home al login
fallback_homedir = /home/%u
default_shell = /bin/bash

# Permetti solo questo gruppo AD
ad_access_filter = (memberOf=CN=LinuxUsers,OU=Groups,DC=DOMINIO,DC=AZIENDA,DC=IT)
EOF

chmod 600 /etc/sssd/sssd.conf
systemctl enable --now sssd

# PAM per home directory automatica
pam-auth-update --enable mkhomedir
```

---

# Parte E — Riepilogo

## Comandi essenziali

| Operazione | Comando |
|---|---|
| Crea utente completo | `useradd -m -s /bin/bash -G sudo mario` |
| Imposta password | `passwd mario` |
| Aggiungi a gruppo | `usermod -aG sudo mario` |
| Lock account | `usermod -L mario` |
| Vedi info utente | `id mario` |
| Vedi gruppi | `groups mario` |
| Modifica shell | `usermod -s /bin/zsh mario` |
| Scadenza password | `chage -M 90 mario` |
| Verifica tentavitivi falliti | `faillock --user mario` |
| Sblocca account | `faillock --user mario --reset` |

## /etc/passwd campi

```
nome : x : UID : GID : GECOS : home : shell
mario : x : 1001 : 1001 : Mario Rossi : /home/mario : /bin/bash
```

## Prossimi passi

- `tutorial_linux_13_logging.md` — rsyslog, journald, logrotate
- `tutorial_linux_11_sicurezza.md` — sudoers avanzato, AppArmor
