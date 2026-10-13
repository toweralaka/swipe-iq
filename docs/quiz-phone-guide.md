# Try an optional dare on your phone

A dare is an optional three-question solo play offered between posts. It does not appear after every post and never blocks scrolling. Friend challenges are coming in a later milestone. The server checks your answers. You see the correct answers and explanations only after submitting.

## Prepare the app

1. Open a terminal in swipe-iq/backend.
2. Update the database:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py migrate
   ~~~

3. Start the backend:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
   ~~~

4. In a second terminal, open swipe-iq/mobile. Start Expo:

   ~~~powershell
   npm.cmd start -- --go
   ~~~

5. Open the app on your Android phone. Follow [sign-in setup](authentication-setup.md) if needed. The phone and computer must be on the same Wi-Fi for this local setup.
6. Ask the admin to publish a reviewed post with exactly three questions. [These steps](../README.md#admin-make-a-lesson-available) explain how. Drafts will not appear.

## Play and see your progress

1. Sign in and tick Biology (JAMB). Tap **Let’s scroll**.
2. Scroll through your mix. When a purple dare card appears, tap **I’m game ✦**, or swipe past / tap **Keep scrolling ↑**. The first dare appears after 3–7 content items; later ones have 5–9 content items between them. A short feed may end before any dare appears.
3. Tap one answer for each question. A green answer is your selection; it does not mean the answer is correct. There is no timer.
4. Tap **Show my score**. Stay connected while submitting. The app shows your score out of three, your answers, the correct answers, and explanations.
5. Tap **Play again** for practice. The first completed play is marked **First play**. Later plays of the same post are marked **Practice**. A corrected replacement of that post is still the same post for progress.
6. Tap **My progress**, or open **Settings → My progress** from the feed. You can open earlier results and load more history.

“Posts tried” counts posts where you chose to submit a dare, even if you scored zero. This is optional play history, not a lesson checklist. The first-play percentage uses only your first completed quiz for each post. Repeating an easy quiz does not raise this number. These counts describe activity and quiz answers; they do not prove improved exam performance.

## If the connection drops

- Each choice is saved on this phone. If saving fails, the app reports it and keeps the previous saved choice. Make space on the phone and try again.
- Before contacting the server, the app saves all three answers and a submission ID. Once submission starts, the answers are fixed until that submission succeeds.
- If the reply is lost, tap **Retry saved submission**. The same answers and ID are sent again. The server returns the recorded result if it already accepted them; it does not count another play.
- You can close the app and open **Settings → My progress → Resume dare** or **Retry saved dare** to recover those answers. You do not need to find the same random feed position again. Use an installed preview build to test a true offline restart; Expo Go may need the development server to start.
- The app never submits automatically when Wi-Fi returns. Opening a quiz, submitting, and loading saved results from the server need a connection. Unsubmitted choices survive a restart, but question text is fetched again when you reopen the quiz.
- If the admin withdraws or replaces a post before the server accepts your answers, you cannot submit a new attempt for that old version. Refresh the feed and open the current post. Previously accepted results stay in your history. Retrying a previously accepted submission still returns its original result.
- **Clear saved posts and files** keeps unfinished quiz answers. Signing out, session expiry/rejection, and switching accounts remove them. Completed results remain on the server for the same account.
- The phone keeps at most 20 unfinished quizzes. Finish one before starting a 21st. These small answer files are separate from the 100 MB content cache. They contain selected choices and IDs, not passwords, email links, question text, or answer keys.

## Record the phone results

Desktop tests have passed. These phone checks are still open:

- Skip a dare and confirm scrolling continues without submitting anything. There should be no quiz button at the end of ordinary posts or inside Read more.
- Submit three answers and compare the score/explanations with the reviewed questions.
- Play again. Check that practice appears separately and the posts-tried count stays the same.
- Leave halfway through, close/reopen the app, and confirm your choices remain.
- Interrupt the connection around submission. Restore it and retry. Confirm one history entry for that submission.
- Sign out and sign in as another invited user. Confirm the second user cannot see the first user's answers, results, or progress.
- Restart and sign back in as the original user. Confirm completed history is still available.
- Try a saved dare whose post was withdrawn and confirm new submissions are blocked while earlier results remain available.
- Try larger phone text and a small screen. Confirm all choices, explanations, and buttons can be reached by scrolling.

Record the phone model, Android version, build type, steps, expected result, and actual result. Report failures before accepting this milestone.
