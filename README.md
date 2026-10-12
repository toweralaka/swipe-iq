# swipe-iq

Educational revision for Nigerian JAMB Biology candidates. The foundation provides a Django REST API health endpoint and an Expo Android connection screen. Milestone 2 adds staff-only editorial drafts, media, review, publication, and immutable versions. Milestone 3 adds invited email-link login and a protected student content API. The phone lesson feed remains planned.

## Start here

- [Setup and physical Android verification](docs/setup.md)
- [Approved implementation plan](docs/implementation-plan.md)
- [Milestone status and remaining checks](docs/milestones.md)
- [Architecture](docs/architecture.md)
- [Staff editorial workflow](docs/content/editorial-workflow.md)
- [Email login and physical Android checks](docs/authentication-setup.md)
- [Student API contract](docs/api/student-access.md)

Use Python 3.14 and Node 24. Follow the setup guide for isolated dependencies, environment configuration, and checks. No cloud account is needed for Milestone 1.

## Why published content is not showing on the phone yet

The phone app now supports invited email-link sign-in and a connection check. It does not yet have a lesson feed. Publishing makes a reviewed lesson available through the protected student API; the phone needs Milestone 4 screens to display it.

The student API/login code is Milestone 3; real email-to-installed-app acceptance remains pending. The phone feed and media display are Milestone 4. Students cannot browse published lessons in the app until those screens are implemented.

## Admin: prepare and publish a lesson

Complete the [initial setup](docs/setup.md) first. The commands below use PowerShell, starting inside the swipe-iq folder.

1. Open a terminal and enter the backend folder:

   ~~~powershell
   Set-Location backend
   .\.venv\Scripts\python.exe manage.py migrate
   ~~~

2. To add the five sample lessons, run:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py seed_sample_content
   ~~~

   These start as unreviewed drafts. Running the command again preserves existing lessons and edits.

3. If you do not already have an admin account, create one:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py createsuperuser
   ~~~

   Choose your own username and password. This account is for staff; do not give its credentials to students.

4. Start the backend and leave this terminal running:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
   ~~~

5. On your computer, open http://127.0.0.1:8000/admin/ and sign in. Under Editorial, open Learning unit versions and select a draft.

6. Check that its topic belongs to **JAMB Biology**. Subjects are grouped by examination, so JAMB Biology and future SSCE Biology are separate. Read its cards and questions. Correct mistakes, confirm its JAMB objective, and enter the checked teaching reference. Each unit needs 1–3 cards numbered from 1 and exactly three questions numbered 1–3, with four choices and an explanation each.

7. If the lesson uses an image, audio, or video, first add it under Media assets. Supply its description/transcript/captions, attribution, and required size/duration details. Preview the file and confirm its metadata only after checking it. Attach the asset to the lesson's card. Text-only lessons do not require an attachment.

8. Complete the six review confirmations: accuracy, syllabus, humour, accessibility, rights, and references. Add review notes and click Save. Only confirm checks actually performed by a human reviewer.

9. Return to the Learning unit versions list. Tick the box beside the lesson, choose Publish selected reviewed drafts from the Action menu, and click Go. Your staff account needs publication permission; a local superuser has it.

10. Confirm the lesson's status is Published. If publication fails, read the displayed message, fix the missing requirements, save, and try again. A normal Save leaves a lesson as a draft.

The lesson is now approved in the database and available to signed-in candidates through the student API, ready for the future phone feed. It is not currently visible to students on the phone. For corrections, create a replacement draft and review it again; published versions are locked. See the [full editorial walkthrough](docs/content/editorial-workflow.md).

## Phone: what you can access now

1. Connect the Android phone and computer to the same private Wi-Fi.
2. Find the computer's Wi-Fi IPv4 address with ipconfig. In backend/.env, include that address in DJANGO_ALLOWED_HOSTS. In mobile/.env, set EXPO_PUBLIC_API_URL=http://YOUR_COMPUTER_WIFI_IPV4:8000. Use the computer's address, not the phone's address or localhost. Keep real .env files private.
3. Start the backend using step 4 above. In a second terminal, starting inside swipe-iq, run:

   ~~~powershell
   Set-Location mobile
   npm.cmd start -- --go
   ~~~

4. Open Expo Go on the phone and scan the terminal QR code. Follow the [setup guide](docs/setup.md) if an SDK/version message appears.
5. Tap Check connection. Connected to Swipe-IQ API confirms that the phone can reach the server. It does not mean lessons can be displayed yet.

For a **staff-only preview on a phone**, open http://YOUR_COMPUTER_WIFI_IPV4:8000/admin/ in the phone browser, sign in with your own staff account, and open Learning unit versions. You can inspect the lesson cards/questions and permitted media there. This is the admin interface, not the student app. Use trusted private Wi-Fi for this local development setup.

Changing Wi-Fi settings or republishing a lesson will not make a student feed appear in the current app.

## Student sign-in: Milestone 3

1. Ask the admin to add your email under Accounts → Invitations.
2. Open Swipe-IQ and enter that email, then tap Send login link.
3. For local development, follow the [private email-outbox walkthrough](docs/authentication-setup.md#local-development-without-an-email-provider). A development-only paste option lets you test before a real email provider is configured.
4. With the configured domain, real email, and installed Android build, open the email link on the phone and tap Confirm sign-in. This physical-device route still needs acceptance testing.
5. The app shows your signed-in email. You can sign out and restore your session after restarting the app.

The **student lesson feed is still planned**: in Milestone 4, choose JAMB, then Biology and a topic, and browse published lessons with optional media. Quiz-taking arrives in Milestone 5.
