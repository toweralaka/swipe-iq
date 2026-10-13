# Quiz and progress API

All routes use /api/v1/ and the candidate's Bearer session. Staff cookies do not grant access. Responses use Cache-Control: private, no-store. Feed and lesson responses still contain no questions or answer keys.

| Method and route | Purpose |
| --- | --- |
| GET units/{version_id}/quiz/ | Three questions for a currently available published version. Includes title, version, a suggested submission UUID, question IDs/positions/prompts, and choices a–d. No keys or explanations. Reading does not create an attempt. |
| POST attempts/ | Submit exactly three different question IDs belonging to that version, with choices a–d. Server calculates the score. |
| GET attempts/ | Your completed history, newest first, 20 entries per page. Includes next/count/results, context, number, is_first, score, total, and completion time; no detailed answers in the list. |
| GET attempts/{attempt_uuid}/ | Your original result, including selected/correct choices and explanations. Another candidate's ID returns 404. |
| GET progress/ | Your completed_units, total_attempts, and first_attempt_percentage. Percentage is null until your first completed attempt. |

## Submit answers

~~~json
{
  "version": 1,
  "submission_id": "12345678-1234-1234-1234-123456789abc",
  "answers": [
    {"question_id": 1, "choice": "a"},
    {"question_id": 2, "choice": "c"},
    {"question_id": 3, "choice": "b"}
  ]
}
~~~

Use real IDs from GET quiz. Save the UUID and choices before sending. A new play needs a new UUID. A retry must use the same UUID, version, and answers; answer ordering does not matter.

- 201: new completed attempt. 200: identical submission already accepted; returns that same result.
- 400: malformed input, missing/duplicate/foreign questions, or invalid choices. No attempt created.
- 401: sign-in missing, revoked, or expired. 404: new submission for an unavailable version, or a result not owned by this candidate.
- 409: UUID already used by this candidate with different answers/version. Original result is unchanged.
- 503: database was busy or a constraint prevented recording. Transaction rolled back; retry the exact same submission. Network errors also require the same ID because the server may have accepted the request before the reply was lost.

Result fields: id, version, context, number, is_first, score, total (3), completed_at, and results. Each result holds question_id, position, prompt, choices, selected_choice, correct_choice, is_correct, and explanation. Context snapshots title/topic/subject/examination/unit_key at completion.

Only the server scores. Attempts are saved in one transaction. Database uniqueness protects candidate/submission ID and candidate/stable unit/attempt number. A user-row lock serializes a candidate's requests on PostgreSQL. SQLite may return a busy error under simultaneous writes; use the retry response. Actual concurrent PostgreSQL verification remains a hosted-pilot prerequisite, not a completed desktop check.

A completed unit is a distinct stable post with an accepted quiz, regardless of score. First-play percentage is the sum of scores from number=1 attempts divided by their total questions, rounded to one decimal. Repeats, including a replacement version of the same unit, do not change first-play scores. These are private learning-history measures, not engagement analytics or proof of learning gains.

Results retain their original question text, key, explanation, and context. Withdrawing/replacing content blocks new quizzes and submissions for that old version. Identical retries look up an existing owned submission first and can return it after withdrawal. Original results stay readable in private history. Supported app/admin operations cannot edit or delete attempts.

The phone keeps unfinished choices in a separate account-bound document store, at most 20 drafts, using two alternating copies so an interrupted write keeps the previous valid copy. It sends only on an explicit tap, never as background offline synchronization. Scored results are held briefly in memory for immediate display and fetched from the server for later history; keys are not written to the content cache. Native file behavior still needs [phone checks](../quiz-phone-guide.md).

## Entertainment-first entry flow

Quiz endpoints and server scoring are unchanged. The phone now enters quizzes through optional in-feed dare cards, not a button on every post. Skipping creates no attempt. Unfinished answers are reachable under Settings → My progress. The visible label is posts tried; completed_units remains the existing API field counting stable posts with an accepted quiz. No other user or challenge is created by accepting a current solo dare; two-person challenges remain Milestone 7.
