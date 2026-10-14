# Project working agreements

## Scope and approvals

- Read docs/implementation-plan.md before planning or implementing features. It is the approved baseline; docs/requirements.md and docs/architecture.md are navigation summaries.
- Implement one explicitly authorized milestone at a time. Explain its objective, make necessary changes, run relevant checks, document results, and stop for owner approval before the next milestone.
- Do not treat plan approval as permission to implement all milestones. Ask before changing agreed scope.
- Explain important decisions, alternatives, and verification in plain language. Distinguish facts from assumptions.

## Git and existing work

- Check current branch and working-tree status before edits. Never edit or commit on main.
- Use docs/jamb-mvp-plan for initial documentation and feat/<milestone-name> for implementation.
- Preserve existing user changes. Do not reset, discard, overwrite, or stage unrelated work.
- Do not merge, publish, deploy, or push without explicit authorization. Do not create commits unless requested.
- If Git ownership differs in the sandbox, use a command-scoped safe.directory exception for this exact repository; do not change global trust settings.

## Architecture and content

- Django + DRF; React Native + Expo + TypeScript; SQLite locally and PostgreSQL before hosted pilot.
- Audience: invited Nigerian JAMB Biology candidates on Android.
- AI-1 supports staff-requested new text drafts and optional questions; manual drafting remains available. Human review and explicit publication are mandatory. Never auto-publish.
- Include text, images, audio, video, default data saver, bounded cache, likes, quizzes, progress, and asynchronous challenges according to the plan.
- Defer candidate uploads, sharing, live battles, AI image/meme/video stages until separately approved, audio generation, narrated video, bulk generation, existing-post AI regeneration, and offline write synchronization.
- Enforce permissions, publication visibility, and scoring on the server. Keep answer keys and draft content private.

## Verification and secrets

- Follow docs/setup.md for verified setup and physical Android checks. Backend: .venv/Scripts/python.exe manage.py check and manage.py test from backend/. Mobile: npm.cmd run typecheck, npm.cmd run lint, npm.cmd test, npx.cmd expo install --check, npm.cmd run export:android from mobile/.
- Windows uses the virtual environment Python directly; Linux CI uses python after installing requirements. Phone acceptance and remote CI must be reported separately from desktop checks.
- Run checks appropriate to the change. For documentation, validate links, required content, branch, and preservation of existing work.
- Do not invent version compatibility or successful device checks; verify them.
- Never commit real secrets, email tokens, credentials, local environments, or identifiable pilot exports. Provide placeholder-only environment examples.

## Documentation

- Keep approved scope in docs/implementation-plan.md; record changed decisions explicitly and obtain approval.
- Update docs/milestones.md with evidence and remaining dependencies; capture reusable lessons in docs/workflow/learning-log.md.
- Add skills only for proven repeatable workflows. Add MCP integrations only for a justified concrete need.
- Update README based on the state of the app
