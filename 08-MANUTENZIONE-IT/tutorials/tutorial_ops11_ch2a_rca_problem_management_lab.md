# Tutorial: Root Cause Analysis e Problem Management

> **Documento di riferimento:** `11-troubleshooting-generale.md` (sezioni 12-16)
> **Dominio:** Troubleshooting Generale IT (Dominio 11)
> **Ambito:** RCA approfondita (5 Whys, Ishikawa, FTA, Kepner-Tregoe, Pareto), Problem Management ITIL 4, matrice di escalation, Knowledge Base Management
> **Durata lab:** 7-9 ore (suddivise in 3 sessioni)
> **Livello:** Avanzato — richiede esperienza operativa con incidenti reali
> **Prerequisiti:** `tutorial_ops07_ch1b_incident_management_lab.md`, `tutorial_ops11_ch1a_methodology_network_lab.md`
> **Ambiente:** Carta e penna per esercizi RCA + GLPI per registrazione Problem Record

---

## Analogia Iniziale: L'Investigatore

Un detective non si ferma al "chi ha sparato" — cerca il movente, l'opportunità, la sequenza esatta di eventi. Sherlock Holmes non dichiara "la pistola ha ucciso il colonnello" e chiude il caso. Indaga: perché il colonnello era lì, perché qualcuno voleva ucciderlo, come prevenire che accada di nuovo.

La **Root Cause Analysis** è l'investigazione IT. Non ti fermi a "il server era giù perché il disco era pieno". Indaghi: perché il disco era pieno (log cresciuti), perché i log erano cresciuti (il servizio era in crash loop), perché era in crash loop (deployment rotto), perché il deployment era rotto (test insufficienti), perché i test erano insufficienti (pressione sul team di sviluppo).

La **causa radice** è la pressione che ha eliminato i test. Risolvi quello, e non avrai più lo stesso incidente.

---

## Lab Environment Setup

### Prerequisiti

Questo tutorial usa principalmente:
1. **GLPI** a `http://192.168.56.20:8080` — per gestire Problem Record e KEDB
2. **Carte di scenario** — esercizi di analisi su incidenti simulati (su carta prima, poi su GLPI)
3. **Python** su SRV-LINUX-01 — per automazione KCS

```bash
# Su SRV-LINUX-01 — verificare GLPI
curl -sf http://localhost:8080/glpi/ && echo "GLPI: OK" || echo "GLPI: non raggiungibile"

# Directory di lavoro per questo tutorial
mkdir -p /opt/rca/{scenarios,kedb,templates,reports}
```

---

## PART A: FONDAMENTI — La Famiglia delle Tecniche RCA

### Concetto A1: Perché la RCA è Diversa dal Troubleshooting

**Analogia**: Il troubleshooting è il pronto soccorso — stabilizzi il paziente, fermi l'emorragia. La RCA è la diagnosi cardiologica approfondita — capisci perché il cuore si è fermato e come evitarlo.

**Differenza fondamentale:**

| Dimensione | Troubleshooting | Root Cause Analysis |
|---|---|---|
| **Obiettivo** | Ripristinare il servizio | Trovare e correggere la causa radice |
| **Tempo** | Minuti/ore durante l'incidente | Ore/giorni dopo l'incidente |
| **Output** | Servizio funzionante | Report RCA con action items |
| **Domanda chiave** | "Come faccio a far funzionare di nuovo?" | "Perché si è rotto e come evitiamo la prossima volta?" |
| **Approccio** | Empirico, reattivo | Analitico, investigativo |

**Quando fare una RCA formale:**
- Tutti gli incidenti P1 (obbligatorio)
- Incidenti P2 con impatto significativo (raccomandato)
- Incidenti ricorrenti (3+ incidenti identici in 30 giorni)
- Quando la causa non è chiara dopo la risoluzione

### Concetto A2: La Scelta della Tecnica RCA

Non esiste una tecnica "migliore" in assoluto — ogni tecnica ha i suoi punti di forza:

```
5 WHYS
  ↓ Veloce, intuitivo, per problemi lineari
  ✅ Usa quando la catena causale è unica e diretta
  ❌ Non adatto a problemi multi-causa complessi

ISHIKAWA (Fishbone)
  ↓ Esplora tutte le categorie di causa in modo sistematico
  ✅ Usa quando non sai dove guardare, vuoi un brainstorming strutturato
  ❌ Non modella relazioni logiche (AND/OR) tra le cause

FAULT TREE ANALYSIS (FTA)
  ↓ Modella relazioni logiche booleane (AND, OR)
  ✅ Usa per analisi di affidabilità, single point of failure, ridondanza
  ❌ Complesso da disegnare per sistemi grandi

KEPNER-TREGOE (IS/IS NOT)
  ↓ Delimita chirurgicamente il problema per differenza
  ✅ Usa quando il problema è intermittente, parziale, o ha una distribuzione strana
  ❌ Richiede tempo — non adatto durante un incidente attivo

ANALISI DI PARETO
  ↓ Identifica le cause che generano l'80% dei problemi
  ✅ Usa per prioritizzare gli investimenti di miglioramento
  ❌ Richiede dati storici aggregati (non per singolo incidente)
```

### Concetto A3: La Distinzione Sintomo / Causa / Causa Radice

**Analogia**: Un paziente ha la febbre (sintomo). La febbre è causata da un'infezione polmonare (causa prossima). L'infezione è avvenuta perché il sistema immunitario è compromesso per un trattamento chemioterapico (causa radice). Curare solo la febbre con il paracetamolo non risolve il problema.

**La triade sintomo–causa–causa radice:**

```
SINTOMO           "Il sito web è irraggiungibile"
      ↓
CAUSA PROSSIMA    "Il servizio Apache è fermo"
      ↓
CAUSA INTERMEDIA  "Il server ha esaurito la RAM"
      ↓
CAUSA RADICE      "Nessun alert configurato sulla memoria"
                  + "Nessun limite JVM configurato"
```

**Regola pratica**: la causa radice è sempre trovata a un livello organizzativo o procedurale, non solo tecnico. Se la causa radice è "il disco era pieno" — non hai finito. Il disco era pieno perché: nessuno monitorava (processo mancante), o il capacity planning non era stato fatto (pratica mancante).

### Concetto A4: Problem Management ITIL 4 — Incidente vs Problema

**Analogia**: L'incidente è un singolo tubo che perde. Il problema è la causa sistemica — le tubature di quell'edificio sono vecchie e cedono periodicamente. L'incident manager aggiusta il singolo tubo. Il problem manager studia le tubature e pianifica la sostituzione.

```
INCIDENTE ≠ PROBLEMA

Incidente: "Il database è andato giù questa mattina alle 10:30"
  → Risposta: Riavviare il DB, comunicare agli utenti, ripristinare
  → Owner: Incident Manager
  → Obiettivo: RIPRISTINO DEL SERVIZIO (MTTR)

Problema: "Il database è andato giù 4 volte questo mese"
  → Risposta: Aprire un Problem Record, fare RCA, trovare e correggere la causa
  → Owner: Problem Manager
  → Obiettivo: PREVENZIONE DEGLI INCIDENTI FUTURI
```

**Ciclo di vita di un Problem Record ITIL:**

```
1. RILEVAMENTO
   → Trigger: 3+ incidenti identici, Major Incident concluso, analisi trend
   → Azione: Aprire Problem Record in GLPI

2. CATEGORIZZAZIONE E PRIORITÀ
   → Categoria: Rete / Server / Applicazione / Database / Sicurezza
   → Priorità: basata su frequenza incidenti + impatto medio

3. INVESTIGAZIONE
   → Tecnica RCA scelta (5 Whys, Ishikawa, KT...)
   → Coinvolgere i team tecnici competenti

4. KNOWN ERROR / WORKAROUND
   → Se trovato workaround: documentarlo in KEDB
   → Il Service Desk può usarlo per risolvere velocemente gli incidenti correlati

5. RISOLUZIONE PERMANENTE
   → Aprire RFC (Request for Change)
   → Implementare fix tramite Change Management
   → Verificare che gli incidenti cessi no

6. CHIUSURA
   → Documentare tutto, chiudere il Problem Record
   → Aggiornare la knowledge base
```

---

## PART B: OPERAZIONI — Applicare le Tecniche RCA

### Esercizio B1: 5 Whys — Applicazione su Scenario Reale

**Obiettivo.** Applicare la tecnica dei 5 Whys a uno scenario di incidente IT reale e documentare il risultato.

**Scenario:** L'applicazione CRM aziendale è rimasta irraggiungibile per 2 ore la scorsa settimana. Il servizio è stato ripristinato riavviando il container Docker. Ora devi fare la RCA.

**Informazioni disponibili** (raccolte durante l'incidente):
- Timestamp incidente: 2026-07-15 09:15 UTC
- Durata: 2 ore (09:15 – 11:15)
- Sintomo: container CRM in stato "OOMKilled"
- Dimensione heap JVM al momento del crash: 14.9 GB
- RAM disponibile sul server: 16 GB
- Ultimo deployment CRM: 2026-07-14 22:00 UTC (sera prima)
- Configurazione JVM: `-Xmx` non impostato (heap illimitato)
- Monitoring: nessun alert configurato per memoria container

**Step 1 — Eseguire i 5 Whys**

```
5 WHYS — CRM IRRAGGIUNGIBILE (INC-2026-0847)
Analista: [tuo nome]
Data: 2026-07-15
════════════════════════════════════════════

Problema osservato:
  Il container CRM è in stato OOMKilled alle 09:15 UTC.

WHY 1: Perché il container è OOMKilled?
→ [Risposta]: Il processo Java ha consumato tutta la RAM disponibile 
  (14.9 GB su 16 GB totali), il kernel ha terminato il container.

WHY 2: Perché il processo Java ha consumato tutta la RAM?
→ [Risposta]: Il parametro JVM -Xmx (max heap) non è configurato,
  quindi Java usa tutto il sistema operativo come heap.

WHY 3: Perché -Xmx non è configurato nel deployment?
→ [Risposta]: Il deployment del 14/07 ha sostituito il template 
  Kubernetes (che aveva -Xmx=4g) con un deployment Docker senza 
  lo stesso parametro.

WHY 4: Perché il nuovo deployment non ha ereditato il parametro?
→ [Risposta]: Non esiste un processo di peer review per le 
  configurazioni di deployment. Il cambiamento è stato fatto 
  da un singolo sviluppatore senza revisione.

WHY 5: Perché non esiste il processo di peer review?
→ [Risposta]: La procedura di deployment non include un checklist
  che copra la configurazione JVM, e non è stata definita 
  alcuna policy per i parametri obbligatori dei container.

CAUSA RADICE:
  Assenza di un processo di peer review per i deployment e 
  mancanza di una checklist dei parametri obbligatori per i container.

CAUSE CONTRIBUENTI:
  1. Nessun limite di risorse a livello Kubernetes/Docker
  2. Nessun alert di monitoraggio sulla memoria del container
  3. Il deployment è avvenuto in orario non lavorativo (22:00)
     senza copertura on-call adeguata

AZIONI CORRETTIVE:
  [ ] IMMEDIATA (24h): Configurare -Xmx4g sul container CRM
  [ ] BREVE (1 settimana): Aggiungere memory limit Docker/K8s (6Gi)
  [ ] MEDIO (2 settimane): Configurare alert Prometheus per memoria container > 80%
  [ ] LUNGO (1 mese): Creare checklist obbligatoria per i deployment
      con peer review richiesta per tutti i parametri JVM e resource limits
```

**Step 2 — Creare il Problem Record in GLPI**

```python
#!/usr/bin/env python3
"""
create_problem_record.py — Crea un Problem Record in GLPI via API.
"""

import requests
import json

GLPI_URL = "http://192.168.56.20:8080/glpi"
USER_TOKEN = "YOUR_USER_TOKEN"
APP_TOKEN = "YOUR_APP_TOKEN"


def get_session(url: str, user_token: str, app_token: str) -> str | None:
    resp = requests.get(
        f"{url}/apirest.php/initSession",
        headers={"Authorization": f"user_token {user_token}", "App-Token": app_token},
        timeout=10
    )
    if resp.status_code == 200:
        return resp.json().get("session_token")
    print(f"Errore sessione: {resp.status_code} — {resp.text}")
    return None


def create_problem(url: str, session: str, app_token: str, problem_data: dict) -> int | None:
    headers = {
        "App-Token": app_token,
        "Session-Token": session,
        "Content-Type": "application/json"
    }
    resp = requests.post(
        f"{url}/apirest.php/Problem",
        headers=headers,
        json={"input": problem_data},
        timeout=15
    )
    if resp.status_code in (200, 201):
        return resp.json().get("id")
    print(f"Errore creazione problema: {resp.status_code} — {resp.text}")
    return None


def add_followup(url: str, session: str, app_token: str, problem_id: int, content: str) -> None:
    headers = {"App-Token": app_token, "Session-Token": session, "Content-Type": "application/json"}
    requests.post(
        f"{url}/apirest.php/ITILFollowup",
        headers=headers,
        json={"input": {"items_id": problem_id, "itemtype": "Problem", "content": content, "is_private": 0}},
        timeout=10
    )


def kill_session(url: str, session: str, app_token: str) -> None:
    requests.get(
        f"{url}/apirest.php/killSession",
        headers={"App-Token": app_token, "Session-Token": session},
        timeout=5
    )


def main() -> None:
    session = get_session(GLPI_URL, USER_TOKEN, APP_TOKEN)
    if not session:
        print("Impossibile avviare la sessione GLPI")
        return

    try:
        problem_data = {
            "name": "CRM OOMKilled - Memory leak / assenza -Xmx",
            "content": (
                "Il container CRM è in stato OOMKilled il 2026-07-15 09:15 UTC.\n"
                "Incidente correlato: INC-2026-0847 (durata 2 ore).\n\n"
                "CAUSA RADICE identificata tramite 5 Whys:\n"
                "- Assenza processo di peer review per deployment\n"
                "- Mancanza checklist parametri obbligatori container\n\n"
                "CAUSE CONTRIBUENTI:\n"
                "1. JVM senza -Xmx\n"
                "2. Nessun memory limit Docker\n"
                "3. Nessun alert monitoraggio memoria container"
            ),
            "status": 3,      # Stato: In corso / Analysis
            "urgency": 2,     # Media
            "impact": 3,      # Alto (2 ore di downtime)
            "priority": 2,    # High
        }

        problem_id = create_problem(GLPI_URL, session, APP_TOKEN, problem_data)
        if problem_id:
            print(f"Problem Record creato: PRB-{problem_id}")
            print(f"Aprire su GLPI: {GLPI_URL}/front/problem.form.php?id={problem_id}")

            # Aggiungere la RCA come followup
            rca_content = (
                "=== RCA — 5 WHYS ===\n\n"
                "WHY 1: Container OOMKilled → Java senza -Xmx consuma tutta la RAM\n"
                "WHY 2: -Xmx non configurato → deployment del 14/07 ha rimosso il parametro\n"
                "WHY 3: Parametro rimosso → nessuna peer review del deployment\n"
                "WHY 4: Nessuna peer review → processo non definito\n"
                "WHY 5: Processo non definito → assenza di checklist e policy\n\n"
                "CAUSA RADICE: Mancanza processo peer review deployment + assenza checklist\n\n"
                "AZIONI (owner: DevOps team):\n"
                "[ ] 24h: -Xmx4g su container CRM\n"
                "[ ] 1w: memory limit Docker 6Gi\n"
                "[ ] 2w: alert Prometheus memoria container\n"
                "[ ] 1m: checklist deployment obbligatoria"
            )
            add_followup(GLPI_URL, session, APP_TOKEN, problem_id, rca_content)
            print(f"RCA aggiunta come followup al problema PRB-{problem_id}")

    finally:
        kill_session(GLPI_URL, session, APP_TOKEN)


if __name__ == "__main__":
    main()
```

---

### Esercizio B2: Diagramma Ishikawa — Caso Studio "Applicazione Lenta"

**Obiettivo.** Costruire un diagramma di Ishikawa per un problema complesso con cause multiple.

**Scenario:** Il sistema ERP è lento dalle 09:00 alle 12:00 ogni mattina. Il problema è presente da 3 settimane, da quando è stato fatto un upgrade del database. Gli utenti si lamentano di attese di 30-60 secondi per operazioni che prima duravano 2-3 secondi.

**Step 1 — Costruire il diagramma**

```
FISHBONE DIAGRAM — "ERP LENTO 09:00-12:00"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

               PERSONE            TECNOLOGIA
                  │                   │
         ┌────────┘                   └────────┐
         │                                     │
     DBA assente     ←──────────── CPU DB al 95%
     in mattina                               │
         │              ERP                   │
     Dev non sa    ←─────LENTO────→    DB aggiornato
     query tuning     09:00-12:00       senza indici
         │          (effetto / problema)       │
         └────────┐                   ┌────────┘
                  │                   │
               PROCESSI            DATI/ENV
                  │                   │
     Upgrade DB    │                  │
     senza test   ←┘                  └→  Stats DB non
     su staging                           ricalcolate
         │                                dopo upgrade
     No query                              │
     plan cache                       Indici obsoleti
     review                           (piani di esecuzione
                                       non più validi)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Step 2 — Approfondire ogni causa con test specifici**

```python
#!/usr/bin/env python3
"""
ishikawa_investigation.py — Traccia un'indagine Ishikawa strutturata.
Per ogni causa identifica il test, i risultati e la probabilità.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Cause:
    category: str
    description: str
    test_command: str
    test_result: str = ""
    probability: Literal["alta", "media", "bassa", "confermata", "esclusa"] = "media"
    action: str = ""


ISHIKAWA_CAUSES = [
    Cause(
        category="Tecnologia",
        description="CPU database al 95% nelle ore di picco",
        test_command="SELECT * FROM pg_stat_activity WHERE state = 'active' ORDER BY query_start;",
        test_result="Trovate 47 query con durata > 30 secondi, tutte fan attive nelle 09:00-11:30",
        probability="confermata",
        action="Ottimizzare le query più lente, aggiungere indici mancanti"
    ),
    Cause(
        category="Dati/Ambiente",
        description="Statistiche DB non ricalcolate dopo l'upgrade",
        test_command="SELECT schemaname, tablename, last_analyze, last_autoanalyze FROM pg_stat_user_tables ORDER BY last_analyze NULLS FIRST;",
        test_result="23 tabelle non aggiornate da > 3 settimane (data upgrade)",
        probability="confermata",
        action="ANALYZE su tutte le tabelle principali, configurare autovacuum più aggressivo"
    ),
    Cause(
        category="Processi",
        description="Upgrade DB senza test su staging",
        test_command="git log --oneline --since='3 weeks ago'  # verificare la storia dei deploy",
        test_result="Upgrade eseguito direttamente in produzione senza ambiente di test",
        probability="confermata",
        action="Creare pipeline staging → produzione obbligatoria per tutti i DB upgrade"
    ),
    Cause(
        category="Tecnologia",
        description="Indici obsoleti / piani di esecuzione non validi",
        test_command="EXPLAIN ANALYZE SELECT ... (la query più lenta dall'ERP);",
        test_result="Seq Scan su tabella orders (5M righe) invece di Index Scan",
        probability="confermata",
        action="REINDEX su tabelle principali, verificare gli indici dopo ogni major upgrade"
    ),
    Cause(
        category="Persone",
        description="DBA non disponibile in orario picco per monitoraggio",
        test_command="Verificare il calendario reperibilità",
        test_result="DBA disponibile solo 09:00-17:00, picco 09:00-12:00 coincide",
        probability="media",
        action="Configurare alert automatici, non dipendere dalla presenza fisica"
    ),
]


def print_investigation_report(causes: list[Cause]) -> None:
    print("\n" + "=" * 70)
    print("  REPORT INDAGINE ISHIKAWA")
    print("=" * 70)

    confirmed = [c for c in causes if c.probability == "confermata"]
    excluded = [c for c in causes if c.probability == "esclusa"]
    pending = [c for c in causes if c.probability not in ("confermata", "esclusa")]

    status_map = {
        "confermata": "✅ CONFERMATA",
        "esclusa": "❌ ESCLUSA",
        "alta": "⚠️  PROBABILE",
        "media": "❓ VERIFICARE",
        "bassa": "➖ IMPROBABILE"
    }

    for cause in causes:
        status = status_map.get(cause.probability, "❓")
        print(f"\n  [{cause.category}] {cause.description}")
        print(f"  Stato:      {status}")
        print(f"  Test:       {cause.test_command[:60]}...")
        if cause.test_result:
            print(f"  Risultato:  {cause.test_result[:80]}")
        if cause.action:
            print(f"  Azione:     {cause.action[:80]}")

    print(f"\n{'=' * 70}")
    print(f"  RIEPILOGO:")
    print(f"  Cause confermate: {len(confirmed)}")
    print(f"  Cause escluse:    {len(excluded)}")
    print(f"  Da verificare:    {len(pending)}")
    print(f"\n  CAUSA RADICE PRINCIPALE:")
    for c in confirmed:
        print(f"  → {c.description} [{c.category}]")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    print_investigation_report(ISHIKAWA_CAUSES)
```

---

### Esercizio B3: Kepner-Tregoe — Matrice IS/IS NOT

**Obiettivo.** Applicare la matrice IS/IS NOT a un problema con distribuzione anomala (si verifica solo in certi contesti).

**Scenario:** Il modulo "Fatturazione" dell'ERP non funziona, ma solo per gli utenti di Milano, e solo dal lunedì al giovedì. Il venerdì e il weekend funziona. Roma e Napoli non hanno problemi.

**Step 1 — Costruire la matrice IS/IS NOT**

```
MATRICE KEPNER-TREGOE IS/IS NOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Problema: Modulo Fatturazione ERP non funziona

┌──────────────┬──────────────────────┬──────────────────────┬─────────────────────┐
│ DIMENSIONE   │ IS (È)               │ IS NOT (NON È)       │ DISTINZIONE         │
├──────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ COSA         │ Modulo Fatturazione  │ Modulo Ordini        │ Fatturazione usa    │
│              │ non funziona         │ funziona             │ un'API esterna      │
│              │ (timeout / errore    │ Modulo Magazzino     │ di fiscalizzazione  │
│              │ 504)                 │ funziona             │                     │
├──────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ DOVE         │ Solo utenti Milano   │ Roma: funziona       │ Milano ha proxy     │
│              │                      │ Napoli: funziona     │ locale diverso      │
│              │                      │ HQ: funziona         │ (configurato a      │
│              │                      │                      │ gennaio 2026)       │
├──────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ QUANDO       │ Lunedì – Giovedì     │ Venerdì: funziona    │ Il Venerdì il DBA   │
│              │ 08:00 – 18:00        │ Weekend: funziona    │ esegue la           │
│              │                      │ Notte: funziona      │ manutenzione del    │
│              │                      │                      │ proxy (riavvio)     │
├──────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ QUANTO       │ Tutti gli utenti di  │ Non tutti i moduli:  │ Solo le funzioni    │
│              │ Milano su Fatturaz.  │ solo Fatturazione    │ che chiamano API    │
│              │ (~35 utenti)         │ (Ordini non usano    │ fiscalizzazione     │
│              │                      │ l'API esterna)       │ esterna (Agyo)      │
└──────────────┴──────────────────────┴──────────────────────┴─────────────────────┘

ANALISI DELLE DISTINZIONI:
1. Milano ha un proxy locale diverso da Roma/Napoli (installato a gennaio)
2. Il Venerdì il proxy viene riavviato per manutenzione → funziona
3. Solo i moduli che usano l'API esterna Agyo (fatturazione elettronica) sono colpiti

IPOTESI DERIVATA DALLE DISTINZIONI:
  Il proxy di Milano blocca o altera le richieste verso l'API Agyo 
  (probabilmente una regola SSL inspection errata o timeout aggressivo 
  che viene azzerato al riavvio del Venerdì).

TEST DI CONFERMA:
  → Bypassare il proxy di Milano per l'IP dell'API Agyo
  → Se il modulo funziona: ipotesi confermata
  → Se non funziona: cercare un'altra distinzione
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Step 2 — Creare lo script di test di conferma**

```python
#!/usr/bin/env python3
"""
kt_hypothesis_test.py — Test automatizzato per confermare o smentire
l'ipotesi derivata dalla matrice Kepner-Tregoe.
"""

import requests
import socket
import subprocess


def test_api_connectivity(api_url: str, timeout: int = 10) -> dict:
    """Testa la connettività verso l'API esterna."""
    result = {
        "url": api_url,
        "reachable": False,
        "status_code": None,
        "response_time_ms": None,
        "error": None
    }
    try:
        import time
        start = time.time()
        resp = requests.get(api_url, timeout=timeout, verify=False)
        elapsed = (time.time() - start) * 1000
        result["reachable"] = True
        result["status_code"] = resp.status_code
        result["response_time_ms"] = round(elapsed, 1)
    except requests.exceptions.ProxyError as e:
        result["error"] = f"Proxy error: {e}"
    except requests.exceptions.SSLError as e:
        result["error"] = f"SSL error (proxy inspection?): {e}"
    except requests.exceptions.ConnectTimeout:
        result["error"] = "Timeout di connessione"
    except Exception as e:
        result["error"] = str(e)
    return result


def test_proxy_bypass(api_url: str, timeout: int = 10) -> dict:
    """Testa la connettività bypassando il proxy."""
    import os
    old_http = os.environ.pop("http_proxy", None)
    old_https = os.environ.pop("https_proxy", None)
    try:
        return test_api_connectivity(api_url, timeout)
    finally:
        if old_http:
            os.environ["http_proxy"] = old_http
        if old_https:
            os.environ["https_proxy"] = old_https


def main() -> None:
    # URL dell'API esterna (esempio simulato in lab)
    api_url = "http://192.168.56.20:8080/glpi/apirest.php/initSession"

    print("=" * 60)
    print("  TEST KEPNER-TREGOE — Conferma ipotesi proxy")
    print("=" * 60)

    # Test con proxy (simula la situazione di Milano)
    print("\n1. Test CON proxy (simula Milano):")
    with_proxy = test_api_connectivity(api_url)
    _print_result(with_proxy)

    # Test senza proxy (simula il bypass)
    print("\n2. Test SENZA proxy (bypass):")
    without_proxy = test_proxy_bypass(api_url)
    _print_result(without_proxy)

    # Interpretazione
    print("\n" + "=" * 60)
    print("  INTERPRETAZIONE:")
    if with_proxy["error"] and not without_proxy["error"]:
        print("  ✅ IPOTESI CONFERMATA: il proxy causa il problema")
        print("  → Azione: esaminare le regole SSL inspection del proxy di Milano")
    elif not with_proxy["error"] and not without_proxy["error"]:
        print("  ❌ IPOTESI NON CONFERMATA: entrambi i percorsi funzionano")
        print("  → L'ipotesi è sbagliata: cercare un'altra distinzione")
    elif with_proxy["error"] and without_proxy["error"]:
        print("  ❌ ENTRAMBI I PERCORSI FALLISCONO")
        print("  → Il problema non è il proxy: è l'API stessa a non rispondere")
    print("=" * 60)


def _print_result(result: dict) -> None:
    if result["reachable"]:
        print(f"  ✅ Raggiungibile — Status: {result['status_code']} — {result['response_time_ms']} ms")
    else:
        print(f"  ❌ Non raggiungibile — Errore: {result['error']}")


if __name__ == "__main__":
    main()
```

---

### Esercizio B4: Analisi Pareto — Prioritizzare le Azioni di Miglioramento

**Obiettivo.** Analizzare 3 mesi di dati incidenti e identificare le cause che generano l'80% dei problemi.

```python
#!/usr/bin/env python3
"""
pareto_incident_analysis.py — Analisi di Pareto su dati incidenti da GLPI
o da file JSON di esempio. Identifica le cause dell'80% degli incidenti.
"""

import json
import requests
from collections import Counter
from pathlib import Path

GLPI_URL = "http://192.168.56.20:8080/glpi"
USER_TOKEN = "YOUR_USER_TOKEN"
APP_TOKEN = "YOUR_APP_TOKEN"

# Dati di esempio (3 mesi di incidenti simulati)
SAMPLE_DATA_90_DAYS = [
    {"id": i, "root_cause": cause, "priority": prio, "downtime_min": minutes}
    for i, (cause, prio, minutes) in enumerate([
        ("Errore di configurazione", "P2", 45), ("Patch non applicato", "P2", 90),
        ("Errore di configurazione", "P3", 15), ("Capacity insufficiente", "P2", 120),
        ("Password/Cert scaduto", "P3", 30), ("Errore di configurazione", "P1", 240),
        ("Guasto hardware", "P1", 180), ("Patch non applicato", "P3", 30),
        ("Errore di configurazione", "P3", 10), ("Capacity insufficiente", "P3", 60),
        ("Password/Cert scaduto", "P2", 45), ("Errore di configurazione", "P3", 20),
        ("Bug software vendor", "P2", 75), ("Patch non applicato", "P2", 60),
        ("Capacity insufficiente", "P2", 90), ("Password/Cert scaduto", "P3", 30),
        ("Errore utente", "P3", 15), ("Errore di configurazione", "P3", 25),
        ("Guasto hardware", "P2", 120), ("Bug software vendor", "P3", 45),
        ("Errore di configurazione", "P2", 50), ("Patch non applicato", "P1", 200),
        ("Capacity insufficiente", "P3", 40), ("Password/Cert scaduto", "P3", 25),
        ("Errore di configurazione", "P3", 30), ("Bug software vendor", "P3", 55),
        ("Errore utente", "P4", 10), ("Guasto hardware", "P3", 90),
        ("Patch non applicato", "P2", 80), ("Errore di configurazione", "P2", 35),
    ] * 4)  # 120 incidenti
]


def calculate_pareto(incidents: list[dict]) -> None:
    total = len(incidents)

    # Conteggio per causa
    cause_counts = Counter(inc["root_cause"] for inc in incidents)

    # Downtime totale per causa
    cause_downtime: dict[str, int] = {}
    for inc in incidents:
        cause = inc["root_cause"]
        cause_downtime[cause] = cause_downtime.get(cause, 0) + inc.get("downtime_min", 0)

    print(f"\n{'='*75}")
    print(f"  ANALISI PARETO — {total} INCIDENTI (90 GIORNI)")
    print(f"{'='*75}")
    print(f"\n  {'Causa Radice':<32} {'N':>4} {'%':>6}  {'Cum.%':>7}  {'DT(h)':>6}  Priorità")
    print(f"  {'-'*72}")

    cumulative = 0.0
    for cause, count in cause_counts.most_common():
        pct = count / total * 100
        cumulative += pct
        dt_hours = cause_downtime.get(cause, 0) / 60
        action_flag = "🔴 CRITICA" if cumulative <= 80 else ("🟡 MEDIA" if cumulative <= 95 else "⚪ BASSA")
        print(f"  {cause:<32} {count:>4} {pct:>6.1f}%  {cumulative:>7.1f}%  {dt_hours:>6.1f}h  {action_flag}")

    print(f"\n{'='*75}")
    print("  PIANO DI AZIONE DERIVATO:")
    print(f"{'='*75}")

    improvement_actions = {
        "Errore di configurazione": [
            "Introdurre peer review obbligatoria per ogni change di configurazione",
            "Implementare Infrastructure as Code (Ansible/Terraform) per standardizzare",
            "Configurare drift detection automatizzata (Ansible check mode + alert)"
        ],
        "Patch non applicato": [
            "Automatizzare il patching con WSUS/SCCM + finestre fisse settimanali",
            "Dashboard patch compliance con alert per sistemi > 30 giorni non patchati",
            "Processo di eccezione documentato per sistemi che non possono essere patchati"
        ],
        "Capacity insufficiente": [
            "Capacity planning trimestrale con dati Prometheus predict_linear()",
            "Alert Prometheus a 75% utilizzo (warning) e 85% (critical)",
            "Processo di approvvigionamento accelerato (max 2 settimane)"
        ],
        "Password/Cert scaduto": [
            "Inventario centralizzato di tutti i certificati (con data scadenza)",
            "Alert automatici 60/30/7/1 giorni prima della scadenza",
            "Rotazione automatica certificati con Let's Encrypt o Vault"
        ],
    }

    cumulative2 = 0.0
    for cause, count in cause_counts.most_common():
        pct = count / total * 100
        cumulative2 += pct
        if cumulative2 > 85:
            break
        actions = improvement_actions.get(cause, ["Analisi specifica richiesta"])
        print(f"\n  {cause} ({count} incidenti, {cause_downtime.get(cause,0)/60:.0f}h downtime):")
        for action in actions:
            print(f"    → {action}")

    print(f"\n{'='*75}\n")


if __name__ == "__main__":
    calculate_pareto(SAMPLE_DATA_90_DAYS)
```

---

### Esercizio B5: Known Error Database — Creare e Interrogare la KEDB

**Obiettivo.** Creare e gestire una Knowledge Base degli errori noti (KEDB) in formato locale, usabile dal Service Desk per risolvere velocemente gli incidenti ricorrenti.

```python
#!/usr/bin/env python3
"""
kedb_manager.py — Gestione del Known Error Database (KEDB) locale.
"""

import json
from datetime import datetime
from pathlib import Path

KEDB_PATH = Path("/opt/rca/kedb/kedb.json")


def load_kedb() -> list[dict]:
    if KEDB_PATH.exists():
        return json.loads(KEDB_PATH.read_text())
    return []


def save_kedb(entries: list[dict]) -> None:
    KEDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    KEDB_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False))


def add_entry(
    title: str,
    symptom: str,
    root_cause: str,
    workaround: str,
    permanent_fix: str,
    service: str,
    problem_id: str
) -> str:
    entries = load_kedb()
    entry_id = f"KE-{datetime.now().strftime('%Y')}-{len(entries)+1:04d}"
    entry = {
        "id": entry_id,
        "problem_id": problem_id,
        "service": service,
        "title": title,
        "symptom": symptom,
        "root_cause": root_cause,
        "workaround": workaround,
        "permanent_fix": permanent_fix,
        "status": "workaround_active",
        "created": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
    }
    entries.append(entry)
    save_kedb(entries)
    return entry_id


def search_kedb(keyword: str) -> list[dict]:
    entries = load_kedb()
    kw = keyword.lower()
    return [
        e for e in entries
        if kw in e.get("symptom", "").lower()
        or kw in e.get("title", "").lower()
        or kw in e.get("service", "").lower()
    ]


def print_entry(entry: dict) -> None:
    print(f"\n{'='*65}")
    print(f"  KEDB ID: {entry['id']}  |  Problema: {entry['problem_id']}")
    print(f"  Servizio: {entry['service']}")
    print(f"  Titolo: {entry['title']}")
    print(f"  Stato: {entry['status']}")
    print(f"\n  SINTOMO:")
    print(f"  {entry['symptom']}")
    print(f"\n  CAUSA RADICE:")
    print(f"  {entry['root_cause']}")
    print(f"\n  WORKAROUND:")
    print(f"  {entry['workaround']}")
    print(f"\n  SOLUZIONE PERMANENTE:")
    print(f"  {entry['permanent_fix']}")
    print(f"{'='*65}")


def main() -> None:
    # Aggiungere gli errori noti dai nostri scenari precedenti
    ke1 = add_entry(
        title="CRM OOMKilled — JVM senza -Xmx su container Docker",
        symptom="Container CRM in stato OOMKilled. Applicazione irraggiungibile (HTTP 502). "
                "Il riavvio del container risolve temporaneamente ma il problema si ripresenta in 4-8 ore.",
        root_cause="Il processo Java del CRM non ha il parametro -Xmx configurato, "
                   "quindi usa tutta la RAM del sistema. Il kernel termina il container (OOM Killer).",
        workaround="1. docker restart crm-container\n"
                   "2. Se si ha accesso al deployment: aggiungere -e JAVA_OPTS='-Xmx4g' al container\n"
                   "   docker run ... -e JAVA_OPTS='-Xmx4g' ...\n"
                   "3. Monitor RAM: docker stats crm-container",
        permanent_fix="RFC-2026-0091: Aggiungere -Xmx4g e memory limit 6Gi al deployment. "
                      "Pianificato per 2026-07-20. Owner: DevOps team.",
        service="CRM — Salesforce interno",
        problem_id="PRB-2026-0018"
    )
    print(f"Aggiunto: {ke1}")

    ke2 = add_entry(
        title="ERP Fatturazione timeout — Proxy Milano blocca API Agyo",
        symptom="Il modulo Fatturazione dell'ERP restituisce errore 504 (timeout) "
                "per gli utenti di Milano. Il problema si verifica solo Lun-Gio 08:00-18:00. "
                "Gli utenti di Roma e Napoli non hanno problemi.",
        root_cause="Il proxy di Milano (installato a gennaio 2026) applica SSL inspection "
                   "verso l'API Agyo che causa un timeout di 30 secondi. L'API richiede 45 secondi. "
                   "Il riavvio settimanale del venerdì resetta il timeout dell'inspection.",
        workaround="1. Aggiungere l'IP dell'API Agyo (185.x.x.x) alla bypass list del proxy\n"
                   "2. Oppure: configurare la regola SSL inspection con timeout 120 secondi",
        permanent_fix="Aggiornare la configurazione proxy di Milano con bypass list per i domini API Agyo. "
                      "RFC-2026-0092 in pianificazione. Entro 2026-07-30.",
        service="ERP — Modulo Fatturazione",
        problem_id="PRB-2026-0019"
    )
    print(f"Aggiunto: {ke2}")

    # Ricerca nella KEDB
    print("\n\n=== RICERCA KEDB: 'timeout' ===")
    results = search_kedb("timeout")
    for entry in results:
        print_entry(entry)

    print("\n\n=== RICERCA KEDB: 'container' ===")
    results = search_kedb("container")
    for entry in results:
        print_entry(entry)

    print(f"\nKEDB salvato in: {KEDB_PATH}")
    print(f"Totale errori noti: {len(load_kedb())}")


if __name__ == "__main__":
    main()
```

---

### Esercizio B6: Matrice di Escalation — Applicazione Pratica

**Obiettivo.** Calcolare la priorità di un incidente dalla matrice Impatto/Urgenza e determinare i passi di escalation corretti.

```python
#!/usr/bin/env python3
"""
escalation_calculator.py — Calcola priorità e passi di escalation
dalla matrice Impatto/Urgenza ITIL.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

PRIORITY_MATRIX = {
    ("alto", "alta"): ("P1", "CRITICAL", 4),
    ("alto", "media"): ("P2", "HIGH", 8),
    ("alto", "bassa"): ("P3", "MEDIUM", 24),
    ("medio", "alta"): ("P2", "HIGH", 8),
    ("medio", "media"): ("P3", "MEDIUM", 24),
    ("medio", "bassa"): ("P4", "LOW", 120),
    ("basso", "alta"): ("P3", "MEDIUM", 24),
    ("basso", "media"): ("P4", "LOW", 120),
    ("basso", "bassa"): ("P5", "MINOR", 240),
}

ESCALATION_STEPS = {
    "P1": [
        (0, "Assegnazione immediata L2 — Bridge call aperta"),
        (5, "Notifica IT Manager e Service Delivery Manager"),
        (15, "Escalation L3 se nessun progresso"),
        (30, "Notifica CTO/Direttore IT — Management briefing"),
        (60, "Valutare failover/DR — Contattare vendor"),
    ],
    "P2": [
        (0, "Assegnazione L1/L2"),
        (15, "Escalation L2 se L1 non risolve"),
        (30, "Notifica IT Manager se nessun workaround"),
        (60, "Escalation L3"),
        (120, "Contatto vendor se necessario"),
    ],
    "P3": [
        (0, "Assegnazione L1"),
        (30, "Escalation L2 se L1 non risolve"),
        (240, "Notifica team lead se nessun progresso"),
        (480, "Escalation L3 se necessario"),
    ],
    "P4": [
        (0, "Inserimento in coda L1 — Risoluzione in orario lavorativo"),
        (480, "Review team lead se non risolto"),
    ],
    "P5": [
        (0, "Inserimento in coda a bassa priorità"),
        (1440, "Pianificazione in manutenzione ordinaria"),
    ]
}


@dataclass
class Incident:
    title: str
    impact: str      # "alto", "medio", "basso"
    urgency: str     # "alta", "media", "bassa"
    description: str = ""
    start_time: datetime = None

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()


def calculate_escalation(incident: Incident) -> None:
    key = (incident.impact.lower(), incident.urgency.lower())
    priority, label, sla_hours = PRIORITY_MATRIX.get(key, ("P4", "LOW", 120))
    steps = ESCALATION_STEPS.get(priority, [])

    print(f"\n{'='*65}")
    print(f"  CALCOLO PRIORITÀ INCIDENTE")
    print(f"{'='*65}")
    print(f"\n  Titolo:    {incident.title}")
    print(f"  Impatto:   {incident.impact.upper()}")
    print(f"  Urgenza:   {incident.urgency.upper()}")
    print(f"\n  PRIORITÀ: {priority} ({label})")
    print(f"  SLA TARGET: {sla_hours} ore lavorative")
    print(f"  Scadenza SLA: {incident.start_time + timedelta(hours=sla_hours):%d/%m/%Y %H:%M}")

    print(f"\n  TIMELINE DI ESCALATION:")
    for minutes, action in steps:
        action_time = incident.start_time + timedelta(minutes=minutes)
        print(f"  T+{minutes:>4}min [{action_time:%H:%M}]: {action}")

    print(f"\n{'='*65}\n")


def main() -> None:
    # Scenario 1: Incidente critico — email aziendale ferma
    incident1 = Incident(
        title="Email aziendale completamente ferma",
        impact="alto",
        urgency="alta",
        description="Exchange Server non risponde. 200 utenti non possono inviare/ricevere email.",
        start_time=datetime.now()
    )
    calculate_escalation(incident1)

    # Scenario 2: Incidente minore — stampante di un dipartimento
    incident2 = Incident(
        title="Stampante Reparto Contabilità non funziona",
        impact="basso",
        urgency="media",
        description="La stampante del terzo piano non stampa. 5 utenti colpiti, hanno stampante alternativa.",
        start_time=datetime.now()
    )
    calculate_escalation(incident2)

    # Scenario 3: Incidente business-critical — ERP durante la chiusura di bilancio
    incident3 = Incident(
        title="ERP lento durante chiusura mensile",
        impact="alto",
        urgency="alta",
        description="ERP risponde in 45 secondi invece di 2. Chiusura mensile in corso. Deadline ore 17:00.",
        start_time=datetime.now()
    )
    calculate_escalation(incident3)


if __name__ == "__main__":
    main()
```

---

## PART C: SISTEMATIZZARE — Knowledge Base e Miglioramento Continuo

### Progetto C1: KCS — Pipeline di Creazione Articoli KB

**Obiettivo.** Creare uno script che automatizza la creazione di articoli KB ogni volta che un incidente viene risolto.

```python
#!/usr/bin/env python3
"""
kcs_article_generator.py — Genera automaticamente la struttura di un articolo KB
da un incidente risolto. Implementa il workflow KCS (Knowledge-Centered Service).
"""

import json
from datetime import datetime
from pathlib import Path

KB_DIR = Path("/opt/rca/kedb")
KB_INDEX_FILE = KB_DIR / "kb_index.json"


def generate_kb_article(
    incident_id: str,
    symptom: str,
    solution: str,
    category: str,
    subcategory: str,
    environment: str,
    author: str,
    keywords: list[str]
) -> str:
    """Genera l'articolo KB e lo salva. Restituisce il KB ID."""
    existing = json.loads(KB_INDEX_FILE.read_text()) if KB_INDEX_FILE.exists() else []
    year = datetime.now().year
    kb_id = f"KB-{year}-{len(existing)+1:04d}"

    article_path = KB_DIR / f"{kb_id.replace('-', '_').lower()}.md"
    KB_DIR.mkdir(parents=True, exist_ok=True)

    content = f"""---
kb_id: {kb_id}
incidente_correlato: {incident_id}
categoria: {category}
sottocategoria: {subcategory}
parole_chiave: [{", ".join(keywords)}]
livello: L1
versione: 1.0
autore: {author}
data_creazione: {datetime.now().strftime("%Y-%m-%d")}
data_revisione: {(datetime.now().replace(month=datetime.now().month%12+1 if datetime.now().month < 12 else 1)).strftime("%Y-%m-%d")}
stato: draft
---

# {kb_id}: {symptom[:60]}

## SINTOMO
{symptom}

## AMBIENTE APPLICABILE
{environment}

## CAUSA
[Da compilare dopo la RCA]

## SOLUZIONE

{solution}

## VERIFICA
- [ ] Il sintomo non si presenta più dopo aver applicato la soluzione
- [ ] L'utente ha confermato la risoluzione

## NOTE
[Casi particolari, eccezioni, versioni specifiche]

## ARTICOLI CORRELATI
[Da compilare]
"""
    article_path.write_text(content, encoding="utf-8")

    # Aggiornare l'indice
    existing.append({
        "id": kb_id,
        "title": symptom[:80],
        "category": category,
        "subcategory": subcategory,
        "keywords": keywords,
        "status": "draft",
        "file": str(article_path.name),
        "created": datetime.now().isoformat()
    })
    KB_INDEX_FILE.write_text(json.dumps(existing, indent=2, ensure_ascii=False))

    return kb_id


def search_kb(query: str) -> list[dict]:
    """Ricerca nella KB per keyword."""
    if not KB_INDEX_FILE.exists():
        return []
    index = json.loads(KB_INDEX_FILE.read_text())
    q = query.lower()
    return [
        entry for entry in index
        if q in entry.get("title", "").lower()
        or any(q in kw.lower() for kw in entry.get("keywords", []))
        or q in entry.get("category", "").lower()
    ]


def main() -> None:
    # Workflow KCS: alla chiusura di ogni incidente, generare l'articolo KB
    print("=== KCS ARTICLE GENERATOR ===\n")

    kb1 = generate_kb_article(
        incident_id="INC-2026-0847",
        symptom="Container CRM in stato OOMKilled. Applicazione irraggiungibile (HTTP 502/504). "
                "Il riavvio temporaneo risolve ma il problema si ripresenta dopo 4-8 ore.",
        solution=(
            "**Step 1**: Identificare il container in OOMKilled\n"
            "  ```\n"
            "  docker ps -a | grep OOMKilled\n"
            "  ```\n"
            "\n"
            "**Step 2**: Riavviare il container con limite memoria\n"
            "  ```\n"
            "  docker restart crm-container\n"
            "  ```\n"
            "\n"
            "**Step 3**: Applicare il workaround permanente\n"
            "  Aggiungere -Xmx4g come variabile d'ambiente Java:\n"
            "  ```\n"
            "  docker run ... -e JAVA_OPTS='-Xmx4g' ...\n"
            "  ```\n"
            "\n"
            "**Step 4**: Monitorare RAM del container\n"
            "  ```\n"
            "  docker stats crm-container\n"
            "  ```\n"
        ),
        category="Applicazione",
        subcategory="Container / Docker",
        environment="Linux Ubuntu 22.04, Docker 24.x, Java 17",
        author="Lab Admin",
        keywords=["docker", "oom", "killed", "java", "heap", "crm", "memoria", "container"]
    )
    print(f"Articolo creato: {kb1}")

    kb2 = generate_kb_article(
        incident_id="INC-2026-0891",
        symptom="Modulo Fatturazione ERP restituisce errore 504 Gateway Timeout "
                "per gli utenti di Milano. Problema Lun-Gio 08:00-18:00. Roma e Napoli OK.",
        solution=(
            "**Step 1**: Verificare se il problema è legato al proxy\n"
            "  Testare l'API Agyo bypassando il proxy:\n"
            "  ```\n"
            "  curl --noproxy '*' https://api.agyo.it/v1/health\n"
            "  ```\n"
            "\n"
            "**Step 2 (workaround immediato)**: Aggiungere IP Agyo alla bypass list del proxy di Milano\n"
            "  Contattare il team Network per aggiungere 185.x.x.x alla whitelist.\n"
            "\n"
            "**Step 3**: Verificare che il modulo Fatturazione funzioni dopo il bypass\n"
            "  Testare con un utente di Milano: creare una fattura di test.\n"
        ),
        category="Applicazione",
        subcategory="ERP / Fatturazione",
        environment="Windows 10/11, ERP v4.2, Proxy Sophos SG v18, API Agyo",
        author="Lab Admin",
        keywords=["erp", "fatturazione", "timeout", "proxy", "504", "milano", "agyo", "api"]
    )
    print(f"Articolo creato: {kb2}")

    # Dimostrare la ricerca
    print("\n--- RICERCA KB: 'container' ---")
    results = search_kb("container")
    for r in results:
        print(f"  {r['id']}: {r['title']}")

    print("\n--- RICERCA KB: 'proxy' ---")
    results = search_kb("proxy")
    for r in results:
        print(f"  {r['id']}: {r['title']}")

    print(f"\nTotale articoli in KB: {len(json.loads(KB_INDEX_FILE.read_text()))}")
    print(f"KB Index: {KB_INDEX_FILE}")


if __name__ == "__main__":
    main()
```

### Progetto C2: Report Mensile Problem Management

```python
#!/usr/bin/env python3
"""
problem_management_report.py — Genera il report mensile del Problem Management.
Metriche: problema aperto, MTTR medio, trend cause, efficacia workaround.
"""

from datetime import datetime
from pathlib import Path
import json

SAMPLE_PROBLEMS = [
    {"id": "PRB-001", "service": "CRM", "status": "chiuso", "root_cause": "Configurazione", "days_open": 5, "incidents_prevented": 4},
    {"id": "PRB-002", "service": "ERP", "status": "workaround", "root_cause": "Proxy/Rete", "days_open": 8, "incidents_prevented": 2},
    {"id": "PRB-003", "service": "AD", "status": "aperto", "root_cause": "Patch", "days_open": 3, "incidents_prevented": 0},
    {"id": "PRB-004", "service": "Email", "status": "chiuso", "root_cause": "Certificato", "days_open": 2, "incidents_prevented": 6},
    {"id": "PRB-005", "service": "DB", "status": "workaround", "root_cause": "Capacity", "days_open": 12, "incidents_prevented": 3},
]


def generate_pm_report(problems: list[dict]) -> None:
    now = datetime.now()
    total = len(problems)
    open_p = sum(1 for p in problems if p["status"] == "aperto")
    workaround = sum(1 for p in problems if p["status"] == "workaround")
    closed = sum(1 for p in problems if p["status"] == "chiuso")
    avg_days = sum(p["days_open"] for p in problems) / total if total else 0
    total_prevented = sum(p["incidents_prevented"] for p in problems)

    print(f"\n{'='*65}")
    print(f"  REPORT PROBLEM MANAGEMENT — {now.strftime('%B %Y')}")
    print(f"{'='*65}")
    print(f"\n  SOMMARIO:")
    print(f"    Problemi totali nel mese:     {total:>3}")
    print(f"    Aperti (in investigazione):   {open_p:>3}")
    print(f"    Workaround attivo:            {workaround:>3}")
    print(f"    Chiusi (fix permanente):      {closed:>3}")
    print(f"    Giorni medi risoluzione:      {avg_days:>5.1f}")
    print(f"    Incidenti prevenuti dalla KB: {total_prevented:>3}")
    print()
    print(f"  DETTAGLIO PROBLEMI:")
    print(f"  {'ID':<10} {'Servizio':<10} {'Stato':<12} {'Causa':<18} {'Gg':>4}  {'Prevenuti':>9}")
    print(f"  {'-'*62}")
    for p in problems:
        icon = "✅" if p["status"] == "chiuso" else ("⚠️ " if p["status"] == "workaround" else "🔴")
        print(f"  {p['id']:<10} {p['service']:<10} {icon} {p['status']:<10} {p['root_cause']:<18} {p['days_open']:>4}  {p['incidents_prevented']:>9}")

    print(f"\n  KPI PROBLEM MANAGEMENT:")
    resolution_rate = closed / total * 100 if total else 0
    icon_rr = "✅" if resolution_rate >= 60 else ("⚠️ " if resolution_rate >= 40 else "❌")
    print(f"    {icon_rr} Resolution Rate:      {resolution_rate:.0f}%  (target: ≥60%)")
    avg_target = 7.0
    icon_avg = "✅" if avg_days <= avg_target else "⚠️ "
    print(f"    {icon_avg} Giorni medi aperti:  {avg_days:.1f}   (target: ≤{avg_target})")
    print(f"    ✅ Incidenti prevenuti:  {total_prevented}  (ogni incidente evitato = ~1h risparmio)")

    print(f"\n{'='*65}\n")


if __name__ == "__main__":
    generate_pm_report(SAMPLE_PROBLEMS)
```

---

## Checklist di Validazione Lab

**Parte A — Fondamenti:**
- [ ] A1: Spiegare la differenza tra troubleshooting e RCA in 2 frasi
- [ ] A2: Scegliere la tecnica RCA corretta per 4 scenari proposti
- [ ] A3: Costruire la triade Sintomo/Causa/Causa radice per un incidente reale
- [ ] A4: Descrivere il ciclo di vita di un Problem Record ITIL in 6 fasi

**Parte B — Esercizi:**
- [ ] B1: 5 Whys completato con 5 iterazioni e azioni correttive
- [ ] B1: Problem Record creato in GLPI (`create_problem_record.py`)
- [ ] B2: Diagramma Ishikawa costruito con almeno 4 categorie e 2+ cause per categoria
- [ ] B2: `ishikawa_investigation.py` eseguito — output mostra cause confermate/escluse
- [ ] B3: Matrice IS/IS NOT completata con 4 dimensioni (Cosa/Dove/Quando/Quanto)
- [ ] B3: `kt_hypothesis_test.py` eseguito — conclusione dell'ipotesi chiara
- [ ] B4: `pareto_incident_analysis.py` — identificate le cause dell'80% degli incidenti
- [ ] B4: 3 azioni specifiche derivate dall'analisi Pareto
- [ ] B5: KEDB creato con almeno 2 Known Error (`kedb_manager.py`)
- [ ] B5: Ricerca nella KEDB funzionante con risultati pertinenti
- [ ] B6: `escalation_calculator.py` — priorità e timeline corrette per 3 scenari

**Parte C — Sistematizzazione:**
- [ ] C1: Almeno 2 articoli KB generati da `kcs_article_generator.py`
- [ ] C1: Ricerca KB funzionante su keyword
- [ ] C2: `problem_management_report.py` genera report con KPI

---

## Appendice A: Guida alla Scelta della Tecnica RCA

```
HAI UN PROBLEMA DA ANALIZZARE
              │
              ↓
Il problema ha una catena causale unica e lineare?
              │
    ┌─────────┴─────────┐
   SÌ                  NO
    │                   │
  5 WHYS          Il problema è intermittente
    │             o colpisce solo certi contesti?
    ✅                  │
              ┌─────────┴─────────┐
             SÌ                  NO
              │                   │
      KEPNER-TREGOE         Vuoi esplorare
      (IS/IS NOT)           tutte le cause possibili?
              ✅                  │
                        ┌─────────┴─────────┐
                       SÌ                  NO
                        │                   │
                   ISHIKAWA            Hai bisogno di
                   (Fishbone)          modellare le
                        ✅             relazioni logiche?
                                            │
                                   ┌────────┴────────┐
                                  SÌ                NO
                                   │                 │
                                  FTA           ANALISI PARETO
                                  ✅           (su dati aggregati)
                                                      ✅
```

---

## Appendice B: Template di Comunicazione Incidente

```
OGGETTO: [STATO] - [Servizio] - [Sintomo breve]

AGGIORNAMENTO INCIDENTE #INC-[ANNO]-[NUMERO]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stato:           IN CORSO / WORKAROUND / RISOLTO
Inizio:          [GG/MM/AAAA HH:MM UTC]
Servizi colpiti: [Nome servizio / Numero utenti]
Priorità:        P[1-5]

Situazione attuale:
[2-3 righe sulla situazione e cosa si sta facendo]

Workaround disponibile:
[Sì: [descrivere] / No]

Prossimo aggiornamento: [HH:MM]
Responsabile incidente: [Nome, recapito]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Appendice C: Integrazioni ITIL 4

| Pratica ITIL 4 | Come si collega |
|---|---|
| **Problem Management** | La pratica principale di questo tutorial: gestire cause radice per prevenire incidenti futuri |
| **Knowledge Management (KCS)** | La KEDB e gli articoli KB sono l'output del Problem Management |
| **Continual Improvement** | L'analisi Pareto identifica le priorità; il PDCA misura i progressi |
| **Incident Management** | Fornisce i dati di input per il Problem Management (ticket, trend, pattern) |
| **Change Enablement** | Ogni soluzione permanente richiede un RFC; il Problem Management alimenta il Change process |
| **Service Level Management** | Ogni incidente prevenuto migliora le SLA; il PM quantifica l'impatto |

---

## Riferimenti

- `11-troubleshooting-generale.md` — Documento sorgente (sezioni 12-16)
- `tutorial_ops07_ch1b_incident_management_lab.md` — Incident Management (prerequisito)
- `tutorial_ops11_ch1a_methodology_network_lab.md` — Metodologia base troubleshooting
- `tutorial_ops11_ch1b_performance_auth_storage_lab.md` — Tutorial precedente in questa serie
- ITIL 4 Foundation: Problem Management Practice
- ITIL 4 Foundation: Knowledge Management Practice
- "Toyota Production System" — Taiichi Ohno (origine dei 5 Whys)
- "The Rational Manager" — Kepner & Tregoe (metodo IS/IS NOT)
- Site Reliability Engineering (Google) — blameless post-mortem culture
