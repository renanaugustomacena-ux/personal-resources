---
corso: "Gestione Piattaforme e DevOps"
fase: "8 — Riferimenti"
modulo: 18
titolo: "Troubleshooting e Guide Pratiche"
versione: "kubectl 1.30; Kubernetes 1.30; Helm 3.15"
livello: "Avanzato"
prerequisiti: ["05-kubernetes", "08-monitoring-observability", "07-ci-cd"]
obiettivi:
  - "Applicare una metodologia strutturata di troubleshooting per incidenti su Kubernetes"
  - "Diagnosticare CrashLoopBackOff, OOMKilled e failure di scheduling con kubectl"
  - "Risolvere problemi di networking K8s tramite nslookup, netcat e NetworkPolicy"
  - "Costruire runbook operativi e checklist di production readiness"
  - "Eseguire post-mortem blameless e migliorare la resilienza del sistema"
tag: [troubleshooting, kubectl, crashloopbackoff, oomkilled, runbook, post-mortem, production-readiness]
---

# Troubleshooting e Guide Pratiche — Documentazione Completa

> **Modulo 18** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al completamento di questo modulo sarai in grado di:
> 1. Applicare una metodologia strutturata di troubleshooting per incidenti su Kubernetes.
> 2. Diagnosticare CrashLoopBackOff, OOMKilled e failure di scheduling con kubectl.
> 3. Risolvere problemi di networking K8s tramite nslookup, netcat e NetworkPolicy.
> 4. Costruire runbook operativi e checklist di production readiness.
> 5. Eseguire post-mortem blameless e migliorare la resilienza del sistema.

## Idee guida

1. **`kubectl describe` + `logs` + `events` = first three commands.**
2. **K8s CrashLoopBackOff: leggere logs, exitcode, prevPod.**
3. **OOMKilled = limit memory troppo basso; raise OR fix leak.**
4. **Network issue K8s: `nslookup`, `nc`, NetworkPolicy verify.**


## Indice

1. [Metodologia di Troubleshooting](#1-metodologia-di-troubleshooting)
2. [Incident Management](#2-incident-management)
3. [Troubleshooting Kubernetes](#3-troubleshooting-kubernetes)
4. [Troubleshooting Docker e Container](#4-troubleshooting-docker-e-container)
5. [Troubleshooting Cloud (AWS/Azure/GCP)](#5-troubleshooting-cloud-awsazuregcp)
6. [Troubleshooting Database](#6-troubleshooting-database)
7. [Troubleshooting Networking](#7-troubleshooting-networking)
8. [Troubleshooting CI/CD Pipeline](#8-troubleshooting-cicd-pipeline)
9. [Runbook Template e Esempi](#9-runbook-template-e-esempi)
10. [Capacity Planning](#10-capacity-planning)
11. [Cost Optimization](#11-cost-optimization)
12. [Disaster Recovery](#12-disaster-recovery)
13. [Checklist Operative](#13-checklist-operative)
14. [Chaos Engineering](#14-chaos-engineering)
15. [Observability-Driven Debugging](#15-observability-driven-debugging)
16. [SLO, Error Budget e Affidabilita'](#16-slo-error-budget-e-affidabilita)

---

## 1. Metodologia di Troubleshooting

### Approccio Sistematico

Il troubleshooting efficace non e' un processo casuale ma una disciplina ingegneristica. Ogni problema tecnico richiede un metodo strutturato che riduca il tempo di risoluzione e prevenga interventi controproducenti.

**Le cinque fasi fondamentali:**

1. **Osservazione** — Raccogliere tutti i dati disponibili prima di formulare qualsiasi ipotesi. Leggere log, metriche, alert, e raccogliere testimonianze dagli utenti o dal team che ha rilevato il problema.
2. **Ipotesi** — Formulare ipotesi ordinate per probabilita'. Non partire dalla causa meno probabile. Considerare le modifiche recenti come prima causa sospetta.
3. **Test** — Verificare ogni ipotesi in modo isolato, modificando una sola variabile alla volta. Documentare ogni test eseguito e il suo risultato.
4. **Verifica** — Confermare che la soluzione applicata risolve effettivamente il problema senza introdurne di nuovi.
5. **Documentazione** — Registrare causa radice, soluzione, e lezioni apprese per il knowledge base del team.

### Binary Search Method

Il metodo binary search applicato al troubleshooting dimezza lo spazio di ricerca ad ogni iterazione. E' particolarmente efficace per problemi in pipeline complesse o catene di servizi.

```
Esempio pratico — Pipeline con 8 servizi:

Richiesta -> A -> B -> C -> D -> E -> F -> G -> H -> Risposta

Passo 1: Verificare il punto medio (D)
  - Se D riceve dati corretti -> il problema e' in E-H
  - Se D riceve dati errati -> il problema e' in A-D

Passo 2: Verificare il nuovo punto medio
  - Se il problema e' in A-D, verificare B
  - Se il problema e' in E-H, verificare F

Passo 3: Convergere sulla causa
  - Iterare finche' non si isola il singolo componente difettoso
```

**Complessita':** O(log n) iterazioni per identificare il componente difettoso su n componenti.

### Divide and Conquer

Separare il sistema in sottosistemi indipendenti e testarli isolatamente:

```bash
# Verificare se il problema e' nel frontend o nel backend
curl -v https://api.example.com/health

# Verificare se il problema e' nel database o nell'applicazione
psql -h db-host -U app_user -c "SELECT 1;"

# Verificare se il problema e' nella rete o nel servizio
ping -c 5 service-host
telnet service-host 8080
```

### Common Sense Approach

Prima di entrare in analisi complesse, verificare le cause piu' frequenti:

- **Il servizio e' in esecuzione?** `systemctl status <service>`
- **C'e' spazio su disco?** `df -h`
- **La memoria e' esaurita?** `free -h`
- **Ci sono stati deployment recenti?** `git log --oneline -5`
- **Il DNS risolve correttamente?** `dig service.example.com`
- **I certificati sono scaduti?** `openssl s_client -connect host:443 2>/dev/null | openssl x509 -noout -dates`
- **Ci sono state modifiche infrastrutturali recenti?** Controllare il changelog IaC.

### Layer-Based Troubleshooting

Analizzare il problema partendo dal livello piu' basso dello stack e salire progressivamente:

```
Layer 1 - Physical / Hardware
  - Connettivita' di rete fisica
  - Stato dei dischi (SMART status)
  - Utilizzo CPU/RAM hardware
  Comandi: dmesg, lspci, smartctl, sensors

Layer 2 - Network
  - Connettivita' IP, routing, firewall
  - DNS resolution
  - TLS/SSL handshake
  Comandi: ip addr, ip route, iptables -L, ss -tlnp, dig, traceroute

Layer 3 - Operating System
  - Stato dei servizi
  - Limiti di sistema (file descriptors, processi)
  - Kernel logs
  Comandi: systemctl, ulimit -a, journalctl, sysctl -a

Layer 4 - Application
  - Log applicativi
  - Configurazione
  - Dipendenze esterne
  Comandi: tail -f /var/log/app.log, env, curl health endpoints

Layer 5 - Data
  - Integrita' dei dati
  - Connettivita' database
  - Stato replicazione
  Comandi: psql, mysql, redis-cli, mongo
```

### Timeline Analysis

Costruire una timeline degli eventi per correlare cause ed effetti:

```
Esempio di timeline analysis:

14:00 - Deploy versione 2.3.1 in produzione
14:05 - Primo alert: latenza p99 > 2s su servizio orders
14:08 - Alert: errori 5xx in aumento (>1% delle richieste)
14:10 - Alert: connessioni database al 95% del pool
14:12 - Incident dichiarato - SEV2
14:15 - Correlazione: il deploy ha introdotto una query N+1
14:20 - Rollback alla versione 2.3.0
14:22 - Metriche in recupero
14:30 - Incident risolto
```

### Correlation Analysis

Sovrapporre metriche di sistemi diversi per identificare correlazioni:

```bash
# Esportare metriche CPU con timestamp
sar -u 1 60 > cpu_metrics.log

# Esportare metriche di rete con timestamp
sar -n DEV 1 60 > network_metrics.log

# Confrontare i timestamp dei picchi di latenza con le metriche di sistema
# In Grafana: sovrapporre dashboard di applicazione, infrastruttura e database
```

### Reproducing the Issue

Un problema che non si puo' riprodurre e' un problema che non si puo' risolvere con certezza:

```bash
# Riprodurre load conditions
ab -n 10000 -c 100 https://api.example.com/endpoint

# Riprodurre condizioni di memoria limitata
stress-ng --vm 2 --vm-bytes 80% --timeout 60s

# Riprodurre condizioni di rete degradata
tc qdisc add dev eth0 root netem delay 200ms loss 5%

# Rimuovere condizioni simulate
tc qdisc del dev eth0 root
```

### Documenting Findings

Ogni sessione di troubleshooting deve produrre documentazione strutturata:

```markdown
## Incident Report - [TITOLO]

**Data:** YYYY-MM-DD
**Durata:** HH:MM - HH:MM
**Severity:** SEV1/SEV2/SEV3/SEV4
**Impatto:** Descrizione dell'impatto sugli utenti

### Causa Radice
Descrizione tecnica della causa

### Timeline
- HH:MM - Evento
- HH:MM - Azione

### Risoluzione
Passi eseguiti per risolvere

### Azioni Preventive
- [ ] Azione 1
- [ ] Azione 2
```

### Criteri di Escalation

Definire chiaramente quando escalare un problema:

| Condizione | Azione |
|---|---|
| Impatto su >50% degli utenti | Escalare immediatamente a SEV1 |
| Nessun progresso dopo 30 minuti | Coinvolgere il team successivo nella matrice |
| Problema in area non di competenza | Escalare al team proprietario del componente |
| Rischio di perdita dati | Escalare a database team e management |
| Problema di sicurezza | Escalare a security team immediatamente |

---

## 2. Incident Management

### Incident Lifecycle

Un incident attraversa fasi ben definite, ognuna con responsabilita' e output specifici:

```
Detection -> Triage -> Response -> Resolution -> Post-Mortem

Detection:
  - Alerting automatico (Prometheus, Datadog, CloudWatch)
  - Segnalazione utente (ticket, chiamata)
  - Monitoraggio proattivo (dashboard review)

Triage:
  - Valutazione dell'impatto
  - Assegnazione della severity
  - Notifica agli stakeholder appropriati

Response:
  - Attivazione del team di risposta
  - Comunicazione iniziale (interna ed esterna)
  - Inizio delle attivita' di diagnosi e mitigazione

Resolution:
  - Applicazione della soluzione (fix o workaround)
  - Verifica del ripristino
  - Comunicazione di risoluzione

Post-Mortem:
  - Analisi della causa radice
  - Identificazione delle azioni preventive
  - Condivisione delle lezioni apprese
```

### Severity Levels

| Livello | Definizione | Impatto | SLA Risposta | SLA Risoluzione |
|---|---|---|---|---|
| **SEV1** | Critical — Servizio completamente non disponibile | Tutti gli utenti impattati, perdita di revenue | 5 minuti | 1 ora |
| **SEV2** | Major — Funzionalita' critica degradata significativamente | >30% utenti impattati, funzionalita' core compromesse | 15 minuti | 4 ore |
| **SEV3** | Minor — Funzionalita' non critica degradata | <30% utenti impattati, workaround disponibile | 30 minuti | 24 ore |
| **SEV4** | Low — Problema minore senza impatto operativo significativo | Singoli utenti, problema cosmetico o di performance minore | 4 ore | 72 ore |

**Esempi concreti per severity:**

- **SEV1:** Sito e-commerce completamente down, API di pagamento non funzionante, data breach attivo
- **SEV2:** Checkout funziona ma con errori intermittenti (30% failure rate), ricerca prodotti non disponibile
- **SEV3:** Pagina profilo utente lenta (>5s), notifiche email in ritardo di 30 minuti
- **SEV4:** Typo nella UI, colore sbagliato su un bottone, log verbosity troppo alta

### Incident Commander Role

L'Incident Commander (IC) e' il coordinatore centrale durante un incident:

**Responsabilita':**
- Dichiarare ufficialmente l'incident e la severity
- Coordinare i team coinvolti
- Gestire la comunicazione (delegare se necessario)
- Prendere decisioni operative (rollback, failover, escalation)
- Garantire che i ruoli siano assegnati: IC, Communications Lead, Operations Lead
- Avviare il processo di post-mortem dopo la risoluzione

**Regole per l'IC:**
- L'IC NON esegue diagnosi o fix direttamente — coordina
- L'IC puo' essere trasferito ad un'altra persona con handoff esplicito
- L'IC ha autorita' decisionale durante l'incident
- L'IC documenta le decisioni prese e le motivazioni

### Communication Templates

**Template notifica interna (Slack/Teams):**

```
🔴 INCIDENT DICHIARATO — SEV[N]

Servizio: [nome servizio]
Impatto: [descrizione impatto utenti]
Inizio: [timestamp]
IC: [nome]
Canale war room: #inc-YYYYMMDD-[breve-descrizione]

Stato: Indagine in corso
Prossimo aggiornamento: [timestamp + 30min]
```

**Template aggiornamento status page (esterno):**

```
[Investigating] Stiamo investigando un problema che impatta
[nome funzionalita']. Alcuni utenti potrebbero riscontrare
[sintomo]. Il nostro team sta lavorando attivamente alla risoluzione.

[Identified] Abbiamo identificato la causa del problema con
[nome funzionalita']. Stiamo applicando una soluzione.

[Monitoring] La soluzione e' stata applicata. Stiamo monitorando
la situazione per confermare il ripristino completo.

[Resolved] Il problema con [nome funzionalita'] e' stato risolto.
Il servizio e' tornato alla piena operativita'. Ci scusiamo per
l'inconveniente.
```

### War Room Procedures

```
1. Apertura war room
   - Creare canale dedicato: #inc-YYYYMMDD-descrizione
   - Invitare: IC, team on-call, stakeholder tecnici
   - Pinare il messaggio iniziale con contesto e severity

2. Regole del war room
   - Solo comunicazione rilevante all'incident
   - Usare thread per discussioni parallele
   - Aggiornamenti di stato ogni 15-30 minuti dall'IC
   - Nessuna speculazione — solo fatti e ipotesi dichiarate

3. Chiusura war room
   - IC dichiara la risoluzione
   - Messaggio finale con summary e prossimi passi
   - Canale archiviato dopo il post-mortem
```

### Escalation Matrix

```
Tempo trascorso | SEV1                    | SEV2                  | SEV3
0 min           | On-call engineer        | On-call engineer      | On-call engineer
15 min          | Team lead + IC          | Team lead             | -
30 min          | Engineering manager     | IC assegnato          | Team lead
1 ora           | VP Engineering + CTO    | Engineering manager   | -
2 ore           | CEO informato           | VP Engineering        | Engineering manager
```

### Handoff Procedures

Quando un incident supera il turno di un ingegnere:

```
Checklist di handoff:
1. Briefing verbale (5-10 minuti) con il successore
2. Documento scritto con:
   - Stato attuale dell'incident
   - Ipotesi investigate (confermate e scartate)
   - Azioni in corso
   - Prossimi passi pianificati
   - Contatti coinvolti
3. Trasferimento formale del ruolo IC (se applicabile)
4. Aggiornamento nel canale incident
```

### Incident Metrics

| Metrica | Definizione | Target |
|---|---|---|
| **MTTD** (Mean Time To Detect) | Tempo tra l'inizio del problema e la sua rilevazione | < 5 minuti |
| **MTTA** (Mean Time To Acknowledge) | Tempo tra la rilevazione e il primo intervento umano | < 15 minuti |
| **MTTR** (Mean Time To Resolve) | Tempo tra la rilevazione e la risoluzione completa | Dipende dalla severity |
| **MTTF** (Mean Time To Failure) | Tempo medio tra due failure dello stesso tipo | In aumento (obiettivo) |

```bash
# Query di esempio per calcolare MTTR da un database di incident
SELECT
  severity,
  AVG(EXTRACT(EPOCH FROM (resolved_at - detected_at))) / 60 AS avg_mttr_minutes,
  PERCENTILE_CONT(0.95) WITHIN GROUP (
    ORDER BY EXTRACT(EPOCH FROM (resolved_at - detected_at))
  ) / 60 AS p95_mttr_minutes
FROM incidents
WHERE resolved_at IS NOT NULL
  AND detected_at >= NOW() - INTERVAL '90 days'
GROUP BY severity
ORDER BY severity;
```

### Post-Mortem Blameless — Guida Approfondita

Il post-mortem blameless e' il pilastro della cultura SRE moderna. Un post-mortem efficace non cerca colpevoli, ma identifica le condizioni sistemiche che hanno permesso all'incidente di verificarsi. L'obiettivo e' trasformare l'outage di un singolo team in un miglioramento condiviso che riduca la probabilita' che lo stesso pattern di failure colpisca un altro servizio il mese successivo.

#### Prerequisiti Culturali

La sicurezza psicologica e' il fondamento. Quando un VP of Engineering dichiara pubblicamente "questo e' il deployment che ho approvato e che ha contribuito all'outage di martedi', ed ecco cosa sto cambiando nel mio processo di review", l'impatto sulla sicurezza psicologica e' maggiore di qualsiasi comunicazione formale sulla cultura blameless. La leadership deve modellare l'onesta' per prima.

#### Tecnica dei 5 Whys (Five Whys)

La tecnica dei 5 Whys, originata dal Toyota Production System, consiste nel chiedere iterativamente "perche'?" fino a raggiungere la causa radice sistemica:

```
Esempio pratico:

1. PERCHE' il sito era down?
   -> Perche' il servizio API ha smesso di rispondere.

2. PERCHE' il servizio API ha smesso di rispondere?
   -> Perche' le connessioni al database erano esaurite.

3. PERCHE' le connessioni erano esaurite?
   -> Perche' una query lenta teneva le connessioni aperte per minuti.

4. PERCHE' la query era lenta?
   -> Perche' una migrazione ha rimosso un indice critico senza che nessuno se ne accorgesse.

5. PERCHE' nessuno se ne e' accorto?
   -> Perche' il processo di review delle migrazioni non include una verifica
      automatica dell'impatto sulle performance delle query esistenti.

Causa radice sistemica: mancanza di un gate automatico nel CI/CD
che verifichi l'impatto delle migrazioni sulle query critiche.

Azione correttiva: implementare un check che esegua EXPLAIN ANALYZE
sulle top-N query prima di approvare una migrazione in produzione.
```

**Attenzione:** I 5 Whys hanno limitazioni. Per incidenti complessi con cause multiple, e' preferibile combinare questa tecnica con un'analisi dei fattori contribuenti (contributing factors). Un incidente raramente ha una singola causa radice lineare — spesso e' il risultato della convergenza di piu' condizioni.

#### Contributing Factors vs Root Cause

Distinguere tra causa radice e fattori contribuenti e' fondamentale per produrre azioni correttive efficaci:

```
Causa radice:
  La condizione necessaria senza la quale l'incidente non si sarebbe verificato.
  Esempio: L'indice mancante sulla tabella orders.

Fattori contribuenti:
  Condizioni che hanno amplificato l'impatto o rallentato la risoluzione.
  - Il connection pool non aveva un timeout configurato
  - L'alert per "connessioni database > 80%" era disabilitato
  - Il team era in una fase di staffing ridotto (festivita')
  - Il runbook per "database connection exhaustion" era obsoleto

Trigger:
  L'evento specifico che ha innescato la catena causale.
  - Il deploy della migrazione v2.4.1 alle 14:00
```

#### Organizational Learning Loop

Il valore del post-mortem si realizza solo se le lezioni apprese vengono sistematizzate e condivise:

```
1. DOCUMENT — Scrivere il post-mortem entro 48 ore
2. REVIEW — Discussione in team entro 1 settimana
3. SHARE — Condividere con l'organizzazione allargata
4. TRACK — Registrare le azioni correttive nel sistema di tracking
5. VERIFY — Follow-up mensile sullo stato delle azioni
6. PATTERN — Analisi trimestrale dei pattern ricorrenti tra post-mortem

Anti-pattern da evitare:
- Post-mortem scritti ma mai discussi
- Azioni correttive create ma mai completate
- Lezioni apprese ma mai condivise al di fuori del team
- Pattern ricorrenti che non vengono mai affrontati strutturalmente
```

#### Template Post-Mortem Avanzato

```markdown
# Post-Mortem: [Titolo Descrittivo dell'Incidente]

## Metadata
- **Data incidente:** YYYY-MM-DD
- **Durata:** HH:MM - HH:MM (X ore Y minuti)
- **Severity:** SEV[N]
- **Incident Commander:** [nome]
- **Autore post-mortem:** [nome]
- **Data post-mortem meeting:** YYYY-MM-DD
- **Stato azioni:** [N completate / M totali]

## Summary
[2-3 frasi che descrivono cosa e' successo, l'impatto, e come e' stato risolto]

## Impatto
- Utenti impattati: [numero o percentuale]
- Durata del disservizio: [minuti]
- Revenue persa stimata: [importo, se applicabile]
- Ticket di supporto generati: [numero]
- SLO violati: [lista SLO con percentuale rimanente di error budget]

## Timeline (UTC)
| Timestamp | Evento | Fonte |
|---|---|---|
| 14:00 | Deploy v2.4.1 | CI/CD |
| 14:05 | Alert latenza p99 > 2s | PagerDuty |
| 14:08 | IC dichiarato | Slack |
| ... | ... | ... |

## Root Cause Analysis
### Causa Radice
[Descrizione tecnica dettagliata]

### Fattori Contribuenti
1. [Fattore 1 con dettaglio]
2. [Fattore 2 con dettaglio]

### Trigger
[Evento specifico che ha innescato l'incidente]

## Detection Analysis
- Come e' stato rilevato: [automatico/manuale]
- Tempo di detection (MTTD): [minuti]
- L'alert era gia' configurato? [si/no]
- Se no, perche' non era stato previsto?

## Response Analysis
- MTTA: [minuti]
- MTTR: [minuti]
- Il runbook esisteva? [si/no/parziale]
- Il runbook era accurato? [si/no]
- Quante persone coinvolte nella risoluzione: [numero]

## Cosa Ha Funzionato
- [Punto con dettaglio]

## Cosa Non Ha Funzionato
- [Punto con dettaglio e proposta di miglioramento]

## Dove Siamo Stati Fortunati
- [Fattori che avrebbero potuto peggiorare l'impatto]

## Azioni Correttive
| ID | Azione | Tipo | Owner | Scadenza | Ticket | Stato |
|---|---|---|---|---|---|---|
| 1 | Aggiungere check indici nel CI | Prevenzione | @dev-team | YYYY-MM-DD | JIRA-123 | TODO |
| 2 | Configurare timeout connection pool | Mitigazione | @platform | YYYY-MM-DD | JIRA-124 | TODO |
| 3 | Riattivare alert connessioni DB | Detection | @sre | YYYY-MM-DD | JIRA-125 | DONE |

Tipo di azione:
- Prevenzione: impedisce che il problema si ripresenti
- Mitigazione: riduce l'impatto se il problema si ripresenta
- Detection: migliora la velocita' di rilevamento
- Processo: modifica procedure operative
```

#### Metriche di Qualita' dei Post-Mortem

| Metrica | Definizione | Target |
|---|---|---|
| Completion rate | % incidenti SEV1-2 con post-mortem completato | > 95% |
| Time to publish | Giorni tra incidente e pubblicazione del post-mortem | < 5 giorni |
| Action item completion | % azioni correttive completate entro la scadenza | > 80% |
| Recurrence rate | % incidenti con la stessa causa radice di un incidente precedente | < 10% |
| Readership | % del team engineering che ha letto il post-mortem | > 70% |

---

## 3. Troubleshooting Kubernetes

### Pod Troubleshooting

#### CrashLoopBackOff

Il pod si avvia, fallisce, e Kubernetes lo riavvia con backoff esponenziale.

```bash
# Verificare lo stato del pod
kubectl get pod <pod-name> -n <namespace>

# Output di esempio:
# NAME          READY   STATUS             RESTARTS      AGE
# my-app-xyz    0/1     CrashLoopBackOff   5 (30s ago)   3m

# Leggere i log del container corrente (o dell'ultimo crash)
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous

# Descrivere il pod per dettagli su eventi e condizioni
kubectl describe pod <pod-name> -n <namespace>

# Cause comuni:
# 1. Errore nell'applicazione (eccezione non gestita, configurazione mancante)
# 2. Health check che fallisce (liveness probe troppo aggressiva)
# 3. Dipendenza non disponibile (database, servizio esterno)
# 4. File di configurazione mancante (ConfigMap/Secret non montato)

# Verificare le variabili d'ambiente e i mount
kubectl exec -it <pod-name> -n <namespace> -- env
kubectl exec -it <pod-name> -n <namespace> -- ls /config/

# Verificare la liveness probe
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[0].livenessProbe}'
```

#### ImagePullBackOff

```bash
# Il pod non riesce a scaricare l'immagine container
kubectl describe pod <pod-name> -n <namespace> | grep -A 5 "Events"

# Output di esempio:
# Events:
#   Type     Reason     Age   From               Message
#   ----     ------     ----  ----               -------
#   Normal   Scheduled  2m    default-scheduler  Successfully assigned...
#   Normal   Pulling    2m    kubelet            Pulling image "registry.example.com/app:v1.2"
#   Warning  Failed     1m    kubelet            Failed to pull image: unauthorized

# Cause e soluzioni:
# 1. Immagine non esistente -> verificare tag e repository
docker manifest inspect registry.example.com/app:v1.2

# 2. Credenziali mancanti -> creare o aggiornare il secret
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass \
  -n <namespace>

# 3. Verificare che il pod usa il secret
kubectl get pod <pod-name> -n <namespace> \
  -o jsonpath='{.spec.imagePullSecrets}'
```

#### OOMKilled

```bash
# Il container ha superato il limite di memoria ed e' stato terminato dal kernel
kubectl describe pod <pod-name> -n <namespace> | grep -A 3 "Last State"

# Output di esempio:
#     Last State:     Terminated
#       Reason:       OOMKilled
#       Exit Code:    137

# Verificare i limiti attuali
kubectl get pod <pod-name> -n <namespace> \
  -o jsonpath='{.spec.containers[0].resources}'

# Verificare l'utilizzo di memoria con metrics-server
kubectl top pod <pod-name> -n <namespace>

# Soluzioni:
# 1. Aumentare il memory limit nel deployment
kubectl patch deployment <deploy-name> -n <namespace> --type='json' \
  -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "1Gi"}]'

# 2. Investigare memory leak nell'applicazione
# 3. Ottimizzare il consumo di memoria (garbage collection, pool sizing)
```

#### Pod in stato Pending

```bash
# Verificare perche' il pod non viene schedulato
kubectl describe pod <pod-name> -n <namespace> | grep -A 10 "Events"

# Cause comuni:
# 1. Risorse insufficienti nel cluster
kubectl describe nodes | grep -A 5 "Allocated resources"

# 2. Node selector o affinity non soddisfatti
kubectl get pod <pod-name> -n <namespace> \
  -o jsonpath='{.spec.nodeSelector}'

# 3. Taints sui nodi che impediscono lo scheduling
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints

# 4. PersistentVolumeClaim in stato Pending
kubectl get pvc -n <namespace>
```

#### Pod Evicted

```bash
# Il nodo ha rimosso il pod per pressione su risorse
kubectl get pods -n <namespace> --field-selector=status.phase=Failed \
  | grep Evicted

# Verificare le condizioni del nodo
kubectl describe node <node-name> | grep -A 5 "Conditions"

# Pulire i pod evicted
kubectl delete pods -n <namespace> --field-selector=status.phase=Failed
```

### Node Troubleshooting

```bash
# Verificare lo stato di tutti i nodi
kubectl get nodes
# Output di esempio:
# NAME          STATUS     ROLES           AGE   VERSION
# node-1        Ready      control-plane   30d   v1.28.2
# node-2        Ready      <none>          30d   v1.28.2
# node-3        NotReady   <none>          30d   v1.28.2

# Investigare un nodo NotReady
kubectl describe node node-3 | grep -A 15 "Conditions"

# Verificare i log del kubelet sul nodo
ssh node-3 "journalctl -u kubelet --since '30 minutes ago' --no-pager | tail -50"

# Verificare pressione su risorse
kubectl describe node node-3 | grep -E "(MemoryPressure|DiskPressure|PIDPressure)"

# Output di esempio:
# Conditions:
#   MemoryPressure   True    ...  KubeletHasInsufficientMemory
#   DiskPressure     False   ...  KubeletHasNoDiskPressure
#   PIDPressure      False   ...  KubeletHasSufficientPID

# Verificare disk pressure
ssh node-3 "df -h"
ssh node-3 "crictl images | wc -l"  # Troppe immagini cached?

# Cordone e drain di un nodo problematico
kubectl cordon node-3
kubectl drain node-3 --ignore-daemonsets --delete-emptydir-data
```

### Service e Networking Issues

```bash
# Verificare che il Service abbia endpoint attivi
kubectl get endpoints <service-name> -n <namespace>
# Se ENDPOINTS e' <none>, nessun pod matcha il selector del Service

# Verificare il selector del Service
kubectl get svc <service-name> -n <namespace> -o yaml | grep -A 5 selector

# Verificare i label dei pod
kubectl get pods -n <namespace> --show-labels

# Test DNS interno al cluster
kubectl run dns-test --image=busybox:1.36 --rm -it --restart=Never -- \
  nslookup <service-name>.<namespace>.svc.cluster.local

# Output atteso:
# Server:    10.96.0.10
# Address:   10.96.0.10:53
# Name:      my-service.default.svc.cluster.local
# Address:   10.100.200.15

# Verificare CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=50

# Test connettivita' tra pod
kubectl run net-test --image=nicolaka/netshoot --rm -it --restart=Never -- \
  curl -v http://<service-name>.<namespace>.svc.cluster.local:8080/health

# Verificare NetworkPolicy
kubectl get networkpolicy -n <namespace>
kubectl describe networkpolicy <policy-name> -n <namespace>

# Troubleshooting Ingress
kubectl get ingress -n <namespace>
kubectl describe ingress <ingress-name> -n <namespace>
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=50
```

### Storage Issues

```bash
# PVC in stato Pending
kubectl get pvc -n <namespace>
# Output di esempio:
# NAME      STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# data-pvc  Pending                                      gp2            5m

kubectl describe pvc data-pvc -n <namespace>
# Cause: nessun PV disponibile, StorageClass errata, provisioner non funzionante

# Verificare StorageClass e provisioner
kubectl get storageclass
kubectl get pods -n kube-system | grep -i provisioner

# Errori di mount
kubectl describe pod <pod-name> -n <namespace> | grep -A 5 "mount"
# "Unable to attach or mount volumes" -> verificare che il volume esista e sia disponibile
```

### RBAC Issues

```bash
# Verificare i permessi di un ServiceAccount
kubectl auth can-i list pods --as=system:serviceaccount:<namespace>:<sa-name> -n <namespace>

# Verificare tutti i permessi
kubectl auth can-i --list --as=system:serviceaccount:<namespace>:<sa-name> -n <namespace>

# Verificare i RoleBinding
kubectl get rolebinding,clusterrolebinding -n <namespace> \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.subjects[*].name}{"\n"}{end}'
```

### Control Plane Issues

```bash
# Verificare lo stato dei componenti del control plane
kubectl get componentstatuses  # deprecato ma ancora utile
kubectl get pods -n kube-system

# Verificare i log dei componenti
kubectl logs -n kube-system kube-apiserver-<node> --tail=100
kubectl logs -n kube-system kube-controller-manager-<node> --tail=100
kubectl logs -n kube-system kube-scheduler-<node> --tail=100
kubectl logs -n kube-system etcd-<node> --tail=100

# Verificare la salute di etcd
kubectl exec -n kube-system etcd-<node> -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```

### Debug con Container Effimeri (Ephemeral Containers)

A partire da Kubernetes 1.25 (GA), i container effimeri rappresentano lo strumento piu' potente per il debugging in-cluster. A differenza di `kubectl exec`, non richiedono che il container target contenga tool di diagnostica — si inietta un container di debug direttamente nel Pod in esecuzione.

#### Quando Usare Container Effimeri

| Scenario | Approccio tradizionale | Approccio ephemeral container |
|---|---|---|
| Container distroless (no shell) | Impossibile fare exec | `kubectl debug` con immagine tool |
| CrashLoopBackOff troppo rapido | Difficile catturare exec prima del crash | Debug con `--target` condivide PID namespace |
| Analisi di rete dal Pod | Richiede curl/dig nel container | Iniettare container con net-tools |
| Profiling runtime | Richiede strumenti pre-installati | Iniettare container con perf/strace |

#### Comandi Fondamentali

```bash
# Debug di un Pod con container distroless — inietta busybox
kubectl debug -it pod/my-app-7b9c5 --image=busybox:1.36 --target=app

# Debug con immagine completa (nicolaka/netshoot per networking)
kubectl debug -it pod/my-app-7b9c5 --image=nicolaka/netshoot --target=app

# Creare copia del Pod con container di debug (non modifica l'originale)
kubectl debug pod/my-app-7b9c5 -it --copy-to=debug-pod --image=ubuntu:22.04 \
  --share-processes

# Debug a livello di nodo — crea Pod privilegiato sul nodo
kubectl debug node/worker-03 -it --image=ubuntu:22.04

# Ispezionare filesystem del container target tramite /proc
# (quando si usa --target, si condivide il PID namespace)
kubectl debug -it pod/my-app-7b9c5 --image=busybox:1.36 --target=app -- sh
# Dentro il container effimero:
ls /proc/1/root/app/          # Filesystem del container target
cat /proc/1/root/app/config.yaml
cat /proc/1/environ           # Variabili d'ambiente del processo target
```

#### Profilo di Debug Personalizzato

Per ambienti con policy di sicurezza restrittive (Pod Security Standards), definire un profilo di debug che rispetti i vincoli:

```bash
# Debug con profilo "restricted" — nessun privilegio elevato
kubectl debug -it pod/my-app-7b9c5 --image=busybox:1.36 \
  --profile=restricted --target=app

# Debug con profilo "netadmin" — capability NET_ADMIN per tcpdump
kubectl debug -it pod/my-app-7b9c5 --image=nicolaka/netshoot \
  --profile=netadmin --target=app

# Profili disponibili: general, restricted, baseline, netadmin, sysadmin
```

#### Flowchart: Scelta dello Strumento di Debug Kubernetes

```
Pod in stato anomalo?
│
├─ Container ha shell? (non distroless)
│  ├─ SI → kubectl exec -it pod/X -- sh
│  │       Sufficiente per la maggior parte dei casi
│  └─ NO → Container distroless
│          └─ kubectl debug -it pod/X --image=busybox --target=app
│
├─ Pod in CrashLoopBackOff?
│  ├─ Crash lento (>10s) → kubectl logs --previous + kubectl exec
│  └─ Crash immediato → kubectl debug pod/X --copy-to=debug-copy \
│                        --image=ubuntu --share-processes
│                        (copia del Pod che non crasha)
│
├─ Problema di rete tra Pod?
│  └─ kubectl debug -it pod/X --image=nicolaka/netshoot --target=app
│     Dentro: tcpdump -i eth0 -nn port 8080
│             nslookup service-name.namespace.svc.cluster.local
│             curl -v http://service:8080/healthz
│
└─ Problema a livello di nodo?
   └─ kubectl debug node/worker-03 -it --image=ubuntu
      Dentro: chroot /host
              journalctl -u kubelet --since "1h ago"
              crictl ps -a
              dmesg | tail -50
```

#### Sicurezza dei Container Effimeri

Considerazioni importanti per ambienti di produzione:

- **RBAC**: limitare `pods/ephemeralcontainers` con Role/ClusterRole specifici
- **Audit logging**: ogni container effimero genera un evento audit — monitorare per uso non autorizzato
- **Pod Security Standards**: i container effimeri devono rispettare le policy del namespace
- **Cleanup**: i container effimeri non vengono rimossi automaticamente — verificare con `kubectl get pod -o json | jq '.spec.ephemeralContainers'`
- **Network namespace condiviso**: il container di debug condivide la rete del Pod — puo' vedere tutto il traffico

```bash
# RBAC: permettere debug solo a SRE
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: pod-debugger
rules:
- apiGroups: [""]
  resources: ["pods/ephemeralcontainers"]
  verbs: ["patch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
```

---

## 4. Troubleshooting Docker e Container

### Container Non Si Avvia

```bash
# Verificare lo stato del container
docker ps -a --filter "name=my-container"

# Output di esempio:
# CONTAINER ID   IMAGE          COMMAND   CREATED   STATUS                     NAMES
# abc123         my-app:v1.0    "./app"   2m ago    Exited (1) 1 minute ago    my-container

# Leggere i log
docker logs my-container
docker logs my-container --tail 100

# Ispezionare il container per dettagli
docker inspect my-container | jq '.[0].State'

# Output di esempio:
# {
#   "Status": "exited",
#   "Running": false,
#   "ExitCode": 1,
#   "Error": "",
#   "OOMKilled": false
# }

# Exit codes comuni:
# 0   - Uscita normale
# 1   - Errore generico dell'applicazione
# 126 - Comando non eseguibile (permessi)
# 127 - Comando non trovato (PATH, entrypoint errato)
# 137 - SIGKILL (OOM o docker kill)
# 139 - SIGSEGV (segmentation fault)
# 143 - SIGTERM (docker stop)

# Avviare il container in modo interattivo per debug
docker run -it --entrypoint /bin/sh my-app:v1.0

# Verificare che l'entrypoint e il CMD siano corretti
docker inspect my-app:v1.0 | jq '.[0].Config.Entrypoint, .[0].Config.Cmd'
```

### Networking Issues

```bash
# Verificare le reti Docker
docker network ls
docker network inspect bridge

# Container non raggiungibili tra loro
# Verificare che siano sulla stessa rete
docker inspect <container1> | jq '.[0].NetworkSettings.Networks'
docker inspect <container2> | jq '.[0].NetworkSettings.Networks'

# Creare una rete dedicata e connettere i container
docker network create app-network
docker network connect app-network container1
docker network connect app-network container2

# Verificare la risoluzione DNS tra container
docker exec container1 ping container2

# Debug networking con container dedicato
docker run --rm --net=host nicolaka/netshoot ss -tlnp
docker run --rm --net=container:<target-container> nicolaka/netshoot curl localhost:8080

# Verificare le porte mappate
docker port my-container
# Output: 8080/tcp -> 0.0.0.0:80

# Problemi con overlay network (Docker Swarm)
docker network inspect --verbose ingress
```

### Storage Issues

```bash
# Verificare lo spazio utilizzato da Docker
docker system df

# Output di esempio:
# TYPE            TOTAL   ACTIVE  SIZE      RECLAIMABLE
# Images          45      10      12.5GB    8.2GB (65%)
# Containers      12      5       500MB     200MB (40%)
# Local Volumes   20      8       5.5GB     3.1GB (56%)
# Build Cache     100     0       2.3GB     2.3GB (100%)

# Pulire risorse non utilizzate
docker system prune -a --volumes  # ATTENZIONE: rimuove tutto cio' che non e' in uso

# Pulire selettivamente
docker image prune -a              # Immagini non referenziate
docker volume prune                # Volumi non montati
docker builder prune               # Build cache

# Problemi di permessi su volumi
docker run -v /host/path:/container/path my-app
# Se l'app non riesce a scrivere, verificare UID/GID
docker exec my-container id
docker exec my-container ls -la /container/path

# Soluzione: specificare l'utente nel run
docker run -u $(id -u):$(id -g) -v /host/path:/container/path my-app
```

### Image Issues

```bash
# Build failure — analizzare il layer che fallisce
docker build --no-cache -t my-app:debug .

# Problemi di layer caching
# Il COPY di file che cambiano frequentemente invalida la cache
# Soluzione: ordinare le istruzioni dal meno al piu' frequentemente modificato
# Dockerfile ottimizzato:
#   FROM node:20-alpine
#   WORKDIR /app
#   COPY package*.json ./        <- cambia raramente
#   RUN npm ci                   <- cached se package.json non cambia
#   COPY . .                     <- cambia frequentemente
#   RUN npm run build

# Verificare la dimensione dei layer
docker history my-app:v1.0

# Multi-stage build per ridurre la dimensione
# Verificare che il final stage contenga solo il necessario
docker inspect my-app:v1.0 | jq '.[0].Size'
```

### Docker Daemon Issues

```bash
# Verificare lo stato del daemon
systemctl status docker
journalctl -u docker --since "1 hour ago" --no-pager | tail -50

# Il daemon non risponde
# Verificare il socket
ls -la /var/run/docker.sock

# Riavviare il daemon (ATTENZIONE: ferma tutti i container senza restart policy)
sudo systemctl restart docker

# Verificare la configurazione del daemon
cat /etc/docker/daemon.json

# Problemi di spazio disco per il daemon
df -h /var/lib/docker
```

### Resource Constraints

```bash
# Verificare l'utilizzo di risorse dei container in esecuzione
docker stats --no-stream

# Output di esempio:
# CONTAINER ID   NAME      CPU %   MEM USAGE / LIMIT    MEM %   NET I/O          BLOCK I/O
# abc123         my-app    85.5%   950MiB / 1GiB        92.8%   1.5MB / 800kB    50MB / 10MB
# def456         redis     2.3%    50MiB / 256MiB       19.5%   500kB / 300kB    5MB / 1MB

# Limitare le risorse di un container
docker run -d \
  --memory=512m \
  --memory-swap=1g \
  --cpus=0.5 \
  --pids-limit=100 \
  my-app:v1.0
```

### Docker Compose Troubleshooting

```bash
# Verificare lo stato di tutti i servizi
docker compose ps

# Verificare la configurazione risolta (dopo variable substitution)
docker compose config

# Log di un servizio specifico
docker compose logs -f --tail 100 <service-name>

# Ricreare un singolo servizio senza toccare gli altri
docker compose up -d --force-recreate <service-name>

# Verificare la risoluzione delle dipendenze (depends_on)
docker compose config --services

# Debug: avviare senza detach per vedere l'output
docker compose up --abort-on-container-exit
```

---

## 5. Troubleshooting Cloud (AWS/Azure/GCP)

### AWS — EC2 Connectivity

```bash
# Verificare lo stato dell'istanza
aws ec2 describe-instances --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].[State.Name, PublicIpAddress, PrivateIpAddress, SubnetId, VpcId]' \
  --output table

# Verificare i Security Groups
aws ec2 describe-security-groups --group-ids sg-0123456789abcdef0 \
  --query 'SecurityGroups[].IpPermissions[]' --output json

# Verificare le NACLs della subnet
aws ec2 describe-network-acls --filters "Name=association.subnet-id,Values=subnet-abc123" \
  --query 'NetworkAcls[].Entries[]' --output table

# Verificare la route table
aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=subnet-abc123" \
  --query 'RouteTables[].Routes[]' --output table

# Verificare che l'istanza abbia un Internet Gateway (per accesso pubblico)
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=vpc-xyz789"

# VPC Flow Logs — verificare traffico bloccato
aws logs filter-log-events \
  --log-group-name "vpc-flow-logs" \
  --filter-pattern "REJECT" \
  --start-time $(date -d '1 hour ago' +%s000)

# EC2 Instance Connect per debug senza SSH key
aws ec2-instance-connect send-ssh-public-key \
  --instance-id i-0123456789abcdef0 \
  --availability-zone eu-west-1a \
  --instance-os-user ec2-user \
  --ssh-public-key file://~/.ssh/id_rsa.pub
```

### AWS — RDS Connection Issues

```bash
# Verificare lo stato dell'istanza RDS
aws rds describe-db-instances --db-instance-identifier my-database \
  --query 'DBInstances[].[DBInstanceStatus, Endpoint.Address, Endpoint.Port]' \
  --output table

# Verificare i Security Groups associati
aws rds describe-db-instances --db-instance-identifier my-database \
  --query 'DBInstances[].VpcSecurityGroups[]' --output table

# Test connettivita'
nc -zv my-database.abc123.eu-west-1.rds.amazonaws.com 5432

# Verificare che il parametro publicly-accessible sia corretto
aws rds describe-db-instances --db-instance-identifier my-database \
  --query 'DBInstances[].PubliclyAccessible'

# Verificare i log di errore RDS
aws rds download-db-log-file-portion \
  --db-instance-identifier my-database \
  --log-file-name error/postgresql.log \
  --starting-token 0
```

### AWS — S3 Access Denied

```bash
# Verificare la bucket policy
aws s3api get-bucket-policy --bucket my-bucket

# Verificare i permessi IAM dell'utente/ruolo corrente
aws sts get-caller-identity
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/my-role \
  --action-names s3:GetObject \
  --resource-arns arn:aws:s3:::my-bucket/*

# Verificare il Block Public Access
aws s3api get-public-access-block --bucket my-bucket

# Verificare la crittografia (KMS key permissions)
aws s3api head-object --bucket my-bucket --key my-file.txt
```

### AWS — Lambda Issues

```bash
# Verificare gli ultimi errori di invocazione
aws lambda get-function --function-name my-function \
  --query 'Configuration.[Runtime, MemorySize, Timeout, LastModified]'

# Leggere i log recenti
aws logs filter-log-events \
  --log-group-name "/aws/lambda/my-function" \
  --start-time $(date -d '30 minutes ago' +%s000) \
  --filter-pattern "ERROR"

# Timeout: aumentare il timeout o ottimizzare il codice
aws lambda update-function-configuration \
  --function-name my-function \
  --timeout 60

# Memory: aumentare la memoria (aumenta anche la CPU allocata)
aws lambda update-function-configuration \
  --function-name my-function \
  --memory-size 512
```

### Azure — VM Connectivity

```bash
# Verificare lo stato della VM
az vm show -g myResourceGroup -n myVM --query '{status: provisioningState, size: hardwareProfile.vmSize}'

# Verificare i Network Security Groups
az network nsg rule list -g myResourceGroup --nsg-name myNSG --output table

# Verificare la connettivita' con Network Watcher
az network watcher test-connectivity \
  --resource-group myResourceGroup \
  --source-resource myVM \
  --dest-address 10.0.1.5 \
  --dest-port 443

# Verificare i log di boot diagnostics
az vm boot-diagnostics get-boot-log -g myResourceGroup -n myVM
```

### Azure — AKS Issues

```bash
# Verificare lo stato del cluster AKS
az aks show -g myResourceGroup -n myAKSCluster \
  --query '{status: provisioningState, kubernetesVersion: kubernetesVersion, nodeCount: agentPoolProfiles[0].count}'

# Ottenere le credenziali e verificare la connettivita'
az aks get-credentials -g myResourceGroup -n myAKSCluster
kubectl get nodes

# Verificare gli aggiornamenti disponibili
az aks get-upgrades -g myResourceGroup -n myAKSCluster --output table
```

### GCP — Compute Engine

```bash
# Verificare lo stato dell'istanza
gcloud compute instances describe my-instance --zone=europe-west1-b \
  --format='table(status, networkInterfaces[0].accessConfigs[0].natIP, networkInterfaces[0].networkIP)'

# Verificare le firewall rules
gcloud compute firewall-rules list --filter="network=default" --format=table

# Serial console per debug boot issues
gcloud compute instances get-serial-port-output my-instance --zone=europe-west1-b

# Verificare i log
gcloud logging read 'resource.type="gce_instance" AND resource.labels.instance_id="123456789"' \
  --limit=50 --format=json
```

### GCP — GKE Issues

```bash
# Verificare lo stato del cluster
gcloud container clusters describe my-cluster --zone=europe-west1-b \
  --format='table(status, currentMasterVersion, currentNodeCount)'

# Ottenere le credenziali
gcloud container clusters get-credentials my-cluster --zone=europe-west1-b

# Verificare le operazioni in corso
gcloud container operations list --filter="targetLink~my-cluster" --format=table
```

### GCP — IAM Issues

```bash
# Verificare i ruoli di un service account
gcloud projects get-iam-policy my-project \
  --flatten="bindings[].members" \
  --filter="bindings.members:my-sa@my-project.iam.gserviceaccount.com" \
  --format='table(bindings.role)'

# Testare i permessi
gcloud asset analyze-iam-policy \
  --organization=123456 \
  --identity="serviceAccount:my-sa@my-project.iam.gserviceaccount.com" \
  --full-resource-name="//storage.googleapis.com/my-bucket"
```

---

## 6. Troubleshooting Database

### PostgreSQL

#### Slow Queries

```sql
-- Identificare le query piu' lente attualmente in esecuzione
SELECT pid, now() - pg_stat_activity.query_start AS duration,
       query, state, wait_event_type, wait_event
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY duration DESC
LIMIT 20;

-- Verificare pg_stat_statements per le query storicamente piu' lente
SELECT
  calls,
  round(total_exec_time::numeric, 2) AS total_ms,
  round(mean_exec_time::numeric, 2) AS avg_ms,
  round((100 * total_exec_time / sum(total_exec_time) OVER ())::numeric, 2) AS pct,
  substr(query, 1, 100) AS query_preview
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Analizzare il piano di esecuzione di una query
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE user_id = 12345 AND status = 'pending';

-- Verificare gli indici mancanti
SELECT
  schemaname, tablename,
  seq_scan, seq_tup_read,
  idx_scan, idx_tup_fetch,
  seq_tup_read / GREATEST(seq_scan, 1) AS avg_rows_per_seq_scan
FROM pg_stat_user_tables
WHERE seq_scan > 100
ORDER BY seq_tup_read DESC
LIMIT 20;
```

#### Connection Exhaustion

```sql
-- Verificare le connessioni correnti
SELECT count(*), state, usename, application_name
FROM pg_stat_activity
GROUP BY state, usename, application_name
ORDER BY count DESC;

-- Verificare il limite massimo
SHOW max_connections;

-- Terminare connessioni idle da troppo tempo
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND query_start < NOW() - INTERVAL '10 minutes'
  AND pid != pg_backend_pid();
```

#### Replication Lag

```sql
-- Sul primary: verificare lo stato della replication
SELECT
  client_addr,
  state,
  sent_lsn,
  write_lsn,
  flush_lsn,
  replay_lsn,
  pg_wal_lsn_diff(sent_lsn, replay_lsn) AS replay_lag_bytes,
  write_lag,
  flush_lag,
  replay_lag
FROM pg_stat_replication;

-- Sulla replica: verificare il ritardo
SELECT
  now() - pg_last_xact_replay_timestamp() AS replication_delay;
```

#### VACUUM Issues

```sql
-- Verificare le tabelle che necessitano VACUUM
SELECT
  schemaname, relname,
  n_dead_tup,
  n_live_tup,
  round(n_dead_tup::numeric / GREATEST(n_live_tup, 1) * 100, 2) AS dead_pct,
  last_vacuum,
  last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;

-- Verificare se autovacuum e' bloccato
SELECT pid, query, state, wait_event_type, wait_event,
       now() - query_start AS duration
FROM pg_stat_activity
WHERE query ILIKE '%vacuum%';

-- VACUUM manuale con VERBOSE per diagnostica
VACUUM (VERBOSE, ANALYZE) my_table;
```

#### Lock Contention

```sql
-- Identificare i lock attivi e le query in attesa
SELECT
  blocked.pid AS blocked_pid,
  blocked.query AS blocked_query,
  blocking.pid AS blocking_pid,
  blocking.query AS blocking_query,
  now() - blocked.query_start AS blocked_duration
FROM pg_stat_activity blocked
JOIN pg_locks bl ON bl.pid = blocked.pid
JOIN pg_locks kl ON kl.locktype = bl.locktype
  AND kl.database IS NOT DISTINCT FROM bl.database
  AND kl.relation IS NOT DISTINCT FROM bl.relation
  AND kl.page IS NOT DISTINCT FROM bl.page
  AND kl.tuple IS NOT DISTINCT FROM bl.tuple
  AND kl.transactionid IS NOT DISTINCT FROM bl.transactionid
  AND kl.classid IS NOT DISTINCT FROM bl.classid
  AND kl.objid IS NOT DISTINCT FROM bl.objid
  AND kl.objsubid IS NOT DISTINCT FROM bl.objsubid
  AND kl.pid != bl.pid
JOIN pg_stat_activity blocking ON kl.pid = blocking.pid
WHERE NOT bl.granted;
```

### MySQL

#### InnoDB Buffer Pool

```sql
-- Verificare l'utilizzo del buffer pool
SHOW ENGINE INNODB STATUS\G

-- Metriche chiave
SELECT
  (SELECT VARIABLE_VALUE FROM performance_schema.global_status
   WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests') AS total_reads,
  (SELECT VARIABLE_VALUE FROM performance_schema.global_status
   WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads') AS disk_reads;

-- Il rapporto disk_reads/total_reads dovrebbe essere < 1%
-- Se e' piu' alto, aumentare innodb_buffer_pool_size
```

#### Deadlocks

```sql
-- Visualizzare l'ultimo deadlock
SHOW ENGINE INNODB STATUS\G
-- Cercare la sezione "LATEST DETECTED DEADLOCK"

-- Monitorare i deadlock
SELECT * FROM performance_schema.events_errors_summary_global_by_error
WHERE ERROR_NAME = 'ER_LOCK_DEADLOCK';

-- Identificare le query che causano lock
SELECT
  r.trx_id AS waiting_trx,
  r.trx_mysql_thread_id AS waiting_thread,
  r.trx_query AS waiting_query,
  b.trx_id AS blocking_trx,
  b.trx_mysql_thread_id AS blocking_thread,
  b.trx_query AS blocking_query
FROM information_schema.innodb_lock_waits w
JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_trx_id
JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_trx_id;
```

### Redis

```bash
# Verificare l'utilizzo di memoria
redis-cli INFO memory

# Output chiave:
# used_memory_human: 1.50G
# used_memory_peak_human: 2.00G
# maxmemory_human: 2.00G
# maxmemory_policy: allkeys-lru
# mem_fragmentation_ratio: 1.15

# Se mem_fragmentation_ratio > 1.5 -> frammentazione eccessiva
# Soluzione: MEMORY PURGE o restart

# Identificare le chiavi piu' grandi
redis-cli --bigkeys

# Verificare la latenza
redis-cli --latency-history -i 5

# Verificare le slow queries
redis-cli SLOWLOG GET 10

# Monitorare i comandi in tempo reale (ATTENZIONE: impatto su performance)
redis-cli MONITOR  # Usare solo brevemente in produzione

# Verificare lo stato del cluster
redis-cli CLUSTER INFO
redis-cli CLUSTER NODES
```

### MongoDB

```bash
# Verificare lo stato del replica set
mongosh --eval "rs.status()"

# Identificare le query lente
mongosh --eval "db.currentOp({'secs_running': {\$gt: 5}})"

# Verificare il profiling delle query
mongosh --eval "db.setProfilingLevel(1, { slowms: 100 })"
mongosh --eval "db.system.profile.find().sort({ts: -1}).limit(10).pretty()"

# Verificare lo stato dello sharding
mongosh --eval "sh.status()"

# Verificare gli indici
mongosh --eval "db.myCollection.getIndexes()"
mongosh --eval "db.myCollection.find({field: 'value'}).explain('executionStats')"
```

---

## 7. Troubleshooting Networking

### DNS Resolution Failures

```bash
# Verificare la risoluzione DNS con dig
dig example.com

# Output di esempio per una risoluzione funzionante:
# ;; ANSWER SECTION:
# example.com.       300   IN  A   93.184.216.34
#
# ;; Query time: 15 msec
# ;; SERVER: 8.8.8.8#53(8.8.8.8)

# Verificare con un server DNS specifico
dig @8.8.8.8 example.com
dig @1.1.1.1 example.com

# Verificare i record specifici
dig example.com MX
dig example.com CNAME
dig example.com TXT
dig example.com NS

# Verificare la propagazione DNS
dig +trace example.com

# Verificare il resolver locale
cat /etc/resolv.conf

# nslookup per verifica rapida
nslookup example.com

# Verificare il DNS inverso
dig -x 93.184.216.34

# Flush della cache DNS locale
sudo systemd-resolve --flush-caches   # systemd-resolved
sudo resolvectl flush-caches          # versioni recenti
```

### SSL/TLS Certificate Issues

```bash
# Verificare il certificato di un server
openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | \
  openssl x509 -noout -dates -subject -issuer

# Output di esempio:
# notBefore=Jan  1 00:00:00 2025 GMT
# notAfter=Dec 31 23:59:59 2025 GMT
# subject=CN = example.com
# issuer=O = Let's Encrypt, CN = R3

# Verificare la catena completa dei certificati
openssl s_client -connect example.com:443 -servername example.com -showcerts 2>/dev/null

# Verificare la scadenza
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | \
  openssl x509 -noout -enddate

# Verificare che il certificato matchi la chiave privata
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa -noout -modulus -in key.pem | openssl md5
# I due hash devono essere identici

# Verificare i protocolli TLS supportati
nmap --script ssl-enum-ciphers -p 443 example.com

# Test con curl per dettagli SSL
curl -vI https://example.com 2>&1 | grep -E "(SSL|TLS|certificate|expire)"
```

### Firewall e Connettivita'

```bash
# Verificare le regole iptables
sudo iptables -L -n -v
sudo iptables -L -n -v -t nat

# Verificare le porte in ascolto
ss -tlnp
# Output di esempio:
# State   Recv-Q  Send-Q  Local Address:Port   Peer Address:Port  Process
# LISTEN  0       128     0.0.0.0:22           0.0.0.0:*          users:(("sshd",pid=1234))
# LISTEN  0       128     0.0.0.0:80           0.0.0.0:*          users:(("nginx",pid=5678))

# Verificare se una porta remota e' raggiungibile
nc -zv remote-host 443
# Connection to remote-host 443 port [tcp/https] succeeded!

# Traceroute per identificare dove si perde la connettivita'
traceroute -n example.com
mtr --report example.com

# Output mtr di esempio:
# HOST                    Loss%   Snt   Last   Avg  Best  Wrst StDev
# 1. 192.168.1.1           0.0%    10    1.2   1.5   1.0   2.8   0.5
# 2. 10.0.0.1              0.0%    10    5.3   5.1   4.8   6.2   0.4
# 3. ???                   100.0    10    0.0   0.0   0.0   0.0   0.0  <- blocco qui
```

### MTU Problems

```bash
# Verificare l'MTU corrente
ip link show

# Test MTU con ping (il flag -M do evita la frammentazione)
ping -M do -s 1472 example.com
# Se fallisce con "message too long", l'MTU e' inferiore a 1500

# Trovare l'MTU corretto con binary search
ping -M do -s 1400 example.com  # funziona? provare piu' alto
ping -M do -s 1450 example.com  # funziona? provare piu' alto
ping -M do -s 1472 example.com  # fallisce? l'MTU e' tra 1450 e 1472

# Impostare l'MTU
sudo ip link set dev eth0 mtu 1400
```

### Latency Diagnosis

```bash
# Misurare la latenza di rete
ping -c 20 example.com

# Misurare la latenza applicativa
curl -o /dev/null -s -w "\
  DNS:        %{time_namelookup}s\n\
  Connect:    %{time_connect}s\n\
  TLS:        %{time_appconnect}s\n\
  TTFB:       %{time_starttransfer}s\n\
  Total:      %{time_total}s\n" \
  https://api.example.com/health

# Output di esempio:
# DNS:        0.015s
# Connect:    0.045s
# TLS:        0.120s
# TTFB:       0.250s    <- tempo dal server a rispondere
# Total:      0.260s
```

### Packet Loss

```bash
# Test prolungato per packet loss
ping -c 100 -i 0.2 example.com | tail -3

# Output:
# 100 packets transmitted, 97 received, 3% packet loss, time 19800ms
# rtt min/avg/max/mdev = 10.123/15.456/45.789/5.678 ms

# Cattura pacchetti per analisi dettagliata
sudo tcpdump -i eth0 -c 1000 -w capture.pcap host example.com

# Analizzare la cattura
tcpdump -r capture.pcap -n | head -20

# Cattura specifica per retransmissions TCP
sudo tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn|tcp-fin) != 0' -c 100
```

### Connection Timeouts

```bash
# Verificare i timeout di connessione TCP
cat /proc/sys/net/ipv4/tcp_syn_retries
cat /proc/sys/net/ipv4/tcp_keepalive_time
cat /proc/sys/net/ipv4/tcp_keepalive_intvl

# Verificare le connessioni in stato TIME_WAIT (possibile esaurimento porte)
ss -s
# Output:
# TCP:   1205 (estab 45, closed 1100, orphaned 0, timewait 1050)

# Se TIME_WAIT e' troppo alto
cat /proc/sys/net/ipv4/tcp_tw_reuse  # dovrebbe essere 1

# Verificare le connessioni per stato
ss -tan | awk '{print $1}' | sort | uniq -c | sort -rn
```

### Load Balancer Health Check Failures

```bash
# Simulare un health check
curl -v http://backend-server:8080/health

# Verificare che il backend risponda entro il timeout del LB
timeout 5 curl -s -o /dev/null -w "%{http_code} %{time_total}s" \
  http://backend-server:8080/health

# Verificare i target group in AWS ALB
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:eu-west-1:123456789012:targetgroup/my-tg/abc123

# Output di esempio:
# {
#   "TargetHealthDescriptions": [
#     {
#       "Target": {"Id": "i-abc123", "Port": 8080},
#       "TargetHealth": {"State": "unhealthy", "Reason": "Target.ResponseCodeMismatch"}
#     }
#   ]
# }
```

---

## 8. Troubleshooting CI/CD Pipeline

### Build Failures

#### Dependency Resolution

```bash
# Node.js — dependency resolution
npm ci --verbose 2>&1 | tail -30
# Se fallisce, pulire la cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Python — dependency conflicts
pip install -r requirements.txt --verbose 2>&1 | grep -i "conflict\|error"
# Usare pip-compile per risolvere i conflitti
pip-compile requirements.in --verbose

# Go — module issues
go mod tidy
go mod verify
go mod download -x

# Java/Maven — dependency tree per identificare conflitti
mvn dependency:tree -Dverbose -Dincludes=groupId:artifactId
```

#### Docker Build Issues in CI

```bash
# Build fallisce per timeout nel download di dipendenze
# Verificare la rete del runner
docker build --network=host -t my-app .

# Build fallisce per spazio disco insufficiente
docker system prune -af
df -h /var/lib/docker

# Cache non funziona in CI (ogni build parte da zero)
# Usare BuildKit con cache export/import
DOCKER_BUILDKIT=1 docker build \
  --cache-from type=registry,ref=registry.example.com/app:cache \
  --cache-to type=registry,ref=registry.example.com/app:cache,mode=max \
  -t my-app:${CI_COMMIT_SHA} .
```

### Test Failures

#### Flaky Tests

```bash
# Identificare test flaky rieseguendo piu' volte
for i in $(seq 1 10); do
  echo "=== Run $i ==="
  pytest tests/test_api.py -x --tb=short 2>&1 | tail -5
done

# Cause comuni di flaky tests:
# 1. Dipendenza dall'ordine di esecuzione -> pytest-randomly
# 2. State condiviso tra test -> verificare setup/teardown
# 3. Timing/race conditions -> usare retry con backoff
# 4. Dipendenze esterne (API, DB) -> mock in CI

# Eseguire test in ordine casuale per identificare dipendenze
pytest --randomly-seed=12345
```

#### Environment Differences

```bash
# Verificare le differenze tra ambiente locale e CI
# Versioni runtime
node --version
python --version
go version

# Variabili d'ambiente
env | sort > ci_env.txt
# Confrontare con l'ambiente locale

# Timezone issues
date +%Z
echo $TZ

# Permessi file
ls -la ./scripts/
# In CI, gli script devono avere il permesso di esecuzione
chmod +x ./scripts/*.sh
```

### Deployment Failures

#### Rollback Procedures

```bash
# Kubernetes — rollback deployment
kubectl rollout undo deployment/<deploy-name> -n <namespace>
kubectl rollout status deployment/<deploy-name> -n <namespace>

# Rollback a una revisione specifica
kubectl rollout history deployment/<deploy-name> -n <namespace>
kubectl rollout undo deployment/<deploy-name> -n <namespace> --to-revision=3

# Helm — rollback release
helm history <release-name> -n <namespace>
helm rollback <release-name> <revision> -n <namespace>

# Verificare lo stato dopo il rollback
helm status <release-name> -n <namespace>
kubectl get pods -n <namespace> -l app=<app-name>
```

#### Canary Deployment Failures

```bash
# Verificare le metriche del canary
kubectl get canary <name> -n <namespace> -o yaml

# Con Flagger, verificare gli eventi
kubectl describe canary <name> -n <namespace>

# Forzare il rollback del canary
kubectl patch canary <name> -n <namespace> \
  --type='json' -p='[{"op": "replace", "path": "/spec/suspend", "value": true}]'
```

### GitHub Actions Issues

```yaml
# Permessi insufficienti — verificare i permessi del workflow
# Nel file .github/workflows/deploy.yml:
permissions:
  contents: read
  packages: write
  id-token: write  # per OIDC con cloud providers

# Runner issues — verificare la disponibilita' del runner
# Usare self-hosted runner con label specifici
# runs-on: [self-hosted, linux, x64]

# Secret non accessibili
# Verificare che i secret siano configurati nel repository/organization
# Settings -> Secrets and variables -> Actions
```

```bash
# Debug GitHub Actions localmente con act
act -l                              # Lista i workflow
act -j build --secret-file .secrets # Eseguire un job specifico

# Verificare i log di un workflow fallito
gh run view <run-id> --log-failed
gh run view <run-id> --log --job=<job-id>

# Rieseguire un workflow fallito
gh run rerun <run-id> --failed
```

### ArgoCD Sync Issues

```bash
# Verificare lo stato dell'applicazione
argocd app get <app-name>

# Output di esempio:
# Name:               my-app
# Sync Status:        OutOfSync
# Health Status:      Degraded
# Sync Policy:        Automated

# Verificare le differenze tra Git e cluster
argocd app diff <app-name>

# Forzare il sync
argocd app sync <app-name> --force

# Verificare i log del sync
argocd app sync <app-name> --dry-run

# Se l'app e' in stato "Unknown" o "Progressing" da troppo tempo
argocd app terminate-op <app-name>
argocd app sync <app-name> --prune

# Verificare i log di ArgoCD
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller --tail=100
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server --tail=100
```

---

## 9. Runbook Template e Esempi

### Struttura Runbook Standard

```markdown
# [TITOLO RUNBOOK]

## Metadata
- **Autore:** [nome]
- **Ultima modifica:** [data]
- **Revisione:** [numero]
- **Servizio:** [nome servizio]
- **Severity trigger:** [SEV level che attiva questo runbook]

## Prerequisiti
- [ ] Accesso SSH ai server / kubectl configurato
- [ ] Permessi IAM necessari: [lista]
- [ ] Strumenti richiesti: [lista]
- [ ] Canale di comunicazione aperto: [canale]

## Quando Usare Questo Runbook
Descrivere le condizioni che richiedono l'esecuzione:
- Alert specifico: [nome alert]
- Sintomi osservati: [descrizione]

## Procedura

### Step 1: Valutazione Iniziale
[Comandi per valutare la situazione]

### Step 2: Azione Correttiva
[Comandi per risolvere il problema]

### Step 3: Verifica
[Comandi per verificare che il problema sia risolto]

## Rollback
Se la procedura causa problemi aggiuntivi:
[Passi per tornare allo stato precedente]

## Escalation
Se la procedura non risolve il problema:
- Contattare: [team/persona]
- Con le seguenti informazioni: [lista dati da fornire]

## Note
[Informazioni aggiuntive, eccezioni, casi particolari]
```

### Esempio: Riavvio Servizio Critico

```markdown
# Runbook: Riavvio Servizio API Gateway

## Metadata
- **Servizio:** api-gateway
- **Severity trigger:** SEV2 — Il servizio non risponde o ha latenza > 10s

## Prerequisiti
- [ ] kubectl configurato per il cluster di produzione
- [ ] Membro del team platform-engineering
- [ ] Incident dichiarato e canale aperto

## Procedura

### Step 1: Valutazione Iniziale
```

```bash
# Verificare lo stato dei pod
kubectl get pods -n production -l app=api-gateway

# Verificare i log per errori
kubectl logs -n production -l app=api-gateway --tail=50 --since=10m

# Verificare le metriche di latenza e errori
kubectl top pods -n production -l app=api-gateway

# Verificare se ci sono pod in stato anomalo
kubectl describe pods -n production -l app=api-gateway | grep -E "(State|Reason|Exit)"
```

```markdown
### Step 2: Rolling Restart
```

```bash
# Eseguire un rolling restart (zero downtime)
kubectl rollout restart deployment/api-gateway -n production

# Monitorare il rollout
kubectl rollout status deployment/api-gateway -n production --timeout=300s

# Verificare che tutti i nuovi pod siano Ready
kubectl get pods -n production -l app=api-gateway -w
```

```markdown
### Step 3: Verifica
```

```bash
# Verificare l'health endpoint
curl -s https://api.example.com/health | jq .

# Verificare la latenza
curl -o /dev/null -s -w "TTFB: %{time_starttransfer}s\n" https://api.example.com/health

# Verificare le metriche in Grafana/Prometheus
# La latenza p99 deve tornare sotto i 500ms entro 5 minuti
```

```markdown
### Rollback
```

```bash
# Se i nuovi pod non funzionano, fare rollback
kubectl rollout undo deployment/api-gateway -n production
kubectl rollout status deployment/api-gateway -n production --timeout=300s
```

### Esempio: Failover Database

```markdown
# Runbook: Failover Database PostgreSQL

## Metadata
- **Servizio:** PostgreSQL primary (RDS / self-managed)
- **Severity trigger:** SEV1 — Primary non raggiungibile

## Prerequisiti
- [ ] Accesso alla console AWS o accesso SSH ai server DB
- [ ] Credenziali DBA
- [ ] Comunicazione aperta con il team applicativo

## Procedura
```

```bash
# === Per RDS ===

# Step 1: Verificare lo stato dell'istanza primary
aws rds describe-db-instances --db-instance-identifier prod-primary \
  --query 'DBInstances[].DBInstanceStatus'

# Step 2: Verificare lo stato della replica
aws rds describe-db-instances --db-instance-identifier prod-replica \
  --query 'DBInstances[].[DBInstanceStatus, ReadReplicaSourceDBInstanceIdentifier]'

# Step 3: Promuovere la replica a primary
aws rds promote-read-replica --db-instance-identifier prod-replica

# Step 4: Monitorare la promozione (richiede circa 5-10 minuti)
watch -n 10 "aws rds describe-db-instances --db-instance-identifier prod-replica \
  --query 'DBInstances[].DBInstanceStatus' --output text"

# Step 5: Aggiornare la configurazione dell'applicazione
# Modificare il DNS o la configurazione per puntare al nuovo primary
# Se si usa Route53:
aws route53 change-resource-record-sets --hosted-zone-id Z123456 \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "db.internal.example.com",
        "Type": "CNAME",
        "TTL": 60,
        "ResourceRecords": [{"Value": "prod-replica.abc123.eu-west-1.rds.amazonaws.com"}]
      }
    }]
  }'

# Step 6: Verificare la connettivita' applicativa
psql -h db.internal.example.com -U app_user -d production -c "SELECT 1;"

# Step 7: Verificare che l'applicazione funzioni
curl -s https://api.example.com/health | jq .
```

### Esempio: Scaling Emergenza

```bash
# Runbook: Scaling Emergenza Kubernetes

# Step 1: Verificare il carico attuale
kubectl top nodes
kubectl top pods -n production --sort-by=cpu

# Step 2: Scalare il deployment
kubectl scale deployment/<deploy-name> -n production --replicas=10

# Step 3: Se i nodi sono saturi, scalare il cluster
# EKS
aws eks update-nodegroup-config \
  --cluster-name prod-cluster \
  --nodegroup-name prod-workers \
  --scaling-config minSize=5,maxSize=20,desiredSize=10

# GKE
gcloud container clusters resize prod-cluster \
  --node-pool default-pool --num-nodes 10 --zone europe-west1-b

# AKS
az aks scale -g myResourceGroup -n myAKSCluster --node-count 10

# Step 4: Verificare che i nuovi pod siano schedulati e Ready
kubectl get pods -n production -l app=<app-name> -w

# Step 5: Verificare che il servizio gestisca il carico
kubectl get hpa -n production
```

### Esempio: Certificate Renewal

```bash
# Runbook: Rinnovo Certificati TLS

# Step 1: Verificare la scadenza dei certificati attuali
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | \
  openssl x509 -noout -enddate -subject

# Step 2: Verificare i certificati in Kubernetes
kubectl get certificates -A
kubectl describe certificate <cert-name> -n <namespace>

# Con cert-manager:
# Step 3: Forzare il rinnovo
kubectl delete certificate <cert-name> -n <namespace>
# cert-manager ricreera' automaticamente il certificato

# Oppure annotare il Certificate per il rinnovo
kubectl annotate certificate <cert-name> -n <namespace> \
  cert-manager.io/renew-before="720h" --overwrite

# Step 4: Verificare lo stato del nuovo certificato
kubectl get certificaterequest -n <namespace>
kubectl get order -n <namespace>
kubectl get challenge -n <namespace>

# Step 5: Verificare che il nuovo certificato sia attivo
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | \
  openssl x509 -noout -dates -serial
```

### Esempio: Incident Response Iniziale

```bash
# Runbook: Risposta Iniziale a Incident

# Step 1: Raccolta informazioni immediate (primi 5 minuti)
echo "=== Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "=== Stato dei servizi critici ==="
kubectl get pods -n production --field-selector=status.phase!=Running
echo "=== Nodi ==="
kubectl get nodes
echo "=== Risorse ==="
kubectl top nodes
echo "=== Eventi recenti ==="
kubectl get events -n production --sort-by=.metadata.creationTimestamp | tail -20

# Step 2: Verificare i servizi esterni
curl -s -o /dev/null -w "API: %{http_code} %{time_total}s\n" https://api.example.com/health
curl -s -o /dev/null -w "Web: %{http_code} %{time_total}s\n" https://www.example.com/
curl -s -o /dev/null -w "Auth: %{http_code} %{time_total}s\n" https://auth.example.com/health

# Step 3: Verificare le dipendenze
# Database
psql -h db.internal -U monitor -c "SELECT 1;" 2>&1 | head -1
# Cache
redis-cli -h redis.internal ping
# Message queue
curl -s http://rabbitmq.internal:15672/api/overview -u monitor:pass | jq '.queue_totals'

# Step 4: Dichiarare l'incident
echo "
=== DICHIARAZIONE INCIDENT ===
Severity: SEV[N]
Impatto: [descrizione]
Servizi coinvolti: [lista]
IC: [nome]
Canale: #inc-$(date +%Y%m%d)-[descrizione]
"
```

---

## 10. Capacity Planning

### Metodologia

Il capacity planning segue un ciclo continuo in quattro fasi:

```
1. COLLECT  -> Raccogliere metriche storiche e attuali
2. ANALYZE  -> Analizzare trend e pattern di utilizzo
3. FORECAST -> Prevedere la domanda futura
4. PLAN     -> Pianificare le risorse necessarie

Ripetere il ciclo trimestralmente o prima di eventi significativi
(lancio prodotto, campagna marketing, picchi stagionali)
```

### Metriche Chiave per Resource Type

| Risorsa | Metriche | Threshold Warning | Threshold Critical |
|---|---|---|---|
| **CPU** | Utilizzo medio, p95, p99 | > 70% medio | > 85% medio |
| **Memoria** | Utilizzo, swap, OOM events | > 80% | > 90% |
| **Disco** | Spazio usato, IOPS, latenza I/O | > 75% spazio, > 80% IOPS | > 85% spazio |
| **Rete** | Bandwidth, packet loss, latenza | > 70% bandwidth | > 85% bandwidth |
| **IOPS** | Read/Write IOPS, queue depth | > 75% provisioned | > 90% provisioned |

```bash
# Raccolta metriche CPU (ultime 4 settimane in Prometheus)
# PromQL per utilizzo medio CPU per nodo
avg by (instance) (
  1 - rate(node_cpu_seconds_total{mode="idle"}[5m])
) * 100

# Memoria utilizzata per nodo
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disco — spazio utilizzato
(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100

# IOPS per disco
rate(node_disk_reads_completed_total[5m]) + rate(node_disk_writes_completed_total[5m])
```

### Forecasting Techniques

#### Linear Regression

```python
# Esempio concettuale di forecasting lineare
# con dati settimanali di utilizzo CPU medio

# Dati storici (settimana, utilizzo_cpu_pct)
# W1: 45%, W2: 47%, W3: 48%, W4: 51%, W5: 52%, W6: 55%, W7: 56%, W8: 58%

# Trend: +1.7% per settimana
# Previsione W12: 58% + (4 * 1.7%) = 64.8%
# Previsione W24: 58% + (16 * 1.7%) = 85.2% <- CRITICO

# Azione: pianificare scaling entro W20
```

#### Percentile-Based Forecasting

```bash
# Query Prometheus per il p95 di utilizzo CPU negli ultimi 30 giorni
quantile(0.95,
  avg by (instance) (
    1 - rate(node_cpu_seconds_total{mode="idle"}[5m])
  )
)

# Confrontare p95 di periodi diversi per identificare il trend
# Ultimo mese vs mese precedente vs 3 mesi fa
```

### Capacity Planning per Kubernetes

```bash
# Verificare il rapporto request/limit attuale
kubectl get pods -A -o json | jq -r '
  .items[] |
  .spec.containers[] |
  select(.resources.requests != null) |
  {
    name: .name,
    cpu_request: .resources.requests.cpu,
    cpu_limit: .resources.limits.cpu,
    mem_request: .resources.requests.memory,
    mem_limit: .resources.limits.memory
  }'

# Identificare pod con request troppo bassi (throttling) o troppo alti (sprechi)
kubectl top pods -A --sort-by=cpu | head -20

# Verificare la capacita' disponibile nel cluster
kubectl describe nodes | grep -A 5 "Allocated resources"

# Output di esempio per un nodo:
# Allocated resources:
#   (Total limits may be over 100 percent, i.e., overcommitted.)
#   Resource           Requests     Limits
#   --------           --------     ------
#   cpu                3800m (95%)  7600m (190%)
#   memory             6Gi (78%)   12Gi (156%)

# Cluster Autoscaler — verificare lo stato
kubectl get configmap -n kube-system cluster-autoscaler-status -o yaml

# Verificare i pod che non possono essere schedulati
kubectl get events -A --field-selector reason=FailedScheduling --sort-by='.lastTimestamp'
```

### Cloud Cost vs Capacity Trade-offs

```
Strategia            | Costo    | Capacita'    | Rischio
---------------------|----------|--------------|--------
Reserved Instances   | Basso    | Garantita    | Lock-in (1-3 anni)
On-Demand            | Alto     | Immediata    | Nessuno
Spot/Preemptible     | Molto basso | Non garantita | Interruzione
Autoscaling          | Variabile| Elastica     | Cold start, delay
Over-provisioning    | Alto     | Sempre pronta| Spreco
```

### Capacity Alerts e Thresholds

```yaml
# Esempio configurazione alert Prometheus per capacity
groups:
  - name: capacity-alerts
    rules:
      - alert: DiskSpaceWarning
        expr: (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) > 0.75
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Disco al {{ $value | humanizePercentage }} su {{ $labels.instance }}"

      - alert: DiskSpaceCritical
        expr: (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) > 0.85
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "CRITICO: Disco al {{ $value | humanizePercentage }} su {{ $labels.instance }}"

      - alert: CPUCapacityWarning
        expr: avg by (instance) (1 - rate(node_cpu_seconds_total{mode="idle"}[5m])) > 0.70
        for: 30m
        labels:
          severity: warning

      - alert: MemoryCapacityWarning
        expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.80
        for: 15m
        labels:
          severity: warning
```

### Seasonal Planning

```
Esempio e-commerce — Pattern stagionale annuale:

Gen-Feb:  Basso     (baseline)          -> Ridurre capacita' (spot, scale-down)
Mar-Apr:  Medio     (primavera)         -> Capacita' standard
Mag-Giu:  Medio     (inizio estate)     -> Capacita' standard
Lug-Ago:  Basso     (vacanze estive)    -> Ridurre capacita'
Set-Ott:  Alto      (back to school)    -> Pre-scale +30%
Nov:      Molto alto (Black Friday)     -> Pre-scale +100%, test di carico
Dic:      Molto alto (Natale)           -> Mantenere capacita' elevata
```

---

## 11. Cost Optimization

### Cloud Cost Anatomy

```
Struttura dei costi cloud tipica:

Compute (40-60%)
  - VM / istanze
  - Container (EKS, AKS, GKE)
  - Serverless (Lambda, Functions)

Storage (15-25%)
  - Block storage (EBS, Managed Disks)
  - Object storage (S3, Blob, GCS)
  - Database storage

Network (10-20%)
  - Data transfer (egress)
  - Load balancer
  - VPN / Direct Connect
  - CDN

Licensing & Other (5-15%)
  - Software licenses (Windows, RHEL)
  - Support plans
  - Marketplace subscriptions
  - DNS / domain
```

### AWS Cost Optimization

```bash
# Identificare le risorse inutilizzate

# EC2 — istanze con CPU < 5% per 14 giorni
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-abc123 \
  --start-time $(date -d '14 days ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average

# EBS — volumi non collegati
aws ec2 describe-volumes \
  --filters "Name=status,Values=available" \
  --query 'Volumes[].[VolumeId, Size, CreateTime]' \
  --output table

# Elastic IP non associate
aws ec2 describe-addresses \
  --query 'Addresses[?AssociationId==`null`].[PublicIp, AllocationId]' \
  --output table

# Load balancer senza target
aws elbv2 describe-target-groups \
  --query 'TargetGroups[?length(LoadBalancerArns)==`0`].[TargetGroupName, TargetGroupArn]'

# RDS — istanze idle
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=my-db \
  --start-time $(date -d '7 days ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Maximum

# Analisi costi con AWS Cost Explorer CLI
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --output table
```

**Reserved Instances vs Savings Plans:**

```
Tipo                  | Flessibilita'  | Sconto  | Commitment
----------------------|----------------|---------|----------
Standard RI           | Bassa (istanza fissa) | 40-60%  | 1-3 anni
Convertible RI        | Media (cambio famiglia) | 30-50%  | 1-3 anni
Compute Savings Plan  | Alta (qualsiasi compute) | 30-50% | 1-3 anni
EC2 Instance SP       | Media (famiglia fissa) | 35-55%  | 1-3 anni

Regola: Savings Plans per nuove adozioni, RI solo se gia' in uso
```

**Spot Instances:**

```bash
# Verificare i prezzi spot attuali
aws ec2 describe-spot-price-history \
  --instance-types m5.xlarge \
  --start-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --product-descriptions "Linux/UNIX" \
  --query 'SpotPriceHistory[].[AvailabilityZone, SpotPrice]' \
  --output table

# Tipicamente 60-90% di sconto rispetto a on-demand
# Adatto per: batch processing, CI/CD runners, workload stateless
# NON adatto per: database, servizi stateful, carichi critici senza failover
```

### Azure Cost Optimization

```bash
# Raccomandazioni di Azure Advisor
az advisor recommendation list --category Cost --output table

# Verificare le VM sotto-utilizzate
az monitor metrics list \
  --resource /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Compute/virtualMachines/<vm> \
  --metric "Percentage CPU" \
  --interval PT1H \
  --start-time $(date -d '7 days ago' -u +%Y-%m-%dT%H:%M:%SZ) \
  --output table

# Reserved VM Instances
az reservations reservation-order list --output table
```

### GCP Cost Optimization

```bash
# Raccomandazioni per right-sizing
gcloud recommender recommendations list \
  --recommender=google.compute.instance.MachineTypeRecommender \
  --project=my-project \
  --location=europe-west1-b \
  --format=table

# Committed Use Discounts (CUD)
gcloud compute commitments list --format=table

# Verificare le VM idle
gcloud recommender recommendations list \
  --recommender=google.compute.instance.IdleResourceRecommender \
  --project=my-project \
  --location=europe-west1-b
```

### Kubernetes Cost Optimization

```bash
# Identificare pod con risorse sovradimensionate
# (request molto piu' alto dell'utilizzo effettivo)
kubectl top pods -A --sort-by=cpu | head -20
kubectl top pods -A --sort-by=memory | head -20

# Confrontare request con utilizzo effettivo
# PromQL per rapporto utilizzo/request CPU
sum by (namespace, pod) (rate(container_cpu_usage_seconds_total[5m]))
/
sum by (namespace, pod) (kube_pod_container_resource_requests{resource="cpu"})

# Identificare namespace con piu' sprechi
# PromQL: memoria richiesta ma non utilizzata per namespace
sum by (namespace) (
  kube_pod_container_resource_requests{resource="memory"}
  -
  container_memory_working_set_bytes
)

# Verificare la configurazione del Cluster Autoscaler
kubectl get deployment -n kube-system cluster-autoscaler -o yaml | \
  grep -A 20 "command:"

# Nodi spot/preemptible nel cluster
kubectl get nodes -l "node.kubernetes.io/lifecycle=spot"
```

### Tools per Cost Management

```bash
# Kubecost — installazione rapida
helm install kubecost cost-analyzer \
  --repo https://kubecost.github.io/cost-analyzer/ \
  --namespace kubecost --create-namespace

# Accesso alla dashboard
kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090

# Infracost — stima costi IaC prima del deploy
infracost breakdown --path=./terraform/
infracost diff --path=./terraform/

# Output di esempio:
# NAME                       MONTHLY QTY  UNIT       MONTHLY COST
# aws_instance.web           730          hours      $65.70
# aws_db_instance.primary    730          hours      $186.00
# aws_s3_bucket.assets       1000         GB-months  $23.00
# TOTAL                                              $274.70
```

### FinOps Practices

```
Principi FinOps fondamentali:

1. Visibilita' — Ogni team vede i propri costi
   - Tagging obbligatorio su tutte le risorse
   - Dashboard per team/progetto/ambiente
   - Report settimanali automatici

2. Ottimizzazione — Ridurre gli sprechi continuamente
   - Review mensile delle risorse inutilizzate
   - Right-sizing trimestrale
   - Commitment planning annuale

3. Accountability — Ogni team e' responsabile dei propri costi
   - Budget per team con alert
   - Costi nel definition of done
   - Cost review nelle retrospettive

Tagging strategy minima:
- team: <nome-team>
- environment: production | staging | development
- project: <nome-progetto>
- cost-center: <codice>
- managed-by: terraform | manual | helm
```

---

## 12. Disaster Recovery

### DR Strategies

```
Strategia        | RTO      | RPO      | Costo   | Complessita'
-----------------|----------|----------|---------|-------------
Backup/Restore   | Ore      | Ore-Giorni| Basso  | Bassa
Pilot Light      | 10-30 min| Minuti   | Medio  | Media
Warm Standby     | Minuti   | Secondi-Min| Alto  | Alta
Multi-Site A/A   | Secondi  | Zero     | Molto alto | Molto alta

Backup/Restore:
  - Backup regolari in una region diversa
  - In caso di disastro: provisioning infrastruttura + restore dati
  - Adatto per: sistemi non critici, ambienti dev/staging

Pilot Light:
  - Componenti core (database) replicati costantemente
  - Infrastruttura compute pre-configurata ma spenta
  - In caso di disastro: accendere compute + scalare
  - Adatto per: sistemi con RTO tollerabile di 15-30 minuti

Warm Standby:
  - Copia scaled-down dell'ambiente completo
  - Traffico reale minimo (canary) per verificare funzionamento
  - In caso di disastro: scalare a full capacity + switch DNS
  - Adatto per: sistemi business-critical

Multi-Site Active-Active:
  - Due o piu' region gestiscono traffico reale simultaneamente
  - Load balancer globale distribuisce il traffico
  - In caso di disastro: il traffico va automaticamente alle region sane
  - Adatto per: sistemi mission-critical con SLA > 99.99%
```

### RTO/RPO Planning Matrix

```
Servizio            | Business Impact  | RTO Target | RPO Target | Strategia DR
--------------------|------------------|------------|------------|-------------
Payment API         | Critico (revenue)| 5 min      | 0          | Multi-Site A/A
User Database       | Critico          | 15 min     | < 1 min    | Warm Standby
Product Catalog     | Alto             | 30 min     | < 5 min    | Warm Standby
Email Service       | Medio            | 2 ore      | < 1 ora    | Pilot Light
Analytics Platform  | Basso            | 24 ore     | < 24 ore   | Backup/Restore
Internal Wiki       | Basso            | 48 ore     | < 24 ore   | Backup/Restore
```

### DR Testing

```
Tipi di DR test (in ordine crescente di realismo):

1. Tabletop Exercise
   - Discussione teorica del piano DR
   - Nessun sistema reale coinvolto
   - Frequenza: trimestrale
   - Durata: 1-2 ore

2. Walkthrough Test
   - Revisione passo-passo delle procedure
   - Verifica dell'accesso ai sistemi e credenziali
   - Frequenza: semestrale
   - Durata: 2-4 ore

3. Simulation Test
   - Simulazione di un disastro specifico
   - Sistemi reali coinvolti ma senza impatto su produzione
   - Frequenza: annuale
   - Durata: 4-8 ore

4. Full Interruption Test
   - Failover reale sull'ambiente DR
   - Traffico di produzione spostato
   - Frequenza: annuale (con finestra di manutenzione)
   - Durata: 8-24 ore
```

### DR Runbook Template

```markdown
# Runbook: Disaster Recovery — [Scenario Specifico]

## Scenario
[Descrizione dettagliata del disastro: region down, data center failure, etc.]

## Pre-condizioni
- [ ] DR site operativo e sincronizzato
- [ ] DNS TTL ridotto a 60s (almeno 24h prima del test)
- [ ] Team di comunicazione allertato
- [ ] Monitoring configurato su entrambe le region

## Fase 1: Dichiarazione Disastro (0-5 min)
1. IC conferma che il disastro soddisfa i criteri di attivazione DR
2. Notifica a tutti gli stakeholder
3. Apertura war room

## Fase 2: Failover (5-30 min)
1. [Procedura specifica per failover]
2. [Verifica replicazione dati]
3. [Switch DNS / traffic routing]

## Fase 3: Verifica (30-60 min)
1. [Test funzionali]
2. [Verifica integrita' dati]
3. [Monitoraggio metriche]

## Fase 4: Comunicazione
1. Status page aggiornata
2. Notifica clienti (se necessario)
3. Aggiornamento interno

## Failback (quando la region primaria e' ripristinata)
1. [Procedura di risincronizzazione dati]
2. [Test sulla region primaria]
3. [Switch graduale del traffico]
4. [Verifica finale]
```

### Cross-Region Failover Procedures

```bash
# === AWS Cross-Region Failover ===

# Step 1: Verificare lo stato della region secondaria
aws ec2 describe-instances --region eu-central-1 \
  --filters "Name=tag:Role,Values=dr-standby" \
  --query 'Reservations[].Instances[].[InstanceId, State.Name]'

# Step 2: Avviare le istanze DR
aws ec2 start-instances --region eu-central-1 \
  --instance-ids i-dr001 i-dr002 i-dr003

# Step 3: Promuovere la replica RDS cross-region
aws rds promote-read-replica-db-cluster \
  --db-cluster-identifier prod-dr-cluster \
  --region eu-central-1

# Step 4: Switch Route53 (failover DNS)
aws route53 change-resource-record-sets --hosted-zone-id Z123 \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z456",
          "DNSName": "alb-dr.eu-central-1.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'

# Step 5: Verificare il failover
dig api.example.com
curl -s https://api.example.com/health | jq .
```

### Data Consistency in DR

```
Sfide di consistenza dati nel DR:

1. Replicazione asincrona
   - Possibile perdita degli ultimi N secondi di dati
   - Soluzione: definire RPO accettabile e monitorare il lag

2. Transazioni in-flight
   - Transazioni non completate al momento del disastro
   - Soluzione: retry a livello applicativo, idempotency

3. Split-brain
   - Due region che credono entrambe di essere il primary
   - Soluzione: fencing (STONITH), consensus protocol, arbitro esterno

4. Riferimenti incrociati
   - Dati che referenziano entita' in altri sistemi
   - Soluzione: replicazione atomica multi-sistema o eventual consistency

Verifica post-failover:
```

```sql
-- Verificare la consistenza dei dati dopo il failover
-- Confrontare i contatori tra primary e DR

-- Conteggio record nelle tabelle critiche
SELECT 'orders' AS table_name, count(*) AS row_count FROM orders
UNION ALL
SELECT 'users', count(*) FROM users
UNION ALL
SELECT 'payments', count(*) FROM payments;

-- Verificare l'ultima transazione
SELECT max(created_at) AS last_transaction FROM orders;

-- Identificare potenziali dati orfani
SELECT o.id FROM orders o
LEFT JOIN payments p ON o.id = p.order_id
WHERE o.status = 'paid' AND p.id IS NULL;
```

### Communication Plan

```
Matrice di comunicazione durante DR:

Audience          | Canale             | Frequenza        | Responsabile
------------------|--------------------|------------------|-------------
Team tecnico      | Slack war room     | Continuo         | IC
Management        | Email + call       | Ogni 30 min      | Communications Lead
Customer support  | Email + briefing   | Ogni 30 min      | Support Manager
Clienti enterprise| Email diretta      | A inizio e fine  | Account Manager
Tutti i clienti   | Status page        | Ogni 15 min      | Communications Lead
Stampa/pubblico   | Solo se necessario | Su approvazione  | PR/Comms team
```

### Lessons Learned Process

```markdown
# Template Post-Mortem DR Test/Incident

## Informazioni Generali
- **Data del test/incident:** YYYY-MM-DD
- **Tipo:** Test pianificato / Incident reale
- **Scenario:** [descrizione]
- **Durata totale:** [ore:minuti]

## Obiettivi e Risultati
| Obiettivo | Target | Risultato | Esito |
|---|---|---|---|
| RTO Payment API | < 5 min | 8 min | FAIL |
| RPO Database | < 1 min | 30 sec | PASS |
| DNS Failover | < 2 min | 1 min 45 sec | PASS |

## Cosa Ha Funzionato
- [Punto 1]
- [Punto 2]

## Cosa Non Ha Funzionato
- [Punto 1 con dettagli]
- [Punto 2 con dettagli]

## Azioni Correttive
| Azione | Responsabile | Scadenza | Priorita' |
|---|---|---|---|
| [Azione 1] | [Nome] | [Data] | Alta |
| [Azione 2] | [Nome] | [Data] | Media |
```

---

## 13. Checklist Operative

### Checklist Pre-Deployment

```markdown
## Pre-Deployment Checklist

### Codice e Test
- [ ] Tutti i test unitari passano
- [ ] Test di integrazione passano
- [ ] Code review approvata da almeno un revisore
- [ ] Nessun TODO critico nel codice da deployare
- [ ] Nessuna dipendenza con vulnerabilita' note (npm audit, pip audit)
- [ ] Le migrazioni database sono state testate in staging

### Configurazione
- [ ] Le variabili d'ambiente sono configurate per l'ambiente target
- [ ] I secret necessari sono presenti nel vault/secret manager
- [ ] La configurazione e' stata validata (dry-run / template rendering)
- [ ] Le feature flag sono configurate correttamente

### Infrastruttura
- [ ] Le risorse necessarie sono disponibili (CPU, memoria, storage)
- [ ] I security group / firewall rules sono configurati
- [ ] I certificati TLS sono validi e non in scadenza imminente
- [ ] Il DNS e' configurato correttamente

### Deployment
- [ ] La strategia di deployment e' definita (rolling, blue-green, canary)
- [ ] La procedura di rollback e' documentata e testata
- [ ] Il team di supporto e' stato avvisato
- [ ] La finestra di deployment e' stata comunicata
- [ ] Il monitoring e' attivo e gli alert sono configurati

### Comunicazione
- [ ] Il team on-call e' stato avvisato
- [ ] Lo stakeholder di riferimento e' informato
- [ ] Il canale di comunicazione per il deployment e' aperto
```

### Checklist Post-Deployment

```markdown
## Post-Deployment Checklist

### Verifica Immediata (primi 15 minuti)
- [ ] L'applicazione risponde agli health check
- [ ] I log non mostrano errori critici
- [ ] Le metriche chiave sono nella norma:
  - [ ] Latenza p99 < [threshold]
  - [ ] Error rate < [threshold]
  - [ ] Throughput nella norma
- [ ] I pod/container sono tutti in stato Running/Ready
- [ ] Le connessioni al database sono stabili

### Verifica Funzionale (primi 30 minuti)
- [ ] I flussi utente principali funzionano (smoke test)
- [ ] Le integrazioni con servizi esterni funzionano
- [ ] Le migrazioni database sono state completate correttamente
- [ ] I job asincroni / worker sono operativi
- [ ] Le code di messaggi non hanno backlog anomalo

### Monitoraggio Continuo (prime 2 ore)
- [ ] Nessun aumento anomalo di errori
- [ ] Nessun memory leak rilevato
- [ ] Le performance sono stabili nel tempo
- [ ] Nessun alert attivato

### Documentazione
- [ ] Il changelog e' stato aggiornato
- [ ] La versione deployata e' registrata
- [ ] Eventuali anomalie sono state documentate
- [ ] Il team on-call e' stato aggiornato sulla nuova versione
```

### Checklist Security Review

```markdown
## Security Review Checklist

### Autenticazione e Autorizzazione
- [ ] Tutti gli endpoint richiedono autenticazione (tranne quelli esplicitamente pubblici)
- [ ] I ruoli e i permessi sono verificati ad ogni richiesta
- [ ] Le password sono hashate con algoritmo sicuro (bcrypt, Argon2)
- [ ] I token di sessione hanno scadenza appropriata
- [ ] Il logout invalida effettivamente la sessione

### Input Validation
- [ ] Tutti gli input utente sono validati e sanitizzati
- [ ] Le query al database sono parametrizzate (nessuna concatenazione di stringhe)
- [ ] Gli upload di file verificano tipo, dimensione e contenuto
- [ ] Gli header HTTP sono validati
- [ ] Nessun uso di eval() o funzioni equivalenti con input utente

### Data Protection
- [ ] I dati sensibili sono cifrati a riposo (AES-256 o equivalente)
- [ ] Le comunicazioni avvengono su TLS 1.2+
- [ ] I log non contengono dati sensibili (password, token, PII)
- [ ] I secret non sono committati nel repository
- [ ] Le risposte di errore non espongono dettagli interni

### HTTP Security Headers
- [ ] Strict-Transport-Security (HSTS) configurato
- [ ] Content-Security-Policy configurato
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY o SAMEORIGIN
- [ ] Referrer-Policy configurata

### Dipendenze
- [ ] Nessuna vulnerabilita' critica nelle dipendenze (audit eseguito)
- [ ] Le dipendenze sono aggiornate alla versione stabile piu' recente
- [ ] Le licenze delle dipendenze sono compatibili

### Logging e Monitoring
- [ ] I tentativi di accesso falliti sono loggati
- [ ] Le operazioni privilegiate sono loggati con audit trail
- [ ] Alert configurati per pattern sospetti (brute force, privilege escalation)
```

### Checklist Infrastructure Change

```markdown
## Infrastructure Change Checklist

### Pre-Change
- [ ] Change request approvata (se necessario dal change advisory board)
- [ ] Impatto valutato: quali servizi sono coinvolti?
- [ ] Backup dello stato attuale dell'infrastruttura
- [ ] Procedura di rollback documentata
- [ ] Finestra di manutenzione schedulata (se necessario)
- [ ] Team coinvolti notificati

### Esecuzione
- [ ] Terraform plan / IaC dry-run eseguito e verificato
- [ ] Le modifiche sono state applicate in ambiente di staging prima
- [ ] Applicare le modifiche in produzione durante la finestra pianificata
- [ ] Monitorare attivamente durante l'applicazione
- [ ] Verificare che le risorse create/modificate siano corrette

### Post-Change
- [ ] Tutti i servizi dipendenti funzionano correttamente
- [ ] Le metriche infrastrutturali sono normali
- [ ] Il monitoraggio e' attivo sulle nuove risorse
- [ ] La documentazione infrastrutturale e' aggiornata
- [ ] I costi sono in linea con le aspettative
- [ ] Lo stato IaC (Terraform state) e' consistente
```

### Checklist Database Migration

```markdown
## Database Migration Checklist

### Pre-Migration
- [ ] La migrazione e' stata testata su un dump di produzione
- [ ] Il tempo stimato di esecuzione e' noto
- [ ] L'impatto sulla disponibilita' del servizio e' valutato
- [ ] Il backup del database e' stato eseguito e verificato
- [ ] La procedura di rollback (migration down) e' testata
- [ ] Il team applicativo e' informato
- [ ] Le connessioni al database possono gestire il lock (se necessario)

### Esecuzione
- [ ] Attivare la maintenance window (se necessaria)
- [ ] Eseguire la migrazione con logging verboso
- [ ] Monitorare il lock sulle tabelle e le connessioni attive
- [ ] Verificare che la migrazione sia completata senza errori

### Post-Migration
- [ ] Verificare lo schema: le tabelle, colonne, indici sono corretti
- [ ] Verificare i dati: conteggi e integrita' referenziale
- [ ] Verificare le performance: le query critiche non sono degradate
- [ ] ANALYZE / VACUUM sulle tabelle modificate (PostgreSQL)
- [ ] Verificare che l'applicazione funzioni con il nuovo schema
- [ ] Aggiornare la documentazione dello schema
```

### Checklist Incident Post-Mortem

```markdown
## Incident Post-Mortem Checklist

### Preparazione (entro 48 ore dall'incident)
- [ ] Timeline degli eventi raccolta da tutti i partecipanti
- [ ] Log e metriche salvate per il periodo dell'incident
- [ ] Partecipanti identificati: chi ha lavorato sull'incident?
- [ ] Post-mortem meeting schedulato
- [ ] Template post-mortem compilato con i fatti noti

### Durante il Meeting
- [ ] Revisione della timeline: e' accurata e completa?
- [ ] Identificazione della causa radice (root cause analysis)
- [ ] Applicazione della tecnica dei "5 Whys"
- [ ] Identificazione dei contributing factors
- [ ] Discussione: cosa ha funzionato bene?
- [ ] Discussione: cosa non ha funzionato?
- [ ] Nessun assegnamento di colpa — focus sui sistemi, non sulle persone
- [ ] Definizione delle azioni correttive con owner e scadenza

### Post-Meeting
- [ ] Documento post-mortem finalizzato e condiviso
- [ ] Azioni correttive registrate nel sistema di tracking (Jira, etc.)
- [ ] Alert e monitoring aggiornati per prevenire ricorrenza
- [ ] Runbook aggiornati o creati se mancanti
- [ ] Lezioni apprese condivise con il team allargato
- [ ] Follow-up schedulato per verificare il completamento delle azioni
```

### Checklist Nuovo Servizio in Produzione

```markdown
## Production Readiness Checklist

### Codice e Architettura
- [ ] Il servizio ha un health check endpoint (/health o /healthz)
- [ ] Il servizio ha un readiness endpoint (se in Kubernetes)
- [ ] Graceful shutdown implementato (gestione SIGTERM)
- [ ] Retry con exponential backoff per chiamate a servizi esterni
- [ ] Circuit breaker configurato per dipendenze critiche
- [ ] Timeouts configurati per tutte le chiamate esterne
- [ ] Idempotency implementata dove necessario

### Observability
- [ ] Logging strutturato (JSON) con correlation ID
- [ ] Metriche esposte (RED: Rate, Errors, Duration)
- [ ] Tracing distribuito integrato (OpenTelemetry)
- [ ] Dashboard Grafana creata con metriche chiave
- [ ] Alert configurati per errori, latenza, saturazione

### Sicurezza
- [ ] Security review completata
- [ ] Autenticazione e autorizzazione implementate
- [ ] Secret gestiti tramite vault/secret manager
- [ ] Dependency audit senza vulnerabilita' critiche
- [ ] Rate limiting configurato

### Resilienza
- [ ] Testato con failure injection (chaos engineering)
- [ ] Capacita' di funzionare in modalita' degradata
- [ ] Auto-scaling configurato (HPA in Kubernetes)
- [ ] Resource limits configurati (CPU, memoria)
- [ ] PodDisruptionBudget configurato

### Operativita'
- [ ] Runbook creato per le operazioni comuni
- [ ] Procedura di deployment documentata
- [ ] Procedura di rollback documentata e testata
- [ ] On-call rotation configurata
- [ ] SLI/SLO definiti e monitorati
- [ ] Capacity planning iniziale completato
- [ ] Backup e disaster recovery pianificati

### Documentazione
- [ ] Architettura del servizio documentata
- [ ] API documentata (OpenAPI/Swagger)
- [ ] Dipendenze documentate (upstream e downstream)
- [ ] Diagramma di flusso dei dati
- [ ] Contatti del team proprietario aggiornati
```

---

## 14. Chaos Engineering

### Principi Fondamentali

La chaos engineering non e' "rompere cose in produzione" — e' il processo scientifico di formulare ipotesi sulla resilienza del sistema e verificarle attraverso esperimenti controllati. Il Chaos Engineering Manifesto (principlesofchaos.org) definisce cinque principi cardine:

1. **Definire lo steady state** — comportamento normale misurabile (latenza p99 < 200ms, error rate < 0.1%)
2. **Ipotizzare che lo steady state si manterra'** — anche sotto perturbazione
3. **Introdurre variabili del mondo reale** — network partition, CPU saturation, pod failure, clock skew
4. **Cercare di confutare l'ipotesi** — se lo steady state si degrada, hai trovato una debolezza
5. **Minimizzare il blast radius** — iniziare piccoli, scalare gradualmente

### Steady-State Hypothesis

Prima di ogni esperimento, documentare formalmente:

```yaml
# Esempio: steady-state hypothesis per un servizio e-commerce
experiment:
  name: "checkout-resilience-under-payment-failure"
  description: "Il servizio checkout gestisce correttamente il fallimento del payment gateway"

  steady_state_hypothesis:
    title: "Il checkout rimane funzionale"
    probes:
      - name: "checkout-latency-p99"
        type: "probe"
        provider:
          type: "prometheus"
          query: "histogram_quantile(0.99, rate(checkout_duration_seconds_bucket[5m]))"
        tolerance:
          type: "range"
          range: [0, 2.0]   # max 2 secondi

      - name: "checkout-error-rate"
        type: "probe"
        provider:
          type: "prometheus"
          query: "rate(checkout_errors_total[5m]) / rate(checkout_requests_total[5m])"
        tolerance:
          type: "range"
          range: [0, 0.05]  # max 5% errori

  method:
    - type: "action"
      name: "kill-payment-service"
      provider:
        type: "kubernetes"
        action: "terminate_pods"
        label_selector: "app=payment-gateway"
        qty: 2              # termina 2 repliche su 3

  rollbacks:
    - type: "action"
      name: "restore-payment-service"
      provider:
        type: "kubernetes"
        action: "scale_deployment"
        deployment: "payment-gateway"
        replicas: 3
```

### Strumenti di Chaos Engineering

#### Litmus Chaos (CNCF)

```bash
# Installare Litmus 3.x
helm repo add litmuschaos https://litmuschaos.github.io/litmus-helm/
helm install litmus litmuschaos/litmus \
  --namespace litmus --create-namespace \
  --set portal.frontend.service.type=NodePort

# Creare un ChaosExperiment per pod-delete
kubectl apply -f - <<'EOF'
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: payment-chaos
  namespace: production
spec:
  appinfo:
    appns: production
    applabel: "app=payment-gateway"
    appkind: deployment
  engineState: active
  chaosServiceAccount: litmus-admin
  experiments:
    - name: pod-delete
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: "60"
            - name: CHAOS_INTERVAL
              value: "10"
            - name: FORCE
              value: "false"
            - name: PODS_AFFECTED_PERC
              value: "50"
EOF

# Monitorare il risultato
kubectl get chaosresult payment-chaos-pod-delete -n production -o yaml
```

#### Chaos Toolkit (Open Source)

```bash
# Installare con plugin Kubernetes
pip install chaostoolkit chaostoolkit-kubernetes chaostoolkit-prometheus

# Eseguire un esperimento
chaos run experiment.json --journal-path results/journal.json

# Verificare il report
chaos report --export-format=pdf results/journal.json report.pdf
```

### GameDay: Organizzazione Pratica

Un GameDay e' un evento strutturato in cui il team esegue esperimenti di chaos in ambiente controllato. Struttura raccomandata:

```
FASE 1 — Preparazione (1 settimana prima)
├── Selezionare scenario di failure
├── Definire steady-state hypothesis
├── Preparare rollback automatici
├── Notificare stakeholder
└── Verificare che monitoring sia funzionante

FASE 2 — Esecuzione (giorno del GameDay)
├── Briefing team (15 min)
├── Verificare steady state baseline
├── Eseguire esperimento
├── Osservare metriche in real-time
├── Documentare osservazioni
└── Eseguire rollback se necessario

FASE 3 — Analisi (entro 48 ore)
├── Confrontare risultati con hypothesis
├── Identificare failure mode scoperti
├── Creare action items per remediation
└── Aggiornare runbook con nuovi scenari

FASE 4 — Remediation (sprint successivo)
├── Implementare fix identificati
├── Aggiungere test di resilienza in CI
└── Schedulare prossimo GameDay
```

### Chaos in CI/CD Pipeline

Integrare esperimenti di chaos nelle pipeline per prevenire regressioni di resilienza:

```yaml
# .github/workflows/chaos-ci.yml
name: Resilience Tests
on:
  schedule:
    - cron: '0 3 * * 1'  # Ogni lunedi' alle 3:00 UTC
  workflow_dispatch:

jobs:
  chaos-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        run: kubectl apply -k overlays/staging/
      - name: Wait for ready
        run: kubectl rollout status deployment/app -n staging --timeout=300s
      - name: Run chaos experiment
        run: |
          pip install chaostoolkit chaostoolkit-kubernetes
          chaos run experiments/pod-failure.json
      - name: Collect results
        if: always()
        run: chaos report --export-format=pdf journal.json chaos-report.pdf
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: chaos-report
          path: chaos-report.pdf
```

---

## 15. Observability-Driven Debugging

### Pipeline OpenTelemetry

OpenTelemetry (OTel) unifica traces, metriche e log in un unico framework di osservabilita'. La pipeline tipica:

```
Applicazione (SDK OTel)
    │
    ▼
OTel Collector (Agent mode — DaemonSet)
    │
    ├── Processor: batch, memory_limiter, tail_sampling
    │
    ▼
OTel Collector (Gateway mode — Deployment)
    │
    ├─► Traces → Jaeger / Tempo / Zipkin
    ├─► Metriche → Prometheus / Mimir
    └─► Log → Loki / Elasticsearch
```

#### Configurazione Collector Ottimizzata

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    send_batch_size: 8192
    timeout: 200ms

  memory_limiter:
    check_interval: 1s
    limit_mib: 1500
    spike_limit_mib: 500

  tail_sampling:
    decision_wait: 10s
    policies:
      - name: errors-policy
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: latency-policy
        type: latency
        latency: {threshold_ms: 1000}
      - name: probabilistic-policy
        type: probabilistic
        probabilistic: {sampling_percentage: 10}

exporters:
  otlp/tempo:
    endpoint: tempo-distributor.observability:4317
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889
  loki:
    endpoint: http://loki-gateway.observability:3100/loki/api/v1/push

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, tail_sampling, batch]
      exporters: [otlp/tempo]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [loki]
```

### Correlazione Trace-to-Log

Il valore reale dell'osservabilita' emerge quando si correla un trace lento con i log esatti prodotti durante quella transazione:

```bash
# 1. Trovare trace ID di richieste lente da Prometheus
#    (richiede exemplar support abilitato)
curl -G 'http://prometheus:9090/api/v1/query' \
  --data-urlencode 'query=histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service="checkout"}[5m]))'

# 2. Da Tempo/Jaeger, cercare il trace ID
curl 'http://tempo:3200/api/traces/abc123def456'

# 3. Da Loki, filtrare i log per quel trace ID
curl -G 'http://loki:3100/loki/api/v1/query_range' \
  --data-urlencode 'query={service="checkout"} |= "abc123def456"'
```

Per abilitare la correlazione automatica, iniettare `trace_id` e `span_id` nei log strutturati:

```python
# Python con OpenTelemetry
import logging
from opentelemetry import trace

class TraceContextFilter(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        ctx = span.get_span_context()
        record.trace_id = format(ctx.trace_id, '032x') if ctx.trace_id else ""
        record.span_id = format(ctx.span_id, '016x') if ctx.span_id else ""
        return True

logger = logging.getLogger(__name__)
logger.addFilter(TraceContextFilter())
formatter = logging.Formatter(
    '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
    '"trace_id":"%(trace_id)s","span_id":"%(span_id)s",'
    '"message":"%(message)s"}'
)
```

### Strategie di Sampling

Il volume di trace in produzione puo' essere enorme. Le strategie di sampling bilanciano costo e visibilita':

| Strategia | Pro | Contro | Quando usare |
|---|---|---|---|
| **Head-based probabilistic** | Semplice, basso overhead | Perde trace importanti | Sviluppo, staging |
| **Tail-based** | Cattura errori e outlier | Richiede collector gateway | Produzione |
| **Rate-limited** | Prevedibile nel costo | Campionamento non uniforme | Alto throughput |
| **Always-on per errori** | Zero trace persi per failure | Volume elevato se error rate alto | Servizi critici |

La configurazione ottimale per produzione combina tail-based sampling con always-on per errori (come mostrato nel collector config sopra).

### eBPF per Osservabilita' Kernel-Level

eBPF (extended Berkeley Packet Filter) permette osservabilita' a livello kernel senza modificare le applicazioni. Strumenti come Cilium Hubble e Tetragon forniscono visibilita' su rete e sicurezza:

```bash
# Installare Cilium con Hubble abilitato
cilium install --set hubble.relay.enabled=true --set hubble.ui.enabled=true

# Osservare flussi di rete in real-time
hubble observe --namespace production --protocol http \
  --verdict DROPPED --follow

# Tetragon: monitorare syscall sospette (security + debugging)
kubectl apply -f - <<'EOF'
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: detect-file-access
spec:
  kprobes:
    - call: "fd_install"
      syscall: false
      args:
        - index: 0
          type: "int"
        - index: 1
          type: "file"
      selectors:
        - matchArgs:
            - index: 1
              operator: "Prefix"
              values:
                - "/etc/shadow"
                - "/etc/passwd"
EOF

# Osservare eventi Tetragon
kubectl logs -n kube-system -l app.kubernetes.io/name=tetragon -f | \
  tetra getevents -o compact
```

### Flowchart: Debug con Osservabilita'

```
Utente segnala lentezza
│
├─ 1. Controllare metriche aggregate
│     Dashboard Grafana → quale servizio ha latenza anomala?
│
├─ 2. Trovare trace esemplare
│     Prometheus exemplar → trace_id del p99
│
├─ 3. Analizzare trace distribuito
│     Tempo/Jaeger → quale span e' il bottleneck?
│     └─ Span lento identificato (es. database query)
│
├─ 4. Correlare con log
│     Loki query: {service="X"} |= "trace_id"
│     └─ Log mostra: "slow query: SELECT * FROM orders WHERE ..."
│
├─ 5. Analisi root cause
│     └─ Query manca indice su colonna filtrata
│
└─ 6. Fix e verifica
      └─ Aggiungere indice → verificare che p99 rientri nello SLO
```

---

## 16. SLO, Error Budget e Affidabilita'

### Gerarchia SLI → SLO → SLA

| Livello | Definizione | Esempio | Chi lo definisce |
|---|---|---|---|
| **SLI** | Metrica grezza | Rapporto richieste con latenza < 300ms / totale richieste | Engineering |
| **SLO** | Target interno | 99.9% delle richieste sotto 300ms su finestra 30 giorni | Engineering + Product |
| **SLA** | Contratto esterno | 99.5% uptime con penali finanziarie se violato | Business + Legal |

Lo SLO deve essere sempre piu' stretto dello SLA per avere margine operativo.

### Calcolo dell'Error Budget

```
Error Budget = 1 - SLO

Esempio con SLO 99.9%:
  Error Budget = 0.1% = 0.001
  In 30 giorni (43,200 minuti):
    Budget disponibile = 43,200 × 0.001 = 43.2 minuti di downtime

  In richieste (10M richieste/mese):
    Budget disponibile = 10,000,000 × 0.001 = 10,000 richieste fallite ammesse
```

### Error Budget Policy Template

```markdown
## Error Budget Policy — [Nome Servizio]

### Soglie di azione

| Budget rimanente | Stato | Azione richiesta |
|---|---|---|
| > 50% | VERDE | Sviluppo normale, deploy a discrezione del team |
| 25-50% | GIALLO | Rallentare feature rischiose, aumentare copertura test |
| 10-25% | ARANCIONE | Freeze feature non critiche, focus su affidabilita' |
| < 10% | ROSSO | Feature freeze totale, tutto l'effort su stabilita' |
| Esaurito | NERO | Stop deploy, incident review obbligatoria per ogni cambio |

### Burn Rate Alert

La burn rate indica quanto velocemente si sta consumando l'error budget:
- **Burn rate 1x** = budget si esaurisce esattamente alla fine della finestra
- **Burn rate 10x** = budget si esaurisce in 3 giorni (su finestra 30gg)
- **Burn rate 100x** = budget si esaurisce in ~7 ore

### Configurazione alert multi-finestra (Google SRE approach)

alerting_rules:
  # Fast burn — rileva incidenti gravi rapidamente
  - alert: ErrorBudgetFastBurn
    expr: |
      (
        1 - (rate(http_requests_total{status!~"5.."}[1h]) / rate(http_requests_total[1h]))
      ) > (14.4 * 0.001)
    for: 2m
    labels:
      severity: critical
      page: true
    annotations:
      summary: "Error budget burn rate 14.4x — esaurimento in ~2 ore"

  # Slow burn — rileva degradazione graduale
  - alert: ErrorBudgetSlowBurn
    expr: |
      (
        1 - (rate(http_requests_total{status!~"5.."}[6h]) / rate(http_requests_total[6h]))
      ) > (6 * 0.001)
    for: 30m
    labels:
      severity: warning
      page: false
    annotations:
      summary: "Error budget burn rate 6x — esaurimento in ~5 giorni"
```

### Dashboard SLO Essenziale

Ogni servizio con SLO definiti deve avere una dashboard con:

1. **Budget rimanente (%)** — barra o gauge con zone colorate
2. **Burn rate attuale** — grafico temporale con soglie di alert
3. **SLI trend** — andamento dell'indicatore nell'ultima finestra SLO
4. **Proiezione esaurimento** — stima di quando il budget si esaurira' al tasso attuale
5. **Storico violazioni** — timeline degli eventi che hanno consumato budget

```promql
# PromQL: budget rimanente (finestra 30 giorni, SLO 99.9%)
1 - (
  sum(increase(http_requests_total{status=~"5..", service="checkout"}[30d]))
  /
  sum(increase(http_requests_total{service="checkout"}[30d]))
) - 0.999

# PromQL: burn rate istantaneo (finestra 1h)
(
  sum(rate(http_requests_total{status=~"5..", service="checkout"}[1h]))
  /
  sum(rate(http_requests_total{service="checkout"}[1h]))
) / 0.001
```

---

## Esercizi

1. **CrashLoopBackOff diagnosis** — Deploya un Pod con un container che fallisce all'avvio (immagine con entrypoint errato). Usa `kubectl describe pod`, `kubectl logs --previous`, e ispeziona `exitCode` e `reason`. Identifica la causa root e correggi il manifest. Documenta la procedura in un mini-runbook.

2. **OOMKilled investigation** — Deploya un'applicazione con memory limit deliberatamente basso (es. 64Mi per un'app Java). Genera carico fino a provocare OOMKilled. Analizza con `kubectl describe pod` (Last State, Exit Code 137). Determina se il fix corretto e' alzare il limit o correggere un memory leak nell'applicazione.

3. **Network troubleshooting** — In un cluster con NetworkPolicy abilitate (Calico o Cilium), deploya due Pod in namespace diversi. Verifica che la comunicazione sia bloccata, poi crea la NetworkPolicy corretta. Usa `kubectl exec` con `nslookup`, `nc -zv` e `curl` per diagnosticare a quale livello (DNS, L4, L7) il traffico viene bloccato.

4. **Incident post-mortem** — Simula un incidente di produzione (es. deployment con configurazione errata che causa downtime). Esegui rollback, poi conduci un post-mortem blameless: timeline, root cause, impact, action items. Produci un documento seguendo il template SRE di Google.

5. **Production readiness review** — Prendi un'applicazione di esempio deployata su Kubernetes. Esegui una production readiness review completa usando la checklist di questo modulo. Identifica almeno 5 gap, prioritizzali per severita', e implementa i fix per i top 3.

6. **Chaos engineering GameDay** — Configura Litmus Chaos o Chaos Toolkit in un cluster di staging. Progetta un esperimento con steady-state hypothesis formale (definisci SLI target, tolerance, probe). Esegui pod-delete su un deployment con 3 repliche. Verifica se il servizio mantiene lo steady state durante l'esperimento. Documenta i risultati in formato experiment journal e proponi remediation per ogni debolezza scoperta.

7. **Observability pipeline end-to-end** — Deploya un OTel Collector in modalita' agent (DaemonSet) con receiver OTLP, processor batch e tail_sampling, ed exporter verso Tempo (traces) e Loki (logs). Instrumenta un'applicazione di esempio per emettere trace con span personalizzati. Verifica la correlazione trace-to-log cercando un trace_id specifico nei log su Loki. Configura un alert Prometheus basato su burn rate con finestra 1h e soglia 14.4x.

8. **Ephemeral container debugging** — Deploya un Pod con immagine distroless (es. `gcr.io/distroless/static-debian12`). Tenta di fare `kubectl exec` e documenta il fallimento. Usa `kubectl debug` con `--image=nicolaka/netshoot --target=app` per diagnosticare connettivita' di rete dal Pod. Esegui `tcpdump`, `nslookup` e `curl` dal container effimero. Documenta le differenze rispetto all'approccio exec tradizionale.

---

## Letture e Riferimenti

### Documentazione ufficiale

- Kubernetes Troubleshooting Guide. https://kubernetes.io/docs/tasks/debug/
- kubectl Cheat Sheet. https://kubernetes.io/docs/reference/kubectl/cheatsheet/
- Kubernetes Debug Running Pods. https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/
- Google SRE Workbook — Postmortem Culture. https://sre.google/workbook/postmortem-culture/
- Google SRE Book — Monitoring Distributed Systems. https://sre.google/sre-book/monitoring-distributed-systems/

### Libri

- Beyer, B. et al. *Site Reliability Engineering*. O'Reilly, 2016. Cap. 12-15 — Troubleshooting, Emergency Response, Postmortems.
- Beyer, B. et al. *The Site Reliability Workbook*. O'Reilly, 2018. Cap. 9 — Incident Response.
- Burns, B. et al. *Kubernetes Up & Running*. O'Reilly, 3rd ed., 2022. Cap. 18 — Debugging.

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione |
|---|---|---|
| [05-kubernetes](05-kubernetes.md) | Kubernetes | Concetti core (Pod, Deployment, Service) necessari per diagnosticare problemi K8s |
| [08-monitoring-observability](08-monitoring-observability.md) | Monitoring e Observability | Alert, metriche e log centralizzati sono il punto di partenza del troubleshooting |
| [07-ci-cd](07-ci-cd.md) | CI/CD | Rollback e deployment strategy influenzano la risposta agli incidenti |
| [13-sicurezza-piattaforme](13-sicurezza-piattaforme.md) | Sicurezza delle Piattaforme | NetworkPolicy e security context sono cause frequenti di failure di networking |
| [09-service-mesh](09-service-mesh.md) | Service Mesh | mTLS, retry e timeout del mesh complicano la diagnosi di problemi di connettivita' |
| [17-storage-distribuito](17-storage-distribuito.md) | Storage Distribuito | PVC pending e OSD failure richiedono troubleshooting specifico dello storage layer |

---

## Glossario

| Termine | Definizione |
|---|---|
| **CrashLoopBackOff** | Stato Kubernetes in cui un container fallisce ripetutamente e il kubelet applica backoff esponenziale tra i restart. |
| **OOMKilled** | Terminazione forzata di un container da parte del kernel Linux quando supera il memory limit (exit code 137). |
| **Exit code** | Codice numerico ritornato dal processo all'uscita: 0 = successo, 1 = errore generico, 137 = SIGKILL (OOM), 143 = SIGTERM. |
| **Pod eviction** | Rimozione forzata di un Pod da un nodo per pressione di risorse (memoria, disco, PID). |
| **Runbook** | Documento operativo con procedure step-by-step per gestire scenari noti (incidenti, maintenance, recovery). |
| **Post-mortem** | Analisi strutturata condotta dopo un incidente per identificare root cause e definire azioni preventive. |
| **Blameless culture** | Approccio SRE che si concentra sui fattori sistemici degli incidenti senza cercare colpevoli individuali. |
| **SLI (Service Level Indicator)** | Metrica quantitativa che misura un aspetto della qualita' del servizio (latenza, error rate, throughput). |
| **SLO (Service Level Objective)** | Target su un SLI che definisce il livello di affidabilita' accettabile (es. 99.9% availability). |
| **Error budget** | Quantita' di disservizio tollerato calcolata come 1 - SLO, usata per bilanciare velocita' e affidabilita'. |
| **NetworkPolicy** | Risorsa Kubernetes che definisce regole firewall L3/L4 per il traffico tra Pod. |
| **PodDisruptionBudget** | Risorsa Kubernetes che limita il numero di Pod di un workload che possono essere interrotti simultaneamente. |
| **Liveness probe** | Health check che indica se un container e' vivo; se fallisce, il kubelet lo riavvia. |
| **Readiness probe** | Health check che indica se un container e' pronto a ricevere traffico; se fallisce, viene rimosso dagli endpoint. |
| **Chaos engineering** | Disciplina che introduce guasti controllati in produzione per scoprire debolezze del sistema. |
| **Steady-state hypothesis** | Ipotesi formale che descrive il comportamento normale e misurabile del sistema, verificata prima e dopo un esperimento di chaos. |
| **Burn rate** | Velocita' con cui si consuma l'error budget; burn rate 1x = budget esaurito esattamente alla fine della finestra SLO. |
| **Ephemeral container** | Container di debug iniettato in un Pod in esecuzione tramite `kubectl debug`, senza modificare il Pod spec originale (GA da K8s 1.25). |
| **OpenTelemetry (OTel)** | Framework open source CNCF che unifica raccolta e esportazione di traces, metriche e log con API e SDK standardizzati. |
| **Tail-based sampling** | Strategia di campionamento che decide se conservare un trace dopo che tutti gli span sono completati, permettendo di catturare selettivamente errori e outlier. |
| **eBPF** | Tecnologia kernel Linux che permette di eseguire programmi sandboxed nel kernel per osservabilita', networking e sicurezza senza modificare il codice sorgente delle applicazioni. |
| **Drift detection** | Rilevamento automatico di discrepanze tra lo stato dichiarato (Git) e lo stato effettivo dell'infrastruttura, tipico di strumenti GitOps come ArgoCD e Flux. |
| **GameDay** | Evento strutturato in cui il team esegue esperimenti di chaos engineering in ambiente controllato per testare la resilienza del sistema e migliorare la risposta agli incidenti. |
| **Blast radius** | Ampiezza dell'impatto di un guasto o esperimento; nella chaos engineering, si inizia con blast radius ridotto e si scala gradualmente. |
