---
corso: "SWE Masterclass"
fase: "5 — DevOps & Cloud Native"
modulo: "5.3"
titolo: "Site Reliability Engineering (SRE)"
versione: "Google SRE Workbook (2018), OpenSLO 1.0, Prometheus 3.x"
livello: "Advanced"
prerequisiti:
  - "Familiarity with monitoring and alerting concepts (Prometheus, Grafana)"
  - "Understanding of distributed systems failure modes"
  - "Container orchestration basics (Kubernetes) — Module 5.2"
  - "Experience with on-call or incident response workflows"
obiettivi:
  - "Define SLIs, SLOs, and error budgets for a multi-tier web service"
  - "Implement burn-rate alerting using multi-window, multi-burn-rate rules in Prometheus"
  - "Conduct a blameless postmortem and produce an actionable remediation plan"
  - "Measure, classify, and systematically reduce toil below 50% of SRE time"
  - "Design an error-budget policy that governs feature-freeze and reliability investment decisions"
tag: [sre, reliability, slo, sli, error-budget, toil, postmortem, incident-response, observability, chaos-engineering]
---

# Module 5.3: Site Reliability Engineering (SRE)

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Design SLI/SLO specifications for availability, latency, and correctness using the good-events / valid-events ratio model.
> - Calculate error budgets, set burn-rate thresholds, and wire multi-window alerts in Prometheus or a managed observability platform.
> - Facilitate a blameless postmortem following the Google SRE template, producing a timeline, root-cause analysis, and prioritised action items.
> - Quantify toil with a structured taxonomy (manual, repetitive, automatable, no enduring value) and prioritise elimination projects by ROI.
> - Draft and ratify an error-budget policy document that triggers feature freezes, mandates reliability sprints, and defines escalation paths.

> **Module 05.3** · **Last updated:** 2026-05-22

## Guiding ideas
1. **Error budget = 1 - SLO.** Central concept of SRE practice.
2. **Toil reduction: < 50% of SRE time.**
3. **Blameless postmortem culture.**
4. **Embedded SRE per service team at scale.**
5. **Reliability hierarchy: monitoring → incident response → postmortem → testing → capacity planning → product development.**

**Date:** 2026-05-22
**Status:** Completed

---

## 1. What SRE Is (and Is Not)

Site Reliability Engineering is a discipline that applies software engineering principles to operations. Coined at Google circa 2003, formalized in the 2016 "Site Reliability Engineering" book (Beyer, Jones, Petoff, Murphy).

**SRE is:**
- Engineering reliability into systems through automation, measurement, and principled risk management.
- Using software engineering skills to solve operational problems.
- A specific implementation of DevOps principles with concrete practices and measurable outcomes.

**SRE is not:**
- A rebranding of operations or sysadmin.
- A title you give to the on-call team without changing anything.
- Only for Google-scale companies. The principles scale down to small teams.

### 1.1 SRE vs DevOps vs Platform Engineering

| Dimension | DevOps | SRE | Platform Engineering |
|:----------|:-------|:----|:--------------------|
| **Focus** | Culture and collaboration | Reliability through engineering | Developer self-service |
| **Metrics** | DORA metrics | SLI/SLO/Error budgets | Developer experience, adoption |
| **Practices** | CI/CD, IaC, monitoring | Error budgets, toil reduction, incident management | Internal developer platforms, golden paths |
| **Team structure** | Embedded or cross-functional | Embedded or centralized | Dedicated platform team |
| **Origin** | 2008, Patrick Debois | 2003, Google (Ben Treynor) | 2020s, evolution of DevOps/SRE |

DevOps is the cultural philosophy. SRE is a concrete methodology. Platform engineering builds the tooling. They are complementary, not competing.

### 1.2 The Dickerson Reliability Hierarchy

Like Maslow's hierarchy but for reliability. You must satisfy lower levels before higher levels provide value:

```
                    ┌────────────┐
                    │  Product   │  Feature development
                    ├────────────┤
                    │ Capacity   │  Capacity planning
                    │ Planning   │
                    ├────────────┤
                    │  Testing   │  Testing + release
                    │ + Release  │  engineering
                    ├────────────┤
                    │Postmortem/ │  Learning from
                    │Root Cause  │  failures
                    ├────────────┤
                    │ Incident   │  Responding to
                    │ Response   │  outages
                    ├────────────┤
                    │ Monitoring │  Knowing what is
                    │            │  happening
                    └────────────┘
```

If your monitoring is poor, investing in capacity planning is wasted — you cannot plan capacity if you cannot measure usage. Fix the foundation first.

---

## 2. SLI / SLO / SLA Design

### 2.1 Definitions

**SLI (Service Level Indicator):** A quantitative measure of a specific aspect of service quality. Always expressed as a ratio:

$$\text{SLI} = \frac{\text{good events}}{\text{valid events}}$$

**SLO (Service Level Objective):** An internal target for the SLI over a specific time window:
- "99.9% of HTTP requests return non-5xx in a rolling 30-day window."

**SLA (Service Level Agreement):** An external, contractual commitment. Violating an SLA has business consequences (refunds, credits, contract penalties):
- "If monthly uptime falls below 99.5%, customer receives 10% service credit."

**Relationship:** SLA < SLO < achievable performance. The SLO is your internal operating target. The SLA is what legal signs. Always leave margin between them.

### 2.2 Choosing Good SLIs

**Categories of SLIs:**

| SLI Type | What it measures | Example |
|:---------|:----------------|:--------|
| **Availability** | Is the service up? | % of requests returning non-5xx |
| **Latency** | How fast is it? | % of requests < 200ms at p99 |
| **Correctness** | Are results right? | % of responses matching expected output |
| **Freshness** | Is data current? | % of time data is < 1 minute old |
| **Throughput** | Can it handle load? | % of time throughput > minimum threshold |
| **Durability** | Is data preserved? | % of written data retrievable after 30 days |
| **Coverage** | Does it process everything? | % of expected items processed in pipeline |

**Rules for good SLIs:**
1. Measure from the user's perspective, not the server's.
2. Measure at the boundary closest to the user (load balancer, CDN edge, mobile client).
3. Avoid internal implementation metrics as SLIs (CPU usage is not an SLI).
4. SLIs must be automatable — no human judgment in measurement.

### 2.3 SLI Measurement Methods

| Method | Pros | Cons |
|:-------|:-----|:-----|
| **Server-side metrics** (request logs, Prometheus) | Easy to implement, rich detail | Misses client-side failures, CDN caching |
| **Load balancer logs** (ALB, Nginx, Envoy) | Closer to user, captures all traffic | Limited application-level detail |
| **Synthetic monitoring** (probes, uptime checks) | Measures from user's location | Limited coverage, only tests probe scenarios |
| **Client-side telemetry** (RUM, mobile SDK) | True user experience | Noisy, sampling required, privacy concerns |

**Best practice:** Combine server-side metrics (primary SLI) with synthetic monitoring (canary SLI) and client-side telemetry (user experience SLI).

### 2.4 Window Types

**Rolling window (preferred):**
- "99.9% over the last 30 days."
- Continuously evaluated. Yesterday's outage still counts today.
- Better for operational decision-making.

**Calendar window:**
- "99.9% per calendar month."
- Resets at month boundary. An outage on the 30th is forgotten on the 1st.
- Better for contractual SLAs (billing cycles).

### 2.5 SLO Design Process

```
1. Identify user journeys (login, checkout, search, data export)
2. For each journey, identify the SLIs that matter
   - What does "working" mean for this journey?
   - What does "fast enough" mean?
3. Set initial SLO targets based on:
   - Historical performance (what has the system achieved?)
   - User expectations (what do users tolerate?)
   - Business requirements (what does the contract say?)
4. Implement SLI measurement
5. Run for 2-4 weeks in "observation mode" — measure but don't enforce
6. Refine SLO targets based on observed data
7. Set up burn-rate alerts
8. Begin error budget policy enforcement
```

### 2.6 Availability Math

| SLO | Allowed downtime / 30 days | Allowed downtime / year |
|:----|:--------------------------|:-----------------------|
| 99.0% | 7h 12m | 3d 15h 36m |
| 99.5% | 3h 36m | 1d 19h 48m |
| 99.9% | **43m 12s** | **8h 45m 36s** |
| 99.95% | 21m 36s | 4h 22m 48s |
| 99.99% | 4m 19s | 52m 34s |
| 99.999% | 26s | 5m 15s |

Each additional "nine" costs approximately 10x in engineering effort. Choose deliberately. Most services do not need 99.99%.

**Composite availability:** If Service A (99.9%) depends on Service B (99.9%), the combined availability is at most 99.9% × 99.9% = 99.8% (assuming serial dependency). With N serial dependencies each at 99.9%, availability drops to 99.9%^N. At 10 dependencies: 99.0%.

---

## 3. Error Budgets

### 3.1 The Concept

$$\text{Error Budget} = (1 - \text{SLO}) \times \text{Window}$$

With a 99.9% SLO over 30 days, your error budget is 0.1% × 30 days = 43 minutes of downtime.

**The budget is a currency:** You "spend" error budget on:
- Releases (some percentage of deploys cause errors).
- Experiments (chaos engineering, load testing in production).
- Technical debt (known unreliable components).
- Planned maintenance (upgrades, migrations).

### 3.2 Error Budget Policy

The policy defines what happens when the budget is consumed:

```
┌──────────────────────────────────────────────┐
│ Error Budget Policy                          │
│                                               │
│ Budget remaining > 50%:                       │
│   → Ship features at normal velocity          │
│   → Experiments allowed                       │
│   → On-call operates normally                 │
│                                               │
│ Budget remaining 20-50%:                      │
│   → Increase canary durations                 │
│   → Prioritize reliability work               │
│   → Review recent changes for contributors    │
│                                               │
│ Budget remaining < 20%:                       │
│   → Feature freeze for the service            │
│   → All engineering focuses on reliability     │
│   → No experiments                             │
│   → Rollback risky recent changes              │
│                                               │
│ Budget exhausted (0%):                        │
│   → Complete development freeze               │
│   → Incident-level response to restore budget │
│   → Escalation to leadership                  │
└──────────────────────────────────────────────┘
```

### 3.3 Error Budget as Alignment Tool

Error budgets resolve the fundamental tension between development velocity and operational stability:

- **Product team wants to ship fast:** Fine, as long as you have error budget. The budget quantifies how much risk you can take.
- **SRE team wants stability:** Fine, but you cannot demand zero risk. The SLO is not 100%. Unused error budget means you could be shipping faster.
- **If error budget is exhausted:** This is not a judgment — it is a fact. The data says the service is below the target. Feature freeze is automatic, not punitive.

This removes emotion from the velocity vs stability debate. The budget is the referee.

---

## 4. Burn-Rate Alerts

### 4.1 Why Not Simple Threshold Alerts?

Alert on "error rate > 1% for 5 minutes" produces:
- **False positives:** A brief spike triggers the page. By the time the engineer looks, it is over.
- **Alert fatigue:** Engineers start ignoring pages.
- **Missed slow burns:** A steady 0.5% error rate that exhausts the monthly budget in 6 days never triggers the 1% threshold.

### 4.2 Burn Rate Concept

Burn rate = how fast you are consuming your error budget relative to the window.

$$\text{Burn Rate} = \frac{\text{observed error rate}}{1 - \text{SLO}}$$

| Burn rate | Budget exhaustion time (30-day window) | Severity |
|:----------|:--------------------------------------|:---------|
| 1× | 30 days (exactly on budget) | Normal |
| 2× | 15 days | Warning |
| 6× | 5 days | Ticket |
| 14.4× | 2 days (50 hours) | Page |
| 36× | 20 hours | Emergency |
| 720× | 1 hour | Critical |

### 4.3 Multi-Window, Multi-Burn-Rate Alerts (Google SRE Workbook)

Two windows per severity: a long window to confirm the trend and a short window to confirm it is still happening:

| Severity | Long window | Short window | Burn rate | Budget consumed |
|:---------|:-----------|:------------|:----------|:---------------|
| **Page (critical)** | 1h | 5m | 14.4× | 2% in 1 hour |
| **Page (high)** | 6h | 30m | 6× | 5% in 6 hours |
| **Ticket** | 3d | 6h | 1× | 10% in 3 days |

**Why two windows?** The long window detects the trend. The short window confirms it is still happening (avoids alerting on a resolved issue).

**Prometheus example:**
```yaml
# 99.9% SLO, 30-day window, 14.4x burn rate over 1h
- alert: HighBurnRate_Page
  expr: |
    (
      sum(rate(http_requests_total{code=~"5.."}[1h]))
      /
      sum(rate(http_requests_total[1h]))
    ) > (14.4 * 0.001)
    and
    (
      sum(rate(http_requests_total{code=~"5.."}[5m]))
      /
      sum(rate(http_requests_total[5m]))
    ) > (14.4 * 0.001)
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Burning error budget at 14.4x rate"
    description: "Error rate is {{ $value | humanizePercentage }}. Budget will exhaust in ~2 days."
```

### 4.4 Sloth — SLO-to-Alert Generator

Sloth takes SLO definitions and generates Prometheus recording rules + alerting rules:

```yaml
# sloth.yaml
version: "prometheus/v1"
service: "my-api"
labels:
  team: platform
slos:
  - name: "requests-availability"
    objective: 99.9
    sli:
      events:
        error_query: sum(rate(http_requests_total{code=~"5.."}[{{.window}}]))
        total_query: sum(rate(http_requests_total[{{.window}}]))
    alerting:
      name: MyAPIAvailability
      page_alert:
        labels:
          severity: critical
      ticket_alert:
        labels:
          severity: warning
```

```bash
sloth generate -i sloth.yaml -o prometheus-rules.yaml
```

---

## 5. Toil

### 5.1 Definition

Toil is work that:
1. **Is manual** — a human must perform it.
2. **Is repetitive** — done over and over.
3. **Is automatable** — could be done by a machine.
4. **Is tactical** — interrupt-driven, not strategic.
5. **Has no enduring value** — does not improve the system long-term.
6. **Scales linearly with service growth** — more traffic = more toil.

**Examples of toil:**
- Manually provisioning user accounts.
- Running database migrations by hand.
- Restarting services that crash due to known bugs.
- Manually scaling capacity for expected traffic.
- Manually responding to alerts that have a known runbook.
- Copy-pasting configuration between environments.

### 5.2 The 50% Rule

Google's SRE practice mandates that SREs spend **at most 50%** of their time on toil. The remaining 50% goes to engineering work that reduces future toil.

If toil exceeds 50%, the team must either:
1. Automate the most time-consuming toil.
2. Escalate to service teams to fix the root causes.
3. Refuse new operational responsibilities until the balance is restored.

### 5.3 Measuring Toil

Track time spent on toil categories:

| Category | Examples | Target |
|:---------|:---------|:-------|
| **Interrupt-driven** | Pages, tickets, manual requests | < 25% of time |
| **Repetitive ops** | Deploys, config changes, cert rotation | < 15% of time |
| **Manual scaling** | Capacity adjustments, resource allocation | < 5% of time |
| **Incident cleanup** | Postmortem actions, manual fixes | < 5% of time |

**Tools:** Time tracking (Jira labels, Toggl), on-call ticket classification, periodic toil surveys.

### 5.4 Toil Reduction Strategies

```
1. AUTOMATE
   - Write runbook → convert to script → convert to cron/controller
   - Self-healing: if the fix is "restart pod", let the liveness probe do it
   - Auto-remediation: PagerDuty → Lambda → fix → close alert

2. ELIMINATE
   - Fix the root cause so the toil scenario never happens
   - If a deploy always requires manual steps, fix the deploy pipeline
   - If a service always needs manual scaling, implement autoscaling

3. REDUCE FREQUENCY
   - Batch manual tasks (weekly instead of daily)
   - Consolidate alerts (group related alerts into one)
   - Increase thresholds (alert only when it matters)

4. TRANSFER
   - Self-service: let service teams manage their own ops
   - Internal developer platform: golden paths that eliminate manual steps
   - Shift-left: let CI/CD handle what on-call used to do
```

---

## 6. Incident Management

### 6.1 Incident Severity Levels

| Severity | Impact | Response time | Responders |
|:---------|:-------|:-------------|:-----------|
| **SEV1 / P1** | Complete service outage, data loss risk, security breach | Immediate (< 5 min) | Incident commander + full team + leadership |
| **SEV2 / P2** | Major degradation, significant user impact | < 15 min | On-call + relevant engineers |
| **SEV3 / P3** | Minor degradation, limited user impact | < 1 hour | On-call handles during business hours |
| **SEV4 / P4** | Cosmetic, no user impact | Next business day | Ticket, no page |

### 6.2 Incident Command System (ICS)

Adapted from emergency response. Roles during a major incident:

**Incident Commander (IC):**
- Single point of authority.
- Makes decisions on priorities and resource allocation.
- Communicates status to leadership and stakeholders.
- Does NOT debug — coordinates others who do.

**Communications Lead:**
- Posts status updates to status page, Slack, email.
- Manages stakeholder communication.
- Keeps the IC focused on resolution, not communication.

**Operations Lead:**
- Directs the technical response.
- Coordinates multiple engineers working on different aspects.
- Manages the war room / incident channel.

**Subject Matter Experts (SMEs):**
- Database engineer, network engineer, application developer.
- Called in by the IC as needed.

**Scribe:**
- Documents the timeline: what was done, when, by whom, what happened.
- This log becomes the postmortem input.

### 6.3 Incident Lifecycle

```
DETECT     → Alert fires, customer report, monitoring catches it
    │
TRIAGE     → Assess severity, assign IC, open incident channel
    │
MITIGATE   → Restore service ASAP (rollback, failover, scale up, redirect)
    │          Mitigation > root cause at this stage. Stop the bleeding.
    │
RESOLVE    → Verify service is fully restored, all indicators green
    │
POSTMORTEM → Blameless analysis, write postmortem doc, assign action items
    │
FOLLOW-UP  → Complete action items, verify fixes, close the incident
```

### 6.4 Mitigation Patterns

| Pattern | When to use | Risk |
|:--------|:-----------|:-----|
| **Rollback** | Bad deploy caused the issue | Safest if deploy is reversible |
| **Feature flag disable** | New feature is causing problems | Instant, no deploy needed |
| **Scale up** | Capacity exhaustion | Cost, may not help if the problem is not capacity |
| **Failover** | Regional or AZ failure | Requires pre-built redundancy |
| **Traffic shedding** | Overload, cascading failure | Deliberate partial outage to save the whole |
| **Circuit breaker** | Downstream dependency failing | Prevents cascade, degrades gracefully |
| **Drain and restart** | Memory leak, stuck process | Temporary fix, leak will recur |

**Rule:** Mitigation first, root cause later. Do not spend 2 hours debugging while the service is down if a rollback would restore it in 2 minutes.

### 6.5 Incident Communication Template

```
INCIDENT NOTIFICATION — SEV2
Service: Payments API
Impact: ~15% of payment requests failing with 500 errors
Start time: 2026-05-22 14:32 UTC
Current status: INVESTIGATING
IC: Jane Smith
Next update: 15:00 UTC

UPDATE 1 (14:45 UTC):
Root cause identified: database connection pool exhaustion.
Mitigation in progress: scaling connection pool and restarting pods.

UPDATE 2 (14:58 UTC):
Mitigation applied. Error rate dropping. Monitoring for 15 minutes
before declaring resolved.

RESOLVED (15:15 UTC):
Service restored to normal. Error rate back to baseline.
Postmortem scheduled for 2026-05-23 10:00 UTC.
```

---

## 7. On-Call Practices

### 7.1 On-Call Design Principles

1. **On-call should be sustainable.** No one should be on-call more than 25% of the time (1 week in 4).
2. **On-call should be compensated.** Time, money, or comp days. Burnout is real.
3. **Pages must be actionable.** If the on-call engineer cannot do anything about it, do not page them.
4. **Runbooks for every alert.** Every alert should link to a runbook with steps to diagnose and mitigate.
5. **Primary + secondary rotation.** Primary is paged first. Secondary is backup.

### 7.2 On-Call Rotation Patterns

| Pattern | Structure | Pros | Cons |
|:--------|:---------|:-----|:-----|
| **Weekly rotation** | One person per week | Simple | One person bears all week's incidents |
| **Follow-the-sun** | Teams in different time zones hand off | No overnight pages | Requires multi-timezone team |
| **Business hours + overnight** | Day shift = primary, night shift = pager-only | Better life quality | More complex scheduling |
| **Buddy system** | Two people share each shift | Reduced single-point-of-failure | Coordination overhead |

### 7.3 On-Call Metrics

Track and review monthly:

| Metric | Target | Red flag |
|:-------|:-------|:---------|
| Pages per shift | < 2 per 12h shift | > 5 = alert fatigue |
| Time to acknowledge | < 5 minutes | > 15 minutes = process problem |
| Time to mitigate | < 30 minutes for SEV2+ | > 2 hours = tooling/runbook problem |
| False positive rate | < 20% of pages | > 50% = alert quality problem |
| After-hours pages | < 1 per week | > 3 = system reliability problem |

### 7.4 On-Call Handoff

```
End of shift:
1. Document any ongoing issues and their status
2. Review upcoming maintenance windows
3. Brief the incoming on-call on any context
4. Transfer the pager (PagerDuty schedule switch)
5. Share any relevant Slack threads or tickets

Start of shift:
1. Review handoff notes
2. Check dashboards for current system health
3. Verify alerting is working (test page if needed)
4. Review any open incidents or ongoing issues
```

### 7.5 Reducing On-Call Burden

1. **Fix the root cause.** If you keep getting paged for the same thing, fix it.
2. **Automate runbook steps.** If the runbook says "restart service X", automate it.
3. **Tune alert thresholds.** If 80% of pages are false positives, the thresholds are wrong.
4. **Group correlated alerts.** One root cause should produce one page, not five.
5. **Invest in self-healing.** Kubernetes restarts, auto-scaling, circuit breakers.
6. **Review on-call load quarterly.** Trend the metrics. Are things getting better or worse?

---

## 8. Postmortem Culture

### 8.1 Blameless Postmortems

**Blameless does not mean accountability-free.** It means:
- We focus on systemic factors, not individual blame.
- "Who" is less important than "what" and "why."
- The goal is to learn and prevent recurrence, not to punish.
- People are honest about what happened because they are not afraid of consequences.

**What blameless is not:**
- Ignoring human error (document it — it reveals process gaps).
- Avoiding difficult conversations (discuss what went wrong directly).
- Accepting repeat incidents without action (patterns of recurrence indicate systemic failure).

### 8.2 Postmortem Template

```markdown
# Postmortem: [Title]

## Metadata
- **Date of incident:** 2026-05-22
- **Duration:** 43 minutes (14:32 - 15:15 UTC)
- **Severity:** SEV2
- **Impact:** ~15% of payment requests failed. ~2,300 affected transactions.
- **Incident Commander:** Jane Smith
- **Postmortem author:** John Doe
- **Postmortem review date:** 2026-05-23

## Summary
One-paragraph summary of what happened, what the impact was, and how it was resolved.

## Timeline (UTC)
| Time | Event |
|------|-------|
| 14:30 | Deploy v2.4.1 rolled out to production |
| 14:32 | Error rate exceeded SLO burn-rate threshold. Page fired. |
| 14:35 | IC acknowledged. War room opened. |
| 14:38 | Identified: DB connection pool exhaustion. New code path opens 3x connections. |
| 14:42 | Decision: rollback to v2.4.0. |
| 14:45 | Rollback initiated. |
| 14:50 | Rollback complete. Error rate decreasing. |
| 15:15 | Error rate at baseline. Incident declared resolved. |

## Root Cause
The v2.4.1 release introduced a new query pattern that opened 3 database
connections per request instead of 1. Under production load, this exhausted
the connection pool (max 100) within 2 minutes, causing subsequent requests
to timeout waiting for a connection.

## Contributing Factors
- Load testing in staging used 10% of production traffic volume — insufficient
  to surface the connection pool issue.
- No monitoring alert on connection pool utilization.
- Code review did not catch the triple-connection pattern.

## What Went Well
- Burn-rate alert fired within 2 minutes.
- Rollback was fast (5 minutes).
- IC identified root cause within 6 minutes.

## What Went Wrong
- Load testing gap.
- No connection pool metrics in dashboards.
- Deploy happened at peak traffic time.

## Action Items
| # | Action | Owner | Due | Priority |
|---|--------|-------|-----|----------|
| 1 | Add connection pool utilization to monitoring dashboard | Jane | 2026-05-24 | P1 |
| 2 | Set alert on pool utilization > 80% | Jane | 2026-05-24 | P1 |
| 3 | Scale load tests to 50% of production traffic | John | 2026-05-31 | P2 |
| 4 | Add deploy freeze window during peak hours | Team | 2026-06-01 | P2 |
| 5 | Add code review checklist item for DB connection patterns | Team | 2026-06-01 | P3 |

## Lessons Learned
1. Connection pool exhaustion is a systemic risk. Monitor it everywhere.
2. Load testing must be representative. 10% is not enough for connection-sensitive code.
3. Deploy timing matters. Avoid peak hours for risky changes.
```

### 8.3 Postmortem Review

- Conduct within 24-72 hours of incident resolution.
- All involved parties attend.
- Review the timeline and root cause collaboratively.
- Assign action items with owners and deadlines.
- Publish to the entire engineering organization.
- Track action item completion. A postmortem without follow-through is theater.

### 8.4 Learning from Postmortems

**Patterns to look for across multiple postmortems:**
- Same root cause recurring (fix did not stick, or fix was incomplete).
- Same contributing factors (load testing gaps, missing monitoring, deploy timing).
- Same service appearing repeatedly (systemic reliability problem).
- Action items consistently not completed (organizational prioritization issue).

**Quarterly postmortem review:** Analyze all incidents from the quarter. Look for trends, systemic issues, and patterns that individual postmortem reviews miss.

---

## 9. Chaos Engineering

### 9.1 Principles (principlesofchaos.org)

1. **Build a hypothesis around steady-state behavior.** Define what "normal" looks like (error rate, latency, throughput).
2. **Vary real-world events.** Inject failures that actually happen: server crash, network partition, disk full, dependency timeout.
3. **Run experiments in production.** Staging is insufficient — it does not have real traffic, real data, or real concurrency.
4. **Automate experiments to run continuously.** One-off game days are good. Continuous experiments are better.
5. **Minimize blast radius.** Start small, contain the experiment, have a kill switch.

### 9.2 Failure Injection Categories

| Category | Examples | Tools |
|:---------|:---------|:------|
| **Infrastructure** | Kill a node, lose an AZ, disk failure | Chaos Mesh, LitmusChaos, AWS FIS |
| **Network** | Latency injection, packet loss, partition | tc (traffic control), Chaos Mesh, Toxiproxy |
| **Application** | Exception injection, memory leak, CPU stress | Gremlin, ChaosBlade, libchaos |
| **Dependency** | Kill downstream service, slow responses, corrupt data | WireMock chaos, Toxiproxy, Chaos Mesh |
| **State** | Corrupt cache, delete queue messages, stale DNS | Custom scripts |

### 9.3 Chaos Mesh (Kubernetes-Native)

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: kill-payment-pod
spec:
  action: pod-kill
  mode: one            # kill one random pod matching selector
  selector:
    namespaces:
    - production
    labelSelectors:
      app: payment-service
  scheduler:
    cron: "0 10 * * 1-5"    # every weekday at 10:00

---
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: payment-latency
spec:
  action: delay
  mode: all
  selector:
    namespaces:
    - production
    labelSelectors:
      app: payment-service
  delay:
    latency: "200ms"
    jitter: "50ms"
    correlation: "25"
  duration: "5m"
```

### 9.4 LitmusChaos

CNCF project for Kubernetes chaos engineering:

```yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: payment-chaos
spec:
  appinfo:
    appns: production
    applabel: app=payment-service
  chaosServiceAccount: litmus-admin
  experiments:
  - name: pod-delete
    spec:
      components:
        env:
        - name: TOTAL_CHAOS_DURATION
          value: "30"
        - name: CHAOS_INTERVAL
          value: "10"
        - name: FORCE
          value: "false"
```

**ChaosHub:** Library of pre-built experiments that you can plug in.

### 9.5 Game Days

Structured chaos engineering exercises:

```
GAME DAY PLAN

Objective: Verify payment service survives loss of primary database replica.

Date: 2026-05-22 (Wednesday, 10:00-12:00 UTC, off-peak)

Participants:
- IC: Jane Smith
- Database team: John Doe
- Payment team: Alice Johnson
- SRE on-call: Bob Williams

Hypothesis:
  When the primary Postgres replica is killed, the payment service will:
  1. Failover to standby within 30 seconds.
  2. Maintain < 1% error rate during failover.
  3. Resume normal operation within 2 minutes.

Experiment:
  1. Baseline: record current metrics (error rate, latency, throughput).
  2. Inject: kill the primary Postgres pod.
  3. Observe: monitor failover time, error rate, client impact.
  4. Verify: all metrics return to baseline.

Abort criteria:
  - Error rate > 5% for > 2 minutes.
  - Any data loss detected.
  - IC decides to abort at any time.

Rollback plan:
  - Restart killed pod.
  - Manual failover if automatic failover fails.
```

### 9.6 Measuring Chaos Engineering Maturity

| Level | Description |
|:------|:-----------|
| **0 — Ad hoc** | No chaos engineering. Failures are surprises. |
| **1 — Game days** | Occasional manual experiments. Specific scenarios. |
| **2 — Automated experiments** | Scheduled experiments in production. Automated analysis. |
| **3 — Continuous chaos** | Always running. Part of CI/CD. Integrated with SLO monitoring. |
| **4 — Chaos as culture** | Every team runs experiments. Chaos results drive architecture decisions. |

---

## 10. Capacity Planning

### 10.1 Demand Forecasting

| Method | Approach | Accuracy |
|:-------|:---------|:---------|
| **Historical trending** | Extrapolate from past usage patterns | Moderate (misses non-linear growth) |
| **Business-driven** | Product team forecasts user growth, feature launches | Higher (accounts for planned changes) |
| **Load testing** | Determine system limits empirically | Highest (measured, not estimated) |
| **Simulation** | Model system behavior under various scenarios | High (but requires accurate models) |

### 10.2 Capacity Planning Process

```
1. MEASURE current state
   - Resource utilization (CPU, memory, disk, network)
   - Traffic patterns (RPS, bandwidth, concurrent users)
   - Performance headroom (how far from limits?)

2. FORECAST future demand
   - Growth rate (users, data, traffic)
   - Upcoming launches (new features, markets, campaigns)
   - Seasonal patterns (Black Friday, end of month, tax season)

3. MODEL capacity needs
   - current_resources × (1 + growth_rate)^months + safety_margin
   - Account for redundancy (N+1, N+2)
   - Account for burst capacity (2-3× normal peak)

4. PLAN procurement
   - Lead time for new capacity (cloud: minutes; on-prem: months)
   - Cost optimization (reserved instances, spot, right-sizing)
   - Timeline alignment (capacity ready before demand arrives)

5. VALIDATE
   - Load test new capacity
   - Verify autoscaling limits
   - Confirm burst handling
```

### 10.3 Headroom Targets

| Resource | Target utilization | Rationale |
|:---------|:------------------|:----------|
| CPU | 50-70% average, 80% peak | Leave room for spikes, GC pauses, burst processing |
| Memory | 60-75% | OOM risk at high utilization, swap thrashing |
| Disk | < 70% | Performance degrades near capacity, need room for logs and temp files |
| Network | < 60% of bandwidth | TCP throughput collapses under congestion |
| Connection pools | < 80% | Queuing delays grow non-linearly near capacity |

### 10.4 Load Shedding and Backpressure

When capacity is exhausted, you must choose which requests to drop:

**Load shedding strategies:**
- **Random drop:** Simple but indiscriminate.
- **Priority-based:** Drop low-priority requests first (batch over interactive).
- **Client-based:** Rate limit per client to prevent single-client starvation.
- **Admission control:** Check capacity before processing. Reject with 503 early.

**Backpressure signals:**
- HTTP 429 (Too Many Requests) with `Retry-After` header.
- HTTP 503 (Service Unavailable).
- gRPC `RESOURCE_EXHAUSTED` (14).
- Queue depth metrics for async systems.

---

## 11. Release Engineering

### 11.1 Progressive Delivery

```
1. DEPLOY to canary (1% traffic)
   → Monitor SLIs for 10 minutes
   → Automated analysis: error rate, latency, saturation
   
2. EXPAND to 10% traffic
   → Monitor for 30 minutes
   → Compare against control group
   
3. EXPAND to 50% traffic
   → Monitor for 1 hour
   → Full metric comparison
   
4. PROMOTE to 100%
   → Monitor for 24 hours
   → Close the release
```

### 11.2 Feature Flags

Decouple deployment from release:

```
Deploy code containing new feature (flag OFF)
    │
    ▼ (safe — feature is dormant)
Enable flag for internal users (dogfooding)
    │
    ▼
Enable flag for 1% of users (canary)
    │
    ▼
Enable flag for 100% of users (GA)
    │
    ▼
Remove flag and dead code (cleanup)
```

**Feature flag tools:** LaunchDarkly, Unleash, Flipt, Flagsmith, AWS AppConfig.

**Feature flag hygiene:**
- Flags have owners and expiration dates.
- Stale flags (> 30 days after GA) are tracked and removed.
- Flag state is part of the incident timeline (was a flag changed recently?).
- Flags are tested in both states (on and off).

### 11.3 Rollback Strategy

| Strategy | Speed | Risk | Use case |
|:---------|:------|:-----|:---------|
| **Feature flag toggle** | Seconds | Lowest | Feature-specific issues |
| **Deployment rollback** | Minutes | Low | Broad regression |
| **Database rollback** | Minutes-hours | Medium | Schema migration issues |
| **Full environment rollback** | Hours | High | Multi-service coordinated failure |

**Rule:** Every deploy must be rollback-safe. This means:
- Database migrations are backward compatible (expand-and-contract pattern).
- APIs are versioned (old clients still work).
- Feature flags guard new behavior.
- Configuration changes are reversible.

---

## 12. Monitoring and Alerting Philosophy

### 12.1 What to Monitor

Follow the Golden Signals (Google SRE):
1. **Latency:** Time to serve a request. Track success and error latency separately.
2. **Traffic:** Demand on the system. RPS, QPS, concurrent connections.
3. **Errors:** Rate of failed requests. Include explicit (5xx) and implicit (wrong data, timeout).
4. **Saturation:** How full is the system? CPU, memory, disk, connection pool.

### 12.2 Alerting Principles

1. **Every alert must be actionable.** If the on-call engineer cannot do anything, do not page them.
2. **Every alert must link to a runbook.** Runbook = symptoms, possible causes, diagnostic steps, mitigation steps.
3. **Prefer SLO-based alerts over threshold alerts.** Burn-rate alerts over static thresholds.
4. **Symptoms over causes.** Alert on "users cannot check out" not "CPU is at 80%."
5. **Minimal routing.** Alert only the team that can fix the problem.
6. **Suppress during maintenance.** Scheduled maintenance should not trigger pages.

### 12.3 Alert Fatigue

**Symptoms:**
- Engineers ignore pages (boy who cried wolf).
- Acknowledgment without investigation.
- Pages during off-hours that resolve before the engineer can act.
- High false-positive rate.

**Remedies:**
- Measure noise: track alert-to-incident ratio. Target > 50% of pages lead to action.
- Periodically review all alerts. Delete or tune those with low signal.
- Group correlated alerts (one root cause = one page).
- Use tiered alerting: critical → page, warning → Slack, info → dashboard.

### 12.4 Runbook Template

```markdown
# Runbook: [Alert Name]

## Alert Description
What this alert means and why it fires.

## Impact
What users experience when this alert is firing.

## Diagnostic Steps
1. Check dashboard: [link]
2. Query: `sum(rate(http_requests_total{code=~"5.."}[5m])) by (service)`
3. Check recent deploys: `kubectl rollout history deployment/<name>`
4. Check dependencies: [dependency status page link]

## Mitigation Steps
1. If caused by recent deploy → rollback: `kubectl rollout undo deployment/<name>`
2. If capacity exhaustion → scale up: `kubectl scale deployment/<name> --replicas=<n>`
3. If dependency failure → enable circuit breaker: [link to feature flag]

## Escalation
If unable to resolve within 30 minutes:
- Page: [team name] via PagerDuty
- Slack: #incident-response

## Related Alerts
- [Other alert that commonly fires with this one]

## History
- 2026-04-15: False positive due to metric lag. Tuned threshold.
- 2026-03-22: Genuine incident. Root cause: DB connection pool. Postmortem: [link]
```

---

## 13. Operational Reviews

### 13.1 Service Review (Monthly)

Structured review of each service's reliability:

```
SERVICE REVIEW — Payment Service — May 2026

SLO Performance:
  Availability: 99.94% (target: 99.9%) ✅
  Latency (p99): 180ms (target: 200ms) ✅
  Error budget remaining: 62% ✅

Incident Summary:
  SEV1: 0
  SEV2: 1 (postmortem completed, all actions done)
  SEV3: 3

On-Call Health:
  Pages per shift: 1.2 (target: < 2) ✅
  False positive rate: 18% (target: < 20%) ✅
  After-hours pages: 2 (target: < 3) ✅

Toil:
  Current toil percentage: 35% (target: < 50%) ✅
  Toil reduction projects: connection pool automation (shipped)

Capacity:
  CPU headroom: 45% ✅
  Memory headroom: 38% ✅
  Growth rate: 12% month-over-month
  Action: provision additional capacity by June 15

Action Items:
  - Complete load testing at 150% current peak
  - Deploy auto-remediation for top 3 pages
```

### 13.2 Production Readiness Review (PRR)

Checklist before a new service enters production:

```
PRODUCTION READINESS REVIEW

Service: New Notification Service

□ SLOs defined and instrumented
□ Dashboards for golden signals
□ Burn-rate alerts configured
□ Runbooks for each alert
□ On-call rotation assigned
□ Logging: structured, correlated with traces
□ Tracing: OpenTelemetry instrumented
□ Graceful shutdown implemented
□ Health checks (liveness, readiness, startup)
□ Resource requests and limits set
□ PodDisruptionBudget defined
□ Network policies in place
□ Secrets managed externally (not in Git)
□ Backup and restore tested for stateful components
□ Load test completed (2× expected peak)
□ Chaos experiment run (pod kill, dependency failure)
□ Rollback procedure documented and tested
□ Dependency SLOs documented
□ Capacity forecast for 6 months
□ Documentation: architecture diagram, data flow, dependencies
```

---

## 14. SRE Team Models

### 14.1 Organizational Models

| Model | Description | When to use |
|:------|:-----------|:-----------|
| **Embedded** | SRE assigned to a product team | Large, complex services with high reliability requirements |
| **Centralized** | Shared SRE team serving multiple product teams | Smaller organizations, shared infrastructure |
| **Consulting** | SRE team reviews and advises, does not operate | Early SRE adoption, building capability |
| **Platform** | SRE team builds self-service reliability tooling | Mature organizations, many teams |

### 14.2 SRE Engagement Model

```
Team requests SRE support
    │
    ▼
PRR (Production Readiness Review)
    │ ← SRE evaluates readiness
    ▼
SRE engagement begins
    │
    ▼ ← SRE takes on-call responsibility
Service meets SLO consistently
    │
    ▼
SRE transfers on-call back to dev team
    │ ← Dev team has learned SRE practices
    ▼
SRE moves to next service
```

**Conditions for SRE disengagement:**
- Service consistently meets SLOs for 3+ months.
- Dev team can handle on-call independently.
- Toil is under 50%.
- Postmortem process is operational.
- Monitoring and alerting are mature.

---

## 15. Key Takeaways

1. **SLOs are the foundation.** Without them, reliability discussions are opinions. With them, they are data-driven decisions.

2. **Error budgets create alignment.** They quantify the trade-off between velocity and reliability. When the budget is empty, the data makes the decision.

3. **Burn-rate alerts eliminate noise.** Multi-window, multi-burn-rate alerting reduces false positives and catches slow burns that threshold alerts miss.

4. **Toil is a reliability tax.** If SREs spend all their time on toil, there is no time for engineering that prevents future toil. The 50% rule is a discipline, not a suggestion.

5. **Blameless postmortems are non-negotiable.** If people hide mistakes, you cannot learn from them. If you cannot learn, you will repeat them.

6. **Incident management is a skill.** Like firefighting, it requires training, roles, procedures, and practice. Game days are the fire drills.

7. **Chaos engineering validates assumptions.** "The circuit breaker will catch it" is a hypothesis. Run the experiment and find out.

8. **Capacity planning is reliability work.** Running out of capacity is an outage. Forecast, provision, validate.

9. **Progressive delivery reduces blast radius.** Canary → expand → promote. Feature flags decouple deployment from release.

10. **SRE is a practice, not a title.** The value is in the principles (SLOs, error budgets, toil reduction, blameless culture) — not in renaming the ops team.

---

## 16. Further Reading

- **"Site Reliability Engineering" (Google SRE Book)** — Beyer, Jones, Petoff, Murphy. The foundational text. Free online: sre.google/sre-book/
- **"The Site Reliability Workbook"** — Practical companion with templates and examples. Free online: sre.google/workbook/
- **"Implementing Service Level Objectives" by Alex Hidalgo** (O'Reilly) — Deep dive into SLO design and implementation.
- **"Incident Management for Operations" by Rob Schnepp et al.** (O'Reilly) — ICS adapted for technology.
- **"Chaos Engineering" by Casey Rosenthal and Nora Jones** (O'Reilly) — Principles and practices of chaos engineering.
- **"Learning Chaos Engineering" by Russ Miles** (O'Reilly) — Practical introduction with tools and experiments.
- **Principles of Chaos Engineering:** principlesofchaos.org
- **Google SRE resources:** sre.google — Articles, case studies, talks.
- **Sloth:** sloth.dev — Generate Prometheus SLO rules.
- **OpenSLO:** openslo.com — Vendor-neutral SLO specification.

---

## 17. Reliability Patterns and Anti-Patterns

### 17.1 Retry with Exponential Backoff and Jitter

Retries amplify failure if done naively. Every client retrying immediately after a failure creates a thundering herd:

```
Attempt  Delay (no jitter)   Delay (with jitter)
1        1s                  0.7s - 1.3s
2        2s                  1.4s - 2.6s
3        4s                  2.8s - 5.2s
4        8s                  5.6s - 10.4s
5        16s                 11.2s - 20.8s
(cap)    30s max             21s - 39s
```

**Formula:** `delay = min(cap, base * 2^attempt) + random_jitter`

**Jitter types:**
- **Full jitter:** `random(0, delay)` — highest variance, best thundering-herd prevention.
- **Equal jitter:** `delay/2 + random(0, delay/2)` — balanced.
- **Decorrelated jitter:** `random(base, prev_delay * 3)` — good for burst workloads.

**Rules for retries:**
1. Only retry on transient failures (5xx, timeout, connection reset). Never retry 4xx (client error).
2. Set a retry budget per request chain — do not retry at every layer.
3. Use a circuit breaker to stop retrying when the downstream is clearly dead.
4. Track retry rate as a metric. High retry rate = underlying problem.

### 17.2 Circuit Breaker Pattern

```
           CLOSED                    OPEN                    HALF-OPEN
        (normal flow)           (all requests fail fast)    (probe downstream)
              │                         │                         │
  Failure     │  failures >             │  timeout                │
  count       │  threshold              │  expires                │
  increments  ├─────────────────────────►├─────────────────────────►│
              │                         │                         │
              │                         │  probe                  │
              │                         │  succeeds               │
              │◄────────────────────────┤◄────────────────────────┤
              │                         │                         │
              │                         │  probe fails            │
              │                         │◄────────────────────────┤
```

**States:**
- **Closed:** Requests flow normally. Failures are counted.
- **Open:** After failure threshold exceeded, all requests fail immediately with a cached error (or fallback response). No load on the downstream.
- **Half-open:** After a timeout, a probe request is sent. If successful, circuit closes. If not, circuit opens again.

**Implementation:** Resilience4j (Java), Polly (.NET), Hystrix (Java, legacy), gobreaker (Go), opossum (Node.js).

### 17.3 Bulkhead Pattern

Isolate critical paths so that a failure in one does not cascade to others:

```
┌──────────────────────────────────────┐
│ Application                          │
│                                       │
│ ┌──────────────┐ ┌──────────────┐    │
│ │ Bulkhead A   │ │ Bulkhead B   │    │
│ │ (Payments)   │ │ (Analytics)  │    │
│ │ 20 threads   │ │ 5 threads    │    │
│ │ 50 queue     │ │ 10 queue     │    │
│ └──────┬───────┘ └──────┬───────┘    │
│        │                │            │
│ ┌──────▼───────┐ ┌──────▼───────┐    │
│ │ Payment API  │ │ Analytics API│    │
│ └──────────────┘ └──────────────┘    │
└──────────────────────────────────────┘
```

If the Analytics API is slow and exhausts its thread pool, the Payment path is unaffected — it has its own isolated pool.

### 17.4 Timeout Budgets

In a microservice chain, the total timeout budget is distributed across the chain:

```
Client timeout: 5s
├── API Gateway: 4.5s
│   ├── Service A: 3s
│   │   ├── Database: 1s
│   │   └── Cache: 200ms
│   └── Service B: 2s
│       └── External API: 1.5s
```

**Rules:**
- Total timeout must be less than the caller's timeout.
- Leave margin for network latency and processing.
- A downstream timeout should trigger a fallback, not a cascade.

### 17.5 Rate Limiting

| Algorithm | Behavior | Best for |
|:----------|:---------|:---------|
| **Token bucket** | Steady rate with burst allowance | General-purpose API rate limiting |
| **Leaky bucket** | Strict steady rate, no bursts | Traffic shaping, queue processing |
| **Fixed window** | Count resets at window boundary | Simple, but burst at window edges |
| **Sliding window** | Smooth count over rolling window | Accurate, slightly more complex |

**Rate limit at multiple levels:**
1. **Edge:** WAF / API Gateway — protect infrastructure.
2. **Service:** Per-endpoint, per-tenant — protect individual services.
3. **Client:** Client-side throttling — respect server limits.

### 17.6 Anti-Patterns

| Anti-pattern | Description | Fix |
|:-------------|:-----------|:----|
| **Retry storm** | Every layer retries independently | Retry budget at outermost layer only |
| **Cascading failure** | One service failure propagates to all callers | Circuit breakers, bulkheads, load shedding |
| **Thundering herd** | All clients retry simultaneously after recovery | Exponential backoff with jitter |
| **Metastable failure** | System oscillates between healthy and unhealthy | Load shedding, admission control, gradual recovery |
| **Death spiral** | Failure causes work that causes more failure | Rate limiting, circuit breakers, graceful degradation |
| **Configuration drift** | Environments diverge over time | GitOps, IaC, immutable infrastructure |
| **Alert fatigue** | Too many alerts, most not actionable | SLO-based alerting, alert review, tuning |
| **MTTR focus without MTBF** | Fast recovery but constant failures | Fix root causes, not just symptoms |

---

## 18. Distributed Systems Reliability

### 18.1 CAP Theorem Practical Implications

In a distributed system, during a network partition (P), you must choose between consistency (C) and availability (A):

| System | Choice | Behavior during partition |
|:-------|:-------|:------------------------|
| **PostgreSQL (single)** | CP | Unavailable if leader fails |
| **Cassandra** | AP | Available but may return stale data |
| **CockroachDB** | CP | Unavailable for affected ranges |
| **DynamoDB** | AP (eventual) or CP (strong reads) | Configurable per request |
| **etcd** | CP | Unavailable if quorum lost |
| **Redis Cluster** | AP | Available, risk of lost writes |

**Practical guidance:** Most services need both. Use CP for state that must be correct (transactions, locks, leader election). Use AP for state that can tolerate staleness (caches, analytics, session data).

### 18.2 Consensus and Leader Election

**Raft** (etcd, CockroachDB, TiKV): Strong leader. Writes go through leader. Leader heartbeats followers. If heartbeat stops, followers start election.

**Paxos** (Google Chubby, classic): More general but harder to implement. Multiple proposers, acceptors, learners.

**SRE concern:** Leader election failures are a major outage vector. Monitor:
- Leader stability (leader changes per hour).
- Election duration.
- Quorum health (healthy member count).

### 18.3 Idempotency

Operations that can be safely retried without side effects:

| Operation | Naturally idempotent? | How to make idempotent |
|:----------|:---------------------|:----------------------|
| GET request | Yes | N/A |
| PUT (replace) | Yes | N/A (if truly replacing, not appending) |
| DELETE | Yes (deleting non-existent = no-op) | N/A |
| POST (create) | **No** | Use idempotency key (client-generated UUID) |
| Payment charge | **No** | Idempotency key in request + dedup on server |
| Message publish | **No** | Dedup key + exactly-once delivery |

**Idempotency key pattern:**
```
Client generates UUID: "ik_abc123"
Request: POST /payments {idempotency_key: "ik_abc123", amount: 100}

Server:
1. Check if "ik_abc123" exists in idempotency store
2. If yes → return cached response (no double-charge)
3. If no → process payment, store result keyed by "ik_abc123"
4. TTL on idempotency keys (24-72 hours)
```

### 18.4 Graceful Degradation

When a dependency fails, degrade gracefully instead of failing completely:

| Service | Full functionality | Degraded mode |
|:--------|:------------------|:-------------|
| **Search** | ML-ranked results | Fallback to simple text match |
| **Recommendations** | Personalized suggestions | Show popular/trending items |
| **User profiles** | Full profile data | Cached/stale profile data |
| **Payments** | Real-time processing | Queue for later processing |
| **Notifications** | Email + SMS + push | Email only (most reliable channel) |

### 18.5 Queue-Based Load Leveling

Absorb bursts by placing work in a queue:

```
Clients → API → Queue (SQS/Kafka/RabbitMQ) → Workers

Burst:  1000 RPS → Queue absorbs → Workers process at 100 RPS
Result: Latency increases (queuing delay) but zero failures
```

**Trade-off:** Increased latency for increased availability. Acceptable for async workloads (email sending, data processing, report generation). Unacceptable for synchronous user-facing requests.

---

## 19. Observability for SRE

### 19.1 Dashboard Design Principles

**The RED method for dashboards:**
1. **Rate** — requests per second.
2. **Errors** — error rate (absolute and percentage).
3. **Duration** — latency distribution (p50, p90, p99, p999).

**Dashboard hierarchy:**
```
Level 1: Executive (SLO compliance, error budget, business metrics)
Level 2: Service (golden signals per service, dependency health)
Level 3: Instance (per-pod CPU/memory/network, per-node metrics)
Level 4: Debug (application-specific: query time, cache hit rate, queue depth)
```

**Anti-patterns:**
- Dashboard with 50 panels nobody looks at.
- Dashboards that require tribal knowledge to interpret.
- Dashboards showing only "happy path" — no error or saturation panels.
- Dashboards without time annotations (deploy markers, incident markers).

### 19.2 Observability Correlation

The goal: from an SLO alert, reach the root cause in **< 3 clicks**:

```
1. SLO alert fires → Dashboard shows error budget burn
   (Click 1)

2. Dashboard → Error rate spike for specific endpoint
   (Click 2)

3. Endpoint → Exemplar trace link → Full distributed trace
   showing slow database query
   (Click 3)

4. Trace span → Correlated logs with SQL query text
   → Root cause identified
```

**Enabling this:**
- Metrics: exemplars linking to traces.
- Logs: `trace_id` and `span_id` fields.
- Dashboards: drill-down links between panels.
- Alerts: link to runbook AND relevant dashboard.

---

## 20. Reliability Cost-Benefit Analysis

### 20.1 The Cost of Nines

| Improvement | Engineering effort | Typical approaches |
|:------------|:------------------|:-------------------|
| 99% → 99.9% | Moderate | Monitoring, basic redundancy, automated deploys |
| 99.9% → 99.95% | Significant | Multi-AZ, load testing, chaos engineering, on-call |
| 99.95% → 99.99% | Substantial | Multi-region, zero-downtime deploys, advanced traffic management |
| 99.99% → 99.999% | Massive | Active-active multi-region, zero-trust networking, formal verification |

### 20.2 When to Invest in Reliability

**Cost of downtime** varies dramatically:

| Service type | Downtime cost per hour (approximate) |
|:-------------|:------------------------------------|
| Internal tool | $100-$1,000 (productivity loss) |
| B2B SaaS | $10,000-$100,000 (customer impact, SLA credits) |
| E-commerce | $100,000-$1M+ (lost sales, brand damage) |
| Financial trading | $1M+ (direct financial loss) |
| Healthcare / safety-critical | Incalculable (human safety) |

**Decision framework:**
- Cost of one more nine > cost of downtime × expected downtime reduction → not worth it.
- Cost of one more nine < cost of downtime × expected downtime reduction → invest.

### 20.3 Reliability Budget Allocation

A balanced reliability investment:

```
Monitoring and alerting:        15%
Incident response tooling:      10%
Automation (toil reduction):    25%
Redundancy and failover:        20%
Chaos engineering and testing:  15%
Capacity planning:              10%
Documentation and training:      5%
```

---

## 21. SRE Metrics and Reporting

### 21.1 Key SRE Metrics

| Metric | What it measures | Target |
|:-------|:----------------|:-------|
| **SLO compliance** | % of time SLIs meet SLO targets | 100% (by definition) |
| **Error budget remaining** | % of error budget not consumed | > 20% |
| **MTTR (Mean Time to Recover)** | Average incident duration | < 30 min for SEV1 |
| **MTTD (Mean Time to Detect)** | Alert fires to human aware | < 5 min |
| **MTTM (Mean Time to Mitigate)** | Detection to service restored | < 15 min |
| **Incident count** | Total incidents per period | Trending down |
| **Toil percentage** | % of SRE time on toil | < 50% |
| **Change failure rate** | % of deploys causing incidents | < 15% |
| **On-call pages** | Pages per shift | < 2 per 12h shift |
| **Postmortem action completion** | % of action items completed on time | > 90% |

### 21.2 Monthly SRE Report Template

```
SRE MONTHLY REPORT — May 2026

EXECUTIVE SUMMARY
  SLO met: 8/10 services
  Error budget status: 6 services > 50%, 2 services 20-50%, 2 services < 20%
  Incidents: 2 SEV1, 5 SEV2, 12 SEV3
  MTTR (SEV1): 22 minutes (target: < 30)
  Toil: 38% (target: < 50%)

SLO PERFORMANCE
  [Table of each service with SLO, actual SLI, budget remaining]

INCIDENT TRENDS
  Total incidents: 19 (down from 23 last month)
  Repeat incidents: 3 (same root causes as previous months)
  Postmortem actions completed: 14/17 (82%)

ON-CALL HEALTH
  Pages per shift: 1.8 (target: < 2)
  After-hours pages: 4 (target: < 8)
  False positive rate: 22% (target: < 20%) ⚠️

TOIL REDUCTION
  Completed: automated cert rotation (saves 4h/week)
  In progress: self-service database provisioning
  Planned: automated capacity scaling for 3 services

RISKS AND ESCALATIONS
  - Service X error budget < 10% — feature freeze recommended
  - Database Y approaching capacity — provision needed by June 15
  - On-call team Z understaffed — hiring request submitted

NEXT MONTH PRIORITIES
  1. Reduce false positive alert rate to < 20%
  2. Complete database capacity provisioning
  3. Launch chaos engineering program for payment service
```

---

## 22. SRE Anti-Patterns

| Anti-pattern | Symptom | Fix |
|:-------------|:--------|:----|
| **SRE as gatekeepers** | SRE team blocks all deploys | Error budget policy decides, not SRE opinions |
| **SLO theater** | SLOs defined but not enforced | Automate error budget tracking, enforce policy |
| **Postmortem graveyard** | Postmortems written but actions never completed | Track completion rate, review in service reviews |
| **Hero culture** | One person always fixes everything | Document knowledge, distribute on-call, pair during incidents |
| **Alert hoarding** | Thousands of alerts, most ignored | Quarterly alert review, delete unused, tune thresholds |
| **100% SLO** | Team demands zero errors | 100% is wrong target. It prevents all change. |
| **SRE island** | SRE team operates in isolation | Embed SREs in product teams, shared on-call |
| **Toil acceptance** | "That's just how it works" | Measure toil, set reduction goals, prioritize automation |
| **Copying Google** | Adopting Google's entire SRE model | Adapt principles to your scale. Start with SLOs and postmortems. |

---

## 23. Getting Started: SRE Adoption Roadmap

### Phase 1: Foundation (Month 1-3)
```
□ Define SLIs and SLOs for top 3 critical services
□ Implement SLI measurement (Prometheus, CloudWatch, etc.)
□ Set up dashboards with golden signals
□ Configure burn-rate alerts
□ Establish on-call rotation
□ Write runbooks for existing alerts
```

### Phase 2: Practice (Month 3-6)
```
□ Implement error budget policy
□ Conduct first blameless postmortem
□ Measure and categorize toil
□ Automate top 3 toil items
□ Run first game day
□ Set up service review cadence
```

### Phase 3: Scale (Month 6-12)
```
□ Extend SLOs to all production services
□ Implement progressive delivery (canary, feature flags)
□ Automate chaos experiments
□ Build internal developer platform (golden paths)
□ Track SRE metrics and report monthly
□ Production readiness review process for new services
```

### Phase 4: Maturity (Month 12+)
```
□ SLO-driven development (reliability as a product requirement)
□ Continuous chaos engineering
□ Toil consistently < 30%
□ Self-service infrastructure
□ Cross-team reliability standards
□ Reliability as a competitive advantage
```

---

## Exercises

### Exercise 1: Define SLOs for a Multi-Tier Service

Given an e-commerce platform with three tiers (API gateway, order service, payment service):
1. Define one availability SLI and one latency SLI for each tier using the good-events / valid-events model.
2. Set a 30-day rolling SLO for each SLI (e.g., availability >= 99.9%, p99 latency <= 300 ms).
3. Calculate the error budget in minutes for each SLO.
4. Draft a one-page error-budget policy that specifies what happens when budget is > 50%, 25–50%, < 25%, and exhausted.
5. Implement the availability SLI as a Prometheus recording rule and create a Grafana dashboard panel that displays remaining error budget as a percentage.

### Exercise 2: Burn-Rate Alerting

1. For a 99.9% availability SLO over 30 days, calculate the 1-hour, 6-hour, and 3-day burn rates that correspond to consuming the entire budget in 1 hour, 6 hours, and 3 days respectively.
2. Write multi-window, multi-burn-rate Prometheus alerting rules following the Google SRE Workbook method (fast-burn page, slow-burn ticket).
3. Deploy the rules to a test Prometheus instance and trigger each alert by injecting synthetic errors.
4. Document the expected response action for each alert severity (page vs. ticket).

### Exercise 3: Blameless Postmortem

Using the scenario: "A config change pushed to production caused a 45-minute outage of the payment service, affecting 12% of checkout attempts":
1. Write a postmortem document following the Google SRE template: title, date, authors, status, summary, impact, timeline, root cause, trigger, detection, resolution, lessons learned, action items.
2. Each action item must have an owner, priority (P0–P3), and a due date.
3. Identify at least two contributing factors beyond the immediate trigger.
4. Propose one preventive action (stop it from happening) and one mitigative action (reduce impact if it recurs).

### Exercise 4: Toil Measurement and Reduction

1. For one week, log every operational task you perform using a structured format: task name, duration, frequency, manual (yes/no), automatable (yes/no), enduring value (yes/no).
2. Calculate your toil percentage: (time on toil tasks / total work time) * 100.
3. Classify each toil item by automation ROI: (weekly time spent * 52) / estimated automation effort.
4. Pick the top-3 highest-ROI items and write a one-paragraph automation proposal for each.
5. Implement at least one automation and measure the time saved over the following week.

### Exercise 5: Game Day — Chaos Experiment

Design and execute a controlled chaos experiment:
1. Define a hypothesis: "If the order-service database connection pool is exhausted, the circuit breaker trips within 5 seconds and the service returns 503 with a retry-after header."
2. Document the blast radius, steady-state metrics, and abort conditions.
3. Execute the experiment in a staging environment using a tool of choice (Chaos Mesh, Litmus, Gremlin, or manual fault injection).
4. Record observations: did the hypothesis hold? What was the actual latency spike, error rate, and recovery time?
5. Write up findings and any corrective actions in a mini-postmortem format.

---

## Readings and References

### Books

| Title | Authors | Publisher | Year | Notes |
|:------|:--------|:----------|:-----|:------|
| *Site Reliability Engineering: How Google Runs Production Systems* | Beyer, Jones, Petoff, Murphy | O'Reilly Media | 2016 | The foundational SRE text; free at sre.google |
| *The Site Reliability Workbook: Practical Ways to Implement SRE* | Beyer, Murphy, Rensin, Kawahara, Thorne | O'Reilly Media | 2018 | Hands-on companion with SLO, alerting, and toil recipes; free at sre.google |
| *Building Secure and Reliable Systems* | Adkins, Beyer, Blankinship, Lewandowski, Oppenheimer, Stubblefield | O'Reilly Media | 2020 | Third Google SRE book — intersection of security and reliability |
| *Implementing Service Level Objectives* | Alex Hidalgo | O'Reilly Media | 2020 | Practitioner guide to SLI selection, SLO negotiation, and error-budget policies |

### Online Resources

| Resource | URL | Retrieved |
|:---------|:----|:----------|
| Google SRE Books (free online) | https://sre.google/books/ | 2026-05-29 |
| Google SRE Workbook — Implementing SLOs | https://sre.google/workbook/implementing-slos/ | 2026-05-29 |
| Google SRE Workbook — Error Budget Policy | https://sre.google/workbook/error-budget-policy/ | 2026-05-29 |
| OpenSLO Specification | https://openslo.com/ | 2026-05-29 |
| Nobl9 — Complete Guide to Error Budgets | https://www.nobl9.com/resources/a-complete-guide-to-error-budgets-setting-up-slos-slis-and-slas-to-maintain-reliability | 2026-05-29 |
| Nerd Level Tech — Mastering SRE Practices (2025) | https://nerdleveltech.com/mastering-sre-practices-a-complete-2025-guide | 2026-05-29 |
| Netdata — Designing Error Budget Policies | https://www.netdata.cloud/academy/designing-error-budget-policies/ | 2026-05-29 |
| Sedai — SRE Error Budgets | https://sedai.io/blog/sre-error-budgets | 2026-05-29 |
| CNCF — Chaos Engineering Whitepaper | https://www.cncf.io/reports/chaos-engineering/ | 2026-05-29 |

### Papers and Specifications

- Treynor Sloss, B. (2017). *The Calculus of Service Availability*. ACM Queue, 15(2).
- Dickerson, M. (2018). *The Hierarchy of Reliability*. Presented at SREcon Americas.
- Nygard, M. T. (2018). *Release It! Design and Deploy Production-Ready Software*, 2nd ed. Pragmatic Bookshelf.

---

## Cross-References

| Module | File | Relationship |
|:-------|:-----|:-------------|
| 5.1 — Container Internals | [01_Container_Internals.md](./01_Container_Internals.md) | cgroup resource limits and OOM behaviour directly impact SLI measurement |
| 5.2 — Kubernetes Architecture | [02_Kubernetes_Architecture.md](./02_Kubernetes_Architecture.md) | K8s probes, PDBs, and HPA are the enforcement layer for SRE reliability targets |
| 5.4 — Infrastructure as Code | [04_Infrastructure_as_Code.md](./04_Infrastructure_as_Code.md) | IaC enables reproducible infrastructure — a prerequisite for SRE's "cattle not pets" philosophy |
| 5.5 — Observability, SLI/SLO/SLA | [05_Observability_SLI_SLO_SLA.md](./05_Observability_SLI_SLO_SLA.md) | Deep dive into the observability stack that provides SLI data to SRE |
| 5.6 — Cloud Architecture | [06_Cloud_Architecture_AWS_Azure_GCP.md](./06_Cloud_Architecture_AWS_Azure_GCP.md) | Cloud-managed SLAs and multi-region patterns support SRE availability targets |
| Database Engineering | [03_Database_Engineering/](../03_Database_Engineering/) | Database reliability (replication, failover, backups) is a critical SRE concern |

---

## Glossary

| Term | Definition |
|:-----|:-----------|
| **Burn Rate** | The rate at which error budget is being consumed relative to a uniform consumption over the SLO window; a burn rate of 1.0 means the budget will be exactly exhausted at window end |
| **Error Budget** | The quantified amount of unreliability permitted by an SLO; calculated as 1 − SLO target (e.g., 0.1% for a 99.9% SLO) |
| **Game Day** | A planned exercise where teams inject controlled failures into production or staging to test resilience and incident response |
| **Golden Signals** | The four key metrics for monitoring any service: latency, traffic, errors, and saturation (from the Google SRE book) |
| **Incident Commander** | The designated leader during an incident who coordinates response, communication, and decision-making |
| **Mean Time to Detect (MTTD)** | Average elapsed time between the onset of an incident and its detection by monitoring or humans |
| **Mean Time to Recover (MTTR)** | Average elapsed time from incident detection to full service restoration |
| **Postmortem** | A structured, blameless document produced after an incident that captures timeline, root cause, impact, and action items |
| **SLA (Service Level Agreement)** | A contractual commitment between a provider and customer specifying consequences (credits, penalties) for SLO violations |
| **SLI (Service Level Indicator)** | A quantitative measure of service behaviour expressed as a ratio of good events to valid events |
| **SLO (Service Level Objective)** | An internal reliability target for an SLI over a defined time window (e.g., "99.9% of requests succeed within 300 ms over 30 days") |
| **Toil** | Manual, repetitive, automatable operational work that scales linearly with service growth and provides no enduring value |
| **Chaos Engineering** | The discipline of experimenting on a distributed system to build confidence in its ability to withstand turbulent conditions in production |
| **On-Call** | A rotation in which engineers are reachable and responsible for responding to production incidents within defined response-time SLAs |
| **Runbook** | A documented procedure for responding to a specific alert or operational scenario, enabling consistent and rapid incident response |