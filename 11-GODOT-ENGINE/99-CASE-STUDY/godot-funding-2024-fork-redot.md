# Case Study — Godot Funding Crisis 2024 and the Redot Fork

> **Type:** governance/community case study
> **Last updated:** 2026-04-27 (historical synthesis)

## Timeline

### Pre-2024: Godot Foundation growth

Godot Engine grew from a niche open-source project to a serious Unity/Unreal alternative through 2020-2023. Donations to the Godot Foundation (Patreon, sponsorships) supported core developers full-time.

### 2024 Q3: governance friction

Internal tensions within the Godot Foundation (community communication, leadership perceived as insufficiently transparent, Twitter/X handling of political discussions) caused community pushback. Some core contributors left. Donations dropped.

### 2024 Q4: Redot announced

A community-led fork called **Redot** was announced as a "more pragmatic, community-driven" Godot continuation. Some moderators and contributors moved to Redot.

### 2025: stabilization

Both Godot Foundation and Redot continue to exist. Most users stay with mainline Godot, but Redot maintains a slowly growing user base. The ecosystem effectively splits into two channels.

## Lessons for projects choosing Godot

1. **Open-source forking is a feature, not a bug.** When a community disagrees, fork is the safety valve.
2. **Lock-in concerns are NOT eliminated by open-source.** They are reduced. You can still face: incompatible API drift, plugin abandonment, support fragmentation.
3. **Track the Godot Foundation governance and Redot trajectory.** For commercial projects, evaluate fork health quarterly.
4. **Save migration plan: be Godot-version-portable.** Don't rely on undocumented internals; if Godot 4.6 → 5.0 breaks, you want ability to evaluate Redot or stay.
5. **Asset pipeline portability.** GDScript ports between forks easily; C# bindings might not. Plan accordingly.

## Recommendations

- **Stay with mainline Godot** for new projects unless you have specific reason to choose Redot.
- **Pin engine version for production.** Godot 4.5 LTS is the safe choice.
- **Have export script that works with both forks** if hedging.

## References

- Godot Foundation. https://godot.foundation/
- Redot Engine. (community fork; check community for latest URL).
- Hacker News + Reddit threads from 2024 Q3-Q4 on the topic.

## Cross-links

- Module 01 — `../GODOT_ENGINE_STUDY.md`.
- Module 11 — `../BUILD_AND_EXPORT.md`: export pipeline portability.
