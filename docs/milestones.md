# Milestone status and prerequisites

Authority: [Approved plan](implementation-plan.md), section 4. Dates use Africa/Lagos.

| Milestone | Status |
| --- | --- |
| 0 — Approved baseline | Documentation prepared; see evidence below. Reviewer/topic dependencies remain open. |
| 1 — Foundation | Implemented on feat/foundation; desktop checks passed; owner confirmed phone connection. |
| 2–9 | Not started; separately authorized in sequence. |

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
