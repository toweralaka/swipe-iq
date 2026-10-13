# Learning log

## 2026-10-12 — Milestone 0: separate decisions from implementation

The approved plan fixes the intended behavior and exclusions before code is generated. Acceptance criteria explain observable success; milestones keep each change small enough to inspect and verify.

A separate Git branch makes the work reviewable without editing main. Existing user changes remain intact and unstaged; branch creation does not make unrelated changes part of this milestone.

Persistent AGENTS.md instructions carry the workflow into later sessions. The plan is authoritative; short requirements/architecture references aid navigation without competing specifications.

Unconfirmed people, services, and devices stay visible in a dependency register. Documentation cannot establish a reviewer, successful device run, or measured educational impact.

Reuse on another app: define audience/problem → write acceptance criteria and exclusions → record trade-offs → create a branch → implement one approved increment → verify → record evidence → request the next milestone's approval.

## Milestone 1 — verify the smallest complete connection

A health endpoint and one phone button test the frontend/backend boundary before adding learning features. The API client validates the response instead of treating any HTTP response as success. Backend and client tests cover the same public contract from both sides.

Pinned Python requirements and the npm lockfile make dependency installation repeatable. CI repeats checks; it cannot prove Wi-Fi access or replace a real-device check. Use the computer’s LAN address on a phone because localhost always refers to the device making the request.

Security advisories were inspected and compatible fixes applied. Forcing an SDK downgrade to silence an audit would trade visible warnings for unverified compatibility; unresolved advisories remain documented rather than hidden.

## Milestone 2 — save, review, and publish are different operations

Draft saves preserve work without exposing it to students. Publication validates the complete saved unit and records the acting reviewer; immutable versions preserve exactly what future attempts refer to. Corrections copy content into a fresh draft and reset review, instead of rewriting history.

Private media access matters even before student APIs exist: hiding draft records is insufficient if their uploaded files are publicly reachable. Preview access therefore requires staff permissions and no public media route is configured.

Tests verify workflow rules, not scientific truth or full media playback. A reviewer must independently check facts and media. Demo seeding is repeatable and cannot overwrite edited drafts or silently publish them.

## Examination refinement — model the context of a subject

A name such as Biology does not identify its exam or syllabus. Making Examination the parent of Subject allows the same subject name under different exams while keeping each curriculum separate. A database constraint enforces uniqueness of the pair, rather than relying on admin wording alone.

A separate migration first adds a nullable relationship, assigns existing subjects to JAMB, then makes the relationship required. This preserves existing lessons instead of resetting the database or rewriting an applied migration. Migration tests verify old data survives; comparison of local editorial rows confirms preservation in this workspace.

Put a relationship in one place and follow it: a lesson's examination comes from its topic's subject. Repeating the examination on every lesson would allow contradictory values. Model preparation and a phone selector are separate increments, verified independently.

## Milestone 3 — distinguish code verification from service/device acceptance

Authentication crosses email, server, Android link handling, and secure device storage. Build the rules locally first: invitation checks, short-lived single-use tokens, revocable sessions, and publication permissions. Tests deliberately exercise expiry, replay, deactivation, failed storage, and offline logout, because these failures must never look like successful sign-in or sign-out.

Keep web links and token exchange separate: email scanners can safely open a help page, while an explicit app confirmation performs a POST. Hash server credentials and keep local test emails out of Git and logs. Document provider/domain/signing configuration without inventing delivered emails or device results.

A prepared app config and successful Android bundle do not establish verified App Links. Record the physical phone checklist separately and leave acceptance pending until the actual external setup and device check are done. This distinction applies to any future app that depends on external services.

## Milestone 4 — test failure paths before calling a feed complete

The phone screens use the same protected backend routes that were built in Milestone 3. This lets us add a usable feed without changing the review-and-publish workflow or exposing drafts.

Keep three jobs separate: screens display lessons, the repository chooses between server and saved content, and the cache manages files and space. This gives each part a clear job and lets tests simulate lost connections and full storage. The same pattern works for a recipe app, field guide, or training app.

A lost connection is different from a server refusing access. Only a network failure can use saved text; rejected sign-ins and missing lessons must stay rejected. Offline copies need a visible label because the phone cannot know about an admin's recent changes until it reconnects.

Clear operations need to handle work already in progress. A generation number makes a download started before sign-out fail when it tries to save afterwards. Otherwise clearing files once would not be enough.

Desktop checks can prove storage rules and request handling. They cannot prove sound stops when an Android app goes into the background or that video captions match speech on a real phone. Record those checks separately, use simple steps, and leave them pending until someone performs them.

## Feed redesign — change the journey without weakening the rules

The owner asked for subject picks and a playful swipe feed instead of a chain of lesson menus. We record that change as an addendum to the approved plan, then update the screens, API contract, tests, and phone guide together. That keeps the reason for the change visible without erasing the earlier decision.

The server still decides which posts are published and which exam a subject belongs to. The phone changes how those safe results look. Search uses the same publication rules, so a prettier screen cannot accidentally make drafts public.

Submitting search once saves requests compared with searching on every keystroke. Full-screen cards need a separate full-text view because long explanations and large phone text cannot always fit. Keep the short view inviting while preserving the complete explanation and media controls.

Tests can check filtering and saved copies. Only real candidates can tell us whether the new flow is more fun. Record their feedback rather than claiming an engagement improvement from the redesign alone.

## Milestone 5: scores, retries, and honest progress

We calculate scores on the server because a phone request can be changed. We also give each submission a stable ID. If the connection drops after the server records a play, retrying that ID returns the same result. A database constraint protects this rule even if requests overlap. A repeat play gets a fresh ID.

We save a result snapshot so later editorial corrections cannot silently rewrite what a candidate answered. A stable post ID links corrected versions for completion and first-play counts. Practice stays visible without raising the original first-play score. These numbers describe app activity, not proven exam improvement.

Unfinished answers deserve different handling from disposable feed copies. They use separate document files and two alternating saves. Tests deliberately interrupt writes and replies; they check whether choices survive and whether a retry keeps its ID. Native phone behavior and PostgreSQL concurrency still require their own checks. The repeatable workflow is to identify the failure that matters, encode the rule, test that failure, and document what remains unverified.

## Entertainment-first scope correction

The owner clarified the experience before further milestone work: funny standalone posts, random subject-based scrolling, one content card today, and occasional optional in-feed dares. We recorded this as an approved change instead of silently treating earlier lesson/completion rules as still current.

A random sort on every page can repeat or skip posts. We use one mix token for the entire scroll, a cursor for the last position, and a publication cutoff. A fresh online feed gets a new mix; offline reads reuse the saved one. Tests check stable pages, withdrawal between pages, and saved cursor pages.

Removing a quiz button also removes a recovery path. We added unfinished dares to private progress so saved answers remain reachable. One-card publishing applies to new publications; existing cards, IDs, reviews, and results stay intact. Seed changes affect only newly created drafts. This is how a product decision becomes concrete rules, compatibility handling, tests, and updated instructions. Fun and incidental learning still need observation with real users; passing tests cannot establish them.

## Milestone 6 — 2026-10-13: likes and useful evidence

A toggle request means “change whatever the server currently has,” which can undo a like if a lost reply is retried. Sending an explicit desired value, true or false, makes repeated requests safe. The phone waits for confirmation. If the reply is uncertain, it reads the saved state before another change. Tests deliberately lose a reply after the simulated server accepts it.

The stable card identity links a like across corrections without attaching it to unrelated posts. Database uniqueness handles duplicate requests; supported writes validate publication and the authenticated account. We reused the existing account-bound request check through a shared auth helper rather than creating a second login path.

A pilot needs clear definitions more than impressive counts. A view here means a connected post was mostly visible for a second. Repeated sightings count once per user/post/day. Failed/offline events are discarded, so reports are incomplete. We separate current like totals from the report window and provide likes among that window's observed viewers for a comparable ratio. Quiz totals come from accepted server attempts.

Reports contain aggregate counts without candidate emails, usernames, IDs, or answer keys and require a staff export permission. This limits accidental disclosure without claiming small groups are anonymous. Desktop tests verify rules, permissions, and output fields; phone timing and PostgreSQL simultaneous writes still need separate checks. The workflow lesson is to define a measurement, handle retries, constrain the database, test failure cases, and document what the numbers cannot tell you.
