# Tutorial Linux 27 — SELinux e AppArmor: Controllo Accesso Obbligatorio

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** SELinux policy, contexts, audit2allow, AppArmor profiles, container security
> **Prerequisiti:** `tutorial_linux_11_sicurezza.md`, `tutorial_linux_14_containerizzazione.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
MAC (Mandatory Access Control)
│
├── SELinux (RHEL/Fedora/CentOS)
│   ├── Mode: enforcing/permissive/disabled
│   ├── Policy: targeted/mls/minimum
│   ├── Contexts: user:role:type:level
│   ├── Booleans — switch policy
│   └── audit2allow — genera policy da audit
│
└── AppArmor (Ubuntu/Debian)
    ├── Mode: enforce/complain/disabled
    ├── Profili in /etc/apparmor.d/
    ├── Capabilities, paths, network
    └── aa-genprof — genera profilo automatico
```

---

# Parte A — SELinux

---

## A1. Concetti fondamentali

```bash
# SELinux: ogni processo e file ha un "contesto" (label)
# Accesso concesso solo se la policy lo permette ESPLICITAMENTE
# Di default: deny all, poi whitelist

# Verifica stato
getenforce          # Enforcing / Permissive / Disabled
sestatus            # dettagliato

# Cambia modalità (runtime, non persiste al reboot)
setenforce 1        # Enforcing (blocca e logga)
setenforce 0        # Permissive (solo logga, non blocca)

# Cambia modalità permanente
sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config

# Contesti SELinux
# Formato: user:role:type:level
# Es: system_u:object_r:httpd_sys_content_t:s0

# Visualizza contesto
ls -Z /var/www/html/         # file
ps -eZ | grep httpd           # processi
id -Z                         # utente corrente

# I processi possono accedere solo a type compatibili:
# httpd_t (processo nginx/apache) → httpd_sys_content_t (file web)
# httpd_t NON può accedere a: var_log_t, etc_t, home_root_t
```

> **Analogia:** DAC (permessi Unix tradizionali) è come il tornello di un palazzo: se hai il badge, entri. SELinux aggiunge un sistema di compartimentazione militare: anche con il badge, puoi accedere solo alle stanze per cui hai uno specifico "nulla osta" (context). Un processo web può leggere i file web, ma non può toccare i file di configurazione del sistema anche se gira come root.

---

## A2. Gestione contesti

```bash
# Cambia contesto di un file
chcon -t httpd_sys_content_t /var/www/html/index.html
chcon -R -t httpd_sys_content_t /var/www/html/   # ricorsivo

# Ripristina contesto predefinito dalla policy
restorecon /var/www/html/index.html
restorecon -Rv /var/www/html/   # -R ricorsivo, -v verbose

# Imposta contesto predefinito per un percorso (persiste)
semanage fcontext -a -t httpd_sys_content_t '/srv/web(/.*)?'
restorecon -Rv /srv/web/

# Lista mapping predefiniti
semanage fcontext -l | grep httpd

# Copia contesto da un file a un altro
chcon --reference=/var/www/html/ /nuovo/path/
```

---

## A3. Booleans e troubleshooting

```bash
# Booleans — switch per policy comuni
getsebool -a                          # lista tutti
getsebool httpd_can_network_connect   # verifica uno specifico

# Abilita temporaneamente
setsebool httpd_can_network_connect on

# Abilita permanentemente
setsebool -P httpd_can_network_connect on
setsebool -P httpd_can_connect_ldap on
setsebool -P httpd_enable_cgi on

# Booleans comuni per nginx/apache
# httpd_can_network_connect — connettiti a backend remoti
# httpd_use_nfs — usa file NFS
# httpd_enable_homedirs — accedi alle home degli utenti
# allow_httpd_anon_write — scrivi directory anon FTP

# Troubleshooting: cosa ha bloccato SELinux?
ausearch -m avc -ts recent              # audit log recente
ausearch -m avc -ts today              # oggi
sealert -a /var/log/audit/audit.log     # analisi human-readable

# Genera policy da denial
# 1. Vedi cosa ha bloccato
ausearch -m avc -ts recent | grep nginx

# 2. Genera modulo policy
ausearch -m avc -ts recent | audit2allow -M mio-nginx

# 3. Installa modulo
semodule -i mio-nginx.pp

# Attenzione: audit2allow può essere troppo permissivo
# Analizza SEMPRE il contenuto prima di installare
audit2allow -a -r   # review interattiva
```

---

# Parte B — AppArmor

---

## B1. Profili AppArmor

```bash
# Stato AppArmor
aa-status
systemctl status apparmor

# Profili disponibili
ls /etc/apparmor.d/
# usr.sbin.nginx  usr.sbin.mysqld  usr.bin.man  ...

# Modalità profilo
aa-enforce /etc/apparmor.d/usr.sbin.nginx     # blocca violazioni
aa-complain /etc/apparmor.d/usr.sbin.nginx    # solo logga
aa-disable /etc/apparmor.d/usr.sbin.nginx     # disabilita

# Ricarica profilo dopo modifica
apparmor_parser -r /etc/apparmor.d/usr.sbin.nginx

# Log violazioni
aa-logprof                            # analizza e suggerisce aggiunte
tail -f /var/log/syslog | grep apparmor
grep "apparmor" /var/log/kern.log
```

---

## B2. Scrivere profili custom

```bash
# Genera profilo automaticamente con aa-genprof
aa-genprof /opt/mia-app/venv/bin/python3
# 1. Avvia il programma in un'altra shell
# 2. Usalo normalmente (genera i log)
# 3. Torna su aa-genprof e premi S per analizzare
# 4. AppArmor chiede conferma per ogni accesso trovato

# Profilo manuale per un'app Python/FastAPI
cat > /etc/apparmor.d/opt.mia-app << 'EOF'
#include <tunables/global>

profile mia-app /opt/mia-app/venv/bin/python3 {
    #include <abstractions/base>
    #include <abstractions/python>
    #include <abstractions/nameservice>
    #include <abstractions/ssl_certs>

    # Python e venv
    /opt/mia-app/venv/bin/python3 mr,
    /opt/mia-app/venv/** r,
    /usr/lib/python3/** r,
    /usr/lib/python3.*/lib-dynload/** mr,

    # Sorgente applicazione
    /opt/mia-app/src/** r,
    /opt/mia-app/src/**.py r,

    # Dati applicazione
    /var/lib/mia-app/ r,
    /var/lib/mia-app/** rw,

    # Log (scrittura)
    /var/log/mia-app/ r,
    /var/log/mia-app/** w,

    # Rete TCP (porta 8000)
    network tcp,
    network inet stream,

    # Socket PostgreSQL
    /var/run/postgresql/.s.PGSQL.5432 rw,

    # Temp
    /tmp/ r,
    /tmp/mia-app/** rw,

    # Procfs (per librerie Python)
    /proc/*/maps r,
    /proc/self/mem r,

    # Deny esplicito su zone pericolose
    deny /etc/passwd r,
    deny /etc/shadow r,
    deny /root/** rwx,
    deny /home/** rwx,
}
EOF

# Carica e abilita
apparmor_parser -r -W /etc/apparmor.d/opt.mia-app
aa-enforce /etc/apparmor.d/opt.mia-app

# Test in modalità complain prima
aa-complain /etc/apparmor.d/opt.mia-app
# Esegui l'app, analizza log
aa-logprof   # aggiunge permessi mancanti
# Poi enforcing
aa-enforce /etc/apparmor.d/opt.mia-app
```

---

# Parte C — Sicurezza container con MAC

---

## C1. Docker + AppArmor/SELinux

```bash
# Docker crea profilo AppArmor automaticamente (docker-default)
docker inspect container | jq '.[0].HostConfig.SecurityOpt'
# ["apparmor:docker-default"]

# Profilo AppArmor custom per container
docker run --security-opt apparmor=mio-profilo-container mia-app

# SELinux con container (RHEL)
docker run --security-opt label=type:container_t mia-app
docker run --security-opt label=disable mia-app   # disabilita SELinux per container

# Profilo AppArmor Docker custom
cat > /etc/apparmor.d/docker-mia-app << 'EOF'
#include <tunables/global>

profile docker-mia-app flags=(attach_disconnected,mediate_deleted) {
    #include <abstractions/base>
    
    network inet tcp,
    network inet udp,
    
    file,           # tutto il filesystem (poi deny espliciti)
    
    deny /proc/sys/** wklx,
    deny @{PROC}/** wlx,
    deny /sys/** wklx,
    
    # Deny shell e tools pericolosi
    deny /bin/sh,
    deny /bin/bash,
    deny /usr/bin/python*,  # a meno che non sia l'app!
}
EOF

apparmor_parser -r /etc/apparmor.d/docker-mia-app
docker run --security-opt apparmor=docker-mia-app mia-app
```

---

# Parte E — Riepilogo

## SELinux quick reference

```bash
# Stato
getenforce; sestatus

# Contesto file
ls -Z percorso
chcon -t tipo file
restorecon -Rv percorso

# Booleans
getsebool -a | grep httpd
setsebool -P bool_name on

# Troubleshooting
ausearch -m avc -ts recent
ausearch -m avc | audit2allow -M modulo
semodule -i modulo.pp
```

## AppArmor quick reference

```bash
# Stato
aa-status

# Modalità
aa-enforce profilo
aa-complain profilo
aa-disable profilo

# Ricarica
apparmor_parser -r /etc/apparmor.d/profilo

# Genera profilo
aa-genprof /percorso/programma

# Log
aa-logprof   # analizza e suggerisce
```

## SELinux vs AppArmor

| Aspetto | SELinux | AppArmor |
|---|---|---|
| Distro | RHEL/Fedora | Ubuntu/Debian |
| Configurazione | Label su file (inode) | Path-based |
| Complessità | Alta | Media |
| Policy | Predefinita completa | Profili individuali |
| Debug | ausearch/audit2allow | aa-logprof |

## Prossimi passi

- `tutorial_linux_28_nginx.md` — nginx avanzato
- `tutorial_linux_34_hardening.md` — hardening completo
