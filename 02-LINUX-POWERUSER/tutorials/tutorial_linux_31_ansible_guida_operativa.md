# Tutorial Linux 31 — Ansible Guida Operativa: Roles, Molecule, AWX

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** Ansible roles, molecule testing, dynamic inventory, callback plugins, AWX/AAP
> **Prerequisiti:** `tutorial_linux_21_automazione.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Ansible Avanzato
│
├── Struttura
│   ├── Roles (task/handlers/vars/templates/defaults/meta)
│   ├── Collections (namespace.collection)
│   └── Galaxy (hub pacchetti)
│
├── Inventory
│   ├── Statico (ini/yaml)
│   ├── Dinamico (script/plugin)
│   └── Inventory plugins (aws_ec2, gcp_compute, azure_rm)
│
├── Testing
│   ├── Molecule (test roles)
│   ├── Testinfra (verifica stato)
│   └── ansible-lint (stile)
│
└── AWX / Automation Controller
    ├── Projects, Templates, Jobs
    ├── Credentials management
    ├── Surveys e webhook trigger
    └── RBAC
```

---

# Parte A — Role Structure

---

## A1. Creare un role

```bash
# Struttura standard role
ansible-galaxy role init my_role

# Struttura creata:
# my_role/
# ├── defaults/
# │   └── main.yml      # variabili con priorità bassa (override facile)
# ├── vars/
# │   └── main.yml      # variabili con priorità alta (non override)
# ├── tasks/
# │   └── main.yml      # task principali
# ├── handlers/
# │   └── main.yml      # handler per notify
# ├── templates/
# │   └── *.j2          # template Jinja2
# ├── files/
# │   └── *             # file statici da copiare
# ├── meta/
# │   └── main.yml      # dipendenze da altri role
# └── README.md
```

```yaml
# roles/nginx/defaults/main.yml
nginx_worker_processes: auto
nginx_worker_connections: 1024
nginx_server_name: "{{ inventory_hostname }}"
nginx_root: /var/www/html
nginx_ssl: false
nginx_ssl_certificate: ""
nginx_ssl_key: ""

# roles/nginx/tasks/main.yml
---
- name: Includi task per OS specifico
  include_tasks: "{{ ansible_os_family | lower }}.yml"

- name: Abilita e avvia nginx
  systemd:
    name: nginx
    enabled: true
    state: started
  notify: reload nginx
```

```yaml
# roles/nginx/tasks/debian.yml
---
- name: Installa nginx (Debian/Ubuntu)
  apt:
    name: nginx
    state: present
    update_cache: true
  tags: [install]

- name: Deploy configurazione nginx
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    owner: root
    group: root
    mode: '0644'
    validate: nginx -t -c %s
  notify: reload nginx
  tags: [config]

- name: Deploy virtual host
  template:
    src: vhost.conf.j2
    dest: "/etc/nginx/sites-available/{{ nginx_server_name }}"
    mode: '0644'
  notify: reload nginx

- name: Abilita virtual host
  file:
    src: "/etc/nginx/sites-available/{{ nginx_server_name }}"
    dest: "/etc/nginx/sites-enabled/{{ nginx_server_name }}"
    state: link
  notify: reload nginx
```

```yaml
# roles/nginx/handlers/main.yml
---
- name: reload nginx
  systemd:
    name: nginx
    state: reloaded

- name: restart nginx
  systemd:
    name: nginx
    state: restarted
```

---

## A2. Role con dipendenze e meta

```yaml
# roles/webapp/meta/main.yml
galaxy_info:
  author: renan
  description: Deploy webapp Python
  license: MIT
  min_ansible_version: "2.14"
  platforms:
    - name: Ubuntu
      versions: ["22.04", "24.04"]

dependencies:
  - role: nginx
    vars:
      nginx_ssl: true
  - role: postgresql
    vars:
      pg_version: "16"
  - role: certbot
    when: nginx_ssl | bool
```

---

# Parte B — Dynamic Inventory

---

## B1. Inventory plugin AWS

```yaml
# inventory/aws.yml
plugin: aws_ec2
regions:
  - eu-west-1
  - eu-central-1

filters:
  "tag:Environment": production
  instance-state-name: running

keyed_groups:
  - key: tags.Role
    prefix: role
  - key: placement.region
    prefix: region

compose:
  ansible_host: public_ip_address
  ansible_user: "'ubuntu'"

# Usa
ansible-inventory -i inventory/aws.yml --list
ansible-inventory -i inventory/aws.yml --graph
ansible all -i inventory/aws.yml -m ping
```

---

## B2. Inventory script custom

```python
#!/usr/bin/env python3
# inventory/dynamic.py
"""Inventory dinamico da API interna o CMDB"""

import json
import sys
import httpx

def get_inventory():
    # Chiama API interna o database
    response = httpx.get("https://cmdb.interno/api/hosts", 
                         headers={"Authorization": "Bearer TOKEN"})
    hosts = response.json()

    inventory = {
        "_meta": {"hostvars": {}},
        "all": {"children": ["ungrouped"]},
    }

    for host in hosts:
        group = f"role_{host['role']}"
        env_group = f"env_{host['environment']}"

        # Aggiungi gruppi
        for g in [group, env_group]:
            if g not in inventory:
                inventory[g] = {"hosts": []}
            inventory[g]["hosts"].append(host["hostname"])
            if "all" in inventory and "children" in inventory["all"]:
                if g not in inventory["all"]["children"]:
                    inventory["all"]["children"].append(g)

        # Variabili per host
        inventory["_meta"]["hostvars"][host["hostname"]] = {
            "ansible_host": host["ip"],
            "ansible_user": host.get("ssh_user", "ubuntu"),
            "datacenter": host["datacenter"],
            "app_port": host.get("app_port", 8000),
        }

    return inventory

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        print(json.dumps(get_inventory()))
    elif len(sys.argv) == 3 and sys.argv[1] == "--host":
        # Già incluso in _meta
        print(json.dumps({}))
    else:
        sys.exit(1)
```

```bash
chmod +x inventory/dynamic.py
ansible -i inventory/dynamic.py all -m ping
```

---

# Parte C — Molecule Testing

---

## C1. Testing role con Molecule

```bash
# Installa Molecule con driver Docker
pip install molecule molecule-plugins[docker] pytest-testinfra ansible-lint

# Inizializza Molecule in un role esistente
cd roles/nginx
molecule init scenario

# Struttura creata:
# molecule/default/
# ├── molecule.yml     # configurazione scenario
# ├── converge.yml     # playbook di applicazione
# ├── verify.yml       # playbook di verifica
# └── prepare.yml      # (opzionale) preparazione
```

```yaml
# molecule/default/molecule.yml
---
dependency:
  name: galaxy

driver:
  name: docker

platforms:
  - name: ubuntu-22.04
    image: "geerlingguy/docker-ubuntu2204-ansible:latest"
    pre_build_image: true
    command: ""
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host
    privileged: true   # per systemd

  - name: ubuntu-24.04
    image: "geerlingguy/docker-ubuntu2404-ansible:latest"
    pre_build_image: true
    command: ""
    privileged: true

provisioner:
  name: ansible
  playbooks:
    converge: converge.yml
    verify: verify.yml
  config_options:
    defaults:
      callbacks_enabled: profile_tasks

verifier:
  name: ansible
```

```yaml
# molecule/default/converge.yml
---
- name: Converge
  hosts: all
  become: true
  vars:
    nginx_server_name: test.local
    nginx_ssl: false

  roles:
    - role: nginx
```

```yaml
# molecule/default/verify.yml
---
- name: Verify
  hosts: all
  become: true
  tasks:
    - name: Verifica nginx in esecuzione
      systemd:
        name: nginx
      register: nginx_status
      failed_when: nginx_status.status.ActiveState != "active"

    - name: Verifica porta 80 in ascolto
      wait_for:
        host: localhost
        port: 80
        timeout: 5

    - name: Verifica risposta HTTP
      uri:
        url: http://localhost/
        status_code: [200, 301, 302]
      register: http_response

    - name: Verifica configurazione nginx
      command: nginx -t
      changed_when: false
```

```bash
# Esegui test
molecule test                   # full cycle: create→converge→verify→destroy
molecule converge               # solo converge (no destroy, per debug)
molecule verify                 # solo verify
molecule destroy                # pulisci container
molecule login                  # shell nel container
```

---

# Parte D — Playbook Avanzati

---

## D1. Patterns avanzati

```yaml
# site.yml — orchestrazione completa
---
- import_playbook: playbooks/infra.yml
- import_playbook: playbooks/database.yml
- import_playbook: playbooks/app.yml

# playbooks/app.yml
---
- name: Deploy applicazione
  hosts: role_webapp
  become: true
  serial: "30%"    # rolling deploy — 30% degli host alla volta
  max_fail_percentage: 20  # se >20% fallisce, stop

  pre_tasks:
    - name: Rimuovi host da load balancer
      uri:
        url: "https://lb.interno/api/drain/{{ inventory_hostname }}"
        method: POST
      delegate_to: localhost

    - name: Attendi drain completo
      pause:
        seconds: 30

  roles:
    - webapp

  post_tasks:
    - name: Verifica health check
      uri:
        url: "http://{{ ansible_host }}:8000/health"
        status_code: 200
      retries: 10
      delay: 5
      register: health_check
      until: health_check.status == 200

    - name: Riabilita nel load balancer
      uri:
        url: "https://lb.interno/api/enable/{{ inventory_hostname }}"
        method: POST
      delegate_to: localhost
```

```yaml
# Callback plugin in ansible.cfg
[defaults]
callbacks_enabled = profile_tasks, timer, yaml

# Output più leggibile e con timing
# TASK [nginx : Installa nginx] *** 0:00:03.456
```

---

## D2. Vault e gestione segreti

```bash
# Crea file vault
ansible-vault create group_vars/all/vault.yml

# Contenuto (nell'editor che si apre):
# vault_db_password: "password_super_sicura"
# vault_api_key: "chiave_api_segreta"

# Cifra file esistente
ansible-vault encrypt group_vars/all/secrets.yml

# Visualizza senza decifrare su disco
ansible-vault view group_vars/all/vault.yml

# Modifica
ansible-vault edit group_vars/all/vault.yml

# Esegui playbook con vault
ansible-playbook site.yml --ask-vault-pass
ansible-playbook site.yml --vault-password-file ~/.vault_pass

# Vault ID (multiple password file)
ansible-vault create --vault-id prod@~/.vault_prod secrets.yml
ansible-playbook site.yml --vault-id prod@~/.vault_prod
```

---

# Parte E — AWX / Automation Controller

---

## E1. AWX installazione e concetti

```bash
# AWX via Operator (Kubernetes)
kubectl create namespace awx
kubectl apply -k github.com/ansible/awx-operator/config/default

cat > awx-instance.yml << 'EOF'
apiVersion: awx.ansible.com/v1beta1
kind: AWX
metadata:
  name: awx
  namespace: awx
spec:
  service_type: LoadBalancer
  ingress_type: ingress
  hostname: awx.esempio.it
EOF

kubectl apply -f awx-instance.yml

# Recupera password admin
kubectl get secret awx-admin-password -n awx \
    -o jsonpath='{.data.password}' | base64 -d
```

```bash
# awxkit — CLI per AWX
pip install awxkit

export TOWER_HOST=https://awx.esempio.it
export TOWER_USERNAME=admin
export TOWER_PASSWORD=password

awx login
awx jobs list         # lista job
awx job_templates list  # lista template

# Lancia un job template via CLI
awx job_templates launch --id 42 \
    --extra_vars '{"app_version": "1.2.3"}' \
    --wait

# Trigger via webhook (Token in AWX → Template → Enable Webhook)
curl -X POST \
    -H "Authorization: Bearer WEBHOOK_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"extra_vars": {"deploy_env": "production"}}' \
    https://awx.esempio.it/api/v2/job_templates/42/launch/
```

---

## Riepilogo

## Struttura progetto Ansible

```
progetto/
├── ansible.cfg
├── site.yml
├── inventory/
│   ├── production/
│   │   ├── hosts.yml
│   │   └── group_vars/
│   └── staging/
│       ├── hosts.yml
│       └── group_vars/
├── playbooks/
│   ├── deploy.yml
│   └── maintenance.yml
├── roles/
│   ├── nginx/
│   ├── postgresql/
│   └── webapp/
└── collections/
    └── requirements.yml
```

## Comandi essenziali

| Comando | Scopo |
|---|---|
| `ansible all -m ping` | Test connettività |
| `ansible-playbook site.yml --check` | Dry run |
| `ansible-playbook site.yml --diff` | Mostra diff file modificati |
| `ansible-playbook site.yml --tags deploy` | Solo task con tag deploy |
| `ansible-lint site.yml` | Verifica stile |
| `molecule test` | Test completo role |
| `ansible-galaxy role install -r requirements.yml` | Installa role da Galaxy |

## Prossimi passi

- `tutorial_linux_32_vpn.md` — VPN con WireGuard
- `tutorial_linux_21_automazione.md` — Ansible basi
