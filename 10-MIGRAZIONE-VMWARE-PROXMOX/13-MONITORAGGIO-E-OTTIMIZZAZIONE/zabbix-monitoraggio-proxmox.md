# Zabbix per il Monitoraggio di Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 5 — Operativita post-migrazione · Modulo 13.1 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** Proxmox cluster operativo; concetti generali monitoring (metriche, soglie, alerting); familiarita Zabbix (server, proxy, agent, template).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. configurare Zabbix Server e Zabbix Agent sui nodi Proxmox VE per raccogliere metriche di sistema (CPU, RAM, disk, network, load);
> 2. integrare Zabbix con la **API Proxmox** (REST) per metriche cluster-level (numero VM running per nodo, stato HA, uso storage per pool);
> 3. configurare **template Zabbix** (community o custom) per discovery automatico di VM, container, storage pool;
> 4. impostare **trigger e alerting** efficaci con soglie multi-step (warning, average, high, disaster) e dependencies per evitare alert fatigue;
> 5. integrare con sistemi di notifica (email, Slack, PagerDuty, webhook custom);
> 6. comparare con Prometheus + Grafana + Alertmanager (alternativa moderna, open-source, pull-based);
> 7. confrontare con vRealize Operations (vROps) o Aria Operations (per chi viene da VMware).
> **Tempo stimato:** lettura 60-90 min · lab 240-360 min (deploy Zabbix + agent + dashboard + alert)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; Zabbix 7.x LTS; Zabbix Agent 2 (Go-based).

## Mappa concettuale

```
+============================================================+
|     Zabbix monitoring stack per Proxmox                    |
+============================================================+
|                                                            |
|   COMPONENTI                                               |
|                                                            |
|   Zabbix Server          DB MySQL/PostgreSQL + frontend    |
|   Zabbix Proxy           opzionale, riduce carico server    |
|   Zabbix Agent (host)    su ogni nodo Proxmox VE           |
|   Zabbix Agent (guest)   opzionale, su VM monitorata       |
|                                                            |
|   FONTI DATI                                               |
|                                                            |
|   Agent passive  pull dal server (porta 10050)             |
|   Agent active   push al server (porta 10051)              |
|   SNMP           per device storage/networking             |
|   API Proxmox    cluster.json, statistics                  |
|   IPMI           hardware health (out-of-band)             |
|                                                            |
|   TEMPLATE                                                 |
|                                                            |
|   Linux by Zabbix Agent  (built-in)                        |
|   Proxmox VE by HTTP     (community: API monitoring)       |
|   Custom discovery       per VM, storage pool, network     |
|                                                            |
|   ALERTING                                                 |
|                                                            |
|   Trigger      condizione (es. CPU > 90% per 5min)         |
|   Severity     warning -> average -> high -> disaster      |
|   Action       notification email/slack/webhook            |
|   Dependencies trigger A blocca trigger B se A fired       |
|   Maintenance  finestra di silenziamento                   |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Monitoring senza alerting actionable e dashboard art.** Bel grafico, zero valore operativo. Per ogni metrica, chiedi: "se questa supera la soglia, cosa fa l'on-call?". Se la risposta e "boh", la metrica non serve come alert.
2. **Zabbix vs Prometheus: Zabbix e push+config-heavy, Prometheus e pull+code-as-config.** Per organizzazioni gia Zabbix-skilled, restare in Zabbix. Per green-field cloud-native, Prometheus + Grafana + Alertmanager e standard de facto.
3. **Auto-discovery e mandatory.** Aggiungere VM manuale a Zabbix non scala. Configurare LLD (Low-Level Discovery) basato su API Proxmox per auto-add nuove VM, auto-cleanup VM rimosse.
4. **Alert fatigue uccide il monitoring.** > 50 alert/giorno = nessuno li legge. Gerarchia: severity, dipendenze, soglie multi-step, suppression in finestra manutenzione.

---

## Introduzione a Zabbix per Ambienti Proxmox

Zabbix rappresenta una delle piattaforme di monitoraggio enterprise open-source più mature e diffuse, con oltre 20 anni di sviluppo. Per le organizzazioni che migrano da VMware a Proxmox, Zabbix offre un percorso naturale di transizione: chi già utilizzava Zabbix con l'integrazione VMware nativa può facilmente estendere il monitoraggio per coprire Proxmox VE senza cambiare piattaforma.

A differenza dello stack Prometheus+Grafana, che eccelle nel monitoraggio cloud-native e nelle metriche time-series, Zabbix offre un approccio più tradizionale e integrato che include discovery automatico, trigger complessi, azioni automatizzate e un ecosistema di template pronti all'uso.

### Confronto degli Approcci di Monitoraggio

```
┌──────────────────────┬────────────────────┬───────────────────────┬─────────────────┐
│ Caratteristica       │ Zabbix             │ Prometheus+Grafana    │ VMware vROps     │
├──────────────────────┼────────────────────┼───────────────────────┼─────────────────┤
│ Modello              │ Push/Pull (agent)  │ Pull (scraping)       │ Push (agent)     │
│ Database             │ MySQL/PostgreSQL   │ TSDB proprio          │ Cassandra        │
│ Dashboard            │ Integrata          │ Grafana (separata)    │ Integrata        │
│ Template             │ Ricco ecosistema   │ Community dashboard   │ Proprietari      │
│ Auto-discovery       │ Nativo avanzato    │ Service discovery     │ Automatico       │
│ Alerting             │ Integrato          │ AlertManager          │ Integrato        │
│ Agent                │ Zabbix Agent       │ Exporters             │ VMware Tools     │
│ API monitoring       │ HTTP Agent nativo  │ Custom exporter       │ Nativo           │
│ Scalabilità          │ Proxy distribuiti  │ Federation/Thanos     │ Cluster vROps    │
│ Costo                │ Gratuito           │ Gratuito              │ Licenza costosa  │
│ Curva apprendimento  │ Media-alta         │ Media                 │ Alta             │
│ Integrazione VMware  │ Template nativo    │ vmware_exporter       │ Nativa completa  │
│ Integrazione Proxmox │ Template community │ pve_exporter          │ Non disponibile  │
└──────────────────────┴────────────────────┴───────────────────────┴─────────────────┘
```

---

## Installazione del Server Zabbix

### Prerequisiti e Pianificazione

```
Requisiti hardware per il server Zabbix:
┌────────────────────────┬──────────────┬───────────────┬────────────────┐
│ Scenario               │ CPU          │ RAM           │ Disco          │
├────────────────────────┼──────────────┼───────────────┼────────────────┤
│ Piccolo (<100 host)    │ 2 vCPU       │ 4 GB          │ 50 GB SSD      │
│ Medio (100-500 host)   │ 4 vCPU       │ 8 GB          │ 200 GB SSD     │
│ Grande (500-5000 host) │ 8+ vCPU      │ 16+ GB        │ 500 GB+ SSD   │
│ Enterprise (5000+)     │ 16+ vCPU     │ 64+ GB        │ 1 TB+ SSD     │
└────────────────────────┴──────────────┴───────────────┴────────────────┘
```

### Installazione su Debian 12 (Bookworm)

```bash
# Aggiungere il repository Zabbix 7.0 LTS
wget https://repo.zabbix.com/zabbix/7.0/debian/pool/main/z/zabbix-release/zabbix-release_7.0-1+debian12_all.deb
dpkg -i zabbix-release_7.0-1+debian12_all.deb
apt update

# Installare il server Zabbix con frontend e database PostgreSQL
apt install -y zabbix-server-pgsql zabbix-frontend-php php8.2-pgsql \
    zabbix-nginx-conf zabbix-sql-scripts zabbix-agent2 postgresql

# Configurare il database PostgreSQL
sudo -u postgres createuser --pwprompt zabbix
# Inserire la password quando richiesto

sudo -u postgres createdb -O zabbix zabbix

# Importare lo schema iniziale
zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | \
    sudo -u zabbix psql zabbix

# Configurare il server Zabbix
cat > /etc/zabbix/zabbix_server.conf << 'EOF'
# Configurazione Database
DBHost=localhost
DBName=zabbix
DBUser=zabbix
DBPassword=password_sicura_qui

# Performance tuning
StartPollers=10
StartPollersUnreachable=5
StartTrappers=5
StartPingers=3
StartDiscoverers=3
StartHTTPPollers=5
StartTimers=2
StartEscalators=2

# Cache
CacheSize=256M
HistoryCacheSize=128M
HistoryIndexCacheSize=64M
TrendCacheSize=64M
ValueCacheSize=128M

# Housekeeping
HousekeepingFrequency=1
MaxHousekeeperDelete=10000

# Timeout
Timeout=30

# Log
LogFile=/var/log/zabbix/zabbix_server.log
LogFileSize=100
DebugLevel=3

# Alert scripts
AlertScriptsPath=/usr/lib/zabbix/alertscripts
ExternalScripts=/usr/lib/zabbix/externalscripts
EOF

# Configurare Nginx per il frontend
cat > /etc/zabbix/nginx.conf << 'EOF'
server {
    listen 8080;
    server_name zabbix.azienda.local;

    root /usr/share/zabbix;

    index index.php;

    location = /favicon.ico {
        log_not_found off;
    }

    location / {
        try_files $uri $uri/ =404;
    }

    location /assets {
        access_log off;
        expires 10d;
    }

    location ~ /\.ht {
        deny all;
    }

    location ~ /(api\/|conf[^\.]|include|locale) {
        deny all;
        return 404;
    }

    location /vendor {
        deny all;
        return 404;
    }

    location ~ [^/]\.php(/|$) {
        fastcgi_pass unix:/var/run/php/php8.2-fpm.sock;
        fastcgi_split_path_info ^(.+\.php)(/.+)$;
        fastcgi_index index.php;

        fastcgi_param DOCUMENT_ROOT /usr/share/zabbix;
        fastcgi_param SCRIPT_FILENAME /usr/share/zabbix$fastcgi_script_name;
        fastcgi_param PATH_TRANSLATED /usr/share/zabbix$fastcgi_script_name;

        include fastcgi_params;
        fastcgi_param QUERY_STRING $query_string;
        fastcgi_param REQUEST_METHOD $request_method;
        fastcgi_param CONTENT_TYPE $content_type;
        fastcgi_param CONTENT_LENGTH $content_length;

        fastcgi_intercept_errors on;
        fastcgi_ignore_client_abort off;
        fastcgi_connect_timeout 60;
        fastcgi_send_timeout 180;
        fastcgi_read_timeout 180;
        fastcgi_buffer_size 128k;
        fastcgi_buffers 4 256k;
        fastcgi_busy_buffers_size 256k;
        fastcgi_temp_file_write_size 256k;
    }
}
EOF

# Configurare PHP
sed -i 's/^;date.timezone.*/date.timezone = Europe\/Rome/' /etc/php/8.2/fpm/php.ini
sed -i 's/^max_execution_time.*/max_execution_time = 300/' /etc/php/8.2/fpm/php.ini
sed -i 's/^max_input_time.*/max_input_time = 300/' /etc/php/8.2/fpm/php.ini
sed -i 's/^post_max_size.*/post_max_size = 16M/' /etc/php/8.2/fpm/php.ini
sed -i 's/^upload_max_filesize.*/upload_max_filesize = 2M/' /etc/php/8.2/fpm/php.ini

# Avviare tutti i servizi
systemctl restart php8.2-fpm nginx
systemctl enable --now zabbix-server zabbix-agent2
systemctl enable --now nginx php8.2-fpm

# Verificare lo stato
systemctl status zabbix-server
systemctl status zabbix-agent2
```

---

## Installazione dell'Agent Zabbix sui Nodi Proxmox

### Zabbix Agent 2 (Raccomandato)

```bash
# Su ogni nodo Proxmox, aggiungere il repository e installare
wget https://repo.zabbix.com/zabbix/7.0/debian/pool/main/z/zabbix-release/zabbix-release_7.0-1+debian12_all.deb
dpkg -i zabbix-release_7.0-1+debian12_all.deb
apt update
apt install -y zabbix-agent2 zabbix-agent2-plugin-*

# Configurare l'agent
cat > /etc/zabbix/zabbix_agent2.conf << 'EOF'
# Configurazione base
PidFile=/run/zabbix/zabbix_agent2.pid
LogFile=/var/log/zabbix/zabbix_agent2.log
LogFileSize=100

# Server Zabbix
Server=zabbix-server.local
ServerActive=zabbix-server.local

# Hostname (deve corrispondere all'host in Zabbix)
Hostname=pve-node01
HostnameItem=system.hostname

# Metadata per auto-registration
HostMetadata=Linux Proxmox VE

# Timeout
Timeout=30

# Monitoraggio avanzato
EnableRemoteCommands=1
LogRemoteCommands=1

# Plugin configurazione
Plugins.SystemRun.LogRemoteCommands=1

# User parameters personalizzati per Proxmox
Include=/etc/zabbix/zabbix_agent2.d/*.conf
EOF

# Creare user parameters per Proxmox
cat > /etc/zabbix/zabbix_agent2.d/proxmox.conf << 'EOF'
# === User Parameters per Proxmox VE ===

# Numero di VM in esecuzione
UserParameter=pve.vm.running,qm list 2>/dev/null | grep running | wc -l

# Numero di VM ferme
UserParameter=pve.vm.stopped,qm list 2>/dev/null | grep stopped | wc -l

# Numero totale di VM
UserParameter=pve.vm.total,qm list 2>/dev/null | tail -n +2 | wc -l

# Numero di container in esecuzione
UserParameter=pve.ct.running,pct list 2>/dev/null | grep running | wc -l

# Numero totale di container
UserParameter=pve.ct.total,pct list 2>/dev/null | tail -n +2 | wc -l

# Stato del cluster (quorate: yes/no)
UserParameter=pve.cluster.quorate,pvecm status 2>/dev/null | grep "Quorate:" | awk '{print $2}'

# Numero di nodi nel cluster
UserParameter=pve.cluster.nodes,pvecm nodes 2>/dev/null | tail -n +2 | wc -l

# Versione Proxmox
UserParameter=pve.version,pveversion 2>/dev/null

# Stato Ceph (HEALTH_OK, HEALTH_WARN, HEALTH_ERR)
UserParameter=pve.ceph.health,ceph health 2>/dev/null | awk '{print $1}'

# Numero OSD up
UserParameter=pve.ceph.osd.up,ceph osd stat 2>/dev/null | grep -oP '\d+ up' | awk '{print $1}'

# Numero OSD totali
UserParameter=pve.ceph.osd.total,ceph osd stat 2>/dev/null | grep -oP '^\d+' | head -1

# Utilizzo storage Ceph percentuale
UserParameter=pve.ceph.usage.pct,ceph df 2>/dev/null | grep TOTAL | awk '{print $5}' | tr -d '%'

# Storage specifico: utilizzo percentuale
UserParameter=pve.storage.usage[*],pvesh get /nodes/$(hostname)/storage/$1/status 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(round(d['used']/d['total']*100,1))" 2>/dev/null || echo 0

# Lista VM con dettagli (JSON per discovery)
UserParameter=pve.vm.discovery,pvesh get /nodes/$(hostname)/qemu --output-format json 2>/dev/null | python3 -c "import json,sys; data=json.load(sys.stdin); result={'data':[{'{#VMID}':str(v['vmid']),'{#VMNAME}':v.get('name',''),'{#VMSTATUS}':v.get('status','')} for v in data]}; print(json.dumps(result))"

# CPU di una VM specifica
UserParameter=pve.vm.cpu[*],pvesh get /nodes/$(hostname)/qemu/$1/status/current 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(round(d.get('cpu',0)*100,2))" 2>/dev/null || echo 0

# Memoria di una VM specifica (percentuale)
UserParameter=pve.vm.mem.pct[*],pvesh get /nodes/$(hostname)/qemu/$1/status/current 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(round(d.get('mem',0)*100,2))" 2>/dev/null || echo 0

# Uptime di una VM specifica
UserParameter=pve.vm.uptime[*],pvesh get /nodes/$(hostname)/qemu/$1/status/current 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('uptime',0))" 2>/dev/null || echo 0

# Stato HA di una risorsa
UserParameter=pve.ha.status[*],pvesh get /cluster/ha/resources/vm:$1 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('state','unknown'))" 2>/dev/null || echo "not_configured"
EOF

# Impostare i permessi per l'utente zabbix
usermod -aG www-data zabbix

# Creare un file sudoers per i comandi Proxmox
cat > /etc/sudoers.d/zabbix-proxmox << 'EOF'
# Permessi Zabbix per monitoraggio Proxmox
zabbix ALL=(ALL) NOPASSWD: /usr/sbin/qm list
zabbix ALL=(ALL) NOPASSWD: /usr/sbin/qm config *
zabbix ALL=(ALL) NOPASSWD: /usr/sbin/qm status *
zabbix ALL=(ALL) NOPASSWD: /usr/sbin/pct list
zabbix ALL=(ALL) NOPASSWD: /usr/sbin/pct config *
zabbix ALL=(ALL) NOPASSWD: /usr/sbin/pct status *
zabbix ALL=(ALL) NOPASSWD: /usr/bin/pvecm status
zabbix ALL=(ALL) NOPASSWD: /usr/bin/pvecm nodes
zabbix ALL=(ALL) NOPASSWD: /usr/bin/pvesh get *
zabbix ALL=(ALL) NOPASSWD: /usr/bin/pveversion
zabbix ALL=(ALL) NOPASSWD: /usr/bin/ceph *
EOF

chmod 440 /etc/sudoers.d/zabbix-proxmox

systemctl enable --now zabbix-agent2
systemctl restart zabbix-agent2

# Verificare la connettività
zabbix_agent2 -t pve.vm.running
zabbix_agent2 -t pve.version
```

### Deploy Automatizzato su Tutti i Nodi

```bash
#!/bin/bash
# deploy-zabbix-agent.sh - Deploy Zabbix Agent 2 su tutti i nodi Proxmox

NODES="pve-node01 pve-node02 pve-node03"
ZABBIX_SERVER="zabbix-server.local"

for NODE in ${NODES}; do
    echo "=== Installazione su ${NODE} ==="

    ssh ${NODE} << EOF
        # Installare il repository e l'agent
        wget -q https://repo.zabbix.com/zabbix/7.0/debian/pool/main/z/zabbix-release/zabbix-release_7.0-1+debian12_all.deb
        dpkg -i zabbix-release_7.0-1+debian12_all.deb
        apt update -qq
        apt install -y -qq zabbix-agent2

        # Configurazione base
        sed -i "s/^Server=.*/Server=${ZABBIX_SERVER}/" /etc/zabbix/zabbix_agent2.conf
        sed -i "s/^ServerActive=.*/ServerActive=${ZABBIX_SERVER}/" /etc/zabbix/zabbix_agent2.conf
        sed -i "s/^Hostname=.*/Hostname=${NODE}/" /etc/zabbix/zabbix_agent2.conf

        systemctl enable --now zabbix-agent2
        echo "${NODE}: Installazione completata"
EOF

    # Copiare la configurazione personalizzata per Proxmox
    scp /etc/zabbix/zabbix_agent2.d/proxmox.conf ${NODE}:/etc/zabbix/zabbix_agent2.d/
    scp /etc/sudoers.d/zabbix-proxmox ${NODE}:/etc/sudoers.d/
    ssh ${NODE} "systemctl restart zabbix-agent2"

    echo "${NODE}: Configurazione Proxmox applicata"
done
```

---

## Monitoraggio SNMP di Proxmox

### Configurazione SNMP sul Nodo Proxmox

```bash
# Installare snmpd
apt install -y snmpd snmp libsnmp-dev

# Configurare SNMP v2c (base)
cat > /etc/snmp/snmpd.conf << 'EOF'
# Comunità SNMP v2c (solo lettura)
rocommunity proxmox_monitor 10.0.0.0/24
rocommunity6 proxmox_monitor ::1/128

# Informazioni di sistema
sysLocation    Datacenter Principale
sysContact     admin@azienda.it
sysName        pve-node01

# Accesso
agentAddress  udp:161,udp6:[::1]:161

# Estendere con dati personalizzati Proxmox
extend pve-vm-count /usr/local/bin/pve-snmp-vmcount.sh
extend pve-ct-count /usr/local/bin/pve-snmp-ctcount.sh
extend pve-cluster-status /usr/local/bin/pve-snmp-cluster.sh

# Monitoraggio disco
disk / 10%
disk /var/lib/vz 10%

# Monitoraggio processi
proc qemu-system 0 0
proc pvedaemon 1 1
proc pveproxy 1 1
proc corosync 1 1

# Monitoraggio load average
load 12 14 14
EOF

# Script helper per SNMP
cat > /usr/local/bin/pve-snmp-vmcount.sh << 'SCRIPT'
#!/bin/bash
echo $(qm list 2>/dev/null | grep running | wc -l)
SCRIPT
chmod +x /usr/local/bin/pve-snmp-vmcount.sh

cat > /usr/local/bin/pve-snmp-ctcount.sh << 'SCRIPT'
#!/bin/bash
echo $(pct list 2>/dev/null | grep running | wc -l)
SCRIPT
chmod +x /usr/local/bin/pve-snmp-ctcount.sh

cat > /usr/local/bin/pve-snmp-cluster.sh << 'SCRIPT'
#!/bin/bash
echo $(pvecm status 2>/dev/null | grep "Quorate:" | awk '{print $2}')
SCRIPT
chmod +x /usr/local/bin/pve-snmp-cluster.sh

systemctl enable --now snmpd
systemctl restart snmpd

# Verificare SNMP
snmpwalk -v2c -c proxmox_monitor localhost system
snmpwalk -v2c -c proxmox_monitor localhost .1.3.6.1.4.1.8072.1.3.2
```

### Configurazione SNMP v3 (Sicuro)

```bash
# Fermare snmpd prima della configurazione v3
systemctl stop snmpd

# Creare un utente SNMPv3
net-snmp-create-v3-user -ro -A "AuthPassword123!" -a SHA -X "PrivPassword456!" -x AES pve_monitor

# Verificare
systemctl start snmpd
snmpwalk -v3 -u pve_monitor -l authPriv -a SHA -A "AuthPassword123!" -x AES -X "PrivPassword456!" localhost system
```

### Configurazione SNMP in Zabbix

```
Aggiungere host in Zabbix con interfaccia SNMP:
1. Configuration → Hosts → Create Host
2. Host name: pve-node01
3. Groups: Proxmox Nodes
4. Interfaces:
   - Agent: 10.0.0.11:10050
   - SNMP: 10.0.0.11:161
5. SNMP version: v2c (o v3 per produzione)
6. Community: proxmox_monitor
7. Templates: Template OS Linux by SNMP
```

---

## Monitoraggio via API con Zabbix HTTP Agent

### Configurazione dell'Accesso API Proxmox

```bash
# Creare un utente API dedicato per Zabbix
pveum user add zabbix@pve --comment "Zabbix monitoring user"
pveum passwd zabbix@pve

# Creare il ruolo con permessi minimi
pveum role add ZabbixMonitoring -privs "VM.Audit,Datastore.Audit,Sys.Audit,Pool.Audit"

# Assegnare il ruolo
pveum aclmod / -user zabbix@pve -role ZabbixMonitoring

# Creare un API token
pveum user token add zabbix@pve monitoring --privsep 0
# Salvare il valore del token!

# Test dell'API
curl -s -k -H "Authorization: PVEAPIToken=zabbix@pve!monitoring=TOKEN_VALORE" \
    "https://pve-node01:8006/api2/json/cluster/resources" | python3 -m json.tool | head -30
```

### Template Zabbix con HTTP Agent per Proxmox API

```xml
<?xml version="1.0" encoding="UTF-8"?>
<zabbix_export>
    <version>7.0</version>
    <template_groups>
        <template_group>
            <uuid>generated-uuid-here</uuid>
            <name>Templates/Virtualization</name>
        </template_group>
    </template_groups>
    <templates>
        <template>
            <uuid>generated-uuid-here</uuid>
            <template>Proxmox VE by HTTP</template>
            <name>Proxmox VE by HTTP</name>
            <description>Template per il monitoraggio di Proxmox VE via API REST</description>
            <groups>
                <group>
                    <name>Templates/Virtualization</name>
                </group>
            </groups>
            <macros>
                <macro>
                    <macro>{$PVE.URL}</macro>
                    <value>https://pve-node01:8006</value>
                    <description>URL del nodo Proxmox</description>
                </macro>
                <macro>
                    <macro>{$PVE.TOKEN.ID}</macro>
                    <value>zabbix@pve!monitoring</value>
                    <description>ID del token API</description>
                </macro>
                <macro>
                    <macro>{$PVE.TOKEN.SECRET}</macro>
                    <value></value>
                    <type>SECRET_TEXT</type>
                    <description>Secret del token API</description>
                </macro>
                <macro>
                    <macro>{$PVE.NODE}</macro>
                    <value>pve-node01</value>
                    <description>Nome del nodo Proxmox</description>
                </macro>
            </macros>
            <items>
                <!-- Stato del nodo -->
                <item>
                    <uuid>generated-uuid</uuid>
                    <name>PVE: Node Status Raw</name>
                    <type>HTTP_AGENT</type>
                    <key>pve.node.status.raw</key>
                    <delay>60s</delay>
                    <value_type>TEXT</value_type>
                    <url>{$PVE.URL}/api2/json/nodes/{$PVE.NODE}/status</url>
                    <headers>
                        <header>
                            <name>Authorization</name>
                            <value>PVEAPIToken={$PVE.TOKEN.ID}={$PVE.TOKEN.SECRET}</value>
                        </header>
                    </headers>
                    <verify_peer>NO</verify_peer>
                    <verify_host>NO</verify_host>
                </item>
                <!-- CPU Usage -->
                <item>
                    <uuid>generated-uuid</uuid>
                    <name>PVE: CPU Usage</name>
                    <type>DEPENDENT</type>
                    <key>pve.node.cpu</key>
                    <delay>0</delay>
                    <value_type>FLOAT</value_type>
                    <units>%</units>
                    <master_item>
                        <key>pve.node.status.raw</key>
                    </master_item>
                    <preprocessing>
                        <step>
                            <type>JSONPATH</type>
                            <parameters>
                                <parameter>$.data.cpu</parameter>
                            </parameters>
                        </step>
                        <step>
                            <type>MULTIPLIER</type>
                            <parameters>
                                <parameter>100</parameter>
                            </parameters>
                        </step>
                    </preprocessing>
                </item>
            </items>
        </template>
    </templates>
</zabbix_export>
```

### Script Python per la Raccolta Metriche via API

```python
#!/usr/bin/env python3
"""
pve_zabbix_collector.py - Raccoglie metriche Proxmox VE per Zabbix
Utilizzo con Zabbix External Check o Trapper
"""

import json
import sys
import ssl
import urllib.request
import urllib.error
from datetime import datetime

# Configurazione
PVE_HOST = "pve-node01.local"
PVE_PORT = 8006
TOKEN_ID = "zabbix@pve!monitoring"
TOKEN_SECRET = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Disabilitare la verifica SSL per certificati self-signed
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def pve_api_call(endpoint):
    """Effettua una chiamata all'API Proxmox"""
    url = f"https://{PVE_HOST}:{PVE_PORT}/api2/json{endpoint}"
    headers = {
        "Authorization": f"PVEAPIToken={TOKEN_ID}={TOKEN_SECRET}"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        response = urllib.request.urlopen(req, context=ssl_context)
        return json.loads(response.read())["data"]
    except urllib.error.URLError as e:
        print(f"Errore API: {e}", file=sys.stderr)
        return None

def get_cluster_resources():
    """Ottiene tutte le risorse del cluster"""
    return pve_api_call("/cluster/resources")

def get_node_status(node):
    """Ottiene lo stato di un nodo"""
    return pve_api_call(f"/nodes/{node}/status")

def get_vm_list(node):
    """Ottiene la lista delle VM su un nodo"""
    return pve_api_call(f"/nodes/{node}/qemu")

def get_storage_status(node):
    """Ottiene lo stato degli storage di un nodo"""
    return pve_api_call(f"/nodes/{node}/storage")

def generate_zabbix_discovery(resources, resource_type):
    """Genera output di discovery per Zabbix LLD"""
    discovery_data = []
    for res in resources:
        if res.get("type") == resource_type:
            item = {
                "{#ID}": str(res.get("vmid", res.get("id", ""))),
                "{#NAME}": res.get("name", ""),
                "{#STATUS}": res.get("status", ""),
                "{#NODE}": res.get("node", ""),
                "{#TYPE}": res.get("type", "")
            }
            if resource_type in ("qemu", "lxc"):
                item["{#MAXMEM}"] = str(res.get("maxmem", 0))
                item["{#MAXCPU}"] = str(res.get("maxcpu", 0))
                item["{#MAXDISK}"] = str(res.get("maxdisk", 0))
            discovery_data.append(item)
    return json.dumps({"data": discovery_data}, indent=2)

def main():
    if len(sys.argv) < 2:
        print("Utilizzo: pve_zabbix_collector.py <comando> [parametri]")
        print("Comandi: discovery_vm, discovery_ct, discovery_storage,")
        print("         node_cpu, node_mem, vm_cpu <vmid>, vm_mem <vmid>")
        sys.exit(1)

    command = sys.argv[1]
    resources = get_cluster_resources()

    if resources is None:
        print("Errore: impossibile ottenere le risorse")
        sys.exit(1)

    if command == "discovery_vm":
        print(generate_zabbix_discovery(resources, "qemu"))
    elif command == "discovery_ct":
        print(generate_zabbix_discovery(resources, "lxc"))
    elif command == "discovery_storage":
        print(generate_zabbix_discovery(resources, "storage"))
    elif command == "node_cpu":
        node = sys.argv[2] if len(sys.argv) > 2 else PVE_HOST.split(".")[0]
        status = get_node_status(node)
        if status:
            print(f"{status.get('cpu', 0) * 100:.2f}")
    elif command == "node_mem":
        node = sys.argv[2] if len(sys.argv) > 2 else PVE_HOST.split(".")[0]
        status = get_node_status(node)
        if status:
            mem = status.get("memory", {})
            pct = (mem.get("used", 0) / mem.get("total", 1)) * 100
            print(f"{pct:.2f}")
    elif command == "vm_cpu":
        vmid = sys.argv[2]
        for res in resources:
            if res.get("type") == "qemu" and str(res.get("vmid")) == vmid:
                print(f"{res.get('cpu', 0) * 100:.2f}")
                break
    elif command == "vm_mem":
        vmid = sys.argv[2]
        for res in resources:
            if res.get("type") == "qemu" and str(res.get("vmid")) == vmid:
                if res.get("maxmem", 0) > 0:
                    pct = (res.get("mem", 0) / res.get("maxmem", 1)) * 100
                    print(f"{pct:.2f}")
                break
    else:
        print(f"Comando sconosciuto: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

```bash
# Installare lo script
cp pve_zabbix_collector.py /usr/lib/zabbix/externalscripts/
chmod +x /usr/lib/zabbix/externalscripts/pve_zabbix_collector.py

# Test
/usr/lib/zabbix/externalscripts/pve_zabbix_collector.py discovery_vm
/usr/lib/zabbix/externalscripts/pve_zabbix_collector.py node_cpu pve-node01
```

---

## Trigger e Soglie di Monitoraggio

### Definizione dei Trigger Principali

```
Trigger critici per Proxmox:
┌─────────────────────────────────────┬──────────┬─────────────────────────────────┐
│ Trigger                             │ Severità │ Espressione Zabbix              │
├─────────────────────────────────────┼──────────┼─────────────────────────────────┤
│ Nodo non raggiungibile              │ Disaster │ nodata(pve.node.cpu,5m)=1       │
│ CPU nodo > 95% per 5 min            │ High     │ min(pve.node.cpu,5m)>95         │
│ CPU nodo > 85% per 15 min           │ Average  │ min(pve.node.cpu,15m)>85        │
│ RAM nodo > 95%                      │ High     │ last(pve.node.mem)>95           │
│ RAM nodo > 90%                      │ Average  │ last(pve.node.mem)>90           │
│ Storage > 90%                       │ High     │ last(pve.storage.usage)>90      │
│ Storage > 80%                       │ Average  │ last(pve.storage.usage)>80      │
│ Cluster quorum perso                │ Disaster │ last(pve.cluster.quorate)="No"  │
│ Ceph non HEALTH_OK                  │ High     │ last(pve.ceph.health)<>"OK"     │
│ OSD down                            │ High     │ last(pve.ceph.osd.up)<          │
│                                     │          │ last(pve.ceph.osd.total)        │
│ VM critica down                     │ High     │ last(pve.vm.status[100])=0      │
│ Load average elevato                │ Average  │ last(system.cpu.load)>nodi_cpu  │
│ Swap in uso                         │ Warning  │ last(system.swap.size[used])>0  │
│ Disco root < 10% libero             │ High     │ last(vfs.fs.pused[/])>90        │
└─────────────────────────────────────┴──────────┴─────────────────────────────────┘
```

### Configurazione Trigger in Zabbix

Nella web interface di Zabbix, navigare a **Configuration → Templates → Proxmox VE → Triggers** e creare i seguenti trigger:

```
Nome: Proxmox Node - CPU usage is too high
Severity: High
Expression: min(/Proxmox VE by Agent/pve.node.cpu,5m)>95
Recovery expression: max(/Proxmox VE by Agent/pve.node.cpu,5m)<90
Tags: scope:performance, component:cpu

Nome: Proxmox Node - Memory usage is too high
Severity: High
Expression: last(/Proxmox VE by Agent/pve.node.mem)>95
Recovery expression: last(/Proxmox VE by Agent/pve.node.mem)<90
Tags: scope:performance, component:memory

Nome: Proxmox Cluster - Quorum lost
Severity: Disaster
Expression: last(/Proxmox VE by Agent/pve.cluster.quorate)<>"Yes"
Tags: scope:availability, component:cluster

Nome: Proxmox Ceph - Health degraded
Severity: High
Expression: last(/Proxmox VE by Agent/pve.ceph.health)<>"HEALTH_OK"
Recovery expression: last(/Proxmox VE by Agent/pve.ceph.health)="HEALTH_OK"
Tags: scope:availability, component:ceph
```

---

## Auto-Discovery delle VM in Zabbix

### Regole LLD (Low-Level Discovery)

La discovery automatica delle VM permette a Zabbix di creare automaticamente item, trigger e grafici per ogni macchina virtuale nel cluster Proxmox.

```
Configurazione Discovery Rule in Zabbix:
1. Configuration → Templates → Proxmox VE → Discovery rules → Create
2. Nome: Discovery VM Proxmox
3. Type: Zabbix agent
4. Key: pve.vm.discovery
5. Update interval: 1h
6. Keep lost resources period: 7d

Item prototypes:
- pve.vm.cpu[{#VMID}]      → CPU usage VM {#VMNAME}
- pve.vm.mem.pct[{#VMID}]  → Memory usage VM {#VMNAME}
- pve.vm.uptime[{#VMID}]   → Uptime VM {#VMNAME}
- pve.ha.status[{#VMID}]   → HA Status VM {#VMNAME}

Trigger prototypes:
- VM {#VMNAME} CPU > 90%:
  Expression: min(/template/pve.vm.cpu[{#VMID}],10m)>90

- VM {#VMNAME} down:
  Expression: last(/template/pve.vm.uptime[{#VMID}])=0

Graph prototypes:
- VM {#VMNAME} Performance:
  Items: pve.vm.cpu[{#VMID}], pve.vm.mem.pct[{#VMID}]
```

### Script Discovery Avanzato

```bash
#!/bin/bash
# pve-discovery-vm.sh - Script di discovery per Zabbix LLD

# Ottenere la lista VM con dettagli
pvesh get /nodes/$(hostname)/qemu --output-format json 2>/dev/null | python3 -c "
import json, sys

data = json.load(sys.stdin)
discovery = {'data': []}

for vm in data:
    # Escludere i template
    if vm.get('template', 0) == 1:
        continue

    item = {
        '{#VMID}': str(vm.get('vmid', '')),
        '{#VMNAME}': vm.get('name', ''),
        '{#VMSTATUS}': vm.get('status', ''),
        '{#VMCPUS}': str(vm.get('cpus', 0)),
        '{#VMMAXMEM}': str(vm.get('maxmem', 0)),
        '{#VMMAXDISK}': str(vm.get('maxdisk', 0)),
        '{#VMTAGS}': vm.get('tags', ''),
        '{#VMNODE}': '$(hostname)'
    }
    discovery['data'].append(item)

print(json.dumps(discovery, indent=2))
"
```

---

## Dashboard Zabbix per Proxmox

### Creazione della Dashboard Principale

Nella web interface di Zabbix, navigare a **Dashboards → Create dashboard** e aggiungere i seguenti widget:

```
Layout Dashboard "Proxmox VE Overview":
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Nodi Online  │  │ VM Running   │  │ CT Running   │            │
│  │ [Single Stat]│  │ [Single Stat]│  │ [Single Stat]│            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ CPU Usage per Nodo                              [Graph]      │ │
│  │ pve-node01: ████████████░░░ 78%                              │ │
│  │ pve-node02: ██████████░░░░░ 65%                              │ │
│  │ pve-node03: ████████████████ 92%                             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────┐ ┌────────────────────────────┐ │
│  │ Memory Usage                 │ │ Storage Usage              │ │
│  │ [Graph - Time series]        │ │ [Pie chart]                │ │
│  │                              │ │                            │ │
│  └──────────────────────────────┘ └────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Top 10 VM per CPU Usage                      [Top hosts]     │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Problemi Attivi                              [Problems]       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Widget Specifici

```
Widget: Host Availability
- Type: Host availability
- Host groups: Proxmox Nodes

Widget: Problems
- Type: Problems
- Host groups: Proxmox Nodes, Proxmox VMs
- Show: Recent problems
- Severity: Warning, Average, High, Disaster

Widget: Graph - CPU Usage
- Type: Graph (classic)
- Items: pve.node.cpu per ogni nodo
- Time period: Last 24 hours

Widget: Data Overview
- Type: Data overview
- Host groups: Proxmox Nodes
- Items: pve.vm.running, pve.ct.running, pve.ceph.health
```

---

## Confronto con l'Integrazione VMware di Zabbix

### Migrazione da Zabbix+VMware a Zabbix+Proxmox

Se l'organizzazione utilizzava già Zabbix per monitorare VMware, la transizione a Proxmox richiede la sostituzione dei template VMware con quelli Proxmox:

```
Mapping Template VMware → Proxmox:
┌────────────────────────────────┬───────────────────────────────────┐
│ Template VMware (Zabbix)       │ Equivalente Proxmox               │
├────────────────────────────────┼───────────────────────────────────┤
│ VMware FQDN                    │ Proxmox VE by HTTP / by Agent     │
│ VMware Guest                   │ Proxmox VM by Agent               │
│ VMware Hypervisor              │ Proxmox Node by Agent + OS Linux  │
│ VMware Datastore               │ Proxmox Storage by Agent          │
│ VMware vCenter                 │ Proxmox Cluster by HTTP           │
│ VMware SD (Simple Check)       │ Proxmox VM Discovery              │
└────────────────────────────────┴───────────────────────────────────┘

Funzionalità VMware Zabbix vs Proxmox Zabbix:
┌──────────────────────────┬──────────────┬───────────────┐
│ Funzionalità             │ VMware       │ Proxmox       │
├──────────────────────────┼──────────────┼───────────────┤
│ Discovery automatico VM  │ Nativo       │ User Param/API│
│ Discovery datastore      │ Nativo       │ User Param/API│
│ CPU/RAM monitoring       │ Nativo       │ Agent+API     │
│ Disk I/O                 │ Nativo       │ Node exporter │
│ Network I/O              │ Nativo       │ Node exporter │
│ Snapshot monitoring      │ Nativo       │ Custom script │
│ HA status                │ Limitato     │ Custom script │
│ Storage cluster          │ vSAN nativo  │ Ceph custom   │
│ Template maturity        │ Molto maturo │ In crescita   │
│ Complessità setup        │ Bassa        │ Media         │
└──────────────────────────┴──────────────┴───────────────┘
```

### Procedura di Migrazione dei Template

```bash
# 1. Esportare la lista degli host VMware monitorati
# In Zabbix: Configuration → Hosts → Filter by group "VMware" → Export

# 2. Mappare ogni host VMware al corrispondente Proxmox
# Creare un file di mappatura CSV
cat > /tmp/vm_mapping.csv << 'EOF'
vmware_name,proxmox_vmid,proxmox_node,proxmox_name
webserver-01,100,pve-node01,webserver-01
database-01,101,pve-node02,database-01
app-server-01,102,pve-node01,app-server-01
EOF

# 3. Script per aggiornare gli host in Zabbix via API
python3 << 'PYTHON'
import json
import csv
import urllib.request

ZABBIX_URL = "http://zabbix-server.local:8080/api_jsonrpc.php"
ZABBIX_TOKEN = "your-api-token"

def zabbix_api(method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": ZABBIX_TOKEN,
        "id": 1
    }
    req = urllib.request.Request(
        ZABBIX_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    response = urllib.request.urlopen(req)
    return json.loads(response.read())["result"]

# Leggere la mappatura
with open("/tmp/vm_mapping.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(f"Aggiornamento: {row['vmware_name']} → {row['proxmox_name']}")
        # Qui andrebbero le chiamate API per aggiornare i template
        # e le configurazioni degli host in Zabbix

print("Migrazione template completata")
PYTHON
```

---

## Best Practice e Raccomandazioni

### Architettura Consigliata

```
Architettura Zabbix per Proxmox Cluster:
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐            │
│  │ pve-node01 │   │ pve-node02 │   │ pve-node03 │            │
│  │ Agent2     │   │ Agent2     │   │ Agent2     │            │
│  │ SNMP       │   │ SNMP       │   │ SNMP       │            │
│  └──────┬─────┘   └──────┬─────┘   └──────┬─────┘            │
│         │                │                │                    │
│         └────────────────┼────────────────┘                    │
│                          │                                     │
│                   ┌──────▼──────┐                              │
│                   │   Zabbix    │                              │
│                   │   Server    │                              │
│                   │  + Frontend │                              │
│                   │  + DB       │                              │
│                   └─────────────┘                              │
│                                                                │
│  Per cluster più grandi, usare Zabbix Proxy:                  │
│                                                                │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐      │
│  │ Site A   │────▶│ Zabbix Proxy │────▶│ Zabbix       │      │
│  │ 10 nodi  │     │ Locale       │     │ Server       │      │
│  └──────────┘     └──────────────┘     │ Centrale     │      │
│  ┌──────────┐     ┌──────────────┐     │              │      │
│  │ Site B   │────▶│ Zabbix Proxy │────▶│              │      │
│  │ 5 nodi   │     │ Locale       │     └──────────────┘      │
│  └──────────┘     └──────────────┘                            │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Checklist di Implementazione

1. Installare il server Zabbix su una VM dedicata (non su un nodo Proxmox)
2. Installare Zabbix Agent 2 su ogni nodo Proxmox
3. Configurare i user parameters personalizzati per Proxmox
4. Creare un utente API Proxmox dedicato al monitoraggio
5. Importare o creare i template specifici per Proxmox
6. Configurare le regole di discovery per VM e container
7. Impostare i trigger con soglie appropriate
8. Configurare le azioni di notifica (email, Slack, ecc.)
9. Creare le dashboard operative
10. Documentare le procedure di escalation
11. Testare gli alert con scenari simulati
12. Pianificare la revisione periodica delle soglie

---

## Conclusioni

Zabbix offre una soluzione di monitoraggio completa e matura per Proxmox VE, particolarmente adatta a organizzazioni che già lo utilizzano per il monitoraggio dell'infrastruttura. La migrazione da un setup Zabbix+VMware a Zabbix+Proxmox è un processo strutturato che richiede la sostituzione dei template e la configurazione degli agent, ma che mantiene la continuità operativa e le competenze del team.

La combinazione di Zabbix Agent, monitoraggio SNMP e accesso API REST fornisce una copertura completa delle metriche Proxmox, con capacità di auto-discovery, alerting avanzato e dashboard integrate che soddisfano le esigenze di ambienti enterprise.

---

## Esercizi

1. **Concettuale — alert design.** Per un cluster Proxmox a 5 nodi: definisci 10 alert essenziali con severity, soglia, action. Esempio: "Cluster lost quorum (severity disaster, escalate to on-call)".
2. **Lab — Zabbix + Proxmox API integration.** Deploy Zabbix Server + Agent su nodi Proxmox; importare il template community "Proxmox VE by HTTP"; validare metriche di cluster + alert basici.
3. **Stretch — confronto Zabbix vs Prometheus.** Sullo stesso cluster, deploy parallelo Zabbix e Prometheus + Grafana; raccogliere stesse metriche; confrontare overhead, learning curve, flessibilita.

## Auto-valutazione

1. Differenza tra Zabbix Agent passive e active.
2. Cos'e Zabbix Proxy e quando usarlo?
3. Auto-discovery LLD: cosa fa?
4. Alert fatigue: come prevenirla?
5. Zabbix vs Prometheus: 2 differenze chiave architettura.

## Letture primarie consigliate

- Zabbix Documentation — Manual. https://www.zabbix.com/documentation/current/en/manual (retrieved 2026-04-27).
- Proxmox VE by HTTP — Zabbix template repository. https://github.com/zabbix/community-templates (retrieved 2026-04-27).
- Prometheus Documentation. https://prometheus.io/docs/ (retrieved 2026-04-27).
- VMware Aria Operations (per confronto). https://www.vmware.com/products/aria-operations.html (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 10.1 — `../10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/ha-manager-regole-e-gruppi.md`: alert su HA state.
- Modulo 12.3 — `../12-SICUREZZA-E-COMPLIANCE/sicurezza-compliance.md`: audit forward a SIEM.
- Modulo 17.x — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/`: troubleshooting con dati monitoring.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Zabbix Server** | Componente principale: gestisce DB, frontend, scheduler. |
| **Zabbix Proxy** | Componente intermedio per ridurre carico server. |
| **Zabbix Agent** | Daemon su host monitorato; raccoglie metriche locali. |
| **Active check** | Agent push verso server (porta 10051). |
| **Passive check** | Server pull dall'agent (porta 10050). |
| **Trigger** | Condizione che attiva un alert. |
| **Action** | Cosa fare quando trigger fira (notify, escalate, exec). |
| **LLD (Low-Level Discovery)** | Auto-discovery dinamica di entita (interfacce, dischi, VM). |
| **Template** | Insieme riusabile di items + triggers + graphs. |
| **Maintenance window** | Finestra di silence per alert. |
| **Severity Zabbix** | Not classified, Information, Warning, Average, High, Disaster. |
| **Prometheus** | Alternative monitoring stack pull-based. |
| **Alertmanager** | Componente Prometheus per routing/grouping alert. |
