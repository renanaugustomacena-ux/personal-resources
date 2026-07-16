# Tutorial Lab — AI e LLM per Automazione: Ollama, LiteLLM e n8n AI Nodes

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `26-ai-llm-automazione.md`
> **Livello:** intermediate → advanced
> **Tempo stimato:** 3 ore
> **Prerequisiti:** Python 3.11+, Docker, conoscenza base API REST
> **Versioni di riferimento:** Ollama 0.3+, LiteLLM 1.x, Python 3.11+

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Configurare Ollama locale per eseguire LLM senza costi cloud
2. Usare LiteLLM come gateway unificato per diversi provider
3. Costruire classificatori di testo robusti con validazione output
4. Implementare un estrattore di dati strutturati da testo libero
5. Integrare LLM in un workflow n8n tramite HTTP node
6. Applicare tecniche di pseudonimizzazione PII prima di inviare a LLM cloud

---

## Lab Environment Setup

```bash
# 1. Installa Ollama
# Linux/Mac:
curl -fsSL https://ollama.ai/install.sh | sh
# Windows: scarica da https://ollama.ai/download

# 2. Avvia Ollama e scarica modello (una tantum, ~2GB)
ollama serve &
ollama pull phi3:mini   # 3.8B params, eccellente per task strutturati, 4GB RAM
# Alternativa più leggera (2GB RAM):
# ollama pull llama3.2:3b

# 3. Verifica Ollama
curl http://localhost:11434/api/tags  # deve mostrare phi3:mini

# 4. Installa dipendenze Python
pip install litellm pydantic structlog httpx jinja2

# 5. Verifica
python -c "import litellm, pydantic, structlog; print('OK')"
```

---

## Analogia Introduttiva

> **Un LLM in un workflow di automazione è come un impiegato con eccezionale capacità di lettura**:
> sai leggere qualsiasi documento e capire l'intento,
> ma hai bisogno di istruzioni precise (prompt) su cosa fare con quello che hai letto,
> e di un modulo da compilare (JSON schema) per restituire il risultato in modo standard.
>
> Il trucco è trattarlo come un **componente con interfaccia definita**:
> input = testo + prompt preciso, output = JSON validato con Pydantic.
> Se l'output non rispetta lo schema, chiedi di riprovare (self-correction).
>
> **Non fidarti mai dell'output LLM come verità assoluta** — validalo sempre.
> Come un dipendente brillante ma giovane: sa molto ma può sbagliare,
> soprattutto su numeri, date, e dati tecnici specifici.

---

## Architettura Lab

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARCHITETTURA AI LAB                               │
│                                                                       │
│  DATI IN INGRESSO (email, ticket, documenti)                         │
│          │                                                            │
│          ▼                                                            │
│  [Pseudonimizzazione PII]  ← per dati sensibili                      │
│          │                                                            │
│          ▼                                                            │
│  ┌───────────────────────────────────────────────┐                  │
│  │              LiteLLM Gateway                   │                  │
│  │                                               │                  │
│  │  provider="ollama/phi3:mini"   ← locale       │                  │
│  │  provider="gpt-4o-mini"        ← cloud        │                  │
│  │  provider="claude-3-haiku"     ← cloud        │                  │
│  └───────────────────┬───────────────────────────┘                  │
│                      │                                               │
│          ┌───────────┼───────────┐                                   │
│          ▼           ▼           ▼                                   │
│  [Classificatore] [Estrattore] [Generatore]                          │
│          │           │           │                                   │
│          ▼           ▼           ▼                                   │
│  [Validazione Pydantic → routing workflow → azioni]                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART A — Classificatore di Testo

### A1 — Classificatore Robusto con Retry

```python
# ai/classificatore.py
from __future__ import annotations

import json
from enum import Enum
from typing import Literal

import litellm
import structlog
from pydantic import BaseModel, ValidationError

log = structlog.get_logger()

# Usa Ollama locale per zero costo
MODELLO_DEFAULT = "ollama/phi3:mini"
OLLAMA_BASE_URL = "http://localhost:11434"

class CategoriaTicket(Enum):
    SUPPORTO_TECNICO = "supporto_tecnico"
    RICHIESTA_COMMERCIALE = "richiesta_commerciale"
    RECLAMO = "reclamo"
    RICHIESTA_INFO = "richiesta_info"
    SPAM = "spam"

class RisultatoClassificazione(BaseModel):
    categoria: Literal[
        "supporto_tecnico", "richiesta_commerciale", "reclamo", "richiesta_info", "spam"
    ]
    confidenza: Literal["alta", "media", "bassa"]
    motivazione: str
    priorita_suggerita: Literal["urgente", "normale", "bassa"]

PROMPT_CLASSIFICAZIONE = """
Classifica il seguente testo. Rispondi ESCLUSIVAMENTE con JSON valido, nessun altro testo.

Schema risposta (rispetta ESATTAMENTE questi valori):
{
  "categoria": "supporto_tecnico" | "richiesta_commerciale" | "reclamo" | "richiesta_info" | "spam",
  "confidenza": "alta" | "media" | "bassa",
  "motivazione": "stringa breve che spiega la classificazione",
  "priorita_suggerita": "urgente" | "normale" | "bassa"
}

Regole:
- supporto_tecnico: problemi tecnici, bug, "non funziona", errori
- richiesta_commerciale: preventivi, prezzi, acquisti, partnership
- reclamo: insoddisfazione, rimborsi, escalation, lamentele
- richiesta_info: domande generali, informazioni, documentazione
- spam: marketing non richiesto, phishing, messaggi irrilevanti
- urgente: parole come "urgente", "bloccato", "impossibile lavorare", "produzione giù"

Testo da classificare:
{testo}
"""

def classifica_testo(testo: str, modello: str = MODELLO_DEFAULT,
                      max_retry: int = 2) -> RisultatoClassificazione | None:
    """Classifica testo con retry e validazione schema."""
    prompt_corrente = PROMPT_CLASSIFICAZIONE.format(testo=testo)
    ultimo_errore: str | None = None

    for tentativo in range(1, max_retry + 2):
        try:
            risposta = litellm.completion(
                model=modello,
                api_base=OLLAMA_BASE_URL if "ollama" in modello else None,
                messages=[{"role": "user", "content": prompt_corrente}],
                temperature=0,
                max_tokens=200,
            )
            contenuto = risposta.choices[0].message.content or ""
            # Pulisci eventuali markdown code blocks
            contenuto = contenuto.strip()
            if contenuto.startswith("```"):
                parti = contenuto.split("```")
                contenuto = parti[1].lstrip("json").strip()
            dati = json.loads(contenuto)
            risultato = RisultatoClassificazione.model_validate(dati)
            log.info("classificazione_ok",
                     categoria=risultato.categoria,
                     confidenza=risultato.confidenza,
                     tentativo=tentativo)
            return risultato

        except (json.JSONDecodeError, ValidationError) as e:
            ultimo_errore = str(e)
            log.warning("classificazione_retry",
                         tentativo=tentativo, errore=ultimo_errore)
            if tentativo <= max_retry:
                prompt_corrente = (
                    f"La tua risposta precedente era errata: {contenuto}\n"
                    f"Errore: {ultimo_errore}\n\n"
                    + PROMPT_CLASSIFICAZIONE.format(testo=testo)
                )

    log.error("classificazione_fallita", max_retry=max_retry, ultimo_errore=ultimo_errore)
    return None

if __name__ == "__main__":
    import structlog
    structlog.configure()

    test_testi = [
        "Il sistema non si avvia dalla stamattina, siamo bloccati in produzione!",
        "Vorrei avere un preventivo per 50 licenze per la nostra azienda",
        "Ho pagato ma il prodotto non è mai arrivato, voglio un rimborso subito",
        "Compra subito Bitcoin con il 200% di rendimento garantito!!!",
    ]
    for testo in test_testi:
        print(f"\nTesto: {testo[:60]}...")
        risultato = classifica_testo(testo)
        if risultato:
            print(f"→ [{risultato.priorita_suggerita.upper()}] {risultato.categoria} "
                  f"(confidenza: {risultato.confidenza})")
            print(f"   {risultato.motivazione}")
        else:
            print("→ Classificazione fallita")
```

---

## PART B — Estrattore di Dati Strutturati

### B1 — Estrazione con JSON Schema

```python
# ai/estrattore.py
from __future__ import annotations

import json
from decimal import Decimal
from datetime import date
from typing import Any

import litellm
import structlog
from pydantic import BaseModel, EmailStr, field_validator

log = structlog.get_logger()

class OrdineEstratto(BaseModel):
    """Schema per estrazione ordini da email/documento."""
    richiedente_nome: str | None = None
    richiedente_email: str | None = None
    azienda: str | None = None
    prodotti: list[dict] = []
    importo_totale: float | None = None
    valuta: str = "EUR"
    data_consegna_richiesta: str | None = None  # formato YYYY-MM-DD
    urgente: bool = False
    note: str = ""

    @field_validator("data_consegna_richiesta")
    @classmethod
    def valida_data(cls, v: str | None) -> str | None:
        if v is None:
            return None
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            return None  # data non parsabile → None invece di errore

PROMPT_ESTRAZIONE = """
Estrai le informazioni dall'email seguente. Rispondi SOLO con JSON valido.
Se un campo non è presente nel testo, usa null (non inventare valori).

Schema:
{
  "richiedente_nome": "stringa o null",
  "richiedente_email": "email o null",
  "azienda": "stringa o null",
  "prodotti": [
    {"nome": "string", "sku": "string o null", "quantita": numero, "prezzo_unitario": numero o null}
  ],
  "importo_totale": numero o null,
  "valuta": "EUR" (default) | "USD" | "GBP",
  "data_consegna_richiesta": "YYYY-MM-DD o null",
  "urgente": true | false,
  "note": "eventuali note speciali"
}

Email:
{email}
"""

def estrai_ordine_da_email(email_testo: str,
                             modello: str = "ollama/phi3:mini") -> OrdineEstratto | None:
    """Estrae informazioni ordine da email in linguaggio naturale."""
    try:
        risposta = litellm.completion(
            model=modello,
            api_base="http://localhost:11434" if "ollama" in modello else None,
            messages=[{
                "role": "user",
                "content": PROMPT_ESTRAZIONE.format(email=email_testo),
            }],
            temperature=0,
            max_tokens=500,
        )
        contenuto = risposta.choices[0].message.content or ""
        contenuto = contenuto.strip()
        if contenuto.startswith("```"):
            contenuto = contenuto.split("```")[1].lstrip("json").strip()
        dati = json.loads(contenuto)
        ordine = OrdineEstratto.model_validate(dati)
        log.info("estrazione_completata",
                 richiedente=ordine.richiedente_nome,
                 num_prodotti=len(ordine.prodotti),
                 urgente=ordine.urgente)
        return ordine
    except Exception as e:
        log.error("estrazione_fallita", errore=str(e))
        return None

if __name__ == "__main__":
    email_test = """
    Buongiorno,
    
    Sono Mario Rossi di TechCorp SRL (mario.rossi@techcorp.it).
    Avrei bisogno urgentemente di:
    - 5 pezzi di Monitor 4K (MON-4K-27) a €299 l'uno
    - 2 tastiere meccaniche (KEYB-MECH-1) 
    
    Totale stimato: €1700
    
    Avrei bisogno della consegna entro il 2026-02-15.
    
    Grazie mille,
    Mario
    """
    ordine = estrai_ordine_da_email(email_test)
    if ordine:
        print(f"Richiedente: {ordine.richiedente_nome} ({ordine.richiedente_email})")
        print(f"Urgente: {ordine.urgente}")
        print(f"Prodotti: {len(ordine.prodotti)}")
        for p in ordine.prodotti:
            print(f"  - {p.get('nome')} × {p.get('quantita')}")
        print(f"Totale: €{ordine.importo_totale}")
        print(f"Consegna: {ordine.data_consegna_richiesta}")
```

---

## PART C — Pseudonimizzazione PII

### C1 — Anonimizza Prima di Inviare a LLM Cloud

```python
# ai/privacy.py
from __future__ import annotations

import re
import structlog

log = structlog.get_logger()

PATTERN_PII = [
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "EMAIL"),
    (r'\b(\+39|0039)?[0-9]{8,12}\b', "TEL"),
    (r'\b[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]\b', "CF"),
    (r'\b(?:IT)?[0-9]{11}\b', "PIVA"),
    (r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b', "CC"),
]

def pseudonimizza(testo: str) -> tuple[str, dict[str, str]]:
    """
    Sostituisce PII con placeholder. Restituisce (testo_anonimo, mapping_ripristino).
    Il mapping usa placeholder→originale per ripristinare dopo elaborazione.
    """
    mapping: dict[str, str] = {}
    contatore = 0
    testo_anonimo = testo

    for pattern, tipo in PATTERN_PII:
        matches = list(re.finditer(pattern, testo_anonimo, re.IGNORECASE))
        for match in matches:
            valore_originale = match.group(0)
            # Controlla se già presente nel mapping
            key_esistente = next(
                (k for k, v in mapping.items() if v == valore_originale), None
            )
            if key_esistente:
                placeholder = key_esistente
            else:
                placeholder = f"[{tipo}_{contatore}]"
                mapping[placeholder] = valore_originale
                contatore += 1
            testo_anonimo = testo_anonimo.replace(valore_originale, placeholder, 1)

    if contatore > 0:
        log.info("pii_pseudonimizzata", valori_sostituiti=contatore)
    return testo_anonimo, mapping

def ripristina(testo_elaborato: str, mapping: dict[str, str]) -> str:
    """Ripristina i valori originali dopo elaborazione LLM."""
    for placeholder, originale in mapping.items():
        testo_elaborato = testo_elaborato.replace(placeholder, originale)
    return testo_elaborato

def classifica_con_privacy(testo: str, funzione_llm) -> dict:
    """Pipeline: pseudonimizza → LLM → ripristina se necessario."""
    testo_anonimo, mapping = pseudonimizza(testo)
    risultato_llm = funzione_llm(testo_anonimo)
    # Il risultato è classificazione, non riproduzione del testo
    # quindi non serve ripristinare — ma logghiamo il mapping per audit
    log.info("classificazione_privacy_safe",
             pii_trovata=len(mapping) > 0,
             num_pii=len(mapping))
    return risultato_llm

if __name__ == "__main__":
    testo = "Mario Rossi (mario.rossi@azienda.it, +39 333 1234567) chiede supporto urgente"
    anonimo, mapping = pseudonimizza(testo)
    print(f"Originale: {testo}")
    print(f"Anonimo: {anonimo}")
    print(f"Mapping: {mapping}")
    ripristinato = ripristina(anonimo, mapping)
    print(f"Ripristinato: {ripristinato}")
    assert ripristinato == testo, "Ripristino fallito!"
    print("✅ Pseudonimizzazione/ripristino OK")
```

---

## PART D — Integrazione con n8n

### D1 — n8n HTTP Node per Ollama

```
CONFIGURAZIONE n8n HTTP NODE → OLLAMA:

1. Aggiungi nodo "HTTP Request" nel workflow n8n
2. Configurazione:
   Method: POST
   URL: http://ollama:11434/api/generate
   (se n8n e Ollama sono nello stesso Docker network)
   
   Body (JSON):
   {
     "model": "phi3:mini",
     "prompt": "Classifica questo testo in UNA categoria: [supporto|commerciale|reclamo|spam].\nRispondi SOLO con la categoria, nessun altro testo.\n\nTesto: {{$json.body.testo}}",
     "stream": false,
     "options": {"temperature": 0}
   }

3. Il nodo restituisce: {"response": "supporto", "done": true}
   Accedi alla categoria: {{$json.response}}

4. Aggiungi nodo "Switch" per routing basato sulla categoria:
   • "supporto" → crea ticket IT
   • "commerciale" → notifica team vendite
   • "reclamo" → escalation priorità alta

DOCKER NETWORK (importante):
  Se n8n e Ollama sono su host diversi, usa l'IP dell'host Ollama.
  Se nello stesso Docker Compose: usa nome servizio "ollama:11434".
  
  # docker-compose.yml aggiornato per Ollama + n8n:
  services:
    ollama:
      image: ollama/ollama
      volumes:
        - ollama_models:/root/.ollama
      ports:
        - "11434:11434"
    n8n:
      image: n8nio/n8n
      depends_on:
        - ollama
      environment:
        OLLAMA_HOST: http://ollama:11434
```

---

## Esercizi

### Esercizio 1 — Classificatore Multi-Classe (30 min)

Estendi il classificatore per gestire anche `lingua_originale` nel risultato:
```python
class RisultatoClassificazioneV2(BaseModel):
    categoria: str
    confidenza: str
    motivazione: str
    priorita_suggerita: str
    lingua_originale: Literal["it", "en", "de", "fr", "es", "altra"]
```
Testa con email in lingue diverse e verifica il campo lingua.

### Esercizio 2 — Batch Processing con Rate Limit (25 min)

Implementa `classifica_batch(testi, max_richieste_per_minuto=10)` che:
- Classifica una lista di testi usando asyncio
- Rispetta il rate limit (attendi tra le richieste se necessario)
- Restituisce lista di `RisultatoClassificazione | None`
- Logga statistiche: N ok, M falliti, latenza media

### Esercizio 3 — Cost Tracker Integrato (20 min)

Aggiungi tracking costi a `classifica_testo()`:
- Dopo ogni chiamata, leggi `risposta.usage` per input/output tokens
- Implementa `CostMonitorLLM.registra_chiamata()` (vedi documento 26)
- Stampa report: X chiamate, Y token totali, €Z costo totale
- Confronta costo Ollama locale (€0) vs gpt-4o-mini (€0.15/1M token)

---

## Riferimenti

- Ollama models: https://ollama.ai/library
- LiteLLM docs: https://docs.litellm.ai/
- Pydantic v2: https://docs.pydantic.dev/latest/
- n8n HTTP node: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/
- Modulo sorgente: `26-ai-llm-automazione.md`
