---
corso: "GitHub e Git Actions"
fase: "2 — Branching e Workflow"
modulo: 2
titolo: "Strategie di Branching — Guida Completa"
versione: "Git 2.47"
livello: "Avanzato"
prerequisiti: ["01-fondamenti-git", "Esperienza base con branch e merge"]
obiettivi:
  - "Confrontare GitFlow, GitHub Flow, Trunk-Based Development e GitLab Flow"
  - "Selezionare la strategia di branching adatta al contesto del team"
  - "Implementare branch protection rules e CODEOWNERS per la code review"
  - "Gestire release branching, hotfix e cherry-pick cross-branch"
  - "Applicare feature flag per disaccoppiare deploy da release"
tag: [branching, gitflow, github-flow, trunk-based, release, codeowners, feature-flag, merge-strategy]
---

# Strategie di Branching — Guida Completa

> **Modulo 02** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al termine di questo modulo sarai in grado di:
>
> 1. Confrontare i modelli di branching (GitFlow, GitHub Flow, Trunk-Based, GitLab Flow) e i loro trade-off
> 2. Selezionare la strategia di branching ottimale in base a dimensione del team, frequenza di release e maturità CI/CD
> 3. Configurare branch protection rules, rulesets e CODEOWNERS per governance del codice
> 4. Gestire release branching con hotfix, cherry-pick e semantic versioning
> 5. Implementare feature flag per separare il deploy dalla release di funzionalità

## Idee guida
1. **Trunk-based > Gitflow per high-velocity team.** Feature flag invece di feature branch lunghe.
2. **GitHub Flow: ottimo per SaaS/web app.**
3. **Gitflow: legacy ma utile per release-heavy product.**
4. **Branch lifetime < 5 giorni per ridurre merge conflict.**


## Indice

- [Panoramica](#panoramica)
- [Teoria: Il Costo del Branching](#teoria-il-costo-del-branching)
- [GitFlow](#gitflow)
- [GitHub Flow](#github-flow)
- [Trunk-Based Development](#trunk-based-development)
- [GitLab Flow](#gitlab-flow)
- [Release Branching](#release-branching)
- [Feature Flags vs Feature Branches](#feature-flags-vs-feature-branches)
- [Branch Protection Rules](#branch-protection-rules)
- [Merge Strategies: Merge Commit, Squash, Rebase](#merge-strategies-merge-commit-squash-rebase)
- [Cherry-Pick Workflows](#cherry-pick-workflows)
- [Monorepo Branching](#monorepo-branching)
- [Confronto Strategie](#confronto-strategie)
- [Conventional Commits](#conventional-commits)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Release Flow (Microsoft)](#release-flow-microsoft)
- [Stacked PRs e Stacked Diffs](#stacked-prs-e-stacked-diffs)
- [Branching per Applicazioni Mobile](#branching-per-applicazioni-mobile)
- [Branching e GitOps — Promozione tra Ambienti](#branching-e-gitops--promozione-tra-ambienti)
- [Anti-Pattern del Branching](#anti-pattern-del-branching)
- [Branching e Metriche DORA](#branching-e-metriche-dora)
- [Naming Convention Avanzate](#naming-convention-avanzate)
- [Feature Flag: Architettura e Strumenti a Confronto](#feature-flag-architettura-e-strumenti-a-confronto)
- [Migrazione tra Strategie di Branching](#migrazione-tra-strategie-di-branching)
- [Matrice Decisionale Avanzata](#matrice-decisionale-avanzata)
- [Casi di Studio Reali](#casi-di-studio-reali)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Esercizi Pratici](#esercizi-pratici)
- [Riferimenti](#riferimenti)

---

## Panoramica

La strategia di branching definisce come il team organizza il lavoro: come si creano branch, come si integrano le modifiche, come si gestiscono release e hotfix. La scelta dipende da dimensione del team, frequenza di release, complessità del progetto, e maturità dell'infrastruttura CI/CD.

Non esiste una strategia universale. Un team di 3 sviluppatori che deploya 10 volte al giorno ha esigenze radicalmente diverse da un team di 50 persone che rilascia un prodotto on-premise ogni trimestre. La strategia di branching è una decisione architetturale, non un dettaglio tecnico.

### Costo della scelta sbagliata

Una strategia inadeguata produce effetti a cascata:
- **Troppo complessa per il team**: rallentamento, errori di procedura, branch abbandonati
- **Troppo semplice per il prodotto**: incapacità di gestire versioni multiple, hotfix rischiosi
- **Branch con vita troppo lunga**: merge conflict crescenti, integrazione dolorosa
- **Assenza di protezioni**: codice rotto in produzione, commit diretti non revisionati

---

## Teoria: Il Costo del Branching

### Integration Frequency e Merge Pain

La relazione tra durata di un branch e difficoltà di integrazione non è lineare — è esponenziale. Un branch che vive per 1 giorno ha tipicamente 0-2 conflitti. Un branch che vive per 2 settimane può averne 20-50. Questo fenomeno è noto come **merge pain curve**.

```
Merge Pain
    │
    │                              ╱
    │                           ╱
    │                        ╱
    │                     ╱
    │                 ╱
    │             ╱
    │         ╱
    │      ╱
    │   ╱
    │╱
    └────────────────────────────────────
                    Durata del Branch (giorni)

    1g = basso rischio
    3g = rischio gestibile
    7g = rischio significativo
    14g+ = rischio critico — refactoring dolorosi, conflitti semantici
```

### La Legge di Continuous Integration

Più frequentemente integri, meno dolorosa è ogni integrazione. Questo principio guida la scelta della strategia:

| Frequenza di Integrazione | Strategia Tipica | Rischio per Integrazione |
|---------------------------|------------------|--------------------------|
| Multipla al giorno | Trunk-Based Development | Minimo |
| Giornaliera | GitHub Flow con branch brevi | Basso |
| Settimanale | GitHub Flow / GitLab Flow | Medio |
| Bi-settimanale o meno | Git Flow | Alto |

### Branch come Debito Tecnico

Ogni branch attivo è un debito: rappresenta codice non integrato, non testato nel contesto completo, non validato dagli altri sviluppatori. Più branch attivi simultaneamente = più debito = più rischio.

```bash
# Contare i branch attivi e la loro età
git for-each-ref --sort=-committerdate --format='%(refname:short) %(committerdate:relative)' refs/heads/ | head -20

# Trovare branch stale (più di 30 giorni senza commit)
git for-each-ref --sort=committerdate --format='%(committerdate:short) %(refname:short)' refs/remotes/origin/ \
  | awk -v cutoff="$(date -d '30 days ago' +%Y-%m-%d)" '$1 < cutoff'

# Contare i branch per sviluppatore
git for-each-ref --format='%(authorname)' refs/remotes/origin/ | sort | uniq -c | sort -rn
```

---

## GitFlow

### Teoria e Contesto

GitFlow è un modello definito da Vincent Driessen nel 2010. È stato progettato per software con release schedulate e versioni multiple mantenute simultaneamente. Nonostante sia considerato legacy per applicazioni SaaS, rimane la scelta corretta per:

- Software distribuito (app mobile, desktop, embedded)
- Librerie open source con supporto multi-versione
- Prodotti enterprise on-premise
- Team che rilasciano su cadenza fissa (mensile, trimestrale)

### Architettura dei Branch

```
GitFlow è un modello rigido con branch dedicati per ogni fase del ciclo di vita.

Branch permanenti:
├── main (o master)    → Codice in produzione (solo release tagged)
└── develop            → Branch di integrazione (prossima release)

Branch temporanei:
├── feature/*          → Nuove funzionalità (da develop, merge in develop)
├── release/*          → Preparazione release (da develop, merge in main + develop)
├── hotfix/*           → Fix urgenti produzione (da main, merge in main + develop)
└── bugfix/*           → Fix non urgenti (da develop, merge in develop)

Ciclo di vita:
1. Creare feature branch da develop
2. Sviluppare e committare sulla feature
3. Merge feature in develop (PR + review)
4. Quando pronto per release: creare release/x.y.z da develop
5. Test e fix sulla release branch
6. Merge release in main (tag) E in develop
7. Per fix urgenti: hotfix da main, merge in main + develop
```

### Workflow Pratico Completo

```bash
# ─── SETUP INIZIALE ───

# Inizializzare GitFlow (usa l'extension git-flow)
git flow init
# Branch names:
# - Production: main
# - Development: develop
# - Feature prefix: feature/
# - Release prefix: release/
# - Hotfix prefix: hotfix/

# Oppure manualmente senza l'extension
git checkout -b develop main
git push -u origin develop


# ─── FEATURE WORKFLOW ───

# Creare una feature branch da develop
git switch develop
git pull origin develop
git switch -c feature/user-auth

# Sviluppo iterativo
# ... modifiche al codice ...
git add src/auth/
git commit -m "feat(auth): implementare login con email e password"

# ... altre modifiche ...
git add src/auth/ tests/auth/
git commit -m "feat(auth): aggiungere validazione input login"

# Tenere aggiornato con develop (opzione merge)
git switch develop && git pull
git switch feature/user-auth
git merge develop
# Risolvere eventuali conflitti

# Oppure tenere aggiornato con develop (opzione rebase — solo branch locale)
git fetch origin
git rebase origin/develop

# Pushare e creare la PR
git push -u origin feature/user-auth
gh pr create --base develop --title "feat(auth): autenticazione utente" \
  --body "## Descrizione
Implementazione del sistema di autenticazione con email/password.

## Modifiche
- Login con validazione input
- Hashing password con bcrypt
- JWT per sessione

## Test
- Unit test per il servizio di autenticazione
- Integration test per il flusso completo di login"

# Dopo approvazione e CI verde
gh pr merge --squash --delete-branch


# ─── RELEASE WORKFLOW ───

# Creare release branch da develop
git switch develop
git pull origin develop
git switch -c release/1.2.0

# Attività sulla release branch:
# - Bump della versione nei file di configurazione
# - Aggiornamento del changelog
# - Fix di bug scoperti durante il testing
npm version 1.2.0 --no-git-tag-version
git add package.json package-lock.json CHANGELOG.md
git commit -m "chore: bump versione a 1.2.0"

# Fix last-minute sulla release branch
git add src/fix.js
git commit -m "fix: correggere edge case nel parsing date"

# Completare la release
git switch main
git merge --no-ff release/1.2.0 -m "release: v1.2.0"
git tag -a v1.2.0 -m "Release 1.2.0

Novità:
- Autenticazione utente
- Dashboard migliorata
- Fix performance query"

# Merge anche in develop per portare i fix della release
git switch develop
git merge --no-ff release/1.2.0 -m "chore: merge release/1.2.0 in develop"

# Push e cleanup
git push origin main develop --tags
git branch -d release/1.2.0
git push origin --delete release/1.2.0


# ─── HOTFIX WORKFLOW ───

# Bug critico in produzione — creare hotfix da main
git switch main
git pull origin main
git switch -c hotfix/critical-xss-fix

# Applicare la fix
git add src/sanitize.js
git commit -m "fix(security): sanitizzare input utente contro XSS"

# Test della fix
npm test
npm run test:security

# Completare l'hotfix
git switch main
git merge --no-ff hotfix/critical-xss-fix -m "hotfix: v1.2.1 — fix XSS"
git tag -a v1.2.1 -m "Hotfix 1.2.1: correzione vulnerabilità XSS"

# Merge anche in develop
git switch develop
git merge --no-ff hotfix/critical-xss-fix -m "chore: merge hotfix/critical-xss-fix in develop"

# Push e cleanup
git push origin main develop --tags
git branch -d hotfix/critical-xss-fix
git push origin --delete hotfix/critical-xss-fix
```

### Criticità di GitFlow

1. **Complessità procedurale**: ogni rilascio richiede 4-6 merge. Errori di procedura sono comuni
2. **develop diventa bottleneck**: tutte le feature convergono qui, creando conflitti
3. **Release branch lunghi**: se la release dura settimane, develop diverge ulteriormente
4. **Doppio merge (main + develop)**: dimenticare il merge in develop è un errore frequente che causa perdita di fix

---

## GitHub Flow

### Teoria e Contesto

GitHub Flow è un modello deliberatamente semplice. Esiste un solo branch permanente (`main`), che deve essere sempre deployable. Ogni modifica passa per un feature branch e una Pull Request. È la strategia dominante per applicazioni web, SaaS e microservizi con deploy continuo.

### Architettura dei Branch

```
GitHub Flow: un branch permanente + feature branch.

Branch permanente:
└── main               → Sempre deployable, protetto

Branch temporanei:
└── feature/*          → Ogni modifica (feature, fix, refactor)
    → Da main, merge in main via PR + review

Ciclo di vita:
1. Creare branch da main (nome descrittivo)
2. Committare frequentemente
3. Aprire PR quando pronto per review
4. Code review + CI checks
5. Merge in main → deploy automatico
6. Eliminare feature branch

Regole inviolabili:
- main è SEMPRE deployable
- Ogni modifica passa per PR + review
- CI deve passare prima del merge
- Deploy automatico dopo merge in main
```

### Workflow Pratico Completo

```bash
# Partire sempre da main aggiornato
git switch main
git pull origin main

# Creare branch con nome descrittivo
# Convenzione: tipo/descrizione-breve
git switch -c fix/login-timeout

# Sviluppo
# ... modifiche ...
git add src/auth/session.js
git commit -m "fix(auth): aumentare timeout sessione da 5s a 30s"

# Pushare e creare PR
git push -u origin fix/login-timeout

gh pr create \
  --title "fix(auth): aumentare timeout sessione" \
  --body "## Problema
Il login fallisce per utenti con connessione lenta perché il timeout
di 5 secondi è troppo basso.

## Soluzione
Aumentato il timeout a 30 secondi con backoff esponenziale.

## Test
- Testato con throttling a 3G nel browser DevTools
- Unit test aggiornati

Fixes #142"

# Dopo review e CI verde
gh pr merge --squash --delete-branch

# Il deploy avviene automaticamente al merge in main
```

### Naming Convention per i Branch

```bash
# Feature branch
feature/oauth2-google-login
feature/dashboard-analytics
feature/JIRA-1234-user-preferences

# Bug fix
fix/login-timeout
fix/memory-leak-websocket
bugfix/JIRA-5678-null-pointer

# Hotfix (urgente)
hotfix/xss-vulnerability
hotfix/database-connection-leak

# Refactoring
refactor/extract-auth-service
refactor/migrate-to-typescript

# Chore
chore/update-dependencies
chore/configure-eslint

# Documentation
docs/api-reference
docs/deployment-guide
```

### Quando GitHub Flow Non Basta

GitHub Flow presuppone che ogni commit su main sia deployabile. Questo non funziona quando:
- Si devono supportare versioni multiple in produzione
- Le release richiedono approvazione formale e window di deploy
- Feature parzialmente completate non possono essere in produzione (e i feature flag non sono un'opzione)

---

## Trunk-Based Development

### Teoria e Contesto

Trunk-Based Development (TBD) è la strategia preferita dai team ad alte performance. Lo State of DevOps Report di Google (DORA) classifica TBD come un predittore chiave di performance per i team di ingegneria. Team come Google, Meta, Microsoft (per parti di codebase) e Uber lo adottano su scala massiva.

Il principio fondamentale: il codice deve essere integrato nel trunk (main) il più rapidamente possibile. Branch di lunga durata sono proibiti. Le feature incomplete vengono nascoste da feature flag.

### Architettura dei Branch

```
Tutti committano direttamente su main (trunk) o con branch brevissimi (< 1 giorno).

Branch permanente:
└── main (trunk)       → Tutti committano qui

Branch temporanei (opzionali):
└── short-lived/*      → Durata massima: 1-2 giorni
    → Da main, merge in main (no long-lived branch!)

Release branch (opzionale):
└── release/*          → Creato dal trunk per release specifiche
    → Solo cherry-pick di fix, nessuna feature

Feature Flags:
- Le feature incomplete vengono nascoste dietro flag
- Il codice è in produzione ma non attivo
- Si attiva la feature quando pronta

Regole:
- Branch vivono massimo 1-2 giorni
- Commit piccoli e frequenti (< 200 righe per commit)
- Feature flags per funzionalità incomplete
- CI/CD obbligatorio (test automatici su ogni commit)
- Nessun branch develop
```

### Workflow Pratico Completo

```bash
# ─── COMMIT DIRETTO SUL TRUNK (modifiche piccole) ───

git switch main
git pull --rebase origin main

# Modifica piccola e auto-contenuta
git add src/config.js
git commit -m "chore: aggiornare URL endpoint analytics"
git push origin main

# ─── SHORT-LIVED BRANCH (modifiche più grandi, max 1-2 giorni) ───

git switch main
git pull --rebase origin main
git switch -c add-dashboard-api

# Sviluppo — max 1-2 giorni
git add src/api/dashboard.js tests/api/dashboard.test.js
git commit -m "feat(api): aggiungere endpoint dashboard con feature flag"

# Push e PR
git push -u origin add-dashboard-api
gh pr create --title "feat(api): endpoint dashboard" --body "Behind feature flag DASHBOARD_V2"

# Merge entro il giorno — squash merge per cronologia pulita
gh pr merge --squash --delete-branch

# ─── RELEASE BRANCH (per release specifiche) ───

# Creare un release branch dal trunk
git switch main
git switch -c release/2.5

# Solo cherry-pick di fix critici dal trunk
git cherry-pick -x abc1234  # Fix critico
git cherry-pick -x def5678  # Altro fix

# Tag e deploy
git tag -a v2.5.0 -m "Release 2.5.0"
git push origin release/2.5 --tags

# I fix vengono fatti PRIMA nel trunk, POI cherry-pickati nella release
```

### Prerequisiti per TBD

TBD richiede maturità tecnica e culturale:

1. **CI/CD robusto**: ogni commit deve essere testato in < 10 minuti
2. **Feature flag system**: LaunchDarkly, Flagsmith, Unleash, o custom
3. **Trunk guard**: pre-commit checks, linting automatico
4. **Cultura del commit piccolo**: il team deve saper scomporre il lavoro
5. **Code review rapida**: review in < 4 ore, non in giorni

```bash
# Verifica: il team è pronto per TBD?

# Tempo medio di CI pipeline
gh api repos/{owner}/{repo}/actions/runs \
  --jq '.workflow_runs[:20] | [.[].run_duration_ms] | add / length / 1000'
# Ideale: < 600 secondi (10 min)

# Età media dei branch attivi
git for-each-ref --sort=committerdate --format='%(committerdate:relative) %(refname:short)' refs/remotes/origin/ \
  | grep -v HEAD | tail -20
# Ideale: nessun branch > 2 giorni

# Frequenza di deploy
gh api repos/{owner}/{repo}/deployments --jq 'length'
# Ideale: > 5 deploy al giorno
```

---

## GitLab Flow

### Teoria e Contesto

GitLab Flow è un compromesso tra la semplicità di GitHub Flow e la struttura di GitFlow. Introduce il concetto di **environment branches**: branch che rappresentano ambienti (staging, production) dove il codice viene promosso progressivamente.

### Variante con Environment Branches

```
Combina la semplicità di GitHub Flow con la gestione degli ambienti.

Branch permanenti:
├── main               → Sviluppo (come develop in GitFlow)
├── staging            → Ambiente di pre-produzione (merge da main)
└── production         → Produzione (merge da staging)

Workflow:
1. Feature branch da main → PR in main
2. main auto-deploy su ambiente di sviluppo
3. Merge main → staging per test di pre-produzione
4. Merge staging → production per rilascio in produzione

Promozione unidirezionale:
  main → staging → production
  (il codice fluisce solo in una direzione)
```

```bash
# Feature sviluppata e mergiata in main
git switch main
git pull
git switch -c feature/new-api
# ... sviluppo ...
git push -u origin feature/new-api
gh pr create --base main --title "feat: new API endpoint"
# Dopo review: merge in main

# Promuovere a staging
git switch staging
git merge --no-ff main -m "chore: promuovere a staging per test"
git push origin staging
# → Deploy automatico su ambiente staging
# → QA team testa

# Promuovere a production dopo test superati
git switch production
git merge --no-ff staging -m "release: promuovere a produzione"
git tag -a v1.5.0 -m "Release 1.5.0"
git push origin production --tags
# → Deploy automatico in produzione
```

### Variante con Release Branches

```
Per prodotti con versioni multiple mantenute.

Branch permanenti:
├── main               → Sviluppo corrente
├── release/1.x        → Branch per versione 1.x (manutenzione)
├── release/2.x        → Branch per versione 2.x (attuale)
└── release/3.x        → Branch per versione 3.x (prossima)

Flusso dei fix:
1. Fix applicato su main (sviluppo corrente)
2. Cherry-pick nelle release branch supportate
3. Tag per ogni release: v2.3.1, v1.15.2, ecc.
```

```bash
# Fix applicato prima su main
git switch main
git add src/fix.js
git commit -m "fix: correggere parsing date per timezone negativi"
git push origin main

# Cherry-pick nelle release supportate
git switch release/2.x
git cherry-pick -x $(git rev-parse main)
git tag -a v2.3.1 -m "Patch 2.3.1: fix parsing date"
git push origin release/2.x --tags

git switch release/1.x
git cherry-pick -x $(git rev-parse main~0)
git tag -a v1.15.2 -m "Patch 1.15.2: fix parsing date"
git push origin release/1.x --tags
```

---

## Release Branching

### Strategia di Release Branching Dettagliata

Il release branching è una tecnica trasversale usata in GitFlow, GitLab Flow e talvolta anche in TBD. Serve a isolare il processo di preparazione di una release dal flusso continuo di sviluppo.

### Modello "Release Train"

Il modello Release Train prevede release a cadenza fissa (es. ogni 2 settimane). Ogni "treno" parte a prescindere da cosa sia pronto — le feature che non sono complete aspettano il treno successivo.

```
Sprint 1         Sprint 2         Sprint 3
   │                │                │
   ▼                ▼                ▼
──────────────────────────────────────────── main
   │                │                │
   ├─ release/1.0   ├─ release/1.1   ├─ release/1.2
   │   ↓              │   ↓              │   ↓
   │  v1.0.0          │  v1.1.0          │  v1.2.0
   │  v1.0.1 (patch)  │                  │

Regole del Release Train:
- La release branch viene creata in una data fissa
- Solo fix critici vengono aggiunti alla release branch
- Le feature non pronte aspettano la release successiva
- La release branch vive massimo 1 settimana
```

```bash
# Creare la release branch alla data prevista
git switch main
git pull origin main
git switch -c release/1.3.0

# Release engineer: solo bug fix da qui in poi
git cherry-pick -x abc1234  # Fix critico dalla main

# Version bump
echo "1.3.0" > VERSION
git add VERSION
git commit -m "chore: bump version a 1.3.0"

# Finalizzare
git tag -a v1.3.0 -m "Release 1.3.0"
git switch main
git merge --no-ff release/1.3.0
git push origin main --tags
git branch -d release/1.3.0
```

### Modello "Release on Demand"

A differenza del Release Train, il Release on Demand non ha cadenza fissa. La release avviene quando un set di feature è pronto e testato.

```bash
# Decidere cosa includere nella release
gh pr list --state merged --base main --search "label:release-1.4" \
  --json number,title --jq '.[] | "#\(.number): \(.title)"'

# Creare la release branch con un commit specifico
git switch -c release/1.4.0 $(git rev-parse main)

# Stabilizzare e rilasciare
# ... stesse attività del Release Train ...
```

---

## Feature Flags vs Feature Branches

### Il Dilemma Fondamentale

Feature branch e feature flag risolvono lo stesso problema — isolare codice non pronto — con approcci opposti:

| Aspetto | Feature Branch | Feature Flag |
|---------|---------------|--------------|
| Isolamento | A livello di VCS (branch separato) | A livello di runtime (codice disattivato) |
| Integrazione | Al merge | Immediata (codice nel trunk) |
| Rischio merge | Alto (cresce con il tempo) | Zero (codice già integrato) |
| Complessità codice | Nessuna aggiunta | Condizionali nel codice |
| Testabilità | Testato in isolamento | Testato nel contesto completo |
| Rollback | Revert del merge commit | Toggle del flag |
| Pulizia | Branch eliminato dopo merge | Flag e codice morto da rimuovere |
| Progressività | Tutto o niente | Canary, % rollout, A/B test |

### Feature Flag: Implementazione

```javascript
// Esempio semplice di feature flag
const flags = {
  DASHBOARD_V2: process.env.FEATURE_DASHBOARD_V2 === 'true',
  NEW_CHECKOUT: process.env.FEATURE_NEW_CHECKOUT === 'true',
};

// Uso nel codice
if (flags.DASHBOARD_V2) {
  renderDashboardV2();
} else {
  renderDashboardV1();
}

// Con un SDK come LaunchDarkly o Unleash
const ldClient = LaunchDarkly.init(sdkKey);
const showNewFeature = await ldClient.variation('new-checkout', user, false);
```

### Strategie di Rollout con Feature Flags

```
1. Kill Switch (on/off globale)
   → Attivare/disattivare la feature per tutti gli utenti
   → Uso: deploy rapido con possibilità di rollback istantaneo

2. Percentage Rollout (graduale)
   → Attivare per il 1%, poi 5%, poi 25%, poi 50%, poi 100%
   → Uso: ridurre il blast radius di bug

3. User Targeting (per utente)
   → Attivare per utenti specifici (beta tester, team interno)
   → Uso: testing in produzione

4. Ring-based Rollout (per anello)
   → Ring 0: sviluppatori interni
   → Ring 1: beta tester
   → Ring 2: utenti early adopter
   → Ring 3: tutti gli utenti
   → Uso: Microsoft usa questo modello per Windows

5. A/B Testing
   → Mostrare versione A al 50% e versione B al 50%
   → Uso: decisioni basate su dati
```

### Lifecycle dei Feature Flags

```bash
# I feature flag devono avere un ciclo di vita definito
# Altrimenti diventano debito tecnico

# 1. CREAZIONE
# Documentare: nome, owner, scadenza prevista, cleanup ticket
# Ticket JIRA/GitHub Issue per il cleanup

# 2. ROLLOUT
# Progressivo: 0% → 1% → 10% → 50% → 100%
# Monitorare metriche a ogni step

# 3. STABILIZZAZIONE
# Il flag è al 100% per almeno 1 settimana senza problemi

# 4. CLEANUP (critico!)
# Rimuovere il flag, il codice del percorso vecchio, e i test condizionali
git add src/ tests/
git commit -m "chore: rimuovere feature flag DASHBOARD_V2 e codice legacy"

# Trovare flag non puliti (tech debt)
grep -rn "FEATURE_" src/ --include="*.ts" --include="*.js" | \
  awk -F: '{print $2}' | sort | uniq -c | sort -rn
```

---

## Branch Protection Rules

### Configurazione Completa

Le branch protection rules impediscono modifiche non autorizzate ai branch critici. Sono essenziali in qualsiasi strategia di branching.

```bash
# Configurare protezione completa per main
gh api repos/{owner}/{repo}/branches/main/protection -X PUT \
  --input - << 'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["ci/build", "ci/test", "ci/lint", "security/codeql"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 2,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
```

### Opzioni delle Branch Protection Rules

| Opzione | Descrizione | Quando Usare |
|---------|-------------|-------------|
| `required_status_checks.strict` | Branch deve essere aggiornato con base prima del merge | Sempre — previene la "race condition" del CI |
| `required_approving_review_count` | Numero minimo di approvazioni | 1 per team piccoli, 2+ per team grandi |
| `dismiss_stale_reviews` | Invalidare approvazioni dopo nuovi push | Sempre — previene l'approvazione di codice non revisionato |
| `require_code_owner_reviews` | Approvazione dei CODEOWNERS obbligatoria | Quando si usa CODEOWNERS |
| `require_last_push_approval` | Chi fa l'ultimo push non può auto-approvare | Sempre — previene bypass |
| `required_linear_history` | Solo squash o rebase merge | Per cronologia lineare |
| `allow_force_pushes` | Permettere force push | Mai su branch protetti |
| `required_conversation_resolution` | Tutte le conversazioni devono essere risolte | Consigliato |
| `enforce_admins` | Applicare le regole anche agli admin | Consigliato (fiducia nei processi, non nelle persone) |

### Protezione per Strategia di Branching

```bash
# ─── GITHUB FLOW: protezione su main ───
# - Richiede PR + 1 review + CI
# - Squash merge per cronologia lineare
# - Auto-delete dei branch dopo merge

# ─── GIT FLOW: protezione su main E develop ───
# main:
# - Richiede PR + 2 review + CI + CODEOWNERS
# - Solo merge commit (--no-ff)
# - Nessun force push
# develop:
# - Richiede PR + 1 review + CI
# - Squash o merge commit

# ─── TRUNK-BASED: protezione su main con bypass CI ───
# main:
# - Richiede CI passing
# - Commit diretti permessi (o PR senza review per branch < 1 giorno)
# - Nessun force push

# ─── GITLAB FLOW: protezione su main + staging + production ───
# production:
# - Richiede PR + 2 review + CI + approval manuale
# - Solo merge da staging
# staging:
# - Richiede PR + 1 review + CI
# - Solo merge da main
# main:
# - Richiede PR + 1 review + CI
```

### Rulesets (Alternativa Moderna)

I rulesets (introdotti nel 2023) sono più flessibili delle branch protection rules tradizionali. Supportano pattern multipli, regole a livello di organizzazione e validazione dei pattern di commit message.

```bash
# Creare un ruleset per tutti i branch di release
gh api repos/{owner}/{repo}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Release Branch Protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main", "refs/heads/release/**"],
      "exclude": []
    }
  },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "required_status_checks": [
          { "context": "ci/build" },
          { "context": "ci/test" }
        ]
      }
    },
    {
      "type": "commit_message_pattern",
      "parameters": {
        "operator": "must_match",
        "pattern": "^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\\(.+\\))?: .+"
      }
    }
  ]
}
EOF
```

---

## Merge Strategies: Merge Commit, Squash, Rebase

### Le Tre Strategie a Confronto

Quando un feature branch viene integrato in main, ci sono tre modi di farlo. Ogni strategia produce una cronologia diversa.

### Merge Commit (`--no-ff`)

Crea un commit di merge che ha due parent. Preserva la topologia completa del branch.

```bash
git switch main
git merge --no-ff feature/auth -m "Merge feature: autenticazione OAuth2"

# Cronologia risultante:
# main: A─B─C───────M
#             \     /
# feature:    D─E─F

# Vantaggi:
# - Contesto preservato: si vede dove il branch è iniziato e finito
# - Revert facile: git revert -m 1 <merge-commit>
# - Bisect funziona bene con il contesto

# Svantaggi:
# - Cronologia non lineare (più difficile da leggere con git log)
# - Ogni merge commit è "rumore" nella cronologia
```

### Squash Merge

Comprime tutti i commit del feature branch in un singolo commit su main. Nessun merge commit.

```bash
git switch main
git merge --squash feature/auth
git commit -m "feat(auth): implementare autenticazione OAuth2

- Login con Google e GitHub
- Validazione token JWT
- Middleware Express per protezione route
- Test unitari e di integrazione"

# Cronologia risultante:
# main: A─B─C─S (S = singolo commit con tutte le modifiche)

# Vantaggi:
# - Cronologia lineare e pulita
# - Ogni commit in main rappresenta una feature/fix completa
# - Facilita bisect e blame

# Svantaggi:
# - Perde la cronologia dettagliata dei singoli commit
# - Non adatto per feature branch con commit di valore storico
# - L'autore del commit è chi fa il merge, non chi ha scritto il codice
```

### Rebase Merge

Riapplica i commit del feature branch sopra main, creando nuovi commit con hash diversi. Produce una cronologia lineare mantenendo i singoli commit.

```bash
git switch feature/auth
git rebase main
git switch main
git merge --ff-only feature/auth

# Cronologia risultante:
# main: A─B─C─D'─E'─F'

# Vantaggi:
# - Cronologia lineare
# - Singoli commit preservati
# - Bisect funziona bene

# Svantaggi:
# - Hash dei commit cambiano (problematico per branch condivisi)
# - Nessun contesto su dove il branch è iniziato/finito
# - Se ci sono conflitti, vanno risolti commit per commit
```

### Matrice Decisionale

| Criterio | Merge Commit | Squash | Rebase |
|----------|-------------|--------|--------|
| Cronologia | Non lineare | Lineare | Lineare |
| Commit preservati | Tutti + merge | Uno solo | Tutti (nuovi hash) |
| Contesto branch | Preservato | Perso | Perso |
| Revert della feature | `git revert -m 1` | `git revert` | Multipli revert |
| Complessità | Bassa | Bassa | Media |
| Per feature branch | Ideale (con `--no-ff`) | Ideale per branch brevi | Ideale per branch personali |
| Per branch condivisi | Unica opzione sicura | OK | Pericoloso |

### Configurazione nel Repository

```bash
# Permettere solo squash merge (cronologia lineare forzata)
gh repo edit --enable-merge-commit=false
gh repo edit --enable-squash-merge=true
gh repo edit --enable-rebase-merge=false

# Permettere solo merge commit (contesto preservato)
gh repo edit --enable-merge-commit=true
gh repo edit --enable-squash-merge=false
gh repo edit --enable-rebase-merge=false

# Permettere tutte le strategie (flessibilità per il team)
gh repo edit --enable-merge-commit=true
gh repo edit --enable-squash-merge=true
gh repo edit --enable-rebase-merge=true

# Configurare il messaggio di squash merge
gh api repos/{owner}/{repo} -X PATCH \
  -f squash_merge_commit_title="PR_TITLE" \
  -f squash_merge_commit_message="PR_BODY"
```

---

## Cherry-Pick Workflows

### Hotfix in Produzione

Il caso d'uso più comune del cherry-pick nelle strategie di branching è portare un fix critico da develop/main a un release branch o direttamente in produzione.

```bash
# Scenario: bug critico scoperto in produzione
# Il fix viene sviluppato su develop e cherry-pickato in main

# 1. Fix su develop
git switch develop
git switch -c bugfix/critical-payment-error
# ... fix ...
git add src/payments/processor.js
git commit -m "fix(payments): correggere calcolo IVA per importi > 10000"
git push -u origin bugfix/critical-payment-error
gh pr create --base develop --title "fix(payments): calcolo IVA errato"
# ... review, merge in develop ...

# 2. Identificare il commit del fix
git log --oneline develop -5
# abc1234 fix(payments): correggere calcolo IVA per importi > 10000

# 3. Cherry-pick in main/production
git switch main
git cherry-pick -x abc1234
# Il flag -x aggiunge "(cherry picked from commit abc1234)" al messaggio

# 4. Tag e deploy
git tag -a v3.2.1 -m "Hotfix: correzione calcolo IVA"
git push origin main --tags
```

### Backporting a Versioni Precedenti

```bash
# Scenario: fix necessario nelle versioni 2.x e 1.x ancora supportate

# Fix committato su main (versione 3.x)
git log --oneline main -1
# def5678 fix: correggere vulnerabilità path traversal

# Backport a release/2.x
git switch release/2.x
git cherry-pick -x def5678
# Risolvere eventuali conflitti (API diverse tra versioni)
git tag -a v2.15.1 -m "Security patch: path traversal"
git push origin release/2.x --tags

# Backport a release/1.x
git switch release/1.x
git cherry-pick -x def5678
# Più conflitti probabili per differenze maggiori
git tag -a v1.30.1 -m "Security patch: path traversal"
git push origin release/1.x --tags
```

### Costruire una Release da Cherry-Pick

In alcune organizzazioni, la release branch viene costruita selezionando commit specifici dal trunk (modello "pick the cherries").

```bash
# Creare release branch vuoto da un tag stabile
git switch -c release/2.0.0 v1.9.0

# Selezionare i commit da includere
git cherry-pick -x commit1 commit2 commit3

# Oppure un range
git cherry-pick -x v1.9.0..feature-ready-commits

# Verificare e rilasciare
npm test
git tag -a v2.0.0 -m "Release 2.0.0"
git push origin release/2.0.0 --tags
```

---

## Monorepo Branching

### La Sfida del Branching in Monorepo

In un monorepo, un singolo repository contiene multipli progetti/servizi. Le strategie di branching standard devono essere adattate perché:

1. Un feature branch potrebbe toccare solo 1 servizio su 20
2. La CI deve essere selettiva (non testare tutto per ogni modifica)
3. Le release possono essere indipendenti per servizio
4. CODEOWNERS è essenziale per la governance

### Strategie Specifiche per Monorepo

```bash
# Struttura tipica monorepo
monorepo/
├── apps/
│   ├── frontend/          # Deploy indipendente
│   ├── api/               # Deploy indipendente
│   └── admin/             # Deploy indipendente
├── libs/
│   ├── shared-ui/         # Libreria condivisa
│   ├── auth/              # Libreria condivisa
│   └── utils/             # Libreria condivisa
├── infrastructure/
│   ├── terraform/
│   └── kubernetes/
└── tools/
    └── scripts/
```

### Trunk-Based con Affected Analysis

La strategia più comune per monorepo è Trunk-Based Development con affected analysis (Nx, Turborepo, Bazel). Solo i progetti impattati da una modifica vengono testati e deployati.

```bash
# Determinare i progetti affetti da una modifica
npx nx affected --target=test --base=origin/main --head=HEAD
# Solo i progetti che dipendono dai file modificati vengono testati

# GitHub Actions con affected analysis
# .github/workflows/ci.yml
```

```yaml
# CI per monorepo con affected analysis
name: CI
on:
  pull_request:
    branches: [main]

jobs:
  affected:
    runs-on: ubuntu-latest
    outputs:
      affected-projects: ${{ steps.affected.outputs.projects }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Necessario per il confronto
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - id: affected
        run: |
          AFFECTED=$(npx nx show projects --affected --base=origin/main --head=HEAD --json)
          echo "projects=$AFFECTED" >> "$GITHUB_OUTPUT"

  test:
    needs: affected
    if: needs.affected.outputs.affected-projects != '[]'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx nx affected --target=test --base=origin/main --head=HEAD
```

### CODEOWNERS per Monorepo

```
# .github/CODEOWNERS per monorepo

# Default
*                               @platform-team

# App specifiche
/apps/frontend/                 @frontend-team
/apps/api/                      @backend-team
/apps/admin/                    @admin-team

# Librerie condivise (richiedono approvazione di più team)
/libs/shared-ui/                @frontend-team @design-system-team
/libs/auth/                     @security-team @backend-team
/libs/utils/                    @platform-team

# Infrastruttura
/infrastructure/                @devops-team @security-team

# Configurazione critica
/nx.json                        @platform-team
/package.json                   @platform-team
/.github/                       @platform-team @devops-team
```

---

## Confronto Strategie

| Aspetto | GitFlow | GitHub Flow | Trunk-Based | GitLab Flow |
|---------|---------|-------------|-------------|-------------|
| Complessità | Alta | Bassa | Media | Media |
| Branch permanenti | 2 (main+develop) | 1 (main) | 1 (main) | 2-3 |
| Vita feature branch | Giorni/settimane | Ore/giorni | Ore (max 1-2 gg) | Ore/giorni |
| Frequenza release | Schedulate | Continuo | Continuo | Continuo/schedulato |
| Feature flags | Non necessari | Opzionali | Necessari | Opzionali |
| Team size ideale | Grande (10+) | Piccolo-medio | Qualsiasi (con maturità) | Medio |
| Versioni multiple | Sì | No | Via release branch | Sì (con branch) |
| Curva apprendimento | Alta | Bassa | Media | Media |
| CI/CD richiesta | Consigliata | Obbligatoria | Obbligatoria (veloce) | Obbligatoria |
| Rollback | Revert/hotfix | Revert PR | Feature flag / revert | Revert |
| DORA metrics | Basse | Medie-alte | Alte | Medie |

### Albero Decisionale

```
Hai bisogno di supportare versioni multiple in produzione?
├── SÌ → Il prodotto è software distribuito (app, librerie, on-premise)?
│        ├── SÌ → GitFlow
│        └── NO → GitLab Flow (variante release branch)
└── NO → Il team deploya più volte al giorno?
         ├── SÌ → Il team ha CI in < 10 min e feature flag system?
         │        ├── SÌ → Trunk-Based Development
         │        └── NO → GitHub Flow (branch brevi)
         └── NO → Il team ha ambienti separati (staging, production)?
                  ├── SÌ → GitLab Flow (variante environment branch)
                  └── NO → GitHub Flow
```

---

## Conventional Commits

```bash
# Formato standardizzato per messaggi di commit
# Facilita: changelog automatico, semantic versioning, leggibilità

# Formato:
# <type>[scope]: <description>
#
# [optional body]
#
# [optional footer]

# Tipi principali:
# feat:     → Nuova funzionalità (minor version bump)
# fix:      → Bug fix (patch version bump)
# docs:     → Solo documentazione
# style:    → Formatting, whitespace (no logic change)
# refactor: → Refactoring (no feature, no fix)
# perf:     → Miglioramento performance
# test:     → Aggiunta/modifica test
# build:    → Build system, dipendenze (npm, pip)
# ci:       → CI/CD pipeline
# chore:    → Manutenzione generica

# Esempi:
git commit -m "feat(auth): add OAuth2 login with Google"
git commit -m "fix(api): handle null response from payment gateway"
git commit -m "docs: update API documentation for v2 endpoints"
git commit -m "refactor(db): extract query builder into separate module"
git commit -m "perf(search): add index on user_email column"
git commit -m "test(auth): add integration tests for OAuth2 flow"

# BREAKING CHANGE (major version bump):
git commit -m "feat(api)!: change response format to JSON:API spec

BREAKING CHANGE: API responses now follow JSON:API specification.
Old response format is no longer supported.
Migration guide: https://docs.example.com/migration/v3"

# Multi-line con body e footer:
git commit -m "fix(auth): prevent session fixation attack

The session ID was not regenerated after successful authentication,
allowing an attacker to fixate a session ID and hijack the user's
session after login.

Now the session is destroyed and recreated with a new ID after
successful authentication.

Refs: CWE-384
Reviewed-by: security-team"

# Tool per enforcing:
# - commitlint + husky (Node.js)
# - commitizen (interactive commit helper)
# - pre-commit hook con regex validation

# Installare commitlint
npm install --save-dev @commitlint/cli @commitlint/config-conventional
echo "module.exports = { extends: ['@commitlint/config-conventional'] }" > commitlint.config.js

# Configurare husky per il pre-commit hook
npx husky init
echo "npx --no-install commitlint --edit \$1" > .husky/commit-msg
```

### Conventional Commits e Semantic Versioning

La relazione tra tipo di commit e version bump:

```
Commit Type          SemVer Bump       Esempio
─────────────────────────────────────────────────────
feat:                MINOR (1.x.0)     1.2.0 → 1.3.0
fix:                 PATCH (1.2.x)     1.2.0 → 1.2.1
perf:                PATCH             1.2.0 → 1.2.1
BREAKING CHANGE:     MAJOR (x.0.0)     1.2.0 → 2.0.0
docs, style, etc:    Nessuno           (non triggera release)
```

---

## Best Practices

### Scelta della Strategia

1. **Non cambiare strategia senza necessità**: il costo di migrazione è alto. Scegliere bene all'inizio
2. **Documentare la strategia scelta**: nel CONTRIBUTING.md, includere diagrammi e comandi concreti
3. **Adattare, non adottare ciecamente**: ogni team può personalizzare la strategia base
4. **Rivalutare periodicamente**: la strategia giusta per un team di 3 potrebbe non funzionare per un team di 30

### Igiene dei Branch

1. **Branch protection su main**: richiedere PR, review, CI passing prima del merge
2. **Nomi branch descrittivi**: `feature/user-auth`, `fix/login-timeout`, `chore/update-deps`
3. **Commit atomici**: un commit = una modifica logica. Non mescolare feature diverse
4. **Squash merge per feature branch**: mantiene la cronologia main pulita
5. **Eliminare branch dopo merge**: evitare accumulo di branch obsoleti (`gh repo edit --delete-branch-on-merge`)
6. **Rebase locale, merge nel remoto**: `git rebase main` prima di pushare feature branch
7. **Tag per ogni release**: `v1.2.3` con annotated tag e changelog
8. **PR template**: standardizzare il formato delle pull request con template

### Automazione

```bash
# Auto-delete dei branch dopo merge
gh repo edit --delete-branch-on-merge

# Configurare auto-merge per PR di Dependabot (patch only)
# .github/workflows/auto-merge-dependabot.yml
```

```yaml
name: Auto-merge Dependabot
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
      - name: Fetch Dependabot metadata
        id: metadata
        uses: dependabot/fetch-metadata@v2
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Auto-merge patch updates
        if: steps.metadata.outputs.update-type == 'version-update:semver-patch'
        run: gh pr merge "$PR_URL" --auto --squash
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Troubleshooting

### Branch Protetto Blocca il Merge

```bash
# Verificare quali check sono falliti
gh pr checks <pr-number>

# Verificare le regole di protezione
gh api repos/{owner}/{repo}/branches/main/protection

# Verificare se il branch è aggiornato con main (strict mode)
gh pr view <pr-number> --json mergeable,mergeStateStatus
# Se mergeStateStatus è "BEHIND", aggiornare il branch:
gh pr update-branch <pr-number>
```

### Branch Divergenti dopo Rebase

```bash
# Errore: "Your branch and 'origin/feature' have diverged"
# Causa: rebase locale ha creato nuovi hash

# Soluzione (solo se sei l'unico a lavorare sul branch):
git push --force-with-lease origin feature/my-branch

# Se altri lavorano sul branch, usare merge invece di rebase
git merge main  # Al posto di git rebase main
```

### Feature Branch Troppo Vecchio

```bash
# Il branch ha accumulato troppi conflitti con main

# Opzione 1: Rebase (se branch personale e < 20 commit)
git switch feature/old-branch
git rebase main
# Risolvere i conflitti commit per commit

# Opzione 2: Merge (se branch condiviso o molti conflitti)
git switch feature/old-branch
git merge main
# Risolvere tutti i conflitti in un singolo merge

# Opzione 3: Ricominciare (se i conflitti sono troppi)
git switch main
git switch -c feature/old-branch-v2
git cherry-pick commit1 commit2 commit3  # Solo i commit di valore
```

### Branch Stale: Pulizia

```bash
# Trovare branch mergiati (sicuri da eliminare)
git branch --merged main | grep -v "main\|develop"

# Eliminare branch mergiati locali
git branch --merged main | grep -v "main\|develop" | xargs git branch -d

# Eliminare branch mergiati remoti
git branch -r --merged origin/main | grep -v "main\|develop" | \
  sed 's/origin\///' | xargs -I {} git push origin --delete {}

# Pulizia referenze remote stale
git remote prune origin
git fetch --prune
```

---

## Release Flow (Microsoft)

### Origini e Filosofia

Release Flow è la strategia di branching adottata internamente da Microsoft per lo sviluppo di Azure DevOps (precedentemente VSTS) e di altri prodotti su larga scala. È un ibrido tra Trunk-Based Development e release branching schedulato, progettato per combinare la velocità di integrazione del trunk con la stabilità delle release controllate.

Il principio fondamentale di Release Flow si articola in tre fasi distinte: **Ship** (integrare il codice nel trunk), **Deploy** (rilasciare il codice negli ambienti) e **Expose** (rendere la funzionalità visibile agli utenti). Queste tre fasi sono deliberatamente disaccoppiate grazie ai feature flag.

### Architettura dei Branch

```
Release Flow: trunk + release branch schedulati.

Branch permanente:
└── main (trunk)       → Tutti sviluppano qui

Branch temporanei:
├── topic/*            → Branch brevi per ogni contribuzione (ore/giorni)
└── release/*          → Creati ogni sprint (es. ogni 3 settimane)

Ciclo di vita:
1. Sviluppatore crea topic branch da main
2. Commit piccoli e frequenti
3. PR con review + CI checks
4. Merge in main (squash)
5. Ogni sprint: creare release branch da main
6. Solo cherry-pick di hotfix dalla main alla release
7. Deploy della release branch in produzione
8. Feature flag controllano l'esposizione

Differenze chiave rispetto a TBD puro:
- Release branch esistono (in TBD puro non necessariamente)
- Sprint-based: release branch create a cadenza regolare
- Cherry-pick: fix sviluppati su main, poi portati nella release

Differenze chiave rispetto a GitFlow:
- NO branch develop separato
- NO feature branch di lunga durata
- Feature flag invece di feature branch per isolamento
- Un solo branch permanente (main)
```

### Workflow Pratico

```bash
# ─── SVILUPPO QUOTIDIANO ───

# Creare un topic branch da main
git switch main
git pull --rebase origin main
git switch -c users/renan/fix-api-timeout

# Sviluppo rapido — il branch vive ore, non giorni
git add src/api/client.js
git commit -m "fix(api): aumentare timeout a 30s per endpoint lenti"

# Push e PR
git push -u origin users/renan/fix-api-timeout
gh pr create --base main \
  --title "fix(api): timeout endpoint" \
  --body "Aumentato timeout da 5s a 30s per gestire endpoint con latenza alta."

# Dopo review → squash merge in main
gh pr merge --squash --delete-branch


# ─── SPRINT RELEASE (ogni 3 settimane) ───

# Il release manager crea il branch di release
git switch main
git pull origin main
git switch -c release/sprint-145

# Nessuna feature viene aggiunta alla release branch
# Solo cherry-pick di fix critici da main

# Fix critico scoperto dopo la creazione della release
git switch main
git add src/critical-fix.js
git commit -m "fix: correggere race condition nel job scheduler"
git push origin main

# Cherry-pick nella release branch
git switch release/sprint-145
git cherry-pick -x $(git log --oneline main -1 --format="%H")
git push origin release/sprint-145

# Deploy della release
git tag -a v2024.sprint145.1 -m "Sprint 145 Release"
git push origin release/sprint-145 --tags


# ─── HOTFIX IN PRODUZIONE ───

# Fix sviluppato PRIMA su main
git switch main
git add src/hotfix.js
git commit -m "fix(security): sanitizzare header X-Forwarded-For"
git push origin main

# Poi cherry-pickato nella release attiva in produzione
git switch release/sprint-145
git cherry-pick -x <commit-hash>
git tag -a v2024.sprint145.2 -m "Hotfix: sanitizzazione header"
git push origin release/sprint-145 --tags
```

### Ship, Deploy, Expose — Il Pattern di Disaccoppiamento

Il vero valore di Release Flow sta nella separazione tra tre concetti che spesso vengono confusi:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHIP (Integrare)                              │
│  Il codice viene mergiato nel trunk continuamente.              │
│  Include codice per feature incomplete, protetto da flag.       │
│  Frequenza: multipla al giorno.                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DEPLOY (Rilasciare)                           │
│  Il codice viene deployato negli ambienti tramite release       │
│  branch. Il codice è in produzione ma non necessariamente       │
│  visibile agli utenti.                                          │
│  Frequenza: ogni sprint (2-3 settimane).                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXPOSE (Esporre)                              │
│  Le feature vengono rese visibili agli utenti tramite           │
│  feature flag. Rollout progressivo: 1% → 10% → 50% → 100%.    │
│  Frequenza: indipendente dal deploy. Può avvenire giorni        │
│  o settimane dopo il deploy.                                    │
└─────────────────────────────────────────────────────────────────┘
```

Questo pattern permette a Microsoft di deployare codice in produzione ogni sprint mantenendo il rischio basso: se una feature causa problemi, il flag viene spento senza richiedere un rollback del deploy.

### Quando Usare Release Flow

Release Flow è indicato quando:

- Il team è grande (50+ sviluppatori) e ha bisogno di una strategia scalabile
- Le release avvengono su cadenza fissa (sprint) ma non necessariamente in continuo
- Si vuole la velocità di integrazione del trunk senza rinunciare alla stabilità delle release branch
- Il prodotto è un servizio cloud con deploy regolari ma non continui
- Esiste un sistema di feature flag maturo

Non è indicato quando:

- Il team è piccolo e deploya continuamente (GitHub Flow è sufficiente)
- Non esiste un'infrastruttura di feature flag
- Il prodotto richiede versioni multiple simultanee (GitFlow è più adatto)

---

## Stacked PRs e Stacked Diffs

### Il Problema delle PR Monolitiche

Le Pull Request grandi sono uno dei principali colli di bottiglia nello sviluppo software. Una PR con 2.000 righe di modifiche richiede ore di review, accumula commenti, attraversa cicli multipli di revisione e spesso finisce per essere approvata con un "LGTM" superficiale perché il reviewer è sopraffatto dalla dimensione.

Studi interni di aziende come Meta e Uber hanno dimostrato che il tempo di review cresce in modo più che lineare con la dimensione della PR:

```
Dimensione PR (righe)    Tempo medio di review    Qualità review
─────────────────────────────────────────────────────────────────
< 50 righe               15 minuti                Alta
50-200 righe             45 minuti                Media-alta
200-500 righe            2-3 ore                  Media
500-1000 righe           4-8 ore                  Bassa
> 1000 righe             1-3 giorni               Molto bassa
```

### Cos'è lo Stacking

Lo stacking (o stacked diffs, stacked PRs) è una metodologia di lavoro in cui una feature grande viene scomposta in una serie di PR piccole e dipendenti, impilate l'una sull'altra. Ogni PR nella "pila" (stack) si basa sulla PR precedente e può essere revisionata e approvata indipendentemente.

```
Workflow tradizionale:                Workflow con stacking:

main ─────────────────── main        main ─────────────────── main
  └── feature/big-change               ├── stack/1-add-schema
       (2000 righe, 1 PR)              ├── stack/2-add-api (basata su 1)
                                        ├── stack/3-add-ui (basata su 2)
                                        └── stack/4-add-tests (basata su 3)
                                        (4 PR da ~500 righe ciascuna)
```

### Come Funziona in Pratica

```bash
# ─── CREARE UNO STACK MANUALMENTE (senza tool) ───

# PR 1: Schema del database
git switch main && git pull
git switch -c stack/1-add-user-schema
git add migrations/
git commit -m "feat(db): aggiungere schema tabella utenti"
git push -u origin stack/1-add-user-schema
gh pr create --base main --title "feat(db): schema utenti [1/4]"

# PR 2: API endpoints (basata sulla PR 1)
git switch -c stack/2-add-user-api  # parte da stack/1
git add src/api/users/
git commit -m "feat(api): aggiungere endpoint CRUD utenti"
git push -u origin stack/2-add-user-api
gh pr create --base stack/1-add-user-schema \
  --title "feat(api): endpoint utenti [2/4]" \
  --body "Dipende da #123 (schema utenti)"

# PR 3: UI (basata sulla PR 2)
git switch -c stack/3-add-user-ui
git add src/components/users/
git commit -m "feat(ui): aggiungere pagina gestione utenti"
git push -u origin stack/3-add-user-ui
gh pr create --base stack/2-add-user-api \
  --title "feat(ui): pagina utenti [3/4]"

# PR 4: Test E2E (basata sulla PR 3)
git switch -c stack/4-add-user-tests
git add tests/e2e/users/
git commit -m "test(e2e): aggiungere test end-to-end per flusso utenti"
git push -u origin stack/4-add-user-tests
gh pr create --base stack/3-add-user-ui \
  --title "test(e2e): test utenti [4/4]"


# ─── QUANDO UNA PR NELLO STACK VIENE AGGIORNATA ───

# Se la PR 1 riceve feedback e viene modificata,
# tutte le PR successive devono essere rebasate

git switch stack/1-add-user-schema
# ... applicare modifiche richieste dal reviewer ...
git add migrations/
git commit -m "fix(db): correggere tipo colonna email"
git push origin stack/1-add-user-schema

# Rebase della PR 2 sulla PR 1 aggiornata
git switch stack/2-add-user-api
git rebase stack/1-add-user-schema
git push --force-with-lease origin stack/2-add-user-api

# Rebase della PR 3 sulla PR 2 aggiornata
git switch stack/3-add-user-ui
git rebase stack/2-add-user-api
git push --force-with-lease origin stack/3-add-user-ui

# E così via per la PR 4...


# ─── MERGE DELLO STACK ───

# Le PR vengono mergiate in ordine, dal basso verso l'alto
# PR 1 → merge in main
# PR 2 → aggiornare base a main, merge in main
# PR 3 → aggiornare base a main, merge in main
# PR 4 → aggiornare base a main, merge in main
```

### Strumenti per lo Stacking

Il rebase manuale dello stack è tedioso e soggetto a errori. Esistono strumenti dedicati che automatizzano il processo:

```bash
# ─── GRAPHITE (il più popolare per GitHub) ───

# Installazione
npm install -g @withgraphite/graphite-cli

# Creare un branch nello stack
gt branch create stack/1-schema
# ... modifiche ...
gt commit create -m "feat(db): schema utenti"

gt branch create stack/2-api    # automaticamente basato su stack/1
# ... modifiche ...
gt commit create -m "feat(api): endpoint utenti"

# Sottomettere tutto lo stack come PR
gt stack submit
# Crea tutte le PR con le dipendenze corrette

# Quando una PR viene aggiornata, rebase automatico dello stack
gt stack restack


# ─── GitHub CLI Nativo (gh-stack, 2026) ───

# GitHub ha introdotto supporto nativo per stacked PRs
# tramite l'estensione gh-stack

gh extension install github/gh-stack

# Sincronizzare tutto lo stack dopo una modifica
gh stack sync
# Rebase a cascata su tutto lo stack + force-push atomico

# Visualizzare lo stato dello stack
gh stack status


# ─── ALTRI STRUMENTI ───

# spr (Stacked Pull Requests) — Go-based, leggero
# git-town — gestione branch con workflow integrati
# ReviewStack — estensione browser per visualizzare stack su GitHub
# Gerrit — supporto nativo per stacked diffs (usato da Android, Chromium)
```

### Quando Usare lo Stacking

Lo stacking è particolarmente efficace quando:

- Una feature richiede modifiche a livelli multipli dello stack (DB → API → UI → test)
- Le PR sarebbero altrimenti troppo grandi per una review efficace (> 500 righe)
- Il team pratica Trunk-Based Development e vuole mantenere branch brevi
- La code review è un collo di bottiglia e serve parallelizzare le approvazioni
- Più reviewer specializzati devono revisionare parti diverse della stessa feature

Non è indicato quando:

- Le modifiche sono piccole e auto-contenute (una PR è sufficiente)
- Il team non è familiare con rebase e la risoluzione di conflitti
- Non si hanno strumenti di automazione per la gestione dello stack

---

## Branching per Applicazioni Mobile

### Sfide Specifiche del Mobile

Lo sviluppo mobile presenta sfide uniche che influenzano la scelta della strategia di branching:

1. **App Store Review**: le release non sono istantanee. Apple e Google impiegano da ore a giorni per approvare un aggiornamento. Non esiste "deploy continuo" nel senso web
2. **Versioni multiple in produzione**: gli utenti non aggiornano tutti simultaneamente. È comune avere 3-5 versioni attive contemporaneamente
3. **Release cadence fissa**: la maggior parte dei team mobile rilascia settimanalmente o bisettimanalmente
4. **Hotfix costosi**: un hotfix richiede una nuova review dell'App Store, quindi i fix urgenti sono più lenti da distribuire
5. **Code freeze obbligatorio**: prima di ogni submission, serve un periodo di stabilizzazione

### Strategia Raccomandata: GitFlow Adattato per Mobile

```
Branch permanenti:
├── main                → Codice in produzione (ultimo rilascio approvato)
└── develop             → Integrazione continua delle feature

Branch temporanei:
├── feature/*           → Nuove funzionalità
├── release/x.y.z       → Candidata al rilascio (code freeze)
├── hotfix/*            → Fix urgenti per la versione in produzione
└── bugfix/*            → Fix non urgenti (su develop)

Calendario tipico (release bisettimanale):

Lunedì S1:     Inizio sprint, feature branch da develop
Venerdì S1:    Feature freeze — tutte le feature mergiate in develop
Lunedì S2:     Creazione release/x.y.z da develop — inizio code freeze
Mercoledì S2:  Solo bugfix sulla release branch
Giovedì S2:    Submission ad App Store / Google Play
Venerdì S2:    Release branch mergiata in main + develop, tag

Regole:
- Feature freeze: nessuna nuova feature dopo una data prestabilita
- Code freeze: solo fix critici sulla release branch
- La release branch vive massimo 1 settimana
- Hotfix: sempre da main, merge in main + develop
```

### Workflow Mobile con Code Freeze

```bash
# ─── SPRINT DI SVILUPPO ───

# Sviluppo feature su branch dedicato
git switch develop && git pull
git switch -c feature/push-notifications
# ... sviluppo per diversi giorni ...
git push -u origin feature/push-notifications
gh pr create --base develop --title "feat: notifiche push"
# Review + merge in develop prima del feature freeze

# ─── FEATURE FREEZE (Venerdì S1) ───

# Tutte le feature devono essere mergiate in develop
# Da questo momento, nessuna nuova feature entra nella release

# ─── CODE FREEZE — CREAZIONE RELEASE (Lunedì S2) ───

git switch develop && git pull
git switch -c release/3.2.0

# Version bump
# iOS: aggiornare Info.plist e .xcodeproj
# Android: aggiornare build.gradle versionCode e versionName
git add . && git commit -m "chore: bump versione a 3.2.0"

# Solo bugfix da qui in poi
git add src/fix.swift
git commit -m "fix: correggere crash su iOS 17 durante rotazione schermo"

# ─── SUBMISSION (Giovedì S2) ───

# Build finale
git tag -a v3.2.0-rc1 -m "Release Candidate 3.2.0"
# → CI/CD genera build per TestFlight e Google Play Internal Testing
# → QA verifica la RC
# → Submission ad App Store Connect e Google Play Console

# ─── DOPO APPROVAZIONE ───

git tag -a v3.2.0 -m "Release 3.2.0"
git switch main
git merge --no-ff release/3.2.0 -m "release: v3.2.0"
git switch develop
git merge --no-ff release/3.2.0 -m "chore: merge release 3.2.0 in develop"
git push origin main develop --tags
git branch -d release/3.2.0

# ─── HOTFIX (se necessario dopo il rilascio) ───

git switch main && git pull
git switch -c hotfix/3.2.1-crash-fix
git add src/fix.swift
git commit -m "fix: crash durante login con biometria su iPad"
# Version bump a 3.2.1
git tag -a v3.2.1 -m "Hotfix 3.2.1"
# → Nuova submission ad App Store (expedited review)
git switch main && git merge --no-ff hotfix/3.2.1-crash-fix
git switch develop && git merge --no-ff hotfix/3.2.1-crash-fix
git push origin main develop --tags
```

### Release Train per Mobile: il Modello Spotify

Spotify adotta un modello di Release Train settimanale per le sue applicazioni mobile. Ogni settimana viene tagliato un release branch dal trunk, indipendentemente da quali feature siano pronte. Le feature non complete aspettano il treno successivo.

```
Settimana 1       Settimana 2       Settimana 3
    │                 │                 │
    ▼                 ▼                 ▼
────────────────────────────────────────────── main (trunk)
    │                 │                 │
    ├── release/w1    ├── release/w2    ├── release/w3
    │   Submission    │   Submission    │   Submission
    │   App Store     │   App Store     │   App Store
    │                 │                 │
    │ ◄── cherry-pick fix critici      │

Vantaggi:
- Ritmo prevedibile per QA e stakeholder
- Feature non pronte non bloccano il rilascio
- Bug non critici vengono corretti nel rilascio successivo
- Cherry-pick solo per fix che non possono aspettare

Requisiti:
- Feature flag per nascondere feature incomplete
- CI/CD robusto con build automatiche per ogni piattaforma
- Processo di QA rapido (< 3 giorni dalla creazione della release branch)
```

---

## Branching e GitOps — Promozione tra Ambienti

### Il Paradigma GitOps

GitOps estende i principi di Git al deployment delle infrastrutture e delle applicazioni. In un ambiente GitOps, lo stato desiderato di ogni ambiente (sviluppo, staging, produzione) è definito in un repository Git, e un operatore (come ArgoCD o Flux) sincronizza l'ambiente reale con lo stato dichiarato nel repository.

La domanda fondamentale è: come organizzare i branch (o le directory) del repository GitOps per rappresentare ambienti multipli?

### Tre Approcci alla Promozione

#### Approccio 1: Branch per Ambiente

Ogni ambiente ha un branch dedicato. La promozione avviene tramite merge tra branch.

```
Repository GitOps:
├── branch: dev         → Ambiente di sviluppo
├── branch: staging     → Ambiente di pre-produzione
└── branch: production  → Ambiente di produzione

Promozione:
  dev → (merge/PR) → staging → (merge/PR) → production

Vantaggi:
- Modello familiare per chi conosce GitLab Flow
- PR come gate di approvazione tra ambienti
- Diff chiaro tra ambienti

Svantaggi:
- Merge conflict frequenti tra branch di ambienti
- Cherry-pick necessari per hotfix
- Difficile confrontare lo stato di due ambienti
- Le differenze tra ambienti (config) si mescolano con le versioni dell'app
```

```bash
# Promozione da dev a staging
git switch staging
git merge --no-ff dev -m "promote: promuovere a staging per test"
git push origin staging
# ArgoCD detecta il cambio e sincronizza l'ambiente staging

# Promozione da staging a production
gh pr create --base production --head staging \
  --title "promote: rilascio v2.3.0 in produzione" \
  --body "Testato in staging per 3 giorni. Tutti i test superati."
# Approvazione manuale richiesta
gh pr merge --merge
```

#### Approccio 2: Directory per Ambiente (Raccomandato)

Tutti gli ambienti sono rappresentati come directory nello stesso branch.

```
Repository GitOps (branch: main):
├── environments/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   └── values.yaml        → image: app:2.3.0-dev.45
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── values.yaml        → image: app:2.3.0-rc.2
│   └── production/
│       ├── kustomization.yaml
│       └── values.yaml        → image: app:2.2.0
├── base/
│   ├── deployment.yaml
│   └── service.yaml
└── README.md

Promozione:
  Aggiornare il tag immagine nella directory dell'ambiente target
  via PR su main

Vantaggi:
- Nessun merge conflict tra ambienti
- Confronto facile tra ambienti (diff tra file nella stessa directory)
- Separazione netta tra configurazione dell'ambiente e versione dell'app
- Un solo branch da gestire
- Audit trail completo tramite commit su main

Svantaggi:
- Meno intuitivo per chi è abituato al modello branch-per-ambiente
- Richiede convenzioni chiare su chi può modificare quale directory
```

```bash
# Promozione: aggiornare il tag immagine in staging
git switch main && git pull
git switch -c promote/staging-v2.3.0

# Aggiornare il tag dell'immagine
sed -i 's/image: app:.*/image: app:2.3.0-rc.2/' environments/staging/values.yaml
git add environments/staging/values.yaml
git commit -m "promote: app v2.3.0-rc.2 in staging"

gh pr create --base main \
  --title "promote: v2.3.0-rc.2 → staging" \
  --body "Promozione automatica dopo CI verde su dev."
# ArgoCD sincronizza dopo il merge
```

#### Approccio 3: Repository per Ambiente

Ogni ambiente ha il proprio repository GitOps. Usato in organizzazioni enterprise con requisiti di separazione dei permessi.

```
Repositories:
├── gitops-dev          → Team di sviluppo ha accesso write
├── gitops-staging      → Team QA + lead hanno accesso write
└── gitops-production   → Solo SRE e release manager hanno accesso write

Promozione:
  Script o pipeline CI copia la configurazione da un repo all'altro
  tramite PR automatiche

Vantaggi:
- Separazione dei permessi nativa tramite GitHub/GitLab
- Audit trail per ambiente
- Ideale per compliance (SOC 2, PCI-DSS)

Svantaggi:
- Overhead di gestione di repository multipli
- Duplicazione di configurazione base
- Promozione più complessa da automatizzare
```

### Matrice di Scelta per GitOps

| Criterio | Branch/Ambiente | Directory/Ambiente | Repository/Ambiente |
|----------|----------------|-------------------|---------------------|
| Complessità setup | Bassa | Media | Alta |
| Scalabilità | Media | Alta | Alta |
| Separazione permessi | Bassa | Media (CODEOWNERS) | Alta |
| Facilità promozione | Media (merge) | Alta (file update) | Bassa (cross-repo) |
| Rischio merge conflict | Alto | Basso | Nessuno |
| Compliance enterprise | Bassa | Media | Alta |
| Team consigliato | Piccolo (< 10) | Medio (10-50) | Grande (50+) o regolato |

---

## Anti-Pattern del Branching

### Anti-Pattern 1: Branch di Lunga Durata (Long-Lived Feature Branch)

Il branch vive per settimane o mesi, accumulando divergenza dal trunk. Al momento del merge, i conflitti sono talmente numerosi da richiedere giorni di lavoro per la risoluzione. Spesso si introducono bug sottili perché il contesto dell'autore è ormai parziale.

```
Sintomi:
- Branch con > 50 commit non mergiati
- Divergenza > 200 righe di diff rispetto a main
- Il developer "ha paura" di fare il merge
- Il merge richiede più di 1 ora di risoluzione conflitti

Cause:
- Feature troppo grande, non scomposta in incrementi
- Mancanza di feature flag per integrare codice incompleto
- Review lenta (giorni di attesa per approvazione)
- Cultura del "merge solo quando è perfetto"

Soluzione:
- Scomporre la feature in PR da < 200 righe
- Integrare quotidianamente nel trunk con feature flag
- Usare stacked PRs per feature multi-layer
- Review in < 4 ore (SLA di team)
```

```bash
# Diagnostica: trovare branch con divergenza pericolosa
git for-each-ref --format='%(refname:short) %(committerdate:relative) %(ahead-behind:main)' \
  refs/remotes/origin/ | sort -t' ' -k3 -rn | head -20

# Se un branch ha > 30 commit ahead di main, è in zona di pericolo
```

### Anti-Pattern 2: Merge Ceremony (Cerimonia del Merge)

Il merge diventa un evento pianificato, con riunioni dedicate, "merge days" nel calendario, e un merge manager incaricato di risolvere i conflitti. Questo indica che i branch vivono troppo a lungo e la strategia è troppo complessa per il team.

```
Sintomi:
- "Merge Friday" o "Integration Day" nel calendario del team
- Una persona dedicata a risolvere conflitti di merge
- Test manuali dopo ogni merge perché la CI non copre
- Regressioni frequenti dopo il merge

Soluzione:
- Passare a branch brevi (< 2 giorni)
- CI obbligatorio con coverage > 80%
- Merge quotidiano nel trunk, non settimanale
- Se il merge è un evento, la strategia è sbagliata
```

### Anti-Pattern 3: Branch per Ambiente (in Codice Applicativo)

Usare branch Git (dev, staging, prod) per gestire differenze tra ambienti nel codice dell'applicazione. Questo porta a divergenze permanenti tra branch che non dovrebbero mai essere mergiati l'uno nell'altro.

```
Problema:
  branch dev     → config: DATABASE_URL=localhost:5432
  branch staging → config: DATABASE_URL=staging-db.internal:5432
  branch prod    → config: DATABASE_URL=prod-db.internal:5432

I tre branch divergono permanentemente e non possono essere mergiati.
Le feature devono essere cherry-pickate in ogni branch separatamente.

Soluzione:
- Usare variabili d'ambiente o file di configurazione per ambiente
- Un singolo branch (main) con config esternalizzata
- Le differenze tra ambienti vivono in:
  - Variabili d'ambiente del runtime
  - File .env (non committati, generati dal CI/CD)
  - ConfigMap/Secrets in Kubernetes
  - Vault, AWS Secrets Manager, o simili
```

### Anti-Pattern 4: Cherry-Pick come Strategia Primaria

Affidarsi sistematicamente al cherry-pick per portare modifiche tra branch, invece di usare merge o rebase. Il cherry-pick crea commit duplicati con hash diversi, rendendo difficile tracciare quali fix sono stati applicati e dove.

```
Sintomi:
- Ogni fix viene cherry-pickato in 3-5 branch
- Difficile sapere se un fix è stato applicato ovunque
- Commit duplicati nella cronologia
- "Abbiamo già il fix nel branch X?" diventa una domanda ricorrente

Quando il cherry-pick è accettabile:
- Hotfix da main a una release branch
- Backport di security patch a versioni precedenti
- Queste sono eccezioni, non la norma

Soluzione per il flusso normale:
- Usare merge unidirezionale (main → staging → production)
- Le modifiche fluiscono sempre nella stessa direzione
- Il cherry-pick è riservato a casi eccezionali
```

### Anti-Pattern 5: Branch Orfani e Stale

Branch creati e mai mergiati, accumulati nel tempo. Il repository diventa un cimitero di branch con nomi criptici che nessuno osa eliminare perché "forse serve ancora a qualcuno".

```bash
# Diagnostica: contare i branch stale (> 90 giorni senza commit)
git for-each-ref --sort=committerdate \
  --format='%(committerdate:short) %(refname:short) %(authorname)' \
  refs/remotes/origin/ | \
  awk -v cutoff="$(date -d '90 days ago' +%Y-%m-%d)" '$1 < cutoff' | \
  wc -l

# Elencare i branch stale con autore
git for-each-ref --sort=committerdate \
  --format='%(committerdate:short) %(refname:short) %(authorname)' \
  refs/remotes/origin/ | \
  awk -v cutoff="$(date -d '90 days ago' +%Y-%m-%d)" '$1 < cutoff'

# Prevenzione:
# 1. Abilitare auto-delete dopo merge
gh repo edit --delete-branch-on-merge

# 2. Script di pulizia periodica (da eseguire settimanalmente)
# Eliminare branch remoti mergiati (escludendo main e develop)
git branch -r --merged origin/main | \
  grep -v 'main\|develop\|release' | \
  sed 's/origin\///' | \
  xargs -I {} echo "git push origin --delete {}"
# Rimuovere "echo" per eseguire effettivamente la pulizia
```

### Anti-Pattern 6: Assenza di Branch Protection

Permettere push diretti su main senza review, CI checks o altre protezioni. Un singolo commit errato può rompere la build, introdurre vulnerabilità di sicurezza o causare downtime in produzione.

```
Conseguenze:
- Commit non revisionati in produzione
- CI aggirato (il test fallisce ma il codice è già su main)
- Nessun audit trail per le modifiche
- Un developer junior può accidentalmente sovrascrivere il lavoro di altri

Anche in Trunk-Based Development:
- Servono status check obbligatori (CI deve passare)
- Branch brevi con PR sono preferibili a commit diretti
- Se il team è < 5 persone, almeno 1 review
- Se il team è > 5 persone, almeno 2 review
```

---

## Branching e Metriche DORA

### Le Quattro Metriche DORA e il Branching

Le metriche DORA (DevOps Research and Assessment), definite dal team di Google Cloud, misurano le performance di un team di ingegneria. La strategia di branching ha un impatto diretto su ciascuna di esse.

| Metrica DORA | Definizione | Impatto del Branching |
|--------------|-------------|----------------------|
| **Deployment Frequency** | Frequenza di deploy in produzione | Branch brevi e CI/CD veloce → deploy frequenti. Branch lunghi → deploy rari e rischiosi |
| **Lead Time for Changes** | Tempo dal commit al deploy in produzione | Ogni review, merge gate e ambiente aggiuntivo aggiunge latenza. Trunk-based minimizza |
| **Change Failure Rate** | Percentuale di deploy che causano incidenti | Feature flag + canary release riducono il tasso. Branch lunghi con "big bang merge" lo aumentano |
| **Failed Deployment Recovery Time** | Tempo per ripristinare il servizio dopo un incidente | Feature flag = rollback istantaneo (secondi). Senza flag = revert + rebuild + redeploy (minuti/ore) |

### Classificazione DORA per Performance Level (2025)

```
                      Elite         High          Medium        Low
                      ─────         ────          ──────        ───
Deploy Frequency      On-demand     1/settimana   1/mese        1/6 mesi
                      (multi/giorno)

Lead Time             < 1 ora       1 giorno-     1 settimana-  1 mese-
                                    1 settimana   1 mese        6 mesi

Change Failure Rate   < 5%          5-10%         10-15%        > 15%

Recovery Time         < 1 ora       < 1 giorno    < 1 settimana > 1 settimana
```

### Correlazione Strategia-Performance

```
Strategia              Performance DORA Tipica    Note
──────────────────────────────────────────────────────────────────
Trunk-Based Dev        Elite / High               Richiede CI veloce + feature flag
GitHub Flow            High / Medium              Con branch brevi (< 2 gg)
GitLab Flow            Medium / High              Dipende dalla velocità di promozione
Release Flow           High                       Con feature flag + sprint release
GitFlow                Medium / Low               Branch lunghi rallentano il ciclo
```

I team che raggiungono il livello "Elite" condividono queste caratteristiche di branching:

1. **Branch che vivono meno di 1 giorno** — integrazione quasi continua
2. **CI pipeline in meno di 10 minuti** — feedback rapido che non blocca il merge
3. **Feature flag per il decoupling deploy/release** — deploy frequente senza rischio
4. **Review in meno di 4 ore** — elimina il collo di bottiglia umano
5. **Trunk-based o branch brevissimi** — minimizza la divergenza e il merge debt

### Misurare l'Impatto della Strategia

```bash
# ─── DEPLOYMENT FREQUENCY ───
# Contare i deploy negli ultimi 30 giorni
gh api repos/{owner}/{repo}/deployments \
  --jq '[.[] | select(.created_at > "2026-04-24")] | length'

# ─── LEAD TIME FOR CHANGES ───
# Tempo medio tra primo commit della PR e merge
gh pr list --state merged --limit 50 --json createdAt,mergedAt \
  --jq '[.[] | ( (.mergedAt | fromdateiso8601) - (.createdAt | fromdateiso8601) ) / 3600] | add / length'
# Risultato in ore

# ─── CHANGE FAILURE RATE ───
# Percentuale di hotfix rispetto al totale dei deploy
TOTAL=$(gh release list --limit 50 | wc -l)
HOTFIX=$(gh release list --limit 50 | grep -ci "hotfix\|patch\|emergency")
echo "Change Failure Rate: $((HOTFIX * 100 / TOTAL))%"

# ─── BRANCH HEALTH ───
# Età media dei branch attivi
git for-each-ref --sort=-committerdate \
  --format='%(committerdate:iso)' refs/remotes/origin/ | head -20 | \
  while read date; do
    echo $(( ($(date +%s) - $(date -d "$date" +%s)) / 86400 )) giorni
  done
```

### La Nuova Metrica: Rework Rate

Il DORA Report 2025 ha introdotto una nuova metrica, il **Rework Rate**, che misura la percentuale di modifiche che richiedono ulteriori correzioni entro un breve periodo dal deploy. Strategie di branching con review approfondite e CI robusto riducono il rework rate.

```bash
# Stimare il rework rate: commit "fix" entro 48 ore da un commit "feat"
git log --oneline --since="30 days ago" --format="%H %s" | \
  grep -c "^.*fix\|^.*hotfix\|^.*revert"
# Dividere per il totale dei commit nel periodo
```

---

## Naming Convention Avanzate

### Sistema di Naming Strutturato per Enterprise

Le naming convention per i branch non sono cosmetiche — sono infrastruttura. I sistemi CI/CD, i tool di automazione e le dashboard di monitoraggio si basano sui nomi dei branch per attivare workflow, generare report e applicare policy.

### Formato Raccomandato

```
<tipo>/<ticket>-<descrizione-breve>

Dove:
- tipo:        feature | fix | hotfix | refactor | chore | docs | test | perf | ci
- ticket:      ID del ticket (JIRA, Linear, GitHub Issue)
- descrizione: kebab-case, max 5 parole

Esempi:
  feature/PROJ-1234-oauth-google-login
  fix/PROJ-5678-null-pointer-dashboard
  hotfix/PROJ-9012-xss-sanitization
  refactor/PROJ-3456-extract-auth-service
  chore/no-ticket-update-dependencies
  docs/PROJ-7890-api-reference-v2
  test/PROJ-2345-e2e-checkout-flow
  perf/PROJ-6789-query-optimization
  ci/PROJ-0123-parallel-test-runners
```

### Naming per Utente (Release Flow / Large Teams)

In team grandi, i branch possono includere il nome dell'utente per facilitare l'identificazione:

```
users/<username>/<tipo>-<descrizione>

Esempi:
  users/renan/feat-oauth-google
  users/maria/fix-dashboard-crash
  users/luca/refactor-db-queries
```

### Naming per Release e Ambienti

```
# Release branch
release/v2.3.0
release/2024.sprint-42
release/2026-Q2

# Environment branch (GitLab Flow)
environment/staging
environment/production

# Hotfix con versione
hotfix/v2.3.1-critical-fix
```

### Validazione Automatica dei Nomi

```bash
# Pre-push hook per validare il nome del branch
# .git/hooks/pre-push (o via husky)

#!/usr/bin/env bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Pattern permesso
PATTERN="^(feature|fix|hotfix|refactor|chore|docs|test|perf|ci|release|users)\/[a-z0-9][a-z0-9._\/-]*$"

if [[ "$BRANCH" == "main" || "$BRANCH" == "develop" ]]; then
  exit 0  # branch permanenti consentiti
fi

if [[ ! "$BRANCH" =~ $PATTERN ]]; then
  echo "ERRORE: Nome branch non valido: $BRANCH"
  echo "Formato richiesto: <tipo>/<ticket>-<descrizione>"
  echo "Tipi validi: feature, fix, hotfix, refactor, chore, docs, test, perf, ci, release, users"
  echo "Esempio: feature/PROJ-1234-oauth-login"
  exit 1
fi
```

```yaml
# GitHub Actions: validazione del nome del branch nella PR
name: Validate Branch Name
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  check-branch:
    runs-on: ubuntu-latest
    steps:
      - name: Validate branch name
        run: |
          BRANCH="${{ github.head_ref }}"
          PATTERN="^(feature|fix|hotfix|refactor|chore|docs|test|perf|ci|release|users)/"
          if [[ ! "$BRANCH" =~ $PATTERN ]]; then
            echo "::error::Nome branch non valido: $BRANCH"
            echo "Il branch deve iniziare con uno dei prefissi: feature/, fix/, hotfix/, refactor/, chore/, docs/, test/, perf/, ci/, release/, users/"
            exit 1
          fi
```

### Tabella Riassuntiva: Naming per Strategia

| Strategia | Formato Feature | Formato Release | Formato Hotfix |
|-----------|----------------|----------------|----------------|
| GitFlow | `feature/PROJ-123-desc` | `release/1.2.0` | `hotfix/1.2.1-desc` |
| GitHub Flow | `fix/desc` o `feat/desc` | N/A (tag su main) | `hotfix/desc` |
| Trunk-Based | `short/desc` (vita < 1 gg) | `release/sprint-42` | `hotfix/desc` |
| Release Flow | `users/name/desc` | `release/sprint-42` | cherry-pick (no branch) |
| GitLab Flow | `feature/PROJ-123-desc` | `release/1.2.0` | `hotfix/desc` |

---

## Feature Flag: Architettura e Strumenti a Confronto

### Architettura di un Sistema di Feature Flag

Un sistema di feature flag maturo non è un semplice `if/else` con variabili d'ambiente. È un'infrastruttura che include targeting, rollout progressivo, metriche, governance e ciclo di vita.

```
┌──────────────────────────────────────────────────────────────┐
│                    Management Dashboard                       │
│  Creazione, targeting, rollout %, metriche, audit log         │
└──────────────────────┬───────────────────────────────────────┘
                       │ API
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    Flag Evaluation Service                    │
│  Valuta le regole di targeting per ogni richiesta             │
│  Caching locale per bassa latenza                             │
│  Fallback a default se il servizio è irraggiungibile          │
└──────────────────────┬───────────────────────────────────────┘
                       │ SDK
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    Application Code                          │
│  SDK integrato (LaunchDarkly, Unleash, Flagsmith, custom)    │
│  Valutazione locale con regole sincronizzate                 │
│  Latenza < 1ms per valutazione                               │
└──────────────────────────────────────────────────────────────┘
```

### Confronto Strumenti di Feature Flag (2025-2026)

| Strumento | Tipo | Prezzo | Self-Hosted | Punti di Forza | Ideale Per |
|-----------|------|--------|-------------|----------------|------------|
| **LaunchDarkly** | SaaS proprietario | Da $10/mese per seat | No | Targeting avanzato, SDK maturo, audit log | Enterprise, team grandi |
| **Unleash** | Open source | Free (community) | Sì | Open source, strategy-based, API-first | Team DevOps, self-hosted |
| **Flagsmith** | Open source | Free (community) | Sì | Remote config + flag, multi-ambiente | Startup, team medi |
| **PostHog** | Open source | Free fino a 1M eventi | Sì | Feature flag + analytics integrati | Product team data-driven |
| **Statsig** | SaaS | Free fino a 10M eventi | No | A/B testing + flag, analisi statistica | Growth team |
| **GrowthBook** | Open source | Free | Sì | Esperimenti + flag, Bayesian stats | Data science team |
| **OpenFeature** | Standard | Free (specifica) | N/A | Standard vendor-neutral, SDK multi-provider | Evitare vendor lock-in |
| **Variabili d'ambiente** | Custom | Free | Sì | Semplice, nessuna dipendenza | Prototipi, team piccoli |

### Tipi di Feature Flag

Non tutti i flag sono uguali. La tassonomia di Martin Fowler distingue diversi tipi, ognuno con ciclo di vita e governance diversi:

```
Tipo di Flag              Durata            Chi lo gestisce     Esempio
──────────────────────────────────────────────────────────────────────────
Release Flag              Giorni/settimane  Developer           Nascondere feature incompleta
Experiment Flag           Settimane/mesi    Product manager     A/B test su checkout
Ops Flag                  Permanente        SRE/DevOps          Circuit breaker, rate limit
Permission Flag           Permanente        Product/business    Feature per piano premium
Kill Switch               Permanente        SRE/DevOps          Disabilitare feature in emergenza
```

### Implementazione Pratica con OpenFeature (Standard Vendor-Neutral)

```typescript
// OpenFeature permette di cambiare provider senza modificare il codice
import { OpenFeature } from '@openfeature/server-sdk';
import { UnleashProvider } from '@openfeature/unleash-provider';

// Configurare il provider (intercambiabile)
await OpenFeature.setProviderAndWait(
  new UnleashProvider({
    url: process.env.UNLEASH_URL,
    apiKey: process.env.UNLEASH_API_KEY,
    appName: 'my-app',
  })
);

const client = OpenFeature.getClient();

// Valutare un flag con contesto utente
const showNewDashboard = await client.getBooleanValue(
  'new-dashboard',
  false, // default value
  {
    targetingKey: user.id,
    attributes: {
      email: user.email,
      plan: user.subscription.plan,
      country: user.country,
    },
  }
);

if (showNewDashboard) {
  renderDashboardV2(user);
} else {
  renderDashboardV1(user);
}
```

### Governance dei Feature Flag

I feature flag non gestiti diventano debito tecnico. Servono regole chiare:

```
Regola                          Implementazione
──────────────────────────────────────────────────────────────────
Ogni flag ha un owner           Campo "owner" nel sistema di flag management
Ogni flag ha una data di scadenza   Ticket automatico per cleanup alla scadenza
Cleanup obbligatorio            CI check che fallisce se esistono flag scaduti
Naming convention               Prefisso per tipo: release.*, experiment.*, ops.*
Documentazione                  Ogni flag ha descrizione, owner, cleanup ticket
Audit log                       Ogni modifica ai flag è tracciata con autore e timestamp
Max flag attivi                 Limite a 50 flag contemporanei per progetto
Review per flag sensibili       Flag che impattano pagamenti/auth richiedono approvazione
```

```bash
# Script CI per verificare flag scaduti
# Esempio con Unleash API
curl -s -H "Authorization: Bearer $UNLEASH_API_KEY" \
  "$UNLEASH_URL/api/admin/features" | \
  jq '[.features[] | select(.stale == true)] | length' | \
  xargs -I {} bash -c '
    if [ {} -gt 0 ]; then
      echo "WARNING: {} feature flag scaduti trovati. Pianificare cleanup."
      exit 1
    fi'
```

---

## Migrazione tra Strategie di Branching

### Da GitFlow a GitHub Flow

La migrazione più comune. Avviene quando un team matura la sua CI/CD e non ha più bisogno di release branch e del branch develop.

```
Piano di migrazione (4-6 settimane):

Settimana 1-2: Preparazione
├── Verificare che CI copra > 80% del codice
├── Configurare deploy automatico da main
├── Documentare la nuova strategia
└── Formare il team sulle differenze

Settimana 3: Transizione
├── Completare tutte le release branch aperte
├── Mergiare develop in main (devono essere identici)
├── Congelare il branch develop
├── Aggiornare branch protection rules
└── Aggiornare PR template e workflow CI

Settimana 4-6: Stabilizzazione
├── Il team lavora con la nuova strategia
├── Retrospettiva settimanale per identificare problemi
├── Rimuovere il branch develop (dopo 2 settimane senza problemi)
└── Aggiornare documentazione e onboarding
```

```bash
# Passo 1: Verificare che develop e main siano allineati
git diff main..develop --stat
# Se ci sono differenze, mergiare develop in main
git switch main
git merge --no-ff develop -m "chore: allineare main con develop per migrazione a GitHub Flow"
git push origin main

# Passo 2: Aggiornare branch protection
# Rimuovere protezione da develop, rafforzare su main
gh api repos/{owner}/{repo}/branches/develop/protection -X DELETE

# Passo 3: Aggiornare i workflow CI per triggerare su main
# Modificare tutti i .github/workflows/*.yml:
# branches: [main]  (rimuovere develop)

# Passo 4: Dopo 2 settimane, eliminare develop
git push origin --delete develop
```

### Da GitHub Flow a Trunk-Based Development

Questa migrazione richiede l'adozione di feature flag e l'accelerazione della code review.

```
Piano di migrazione (6-8 settimane):

Settimana 1-2: Infrastruttura
├── Adottare un sistema di feature flag (Unleash, Flagsmith, o custom)
├── Configurare CI per completare in < 10 minuti
├── Implementare pre-commit hooks per linting e test rapidi
└── Documentare le policy per commit diretti vs. branch brevi

Settimana 3-4: Pratica guidata
├── Il team sperimenta con branch di massimo 1 giorno
├── Introdurre pair programming per ridurre errori
├── Feature flag per ogni nuova feature (anche piccola)
└── Code review in < 4 ore (SLA di team)

Settimana 5-6: Commit diretti (per team piccoli)
├── Permettere commit diretti su main per modifiche < 50 righe
├── Richiedere PR per modifiche > 50 righe
├── Monitorare la stabilità di main (build verde > 99%)
└── Retrospettiva per aggiustare le soglie

Settimana 7-8: Ottimizzazione
├── Ridurre ulteriormente la vita dei branch
├── Automatizzare il cleanup dei feature flag
├── Dashboard per monitorare le metriche DORA
└── Celebrare i miglioramenti con dati concreti
```

### Rischi della Migrazione

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Build instabile su main | Alta (inizialmente) | Alto | CI rigoroso, pre-commit hooks, rollback rapido |
| Resistenza del team | Media | Medio | Formazione, pair programming, mostrare benefici con dati |
| Feature flag non puliti | Alta | Medio | Ticket automatici per cleanup, CI che segnala flag scaduti |
| Regressioni da commit diretti | Media | Alto | Test automatici robusti, code review veloce |
| Perdita di tracciabilità | Bassa | Medio | Conventional commits, squash merge con descrizione dettagliata |

---

## Matrice Decisionale Avanzata

### Fattori di Scelta

La scelta della strategia di branching dipende da molteplici fattori. Questa matrice assegna un punteggio (1-5) per ogni combinazione strategia-criterio per guidare la decisione.

```
                          GitFlow  GitHub   Trunk    GitLab   Release
                                   Flow     Based    Flow     Flow
─────────────────────────────────────────────────────────────────────
Team size < 5               2        5        4        3        2
Team size 5-20              3        4        5        4        4
Team size 20-50             4        3        4        4        5
Team size > 50              5        2        3        3        5

Deploy continuo (SaaS)      1        5        5        4        4
Release schedulata          5        2        3        3        5
Versioni multiple           5        1        2        4        2
Mobile app                  5        2        2        3        3

CI/CD maturo                3        4        5        4        5
CI/CD basico                5        3        1        3        2

Feature flag system         2        3        5        3        5
Nessun feature flag         4        4        1        4        2

Team junior                 3        5        2        3        2
Team senior                 3        4        5        4        5

Compliance/audit            5        3        3        4        5
Nessun requisito            2        5        5        3        3

Monorepo                    2        3        5        3        4
Multi-repo                  4        5        4        4        4

Punteggio: 1 = sconsigliato, 5 = ideale per questo contesto
```

### Albero Decisionale Esteso

```
START: Che tipo di prodotto stai sviluppando?
│
├── Web App / SaaS / Microservizi
│   │
│   ├── Il team ha CI/CD in < 10 min e feature flag?
│   │   ├── SÌ → Quanti sviluppatori?
│   │   │   ├── < 20 → Trunk-Based Development
│   │   │   └── > 20 → Release Flow (Microsoft)
│   │   └── NO → Quanti sviluppatori?
│   │       ├── < 10 → GitHub Flow
│   │       └── > 10 → GitLab Flow
│   │
│   └── Servono ambienti multipli (dev/staging/prod)?
│       ├── SÌ → GitLab Flow o Release Flow
│       └── NO → GitHub Flow
│
├── App Mobile (iOS / Android)
│   │
│   ├── Release settimanale con App Store?
│   │   ├── SÌ → GitFlow adattato per mobile + release train
│   │   └── NO → Quanto spesso rilasci?
│   │       ├── Mensile o meno → GitFlow classico
│   │       └── Bisettimanale → GitFlow con code freeze breve
│   │
│   └── Feature flag disponibili?
│       ├── SÌ → Trunk-Based con release branch per submission
│       └── NO → GitFlow adattato per mobile
│
├── Libreria / SDK / Package Open Source
│   │
│   ├── Supporto versioni multiple (1.x, 2.x, 3.x)?
│   │   ├── SÌ → GitFlow con release branch per versione
│   │   └── NO → GitHub Flow con tag per release
│   │
│   └── Contributi esterni (community)?
│       ├── SÌ → GitHub Flow (fork + PR)
│       └── NO → GitHub Flow o Trunk-Based
│
├── Software On-Premise / Embedded / IoT
│   │
│   └── Necessariamente GitFlow
│       ├── Versioni multiple in produzione
│       ├── Release schedulate
│       ├── Hotfix per versioni specifiche
│       └── Supporto a lungo termine (LTS)
│
└── Infrastruttura / GitOps
    │
    ├── Piccolo team, pochi ambienti → Branch per ambiente
    ├── Team medio, compliance media → Directory per ambiente
    └── Enterprise, compliance alta → Repository per ambiente
```

---

## Casi di Studio Reali

### Caso 1: Google — Trunk-Based Development su Scala Massiva

Google è il riferimento per il Trunk-Based Development su scala estrema. L'intero codebase di Google (miliardi di righe di codice) vive in un singolo repository monolitico con un singolo trunk.

```
Numeri (dati pubblici):
- Repository: > 2 miliardi di righe di codice
- Sviluppatori: > 25.000 sviluppatori attivi
- Commit al giorno: > 60.000
- Build system: Blaze/Bazel
- Feature flag: sì, pervasivi
- Code review: obbligatoria (Critique, poi Gerrit)

Caratteristiche chiave:
- NO branch di lunga durata
- Commit direttamente sul trunk dopo code review
- Build system hermetico (Bazel) che garantisce riproducibilità
- Affected analysis per testare solo ciò che è cambiato
- Feature flag per disaccoppiare deploy da release
- "Presubmit" checks automatici prima di ogni commit
```

### Caso 2: Microsoft Azure DevOps — Release Flow

Microsoft ha documentato pubblicamente la strategia di branching per Azure DevOps, dimostrando che Release Flow scala a team di centinaia di sviluppatori con release sprint-based.

```
Numeri:
- Team: > 500 sviluppatori
- Sprint: 3 settimane
- Branch: main + release branch per sprint
- Feature flag: sì, pervasivi (LaunchDarkly interno)
- Deploy: alla fine di ogni sprint
- Rollout: progressivo tramite ring deployment

Lezioni apprese:
1. I feature flag eliminano il 90% dei branch di lunga durata
2. Cherry-pick da main a release è più sicuro di merge da release a main
3. Un singolo branch principale riduce drasticamente il merge debt
4. Lo sprint cadenzato fornisce prevedibilità senza sacrificare velocità
```

### Caso 3: Spotify — Release Train Mobile

Spotify gestisce una delle app mobile più complesse al mondo con un modello di Release Train settimanale che bilancia velocità e stabilità.

```
Numeri (dati pubblici, 2025):
- Team: > 300 sviluppatori mobile
- Release: settimanale (ogni mercoledì)
- Piattaforme: iOS + Android
- Strategia: Trunk-Based con release branch settimanali
- Feature flag: sì (sistema interno)

Workflow:
1. Mercoledì: taglio del release branch dalla main
2. Giovedì-Lunedì: test e stabilizzazione sul release branch
3. Martedì: submission ad App Store e Google Play
4. Mercoledì: rilascio progressivo (1% → 10% → 50% → 100%)

Regole:
- Bug non critici aspettano la release successiva
- Solo fix critici vengono cherry-pickati nel release branch
- Feature flag per ogni nuova feature significativa
- Nessun code freeze globale — solo il release branch è congelato
```

### Caso 4: Startup Early-Stage — Evoluzione della Strategia

Esempio realistico di come la strategia di branching evolve con la crescita del team.

```
Fase 1: Fondatori (2-3 persone)
├── Strategia: Commit diretti su main
├── Review: informale (pair programming)
├── CI: test base, deploy manuale
├── Giustificazione: overhead minimo, velocità massima
└── Rischio accettabile: team piccolo, comunicazione diretta

Fase 2: Team iniziale (5-8 persone)
├── Strategia: GitHub Flow
├── Review: PR + 1 approvazione
├── CI: test + lint + deploy automatico
├── Giustificazione: servono review, ma il processo deve restare semplice
└── Migrazione: aggiungere branch protection su main

Fase 3: Team in crescita (10-20 persone)
├── Strategia: GitHub Flow con naming convention
├── Review: PR + 1-2 approvazioni + CODEOWNERS
├── CI: test + lint + security scan + deploy per ambiente
├── Giustificazione: servono governance e ownership per area
└── Migrazione: aggiungere CODEOWNERS, rulesets, PR template

Fase 4: Team maturo (20-50 persone)
├── Strategia: Trunk-Based o Release Flow
├── Review: PR + 2 approvazioni + CODEOWNERS + security review
├── CI: < 10 min, feature flag, canary deployment
├── Giustificazione: velocità + stabilità + compliance
└── Migrazione: adottare feature flag, accorciare vita dei branch
```

---

## FAQ — Domande Frequenti

### Q: Quando dovrei passare da GitHub Flow a GitFlow?

Quando hai bisogno di supportare versioni multiple in produzione simultaneamente. Se deploi solo una versione (tipico di SaaS/web app), GitHub Flow è sufficiente. Se i tuoi clienti sono su versioni diverse del prodotto (1.x, 2.x, 3.x), GitFlow o una variante con release branch è necessaria.

### Q: Posso usare Trunk-Based Development con un team junior?

È più difficile ma possibile con le guardie giuste:
- Pair programming per ridurre errori
- CI rigoroso con gate di qualità
- Feature flags gestiti centralmente (non lasciare ai singoli sviluppatori)
- Code review rapida (< 2 ore) come barriera al merge

Il rischio è che commit diretti su main rompano la build. Mitigazione: richiedere PR anche per branch brevi (< 1 giorno).

### Q: Squash merge o merge commit?

Dipende da cosa valorizzi:
- **Squash** se vuoi una cronologia pulita dove ogni commit in main = una feature/fix completata
- **Merge commit** se vuoi preservare la topologia dei branch e la cronologia dettagliata
- **Rebase** se vuoi cronologia lineare con commit individuali preservati

Consiglio pragmatico: **squash merge** per la maggior parte dei team. È il compromesso migliore tra leggibilità e tracciabilità.

### Q: Come gestisco un hotfix in GitHub Flow?

In GitHub Flow, un hotfix è semplicemente un branch con vita brevissima e merge prioritario:

```bash
git switch main && git pull
git switch -c hotfix/critical-bug
# ... fix ...
git push -u origin hotfix/critical-bug
gh pr create --title "fix: critical bug in payment processing" --label "priority:critical"
# Review accelerata (1 reviewer invece di 2)
gh pr merge --squash --delete-branch
# Deploy automatico
```

### Q: Feature flag o feature branch per una feature che richiede 3 mesi?

Feature flag. Una feature di 3 mesi in un branch separato accumulerà conflitti insostenibili. Con feature flag:
1. Il codice viene integrato quotidianamente nel trunk
2. Testato nel contesto completo dell'applicazione
3. Rollout progressivo quando pronto
4. Nessun "big bang merge" alla fine

Il costo è la complessità del codice condizionale, ma è molto inferiore al costo di un merge di 3 mesi.

### Q: Come gestisco il branching in un monorepo con team multipli?

1. **Un solo branch principale** (main/trunk) — non creare branch develop per servizio
2. **CODEOWNERS per area** — ogni team possiede la sua porzione
3. **Affected analysis** — CI testa solo i progetti impattati
4. **Feature branch brevi** — anche in monorepo, < 3 giorni
5. **Path-based triggers** — workflow CI diversi per area del monorepo

### Q: Posso mescolare strategie nello stesso repository?

Tecnicamente sì, ma è sconsigliato. Crea confusione. Eccezione: in un monorepo, team diversi possono avere convenzioni diverse per i loro branch, purché la strategia per main sia unica e documentata.

### Q: Quanto spesso dovrei fare merge da main nel mio feature branch?

Almeno una volta al giorno se il team è attivo. L'obiettivo è minimizzare la divergenza. Configura un reminder:

```bash
# Controllare la divergenza del branch corrente rispetto a main
git rev-list --left-right --count main...HEAD
# Output: 15    8
# 15 commit in main non nel branch, 8 commit nel branch non in main
# Se il primo numero > 20, è ora di integrare
```

---

## Esercizi Pratici

### Esercizio 1: Simulare GitFlow Completo

Obiettivo: praticare il flusso completo di GitFlow in un repository di test.

```bash
# Setup
mkdir gitflow-exercise && cd gitflow-exercise
git init
echo "# App v0.1.0" > README.md
git add README.md && git commit -m "chore: init"
git checkout -b develop

# Compiti:
# 1. Creare 2 feature branch da develop e mergiarle
# 2. Creare un release/1.0.0 da develop
# 3. Fare un fix sulla release branch
# 4. Completare la release (merge in main E develop, tag)
# 5. Creare un hotfix da main
# 6. Completare l'hotfix (merge in main E develop, tag)
# 7. Verificare: git log --graph --oneline --all

# Verifica finale:
# - main ha i tag v1.0.0 e v1.0.1
# - develop contiene tutti i fix
# - Nessun branch temporaneo rimasto
```

### Esercizio 2: Confronto Merge Strategies

Obiettivo: capire la differenza pratica tra merge commit, squash e rebase.

```bash
# Setup
mkdir merge-strategies && cd merge-strategies
git init
echo "Base" > file.txt
git add file.txt && git commit -m "init"

# Per ogni strategia (merge, squash, rebase):
# 1. Creare un feature branch con 3 commit
# 2. Integrare in main con la strategia scelta
# 3. Eseguire: git log --graph --oneline --all
# 4. Confrontare il grafo risultante
# 5. Annotare le differenze nella cronologia

# Domande:
# - Quale strategia rende più facile il revert di tutta la feature?
# - Quale produce la cronologia più leggibile con git log?
# - Quale preserva i singoli commit del feature branch?
```

### Esercizio 3: Feature Flag in Trunk-Based Development

Obiettivo: implementare una feature dietro un flag in un workflow trunk-based.

```bash
# 1. Creare un progetto Node.js minimale con un server Express
# 2. Aggiungere un sistema di feature flag basato su variabili d'ambiente
# 3. Implementare una nuova feature (es. endpoint /api/v2/users)
#    dietro il flag FEATURE_USERS_V2
# 4. Committare direttamente su main (il codice è sicuro dietro il flag)
# 5. Testare:
#    - Senza flag: il vecchio endpoint funziona
#    - Con flag: il nuovo endpoint funziona
# 6. "Rilasciare" attivando il flag
# 7. "Pulire" rimuovendo il flag e il codice vecchio

# Verifica:
# - Tutti i commit sono su main (nessun feature branch)
# - Il codice è sempre funzionante ad ogni commit
```

### Esercizio 4: Branch Protection Rules

Obiettivo: configurare protezioni appropriate per un repository GitHub.

```bash
# 1. Creare un repository su GitHub
# 2. Configurare le branch protection rules per main:
#    - Require PR before merging (1 approval)
#    - Require status checks (creare un workflow CI minimale)
#    - Dismiss stale reviews
#    - Require conversation resolution
# 3. Tentare un push diretto su main (deve fallire)
# 4. Creare un feature branch, PR, e mergare correttamente
# 5. Verificare che le regole funzionino

# Bonus: configurare un ruleset con pattern di commit message
```

### Esercizio 5: Cherry-Pick Workflow per Backporting

Obiettivo: praticare il backporting di fix a versioni precedenti.

```bash
# Setup
mkdir cherry-pick-exercise && cd cherry-pick-exercise
git init
echo "v1.0" > VERSION && git add VERSION && git commit -m "release: v1.0"
git tag v1.0.0
git checkout -b release/1.x
git checkout main
echo "v2.0" > VERSION && git add VERSION && git commit -m "release: v2.0"
git tag v2.0.0

# Compiti:
# 1. Creare un fix su main: echo "fix" > security.patch && git add . && git commit -m "fix: CVE-2024-1234"
# 2. Cherry-pick il fix su release/1.x
# 3. Gestire eventuali conflitti
# 4. Taggare la patch: v1.0.1
# 5. Verificare: git log --oneline --all --graph
```

### Esercizio 6: Monorepo Branching

Obiettivo: simulare un workflow monorepo con team multipli.

```bash
# 1. Creare una struttura monorepo:
#    apps/frontend/  apps/api/  libs/shared/
# 2. Configurare CODEOWNERS con team diversi per area
# 3. Creare un feature branch che modifica solo apps/frontend/
# 4. Creare un feature branch che modifica libs/shared/ (impatta tutti)
# 5. Simulare la CI affected analysis:
#    git diff --name-only main...HEAD | grep "apps/frontend/"
# 6. Verificare che CODEOWNERS richieda i reviewer corretti
```

---

## Riferimenti

- **Git Pro Book — Branching**: https://git-scm.com/book/en/v2/Git-Branching-Branching-Workflows
- **Vincent Driessen — GitFlow**: https://nvie.com/posts/a-successful-git-branching-model/
- **GitHub Flow Guide**: https://docs.github.com/en/get-started/using-github/github-flow
- **GitLab Flow**: https://about.gitlab.com/topics/version-control/what-is-gitlab-flow/
- **Trunk-Based Development**: https://trunkbaseddevelopment.com/
- **DORA — State of DevOps**: https://dora.dev/research/
- **Martin Fowler — Feature Toggles**: https://martinfowler.com/articles/feature-toggles.html
- **Conventional Commits**: https://www.conventionalcommits.org/
- **Semantic Versioning**: https://semver.org/
- **GitHub Docs — Branch Protection**: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-a-branch-protection-rule
- **GitHub Docs — Rulesets**: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets

---

## Letture e Riferimenti

### Documentazione ufficiale

- **Git Branching — Pro Git Book**: https://git-scm.com/book/en/v2/Git-Branching-Branching-Workflows — Capitolo dedicato ai modelli di branching.
- **GitHub Flow Guide**: https://docs.github.com/en/get-started/using-github/github-flow — Guida ufficiale al workflow semplificato di GitHub.
- **Trunk-Based Development**: https://trunkbaseddevelopment.com/ — Sito di riferimento per TBD con pattern, anti-pattern e case study.
- **Vincent Driessen — GitFlow**: https://nvie.com/posts/a-successful-git-branching-model/ — Post originale che ha definito il modello GitFlow.
- **Martin Fowler — Feature Toggles**: https://martinfowler.com/articles/feature-toggles.html — Tassonomia completa dei feature flag e pattern di implementazione.
- **DORA — State of DevOps**: https://dora.dev/research/ — Ricerche annuali che correlano le pratiche di branching con le metriche DORA (deployment frequency, lead time).
- **Conventional Commits**: https://www.conventionalcommits.org/ — Specifica per messaggi di commit strutturati, fondamentale per automazione release.
- **Semantic Versioning 2.0.0**: https://semver.org/ — Specifica formale del versionamento semantico MAJOR.MINOR.PATCH.

### Libri consigliati

- **"Continuous Delivery" — Jez Humble, David Farley** (Addison-Wesley) — Fondamento teorico per trunk-based development e pipeline CI/CD.
- **"Accelerate" — Nicole Forsgren, Jez Humble, Gene Kim** (IT Revolution) — Dati empirici che collegano le pratiche di branching alle performance organizzative.
- **"Release It!" — Michael Nygard** (Pragmatic Bookshelf, 2nd ed.) — Pattern di release e deploy che informano la scelta della strategia di branching.

---

## Riferimenti Incrociati

| Modulo | File | Relazione |
|--------|------|-----------|
| 01 | [01-fondamenti-git.md](01-fondamenti-git.md) | Prerequisito: comandi base di branching, merge e rebase |
| 06 | [06-git-branching-merge-avanzato.md](06-git-branching-merge-avanzato.md) | Approfondisce merge strategies, octopus merge e rerere |
| 08 | [08-git-hooks-automazione.md](08-git-hooks-automazione.md) | Hook per enforce di naming convention e commit lint sui branch |
| 12 | [12-github-repository-management.md](12-github-repository-management.md) | Branch protection rules e rulesets a livello repository |
| 20 | [20-git-workflow-team-guida-completa.md](20-git-workflow-team-guida-completa.md) | Workflow operativi per team con branching e code review integrati |
| 09 | [09-git-lfs-submodules-monorepo.md](09-git-lfs-submodules-monorepo.md) | Strategie di branching specifiche per monorepo e submodule |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **GitFlow** | Modello di branching che utilizza branch main, develop, feature, release e hotfix per gestire cicli di release strutturati |
| **GitHub Flow** | Workflow semplificato basato su main + feature branch con deploy continuo dopo merge della Pull Request |
| **Trunk-Based Development** | Strategia in cui tutti gli sviluppatori committano direttamente su main (trunk) o branch di brevissima durata (<1 giorno) |
| **GitLab Flow** | Variante che aggiunge environment branch (staging, production) al modello GitHub Flow |
| **Feature Flag** | Toggle nel codice che permette di abilitare/disabilitare funzionalità senza cambiare il codice deployato |
| **Branch Protection Rule** | Regola GitHub che impedisce push diretti, richiede review o status check prima del merge |
| **Ruleset** | Evoluzione delle branch protection rules con targeting flessibile e gestione a livello organization |
| **CODEOWNERS** | File che assegna automaticamente reviewer in base ai path dei file modificati nella Pull Request |
| **Release Branch** | Branch dedicato alla stabilizzazione di una release, isolando il lavoro di bugfix dal nuovo sviluppo |
| **Hotfix** | Correzione urgente applicata direttamente a un branch di produzione e poi backportata ai branch di sviluppo |
| **Merge Commit** | Commit con due o più parent che registra l'unione di branch divergenti, preservando la storia completa |
| **Squash Merge** | Tipo di merge che comprime tutti i commit del feature branch in un singolo commit sul branch target |
| **Cherry-pick** | Operazione che copia un singolo commit da un branch a un altro, usata tipicamente per backport di fix |
| **Conventional Commits** | Specifica che struttura i messaggi di commit con tipo (feat, fix, etc.) per abilitare automazione (changelog, versioning) |

---

## Nota sulle Tendenze di Settore 2025-2026

Le ricerche DORA e le analisi di settore più recenti confermano un'accelerazione significativa nell'adozione del trunk-based development anche in settori altamente regolamentati come sanità, finanza e gambling. Mentre nel 2018 il dibattito verteva sulla fattibilità pratica del trunk-based development, nel 2025-2026 la domanda si è invertita: le organizzazioni che non lo adottano devono giustificare la scelta di strategie alternative. Google, Meta, Amazon e la maggior parte delle grandi aziende tecnologiche operano con commit diretti sul mainline, dimostrando che il modello scala efficacemente oltre i 100 ingegneri. Per i team che desiderano effettuare la transizione, l'approccio raccomandato è graduale: passare prima da GitFlow a GitHub Flow, abituarsi a branch di durata sempre più breve e merge più frequenti, per poi ridurre progressivamente la vita dei branch fino a praticare effettivamente trunk-based development. La combinazione di feature flag maturi (LaunchDarkly, Unleash, Flagsmith), test automatizzati robusti e code review sistematiche è il prerequisito tecnico che rende possibile questo passaggio mantenendo la stabilità del codice in produzione in ogni momento.|
