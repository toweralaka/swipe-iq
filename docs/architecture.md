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
