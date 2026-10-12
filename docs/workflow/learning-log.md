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
