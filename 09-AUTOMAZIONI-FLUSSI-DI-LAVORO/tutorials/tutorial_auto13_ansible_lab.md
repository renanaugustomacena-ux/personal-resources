# Tutorial Lab — Ansible: Automazione Infrastruttura Agentless

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `13-ansible-automazione-infrastruttura.md`
> **Livello:** intermediate → advanced
> **Tempo stimato:** 3-4 ore (lab completo)
> **Prerequisiti:** SSH key-based auth, Linux bash base, YAML syntax, concetti networking
> **Versioni di riferimento:** Ansible 9.x (core 2.16+) · Python 3.11+ · Docker per lab locale

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Configurare un inventory statico e dinamico per gestire più host
2. Scrivere playbook idempotenti con handlers, tags e condizioni
3. Strutturare roles riutilizzabili con defaults, templates e handlers
4. Usare Ansible Vault per gestire segreti senza hard-code
5. Testare playbook in container Docker con ansible-test o Molecule
6. Applicare best practice: idempotenza, check mode, diff mode, limit

---

## Lab Environment Setup

```bash
# Prerequisiti
python3 --version       # 3.11+
ansible --version       # 9.x / core 2.16+
docker compose version  # 2.x (per container target del lab)

# Installa Ansible se mancante
pip install ansible==9.6.0 ansible-lint==24.5.0

# Avvia container target (simula 3 server Linux)
cat > docker-compose-lab.yml << 'EOF'
version: "3.9"
services:
  server-web:
    image: ubuntu:22.04
    container_name: server-web
    command: ["sleep", "infinity"]
    networks: [ansible-lab]
  server-db:
    image: ubuntu:22.04
    container_name: server-db
    command: ["sleep", "infinity"]
    networks: [ansible-lab]
  server-monitor:
    image: ubuntu:22.04
    container_name: server-monitor
    command: ["sleep", "infinity"]
    networks: [ansible-lab]
networks:
  ansible-lab:
    driver: bridge
EOF

docker compose -f docker-compose-lab.yml up -d

# Struttura progetto
mkdir -p ansible-lab/{inventory,playbooks,roles,vault}
cd ansible-lab
```

---

## Analogia Introduttiva

> **Ansible è come un'istruzione da seguire per un cuoco**:
> Descrivi lo stato del piatto che vuoi ottenere (idempotente),
> non la sequenza di azioni (imperativo).
> "Il server deve avere Nginx installato e in running"
> Non: "Installa Nginx, poi avvialo, poi verifica".
>
> L'approccio **agentless** significa che Ansible
> si connette via SSH al server remoto, esegue Python,
> e poi se ne va. Non c'è nessun daemon da installare,
> nessun agent da aggiornare.
>
> I **roles** sono ricette standard riutilizzabili:
> "Configura un web server" → stessa ricetta su tutti i server web,
> parametrizzata per ambiente (dev, staging, prod).
> Una volta scritto il role, usi `include_role` ovunque.

---

## Architettura Ansible

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CONTROL NODE (laptop/CI)                         │
│                                                                       │
│  ansible-playbook site.yml                                           │
│       │                                                               │
│  ┌────▼────────────────────────────────────────────────────────┐     │
│  │               PLAYBOOK                                       │     │
│  │                                                               │     │
│  │  Inventory ──▶ Host groups ──▶ Roles ──▶ Tasks ──▶ Modules │     │
│  │  (chi)         (raggruppati)   (come)    (cosa)   (azione)  │     │
│  └────┬──────────────────────────────────────────────────────-─┘     │
│       │                                                               │
│       │  SSH (port 22, key auth)                                     │
└───────┼───────────────────────────────────────────────────────────--─┘
        │
        ├─────── ▶ server-web   (installa nginx, deploy app)
        ├─────── ▶ server-db    (installa postgres, configura)
        └─────── ▶ server-monitor (installa prometheus, grafana)

STRUTTURA PROGETTO:
ansible-lab/
├── ansible.cfg              ← configurazione globale
├── inventory/
│   ├── hosts.ini            ← inventory statico
│   └── dynamic_aws.py       ← inventory dinamico (script)
├── playbooks/
│   ├── site.yml             ← playbook master
│   ├── webservers.yml
│   └── databases.yml
├── roles/
│   ├── common/              ← role base (tutti i server)
│   ├── nginx/               ← role nginx
│   └── postgresql/          ← role postgresql
└── vault/
    └── secrets.yml.enc      ← segreti cifrati con Vault
```

---

## PART A — Inventory e Configurazione Base

### A1 — ansible.cfg

```ini
# file: ansible.cfg
[defaults]
inventory       = inventory/hosts.ini
remote_user     = ansible
private_key_file = ~/.ssh/ansible_lab_key
host_key_checking = False        # Solo lab! In prod: True
forks           = 10             # Esecuzione parallela su max 10 host
timeout         = 30
gather_subset   = min            # Raccoglie solo info essenziali (più veloce)
callback_whitelist = profile_tasks  # Mostra tempo di ogni task

[privilege_escalation]
become          = True
become_method   = sudo
become_user     = root

[ssh_connection]
pipelining      = True           # Riduce connessioni SSH (più veloce)
ssh_args        = -o ControlMaster=auto -o ControlPersist=60s
```

### A2 — Inventory Statico

```ini
# file: inventory/hosts.ini
# Inventory statico: produzione stabile con IP fissi
# Per infrastruttura dinamica (cloud): usa inventory dinamico

# ─── Gruppi Host ───────────────────────────────────────────────────
[webservers]
server-web   ansible_host=server-web   ansible_connection=docker

[databases]
server-db    ansible_host=server-db    ansible_connection=docker

[monitoring]
server-monitor ansible_host=server-monitor ansible_connection=docker

# ─── Gruppo composito ─────────────────────────────────────────────
[production:children]
webservers
databases
monitoring

# ─── Variabili gruppo ─────────────────────────────────────────────
[webservers:vars]
nginx_port=80
nginx_worker_processes=auto
app_env=production

[databases:vars]
postgres_port=5432
postgres_max_connections=100

[production:vars]
# Variabili comuni a tutti i server in production
ntp_server=pool.ntp.org
log_retention_days=90
monitoring_enabled=true
```

### A3 — Inventory Dinamico (AWS/GCP)

```python
#!/usr/bin/env python3
# file: inventory/dynamic_aws.py
"""
Inventory dinamico per AWS EC2.
Ansible esegue questo script con --list o --host HOSTNAME.
Output: JSON con struttura inventory.

In produzione usare i plugin ufficiali:
  amazon.aws.aws_ec2 (comunità AWS)
  google.cloud.gcp_compute (GCP)
"""
from __future__ import annotations

import json
import sys
import os
from typing import Any


def fetch_aws_instances() -> list[dict]:
    """
    In produzione: boto3.client('ec2').describe_instances()
    Qui: dati di esempio statici per il lab.
    """
    return [
        {"id": "i-web-001", "ip": "10.0.1.10", "tags": {"Role": "web", "Env": "prod"}},
        {"id": "i-web-002", "ip": "10.0.1.11", "tags": {"Role": "web", "Env": "prod"}},
        {"id": "i-db-001",  "ip": "10.0.2.10", "tags": {"Role": "db",  "Env": "prod"}},
    ]


def genera_inventory() -> dict[str, Any]:
    """Genera inventory JSON nel formato atteso da Ansible."""
    instances = fetch_aws_instances()
    
    inventory: dict[str, Any] = {
        "_meta": {"hostvars": {}},
        "all": {"children": ["webservers", "databases"]},
        "webservers": {"hosts": [], "vars": {"nginx_port": 80}},
        "databases": {"hosts": [], "vars": {"postgres_port": 5432}},
    }
    
    for inst in instances:
        hostname = inst["id"]
        role = inst["tags"].get("Role", "unknown")
        
        # Aggiungi all'inventory
        if role == "web":
            inventory["webservers"]["hosts"].append(hostname)
        elif role == "db":
            inventory["databases"]["hosts"].append(hostname)
        
        # Variabili host specifiche
        inventory["_meta"]["hostvars"][hostname] = {
            "ansible_host": inst["ip"],
            "aws_instance_id": inst["id"],
            "aws_env": inst["tags"].get("Env", "unknown"),
        }
    
    return inventory


if __name__ == "__main__":
    if "--list" in sys.argv:
        print(json.dumps(genera_inventory(), indent=2))
    elif "--host" in sys.argv and len(sys.argv) > 2:
        hostname = sys.argv[2]
        inventory = genera_inventory()
        hostvars = inventory["_meta"]["hostvars"].get(hostname, {})
        print(json.dumps(hostvars, indent=2))
    else:
        print(json.dumps({}))
```

---

## PART B — Playbook e Roles

### B1 — Playbook Master

```yaml
# file: playbooks/site.yml
---
# Playbook master: eseguito da CI/CD o manualmente
# ansible-playbook playbooks/site.yml
# ansible-playbook playbooks/site.yml --limit webservers   ← solo web server
# ansible-playbook playbooks/site.yml --tags config         ← solo task con tag "config"
# ansible-playbook playbooks/site.yml --check --diff        ← dry run

- name: Configurazione base tutti i server
  hosts: production
  gather_facts: true
  become: true
  
  roles:
    - role: common       # Installazione base: aggiornamenti, utenti, sysctl
      tags: [common]
  
  vars_files:
    - ../vault/secrets.yml  # Segreti decifrati a runtime con --ask-vault-pass

- name: Deploy web server
  hosts: webservers
  gather_facts: true
  become: true
  
  vars:
    nginx_config_template: "nginx.conf.j2"
    app_version: "{{ lookup('env', 'APP_VERSION') | default('1.0.0') }}"
  
  roles:
    - role: nginx
      tags: [nginx, web]
    - role: app_deploy
      tags: [app, deploy]

- name: Configura database
  hosts: databases
  gather_facts: true
  become: true
  serial: 1  # Un host alla volta — rolling update database!
  
  roles:
    - role: postgresql
      tags: [postgresql, db]
```

### B2 — Role Common (Struttura Standard)

```
roles/common/
├── defaults/
│   └── main.yml          ← variabili con valori default (override in group_vars)
├── files/
│   └── sudoers_ansible   ← file statici copiati as-is
├── handlers/
│   └── main.yml          ← handler: eseguiti solo se "notificati"
├── meta/
│   └── main.yml          ← dipendenze del role
├── tasks/
│   ├── main.yml          ← entry point tasks
│   ├── users.yml
│   ├── sysctl.yml
│   └── packages.yml
├── templates/
│   └── sshd_config.j2    ← Jinja2 templates
└── vars/
    └── main.yml           ← variabili NON override (costanti del role)
```

```yaml
# file: roles/common/defaults/main.yml
---
# Valori di default — overridabili in inventory, group_vars, host_vars
common_packages:
  - vim
  - curl
  - wget
  - htop
  - git
  - unzip
  - ca-certificates
  - ntp

common_sysctl:
  net.ipv4.ip_forward: 0
  net.core.somaxconn: 1024
  vm.swappiness: 10
  fs.file-max: 65536

ansible_user_name: ansible
ansible_user_groups: [sudo]
ssh_permit_root_login: "no"
ssh_password_authentication: "no"
```

```yaml
# file: roles/common/tasks/main.yml
---
- name: Aggiorna cache apt
  ansible.builtin.apt:
    update_cache: true
    cache_valid_time: 3600  # Non riesegue se cache < 1h (idempotente)
  tags: [packages]

- name: Installa pacchetti comuni
  ansible.builtin.apt:
    name: "{{ common_packages }}"
    state: present
  tags: [packages]

- name: Configura sysctl
  ansible.posix.sysctl:
    name: "{{ item.key }}"
    value: "{{ item.value }}"
    state: present
    reload: true
  loop: "{{ common_sysctl | dict2items }}"
  tags: [sysctl]

- name: Crea utente ansible
  ansible.builtin.user:
    name: "{{ ansible_user_name }}"
    groups: "{{ ansible_user_groups }}"
    shell: /bin/bash
    create_home: true
    state: present
  tags: [users]

- name: Configura SSH
  ansible.builtin.template:
    src: sshd_config.j2
    dest: /etc/ssh/sshd_config
    owner: root
    group: root
    mode: "0644"
    validate: /usr/sbin/sshd -t -f %s  # Valida prima di applicare!
  notify: Restart sshd
  tags: [ssh, config]

- name: Imposta timezone
  community.general.timezone:
    name: "Europe/Rome"
  tags: [time]
```

```yaml
# file: roles/common/handlers/main.yml
---
# Handler: eseguiti UNA SOLA VOLTA alla fine del play, SOLO se notificati
# Se 5 task notificano "Restart sshd", il restart avviene una sola volta

- name: Restart sshd
  ansible.builtin.service:
    name: sshd
    state: restarted
  # listen permette più notify → stesso handler con nomi diversi
  listen: "restart ssh"
```

```jinja2
{# file: roles/common/templates/sshd_config.j2 #}
{# Jinja2 template per sshd_config #}
# Managed by Ansible — Do not edit manually
# Generated from roles/common/templates/sshd_config.j2

Port 22
PermitRootLogin {{ ssh_permit_root_login }}
PasswordAuthentication {{ ssh_password_authentication }}
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys

# Sicurezza
Protocol 2
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2

# Restrizioni
AllowUsers {{ ansible_user_name }} {% if extra_ssh_users is defined %}{{ extra_ssh_users | join(' ') }}{% endif %}

# Logging
SyslogFacility AUTH
LogLevel INFO
```

### B3 — Role Nginx

```yaml
# file: roles/nginx/tasks/main.yml
---
- name: Installa Nginx
  ansible.builtin.apt:
    name: nginx
    state: present
  notify: Restart nginx

- name: Rimuovi configurazione default
  ansible.builtin.file:
    path: /etc/nginx/sites-enabled/default
    state: absent
  notify: Reload nginx

- name: Configura nginx principale
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    owner: root
    group: root
    mode: "0644"
    validate: nginx -t -c %s
  notify: Reload nginx
  tags: [config]

- name: Configura virtual host
  ansible.builtin.template:
    src: vhost.conf.j2
    dest: "/etc/nginx/sites-available/{{ item.name }}.conf"
    mode: "0644"
  loop: "{{ nginx_vhosts }}"
  notify: Reload nginx
  tags: [config]

- name: Abilita virtual host
  ansible.builtin.file:
    src: "/etc/nginx/sites-available/{{ item.name }}.conf"
    dest: "/etc/nginx/sites-enabled/{{ item.name }}.conf"
    state: link
  loop: "{{ nginx_vhosts }}"
  notify: Reload nginx

- name: Assicura nginx in running e abilitato
  ansible.builtin.service:
    name: nginx
    state: started
    enabled: true

- name: Apri porta 80 nel firewall
  community.general.ufw:
    rule: allow
    port: "{{ nginx_port | string }}"
    proto: tcp
  when: ufw_enabled | default(false)
  tags: [firewall]

# ─── Verifica ─────────────────────────────────────────────────────────────────
- name: Verifica nginx risponde
  ansible.builtin.uri:
    url: "http://localhost:{{ nginx_port }}"
    status_code: [200, 301, 302]
    timeout: 5
  register: nginx_check
  retries: 3
  delay: 2
  tags: [verify]
```

---

## PART C — Ansible Vault

### C1 — Gestione Segreti con Vault

```bash
# ─── Creazione e gestione ────────────────────────────────────────────────────

# Crea nuovo file cifrato
ansible-vault create vault/secrets.yml
# Editor si apre — inserisci le variabili sensibili

# Cifrare file esistente
ansible-vault encrypt vault/secrets.yml

# Visualizza contenuto (richiede password)
ansible-vault view vault/secrets.yml

# Modifica (decifratura temporanea)
ansible-vault edit vault/secrets.yml

# Cifra singola stringa (per usare inline in playbook)
ansible-vault encrypt_string 'SuperSecret123!' --name 'db_password'
# Output:
# db_password: !vault |
#   $ANSIBLE_VAULT;1.1;AES256
#   66386439363...

# Esegui playbook con vault
ansible-playbook site.yml --ask-vault-pass
# In CI/CD: usa --vault-password-file o $ANSIBLE_VAULT_PASSWORD_FILE
```

```yaml
# file: vault/secrets.yml (PRIMA della cifratura)
---
# QUESTO FILE VA CIFRATO con: ansible-vault encrypt vault/secrets.yml
# NON committare la versione in chiaro!

db_root_password: "{{ vault_db_root_password }}"
db_app_password: "{{ vault_db_app_password }}"
api_key_monitoring: "{{ vault_api_key_monitoring }}"
smtp_password: "{{ vault_smtp_password }}"

# Pattern consigliato: variabile vault_ privata + variabile pubblica
# Le variabili pubbliche sono in group_vars/ (senza segreti)
# Le variabili vault_ sono solo in questo file cifrato
```

```yaml
# file: group_vars/production/vars.yml (pubblico, non cifrato)
---
db_host: "db.internal"
db_port: 5432
db_name: "produzione"
db_user: "app"
# db_password: definito in vault/secrets.yml come vault_db_app_password
# In playbook: usa db_password che fa riferimento a vault_db_app_password
```

### C2 — Password File per CI/CD

```bash
# In CI/CD (es. GitLab CI, GitHub Actions):
# Salva la password del vault come secret della CI
# poi crea il file password al runtime

# .github/workflows/deploy.yml (snippet)
# - name: Create vault password file
#   run: echo "$ANSIBLE_VAULT_PASS" > ~/.vault_pass && chmod 600 ~/.vault_pass
#   env:
#     ANSIBLE_VAULT_PASS: ${{ secrets.ANSIBLE_VAULT_PASS }}
#
# - name: Deploy
#   run: ansible-playbook site.yml --vault-password-file ~/.vault_pass

# Alternativa: AWS Secrets Manager, HashiCorp Vault (enterprise)
# Plugin: community.hashi_vault.hashi_vault_kv2_get
```

---

## PART D — Testing con Molecule

### D1 — Setup Molecule

```bash
pip install molecule==6.0.0 molecule-docker==2.1.0

# Inizializza molecule nel role
cd roles/nginx
molecule init scenario --driver-name docker

# Struttura creata:
# molecule/default/
# ├── converge.yml     ← applica il role
# ├── molecule.yml     ← configurazione driver/piattaforme
# ├── verify.yml       ← verifica post-applicazione
# └── prepare.yml      ← setup pre-role (opzionale)
```

```yaml
# file: roles/nginx/molecule/default/molecule.yml
---
dependency:
  name: galaxy
driver:
  name: docker
platforms:
  - name: instance-ubuntu22
    image: "geerlingguy/docker-ubuntu2204-ansible:latest"
    pre_build_image: true
    command: ""
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host
    privileged: true  # Necessario per systemd nei container
  
  - name: instance-ubuntu20
    image: "geerlingguy/docker-ubuntu2004-ansible:latest"
    pre_build_image: true
    command: ""

provisioner:
  name: ansible
  config_options:
    defaults:
      callback_whitelist: profile_tasks
  inventory:
    host_vars:
      instance-ubuntu22:
        nginx_port: 80
        nginx_vhosts:
          - name: test-site
            server_name: test.local
            root: /var/www/html

verifier:
  name: ansible
```

```yaml
# file: roles/nginx/molecule/default/verify.yml
---
- name: Verifica nginx
  hosts: all
  become: true
  tasks:
    - name: Verifica nginx è running
      ansible.builtin.service_facts:
    
    - name: Assert nginx attivo
      ansible.builtin.assert:
        that:
          - "'nginx' in services"
          - "services['nginx']['state'] == 'running'"
          - "services['nginx']['status'] == 'enabled'"
        fail_msg: "Nginx non è running o non è abilitato"
    
    - name: Verifica porta 80 aperta
      ansible.builtin.wait_for:
        port: 80
        timeout: 10
    
    - name: Verifica risposta HTTP 200
      ansible.builtin.uri:
        url: "http://localhost:80"
        status_code: [200, 301]
      register: result
    
    - name: Assert status code valido
      ansible.builtin.assert:
        that: result.status in [200, 301]
```

```bash
# Comandi Molecule
molecule converge   # Applica il role nel container
molecule verify     # Esegui i test di verifica
molecule test       # Ciclo completo: create → prepare → converge → verify → destroy
molecule destroy    # Rimuovi i container
molecule lint       # ansible-lint sul role
```

---

## Esercizi

### Esercizio 1 — Playbook Check Mode (10 min)

```bash
# Esegui il playbook in dry-run (nessun cambiamento reale)
# --check: simula l'esecuzione
# --diff: mostra le differenze per file/template

ansible-playbook playbooks/site.yml \
  --check \
  --diff \
  --limit server-web

# Atteso: vedi cosa cambierebbe senza cambiare nulla
```

### Esercizio 2 — Role Postgresql (45 min)

Crea `roles/postgresql/` con:
- Task: installa postgresql-16, configura pg_hba.conf, crea database e utente
- Template: postgresql.conf.j2 con variabili (max_connections, shared_buffers)
- Handler: reload postgresql
- Molecule test: verifica che l'utente possa connettersi

```yaml
# Hint: tasks principali
- name: Installa PostgreSQL 16
  ansible.builtin.apt:
    name: [postgresql-16, postgresql-contrib, python3-psycopg2]
    state: present

- name: Crea database applicazione
  community.postgresql.postgresql_db:
    name: "{{ db_name }}"
    state: present
  become_user: postgres

- name: Crea utente database
  community.postgresql.postgresql_user:
    name: "{{ db_user }}"
    password: "{{ db_password }}"  # Da vault!
    db: "{{ db_name }}"
    priv: ALL
  become_user: postgres
  no_log: true  # Non loggare la password!
```

### Esercizio 3 — Inventory Dinamico da Docker (30 min)

Scrivi un inventory dinamico che interroga Docker locale:
```python
import docker
import json, sys

def main():
    client = docker.from_env()
    containers = client.containers.list()
    inventory = {"_meta": {"hostvars": {}}, "all": {"hosts": []}}
    for c in containers:
        name = c.name
        inventory["all"]["hosts"].append(name)
        inventory["_meta"]["hostvars"][name] = {
            "ansible_connection": "docker",
            "ansible_host": name,
        }
    print(json.dumps(inventory))

if "--list" in sys.argv:
    main()
```

---

## Script di Verifica Prerequisiti

```bash
#!/usr/bin/env bash
# file: verifica_prerequisiti.sh
set -euo pipefail

echo "Verifica prerequisiti Ansible Lab..."

check() {
    local nome="$1"
    local cmd="$2"
    if eval "$cmd" &>/dev/null; then
        echo "  [OK] $nome"
    else
        echo "  [FAIL] $nome"
        return 1
    fi
}

check "Python 3.11+" "python3 -c 'import sys; assert sys.version_info >= (3,11)'"
check "Ansible" "ansible --version"
check "ansible-lint" "ansible-lint --version"
check "Docker" "docker info"

# Verifica connettività container lab
for server in server-web server-db server-monitor; do
    if docker inspect "$server" &>/dev/null; then
        echo "  [OK] Container $server disponibile"
    else
        echo "  [WARN] Container $server non trovato — avvia docker-compose-lab.yml"
    fi
done

echo "Prerequisiti verificati!"
```

---

## Riferimenti

- Ansible Documentation: https://docs.ansible.com/
- Ansible Best Practices: https://docs.ansible.com/ansible/latest/tips_tricks/
- Molecule Testing Framework: https://ansible.readthedocs.io/projects/molecule/
- Ansible Galaxy Roles: https://galaxy.ansible.com/
- Modulo sorgente: `13-ansible-automazione-infrastruttura.md`
