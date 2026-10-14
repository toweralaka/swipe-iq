# Swipe-IQ: JAMB Biology MVP — Approved Implementation Plan

Status: Baseline approved on 2026-10-12; admin AI-generation revision approved on 2026-10-13 (Africa/Lagos).
AI-1 implementation was authorized on 2026-10-13. Its code and desktop checks are complete; controlled live generation, human review, and phone acceptance remain pending. AI-2 and AI-3 are not started and require separate approval. Manual drafting remains available; publication permits zero or exactly three reviewed questions.
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
| Usability | At least 80% complete login → subject selection → feed without help; assess optional dare usability separately. |
| Engagement | Measure enjoyment and voluntary dare acceptance; quiz completion is not required to use the feed. |
| Return use | At least 50% return on another day. |
| Expressed interest | Unique likes / unique content viewers, by topic and media type. |
| Learning | Equivalent baseline and delayed questions 48–72 hours apart; report changes and participant counts. |
| Connectivity | Record failed loads; test text access under slow/interrupted connections. |
| Editorial effort | Record drafting, media preparation, and review time per unit. |

Thresholds guide investigation, not promised outcomes. Likes express interest, not proof of learning. Small pilot results must not be presented as causal proof or guaranteed exam improvement.

## 2. MVP scope and acceptance criteria

Confirmed: text, images, audio, and video are included now; data saver and caching are included; downloadable offline lessons are deferred; login is invitation-only.

Start with six posts across three syllabus-aligned topics, covering all four media types across the collection. Each new post has one learning objective, exactly one content card, and zero or exactly three four-choice questions. Only posts with three reviewed questions can supply dares. Preserve existing content and version history.

| Feature | Acceptance criteria |
| --- | --- |
| Email login links | An invited candidate requests a link, opens it on Android, and signs in without a password. Expired, used, and invalid links offer recovery. Non-invited addresses cannot register. |
| Subject-based feed | Candidates choose exam-labelled subjects and browse a random mix of standalone published posts. Drafts remain inaccessible. Loading, empty, error, retry, and end states work. |
| Text and images | Text loads independently of optional media. Images are compressed, have alternative descriptions, and load on request in data saver mode. |
| Audio | User-initiated playback; duration and download size shown; transcript supplies the educational explanation without playback. |
| Video | User-initiated playback; lightweight version, captions, and text summary available; leaving the item stops playback. |
| AI-assisted publishing | Staff request new text, image, meme, or silent captioned video drafts through admin in stages AI-1–AI-3. Questions are optional. A human checks accuracy, humour, syllabus alignment, references, accessibility, and media rights before explicit publication. Manual drafting remains available. |
| Quizzes | Optional dares use only published posts with three reviewed questions. Zero-question posts remain publishable and visible in the feed. Server calculates scores; keys stay hidden before submission; explanations follow submission; retries do not create duplicates. |
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
- Automatic publication, audio generation, narrated video, bulk generation, and AI regeneration of existing posts. Integrated generation of new posts is planned in AI-1–AI-3.
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

Django admin generation request → database job queue → worker → OpenAI API → validated unreviewed draft → human review → explicit publication. Manual draft entry remains available.
Android app ↔ DRF API ↔ database; app also uses local cache and media storage/CDN; backend uses email delivery.

- React Native + Expo + TypeScript: Android screens, navigation, playback, caching, and API calls.
- Django admin: staff-only generation requests/status, manual drafting, media attachment, review, publication, and withdrawal.
- Generation worker: a separate process in the same Django project, started by a management command; processes database jobs without blocking admin pages. No Redis or Celery initially.
- OpenAI adapter: backend-only credentials and configured models; validated structured text/questions, image generation, and asynchronous video jobs.
- Pillow and FFmpeg/ffprobe: prepare generated images/memes and videos for existing media limits; retain private originals for staff inspection.
- DRF: authentication, content access, scoring, likes, challenges, reporting.
- SQLite locally; PostgreSQL before hosted pilot: simple initial setup, then verify deployment behavior.
- Object storage/CDN: store and deliver media outside application requests.
- Email service: login-link delivery; local email backend during development.
- REST/JSON under /api/v1/: documented frontend/backend communication.

One backend project; no microservices or separate queue platform initially. AI generation adds one configured worker process and database-backed jobs.

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
- Admin generation requires a provider connection. Generation jobs do not introduce candidate offline quiz/like synchronization.

Editorial limits: images ≤250 KB; audio ≤90 seconds/1 MB; video ≤60 seconds/5 MB and height ≤480 pixels. Staff can still prepare uploaded files manually. AI-2 adds generated-image/meme preparation; AI-3 adds generated-video conversion to these limits. General upload transcoding and adaptive streaming remain deferred.

These are pilot defaults to test, not playback guarantees. Text alternatives keep objectives accessible when media fails.

### Data and API boundaries

Core records: users/invitations, login tokens/sessions, syllabus topics/objectives, learning-unit versions, feed items, media assets, questions, attempts, likes, challenges, learning events, generation jobs and their provenance.

- Published versions immutable; corrections create replacements.
- Attempts/challenges retain original version.
- Feed items have stable identities so likes survive revisions.
- Media metadata: type, size, duration, transcript/captions, attribution.
- Endpoints: login-link request/exchange, logout, content, attempts, progress, like/unlike, challenge lifecycle.
- Idempotent like/unlike operations and unique submission identifiers support safe retries.
- Server enforces permissions and publication visibility.
- Generation is staff-only through admin, with a separate permission; no public generation endpoint.
- Feed responses add quiz_available without questions or keys. Older cached posts missing the flag remain readable but cannot supply dares until refreshed.

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

### AI generation stages — approved 2026-10-13

These stages extend the approved scope without renumbering Milestones 0–9. Each needs separate implementation approval; approving this document does not start a stage or automatically change the existing milestone order.

| Stage | Status | Objective and prerequisites | Tasks and completion criteria |
| --- | --- | --- | --- |
| AI-1 — Admin jobs and text | Implemented; live and phone acceptance pending | New-post generation after the editorial/feed/quiz foundations. Provider configuration and a checked source example are needed before live checks. | Admin form, generation permission, job model/migration, queue worker, provider adapter, validated text/optional questions, and quiz eligibility. Admin can generate and review a draft; zero-question posts publish and never supply dares; permission, duplicate, and recovery tests pass. |
| AI-2 — Images and memes | Not started; separate approval required | Actual generated media after AI-1 acceptance. Requires image-model access and Pillow. | Generate original images, render meme captions locally, prepare descriptions and private previews. Prepared images meet the 250 KB limit; text is readable; human/device review passes. |
| AI-3 — Silent captioned videos | Not started; separate approval required | Actual videos after AI-2 acceptance. Requires video-model access, FFmpeg/ffprobe, and worker runtime checks. | Save/poll provider jobs, download and prepare a silent captioned MP4 with a text alternative. Default eight-second portrait clip; height ≤480 pixels and size ≤5 MB; actual format/duration, Android playback, and human review pass. |

## 5. Testing and quality

- Backend: publication with zero or exactly three questions, permissions, login expiry/reuse, scoring, duplicates, likes, challenge transitions, generation recovery, provider failures, and atomic draft creation.
- Mobile: login recovery, data saver, loading/errors, likes, submissions, playback, quiz eligibility, and stable dare placement with question-free posts.
- Real Android: email links with app closed/open, slow connections, interrupted media, larger fonts, cache.
- Integration: PostgreSQL before hosting; real email delivery and storage; a controlled live generation check for each separately approved AI stage. Automated tests mock providers and spend no API credits.
- CI: backend checks/tests, TypeScript, frontend tests, linting.
- Editorial: Biology accuracy, syllabus mapping, humour, accessibility, references, media rights; tests cannot establish educational quality.
- Media preparation: actual image sizes/meme readability and decoded video duration, dimensions, format, captions, and private storage. Reject files that cannot meet limits. Human preview and Android playback remain required.
- Generation failures: unauthorized access, duplicate clicks/imports, invalid output, refusals, missing settings, rate limits, uncertain timeouts, and no automatic publication.

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
| Media increases scope/cost | Separate AI stages, short outputs, fixed limits, bounded requests, and preparation checks. |
| Paid requests duplicate or fail | Save job/provider IDs, resume known jobs, and flag uncertain outcomes rather than blindly submitting another paid request. |
| Generated files fail device limits | Prepare images with Pillow and videos with FFmpeg; reject unreadable/oversized results and require human/device review. |
| Email delays block access | Early delivery test; resend/recovery; monitor without secrets. |
| AI misconceptions | Review each item/question; independently verify references. |
| Likes reward entertainment alone | Compare with completion and delayed learning. |
| Cache becomes outdated | Version assets; refresh status online; label offline; bound retention. |
| Recruitment assumptions fail | Confirm access, ages, email availability, willingness. |

Before relevant milestones: identify reviewer, three syllabus topics, pilot organizer, email service/domain, and hosting budget. OpenAI is selected for generation. Before live AI checks, establish API account access/funding, backend-only credentials, configured models, and a server-enforced daily limit. Verify SDK compatibility and model access in each stage. FFmpeg/ffprobe were not found on PATH during planning; install them before AI-3. Hosting the generator also requires worker operation, private-file backups, and spending monitoring. This documentation approval does not authorize paid calls, purchases, installations, or application implementation.

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

Historical decision record: status statements below describe that checkpoint, not current implementation status.

Owner requested examination-aware models: JAMB is the MVP examination, with others such as SSCE reserved for future releases. This explicitly refines the existing topic-based feed and M2 content hierarchy; it does not authorize additional milestones or examinations in the MVP.

- Examination → Subject → Topic → Learning unit version. Biology is unique per examination, not globally.
- Existing subjects/content migrate to JAMB, preserving record identities, text, questions, publication status, and review history.
- Admin identifies each subject/topic's examination and supports examination filtering. Published/withdrawn content cannot be reassigned to another examination through subject/topic saves.
- JAMB is initially active. Other examination records default to inactive; no SSCE lessons are seeded.
- M3 student APIs must expose examination identity and restrict availability to active examinations and published content. M4 selection must clearly identify JAMB Biology. These student features remain unimplemented.

Acceptance for this model increment: JAMB Biology and SSCE Biology can coexist; duplicate Biology within one examination is rejected; every subject requires an examination; existing lessons retain their data under JAMB; seed commands target JAMB; tests verify migration, filtering, and history protection. Future examinations require their own reviewed syllabus/content before activation.

## Owner-approved feed change — 2026-10-12

Historical decision record: this was the scope of that feed increment; later milestones and approved revisions extend it.

The owner asked to replace the lesson-menu entry flow with a playful, full-screen feed and search. This updates the earlier topic-based entry flow within Milestone 4. Other milestone boundaries and publication rules stay in place.

Acceptance criteria:

- After sign-in, show subject checkboxes with the exam in parentheses, such as Biology (JAMB). Choose at least one subject, up to 20.
- Continue straight into posts from those subjects. No exam/topic/lesson menu is required before scrolling.
- Each post fills the feed area. Swiping up moves to the next post. Long text, transcripts, and sources remain available through Read more.
- Search finds published content within the selected subjects. Empty results, connection failures, retry, loading, and the end of the feed have clear states.
- Remember subject picks in this account's phone cache. Let users change them; clear them with cached content or sign-out. This is not a cross-device preference service.
- Keep data saver on by default, user-started audio/video, playback pause when leaving a post, offline labels, publication checks, and the 100 MB cache limit.
- JAMB Biology remains the MVP content scope. No extra exams, user uploads, likes, quizzes, sharing, recommendations, or automatic publication are added by this change.

The feed uses reviewed card text already in the database. A new layout does not establish that jokes are funny or learning improves; review and pilot feedback still decide that.

## Owner-approved entertainment-first update — 2026-10-12

Historical decision record, retained. The AI revision below adds optional question generation and quiz eligibility; the entertainment-first experience remains the target.

The owner clarified that Swipe-IQ is for fun, relaxing scrolling, with Biology woven into entertaining content. This update supersedes earlier lesson-sequence, fixed post-to-quiz, multi-card publication, and completion-target assumptions. The owner explicitly authorized implementation after choosing in-feed dares and one content item per post.

Acceptance criteria:

- Show random standalone posts within the candidate's chosen subjects/examinations. No required topic order or teaching sequence. A fresh online opening/refresh gets a new mix; loading more keeps that mix stable. A small collection can still produce the same visible order by chance.
- Newly published posts have exactly one card, optionally with one media attachment. Multiple content items/carousels are deferred. Keep the card relationship for future expansion. Existing multi-card content, IDs, review history, and attempts must not be rewritten or deleted automatically; legacy cards remain individual feed items.
- Optional dare cards appear inside the feed, never as interrupting pop-ups or as a required ending to a post. Dismiss by swiping or Keep scrolling. Vary spacing: first after 3–7 content items, then after 5–9; do not insert dares into an empty feed. These are testable initial defaults, not evidence of an ideal frequency.
- Remove quiz buttons from post endings and Read more. Accepting a dare opens the existing three-question solo quiz. Resuming unfinished dares remains available through Settings → My progress. No timer, automatic submission, or requirement to play.
- Two-person friend challenges remain Milestone 7. Clearly label them as coming later; do not show a working challenge invitation/code or opponent result before that functionality exists.
- Keep server scoring, hidden keys, retry safety, private attempt history, saved answers, media controls, and account isolation. Progress describes optional plays/posts tried, not required lesson completion. The API's existing completed_units field remains a compatibility count of posts with an accepted quiz.
- New sample drafts contain one standalone content card. Seed reruns preserve every existing draft/publication and human edit. Existing multi-card drafts require a human to reduce a replacement/new draft to one card before publishing.
- Maintain subject/search boundaries, publication removal, no autoplay, offscreen/background pause, data saver, bounded cache, and offline labels. Saved feed pages retain their mix and next cursor. Withdrawal during paging must not cause offset-based skipping.

Evaluation changes: remove the proposed 60% started-unit-to-quiz completion target as a product success requirement. Measure voluntary dare acceptance separately from return use and enjoyment; optional quiz use must not gate access. Learning/retention remains a hypothesis tested with agreed pilot questions; incidental learning is an intended effect, not an established fact. Likes and two-person challenges remain separately authorized milestones.

## Owner-approved admin AI-generation revision — 2026-10-13

At the time of this planning revision, owner approval covered this documentation update and the following target scope. All three AI stages were not started and required separate approval. The later AI-1 implementation checkpoint below records its authorization and current evidence; AI-2 and AI-3 remain unstarted. This revision supersedes manual-only AI drafting, the integrated-generation deferral, universal three-question publication, and the generated-media preparation deferral. Human review and explicit publication remain mandatory.

### Admin workflow

1. Open Content generation in Django admin and choose an existing topic. Its subject and examination are filled from that topic.
2. Enter one learning objective, the desired content brief, the official syllabus excerpt/reference, and checked teaching material. Start with staff-supplied sources; automatic syllabus downloading and web research are deferred.
3. Choose text, image, meme, or video. Enable each format only when its stage is implemented and configured. Generate three quiz questions starts unchecked.
4. Click Generate draft and return promptly to a saved job page. Show queued, generating, preparing media, draft ready, failed, or needs checking. Refresh reads saved progress; it must not start another paid request.
5. Open the new unreviewed draft and edit it. Each request creates exactly one card and either zero or three questions, according to the checkbox.
6. Check the content, questions, media, references, humour, accessibility, and rights. Complete the existing six human-review confirmations and media verification, then explicitly publish.

Each request creates a new post, not a replacement. Manual authoring remains available. Do not overwrite existing text, card identities, questions, review records, likes, or attempts. Question-free posts appear in the feed and subject list but never supply dares. Adding questions to a published question-free post uses the existing human-reviewed replacement workflow; AI regeneration of existing posts is deferred.

### Worker, validation, and private storage

- Add a generation Django app with a database queue and management-command worker. One configured worker processes one job at a time. Provider calls run outside admin requests and long database transactions; no Redis or Celery initially.
- Require an explicit staff generation permission. Protect job results/files with staff permissions. Candidates cannot inspect jobs or trigger generation. Keep API keys in the backend environment, never in mobile configuration or browser responses. Send content briefs/references, not candidate data.
- Request schema-constrained text, then validate it in the application: one card, the chosen format, and zero or exactly three questions. Each question needs four distinct choices, one correct answer, and an explanation. Structured output does not establish scientific accuracy.
- Record the creator, brief/source snapshot, format, questions flag, prompt version, provider/model IDs, timestamps/status, available usage, and resulting draft link. Show safe failure messages without credentials or raw provider error bodies.
- Create the new unit/version/card and optional questions in one database transaction. Link a job to at most one resulting draft. Leave all review confirmations and media approval unset. Do not present a half-created draft as ready.
- Store originals and prepared assets privately, outside Git. Reuse authenticated previews, not public file URLs. Isolate failed/unfinished files from published assets.
- Text produces a standalone funny post. Images produce actual original visuals with meaningful text alternatives. Memes use a generated background and locally rendered captions so saved words match the requested caption; store memes as image assets.
- Pillow prepares images/memes. FFmpeg/ffprobe prepares generated video, strips audio, and checks actual duration/dimensions. Supply readable captions and a text alternative. Reject files that cannot meet existing limits without becoming unreadable; retain them privately for staff inspection.

### Failures and compatibility

- Duplicate clicks reuse a generation request rather than adding paid jobs. Reprocessing a completed job must not import another draft.
- Save known provider job IDs and resume/check those jobs after worker restarts. Video polling reads an existing job; it does not submit new generation requests.
- If a submitted request times out with no reliable outcome, mark it needs checking. Do not automatically start another paid generation. Staff can explicitly create a new job after checking the uncertainty and potential additional cost.
- Handle refusals, invalid output, missing credentials/models, rate limits, preparation failures, and storage errors with a clear saved status and no automatic publication.
- Add quiz_available to safe post responses. Reject new quiz access/submissions for posts without three questions. Keep keys private and preserve retrieval/retries of previously accepted attempts.
- Choose dare candidates only from eligible posts already loaded. Pages without eligible posts must not generate broken dares. Loading more must not insert dares retroactively or reorder earlier entries. Cached posts missing the flag stay readable but cannot supply dares until refreshed.

### Defaults and prerequisites

- One new post per job; no bulk generation. Questions unchecked by default.
- One configured worker; server-enforced limit of five new generation jobs per day.
- Model names, timeouts, and limits are backend configuration, not arbitrary admin inputs. Generation stays disabled until credentials, model names, and the daily limit are configured.
- Verify API account access, funding, chosen-model availability, and Python SDK/media-library compatibility before live checks. Pin verified dependency versions; do not assume every account supports every format.
- Audio generation, narrated video, existing-post AI regeneration, and automatic publication remain deferred. Existing manually uploaded audio remains supported.
- Before hosting, configure worker operation, private-file backups, and spending monitoring. A request quota is not a guaranteed currency spending cap.

### Files to change during implementation

| Files/area | Planned changes |
| --- | --- |
| backend/generation/ (new) | Job model/migration, admin form/status/permissions, OpenAI adapter, prompts/output validation, worker command, private media preparation, and tests. |
| backend/config/settings.py; backend/.env.example; backend/requirements.txt | Register the app, placeholder settings, backend credential/model/limit configuration, and pinned dependencies. |
| backend/editorial/services.py; backend/editorial/admin.py | Permit zero or exactly three questions, retain human-review gates, explain optional questions, and link generated drafts to their job. |
| backend/editorial/student_api.py | Expose quiz_available without questions, keys, or private generation metadata. |
| backend/learning/views.py; backend/learning/services.py | Reject new access/submissions for missing quizzes while retaining original results and accepted-submission retries. |
| mobile/src/feed/types.ts; mobile/src/feed/mix.ts; mobile/src/feed/repository.ts | Read/cache eligibility and select safe dare candidates without changing existing feed positions. |
| Backend and mobile test files | Cover job recovery, permissions, publication/quiz eligibility, output validation, retries, media preparation, and cache compatibility. |
| AGENTS.md | During AI-1, align manual-only/deferred-generation rules with this approved scope and mandatory human review. This documentation-only update does not edit AGENTS.md. |
| README.md and docs/ | At the corresponding stage, update setup, requirements, architecture, milestones, drafting/editorial/media guides, API notes, and learning log to match implemented behavior. |
| .github/workflows/checks.yml | Add media-processing test dependencies when those stages arrive. |

### Acceptance checks

- Unauthorized users cannot generate content or inspect private jobs/files. Server limits apply to duplicate/concurrent submissions.
- Double-clicks and worker recovery do not duplicate jobs or drafts; unknown paid-request outcomes do not trigger blind retries.
- Refusals, malformed output, missing settings, rate limits, timeouts, storage/preparation failures, and interrupted imports produce clear statuses without half-ready drafts.
- Generated output never sets review confirmations or publishes itself. Human editing and explicit publication remain necessary.
- Zero-question and complete three-question posts can publish; one or two questions cannot. Question-free posts still appear in the feed/subject list but never supply dares. Preserve existing content and attempt history.
- Pagination and older cached data keep posts readable and dare placement stable, including pages with no quiz-eligible posts.
- Image/meme size and readability pass; video actual duration/dimensions/format and text alternatives pass. Human preview and physical Android checks are required for media acceptance.
- Automated tests mock providers and spend no credits. Each separately approved stage also needs a controlled live generation check and human review. Mocked tests do not establish API access, output quality, or phone success.

Official provider references used during planning:

- [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Image generation](https://developers.openai.com/api/docs/guides/image-generation)
- [Video generation](https://developers.openai.com/api/docs/guides/video-generation)

Related project references: [Editorial workflow](content/editorial-workflow.md), [media preparation](content/media-preparation.md), and [milestone status](milestones.md). These describe existing implementation checkpoints and will be aligned when the corresponding AI stage is implemented.

## AI-1 implementation checkpoint — 2026-10-13

The owner explicitly authorized AI-1. Staff can request new text drafts in admin, with supplied source excerpts and optional three-question quizzes. A separate worker calls OpenAI, saves confirmed output, and imports a new unreviewed draft in one transaction. Publication remains a human action. Zero-question posts appear in the feed but never supply dares.

Desktop evidence: 110 backend tests and 57 mobile helper tests pass, including permissions, duplicate requests, quota limits, interrupted jobs, provider failures, atomic imports, and mixed quiz eligibility. The migration preserved existing records. See [milestone evidence](milestones.md) and [setup steps](ai-generation-setup.md).

Live generation still needs a backend API key and text model. No paid calls or automatic publication occurred. Human content review, physical-phone acceptance, remote CI, and PostgreSQL concurrency checks remain pending. AI-2 and AI-3 need separate owner approval.

Update — 2026-10-14: the owner reported successful mobile use in Expo Go. General phone use is confirmed by the owner; individual phone test cases were not specified. Live AI generation, human content review, and the remaining detailed checks are not confirmed by this report. See the dated update in [milestone evidence](milestones.md).
