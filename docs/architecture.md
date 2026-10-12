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

Text precedes optional media; no autoplay; transcripts/captions support learning without playback. Cache is bounded at 100 MB; account-specific cached data clears on logout. Offline writes and downloads are deferred.

## Deployment gate

Before Milestone 8: verify PostgreSQL, HTTPS, persistent storage, email delivery, Android build, logs without secrets, and backup restoration. Domain/email setup is needed earlier for Milestone 3 device acceptance. Providers and budget remain unselected.

## Examination and subject hierarchy

Content follows Examination → Subject → Topic → Learning unit version → Cards/questions. A subject name is unique within its examination: JAMB Biology and future SSCE Biology are separate subjects with their own topics and syllabus mappings. Store the examination once on Subject; versions inherit it through their topic, avoiding contradictory examination fields.

Examination has a stable code, display name, and active flag. Migration 0002 assigns existing subjects to JAMB without replacing lessons or review history. JAMB is active; newly created examinations default to inactive. The M3 student API filters active examinations and published content on the server. The phone selector remains M4.

Admin shows examination-qualified subjects/topics and an examination column/filter for lesson versions. Subjects and topics used by published or withdrawn lessons cannot be moved to another examination through model saves. Create separate curriculum records instead.

## Milestone 3 access implementation

The accounts app owns invitations, hashed single-use tokens, revocable hashed sessions, database rate buckets, and staff invitation/session administration. Student endpoints explicitly use bearer-session authentication; Django staff cookies do not grant student API access. The editorial student API exposes only the latest published version per unit from active examinations, with examination-qualified subjects and private media access. Questions and review metadata are excluded.

Expo Router supplies home/login/connection routes. SecureStore holds the credential; account identity is verified against the server on restore. Reading an incoming fragment link only presents confirmation. Backend /login is a static fallback; configured Android association data is served at /.well-known/assetlinks.json. No domain, email provider, signing identity, cloud build, or physical Android acceptance has been assumed.

See [API contract](api/student-access.md) and [authentication setup](authentication-setup.md). Local streaming establishes access control; media playback, caching, CDN delivery, and quiz routes remain later increments.
