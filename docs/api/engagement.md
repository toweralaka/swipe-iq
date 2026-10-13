# Likes and engagement API

Candidate routes use /api/v1/, Bearer authentication, and private/no-store responses. Staff cookies do not grant candidate access. No candidate route exposes another account's state or public counts.

## Private likes

GET units/{version}/cards/{identity}/like/ returns {"liked":false} or true for this candidate.

POST the same route with {"liked":true} or {"liked":false} sets the desired state. It does not toggle on every request. Repeating a request returns the same state and cannot add records. The database permits one row per candidate/stable unit/card identity. Corrected versions retaining that identity share the like; different units remain separate.

The current published version, active examination, and card/version match are checked on both reads and writes. Draft, withdrawn, superseded, inactive, missing, and mismatched content returns 404. Invalid input returns 400; missing/rejected candidate session returns 401; database contention returns 503. No success is reported for a database error.

The phone disables repeated taps and updates its display after confirmation. On an uncertain response, it keeps the prior confirmed value, marks it unconfirmed, and offers a GET check before allowing another change. It does not blindly toggle again. State is held only in account-bound memory, not written to the content cache or an offline write queue. Session/request binding uses the existing protected candidate wrapper.

## Daily signals

POST engagement/events/:

~~~json
{"version":1,"card_identity":"12345678-1234-1234-1234-123456789abc","kind":"view"}
~~~

Kinds: view, dare_shown, dare_accepted. The server supplies the Nigeria calendar day and receipt time; client account/day/context claims do not select those values. Publication/card access is checked. A uniqueness constraint permits one record per candidate/stable unit/card/kind/day. A repeated event returns 200, a new event 201, both with recorded=true and day. Invalid input returns 400, missing sign-in 401, unavailable content 404, database contention 503. GET is unsupported (405).

Accepting a dare also ensures a same-day dare_shown record in the same transaction. It does not create an attempt, invite an opponent, or guarantee a quiz completion. There is no skip event. Offline or failed event delivery is discarded; no background write synchronization. Re-entering a visible item may try again, but the server uniqueness rule still limits counts.

The phone uses the feed's mostly-visible threshold (70%) and waits one second while focused, uncovered, connected, and in the foreground. Prefetching is not a view. Native timing/viewability still needs device verification. Counts describe received daily unique signals, not every appearance or precise reading time. The bounded in-memory delivery guard reduces repeat requests; it is not the source of truth.

## Staff export

GET /admin/engagement/engagementevent/export/?days=7 requires a staff cookie and engagement.export_engagementevent permission. The admin list exposes a download link to allowed staff. The response is a private/no-store JSON attachment. Anonymous/nonstaff browser access redirects to staff login; staff lacking export permission receives 403. The window must be 1–90 Lagos calendar days including today; invalid values return 400.

The report contains grouped daily/unique viewers and dare signals with exam/subject/topic/media snapshots, current active-like totals, aggregate accepted quiz/first/practice scores, daily active-candidate counts, and candidates observed on multiple days. Current likes are an all-time state snapshot as of export, not windowed new-like counts. Activity/return counts use received events only, not every authenticated request. Quiz counts come directly from saved server attempts.

No emails, usernames, account IDs, credentials, selected answers, or keys are exported. Stable content identifiers and grouping labels remain. Historical withdrawn/replaced activity remains reportable to staff. Different grouping buckets can share candidates; unique counts cannot simply be summed. This is aggregate internal reporting, not an assertion that small groups are anonymous or that interest proves learning.

SQLite constraints and retry behavior are tested locally. PostgreSQL simultaneous-write behavior remains a hosted-pilot check. See the [plain-language walkthrough](../likes-and-engagement-guide.md).

For an interest ratio, use content.viewers_with_active_like divided by that same row’s unique_viewers, when viewers is above zero. This means current likes among observed viewers in the report window. It does not measure when the like was made. Do not divide all-time active_likes_as_of_now totals by seven-day viewers. Offline/missing observations can still bias this ratio.
