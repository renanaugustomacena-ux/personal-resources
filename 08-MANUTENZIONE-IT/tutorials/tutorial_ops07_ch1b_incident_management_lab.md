# Tutorial: Gestione Incidenti e Post-Mortem — Hands-On Lab

> **Documento di riferimento:** `07-monitoraggio-incidenti.md` (sezioni 4-5: Gestione Incidenti e Performance Monitoring)
> **Dominio:** IT Operations — Incident Management & Observability
> **Ambito:** Processo incident management (5 fasi), SEV1-SEV4 classificazione, War Room, ruoli, SLA risposta, template comunicazione, Post-Mortem blameless, capacity planning con PromQL, RED metrics, KPI MTTR/MTTA
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio-Avanzato — richiede ops07a (Monitoring Setup) e ops01b (ITIL Incident/Problem)
> **Prerequisiti:** Prometheus + Grafana attivi (da ops07a), GLPI operativo, conoscenza del processo ITIL incident
> **Ambiente:** SRV-LINUX-01 (script, GLPI), DC-LAB-01 (Windows Event Log per simulazione)

---

## Lab Environment Setup

```bash
# Su SRV-LINUX-01 — verifica prerequisiti per questo lab
echo "=== VERIFICA PREREQUISITI INCIDENT MANAGEMENT LAB ==="

# Prometheus attivo?
if curl -s --connect-timeout 5 http://localhost:9090/-/healthy 2>/dev/null | grep -q "Prometheus"; then
    echo "[OK] Prometheus attivo"
else
    echo "[WARN] Prometheus non attivo — completa ops07a prima di questo lab"
fi

# GLPI accessibile?
if curl -s --connect-timeout 5 http://localhost:8080/glpi 2>/dev/null | grep -q -i "glpi\|html"; then
    echo "[OK] GLPI raggiungibile"
else
    echo "[INFO] GLPI non raggiungibile — alcune esercitazioni useranno simulazioni"
fi

# Crea struttura directory per incident management
mkdir -p /incident-mgmt/{playbooks,postmortems,reports,templates}
echo ""
echo "Directory incident management:"
ls /incident-mgmt
```

```powershell
# Su DC-LAB-01 — verifica log di sicurezza (usato per simulare incident)
Write-Host "=== PREREQUISITI INCIDENT MANAGEMENT (DC-LAB-01) ==="
$secLog = Get-WinEvent -ListLog Security -ErrorAction SilentlyContinue
if ($secLog) {
    Write-Host "[OK] Security Event Log disponibile"
    Write-Host "     Dimensione: $([math]::Round($secLog.FileSize/1MB,1)) MB"
}
```

---

## PART A: FONDAMENTI — La Differenza tra Panico e Processo

> Quando il sistema più critico dell'azienda va giù alle 2 di notte, ci sono due possibili reazioni del team IT. Reazione senza processo: telefonate caotiche, "chi ha fatto cosa?", tre persone che lavorano sullo stesso problema senza coordinarsi, nessuno che aggiorna i clienti, nessuna documentazione di cosa è stato provato. Reazione con processo: l'alert automatico sveglia il tecnico on-call, viene dichiarato un incident SEV1 in 5 minuti, i ruoli sono assegnati, il Communications Lead invia il primo update agli stakeholder entro 30 minuti, lo Scribe documenta ogni azione, il sistema viene ripristinato in 90 minuti. La differenza non è la competenza tecnica — è il processo.

---

### Concetto A1: Le 5 Fasi dell'Incident Management

> **Analogia.** I pronto soccorso degli ospedali hanno un sistema di triage preciso: chi arriva viene valutato in pochi minuti, assegnato a una categoria di urgenza (codice rosso, giallo, verde, bianco), e trattato in base alla priorità clinica — non all'ordine di arrivo. Il triage previene che il medico passi un'ora con un'unghia incarnita mentre un paziente con infarto aspetta. L'incident management applica lo stesso principio all'IT: non tutti i problemi sono uguali, non tutte le risorse devono essere mobilitate per ogni problema.

**Le 5 fasi:**

```
FASE 1: DETECTION (Rilevazione)
  Come viene rilevato l'incident:
  → Alert automatico dal monitoraggio (PREFERITO — veloce)
  → Segnalazione utente via help desk (lenta — l'utente ha già il problema)
  → Controllo manuale di routine (fortuito)
  → Segnalazione fornitore
  
  Metrica chiave: TTD (Time To Detect)
  Target: < 5 minuti per SEV1 con monitoraggio
  
  SENZA monitoraggio: TTD tipico 30-60 minuti (quando l'utente chiama)
  CON monitoraggio:   TTD tipico 1-5 minuti (alert automatico)
  
  → Per questo investiamo in Prometheus + alert (ops07a)

FASE 2: TRIAGE (Classificazione)
  Assegna severità in 2-5 minuti:
  
  SEV1 (Critico):
    Servizio completamente down per tutti gli utenti
    O perdita dati in corso
    O violazione sicurezza confermata
    Risposta: IMMEDIATA, risorse massime, management notificato
    Esempio: database produzione inaccessibile, ransomware attivo
    
  SEV2 (Grave):
    Funzionalità critica degradata, workaround parziale disponibile
    Risposta: entro 15 minuti, team dedicato
    Esempio: tempi risposta 10x il normale, payment service intermittente
    
  SEV3 (Moderato):
    Funzionalità non critica impattata, workaround disponibile
    Risposta: entro 1 ora, orario lavorativo
    Esempio: report giornaliero fallito, un server su tre non funzionante
    
  SEV4 (Basso):
    Impatto minimo o funzionalità minore
    Risposta: entro 4 ore, pianificabile
    Esempio: errore formattazione report, lentezza sporadica

FASE 3: INVESTIGATION (Indagine)
  Domande strutturate da rispondere:
  "Quando è iniziato?" → guarda metriche Prometheus (punto di cambio)
  "Cosa è cambiato?" → deployment, patch, config, infrastruttura
  "Chi è impattato?" → tutti? alcuni? quale funzionalità?
  "Quali servizi dipendenti?" → tutto ciò che dipende dal servizio down
  
  Strumenti nel lab:
  → Prometheus: grafici CPU/RAM/disco al momento dell'incident
  → Windows Event Log: ID 4625 (login falliti), 7045 (nuovo servizio)
  → journalctl: log Linux con --since/-until
  → GLPI: history del CI colpito (modifiche recenti)

FASE 4: RESOLUTION (Risoluzione)
  Tipi di risoluzione:
  Fix immediato: risolvi la causa (riavvio, rollback, patch)
  Workaround: soluzione temporanea per ripristinare il servizio
               mentre lavori alla correzione definitiva
  Escalation: coinvolgi specialisti o vendor se necessario
  
  Metriche chiave:
  MTTA: Mean Time To Acknowledge (presa in carico)
  MTTR: Mean Time To Resolve (risoluzione completa)
  Target SEV1: MTTA < 5min, MTTR < 1h

FASE 5: POST-MORTEM
  Dopo ogni SEV1/SEV2 (obbligatorio) e SEV3 (raccomandato)
  → Blameless: non cerchi colpevoli, cerchi cause sistemiche
  → Template strutturato (vedremo in B4)
  → Action items assegnati con owner e deadline
  → Condivisione con tutto il team IT
```

---

### Concetto A2: La War Room — Risposta Coordinata

> **Analogia.** In una grande operazione chirurgica c'è un chirurgo che opera, un anestesista che monitora i parametri, un'infermiera che porta gli strumenti, un'altra che registra le azioni. Ognuno sa il proprio ruolo, nessuno si sovrappone, il chirurgo non deve rispondere al telefono. La War Room è la sala operatoria dell'incident management: ruoli chiari, comunicazione strutturata, nessuna distrazione.

**Struttura della War Room:**

```
RUOLI (assegnati entro 5 minuti dall'incident):

Incident Commander (IC):
  Non lavora tecnicamente — COORDINA
  → Decide le priorità delle azioni
  → Autorizza risorse (chiamare il vendor? riavviare in produzione?)
  → Dichiara la fine dell'incident
  → Una sola persona, non un comitato

Communications Lead:
  → Aggiornamenti periodici agli stakeholder (ogni 15-30 min per SEV1)
  → Gestisce la status page
  → Risponde alle domande di management/clienti
  → Prepara la comunicazione post-risoluzione

Technical Lead:
  → Guida l'analisi tecnica
  → Coordina i tecnici (non lavora da solo su tutto)
  → Aggiorna l'IC sullo stato
  → Decision maker tecnico

Scribe (Documentarista):
  → Scrive TUTTO in tempo reale:
    "14:32 - test rollback versione precedente"
    "14:35 - rollback fallito, errore di migrazione DB"
    "14:41 - tentativo restore database da backup"
  → Fondamentale per il post-mortem!
  → Può essere un tecnico non direttamente coinvolto

SME (Subject Matter Expert):
  → Specialista del sistema coinvolto
  → Chiamato in causa dall'IC quando necessario
  → Può essere remoto

CANALE DEDICATO:
  Crea un canale Slack/Teams specifico: #inc-2026-0715-glpi-down
  → Tutta la comunicazione tecnica in quel canale
  → Non in canali generici dove si perde nel rumore
  → Serve come log automatico dell'incident

CADENZA COMUNICAZIONI (per SEV1):
  T+0:   Alert rilevato
  T+5:   IC assegnato, war room attivata
  T+15:  Primo update stakeholder (stato: in indagine)
  T+30:  Update (stato: causa identificata / in corso fix)
  T+60:  Update o risoluzione
  Ogni 15m: update se ancora in corso
```

---

### Concetto A3: Il Post-Mortem Blameless

> **Analogia.** Quando un aereo ha un incidente, l'investigazione non si chiude con "il pilota ha sbagliato" — anche se tecnicamente il pilota ha fatto qualcosa di sbagliato. L'investigazione va più in profondo: perché il sistema ha permesso quell'errore? Perché la formazione non ha coperto quello scenario? Perché l'alert non ha funzionato? Il risultato non è la punizione del pilota, ma cambiamenti ai protocolli, ai sistemi di allerta, alla formazione — che rendono più difficile per qualsiasi pilota futuro fare lo stesso errore. Questo è il blameless post-mortem.

**Principi chiave:**

```
BLAMELESS = la persona non è la causa radice

  Sbagliato: "Mario ha cancellato la tabella sbagliata"
  Corretto:  "Il sistema permetteva a qualsiasi admin di
              eseguire DROP TABLE in produzione senza conferma"
  
  La differenza:
  Sbagliato → Mario ha paura, nasconde i problemi, le cause rimangono
  Corretto  → Il team rimuove il rischio sistemico, l'errore non si ripete

STRUTTURA POST-MORTEM:
  1. Riepilogo esecutivo (2-3 frasi)
  2. Impatto (durata, servizi, utenti, SLA violati)
  3. Timeline dettagliata (ogni azione con timestamp)
  4. Causa radice (NON "errore umano")
  5. Fattori contribuenti (cosa ha amplificato il problema)
  6. Cosa ha funzionato bene
  7. Cosa può essere migliorato
  8. Action items (owner, priorità, deadline)
  9. Lezioni apprese

QUANDO FARE IL POST-MORTEM:
  SEV1: SEMPRE, entro 2-3 giorni dall'incident
  SEV2: SEMPRE, entro 5 giorni
  SEV3: RACCOMANDATO se problemi ricorrenti
  
  Il post-mortem deve essere completato quando la memoria
  è ancora fresca — non 3 settimane dopo!
```

---

### Concetto A4: Metriche di Performance — RED Metrics e SLO

> **Analogia.** Un ristorante può misurare molte cose: temperatura cucina, numero di ingredienti in magazzino, ore lavorate dal personale. Ma il cliente lo giudica su tre cose: il cibo arriva? (Rate), il cibo è quello giusto? (Errors), arriva in tempo ragionevole? (Duration). Le RED metrics — Rate, Errors, Duration — sono il "ristorante" del tuo servizio: misurano esattamente quello che il cliente/utente sperimenta.

```
RED METRICS:
  Rate (Throughput): richieste al secondo → indicatore di carico
  Errors: % richieste che falliscono → indicatore di qualità
  Duration: tempo di risposta → indicatore di performance
  
  Come misurarle con Prometheus (se l'app espone metriche):
  
  Rate:
    sum(rate(http_requests_total[5m]))
    
  Error Rate:
    sum(rate(http_requests_total{status=~"5.."}[5m])) /
    sum(rate(http_requests_total[5m])) * 100
    
  Duration (P99):
    histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

CAPACITY PLANNING con predict_linear():
  # Disco si esaurirà in 30 giorni?
  predict_linear(node_filesystem_avail_bytes[7d], 30*24*3600) < 0
  
  # RAM trend — quando raggiungerà il 95%?
  # (richiederebbe calcolo inverso — usa Grafana con trend visivo)

KPI METRICHE INCIDENT:
  MTTA: Mean Time To Acknowledge
    Target SEV1: < 5 minuti
    Target SEV2: < 15 minuti
    
  MTTR: Mean Time To Resolve  
    Target SEV1: < 60 minuti
    Target SEV2: < 4 ore
    
  Incident Frequency: trend mensile incidenti per severità
    → in aumento? → problema sistemico da investigare
    → in diminuzione? → improvement actions efficaci
    
  False Positive Rate: % alert che non richiedevano azione
    → Target: < 5% (alert fatigue se > 20%)
```

---

### Concetto A5: SLA Interni e Comunicazione con il Business

> Un SLA (Service Level Agreement) interno non è solo una promessa formale — è un contratto di aspettative tra IT e business. Senza SLA, ogni incident diventa una negoziazione emotiva: il manager dice "è critico, risolvetelo adesso!", l'IT dice "stiamo lavorando", nessuno sa se il ritmo è accettabile. Con SLA definiti, tutti sanno: SEV2 = risolto entro 4 ore. Se siamo a 3 ore e non c'è fix, l'IC sa che deve escalare. Il business sa che può aspettarsi un aggiornamento ogni 30 minuti.

```
SLA DI RISPOSTA PER SEVERITÀ:

  Sev | ACK Target | Update Freq | Risoluzione Target
  ────────────────────────────────────────────────────
  1   | 5 min      | ogni 15 min | 1 ora
  2   | 15 min     | ogni 30 min | 4 ore
  3   | 1 ora      | ogni 2 ore  | 24 ore (business h.)
  4   | 4 ore      | giornaliero | 72 ore (business h.)

ESCALATION AUTOMATICA SE SLA VIOLATO:
  T+5 e SEV1 non acknowledgment → sveglia team lead
  T+60 e SEV1 non risolto → notifica IT Manager
  T+4h e SEV2 non risolto → notifica IT Manager

COMUNICAZIONE VERSO IL BUSINESS:
  Cosa il business vuole sapere (NON vuole dettagli tecnici):
  ✓ Cosa non funziona
  ✓ Chi è impattato
  ✓ Quando sarà risolto (stima realistica)
  ✓ Cosa può fare nel frattempo (workaround)
  
  Cosa NON scrivere nella comunicazione business:
  ✗ "Il container Docker ha un deadlock nel thread pool"
  ✗ "Stiamo analizzando il core dump"
  ✗ "Non sappiamo ancora la causa"
  
  Template business:
  "Il servizio [X] è attualmente non disponibile.
   Impatto: [descrizione utente-centrica]
   Workaround: [se disponibile]
   Stima ripristino: [ora/periodo]
   Prossimo aggiornamento: tra [X] minuti"
```

---

## PART B: OPERAZIONI — Gestire Incidenti nel Lab

---

### Esercizio B1: Simulare e Gestire un Incident SEV2

**Obiettivo.** Simulare un incident SEV2 (servizio GLPI degradato), seguire il processo completo di incident management e documentare ogni fase in GLPI.

**Background.** Questo esercizio simula la risposta a un servizio lento/degradato — lo scenario più comune nella vita reale. Non è un'interruzione completa (SEV1), ma abbastanza grave da richiedere una risposta strutturata.

**Step 1 — Rilevazione (T+0):**

```bash
# Su SRV-LINUX-01
# Simula alert da Prometheus: GLPI ha tempi di risposta elevati

echo "=== SIMULAZIONE ALERT GLPI DEGRADATO ===" 

# Genera artificialmente carico per simulare rallentamento
# (non modifica dati reali — solo carico CPU temporaneo)
echo "Simulazione carico sistema per 30 secondi..."
stress-ng --cpu 2 --timeout 30s 2>/dev/null &
STRESS_PID=$!

sleep 5

# Misura il tempo di risposta di GLPI in questo momento
echo ""
echo "Tempo risposta GLPI durante carico simulato:"
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" --connect-timeout 5 http://localhost:8080/glpi 2>/dev/null || echo "timeout")
echo "  Risposta: ${RESPONSE_TIME}s (normale < 1s, degradato > 2s)"

# Annota l'orario dell'alert
INCIDENT_START=$(date '+%Y-%m-%d %H:%M:%S')
echo ""
echo "=== ALERT GENERATO ==="
echo "Timestamp: $INCIDENT_START"
echo "Tipo: HTTP Response Time Alto"
echo "Servizio: GLPI (http://192.168.56.20:8080/glpi)"
echo "Valore: ${RESPONSE_TIME}s (soglia: > 2s)"
echo ""
echo "PROSSIMA AZIONE: classificazione incident (Triage)"

# Cleanup
wait $STRESS_PID 2>/dev/null || true
```

**Step 2 — Triage (T+2 minuti):**

```bash
echo "=== TRIAGE INCIDENT ==="
echo "Orario: $(date '+%H:%M:%S')"
echo ""

# Raccolta informazioni rapida per classificare
echo "DOMANDE DI TRIAGE:"
echo ""

echo "1. Chi è impattato?"
echo "   → Tutti gli utenti di GLPI o solo alcuni?"
GLPI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8080/glpi 2>/dev/null || echo "000")
echo "   → HTTP status: $GLPI_STATUS"
echo "   → Risposta: tutti (il servizio risponde ma lento)"
echo ""

echo "2. Workaround disponibile?"
echo "   → Sì: gli utenti possono usare GLPI lentamente"
echo "   → Gli utenti sono impattati ma non completamente bloccati"
echo ""

echo "3. Quante funzionalità critiche sono impattate?"
echo "   → Ticketing lento ma funzionante"
echo ""

echo "CLASSIFICAZIONE INCIDENT:"
echo "  SEVERITÀ: SEV2 (servizio critico degradato, workaround disponibile)"
echo "  MOTIVO: GLPI funziona ma lento, impatta produttività di TUTTI gli utenti"
echo "          Se fosse solo lentezza minima → SEV3"
echo "          Se non funzionasse del tutto → SEV1"
echo ""
echo "ASSEGNAZIONE RUOLI:"
echo "  Incident Commander: lab-admin"
echo "  Technical Lead: lab-admin (stesso in lab, in produzione persone diverse)"
echo "  Communications Lead: lab-admin"
echo "  Scribe: log scritto in questo script"

# Crea log incident
INCIDENT_ID="INC-$(date +%Y%m%d-%H%M)"
LOG_FILE="/incident-mgmt/reports/incident-$INCIDENT_ID.log"

cat > "$LOG_FILE" << EOF
=== INCIDENT LOG: $INCIDENT_ID ===
SEV: SEV2
Servizio: GLPI
Avvio: $INCIDENT_START
IC: lab-admin

TIMELINE:
$INCIDENT_START → RILEVAZIONE: alert tempo risposta GLPI > 2s
$(date '+%Y-%m-%d %H:%M:%S') → TRIAGE: classificato SEV2, IC assegnato
EOF

echo ""
echo "[OK] Log incident creato: $LOG_FILE"
```

**Step 3 — Investigazione (T+5 minuti):**

```bash
echo ""
echo "=== INVESTIGATION ==="
echo "Orario: $(date '+%H:%M:%S')"
echo ""

echo "Raccogliendo informazioni diagnostiche..."

# Check 1: risorse di sistema al momento dell'incident
echo "--- Risorse sistema ---"
echo "CPU load:"
uptime
echo ""
echo "Memoria:"
free -h | awk 'NR==1 || NR==2 {print $0}'
echo ""
echo "Disco:"
df -h / | awk 'NR==2 {print "Root:", $5, "usato"}'

# Check 2: processi che consumano più CPU
echo ""
echo "--- Top processi per CPU ---"
ps aux --sort=-%cpu | head -6 | awk '{printf "  %-20s %5s%%\n", $11, $3}'

# Check 3: log di sistema per errori recenti
echo ""
echo "--- Errori recenti nei log (ultimi 10 minuti) ---"
journalctl --since "10 minutes ago" --no-pager -q --priority=err 2>/dev/null | head -10 || echo "  Nessun errore critico nei log"

# Check 4: Docker containers (GLPI è in Docker)
echo ""
echo "--- Stato container Docker ---"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}" 2>/dev/null | head -10

# Check 5: Query Prometheus per identificare il punto di cambio
echo ""
echo "--- Query Prometheus: CPU nelle ultime 30 minuti ---"
echo "(apri http://192.168.56.20:9090 e cerca spike CPU)"
echo "Query: 100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[1m])) * 100)"

# Aggiorna log incident
cat >> "$LOG_FILE" << EOF
$(date '+%Y-%m-%d %H:%M:%S') → INVESTIGATION: avviata raccolta diagnostica
  CPU load: $(uptime | awk -F'load average: ' '{print $2}')
  RAM disponibile: $(free -m | awk 'NR==2 {print $7}') MB
  Container Docker: $(docker ps -q 2>/dev/null | wc -l) container running
EOF

echo ""
echo "=== IPOTESI DI CAUSA ==="
echo "  1. Carico CPU elevato (stress test o batch job) → verificare con top"
echo "  2. Memoria in esaurimento → verificare OOM killer in journalctl"
echo "  3. Disco GLPI pieno → verificare /var/lib/docker e /backup"
echo "  4. Problema rete interna → ping tra servizi"
```

**Step 4 — Risoluzione e chiusura:**

```bash
echo ""
echo "=== RESOLUTION ==="
echo "Orario: $(date '+%H:%M:%S')"

# Verifica che il carico simulato sia terminato
CURRENT_LOAD=$(uptime | awk -F'load average: ' '{print $2}' | awk -F',' '{print $1}')
echo "Load average attuale: $CURRENT_LOAD"

RESPONSE_TIME_NOW=$(curl -s -o /dev/null -w "%{time_total}" --connect-timeout 5 http://localhost:8080/glpi 2>/dev/null || echo "timeout")
echo "Tempo risposta GLPI: ${RESPONSE_TIME_NOW}s"

if (( $(echo "${RESPONSE_TIME_NOW:-99} < 2" | bc -l 2>/dev/null || echo 0) )); then
    RESOLUTION_STATUS="RISOLTO"
    echo "[OK] GLPI risponde normalmente"
else
    RESOLUTION_STATUS="MONITORAGGIO"
    echo "[INFO] GLPI ancora lento — monitorare per 10 minuti"
fi

RESOLUTION_TIME=$(date '+%Y-%m-%d %H:%M:%S')

# Aggiorna log incident
cat >> "$LOG_FILE" << EOF
$(date '+%Y-%m-%d %H:%M:%S') → CAUSA RADICE: carico CPU elevato (stress test simulato)
$(date '+%Y-%m-%d %H:%M:%S') → AZIONE: attesa termine processo di carico
$RESOLUTION_TIME → RISOLUZIONE: $RESOLUTION_STATUS (GLPI risponde in ${RESPONSE_TIME_NOW}s)
EOF

echo ""
echo "=== INCIDENT CHIUSO ==="
echo "Incident ID: $INCIDENT_ID"
echo "SEV: SEV2"
echo "Durata: stimata 15-30 minuti (simulazione accelerata)"
echo "Causa: carico CPU elevato → rallentamento applicativo"
echo "Risoluzione: terminazione processo causa carico"
echo ""
echo "PROSSIMI PASSI:"
echo "  1. Comunicazione chiusura agli stakeholder"
echo "  2. Apertura ticket in GLPI per documentazione"
echo "  3. Post-mortem (entro 5 giorni per SEV2)"
echo "  4. Action item: aggiungere alert processo stress-ng (o simile)"

# Leggi il log finale
echo ""
echo "=== LOG INCIDENT COMPLETO ==="
cat "$LOG_FILE"
```

**Checkpoint di verifica B1:**
- [ ] Incident rilevato e classificato SEV2 con motivazione
- [ ] Ruoli assegnati (IC, Technical Lead, Communications Lead, Scribe)
- [ ] Log incident creato con timeline
- [ ] Investigation completata con raccolta diagnostica
- [ ] Incident chiuso con causa documentata

---

### Esercizio B2: Aprire e Gestire Incident in GLPI

**Obiettivo.** Creare un ticket di incident in GLPI seguendo la procedura ITIL, assegnarlo correttamente, e documentare la risoluzione.

**Step 1 — Crea ticket incident in GLPI:**

```bash
# Su SRV-LINUX-01

echo "=== CREAZIONE INCIDENT IN GLPI ==="
echo "URL: http://192.168.56.20:8080/glpi"
echo ""
echo "PROCEDURA (interfaccia web GLPI):"
echo ""
echo "1. Login → lab-user (oppure admin per test)"
echo ""
echo "2. Menu: Assistenza → Crea ticket"
echo ""
echo "3. Compila il form:"
cat << 'EOF'
   Tipo:           Incident
   Titolo:         [INC-20260715-1432] GLPI risposta lenta - SEV2
   Categoria:      Hardware & Software → Servizi IT → GLPI
   
   Urgenza:        Alta (SEV2)
   Impatto:        Alto (tutti gli utenti GLPI impattati)
   Priorità:       Alta (calcolata automaticamente da urgenza+impatto)
   
   Descrizione:
   == INCIDENT SEV2 — GLPI Degradato ==
   Data/Ora rilevazione: 2026-07-15 14:32:00
   Rilevato da: Alert Prometheus (HTTP Response Time)
   
   SINTOMI:
   - GLPI risponde in > 3 secondi (normale: < 1s)
   - Tutti gli utenti impattati
   - Funzionalità disponibile ma degradata
   
   IMPATTO:
   - Rallentamento operazioni ticketing per tutti gli utenti
   - Stima: N utenti impattati
   
   WORKAROUND: sistema funziona, anche se lentamente
   
   AZIONI INIZIALI:
   - Verificato: CPU load elevato (causa: processo di carico)
   - Verificato: container Docker funzionanti
   
   Assegnato a: IT Operations Lab
   
4. Salva il ticket → otterrai ID (es: #42)
EOF

echo ""
echo "DOPO LA CREAZIONE DEL TICKET:"
echo ""
echo "5. Aggiungi followup man mano che l'incident evolve:"
echo "   Menu: Aggiornamento del ticket → Nuovo followup"
echo "   Testo: [HH:MM] Causa identificata: processo di carico CPU"
echo "          Azione: terminazione processo"
echo "          Stato: Fix in corso"
echo ""
echo "6. Chiudi il ticket a risoluzione:"
echo "   Soluzione: Il carico CPU era causato da [causa]."
echo "             Sistema ripristinato alle [ora]."
echo "             Durata incident: X minuti."
echo "             Causa radice: [descrizione]."
echo "   Stato: Risolto → Chiuso"
```

**Step 2 — Usa API GLPI per automazione (avanzato):**

```bash
echo ""
echo "=== CREAZIONE TICKET GLPI VIA API ==="
echo "Questo mostra come automatizzare la creazione ticket (es. da Alertmanager)"

# Ottieni il token di sessione GLPI
GLPI_URL="http://localhost:8080/glpi"
APP_TOKEN="TestAppToken123"   # configurato in GLPI → Setup → API

# Ottieni token sessione
SESSION_RESPONSE=$(curl -s -X GET \
    "$GLPI_URL/apirest.php/initSession" \
    -H "Content-Type: application/json" \
    -H "Authorization: user_token YourGLPIUserToken" \
    -H "App-Token: $APP_TOKEN" 2>/dev/null || echo '{}')

SESSION_TOKEN=$(echo "$SESSION_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_token',''))" 2>/dev/null)

if [[ -n "$SESSION_TOKEN" ]]; then
    echo "[OK] Sessione GLPI API aperta"
    
    # Crea ticket via API
    TICKET_RESPONSE=$(curl -s -X POST \
        "$GLPI_URL/apirest.php/Ticket" \
        -H "Content-Type: application/json" \
        -H "App-Token: $APP_TOKEN" \
        -H "Session-Token: $SESSION_TOKEN" \
        -d '{
            "input": {
                "name": "[AUTO] GLPI Response Time Alert - SEV2",
                "content": "Alert automatico da Prometheus\nTempo risposta > 2s\nSistema: GLPI\nValore: 3.2s",
                "urgency": 4,
                "impact": 4,
                "itilcategories_id": 1,
                "type": 1
            }
        }' 2>/dev/null || echo '{}')
    
    TICKET_ID=$(echo "$TICKET_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
    echo "[OK] Ticket #$TICKET_ID creato via API"
    
    # Chiudi sessione
    curl -s -X GET "$GLPI_URL/apirest.php/killSession" \
        -H "Session-Token: $SESSION_TOKEN" \
        -H "App-Token: $APP_TOKEN" > /dev/null
else
    echo "[INFO] API GLPI non configurata (normale nel lab)"
    echo "  Configurazione API: GLPI → Setup → API → Enable REST API"
    echo "  Poi crea un App Token e User Token"
    echo ""
    echo "  La procedura manuale (interfaccia web) è equivalente"
fi
```

**Checkpoint di verifica B2:**
- [ ] Ticket incident creato in GLPI con priorità Alta
- [ ] Ticket contiene: tipo, impatto, urgenza, descrizione strutturata
- [ ] Followup aggiunti durante la risoluzione
- [ ] Ticket chiuso con soluzione documentata

---

### Esercizio B3: Scrivere i Playbook — La Guida per le Emergenze

**Obiettivo.** Creare playbook per i 3 scenari di incident più comuni nel lab: host down, disco pieno, servizio non risponde.

**Background.** Un playbook è una procedura operativa specifica per uno scenario di incident. Non è un'enciclopedia — è una lista di controllo da seguire sotto pressione, in 3 ore di notte, quando si è mezzo addormentati. Deve essere essenziale, sequenziale, e portare alla risoluzione nel minor tempo possibile.

**Step 1 — Playbook: Host Down:**

```bash
cat > /incident-mgmt/playbooks/PB-001-host-down.md << 'EOF'
# PB-001: Host Non Raggiungibile

**Trigger alert:** `up == 0` per > 2 minuti
**SEV:** SEV1 se host Tier 1, SEV2 se host Tier 2
**Tempo stimato risoluzione:** 15 minuti (VM) → 2 ore (hardware fisico)

---

## STEP 1: VERIFICA (2 minuti)

```bash
# Ping da SRV-LINUX-01
ping -c 5 <IP_HOST>

# Se ping fallisce: è la rete o l'host?
ping -c 3 192.168.56.1   # gateway
```

☐ Ping risponde → problema del servizio, non dell'host → vai a PB-003
☐ Ping non risponde ma gateway OK → host down

## STEP 2: IDENTIFICA IL TIPO

☐ VM (VirtualBox/Proxmox/VMware)?
   - Apri console hypervisor
   - Verifica stato VM: running/stopped/paused
   - Se stopped: avvia la VM
   - Se paused: resume
   - Se running: accedi alla console → verifica kernel panic / OOM

☐ Server fisico?
   - Accedi all'iLO/iDRAC (console remota hardware)
   - Verifica indicatori LED (errore disco? memoria?)
   - Se necessario: accesso fisico in sala server

## STEP 3: VERIFICA POST-RIAVVIO

```bash
# Attendi 2 minuti dopo avvio, poi:
ping -c 3 <IP_HOST>
ssh lab-admin@<IP_HOST> 'uptime && systemctl list-units --failed'
```

☐ Sistema risponde
☐ Nessun servizio in failed
☐ Prometheus mostra host UP

## STEP 4: SE NON RISOLVIBILE IN 15 MINUTI

→ Escalation a Team Lead
→ Attiva DRP se host è Tier 1 (vedi DRP-LAB-v1.0.md)
→ Aggiornamento stakeholder

## DOCUMENTA NEL TICKET:

- Ora rilevazione
- Causa identificata (hardware/software/rete)
- Azione intrapresa
- Ora ripristino
- Post-mortem richiesto? (SEV1: sempre)
EOF

echo "[OK] Playbook PB-001 creato"
```

**Step 2 — Playbook: Disco Pieno:**

```bash
cat > /incident-mgmt/playbooks/PB-002-disco-pieno.md << 'EOF'
# PB-002: Disco in Esaurimento o Pieno

**Trigger alert:** utilizzo disco > 90% (CRITICAL) o > 80% (WARNING)
**SEV:** SEV1 se disco root pieno (sistema non funzionante), SEV2 se > 90%
**Tempo stimato risoluzione:** 10-30 minuti

---

## STEP 1: IDENTIFICAZIONE (1 minuto)

```bash
df -h
# Identifica quale filesystem è pieno
# Esempi comuni: /, /var, /var/log, /backup, /home
```

## STEP 2: TROVA I FILE GRANDI

```bash
# I 20 file più grandi sulla partizione interessata
du -sh /var/* 2>/dev/null | sort -rh | head -20

# Se /var/log è pieno:
du -sh /var/log/* | sort -rh | head -10
ls -lth /var/log/*.log | head -10

# Se è /var/lib/docker:
docker system df
```

## STEP 3: PULIZIA SICURA

```bash
# Log vecchi (sicuro)
journalctl --vacuum-size=500M
journalctl --vacuum-time=7d

# Log compressi (.gz) vecchi
find /var/log -name "*.gz" -mtime +30 -delete

# Cache APT (sicuro)
apt clean 2>/dev/null

# Docker: immagini/container/volumi non usati
docker system prune -f    # WARNING: rimuove immagini non taggate

# File temp abbandonati
find /tmp -mtime +3 -type f -delete
```

## STEP 4: VERIFICA

```bash
df -h   # Lo spazio è aumentato?
# Target: < 80% utilizzo dopo pulizia
```

## STEP 5: PREVENZIONE

```bash
# Aggiungi al backup_health.sh o monitoring: alert a 75% WARN
# Verifica retention log: /etc/logrotate.conf
# Considera espansione disco se crescita costante
```

## SE NON LIBERABILE IN 30 MINUTI:
→ Pulizia di emergenza più aggressiva (valuta con IC)
→ Espansione disco (richiede Change Request se in produzione)
→ Migrazione dati su storage aggiuntivo

## DOCUMENTA:
- Partizione colpita e % utilizzo al momento dell'alert
- Causa: log, Docker, backup, dati utente?
- GB liberati
- Azione preventiva pianificata
EOF

echo "[OK] Playbook PB-002 creato"
```

**Step 3 — Playbook: Servizio Non Risponde:**

```bash
cat > /incident-mgmt/playbooks/PB-003-servizio-giù.md << 'EOF'
# PB-003: Servizio Non Risponde (GLPI, MySQL, SSH, etc.)

**Trigger:** HTTP 5xx, TCP timeout, Uptime Kuma DOWN
**SEV:** SEV1 se Tier 1, SEV2 se Tier 2

---

## STEP 1: CLASSIFICA IL PROBLEMA

```bash
# Il host risponde al ping?
ping -c 3 <IP_HOST>

# Il porto TCP è aperto?
nc -zv <IP_HOST> <PORTA>   # es: nc -zv 192.168.56.20 8080

# Il servizio risponde a livello applicativo?
curl -sv http://<HOST>:<PORTA>/<endpoint>
```

## STEP 2: VERIFICA STATO SERVIZIO

```bash
# Linux (systemd)
systemctl status <nome-servizio>
journalctl -u <nome-servizio> -n 50

# Docker
docker ps | grep <container>
docker logs <container> --tail 50

# Windows (PowerShell su DC-LAB-01)
Get-Service -Name <NomeServizio> | Select-Object Status
Get-EventLog -LogName Application -Source <servizio> -Newest 10
```

## STEP 3: AZIONE PER TIPO

**Servizio crashato (ExitCode != 0):**
```bash
systemctl restart <servizio>
# Poi: systemctl status <servizio>   (deve essere active/running)
```

**Container Docker:**
```bash
docker restart <container>
docker logs <container> --tail 20
```

**Problema di dipendenza (DB non disponibile per l'app):**
```bash
# Verifica il servizio dipendente (es: MySQL per GLPI)
docker exec glpi-db mysql -uroot -p -e "SELECT 1" 2>/dev/null
# Se DB non risponde → vai a PB-002 per disco, o verifica credenziali
```

**Out of Memory (OOM):**
```bash
# Verifica dmesg per OOM killer
dmesg | grep -i "oom\|killed"
journalctl --since "1 hour ago" | grep -i "out of memory\|oom"
# Azione: libera RAM (riavvio servizi non essenziali) o aggiungi swap
```

## STEP 4: VERIFICA RIPRISTINO

```bash
# Verifica che il servizio risponda
curl -s -o /dev/null -w "%{http_code} %{time_total}s" http://<HOST>:<PORTA>
# Atteso: 200 < 2s
```

## STEP 5: PREVENZIONE

- Aggiungi healthcheck al container Docker
- Configura restart automatico: `systemctl enable <servizio>` o `restart: always` in docker
- Verifica limits di memoria (cgroups)
- Rivedi la causa nel post-mortem

## DOCUMENTA:
- Timestamp detection e risoluzione
- Causa: crash, OOM, dipendenza, configurazione
- Servizi impattati a cascata
- Azione applicata
EOF

echo "[OK] Playbook PB-003 creato"
echo ""
echo "=== PLAYBOOK DISPONIBILI ==="
ls -la /incident-mgmt/playbooks/
```

**Checkpoint di verifica B3:**
- [ ] PB-001 (host down) creato con 4 step diagnostici
- [ ] PB-002 (disco pieno) creato con comandi di pulizia
- [ ] PB-003 (servizio giù) creato con diagnosi per tipo
- [ ] Almeno un playbook testato sul lab (es. simulazione servizio down)

---

### Esercizio B4: Scrivere un Post-Mortem

**Obiettivo.** Scrivere un post-mortem blameless per l'incident simulato in B1, seguendo il template strutturato.

**Step 1 — Compila il post-mortem:**

```bash
# Su SRV-LINUX-01

cat > /incident-mgmt/postmortems/PIR-INC-$(date +%Y%m%d)-GLPI-LENTO.md << 'EOF'
# Post-Incident Review: GLPI Response Time Degraded

**Data Incidente:** 2026-07-15
**Durata:** 14:32 - 14:47 (15 minuti)
**Severità:** SEV2
**Incident Commander:** lab-admin
**Autore PIR:** lab-admin
**Data PIR:** 2026-07-17 (entro 5 giorni dall'incident)
**Partecipanti PIR:** lab-admin

---

## Riepilogo Esecutivo

Il servizio GLPI ha mostrato tempi di risposta superiori a 3 secondi (normale < 1s)
per un periodo di 15 minuti, impattando tutti gli utenti del sistema di ticketing.
La causa radice è stata un processo di carico CPU non pianificato (stress-ng) avviato
a scopo di test senza coordinamento con il team operativo.
Il servizio è stato ripristinato alla conclusione naturale del processo.

---

## Impatto

- **Durata totale:** 15 minuti
- **Servizi impattati:** GLPI (servizio di ticketing IT)
- **Utenti impattati:** Tutti gli utenti GLPI (stima: N utenti)
- **Funzionalità degradate:** Tutti i moduli GLPI (lentezza uniforme)
- **SLA violato:** Sì — tempo risposta > 2s per 15 minuti (soglia SLA: < 1s)
- **Impatto finanziario:** Trascurabile (laboratorio)

---

## Timeline Dettagliata

| Ora       | Evento |
|-----------|--------|
| 14:32:00  | Alert Prometheus generato: HTTP response time GLPI > 2s |
| 14:32:30  | lab-admin riceve notifica alert (Uptime Kuma) |
| 14:33:00  | Triage: classificato SEV2, ruoli assegnati |
| 14:34:00  | Investigation avviata: controllo risorse sistema |
| 14:35:00  | Identificato: CPU load 1.8 (elevato per 2 vCPU) |
| 14:36:00  | Identificato: processo stress-ng in esecuzione |
| 14:42:00  | Processo stress-ng terminato naturalmente |
| 14:43:00  | Verifica: GLPI risponde in 0.3s (normale) |
| 14:47:00  | Incident dichiarato RISOLTO |

**TTD (Time To Detect):** < 1 minuto (alert automatico Prometheus)
**MTTA (Time To Acknowledge):** 30 secondi
**MTTR (Time To Resolve):** 15 minuti

---

## Causa Radice

Un processo di stress test CPU (`stress-ng --cpu 2 --timeout 30s`) è stato avviato
su SRV-LINUX-01 senza preavviso al team, causando saturazione CPU e rallentamento
di tutti i servizi, incluso GLPI.

**Nota importante (blameless):** Il sistema non aveva alcun meccanismo che impedisse
l'avvio di processi ad alto consumo CPU in produzione. Non è "colpa" di chi ha avviato
il processo — il problema è che non esiste un processo di Change Management per i test
di carico, né un alert preventivo per CPU in rapida crescita.

---

## Fattori Contribuenti

1. **Assenza di processo Change Management per test di carico**
   Il team non aveva procedure per richiedere approvazione prima di eseguire test
   impattanti l'ambiente condiviso.

2. **Alert reattivo, non preventivo**
   L'alert scatta a 80% CPU dopo 5 minuti. Se scattasse a 60% con trend in aumento,
   darebbe più tempo per agire preventivamente.

3. **Finestra di manutenzione non definita**
   Test di carico dovrebbero avvenire in orari fuori dall'uso operativo del sistema.

---

## Cosa Ha Funzionato Bene

- Alert Prometheus rilevato l'incident in < 1 minuto (vs 30+ minuti senza monitoraggio)
- Triage completato rapidamente (< 2 minuti dall'alert)
- Investigation strutturata con diagnostica sistematica
- Log incident creato in tempo reale

---

## Cosa Può Essere Migliorato

- Nessun processo di Change Management per test di carico
- Alert CPU basato su soglia statica (80% per 5 min) — non rileva rampe rapide
- Nessuna correlazione automatica tra alert e processi in esecuzione

---

## Action Items

| # | Azione | Responsabile | Priorità | Scadenza | Stato |
|---|--------|--------------|----------|----------|-------|
| 1 | Creare SOP per test di carico (approvazione richiesta se CPU > 50% per > 5 min) | lab-admin | Alta | 2026-07-22 | Aperto |
| 2 | Aggiungere alert Prometheus per CPU in crescita rapida (trend > 20%/min) | lab-admin | Media | 2026-07-29 | Aperto |
| 3 | Definire finestre di manutenzione per test impattanti | lab-admin | Bassa | 2026-08-05 | Aperto |

---

## Lezioni Apprese

1. **Il monitoraggio automatico ha evitato un incident più grave**: senza Prometheus,
   l'incident sarebbe stato rilevato solo dagli utenti (TTD stimato: 15-30 minuti).
   Il valore del sistema di monitoraggio è stato confermato.

2. **Il processo strutturato riduce il tempo di risoluzione**: seguire il framework
   (triage → investigation → resolution) ha evitato azioni casuali e ha portato
   alla diagnosi corretta in 3 minuti.

3. **Test di carico non pianificati sono una minaccia reale**: in produzione, questo
   scenario accade con batch notturni, backup, job di indicizzazione. Il sistema di
   monitoraggio deve essere calibrato per rilevare queste situazioni.
EOF

echo "[OK] Post-mortem creato"
ls -la /incident-mgmt/postmortems/

echo ""
echo "=== RIEPILOGO POST-MORTEM ==="
head -5 /incident-mgmt/postmortems/PIR-INC-$(date +%Y%m%d)-GLPI-LENTO.md
```

**Checkpoint di verifica B4:**
- [ ] Post-mortem completo con tutte le 9 sezioni
- [ ] Timeline con timestamp reali dell'esercizio
- [ ] Causa radice formulata in modo blameless (sistema, non persona)
- [ ] Almeno 3 action items con owner e scadenza

---

### Esercizio B5: Dashboard Capacity Planning in Grafana

**Obiettivo.** Creare una dashboard Grafana di Capacity Planning con previsioni di crescita per disco e memoria.

**Step 1 — Query per capacity planning:**

```bash
# Su SRV-LINUX-01

echo "=== QUERY PROMQL PER CAPACITY PLANNING ==="
echo ""
echo "Queste query rispondono a: 'quando avremo un problema?'"
echo ""
echo "1. DISCO: si riempirà entro 7 giorni?"
echo "   predict_linear(node_filesystem_avail_bytes{mountpoint='/'}[6h], 7*24*3600) < 0"
echo ""
echo "   Risposta attuale:"
PRED_DISK=$(curl -s "http://localhost:9090/api/v1/query?query=predict_linear%28node_filesystem_avail_bytes%7Bmountpoint%3D%22%2F%22%7D%5B6h%5D%2C%207*24*3600%29" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('data',{}).get('result',[]); val=float(r[0]['value'][1]) if r else None; print(f'{val/1024/1024/1024:.2f} GB predetti disponibili tra 7gg' if val and val > 0 else 'ATTENZIONE: disco si riempirà entro 7 giorni!') if val is not None else print('N/A')" 2>/dev/null || echo "N/A")
echo "   $PRED_DISK"
echo ""

echo "2. RAM: utilizzo medio ultimi 7 giorni?"
echo "   avg_over_time((1 - node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes) * 100 [7d])"
echo ""
echo "3. TOP filesystem per utilizzo:"
echo "   topk(5, 100 - (node_filesystem_avail_bytes / node_filesystem_size_bytes * 100))"
echo ""

DISK_PCT=$(curl -s 'http://localhost:9090/api/v1/query?query=100%20-%20(node_filesystem_avail_bytes%7Bmountpoint%3D%22%2F%22%7D%20%2F%20node_filesystem_size_bytes%7Bmountpoint%3D%22%2F%22%7D%20*%20100)' 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('data',{}).get('result',[]); print(f'{float(r[0][\"value\"][1]):.1f}%' if r else 'N/A')" 2>/dev/null || echo "N/A")
echo "   Disco root attuale: $DISK_PCT"
```

**Step 2 — Crea dashboard Capacity Planning in Grafana:**

```bash
echo ""
echo "=== CREAZIONE DASHBOARD CAPACITY PLANNING ==="

# Crea dashboard via API Grafana
CAPACITY_DASHBOARD='{
  "dashboard": {
    "id": null,
    "title": "Capacity Planning — LAB",
    "description": "Dashboard per pianificazione capacità",
    "tags": ["capacity", "lab"],
    "timezone": "browser",
    "refresh": "1h",
    "panels": [
      {
        "id": 1,
        "title": "CPU Utilizzo — Trend 24h",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU% - {{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "max": 100,
            "min": 0,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": null, "color": "green"},
                {"value": 80, "color": "yellow"},
                {"value": 95, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "RAM Utilizzo — Trend 24h",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
            "legendFormat": "RAM% - {{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "max": 100,
            "min": 0
          }
        }
      },
      {
        "id": 3,
        "title": "Disco % per Partizione",
        "type": "gauge",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "100 - (node_filesystem_avail_bytes{fstype!~\"tmpfs|overlay|squashfs\"} / node_filesystem_size_bytes * 100)",
            "legendFormat": "{{instance}} {{mountpoint}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "max": 100,
            "min": 0,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": null, "color": "green"},
                {"value": 80, "color": "yellow"},
                {"value": 90, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 4,
        "title": "Previsione Disco Root (24h)",
        "type": "stat",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "predict_linear(node_filesystem_avail_bytes{mountpoint=\"/\"}[6h], 24*3600) / 1024 / 1024 / 1024",
            "legendFormat": "GB liberi tra 24h"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "GB",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": null, "color": "red"},
                {"value": 1, "color": "yellow"},
                {"value": 5, "color": "green"}
              ]
            }
          }
        }
      }
    ]
  },
  "overwrite": true,
  "folderId": 0
}'

DASH_RESULT=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -u "admin:Lab@2024!" \
    http://localhost:3000/api/dashboards/db \
    -d "$CAPACITY_DASHBOARD" 2>/dev/null || echo '{}')

if echo "$DASH_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('url',''))" 2>/dev/null | grep -q "/d/"; then
    DASH_URL=$(echo "$DASH_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('url',''))" 2>/dev/null)
    echo "[OK] Dashboard creata: http://192.168.56.20:3000$DASH_URL"
else
    echo "[INFO] Creazione via API non riuscita"
    echo "Crea manualmente in Grafana:"
    echo "  1. New Dashboard → Add visualization"
    echo "  2. Data source: Prometheus-Lab"
    echo "  3. Query: predict_linear(node_filesystem_avail_bytes{mountpoint='/'}[6h], 24*3600)"
    echo "  4. Title: 'Spazio disco tra 24h (GB)'"
    echo "  5. Unit: GB"
fi
```

**Checkpoint di verifica B5:**
- [ ] Dashboard Capacity Planning creata in Grafana
- [ ] Pannello previsione disco (predict_linear) configurato
- [ ] Query CPU e RAM trend 24h funzionanti
- [ ] Soglie di colore configurate (verde/giallo/rosso)

---

## PART C: SISTEMATIZZARE — Incident Management come Pratica Continua

---

### Progetto C1: SOP-INC-001 — Risposta agli Incidenti

```
Documento: SOP-INC-001
Titolo:    Procedura Standard di Risposta agli Incidenti
Versione:  1.0
Owner:     IT Operations

QUANDO USARE: ogni volta che un alert automatico o segnalazione utente
              indica un'interruzione o degradazione di un servizio IT

---

PASSO 1: TRIAGE (< 5 minuti dall'alert)

  [ ] Raccogli informazioni di base:
      - Quale servizio è impattato?
      - Quanti utenti?
      - Funzionalità completamente assente o solo degradata?
  
  [ ] Assegna severità:
      □ SEV1: servizio completamente down, tutti gli utenti
      □ SEV2: funzionalità critica degradata, workaround disponibile
      □ SEV3: funzionalità non critica, workaround disponibile
      □ SEV4: impatto minimo, pianificabile
  
  [ ] Assegna ruoli (SEV1/SEV2):
      IC: _______________
      Technical Lead: ___
      Comm. Lead: _______
      Scribe: ___________

PASSO 2: COMUNICAZIONE INIZIALE (< 15 minuti per SEV1, < 30 min per SEV2)

  Template (vedi sezione "Template" del DRP):
  SOGGETTO: [INCIDENT SEV{X}] {Servizio} — {Stato}

  [ ] Notifica agli stakeholder interni
  [ ] Aggiorna status page (Uptime Kuma: segna come "Down" o "Degraded")
  [ ] Crea canale dedicato: #inc-YYYYMMDD-{descrizione-breve}

PASSO 3: APERTURA TICKET GLPI

  [ ] Vai a: GLPI → Assistenza → Crea ticket
  [ ] Tipo: Incident
  [ ] Titolo: [INC-YYYYMMDD-HHMM] {Servizio} — SEV{X}
  [ ] Urgenza/Impatto: in base alla severità
  [ ] Descrizione: usa il template strutturato
  [ ] Ticket ID ottenuto: ___

PASSO 4: INVESTIGATION

  [ ] Quando è iniziato? (metriche Prometheus: cerca il punto di cambio)
  [ ] Cosa è cambiato? (deploy? patch? config?)
  [ ] Quale servizio dipendente?
  [ ] Consulta playbook applicabile:
      Host down → PB-001
      Disco pieno → PB-002
      Servizio giù → PB-003

PASSO 5: RISOLUZIONE

  [ ] Applica fix o workaround
  [ ] Verifica ripristino (monitor per 10 min dopo il fix)
  [ ] Aggiorna ticket GLPI con la soluzione
  [ ] Aggiorna stakeholder: comunicazione di risoluzione
  [ ] Segna Uptime Kuma come "Operational"

PASSO 6: POST-MORTEM

  SEV1: OBBLIGATORIO entro 2-3 giorni
  SEV2: OBBLIGATORIO entro 5 giorni
  SEV3: raccomandato se ricorrente

  [ ] Usa template PIR
  [ ] Invia a: tutto il team IT
  [ ] Action items: aggiungi a backlog GLPI (tipo: Problema o Change)
```

---

### Progetto C2: Script incident_report.sh

```bash
#!/usr/bin/env bash
# incident_report.sh — Genera report mensile degli incidenti
# Analizza i log in /incident-mgmt/reports/ e produce statistiche

set -euo pipefail

REPORTS_DIR="/incident-mgmt/reports"
POSTMORTEMS_DIR="/incident-mgmt/postmortems"
MONTH=$(date +%Y-%m)
OUTPUT="/incident-mgmt/reports/monthly-report-${MONTH}.txt"

echo "=== REPORT MENSILE INCIDENTI — $MONTH ===" | tee "$OUTPUT"
echo "Generato: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$OUTPUT"
echo "" | tee -a "$OUTPUT"

# ─── STATISTICHE INCIDENT ─────────────────────────────────────────
echo "INCIDENT APERTI NEL MESE:" | tee -a "$OUTPUT"
TOTAL=$(find "$REPORTS_DIR" -name "incident-INC-$(date +%Y%m)*.log" 2>/dev/null | wc -l)
echo "  Totale: $TOTAL" | tee -a "$OUTPUT"

# Conta per severità (dal nome file o contenuto)
SEV1=$(find "$REPORTS_DIR" -name "*.log" 2>/dev/null -newer /tmp -exec grep -l "SEV: SEV1" {} \; 2>/dev/null | wc -l)
SEV2=$(find "$REPORTS_DIR" -name "*.log" 2>/dev/null -exec grep -l "SEV: SEV2" {} \; 2>/dev/null | wc -l)
echo "  SEV1: $SEV1 | SEV2: $SEV2" | tee -a "$OUTPUT"

# ─── POST-MORTEM COMPLETATI ────────────────────────────────────────
echo "" | tee -a "$OUTPUT"
echo "POST-MORTEM COMPLETATI:" | tee -a "$OUTPUT"
PIR_COUNT=$(find "$POSTMORTEMS_DIR" -name "PIR-INC-$(date +%Y%m)*.md" 2>/dev/null | wc -l)
echo "  $PIR_COUNT post-mortem scritti questo mese" | tee -a "$OUTPUT"

if [[ "$SEV1" -gt 0 && "$PIR_COUNT" -lt "$SEV1" ]]; then
    echo "  [WARN] Non tutti i SEV1 hanno un post-mortem!" | tee -a "$OUTPUT"
fi

# ─── METRICHE PROMETHEUS PER AVAILABILITY ─────────────────────────
echo "" | tee -a "$OUTPUT"
echo "DISPONIBILITÀ SERVIZI (da Prometheus):" | tee -a "$OUTPUT"

UPTIME_PCT=$(curl -s "http://localhost:9090/api/v1/query?query=avg_over_time(up[30d])*100" 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); results=d.get('data',{}).get('result',[]); [print(f'  {r[\"labels\"].get(\"job\",\"unknown\")}: {float(r[\"value\"][1]):.2f}%') for r in results]" 2>/dev/null || \
    echo "  (Prometheus non disponibile)")

echo "$UPTIME_PCT" | tee -a "$OUTPUT"

# ─── ACTION ITEMS PENDENTI ─────────────────────────────────────────
echo "" | tee -a "$OUTPUT"
echo "ACTION ITEMS APERTI DAI POST-MORTEM:" | tee -a "$OUTPUT"
OPEN_ITEMS=$(grep -r "| Aperto" "$POSTMORTEMS_DIR" 2>/dev/null | wc -l)
echo "  $OPEN_ITEMS action item ancora aperti" | tee -a "$OUTPUT"

if [[ "$OPEN_ITEMS" -gt 0 ]]; then
    echo "  Dettaglio:" | tee -a "$OUTPUT"
    grep -r "| Aperto" "$POSTMORTEMS_DIR" 2>/dev/null | \
        sed 's/.*\/PIR-/  PIR-/; s/.md:.*//' | \
        head -10 | tee -a "$OUTPUT"
fi

echo "" | tee -a "$OUTPUT"
echo "Report completato: $OUTPUT"
cat "$OUTPUT"
```

**Installazione:**

```bash
sudo cp /tmp/incident_report.sh /usr/local/bin/incident_report.sh 2>/dev/null || \
    sudo install -m 755 <(cat /tmp/incident_report.sh) /usr/local/bin/incident_report.sh 2>/dev/null || \
    echo "Copia manuale richiesta"

echo "Crontab per report mensile automatico (primo giorno del mese alle 09:00):"
echo "0 9 1 * * lab-admin /usr/local/bin/incident_report.sh > /var/log/incident_report.log 2>&1"
```

---

### Progetto C3: Integrazione ITIL — Problem Management e Knowledge Base

```
ITIL v4 PRACTICE: Incident Management + Problem Management

IL CICLO CONTINUO:

  Incident → Risolto → Post-Mortem → Action Items → Problem Management
  
  INCIDENT: "GLPI risponde lento"
    → Risolto: "terminato processo di carico"
    → Ma la causa radice (stress test non pianificato) non è risolta
    
  PROBLEM: creato quando un incident ha causa radice non ancora rimossa
    → In GLPI: tipo "Problema" invece di "Incident"
    → Collegato all'incident originale
    → Assegnato al team con skill appropriate
    → Chiuso quando la causa radice è permanentemente rimossa
    
    Esempio:
    Incident INC-001: "GLPI lento"
    Problem PB-001: "Mancanza procedura test di carico"
    Action: "Creare SOP test di carico"
    Change: "Implementare procedura approvazione test carico"
    
  KNOWN ERROR DATABASE (KED):
    Quando un problema è noto ma non ancora risolto,
    crea un Known Error in GLPI:
    → Soluzione temporanea documentata
    → Trigger automatico: se INC simile arriva → copia la soluzione temporanea
    → Risparmia tempo nella risposta a incident ricorrenti

KNOWLEDGE BASE IN GLPI:
  
  Menu: Strumenti → Knowledge Base
  
  Crea articoli per:
  1. "Come rispondere a un alert di disco pieno" → PB-002 come articolo KB
  2. "Procedura post-mortem" → template PIR come articolo KB
  3. "Contatti emergenza" → lista contatti da /dr/contact-list.txt
  4. "RTO/RPO per sistema" → BIA da ops06b
  
  Quando un tecnico riceve un incident simile a uno storico,
  cerca in KB prima di reinventare la soluzione!

METRICHE ITIL CHIAVE DA MONITORARE (dashboard Grafana):

  MTTR per SEV:
    (richiede calcolo manuale dai log o integrazione GLPI→Prometheus)
    
  FCR (First Call Resolution):
    % incident risolti al primo contatto senza escalation
    Target: > 70%
    
  Backlog Incident:
    Incident aperti da > SLA target → richiedono attenzione immediata
    
  Problem-to-Incident Ratio:
    % incident derivanti da problemi noti → se alto: KB non viene usata
    Target: < 20%
```

---

## Checklist di Validazione Lab — ops07b

```
FONDAMENTI (Part A):
  [ ] A1: Conosci le 5 fasi dell'incident management con metriche chiave (TTD, MTTR)
  [ ] A2: Sai i 4 livelli SEV con criteri di classificazione ed esempi
  [ ] A3: Sai la struttura della war room (4 ruoli principali con responsabilità)
  [ ] A4: Conosci i principi del blameless post-mortem
  [ ] A5: Sai cosa sono le RED metrics e come si collegano agli SLA

OPERAZIONI (Part B):
  [ ] B1: Incident SEV2 simulato con triage, investigation, resolution e log
  [ ] B2: Ticket GLPI creato con struttura corretta (tipo, urgenza, impatto, descrizione)
  [ ] B3: Almeno 2 playbook creati in /incident-mgmt/playbooks/
  [ ] B4: Post-mortem blameless scritto con causa radice e action items
  [ ] B5: Dashboard Capacity Planning in Grafana con predict_linear()

SISTEMATIZZARE (Part C):
  [ ] C1: SOP-INC-001 letta e compresa
  [ ] C2: Script incident_report.sh installato
  [ ] C3: Almeno un articolo di Knowledge Base creato in GLPI
```

---

## Appendice A: Template Comunicazioni

**Notifica interna SEV1:**
```
[INCIDENT SEV1] {Servizio} — COMPLETAMENTE DOWN

Orario rilevazione: {HH:MM}
Incident Commander: {nome}
Canale: #{canale-incident}

IMPATTO: {servizio} non disponibile per TUTTI gli utenti
CAUSA: In indagine
WORKAROUND: Nessuno disponibile

AZIONI:
  - IC assegnato e war room attiva
  - Investigation in corso

PROSSIMO AGGIORNAMENTO: tra 15 minuti
```

**Notifica chiusura:**
```
[RESOLVED SEV{X}] {Servizio} — Ripristinato

Ora ripristino: {HH:MM}
Durata incident: {X} minuti

CAUSA: {descrizione breve causa radice}
AZIONE: {cosa è stato fatto}

Post-mortem pianificato entro {data}.
Grazie per la pazienza.

IT Operations
```

---

## Riferimenti

- `07-monitoraggio-incidenti.md` — sezioni 4 (gestione incidenti) e 5 (performance)
- ITIL v4 Practice Guide: Incident Management
- Google SRE Book: Chapter 14 (Managing Incidents)
- PagerDuty Incident Response Guide (open source): response.pagerduty.com
- **Tutorial precedente:** `tutorial_ops07_ch1a_monitoring_setup_lab.md`
- **Tutorial successivo:** `tutorial_ops08_ch1a_asset_lifecycle_lab.md`
