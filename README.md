# Swipe-IQ

Swipe-IQ helps Nigerian JAMB Biology candidates revise with short lessons. Lessons can include text, images, audio, and video. AI drafts the content; a human checks it before an admin publishes it.

The phone app now lets invited users sign in, tick subjects such as Biology (JAMB), and swipe through a colourful full-screen feed. Search finds posts within the chosen subjects. Data saver starts on. Viewed text and loaded media are saved on the phone, up to 100 MB. Quizzes, likes, and challenges will come in later milestones.

The code has desktop checks. Real email links in an installed Android app and the new media/offline features still need phone checks. See [milestone status](docs/milestones.md).

## Start here

- [Set up the backend and phone app](docs/setup.md)
- [Sign in using a local test link or real email](docs/authentication-setup.md)
- [Use and test the phone feed](docs/feed-phone-guide.md)
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
6. Check that the topic belongs to **JAMB Biology**. Read the cards and questions, fix mistakes, and enter the teaching reference you checked. Each lesson needs 1–3 cards and exactly three questions. Each question needs four choices and an explanation. The phone shows the cards now; quiz screens come later.
7. For media, add a file under **Media assets** and attach it to a card. Add the description, transcript, captions, source, and file details required for that format. Play or view it before confirming its details. See [media preparation](docs/content/media-preparation.md) for the limits.
8. Complete the six review checks: accuracy, syllabus, humour, accessibility, rights, and references. Add your review notes and save. Confirm only checks a human has actually done.
9. Return to the lesson list, tick the reviewed draft, choose **Publish selected reviewed drafts**, and click **Go**. Your account needs permission to publish; a local superuser has it.
10. Check that the status says **Published**. If there is an error, fix the listed problem and try again. Clicking Save alone does not publish a lesson.
11. Under **Accounts → Invitations**, add the student's email and leave it active. Students use email links, not your staff username and password.

A published lesson in an active exam can now appear in the phone feed. Published versions are locked. To correct one, make a replacement draft, review it, and publish it. The [editorial guide](docs/content/editorial-workflow.md) explains the full process.

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
9. Read each post. Tap **Read more** for the full text, transcripts, sources, and the idea behind the joke. Tap **Search**, enter a word such as cells, and submit to find related posts in your subjects. With data saver on, tap **Load image**, **Load audio**, or **Load video** to fetch a file. Its size is shown first. Audio and video need a separate tap on **Play** and stop when you leave the card or app. Text and transcripts remain readable without loading the file.
10. Tap **Subjects** to change your mix. Tap **Settings** to change data saver, clear saved posts/files, or sign out. Data saver off loads visible images automatically; audio and video still wait for you.

If no subjects or posts appear, ask the admin to check publication and the exam's active setting. Refresh the feed after publishing. For slow Wi-Fi, offline reading, and playback checks, follow the [phone feed guide](docs/feed-phone-guide.md).
