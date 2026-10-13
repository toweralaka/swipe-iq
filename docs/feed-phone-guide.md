# Use your swipe feed on Android

The app now opens a subject picker after sign-in. Choose your mix, then swipe through short, colourful posts. You do not need to open exam, topic, and lesson menus first.

## Start the updated app

1. Complete [setup](setup.md). If you installed an earlier milestone, run npm.cmd ci in mobile/ to install the media packages.
2. Restart Django so the new feed/search route is available. From backend/:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
   ~~~

3. Stop Expo with Ctrl+C. From mobile/, start it again:

   ~~~powershell
   npm.cmd start -- --go --clear
   ~~~

4. Keep the computer and phone on the same private Wi-Fi. Open Expo Go and scan the QR code. The first bundle may take a minute.
5. If you use an installed development/preview build made before the media packages were added, it needs a new build. Restarting Expo cannot add native packages to an old installed app. See [login setup](authentication-setup.md). No cloud build has been run for you.
6. Sign in using an invited email. Follow the [local email steps](authentication-setup.md#local-development-without-an-email-provider) if you do not have a real email service yet.

Before trying content, ask a human reviewer to publish a checked post under JAMB Biology. Use [media preparation](content/media-preparation.md) for permitted image, audio, and video examples. Sample drafts are not automatically approved or published.

## Pick your subjects

1. After sign-in, the app shows **Pick your kind of fun**.
2. Tick the checkbox beside **Biology (JAMB)**. Each label includes the exam so future Biology courses cannot be mixed up.
3. Pick at least one subject. The app supports up to 20 choices, but JAMB Biology is the current MVP.
4. Tap **Let’s scroll**. Your feed opens immediately.

Only subjects with available published posts appear. Your choices are remembered in this account's phone cache. Clearing saved copies, signing out, or the phone removing cached files can reset them. Choices are not shared across phones.

## Swipe and explore

- Swipe **up** for the next post; swipe down to go back through loaded posts. Posts are mixed randomly within your subjects, with no lesson order. Refresh at the end for a new online mix.
- New posts have one content card. Carousels are future work. Earlier multi-card content is preserved and each old card is shown separately.
- Purple dare cards occasionally appear between posts. Swipe past, tap **Keep scrolling ↑**, or tap **I’m game ✦** for an optional solo play. Friend challenges are coming later. Dares do not appear after every post.
- Each post fills the feed area, with a different colour as you move through it.
- Tap **Read more** for the full text, transcripts, sources, and the idea behind the joke. Long text is shortened in the swipe view so buttons remain reachable.
- Tap **Subjects** to change your mix. Tap **Settings** for data saver, saved copies, and sign-out.
- More text loads as you approach the end. A finished feed says **You’re all caught up**. This is a small reviewed collection, not an endless recommendation service.

A bright layout does not make every joke work. Tell the reviewer when a post is confusing or unfunny; the reviewer can prepare a corrected version.

## Find something specific

1. Tap **Search** at the top of the feed.
2. Enter a word or short phrase, such as cells, membrane, or energy. Use up to 120 characters and 10 words.
3. Tap **Find my next aha** or the keyboard's search button.
4. Swipe through matching posts. Search looks in titles, card text, topic names, subject names, and learning aims, within your chosen subjects.
5. Tap **Clear** to return to your normal mix.

Search happens when you submit, rather than sending a request for every letter. If nothing matches, try a shorter word. This is word matching; it does not guess synonyms or generate answers.

## Load media without wasting data

Data saver starts **on**. Text and file details arrive first. The file waits for you to tap Load.

1. Read the file's type, size, and length.
2. Tap **Load image**, **Load audio**, or **Load video** and wait for it to finish.
3. Audio and video then need a separate tap on **Play**. They never start by themselves.
4. Swipe away, open Search/Read more, leave the feed, or put the app in the background. Playback should pause.
5. If you would rather read, open **Read more** for the transcript or image description. Video captions appear at their checked times during playback.

On small screens or with larger Android text, the feed shows **Open image/audio/video** instead of squeezing controls into the post. Tap it to open the full view, then Load and Play. Scrolling media out of that view should pause playback too.

In **Settings**, turn data saver off if you want visible images to load automatically. Audio and video still need Load and Play. The setting stays on this phone when you restart.

## Try saved posts offline

A cache is a saved copy the app can reuse. Feed text, subject lists, and completed media downloads share a 100 MB limit and at most 200 entries. The app removes items used least recently when space runs out. Android can also remove these files when it needs space.

1. While connected, pick subjects and view a few posts. Load the media you want to test.
2. Leave the app open, then turn off Wi-Fi and mobile data.
3. Change subjects and continue with the same saved choices, or repeat a search you already loaded. Wait for the request to fail; this can take up to 15 seconds.
4. Check the **Offline · saved posts** label. Read the text and try a completed media download.
5. Try a search or page you have not opened before. It should explain that it is not saved. The app cannot search all content while offline.
6. Restore the connection. The app checks saved versions with the backend and reloads the feed. Withdrawn/replaced versions are removed from saved copies.

You must sign in successfully while connected first. An already checked, unexpired sign-in can then reopen saved content offline. Use an installed preview build for a true offline restart test: Expo Go may need the development computer to start.

The phone cannot learn about a withdrawal while disconnected, which is why saved posts carry an Offline label. A server error or rejected sign-in does not count as offline access. The phone needs access to this backend, not just any internet connection.

## Clear saved copies or sign out

1. Open **Settings**.
2. Tap **Clear saved posts and files** and wait for confirmation. This also resets saved subject choices, but keeps you signed in.
3. While offline, try previously saved posts. They should no longer be available. Reconnect to load them again.
4. To sign out, reconnect and tap **Sign out**. The backend ends the session and the app clears this account's saved copies and subject choices.
5. If sign-out fails offline, reconnect and retry. The app does not claim the server ended a session while unreachable.
6. Sign in with another invited test account. It should not inherit the previous account's choices or offline copies.

Teaching content is saved in the app's normal cache, not an encrypted document store. Login credentials are stored separately in protected phone storage.

## Record the phone results

Write down the date, phone model, Android version, Expo Go or installed build, and pass/fail notes. Do not record live login links or credentials.

| Check | Expected result |
| --- | --- |
| Subject choice | Checkboxes show Biology (JAMB); no choices means Continue is disabled; saved choices belong to this account. |
| First feed | Continue goes straight to posts, with no topic/lesson menu. |
| Swipe | One post fills the feed area; swipe up advances; more pages load near the end; the end is clear. |
| Random mix | Refresh gets a new mix; loading more does not reshuffle already loaded posts. Small collections may repeat the same order by chance. |
| Optional dares | Dares appear in the feed with varied spacing; skipping works; no forced post-ending quiz; media pauses on a dare. |
| Search | Related published posts appear within selected subjects; Clear restores the mix; no matches and failed requests are distinct. |
| Text | The short view is readable; Read more contains the complete explanation. |
| Image | Data saver on waits for Load; off loads visible images. Descriptions remain available. |
| Audio/video | Wait for Load and Play; pause works; swiping away, opening an overlay, leaving the route, and backgrounding pause playback. |
| Captions/transcripts | Captions match speech; Read more works without downloading media. |
| Large text/small screen | Buttons remain reachable; full text and media are available in the scrollable detail view. |
| Slow/interrupted connection | Text remains usable; failures offer retry; unfinished files are not saved. |
| Offline/reconnect | Saved pages are labelled; uncached searches explain the limit; reconnect removes unavailable versions. |
| Clear/sign-out | Saved content and subject picks are removed; another account cannot reuse them. |

These checks remain pending until someone records them on a physical phone. Desktop tests do not prove that a feed feels fun or that native playback works correctly.

## Common problems

**No subjects or posts:** ask the admin to check that a human-reviewed version says Published and its exam is active. Drafts are hidden. Return to the subject picker or refresh the feed after publication.

**Feed returns an error after updating:** restart Django as well as Expo and refresh once while connected so the updated feed format is saved. The new feed/search endpoint must be running on the backend.

**Cannot reach server:** check Wi-Fi, the Django terminal, computer IPv4 address, allowed hosts, and firewall steps in [setup](setup.md). Restart Expo after changing mobile/.env.

**File will not open:** retry while connected. Ask the admin to check the actual file format and details. Read the transcript meanwhile. If a saved file is damaged, clear saved copies and load it again.

**Sign-in expired:** reconnect and request another email link. Offline reading does not extend the 30-day session or undo an admin's access change.

## Fix “Unable to resolve expo-video”

This can happen if Expo was running when the media packages were installed.

1. Stop Expo with **Ctrl+C**.
2. From swipe-iq/mobile, run npm.cmd ci if this milestone's dependencies have not been installed.
3. Start with a fresh bundler cache:

   ~~~powershell
   npm.cmd start -- --go --clear
   ~~~

4. Close the app in Expo Go, then scan the new QR code. Wait for the fresh bundle.

For an installed development build, use npm.cmd start -- --dev-client --clear instead. An old installed build may also need rebuilding to include the new native packages.

## Quick play and progress

Accept a purple in-feed dare with **I’m game ✦**, or skip it and keep scrolling. Answer three questions and submit to see your score and explanations. Open **Settings → My progress** for history and unfinished dares. There are no quiz buttons on ordinary posts. Follow the [quiz phone guide](quiz-phone-guide.md) for setup, saved answers, retries, and the phone checklist.
