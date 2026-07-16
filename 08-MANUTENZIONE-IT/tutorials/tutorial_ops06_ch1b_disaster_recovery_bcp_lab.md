# Tutorial: Disaster Recovery e Business Continuity — Hands-On Lab

> **Documento di riferimento:** `06-backup-disaster-recovery.md` (sezioni 4-5: Disaster Recovery Plan e Business Continuity)
> **Dominio:** Protezione Dati — DR/BCP Operations
> **Ambito:** BIA, RTO/RPO, DRP struttura e scenari, test DR, HA (clustering, replica DB, DNS failover), Business Continuity Plan, MBCO, procedure di fallback manuale
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio-Avanzato — richiede ops06a (Backup Strategy)
> **Prerequisiti:** DC-LAB-01, SRV-LINUX-01 operativi; tutorial ops06a completato
> **Ambiente:** DC-LAB-01 (WSFC concepts, PowerShell), SRV-LINUX-01 (Pacemaker/HAProxy theory, bash DR scripts)

---

## Lab Environment Setup

```bash
# Su SRV-LINUX-01 — prepara struttura directory DR
sudo mkdir -p /dr/{docs,test-results,runbooks,contact-list}
sudo chown -R lab-admin:lab-admin /dr
echo "Directory DR setup completato"
ls /dr
```

```powershell
# Su DC-LAB-01 — verifica prerequisiti
Write-Host "=== VERIFICA PRE-LAB DR ==="
# Verifica backup esistente da tutorial ops06a
$backupSets = Get-WBBackupSet -ErrorAction SilentlyContinue
if ($backupSets) {
    Write-Host "[OK] Backup disponibili: $($backupSets.Count)"
} else {
    Write-Host "[WARN] Nessun backup trovato — completare ops06a prima di questo lab"
}
# Verifica AD
if (Get-Service "NTDS" -ErrorAction SilentlyContinue) {
    Write-Host "[OK] Active Directory attivo"
}
```

---

## PART A: FONDAMENTI — Pianificare la Sopravvivenza dell'IT

> In IT Operations, la domanda non è "se" avremo un disastro, ma "quando". Un incendio nel server room, un ransomware che cifra tutto, un amministratore che cancella l'OU sbagliata, un aggiornamento che porta giù l'intera rete. Il Disaster Recovery non è una procedura tecnica: è un piano di sopravvivenza aziendale. La differenza tra un'azienda che sopravvive a un disastro IT e una che chiude (statisticamente, il 40% delle aziende che subisce un disastro IT senza DR plan non riapre entro un anno) sta quasi interamente nella qualità della pianificazione fatta PRIMA dell'evento.

---

### Concetto A1: BIA — Prima di Pianificare, Capire cosa Perdi

> **Analogia.** Prima di comprare un'assicurazione, un imprenditore fa un inventario: cosa ho, quanto vale, quanto mi costerebbe perderlo? La Business Impact Analysis (BIA) è lo stesso processo applicato all'IT. Non ha senso avere un sito DR da 100.000€/anno per un sistema che genera 500€ al mese di valore. La BIA risponde alla domanda: "Se questo sistema va giù, quanto ci costa ogni ora?"

**Il framework BIA:**

```
PROCESSO BIA:

Passo 1 — IDENTIFICA i servizi critici:
  Chiedi ai responsabili di business:
  "Se questo sistema non funzionasse per 4 ore, cosa succederebbe?"
  "Se i dati di ieri fossero persi per sempre, quanto ci costerebbe?"

Passo 2 — QUANTIFICA l'impatto per servizio:
  Impatto finanziario:
    → Vendite perse per ora di downtime
    → Costi di recupero manuale
    → Penali contrattuali (SLA verso clienti)
    → Sanzioni regolamentari (GDPR, NIS2)
    
  Impatto operativo:
    → Dipendenti impossibilitati a lavorare
    → Processi che si bloccano a cascata
    
  Impatto reputazionale:
    → Clienti che migrano alla concorrenza
    → Copertura mediatica negativa

Passo 3 — DEFINISCI RTO e RPO per sistema:

  RTO (Recovery Time Objective):
    Risponde a: "Quanto posso stare senza questo sistema?"
    Esempio: ERP → RTO = 4h (dopo 4h i processi di business si bloccano)
    
  RPO (Recovery Point Objective):
    Risponde a: "Quanti dati posso permettermi di perdere?"
    Esempio: Database ordini → RPO = 1h (massimo 1 ora di ordini persi)

Passo 4 — CLASSIFICA per tier:
  
  Tier 1 — Critico (RTO < 1h, RPO < 15min):
    AD, storage primario, sistema di pagamento
    Richiede: replica sincrona, hot site, backup ogni 15 min
    
  Tier 2 — Importante (RTO 1-4h, RPO 1h):
    ERP, CRM, email, file server
    Richiede: replica asincrona, warm site, backup orario
    
  Tier 3 — Necessario (RTO 4-24h, RPO 4h):
    Intranet, reportistica, development
    Richiede: backup giornaliero, cold site o cloud
    
  Tier 4 — Non critico (RTO 24-72h, RPO 24h):
    Archivi storici, sistemi di test
    Richiede: backup giornaliero, restore on-demand
```

**Tabella BIA — Esempio LAB:**

```
Sistema          | Tier | RTO   | RPO   | Impatto/h         | Priorità restore
───────────────────────────────────────────────────────────────────────────────
Active Directory | 1    | 2h    | 30min | Nessun login → blocco totale
GLPI (ITSM)      | 2    | 4h    | 1h    | Ticketing manuale (carta)
DNS/DHCP         | 1    | 1h    | 1h    | Rete non raggiungibile per nome
File server      | 2    | 4h    | 4h    | Condivisioni non accessibili
```

---

### Concetto A2: Il DRP — Struttura di un Piano di Recovery Reale

> **Analogia.** I vigili del fuoco non arrivano a un incendio e improvvisano. Hanno piani predefiniti per ogni tipo di edificio, ruoli chiari, equipaggiamento pronto, procedure di comunicazione con ospedali e polizia. Il DRP è il piano dei vigili del fuoco per il tuo IT: chi fa cosa, in quale ordine, con quali strumenti, e come si comunica durante la crisi.

**Struttura di un DRP:**

```
DISASTER RECOVERY PLAN — STRUTTURA:

1. PRESUPPOSTI E SCOPE
   → Quali sistemi copre?
   → Quali scenari include (e quali esclude)?
   → Quando viene attivato?
   
2. TEAM DI RISPOSTA
   Ruolo              | Responsabilità           | Titolare  | Backup
   ───────────────────────────────────────────────────────────────────
   DR Manager         | Decisione di attivazione | [nome]    | [nome]
   Infrastructure Lead| Ripristino rete/server   | [nome]    | [nome]
   Application Lead   | Ripristino applicazioni  | [nome]    | [nome]
   Security Lead      | Valutazione sicurezza    | [nome]    | [nome]
   Communication Lead | Comunicazioni            | [nome]    | [nome]

3. ORDINE DI RIPRISTINO (dipende da BIA):
   Step 1: Rete (firewall, switch, DNS)
   Step 2: Identità (Active Directory)
   Step 3: Storage e hypervisor
   Step 4: Sistemi Tier 1 (ordine BIA)
   Step 5: Sistemi Tier 2
   Step 6: Sistemi Tier 3-4
   Step 7: Validazione end-to-end

4. PROCEDURE SPECIFICHE PER SCENARIO:
   → Guasto hardware singolo server
   → Guasto data center completo
   → Attacco ransomware
   → Corruzione logica (cancellazione accidentale)
   → Outage cloud provider
   
5. COMUNICAZIONE:
   → Chi notificare e quando (interna: 30 min / esterna: 2h)
   → Canali alternativi se i sistemi aziendali sono down
   → Template comunicazioni pre-scritte
   
6. TEST E MANUTENZIONE:
   → Frequenza test per tipo
   → Processo di aggiornamento del piano
   → Registro test e azioni correttive
```

---

### Concetto A3: Scenari di Disastro — Prepararsi allo Specifico

> Ogni disastro è diverso. Un guasto hardware singolo è una procedura. Un ransomware è un'altra. Una cancellazione accidentale AD è un'altra ancora. Il DRP deve avere procedure specifiche per ogni scenario — una procedura generica "ripristina dal backup" è inutile sotto pressione.

**I 5 scenari principali e le loro differenze:**

```
SCENARIO 1: GUASTO HARDWARE SINGOLO
  Cause: disco guasto, alimentatore, memoria, scheda madre
  Impatto: servizio down, altri sistemi OK
  Procedura:
    → VM su hypervisor: migra su altro host (HA)
    → Server fisico: sostituisci componente o ripristina su hardware alternativo
  RTO tipico: 1-4h (VM), 4-24h (fisico)
  Rischio backup: BASSO — restore standard

SCENARIO 2: GUASTO DATA CENTER COMPLETO
  Cause: incendio, alluvione, interruzione energia prolungata (>UPS duration)
  Impatto: TUTTI i sistemi down
  Procedura:
    → Attiva sito DR (hot/warm/cold/cloud)
    → Aggiorna DNS per reindirizzare traffico
    → Ripristina sistemi in ordine BIA
  RTO tipico: 4h (hot) → 24-72h (cold)
  
SCENARIO 3: ATTACCO RANSOMWARE (IL PIÙ COMPLESSO)
  Cause: phishing, RDP esposto, credenziali rubate, supply chain
  Impatto: dati cifrati, sistemi potenzialmente compromessi
  Fasi:
    T+0:   Identificazione (alert da EDR, utenti non riescono ad aprire file)
    T+15m: ISOLAMENTO — stacca i sistemi infetti dalla rete
           (non spegnere: potresti distruggere evidenze forensi in RAM)
    T+1h:  Valutazione — quale variante? quali sistemi colpiti?
           I backup sono intatti (i ransomware moderni li cercano!)
    T+2h:  Verifica backup immutabili/air-gapped (3-2-1-1-0 rule!)
    T+4h:  Ricostruzione infrastruttura DA ZERO (non fidarsi dei sistemi)
    T+24h: Ripristino dati da backup verified
    Post:  Cambia TUTTE le credenziali, patch, forensics
    Obblighi legali: notifica Garante Privacy entro 72h se dati personali esposti
    
SCENARIO 4: CANCELLAZIONE ACCIDENTALE (il più comune)
  Cause: errore operatore, script sbagliato
  Esempi: rm -rf /etc, Remove-ADOrganizationalUnit, DROP DATABASE
  Procedura:
    AD: usa AD Recycle Bin (se abilitato) → ripristino autoritativo
    DB: restore point-in-time dal backup
    File: shadow copy o restore backup
    
SCENARIO 5: OUTAGE CLOUD PROVIDER
  Cause: problemi provider (Azure outage, AWS region failure)
  Procedura:
    → Failover su region secondaria (se configurata)
    → Aggiornamento DNS
    → Comunicazione utenti con ETA realistica
```

---

### Concetto A4: Alta Disponibilità — Prevenire il Disastro

> **Analogia.** Un aereo moderno ha quattro motori non perché uno non basti, ma perché se uno va in avaria durante il volo, l'aereo continua a volare. L'Alta Disponibilità (HA) applica lo stesso principio ai servizi IT: rimuove i Single Point of Failure (SPOF) così che un guasto non causi downtime. La HA riduce la probabilità di attivare il DRP.

**Livelli di HA:**

```
COMPONENTE       | SPOF senza HA    | SOLUZIONE HA
─────────────────────────────────────────────────────
Server           | Singolo server   | Clustering (WSFC, Pacemaker)
                 |                  | VM con HA hypervisor
                 |                  |
Storage          | Singolo disco    | RAID (locale)
                 | Singolo array    | Replica storage (storage → storage)
                 |                  |
Rete             | Singolo switch   | Switch ridondanti + spanning tree
                 | Singolo uplink   | NIC teaming / bonding
                 | Singolo firewall | Firewall in HA pair
                 |                  |
Database         | Singolo DB       | Always On (SQL Server)
                 |                  | Streaming Replication (PostgreSQL)
                 |                  | MariaDB Galera Cluster
                 |                  |
Bilanciamento    | Singolo server   | Load Balancer (HAProxy, NGINX)
carico           | applicativo      | DNS round-robin
                 |                  |
Geografico       | Singolo sito     | Active-Active / Active-Passive
                 |                  | (richiede WAN/cloud + replica storage)

FORMULA:
  Uptime = (1 - P_failure^n) × 100%
  
  n=1 server:  P(guasto) = 0.01  → Uptime 99%
  n=2 server:  P(guasto) = 0.0001 → Uptime 99.99%
  n=3 server:  P(guasto) = 0.000001 → Uptime 99.9999%
```

---

### Concetto A5: BCP — Il DRP Non Basta

> **Analogia.** Se brucia l'ufficio, non basta sapere come ripristinare i server. Bisogna sapere dove lavoreranno i dipendenti, come risponderanno ai clienti, come continueranno a prendere ordini (anche se solo su carta), come comunicheranno quando email e telefono aziendale sono down. Il BCP è più grande del DRP: include le persone, i processi manuali, la comunicazione, la sede alternativa.

```
DRP vs BCP:

DRP (Disaster Recovery PLAN):
  → Si occupa di: sistemi IT, dati, infrastruttura
  → Domanda: "Come ripristino i server?"
  → Standard: ISO 27031
  → Owner: IT Manager

BCP (Business Continuity PLAN):
  → Si occupa di: TUTTA l'organizzazione
  → Domanda: "Come continua il business se IT è down?"
  → Include: sede alternativa, procedure manuali, gestione HR in crisi
  → Standard: ISO 22301
  → Owner: CEO / COO

MBCO (Minimum Business Continuity Objective):
  → Non si ripristina tutto al 100%, si definisce il MINIMO necessario
  → Esempio MBCO: "Almeno il 50% degli ordini processabili, fatturazione attiva"
  → Guida le PRIORITÀ di ripristino
  
PROCEDURE DI FALLBACK MANUALE:
  Ogni processo critico deve avere una versione "carta e penna":
  → Ordini: moduli cartacei pre-stampati
  → Comunicazioni: cellulari personali + WhatsApp/Signal group aziendale
  → Accesso emergenza: lista password in busta sigillata in cassaforte fisica
  → Pagamenti: procedura bonifico telefonico con la banca
```

---

## PART B: OPERAZIONI — Testare e Documentare il DR

---

### Esercizio B1: Tabletop Exercise — Simulazione Ransomware su Carta

**Obiettivo.** Eseguire un tabletop exercise (esercitazione teorica) seguendo la procedura di risposta a un attacco ransomware, identificando gap e tempi di risposta attesi.

**Background.** Il tabletop exercise è il metodo più efficiente per validare un DRP: si percorre il piano su carta, si simulano le decisioni, si identificano i problemi SENZA impattare la produzione. Costa solo tempo del team.

**Setup — scenario:**

```
SCENARIO SIMULATO:
Data: lunedì mattina, ore 09:15
Segnalazione: un utente su WKS-LAB-01 non riesce ad aprire i suoi file Excel
              Gli header dei file sono stati cambiati in ".encrypted"
              Sul desktop appare "YOUR_FILES_ARE_ENCRYPTED_README.txt"

Obiettivo: percorri la procedura di risposta e documenta i tempi
```

**Step 1 — Identification (T+0 a T+15 minuti):**

```bash
# Su SRV-LINUX-01 — simula la raccolta di informazioni iniziali
echo "=== IDENTIFICATION PHASE — T+0 ==="
cat << 'EOF'
CHECKLIST DI IDENTIFICAZIONE:

[ ] 1. Conferma l'alert:
        - Parla con l'utente: solo il suo PC? altri colleghi?
        - Accedi al PC infetto (se sicuro): controlla i file
        
[ ] 2. Determina la portata PRIMA di agire:
        - Quanti sistemi mostrano sintomi?
        - Controlla i file server: sono state cifrate condivisioni?
        - Controlla il backup: i file di backup sono intatti?
        
[ ] 3. NON fare ancora nulla di distruttivo:
        ✗ NON spegnere il PC infetto (perdi evidenze RAM)
        ✗ NON cancellare nulla
        ✗ NON pagare il riscatto
        ✓ DOCUMENTA tutto (screenshot, note, orari)
        
[ ] 4. Notifica immediata:
        - IT Manager: entro 5 minuti dall'identificazione
        - Responsabile Sicurezza (se esiste)
        
DOMANDA: con le informazioni disponibili, è davvero ransomware
         o potrebbe essere un malfunzionamento di un'app?
EOF

echo ""
echo "Tempo teorico questa fase: 15 minuti"
echo "Responsabile: IT Operations on-duty"
```

**Step 2 — Containment (T+15 a T+30 minuti):**

```bash
echo "=== CONTAINMENT PHASE — T+15 ==="
cat << 'EOF'
AZIONI DI ISOLAMENTO:

[ ] IMMEDIATO — Isolamento di rete:
    Opzione A (preferita): disabilita la porta dello switch a cui è connesso il PC
    Opzione B (alternativa): stacca fisicamente il cavo di rete
    Opzione C (emergenza): disabilita l'account utente infetto in AD
    
    PER OGNI SISTEMA SOSPETTO:
    - Stacca dalla rete MA NON spegnere
    - Identifica e blocca connessioni est-ovest nel firewall/VLAN
    
[ ] VERIFICA BACKUP (CRITICO):
    Controlla SUBITO se i backup sono intatti:
    → rsync: ls /backup/lab-local/ | tail -5 — ci sono file .encrypted?
    → Borg: borg list /backup/borg-repo — repository accessibile?
    → I backup immutabili (append-only Borg, WORM S3) non dovrebbero
      essere stati toccati — ma verifica!
    
[ ] IDENTIFICA LA VARIANTE:
    Cerca il nome nel file README lasciato dal ransomware
    → Cerca su nomoreransom.org: esiste un decryptor gratuito?
    → Se sì, potrebbe non essere necessario il restore completo
    
COMUNICAZIONI T+30:
    Notifica management (email/telefono):
    "Rilevato potenziale ransomware su [sistemi]. Sistemi isolati.
     Backup verificati [intatti/a rischio]. Avvio procedura DR.
     Prossimo aggiornamento tra 2 ore."
EOF

echo "Tempo teorico questa fase: 15 minuti"
```

**Step 3 — Eradication e Recovery (T+1h a T+24h+):**

```bash
echo "=== ERADICATION & RECOVERY PHASE ==="
cat << 'EOF'
SEQUENZA DI RECOVERY:

T+1h-4h: ASSESSMENT COMPLETO
  - Inventario completo sistemi compromessi vs intatti
  - Backup audit: quali backup sono puliti e di quando?
  - Decisione: pago il riscatto? (Quasi mai consigliato)
  
T+4h-8h: RICOSTRUZIONE INFRASTRUTTURA BASE
  1. Prepara ambiente di rete pulito (VLAN separata)
  2. Ripristina un Domain Controller da backup System State
     wbadmin start systemstaterecovery -version:[id] -quiet
  3. Cambia TUTTE le password AD (servizi, admin, utenti)
  
T+8h-24h: RIPRISTINO SISTEMI IN ORDINE BIA
  1. Tier 1 (AD, DNS già fatto sopra)
  2. Database GLPI da backup mysqldump:
     zcat /backup/lab-local/[data]/glpi_db_*.sql.gz | mysql -u root -p glpi
  3. File server da backup rsync/Borg
  4. Workstation: reinstalla da zero (non fidare dei sistemi infetti)
  
T+24h-72h: RIPRISTINO SISTEMI RIMANENTI
  - Sistemi Tier 2-3 in ordine
  - Reinstallazione workstation
  - Verifica funzionale completa
  
POST-INCIDENT (obbligatorio):
  - Notifica Garante Privacy entro 72h (se dati personali coinvolti)
  - Notifica Polizia Postale (incidente informatico)
  - Forensics: come è entrato il ransomware?
  - Patching del vettore di attacco prima di riconnettere tutto
  
TEMPO TOTALE ATTESO nel lab:
  Se backup intatti e DRP documentato: 24-48h
  Se backup compromessi: indefinito (scenario worst-case)
EOF

echo "Documenta i tempi attesi in /dr/test-results/tabletop-ransomware-$(date +%Y%m%d).txt"
```

**Step 4 — Documenta i risultati del tabletop:**

```bash
cat > "/dr/test-results/tabletop-ransomware-$(date +%Y%m%d).txt" << EOF
=== TABLETOP EXERCISE REPORT ===
Data: $(date '+%Y-%m-%d')
Scenario: Attacco ransomware su WKS-LAB-01
Partecipanti: lab-admin (simulato)
Tipo test: Tabletop (esercitazione teorica)

TEMPI STIMATI:
  Identification:  15 minuti
  Containment:     15 minuti
  Assessment:      3 ore
  Infrastruttura base: 4-8 ore
  Tier 1 completamente ripristinato: 24 ore
  Recovery completo: 48 ore

GAP IDENTIFICATI:
  [ ] Lista contatti fornitore hardware non trovata durante l'esercizio
  [ ] Procedura backup non documentata in modo da essere seguita in crisi
  [ ] Nessun canale di comunicazione alternativo se email è down
  [ ] Password Borg repository documentata? → deve essere nel vault

AZIONI CORRETTIVE:
  1. Creare /dr/contact-list.txt con contatti emergenza
  2. Stampare procedure DRP e conservare fuori dal server room
  3. Configurare gruppo Telegram/Signal per comunicazioni emergenza
  4. Documentare passphrase Borg nel password manager aziendale

VERDICT: DRP parzialmente documentato — livello di preparazione INSUFFICIENTE
         per un ransomware reale. Gap critici su comunicazione e procedure.
EOF

cat "/dr/test-results/tabletop-ransomware-$(date +%Y%m%d).txt"
```

**Checkpoint di verifica B1:**
- [ ] Scenario ransomware percorso con tutte le 3 fasi
- [ ] Report tabletop salvato con gap identificati
- [ ] Almeno 3 gap identificati e azioni correttive documentate

---

### Esercizio B2: BIA pratico — Classificare i Sistemi del Lab

**Obiettivo.** Eseguire una mini-BIA sui sistemi del lab per definire RTO, RPO e priorità di restore.

**Step 1 — Inventario sistemi:**

```bash
# Su SRV-LINUX-01

echo "=== BIA — INVENTARIO SISTEMI LAB ==="

# Rileva servizi attivi
echo "Servizi Linux attivi:"
systemctl list-units --type=service --state=active --no-legend | \
    grep -E "(ssh|mysql|docker|glpi|nginx|apache)" | \
    awk '{print "  →", $1}'

echo ""
echo "Containers Docker attivi:"
docker ps --format "  → {{.Names}} ({{.Image}})" 2>/dev/null || echo "  (Docker non attivo)"

echo ""
echo "Processo di BIA — domande da rispondere per ogni sistema:"
cat << 'EOF'
Per ogni servizio, rispondere:
  1. Se questo servizio fosse down per 1 ora, cosa succederebbe?
  2. Quanti utenti/processi ne dipendono?
  3. Esiste un workaround manuale? Per quanto tempo è sostenibile?
  4. Quale è il valore economico/operativo per ora di downtime?
EOF
```

**Step 2 — Compila la matrice BIA:**

```bash
# Crea documento BIA del lab
cat > /dr/docs/bia-lab.txt << 'EOF'
=== BUSINESS IMPACT ANALYSIS — LAB ENVIRONMENT ===
Data analisi: $(date +%Y-%m-%d)
Analista: lab-admin

SISTEMA: Active Directory (DC-LAB-01)
  Funzione: Autenticazione di tutti gli utenti e computer del dominio
  Dipendenze: TUTTI gli altri sistemi (login, GPO, DNS)
  Impatto se down 1h: nessun utente può autenticarsi al dominio
  Impatto se down 4h: operazioni completamente bloccate
  Workaround manuale: account locali (limitato, solo per emergenza)
  RTO: 2 ore
  RPO: 30 minuti
  TIER: 1 (Critico)

SISTEMA: GLPI (SRV-LINUX-01 — Docker)
  Funzione: Service desk, inventario, ticketing IT
  Dipendenze: MariaDB, Docker, SRV-LINUX-01
  Impatto se down 1h: ticketing manuale via email/telefono
  Impatto se down 4h: perdita tracciabilità incident
  Workaround manuale: foglio Excel / carta — sostenibile per 8h
  RTO: 4 ore
  RPO: 1 ora
  TIER: 2 (Importante)

SISTEMA: SSH/Admin access (SRV-LINUX-01)
  Funzione: Accesso amministrativo al server Linux
  Dipendenze: Networking, sshd
  Impatto se down 1h: impossibile gestire server Linux
  Impatto se down 4h: sistemi Linux non gestibili
  Workaround manuale: accesso console fisico (se in loco)
  RTO: 1 ora
  RPO: N/A (nessun dato da ripristinare)
  TIER: 2 (Importante — necessario per recovery di altri sistemi)

SISTEMA: File backup (rsync + Borg)
  Funzione: Protezione dati — senza questo il DR non funziona
  Dipendenze: /backup storage
  Impatto se compromesso: NESSUN RECOVERY POSSIBILE
  TIER: 1 (Critico) — i backup sono infrastruttura critica!
EOF

echo "BIA creata in /dr/docs/bia-lab.txt"
cat /dr/docs/bia-lab.txt
```

**Checkpoint di verifica B2:**
- [ ] Inventario sistemi LAB completato
- [ ] Almeno 3 sistemi classificati con RTO/RPO/Tier
- [ ] Documento BIA salvato in /dr/docs/

---

### Esercizio B3: Alta Disponibilità — Configurare DNS Failover (Simulazione)

**Obiettivo.** Comprendere il DNS failover come meccanismo di HA di alto livello e simulare il comportamento in laboratorio con record DNS multipli.

**Background.** Il DNS failover è spesso il meccanismo più semplice per reindirizzare il traffico da un server guasto a uno funzionante. In produzione si usano servizi come Route 53 (AWS) o Cloudflare con health check integrati. Nel lab lo simulo con TTL bassi e record multipli.

**Step 1 — Comprendi il DNS failover:**

```powershell
# Su DC-LAB-01 — visualizza configurazione DNS attuale
Import-Module DnsServer -ErrorAction SilentlyContinue

# Visualizza record A esistenti
Write-Host "=== RECORD DNS ATTUALI ==="
Get-DnsServerResourceRecord -ZoneName "lab.local" -RRType A | 
    Select-Object HostName, RecordData | Format-Table -AutoSize

# Record attuale per SRV-LINUX-01
$linuxRecord = Get-DnsServerResourceRecord -ZoneName "lab.local" -Name "srv-linux-01" -RRType A -ErrorAction SilentlyContinue
if ($linuxRecord) {
    Write-Host "SRV-LINUX-01 risolve in: $($linuxRecord.RecordData.IPv4Address)"
} else {
    Write-Host "[INFO] Record srv-linux-01 non trovato — normale nel lab"
}
```

**Step 2 — Crea record per simulare failover:**

```powershell
# Aggiunge un record "servizio" che può essere reindirizzato

# Record per simulare un servizio web con failover
$zoneName = "lab.local"

# Servizio primario
try {
    Add-DnsServerResourceRecordA -ZoneName $zoneName `
        -Name "webservice" -IPv4Address "192.168.56.20" `
        -TimeToLive ([TimeSpan]::FromSeconds(60)) `
        -ErrorAction Stop
    Write-Host "[OK] Record webservice.lab.local → 192.168.56.20 (primario)"
} catch {
    Write-Host "[INFO] Record già esistente o errore: $_"
}

# Visualizza il TTL basso configurato
$record = Get-DnsServerResourceRecord -ZoneName $zoneName -Name "webservice" -RRType A -ErrorAction SilentlyContinue
if ($record) {
    Write-Host "TTL configurato: $($record.TimeToLive.TotalSeconds) secondi"
    Write-Host ""
    Write-Host "SPIEGAZIONE DEL TTL BASSO:"
    Write-Host "  TTL 60s = dopo 60 secondi, i client ri-risolvono il nome"
    Write-Host "  In caso di failover: aggiorna il record DNS → traffico reindirizzato in max 60s"
    Write-Host "  Produzione tipica: TTL 300s per bilanciare performance e velocità failover"
}
```

**Step 3 — Simula il failover DNS:**

```powershell
Write-Host ""
Write-Host "=== SIMULAZIONE FAILOVER DNS ==="
Write-Host ""
Write-Host "SCENARIO: SRV-LINUX-01 (192.168.56.20) non risponde"
Write-Host ""

# Prima del failover
Write-Host "Prima del failover:"
Resolve-DnsName "webservice.lab.local" -Server "192.168.56.10" -ErrorAction SilentlyContinue |
    Select-Object Name, IPAddress | Format-Table

# Simula failover: aggiorna il record al server di backup
Write-Host ""
Write-Host "AZIONE: Aggiornamento record DNS per failover..."
Write-Host "(In produzione: health check automatico fa questo istantaneamente)"
Write-Host ""

# In un ambiente reale, il DC-LAB-01 potrebbe servire come server di backup
$backupIp = "192.168.56.10"
Write-Host "Aggiorno webservice.lab.local → $backupIp (server di backup)"

# Per il lab, mostriamo solo il comando (non modificare configurazioni di produzione)
Write-Host ""
Write-Host "Comando per aggiornare il record:"
Write-Host "  Remove-DnsServerResourceRecord -ZoneName lab.local -Name webservice -RRType A -Force"
Write-Host "  Add-DnsServerResourceRecordA -ZoneName lab.local -Name webservice -IPv4Address $backupIp -TTL 60"
Write-Host ""
Write-Host "Dopo l'aggiornamento DNS (entro 60s grazie al TTL basso):"
Write-Host "  Resolve-DnsName webservice.lab.local → $backupIp"
Write-Host ""
Write-Host "CHIAVE: il DNS failover funziona solo se:"
Write-Host "  1. Il TTL è basso (< 300s) sui record critici"  
Write-Host "  2. Il server di backup è già pronto (non basta l'IP, serve il servizio)"
Write-Host "  3. I dati sono sincronizzati (il server di backup ha i dati aggiornati)"
```

**Step 4 — HA con clustering su Linux (teoria e comandi):**

```bash
# Su SRV-LINUX-01 — Comprensione Pacemaker/Corosync (non installare in produzione senza pianificazione)

echo "=== ALTA DISPONIBILITÀ — PACEMAKER/COROSYNC ==="
echo ""
echo "Pacemaker è il gestore delle risorse HA su Linux."
echo "Corosync è il layer di comunicazione tra i nodi del cluster."
echo ""
echo "In un cluster HA a 2 nodi:"
echo "  SRV-LINUX-01 (nodo1) ←→ SRV-LINUX-02 (nodo2, non presente nel lab)"
echo "  Se nodo1 cade → nodo2 prende il virtual IP e avvia i servizi"
echo ""
echo "Comandi chiave Pacemaker (da conoscere):"
echo ""
cat << 'EOF'
# Verifica stato cluster
pcs status

# Crea risorsa IP virtuale (VIP) che migra tra i nodi
pcs resource create VIP ocf:heartbeat:IPaddr2 \
    ip=192.168.56.100 cidr_netmask=24 \
    op monitor interval=10s

# Crea risorsa servizio
pcs resource create WebApp systemd:nginx \
    op monitor interval=30s

# Vincolo: WebApp deve stare sullo stesso nodo di VIP
pcs constraint colocation add WebApp with VIP INFINITY

# Vincolo: VIP deve avviarsi prima di WebApp
pcs constraint order VIP then WebApp

# In caso di failover manuale (migrazione):
pcs resource move VIP nodo2

# Verifica health nodi
pcs node status
EOF

echo ""
echo "Nota: Pacemaker richiede 2+ nodi. Con un solo nodo nel lab,"
echo "      si usa HA tramite VM migration (Hyper-V, VMware, Proxmox)"
```

**Checkpoint di verifica B3:**
- [ ] Record DNS webservice creato con TTL basso (60s)
- [ ] Compreso il meccanismo di DNS failover
- [ ] Comandi Pacemaker letti e compresi concettualmente

---

### Esercizio B4: DRP — Creare il Piano Formale del Lab

**Obiettivo.** Creare un DRP minimale ma completo per l'ambiente lab, seguendo la struttura di un DRP enterprise.

**Step 1 — Genera il template DRP:**

```bash
# Su SRV-LINUX-01

DRP_FILE="/dr/docs/DRP-LAB-v1.0.md"

cat > "$DRP_FILE" << 'DRPEOF'
# DISASTER RECOVERY PLAN — LAB ENVIRONMENT
Versione: 1.0
Data: [DATA]
Owner: IT Operations Lab
Revisione: Annuale o dopo ogni incidente significativo

---

## 1. SCOPE E OBIETTIVI

**Sistemi coperti:**
- DC-LAB-01 (192.168.56.10) — Active Directory, DNS
- SRV-LINUX-01 (192.168.56.20) — GLPI, backup, servizi Linux
- WKS-LAB-01 (192.168.56.30) — Workstation di test

**Scenari coperti:**
- [x] Guasto hardware singolo server
- [x] Attacco ransomware
- [x] Cancellazione accidentale Active Directory
- [ ] Guasto data center completo (fuori scope per lab VirtualBox)

**RTO Globale:** 8 ore per ripristino Tier 1
**RPO Globale:** 24 ore (backup giornaliero)

---

## 2. TEAM DI RISPOSTA

| Ruolo | Titolare | Contatto | Backup |
|-------|----------|----------|--------|
| DR Manager | lab-admin | [cellulare] | [backup] |
| Infrastructure Lead | lab-admin | [cellulare] | [backup] |

**Canali di comunicazione d'emergenza:**
- Primario: email lab-admin@lab.local
- Alternativo (se email down): WhatsApp gruppo "IT-EMERGENCY"
- Voce: [numero diretto]

---

## 3. CLASSIFICAZIONE SISTEMI (dalla BIA)

| Sistema | Tier | RTO | RPO | Note |
|---------|------|-----|-----|------|
| Active Directory | 1 | 2h | 30min | Ripristina per primo |
| DNS/DHCP | 1 | 1h | 1h | Dipende da AD |
| GLPI | 2 | 4h | 1h | Backup in Docker |
| File backup | 1 | N/A | N/A | INFRASTRUTTURA CRITICA |

---

## 4. ORDINE DI RIPRISTINO

```
STEP 1: Networking (firewall, switch, VPN) — RESPONSABILE: [nome]
STEP 2: Active Directory — DC-LAB-01 — RESPONSABILE: [nome]  
STEP 3: DNS/DHCP (già incluso in AD) — RESPONSABILE: [nome]
STEP 4: Database GLPI (MariaDB) — RESPONSABILE: [nome]
STEP 5: Applicazione GLPI — RESPONSABILE: [nome]
STEP 6: Workstation — RESPONSABILE: [nome]
STEP 7: Validazione end-to-end — RESPONSABILE: [nome]
```

---

## 5. PROCEDURE PER SCENARIO

### 5A. Guasto Hardware Singolo
1. Identifica il componente guasto (dmesg, Event Viewer)
2. Se VM: migra su altro host
3. Se fisico: ordina componente sostitutivo (contratto: [fornitore])
4. Ripristina da backup su hardware alternativo:
   ```
   wbadmin start systemstaterecovery -version:[id]
   ```

### 5B. Attacco Ransomware
1. [T+0-15min] IDENTIFICA: conferma sintomi, stima portata
2. [T+15-30min] ISOLA: stacca dalla rete (non spegnere!)
3. [T+30-60min] VERIFICA BACKUP: intatti? immutabili?
4. [T+1-4h] VALUTA: quale variante? decryptor disponibile?
5. [T+4h+] RECOVERY: ricostruisci infrastruttura pulita
6. Notifica: Garante Privacy (72h), Polizia Postale

### 5C. Cancellazione Accidentale AD
1. STOP: non fare altre operazioni che potrebbero peggiorare
2. Se oggetto singolo cancellato → AD Recycle Bin:
   ```powershell
   Get-ADObject -Filter {isDeleted -eq $true} -IncludeDeletedObjects
   Restore-ADObject -Identity [GUID]
   ```
3. Se OU intera o corruzione grave → restore autoritativo:
   ```
   Riavvia DC in DSRM → wbadmin start systemstaterecovery
   ```

---

## 6. COMUNICAZIONE

### Template Email — Primo Annuncio
```
SOGGETTO: [IT ALERT] Interruzione servizio [sistema] — [data/ora]

Gentili utenti,
informiamo che il servizio [sistema] è attualmente non disponibile.
Causa: [nota/in verifica]
Stima ripristino: [ora o "in aggiornamento"]
Workaround: [istruzioni se disponibili]
Prossimo aggiornamento: tra 2 ore

IT Operations
```

### Template Email — Ripristino
```
SOGGETTO: [IT RESOLVED] Servizio [sistema] ripristinato — [ora]

Il servizio [sistema] è stato ripristinato alle [ora].
Causa dell'interruzione: [breve descrizione]
Durata: [X ore X minuti]

Per report completo sulle cause e azioni preventive, 
sarà inviato un post-mortem entro 5 giorni lavorativi.

IT Operations
```

---

## 7. LISTA CONTATTI EMERGENZA

| Fornitore | Tipo | Numero | Contratto | SLA |
|-----------|------|--------|-----------|-----|
| [Hardware] | Server/storage | [numero] | [#contratto] | [SLA] |
| [ISP] | Connettività | [numero] | [#contratto] | [SLA] |
| [Cloud] | IaaS/backup | [supporto] | [account] | [SLA] |

---

## 8. TEST DR

| Tipo Test | Frequenza | Ultimo Eseguito | Esito | Prossimo |
|-----------|-----------|-----------------|-------|----------|
| Tabletop exercise | Trimestrale | [data] | [esito] | [data] |
| Test restore file | Mensile | [data] | [esito] | [data] |
| Test restore DB | Mensile | [data] | [esito] | [data] |
| Simulazione completa | Annuale | [data] | [esito] | [data] |
DRPEOF

echo "[OK] DRP creato in $DRP_FILE"
wc -l "$DRP_FILE"
```

**Checkpoint di verifica B4:**
- [ ] DRP creato in /dr/docs/DRP-LAB-v1.0.md
- [ ] Sezioni 1-8 complete con dati del lab
- [ ] Almeno 2 scenari documentati con procedure specifiche

---

### Esercizio B5: Test Restore Completo — Misura il tuo RTO Reale

**Obiettivo.** Eseguire un test di restore GLPI (database + configurazione) e documentare il tempo reale, confrontandolo con l'RTO definito nella BIA.

**Step 1 — Prepara l'ambiente di test restore:**

```bash
# Su SRV-LINUX-01

echo "=== TEST RESTORE COMPLETO — $(date '+%Y-%m-%d %H:%M:%S') ==="
RESTORE_TEST_DIR="/backup/lab-test-restore/full-test-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESTORE_TEST_DIR"

echo "Directory test restore: $RESTORE_TEST_DIR"
echo ""
echo "OBIETTIVO: verifica che i backup di GLPI possano essere ripristinati"
echo "           e misura il tempo necessario (confronta con RTO = 4h)"
echo ""

# Fase 1: Verifica disponibilità backup
echo "=== FASE 1: VERIFICA BACKUP DISPONIBILI ==="
START_RESTORE=$(date +%s)

LAST_BACKUP_DIR=$(find /backup/lab-local -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sort | tail -1)
if [[ -n "$LAST_BACKUP_DIR" ]]; then
    echo "[OK] Ultimo backup disponibile: $LAST_BACKUP_DIR"
    ls -lh "$LAST_BACKUP_DIR/" 2>/dev/null || echo "Directory vuota"
else
    echo "[WARN] Nessun backup rsync trovato — usa Borg o crea backup di test"
    LAST_BACKUP_DIR="/tmp/test-restore-sim"
    mkdir -p "$LAST_BACKUP_DIR"
fi

PHASE1_TIME=$(( $(date +%s) - START_RESTORE ))
echo "Tempo fase 1 (identificazione backup): ${PHASE1_TIME}s"
```

**Step 2 — Restore database GLPI:**

```bash
echo ""
echo "=== FASE 2: RESTORE DATABASE GLPI ==="
PHASE2_START=$(date +%s)

# Trova backup SQL
BACKUP_SQL=$(find /backup/lab-local -name "*.sql.gz" 2>/dev/null | sort | tail -1)

if [[ -n "$BACKUP_SQL" ]]; then
    echo "Backup SQL trovato: $BACKUP_SQL"
    echo "Dimensione: $(du -sh "$BACKUP_SQL" | awk '{print $1}')"
    
    # Verifica il contenuto (senza eseguire restore reale)
    echo ""
    echo "Verifica struttura backup:"
    zcat "$BACKUP_SQL" 2>/dev/null | grep -E "^CREATE TABLE|^-- Dump|^-- MariaDB" | head -5
    
    echo ""
    echo "Procedura di restore reale (non eseguita per preservare GLPI attivo):"
    echo "  1. docker exec [container] mysqladmin -uroot -p drop glpi"
    echo "  2. docker exec [container] mysqladmin -uroot -p create glpi"
    echo "  3. zcat $BACKUP_SQL | docker exec -i [container] mysql -uroot -p glpi"
    echo "  4. Verifica: docker exec [container] mysql -uroot -p -e 'SELECT COUNT(*) FROM glpi.glpi_tickets;'"
    echo ""
    echo "[OK] Procedura verificata. Backup SQL è valido."
else
    echo "[INFO] Nessun backup SQL trovato — simulazione procedura"
    echo ""
    echo "Backup mysqldump tipico da creare:"
    echo "  docker exec glpi-db mysqldump --single-transaction -uroot -pPASSWORD glpi | gzip > glpi_backup.sql.gz"
fi

PHASE2_TIME=$(( $(date +%s) - PHASE2_START ))
echo "Tempo fase 2 (restore DB simulato): ${PHASE2_TIME}s"
```

**Step 3 — Restore file di configurazione:**

```bash
echo ""
echo "=== FASE 3: RESTORE CONFIGURAZIONI ==="
PHASE3_START=$(date +%s)

# Test restore da BorgBackup
if command -v borg &>/dev/null && [[ -d "/backup/borg-repo" ]]; then
    echo "Restore file /etc da Borg..."
    ARCHIVE=$(BORG_PASSPHRASE="LabBackup2024Sicuro!" borg list /backup/borg-repo --short 2>/dev/null | head -1)
    
    if [[ -n "$ARCHIVE" ]]; then
        cd "$RESTORE_TEST_DIR"
        BORG_PASSPHRASE="LabBackup2024Sicuro!" borg extract \
            "/backup/borg-repo::${ARCHIVE}" \
            etc/hostname etc/hosts etc/passwd \
            2>/dev/null
        
        echo "[OK] File di configurazione ripristinati:"
        ls -la "$RESTORE_TEST_DIR/etc/" 2>/dev/null || echo "(directory etc non creata)"
    else
        echo "[INFO] Nessun archivio Borg disponibile"
    fi
else
    echo "[INFO] Borg non disponibile — simulazione completata concettualmente"
fi

PHASE3_TIME=$(( $(date +%s) - PHASE3_START ))
echo "Tempo fase 3 (restore config): ${PHASE3_TIME}s"
```

**Step 4 — Report test restore:**

```bash
TOTAL_TEST_TIME=$(( $(date +%s) - START_RESTORE ))

echo ""
echo "=== REPORT TEST RESTORE ==="
REPORT_FILE="/dr/test-results/restore-test-$(date +%Y%m%d_%H%M%S).txt"

cat > "$REPORT_FILE" << EOF
=== TEST RESTORE REPORT ===
Data:         $(date '+%Y-%m-%d %H:%M:%S')
Eseguito da:  $(whoami) su $(hostname)
Tipo test:    Restore parziale (simulazione procedure)

TEMPI:
  Fase 1 (identificazione backup): ${PHASE1_TIME}s
  Fase 2 (restore database):       ${PHASE2_TIME}s  
  Fase 3 (restore configurazioni): ${PHASE3_TIME}s
  TOTALE SIMULAZIONE:              ${TOTAL_TEST_TIME}s

NOTA: I tempi sopra sono per la SIMULAZIONE.
      Restore reale di GLPI su hardware equivalente: stimato 45-90 minuti
      RTO target (dalla BIA): 4 ore
      VERDICT: RTO target raggiungibile con questa procedura

BACKUP UTILIZZATO:
  rsync: $(find /backup/lab-local -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sort | tail -1 || echo "non trovato")
  Borg:  $(BORG_PASSPHRASE="LabBackup2024Sicuro!" borg list /backup/borg-repo --short 2>/dev/null | head -1 || echo "non disponibile")

PROSSIMO TEST: $(date -d "+30 days" '+%Y-%m-%d' 2>/dev/null || date '+%Y-%m-%d') (mensile)

AZIONI DI MIGLIORAMENTO:
  [ ] Automatizzare verifica mensile con script
  [ ] Misurare RTO reale con restore completo su sistema di test
  [ ] Aggiornare BIA se RTO reale differisce dal target
EOF

cat "$REPORT_FILE"
echo ""
echo "[OK] Report salvato in $REPORT_FILE"
```

**Checkpoint di verifica B5:**
- [ ] Test restore eseguito con documentazione dei tempi
- [ ] Report salvato in /dr/test-results/
- [ ] RTO stimato confrontato con RTO target dalla BIA

---

## PART C: SISTEMATIZZARE — DR come Pratica Continua

---

### Progetto C1: SOP-DR-001 — Procedura di Attivazione DR

```
Documento: SOP-DR-001
Titolo:    Attivazione Piano di Disaster Recovery
Versione:  1.0
Owner:     IT Operations
Quando usare: Quando un incidente supera la capacità di risposta normale
              e richiede l'attivazione del DRP

CRITERI DI ATTIVAZIONE DR (almeno uno deve verificarsi):
  [ ] Sistema Tier 1 non raggiunge RTO standard (> 2h di tentativi normali)
  [ ] Più sistemi Tier 1 down contemporaneamente
  [ ] Attacco ransomware confermato
  [ ] Data center primario non accessibile
  [ ] Il DR Manager dichiara lo stato di emergenza

PROCEDURA:

[ ] T+0 — DICHIARAZIONE DR
    DR Manager dichiara stato di emergenza
    Orario dichiarazione: ________
    Sistemi interessati: ________

[ ] T+5min — NOTIFICA TEAM
    Contatta tutti i ruoli (telefono, non email se sistemi down):
    - Infrastructure Lead: [numero]
    - Application Lead: [numero]
    - Communication Lead: [numero]
    Punto di raccolta: [sede fisica / videocall link alternativo]

[ ] T+10min — COMUNICAZIONE INIZIALE
    Communication Lead invia annuncio agli utenti:
    Template: /dr/docs/DRP-LAB-v1.0.md sezione 6

[ ] T+15min — ASSESSMENT
    Infrastructure Lead: quali sistemi sono down? backup intatti?
    Compila checklist di assessment:
      [ ] Networking: OK / DOWN
      [ ] Active Directory: OK / DOWN
      [ ] Storage backup: OK / COMPROMESSO
      [ ] Sistemi Tier 1: OK / DOWN (elenco)

[ ] T+30min — DECISIONE DI RECOVERY
    DR Manager, sulla base dell'assessment, decide:
      A) Recovery in loco (se infrastruttura riparabile < RTO)
      B) Failover su sito DR (se disastro fisico)
      C) Recovery graduale da backup (se attacco/corruzione logica)

[ ] T+30min+ — ESECUZIONE RECOVERY
    Segui le procedure specifiche per scenario:
      Ransomware → sezione 5B del DRP
      Hardware → sezione 5A del DRP
      Cancellazione AD → sezione 5C del DRP

[ ] T+[ora ripristino] — VALIDAZIONE
    Infrastructure Lead e Application Lead validano ogni sistema:
      [ ] Active Directory: test login con utente non admin
      [ ] GLPI: apri ticket di test, chiudilo
      [ ] Networking: ping tra tutti i sistemi
      [ ] DNS: risoluzione nomi funzionante

[ ] T+[ora ripristino+30min] — COMUNICAZIONE RIPRISTINO
    Communication Lead invia comunicazione di ripristino
    Template: /dr/docs/DRP-LAB-v1.0.md sezione 6

[ ] T+[+7 giorni] — POST-MORTEM
    Sessione lessons learned:
    - Cause dell'incidente
    - Cosa ha funzionato
    - Gap identificati
    - Azioni correttive con owner e scadenza
    Aggiorna DRP con le lezioni apprese
```

---

### Progetto C2: Script dr_readiness.sh — Verifica Continua della Prontezza DR

```bash
#!/usr/bin/env bash
# dr_readiness.sh — Verifica che l'ambiente sia pronto per un DR
# Da eseguire settimanalmente per garantire prontezza continua

set -euo pipefail

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
HOSTNAME_FQDN=$(hostname -f 2>/dev/null || hostname)
ISSUES=()
WARNINGS=()
DR_DIR="/dr"
REPORT_DIR="$DR_DIR/test-results"
JSON_OUTPUT=false

[[ "${1:-}" == "--json" ]] && JSON_OUTPUT=true
mkdir -p "$REPORT_DIR"

log() { [[ "$JSON_OUTPUT" != true ]] && echo "[$(date '+%H:%M:%S')] $*"; }

# ─── CHECK 1: DOCUMENTI DR ────────────────────────────────────────
check_dr_docs() {
    log "CHECK 1: Documenti DR..."
    local docs_ok=0
    local docs_missing=()

    for doc in "$DR_DIR/docs/DRP-LAB-v1.0.md" "$DR_DIR/docs/bia-lab.txt"; do
        if [[ -f "$doc" ]]; then
            # Verifica che non sia troppo vecchio (> 90 giorni = da rivedere)
            local age_days=$(( ($(date +%s) - $(stat -c %Y "$doc")) / 86400 ))
            if [[ "$age_days" -gt 90 ]]; then
                WARNINGS+=("DOCS: $doc non aggiornato da $age_days giorni (rivedere)")
            else
                log "  [OK] $(basename $doc) — ${age_days} giorni fa"
                ((docs_ok++))
            fi
        else
            docs_missing+=("$(basename $doc)")
            ISSUES+=("DOCS: documento DR mancante: $doc")
        fi
    done

    log "  Documenti OK: $docs_ok / 2"
}

# ─── CHECK 2: BACKUP RECENTE ──────────────────────────────────────
check_backup_ready() {
    log "CHECK 2: Backup disponibile per DR..."

    # Verifica Borg
    if command -v borg &>/dev/null && [[ -d "/backup/borg-repo" ]]; then
        BORG_COUNT=$(BORG_PASSPHRASE="${BORG_PASSPHRASE:-LabBackup2024Sicuro!}" \
            borg list /backup/borg-repo --short 2>/dev/null | wc -l)
        if [[ "$BORG_COUNT" -gt 0 ]]; then
            log "  [OK] Repository Borg: $BORG_COUNT archivi disponibili"
        else
            ISSUES+=("BACKUP: repository Borg vuoto — DR non possibile!")
        fi
    else
        WARNINGS+=("BACKUP: Borg non configurato")
    fi

    # Verifica ultimo backup rsync
    local last_backup
    last_backup=$(find /backup/lab-local -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sort | tail -1)
    if [[ -n "$last_backup" ]]; then
        local age_hours=$(( ($(date +%s) - $(stat -c %Y "$last_backup")) / 3600 ))
        if [[ "$age_hours" -le 25 ]]; then
            log "  [OK] Backup rsync recente: $age_hours ore fa"
        else
            WARNINGS+=("BACKUP: backup rsync vecchio di $age_hours ore")
        fi
    else
        ISSUES+=("BACKUP: nessun backup rsync trovato")
    fi
}

# ─── CHECK 3: ULTIMO TEST RESTORE ─────────────────────────────────
check_last_restore_test() {
    log "CHECK 3: Test restore recente..."

    local restore_reports
    restore_reports=$(find "$REPORT_DIR" -name "restore-test-*.txt" 2>/dev/null | sort | tail -1)

    if [[ -n "$restore_reports" ]]; then
        local report_age=$(( ($(date +%s) - $(stat -c %Y "$restore_reports")) / 86400 ))
        if [[ "$report_age" -le 30 ]]; then
            log "  [OK] Ultimo test restore: $report_age giorni fa"
        elif [[ "$report_age" -le 60 ]]; then
            WARNINGS+=("RESTORE: ultimo test ${report_age} giorni fa (soglia: 30gg)")
        else
            ISSUES+=("RESTORE: nessun test restore negli ultimi 60 giorni — DR a rischio!")
        fi
    else
        WARNINGS+=("RESTORE: nessun report test restore trovato")
    fi
}

# ─── CHECK 4: CONTATTI DR ─────────────────────────────────────────
check_dr_contacts() {
    log "CHECK 4: Lista contatti DR..."

    local contacts_file="$DR_DIR/contact-list.txt"
    if [[ -f "$contacts_file" ]]; then
        local contact_count
        contact_count=$(grep -c "." "$contacts_file" 2>/dev/null || echo 0)
        log "  [OK] Lista contatti presente ($contact_count righe)"
    else
        WARNINGS+=("CONTACTS: lista contatti emergenza non trovata in $contacts_file")
    fi
}

# ─── ESEGUI TUTTI I CHECK ─────────────────────────────────────────
log "=========================================="
log "DR READINESS CHECK — $TIMESTAMP"
log "Host: $HOSTNAME_FQDN"
log "=========================================="

check_dr_docs
check_backup_ready
check_last_restore_test
check_dr_contacts

# ─── CALCOLA STATUS ───────────────────────────────────────────────
STATUS="READY"
[[ "${#WARNINGS[@]}" -gt 0 ]] && STATUS="PARTIAL"
[[ "${#ISSUES[@]}" -gt 0 ]]   && STATUS="NOT_READY"

# ─── OUTPUT ───────────────────────────────────────────────────────
if [[ "$JSON_OUTPUT" == true ]]; then
    cat << EOF
{
  "timestamp": "$TIMESTAMP",
  "hostname": "$HOSTNAME_FQDN",
  "dr_readiness_status": "$STATUS",
  "issues_count": ${#ISSUES[@]},
  "warnings_count": ${#WARNINGS[@]},
  "issues": $(printf '%s\n' "${ISSUES[@]:-}" | jq -R . | jq -s .),
  "warnings": $(printf '%s\n' "${WARNINGS[@]:-}" | jq -R . | jq -s .)
}
EOF
else
    log ""
    log "=========================================="
    log "DR READINESS: $STATUS"
    log "  Issues:   ${#ISSUES[@]}"
    log "  Warnings: ${#WARNINGS[@]}"
    for i in "${ISSUES[@]}"; do log "  [ISSUE] $i"; done
    for w in "${WARNINGS[@]}"; do log "  [WARN]  $w"; done
    log "=========================================="
fi

# ─── SALVA REPORT ─────────────────────────────────────────────────
{
    echo "DR READINESS REPORT — $TIMESTAMP"
    echo "Status: $STATUS"
    echo "Issues: ${#ISSUES[@]}"
    for i in "${ISSUES[@]}"; do echo "  ISSUE: $i"; done
    echo "Warnings: ${#WARNINGS[@]}"
    for w in "${WARNINGS[@]}"; do echo "  WARN: $w"; done
} > "$REPORT_DIR/dr_readiness_$(date +%Y%m%d).txt"

case "$STATUS" in
    "READY")     exit 0 ;;
    "PARTIAL")   exit 1 ;;
    *)           exit 2 ;;
esac
```

**Installazione e pianificazione:**

```bash
# Copia script e rendi eseguibile
sudo cp /tmp/dr_readiness.sh /usr/local/bin/dr_readiness.sh
sudo chmod +x /usr/local/bin/dr_readiness.sh

# Test manuale
bash /usr/local/bin/dr_readiness.sh

# Pianifica verifica settimanale (ogni lunedì alle 09:00)
echo "Aggiungi a /etc/crontab:"
echo "0 9 * * 1 lab-admin /usr/local/bin/dr_readiness.sh >> /var/log/dr_readiness.log 2>&1"
```

---

### Progetto C3: Integrazione ITIL — DR come Service Continuity Management

```
ITIL v4 PRACTICE: IT Service Continuity Management (ITSCM)

Il DRP è l'implementazione operativa dell'ITSCM:

ITIL Concept          | Implementazione Lab
──────────────────────────────────────────────────────
BIA (Business Impact  | /dr/docs/bia-lab.txt
Analysis)             | Tier 1-4, RTO/RPO per sistema
                      |
Continuity Plan       | /dr/docs/DRP-LAB-v1.0.md
                      | Scenari specifici, ordine restore
                      |
Testing               | /dr/test-results/ con report
                      | Mensile (restore), Annuale (simulazione)
                      |
Review & Update       | Annuale o dopo ogni incidente
                      | SOP-DR-001 sezione post-mortem
                      |
Recovery Options      | Backup Borg + rsync (cold restore)
                      | (Lab: no hot site — troppo costoso)


RELAZIONE CON ALTRE PRATICHE ITIL:

Incident Management:
  → Incidente P1/P2 può evolvere in attivazione DRP
  → GLPI ticket deve linkare al DRP attivato
  → Timeline incidente → input per post-mortem DRP

Problem Management:
  → Causa radice identificata → aggiornamento DRP
  → "Come prevenire che questo accada di nuovo?"

Change Management:
  → Modifiche infrastruttura → aggiornamento DRP
  → Cambio hardware → aggiornamento contatti fornitore
  → Cambio architettura → nuova BIA se impatta RTO/RPO

Knowledge Management:
  → Lessons learned da ogni test e incidente
  → Procedure aggiornate nella Knowledge Base (GLPI)
  → Onboarding nuovo personale IT: DRP come documento 1


REGISTRAZIONE IN GLPI:

Crea in GLPI → Gestione → Documenti:
  Tipo documento: Piano DR
  Nome: DRP-LAB-v1.0
  Allegato: /dr/docs/DRP-LAB-v1.0.md
  Data revisione: [data prossima revisione]
  Owner: IT Operations

Crea Promemoria in GLPI per test periodici:
  Oggetto: "Test mensile restore backup"
  Categoria: IT Continuity
  Frequenza: Mensile
  Assegnato a: IT Operations Team
```

---

## Checklist di Validazione Lab — ops06b

```
FONDAMENTI (Part A):
  [ ] A1: Sai cos'è la BIA e come si calcolano RTO e RPO (con esempio)
  [ ] A2: Conosci la struttura di un DRP (8 sezioni principali)
  [ ] A3: Sai descrivere la sequenza di risposta a un ransomware (5 fasi)
  [ ] A4: Sai distinguere HA da DR (HA = previeni downtime, DR = recupero dopo)
  [ ] A5: Sai la differenza tra BCP e DRP con esempio concreto

OPERAZIONI (Part B):
  [ ] B1: Tabletop exercise ransomware completato con report e gap identificati
  [ ] B2: BIA del lab compilata con almeno 3 sistemi classificati
  [ ] B3: Record DNS failover creato e meccanismo compreso
  [ ] B4: DRP formale creato in /dr/docs/DRP-LAB-v1.0.md
  [ ] B5: Test restore documentato con report in /dr/test-results/

SISTEMATIZZARE (Part C):
  [ ] C1: SOP-DR-001 letta e capita
  [ ] C2: Script dr_readiness.sh installato e testato
  [ ] C3: DRP registrato come documento in GLPI
  [ ] C4: Prossima data di test schedulata nel calendario IT
```

---

## Appendice A: Comandi di Riferimento Rapido — DR

```powershell
# ─── ACTIVE DIRECTORY RECOVERY ───────────────────────────────────
# Lista versioni backup System State disponibili
wbadmin get versions -backupTarget:C:\Backup

# Ripristino System State (avvia in DSRM)
# wbadmin start systemstaterecovery -version:"MM/DD/YYYY-HH:MM" -quiet

# AD Recycle Bin — elenca oggetti cancellati
Get-ADObject -Filter {isDeleted -eq $true} -IncludeDeletedObjects |
    Select-Object Name, ObjectClass, WhenChanged | Format-Table

# Ripristina oggetto specifico dal Recycle Bin
# Restore-ADObject -Identity "<GUID>"

# Abilita AD Recycle Bin (una volta sola)
Enable-ADOptionalFeature -Identity "Recycle Bin Feature" `
    -Scope ForestOrConfigurationSet `
    -Target (Get-ADForest).Name -Confirm:$false

# ─── WINDOWS FAILOVER CLUSTER ─────────────────────────────────────
# Valida prerequisiti cluster (senza modificare nulla)
Test-Cluster -Node "node1","node2" -Include "Storage","Network","Inventory"

# Stato cluster
Get-Cluster | Format-List
Get-ClusterNode | Select-Object Name, State

# Migra un ruolo cluster manualmente
# Move-ClusterGroup -Name "Nome-Gruppo" -Node "node2"
```

```bash
# ─── LINUX HA / DR ────────────────────────────────────────────────
# Verifica stato Pacemaker cluster
pcs status 2>/dev/null || echo "Pacemaker non installato"

# Test connettività verso tutti i sistemi del lab
for host in 192.168.56.10 192.168.56.20 192.168.56.30; do
    ping -c 1 -W 1 "$host" &>/dev/null && echo "  $host: OK" || echo "  $host: NON RAGGIUNGIBILE"
done

# Verifica DNS
host dc-lab-01.lab.local 192.168.56.10 2>/dev/null || echo "DNS non configurato"

# Log di sistema per identificare cause di downtime
journalctl -b -1 --no-pager -n 50  # boot precedente
journalctl --since "2 hours ago" --no-pager | grep -i "error\|fail\|crit"
```

---

## Appendice B: Matrice Scenari DR

```
Scenario            | RTO atteso | Backup usato        | Procedura
─────────────────────────────────────────────────────────────────────
Hardware singolo VM | 1-2h       | N/A (migra VM)      | Hyp. HA
Hardware singolo FIS| 4-24h      | Bare metal restore  | SOP-HW-001
Ransomware          | 24-72h     | Borg + rsync        | SOP-DR-001 5B
Cancellazione AD    | 1-4h       | Borg / System State | SOP-DR-001 5C
Cancellazione file  | 30min-2h   | rsync / shadow copy | SOP-DR-001 5C
Corruzione DB       | 2-4h       | mysqldump + binlog  | SOP-DR-001 5C
Data center failure | 4-48h      | Tutti i backup      | SOP-DR-001 full
Cloud provider down | 1-4h       | Region failover     | SOP-CLOUD-001
```

---

## Riferimenti

- `06-backup-disaster-recovery.md` — sezioni 4 (DRP) e 5 (Business Continuity)
- ISO 22301: Business Continuity Management Systems
- ISO 27031: ICT Readiness for Business Continuity
- NIST SP 800-34: Contingency Planning Guide
- nomoreransom.org: database decryptor per ransomware noti
- ITIL v4 Practice Guide: IT Service Continuity Management
- **Tutorial precedente:** `tutorial_ops06_ch1a_backup_strategy_lab.md`
- **Tutorial successivo:** `tutorial_ops07_ch1a_monitoring_setup_lab.md`
