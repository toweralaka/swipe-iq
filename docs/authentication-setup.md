# Email login and physical Android checks

Milestone 3 code supports local development and configurable Android App Links. Real email/domain/signing configuration and an installed build are required to complete device acceptance. M2 human teaching-content review remains separate.

## Local development without an email provider

1. Follow [setup](setup.md), then run from backend/:

       .\.venv\Scripts\python.exe manage.py migrate
       .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

2. In the staff admin, open Accounts → Invitations → Add. Enter your test email address and leave active checked. No password or student staff access is needed. Do not add real pilot addresses to Git.
3. Optionally set LOGIN_LINK_BASE_URL in your private backend/.env to http://YOUR_COMPUTER_WIFI_IPV4:8000/login. Restart Django. The default is localhost; local paste testing does not navigate to the link host.
4. Open the phone app on the same Wi-Fi with EXPO_PUBLIC_API_URL pointing to your computer. Use npm.cmd start -- --go for the Expo Go route; restart with a cleared cache after switching to Router. Installed development builds can use npm.cmd start -- --dev-client.
5. Enter the invited email and tap Send login link. The default development email backend saves the message to backend/.local-email/. It does not send a real email. Open the newest local message privately in your editor and copy its complete /login#token=... URL. Do not paste tokens into chat or screenshots.
6. In a development app, tap Test a local login link, paste the URL, tap Read local link, then Confirm sign-in. Opening/reading a link alone must not sign you in. The home screen displays the authenticated email.
7. Restart the app and verify the session restores; tap Sign out and verify the account disappears. If disconnected, sign-out must show an error and allow retry rather than claiming server revocation.

This checks local API/session behavior. It does not establish real email delivery or verified HTTPS App Links. The student feed/examination selector remains M4. The existing Connection check screen remains available.

## Configure real email and verified links

1. Choose an owned domain and email service; purchase/provider provisioning requires owner authorization. No provider or cost has been assumed or configured by this milestone.
2. Set private backend settings from backend/.env.example: SMTP host/port/credentials, sender, and LOGIN_LINK_BASE_URL=https://YOUR_DOMAIN/login. The sender must be verified with your chosen email service. Preview builds also require an HTTPS EXPO_PUBLIC_API_URL reachable from the phone.
3. In private mobile/.env set EXPO_PUBLIC_LOGIN_HOST=YOUR_DOMAIN (no scheme/path). This public hostname is bundled into the app. It must match the login-link host. App config generates auto-verified HTTPS /login intent filters only when a hostname is set.
4. Android application ID defaults to com.swipeiq.mobile; backend ANDROID_PACKAGE must match it. Change the package before distributing builds if you require another identifier. Keep backend and mobile values aligned.
5. EAS profiles are supplied in mobile/eas.json. After owner setup of an Expo account/project, run npx.cmd eas-cli@latest build --platform android --profile development or --profile preview from mobile/. Cloud build/account setup and publishing have not been run. A preview build uses the configured HTTPS API; a development build connects to Metro.
6. Obtain the installed build signing certificate's SHA-256 fingerprint using npx.cmd eas-cli@latest credentials -p android. Set ANDROID_CERT_FINGERPRINTS on the backend to the fingerprint(s). Signing keys stay private; the public certificate fingerprint belongs in the association document.
7. Serve the configured backend /.well-known/assetlinks.json on the exact login domain over HTTPS with application/json and no redirects. Without fingerprints this endpoint returns 404, intentionally. If the domain is hosted elsewhere, serve the equivalent association document there. Serve /login as the installation/help fallback. Configure host routing without request/body/token logging.
8. Install the matching APK on your Android phone. Changing hostname/intent filters requires a new build. Verify Android recognizes the domain in the app's Open by default settings.

Reference instructions: [Expo SDK 57 Router](https://docs.expo.dev/versions/v57.0.0/sdk/router/), [installation](https://docs.expo.dev/router/installation/), [SecureStore](https://docs.expo.dev/versions/v57.0.0/sdk/securestore/), and [Android App Links](https://docs.expo.dev/linking/android-app-links/).

## Acceptance checklist to record before closing M3

- Real invitation email received; unknown address gets the same generic app response and no invitation email.
- Installed Android app opens the HTTPS email link while closed and while already running; no token consumed until Confirm sign-in.
- Signed-in screen comes from an authenticated /auth/me/ request. Force-close/reopen preserves sign-in.
- Expired, reused, malformed links offer a new-link route; resend and rate-limit recovery are understandable.
- Logout revokes the credential; expired/deactivated sessions cannot read content.
- Help page works when the app is unavailable. Capture device/build/date and outcomes without credentials or email tokens.
- Published-content API identifies JAMB Biology, hides drafts/answer keys, and rejects inactive examinations. Do not expect a lesson feed screen before M4.

Automated tests validate these server/client rules but do not prove actual Android intent delivery, email delivery, or secure storage on your phone. No such physical-device result is claimed yet.
