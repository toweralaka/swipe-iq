# Swipe-IQ: JAMB Biology MVP — Approved Implementation Plan

Status: Approved by the project owner on 2026-10-12 (Africa/Lagos).
This document preserves the approved revised plan. Execution is authorized one milestone at a time; approval of the plan is not approval to implement every milestone.

## 1. Problem and target audience

Audience: Nigerian candidates preparing for JAMB UTME Biology, initially recruited into an invited Android pilot.

Problem hypothesis: Candidates may struggle to sustain revision using conventional materials. Humorous, syllabus-aligned explanations across text, images, audio, and video may encourage revision; quizzes can reveal whether learning follows engagement.

Solution: An educational feed with reviewed AI-assisted content, quizzes, personal progress, likes, and asynchronous challenges.

JAMB provides an official Biology syllabus through IBASS. Map each learning unit to its objectives and record the reference used. Syllabus availability does not imply complete MVP coverage.
Reference: https://ibass.jamb.gov.ng/assets/uploads/Biology.pdf

### Assumptions to validate

- Candidates are accessible and willing to participate.
- They have usable email accounts and can receive login links.
- Humour and media formats improve engagement without distracting from learning.
- Lightweight media works on participants' devices and connections.
- Engagement translates into retained knowledge.
- Recruitment does not depend on an SS1 classroom. Confirm ages and participation arrangements rather than assuming all candidates are adults or that permission could never apply.

Proposed pilot: 10–15 invited candidates over one week.

| Indicator | Measurement and initial goal |
| --- | --- |
| Usability | At least 80% complete login → learning unit → quiz without help. |
| Engagement | At least 60% of started units reach quiz completion. |
| Return use | At least 50% return on another day. |
| Expressed interest | Unique likes / unique content viewers, by topic and media type. |
| Learning | Equivalent baseline and delayed questions 48–72 hours apart; report changes and participant counts. |
| Connectivity | Record failed loads; test text access under slow/interrupted connections. |
| Editorial effort | Record drafting, media preparation, and review time per unit. |

Thresholds guide investigation, not promised outcomes. Likes express interest, not proof of learning. Small pilot results must not be presented as causal proof or guaranteed exam improvement.

## 2. MVP scope and acceptance criteria

Confirmed: text, images, audio, and video are included now; data saver and caching are included; downloadable offline lessons are deferred; login is invitation-only.

Start with six learning units across three syllabus-aligned topics, covering all four media types across the collection. Each unit has one learning objective, up to three feed items, and three four-choice questions.

| Feature | Acceptance criteria |
| --- | --- |
| Email login links | An invited candidate requests a link, opens it on Android, and signs in without a password. Expired, used, and invalid links offer recovery. Non-invited addresses cannot register. |
| Topic-based feed | Candidates choose Biology topics and browse published content. Drafts remain inaccessible. Loading, empty, error, retry, and end states work. |
| Text and images | Text loads independently of optional media. Images are compressed, have alternative descriptions, and load on request in data saver mode. |
| Audio | User-initiated playback; duration and download size shown; transcript supplies the educational explanation without playback. |
| Video | User-initiated playback; lightweight version, captions, and text summary available; leaving the item stops playback. |
| AI-assisted publishing | AI drafts are manually entered; a human checks accuracy, humour, syllabus alignment, references, accessibility, and media rights before publication. |
| Quizzes | Server calculates scores; answer keys hidden before submission; results explain answers; submission retries do not create duplicates. |
| Progress | Completed units and quiz history persist across sessions; first attempts and repeat practice are distinguishable. |
| Likes | Like/unlike individual feed items; at most one active like per account/item; persisted state; failed requests do not display false success. |
| Challenges | Two candidates use a code to complete the same quiz version at different times; one scored challenge attempt each; ties supported. |
| Pilot reporting | Staff export pseudonymous engagement and quiz summaries; emails excluded from analytical exports. |

Like defaults: private candidate like state; staff aggregate counts; likes do not alter feed ranking.

Challenge defaults: seven-day expiry, no self-joining, no public leaderboard, score-only comparison. Detailed answers appear after both finish or expiry. Prior practice means these are friendly activities, not controlled assessments.

### Deferred

- Candidate uploads and creator profiles.
- Sharing, comments, messaging, follows, and public discovery.
- Live battles and algorithmic recommendations.
- Integrated AI generation and automatic publication.
- Offline quiz/like synchronization and downloadable lesson packs.
- Full syllabus coverage, full mock examinations, iOS, and app-store release.

Future candidate uploads enter a review queue before publication. Preserve authorship/media metadata now; do not build upload endpoints or moderation infrastructure prematurely.

## 3. Architecture and decisions

### Backend: Django REST Framework

| Option | Benefit | Trade-off |
| --- | --- | --- |
| Django + DRF (selected) | Integrated models, migrations, staff administration, permissions, and APIs. | More framework conventions to learn. |
| FastAPI | Type-based validation, automatic API documentation, async support. | Editorial admin, database/migration setup, and account management need separate assembly. |

Django + DRF reduces work for our review/publishing workflow. Storage infrastructure serves media; changing API framework alone does not solve slow delivery.
References: https://fastapi.tiangolo.com/features/ and https://docs.djangoproject.com/en/5.2/ref/contrib/admin/

### Components

External AI tool → manual draft entry → Django admin → reviewed publication.
Android app ↔ DRF API ↔ database; app also uses local cache and media storage/CDN; backend uses email delivery.

- React Native + Expo + TypeScript: Android screens, navigation, playback, caching, and API calls.
- Django admin: staff-only drafting, media attachment, review, publication, and withdrawal.
- DRF: authentication, content access, scoring, likes, challenges, reporting.
- SQLite locally; PostgreSQL before hosted pilot: simple initial setup, then verify deployment behavior.
- Object storage/CDN: store and deliver media outside application requests.
- Email service: login-link delivery; local email backend during development.
- REST/JSON under /api/v1/: documented frontend/backend communication.

One backend application; no microservices or background processing platform initially.

### Passwordless login

1. Candidate submits an invited email.
2. Server returns the same generic response for invited and unknown addresses.
3. Server emails a random single-use link valid for 15 minutes.
4. Link opens Android app; candidate confirms sign-in.
5. App exchanges token for a revocable session credential in SecureStore.

Store only a hash of the login token. Rate-limit by address and IP, exclude tokens from logs, and consume atomically. Opening the link must not consume it: email scanners may open links automatically.

Use verified HTTPS Android App Links for the pilot, requiring a domain and installed development/preview build. Expo Go alone is not the authentication acceptance environment. Provide an installation/help page when the app is unavailable.
Reference: https://docs.expo.dev/linking/android-app-links/

Sessions expire after 30 days and are revoked on logout. Staff administration uses separate protected staff credentials.

### Media and connectivity

Data saver enabled by default.

- Fetch text and small metadata first; never autoplay audio/video.
- Show type, duration, size, and explicit load/play controls.
- Pause playback when an item leaves the screen.
- Cache viewed text and successfully downloaded assets within 100 MB; evict least-recently-used items; provide clear-cache control.
- Label cached content offline; refresh publication status on reconnection.
- Clear account-specific cached data on logout.
- Connectivity required for login, quiz submission, likes, and challenges. Preserve selected quiz answers locally until submission succeeds.

Editorial limits: images ≤250 KB; audio ≤90 seconds/1 MB; video ≤60 seconds/5 MB and ≤480p. Staff prepare compatible files before upload. Automated transcoding and adaptive streaming are deferred.

These are pilot defaults to test, not playback guarantees. Text alternatives keep objectives accessible when media fails.

### Data and API boundaries

Core records: users/invitations, login tokens/sessions, syllabus topics/objectives, learning-unit versions, feed items, media assets, questions, attempts, likes, challenges, learning events.

- Published versions immutable; corrections create replacements.
- Attempts/challenges retain original version.
- Feed items have stable identities so likes survive revisions.
- Media metadata: type, size, duration, transcript/captions, attribution.
- Endpoints: login-link request/exchange, logout, content, attempts, progress, like/unlike, challenge lifecycle.
- Idempotent like/unlike operations and unique submission identifiers support safe retries.
- Server enforces permissions and publication visibility.

## 4. Implementation milestones

Branch rule: inspect working tree before changes. Use docs/jamb-mvp-plan for approved planning artifacts and feat/<milestone-name> for implementation. Never edit or commit on main; avoid branch switches that risk existing work. Merging or publishing requires explicit authorization.

### Milestone 0 — Record the approved baseline

- Objective: establish shared specifications and working agreements.
- Prerequisite: approval of this replacement plan.
- Tasks/files: requirements, architecture, milestones, decision log, AGENTS.md on separate branch; identify reviewer and syllabus reference.
- Verification/completion: scope, acceptance criteria, branch policy, dependencies documented and reviewed.

### Milestone 1 — Reproducible foundation

- Objective: runnable backend/mobile foundation.
- Prerequisite: M0.
- Tasks/files: inspect tools; choose compatible versions; scaffold backend/mobile; health endpoint; environment examples; dependency locks; setup instructions; CI configuration.
- Verification/completion: backend checks pass; Android opens and reaches API; setup reproducible.

### Milestone 2 — Editorial content and media

- Objective: reviewable multimedia learning units.
- Prerequisites: M1 and one sample objective.
- Tasks/files: models, migrations, admin review controls, drafting prompt, media preparation guide, demo seed command.
- Verification/completion: drafts hidden; review and valid assets required to publish; approved samples for all four formats.

### Milestone 3 — Email login and student API

- Objective: invited passwordless access and student content API.
- Prerequisites: M2; domain/email configuration for real-device acceptance.
- Tasks/files: invitations, token exchange, sessions, permissions, App Links, login screen, API docs, auth tests.
- Verification/completion: email → installed app → authenticated request works; expired/reused tokens and unknown emails behave correctly.

### Milestone 4 — Feed, playback, and caching

- Objective: usable feed under constrained connectivity.
- Prerequisite: M3.
- Tasks/files: topic/feed screens, media components, text alternatives, cache service, data saver controls, failure states.
- Verification/completion: all formats work on Android; no autoplay; slow/offline checks pass; bounded cache clears on logout.

### Milestone 5 — Quizzes and progress

- Objective: verified learning loop.
- Prerequisite: M4.
- Tasks/files: scoring/submission APIs, result/progress screens, saved answer state, meaningful tests.
- Verification/completion: correct scoring, hidden keys, retry safety, private history, session persistence demonstrated.

### Milestone 6 — Likes and engagement evidence

- Objective: capture expressed interest and basic engagement.
- Prerequisite: M5.
- Tasks/files: like/unlike API/UI, unique constraints, event recording, aggregate export.
- Verification/completion: repeated taps/retries cannot inflate likes; errors restore correct state; exports exclude emails.

### Milestone 7 — Asynchronous challenges

- Objective: two-candidate friendly competition.
- Prerequisite: M6.
- Tasks/files: models/endpoints/screens, expiry rules, result visibility, concurrency tests.
- Verification/completion: same-version quiz; self-join, third participant, duplicates, ties, expiry handled correctly.

### Milestone 8 — Hosted pilot readiness

- Objective: deploy and prepare evaluation.
- Prerequisites: M7 and six reviewed units.
- Tasks/files: PostgreSQL, media storage, HTTPS, email delivery, Android build, backups, deployment guide, pilot protocol.
- Verification/completion: two-device end-to-end checks; backup restoration; understood delivery costs and participation arrangements.

### Milestone 9 — Evaluate and demonstrate

- Objective: honest evidence and reusable handover.
- Prerequisite: completed pilot.
- Tasks/files: analyze engagement/delayed checks; fix priority defects; handover, learning log, demo script.
- Verification/completion: another developer follows setup; evidence accurately labelled; 3–5 minute demo.

Every milestone gets a short plan, owner approval, implementation, verification, and learning note. Split further if changes become difficult to review.

## 5. Testing and quality

- Backend: publication, permissions, login expiry/reuse, scoring, duplicates, likes, challenge transitions.
- Mobile: login recovery, data saver, loading/errors, likes, submissions, playback.
- Real Android: email links with app closed/open, slow connections, interrupted media, larger fonts, cache.
- Integration: PostgreSQL before hosting; real email delivery and storage.
- CI: backend checks/tests, TypeScript, frontend tests, linting.
- Editorial: Biology accuracy, syllabus mapping, humour, accessibility, references, media rights; tests cannot establish educational quality.

Done: acceptance criteria demonstrated, relevant checks pass, critical findings resolved, documentation updated, important code explained plainly.

## 6. Codex workflow and reusable artifacts

Proposed structure:

    README.md                 Purpose and setup/run/test commands
    AGENTS.md                 Durable guidance and branch rule
    backend/                  Django apps, migrations, API, tests
    mobile/                   Screens, playback, cache, API client, tests
    docs/implementation-plan.md  This approved plan
    docs/requirements.md      Features and acceptance criteria
    docs/architecture.md      Components, data flow, API boundaries
    docs/milestones.md        Progress, prerequisites, verification
    docs/decisions/           Choices, alternatives, reasons
    docs/content/             AI prompt, review/media standards
    docs/workflow/            Task/review templates, learning log
    docs/pilot/               Protocol, evidence, demo script
    .agents/skills/           Proven workflows, introduced gradually
    .github/workflows/        Automated checks

Codex cycle: inspect → plan → discuss → approve one milestone → implement on feature branch → test → review diff → document → verified checkpoint.

AGENTS.md requires branch verification before edits, secret protection, verified commands, and milestone approval boundaries. Skills capture repeated proven workflows; no custom MCP initially. Add integrations for concrete needs such as GitHub issue/PR management or official docs. The workflow must remain usable without them.
Reference: https://learn.chatgpt.com/guides/best-practices

Existing wip notes are ignored working context, not authoritative shared documentation. Approved docs live in docs/.

## 7. Risks and dependencies

| Risk | Response |
| --- | --- |
| Media increases scope/cost | Short manually prepared files, fixed limits, no automatic transcoding. |
| Email delays block access | Early delivery test; resend/recovery; monitor without secrets. |
| AI misconceptions | Review each item/question; independently verify references. |
| Likes reward entertainment alone | Compare with completion and delayed learning. |
| Cache becomes outdated | Version assets; refresh status online; label offline; bound retention. |
| Recruitment assumptions fail | Confirm access, ages, email availability, willingness. |

Before relevant milestones: identify reviewer, three syllabus topics, pilot organizer, email service/domain, hosting budget. Provider selection belongs in milestone planning; no purchase/configuration is authorized by this plan alone.

## 8. Four-minute demonstration

| Time | Demonstration |
| --- | --- |
| 0:00–0:30 | Audience, revision hypothesis, syllabus mapping. |
| 0:30–1:00 | AI draft, reviewer correction, publication. |
| 1:00–2:00 | Passwordless login, multimedia feed, data saver, transcript, like. |
| 2:00–2:45 | Quiz explanation, progress, prepared two-account challenge. |
| 2:45–3:15 | Feature branch, Codex plan, reviewed change, passing tests. |
| 3:15–4:00 | Actual findings/limitations; future uploads, sharing, wider coverage. |

Use clearly labelled sample data if evaluation has not occurred; do not invent impact evidence.

## Examination scope refinement — 2026-10-12

Owner requested examination-aware models: JAMB is the MVP examination, with others such as SSCE reserved for future releases. This explicitly refines the existing topic-based feed and M2 content hierarchy; it does not authorize additional milestones or examinations in the MVP.

- Examination → Subject → Topic → Learning unit version. Biology is unique per examination, not globally.
- Existing subjects/content migrate to JAMB, preserving record identities, text, questions, publication status, and review history.
- Admin identifies each subject/topic's examination and supports examination filtering. Published/withdrawn content cannot be reassigned to another examination through subject/topic saves.
- JAMB is initially active. Other examination records default to inactive; no SSCE lessons are seeded.
- M3 student APIs must expose examination identity and restrict availability to active examinations and published content. M4 selection must clearly identify JAMB Biology. These student features remain unimplemented.

Acceptance for this model increment: JAMB Biology and SSCE Biology can coexist; duplicate Biology within one examination is rejected; every subject requires an examination; existing lessons retain their data under JAMB; seed commands target JAMB; tests verify migration, filtering, and history protection. Future examinations require their own reviewed syllabus/content before activation.
