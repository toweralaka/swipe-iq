# Student access implementation — Milestone 3

Status: implementation choices within the approved baseline. Domain/email/build acceptance remains pending.

Use opaque random bearer credentials, stored as hashes on the server and in SecureStore on the phone. JWTs are an alternative, but immediate logout/invitation revocation would still need server state; a database session is simpler for this small invited pilot. No third-party authentication service or new Python dependency is needed.

Use database-backed fixed-window rate buckets with conditional increments. DRF's cache-based throttling is easier to configure but does not guarantee atomic counting across workers. The fixed window is simple and testable; burst behavior at boundaries and trusted proxy configuration are documented.

Use fragment login tokens so web access logs receive only /login. Android links are mapped to an in-memory Router confirmation route, and only a button sends a POST exchange. Tokens are not persisted on the device or recorded by analytics. A private local file outbox avoids putting development email tokens into server console logs. The local paste route is gated by __DEV__ and does not replace real email/App Links acceptance.

Use Expo Router as required by mobile/AGENTS.md. Retain the foundation connection screen as a separate route. Add SDK-compatible Router, SecureStore, and development-build dependencies; align animation and React DOM dependencies with Expo's installed version map rather than forcing incompatible peers. Preview builds enforce an HTTPS API.

M3 exposes read-only published content contracts; M4 implements the actual examination selection and feed. Content/media human approval remains a separate gate and is not established by automated tests or by authorization to write authentication code.
