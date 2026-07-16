# Tutorial Lab — Testing e Qualità dei Workflow di Automazione

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `06-testing-qualita-automazione.md`
> **Livello:** intermediate
> **Tempo stimato:** 2.5 ore
> **Prerequisiti:** Python 3.11+, pytest, conoscenza base dei pattern di automazione
> **Versioni di riferimento:** pytest 8.x, httpx 0.27+, pytest-asyncio 0.23+

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Strutturare una test suite per workflow di automazione
2. Scrivere unit test per funzioni di trasformazione e validazione dati
3. Usare mock server per testare client HTTP senza dipendenze esterne
4. Implementare contract test per verificare che le API usate rispettino il contratto atteso
5. Creare integration test con dipendenze containerizzate (RabbitMQ, Redis)
6. Costruire quality gate che bloccano deploy in presenza di regression

---

## Lab Environment Setup

```bash
# Crea ambiente isolato
python -m venv venv && source venv/bin/activate  # Linux/Mac
# oppure: venv\Scripts\activate  (Windows)

# Installazione dipendenze testing
pip install pytest pytest-asyncio pytest-cov httpx respx structlog

# Verifica
pytest --version
# pytest 8.x.x

# Struttura directory del lab
mkdir -p tests/{unit,integration,contract,fixtures}
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py
touch tests/contract/__init__.py tests/fixtures/__init__.py
```

---

## Analogia Introduttiva

> **Testare workflow di automazione è come controllare una catena di montaggio**:
> puoi testare ogni singolo robot (unit test),
> testare la collaborazione tra due robot consecutivi (integration test),
> e testare che il prodotto finito rispetti le specifiche del cliente (contract test).
>
> Il **mock server** è un "robot simulato" che risponde esattamente come l'originale
> ma senza i costi e le dipendenze di rete — perfetto per test rapidi e deterministici.
>
> Il **quality gate** è il collaudatore finale:
> se il prodotto non passa l'ispezione, non lascia la fabbrica.
> In CI/CD questo significa che il deploy viene bloccato automaticamente
> se anche un solo test fallisce.

---

## Architettura della Test Suite

```
tests/
├── unit/
│   ├── test_trasformazioni.py    ← test funzioni pure
│   ├── test_validazione.py       ← test validazione input
│   └── test_calcoli.py           ← test logica business
├── integration/
│   ├── test_webhook_server.py    ← server HTTP locale
│   └── test_queue_consumer.py    ← RabbitMQ containerizzato
├── contract/
│   ├── test_api_contratto.py     ← verifica contratti API
│   └── pacts/                    ← file pact (se usi Pact)
├── fixtures/
│   ├── conftest.py               ← fixture condivise pytest
│   ├── payloads.py               ← dati di test realistici
│   └── schemas.py                ← JSON Schema per validazione
└── conftest.py                   ← fixture globali + setup
```

---

## PART A — Unit Test

### A1 — Test Funzioni di Trasformazione

```python
# tests/unit/test_trasformazioni.py
from __future__ import annotations

import pytest
from decimal import Decimal
from datetime import date

# Funzioni da testare (da automazione/trasformazioni.py)
from automazione.trasformazioni import (
    normalizza_email,
    formatta_importo,
    parse_data_it,
    sanitizza_payload_ordine,
)


class TestNormalizzaEmail:
    def test_lowercase(self):
        assert normalizza_email("MARIO@AZIENDA.IT") == "mario@azienda.it"

    def test_rimuove_spazi(self):
        assert normalizza_email("  mario@azienda.it  ") == "mario@azienda.it"

    def test_email_valida_invariata(self):
        email = "mario.rossi@sotto.dominio.it"
        assert normalizza_email(email) == email

    def test_email_vuota_raise(self):
        with pytest.raises(ValueError, match="Email non può essere vuota"):
            normalizza_email("")

    def test_email_senza_at_raise(self):
        with pytest.raises(ValueError, match="Email non valida"):
            normalizza_email("mario.rossi.azienda.it")

    @pytest.mark.parametrize("email,atteso", [
        ("MARIO@TEST.COM", "mario@test.com"),
        ("  TEST@PROVA.IT  ", "test@prova.it"),
        ("user+tag@domain.org", "user+tag@domain.org"),
    ])
    def test_parametrizzato(self, email: str, atteso: str):
        assert normalizza_email(email) == atteso


class TestFormattaImporto:
    def test_due_decimali(self):
        assert formatta_importo(Decimal("100")) == "100.00"

    def test_arrotondamento_corretto(self):
        assert formatta_importo(Decimal("10.005")) == "10.01"

    def test_importo_negativo(self):
        assert formatta_importo(Decimal("-50.5")) == "-50.50"

    def test_zero(self):
        assert formatta_importo(Decimal("0")) == "0.00"

    def test_importo_grande(self):
        assert formatta_importo(Decimal("1234567.89")) == "1234567.89"

    def test_tipo_sbagliato_raise(self):
        with pytest.raises(TypeError):
            formatta_importo(100.5)  # float invece di Decimal


class TestParseDataIt:
    def test_formato_slash(self):
        assert parse_data_it("15/01/2026") == date(2026, 1, 15)

    def test_formato_iso(self):
        assert parse_data_it("2026-01-15") == date(2026, 1, 15)

    def test_formato_punto(self):
        assert parse_data_it("15.01.2026") == date(2026, 1, 15)

    def test_data_invalida_raise(self):
        with pytest.raises(ValueError, match="Formato data non riconosciuto"):
            parse_data_it("32/13/2026")

    def test_stringa_vuota_raise(self):
        with pytest.raises(ValueError):
            parse_data_it("")


class TestSanitizzaPayloadOrdine:
    def test_payload_valido_invariato(self):
        payload = {
            "ordine_id": "ORD-001",
            "importo": "149.90",
            "cliente_email": "mario@test.it",
        }
        risultato = sanitizza_payload_ordine(payload)
        assert risultato["ordine_id"] == "ORD-001"
        assert risultato["importo"] == Decimal("149.90")
        assert risultato["cliente_email"] == "mario@test.it"

    def test_campi_obbligatori_mancanti(self):
        with pytest.raises(ValueError, match="Campo obbligatorio mancante: ordine_id"):
            sanitizza_payload_ordine({"importo": "100"})

    def test_importo_non_numerico_raise(self):
        with pytest.raises(ValueError, match="importo deve essere numerico"):
            sanitizza_payload_ordine({"ordine_id": "ORD-001", "importo": "abc"})

    def test_campi_extra_rimossi(self):
        payload = {
            "ordine_id": "ORD-001",
            "importo": "10.00",
            "cliente_email": "t@t.it",
            "campo_inaspettato": "ignorami",
        }
        risultato = sanitizza_payload_ordine(payload)
        assert "campo_inaspettato" not in risultato
```

---

## PART B — Mock Server per HTTP Client

### B1 — Usare respx per Mock HTTP

```python
# tests/unit/test_api_client.py
from __future__ import annotations

import pytest
import httpx
import respx
from decimal import Decimal

# Il client da testare
from automazione.api_client import ClientOrdini, OrdineNonTrovatoError


@pytest.fixture
def mock_api():
    """Mock del server API ordini per tutti i test del modulo."""
    with respx.mock(base_url="https://api.esempio.com") as mock:
        yield mock


class TestClientOrdini:
    def test_get_ordine_ok(self, mock_api):
        mock_api.get("/ordini/ORD-001").mock(return_value=httpx.Response(
            200,
            json={
                "id": "ORD-001",
                "importo": "149.90",
                "stato": "confermato",
                "cliente": "Mario Rossi",
            },
        ))
        client = ClientOrdini(base_url="https://api.esempio.com", api_key="test-key")
        ordine = client.get_ordine("ORD-001")
        assert ordine["id"] == "ORD-001"
        assert Decimal(ordine["importo"]) == Decimal("149.90")

    def test_get_ordine_non_trovato(self, mock_api):
        mock_api.get("/ordini/ORD-999").mock(return_value=httpx.Response(
            404,
            json={"error": "Ordine non trovato"},
        ))
        client = ClientOrdini(base_url="https://api.esempio.com", api_key="test-key")
        with pytest.raises(OrdineNonTrovatoError, match="ORD-999"):
            client.get_ordine("ORD-999")

    def test_get_ordine_server_error_raise(self, mock_api):
        mock_api.get("/ordini/ORD-001").mock(return_value=httpx.Response(500))
        client = ClientOrdini(base_url="https://api.esempio.com", api_key="test-key")
        with pytest.raises(httpx.HTTPStatusError):
            client.get_ordine("ORD-001")

    def test_crea_ordine_invia_payload_corretto(self, mock_api):
        mock_api.post("/ordini").mock(return_value=httpx.Response(
            201,
            json={"id": "ORD-NEW", "stato": "pending"},
        ))
        client = ClientOrdini(base_url="https://api.esempio.com", api_key="test-key")
        payload = {"importo": "99.90", "prodotto": "Mouse USB", "cliente_email": "a@b.it"}
        risposta = client.crea_ordine(payload)
        # Verifica che il payload sia stato inviato
        request_inviata = mock_api.calls.last.request
        import json
        body_inviato = json.loads(request_inviata.content)
        assert body_inviato["importo"] == "99.90"
        assert risposta["id"] == "ORD-NEW"

    def test_timeout_gestito(self, mock_api):
        mock_api.get("/ordini/ORD-001").mock(side_effect=httpx.ConnectTimeout)
        client = ClientOrdini(base_url="https://api.esempio.com", api_key="test-key",
                               timeout=5.0)
        with pytest.raises(httpx.TimeoutException):
            client.get_ordine("ORD-001")
```

---

## PART C — Contract Test

### C1 — Verifica Contratto API Esterna

```python
# tests/contract/test_api_contratto.py
from __future__ import annotations

import jsonschema
import pytest
import httpx

# Schema JSON del contratto atteso per l'API ordini
SCHEMA_ORDINE = {
    "type": "object",
    "required": ["id", "importo", "stato", "created_at"],
    "properties": {
        "id": {"type": "string", "pattern": "^ORD-[0-9]+$"},
        "importo": {"type": "string"},
        "stato": {
            "type": "string",
            "enum": ["pending", "confermato", "spedito", "consegnato", "annullato"],
        },
        "created_at": {"type": "string", "format": "date-time"},
        "cliente": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "email": {"type": "string", "format": "email"},
            },
        },
    },
    "additionalProperties": True,
}

SCHEMA_ERRORE = {
    "type": "object",
    "required": ["error"],
    "properties": {
        "error": {"type": "string"},
        "code": {"type": "string"},
    },
}


@pytest.mark.contract
class TestContrattoAPIOrdinI:
    """
    Contract test: verifica che l'API esterna rispetti il contratto atteso.
    NOTA: questi test richiedono rete (marker: contract).
    In CI eseguire solo con flag specifico: pytest -m contract
    """
    BASE_URL = "https://jsonplaceholder.typicode.com"

    def test_schema_risposta_post(self):
        """Verifica che POST /todos rispetti lo schema atteso."""
        SCHEMA_TODO = {
            "type": "object",
            "required": ["id", "title", "completed", "userId"],
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "completed": {"type": "boolean"},
                "userId": {"type": "integer"},
            },
        }
        with httpx.Client(timeout=10) as client:
            resp = client.post(f"{self.BASE_URL}/todos",
                               json={"title": "test task", "completed": False, "userId": 1})
            assert resp.status_code == 201, f"Atteso 201, ricevuto {resp.status_code}"
            jsonschema.validate(instance=resp.json(), schema=SCHEMA_TODO)

    def test_campo_id_sempre_presente(self):
        """Verifica che il campo 'id' sia sempre presente e intero."""
        with httpx.Client(timeout=10) as client:
            for todo_id in range(1, 4):
                resp = client.get(f"{self.BASE_URL}/todos/{todo_id}")
                assert resp.status_code == 200
                data = resp.json()
                assert "id" in data, f"Campo 'id' mancante per todo {todo_id}"
                assert isinstance(data["id"], int)

    def test_content_type_json(self):
        """Verifica che le risposte abbiano Content-Type application/json."""
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{self.BASE_URL}/todos/1")
            assert "application/json" in resp.headers.get("content-type", "")


def valida_risposta(response_json: dict, schema: dict, nome_test: str) -> None:
    """Helper per validazione schema con messaggio di errore chiaro."""
    try:
        jsonschema.validate(instance=response_json, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"[{nome_test}] Contratto violato: {e.message}\nPath: {list(e.path)}")
```

---

## PART D — Quality Gate

### D1 — Script Quality Gate per CI/CD

```python
# scripts/quality_gate.py
"""
Quality gate: esegue test suite e blocca il deploy se soglie non rispettate.
Uso: python scripts/quality_gate.py
Exit code 0 = OK, 1 = BLOCCATO
"""
from __future__ import annotations

import subprocess
import sys
import json
from dataclasses import dataclass
from pathlib import Path

@dataclass
class SoglieQualita:
    copertura_minima: float = 80.0
    max_test_falliti: int = 0
    max_warning_security: int = 0

def esegui_test_con_copertura() -> tuple[int, float]:
    """Esegue pytest con coverage. Restituisce (num_falliti, copertura_pct)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "--tb=short",
         "--json-report", "--json-report-file=reports/test_results.json",
         "--cov=automazione",
         "--cov-report=json:reports/coverage.json",
         "-m", "not contract",  # escludi contract test in CI standard
         "tests/"],
        capture_output=True, text=True,
    )
    num_falliti = 0
    copertura = 0.0
    cov_path = Path("reports/coverage.json")
    if cov_path.exists():
        dati_cov = json.loads(cov_path.read_text())
        copertura = dati_cov["totals"]["percent_covered"]
    report_path = Path("reports/test_results.json")
    if report_path.exists():
        dati_test = json.loads(report_path.read_text())
        num_falliti = dati_test["summary"].get("failed", 0)
    return num_falliti, copertura

def controlla_sicurezza() -> int:
    """Esegue bandit per security check. Restituisce numero di warning HIGH/MEDIUM."""
    result = subprocess.run(
        ["bandit", "-r", "automazione/", "-f", "json", "-o", "reports/security.json",
         "-l"],
        capture_output=True, text=True,
    )
    sec_path = Path("reports/security.json")
    if not sec_path.exists():
        return 0
    dati = json.loads(sec_path.read_text())
    high_medium = sum(
        1 for r in dati.get("results", [])
        if r["issue_severity"] in ("HIGH", "MEDIUM")
    )
    return high_medium

def esegui_quality_gate(soglie: SoglieQualita = SoglieQualita()) -> bool:
    """Restituisce True se la qualità è accettabile, False se il deploy va bloccato."""
    Path("reports").mkdir(exist_ok=True)
    print("=== QUALITY GATE ===")
    blocchi = []

    print("\n[1/3] Esecuzione test suite...")
    num_falliti, copertura = esegui_test_con_copertura()
    print(f"  Test falliti: {num_falliti} (soglia: max {soglie.max_test_falliti})")
    print(f"  Copertura: {copertura:.1f}% (soglia: min {soglie.copertura_minima}%)")

    if num_falliti > soglie.max_test_falliti:
        blocchi.append(f"Test falliti: {num_falliti} > {soglie.max_test_falliti}")
    if copertura < soglie.copertura_minima:
        blocchi.append(f"Copertura: {copertura:.1f}% < {soglie.copertura_minima}%")

    print("\n[2/3] Security scan...")
    try:
        warning_security = controlla_sicurezza()
        print(f"  Warning HIGH/MEDIUM: {warning_security} (soglia: max {soglie.max_warning_security})")
        if warning_security > soglie.max_warning_security:
            blocchi.append(f"Security warning: {warning_security} > {soglie.max_warning_security}")
    except FileNotFoundError:
        print("  bandit non installato — skip security scan")

    print("\n=== RISULTATO ===")
    if blocchi:
        print("🚫 QUALITY GATE BLOCCATO:")
        for b in blocchi:
            print(f"   - {b}")
        return False
    print("✅ QUALITY GATE SUPERATO — deploy autorizzato")
    return True

if __name__ == "__main__":
    ok = esegui_quality_gate()
    sys.exit(0 if ok else 1)
```

### D2 — Configurazione pytest.ini e Marker

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

markers =
    unit: Test unitari veloci (no I/O esterno)
    integration: Test di integrazione (richiede Docker)
    contract: Contract test (richiede rete)
    slow: Test lenti (>5 secondi)

addopts =
    --strict-markers
    -v
    --tb=short

filterwarnings =
    error
    ignore::DeprecationWarning:httpx.*
```

---

## Esercizi

### Esercizio 1 — TDD: CircuitBreaker (30 min)

Implementa con TDD (test prima, codice dopo) una classe `CircuitBreaker` con:
- Stato CLOSED (funziona), OPEN (blocca), HALF_OPEN (test)
- Scrive i test prima in `tests/unit/test_circuit_breaker.py`
- Poi implementa la classe in `automazione/circuit_breaker.py` fino a far passare tutti i test

### Esercizio 2 — Mock Webhook Server (25 min)

Implementa un fixture pytest che avvia un server Flask minimale in un thread:
```python
@pytest.fixture(scope="module")
def webhook_server():
    """Server webhook locale per integration test."""
    # TODO: avvia Flask in thread
    # TODO: yield URL
    # TODO: teardown: ferma il server
```
Poi scrivi un test che:
1. Configura il tuo client webhook verso il server locale
2. Invia una richiesta POST
3. Verifica che il server abbia ricevuto i dati corretti

### Esercizio 3 — Coverage Report (10 min)

Esegui `pytest --cov=automazione --cov-report=html tests/unit/` e analizza il report HTML:
- Quali funzioni hanno copertura 0%?
- Ci sono branch non coperti (color verde chiaro nel report)?
- Aggiungi almeno 2 test per portare la copertura totale sopra 80%

---

## Riferimenti

- pytest docs: https://docs.pytest.org/
- respx (mock HTTP): https://lundberg.github.io/respx/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- jsonschema: https://python-jsonschema.readthedocs.io/
- bandit (security): https://bandit.readthedocs.io/
- Modulo sorgente: `06-testing-qualita-automazione.md`
