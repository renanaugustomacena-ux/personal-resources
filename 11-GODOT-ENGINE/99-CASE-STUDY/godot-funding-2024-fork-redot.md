---
course: "Godot 4 in Production"
file-role: "Case study — open-source funding, governance, and the 2024 Redot fork"
version: "Godot 4.5 / GDScript 2.0"
updated: 2026-07-27
tags: [godot, case-study, governance, open-source, funding, redot, fork, engine-risk]
---

# Case Study — Godot Funding, the 2024 Controversy, and the Redot Fork

> **Updated:** 2026-07-27 — historical synthesis; facts verified against the sources graded in [§10](#10-sources). Where accounts conflict, the dispute is stated rather than resolved.

**Type:** governance/community case study. This file supports the course's production stance: choosing an engine is a *supplier decision*, and suppliers — even MIT-licensed ones — carry governance, funding, and continuity risk that a professional evaluates explicitly.

## Contents

1. [Why this case study](#1-why-this-case-study)
2. [Background: how Godot is funded and governed](#2-background-how-godot-is-funded-and-governed)
3. [Timeline](#3-timeline)
4. [What happened (September-October 2024)](#4-what-happened-september-october-2024)
5. [Fork mechanics: what forking an MIT engine entails](#5-fork-mechanics-what-forking-an-mit-engine-entails)
6. [Stakeholder analysis](#6-stakeholder-analysis)
7. [Outcomes & current status](#7-outcomes--current-status)
8. [Lessons](#8-lessons)
9. [Discussion questions](#9-discussion-questions)
10. [Sources](#10-sources)

---

## 0. Key terms used in this file

| Term | Meaning here |
|---|---|
| **Fork** | A copy of a project's source continued independently under a new name/governance; legal by default under MIT. |
| **Upstream / downstream** | The original project a fork copies from / the fork consuming its changes (Redot is downstream of Godot). |
| **Fiscal sponsor** | Non-profit that holds funds and handles admin for a project without its own legal entity (SFC's old role for Godot). |
| **Trademark** | Legal protection of the *name/brand*, independent of the code license; the reason forks must rebrand. |
| **Steward / foundation** | The entity holding trademark, infrastructure, and funding for an open project (Godot Foundation). |
| **LTS** | Long-term support release line, maintained with fixes without breaking changes (Redot's "26.x" branding; Godot 4.5 is this course's pinned reference). |
| **Governance** | Who decides — and by what documented process — on direction, moderation, and money. |

## 1. Why this case study

In late September 2024, a single social-media post from the Godot Engine's official account triggered weeks of community conflict, moderation disputes, and — within days — a fork of the engine (**Redot**). No code was at fault; no license changed; no company was acquired. Yet studios mid-project suddenly had to answer questions normally reserved for proprietary vendors: *Who controls our toolchain? What happens if its community splits? What exactly would we do about it?*

For this course the episode is ideal teaching material because it is **recent, well documented, low-casualty, and structurally repeatable**: the same dynamics (foundation-run project + commercial satellite + volunteer community + social media) describe most large open-source projects you will ever depend on.

## 2. Background: how Godot is funded and governed

**The engine.** Godot is an MIT-licensed game engine, open-sourced in early 2014 by Juan Linietsky and Ariel Manzur. The permissive license means anyone may use, modify, redistribute, and fork the code, including commercially, with attribution (Module 01 — [GODOT_ENGINE_STUDY.md](../GODOT_ENGINE_STUDY.md)).

**Fiscal home.** From 2015 the project was a member of the **Software Freedom Conservancy** (SFC), a US non-profit that held its funds. In 2022 the project "graduated": the **Godot Foundation** was formed (August 2022, announced November 1, 2022) as a dedicated non-profit in the Netherlands, initially adopting SFC-modeled policies, with the existing project leadership committee becoming its board. It reached full operating capacity in July 2023 (sources: SFC announcement; Godot Foundation Annual Report 2023).

**Funding model.** The Foundation is funded primarily by **donations**: the Godot Development Fund (recurring individual donations), corporate sponsorships, and grants. It uses this money mainly to contract developers and administrators — by December 2024, 10 contractors on the engine (6 full-time, 4 part-time) plus 3 on administration/infrastructure, versus 2,500+ total volunteer contributors (source: Godot Foundation update, Dec 2024).

**The commercial satellite.** **W4 Games**, founded in 2021-2022 by Godot veterans including Juan Linietsky and Rémi Verschelde, is a separate for-profit company selling Godot-adjacent services (notably console porting, "W4 Consoles"). It raised a **$8.5M seed round in September 2022** (led by OSS Capital and LUX Capital) and a **$15M Series A announced December 2023** (led by OSS Capital, with investors including Naval Ravikant and GitHub CEO Thomas Dohmke). W4 does not own the engine; it funds and employs people who work on it and monetizes services around it (sources: W4 Games announcements; Game Developer, 2023-12-12).

**Where the money enters.** Individuals and companies donate through the Godot Development Fund (https://fund.godotengine.org/), one-off donations, and sponsorships; the Foundation publishes annual and financial reports on godot.foundation. This structure matters for the case: because income is many small recurring pledges rather than a few contracts, *community sentiment converts into funding signal within days* — in both directions.

**Context multiplier.** Unity's September 2023 runtime-fee controversy had pushed a wave of developers toward Godot during 2023-2024, raising both the user base and the temperature of engine-choice discussions.

## 3. Timeline

| Date | Event | Source grade* |
|---|---|---|
| early 2014 | Godot open-sourced under MIT license | P |
| 2015 | Godot joins Software Freedom Conservancy | P |
| 2022-08 / 2022-11-01 | Godot Foundation formed; SFC "graduation" announced | P |
| 2022-09 | W4 Games announces $8.5M seed (OSS Capital, LUX Capital) | P |
| 2023-07 | Foundation reaches full operating capacity | P |
| 2023-12 | W4 Games announces $15M Series A (OSS Capital lead) | P/S |
| 2024-08-15 | Godot 4.3 released | P |
| 2024-09-27 | Official Godot X account posts the "#Wokot" message | S/T |
| 2024-09-27→29 | Account blocks numerous repliers; blocking itself becomes the story; reports of a small number of GitHub/community bans (KYM records 5 GitHub blocks) | T (disputed details) |
| 2024-09-28 | Co-founder Juan Linietsky posts statements, then sets his account private | T |
| 2024-09-30 | Godot Foundation board issues a statement acknowledging mistaken blocks and offering an appeal route | P |
| 2024-09-30 | **Redot Engine fork announced** the same day; Hacker News thread reaches front page | P/S |
| 2024-10 | Wave of smaller forks and media coverage; Redot organizes team and infrastructure | S |
| 2024-12-18 | Redot 4.3 stable released (based on Godot 4.3) | P |
| 2024-12 | Godot Foundation December update: 13 contractors, policies revised (Sept 2024), asset store and priorities page announced | P |
| 2025-03-03 | Godot 4.4 released | P |
| 2025-09-15 | Godot 4.5 released (this course's pinned version) | P |
| 2026-01-31 | Redot 4.4 stable released (incorporating Godot 4.4.1) | P |
| 2026-Q1/Q2 | Redot ships its own "LTS 26.1"/"26.2" release line; 1.5-year retrospective interview published | P/T |

\* **P** = primary (the organization's own publication) · **S** = secondary (independent press) · **T** = tertiary/community documentation (treat figures with care). See [§10](#10-sources).

## 4. What happened (September-October 2024)

**The post.** On September 27, 2024, the official Godot Engine account on X (Twitter) published a short message — as archived by the Know Your Meme event page: *"Apparently game engines are woke now? Well then, we won't complain 🌈 Show us your #Wokot games below"* — responding to online discourse labeling engines and games "woke." The post drew massive engagement (KYM records ~1.7M views within three days) and polarized replies.

**The moderation response.** Over the following ~48 hours, the account operator blocked a large number of accounts. Critics documented cases where users blocked or banned from community spaces appeared to have posted mild criticism or unrelated questions; KYM's compilation includes a user reporting a GitHub block after quoting co-founder Juan Linietsky. It is **undisputed** that blocking occurred at scale and included mistakes; it is **disputed** how many blocks were responses to genuine harassment versus criticism — both existed, and no authoritative tally was published. The Godot Foundation's September 30 statement acknowledged that it had "mistakenly blocked individuals who were not participating" in harassment and opened an appeal form; it reported 5 GitHub accounts blocked for violations.

**The community split.** The hashtag "#Wokot" trended in engine-dev circles; discussion threads on X, Reddit, and Hacker News ran for weeks. On September 30, 2024 — the same day as the Foundation statement — the **Redot** fork was announced, positioning itself as a community-driven engine focused on development rather than social-media positioning. Some community members, including moderators of unofficial spaces and a number of contributors, aligned with the fork; the overwhelming majority of engine contributors remained with mainline Godot.

**On donations.** Contemporaneous social-media claims that Godot's funding collapsed are **not supported** by the figures later compiled: KYM's documentation (citing Foundation-side communications) records €170/month in cancelled sponsorships against €1,610/month in new ones in the immediate aftermath (10 cancellations, 74 new sign-ups). An earlier revision of this case study stated flatly that "donations dropped"; that claim is downgraded here to *disputed and probably false in net terms*, illustrating exactly why this file grades its sources.

**The fork wave.** Redot was not alone: October 2024 coverage (It's FOSS News) documented several fork attempts announced in the controversy's wake. This is the normal signature of such episodes — forking is cheap to announce and expensive to sustain — and, as typically happens, most attempts went dormant within months. Redot is the one that built a team, infrastructure, and a release cadence, which is why this case study tracks it specifically.

**What did not happen.** No license change, no code lockout, no service shutdown, no legal action between the parties. Every consequence flowed through *people*: attention, trust, moderation, and affiliation.

## 5. Fork mechanics: what forking an MIT engine entails

The MIT license makes the *legal* act of forking trivial — copy the repository, keep the copyright notice. Everything else is operational:

1. **Rebranding.** "Godot" (name, logo) is protected by trademark held for the project; a fork must rename and re-badge everything user-visible. Redot renamed the engine, editor branding, and namespaces where required.
2. **Infrastructure.** Upstream Godot's value includes build farms, export-template hosting, documentation sites, the asset library, and release engineering. A fork must stand all of this up itself — in practice the bulk of early fork work is infrastructure, not features.
3. **Tracking upstream.** A fork chooses between diverging (freedom, at the cost of merging pain) and tracking (staying compatible, at the cost of independence). Redot's early releases track upstream closely: Redot 4.3 (2024-12-18) is based on Godot 4.3, and Redot 4.4 stable (2026-01-31) explicitly incorporates Godot 4.4.1's features and fixes, with Redot-specific changes layered on. From 2026 Redot also introduced its own "LTS 26.x" versioning line.
4. **Governance & trust.** A fork must convince plugin authors, tutorial makers, and studios that it will still exist in three years. This is the slowest asset to build and the real moat of incumbents.
5. **Compatibility surface.** Because both engines share formats (`.tscn`, `.gdshader`, GDScript), projects port between them with little friction *while divergence stays low* — a property that decays silently over time and must be re-verified per release (see the checklist in [§8](#8-lessons)).

### What Redot changed (beyond the name)

Verifiable from Redot's own releases and communications, as of the file date:

- **Branding and identity:** full rename of engine, editor, and web presence (trademark-driven, see above).
- **Governance and positioning:** a separate team and community structure presenting itself as community-driven and focused on engine development rather than official-channel social positioning (self-description; see the Lunduke interview — a friendly venue, so treat it as the fork's own voice).
- **Release engineering:** its own cadence and, from 2026, its own **LTS 26.x** version scheme decoupled from upstream numbering, while stable releases (4.3, 4.4) explicitly incorporate the corresponding upstream Godot releases plus Redot-side changes.
- **What it did *not* change:** the license (MIT), the language (GDScript), the file formats, or — so far — any API surface large enough to break typical Godot projects, per its own release notes.

### Comparable forks in open-source history

Placing Redot on the spectrum of famous forks clarifies the possible trajectories:

| Fork (year) | Trigger | Outcome (coarse) | Analogy for Godot/Redot |
|---|---|---|---|
| OpenOffice.org → LibreOffice (2010) | Distrust of new corporate owner | Community and distros moved; fork became the de facto standard | The "fork wins" ceiling case |
| MySQL → MariaDB (2009-2010) | Acquisition of the steward | Long-term coexistence; fork strong in distros, original strong commercially | Stable two-channel equilibrium |
| ownCloud → Nextcloud (2016) | Founder/company governance split | Founder-led fork captured most community momentum | What credible leadership exit looks like |
| io.js → Node.js (2014-2015) | Governance/release-process dispute | Fork **merged back** after a neutral foundation was created | Fork as successful negotiation lever |
| Gitea → Forgejo (2022) | Ownership-transfer concerns | Soft fork tracking upstream under non-profit governance | Closest structural match to Redot's tracking strategy |

The spread of outcomes — replacement, coexistence, reabsorption — is why the course treats "fork health" as a metric to *monitor*, not a verdict to pronounce once.

## 6. Stakeholder analysis

| Stakeholder | Stake | Exposure in this episode | Post-episode position |
|---|---|---|---|
| Godot Foundation | Donations, trademark, project stewardship | Reputation and moderation legitimacy questioned | Revised policies (Sept 2024), continued growth, more formal communications |
| Core maintainers | Engine quality, sustainable workload | Harassment waves in both directions; time lost to conflict | Largely stayed; release cadence (4.4, 4.5) undisturbed |
| W4 Games | Commercial services on a healthy mainline | Indirect: investor and customer perception of ecosystem stability | Unaffected operationally; continued release-cycle involvement |
| Volunteer contributors | Meritocratic access, community belonging | Some blocked/alienated; most unaffected | Vast majority upstream; a minority moved to Redot |
| Studios & users | Toolchain continuity | Forced to articulate engine-risk posture mid-project | Mostly stayed; gained a fallback option they didn't ask for |
| Redot team | Fork viability, differentiated identity | Had to prove it was more than a protest repo | Shipping stable releases on its own cadence since 2024-12 |
| Plugin/asset ecosystem | Single compatible target | Risk of a split API surface | Minimal practical split so far due to Redot's upstream tracking |

## 7. Outcomes & current status

As verifiable through mid-2026:

- **Mainline Godot continued uninterrupted:** 4.4 (2025-03-03) and 4.5 (2025-09-15) shipped on cadence with thousands of contributors; the Foundation reported growing contractor staffing and new programs (asset store, priorities page) in its December 2024 update.
- **Redot survived past the "protest fork" phase**, which most fork attempts do not: stable releases (4.3 in 2024, 4.4 in 2026), its own LTS branding, and an active team giving retrospective interviews at the 1.5-year mark.
- **The ecosystem did not meaningfully split:** documentation, plugins, and tutorials still target Godot; Redot's close upstream tracking means most Godot material works there, which is simultaneously Redot's compatibility strength and its differentiation problem.
- **The original revision of this file predicted** "the ecosystem effectively splits into two channels" — that reads as overstated in 2026: the accurate description is *one mainline channel plus a maintained downstream fork*.
- **Governance changes stuck:** the Foundation's move from SFC-template policies to organization-specific policies (adopted September 2024) and more formal communication practice are the lasting institutional traces of the episode.

### A monitoring dashboard for fork health

"Track the trajectory quarterly" (original lesson #3) is only actionable with concrete probes. This is the course's suggested quarterly 30-minute check, applicable to any engine/fork pair:

| Metric | Where to check | Healthy signal |
|---|---|---|
| Release cadence | Both projects' release pages | Stable releases within their announced windows |
| Upstream-merge lag (fork) | Fork release notes ("based on X") | Fork incorporates upstream stable within 1-2 quarters |
| Contributor breadth | GitHub insights/contributors | No single-digit contributor concentration on critical subsystems |
| Funding trend | Foundation reports / dev fund page | Stable or growing recurring support |
| Infrastructure ownership | Build/template/docs hosting | Reproducible from public sources, not one person's server |
| Ecosystem targeting | Your critical plugins' CI matrices | Plugins test against the branch *you* ship on |
| Community temperature | Forum/issue tone, moderation actions | Conflicts resolved by documented process |

Log the seven answers with dates in your project's engine-risk note ([00-CAPSTONE.md](../00-CAPSTONE.md), Appendix A §7). Three consecutive degrading quarters is the trigger to actually cost out your exit plan.

## 8. Lessons

### For open-source governance

1. **The official account is the project.** A social account with the project's name carries governance weight; posting and moderation from it are *governance acts*, and mistakes there cost trust at the same rate as bad releases.
2. **Moderation needs due process before the crisis.** The Foundation's appeal form was created after mistaken blocks; projects should define block/ban criteria, separation of roles, and appeal routes in calm times.
3. **Forking is the constitutional safety valve** — and its *credible possibility* disciplines incumbents even when almost nobody leaves. (Preserved from the original revision: "Open-source forking is a feature, not a bug.")
4. **Outrage metrics are not exit metrics.** Viral anger predicted a donation collapse that the verified figures contradict; governance decisions should track committed resources (donations, contributions), not engagement.
5. **Commercial satellites stabilize.** W4's funded, revenue-motivated interest in a healthy mainline added continuity pressure independent of community mood.

### For studios choosing an engine (preserved and extended from the original revision)

1. **Lock-in concerns are NOT eliminated by open source — only reduced.** You can still face API drift, plugin abandonment, and support fragmentation.
2. **Pin the engine version for production.** This course pins Godot 4.5; upgrades are planned migrations, not routine updates.
3. **Track fork health quarterly** for commercial projects: release cadence, contributor counts, infrastructure ownership, upstream-merge lag.
4. **Be engine-version-portable in your save layer.** Don't rely on undocumented internals; serialize plain data (Module 08 — [DATABASE_AND_PERSISTENCE.md](../DATABASE_AND_PERSISTENCE.md)).
5. **Plan asset/code portability.** GDScript and text scene formats port between close forks easily; native extensions and C# bindings may not.
6. **Keep an export pipeline that could target either fork** if you need the hedge (Module 11 — [BUILD_AND_EXPORT.md](../BUILD_AND_EXPORT.md)); a CI matrix entry is cheap insurance.
7. **Default recommendation (unchanged from the original revision):** stay with mainline Godot for new projects unless you have a specific, articulable reason to choose the fork.

### Course recommendations (preserved from the original revision)

- **Stay with mainline Godot** for new projects unless you have a specific reason to choose Redot; as of 2026 mainline retains the overwhelming majority of contributors, documentation, plugins, and release infrastructure.
- **Pin the engine version for production.** Godot 4.5 is this course's pinned reference; treat every engine upgrade as a planned migration with a test pass, never an automatic update.
- **Keep an export script that would work with both forks** if you need the hedge — while divergence is low this is nearly free, and the day it stops being nearly free is itself the signal you were waiting for.

### Engine-risk assessment checklist

Run this for *any* engine (or fork) before committing a product to it; capstone architecture docs must include a short version ([00-CAPSTONE.md](../00-CAPSTONE.md), LO-12):

- [ ] **License:** OSI-approved? Any dual-licensing or trademark constraints on shipping?
- [ ] **Governance:** who can change direction — a foundation, a company, one person? Is there a public decision process?
- [ ] **Funding:** what pays maintainers, and how concentrated is it (single sponsor risk)?
- [ ] **Release engineering:** cadence kept over the last 3 years? Security/maintenance releases for old branches?
- [ ] **Bus factor:** how many people hold release keys, infrastructure, and critical subsystem knowledge?
- [ ] **Fork viability:** if you *had* to fork or switch, does the build reproduce from public sources (templates, toolchain, docs)?
- [ ] **Ecosystem health:** are your critical plugins maintained? By whom? With tests?
- [ ] **Community temperature:** is conflict handled with process or with moderation improvisation?
- [ ] **Your exit cost:** measured in weeks, what would migrating this specific project cost today? Re-estimate at each milestone.

## 9. Discussion questions

1. The September 27 post, the mass blocking, and the Foundation statement are three distinct decision points. At which one was the fork made inevitable, if any — and what alternative action at that point would have changed the outcome?
2. Should an open-source project's official social account express positions on cultural controversies at all? Defend both answers with reference to stakeholder exposure (§6).
3. Redot chose close upstream tracking. What does that strategy optimize for, what does it make impossible, and when should a fork deliberately diverge?
4. The verified donation figures contradicted the loudest contemporary narrative. Design a dashboard of 5 metrics a foundation should publish so that the *next* controversy can be evaluated on evidence within days.
5. Your studio is 8 months into a Godot 4.5 product on the day an episode like this begins. Using the checklist in §8, write the one-page memo you'd send to leadership within 48 hours.
6. Compare this episode to the Unity 2023 runtime-fee controversy: which risks are shared, and which are specific to the open-source governance model?
7. The MIT license made Redot legal; trademark law made renaming mandatory. Is a strong project trademark good or bad for *users'* fork insurance?
8. "Most users stayed." Is that evidence the governance worked, that switching costs dominate, or both? What experiment or data would distinguish these?

## 10. Sources

Graded: **P** primary · **S** secondary press · **T** tertiary/community (verify before reuse). Full annotations in [00-BIBLIOGRAPHY.md](../00-BIBLIOGRAPHY.md) §6.

**Method note.** Dates and figures in this file were cross-checked on 2026-07-27: every date in the timeline traces to at least one P or S source; figures available only from T sources (post text, engagement counts, donation deltas) are attributed as such in the body and should not be re-cited as established fact without independent confirmation.

- **[P]** Software Freedom Conservancy — "Announcing Godot's Graduation from SFC!" (2022-11-01). https://sfconservancy.org/news/2022/nov/01/godot-graduates/
- **[P]** Godot Foundation — site, Annual Report 2023. https://godot.foundation/
- **[P]** Godot Foundation update, December 2024. https://godotengine.org/article/godot-foundation-update-dec-2024/
- **[P]** W4 Games — seed announcement ($8.5M, 2022). https://www.w4games.com/blog/w4-games-news-1/w4-games-raises-8-5-million-to-support-godot-engine-growth-25
- **[P]** W4 Games — Series A announcement ($15M, 2023). https://www.w4games.com/blog/w4-games-news-1/w4-games-raises-15m-to-drive-video-game-development-inflection-with-godot-engine-6
- **[S]** Game Developer — "W4 Games nets $15 million to help Godot scale 'exponentially'" (2023-12-12). https://www.gamedeveloper.com/production/w4-games-nets-15-million-to-help-godot-scale-exponentially
- **[S]** GamingOnLinux — W4 seed coverage (2022-09). https://www.gamingonlinux.com/2022/09/w4-games-raised-8-5-million-usd-to-support-godot-engine/
- **[T]** Know Your Meme — "Godot Engine User Blocking Controversy / #Wokot" (event page; archived post text, dates, engagement and donation figures). https://knowyourmeme.com/memes/events/godot-engine-user-blocking-controversy-wokot
- **[S]** It's FOSS News — "Godot Engine Fiasco Leads To Many New Forks" (2024-10). https://news.itsfoss.com/godot-engine-fiasco/
- **[S]** Hacker News — "Redot Engine: A Fork of the Godot Engine" (2024). https://news.ycombinator.com/item?id=41698094
- **[P]** Redot Engine — "Redot Engine 4.3 is now stable" (2024-12-18). https://www.redotengine.org/blog/release-4-3-stable
- **[P]** Redot Engine — GitHub releases (Redot 4.4 stable 2026-01-31; LTS 26.x). https://github.com/Redot-Engine/redot-engine/releases
- **[P]** Godot — release notes 4.3 / 4.4 / 4.5. https://godotengine.org/releases/4.3/ · https://godotengine.org/releases/4.4/ · https://godotengine.org/releases/4.5/
- **[T]** Lunduke — "Interview: Redot, 1.5 Years After Forking from Godot" (2026). https://lunduke.substack.com/p/interview-redot-15-years-after-forking

## Cross-links

- Module 01 — [../GODOT_ENGINE_STUDY.md](../GODOT_ENGINE_STUDY.md): engine architecture and licensing foundations.
- Module 11 — [../BUILD_AND_EXPORT.md](../BUILD_AND_EXPORT.md): export-pipeline portability (the practical hedge discussed in §8).
- [../00-CAPSTONE.md](../00-CAPSTONE.md): LO-12 requires an engine-risk note in your architecture document, using §8's checklist.
- [../00-BIBLIOGRAPHY.md](../00-BIBLIOGRAPHY.md): annotated versions of every source above.
