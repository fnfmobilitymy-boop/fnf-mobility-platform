# Customer accounts

Both normal and AI checkout require a verified customer session and customer CSRF header. New orders belong to an account; private order links cannot bypass that account. Owners retain access. Existing unlinked orders keep their legacy capability links and are never claimed solely by email.

Email: register (12+ character password), verify a six-digit code (10 minutes, five attempts), log in, reset password and log out. Password reset invalidates existing customer sessions. Customer sessions are separate from owner sessions and expire in 30 days. The account page lists only that account's orders. Checkout keeps its form in place while the modal is open.

## Enable actual delivery

Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD and SMTP_FROM privately in Render. SMTP uses STARTTLS unless SMTP_SSL=true. In APP_TEST_MODE=true no mail is sent; a clearly labelled test code is shown. With test mode off, email registration refuses to operate without SMTP configuration.

## Enable Google

In Google Cloud / Google Auth Platform configure branding, audience and an OAuth client of type Web application. During Google's testing mode add the intended test users. Register this exact authorized redirect URI:

https://kenny-studio-orders-test.onrender.com/api/account/google/callback

Configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET privately in the target Render service, then deploy. Never put the secret in browser code or chat. If moving to a custom backend hostname, update PUBLIC_URL and the authorized redirect URI together.

The flow uses an HttpOnly state cookie, one-time server state, nonce and PKCE. ID tokens are verified with Google's official google-auth library against fetched Google certificates, audience, issuer and expiry. Google sub is the identity. A matching email does not merge accounts automatically: an existing email account must first sign in with its password, then explicitly link Google on its account page.

Google runs in a popup to retain checkout details. Allow popups for the backend hostname. The current widget is hosted on the backend; do not embed this cookie-based checkout across unrelated origins without a same-origin sign-in handoff.

## Release checks

24 in-process ASGI tests cover the previous order/payment flows plus account verification, OTP attempts/expiry/replay, password reset/session invalidation, customer/owner separation, order ownership, CSRF, duplicate submissions, normal and AI login requirements, Google state/nonce checks and explicit account linking. Google provider calls are mocked in this environment; real Google login requires the OAuth configuration above. Browser JS syntax and prior live-sync/order-bell VM checks also pass. Local package download and real browser execution are sandbox-blocked, so the official verifier is installed in Render's Docker build.

The current service is still TEST ONLY without a persistent disk. Do not disable test mode until durable storage and real email delivery are configured and verified. WhatsApp remains paused.
