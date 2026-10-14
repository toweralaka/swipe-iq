# Requirements reference

Approved baseline: [Implementation plan](implementation-plan.md), sections 1–2. All feature acceptance criteria there are authoritative.

## Intended outcome

Help invited Nigerian JAMB Biology candidates begin and sustain revision through entertaining, accurate, syllabus-aligned content and retrieval practice. Engagement and learning improvement are hypotheses to measure.

## Included

Passwordless email links; subject-selected full-screen published feed and search; text/images/audio/video; human-reviewed AI drafts; data saver and bounded caching; quizzes/explanations; progress; private likes with staff aggregates; asynchronous two-person challenges; pseudonymous pilot reporting.

## Excluded

Candidate uploads, sharing, social features, live battles, personalized ranking, automated AI publishing, integrated generation, offline submissions, full syllabus/mocks, iOS, app-store release.

## Pilot and content

Six units across three syllabus-aligned topics; all four formats represented across the collection. Each unit has one objective, up to three feed items, three four-choice questions. Proposed pilot: 10–15 candidates for one week. English is the inherited content default; confirm suitability with participants.

## Open dependencies

Reviewer and topic shortlist unconfirmed. Recruitment, ages, email availability, and participation arrangements require validation. Do not claim verified curriculum coverage or measured impact before evidence exists.

## Examination scope refinement — 2026-10-12

Owner confirmed JAMB is the MVP examination; other examinations follow later. Subjects belong to an examination, so future student selection must identify **JAMB Biology**, rather than an ambiguous Biology. SSCE content, syllabus mapping, and student availability are outside this increment. See the [approved plan addendum](implementation-plan.md#examination-scope-refinement--2026-10-12).

## Owner-requested swipe flow

After sign-in, choose subjects using checkboxes labelled with their exam, then continue straight to full-screen posts. Swipe up to advance. Search stays within chosen subjects. Read more keeps full text and media alternatives available. Subject choices belong to this account's phone cache and can be changed or cleared. See the latest [approved plan addendum](implementation-plan.md#owner-approved-feed-change--2026-10-12).

## Milestone 5 implementation

Quick play now offers three questions for a published post. The server scores all three, then returns explanations. Identical retries count once. Results and history belong only to the signed-in candidate. Completion means submitting a quiz; first-play percentages exclude practice, including corrected versions of the same post. Choices survive reopening on the same account until submission succeeds or sign-out clears them. Submission and history need a connection. See [phone acceptance steps](quiz-phone-guide.md); device acceptance remains pending.

## Approved entertainment-first update

Users scroll a random subject-based mix for fun; there is no required learning sequence. New publications have exactly one content card; carousels are deferred. Older content stays intact. Optional in-feed dare cards appear at varied intervals, can be skipped, and are independent of finishing a post. Fixed post-ending quiz buttons are removed. Current accepted dares are solo plays; friend challenges remain Milestone 7 and are labelled as coming later. Settings → My progress keeps unfinished dares and optional play history reachable.

Acceptance: one-card publishing, stable shuffled cursor pages, subject/search boundaries, no server write on skipping, no answer keys before submission, unchanged retry/account protections, saved mixed pages offline, and pause when media leaves view for a dare. Physical-phone checks remain open. See the latest [approved-plan addendum](implementation-plan.md#owner-approved-entertainment-first-update--2026-10-12).

## Milestone 6 implementation

A candidate can privately like/unlike a published feed item. Repeated taps or identical requests cannot add duplicate likes. Corrections that retain the stable card identity keep the like. The phone waits for server confirmation; an uncertain reply offers a state check instead of another blind toggle. Offline likes are disabled and are never queued. Likes do not rank the feed.

Connected visible posts and optional dare shown/accepted signals count at most once per candidate/stable post/day. Skipping remains request-free. Staff with explicit export permission can download aggregate activity and server quiz totals without emails/account IDs/answers. Interest ratios use current likes among the same observed viewers, not mismatched all-time totals. Counts remain partial observations, not proof of learning. The [phone/admin checklist](likes-and-engagement-guide.md) remains open.

## AI-1 implementation

Staff can request new text drafts in admin using a selected topic, objective, brief, syllabus excerpt, and checked teaching source. Questions are optional: zero or exactly three per published post. Only quiz-ready posts supply optional dares. A separate worker creates unreviewed drafts; humans still review and publish them. Generation starts disabled unless backend settings enable it and provide credentials, a model, and a daily limit. See [setup](ai-generation-setup.md). Images, memes, and silent videos await separate stage approval.
