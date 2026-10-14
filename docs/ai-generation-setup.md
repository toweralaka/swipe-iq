# Generate a text draft from admin

AI-1 adds text drafts and optional questions. Images, memes, and videos are later stages. The AI creates a new draft; a human still checks and publishes it.

## Prepare the backend

1. Open a terminal in swipe-iq/backend. Install this milestone's pinned dependencies:

   ~~~powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe manage.py migrate
   ~~~

2. In your private backend/.env, configure:

   ~~~dotenv
   AI_GENERATION_ENABLED=true
   OPENAI_API_KEY=replace-with-your-private-api-key
   AI_TEXT_MODEL=your-enabled-text-model
   AI_DAILY_JOB_LIMIT=5
   AI_REQUEST_TIMEOUT=60
   ~~~

   Use an OpenAI API project you control, with funding and a text model that supports the Responses API and Structured Outputs. The model value must be an actual model ID available to your account, not the placeholder above. Keep the key in backend/.env, never mobile/.env, Git, screenshots, or chat. The app does not fetch source links or use candidate information in prompts.

   Generation is off by default. A missing key/model, disabled flag, or invalid quota prevents requests. The settings check does not prove the key has funding or access to the chosen model; the controlled live check below establishes that.

3. Start Django and leave this terminal open:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
   ~~~

4. Open http://127.0.0.1:8000/admin/ on the computer. Sign in as a staff user. A local superuser has the needed permissions. For another staff user, grant:

   - Generation: Can request AI content drafts and Can view content generation request.
   - Editorial: the existing add/view/change permissions needed to edit drafts. Give publication permission only to a reviewer who should publish.

## Request a draft

1. Open **Generation → Content generation requests → Add**.
2. Choose a topic. The topic label includes its subject and exam; those values become part of the saved source snapshot.
3. Enter one learning objective and the idea you want. For example, ask for a memorable membrane/bouncer analogy that clearly explains its scientific limit. This is a content brief, not verified teaching material.
4. Enter the official syllabus link and relevant excerpt. Paste the checked teaching reference and a short source excerpt or your checked notes. A URL alone is not enough: the worker does not open links. Do not paste whole books or candidate details.
5. Leave the format as **Text**. Leave **Generate three quiz questions** unchecked for a normal post, or tick it for an optional dare-ready quiz.
6. Click **Generate draft**. The page opens a saved request with **Queued** status. It has not contacted OpenAI yet. Repeated submission of this same form points to the same job. To request a different post, open a new form.

## Run the worker

A worker is a separate program that does the slow generation work while the admin page stays usable.

1. Open a second terminal in swipe-iq/backend. Check the provider account and usage settings before starting: processing queued jobs can incur API charges.
2. For your first controlled live check, queue just one request and run:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py generation_worker --once
   ~~~

   This processes at most one queued request or one already-saved response. If older jobs are queued, the oldest goes first. Inspect the queue before running it.

3. Refresh the request page in admin. It should move through **Generating** and **Response saved** to **Draft ready**. Page refresh reads the database; it does not start another generation.
4. For normal local use after the live check passes, run:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py generation_worker
   ~~~

   Leave it open. It checks the queue every two seconds when idle. Use Ctrl+C to stop. Restart the worker after changing code or backend/.env.

Only one local worker can hold the process lock. Do not delete a live .generation-worker.lock file. The operating system releases the lock when the process exits; an empty/stale file does not mean a worker is running. The local lock is not a multi-host queue coordinator. Run exactly one configured worker; PostgreSQL/multi-host behavior needs verification before hosting.

The daily quota is shared by all staff and uses Nigeria calendar days. The example permits five new jobs per day. Failed or uncertain requests also use a slot; refreshing or resubmitting the same request does not. The quota limits job requests, not a guaranteed currency bill. Each call also has a 4,000-output-token cap and automatic SDK retries are disabled. A queued job retains the model chosen when it was submitted.

## Review and publish

1. When **Draft ready** appears, click **Review the unreviewed draft** on the request page.
2. Read and edit the post. Check the saved AI verification notes, source material, and each question/answer if requested. AI wording and structured output are not proof of correctness.
3. The new version is a draft with one card. All human-review confirmations remain unset. No media is generated in AI-1.
4. Complete the existing [editorial review](content/editorial-workflow.md), add review notes, and explicitly publish. Saving alone does not publish.
5. A post may have zero questions or exactly three. One or two questions cannot be published. A zero-question post appears in the normal feed and subject list but never supplies a dare.
6. To add questions to already published content, use a reviewed replacement draft. AI-1 does not regenerate existing posts or overwrite human edits.

## Read failures safely

| Status/message | What to do |
| --- | --- |
| Generation off or missing key/model | Fix private backend settings, restart Django/worker, and submit again. No job is accepted until configuration is valid. |
| Queued | Start the worker. Django alone does not process jobs. |
| Daily limit reached | Wait until the next Nigeria day. Opening more browser tabs does not bypass it. |
| Failed | Read the safe message. Check model access, funding, credentials, or source/topic changes. A new form is a new request and may incur another charge. |
| Needs checking, no saved response | The reply may have been lost after submission. Check provider activity and usage before asking again. The worker will not resend this job automatically. |
| Needs checking, saved response present | Inspect the retained result. Invalid or mismatched output is not imported. Usable text can be copied into a manually authored draft and reviewed; do not edit job status through SQL to force it through. |
| Interrupted worker | Restart it. Requests interrupted before a confirmed save become Needs checking. A confirmed saved response can finish import without another provider call. |
| Topic changed | Open a new request with the current topic. A saved result is not silently reassigned to changed exam/subject/topic context. |

Job pages and generated results are private staff records. Errors do not print API credentials or raw provider error bodies. The only student API change is quiz_available; it never includes generation inputs, questions, or keys in the feed.

## Verify this milestone

Automated checks use mocked provider responses and make no paid calls. Complete these separate live/human/phone checks:

1. Generate one text post without questions using checked source material. Record model ID, job ID, status, and provider usage; never record the key.
2. Confirm one unreviewed draft was created and nothing was auto-published. Review it as a human, publish explicitly, and check that it appears on the phone with no dare drawn from it.
3. When ready for a second live check, request a post with questions. Confirm exactly three sensible questions, correct keys/explanations, and human review before publication.
4. Confirm the published quiz-ready post can supply an optional dare and the feed still works when all other posts have no questions. Check saved/offline pages and old cached posts after refresh.
5. Resubmit the original form or refresh the job page. Confirm it does not add another job, draft, or paid provider call.
6. Check another staff user without generation/view permission cannot request or inspect results. Confirm the normal phone account cannot access staff job pages.

Record failures before accepting AI-1. Image/meme/video generation remains unimplemented and needs separate stage approval.
