# Local development and physical Android setup

## What this milestone proves

Django serves a public liveness endpoint; the Expo app requests it and shows success/error. This verifies the toolchain and network boundary, not learning features or production readiness.

Use Node 24.x and Python 3.14.x. The lockfiles record installed dependency versions; do not replace them with arbitrary tutorial versions. Django 5.2.18 supports this Python; Expo SDK 57 targets React Native 0.86 and requires Node >=22.13. This project standardizes on Node 24 for local/CI parity.
Sources: https://docs.djangoproject.com/en/5.2/faq/install/ and https://docs.expo.dev/versions/latest/

## 1. Backend (PowerShell, repository root)

    python -m venv backend/.venv
    .\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
    Copy-Item backend/.env.example backend/.env

Edit backend/.env: replace 192.168.1.10 in DJANGO_ALLOWED_HOSTS with your computer's private Wi-Fi IPv4 address. Find it with ipconfig. Keep localhost and 127.0.0.1. Do not set ALLOWED_HOSTS to *.

    Set-Location backend
    .\.venv\Scripts\python.exe manage.py migrate
    .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

Using the virtual environment's Python directly avoids PowerShell activation-policy and py-launcher issues. Migrate creates the local SQLite tables. Binding to 0.0.0.0 lets the phone reach the API; it is not an address to enter on the phone. Use trusted private Wi-Fi only; the development server is not a deployment server.

On the computer, open http://127.0.0.1:8000/api/v1/health/.
Expected: {"status":"ok","service":"swipe-iq-api"}.

## 2. Mobile (another PowerShell terminal, repository root)

    Set-Location mobile
    npm.cmd ci
    Copy-Item .env.example .env

Edit mobile/.env: EXPO_PUBLIC_API_URL=http://YOUR_COMPUTER_WIFI_IPV4:8000 (no /api/v1 suffix). EXPO_PUBLIC values are visible in the app; never put secrets in them.

    npm.cmd start

Install Expo Go on your physical Android phone. Phone and computer must be on the same private Wi-Fi. Scan the terminal QR code with Expo Go. No Java, Android Studio, or adb is needed for this route.

The project uses Expo SDK 57. If your installed Expo Go reports SDK incompatibility, obtain the matching Android Expo Go build from https://expo.dev/go rather than changing dependency versions individually. Domain-verified email login in M3 will use an installed development/preview build instead of Expo Go.

Restart Expo after changing the API address (use npm.cmd start -- --clear if values appear stale). If your router assigns a new computer address, update both environment files and restart both servers.

## 3. Required physical-phone acceptance

1. In the phone browser, open http://YOUR_COMPUTER_WIFI_IPV4:8000/api/v1/health/ and confirm the JSON.
2. Open the app; tap Check connection; confirm Connected to Swipe-IQ API.
3. Stop Django; tap again; confirm a visible failure and that the button becomes available again.
4. Restart Django; tap again; confirm recovery.
5. Repeat with larger Android text settings and confirm the screen scrolls/readability remains usable.

Record phone model, Android version, Expo Go version, date, and results in docs/milestones.md. These checks cannot be claimed complete from a desktop-only run.

## Troubleshooting

- localhost on the phone refers to the phone, not the computer.
- Browser connection fails: check Wi-Fi/IP/port, Django bind address, and private-network firewall permissions. Guest Wi-Fi/client isolation or VPNs can block local access.
- Allow Python and Node through Windows Firewall on private networks if prompted; do not disable the firewall.
- HTTP 400/DisallowedHost: add the computer IPv4 to DJANGO_ALLOWED_HOSTS and restart Django.
- Expo QR fails: confirm Metro's LAN address is reachable; an Expo tunnel alone does not expose the Django API.
- Browser JSON works but app fails: verify mobile/.env and restart Expo.
- Network errors time out after ten seconds and can be retried. No requests run automatically.

## Automated verification

Backend, from backend/:

    .\.venv\Scripts\python.exe -m pip check
    .\.venv\Scripts\python.exe manage.py check
    .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
    .\.venv\Scripts\python.exe manage.py test

Mobile, from mobile/:

    npm.cmd run typecheck
    npm.cmd run lint
    npm.cmd test
    npx.cmd expo install --check
    npm.cmd run export:android

Android export verifies JavaScript bundling, not an installed app or phone networking. GitHub Actions runs equivalent commands on Linux when pushed; local success is not a claim that remote CI has run.

## Environment and scope

.env files, virtual environments, SQLite files, node_modules, .expo, and dist are ignored. Example files contain placeholders. Local DEBUG/HTTP are for development; hosted HTTPS, secrets, PostgreSQL, email, and media storage come in later milestones. The health endpoint proves liveness only, not database readiness.

Milestone 1 does not include accounts, content, quizzes, likes, or challenges. Reviewer/topic choices remain deferred to content planning.

## Milestone 2: staff editorial setup

After applying migrations, follow [editorial workflow](content/editorial-workflow.md) for seed_demo, interactive createsuperuser, draft editing, media review, publication, and replacement/withdrawal. Private uploads stay outside Git. Human-reviewed sample content is a separate acceptance gate.

## Milestone 3: invited email login

Follow [authentication setup](authentication-setup.md) for invitation administration, private local email messages, development login, domain/SMTP settings, installed Android builds, and real-device acceptance. Mobile navigation now uses Expo Router; start Expo Go explicitly with npm.cmd start -- --go, or an installed development build with npm.cmd start -- --dev-client. The student API contract is in [student access](api/student-access.md).
