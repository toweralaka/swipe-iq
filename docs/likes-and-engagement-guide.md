# Likes and the pilot report

Likes let you say a post made you smile or interested you. Your like is private. Other candidates do not see it or a public like count. Likes do not change the random feed order.

## Update your local app

1. Open a terminal in swipe-iq/backend.
2. Add the new database tables:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py migrate
   ~~~

3. Start Django:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
   ~~~

4. Open a second terminal in swipe-iq/mobile. Stop an old Expo process with Ctrl+C, then run:

   ~~~powershell
   npm.cmd start -- --go --clear
   ~~~

5. Open the app on the phone, sign in, and choose Biology (JAMB). See [sign-in setup](authentication-setup.md) if needed. No new mobile package is needed for this milestone.

## Like a post

1. Open a published post in the feed. Wait for **Checking…** to finish.
2. Tap **♡ Like**. The button waits for the server before showing **♥ Liked**. While it waits, more taps are disabled.
3. Tap **♥ Liked** to remove the like.
4. You can also like the post inside **Read more**. Both places show the same saved state.
5. Restart or sign back into the same account. The app checks your saved like again. Clearing phone copies does not delete server likes. A corrected post keeps the like when the reviewer retains its stable card identity.

If the reply is lost, the app keeps the last confirmed display and shows an error. Tap **Retry like check** to ask the server what was saved. It does not send another change blindly. Repeated like requests cannot create extra likes.

You need a connection to change likes. Saved offline posts show **Connect to like**. No like or activity is queued for later upload. When you reconnect, the app checks the current state. Signing in as another candidate does not carry your like display into that account.

## What the pilot counts

The pilot records three simple signals while connected:

- A post stayed mostly visible for one second while the feed was open and the app was active.
- An optional dare stayed visible for one second.
- You tapped **I’m game ✦**. A quick tap also counts the dare as shown, even if it happened before the one-second mark.

Each signal counts at most once per candidate, stable post, and day. Days use Nigeria time (Africa/Lagos). Revisiting or retrying the same signal that day does not add to its count. A dare can be shown several times in a day, but this report still counts that candidate/post once. These are daily unique signals, not raw impression or tap totals.

Skipping still lets you scroll without submitting anything. The app does not send a skip event. Scrolling quickly past, reading offline, or a failed delivery may leave no view record. Downloading or playing media is not counted as understanding it. Quiz totals come from accepted server attempts, not from a phone claiming completion.

## Admin: download the report

1. Open http://127.0.0.1:8000/admin/ on the computer and sign in with your staff account.
2. A local superuser already has the required permissions. For another staff user, grant **Engagement → engagement event → Can view engagement event** and **Can export aggregate engagement reports** under that user's permissions. Save the user. Do not grant these to candidates.
3. Open **Engagement → Engagement events**.
4. Click **Download 7-day aggregate report**. An empty pilot can produce an empty report; it does not generate sample activity.
5. Open the downloaded JSON file in a text editor. JSON is a text file with labelled lists and numbers. Keep real pilot reports outside the Git project.
6. For another window, use the same download address with ?days=14, for example /admin/engagement/engagementevent/export/?days=14. Allowed windows are 1–90 days, including today.

The report contains:

| Section | Meaning |
| --- | --- |
| content | Daily view counts, unique viewers, and daily dare-shown/accepted counts, grouped by stable post, exam, subject, topic, and media type. |
| active_likes_as_of_now | Current active likes per stable post, including likes made before the chosen report window. It is a snapshot, not the number of new likes during that window. |
| quiz_summary | Accepted attempts by post/version in the window, unique candidates, first plays, repeat practice, and first-play correct/total questions. |
| daily_active_candidates | Candidates with at least one received engagement event that day. Candidates who only read offline or whose events failed can be missing. |
| candidates_active_on_multiple_days | Candidates with received events on two or more days in the window. It does not identify them. |

The download excludes emails, usernames, account IDs, credentials, selected answers, and answer keys. It contains group counts, post identifiers, and teaching-topic labels. Different media/topic buckets can include the same viewer, so do not add their unique-viewer counts as though they were different people. Small counts are internal pilot evidence, not a public claim of anonymity.

Likes show interest, not learning gains. Missing network events mean these counts can understate use. Do not present them as exact time spent, proof that a joke worked, or proof of improved exam scores.

## Record phone and admin checks

Desktop checks do not establish real-phone behavior. Record phone model, Android version, build type, steps, and pass/fail notes for:

- Like, unlike, repeated taps, and matching state in Read more.
- Restart/sign-in persistence and separation between two invited accounts.
- Lost reply: interrupt the connection near a like request, reconnect, then use Retry like check. Confirm the server has at most one like record.
- Offline posts: liking is disabled and nothing changes later without a new tap.
- Withdrawn/replaced content: hidden posts cannot receive new likes/events; a corrected post with the retained identity keeps its like.
- Larger text and a small screen: Like, Read more, retry messages, and media controls remain reachable.
- Leave a visible post open, then view it again. The report counts one view that day. Try a dare; skipping does not create a quiz attempt.
- Prefetched/offscreen items, Search, Read more overlays, and backgrounding do not create new feed-view signals. Returning to an already counted post that day does not add a second record.
- Staff report download works with permission, fails without it, and contains no account details. Use test accounts and checked sample content; do not publish drafts just to fill a report.

For an interest ratio, use content.viewers_with_active_like divided by that same row’s unique_viewers, when viewers is above zero. This means current likes among observed viewers in the report window. It does not measure when the like was made. Do not divide all-time active_likes_as_of_now totals by seven-day viewers. Offline/missing observations can still bias this ratio.
