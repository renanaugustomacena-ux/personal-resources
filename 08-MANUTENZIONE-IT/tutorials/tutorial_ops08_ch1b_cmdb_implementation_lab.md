# Tutorial: CMDB — Implementazione e Gestione con GLPI

> **Documento di riferimento:** `13-cmdb-glpi-snipeit-implementazione.md`
> **Dominio:** IT Operations — Configuration Management / CMDB
> **Ambito:** CMDB vs ITAM, modello CI e relazioni, service mapping, discovery automatizzata, federazione, GLPI 10/11 con GLPI Agent, Snipe-IT, API automation Python, qualità dati, impact analysis
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio (prerequisiti: ops08a completato, GLPI operativo)
> **Prerequisiti:** `tutorial_ops08_ch1a_asset_lifecycle_lab.md`, GLPI attivo su SRV-LINUX-01
> **Ambiente:** SRV-LINUX-01 (GLPI, script Python), DC-LAB-01 (Windows agent), WKS-LAB-01 (client)

---

## Lab Environment Setup

```bash
# Su SRV-LINUX-01 — verifica prerequisiti CMDB lab
echo "=== SETUP AMBIENTE CMDB LAB ==="

# GLPI attivo?
if curl -s --connect-timeout 5 http://localhost:8080/glpi 2>/dev/null | grep -qi "html"; then
    echo "[OK] GLPI raggiungibile"
else
    echo "[WARN] GLPI non attivo — avvia con: docker start glpi-app (o il tuo setup)"
fi

# Python per le esercitazioni API
python3 --version 2>/dev/null && echo "[OK] Python3 disponibile" || echo "[INFO] Python3 non trovato"
pip3 show requests 2>/dev/null | grep -q Name && echo "[OK] requests installato" || {
    echo "Installo requests..."
    pip3 install requests 2>/dev/null || pip install requests 2>/dev/null
}

# Struttura directory per il lab
mkdir -p /cmdb-lab/{scripts,exports,relationships}
echo "[OK] Directory /cmdb-lab pronta"
```

---

## PART A: FONDAMENTI — La Differenza tra "Avere un Inventario" e "Capire le Dipendenze"

> Immagina di gestire una città. Il catasto ti dice quanti edifici ci sono, dove si trovano, a chi appartengono. Ma non ti dice che se chiudi via Roma, 3 ospedali diventano inaccessibili, 12 scuole perdono il percorso dei pullman, e il mercato ortofrutticolo non riceve le forniture. Quella rete di dipendenze è la differenza tra un inventario (catasto) e un CMDB (mappa della città). Senza le relazioni, sai cosa c'è — non capisci cosa succede quando qualcosa si rompe.

---

### Concetto A1: CMDB vs ITAM — Due Domande Diverse

> **Analogia.** Un'azienda ha due tipi di documenti su ogni auto aziendale: il libretto di circolazione (dati legali e tecnici: targa, telaio, revisione, assicurazione — è dell'ITAM) e la carta che dice "questa auto è assegnata al direttore commerciale, percorre il tratto Milano-Roma il martedì mattina, porta il campionario di prodotti, e senza di essa il direttore non può fare il 30% delle visite clienti" (dipendenze operative — è del CMDB). Il CMDB risponde a domande operative; l'ITAM risponde a domande finanziarie.

```
CONFRONTO FONDAMENTALE:

  ASPETTO               CMDB                          ITAM
  ─────────────────────────────────────────────────────────────────
  Domanda chiave        "Cosa gestisco operativamente?" "Cosa possiedo?"
  Owner tipico          IT Operations                  IT Finance
  Unità base            Configuration Item (CI)        Asset
  Attributo principale  Relazioni tra CI               Costo, garanzia
  Aggiornamento         Continuo (ad ogni change)      Periodico (acquisti)
  Valore principale     Impact analysis                Audit licenze
  
  STESSO OGGETTO, DUE VISTE:
  
  Laptop Dell Mario Rossi — ITAM view:
    Acquisto: €1.230 (15/03/2024)
    Garanzia: ProSupport NBD, scade 15/03/2027
    Fornitore: Dell Italia
    Ammortamento: 3 anni → €410/anno
    
  Laptop Dell Mario Rossi — CMDB view:
    Hostname: IT-VND-MR01
    IP: 10.0.5.42, MAC: aa:bb:cc:dd:ee:ff
    OS: Windows 11 Pro 23H2
    Dipende da: AD (autenticazione), WSUS (aggiornamenti), VPN (accesso remoto)
    Usato da: utente Mario Rossi, reparto Commerciale
    Servizi erogati: CRM, Email, File Share Commerciale
    
  GLPI integra entrambe le viste nello stesso record.
  Snipe-IT è solo ITAM — per CMDB richiede integrazione esterna.
```

---

### Concetto A2: Il Modello CI e le Relazioni — il Cuore del CMDB

> **Analogia.** Un organigramma aziendale non è solo una lista di persone — è la rappresentazione delle relazioni gerarchiche e funzionali. "Chi riporta a chi", "chi dipende da chi per le approvazioni", "se il CEO è assente, chi ha l'autorità?". Il modello CI del CMDB è l'organigramma dell'infrastruttura IT: non solo "cosa esiste" ma "chi dipende da chi, chi ospita chi, chi gestisce chi".

**Classi di CI principali:**

```
HARDWARE:         Server, Switch, Router, Firewall, Workstation, Laptop,
                  UPS, Storage (NAS/SAN), Rack, PDU

SOFTWARE:         Sistema Operativo, Applicazione, Database Instance,
                  Web Service, Container, Container Image

VIRTUALIZZAZIONE: Hypervisor, Virtual Machine, Cluster, Resource Pool

RETE:             VLAN, Subnet, IP Address, Certificato SSL/TLS,
                  DNS Zone, Load Balancer

SERVIZI:          Business Service (es. "Gestione Ordini"),
                  Application Service, Technical Service

CONTRATTI:        Licenza Software, Contratto Manutenzione, SLA, Vendor

TIPOLOGIE DI RELAZIONI (direzionali!):

  depends on:   A non funziona senza B
                "App OrderMgmt depends on DB ORDERS_PROD"
                
  hosted on:    A risiede fisicamente/virtualmente su B
                "DB ORDERS_PROD hosted on VM db-prod-01"
                
  runs on:      A esegue su B (VM su hypervisor, container su node)
                "VM db-prod-01 runs on Hypervisor esx-prod-02"
                
  member of:    A è parte di B (cluster, pool)
                "esx-prod-02 member of Cluster ESX-PROD"
                
  connected to: A è connesso fisicamente/logicamente a B
                "SW-ACCESS-01 connected to SW-CORE-01"
                
  installed on: Software A installato su hardware B
                "Office 365 installed on Workstation IT-VND-MR01"
                
  used by:      A è consumato da B
                "Service Email used by All Departments"
```

---

### Concetto A3: Service Mapping — Dalla Tecnologia al Business

> **Analogia.** Quando in un condominio salta la corrente, l'amministratore deve sapere immediatamente: quali appartamenti sono colpiti? Quale impianto è guasto? Quale gestore ha la competenza? Il Service Mapping è la risposta del CMDB a questa domanda nell'IT: quando il server "db-prod-01" va down, l'IC (Incident Commander) vede in 10 secondi che questo blocca l'applicazione OrderMgmt, che eroga il servizio Gestione Ordini, che impatta il reparto Vendite e Logistica.

**Esempio concreto di mappa servizio:**

```
[Business Service: Gestione Ordini] ← criticità: ALTA
  │
  ├─ used by → [Reparto Vendite] + [Reparto Logistica]
  │
  ├─ depends on → [App: OrderMgmt v3.4]
  │               │
  │               ├─ hosted on → [VM: app-orders-prod-01]
  │               │              └─ runs on → [Hypervisor: esx-prod-02]
  │               │                            └─ member of → [Cluster: ESX-PROD]
  │               │
  │               ├─ depends on → [DB: ORDERS_PROD (PostgreSQL 14)]
  │               │               └─ hosted on → [VM: db-orders-prod-01]
  │               │                              └─ runs on → [esx-prod-02]
  │               │
  │               └─ depends on → [Service: Email (per notifiche)]
  │
  └─ SLA: RTO 2h, RPO 30min (Tier 1)

IMPATTO DI UN GUASTO A esx-prod-02:
  → VM app-orders-prod-01 DOWN
  → VM db-orders-prod-01 DOWN
  → App OrderMgmt DOWN
  → Business Service Gestione Ordini DOWN
  → Reparto Vendite e Logistica BLOCCATI
  
  Senza CMDB: "qualcosa non funziona" → investigation 30+ minuti
  Con CMDB:   IC vede il grafo in 30 secondi → escalation mirata
```

---

### Concetto A4: Discovery Automatica e Federazione

> **Analogia.** Un censimento nazionale non funziona se i funzionari vanno porta a porta a compilare schede a mano — troppo lento, troppo soggetto a errori, stantio non appena finito. I moderni censimenti usano combinazione di registrazioni automatiche (anagrafe, catasto, INPS) e campionamento manuale. Il CMDB funziona allo stesso modo: discovery automatica per la massa dei CI, federazione con sistemi specialistici, verifica manuale periodica.

```
TECNICHE DI DISCOVERY:

  Agent-based:
    FusionInventory Agent / GLPI Agent installato sul target
    Vantaggi: dati approfonditi, aggiornamento frequente
    Svantaggi: installazione su ogni endpoint
    Ideale per: server, workstation, laptop

  Agentless:
    WMI/WinRM per Windows: query dirette senza installazione
    SSH per Linux: login read-only, comandi remoti
    SNMP per dispositivi di rete: standard universale
    Ideale per: dispositivi senza OS gestibile (switch, printer)
    
  API Integration (Federazione):
    Active Directory → LDAP query per utenti e computer
    vCenter → API per VM e hypervisor
    AWS → Resource Graph per risorse cloud
    Azure → Azure Resource Graph
    Intune → Graph API per endpoint gestiti
    
FEDERAZIONE vs REPLICAZIONE:

  Anti-pattern (NO!): copiare tutti i dati in CMDB
    → duplicazione → divergenza → obsolescenza
    
  Pattern corretto (SÌ!): CMDB ha riferimento univoco al sistema
                           authoritative, non copia i dati
  
  Esempio:
    CMDB record: Computer "IT-VND-MR01"
      → AD reference: CN=IT-VND-MR01,OU=Computers,DC=azienda,DC=local
      → Intune Device ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    
    Quando serve info OS aggiornata → chiede all'AD
    Quando serve stato patch → chiede a Intune
    Non duplica quelle info in CMDB → non diverge mai
    
REGOLA D'ORO DEL CMDB:
  1.000 CI accurati > 10.000 CI con 30% obsoleti
  
  Scope iniziale: solo i 5-10 servizi business più critici
  Non cercare di censire tutto subito → swamp di dati inutili
```

---

### Concetto A5: GLPI — Lo Strumento del Lab

```
GLPI (Gestionnaire Libre de Parc Informatique)
  → open source GPL, nessun costo licenza
  → nativamente in italiano
  → copre: ITAM + CMDB + ticketing ITIL + contratti + KB
  → ampiamente usato in Italia (settore pubblico, PMI)
  
VERSIONI RILEVANTI (2026):
  GLPI 10.0.x → ancora supportata, usa FusionInventory plugin
  GLPI 11.0.x → nuova architettura, GLPI Agent nativo (consigliata)
  
CLASSI CI NATIVE IN GLPI:
  Computer (server, workstation, laptop, VM)
  Network Equipment (switch, router, firewall, AP)
  Printer
  Phone
  Monitor, Peripheral
  Software, Software License
  Rack, Enclosure, PDU
  Cluster, Domain, Certificate
  GenericObject (plugin) → classi custom (es. BusinessService, CloudInstance)

NAVIGAZIONE RAPIDA:
  Asset → Computer, Network Equipment, ecc.
  Configurazione → Topologia (grafo relazioni)
  Gestione → Analisi di impatto
  Plugin → CMDB (per plugin Infotel)
```

---

## PART B: OPERAZIONI — Costruire la CMDB del Lab

---

### Esercizio B1: Modellare i CI Principali in GLPI

**Obiettivo.** Creare i CI fondamentali dell'ambiente lab in GLPI, con attributi corretti e lo stato di ciascun sistema.

**Step 1 — Crea CI base via interfaccia GLPI:**

```bash
# Su SRV-LINUX-01

echo "=== MODELLAZIONE CI IN GLPI ==="
echo "URL: http://192.168.56.20:8080/glpi"
echo ""
echo "CI DA CREARE (in ordine):"
echo ""
cat << 'EOF'
1. LOCATION (prerequisito per CI):
   Asset → Locations → + Aggiungi
   Nome: "Data Center Lab"
   Nome: "Sala Uffici Lab"

2. CI SERVER — SRV-LINUX-01:
   Asset → Computer → + Aggiungi
   Nome:          SRV-LINUX-01
   Tipo:          Server
   Produttore:    VirtualBox (lab)
   Modello:       VM Ubuntu 22.04
   OS:            Ubuntu Server 22.04 LTS
   IP:            192.168.56.20
   Location:      Data Center Lab
   Stato:         In uso
   Criticità:     Alta (erogà GLPI, Prometheus, Grafana)
   Utente:        lab-admin
   
3. CI SERVER — DC-LAB-01:
   Nome:          DC-LAB-01
   Tipo:          Server
   OS:            Windows Server 2022
   Ruolo:         Domain Controller
   IP:            192.168.56.10
   Location:      Data Center Lab
   Stato:         In uso
   Criticità:     Critica (AD = Tier 1)
   
4. CI WORKSTATION — WKS-LAB-01:
   Asset → Computer → + Aggiungi
   Nome:          WKS-LAB-01
   Tipo:          Workstation
   OS:            Windows 10
   IP:            192.168.56.30
   Location:      Sala Uffici Lab
   Stato:         In uso
   Utente:        lab-user
EOF

echo ""
echo "Dopo la creazione, procedi con B2 (relazioni tra CI)."
```

**Step 2 — Aggiungi CI Software come Configuration Item:**

```bash
echo "=== CI SOFTWARE E SERVIZI ==="
echo ""
echo "In GLPI, i Software sono CI a loro volta:"
echo ""
cat << 'EOF'
Asset → Software → + Aggiungi

Software 1: GLPI
  Nome:     GLPI
  Produttore: Teclib'
  Versione corrente: 10.0.x
  Tipo licenza: Open Source
  Installato su: SRV-LINUX-01 (Tab "Installazioni")

Software 2: Prometheus
  Nome:     Prometheus
  Produttore: Prometheus Authors
  Versione: 2.x
  Installato su: SRV-LINUX-01

Software 3: Active Directory Domain Services
  Nome:     Active Directory DS
  Produttore: Microsoft
  Installato su: DC-LAB-01

COLLEGARE SOFTWARE A SERVER (relazione "installed on"):
  Apri record SRV-LINUX-01
  Tab "Software" → Aggiungi
  → Seleziona GLPI, Prometheus, Grafana, Uptime Kuma
EOF
```

**Step 3 — Verifica via API GLPI:**

```bash
# Su SRV-LINUX-01 — verifica CI creati via REST API

echo "=== VERIFICA CI VIA API GLPI ==="

# Ottieni token sessione
SESSION=$(curl -s -X GET \
    "http://localhost:8080/glpi/apirest.php/initSession" \
    -H "Authorization: user_token glpi" \
    -H "App-Token: glpi" \
    -H "Content-Type: application/json" 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_token','NOTOKEN'))" 2>/dev/null)

if [[ "$SESSION" != "NOTOKEN" && -n "$SESSION" ]]; then
    echo "[OK] Sessione API aperta: $SESSION"
    
    # Lista computer nel CMDB
    COMPUTERS=$(curl -s -X GET \
        "http://localhost:8080/glpi/apirest.php/Computer" \
        -H "Session-Token: $SESSION" \
        -H "App-Token: glpi" \
        -H "Content-Type: application/json" 2>/dev/null | \
        python3 -c "import sys,json; items=json.load(sys.stdin); [print(f'  [{i[\"id\"]}] {i[\"name\"]}') for i in items] if isinstance(items,list) else print('nessun risultato')" 2>/dev/null)
    
    echo ""
    echo "CI Computer nel CMDB:"
    echo "$COMPUTERS"
    
    # Chiudi sessione
    curl -s -X GET "http://localhost:8080/glpi/apirest.php/killSession" \
        -H "Session-Token: $SESSION" -H "App-Token: glpi" > /dev/null
else
    echo "[INFO] API GLPI non configurata o non raggiungibile"
    echo "Verifica manualmente in GLPI → Asset → Computer"
fi
```

**Checkpoint di verifica B1:**
- [ ] Location "Data Center Lab" e "Sala Uffici Lab" create
- [ ] CI SRV-LINUX-01 creato con IP, OS, criticità Alta
- [ ] CI DC-LAB-01 creato con criticità Critica
- [ ] CI WKS-LAB-01 creato
- [ ] Software GLPI e Prometheus collegati a SRV-LINUX-01

---

### Esercizio B2: Modellare le Relazioni e l'Analisi di Impatto

**Obiettivo.** Creare il grafo di dipendenze tra i CI del lab e testare l'analisi di impatto: "se DC-LAB-01 cade, cosa si ferma?"

**Step 1 — Modella le dipendenze:**

```bash
echo "=== MODELLAZIONE RELAZIONI CI ==="
echo ""
echo "MAPPA DIPENDENZE DEL LAB:"
echo ""
cat << 'MAPPA'
[DC-LAB-01 — Domain Controller]
  ← depends on ←  SRV-LINUX-01 (per DNS queries)
  → AD autentica → WKS-LAB-01 (login Windows)
  → AD autentica → SRV-LINUX-01 (LDAP auth per GLPI)

[SRV-LINUX-01 — App Server]
  → ospita → GLPI (Asset Management)
  → ospita → Prometheus (Monitoring)
  → ospita → Grafana (Dashboards)
  → ospita → Uptime Kuma (Synthetic monitoring)
  → ospita → MariaDB/MySQL (Database per GLPI)

[WKS-LAB-01 — Workstation]
  → dipende da → DC-LAB-01 (autenticazione)
  → accede a → GLPI su SRV-LINUX-01
  → accede a → Grafana su SRV-LINUX-01

SERVIZI BUSINESS (da modellare):
  [Service: IT Operations Lab]
    → depends on → GLPI (ticketing)
    → depends on → AD (autenticazione)
    → depends on → Prometheus+Grafana (monitoring)
MAPPA

echo ""
echo "IN GLPI — Configurazione Analisi di Impatto:"
echo ""
cat << 'EOF'
1. Apri record DC-LAB-01
2. Cerca tab "Impatto" o "Analisi di impatto"
   (richiede GLPI 10+ e sezione attivata in Configurazione)
3. Aggiungi dipendenza:
   DC-LAB-01 → [fornisce] → WKS-LAB-01 (autenticazione)
   DC-LAB-01 → [fornisce] → GLPI tramite SRV-LINUX-01 (LDAP)

ALTERNATIVA — Plugin CMDB Infotel:
  Installa plugin CMDB da Marketplace GLPI
  → Service objects, impact analysis estesa, icone CI custom
EOF
```

**Step 2 — Script Python per popolare relazioni via API:**

```python
#!/usr/bin/env python3
"""
glpi_populate_cmdb.py — Popola CI e relazioni GLPI via REST API
"""
import requests
import json
import sys

GLPI_URL = "http://localhost:8080/glpi"
APP_TOKEN = "glpi"
USER_TOKEN = "glpi"

def get_session_token():
    resp = requests.get(
        f"{GLPI_URL}/apirest.php/initSession",
        headers={
            "Authorization": f"user_token {USER_TOKEN}",
            "App-Token": APP_TOKEN,
            "Content-Type": "application/json"
        },
        timeout=10
    )
    resp.raise_for_status()
    return resp.json().get("session_token")

def api_request(method: str, endpoint: str, session: str, data: dict = None):
    headers = {
        "Session-Token": session,
        "App-Token": APP_TOKEN,
        "Content-Type": "application/json"
    }
    url = f"{GLPI_URL}/apirest.php/{endpoint}"
    
    if method == "GET":
        resp = requests.get(url, headers=headers, timeout=10)
    elif method == "POST":
        resp = requests.post(url, headers=headers, json={"input": data}, timeout=10)
    else:
        raise ValueError(f"Metodo non supportato: {method}")
    
    if resp.status_code not in (200, 201):
        print(f"  [WARN] {method} {endpoint}: HTTP {resp.status_code}")
        return None
    return resp.json()

def kill_session(session: str):
    requests.get(
        f"{GLPI_URL}/apirest.php/killSession",
        headers={"Session-Token": session, "App-Token": APP_TOKEN},
        timeout=5
    )

def main():
    print("=== POPOLAMENTO CMDB GLPI VIA API ===")
    
    try:
        session = get_session_token()
        print(f"[OK] Sessione API aperta")
    except Exception as e:
        print(f"[FAIL] Impossibile aprire sessione GLPI: {e}")
        print("       Verifica che GLPI sia attivo e le credenziali siano corrette")
        return 1
    
    try:
        # Verifica CI esistenti
        computers = api_request("GET", "Computer", session)
        if computers:
            print(f"[INFO] Computer presenti nel CMDB: {len(computers) if isinstance(computers, list) else 0}")
            if isinstance(computers, list):
                for c in computers:
                    print(f"  - [{c.get('id')}] {c.get('name', 'N/A')}")
        
        # Esempio: aggiorna commento su SRV-LINUX-01 (se esiste)
        # In produzione: qui crei CI mancanti, aggiungi relazioni, ecc.
        print("")
        print("[INFO] Per creare nuovi CI o relazioni via API:")
        print("  POST /Computer con dati del server")
        print("  Usa il campo 'comment' per note operative")
        print("  Usa 'NetworkPort' per aggiungere interfacce di rete")
        
        return 0
    
    finally:
        kill_session(session)
        print("[OK] Sessione API chiusa")

if __name__ == "__main__":
    sys.exit(main())
```

**Salva ed esegui:**

```bash
# Su SRV-LINUX-01

cat > /cmdb-lab/scripts/glpi_populate_cmdb.py << 'PYEOF'
# (contenuto dello script sopra)
PYEOF

# (in alternativa, crea il file manualmente con il contenuto Python)
python3 /cmdb-lab/scripts/glpi_populate_cmdb.py 2>&1 || \
    echo "[INFO] Esecuzione manuale fallita — verifica GLPI API token"
```

**Step 3 — Test analisi impatto manuale:**

```bash
echo ""
echo "=== TEST ANALISI DI IMPATTO ==="
echo ""
echo "SCENARIO: DC-LAB-01 va DOWN alle 14:30"
echo ""
echo "SENZA CMDB (scenario tipico senza documentazione):"
echo "  14:30 — Alert: WKS-LAB-01 non autentica"
echo "  14:35 — Tecnico: 'Problema nel workstation?'"
echo "  14:40 — Tecnico: 'No, è la rete?'"
echo "  14:45 — Tecnico: 'GLPI è down anche quello?'"
echo "  14:50 — Scoperta causa: DC-LAB-01 down"
echo "  TTI (Time to Identify): 20 minuti"
echo ""
echo "CON CMDB e impact analysis:"
echo "  14:30 — Alert: DC-LAB-01 up{} = 0"
echo "  14:31 — IC apre impact analysis in GLPI"
echo "  14:31 — Vede: WKS-LAB-01 (auth), GLPI (LDAP), VPN (se presente)"
echo "  14:31 — Comunica impatto a tutti i team affetti"
echo "  TTI: 1 minuto"
echo ""
echo "DIFFERENZA: 19 minuti di investigazione eliminati"
echo ""

# Mostra le dipendenze del lab che abbiamo modellato
echo "Mappa dipendenze configurata:"
cat << 'DEPS'
DC-LAB-01 DOWN →
  ├── WKS-LAB-01: autenticazione AD fallisce
  ├── GLPI (su SRV-LINUX-01): login LDAP fallisce
  └── DNS: se DC è anche DNS server → risoluzione nomi fallisce
  
SRV-LINUX-01 DOWN →
  ├── GLPI: non raggiungibile (monitoring, ticketing)
  ├── Prometheus: nessun dato metriche
  ├── Grafana: dashboards offline
  └── Uptime Kuma: synthetic monitoring offline
DEPS
```

**Checkpoint di verifica B2:**
- [ ] Mappa dipendenze del lab disegnata (anche su carta)
- [ ] Almeno 2 relazioni CI-CI create in GLPI
- [ ] Script Python testato (anche se API non disponibile)
- [ ] Sai rispondere: "Se DC-LAB-01 cade, cosa si ferma?"

---

### Esercizio B3: Snipe-IT — Asset Management Dedicato

**Obiettivo.** Deployare Snipe-IT in Docker come alternativa ITAM-focused a GLPI, e importare i 3 asset del lab.

**Step 1 — Deploy Snipe-IT con Docker:**

```bash
# Su SRV-LINUX-01

echo "=== DEPLOY SNIPE-IT VIA DOCKER ==="
mkdir -p /opt/snipeit/{storage,mysql}
cd /opt/snipeit

# File .env
cat > /opt/snipeit/.env << 'ENV'
# Snipe-IT Lab Configuration
APP_ENV=production
APP_DEBUG=false
APP_KEY=
APP_URL=http://192.168.56.20:8082
APP_TIMEZONE=Europe/Rome
APP_LOCALE=it

DB_CONNECTION=mysql
DB_HOST=snipeit-mysql
DB_PORT=3306
DB_DATABASE=snipeit
DB_USERNAME=snipeit
DB_PASSWORD=SnipeLabPass2024!

MYSQL_ROOT_PASSWORD=SnipeRootPass2024!
MYSQL_DATABASE=snipeit
MYSQL_USER=snipeit
MYSQL_PASSWORD=SnipeLabPass2024!

MAIL_MAILER=log
MAIL_FROM_ADDR=snipeit@lab.local
MAIL_FROM_NAME='Snipe-IT Lab'
ENV

# Docker Compose
cat > /opt/snipeit/docker-compose.yml << 'DC'
version: '3.8'
services:
  snipeit:
    image: snipe/snipe-it:latest
    container_name: snipeit
    restart: unless-stopped
    depends_on:
      - snipeit-mysql
    env_file: .env
    ports:
      - "8082:80"
    volumes:
      - ./storage:/var/lib/snipeit
    networks:
      - snipeit-net

  snipeit-mysql:
    image: mysql:8.0
    container_name: snipeit-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - ./mysql:/var/lib/mysql
    networks:
      - snipeit-net

networks:
  snipeit-net:
    name: snipeit-net
DC

echo "[OK] File configurazione creati"
echo ""
echo "Genera APP_KEY:"
docker run --rm snipe/snipe-it:latest php artisan key:generate --show 2>/dev/null | tail -1 | \
    xargs -I{} sed -i "s|APP_KEY=|APP_KEY={}|" /opt/snipeit/.env
echo "[OK] APP_KEY generata"
echo ""
echo "Avvia Snipe-IT:"
echo "  cd /opt/snipeit && docker compose up -d"
echo ""
echo "Setup wizard: http://192.168.56.20:8082 (attendi 2-3 min per primo avvio)"
echo "Poi: Pre-Flight Check → Setup wizard"
```

**Step 2 — Import asset lab via API Snipe-IT:**

```python
#!/usr/bin/env python3
"""
snipeit_import.py — Importa i 3 asset del lab in Snipe-IT via REST API
Esegui dopo aver completato il setup wizard di Snipe-IT
"""
import requests
import json
import sys

SNIPE_URL = "http://192.168.56.20:8082"
# Genera token in Snipe-IT → Profile → API → Generate Token
TOKEN = "SNIPEIT_BEARER_TOKEN"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Dati asset del lab
LAB_ASSETS = [
    {
        "asset_tag":      "HW-SRV-0001",
        "name":           "SRV-LINUX-01",
        "serial":         "VM-LINUX-LAB-001",
        "model_id":       1,      # Aggiorna con l'ID reale dopo creazione modello
        "status_id":      2,      # 2 = Deployed/In uso
        "purchase_date":  "2024-01-15",
        "purchase_cost":  0.00,   # VM di lab
        "warranty_months": 36,
        "notes":          "Server Ubuntu 22.04 — GLPI, Prometheus, Grafana"
    },
    {
        "asset_tag":      "HW-SRV-0002",
        "name":           "DC-LAB-01",
        "serial":         "VM-WIN-LAB-001",
        "model_id":       2,
        "status_id":      2,
        "purchase_date":  "2024-01-15",
        "purchase_cost":  0.00,
        "warranty_months": 36,
        "notes":          "Windows Server 2022 — Domain Controller, DNS, DHCP"
    },
    {
        "asset_tag":      "HW-WKS-0001",
        "name":           "WKS-LAB-01",
        "serial":         "VM-WIN10-LAB-001",
        "model_id":       3,
        "status_id":      2,
        "purchase_date":  "2024-01-15",
        "purchase_cost":  0.00,
        "warranty_months": 24,
        "notes":          "Windows 10 — Workstation utente lab-user"
    }
]

def import_assets():
    print("=== IMPORT ASSET IN SNIPE-IT ===")
    
    for asset in LAB_ASSETS:
        try:
            resp = requests.post(
                f"{SNIPE_URL}/api/v1/hardware",
                headers=HEADERS,
                json=asset,
                timeout=10
            )
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get("status") == "success":
                    asset_id = result.get("payload", {}).get("id", "?")
                    print(f"[OK] {asset['name']} creato (ID: {asset_id})")
                else:
                    print(f"[WARN] {asset['name']}: {result.get('messages', 'errore sconosciuto')}")
            else:
                print(f"[FAIL] {asset['name']}: HTTP {resp.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"[FAIL] Snipe-IT non raggiungibile: {SNIPE_URL}")
            print("       Completa il setup wizard prima di eseguire questo script")
            return 1
        except Exception as e:
            print(f"[FAIL] {asset['name']}: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(import_assets())
```

```bash
# Salva ed esegui
cat > /cmdb-lab/scripts/snipeit_import.py << 'PYEOF'
# (contenuto dello script sopra)
PYEOF

echo "Script salvato in /cmdb-lab/scripts/snipeit_import.py"
echo ""
echo "Per eseguire (dopo setup Snipe-IT):"
echo "  1. Genera Bearer Token in Snipe-IT → Profilo → API"
echo "  2. Crea i modelli (Server VM, Workstation VM) nel wizard"
echo "  3. Aggiorna model_id nello script con i valori reali"
echo "  4. python3 /cmdb-lab/scripts/snipeit_import.py"
```

**Checkpoint di verifica B3:**
- [ ] Snipe-IT Docker compose file creato
- [ ] Snipe-IT avviato e raggiungibile su porta 8082 (o tentativo)
- [ ] Script di import Python preparato
- [ ] Sai la differenza di scope tra GLPI e Snipe-IT

---

### Esercizio B4: Mantenere la Qualità dei Dati CMDB

**Obiettivo.** Creare un processo sistematico per rilevare e correggere dati obsoleti/errati nel CMDB (orphan CI, CI senza relazioni, record duplicati).

**Step 1 — Script di quality check:**

```bash
cat > /cmdb-lab/scripts/cmdb_quality_check.sh << 'SCRIPT'
#!/usr/bin/env bash
# cmdb_quality_check.sh — Verifica qualità dati CMDB

set -euo pipefail

GLPI_URL="http://localhost:8080/glpi"
TODAY=$(date '+%Y-%m-%d')
REPORT="/cmdb-lab/exports/cmdb-quality-$(date +%Y%m).txt"

mkdir -p /cmdb-lab/exports

echo "=== REPORT QUALITÀ CMDB — $TODAY ===" | tee "$REPORT"
echo "" | tee -a "$REPORT"

# ─── CHECK 1: CI NON AGGIORNATI ────────────────────────────
echo "CHECK 1: CI non aggiornati da > 90 giorni" | tee -a "$REPORT"
echo "  Questi CI potrebbero essere obsoleti o dimenticati" | tee -a "$REPORT"
echo ""  | tee -a "$REPORT"
echo "  (Verifica manuale in GLPI → Asset → Computer)" | tee -a "$REPORT"
echo "  Filtro: 'Data modifica' < $(date -d '90 days ago' +%Y-%m-%d)" | tee -a "$REPORT"
echo "" | tee -a "$REPORT"

# ─── CHECK 2: DISCOVERY ASSET ATTIVI ───────────────────────
echo "CHECK 2: Asset di rete attivi (non documentati in CMDB)" | tee -a "$REPORT"
echo "" | tee -a "$REPORT"

# Scan rete per host attivi (richiede nmap)
if command -v nmap &>/dev/null; then
    echo "  Scan rete 192.168.56.0/24..." | tee -a "$REPORT"
    LIVE_HOSTS=$(nmap -sn 192.168.56.0/24 2>/dev/null | grep "Nmap scan report" | \
        awk '{print $NF}' | tr -d '()')
    echo "  Host rilevati:" | tee -a "$REPORT"
    echo "$LIVE_HOSTS" | while read -r host; do
        echo "    $host" | tee -a "$REPORT"
    done
    LIVE_COUNT=$(echo "$LIVE_HOSTS" | grep -c "." 2>/dev/null || echo 0)
    echo "  Totale: $LIVE_COUNT host attivi" | tee -a "$REPORT"
    echo "  → Confronta con CI nel CMDB: tutti documentati?" | tee -a "$REPORT"
else
    echo "  [INFO] nmap non disponibile — installa con: apt install nmap" | tee -a "$REPORT"
    echo "  Alternativa: ping sweep manuale" | tee -a "$REPORT"
fi
echo "" | tee -a "$REPORT"

# ─── CHECK 3: CERTIFICATI IN SCADENZA ──────────────────────
echo "CHECK 3: Certificati SSL/TLS in scadenza" | tee -a "$REPORT"
echo "" | tee -a "$REPORT"

# Verifica certificato GLPI (se https)
GLPI_CERT_CHECK=$(echo | openssl s_client -connect 192.168.56.20:443 2>/dev/null | \
    openssl x509 -noout -dates 2>/dev/null || echo "no_https")
if [[ "$GLPI_CERT_CHECK" != "no_https" ]]; then
    echo "$GLPI_CERT_CHECK" | tee -a "$REPORT"
else
    echo "  GLPI usa HTTP (no certificato da verificare)" | tee -a "$REPORT"
fi
echo "" | tee -a "$REPORT"

# ─── RIEPILOGO ─────────────────────────────────────────────
echo "=== RIEPILOGO AZIONI RICHIESTE ===" | tee -a "$REPORT"
echo "  1. Verifica CI non aggiornati da > 90 giorni → aggiorna o dismetti" | tee -a "$REPORT"
echo "  2. Confronta host rilevati con CMDB → documenta quelli mancanti" | tee -a "$REPORT"
echo "  3. Pianifica rinnovo certificati in scadenza < 30 giorni" | tee -a "$REPORT"
echo "" | tee -a "$REPORT"
echo "Report: $REPORT" | tee -a "$REPORT"
SCRIPT

chmod +x /cmdb-lab/scripts/cmdb_quality_check.sh
echo "[OK] Script qualità CMDB creato"
bash /cmdb-lab/scripts/cmdb_quality_check.sh
```

**Step 2 — Regole di certificazione CI:**

```bash
echo ""
echo "=== PROCESSO DI CERTIFICAZIONE CI ==="
echo ""
cat << 'EOF'
OGNI 90 GIORNI — Processo di revisione CI:

  Per ogni servizio business critico, il "CI Owner" (tecnico responsabile):
  
  STEP 1: Accede al CI in GLPI
  STEP 2: Verifica che ogni campo sia ancora corretto:
    - IP ancora quello? (cambio DHCP?)
    - OS aggiornato? (patch recente? upgrade versione?)
    - Software installato aggiornato?
    - Relazioni ancora valide? (cambio architettura?)
    - Utente assegnatario ancora quello?
    
  STEP 3: Aggiorna i campi obsoleti
  
  STEP 4: Aggiunge un "commento di certificazione":
    "CI verificato e corretto — [data] — [nome tecnico]"
    
  STEP 5: Aggiorna il campo "Data ultima modifica" (automatico GLPI)

METRICHE DI QUALITÀ:
  Accuratezza inventario: > 95%
    (CI CMDB che corrispondono alla realtà fisica)
    
  CI certificati nell'ultimo trimestre: > 80%
    (CI revisionati attivamente)
    
  CI senza relazioni ("orphan"): < 5%
    (CI non collegati ad altri → probabilmente inutili o incompleti)
    
COME MISURARE (tramite GLPI Reports o query SQL):
  -- Esempio query MariaDB (richiede accesso diretto al DB GLPI)
  SELECT name, date_mod, comment 
  FROM glpi_computers 
  WHERE date_mod < DATE_SUB(NOW(), INTERVAL 90 DAY)
  AND is_deleted = 0
  ORDER BY date_mod ASC;
EOF
```

**Checkpoint di verifica B4:**
- [ ] Script cmdb_quality_check.sh eseguito
- [ ] Comprendi le 3 verifiche di qualità (obsolescenza, discovery, certificati)
- [ ] Processo di certificazione CI 90 giorni compreso
- [ ] Sai cos'è un "orphan CI" e perché è problematico

---

### Esercizio B5: Service Mapping — Mappa il Servizio "IT Operations Lab"

**Obiettivo.** Creare la mappa completa del servizio "IT Operations Lab" come Business Service in GLPI, collegando tutti i CI tecnici.

```bash
echo "=== SERVICE MAPPING — IT OPERATIONS LAB ==="
echo ""
echo "Creiamo la mappa del servizio 'IT Operations Lab'."
echo ""
echo "OPZIONE A — Con plugin GenericObject (se installato):"
echo ""
cat << 'EOF'
1. Configura → Oggetti generici → + Aggiungi tipo
   Nome: "Business Service"
   Attributi: Nome, Criticità, Owner, RTO, RPO

2. Asset → Business Services → + Aggiungi
   Nome:        IT Operations Lab
   Criticità:   Alta (lab di training)
   Owner:       lab-admin
   RTO:         4 ore
   RPO:         1 ora

3. Nel record "IT Operations Lab":
   Aggiungi relazione → "depends on" → GLPI (Software)
   Aggiungi relazione → "depends on" → AD DS (Software su DC-LAB-01)
   Aggiungi relazione → "depends on" → Prometheus (Software)
EOF

echo ""
echo "OPZIONE B — Usando campo 'Commento' come workaround (senza plugin):"
echo ""
echo "Apri record SRV-LINUX-01 in GLPI"
echo "Campo Commento:"
cat << 'COMMENT'
=== SERVICE MAP: IT OPERATIONS LAB ===

Business Service: IT Operations Lab
  Criticità: Alta | RTO: 4h | RPO: 1h

CI dipendenti da questo server:
  → GLPI (ticketing/CMDB) — porta 8080
  → Prometheus (metriche) — porta 9090
  → Grafana (dashboards) — porta 3000
  → Uptime Kuma (synthetic) — porta 3001
  → MariaDB (DB per GLPI) — porta 3306

Dipendenze upstream:
  → DC-LAB-01 (AD/DNS) per autenticazione GLPI
  
Impact chain: SRV-LINUX-01 DOWN → tutti i servizi IT lab offline
COMMENT

echo ""
echo "=== EXPORT SERVICE MAP ==="
# Salva la mappa in un file per documentazione
cat > /cmdb-lab/relationships/service-map-it-ops-lab.md << 'MAPEOF'
# Service Map: IT Operations Lab

Data: $(date '+%Y-%m-%d')
Owner: lab-admin

## Business Service
- **Nome:** IT Operations Lab
- **Criticità:** Alta
- **RTO:** 4 ore | **RPO:** 1 ora
- **SLA:** disponibilità 95% (lab)

## Dipendenze (Infrastructure Stack)

```
[IT Operations Lab — Business Service]
  ├── depends on → [GLPI v10]
  │                └── hosted on → [SRV-LINUX-01]
  │                                └── depends on → [MariaDB]
  │                                └── depends on → [DC-LAB-01] (LDAP auth)
  │
  ├── depends on → [Prometheus]
  │                └── hosted on → [SRV-LINUX-01]
  │                └── scrapes → [Node Exporter (SRV-LINUX-01)]
  │                └── scrapes → [Windows Exporter (DC-LAB-01)]
  │
  ├── depends on → [Grafana]
  │                └── hosted on → [SRV-LINUX-01]
  │                └── data source → [Prometheus]
  │
  └── depends on → [Active Directory DS]
                   └── hosted on → [DC-LAB-01]
                   └── serves → [WKS-LAB-01]
                   └── serves → [GLPI LDAP auth]
```

## Analisi di Impatto

| CI Down | Servizi Impattati | Severity |
|---------|-------------------|----------|
| DC-LAB-01 | Login GLPI (LDAP), WKS autenticazione | SEV2 |
| SRV-LINUX-01 | GLPI, Prometheus, Grafana, Uptime Kuma | SEV1 |
| WKS-LAB-01 | Solo accesso workstation lab-user | SEV3 |
MAPEOF

echo "[OK] Service map salvata: /cmdb-lab/relationships/service-map-it-ops-lab.md"
cat /cmdb-lab/relationships/service-map-it-ops-lab.md
```

**Checkpoint di verifica B5:**
- [ ] Service Map "IT Operations Lab" creata in GLPI (o documentata)
- [ ] File service-map-it-ops-lab.md salvato con dipendenze complete
- [ ] Sai rispondere: "Se SRV-LINUX-01 cade, qual è il SEV?"
- [ ] Hai capito la differenza tra top-down e bottom-up service mapping

---

## PART C: SISTEMATIZZARE — CMDB come Asset Operativo

---

### Progetto C1: SOP-CMDB-001 — Gestione Configuration Item

```
Documento: SOP-CMDB-001
Titolo:    Procedura Standard Gestione Configuration Item
Versione:  1.0
Owner:     IT Operations

---

APERTURA NUOVO CI:
  TRIGGER: nuovo server/VM acquistato, nuovo servizio deployato,
           nuovo dispositivo di rete installato

  [ ] Identificazione univoca: nome, hostname, IP
  [ ] Classificazione: tipo CI, criticità (Critica/Alta/Media/Bassa)
  [ ] Attributi obbligatori compilati:
      - Tipo, Produttore, Modello, OS (per HW)
      - Versione, Vendor, URL/porta (per Software)
      - Data installazione, Owner tecnico
  [ ] Relazioni minime definite:
      - "hosted on" (se software/VM)
      - "depends on" (dipendenze critiche)
      - "used by" (chi usa questo CI?)
  [ ] CI collegato al ticket di Change (se Change Management attivo)
  [ ] Revisione impact analysis dopo aggiunta relazioni

AGGIORNAMENTO CI:
  TRIGGER: ogni Change che modifica un CI (upgrade OS, cambio IP,
           aggiunta RAM, nuovo software installato)

  [ ] Apri il CI impattato in GLPI
  [ ] Aggiorna l'attributo modificato
  [ ] Aggiungi commento: "[data] — [cosa è cambiato] — [change ref.]"
  [ ] Verifica relazioni ancora valide (il Change potrebbe averle modificate)
  [ ] CMDB aggiornato PRIMA della chiusura del ticket di Change

DISMISSIONE CI:
  TRIGGER: server dismesso, VM eliminata, servizio terminato

  [ ] Verifica relazioni: chi dipende da questo CI?
      → Se esistono dipendenze → risolvi prima di dismettere
  [ ] Notifica ai team che usano il CI
  [ ] Aggiorna stato CI: "Ritirato" (non cancellare — mantieni storia)
  [ ] Rimuovi relazioni attive (mantieni relazioni storiche)
  [ ] Collegamento a ticket di decommissioning

AUDIT TRIMESTRALE CI:
  [ ] Lista CI con "Data ultima modifica" > 90 giorni → verifica
  [ ] Lista CI "orphan" (senza relazioni) → indaga o rimuovi
  [ ] Confronto discovery automatica vs CMDB
  [ ] Aggiorna "CI Owner" se personale cambiato
  [ ] Report qualità: accuratezza % (target: > 95%)
```

---

### Progetto C2: Automazione CMDB con GLPI Agent

```bash
#!/usr/bin/env bash
# setup_glpi_agent.sh — Configura GLPI Agent (sostituto di FusionInventory)
# Per GLPI 11+ — usa inventory nativo

echo "=== SETUP GLPI AGENT ==="
echo "GLPI Agent è il successore di FusionInventory per GLPI 11+"
echo ""

# Opzione 1: GLPI Agent su Ubuntu (SRV-LINUX-01)
GLPI_SERVER="http://192.168.56.20:8080/glpi"

# Scarica e installa GLPI Agent (verifica ultima versione su GitHub)
AGENT_VERSION="1.16"
AGENT_DEB="glpi-agent_${AGENT_VERSION}_all.deb"

if [[ ! -f "/usr/local/bin/glpi-agent" ]]; then
    echo "Download GLPI Agent ${AGENT_VERSION}..."
    wget -q "https://github.com/glpi-project/glpi-agent/releases/download/${AGENT_VERSION}/${AGENT_DEB}" \
        -O "/tmp/${AGENT_DEB}" 2>/dev/null || {
        echo "[INFO] Download non disponibile — configurazione manuale richiesta"
        echo "       URL: https://github.com/glpi-project/glpi-agent/releases"
    }
    
    if [[ -f "/tmp/${AGENT_DEB}" ]]; then
        sudo dpkg -i "/tmp/${AGENT_DEB}" 2>/dev/null && echo "[OK] GLPI Agent installato"
    fi
fi

# Configurazione
if command -v glpi-agent &>/dev/null; then
    sudo tee /etc/glpi-agent/agent.cfg > /dev/null << CFG
# GLPI Agent Configuration
server = $GLPI_SERVER
tag = SRV-LINUX-LABS
delaytime = 86400
backend-collect-timeout = 180
CFG
    
    sudo systemctl enable glpi-agent 2>/dev/null
    sudo systemctl restart glpi-agent 2>/dev/null
    echo "[OK] GLPI Agent configurato → $GLPI_SERVER"
    
    echo ""
    echo "Test inventario immediato:"
    sudo glpi-agent --force 2>&1 | head -20
else
    echo "[INFO] GLPI Agent non installato"
    echo "       Nel lab usa FusionInventory Agent (ops08a)"
    echo "       GLPI Agent è raccomandato per GLPI 11+"
fi

echo ""
echo "Verifica in GLPI → Amministrazione → Inventario"
```

---

### Progetto C3: Integrazione CMDB ↔ Incident Management

```
CICLO DI VITA COMPLETO: INCIDENT → CMDB → PROBLEM → CHANGE

  INCIDENT aperto:
    → tecnico seleziona il CI impattato in GLPI
    → Impact analysis automatica mostra servizi a rischio
    → Communications Lead notifica i team impattati (da relazione "used by")
    
  DOPO RISOLUZIONE:
    → Se causa è un attributo CI non corretto → aggiorna CMDB
    → Se causa è relazione non documentata → aggiungi relazione
    → Se causa è CI non presente nel CMDB → crea CI mancante
    
  PROBLEM MANAGEMENT:
    → Problem record collegato ai CI coinvolti
    → CMDB mostra frequenza incident per CI → identifica CI problematici
    → CI con > 3 incident simili → candidato per Problem + Change
    
  CHANGE MANAGEMENT:
    → Ogni change deve referenziare il CI in CMDB
    → Pre-change: impact analysis CMDB mostra CI a rischio
    → Post-change: CMDB aggiornato con le modifiche effettuate

REPORT MENSILE CMDB:
  Dati da estrarre da GLPI e portare al management:
  
  ✓ Numero CI totali (trend: cresce o decresce?)
  ✓ CI per stato (In uso / Dismesso / In riparazione)
  ✓ CI per criticità (Critica/Alta/Media/Bassa)
  ✓ CI aggiornati nel mese (qualità dati)
  ✓ Incident per CI (top 5 CI con più incident = candidati Problem)
  ✓ Copertura discovery automatica (% CI con ultimo inventario < 30gg)
  
  Questo report dimostra al management il valore del CMDB:
  "Grazie alla CMDB, l'incident del 15/07 è stato diagnosticato in
   2 minuti invece dei soliti 20 — impatto stimato: 1.500€ risparmio"
```

---

## Checklist di Validazione Lab — ops08b

```
FONDAMENTI (Part A):
  [ ] A1: Sai la differenza tra CMDB (operativo) e ITAM (finanziario)
  [ ] A2: Conosci i tipi di relazioni CI (depends on, hosted on, runs on)
  [ ] A3: Sai cosa è il service mapping e la differenza top-down/bottom-up
  [ ] A4: Conosci le 3 tecniche di discovery (agent, agentless, API federation)
  [ ] A5: Sai la regola d'oro: "1.000 CI accurati > 10.000 CI obsoleti"

OPERAZIONI (Part B):
  [ ] B1: CI per SRV-LINUX-01, DC-LAB-01, WKS-LAB-01 creati in GLPI
  [ ] B2: Almeno 2 relazioni CI-CI modellate in GLPI
  [ ] B3: Snipe-IT deployato (o tentato) e compreso come alternativa ITAM
  [ ] B4: Script cmdb_quality_check.sh eseguito con risultati
  [ ] B5: Service map "IT Operations Lab" creata con grafo dipendenze

SISTEMATIZZARE (Part C):
  [ ] C1: SOP-CMDB-001 compresa (apertura, aggiornamento, dismissione CI)
  [ ] C2: GLPI Agent configurato (o FusionInventory come alternativa)
  [ ] C3: Comprendi il ciclo CMDB ↔ Incident ↔ Problem ↔ Change
```

---

## Appendice A: Confronto CMDB Tools

| Feature | GLPI 10/11 | Snipe-IT | ServiceNow |
|---------|-----------|----------|------------|
| Tipo | ITSM + CMDB + ITAM | ITAM puro | Enterprise ITSM |
| Licenza | Open Source | Open Source | SaaS a pagamento |
| Discovery | FusionInventory / GLPI Agent | Script/API esterni | Discovery nativa |
| Relazioni CI | Sì (plugin CMDB) | No | Sì (avanzata) |
| Impact Analysis | Sì (GLPI 10+) | No | Sì (eccellente) |
| Service Mapping | Manuale | No | Automatica |
| REST API | Sì | Sì (ottima) | Sì |
| Costo indicativo | Gratuito | Gratuito | ~€50K+/anno |
| Ideale per | PMI, PA italiana | PMI (solo asset) | Enterprise |

## Riferimenti

- `13-cmdb-glpi-snipeit-implementazione.md` — Guida completa CMDB e tools
- ITIL v4 Practice Guide: Service Configuration Management
- GLPI Agent: https://github.com/glpi-project/glpi-agent
- Snipe-IT API Docs: https://snipe-it.readme.io/reference
- **Tutorial precedente:** `tutorial_ops08_ch1a_asset_lifecycle_lab.md`
- **Tutorial successivo:** `tutorial_ops09_ch1a_sop_runbook_creation_lab.md`
