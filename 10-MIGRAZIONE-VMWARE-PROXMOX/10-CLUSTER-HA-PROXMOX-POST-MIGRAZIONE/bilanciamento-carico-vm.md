# Bilanciamento del Carico delle VM nel Cluster

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 4 — Cluster HA post-migrazione · Modulo 10.4 (chiude la sezione cluster-HA, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 10.1-10.3 (HA Manager, live migration, fencing); concetti generali di scheduling, capacity planning; familiarita Prometheus + Grafana per monitoring; bash/python per automazione.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. valutare il **carico di un cluster Proxmox** lungo dimensioni multiple (CPU%, RAM allocata vs available, IOPS storage backend, network usage) e identificare squilibri attesi vs critici;
> 2. applicare strategie di **placement iniziale** (al deployment di nuove VM) per minimizzare lo squilibrio: round-robin, weighted by capacity, affinita per workload type, anti-affinita per ridondanza;
> 3. eseguire **rebalancing manuale** via `qm migrate --online` quando sbilanciato, scegliendo VM da migrare in base a impatto (RAM piccola, dirty rate basso, no SLA stretto);
> 4. usare strumenti community (es. **proxmox-load-balancer**, **ProxLB**, hookscript custom) come surrogato di vSphere DRS, valutando trade-off (semplicita vs autonomia);
> 5. definire **policy di anti-affinita** via gruppi HA separati (es. due DB primary+replica su nodi diversi, due web frontend su nodi diversi);
> 6. monitorare il bilanciamento con dashboard Prometheus/Grafana (heatmap utilizzo per nodo, alert su sbilanciamento prolungato);
> 7. confrontare Proxmox manual rebalancing con vSphere DRS automation: cosa Proxmox *non* fa nativamente, e perche per molti deployment la mancanza di DRS automatico non e critica.
> **Tempo stimato:** lettura 50-70 min · lab 240-300 min (cluster + dashboard + script rebalancing)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; Prometheus 2.x + node_exporter; Grafana 10.x; ProxLB / proxmox-load-balancer (community).

## Mappa concettuale

```
+============================================================+
|     Load balancing Proxmox: pipeline e decision tree       |
+============================================================+
|                                                            |
|   1. RACCOGLI METRICHE (Prometheus + node_exporter)        |
|      - CPU% per nodo (5min avg)                            |
|      - RAM allocata vs available                           |
|      - IOPS storage (per device)                           |
|      - Network (rx/tx per NIC)                             |
|      - Numero VM running per nodo                          |
|                                                            |
|   2. CALCOLA SQUILIBRIO                                    |
|      - dev_std(cpu_pct_per_nodo)                           |
|      - max_load - min_load                                 |
|      - threshold: > 30% delta = sbilanciato                |
|                                                            |
|   3. DECISIONE                                             |
|                                                            |
|        +---------------------------+                       |
|        | Squilibrio > soglia?      |                       |
|        +---------------------------+                       |
|              |              |                              |
|              No             Si                             |
|              |              |                              |
|              v              v                              |
|        [No action]    +-------------+                      |
|                       | Identifica  |                      |
|                       | candidate   |                      |
|                       | VM e target |                      |
|                       +-------------+                      |
|                              |                             |
|                              v                             |
|                       +-------------+                      |
|                       | Live migr.  |                      |
|                       | qm migrate  |                      |
|                       | --online    |                      |
|                       +-------------+                      |
|                                                            |
|   4. SELEZIONE CANDIDATE VM                                |
|      - RAM piccola (downtime piu breve)                    |
|      - Dirty rate basso (converge piu facile)              |
|      - No SLA "no migration" tag                           |
|      - Non in gruppo restricted al solo nodo source        |
|                                                            |
|   5. SELEZIONE TARGET NODE                                 |
|      - Capacity disponibile (CPU + RAM + storage)          |
|      - Stesso storage pool (per shared) o stesso          |
|        replication group (per ZFS replicated)              |
|      - No anti-affinity con altre VM gia li                |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   STRATEGIE DI PLACEMENT INIZIALE                          |
|                                                            |
|   Round-robin     prossimo nodo nel ciclo                  |
|   Capacity-based  nodo con piu RAM/CPU disponibile         |
|   Affinity        VM stesso tipo sullo stesso nodo (cache  |
|                   warmup, locality)                        |
|   Anti-affinity   VM critiche su nodi diversi (HA)         |
|   Storage-locality VM su nodi che hanno il volume locale   |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Proxmox non e DRS, e non deve esserlo per la maggior parte dei deployment.** vSphere DRS migra continuamente, anche per piccoli squilibri. Per cluster di 3-10 nodi con ~50-100 VM, un rebalancing settimanale e sufficiente; ottimizzazione costante e overkill.
2. **Il monitoring e il vero strumento di bilanciamento.** Non si puo bilanciare cio che non si misura. Prima di automatizzare, configurare Prometheus + Grafana con heatmap per nodo, alert su delta prolungato, e visibilita storica.
3. **Il rebalancing migliore avviene al placement iniziale.** Pianificare bene quale nodo ospita quale VM al momento del deployment evita 90% del lavoro di rebalancing. Usare placement script o policy in fase di deploy automation (Ansible, Terraform).
4. **DRS automation richiede fiducia.** ProxLB e proxmox-load-balancer sono progetti community che funzionano, ma muovere VM senza supervisione richiede che tu ti fidi della logica del tool. Per produzione critica: testare il tool in lab per settimane prima di abilitare in prod.
5. **Anti-affinita via gruppi separati funziona, ma richiede manutenzione.** Aggiungere una nuova VM critica significa configurare gruppo + priorita + restricted con cura. Documentare la policy di anti-affinity nei runbook, non solo nei file di config.

---

## Introduzione

Il bilanciamento del carico delle macchine virtuali (VM load balancing) e il processo di distribuzione ottimale dei workload tra i nodi del cluster per massimizzare l'utilizzo delle risorse, evitare colli di bottiglia e garantire performance prevedibili.

A differenza di VMware vSphere, dove DRS (Distributed Resource Scheduler) effettua automaticamente il bilanciamento migrando le VM tra gli host, Proxmox VE non include un meccanismo DRS nativo. Questo richiede un approccio piu consapevole da parte dell'amministratore, basato su monitoraggio attivo, strategie di placement e, opzionalmente, script di automazione.

---

## Perche il Bilanciamento e Importante

### Scenari di Sbilanciamento

```
SCENARIO: Cluster sbilanciato dopo migrazione da VMware

+------------------+    +------------------+    +------------------+
|     Nodo 1       |    |     Nodo 2       |    |     Nodo 3       |
+------------------+    +------------------+    +------------------+
| CPU: 92%         |    | CPU: 15%         |    | CPU: 25%         |
| RAM: 88% (225GB) |    | RAM: 30% (77GB)  |    | RAM: 35% (90GB)  |
| VM: 25           |    | VM: 8            |    | VM: 10           |
| I/O: saturo      |    | I/O: idle        |    | I/O: basso       |
+------------------+    +------------------+    +------------------+

Problemi:
- Nodo 1 sovraccarico: performance degradate per tutte le VM
- Nodi 2/3 sottoutilizzati: spreco di risorse
- Se Nodo 1 cade: impossibile ospitare tutte le VM su 2 nodi
- Nessuna capacita N-1 effettiva
```

```
SCENARIO: Cluster bilanciato (obiettivo)

+------------------+    +------------------+    +------------------+
|     Nodo 1       |    |     Nodo 2       |    |     Nodo 3       |
+------------------+    +------------------+    +------------------+
| CPU: 45%         |    | CPU: 40%         |    | CPU: 42%         |
| RAM: 55% (141GB) |    | RAM: 50% (128GB) |    | RAM: 48% (123GB) |
| VM: 15           |    | VM: 14           |    | VM: 14           |
| I/O: moderato    |    | I/O: moderato    |    | I/O: moderato    |
+------------------+    +------------------+    +------------------+

Vantaggi:
- Performance uniformi per tutte le VM
- Capacita N-1 garantita (ogni nodo ha margine)
- Manutenzione possibile su qualsiasi nodo
- Headroom per picchi di carico
```

---

## Monitoraggio delle Risorse per Nodo

### Comandi CLI per il Monitoraggio

```bash
# ============================================================
# Stato di tutti i nodi del cluster
# ============================================================

# Panoramica risorse per nodo
pvesh get /cluster/resources --type node --output-format json | \
    python3 -c "
import sys, json
nodes = json.loads(sys.stdin.read())
print(f'{'Nodo':<10} {'CPU%':<8} {'RAM Usata':<12} {'RAM Tot':<12} {'RAM%':<8} {'Uptime':<10}')
print('-' * 62)
for n in sorted(nodes, key=lambda x: x['node']):
    cpu = n.get('cpu', 0) * 100
    mem_used = n.get('mem', 0) / 1073741824
    mem_total = n.get('maxmem', 0) / 1073741824
    mem_pct = (n.get('mem', 0) / n.get('maxmem', 1)) * 100
    uptime_h = n.get('uptime', 0) / 3600
    print(f'{n[\"node\"]:<10} {cpu:<8.1f} {mem_used:<12.1f}GB {mem_total:<12.1f}GB {mem_pct:<8.1f} {uptime_h:<10.0f}h')
"

# ============================================================
# Dettaglio VM per ogni nodo
# ============================================================

# Elenco VM con risorse per nodo
for node in pve1 pve2 pve3; do
    echo "=== $node ==="
    pvesh get /nodes/$node/qemu --output-format json 2>/dev/null | \
        python3 -c "
import sys, json
vms = json.loads(sys.stdin.read())
total_cpu = 0
total_mem = 0
for vm in sorted(vms, key=lambda x: -x.get('mem',0)):
    cpu = vm.get('cpus', 0)
    mem = vm.get('maxmem', 0) / 1073741824
    status = vm.get('status', 'unknown')
    name = vm.get('name', 'N/A')
    total_cpu += cpu
    total_mem += mem
    if status == 'running':
        print(f'  VM {vm[\"vmid\"]:<6} {name:<25} vCPU:{cpu:<3} RAM:{mem:.0f}GB  [{status}]')
print(f'  --- Totale: {total_cpu} vCPU, {total_mem:.0f} GB RAM ---')
"
    echo ""
done

# ============================================================
# Monitoraggio in tempo reale
# ============================================================

# CPU e RAM di un nodo specifico
pvesh get /nodes/pve1/status --output-format json | \
    python3 -c "
import sys, json
d = json.loads(sys.stdin.read())
cpu = d.get('cpu', 0) * 100
mem = d['memory']
print(f'CPU: {cpu:.1f}%')
print(f'RAM: {mem[\"used\"]/1073741824:.1f} / {mem[\"total\"]/1073741824:.1f} GB ({mem[\"used\"]/mem[\"total\"]*100:.1f}%)')
print(f'Load: {d.get(\"loadavg\", [\"N/A\"])}')
print(f'Uptime: {d.get(\"uptime\",0)/3600:.0f} ore')
"

# Monitoraggio continuo con watch
watch -n 5 'pvesh get /cluster/resources --type node 2>/dev/null | grep -E "cpu|mem|node"'
```

### Utilizzo dell'API per Dashboard Personalizzata

```bash
#!/bin/bash
# /usr/local/bin/cluster-dashboard.sh
# Dashboard testuale per il bilanciamento del cluster

clear
echo "======================================================================"
echo "         CLUSTER PROXMOX VE - DASHBOARD RISORSE"
echo "         $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================================"
echo ""

# Raccogliere dati da tutti i nodi
pvesh get /cluster/resources --type node --output-format json 2>/dev/null | \
python3 << 'PYEOF'
import sys, json

nodes = json.loads(sys.stdin.read())
nodes = sorted(nodes, key=lambda x: x['node'])

# Header
print(f"{'Nodo':<10} {'CPU':>6} {'RAM Usata':>10} {'RAM Tot':>10} {'RAM%':>6} {'VM':>4}")
print("-" * 56)

total_cpu = 0
total_mem_used = 0
total_mem_total = 0

for n in nodes:
    cpu = n.get('cpu', 0) * 100
    mem_used = n.get('mem', 0) / (1024**3)
    mem_total = n.get('maxmem', 0) / (1024**3)
    mem_pct = (n.get('mem', 0) / max(n.get('maxmem', 1), 1)) * 100

    # Indicatore visivo
    if cpu > 80 or mem_pct > 85:
        indicator = "!!"
    elif cpu > 60 or mem_pct > 70:
        indicator = "! "
    else:
        indicator = "  "

    total_cpu += cpu
    total_mem_used += mem_used
    total_mem_total += mem_total

    print(f"{n['node']:<10} {cpu:>5.1f}% {mem_used:>8.1f}GB {mem_total:>8.1f}GB {mem_pct:>5.1f}% {indicator}")

print("-" * 56)
avg_cpu = total_cpu / max(len(nodes), 1)
avg_mem = (total_mem_used / max(total_mem_total, 1)) * 100
print(f"{'Media':<10} {avg_cpu:>5.1f}% {total_mem_used:>8.1f}GB {total_mem_total:>8.1f}GB {avg_mem:>5.1f}%")

# Calcolo sbilanciamento
cpu_values = [n.get('cpu', 0) * 100 for n in nodes]
mem_values = [(n.get('mem', 0) / max(n.get('maxmem', 1), 1)) * 100 for n in nodes]

cpu_spread = max(cpu_values) - min(cpu_values)
mem_spread = max(mem_values) - min(mem_values)

print()
print(f"Sbilanciamento CPU: {cpu_spread:.1f}% (max-min)")
print(f"Sbilanciamento RAM: {mem_spread:.1f}% (max-min)")

if cpu_spread > 30 or mem_spread > 25:
    print(">> ATTENZIONE: Cluster significativamente sbilanciato!")
elif cpu_spread > 15 or mem_spread > 15:
    print(">> NOTA: Cluster moderatamente sbilanciato")
else:
    print(">> OK: Cluster ragionevolmente bilanciato")
PYEOF

echo ""
echo "======================================================================"
```

---

## Strategie di Placement Manuale

### Strategia 1: Round-Robin per Dimensione

Distribuire le VM in ordine decrescente di dimensione (RAM), assegnandole ai nodi a rotazione.

```bash
# Esempio di distribuzione round-robin:
# VM ordinate per RAM (decrescente):
#   VM 110: 32 GB (DB)
#   VM 111: 32 GB (DB replica)
#   VM 100: 16 GB (App Server 1)
#   VM 101: 16 GB (App Server 2)
#   VM 120: 8 GB (Web Server 1)
#   VM 121: 8 GB (Web Server 2)
#   VM 130: 4 GB (Monitoring)
#   VM 131: 4 GB (Backup proxy)
#   VM 140: 2 GB (DNS 1)
#   VM 141: 2 GB (DNS 2)

# Distribuzione round-robin:
# Nodo 1: VM 110 (32GB) + VM 101 (16GB) + VM 121 (8GB) + VM 131 (4GB) = 60 GB
# Nodo 2: VM 111 (32GB) + VM 100 (16GB) + VM 120 (8GB) + VM 130 (4GB) = 60 GB
# Nodo 3: VM 140 (2GB) + VM 141 (2GB) + headroom per failover          =  4 GB

# Script per calcolare la distribuzione ottimale:
cat > /usr/local/bin/plan-distribution.py << 'PYEOF'
#!/usr/bin/env python3
"""Pianifica la distribuzione ottimale delle VM tra i nodi"""

import json
import subprocess
import sys

def get_vms():
    """Raccoglie informazioni su tutte le VM del cluster"""
    result = subprocess.run(
        ['pvesh', 'get', '/cluster/resources', '--type', 'vm', '--output-format', 'json'],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def plan_distribution(vms, num_nodes=3, node_ram_gb=256):
    """Distribuisce le VM per bilanciare la RAM"""
    # Filtrare solo VM running
    running = [v for v in vms if v.get('status') == 'running' and v.get('type') == 'qemu']

    # Ordinare per RAM decrescente
    running.sort(key=lambda x: x.get('maxmem', 0), reverse=True)

    # Inizializzare i nodi
    nodes = {f'node{i+1}': {'vms': [], 'ram': 0, 'vcpu': 0} for i in range(num_nodes)}
    node_names = list(nodes.keys())

    # Algoritmo greedy: assegnare ogni VM al nodo con meno RAM allocata
    for vm in running:
        ram_gb = vm.get('maxmem', 0) / (1024**3)
        vcpu = vm.get('maxcpu', 0)

        # Trovare il nodo con meno RAM
        target = min(node_names, key=lambda n: nodes[n]['ram'])
        nodes[target]['vms'].append(vm)
        nodes[target]['ram'] += ram_gb
        nodes[target]['vcpu'] += vcpu

    # Stampare il piano
    print("\n=== PIANO DI DISTRIBUZIONE OTTIMALE ===\n")
    for name, data in nodes.items():
        pct = (data['ram'] / node_ram_gb) * 100
        print(f"{name}: {data['ram']:.0f} GB RAM ({pct:.0f}%), {data['vcpu']} vCPU, {len(data['vms'])} VM")
        for vm in data['vms']:
            print(f"  - VM {vm['vmid']:>5} ({vm.get('name','N/A'):<25}) "
                  f"RAM: {vm.get('maxmem',0)/(1024**3):.0f}GB  vCPU: {vm.get('maxcpu',0)}")
        print()

    # Verificare N-1
    max_ram = max(n['ram'] for n in nodes.values())
    remaining_capacity = (num_nodes - 1) * node_ram_gb
    total_ram = sum(n['ram'] for n in nodes.values())
    print(f"RAM totale allocata: {total_ram:.0f} GB")
    print(f"Capacita N-1: {remaining_capacity:.0f} GB")
    if total_ram <= remaining_capacity:
        print("OK: Capacita N-1 sufficiente")
    else:
        print(f"ATTENZIONE: Capacita N-1 INSUFFICIENTE! "
              f"Eccesso: {total_ram - remaining_capacity:.0f} GB")

if __name__ == '__main__':
    vms = get_vms()
    num_nodes = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    ram_per_node = int(sys.argv[2]) if len(sys.argv) > 2 else 256
    plan_distribution(vms, num_nodes, ram_per_node)
PYEOF

chmod +x /usr/local/bin/plan-distribution.py

# Eseguire:
# python3 /usr/local/bin/plan-distribution.py 3 256
```

### Strategia 2: Separazione per Tipo di Workload

```
+------------------------------------------------------------------+
|              SEPARAZIONE PER WORKLOAD                            |
+------------------------------------------------------------------+
|                                                                  |
|  Nodo 1: COMPUTE-INTENSIVE                                       |
|  +------------------------------------------------------+       |
|  | Application Server (CPU-bound)                        |       |
|  | Batch processing                                      |       |
|  | CI/CD runners                                         |       |
|  | Caratteristica: alto utilizzo CPU, RAM moderata       |       |
|  +------------------------------------------------------+       |
|                                                                  |
|  Nodo 2: MEMORY-INTENSIVE                                        |
|  +------------------------------------------------------+       |
|  | Database Server (PostgreSQL, MySQL)                   |       |
|  | Cache Server (Redis, Memcached)                       |       |
|  | Elasticsearch                                         |       |
|  | Caratteristica: alta RAM, CPU moderato                |       |
|  +------------------------------------------------------+       |
|                                                                  |
|  Nodo 3: I/O-INTENSIVE                                           |
|  +------------------------------------------------------+       |
|  | File Server                                           |       |
|  | Backup proxy                                          |       |
|  | Storage gateway                                       |       |
|  | Caratteristica: alto I/O disco, CPU/RAM moderati      |       |
|  +------------------------------------------------------+       |
|                                                                  |
+------------------------------------------------------------------+
```

### Strategia 3: Affinita e Anti-Affinita

```bash
# Anti-affinita: separare istanze ridondanti su nodi diversi

# Esempio: 2 web server su nodi diversi
# VM 100 (web1) -> Nodo 1
# VM 101 (web2) -> Nodo 2

# Implementazione tramite HA Groups:
ha-manager groupadd web-primary --nodes "pve1:3,pve2:1,pve3:1"
ha-manager groupadd web-secondary --nodes "pve2:3,pve3:1,pve1:1"

ha-manager add vm:100 --state started --group web-primary
ha-manager add vm:101 --state started --group web-secondary

# Affinita: tenere insieme VM che comunicano frequentemente
# VM 200 (app) e VM 201 (cache) sullo stesso nodo per latenza minima
ha-manager groupadd app-tier --nodes "pve1:3,pve2:1,pve3:1"
ha-manager add vm:200 --state started --group app-tier
ha-manager add vm:201 --state started --group app-tier
```

---

## Script per Bilanciamento Automatizzato via API

### Script di Bilanciamento Basato su RAM

```bash
#!/bin/bash
# /usr/local/bin/auto-balance.sh
# Script per suggerire e opzionalmente eseguire migrazioni di bilanciamento

THRESHOLD=20     # Soglia di sbilanciamento RAM in percentuale
DRY_RUN=true     # true = solo suggerimenti, false = esegue migrazioni
LOG="/var/log/auto-balance.log"

echo "$(date): Auto-balance check started" | tee -a $LOG

# Raccogliere dati dei nodi
NODE_DATA=$(pvesh get /cluster/resources --type node --output-format json 2>/dev/null)

# Calcolare lo sbilanciamento
BALANCE_INFO=$(echo "$NODE_DATA" | python3 << 'PYEOF'
import sys, json

nodes = json.loads(sys.stdin.read())
node_info = []

for n in nodes:
    if n.get('status') != 'online':
        continue
    mem_pct = (n.get('mem', 0) / max(n.get('maxmem', 1), 1)) * 100
    node_info.append({
        'name': n['node'],
        'mem_pct': mem_pct,
        'mem_free_gb': (n.get('maxmem', 0) - n.get('mem', 0)) / (1024**3),
        'cpu_pct': n.get('cpu', 0) * 100
    })

node_info.sort(key=lambda x: x['mem_pct'], reverse=True)
spread = node_info[0]['mem_pct'] - node_info[-1]['mem_pct']

for n in node_info:
    print(f"NODE:{n['name']}:MEM:{n['mem_pct']:.1f}:FREE:{n['mem_free_gb']:.1f}:CPU:{n['cpu_pct']:.1f}")
print(f"SPREAD:{spread:.1f}")
PYEOF
)

SPREAD=$(echo "$BALANCE_INFO" | grep "^SPREAD:" | cut -d: -f2)

echo "Sbilanciamento RAM: ${SPREAD}%" | tee -a $LOG

# Verificare se il bilanciamento e necessario
if (( $(echo "$SPREAD < $THRESHOLD" | bc -l) )); then
    echo "Cluster bilanciato (spread ${SPREAD}% < soglia ${THRESHOLD}%)" | tee -a $LOG
    exit 0
fi

echo "Bilanciamento necessario (spread ${SPREAD}% > soglia ${THRESHOLD}%)" | tee -a $LOG

# Identificare il nodo piu carico e quello meno carico
MOST_LOADED=$(echo "$BALANCE_INFO" | grep "^NODE:" | head -1 | cut -d: -f2)
LEAST_LOADED=$(echo "$BALANCE_INFO" | grep "^NODE:" | tail -1 | cut -d: -f2)

echo "Nodo piu carico: $MOST_LOADED" | tee -a $LOG
echo "Nodo meno carico: $LEAST_LOADED" | tee -a $LOG

# Trovare la VM migliore da migrare (quella che bilancerebbe meglio)
pvesh get /nodes/$MOST_LOADED/qemu --output-format json 2>/dev/null | \
python3 -c "
import sys, json
vms = json.loads(sys.stdin.read())
running = [v for v in vms if v.get('status') == 'running']
running.sort(key=lambda x: x.get('maxmem', 0))

# Trovare la VM che ridurrebbe maggiormente lo sbilanciamento
target_transfer = float('$SPREAD') / 2  # Obiettivo: dimezzare lo spread
for vm in running:
    mem_gb = vm.get('maxmem', 0) / (1024**3)
    print(f'CANDIDATE:vm:{vm[\"vmid\"]}:{vm.get(\"name\",\"N/A\")}:{mem_gb:.1f}GB')
" | while read -r line; do
    VMID=$(echo "$line" | cut -d: -f3)
    VMNAME=$(echo "$line" | cut -d: -f4)
    VMRAM=$(echo "$line" | cut -d: -f5)

    echo "Candidata: VM $VMID ($VMNAME) - $VMRAM" | tee -a $LOG

    if [ "$DRY_RUN" = "true" ]; then
        echo "DRY RUN: qm migrate $VMID $LEAST_LOADED --online" | tee -a $LOG
    else
        echo "Esecuzione: qm migrate $VMID $LEAST_LOADED --online" | tee -a $LOG
        qm migrate $VMID $LEAST_LOADED --online 2>&1 | tee -a $LOG
    fi
    break  # Migrare solo una VM per ciclo
done

echo "$(date): Auto-balance check completed" | tee -a $LOG
```

### Cron Job per Bilanciamento Periodico

```bash
# Eseguire il check di bilanciamento ogni ora
crontab -e

# Check bilanciamento ogni ora (solo suggerimenti)
0 * * * * /usr/local/bin/auto-balance.sh >> /var/log/auto-balance.log 2>&1

# Check bilanciamento con esecuzione automatica (solo in orari non critici)
# 0 3 * * * DRY_RUN=false /usr/local/bin/auto-balance.sh >> /var/log/auto-balance.log 2>&1
```

---

## Bilanciamento Basato sull'API REST Proxmox

### Script Python per Bilanciamento Avanzato

```python
#!/usr/bin/env python3
"""
/usr/local/bin/pve-balancer.py
Bilanciamento avanzato del cluster Proxmox VE via API REST

Uso: python3 pve-balancer.py [--execute] [--threshold 20]
"""

import argparse
import json
import subprocess
import sys
from collections import defaultdict


def api_get(path):
    """Chiama l'API locale di Proxmox"""
    result = subprocess.run(
        ['pvesh', 'get', path, '--output-format', 'json'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Errore API: {result.stderr}", file=sys.stderr)
        return None
    return json.loads(result.stdout)


def get_cluster_state():
    """Raccoglie lo stato completo del cluster"""
    nodes = {}
    resources = api_get('/cluster/resources')

    if not resources:
        return None

    for r in resources:
        if r['type'] == 'node' and r.get('status') == 'online':
            nodes[r['node']] = {
                'cpu_pct': r.get('cpu', 0) * 100,
                'mem_used': r.get('mem', 0),
                'mem_total': r.get('maxmem', 0),
                'mem_pct': (r.get('mem', 0) / max(r.get('maxmem', 1), 1)) * 100,
                'vms': []
            }
        elif r['type'] == 'qemu' and r.get('status') == 'running':
            node = r.get('node')
            if node:
                vm_info = {
                    'vmid': r['vmid'],
                    'name': r.get('name', 'N/A'),
                    'mem': r.get('maxmem', 0),
                    'cpu': r.get('maxcpu', 0),
                    'node': node
                }
                if node not in nodes:
                    nodes[node] = {'vms': [], 'mem_used': 0, 'mem_total': 0}
                nodes[node]['vms'].append(vm_info)

    return nodes


def calculate_migrations(nodes, threshold=20):
    """Calcola le migrazioni necessarie per bilanciare il cluster"""
    if not nodes or len(nodes) < 2:
        return []

    # Calcolare la RAM allocata (somma RAM VM) per nodo
    node_allocated = {}
    for name, data in nodes.items():
        allocated = sum(vm['mem'] for vm in data['vms'])
        node_allocated[name] = {
            'allocated_gb': allocated / (1024**3),
            'total_gb': data['mem_total'] / (1024**3),
            'pct': (allocated / max(data['mem_total'], 1)) * 100,
            'vms': data['vms']
        }

    # Calcolare media e spread
    pct_values = [d['pct'] for d in node_allocated.values()]
    avg_pct = sum(pct_values) / len(pct_values)
    spread = max(pct_values) - min(pct_values)

    print(f"\nStato attuale:")
    print(f"{'Nodo':<10} {'Allocata':<12} {'Totale':<12} {'%':<8} {'VM':<5}")
    print("-" * 47)
    for name, data in sorted(node_allocated.items()):
        print(f"{name:<10} {data['allocated_gb']:<12.1f} {data['total_gb']:<12.1f} "
              f"{data['pct']:<8.1f} {len(data['vms']):<5}")
    print(f"\nMedia: {avg_pct:.1f}%  |  Spread: {spread:.1f}%  |  Soglia: {threshold}%")

    if spread < threshold:
        print(f"\nCluster bilanciato (spread {spread:.1f}% < soglia {threshold}%)")
        return []

    # Identificare migrazioni
    migrations = []
    sorted_nodes = sorted(node_allocated.items(), key=lambda x: x[1]['pct'], reverse=True)

    source_name, source_data = sorted_nodes[0]
    target_name, target_data = sorted_nodes[-1]

    excess_gb = (source_data['pct'] - avg_pct) * source_data['total_gb'] / 100

    # Trovare la VM migliore da migrare
    candidates = sorted(source_data['vms'], key=lambda v: abs(v['mem']/(1024**3) - excess_gb))

    if candidates:
        best = candidates[0]
        migrations.append({
            'vmid': best['vmid'],
            'name': best['name'],
            'mem_gb': best['mem'] / (1024**3),
            'source': source_name,
            'target': target_name
        })

    return migrations


def main():
    parser = argparse.ArgumentParser(description='Bilanciamento cluster Proxmox VE')
    parser.add_argument('--execute', action='store_true', help='Eseguire le migrazioni')
    parser.add_argument('--threshold', type=float, default=20, help='Soglia sbilanciamento %')
    args = parser.parse_args()

    print("=" * 60)
    print("  PROXMOX VE CLUSTER BALANCER")
    print("=" * 60)

    nodes = get_cluster_state()
    if not nodes:
        print("Errore: impossibile ottenere lo stato del cluster")
        sys.exit(1)

    migrations = calculate_migrations(nodes, args.threshold)

    if not migrations:
        print("\nNessuna migrazione necessaria.")
        return

    print(f"\nMigrazioni suggerite:")
    for m in migrations:
        print(f"  VM {m['vmid']} ({m['name']}, {m['mem_gb']:.0f}GB): "
              f"{m['source']} -> {m['target']}")

    if args.execute:
        print("\nEsecuzione migrazioni...")
        for m in migrations:
            print(f"  Migrazione VM {m['vmid']} da {m['source']} a {m['target']}...")
            result = subprocess.run(
                ['qm', 'migrate', str(m['vmid']), m['target'], '--online'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  OK: VM {m['vmid']} migrata con successo")
            else:
                print(f"  ERRORE: {result.stderr}")
    else:
        print("\nPer eseguire: python3 pve-balancer.py --execute")


if __name__ == '__main__':
    main()
```

---

## Pianificazione delle Migrazioni di Manutenzione

### Procedura per Svuotare un Nodo

```bash
# Procedura step-by-step per manutenzione di un nodo

# 1. Verificare lo stato attuale
echo "=== Stato prima della manutenzione ==="
pvesh get /cluster/resources --type node
echo ""
echo "VM su pve1:"
qm list

# 2. Disabilitare l'HA per le VM che verranno migrate
# (opzionale ma raccomandato per evitare conflitti)
for vmid in $(qm list | awk 'NR>1 {print $1}'); do
    ha_state=$(ha-manager config 2>/dev/null | grep -A1 "^vm: $vmid" | grep state | awk '{print $2}')
    if [ -n "$ha_state" ]; then
        echo "Impostando VM $vmid in stato HA 'ignored'"
        ha-manager set vm:$vmid --state ignored
    fi
done

# 3. Migrare tutte le VM (bilanciando tra i nodi rimanenti)
TARGETS=("pve2" "pve3")
INDEX=0

for vmid in $(qm list | awk '/running/{print $1}'); do
    target=${TARGETS[$((INDEX % ${#TARGETS[@]}))]}
    echo "Migrazione VM $vmid -> $target"
    qm migrate $vmid $target --online
    INDEX=$((INDEX + 1))
done

# 4. Migrare i container
for ctid in $(pct list | awk 'NR>1 && /running/{print $1}'); do
    target=${TARGETS[$((INDEX % ${#TARGETS[@]}))]}
    echo "Migrazione CT $ctid -> $target"
    pct migrate $ctid $target --online
    INDEX=$((INDEX + 1))
done

# 5. Verificare che il nodo sia vuoto
echo ""
echo "=== Verifica nodo vuoto ==="
echo "VM rimanenti su pve1:"
qm list
echo "CT rimanenti su pve1:"
pct list

# 6. Il nodo e ora pronto per la manutenzione
echo ""
echo "Nodo pve1 pronto per la manutenzione"
```

---

## Confronto con VMware DRS

### Tabella Comparativa Dettagliata

```
+--------------------------------------------+-------------------------------------------+
| VMware DRS                                 | Proxmox VE                                |
+--------------------------------------------+-------------------------------------------+
| Bilanciamento automatico                   | Nessun bilanciamento automatico nativo    |
| Livelli: Manual, Partially, Fully Auto     | Solo manuale (script per automazione)     |
| Migration threshold (1-5)                  | Soglia personalizzabile via script        |
| CPU + RAM balancing                        | Script personalizzabili per qualsiasi     |
|                                            | metrica                                   |
| VM-VM affinity/anti-affinity rules         | Simulabile con HA Groups                  |
| VM-Host affinity rules                     | HA Groups restricted                      |
| DRS Groups (VM groups, Host groups)        | HA Groups                                 |
| Predictive DRS (vRealize)                  | Nessun equivalente                        |
| Network-aware placement                    | Non disponibile                           |
| Storage DRS (SDRS)                         | Non disponibile                           |
| DRS score e raccomandazioni                | Script personalizzati                     |
| Integration con vRealize Operations        | Integrazione con tool esterni (Grafana)   |
+--------------------------------------------+-------------------------------------------+
```

### Cosa si Perde Senza DRS

```
Funzionalita DRS critiche e workaround Proxmox:

1. Bilanciamento automatico
   VMware: DRS migra automaticamente le VM
   Proxmox: Script cron + monitoraggio
   Impatto: medio (la maggior parte dei cluster non necessita
            bilanciamento frequente)

2. Initial placement
   VMware: DRS sceglie il nodo ottimale per nuove VM
   Proxmox: L'operatore sceglie il nodo manualmente
   Impatto: basso (scelta manuale informata)

3. Maintenance mode
   VMware: DRS evacua automaticamente l'host
   Proxmox: Script di evacuazione manuale
   Impatto: basso (procedura documentata)

4. Predictive DRS
   VMware: Anticipa i picchi di carico
   Proxmox: Nessun equivalente
   Impatto: basso (utile solo per workload molto variabili)
```

---

## Tool della Community

### Proxmox VE Helper Scripts

```bash
# La community ha sviluppato diversi strumenti per il bilanciamento:

# 1. pve-cluster-rebalance (script della community)
# Repository: cerca "proxmox rebalance" su GitHub
# Funzionalita: suggerisce migrazioni per bilanciare RAM e CPU

# 2. Integrazione con Prometheus + Grafana
# Exportare metriche del cluster verso Prometheus
# Usare Grafana per la visualizzazione e alerting

# Installare pve-exporter per Prometheus:
pip3 install prometheus-pve-exporter

# Configurazione pve-exporter
cat > /etc/prometheus/pve.yml << 'EOF'
default:
    user: root@pam
    token_name: "prometheus"
    token_value: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    verify_ssl: false
EOF

# 3. Ansible per automazione
# Usare il modulo community.general.proxmox per gestire le VM
# Esempio playbook per bilanciamento:
# - name: Balance cluster
#   hosts: localhost
#   tasks:
#     - community.general.proxmox:
#         api_host: pve1
#         api_user: root@pam
#         api_token_id: ansible
#         api_token_secret: xxxx
#         vmid: 100
#         node: pve2
#         migrate: yes
```

---

## Workflow Pratico di Bilanciamento

### Procedura Settimanale Raccomandata

```
+------------------------------------------------------------------+
|        WORKFLOW SETTIMANALE DI BILANCIAMENTO                     |
+------------------------------------------------------------------+
|                                                                  |
| 1. LUNEDI MATTINA: Revisione dashboard                          |
|    - Controllare lo spread CPU e RAM tra i nodi                 |
|    - Identificare trend di crescita                             |
|    - Verificare capacita N-1                                    |
|                                                                  |
| 2. SE SBILANCIATO (spread > 20%):                               |
|    a. Identificare le VM candidate alla migrazione              |
|    b. Verificare le finestre di manutenzione                    |
|    c. Comunicare ai team applicativi (se necessario)            |
|    d. Eseguire le migrazioni in orari a basso traffico          |
|                                                                  |
| 3. DOPO LE MIGRAZIONI:                                          |
|    - Verificare che tutte le VM siano operative                 |
|    - Controllare il nuovo bilanciamento                         |
|    - Documentare le modifiche                                   |
|                                                                  |
| 4. VENERDI POMERIGGIO: Rapporto settimanale                    |
|    - Generare report di utilizzo risorse                        |
|    - Identificare VM sovra/sotto-dimensionate                   |
|    - Pianificare azioni per la settimana successiva             |
+------------------------------------------------------------------+
```

---

## Conclusioni

Il bilanciamento del carico in Proxmox VE richiede un approccio piu attivo rispetto a VMware DRS, ma offre il vantaggio di un controllo totale sulle decisioni di placement. La combinazione di monitoraggio regolare, script di automazione e procedure documentate permette di mantenere il cluster in uno stato ottimale.

Per la maggior parte degli ambienti, un bilanciamento settimanale o al bisogno e sufficiente. I workload tipici di un'azienda non cambiano drasticamente ogni ora, rendendo DRS un lusso piu che una necessita. L'importante e avere visibilita sullo stato delle risorse e procedure pronte per quando il bilanciamento diventa necessario.

La community Proxmox continua a sviluppare strumenti e script che colmano il gap con DRS. L'integrazione con sistemi di monitoraggio come Prometheus e Grafana offre una visibilita spesso superiore a quella del client vSphere, permettendo decisioni informate e tempestive.

---

## Approfondimenti — note del 2026-04-27

> **Approfondimento — ProxLB: DRS-like automation per Proxmox.** Progetto community attivo: [ProxLB on GitHub](https://github.com/gyptazy/ProxLB). Implementa balance automatico basato su CPU/RAM con threshold configurabili, dry-run mode per validare le decisioni prima di applicarle, esclusione di VM (tag-based o nome-based), supporto cluster fino a 32 nodi. Configurazione tipica: `/etc/proxlb/proxlb.yml` con `balanceness_cpu: 30`, `balanceness_memory: 25`, esecuzione via cron `*/30 * * * *`. Usa `qm migrate --online` come backend, quindi i requisiti di live migration (storage condiviso o ZFS replicated) si applicano. Trade-off: semplicita di setup vs autonomia: in produzione abilitare `--dry-run` per la prima settimana, esaminare le decisioni proposte, poi attivare l'esecuzione effettiva. Fonte: [ProxLB README](https://github.com/gyptazy/ProxLB), retrieved 2026-04-27.

> **Caso reale — Rebalancing settimanale via cron + script custom su cluster 6-nodi.** Setup adottato in produzione per ~80 VM su 6 nodi: (1) Prometheus raccoglie metriche; (2) script Python settimanale (eseguito ogni domenica notte) calcola lo squilibrio: `sum_cpu = sum(cpu_pct[node])`, `target = sum_cpu/n_nodes`, `imbalance[node] = cpu_pct[node] - target`; (3) per ogni nodo con imbalance > +20%, identifica VM "candidate" (RAM piccola, no DB tag); (4) per ogni VM, identifica il nodo "underloaded"; (5) esegue `qm migrate <VMID> <target> --online --bwlimit 100000`; (6) attende completamento, valida `qm status`, log su SIEM; (7) report email con riepilogo migrazioni. Risultato: cluster stabile in ±10% di carico per nodo, zero incidenti in 18 mesi. Lezione: l'automazione semplice "manualmente coadiuvata" (script + cron + monitoring) batte ogni giorno DRS automatico in produttivita per cluster medio-piccoli. Fonte: case study interno, riferimento metodologico [Prometheus alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/), retrieved 2026-04-27.

---

## Esercizi

1. **Concettuale — design placement policy.** Descrivi in 12-15 righe la policy di placement per un cluster a 4 nodi che deve ospitare: 10 VM web frontend (small, stateless), 4 VM DB (large, stateful, anti-affinity primary/replica), 6 VM Redis cache (medium, stateful), 8 VM batch worker (variable RAM, low priority). Indica per ognuna: criterio di placement iniziale, criterio di rebalancing, eventuali gruppi HA con anti-affinity.

2. **Lab — dashboard Grafana con heatmap nodi.** Creare una dashboard Grafana con: (a) heatmap CPU% per nodo (1 colonna per nodo, righe = ultimi 24h); (b) tabella RAM allocata vs available per nodo; (c) numero VM per nodo; (d) alert se delta CPU% tra nodo max e min > 30% per > 30 min. Esportare il JSON e documentare le query utilizzate.

3. **Stretch — script di rebalancing safe.** Scrivere uno script Python che: (1) legge metriche Prometheus per CPU/RAM per nodo; (2) calcola squilibrio; (3) propone una lista di migrazioni in formato `[{vmid, source, target, expected_impact}]`; (4) supporta modalita `--dry-run` (no execute) e `--apply` (esegue); (5) in modalita apply, esegue una migration alla volta, attende completion, valida health del cluster prima di passare alla successiva; (6) supporta lista di VM "exclude" (mai migrate); (7) emit report JSON con timeline.

## Auto-valutazione

1. Differenza fra placement iniziale e rebalancing operativo.
2. Perche Proxmox non implementa DRS automatico nativo e quando questo e un limite reale?
3. Quali metriche raccogliere per decidere se rebalanciare?
4. Anti-affinity in Proxmox: come si implementa via gruppi HA?
5. ProxLB: cos'e e quando usarlo?
6. Strategia di selezione VM "candidate" per migrazione: criteri principali.
7. Quale e il rischio di rebalancing automatico senza dry-run iniziale?

## Letture primarie consigliate

- ProxLB — DRS-like load balancer per Proxmox (community). https://github.com/gyptazy/ProxLB (retrieved 2026-04-27).
- Proxmox VE Admin Guide — Cluster Manager. https://pve.proxmox.com/pve-docs/chapter-pvecm.html (retrieved 2026-04-27).
- Prometheus — Best practices for instrumentation. https://prometheus.io/docs/practices/instrumentation/ (retrieved 2026-04-27).
- Grafana — Dashboard JSON model. https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/ (retrieved 2026-04-27).
- VMware vSphere DRS (per confronto). https://docs.vmware.com/en/VMware-vSphere/8.0/com.vmware.vsphere.resmgmt.doc/GUID-902B0DA5-DD0B-4E1A-8D62-BBF5DB1B2C40.html (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 10.1 — `ha-manager-regole-e-gruppi.md`: gruppi HA per anti-affinity.
- Modulo 10.2 — `live-migration-proxmox-interna.md`: migration come strumento di rebalancing.
- Modulo 13.x — `../13-MONITORAGGIO-E-OTTIMIZZAZIONE/zabbix-monitoraggio-proxmox.md`: monitoring del cluster e alert sbilanciamento.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Load balancing** | Distribuzione carico tra nodi del cluster. |
| **DRS (vSphere)** | Distributed Resource Scheduler; bilanciamento dinamico (assente in Proxmox nativo). |
| **Placement policy** | Regole per scegliere il nodo target al deploy di una nuova VM. |
| **Anti-affinity** | Regola: due VM specifiche *mai* sullo stesso nodo. |
| **Affinity** | Regola: due VM specifiche *sempre* sullo stesso nodo. |
| **ProxLB** | Tool community per balancing Proxmox stile-DRS. |
| **proxmox-load-balancer** | Altro tool community per balancing. |
| **Heatmap (Grafana)** | Visualizzazione 2D di metriche nel tempo per categoria. |
| **Threshold di sbilanciamento** | Delta % tra nodo max load e min load, oltre cui rebalanciare. |
| **Capacity reserve** | % di capacita lasciata libera per failover (tipicamente 1/N per cluster a N nodi). |
