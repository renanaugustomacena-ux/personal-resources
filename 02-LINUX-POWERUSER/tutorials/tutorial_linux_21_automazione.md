# Tutorial Linux 21 — Automazione: cron, at, anacron, Ansible

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** cron avanzato, at/batch, anacron, systemd timer, Ansible basics
> **Prerequisiti:** `tutorial_linux_04_systemd.md`, `tutorial_linux_02_shell_mastery.md`
> **Durata stimata:** 12-14 ore

---

## Mappa concettuale

```
Automazione Linux
│
├── Task scheduling
│   ├── cron — scheduling ricorrente
│   ├── at — esecuzione una tantum
│   ├── batch — esecuzione a carico basso
│   └── anacron — per sistemi non 24/7
│
├── systemd timer
│   ├── Alternativa moderna a cron
│   ├── Dipendenze su altri servizi
│   └── Logging integrato journal
│
└── Ansible
    ├── Inventory — host gestiti
    ├── Playbook — sequenza di task
    ├── Roles — moduli riusabili
    ├── Vault — segreti cifrati
    └── Ad-hoc commands
```

---

# Parte A — cron

---

## A1. Sintassi cron completa

```bash
# Formato: minuto ora giorno-mese mese giorno-settimana comando
# * = qualsiasi valore
# */n = ogni n unità
# a-b = range da a a b
# a,b,c = lista valori

# Esempi
# Ogni minuto
* * * * * /path/script.sh

# Alle 2:30 ogni giorno
30 2 * * * /opt/scripts/backup.sh

# Alle 8:00 ogni lunedì-venerdì
0 8 * * 1-5 /opt/scripts/report.sh

# Il primo di ogni mese
0 0 1 * * /opt/scripts/monthly.sh

# Ogni 15 minuti
*/15 * * * * /opt/scripts/check.sh

# Alle 9:00, 12:00, 15:00
0 9,12,15 * * * /opt/scripts/notifica.sh

# Ogni giorno lavorativo alle 18:30
30 18 * * 1-5 /opt/scripts/chiusura.sh

# Edita crontab dell'utente corrente
crontab -e

# Edita crontab di un altro utente (root)
crontab -u mario -e

# Lista crontab
crontab -l
crontab -u mario -l

# Rimuovi crontab
crontab -r

# /etc/cron.d/ — crontab di sistema con utente esplicito
cat > /etc/cron.d/backup-database << 'EOF'
# Backup database ogni notte alle 2:00
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=admin@esempio.it

0 2 * * * postgres /opt/scripts/backup-postgres.sh >> /var/log/backup.log 2>&1
EOF

# /etc/cron.daily/ — script eseguiti ogni giorno da cron
# /etc/cron.weekly/ — ogni settimana
# /etc/cron.monthly/ — ogni mese
# (no crontab, solo file eseguibili nella directory)
```

> **Analogia:** cron è come un orologiaio automatico che carica una serie di sveglie con compiti precisi. Ogni riga del crontab è una sveglia: "alle 02:00, esegui questo script". anacron è la versione per chi non lascia il computer sempre acceso — recupera i compiti saltati al prossimo avvio, come recuperare i messaggi di un segretario dopo un'assenza.

---

## A2. Variabili e gestione output

```bash
# Variabili in crontab
# SHELL — shell da usare (default /bin/sh)
# PATH — percorso comandi
# MAILTO — invia output via email (vuoto = nessuna email)
# HOME — directory home

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=admin@esempio.it
HOME=/root

# Reindirizza output su file invece di email
0 2 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1

# Silenzia output (nessuna email, nessun log)
0 2 * * * /opt/scripts/check.sh > /dev/null 2>&1

# Log con rotazione automatica (usa logger per journal)
0 2 * * * /opt/scripts/backup.sh 2>&1 | logger -t backup-script

# Pattern robusto per script cron
0 2 * * * /usr/bin/flock -n /tmp/backup.lock /opt/scripts/backup.sh
# flock -n: fallisce immediatamente se già bloccato (no sovrapposizione)

# Verifica cronologia cron
grep CRON /var/log/syslog | tail -20
journalctl -u cron --since today
```

---

# Parte B — at e anacron

---

## B1. at: esecuzione una tantum

```bash
# Esegui una volta in futuro
# Sintassi: at [TEMPO]
at now + 5 minutes << 'EOF'
/opt/scripts/riavvio.sh
EOF

at 14:30 << 'EOF'
systemctl restart nginx
EOF

at midnight + 1 week << 'EOF'
/opt/scripts/pulizia-mensile.sh
EOF

# Formati tempo
at now + 10 minutes
at 15:00
at 15:00 tomorrow
at 15:00 2024-01-20
at noon          # 12:00
at midnight      # 00:00
at teatime       # 16:00 (!)

# Lista job pianificati
atq

# Vedi contenuto di un job
at -c 3    # job numero 3

# Cancella job
atrm 3     # rimuovi job 3

# batch — come at ma esegui solo quando load < 0.8
batch << 'EOF'
/opt/scripts/compressione-archivi.sh
EOF
```

---

## B2. anacron

```bash
# anacron esegue task "almeno una volta al giorno/settimana/mese"
# Ideale per laptop e server non 24/7

# /etc/anacrontab
cat /etc/anacrontab
# SHELL=/bin/sh
# PATH=/sbin:/bin:/usr/sbin:/usr/bin
# MAILTO=root
# RANDOM_DELAY=45    # aggiunge ritardo casuale fino a 45 min
# START_HOURS_RANGE=3-22  # esegui solo tra le 3 e le 22

# Formato: periodo(giorni) ritardo(min) nome comando
# 1    5    cron.daily  nice run-parts /etc/cron.daily
# 7    25   cron.weekly nice run-parts /etc/cron.weekly
# @monthly 45 cron.monthly nice run-parts /etc/cron.monthly

# Aggiungi task personalizzato
echo "1 10 backup-quotidiano /opt/scripts/backup.sh" >> /etc/anacrontab

# Forza esecuzione
anacron -f -n    # -f force, -n no delay
anacron -u       # aggiorna timestamp senza eseguire

# Tracciamento
ls /var/spool/anacron/    # timestamp ultima esecuzione
```

---

# Parte C — Ansible

---

## C1. Installazione e configurazione

```bash
# Installazione
apt install ansible
# oppure
pip install ansible

# Struttura progetto
mkdir -p ansible/{inventory,playbooks,roles}

# Inventory — lista host gestiti
cat > ansible/inventory/hosts.ini << 'EOF'
[webserver]
web1.esempio.it ansible_user=mario ansible_port=2222
web2.esempio.it

[database]
db1.esempio.it ansible_user=postgres

[monitoring]
grafana.esempio.it

[all:vars]
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_private_key_file=~/.ssh/id_ed25519
EOF

# Inventory YAML (più espressivo)
cat > ansible/inventory/hosts.yml << 'EOF'
all:
  children:
    webserver:
      hosts:
        web1.esempio.it:
          ansible_user: mario
          http_port: 80
        web2.esempio.it:
          ansible_user: mario
    database:
      hosts:
        db1.esempio.it:
          ansible_user: postgres
          pg_version: 16
EOF

# Test connettività
ansible all -i inventory/hosts.ini -m ping
ansible webserver -i inventory/hosts.ini -m ping

# Comandi ad-hoc
ansible webserver -i inventory/ -m shell -a "df -h"
ansible database -i inventory/ -m shell -a "systemctl status postgresql"
ansible all -i inventory/ -m package -a "name=htop state=present" --become
```

---

## C2. Playbook Ansible

```yaml
# ansible/playbooks/webserver-setup.yml
---
- name: Setup Web Server
  hosts: webserver
  become: yes     # sudo
  vars:
    nginx_version: "1.24.*"
    app_user: "appuser"
    app_dir: "/opt/mia-app"
    deploy_port: 8000

  tasks:
    - name: Aggiorna apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Installa nginx
      apt:
        name: "nginx={{ nginx_version }}"
        state: present

    - name: Crea utente applicazione
      user:
        name: "{{ app_user }}"
        system: yes
        create_home: no
        shell: /usr/sbin/nologin

    - name: Crea directory applicazione
      file:
        path: "{{ app_dir }}"
        state: directory
        owner: "{{ app_user }}"
        group: "{{ app_user }}"
        mode: '0755'

    - name: Copia configurazione nginx
      template:
        src: templates/nginx-vhost.conf.j2
        dest: /etc/nginx/sites-available/mia-app.conf
        owner: root
        group: root
        mode: '0644'
      notify: Ricarica nginx

    - name: Abilita virtual host
      file:
        src: /etc/nginx/sites-available/mia-app.conf
        dest: /etc/nginx/sites-enabled/mia-app.conf
        state: link

    - name: Apri porta nel firewall
      ufw:
        rule: allow
        port: "{{ deploy_port }}"
        proto: tcp

    - name: Abilita e avvia nginx
      systemd:
        name: nginx
        enabled: yes
        state: started

  handlers:
    - name: Ricarica nginx
      systemd:
        name: nginx
        state: reloaded
```

```bash
# Esegui playbook
ansible-playbook -i inventory/ playbooks/webserver-setup.yml

# Dry-run (check mode)
ansible-playbook -i inventory/ playbooks/webserver-setup.yml --check

# Solo certi host
ansible-playbook -i inventory/ playbooks/webserver-setup.yml --limit web1.esempio.it

# Solo certi tag
ansible-playbook -i inventory/ playbooks/webserver-setup.yml --tags nginx

# Verbose
ansible-playbook -i inventory/ playbooks/webserver-setup.yml -v   # -vvv per massimo
```

---

## C3. Ansible Vault

```bash
# Cifra file con segreti
ansible-vault create ansible/vault/secrets.yml
# Inserisci la vault password

# Oppure cifra un file esistente
ansible-vault encrypt secrets.yml

# Visualizza
ansible-vault view secrets.yml

# Modifica
ansible-vault edit secrets.yml

# Decifra (attenzione: in chiaro su disco!)
ansible-vault decrypt secrets.yml

# Usa vault nei playbook
# vars_files:
#   - vault/secrets.yml

# Esegui con vault password
ansible-playbook --ask-vault-pass playbook.yml
# oppure da file
ansible-playbook --vault-password-file ~/.vault_pass playbook.yml
```

---

# Parte E — Riepilogo

## Quando usare cosa

| Strumento | Caso d'uso |
|---|---|
| `cron` | Task ricorrenti semplici, singolo server |
| `at` | Esecuzione una tantum pianificata |
| `anacron` | Server non sempre acceso |
| `systemd timer` | Task con dipendenze o logging avanzato |
| `Ansible` | Automazione multi-server, infrastruttura come codice |

## Ansible comandi essenziali

```bash
# Test connettività
ansible all -m ping

# Comandi ad-hoc
ansible host -m shell -a "comando"
ansible host -m package -a "name=nginx state=present" --become

# Playbook
ansible-playbook playbook.yml --check    # dry-run
ansible-playbook playbook.yml           # esegui

# Vault
ansible-vault create secrets.yml
ansible-playbook --ask-vault-pass playbook.yml
```

## Prossimi passi

- `tutorial_linux_31_ansible.md` — Ansible guida operativa completa
- `tutorial_linux_22_troubleshooting.md` — diagnostica sistema avanzata
