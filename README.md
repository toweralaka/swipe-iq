# Swipe-IQ

Swipe-IQ is a fun feed for Nigerian JAMB Biology candidates. Funny posts weave Biology into a relaxing scroll, using text, images, audio, or video. Staff can now request AI text drafts from admin or enter content manually. A human checks each draft before an admin publishes it.

The phone app now lets invited users sign in, tick subjects such as Biology (JAMB), and swipe through a colourful full-screen feed. Search finds posts within the chosen subjects. Data saver starts on. Viewed text and loaded media are saved on the phone, up to 100 MB. Posts appear in a random mix, with no lesson sequence. Occasional in-feed dares offer an optional three-question solo play. Swipe past them whenever you like. Scores and explanations are private. Private likes now let users show interest. Staff can download an aggregate pilot report. Friend challenges will come in a later milestone. New posts have one content card; carousels are future work.

The code has desktop checks. Real email links in an installed Android app and the media, offline, quiz, and like features still need phone checks. See [milestone status](docs/milestones.md).

## Start here

- [Set up the backend and phone app](docs/setup.md)
- [Sign in using a local test link or real email](docs/authentication-setup.md)
- [Use and test the phone feed](docs/feed-phone-guide.md)
- [Play quizzes and check progress](docs/quiz-phone-guide.md)
- [Use likes and download the pilot report](docs/likes-and-engagement-guide.md)
- [Generate an AI text draft in admin](docs/ai-generation-setup.md)
- [Review and publish content](docs/content/editorial-workflow.md)
- [Approved plan](docs/implementation-plan.md), [architecture](docs/architecture.md), and [student API](docs/api/student-access.md)

Use Python 3.14 and Node 24. The setup guide explains how to install the project and fill in the private environment files.

## Admin: make a lesson available

These commands use PowerShell. Start inside the swipe-iq folder after completing [setup](docs/setup.md).

1. Open the backend folder and prepare the database:

   ~~~powershell
   Set-Location backend
   .\.venv\Scripts\python.exe manage.py migrate
   ~~~

2. To add five sample lessons, run:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py seed_sample_content
   ~~~

   They are drafts. Running this again keeps existing lessons and your edits.

3. Create a staff account if you do not have one:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py createsuperuser
   ~~~

4. Start the server and leave this terminal open:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
   ~~~

5. Open http://127.0.0.1:8000/admin/ on the computer. Sign in with your staff account. Under **Editorial → Learning unit versions**, open a draft.
6. Check that the topic belongs to **JAMB Biology**. Read the cards and questions, fix mistakes, and enter the teaching reference you checked. Each new post needs exactly one content card. Questions are optional: leave them empty or add exactly three for dares. Each question needs four choices and an explanation. The feed shows the post. Its questions can appear in a separate optional dare.
7. For media, add a file under **Media assets** and attach it to a card. Add the description, transcript, captions, source, and file details required for that format. Play or view it before confirming its details. See [media preparation](docs/content/media-preparation.md) for the limits.
8. Complete the six review checks: accuracy, syllabus, humour, accessibility, rights, and references. Add your review notes and save. Confirm only checks a human has actually done.
9. Return to the lesson list, tick the reviewed draft, choose **Publish selected reviewed drafts**, and click **Go**. Your account needs permission to publish; a local superuser has it.
10. Check that the status says **Published**. If there is an error, fix the listed problem and try again. Clicking Save alone does not publish a lesson.
11. Under **Accounts → Invitations**, add the student's email and leave it active. Students use email links, not your staff username and password.

A published post in an active exam can now appear in the phone feed. Refresh at the end for a new random mix. Existing multi-card content is preserved; its cards still appear individually. Published versions are locked. To correct one, make a replacement draft, review it, and publish it. The [editorial guide](docs/content/editorial-workflow.md) explains the full process.

## Why a new subject may not appear

**The app only lists subjects with at least one available published post in an active examination.** Adding a subject in admin alone is not enough. This keeps users from choosing subjects with empty feeds.

To make a subject appear:

1. Under **Editorial → Examinations**, check that its examination is active.
2. Under **Subjects**, check that the subject belongs to that examination.
3. Under **Topics**, add a topic belonging to the subject.
4. Create a learning unit and draft version using that topic. Add one content card and either no questions or exactly three, then complete the human review described above.
5. Run **Publish selected reviewed drafts** and confirm the status is **Published**. Drafts and withdrawn versions do not qualify. A subject disappears if it has no remaining available published content.
6. While the phone is connected, open **Settings → Change my subjects** to reload the list. If it is already open, leave it and reopen it. **Offline · showing saved subjects** means the list may be out of date.

For developers: this filtering happens in the backend's SubjectList in backend/editorial/student_api.py. It uses available_versions(), which restricts content to the latest published version per unit in an active exam. Creating a subject does not require rebuilding Expo Go; the app needs a fresh response from the backend.

## Student: open your feed on the phone

1. Connect the Android phone and computer to the same private Wi-Fi.
2. On the computer, run **ipconfig** and find the Wi-Fi IPv4 address. Put this address in **DJANGO_ALLOWED_HOSTS** in backend/.env. Set **EXPO_PUBLIC_API_URL=http://YOUR_COMPUTER_WIFI_IPV4:8000** in mobile/.env. Use the computer's address; localhost on the phone means the phone itself. Keep real .env files private.
3. Start the backend with step 4 above. Open a second terminal inside swipe-iq and run:

   ~~~powershell
   Set-Location mobile
   npm.cmd start -- --go
   ~~~

4. Open Expo Go on the phone and scan the QR code. If it reports a version problem, follow [setup](docs/setup.md).
5. Tap **Check server connection**, then **Check connection**. A successful check means the app can reach the backend. Return to the home screen.
6. Ask the admin to invite your email. Enter it and tap **Send my login link**. For local testing, use the [local email steps](docs/authentication-setup.md#local-development-without-an-email-provider): the default setup saves the message on the computer rather than sending it to your inbox.
7. Open the link using the method in that guide and tap **Confirm sign-in**. Check that your email appears on the home screen.
8. Tick **Biology (JAMB)** on the subject screen, then tap **Let’s scroll**. Your feed opens right away. Swipe up for another post. Only subjects with published content appear; extra exams such as SSCE are future work.
9. Read each post. Tap **♡ Like** to save a private like, or **♥ Liked** to remove it. Wait for confirmation; if it fails, use **Retry like check**. Likes need a connection and do not change your feed order. Tap **Read more** for the full text, transcripts, sources, and the idea behind the joke. Tap **Search**, enter a word such as cells, and submit to find related posts in your subjects. With data saver on, tap **Load image**, **Load audio**, or **Load video** to fetch a file. Its size is shown first. Audio and video need a separate tap on **Play** and stop when you leave the card or app. Text and transcripts remain readable without loading the file.
10. An occasional purple dare card appears between posts. Tap **I’m game ✦** to try three questions, or swipe past it / tap **Keep scrolling ↑**. Playing is optional. You need a connection to submit. Saved answers and the submission ID make retries count only once. Friend challenges are clearly marked as coming later.
11. Tap **My progress** on the result page or under **Settings** to resume unfinished dares and see posts tried, first-play scores, and earlier results. Repeat practice is labelled separately.
12. Tap **Subjects** to change your mix. Tap **Settings** to change data saver, clear saved posts/files, or sign out. Data saver off loads visible images automatically; audio and video still wait for you. Clearing saved posts keeps unfinished quiz answers. Signing out removes unfinished answers, but completed history stays on the server.

If no subjects or posts appear, ask the admin to check publication and the exam's active setting. Refresh the feed after publishing. For slow Wi-Fi, offline reading, and playback checks, follow the [phone feed guide](docs/feed-phone-guide.md).

## Admin: see interest and activity

Open **Engagement → Engagement events** in the staff admin, then click **Download 7-day aggregate report**. A superuser has access; other staff need view-event and export-report permissions. The report includes grouped views, likes, optional dare choices, and quiz totals without candidate emails or account IDs. See the [report guide](docs/likes-and-engagement-guide.md) for steps and how to read the numbers. Failed or offline events are not uploaded later, so these are partial pilot counts, not proof of learning.

## Admin: generate a text draft

Open **Generation → Content generation requests → Add**. Choose a topic, enter the desired idea and checked syllabus/teaching excerpts, and optionally tick **Generate three quiz questions**. Start the separate worker to process the request, then open the draft, review it, and publish explicitly. Follow [AI generation setup](docs/ai-generation-setup.md) for the backend API key/model, daily limit, permissions, worker commands, and failure recovery.

AI-1 generates new text posts only. Images, memes, and videos are later stages. Zero-question posts can be published and liked, but cannot supply dares. A provider account/model configuration and controlled live check are still needed; mocked tests do not establish live generation quality.

### More sample drafts

To add five JAMB Government and five JAMB Chemistry posts, run `.\.venv\Scripts\python.exe manage.py seed_jamb_subjects` from backend. Each post has one text card and no quiz. Review and publish them in admin before users can see them. See [sample steps](docs/content/jamb-subject-samples.md).

## Public landing page

Start the Django backend and open http://127.0.0.1:8000/ in a browser. The page describes Swipe-IQ and shows disabled Google Play download buttons labelled Coming soon. No store link is active. The page uses no external fonts, scripts, or images. Its template is backend/health/templates/health/landing.html.
