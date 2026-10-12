# Editorial workflow — Milestone 2

## Start the staff interface

From backend/ in PowerShell:

    .\.venv\Scripts\python.exe manage.py migrate
    .\.venv\Scripts\python.exe manage.py seed_demo
    .\.venv\Scripts\python.exe manage.py createsuperuser
    .\.venv\Scripts\python.exe manage.py runserver

Choose your own staff password interactively; none is seeded. Open http://127.0.0.1:8000/admin/. Keep the account private. Student passwordless login is implemented in M3 with real-device acceptance pending; staff admin uses Django's separate staff login.

seed_demo is repeatable and preserves existing edits. It creates two unreviewed cell-comparison learning-unit drafts aligned to the [official JAMB mapping](syllabus-source.md), five cards, and six questions. It does not create accounts, upload media, check review boxes, or publish. These examples are not a validated topic shortlist or approved lessons.

## Staff roles

For local evaluation, a superuser can perform all steps. For regular use, give editors active staff status and add/view/change permissions for editorial records. Give reviewers view permissions and the custom Can review, publish, and withdraw learning units permission. They need change permissions to edit review confirmations, and add permissions to create replacements. Only staff with view-media permission can preview files. Do not give candidates staff access.

## Prepare and review

1. Select a topic under **JAMB Biology**. Each subject belongs to one examination; the topic dropdown includes the examination in its label. Confirm the learning objective and map it to the official JAMB syllabus; record the objective/reference on the version.
2. Use [drafting prompt](ai-drafting-prompt.md) with an external AI tool. Enter tool/date/prompt notes in AI provenance. Suggested AI references must be independently checked.
3. Create a stable Learning unit, then a version starting at 1. Save as draft. Its title, objective, topic, and content belong to that version.
4. Create media assets separately following [media preparation](media-preparation.md). File size and basic signature are checked automatically; staff must verify actual playback/duration/dimensions and rights.
5. Add 1–3 cards numbered from 1, each with meaningful text. Attach media as needed. The collection can use all four formats; a single unit need not contain all four.
6. Add exactly three questions numbered 1–3; provide four distinct choices, one correct letter, and an explanatory answer for each.
7. Complete [review checklist](review-checklist.md), six confirmations, verified source details, and review notes. Save changes before running publication actions.
8. In the learning-unit-version list, select the draft and run Publish selected reviewed drafts. The service revalidates the complete saved unit, records the acting reviewer/time, and freezes the version.

A normal save never publishes. Failed publication leaves the draft unchanged and displays the reason. M2 added no student content API. M3 now provides an authenticated published-content API and media route; drafts remain staff-only. See [student API](../api/student-access.md).

## Corrections and withdrawal

- Select a version and Create replacement drafts. This copies cards/questions, retains stable card IDs, increments the version, and resets all review confirmations and reviewer metadata.
- Edit the replacement; use new media assets if their content changes. Shared published assets cannot be edited.
- Recheck and publish the replacement explicitly. This does not automatically withdraw the prior version; use Withdraw selected published versions when appropriate.
- Withdrawal preserves history and assets. It cannot be undone by editing status. Create/review a replacement instead.

Bulk update/delete shortcuts are blocked for editorial records. Model saves enforce guards, not merely disabled admin controls. Direct SQL is outside application protections; never use it for editorial maintenance.

## Human acceptance still required

Nominate a reviewer. The initial objective is now mapped to the official JAMB syllabus; see [source and mapping](syllabus-source.md). The reviewer still checks mapping currency and scientific accuracy. Supply real permitted PNG/JPEG, MP3/WAV, and MP4 samples; review and publish sample units demonstrating all four content formats. Test fixtures are not teaching media and no automated check establishes Biology accuracy.

Before closing M2, record reviewer/date, unit/version, checked reference, formats inspected, publication/correction/withdrawal results. Keep personal details and unpublished files out of Git.

## Additional memorable sample drafts

Use [five humorous Biology samples](sample-content.md) for more realistic text-based review practice. Run seed_sample_content to add them without replacing the earlier demo units.

## Examination setup

Migration and seed commands establish JAMB. In admin, Examinations lists its name/code/active flag. Subjects require an examination; Biology under JAMB is distinct from Biology under another exam. Topics belong to these exam-specific subjects. Lesson versions show their examination in the list and can be filtered by it.

Only JAMB is in the MVP. For a future examination, create a separate inactive examination, its subjects, and topics; do not move existing JAMB subjects/topics. Activation will control future student availability through the M3 student API. Do not treat the active flag as publication or as a working phone selector today.
