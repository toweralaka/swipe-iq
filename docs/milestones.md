# Milestone status and prerequisites

Authority: [Approved plan](implementation-plan.md), section 4. Dates use Africa/Lagos.

| Milestone | Status |
| --- | --- |
| 0 — Approved baseline | Documentation prepared; see evidence below. Reviewer/topic dependencies remain open. |
| 1 — Foundation | Implemented on feat/foundation; desktop checks passed; owner confirmed phone connection. |
| 2 — Editorial content and media | Implementation and automated checks complete on feat/editorial-content; human content/media acceptance pending. |
| 3 — Email login and student API | Implemented on feat/student-access; desktop checks passed; external configuration and installed-phone acceptance pending. |
| 4–9 | Not started; separately authorized in sequence. |

## Milestone 0 evidence — 2026-10-12

- Approved plan saved with scope, choices, acceptance criteria, milestones, testing, workflow, risks, demo.
- Requirements/architecture references, accepted decision record, AGENTS.md, review template, and learning log created.
- Work isolated on docs/jamb-mvp-plan; existing README.md and .gitignore preserved.
- Official syllabus source identified: https://ibass.jamb.gov.ng/assets/uploads/Biology.pdf (not a claim of verified edition/topic mapping).
- Reviewer: unconfirmed; owner must nominate before editorial approval.
- Initial three topics and pilot organizer: unconfirmed.
- No application scaffold, dependency installation, or application tests created.

## Milestone 1 objective

Make a reproducible backend/mobile foundation: health API, Android screen reaching it, setup instructions, dependency locks, and automated checks. No login, media, quizzes, or challenges yet.

### Prerequisites and current evidence

- Owner approved M1 and physical Android route.
- Use feat/foundation; inspect working tree before switching and preserve existing work.
- Documentation from M0 exists. Reviewer/topic confirmations remain open for content milestones; they do not technically block foundation work. Record explicit deferral when starting M1.
- Last environment inspection: Git 2.55.0.windows.3, Python via python 3.14.6, Node v24.19.0, npm 11.17.0. Recheck before selecting dependencies; compatibility not yet established.
- py launcher did not find Python; use verified python path. adb/Java not found on PATH; emulator availability not established.
- Device choice: physical Android + Expo Go approved for M1; installed development/preview build needed for M3.
- Verify phone-to-computer networking. Phone localhost does not refer to the development computer.
- Shell execution helper previously failed; a read-only Node runner established tool availability. Recheck command execution before dependency installation.

### Expected creation/configuration

backend/ scaffold and isolated Python environment; mobile/ Expo/TypeScript scaffold; health endpoint/client; placeholder environment examples; expanded ignore rules; pinned/locked dependencies; CI checks; verified setup/run/test guide.

### Exit evidence

Backend checks/tests pass; mobile type checks pass; Android reaches health endpoint; documented clean setup is reproducible; no secrets tracked. Report actual command results, distinguish unrun device checks, and stop for approval before M2.

## Dependency register

| Dependency | Resolver | Required before |
| --- | --- | --- |
| Content reviewer and initial topics | Project owner | M2 approved content |
| Android device route/access | Project owner with Codex setup inspection | M1 device acceptance |
| Compatible runtime/dependency versions | Codex verifies official compatibility | M1 installation |
| Domain and email service/budget | Owner selects after concrete options | M3 real-device login |
| Pilot organizer/ages/participation | Project owner | Recruitment/M8 |
| Hosting/media storage budget/providers | Owner selects after concrete options | M8 deployment |

## Documentation verification — 2026-10-12

Passed: all local Markdown links resolve; approved acceptance table and all ten milestones present; documentation whitespace checks; Git diff whitespace check for tracked changes; README/.gitignore preserved byte-for-byte; branch is docs/jamb-mvp-plan; no backend/mobile scaffold. No application tests exist or were run. No files staged, committed, pushed, or deployed.

## Milestone 1 implementation evidence

- Branch: feat/foundation; no commits, push, merge, or deployment. Existing planning documents carried forward without discarding user work.
- Backend: Django 5.2.18, DRF 3.17.2, Python 3.14.6; isolated environment and pinned requirements; SQLite migrations applied locally.
- Mobile: Expo 57.0.27, React Native 0.86.3, React 19.2.3; Node 24.19.0; npm lockfile.
- Implemented public GET /api/v1/health/ and Android connection screen with loading/error/retry and 10-second timeout.
- Added placeholder environment examples, generated-file ignores, setup guide, and GitHub Actions checks.
- Passed: Django system check; migration drift check; pip dependency check; two backend tests; live HTTP GET 200/POST 405; TypeScript; ESLint; five mobile API client tests; Expo dependency alignment; Android bundle export.
- npm audit fix applied compatible updates; 22 advisories remain (7 moderate, 15 high), involving transitive Expo/Metro/node-forge/xcode dependencies. npm suggests breaking Expo/React Native downgrades; these were not applied. Keep development servers on trusted private networks and re-evaluate advisories before pilot hosting. Audit is not clean; do not claim otherwise.
- Owner confirmed physical-phone connection in this session. Phone model/version, failure/recovery and larger-text checks were not individually reported; do not infer them. Clean setup by another developer remains unverified.
- Remote GitHub Actions has not run. Local bundle success does not establish physical-phone success.
- Reviewer/topic confirmation explicitly deferred to M2; organizer/recruitment remain pilot dependencies.
- Phone connection confirmed by owner. Commit/PR authorized; M2 still requires separate approval.

### Final foundation verification

Clean npm ci succeeded from package-lock.json. TypeScript, ESLint, and all five mobile client tests passed again after reinstall. Local documentation links resolve; source whitespace checks pass; generated environments/database/dependencies/bundles are ignored; environment examples remain trackable. Non-failing warnings: ESLint 9 deprecation from Expo-compatible tooling and Node module auto-detection during API tests. The dependency audit remains unresolved as recorded above.

### Owner acceptance

Owner reports: “phone connection has been verified”. Recorded as user-reported evidence, not a new agent-run device check. Commit and PR creation authorized; no merge authorization.

## Milestone 2 implementation evidence

- Owner authorized M2; branch feat/editorial-content starts from the committed foundation. No merge, commit, push, or PR requested for this milestone.
- Implemented subjects/topics, stable learning units, immutable version history, ordered cards, four-choice questions, and private media assets with authorship/attribution.
- Staff admin provides draft editing, private media preview, explicit permission-checked publish/withdraw actions, and replacement drafts with reset review confirmations and retained card identities.
- Publication checks all six human-review confirmations, saved references/review notes, 1–3 cards, exactly three questions, and media validation/confirmation. Published history cannot be edited or bulk-deleted through supported application paths.
- Added initial migration and applied it locally. Added repeatable seed_demo command; two runs created then preserved two unreviewed sample units (five cards, six questions). No sample was published, no media fabricated, no credentials created.
- Added drafting prompt, human review checklist, editorial walkthrough, and media preparation guide under docs/content/.
- Passed: 22 backend tests including existing health tests, admin action success/failure, permissions, missing files, publication freezing/replacements, supported format attachment, constraints and repeatable seeding. Django system check and migration drift check pass.
- Media limits: actual size/basic extension/signature validated; declared duration/height and actual playback/caption timing are human-verified, not measured by a decoder. This is documented; metadata confirmation cannot substitute for a real review.
- Human acceptance OPEN: reviewer nomination, confirmation of sample objective/JAMB mapping, real permitted image/audio/video samples, and recorded approval across all four formats. Provisional cell-comparison drafts are not approved teaching material.
- No student API, mobile playback, AI integration, or later-milestone features added. No mobile changes; backend checks are the relevant automated scope.
- Do not mark M2 fully accepted or advance to M3 until human review evidence and owner approval are provided.

Final M2 documentation checks passed: local Markdown links, tracked whitespace, Django system check, migration drift, and private upload/environment ignore rules. Admin upload round-trip test also passed; no real media or secrets were committed.

### Official syllabus mapping

Owner selected the official JAMB Biology syllabus. Seed defaults now map to Section A / topic 1(b) / objective iv (plant/animal cell comparison); see content/syllabus-source.md for provenance and retrieval limitations. Added safe opt-in alignment for untouched legacy seed metadata, preserving editor changes and publication history. All 25 backend tests pass; no migration drift. Content and media still require human review; no publication occurred.

### Five humorous sample units

Owner requested five Biology sample contents. Added seed_sample_content and original text/quiz data covering membrane, wall, chloroplast, mitochondria, and nucleus within the existing cell-structure syllabus topic. Seeded five additional unreviewed drafts locally (15 cards, 15 questions); rerun preserved them. All 27 backend tests pass, including review gating and non-overwrite checks. No publication, media generation, commit, or push. These are candidate sample material, not a change to pilot unit/topic limits.

### Examination-aware content refinement

Owner authorized examination-aware models while retaining JAMB as the only MVP exam. Added Examination and a required Subject relationship, uniqueness per examination, admin labels/filters, JAMB-specific seeds, and protections against reassigning published/withdrawn subjects/topics. Other exams default to inactive; no SSCE data was seeded.

Migration 0002 applied locally. Compared every pre-existing editorial table row using its original columns before/after: all preserved, including lesson identities and publication/review data; existing subjects assigned to JAMB. Passed 34 backend tests, including old-schema migration, exam separation, required/unique relationships, protected deletion, publication history, seed scope, and admin labels. Django system check and migration drift check pass.

Updated approved-plan addendum, requirements, architecture, README, editorial instructions, and learning log. No mobile changes, student selector/API, commit, push, or later milestone implementation. M2 human acceptance remains open as recorded above.

## Milestone 3 — Email login and student API

Owner requested the next milestone after committing M2. Work is isolated on feat/student-access, based on the existing M2 commit; the owner's unfinished AGENTS.md edit is preserved. This authorizes M3 code work, not a claim that M2 human content/media acceptance is complete. M4 is not started.

Objective: invited candidates request a short-lived email link, explicitly confirm sign-in in the phone app, and receive revocable access to published content. The phone lesson feed remains M4.

Implemented:

- Invitation admin; random 15-minute login tokens stored only as hashes; conditional single-use exchange; unusable candidate passwords; hashed 30-day sessions; logout, expiry, and immediate invitation/account deactivation checks.
- Database fixed-window address/IP throttling, generic invited/unknown responses, no token in API URLs, and safe generic delivery-error logging. Development email uses an ignored private file outbox.
- Read-only paginated examinations/subjects/topics/units and authenticated media. Active exams and latest published versions only; no draft files, questions, answer keys, or staff review metadata.
- Expo Router home/confirmation/connection routes, SecureStore session lifecycle, explicit confirmation, recovery messages, and a development-only local-link paste path. No sign-out success is reported when server revocation fails offline.
- Android App Links intent configuration gated by an actual hostname, configurable association endpoint, static installation/help fallback, and EAS development/preview profiles. No domain/provider/account provisioning, email send to a real candidate, cloud build, or deployment performed.
- Local accounts migration applied without altering editorial content. Environment examples, API contract, device guide, README, architecture/decision record, and learning log updated.

Verification:

- All 53 backend tests pass (34 existing plus 19 access/content scenarios). Django system check and migration drift check pass.
- All 14 mobile tests pass, including restored/expired sessions, offline logout, storage-failure cleanup, untrusted links, and normal launch. TypeScript and ESLint pass.
- Expo dependency alignment passes after updating within SDK 57 to Expo 57.0.28 and aligning React DOM/animation peers. Final Android bundle export passes.
- npm reports 28 dependency advisories (10 moderate, 18 high). They remain unresolved; no forced SDK downgrade or clean-audit claim. Node module auto-detection warning is non-failing. Physical Android behavior is not inferred from bundle/tests.

Acceptance still pending:

- Owner-selected domain/email service and sender configuration; HTTPS API reachable from phone; signing certificate and matching association document; installed development/preview build.
- Real email → installed app, cold/warm App Links, persisted sign-in, recovery/logout, and help-page acceptance on the phone, recorded using [authentication setup](authentication-setup.md).
- M2 reviewer approval and real permitted multimedia sample acceptance remain open. No content was auto-published.

Next owner action: follow the local-outbox walkthrough for a reversible login check, then provide domain/email choices and record the installed-phone checks. Stop before M4 until owner approval. No commit, push, merge, or deployment authorized by this implementation request.

Final M3 desktop checkpoint: clean npm ci succeeded from the updated lockfile; TypeScript, ESLint, all 14 mobile helper/lifecycle tests, and Android export passed again after that clean install. Local documentation links (28 checked), source whitespace, secret-pattern checks, and private outbox/environment/database/build exclusions pass. No real-device or remote CI result is inferred.
