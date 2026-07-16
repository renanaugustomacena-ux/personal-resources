# Module 8.6: Code Review Rubrics

> **Module 08.6** · **Last updated:** 2026-05-22

## Guiding ideas

1. **Code review = teaching + quality + shared ownership.**
2. **Limit PR size: < 400 lines added.** Beyond, comprehension drops.
3. **Comment style: questioning > prescribing. "Why this?" > "Don't do this".**
4. **Rubric: correctness, clarity, security, performance, maintainability.**
5. **Approve != endorsement of every line; flag concerns explicitly.**
6. **Review speed matters: median time-to-first-review < 4 hours.**

---

## 1. Why Code Review Matters

Code review is the single highest-leverage quality practice a team can adopt. It
catches bugs before they reach production, spreads knowledge across the team,
enforces standards, and builds shared ownership of the codebase.

### 1.1 What code review accomplishes

| Goal | Mechanism | Metric |
|---|---|---|
| **Bug prevention** | Human pattern matching catches what tests miss | Defect escape rate |
| **Knowledge sharing** | Every review is a teaching moment | Bus factor per module |
| **Code quality** | Consistent standards enforced socially | Readability score, complexity metrics |
| **Security** | Catch auth gaps, injection, data leaks | Security defects caught in review vs. production |
| **Onboarding** | New engineers learn codebase by reviewing | Time to first meaningful contribution |
| **Documentation** | PR descriptions and review comments are searchable context | "Why was this done?" answered in PR history |

### 1.2 What code review does NOT accomplish

- **Replacing tests**: Review is not a substitute for automated testing.
- **Replacing CI**: Formatting, linting, type-checking should be automated.
- **Architecture design**: Reviews are too late for fundamental design changes.
  Use RFCs/ADRs before coding.
- **Complete security audit**: Reviews catch common issues but are not a
  penetration test.

### 1.3 Code review cost-benefit

Studies consistently show that code review catches 60-70% of defects before
they reach QA or production (Fagan inspections, Microsoft research). The cost is
real — reviewer time, context switching, PR wait time — but the return is high.

The key insight: **review quality degrades sharply after 400 lines**. A 200-line
PR gets thorough review; a 2,000-line PR gets "LGTM."

```
Defect detection rate vs PR size:
  < 200 lines: ~70% defects caught
  200-400 lines: ~50% defects caught
  400-800 lines: ~30% defects caught
  > 800 lines: ~15% defects caught ("LGTM" territory)
```

---

## 2. Review Rubric — The Complete Framework

A review rubric standardizes what reviewers check. Without it, reviews become
inconsistent: one reviewer checks only style, another only correctness, a third
rubber-stamps everything.

### 2.1 Rubric dimensions

| Dimension | Core question | Severity if missed |
|---|---|---|
| **Correctness** | Does it solve the stated problem? | HIGH — shipped bug |
| **Edge cases** | What happens with empty, null, huge, concurrent, malformed input? | HIGH — production incident |
| **Security** | Auth check? SQL injection? XSS? Data exposure? | CRITICAL — vulnerability |
| **Performance** | N+1? O(n²)? Unbounded query? Memory leak? | MEDIUM-HIGH — scaling issue |
| **Error handling** | Errors caught, logged, surfaced to user? No silent failures? | HIGH — hard-to-debug production issues |
| **Tests** | Coverage adequate? Edge cases tested? Tests readable? | MEDIUM — technical debt |
| **API design** | Consistent naming? Backward compatible? Versioned? | MEDIUM — integration breakage |
| **Documentation** | Comments where why isn't obvious? README updated? | LOW-MEDIUM — knowledge loss |
| **Style** | Matches team conventions? Consistent with codebase? | LOW — noise, not bugs |
| **Maintainability** | Readable in 6 months? Reasonable complexity? | MEDIUM — long-term cost |

### 2.2 Detailed rubric per dimension

#### 2.2.1 Correctness

```
□ Does the code solve the stated problem in the ticket/issue?
□ Are all acceptance criteria met?
□ Do the tests actually verify the behavior (not just exercise the code)?
□ Is the logic correct for all branches?
□ Are assumptions documented if not obvious?
□ Is the code idempotent where it should be? (especially API handlers, event consumers)
□ Are race conditions handled? (check-then-act without locking?)
□ Is the data transformation correct? (units, encoding, timezone)
```

**Common correctness bugs caught in review:**

| Bug pattern | Example | Detection strategy |
|---|---|---|
| Off-by-one | `for (let i = 0; i <= arr.length; ...)` | Trace loop boundaries manually |
| Wrong comparison | `if (a = b)` instead of `if (a === b)` | Check all conditionals |
| Null dereference | `user.address.city` without null check | Follow the data flow |
| Type coercion | `"5" + 3` → `"53"` in JavaScript | Check mixed-type operations |
| Incorrect enum | Wrong status constant used | Verify against spec |
| Missing await | `async function` called without `await` | Check all async calls |
| Wrong error code | `return 200` for an error case | Verify HTTP status codes |

#### 2.2.2 Edge cases

```
□ Empty input (empty string, empty array, null, undefined, 0)
□ Boundary values (MAX_INT, empty string vs null, -1, 0, 1)
□ Unicode (emoji, RTL text, zero-width characters, long multi-byte strings)
□ Large input (100K items, 10MB payload, 50 concurrent requests)
□ Concurrent access (two users editing same resource simultaneously)
□ Time-sensitive (midnight, DST transition, leap second, year boundary)
□ Malformed input (invalid JSON, truncated payload, wrong encoding)
□ Network failures (timeout, partial response, DNS failure, connection reset)
```

#### 2.2.3 Security

```
□ Authentication: Is the endpoint protected? Correct auth middleware applied?
□ Authorization: Does the user have permission for this specific resource?
□ Input validation: All external input validated before processing?
□ SQL injection: Parameterized queries used? No string concatenation?
□ XSS: Output encoded? No raw HTML insertion from user input?
□ CSRF: State-changing endpoints protected with tokens?
□ Path traversal: File paths sanitized? No `../` in user-controlled paths?
□ Data exposure: No PII in logs? No secrets in responses? No verbose errors?
□ Rate limiting: Endpoint rate-limited appropriately?
□ Mass assignment: Only allowed fields accepted from request body?
□ IDOR: Object references validated against the authenticated user's access?
□ Cryptography: No custom crypto? Using well-known libraries? Keys managed properly?
```

#### 2.2.4 Performance

```
□ N+1 queries: Loop that issues a query per iteration?
□ Algorithmic complexity: O(n²) where O(n log n) exists?
□ Unbounded queries: SELECT without LIMIT or WHERE? Pagination missing?
□ Missing indexes: Query filtering on unindexed columns?
□ Memory: Loading entire dataset into memory? Streaming possible?
□ Connection pooling: Creating new connections per request?
□ Caching: Expensive computation that could be cached?
□ Payload size: Returning more data than the client needs?
□ Regex: Catastrophic backtracking possible? (ReDoS)
□ Lock contention: Holding locks longer than necessary?
```

**N+1 query example (caught in review):**

```python
# BAD: N+1 — one query per order
orders = Order.objects.filter(user=user)
for order in orders:
    items = OrderItem.objects.filter(order=order)  # N queries
    ...

# GOOD: Eager loading — 2 queries total
orders = Order.objects.filter(user=user).prefetch_related('items')
for order in orders:
    items = order.items.all()  # No additional query
    ...
```

#### 2.2.5 Error handling

```
□ All error paths handled (not just happy path)?
□ Errors propagated with context (not swallowed)?
□ User-facing errors are friendly (no stack traces in API responses)?
□ Errors logged with enough context to debug (request ID, user ID, input)?
□ Transient errors retried with backoff?
□ Partial failures handled (batch operation: what if item 3/10 fails)?
□ Resource cleanup on error (file handles, connections, transactions)?
□ Error types specific (not generic catch-all)?
```

#### 2.2.6 Tests

```
□ Tests exist for new functionality?
□ Tests verify behavior, not implementation details?
□ Edge cases covered (empty, null, boundary)?
□ Error cases tested (what happens when it fails)?
□ Test names describe the behavior under test?
□ Tests are independent (no shared mutable state between tests)?
□ Mocks are reasonable (not mocking everything)?
□ Integration tests for cross-boundary logic?
□ No test code in production paths?
□ Coverage meets team minimum (typically 80%)?
```

#### 2.2.7 API design

```
□ RESTful conventions followed? (correct HTTP verbs, status codes, URL patterns)
□ Backward compatible? (no breaking changes without version bump)
□ Consistent naming with existing API surface?
□ Error responses follow standard format?
□ Pagination for list endpoints?
□ Idempotent where expected? (PUT, DELETE)
□ Rate limiting documented?
□ OpenAPI spec updated?
```

#### 2.2.8 Maintainability

```
□ Code is readable without comments (good names, clear flow)?
□ Functions are small (< 50 lines)?
□ Files are focused (< 800 lines)?
□ No deep nesting (> 4 levels)?
□ No magic numbers (named constants)?
□ No code duplication (DRY)?
□ Complexity reasonable (cyclomatic < 10 per function)?
□ Dependencies justified (not adding a library for one utility function)?
□ Configuration externalized (no hardcoded URLs, ports, limits)?
□ Feature flags have TTL (not permanent tech debt)?
```

---

## 3. PR Templates

PR templates guide authors to provide the information reviewers need.

### 3.1 Standard PR template

```markdown
<!-- .github/pull_request_template.md -->

## Summary
<!-- 1-3 sentences: what and why, not how -->

## Changes
<!-- Bulleted list of significant changes -->

## Type
- [ ] feat: New feature
- [ ] fix: Bug fix
- [ ] refactor: Code restructuring
- [ ] docs: Documentation
- [ ] test: Tests
- [ ] chore: Tooling/config

## Testing
<!-- How was this tested? What test cases were added? -->
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Screenshots
<!-- If UI changes, before/after screenshots -->

## Checklist
- [ ] Self-review completed
- [ ] Tests pass locally
- [ ] No new warnings
- [ ] Documentation updated (if applicable)
- [ ] Breaking changes documented (if applicable)

## Related Issues
<!-- Closes #123, Relates to #456 -->
```

### 3.2 Security-sensitive PR template

```markdown
<!-- .github/PULL_REQUEST_TEMPLATE/security.md -->

## Summary
<!-- What security-relevant change is being made? -->

## Threat Model
<!-- What threats does this address or introduce? -->

## Security Checklist
- [ ] Input validation on all external data
- [ ] Authentication/authorization verified
- [ ] No secrets in code or logs
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF protection
- [ ] Rate limiting
- [ ] Data classification considered (PII handling)

## Security Review
- [ ] Reviewed by @security-team member
```

### 3.3 Database migration PR template

```markdown
<!-- .github/PULL_REQUEST_TEMPLATE/migration.md -->

## Summary
<!-- What schema change is being made and why? -->

## Migration
- [ ] Migration is reversible (has down migration)
- [ ] Migration tested on production-size dataset
- [ ] Migration locks analyzed (will it lock tables?)
- [ ] Backward compatible (old code works with new schema)
- [ ] Forward compatible (new code works with old schema)

## Performance Impact
<!-- Estimated migration time on production data volume -->
- Table size: ~N rows
- Estimated lock time: ~N seconds
- Estimated total time: ~N minutes

## Rollback Plan
<!-- Steps to revert if migration causes issues -->
```

---

## 4. Review Comment Etiquette

### 4.1 Comment prefixes

Consistent prefixes reduce ambiguity about comment severity:

| Prefix | Meaning | Action required |
|---|---|---|
| `blocking:` | Must fix before merge | Yes, fix required |
| `nit:` | Minor style or formatting issue | Optional |
| `question:` | Requesting clarification, not necessarily a change | Respond |
| `suggestion:` | Alternative approach, take-or-leave | Consider |
| `praise:` | Calling out good work | None (builds team morale) |
| `thought:` | Observation for future consideration | Acknowledge |
| `todo:` | Acceptable now but needs follow-up | Create ticket |

### 4.2 Comment tone guidelines

**Good comment:**
```
question: I see this retries 3 times with no backoff. 
What happens if the downstream service is overloaded? 
Exponential backoff might prevent a thundering herd.
See: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
```

**Bad comment:**
```
This is wrong. You should use exponential backoff.
```

**Good comment:**
```
suggestion: Consider extracting this block into a separate function.
It's doing three distinct things: validation, transformation, and persistence.
Splitting would make each part independently testable.
```

**Bad comment:**
```
This function is too long.
```

### 4.3 Principles

| Principle | Explanation |
|---|---|
| **Ask, don't tell** | "Have you considered X?" > "Do X." |
| **Explain why** | Rationale makes feedback actionable |
| **Distinguish severity** | Use prefixes so authors prioritize |
| **Acknowledge good work** | "praise: This error handling is thorough" builds culture |
| **Review the code, not the person** | "This function" not "You wrote this badly" |
| **Be timely** | Review within 4 hours; don't block others |
| **Assume competence** | The author may know something you don't |
| **Offer alternatives** | Don't just say "bad"; show what "better" looks like |

### 4.4 Responding to reviews

| Do | Don't |
|---|---|
| Address every comment (resolve or explain) | Ignore comments |
| Explain reasoning if you disagree | Get defensive |
| Ask for clarification if feedback is unclear | Assume bad intent |
| Mark resolved comments as resolved | Leave threads hanging |
| Thank reviewers for catching issues | Take feedback personally |
| Create follow-up tickets for deferred items | Commit to fixing "later" without a ticket |

---

## 5. Review Automation

Automate what machines do better than humans: style checks, formatting, type
checking, test coverage, dependency audits. Reserve human review for correctness,
design, security, and context-dependent judgment.

### 5.1 What to automate vs. what humans review

| Automated (CI) | Human review |
|---|---|
| Formatting (prettier, gofmt, black) | Correctness of logic |
| Linting (eslint, golint, ruff) | Design and architecture fit |
| Type checking (tsc, mypy, go vet) | Security implications |
| Test execution and coverage | Edge case identification |
| Dependency vulnerability scan | Naming and readability |
| Commit message format | Performance implications |
| PR size check | Business logic correctness |
| Branch naming convention | Error handling completeness |
| License compliance | API design consistency |

### 5.2 Danger.js

Danger runs during CI and posts automated review comments on PRs. It codifies
team conventions into executable rules.

```javascript
// dangerfile.ts
import { danger, warn, fail, message } from 'danger';

// PR size check
const linesChanged = danger.github.pr.additions + danger.github.pr.deletions;
if (linesChanged > 400) {
  warn(`PR is ${linesChanged} lines. Consider splitting into smaller PRs.`);
}
if (linesChanged > 1000) {
  fail(`PR exceeds 1000 lines. Must be split before review.`);
}

// Missing tests check
const srcChanges = danger.git.modified_files.filter(f => f.startsWith('src/'));
const testChanges = danger.git.modified_files.filter(f => f.includes('.test.') || f.includes('.spec.'));
if (srcChanges.length > 0 && testChanges.length === 0) {
  warn('Source files changed but no test files were modified. Please add tests.');
}

// Missing description
if (!danger.github.pr.body || danger.github.pr.body.length < 50) {
  fail('PR description is too short. Please describe what and why.');
}

// Security-sensitive file changes
const securityFiles = danger.git.modified_files.filter(f =>
  f.includes('auth') || f.includes('security') || f.includes('crypto') ||
  f.includes('payment') || f.includes('token')
);
if (securityFiles.length > 0) {
  warn(`Security-sensitive files modified: ${securityFiles.join(', ')}. ` +
       'Please request review from @security-team.');
}

// Database migration check
const migrationFiles = danger.git.created_files.filter(f => f.includes('migration'));
if (migrationFiles.length > 0) {
  message('Database migration detected. Please verify:\n' +
    '- Migration is reversible\n' +
    '- Tested on production-size dataset\n' +
    '- No long table locks');
}

// Package.json changes
const packageChanged = danger.git.modified_files.includes('package.json');
const lockfileChanged = danger.git.modified_files.includes('pnpm-lock.yaml') ||
                        danger.git.modified_files.includes('package-lock.json');
if (packageChanged && !lockfileChanged) {
  fail('package.json changed but lockfile was not updated. Run `pnpm install`.');
}

// Console.log check
const jsFiles = danger.git.modified_files.filter(f =>
  f.endsWith('.ts') || f.endsWith('.tsx') || f.endsWith('.js')
);
for (const file of jsFiles) {
  const diff = await danger.git.diffForFile(file);
  if (diff && diff.added.includes('console.log')) {
    warn(`\`console.log\` found in ${file}. Remove before merge.`);
  }
}

// Changelog check for features
const isFeat = danger.github.pr.title.startsWith('feat');
const changelogChanged = danger.git.modified_files.includes('CHANGELOG.md');
if (isFeat && !changelogChanged) {
  warn('New feature PR but CHANGELOG.md not updated.');
}
```

```yaml
# GitHub Actions integration
- name: Danger
  uses: danger/danger-js@v12
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 5.3 ReviewBot and similar tools

| Tool | Platform | What it does |
|---|---|---|
| **Danger.js** | GitHub, GitLab, Bitbucket | Custom rules as code, posts comments |
| **ReviewBot** | GitHub | Automated review based on configurable rules |
| **Reviewdog** | GitHub, GitLab | Runs linters and posts results as review comments |
| **SonarQube** | Any (CI integration) | Code quality, security hotspots, tech debt |
| **CodeClimate** | GitHub | Maintainability, test coverage tracking |
| **Codacy** | GitHub, GitLab, Bitbucket | Automated code review, patterns, duplication |
| **Semgrep** | Any (CI integration) | Lightweight static analysis with custom rules |

### 5.4 Reviewdog integration

Reviewdog posts linter results as inline PR comments, exactly where the issue is.

```yaml
# GitHub Actions with reviewdog
- name: Run ESLint with reviewdog
  uses: reviewdog/action-eslint@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    reporter: github-pr-review      # Posts as review comments
    eslint_flags: 'src/'

- name: Run golangci-lint with reviewdog
  uses: reviewdog/action-golangci-lint@v2
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    reporter: github-pr-review
```

### 5.5 Coverage enforcement

```yaml
# Fail CI if coverage drops below threshold
- name: Check test coverage
  run: |
    npx jest --coverage --coverageThreshold='{
      "global": {
        "branches": 80,
        "functions": 80,
        "lines": 80,
        "statements": 80
      }
    }'

# Post coverage report as PR comment
- name: Coverage Report
  uses: romeovs/lcov-reporter-action@v0.4
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    lcov-file: coverage/lcov.info
```

---

## 6. PR Size and Review Load

### 6.1 Optimal PR size

Research (Google Engineering Practices, Microsoft studies) consistently shows:

| PR size (lines added) | Review quality | Review time | Reviewer engagement |
|---|---|---|---|
| < 100 | Excellent | < 15 min | High |
| 100-200 | Very good | 15-30 min | High |
| 200-400 | Good | 30-60 min | Moderate |
| 400-800 | Degraded | 60-120 min | Low |
| > 800 | Poor ("LGTM") | Variable | Very low |

### 6.2 Strategies for small PRs

| Technique | Description |
|---|---|
| **Stacked PRs** | Break feature into sequential PRs, each building on the previous |
| **Incremental delivery** | Ship behavior behind a feature flag in multiple PRs |
| **Extract-then-use** | PR 1: extract utility/refactor. PR 2: use it for the feature |
| **Schema-first** | PR 1: database migration. PR 2: business logic. PR 3: UI |
| **Interface-first** | PR 1: define interface/types. PR 2: implement. PR 3: integrate |

### 6.3 Stacked PRs

Stacked PRs are a chain where each PR builds on the previous one. They let you
break a large feature into reviewable increments while keeping the full context.

```
main ← PR 1: Add User model and migration
         ← PR 2: Add UserRepository and unit tests
           ← PR 3: Add UserService with business logic
             ← PR 4: Add UserController and API endpoints
               ← PR 5: Add frontend form and integration tests
```

**Tools for stacked PRs:**

| Tool | Platform | Features |
|---|---|---|
| **graphite.dev** | GitHub | CLI + web UI, auto-restack, PR dependencies |
| **ghstack** (Meta) | GitHub | Push stack of commits as individual PRs |
| **spr** (Evernote) | GitHub | One commit = one PR, auto-rebase |
| **git-branchless** | Any | Local stacked branches, interactive rebase |
| **Aviator** | GitHub | Stack management + merge queue |

```bash
# Graphite CLI workflow
gt create feat/user-model     # Create first PR in stack
# ... commit work ...
gt create feat/user-repo      # Create second PR, stacked on first
# ... commit work ...
gt create feat/user-service   # Create third PR
gt submit                     # Push all PRs to GitHub with dependencies
gt sync                       # Restack all PRs after changes
```

### 6.4 Review load balancing

If a few team members receive all review requests, review quality drops and
those individuals become bottlenecks.

**Load balancing strategies:**

| Strategy | Implementation |
|---|---|
| **Round-robin** | GitHub auto-assign: rotate reviewers within a team |
| **Load-based** | Assign to team member with fewest open review requests |
| **Domain-based** | CODEOWNERS routes reviews to relevant experts |
| **Buddy system** | Each engineer has a primary review buddy (rotates monthly) |
| **Review duty** | One team member is "on review duty" each day |

```yaml
# GitHub auto-assign configuration
# .github/auto_assign.yml (with auto-assign action)
addReviewers: true
addAssignees: false
numberOfReviewers: 2
reviewers:
  - engineer-a
  - engineer-b
  - engineer-c
  - engineer-d
skipAlreadyAssigned: true
skipAlreadyReviewed: true
```

### 6.5 Review speed metrics

| Metric | Target | Why it matters |
|---|---|---|
| **Time to first review** | < 4 hours | Unblocks author quickly |
| **Time to approval** | < 24 hours | Prevents stale branches |
| **Review iterations** | < 3 rounds | More rounds = unclear initial feedback |
| **Review queue depth** | < 5 per reviewer | Beyond 5, quality drops |
| **PR age at merge** | < 48 hours | Stale PRs accumulate conflicts |

**Measuring review speed:**

```bash
# GitHub CLI: list open PRs with age
gh pr list --state open --json number,title,createdAt,reviewRequests \
  --jq '.[] | "\(.number) | \(.title) | \(.createdAt) | reviewers: \(.reviewRequests | length)"'
```

Tools for metrics: **LinearB**, **Sleuth**, **Swarmia**, **Pluralsight Flow**
(formerly GitPrime), **GitHub Insights** (Enterprise).

---

## 7. Specialized Review Checklists

### 7.1 Database migration review

```
□ Migration is reversible (has rollback/down migration)
□ Tested on production-size dataset
□ No long-running table locks (ALTER TABLE on large tables)
□ New columns are nullable or have defaults (backward compatible)
□ Indexes added for new query patterns
□ Old column/table dropped only after all code paths updated
□ Data migration separated from schema migration
□ Estimated lock time documented in PR
□ Tested with concurrent traffic
```

### 7.2 API endpoint review

```
□ Correct HTTP method and status codes
□ Input validation with descriptive error messages
□ Authentication and authorization middleware applied
□ Rate limiting configured
□ Pagination for list endpoints
□ Consistent response format with existing API
□ OpenAPI spec updated
□ Backward compatible (no breaking changes without version bump)
□ Error responses include request ID for debugging
□ Request/response logged (without PII)
```

### 7.3 Frontend/UI review

```
□ Responsive at all breakpoints (320, 768, 1024, 1440)
□ Keyboard navigable
□ Screen reader compatible (ARIA labels, semantic HTML)
□ Loading states handled (spinner, skeleton, error)
□ Empty states handled (no data, first use)
□ Error states handled (network error, validation error)
□ No layout shift (explicit dimensions on images, skeleton loaders)
□ Performance: no unnecessary re-renders
□ Accessibility: color contrast >= 4.5:1
□ i18n: no hardcoded strings (if applicable)
```

### 7.4 Infrastructure/IaC review

```
□ Least privilege IAM permissions (no wildcards)
□ Encryption at rest and in transit
□ No secrets in IaC files (use secret references)
□ Resource naming follows convention
□ Tags applied (environment, team, cost-center)
□ Destroy prevention on critical resources
□ Change is backward compatible (won't destroy and recreate)
□ Cost estimate reviewed (Infracost or similar)
□ Terraform plan output reviewed (no unexpected destroys)
□ State file management addressed (remote state, locking)
```

### 7.5 Dependency update review

```
□ Changelog reviewed for breaking changes
□ Major version bumps have migration steps documented
□ License compatible with project
□ Security advisories checked (npm audit, pip-audit, cargo audit)
□ CI passes with new version
□ Lock file updated
□ No unnecessary transitive dependency changes
□ Release recency: last release within 12 months?
□ Maintenance status: active maintainers?
```

---

## 8. Review Anti-Patterns

### 8.1 Reviewer anti-patterns

| Anti-pattern | Description | Fix |
|---|---|---|
| **Rubber stamp** | "LGTM" without actually reading the code | Use rubric, require meaningful comment |
| **Nitpick firehose** | 30 style comments, 0 correctness comments | Automate style; focus on substance |
| **Gatekeeper** | Blocks PRs for personal preferences not in style guide | Codify rules or defer to author |
| **Ghost reviewer** | Assigned but never reviews | Time-box reviews; escalate after 24h |
| **Scope creep** | "While you're at it, refactor X" | Create separate ticket for refactors |
| **Rewrite reviewer** | Would have written it differently = wrong | Accept multiple valid approaches |
| **Delayed reviewer** | Reviews after 3 days when context is lost | Review within 4 hours |
| **Inconsistent reviewer** | Different standards for different people | Use written rubric |

### 8.2 Author anti-patterns

| Anti-pattern | Description | Fix |
|---|---|---|
| **Mega PR** | 2,000-line PR with 15 changed files | Break into smaller PRs |
| **WIP PR with no context** | "WIP please review" with no description | Fill PR template before requesting review |
| **Defensive author** | Argues every comment without considering feedback | Assume good intent |
| **Drive-by merger** | Merges immediately after one "LGTM" | Wait for required reviewers |
| **Comment ignorer** | Marks comments resolved without addressing them | Address or discuss every comment |
| **Test skipper** | "Tests coming in follow-up PR" (never comes) | Tests in same PR or create ticket immediately |
| **Force pusher** | Force pushes during review, losing comment context | Use incremental commits during review |

### 8.3 Process anti-patterns

| Anti-pattern | Description | Fix |
|---|---|---|
| **No reviewers required** | PRs merge without any review | Branch protection: require 1+ reviews |
| **Everyone reviews everything** | 8 reviewers assigned, 1 actually reads | 2 reviewers max, use CODEOWNERS |
| **Review after merge** | Code ships, review is retroactive | Enforce pre-merge review |
| **No CI before review** | Reviewers catch lint errors | CI must pass before review starts |
| **Review not tracked** | No metrics on review speed or quality | Instrument review process |

---

## 9. Review Process Workflows

### 9.1 Standard workflow

```
Author creates PR
    │
    ▼
CI runs (lint, test, type-check, build)
    │
    ├── CI fails → Author fixes → CI re-runs
    │
    ▼ CI passes
Automated checks (Danger.js, coverage, PR size)
    │
    ▼
Reviewer assigned (auto-assign or CODEOWNERS)
    │
    ▼
Reviewer reviews using rubric
    │
    ├── Comments left → Author addresses → Re-review
    │
    ▼ Approved
Merge queue (if enabled)
    │
    ▼
Merge to main → Deploy
```

### 9.2 Security-sensitive workflow

```
Author creates PR touching auth/payments/crypto
    │
    ▼
CI runs (including SAST scan, dependency audit)
    │
    ▼
Danger.js flags security-sensitive files
    │
    ▼
CODEOWNERS assigns @security-team
    │
    ▼
Domain reviewer reviews functionality
    │
    ▼
Security reviewer reviews security aspects
    │
    ├── Security issues found → Must fix → Re-review
    │
    ▼ Both approved
Merge
```

### 9.3 Emergency hotfix workflow

```
Production incident confirmed
    │
    ▼
Author creates hotfix branch from main
    │
    ▼
Fix implemented with minimal scope
    │
    ▼
CI runs (abbreviated: critical tests only)
    │
    ▼
Expedited review (1 senior reviewer, synchronous)
    │
    ▼
Merge and deploy immediately
    │
    ▼
Full review within 24h (retroactive, more thorough)
    │
    ▼
Follow-up PR for proper fix (if hotfix was a band-aid)
```

---

## 10. Self-Review Before Requesting Review

Authors should self-review before requesting review. This catches the obvious
issues and shows respect for the reviewer's time.

### 10.1 Author's self-review checklist

```
Before requesting review:
□ Read your own diff line by line
□ PR description is complete (what, why, testing, screenshots)
□ CI is green
□ No debug statements (console.log, print, debugger)
□ No commented-out code
□ No TODO without a ticket number
□ Tests added for new behavior
□ Tests pass locally
□ Documentation updated if needed
□ Commit messages follow convention
□ PR size < 400 lines (or justified in description)
□ No secrets, keys, or tokens in code
□ No unintended file changes (e.g., IDE config, lockfile churn)
```

### 10.2 The "fresh eyes" technique

After finishing code, wait 30 minutes before self-reviewing. This reduces
confirmation bias — you'll read what the code actually does, not what you
intended it to do.

---

## 11. Review Culture

### 11.1 Building a healthy review culture

| Practice | Description |
|---|---|
| **Review speed as a team value** | Track and discuss review latency in retros |
| **Praise in reviews** | Call out good patterns, not just problems |
| **Learning over gatekeeping** | Reviews are teaching opportunities |
| **Written standards** | Style guide + rubric eliminate subjective debates |
| **Automate the automatable** | Humans review logic; machines review format |
| **Rotate reviewers** | Prevents knowledge silos and reviewer burnout |
| **Review onboarding** | New engineers shadow reviews before leading them |
| **Blameless feedback** | "The code" has issues, not "you" |

### 11.2 Google's code review guidelines (summary)

Key principles from Google's Engineering Practices documentation:

1. **Reviewers should approve a CL that improves the overall code health of the
   system, even if it isn't perfect.** Perfect is the enemy of shipped.

2. **Reviewers should favor approving a CL once it reaches a state where it
   definitely improves the code health, even if there are minor things that could
   be improved.** Leave minor suggestions as non-blocking comments.

3. **There is no such thing as "perfect" code — there is only "better" code.**
   Accept that every PR makes the codebase better, not perfect.

4. **Technical facts and data overrule opinions and personal preferences.**
   "I prefer" is not a blocking reason unless backed by data.

5. **Style should be consistent with the existing codebase.** If no style guide
   exists, accept the author's style (it's their code to maintain).

### 11.3 Review retrospectives

Quarterly, review the review process itself:

```
Review retrospective agenda:
1. Review speed metrics (time to first review, time to merge)
2. Review quality (defects caught in review vs. escaped to production)
3. Review load distribution (is it balanced across the team?)
4. Common themes in review feedback (repeated issues → add linting rule)
5. Team satisfaction with review process (survey)
6. Action items for improvement
```

---

## 12. Exercises

1. **Lab — rubric application.** Apply the complete review rubric to 3 recent PRs
   in your project. Document findings by rubric dimension. Identify which
   dimensions were previously under-reviewed.

2. **Lab — Danger.js setup.** Configure Danger.js for a project with at least 5
   rules: PR size, missing tests, missing description, security file changes,
   and console.log detection.

3. **Lab — PR template.** Create PR templates for your project: a standard
   template and a security-sensitive template. Ensure they're enforced via
   GitHub repository settings.

4. **Lab — review metrics.** Measure time-to-first-review and time-to-merge for
   the last 20 PRs on your project. Identify bottlenecks.

5. **Stretch — stacked PRs.** Break a large feature into a stack of 3-5 PRs using
   graphite or ghstack. Document the experience.

6. **Stretch — automated review pipeline.** Build a full automated review pipeline:
   reviewdog + coverage enforcement + Danger.js + CODEOWNERS.

---

## 13. Recommended Reading

- Google, *Engineering Practices: Code Review* (google.github.io/eng-practices).
- Microsoft Research, *Code Reviewing Best Practices* (research.microsoft.com).
- Michaela Greiler, *Code Review Checklist* (michaelagreiler.com).
- Trisha Gee, *Code Review Best Practices* (JetBrains blog).
- Gunnar Morling, *The Code Review Pyramid* (blog.gunnarmorling.de).

---

## Glossary

| Term | Definition |
|---|---|
| **PR (Pull Request)** | Request to merge a branch into another, with review |
| **CR (Code Review)** | Human review of code changes before merge |
| **LGTM** | "Looks Good To Me" — approval signal |
| **Nit** | Minor, non-blocking style suggestion |
| **Blocking** | Comment that must be addressed before merge |
| **Rubber stamp** | Approval without meaningful review |
| **Stacked PR** | Chain of PRs where each builds on the previous |
| **CODEOWNERS** | File defining who must review changes to specific paths |
| **Danger.js** | CI tool that automates PR review checks |
| **Reviewdog** | CI tool that posts linter results as review comments |
| **Bus factor** | Number of people who must leave before knowledge is lost |
| **Rubric** | Structured framework for consistent evaluation |
| **Self-review** | Author reviewing their own diff before requesting peer review |
| **Review queue** | Backlog of PRs awaiting review by a reviewer |
| **Merge queue** | System that serializes merges, testing each against latest main |
| **SonarQube** | Platform for code quality analysis and technical debt tracking |
