---
corso: "Automazioni e Flussi di Lavoro"
fase: "2 — Scripting e Integrazione"
modulo: 13
titolo: "Ansible per l'Automazione dell'Infrastruttura — Guida Approfondita"
versione: "Ansible 9.x/10.x, ansible-core 2.16+, AWX/AAP 24+"
livello: "competent → proficient"
prerequisiti:
  - "Linux/SSH"
  - "YAML"
  - "Concetti config management"
obiettivi:
  - "Scrivere playbook idempotenti verificabili con esecuzioni ripetute"
  - "Organizzare automazioni in roles e collections riusabili e testabili"
  - "Gestire secrets con Ansible Vault integrato in pipeline CI/CD"
  - "Configurare inventory dinamici per ambienti cloud e ibridi"
  - "Deployare e operare AWX/AAP per gestione centralizzata dei playbook"
tag: [ansible, infrastruttura, playbook, roles, vault, awx, idempotenza, config-management]
---

# Ansible per l'Automazione dell'Infrastruttura — Guida Approfondita

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 3 — Piattaforme · Modulo 13
> **Prerequisiti:** Linux/SSH; YAML; concetti config management.
> **Obiettivi:** Ansible playbook idempotenti, roles, collections, vault, inventory dinamico, AAP/AWX.
> **Tempo:** lettura 90 min · lab 360 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-24
> **Versioni:** Ansible 9.x/10.x, ansible-core 2.16+, ansible-vault, AWX/AAP 24+.

## Idee guida

1. **Playbook idempotenti by design.** "Esegui 10 volte stesso playbook, stato finale identico."
2. **Roles > monolithic playbook.** Riusabilita, testing, sharing.
3. **Vault per secrets, no `--ask-pass`.** Vault password in CI da env var/secret manager.
4. **Inventory dinamico per scale.** AWS EC2, Azure VM, GCP via plugin nativi.
5. **Mai `gather_facts` se non servono.** Risparmia 10-30% del tempo execution.

---

## Indice

- [Panoramica](#panoramica)
- [Architettura e Concetti Fondamentali](#architettura-e-concetti-fondamentali)
- [Installazione e Configurazione Iniziale](#installazione-e-configurazione-iniziale)
- [Inventory Management](#inventory-management)
- [Dynamic Inventory: AWS e Azure](#dynamic-inventory-aws-e-azure)
- [Playbook: Struttura e Pattern](#playbook-struttura-e-pattern)
- [Moduli Essenziali](#moduli-essenziali)
- [Struttura dei Roles](#struttura-dei-roles)
- [Jinja2 Templates](#jinja2-templates)
- [Variabili: Precedenza e Organizzazione](#variabili-precedenza-e-organizzazione)
- [Ansible Vault](#ansible-vault)
- [Ansible Galaxy](#ansible-galaxy)
- [Pattern di Provisioning Server](#pattern-di-provisioning-server)
- [Configuration Management](#configuration-management)
- [Deployment di Applicazioni](#deployment-di-applicazioni)
- [AWX / Ansible Tower Overview](#awx--ansible-tower-overview)
- [Testing con Molecule](#testing-con-molecule)
- [Integrazione CI/CD](#integrazione-cicd)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

Ansible è uno strumento di automazione dell'infrastruttura open source, sviluppato originariamente da Michael DeHaan e oggi mantenuto da Red Hat. Si distingue dagli altri Configuration Management tools (Puppet, Chef, SaltStack) per la sua architettura agentless: non richiede l'installazione di alcun software sui nodi gestiti, utilizzando esclusivamente SSH (per Linux/Unix) o WinRM (per Windows) per comunicare con i target. Questa caratteristica elimina la necessità di gestire un'infrastruttura aggiuntiva di agenti, semplificando drasticamente l'adozione e riducendo la superficie di attacco.

Ansible opera secondo il principio dell'idempotenza: l'esecuzione ripetuta della stessa configurazione produce sempre lo stesso stato finale, senza effetti collaterali. Un playbook Ansible descrive lo stato desiderato dell'infrastruttura — non una sequenza di comandi — e il motore di Ansible calcola le azioni necessarie per raggiungere quello stato. Se il sistema è già nello stato desiderato, Ansible non apporta modifiche (riportando "ok" anziché "changed").

Il linguaggio di configurazione di Ansible è YAML, scelto per la sua leggibilità anche da parte di operatori non sviluppatori. I playbook Ansible possono essere versionati in Git, revisionati come codice, e trattati secondo le pratiche Infrastructure as Code (IaC). In questa guida esploreremo ogni aspetto di Ansible, dall'inventory management ai pattern di deployment avanzati, con esempi concreti e configurazioni pronte per la produzione.

---

## Architettura e Concetti Fondamentali

### Componenti

- **Control Node**: la macchina da cui si eseguono i comandi Ansible. Richiede Python 3.9+ e il pacchetto `ansible` installato. Può essere un laptop, un server di deployment, o un runner CI/CD.
- **Managed Nodes**: i server target gestiti da Ansible. Richiedono solo Python (2.7+ o 3.5+) e un'accessibilità SSH. Non necessitano di alcun software Ansible installato.
- **Inventory**: l'elenco dei managed nodes, organizzati in gruppi. Può essere un file statico (INI o YAML) o generato dinamicamente da un plugin.
- **Modules**: unità di lavoro eseguite sui managed nodes (es. `apt`, `copy`, `service`). Ansible include oltre 3.000 moduli nella distribuzione standard.
- **Plugins**: estendono le funzionalità di Ansible (connection plugins, callback plugins, lookup plugins, filter plugins).
- **Playbook**: file YAML che descrive una serie di "play" — associazioni tra un gruppo di host e una serie di task da eseguire.
- **Role**: struttura organizzativa che raggruppa task, handler, variabili, template e file correlati in un'unità riutilizzabile.

### Flusso di Esecuzione

```
Control Node                           Managed Node
    │                                       │
    ├── 1. Legge inventory                  │
    ├── 2. Legge playbook                   │
    ├── 3. Per ogni task:                   │
    │   ├── Genera modulo Python            │
    │   ├── Copia modulo via SSH ──────────►│
    │   │                                   ├── Esegue modulo
    │   │                                   ├── Restituisce JSON
    │   ◄── Riceve risultato ◄──────────────┤
    │   └── Registra changed/ok/failed      │
    └── 4. Esegue handlers se notificati    │
```

Ansible genera dinamicamente piccoli script Python per ogni modulo, li trasferisce ai managed nodes via SSH (tramite il modulo `sftp` o `scp`), li esegue remotamente, e raccoglie l'output JSON. Questo processo si chiama "module execution pipeline".

---

## Installazione e Configurazione Iniziale

### Installazione

```bash
# Via pip (raccomandato per la versione più aggiornata)
python3 -m pip install --user ansible

# Via package manager (Debian/Ubuntu)
sudo apt update
sudo apt install -y ansible

# Via package manager (RHEL/CentOS/Fedora)
sudo dnf install -y ansible

# Verifica
ansible --version
```

### Configurazione: ansible.cfg

Il file di configurazione `ansible.cfg` controlla il comportamento globale di Ansible. La ricerca avviene in quest'ordine di precedenza:

1. `ANSIBLE_CONFIG` (variabile di ambiente)
2. `./ansible.cfg` (directory corrente)
3. `~/.ansible.cfg` (home utente)
4. `/etc/ansible/ansible.cfg` (globale)

File di configurazione raccomandato per un progetto:

```ini
[defaults]
inventory = inventory/
roles_path = roles/
retry_files_enabled = False
host_key_checking = False
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts_cache
fact_caching_timeout = 86400
stdout_callback = yaml
callbacks_enabled = timer, profile_tasks

# Parallelismo
forks = 20
pipelining = True

# SSH
timeout = 30
remote_user = deploy

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o PreferredAuthentications=publickey
pipelining = True
```

L'opzione `pipelining = True` è un'ottimizzazione significativa: elimina la necessità di creare file temporanei sui managed nodes, eseguendo i moduli direttamente tramite la connessione SSH. Questo riduce la latenza di ogni task. Richiede che `requiretty` sia disabilitato nel sudoers dei managed nodes.

### SSH Key Setup

```bash
# Generare una SSH key dedicata per Ansible
ssh-keygen -t ed25519 -C "ansible@control-node" -f ~/.ssh/ansible_ed25519

# Distribuire la chiave ai managed nodes
ssh-copy-id -i ~/.ssh/ansible_ed25519.pub deploy@server1.example.com
ssh-copy-id -i ~/.ssh/ansible_ed25519.pub deploy@server2.example.com

# Verificare la connettività
ansible all -m ping
```

---

## Inventory Management

### Inventory Statico in Formato INI

```ini
# inventory/hosts.ini

[webservers]
web1.example.com ansible_host=10.0.1.10
web2.example.com ansible_host=10.0.1.11
web3.example.com ansible_host=10.0.1.12

[dbservers]
db-primary.example.com ansible_host=10.0.2.10
db-replica.example.com ansible_host=10.0.2.11

[loadbalancers]
lb1.example.com ansible_host=10.0.0.10

[production:children]
webservers
dbservers
loadbalancers

[production:vars]
ansible_user=deploy
ansible_ssh_private_key_file=~/.ssh/ansible_ed25519
environment=production
ntp_server=ntp.example.com
```

### Inventory Statico in Formato YAML

```yaml
# inventory/hosts.yml
all:
  children:
    production:
      children:
        webservers:
          hosts:
            web1.example.com:
              ansible_host: 10.0.1.10
              http_port: 8080
            web2.example.com:
              ansible_host: 10.0.1.11
              http_port: 8080
            web3.example.com:
              ansible_host: 10.0.1.12
              http_port: 8080
          vars:
            nginx_worker_processes: 4
        dbservers:
          hosts:
            db-primary.example.com:
              ansible_host: 10.0.2.10
              postgresql_role: primary
            db-replica.example.com:
              ansible_host: 10.0.2.11
              postgresql_role: replica
          vars:
            postgresql_version: "16"
      vars:
        ansible_user: deploy
        environment: production
```

### Organizzazione delle Variabili per Host e Gruppo

Ansible carica automaticamente le variabili da file YAML corrispondenti ai nomi degli host e dei gruppi:

```
inventory/
├── hosts.yml
├── group_vars/
│   ├── all.yml          # Variabili per tutti gli host
│   ├── production.yml   # Variabili per il gruppo production
│   ├── webservers.yml   # Variabili per il gruppo webservers
│   └── dbservers.yml    # Variabili per il gruppo dbservers
└── host_vars/
    ├── web1.example.com.yml  # Variabili specifiche per web1
    └── db-primary.example.com.yml
```

---

## Dynamic Inventory: AWS e Azure

### AWS Dynamic Inventory

Per ambienti AWS, Ansible può generare l'inventory dinamicamente dalle istanze EC2:

Plugin file `inventory/aws_ec2.yml`:

```yaml
plugin: amazon.aws.aws_ec2
regions:
  - eu-south-1
  - eu-west-1

filters:
  tag:Environment:
    - production
    - staging
  instance-state-name:
    - running

keyed_groups:
  - key: tags.Role
    prefix: role
    separator: "_"
  - key: tags.Environment
    prefix: env
  - key: placement.availability_zone
    prefix: az

hostnames:
  - tag:Name
  - private-ip-address

compose:
  ansible_host: private_ip_address
  ansible_user: "'ubuntu'"
```

### Azure Dynamic Inventory

Plugin file `inventory/azure_rm.yml`:

```yaml
plugin: azure.azcollection.azure_rm
auth_source: auto

include_vm_resource_groups:
  - production-rg
  - staging-rg

keyed_groups:
  - key: tags.role | default('untagged')
    prefix: role
  - key: tags.environment | default('unknown')
    prefix: env
  - key: location
    prefix: location

hostnames:
  - tag:Name
  - default

compose:
  ansible_host: private_ipv4_addresses[0] if private_ipv4_addresses else public_ip_address
```

Installazione delle collection necessarie:

```bash
ansible-galaxy collection install amazon.aws
ansible-galaxy collection install azure.azcollection

# Dipendenze Python
pip install boto3 botocore  # per AWS
pip install azure-identity azure-mgmt-compute azure-mgmt-network  # per Azure
```

---

## Playbook: Struttura e Pattern

### Struttura Base

```yaml
---
# playbooks/site.yml - Playbook principale
- name: Configurazione webserver
  hosts: webservers
  become: true
  gather_facts: true
  vars:
    app_name: myapp
    app_port: 8080

  pre_tasks:
    - name: Aggiornare la cache dei pacchetti
      apt:
        update_cache: true
        cache_valid_time: 3600

  roles:
    - role: common
    - role: nginx
      vars:
        nginx_server_name: "{{ inventory_hostname }}"
    - role: app_deploy
      tags: [deploy]

  post_tasks:
    - name: Verificare che l'applicazione risponda
      uri:
        url: "http://localhost:{{ app_port }}/health"
        status_code: 200
      register: health_check
      retries: 5
      delay: 10
      until: health_check.status == 200

  handlers:
    - name: Reload nginx
      service:
        name: nginx
        state: reloaded
```

### Pattern: Rolling Update

Per aggiornare i server in modo graduale senza downtime:

```yaml
---
- name: Rolling update webserver
  hosts: webservers
  become: true
  serial: 1  # Un server alla volta
  max_fail_percentage: 0  # Zero tolerance per i fallimenti

  pre_tasks:
    - name: Rimuovere il server dal load balancer
      uri:
        url: "http://{{ lb_host }}/api/backends/{{ inventory_hostname }}"
        method: DELETE
      delegate_to: localhost

    - name: Attendere che il server si svuoti di connessioni attive
      wait_for:
        timeout: 30

  roles:
    - role: app_deploy

  post_tasks:
    - name: Verificare health check
      uri:
        url: "http://localhost:{{ app_port }}/health"
        status_code: 200
      retries: 10
      delay: 5
      register: result
      until: result.status == 200

    - name: Reinserire nel load balancer
      uri:
        url: "http://{{ lb_host }}/api/backends"
        method: POST
        body_format: json
        body:
          hostname: "{{ inventory_hostname }}"
          port: "{{ app_port }}"
      delegate_to: localhost
```

### Pattern: Canary Deployment

```yaml
---
# Deploy prima su un singolo server (canary)
- name: Canary deployment
  hosts: webservers[0]
  become: true
  roles:
    - role: app_deploy
      vars:
        app_version: "{{ new_version }}"

  post_tasks:
    - name: Health check post-deploy
      uri:
        url: "http://localhost:{{ app_port }}/health"
        status_code: 200
      retries: 10
      delay: 5

    - name: Attendere e monitorare il canary
      pause:
        minutes: 5
        prompt: "Canary deployment attivo. Verificare metriche e log. Premere ENTER per continuare o Ctrl+C per annullare."

# Se il canary passa, deploy sul resto
- name: Full deployment
  hosts: webservers:!webservers[0]
  become: true
  serial: "33%"
  roles:
    - role: app_deploy
      vars:
        app_version: "{{ new_version }}"
```

---

## Moduli Essenziali

### Gestione Pacchetti

```yaml
# APT (Debian/Ubuntu)
- name: Installare pacchetti
  apt:
    name:
      - nginx
      - python3-pip
      - postgresql-client
    state: present
    update_cache: true

- name: Rimuovere pacchetti non necessari
  apt:
    autoremove: true
    purge: true

# YUM/DNF (RHEL/CentOS/Fedora)
- name: Installare pacchetti con DNF
  dnf:
    name:
      - httpd
      - python3
      - postgresql
    state: present
```

### Gestione File e Directory

```yaml
- name: Creare directory
  file:
    path: /opt/myapp
    state: directory
    owner: deploy
    group: deploy
    mode: '0755'

- name: Copiare file di configurazione
  copy:
    src: files/app.conf
    dest: /etc/myapp/app.conf
    owner: root
    group: root
    mode: '0644'
    backup: true  # Crea backup del file esistente
  notify: Restart app

- name: Deployare template
  template:
    src: templates/nginx.conf.j2
    dest: /etc/nginx/sites-available/myapp
    owner: root
    group: root
    mode: '0644'
    validate: nginx -t -c %s
  notify: Reload nginx
```

### Gestione Servizi

```yaml
- name: Abilitare e avviare nginx
  service:
    name: nginx
    state: started
    enabled: true

- name: Riavviare PostgreSQL
  systemd:
    name: postgresql
    state: restarted
    daemon_reload: true
```

### Gestione Utenti e Gruppi

```yaml
- name: Creare gruppo applicativo
  group:
    name: appgroup
    gid: 1500
    state: present

- name: Creare utente applicativo
  user:
    name: deploy
    group: appgroup
    groups: sudo,docker
    shell: /bin/bash
    create_home: true
    ssh_key_bits: 4096
    generate_ssh_key: true
    state: present
```

### Gestione Firewall

```yaml
- name: Configurare firewalld
  firewalld:
    port: "{{ item }}"
    permanent: true
    state: enabled
    immediate: true
  loop:
    - 80/tcp
    - 443/tcp
    - 22/tcp

# Oppure con UFW (Ubuntu)
- name: Configurare UFW
  ufw:
    rule: allow
    port: "{{ item.port }}"
    proto: "{{ item.proto }}"
  loop:
    - { port: '80', proto: 'tcp' }
    - { port: '443', proto: 'tcp' }
    - { port: '22', proto: 'tcp' }
```

### Gestione Container Docker

```yaml
- name: Installare Docker
  apt:
    name:
      - docker.io
      - docker-compose-plugin
    state: present

- name: Avviare container applicativo
  docker_container:
    name: myapp
    image: "myregistry.example.com/myapp:{{ app_version }}"
    state: started
    restart_policy: unless-stopped
    ports:
      - "8080:8080"
    env:
      DATABASE_URL: "{{ database_url }}"
      REDIS_URL: "{{ redis_url }}"
    volumes:
      - /opt/myapp/data:/app/data
    networks:
      - name: app_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## Struttura dei Roles

### Directory Layout Completo

```
roles/
└── webserver/
    ├── tasks/
    │   ├── main.yml          # Entry point dei task
    │   ├── install.yml       # Task di installazione
    │   ├── configure.yml     # Task di configurazione
    │   └── deploy.yml        # Task di deployment
    ├── handlers/
    │   └── main.yml          # Handler (restart, reload)
    ├── templates/
    │   ├── nginx.conf.j2     # Template Jinja2 per nginx
    │   └── app.service.j2    # Template per systemd unit
    ├── files/
    │   └── ssl/              # File statici da copiare
    │       ├── dhparam.pem
    │       └── ssl-params.conf
    ├── vars/
    │   └── main.yml          # Variabili interne (alta priorità)
    ├── defaults/
    │   └── main.yml          # Valori di default (bassa priorità, sovrascrivibili)
    ├── meta/
    │   └── main.yml          # Metadati: dipendenze, piattaforme supportate
    ├── tests/
    │   ├── test.yml          # Playbook di test
    │   └── inventory
    └── README.md
```

### Esempio: Role "webserver"

`roles/webserver/defaults/main.yml`:
```yaml
---
nginx_worker_processes: auto
nginx_worker_connections: 1024
nginx_keepalive_timeout: 65
nginx_server_name: "{{ inventory_hostname }}"
nginx_ssl_enabled: true
nginx_ssl_certificate: /etc/ssl/certs/server.crt
nginx_ssl_certificate_key: /etc/ssl/private/server.key
app_port: 8080
```

`roles/webserver/tasks/main.yml`:
```yaml
---
- name: Include install tasks
  include_tasks: install.yml
  tags: [install]

- name: Include configure tasks
  include_tasks: configure.yml
  tags: [configure]
```

`roles/webserver/tasks/install.yml`:
```yaml
---
- name: Installare Nginx
  apt:
    name: nginx
    state: present
    update_cache: true

- name: Creare directory per SSL
  file:
    path: /etc/nginx/ssl
    state: directory
    mode: '0700'
```

`roles/webserver/tasks/configure.yml`:
```yaml
---
- name: Deployare configurazione Nginx principale
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    mode: '0644'
  notify: Reload nginx

- name: Deployare virtual host
  template:
    src: vhost.conf.j2
    dest: "/etc/nginx/sites-available/{{ nginx_server_name }}"
    mode: '0644'
  notify: Reload nginx

- name: Abilitare virtual host
  file:
    src: "/etc/nginx/sites-available/{{ nginx_server_name }}"
    dest: "/etc/nginx/sites-enabled/{{ nginx_server_name }}"
    state: link
  notify: Reload nginx

- name: Rimuovere default virtual host
  file:
    path: /etc/nginx/sites-enabled/default
    state: absent
  notify: Reload nginx
```

`roles/webserver/handlers/main.yml`:
```yaml
---
- name: Reload nginx
  service:
    name: nginx
    state: reloaded

- name: Restart nginx
  service:
    name: nginx
    state: restarted
```

`roles/webserver/meta/main.yml`:
```yaml
---
galaxy_info:
  role_name: webserver
  author: infrastructure-team
  description: Configurazione Nginx webserver
  license: MIT
  min_ansible_version: "2.14"
  platforms:
    - name: Ubuntu
      versions:
        - jammy
        - noble
    - name: Debian
      versions:
        - bookworm

dependencies:
  - role: common
```

---

## Jinja2 Templates

Ansible utilizza Jinja2 come motore di template per generare file di configurazione dinamici.

### Template Nginx Completo

`roles/webserver/templates/nginx.conf.j2`:
```nginx
# Generato da Ansible - NON MODIFICARE MANUALMENTE
# Template: roles/webserver/templates/nginx.conf.j2

user www-data;
worker_processes {{ nginx_worker_processes }};
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections {{ nginx_worker_connections }};
    multi_accept on;
    use epoll;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout {{ nginx_keepalive_timeout }};
    types_hash_max_size 2048;
    server_tokens off;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml;

{% if nginx_ssl_enabled %}
    # SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
{% endif %}

{% for upstream in nginx_upstreams | default([]) %}
    upstream {{ upstream.name }} {
{% for server in upstream.servers %}
        server {{ server.address }}:{{ server.port | default(80) }} weight={{ server.weight | default(1) }};
{% endfor %}
        keepalive 32;
    }

{% endfor %}
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

### Template systemd Service Unit

`roles/webserver/templates/app.service.j2`:
```ini
# Generato da Ansible - NON MODIFICARE MANUALMENTE
[Unit]
Description={{ app_name }} Application Server
Documentation={{ app_documentation_url | default('') }}
After=network.target
{% if app_requires_database | default(false) %}
After=postgresql.service
Requires=postgresql.service
{% endif %}

[Service]
Type=simple
User={{ app_user | default('deploy') }}
Group={{ app_group | default('deploy') }}
WorkingDirectory={{ app_install_dir }}

{% for key, value in app_environment.items() %}
Environment="{{ key }}={{ value }}"
{% endfor %}

ExecStart={{ app_install_dir }}/bin/{{ app_name }} {{ app_start_args | default('') }}
ExecReload=/bin/kill -HUP $MAINPID

Restart=on-failure
RestartSec=10

# Hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths={{ app_data_dir }}
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

---

## Variabili: Precedenza e Organizzazione

Ansible ha un sistema di precedenza delle variabili con 22 livelli. I più importanti, dal più basso al più alto:

```
1.  role defaults (roles/x/defaults/main.yml)         ← più basso
2.  inventory file group vars
3.  inventory group_vars/all.yml
4.  inventory group_vars/<group>.yml
5.  inventory host_vars/<host>.yml
6.  playbook group_vars/all.yml
7.  playbook group_vars/<group>.yml
8.  playbook host_vars/<host>.yml
9.  host facts / cached facts
10. play vars
11. play vars_prompt
12. play vars_files
13. role vars (roles/x/vars/main.yml)
14. block vars
15. task vars
16. include_vars
17. set_facts / registered vars
18. role params (passati con la direttiva role:)
19. include params
20. extra vars (-e / --extra-vars)                     ← più alto
```

### Regola Pratica

- **defaults/**: valori sensati di default, facilmente sovrascrivibili
- **vars/**: valori interni al role che non dovrebbero essere sovrascritti
- **group_vars/**: configurazione specifica per gruppo di host
- **host_vars/**: configurazione specifica per singolo host
- **extra vars**: override temporanei dalla riga di comando

```bash
# Extra vars sovrascrivono tutto
ansible-playbook site.yml -e "app_version=2.1.0 environment=staging"
```

---

## Ansible Vault

Ansible Vault permette di cifrare variabili e file contenenti dati sensibili (password, chiavi API, certificati) utilizzando AES-256.

### Cifratura di un Intero File

```bash
# Creare un file cifrato
ansible-vault create group_vars/production/vault.yml

# Cifrare un file esistente
ansible-vault encrypt group_vars/production/secrets.yml

# Modificare un file cifrato
ansible-vault edit group_vars/production/vault.yml

# Decifrare un file
ansible-vault decrypt group_vars/production/vault.yml

# Visualizzare un file cifrato
ansible-vault view group_vars/production/vault.yml
```

### Cifratura di Singole Stringhe

Per non cifrare interi file, si possono cifrare singole stringhe da inline nel YAML:

```bash
ansible-vault encrypt_string 'password-super-segreta' --name 'db_password'
```

Output da inserire nel file YAML:

```yaml
db_password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  6234646135336638303563...
```

### Pattern Raccomandato per i Segreti

Utilizzare un file `vault.yml` separato nel `group_vars` con le variabili cifrate, e un file `vars.yml` non cifrato che le referenzia:

```yaml
# group_vars/production/vault.yml (cifrato)
vault_db_password: "password-segreta"
vault_api_key: "chiave-api-segreta"

# group_vars/production/vars.yml (non cifrato)
db_password: "{{ vault_db_password }}"
api_key: "{{ vault_api_key }}"
```

Questo pattern permette di cercare e leggere le variabili nel file `vars.yml` senza dover decifrare il vault.

### Esecuzione con Vault

```bash
# Prompt per la password
ansible-playbook site.yml --ask-vault-pass

# Password da file
ansible-playbook site.yml --vault-password-file ~/.vault_password

# Più vault con ID diversi
ansible-vault encrypt --vault-id production@prompt group_vars/production/vault.yml
ansible-playbook site.yml --vault-id production@~/.vault_pass_production
```

---

## Ansible Galaxy

Ansible Galaxy è il repository pubblico di roles e collections condivise dalla community.

### Installazione di Roles e Collections

```bash
# Installare un role
ansible-galaxy role install geerlingguy.docker

# Installare una collection
ansible-galaxy collection install community.general
ansible-galaxy collection install community.postgresql

# Installare da un file requirements
ansible-galaxy install -r requirements.yml
```

`requirements.yml`:
```yaml
---
roles:
  - name: geerlingguy.docker
    version: "6.1.0"
  - name: geerlingguy.postgresql
    version: "3.4.0"
  - name: geerlingguy.certbot
    version: "5.1.0"

collections:
  - name: community.general
    version: ">=7.0.0"
  - name: community.postgresql
    version: ">=3.0.0"
  - name: amazon.aws
    version: ">=6.0.0"
```

### Creare un Role con galaxy init

```bash
ansible-galaxy role init roles/myapp
```

Genera la struttura completa del role con tutti i file e directory standard.

---

## Pattern di Provisioning Server

### Provisioning Completo di un Server Ubuntu

```yaml
---
- name: Provisioning base server Ubuntu
  hosts: all
  become: true
  gather_facts: true

  vars:
    admin_users:
      - name: admin
        ssh_key: "ssh-ed25519 AAAA... admin@company.com"
        sudo: true
      - name: deploy
        ssh_key: "ssh-ed25519 AAAA... deploy@ci-server"
        sudo: false

  tasks:
    - name: Aggiornare tutti i pacchetti
      apt:
        upgrade: dist
        update_cache: true
        cache_valid_time: 3600

    - name: Installare pacchetti base
      apt:
        name:
          - curl
          - wget
          - vim
          - htop
          - tmux
          - git
          - ufw
          - fail2ban
          - unattended-upgrades
          - apt-transport-https
          - ca-certificates
          - gnupg
          - lsb-release
        state: present

    - name: Configurare timezone
      timezone:
        name: Europe/Rome

    - name: Configurare NTP
      apt:
        name: chrony
        state: present

    - name: Creare utenti admin
      user:
        name: "{{ item.name }}"
        groups: "{{ 'sudo' if item.sudo else '' }}"
        shell: /bin/bash
        create_home: true
        state: present
      loop: "{{ admin_users }}"

    - name: Configurare SSH keys
      authorized_key:
        user: "{{ item.name }}"
        key: "{{ item.ssh_key }}"
        exclusive: true
      loop: "{{ admin_users }}"

    - name: Hardening SSH
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: "{{ item.regexp }}"
        line: "{{ item.line }}"
      loop:
        - { regexp: '^#?PermitRootLogin', line: 'PermitRootLogin no' }
        - { regexp: '^#?PasswordAuthentication', line: 'PasswordAuthentication no' }
        - { regexp: '^#?X11Forwarding', line: 'X11Forwarding no' }
        - { regexp: '^#?MaxAuthTries', line: 'MaxAuthTries 3' }
      notify: Restart sshd

    - name: Configurare UFW - default deny
      ufw:
        direction: incoming
        policy: deny

    - name: Configurare UFW - allow SSH
      ufw:
        rule: allow
        port: '22'
        proto: tcp

    - name: Abilitare UFW
      ufw:
        state: enabled

    - name: Configurare fail2ban per SSH
      copy:
        dest: /etc/fail2ban/jail.local
        content: |
          [sshd]
          enabled = true
          port = ssh
          filter = sshd
          maxretry = 5
          bantime = 3600
          findtime = 600
      notify: Restart fail2ban

    - name: Configurare aggiornamenti automatici di sicurezza
      copy:
        dest: /etc/apt/apt.conf.d/20auto-upgrades
        content: |
          APT::Periodic::Update-Package-Lists "1";
          APT::Periodic::Unattended-Upgrade "1";
          APT::Periodic::AutocleanInterval "7";

  handlers:
    - name: Restart sshd
      service:
        name: sshd
        state: restarted

    - name: Restart fail2ban
      service:
        name: fail2ban
        state: restarted
```

---

## Configuration Management

### Gestione Configurazione PostgreSQL

```yaml
---
- name: Configurazione PostgreSQL
  hosts: dbservers
  become: true

  vars:
    postgresql_version: "16"
    postgresql_data_dir: "/var/lib/postgresql/{{ postgresql_version }}/main"
    postgresql_config_dir: "/etc/postgresql/{{ postgresql_version }}/main"

  tasks:
    - name: Installare PostgreSQL
      apt:
        name:
          - "postgresql-{{ postgresql_version }}"
          - "postgresql-client-{{ postgresql_version }}"
          - python3-psycopg2
        state: present

    - name: Configurare postgresql.conf
      template:
        src: postgresql.conf.j2
        dest: "{{ postgresql_config_dir }}/postgresql.conf"
      notify: Restart postgresql

    - name: Configurare pg_hba.conf
      template:
        src: pg_hba.conf.j2
        dest: "{{ postgresql_config_dir }}/pg_hba.conf"
      notify: Reload postgresql

    - name: Creare database applicativo
      community.postgresql.postgresql_db:
        name: "{{ app_db_name }}"
        encoding: UTF-8
        lc_collate: it_IT.UTF-8
        lc_ctype: it_IT.UTF-8
        template: template0
      become_user: postgres

    - name: Creare utente database
      community.postgresql.postgresql_user:
        db: "{{ app_db_name }}"
        name: "{{ app_db_user }}"
        password: "{{ app_db_password }}"
        priv: ALL
        state: present
      become_user: postgres

  handlers:
    - name: Restart postgresql
      service:
        name: postgresql
        state: restarted

    - name: Reload postgresql
      service:
        name: postgresql
        state: reloaded
```

---

## Deployment di Applicazioni

### Pattern: Blue-Green Deployment

```yaml
---
- name: Blue-Green deployment
  hosts: webservers
  become: true

  vars:
    app_releases_dir: /opt/app/releases
    app_shared_dir: /opt/app/shared
    app_current_link: /opt/app/current
    release_timestamp: "{{ ansible_date_time.epoch }}"
    new_release_dir: "{{ app_releases_dir }}/{{ release_timestamp }}"

  tasks:
    - name: Creare directory release
      file:
        path: "{{ new_release_dir }}"
        state: directory
        owner: deploy
        group: deploy

    - name: Scaricare l'artefatto
      get_url:
        url: "{{ artifact_url }}"
        dest: "/tmp/app-{{ app_version }}.tar.gz"
        checksum: "sha256:{{ artifact_checksum }}"

    - name: Estrarre l'artefatto
      unarchive:
        src: "/tmp/app-{{ app_version }}.tar.gz"
        dest: "{{ new_release_dir }}"
        remote_src: true

    - name: Link shared resources
      file:
        src: "{{ app_shared_dir }}/{{ item }}"
        dest: "{{ new_release_dir }}/{{ item }}"
        state: link
      loop:
        - .env
        - log
        - uploads

    - name: Aggiornare il symlink current
      file:
        src: "{{ new_release_dir }}"
        dest: "{{ app_current_link }}"
        state: link
        force: true
      notify: Restart application

    - name: Pulizia vecchie release (mantenere le ultime 5)
      shell: |
        ls -dt {{ app_releases_dir }}/*/ | tail -n +6 | xargs rm -rf
      changed_when: false

  handlers:
    - name: Restart application
      systemd:
        name: "{{ app_name }}"
        state: restarted
```

---

## AWX / Ansible Tower Overview

AWX è la versione open source di Ansible Tower (ora Ansible Automation Platform), che fornisce un'interfaccia web, API REST, RBAC e scheduling per l'esecuzione di playbook Ansible.

### Componenti Principali

- **Dashboard**: vista d'insieme sullo stato dei job, degli host e dei progetti
- **Projects**: repository Git contenenti playbook e roles
- **Inventories**: gestione centralizzata degli inventory (statici e dinamici)
- **Templates**: definizioni di job riutilizzabili (playbook + inventory + credenziali)
- **Credentials**: gestione sicura delle credenziali (SSH keys, API tokens, vault passwords)
- **RBAC**: sistema di permessi granulare basato su ruoli (Admin, Auditor, Use, Execute)
- **Notifications**: integrazione con Slack, email, webhook per notifiche sui job

### Installazione AWX con Docker

```bash
# Clonare il repository AWX
git clone -b 23.5.1 https://github.com/ansible/awx.git
cd awx

# Installare con Docker Compose
make docker-compose-build
make docker-compose
```

### Workflow Templates

AWX supporta Workflow Templates — catene di job template con logica condizionale:

```
[Provision Server]
    ├── (success) → [Configure Base]
    │                   ├── (success) → [Deploy App]
    │                   │                   ├── (success) → [Run Tests]
    │                   │                   │                   ├── (success) → [Notify: OK]
    │                   │                   │                   └── (failure) → [Rollback] → [Notify: FAIL]
    │                   │                   └── (failure) → [Notify: Deploy Failed]
    │                   └── (failure) → [Notify: Config Failed]
    └── (failure) → [Notify: Provision Failed]
```

---

## Testing con Molecule

Molecule è il framework di testing per i roles Ansible. Permette di testare i roles in container Docker o macchine virtuali in modo automatizzato.

### Installazione

```bash
pip install molecule molecule-docker
```

### Inizializzazione

```bash
cd roles/webserver
molecule init scenario --driver-name docker
```

### Struttura dei File Molecule

```
roles/webserver/molecule/
└── default/
    ├── molecule.yml        # Configurazione dello scenario
    ├── converge.yml        # Playbook di test (applica il role)
    ├── verify.yml          # Test di verifica
    └── prepare.yml         # Preparazione pre-test (opzionale)
```

`molecule/default/molecule.yml`:
```yaml
---
dependency:
  name: galaxy
  options:
    requirements-file: requirements.yml

driver:
  name: docker

platforms:
  - name: ubuntu-jammy
    image: geerlingguy/docker-ubuntu2204-ansible:latest
    command: ""
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host
    privileged: true
    pre_build_image: true

  - name: debian-bookworm
    image: geerlingguy/docker-debian12-ansible:latest
    command: ""
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host
    privileged: true
    pre_build_image: true

provisioner:
  name: ansible
  inventory:
    group_vars:
      all:
        nginx_server_name: "test.example.com"
        app_port: 8080

verifier:
  name: ansible
```

`molecule/default/converge.yml`:
```yaml
---
- name: Converge
  hosts: all
  become: true
  roles:
    - role: webserver
```

`molecule/default/verify.yml`:
```yaml
---
- name: Verify
  hosts: all
  become: true
  gather_facts: false

  tasks:
    - name: Verificare che Nginx sia installato
      command: nginx -v
      register: nginx_version
      changed_when: false

    - name: Verificare che Nginx sia in esecuzione
      service_facts:

    - name: Assert Nginx running
      assert:
        that:
          - "'nginx' in ansible_facts.services"
          - "ansible_facts.services['nginx'].state == 'running'"

    - name: Verificare che la porta 80 sia in ascolto
      wait_for:
        port: 80
        timeout: 10

    - name: Verificare la configurazione Nginx
      command: nginx -t
      register: nginx_test
      changed_when: false

    - name: Assert configurazione valida
      assert:
        that:
          - nginx_test.rc == 0
```

### Esecuzione dei Test

```bash
# Ciclo completo: create → converge → verify → destroy
molecule test

# Solo converge (per sviluppo iterativo)
molecule converge

# Solo verify
molecule verify

# Login nel container per debug
molecule login --host ubuntu-jammy

# Distruggere l'ambiente
molecule destroy
```

---

## Integrazione CI/CD

### GitHub Actions

```yaml
# .github/workflows/ansible-test.yml
name: Ansible Role Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  molecule:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        distro:
          - ubuntu2204
          - debian12
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install ansible molecule molecule-docker

      - name: Run Molecule tests
        run: molecule test
        env:
          MOLECULE_DISTRO: ${{ matrix.distro }}

  deploy:
    needs: molecule
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Ansible
        run: pip install ansible

      - name: Run playbook
        run: |
          ansible-playbook playbooks/site.yml -i inventory/production
        env:
          ANSIBLE_VAULT_PASSWORD: ${{ secrets.ANSIBLE_VAULT_PASSWORD }}
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - test
  - deploy

ansible-lint:
  stage: lint
  image: python:3.11
  script:
    - pip install ansible-lint
    - ansible-lint playbooks/ roles/

molecule-test:
  stage: test
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - apk add --no-cache python3 py3-pip
    - pip install ansible molecule molecule-docker
  script:
    - molecule test

deploy-production:
  stage: deploy
  image: python:3.11
  only:
    - main
  script:
    - pip install ansible
    - echo "$VAULT_PASSWORD" > /tmp/.vault_pass
    - ansible-playbook playbooks/site.yml -i inventory/production --vault-password-file /tmp/.vault_pass
  after_script:
    - rm -f /tmp/.vault_pass
```

---

## Best Practices

### Organizzazione del Progetto

1. **Struttura standard**: seguire il layout directory raccomandato da Ansible (inventory, group_vars, host_vars, playbooks, roles).
2. **Un role per responsabilità**: ogni role deve gestire un singolo aspetto (webserver, database, monitoring), non un intero stack.
3. **Versionamento dei roles**: pinnare le versioni dei roles esterni nel `requirements.yml`.
4. **Separare dati e logica**: le variabili negli inventory e nei group_vars, la logica nei roles e nei playbook.

### Idempotenza e Affidabilità

5. **Evitare shell/command quando possibile**: preferire sempre i moduli nativi di Ansible (idempotenti per design) ai moduli shell e command.
6. **Usare `creates` e `removes`**: quando shell/command sono necessari, usare i parametri `creates` e `removes` per renderli idempotenti.
7. **Check mode**: tutti i playbook dovrebbero supportare `--check` (dry run) senza errori.
8. **Handler per i restart**: mai riavviare un servizio direttamente in un task — usare sempre i handler con notify per evitare restart multipli.

### Sicurezza

9. **Vault per tutti i segreti**: ogni password, chiave API o certificato deve essere cifrato con Ansible Vault.
10. **No passwords in plain text**: mai in variabili, inventory o playbook.
11. **SSH key authentication**: usare sempre SSH key, mai password, per la connessione ai managed nodes.
12. **Limitare become**: applicare `become: true` solo ai task che lo richiedono, non a livello di play quando non necessario.

### Testing

13. **Molecule per ogni role**: ogni role deve avere test Molecule funzionanti.
14. **Linting obbligatorio**: eseguire `ansible-lint` in CI per catturare errori e anti-pattern.
15. **Test su più piattaforme**: testare i roles su tutte le distribuzioni target (Ubuntu, Debian, RHEL).

---

## Troubleshooting

### Problema: "Permission denied" sui Managed Nodes

**Sintomi**: Ansible fallisce con "Permission denied (publickey)" o "Unreachable".

**Causa**: la SSH key non è stata distribuita al managed node, l'utente specificato non esiste sul target, o i permessi del file `~/.ssh/authorized_keys` sono errati (SSH richiede che il file sia leggibile solo dal proprietario).

**Soluzione**: verificare la connettività SSH manuale: `ssh -i ~/.ssh/ansible_key deploy@target`. Controllare i permessi: `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys` sul target. Verificare `ansible_user` e `ansible_ssh_private_key_file` nell'inventory.

### Problema: Task "changed" ad Ogni Esecuzione

**Sintomi**: un task riporta "changed" anche quando non dovrebbe apportare modifiche.

**Causa**: il task utilizza `shell` o `command` senza condizioni di idempotenza, oppure un template viene rigenerato ad ogni esecuzione (es. contiene un timestamp).

**Soluzione**: aggiungere `creates` o `removes` ai task shell/command. Utilizzare `changed_when: false` se il comando è di sola lettura. Rimuovere elementi variabili (timestamp, random) dai template.

### Problema: "No matching host found" con Dynamic Inventory

**Sintomi**: `ansible-playbook` non trova host nonostante il dynamic inventory sia configurato.

**Causa**: il plugin di inventory potrebbe non essere attivato, le credenziali cloud potrebbero essere errate, o i filtri nel file di configurazione del plugin potrebbero escludere tutti gli host.

**Soluzione**: verificare l'inventory con `ansible-inventory -i inventory/aws_ec2.yml --list`. Controllare le credenziali AWS/Azure con `aws sts get-caller-identity` o `az account show`. Esaminare i filtri nel file di configurazione del plugin.

### Problema: Vault Password Dimenticata

**Sintomi**: impossibile decifrare i file vault perché la password è stata persa.

**Causa**: la password vault è stata persa o non documentata.

**Soluzione**: non esiste un modo per recuperare la password vault (design by intention — la sicurezza non sarebbe reale se fosse bypassabile). È necessario ricreare i file vault con una nuova password, reinserendo tutti i segreti. Per prevenire: archiviare la vault password in un password manager aziendale e impostare un file vault-password-file referenziato in `ansible.cfg`.

### Problema: Task Molto Lenti su Molti Host

**Sintomi**: l'esecuzione del playbook impiega molto tempo, specialmente con molti host.

**Causa**: il numero di `forks` è troppo basso (default 5), il pipelining non è attivato, o `gather_facts` viene eseguito su ogni play senza caching.

**Soluzione**: aumentare `forks` in `ansible.cfg` (es. 20-50, in base alla potenza del control node). Abilitare `pipelining = True`. Configurare il fact caching con `gathering = smart` e `fact_caching = jsonfile`. Disabilitare `gather_facts` nei play che non ne hanno bisogno.

---

## Riferimenti

- **Documentazione ufficiale Ansible**: https://docs.ansible.com/ansible/latest/
- **Ansible Galaxy**: https://galaxy.ansible.com/
- **Ansible Best Practices**: https://docs.ansible.com/ansible/latest/tips_tricks/ansible_tips_tricks.html
- **Ansible Module Index**: https://docs.ansible.com/ansible/latest/collections/index_module.html
- **Molecule Documentation**: https://molecule.readthedocs.io/
- **AWX Project**: https://github.com/ansible/awx
- **Ansible Lint**: https://ansible.readthedocs.io/projects/lint/
- **Jinja2 Template Documentation**: https://jinja.palletsprojects.com/
- **Ansible Vault Documentation**: https://docs.ansible.com/ansible/latest/vault_guide/
- **Red Hat Ansible Automation Platform**: https://www.redhat.com/en/technologies/management/ansible
- **Jeff Geerling's Ansible for DevOps**: https://www.ansiblefordevops.com/

---

## Letture e Riferimenti

### Documentazione ufficiale

- Ansible — Playbook Guide: https://docs.ansible.com/ansible/latest/playbook_guide/index.html (consultato: 2026-05-24)
- Ansible — Role Directory Structure: https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html (consultato: 2026-05-24)
- Ansible — Inventory Plugins: https://docs.ansible.com/ansible/latest/plugins/inventory.html (consultato: 2026-05-24)
- Molecule — Testing Ansible Roles: https://ansible.readthedocs.io/projects/molecule/getting-started/ (consultato: 2026-05-24)
- Ansible — Collections Using and Developing: https://docs.ansible.com/ansible/latest/collections_guide/index.html (consultato: 2026-05-24)
- AWX — Installation Guide: https://ansible.readthedocs.io/projects/awx/en/latest/installation/ (consultato: 2026-05-24)

### Libri

- **"Ansible for DevOps"** — Jeff Geerling (Leanpub). Guida pratica con esempi reali di playbook, roles, e deploy su infrastrutture di produzione.
- **"Ansible: Up and Running"** — Bas Meijer, Lorin Hochstein, Rene Moser (O'Reilly, 3a ed.). Copertura completa da basics a pattern avanzati (callback plugins, custom modules, testing).

---

## Esercizi

1. **Lab — playbook idempotente.** Configura nginx + firewall + ssh hardening; esegui 10x; verifica `changed=0` dalla 2a esecuzione.
2. **Lab — role sharing.** Crea un role per Postgres install + tuning; pubblica su Ansible Galaxy.
3. **Stretch — AWX deployment.** Deploy AWX su K8s, integra con Git per playbook + LDAP per auth.

## Auto-valutazione

1. Playbook idempotente: come si verifica?
2. Roles vs collections.
3. Vault: gestione password in CI.
4. Inventory dinamico: tipici plugin.
5. AWX vs AAP: differenza.

## Collegamenti incrociati

- Modulo 12 — `12-python-automazione-avanzata.md`: alternativa code-first.
- Modulo `../06-GESTIONE-PIATTAFORME/`: IaC ecosystem.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Playbook** | YAML con sequenza di task. |
| **Role** | Modulo riusabile (tasks, vars, handlers). |
| **Collection** | Gruppo di roles + plugins distribuiti. |
| **Inventory** | Lista di host target. |
| **Idempotenza** | Stesso input = stesso output. |
| **Vault** | Strumento Ansible per cifrare secrets. |
| **AWX** | Open-source UI per Ansible. |
| **AAP** | Red Hat Ansible Automation Platform (commercial). |
| **Galaxy** | Hub community per roles/collections. |
