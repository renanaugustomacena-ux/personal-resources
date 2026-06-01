---
corso: "Automazioni e Flussi di Lavoro"
fase: "4 — Qualità"
modulo: 6
titolo: "Testing e Qualità dell'Automazione"
versione: "1.0"
livello: "Avanzato"
prerequisiti:
  - "Moduli 01-04"
  - "pytest basics, mock concepts"
obiettivi:
  - "Scrivere unit test per workflow scriptati con pytest e framework equivalenti"
  - "Implementare integration test per API con mock dei servizi esterni"
  - "Progettare end-to-end test per workflow low-code con verifica stato finale"
  - "Applicare contract testing (Pact, OpenAPI validation) per prevenire breaking change"
  - "Organizzare test pyramid bilanciata: molte unit, poche e2e, copertura 80%+"
tag: [testing, unit-test, integration-test, e2e, contract-testing, qualità, mock]
---

# Testing e Qualita dell'Automazione -- Guida Completa

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 5 — Governance · Modulo 06
> **Prerequisiti:** Moduli 01-04; pytest basics, mock concepts.
> **Obiettivi:** unit test workflow scriptati, integration test API, end-to-end test workflow low-code, mock external services, contract testing.
> **Tempo:** lettura 60-90 min · lab 240 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Scrivere unit test per workflow scriptati con pytest e framework equivalenti
> 2. Implementare integration test per API con mock dei servizi esterni
> 3. Progettare end-to-end test per workflow low-code con verifica stato finale
> 4. Applicare contract testing (Pact, OpenAPI validation) per prevenire breaking change
> 5. Organizzare test pyramid bilanciata: molte unit, poche e2e, copertura 80%+
>
> **Prerequisiti:** [Modulo 01](01-fondamenti-automazione.md), [Modulo 02](02-piattaforme-low-code.md), [Modulo 03](03-scripting-automazione.md), [Modulo 04](04-integrazione-api.md) -- pytest basics, mock concepts
> **Tempo stimato:** 5-6 ore · **Livello:** Avanzato

## Idee guida

1. **Test pyramid: tante unit, poche e2e.** Unit test cattura 80% bug a 5% del costo.
2. **Mock external services in CI.** Hitting reale Stripe in CI = bill + flakiness.
3. **Contract testing previene "ha cambiato API senza dirmelo".** Pact, OpenAPI validation.
4. **Low-code testing e dolore.** Senza codice, niente unit test. Solo e2e via UI automation.
5. **Idempotency test deve esistere.** "Eseguo 2 volte stesso input, verifico nessun side effect duplicato."

---

## Indice

1. [Panoramica](#panoramica)
2. [Testing di Workflow](#testing-di-workflow)
   - [Unit Test per Automazioni](#unit-test-per-automazioni)
   - [Integration Test](#integration-test)
   - [End-to-End Test](#end-to-end-test)
3. [Testing Piattaforme Low-Code](#testing-piattaforme-low-code)
   - [n8n Testing](#n8n-testing)
   - [Make Testing](#make-testing)
   - [Power Automate Testing](#power-automate-testing)
4. [Validazione Dati](#validazione-dati)
5. [Monitoraggio Automazioni in Produzione](#monitoraggio-automazioni-in-produzione)
   - [Metriche Chiave](#metriche-chiave)
   - [Alerting](#alerting)
   - [Dashboard](#dashboard)
   - [Logging](#logging)
6. [Gestione Errori](#gestione-errori)
   - [Strategie di Retry](#strategie-di-retry)
   - [Notifica Errori](#notifica-errori)
   - [Recovery Procedures](#recovery-procedures)
7. [Documentazione Automazioni](#documentazione-automazioni)
8. [Best Practices](#best-practices)

---

## Panoramica

Il testing delle automazioni rappresenta una disciplina fondamentale che troppo spesso viene sottovalutata. Quando un processo manuale contiene un errore, l'impatto e limitato: un singolo operatore commette un singolo errore su un singolo record. Quando un'automazione contiene un errore, l'impatto si moltiplica istantaneamente: migliaia di record possono essere corrotti, centinaia di email inviate erroneamente, decine di sistemi possono ricevere dati sbagliati, il tutto nel giro di pochi secondi. La velocita che rende le automazioni potenti e la stessa velocita che rende i loro errori devastanti.

Il costo di un bug in un'automazione e esponenzialmente superiore rispetto al costo dello stesso bug in un processo manuale. Un errore nel calcolo di una fattura, scoperto immediatamente da un operatore umano, diventa un problema di lieve entita. Lo stesso errore in un'automazione che processa 10.000 fatture al giorno genera un disastro finanziario e reputazionale che puo richiedere settimane di lavoro correttivo. Per questo motivo, ogni minuto investito nel testing e nel quality assurance delle automazioni produce un ritorno moltiplicato.

### La Piramide del Testing per le Automazioni

La piramide del testing tradizionale si applica con forza ancora maggiore nel contesto dell'automazione dei workflow:

```
        /\
       /  \        End-to-End Test
      / E2E\       (pochi, costosi, lenti, ma essenziali)
     /------\
    /        \     Integration Test
   / Integraz.\    (numero moderato, verificano le connessioni)
  /------------\
 /              \  Unit Test
/ Unit Test      \ (molti, veloci, economici, base solida)
------------------
```

Alla base troviamo gli **unit test**: numerosi, rapidi da eseguire e da scrivere, verificano che ogni singola funzione o trasformazione si comporti correttamente in isolamento. Al livello intermedio si collocano gli **integration test**: verificano che i componenti dell'automazione comunichino correttamente tra loro e con i servizi esterni. Al vertice gli **end-to-end test**: pochi ma cruciali, simulano l'intero percorso del workflow dall'inizio alla fine, validando che il risultato finale sia quello atteso.

Questa guida copre in modo approfondito tutte e tre le tipologie, insieme alle strategie di monitoraggio, gestione degli errori e documentazione che garantiscono la qualita continua delle automazioni in produzione.

---

## Testing di Workflow

### Unit Test per Automazioni

Gli unit test costituiscono il fondamento della strategia di quality assurance. Nel contesto delle automazioni, un unit test verifica il comportamento di una singola funzione, una singola trasformazione dati, un singolo componente logico del workflow, in completo isolamento rispetto a sistemi esterni.

#### Testing delle Funzioni di Trasformazione

Ogni automazione include funzioni che trasformano dati da un formato all'altro. Queste funzioni devono essere testate in modo rigoroso, coprendo sia i casi normali sia quelli limite.

```python
# automation/transforms.py

from datetime import datetime
from typing import Optional

def normalizza_nome_cliente(nome: str) -> str:
    """Normalizza il nome del cliente rimuovendo spazi e capitalizzando."""
    if not nome or not nome.strip():
        raise ValueError("Il nome del cliente non puo essere vuoto")
    parti = nome.strip().split()
    return " ".join(parte.capitalize() for parte in parti)

def calcola_sconto(totale: float, codice_cliente: str) -> float:
    """Calcola lo sconto in base al tipo di cliente."""
    sconti = {
        "GOLD": 0.15,
        "SILVER": 0.10,
        "BRONZE": 0.05,
    }
    categoria = codice_cliente[:4].upper() if len(codice_cliente) >= 4 else ""
    percentuale = sconti.get(categoria, 0.0)
    return round(totale * percentuale, 2)

def formatta_data_fattura(data: datetime, locale: str = "it") -> str:
    """Formatta la data per la fattura secondo il locale specificato."""
    if locale == "it":
        return data.strftime("%d/%m/%Y")
    elif locale == "en":
        return data.strftime("%m/%d/%Y")
    elif locale == "iso":
        return data.strftime("%Y-%m-%d")
    else:
        raise ValueError(f"Locale non supportato: {locale}")
```

```python
# tests/test_transforms.py

import pytest
from datetime import datetime
from automation.transforms import (
    normalizza_nome_cliente,
    calcola_sconto,
    formatta_data_fattura,
)

class TestNormalizzaNomeCliente:
    def test_nome_semplice(self):
        assert normalizza_nome_cliente("mario rossi") == "Mario Rossi"

    def test_nome_con_spazi_extra(self):
        assert normalizza_nome_cliente("  mario   rossi  ") == "Mario Rossi"

    def test_nome_gia_corretto(self):
        assert normalizza_nome_cliente("Mario Rossi") == "Mario Rossi"

    def test_nome_tutto_maiuscolo(self):
        assert normalizza_nome_cliente("MARIO ROSSI") == "Mario Rossi"

    def test_nome_vuoto_solleva_errore(self):
        with pytest.raises(ValueError, match="non puo essere vuoto"):
            normalizza_nome_cliente("")

    def test_nome_solo_spazi_solleva_errore(self):
        with pytest.raises(ValueError):
            normalizza_nome_cliente("   ")

class TestCalcolaSconto:
    def test_cliente_gold(self):
        assert calcola_sconto(100.0, "GOLD-001") == 15.0

    def test_cliente_silver(self):
        assert calcola_sconto(200.0, "SILV-042") == 20.0

    def test_cliente_bronze(self):
        assert calcola_sconto(50.0, "BRON-100") == 2.5

    def test_cliente_senza_sconto(self):
        assert calcola_sconto(100.0, "STANDARD-001") == 0.0

    def test_codice_corto(self):
        assert calcola_sconto(100.0, "AB") == 0.0

    def test_arrotondamento(self):
        assert calcola_sconto(33.33, "GOLD-001") == 5.0

class TestFormattaDataFattura:
    def test_formato_italiano(self):
        data = datetime(2026, 3, 15)
        assert formatta_data_fattura(data, "it") == "15/03/2026"

    def test_formato_inglese(self):
        data = datetime(2026, 3, 15)
        assert formatta_data_fattura(data, "en") == "03/15/2026"

    def test_formato_iso(self):
        data = datetime(2026, 3, 15)
        assert formatta_data_fattura(data, "iso") == "2026-03-15"

    def test_locale_non_supportato(self):
        with pytest.raises(ValueError, match="Locale non supportato"):
            formatta_data_fattura(datetime.now(), "fr")
```

#### Mocking delle API Esterne

Le automazioni dipendono quasi sempre da API esterne. Gli unit test devono isolare queste dipendenze attraverso il mocking, in modo da testare la logica senza effettuare chiamate reali.

```python
# automation/crm_sync.py

import requests
from typing import Dict, List

class CRMClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def ottieni_contatto(self, email: str) -> Dict:
        risposta = requests.get(
            f"{self.base_url}/contacts",
            params={"email": email},
            headers=self.headers,
            timeout=30
        )
        risposta.raise_for_status()
        contatti = risposta.json().get("data", [])
        if not contatti:
            raise ValueError(f"Contatto non trovato: {email}")
        return contatti[0]

    def aggiorna_contatto(self, contact_id: str, dati: Dict) -> Dict:
        risposta = requests.patch(
            f"{self.base_url}/contacts/{contact_id}",
            json=dati,
            headers=self.headers,
            timeout=30
        )
        risposta.raise_for_status()
        return risposta.json()
```

```python
# tests/test_crm_sync.py

import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError, Timeout
from automation.crm_sync import CRMClient

@pytest.fixture
def client():
    return CRMClient("https://api.crm.example.com", "test-api-key")

class TestOttieniContatto:
    @patch("automation.crm_sync.requests.get")
    def test_contatto_trovato(self, mock_get, client):
        mock_risposta = MagicMock()
        mock_risposta.json.return_value = {
            "data": [{"id": "123", "email": "mario@example.com", "nome": "Mario"}]
        }
        mock_risposta.raise_for_status.return_value = None
        mock_get.return_value = mock_risposta

        risultato = client.ottieni_contatto("mario@example.com")

        assert risultato["id"] == "123"
        assert risultato["email"] == "mario@example.com"
        mock_get.assert_called_once_with(
            "https://api.crm.example.com/contacts",
            params={"email": "mario@example.com"},
            headers={"Authorization": "Bearer test-api-key"},
            timeout=30
        )

    @patch("automation.crm_sync.requests.get")
    def test_contatto_non_trovato(self, mock_get, client):
        mock_risposta = MagicMock()
        mock_risposta.json.return_value = {"data": []}
        mock_risposta.raise_for_status.return_value = None
        mock_get.return_value = mock_risposta

        with pytest.raises(ValueError, match="Contatto non trovato"):
            client.ottieni_contatto("inesistente@example.com")

    @patch("automation.crm_sync.requests.get")
    def test_errore_http(self, mock_get, client):
        mock_risposta = MagicMock()
        mock_risposta.raise_for_status.side_effect = HTTPError("500 Server Error")
        mock_get.return_value = mock_risposta

        with pytest.raises(HTTPError):
            client.ottieni_contatto("mario@example.com")

    @patch("automation.crm_sync.requests.get")
    def test_timeout(self, mock_get, client):
        mock_get.side_effect = Timeout("Connection timed out")

        with pytest.raises(Timeout):
            client.ottieni_contatto("mario@example.com")
```

Per un mocking piu sofisticato delle chiamate HTTP, la libreria `responses` offre un'interfaccia dichiarativa particolarmente elegante:

```python
# tests/test_crm_sync_responses.py

import responses
import pytest
from automation.crm_sync import CRMClient

@pytest.fixture
def client():
    return CRMClient("https://api.crm.example.com", "test-api-key")

@responses.activate
def test_ottieni_contatto_con_responses(client):
    responses.add(
        responses.GET,
        "https://api.crm.example.com/contacts",
        json={"data": [{"id": "456", "email": "luigi@example.com"}]},
        status=200
    )

    risultato = client.ottieni_contatto("luigi@example.com")
    assert risultato["id"] == "456"

@responses.activate
def test_aggiorna_contatto_con_responses(client):
    responses.add(
        responses.PATCH,
        "https://api.crm.example.com/contacts/456",
        json={"id": "456", "nome": "Luigi Verdi"},
        status=200
    )

    risultato = client.aggiorna_contatto("456", {"nome": "Luigi Verdi"})
    assert risultato["nome"] == "Luigi Verdi"
```

#### Testing della Gestione Errori

Un aspetto critico degli unit test per le automazioni e verificare che i percorsi di errore siano gestiti correttamente. Un'automazione che si blocca silenziosamente o che propaga eccezioni non gestite puo causare danni significativi.

```python
# tests/test_error_handling.py

import pytest
from unittest.mock import patch, MagicMock

def processa_ordine(ordine: dict) -> dict:
    """Processa un ordine con gestione errori robusta."""
    errori = []

    if "id" not in ordine:
        errori.append("ID ordine mancante")
    if "importo" not in ordine or ordine.get("importo", 0) <= 0:
        errori.append("Importo non valido")
    if "email_cliente" not in ordine:
        errori.append("Email cliente mancante")

    if errori:
        return {"successo": False, "errori": errori, "ordine": ordine}

    return {
        "successo": True,
        "ordine_processato": {
            "id": ordine["id"],
            "importo_netto": round(ordine["importo"] * 0.78, 2),
            "email_conferma": ordine["email_cliente"],
        }
    }

class TestProcessaOrdine:
    def test_ordine_valido(self):
        ordine = {"id": "ORD-001", "importo": 100.0, "email_cliente": "a@b.com"}
        risultato = processa_ordine(ordine)
        assert risultato["successo"] is True
        assert risultato["ordine_processato"]["importo_netto"] == 78.0

    def test_ordine_senza_id(self):
        ordine = {"importo": 100.0, "email_cliente": "a@b.com"}
        risultato = processa_ordine(ordine)
        assert risultato["successo"] is False
        assert "ID ordine mancante" in risultato["errori"]

    def test_ordine_importo_negativo(self):
        ordine = {"id": "ORD-002", "importo": -50.0, "email_cliente": "a@b.com"}
        risultato = processa_ordine(ordine)
        assert risultato["successo"] is False
        assert "Importo non valido" in risultato["errori"]

    def test_ordine_multipli_errori(self):
        ordine = {}
        risultato = processa_ordine(ordine)
        assert risultato["successo"] is False
        assert len(risultato["errori"]) == 3
```

---

### Integration Test

Gli integration test verificano che i componenti dell'automazione funzionino correttamente quando sono connessi tra loro. A differenza degli unit test, questi test coinvolgono sistemi reali (o simulazioni realistiche) e verificano la comunicazione effettiva tra componenti.

#### Testing della Connettivita API

```python
# tests/integration/test_api_connectivity.py

import pytest
import requests
import os

# Questi test richiedono variabili d'ambiente configurate
# Eseguire solo in ambiente di staging/test

@pytest.mark.integration
class TestConnettivitaAPI:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.crm_url = os.environ.get("TEST_CRM_URL", "https://sandbox.crm.example.com")
        self.crm_key = os.environ.get("TEST_CRM_API_KEY")
        if not self.crm_key:
            pytest.skip("TEST_CRM_API_KEY non configurata")

    def test_autenticazione_crm(self):
        risposta = requests.get(
            f"{self.crm_url}/api/v1/me",
            headers={"Authorization": f"Bearer {self.crm_key}"},
            timeout=10
        )
        assert risposta.status_code == 200
        dati = risposta.json()
        assert "id" in dati

    def test_permessi_lettura_contatti(self):
        risposta = requests.get(
            f"{self.crm_url}/api/v1/contacts",
            headers={"Authorization": f"Bearer {self.crm_key}"},
            params={"limit": 1},
            timeout=10
        )
        assert risposta.status_code == 200

    def test_permessi_scrittura_contatti(self):
        # Crea un contatto di test
        contatto_test = {
            "email": "integration-test@example.com",
            "nome": "Test Integration",
            "tags": ["test-automatico"]
        }
        risposta = requests.post(
            f"{self.crm_url}/api/v1/contacts",
            headers={"Authorization": f"Bearer {self.crm_key}"},
            json=contatto_test,
            timeout=10
        )
        assert risposta.status_code in [200, 201]

        # Cleanup: elimina il contatto creato
        contact_id = risposta.json()["id"]
        requests.delete(
            f"{self.crm_url}/api/v1/contacts/{contact_id}",
            headers={"Authorization": f"Bearer {self.crm_key}"},
            timeout=10
        )
```

#### Testing dei Webhook Receiver

I webhook sono un componente critico di molte automazioni. E fondamentale verificare che il receiver gestisca correttamente i payload in arrivo.

```python
# tests/integration/test_webhook_receiver.py

import pytest
import requests
import json
import hmac
import hashlib

@pytest.mark.integration
class TestWebhookReceiver:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.webhook_url = "http://localhost:5000/webhooks/ordini"
        self.webhook_secret = "test-secret-key"

    def _firma_payload(self, payload: str) -> str:
        return hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    def test_webhook_payload_valido(self):
        payload = json.dumps({
            "evento": "ordine.creato",
            "dati": {"id": "ORD-TEST-001", "importo": 99.99}
        })
        firma = self._firma_payload(payload)

        risposta = requests.post(
            self.webhook_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": firma
            },
            timeout=10
        )
        assert risposta.status_code == 200
        assert risposta.json()["accettato"] is True

    def test_webhook_firma_non_valida(self):
        payload = json.dumps({"evento": "ordine.creato", "dati": {}})

        risposta = requests.post(
            self.webhook_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": "firma-sbagliata"
            },
            timeout=10
        )
        assert risposta.status_code == 401

    def test_webhook_payload_malformato(self):
        risposta = requests.post(
            self.webhook_url,
            data="questo non e json",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        assert risposta.status_code == 400
```

#### Ambienti di Test con Docker

Docker permette di creare ambienti di integration test riproducibili e isolati. Un file `docker-compose.test.yml` tipico per testare automazioni:

```yaml
# docker-compose.test.yml
version: "3.8"

services:
  test-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: automation_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d automation_test"]
      interval: 5s
      timeout: 5s
      retries: 5

  test-redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  test-webhook-server:
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      DATABASE_URL: postgresql://test_user:test_password@test-db:5432/automation_test
      REDIS_URL: redis://test-redis:6379/0
    depends_on:
      test-db:
        condition: service_healthy
      test-redis:
        condition: service_healthy
    ports:
      - "5001:5000"

  integration-tests:
    build:
      context: .
      dockerfile: Dockerfile.test
    command: pytest tests/integration/ -v --tb=short
    environment:
      TEST_WEBHOOK_URL: http://test-webhook-server:5000
      DATABASE_URL: postgresql://test_user:test_password@test-db:5432/automation_test
      REDIS_URL: redis://test-redis:6379/0
    depends_on:
      test-webhook-server:
        condition: service_started
      test-db:
        condition: service_healthy
```

#### Test Fixture e Dati di Test

Le fixture sono fondamentali per creare dati di test consistenti e riutilizzabili:

```python
# tests/conftest.py

import pytest
import psycopg2
from datetime import datetime, timedelta

@pytest.fixture(scope="session")
def db_connection():
    """Connessione al database di test, condivisa per l'intera sessione."""
    conn = psycopg2.connect(
        host="localhost", port=5433,
        dbname="automation_test",
        user="test_user", password="test_password"
    )
    yield conn
    conn.close()

@pytest.fixture(autouse=True)
def pulisci_database(db_connection):
    """Pulisce le tabelle prima di ogni test."""
    cursore = db_connection.cursor()
    cursore.execute("DELETE FROM log_esecuzioni")
    cursore.execute("DELETE FROM ordini_test")
    db_connection.commit()
    yield
    db_connection.rollback()

@pytest.fixture
def ordini_campione(db_connection):
    """Inserisce ordini di esempio per i test."""
    cursore = db_connection.cursor()
    ordini = [
        ("ORD-001", 150.00, "completato", datetime.now() - timedelta(days=1)),
        ("ORD-002", 75.50, "in_attesa", datetime.now()),
        ("ORD-003", 200.00, "errore", datetime.now() - timedelta(hours=2)),
    ]
    for ordine in ordini:
        cursore.execute(
            "INSERT INTO ordini_test (id, importo, stato, data_creazione) VALUES (%s, %s, %s, %s)",
            ordine
        )
    db_connection.commit()
    return ordini
```

---

### End-to-End Test

Gli end-to-end test (E2E) verificano l'intero flusso dell'automazione, dall'evento scatenante al risultato finale. Sono i test piu costosi da mantenere ma anche i piu importanti per garantire che il workflow completo funzioni come previsto.

#### Full Workflow Testing

```python
# tests/e2e/test_workflow_ordine_completo.py

import pytest
import requests
import time
import json

@pytest.mark.e2e
class TestWorkflowOrdineCompleto:
    """
    Testa l'intero flusso: ricezione ordine -> validazione ->
    aggiornamento CRM -> invio email conferma -> aggiornamento inventario.
    """

    STAGING_URL = "https://staging.automazione.example.com"
    TIMEOUT_WORKFLOW = 30  # secondi max per completamento

    @pytest.fixture(autouse=True)
    def setup_e_cleanup(self):
        """Prepara l'ambiente di staging e pulisce dopo il test."""
        self.ordine_test_id = f"E2E-TEST-{int(time.time())}"
        yield
        # Cleanup: rimuovi dati di test dal sistema di staging
        requests.delete(
            f"{self.STAGING_URL}/api/admin/cleanup",
            json={"ordine_id": self.ordine_test_id},
            timeout=10
        )

    def test_flusso_ordine_completo(self):
        # 1. Invia l'ordine tramite webhook
        ordine = {
            "id": self.ordine_test_id,
            "cliente": {"email": "e2e-test@example.com", "nome": "Test E2E"},
            "prodotti": [{"sku": "TEST-PROD-001", "quantita": 2, "prezzo": 29.99}],
            "totale": 59.98
        }

        risposta = requests.post(
            f"{self.STAGING_URL}/webhooks/ordini",
            json={"evento": "ordine.creato", "dati": ordine},
            timeout=10
        )
        assert risposta.status_code == 200

        # 2. Attendi il completamento del workflow
        workflow_completato = False
        for tentativo in range(self.TIMEOUT_WORKFLOW):
            time.sleep(1)
            stato = requests.get(
                f"{self.STAGING_URL}/api/workflow-status/{self.ordine_test_id}",
                timeout=10
            ).json()

            if stato.get("stato") == "completato":
                workflow_completato = True
                break
            elif stato.get("stato") == "errore":
                pytest.fail(f"Workflow fallito: {stato.get('errore')}")

        assert workflow_completato, "Workflow non completato entro il timeout"

        # 3. Verifica risultati nel CRM
        contatto_crm = requests.get(
            f"{self.STAGING_URL}/api/verify/crm-contact",
            params={"email": "e2e-test@example.com"},
            timeout=10
        ).json()
        assert contatto_crm.get("ultimo_ordine") == self.ordine_test_id

        # 4. Verifica invio email
        email_log = requests.get(
            f"{self.STAGING_URL}/api/verify/email-sent",
            params={"to": "e2e-test@example.com", "ordine_id": self.ordine_test_id},
            timeout=10
        ).json()
        assert email_log.get("inviata") is True

        # 5. Verifica aggiornamento inventario
        inventario = requests.get(
            f"{self.STAGING_URL}/api/verify/inventory",
            params={"sku": "TEST-PROD-001"},
            timeout=10
        ).json()
        assert inventario.get("quantita_riservata") >= 2
```

#### Ambienti Sandbox e Account di Test

Per gli E2E test e indispensabile disporre di un ambiente sandbox completamente separato dalla produzione. Ogni servizio esterno utilizzato dall'automazione deve avere un corrispondente ambiente di test:

- **CRM sandbox**: account separato con dati fittizi, API key dedicata
- **Email sandbox**: servizi come Mailtrap o Mailhog per catturare le email senza inviarle realmente
- **Payment sandbox**: ambienti di test forniti dai gateway di pagamento (es. Stripe test mode)
- **Database di staging**: copia della struttura di produzione con dati sintetici

Ogni test E2E deve includere una procedura di **cleanup** che ripristina lo stato dell'ambiente al termine dell'esecuzione, indipendentemente dal risultato del test. Questo garantisce che i test successivi non siano influenzati da dati residui.

---

## Testing Piattaforme Low-Code

### n8n Testing

n8n offre diverse modalita per testare i workflow prima di metterli in produzione.

**Esecuzione in Modalita Test**: ogni workflow in n8n puo essere eseguito manualmente tramite il pulsante "Execute Workflow" nell'editor. Questa esecuzione utilizza i dati reali dei nodi di input (o dati di esempio iniettati manualmente) e mostra il risultato di ogni singolo nodo.

**Test Webhook**: per i workflow attivati da webhook, n8n fornisce un URL di test separato da quello di produzione. L'URL di test (tipicamente con il path `/webhook-test/`) e attivo solo quando l'editor del workflow e aperto, consentendo di testare i payload in arrivo senza rischiare di attivare il workflow di produzione.

**Iniezione di Dati Mock**: e possibile iniettare dati di test in qualsiasi punto del workflow utilizzando il nodo "Set" con dati statici. Una strategia efficace consiste nel creare un nodo "IF" all'inizio del workflow che controlla una variabile d'ambiente `N8N_TEST_MODE`: se attiva, il workflow utilizza dati mock invece di quelli reali.

```json
{
  "nodes": [
    {
      "name": "Controlla Modalita Test",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $env.N8N_TEST_MODE }}",
              "value2": "true"
            }
          ]
        }
      }
    },
    {
      "name": "Dati Mock",
      "type": "n8n-nodes-base.set",
      "parameters": {
        "values": {
          "string": [
            {"name": "ordine_id", "value": "TEST-001"},
            {"name": "email", "value": "test@example.com"}
          ],
          "number": [
            {"name": "importo", "value": 99.99}
          ]
        }
      }
    }
  ]
}
```

**Versionamento dei Workflow**: n8n supporta l'export dei workflow in formato JSON. E buona pratica versionare questi file JSON nel repository Git, consentendo di tracciare le modifiche e di effettuare rollback in caso di problemi. Un workflow CI/CD puo automatizzare l'import dei workflow in un'istanza di staging per il testing.

---

### Make Testing

Make (precedentemente Integromat) fornisce strumenti specifici per il testing degli scenari.

**Esecuzione di Test dello Scenario**: il pulsante "Run once" permette di eseguire una singola iterazione dello scenario. Durante questa esecuzione, Make mostra il flusso dei dati attraverso ogni modulo, evidenziando eventuali errori e i dati in input/output di ciascun passaggio.

**Dati di Esempio**: ogni modulo in Make puo essere configurato con dati di esempio (sample data) che vengono utilizzati durante la progettazione dello scenario. E importante che questi dati siano rappresentativi dei casi reali, inclusi i casi limite come campi vuoti, caratteri speciali e valori estremi.

**Simulazione Errori**: per testare la gestione degli errori, e possibile utilizzare il modulo "Tools > Set Variable" per forzare condizioni di errore, oppure configurare temporaneamente un modulo con credenziali non valide per verificare che il percorso di errore sia gestito correttamente. Make supporta anche i "Error Handler" che possono essere testati individualmente.

**Versionamento dei Blueprint**: Make consente di esportare gli scenari come blueprint JSON. Questi blueprint devono essere versionati nel repository Git. E consigliabile mantenere un naming convention chiaro: `scenario-nome-v1.0.json`, `scenario-nome-v1.1.json`.

---

### Power Automate Testing

Microsoft Power Automate offre funzionalita di testing integrate nell'ecosistema Microsoft.

**Test con Trigger Manuale**: Power Automate consente di testare un flusso aggiungendo un trigger manuale temporaneo. Il pulsante "Test" nella barra superiore dell'editor offre due opzioni: "Manually" (esecuzione con dati inseriti manualmente) e "Automatically" (utilizza i dati dell'ultimo trigger reale).

**Testing delle Espressioni**: le espressioni di Power Automate (basate su Workflow Definition Language) possono essere complesse. E possibile testarle isolatamente utilizzando l'azione "Compose" che valuta un'espressione e ne mostra il risultato. Esempio di espressioni da testare:

```
@{formatDateTime(utcNow(), 'dd/MM/yyyy')}
@{if(equals(triggerBody()?['stato'], 'attivo'), 'Processa', 'Ignora')}
@{coalesce(triggerBody()?['nome'], 'Nome non disponibile')}
```

**Testing dei Connector**: ogni connector utilizzato nel flusso deve essere verificato individualmente. Power Automate mostra lo stato delle connessioni nella sezione "Data > Connections". Prima di eseguire un test completo, verificare che tutte le connessioni siano in stato "Connected".

---

## Validazione Dati

La validazione dei dati e una delle misure preventive piu importanti per le automazioni. Un'automazione che processa dati non validi puo propagare errori in cascata attraverso tutti i sistemi collegati.

### Pattern di Validazione dell'Input

#### JSON Schema Validation

JSON Schema e uno standard potente per definire la struttura attesa dei dati:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Ordine",
  "description": "Schema per la validazione degli ordini in ingresso",
  "type": "object",
  "required": ["id", "cliente", "prodotti", "totale"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^ORD-[0-9]{3,10}$",
      "description": "Identificativo univoco dell'ordine"
    },
    "cliente": {
      "type": "object",
      "required": ["email", "nome"],
      "properties": {
        "email": {"type": "string", "format": "email"},
        "nome": {"type": "string", "minLength": 2, "maxLength": 100},
        "telefono": {"type": "string", "pattern": "^\\+?[0-9]{8,15}$"}
      }
    },
    "prodotti": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["sku", "quantita", "prezzo"],
        "properties": {
          "sku": {"type": "string"},
          "quantita": {"type": "integer", "minimum": 1},
          "prezzo": {"type": "number", "minimum": 0.01}
        }
      }
    },
    "totale": {
      "type": "number",
      "minimum": 0.01
    },
    "note": {
      "type": "string",
      "maxLength": 500
    }
  },
  "additionalProperties": false
}
```

```python
# automation/validazione.py

import jsonschema
import json
from pathlib import Path

def valida_ordine(dati: dict) -> tuple[bool, list[str]]:
    """Valida un ordine contro lo schema JSON."""
    schema_path = Path(__file__).parent / "schemas" / "ordine.schema.json"
    with open(schema_path) as f:
        schema = json.load(f)

    errori = []
    validatore = jsonschema.Draft202012Validator(schema)
    for errore in validatore.iter_errors(dati):
        percorso = " -> ".join(str(p) for p in errore.absolute_path)
        errori.append(f"{percorso}: {errore.message}" if percorso else errore.message)

    return len(errori) == 0, errori
```

#### Validazione con Pydantic

Pydantic offre un approccio ancora piu integrato con Python per la validazione dei dati, combinando type checking, validazione e serializzazione in un unico modello:

```python
# automation/modelli.py

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime

class Prodotto(BaseModel):
    sku: str = Field(..., min_length=3, max_length=50)
    quantita: int = Field(..., ge=1, le=9999)
    prezzo: float = Field(..., gt=0)

    @field_validator("sku")
    @classmethod
    def sku_formato_valido(cls, v: str) -> str:
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("SKU contiene caratteri non validi")
        return v.upper()

class Cliente(BaseModel):
    email: EmailStr
    nome: str = Field(..., min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, pattern=r"^\+?[0-9]{8,15}$")

class Ordine(BaseModel):
    id: str = Field(..., pattern=r"^ORD-[0-9]{3,10}$")
    cliente: Cliente
    prodotti: list[Prodotto] = Field(..., min_length=1)
    totale: float = Field(..., gt=0)
    note: Optional[str] = Field(None, max_length=500)
    data_creazione: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("totale")
    @classmethod
    def totale_coerente(cls, v: float, info) -> float:
        if "prodotti" in info.data:
            totale_calcolato = sum(
                p.quantita * p.prezzo for p in info.data["prodotti"]
            )
            differenza = abs(v - totale_calcolato)
            if differenza > 0.01:
                raise ValueError(
                    f"Totale ({v}) non corrisponde alla somma dei prodotti ({totale_calcolato})"
                )
        return v

# Esempio di utilizzo nella pipeline di automazione
def processa_input_ordine(dati_raw: dict) -> tuple[bool, Ordine | list[str]]:
    """Valida e processa i dati di un ordine in ingresso."""
    try:
        ordine = Ordine(**dati_raw)
        return True, ordine
    except Exception as e:
        errori = []
        for errore in e.errors():
            campo = " -> ".join(str(loc) for loc in errore["loc"])
            errori.append(f"{campo}: {errore['msg']}")
        return False, errori
```

### Sanitizzazione dei Dati

Oltre alla validazione, la sanitizzazione e fondamentale per prevenire injection e dati corrotti:

```python
# automation/sanitizzazione.py

import re
import html
from typing import Any

def sanitizza_stringa(valore: str, max_lunghezza: int = 1000) -> str:
    """Sanitizza una stringa rimuovendo caratteri pericolosi."""
    # Rimuovi caratteri di controllo (eccetto newline e tab)
    valore = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", valore)
    # Escape HTML per prevenire XSS se il dato finisce in un contesto web
    valore = html.escape(valore)
    # Tronca alla lunghezza massima
    return valore[:max_lunghezza]

def sanitizza_payload(dati: dict, profondita_max: int = 10) -> dict:
    """Sanitizza ricorsivamente un dizionario di dati."""
    if profondita_max <= 0:
        raise ValueError("Payload troppo profondamente annidato")

    risultato = {}
    for chiave, valore in dati.items():
        chiave_sanitizzata = sanitizza_stringa(str(chiave), max_lunghezza=100)
        if isinstance(valore, str):
            risultato[chiave_sanitizzata] = sanitizza_stringa(valore)
        elif isinstance(valore, dict):
            risultato[chiave_sanitizzata] = sanitizza_payload(valore, profondita_max - 1)
        elif isinstance(valore, list):
            risultato[chiave_sanitizzata] = [
                sanitizza_payload(item, profondita_max - 1) if isinstance(item, dict)
                else sanitizza_stringa(str(item)) if isinstance(item, str)
                else item
                for item in valore
            ]
        else:
            risultato[chiave_sanitizzata] = valore
    return risultato
```

---

## Monitoraggio Automazioni in Produzione

### Metriche Chiave

Il monitoraggio in produzione e il complemento indispensabile del testing pre-deployment. Anche le automazioni piu testate possono incontrare problemi imprevisti in produzione: cambiamenti nelle API esterne, volumi di dati inattesi, degradazione delle performance.

Le metriche fondamentali da monitorare per ogni automazione sono:

- **Tasso di successo/fallimento**: percentuale di esecuzioni completate con successo rispetto al totale. Un'automazione sana dovrebbe mantenere un tasso di successo superiore al 99%.
- **Durata dell'esecuzione**: tempo medio, percentile 95 e percentile 99. Un aumento graduale della durata puo indicare problemi di performance che diventeranno critici.
- **Volume di dati processati**: numero di record/eventi elaborati per esecuzione e per unita di tempo.
- **Tasso di errore per tipo**: classificazione degli errori (timeout, errori di validazione, errori API, errori di autenticazione) per identificare pattern.
- **Profondita della coda**: se l'automazione processa una coda di messaggi, il numero di messaggi in attesa e un indicatore critico di capacita.

```python
# automation/metriche.py

from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Definizione delle metriche Prometheus
ESECUZIONI_TOTALI = Counter(
    "automazione_esecuzioni_totali",
    "Numero totale di esecuzioni",
    ["workflow", "stato"]
)

DURATA_ESECUZIONE = Histogram(
    "automazione_durata_secondi",
    "Durata dell'esecuzione in secondi",
    ["workflow"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

RECORD_PROCESSATI = Counter(
    "automazione_record_processati_totali",
    "Numero totale di record processati",
    ["workflow", "tipo"]
)

CODA_PROFONDITA = Gauge(
    "automazione_coda_profondita",
    "Numero di messaggi in coda",
    ["workflow"]
)

ERRORI_PER_TIPO = Counter(
    "automazione_errori_totali",
    "Errori per tipo",
    ["workflow", "tipo_errore"]
)

def monitora_esecuzione(nome_workflow: str):
    """Decorator per monitorare automaticamente l'esecuzione di un workflow."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            inizio = time.time()
            try:
                risultato = func(*args, **kwargs)
                ESECUZIONI_TOTALI.labels(workflow=nome_workflow, stato="successo").inc()
                return risultato
            except Exception as e:
                ESECUZIONI_TOTALI.labels(workflow=nome_workflow, stato="errore").inc()
                tipo_errore = type(e).__name__
                ERRORI_PER_TIPO.labels(
                    workflow=nome_workflow, tipo_errore=tipo_errore
                ).inc()
                raise
            finally:
                durata = time.time() - inizio
                DURATA_ESECUZIONE.labels(workflow=nome_workflow).observe(durata)
        return wrapper
    return decorator

# Esempio di utilizzo
@monitora_esecuzione("sincronizzazione_crm")
def sincronizza_contatti_crm(contatti: list) -> dict:
    """Workflow di sincronizzazione contatti verso il CRM."""
    processati = 0
    errori = 0
    for contatto in contatti:
        try:
            # ... logica di sincronizzazione ...
            processati += 1
        except Exception:
            errori += 1
    RECORD_PROCESSATI.labels(
        workflow="sincronizzazione_crm", tipo="contatti"
    ).inc(processati)
    return {"processati": processati, "errori": errori}
```

---

### Alerting

Un sistema di alerting efficace deve bilanciare la tempestivita delle notifiche con la prevenzione dell'alert fatigue. Troppi alert non azionabili portano il team a ignorarli, vanificando lo scopo del monitoraggio.

**Soglie di Alert**: le soglie devono essere definite in base al comportamento storico dell'automazione e agli SLA concordati.

```yaml
# alerting-rules.yml (Prometheus Alertmanager)

groups:
  - name: automazione_alert
    rules:
      - alert: AutomazioneErrorRateAlto
        expr: |
          rate(automazione_esecuzioni_totali{stato="errore"}[5m])
          / rate(automazione_esecuzioni_totali[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Tasso di errore alto per {{ $labels.workflow }}"
          description: "Il workflow {{ $labels.workflow }} ha un tasso di errore del {{ $value | humanizePercentage }} negli ultimi 5 minuti."
          runbook_url: "https://wiki.internal/runbooks/{{ $labels.workflow }}"

      - alert: AutomazioneDurataAnomala
        expr: |
          histogram_quantile(0.95, rate(automazione_durata_secondi_bucket[15m]))
          > 2 * histogram_quantile(0.95, rate(automazione_durata_secondi_bucket[24h]))
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Durata anomala per {{ $labels.workflow }}"
          description: "Il p95 della durata e raddoppiato rispetto alla media giornaliera."

      - alert: AutomazioneCompletamenteFerma
        expr: |
          increase(automazione_esecuzioni_totali[30m]) == 0
          and automazione_esecuzioni_totali > 0
        for: 30m
        labels:
          severity: critical
        annotations:
          summary: "Automazione {{ $labels.workflow }} ferma da 30 minuti"
          description: "Non sono state registrate esecuzioni negli ultimi 30 minuti. Verificare lo stato del servizio."

      - alert: CodaProfonditaCritica
        expr: automazione_coda_profondita > 1000
        for: 15m
        labels:
          severity: critical
        annotations:
          summary: "Coda di {{ $labels.workflow }} oltre i 1000 messaggi"
```

**Canali di Notifica**: gli alert devono essere instradati al canale appropriato in base alla severita:

- **Informational**: canale Slack dedicato (es. `#automazioni-info`)
- **Warning**: canale Slack + email al team
- **Critical**: PagerDuty / OpsGenie per notifica immediata con escalation

**Policy di Escalation**: se un alert critico non viene riconosciuto entro 15 minuti, viene escalato al livello successivo. Dopo 30 minuti senza riconoscimento, viene notificato il responsabile del team.

---

### Dashboard

Una dashboard Grafana ben progettata fornisce visibilita immediata sullo stato di tutte le automazioni.

```json
{
  "dashboard": {
    "title": "Monitoraggio Automazioni",
    "panels": [
      {
        "title": "Tasso di Successo (ultimi 30 min)",
        "type": "gauge",
        "targets": [
          {
            "expr": "sum(rate(automazione_esecuzioni_totali{stato='successo'}[30m])) / sum(rate(automazione_esecuzioni_totali[30m])) * 100",
            "legendFormat": "Tasso successo %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "orange", "value": 95},
                {"color": "green", "value": 99}
              ]
            },
            "min": 0,
            "max": 100,
            "unit": "percent"
          }
        }
      },
      {
        "title": "Durata Esecuzione per Workflow (p95)",
        "type": "timeseries",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(automazione_durata_secondi_bucket[5m])) by (le, workflow))",
            "legendFormat": "{{ workflow }}"
          }
        ]
      },
      {
        "title": "Errori per Tipo (ultimi 60 min)",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (tipo_errore) (increase(automazione_errori_totali[1h]))",
            "legendFormat": "{{ tipo_errore }}"
          }
        ]
      },
      {
        "title": "Throughput (record/minuto)",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(automazione_record_processati_totali[5m])) by (workflow) * 60",
            "legendFormat": "{{ workflow }}"
          }
        ]
      },
      {
        "title": "Profondita Coda",
        "type": "timeseries",
        "targets": [
          {
            "expr": "automazione_coda_profondita",
            "legendFormat": "{{ workflow }}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "thresholdsStyle": {"mode": "line+area"}
            },
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "orange", "value": 500},
                {"color": "red", "value": 1000}
              ]
            }
          }
        }
      }
    ]
  }
}
```

Le query PromQL principali per il monitoraggio delle automazioni:

```promql
# Tasso di successo complessivo
sum(rate(automazione_esecuzioni_totali{stato="successo"}[5m]))
/ sum(rate(automazione_esecuzioni_totali[5m]))

# Durata media per workflow
rate(automazione_durata_secondi_sum[5m])
/ rate(automazione_durata_secondi_count[5m])

# Top 5 workflow per numero di errori nell'ultima ora
topk(5, sum by (workflow) (increase(automazione_errori_totali[1h])))

# Tendenza della durata (confronto con ieri)
histogram_quantile(0.95, rate(automazione_durata_secondi_bucket[1h]))
/ histogram_quantile(0.95, rate(automazione_durata_secondi_bucket[1h] offset 24h))
```

---

### Logging

Un sistema di logging strutturato e indispensabile per il debugging e l'analisi post-mortem delle automazioni.

#### Logging Strutturato

```python
# automation/logging_config.py

import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

class StructuredFormatter(logging.Formatter):
    """Formatter che produce log in formato JSON strutturato."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "livello": record.levelname,
            "logger": record.name,
            "messaggio": record.getMessage(),
            "modulo": record.module,
            "funzione": record.funcName,
            "linea": record.lineno,
        }

        # Aggiungi attributi extra se presenti
        for attr in ["workflow", "correlation_id", "ordine_id", "fase"]:
            if hasattr(record, attr):
                log_entry[attr] = getattr(record, attr)

        # Aggiungi informazioni sull'eccezione se presente
        if record.exc_info and record.exc_info[0]:
            log_entry["eccezione"] = {
                "tipo": record.exc_info[0].__name__,
                "messaggio": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }

        return json.dumps(log_entry, ensure_ascii=False)


def configura_logging(nome_workflow: str, livello: str = "INFO"):
    """Configura il logging strutturato per un workflow."""
    logger = logging.getLogger(nome_workflow)
    logger.setLevel(getattr(logging, livello))

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)

    return logger


class ContextLogger:
    """Logger con contesto automatico per il tracing delle automazioni."""

    def __init__(self, nome_workflow: str, correlation_id: Optional[str] = None):
        self.logger = configura_logging(nome_workflow)
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.workflow = nome_workflow

    def _extra(self, **kwargs) -> dict:
        extra = {
            "workflow": self.workflow,
            "correlation_id": self.correlation_id,
        }
        extra.update(kwargs)
        return extra

    def info(self, messaggio: str, **kwargs):
        self.logger.info(messaggio, extra=self._extra(**kwargs))

    def warning(self, messaggio: str, **kwargs):
        self.logger.warning(messaggio, extra=self._extra(**kwargs))

    def error(self, messaggio: str, exc_info=None, **kwargs):
        self.logger.error(messaggio, exc_info=exc_info, extra=self._extra(**kwargs))

    def debug(self, messaggio: str, **kwargs):
        self.logger.debug(messaggio, extra=self._extra(**kwargs))

    def critical(self, messaggio: str, exc_info=None, **kwargs):
        self.logger.critical(messaggio, exc_info=exc_info, extra=self._extra(**kwargs))
```

I cinque livelli di log e il loro utilizzo nelle automazioni:

| Livello    | Utilizzo nel contesto dell'automazione                                                |
|------------|--------------------------------------------------------------------------------------|
| `DEBUG`    | Dettagli interni di elaborazione, payload completi, valori intermedi delle trasformazioni. Usare solo in sviluppo o per debugging temporaneo.  |
| `INFO`     | Inizio e fine dell'esecuzione, numero di record processati, passaggi principali del workflow. Il livello standard in produzione.                |
| `WARNING`  | Situazioni anomale ma gestite: retry in corso, dati incompleti ma processabili, rate limit avvicinato, risposta lenta da API esterna.           |
| `ERROR`    | Errori che impediscono il completamento di una singola operazione ma non del workflow intero: record non processabile, API restituisce errore.  |
| `CRITICAL` | Errori che impediscono il funzionamento del workflow: impossibile connettersi al database, credenziali scadute, servizio critico non disponibile.|

#### Correlation ID per il Tracing

Ogni esecuzione di un workflow deve generare un **correlation ID** univoco (tipicamente un UUID) che viene propagato attraverso tutti i sistemi toccati dall'automazione. Questo ID consente di ricostruire l'intero percorso di un'esecuzione attraverso log distribuiti su piu servizi.

#### Centralizzazione dei Log

Per le automazioni in produzione, i log devono essere centralizzati in un sistema dedicato:

- **ELK Stack** (Elasticsearch, Logstash, Kibana): soluzione completa per l'indicizzazione, la ricerca e la visualizzazione dei log. Elasticsearch consente ricerche full-text sui log, Kibana offre dashboard e visualizzazioni.
- **Grafana Loki**: alternativa leggera a ELK, progettata per integrarsi nativamente con Grafana. Utilizza un modello di indicizzazione basato su label invece di indicizzare il contenuto completo, risultando piu efficiente per grandi volumi di log.

La **retention** dei log deve essere calibrata in base ai requisiti normativi e operativi: tipicamente 30 giorni per i log di livello DEBUG/INFO, 90 giorni per WARNING, e 1 anno o piu per ERROR e CRITICAL. La **rotazione** dei log deve essere configurata per evitare l'esaurimento dello spazio disco, specialmente per le automazioni che generano grandi volumi di log.

---

## Gestione Errori

### Strategie di Retry

Gli errori nelle automazioni non sono tutti uguali. La strategia di retry deve essere calibrata in base al tipo di errore.

#### Immediate Retry

Il retry immediato e appropriato solo per errori molto transitori, come un pacchetto di rete perso. Viene effettuato un numero limitato di tentativi (tipicamente 1-2) senza alcun ritardo.

#### Exponential Backoff

La strategia piu utilizzata per gli errori transitori (timeout, rate limit, servizio temporaneamente non disponibile). Il tempo di attesa aumenta esponenzialmente tra un tentativo e l'altro, con un elemento di jitter (casualita) per evitare che piu automazioni riprovino simultaneamente.

```python
# automation/retry.py

import time
import random
import logging
from functools import wraps
from typing import Tuple, Type

logger = logging.getLogger(__name__)

def retry_con_backoff(
    max_tentativi: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    eccezioni_retry: Tuple[Type[Exception], ...] = (Exception,),
    eccezioni_fatali: Tuple[Type[Exception], ...] = (ValueError, KeyError),
):
    """
    Decorator per retry con exponential backoff e jitter.

    Args:
        max_tentativi: numero massimo di tentativi
        base_delay: ritardo iniziale in secondi
        max_delay: ritardo massimo in secondi
        eccezioni_retry: tuple di eccezioni per le quali effettuare retry
        eccezioni_fatali: tuple di eccezioni che NON devono essere ritentate
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ultimo_errore = None
            for tentativo in range(1, max_tentativi + 1):
                try:
                    return func(*args, **kwargs)
                except eccezioni_fatali as e:
                    logger.error(
                        f"Errore fatale (non ritentabile) in {func.__name__}: {e}"
                    )
                    raise
                except eccezioni_retry as e:
                    ultimo_errore = e
                    if tentativo == max_tentativi:
                        logger.error(
                            f"Esauriti {max_tentativi} tentativi per {func.__name__}: {e}"
                        )
                        raise

                    delay = min(base_delay * (2 ** (tentativo - 1)), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    attesa = delay + jitter

                    logger.warning(
                        f"Tentativo {tentativo}/{max_tentativi} fallito per "
                        f"{func.__name__}: {e}. Retry tra {attesa:.1f}s"
                    )
                    time.sleep(attesa)

            raise ultimo_errore
        return wrapper
    return decorator
```

#### Circuit Breaker

Il circuit breaker previene il sovraccarico di un servizio gia in difficolta. Dopo un numero definito di fallimenti consecutivi, il circuito si "apre" e le chiamate successive falliscono immediatamente senza tentare la connessione, dando al servizio il tempo di recuperare.

```python
# automation/circuit_breaker.py

import time
from enum import Enum
from threading import Lock

class StatoCircuito(Enum):
    CHIUSO = "chiuso"        # Funzionamento normale
    APERTO = "aperto"        # Blocca tutte le richieste
    SEMI_APERTO = "semi_aperto"  # Permette una richiesta di test

class CircuitBreakerAperto(Exception):
    """Eccezione lanciata quando il circuit breaker e aperto."""
    pass

class CircuitBreaker:
    def __init__(
        self,
        nome: str,
        soglia_fallimenti: int = 5,
        timeout_reset: float = 60.0,
    ):
        self.nome = nome
        self.soglia_fallimenti = soglia_fallimenti
        self.timeout_reset = timeout_reset
        self.stato = StatoCircuito.CHIUSO
        self.conteggio_fallimenti = 0
        self.ultimo_fallimento = 0.0
        self.lock = Lock()

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            self._verifica_stato()
            try:
                risultato = func(*args, **kwargs)
                self._registra_successo()
                return risultato
            except Exception as e:
                self._registra_fallimento()
                raise
        return wrapper

    def _verifica_stato(self):
        with self.lock:
            if self.stato == StatoCircuito.APERTO:
                if time.time() - self.ultimo_fallimento > self.timeout_reset:
                    self.stato = StatoCircuito.SEMI_APERTO
                else:
                    raise CircuitBreakerAperto(
                        f"Circuit breaker '{self.nome}' aperto. "
                        f"Riprova tra {self.timeout_reset - (time.time() - self.ultimo_fallimento):.0f}s"
                    )

    def _registra_successo(self):
        with self.lock:
            self.conteggio_fallimenti = 0
            self.stato = StatoCircuito.CHIUSO

    def _registra_fallimento(self):
        with self.lock:
            self.conteggio_fallimenti += 1
            self.ultimo_fallimento = time.time()
            if self.conteggio_fallimenti >= self.soglia_fallimenti:
                self.stato = StatoCircuito.APERTO
```

#### Dead Letter Queue e Manual Review Queue

Quando tutti i tentativi di retry sono esauriti, il messaggio o l'evento deve essere instradato verso una **dead letter queue** (DLQ). La DLQ conserva i messaggi non processabili per un'analisi successiva e un eventuale riprocessamento manuale.

La **manual review queue** e un concetto simile ma orientato ai dati che richiedono verifica umana: record con dati anomali, ordini con importi insoliti, richieste che non superano le regole di validazione. Questi elementi non sono necessariamente errori tecnici, ma casi che richiedono giudizio umano.

---

### Notifica Errori

#### Classificazione degli Errori

La classificazione corretta degli errori e fondamentale per determinare la risposta appropriata:

- **Errori transitori**: timeout di rete, rate limit, servizio temporaneamente non disponibile. Richiedono retry automatico e generano alert solo se persistono.
- **Errori permanenti**: dati non validi, risorsa non trovata (404), autenticazione fallita (401/403). Non hanno senso di essere ritentati e richiedono intervento umano o correzione dei dati.
- **Errori di sistema**: crash dell'applicazione, esaurimento memoria, disco pieno. Richiedono intervento immediato sull'infrastruttura.

#### Prevenzione dell'Alert Fatigue

L'alert fatigue si verifica quando il volume di notifiche e cosi alto che il team smette di prestare attenzione. Strategie di prevenzione:

- **Aggregazione**: invece di un alert per ogni singolo errore, aggregare gli errori simili e notificare un sommario (es. "47 errori di timeout verso API-X nell'ultima ora")
- **Deduplicazione**: non ripetere lo stesso alert se il precedente non e stato ancora risolto
- **Soglie dinamiche**: basare le soglie sul comportamento storico piuttosto che su valori assoluti
- **Link al runbook**: ogni alert deve includere un link alla procedura di risoluzione, rendendo l'alert immediatamente azionabile

---

### Recovery Procedures

#### Recupero Automatico

Le automazioni dovrebbero implementare meccanismi di recupero automatico quando possibile:

- **Riprocessamento automatico dalla DLQ**: dopo un periodo configurabile, i messaggi nella dead letter queue vengono automaticamente riprocessati
- **Failover su sistemi alternativi**: se l'API primaria non e disponibile, l'automazione puo passare a un'API di backup
- **Degradazione controllata**: l'automazione riduce la funzionalita (ad esempio, salta l'invio dell'email di conferma) piuttosto che fallire completamente

#### Procedure di Intervento Manuale

Quando il recupero automatico non e sufficiente, devono esistere procedure documentate per l'intervento manuale:

1. **Identificazione**: consultare i log e la dashboard per comprendere la natura e la portata del problema
2. **Contenimento**: se necessario, disabilitare l'automazione per prevenire ulteriori danni
3. **Diagnosi**: analizzare la causa radice utilizzando correlation ID e log strutturati
4. **Risoluzione**: applicare la correzione (fix del codice, aggiornamento credenziali, pulizia dati)
5. **Verifica**: eseguire un test manuale per confermare la risoluzione
6. **Riprocessamento**: riprocessare i dati accumulati durante il periodo di disservizio
7. **Post-mortem**: documentare l'incidente e le azioni preventive

#### Riconciliazione dei Dati

Dopo un'interruzione, e spesso necessario riconciliare i dati tra i sistemi. Un processo di riconciliazione tipico:

```python
# automation/riconciliazione.py

def riconcilia_ordini(
    ordini_sorgente: list[dict],
    ordini_destinazione: list[dict]
) -> dict:
    """
    Confronta gli ordini tra sistema sorgente e destinazione
    per identificare discrepanze.
    """
    sorgente_ids = {o["id"]: o for o in ordini_sorgente}
    destinazione_ids = {o["id"]: o for o in ordini_destinazione}

    mancanti_in_destinazione = []
    mancanti_in_sorgente = []
    discrepanze = []

    for id_ordine, ordine in sorgente_ids.items():
        if id_ordine not in destinazione_ids:
            mancanti_in_destinazione.append(ordine)
        else:
            dest = destinazione_ids[id_ordine]
            if ordine.get("importo") != dest.get("importo"):
                discrepanze.append({
                    "id": id_ordine,
                    "campo": "importo",
                    "sorgente": ordine.get("importo"),
                    "destinazione": dest.get("importo")
                })

    for id_ordine in destinazione_ids:
        if id_ordine not in sorgente_ids:
            mancanti_in_sorgente.append(destinazione_ids[id_ordine])

    return {
        "mancanti_in_destinazione": mancanti_in_destinazione,
        "mancanti_in_sorgente": mancanti_in_sorgente,
        "discrepanze": discrepanze,
        "totale_problemi": (
            len(mancanti_in_destinazione)
            + len(mancanti_in_sorgente)
            + len(discrepanze)
        )
    }
```

#### Procedure di Rollback

Ogni modifica introdotta da un'automazione deve essere reversibile. Le procedure di rollback devono essere documentate e testate periodicamente:

- **Rollback del codice**: il codice dell'automazione e versionato in Git; un rollback equivale a un deploy della versione precedente
- **Rollback dei dati**: per le modifiche ai dati, mantenere un log delle operazioni che consenta di invertire le modifiche (pattern event sourcing)
- **Rollback delle configurazioni**: le configurazioni delle piattaforme low-code devono essere versionate come blueprint/JSON, consentendo il ripristino rapido

---

## Documentazione Automazioni

Una documentazione accurata e essenziale per la manutenibilita a lungo termine delle automazioni. Ogni automazione deve essere registrata in un catalogo centralizzato.

### Catalogo delle Automazioni

Il catalogo e un registro centrale di tutte le automazioni attive, contenente per ciascuna:

| Campo                  | Descrizione                                             |
|------------------------|---------------------------------------------------------|
| Nome                   | Identificativo univoco dell'automazione                 |
| Descrizione            | Cosa fa l'automazione e perche esiste                   |
| Owner                  | Persona o team responsabile                             |
| Piattaforma            | n8n, Make, Power Automate, script custom, ecc.         |
| Frequenza              | Schedulazione o trigger                                 |
| Sistemi coinvolti      | Lista dei servizi/API utilizzati                        |
| SLA                    | Tempo massimo di disservizio accettabile                |
| Link dashboard         | URL della dashboard di monitoraggio                     |
| Link runbook           | URL della procedura operativa                           |
| Ultima modifica        | Data e descrizione dell'ultimo cambiamento              |

### Template README per ogni Automazione

```markdown
# Nome dell'Automazione

## Scopo
Descrizione chiara di cosa fa l'automazione e quale problema aziendale risolve.

## Trigger
- Tipo: webhook / schedulazione / evento
- Dettagli: [URL webhook / espressione cron / nome evento]

## Input
- Sorgente dei dati
- Formato atteso (link allo schema JSON)
- Volume tipico

## Output
- Destinazione dei dati
- Formato prodotto
- Effetti collaterali (email inviate, record creati, ecc.)

## Dipendenze
- Servizio A (versione X.Y) - [link documentazione API]
- Servizio B (versione Z.W) - [link documentazione API]
- Librerie: requirements.txt o package.json

## Configurazione
- Variabili d'ambiente richieste
- Secrets necessari (dove sono conservati)
- Parametri configurabili

## Monitoraggio
- Dashboard: [link]
- Alert configurati: [lista]
- Log: [dove trovarli]

## Runbook
- Procedura di restart
- Procedura di rollback
- Contatti di emergenza
- Problemi noti e soluzioni
```

### Change Log

Ogni automazione deve mantenere un registro delle modifiche che documenti non solo cosa e cambiato, ma perche:

```markdown
## Change Log

### 2026-03-25
- Aggiunto retry con exponential backoff per le chiamate al CRM (causa: timeout frequenti nelle ore di punta)
- Aumentato il timeout delle chiamate API da 10s a 30s

### 2026-03-15
- Aggiunto campo "codice_fiscale" alla sincronizzazione contatti (richiesta dal reparto contabilita)
- Aggiornato lo schema di validazione JSON

### 2026-03-01
- Deploy iniziale dell'automazione
- Configurati alert su Slack e PagerDuty
```

---

## Best Practices

1. **Testare ogni automazione prima del deploy in produzione, senza eccezioni.** Anche un'automazione apparentemente semplice (un singolo passaggio di copia dati) puo contenere errori nelle trasformazioni, nei mapping dei campi o nella gestione dei valori nulli. Utilizzare la piramide del testing: molti unit test, un numero adeguato di integration test e almeno un end-to-end test per ogni workflow critico.

2. **Implementare la validazione dei dati in ingresso e in uscita in ogni punto di confine.** Ogni volta che i dati entrano nell'automazione (da un webhook, da un'API, da un file) e ogni volta che escono (verso un database, un'API, un file), devono essere validati contro uno schema definito. Utilizzare JSON Schema o Pydantic per definire questi schemi in modo formale e testabile.

3. **Adottare il principio di fail-fast e fail-loud.** Un'automazione che fallisce silenziosamente e molto piu pericolosa di una che fallisce in modo evidente. Ogni errore deve essere loggato, classificato e notificato. Mai catturare eccezioni generiche senza almeno loggarle. Mai ignorare un codice di risposta HTTP diverso da 2xx.

4. **Utilizzare ambienti separati per sviluppo, staging e produzione.** Ogni piattaforma di automazione (n8n, Make, Power Automate) e ogni script custom deve avere almeno un ambiente di staging dove testare le modifiche con dati realistici prima di applicarle alla produzione. Le credenziali API devono essere diverse per ogni ambiente.

5. **Versionare tutto: codice, configurazioni, blueprint, schemi.** Il codice degli script va in Git. I workflow delle piattaforme low-code devono essere esportati come JSON e versionati. Gli schemi di validazione devono essere versionati. Le configurazioni degli alert e delle dashboard devono essere versionati (Infrastructure as Code). Questo consente rollback rapidi e tracciabilita delle modifiche.

6. **Monitorare proattivamente con metriche, log strutturati e alert calibrati.** Non aspettare che un utente segnali un problema. Configurare dashboard che mostrino il tasso di successo, la durata delle esecuzioni e il volume processato. Configurare alert con soglie basate sul comportamento storico. Utilizzare log strutturati (JSON) con correlation ID per facilitare il debugging.

7. **Documentare ogni automazione con rigore e mantenere la documentazione aggiornata.** Un'automazione non documentata e un debito tecnico che cresce nel tempo. Utilizzare il template README descritto in questa guida per ogni automazione. Mantenere un catalogo centralizzato. Aggiornare il change log ad ogni modifica.

8. **Implementare strategie di retry intelligenti con circuit breaker.** Non tutti gli errori meritano un retry. Classificare gli errori in transitori e permanenti. Utilizzare exponential backoff con jitter per i retry. Implementare circuit breaker per proteggere i servizi esterni da sovraccarico. Instradare i messaggi non processabili verso una dead letter queue per analisi successiva.

9. **Eseguire test di regressione dopo ogni modifica, anche quelle apparentemente innocue.** Una modifica a una singola trasformazione puo avere effetti a cascata su tutto il workflow. Mantenere una suite di test automatizzati che viene eseguita in una pipeline CI/CD ad ogni push. Integrare i test delle automazioni nel flusso di sviluppo standard del team.

10. **Pianificare e testare le procedure di disaster recovery regolarmente.** Non basta avere procedure documentate: devono essere testate periodicamente (almeno trimestralmente) per verificare che funzionino. Simulare scenari di fallimento: cosa succede se l'API del CRM e non disponibile per 2 ore? Cosa succede se il database si corrompe? Cosa succede se un webhook invia dati malformati per 30 minuti prima che ce ne accorgiamo? Avere risposte testate a queste domande e cio che distingue un sistema di automazione resiliente da uno fragile.

---

> **Nota finale**: il testing e la qualita delle automazioni non sono un'attivita una tantum, ma un processo continuo. Man mano che i requisiti cambiano, i volumi crescono e i sistemi si evolvono, anche la strategia di testing e monitoraggio deve essere rivista e aggiornata. L'investimento in qualita e l'investimento con il ritorno piu alto nel mondo dell'automazione.

---

## Esercizi

1. **Lab — pytest workflow Python.** Scrivi 5 test (unit + integration) per uno script di automazione esistente, raggiungere 80% coverage.
2. **Lab — mock di Stripe webhook.** Test riceve webhook con HMAC valido e invalido; verifica processing differente.
3. **Stretch — contract testing.** Implementa Pact tra producer (la tua API) e consumer (script che la usa).

## Auto-valutazione

1. Test pyramid: cosa significa e perche?
2. Mock vs stub vs fake: differenze.
3. Contract testing: a cosa serve?
4. Low-code testing: limiti e workaround.
5. Idempotency test: come strutturarlo?

## Letture primarie consigliate

- Martin Fowler — *Test Pyramid*. https://martinfowler.com/articles/practical-test-pyramid.html
- pytest documentation. https://docs.pytest.org/
- Pact contract testing. https://docs.pact.io/

## Collegamenti incrociati

- Modulo 17 — `17-retry-idempotency-pattern.md`: idempotency.
- Modulo 18 — `18-workflow-versioning-rollback.md`: versioning + test.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Test pyramid** | Unit > integration > e2e. |
| **Mock** | Fake che verifica chiamate. |
| **Stub** | Fake che ritorna valori predefiniti. |
| **Contract testing** | Test che verifica consumer/producer aderiscono a contratto. |
| **Pact** | Tool contract testing. |
| **Coverage** | % di codice eseguito da test. |
