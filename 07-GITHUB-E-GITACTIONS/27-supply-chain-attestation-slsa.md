---
corso: "GitHub e Git Actions"
fase: "5 — Sicurezza"
modulo: 27
titolo: "Supply-Chain Attestation e SLSA in GitHub Actions"
versione: "SLSA v1.0 / Sigstore GA / in-toto v1"
livello: "Avanzato"
prerequisiti:
  - "19-github-actions-ci-cd-ricette"
  - "16-github-security-scanning"
  - "14-github-packages-pages-releases"
obiettivi:
  - "Descrivere i livelli SLSA e i requisiti di build provenance"
  - "Generare attestazioni in formato in-toto con il SLSA GitHub generator"
  - "Firmare e verificare artefatti con Sigstore (cosign, Rekor, Fulcio)"
  - "Produrre e consumare SBOM in formato SPDX e CycloneDX"
  - "Integrare Dependabot, dependency-review e OpenSSF Scorecard nella CI"
tag: [slsa, supply-chain, attestation, sigstore, cosign, sbom, dependabot, provenance, in-toto]
---

# Supply-Chain Attestation e SLSA in GitHub Actions

> **Modulo 27** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Descrivere i livelli SLSA e i requisiti di build provenance
> 2. Generare attestazioni in formato in-toto con il SLSA GitHub generator
> 3. Firmare e verificare artefatti con Sigstore (cosign, Rekor, Fulcio)
> 4. Produrre e consumare SBOM in formato SPDX e CycloneDX
> 5. Integrare Dependabot, dependency-review e OpenSSF Scorecard nella CI

---

## Indice

1. [Idee guida](#idee-guida)
2. [Il problema della supply chain](#il-problema-della-supply-chain)
3. [SLSA framework — livelli e requisiti](#slsa-framework--livelli-e-requisiti)
4. [Build provenance](#build-provenance)
5. [Formato attestazione — in-toto](#formato-attestazione--in-toto)
6. [SLSA GitHub generator](#slsa-github-generator)
7. [Sigstore — cosign, Rekor, Fulcio](#sigstore--cosign-rekor-fulcio)
8. [Software Bill of Materials (SBOM)](#software-bill-of-materials-sbom)
9. [VEX — Vulnerability Exploitability eXchange](#vex--vulnerability-exploitability-exchange)
10. [Dependabot — alerts, updates, security updates](#dependabot--alerts-updates-security-updates)
11. [Dependency review action](#dependency-review-action)
12. [npm provenance e Trusted Publishing](#npm-provenance-e-trusted-publishing)
13. [Container signing e attestation](#container-signing-e-attestation)
14. [GitHub Artifact Attestations](#github-artifact-attestations)
15. [OpenSSF Scorecard](#openssf-scorecard)
16. [Hardening dei workflow GitHub Actions](#hardening-dei-workflow-github-actions)
17. [Regolamentazione e compliance](#regolamentazione-e-compliance)
18. [Architettura di verifica end-to-end](#architettura-di-verifica-end-to-end)
19. [Verification workflows](#verification-workflows)
20. [Pattern avanzati](#pattern-avanzati)
21. [Esercizi](#esercizi)
22. [Troubleshooting — 20 problemi comuni](#troubleshooting--20-problemi-comuni)
23. [FAQ — 20 domande e risposte](#faq--20-domande-e-risposte)
24. [Letture consigliate](#letture-consigliate)
25. [Glossario](#glossario)

---

## Idee guida

1. **`actions/attest-build-provenance@v1` genera SLSA L2 provenance** — prova crittografica dell'origine dell'artefatto.
2. **cosign sign auto via OIDC keyless** — firma senza gestire chiavi private.
3. **Dependency review action: PR diff per security regression** — blocca PR che introducono vulnerabilità note.
4. **GitHub Artifact Attestations GA dal 2024** — integrazione nativa nell'ecosistema.
5. **La supply chain è sicura quanto il suo anello più debole** — ogni fase (source → build → distribute → consume) va protetta.

---

## Il problema della supply chain

### Attacchi reali alla supply chain

| Anno | Attacco | Impatto |
|---|---|---|
| 2020 | SolarWinds | Build system compromesso, malware inserito in update firmati |
| 2021 | Codecov | Script di upload bash compromesso, exfiltration di CI secrets |
| 2021 | ua-parser-js | npm package hijacked, crypto-miner distribuito |
| 2022 | node-ipc | Maintainer inserisce codice distruttivo intenzionalmente |
| 2023 | 3CX | Dipendenza compromessa → supply chain attack a catena |
| 2024 | xz-utils (CVE-2024-3094) | Backdoor inserita in libreria di compressione via social engineering |
| 2024 | Ultralytics | Template injection in GitHub Actions → build pipeline compromesso, versioni malevole pubblicate |
| 2025 | TinyColor (npm) | Script maligni iniettati in pacchetto popolare, worm auto-propagante che raccoglieva token e credenziali cloud |
| 2025 | tj-actions/changed-files | GitHub Action compromessa (CVE-2025-30066), exfiltration di CI/CD secrets da 23.000+ repository |
| 2026 | Axios (npm) | Token npm di un maintainer rubato, RAT cross-platform in due versioni avvelenate |
| 2026 | Trivy (Aqua Security) | Attacco multi-fase allo scanner di vulnerabilità, backdoor persistente + worm npm auto-propagante |

#### Escalation quantitativa degli attacchi

I numeri mostrano un'escalation drammatica nella frequenza degli attacchi alla supply chain open source. Secondo i dati aggregati da Sonatype, Snyk e Socket.dev, il volume di pacchetti maligni noti è cresciuto di oltre tre ordini di grandezza in cinque anni:

| Anno | Pacchetti maligni rilevati | Crescita anno su anno |
|---|---|---|
| 2020 | ~929 | Baseline |
| 2021 | ~6.500 | +600% |
| 2022 | ~18.000 | +177% |
| 2023 | ~98.000 | +444% |
| 2024 | ~459.000 | +368% |
| 2025 | ~454.600 (solo nuovi) | Totale cumulativo: 1.233.000+ |

Questa tendenza evidenzia un cambio di paradigma: gli attaccanti hanno scoperto che compromettere una singola dipendenza upstream è molto più efficiente che attaccare singoli target downstream. Un pacchetto npm maligno con 1.000 download settimanali può colpire centinaia di organizzazioni con un solo publish. L'attacco ad Axios nel marzo 2026 lo ha dimostrato concretamente: due versioni avvelenate, pubblicate sfruttando un token npm rubato, hanno installato un RAT (Remote Access Trojan) cross-platform che stabiliva comunicazioni con un server C2 entro due secondi dall'esecuzione di `npm install`.

L'attacco a Trivy nello stesso mese è stato ancora più sofisticato. Aqua Security, il vendor dietro Trivy — uno degli scanner di vulnerabilità open source più utilizzati al mondo — ha subito un attacco in più fasi: compromissione del build pipeline, iniezione di backdoor persistenti nelle macchine degli sviluppatori, e propagazione worm-like attraverso decine di pacchetti npm collegati. L'ironia di uno scanner di sicurezza trasformato in vettore di attacco ha sottolineato un principio fondamentale: nessun componente della supply chain è immune per definizione.

### La superficie di attacco

```text
                    Superficie di attacco
                    =====================

  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │  Source   │ ──► │  Build   │ ──► │ Publish  │ ──► │ Consume  │
  │          │     │          │     │          │     │          │
  │ • Commit │     │ • CI env │     │ • Registry│    │ • Install│
  │ • PR     │     │ • Deps   │     │ • CDN    │     │ • Import │
  │ • Branch │     │ • Scripts│     │ • Mirror │     │ • Run    │
  └──────────┘     └──────────┘     └──────────┘     └──────────┘
       ▲                ▲                ▲                ▲
  Compromised     Tampered build    Man-in-the-      Dependency
  maintainer      environment       middle            confusion
```

### Evoluzione degli attacchi 2024-2026

Il panorama degli attacchi alla supply chain si è evoluto drasticamente tra il 2024 e il 2026. Secondo il rapporto Sonatype 2026, sono stati identificati oltre 454.600 nuovi pacchetti maligni nel solo 2025, portando il totale cumulativo di malware noto e bloccato a oltre 1.233.000 pacchetti tra npm, PyPI, Maven Central, NuGet e Hugging Face.

#### Slopsquatting — l'attacco AI-driven

Una nuova categoria di attacco emersa nel 2025 è lo **slopsquatting**, termine coniato dal ricercatore Seth Larson. Si tratta di una variante del typosquatting dove gli attaccanti registrano nomi di pacchetti che i modelli AI tendono a "allucinare" — ovvero, suggerire come se esistessero quando in realtà non esistono.

```text
Come funziona lo slopsquatting
==============================

1. Un modello AI genera codice per lo sviluppatore
2. Il codice include un import: "import express-mongoose"
3. Il pacchetto "express-mongoose" NON esiste su npm
4. L'attaccante, prevedendo l'allucinazione, ha già registrato
   "express-mongoose" con codice maligno
5. Lo sviluppatore esegue "npm install express-mongoose"
6. Il malware viene installato nel progetto
```

Uno studio presentato a USENIX Security 2025, analizzando 576.000 campioni di codice generati da 16 modelli AI, ha rivelato dati allarmanti:

| Metrica | Valore |
|---|---|
| Campioni con pacchetti inesistenti | ~20% |
| Nomi allucinati ricorrenti tra run | 58% |
| Nomi ricorrenti in 10 tentativi identici | 43% |
| Tipo: conflazione (es. express-mongoose) | 38% |
| Tipo: variante typo | 13% |
| Tipo: fabbricazione pura | 51% |

**Mitigazioni contro lo slopsquatting:**

1. **Verificare sempre** che un pacchetto esista sul registry ufficiale prima di installarlo.
2. **Non fidarsi ciecamente** del codice generato da AI — trattare ogni suggerimento come non verificato.
3. **Usare lockfile** (`package-lock.json`, `yarn.lock`, `poetry.lock`) e verificare le modifiche.
4. **Dependency review action** rileva pacchetti senza cronologia o reputazione.
5. **Socket.dev** e tool simili analizzano il comportamento runtime dei pacchetti.

#### Compromissione di GitHub Actions: tj-actions/changed-files (2025)

Nel marzo 2025, l'azione `tj-actions/changed-files` è stata compromessa (CVE-2025-30066), colpendo oltre 23.000 repository. L'attaccante ha modificato il codice dell'azione per esfiltrare secrets CI/CD dai runner. Questo attacco ha dimostrato che anche le azioni GitHub usate nei workflow sono un vettore di supply chain critico.

**Lezioni dall'attacco tj-actions:**

```yaml
# VULNERABILE: usa un tag mutabile
- uses: tj-actions/changed-files@v45

# SICURO: pin by SHA — il tag è un commento per leggibilità
- uses: tj-actions/changed-files@d6babd6899969df1a11d14c368ffddc5f81a5f46 # v45.0.1
```

L'unico modo per usare un'azione come release immutabile è il pin tramite SHA completo del commit. Un tag può essere riscritto dall'attaccante, un SHA no (a meno di collisione SHA-1, computazionalmente impraticabile).

#### Typosquatting su larga scala

Nel 2024-2025, PyPI ha rimosso centinaia di typosquat maligni al mese. Esempi documentati:

| Pacchetto legittimo | Typosquat maligno | Tecnica |
|---|---|---|
| `requests` | `requets` | Scambio lettere |
| `colorama` | `colorama-py` | Suffisso plausibile |
| `selenium` | `selemium` | Omissione lettera |
| `beautifulsoup4` | `beautifulsoup` | Versione senza numero |
| `pytorch` | `pytoroch` | Anagramma parziale |

Su npm, oltre il 99% del malware open-source nel 2025 è stato pubblicato proprio su questo registro. I pacchetti maligni tipicamente eseguono script `postinstall` che scaricano ed eseguono payload remoti, esfiltrano variabili d'ambiente (inclusi token CI/CD), o installano crypto-miner.

### Cosa risolve SLSA

SLSA (Supply-chain Levels for Software Artifacts, pronunciato "salsa") definisce un framework graduato di requisiti per proteggere l'integrità della supply chain:

- **Provenance:** chi ha buildato cosa, da quale source, in quale ambiente.
- **Verificabilità:** ogni attestazione è firmata e verificabile crittograficamente.
- **Gradualità:** livelli incrementali (L0 → L3) con requisiti crescenti.

---

## SLSA framework — livelli e requisiti

### Panoramica dei livelli

| Livello | Nome | Requisiti chiave |
|---|---|---|
| **L0** | Nessuna garanzia | Nessuna provenance. Stato di default. |
| **L1** | Provenance exists | La build genera provenance (chi, cosa, quando). Il formato è standardizzato. |
| **L2** | Hosted build | La build avviene su un servizio hosted (es. GitHub Actions). La provenance è firmata dal servizio. |
| **L3** | Hardened build | Isolamento tra build. Provenance non falsificabile dal maintainer. |

### Requisiti dettagliati per livello

#### SLSA L1 — Provenance exists

```text
✅ Build process definito (script, workflow)
✅ Provenance generata automaticamente
✅ Provenance include: builder, source, invocation, materiali
✅ Provenance distribuita con l'artefatto
```

#### SLSA L2 — Hosted build

```text
✅ Tutto di L1, più:
✅ Build su servizio hosted (GitHub Actions, Cloud Build, ecc.)
✅ Provenance firmata dal servizio di build
✅ Provenance autenticata (verificabile la firma)
✅ Il servizio di build ha un'identità verificabile
```

#### SLSA L3 — Hardened build

```text
✅ Tutto di L2, più:
✅ Runner isolati (ephemeral, non condivisi)
✅ Provenance non falsificabile dal developer/maintainer
✅ Il workflow è locked a una specifica ref (no modifica runtime)
✅ Il builder è hardened contro compromissioni
```

### Evoluzione del framework: da v0.1 a v1.1

Il passaggio da SLSA v0.1 a v1.0 ha introdotto cambiamenti concettuali significativi. La modifica più importante è la divisione dei requisiti in **track** separati. Un track SLSA si concentra su un aspetto specifico della supply chain.

```text
SLSA v0.1 (2021-2023)          SLSA v1.0+ (2023-oggi)
=====================          ========================

  Livelli monolitici            Track separati
  L1 → L2 → L3 → L4           ┌─ Build Track (L1-L3)
                                ├─ Source Track (futuro)
  Tutto in un singolo           ├─ Dependencies Track (futuro)
  percorso graduato             └─ Common requirements

  4 livelli                     3 livelli per track
  Requisiti misti               Requisiti specifici per track
```

SLSA v1.0 include solo il **Build Track**, ma le versioni future aggiungeranno track per source code management, gestione delle dipendenze e altri aspetti della supply chain.

**SLSA v1.1** (rilasciato nel 2024, stabile) ha raffinato la specifica con chiarimenti su:

- **Requisiti di isolamento per L3:** definizione più precisa di cosa significa "builder hardened".
- **Provenance completeness:** guida su quali campi della provenance sono obbligatori vs raccomandati.
- **Multi-platform builds:** come gestire la provenance per build che producono artefatti per più architetture.
- **Dependency completeness:** raccomandazioni sulla registrazione delle dipendenze risolte nella provenance.

#### Build Track — requisiti in dettaglio

| Requisito | L1 | L2 | L3 |
|---|---|---|---|
| Build process documentato | Obbligatorio | Obbligatorio | Obbligatorio |
| Provenance generata automaticamente | Obbligatorio | Obbligatorio | Obbligatorio |
| Provenance include parametri esterni | Obbligatorio | Obbligatorio | Obbligatorio |
| Builder hosted (non locale) | — | Obbligatorio | Obbligatorio |
| Provenance firmata dal servizio | — | Obbligatorio | Obbligatorio |
| Identità del builder verificabile | — | Obbligatorio | Obbligatorio |
| Runner ephemeral/isolato | — | — | Obbligatorio |
| Provenance non falsificabile dal maintainer | — | — | Obbligatorio |
| Workflow locked a una ref specifica | — | — | Obbligatorio |
| Parametri controllati dal builder | — | — | Obbligatorio |

#### Source Track — SLSA v1.2 (approvato novembre 2025)

Il Source Track è stato per anni la grande assente della specifica SLSA. Dalla bozza iniziale v0.1 del 2021 — che trattava i requisiti di source e build come un percorso monolitico — il Source Track è passato attraverso molteplici revisioni prima di raggiungere la maturità in SLSA v1.2.

**Cronologia dello sviluppo:**

```text
2021     v0.1 sketch — requisiti source incorporati nei livelli monolitici L1-L4
2023     v1.0 — Source Track rinviato; solo Build Track pubblicato
2024     v1.1 — nessun cambiamento per Source Track, rimane "in sviluppo"
2025 Q1  Source Track Draft v0.1 — prima bozza dedicata, presentata all'OpenSSF Day Europe
2025 Q3  Source Track RC1 — Release Candidate con 4 livelli (L0-L3)
2025 Q4  Source Track RC2 / SLSA v1.2 — approvato dal SLSA Steering Committee (novembre 2025)
```

Il Source Track v1.2 definisce **quattro livelli** per la gestione del codice sorgente:

| Livello | Nome | Requisiti chiave |
|---|---|---|
| **Source L0** | No guarantees | Nessun requisito — baseline implicita |
| **Source L1** | Version controlled | Il codice è in un sistema di version control; le modifiche sono tracciate con autore e timestamp |
| **Source L2** | Verified history | Ogni revisione ha un'identità verificata dell'autore; la piattaforma attesta la storia delle modifiche; le revisioni sono immutabili dopo il merge |
| **Source L3** | Retained and two-party review | Revisione obbligatoria da parte di almeno una persona diversa dall'autore (two-party review); la piattaforma garantisce la conservazione delle revisioni e impedisce la riscrittura della storia; branch protection rules enforced |

**Dettaglio dei requisiti per livello:**

| Requisito | L0 | L1 | L2 | L3 |
|---|---|---|---|---|
| Codice in version control system | — | Obbligatorio | Obbligatorio | Obbligatorio |
| Revisioni tracciate con autore e timestamp | — | Obbligatorio | Obbligatorio | Obbligatorio |
| Identità dell'autore verificata dalla piattaforma | — | — | Obbligatorio | Obbligatorio |
| Revisioni immutabili (no force-push post-merge) | — | — | Obbligatorio | Obbligatorio |
| Source provenance attestation | — | — | Obbligatorio | Obbligatorio |
| Two-party review (reviewer ≠ autore) | — | — | — | Obbligatorio |
| Conservazione delle revisioni (retention policy) | — | — | — | Obbligatorio |
| Branch protection enforced dalla piattaforma | — | — | — | Obbligatorio |

**Source Provenance Attestation** — un concetto centrale introdotto dal Source Track. A differenza della build provenance (che attesta _come_ un artefatto è stato compilato), la source provenance attesta _quali modifiche_ sono state integrate nel codice sorgente e _chi_ le ha approvate. Il predicato utilizzato è `https://slsa.dev/source-provenance/v1-rc1`, che include:

- Il repository URI e il commit SHA della revisione attestata.
- L'elenco dei reviewer che hanno approvato la modifica.
- Il branch di destinazione e le protezioni attive al momento del merge.
- L'identità della piattaforma SCM che ha eseguito il merge.

**Mapping GitHub → Source Track:**

| Requisito Source Track | Implementazione GitHub |
|---|---|
| Version control system | Git repository ospitato su GitHub |
| Identità verificata | GitHub identity via SAML SSO, vigilant mode, o commit signing con chiavi SSH/GPG verificate |
| Revisioni immutabili | Branch protection rule: "Block force pushes" + "Block deletions" |
| Source provenance | GitHub Artifact Attestations con predicate type `https://slsa.dev/source-provenance/v1-rc1` (supporto in preview Q1 2026) |
| Two-party review | Branch protection rule: "Require a pull request before merging" + "Require approvals" ≥ 1 |
| Retention | Repository retention policy + GitHub archival (Arctic Code Vault per repos pubblici) |
| Branch protection enforced | Rulesets (repository rules) con enforcement "Active" e nessuna eccezione per admin |

**Interazione tra Build Track e Source Track:** I due track sono complementari ma indipendenti. Un artefatto può raggiungere Build L3 senza soddisfare alcun requisito Source (e viceversa). L'obiettivo a lungo termine di SLSA è che i consumatori possano verificare _sia_ la build provenance _sia_ la source provenance:

```text
Consumer verifica artefatto
├── Build Track L3: "questo binary è stato prodotto da un builder isolato e verificabile"
└── Source Track L3: "il codice sorgente è passato attraverso code review e la storia è immutabile"
```

La combinazione di entrambi i track al livello L3 fornisce la protezione più robusta contro gli attacchi alla supply chain: garantisce che nessuna singola persona — nemmeno un maintainer compromesso — possa introdurre codice malevolo che venga poi compilato e distribuito senza traccia di revisione.

**Nota sulla stabilità:** SLSA v1.2 con Source Track è contrassegnato come "Release Candidate 2" a novembre 2025. Il comitato tecnico SLSA prevede la promozione a "Stable" nella prima metà del 2026, subordinata all'implementazione di almeno due piattaforme SCM conformi (GitHub e GitLab sono le candidate principali).

#### Dependencies Track (in sviluppo)

Il Dependencies Track si concentrerà su:

1. **Dipendenze note e dichiarate:** tutte le dipendenze devono essere esplicitamente dichiarate.
2. **Dipendenze verificate:** ogni dipendenza deve avere provenance verificabile.
3. **Dipendenze scansionate:** scan automatico per vulnerabilità note.
4. **SBOM obbligatorio:** generazione e distribuzione di un SBOM completo.

### Mapping GitHub Actions → SLSA

| Requisito SLSA | Come GitHub Actions lo soddisfa |
|---|---|
| Hosted build platform | GitHub-hosted runners |
| Ephemeral environment | Ogni job ha un runner pulito |
| Signed provenance | `actions/attest-build-provenance` firma via Sigstore |
| Non-forgeable provenance | Il token OIDC è emesso dal runner, non dal workflow |
| Source identity | SHA del commit, ref del branch, repository |
| Builder identity | Workflow ref, runner environment |

---

## Build provenance

### Cos'è la provenance

La provenance è un documento firmato che risponde a:

- **Chi** ha buildato l'artefatto? (builder identity)
- **Cosa** è stato buildato? (subject — nome e digest)
- **Da dove** viene il source code? (source repository, commit SHA)
- **Come** è stato buildato? (workflow, parametri, ambiente)
- **Quando** è stato buildato? (timestamp)

### Esempio di provenance

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "ghcr.io/myorg/myimage",
      "digest": {
        "sha256": "abc123def456..."
      }
    }
  ],
  "predicateType": "https://slsa.dev/provenance/v1",
  "predicate": {
    "buildDefinition": {
      "buildType": "https://actions.github.io/buildtypes/workflow/v1",
      "externalParameters": {
        "workflow": {
          "ref": "refs/heads/main",
          "repository": "https://github.com/myorg/myrepo",
          "path": ".github/workflows/build.yml"
        }
      },
      "internalParameters": {
        "github": {
          "event_name": "push",
          "repository_id": "67890",
          "repository_owner_id": "12345"
        }
      },
      "resolvedDependencies": [
        {
          "uri": "git+https://github.com/myorg/myrepo@refs/heads/main",
          "digest": {
            "gitCommit": "abc123def456789..."
          }
        }
      ]
    },
    "runDetails": {
      "builder": {
        "id": "https://github.com/actions/runner/github-hosted"
      },
      "metadata": {
        "invocationId": "https://github.com/myorg/myrepo/actions/runs/123456789/attempts/1",
        "startedOn": "2026-05-22T10:00:00Z",
        "finishedOn": "2026-05-22T10:05:00Z"
      }
    }
  }
}
```

### Campi critici per la sicurezza

| Campo | Perché è importante |
|---|---|
| `subject.digest.sha256` | Lega la provenance a un artefatto specifico, immutabile |
| `buildDefinition.externalParameters.workflow` | Identifica esattamente quale workflow ha prodotto l'artefatto |
| `resolvedDependencies[].digest.gitCommit` | Lega la build a un commit source preciso |
| `runDetails.builder.id` | Identifica la piattaforma di build (non falsificabile) |
| `runDetails.metadata.invocationId` | Link diretto alla run di GitHub Actions |

---

## Formato attestazione — in-toto

### Struttura in-toto Statement

[in-toto](https://in-toto.io/) è lo standard per le attestazioni di supply chain. Ogni attestazione è un "Statement" con tre parti:

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [...],        // Artefatti a cui si riferisce
  "predicateType": "...",  // Tipo di predicato
  "predicate": {...}       // Contenuto del predicato
}
```

### Tipi di predicato

| Predicato | URI | Scopo |
|---|---|---|
| **SLSA Provenance** | `https://slsa.dev/provenance/v1` | Origine della build |
| **SPDX SBOM** | `https://spdx.dev/Document/v2.3` | Bill of materials |
| **CycloneDX SBOM** | `https://cyclonedx.org/bom/v1.5` | Bill of materials |
| **Vulnerability scan** | `https://cosign.sigstore.dev/attestation/vuln/v1` | Risultati scan |
| **Custom** | URI personalizzato | Attestazioni custom |

### DSSE (Dead Simple Signing Envelope)

Le attestazioni in-toto sono wrappate in una busta DSSE per la firma:

```json
{
  "payloadType": "application/vnd.in-toto+json",
  "payload": "<base64-encoded statement>",
  "signatures": [
    {
      "keyid": "",
      "sig": "<base64-encoded signature>"
    }
  ]
}
```

### Anatomia completa dell'in-toto Statement v1

Lo Statement v1 è il cuore del framework in-toto. Ogni campo ha un ruolo preciso nella catena di fiducia:

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "pkg:npm/@myorg/mypackage@1.2.3",
      "digest": {
        "sha256": "a1b2c3d4e5f6...",
        "sha512": "f6e5d4c3b2a1..."
      }
    }
  ],
  "predicateType": "https://slsa.dev/provenance/v1",
  "predicate": { ... }
}
```

**Campo `_type`:** identifica il formato del documento. Per Statement v1, è sempre `https://in-toto.io/Statement/v1`. Questo permette ai verificatori di parsare correttamente il documento senza ambiguità.

**Campo `subject`:** uno o più artefatti a cui l'attestazione si riferisce. Ogni subject ha un `name` (identificativo leggibile) e un `digest` (hash crittografico). Il nome può seguire la convenzione Package URL (purl) per una identificazione standardizzata. Sono supportati più algoritmi di digest simultaneamente — tipicamente SHA-256, con SHA-512 come backup.

**Campo `predicateType`:** URI che identifica il tipo di predicato. Questo campo permette ai consumatori di sapere come interpretare il contenuto del `predicate`. Il framework definisce predicati standard ma supporta anche URI personalizzati.

**Campo `predicate`:** contenuto specifico del tipo di predicato. La struttura dipende interamente dal `predicateType`.

### Predicati avanzati

Oltre ai predicati base, il framework supporta predicati specializzati per casi d'uso specifici:

#### SCAI — Supply Chain Attribute Integrity

Il predicato SCAI (Supply Chain Attribute Integrity) permette di attestare attributi generici di un artefatto, come risultati di test, metriche di qualità del codice, o conformità a standard:

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [{"name": "myapp", "digest": {"sha256": "..."}}],
  "predicateType": "https://in-toto.io/attestation/scai/attribute-report/v0.2",
  "predicate": {
    "attributes": [
      {
        "attribute": "PASSED_CODE_REVIEW",
        "target": {"name": "myapp", "digest": {"sha256": "..."}},
        "conditions": {"reviewers_count": 2, "approved": true},
        "evidence": {
          "name": "pr-review-report",
          "uri": "https://github.com/myorg/myrepo/pull/42"
        }
      },
      {
        "attribute": "PASSED_STATIC_ANALYSIS",
        "target": {"name": "myapp", "digest": {"sha256": "..."}},
        "conditions": {"tool": "semgrep", "findings_critical": 0}
      }
    ]
  }
}
```

#### Link Predicate (legacy ma ancora diffuso)

Il predicato Link è il formato originale di in-toto, che modella un singolo passo nella supply chain:

```json
{
  "predicateType": "https://in-toto.io/attestation/link/v0.3",
  "predicate": {
    "name": "build",
    "command": ["make", "build"],
    "materials": [
      {"uri": "git+https://github.com/myorg/myrepo", "digest": {"sha256": "..."}}
    ],
    "products": [
      {"uri": "file:///build/output/binary", "digest": {"sha256": "..."}}
    ],
    "byproducts": {
      "return-value": 0,
      "stdout": "Build completed successfully",
      "stderr": ""
    },
    "environment": {
      "os": "ubuntu-22.04",
      "arch": "amd64"
    }
  }
}
```

#### Runtime Trace Predicate

Per ambienti con requisiti di tracciabilità stringenti, è possibile attestare il comportamento runtime:

```json
{
  "predicateType": "https://in-toto.io/attestation/runtime-trace/v0.1",
  "predicate": {
    "monitor": "strace",
    "tracePolicy": "network-egress-only",
    "observations": [
      {"type": "network", "destination": "registry.npmjs.org:443", "allowed": true},
      {"type": "network", "destination": "evil.example.com:443", "allowed": false}
    ]
  }
}
```

### Relazione tra i componenti

```text
┌─────────────────────────────────────────────┐
│  DSSE Envelope                               │
│  ┌─────────────────────────────────────────┐ │
│  │  in-toto Statement                      │ │
│  │  ┌───────────┐  ┌────────────────────┐  │ │
│  │  │  Subject  │  │  Predicate         │  │ │
│  │  │  (digest) │  │  (SLSA Provenance  │  │ │
│  │  │           │  │   o SBOM           │  │ │
│  │  │           │  │   o Vuln scan)     │  │ │
│  │  └───────────┘  └────────────────────┘  │ │
│  └─────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────┐ │
│  │  Signature (Sigstore / cosign)          │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## SLSA GitHub generator

### slsa-framework/slsa-github-generator

Il progetto ufficiale SLSA fornisce un reusable workflow che genera provenance L3:

```yaml
name: SLSA Provenance
on:
  release:
    types: [created]

permissions:
  id-token: write
  contents: write
  actions: read

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digests: ${{ steps.hash.outputs.digests }}
    steps:
      - uses: actions/checkout@v4

      - name: Build binary
        run: |
          go build -o my-binary ./cmd/
          sha256sum my-binary > checksums.txt

      - name: Generate hash
        id: hash
        run: |
          DIGEST=$(sha256sum my-binary | awk '{print $1}')
          echo "digests=$(echo -n "my-binary:$DIGEST" | base64 -w0)" >> "$GITHUB_OUTPUT"

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: my-binary
          path: my-binary

  provenance:
    needs: build
    permissions:
      actions: read
      id-token: write
      contents: write
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.0.0
    with:
      base64-subjects: "${{ needs.build.outputs.digests }}"
      upload-assets: true
```

### Cosa produce

1. Un file `my-binary.intoto.jsonl` contenente la provenance SLSA L3.
2. Firmato via Sigstore (OIDC keyless).
3. Registrato nel transparency log Rekor.
4. Allegato alla GitHub Release.

### Container provenance

```yaml
# Provenance per container image
provenance:
  needs: build
  permissions:
    actions: read
    id-token: write
    packages: write
  uses: slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@v2.0.0
  with:
    image: ghcr.io/myorg/myimage
    digest: ${{ needs.build.outputs.digest }}
    registry-username: ${{ github.actor }}
    gha-token: ${{ secrets.GITHUB_TOKEN }}
```

---

## Sigstore — cosign, Rekor, Fulcio

### Panoramica dell'ecosistema Sigstore

```text
┌──────────────────────────────────────────────────────────┐
│  Sigstore Ecosystem                                       │
│                                                           │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────────┐  │
│  │  Fulcio   │   │  Rekor   │   │  cosign              │  │
│  │  (CA)     │   │  (Log)   │   │  (Client)            │  │
│  │           │   │          │   │                      │  │
│  │  Emette   │   │ Registra │   │  Firma, verifica,    │  │
│  │  certificati  │ in modo  │   │  attesta artefatti   │  │
│  │  effimeri │   │ immutabile│  │                      │  │
│  └──────────┘   └──────────┘   └──────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Fulcio — Certificate Authority

Fulcio emette certificati X.509 di breve durata basati su identità OIDC:

1. Il client si autentica via OIDC (GitHub Actions token).
2. Fulcio verifica il token e emette un certificato con lifetime ~10 minuti.
3. Il certificato contiene l'identità OIDC (es. repository, workflow).
4. Il client usa il certificato per firmare l'artefatto.

### Rekor — Transparency Log

Rekor è un log immutabile e pubblico che registra tutte le firme:

- **Immutabile:** una volta registrata, una entry non può essere modificata o cancellata.
- **Verificabile:** chiunque può verificare che una firma è stata registrata.
- **Timestamped:** ogni entry ha un timestamp verificabile.
- **Pubblico:** [rekor.sigstore.dev](https://rekor.sigstore.dev)

```bash
# Cercare nel log Rekor
rekor-cli search --email "ciupsciups@libero.it"
rekor-cli search --sha "sha256:abc123..."

# Ottenere un'entry specifica
rekor-cli get --uuid "abc123..."
```

### cosign — il client

```bash
# Installare cosign
go install github.com/sigstore/cosign/v2/cmd/cosign@latest

# === FIRMARE ===

# Firma keyless (usa OIDC — ideale per CI)
cosign sign --yes ghcr.io/myorg/myimage@sha256:abc123...

# Firma con chiave privata
cosign generate-key-pair
cosign sign --key cosign.key ghcr.io/myorg/myimage@sha256:abc123...

# === VERIFICARE ===

# Verifica keyless — richiede certificate identity e issuer
cosign verify \
  --certificate-identity "https://github.com/myorg/myrepo/.github/workflows/build.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/myorg/myimage@sha256:abc123...

# === ATTESTARE ===

# Attestare un artefatto con predicato custom
cosign attest --yes \
  --predicate sbom.spdx.json \
  --type spdxjson \
  ghcr.io/myorg/myimage@sha256:abc123...

# Verificare attestazione
cosign verify-attestation \
  --certificate-identity "https://github.com/myorg/myrepo/.github/workflows/build.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  --type spdxjson \
  ghcr.io/myorg/myimage@sha256:abc123...
```

### Cosign v3 — bundle format e trusted root

Cosign v3 rappresenta un'evoluzione significativa rispetto alle versioni precedenti, con il nuovo bundle format come default. I cambiamenti principali:

| Caratteristica | Cosign v2 | Cosign v3 |
|---|---|---|
| Bundle format | Opt-in (`--new-bundle-format`) | Default |
| Trusted root | File separati | File unificato (`--trusted-root`) |
| Signing config | Hardcoded | Configurabile (`--signing-config`) |
| Output firma | Tag OCI separato | Bundle Sigstore integrato |
| Rotazione log | Manuale | Automatica via signing config |

#### Il Sigstore Bundle

Il bundle Sigstore contiene tutto il materiale necessario per la verifica offline in un singolo file:

```json
{
  "mediaType": "application/vnd.dev.sigstore.bundle.v0.3+json",
  "verificationMaterial": {
    "certificate": {
      "rawBytes": "<base64-encoded X.509 certificate>"
    },
    "tlogEntries": [
      {
        "logIndex": "12345678",
        "logId": {
          "keyId": "<base64-encoded Rekor public key>"
        },
        "kindVersion": {
          "kind": "hashedrekord",
          "version": "0.0.1"
        },
        "integratedTime": "1716393600",
        "inclusionPromise": {
          "signedEntryTimestamp": "<base64>"
        },
        "inclusionProof": {
          "logIndex": "12345678",
          "rootHash": "<hex>",
          "treeSize": "98765432",
          "hashes": ["<hex>", "<hex>", "<hex>"]
        },
        "canonicalizedBody": "<base64>"
      }
    ],
    "timestampVerificationData": {
      "rfc3161Timestamps": []
    }
  },
  "messageSignature": {
    "messageDigest": {
      "algorithm": "SHA2_256",
      "digest": "<base64>"
    },
    "signature": "<base64>"
  }
}
```

#### Operazioni con cosign v3

```bash
# Firmare un blob con bundle output (default in v3)
cosign sign-blob --bundle my-artifact.bundle my-artifact.tar.gz

# Verificare un blob dal bundle
cosign verify-blob --bundle my-artifact.bundle \
  --certificate-identity "https://github.com/myorg/myrepo/.github/workflows/release.yml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  my-artifact.tar.gz

# Usare trusted-root personalizzato (per istanze Sigstore private)
cosign verify --trusted-root /path/to/trusted-root.json \
  ghcr.io/myorg/myimage@sha256:abc123...

# Firmare con timestamp authority (RFC 3161)
cosign sign-blob --bundle my-artifact.bundle \
  --timestamp-server-url "https://freetsa.org/tsr" \
  my-artifact.tar.gz
```

#### Trusted Root

Il file `trusted-root.json` consolida tutte le root of trust per la verifica:

```json
{
  "mediaType": "application/vnd.dev.sigstore.trustedroot+json;version=0.1",
  "tlogs": [
    {
      "baseUrl": "https://rekor.sigstore.dev",
      "hashAlgorithm": "SHA2_256",
      "publicKey": {
        "rawBytes": "<base64>",
        "keyDetails": "PKIX_ECDSA_P256_SHA_256",
        "validFor": {"start": "2021-01-12T11:53:27Z"}
      },
      "logId": {"keyId": "<base64>"}
    }
  ],
  "certificateAuthorities": [
    {
      "subject": {"organization": "sigstore.dev", "commonName": "sigstore"},
      "uri": "https://fulcio.sigstore.dev",
      "certChain": {"certificates": [{"rawBytes": "<base64>"}]},
      "validFor": {"start": "2022-04-13T20:06:15Z"}
    }
  ],
  "timestampAuthorities": []
}
```

Questo approccio permette la rotazione delle chiavi di Rekor e dei certificati di Fulcio senza aggiornare il client cosign — basta aggiornare il file trusted-root.

### Rekor v2 — Architettura tile-based

Nell'ottobre 2025, il progetto Sigstore ha rilasciato **Rekor v2 GA** (General Availability), la riscrittura più significativa del transparency log dalla sua creazione nel 2021. La motivazione principale è stata la scalabilità: Rekor v1, basato su Trillian (Google Certificate Transparency), ha raggiunto i limiti architetturali gestendo centinaia di milioni di entry nel log globale condiviso.

**Architettura Trillian-Tessera:**

Rekor v2 abbandona il backend Trillian a favore di **Trillian-Tessera** (noto anche come "tlog-tiles"), un'implementazione tile-based ispirata alla Go module checksum database (`sum.golang.org`). Il log è organizzato in tile fissi:

```text
Rekor v1 (Trillian)              Rekor v2 (Trillian-Tessera)
====================             ===========================

  Merkle Tree monolitico           Tile-based log
  ┌──────────────────┐            ┌───┬───┬───┬───┐
  │  Root Hash       │            │T0 │T1 │T2 │T3 │  ← tile di dati
  │  ├── Node        │            ├───┼───┼───┼───┤
  │  │   ├── Leaf    │            │H0 │H1 │H2 │H3 │  ← tile di hash
  │  │   └── Leaf    │            └───┴───┴───┴───┘
  │  └── Node        │
  │      ├── Leaf    │            Ogni tile = 256 entry
  │      └── Leaf    │            Servibili via CDN/object storage
  └──────────────────┘            Nessun database relazionale
```

**Cambiamenti critici in Rekor v2:**

| Aspetto | Rekor v1 | Rekor v2 |
|---|---|---|
| Backend | Trillian + MySQL/MariaDB | Trillian-Tessera + object storage (S3, GCS, Azure Blob) |
| Tipi di entry supportati | hashedrekord, rekord, rpm, dsse, intoto, cose, tuf, alpine, helm | Solo **hashedrekord** e **dsse** |
| Supporto PGP/minisign/SSH | Sì | **Rimosso** — solo firme Sigstore (Fulcio OIDC + cosign) |
| Indice di ricerca | Search API con query per email, hash, chiave pubblica | **Rimosso** — lookup solo per log index o entry UUID |
| Timestamp authority | Integrata nel log entry | Dedicata (Timestamp Authority separata, RFC 3161-compatible) |
| Sharding | Log singolo, crescita illimitata | **Log shardati** con URL dedicati per shard |
| Storage | Database relazionale | Object storage (tile come file statici su CDN) |
| Costo operativo | Alto (database, replica, backup) | **Ridotto ~80%** (file statici su cloud storage) |

**Migrazione e deprecazione di Rekor v1:**

La timeline annunciata dal Sigstore Technical Steering Committee:

```text
Ottobre 2025     Rekor v2 GA — nuove entry scritte solo su v2
Gennaio 2026     Rekor v1 in modalità read-only (nessuna nuova entry)
Luglio 2026      Rekor v1 API deprecata — redirect automatico a v2
Dicembre 2026    Rekor v1 spento — i dati storici migrati in v2 come shard frozen
```

**Impatto sui workflow GitHub Actions:**

Per la maggior parte degli utenti, la migrazione a Rekor v2 è trasparente. Le action ufficiali (`sigstore/cosign-installer`, `actions/attest-build-provenance`, `slsa-framework/slsa-github-generator`) gestiscono automaticamente il routing verso il backend corretto tramite il file `trusted-root.json`. Tuttavia, chi usa Rekor direttamente tramite API REST deve aggiornare:

```bash
# Rekor v1 — ricerca per hash (DEPRECATA)
rekor-cli search --sha "sha256:abc123..."

# Rekor v2 — lookup per log index (unico metodo supportato)
rekor-cli get --log-index 12345678
# oppure per UUID
rekor-cli get --uuid "24296fb24b8ad77a..."

# Verifica inclusion proof con tile-based log
cosign verify-blob --bundle entry.sigstore.json \
  --certificate-identity "user@example.com" \
  --certificate-oidc-issuer "https://accounts.google.com" \
  my-artifact.tar.gz
```

**Perché la rimozione dell'indice di ricerca è significativa:** In Rekor v1, era possibile cercare tutte le entry associate a un determinato indirizzo email o chiave pubblica. Questa funzionalità, sebbene utile per il debugging, rappresentava un rischio per la privacy (chiunque poteva enumerare tutte le firme associate a un'identità) e un collo di bottiglia per le prestazioni. Rekor v2 adotta un approccio "append-only log senza indice" — i consumatori devono conoscere il log index o l'UUID dell'entry specifica. Per il discovery, Sigstore raccomanda di allegare il bundle `.sigstore.json` direttamente all'artefatto o al container image come OCI artifact.

### Gitsign — firma keyless dei commit Git

**Gitsign** è un componente dell'ecosistema Sigstore che estende il paradigma di firma keyless ai commit Git. Invece di gestire chiavi GPG o SSH per firmare i commit, Gitsign utilizza il flusso OIDC → Fulcio → Rekor già descritto per cosign, applicandolo ai commit e ai tag Git.

**Come funziona:**

```text
Developer esegue `git commit -S`
         │
         ▼
Gitsign intercetta la richiesta di firma
         │
         ▼
Browser apre il provider OIDC (GitHub, Google, Microsoft)
         │
         ▼
Fulcio emette un certificato X.509 effimero (validità ~10 min)
    legato all'identità OIDC del developer
         │
         ▼
Gitsign firma il commit con il certificato effimero
         │
         ▼
La firma + il certificato vengono registrati su Rekor
         │
         ▼
Il commit contiene la firma S/MIME nel campo `gpgsig`
```

**Installazione e configurazione (Gitsign v0.16.0, maggio 2026):**

```bash
# Installazione via Go
go install github.com/sigstore/gitsign@latest

# Oppure via Homebrew
brew install sigstore/tap/gitsign

# Configurazione globale
git config --global gpg.x509.program gitsign
git config --global gpg.format x509
git config --global commit.gpgsign true

# Opzionale: specificare il connettore Fulcio/Rekor
git config --global gitsign.fulcio https://fulcio.sigstore.dev
git config --global gitsign.rekor https://rekor.sigstore.dev
```

**Verifica dei commit firmati con Gitsign:**

```bash
# Verifica manuale
gitsign verify --certificate-identity "developer@example.com" \
  --certificate-oidc-issuer "https://github.com/login/oauth" \
  HEAD

# Verifica con output dettagliato
gitsign verify --verbose HEAD
# Output:
# tlog index: 45678901
# Fulcio certificate:
#   Issuer: https://github.com/login/oauth
#   Subject: developer@example.com
#   GitHub Workflow: refs/heads/main
# Certificate valid at time of signing
# Entry included in Rekor log

# Verifica via GitHub UI
# GitHub riconosce i commit firmati con Gitsign e mostra il badge "Verified"
# quando il certificato Fulcio è legato a un'identità GitHub verificata
```

**Relazione con SLSA Source Track:** Gitsign è una delle implementazioni raccomandate per soddisfare il requisito di "identità verificata dell'autore" al livello Source L2. A differenza della firma GPG tradizionale — dove la chiave può essere compromessa, condivisa, o mai revocata — Gitsign lega ogni firma a un'identità OIDC verificata al momento della firma. Questo elimina il problema della gestione delle chiavi a lungo termine e fornisce un audit trail completo tramite Rekor.

**Limitazioni attuali di Gitsign:**

- Richiede accesso al browser per il flusso OIDC interattivo (non ideale per ambienti headless o CI). In CI, si può usare il flusso OIDC non-interattivo con `SIGSTORE_ID_TOKEN`.
- I certificati Fulcio sono effimeri: non è possibile verificare la firma _dopo_ la scadenza del certificato senza consultare Rekor per il timestamp di inclusione.
- La dimensione del commit aumenta di circa 2-4 KB per la firma S/MIME + il certificato inline.
- Non tutti gli strumenti Git visualizzano correttamente le firme X.509 (rispetto alle firme GPG, che sono supportate universalmente).

### Workflow completo con cosign

```yaml
name: Build, Sign, Attest
on:
  push:
    branches: [main]

permissions:
  contents: read
  packages: write
  id-token: write

jobs:
  build-sign:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: sigstore/cosign-installer@v3

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/myorg/myimage:${{ github.sha }}

      - name: Sign image
        run: |
          cosign sign --yes \
            ghcr.io/myorg/myimage@${{ steps.build.outputs.digest }}

      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        with:
          image: ghcr.io/myorg/myimage@${{ steps.build.outputs.digest }}
          output-file: sbom.spdx.json
          format: spdx-json

      - name: Attest SBOM
        run: |
          cosign attest --yes \
            --predicate sbom.spdx.json \
            --type spdxjson \
            ghcr.io/myorg/myimage@${{ steps.build.outputs.digest }}
```

---

## Software Bill of Materials (SBOM)

### Cos'è un SBOM

Un SBOM è un inventario completo di tutti i componenti software che costituiscono un artefatto:

```text
Il tuo software
├── Dipendenza A (v1.2.3) — MIT License
│   ├── Sub-dipendenza A1 (v0.9.0) — Apache 2.0
│   └── Sub-dipendenza A2 (v2.1.0) — BSD-3
├── Dipendenza B (v4.5.6) — Apache 2.0
│   └── Sub-dipendenza B1 (v1.0.0) — MIT
└── Dipendenza C (v7.8.9) — GPL-3.0  ← ATTENZIONE licenza
```

### Formati SBOM

| Formato | Standard | Uso tipico |
|---|---|---|
| **SPDX** | ISO/IEC 5962:2021 | Compliance, governo, enterprise |
| **CycloneDX** | OWASP | Security-focused, integrazione DevSecOps |

### Generare SBOM in GitHub Actions

```yaml
# Con Anchore Syft
- name: Generate SBOM (Syft)
  uses: anchore/sbom-action@v0
  with:
    image: ghcr.io/myorg/myimage@${{ steps.build.outputs.digest }}
    output-file: sbom.spdx.json
    format: spdx-json

# Con Microsoft SBOM Tool
- name: Generate SBOM (Microsoft)
  uses: microsoft/sbom-action@v2
  with:
    buildDropPath: ./build
    outputPath: ./sbom

# Con Trivy
- name: Generate SBOM (Trivy)
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: image
    image-ref: ghcr.io/myorg/myimage:latest
    format: spdx-json
    output: sbom.spdx.json
```

### SBOM per progetto Node.js

```yaml
- name: Generate npm SBOM
  run: |
    # npm ha generazione SBOM integrata
    npm sbom --sbom-format spdx > sbom.spdx.json

    # Alternativa: CycloneDX
    npx @cyclonedx/cyclonedx-npm --output-format JSON > sbom.cdx.json
```

### SBOM per progetto Python

```yaml
- name: Generate Python SBOM
  run: |
    pip install cyclonedx-bom
    cyclonedx-py requirements \
      --input-file requirements.txt \
      --output-format json \
      --output-file sbom.cdx.json
```

### SBOM come GitHub dependency graph

GitHub genera automaticamente un dependency graph per i linguaggi supportati. Per SBOM personalizzati:

```yaml
- name: Upload SBOM to dependency graph
  uses: advanced-security/spdx-dependency-submission-action@v0.1.1
  with:
    filePath: sbom.spdx.json
```

---

### SBOM per ecosistemi aggiuntivi

#### Go modules

```yaml
- name: Generate Go SBOM
  run: |
    # Syft supporta nativamente go.sum
    syft packages dir:. -o spdx-json > sbom.spdx.json

    # Alternativa con CycloneDX gomod
    go install github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod@latest
    cyclonedx-gomod mod -json -output sbom.cdx.json
```

#### Rust (Cargo)

```yaml
- name: Generate Rust SBOM
  run: |
    cargo install cargo-cyclonedx
    cargo cyclonedx --format json --output-file sbom.cdx.json

    # Con Syft
    syft packages dir:. -o spdx-json > sbom.spdx.json
```

#### Multi-linguaggio con Syft

```yaml
- name: Generate comprehensive SBOM
  run: |
    # Syft rileva automaticamente tutti i package manager
    syft packages dir:. \
      -o spdx-json \
      --source-name "myproject" \
      --source-version "${{ github.sha }}" \
      > sbom.spdx.json

    # Includere anche i layer Docker
    syft packages ghcr.io/myorg/myimage@${{ steps.build.outputs.digest }} \
      -o cyclonedx-json \
      --scope all-layers \
      > sbom-container.cdx.json
```

### Confronto approfondito SPDX vs CycloneDX

| Criterio | SPDX | CycloneDX |
|---|---|---|
| **Standardizzazione** | ISO/IEC 5962:2021 | OWASP Standard |
| **Focus principale** | Licenze, compliance | Sicurezza, vulnerabilità |
| **Versione corrente** | SPDX 2.3 (3.0 in sviluppo) | CycloneDX 1.7 (ottobre 2025) |
| **VEX integrato** | No (documento separato) | Sì (CycloneDX VEX nativo) |
| **Formati output** | JSON, YAML, RDF/XML, Tag-Value | JSON, XML, Protobuf |
| **Relazioni componenti** | Dettagliate (CONTAINS, DEPENDS_ON, ecc.) | Basiche (dependencies) |
| **Licensing expressions** | Molto maturo (SPDX expressions) | Supportato ma meno dettagliato |
| **Use case ideale** | Procurement governativo, legal compliance | DevSecOps, CI/CD automation |
| **Tool ecosystem** | Syft, SPDX tools, Tern | Syft, CycloneDX CLI, Trivy |
| **Supporto Kubernetes** | Buono | Eccellente (Grype, Trivy) |
| **Interoperabilità** | Protobom (conversione) | Protobom (conversione) |

**Raccomandazione pratica:** generare SBOM in entrambi i formati quando possibile. Usare SPDX per requisiti di compliance/procurement e CycloneDX per workflow di sicurezza. Tool come Protobom e BomCTL permettono conversione lossless tra i due formati.

---

## VEX — Vulnerability Exploitability eXchange

### Cos'è VEX

VEX (Vulnerability Exploitability eXchange) è un tipo di advisory di sicurezza il cui obiettivo è comunicare l'effettiva sfruttabilità di componenti con vulnerabilità note nel contesto del prodotto in cui sono utilizzati. In pratica, VEX risponde alla domanda: "questa CVE nel mio SBOM è davvero un problema per il mio software?"

Un SBOM senza VEX genera rumore: se una dipendenza transitiva ha una CVE, ma il codice vulnerabile non è raggiungibile nel contesto del prodotto, il team di sicurezza perde tempo a investigare falsi positivi.

### Status VEX

| Status | Significato |
|---|---|
| **Not Affected** | La vulnerabilità non è sfruttabile nel contesto del prodotto |
| **Affected** | La vulnerabilità è sfruttabile — serve remediation |
| **Fixed** | La vulnerabilità è stata risolta in questa versione |
| **Under Investigation** | L'analisi è in corso |

### Formati VEX

Esistono tre implementazioni principali di VEX:

#### OpenVEX

Formato leggero e standalone, progettato per semplicità e ampia adozione:

```json
{
  "@context": "https://openvex.dev/ns/v0.2.0",
  "@id": "https://example.com/vex/2026-05-24/1",
  "author": "security-team@myorg.com",
  "timestamp": "2026-05-24T10:00:00Z",
  "version": 1,
  "statements": [
    {
      "vulnerability": {
        "@id": "https://nvd.nist.gov/vuln/detail/CVE-2024-1234"
      },
      "products": [
        {"@id": "pkg:oci/myimage@sha256:abc123..."}
      ],
      "status": "not_affected",
      "justification": "component_not_present",
      "impact_statement": "La funzione vulnerabile di libfoo non viene invocata nel nostro codice. Il pacchetto è incluso come dipendenza transitiva ma il modulo affetto è eliminato dal tree-shaking in fase di build."
    },
    {
      "vulnerability": {
        "@id": "https://nvd.nist.gov/vuln/detail/CVE-2025-5678"
      },
      "products": [
        {"@id": "pkg:oci/myimage@sha256:abc123..."}
      ],
      "status": "fixed",
      "action_statement": "Aggiornato a libbar >= 2.3.1 che include il fix."
    }
  ]
}
```

#### CycloneDX VEX

CycloneDX integra VEX direttamente nel documento SBOM:

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.7",
  "vulnerabilities": [
    {
      "id": "CVE-2024-1234",
      "source": {"name": "NVD", "url": "https://nvd.nist.gov/"},
      "ratings": [
        {"score": 7.5, "severity": "high", "method": "CVSSv31"}
      ],
      "analysis": {
        "state": "not_affected",
        "justification": "code_not_reachable",
        "detail": "La funzione vulnerabile non è raggiungibile dal nostro entry point.",
        "response": ["will_not_fix"]
      },
      "affects": [
        {"ref": "component-uuid-1234"}
      ]
    }
  ]
}
```

#### CSAF VEX

Common Security Advisory Framework — formato più strutturato e formale, adottato da grandi vendor:

```json
{
  "document": {
    "category": "csaf_vex",
    "publisher": {
      "category": "vendor",
      "name": "MyOrg Security Team"
    },
    "title": "VEX per MyProduct v2.1",
    "tracking": {
      "current_release_date": "2026-05-24T10:00:00Z",
      "id": "MYORG-VEX-2026-001",
      "initial_release_date": "2026-05-24T10:00:00Z",
      "revision_history": [{"date": "2026-05-24T10:00:00Z", "number": "1"}],
      "status": "final",
      "version": "1"
    }
  },
  "vulnerabilities": [
    {
      "cve": "CVE-2024-1234",
      "product_status": {
        "known_not_affected": ["CSAFPID-0001"]
      },
      "threats": [
        {
          "category": "impact",
          "details": "Componente non raggiungibile nel contesto del prodotto."
        }
      ]
    }
  ]
}
```

### Workflow VEX in GitHub Actions

```yaml
name: SBOM + VEX Pipeline
on:
  push:
    branches: [main]

jobs:
  sbom-vex:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate SBOM
        run: |
          syft packages dir:. -o cyclonedx-json > sbom.cdx.json

      - name: Scan vulnerabilities
        run: |
          grype sbom:sbom.cdx.json -o json > vuln-report.json

      - name: Generate VEX
        run: |
          # Installare vexctl
          go install github.com/openvex/vexctl@latest

          # Creare un documento VEX per CVE non sfruttabili
          vexctl create \
            --product "pkg:github/myorg/myrepo@${{ github.sha }}" \
            --vuln "CVE-2024-1234" \
            --status "not_affected" \
            --justification "component_not_present" \
            > vex.openvex.json

      - name: Apply VEX to filter false positives
        run: |
          # Filtrare le vulnerabilità non applicabili
          grype sbom:sbom.cdx.json \
            --vex vex.openvex.json \
            -o json > filtered-vulns.json

          # Contare solo le vulnerabilità reali
          REAL_VULNS=$(jq '[.matches[] | select(.vulnerability.severity == "Critical" or .vulnerability.severity == "High")] | length' filtered-vulns.json)
          echo "Vulnerabilità reali (dopo VEX): $REAL_VULNS"

          if [ "$REAL_VULNS" -gt 0 ]; then
            echo "ATTENZIONE: $REAL_VULNS vulnerabilità critiche/alte da risolvere"
            exit 1
          fi

      - name: Attest VEX
        run: |
          cosign attest --yes \
            --predicate vex.openvex.json \
            --type openvex \
            ghcr.io/myorg/myimage@${{ needs.build.outputs.digest }}
```

### Quando usare VEX

| Scenario | Necessità di VEX |
|---|---|
| CVE in dipendenza transitiva non raggiungibile | Sì — `not_affected`, `code_not_reachable` |
| CVE in modulo usato ma con workaround | Sì — `affected`, con `action_statement` |
| CVE risolta nell'ultimo aggiornamento | Sì — `fixed` |
| CVE in fase di analisi | Sì — `under_investigation` |
| CVE attivamente sfruttata nel prodotto | No — serve un fix immediato, non un VEX |

---

## Dependabot — alerts, updates, security updates

### Dependabot Alerts

Notifiche automatiche quando una dipendenza ha una vulnerabilità nota (CVE):

```yaml
# Abilitazione: Settings → Security → Dependabot alerts → Enable
# Nessun file di configurazione necessario per gli alerts base
```

Come funziona:
1. GitHub analizza il dependency graph del repository.
2. Confronta le dipendenze con il GitHub Advisory Database.
3. Crea un alert per ogni vulnerabilità trovata.
4. Notifica i maintainer via email/web.

### Dependabot Security Updates

PR automatiche per aggiornare dipendenze con vulnerabilità:

```yaml
# Abilitazione: Settings → Security → Dependabot security updates → Enable
# Crea PR automatiche per aggiornare le dipendenze vulnerabili
```

### Dependabot Version Updates

PR automatiche per mantenere le dipendenze aggiornate (anche senza vulnerabilità):

```yaml
# .github/dependabot.yml
version: 2
updates:
  # npm
  - package-ecosystem: npm
    directory: "/"
    schedule:
      interval: weekly
      day: monday
      time: "09:00"
      timezone: "Europe/Rome"
    open-pull-requests-limit: 10
    reviewers:
      - "myorg/security-team"
    labels:
      - "dependencies"
      - "security"
    commit-message:
      prefix: "chore(deps):"
    ignore:
      - dependency-name: "lodash"
        update-types: ["version-update:semver-patch"]
    groups:
      dev-dependencies:
        dependency-type: "development"
        update-types:
          - "minor"
          - "patch"
      production-minor:
        dependency-type: "production"
        update-types:
          - "minor"
          - "patch"

  # Docker
  - package-ecosystem: docker
    directory: "/"
    schedule:
      interval: weekly
    labels:
      - "docker"

  # GitHub Actions
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
    labels:
      - "ci"

  # pip
  - package-ecosystem: pip
    directory: "/"
    schedule:
      interval: weekly

  # Go modules
  - package-ecosystem: gomod
    directory: "/"
    schedule:
      interval: weekly

  # Terraform
  - package-ecosystem: terraform
    directory: "/infra"
    schedule:
      interval: monthly
```

### Grouping delle PR Dependabot

```yaml
# Raggruppare per ridurre il numero di PR
groups:
  # Un'unica PR per tutte le patch dev
  dev-patch:
    dependency-type: "development"
    update-types: ["patch"]

  # Un'unica PR per minor production
  prod-minor:
    dependency-type: "production"
    update-types: ["minor"]
    exclude-patterns:
      - "aws-*"  # Escludi AWS SDK (trattamento separato)

  # AWS SDK separato
  aws-sdk:
    patterns:
      - "aws-*"
      - "@aws-sdk/*"
```

### PR multi-ecosistema (2025)

A partire da luglio 2025, Dependabot supporta la creazione di un'unica PR che consolida aggiornamenti da più ecosistemi. Questo riduce drasticamente il rumore per progetti che combinano Docker, Terraform, pip e altri tool:

```yaml
# .github/dependabot.yml — multi-ecosystem grouping
version: 2
updates:
  - package-ecosystem: npm
    directory: "/"
    schedule:
      interval: weekly
    groups:
      infrastructure:
        patterns:
          - "@aws-sdk/*"
          - "aws-*"
        update-types: ["minor", "patch"]
      testing:
        patterns:
          - "jest*"
          - "@testing-library/*"
          - "vitest"
        update-types: ["minor", "patch"]
      linting:
        patterns:
          - "eslint*"
          - "prettier"
          - "@typescript-eslint/*"

  - package-ecosystem: docker
    directory: "/"
    schedule:
      interval: weekly
    groups:
      base-images:
        patterns:
          - "node"
          - "alpine"
          - "ubuntu"

  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
    groups:
      all-actions:
        patterns:
          - "*"
        update-types: ["minor", "patch"]
```

### Auto-merge sicuro con periodo di grazia

Una best practice emersa nel 2025 è quella di ritardare l'auto-merge per dare tempo alla community di individuare eventuali compromissioni. Un pacchetto maligno viene tipicamente scoperto e rimosso dal registry entro 24-72 ore:

```yaml
name: Dependabot Auto-merge con Grace Period
on:
  pull_request:
    types: [opened, synchronize]

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

      # Auto-merge solo patch, solo dopo che tutti i check passano
      - name: Auto-merge patch updates
        if: steps.metadata.outputs.update-type == 'version-update:semver-patch'
        run: |
          # Attendere 3 giorni prima di mergeare (grace period)
          PR_CREATED=$(gh pr view "$PR" --json createdAt -q '.createdAt')
          PR_AGE_HOURS=$(( ($(date +%s) - $(date -d "$PR_CREATED" +%s)) / 3600 ))

          if [ "$PR_AGE_HOURS" -lt 72 ]; then
            echo "PR troppo recente ($PR_AGE_HOURS ore). Grace period: 72 ore."
            exit 0
          fi

          gh pr merge "$PR" --auto --squash
        env:
          PR: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      # Minor production: richiede review manuale
      - name: Label minor production updates
        if: |
          steps.metadata.outputs.update-type == 'version-update:semver-minor' &&
          steps.metadata.outputs.dependency-type == 'direct:production'
        run: |
          gh pr edit "$PR" --add-label "needs-review"
        env:
          PR: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Dependabot security updates vs version updates

È importante distinguere i due meccanismi:

| Caratteristica | Security Updates | Version Updates |
|---|---|---|
| **Trigger** | CVE nel GitHub Advisory Database | Nuova versione disponibile |
| **Configurazione** | Settings → Security | `.github/dependabot.yml` |
| **Frequenza** | Immediata al rilevamento | Schedulata (daily/weekly/monthly) |
| **Scope** | Solo dipendenze con CVE | Tutte le dipendenze |
| **Auto-enable** | Sì (per repo pubblici) | No (richiede file config) |
| **Raggruppamento** | No | Sì (con groups) |
| **Priorità** | Alta — risolvere subito | Media — a discrezione del team |

---

## Dependency review action

### Scopo

Blocca PR che introducono dipendenze con vulnerabilità note o licenze vietate:

```yaml
name: Dependency Review
on:
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  dependency-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: moderate
          deny-licenses: GPL-3.0, AGPL-3.0
          comment-summary-in-pr: always
          allow-ghsas: GHSA-xxxx-yyyy-zzzz  # falsi positivi noti
```

### Configurazione avanzata

```yaml
- uses: actions/dependency-review-action@v4
  with:
    # Severità minima per fallire
    fail-on-severity: moderate  # low, moderate, high, critical

    # Licenze vietate
    deny-licenses: GPL-3.0, AGPL-3.0, SSPL-1.0

    # Oppure: lista di licenze permesse (allowlist)
    allow-licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC

    # Ignorare vulnerabilità specifiche
    allow-ghsas: GHSA-xxxx-yyyy-zzzz, GHSA-aaaa-bbbb-cccc

    # Commento nella PR
    comment-summary-in-pr: always  # always, on-failure, never

    # Fallire anche per scope specifici
    fail-on-scopes: runtime  # runtime, development, unknown

    # File di configurazione esterna
    config-file: .github/dependency-review-config.yml

    # Warn invece di fail per licenze
    warn-only: false

    # Retry su errori transitori
    retry-on-snapshot-warnings: true
    retry-on-snapshot-warnings-timeout: 120
```

### Config file esterno

```yaml
# .github/dependency-review-config.yml
fail-on-severity: moderate
deny-licenses:
  - GPL-3.0
  - AGPL-3.0
  - SSPL-1.0
allow-ghsas:
  - GHSA-xxxx-yyyy-zzzz
fail-on-scopes:
  - runtime
```

---

## npm provenance e Trusted Publishing

### Cos'è npm provenance

npm provenance lega un pacchetto pubblicato al suo source repository e al workflow di build, usando SLSA provenance:

```text
npm package (v1.2.3)
  ├── Source: github.com/myorg/mypackage @ commit abc123
  ├── Build: GitHub Actions workflow build.yml
  ├── Signed: Sigstore (OIDC keyless)
  └── Verified: ✅ npmjs.com mostra badge "Provenance"
```

### Workflow per npm provenance

```yaml
name: Publish with Provenance
on:
  release:
    types: [created]

permissions:
  contents: read
  id-token: write  # Necessario per OIDC → Sigstore

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: https://registry.npmjs.org

      - run: npm ci

      - run: npm publish --provenance --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Verificare npm provenance

```bash
# Vedere la provenance di un pacchetto
npm audit signatures

# Dettagli di un pacchetto specifico
npm view <package-name> --json | jq '.dist.attestations'

# Sul sito npmjs.com: cercare il badge "Provenance" nella pagina del pacchetto
```

### Requisiti

| Requisito | Dettaglio |
|---|---|
| npm versione | >= 9.5.0 |
| Node.js | >= 18 |
| Registry | npmjs.com (non registry privati) |
| CI | GitHub Actions (o altro provider OIDC supportato) |
| Permissions | `id-token: write` |

### Trusted Publishing (luglio 2025)

Trusted Publishing è il gold standard per la pubblicazione npm dal 2025. Elimina completamente la necessità di gestire token API npm nei sistemi CI/CD. Invece di usare un secret `NPM_TOKEN`, il CI/CD provider (GitHub Actions, GitLab CI/CD) attesta direttamente l'identità del publisher, e npm verifica questa attestazione.

```text
Prima di Trusted Publishing      Con Trusted Publishing
============================     ========================

  Developer                       Developer
      │                               │
      ▼                               ▼
  GitHub Actions                  GitHub Actions
      │                               │
      │ usa NPM_TOKEN               │ attesta identità via OIDC
      │ (secret da gestire)          │ (nessun token)
      ▼                               ▼
  npm registry                    npm registry
      │                               │
      │ verifica token               │ verifica attestazione OIDC
      ▼                               ▼
  Pacchetto pubblicato            Pacchetto pubblicato
                                  + provenance automatica
```

#### Configurazione Trusted Publishing

1. Andare su npmjs.com → Package Settings → Publishing access.
2. Aggiungere un "Trusted Publisher" specificando:
   - Repository GitHub (es. `myorg/mypackage`)
   - Workflow file (es. `.github/workflows/publish.yml`)
   - Environment GitHub (es. `npm-publish`, opzionale ma raccomandato)

```yaml
name: Publish con Trusted Publishing
on:
  release:
    types: [created]

permissions:
  contents: read
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: npm-publish  # Environment configurato su npmjs.com
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          registry-url: https://registry.npmjs.org

      - run: npm ci

      - run: npm publish --provenance --access public
        # NESSUN NODE_AUTH_TOKEN necessario!
        # L'identità OIDC del workflow è sufficiente
```

#### Vantaggi del Trusted Publishing

| Aspetto | Token tradizionale | Trusted Publishing |
|---|---|---|
| Gestione secrets | Manuale (rotazione, storage) | Nessuno |
| Rischio di leak | Token nei log, compromissione CI | Impossibile — nessun token |
| Provenance | Opt-in (`--provenance`) | Automatica |
| Ambito di pubblicazione | Chiunque abbia il token | Solo il workflow specifico |
| Revoca | Manuale | Automatica (legata al repo) |
| Audit trail | Limitato | Completo (OIDC + Rekor) |

### Deprecazione dei Legacy Token npm

Alla fine del 2025, npm ha annunciato il sunset dei Legacy Token a favore dei Granular Access Token. Le differenze:

- **Legacy Token:** accesso completo a tutti i pacchetti dell'account, nessuna scadenza, nessun scope granulare.
- **Granular Access Token:** scope limitato a pacchetti specifici, scadenza configurabile, permessi read/publish separati, restrizione per IP.

```bash
# Creare un granular access token via CLI
npm token create --type granular \
  --packages "mypackage" \
  --permissions "read-write" \
  --expires "90d" \
  --cidr "0.0.0.0/0"
```

### Attacchi alla provenance — limiti e contromisure

La provenance SLSA non è una panacea. Ricercatori di sicurezza hanno dimostrato scenari in cui la provenance firmata può essere aggirata o manipolata.

#### Mini Shai-Hulud (2024)

L'attacco "Mini Shai-Hulud", presentato da Adnan Khan alla DEF CON 32 (agosto 2024), ha dimostrato come un attaccante possa hijackare il token OIDC di un workflow GitHub Actions per pubblicare un pacchetto npm con provenance SLSA L3 valida — ma contenente codice malevolo.

**Vettore di attacco:**

```text
1. Attaccante identifica un workflow con permesso id-token: write
   in un repository target
2. Attaccante trova un injection point (es. issue title non sanitizzato
   usato in un `run:` step)
3. Attaccante esegue codice arbitrario nel contesto del workflow
4. Il codice malevolo usa il token OIDC del runner per firmare
   un artefatto con provenance valida
5. L'artefatto risulta "verificato" — provenance legata al repo legittimo
```

Questo attacco è particolarmente insidioso perché la provenance generata è _tecnicamente corretta_: il pacchetto è stato effettivamente buildato da quel repository su GitHub Actions. La provenance non mente — è il codice nel repository che è stato temporaneamente compromesso tramite injection.

#### s1ngularity (2025)

L'attacco "s1ngularity", presentato da Yaron Avital di Legit Security al SupplyChainSecurityCon 2025, ha dimostrato un bypass diverso: abusare della re-usable workflow trust boundary in SLSA L3. In questo scenario, un attaccante con accesso a un repository che _chiama_ un reusable workflow SLSA generator può manipolare i parametri passati al workflow, alterando l'artefatto prodotto mantenendo la provenance L3 del generator.

**Contromisure raccomandate:**

| Contromisura | Efficacia | Complessità |
|---|---|---|
| Sanitizzare tutti gli input nei workflow (`run:` steps) | Previene injection | Bassa |
| Usare `if: github.event_name == 'push'` per limitare `id-token: write` | Riduce la superficie di attacco | Bassa |
| Abilitare `step-security/harden-runner` in modalità audit | Rileva chiamate di rete anomale | Media |
| Usare Kyverno/OPA per verificare che il workflow ref nella provenance sia in una allowlist | Previene provenance da workflow non autorizzati | Media |
| Defense in depth: combinare provenance + SBOM + vulnerability scan + runtime monitoring | Non affidarsi a un singolo controllo | Alta |

L'approccio di difesa in profondità (defense-in-depth) è il più robusto: nessun singolo meccanismo di verifica è sufficiente. La provenance SLSA deve essere un _layer_ nella strategia di sicurezza, non l'unico.

### PyPI Trusted Publishing e PEP 740

L'ecosistema Python ha adottato il modello di Trusted Publishing in modo indipendente da npm, con un'implementazione che va oltre la semplice provenance e introduce **attestazioni digitali native** per ogni pacchetto pubblicato.

#### Trusted Publishing per PyPI

Configurato dal 2023, il Trusted Publishing di PyPI funziona in modo analogo a quello di npm: il repository PyPI accetta un token OIDC da GitHub Actions come credenziale di pubblicazione, eliminando la necessità di API token statici.

```yaml
name: Publish to PyPI
on:
  release:
    types: [published]

permissions:
  id-token: write  # Obbligatorio per OIDC
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/mio-pacchetto
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build tools
        run: pip install build

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # Nessun password o token necessario!
        # L'identità OIDC del workflow è sufficiente
```

**Prerequisito:** Il maintainer deve configurare il "Trusted Publisher" nella pagina del progetto su PyPI, specificando il repository GitHub, il workflow file name e opzionalmente l'environment name.

#### PEP 740 — Digital Attestations per PyPI

**PEP 740** ("Index support for digital attestations"), approvato nel 2024 e implementato progressivamente nel 2025, introduce attestazioni digitali firmate come oggetto di prima classe nel Python Package Index. A differenza di npm, dove la provenance è un campo aggiuntivo nel metadata, PEP 740 definisce un formato strutturato che permette a qualsiasi tool di generare e verificare attestazioni.

**Struttura di un'attestazione PEP 740:**

```json
{
  "version": 1,
  "verification_material": {
    "certificate": "<PEM-encoded Fulcio certificate>",
    "transparency_entries": [
      {
        "logIndex": 98765432,
        "logId": "...",
        "integratedTime": 1732000000,
        "inclusionProof": { "..." }
      }
    ]
  },
  "envelope": {
    "statement": {
      "_type": "https://in-toto.io/Statement/v1",
      "subject": [
        {
          "name": "mio-pacchetto-1.0.0.tar.gz",
          "digest": {"sha256": "abc123..."}
        }
      ],
      "predicateType": "https://docs.pypi.org/attestations/publish/v1",
      "predicate": {
        "transparency": "https://rekor.sigstore.dev"
      }
    },
    "signature": "<base64 DSSE signature>"
  }
}
```

**Generazione automatica delle attestazioni (v1.11.0+):**

A partire dalla versione v1.11.0 di `pypa/gh-action-pypi-publish` (rilasciata nel 2025), le attestazioni PEP 740 sono generate **automaticamente** durante la pubblicazione tramite Trusted Publishing. Non è necessaria alcuna configurazione aggiuntiva — il workflow sopra produce attestazioni per default.

```bash
# Verificare le attestazioni di un pacchetto PyPI
pip download mio-pacchetto==1.0.0 --no-deps
python -m pypi_attestations verify mio-pacchetto-1.0.0.tar.gz \
  --identity "workflow@github.com" \
  --issuer "https://token.actions.githubusercontent.com"

# Oppure tramite l'API PyPI
curl -s https://pypi.org/simple/mio-pacchetto/1.0.0/ \
  -H "Accept: application/vnd.pypi.simple.v1+json" | \
  jq '.files[].provenance'
```

**Confronto npm provenance vs PyPI attestations:**

| Aspetto | npm provenance | PyPI PEP 740 |
|---|---|---|
| Formato | Sigstore bundle proprietario | in-toto Statement + DSSE (standard) |
| Generazione automatica | `--provenance` flag al `npm publish` | Automatica con Trusted Publishing (v1.11.0+) |
| Predicate type | `https://slsa.dev/provenance/v1` | `https://docs.pypi.org/attestations/publish/v1` |
| Verifica client-side | `npm audit signatures` | `pip` (supporto in sviluppo), tool dedicati |
| Adozione (maggio 2026) | ~28% dei top-1000 pacchetti | ~15% dei top-1000 pacchetti |
| Retrocompatibilità | Trasparente — nessun cambiamento per i consumatori | Trasparente — attestazioni opzionali nel metadata |

**Stato dell'ecosistema Python (maggio 2026):** Oltre 45.000 progetti su PyPI hanno configurato un Trusted Publisher, e circa 12.000 pubblicano con attestazioni PEP 740 attive. L'adozione è in crescita rapida dopo che pip ha iniziato a mostrare warning per i pacchetti privi di attestazioni (a partire da pip 25.1, marzo 2026). Il Python Packaging Authority (PyPA) ha annunciato l'intenzione di rendere le attestazioni obbligatorie per nuovi progetti entro il 2027.

---

## Container signing e attestation

### Firmare container con cosign (keyless)

```yaml
name: Build, Push, Sign Container
on:
  push:
    branches: [main]

permissions:
  contents: read
  packages: write
  id-token: write

jobs:
  container:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: sigstore/cosign-installer@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/myorg/myimage
          tags: |
            type=sha
            type=semver,pattern={{version}}
            type=ref,event=branch

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

      - name: Sign the image
        run: |
          cosign sign --yes \
            ghcr.io/myorg/myimage@${{ steps.build.outputs.digest }}

      - name: Verify signature
        run: |
          cosign verify \
            --certificate-identity "https://github.com/myorg/myrepo/.github/workflows/build.yml@refs/heads/main" \
            --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
            ghcr.io/myorg/myimage@${{ steps.build.outputs.digest }}
```

### Attestazione con predicati multipli

```yaml
      # SBOM attestation
      - name: Generate and attest SBOM
        run: |
          syft ghcr.io/myorg/myimage@${{ steps.build.outputs.digest }} \
            -o spdx-json > sbom.spdx.json

          cosign attest --yes \
            --predicate sbom.spdx.json \
            --type spdxjson \
            ghcr.io/myorg/myimage@${{ steps.build.outputs.digest }}

      # Vulnerability scan attestation
      - name: Scan and attest vulnerabilities
        run: |
          trivy image --format cosign-vuln \
            ghcr.io/myorg/myimage@${{ steps.build.outputs.digest }} \
            > vuln-report.json

          cosign attest --yes \
            --predicate vuln-report.json \
            --type vuln \
            ghcr.io/myorg/myimage@${{ steps.build.outputs.digest }}
```

### Kubernetes admission control con cosign

```yaml
# Kyverno policy per verificare firma cosign
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-cosign-signature
spec:
  validationFailureAction: Enforce
  background: false
  rules:
    - name: check-image-signature
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "ghcr.io/myorg/*"
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/myorg/*/.github/workflows/*@refs/heads/main"
                    issuer: "https://token.actions.githubusercontent.com"
                    rekor:
                      url: https://rekor.sigstore.dev
```

---

## GitHub Artifact Attestations

### Panoramica

GitHub Artifact Attestations (GA dal 2024) integra nativamente la generazione e la verifica di attestazioni di build:

```yaml
# Generare attestazione
- uses: actions/attest-build-provenance@v1
  with:
    subject-name: ghcr.io/myorg/myimage
    subject-digest: ${{ steps.build.outputs.digest }}
    push-to-registry: true

# Verificare attestazione
# CLI:
gh attestation verify oci://ghcr.io/myorg/myimage:tag --owner myorg
```

### Workflow completo per container

```yaml
name: Build with Attestation
on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read
  attestations: write
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/myorg/myimage:${{ github.sha }}

      - name: Attest build provenance
        uses: actions/attest-build-provenance@v1
        with:
          subject-name: ghcr.io/myorg/myimage
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true

      - name: Attest SBOM
        uses: actions/attest-sbom@v1
        with:
          subject-name: ghcr.io/myorg/myimage
          subject-digest: ${{ steps.build.outputs.digest }}
          sbom-path: sbom.spdx.json
          push-to-registry: true
```

### Workflow per binary artifacts

```yaml
name: Build Binary with Attestation
on:
  release:
    types: [created]

permissions:
  id-token: write
  contents: write
  attestations: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: |
          go build -o my-binary ./cmd/
          sha256sum my-binary

      - name: Attest binary
        uses: actions/attest-build-provenance@v1
        with:
          subject-path: my-binary

      - name: Upload to release
        run: |
          gh release upload ${{ github.event.release.tag_name }} my-binary
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Verificare attestazioni

```bash
# Verificare container image
gh attestation verify oci://ghcr.io/myorg/myimage:tag --owner myorg

# Verificare file locale
gh attestation verify my-binary --owner myorg

# Verificare con output dettagliato
gh attestation verify oci://ghcr.io/myorg/myimage:tag \
  --owner myorg \
  --format json | jq .

# Verificare contro un repository specifico
gh attestation verify my-binary \
  --repo myorg/myrepo

# Listare attestazioni
gh attestation list --owner myorg --artifact-name myimage
```

---

## OpenSSF Scorecard

### Cos'è Scorecard

[Scorecard](https://securityscorecards.dev/) è uno strumento OpenSSF che valuta automaticamente le pratiche di sicurezza di un progetto open source:

| Check | Cosa valuta |
|---|---|
| **Binary-Artifacts** | Binari committati nel repo |
| **Branch-Protection** | Regole di protezione dei branch |
| **CI-Tests** | Test automatici nei workflow |
| **CII-Best-Practices** | Badge CII Best Practices |
| **Code-Review** | Review prima del merge |
| **Contributors** | Diversità dei contributor |
| **Dangerous-Workflow** | Pattern pericolosi nei workflow |
| **Dependency-Update-Tool** | Dependabot o Renovate configurato |
| **Fuzzing** | Fuzzing integrato |
| **License** | Licenza presente |
| **Maintained** | Attività recente |
| **Packaging** | Build da fonte (non binari) |
| **Pinned-Dependencies** | Hash pinning per azioni e dipendenze |
| **SAST** | Static analysis configurata |
| **Security-Policy** | SECURITY.md presente |
| **Signed-Releases** | Release firmate |
| **Token-Permissions** | Permessi minimali nei workflow |
| **Vulnerabilities** | Vulnerabilità note non risolte |

### Workflow Scorecard

```yaml
name: OpenSSF Scorecard
on:
  branch_protection_rule:
  schedule:
    - cron: "0 6 * * 1"  # Ogni lunedì alle 06:00
  push:
    branches: [main]

permissions: read-all

jobs:
  analysis:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false

      - name: Run Scorecard
        uses: ossf/scorecard-action@v2.4.0
        with:
          results_file: results.sarif
          results_format: sarif
          publish_results: true

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

### Badge Scorecard

```markdown
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/myorg/myrepo/badge)](https://securityscorecards.dev/viewer/?uri=github.com/myorg/myrepo)
```

---

## Hardening dei workflow GitHub Actions

### Il problema della sicurezza dei workflow

I workflow GitHub Actions sono essi stessi parte della supply chain. Un workflow compromesso può esfiltrare secrets, modificare artefatti o iniettare codice maligno nella pipeline. L'attacco a `tj-actions/changed-files` nel marzo 2025 ha dimostrato che le azioni di terze parti sono un vettore critico.

### Pinning delle azioni per hash

L'unico modo per usare un'azione come release immutabile è il pin tramite SHA completo del commit:

```yaml
# INSICURO: tag mutabile — l'attaccante può riscrivere il tag
- uses: actions/checkout@v4
- uses: docker/build-push-action@v5

# SICURO: SHA immutabile — commento per leggibilità umana
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
- uses: docker/build-push-action@4a13e500e55cf31b7a5d59a38ab2040ab0f42f56 # v5.1.0
```

Per automatizzare il pinning, usare StepSecurity o Renovate con hash pinning:

```bash
# StepSecurity CLI: pin automatico di tutte le azioni nel repo
npx step-security/secure-repo \
  --type pin-actions \
  --repo myorg/myrepo
```

### Permessi minimali (least privilege)

Ogni workflow deve dichiarare esplicitamente i permessi necessari, sia a livello di workflow che di job:

```yaml
# A livello di workflow: default restrittivo
permissions: read-all  # o meglio: permessi specifici per job

jobs:
  build:
    permissions:
      contents: read        # Checkout del codice
      packages: write       # Push al registry
      id-token: write       # OIDC per cosign/attestazioni
      # NIENTE attestations: write se non serve
      # NIENTE pull-requests: write se non serve
    runs-on: ubuntu-latest
    steps: ...

  lint:
    permissions:
      contents: read        # Solo lettura
    runs-on: ubuntu-latest
    steps: ...
```

**Regola d'oro:** se un permesso non è esplicitamente necessario per il job, non dichiararlo. GitHub imposta `GITHUB_TOKEN` con solo i permessi dichiarati.

### Harden-Runner — EDR per GitHub Actions

[Harden-Runner](https://github.com/step-security/harden-runner) di StepSecurity funziona come un EDR (Endpoint Detection and Response) per i runner CI/CD. Monitora:

- **Network egress:** ogni connessione in uscita dal runner.
- **File integrity:** modifiche a file critici durante la build.
- **Process activity:** processi avviati durante l'esecuzione.

```yaml
name: Build con Harden-Runner
on:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Harden Runner
        uses: step-security/harden-runner@17d0e2bd7d51742c71671bd19fa12bdc9d40a3d6 # v2.8.1
        with:
          # Modalità audit: registra tutte le connessioni
          egress-policy: audit

          # Modalità block: permette solo connessioni autorizzate
          # egress-policy: block
          # allowed-endpoints: >
          #   github.com:443
          #   registry.npmjs.org:443
          #   ghcr.io:443
          #   fulcio.sigstore.dev:443
          #   rekor.sigstore.dev:443
          #   tuf-repo-cdn.sigstore.dev:443

      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1

      - name: Build
        run: npm ci && npm run build
```

#### Passaggio da audit a block

Il processo raccomandato:

1. **Fase 1 — Audit:** attivare `egress-policy: audit` per almeno una settimana. Harden-Runner costruisce un baseline delle connessioni legittime.
2. **Fase 2 — Analisi:** verificare il baseline nella dashboard StepSecurity. Identificare le connessioni necessarie.
3. **Fase 3 — Block:** passare a `egress-policy: block` con la lista di `allowed-endpoints` derivata dal baseline.

```yaml
# Esempio di allowed-endpoints per un progetto Node.js + Docker
allowed-endpoints: >
  github.com:443
  api.github.com:443
  registry.npmjs.org:443
  ghcr.io:443
  *.actions.githubusercontent.com:443
  fulcio.sigstore.dev:443
  rekor.sigstore.dev:443
  tuf-repo-cdn.sigstore.dev:443
  objects.githubusercontent.com:443
  production.cloudflare.docker.com:443
```

### Protezione dei secrets nei workflow

```yaml
# Pattern: usare GitHub Environments per limitare l'accesso ai secrets
jobs:
  build:
    runs-on: ubuntu-latest
    # Nessun environment — nessun accesso a secrets di produzione
    steps:
      - run: npm ci && npm test

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production  # Solo questo job accede ai secrets di produzione
    steps:
      - run: ./deploy.sh
        env:
          DEPLOY_KEY: ${{ secrets.PRODUCTION_DEPLOY_KEY }}
```

### Pattern pericolosi da evitare

```yaml
# PERICOLOSO: pull_request_target con checkout del PR
# Un attaccante può aprire una PR con codice maligno che viene eseguito
# con i permessi del branch target
on:
  pull_request_target:
jobs:
  build:
    steps:
      # MAI fare checkout della PR head con pull_request_target
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # PERICOLOSO
      - run: npm ci && npm test  # Esegue codice dell'attaccante con GITHUB_TOKEN del repo

# SICURO: usare pull_request (non _target) per codice non fidato
on:
  pull_request:
jobs:
  build:
    steps:
      - uses: actions/checkout@v4  # Checkout della PR merge ref — sicuro
      - run: npm ci && npm test
```

### GitHub Actions 2026 Security Roadmap

GitHub ha pubblicato la roadmap di sicurezza per Actions nel 2026, con funzionalità chiave:

| Feature | Stato | Descrizione |
|---|---|---|
| Workflow dependency locking | GA | Lock delle dipendenze dei workflow per prevenire supply chain attacks |
| Native egress firewall | GA (aprile 2026) | Firewall Layer 7 nativo per controllare il traffico in uscita dai runner |
| Scoped secrets | GA | Secrets con scope granulare (per job, per step) |
| Policy-driven execution | Preview | Governance centralizzata su quali azioni possono essere eseguite |
| Actions Data Stream | Preview | Streaming di audit log in tempo reale |
| OIDC custom property claims | GA (aprile 2026) | Claims personalizzati nei token OIDC per policy di verifica più granulari |

---

## Regolamentazione e compliance

### Panoramica normativa

Il panorama normativo della supply chain software si è consolidato tra il 2024 e il 2026. Due regolamenti principali guidano i requisiti:

```text
┌─────────────────────────────────────────────────────────────┐
│  Normativa Supply Chain Software (2024-2027)                │
│                                                             │
│  ┌─────────────────────┐    ┌────────────────────────────┐  │
│  │ USA                 │    │ Unione Europea             │  │
│  │                     │    │                            │  │
│  │ Executive Order     │    │ Cyber Resilience Act       │  │
│  │ 14028 (2021)        │    │ (CRA, 2024)                │  │
│  │                     │    │                            │  │
│  │ CISA SBOM Minimum   │    │ SBOM obbligatorio per      │  │
│  │ Elements (rev 2025) │    │ "prodotti con elementi     │  │
│  │                     │    │  digitali"                 │  │
│  │ NIST SSDF           │    │                            │  │
│  │ (SP 800-218)        │    │ Sanzioni: fino a 15M EUR   │  │
│  │                     │    │ o 2,5% fatturato globale   │  │
│  └─────────────────────┘    └────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────┐    ┌────────────────────────────┐  │
│  │ FDA (Dispositivi    │    │ NIS2 Directive (UE)        │  │
│  │  medici)            │    │                            │  │
│  │                     │    │ Obbligo di supply chain    │  │
│  │ SBOM obbligatorio   │    │ risk management per        │  │
│  │ + VEX da marzo 2026 │    │ operatori essenziali       │  │
│  └─────────────────────┘    └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### EU Cyber Resilience Act (CRA) — dettagli

Il CRA è entrato in vigore il 10 dicembre 2024 ed è il regolamento più impattante per la supply chain software in Europa.

#### Timeline di implementazione

| Data | Milestone |
|---|---|
| 10 dicembre 2024 | CRA entra in vigore |
| 11 settembre 2026 | Obbligo di reporting vulnerabilità attivamente sfruttate |
| metà 2026 (stimato) | Standard orizzontale per schema SBOM |
| 11 dicembre 2027 | Obbligo pieno di conformità |

#### Requisiti SBOM del CRA

1. **SBOM obbligatorio** per ogni "prodotto con elementi digitali" venduto nell'UE.
2. **Formato machine-readable** — SPDX o CycloneDX (il CRA non specifica un formato esatto, ma richiede "formato comunemente usato e machine-readable").
3. **Almeno le dipendenze top-level** devono essere documentate.
4. **Aggiornamento continuo** — l'SBOM deve essere mantenuto aggiornato per tutta la vita del prodotto.
5. **Disponibilità su richiesta** — i produttori devono fornire l'SBOM alle autorità di sorveglianza su "richiesta motivata".
6. **Retention di 10 anni** — la documentazione di sicurezza, incluso l'SBOM, deve essere conservata per 10 anni dopo l'immissione sul mercato.

#### Impatto pratico

```yaml
# Workflow CI che soddisfa i requisiti CRA base
name: CRA Compliance Pipeline
on:
  push:
    tags: ['v*']  # Solo su release

permissions:
  contents: read
  id-token: write
  attestations: write
  packages: write

jobs:
  build-and-comply:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: npm ci && npm run build

      # 1. SBOM obbligatorio (CRA Art. 13)
      - name: Generate SBOM (SPDX per compliance)
        run: |
          syft packages dir:. \
            -o spdx-json \
            --source-name "${{ github.event.repository.name }}" \
            --source-version "${{ github.ref_name }}" \
            > sbom.spdx.json

      # 2. SBOM in formato security (CycloneDX per DevSecOps)
      - name: Generate SBOM (CycloneDX per security)
        run: |
          syft packages dir:. -o cyclonedx-json > sbom.cdx.json

      # 3. Vulnerability scan (CRA Art. 11 — gestione vulnerabilità)
      - name: Scan vulnerabilities
        run: |
          grype sbom:sbom.cdx.json \
            -o json \
            --fail-on critical \
            > vuln-report.json

      # 4. License check (due diligence componenti terze parti)
      - name: Check licenses
        run: |
          syft packages dir:. -o spdx-json | \
            jq '[.packages[].licenseConcluded] | unique' > licenses.json

          # Verificare che non ci siano licenze incompatibili
          BANNED=$(jq '[.[] | select(. == "GPL-3.0-only" or . == "AGPL-3.0-only")] | length' licenses.json)
          if [ "$BANNED" -gt 0 ]; then
            echo "ERRORE: Licenze incompatibili trovate"
            exit 1
          fi

      # 5. Attestazione provenance (tracciabilità build)
      - name: Attest build provenance
        uses: actions/attest-build-provenance@v1
        with:
          subject-path: ./dist/

      # 6. Archiviazione SBOM (retention 10 anni)
      - name: Archive SBOM
        uses: actions/upload-artifact@v4
        with:
          name: cra-compliance-${{ github.ref_name }}
          path: |
            sbom.spdx.json
            sbom.cdx.json
            vuln-report.json
            licenses.json
          retention-days: 3650  # ~10 anni
```

### Executive Order 14028 (USA)

L'EO 14028, firmato nel 2021, richiede SBOM e provenance per software venduto al governo federale USA. I requisiti sono stati raffinati nel 2025 attraverso le revisioni CISA dei "Minimum Elements" per SBOM.

**Requisiti chiave per venditori al governo USA:**

1. SBOM per ogni versione del software.
2. SBOM in formato SPDX o CycloneDX.
3. Provenance del software (chi ha buildato, da quale source).
4. Attestazione di conformità alle pratiche di sviluppo sicuro (NIST SSDF).
5. Notifica tempestiva di vulnerabilità.

### NIST Secure Software Development Framework (SSDF)

Il NIST SP 800-218 (SSDF) definisce le pratiche di sviluppo sicuro che i venditori devono attestare:

| Pratica | Descrizione | Mappatura SLSA/Sigstore |
|---|---|---|
| PO.1 | Definire requisiti di sicurezza | Policy-as-code |
| PS.1 | Proteggere il software dall'accesso non autorizzato | Branch protection, commit signing |
| PS.2 | Proteggere i componenti software | SBOM, dependency review |
| PS.3 | Proteggere il processo di build | SLSA L2+, provenance |
| PW.1 | Progettare software sicuro | Threat modeling |
| PW.6 | Verificare il software | SAST, DAST, fuzzing |
| PW.7 | Proteggere il codice da modifiche non autorizzate | Commit signing, code review |
| PW.8 | Test per vulnerabilità | Trivy, Grype, CodeQL |
| PW.9 | Correggere le vulnerabilità | Dependabot, patch management |
| RV.1 | Identificare e confermare le vulnerabilità | VEX, vulnerability triage |

---

## Architettura di verifica end-to-end

### Modello di fiducia a strati

Un'architettura di supply chain security completa opera su quattro strati di verifica, ciascuno con i propri meccanismi crittografici e policy:

```text
┌─────────────────────────────────────────────────────────────────┐
│  Strato 4: DEPLOY-TIME VERIFICATION                            │
│  • Admission controller (Kyverno, OPA, Policy Controller)       │
│  • Verifica firme + attestazioni prima del deploy               │
│  • Policy: "solo immagini firmate da workflow specifici"         │
├─────────────────────────────────────────────────────────────────┤
│  Strato 3: REGISTRY-TIME VERIFICATION                           │
│  • Firme cosign nel registry OCI                                │
│  • Attestazioni (provenance, SBOM, VEX) allegate alle immagini  │
│  • GitHub Artifact Attestations come data store                  │
├─────────────────────────────────────────────────────────────────┤
│  Strato 2: BUILD-TIME PROVENANCE                                │
│  • SLSA L2/L3 provenance generata dal builder                   │
│  • In-toto statement firmato via Sigstore                       │
│  • Rekor transparency log come timestamping                     │
├─────────────────────────────────────────────────────────────────┤
│  Strato 1: SOURCE INTEGRITY                                    │
│  • Commit signing (GPG, SSH, Sigstore gitsign)                  │
│  • Branch protection rules                                      │
│  • Code review enforcement                                      │
│  • Dependency review action                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Implementazione completa multi-strato

#### Strato 1 — Source integrity

```yaml
# .github/workflows/source-integrity.yml
name: Source Integrity Checks
on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

jobs:
  commit-signing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Verify commit signatures
        run: |
          # Verificare che tutti i commit della PR siano firmati
          UNSIGNED=$(git log --format='%H %GS' origin/main..HEAD | grep -c 'N$' || true)
          if [ "$UNSIGNED" -gt 0 ]; then
            echo "ATTENZIONE: $UNSIGNED commit non firmati nella PR"
            # In modalità strict: exit 1
          fi

  dependency-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: moderate
          deny-licenses: GPL-3.0, AGPL-3.0, SSPL-1.0
          comment-summary-in-pr: always

  secret-scanning:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Scan for secrets
        run: |
          # Usare trufflehog per scanning locale
          docker run --rm -v "$PWD:/repo" \
            trufflesecurity/trufflehog:latest \
            filesystem /repo \
            --fail \
            --only-verified
```

#### Strato 2 — Build-time provenance

```yaml
# .github/workflows/build-provenance.yml
name: Build with SLSA Provenance
on:
  push:
    branches: [main]
    tags: ['v*']

permissions:
  contents: read
  packages: write
  id-token: write
  attestations: write

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digest: ${{ steps.build.outputs.digest }}
      image: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4

      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=sha
            type=semver,pattern={{version}}
            type=ref,event=branch

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          provenance: true
          sbom: true

      # Attestazione provenance SLSA L2
      - uses: actions/attest-build-provenance@v1
        with:
          subject-name: ghcr.io/${{ github.repository }}
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true
```

#### Strato 3 — Registry-time attestazioni

```yaml
  attest:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: sigstore/cosign-installer@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # Firma cosign keyless
      - name: Sign image
        run: |
          cosign sign --yes \
            ghcr.io/${{ github.repository }}@${{ needs.build.outputs.digest }}

      # SBOM attestation
      - name: Generate and attest SBOM
        run: |
          syft ghcr.io/${{ github.repository }}@${{ needs.build.outputs.digest }} \
            -o spdx-json > sbom.spdx.json

          cosign attest --yes \
            --predicate sbom.spdx.json \
            --type spdxjson \
            ghcr.io/${{ github.repository }}@${{ needs.build.outputs.digest }}

      # Vulnerability scan attestation
      - name: Scan and attest
        run: |
          trivy image --format cosign-vuln \
            ghcr.io/${{ github.repository }}@${{ needs.build.outputs.digest }} \
            > vuln-report.json

          cosign attest --yes \
            --predicate vuln-report.json \
            --type vuln \
            ghcr.io/${{ github.repository }}@${{ needs.build.outputs.digest }}
```

#### Strato 4 — Deploy-time enforcement

```yaml
# Kyverno ClusterPolicy per verificare firma + SBOM + vuln scan
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-signed-images-with-sbom
spec:
  validationFailureAction: Enforce
  webhookTimeoutSeconds: 30
  rules:
    # Regola 1: Richiedere firma cosign
    - name: verify-cosign-signature
      match:
        any:
          - resources:
              kinds: [Pod]
      verifyImages:
        - imageReferences:
            - "ghcr.io/myorg/*"
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/myorg/*/.github/workflows/*@refs/heads/main"
                    issuer: "https://token.actions.githubusercontent.com"
                    rekor:
                      url: https://rekor.sigstore.dev

    # Regola 2: Richiedere attestazione SBOM
    - name: verify-sbom-attestation
      match:
        any:
          - resources:
              kinds: [Pod]
      verifyImages:
        - imageReferences:
            - "ghcr.io/myorg/*"
          attestations:
            - type: spdxjson
              attestors:
                - entries:
                    - keyless:
                        subject: "https://github.com/myorg/*"
                        issuer: "https://token.actions.githubusercontent.com"
              conditions:
                - all:
                    - key: "{{ packages[].name }}"
                      operator: NotEquals
                      value: ""

    # Regola 3: Richiedere scan vulnerabilità senza critical
    - name: verify-no-critical-vulns
      match:
        any:
          - resources:
              kinds: [Pod]
      verifyImages:
        - imageReferences:
            - "ghcr.io/myorg/*"
          attestations:
            - type: vuln
              attestors:
                - entries:
                    - keyless:
                        subject: "https://github.com/myorg/*"
                        issuer: "https://token.actions.githubusercontent.com"
              conditions:
                - all:
                    - key: "{{ matches[?vulnerability.severity=='Critical'] | length(@) }}"
                      operator: Equals
                      value: "0"
```

### Sigstore Policy Controller come alternativa

Il [Policy Controller](https://docs.sigstore.dev/policy-controller/overview/) di Sigstore è un'alternativa a Kyverno specifica per la verifica di firme e attestazioni:

```yaml
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata:
  name: require-provenance
spec:
  images:
    - glob: "ghcr.io/myorg/**"
  authorities:
    - keyless:
        identities:
          - issuer: "https://token.actions.githubusercontent.com"
            subjectRegExp: "https://github.com/myorg/.*"
        ctlog:
          url: https://rekor.sigstore.dev
  policy:
    type: cue
    data: |
      predicateType: "https://slsa.dev/provenance/v1"
      predicate: {
        buildDefinition: {
          buildType: =~"^https://actions.github.io/"
        }
      }
```

### OPA Gatekeeper per verifica immagini

Per chi usa già OPA Gatekeeper, la verifica delle immagini richiede un webhook esterno come Connaisseur:

```yaml
# ConstraintTemplate per OPA Gatekeeper
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sallowedregistries
spec:
  crd:
    spec:
      names:
        kind: K8sAllowedRegistries
      validation:
        openAPIV3Schema:
          type: object
          properties:
            registries:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sallowedregistries

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not registry_allowed(container.image)
          msg := sprintf("Image '%v' is not from an allowed registry", [container.image])
        }

        registry_allowed(image) {
          startswith(image, input.parameters.registries[_])
        }
```

---

## Verification workflows

### Pipeline completa: build → sign → attest → verify

```yaml
name: Secure Build Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  packages: write
  id-token: write
  attestations: write
  security-events: write
  pull-requests: write

jobs:
  # 1. Dependency review (solo PR)
  dependency-review:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: moderate
          deny-licenses: GPL-3.0, AGPL-3.0

  # 2. Build e test
  build:
    runs-on: ubuntu-latest
    outputs:
      digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          push: ${{ github.event_name == 'push' }}
          tags: ghcr.io/myorg/myimage:${{ github.sha }}

  # 3. SBOM generation
  sbom:
    needs: build
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: anchore/sbom-action@v0
        with:
          image: ghcr.io/myorg/myimage@${{ needs.build.outputs.digest }}
          output-file: sbom.spdx.json
          format: spdx-json

      - uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.spdx.json

  # 4. Vulnerability scan
  scan:
    needs: build
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: ghcr.io/myorg/myimage@${{ needs.build.outputs.digest }}
          format: sarif
          output: trivy-results.sarif
          severity: CRITICAL,HIGH

      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-results.sarif

  # 5. Sign e attest
  sign-attest:
    needs: [build, sbom, scan]
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: sigstore/cosign-installer@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Sign image
        run: |
          cosign sign --yes \
            ghcr.io/myorg/myimage@${{ needs.build.outputs.digest }}

      - uses: actions/attest-build-provenance@v1
        with:
          subject-name: ghcr.io/myorg/myimage
          subject-digest: ${{ needs.build.outputs.digest }}
          push-to-registry: true

  # 6. Verify
  verify:
    needs: sign-attest
    runs-on: ubuntu-latest
    steps:
      - uses: sigstore/cosign-installer@v3

      - name: Verify signature
        run: |
          cosign verify \
            --certificate-identity "https://github.com/myorg/myrepo/.github/workflows/build.yml@refs/heads/main" \
            --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
            ghcr.io/myorg/myimage@${{ needs.build.outputs.digest }}

      - name: Verify attestation
        run: |
          gh attestation verify \
            oci://ghcr.io/myorg/myimage@${{ needs.build.outputs.digest }} \
            --owner myorg
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Pattern avanzati

### Policy-as-code per attestazioni

```yaml
# .github/attestation-policy.yml
required-attestations:
  - type: build-provenance
    builder:
      - "https://github.com/actions/runner/github-hosted"
    source:
      - "https://github.com/myorg/*"
  - type: sbom
    format: spdx-json
  - type: vulnerability-scan
    max-severity: high

denied-licenses:
  - GPL-3.0
  - AGPL-3.0
```

### Verifica pre-deploy con gate

```yaml
  deploy:
    needs: verify
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Gate — verify all attestations
        run: |
          ATTESTATIONS=$(gh attestation list \
            --owner myorg \
            --artifact-name myimage \
            --digest ${{ needs.build.outputs.digest }} \
            --format json)

          # Verificare che esistano provenance + SBOM
          PROVENANCE=$(echo "$ATTESTATIONS" | jq '[.[] | select(.predicateType == "https://slsa.dev/provenance/v1")] | length')
          SBOM=$(echo "$ATTESTATIONS" | jq '[.[] | select(.predicateType | contains("spdx"))] | length')

          if [ "$PROVENANCE" -lt 1 ] || [ "$SBOM" -lt 1 ]; then
            echo "❌ Missing required attestations"
            exit 1
          fi

          echo "✅ All required attestations present"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Deploy
        run: ./scripts/deploy.sh
```

### Multi-architettura con attestazione

```yaml
  build-multiarch:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        platform: [linux/amd64, linux/arm64]
    steps:
      - uses: docker/build-push-action@v5
        id: build
        with:
          push: true
          platforms: ${{ matrix.platform }}
          tags: ghcr.io/myorg/myimage:${{ github.sha }}-${{ matrix.platform }}

      - uses: actions/attest-build-provenance@v1
        with:
          subject-name: ghcr.io/myorg/myimage
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true
```

---

## Esercizi

### Lab 1 — Pipeline SLSA L2 completa

1. Crea un workflow che builda un container image.
2. Aggiungi `actions/attest-build-provenance@v1` per generare la provenance.
3. Verifica con `gh attestation verify`.
4. Ispeziona la provenance: identifica builder, source commit, workflow.

### Lab 2 — Dependency review enforcement

1. Configura `actions/dependency-review-action@v4` nel repository.
2. Crea una PR che aggiunge una dipendenza con una vulnerabilità nota.
3. Verifica che il check fallisca.
4. Configura deny-licenses per bloccare GPL-3.0.
5. Testa con una dipendenza GPL.

### Lab 3 — npm publish con provenance

1. Crea un pacchetto npm di test.
2. Configura il workflow per pubblicare con `--provenance`.
3. Verifica su npmjs.com che appaia il badge "Provenance".
4. Esegui `npm audit signatures` per verificare localmente.

### Lab 4 — Container signing con cosign

1. Installa cosign localmente.
2. Crea un workflow che builda, pusha e firma un container.
3. Verifica la firma con `cosign verify`.
4. Aggiungi un'attestazione SBOM.
5. Verifica l'attestazione con `cosign verify-attestation`.

### Lab 5 — SBOM completo

1. Genera un SBOM per il tuo progetto con Syft o Trivy.
2. Analizza il contenuto: conta le dipendenze, identifica le licenze.
3. Attesta l'SBOM al container image.
4. Configura l'upload al GitHub dependency graph.

### Lab 6 — Scorecard

1. Configura il workflow Scorecard nel tuo repository.
2. Analizza i risultati: quali check falliscono?
3. Migliora almeno 3 check (es. pinned dependencies, branch protection, token permissions).
4. Riesegui e confronta i punteggi.

### Stretch — Kyverno admission policy

1. Configura Kyverno nel tuo cluster Kubernetes.
2. Crea una policy che richiede firma cosign per immagini da `ghcr.io/myorg/*`.
3. Testa con un'immagine firmata (deve passare) e una non firmata (deve fallire).

---

## Troubleshooting — 20 problemi comuni

### 1. `Error: attestation upload failed: forbidden`

**Causa:** manca `permissions: attestations: write` nel workflow.

**Soluzione:**
```yaml
permissions:
  attestations: write
  id-token: write
  contents: read
```

### 2. `Error: cosign sign failed: getting identity token`

**Causa:** `permissions: id-token: write` non dichiarato.

**Soluzione:** aggiungere la permission. Necessaria per il flusso keyless via Sigstore.

### 3. `Error: no matching attestations found`

**Causa:** attestazione cercata con owner/repository sbagliato.

**Soluzione:**
```bash
# Verificare con l'owner corretto
gh attestation verify oci://ghcr.io/myorg/myimage:tag --owner myorg

# Listare le attestazioni disponibili
gh attestation list --owner myorg --artifact-name myimage
```

### 4. npm publish con provenance fallisce: `npm ERR! 403`

**Causa:** il token npm non ha permessi di pubblicazione, o il pacchetto esiste già su un altro account.

**Soluzione:** verificare che `NPM_TOKEN` abbia scope `publish` e che il pacchetto sia del tuo account.

### 5. SBOM generation produce file vuoto

**Causa:** l'immagine container non ha un filesystem con pacchetti riconosciuti, o il tool SBOM non supporta il package manager.

**Soluzione:** verificare che l'immagine abbia un package manager (apt, npm, pip, ecc.) e usare un tool compatibile.

### 6. Dependency review action fallisce con `Error: snapshot warnings`

**Causa:** il dependency graph non è ancora aggiornato.

**Soluzione:**
```yaml
- uses: actions/dependency-review-action@v4
  with:
    retry-on-snapshot-warnings: true
    retry-on-snapshot-warnings-timeout: 120
```

### 7. `Error: certificate identity mismatch` in cosign verify

**Causa:** il `--certificate-identity` non corrisponde al workflow che ha firmato.

**Soluzione:** controllare esattamente quale workflow e ref ha firmato:
```bash
cosign verify --certificate-identity-regexp ".*myrepo.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/myorg/myimage@sha256:abc
```

### 8. Rekor entry non trovata

**Causa:** la firma è stata eseguita con `--tlog-upload=false` o Rekor era down durante la firma.

**Soluzione:** rifirmare con Rekor abilitato (default).

### 9. Scorecard punteggio basso su "Pinned-Dependencies"

**Causa:** action usate senza hash pinning (es. `uses: actions/checkout@v4` invece di `uses: actions/checkout@hash`).

**Soluzione:**
```yaml
# Invece di:
- uses: actions/checkout@v4

# Usare:
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
```

### 10. Dependabot PR non si auto-merge

**Causa:** auto-merge richiede configurazione separata, branch protection, e status checks obbligatori.

**Soluzione:** configurare auto-merge via workflow:
```yaml
name: Dependabot auto-merge
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
      - if: steps.metadata.outputs.update-type == 'version-update:semver-patch'
        run: gh pr merge "$PR" --auto --squash
        env:
          PR: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 11. `Error: push-to-registry failed: unauthorized`

**Causa:** manca `permissions: packages: write` per pushare attestazioni al registry.

**Soluzione:** aggiungere la permission.

### 12. SLSA generator workflow fallisce: `Error: base64-subjects is empty`

**Causa:** l'output del job di build non è stato correttamente passato al job di provenance.

**Soluzione:** verificare che l'output sia correttamente base64-encoded e passato via `needs.build.outputs.digests`.

### 13. Container build con multi-stage non genera SBOM completo

**Causa:** il tool SBOM analizza solo il layer finale, non gli stage intermedi.

**Soluzione:** generare l'SBOM dal Dockerfile o dal lockfile, non dall'immagine finale.

### 14. `Error: Fulcio certificate verification failed`

**Causa:** il certificato Fulcio è scaduto (durata ~10 min) o il clock è sfasato.

**Soluzione:** la verifica usa Rekor timestamp, non il certificato live. Se persiste, verificare la connettività a `fulcio.sigstore.dev`.

### 15. Dependabot ignora un ecosistema

**Causa:** il `package-ecosystem` o il `directory` nel `dependabot.yml` non corrisponde al layout del progetto.

**Soluzione:** verificare che il path sia corretto:
```yaml
# Se il Dockerfile è in /docker/
- package-ecosystem: docker
  directory: "/docker"
```

### 16. `gh attestation verify` fallisce con exit code 1 senza messaggio

**Causa:** versione di `gh` troppo vecchia (attestation è un'extension recente).

**Soluzione:** aggiornare `gh` e verificare che l'extension sia installata:
```bash
gh extension install github/gh-attestation
# o aggiornare gh alla versione più recente
```

### 17. Cosign non trova le firme nell'OCI registry

**Causa:** le firme sono state pushate con un tag diverso o il registry non supporta OCI artifacts.

**Soluzione:** usare il digest per la verifica, non il tag:
```bash
cosign verify ghcr.io/myorg/myimage@sha256:abc123... # digest, non tag
```

### 18. SBOM non include dipendenze dev

**Causa:** il tool SBOM potrebbe filtrare le dev dependencies per default.

**Soluzione:** usare l'opzione per includerle se necessario:
```bash
syft packages dir:. --scope all-layers
```

### 19. Dependency review non rileva vulnerabilità in sub-dipendenze

**Causa:** il dependency graph non risolve tutte le sub-dipendenze per alcuni ecosistemi.

**Soluzione:** usare `npm audit` / `pip audit` / `govulncheck` come check aggiuntivi.

### 20. Attestazione presente ma `gh attestation verify` fallisce

**Causa:** l'attestazione è per un digest diverso dall'immagine corrente (es. immagine ribuildata senza re-attestare).

**Soluzione:** dopo ogni rebuild, rigenerare l'attestazione con il nuovo digest.

---

## FAQ — 20 domande e risposte

### 1. SLSA è obbligatorio?

No, SLSA è un framework volontario. Tuttavia, molte organizzazioni lo richiedono nelle policy di procurement e compliance. Executive Order 14028 (USA) richiede SBOM e provenance per software venduto al governo.

### 2. Qual è la differenza tra SLSA L2 e L3?

L2: la provenance è firmata dal servizio di build hosted. L3: aggiunge isolamento del builder e non-falsificabilità dal maintainer. Con GitHub Actions, `actions/attest-build-provenance` produce L2, `slsa-framework/slsa-github-generator` produce L3.

### 3. Cosign keyless è sicuro quanto le chiavi tradizionali?

Sì, per CI/CD. La sicurezza si basa su: (1) la trust nell'identity provider (GitHub OIDC), (2) il transparency log (Rekor) che registra ogni firma, (3) Fulcio che verifica l'identità prima di emettere il certificato.

### 4. Posso usare Sigstore con un registry privato?

Sì. cosign supporta OCI registry compatibili. Le firme vengono salvate come OCI artifacts nello stesso registry. Alcuni registry enterprise (Harbor, JFrog) hanno supporto nativo.

### 5. SBOM rallenta la CI pipeline?

La generazione SBOM richiede tipicamente 1-3 minuti. Può essere parallelizzata con altri job. L'impatto è minimo rispetto al valore di sicurezza.

### 6. Qual è la differenza tra SPDX e CycloneDX?

SPDX è uno standard ISO focalizzato su licenze e compliance. CycloneDX è uno standard OWASP focalizzato su sicurezza e vulnerabilità. Entrambi sono validi; scegliere in base al caso d'uso.

### 7. Dependabot vs Renovate: quale scegliere?

Dependabot: integrato in GitHub, zero setup, supporta i principali ecosistemi. Renovate: più configurabile, supporta più ecosistemi, auto-merge avanzato, supporta monorepo meglio. Per la maggior parte dei progetti GitHub, Dependabot è sufficiente.

### 8. Come gestisco i falsi positivi nella dependency review?

Usare `allow-ghsas`:
```yaml
- uses: actions/dependency-review-action@v4
  with:
    allow-ghsas: GHSA-xxxx-yyyy-zzzz
```

### 9. Posso attestare artefatti non-container (binari, tarball)?

Sì. `actions/attest-build-provenance@v1` supporta `subject-path` per file locali e `subject-name`/`subject-digest` per container.

### 10. L'attestazione sopravvive al re-tag di un'immagine?

L'attestazione è legata al digest (SHA256), non al tag. Se l'immagine mantiene lo stesso digest, l'attestazione resta valida. Se viene ribuildata (nuovo digest), serve una nuova attestazione.

### 11. Come integro SLSA con Kubernetes?

Usare admission controller (Kyverno, OPA/Gatekeeper, Connaisseur) che verificano le firme e le attestazioni prima di ammettere un pod.

### 12. Posso generare provenance per build locali?

SLSA L2+ richiede un builder hosted. Per build locali, si può generare provenance L1 con `slsa-verifier` ma non è firmata dal servizio.

### 13. Quante attestazioni posso allegare a un artefatto?

Non c'è un limite pratico. Tipicamente: provenance + SBOM + vulnerability scan = 3 attestazioni.

### 14. Le attestazioni GitHub sono pubbliche?

Per repository pubblici, sì. Per repository privati, le attestazioni sono visibili solo a chi ha accesso al repository.

### 15. Come migro da signing con chiave a keyless?

1. Inizia a firmare con keyless in parallelo.
2. Verifica che la pipeline funzioni.
3. Aggiorna i verificatori (admission controller, policy) per accettare firme keyless.
4. Dismetti le chiavi private.

### 16. Scorecard funziona con repository privati?

Sì, ma i risultati non vengono pubblicati su `securityscorecards.dev`. Restano visibili solo nel repository (SARIF upload).

### 17. Posso personalizzare i predicati dell'attestazione?

Sì, con cosign:
```bash
cosign attest --predicate my-custom-predicate.json --type custom ghcr.io/...
```

### 18. Le attestazioni hanno un costo?

Su GitHub: gratuite per repository pubblici. Per repository privati, richiedono GitHub Enterprise o un piano con GitHub Advanced Security (per Artifact Attestations).

### 19. Come verifico la supply chain delle Action che uso?

1. Pinned by hash (`uses: action@sha256:...`).
2. Verificare la Scorecard del repository dell'action.
3. Controllare se l'action pubblica provenance.
4. Usare `step-security/harden-runner` per monitorare le chiamate di rete.

### 20. SBOM è richiesto legalmente?

Dipende dalla giurisdizione e dal settore. In USA, Executive Order 14028 lo richiede per software venduto al governo federale. Nell'Unione Europea, il **Cyber Resilience Act (CRA)** — Regolamento (UE) 2024/2847, pubblicato in Gazzetta Ufficiale il 20 novembre 2024 — introduce obblighi SBOM vincolanti per i prodotti con elementi digitali commercializzati nel mercato unico europeo. È buona pratica generare SBOM comunque, indipendentemente dalla giurisdizione.

#### EU Cyber Resilience Act — obblighi SBOM e supply chain

Il CRA è il primo regolamento europeo che impone requisiti di cybersecurity per **tutti i prodotti con elementi digitali** venduti nell'UE, incluso software standalone, firmware, e dispositivi IoT. I requisiti più rilevanti per la supply chain software:

**Timeline di conformità:**

| Data | Obbligo |
|---|---|
| 20 novembre 2024 | Pubblicazione in Gazzetta Ufficiale UE |
| 11 giugno 2026 | Obbligo di notifica degli organismi di valutazione della conformità |
| **11 settembre 2026** | **Obbligo di segnalazione delle vulnerabilità attivamente sfruttate** (entro 24 ore dalla discovery) |
| **11 dicembre 2027** | **Conformità piena** — tutti i prodotti devono soddisfare i requisiti essenziali di cybersecurity, incluso SBOM |

**Requisiti SBOM del CRA (Allegato I, Parte II, punto 1):**

Il fabbricante deve "identificare e documentare le vulnerabilità e i componenti contenuti nei prodotti con elementi digitali, anche redigendo un **software bill of materials** in un formato comunemente utilizzato e leggibile dalle macchine che copra quantomeno le dipendenze di primo livello del prodotto."

In pratica questo significa:

- Formato machine-readable obbligatorio (SPDX o CycloneDX).
- Copertura minima: dipendenze di primo livello (first-level dependencies).
- Il SBOM deve essere incluso nella documentazione tecnica.
- Aggiornamento del SBOM richiesto per ogni release e per ogni vulnerabilità corretta.

**Impatto per i workflow GitHub Actions:** Le pipeline CI/CD dovranno integrare la generazione SBOM come fase obbligatoria del processo di release per qualsiasi software destinato al mercato UE. I workflow già descritti in questo documento (con `anchore/sbom-action`, `syft`, o `cyclonedx-gomod`) soddisfano i requisiti tecnici del CRA quando configurati correttamente.

**Esenzione per il software open source non-commerciale:** Il CRA esenta esplicitamente il software open source sviluppato e distribuito senza scopo commerciale (Articolo 3, definizione di "open-source software steward"). Tuttavia, il software open source incluso come _componente_ in un prodotto commerciale rimane soggetto ai requisiti — la responsabilità ricade sul fabbricante che integra il componente.

---

## Letture consigliate

- SLSA framework — [slsa.dev](https://slsa.dev/)
- SLSA Source Track v1.2 RC2 — [slsa.dev/spec/v1.2/source-requirements](https://slsa.dev/spec/v1.2/source-requirements)
- GitHub Artifact Attestations — [docs.github.com/en/actions/security-guides/using-artifact-attestations](https://docs.github.com/en/actions/security-guides/using-artifact-attestations)
- Sigstore documentation — [docs.sigstore.dev](https://docs.sigstore.dev/)
- Rekor v2 announcement — [blog.sigstore.dev/rekor-v2-ga](https://blog.sigstore.dev/rekor-v2-ga)
- Gitsign — [github.com/sigstore/gitsign](https://github.com/sigstore/gitsign)
- in-toto specification — [in-toto.io](https://in-toto.io/)
- OpenSSF Scorecard — [securityscorecards.dev](https://securityscorecards.dev/)
- SPDX specification — [spdx.dev](https://spdx.dev/)
- CycloneDX specification — [cyclonedx.org](https://cyclonedx.org/)
- npm provenance docs — [docs.npmjs.com/generating-provenance-statements](https://docs.npmjs.com/generating-provenance-statements)
- PyPI Trusted Publishing — [docs.pypi.org/trusted-publishers](https://docs.pypi.org/trusted-publishers/)
- PEP 740 — [peps.python.org/pep-0740](https://peps.python.org/pep-0740/)
- Dependabot configuration — [docs.github.com/en/code-security/dependabot](https://docs.github.com/en/code-security/dependabot)
- Dependency review action — [github.com/actions/dependency-review-action](https://github.com/actions/dependency-review-action)
- cosign documentation — [docs.sigstore.dev/cosign/overview](https://docs.sigstore.dev/cosign/overview)
- Kyverno image verification — [kyverno.io/docs/writing-policies/verify-images](https://kyverno.io/docs/writing-policies/verify-images/)
- SLSA GitHub generator — [github.com/slsa-framework/slsa-github-generator](https://github.com/slsa-framework/slsa-github-generator)
- EU Cyber Resilience Act — [Regolamento (UE) 2024/2847](https://eur-lex.europa.eu/eli/reg/2024/2847/oj)

- SLSA framework — [slsa.dev](https://slsa.dev/)
- GitHub Artifact Attestations — [docs.github.com/en/actions/security-guides/using-artifact-attestations](https://docs.github.com/en/actions/security-guides/using-artifact-attestations)
- Sigstore documentation — [docs.sigstore.dev](https://docs.sigstore.dev/)
- in-toto specification — [in-toto.io](https://in-toto.io/)
- OpenSSF Scorecard — [securityscorecards.dev](https://securityscorecards.dev/)
- SPDX specification — [spdx.dev](https://spdx.dev/)
- CycloneDX specification — [cyclonedx.org](https://cyclonedx.org/)
- npm provenance docs — [docs.npmjs.com/generating-provenance-statements](https://docs.npmjs.com/generating-provenance-statements)
- Dependabot configuration — [docs.github.com/en/code-security/dependabot](https://docs.github.com/en/code-security/dependabot)
- Dependency review action — [github.com/actions/dependency-review-action](https://github.com/actions/dependency-review-action)
- cosign documentation — [docs.sigstore.dev/cosign/overview](https://docs.sigstore.dev/cosign/overview)
- Kyverno image verification — [kyverno.io/docs/writing-policies/verify-images](https://kyverno.io/docs/writing-policies/verify-images/)
- SLSA GitHub generator — [github.com/slsa-framework/slsa-github-generator](https://github.com/slsa-framework/slsa-github-generator)

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [14 — GitHub Packages, Pages e Releases](14-github-packages-pages-releases.md) | Container registry e npm registry dove pubblicare artefatti attestati |
| [16 — GitHub Security e Scanning](16-github-security-scanning.md) | Dependabot alerts e dependency review complementano la supply-chain security |
| [19 — GitHub Actions: Ricette CI/CD](19-github-actions-ci-cd-ricette.md) | Pipeline CI/CD in cui integrare SLSA generator e SBOM generation |
| [24 — DevOps Completo con GitHub](24-devops-completo-con-github.md) | Pipeline end-to-end dove attestazione e firma sono fasi del delivery |
| [26 — OIDC Cloud Credentials](26-oidc-cloud-credentials.md) | OIDC fornisce l'identità del workflow usata per la provenance firmata |
| [28 — CodeQL e GitHub Advanced Security](28-codeql-advanced-security.md) | GHAS + supply-chain attestation coprono SAST e SCA in modo complementare |

---

## Glossario

| Termine | Definizione |
|---|---|
| **SLSA** | Supply-chain Levels for Software Artifacts — framework graduato per la sicurezza della supply chain software |
| **Provenance** | Documento firmato che attesta l'origine di un artefatto: chi, cosa, come, quando, dove è stato buildato |
| **Attestation** | Dichiarazione firmata crittograficamente su un artefatto (provenance, SBOM, scan risultati) |
| **in-toto** | Standard per le attestazioni di supply chain — definisce il formato Statement con subject e predicate |
| **DSSE** | Dead Simple Signing Envelope — formato per wrappare e firmare attestazioni in-toto |
| **Sigstore** | Ecosistema open source per la firma e la verifica di artefatti software (cosign, Rekor, Fulcio) |
| **cosign** | Tool client Sigstore per firmare, verificare e attestare container image e artefatti |
| **Fulcio** | Certificate Authority Sigstore — emette certificati effimeri basati su identità OIDC |
| **Rekor** | Transparency log Sigstore — registro immutabile e pubblico di tutte le firme |
| **Keyless signing** | Firma senza gestire chiavi private — usa OIDC identity + Fulcio per la firma |
| **SBOM** | Software Bill of Materials — inventario completo dei componenti software di un artefatto |
| **SPDX** | Software Package Data Exchange — standard ISO per SBOM, focalizzato su licenze |
| **CycloneDX** | Standard OWASP per SBOM, focalizzato su sicurezza e vulnerabilità |
| **Dependabot** | Servizio GitHub che monitora le dipendenze per vulnerabilità e aggiornamenti |
| **Dependency review** | Check automatico sulle PR che identifica dipendenze vulnerabili introdotte |
| **npm provenance** | Funzionalità di npm che lega un pacchetto pubblicato al suo source repo e build workflow |
| **Scorecard** | Tool OpenSSF che valuta le pratiche di sicurezza di un progetto open source |
| **SARIF** | Static Analysis Results Interchange Format — formato standard per risultati di analisi statica |
| **`actions/attest-build-provenance`** | Action GitHub ufficiale per generare provenance SLSA L2 |
| **`slsa-github-generator`** | Reusable workflow del progetto SLSA per generare provenance L3 |
| **Transparency log** | Registro pubblico e immutabile che registra eventi crittografici (firme, certificati) |
| **OCI artifact** | Artefatto generico (firma, attestazione, SBOM) memorizzato in un registry OCI-compatible |
| **Admission controller** | Componente Kubernetes che verifica i pod prima di ammetterli (es. Kyverno, OPA) |
| **Hash pinning** | Pratica di specificare dipendenze tramite hash crittografico anziché tag/versione |
| **Gitsign** | Tool Sigstore per la firma keyless dei commit Git — usa OIDC + Fulcio + Rekor al posto di chiavi GPG/SSH |
| **Rekor v2** | Riscrittura del transparency log Sigstore con backend Trillian-Tessera tile-based, GA ottobre 2025 |
| **Trillian-Tessera** | Backend tile-based per transparency log — organizza le entry in tile fissi servibili via CDN/object storage |
| **PEP 740** | Python Enhancement Proposal per attestazioni digitali native su PyPI — define il formato e l'API per la verifica |
| **Trusted Publishing** | Meccanismo che permette a un workflow CI/CD di pubblicare pacchetti usando OIDC identity invece di API token statici |
| **Source Track** | Track SLSA (v1.2) focalizzato sulla gestione del codice sorgente — livelli L0-L3 per VCS, identity, review, retention |
| **Source provenance** | Attestazione dell'origine del codice sorgente — chi ha approvato quali modifiche e con quali protezioni attive |
| **Mini Shai-Hulud** | Attacco dimostrativo (DEF CON 32, 2024) che hijacka il token OIDC di un workflow per generare provenance SLSA valida su codice malevolo |
