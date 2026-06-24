## Plan: Rayyan Full JSON Revamp

Deliver a full product revamp that keeps your core Quran learning logic, simplifies daily use for kids, adds powerful parent controls, and persists all data to structured JSON files with multi-profile support. The implementation should be phased so learning data is never lost and each phase can be verified independently.

**Steps**
1. Phase 1: Foundation and safety baseline.
2. Freeze current behavior by documenting existing XP, streak, memorization, revision, achievement, and reward rules from the current app so refactor parity is measurable.
3. Introduce a modular package structure (config, models, persistence, services/business, ui/pages, utilities) while keeping app startup in a thin entry file. *Blocks all later phases.*
4. Add centralized configuration for app constants and Surah metadata so business rules are not embedded in UI functions. *Depends on 3.*
5. Phase 2: JSON-first persistence and profile architecture.
6. Implement file-based storage using a data folder with multiple JSON files (profiles index, per-child progress, rewards catalog, app settings, backups metadata). *Depends on 3; parallel with 4 after interfaces are set.*
7. Implement safe read/write layer with atomic writes, schema versioning, and corruption fallback to latest backup. *Depends on 6.*
8. Build multi-profile manager (create, switch, archive child profiles) and connect active profile to all progress actions. *Depends on 6.*
9. Add migration path from current in-memory/session export format into the new JSON schema so no existing data is lost. *Depends on 6 and 7.*
10. Phase 3: Core domain extraction (logic parity first).
11. Move existing business logic into reusable service modules: XP/level engine, streak engine, memorization tracker, revision scheduler, achievements evaluator, reward unlock evaluator. *Depends on 3 and 4; parallel sub-steps possible.*
12. Add domain-level tests for parity with current behavior before introducing new game mechanics. *Depends on 11.*
13. Keep optional advanced scheduling hooks for future spaced repetition, but default to current predictable revision behavior until explicitly enabled. *Depends on 11.*
14. Phase 4: Kid-first UX revamp (stunning but simple).
15. Redesign dashboard into a motivational daily mission view: big progress hero, today goals, streak flame, next reward preview, and one-tap “start now” actions. *Depends on 11 and 12.*
16. Introduce lightweight animation and celebratory moments only at milestones (level up, streak save, surah completion) to avoid visual clutter. *Depends on 15.*
17. Surface “What next?” recommendations generated from due revision + nearest completion opportunities so child always has a clear next action. *Depends on 11 and 15.*
18. Phase 5: Memorization and Revision simplification.
19. Rebuild memorization page to a compact surah-first flow with multi-select ayah chips and batch actions (mark memorized, unmark, quick ranges). *Depends on 11 and 15.*
20. Rebuild revision page similarly with batch multi-select marking and due/locked visual grouping so child can complete revision quickly. *Depends on 11 and 15.*
21. Preserve all existing tracking fields while simplifying interaction density and reducing forms/buttons per screen. *Depends on 19 and 20.*
22. Phase 6: Rewards and parent controls expansion.
23. Build rewards catalog manager for parents with add-one and bulk-add flows (text list and JSON import), supporting manual, XP-cost, and level-unlock rewards in one model. *Depends on 6, 8, and 11.*
24. Add reward lifecycle states (locked, unlocked, claimed, redeemed) and parent approval settings for redemption. *Depends on 23.*
25. Add parent dashboard for weekly summaries, goal setting, consistency trends, and focused intervention hints (e.g., revision backlog rising). *Depends on 11 and 8; parallel with 23.*
26. Phase 7: Daily engagement mechanics (non-bulky gamification).
27. Add daily quests with small XP bonuses tied to learning actions (memorize x ayahs, revise y ayahs, finish one surah section). *Depends on 11 and 15.*
28. Add badge milestones and celebration timeline that highlights effort consistency, not only total points. *Depends on 27.*
29. Add adaptive praise messages from recent activity context to keep emotional motivation high with minimal UI noise. *Depends on 15 and 27.*
30. Phase 8: Verification, hardening, and rollout.
31. Run migration tests on sample old data and verify parity metrics before/after migration per profile. *Depends on 9 and 12.*
32. Execute full manual UX pass on child flows (dashboard, memorization, revision) to ensure fewer clicks and clearer progression cues. *Depends on 15 through 21.*
33. Execute parent flow tests (bulk rewards, profile switch, backups, restore) and verify JSON integrity after each operation. *Depends on 23 through 25 and 31.*
34. Release in two stages: parity release first, feature-rich release second to reduce risk. *Depends on all prior phases.*

**Relevant files**
- c:/Users/mparakkottm2/PycharmProjects/rayyan/app.py — source of current logic to extract into modules and keep behavior-compatible.
- c:/Users/mparakkottm2/PycharmProjects/rayyan/requirements.txt — dependencies update point after modular split and testing tooling additions.
- c:/Users/mparakkottm2/PycharmProjects/rayyan/plan.md — prior UI-only plan reference; superseded by full revamp scope.
- c:/Users/mparakkottm2/PycharmProjects/rayyan/GUI-plan.md — prior polish plan reference; retain only relevant UX ideas.

**Verification**
1. Functional parity checks: same inputs produce same XP, streak, revision eligibility, and achievement outcomes before and after refactor.
2. Persistence checks: refresh/restart app and confirm all profiles and progress survive with no manual export step.
3. Multi-profile checks: switching children never leaks or overwrites another child’s progress.
4. Batch action checks: marking multiple ayahs memorized/revised updates all selected ayahs correctly in one action.
5. Rewards checks: parent add-one, bulk add, XP-cost unlock, level unlock, claim, and redeem flows all persist correctly.
6. Recovery checks: simulate bad JSON/corrupt file and confirm backup restore path works.
7. UX checks: child can complete a daily learning loop from dashboard in minimal steps without crowded screens.

**Decisions**
- Confirmed: multi-profile support in initial revamp.
- Confirmed: persistence as a folder of multiple JSON files, not SQLite.
- Confirmed: rewards model includes manual rewards, XP-cost rewards, level-unlock rewards, plus bulk import.
- Included scope: full architecture split, UI redesign, new parent and gamification features, migration and backups.
- Excluded scope: cloud sync and mobile native app conversion in this revamp iteration.

**Further Considerations**
1. Profile identity strategy: Option A child nickname only, Option B nickname plus avatar code, Option C stable generated profile IDs (recommended for safer JSON linking).
2. Reward bulk format defaults: Option A newline text list, Option B CSV, Option C both text and JSON import (recommended).
3. Advanced revision mode rollout: Option A keep fixed current logic only, Option B optional smart mode toggle (recommended), Option C replace immediately with smart scheduler.