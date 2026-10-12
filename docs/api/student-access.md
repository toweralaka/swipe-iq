# Student access API

All paths below use /api/v1/. JSON requests and responses; lists use {count, next, previous, results}, 20 rows per page. Follow next only on the configured API host. Authenticated requests send Authorization: Bearer <credential>. Cookies and staff credentials do not authorize student routes. Auth/content responses use no-store.

## Authentication

| Method/path | Input | Result |
| --- | --- | --- |
| POST auth/request-link/ | {"email":"invited@example.com"} | 202 with the same generic message for invited/unknown/inactive addresses. No token in response. Invalid email: 400; rate limit: 429 with Retry-After. |
| POST auth/exchange/ | {"token":"<43-character-email-token>"} | 200 with credential and expires_at. Invalid/expired/reused token: 403; malformed: 400. |
| GET auth/me/ | Bearer credential | {id,email,expires_at}; invalid/expired/revoked session: 401. |
| POST auth/logout/ | Bearer credential and {} | 204, session revoked; invalid/already revoked: 401. Client treats 401 as already signed out. |

Tokens: 32 random bytes, 15-minute lifetime, single-use conditional database consumption. Sessions: independently random, 30 days, revocable. Only SHA-256 digests are stored. New candidates receive unusable passwords and no staff privileges. Deactivating an invitation/user immediately denies access. Invitations linked to accounts cannot change email through instance/admin saves; deactivate and create another invitation instead.

Email/IP request limits: 3 per normalized email and 20 per IP in fixed 15-minute windows; exchange: 30 per IP per window. Database conditional increments protect counts; identifiers are keyed hashes, not raw addresses/IPs. Boundaries can permit adjacent-window bursts. REMOTE_ADDR is used; no untrusted forwarding header is accepted. Trusted proxy/client IP behavior must be verified before hosting. Generic responses conceal invitation status in the response body; SMTP timing is not constant-time.

Delivery failures return the same response and emit only a generic configuration error. Local file-based email is for development; real SMTP must be verified separately. Do not enable request-body logging or analytics on authentication routes. Login URLs use /login#token=..., keeping secrets out of web request URLs. GET /login is a static installation/help page and never exchanges a token.

## Published content

All routes require a valid student session, even when the result is empty.

| GET path | Optional filter | Result |
| --- | --- | --- |
| examinations/ | — | Active examinations that have available content: id/code/name. |
| subjects/ | examination=jamb | Subject id/name and nested examination. |
| topics/ | subject=<id> | Topic id/name, nested subject/examination. |
| units/ | topic=<id> | Latest published version per stable unit: id/unit_key/number/title/objective/topic. |
| units/<version-id>/ | — | Same metadata plus ordered cards: identity/position/text/media. |
| media/<uuid>/ | — | Authenticated file bytes, only if attached to an available version. |

Only published content from active examinations is available. Draft, withdrawn, superseded, and unknown version IDs return 404; list queries cannot reveal them. If the newest publication is withdrawn while an older version remains published, that older publication becomes available again; withdraw all unwanted publications explicitly.

Media metadata: id/kind/byte_size/duration_seconds/alt_text/transcript/captions_vtt/attribution/url. URL is an API-relative path requiring the same Authorization header; no direct storage URL is exposed. The phone downloads these small files with an Authorization header and plays the saved local copy. Range streaming and delivery through a separate media host remain future hosting work.

Questions, correct choices, explanations, review notes, AI provenance, staff identities, and draft files are excluded. Quiz delivery/scoring arrives in M5. Unsupported writes return 405. Milestone 4 uses these routes for the phone feed and media.

## Retention and checks

Local outbox files contain live secrets: delete them after testing and never commit or share them. Before hosting, schedule removal of expired login tokens, expired/revoked sessions, and expired RateBucket rows, and define operational retention without changing attempt/history records. PostgreSQL concurrency and trusted proxy behavior remain deployment checks; SQLite tests do not prove hosted multi-worker behavior.

## Check saved lessons — Milestone 4

POST /api/v1/units/availability/ requires the same student Authorization header. Send {"version_ids":[1,2]} with up to 200 positive IDs. The response is {"available_ids":[1]} containing only versions that the account can read now. Invalid input returns 400; no sign-in returns 401.

This read-only check uses POST to send a bounded list in the request body. It does not publish or change lessons. The phone uses it on opening the feed, returning to the app, and reconnecting. It removes saved text/media for unavailable versions and reloads lists. Offline copies can remain visible until a successful server check; they are labelled Offline.

GET auth/me/ includes the session's expires_at timestamp. The phone stores the last checked account and expiry beside the credential in SecureStore. A network failure can restore that same unexpired account offline. A rejected session clears the credential and account's cache. HTTP errors never unlock saved content as an offline fallback.

## Swipe feed and search

GET /api/v1/feed/?subjects=1,2&q=cells requires a student session. subjects is required: 1–20 positive subject IDs, separated by commas. It filters by subject identity, including its exam, so Biology under JAMB and SSCE cannot be confused. Only active exams and latest published versions are included.

Optional q accepts up to 120 characters and 10 words. Each word must match a title, aim, card text, topic, or subject name; matching ignores case for the MVP's English text. This is simple word matching, not AI search or recommendations.

The response is a cursor page of up to 10 post versions with count, next, mix, and results. Each result has the same safe fields/cards as the unit-detail route. New publications have one content card. The phone turns every card into a full-screen post to preserve access to older multi-card content. Media bytes still require a separate request. Questions, answer keys, drafts, and review notes remain hidden. Each first request gets a random mix token. Stable seeded ordering keeps that mix while paging; a publication-time cutoff excludes later publications until refresh. Follow the returned cursor instead of page numbers. The next link includes mix and before; preserve them. Optional mix is 32 lowercase hex characters and before is an ISO timestamp. Cursor paging avoids skipping an item when a preceding publication is withdrawn. Follow next only on the same server, feed path, subjects, and search.

Invalid filters return 400, missing/rejected sign-in returns 401, and no matching content returns an empty 200 page. These feed pages use the same phone cache and reconnect checks as unit details. Search history is not stored as a separate account feature.

## Quizzes and progress

Milestone 5 adds separate authenticated quiz, submission, result, and progress routes. Feed and lesson endpoints still omit questions and keys. See the [quiz API](quiz-progress.md) for payloads, private history, and safe retries.

Dares are inserted on the phone between content items, based on the returned mix token. They do not expose questions/keys, submit attempts, or start a two-person challenge merely by being displayed. Skipping a dare performs no server write. Search remains within the chosen subjects; dares draw from that returned content. The first-page cache uses the subject/search path and stores its returned mix and next cursor so offline reopening can reuse the last viewed mix. Old cached feed formats need one connected refresh after this update.
