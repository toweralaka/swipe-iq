# Sign in with an email link

Students use a login link instead of a password. You can test this locally now. Opening real email links in an installed Android app also needs a domain, email service, and matching app build. Those phone checks are still pending.

## Local development without an email provider

The default setup saves test emails on your computer. It does not send them to an inbox.

1. Complete [setup](setup.md). From backend/, prepare the database and start the server:

   ~~~powershell
   .\.venv\Scripts\python.exe manage.py migrate
   .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
   ~~~

2. Open http://127.0.0.1:8000/admin/ on the computer and sign in with your staff account. Go to **Accounts → Invitations → Add**. Enter your test email and leave Active checked. Students do not need staff access or a password.
3. In mobile/.env, set EXPO_PUBLIC_API_URL to the computer's Wi-Fi address, as explained in [setup](setup.md). Keep the phone on the same private Wi-Fi.
4. In another terminal, from mobile/, start Expo:

   ~~~powershell
   npm.cmd start -- --go
   ~~~

   Scan the QR code with Expo Go. If an old screen still appears, stop Expo and run npm.cmd start -- --go --clear. If you use an installed development build instead, use npm.cmd start -- --dev-client.

5. Enter the invited email and tap **Send my login link**. Open the newest message in backend/.local-email/ privately in your editor. Copy its complete /login#token=... URL. A link is a temporary sign-in secret: do not put it in chat, Git, or screenshots.
6. In the development app, tap **Test a local login link**, paste the URL, and tap **Read local link**. Then tap **Confirm sign-in**. Reading the link alone does not sign you in.
7. Check that your email appears on the home screen. Tick **Biology (JAMB)** and tap **Let’s scroll** to open your feed. See the [feed guide](feed-phone-guide.md) for media and offline checks.
8. Restart the app while connected and check that it remembers your sign-in. Tap **Sign out** and check that the account disappears. If disconnected, sign-out shows an error; reconnect and retry so the server can end the session too.

Optional: set LOGIN_LINK_BASE_URL in backend/.env to http://YOUR_COMPUTER_WIFI_IPV4:8000/login and restart Django. The default localhost URL is fine for the development paste test because that test reads the token without opening the website.

These steps test local sign-in. They do not prove real email delivery or Android opening an HTTPS link in your installed app.

## Set up real email and links that open the app

A domain is your website address. Android App Links let a link on that website open your app. Android checks a small file on the website to confirm that the website and app belong together.

1. Choose a domain you own and an email service. Agree the service and budget before buying anything. Neither has been set up for this project yet.
2. Fill in the private backend settings using backend/.env.example: the email service's SMTP host, port, credentials, and sender address. Verify the sender with that service. Set LOGIN_LINK_BASE_URL=https://YOUR_DOMAIN/login. Keep email credentials private.
3. Set EXPO_PUBLIC_API_URL in mobile/.env to an HTTPS backend address that the phone can reach. An installed preview build requires HTTPS.
4. Set EXPO_PUBLIC_LOGIN_HOST=YOUR_DOMAIN in mobile/.env. Use only the hostname, with no https:// or path. It must match the domain in the email link. This hostname becomes part of the app build and is not a secret.
5. Check the app's Android ID. It defaults to com.swipeiq.mobile. The backend's ANDROID_PACKAGE must match. If you want a different ID, choose it before distributing builds.
6. Set up an Expo account/project for builds. Expo's EAS service builds an installable Android app in the cloud. The project includes development and preview settings in mobile/eas.json. After that setup, from mobile/ run one of:

   ~~~powershell
   npx.cmd eas-cli@latest build --platform android --profile development
   npx.cmd eas-cli@latest build --platform android --profile preview
   ~~~

   Choose **development** if you want it to connect to the local Expo server; choose **preview** for an installed app that runs without that server. No cloud build, account setup, or app publishing has been run for you.

7. Get the build's signing certificate fingerprint:

   ~~~powershell
   npx.cmd eas-cli@latest credentials -p android
   ~~~

   Copy the SHA-256 fingerprint into the backend's ANDROID_CERT_FINGERPRINTS setting. A fingerprint is a public identifier for the build's signing certificate. Keep the actual signing keys private.

8. Serve /.well-known/assetlinks.json on the exact login domain over HTTPS, with application/json and no redirect. Django provides this file when the package and fingerprints are configured; without fingerprints it returns 404. If the website is hosted elsewhere, put the matching file there. Android reads it to check the app/domain connection.
9. Serve /login on the same domain as a help page for people who cannot open the app. Configure the host so it does not log login tokens or request bodies.
10. Install the matching APK on the phone. In Android's app settings, check **Open by default** to confirm the domain can open this app. Changing the hostname, app-link settings, or native packages requires another app build.

See the official guides for [Expo SDK 57 Router](https://docs.expo.dev/versions/v57.0.0/sdk/router/), [Router installation](https://docs.expo.dev/router/installation/), [protected phone storage](https://docs.expo.dev/versions/v57.0.0/sdk/securestore/), and [Android App Links](https://docs.expo.dev/linking/android-app-links/).

## Phone checks before closing Milestone 3

Record the phone model, Android version, build, date, and pass/fail notes. Leave live links and credentials out of the record.

- The invited address receives a real email. An unknown address sees the same generic response in the app but receives no invitation email.
- The installed app opens the email link when closed and when already running. The link is used only after Confirm sign-in.
- The signed-in email is checked against the backend. Closing and reopening the app keeps the sign-in.
- Expired, reused, or broken links explain how to request another. Too many requests produce a clear wait-and-retry message.
- Sign-out ends the server session. Expired or deactivated sessions cannot fetch content.
- The help page works when the app is unavailable.
- The phone feed identifies JAMB Biology and hides drafts. The backend hides answer keys and inactive examinations.

Automated tests check these rules in code. They do not prove email delivery, Android link handling, or protected storage on your phone. Those checks still need to be recorded. Human review of teaching content remains a separate requirement.
