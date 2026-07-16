# Module 8.5: Git Branching Strategies

> **Module 08.5** · **Last updated:** 2026-05-22

## Guiding ideas

1. **Trunk-based: main always deployable; short-lived feature branches (< 1 day).**
2. **GitHub Flow: main + feature branches; deploy from main.**
3. **Gitflow: main + develop + feature/release/hotfix; legacy for most web apps.**
4. **Release Train: scheduled releases; feature flags decouple deploy from release.**
5. **The best strategy is the one your team actually follows consistently.**

---

## 1. Why Branching Strategy Matters

A branching strategy is not just a Git workflow — it encodes how your team
collaborates, how code reaches production, how hotfixes are deployed, and how
releases are communicated. A mismatched strategy creates friction at every step:
merge conflicts, release delays, deployment confusion, and on-call nightmares.

### 1.1 Strategy selection criteria

| Factor | Trunk-based | GitHub Flow | GitLab Flow | Gitflow | Release Train |
|---|---|---|---|---|---|
| Team size | Any | Small-medium | Medium-large | Any | Large |
| Deploy frequency | Continuous | Continuous | Per-environment | Scheduled | Scheduled |
| Release audience | Internal/SaaS | SaaS | SaaS + staging | Packaged/mobile | Mobile/enterprise |
| CI/CD maturity | Must be high | Moderate | Moderate | Low OK | Moderate |
| Feature flags needed? | Yes | Helpful | Helpful | No | Yes |
| Rollback mechanism | Feature flag / revert | Revert | Revert | Hotfix branch | Revert / flag |
| Merge conflict frequency | Very low | Low | Low | High | Moderate |
| Cognitive overhead | Low | Low | Moderate | High | Moderate |

### 1.2 Decision flowchart

```
Can you deploy to production multiple times per day?
├── Yes
│   ├── Do you have feature flags infrastructure?
│   │   ├── Yes → Trunk-based development
│   │   └── No → GitHub Flow
│   └── Do you need environment-specific branches (staging, pre-prod)?
│       ├── Yes → GitLab Flow
│       └── No → GitHub Flow
└── No
    ├── Are you shipping a versioned product (mobile app, SDK, on-prem)?
    │   ├── Yes
    │   │   ├── Do you have a fixed release cadence (every 2 weeks)?
    │   │   │   ├── Yes → Release Train
    │   │   │   └── No → Gitflow
    │   │   └── Is the release approval process heavyweight?
    │   │       ├── Yes → Gitflow
    │   │       └── No → GitHub Flow with release branches
    │   └── No → GitHub Flow
    └── Regulated industry with audit trail requirements?
        ├── Yes → Gitflow or GitLab Flow (with environment branches)
        └── No → GitHub Flow
```

---

## 2. Trunk-Based Development

The simplest model. Everyone commits to `main` (the trunk). Short-lived feature
branches are optional but must merge within hours, ideally within a day.

### 2.1 Core rules

1. **main is always releasable.** Every commit passes all tests.
2. **Feature branches live < 1 day.** If it takes longer, break it into smaller
   increments using feature flags.
3. **No long-lived branches.** No `develop`, no `staging` branch.
4. **Continuous integration is mandatory.** Broken main = production incident.
5. **Feature flags control visibility, not branches.**

### 2.2 Workflow

```
main ─────●────●────●────●────●────●────●────●────●──→
           \  /      \  /           \  /
            ○─       ○─              ○─
         (feat-a)  (feat-b)       (feat-c)
         2 hours    4 hours        6 hours
```

```bash
# Start work
git checkout main
git pull
git checkout -b feat/add-user-search

# Work, commit frequently (small, focused commits)
git add -p
git commit -m "feat: add user search query builder"

# Rebase on latest main before pushing
git fetch origin main
git rebase origin/main

# Push and create PR
git push -u origin feat/add-user-search
gh pr create --title "feat: add user search" --body "..."

# After approval + CI green: merge (squash or rebase)
gh pr merge --squash --delete-branch
```

### 2.3 Feature flags enabling trunk-based

Without feature flags, trunk-based is impossible for features that take more than
a day. Feature flags let you merge incomplete work safely.

```typescript
// Feature flag check at runtime
if (featureFlags.isEnabled('user-search', { userId: user.id })) {
  renderSearchComponent();
} else {
  renderLegacyList();
}
```

Feature flag lifecycle:

```
Flag created → Code merged behind flag → Internal testing → 
Percentage rollout (1% → 10% → 50% → 100%) → Flag removed
```

**Flag management tools:**

| Tool | Type | Strengths |
|---|---|---|
| LaunchDarkly | SaaS | Mature, targeting rules, audit log |
| Unleash | Self-hosted / SaaS | Open source, good for privacy-sensitive orgs |
| Flipt | Self-hosted | Lightweight, gRPC-native |
| Flagsmith | Self-hosted / SaaS | Open source, feature-rich |
| AWS AppConfig | SaaS | AWS-native, no extra vendor |
| Environment variables | DIY | Simplest possible; no gradual rollout |

**Feature flag anti-patterns:**

| Anti-pattern | Risk | Fix |
|---|---|---|
| Flag never removed | Tech debt, dead code paths | Set TTL at creation; alert after expiry |
| Flag in database logic | Complex queries, data inconsistency | Flags control UI/API layer, not data model |
| Nested flag dependencies | Combinatorial explosion | Flags should be independent |
| No flag ownership | Nobody removes them | DRI assigned at creation |
| Testing without flag combinations | Bugs in flag-off path | Test both paths in CI |
| Flags controlling infrastructure | Config drift | Use infrastructure-as-code, not flags |

### 2.4 Trunk-based at scale (Google, Meta)

Google and Meta use trunk-based development with tens of thousands of developers
on a single monorepo.

Key enablers:
- **Very fast CI** (< 10 minutes for affected tests).
- **Hermetic builds** (reproducible, no shared mutable state).
- **Code ownership** (CODEOWNERS enforces review by domain experts).
- **Submit queue** (merge queue serializes merges, runs CI per merge).
- **Virtual monorepo tools** (Bazel, Buck2) build only what changed.

### 2.5 When trunk-based breaks down

- Team doesn't have fast CI (> 30 minutes per run).
- No feature flag infrastructure and features take weeks.
- Regulatory requirement for release branches with audit trail.
- Team members rarely communicate (remote, async-heavy, different timezones).
- Mobile apps with App Store review cycles (can't deploy continuously).

---

## 3. GitHub Flow

Simple branching model created by GitHub. Main branch + short-lived feature
branches. Deploy from main. No `develop` branch, no release branches.

### 3.1 Core rules

1. **main is always deployable.**
2. **Create a descriptively named branch off main for each feature.**
3. **Push to the branch regularly; open a PR when ready for review.**
4. **After review and CI, merge to main.**
5. **Deploy immediately after merge.**

### 3.2 Workflow

```
main ─────●────────●────────●────────●────────●──→
           \      /          \      /
            ○──○─○            ○──○─○
         feat/search       fix/auth-timeout
           3 days              2 days
```

```bash
# Create feature branch
git checkout -b feat/notification-preferences
# ... develop, commit, push ...
git push -u origin feat/notification-preferences

# Open PR
gh pr create --title "feat: notification preferences" \
  --body "Adds user-configurable notification channels (email, SMS, push)"

# After review: merge to main
gh pr merge --merge --delete-branch

# Deploy (automated via CI/CD)
# main merge triggers: build → test → deploy staging → smoke test → deploy prod
```

### 3.3 GitHub Flow vs. trunk-based

| Aspect | Trunk-based | GitHub Flow |
|---|---|---|
| Branch lifetime | Hours | Days (1-5) |
| Feature flags | Required for larger features | Nice-to-have |
| CI speed requirement | Critical | Important |
| PR size | Very small | Small-medium |
| Direct commits to main | Sometimes (small fixes) | Never |
| Deploy trigger | Every commit to main | Every merge to main |

### 3.4 GitHub Flow with environments

For teams that need a staging environment but don't want full GitLab Flow:

```
main → deploy to production (after CI)

# For staging testing:
# Deploy any branch to staging via manual trigger or label
gh pr edit --add-label "deploy-to-staging"
# CI deploys that branch to staging
# After validation, merge PR to main → auto-deploy to prod
```

---

## 4. GitLab Flow

Adds environment branches to GitHub Flow. Bridges the gap between feature
branches and multiple deployment environments.

### 4.1 Variant 1: Environment branches

```
main ─────●────●────●────●────●────●──→
           \  /      \  /      \  /
            ○─       ○─        ○─
          (features)

staging ──────●──────●──────●──→
              ↑      ↑      ↑
           (cherry-pick from main)

production ─────●──────●──→
                ↑      ↑
             (cherry-pick from staging)
```

Flow: Feature → main → staging → production. Each environment branch is a gate.

### 4.2 Variant 2: Release branches

For versioned products that need to maintain multiple versions:

```
main ─────●────●────●────●────●────●────●──→
           \                   \
            release/1.0         release/2.0
              ●──●──●             ●──●
           (hotfixes only)     (hotfixes)
```

### 4.3 When to use GitLab Flow

- You need staging/pre-prod environments with manual gates.
- You deploy to multiple environments at different cadences.
- You need the simplicity of GitHub Flow but with environment promotion.
- Regulatory compliance requires environment-specific approval.

### 4.4 GitLab Flow anti-patterns

| Anti-pattern | Risk | Fix |
|---|---|---|
| Cherry-picking creates divergence | Staging and production drift | Merge forward, not cherry-pick back |
| Environment branches accumulate drift | Conflicts on promotion | Promote frequently (daily) |
| Skipping staging | Untested code in production | Enforce promotion chain in CI |

---

## 5. Gitflow (Vincent Driessen, 2010)

The most structured branching model. Two long-lived branches (`main` and `develop`)
plus three types of short-lived branches (feature, release, hotfix).

### 5.1 Branch structure

```
main ─────●──────────────────●──────────────●──→
           \                  ↑              ↑
            \           release/1.0    release/2.0
             \           /    \          /
develop ─────●──●──●──●──●──●──●──●──●──●──●──→
              \  /  \  /               \  /
               ○─    ○─                 ○─
           feature/a feature/b      feature/c
```

### 5.2 Branch types

| Branch | Source | Merges into | Purpose |
|---|---|---|---|
| `main` | — | — | Production-ready code; every commit is a release |
| `develop` | `main` (initial) | — | Integration branch; next release candidate |
| `feature/*` | `develop` | `develop` | New feature development |
| `release/*` | `develop` | `main` + `develop` | Release preparation (version bump, final fixes) |
| `hotfix/*` | `main` | `main` + `develop` | Emergency production fix |

### 5.3 Workflow commands

```bash
# Start a feature
git checkout develop
git checkout -b feature/user-export
# ... develop ...
git checkout develop
git merge --no-ff feature/user-export
git branch -d feature/user-export

# Start a release
git checkout develop
git checkout -b release/1.2.0
# ... bump version, final fixes ...
git checkout main
git merge --no-ff release/1.2.0
git tag -a v1.2.0 -m "Release 1.2.0"
git checkout develop
git merge --no-ff release/1.2.0
git branch -d release/1.2.0

# Hotfix
git checkout main
git checkout -b hotfix/1.2.1
# ... fix ...
git checkout main
git merge --no-ff hotfix/1.2.1
git tag -a v1.2.1 -m "Hotfix 1.2.1"
git checkout develop
git merge --no-ff hotfix/1.2.1
git branch -d hotfix/1.2.1
```

### 5.4 git-flow CLI extension

```bash
# Install
brew install git-flow-avh    # macOS
apt install git-flow         # Debian/Ubuntu

# Initialize
git flow init
# Accepts defaults: main, develop, feature/, release/, hotfix/

# Feature workflow
git flow feature start user-export
# ... work ...
git flow feature finish user-export

# Release workflow
git flow release start 1.2.0
# ... version bump, changelog ...
git flow release finish 1.2.0

# Hotfix workflow
git flow hotfix start 1.2.1
# ... fix ...
git flow hotfix finish 1.2.1
```

### 5.5 Why Gitflow is legacy for most web teams

| Problem | Explanation |
|---|---|
| Merge conflicts | Two long-lived branches = constant merge conflicts |
| Slow releases | Release branches add ceremony and delay |
| Cognitive overhead | 5 branch types, multiple merge directions |
| Incompatible with CD | Can't deploy continuously with release branches |
| Hotfix double-merge | Must merge hotfix into both `main` and `develop` |
| develop branch is waste | If you deploy from main, develop adds no value |

**When Gitflow still makes sense:**

- Versioned desktop/mobile software with named releases.
- Products with long QA cycles (medical devices, embedded systems).
- Open-source projects maintaining multiple major versions.
- Regulated industries requiring formal release sign-off.

---

## 6. Release Trains

Scheduled release cadence where whatever is ready ships on a fixed date, and
whatever isn't ready waits for the next train.

### 6.1 How release trains work

```
Week 1-2: Feature development (merge to main behind flags)
Week 3:   Feature freeze → cut release branch
Week 4:   QA on release branch → fix only regressions
Week 5:   Release day → deploy to production, remove flags
```

```
main ─────●──●──●──●──●──●──●──●──●──●──●──→
                       \                \
                  release/2026.03    release/2026.04
                    (freeze)          (freeze)
                    ●──●──●           ●──●
                  (bugfixes only)
```

### 6.2 Release train cadence examples

| Product type | Cadence | Examples |
|---|---|---|
| Mobile app | 2 weeks | Many iOS/Android apps (App Store review ~24-48h) |
| Enterprise SaaS | Monthly | Salesforce, ServiceNow |
| Browser | 4 weeks | Chrome, Firefox |
| OS/Platform | 6-12 months | macOS, Ubuntu LTS |
| Embedded/IoT | Quarterly+ | Firmware releases |

### 6.3 Feature flags with release trains

Feature flags are essential for release trains. Without them, incomplete features
block the train.

```
Feature A: ready     → flag ON in release branch → ships
Feature B: 80% done  → flag OFF in release branch → doesn't ship, rides next train
Feature C: ready     → flag ON in release branch → ships
```

### 6.4 Release train anti-patterns

| Anti-pattern | Risk | Fix |
|---|---|---|
| Train waits for one feature | Defeats the purpose; delays everything | Feature rides next train |
| No feature freeze | Release branch is a moving target | Strict freeze date |
| Cherry-picking features onto train | Bypasses QA cycle | Features must be in main before freeze |
| No rollback plan | Broken release stays broken | Canary deploy + instant rollback |
| Train too infrequent | Pressure to include everything | Shorten cadence |

---

## 7. Branch Naming Conventions

Consistent naming reduces confusion and enables automation (CI pattern matching,
auto-labeling, deploy rules).

### 7.1 Recommended convention

```
<type>/<ticket-id>-<short-description>
```

| Type | Purpose | Example |
|---|---|---|
| `feat/` | New feature | `feat/PROJ-123-user-search` |
| `fix/` | Bug fix | `fix/PROJ-456-auth-timeout` |
| `hotfix/` | Production emergency fix | `hotfix/PROJ-789-payment-null` |
| `chore/` | Tooling, config, CI | `chore/PROJ-101-upgrade-node-20` |
| `refactor/` | Code restructuring | `refactor/PROJ-202-extract-service` |
| `docs/` | Documentation only | `docs/PROJ-303-api-reference` |
| `test/` | Test-only changes | `test/PROJ-404-add-integration` |
| `release/` | Release preparation | `release/2.1.0` |
| `experiment/` | Throwaway exploration | `experiment/try-htmx` |

### 7.2 Branch name automation

```yaml
# GitHub Actions: enforce branch naming
name: Branch Name Check
on: pull_request

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Check branch name
        run: |
          BRANCH="${{ github.head_ref }}"
          PATTERN="^(feat|fix|hotfix|chore|refactor|docs|test|release|experiment)/"
          if [[ ! "$BRANCH" =~ $PATTERN ]]; then
            echo "::error::Branch name '$BRANCH' does not match pattern: $PATTERN"
            exit 1
          fi
```

### 7.3 Branch protection rules

```yaml
# GitHub branch protection (via API or UI)
main:
  require_pull_request_reviews:
    required_approving_review_count: 1
    dismiss_stale_reviews: true
    require_code_owner_reviews: true
  require_status_checks:
    strict: true         # Branch must be up-to-date with main
    contexts:
      - "ci/tests"
      - "ci/lint"
      - "ci/security"
  require_linear_history: true    # No merge commits (squash or rebase)
  require_signed_commits: false   # Enable for high-security repos
  allow_force_pushes: false
  allow_deletions: false
```

---

## 8. Merge Strategies

How you integrate branches affects history readability, bisect-ability, and
conflict resolution.

### 8.1 Merge commit (`--no-ff`)

```
main ─────●────────●────●──→
           \      /
            ○──○─○
         feat/search
```

Creates an explicit merge commit. Preserves full branch history.

**Pros:** Full history visible; easy to revert entire feature (revert the merge commit).
**Cons:** Noisy history with many merge commits; non-linear.

### 8.2 Squash merge

```
main ─────●────●────●──→
                     ↑
              (squashed: 5 commits → 1)
```

All branch commits compressed into a single commit on main.

**Pros:** Clean linear history on main; each feature = one commit.
**Cons:** Loses granular commit history; harder to bisect within a feature.

### 8.3 Rebase merge

```
main ─────●────●────○──○──○──→
                     ↑  ↑  ↑
              (rebased: 3 commits replayed on top of main)
```

Branch commits replayed on top of main, then fast-forward merged.

**Pros:** Linear history; preserves individual commits.
**Cons:** Requires clean, well-structured commits; can't easily revert entire feature.

### 8.4 Which merge strategy to use

| Strategy | Best for | History style |
|---|---|---|
| Merge commit | Gitflow, long-lived branches | Non-linear, verbose |
| Squash merge | GitHub Flow, short features | Linear, one commit per feature |
| Rebase merge | Trunk-based, curated history | Linear, preserves commits |

**Recommendation for most teams:** Squash merge for feature branches into main.
It produces the cleanest history and makes `git log --oneline main` useful.

### 8.5 Merge queue

A merge queue serializes PR merges, ensuring that each PR is tested against the
latest main before merging. Prevents the "it was green when I merged" problem.

```
Without merge queue:
  PR-A merges (CI green on commit X)
  PR-B merges (CI green on commit X, but doesn't include PR-A)
  → main may be broken because PR-A and PR-B conflict

With merge queue:
  PR-A enters queue → CI runs on main + PR-A → merge
  PR-B enters queue → CI runs on main + PR-A + PR-B → merge
  → main is always green
```

**Available merge queues:**

| Tool | Platform | Features |
|---|---|---|
| GitHub Merge Queue | GitHub | Native, auto-rebase, batch merging |
| Mergify | GitHub | Rule engine, priority queues, batch |
| Bors | GitHub | Rust-community originated, simple |
| GitLab Merge Trains | GitLab | Native, pipeline-based |
| Aviator MergeQueue | GitHub | Parallel testing, priority |

```yaml
# GitHub merge queue configuration (branch protection)
main:
  require_merge_queue: true
  merge_queue:
    merge_method: squash
    max_entries_to_build: 5
    min_entries_to_merge: 1
    max_entries_to_merge: 5
    grouping_strategy: ALLGREEN
```

### 8.6 Merge conflict prevention

| Practice | Impact |
|---|---|
| Short-lived branches (< 3 days) | Conflicts can't accumulate |
| Small PRs (< 400 lines added) | Less surface area for conflict |
| Frequent rebasing on main | Catch conflicts early |
| CODEOWNERS with narrow scope | Fewer people touching same files |
| Modular architecture | Changes don't cross module boundaries |
| Feature flags over feature branches | Merge early, expose later |

---

## 9. Monorepo Branching Strategies

Monorepos contain multiple projects/services in a single repository. Branching
strategy needs adjustment.

### 9.1 Monorepo + trunk-based (recommended)

```
monorepo/
├── packages/
│   ├── api/          # Backend API
│   ├── web/          # Frontend app
│   ├── mobile/       # Mobile app
│   ├── shared/       # Shared libraries
│   └── infra/        # Terraform/Pulumi
├── .github/
│   └── CODEOWNERS
└── nx.json           # or turbo.json, bazel BUILD
```

Key enablers:
- **Affected-only CI**: only build/test packages that changed.
- **CODEOWNERS per directory**: right reviewers for each package.
- **Independent versioning**: each package has its own version.

```bash
# Nx: run tests only for affected packages
npx nx affected --target=test --base=origin/main

# Turborepo: same concept
npx turbo run test --filter=...[origin/main]

# Bazel: query affected targets
bazel query 'rdeps(//..., set($(git diff --name-only origin/main)))' | \
  xargs bazel test
```

### 9.2 CODEOWNERS

```
# .github/CODEOWNERS

# Default: require review from engineering leads
*                           @org/engineering-leads

# Package-specific ownership
/packages/api/              @org/backend-team
/packages/web/              @org/frontend-team
/packages/mobile/           @org/mobile-team
/packages/shared/           @org/platform-team
/packages/infra/            @org/sre-team

# Security-sensitive paths require security team review
/packages/api/src/auth/     @org/security-team @org/backend-team
/packages/api/src/payments/ @org/security-team @org/backend-team

# CI/CD config requires platform team
/.github/                   @org/platform-team
/Dockerfile                 @org/platform-team
```

### 9.3 Monorepo tools comparison

| Tool | Language | Build | Test | Cache | Remote cache |
|---|---|---|---|---|---|
| **Nx** | JS/TS (any via plugins) | Yes | Yes | Yes | Nx Cloud |
| **Turborepo** | JS/TS | Yes | Yes | Yes | Vercel Remote Cache |
| **Bazel** | Any | Yes | Yes | Yes | Yes (remote execution) |
| **Pants** | Python, Go, Java | Yes | Yes | Yes | Yes |
| **Rush** | JS/TS | Yes | Yes | Yes | Azure Storage |
| **Lerna** | JS/TS (legacy) | No | No | No | No |

### 9.4 Monorepo anti-patterns

| Anti-pattern | Risk | Fix |
|---|---|---|
| Running all tests for every change | CI takes 45 minutes | Affected-only CI |
| No CODEOWNERS | Wrong reviewers, or no reviewers | Define ownership per directory |
| Shared `package.json` with all deps | Version conflicts, bloated installs | Per-package `package.json` |
| Circular dependencies between packages | Build order breaks, hard to reason about | Enforce DAG with lint rules |
| Everyone can merge to any package | Accidental breakage | Branch protection per path (CODEOWNERS) |

---

## 10. Code Ownership (CODEOWNERS)

### 10.1 Why code ownership matters

- **Faster reviews**: the right people review the right code.
- **Accountability**: every file has a responsible team.
- **Knowledge preservation**: ownership prevents single points of failure.
- **Security**: sensitive paths require security team sign-off.

### 10.2 CODEOWNERS syntax

```
# File: .github/CODEOWNERS (GitHub) or CODEOWNERS (GitLab)

# Syntax: <pattern> <owner> [<owner>...]
# Owners can be: @username, @org/team-name, email@example.com

# Global default
*                       @org/engineering-leads

# Directory ownership
/src/auth/              @org/security-team
/src/billing/           @org/billing-team
/docs/                  @org/docs-team

# File-type ownership
*.proto                 @org/platform-team
*.tf                    @org/infra-team
Dockerfile              @org/platform-team
docker-compose*.yml     @org/platform-team

# Specific file ownership
/src/config/secrets.go  @org/security-team

# Multiple owners (any can approve)
/src/api/               @org/backend-team @org/api-reviewers

# Exclude pattern (empty owner = no required review)
# /docs/internal/       # (commented out: no automatic reviewer)
```

### 10.3 Code ownership anti-patterns

| Anti-pattern | Risk | Fix |
|---|---|---|
| Single person owns everything | Bus factor = 1 | Team ownership, not individual |
| Ownership too broad | `* @everyone` means no one | Narrow to directories/packages |
| Ownership not enforced | People bypass CODEOWNERS | Enable "require code owner reviews" |
| Stale ownership (person left) | Reviews never happen | Audit quarterly |
| No ownership for CI/infra | Anyone can change deploy pipeline | Assign platform team |

### 10.4 Ownership review cadence

```
Quarterly CODEOWNERS audit:
1. Check for owners who left the org → reassign
2. Check for directories with no owner → assign
3. Check for overly broad patterns → narrow
4. Check for single-person ownership → add backup
5. Verify security-sensitive paths have @security-team
```

---

## 11. Commit Message Conventions

Consistent commit messages enable automated changelogs, semantic versioning, and
meaningful `git log` output.

### 11.1 Conventional Commits

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:

| Type | Semantic version bump | Description |
|---|---|---|
| `feat` | MINOR | New feature |
| `fix` | PATCH | Bug fix |
| `docs` | — | Documentation only |
| `style` | — | Formatting, missing semicolons |
| `refactor` | — | Code change that neither fixes nor adds |
| `perf` | PATCH | Performance improvement |
| `test` | — | Adding or correcting tests |
| `build` | — | Build system or external dependencies |
| `ci` | — | CI configuration |
| `chore` | — | Other changes that don't modify src or test |
| `revert` | varies | Reverts a previous commit |

**Breaking change:**

```
feat!: remove v1 API endpoints

BREAKING CHANGE: All /v1/* endpoints are removed.
Clients must migrate to /v2/* before upgrading.
```

### 11.2 Commit message examples

```
feat(auth): add TOTP-based MFA support

Implements RFC 6238 TOTP generation and validation.
Supports Google Authenticator and Authy.

Closes #234
```

```
fix(payments): prevent double-charge on timeout retry

When a payment gateway returns a timeout, the retry logic was
not checking for idempotency key collision. This caused
double-charges for ~0.1% of transactions.

Root cause: missing idempotency check in RetryInterceptor.
Fix: check existing transaction by idempotency key before retry.

Fixes #567
```

```
refactor(orders): extract pricing calculation to domain service

Move pricing logic from OrderController into PricingService.
No behavior change; improves testability and reuse.
```

### 11.3 Enforcing commit messages

```bash
# commitlint + husky (Node.js projects)
npm install --save-dev @commitlint/cli @commitlint/config-conventional husky

# commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor',
      'perf', 'test', 'build', 'ci', 'chore', 'revert'
    ]],
    'subject-max-length': [2, 'always', 72],
    'body-max-line-length': [2, 'always', 100],
  },
};

# Setup husky hook
npx husky init
echo 'npx --no -- commitlint --edit $1' > .husky/commit-msg
```

```yaml
# CI enforcement (GitHub Actions)
- name: Lint commit messages
  uses: wagoid/commitlint-github-action@v5
  with:
    configFile: commitlint.config.js
```

### 11.4 Automated changelogs

With Conventional Commits, changelogs can be generated automatically:

```bash
# Using standard-version (or release-please)
npx standard-version
# Reads commits since last tag
# Bumps version based on commit types
# Generates CHANGELOG.md
# Creates version commit and tag

# Google's release-please (GitHub Action)
# Automatically creates release PRs with changelog
```

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/release-please-action@v4
        with:
          release-type: node
```

---

## 12. Git Workflow Comparison Matrix

| Dimension | Trunk-based | GitHub Flow | GitLab Flow | Gitflow | Release Train |
|---|---|---|---|---|---|
| Long-lived branches | 1 (main) | 1 (main) | 2-3 (main + env) | 2 (main + develop) | 1 (main) + release |
| Feature branches | Optional, < 1 day | Yes, 1-5 days | Yes, 1-5 days | Yes, days-weeks | Yes, any length |
| Release branches | No | No | Environment branches | Yes | Yes, per train |
| Hotfix process | Fix on main | Fix on main | Fix on main, promote | Hotfix branch | Fix on main or release |
| Merge conflicts | Rare | Uncommon | Uncommon | Frequent | Uncommon |
| CI complexity | Low | Low | Medium | High | Medium |
| Release control | Feature flags | Deploy on merge | Environment promotion | Release branch | Train schedule |
| Best for | High-velocity SaaS | Small-medium web | Multi-env enterprise | Versioned products | Mobile, scheduled releases |
| Worst for | Versioned products | Multi-env needs | Simple projects | Web SaaS | Small teams |

---

## 13. Migration Guides

### 13.1 Gitflow to trunk-based

```
Phase 1 (2 weeks): Preparation
- Set up feature flag infrastructure
- Configure merge queue
- Set up branch protection on main
- Train team on trunk-based practices

Phase 2 (2 weeks): Parallel operation
- New features use trunk-based (short branches + flags)
- Existing Gitflow features complete in develop
- Release from develop as usual

Phase 3 (1 week): Cutover
- Merge develop into main (final sync)
- Delete develop branch
- All new work goes to main via short branches
- Monitor merge queue, CI times, deploy frequency

Phase 4 (ongoing): Optimization
- Reduce branch lifetime (target < 1 day)
- Remove old feature flags (set TTL)
- Speed up CI (target < 10 minutes)
- Measure: deploy frequency, lead time, change failure rate
```

### 13.2 GitHub Flow to trunk-based

Simpler migration since they're already close:

```
1. Add feature flag infrastructure
2. Enforce shorter branch lifetimes (< 1 day vs. < 5 days)
3. Enable merge queue
4. Train team to break work into smaller increments
5. Measure and iterate
```

---

## 14. Measuring Branching Strategy Effectiveness

Use DORA metrics to evaluate whether your branching strategy is working:

| Metric | Elite | High | Medium | Low |
|---|---|---|---|---|
| **Deployment frequency** | On-demand (multiple/day) | Weekly-monthly | Monthly-bimonthly | Fewer than once per 6 months |
| **Lead time for changes** | < 1 hour | 1 day - 1 week | 1 week - 1 month | > 1 month |
| **Change failure rate** | < 5% | 5-10% | 10-15% | > 15% |
| **Time to restore** | < 1 hour | < 1 day | < 1 week | > 1 week |

If your branching strategy is creating friction (high lead time, low deploy
frequency), it's a signal to simplify.

---

## 15. Exercises

1. **Lab — trunk-based conversion.** Take an existing Gitflow project and convert
   it to trunk-based. Document the migration steps and team training needed.

2. **Lab — feature flag.** Implement a feature flag system (Unleash or Flipt)
   and use it to merge an incomplete feature to main safely.

3. **Lab — merge queue.** Set up GitHub's merge queue on a repository. Simulate
   conflicting PRs and verify the queue catches the issue.

4. **Lab — CODEOWNERS.** Define CODEOWNERS for a monorepo with at least 4
   packages. Verify that PRs require the correct reviewers.

5. **Lab — commit conventions.** Set up commitlint + husky in a project. Configure
   automated changelog generation with release-please.

6. **Stretch — monorepo CI.** Set up affected-only CI with Nx or Turborepo. Measure
   CI time reduction vs. running everything.

7. **Stretch — DORA metrics.** Instrument your pipeline to track DORA metrics.
   Compare before/after a branching strategy change.

---

## 16. Recommended Reading

- Forsgren, Humble, Kim, *Accelerate* (2018) — DORA metrics and their correlation
  with branching strategy.
- Paul Hammant, *trunkbaseddevelopment.com* — comprehensive guide to trunk-based.
- Vincent Driessen, *A successful Git branching model* (2010 blog post) — original
  Gitflow.
- GitHub, *Understanding the GitHub Flow* (docs.github.com).
- Martin Fowler, *Feature Toggles (Feature Flags)* (martinfowler.com).
- Google Engineering, *Why Google Stores Billions of Lines of Code in a Single
  Repository* (ACM, 2016).

---

## Glossary

| Term | Definition |
|---|---|
| **Trunk-based** | Branching model where all developers commit to a single main branch with short-lived feature branches |
| **GitHub Flow** | Simplified branching: main + feature branches, deploy on merge |
| **GitLab Flow** | GitHub Flow extended with environment branches for promotion |
| **Gitflow** | Structured model with main, develop, feature, release, and hotfix branches |
| **Release Train** | Scheduled release cadence; features ship when ready by the train date |
| **Feature flag** | Runtime toggle that controls feature visibility independently of deployment |
| **Merge queue** | System that serializes PR merges, testing each against the latest main |
| **CODEOWNERS** | File defining which teams/individuals must review changes to specific paths |
| **Trunk** | The main integration branch (usually called `main` or `master`) |
| **Squash merge** | Compressing all branch commits into a single commit on merge |
| **Rebase merge** | Replaying branch commits on top of the target branch |
| **Conventional Commits** | Commit message format enabling automated versioning and changelogs |
| **DORA metrics** | Four metrics measuring software delivery performance |
| **Monorepo** | Single repository containing multiple projects or services |
| **Affected-only CI** | Running CI checks only for packages/projects impacted by a change |
| **Branch protection** | Rules preventing direct pushes, requiring reviews and CI checks |
