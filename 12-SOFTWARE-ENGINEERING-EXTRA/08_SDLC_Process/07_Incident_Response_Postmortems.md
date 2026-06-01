---
corso: "SWE Masterclass"
fase: "8 — SDLC & Process"
modulo: "08.7"
titolo: "Incident Response & Postmortems"
versione: "NIST SP 800-61 Rev. 3 / CSF 2.0"
livello: "Advanced"
prerequisiti:
  - "Production operations and on-call rotation experience"
  - "Familiarity with monitoring, alerting, and observability stacks"
  - "Understanding of SLA/SLO/SLI concepts"
  - "Basic knowledge of change management processes"
obiettivi:
  - "Design a severity classification matrix and map it to response SLAs"
  - "Execute a full incident lifecycle from detection through follow-up"
  - "Facilitate a blameless postmortem that produces actionable root-cause analysis"
  - "Build and evaluate incident metrics dashboards (MTTD, MTTR, change failure rate)"
  - "Plan and run a chaos-engineering game day to validate incident readiness"
tag: [incident-response, postmortem, on-call, SRE, chaos-engineering, blameless-culture, NIST-800-61, error-budget]
---

# Module 8.7: Incident Response & Postmortems

> **Learning objectives — by the end of this module you will be able to:**
>
> 1. Design a severity classification matrix and map each level to response SLAs, communication cadence, and escalation paths.
> 2. Execute a full incident lifecycle — detection, triage, mitigation, resolution, postmortem, and follow-up — using the Incident Commander model.
> 3. Facilitate a blameless postmortem that produces 5-Whys or Fishbone root-cause analysis with owner-assigned, time-bound action items.
> 4. Build and evaluate incident metrics dashboards (MTTD, MTTR, change failure rate, recurrence rate) to drive continuous improvement.
> 5. Plan and run a chaos-engineering game day, measure response readiness, and feed findings back into runbooks and alert tuning.

> **Module 08.7** · **Last updated:** 2026-05-22

## Guiding ideas

1. **IC (Incident Commander) role rotates; not seniority-based.**
2. **Comms updates every 30 min during incident.**
3. **Blameless postmortem: focus on system, not individual.**
4. **Action items with owner + due date; close within 30 days.**
5. **Pareto: 20% root causes generate 80% incidents.**
6. **Every incident is a learning opportunity, not a failure.**

---

## 1. Why Incident Response Matters

Every production system will fail. The question is not whether, but when, how
badly, and how fast you recover. A structured incident response process reduces
MTTR (Mean Time to Resolve), limits blast radius, preserves evidence for
learning, and prevents recurring incidents.

### 1.1 The cost of incidents

| Impact type | Example | Cost |
|---|---|---|
| Revenue loss | E-commerce site down for 1 hour | Direct revenue × downtime |
| Customer trust | Repeated outages, poor communication | Churn, brand damage |
| Engineering time | All-hands firefighting, postmortem | Opportunity cost |
| SLA breach | 99.9% SLA with too many minutes down | Contractual penalties, credits |
| Regulatory | Data breach without timely notification | Fines (GDPR: up to 4% annual revenue) |
| Employee burnout | Chronic on-call stress, hero culture | Attrition, hiring cost |

### 1.2 Incident vs. problem vs. change

| Concept | Definition | Example |
|---|---|---|
| **Incident** | Unplanned interruption or degradation | API returning 500 errors |
| **Problem** | Root cause of one or more incidents | Memory leak in service X |
| **Change** | Planned modification to the system | Deploy new version of service X |

Incidents require immediate response. Problems require investigation. Changes
require controlled deployment. Conflating them causes either panic during
routine changes or complacency during real incidents.

---

## 2. Severity Levels

A severity classification determines the urgency, communication cadence, and
staffing level for an incident.

### 2.1 Severity definitions

| Level | Name | Definition | Examples |
|---|---|---|---|
| **SEV1** | Critical | Total service outage or data loss/breach affecting all users | Complete site down, payment processing broken, data breach |
| **SEV2** | Major | Significant feature outage affecting many users | Search broken, login failing for 30% of users, payment delays |
| **SEV3** | Minor | Partial degradation affecting some users | Slow page loads (>5s), email notifications delayed, non-critical feature broken |
| **SEV4** | Low | Cosmetic or non-impacting issue | Typo in UI, incorrect color, minor logging error |

### 2.2 Severity response matrix

| Aspect | SEV1 | SEV2 | SEV3 | SEV4 |
|---|---|---|---|---|
| **Response time** | < 5 min | < 15 min | < 1 hour | Next business day |
| **Comms cadence** | Every 15 min | Every 30 min | Every 2 hours | Async |
| **IC required** | Yes, dedicated | Yes | Optional | No |
| **War room** | Yes | Yes | No | No |
| **Exec notification** | Immediately | Within 30 min | Daily summary | No |
| **Customer comms** | Status page + proactive email | Status page | Status page if long | No |
| **Postmortem required** | Yes, within 3 days | Yes, within 5 days | If recurrent | No |
| **On-call escalation** | Page primary + secondary | Page primary | Notify in channel | Ticket |

### 2.3 Severity misclassification

**Under-classifying** (calling a SEV1 a SEV3): slow response, larger impact,
customer complaints, SLA breach.

**Over-classifying** (calling a SEV4 a SEV1): alert fatigue, crying wolf,
engineers stop taking pages seriously.

Calibrate regularly: review severity classifications in postmortems. If the
classification was wrong, discuss why and adjust criteria.

---

## 3. On-Call Practices

### 3.1 On-call structure

```
Primary on-call: first responder to pages
    │
    ▼ (if unacknowledged after 5 min)
Secondary on-call: backup
    │
    ▼ (if unacknowledged after 10 min)
Engineering manager: escalation point
    │
    ▼ (if SEV1 or unacknowledged after 15 min)
VP Engineering / CTO: executive escalation
```

### 3.2 On-call responsibilities

```
During on-call rotation:
□ Acknowledge pages within 5 minutes
□ Triage: determine severity, assess blast radius
□ Mitigate: stop the bleeding (rollback, failover, feature flag off)
□ Communicate: update status page, notify stakeholders
□ Escalate: if beyond your expertise, escalate immediately
□ Document: timestamp every action in the incident channel
□ Hand off: brief the next responder at rotation change

NOT during on-call rotation:
□ Do not do deep investigation during incident (that's for postmortem)
□ Do not deploy unrelated changes during active incident
□ Do not fix root cause during incident (fix symptoms, investigate later)
```

### 3.3 On-call health

| Practice | Purpose |
|---|---|
| **Rotation length: 1 week** | Long enough for context, short enough to avoid burnout |
| **Handoff document** | Outgoing on-call briefs incoming on outstanding issues |
| **Follow-the-sun** | Distribute across time zones to avoid overnight pages |
| **On-call compensation** | Extra pay, comp time, or PTO for on-call shifts |
| **Alert budget** | Max pages/week; if exceeded, fix alert quality before adding more |
| **Shadow on-call** | New engineers shadow before taking primary rotation |
| **Quarterly review** | Analyze page frequency, false positives, MTTR per rotation |

### 3.4 Alert quality

Bad alerts cause more damage than bad code. Alert fatigue kills incident response.

| Alert quality metric | Target | Remediation |
|---|---|---|
| False positive rate | < 5% | Tune thresholds, add hysteresis |
| Pages per week | < 2 per on-call | Fix noisy alerts, consolidate |
| Actionable rate | > 95% | Every alert has a runbook; remove alerts without one |
| Acknowledgment time | < 5 min | Verify paging reaches the right person |
| MTTR per alert | Trending down | Improve runbooks, automate mitigations |

```
Alert quality tiers:
  Tier 1 (Page): Wake-me-up-at-3am severity. User-facing impact confirmed.
  Tier 2 (Notify): Important but not urgent. Slack channel notification.
  Tier 3 (Log): Informational. Dashboard only. No notification.

Rule: If a Tier 1 alert fires and the on-call can't do anything about it
at 3 AM, it should be Tier 2.
```

### 3.5 PagerDuty / Opsgenie / Incident.io configuration

```yaml
# PagerDuty service configuration (conceptual)
services:
  - name: "API Service"
    escalation_policy:
      - target: primary-on-call
        timeout_minutes: 5
      - target: secondary-on-call
        timeout_minutes: 5
      - target: engineering-manager
        timeout_minutes: 10
    alert_grouping:
      type: intelligent
      timeout_seconds: 300    # Group related alerts within 5 min
    auto_resolve:
      timeout_minutes: 240    # Auto-resolve after 4 hours if no update
```

---

## 4. Incident Lifecycle

### 4.1 The six phases

```
1. DETECTION        2. TRIAGE          3. MITIGATION
   Alert fires or      Severity          Stop the
   user reports         classification    bleeding
        │                    │                │
        ▼                    ▼                ▼
4. RESOLUTION       5. POSTMORTEM      6. FOLLOW-UP
   Root cause           Blameless          Action items
   fixed                analysis           completed
```

### 4.2 Phase 1: Detection

**How incidents are detected:**

| Detection method | Time to detect | Reliability |
|---|---|---|
| Synthetic monitoring (uptime checks) | < 1 min | High for availability |
| Metric alerts (latency, error rate) | 1-5 min | High for performance |
| Log-based alerts (error patterns) | 2-10 min | Medium (log pipeline latency) |
| Customer reports | 15-60 min | Low (late, incomplete) |
| Social media / HN | 30-120 min | Very late |
| Internal discovery (engineer notices) | Variable | Unreliable |

**Goal:** Detect before customers do. Synthetic monitoring + metric alerts should
catch 90%+ of incidents before any user report.

### 4.3 Phase 2: Triage

The first responder determines severity and decides who else to involve.

```
Triage decision tree:
  Is the service completely down?
  ├── Yes → SEV1 → Page IC, open war room
  └── No
      ├── Is it affecting > 10% of users?
      │   ├── Yes → SEV2 → Page IC
      │   └── No
      │       ├── Is it a data integrity issue?
      │       │   ├── Yes → SEV1 → Page IC + data team
      │       │   └── No
      │       │       ├── Is it degrading performance > 2x normal?
      │       │       │   ├── Yes → SEV3 → Notify in channel
      │       │       │   └── No → SEV4 → Create ticket
      │       │       └──
      │       └──
      └──
```

### 4.4 Phase 3: Mitigation

The goal of mitigation is to restore service, not to fix the root cause. Speed
matters more than elegance.

**Common mitigation actions:**

| Action | When to use | Time to effect |
|---|---|---|
| Rollback deployment | Bad deploy caused the incident | 1-5 min |
| Feature flag off | Specific feature is broken | < 1 min |
| Scale up | Capacity issue | 2-10 min |
| Failover to secondary | Primary region/instance down | 1-15 min |
| Block bad traffic | DDoS or bad actor | 1-5 min |
| Restart service | Memory leak or stuck process | 1-2 min |
| Switch to maintenance mode | Need time to investigate safely | < 1 min |
| Revert database migration | Migration caused data issue | 5-30 min |
| DNS redirect | Route around broken component | 5-30 min (TTL) |

### 4.5 Phase 4: Resolution

Root cause identified and permanently fixed. This may happen during the incident
(simple cases) or in follow-up work (complex cases).

Resolution is confirmed when:
- The fix is deployed to production.
- Monitoring confirms the issue is resolved.
- Customer-facing impact has ended.
- Status page updated to "resolved."

### 4.6 Phase 5: Postmortem (covered in detail in Section 6)

### 4.7 Phase 6: Follow-up

Action items from the postmortem are tracked to completion.

```
Action item tracking:
  - Each item has an owner and a due date (max 30 days)
  - Items are tracked in a shared system (Jira, Linear, GitHub Issues)
  - Weekly review of open action items in team standup
  - Items not completed by due date are escalated to engineering manager
  - Quarterly review: % of action items completed on time
```

---

## 5. Incident Commander Role

### 5.1 What the IC does

The IC is the single point of coordination during an incident. They do NOT
necessarily fix the problem — they coordinate.

| Responsibility | Details |
|---|---|
| **Assess severity** | Classify and reclassify as information emerges |
| **Assemble the team** | Page relevant engineers, coordinate across teams |
| **Run the war room** | Facilitate discussion, prevent chaos, assign tasks |
| **Communicate** | Update status page, Slack, stakeholders at cadence |
| **Track timeline** | Ensure all actions and findings are timestamped |
| **Make decisions** | When team disagrees, IC decides (rollback now? wait?) |
| **Declare resolution** | Confirm the incident is over |
| **Initiate postmortem** | Schedule and assign postmortem facilitator |

### 5.2 What the IC does NOT do

- Debug the code (delegate to subject matter experts).
- Write the fix (delegate).
- Talk to customers directly (delegate to support/comms).
- Make heroic solo efforts (the role is coordination, not heroism).

### 5.3 IC rotation

IC duty rotates across the engineering team. Every engineer should serve as IC
at least once per quarter to build the skill.

**IC training program:**

```
Level 1 (shadow): Observe 2 real incidents as IC shadow
Level 2 (practice): Run 2 game day incidents as IC
Level 3 (live): IC a real SEV3 incident with a shadow IC
Level 4 (qualified): IC any severity independently
```

### 5.4 War room protocols

```
War room rules:
1. IC speaks first in each update cycle
2. One conversation at a time (no side discussions)
3. State findings as facts, not guesses ("I see X in logs" not "I think it might be Y")
4. Actions are assigned explicitly ("Alice, please check database connections")
5. Every 15 min: IC summarizes status, asks for new findings
6. Use a shared document for timeline (not just voice/chat)
7. Non-essential people listen, don't speak (mute by default in video)
8. If you have a theory, state it to the IC, not to the channel at large
```

### 5.5 Communication templates

**Status page update (initial):**

```
Title: Elevated Error Rates on API

Status: Investigating

We are currently investigating elevated error rates on our API.
Some users may experience failed requests or slow responses.
Our team is actively working on the issue.

Next update in 30 minutes or sooner if there is a significant change.

Posted: 2026-05-22T14:30:00Z
```

**Status page update (identified):**

```
Title: Elevated Error Rates on API

Status: Identified

We have identified the cause of elevated error rates as a faulty
configuration deployment. We are rolling back the change.
Service should begin recovering within the next 15 minutes.

Next update in 15 minutes.

Updated: 2026-05-22T15:00:00Z
```

**Status page update (resolved):**

```
Title: Elevated Error Rates on API

Status: Resolved

The issue causing elevated API error rates has been resolved.
A faulty configuration was deployed at 14:15 UTC and rolled back
at 15:05 UTC. Full service was restored at 15:10 UTC.

Total impact duration: approximately 55 minutes.
Affected services: REST API, Webhooks.
No data loss occurred.

We will publish a detailed postmortem within 5 business days.

Resolved: 2026-05-22T15:10:00Z
```

**Slack channel update (for internal stakeholders):**

```
🔴 INCIDENT — SEV2 — API Error Rates
IC: @alice
Channel: #inc-2026-05-22-api-errors

Status: INVESTIGATING
Impact: ~15% of API requests returning 500
Duration: 30 minutes so far
Customer-facing: Yes, status page updated

Last action: Checking recent deploys for correlation
Next update: 14:45 UTC

@support-team: Known issue, direct customers to status page
@sales-team: Hold on sending SLA breach calculations until resolved
```

**Email to affected customers (post-resolution):**

```
Subject: Resolved: API Service Disruption — [Date]

Dear [Customer],

Between [start time] and [end time] UTC on [date], our API service
experienced elevated error rates. Approximately [X]% of requests
returned errors during this period.

Root cause: [one sentence]
Impact to your account: [specific impact if known]
Resolution: [one sentence]

We are conducting a thorough review and will implement safeguards
to prevent recurrence. A detailed incident report will be available
at [link] within 5 business days.

We sincerely apologize for the disruption.

[Name], [Title]
```

---

## 6. Blameless Postmortems

### 6.1 The blameless principle

Blameless does NOT mean "no one is accountable." It means:

- We don't punish people for making mistakes.
- We examine the system that allowed the mistake.
- We ask "how did the system make this the easy/obvious thing to do?" not
  "who screwed up?"
- People are more likely to report near-misses if there's no punishment.
- We distinguish between human error and negligence (rare).

**Why blameless works:** If engineers fear punishment, they hide mistakes, avoid
risky but necessary work, and the organization learns nothing.

### 6.2 Postmortem format (comprehensive)

```markdown
# Postmortem: [Incident Title]

**Date:** [YYYY-MM-DD]
**Authors:** [Postmortem writer(s)]
**Status:** Draft | Review | Final
**Severity:** SEV[1-4]
**IC:** [Name]

## Executive Summary
[2-3 sentences: what happened, impact, duration, resolution]

## Impact
- **Duration:** [start time] to [end time] UTC ([N] minutes)
- **Users affected:** [number or percentage]
- **Revenue impact:** [estimated dollar amount or "not quantified"]
- **SLA impact:** [SLA credits owed, if any]
- **Data impact:** [data loss, corruption, or exposure — or "none"]
- **Downstream impact:** [services or partners affected]

## Timeline (UTC)

| Time | Event |
|------|-------|
| 14:15 | Deploy v2.3.4 to production (config change to payment service) |
| 14:18 | Error rate alert fires (>5% 5xx responses) |
| 14:20 | On-call acknowledges page |
| 14:22 | On-call begins investigation, checks recent deploys |
| 14:25 | On-call identifies correlation with v2.3.4 deploy |
| 14:28 | IC declared (Alice), war room opened |
| 14:30 | Status page updated: "Investigating" |
| 14:35 | Decision: rollback v2.3.4 |
| 14:38 | Rollback initiated |
| 14:42 | Rollback complete, error rate dropping |
| 14:45 | Error rate back to baseline |
| 14:50 | IC confirms resolution, monitoring for 15 min |
| 15:05 | IC declares incident resolved |
| 15:10 | Status page updated: "Resolved" |

## Root Cause

### What happened
[Detailed technical description of what went wrong]

### 5 Whys Analysis
1. **Why did users see errors?** The payment service returned 500 errors
   for all requests.
2. **Why did the payment service fail?** The database connection string
   pointed to a non-existent host after the config change.
3. **Why was the config wrong?** The config template used a variable
   `DB_HOST_PROD` that was renamed to `DB_PRIMARY_HOST` in a recent
   infrastructure change, but the payment service template wasn't updated.
4. **Why wasn't this caught in staging?** Staging uses a different config
   template that still had the old variable name (which worked in staging).
5. **Why were staging and production configs different?** No automated
   check validates config parity between environments.

### Contributing Factors
- No integration test that verifies database connectivity after config deploy.
- Config change was deployed globally (no canary).
- Payment service has no circuit breaker; it retried failed connections
  indefinitely, amplifying the error.

## What Went Well
- Alert fired within 3 minutes of deploy.
- On-call responded quickly (2 minutes to acknowledge).
- IC decision to rollback was fast (7 minutes from page to rollback decision).
- Rollback process worked smoothly (4 minutes to complete).
- Customer communication was timely and accurate.

## What Went Poorly
- Config change was not canary-deployed.
- Staging did not catch the issue due to config divergence.
- No automated config validation.
- War room had initial confusion about who was IC.

## Action Items

| ID | Action | Owner | Priority | Due Date | Status |
|----|--------|-------|----------|----------|--------|
| 1 | Add config validation CI check comparing staging and prod templates | @bob | P1 | 2026-06-01 | TODO |
| 2 | Implement canary deployment for config changes | @carol | P1 | 2026-06-15 | TODO |
| 3 | Add integration test that verifies DB connectivity after config deploy | @bob | P2 | 2026-06-15 | TODO |
| 4 | Add circuit breaker to payment service DB connections | @dave | P2 | 2026-06-30 | TODO |
| 5 | Update IC rotation docs to clarify declaration process | @alice | P3 | 2026-06-01 | TODO |
| 6 | Unify staging and production config templates | @carol | P2 | 2026-06-30 | TODO |

## Lessons Learned
1. Config changes need the same deployment rigor as code changes.
2. Environment divergence is a latent incident waiting to happen.
3. Fast rollback capability is the most important safety net.
4. Circuit breakers prevent cascading failures from turning a partial
   outage into a complete outage.

## Related Incidents
- [INC-2026-0234: Similar config issue in auth service](link)

## Appendix
- [Link to incident channel transcript]
- [Link to relevant dashboards]
- [Link to deploy logs]
```

### 6.3 The 5 Whys technique

Start with the observable symptom. Ask "why" at each level until you reach a
systemic root cause (usually 3-5 levels).

**Good 5 Whys:** Reaches a process, tooling, or system gap.
**Bad 5 Whys:** Stops at "because someone made a mistake" — that's blame, not
root cause.

| Level | Good example | Bad example |
|---|---|---|
| Why 1 | Users saw 500 errors | Users saw 500 errors |
| Why 2 | Payment service crashed | Payment service crashed |
| Why 3 | DB connection string was wrong | Bob typed the wrong config value |
| Why 4 | Config template used stale variable name | Bob was careless |
| Why 5 | No automated config validation exists | Bob needs more training |

The good chain leads to an action item (add config validation). The bad chain
leads to blaming an individual, which teaches nothing.

### 6.4 Alternative root cause analysis methods

| Method | Best for | Description |
|---|---|---|
| **5 Whys** | Simple, single-cause incidents | Iterative questioning |
| **Fishbone (Ishikawa)** | Multi-factor incidents | Categorize causes: People, Process, Technology, Environment |
| **Timeline analysis** | Complex, multi-actor incidents | Map all events and decisions on a timeline |
| **Human factors analysis** | Incidents involving human decisions | Analyze cognitive load, information availability, time pressure |
| **Resilience analysis** | Near-misses and "how it worked" | Study what went right and why the system was resilient |

### 6.5 Fishbone diagram for root cause analysis

```
                        ┌─── People ──────────────┐
                        │ - IC declaration delayed │
                        │ - Config deployer assumed │
                        │   staging = production   │
                        │                          │
            ┌─── Process ──────────────┐           │
            │ - No canary for config   │           │
            │ - No config diff check   │           │
            │ - No integration test    │           │
            │                          │           │
Incident ◄──┤                          │           │
            │                          │           │
            └─── Technology ──────────┐│           │
                │ - No circuit breaker ││           │
                │ - Config template    ││           │
                │   divergence         ││           │
                │ - Retry storm        │┘           │
                └──────────────────────┘            │
                                                    │
                        └─── Environment ───────────┘
                          - Staging infra differs
                            from production
```

### 6.6 Postmortem facilitation

The facilitator is NOT the IC. Ideally a neutral party who was not involved in
the incident.

**Facilitation guide:**

```
1. Set the stage (5 min)
   - State the blameless principle explicitly
   - Clarify this is about learning, not blame
   - Everyone who contributed to the incident response should attend

2. Walk through the timeline (15 min)
   - Narrator reads the timeline
   - Each participant adds their perspective
   - IC fills in decision-making context

3. Identify contributing factors (15 min)
   - What made the incident possible?
   - What made detection slow?
   - What made mitigation slow?
   - What made recovery slow?

4. Identify what went well (10 min)
   - What worked as designed?
   - Where did the team excel?
   - What saved us from a worse outcome?

5. Define action items (15 min)
   - Each action has an owner, priority, and due date
   - P1 items prevent recurrence; P2 items reduce impact; P3 improve process
   - No more than 7 action items (focus on highest impact)

6. Review and close (5 min)
   - Read action items aloud
   - Set postmortem review date (30 days)
   - Thank participants
```

### 6.7 Postmortem anti-patterns

| Anti-pattern | Why it's bad | Fix |
|---|---|---|
| Blame-focused | Engineers hide mistakes | Enforce blameless culture from leadership |
| No action items | Same incident repeats | Every postmortem must have ≥ 1 action item |
| Action items never completed | Learning lost | Track completion; review in standup |
| Too many action items | Nothing gets done | Max 7; prioritize ruthlessly |
| Postmortem weeks later | Details forgotten | Within 5 business days |
| Only IC writes it | Limited perspective | Multiple contributors |
| Not shared | No organizational learning | Publish internally (sanitized) |
| Copy-paste template | Hollow compliance | Thoughtful analysis > checkbox filling |

---

## 7. SRE Incident Lifecycle (Google)

Google's SRE book formalizes incident management into a structured lifecycle.

### 7.1 Roles during an incident

| Role | Responsibility |
|---|---|
| **Incident Commander (IC)** | Overall coordination, communication, decision-making |
| **Operations Lead (OL)** | Hands-on investigation and mitigation |
| **Communications Lead** | Status page, stakeholder updates, customer comms |
| **Scribe** | Records timeline, actions, findings in real-time |
| **Subject Matter Experts (SMEs)** | Domain experts pulled in as needed |

For small incidents (SEV3-4), one person fills multiple roles. For SEV1, each
role should be a separate person.

### 7.2 Incident documentation during the incident

The scribe maintains a live incident document (Google Doc, Notion page, or
incident management tool):

```markdown
# INC-2026-05-22-001: API Error Rates

## Status: MITIGATING
## IC: @alice
## OL: @bob
## Comms: @carol
## Scribe: @dave

## Live Timeline
- 14:15 UTC — Deploy v2.3.4
- 14:18 UTC — Error rate alert fires
- 14:20 UTC — @bob acknowledges page
- 14:22 UTC — @bob investigating, checking deploys
- 14:25 UTC — Correlation with v2.3.4 deploy confirmed
- 14:28 UTC — @alice takes IC role
- 14:30 UTC — Status page updated
- 14:35 UTC — IC decides to rollback
[updated in real-time by scribe]

## Current Hypothesis
Config change in v2.3.4 broke DB connection string for payment service.

## Actions In Progress
- @bob: Rolling back v2.3.4 (started 14:38)
- @carol: Updating status page (done 14:30)

## Open Questions
- Was any data corrupted during the outage?
- Are there other services using the same config template?
```

### 7.3 Incident management tools

| Tool | Strengths |
|---|---|
| **PagerDuty** | Alerting, escalation, on-call scheduling |
| **Opsgenie** (Atlassian) | Similar to PagerDuty, Atlassian integration |
| **Incident.io** | Slack-native incident management, postmortems |
| **FireHydrant** | Full lifecycle: declare, respond, learn |
| **Rootly** | Slack-native, retrospectives, action tracking |
| **Statuspage** (Atlassian) | Public and private status pages |
| **Betteruptime** | Uptime monitoring + status pages |

---

## 8. Chaos Engineering for Readiness

Chaos engineering proactively injects failures to test incident response
before real incidents happen.

### 8.1 Principles of chaos engineering

1. **Build a hypothesis about steady state behavior.** "If we kill one API pod,
   load balancer routes traffic to remaining pods with no user impact."
2. **Vary real-world events.** Kill pods, inject latency, corrupt data, simulate
   network partitions.
3. **Run experiments in production.** Staging doesn't have production traffic
   patterns, data volumes, or dependency behavior.
4. **Automate experiments to run continuously.** One-time experiments prove a
   point; continuous experiments catch regressions.
5. **Minimize blast radius.** Start small; increase scope as confidence grows.

### 8.2 Chaos engineering tools

| Tool | Scope | Features |
|---|---|---|
| **Chaos Monkey** (Netflix) | Instance termination | Randomly kills VMs/containers |
| **Litmus Chaos** | Kubernetes | Pod kill, network chaos, disk fill, CPU stress |
| **Chaos Mesh** | Kubernetes | Network, I/O, time, stress, JVM, DNS |
| **Gremlin** | Multi-platform (SaaS) | Resource, network, state attacks + gamedays |
| **AWS Fault Injection Service** | AWS | EC2, ECS, EKS, RDS fault injection |
| **Toxiproxy** (Shopify) | Network proxy | Latency, timeout, bandwidth, connection reset |
| **Pumba** | Docker | Container kill, network emulation |

### 8.3 Game days

Structured chaos engineering exercises where the team practices incident response
with controlled failures.

**Game day format:**

```
Preparation (1 week before):
1. Define failure scenario (e.g., "primary database becomes read-only")
2. Define expected behavior (e.g., "writes fail gracefully, reads continue")
3. Notify participants (but don't reveal the specific scenario)
4. Ensure rollback mechanism is ready
5. Choose a facilitator (not a participant)

Execution (2-4 hours):
1. Facilitator injects failure
2. On-call detects and responds as in a real incident
3. IC coordinates response
4. Team mitigates and resolves
5. Facilitator observes but doesn't intervene unless safety threshold breached

Debrief (1 hour, immediately after):
1. What happened (timeline review)
2. What surprised us
3. What was the response time for each phase?
4. What didn't work as expected?
5. Action items for improvement
```

### 8.4 Chaos engineering maturity model

| Level | Description | Activities |
|---|---|---|
| **0: None** | No chaos engineering | — |
| **1: Ad-hoc** | Occasional manual experiments | Kill a pod, see what happens |
| **2: Planned** | Regular game days | Monthly game days with scenarios |
| **3: Automated** | Continuous chaos in staging | Litmus/ChaosMesh running daily |
| **4: Production** | Continuous chaos in production | Chaos Monkey in production |
| **5: Culture** | Chaos is part of definition of done | New service must pass chaos tests |

### 8.5 Failure injection examples

```yaml
# Litmus Chaos: pod kill experiment
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: api-pod-kill
spec:
  appinfo:
    appns: production
    applabel: app=api-service
  chaosServiceAccount: litmus-admin
  experiments:
    - name: pod-delete
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: '60'          # Kill pods for 60 seconds
            - name: CHAOS_INTERVAL
              value: '10'          # Every 10 seconds
            - name: FORCE
              value: 'true'
```

```yaml
# Toxiproxy: inject 500ms latency on database connection
# toxiproxy-cli
toxiproxy-cli toxic add \
  --type latency \
  --attribute latency=500 \
  --attribute jitter=100 \
  postgres_proxy
```

```yaml
# Chaos Mesh: network partition between services
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: api-to-db-partition
spec:
  action: partition
  mode: all
  selector:
    labelSelectors:
      app: api-service
  direction: to
  target:
    selector:
      labelSelectors:
        app: postgresql
  duration: "120s"
```

---

## 9. Incident Metrics

### 9.1 Key metrics

| Metric | Definition | Target |
|---|---|---|
| **MTTD** (Mean Time to Detect) | Time from incident start to first alert | < 5 min |
| **MTTA** (Mean Time to Acknowledge) | Time from alert to human acknowledgment | < 5 min |
| **MTTR** (Mean Time to Resolve) | Time from incident start to resolution | SEV1: < 1h; SEV2: < 4h |
| **MTTM** (Mean Time to Mitigate) | Time from detection to customer impact stopped | < 15 min |
| **Incident frequency** | Incidents per week/month | Trending down |
| **Change failure rate** | % of changes causing incidents | < 5% |
| **Recurrence rate** | % of incidents that are repeats | < 10% |
| **Action item completion rate** | % of postmortem actions completed on time | > 90% |
| **Customer-reported incidents** | % detected by customers vs. monitoring | < 10% |

### 9.2 Incident dashboard

```
Incident Dashboard (Monthly)
═══════════════════════════════════════════════
Total incidents:     12 (↓ from 15 last month)
  SEV1:              0  (↓ from 1)
  SEV2:              2  (↓ from 3)
  SEV3:              7  (→ same)
  SEV4:              3  (→ same)

MTTR (avg):          42 min (↓ from 58 min)
MTTD (avg):          3 min  (→ same)
Change failure rate: 4.2%   (↓ from 6.1%)
Recurrence rate:     8%     (↓ from 15%)

Top causes:
  1. Config errors:          4 incidents (33%)
  2. Dependency failures:    3 incidents (25%)
  3. Capacity:               2 incidents (17%)
  4. Code bugs:              2 incidents (17%)
  5. Network:                1 incident  (8%)

Action items from postmortems:
  Open:      7
  Overdue:   2 (escalated)
  Completed: 23 this month
═══════════════════════════════════════════════
```

### 9.3 Incident trends analysis

Track categories of incidents over time to identify systemic issues:

```
Quarterly incident categories:
  Q1 2026:  Config: 40%  |  Deploy: 25%  |  Capacity: 20%  |  Other: 15%
  Q2 2026:  Config: 15%  |  Deploy: 30%  |  Capacity: 25%  |  Other: 30%
                    ↓ Config validation CI added in Q1
                                     ↑ New deploy pipeline, teething issues
```

---

## 10. Incident Communication Channels

### 10.1 Channel strategy

| Channel | Audience | Cadence | Content |
|---|---|---|---|
| **War room** (Slack/Zoom) | Incident responders | Continuous | Technical discussion, coordination |
| **Incident Slack channel** | Engineering org | Every 15-30 min | Status updates, severity, ETA |
| **Status page** | Customers | Every 15-30 min | Impact, workarounds, resolution status |
| **Email** | Affected customers | At resolution | Full incident report, SLA impact |
| **Exec briefing** | Leadership | At triage + resolution | Business impact, ETA, customer exposure |
| **Support channel** | Support team | At triage | Talking points, known workarounds |

### 10.2 Status page best practices

| Practice | Why |
|---|---|
| Host status page on independent infrastructure | If your infra is down, your status page should still work |
| Update proactively, not reactively | Customers should learn from your status page, not Twitter |
| Be specific about impact | "Some users" → "Users in EU region" → "~30% of EU users" |
| Provide workarounds when possible | "Use mobile app" or "Retry in 5 minutes" |
| Include next update time | Reduces support load ("we'll update in 30 minutes") |
| Post-incident report link | Reference postmortem for full details |

---

## 11. SLA, SLO, SLI — Tying Incidents to Service Levels

### 11.1 Definitions

| Term | Definition | Example |
|---|---|---|
| **SLI** (Service Level Indicator) | A metric that measures service quality | Request success rate, p99 latency |
| **SLO** (Service Level Objective) | A target value for an SLI | 99.9% success rate, p99 < 200ms |
| **SLA** (Service Level Agreement) | A contract promising a specific SLO | 99.9% uptime or credits issued |
| **Error budget** | The allowed failure (1 - SLO) | 0.1% = 43.2 min/month |

### 11.2 Error budget and incident response

```
Monthly error budget: 43.2 minutes (99.9% SLO)

Incident A: 12 minutes  → Budget remaining: 31.2 minutes
Incident B: 20 minutes  → Budget remaining: 11.2 minutes
Incident C: 15 minutes  → Budget EXCEEDED by 3.8 minutes

When budget is exceeded:
1. Freeze non-critical deploys
2. Prioritize reliability work over feature work
3. Review all recent postmortem action items
4. Conduct targeted chaos engineering
5. Resume normal operations when budget is positive again
```

---

## 12. Exercises

1. **Lab — incident drill.** Run a game day: inject a failure (kill a service,
   corrupt config), have the team respond with full IC protocol, write a
   postmortem, and track action items.

2. **Lab — severity calibration.** Take 10 past incidents and re-classify them
   using the severity matrix. Identify any misclassifications and their impact.

3. **Lab — postmortem writing.** Write a complete postmortem for a past incident
   using the full template. Facilitate a 1-hour postmortem meeting with the team.

4. **Lab — runbook validation.** Take a critical runbook and have someone who has
   never run it execute it. Document every place they get stuck. Fix the runbook.

5. **Lab — alert audit.** Review all Tier 1 alerts for the last month. Calculate
   false positive rate, acknowledgment time, and actionability. Remove or
   reclassify non-actionable alerts.

6. **Stretch — chaos engineering.** Set up Litmus Chaos or Chaos Mesh in a staging
   cluster. Define 3 experiments (pod kill, network latency, disk full). Run them
   and document findings.

7. **Stretch — incident metrics dashboard.** Build a dashboard tracking MTTD,
   MTTR, incident frequency, and change failure rate. Review monthly.

---

## 13. Recommended Reading

- Beyer, Jones, Petoff, Murphy, *Site Reliability Engineering* (O'Reilly, 2016)
  — chapters 12-14 on incident management.
- Nygard, *Release It!* (Pragmatic Bookshelf, 2nd ed. 2018) — stability patterns.
- Etsy, *Debriefing Facilitation Guide* (etsy.com/codeascraft).
- PagerDuty, *Incident Response Documentation* (response.pagerduty.com).
- Sidney Dekker, *The Field Guide to Understanding Human Error* (3rd ed., 2014).
- John Allspaw, *Post-Incident Reviews: Learning from Failure* (adaptivecapacitylabs.com).
- Casey Rosenthal, Nora Jones, *Chaos Engineering* (O'Reilly, 2020).

---

## Glossary

| Term | Definition |
|---|---|
| **IC** | Incident Commander — coordinates response during an incident |
| **OL** | Operations Lead — performs hands-on investigation and mitigation |
| **SEV1-4** | Severity classification levels (1 = most critical) |
| **MTTR** | Mean Time to Resolve — average time from incident start to resolution |
| **MTTD** | Mean Time to Detect — average time from incident start to first alert |
| **MTTA** | Mean Time to Acknowledge — average time from alert to human response |
| **MTTM** | Mean Time to Mitigate — average time from detection to customer impact stopped |
| **Blameless** | Postmortem culture that focuses on systems, not individuals |
| **5 Whys** | Root cause analysis technique using iterative "why?" questions |
| **War room** | Dedicated communication space for incident responders |
| **Error budget** | Allowed failure time defined as (1 - SLO) |
| **SLI** | Service Level Indicator — metric measuring service quality |
| **SLO** | Service Level Objective — target value for an SLI |
| **SLA** | Service Level Agreement — contractual promise of service level |
| **Game day** | Controlled chaos engineering exercise for incident readiness |
| **Chaos engineering** | Practice of injecting failures to build confidence in system resilience |
| **Fishbone diagram** | Root cause analysis method categorizing causes (People, Process, Tech, Env) |
| **Scribe** | Person who records timeline and actions during an incident |
| **Runbook** | Step-by-step operational procedure for common tasks or incidents |
| **Circuit breaker** | Pattern that prevents cascading failures by stopping retries after threshold |
| **Feature flag** | Runtime toggle to disable broken features without rollback |

---

## Readings and References

| # | Source | URL | Retrieved |
|---|--------|-----|-----------|
| 1 | NIST SP 800-61 Rev. 3 — Incident Response Recommendations and Considerations for Cybersecurity Risk Management | https://csrc.nist.gov/pubs/sp/800/61/r3/final | 2026-05-29 |
| 2 | NIST SP 800-61 Rev. 2 — Computer Security Incident Handling Guide (withdrawn, historical reference) | https://csrc.nist.gov/pubs/sp/800/61/r2/final | 2026-05-29 |
| 3 | PagerDuty — Incident Response Documentation | https://response.pagerduty.com/ | 2026-05-29 |
| 4 | PagerDuty — Postmortem Documentation (blameless postmortems, facilitation, culture) | https://postmortems.pagerduty.com/ | 2026-05-29 |
| 5 | PagerDuty — The Blameless Postmortem | https://postmortems.pagerduty.com/culture/blameless/ | 2026-05-29 |
| 6 | PagerDuty — Postmortem Process | https://response.pagerduty.com/after/post_mortem_process/ | 2026-05-29 |
| 7 | NIST Incident Response Framework — SP 800-61 Four Phases Explained | https://ir-os.com/resources/nist-incident-response-framework | 2026-05-29 |
| 8 | Beyer, Jones, Petoff, Murphy. *Site Reliability Engineering* (O'Reilly, 2016) — chapters 12-14 | — | — |
| 9 | Nygard. *Release It!* 2nd ed. (Pragmatic Bookshelf, 2018) | — | — |
| 10 | Dekker. *The Field Guide to Understanding Human Error* 3rd ed. (2014) | — | — |
| 11 | Rosenthal, Jones. *Chaos Engineering* (O'Reilly, 2020) | — | — |

---

## Cross-References

| Module / Folder | Relevance |
|---|---|
| [01_Methodologies_Agile_Scrum_Kanban.md](./01_Methodologies_Agile_Scrum_Kanban.md) | Sprint-level incident retrospective integration; Kanban WIP limits during incident follow-up |
| [02_Testing_Strategies.md](./02_Testing_Strategies.md) | Regression tests created from postmortem action items; chaos-test coverage |
| [05_Git_Branching_Strategies.md](./05_Git_Branching_Strategies.md) | Hotfix branch workflows triggered by SEV1/SEV2 incidents; rollback procedures |
| [06_Code_Review_Rubrics.md](./06_Code_Review_Rubrics.md) | Post-incident code-review gates for fixes; review rubrics for postmortem action-item PRs |
| [08_Secure_SDLC_OWASP_SAMM.md](./08_Secure_SDLC_OWASP_SAMM.md) | SAMM Operations → Incident Management practice; security-incident response alignment |
| [../04_Security_Cryptography/](../04_Security_Cryptography/) | Cryptographic incident handling (key compromise, certificate revocation); NIST CSF alignment |
