---
corso: "GitHub e Git Actions"
fase: "5 — Sicurezza"
modulo: 28
titolo: "CodeQL e GitHub Advanced Security"
versione: "CodeQL CLI 2.x / GHAS GA"
livello: "Avanzato"
prerequisiti:
  - "16-github-security-scanning"
  - "18-github-actions-avanzate"
  - "19-github-actions-ci-cd-ricette"
obiettivi:
  - "Descrivere l'architettura CodeQL: database extraction, query evaluation, SARIF output"
  - "Scrivere custom query QL per identificare pattern di vulnerabilità specifici"
  - "Configurare secret scanning con custom pattern e push protection"
  - "Abilitare e gestire GitHub Advanced Security a livello organization"
  - "Interpretare la Security Overview dashboard e prioritizzare le remediation"
tag: [codeql, ghas, sast, secret-scanning, push-protection, sarif, dependabot, code-scanning]
---

# CodeQL e GitHub Advanced Security

> **Modulo 28** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Descrivere l'architettura CodeQL: database extraction, query evaluation, SARIF output
> 2. Scrivere custom query QL per identificare pattern di vulnerabilità specifici
> 3. Configurare secret scanning con custom pattern e push protection
> 4. Abilitare e gestire GitHub Advanced Security a livello organization
> 5. Interpretare la Security Overview dashboard e prioritizzare le remediation

---

## Indice

1. [Idee guida](#idee-guida)
2. [Architettura CodeQL](#architettura-codeql)
3. [CodeQL database](#codeql-database)
4. [Il linguaggio QL](#il-linguaggio-ql)
5. [QL Packs e Query Suites](#ql-packs-e-query-suites)
6. [Setup CodeQL in GitHub Actions](#setup-codeql-in-github-actions)
7. [Custom queries](#custom-queries)
8. [Formato SARIF](#formato-sarif)
9. [Secret scanning](#secret-scanning)
10. [Secret scanning — custom patterns](#secret-scanning--custom-patterns)
11. [Push protection](#push-protection)
12. [Dependabot alerts e updates](#dependabot-alerts-e-updates)
13. [Dependabot security updates](#dependabot-security-updates)
14. [GitHub Advanced Security — panoramica](#github-advanced-security--panoramica)
15. [Code scanning autofix](#code-scanning-autofix)
16. [Security overview dashboard](#security-overview-dashboard)
17. [GHAS licensing e abilitazione](#ghas-licensing-e-abilitazione)
18. [Pattern avanzati](#pattern-avanzati)
19. [Il linguaggio QL — funzionalità avanzate](#il-linguaggio-ql--funzionalità-avanzate)
20. [Models-as-data e data extensions](#models-as-data-e-data-extensions)
21. [Threat model configuration](#threat-model-configuration)
22. [Multi-repository variant analysis (MRVA)](#multi-repository-variant-analysis-mrva)
23. [Security campaigns](#security-campaigns)
24. [Secret scanning — rilevamento generico con AI](#secret-scanning--rilevamento-generico-con-ai)
25. [Dependabot auto-triage rules](#dependabot-auto-triage-rules)
26. [GHAS 2025: Secret Protection e Code Security](#ghas-2025-secret-protection-e-code-security)
27. [SARIF avanzato](#sarif-avanzato)
28. [CodeQL Action v4 e migrazione](#codeql-action-v4-e-migrazione)
29. [CodeQL per linguaggi compilati — configurazione build](#codeql-per-linguaggi-compilati--configurazione-build)
30. [CodeQL CLI vs VS Code extension — confronto workflow](#codeql-cli-vs-vs-code-extension--confronto-workflow)
31. [Default vs extended query suites — analisi dettagliata](#default-vs-extended-query-suites--analisi-dettagliata)
32. [Secret scanning — configurazione pattern in push protection](#secret-scanning--configurazione-pattern-in-push-protection)
33. [Code scanning AI-powered — modello ibrido](#code-scanning-ai-powered--modello-ibrido)
34. [Model packs — creazione e distribuzione](#model-packs--creazione-e-distribuzione)
35. [Esercizi](#esercizi)
36. [Troubleshooting — 20 problemi comuni](#troubleshooting--20-problemi-comuni)
37. [FAQ — 20 domande e risposte](#faq--20-domande-e-risposte)
38. [Letture consigliate](#letture-consigliate)
39. [Glossario](#glossario)

---

## Idee guida

1. **CodeQL = SAST integrato GitHub.** Linguaggio SQL-like per interrogare il codice come un database.
2. **Default queries coprono OWASP Top 10 + CWE Top 25.**
3. **Custom queries per pattern proprietari:** ogni team può scrivere regole specifiche.
4. **Secret scanning + push protection:** blocca i commit che contengono secret prima del push.
5. **GHAS unifica:** code scanning, secret scanning, dependency review in un unico framework di sicurezza.

---

## Architettura CodeQL

### Come funziona CodeQL

CodeQL tratta il codice sorgente come un **database relazionale** interrogabile:

```text
Source Code
    │
    ▼
┌──────────────────┐
│  CodeQL Extractor │   ← Analizza il codice, estrae AST, CFG, tipo info
│  (per linguaggio) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  CodeQL Database  │   ← Database relazionale: tabelle, relazioni, fatti
│  (snapshot)       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  QL Engine        │   ← Motore di query: esegue query QL sul database
│  (Datalog-based)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Results (SARIF)  │   ← Risultati in formato SARIF, integrati in GitHub
└──────────────────┘
```

### Componenti principali

| Componente | Ruolo |
|---|---|
| **Extractor** | Programma specifico per linguaggio che analizza il source code e popola il database |
| **Database** | Snapshot relazionale del codebase: AST, data flow, control flow, tipo system |
| **QL engine** | Motore di valutazione basato su Datalog per eseguire query dichiarative |
| **Query packs** | Collezioni di query predefinite (security, quality, metrics) |
| **SARIF output** | Formato standard per i risultati, integrato nella Security tab di GitHub |

### Linguaggi supportati

| Linguaggio | Stato | Note |
|---|---|---|
| C/C++ | GA | Richiede build system configurato |
| C# | GA | .NET framework e .NET Core |
| Go | GA | Analisi senza build step |
| Java/Kotlin | GA | Build con Maven/Gradle |
| JavaScript/TypeScript | GA | Analisi senza build step |
| Python | GA | Analisi senza build step |
| Ruby | GA | Analisi senza build step |
| Swift | GA | Richiede Xcode |

### Data flow analysis

La potenza di CodeQL sta nell'analisi del flusso dati:

```text
Taint tracking: segue i dati "contaminati" dall'input alla sink

Source (input utente)                    Sink (operazione pericolosa)
─────────────────────                    ──────────────────────────
request.getParameter("q")  ──────────►  executeQuery(q)
                              │
                              │ attraverso:
                              │ - assegnazioni
                              │ - chiamate a funzione
                              │ - return values
                              │ - concatenazioni
                              │ - trasformazioni
```

CodeQL può tracciare il flusso dati attraverso:
- **Intra-procedurale:** all'interno di una singola funzione.
- **Inter-procedurale:** attraverso chiamate di funzione, anche su più file.
- **Framework-aware:** comprende i pattern dei framework (Express, Spring, Django, ecc.).

---

## CodeQL database

### Creazione del database

```bash
# Installare CodeQL CLI
gh extension install github/gh-codeql

# Creare un database JavaScript (no build step)
codeql database create ./codeql-db \
  --language=javascript \
  --source-root=./my-project

# Creare un database Java (con build)
codeql database create ./codeql-db \
  --language=java \
  --source-root=./my-project \
  --command="mvn clean compile -DskipTests"

# Creare un database multi-linguaggio
codeql database create ./codeql-db \
  --language=javascript,python \
  --source-root=./my-project

# Analizzare un database esistente
codeql database analyze ./codeql-db \
  codeql/javascript-queries:codeql-suites/javascript-security-extended.qls \
  --format=sarif-latest \
  --output=results.sarif
```

### Struttura interna del database

```text
codeql-db/
├── db-javascript/
│   ├── default/
│   │   ├── ast.rel        ← Abstract Syntax Tree
│   │   ├── cfg.rel        ← Control Flow Graph
│   │   ├── type.rel       ← Type information
│   │   ├── expr.rel       ← Expressions
│   │   ├── stmt.rel       ← Statements
│   │   └── ...
│   └── semmlecode.javascript.dbscheme
├── src/                   ← Copia del source code
├── diagnostic/            ← Log di estrazione
└── codeql-database.yml    ← Metadata
```

### Relazioni nel database

Il database contiene tabelle relazionali che rappresentano il codice:

| Tabella | Contenuto |
|---|---|
| `exprs` | Tutte le espressioni (literal, call, access) |
| `stmts` | Tutti gli statement (if, for, return) |
| `functions` | Definizioni di funzione |
| `variables` | Variabili e parametri |
| `types` | Informazioni sui tipi |
| `locations` | Posizione nel source (file, riga, colonna) |
| `dataflow` | Flusso dati tra nodi |
| `taintflow` | Propagazione del taint |

---

## Il linguaggio QL

### Sintassi base

QL è un linguaggio dichiarativo derivato da Datalog, con elementi di SQL e programmazione logica:

```ql
/**
 * @name Trova tutte le funzioni con più di 50 righe
 * @description Funzioni lunghe sono difficili da mantenere
 * @kind problem
 * @problem.severity warning
 * @id custom/long-functions
 */

import javascript

from Function f
where f.getNumLines() > 50
  and not f.getFile().getRelativePath().matches("%test%")
  and not f.getFile().getRelativePath().matches("%node_modules%")
select f, "La funzione " + f.getName() + " ha " + f.getNumLines().toString() + " righe."
```

### Struttura di una query

```ql
/**
 * Metadata (JSDoc comments)
 * @name Nome leggibile della query
 * @description Descrizione del problema
 * @kind problem | path-problem   ← tipo di risultato
 * @problem.severity error | warning | recommendation
 * @precision high | medium | low
 * @id <scope>/<identifier>
 * @tags security
 *       external/cwe/cwe-079
 */

// Import del linguaggio
import <language>

// Classi e predicati ausiliari (opzionale)
class MyClass extends ... { ... }
predicate myPredicate(...) { ... }

// Clausola from-where-select
from <tipo> <variabile>, ...
where <condizioni>
select <risultato>, <messaggio>
```

### Tipi di query

| `@kind` | Uso | Output |
|---|---|---|
| `problem` | Alert semplice — "questo punto ha un problema" | Posizione + messaggio |
| `path-problem` | Alert con traccia — "i dati fluiscono da qui a lì" | Source → Sink + path |
| `metric` | Metriche numeriche | Valore numerico |
| `diagnostic` | Informazioni diagnostiche | Testo libero |

### Predicati e classi

```ql
// Predicato: condizione riutilizzabile
predicate isSensitiveParam(Parameter p) {
  p.getName().regexpMatch("(?i).*(password|secret|token|key|auth).*")
}

// Classe: estende un tipo base con logica custom
class HardcodedSecret extends StringLiteral {
  HardcodedSecret() {
    this.getValue().regexpMatch("(?i)(api[_-]?key|secret|password|token)\\s*[:=]\\s*['\"]?[a-zA-Z0-9+/]{16,}.*")
  }
}
```

### Taint tracking query (path-problem)

```ql
/**
 * @name SQL injection
 * @description Dati utente non sanitizzati in query SQL
 * @kind path-problem
 * @problem.severity error
 * @precision high
 * @id js/sql-injection
 * @tags security
 *       external/cwe/cwe-089
 */

import javascript
import semmle.javascript.security.dataflow.SqlInjectionQuery
import DataFlow::PathGraph

from SqlInjection::Configuration cfg, DataFlow::PathNode source, DataFlow::PathNode sink
where cfg.hasFlowPath(source, sink)
select sink.getNode(), source, sink,
  "Possibile SQL injection: dati dall'$@ raggiungono questa query.",
  source.getNode(), "input utente"
```

### Esempi di query comuni

#### Trovare console.log rimasti nel codice

```ql
/**
 * @name Console.log in production code
 * @kind problem
 * @problem.severity warning
 * @id custom/console-log-in-prod
 */

import javascript

from MethodCallExpr call
where call.getReceiver().(VarAccess).getName() = "console"
  and call.getMethodName() = "log"
  and not call.getFile().getRelativePath().matches("%test%")
  and not call.getFile().getRelativePath().matches("%spec%")
select call, "console.log trovato in codice non-test."
```

#### Trovare password hardcoded

```ql
/**
 * @name Hardcoded password
 * @kind problem
 * @problem.severity error
 * @id custom/hardcoded-password
 * @tags security
 *       external/cwe/cwe-798
 */

import python

from Assignment a, StringLiteral s
where a.getValue() = s
  and a.getTarget().(Name).getId().regexpMatch("(?i).*(password|passwd|pwd|secret|api_key).*")
  and s.getText().length() > 5
select a, "Possibile password hardcoded nella variabile '" + a.getTarget().(Name).getId() + "'."
```

#### Trovare endpoint senza autenticazione (Express)

```ql
/**
 * @name Unauthenticated endpoint
 * @kind problem
 * @problem.severity warning
 * @id custom/unauth-endpoint
 */

import javascript

from MethodCallExpr route
where (route.getMethodName() = "get" or
       route.getMethodName() = "post" or
       route.getMethodName() = "put" or
       route.getMethodName() = "delete")
  and route.getReceiver().getAType().getName() = "Router"
  and not exists(MethodCallExpr middleware |
    middleware.getMethodName() = "use" and
    middleware.getArgument(0).(VarAccess).getName().matches("%auth%")
  )
select route, "Endpoint potenzialmente senza middleware di autenticazione."
```

---

## QL Packs e Query Suites

### QL Packs

Un QL pack è un pacchetto di query con metadata e dipendenze:

```yaml
# qlpack.yml
name: myorg/custom-security-queries
version: 1.0.0
description: Query di sicurezza custom per il nostro codebase
dependencies:
  codeql/javascript-all: "*"
  codeql/javascript-queries: "*"
default-suite-file: suites/custom-security.qls
library: false
```

### Struttura di un QL pack

```text
my-ql-pack/
├── qlpack.yml              ← Metadata del pack
├── suites/
│   ├── custom-security.qls ← Query suite
│   └── custom-quality.qls
├── queries/
│   ├── security/
│   │   ├── SqlInjection.ql
│   │   ├── XssVulnerability.ql
│   │   └── HardcodedSecret.ql
│   └── quality/
│       ├── LongFunction.ql
│       └── ConsoleLog.ql
└── lib/
    └── CustomPredicates.qll  ← Libreria condivisa
```

### Query Suites

Un query suite seleziona quali query eseguire:

```yaml
# suites/custom-security.qls
- description: Query di sicurezza custom
- queries: queries/security
- apply: security-severity
- include:
    severity: error
    severity: warning

# Oppure: incluedere query da pack esterni + custom
- qlpack: codeql/javascript-queries
- include:
    kind: problem
    tags contain: security
- queries: queries/security
```

### Query suites predefiniti

| Suite | Contenuto | Uso |
|---|---|---|
| `default` | Query con alta precision e severity ≥ warning | PR check, CI quotidiano |
| `security-extended` | Tutte le security queries incluse quelle con precision media | Audit approfondito |
| `security-and-quality` | Security + code quality | Revisione completa |
| `security-experimental` | Query sperimentali (possibili falsi positivi) | Ricerca, valutazione |

```yaml
# Usare un suite in GitHub Actions
- uses: github/codeql-action/init@v3
  with:
    languages: javascript
    queries: security-extended  # oppure: security-and-quality
```

### Pubblicare un QL pack

```bash
# Login al registry
codeql pack publish --registry=https://ghcr.io myorg/custom-security-queries

# Usare nel workflow
- uses: github/codeql-action/init@v3
  with:
    languages: javascript
    packs: myorg/custom-security-queries@1.0.0
```

---

## Setup CodeQL in GitHub Actions

### Workflow base

```yaml
name: CodeQL Analysis
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 4 * * 1"  # Ogni lunedì alle 04:00

permissions:
  security-events: write
  contents: read
  actions: read

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    runs-on: ${{ matrix.language == 'swift' && 'macos-latest' || 'ubuntu-latest' }}
    timeout-minutes: 360
    strategy:
      fail-fast: false
      matrix:
        include:
          - language: javascript-typescript
            build-mode: none
          - language: python
            build-mode: none
          - language: java-kotlin
            build-mode: autobuild

    steps:
      - uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          build-mode: ${{ matrix.build-mode }}
          queries: security-extended

      # Per linguaggi compilati (se build-mode != none e != autobuild)
      - if: matrix.build-mode == 'manual'
        name: Build
        run: |
          mvn clean compile -DskipTests

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
```

### Configurazione avanzata

```yaml
      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: javascript-typescript
          # Query suite
          queries: security-extended
          # QL pack aggiuntivi
          packs: |
            myorg/custom-security-queries@1.0.0
            codeql/javascript-queries:codeql-suites/javascript-security-and-quality.qls
          # Config file
          config-file: .github/codeql/codeql-config.yml
          # Trap caching per velocità
          trap-caching: true
```

### File di configurazione CodeQL

```yaml
# .github/codeql/codeql-config.yml
name: "CodeQL Config"

# Query da eseguire
queries:
  - uses: security-extended
  - uses: ./custom-queries  # Percorso relativo nel repo

# File/directory da escludere
paths-ignore:
  - "**/test/**"
  - "**/tests/**"
  - "**/*.test.js"
  - "**/*.spec.js"
  - "**/node_modules/**"
  - "**/vendor/**"
  - "**/__mocks__/**"
  - "**/dist/**"
  - "**/build/**"
  - "**/generated/**"

# File da includere (restrittivo)
paths:
  - src
  - lib

# Packs aggiuntivi
packs:
  javascript:
    - myorg/js-security-queries@~1.0.0
  python:
    - myorg/py-security-queries@~1.0.0

# Query filters
query-filters:
  - exclude:
      id: js/unused-local-variable
  - exclude:
      tags contain: experimental
```

### Multi-repository CodeQL con reusable workflow

```yaml
# .github/workflows/codeql-reusable.yml (in un repo template)
name: CodeQL Reusable
on:
  workflow_call:
    inputs:
      languages:
        required: true
        type: string
      queries:
        required: false
        type: string
        default: security-extended

permissions:
  security-events: write
  contents: read
  actions: read

jobs:
  analyze:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        language: ${{ fromJSON(inputs.languages) }}
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: ${{ inputs.queries }}
      - uses: github/codeql-action/analyze@v3
```

```yaml
# In ogni repository che usa il template
name: CodeQL
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: "0 4 * * 1"

jobs:
  codeql:
    uses: myorg/.github/.github/workflows/codeql-reusable.yml@main
    with:
      languages: '["javascript-typescript", "python"]'
      queries: security-and-quality
```

---

## Custom queries

### Creare una query custom passo-passo

#### 1. Setup ambiente locale

```bash
# Installare VS Code + extension CodeQL
code --install-extension github.vscode-codeql

# Clonare il repository delle query standard
git clone https://github.com/github/codeql.git

# Creare la directory per query custom
mkdir -p my-queries/queries my-queries/lib my-queries/suites
```

#### 2. Scrivere la query

```ql
// my-queries/queries/NoHardcodedApiEndpoint.ql

/**
 * @name Hardcoded API endpoint
 * @description URL di API hardcoded nel source code
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id custom/hardcoded-api-endpoint
 * @tags maintainability
 *       configuration
 */

import javascript

from StringLiteral s
where s.getValue().regexpMatch("https?://api\\..+\\..+/.*")
  and not s.getFile().getRelativePath().matches("%test%")
  and not s.getFile().getRelativePath().matches("%config%")
  and not s.getFile().getRelativePath().matches("%.env%")
select s, "URL di API hardcoded: " + s.getValue() + ". Usare variabili d'ambiente o configurazione."
```

#### 3. Testare localmente

```bash
# Creare database del progetto
codeql database create ./test-db --language=javascript --source-root=./my-project

# Eseguire la query
codeql query run my-queries/queries/NoHardcodedApiEndpoint.ql \
  --database=./test-db

# Eseguire con output SARIF
codeql database analyze ./test-db \
  my-queries/queries/NoHardcodedApiEndpoint.ql \
  --format=sarif-latest \
  --output=results.sarif
```

#### 4. Aggiungere al workflow

```yaml
- uses: github/codeql-action/init@v3
  with:
    languages: javascript-typescript
    queries: security-extended, ./my-queries/queries/
```

### Libreria condivisa (.qll)

```ql
// my-queries/lib/CustomSources.qll

import javascript

/** Identifica input utente custom del nostro framework */
class CustomUserInput extends DataFlow::Node {
  CustomUserInput() {
    exists(MethodCallExpr call |
      call.getMethodName() = "getBody" or
      call.getMethodName() = "getQuery" or
      call.getMethodName() = "getHeader"
    |
      this = call.flow()
    )
  }
}

/** Identifica sink pericolosi custom */
class CustomDangerousSink extends DataFlow::Node {
  CustomDangerousSink() {
    exists(MethodCallExpr call |
      call.getMethodName() = "executeRawQuery" or
      call.getMethodName() = "renderTemplate" or
      call.getMethodName() = "sendEmail"
    |
      this = call.getArgument(0).flow()
    )
  }
}
```

### Unit test per query

```ql
// my-queries/tests/NoHardcodedApiEndpoint/test.js

// GOOD: no alert
const apiUrl = process.env.API_URL;
fetch(apiUrl);

// BAD: hardcoded API URL
const data = fetch("https://api.example.com/v1/users");  // $ MISSING: alert

// GOOD: in config file (excluded by path)
// (test in config/ directory would be excluded)
```

```bash
# Eseguire i test delle query
codeql test run my-queries/tests/
```

---

## Formato SARIF

### Cos'è SARIF

SARIF (Static Analysis Results Interchange Format) è uno standard OASIS per i risultati di analisi statica:

```json
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "CodeQL",
          "version": "2.18.0",
          "semanticVersion": "2.18.0",
          "rules": [
            {
              "id": "js/sql-injection",
              "name": "SqlInjection",
              "shortDescription": {
                "text": "SQL injection"
              },
              "fullDescription": {
                "text": "Dati utente non sanitizzati in query SQL..."
              },
              "defaultConfiguration": {
                "level": "error"
              },
              "properties": {
                "tags": ["security", "external/cwe/cwe-089"],
                "precision": "high",
                "problem.severity": "error"
              }
            }
          ]
        }
      },
      "results": [
        {
          "ruleId": "js/sql-injection",
          "ruleIndex": 0,
          "level": "error",
          "message": {
            "text": "Possibile SQL injection: dati dall'[input utente](1) raggiungono questa query."
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "src/db/queries.js",
                  "uriBaseId": "%SRCROOT%"
                },
                "region": {
                  "startLine": 42,
                  "startColumn": 5,
                  "endLine": 42,
                  "endColumn": 55
                }
              }
            }
          ],
          "relatedLocations": [
            {
              "id": 1,
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "src/routes/users.js"
                },
                "region": {
                  "startLine": 15,
                  "startColumn": 20,
                  "endLine": 15,
                  "endColumn": 45
                }
              },
              "message": {
                "text": "input utente"
              }
            }
          ],
          "codeFlows": [
            {
              "threadFlows": [
                {
                  "locations": [
                    {
                      "location": {
                        "physicalLocation": {
                          "artifactLocation": { "uri": "src/routes/users.js" },
                          "region": { "startLine": 15 }
                        },
                        "message": { "text": "Source: req.query.search" }
                      }
                    },
                    {
                      "location": {
                        "physicalLocation": {
                          "artifactLocation": { "uri": "src/db/queries.js" },
                          "region": { "startLine": 42 }
                        },
                        "message": { "text": "Sink: db.query(sql)" }
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Upload SARIF da tool terzi

```yaml
# Upload risultati da qualsiasi tool che produce SARIF
- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: results.sarif
    category: my-custom-tool

# Esempio con ESLint (output SARIF)
- name: ESLint SARIF
  run: npx eslint --format @microsoft/eslint-formatter-sarif --output-file eslint.sarif .
  continue-on-error: true

- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: eslint.sarif
    category: eslint

# Esempio con Semgrep
- name: Semgrep SARIF
  run: semgrep --config=auto --sarif --output=semgrep.sarif .
  continue-on-error: true

- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: semgrep.sarif
    category: semgrep
```

---

## Secret scanning

### Come funziona

GitHub Secret Scanning analizza il contenuto del repository (commit, issue, PR, wiki) per trovare secret accidentalmente committati:

```text
Commit push ──► Secret scanning engine ──► Match trovato?
                     │                          │
                     │ Pattern database:         │ Sì ──► Alert creato
                     │ - GitHub tokens           │        + notifica partner
                     │ - AWS keys                │          (se partner program)
                     │ - Azure credentials       │
                     │ - GCP service account keys│
                     │ - npm tokens              │
                     │ - Stripe keys             │
                     │ - 200+ pattern            │
                     │                           │ No ──► Nessuna azione
```

### Partner program

Per molti provider, GitHub notifica automaticamente il partner quando viene trovato un loro secret:

| Partner | Tipo di secret | Azione del partner |
|---|---|---|
| AWS | Access key | Revoca automatica possibile |
| Azure | Service principal key | Notifica all'admin |
| GitHub | Personal access token | Revoca automatica |
| npm | Token | Revoca automatica |
| Stripe | Secret key | Notifica |
| Twilio | API key | Notifica |
| ... | 200+ partner | Varie |

### Abilitazione

```text
Repository Settings → Security → Code security and analysis
  → Secret scanning: Enable
  → Push protection: Enable (opzionale ma consigliato)
```

Per organizzazioni:

```text
Organization Settings → Code security and analysis
  → Secret scanning: Enable for all repositories
  → Push protection: Enable for all repositories
```

### API per secret scanning alerts

```bash
# Listare gli alert
gh api repos/myorg/myrepo/secret-scanning/alerts

# Dettagli di un alert
gh api repos/myorg/myrepo/secret-scanning/alerts/42

# Risolvere un alert (false positive)
gh api -X PATCH repos/myorg/myrepo/secret-scanning/alerts/42 \
  -f state="resolved" \
  -f resolution="false_positive"

# Risolvere un alert (revocato)
gh api -X PATCH repos/myorg/myrepo/secret-scanning/alerts/42 \
  -f state="resolved" \
  -f resolution="revoked"
```

---

## Secret scanning — custom patterns

### Definire pattern personalizzati

Per secret specifici della tua organizzazione (es. token interni, API key custom):

```text
Organization Settings → Code security → Secret scanning
  → Custom patterns → New pattern
```

### Formato dei pattern

```yaml
# Esempio: token interno con prefisso "MYORG_"
Name: MyOrg Internal Token
Secret format: MYORG_[a-zA-Z0-9]{32}
Before secret: (token|key|secret)\s*[:=]\s*["']?
After secret: ["']?\s*[;,}\n]

# Esempio: API key con formato specifico
Name: Internal API Key v2
Secret format: iak_v2_[a-f0-9]{40}

# Esempio: database connection string
Name: Internal DB Connection String
Secret format: postgres://[a-zA-Z0-9_]+:[^@]+@db\.(internal|staging)\.myorg\.com:\d+/[a-zA-Z0-9_]+
```

### Dry run

Prima di attivare un pattern custom, eseguire un dry run:

```text
Custom pattern → Dry run → Rivedi i risultati → Attiva solo se i falsi positivi sono accettabili
```

### Pattern a livello organizzazione

```bash
# Via API — creare un pattern custom per l'organizzazione
gh api -X POST /orgs/myorg/secret-scanning/custom-patterns \
  -f name="Internal Token" \
  -f pattern="MYORG_[a-zA-Z0-9]{32}" \
  -f before_secret="(token|key|secret)\s*[:=]\s*[\"']?" \
  -f after_secret="[\"']?\s*[;,}\n]"
```

---

## Push protection

### Come funziona

Push protection blocca un `git push` **prima** che il secret raggiunga il repository:

```text
Developer:  git push origin main

GitHub:     ⚠ Push bloccato!
            Il push contiene un secret rilevato:
            - File: src/config.js, riga 15
            - Tipo: AWS Access Key
            - Valore: AKIA...XXXX (parziale)

            Opzioni:
            1. Rimuovere il secret e riprovare
            2. Bypassare (con giustificazione)
            3. Segnalare come falso positivo
```

### Abilitazione

```text
Repository Settings → Security → Push protection → Enable
```

### Bypass

Quando un developer bypassa push protection, deve specificare una ragione:

| Ragione | Significato |
|---|---|
| **It's used in tests** | Il secret è un valore di test, non reale |
| **It's a false positive** | Il pattern matcha ma non è un secret |
| **I'll fix it later** | Consapevolezza, fix pianificato |

Ogni bypass viene loggato nell'audit log dell'organizzazione.

### Delegated bypass

```text
Organization Settings → Code security → Push protection
  → Delegated bypass → Enable

Configurare:
  - Chi può bypassare (team/ruoli)
  - Chi deve approvare il bypass
  - Timeout dell'approvazione
```

### Push protection per la CLI

```bash
# Se il push viene bloccato:
$ git push origin main
remote: error: GH013: Secret scanning found the following secrets:
remote:   - AWS Access Key ID in src/config.js:15
remote:
remote: To push, either:
remote:   1. Remove the secret
remote:   2. Use the web UI to allow the push: https://github.com/myorg/myrepo/...

# Per rimuovere il secret dalla history
git filter-repo --invert-paths --path src/config.js
# oppure
git rebase -i HEAD~3  # se il commit è recente
```

---

## Dependabot alerts e updates

### Dependabot Alerts

```text
Security tab → Dependabot alerts

Ogni alert include:
- CVE/GHSA identifier
- Severity (critical, high, medium, low)
- Affected package e version range
- Fixed version (se disponibile)
- CWE (tipo di vulnerabilità)
- CVSS score
```

### Configurazione Dependabot Version Updates

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: npm
    directory: "/"
    schedule:
      interval: weekly
      day: monday
      time: "09:00"
      timezone: Europe/Rome
    open-pull-requests-limit: 10
    reviewers:
      - "myorg/security-team"
    labels:
      - "dependencies"
    commit-message:
      prefix: "chore(deps):"
    groups:
      dev-dependencies:
        dependency-type: development
        update-types:
          - minor
          - patch
      production-deps:
        dependency-type: production
        update-types:
          - patch
    ignore:
      - dependency-name: "typescript"
        update-types: ["version-update:semver-major"]

  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
    labels:
      - "ci"
    commit-message:
      prefix: "ci(deps):"

  - package-ecosystem: docker
    directory: "/"
    schedule:
      interval: monthly
```

### Auto-merge per Dependabot

```yaml
# .github/workflows/dependabot-auto-merge.yml
name: Dependabot Auto-merge
on: pull_request

permissions:
  contents: write
  pull-requests: write

jobs:
  auto-merge:
    if: github.actor == 'dependabot[bot]'
    runs-on: ubuntu-latest
    steps:
      - uses: dependabot/fetch-metadata@v2
        id: metadata

      - name: Auto-merge patch updates
        if: |
          steps.metadata.outputs.update-type == 'version-update:semver-patch' &&
          steps.metadata.outputs.dependency-type == 'direct:development'
        run: gh pr merge "$PR" --auto --squash
        env:
          PR: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Dependabot security updates

### Differenza tra version updates e security updates

| Aspetto | Version Updates | Security Updates |
|---|---|---|
| **Trigger** | Schedule (cron) | Vulnerabilità rilevata (advisory) |
| **Scopo** | Mantenere dipendenze aggiornate | Risolvere vulnerabilità specifiche |
| **Configurazione** | `dependabot.yml` obbligatorio | Abilitazione in Settings (no file) |
| **PR** | Aggiornamento alla latest | Aggiornamento alla versione minima che risolve la CVE |

### Abilitazione

```text
Repository Settings → Security → Dependabot security updates → Enable
```

### Grouped security updates

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: npm
    directory: "/"
    schedule:
      interval: weekly
    groups:
      security-patches:
        applies-to: security-updates
        dependency-type: production
```

---

## GitHub Advanced Security — panoramica

### Componenti GHAS

```text
GitHub Advanced Security (GHAS)
├── Code Scanning (CodeQL)
│   ├── Default queries (OWASP Top 10, CWE Top 25)
│   ├── Security-extended queries
│   ├── Custom queries
│   └── Third-party SARIF upload
├── Secret Scanning
│   ├── Built-in patterns (200+)
│   ├── Custom patterns
│   ├── Push protection
│   └── Partner program (auto-revocation)
├── Dependency Review
│   ├── PR-time vulnerability check
│   ├── License check
│   └── Advisory database
├── Security Overview
│   ├── Organization-level dashboard
│   ├── Risk assessment
│   └── Coverage metrics
└── Code Scanning Autofix (Copilot)
    ├── AI-suggested fixes per alert
    └── One-click PR creation
```

### Cosa è gratuito vs. GHAS

| Funzionalità | Public repos | Private repos (Free/Team) | Private repos (GHAS) |
|---|---|---|---|
| Dependabot alerts | Gratuito | Gratuito | Gratuito |
| Dependabot security updates | Gratuito | Gratuito | Gratuito |
| Dependabot version updates | Gratuito | Gratuito | Gratuito |
| Dependency graph | Gratuito | Gratuito | Gratuito |
| Secret scanning alerts | Gratuito | — | Incluso |
| Push protection | Gratuito | — | Incluso |
| Custom patterns | Gratuito | — | Incluso |
| Code scanning (CodeQL) | Gratuito | — | Incluso |
| Code scanning autofix | Gratuito | — | Incluso |
| Security overview | Gratuito | — | Incluso |
| Dependency review | Gratuito | — | Incluso |

### Abilitazione GHAS per un'organizzazione

```text
Organization Settings → Code security and analysis
→ GitHub Advanced Security → Enable for all repositories

Oppure selettivamente:
→ Enable for new repositories
→ Abilitare per singoli repository in Repository Settings
```

---

## Code scanning autofix

### Cos'è

Code scanning autofix usa AI (Copilot) per generare automaticamente fix per gli alert CodeQL:

```text
Alert: SQL Injection in src/db/queries.js:42
  ┌──────────────────────────────────────┐
  │ Autofix disponibile                   │
  │                                       │
  │ Suggerimento: usare parametri bindati │
  │ invece di concatenazione stringa      │
  │                                       │
  │ [Visualizza suggerimento]             │
  │ [Crea PR con fix]                     │
  │ [Ignora]                              │
  └──────────────────────────────────────┘
```

### Come funziona

1. CodeQL identifica un alert (es. SQL injection).
2. Copilot analizza il codice circostante e il tipo di vulnerabilità.
3. Genera un fix suggerito con spiegazione.
4. Il developer può accettare, modificare, o rifiutare.
5. Se accettato, crea automaticamente un commit o una PR.

### Linguaggi supportati per autofix

| Linguaggio | Supporto |
|---|---|
| JavaScript/TypeScript | GA |
| Python | GA |
| Java | GA |
| C# | GA |
| Go | GA (limitato) |
| Ruby | Beta |
| C/C++ | Non supportato |
| Swift | Non supportato |

### Esempio di autofix

```diff
# Prima (vulnerabile):
- const query = "SELECT * FROM users WHERE name = '" + req.query.name + "'";
- db.query(query);

# Dopo (fix suggerito da autofix):
+ const query = "SELECT * FROM users WHERE name = $1";
+ db.query(query, [req.query.name]);
```

### Abilitazione

```text
Repository Settings → Code security → Code scanning
  → Autofix → Enable
```

---

## Security overview dashboard

### Panoramica

La Security Overview fornisce una vista aggregata dello stato di sicurezza a livello di organizzazione:

```text
Organization → Security → Overview

Dashboard mostra:
├── Risk assessment
│   ├── Repositories con alert critici
│   ├── Repositories senza code scanning
│   └── Trend nel tempo
├── Coverage
│   ├── % repository con code scanning abilitato
│   ├── % repository con secret scanning
│   ├── % repository con Dependabot
│   └── Gap da colmare
├── Alert trends
│   ├── Nuovi alert per settimana
│   ├── Alert risolti per settimana
│   ├── MTTR (Mean Time To Remediate)
│   └── Backlog per severity
└── Per-repository detail
    ├── Alert aperti per tipo
    ├── Ultimo scan
    └── Coverage status
```

### Filtri disponibili

```text
# Filtrare per severity
is:open severity:critical

# Filtrare per tipo di alert
tool:codeql
tool:secret-scanning
tool:dependabot

# Filtrare per team
team:backend-team

# Filtrare per repository
repo:myorg/myrepo

# Filtrare per stato
is:open
is:closed

# Filtrare per MTTR
closed:>30d  # Alert che hanno richiesto > 30 giorni per essere risolti
```

### Metriche chiave

| Metrica | Target consigliato |
|---|---|
| **Coverage** | 100% repository con code scanning |
| **Critical alert MTTR** | < 7 giorni |
| **High alert MTTR** | < 30 giorni |
| **Alert backlog trend** | Decrescente |
| **Secret scanning coverage** | 100% con push protection |

### API per Security Overview

```bash
# Alert code scanning per repository
gh api repos/myorg/myrepo/code-scanning/alerts \
  --jq '[.[] | select(.state == "open")] | length'

# Alert Dependabot per organizzazione
gh api orgs/myorg/dependabot/alerts \
  --jq '[.[] | select(.state == "open" and .security_advisory.severity == "critical")] | length'

# Secret scanning alerts
gh api repos/myorg/myrepo/secret-scanning/alerts \
  --jq '[.[] | select(.state == "open")] | length'
```

---

## GHAS licensing e abilitazione

### Modello di pricing

| Piano | Costo | Include |
|---|---|---|
| **GitHub Free / Team** | Gratuito | Dependabot, dependency graph |
| **GHAS (per committer)** | ~$49/committer/mese | Code scanning, secret scanning, dependency review, security overview |
| **Public repos** | Gratuito | Tutto GHAS gratuitamente |

### Committer counting

Un "active committer" è contato se ha fatto almeno un commit a un repository con GHAS abilitato negli ultimi 90 giorni:

```text
Committer unico che contribuisce a:
- Repo A (GHAS abilitato) ← conta 1 committer
- Repo B (GHAS abilitato) ← stesso committer, conta 0 (già contato)
- Repo C (GHAS non abilitato) ← non conta
```

### Abilitazione graduale

```text
Strategia consigliata:
1. Abilitare su repository critici (customer-facing, auth, payment)
2. Espandere ai repository con più contributor
3. Abilitare per tutta l'organizzazione
4. Monitorare il costo via Settings → Billing → GHAS
```

### API per gestire GHAS

```bash
# Abilitare GHAS per un repository
gh api -X PUT repos/myorg/myrepo \
  -f security_and_analysis.advanced_security.status="enabled"

# Abilitare code scanning default setup
gh api -X PATCH repos/myorg/myrepo/code-scanning/default-setup \
  -f state="configured" \
  -f query_suite="extended"

# Verificare lo stato
gh api repos/myorg/myrepo \
  --jq '.security_and_analysis'
```

---

## Pattern avanzati

### Security gate in CI/CD

```yaml
name: Security Gate
on:
  pull_request:

jobs:
  security-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Check CodeQL alerts
        run: |
          ALERTS=$(gh api repos/${{ github.repository }}/code-scanning/alerts \
            --jq '[.[] | select(.state == "open" and .rule.security_severity_level == "critical")] | length')

          if [ "$ALERTS" -gt 0 ]; then
            echo "BLOCKED: $ALERTS critical CodeQL alerts found"
            exit 1
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Check Dependabot alerts
        run: |
          CRITICAL=$(gh api repos/${{ github.repository }}/dependabot/alerts \
            --jq '[.[] | select(.state == "open" and .security_advisory.severity == "critical")] | length')

          if [ "$CRITICAL" -gt 0 ]; then
            echo "BLOCKED: $CRITICAL critical Dependabot alerts found"
            exit 1
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Check secret scanning
        run: |
          SECRETS=$(gh api repos/${{ github.repository }}/secret-scanning/alerts \
            --jq '[.[] | select(.state == "open")] | length')

          if [ "$SECRETS" -gt 0 ]; then
            echo "BLOCKED: $SECRETS secret scanning alerts found"
            exit 1
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Monitoraggio multi-repo con script

```bash
#!/usr/bin/env bash
# security-audit.sh — audit GHAS coverage per organizzazione

ORG="myorg"
echo "=== Security Audit per $ORG ==="

# Lista repository senza code scanning
echo ""
echo "--- Repository SENZA code scanning ---"
gh api "/orgs/$ORG/repos" --paginate --jq '.[].full_name' | while read -r repo; do
  SCANNING=$(gh api "repos/$repo/code-scanning/default-setup" 2>/dev/null | jq -r '.state // "not_configured"')
  if [ "$SCANNING" != "configured" ]; then
    echo "  ⚠ $repo: $SCANNING"
  fi
done

# Alert critici aperti
echo ""
echo "--- Alert CRITICI aperti ---"
gh api "/orgs/$ORG/code-scanning/alerts?state=open&severity=critical" --paginate \
  --jq '.[] | "\(.repository.full_name): \(.rule.description) [\(.html_url)]"'

# Secret scanning alerts
echo ""
echo "--- Secret scanning alerts aperti ---"
gh api "/orgs/$ORG/secret-scanning/alerts?state=open" --paginate \
  --jq '.[] | "\(.repository.full_name): \(.secret_type) [\(.html_url)]"'
```

### CodeQL + Semgrep combinati

```yaml
name: Combined SAST
on:
  push:
    branches: [main]
  pull_request:

permissions:
  security-events: write
  contents: read

jobs:
  codeql:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: javascript-typescript
          queries: security-extended
      - uses: github/codeql-action/analyze@v3

  semgrep:
    runs-on: ubuntu-latest
    container:
      image: semgrep/semgrep
    steps:
      - uses: actions/checkout@v4
      - run: semgrep --config=auto --sarif --output=semgrep.sarif .
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: semgrep.sarif
          category: semgrep
```

### Dependency review action

La Dependency Review Action analizza le dipendenze introdotte in una PR e blocca il merge se trova vulnerabilità o licenze non approvate:

```yaml
name: Dependency Review
on: pull_request

permissions:
  contents: read
  pull-requests: write

jobs:
  dependency-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Dependency Review
        uses: actions/dependency-review-action@v4
        with:
          # Bloccare PR con vulnerabilità di severity alta o critica
          fail-on-severity: high

          # Controllo licenze
          allow-licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC
          deny-licenses: GPL-3.0, AGPL-3.0

          # Bloccare pacchetti specifici
          deny-packages: |
            npm:colors
            npm:faker

          # Bloccare dipendenze con advisory non risolti
          fail-on-scopes: runtime

          # Commentare sulla PR con i dettagli
          comment-summary-in-pr: always

          # Licenze sconosciute
          allow-unknown-licenses: false
```

#### Configurazione avanzata con output strutturato

```yaml
      - name: Dependency Review
        uses: actions/dependency-review-action@v4
        id: dep-review
        with:
          fail-on-severity: high
          allow-licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, Unlicense, 0BSD
          deny-licenses: GPL-3.0-only, AGPL-3.0-only, AGPL-3.0-or-later
          comment-summary-in-pr: always
          warn-only: false
          base-ref: ${{ github.event.pull_request.base.sha }}
          head-ref: ${{ github.event.pull_request.head.sha }}

      - name: Report vulnerabilità
        if: failure()
        run: |
          echo "## Dependency Review Failed" >> $GITHUB_STEP_SUMMARY
          echo "La PR introduce dipendenze con vulnerabilità o licenze non approvate." >> $GITHUB_STEP_SUMMARY
          echo "Consultare i dettagli nel commento della PR." >> $GITHUB_STEP_SUMMARY
```

#### Confronto con Dependabot

| Aspetto | Dependabot Alerts | Dependency Review Action |
|---|---|---|
| **Quando** | Dopo il merge (scansione continua) | Prima del merge (gate nella PR) |
| **Scopo** | Monitorare vulnerabilità esistenti | Prevenire nuove vulnerabilità |
| **Licenze** | Non controlla | Controlla e blocca |
| **Azione** | Crea alert + PR di fix | Blocca il merge |
| **Costo** | Gratuito | Gratuito (public repos) / GHAS (private) |

### Webhook per alert security

```yaml
# Notificare Slack per nuovi alert critici
name: Security Alert Notification
on:
  code_scanning_alert:
    types: [created]
  secret_scanning_alert:
    types: [created]

jobs:
  notify:
    runs-on: ubuntu-latest
    if: |
      (github.event_name == 'code_scanning_alert' &&
       github.event.alert.rule.security_severity_level == 'critical') ||
      github.event_name == 'secret_scanning_alert'
    steps:
      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚨 Security Alert in ${{ github.repository }}: ${{ github.event.alert.rule.description || github.event.alert.secret_type }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_SECURITY_WEBHOOK }}
```

---

## Il linguaggio QL — funzionalità avanzate

### Ricorsione e chiusure transitive

QL supporta predicati ricorsivi che dipendono, direttamente o indirettamente, da se stessi. Il compilatore QL calcola il minimo punto fisso della ricorsione: parte dall'insieme vuoto e applica ripetutamente il predicato fino a quando l'insieme non cambia più.

Le **chiusure transitive** sono la forma più comune di ricorsione in QL:

```ql
/**
 * Trova tutte le classi che ereditano (direttamente o indirettamente) da una classe base.
 */
import java

// Chiusura transitiva con `+` (uno o più passi)
from Class base, Class derived
where derived.getASupertype+() = base
  and base.getName() = "AbstractController"
select derived, "Classe che estende AbstractController (direttamente o indirettamente)."

// Chiusura riflessiva transitiva con `*` (zero o più passi)
from Class base, Class related
where related.getASupertype*() = base
  and base.getName() = "BaseService"
select related, "Classe uguale o derivata da BaseService."
```

#### Predicato ricorsivo esplicito

```ql
/**
 * Calcola tutti i file importati ricorsivamente da un modulo Python.
 */
import python

predicate imports(Module m1, Module m2) {
  m1.getAnImportedModule() = m2
}

predicate transitiveImport(Module m1, Module m2) {
  imports(m1, m2)
  or
  exists(Module mid |
    imports(m1, mid) and
    transitiveImport(mid, m2)
  )
}

from Module entry, Module dep
where entry.getName() = "main"
  and transitiveImport(entry, dep)
select dep, "Modulo importato transitivamente da main."
```

### Aggregati

QL supporta aggregati standard simili a SQL, più aggregati monotoni specifici per la semantica a punto fisso.

#### Aggregati standard

```ql
import javascript

// count: contare elementi
from File f
where count(Function fn | fn.getFile() = f) > 20
select f, "File con più di 20 funzioni: " +
  count(Function fn | fn.getFile() = f).toString()

// max: trovare il massimo
select max(Function f | | f.getNumLines())
  as maxLines,
  "La funzione più lunga ha " + maxLines.toString() + " righe."

// min: trovare il minimo
from Function f
where f.getNumLines() = min(Function g | | g.getNumLines())
select f, "Funzione più corta del codebase."

// sum: somma
from File f
select f, sum(Function fn | fn.getFile() = f | fn.getNumLines())
  as totalLines
order by totalLines desc

// avg: media
from File f
select f, avg(Function fn | fn.getFile() = f | fn.getNumLines())
  as avgLines
order by avgLines desc

// rank: ordinamento
from Function f
where rank[1..10](Function g | | g.getNumLines() order by g.getNumLines() desc) = f
select f, f.getNumLines(), "Tra le 10 funzioni più lunghe."

// strictcount: come count ma fallisce se non ci sono risultati
// (utile per evitare divisione per zero in rapporti)
from File f
where strictcount(Function fn | fn.getFile() = f) > 0
select f, strictcount(Function fn | fn.getFile() = f)
```

#### Aggregati monotoni

Gli aggregati monotoni funzionano correttamente all'interno di predicati ricorsivi, cosa che gli aggregati standard non garantiscono:

```ql
// Esempio concettuale: contare la profondità massima
// di una catena di chiamate ricorsiva
predicate callDepth(Function f, int depth) {
  not exists(Function caller | caller.getACallee() = f) and depth = 0
  or
  exists(Function caller, int callerDepth |
    caller.getACallee() = f and
    callDepth(caller, callerDepth) and
    depth = callerDepth + 1
  )
}
```

### Formule quantificate

QL supporta quantificatori esistenziali e universali dalla logica matematica.

#### Quantificatore esistenziale — `exists`

```ql
import javascript

// Trova funzioni che contengono almeno un accesso a variabile globale
from Function f
where exists(VarAccess va |
  va.getEnclosingFunction() = f and
  va.getVariable().isGlobal()
)
select f, "Funzione che accede a variabile globale."
```

#### Quantificatore universale — `forall`

```ql
import javascript

// Trova classi dove TUTTI i metodi hanno meno di 30 righe
from Class c
where forall(Function m |
  m = c.getAMethod() |
  m.getNumLines() < 30
)
select c, "Classe con tutti i metodi sotto le 30 righe (buona pratica)."
```

#### Quantificatore `forex` (forall + exists)

`forex` combina `forall` con l'esigenza che esista almeno un elemento — `forall` da solo è vero vacuamente per insiemi vuoti:

```ql
import javascript

// Trova file dove TUTTI i parametri di funzione
// (e ce ne deve essere almeno uno) hanno annotazioni di tipo
from File f
where forex(Parameter p |
  p.getFunction().getFile() = f |
  p.getTypeAnnotation().toString() != ""
)
select f, "File con type annotation su tutti i parametri."
```

### Cast e instanceof

```ql
import javascript

// Cast esplicito
from Expr e
where e instanceof StringLiteral
select e.(StringLiteral).getValue(), "Valore stringa letterale."

// instanceof in condizione where
from DataFlow::Node node
where node.asExpr() instanceof MethodCallExpr
  and node.asExpr().(MethodCallExpr).getMethodName() = "eval"
select node, "Uso pericoloso di eval()."
```

### Classi astratte e caratteri

```ql
import javascript

/**
 * Classe astratta che rappresenta un sink di sicurezza generico.
 * Le sottoclassi definiscono sink specifici.
 */
abstract class SecuritySink extends DataFlow::Node {
  abstract string getKind();
}

class SqlSink extends SecuritySink {
  SqlSink() {
    exists(MethodCallExpr call |
      call.getMethodName().regexpMatch("(?i)(query|exec|execute|raw)") and
      this = call.getArgument(0).flow()
    )
  }
  override string getKind() { result = "sql-injection" }
}

class XssSink extends SecuritySink {
  XssSink() {
    exists(MethodCallExpr call |
      call.getMethodName() = "innerHTML" or
      call.getMethodName() = "write"
    |
      this = call.getArgument(0).flow()
    )
  }
  override string getKind() { result = "xss" }
}
```

### Moduli QL

```ql
// Definire un modulo per organizzare predicati e classi
module AuthChecks {
  predicate isAuthMiddleware(Function f) {
    f.getName().regexpMatch("(?i).*(auth|authenticate|authorize|verify).*")
  }

  predicate hasAuthCheck(Function handler) {
    exists(MethodCallExpr call |
      call.getEnclosingFunction() = handler and
      isAuthMiddleware(call.getCallee())
    )
  }

  class UnauthenticatedHandler extends Function {
    UnauthenticatedHandler() {
      this.getName().regexpMatch("(?i)(get|post|put|delete|patch).*") and
      not hasAuthCheck(this)
    }
  }
}

// Usare il modulo
from AuthChecks::UnauthenticatedHandler h
select h, "Handler HTTP potenzialmente senza autenticazione."
```

---

## Models-as-data e data extensions

### Panoramica

A partire da CodeQL 2.25.2, è possibile definire modelli di sicurezza (source, sink, sanitizer, barrier) in modo **dichiarativo** tramite file YAML, senza scrivere query QL custom. Questa funzionalità si chiama **models-as-data** e utilizza predicati estensibili.

### Perché usare models-as-data

| Approccio | Pro | Contro |
|---|---|---|
| **Query QL custom** | Massima flessibilità, logica complessa | Richiede conoscenza QL, manutenzione costosa |
| **Models-as-data (YAML)** | Dichiarativo, facile da mantenere, non richiede QL | Limitato a pattern standard (source/sink/barrier) |

### Struttura di un file di data extension

```yaml
# .github/codeql/extensions/custom-models.yml
extensions:
  - addsTo:
      pack: codeql/javascript-all
      extensible: sourceModel
    data:
      # Definire una nuova source: il metodo getUnsafeInput()
      # della classe MyFramework
      - ["MyFramework", "Member[getUnsafeInput]",
         "ReturnValue", "remote", "manual"]

  - addsTo:
      pack: codeql/javascript-all
      extensible: sinkModel
    data:
      # Definire un nuovo sink: il primo argomento di executeRaw()
      - ["DatabaseClient", "Member[executeRaw]",
         "Argument[0]", "sql-injection", "manual"]

  - addsTo:
      pack: codeql/javascript-all
      extensible: summaryModel
    data:
      # Definire un summary: i dati fluiscono dall'argomento 0
      # al valore di ritorno di transform()
      - ["DataUtils", "Member[transform]",
         "Argument[0]", "ReturnValue", "taint", "manual"]
```

### Barrier e barrier guard

I barrier dichiarativi permettono di sopprimere falsi positivi senza modificare le query:

```yaml
# .github/codeql/extensions/barriers.yml
extensions:
  # Barrier: il metodo sanitize() rende i dati sicuri
  - addsTo:
      pack: codeql/javascript-all
      extensible: barrierModel
    data:
      # [tipo, path di accesso, input, kind, provenienza]
      - ["Sanitizer", "Member[sanitize]",
         "ReturnValue", "sql-injection", "manual"]
      - ["Sanitizer", "Member[escapeHtml]",
         "ReturnValue", "xss", "manual"]
      - ["Validator", "Member[validateInput]",
         "ReturnValue", "path-injection", "manual"]

  # Barrier guard: isValid() restituisce true se i dati sono sicuri
  - addsTo:
      pack: codeql/javascript-all
      extensible: barrierGuardModel
    data:
      # [tipo, path, input, kind, value booleano, provenienza]
      - ["InputValidator", "Member[isValid]",
         "Argument[0]", "sql-injection", "true", "manual"]
      - ["AuthChecker", "Member[isAuthenticated]",
         "Argument[0]", "auth-bypass", "true", "manual"]
```

### Linguaggi supportati per models-as-data

| Linguaggio | Source/Sink | Summary | Barrier | Barrier Guard |
|---|---|---|---|---|
| C/C++ | Sì | Sì | Sì (2.25.2+) | Sì (2.25.2+) |
| C# | Sì | Sì | Sì (2.25.2+) | Sì (2.25.2+) |
| Go | Sì | Sì | Sì (2.25.2+) | Sì (2.25.2+) |
| Java/Kotlin | Sì | Sì | Sì (2.25.2+) | Sì (2.25.2+) |
| JavaScript/TS | Sì | Sì | Sì (2.25.2+) | Sì (2.25.2+) |
| Python | Sì | Sì | Sì (2.25.2+) | Sì (2.25.2+) |
| Ruby | Sì | Sì | Sì (2.25.2+) | Sì (2.25.2+) |
| Rust | Sì | Sì | Sì (2.25.2+) | Sì (2.25.2+) |

### Integrazione nel workflow

```yaml
# Usare le data extensions nel workflow CodeQL
- uses: github/codeql-action/init@v4
  with:
    languages: javascript-typescript
    queries: security-extended
    # Le data extensions in .github/codeql/extensions/
    # vengono caricate automaticamente
    config-file: .github/codeql/codeql-config.yml
```

```yaml
# .github/codeql/codeql-config.yml
name: "CodeQL Config con data extensions"
queries:
  - uses: security-extended
# I file .yml in .github/codeql/extensions/ sono caricati automaticamente
# se il config-file è nella stessa directory o una directory padre
```

---

## Threat model configuration

### Cos'è un threat model

Un threat model definisce quali fonti di input sono considerate potenzialmente pericolose. CodeQL supporta diversi livelli di threat model:

| Threat Model | Descrizione | Esempio |
|---|---|---|
| **remote** | Input da fonti remote (rete, HTTP) | `req.body`, `req.query`, API calls |
| **local** | Input da fonti locali (file system, env vars, stdin) | `process.env`, `fs.readFile()`, `argv` |
| **environment** | Solo variabili d'ambiente | `process.env.DATABASE_URL` |
| **database** | Dati letti da database | `db.query()` risultati |

### Configurazione nel workflow

```yaml
# .github/codeql/codeql-config.yml
name: "CodeQL con threat model personalizzato"

queries:
  - uses: security-extended

threat-models:
  # Abilitare il threat model remoto (default)
  - remote

  # Abilitare anche il threat model locale
  # (considera env vars, file system come untrusted)
  - local

  # Oppure specificare granularmente
  # - environment   # solo env vars
```

### Quando usare i diversi threat model

| Scenario | Threat model consigliato |
|---|---|
| Applicazione web esposta a internet | `remote` (default) |
| Microservizio interno con input da altri servizi | `remote` + `local` |
| CLI tool che legge file locali | `local` |
| Applicazione che processa env vars da CI/CD | `remote` + `environment` |
| Audit di sicurezza approfondito | `remote` + `local` (massima copertura) |

### Esempio pratico: ambiente vs. remote

Con threat model `remote` (default), CodeQL segnala solo le vulnerabilità dove i dati provengono dalla rete:

```javascript
// Segnalato con threat model "remote":
app.get('/search', (req, res) => {
  const query = req.query.q;        // ← source remota
  db.query("SELECT * FROM users WHERE name = '" + query + "'");  // SQL injection
});

// NON segnalato con solo "remote", MA segnalato con "local":
const configPath = process.env.CONFIG_FILE;   // ← source locale
const data = fs.readFileSync(configPath);      // path traversal potenziale
```

Abilitando `local`, CodeQL considererà anche `process.env` e `fs.readFileSync` come potenziali fonti di dati contaminati, aumentando la copertura ma anche i possibili falsi positivi.

---

## Multi-repository variant analysis (MRVA)

### Cos'è MRVA

La Multi-Repository Variant Analysis (MRVA) permette di eseguire una query CodeQL su fino a 1.000 repository simultaneamente, utilizzando database pre-costruiti. È uno strumento fondamentale per la ricerca di vulnerabilità su larga scala.

### Casi d'uso

| Caso d'uso | Descrizione |
|---|---|
| **Variant analysis** | Dopo aver trovato una vulnerabilità in un progetto, cercare lo stesso pattern in progetti simili |
| **Audit organizzazione** | Verificare che nessun repository dell'organizzazione contenga un pattern vulnerabile |
| **Ricerca zero-day** | Cercare nuove classi di vulnerabilità in repository open source |
| **Compliance check** | Verificare che tutti i repository rispettino una policy di sicurezza specifica |
| **Pre-disclosure** | Prima di pubblicare un advisory, verificare l'impatto su larga scala |

### MRVA da VS Code

#### Setup

```text
1. Installare VS Code + extension "CodeQL"
2. Aprire il CodeQL Starter Workspace
3. Nella barra laterale CodeQL → "Variant Analysis Repositories"
4. Aggiungere liste di repository:
   - Repository individuali
   - Liste personalizzate
   - Top 100/1000 di un linguaggio su GitHub
```

#### Workflow

```text
1. Scrivere una query QL (o selezionare una esistente)
2. Click destro → "Run Variant Analysis"
3. Selezionare la lista di repository target
4. GitHub Actions esegue la query su tutti i repository
5. I risultati vengono aggregati e mostrati in VS Code
```

### MRVA da CLI con gh-mrva

```bash
# Installare l'extension gh-mrva
gh extension install GitHubSecurityLab/gh-mrva

# Creare una lista di repository
gh mrva list create my-org-repos \
  --repos myorg/repo1 myorg/repo2 myorg/repo3

# Oppure usare una lista predefinita
gh mrva list create top-js --top 100 --language javascript

# Eseguire una query su tutti i repository della lista
gh mrva submit \
  --query ./queries/sql-injection.ql \
  --list my-org-repos \
  --language javascript

# Controllare lo stato
gh mrva status

# Scaricare i risultati
gh mrva download --output ./mrva-results/
```

### MRVA con mrva (tool Trail of Bits)

Per un approccio terminal-first che esegue tutto localmente:

```bash
# Installare mrva (richiede CodeQL CLI)
pip install mrva

# Scaricare database CodeQL da GitHub
mrva download --language javascript \
  --repos myorg/repo1 myorg/repo2 \
  --output ./databases/

# Eseguire la query su tutti i database scaricati
mrva analyze \
  --query ./queries/my-query.ql \
  --databases ./databases/ \
  --output ./results/

# Output in formato SARIF o CSV
mrva analyze \
  --query ./queries/my-query.ql \
  --databases ./databases/ \
  --format sarif \
  --output ./results/results.sarif
```

### Esempio pratico: trovare Log4Shell su larga scala

```ql
/**
 * @name Log4j JNDI injection (Log4Shell)
 * @kind path-problem
 * @problem.severity error
 * @id custom/log4shell-variant
 * @tags security
 *       external/cwe/cwe-917
 */

import java
import semmle.java.dataflow.TaintTracking
import DataFlow::PathGraph

class Log4jLogCall extends MethodAccess {
  Log4jLogCall() {
    this.getMethod().getDeclaringType().hasQualifiedName("org.apache.logging.log4j", _) and
    this.getMethod().getName().regexpMatch("(info|warn|error|debug|fatal|trace|log)")
  }
}

class Log4ShellConfig extends TaintTracking::Configuration {
  Log4ShellConfig() { this = "Log4ShellConfig" }

  override predicate isSource(DataFlow::Node source) {
    exists(Parameter p |
      p.getCallable().isPublic() and
      source.asParameter() = p
    )
  }

  override predicate isSink(DataFlow::Node sink) {
    exists(Log4jLogCall call |
      sink.asExpr() = call.getAnArgument()
    )
  }
}

from Log4ShellConfig cfg, DataFlow::PathNode source, DataFlow::PathNode sink
where cfg.hasFlowPath(source, sink)
select sink.getNode(), source, sink,
  "Potenziale Log4Shell: dati non fidati dall'$@ raggiungono un log Log4j.",
  source.getNode(), "input esterno"
```

---

## Security campaigns

### Cos'è una security campaign

Le security campaigns sono una funzionalità GA (Generally Available) di GitHub Code Security che permette di organizzare la remediation delle vulnerabilità su larga scala. Una campagna raggruppa alert di sicurezza, li assegna ai developer, e utilizza Copilot Autofix per suggerire fix automatici.

### Statistiche di efficacia

| Metrica | Senza campagne | Con campagne + Copilot Autofix |
|---|---|---|
| Tasso di remediation | ~10% degli alert | ~55% degli alert |
| Tempo medio per fix (MTTR) | Settimane/mesi | Ore/giorni |
| Coinvolgimento developer | Basso (alert ignorati) | Alto (assegnati + fix suggeriti) |

### Creare una security campaign

```text
Organization → Security → Campaigns → New campaign

Configurare:
1. Nome: "Q3 2026 — Eliminare SQL Injection"
2. Filtri: tool:codeql, rule:sql-injection, severity:critical+high
3. Repository: tutti o selezionati
4. Durata: 30 giorni
5. Manager: @security-team
6. Assegnazione: automatica ai code owner
```

### Workflow di una campagna

```text
1. Security manager crea la campagna
   │
2. Alert vengono raggruppati e assegnati ai developer
   │
3. Copilot Autofix genera fix suggeriti per ogni alert
   │
4. Developer ricevono notifica con:
   │  - Descrizione della vulnerabilità
   │  - Fix suggerito da Copilot
   │  - Pulsante "Crea PR con fix"
   │
5. Developer rivede, modifica se necessario, e crea la PR
   │
6. PR viene mergiata → alert risolto
   │
7. Security manager monitora il progresso nella dashboard
```

### Copilot Autofix per alert esistenti

A partire da ottobre 2025, è possibile assegnare alert di code scanning direttamente a Copilot come coding agent:

```text
Security tab → Code scanning alerts → Seleziona alert
  → "Assign to Copilot" (beta)

Copilot:
1. Analizza il codice circostante
2. Comprende il tipo di vulnerabilità (CWE)
3. Genera un fix contestualizzato
4. Crea automaticamente una PR con:
   - Il fix applicato
   - Spiegazione del cambiamento
   - Test suggeriti (quando possibile)
```

### Linguaggi supportati per Copilot Autofix

| Linguaggio | Stato (2026) |
|---|---|
| JavaScript/TypeScript | GA |
| Python | GA |
| Java/Kotlin | GA |
| C# | GA |
| Go | GA |
| C/C++ | GA |
| Ruby | GA |
| Swift | GA |
| Rust | Beta |

---

## Secret scanning — rilevamento generico con AI

### Architettura del rilevamento AI

GitHub utilizza un sistema a due modelli per rilevare password e secret generici che non corrispondono ai pattern di provider noti:

```text
Commit push / scan repository
         │
         ▼
┌─────────────────────┐
│  Primo modello       │   ← GPT-3.5-Turbo: scansione rapida,
│  (scansione iniziale)│      identifica candidati
└──────────┬──────────┘
           │ candidati
           ▼
┌─────────────────────┐
│  Secondo modello     │   ← GPT-4: conferma con alta precisione,
│  (conferma)          │      tecnica MetaReflection di Microsoft
└──────────┬──────────┘
           │ confermati
           ▼
┌─────────────────────┐
│  Alert creato        │   ← Tipo: "generic" (non "experimental")
│  (severity: high)    │      dal marzo 2025
└─────────────────────┘
```

### Risultati del sistema AI

| Metrica | Valore |
|---|---|
| Riduzione falsi positivi (vs. solo regex) | 94% |
| Copertura repository (con Secret Protection) | ~35% dei repos rileva password |
| Tipo di secret rilevati | Password generiche in contenuto git |

### Validazione dei secret (validity checks)

I validity checks verificano se un secret rilevato è ancora attivo, permettendo di prioritizzare la risposta:

```text
Alert: AWS Access Key trovata in config.js

Stato validità:
  ✓ Active    — Il secret è ancora valido. AZIONE IMMEDIATA richiesta.
  ✗ Inactive  — Il secret è stato revocato. Priorità bassa.
  ? Unknown   — Impossibile verificare. Trattare come attivo.
```

Provider con supporto validity check (2026):

| Provider | Validity Check |
|---|---|
| GitHub | Sì |
| AWS | Sì |
| Azure | Sì |
| npm | Sì (dal 2026) |
| Stripe | Sì |
| Airtable | Sì (dal 2026) |
| DeepSeek | Sì (dal 2026) |
| Pinecone | Sì (dal 2026) |
| Sentry | Sì (dal 2026) |

### Metadata estesi per secret

Dal febbraio 2026, gli alert di secret scanning includono metadata estesi:

```text
Alert: GitHub Personal Access Token

Metadata estesi:
  - Owner: mario.rossi@example.com
  - Creato il: 2025-11-15
  - Scade il: 2026-11-15
  - Identifier: ghp_xxx...xxx
  - Permessi: repo, read:org
```

### Pattern non-provider

I pattern non-provider rilevano secret che non sono legati a un provider specifico:

| Tipo | Esempio |
|---|---|
| RSA private key | `-----BEGIN RSA PRIVATE KEY-----` |
| Generic API key | `api_key = "abc123def456..."` |
| Connection string | `postgres://user:pass@host:5432/db` |
| JWT secret | `jwt_secret = "my-super-secret-key"` |
| Generic password | `password = "P@ssw0rd123!"` |

---

## Dependabot auto-triage rules

### Panoramica

Le auto-triage rules permettono di gestire automaticamente gli alert Dependabot in base a regole personalizzate, riducendo il rumore e concentrando l'attenzione sulle vulnerabilità che contano.

### Regole preset di GitHub

GitHub fornisce regole preset che si applicano automaticamente:

```text
Preset: "Dismiss low-impact alerts for development dependencies"

Logica:
  Se:
    - L'alert è su una dipendenza di sviluppo (devDependency)
    - La vulnerabilità NON ha un exploit noto
    - La vulnerabilità NON riguarda malware
    - La severity è low o medium
  Allora:
    - Dismiss automatico con stato "auto-dismissed"
    - L'alert rimane visibile ma non genera rumore
```

### Regole custom

```text
Organization Settings → Code security → Dependabot
  → Auto-triage rules → New rule

Esempio 1: Ignorare vulnerabilità in dipendenze di test
  Nome: "Dismiss test-only deps"
  Condizioni:
    - Ecosistema: npm
    - Scope: development
    - Severity: low, medium
  Azione: Dismiss

Esempio 2: Auto-dismiss per CWE specifici a basso rischio
  Nome: "Low risk CWE auto-dismiss"
  Condizioni:
    - CWE: CWE-400 (Uncontrolled Resource Consumption)
    - Severity: low
    - Nessun exploit noto
  Azione: Dismiss

Esempio 3: Tenere aperti solo gli alert critici per un pacchetto
  Nome: "Only critical for lodash"
  Condizioni:
    - Package name: lodash
    - Severity: NOT critical
  Azione: Dismiss
```

### Configurazione via API

```bash
# Creare una regola auto-triage per l'organizzazione
gh api -X POST /orgs/myorg/dependabot/auto-triage-rules \
  -f name="Dismiss low dev deps" \
  -f target="development" \
  -f severity='["low", "medium"]' \
  -f action="dismiss" \
  -f ecosystem="npm"

# Listare le regole esistenti
gh api /orgs/myorg/dependabot/auto-triage-rules

# Eliminare una regola
gh api -X DELETE /orgs/myorg/dependabot/auto-triage-rules/42
```

### Flusso decisionale per auto-triage

```text
Nuovo alert Dependabot
    │
    ├─ È malware? ──────────────────── Sì → BLOCCA (mai dismiss)
    │
    ├─ Ha exploit noto (EPSS alto)? ── Sì → MANTIENI aperto
    │
    ├─ È dipendenza runtime? ───────── Sì → MANTIENI aperto
    │                                         (anche se severity bassa)
    │
    ├─ È dipendenza dev + severity ── Sì → DISMISS (preset GitHub)
    │   bassa + no exploit?
    │
    ├─ Matcha una regola custom? ──── Sì → Applica azione regola
    │
    └─ Default ──────────────────────── MANTIENI aperto
```

---

## GHAS 2025: Secret Protection e Code Security

### Ristrutturazione dei prodotti

Dal 1 aprile 2025, GitHub Advanced Security è stato scomposto in due prodotti acquistabili separatamente:

```text
┌─────────────────────────────────────────────────┐
│            Prima: GitHub Advanced Security       │
│   (un unico prodotto, ~$49/committer/mese)       │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
   ┌────────────────────────────────────┐
   │                                    │
   ▼                                    ▼
┌──────────────────────┐  ┌─────────────────────────┐
│ GitHub Secret         │  │ GitHub Code Security     │
│ Protection            │  │                          │
│ $19/committer/mese    │  │ $30/committer/mese       │
│                       │  │                          │
│ Include:              │  │ Include:                  │
│ - Secret scanning     │  │ - Code scanning (CodeQL) │
│ - Push protection     │  │ - Copilot Autofix        │
│ - Custom patterns     │  │ - Security campaigns     │
│ - AI generic detect.  │  │ - Dependency Review Act. │
│ - Validity checks     │  │ - Security Overview      │
│ - Security insights   │  │ - Third-party SARIF      │
└──────────────────────┘  └─────────────────────────┘
```

### Confronto dettagliato

| Funzionalità | Secret Protection ($19) | Code Security ($30) | Entrambi ($49) |
|---|---|---|---|
| Secret scanning | Incluso | — | Incluso |
| Push protection | Incluso | — | Incluso |
| Custom patterns | Incluso | — | Incluso |
| AI generic detection | Incluso | — | Incluso |
| Validity checks | Incluso | — | Incluso |
| Code scanning (CodeQL) | — | Incluso | Incluso |
| Copilot Autofix | — | Incluso | Incluso |
| Security campaigns | — | Incluso | Incluso |
| Dependency Review Action | — | Incluso | Incluso |
| Security Overview | Parziale | Completo | Completo |
| Custom CodeQL queries | — | Incluso | Incluso |

### Disponibilità per piano GitHub

| Piano GitHub | Secret Protection | Code Security |
|---|---|---|
| Free (public repos) | Gratuito | Gratuito |
| Free (private repos) | Non disponibile | Non disponibile |
| Team | Acquistabile ($19) | Acquistabile ($30) |
| Enterprise | Acquistabile ($19) | Acquistabile ($30) |

Nota importante: i clienti GitHub Team possono ora acquistare questi prodotti di sicurezza senza necessità di una sottoscrizione Enterprise — una novità significativa rispetto al modello precedente.

---

## SARIF avanzato

### Fingerprint e partialFingerprints

I fingerprint permettono di tracciare un alert tra diverse esecuzioni dell'analisi, anche se il codice cambia (es. righe aggiunte/rimosse):

```json
{
  "results": [
    {
      "ruleId": "js/sql-injection",
      "fingerprints": {
        "0": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
      },
      "partialFingerprints": {
        "primaryLocationLineHash": "abc123def456",
        "primaryLocationStartColumnFingerprint": "5",
        "contextRegionFingerprint": "e7f8a9b0c1d2"
      }
    }
  ]
}
```

| Tipo | Scopo |
|---|---|
| `fingerprints` | Identificatore stabile e completo del risultato |
| `partialFingerprints` | Frammenti che contribuiscono all'identificazione (line hash, column, context) |

GitHub usa i `partialFingerprints` per determinare se un alert è nuovo o già esistente, permettendo di mostrare correttamente "New alert" vs. "Existing alert" nelle PR.

### Taxonomie

Le taxonomie classificano i risultati in sistemi standard (CWE, OWASP) in modo più strutturato rispetto ai semplici tag:

```json
{
  "runs": [
    {
      "taxonomies": [
        {
          "name": "CWE",
          "version": "4.14",
          "organization": "MITRE",
          "shortDescription": { "text": "Common Weakness Enumeration" },
          "informationUri": "https://cwe.mitre.org/",
          "taxa": [
            {
              "id": "79",
              "name": "ImproperNeutralizationOfInput",
              "shortDescription": { "text": "Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')" }
            },
            {
              "id": "89",
              "name": "SqlInjection",
              "shortDescription": { "text": "Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')" }
            }
          ]
        }
      ],
      "results": [
        {
          "ruleId": "js/sql-injection",
          "taxa": [
            {
              "toolComponent": { "name": "CWE" },
              "id": "89"
            }
          ]
        }
      ]
    }
  ]
}
```

### Invocations

L'oggetto `invocations` documenta l'esecuzione dello strumento di analisi:

```json
{
  "runs": [
    {
      "invocations": [
        {
          "executionSuccessful": true,
          "startTimeUtc": "2026-05-24T10:30:00Z",
          "endTimeUtc": "2026-05-24T10:35:42Z",
          "exitCode": 0,
          "toolExecutionNotifications": [
            {
              "level": "warning",
              "message": {
                "text": "Some files were not analyzed due to extraction errors."
              },
              "descriptor": { "id": "extraction-warning" }
            }
          ],
          "properties": {
            "queriesExecuted": 496,
            "databaseSize": "1.2 GB",
            "peakMemory": "4.8 GB"
          }
        }
      ]
    }
  ]
}
```

### Convertire output di tool terzi in SARIF

```python
#!/usr/bin/env python3
"""Convertire output di un tool custom in formato SARIF 2.1.0."""

import json
import sys

def create_sarif(findings: list[dict]) -> dict:
    """Genera un documento SARIF da una lista di finding."""
    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "MyCustomScanner",
                        "version": "1.0.0",
                        "informationUri": "https://example.com/scanner",
                        "rules": _extract_rules(findings)
                    }
                },
                "results": [_to_result(f) for f in findings],
                "taxonomies": [
                    {
                        "name": "CWE",
                        "version": "4.14",
                        "organization": "MITRE",
                        "informationUri": "https://cwe.mitre.org/"
                    }
                ]
            }
        ]
    }

def _extract_rules(findings: list[dict]) -> list[dict]:
    seen = set()
    rules = []
    for f in findings:
        if f["rule_id"] not in seen:
            seen.add(f["rule_id"])
            rules.append({
                "id": f["rule_id"],
                "shortDescription": {"text": f["title"]},
                "defaultConfiguration": {
                    "level": f.get("level", "warning")
                },
                "properties": {
                    "tags": f.get("tags", [])
                }
            })
    return rules

def _to_result(finding: dict) -> dict:
    return {
        "ruleId": finding["rule_id"],
        "level": finding.get("level", "warning"),
        "message": {"text": finding["message"]},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": finding["file"],
                        "uriBaseId": "%SRCROOT%"
                    },
                    "region": {
                        "startLine": finding["line"],
                        "startColumn": finding.get("column", 1)
                    }
                }
            }
        ],
        "partialFingerprints": {
            "primaryLocationLineHash": finding.get("hash", "")
        }
    }

if __name__ == "__main__":
    findings = json.load(sys.stdin)
    sarif = create_sarif(findings)
    json.dump(sarif, sys.stdout, indent=2)
```

---

## CodeQL Action v4 e migrazione

### Migrazione da v3 a v4

CodeQL Action v4 è stato rilasciato il 7 ottobre 2025 e utilizza il runtime Node.js 24. La v3 sarà deprecata a dicembre 2026.

### Modifiche necessarie

```yaml
# Prima (v3)
- uses: github/codeql-action/init@v3
- uses: github/codeql-action/analyze@v3

# Dopo (v4)
- uses: github/codeql-action/init@v4
- uses: github/codeql-action/analyze@v4
```

### Nuove funzionalità in v4

| Funzionalità | v3 | v4 |
|---|---|---|
| Runtime Node.js | 20 | 24 |
| TRAP caching | Sì | Migliorato (30% più veloce) |
| Build mode detection | Manuale | Automatico per più linguaggi |
| SARIF upload | Limite 10 MB | Limite 20 MB |
| Data extensions | Supporto base | Supporto completo (barrier/barrierGuard) |
| Caching database | Opzionale | Default attivo |

### Statistiche di copertura query (2026)

Con CodeQL 2.25.3+, il numero di query di sicurezza disponibili:

| Suite | Query totali | CWE coperte |
|---|---|---|
| Default | 496 | 169 |
| Extended | 627 (496 + 131) | 201 (169 + 32) |
| Security-and-quality | ~800+ | 201 + quality |

### Performance tuning

```yaml
# Ottimizzare le performance di CodeQL
- uses: github/codeql-action/init@v4
  with:
    languages: javascript-typescript
    queries: security-extended

    # TRAP caching: riutilizza dati tra esecuzioni
    trap-caching: true

    # RAM allocation (default: auto)
    ram: 8192  # MB

    # Thread count (default: auto)
    threads: 4

    # Timeout per singola query
    # (in codeql-config.yml)
    # timeout-per-query: 300  # secondi
```

```yaml
# .github/codeql/codeql-config.yml
name: "CodeQL Optimized"
queries:
  - uses: security-extended

# Escludere codice non rilevante per ridurre tempi
paths-ignore:
  - "**/test/**"
  - "**/tests/**"
  - "**/*.test.*"
  - "**/*.spec.*"
  - "**/node_modules/**"
  - "**/vendor/**"
  - "**/dist/**"
  - "**/build/**"
  - "**/generated/**"
  - "**/__fixtures__/**"
  - "**/__snapshots__/**"
  - "**/migrations/**"
  - "**/coverage/**"

# Timeout per query complesse
query-filters:
  - exclude:
      tags contain: experimental
```

---

## CodeQL per linguaggi compilati — configurazione build

CodeQL analizza linguaggi compilati (C/C++, Java/Kotlin, C#, Swift, Go, Rust) in modo
fondamentalmente diverso rispetto ai linguaggi interpretati. Per i linguaggi interpretati
(JavaScript, TypeScript, Python, Ruby) l'extractor opera direttamente sul codice sorgente,
ma per i linguaggi compilati deve **osservare il processo di compilazione** per costruire
un database accurato che includa informazioni su tipi, risoluzione dei simboli e flusso
di controllo inter-procedurale.

### Tre modalità di build

A partire da CodeQL CLI 2.15+ e CodeQL Action v3/v4, esistono tre modalità di build
dichiarate tramite la proprietà `build-mode` nella configurazione del workflow:

| Modalità | Comportamento | Linguaggi supportati |
|----------|--------------|----------------------|
| `none` | Analisi senza compilazione; l'extractor lavora solo sul sorgente. Più veloce ma meno preciso per linguaggi compilati. | Java/Kotlin (GA), C# (GA), Swift (beta), C/C++ (beta da CodeQL 2.20.0) |
| `autobuild` | CodeQL tenta di individuare automaticamente il sistema di build (Maven, Gradle, MSBuild, CMake, make, xcodebuild) e avvia la compilazione. | Tutti i linguaggi compilati |
| `manual` | L'utente specifica esplicitamente i comandi di build nel workflow. Necessario quando autobuild fallisce o quando la build richiede configurazione speciale. | Tutti i linguaggi compilati |

### Guida per linguaggio

**C/C++** — Il linguaggio più complesso da configurare. `autobuild` cerca un `Makefile`,
`CMakeLists.txt` o `configure` nella root. Per progetti con toolchain personalizzate
(cross-compilation, Bazel, Meson), la modalità `manual` è quasi sempre necessaria.
La modalità `none` è disponibile in beta da CodeQL 2.20.0 (febbraio 2025) e offre
risultati ragionevoli per analisi di base, ma perde precisione sui tipi e sui template C++
rispetto a una build completa. Consiglio: usare `none` per triage rapido, `manual` per
scansioni definitive in CI.

```yaml
# C/C++ con build manuale
- name: Configure build
  run: |
    mkdir -p build && cd build
    cmake .. -DCMAKE_BUILD_TYPE=Release \
             -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
- name: Initialize CodeQL
  uses: github/codeql-action/init@v4
  with:
    languages: cpp
    build-mode: manual
- name: Build
  run: cmake --build build --parallel $(nproc)
- name: Perform CodeQL Analysis
  uses: github/codeql-action/analyze@v4
```

**Java/Kotlin** — `autobuild` funziona bene con Maven (`pom.xml`) e Gradle
(`build.gradle` / `build.gradle.kts`). Per progetti multi-modulo Gradle, assicurarsi
che il task `compileJava` sia raggiungibile dal modulo root. La modalità `none` è GA
dal 2024 e produce risultati di qualità comparabile alla build completa per la maggior
parte dei progetti Java, poiché l'extractor riesce a risolvere i tipi dal bytecode
delle dipendenze scaricate. Attenzione: con `none`, le dipendenze devono essere risolvibili
(es. `mvn dependency:resolve` o cache Gradle presente).

**C#** — `autobuild` cerca file `.sln` o `.csproj` e invoca `dotnet build` o `msbuild`.
Per soluzioni con più target framework o build condizionali, preferire `manual`.
La modalità `none` è GA e funziona bene per la maggior parte dei progetti .NET 6+.
Per .NET Framework legacy, `manual` con `msbuild` resta la scelta più affidabile.

**Swift** — Supporto in beta. `autobuild` usa `xcodebuild` cercando un file `.xcodeproj`
o `.xcworkspace`. Richiede macOS runner (`runs-on: macos-latest`). La modalità `none`
è in beta e ha limitazioni sulla risoluzione dei moduli Swift Package Manager complessi.

**Go** — Go è un caso speciale: pur essendo compilato, CodeQL lo tratta come un linguaggio
con extractor diretto. La modalità `none` è il default e funziona perfettamente perché
il compilatore Go è deterministico e veloce. Non serve configurazione di build nella
stragrande maggioranza dei casi.

**Rust** — Supporto sperimentale aggiunto nel 2025. Richiede la modalità `manual` con
`cargo build`. L'extractor Rust è ancora in fase di maturazione; la copertura delle
query di sicurezza è limitata rispetto a C/C++ o Java.

### Workflow con build mode misto (multi-linguaggio)

Quando un repository contiene sia codice interpretato che compilato, si possono usare
build mode diversi nella stessa matrix:

```yaml
strategy:
  fail-fast: false
  matrix:
    include:
      - language: javascript-typescript
        build-mode: none
      - language: java-kotlin
        build-mode: none          # GA, buona copertura senza build
      - language: cpp
        build-mode: manual        # richiede build esplicita
steps:
  - uses: actions/checkout@v4
  - name: Initialize CodeQL
    uses: github/codeql-action/init@v4
    with:
      languages: ${{ matrix.language }}
      build-mode: ${{ matrix.build-mode }}
  - if: matrix.build-mode == 'manual'
    name: Manual build
    shell: bash
    run: |
      mkdir -p build && cd build
      cmake .. && make -j$(nproc)
  - name: Perform CodeQL Analysis
    uses: github/codeql-action/analyze@v4
    with:
      category: "/language:${{ matrix.language }}"
```

### Diagnostica build fallite

Quando `autobuild` fallisce, CodeQL genera log diagnostici accessibili tramite:

```bash
# Scaricare i log dal workflow run
gh run download <run-id> --name codeql-logs

# Oppure tramite CLI locale
codeql database create my-db --language=cpp --command="make" \
  --verbosity=debug 2>&1 | tee codeql-build.log
```

Errori comuni: dipendenze mancanti nel runner, variabili d'ambiente non impostate,
SDK/toolchain non installati. La soluzione è quasi sempre passare a `manual` e
replicare esattamente la pipeline di build di produzione.

---

## CodeQL CLI vs VS Code extension — confronto workflow

CodeQL offre due interfacce principali per lo sviluppo e il debugging di query:
la **CLI** (`codeql`) e l'**estensione VS Code** (CodeQL for VS Code). Entrambe
condividono lo stesso motore di analisi, ma differiscono nel workflow operativo.

### Tabella comparativa

| Aspetto | CodeQL CLI | VS Code Extension |
|---------|-----------|-------------------|
| **Installazione** | Download manuale o `gh extension install github/gh-codeql` | Marketplace VS Code, installa CLI automaticamente |
| **Gestione CLI** | Manuale (PATH, aggiornamenti) | Automatica: l'estensione scarica e aggiorna la CLI |
| **Creazione database** | `codeql database create` con controllo completo | Pulsante "Download Database" da GitHub o creazione locale |
| **Esecuzione query** | `codeql query run` / `codeql database analyze` | Click destro → "Run Query" con risultati inline |
| **Visualizzazione risultati** | SARIF, CSV, o formato tabulare in terminale | Pannello dedicato con navigazione source-to-sink |
| **Debugging query** | Limited: `--dump-ra`, log verbosi | Quick Evaluation su espressioni parziali, AST viewer |
| **Autocompletamento QL** | Nessuno (editor generico) | IntelliSense completo per QL |
| **MRVA** | Non supportato direttamente | Integrato: analisi su fino a 1.000 repository |
| **Automazione CI** | Ideale: scriptabile, integrabile in pipeline | Non applicabile |
| **Pack management** | `codeql pack create`, `publish`, `download` | Supporto tramite CLI integrata |
| **Threat model config** | Flag `--threat-model` nella CLI | Configurabile in settings |

### Quando usare la CLI

- **Pipeline CI/CD**: la CLI è l'unica opzione per automazione. L'Action v4 la usa
  internamente.
- **Scripting e batch**: analisi su molti repository in sequenza, integrazione con
  sistemi di ticketing, generazione report automatici.
- **Ambienti headless**: server di build, container Docker, runner self-hosted senza
  interfaccia grafica.
- **Controllo granulare**: selezione precisa di query suite, filtri per severity,
  configurazione RAM/thread, timeout per query.
- **Database forensics**: ispezione diretta del database con `codeql dataset`
  per comprendere la struttura dell'AST.

```bash
# Workflow CLI tipico per analisi locale
codeql database create ./codeql-db \
  --language=python \
  --source-root=./src \
  --threads=0 \
  --ram=8192

codeql database analyze ./codeql-db \
  codeql/python-queries:codeql-suites/python-security-and-quality.qls \
  --format=sarif-latest \
  --output=results.sarif \
  --threads=0
```

### Quando usare VS Code

- **Sviluppo query custom**: l'autocompletamento QL, il syntax highlighting e
  il Quick Evaluation rendono VS Code enormemente più produttivo per scrivere
  e debuggare query.
- **Esplorazione AST**: il pannello AST Viewer permette di navigare la struttura
  del codice analizzato e capire quali classi QL modellano ciascun costrutto.
- **MRVA (Multi-Repository Variant Analysis)**: l'estensione permette di lanciare
  una query su fino a 1.000 repository GitHub direttamente dall'editor,
  visualizzando i risultati in un pannello dedicato. Fondamentale per verificare
  se una vulnerabilità scoperta in un progetto esiste anche altrove.
- **Formazione**: l'ambiente integrato abbassa la barriera d'ingresso per chi
  sta imparando QL.
- **Triage interattivo**: navigazione click-through dal risultato della query
  al codice sorgente, con evidenziazione del data flow path.

### Gestione automatica della CLI

L'estensione VS Code gestisce automaticamente il download, l'installazione e
l'aggiornamento della CLI CodeQL. Quando si apre un workspace con file `.ql`,
l'estensione verifica la versione della CLI e la aggiorna se necessario.
È possibile sovrascrivere questo comportamento puntando a una CLI installata
manualmente tramite il setting `codeql.cli.executablePath`. Questo è utile
quando si vuole testare una versione specifica della CLI o quando si lavora
offline.

---

## Default vs extended query suites — analisi dettagliata

CodeQL organizza le proprie query in **suite** (collezioni), ciascuna con un
profilo di copertura e precisione diverso. La scelta della suite influenza
direttamente il numero di alert generati, la copertura CWE e il rapporto
segnale/rumore.

### Suite disponibili

| Suite | Query (2.25.3+) | CWE coperti | Precisione | Uso tipico |
|-------|-----------------|-------------|------------|------------|
| `default` | ~496 | ~169 | Alta (≥ high precision) | CI/CD su ogni PR, scansione continua |
| `security-extended` | ~627 | ~201 | Media-alta | Analisi periodica, audit di sicurezza |
| `security-and-quality` | ~800+ | ~201+ qualità | Variabile | Revisione completa, analisi una tantum |

### Come funziona il filtro di precisione

Ogni query CodeQL ha metadata che includono `@precision` (very-high, high, medium, low)
e `@problem.severity` (error, warning, recommendation). La suite `default` include
solo query con `@precision` high o very-high, eliminando quelle che tendono a generare
falsi positivi. La suite `extended` abbassa la soglia a medium, aggiungendo ~131 query
in più che coprono 32 CWE aggiuntivi ma con un tasso di falsi positivi più alto.

### Matrice decisionale

| Scenario | Suite consigliata | Motivazione |
|----------|------------------|-------------|
| PR check obbligatorio | `default` | Basso rumore, non blocca sviluppatori con falsi positivi |
| Scansione notturna su branch principale | `security-extended` | Più copertura, triage il giorno dopo |
| Audit pre-rilascio | `security-and-quality` | Massima copertura, accettabile più triage |
| Compliance SOC 2 / ISO 27001 | `security-extended` | Buon bilanciamento copertura/precisione |
| Progetto open source ad alta visibilità | `default` + MRVA extended | Default in CI, extended per analisi periodica |
| Repository con molto codice legacy | `default` inizialmente | Evita flood di alert; gradualmente aggiungere extended |

### Configurazione nel workflow

```yaml
# Default suite (implicita)
- uses: github/codeql-action/init@v4
  with:
    languages: javascript-typescript
    # queries: nessuna specifica = default suite

# Extended suite
- uses: github/codeql-action/init@v4
  with:
    languages: javascript-typescript
    queries: security-extended

# Security and quality
- uses: github/codeql-action/init@v4
  with:
    languages: python
    queries: security-and-quality

# Default + query custom aggiuntive
- uses: github/codeql-action/init@v4
  with:
    languages: java-kotlin
    queries: +./custom-queries/
```

Il prefisso `+` è fondamentale: senza di esso, le query custom **sostituiscono**
la suite default anziché aggiungersi. Con `+`, le query custom si aggiungono
alla suite selezionata.

### Migrazione graduale da default a extended

Per organizzazioni che vogliono aumentare la copertura senza sovraccaricare
i team di sviluppo, la strategia raccomandata è:

1. Attivare `security-extended` in modalità **audit** (non bloccante su PR)
2. Analizzare gli alert aggiuntivi per 2-4 settimane
3. Creare regole di dismissal per i falsi positivi ricorrenti tramite
   `code-scanning-config.yml` con `query-filters`
4. Quando il tasso di falsi positivi è accettabile, rendere la suite bloccante

---

## Secret scanning — configurazione pattern in push protection

Il secret scanning di GitHub identifica credenziali, token e chiavi API
committati accidentalmente nel codice sorgente. La **push protection**
estende questa funzionalità bloccando il push **prima** che il secret
raggiunga il repository remoto, prevenendo l'esposizione anziché limitarsi
a segnalarla post-commit.

### Evoluzione 2025-2026

| Data | Evento |
|------|--------|
| Ago 2025 | Push protection per pattern personalizzati raggiunge GA |
| Nov 2025 | Rilevamento stringhe base64 ad alta entropia |
| Gen 2026 | Secret scanning delegated bypass GA |
| Apr 2026 | Nuovi provider: Figma, GCP Service Account, Langchain, PostHog |
| Q2 2026 | Scansione proattiva di secret in wiki e GitHub Pages |

### Pattern personalizzati con push protection

Le organizzazioni possono definire pattern regex personalizzati per identificare
secret interni (token proprietari, chiavi di servizi interni) e abilitare
push protection su ciascun pattern individualmente:

```
Tipo: Custom pattern
Nome: Internal API Token
Pattern: MYORG_[A-Za-z0-9]{32,64}
Push protection: Enabled
Publish: Organization-wide
```

Ogni pattern personalizzato supporta:
- **Regex primario**: il pattern principale da cercare
- **Before-secret**: contesto opzionale che precede il secret (riduce falsi positivi)
- **After-secret**: contesto opzionale che segue il secret
- **Test strings**: stringhe di esempio per validare il pattern prima dell'attivazione

### Delegated bypass

Il **delegated bypass** permette di designare un team di reviewers che deve
approvare ogni richiesta di bypass della push protection. Quando uno sviluppatore
tenta di pushare un secret e sceglie "bypass", la richiesta viene instradata al
team designato anziché essere approvata automaticamente:

```
Organizzazione → Settings → Code security → Push protection
→ "Who can bypass push protection" → Designated reviewers
→ Selezionare team: @myorg/security-team
```

Questo crea un audit trail completo e garantisce che nessun secret venga
esposto senza revisione esplicita da parte del team di sicurezza.

### Gestione via API

```bash
# Elencare tutti gli alert di secret scanning
gh api repos/{owner}/{repo}/secret-scanning/alerts \
  --jq '.[] | {number, state, secret_type, push_protection_bypassed}'

# Risolvere un alert
gh api -X PATCH repos/{owner}/{repo}/secret-scanning/alerts/42 \
  -f state=resolved -f resolution=revoked

# Elencare pattern personalizzati dell'organizzazione
gh api orgs/{org}/code-security/configurations \
  --jq '.[] | select(.secret_scanning_push_protection == "enabled")'
```

### Rilevamento base64 e alta entropia

A partire da novembre 2025, il secret scanning include un modello di rilevamento
per stringhe base64 ad alta entropia che non corrispondono a pattern noti di
provider specifici. Questo cattura credenziali custom, token JWT non standard e
chiavi codificate manualmente. Il modello usa una pipeline a due fasi:
un primo classificatore veloce filtra i candidati per entropia, e un secondo
modello più accurato verifica la probabilità che la stringa sia effettivamente
un secret. Questo approccio bilancia recall e precisione, mantenendo il tasso
di falsi positivi sotto il 5%.

---

## Code scanning AI-powered — modello ibrido

Nel Q2 2026, GitHub ha introdotto in public beta un modello ibrido di code scanning
che combina l'analisi statica tradizionale di CodeQL con modelli di linguaggio
addestrati per identificare pattern di vulnerabilità. Questo approccio estende
la copertura dell'analisi a categorie di bug che l'analisi statica classica
fatica a rilevare.

### Architettura del modello ibrido

Il sistema opera in due fasi complementari:

1. **Fase CodeQL classica**: le query QL standard analizzano il codice con
   data flow analysis, taint tracking e control flow analysis. Questa fase
   produce risultati ad alta precisione con bassi falsi positivi.

2. **Fase AI**: un modello di linguaggio analizza il codice sorgente e i
   risultati intermedi di CodeQL per identificare pattern sospetti che
   sfuggono all'analisi statica tradizionale. Il modello è stato addestrato
   su milioni di vulnerabilità confermate e fix associati estratti dall'ecosistema
   open source.

### Categorie di vulnerabilità migliorate

Il modello ibrido migliora significativamente la rilevazione di:

- **Errori logici di business**: condizioni di autorizzazione incomplete,
  race condition in operazioni finanziarie, bypass di validazione multi-step
- **Vulnerabilità context-dependent**: injection che richiedono comprensione
  del contesto applicativo (es. template injection in framework specifici)
- **Misconfiguration di sicurezza**: header mancanti, configurazioni TLS
  deboli, permessi eccessivi in file di configurazione
- **Vulnerabilità in codice generato da AI**: pattern insicuri introdotti
  da coding assistant che passano la review manuale

### Configurazione

```yaml
- uses: github/codeql-action/init@v4
  with:
    languages: javascript-typescript
    # Il modello AI si attiva automaticamente per i repository
    # che hanno GHAS abilitato e partecipano alla beta.
    # Non richiede configurazione aggiuntiva nel workflow.
```

L'opt-in alla beta avviene a livello di organizzazione:

```
Organizzazione → Settings → Code security → Code scanning
→ "AI-powered code scanning (beta)" → Enable
```

### Interazione con Copilot Autofix

Gli alert generati dal modello AI sono compatibili con Copilot Autofix.
Quando il modello ibrido identifica una vulnerabilità, Copilot Autofix
può generare una proposta di fix che tiene conto sia dell'analisi statica
tradizionale che del contesto semantico identificato dal modello AI.
Questo produce fix di qualità superiore rispetto a quelli basati solo
sull'output CodeQL tradizionale, con un tasso di accettazione del fix
stimato al 72% nella beta interna.

### Limitazioni della beta

- Disponibile solo per JavaScript/TypeScript e Python nella fase iniziale
- Latenza aggiuntiva di 30-90 secondi per l'analisi AI rispetto al solo CodeQL
- I risultati AI hanno precision tag `medium` e non sono inclusi nella suite `default`
- Richiede GHAS Code Security tier ($30/committer/mese)
- Non sostituisce CodeQL: lo complementa. Le query QL restano la base dell'analisi

---

## Model packs — creazione e distribuzione

I **model packs** sono pacchetti CodeQL che contengono esclusivamente data extensions
(file YAML di modellazione) senza query QL. Permettono di distribuire modelli di
sicurezza per framework e librerie personalizzate attraverso il GitHub Container
Registry (GHCR), consentendo a team diversi di condividere la conoscenza su API
sicure e insicure senza duplicare codice.

### Struttura di un model pack

```
my-org-models/
├── qlpack.yml
├── models/
│   ├── internal-auth-lib.yml
│   ├── custom-orm.yml
│   └── payment-gateway.yml
└── .codeqlmanifest.json
```

Il file `qlpack.yml` dichiara il pack come model pack:

```yaml
name: my-org/security-models
version: 1.2.0
library: true
extensionTargets:
  codeql/java-all: ">=1.0.0"
dataExtensions:
  - models/**/*.yml
```

La chiave `extensionTargets` specifica quali pack di libreria standard vengono
estesi. La chiave `dataExtensions` indica dove trovare i file YAML con le
definizioni di source, sink, summary e barrier.

### Esempio di data extension

```yaml
extensions:
  - addsTo:
      pack: codeql/java-all
      extensible: sinkModel
    data:
      - ["my.org.payment", "PaymentGateway", true,
         "processPayment", "(String,BigDecimal)", "",
         "Argument[0]", "sql-injection", "manual"]
      - ["my.org.payment", "PaymentGateway", true,
         "setCallback", "(String)", "",
         "Argument[0]", "url-redirection", "manual"]

  - addsTo:
      pack: codeql/java-all
      extensible: summaryModel
    data:
      - ["my.org.auth", "TokenValidator", true,
         "sanitize", "(String)", "",
         "Argument[0]", "ReturnValue", "taint", "manual"]
```

### Pubblicazione su GHCR

```bash
# Login al registry
codeql pack download --registries-auth-stdin <<< "$GITHUB_TOKEN"

# Creare il pack
codeql pack create ./my-org-models

# Pubblicare
codeql pack publish ./my-org-models \
  --groups=my-org-internal

# Versionamento semantico: patch per nuovi modelli,
# minor per nuove librerie modellate,
# major per breaking changes nei modelli esistenti
```

### Consumo nei workflow

```yaml
- uses: github/codeql-action/init@v4
  with:
    languages: java-kotlin
    packs: |
      my-org/security-models@~1.2.0
      my-org/framework-models@^2.0.0
    registries: |
      - url: https://ghcr.io/v2/
        packages:
          - my-org/*
        token: ${{ secrets.CODEQL_PACK_TOKEN }}
```

### Vantaggi operativi

- **Separazione delle responsabilità**: il team di sicurezza mantiene i modelli,
  i team di sviluppo li consumano senza modificare i workflow.
- **Versionamento**: i model pack seguono semver, permettendo pin di versione
  e aggiornamenti controllati.
- **Riutilizzo cross-repository**: un singolo model pack può essere usato da
  centinaia di repository nella stessa organizzazione.
- **Testing**: i modelli possono essere testati con `codeql test run` usando
  test case dedicati che verificano che source, sink e summary siano
  correttamente definiti.
- **Composizione**: più model pack possono essere combinati nella stessa
  analisi, ciascuno focalizzato su un dominio applicativo diverso
  (autenticazione, pagamenti, logging, ecc.).

---

## Esercizi

### Lab 1 — CodeQL setup base

1. Abilita CodeQL per un repository con codice JavaScript o Python.
2. Usa il default setup (UI) o crea un workflow manuale.
3. Genera almeno un alert (es. inserisci intenzionalmente una SQL injection in codice di test).
4. Analizza l'alert nella Security tab: severity, CWE, data flow path.

### Lab 2 — Custom CodeQL query

1. Scrivi una query QL che trova `console.log` in codice non-test.
2. Testala localmente con `codeql query run`.
3. Integrala nel workflow GitHub Actions.
4. Verifica che gli alert appaiano nella Security tab.

### Lab 3 — Secret scanning e push protection

1. Abilita secret scanning e push protection per il repository.
2. Genera un token di test (es. `MYTEST_abcdef1234567890abcdef1234567890`).
3. Prova a committare un file con il token → verifica che il push sia bloccato.
4. Configura un custom pattern per token interni.
5. Esegui un dry run del pattern.

### Lab 4 — Dependabot configurazione completa

1. Crea un `dependabot.yml` per npm + GitHub Actions + Docker.
2. Configura grouping per dev dependencies.
3. Configura auto-merge per patch updates.
4. Verifica che le PR vengano create correttamente.

### Lab 5 — Security gate pipeline

1. Crea un workflow "security gate" che blocca le PR se ci sono alert critici.
2. Controlla code scanning, Dependabot e secret scanning alerts.
3. Testa con un alert critico aperto → la PR deve essere bloccata.
4. Risolvi l'alert → la PR deve passare.

### Lab 6 — SARIF da tool esterno

1. Configura ESLint con output SARIF.
2. Carica il SARIF con `codeql-action/upload-sarif`.
3. Verifica che gli alert ESLint appaiano nella Security tab.
4. Confronta con gli alert CodeQL nativi.

### Lab 7 — Models-as-data: barrier personalizzati

1. Crea un progetto JavaScript con una funzione `sanitizeInput()` che sanifica l'input.
2. Scrivi codice che usa `sanitizeInput()` prima di una query SQL.
3. Verifica che CodeQL segnali un alert SQL injection (senza il modello).
4. Crea un file `.github/codeql/extensions/barriers.yml` con un `barrierModel` per `sanitizeInput()`.
5. Riesegui l'analisi e verifica che l'alert sia stato soppresso.

### Lab 8 — MRVA: ricerca variant su larga scala

1. Installa l'extension CodeQL per VS Code.
2. Scrivi una query QL che trova `eval()` con input non fidato in JavaScript.
3. Configura una lista di 10 repository open source JavaScript.
4. Esegui la variant analysis e analizza i risultati.
5. Documenta quanti repository sono affetti e il tipo di vulnerabilità.

### Lab 9 — Dependency Review Action con compliance licenze

1. Configura la Dependency Review Action in un progetto npm.
2. Definisci una whitelist di licenze approvate (MIT, Apache-2.0, BSD).
3. Aggiungi una dipendenza con licenza GPL-3.0 e verifica che la PR venga bloccata.
4. Aggiungi una dipendenza con vulnerabilità critica e verifica il blocco.
5. Configura `comment-summary-in-pr: always` per avere un report nella PR.

### Lab 10 — Threat model locale

1. Configura CodeQL con threat model `remote` + `local` in `codeql-config.yml`.
2. Crea codice Python che legge una variabile d'ambiente e la usa in un `os.system()`.
3. Verifica che con solo `remote` l'alert NON appare.
4. Verifica che con `remote` + `local` l'alert appare.
5. Confronta il numero di alert tra le due configurazioni.

### Lab 11 — Auto-triage rules per Dependabot

1. Abilita Dependabot alerts per un progetto con dipendenze note vulnerabili.
2. Crea una regola auto-triage che dismissi gli alert di severity `low` su dipendenze `development`.
3. Crea una seconda regola che mantenga aperti tutti gli alert con exploit noti.
4. Verifica che le regole vengano applicate correttamente.
5. Monitora il rapporto segnale/rumore degli alert.

### Lab 12 — Convertitore SARIF custom

1. Crea uno script che converte l'output di un tool di analisi (es. output JSON generico) in formato SARIF 2.1.0.
2. Includi fingerprint, taxonomie CWE e invocations nello SARIF.
3. Carica il SARIF con `codeql-action/upload-sarif`.
4. Verifica che gli alert appaiano nella Security tab con le informazioni corrette.
5. Verifica che gli alert persistano tra esecuzioni grazie ai fingerprint.

### Stretch — QL pack personalizzato

1. Crea un QL pack con almeno 3 query custom.
2. Crea un query suite che le include.
3. Pubblica il pack su GHCR.
4. Usalo in un workflow in un altro repository.

---

## Troubleshooting — 20 problemi comuni

### 1. `Error: CodeQL analysis failed: no supported languages found`

**Causa:** il linguaggio non è supportato o il source code non è nella directory attesa.

**Soluzione:** verificare che il linguaggio sia nella lista supportata e che `actions/checkout` sia eseguito prima di `codeql-action/init`.

### 2. CodeQL impiega troppo tempo (> 2 ore)

**Causa:** codebase molto grande, troppe query, o build lenta per linguaggi compilati.

**Soluzione:**
```yaml
# Limitare le query
- uses: github/codeql-action/init@v3
  with:
    queries: security-extended  # non security-and-quality

# Escludere test e generated code
# In codeql-config.yml:
paths-ignore:
  - "**/test/**"
  - "**/generated/**"
  - "**/node_modules/**"

# Aumentare il timeout
timeout-minutes: 360

# Usare TRAP caching
- uses: github/codeql-action/init@v3
  with:
    trap-caching: true
```

### 3. `Error: Unable to resolve queries`

**Causa:** il QL pack o la query suite specificati non esistono o hanno un errore di path.

**Soluzione:**
```yaml
# Verificare il nome esatto della suite
queries: security-extended  # corretto
# Non: queries: codeql/security-extended  # sbagliato
```

### 4. Alert non appaiono nella Security tab

**Causa:** manca `permissions: security-events: write` o il SARIF upload fallisce silenziosamente.

**Soluzione:**
```yaml
permissions:
  security-events: write  # OBBLIGATORIO
  contents: read
  actions: read
```

### 5. Secret scanning non rileva un secret noto

**Causa:** il tipo di secret non è nel database di pattern, o il secret è troppo corto/generico.

**Soluzione:** creare un custom pattern per il tipo di secret specifico.

### 6. Push protection bloccato ma il secret è un falso positivo

**Causa:** il pattern matcha ma il valore non è un secret reale.

**Soluzione:** 
1. Bypassare con ragione "false positive" nella UI.
2. Se ricorrente, contattare il supporto per affinare il pattern.
3. Per pattern custom: aggiustare la regex.

### 7. Dependabot non crea PR

**Causa:** `dependabot.yml` ha errori di sintassi, o il path del `directory` è sbagliato, o il limite di PR aperte è raggiunto.

**Soluzione:**
```bash
# Verificare la sintassi
# Settings → Code security → Dependabot → View logs

# Verificare il directory
# Deve puntare alla directory che contiene il lockfile
directory: "/"  # dove sta package.json
```

### 8. `Error: codeql-action/init must be run before codeql-action/analyze`

**Causa:** i due step sono in job separati, o l'ordine è sbagliato.

**Soluzione:** `init` e `analyze` devono essere nello stesso job, nell'ordine corretto.

### 9. CodeQL non analizza file TypeScript

**Causa:** i file TypeScript sono analizzati sotto `javascript-typescript`, non come linguaggio separato.

**Soluzione:**
```yaml
- uses: github/codeql-action/init@v3
  with:
    languages: javascript-typescript  # include TS
```

### 10. Custom query produce troppi falsi positivi

**Causa:** la query è troppo generica, manca precision nel pattern matching.

**Soluzione:**
1. Aggiungere condizioni più restrittive nella clausola `where`.
2. Escludere file di test e codice generato.
3. Usare `@precision low` per non intasare gli alert.

### 11. `Error: SARIF upload failed: 413 Payload Too Large`

**Causa:** il file SARIF supera il limite di 10 MB.

**Soluzione:**
```bash
# Filtrare solo alert con severity alta
# O suddividere l'analisi per linguaggio/directory
```

### 12. Code scanning autofix non disponibile

**Causa:** autofix richiede GHAS + Copilot. Non disponibile per tutti i linguaggi.

**Soluzione:** verificare che GHAS e Copilot siano abilitati. Verificare il linguaggio supportato.

### 13. Secret scanning alert per un secret già ruotato

**Causa:** il secret è ancora nel git history, anche se rimosso dal branch corrente.

**Soluzione:**
1. Risolvere l'alert come "revoked".
2. Se il secret è nel history: considerare `git filter-repo` per rimuoverlo.
3. Il secret è già stato ruotato, quindi non è più utilizzabile.

### 14. Dependabot security update crea conflitto

**Causa:** l'aggiornamento di sicurezza confligge con altri cambiamenti nel lockfile.

**Soluzione:**
```bash
# Rebase manuale della PR Dependabot
# Nella PR Dependabot, commentare:
@dependabot rebase
```

### 15. CodeQL non trova vulnerabilità ovvie

**Causa:** la query default potrebbe non coprire quel pattern specifico, o il data flow è troppo complesso.

**Soluzione:**
1. Provare `security-and-quality` invece di `default`.
2. Verificare se esiste una query specifica per quel CWE.
3. Scrivere una custom query.

### 16. `Error: Resource not accessible by integration`

**Causa:** il GITHUB_TOKEN non ha i permessi necessari.

**Soluzione:**
```yaml
permissions:
  security-events: write
  contents: read
  actions: read
```

### 17. Dependabot PR ha check falliti

**Causa:** Dependabot non ha accesso ai secret del repository (per sicurezza).

**Soluzione:** usare `pull_request_target` per i workflow che richiedono secret, oppure configurare Dependabot secrets separati.

### 18. Security overview vuota per l'organizzazione

**Causa:** GHAS non è abilitato per nessun repository, o l'utente non ha permessi org admin.

**Soluzione:** abilitare GHAS per almeno un repository e verificare i permessi.

### 19. `Error: autobuild failed`

**Causa:** per linguaggi compilati (Java, C#, C++), autobuild non riesce a compilare il progetto.

**Soluzione:**
```yaml
# Usare build-mode: manual e specificare il comando di build
- uses: github/codeql-action/init@v3
  with:
    languages: java-kotlin
    build-mode: manual

- name: Build
  run: mvn clean compile -DskipTests
```

### 20. CodeQL query non si compila

**Causa:** errore di sintassi QL, import mancante, o versione di QL pack incompatibile.

**Soluzione:**
```bash
# Verificare la compilazione
codeql query compile my-queries/queries/MyQuery.ql

# Verificare le dipendenze
codeql pack resolve-dependencies my-queries/
```

---

## FAQ — 20 domande e risposte

### 1. CodeQL è gratuito?

Per repository pubblici: sì, completamente gratuito. Per repository privati: richiede una licenza GitHub Advanced Security (GHAS), che è un add-on per GitHub Enterprise.

### 2. CodeQL sostituisce ESLint / SonarQube?

No. CodeQL si focalizza su vulnerabilità di sicurezza con analisi inter-procedurale (data flow, taint tracking). ESLint e SonarQube coprono code quality e stile. Sono complementari.

### 3. Quante vulnerabilità copre CodeQL di default?

Le query default coprono OWASP Top 10 e CWE Top 25. Le suite `security-extended` aggiungono centinaia di query addizionali. La lista completa è su [codeql.github.com/codeql-query-help](https://codeql.github.com/codeql-query-help/).

### 4. Posso usare CodeQL localmente?

Sì. Installare la CodeQL CLI e VS Code extension. Creare un database locale e eseguire query. L'uso locale è gratuito per ricerca e sviluppo query.

### 5. Le custom queries rallentano il workflow?

Ogni query aggiunge tempo. Query semplici (problem) aggiungono secondi. Query complesse (path-problem con taint tracking) possono aggiungere minuti. Misurare con la diagnostica integrata.

### 6. Secret scanning funziona con repository privati?

Sì, con GHAS abilitato. Per repository pubblici è gratuito.

### 7. Push protection blocca anche i commit in PR da fork?

Sì, se push protection è abilitato. I contributor a fork ricevono lo stesso blocco.

### 8. Posso disabilitare alert specifici?

Sì:
```text
Security tab → Alert → Dismiss → Ragione
  - False positive
  - Won't fix
  - Used in tests
```

### 9. Come gestisco i falsi positivi ricorrenti?

1. Dismiss con ragione appropriata.
2. Per CodeQL: aggiungere il query ID al `query-filters` di esclusione.
3. Per secret scanning: segnalare come false positive.
4. Per Dependabot: usare `ignore` nel `dependabot.yml`.

### 10. CodeQL può analizzare codice di terze parti (vendor, node_modules)?

Per default li esclude. Se vuoi includerli, rimuovili da `paths-ignore`. Ma attenzione: aumenta drasticamente il tempo di analisi e il numero di alert.

### 11. Quanto spazio occupa un database CodeQL?

Dipende dalla dimensione del codebase. Tipicamente 100 MB – 2 GB. Per codebase molto grandi (>1M LoC), può superare i 5 GB.

### 12. Posso usare CodeQL in self-hosted runners?

Sì. Il runner deve avere le risorse necessarie (RAM 8 GB+ consigliata). Installare la CodeQL CLI o usare `codeql-action` che la scarica automaticamente.

### 13. SARIF è supportato da altri tool oltre GitHub?

Sì. SARIF è uno standard aperto supportato da Azure DevOps, VS Code, Semgrep, SonarQube, e molti altri. Qualsiasi tool che produce SARIF può essere integrato nella Security tab di GitHub.

### 14. Dependabot funziona con monorepo?

Sì. Specificare più entries in `dependabot.yml` con `directory` diversi:
```yaml
updates:
  - package-ecosystem: npm
    directory: "/packages/frontend"
  - package-ecosystem: npm
    directory: "/packages/backend"
```

### 15. Come migro da SonarQube a CodeQL?

1. Mantenere SonarQube per code quality.
2. Abilitare CodeQL per security scanning.
3. Confrontare i risultati per 1-2 mesi.
4. Valutare se CodeQL copre sufficientemente le regole SonarQube di sicurezza.
5. Eventualmente ridurre il scope di SonarQube a solo quality.

### 16. Code scanning autofix può introdurre bug?

I fix sono suggerimenti. Devono essere revisionati da un developer. Autofix non fa commit automatici — richiede sempre approvazione umana.

### 17. Posso forzare code scanning come required check?

Sì:
```text
Repository Settings → Branches → Branch protection rules
→ Require status checks → Selezionare "CodeQL"
```

### 18. Secret scanning rileva secret in file binari?

No. Secret scanning analizza solo file di testo. Secret in binari, immagini, o file compressi non vengono rilevati.

### 19. Qual è il MTTR medio per alert CodeQL?

Dipende dall'organizzazione. Il benchmark è: Critical < 7 giorni, High < 30 giorni, Medium < 90 giorni. Monitorare via Security Overview.

### 20. GHAS include penetration testing?

No. GHAS è SAST (Static Application Security Testing) + SCA (Software Composition Analysis) + secret detection. Il penetration testing è DAST (Dynamic) e richiede tool separati (OWASP ZAP, Burp Suite, ecc.).

---

## Letture consigliate

- CodeQL documentation — [codeql.github.com/docs](https://codeql.github.com/docs/)
- CodeQL query help — [codeql.github.com/codeql-query-help](https://codeql.github.com/codeql-query-help/)
- GitHub Advanced Security — [docs.github.com/en/get-started/learning-about-github/about-github-advanced-security](https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security)
- Secret scanning docs — [docs.github.com/en/code-security/secret-scanning](https://docs.github.com/en/code-security/secret-scanning)
- Dependabot docs — [docs.github.com/en/code-security/dependabot](https://docs.github.com/en/code-security/dependabot)
- SARIF specification — [docs.oasis-open.org/sarif/sarif/v2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0)
- QL language reference — [codeql.github.com/docs/ql-language-reference](https://codeql.github.com/docs/ql-language-reference/)
- CodeQL for VS Code — [codeql.github.com/docs/codeql-for-visual-studio-code](https://codeql.github.com/docs/codeql-for-visual-studio-code/)
- OWASP Top 10 — [owasp.org/www-project-top-ten](https://owasp.org/www-project-top-ten/)
- CWE Top 25 — [cwe.mitre.org/top25](https://cwe.mitre.org/top25/)
- Code scanning autofix — [docs.github.com/en/code-security/code-scanning/managing-code-scanning-alerts/about-autofix-for-codeql-code-scanning](https://docs.github.com/en/code-security/code-scanning/managing-code-scanning-alerts/about-autofix-for-codeql-code-scanning)
- GHAS licensing — [docs.github.com/en/billing/managing-billing-for-github-advanced-security](https://docs.github.com/en/billing/managing-billing-for-github-advanced-security)
- Models-as-data documentation — [codeql.github.com/docs/codeql-language-guides/customizing-library-models-for-java-and-kotlin](https://codeql.github.com/docs/codeql-language-guides/customizing-library-models-for-java-and-kotlin/)
- QL language reference — Recursion — [codeql.github.com/docs/ql-language-reference/recursion](https://codeql.github.com/docs/ql-language-reference/recursion/)
- QL language reference — Predicates — [codeql.github.com/docs/ql-language-reference/predicates](https://codeql.github.com/docs/ql-language-reference/predicates/)
- QL language reference — Formulas — [codeql.github.com/docs/ql-language-reference/formulas](https://codeql.github.com/docs/ql-language-reference/formulas/)
- Security campaigns — [docs.github.com/en/code-security/concepts/security-at-scale/about-security-campaigns](https://docs.github.com/en/code-security/concepts/security-at-scale/about-security-campaigns)
- Copilot Autofix for code scanning — [docs.github.com/en/code-security/concepts/code-scanning/copilot-autofix-for-code-scanning](https://docs.github.com/en/code-security/concepts/code-scanning/copilot-autofix-for-code-scanning)
- Dependabot auto-triage rules — [docs.github.com/en/code-security/dependabot/dependabot-auto-triage-rules](https://docs.github.com/en/code-security/dependabot/dependabot-auto-triage-rules)
- Multi-repository variant analysis — [docs.github.com/en/code-security/concepts/code-scanning/multi-repository-variant-analysis](https://docs.github.com/en/code-security/concepts/code-scanning/multi-repository-variant-analysis)
- Dependency Review Action — [docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/configuring-the-dependency-review-action](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/configuring-the-dependency-review-action)
- Generic secret detection AI — [docs.github.com/en/code-security/secret-scanning/copilot-secret-scanning/responsible-ai-generic-secrets](https://docs.github.com/en/code-security/secret-scanning/copilot-secret-scanning/responsible-ai-generic-secrets)
- GHAS unbundling announcement — [resources.github.com/evolving-github-advanced-security](https://resources.github.com/evolving-github-advanced-security/)
- Trail of Bits mrva CLI — [blog.trailofbits.com/2025/12/11/introducing-mrva-a-terminal-first-approach-to-codeql-multi-repo-variant-analysis](https://blog.trailofbits.com/2025/12/11/introducing-mrva-a-terminal-first-approach-to-codeql-multi-repo-variant-analysis/)
- SARIF specification v2.1.0 — [docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
- GitHub Actions 2026 Security Roadmap — [github.blog/news-insights/product-news/whats-coming-to-our-github-actions-2026-security-roadmap](https://github.blog/news-insights/product-news/whats-coming-to-our-github-actions-2026-security-roadmap/)

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [16 — GitHub Security e Scanning](16-github-security-scanning.md) | Fondamenti di security scanning; GHAS estende con CodeQL e secret scanning avanzato |
| [18 — GitHub Actions Avanzate](18-github-actions-avanzate.md) | Workflow riutilizzabili per eseguire CodeQL su più repository |
| [19 — GitHub Actions: Ricette CI/CD](19-github-actions-ci-cd-ricette.md) | Integrazione code scanning come quality gate nella pipeline CI |
| [24 — DevOps Completo con GitHub](24-devops-completo-con-github.md) | Security shift-left: CodeQL e secret scanning nel ciclo DevSecOps |
| [26 — OIDC Cloud Credentials](26-oidc-cloud-credentials.md) | OIDC elimina i secret statici che push protection altrimenti blocca |
| [27 — Supply-Chain Attestation e SLSA](27-supply-chain-attestation-slsa.md) | Dependabot e SCA in GHAS completano la supply-chain attestation |

---

## Glossario

| Termine | Definizione |
|---|---|
| **CodeQL** | Motore di analisi semantica del codice che tratta il source come un database relazionale interrogabile con query dichiarative QL |
| **QL** | Linguaggio di query dichiarativo (derivato da Datalog) usato per interrogare database CodeQL |
| **SAST** | Static Application Security Testing — analisi di sicurezza del codice sorgente senza esecuzione |
| **SCA** | Software Composition Analysis — analisi delle dipendenze per vulnerabilità note e licenze |
| **SARIF** | Static Analysis Results Interchange Format — standard OASIS per i risultati di analisi statica |
| **CWE** | Common Weakness Enumeration — catalogo standardizzato di debolezze software |
| **CVE** | Common Vulnerabilities and Exposures — identificatori univoci per vulnerabilità note |
| **GHSA** | GitHub Security Advisory — advisory di sicurezza nel database GitHub |
| **GHAS** | GitHub Advanced Security — suite di sicurezza enterprise (code scanning, secret scanning, dependency review) |
| **Extractor** | Componente CodeQL che analizza il source code di un linguaggio specifico e popola il database |
| **QL Pack** | Pacchetto distribuibile di query QL con metadata, dipendenze e query suites |
| **Query Suite** | File `.qls` che seleziona un sottoinsieme di query da eseguire |
| **Taint tracking** | Tecnica di analisi che segue la propagazione di dati "contaminati" (input utente) dalla source alla sink |
| **Data flow analysis** | Analisi del flusso dei dati attraverso il programma, incluso tra funzioni e file |
| **Source** | Punto dove entrano dati non fidati (es. `request.getParameter()`) |
| **Sink** | Punto dove i dati raggiungono un'operazione pericolosa (es. `db.query()`) |
| **Secret scanning** | Funzionalità GitHub che rileva automaticamente secret committati nel repository |
| **Push protection** | Meccanismo che blocca il `git push` prima che un secret raggiunga il repository |
| **Custom pattern** | Pattern regex definito dall'utente per secret scanning, per rilevare secret specifici dell'organizzazione |
| **Dependabot** | Servizio GitHub che monitora le dipendenze e crea PR automatiche per aggiornamenti e fix di sicurezza |
| **Code scanning autofix** | Funzionalità AI (Copilot-powered) che suggerisce fix automatici per alert CodeQL |
| **Security Overview** | Dashboard a livello organizzazione che mostra lo stato di sicurezza aggregato di tutti i repository |
| **Advisory Database** | Database curato da GitHub con informazioni su vulnerabilità note nelle dipendenze open source |
| **Dependency graph** | Grafo delle dipendenze di un repository, generato automaticamente da GitHub |
| **OWASP Top 10** | Lista delle 10 vulnerabilità web più critiche, aggiornata periodicamente da OWASP |
| **Active committer** | Utente che ha fatto commit negli ultimi 90 giorni a un repository con GHAS abilitato — unità di billing |
| **MRVA** | Multi-Repository Variant Analysis — tecnica per eseguire una query CodeQL su centinaia di repository simultaneamente alla ricerca di pattern vulnerabili |
| **Models-as-data** | Approccio dichiarativo (YAML) per definire source, sink, sanitizer e barrier senza scrivere query QL custom |
| **Data extension** | File YAML che estende i modelli di sicurezza CodeQL con definizioni custom di source, sink, summary e barrier |
| **Barrier** | Funzione o metodo il cui output è considerato sanitizzato per un tipo specifico di vulnerabilità, interrompendo il flusso di taint |
| **Barrier guard** | Funzione che restituisce un valore booleano indicante se i dati sono sicuri, bloccando il flusso di taint nel branch protetto |
| **Threat model** | Configurazione che definisce quali fonti di input sono considerate potenzialmente pericolose (remote, local, environment) |
| **Validity check** | Verifica automatica che determina se un secret rilevato da secret scanning è ancora attivo presso il provider |
| **Security campaign** | Funzionalità GA di GitHub Code Security che raggruppa alert e coordina la remediation su larga scala con Copilot Autofix |
| **Auto-triage rule** | Regola automatica che gestisce gli alert Dependabot (dismiss/reopen) in base a condizioni configurabili |
| **Generic secret** | Secret non legato a un provider specifico (es. password generiche, chiavi private RSA) rilevato tramite AI |
| **GitHub Secret Protection** | Prodotto standalone ($19/committer/mese) che include secret scanning, push protection e rilevamento AI |
| **GitHub Code Security** | Prodotto standalone ($30/committer/mese) che include code scanning CodeQL, Copilot Autofix e security campaigns |
| **Chiusura transitiva** | Operatore QL (`+` o `*`) che applica ricorsivamente un predicato per seguire catene di relazioni |
| **Aggregato** | Operazione QL (`count`, `sum`, `avg`, `min`, `max`, `rank`) che calcola un valore da un insieme di tuple |
| **Quantificatore** | Formula QL (`exists`, `forall`, `forex`) che introduce variabili temporanee e le testa contro condizioni logiche |
| **TRAP file** | Tuples Representing Abstract Properties — formato intermedio usato dagli extractor CodeQL per rappresentare fatti sul codice |
| **Fingerprint SARIF** | Identificatore stabile di un risultato di analisi statica, usato per tracciare alert tra esecuzioni successive |
| **Taxonomia SARIF** | Classificazione strutturata dei risultati secondo sistemi standard (CWE, OWASP) nel formato SARIF |
| **EPSS** | Exploit Prediction Scoring System — punteggio che stima la probabilità che una vulnerabilità venga sfruttata entro 30 giorni |
