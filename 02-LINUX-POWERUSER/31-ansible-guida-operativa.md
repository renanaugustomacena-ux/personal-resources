# Ansible: Guida Operativa — Guida Approfondita

> **Modulo 31** · **Aggiornamento:** 2026-05-23

---

> **Modulo del corso:** Linux per ingegneri di sistema
>
> **Prerequisiti:** Conoscenza base di Linux CLI, SSH, YAML, Python 3. Familiarità con la gestione di server remoti e il concetto di gestione della configurazione. Modulo 02 (Shell Scripting) e Modulo 10 (Networking) raccomandati.
>
> **Obiettivi:**
> 1. Progettare e gestire inventory statici e dinamici per ambienti multi-cloud
> 2. Scrivere playbook idempotenti con gestione errori, handler, tag e strategie di esecuzione
> 3. Creare e testare roles riutilizzabili con Molecule e ansible-lint
> 4. Gestire segreti con Ansible Vault (inline, multi-vault, integrazione CI/CD)
> 5. Applicare pattern operativi reali: rolling update, canary deployment, blue-green
> 6. Configurare AWX/AAP per orchestrazione enterprise con RBAC e scheduling
>
> **Tempo stimato:** 16-20 ore
>
> **Livello:** Intermedio-Avanzato
>
> **Ultimo aggiornamento:** 2026-05-23
>
> **Versioni di riferimento:** ansible-core 2.17+, ansible 10+ (pacchetto community), Python 3.10+

---

## Mappa Concettuale

```
                          ┌──────────────────────┐
                          │    CONTROL NODE       │
                          │  (ansible-playbook)   │
                          └──────────┬───────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
     ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
     │   INVENTORY      │   │   PLAYBOOK       │   │  ansible.cfg    │
     │ static / dynamic │   │ YAML declarativo │   │  configurazione │
     └────────┬────────┘   └────────┬────────┘   └─────────────────┘
              │                      │
              │            ┌─────────┼─────────┐
              │            │         │         │
              │     ┌──────▼──┐ ┌────▼───┐ ┌───▼────┐
              │     │  ROLES  │ │ VARS   │ │ VAULT  │
              │     │modulari │ │ facts  │ │segreti │
              │     └──┬──┬──┘ └────────┘ └────────┘
              │        │  │
              │  ┌─────▼──▼──────┐
              │  │  COLLECTIONS   │
              │  │namespace.coll  │
              │  └───────────────┘
              │
    ┌─────────▼─────────────────────────────────────┐
    │                 TRASPORTO                       │
    │   SSH (default) │ WinRM │ Local │ Paramiko     │
    └─────────┬──────────┬──────────┬───────────────┘
              │          │          │
     ┌────────▼───┐ ┌────▼────┐ ┌───▼──────────┐
     │ Managed    │ │ Managed │ │ Managed      │
     │ Node 1     │ │ Node 2  │ │ Node N       │
     │ (Python 3) │ │(no agent│ │ (idempotent) │
     └────────────┘ └─────────┘ └──────────────┘

    FLUSSO: Inventory → Playbook → Role/Task → Modulo → SSH → Nodo gestito
    PRINCIPIO: Stato desiderato dichiarativo + Idempotenza
```

---

## Idee guida
1. **Idempotent playbook by design.**
2. **Roles + collections per modular share.**
3. **Vault per secrets (mai plaintext in inventory).**
4. **AAP/AWX per UI + scheduling enterprise.**


## Indice

- [Panoramica](#panoramica)
- [Installazione e Architettura](#installazione-e-architettura)
- [Architettura in Dettaglio](#architettura-in-dettaglio)
- [Inventory: Statico e Dinamico](#inventory-statico-e-dinamico)
- [Inventory Dinamico Multi-Cloud](#inventory-dinamico-multi-cloud)
- [Playbook: Struttura e Sintassi](#playbook-struttura-e-sintassi)
- [Moduli Essenziali](#moduli-essenziali)
- [Variabili e Facts](#variabili-e-facts)
- [Jinja2 Templates](#jinja2-templates)
- [Jinja2 in Profondità](#jinja2-in-profondità)
- [Roles](#roles)
- [Collections](#collections)
- [Ansible Vault](#ansible-vault)
- [Vault Avanzato](#vault-avanzato)
- [Handlers, Tags e Strategie](#handlers-tags-e-strategie)
- [Strategie di Esecuzione Avanzate](#strategie-di-esecuzione-avanzate)
- [Idempotenza: Principi e Pratica](#idempotenza-principi-e-pratica)
- [Testing con Molecule](#testing-con-molecule)
- [Performance e Ottimizzazione](#performance-e-ottimizzazione)
- [Sicurezza Avanzata](#sicurezza-avanzata)
- [Ansible AWX / AAP](#ansible-awx--aap)
- [Pattern Reali: Rolling Update](#pattern-reali-rolling-update)
- [Pattern Reali: Canary Deployment](#pattern-reali-canary-deployment)
- [Pattern Reali: Blue-Green Deployment](#pattern-reali-blue-green-deployment)
- [Pattern Reali: Infrastructure Provisioning](#pattern-reali-infrastructure-provisioning)
- [Pattern Comuni: LAMP Stack](#pattern-comuni-lamp-stack)
- [Pattern Comuni: Hardening Playbook](#pattern-comuni-hardening-playbook)
- [Execution Environments (EE)](#execution-environments-ee)
- [ansible-navigator](#ansible-navigator)
- [ansible-lint: Regole e Profili Avanzati](#ansible-lint-regole-e-profili-avanzati)
- [Callback Plugin](#callback-plugin)
- [Sviluppo di Moduli Custom](#sviluppo-di-moduli-custom)
- [Automazione di Rete (Cisco, Juniper, Arista)](#automazione-di-rete-cisco-juniper-arista)
- [Automazione Windows con Ansible](#automazione-windows-con-ansible)
- [Integrazione CI/CD con GitHub Actions](#integrazione-cicd-con-github-actions)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)
- [Esercizi](#esercizi)
- [Auto-valutazione](#auto-valutazione)
- [Letture Primarie](#letture-primarie)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario Locale](#glossario-locale)

---

## Panoramica

Ansible è lo strumento di automazione IT più diffuso, sviluppato da Red Hat, che permette di gestire configurazione, deployment e orchestrazione di infrastrutture senza installare agenti sui nodi gestiti. Ansible utilizza SSH come trasporto e YAML come linguaggio di configurazione, rendendolo accessibile a chiunque abbia familiarità con l'amministrazione di sistemi Linux.

La filosofia di Ansible è l'idempotenza: eseguire un playbook più volte produce sempre lo stesso risultato finale, indipendentemente dallo stato iniziale del sistema. Questo significa che un playbook non è una sequenza di comandi ("installa il pacchetto X, poi modifica il file Y"), ma una dichiarazione dello stato desiderato del sistema ("il pacchetto X deve essere installato, il file Y deve avere questo contenuto"). Ansible si occupa di determinare le azioni necessarie per raggiungere lo stato desiderato.

Questo documento copre Ansible dalla prospettiva operativa di un system administrator: dall'inventory alla struttura dei playbook, dai moduli essenziali ai roles riutilizzabili, dalla gestione sicura dei segreti con Vault fino a due progetti completi (LAMP stack e hardening). L'obiettivo è fornire le competenze per automatizzare la gestione di decine o centinaia di server in modo affidabile, ripetibile e documentato.

---

## Installazione e Architettura

### Installazione

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ansible

# Oppure via pip (versione più recente)
pip3 install ansible

# Verifica
ansible --version
# ansible [core 2.16.x]
#   config file = /etc/ansible/ansible.cfg
#   python version = 3.12.x
```

### Architettura

```
┌──────────────────────────────────────────────────┐
│              Control Node                         │
│  (dove esegui Ansible — il tuo laptop/bastion)    │
│                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Inventory│  │ Playbook │  │ ansible.cfg  │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
│                                                    │
│  ansible / ansible-playbook                       │
└────────┬───────────┬───────────┬─────────────────┘
         │ SSH       │ SSH       │ SSH
┌────────▼───┐ ┌─────▼────┐ ┌───▼──────────┐
│ Managed    │ │ Managed  │ │ Managed      │
│ Node 1     │ │ Node 2   │ │ Node N       │
│            │ │          │ │              │
│ (no agent) │ │ (no agent)│ │ (no agent)  │
└────────────┘ └──────────┘ └──────────────┘
```

### Configurazione

```ini
# ansible.cfg (nella directory del progetto — ha precedenza su /etc/ansible/ansible.cfg)

[defaults]
inventory = ./inventory/
roles_path = ./roles/
collections_paths = ./collections/
remote_user = deploy
private_key_file = ~/.ssh/id_ed25519
host_key_checking = False
retry_files_enabled = False
stdout_callback = yaml
forks = 20                    # parallelismo (default 5)
timeout = 30

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
pipelining = True             # riduce le connessioni SSH (grande miglioramento performance)
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

---

## Architettura in Dettaglio

### Control Node vs Managed Nodes

Il **control node** è la macchina su cui è installato Ansible — il tuo laptop, un bastion host o un server CI/CD. È l'unico nodo che richiede l'installazione di Ansible. Può essere qualsiasi macchina Unix/Linux/macOS con Python 3.10+; Windows non è supportato come control node (ma può essere managed node via WinRM).

I **managed nodes** (o "target nodes") sono i server gestiti da Ansible. Non richiedono alcun agente: Ansible si connette via SSH, copia un modulo Python temporaneo, lo esegue, raccoglie l'output e rimuove il modulo. L'unico requisito è Python 3 (versione 3.6+, raccomandata 3.10+) installato sul nodo.

```
FLUSSO DI ESECUZIONE DI UN TASK:

  Control Node                          Managed Node
  ┌──────────────┐                     ┌──────────────┐
  │ 1. Legge il  │                     │              │
  │    playbook  │                     │              │
  │              │                     │              │
  │ 2. Genera il │    SSH (porta 22)   │              │
  │    modulo    │ ─────────────────►  │ 4. Python    │
  │    Python    │    3. Copia modulo  │    esegue il │
  │              │                     │    modulo    │
  │              │  ◄─────────────────  │              │
  │ 6. Elabora   │    5. Ritorna JSON  │ 5. Rimuove  │
  │    risultato │                     │    modulo    │
  └──────────────┘                     └──────────────┘
```

### Trasporto SSH e Connection Plugin

Ansible utilizza per default OpenSSH nativo (`ssh`) come trasporto. Il connection plugin determina come Ansible si connette ai nodi gestiti.

```ini
# I connection plugin più comuni in ansible.cfg:

# SSH nativo (default, raccomandato)
[defaults]
transport = ssh

# Paramiko (SSH in puro Python — utile su sistemi senza OpenSSH client)
# transport = paramiko

# Locale (esegui sul control node stesso, senza SSH)
# ansible_connection=local  →  per il nodo corrente
```

| Connection Plugin | Uso                                | Note                                    |
|-------------------|------------------------------------|-----------------------------------------|
| `ssh`             | Default per Linux/Unix             | Usa OpenSSH nativo, supporta pipelining |
| `paramiko`        | Fallback SSH                       | Puro Python, nessuna dipendenza esterna |
| `local`           | Esecuzione locale                  | Per task sul control node               |
| `winrm`           | Windows managed nodes              | Richiede `pywinrm`, usa WinRM           |
| `docker`          | Container Docker                   | Esecuzione diretta nel container        |
| `podman`          | Container Podman                   | Come docker ma per Podman               |
| `network_cli`     | Dispositivi di rete (Cisco, Arista)| Connessione CLI su dispositivi di rete  |
| `httpapi`         | API REST di apparati               | Per dispositivi con interfaccia REST    |

### Requisiti Python sui Managed Nodes

```yaml
# Se Python 3 non è nel path standard, specificalo nell'inventory:
all:
  vars:
    ansible_python_interpreter: /usr/bin/python3

# Per distribuzioni con Python in posizioni non standard:
# ansible_python_interpreter: /usr/local/bin/python3.11

# Modulo raw — unica eccezione che non richiede Python sul nodo:
- name: Installa Python su nodo minimal
  raw: apt-get install -y python3
  become: true
  when: ansible_python_interpreter is not defined
```

### Ordine di Ricerca di ansible.cfg

Ansible cerca il file di configurazione nel seguente ordine (il primo trovato vince):

1. `ANSIBLE_CONFIG` (variabile d'ambiente)
2. `./ansible.cfg` (directory corrente — raccomandato per progetto)
3. `~/.ansible.cfg` (home directory dell'utente)
4. `/etc/ansible/ansible.cfg` (globale di sistema)

```bash
# Verifica quale config è in uso:
ansible --version
# ansible [core 2.17.x]
#   config file = /path/to/ansible.cfg   ← il file in uso

# Visualizza tutte le configurazioni attive:
ansible-config dump --only-changed
```

---

## Inventory: Statico e Dinamico

### Inventory Statico (INI)

```ini
# inventory/hosts.ini

[webservers]
web01 ansible_host=10.0.1.10
web02 ansible_host=10.0.1.11
web03 ansible_host=10.0.1.12

[dbservers]
db01 ansible_host=10.0.2.10 ansible_port=22
db02 ansible_host=10.0.2.11

[cache]
redis01 ansible_host=10.0.3.10

[staging]
staging01 ansible_host=10.0.10.10

[production:children]
webservers
dbservers
cache

[all:vars]
ansible_python_interpreter=/usr/bin/python3
ntp_server=ntp.example.com
```

### Inventory Statico (YAML) — Raccomandato

```yaml
# inventory/hosts.yml

all:
  vars:
    ansible_python_interpreter: /usr/bin/python3
    ntp_server: ntp.example.com

  children:
    production:
      children:
        webservers:
          hosts:
            web01:
              ansible_host: 10.0.1.10
              http_port: 8080
            web02:
              ansible_host: 10.0.1.11
              http_port: 8080
            web03:
              ansible_host: 10.0.1.12
              http_port: 8080
          vars:
            nginx_worker_processes: auto

        dbservers:
          hosts:
            db01:
              ansible_host: 10.0.2.10
              postgresql_version: 16
            db02:
              ansible_host: 10.0.2.11
              postgresql_version: 16
          vars:
            backup_enabled: true

        cache:
          hosts:
            redis01:
              ansible_host: 10.0.3.10

    staging:
      hosts:
        staging01:
          ansible_host: 10.0.10.10
```

### Inventory Dinamico

Per ambienti cloud dove i server cambiano frequentemente:

```bash
# AWS EC2 — usa plugin aws_ec2
# inventory/aws_ec2.yml
plugin: amazon.aws.aws_ec2
regions:
  - eu-west-1
keyed_groups:
  - key: tags.Environment
    prefix: env
  - key: tags.Role
    prefix: role
filters:
  tag:Managed: ansible
  instance-state-name: running
compose:
  ansible_host: private_ip_address

# Verifica
ansible-inventory -i inventory/aws_ec2.yml --list
ansible-inventory -i inventory/aws_ec2.yml --graph
```

---

## Inventory Dinamico Multi-Cloud

### Altri Plugin Inventory Cloud

| Provider | Plugin | Collection | Installazione pip |
|----------|--------|-----------|-------------------|
| GCP | `google.cloud.gcp_compute` | `google.cloud` | `google-auth requests` |
| Azure | `azure.azcollection.azure_rm` | `azure.azcollection` | `azure-identity azure-mgmt-compute` |
| NetBox | `netbox.netbox.nb_inventory` | `netbox.netbox` | `pynetbox` |

Struttura identica all'esempio AWS: `plugin`, `keyed_groups`, `compose` per `ansible_host`, filtri per tag/label. Consulta la documentazione della collection specifica per i parametri di autenticazione.

### Gruppi di Gruppi e Inventory Multi-Ambiente

```yaml
# inventory/production/hosts.yml
all:
  children:
    production:
      children:
        eu_west:
          children:
            eu_west_webservers:
              hosts:
                prod-web-eu-01: { ansible_host: 10.1.1.10 }
                prod-web-eu-02: { ansible_host: 10.1.1.11 }
            eu_west_dbservers:
              hosts:
                prod-db-eu-01: { ansible_host: 10.1.2.10 }
        us_east:
          children:
            us_east_webservers:
              hosts:
                prod-web-us-01: { ansible_host: 10.2.1.10 }
            us_east_dbservers:
              hosts:
                prod-db-us-01: { ansible_host: 10.2.2.10 }

        # Metagruppi trasversali
        all_webservers:
          children:
            eu_west_webservers:
            us_east_webservers:
        all_dbservers:
          children:
            eu_west_dbservers:
            us_east_dbservers:
```

### Struttura Directory host_vars / group_vars Multi-Ambiente

```
project/
├── inventory/
│   ├── production/
│   │   ├── hosts.yml
│   │   ├── group_vars/
│   │   │   ├── all/
│   │   │   │   ├── vars.yml         # variabili comuni produzione
│   │   │   │   └── vault.yml        # segreti criptati produzione
│   │   │   ├── webservers.yml
│   │   │   └── dbservers.yml
│   │   └── host_vars/
│   │       ├── prod-web-eu-01.yml
│   │       └── prod-db-eu-01.yml
│   ├── staging/
│   │   ├── hosts.yml
│   │   ├── group_vars/
│   │   │   └── all/
│   │   │       ├── vars.yml
│   │   │       └── vault.yml
│   │   └── host_vars/
│   └── development/
│       ├── hosts.yml
│       └── group_vars/
│           └── all.yml
├── playbooks/
├── roles/
└── ansible.cfg
```

```bash
# Esecuzione per ambiente specifico:
ansible-playbook -i inventory/production site.yml
ansible-playbook -i inventory/staging site.yml

# Verifica l'inventory risolto:
ansible-inventory -i inventory/production --graph
ansible-inventory -i inventory/production --host prod-web-eu-01
```

### Inventory Plugin: Combinare Fonti Multiple

```yaml
# ansible.cfg — abilita plugin inventory
[inventory]
enable_plugins = host_list, script, auto, yaml, ini, toml,
                 amazon.aws.aws_ec2, google.cloud.gcp_compute,
                 azure.azcollection.azure_rm, netbox.netbox.nb_inventory
```

```bash
# Inventari multipli in una directory:
# Ansible legge tutti i file in ordine alfabetico
inventory/
├── 01-static.yml          # host fisici
├── 02-aws_ec2.yml         # istanze AWS
├── 03-gcp_compute.yml     # istanze GCP
└── group_vars/
    └── all.yml
```

### Constructed Inventory: Gruppi Dinamici dai Facts

Il plugin `ansible.builtin.constructed` crea gruppi e variabili **calcolati a runtime** da facts o variabili esistenti, senza interrogare API esterne. Viene caricato come layer aggiuntivo sopra qualunque sorgente (statica o dinamica).

```yaml
# inventory/constructed.yml — caricato DOPO le altre sorgenti
plugin: ansible.builtin.constructed
strict: false

groups:
  debian_family: ansible_os_family == "Debian"
  env_production: environment == "production"
  prod_web: "'webservers' in group_names and environment == 'production'"
  high_memory: ansible_memtotal_mb >= 16384

keyed_groups:
  - prefix: distro
    key: ansible_distribution | default("unknown")
  - prefix: env
    key: environment | default("untagged")

compose:
  ansible_host_short: inventory_hostname.split('.')[0]
```

```bash
# Targeting mirato con gruppi costruiti:
ansible-playbook site.yml -l 'debian_family:&high_memory:&env_production'
ansible -m debug -a "var=group_names" web01.example.com
```

> **Attenzione:** il constructed plugin richiede facts già disponibili. Usa `fact_caching` oppure un play preliminare di raccolta facts.

### Comandi ad-hoc

```bash
# Ping tutti gli host
ansible all -m ping

# Ping un gruppo
ansible webservers -m ping

# Esegui comando
ansible dbservers -m shell -a "df -h"

# Copia file
ansible webservers -m copy -a "src=./index.html dest=/var/www/html/"

# Installa pacchetto
ansible webservers -m apt -a "name=nginx state=present" --become

# Raccoglie facts
ansible web01 -m setup
ansible web01 -m setup -a "filter=ansible_distribution*"
```

---

## Playbook: Struttura e Sintassi

### Playbook Base

```yaml
# site.yml — playbook principale
---
- name: Configura web servers
  hosts: webservers
  become: true

  vars:
    app_name: myapp
    app_port: 8080

  pre_tasks:
    - name: Aggiorna cache apt
      apt:
        update_cache: true
        cache_valid_time: 3600

  tasks:
    - name: Installa Nginx
      apt:
        name: nginx
        state: present

    - name: Configura Nginx
      template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/sites-available/{{ app_name }}.conf
        owner: root
        group: root
        mode: '0644'
      notify: Reload Nginx

    - name: Abilita sito
      file:
        src: /etc/nginx/sites-available/{{ app_name }}.conf
        dest: /etc/nginx/sites-enabled/{{ app_name }}.conf
        state: link
      notify: Reload Nginx

    - name: Assicura che Nginx sia avviato
      service:
        name: nginx
        state: started
        enabled: true

  handlers:
    - name: Reload Nginx
      service:
        name: nginx
        state: reloaded

- name: Configura database servers
  hosts: dbservers
  become: true
  roles:
    - postgresql
```

### Condizionali

```yaml
tasks:
  - name: Installa pacchetto (Debian/Ubuntu)
    apt:
      name: htop
      state: present
    when: ansible_os_family == "Debian"

  - name: Installa pacchetto (RHEL/CentOS)
    dnf:
      name: htop
      state: present
    when: ansible_os_family == "RedHat"

  - name: Configura solo se la variabile è definita
    template:
      src: custom.conf.j2
      dest: /etc/myapp/custom.conf
    when: custom_config is defined and custom_config | length > 0

  - name: Esegui solo in produzione
    command: /opt/app/warmup-cache.sh
    when: "'production' in group_names"
```

### Cicli (Loop)

```yaml
tasks:
  - name: Installa pacchetti multipli
    apt:
      name: "{{ item }}"
      state: present
    loop:
      - nginx
      - postgresql-client
      - redis-tools
      - htop
      - tmux

  # Forma più efficiente per apt:
  - name: Installa pacchetti (batch)
    apt:
      name:
        - nginx
        - postgresql-client
        - redis-tools
      state: present

  - name: Crea utenti
    user:
      name: "{{ item.name }}"
      groups: "{{ item.groups }}"
      shell: /bin/bash
    loop:
      - { name: 'deploy', groups: 'www-data,sudo' }
      - { name: 'monitor', groups: 'adm' }
      - { name: 'backup', groups: 'backup' }

  - name: Copia file di configurazione
    template:
      src: "{{ item.src }}"
      dest: "{{ item.dest }}"
      mode: "{{ item.mode | default('0644') }}"
    loop:
      - { src: 'nginx.conf.j2', dest: '/etc/nginx/nginx.conf' }
      - { src: 'app.conf.j2', dest: '/etc/myapp/app.conf', mode: '0600' }
```

### Blocchi e Error Handling

```yaml
tasks:
  - name: Blocco con gestione errori
    block:
      - name: Deploy nuova versione
        git:
          repo: https://github.com/org/app.git
          dest: /opt/app
          version: "{{ app_version }}"

      - name: Installa dipendenze
        pip:
          requirements: /opt/app/requirements.txt

      - name: Migra database
        command: /opt/app/manage.py migrate
        register: migrate_result

    rescue:
      - name: Rollback su errore
        git:
          repo: https://github.com/org/app.git
          dest: /opt/app
          version: "{{ app_previous_version }}"

      - name: Notifica fallimento
        debug:
          msg: "Deploy fallito! Rollback a {{ app_previous_version }}"

    always:
      - name: Riavvia applicazione (sempre)
        service:
          name: myapp
          state: restarted
```

---

## Moduli Essenziali

### Gestione Pacchetti

```yaml
# apt (Debian/Ubuntu)
- name: Installa pacchetto
  apt:
    name: nginx
    state: present              # present, absent, latest

- name: Aggiorna tutti i pacchetti
  apt:
    upgrade: dist
    update_cache: true

# dnf/yum (RHEL/Fedora)
- name: Installa pacchetto
  dnf:
    name: httpd
    state: present
```

### Gestione File

```yaml
# copy — copia file dal control node
- name: Copia file di configurazione
  copy:
    src: files/app.conf
    dest: /etc/myapp/app.conf
    owner: root
    group: root
    mode: '0644'
    backup: true                # crea backup del file originale

# template — processa template Jinja2
- name: Genera configurazione
  template:
    src: templates/nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    validate: 'nginx -t -c %s'  # valida prima di applicare!

# file — gestisci proprietà file, crea directory, link
- name: Crea directory
  file:
    path: /opt/app/logs
    state: directory
    owner: app
    group: app
    mode: '0755'

- name: Crea link simbolico
  file:
    src: /opt/app/current/public
    dest: /var/www/html
    state: link

# lineinfile — modifica una riga in un file
- name: Assicura configurazione in sshd_config
  lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^PermitRootLogin'
    line: 'PermitRootLogin no'
    validate: 'sshd -t -f %s'
```

### Gestione Servizi

```yaml
- name: Avvia e abilita servizio
  service:
    name: nginx
    state: started
    enabled: true

# systemd specifico
- name: Ricarica systemd e avvia
  systemd:
    name: myapp
    state: started
    enabled: true
    daemon_reload: true
```

### Gestione Utenti

```yaml
- name: Crea utente applicativo
  user:
    name: deploy
    groups: www-data,sudo
    shell: /bin/bash
    create_home: true
    generate_ssh_key: true
    ssh_key_bits: 4096

- name: Aggiungi chiave SSH autorizzata
  authorized_key:
    user: deploy
    key: "{{ lookup('file', 'files/deploy_key.pub') }}"
    state: present
```

### Comandi e Script

```yaml
# command — esegue comando (no shell features)
- name: Esegui migrazione
  command: /opt/app/manage.py migrate --noinput
  args:
    chdir: /opt/app
  register: migrate_output
  changed_when: "'No migrations to apply' not in migrate_output.stdout"

# shell — esegue in shell (pipe, redirect disponibili)
- name: Conta file di log
  shell: find /var/log -name '*.log' -mtime +30 | wc -l
  register: old_logs
  changed_when: false  # comando di sola lettura

# script — copia ed esegue uno script locale
- name: Esegui script di setup
  script: scripts/initial-setup.sh
  args:
    creates: /opt/app/.initialized  # non eseguire se il file esiste
```

---

## Variabili e Facts

### Precedenza delle Variabili (dalla più bassa alla più alta)

1. Defaults dei role (`roles/x/defaults/main.yml`)
2. Inventory vars (`inventory/group_vars/`, `inventory/host_vars/`)
3. Playbook `vars:`
4. Task `vars:`
5. Extra vars (`-e` dalla command line) — la più alta

### Struttura Directory per Variabili

```
project/
├── inventory/
│   ├── hosts.yml
│   ├── group_vars/
│   │   ├── all.yml           # variabili per tutti gli host
│   │   ├── webservers.yml    # variabili per il gruppo webservers
│   │   └── dbservers.yml
│   └── host_vars/
│       ├── web01.yml          # variabili specifiche per web01
│       └── db01.yml
├── playbooks/
├── roles/
└── ansible.cfg
```

```yaml
# inventory/group_vars/all.yml
---
ntp_servers:
  - 0.pool.ntp.org
  - 1.pool.ntp.org
timezone: Europe/Rome
admin_email: ops@example.com

# inventory/group_vars/webservers.yml
---
nginx_worker_processes: auto
nginx_worker_connections: 4096
app_port: 8080

# inventory/host_vars/web01.yml
---
nginx_worker_processes: 8  # override per questo host
```

### Facts

I facts sono variabili raccolte automaticamente dal sistema target:

```yaml
# Usa facts nelle task
- name: Configura swap solo se RAM < 4GB
  command: fallocate -l 2G /swapfile
  when: ansible_memtotal_mb < 4096

- name: Mostra info sistema
  debug:
    msg: |
      OS: {{ ansible_distribution }} {{ ansible_distribution_version }}
      Kernel: {{ ansible_kernel }}
      CPU: {{ ansible_processor_count }} cores
      RAM: {{ ansible_memtotal_mb }} MB
      IP: {{ ansible_default_ipv4.address }}

# Custom facts — crea file in /etc/ansible/facts.d/ sui target
# /etc/ansible/facts.d/app.fact (JSON o INI)
# { "version": "2.1.0", "environment": "production" }
# Accessibile come: ansible_local.app.version
```

### Register e Debug

```yaml
- name: Verifica versione app
  command: /opt/app/bin/app --version
  register: app_version_output
  changed_when: false

- name: Mostra versione
  debug:
    var: app_version_output.stdout

- name: Fallisci se versione non corretta
  assert:
    that:
      - "'2.1' in app_version_output.stdout"
    fail_msg: "Versione app non corretta: {{ app_version_output.stdout }}"
```

### Precedenza Variabili — Livelli Chiave

Ansible definisce 22 livelli di precedenza (lista completa: vedi Letture Primarie). I livelli da ricordare:

```
role defaults (2) < group_vars (6-7) < host_vars (9-10) < play vars (12)
  < role vars (15) < set_fact (19) < extra vars -e (22, SEMPRE VINCE)
```

**Regola pratica**: usa `defaults/` per valori sovrascrivibili dall'utente del role. Usa `vars/` solo per costanti interne. Errore comune: `role/vars` (15) sovrascrive `group_vars` (6-7).

---

## Jinja2 Templates

### Template Base

```jinja2
{# templates/nginx.conf.j2 #}
# Generato da Ansible — NON MODIFICARE MANUALMENTE
# Host: {{ ansible_hostname }}
# Data: {{ ansible_date_time.iso8601 }}

user www-data;
worker_processes {{ nginx_worker_processes | default('auto') }};
pid /run/nginx.pid;

events {
    worker_connections {{ nginx_worker_connections | default(1024) }};
}

http {
    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    server_tokens off;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

{% if nginx_gzip_enabled | default(true) %}
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
{% endif %}

{% for server in nginx_servers | default([]) %}
    server {
        listen {{ server.port | default(80) }};
        server_name {{ server.name }};

{% if server.ssl | default(false) %}
        ssl_certificate /etc/ssl/certs/{{ server.name }}.pem;
        ssl_certificate_key /etc/ssl/private/{{ server.name }}.key;
{% endif %}

        location / {
{% if server.proxy_pass is defined %}
            proxy_pass {{ server.proxy_pass }};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
{% else %}
            root {{ server.root | default('/var/www/html') }};
            index index.html;
{% endif %}
        }
    }

{% endfor %}
}
```

### Filtri Jinja2 Utili

```jinja2
{# Filtri comuni #}
{{ variable | default('valore_default') }}
{{ list_var | join(', ') }}
{{ string_var | upper }}
{{ string_var | lower }}
{{ string_var | regex_replace('old', 'new') }}
{{ dict_var | to_json }}
{{ dict_var | to_yaml }}
{{ number_var | int }}
{{ password_var | password_hash('sha512') }}
{{ file_content | b64encode }}
{{ path_var | basename }}
{{ path_var | dirname }}
{{ list_var | unique }}
{{ list_var | sort }}
{{ list_var | length }}

{# Lookup #}
{{ lookup('file', '/path/to/file') }}
{{ lookup('env', 'HOME') }}
{{ lookup('password', '/dev/null length=32 chars=ascii_letters,digits') }}
```

---

## Jinja2 in Profondità

### Filtri Avanzati

```jinja2
{# map — applica un filtro/attributo a ogni elemento di una lista #}
{{ users | map(attribute='name') | list }}
{# Risultato: ['alice', 'bob', 'charlie'] da una lista di dizionari #}

{{ ports | map('int') | list }}
{# Converte tutti gli elementi in interi #}

{# select / selectattr — filtra elementi da una lista #}
{{ users | selectattr('active', 'equalto', true) | list }}
{# Filtra solo utenti attivi #}

{{ numbers | select('greaterthan', 10) | list }}
{# Filtra numeri > 10 #}

{{ services | selectattr('state', 'equalto', 'running') | map(attribute='name') | list }}
{# Nomi dei servizi in stato running #}

{# reject / rejectattr — opposto di select #}
{{ users | rejectattr('disabled', 'defined') | list }}
{# Rimuovi utenti con attributo 'disabled' #}

{# regex_replace — sostituzione con espressioni regolari #}
{{ hostname | regex_replace('^(\\w+)\\..*$', '\\1') }}
{# Estrai il primo componente del FQDN #}

{{ ip_address | regex_replace('(\\d+\\.\\d+\\.\\d+\\.)(\\d+)', '\\g<1>0/24') }}
{# 10.0.1.15 → 10.0.1.0/24 #}

{# ternary — operatore condizionale inline #}
{{ (env == 'production') | ternary('WARN', 'DEBUG') }}
{# Ritorna 'WARN' se produzione, 'DEBUG' altrimenti #}

{# combine — unisci dizionari #}
{{ default_config | combine(override_config) }}
{# Il secondo dizionario sovrascrive le chiavi del primo #}

{{ default_config | combine(override_config, recursive=True) }}
{# Unione ricorsiva per dizionari annidati #}

{# ipaddr — manipolazione indirizzi IP (richiede netaddr) #}
{{ '10.0.1.15/24' | ansible.utils.ipaddr('network') }}
{# 10.0.1.0 #}

{{ '10.0.1.15/24' | ansible.utils.ipaddr('prefix') }}
{# 24 #}

{# Formattazione e manipolazione stringhe #}
{{ 'my_variable_name' | replace('_', '-') }}
{{ items | map('regex_replace', '^(.*)$', 'prefix-\\1') | list }}
{{ long_string | truncate(80, True, '...') }}
{{ multiline_var | indent(4) }}

{# Calcoli e conversioni #}
{{ ansible_memtotal_mb | human_readable }}
{{ filesystem_size | human_to_bytes }}
{{ timestamp | to_datetime }}
{{ list_of_numbers | sum }}
{{ list_of_numbers | min }}
{{ list_of_numbers | max }}
```

### Test Jinja2

I test verificano condizioni sulle variabili — diversi dai filtri, si usano con `is`:

```jinja2
{# Test di esistenza #}
{% if my_var is defined %}...{% endif %}
{% if my_var is undefined %}...{% endif %}
{% if my_var is none %}...{% endif %}

{# Test su stringhe con regex #}
{% if hostname is match('^web\\d+') %}
  {# match verifica dall'inizio della stringa #}
{% endif %}

{% if log_line is search('ERROR|CRITICAL') %}
  {# search verifica in qualsiasi punto della stringa #}
{% endif %}

{% if version is version('2.0', '>=') %}
  {# Confronto tra versioni semver #}
{% endif %}

{# Test su tipi #}
{% if my_var is string %}...{% endif %}
{% if my_var is number %}...{% endif %}
{% if my_var is iterable %}...{% endif %}
{% if my_var is mapping %}...{% endif %}
{# mapping = dizionario #}

{# Test su file (nei template) #}
{% if '/etc/myapp/custom.conf' is file %}...{% endif %}
{% if '/opt/app' is directory %}...{% endif %}
{% if '/usr/local/bin/tool' is link %}...{% endif %}

{# Test combinati #}
{% if my_var is defined and my_var is not none and my_var | length > 0 %}
  {# La variabile esiste, non è null, e non è vuota #}
{% endif %}
```

### Lookup Avanzati

I lookup leggono dati da fonti esterne sul **control node** (non sui managed nodes):

```yaml
tasks:
  # file — legge contenuto di un file locale
  - name: Carica chiave SSH
    authorized_key:
      user: deploy
      key: "{{ lookup('file', '~/.ssh/id_ed25519.pub') }}"

  # env — legge variabile d'ambiente
  - name: Usa variabile d'ambiente
    debug:
      msg: "Home directory: {{ lookup('env', 'HOME') }}"

  # pipe — esegue comando e cattura output
  - name: Ottieni data corrente
    debug:
      msg: "Timestamp: {{ lookup('pipe', 'date +%Y%m%d-%H%M%S') }}"

  - name: Ottieni ultimo commit
    debug:
      msg: "Commit: {{ lookup('pipe', 'git rev-parse --short HEAD') }}"

  # password — genera password casuali
  - name: Genera password per database
    set_fact:
      db_generated_password: "{{ lookup('password', '/tmp/db_password length=24 chars=ascii_letters,digits,punctuation') }}"

  # password senza persistere su file:
  - name: Genera password temporanea
    set_fact:
      temp_password: "{{ lookup('password', '/dev/null length=32 chars=ascii_letters,digits') }}"

  # Altri lookup disponibili: csvfile, ini, dig (DNS), url, template, first_found
  # Documentazione: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/#lookup-plugins
```

---

## Roles

I roles sono l'unità di riutilizzo in Ansible. Organizzano playbook complessi in componenti modulari con una struttura directory standard.

### Struttura di un Role

```
roles/
└── myapp/
    ├── defaults/main.yml     # Variabili default — interfaccia pubblica (sovrascrivibile)
    ├── vars/main.yml         # Costanti interne — precedenza alta, NON sovrascrivere
    ├── tasks/
    │   ├── main.yml          # Entry point — include gli altri file
    │   ├── install.yml
    │   ├── configure.yml
    │   └── service.yml
    ├── handlers/main.yml     # Handler richiamati con notify
    ├── files/                # File statici copiati con copy
    ├── templates/            # Template Jinja2 processati con template
    ├── meta/main.yml         # Metadati: dipendenze, piattaforme, licenza
    ├── tests/                # Inventory + playbook per test locali
    └── molecule/default/     # Config Molecule per test automatici
```

### meta/main.yml — Dipendenze e Metadati

```yaml
# roles/myapp/meta/main.yml
---
galaxy_info:
  author: Renan Augusto Macena
  description: Role per installazione e configurazione di MyApp
  license: MIT
  min_ansible_version: "2.17"
  platforms:
    - name: Ubuntu
      versions: [jammy, noble]
    - name: Debian
      versions: [bookworm]
    - name: EL
      versions: [8, 9]

dependencies:
  # Dipendenze eseguite PRIMA del role corrente
  - role: common
    vars:
      common_packages:
        - curl
        - jq
  - role: nginx
    vars:
      nginx_worker_processes: "{{ myapp_nginx_workers | default('auto') }}"
  # Dipendenze da collection:
  - role: geerlingguy.docker
    when: myapp_containerized | default(false)
```

### Pattern di Riutilizzo dei Roles

```yaml
# 1. Inclusione classica nel play:
- hosts: webservers
  roles:
    - common
    - nginx
    - myapp

# 2. Inclusione con variabili:
- hosts: webservers
  roles:
    - role: nginx
      vars:
        nginx_port: 8080
    - role: myapp
      vars:
        myapp_version: "2.1.0"

# 3. Inclusione condizionale:
- hosts: all
  roles:
    - role: monitoring
      when: monitoring_enabled | default(true)

# 4. include_role dinamico (nel tasks):
- hosts: webservers
  tasks:
    - name: Includi role in base al tipo di app
      include_role:
        name: "{{ app_type }}_setup"
      vars:
        app_port: 8080

# 5. import_role statico (risolto a parse time):
- hosts: webservers
  tasks:
    - name: Importa role nginx
      import_role:
        name: nginx
      vars:
        nginx_port: 443
      tags: [nginx]
```

### Esempio Completo: Role PostgreSQL

```yaml
# roles/postgresql/defaults/main.yml
---
postgresql_version: 16
postgresql_listen_addresses: "127.0.0.1"
postgresql_port: 5432
postgresql_max_connections: 200
postgresql_shared_buffers: "{{ (ansible_memtotal_mb * 0.25) | int }}MB"
postgresql_effective_cache_size: "{{ (ansible_memtotal_mb * 0.75) | int }}MB"
postgresql_work_mem: "32MB"
postgresql_maintenance_work_mem: "512MB"

postgresql_databases: []
postgresql_users: []
postgresql_hba_entries:
  - { type: local, database: all, user: postgres, method: peer }
  - { type: local, database: all, user: all, method: scram-sha-256 }
  - { type: host, database: all, user: all, address: '127.0.0.1/32', method: scram-sha-256 }
```

```yaml
# roles/postgresql/tasks/main.yml
---
- name: Include install tasks
  include_tasks: install.yml

- name: Include configure tasks
  include_tasks: configure.yml

- name: Include databases tasks
  include_tasks: databases.yml
```

```yaml
# roles/postgresql/tasks/install.yml
---
- name: Aggiungi repository PostgreSQL
  apt:
    deb: "https://www.postgresql.org/media/keys/ACCC4CF8.asc"
  when: ansible_os_family == "Debian"

- name: Installa PostgreSQL
  apt:
    name:
      - "postgresql-{{ postgresql_version }}"
      - "postgresql-client-{{ postgresql_version }}"
      - python3-psycopg2
    state: present
```

```yaml
# roles/postgresql/tasks/configure.yml
---
- name: Configura postgresql.conf
  template:
    src: postgresql.conf.j2
    dest: "/etc/postgresql/{{ postgresql_version }}/main/postgresql.conf"
    owner: postgres
    group: postgres
    mode: '0644'
  notify: Restart PostgreSQL

- name: Configura pg_hba.conf
  template:
    src: pg_hba.conf.j2
    dest: "/etc/postgresql/{{ postgresql_version }}/main/pg_hba.conf"
    owner: postgres
    group: postgres
    mode: '0640'
  notify: Reload PostgreSQL

- name: Assicura che PostgreSQL sia avviato
  service:
    name: postgresql
    state: started
    enabled: true
```

```yaml
# roles/postgresql/handlers/main.yml
---
- name: Restart PostgreSQL
  service:
    name: postgresql
    state: restarted

- name: Reload PostgreSQL
  service:
    name: postgresql
    state: reloaded
```

### Uso dei Roles

```yaml
# site.yml
---
- name: Configura database servers
  hosts: dbservers
  become: true
  roles:
    - role: postgresql
      vars:
        postgresql_databases:
          - name: myapp
            owner: appuser
        postgresql_users:
          - name: appuser
            password: "{{ vault_db_password }}"
```

### argument_spec: Validazione dei Parametri dei Roles

A partire da Ansible 2.11, i roles possono dichiarare uno schema formale dei propri
parametri con `meta/argument_specs.yml`. Ansible valida automaticamente tipo, valori
obbligatori, range e scelte ammesse **prima** di eseguire qualunque task del role.
Questo elimina interi classi di errori runtime: variabili mancanti, tipi sbagliati,
valori fuori range.

```yaml
# roles/nginx/meta/argument_specs.yml
---
argument_specs:
  main:
    short_description: "Configura Nginx come reverse proxy"
    description:
      - "Installa, configura e avvia Nginx."
      - "Supporta Ubuntu 22.04+ e RHEL 8+."
    author: "Renan Augusto Macena"

    options:
      nginx_port:
        description: "Porta di ascolto per Nginx"
        type: int
        required: false
        default: 80
        # Validazione: la porta deve essere in range valido
        # (Ansible non supporta range nativi, ma il type check è automatico)

      nginx_worker_processes:
        description: "Numero di worker processes"
        type: str
        required: false
        default: "auto"
        choices:
          - "auto"
          - "1"
          - "2"
          - "4"
          - "8"

      nginx_ssl_enabled:
        description: "Abilita terminazione TLS"
        type: bool
        required: false
        default: false

      nginx_ssl_certificate:
        description: "Percorso al certificato TLS"
        type: path
        required: false
        # Richiesto solo quando SSL è abilitato — validato nelle task

      nginx_upstreams:
        description: "Lista di backend upstream"
        type: list
        required: true
        elements: dict
        options:
          name:
            description: "Nome del blocco upstream"
            type: str
            required: true
          servers:
            description: "Lista di server backend"
            type: list
            required: true
            elements: str
          method:
            description: "Algoritmo di bilanciamento"
            type: str
            required: false
            default: "round_robin"
            choices:
              - "round_robin"
              - "least_conn"
              - "ip_hash"

      nginx_rate_limit:
        description: "Rate limiting (es. 10r/s)"
        type: str
        required: false

  # Entry point secondario per sotto-task specifiche
  configure_ssl:
    short_description: "Configura solo i certificati SSL"
    options:
      nginx_ssl_certificate:
        type: path
        required: true
      nginx_ssl_private_key:
        type: path
        required: true
      nginx_ssl_protocols:
        type: list
        elements: str
        default:
          - "TLSv1.2"
          - "TLSv1.3"
```

**Cosa succede con parametri invalidi:**

```bash
# Invocazione con tipo sbagliato
$ ansible-playbook site.yml -e "nginx_port=not_a_number"
# ERRORE: argument 'nginx_port' is of type <class 'str'> and we were
# unable to convert to int: invalid literal for int()

# Invocazione con scelta non valida
$ ansible-playbook site.yml -e "nginx_worker_processes=16"
# ERRORE: value of nginx_worker_processes must be one of: auto, 1, 2, 4, 8

# Parametro obbligatorio mancante
$ ansible-playbook site.yml  # senza nginx_upstreams
# ERRORE: missing required arguments: nginx_upstreams
```

**Validazione custom nelle task con assert:**

```yaml
# roles/nginx/tasks/validate.yml
# Per validazioni più complesse non esprimibili in argument_specs
---
- name: Valida combinazione SSL
  assert:
    that:
      - nginx_ssl_certificate is defined
      - nginx_ssl_private_key is defined
    fail_msg: >-
      Quando nginx_ssl_enabled=true, devi definire
      nginx_ssl_certificate e nginx_ssl_private_key
  when: nginx_ssl_enabled | bool

- name: Valida che la porta non sia privilegiata senza become
  assert:
    that:
      - nginx_port >= 1024 or ansible_become | default(false)
    fail_msg: >-
      La porta {{ nginx_port }} richiede privilegi root.
      Usa become: true oppure una porta >= 1024
```

**Documentazione automatica:**

```bash
# Genera documentazione del role a partire da argument_specs
ansible-doc -t role nginx

# Output strutturato per tool di CI
ansible-doc -t role nginx -j | python3 -m json.tool
```

> **Best practice:** Dichiara `argument_specs` per tutti i roles destinati a team
> multipli o a Ansible Galaxy. Il costo è un singolo file YAML; il beneficio è
> validazione automatica, documentazione gratis, e messaggi d'errore chiari.

---

## Collections

Le collections sono il meccanismo di distribuzione moderno di Ansible. Raggruppano moduli, roles, plugin e documentazione in pacchetti installabili con namespace.

### Installazione di Collections

```bash
# Installa singola collection
ansible-galaxy collection install amazon.aws
ansible-galaxy collection install google.cloud
ansible-galaxy collection install azure.azcollection
ansible-galaxy collection install community.general

# Installa versione specifica
ansible-galaxy collection install community.postgresql:>=3.0.0,<4.0.0

# Installa da requirements.yml (raccomandato per progetto)
ansible-galaxy collection install -r requirements.yml
```

```yaml
# requirements.yml — blocca le versioni per riproducibilità
---
collections:
  - name: amazon.aws
    version: ">=7.0.0,<8.0.0"
  - name: community.general
    version: ">=8.0.0"
  - name: community.postgresql
    version: ">=3.0.0"
  - name: ansible.posix
    version: ">=1.5.0"
  - name: ansible.utils
    version: ">=3.0.0"

roles:
  - name: geerlingguy.docker
    version: "7.1.0"
  - name: geerlingguy.certbot
    version: "5.1.0"
```

```bash
# Installa tutto da requirements.yml
ansible-galaxy install -r requirements.yml

# Installa in directory locale al progetto
ansible-galaxy collection install -r requirements.yml -p ./collections/
```

### Formato Namespace.Collection (FQCN)

Usa sempre il **Fully Qualified Collection Name** nei task:

```yaml
tasks:
  - amazon.aws.ec2_instance: { name: web-01, instance_type: t3.medium, state: running }
  - community.docker.docker_container: { name: myapp, image: "myapp:latest", state: started }
  # NON RACCOMANDATO: nome breve (ec2_instance) — ambiguo con più collection
```

### Creare una Collection Personalizzata

```bash
ansible-galaxy collection init mycompany.infrastructure
# Struttura: galaxy.yml, plugins/{modules,filter,lookup,callback,inventory}/,
#            roles/, playbooks/, meta/runtime.yml, tests/
```

Configura `galaxy.yml` con namespace, name, version, dependencies. Build: `ansible-galaxy collection build`. Installa locale: `ansible-galaxy collection install mycompany-infrastructure-1.0.0.tar.gz`. Pubblica su Galaxy: `ansible-galaxy collection publish <tarball> --api-key=<token>`.

---

## Ansible Vault

Vault permette di criptare variabili sensibili (password, chiavi API, certificati) che devono essere versionati in git.

```bash
# Crea file criptato
ansible-vault create group_vars/all/vault.yml

# Cripta file esistente
ansible-vault encrypt group_vars/production/secrets.yml

# Decripta
ansible-vault decrypt group_vars/production/secrets.yml

# Modifica file criptato
ansible-vault edit group_vars/production/secrets.yml

# Visualizza contenuto
ansible-vault view group_vars/production/secrets.yml

# Cambia password
ansible-vault rekey group_vars/production/secrets.yml
```

### Struttura Raccomandata

```yaml
# group_vars/all/vars.yml — variabili in chiaro
---
db_host: db01.example.com
db_name: myapp
db_user: appuser

# group_vars/all/vault.yml — variabili criptate
---
vault_db_password: "s3cur3_p4ssw0rd"
vault_api_key: "ak_live_xxxxxxxxx"
vault_ssl_private_key: |
  -----BEGIN PRIVATE KEY-----
  ...
  -----END PRIVATE KEY-----
```

```yaml
# Uso nelle variabili in chiaro (riferimento al vault)
# group_vars/all/vars.yml
db_password: "{{ vault_db_password }}"
api_key: "{{ vault_api_key }}"
```

```bash
# Esecuzione con vault
ansible-playbook site.yml --ask-vault-pass

# Oppure con password file
echo "vault_password_here" > .vault_pass
chmod 600 .vault_pass
ansible-playbook site.yml --vault-password-file .vault_pass

# Oppure in ansible.cfg:
# [defaults]
# vault_password_file = .vault_pass
```

---

## Vault Avanzato

### Vault Inline con encrypt_string

Invece di criptare un intero file, puoi criptare singole variabili inline:

```bash
# Cripta una stringa per inserirla in un file YAML
ansible-vault encrypt_string 's3cur3_p4ssw0rd' --name 'vault_db_password'

# Output (incolla nel tuo vars file):
# vault_db_password: !vault |
#   $ANSIBLE_VAULT;1.1;AES256
#   36623964613663373...

# Cripta leggendo da stdin (per evitare che la password appaia nella history):
echo -n 'my_secret_value' | ansible-vault encrypt_string --stdin-name 'vault_api_key'

# Cripta con vault-id specifico:
ansible-vault encrypt_string --vault-id prod@prompt 's3cur3' --name 'vault_db_password'
```

```yaml
# group_vars/all/vars.yml — inline vault mescolato con variabili in chiaro
---
db_host: db01.example.com
db_name: myapp
db_user: appuser
db_password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  36623964613663373838363133636639386365396534613038653764643838626263
  3933633862343737316562326365383735373230356138650a306639616134353362
  ...
api_key: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  61383935653732616266...
```

### Multi-Vault ID

In ambienti con più livelli di accesso (dev, staging, prod), usa vault ID diversi con password diverse:

```bash
# Cripta file con vault ID specifici
ansible-vault encrypt --vault-id dev@prompt group_vars/development/vault.yml
ansible-vault encrypt --vault-id staging@prompt group_vars/staging/vault.yml
ansible-vault encrypt --vault-id prod@/path/to/prod_vault_pass group_vars/production/vault.yml

# Il vault ID viene registrato nell'header del file criptato:
# $ANSIBLE_VAULT;1.2;AES256;prod

# Esecuzione con vault ID multipli:
ansible-playbook site.yml \
  --vault-id dev@prompt \
  --vault-id prod@/path/to/prod_vault_pass

# ansible.cfg con vault ID:
# [defaults]
# vault_identity_list = dev@/path/to/dev_pass, prod@/path/to/prod_pass
```

### Vault con Script di Password

Per CI/CD, crea uno script bash che legge la password da un secret manager (HashiCorp Vault, AWS Secrets Manager, env vars) in base al vault-id passato come `$1`. Uso: `--vault-id prod@vault-password-client.sh`. `chmod 700` sullo script.

### Best Practice per Vault

- Prefissa tutte le variabili criptate con `vault_` (es. `vault_db_password`)
- In `vars.yml` referenzia: `db_password: "{{ vault_db_password }}"`
- Vantaggi: grep facile sui segreti, separazione definizione/uso
- I file vault **devono** essere in git (sono criptati). Ignora solo il file con la password (`.vault_pass`)

---

## Handlers, Tags e Strategie

### Handlers

```yaml
# Gli handler vengono eseguiti una sola volta alla fine del play,
# indipendentemente da quante task li notificano

handlers:
  - name: Restart Nginx
    service:
      name: nginx
      state: restarted

  - name: Reload Nginx
    service:
      name: nginx
      state: reloaded

  # Handler chain
  - name: Validate Nginx config
    command: nginx -t
    listen: "restart nginx safely"

  - name: Restart Nginx after validation
    service:
      name: nginx
      state: restarted
    listen: "restart nginx safely"
```

### Tags

```yaml
tasks:
  - name: Installa pacchetti
    apt:
      name: nginx
      state: present
    tags: [install, nginx]

  - name: Configura Nginx
    template:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf
    tags: [config, nginx]

  - name: Deploy applicazione
    git:
      repo: https://github.com/org/app.git
      dest: /opt/app
    tags: [deploy]
```

```bash
# Esegui solo task con tag specifici
ansible-playbook site.yml --tags "config"
ansible-playbook site.yml --tags "deploy,config"

# Escludi tag
ansible-playbook site.yml --skip-tags "install"

# Lista task con relativi tag
ansible-playbook site.yml --list-tasks
```

---

## Strategie di Esecuzione Avanzate

### serial e max_fail_percentage

```yaml
# serial — esegui il play in batch di N host alla volta
# Fondamentale per rolling update senza downtime

- name: Rolling update dei web server
  hosts: webservers
  become: true
  serial: 2                    # 2 host alla volta
  # serial: "30%"             # oppure percentuale
  # serial: [1, 3, 5]         # prima 1, poi 3, poi 5 alla volta (rampa)
  max_fail_percentage: 25      # interrompi se >25% dei batch fallisce

  pre_tasks:
    - name: Rimuovi dal load balancer
      uri:
        url: "http://lb.example.com/api/backends/{{ inventory_hostname }}/disable"
        method: POST
      delegate_to: localhost

  roles:
    - myapp

  post_tasks:
    - name: Verifica health check
      uri:
        url: "http://{{ ansible_host }}:{{ app_port }}/health"
        status_code: 200
      retries: 5
      delay: 3

    - name: Riaggiungi al load balancer
      uri:
        url: "http://lb.example.com/api/backends/{{ inventory_hostname }}/enable"
        method: POST
      delegate_to: localhost
```

### Strategy Plugin

Tre strategie disponibili:
- **linear** (default): ogni task completata su tutti gli host prima di passare alla successiva
- **free**: host procedono indipendentemente senza sincronizzazione
- **debug**: si ferma ad ogni errore per debugging interattivo (solo sviluppo)

Configurazione globale: `strategy = linear` in ansible.cfg `[defaults]`.

### throttle — Limitare il Parallelismo per Task

```yaml
tasks:
  # throttle è diverso da serial: limita una singola task, non il play intero
  - name: Migrazione database (max 1 alla volta)
    command: /opt/app/manage.py migrate
    throttle: 1

  - name: Restart con rate limiting (max 3 in parallelo)
    service:
      name: myapp
      state: restarted
    throttle: 3
```

### run_once — Esegui una Sola Volta

`run_once: true` esegue la task solo sul primo host del batch (utile per migrazioni DB, notifiche). Combinabile con `delegate_to: localhost` per azioni centralizzate.

### Flushing degli Handler

`meta: flush_handlers` forza l'esecuzione degli handler pendenti immediatamente, invece di attendere la fine del play. Utile per verificare health check dopo restart.

---
## Idempotenza: Principi e Pratica

L'idempotenza è il principio fondamentale di Ansible: eseguire un playbook più volte produce lo stesso risultato. Un playbook ben scritto mostra "changed=0" quando lo stato desiderato è già raggiunto.

### Scrivere Task Idempotenti

```yaml
# SBAGLIATO — command/shell non sono idempotenti per default
- name: Crea utente
  command: useradd deploy

# CORRETTO — usa il modulo dedicato (idempotente per design)
- name: Crea utente
  user:
    name: deploy
    state: present

# SBAGLIATO — scarica file ogni volta
- name: Scarica applicazione
  command: wget https://releases.example.com/app-2.1.tar.gz -O /tmp/app.tar.gz

# CORRETTO — usa get_url con checksum
- name: Scarica applicazione
  get_url:
    url: https://releases.example.com/app-2.1.tar.gz
    dest: /tmp/app.tar.gz
    checksum: sha256:abcdef1234567890...

# SBAGLIATO — esegue sempre
- name: Inizializza database
  command: /opt/app/init-db.sh

# CORRETTO — usa creates per skip se già eseguito
- name: Inizializza database
  command: /opt/app/init-db.sh
  args:
    creates: /opt/app/.db_initialized

# CORRETTO alternativo — usa una condizione
- name: Verifica se il database è inizializzato
  stat:
    path: /opt/app/.db_initialized
  register: db_init_flag

- name: Inizializza database
  command: /opt/app/init-db.sh
  when: not db_init_flag.stat.exists
```

### changed_when e failed_when

```yaml
tasks:
  # changed_when — controlla quando una task è "changed"
  - name: Verifica stato del cluster
    command: /opt/cluster/status.sh
    register: cluster_status
    changed_when: false          # comando di sola lettura — mai "changed"

  - name: Applica migrazione
    command: /opt/app/manage.py migrate
    register: migrate_output
    changed_when: "'Applying' in migrate_output.stdout"
    # "changed" solo se la migrazione ha effettivamente applicato qualcosa

  - name: Aggiungi riga a crontab
    command: >
      crontab -l | grep -q 'backup.sh' ||
      (crontab -l; echo '0 2 * * * /opt/backup.sh') | crontab -
    register: cron_result
    changed_when: cron_result.rc == 0 and 'no crontab' not in cron_result.stderr

  # failed_when — controlla quando una task è "failed"
  - name: Verifica connessione al database
    command: pg_isready -h {{ db_host }} -p {{ db_port }}
    register: pg_check
    failed_when: pg_check.rc != 0 and pg_check.rc != 2
    # rc=2 significa "accetta connessioni ma rifiuta" — non è un fallimento

  - name: Verifica spazio disco
    shell: df -h / | awk 'NR==2 {print $5}' | tr -d '%'
    register: disk_usage
    failed_when: disk_usage.stdout | int > 90
    changed_when: false
```

### Check Mode (Dry Run) e Diff

```bash
# Dry run — mostra cosa cambierebbe SENZA modificare nulla
ansible-playbook site.yml --check

# Dry run con diff — mostra il diff dei file che cambierebbero
ansible-playbook site.yml --check --diff

# Solo diff (senza check — applica E mostra il diff)
ansible-playbook site.yml --diff
```

```yaml
tasks:
  # Alcune task devono sempre eseguire anche in check mode:
  - name: Raccogli stato corrente (necessario per condizionali)
    command: /opt/app/version.sh
    register: app_version
    check_mode: false          # esegui anche in --check

  # Alcune task non supportano check mode:
  - name: Esegui script custom
    command: /opt/setup.sh
    args:
      creates: /opt/.setup_done
    # command non supporta nativamente --check, ma creates lo rende safe
```

---

## Testing con Molecule

Molecule è il framework standard per testare Ansible roles in ambienti isolati (container Docker, VM, cloud). Garantisce che i roles funzionino correttamente prima del deployment in produzione.

### Installazione

```bash
pip3 install molecule molecule-plugins[docker]

# Oppure con supporto Podman:
# pip3 install molecule molecule-plugins[podman]

# Verifica:
molecule --version
```

### Inizializzazione di un Role con Molecule

```bash
# Crea un nuovo role con scaffolding Molecule:
molecule init role mycompany.myapp --driver-name docker

# Oppure aggiungi Molecule a un role esistente:
cd roles/myapp/
molecule init scenario --driver-name docker
```

### Configurazione Molecule

```yaml
# roles/myapp/molecule/default/molecule.yml — essenziale
---
driver:
  name: docker
platforms:
  - name: instance-ubuntu
    image: ubuntu:24.04
    pre_build_image: true
    command: /lib/systemd/systemd
    privileged: true
provisioner:
  name: ansible
verifier:
  name: ansible
lint: |
  set -e
  yamllint .
  ansible-lint
```

```yaml
# converge.yml — applica il role
---
- name: Converge
  hosts: all
  become: true
  roles:
    - role: myapp
```

```yaml
# verify.yml — asserzioni post-converge
---
- name: Verify
  hosts: all
  become: true
  gather_facts: false
  tasks:
    - service_facts:
    - assert:
        that:
          - "'myapp.service' in ansible_facts.services"
          - "ansible_facts.services['myapp.service'].state == 'running'"
    - wait_for: { port: 8080, timeout: 10 }
    - uri: { url: "http://localhost:8080/health", status_code: 200 }
```

### Comandi Molecule

```bash
# Workflow completo:
molecule test                # Esegue l'intera sequenza: create → converge → verify → destroy

# Step individuali:
molecule create              # Crea le istanze (container/VM)
molecule converge            # Esegui il role sulle istanze
molecule verify              # Esegui le verifiche
molecule idempotence         # Riesegui converge — verifica che changed=0
molecule destroy             # Distruggi le istanze
molecule login               # SSH nella istanza per debugging
molecule lint                # Esegui yamllint + ansible-lint

# Scenario specifico:
molecule test -s my_scenario
```

### ansible-lint e yamllint

```bash
pip3 install ansible-lint yamllint
ansible-lint roles/myapp/          # Profili: min, basic, moderate, safety, shared, production
```

Configura `.ansible-lint` (profilo, skip_list, exclude_paths) e `.yamllint` (line-length, indentation) nella root del progetto.

### Integrazione CI/CD

Pipeline tipica in GitHub Actions: job `lint` (yamllint + ansible-lint) → job `molecule` (matrix multi-distro). Installa `ansible-core`, `molecule`, `molecule-plugins[docker]`, esegui `molecule test`.

---

## Performance e Ottimizzazione

### SSH Pipelining

Il pipelining è l'ottimizzazione più impattante. Senza pipelining, Ansible esegue 4+ connessioni SSH per task. Con pipelining, una sola.

```ini
# ansible.cfg
[ssh_connection]
pipelining = True

# ATTENZIONE: pipelining richiede che requiretty NON sia impostato
# in /etc/sudoers sui managed nodes:
# Defaults    !requiretty    ← aggiungere se manca
```

### SSH ControlMaster (Multiplexing)

```ini
# ansible.cfg — già attivo nel template precedente, ma ecco il dettaglio:
[ssh_connection]
ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o PreferredAuthentications=publickey

# ControlMaster: riutilizza la connessione SSH tra task
# ControlPersist: mantieni la connessione aperta 60 secondi dopo l'ultima task
# PreferredAuthentications: salta tentativi GSSAPI/password, accelera l'handshake
```

### Mitogen

Plugin di strategia che sostituisce il trasporto SSH con un protocollo ottimizzato (2-7x più veloce). `pip3 install mitogen`, configura `strategy = mitogen_linear` in ansible.cfg. Benchmark tipico: SSH vanilla 180s → SSH+pipelining+CM 45s → Mitogen 25s.

### Fact Caching

Per default, Ansible raccoglie i facts ad ogni esecuzione (`gather_facts: true`). Con centinaia di host, questo è costoso. Il fact caching salva i facts tra le esecuzioni.

```ini
# ansible.cfg — cache facts in file JSON locali
[defaults]
gathering = smart              # Raccogli solo se non in cache
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts_cache
fact_caching_timeout = 3600    # Scadenza in secondi (1 ora)
```

Alternativa Redis per ambienti multi-utente: `fact_caching = redis`, `fact_caching_connection = localhost:6379:0`. Valori `gathering`: `implicit` (default, sempre), `explicit` (solo se `gather_facts: true`), `smart` (solo se non in cache).

### Task Asincrone e Polling

Per task lunghe (compile, migrazioni), usa `async` + `poll`:

```yaml
- name: Aggiorna pacchetti
  apt: { upgrade: dist, update_cache: true }
  async: 600         # timeout secondi
  poll: 15           # controlla ogni 15s

- name: Build in background
  command: /opt/app/build.sh
  async: 3600
  poll: 0            # fire-and-forget
  register: build_job

- name: Attendi build
  async_status: { jid: "{{ build_job.ansible_job_id }}" }
  register: build_result
  until: build_result.finished
  retries: 120
  delay: 30
```

### Forks — Parallelismo

```ini
# ansible.cfg
[defaults]
forks = 20                     # Quanti host in parallelo (default 5)

# Regola empirica:
# - 5   → test / piccoli ambienti
# - 20  → ambienti medi (50-100 host)
# - 50  → ambienti grandi (500+ host) — richiede risorse sul control node
# - Controlla RAM e CPU del control node: ogni fork è un processo Python

# Override da command line:
# ansible-playbook site.yml -f 50
```

### Ottimizzare Playbook Lenti

1. `gather_subset: [network, hardware]` — raccolta facts selettiva
2. `strategy: free` — host indipendenti procedono senza sincronizzazione
3. Batch installs: `apt: { name: [a, b, c, d] }` (1 SSH) vs `loop` (N SSH)

---

## Sicurezza Avanzata

### become — Escalazione di Privilegi

```yaml
# Play-level become:
- hosts: webservers
  become: true                 # Diventa root per tutte le task
  become_method: sudo          # sudo, su, pbrun, pfexec, doas, dzdo, ksu, runas
  become_user: root            # Utente target (default: root)
  tasks: [...]

# Task-level become:
- name: Installa pacchetto (richiede root)
  apt:
    name: nginx
    state: present
  become: true

- name: Esegui come utente applicativo (NON root)
  command: /opt/app/start.sh
  become: true
  become_user: app             # Diventa utente 'app', non root

# become_flags per casi speciali:
- name: Diventa utente con login shell
  command: whoami
  become: true
  become_user: deploy
  become_flags: '-i'           # Simula login shell (-i per sudo)
```

### Metodi di Escalazione

Metodi disponibili: `sudo` (default Linux), `su`, `pbrun` (PowerBroker), `doas` (OpenBSD), `runas` (Windows). Configurabili in ansible.cfg `[privilege_escalation]` o per-play con `become_method`.

### Gestione Chiavi SSH

```yaml
# Pattern: distribuzione chiavi SSH con Ansible
- name: Gestione chiavi SSH
  hosts: all
  become: true
  tasks:
    - user: { name: deploy, groups: sudo, shell: /bin/bash }
    - authorized_key:
        user: deploy
        key: "{{ item }}"
        state: present
      loop: "{{ authorized_ssh_keys }}"
    - authorized_key:
        user: deploy
        key: "{{ item }}"
        state: absent
      loop: "{{ revoked_ssh_keys | default([]) }}"
    - file: { path: /home/deploy/.ssh, state: directory, owner: deploy, mode: '0700' }
```

### no_log — Nascondere Dati Sensibili

`no_log: true` impedisce che valori sensibili appaiano nell'output e nei log. Usalo su ogni task che manipola password, API key, certificati. Senza `no_log`, l'output mostra i valori in chiaro. Con `no_log`: `{"censored": "..."}`. Attenzione: nasconde anche gli errori — per debug temporaneo, rimuovilo o usa `-vvvv`.

### Sicurezza dell'Ambiente Ansible

Checklist protezione control node:
1. Mai eseguire Ansible come root sul control node
2. `chmod 0600` su ansible.cfg e inventory
3. Ruotare password vault periodicamente
4. Audit trail: `log_path = /var/log/ansible/ansible.log`
5. Guard produzione: `assert` + `fail_msg` prima di azioni distruttive
6. `--check --diff` prima di ogni applicazione in produzione

---

## Ansible AWX / AAP

AWX è la versione open-source di Ansible Automation Platform (AAP, ex Tower). Fornisce UI web, API REST, RBAC, scheduling, logging centralizzato e gestione credenziali per l'esecuzione di playbook Ansible in ambiente enterprise.

### Architettura AWX

```
┌─────────────────────────────────────────────────────────────┐
│                        AWX / AAP                             │
│                                                              │
│  ┌───────────┐  ┌────────────┐  ┌──────────────────────┐   │
│  │   Web UI   │  │  REST API  │  │   Task Dispatcher     │   │
│  │ (Angular)  │  │ (Django)   │  │   (Redis + Workers)   │   │
│  └─────┬─────┘  └─────┬──────┘  └──────────┬───────────┘   │
│        │               │                     │               │
│  ┌─────▼───────────────▼─────────────────────▼───────────┐  │
│  │              PostgreSQL Database                        │  │
│  │  (inventory, credentials, job history, RBAC)           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Projects     │  │  Credentials  │  │  Inventories     │  │
│  │ (git repos)  │  │  (vault, SSH) │  │  (static/dynamic)│  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ SSH / WinRM
             ┌────────────┼────────────┐
     ┌───────▼──┐  ┌──────▼──┐  ┌─────▼────┐
     │ Managed  │  │ Managed │  │ Managed  │
     │ Node 1   │  │ Node 2  │  │ Node N   │
     └──────────┘  └─────────┘  └──────────┘
```

### Concetti Fondamentali AWX

```
ORGANIZZAZIONE → TEAM → UTENTE
       │
       ├── PROGETTO (repository git con playbook)
       │
       ├── INVENTARIO (host/gruppi, statico o sincronizzato)
       │
       ├── CREDENZIALE (SSH key, vault password, cloud creds)
       │
       └── JOB TEMPLATE
                │
                ├── Playbook (dal progetto)
                ├── Inventario
                ├── Credenziale
                ├── Variabili extra
                └── Schedule (cron-like, opzionale)
                     │
                     └── JOB (esecuzione singola, con log e status)
```

### Installazione AWX

AWX si installa su Kubernetes tramite **AWX Operator** (`kubectl apply` del manifest operator + custom resource `AWX`). Riferimento: https://ansible.readthedocs.io/projects/awx-operator/ (consultato 2026-05-23)

### Job Template — Esempio

```yaml
# Configurazione Job Template in AWX (via API o UI):

# Nome: Deploy Web Application
# Progetto: myapp-ansible (repository git)
# Playbook: playbooks/deploy.yml
# Inventario: Production
# Credenziale: SSH Key Deploy + Vault Password
# Variabili extra (survey):
#   app_version: "2.1.0"
#   deploy_strategy: "rolling"
# Verbosity: 1 (Normal)
# Forks: 20
# Job Tags: deploy
# Limiti: webservers
# Callback: webhook Slack su completamento

# Esempio API per lanciare un job:
# curl -X POST https://awx.example.com/api/v2/job_templates/42/launch/ \
#   -H "Authorization: Bearer <token>" \
#   -H "Content-Type: application/json" \
#   -d '{"extra_vars": {"app_version": "2.2.0"}}'
```

### RBAC (Role-Based Access Control)

```
RUOLI BUILT-IN AWX:

Admin           → Tutto (organizzazione)
Auditor         → Sola lettura su tutto
Execute         → Può lanciare job template
Read            → Sola lettura su risorse specifiche
Use             → Può usare credenziali/inventari nei job template
Update          → Può aggiornare progetti (git pull)

PATTERN RBAC:

Organizzazione: OPS
├── Team: Platform Engineers
│   ├── Permessi: Admin su tutti i progetti/inventari
│   └── Utenti: alice, bob
├── Team: Developers
│   ├── Permessi: Execute su "Deploy App", Read su inventari
│   └── Utenti: charlie, dave
└── Team: Security
    ├── Permessi: Auditor, Execute su "Security Scan"
    └── Utenti: eve
```

---

## Pattern Reali: Rolling Update

Il rolling update aggiorna i server un batch alla volta, mantenendo il servizio disponibile durante il deployment.

```yaml
# playbooks/rolling-update.yml
---
- name: Rolling Update - Web Application
  hosts: webservers
  become: true
  serial: "25%"                # Aggiorna 25% dei server alla volta
  max_fail_percentage: 10      # Interrompi se >10% dei batch fallisce
  order: sorted                # Ordine prevedibile (sorted, reverse_sorted, shuffle)

  pre_tasks:
    - name: Verifica salute pre-deploy
      uri:
        url: "http://{{ ansible_host }}:{{ app_port }}/health"
        status_code: 200
      retries: 3
      delay: 2

    - name: Rimuovi dal load balancer
      uri:
        url: "http://{{ lb_api }}/api/v1/backends/{{ inventory_hostname }}"
        method: DELETE
        headers:
          Authorization: "Bearer {{ vault_lb_token }}"
      delegate_to: localhost

    - name: Attendi drain delle connessioni
      pause:
        seconds: 10

  roles:
    - role: myapp
      vars:
        myapp_version: "{{ deploy_version }}"

  post_tasks:
    - name: Verifica health check post-deploy
      uri:
        url: "http://{{ ansible_host }}:{{ app_port }}/health"
        status_code: 200
      retries: 10
      delay: 5
      register: health_check

    - name: Riaggiungi al load balancer
      uri:
        url: "http://{{ lb_api }}/api/v1/backends"
        method: POST
        body_format: json
        body:
          hostname: "{{ inventory_hostname }}"
          address: "{{ ansible_host }}"
          port: "{{ app_port }}"
        headers:
          Authorization: "Bearer {{ vault_lb_token }}"
      delegate_to: localhost

    - name: Attendi stabilizzazione
      pause:
        seconds: 15
```

---

## Pattern Reali: Canary Deployment

Il canary deployment invia prima il traffico a un piccolo sottoinsieme di server per validare la nuova versione prima di procedere.

```yaml
# playbooks/canary-deploy.yml
---
# Fase 1: Deploy sul canary (1 server)
- name: Canary Deploy - Fase 1
  hosts: webservers[0]         # Solo il primo server
  become: true
  serial: 1

  tasks:
    - name: Deploy versione canary
      include_role:
        name: myapp
      vars:
        myapp_version: "{{ deploy_version }}"

    - name: Verifica health check canary
      uri:
        url: "http://{{ ansible_host }}:{{ app_port }}/health"
        status_code: 200
      retries: 10
      delay: 5

    - name: Attendi periodo di osservazione
      pause:
        seconds: 120
        prompt: "Canary in esecuzione su {{ inventory_hostname }}. Verifica metriche. Premi ENTER per continuare o Ctrl+C per interrompere."

    # Verifica metriche canary via monitoring API (Prometheus/Grafana):
    # query error rate 5xx, assert < 5%, altrimenti fail_msg interrompe il deploy
    # delegate_to: localhost per raggiungere l'API di monitoring

# Fase 2: Deploy su tutti gli altri
- name: Canary Deploy - Fase 2 (rollout completo)
  hosts: webservers[1:]        # Tutti tranne il canary
  become: true
  serial: "33%"
  max_fail_percentage: 10

  roles:
    - role: myapp
      vars:
        myapp_version: "{{ deploy_version }}"

  post_tasks:
    - name: Verifica health check
      uri:
        url: "http://{{ ansible_host }}:{{ app_port }}/health"
        status_code: 200
      retries: 10
      delay: 5
```

---

## Pattern Reali: Blue-Green Deployment

Il blue-green deployment mantiene due ambienti identici (blue e green). Il traffico viene spostato dall'ambiente attivo a quello inattivo dopo il deploy. Struttura in 3 play:

```yaml
# playbooks/blue-green-deploy.yml — schema
---
# Play 1: Identifica ambiente attivo via LB API, calcola target
- name: Blue-Green - Identifica ambiente
  hosts: localhost
  tasks:
    - uri:
        url: "http://{{ lb_api }}/api/v1/active-environment"
      register: active_env
    - set_fact:
        target_env: "{{ 'green' if active_env.json.environment == 'blue' else 'blue' }}"

# Play 2: Deploy + health check sull'ambiente inattivo
- name: Blue-Green - Deploy
  hosts: "{{ hostvars.localhost.target_env }}_servers"
  become: true
  tasks:
    - include_role: { name: myapp }
    - uri: { url: "http://{{ ansible_host }}:{{ app_port }}/health", status_code: 200 }
      retries: 15
      delay: 5

# Play 3: Switch traffico via LB API + verifica
- name: Blue-Green - Switch
  hosts: localhost
  tasks:
    - uri:
        url: "http://{{ lb_api }}/api/v1/switch"
        method: POST
        body_format: json
        body: { environment: "{{ target_env }}" }
    - uri: { url: "http://{{ app_domain }}/api/v1/status" }
      register: final_check
      retries: 5
      delay: 5
```

---

## Pattern Reali: Infrastructure Provisioning

Ansible può orchestrare la creazione di infrastruttura cloud (VPC, subnet, security group, istanze) e poi configurare le istanze appena create, il tutto in un unico playbook a due fasi:

1. **Fase locale** (`hosts: localhost`): usa collection cloud (`amazon.aws`, `google.cloud`, `azure.azcollection`) per creare risorse e aggiungerle all'inventory in-memory con `add_host`
2. **Fase remota** (`hosts: new_servers`): configura i nodi appena creati applicando roles

Per esempi completi di provisioning multi-cloud, vedi il **Modulo 25 (Cloud Infrastructure)**. Collection di riferimento: `amazon.aws`, `google.cloud`, `azure.azcollection`.

---

## Pattern Comuni: LAMP Stack

```yaml
# playbooks/lamp.yml — LAMP stack completo
---
- name: Setup LAMP Stack
  hosts: webservers
  become: true

  vars:
    mysql_root_password: "{{ vault_mysql_root_password }}"
    app_db_name: myapp
    app_db_user: myapp
    app_db_password: "{{ vault_app_db_password }}"
    php_version: "8.3"
    document_root: /var/www/myapp

  tasks:
    # Apache
    - name: Installa Apache
      apt:
        name:
          - apache2
          - libapache2-mod-php{{ php_version }}
        state: present

    - name: Abilita moduli Apache
      apache2_module:
        name: "{{ item }}"
        state: present
      loop: [rewrite, ssl, headers]
      notify: Restart Apache

    # PHP
    - name: Installa PHP e estensioni
      apt:
        name:
          - "php{{ php_version }}"
          - "php{{ php_version }}-mysql"
          - "php{{ php_version }}-curl"
          - "php{{ php_version }}-gd"
          - "php{{ php_version }}-mbstring"
          - "php{{ php_version }}-xml"
          - "php{{ php_version }}-zip"
        state: present

    # MariaDB
    - name: Installa MariaDB
      apt:
        name:
          - mariadb-server
          - mariadb-client
          - python3-pymysql
        state: present

    - name: Avvia MariaDB
      service:
        name: mariadb
        state: started
        enabled: true

    - name: Imposta password root MariaDB
      mysql_user:
        name: root
        password: "{{ mysql_root_password }}"
        login_unix_socket: /var/run/mysqld/mysqld.sock
        state: present

    - name: Crea database applicazione
      mysql_db:
        name: "{{ app_db_name }}"
        state: present
        login_user: root
        login_password: "{{ mysql_root_password }}"

    - name: Crea utente database
      mysql_user:
        name: "{{ app_db_user }}"
        password: "{{ app_db_password }}"
        priv: "{{ app_db_name }}.*:ALL"
        state: present
        login_user: root
        login_password: "{{ mysql_root_password }}"

    # Virtual Host
    - name: Configura Virtual Host
      template:
        src: templates/apache-vhost.conf.j2
        dest: /etc/apache2/sites-available/myapp.conf
      notify: Reload Apache

    - name: Abilita sito
      command: a2ensite myapp.conf
      args:
        creates: /etc/apache2/sites-enabled/myapp.conf
      notify: Reload Apache

    - name: Crea document root
      file:
        path: "{{ document_root }}"
        state: directory
        owner: www-data
        group: www-data
        mode: '0755'

  handlers:
    - name: Restart Apache
      service:
        name: apache2
        state: restarted

    - name: Reload Apache
      service:
        name: apache2
        state: reloaded
```

---

## Pattern Comuni: Hardening Playbook

```yaml
# playbooks/hardening.yml — Linux server hardening
---
- name: Hardening Linux Server
  hosts: all
  become: true

  vars:
    ssh_port: 22
    allowed_ssh_users: [deploy, admin]
    sysctl_params:
      net.ipv4.ip_forward: 0
      net.ipv4.conf.all.send_redirects: 0
      net.ipv4.conf.default.accept_source_route: 0
      net.ipv4.conf.all.accept_redirects: 0
      net.ipv4.conf.all.log_martians: 1
      net.ipv4.icmp_echo_ignore_broadcasts: 1
      net.ipv4.tcp_syncookies: 1
      kernel.randomize_va_space: 2

  tasks:
    # SSH Hardening
    - name: Configura SSH
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: "{{ item.regexp }}"
        line: "{{ item.line }}"
        validate: 'sshd -t -f %s'
      loop:
        - { regexp: '^#?PermitRootLogin', line: 'PermitRootLogin no' }
        - { regexp: '^#?PasswordAuthentication', line: 'PasswordAuthentication no' }
        - { regexp: '^#?X11Forwarding', line: 'X11Forwarding no' }
        - { regexp: '^#?MaxAuthTries', line: 'MaxAuthTries 3' }
        - { regexp: '^#?ClientAliveInterval', line: 'ClientAliveInterval 300' }
        - { regexp: '^#?ClientAliveCountMax', line: 'ClientAliveCountMax 2' }
        - { regexp: '^#?Port ', line: "Port {{ ssh_port }}" }
      notify: Restart SSHD

    - name: Limita utenti SSH
      lineinfile:
        path: /etc/ssh/sshd_config
        line: "AllowUsers {{ allowed_ssh_users | join(' ') }}"
        validate: 'sshd -t -f %s'
      notify: Restart SSHD

    # Kernel hardening
    - name: Applica parametri sysctl
      sysctl:
        name: "{{ item.key }}"
        value: "{{ item.value }}"
        sysctl_set: true
        state: present
        reload: true
      loop: "{{ sysctl_params | dict2items }}"

    # Firewall
    - name: Installa UFW
      apt:
        name: ufw
        state: present

    - name: Configura UFW default
      ufw:
        state: enabled
        direction: "{{ item.direction }}"
        policy: "{{ item.policy }}"
      loop:
        - { direction: incoming, policy: deny }
        - { direction: outgoing, policy: allow }

    - name: Consenti SSH
      ufw:
        rule: allow
        port: "{{ ssh_port }}"
        proto: tcp

    # Aggiornamenti automatici
    - name: Installa unattended-upgrades
      apt:
        name: unattended-upgrades
        state: present

    - name: Configura aggiornamenti di sicurezza automatici
      copy:
        content: |
          APT::Periodic::Update-Package-Lists "1";
          APT::Periodic::Unattended-Upgrade "1";
          APT::Periodic::AutocleanInterval "7";
        dest: /etc/apt/apt.conf.d/20auto-upgrades

    # Audit
    - name: Installa auditd
      apt:
        name:
          - auditd
          - audispd-plugins
        state: present

    - name: Avvia auditd
      service:
        name: auditd
        state: started
        enabled: true

    # Disabilita servizi non necessari
    - name: Disabilita servizi
      service:
        name: "{{ item }}"
        state: stopped
        enabled: false
      loop:
        - avahi-daemon
        - cups
      ignore_errors: true

  handlers:
    - name: Restart SSHD
      service:
        name: sshd
        state: restarted
```

---

## Execution Environments (EE)

Gli **Execution Environments** (EE) rappresentano l'evoluzione architetturale di Ansible per risolvere il problema storico delle dipendenze. Un EE è un'immagine container (OCI-compliant) che incapsula tutto il necessario per eseguire playbook:

- **ansible-core** (versione specifica)
- **Collezioni Ansible** richieste dal progetto
- **Dipendenze Python** (boto3, pywinrm, netmiko, ecc.)
- **Librerie di sistema** (libxml2, sshpass, krb5, ecc.)

### Perché usare gli EE

Senza EE, ogni control node deve avere installate tutte le dipendenze globalmente, creando conflitti tra progetti con requisiti diversi. Gli EE eliminano il classico problema "funziona sulla mia macchina" garantendo:

- **Riproducibilità**: lo stesso ambiente su laptop, CI/CD e AAP/AWX
- **Isolamento**: progetti diversi con dipendenze incompatibili coesistono
- **Portabilità**: nessuna configurazione manuale del control node
- **Versionamento**: l'EE è versionato come qualsiasi artefatto software

### ansible-builder

`ansible-builder` è lo strumento ufficiale per costruire immagini EE. Si installa via pip:

```bash
pip install ansible-builder
```

La configurazione avviene tramite il file `execution-environment.yml`:

```yaml
---
version: 3

images:
  base_image:
    name: 'quay.io/ansible/ansible-runner:latest'

dependencies:
  galaxy: requirements.yml
  python: requirements.txt
  system: bindep.txt

additional_build_files:
  - src: files/ansible.cfg
    dest: configs

additional_build_steps:
  prepend_galaxy:
    - ENV ANSIBLE_GALAXY_SERVER_AUTOMATION_HUB_URL=https://console.redhat.com/api/automation-hub/
  prepend_final:
    - COPY _build/configs/ansible.cfg /etc/ansible/ansible.cfg
  append_final:
    - RUN echo "EE custom build completato"
```

Il file `requirements.yml` elenca le collezioni:

```yaml
---
collections:
  - name: cisco.ios
    version: '>=6.0.0'
  - name: amazon.aws
    version: '>=7.0.0'
  - name: ansible.windows
    version: '>=2.0.0'
  - name: community.general
    version: '>=8.0.0'
```

Il file `requirements.txt` elenca le dipendenze Python aggiuntive:

```text
boto3>=1.28.0
botocore>=1.31.0
pywinrm>=0.4.3
jmespath>=1.0.1
netaddr>=0.9.0
```

Il file `bindep.txt` specifica pacchetti di sistema:

```text
gcc [compile]
python3-devel [compile]
libxml2-devel [platform:centos-8 platform:rhel-8]
krb5-devel [platform:centos-8 platform:rhel-8]
```

Per costruire l'immagine:

```bash
# Build con tag specifico
ansible-builder build --tag myorg/ee-network:2.1.0 --container-runtime podman

# Build con context directory personalizzata
ansible-builder build --tag myorg/ee-cloud:1.0.0 --build-arg EE_BASE_IMAGE=quay.io/ansible/ansible-runner:2.3

# Ispezionare il Containerfile generato senza costruire
ansible-builder create --output-filename Containerfile
```

### EE e AWX/AAP

In AWX e Ansible Automation Platform, gli EE vengono registrati come risorse:

1. Costruire e pushare l'EE nel registry (quay.io, Docker Hub, registry interno)
2. In AWX: **Administration → Execution Environments → Add**
3. Specificare URL dell'immagine e credenziali del registry
4. Associare l'EE a un Job Template o Organization

Ogni Job Template può utilizzare un EE diverso, permettendo team differenti di lavorare con stack tecnologici incompatibili sullo stesso cluster AWX.

### Best Practice per gli EE

- **Versionare** sempre le immagini EE con tag semantici (mai solo `:latest`)
- **Minimizzare** le dipendenze: un EE per dominio (rete, cloud, Windows) anziché uno monolitico
- **Automatizzare** la build degli EE nella CI/CD pipeline
- **Scansionare** le immagini per vulnerabilità con Trivy, Grype o strumenti equivalenti
- **Testare** gli EE con molecule prima di promuoverli in produzione
- **Documentare** quali collezioni e versioni sono incluse in ciascun EE

---

## ansible-navigator

`ansible-navigator` è il successore moderno di `ansible-playbook`, progettato per lavorare nativamente con gli Execution Environments. Fornisce un'interfaccia text-based interattiva (TUI) oltre alla modalità tradizionale stdout.

### Installazione

```bash
pip install ansible-navigator

# Oppure tramite il pacchetto RPM su RHEL/Fedora
dnf install ansible-navigator
```

### Modalità di esecuzione

ansible-navigator supporta due modalità:

**Modalità stdout** (comportamento classico, compatibile con script e CI/CD):

```bash
ansible-navigator run site.yml -m stdout --eei myorg/ee-cloud:2.1.0
```

**Modalità interactive** (TUI con navigazione, ispezione e drill-down):

```bash
ansible-navigator run site.yml --eei myorg/ee-cloud:2.1.0
```

Nella modalità interattiva è possibile:

- Navigare i risultati play-by-play e task-by-task
- Ispezionare stdout/stderr di ogni singolo task
- Visualizzare la documentazione dei moduli inline (`:doc <modulo>`)
- Esplorare l'inventario e le variabili host (`:inventory`)
- Verificare le collezioni disponibili (`:collections`)
- Controllare la configurazione corrente (`:config`)

### Sotto-comandi principali

| Comando | Descrizione |
|---------|-------------|
| `run` | Esegue playbook (equivalente di `ansible-playbook`) |
| `inventory` | Esplora inventario (equivalente di `ansible-inventory`) |
| `config` | Mostra configurazione attiva |
| `doc` | Mostra documentazione moduli |
| `collections` | Elenca collezioni disponibili nell'EE |
| `images` | Ispeziona contenuto delle immagini EE |
| `replay` | Riproduce un artifact salvato |
| `lint` | Esegue ansible-lint sul playbook |

### Configurazione con ansible-navigator.yml

Il file di configurazione `ansible-navigator.yml` (nella root del progetto o in `~/.ansible-navigator.yml`) centralizza tutte le impostazioni:

```yaml
---
ansible-navigator:
  execution-environment:
    container-engine: podman
    enabled: true
    image: myorg/ee-production:2.1.0
    pull:
      policy: missing
    volume-mounts:
      - src: /home/user/.ssh
        dest: /home/runner/.ssh
        options: "ro"
    environment-variables:
      set:
        ANSIBLE_CALLBACKS_ENABLED: "ansible.posix.profile_tasks"
      pass:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY

  mode: stdout

  playbook-artifact:
    enable: true
    save-as: artifacts/{playbook_name}-{ts_utc}.json

  logging:
    level: warning
    append: false
    file: /tmp/ansible-navigator.log

  ansible:
    config:
      path: ./ansible.cfg
    cmdline: "--forks 20 --timeout 60"
    inventories:
      - ./inventory/production/
```

### Artifact e replay

ansible-navigator salva automaticamente gli artifact di ogni esecuzione in formato JSON. Questi artifact contengono l'output completo di ogni task, le variabili utilizzate e i risultati. È possibile riesaminare un'esecuzione passata:

```bash
# Riprodurre un artifact in modalità interattiva
ansible-navigator replay artifacts/site-2025-01-15T14:30:00.json

# Riprodurre in stdout per l'integrazione CI/CD
ansible-navigator replay artifacts/site-2025-01-15T14:30:00.json -m stdout
```

### Migrazione da ansible-playbook

La migrazione è diretta. La maggior parte dei flag CLI sono equivalenti:

| ansible-playbook | ansible-navigator |
|-----------------|-------------------|
| `ansible-playbook site.yml -i inv` | `ansible-navigator run site.yml -i inv` |
| `ansible-playbook --check --diff` | `ansible-navigator run --check --diff` |
| `ansible-playbook --limit webservers` | `ansible-navigator run --limit webservers` |
| `ansible-playbook --tags deploy` | `ansible-navigator run --tags deploy` |
| `ansible-playbook -e @vars.yml` | `ansible-navigator run -e @vars.yml` |

---

## ansible-lint: Regole e Profili Avanzati

`ansible-lint` è lo strumento di analisi statica per il codice Ansible. Oltre alle regole di base, supporta un sistema di profili progressivi e regole personalizzate.

### Profili di severità

ansible-lint organizza le regole in profili cumulativi, dal meno al più restrittivo:

| Profilo | Regole | Uso consigliato |
|---------|--------|-----------------|
| `min` | Solo errori di sintassi | Progetti legacy in fase di migrazione |
| `basic` | min + deprecazioni e naming | Progetti in fase di adozione |
| `moderate` | basic + best practice comuni | Sviluppo attivo |
| `safety` | moderate + sicurezza | Progetti con requisiti di compliance |
| `shared` | safety + regole per codice condiviso | Roles e collezioni pubbliche |
| `production` | Tutte le regole attive | Produzione con CI/CD enforcement |

Configurare il profilo nel file `.ansible-lint`:

```yaml
---
profile: production

exclude_paths:
  - .cache/
  - .github/
  - molecule/
  - tests/output/

skip_list:
  - experimental    # Ignora regole sperimentali
  - meta-no-tags    # Permetti roles senza tag

warn_list:
  - no-changed-when   # Avvisa ma non fallisce
  - command-instead-of-module

enable_list:
  - fqcn             # Forza nomi fully-qualified per tutti i moduli
  - no-free-form     # Vieta sintassi free-form nei task

use_default_rules: true

kinds:
  - playbook: "**/playbooks/*.yml"
  - tasks: "**/tasks/*.yml"
  - vars: "**/vars/*.yml"
  - meta: "**/meta/main.yml"
  - handlers: "**/handlers/*.yml"
```

### Regole chiave per la produzione

**FQCN (Fully Qualified Collection Name)**: a partire da Ansible 2.10+, tutti i moduli dovrebbero usare il nome completo:

```yaml
# ERRATO — ambiguo, potrebbe risolvere a moduli diversi
- name: Installa pacchetto
  yum:
    name: httpd

# CORRETTO — esplicito e deterministico
- name: Installa pacchetto
  ansible.builtin.yum:
    name: httpd
```

**no-changed-when**: ogni task con `command`, `shell` o `raw` deve specificare `changed_when`:

```yaml
- name: Verifica stato servizio
  ansible.builtin.command: systemctl is-active nginx
  register: nginx_status
  changed_when: false
  failed_when: nginx_status.rc not in [0, 3]
```

**risky-file-permissions**: tutti i file creati devono avere permessi espliciti:

```yaml
- name: Crea file di configurazione
  ansible.builtin.template:
    src: app.conf.j2
    dest: /etc/app/app.conf
    owner: app
    group: app
    mode: '0640'     # Obbligatorio, non lasciare al default
```

### Regole personalizzate

È possibile creare regole custom in Python. Creare una directory `rules/` e aggiungere un file Python:

```python
# rules/check_become_user.py
"""Regola custom: verifica che become_user sia specificato quando become=true."""
from ansiblelint.rules import AnsibleLintRule

class CheckBecomeUser(AnsibleLintRule):
    id = "custom-become-user"
    shortdesc = "become richiede become_user esplicito"
    description = (
        "Quando si usa become: true, specificare sempre "
        "become_user per evitare ambiguità."
    )
    severity = "MEDIUM"
    tags = ["security", "custom"]

    def matchtask(self, task, file=None):
        if task.get("become", False) and "become_user" not in task:
            return self.shortdesc
        return False
```

Registrare la directory nel file `.ansible-lint`:

```yaml
rulesdir:
  - ./rules/
```

### Integrazione con pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/ansible/ansible-lint
    rev: v24.10.0
    hooks:
      - id: ansible-lint
        args: [--profile, production]
        additional_dependencies:
          - ansible-core>=2.16
```

---

## Callback Plugin

I **callback plugin** sono il meccanismo di Ansible per personalizzare l'output e reagire agli eventi durante l'esecuzione. Esistono due categorie principali:

### Tipi di callback

**stdout callbacks** — controllano il formato dell'output principale (uno solo attivo alla volta):

| Plugin | Descrizione |
|--------|-------------|
| `default` | Output standard di Ansible |
| `yaml` | Output formattato in YAML leggibile |
| `json` | Output in JSON strutturato |
| `minimal` | Solo errori e changed |
| `dense` | Una riga per task |
| `debug` | Output dettagliato per troubleshooting |

**notification/aggregate callbacks** — possono essere attivi contemporaneamente:

| Plugin | Descrizione |
|--------|-------------|
| `profile_tasks` | Tempo di esecuzione per ogni task |
| `profile_roles` | Tempo di esecuzione aggregato per role |
| `timer` | Tempo totale dell'esecuzione |
| `junit` | Genera report JUnit XML per CI/CD |
| `log_plays` | Registra le esecuzioni su file |
| `mail` | Invia email sui risultati |
| `slack` | Notifiche su Slack |

### Abilitare i callback

In `ansible.cfg`:

```ini
[defaults]
stdout_callback = yaml
callbacks_enabled = ansible.posix.profile_tasks, ansible.posix.timer, community.general.log_plays

[callback_log_plays]
log_folder = /var/log/ansible/plays/
```

### Esempio: profile_tasks per ottimizzazione

Il callback `profile_tasks` aggiunge il tempo di esecuzione accanto a ogni task, rendendo immediato identificare i colli di bottiglia:

```
TASK [Installa dipendenze Python] ****************************
ok: [web01] => {"changed": false}
Tuesday 15 January 2025  14:30:15 +0100 (0:01:23.456) 0:03:45.678 ****

TASK [Compila assets frontend] *******************************
changed: [web01] => {"changed": true}
Tuesday 15 January 2025  14:31:38 +0100 (0:00:42.123) 0:04:27.801 ****
```

### Callback JUnit per CI/CD

Il callback JUnit genera un file XML compatibile con Jenkins, GitLab CI, GitHub Actions e altri sistemi CI:

```ini
[defaults]
callbacks_enabled = junit

[callback_junit]
output_dir = ./test-results/
fail_on_change = true
include_setup_tasks_in_report = true
test_case_prefix = ansible_
```

### Sviluppo di un callback custom

Un callback personalizzato è una classe Python che eredita da `CallbackBase`:

```python
# callback_plugins/notify_deploy.py
"""Callback plugin per notificare i deploy via webhook."""
from datetime import datetime, timezone
from ansible.plugins.callback import CallbackBase

DOCUMENTATION = """
  name: notify_deploy
  type: notification
  short_description: Notifica deploy via webhook
  description:
    - Invia una notifica HTTP quando un playbook termina
  requirements:
    - requests
"""

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'notify_deploy'
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self):
        super().__init__()
        self._start_time = None
        self._task_results = {"ok": 0, "failed": 0, "changed": 0, "skipped": 0}

    def v2_playbook_on_start(self, playbook):
        self._start_time = datetime.now(timezone.utc)
        self._playbook_name = playbook._file_name

    def v2_runner_on_ok(self, result):
        if result.is_changed():
            self._task_results["changed"] += 1
        else:
            self._task_results["ok"] += 1

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if not ignore_errors:
            self._task_results["failed"] += 1

    def v2_runner_on_skipped(self, result):
        self._task_results["skipped"] += 1

    def v2_playbook_on_stats(self, stats):
        import requests
        duration = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        payload = {
            "playbook": self._playbook_name,
            "duration_seconds": duration,
            "results": self._task_results,
            "timestamp": self._start_time.isoformat(),
            "status": "failed" if self._task_results["failed"] > 0 else "success"
        }
        webhook_url = self._plugin_options.get("webhook_url", "")
        if webhook_url:
            requests.post(webhook_url, json=payload, timeout=10)
```

---

## Sviluppo di Moduli Custom

Quando i moduli esistenti non coprono un'esigenza specifica, Ansible permette di sviluppare moduli custom in Python. Un modulo custom segue una struttura precisa e interagisce con Ansible tramite la classe `AnsibleModule`.

### Struttura di un modulo

Un modulo Ansible è un file Python autonomo che:

1. Definisce `DOCUMENTATION`, `EXAMPLES` e `RETURN` come stringhe YAML
2. Usa `AnsibleModule` per gestire parametri, validazione e output
3. Implementa la logica in una funzione `main()`
4. Gestisce il check mode per permettere dry-run

### Esempio completo: modulo per gestire un'applicazione custom

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Modulo Ansible per gestire il servizio MyApp."""

DOCUMENTATION = r"""
---
module: myapp_service
short_description: Gestisce il ciclo di vita del servizio MyApp
version_added: "1.0.0"
description:
  - Avvia, ferma o riavvia il servizio MyApp
  - Verifica lo stato di salute tramite health check endpoint
  - Supporta check mode per operazioni dry-run
options:
  name:
    description: Nome dell'istanza del servizio
    required: true
    type: str
  state:
    description: Stato desiderato del servizio
    required: true
    type: str
    choices: ['started', 'stopped', 'restarted', 'healthy']
  port:
    description: Porta del servizio
    required: false
    type: int
    default: 8080
  health_endpoint:
    description: Percorso dell'endpoint di health check
    required: false
    type: str
    default: '/health'
  timeout:
    description: Timeout in secondi per l'health check
    required: false
    type: int
    default: 30
author:
  - "Operatore Ansible"
"""

EXAMPLES = r"""
- name: Avvia il servizio MyApp
  myapp_service:
    name: production
    state: started
    port: 8080

- name: Verifica che il servizio sia healthy
  myapp_service:
    name: production
    state: healthy
    health_endpoint: /api/health
    timeout: 60

- name: Riavvia il servizio
  myapp_service:
    name: staging
    state: restarted
"""

RETURN = r"""
status:
  description: Stato corrente del servizio
  type: str
  returned: always
  sample: running
pid:
  description: PID del processo
  type: int
  returned: when running
  sample: 12345
health:
  description: Risultato dell'health check
  type: dict
  returned: when state=healthy
  sample: {"status": "ok", "uptime": 3600}
"""

import time
from ansible.module_utils.basic import AnsibleModule

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def check_service_running(module, name):
    """Verifica se il servizio è in esecuzione."""
    rc, stdout, stderr = module.run_command(
        ["systemctl", "is-active", f"myapp-{name}"]
    )
    return rc == 0, stdout.strip()


def get_service_pid(module, name):
    """Ottiene il PID del servizio."""
    rc, stdout, stderr = module.run_command(
        ["systemctl", "show", f"myapp-{name}", "--property=MainPID", "--value"]
    )
    if rc == 0 and stdout.strip().isdigit():
        return int(stdout.strip())
    return None


def health_check(port, endpoint, timeout):
    """Esegue un health check HTTP."""
    url = f"http://localhost:{port}{endpoint}"
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return True, resp.json()
        except Exception as e:
            last_error = str(e)
        time.sleep(2)
    return False, {"error": last_error or "timeout"}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(
                type='str', required=True,
                choices=['started', 'stopped', 'restarted', 'healthy']
            ),
            port=dict(type='int', default=8080),
            health_endpoint=dict(type='str', default='/health'),
            timeout=dict(type='int', default=30),
        ),
        supports_check_mode=True,
    )

    if module.params['state'] == 'healthy' and not HAS_REQUESTS:
        module.fail_json(msg="Il modulo Python 'requests' è necessario per state=healthy")

    name = module.params['name']
    state = module.params['state']
    result = dict(changed=False, status='unknown')

    is_running, current_status = check_service_running(module, name)

    if state == 'started':
        if not is_running:
            if module.check_mode:
                result['changed'] = True
            else:
                rc, stdout, stderr = module.run_command(
                    ["systemctl", "start", f"myapp-{name}"]
                )
                if rc != 0:
                    module.fail_json(msg=f"Impossibile avviare il servizio: {stderr}")
                result['changed'] = True
        result['status'] = 'running'
        result['pid'] = get_service_pid(module, name)

    elif state == 'stopped':
        if is_running:
            if module.check_mode:
                result['changed'] = True
            else:
                rc, stdout, stderr = module.run_command(
                    ["systemctl", "stop", f"myapp-{name}"]
                )
                if rc != 0:
                    module.fail_json(msg=f"Impossibile fermare il servizio: {stderr}")
                result['changed'] = True
        result['status'] = 'stopped'

    elif state == 'restarted':
        if module.check_mode:
            result['changed'] = True
        else:
            rc, stdout, stderr = module.run_command(
                ["systemctl", "restart", f"myapp-{name}"]
            )
            if rc != 0:
                module.fail_json(msg=f"Impossibile riavviare il servizio: {stderr}")
            result['changed'] = True
        result['status'] = 'running'

    elif state == 'healthy':
        if not is_running:
            module.fail_json(msg=f"Il servizio myapp-{name} non è in esecuzione")
        healthy, health_data = health_check(
            module.params['port'],
            module.params['health_endpoint'],
            module.params['timeout']
        )
        if not healthy:
            module.fail_json(msg="Health check fallito", health=health_data)
        result['status'] = 'healthy'
        result['health'] = health_data

    module.exit_json(**result)


if __name__ == '__main__':
    main()
```

### Posizionamento dei moduli custom

I moduli custom possono risiedere in diverse posizioni:

```text
# Nel progetto corrente
./library/myapp_service.py

# In un role
roles/myapp/library/myapp_service.py

# In una collezione
collections/ansible_collections/myorg/myapp/plugins/modules/myapp_service.py

# Globalmente (sconsigliato per progetti condivisi)
~/.ansible/plugins/modules/myapp_service.py
```

### Test dei moduli custom

Testare un modulo custom con Molecule e un playbook di verifica:

```yaml
# molecule/default/verify.yml
- name: Verifica modulo myapp_service
  hosts: all
  tasks:
    - name: Test check mode
      myapp_service:
        name: test
        state: started
      check_mode: true
      register: check_result

    - name: Verifica che check mode non modifichi nulla
      ansible.builtin.assert:
        that:
          - check_result is changed or check_result is not changed
          - check_result.status is defined

    - name: Avvia servizio
      myapp_service:
        name: test
        state: started
      register: start_result

    - name: Verifica avvio
      ansible.builtin.assert:
        that:
          - start_result.status == 'running'
```

### Module utilities condivise

Per condividere codice tra moduli, usare `module_utils`:

```python
# plugins/module_utils/myapp_common.py
"""Utility condivise per i moduli MyApp."""

def parse_config(config_path):
    """Analizza il file di configurazione MyApp."""
    import json
    with open(config_path, 'r') as f:
        return json.load(f)

def validate_port(port):
    """Valida che la porta sia nell'intervallo consentito."""
    if not 1024 <= port <= 65535:
        raise ValueError(f"Porta {port} non valida (range: 1024-65535)")
    return True
```

Importare nel modulo:

```python
from ansible.module_utils.myapp_common import parse_config, validate_port
```

---

## Automazione di Rete (Cisco, Juniper, Arista)

Ansible supporta l'automazione di apparati di rete grazie a collezioni dedicate e connection plugin specializzati. A differenza dell'automazione server tradizionale (SSH + Python), i dispositivi di rete richiedono approcci specifici.

### Collezioni per il networking

| Vendor | Collezione | Moduli principali |
|--------|-----------|-------------------|
| Cisco IOS/IOS-XE | `cisco.ios` | `ios_config`, `ios_command`, `ios_interfaces`, `ios_vlans` |
| Cisco NX-OS | `cisco.nxos` | `nxos_config`, `nxos_bgp_global`, `nxos_vlans` |
| Juniper Junos | `junipernetworks.junos` | `junos_config`, `junos_command`, `junos_interfaces` |
| Arista EOS | `arista.eos` | `eos_config`, `eos_command`, `eos_interfaces`, `eos_bgp_global` |
| Multi-vendor | `ansible.netcommon` | `cli_command`, `cli_config`, `netconf_config` |

Installazione:

```bash
ansible-galaxy collection install cisco.ios cisco.nxos junipernetworks.junos arista.eos ansible.netcommon
```

### Connection plugin per dispositivi di rete

| Plugin | Protocollo | Uso |
|--------|-----------|-----|
| `ansible.netcommon.network_cli` | SSH (CLI) | Cisco IOS, NX-OS, Arista EOS |
| `ansible.netcommon.netconf` | NETCONF (XML/SSH) | Juniper Junos, IOS-XE |
| `ansible.netcommon.httpapi` | REST API | Arista eAPI, NX-OS NX-API |

Configurazione nell'inventario:

```yaml
# inventory/network.yml
---
all:
  children:
    cisco_switches:
      hosts:
        sw-core-01:
          ansible_host: 10.0.1.1
        sw-access-01:
          ansible_host: 10.0.1.2
      vars:
        ansible_network_os: cisco.ios.ios
        ansible_connection: ansible.netcommon.network_cli
        ansible_user: "{{ vault_network_user }}"
        ansible_password: "{{ vault_network_password }}"
        ansible_become: true
        ansible_become_method: enable
        ansible_become_password: "{{ vault_enable_password }}"

    juniper_routers:
      hosts:
        rt-border-01:
          ansible_host: 10.0.2.1
      vars:
        ansible_network_os: junipernetworks.junos.junos
        ansible_connection: ansible.netcommon.netconf
        ansible_user: "{{ vault_junos_user }}"
        ansible_password: "{{ vault_junos_password }}"

    arista_switches:
      hosts:
        sw-leaf-01:
          ansible_host: 10.0.3.1
      vars:
        ansible_network_os: arista.eos.eos
        ansible_connection: ansible.netcommon.httpapi
        ansible_httpapi_use_ssl: true
        ansible_httpapi_validate_certs: false
        ansible_user: "{{ vault_arista_user }}"
        ansible_password: "{{ vault_arista_password }}"
```

### Resource Modules (approccio dichiarativo)

I resource modules sono il modo moderno di gestire la configurazione di rete. Invece di inviare comandi CLI grezzi, si dichiara lo stato desiderato:

```yaml
- name: Configura VLAN su switch Cisco
  cisco.ios.ios_vlans:
    config:
      - vlan_id: 100
        name: MANAGEMENT
        state: active
        shutdown: disabled
      - vlan_id: 200
        name: SERVERS
        state: active
      - vlan_id: 300
        name: DMZ
        state: active
    state: merged    # merged | replaced | overridden | deleted

- name: Configura interfacce L3
  cisco.ios.ios_l3_interfaces:
    config:
      - name: Vlan100
        ipv4:
          - address: 10.100.0.1/24
      - name: Vlan200
        ipv4:
          - address: 10.200.0.1/24
    state: merged
```

Gli stati disponibili per i resource modules:

| Stato | Comportamento |
|-------|--------------|
| `merged` | Aggiunge/aggiorna la configurazione specificata (default) |
| `replaced` | Sostituisce la configurazione della singola risorsa |
| `overridden` | Sostituisce TUTTA la configurazione della classe di risorse |
| `deleted` | Rimuove la configurazione specificata |
| `gathered` | Raccoglie la configurazione attuale senza modifiche |
| `rendered` | Genera i comandi senza applicarli |
| `parsed` | Analizza una configurazione testuale offline |

### Automazione multi-vendor con moduli platform-independent

I moduli `cli_command` e `cli_config` di `ansible.netcommon` funzionano su qualsiasi piattaforma con `network_cli`:

```yaml
- name: Backup configurazione multi-vendor
  hosts: all_network_devices
  gather_facts: false
  tasks:
    - name: Raccogli configurazione running
      ansible.netcommon.cli_command:
        command: "{{ show_run_command }}"
      register: running_config

    - name: Salva backup locale
      ansible.builtin.copy:
        content: "{{ running_config.stdout }}"
        dest: "backups/{{ inventory_hostname }}_{{ ansible_date_time.date }}.cfg"
      delegate_to: localhost
```

Con variabili per vendor nel group_vars:

```yaml
# group_vars/cisco_switches.yml
show_run_command: "show running-config"

# group_vars/juniper_routers.yml
show_run_command: "show configuration | display set"

# group_vars/arista_switches.yml
show_run_command: "show running-config"
```

### Configurazione BGP multi-vendor

```yaml
- name: Configura BGP su Cisco IOS
  cisco.ios.ios_bgp_global:
    config:
      as_number: '65001'
      router_id: 10.0.0.1
      neighbors:
        - neighbor_address: 10.0.0.2
          remote_as: '65002'
          description: "Peer verso ISP"
          timers:
            keepalive: 30
            holdtime: 90
    state: merged

- name: Configura BGP su Juniper
  junipernetworks.junos.junos_bgp_global:
    config:
      as_number: '65001'
      router_id: 10.0.0.1
    state: merged
```

### Validazione configurazione di rete

```yaml
- name: Valida configurazione prima del deploy
  hosts: cisco_switches
  gather_facts: false
  tasks:
    - name: Verifica raggiungibilità gateway
      ansible.netcommon.cli_command:
        command: "ping {{ gateway_ip }} repeat 3"
      register: ping_result
      failed_when: "'Success rate is 0' in ping_result.stdout"

    - name: Verifica stato interfacce critiche
      cisco.ios.ios_command:
        commands:
          - show interface status | include connected
      register: intf_status

    - name: Controlla che le interfacce uplink siano up
      ansible.builtin.assert:
        that:
          - "'connected' in intf_status.stdout[0]"
        fail_msg: "Interfacce uplink non operative"
```

---

## Automazione Windows con Ansible

Ansible supporta pienamente l'automazione di host Windows tramite il protocollo **WinRM** (Windows Remote Management) e moduli dedicati della collezione `ansible.windows`.

### Prerequisiti

**Sul control node (Linux)**:

```bash
pip install pywinrm>=0.4.3
# Per autenticazione Kerberos (Active Directory):
pip install pywinrm[kerberos]
# Pacchetti di sistema per Kerberos:
dnf install krb5-devel krb5-workstation   # RHEL/Fedora
apt install libkrb5-dev krb5-user          # Debian/Ubuntu
```

**Sull'host Windows** — abilitare WinRM con lo script ufficiale Ansible:

```powershell
# Eseguire in PowerShell come Amministratore
# Scarica e configura WinRM per Ansible
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$url = "https://raw.githubusercontent.com/ansible/ansible-documentation/devel/examples/scripts/ConfigureRemotingForAnsible.ps1"
$file = "$env:temp\ConfigureRemotingForAnsible.ps1"
Invoke-WebRequest -Uri $url -OutFile $file
powershell.exe -ExecutionPolicy ByPass -File $file -EnableCredSSP -DisableBasicAuth -ForceNewSSLCert
```

### Inventario per host Windows

```yaml
# inventory/windows.yml
---
all:
  children:
    windows_servers:
      hosts:
        win-web-01:
          ansible_host: 192.168.1.100
        win-db-01:
          ansible_host: 192.168.1.101
      vars:
        ansible_connection: winrm
        ansible_port: 5986
        ansible_winrm_transport: ntlm           # ntlm | kerberos | credssp
        ansible_winrm_server_cert_validation: ignore  # Solo per lab/test
        ansible_user: "{{ vault_win_user }}"
        ansible_password: "{{ vault_win_password }}"

    windows_domain_controllers:
      hosts:
        win-dc-01:
          ansible_host: 192.168.1.10
      vars:
        ansible_connection: winrm
        ansible_port: 5986
        ansible_winrm_transport: kerberos
        ansible_user: admin@DOMINIO.LOCAL
        ansible_password: "{{ vault_dc_password }}"
```

### Collezioni Windows

| Collezione | Contenuto |
|------------|-----------|
| `ansible.windows` | Moduli core: `win_copy`, `win_file`, `win_service`, `win_user`, `win_regedit`, `win_dsc`, `win_package` |
| `community.windows` | Moduli community: `win_firewall_rule`, `win_iis_website`, `win_domain_controller`, `win_domain_membership` |
| `microsoft.ad` | Active Directory: `user`, `group`, `computer`, `ou`, `gpo` |
| `chocolatey.chocolatey` | Gestione pacchetti Chocolatey: `win_chocolatey`, `win_chocolatey_source` |

### Playbook di esempio: provisioning server Windows

```yaml
---
- name: Provisioning server Windows
  hosts: windows_servers
  gather_facts: true

  vars:
    required_features:
      - Web-Server
      - Web-Asp-Net45
      - NET-Framework-45-Core
    firewall_rules:
      - name: HTTP
        localport: 80
        protocol: tcp
        action: allow
      - name: HTTPS
        localport: 443
        protocol: tcp
        action: allow

  tasks:
    - name: Installa feature Windows
      ansible.windows.win_feature:
        name: "{{ required_features }}"
        state: present
        include_management_tools: true
      register: feature_install

    - name: Riavvia se necessario dopo installazione feature
      ansible.windows.win_reboot:
        reboot_timeout: 600
        msg: "Riavvio post-installazione feature"
      when: feature_install.reboot_required

    - name: Installa pacchetti via Chocolatey
      chocolatey.chocolatey.win_chocolatey:
        name: "{{ item }}"
        state: present
      loop:
        - git
        - notepadplusplus
        - 7zip
        - dotnet-runtime

    - name: Configura regole firewall
      community.windows.win_firewall_rule:
        name: "Allow {{ item.name }}"
        localport: "{{ item.localport }}"
        protocol: "{{ item.protocol }}"
        action: "{{ item.action }}"
        direction: in
        state: present
        enabled: true
      loop: "{{ firewall_rules }}"

    - name: Crea directory applicazione
      ansible.windows.win_file:
        path: C:\Apps\MyWebApp
        state: directory

    - name: Deploy configurazione applicazione
      ansible.windows.win_template:
        src: templates/web.config.j2
        dest: C:\Apps\MyWebApp\web.config

    - name: Configura servizio Windows
      ansible.windows.win_service:
        name: MyWebAppService
        path: C:\Apps\MyWebApp\app.exe
        state: started
        start_mode: auto
        description: "Servizio web applicazione principale"

    - name: Imposta chiavi di registro
      ansible.windows.win_regedit:
        path: HKLM:\SOFTWARE\MyWebApp
        name: Environment
        data: production
        type: string

    - name: Verifica connettività servizio
      ansible.windows.win_uri:
        url: http://localhost:80/health
        return_content: true
        status_code: 200
      register: health_check
      retries: 5
      delay: 10
      until: health_check.status_code == 200
```

### DSC (Desired State Configuration)

Ansible può sfruttare le risorse DSC di PowerShell per gestire la configurazione:

```yaml
- name: Configura IIS via DSC
  ansible.windows.win_dsc:
    resource_name: xWebsite
    Name: MyWebsite
    PhysicalPath: C:\inetpub\MyWebsite
    State: Started
    BindingInfo:
      - Protocol: https
        Port: 443
        CertificateThumbprint: "{{ cert_thumbprint }}"
```

### Gestione aggiornamenti Windows

```yaml
- name: Gestione Windows Update
  hosts: windows_servers
  tasks:
    - name: Installa aggiornamenti di sicurezza
      ansible.windows.win_updates:
        category_names:
          - SecurityUpdates
          - CriticalUpdates
        state: installed
        reboot: true
        reboot_timeout: 3600
      register: update_result

    - name: Report aggiornamenti installati
      ansible.builtin.debug:
        msg: "Installati {{ update_result.installed_update_count }} aggiornamenti"
      when: update_result.installed_update_count | default(0) > 0
```

---

## Integrazione CI/CD con GitHub Actions

L'integrazione di Ansible nelle pipeline CI/CD automatizza il testing, la validazione e il deployment del codice infrastrutturale. GitHub Actions è una piattaforma ideale per questo scopo.

### Pipeline completa: lint, test, deploy

```yaml
# .github/workflows/ansible-pipeline.yml
---
name: Ansible CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    paths:
      - 'ansible/**'
      - 'roles/**'
      - 'playbooks/**'
      - '.github/workflows/ansible-pipeline.yml'
  pull_request:
    branches: [main]
    paths:
      - 'ansible/**'
      - 'roles/**'
      - 'playbooks/**'

env:
  ANSIBLE_FORCE_COLOR: "true"
  PY_COLORS: "1"

jobs:
  lint:
    name: "Ansible Lint"
    runs-on: ubuntu-latest
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Installa dipendenze
        run: |
          pip install ansible-core ansible-lint yamllint

      - name: YAML Lint
        run: yamllint -c .yamllint.yml .

      - name: Ansible Lint
        run: ansible-lint --profile production --force-color

  molecule:
    name: "Molecule Test - ${{ matrix.role }}"
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      fail-fast: false
      matrix:
        role:
          - roles/common
          - roles/nginx
          - roles/postgresql
          - roles/hardening
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Installa dipendenze
        run: |
          pip install ansible-core molecule molecule-plugins[docker] docker pytest-testinfra

      - name: Esegui Molecule
        run: molecule test
        working-directory: ${{ matrix.role }}
        env:
          MOLECULE_DISTRO: ubuntu2204

  security-scan:
    name: "Security Scan"
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Installa dipendenze
        run: pip install ansible-core ansible-lint

      - name: Verifica assenza credenziali hardcoded
        run: |
          # Cerca pattern sospetti nei playbook
          if grep -rn "password:" playbooks/ roles/ --include="*.yml" | grep -v "vault_" | grep -v "{{ " | grep -v "#"; then
            echo "ERRORE: Possibili credenziali hardcoded trovate"
            exit 1
          fi

      - name: Ansible Lint profilo sicurezza
        run: ansible-lint --profile safety playbooks/ roles/

  deploy-staging:
    name: "Deploy Staging"
    runs-on: ubuntu-latest
    needs: [molecule, security-scan]
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Installa Ansible
        run: |
          pip install ansible-core
          ansible-galaxy collection install -r requirements.yml

      - name: Configura SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_ed25519
          chmod 600 ~/.ssh/id_ed25519
          ssh-keyscan -H ${{ secrets.STAGING_HOST }} >> ~/.ssh/known_hosts

      - name: Deploy su staging
        run: |
          ansible-playbook playbooks/site.yml \
            -i inventory/staging/ \
            --diff \
            --limit staging
        env:
          ANSIBLE_VAULT_PASSWORD: ${{ secrets.VAULT_PASSWORD }}

  deploy-production:
    name: "Deploy Production"
    runs-on: ubuntu-latest
    needs: [molecule, security-scan]
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Installa Ansible
        run: |
          pip install ansible-core
          ansible-galaxy collection install -r requirements.yml

      - name: Configura SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_ed25519
          chmod 600 ~/.ssh/id_ed25519
          ssh-keyscan -H ${{ secrets.PRODUCTION_HOSTS }} >> ~/.ssh/known_hosts

      - name: Deploy produzione (rolling)
        run: |
          ansible-playbook playbooks/site.yml \
            -i inventory/production/ \
            --diff \
            -e "deploy_strategy=rolling" \
            -e "serial_count=2"
        env:
          ANSIBLE_VAULT_PASSWORD: ${{ secrets.VAULT_PASSWORD }}

      - name: Verifica post-deploy
        run: |
          ansible-playbook playbooks/verify.yml \
            -i inventory/production/ \
            --tags smoke-test
        env:
          ANSIBLE_VAULT_PASSWORD: ${{ secrets.VAULT_PASSWORD }}
```

### Gestione dei segreti in GitHub Actions

I segreti Ansible Vault vengono iniettati tramite GitHub Secrets:

```yaml
# Nel playbook, usare un vault password file temporaneo
- name: Deploy con vault
  run: |
    echo "${{ secrets.VAULT_PASSWORD }}" > .vault_pass
    ansible-playbook site.yml --vault-password-file .vault_pass
    rm -f .vault_pass
```

Approccio alternativo con variabile d'ambiente:

```yaml
# ansible.cfg nel repository
[defaults]
vault_password_file = /dev/stdin

# Nel workflow
- name: Deploy
  run: echo "$ANSIBLE_VAULT_PASSWORD" | ansible-playbook site.yml
  env:
    ANSIBLE_VAULT_PASSWORD: ${{ secrets.VAULT_PASSWORD }}
```

### Matrix testing per piattaforme multiple

```yaml
molecule-matrix:
  name: "Test ${{ matrix.role }} on ${{ matrix.distro }}"
  runs-on: ubuntu-latest
  strategy:
    fail-fast: false
    matrix:
      role: [common, nginx, hardening]
      distro: [ubuntu2204, debian12, rocky9, fedora39]
  steps:
    - uses: actions/checkout@v4
    - name: Molecule test
      run: molecule test
      working-directory: roles/${{ matrix.role }}
      env:
        MOLECULE_DISTRO: ${{ matrix.distro }}
```

### Notifica risultati

```yaml
  notify:
    name: "Notifica risultati"
    runs-on: ubuntu-latest
    needs: [deploy-production]
    if: always()
    steps:
      - name: Notifica successo
        if: needs.deploy-production.result == 'success'
        run: |
          curl -X POST "${{ secrets.WEBHOOK_URL }}" \
            -H "Content-Type: application/json" \
            -d '{"text":"Deploy produzione completato con successo","status":"success"}'

      - name: Notifica fallimento
        if: needs.deploy-production.result == 'failure'
        run: |
          curl -X POST "${{ secrets.WEBHOOK_URL }}" \
            -H "Content-Type: application/json" \
            -d '{"text":"ATTENZIONE: Deploy produzione fallito","status":"failure"}'
```

### Workflow di validazione per Pull Request

```yaml
# .github/workflows/ansible-pr-validation.yml
---
name: PR Validation

on:
  pull_request:
    branches: [main, develop]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Installa strumenti
        run: pip install ansible-core ansible-lint yamllint

      - name: Verifica sintassi
        run: ansible-playbook --syntax-check playbooks/*.yml

      - name: Ansible Lint
        run: ansible-lint --profile production

      - name: Verifica inventory
        run: ansible-inventory -i inventory/staging/ --list > /dev/null

      - name: Dry-run playbook (check mode)
        run: |
          ansible-playbook playbooks/site.yml \
            -i inventory/staging/ \
            --check --diff \
            --limit test-host
        env:
          ANSIBLE_VAULT_PASSWORD: ${{ secrets.VAULT_PASSWORD }}
```

---

## Best Practices

1. **Usa roles per tutto ciò che è riutilizzabile**: Ogni componente (nginx, postgresql, docker, ecc.) deve essere un role separato con variabili configurabili.

2. **Segui la struttura directory di Ansible**: Non inventare strutture custom. La struttura standard è documentata e tutti la conoscono.

3. **Testa con `--check` e `--diff`**: Prima di applicare, usa `ansible-playbook --check --diff` per vedere cosa cambierebbe senza modificare nulla.

4. **Abilita pipelining**: In ansible.cfg, `pipelining = True` riduce significativamente il numero di connessioni SSH e migliora le performance.

5. **Usa Vault per TUTTI i segreti**: Password, chiavi API, certificati — tutto deve essere in file vault. Mai in chiaro nel repository.

6. **Versiona tutto in git**: L'intera directory Ansible (playbook, roles, inventory, vault) deve essere in un repository git. Questo è la tua documentazione dell'infrastruttura.

7. **Idempotenza**: Ogni task deve essere idempotente. Usa `creates:`, `removes:`, `when:`, e `changed_when:` per evitare azioni ripetute. Evita `command`/`shell` quando esiste un modulo.

8. **Nomi descrittivi per le task**: Il nome della task deve descrivere cosa fa, non come lo fa: "Assicura che Nginx sia installato" non "Esegui apt install nginx".

9. **Tag per esecuzione selettiva**: Tagga le task per poter eseguire solo le parti necessarie: `--tags deploy` per il solo deployment, `--tags config` per la sola configurazione.

10. **Testa i roles con Molecule**: Molecule permette di testare i roles in container isolati prima di applicarli in produzione.

---

## Troubleshooting

### Problema: SSH connection timeout

**Sintomi**: `UNREACHABLE! => {"msg": "Failed to connect to the host via ssh"}`.

**Causa**: Firewall, SSH non in ascolto, chiave SSH sbagliata, utente sbagliato.

**Soluzione**:
```bash
# Test connessione manuale
ssh -vvv -i ~/.ssh/id_ed25519 deploy@target_host

# Verifica inventory
ansible target_host -m ping -vvvv

# Controlla ansible.cfg per remote_user, private_key_file
```

### Problema: Permission denied su become

**Sintomi**: `"msg": "Missing sudo password"` o `"MODULE FAILURE"`.

**Causa**: L'utente non ha permessi sudo, o sudo richiede password.

**Soluzione**:
```bash
# Usa --ask-become-pass
ansible-playbook site.yml --ask-become-pass

# Oppure configura sudo senza password per l'utente deploy:
# /etc/sudoers.d/deploy:
# deploy ALL=(ALL) NOPASSWD: ALL
```

### Problema: Task non idempotente — sempre "changed"

**Sintomi**: Una task mostra "changed" ad ogni esecuzione anche se lo stato non cambia.

**Causa**: Uso di `command`/`shell` senza `changed_when` o `creates`.

**Soluzione**:
```yaml
# PRIMA (non idempotente)
- name: Configura app
  command: /opt/app/setup.sh

# DOPO (idempotente)
- name: Configura app
  command: /opt/app/setup.sh
  args:
    creates: /opt/app/.configured
  # Il comando non viene eseguito se il file esiste
```

### Problema: Errore nel template Jinja2

**Sintomi**: `AnsibleUndefinedVariable: 'my_var' is undefined` oppure `TemplateSyntaxError`.

**Causa**: Variabile non definita, sintassi Jinja2 errata, parentesi non chiuse.

**Soluzione**:
```yaml
# 1. Usa il filtro default per variabili opzionali:
{{ my_var | default('fallback_value') }}

# 2. Testa il template localmente:
# ansible localhost -m template -a "src=template.j2 dest=/tmp/test.conf"

# 3. Debug variabili disponibili:
- name: Mostra tutte le variabili
  debug:
    var: vars

# 4. Errori di sintassi comuni:
# SBAGLIATO: {% if foo = "bar" %}     (= invece di ==)
# CORRETTO:  {% if foo == "bar" %}
# SBAGLIATO: {{ foo | upper | }}      (pipe finale senza filtro)
# CORRETTO:  {{ foo | upper }}
```

### Problema: Module not found

**Sintomi**: `ERROR! couldn't resolve module/action 'amazon.aws.ec2_instance'`.

**Causa**: Collection non installata o FQCN errato.

**Soluzione**:
```bash
# Verifica collections installate:
ansible-galaxy collection list

# Installa la collection mancante:
ansible-galaxy collection install amazon.aws

# Verifica il nome esatto del modulo:
ansible-doc -l | grep ec2_instance
ansible-doc amazon.aws.ec2_instance

# Se usi requirements.yml, reinstalla:
ansible-galaxy install -r requirements.yml --force
```

### Problema: Confusione sulla precedenza delle variabili

**Sintomi**: Una variabile ha un valore inaspettato. L'override non funziona.

**Causa**: La variabile è sovrascritta da un livello di precedenza più alto.

**Soluzione**:
```bash
# Debug: mostra da dove proviene una variabile
ansible -m debug -a "var=my_var" -i inventory/ target_host

# Cause comuni:
# - role/vars/ sovrascrive group_vars (livello 15 > livello 6-7)
# - extra vars (-e) sovrascrivono TUTTO (livello 22)
# - set_fact sovrascrive role defaults (livello 19 > livello 2)

# Soluzione: usa defaults/ (non vars/) nei roles per valori override-abili
# roles/myapp/defaults/main.yml  ← l'utente può sovrascrivere
# roles/myapp/vars/main.yml      ← costanti interne, difficili da sovrascrivere
```

### Problema: Python interpreter mismatch

**Sintomi**: `MODULE FAILURE: No module named 'apt'` oppure `/usr/bin/python: not found`.

**Causa**: Ansible non trova Python 3 sul managed node, o usa Python 2.

**Soluzione**:
```yaml
# Specifica l'interprete nell'inventory:
all:
  vars:
    ansible_python_interpreter: /usr/bin/python3

# Per host specifici:
# inventory/host_vars/legacy-server.yml
ansible_python_interpreter: /usr/local/bin/python3.11

# Verifica quale Python Ansible sta usando:
ansible target -m debug -a "var=ansible_python_interpreter"
ansible target -m setup -a "filter=ansible_python_version"

# Su sistemi minimal (senza Python):
- name: Bootstrap Python
  raw: apt-get install -y python3 python3-apt
  become: true
```

### Problema: Vault password errata o dimenticata

**Sintomi**: `ERROR! Decryption failed on /path/to/vault.yml`.

**Causa**: Password sbagliata, vault-id mismatch, file corrotto.

**Soluzione**:
```bash
# Verifica quale vault-id è usato nel file:
head -1 group_vars/production/vault.yml
# $ANSIBLE_VAULT;1.2;AES256;prod   ← vault-id è "prod"
# $ANSIBLE_VAULT;1.1;AES256        ← nessun vault-id

# Specifica il vault-id corretto:
ansible-playbook site.yml --vault-id prod@prompt

# Se la password è persa:
# Non c'è recovery. Rigenera i segreti e ricripta con nuova password.
# Questo è un promemoria: CONSERVA le password vault in modo sicuro
# (password manager, HSM, KMS)
```

### Problema: Fact gathering lento o fallisce

**Soluzione**: `gather_facts: false` se non servono. `gather_subset: [min]` per facts minimi. `gather_timeout: 30` in ansible.cfg. Abilita fact caching: `gathering = smart`, `fact_caching = jsonfile`.

### Problema: Handler non viene eseguito

**Causa**: nome handler ≠ nome nel notify, oppure task non ha generato `changed`. I nomi devono corrispondere **esattamente**. Handler eseguiti solo a fine play — usa `meta: flush_handlers` per esecuzione immediata.

### Problema: Task async timeout

**Soluzione**: aumenta `async: 3600` e `poll: 30`. Per fire-and-forget: `poll: 0` + verifica con `async_status` e `until: job_result.finished`.

### Problema: Connection plugin errato

**Soluzione**: specifica `ansible_connection` per gruppo: `ssh` (Linux), `winrm` (Windows), `local` (localhost).

### Problema: Galaxy collection in conflitto

**Soluzione**: `ansible-galaxy collection install <name> --force`. Pin versioni in requirements.yml: `version: ">=8.0.0,<9.0.0"`. Se persiste: rimuovi la directory della collection e reinstalla.

### Problema: Permission denied su file copiati

**Soluzione**: specifica sempre `owner`, `group`, `mode` nei moduli `copy`/`template`. Su RHEL: verifica contesto SELinux con `sefcontext` + `restorecon -Rv`.

### Problema: Playbook lento

**Diagnosi**: `ANSIBLE_CALLBACKS_ENABLED=profile_tasks ansible-playbook site.yml`. Checklist: pipelining=True, forks=20+, gathering=smart, SSH ControlMaster, batch installs, gather_subset, free strategy.

### Problema: "Shared connection to X closed"

**Causa**: conflitto SSH ControlMaster con sudo. **Soluzione**: `ssh_args = -o ControlPersist=60s -o ServerAliveInterval=15`, `pipelining = True`. Ultimo resort: `ControlMaster=no`.

---

## Riferimenti

- **Ansible Documentation**: https://docs.ansible.com/ansible/latest/
- **Ansible Galaxy** (roles): https://galaxy.ansible.com/
- **Ansible Best Practices**: https://docs.ansible.com/ansible/latest/tips_tricks/
- **Molecule** (testing roles): https://ansible.readthedocs.io/projects/molecule/
- **Ansible Lint**: https://ansible.readthedocs.io/projects/lint/
- **Jeff Geerling's Ansible Books**: https://www.ansiblefordevops.com/
- `ansible-doc -l` — lista tutti i moduli disponibili
- `ansible-doc apt` — documentazione di un modulo specifico

---

## Esercizi

### Esercizio 1: Inventory Multi-Ambiente

Crea una struttura inventory completa per un progetto con tre ambienti (development, staging, production):

1. Definisci almeno 3 gruppi: `webservers`, `dbservers`, `cache`
2. Usa il formato YAML
3. Implementa `group_vars/` con variabili diverse per ambiente (es. `app_debug: true` in development, `false` in production)
4. Implementa `host_vars/` per almeno un host con override specifico
5. Verifica con `ansible-inventory --graph` e `ansible-inventory --host <hostname>`

**Obiettivo:** Comprendere la risoluzione delle variabili e la struttura inventory multi-ambiente.

### Esercizio 2: Role con Molecule

Crea un role `webapp` che:

1. Installa Nginx e configura un virtual host
2. Crea un utente applicativo con chiave SSH
3. Deploya un file `index.html` dal template
4. Configura un servizio systemd per l'applicazione
5. Ha defaults sovrascrivibili (`webapp_port`, `webapp_user`, `webapp_domain`)
6. Include un test Molecule che verifica: servizio attivo, porta in ascolto, health check HTTP

```bash
# Comandi da eseguire:
molecule init role mycompany.webapp --driver-name docker
# ... sviluppa il role ...
molecule test
molecule test --destroy=never   # per debugging
```

**Obiettivo:** Padroneggiare la struttura dei role e il testing con Molecule.

### Esercizio 3: Vault e Deploy Sicuro

Crea un playbook che deploya un'applicazione con gestione completa dei segreti:

1. Cripta le credenziali del database con Vault (usa `encrypt_string` per inline vault)
2. Usa multi-vault ID: `dev` e `prod` con password diverse
3. Il playbook deve: creare il database, l'utente DB, deployare l'app, configurare `.env` con i segreti
4. Verifica che `no_log: true` sia usato per tutte le task che manipolano segreti
5. Testa con `--check --diff` per verificare che i segreti non appaiano nell'output

**Obiettivo:** Gestione sicura dei segreti in un workflow reale.

### Esercizio 4: Rolling Update con Verifica

Implementa un playbook di rolling update per un cluster di 6 web server:

1. Aggiorna i server in batch di 2 (`serial: 2`)
2. Prima di ogni batch: rimuovi dal load balancer (simula con `debug`)
3. Deploya la nuova versione dell'applicazione
4. Esegui health check post-deploy con `uri` module e retry
5. Riaggiungi al load balancer dopo health check positivo
6. Interrompi se >1 server fallisce (`max_fail_percentage: 20`)
7. Alla fine, esegui uno smoke test globale (`run_once: true`)

**Obiettivo:** Padroneggiare `serial`, `max_fail_percentage`, `delegate_to`, e i pattern di zero-downtime deployment.

---

## Auto-valutazione

### Domanda 1: Architettura e Trasporto
Qual è l'unico requisito sui managed nodes per l'esecuzione di moduli Ansible standard? Quale modulo fa eccezione?

<details>
<summary>Risposta</summary>

L'unico requisito è **Python 3** (versione 3.6+, raccomandata 3.10+) installato sul managed node. Ansible copia un modulo Python temporaneo via SSH, lo esegue, e lo rimuove.

L'eccezione è il modulo **`raw`**, che non richiede Python sul nodo. Esegue un comando direttamente via SSH senza wrapping Python, ed è usato tipicamente per installare Python su nodi minimal:

```yaml
- raw: apt-get install -y python3
```

Anche il modulo **`script`** non richiede Python sul nodo target (copia ed esegue uno script locale).

Fonte: https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#managed-node-requirements (consultato 2026-05-23)
</details>

### Domanda 2: Precedenza Variabili
Un role `nginx` ha `nginx_port: 80` in `defaults/main.yml` e `nginx_port: 8080` in `vars/main.yml`. In `group_vars/webservers.yml` hai `nginx_port: 443`. Quale valore viene usato e perché?

<details>
<summary>Risposta</summary>

Il valore usato è **`8080`** (da `roles/nginx/vars/main.yml`).

La precedenza è:
- `defaults/main.yml` → livello 2 (il più basso)
- `group_vars/webservers.yml` → livello 6-7
- `vars/main.yml` → livello 15

`vars/main.yml` (livello 15) sovrascrive `group_vars` (livello 6-7), che a sua volta sovrascrive `defaults` (livello 2).

**Regola pratica**: usa `defaults/` per valori che l'utente del role deve poter sovrascrivere tramite inventory o playbook vars. Usa `vars/` solo per costanti interne al role che non devono essere sovrascritte.

Se vuoi che `group_vars` prevalga, sposta `nginx_port` da `vars/main.yml` a `defaults/main.yml`.

Fonte: https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence (consultato 2026-05-23)
</details>

### Domanda 3: Idempotenza
Perché questa task non è idempotente? Come la correggi?

```yaml
- name: Aggiungi riga al file hosts
  shell: echo "10.0.1.10 app.local" >> /etc/hosts
```

<details>
<summary>Risposta</summary>

Non è idempotente perché ogni esecuzione **aggiunge** una riga duplicata al file. Dopo 5 esecuzioni, il file conterrà 5 copie della stessa riga.

Correzione con il modulo **`lineinfile`** (idempotente per design):

```yaml
- name: Aggiungi riga al file hosts
  lineinfile:
    path: /etc/hosts
    line: "10.0.1.10 app.local"
    state: present
```

`lineinfile` verifica se la riga esiste già prima di aggiungerla. Se esiste, non fa nulla (stato "ok", non "changed").

Alternativa se il `shell` è indispensabile:

```yaml
- name: Aggiungi riga al file hosts
  shell: echo "10.0.1.10 app.local" >> /etc/hosts
  args:
    creates: /etc/hosts.app_local_added
  register: hosts_result
  changed_when: hosts_result.rc == 0
  notify: mark hosts updated
```

Ma questa è una soluzione fragile — il modulo `lineinfile` è sempre preferibile.
</details>

### Domanda 4: Vault Multi-ID
In un progetto con ambienti dev e prod, vuoi usare password vault diverse per ciascun ambiente. Come configuri il sistema e come esegui un playbook che necessita di entrambi i vault?

<details>
<summary>Risposta</summary>

**Configurazione:**

1. Cripta i file con vault-id specifici:
```bash
ansible-vault encrypt --vault-id dev@prompt group_vars/development/vault.yml
ansible-vault encrypt --vault-id prod@/path/to/prod_pass group_vars/production/vault.yml
```

2. In `ansible.cfg`, configura le identità:
```ini
[defaults]
vault_identity_list = dev@/path/to/dev_pass, prod@/path/to/prod_pass
```

3. Oppure da command line:
```bash
ansible-playbook site.yml \
  --vault-id dev@prompt \
  --vault-id prod@/path/to/prod_pass
```

L'header del file criptato registra il vault-id usato (es. `$ANSIBLE_VAULT;1.2;AES256;prod`), e Ansible associa automaticamente la password corretta.

Per sicurezza in CI/CD, usa uno script che legge le password da un secret manager (HashiCorp Vault, AWS Secrets Manager, ecc.) e passalo come `--vault-id dev@script.sh`.

Fonte: https://docs.ansible.com/ansible/latest/vault_guide/vault_managing_passwords.html (consultato 2026-05-23)
</details>

### Domanda 5: Strategy e Serial
Qual è la differenza tra `strategy: free` e `serial: N`? Possono essere combinati?

<details>
<summary>Risposta</summary>

- **`strategy: free`** — Ogni host procede indipendentemente attraverso le task. Gli host veloci non aspettano quelli lenti. Non cambia il numero di host nel play, ma rimuove la sincronizzazione tra task.

- **`serial: N`** — Divide gli host in batch di N. Il play viene eseguito completamente su un batch prima di passare al successivo. Dentro ogni batch, la strategy (default `linear`) sincronizza le task.

**Sì, possono essere combinati:**

```yaml
- hosts: webservers
  serial: 5
  strategy: free
```

Questo esegue il play su 5 host alla volta, ma dentro ogni batch di 5 gli host procedono indipendentemente (senza sincronizzazione tra task).

**Caso d'uso:** Rolling update dove vuoi limitare l'impatto (serial) ma massimizzare la velocità dentro ogni batch (free).

Fonte: https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_strategies.html (consultato 2026-05-23)
</details>

### Domanda 6: Molecule
Qual è la differenza tra `molecule converge` e `molecule test`? Quando usi l'uno e quando l'altro?

<details>
<summary>Risposta</summary>

- **`molecule converge`** — Esegue solo la fase di provisioning (applicazione del role sulle istanze). Non distrugge le istanze alla fine. Utile durante lo **sviluppo**: puoi iterare rapidamente, fare `molecule login` per debugging, e rieseguire `converge` dopo le modifiche.

- **`molecule test`** — Esegue la sequenza completa: `dependency → lint → cleanup → destroy → syntax → create → prepare → converge → idempotence → side_effect → verify → cleanup → destroy`. Distrugge le istanze alla fine. Usato in **CI/CD** e per validazione finale prima del merge.

Sequenza tipica di sviluppo:
```bash
molecule create          # Crea istanze
molecule converge        # Applica il role (ripetibile)
molecule login           # Debug interattivo
molecule converge        # Ri-applica dopo modifiche
molecule idempotence     # Verifica idempotenza
molecule verify          # Esegui test
molecule destroy         # Pulisci quando hai finito
```

In CI/CD: `molecule test` (esegue tutto in un colpo).

Fonte: https://ansible.readthedocs.io/projects/molecule/ (consultato 2026-05-23)
</details>

### Domanda 7: Performance
Elenca 3 ottimizzazioni che puoi applicare ad Ansible per ridurre il tempo di esecuzione su un inventory di 200+ host. Quale ha l'impatto maggiore?

<details>
<summary>Risposta</summary>

Le 3 ottimizzazioni principali:

1. **SSH Pipelining** (`pipelining = True` in ansible.cfg) — Riduce le connessioni SSH da 4+ per task a 1. Richiede `Defaults !requiretty` in `/etc/sudoers`.

2. **Fact Caching** (`gathering = smart`, `fact_caching = jsonfile` o `redis`) — Evita di raccogliere facts ad ogni esecuzione. Su 200 host, il gathering può richiedere 2-5 minuti.

3. **Forks** (`forks = 50` in ansible.cfg) — Aumenta il parallelismo da 5 (default) a 50. Ogni fork è un processo Python sul control node; monitora CPU e RAM.

**Impatto maggiore**: **Mitogen** (se applicabile) — sostituisce il trasporto SSH con un protocollo ottimizzato, riducendo i tempi del 2-7x. Non è un'opzione built-in ma un plugin esterno.

Tra le opzioni built-in, **pipelining** ha l'impatto maggiore perché riduce il numero di round-trip SSH per ogni singola task su ogni singolo host.

Ottimizzazioni aggiuntive: SSH ControlMaster, `gather_subset` per limitare i facts raccolti, batch installs (lista di pacchetti invece di loop), `strategy: free` per task indipendenti.
</details>

### Domanda 8: Sicurezza
Un collega ha scritto questo task. Identifica i problemi di sicurezza:

```yaml
- name: Configura database
  shell: >
    mysql -u root -p{{ db_root_password }}
    -e "CREATE USER '{{ db_user }}'@'%' IDENTIFIED BY '{{ db_password }}'"
```

<details>
<summary>Risposta</summary>

Problemi di sicurezza:

1. **Password nella command line** — La password appare in `ps aux`, nella history di shell, e nei log di Ansible (stdout/stderr del task). Chiunque sul sistema può vederla.

2. **Manca `no_log: true`** — Senza `no_log`, l'intero comando con le password appare nell'output di Ansible e in eventuali log centralizzati.

3. **Usa `shell` invece del modulo dedicato** — Il modulo `mysql_user` gestisce la connessione in modo sicuro, senza esporre password nella process table.

4. **`'%'` come host** — Permette connessione da qualsiasi IP. Dovrebbe essere limitato a subnet specifiche.

**Correzione:**

```yaml
- name: Configura database
  mysql_user:
    name: "{{ db_user }}"
    password: "{{ db_password }}"
    host: "10.0.1.%"
    priv: "{{ db_name }}.*:ALL"
    login_user: root
    login_password: "{{ db_root_password }}"
    login_unix_socket: /var/run/mysqld/mysqld.sock
    state: present
  no_log: true
```

Questo approccio: usa il modulo dedicato (no process table leaks), aggiunge `no_log`, e limita l'host di connessione.
</details>

---

## Letture Primarie

| Risorsa | URL | Note |
|---------|-----|------|
| Ansible Documentation — Getting Started | https://docs.ansible.com/ansible/latest/getting_started/ | Punto di partenza ufficiale |
| Ansible Playbook Guide | https://docs.ansible.com/ansible/latest/playbook_guide/ | Guida completa ai playbook |
| Ansible Module Index | https://docs.ansible.com/ansible/latest/collections/index.html | Indice di tutti i moduli per collection |
| Variable Precedence | https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence | I 22 livelli di precedenza |
| Ansible Vault Guide | https://docs.ansible.com/ansible/latest/vault_guide/ | Guida completa a Vault |
| Ansible Galaxy | https://galaxy.ansible.com/ | Repository pubblico di roles e collections |
| Molecule Documentation | https://ansible.readthedocs.io/projects/molecule/ | Testing framework per roles |
| Ansible Lint Documentation | https://ansible.readthedocs.io/projects/lint/ | Linter per best practices |
| AWX Documentation | https://ansible.readthedocs.io/projects/awx/ | Versione open-source di AAP |
| Red Hat AAP | https://www.redhat.com/en/technologies/management/ansible | Piattaforma enterprise |
| Ansible Best Practices | https://docs.ansible.com/ansible/latest/tips_tricks/ansible_tips_tricks.html | Tips & tricks ufficiali |
| Ansible Performance Tuning | https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_strategies.html | Strategie e parallelismo |

Data di consultazione: 2026-05-23

---

## Collegamenti Incrociati

| Modulo | Titolo | Relazione |
|--------|--------|-----------|
| 01 | Fondamenti Linux | Prerequisito: CLI, filesystem, permessi |
| 02 | Shell Scripting | Prerequisito: bash scripting per template e script Ansible |
| 10 | Networking | Prerequisito: SSH, firewall, DNS |
| 15 | Security Hardening | Complementare: hardening manuale vs automatizzato con Ansible |
| 18 | Docker & Containers | Complementare: Ansible per orchestrazione container, Molecule usa Docker |
| 20 | CI/CD Pipelines | Complementare: Ansible nei pipeline CI/CD, GitOps |
| 25 | Cloud Infrastructure | Complementare: provisioning cloud con moduli Ansible |
| 30 | Infrastructure as Code | Complementare: Ansible vs Terraform, quando usare quale |
| 32 | Kubernetes | Complementare: Ansible per bootstrap cluster K8s, AWX su K8s |

---

## Glossario Locale

| Termine | Definizione |
|---------|-------------|
| **Control Node** | La macchina su cui è installato Ansible e da cui vengono eseguiti i playbook |
| **Managed Node** | Un server gestito da Ansible (target node). Non richiede agenti |
| **Inventory** | File o plugin che definisce gli host e i gruppi gestiti da Ansible |
| **Playbook** | File YAML che dichiara lo stato desiderato dell'infrastruttura |
| **Play** | Un blocco all'interno di un playbook che associa un gruppo di host a una lista di task |
| **Task** | Una singola azione in un playbook (es. installa pacchetto, copia file) |
| **Module** | Unità di codice Python che Ansible esegue sui managed nodes (es. `apt`, `copy`, `template`) |
| **Role** | Struttura directory standard per organizzare task, handler, variabili e template riutilizzabili |
| **Collection** | Pacchetto di distribuzione che contiene moduli, roles, plugin e documentazione con namespace |
| **Handler** | Task speciale eseguita solo quando notificata da un'altra task (tipicamente restart/reload servizi) |
| **Fact** | Variabile raccolta automaticamente dal sistema target (OS, RAM, IP, ecc.) |
| **Vault** | Meccanismo di crittografia per proteggere variabili sensibili (password, chiavi, certificati) |
| **Idempotenza** | Proprietà per cui eseguire un'operazione più volte produce sempre lo stesso risultato |
| **FQCN** | Fully Qualified Collection Name — formato `namespace.collection.module` (es. `amazon.aws.ec2_instance`) |
| **Jinja2** | Motore di template Python usato da Ansible per generare file di configurazione dinamici |
| **Pipelining** | Ottimizzazione SSH che esegue moduli senza creare file temporanei sul managed node |
| **AWX** | Versione open-source di Ansible Automation Platform (ex Tower) con UI web, API, RBAC |
| **AAP** | Ansible Automation Platform — prodotto enterprise Red Hat (include AWX + supporto) |
| **Become** | Meccanismo di escalazione dei privilegi (tipicamente sudo) per eseguire task come root |
| **Galaxy** | Repository pubblico di roles e collections Ansible, e il tool CLI per gestirle |
| **Molecule** | Framework di test per roles Ansible, esegue i test in container isolati |
| **Serial** | Parametro del play che esegue il deployment in batch di N host alla volta |
| **Strategy** | Plugin che controlla l'ordine di esecuzione delle task (linear, free, debug) |
| **Callback Plugin** | Plugin che intercetta eventi di esecuzione per modificare output o inviare notifiche |
| **stdout_callback** | Il callback che controlla il formato visivo dell'output nel terminale (uno solo attivo) |
| **WinRM** | Windows Remote Management — protocollo per gestire host Windows da Ansible |
| **Constructed Inventory** | Plugin inventory che crea gruppi e variabili calcolati a runtime dai facts esistenti |
| **argument_spec** | Schema di validazione dei parametri di un role, dichiarato in `meta/argument_specs.yml` |
| **network_cli** | Connection plugin per dispositivi di rete che usano CLI via SSH |
| **netconf** | Connection plugin per dispositivi di rete che supportano il protocollo NETCONF (RFC 6241) |
| **httpapi** | Connection plugin per dispositivi di rete gestiti via REST/HTTP API |
