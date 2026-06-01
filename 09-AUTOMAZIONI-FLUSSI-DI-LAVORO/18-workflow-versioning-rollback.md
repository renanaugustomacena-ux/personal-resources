---
corso: "Automazioni e Flussi di Lavoro"
fase: "5 — Pattern Avanzati"
modulo: 18
titolo: "Versioning, Deploy e Rollback dei Workflow di Automazione"
versione: "n8n 1.x, Power Platform 2024+"
livello: "competent → proficient"
prerequisiti: ["Modulo 06 — Orchestrazione", "Modulo 07 — CI/CD Workflow", "Git basics", "CI/CD concepts"]
obiettivi:
  - "Versionare workflow come codice in Git con diff, blame e code review su JSON/YAML"
  - "Costruire pipeline CI/CD per workflow: lint, test, deploy automatico e smoke test"
  - "Eseguire rollback sicuro tramite re-deploy della versione precedente senza modifiche manuali in prod"
  - "Gestire Power Platform solutions con export/import automatizzato e environment variable"
  - "Implementare feature flag per rilascio progressivo di workflow con canary e blue-green deploy"
tag: [versioning, rollback, ci-cd, deploy, feature-flag, workflow-as-code, blue-green, canary]
---

# Versioning, Deploy e Rollback dei Workflow di Automazione

> **Obiettivi di apprendimento**
> 1. Versionare workflow come codice in Git con diff, blame e code review su JSON/YAML
> 2. Costruire pipeline CI/CD per workflow: lint, test, deploy automatico e smoke test
> 3. Eseguire rollback sicuro tramite re-deploy della versione precedente senza modifiche manuali in prod
> 4. Gestire Power Platform solutions con export/import automatizzato e environment variable
> 5. Implementare feature flag per rilascio progressivo di workflow con canary e blue-green deploy

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 4 — Pattern di affidabilita · Modulo 18
> **Prerequisiti:** Moduli 06, 07; Git basics; CI/CD concepts.
> **Obiettivi:** versioning workflow in Git (n8n JSON, Power Platform solutions), deploy automation pipeline, rollback procedure.
> **Tempo:** lettura 60 min · lab 240 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-24

## Idee guida

1. **Workflow as code: JSON in Git.** Diff, code review, blame, history.
2. **Pipeline CI/CD per workflow: lint, test, deploy, smoke.** Stesse tecniche dell'app code.
3. **Rollback = re-deploy precedente versione.** Mai modifiche manuali in prod.
4. **Solution-based deploy (Power Platform) > export ad hoc.** Solution incapsula tutto.
5. **Feature flag per deploy graduale.** "Solo 10% del traffico al nuovo workflow."

---

## Indice

- [Panoramica](#panoramica)
- [Concetti Fondamentali](#concetti-fondamentali)
  - [Perche Versionare i Workflow](#perche-versionare-i-workflow)
  - [Workflow as Code: il Cambio di Paradigma](#workflow-as-code-il-cambio-di-paradigma)
  - [Strategie di Versioning per Piattaforma](#strategie-di-versioning-per-piattaforma)
- [Guida Pratica](#guida-pratica)
  - [Repository Git Dedicato per Automazioni](#repository-git-dedicato-per-automazioni)
  - [Branch Strategy: GitFlow vs Trunk-Based](#branch-strategy-gitflow-vs-trunk-based)
  - [Pipeline CI/CD per Workflow](#pipeline-cicd-per-workflow)
  - [Esempio End-to-End: Deploy n8n Fatturazione PA](#esempio-end-to-end-deploy-n8n-fatturazione-pa)
- [Configurazione](#configurazione)
  - [Multi-Ambiente: Dev, Staging, Prod](#multi-ambiente-dev-staging-prod)
  - [Secrets Management](#secrets-management)
  - [Blue/Green e Canary Release](#bluegreen-e-canary-release)
  - [Schema e Contract Versioning](#schema-e-contract-versioning)
  - [Testing Pre-Deploy](#testing-pre-deploy)
- [Best Practices](#best-practices)
  - [Documentation as Code](#documentation-as-code)
  - [Disaster Recovery](#disaster-recovery)
  - [Procedure di Rollback Sicuro](#procedure-di-rollback-sicuro)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

Versionare un workflow di automazione significa applicare alle catene di integrazione gli stessi principi di disciplina ingegneristica che da decenni governano lo sviluppo software: ogni modifica e tracciata, ogni rilascio e riproducibile, ogni rollback e una procedura definita anziche un'improvvisazione. In assenza di versioning, un workflow di produzione che ieri funzionava perfettamente puo trovarsi oggi in uno stato indeterminato senza che nessuno sia in grado di ricostruire chi ha modificato cosa, quando e perche. Quando l'automazione tocca processi critici -- emissione di fatture elettroniche verso lo SDI, generazione di F24 verso l'Agenzia delle Entrate, sincronizzazione di anagrafiche cliente tra CRM e gestionale -- l'assenza di versioning si traduce in giorni di fermo operativo e in violazioni potenziali di compliance.

Le piattaforme di workflow automation sono nate con un'enfasi forte sul "low-code" e sull'usabilita immediata, e per anni hanno relegato il versioning a funzionalita secondaria o assente. Oggi il quadro e cambiato: Zapier ha introdotto la versions history nativa con possibilita di rollback manuale, Make consente l'export di scenari in formato Blueprint JSON, n8n permette l'esportazione completa dei workflow in JSON facilmente versionabile in Git, Power Automate offre il sistema Solutions integrato con il framework ALM di Microsoft Dataverse e con la Power Platform CLI per il source control. Tuttavia, l'esistenza di funzionalita native non implica che vengano usate correttamente: la maturita del versioning dipende dalle pratiche organizzative, non dagli strumenti.

Questa guida copre il ciclo completo del versioning di workflow: dall'istituzione di un repository Git dedicato alla definizione di una branch strategy, dalla pipeline CI/CD che promuove un workflow da dev a prod alla configurazione blue/green per automazioni critiche, dai criteri per un rollback sicuro alla gestione del versioning di schemi e contratti API. Ogni sezione include esempi pratici, comandi verificati e procedure operative pronte da adattare al contesto di una PMI italiana o di un'organizzazione enterprise.

---

## Concetti Fondamentali

### Perche Versionare i Workflow

La giustificazione del versioning non e tecnica ma operativa, e poggia su quattro pilastri.

Il primo pilastro e l'**audit**. Ogni organizzazione regolata -- bancaria, sanitaria, fiscale, contabile -- deve essere in grado di rispondere alla domanda "chi ha modificato questo processo, quando, e con quale autorizzazione?". Per un workflow che genera o trasmette dati fiscali, l'audit non e un nice-to-have: l'Agenzia delle Entrate, in caso di verifica, puo richiedere evidenza dei processi automatizzati che hanno generato fatture, comunicazioni IVA o LIPE. Senza versioning con storia firmata (commit Git con autore, timestamp, hash), l'audit e impossibile.

Il secondo pilastro e il **rollback**. Quando un deploy introduce un bug -- una mappatura errata che invia il codice fiscale in luogo della partita IVA, una conversione di valuta sbagliata, un endpoint chiamato sull'ambiente errato -- la prima domanda non e "come correggiamo?" ma "come torniamo allo stato precedente in cinque minuti?". Senza versioning, il rollback diventa un'operazione di reverse engineering basata sulla memoria.

Il terzo pilastro e la **gestione multi-ambiente**. Un workflow maturo non viene scritto direttamente in produzione: viene sviluppato in un ambiente dev, validato in staging con dati realistici ma non sensibili, e infine promosso in produzione. Senza versioning, la promozione tra ambienti diventa un copia-incolla manuale soggetto a deriva.

Il quarto pilastro e la **compliance**. GDPR, ISO 27001, SOC 2, e -- per il settore finanziario italiano -- le linee guida Banca d'Italia su outsourcing e digital operational resilience (DORA), tutte richiedono evidenza di change management formalizzato. Il versioning Git con branch protetti, code review e CI/CD documentata e la prova piu economica e robusta che un cambio non sia stato applicato in modo arbitrario.

### Workflow as Code: il Cambio di Paradigma

Il principio fondante del versioning serio dei workflow e "automation as code": il workflow non e cio che vedi nell'editor visuale, ma cio che e descritto in un file di testo (JSON, YAML, Blueprint) versionato in Git. L'editor visuale e un'interfaccia di rendering del file, non la fonte di verita. Questo cambio di paradigma ha implicazioni importanti.

La prima implicazione e che ogni modifica al workflow deve passare per una pull request, non per l'editor della piattaforma. Se uno sviluppatore apre l'editor n8n di produzione, modifica un nodo e clicca "Save", quel cambio non e tracciato in Git: la prossima sincronizzazione dal repository sovrascrivera la modifica, oppure il file in Git divergera silenziosamente dalla realta dell'istanza. La regola operativa e: editor di produzione in sola lettura, modifiche solo via merge da Git.

La seconda implicazione e la necessita di un meccanismo di sincronizzazione bidirezionale o, preferibilmente, unidirezionale Git -> piattaforma. Quando il file JSON nel repository cambia, una pipeline CI/CD lo importa nell'istanza target. Quando un developer vuole modificare un workflow esistente, lo esporta dalla piattaforma di dev, committa il diff e apre una PR.

La terza implicazione e che la review del codice diventa review del workflow. Reviewer competenti devono leggere un file Blueprint Make o un export n8n e capire cosa fa, individuare le mappature errate, segnalare i nodi senza error handling. Questo richiede formazione e convenzioni di naming rigorose.

### Strategie di Versioning per Piattaforma

Ogni piattaforma offre meccanismi diversi, con livelli di maturita molto eterogenei.

#### Zapier

Zapier mantiene una **versions history** automatica per ogni Zap. Ad ogni salvataggio significativo, la piattaforma crea una snapshot accessibile dalla sezione "Versions" del Zap. Il rollback e manuale: dall'interfaccia si seleziona una versione precedente e si attiva. La history non e illimitata (tipicamente le ultime 30 versioni nei piani Team e Company) e non offre diff visivi efficaci tra versioni.

Le limitazioni operative sono importanti: non esiste API ufficiale per esportare versioni programmaticamente, non c'e supporto nativo per branch o ambienti separati (devi creare Zap distinti per dev/prod e tenerli sincronizzati a mano), non c'e webhook che notifichi le modifiche. La **Zapier Manager API** -- introdotta come parte di Zapier for Companies -- permette gestione programmatica di Zap (attivazione/disattivazione, lettura status), ma non un export pulito in JSON.

La pratica raccomandata su Zapier e: usare la versions history come safety net di breve termine, ma per un versioning serio mantenere uno screenshot/export manuale settimanale dei Zap critici archiviato in un repository documentale, e duplicare i Zap per ambiente con suffisso `_dev`, `_staging`, `_prod`.

#### Make (ex Integromat)

Make offre una **Scenarios history** ma e meno robusta di Zapier: traccia execuzioni e modifiche ma non offre rollback granulare a versioni storiche di scenario. Lo strumento serio per il versioning su Make e l'**export Blueprint JSON**: ogni scenario puo essere esportato come file JSON contenente la struttura completa di moduli, connessioni, mappings ed espressioni.

Il workflow Make-as-code pratico:

```bash
# Export manuale: dall'editor scenario -> ... -> Export Blueprint
# Salva il file scenario-XXXX.blueprint.json

# Import: dall'editor scenario -> ... -> Import Blueprint
# Seleziona il file e crea/sovrascrivi
```

Make espone una **REST API** (richiede piano Teams o superiore) che include endpoint per scenari (`/scenarios/{id}`, `/scenarios/{id}/blueprint`), con possibilita di GET/PUT del blueprint. Questo abilita una pipeline CI/CD reale.

Le limitazioni di Make: le connections (credenziali OAuth verso servizi esterni) non sono incluse nel blueprint -- vanno ricreate manualmente nell'ambiente target o referenziate per ID. Le data stores e webhooks hanno ID environment-specific che devono essere remappati al deploy.

#### n8n

n8n e la piattaforma piu vicina al paradigma "workflow as code" puro. Ogni workflow puo essere esportato in JSON via UI (`Workflow -> Download`) o via CLI:

```bash
# Export di un singolo workflow
n8n export:workflow --id=42 --output=workflows/42.json

# Export di tutti i workflow attivi
n8n export:workflow --all --output=workflows/

# Import
n8n import:workflow --input=workflows/42.json
```

Il file JSON contiene la struttura completa: nodi, connessioni, settings, parametri. Le credenziali sono referenziate per ID e nome ma non includono i secret values, che vanno gestiti separatamente.

n8n offre inoltre **n8n Cloud Versioning** (sui piani a pagamento): una history automatica con possibilita di confronto e rollback. Per chi self-hosta, esiste il pattern "Source Control" integrato (a partire dalle versioni 1.x) che collega l'istanza a un repository Git e gestisce push/pull dei workflow.

La configurazione tipica self-hosted con Source Control:

```bash
# Variabili di ambiente per l'integrazione Git
N8N_SOURCE_CONTROL_BRANCH=main
N8N_SOURCE_CONTROL_REPOSITORY_URL=git@github.com:azienda/n8n-workflows.git
N8N_SOURCE_CONTROL_DEFAULT_BRANCH_NAME=main
```

Dall'UI Settings -> Source Control si configura la chiave SSH e si abilita push/pull manuale o automatico.

#### Power Automate

Microsoft Power Automate e profondamente integrato con il framework **ALM (Application Lifecycle Management) di Power Platform**, basato su **Solutions**. Una Solution e un contenitore che raggruppa flow, app, tabelle Dataverse, connessioni, riferimenti environment-specific. Le Solutions sono il meccanismo nativo per spostare workflow tra ambienti.

Il flusso ALM tipico:

```
Dev environment        Build env             Test env             Prod env
   |                      |                     |                    |
   | Export unmanaged     |                     |                    |
   | Solution             |                     |                    |
   |--------------------->|                     |                    |
   |                      | Build managed       |                    |
   |                      | Solution            |                    |
   |                      |-------------------->|                    |
   |                      |                     | Validate, UAT      |
   |                      |                     |------------------->|
   |                      |                     |                    | Import managed
```

La **Power Platform CLI (`pac`)** automatizza tutto:

```bash
# Esporta solution dall'ambiente dev
pac solution export --path ./MySolution.zip --name MySolution --managed false

# Importa nell'ambiente target
pac solution import --path ./MySolution_managed.zip --environment https://target.crm.dynamics.com

# Pack/Unpack di una solution per source control
pac solution unpack --zipfile MySolution.zip --folder ./src/MySolution
pac solution pack --folder ./src/MySolution --zipfile MySolution.zip
```

Il source control diventa pratico unpackando la solution in una struttura di file (XML, JSON) che e diff-friendly e committabile in Git. Microsoft fornisce GitHub Actions ufficiali (`microsoft/powerplatform-actions`) che incapsulano `pac` per pipeline CI/CD complete.

I **Connection References** e le **Environment Variables** in Power Platform sono il meccanismo per disaccoppiare configurazioni environment-specific (URL endpoint, tenant ID, credenziali) dalla logica del flow, permettendo che una stessa solution funzioni in dev, test e prod cambiando solo i valori dei riferimenti.

---

## Guida Pratica

### Repository Git Dedicato per Automazioni

La fondazione del versioning serio e un repository Git dedicato che ospita tutti i workflow come codice. Mescolare workflow con codice applicativo e una scelta possibile per progetti molto piccoli, ma per organizzazioni con piu di una manciata di automazioni il repository dedicato (`automations/`) e nettamente preferibile.

#### Struttura Cartelle Raccomandata

```
automations/
├── README.md                          # Overview del repo, conventions, owner
├── CHANGELOG.md                       # Changelog aggregato dei rilasci
├── .github/
│   └── workflows/
│       ├── validate.yml               # CI: validazione su PR
│       ├── deploy-staging.yml         # CD: deploy su staging
│       └── deploy-prod.yml            # CD: deploy su prod (manuale)
├── docs/
│   ├── adr/                           # Architecture Decision Records
│   │   ├── 0001-piattaforma-target.md
│   │   └── 0002-strategia-multi-ambiente.md
│   └── runbooks/
│       └── rollback-procedure.md
├── n8n/
│   ├── dev/
│   │   ├── FIN-fatture-pa-sdi.json
│   │   ├── FIN-fatture-pa-sdi.README.md
│   │   ├── HR-onboarding-dipendente.json
│   │   └── HR-onboarding-dipendente.README.md
│   ├── staging/
│   └── prod/
├── make/
│   ├── dev/
│   │   ├── CRM-sync-hubspot-zoho.blueprint.json
│   │   └── CRM-sync-hubspot-zoho.README.md
│   ├── staging/
│   └── prod/
├── zapier/
│   └── exports/
│       ├── 2026-04-15-zap-lead-capture.json
│       └── ...
├── power-automate/
│   ├── solutions/
│   │   └── FinanceAutomation/
│   │       ├── src/                   # Unpacked solution
│   │       └── solution.xml
│   └── environment-variables/
│       ├── dev.json
│       ├── staging.json
│       └── prod.json
├── tests/
│   ├── contracts/                     # Pact contracts per API esterne
│   └── data/                          # Dataset sintetici per test
└── scripts/
    ├── export-all-n8n.sh
    ├── validate-blueprint.py
    └── deploy.sh
```

La separazione `dev/`, `staging/`, `prod/` per piattaforma evita confusione e permette pipeline CI/CD distinte per ambiente. La cartella `docs/adr/` e cruciale per tracciare decisioni architettoniche con il pattern Architecture Decision Records di Michael Nygard.

#### Convenzioni Naming

Convenzione raccomandata per i file:

```
[DOMINIO]-[descrizione-breve-kebab-case].[ext]

Esempi:
FIN-fatture-pa-sdi.json
HR-onboarding-dipendente.json
CRM-sync-hubspot-zoho.blueprint.json
SUP-ticket-zendesk-jira.json
```

Il prefisso dominio (`FIN`, `HR`, `CRM`, `SUP`, `OPS`, `MKT`) accelera la navigazione e il routing degli alert verso il team owner corretto.

#### README per Workflow

Ogni workflow deve avere un README accanto al file JSON che documenta lo scopo, i trigger, gli input/output, le credenziali necessarie, l'owner e la procedura di rollback. Esempio:

```markdown
# FIN-fatture-pa-sdi

## Scopo
Trasmette fatture elettroniche generate dal gestionale interno verso lo SDI
dell'Agenzia delle Entrate via API SdI.

## Trigger
Webhook POST `/webhook/fatture-nuove` chiamato dal gestionale dopo emissione.

## Input
JSON conforme a schema FatturaPA v1.2.2.

## Output
- Notifica di accettazione/scarto SdI
- Aggiornamento stato fattura nel gestionale
- Notifica Slack #finance-alerts in caso di scarto

## Credenziali
- `sdi-api-prod`: certificato qualificato per autenticazione SdI
- `gestionale-api`: token per callback verso gestionale
- `slack-webhook-finance`: webhook canale alert

## Owner
Marco Bianchi (marco.bianchi@azienda.it) -- Finance Automation Team

## Rollback Procedure
Vedi `docs/runbooks/rollback-procedure.md`. Workflow ID n8n: 42.

## SLA
- RTO: 15 minuti
- RPO: 5 minuti (queue retention)
```

#### Commit Message Convenzionali

Adozione di **Conventional Commits** (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`) per messaggi di commit chiari e per generare changelog automatici:

```
feat(n8n): aggiunge workflow FIN-fatture-pa-sdi
fix(make): corregge mapping codice fiscale in CRM-sync-hubspot-zoho
refactor(n8n): estrae sub-workflow notifica-slack
docs(adr): aggiunge ADR-0003 scelta queue mode Redis
chore(deps): aggiorna n8n da 1.45 a 1.46 in compose.prod.yml
```

### Branch Strategy: GitFlow vs Trunk-Based

La scelta della branch strategy ha impatto operativo significativo. Per workflow di automazione, due approcci sono validi.

#### GitFlow (semplificato)

```
main             ────────●────────────●────────────●─── (prod)
                        ↑            ↑            ↑
release         ───────●─────────────●─────────── ●─── (staging)
                      ↑              ↑            ↑
develop         ●────●────●────●────●────●────●──●─── (dev)
                ↑    ↑                   ↑
feature/x       ●────┘                   |
feature/y                ●───────────────┘
```

Adatto a organizzazioni con cicli di rilascio strutturati (es. release settimanali o quindicinali), team multi-developer, ambienti staging stabili. La complessita aggiuntiva si paga in overhead di merge.

#### Trunk-Based Development

```
main             ●────●────●────●────●────●────●──── (continuous deploy)
                 ↑    ↑              ↑    ↑
feature/x        ●────┘              |    |
feature/y                            ●────┘
```

Adatto a team piccoli (1-3 developer), automazioni a basso rischio o con feature flags robusti, deploy frequenti. Richiede CI/CD molto solida e pratica disciplinata di feature flagging per nascondere lavoro in corso.

Per la maggior parte delle PMI italiane con un team di automazione di 1-2 persone, **trunk-based con deploy manuale a prod** e la scelta pragmatica: si lavora su `main`, ogni commit triggera deploy automatico in dev, deploy in staging triggerato da tag, deploy in prod richiede approval manuale da un secondo paio di occhi.

### Pipeline CI/CD per Workflow

Una pipeline CI/CD per workflow ha tre stadi essenziali: **validate** (sintassi, schema, naming), **test** (workflow test, contract test), **deploy** (importa nell'istanza target).

#### Esempio GitHub Actions per n8n

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy n8n Workflows to Staging

on:
  push:
    branches: [main]
    paths:
      - 'n8n/staging/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install n8n CLI
        run: npm install -g n8n

      - name: Validate JSON syntax
        run: |
          for f in n8n/staging/*.json; do
            jq empty "$f" || exit 1
          done

      - name: Validate workflow schema
        run: python scripts/validate-n8n-workflow.py n8n/staging/

      - name: Check naming convention
        run: |
          for f in n8n/staging/*.json; do
            basename=$(basename "$f" .json)
            if ! echo "$basename" | grep -qE '^[A-Z]{3}-[a-z0-9-]+$'; then
              echo "ERRORE: $f non rispetta naming [DOMINIO]-[descrizione]"
              exit 1
            fi
          done

  deploy:
    needs: validate
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Setup SSH for n8n staging
        uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.N8N_STAGING_SSH_KEY }}

      - name: Deploy via n8n CLI over SSH
        env:
          N8N_HOST: ${{ secrets.N8N_STAGING_HOST }}
          N8N_USER: ${{ secrets.N8N_STAGING_USER }}
        run: |
          for f in n8n/staging/*.json; do
            scp "$f" "$N8N_USER@$N8N_HOST:/tmp/"
            ssh "$N8N_USER@$N8N_HOST" "n8n import:workflow --input=/tmp/$(basename $f) --separate"
          done

      - name: Smoke test
        run: bash scripts/smoke-test-staging.sh

      - name: Notify Slack
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Deploy n8n staging: ${{ job.status }} -- commit ${{ github.sha }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_DEPLOYS }}
```

#### Esempio per Make tramite REST API

```yaml
# .github/workflows/deploy-make-prod.yml
name: Deploy Make Scenarios to Prod

on:
  workflow_dispatch:
    inputs:
      scenario:
        description: 'Nome scenario (es. CRM-sync-hubspot-zoho)'
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://eu1.make.com/scenarios
    steps:
      - uses: actions/checkout@v4

      - name: Upload Blueprint via Make API
        env:
          MAKE_API_TOKEN: ${{ secrets.MAKE_API_TOKEN_PROD }}
          MAKE_TEAM_ID: ${{ secrets.MAKE_TEAM_ID_PROD }}
          SCENARIO_NAME: ${{ inputs.scenario }}
        run: |
          BLUEPRINT="make/prod/${SCENARIO_NAME}.blueprint.json"
          SCENARIO_ID=$(jq -r '.metadata.scenarioId' "$BLUEPRINT")

          curl -X PUT "https://eu1.make.com/api/v2/scenarios/${SCENARIO_ID}/blueprint" \
            -H "Authorization: Token ${MAKE_API_TOKEN}" \
            -H "Content-Type: application/json" \
            --data-binary "@${BLUEPRINT}"
```

Il deploy in prod e dietro `workflow_dispatch` (manuale) e usa l'**environment protection rules** di GitHub per richiedere approval di un reviewer.

### Esempio End-to-End: Deploy n8n Fatturazione PA

Scenario reale: una PMI italiana ha un workflow n8n che riceve fatture dal gestionale, le valida contro lo schema FatturaPA, le firma e le invia allo SDI. Il flusso di deploy completo dev -> prod:

**Giorno 1, Sviluppatore in dev.**

```bash
# Lavora sull'istanza n8n dev (porta 5678)
# Aggiunge un nodo "Validate XSD" prima dell'invio
# Salva nel workflow ID 42 sull'istanza dev
```

**Export e commit.**

```bash
# Sulla macchina dev
n8n export:workflow --id=42 --output=/tmp/FIN-fatture-pa-sdi.json

# Sulla macchina dello sviluppatore
cd ~/repos/automations
cp /tmp/FIN-fatture-pa-sdi.json n8n/dev/

git checkout -b feat/validazione-xsd-fatture
git add n8n/dev/FIN-fatture-pa-sdi.json
git commit -m "feat(n8n): aggiunge validazione XSD pre-invio SDI

Aggiunto nodo Function che valida la fattura contro lo schema XSD
FatturaPA v1.2.2 prima della trasmissione. Riduce gli scarti SDI
da errori di formato.

Refs: TICKET-1342"
git push -u origin feat/validazione-xsd-fatture
```

**Pull request e review.**

Sviluppatore apre PR su GitHub. Reviewer (collega senior) verifica:
1. Il diff JSON e leggibile e contenuto.
2. Il nodo Function ha error handling.
3. Il README accanto al workflow e aggiornato.
4. Non ci sono credenziali hardcoded nel JSON.

CI esegue automaticamente: validazione JSON, validazione schema, naming check. Tutto verde, merge in `main`.

**Deploy automatico in dev.**

GitHub Actions triggera `deploy-dev.yml`, importa il file in n8n dev, esegue smoke test che invia una fattura di test allo SDI di test.

**Promote a staging.**

Sviluppatore copia il file da `n8n/dev/` a `n8n/staging/` (o usa uno script di promote che remappa le credenziali staging):

```bash
./scripts/promote.sh n8n FIN-fatture-pa-sdi dev staging
git add n8n/staging/FIN-fatture-pa-sdi.json
git commit -m "chore(n8n): promote FIN-fatture-pa-sdi a staging"
git push
```

GitHub Actions deploya in staging. QA esegue test funzionali con dataset realistico.

**Promote a prod.**

Dopo validazione QA (3-5 giorni in staging per workflow critici), promote a prod:

```bash
./scripts/promote.sh n8n FIN-fatture-pa-sdi staging prod
git add n8n/prod/FIN-fatture-pa-sdi.json
git commit -m "chore(n8n): promote FIN-fatture-pa-sdi a prod"
git push
```

Il deploy in prod richiede approval manuale (configurato via GitHub Environments). Reviewer approva, deploy parte, smoke test post-deploy verifica che il workflow risponda al webhook di test. Notifica Slack `#finance-deploys`.

**Tag di rilascio.**

```bash
git tag -a v2026.04.22-fatture-xsd -m "Validazione XSD pre-SDI"
git push --tags
```

Il tag rende immediatamente identificabile lo stato di prod a quella data.

---

## Configurazione

### Multi-Ambiente: Dev, Staging, Prod

La separazione fisica e logica degli ambienti e prerequisito per ogni strategia di versioning seria. La configurazione tipica per una PMI:

| Ambiente | Scopo | Dati | Credenziali | Accesso |
|----------|-------|------|-------------|---------|
| **dev** | Sviluppo libero | Sintetici, fake | Sandbox API esterne | Sviluppatori |
| **staging** | Validazione pre-prod | Anonimizzati realistici | Sandbox o produzione read-only | Sviluppatori + QA |
| **prod** | Produzione | Reali | Produzione | Operatori, lettura per dev |

Per n8n self-hosted, tre istanze separate (Docker Compose distinti, magari sullo stesso host con porte diverse o su VPS separati):

```yaml
# docker-compose.dev.yml
services:
  n8n-dev:
    image: n8nio/n8n:1.46.0
    ports: ["5678:5678"]
    environment:
      - N8N_HOST=n8n-dev.azienda.it
      - WEBHOOK_URL=https://n8n-dev.azienda.it/
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_DATABASE=n8n_dev
    volumes:
      - n8n_dev_data:/home/node/.n8n
```

Variazioni equivalenti per `staging` e `prod`, con database e volumi separati.

Per Make e Zapier, dato che sono SaaS multi-tenant, "ambiente" significa workspace/team distinti (Make: due team account; Zapier: account team distinti o folder con suffisso `_dev`/`_prod`).

Per Power Automate, l'isolamento e nativo via **Power Platform Environments** (`Default`, `MyOrg-Dev`, `MyOrg-Test`, `MyOrg-Prod`), ognuno con la sua istanza Dataverse e le sue connection references.

### Secrets Management

Le credenziali (API key, token OAuth, certificati) **non devono mai essere committate in Git**. Le strategie:

#### Secret Manager Cloud-Native

- **AWS Secrets Manager** o **AWS Systems Manager Parameter Store**
- **Azure Key Vault**
- **Google Secret Manager**
- **HashiCorp Vault** (self-hosted o HCP)

Pattern: il workflow legge il secret a runtime via API o variabile d'ambiente iniettata. Per n8n, le credenziali sono cifrate nel database con `N8N_ENCRYPTION_KEY`; il valore della encryption key e a sua volta in Vault.

```bash
# All'avvio di n8n in prod, recupera la encryption key da Vault
export N8N_ENCRYPTION_KEY=$(vault kv get -field=key secret/n8n/prod/encryption)
docker compose up -d
```

#### GitHub Secrets per CI/CD

Per i token utilizzati dalle pipeline (n8n SSH key, Make API token, Power Platform service principal), usare **GitHub Secrets** scoped per environment:

```
Settings -> Environments -> production -> Add secret
  N8N_PROD_SSH_KEY = (chiave privata SSH)
  MAKE_API_TOKEN_PROD = (token API Make prod)
  POWER_PLATFORM_TENANT_ID = (tenant Azure AD)
  POWER_PLATFORM_CLIENT_SECRET = (client secret service principal)
```

#### Anti-Pattern da Evitare

- **NO**: `.env` committato in Git anche se "solo per dev".
- **NO**: token in chiaro nei file Blueprint Make o JSON n8n.
- **NO**: condivisione di credenziali via Slack o email.
- **NO**: account di servizio condiviso tra dev e prod.

### Blue/Green e Canary Release

Per workflow critici (es. fatturazione SdI, sincronizzazione anagrafica clienti), il deploy big-bang del nuovo workflow su prod e rischioso. Due pattern mitigano il rischio.

#### Blue/Green Deploy

Si mantengono due versioni in produzione in parallelo: la "blue" (corrente) e la "green" (nuova). Il traffico viene switched dalla blue alla green quando la green e validata.

Implementazione concreta su n8n:
1. Workflow `FIN-fatture-pa-sdi` (blue) attivo, ascolta su webhook `/webhook/fatture-nuove`.
2. Si crea workflow `FIN-fatture-pa-sdi-v2` (green), che ascolta su webhook `/webhook/fatture-nuove-v2` ma e disattivato.
3. Si attiva la green e si esegue traffico di test verso `/webhook/fatture-nuove-v2`.
4. Quando la green e validata, si modifica il reverse proxy (nginx/Traefik) per redirigere `/webhook/fatture-nuove` -> `/webhook/fatture-nuove-v2`.
5. Switch atomico, blue rimane disattivata come fallback.
6. Dopo 7 giorni di osservazione senza problemi, blue viene eliminata.

Esempio configurazione nginx:

```nginx
# Blue (corrente) -> /webhook/fatture-nuove
# Green (nuova) -> /webhook/fatture-nuove-v2

# Per switch atomico, basta cambiare il proxy_pass e ricaricare
location /webhook/fatture-nuove {
    # proxy_pass http://n8n/webhook/fatture-nuove;       # Blue
    proxy_pass http://n8n/webhook/fatture-nuove-v2;      # Green
}
```

```bash
# Switch
sudo nginx -t && sudo systemctl reload nginx
```

#### Canary Release

Si esegue un rollout graduale: una percentuale crescente di traffico viene routata alla nuova versione mentre la maggioranza continua sulla vecchia.

Pattern con feature flag esterno (es. LaunchDarkly o un semplice toggle in Redis):

```javascript
// Nel workflow n8n, primo nodo Function
const useNewVersion = $('Redis').first().json.canary_percentage > Math.random() * 100;
if (useNewVersion) {
  // Routing al sub-workflow nuovo
  return [{ json: { ...$json, version: 'v2' } }];
} else {
  // Routing al sub-workflow vecchio
  return [{ json: { ...$json, version: 'v1' } }];
}
```

Si imposta `canary_percentage = 10` -> 10% del traffico va alla v2. Si monitora error rate, latenza, business metrics. Dopo 24h senza anomalie, si sale a 25%, 50%, 100%.

### Schema e Contract Versioning

I workflow consumano e producono dati strutturati. Quando lo schema cambia, le conseguenze si propagano a tutti i consumatori.

#### Backward-Compatible vs Breaking Changes

| Tipo Cambio | Compatibile? | Esempi |
|-------------|--------------|--------|
| Aggiunta campo opzionale | Si | Aggiungere `data_scadenza` opzionale al payload fattura |
| Rinomina campo | No (breaking) | `cliente_id` -> `customer_id` |
| Rimozione campo | No (breaking) | Rimuovere `note_aggiuntive` |
| Restrizione enum | No | `stato in ['attivo', 'sospeso']` -> solo `'attivo'` |
| Estensione enum | Si | Aggiunta valore `'archiviato'` |
| Cambio tipo | No | `quantita: int` -> `quantita: decimal` |

#### Strategia di Versioning API

Per workflow esposti come API (es. webhook n8n consumati da gestionali esterni), il versioning espliito via header o URL e mandatory:

```
POST /webhook/v1/fatture-nuove           # Versione 1, deprecata
POST /webhook/v2/fatture-nuove           # Versione 2, corrente
```

Oppure via header:

```
POST /webhook/fatture-nuove
API-Version: 2
```

#### Deprecation Policy

Una policy raccomandata: **90 giorni di overlap** tra v1 e v2 dopo l'annuncio della deprecazione. Durante l'overlap:
- v1 risponde con header `Deprecation: true` e `Sunset: <data-rimozione>`.
- Notifica via email a tutti i consumatori noti (mantenere lista).
- Log warning su ogni chiamata v1 per identificare consumatori sconosciuti.

Dopo 90 giorni, v1 viene rimossa.

### Testing Pre-Deploy

Tre livelli di testing prima di deploy in prod.

#### Test Funzionali del Workflow

Workflow di test che invocano il workflow target con dataset sintetici e verificano output. Per n8n si puo creare un secondo workflow `TEST-FIN-fatture-pa-sdi` che:
1. Genera una fattura sintetica.
2. Invoca via HTTP Request il webhook target.
3. Verifica la risposta.
4. Logga risultato in un canale Slack di test.

#### Contract Test su API Esterne

Le API esterne (SdI, banking, gestionali SaaS) cambiano nel tempo. **Pact** e il framework di riferimento per contract testing:

```javascript
// pact-test.js -- verifica che SDI risponda come ci aspettiamo
const { Pact } = require('@pact-foundation/pact');
const provider = new Pact({
  consumer: 'n8n-fatture-workflow',
  provider: 'sdi-agenzia-entrate',
});

describe('SDI invoice submission', () => {
  it('returns acceptance notification', async () => {
    await provider.addInteraction({
      uponReceiving: 'a valid FatturaPA submission',
      withRequest: {
        method: 'POST',
        path: '/sdi/submit',
        body: { /* fattura valida */ },
      },
      willRespondWith: {
        status: 200,
        body: { stato: 'accettata', identificativo: 'SDI-2026-XXXX' },
      },
    });
    // ... esegue chiamata e verifica
  });
});
```

I contract test girano in CI per ogni PR, segnalando se l'API esterna ha cambiato schema.

#### Smoke Test Post-Deploy

Subito dopo il deploy in prod, una sequenza di chiamate base verifica che il workflow risponda. Esempio bash:

```bash
#!/bin/bash
# scripts/smoke-test-prod.sh

set -e

WEBHOOK_URL="https://n8n.azienda.it/webhook/fatture-nuove"
TEST_PAYLOAD='{"test": true, "fattura": { ... }}'

response=$(curl -sS -o /dev/null -w "%{http_code}" \
  -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD")

if [[ "$response" != "200" ]]; then
  echo "SMOKE TEST FAILED: HTTP $response"
  exit 1
fi

echo "Smoke test OK"
```

In caso di fallimento, la pipeline triggera **rollback automatico**.

---

## Best Practices

### Documentation as Code

#### Architecture Decision Records

Ogni decisione architettonica significativa (scelta piattaforma, pattern multi-tenancy, strategia rollback) viene documentata come ADR in `docs/adr/`. Template:

```markdown
# ADR-0003: Adozione di n8n self-hosted in queue mode

## Status
Accepted (2026-03-15)

## Context
Volume di esecuzioni cresciuto da 5k/mese a 50k/mese. Single-instance
n8n inizia a saturare CPU durante picchi. Latenza webhook degrada.

## Decision
Migriamo a queue mode con worker dedicati e Redis come broker.

## Consequences
+ Scalabilita orizzontale dei worker
+ Resilienza: webhook accettati anche se worker down
- Complessita operativa: 3 servizi invece di 1
- Costo: +1 VPS Redis (€10/mese) + 1 worker VPS (€20/mese)

## Alternatives considered
- Verticale: aumentare risorse del singolo nodo. Scartato perche tetto.
- Migrare a n8n Cloud: scartato per costo a 50k esecuzioni (€450/mese).
```

#### Changelog Automatico

Con Conventional Commits, si genera changelog automaticamente:

```bash
# package.json
"scripts": {
  "changelog": "conventional-changelog -p angular -i CHANGELOG.md -s"
}

npm run changelog
```

Il file `CHANGELOG.md` viene aggiornato ad ogni release con la lista dei `feat:`, `fix:`, `BREAKING CHANGE:`.

### Disaster Recovery

#### Backup Giornaliero

Per ogni piattaforma, backup giornaliero degli export oltre al backup del database:

```bash
# scripts/backup-daily.sh
#!/bin/bash
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/backups/automations/$DATE"
mkdir -p "$BACKUP_DIR"

# Export workflow n8n via CLI
docker exec n8n-prod n8n export:workflow --all \
  --output="/tmp/n8n-export-$DATE.json"
docker cp n8n-prod:/tmp/n8n-export-$DATE.json "$BACKUP_DIR/"

# Export Make scenarios via API
for scenario_id in $(curl -sS -H "Authorization: Token $MAKE_TOKEN" \
  "https://eu1.make.com/api/v2/scenarios?teamId=$TEAM_ID" \
  | jq -r '.scenarios[].id'); do
    curl -sS -H "Authorization: Token $MAKE_TOKEN" \
      "https://eu1.make.com/api/v2/scenarios/$scenario_id/blueprint" \
      > "$BACKUP_DIR/make-scenario-$scenario_id.json"
done

# Sync su S3 con versioning attivo
aws s3 sync "$BACKUP_DIR" "s3://azienda-backups/automations/$DATE/"

# Retention: cancella backup locali > 7 giorni
find /backups/automations -mindepth 1 -maxdepth 1 -mtime +7 -exec rm -rf {} +
```

S3 con versioning attivo + lifecycle policy (transizione a Glacier dopo 30gg, eliminazione dopo 1 anno) e la combinazione cost-effective per retention lunga.

#### Runbook di Ripristino

Documento operativo step-by-step per ricostruire l'ambiente da zero. Esempio struttura:

```markdown
# Runbook: Ripristino n8n Prod da Backup

## Prerequisiti
- Accesso SSH al VPS di backup
- Credenziali AWS S3
- N8N_ENCRYPTION_KEY archiviata in Vault

## Procedura

### 1. Ripristino database (15 min)
```bash
aws s3 cp s3://azienda-backups/automations/2026-04-22/n8n-db.dump .
pg_restore -d n8n_prod n8n-db.dump
```

### 2. Avvio istanza n8n (5 min)
```bash
export N8N_ENCRYPTION_KEY=$(vault kv get -field=key secret/n8n/prod/encryption)
docker compose -f docker-compose.prod.yml up -d
```

### 3. Validazione (10 min)
```bash
curl https://n8n.azienda.it/healthz
./scripts/smoke-test-prod.sh
```

## RTO target: 30 minuti
## RPO target: 24 ore (backup giornaliero)
```

#### RTO e RPO

| Workflow | RTO | RPO | Strategia |
|----------|-----|-----|-----------|
| FIN-fatture-pa-sdi | 15min | 5min | Queue mode + DB replica |
| HR-onboarding | 4h | 24h | Backup giornaliero |
| MKT-newsletter | 24h | 24h | Backup giornaliero |

Workflow con RTO basso giustificano costi di alta disponibilita; workflow tolleranti possono restare su backup base.

### Procedure di Rollback Sicuro

#### Criteri Trigger di Rollback

Rollback automatico quando, nei primi 30 minuti post-deploy:
- **Error rate** > 5% delle esecuzioni
- **Latenza p95** > 2x baseline
- **Smoke test** fallisce
- **Business metric critica** (es. fatture accettate da SDI) crolla > 50%

Rollback manuale quando:
- Bug funzionale segnalato da utente.
- Decisione di product per qualunque motivo.

#### Rollback Automatico in Pipeline

```yaml
# Estratto deploy-prod.yml
- name: Smoke test post-deploy
  id: smoke
  continue-on-error: true
  run: ./scripts/smoke-test-prod.sh

- name: Rollback se smoke fallisce
  if: steps.smoke.outcome == 'failure'
  run: |
    PREV_TAG=$(git describe --tags --abbrev=0 HEAD~1)
    git checkout "$PREV_TAG" -- n8n/prod/
    ./scripts/deploy-n8n.sh prod
    # Notifica
    curl -X POST "$SLACK_WEBHOOK" \
      -d '{"text":"ROLLBACK eseguito a '"$PREV_TAG"'"}'
    exit 1
```

#### Rollback Manuale Step-by-Step

```bash
# 1. Identificare la versione precedente stabile
git log --oneline n8n/prod/FIN-fatture-pa-sdi.json | head -5

# 2. Checkout della versione precedente
git checkout <commit-precedente> -- n8n/prod/FIN-fatture-pa-sdi.json

# 3. Importare nell'istanza n8n prod
scp n8n/prod/FIN-fatture-pa-sdi.json prod-server:/tmp/
ssh prod-server "n8n import:workflow --input=/tmp/FIN-fatture-pa-sdi.json"

# 4. Verifica
./scripts/smoke-test-prod.sh

# 5. Commit del rollback come nuovo commit (NON force-push)
git checkout main
git commit -m "fix(n8n): rollback FIN-fatture-pa-sdi a <commit-precedente>

Bug introdotto in <commit-buggy>: validazione XSD rejectava fatture
con codice destinatario di 7 caratteri (validi).

Refs: INCIDENT-0042"
git push
```

#### Esempio: Rollback Make Scenario CRM HubSpot

Scenario reale: dopo deploy di una nuova versione dello scenario `CRM-sync-hubspot-zoho`, il sync inizia a duplicare contatti. Rilevato dopo 2 ore.

```bash
# 1. Disattivazione immediata via API Make
curl -X POST "https://eu1.make.com/api/v2/scenarios/12345/stop" \
  -H "Authorization: Token $MAKE_TOKEN"

# 2. Identificare blueprint precedente in Git
cd ~/repos/automations
git log --oneline make/prod/CRM-sync-hubspot-zoho.blueprint.json
# Output: abc1234 feat(make): nuova logica dedup
#         def5678 fix(make): correzione mapping email
#         ghi9012 chore: setup iniziale

# 3. Restore versione precedente (def5678)
git checkout def5678 -- make/prod/CRM-sync-hubspot-zoho.blueprint.json

# 4. Upload via Make API
curl -X PUT "https://eu1.make.com/api/v2/scenarios/12345/blueprint" \
  -H "Authorization: Token $MAKE_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary "@make/prod/CRM-sync-hubspot-zoho.blueprint.json"

# 5. Riattivazione
curl -X POST "https://eu1.make.com/api/v2/scenarios/12345/start" \
  -H "Authorization: Token $MAKE_TOKEN"

# 6. Cleanup duplicati creati durante il bug
psql -d crm_prod -f scripts/cleanup-hubspot-duplicates.sql

# 7. Post-mortem
# Nuovo file docs/postmortems/2026-04-22-hubspot-dedup-incident.md
```

---

## Troubleshooting

### Diff JSON Illeggibile

**Problema**: il diff Git di un export n8n e di centinaia di righe perche ogni save cambia `updatedAt`, `versionId`, `meta`.

**Soluzione**: script di "normalizzazione" pre-commit che rimuove campi non significativi:

```python
# scripts/normalize-n8n-export.py
import json, sys

VOLATILE_FIELDS = ['updatedAt', 'versionId', 'meta', 'pinData']

def normalize(workflow):
    for f in VOLATILE_FIELDS:
        workflow.pop(f, None)
    # Sort keys per diff stabile
    return json.dumps(workflow, indent=2, sort_keys=True)

if __name__ == '__main__':
    for path in sys.argv[1:]:
        with open(path) as f:
            wf = json.load(f)
        with open(path, 'w') as f:
            f.write(normalize(wf))
```

Hook `pre-commit` lo esegue su ogni `*.json` modificato.

### Credenziali Non Trovate Dopo Import

**Problema**: dopo `n8n import:workflow`, l'esecuzione fallisce con "Credential not found".

**Causa**: il JSON referenzia credenziali per ID, ma gli ID di credenziali non sono portabili tra istanze.

**Soluzione**: usare riferimenti per **nome** anziche ID. n8n moderni supportano `credentialsByName` nei nodi:

```json
{
  "credentials": {
    "httpBasicAuth": {
      "id": "1",
      "name": "sdi-api-prod"
    }
  }
}
```

In fase di import, sostituire `id` con il valore corretto sull'istanza target via script o usare il pattern di n8n Source Control che gestisce mappatura automatica.

### Make Connection Reference Broken

**Problema**: import blueprint Make in nuovo team -- le connessioni OAuth non esistono e lo scenario non parte.

**Soluzione**: pre-creare le connessioni nell'ambiente target con stesso nome, e usare il pattern di **connection mapping**:

```bash
# Pre-deploy: lista connection ID nel blueprint
jq '.. | objects | select(.connection?) | .connection' \
  make/prod/CRM-sync.blueprint.json

# Recupera ID connessioni equivalenti nell'ambiente target
curl -H "Authorization: Token $MAKE_TOKEN" \
  "https://eu1.make.com/api/v2/connections?teamId=$TARGET_TEAM" | jq

# Sed di sostituzione ID nel blueprint prima di upload
sed -i 's/"connection":12345/"connection":67890/g' \
  make/prod/CRM-sync.blueprint.json
```

### Power Automate Solution Import Fallisce

**Problema**: `pac solution import` fallisce con "Connection reference X cannot be resolved".

**Soluzione**: prima dell'import, creare le **Connection References** e impostare i valori delle **Environment Variables** nel target environment:

```bash
pac solution import \
  --path MySolution_managed.zip \
  --environment https://prod.crm.dynamics.com \
  --connection-references "shared_sharepoint=conn-prod-sp-001,shared_outlook=conn-prod-out-002" \
  --settings-file environment-variables/prod.json
```

### Rollback Blocca Esecuzioni in Coda

**Problema**: dopo rollback, le esecuzioni in coda (queue mode) generate dalla versione buggy continuano a fallire.

**Soluzione**: prima del rollback, drenare la coda:

```bash
# Pause workflow nel master
curl -X POST "http://n8n-master:5678/rest/workflows/42/deactivate"

# Attendi che la coda si svuoti (max 5 min)
while [ "$(redis-cli LLEN bull:n8n:wait)" != "0" ]; do
  sleep 10
done

# Esegui rollback
n8n import:workflow --input=FIN-fatture-pa-sdi.json

# Riattiva
curl -X POST "http://n8n-master:5678/rest/workflows/42/activate"
```

### Schema Drift Tra Ambienti

**Problema**: i workflow in dev/staging/prod hanno schema diverso perche modifiche manuali sono state fatte direttamente in editor di prod.

**Soluzione**: introdurre **drift detection** in CI:

```yaml
# .github/workflows/drift-detection.yml
name: Daily Drift Detection
on:
  schedule:
    - cron: '0 6 * * *'  # ogni giorno alle 06:00 UTC

jobs:
  check-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Export current prod workflows
        run: |
          ssh prod-server "n8n export:workflow --all --output=/tmp/current.json"
          scp prod-server:/tmp/current.json /tmp/
      - name: Diff against repo
        run: |
          python scripts/normalize-n8n-export.py /tmp/current.json
          if ! diff -q /tmp/current.json n8n/prod/; then
            echo "DRIFT RILEVATO"
            # Notifica
            curl -X POST "$SLACK_WEBHOOK" -d '{"text":"Drift n8n prod"}'
            exit 1
          fi
```

---

## Riferimenti

### Documentazione Ufficiale

- **n8n Source Control Docs**: documentazione su integrazione Git, branch, push/pull workflow.
- **n8n CLI Reference**: comandi `import:workflow`, `export:workflow`, `execute`.
- **Make API Reference**: endpoint `/scenarios`, `/scenarios/{id}/blueprint`.
- **Zapier Manager API**: gestione Zap programmatica per piani Company.
- **Power Platform ALM Guide**: framework completo per source control e CI/CD su Power Automate.
- **Power Platform CLI Reference (`pac`)**: comandi solution, environment, deploy.
- **Microsoft Power Platform GitHub Actions**: action ufficiali per CI/CD Power Apps/Automate.

### Standard e Specifiche

- **Conventional Commits 1.0.0**: spec per messaggi di commit semantici.
- **Architecture Decision Records (Michael Nygard)**: pattern per tracciare decisioni.
- **Pact Specification**: contract testing tra consumer e provider.
- **Semantic Versioning 2.0.0**: schema MAJOR.MINOR.PATCH.

### Strumenti

- **conventional-changelog**: generatore changelog da Conventional Commits.
- **HashiCorp Vault**: secret management on-prem o HCP cloud.
- **Pact Broker**: hub per contract testing distribuito.
- **GitHub Actions / GitLab CI / Jenkins**: piattaforme CI/CD.
- **act**: esegue GitHub Actions in locale per testing.

### Letture Consigliate

- "Continuous Delivery" -- Jez Humble, David Farley.
- "Release It!" -- Michael Nygard (capitoli su deploy, rollback, stability patterns).
- "Accelerate" -- Forsgren, Humble, Kim (metriche DORA su deployment frequency, MTTR, change failure rate).
- "The Phoenix Project" -- Gene Kim (storia DevOps narrata).

### Comunita e Risorse

- **n8n Community Forum**: pattern condivisi su versioning e deploy.
- **Make Community**: thread su Blueprint API e CI/CD.
- **Power Platform Community**: best practice ALM.
- **r/devops, r/sysadmin** su Reddit: discussioni operative su CI/CD per workflow.

---

## Esercizi

1. **Lab — n8n in Git.** Setup repo Git con workflow JSON; pipeline GitHub Actions lint + deploy a n8n via API.
2. **Lab — rollback drill.** Deploy nuovo workflow rotto in prod; misurare tempo per detection + rollback alla versione precedente.
3. **Stretch — feature flag con LaunchDarkly.** Wrappa workflow con flag; abilita progressivamente.

## Auto-valutazione

1. Workflow as code: vantaggi.
2. Solution Power Platform: cos'e?
3. Rollback procedure: 3 step minimi.
4. Feature flag: tool comuni.
5. CI/CD per workflow: tool tipici.

## Collegamenti incrociati

- Modulo 25 (NEW) — `25-multi-environment-promotion.md`: dev → prod.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Workflow as code** | Workflow versionato come codice. |
| **Solution (Power Platform)** | Container per package + deploy. |
| **Pipeline CI/CD** | Automazione build → test → deploy. |
| **Feature flag** | Toggle runtime per abilitare feature. |
| **Rollback** | Tornare a versione precedente. |
| **Smoke test** | Test rapido post-deploy. |
| **Blue-green deploy** | Due ambienti, switch atomico. |
| **Canary deploy** | Rilascio progressivo a % utenti. |

---

## Letture e Riferimenti

- n8n — Source control and environments. https://docs.n8n.io/source-control-environments/
- Microsoft — Power Platform ALM (Application Lifecycle Management). https://learn.microsoft.com/en-us/power-platform/alm/
- Microsoft — Solution concepts in Power Platform. https://learn.microsoft.com/en-us/power-apps/maker/data-platform/solutions-overview
- GitHub — GitHub Actions workflow syntax. https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
- LaunchDarkly — Feature flags best practices. https://docs.launchdarkly.com/guides/best-practices
- Temporal — Versioning workflows. https://docs.temporal.io/develop/dotnet/versioning
- Humble, Jez; Farley, David. *Continuous Delivery*. Addison-Wesley, 2010. — Cap. 2, 5, 10 (deployment pipeline, release management).
- Forsgren, Nicole; Humble, Jez; Kim, Gene. *Accelerate*. IT Revolution, 2018. — Deployment frequency, lead time, MTTR.
