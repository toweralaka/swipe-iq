# Student access API — Milestone 3

All paths below use /api/v1/. JSON requests and responses; lists use {count, next, previous, results}, 20 rows per page. Follow next only on the configured API host. Authenticated requests send Authorization: Bearer <credential>. Cookies and staff credentials do not authorize student routes. Auth/content responses use no-store.

## Authentication

| Method/path | Input | Result |
| --- | --- | --- |
| POST auth/request-link/ | {"email":"invited@example.com"} | 202 with the same generic message for invited/unknown/inactive addresses. No token in response. Invalid email: 400; rate limit: 429 with Retry-After. |
| POST auth/exchange/ | {"token":"<43-character-email-token>"} | 200 with credential and expires_at. Invalid/expired/reused token: 403; malformed: 400. |
| GET auth/me/ | Bearer credential | {id,email}; invalid/expired/revoked session: 401. |
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

Media metadata: id/kind/byte_size/duration_seconds/alt_text/transcript/captions_vtt/attribution/url. URL is an API-relative path requiring the same Authorization header; no direct storage URL is exposed. This local file streaming endpoint establishes access control; playback/range/CDN delivery is deferred to the feed/hosting work.

Questions, correct choices, explanations, review notes, AI provenance, staff identities, and draft files are excluded. Quiz delivery/scoring arrives in M5. Unsupported writes return 405. M3 exposes the contract; M4 builds the student feed/selection/playback screens.

## Retention and checks

Local outbox files contain live secrets: delete them after testing and never commit or share them. Before hosting, schedule removal of expired login tokens, expired/revoked sessions, and expired RateBucket rows, and define operational retention without changing attempt/history records. PostgreSQL concurrency and trusted proxy behavior remain deployment checks; SQLite tests do not prove hosted multi-worker behavior.
