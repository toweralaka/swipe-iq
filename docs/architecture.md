# Architecture reference

Approved baseline: [Implementation plan](implementation-plan.md), section 3; decision rationale: [Decision record](decisions/0001-approved-baseline.md).

## Responsibilities

- External AI tool creates drafts; staff manually enter/review/publish in Django admin.
- DRF provides versioned REST/JSON APIs, authorization, server scoring, likes, challenges, reporting.
- React Native/Expo/TypeScript provides Android navigation, display/playback, data saver, and caching.
- SQLite supports local setup; PostgreSQL is verified before hosted pilot.
- Storage/CDN serves media; email service sends single-use login links.

## Boundaries

One backend application. No microservices, integrated AI provider, automatic transcoding, or background processing platform initially. Manual media preparation precedes upload.

The API includes login-link request/exchange, logout, content, attempts, progress, likes, and challenges under /api/v1/. Exact request schemas are documented with the relevant implementation milestone, not invented during documentation setup.

Published content is versioned and immutable; attempts/challenges reference original versions; feed identities preserve likes. Server hides drafts and answer keys. Android uses SecureStore for revocable sessions and verified HTTPS App Links for pilot login.

Text precedes optional media; no autoplay; transcripts/captions support learning without playback. Cache is bounded at 100 MB; account-specific cached data clears on logout. Offline writes and a permanent download library are deferred; completed media requests can be kept in the bounded cache.

## Deployment gate

Before Milestone 8: verify PostgreSQL, HTTPS, persistent storage, email delivery, Android build, logs without secrets, and backup restoration. Domain/email setup is needed earlier for Milestone 3 device acceptance. Providers and budget remain unselected.

## Examination and subject hierarchy

Content follows Examination → Subject → Topic → Learning unit version → Cards/questions. A subject name is unique within its examination: JAMB Biology and future SSCE Biology are separate subjects with their own topics and syllabus mappings. Store the examination once on Subject; versions inherit it through their topic, avoiding contradictory examination fields.

Examination has a stable code, display name, and active flag. Migration 0002 assigns existing subjects to JAMB without replacing lessons or review history. JAMB is active; newly created examinations default to inactive. The M3 student API filters active examinations and published content on the server. Milestone 4 adds the phone selector.

Admin shows examination-qualified subjects/topics and an examination column/filter for lesson versions. Subjects and topics used by published or withdrawn lessons cannot be moved to another examination through model saves. Create separate curriculum records instead.

## Milestone 3 access implementation

The accounts app owns invitations, hashed single-use tokens, revocable hashed sessions, database rate buckets, and staff invitation/session administration. Student endpoints explicitly use bearer-session authentication; Django staff cookies do not grant student API access. The editorial student API exposes only the latest published version per unit from active examinations, with examination-qualified subjects and private media access. Questions and review metadata are excluded.

Expo Router supplies home/login/connection routes. SecureStore holds the credential; account identity is verified against the server on restore. Reading an incoming fragment link only presents confirmation. Backend /login is a static fallback; configured Android association data is served at /.well-known/assetlinks.json. No domain, email provider, signing identity, cloud build, or physical Android acceptance has been assumed.

See [API contract](api/student-access.md) and [authentication setup](authentication-setup.md). The media endpoint checks access. Milestone 4 adds phone playback and saved copies; a separate media delivery host and quizzes remain later work.

## Milestone 4 phone feed and saved copies

The phone uses Expo Router screens for exam → subject → topic → lesson. The feed repository is a small layer between screens and the backend: it reads the server first, checks response fields, and uses saved text only when a network request fails. A 401, 404, or server error does not unlock an old saved response.

Media files are small enough to download in full before playback. This is easier to reason about than live streaming for the MVP, and makes completed files usable offline. The trade-off is that users must wait for the whole clip before pressing Play. File limits remain 250 KB for images, 1 MB for audio, and 5 MB for video. Auth headers stay on the configured backend; redirected file requests are rejected.

Expo Audio and Video play local files. Playback waits for Play and pauses when the card leaves view, the route closes, or the app goes into the background. Video captions use the supplied VTT cue times. Images load on request by default; data saver off allows visible images to load automatically. Background playback, recording, and picture-in-picture are disabled.

A file cache keeps text, lists, and completed media under 100 MB, including its index. It removes items used least recently and allows at most 200 entries. It belongs to one backend/account at a time. A generation number rejects late downloads after clearing or changing accounts, so a request started before logout cannot repopulate the old cache. Android may still remove cache files to free space.

SecureStore holds the last server-checked account and session expiry, bound to its credential. This supports offline reopening after a successful online login without extending the session. Saved teaching content is in the normal app cache, not an encrypted store. On opening the feed, returning to the app, and reconnecting, an authenticated availability check removes saved versions no longer published. While disconnected, the app cannot know about new withdrawals and labels saved text Offline.

The device adapter uses Expo FileSystem. Tests use an in-memory disk with the same small interface, so storage limits, corruption recovery, and account isolation can be checked without pretending a desktop test proves native playback. See [phone checks](feed-phone-guide.md).

## Owner-requested swipe flow

The main phone route is now sign-in → subject checkboxes → swipe feed. Subjects include their exam label. The old topic/detail routes still work as direct routes, but the main flow no longer sends candidates through those menus.

GET feed/ filters by selected subject IDs and an optional short search. It returns safe unit metadata and cards in small pages; the phone displays one card per screen. Search uses database word matching over published content, not an external AI service. This avoids another provider and keeps unpublished material out of search.

Subject picks live in the same account's bounded phone cache. Feed pages also store their version IDs through the existing unit-cache records, so reconnect checks can remove unavailable versions and their old feed pages. Clearing content clears picks too; cross-device preferences remain future work.

The screen uses a paged FlatList to keep a few posts mounted at a time. Read more supplies complete text and alternatives in a scrollable view. Small screens and larger text can open media there; only the visible media area can play. Data saver and publication rules remain the same.

API references checked: [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/), [React Native FlatList](https://reactnative.dev/docs/flatlist), and [Django queries](https://docs.djangoproject.com/en/5.2/topics/db/queries/).
