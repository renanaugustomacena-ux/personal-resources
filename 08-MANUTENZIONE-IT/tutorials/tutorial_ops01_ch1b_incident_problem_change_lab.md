# Tutorial: Incident, Problem e Change Management — Hands-On Lab

> **Documento di riferimento:** `01-framework-metodologie.md` (sezioni 3-5)
> **Dominio:** Framework ITIL e Metodologie
> **Ambito:** Gestione degli Incidenti, dei Problemi e dei Cambiamenti — le tre pratiche operative quotidiane più importanti di ITIL v4
> **Durata lab:** 4-5 ore
> **Livello:** Principiante-Intermedio — richiede ops00 (lab) e ops01a (ITIL Fondamenti)
> **Prerequisiti:** `tutorial_ops01_ch1a_itil_foundations_lab.md` — in particolare GLPI installato e funzionante su SRV-LINUX-01
> **Ambiente:** GLPI su SRV-LINUX-01 (http://192.168.56.20:8080/glpi), DC-LAB-01, WKS-LAB-01

---

## Lab Environment Setup

**Verifica prerequisiti:**

```powershell
# Da WKS-LAB-01: verifica che GLPI sia accessibile
Invoke-WebRequest -Uri "http://192.168.56.20:8080/glpi" -UseBasicParsing -TimeoutSec 5 |
    Select-Object StatusCode, StatusDescription
```

Output atteso: `StatusCode: 200`

**Se GLPI non risponde**, avvia il container Docker:

```bash
# SSH su SRV-LINUX-01
ssh lab-admin@192.168.56.20

cd ~/glpi-docker
docker compose up -d
sleep 10
docker compose ps
```

Poi apri il browser su WKS-LAB-01 e naviga a `http://192.168.56.20:8080/glpi`

---

## PART A: FONDAMENTI — Le Tre Pratiche Operative Fondamentali di ITIL

> IT Operations senza Incident/Problem/Change management è come una cucina di ristorante senza ricette, senza responsabile qualità e senza protocolli: ogni cuoco fa a modo suo, i piatti escono diversi ogni volta, e quando qualcosa va storto non si sa perché. Queste tre pratiche trasformano le operazioni IT da artigianali a ingegneristiche.

---

### Concetto A1: Incident Management — Spegnere gli Incendi in Modo Professionale

> **Analogia.** Una chiamata al 112 non funziona così: "C'è un incendio in via Roma, fammi sapere come va." Funziona così: "Via Roma 42, appartamento al terzo piano, fumo visibile, nessun ferito apparente, porte chiuse." Informazioni precise, classificazione immediata (incendio vs fuga gas), dispaccio della risorsa giusta (pompieri vs gas). L'Incident Management IT funziona esattamente così.

**Cos'è un Incidente?**

Un **incidente** è un'interruzione non pianificata o una riduzione della qualità di un servizio IT.

| Incidente | Non è un incidente |
|---|---|
| Il server va down | Aggiungere un utente ad Active Directory |
| La rete cade | Cambiare il wallpaper del desktop policy |
| L'email non funziona per 100 persone | Installare un nuovo software su richiesta |
| Il backup fallisce alle 03:00 | Reset password dimenticata |

La seconda colonna sono **Service Request** — richieste pianificate e previste. Un incidente è sempre inaspettato e negativo.

**Il ciclo di vita di un Incidente in 7 fasi:**

```
1. DETECTION        Il problema viene rilevato (monitoring, utente, team IT)
       ↓
2. LOGGING          Il ticket viene aperto con le informazioni base
       ↓
3. CLASSIFICATION   Categoria (Hardware/Software/Rete) + Sottocategoria
       ↓
4. PRIORITIZATION   Impatto × Urgenza → P1/P2/P3/P4/P5
       ↓
5. INVESTIGATION    Diagnosi: cosa è successo? Dati di log, KEDB, KB
       ↓
6. RESOLUTION       Fix applicato, servizio ripristinato, verificato
       ↓
7. CLOSURE          Documentato, utente confermato, KB aggiornata
```

**La matrice Impatto × Urgenza — la chiave della prioritizzazione:**

| | Urgenza Alta (nessun workaround) | Urgenza Media (workaround parziale) | Urgenza Bassa (workaround efficace) |
|---|---|---|---|
| **Impatto Alto** (servizio critico, >50 utenti) | **P1 — Critico** | **P2 — Alto** | **P3 — Medio** |
| **Impatto Medio** (funzione importante, alcuni utenti) | **P2 — Alto** | **P3 — Medio** | **P4 — Basso** |
| **Impatto Basso** (funzione non critica, utente singolo) | **P3 — Medio** | **P4 — Basso** | **P5 — Pianificato** |

**SLA per priorità — i tempi che devi rispettare:**

| Priorità | Tempo Risposta | Tempo Risoluzione | Esempio reale |
|---|---|---|---|
| P1 — Critico | 15 minuti | 1 ora | ERP giù per 200 utenti |
| P2 — Alto | 30 minuti | 4 ore | Email non funziona per un dipartimento |
| P3 — Medio | 2 ore | 8 ore lavorative | Stampante condivisa offline |
| P4 — Basso | 4 ore | 24 ore lavorative | Problema grafico su app non critica |
| P5 — Pianificato | 8 ore | 5 giorni | Ottimizzazione prestazioni |

**I livelli di escalation:**

```
L1 — Service Desk
  ↓  (se non risolto in N minuti o competenza insufficiente)
L2 — Tecnici Specializzati (server admin, network engineer, DBA)
  ↓  (se non risolto o richiede conoscenza di codice/architettura)
L3 — Architetti / Expert Engineers
  ↓  (se il problema è nel prodotto del vendor)
Vendor Support (HP, Microsoft, Oracle, Cisco...)
```

**Il Major Incident — quando si attiva il protocollo di crisi:**

Un Major Incident si dichiara quando criteri predefiniti sono soddisfatti (es. servizio critico down, > 100 utenti impattati). Il processo prevede:
1. **Dichiarazione** del Major Incident entro 5 minuti
2. **Convocazione bridge call** immediata con tutti gli specialisti
3. **Comunicazione iniziale** agli stakeholder entro 15 minuti
4. **Aggiornamenti ogni 30 minuti** fino alla risoluzione
5. **Post-Incident Review** entro 48 ore dalla risoluzione

---

### Concetto A2: Problem Management — Capire Perché e Prevenire

> **Analogia.** Un pronto soccorso cura le ferite (Incident Management). Ma se ogni lunedì mattina arrivano 10 persone con lo stesso tipo di frattura alla mano destra, qualcuno deve investigare il perché — forse il tornio di una fabbrica vicina ha un difetto di sicurezza. Quell'investigazione è il Problem Management.

**La differenza fondamentale:**

| | Incident Management | Problem Management |
|---|---|---|
| **Focus** | Ripristinare il servizio (FAST) | Trovare la causa radice |
| **Tempo** | Minuti o ore | Giorni o settimane |
| **Domanda chiave** | "Come lo faccio ripartire?" | "Perché si è rotto?" |
| **Output** | Servizio ripristinato | Fix permanente o workaround documentato |
| **Metafora** | Pompiere | Investigatore |

**Gestione Reattiva vs Proattiva:**

- **Reattiva**: si attiva DOPO gli incidenti → "Questo è il terzo crash del database in 30 giorni — apriamo un Problem ticket"
- **Proattiva**: si attiva PRIMA → "Il trend di utilizzo disco mostra che arriveremo al 95% tra 3 settimane — apriamo un Problem ticket ora"

**Le 3 tecniche di Root Cause Analysis:**

**1. I 5 Perché (5 Whys) — la tecnica più semplice:**

```
Problema: Il server database si è bloccato.
Perché 1? Il disco era pieno al 100%.
Perché 2? Le tabelle temporanee sono cresciute in modo incontrollato.
Perché 3? Una procedura batch non cancella le temp tables dopo l'uso.
Perché 4? Il codice della procedura non include uno step di cleanup.
Perché 5? La code review checklist non include la gestione delle risorse temporanee.
→ CAUSA RADICE: mancanza di standard di coding per le risorse temporanee.
→ FIX: aggiornare la code review checklist + job automatico di cleanup.
```

**2. Diagramma di Ishikawa (a lisca di pesce):**

Utile quando le cause possono essere molteplici e non sequenziali:

```
                    PROBLEMA (il pesce)
                          |
        Persone ──────────┤──────────── Tecnologia
        (errore umano,    |             (bug, guasto HW,
         formazione)      |              capacità)
                          |
        Processi ─────────┤──────────── Ambiente
        (procedure        |             (temperatura, UPS,
         mancanti)        |              connettività)
                          |
        Dati ─────────────┤──────────── Fornitori
        (corruzione,      |             (componente difettoso,
         migrazione)      |              supporto inadeguato)
```

**3. Metodo Kepner-Tregoe:**

Strutturato per problemi complessi con molte variabili:
1. **Descrivi il problema**: cosa è? cosa NON è? dove è? dove NON è? quando? con che frequenza?
2. **Identifica le differenze**: cosa è cambiato rispetto a quando funzionava?
3. **Formula ipotesi** basate sulle differenze trovate
4. **Verifica** ogni ipotesi con dati concreti

**Il Known Error Database (KEDB):**

Quando la causa radice è trovata ma la fix permanente non è ancora pronta, si documenta un **Known Error**: causa nota, workaround documentato, stato della fix.

```
Known Error KE-2026-00045:
Causa: procedure batch ERP non puliscono le temp tables
Workaround: eseguire /opt/scripts/cleanup_temp_tables.sh via cron giornaliero
Fix permanente: Change Request CHG-2026-00178 (in pianificazione)
Incidenti collegati: INC-00142, INC-00098, INC-00067
```

---

### Concetto A3: Change Management — Modificare senza Rompere

> **Analogia.** Un chirurgo non apre il torace del paziente e "vede come va". Prima studia la risonanza (analisi), pianifica l'intervento (RFC), si assicura che il team anestesiologico e infermieristico sia pronto (CAB), ha un piano se qualcosa va storto (rollback plan), e documenta tutto dopo (post-change review). Change Management è la stessa cosa applicata all'IT.

**Cos'è un Cambiamento?**

Qualsiasi aggiunta, modifica o rimozione di qualunque elemento che possa avere effetti sui servizi IT.

**I 3 tipi di Change:**

```
STANDARD CHANGE
├── Pre-autorizzato, basso rischio, procedura documentata
├── NON richiede CAB per ogni istanza
└── Esempi: reset password, aggiunta RAM, creazione mailbox

NORMAL CHANGE  
├── Richiede valutazione, approvazione CAB, pianificazione
├── Il tipo più comune per aggiornamenti significativi
└── Esempi: upgrade firmware switch, migrazione database

EMERGENCY CHANGE
├── Deve essere implementato SUBITO (incidente critico in corso)
├── Approvazione Emergency CAB (eCAB) accelerata
├── ⚠ Deve essere l'eccezione — frequenza alta = processo rotto
└── Esempi: patch zero-day in produzione, fix corruzione dati
```

**Il processo di un Normal Change:**

```
1. RFC (Request For Change) → submit in GLPI con:
   - Descrizione del change e motivazione
   - Sistemi e servizi impattati
   - Piano di implementazione step-by-step
   - Piano di rollback (cosa fare se va male)
   - Stima tempo (implementazione + rollback)
   - Finestra di manutenzione proposta

2. Revisione tecnica → il change manager verifica completezza RFC

3. Valutazione rischio → score 1-10 da matrice (complessità, impatto fallimento, experience, rollback)

4. CAB Meeting → approvazione da Change Advisory Board

5. Pianificazione → inserimento nel change calendar, notifica utenti

6. Implementazione → durante la finestra di manutenzione

7. Post-Change Review → il change ha avuto successo? Servizi OK?

8. Closure → documentazione finale, lezioni apprese
```

**La matrice di rischio del change:**

| Fattore | Peso | Punteggio 1-3 |
|---|---|---|
| Complessità tecnica | 25% | 1=semplice, 2=media, 3=complessa |
| Impatto se fallisce | 30% | 1=basso, 2=medio, 3=critico |
| Esperienza precedente | 15% | 3=nuovo, 2=parziale, 1=già fatto |
| Finestra manutenzione | 10% | 1=ampia, 2=normale, 3=ristretta |
| Piano di rollback | 20% | 1=testato, 2=documentato, 3=assente |

Score complessivo:
- 1-3: Basso rischio → approvazione del change manager
- 4-6: Medio → approvazione CAB
- 7-9: Alto → CAB + senior management
- 10: Critico → board/CIO

---

### Concetto A4: Il Flusso Integrato — Incident → Problem → Change

> **Analogia.** È come una catena di sicurezza in fabbrica: l'operaio si taglia il dito (Incident → primo soccorso immediato). Si scopre che è il quinto incidente al tornio questa settimana (Problem → indagine causa: il tornio non ha la protezione obbligatoria). Si installa la protezione (Change → modifica pianificata con piano di rollback). Il flusso integrato trasforma un'emergenza in prevenzione strutturata.

**Il flusso completo in un esempio reale:**

```
LUNEDÌ 09:15
  Zabbix alert: "PostgreSQL connection refused" → Aperto INC-2026-00142 P1
  
  L2 DBA interviene → Root cause immediata: disco 100% (temp tables)
  Disco ripulito, PostgreSQL riavviato → Servizio ripristinato alle 09:52
  MTTR: 37 minuti
  
  Ticket INC chiuso, aperto PRB-2026-00089
  
MARTEDÌ-VENERDÌ
  Problem Management analizza: PRB-2026-00089
  5 Whys applicato → causa radice: code review checklist incompleta
  Workaround documentato nel KEDB (cron cleanup notturno)
  
  RFC aperta: CHG-2026-00178
  "Aggiornamento procedure batch ERP per gestione automatica temp tables"
  Rischio valutato: medio (4.5/10) → necessita approvazione CAB
  
SABATO SUCCESSIVO
  CAB approva il change
  Finestra manutenzione: sabato 22:00-02:00
  Change implementato, testato, verificato
  
  INC originale: 0 ricorrenze nelle settimane successive ✓
```

**Perché il flusso integrato è fondamentale:**

Senza Problem Management, risolvi lo stesso incidente infinite volte.
Senza Change Management, la "fix" che applichi causa un nuovo incidente.
Con tutti e tre: incidenti → si riducono nel tempo, ogni cambio è sicuro.

---

### Concetto A5: KPI delle Tre Pratiche — Misurare la Maturità

**KPI Incident Management:**

| KPI | Formula | Target Tipico |
|---|---|---|
| MTTR (Mean Time To Resolve) | Somma durate incidenti / numero incidenti | Varia per priorità |
| MTTA (Mean Time To Acknowledge) | Tempo segnalazione → presa in carico | < 15 min (P1) |
| First Call Resolution (FCR) | Incidenti risolti al primo contatto / totale | > 65% |
| SLA Compliance | Incidenti risolti in SLA / totale | > 95% |
| Reopen Rate | Incidenti riaperti dopo chiusura / totale | < 5% |

**KPI Problem Management:**

| KPI | Formula | Target |
|---|---|---|
| Riduzione incidenti ricorrenti | % riduzione mese/mese | -30% annuo |
| KEDB attivi | Numero di Known Error aperti | Trend decrescente |
| Tempo identificazione causa radice | Dall'apertura PRB alla RCA | < 5 gg lavorativi |

**KPI Change Management:**

| KPI | Formula | Target |
|---|---|---|
| Change Success Rate | Change senza rollback / totali | > 95% |
| Emergency Change Rate | Emergency change / change totali | < 5% |
| Change Lead Time | Dal RFC alla chiusura | < 10 gg per normal |
| Change-Induced Incidents | Incidenti causati da change / change totali | < 5% |

---

## PART B: OPERAZIONI — Gestire Incident, Problem e Change in GLPI

> Tutti gli esercizi usano GLPI su `http://192.168.56.20:8080/glpi` (utente: glpi / password: glpi)

---

### Esercizio B1: Classificare e Prioritizzare Scenari Reali

**Obiettivo.** Prima di aprire qualsiasi ticket, devi saper classificare correttamente cosa stai guardando. Questo esercizio sviluppa il "riflesso ITSM" — la capacità di leggere una situazione e istantaneamente sapere cosa fare.

**Leggi ogni scenario e rispondi:**
1. È un Incident, Service Request, Problem o Change?
2. Se è un Incident: che priorità (P1-P5)?
3. Quale sarebbe il primo step da fare?

---

**Scenario 1:** Alle 08:45 un utente chiama il Service Desk dicendo "non riesco ad aprire Outlook, mi dà errore 0x8004011D".

<details>
<summary>→ Risposta</summary>

- **Tipo**: Incident (interruzione non pianificata per l'utente)
- **Impatto**: Basso (utente singolo)
- **Urgenza**: Media (ha workaround: può usare webmail)
- **Priorità**: P4
- **Primo step**: Registrare il ticket, chiedere da quando avviene e cosa è cambiato di recente (nuovo aggiornamento? cambio password?)

</details>

---

**Scenario 2:** Il tuo sistema di monitoring (Zabbix) mostra che DC-LAB-01 ha il disco C: al 98% di utilizzo.

<details>
<summary>→ Risposta</summary>

- **Tipo**: Incident (P2 Alto) — il Domain Controller è un sistema critico. Il disco pieno impedirebbe i login di tutti gli utenti del dominio.
- **Impatto**: Alto (tutti gli utenti del dominio saranno impattati quando arriva al 100%)
- **Urgenza**: Alta (poche ore prima del collasso totale)
- **Priorità**: P2
- **Primo step**: Escalation immediata a L2, liberare spazio (log vecchi, Windows.old, WinSxS), poi aprire Problem ticket per capire perché è cresciuto

</details>

---

**Scenario 3:** Mario Rossi chiede di creare una nuova mailbox per la nuova dipendente Anna Ferrari che inizia lunedì.

<details>
<summary>→ Risposta</summary>

- **Tipo**: Service Request (richiesta pianificata, standard)
- **NON è un incidente** — è attività ordinaria prevista
- **Priorità SR**: Normal (da completare entro il giorno dell'inizio)
- **Primo step**: Verificare nel catalogo servizi se c'è uno Standard Change già approvato per la creazione mailbox (in molte organizzazioni sì)

</details>

---

**Scenario 4:** Negli ultimi 30 giorni si sono verificati 5 incidenti identici: il servizio GLPI su SRV-LINUX-01 si riavvia ogni volta che il container Docker va sotto pressione di memoria. Ogni volta L2 risolve in 20 minuti ma il problema ritorna.

<details>
<summary>→ Risposta</summary>

- **Tipo**: Problem (causa ricorrente di incidenti multipli)
- **NON è un nuovo Incident** da gestire — è un Pattern da investigare
- **Priorità PRB**: Medio (ogni incidente è P3, ma la ricorrenza li eleva)
- **Primo step**: Aprire ticket Problem in GLPI, analizzare i log dei 5 incidenti, applicare 5 Whys, identificare la causa radice (probabile: limit di memoria del container GLPI non configurato)

</details>

---

**Scenario 5:** Il team di sviluppo vuole aggiornare PHP da 7.4 a 8.2 su SRV-LINUX-01 perché la versione attuale va EOL (End of Life) e non riceverà più patch di sicurezza.

<details>
<summary>→ Risposta</summary>

- **Tipo**: Change — Normal Change (aggiornamento significativo di componente infrastrutturale)
- **Rischio**: Medio-Alto (l'upgrade PHP può rompere applicazioni che dipendono da API deprecate)
- **Primo step**: Aprire RFC in GLPI con: analisi delle applicazioni impattate (GLPI, eventuali web app), piano di test in ambiente staging, piano di rollback (downgrade a 7.4 o snapshot pre-change), finestra di manutenzione proposta

</details>

---

**Scenario 6:** Alle 23:47 il sistema di monitoring rileva che il sito web aziendale esposto a Internet è irraggiungibile. Analisi rapida: il certificato SSL è scaduto ieri notte alle 00:00.

<details>
<summary>→ Risposta</summary>

- **Tipo**: Incident P2 + Emergency Change
- **L'Incident** è che il sito è giù → P2 (servizio critico per il business, impatto su tutti i visitatori)
- **L'Emergency Change** è il rinnovo del certificato SSL → richiede approvazione eCAB (email/Slack con il change manager e il security team)
- **Causa**: il monitoraggio della scadenza certificati era assente → aprire anche Problem ticket
- **Sequenza**: (1) Incident P2, (2) Emergency Change per rinnovo SSL, (3) Problem per capire perché non era monitorata la scadenza

</details>

**Checkpoint B1:**
- [ ] Sai distinguere Incident da Service Request da Problem da Change
- [ ] Sai calcolare la priorità P1-P5 a partire da Impatto e Urgenza
- [ ] Hai capito che uno stesso evento può generare sia un Incident che un Problem e/o un Change

---

### Esercizio B2: Gestire un Incident P2 in GLPI — Simulazione Completa

**Obiettivo.** Simulare il ciclo di vita completo di un Incident P2 in GLPI, dalla registrazione alla chiusura.

**Scenario da simulare:** Alle 14:30 su DC-LAB-01 il servizio DNS smette di rispondere. WKS-LAB-01 non riesce più a risolvere nomi di dominio. L'accesso a Internet e alle risorse di rete condivise è interrotto.

**Step 1 — Simula l'incidente su DC-LAB-01:**

```powershell
# Su DC-LAB-01: ferma temporaneamente il servizio DNS (1 minuto)
Stop-Service DNS
Start-Sleep -Seconds 5

# Su WKS-LAB-01: verifica che DNS non funzioni
nslookup google.com 192.168.56.10
# Output atteso: errore di timeout o "can't find server name"
```

**Step 2 — Apri il ticket Incident in GLPI:**

1. Apri `http://192.168.56.20:8080/glpi` su WKS-LAB-01
2. Helpdesk → Create a ticket
3. Compila:

```
Tipo:           Incident
Titolo:         [P2] Servizio DNS non disponibile su DC-LAB-01
Categoria:      Network > DNS
Urgenza:        4 (High)
Impatto:        4 (High)
Priorità:       GLPI calcola: 5 (Very High) → Aggiusta a P2
Descrizione:    
  SINTOMO: Il servizio DNS su DC-LAB-01 (192.168.56.10) non risponde.
  RILEVAMENTO: 14:30 - controllo manuale / nslookup timeout
  IMPATTI: WKS-LAB-01 non riesce a risolvere nomi di dominio.
           Accesso Internet e risorse condivise interrotte.
  UTENTI IMPATTATI: Tutti gli utenti che dipendono da questo DNS
  WORKAROUND: Configurare temporaneamente 8.8.8.8 come DNS alternativo
              (riduce impatto ma non risolve il problema AD)
  
Assegnato a:    IT Team (gruppo)
SLA:            P2 → risoluzione entro 4 ore
```

**Step 3 — Traccia le attività di investigazione:**

Aggiungi Follow-up al ticket mentre lavori:

```
Follow-up 1 [14:32]:
  Verificato: servizio DNS su DC-LAB-01 in stato "Stopped"
  Comando: Get-Service DNS → Status = Stopped
  Il servizio era precedentemente in stato Running.
  Causa immediata: servizio stoppato manualmente o crash.
  
Follow-up 2 [14:35]:
  Riavvio servizio DNS in corso.
  Comando: Start-Service DNS
  Verifica: Get-Service DNS → Status = Running
  
Follow-up 3 [14:36]:
  Verifica risoluzione nomi: nslookup google.com 192.168.56.10 → OK
  Verifica AD: dcdiag /test:DNS → PASSED
  Servizio ripristinato. MTTR: 6 minuti.
```

**Step 4 — Risolvi il ticket:**

```powershell
# Riavvia DNS su DC-LAB-01 (torna alla normalità)
Start-Service DNS
Get-Service DNS

# Verifica da WKS-LAB-01
nslookup lab.local 192.168.56.10
nslookup dc-lab-01.lab.local 192.168.56.10
```

In GLPI:
- Stato → **Solved**
- Soluzione: "Riavviato servizio DNS su DC-LAB-01. Causa immediata: servizio in stato Stopped. Aperto Problem ticket PRB per investigare causa del crash."
- Clicca **Save**

**Checkpoint B2:**
- [ ] Ticket Incident aperto con Categoria, Priorità, Descrizione strutturata
- [ ] Almeno 3 Follow-up con attività di investigazione tracciati
- [ ] DNS ripristinato, verificato con `nslookup`
- [ ] Ticket chiuso in stato "Solved" con soluzione documentata
- [ ] Sai calcolare il MTTR dell'incidente (minuti dall'apertura alla risoluzione)

---

### Esercizio B3: Aprire e Gestire un Problem Ticket — Root Cause Analysis

**Obiettivo.** Partendo dall'Incident B2, aprire un Problem ticket, applicare i 5 Perché, documentare nel KEDB.

**Scenario:** Il DNS si è fermato per la terza volta questa settimana. È ora di investire tempo nella causa radice.

**Step 1 — Apri il Problem ticket in GLPI:**

1. Vai al ticket dell'Incident B2
2. Nella sezione in fondo: **Problems → Associate a problem**
3. Oppure: Helpdesk → Problems → Add

```
Tipo:           Problem
Titolo:         [PRB] Servizio DNS su DC-LAB-01 va in crash periodicamente
Stato:          In Progress
Urgenza:        3 (Medium)
Impatto:        4 (High)
Descrizione:    Il servizio DNS su DC-LAB-01 si è fermato 3 volte
                questa settimana (15/07, 14/07, 13/07).
                Ogni volta viene risolto con riavvio manuale in < 10 min
                ma la causa radice non è ancora identificata.
Incidenti collegati: INC-B2, [altri incidenti precedenti]
```

**Step 2 — Applica i 5 Perché:**

Esegui l'analisi e documentala come Follow-up nel ticket Problem:

```bash
# Su DC-LAB-01: raccoglie dati per la RCA
# 1. Ultimo riavvio del servizio DNS
Get-EventLog -LogName System -Source "*DNS*" -Newest 20

# 2. Event Log per crash del servizio
Get-WinEvent -FilterHashtable @{LogName='System'; Id=7034; StartTime=(Get-Date).AddDays(-7)} |
    Where-Object {$_.Message -like "*DNS*"} |
    Select-Object TimeCreated, Message

# 3. Memoria disponibile al momento dei crash
Get-WinEvent -FilterHashtable @{LogName='System'; Id=2004; StartTime=(Get-Date).AddDays(-7)} |
    Select-Object TimeCreated, Message -First 10

# 4. Verifica configurazione recovery del servizio DNS
sc.exe qfailure DNS
```

**Documenta l'analisi 5 Whys nel Follow-up:**

```
RCA — 5 Whys per PRB: DNS crash

Il servizio DNS su DC-LAB-01 si ferma periodicamente.

PERCHÉ 1? Il processo dns.exe si chiude con exit code non-zero
  → Event ID 7034: "The DNS Server service terminated unexpectedly"

PERCHÉ 2? La RAM disponibile scende sotto 100 MB prima del crash
  → Event 2004 (memory warning) trovati ~30 minuti prima di ogni crash

PERCHÉ 3? Un processo non identificato occupa progressivamente tutta la RAM
  → Performance Monitor mostra crescita costante di "Private Bytes" di un processo

PERCHÉ 4? Il processo è svchost.exe (Windows Update) che scarica updates durante orario lavorativo
  → Scheduled task "Windows Update" configurato per "Any time"

PERCHÉ 5? La policy di manutenzione del DC non specifica un orario per Windows Update
  → Manca una Group Policy per il controllo degli orari di aggiornamento

CAUSA RADICE: Windows Update compete con i servizi critici per la RAM
durante l'orario lavorativo, portando DNS a crashare per OOM.

WORKAROUND: Configurare task di Windows Update su DC-LAB-01 per
le sole ore 03:00-05:00.

FIX PERMANENTE: Group Policy per WSUS con orari di download/install
notturni per tutti i Domain Controller. → aprire RFC in Change Management.
```

**Step 3 — Documenta il Known Error:**

Nel Problem ticket, aggiungi:

```
STATO KNOWN ERROR:
Causa Radice: IDENTIFICATA
Workaround: Sì — configurare Windows Update per ore notturne (03:00-05:00)
Fix permanente: No — in pianificazione tramite RFC
Change Request: CHG da aprire (esercizio B4)
```

**Checkpoint B3:**
- [ ] Problem ticket aperto in GLPI e collegato all'Incident
- [ ] 5 Whys completato e documentato nel Follow-up
- [ ] Causa radice identificata: Windows Update consuma RAM durante orario lavorativo
- [ ] Workaround documentato (configurazione orari Update)
- [ ] Stato Known Error compilato nel ticket Problem

---

### Esercizio B4: Change Management — Aprire un RFC e Simulare il CAB

**Obiettivo.** Aprire una Request For Change (RFC) in GLPI per risolvere definitivamente il problema del DNS, valutare il rischio, e simulare l'approvazione CAB.

**Step 1 — Apri la RFC in GLPI:**

1. Helpdesk → Changes → Add
2. Compila:

```
Tipo:           Normal Change
Titolo:         [CHG] Configurare WSUS/Windows Update orari notturni su DC-LAB-01
Categoria:      Infrastructure > Patch Management
Stato:          New

DESCRIZIONE E MOTIVAZIONE:
Tre incidenti DNS (INC-B2 e precedenti) causati da Windows Update
che compete con DNS per risorse RAM durante l'orario lavorativo.
Causa identificata nel Problem PRB: DNS crash.
Questa RFC implementa la fix permanente tramite Group Policy WSUS.

SISTEMI IMPATTATI:
- DC-LAB-01 (principal)
- Tutti i client del dominio lab.local (indirettamente, effetto positivo)

STIMA RISCHIO: Medio
- Complessità tecnica: Bassa (GPO WSUS è standard)
- Impatto se fallisce: Medio (DC funziona ma Update potrebbe non applicarsi)
- Esperienza: Media (configurato in passato)
- Finestra di manutenzione: Ampia (solo GPO — nessun riavvio necessario)
- Rollback: Disabilitare la GPO (1 minuto) → rischio Basso

PIANO DI IMPLEMENTAZIONE:
Step 1: Creare GPO "DC-Update-Policy" in Group Policy Management Console
Step 2: Configurare: Computer Config → Admin Templates → Windows Components
        → Windows Update → Configure Automatic Updates
        → Download e installa: Ogni giorno alle 03:00
Step 3: Collegare GPO all'OU "Domain Controllers"
Step 4: Verificare che la policy sia applicata: gpupdate /force su DC-LAB-01
Step 5: Monitoraggio per 1 settimana — nessun nuovo crash DNS atteso

PIANO DI ROLLBACK:
Se la GPO causa problemi: Get-GPO "DC-Update-Policy" | Remove-GPLink -Target ...
Tempo rollback: < 5 minuti

FINESTRA DI MANUTENZIONE PROPOSTA:
Giovedì sera 16/07/2026 21:00 — nessun riavvio richiesto

PROBLEM COLLEGATO: PRB (ops01b B3)
```

**Step 2 — Simula il CAB Meeting:**

Per questo esercizio, fai il ruolo di Change Manager e valuta la RFC:

```
VALUTAZIONE RISCHIO — CHG: WSUS notturno DC-LAB-01

| Fattore               | Peso | Score | Punteggio |
|-----------------------|------|-------|-----------|
| Complessità tecnica   |  25% |   1   |   0.25    |
| Impatto se fallisce   |  30% |   2   |   0.60    |
| Esperienza precedente |  15% |   1   |   0.15    |
| Finestra manutenzione |  10% |   1   |   0.10    |
| Piano di rollback     |  20% |   1   |   0.20    |
|                       |      | TOTALE|   1.30    |

Score finale: 1.30 / 3.0 = 43% → RISCHIO BASSO

DECISIONE CAB: APPROVATO
Approvato da: [Change Manager simulato]
Data: 2026-07-16
Finestra: 2026-07-17 21:00-22:00
```

Aggiorna il ticket in GLPI: Stato → **Approved**

**Step 3 — Implementa il Change:**

```powershell
# Su DC-LAB-01: implementa il change
# (Tramite Group Policy oppure direttamente nel Registry per il lab)

# Opzione lab rapida: configura il registro di Windows Update
# (equivale a quello che farebbe la GPO)
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" `
    /v AUOptions /t REG_DWORD /d 4 /f      # Auto download e install schedulata

reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" `
    /v ScheduledInstallDay /t REG_DWORD /d 0 /f   # Ogni giorno

reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" `
    /v ScheduledInstallTime /t REG_DWORD /d 3 /f  # Alle 03:00

# Verifica la configurazione
reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"

# Verifica DNS ancora funzionante dopo il change
Resolve-DnsName lab.local -Server 192.168.56.10
```

**Step 4 — Chiudi il Change in GLPI:**

```
Soluzione:  GPO/Registry configurato per Windows Update alle 03:00 su DC-LAB-01.
            Servizio DNS verificato funzionante post-change.
            Monitoraggio attivo per 7 giorni.

Post-Change Review: Change completato senza problemi.
Verifiche: DNS OK, AD replica OK, logon utenti OK.
Lezioni apprese: Aggiungere monitoraggio RAM su DC con alert a 500MB.

Stato: CLOSED (Success)
```

**Checkpoint B4:**
- [ ] RFC aperta in GLPI con motivazione, piano implementazione e rollback
- [ ] Matrice rischio compilata, rischio classificato come Basso
- [ ] Change approvato (stato → Approved)
- [ ] Change implementato: orari Windows Update configurati
- [ ] Post-Change Review documentata, change chiuso come "Success"
- [ ] Problem PRB collegato alla RFC è ora in stato "Resolved" (fix permanente applicata)

---

### Esercizio B5: Dashboard KPI in GLPI — Misurare la Maturità ITSM

**Obiettivo.** Impostare i KPI delle pratiche Incident/Problem/Change in GLPI e creare una vista mensile.

```bash
# Su SRV-LINUX-01: accedi al container GLPI per interrogare il DB
docker exec -it glpi-db mariadb -u glpiuser -pGlpiDbPass123! glpidb << 'SQL'

-- KPI Incident: conteggio per priorità (ultimo mese)
SELECT 
    priority,
    COUNT(*) as totale,
    AVG(TIMESTAMPDIFF(MINUTE, date_creation, solvedate)) as MTTR_minuti
FROM glpi_tickets
WHERE type = 1  -- 1 = Incident
  AND date_creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY priority
ORDER BY priority;

-- KPI Change: success rate
SELECT
    COUNT(*) as totale_change,
    SUM(CASE WHEN status = 5 THEN 1 ELSE 0 END) as successi,
    ROUND(SUM(CASE WHEN status = 5 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as success_rate_pct
FROM glpi_tickets
WHERE type = 3  -- 3 = Change
  AND date_creation >= DATE_SUB(NOW(), INTERVAL 30 DAY);

-- KPI Problem: problemi aperti
SELECT
    status,
    COUNT(*) as totale
FROM glpi_tickets
WHERE type = 2  -- 2 = Problem
GROUP BY status;

SQL
```

In GLPI, vai a **Dashboard** → Aggiungi un widget:

1. Widget "Tickets by Type and Status" — mostra la distribuzione Incident/Problem/Change
2. Widget "Average Resolution Time" — mostra il trend MTTR
3. Widget "SLA Compliance" — mostra la percentuale di rispetto degli SLA

**Checkpoint B5:**
- [ ] Query SQL eseguita con successo sul database GLPI
- [ ] Dashboard con almeno 2 widget configurata
- [ ] Sai leggere i KPI e interpretarli (MTTR alto = cosa significa?)

---

## PART C: SISTEMATIZZARE — Governance delle Tre Pratiche ITSM

---

### Progetto C1: SOP Incident Management

```markdown
# SOP-INC-001: Processo di Gestione degli Incidenti

**Versione:** 1.0 | **Data:** 2026-07-15 | **Owner:** Service Desk Manager

---

## 1. Obiettivo
Garantire che tutti gli incidenti siano registrati, classificati, risolti e chiusi in modo coerente, minimizzando l'impatto sul business e rispettando gli SLA.

## 2. Scope
Applicabile a tutti gli incidenti IT segnalati a qualsiasi canale (portale, email, telefono, monitoring).

## 3. Definizioni
- **Incidente**: interruzione non pianificata o degradazione di un servizio IT
- **Service Request**: richiesta pianificata di un servizio standard
- **Major Incident**: incidente con impatto massimo sul business (criteri: vedi §7)
- **Workaround**: soluzione temporanea che riduce l'impatto senza risolvere la causa

## 4. Canali di Segnalazione
| Canale | Priorità default | Ore operative |
|--------|-----------------|---------------|
| Telefono Help Desk | P3 (poi riclassificato) | 08:00-18:00 |
| Portale GLPI | P4 | 24/7 |
| Email support | P4 | 08:00-18:00 |
| Monitoring (Zabbix) | Auto | 24/7 |

## 5. Classificazione e Prioritizzazione
Matrice Impatto × Urgenza → P1/P2/P3/P4/P5 (vedi tabella in A1)

## 6. Tempi SLA
| Priorità | Risposta | Risoluzione |
|---------|---------|------------|
| P1 | 15 min | 1 ora |
| P2 | 30 min | 4 ore |
| P3 | 2 ore | 8 ore lav. |
| P4 | 4 ore | 24 ore lav. |
| P5 | 8 ore | 5 giorni |

## 7. Criteri Major Incident (P1)
Un Major Incident viene dichiarato se:
- Servizio critico completamente non disponibile (ERP, email, rete WAN)
- > 50 utenti impattati simultaneamente
- Impatto finanziario > €10.000/ora stimato
- Dichiarato dal Service Desk Manager o dal Manager on-call

## 8. Escalation
L1 (15 min senza progresso P1/P2) → L2 (60 min) → L3 (120 min) → Vendor

## 9. Criteri di Chiusura
- Servizio verificato funzionante
- Utente ha confermato la risoluzione (o silenzio assenso dopo 24h)
- Documentazione completa nel ticket
- Knowledge Base aggiornata se applicabile
```

---

### Progetto C2: Template RFC Standard e Runbook

**Template RFC per Normal Change:**

```markdown
# RFC — Request For Change

**ID:** CHG-YYYY-XXXXX
**Data Richiesta:** 
**Richiedente:**
**Change Manager:**

---

## 1. Sommario Esecutivo
[2-3 righe: cosa cambia, perché, beneficio atteso]

## 2. Dettaglio del Change
**Sistemi coinvolti:**
**Finestra proposta:**
**Impatto previsto durante implementazione:**

## 3. Motivazione e Business Case
[Collegamento a Problem ticket / Incident ricorrente / Requisito sicurezza]

## 4. Piano di Implementazione
| Step | Azione | Responsabile | Durata stim. |
|------|--------|-------------|--------------|
| 1 | | | |
| 2 | | | |

## 5. Piano di Rollback
**Trigger per rollback:** [condizioni che richiedono rollback]
**Procedura rollback:**
| Step | Azione | Responsabile | Durata stim. |
|------|--------|-------------|--------------|
| 1 | | | |

**Tempo massimo rollback:** _____ minuti

## 6. Test e Verifica Post-Change
- [ ] [Test 1]
- [ ] [Test 2]
- [ ] Servizi critici verificati funzionanti

## 7. Comunicazione
**Utenti da notificare:**
**Testo notifica:**

## 8. Valutazione Rischio
| Fattore | Peso | Score | Pond. |
|---------|------|-------|-------|
| Complessità | 25% | | |
| Impatto fallimento | 30% | | |
| Esperienza | 15% | | |
| Finestra maint. | 10% | | |
| Rollback | 20% | | |
| **TOTALE** | | | |

**Rischio:** [ ] Basso [ ] Medio [ ] Alto

## 9. Autorizzazioni
- Change Manager: _________ Data: _____
- CAB Approval: _________ Data: _____
```

---

### Progetto C3: Script Python — KPI Mensile ITSM

```python
#!/usr/bin/env python3
"""kpi_itsm_monthly.py — Calcola e visualizza KPI mensili ITSM.
In produzione questi dati vengono dalla API GLPI.
"""

# Dataset di esempio per luglio 2026
incidents = [
    {"id": "INC-001", "priority": 1, "open_min": "2026-07-01 09:15", "resolve_min": 37, "sla_min": 60,   "reopened": False},
    {"id": "INC-002", "priority": 2, "open_min": "2026-07-03 14:30", "resolve_min": 95, "sla_min": 240,  "reopened": False},
    {"id": "INC-003", "priority": 3, "open_min": "2026-07-05 10:00", "resolve_min": 280,"sla_min": 480,  "reopened": True},
    {"id": "INC-004", "priority": 2, "open_min": "2026-07-08 11:45", "resolve_min": 210,"sla_min": 240,  "reopened": False},
    {"id": "INC-005", "priority": 4, "open_min": "2026-07-10 16:00", "resolve_min": 720,"sla_min": 1440, "reopened": False},
    {"id": "INC-006", "priority": 3, "open_min": "2026-07-12 09:30", "resolve_min": 180,"sla_min": 480,  "reopened": False},
    {"id": "INC-007", "priority": 1, "open_min": "2026-07-15 08:00", "resolve_min": 45, "sla_min": 60,   "reopened": False},
]

problems = [
    {"id": "PRB-001", "state": "resolved", "rca_days": 3},
    {"id": "PRB-002", "state": "in_progress", "rca_days": None},
]

changes = [
    {"id": "CHG-001", "type": "normal", "result": "success", "emergency": False},
    {"id": "CHG-002", "type": "normal", "result": "success", "emergency": False},
    {"id": "CHG-003", "type": "emergency", "result": "success", "emergency": True},
]

print("=" * 60)
print("  KPI ITSM — Luglio 2026")
print("=" * 60)

# --- Incident KPIs ---
print("\n[INCIDENT MANAGEMENT]")

total_inc = len(incidents)
mttr_vals = [i["resolve_min"] for i in incidents]
avg_mttr = sum(mttr_vals) / len(mttr_vals)

sla_ok = sum(1 for i in incidents if i["resolve_min"] <= i["sla_min"])
sla_pct = sla_ok / total_inc * 100

reopened = sum(1 for i in incidents if i["reopened"])
reopen_rate = reopened / total_inc * 100

p1_mttr = [i["resolve_min"] for i in incidents if i["priority"] == 1]
avg_p1_mttr = sum(p1_mttr) / len(p1_mttr) if p1_mttr else 0

print(f"  Incidenti totali: {total_inc}")
print(f"  MTTR medio: {avg_mttr:.0f} min")
print(f"  MTTR P1 medio: {avg_p1_mttr:.0f} min (target: ≤60 min) → {'OK' if avg_p1_mttr <= 60 else 'WARN'}")
print(f"  SLA Compliance: {sla_pct:.1f}% (target: ≥95%) → {'OK ' if sla_pct >= 95 else 'WARN'}")
print(f"  Reopen Rate: {reopen_rate:.1f}% (target: ≤5%) → {'OK ' if reopen_rate <= 5 else 'WARN'}")

# Per priorità
print("  Distribuzione per priorità:")
for p in sorted(set(i["priority"] for i in incidents)):
    count = sum(1 for i in incidents if i["priority"] == p)
    print(f"    P{p}: {count} incidenti")

# --- Problem KPIs ---
print("\n[PROBLEM MANAGEMENT]")
total_prb = len(problems)
resolved_prb = sum(1 for p in problems if p["state"] == "resolved")
open_prb = total_prb - resolved_prb
rca_days = [p["rca_days"] for p in problems if p["rca_days"] is not None]
avg_rca = sum(rca_days) / len(rca_days) if rca_days else 0

print(f"  Problemi aperti: {open_prb}")
print(f"  Problemi risolti: {resolved_prb}")
print(f"  Tempo medio RCA: {avg_rca:.1f} gg (target: ≤5 gg) → {'OK ' if avg_rca <= 5 else 'WARN'}")

# --- Change KPIs ---
print("\n[CHANGE MANAGEMENT]")
total_chg = len(changes)
success_chg = sum(1 for c in changes if c["result"] == "success")
emergency_chg = sum(1 for c in changes if c["emergency"])
success_rate = success_chg / total_chg * 100
emergency_rate = emergency_chg / total_chg * 100

print(f"  Change totali: {total_chg}")
print(f"  Change Success Rate: {success_rate:.1f}% (target: ≥95%) → {'OK ' if success_rate >= 95 else 'WARN'}")
print(f"  Emergency Change Rate: {emergency_rate:.1f}% (target: ≤5%) → {'OK ' if emergency_rate <= 5 else 'WARN'}")

print("\n" + "=" * 60)
```

**Esegui lo script:**

```bash
# Su SRV-LINUX-01
python3 /opt/lab-scripts/kpi_itsm_monthly.py
```

---

## Checklist di Validazione — Tutorial ops01b Completato

### Fondamenti (Part A)
- [ ] Sai distinguere Incident da Service Request da Problem da Change con esempi
- [ ] Sai calcolare la priorità P1-P5 usando la matrice Impatto × Urgenza
- [ ] Sai elencare le 7 fasi del ciclo di vita di un Incident
- [ ] Sai descrivere i 3 tipi di Change (Standard/Normal/Emergency)
- [ ] Sai spiegare la differenza tra Workaround e Fix Permanente
- [ ] Sai applicare i 5 Perché per identificare una causa radice
- [ ] Sai leggere e interpretare KPI ITSM (MTTR, SLA Compliance, Change Success Rate)

### Operazioni (Part B)
- [ ] B1: Classificato correttamente tutti e 6 gli scenari proposti
- [ ] B2: Incident P2 DNS aperto in GLPI con Categoria, Priorità, Descrizione strutturata
- [ ] B2: Almeno 3 Follow-up di investigazione documentati nel ticket
- [ ] B2: DNS ripristinato, ticket chiuso con soluzione documentata
- [ ] B3: Problem ticket aperto in GLPI e collegato all'Incident
- [ ] B3: 5 Whys completato — causa radice: Windows Update consuma RAM
- [ ] B3: Workaround documentato nel ticket Problem
- [ ] B4: RFC (CHG) aperta con piano implementazione e rollback completi
- [ ] B4: Matrice di rischio compilata: score Basso
- [ ] B4: Change approvato, implementato, e chiuso come "Success"
- [ ] B5: Query SQL sui KPI GLPI eseguita con successo
- [ ] B5: Dashboard con almeno 2 widget configurata in GLPI

### Governance (Part C)
- [ ] SOP-INC-001 letta e compresa (criteri Major Incident, SLA, escalation)
- [ ] Template RFC compilato per il change dell'esercizio B4
- [ ] Script `kpi_itsm_monthly.py` eseguito con output corretto

---

## Appendice A: Triage Decision Tree

```
NUOVO EVENTO IT ──────────────────────────────────────┐
                                                       │
┌──────────────────────────────────────────────────────┤
│                                                       │
▼                                                       │
"È qualcosa che dovrebbe/deve funzionare ma non         │
 funziona?"                                            │
   SÌ → INCIDENT → calcola P1-P5 → apri INC ticket    │
   NO  → continua ▼                                    │
                                                       │
"È una richiesta standard prevista e pianificata?"     │
   SÌ → SERVICE REQUEST → apri SR ticket               │
   NO  → continua ▼                                    │
                                                       │
"È la causa/pattern di incidenti multipli?"            │
   SÌ → PROBLEM → apri PRB ticket + RCA                │
   NO  → continua ▼                                    │
                                                       │
"Stai aggiungendo/modificando/rimuovendo qualcosa?"    │
   SÌ → CHANGE → Standard/Normal/Emergency?            │
        Standard: procedura documentata, procedi       │
        Normal: apri RFC, CAB, finestra manutenzione   │
        Emergency: apri RFC urgente, eCAB immediato    │
   NO  → Documenta la situazione e riclassifica        │
                                                       │
└──────────────────────────────────────────────────────┘
```

---

## Appendice B: Cheat Sheet Comandi GLPI

| Azione | URL GLPI | Note |
|--------|----------|------|
| Nuovo Incident | /glpi/front/ticket.form.php | Tipo=Incident |
| Nuovo Problem | /glpi/front/problem.form.php | |
| Nuova RFC Change | /glpi/front/change.form.php | |
| Dashboard KPI | /glpi/front/central.php | Widget configurabili |
| KEDB (Known Error) | Incident → Problemi collegati | |
| Catalogo Servizi | /glpi/front/knowbaseitem.php | Knowledge Base |
| Gestione SLA | Setup → Dropdowns → SLA | Solo Admin |

---

## Riferimenti

| Risorsa | Posizione | Contenuto |
|---|---|---|
| Documento sorgente | `../01-framework-metodologie.md` (sez. 3-5) | Incident, Problem, Change |
| ITIL 4 Foundation | axelos.com | Definizioni ufficiali |
| GLPI Documentation | glpi-project.org/documentation | GLPI ITSM tool |
| Tutorial ops01a | `tutorial_ops01_ch1a_itil_foundations_lab.md` | ITIL Fondamenti |
| Tutorial ops07a | `tutorial_ops07_ch1a_monitoring_setup_lab.md` | Monitoring → fonte di Incident |
| Tutorial ops11a | `tutorial_ops11_ch1a_methodology_network_lab.md` | Troubleshooting → supporta RCA |

---

*Fine tutorial ops01b — Prossimo: `tutorial_ops04_ch1a_dns_dhcp_ntp_lab.md`*
