# Kenny Studio · Orders & Payments

A separate server for the existing Kenny Studio static site. The portfolio, animations and approved price catalogue remain intact. The catalogue is imported directly from the existing `source/seo` modules, not retyped client prices.

## What is implemented

- Real SQLite persistence for project requests, selected services, quantities, contact details, requirements, approved scope, payment stages, uploads, documents and audit history.
- Server-calculated catalogue starting estimates, including quantity limits, RM500 + RM150/page language setup and minimum 5 simple product entries.
- Owner dashboard `/admin`, password authentication, HttpOnly/SameSite session cookie, CSRF checks, login throttling and protected files.
- Customer portal `/order/<id>` with a 256-bit private access link in its URL fragment. Opening the link stores access in that browser tab and removes the fragment from the address bar. Owner can copy the link from the order dashboard. Links are private bearer access: keep them private.
- Owner approves the final amount, scope and payment method. Three numbered PDF invoices are issued transactionally. Deposit opens first. Owner releases the 30% preview and 20% acceptance stages only after the previous payment is verified and a milestone note is recorded.
- Stripe Checkout creates server-enforced MYR line items for the stage amount plus 6%. Signed webhooks validate stage, session, exact amount, currency, mode and replay protection. Returning from Stripe never marks an order paid.
- Bank, TNG and USDT receipts really upload to private persistent storage (JPG/PNG/PDF, 10 MB). Owner checks actual funds before approving; receipt upload alone never changes payment to paid. USDT requires exact agreed stage token amounts and a TRON transaction hash. No exchange rate or on-chain confirmation is invented.
- Immutable, numbered invoice and verified-payment receipt PDFs. These documents are not validated Malaysian LHDN e-Invoices.
- Transactional email outbox with bounded retries. Messages stay queued until real SMTP settings are supplied; no fake delivery claims.
- English / 中文 / Bahasa Melayu interface. Request details are not stored in localStorage; only service IDs/quantities and language preferences are. The private customer capability uses tab-scoped sessionStorage.

## Deploy on your Render account

Repository: `fnfmobilitymy-boop/fnf-mobility-platform`
Branch: **`orders-backend-20261031`**
Blueprint: root **`render.yaml`**

Quick deploy: https://render.com/deploy?repo=https://github.com/fnfmobilitymy-boop/fnf-mobility-platform/tree/orders-backend-20261031

Render supports specifying the branch in this repository URL: https://render.com/docs/deploy-to-render#specifying-a-branch

1. Open https://dashboard.render.com/blueprints and select **New Blueprint Instance**.
2. Connect/select the repository above, explicitly select branch `orders-backend-20261031`, and use `render.yaml`.
3. Set `ADMIN_PASSWORD` in the private Render form to a strong password of at least 12 characters. Login email is `hello@kennystudio.cfd`. Do not send the password in chat or commit it. Render generates `APP_SECRET`; keep it stable across deployments so customer links keep working.
4. Review the paid web-service/persistent-disk plan and Render's displayed price before creating. A free ephemeral filesystem is unsuitable for real orders and receipts. The blueprint provisions a 1 GB disk mounted at `/data` and one server worker. It does not automatically charge or deploy from this repository alone.
5. Render runs the Dockerfile and `/api/health` health check. `RENDER_EXTERNAL_URL` supplies the actual HTTPS origin automatically. If you later use a custom domain, set `PUBLIC_URL` to that HTTPS origin.
6. Open the Render URL for customer requests, and `<Render URL>/admin` for your dashboard. A fresh database starts empty; no fake orders or testimonials are seeded.

The production persistent-storage blueprint has **not** been deployed. A separate free testing service is live at https://kenny-studio-orders-test.onrender.com with APP_TEST_MODE=true. It does not accept real payments or send mail and its data are ephemeral. The GitHub Pages production site is not redirected to the test server.

## Enable Stripe after the server is live

In Render's **Environment**, add real private `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`. Never put secret keys in HTML, GitHub or chat. Use test-mode keys first.

Create a Stripe webhook pointing to `<actual Render origin>/api/stripe/webhook`, selecting:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`

Copy that endpoint's signing secret into `STRIPE_WEBHOOK_SECRET`. Use a matching test/live key and webhook configuration. Redeploy after environment changes. The existing customer-entered Payment Link is intentionally not used for automatic exact-amount billing.

Before accepting real money, perform a Stripe test checkout in your deployed environment and verify the 50% / 30% / 20% ledger, 6% fee and webhook receipt. Tests in this repository do not send real charges or contact Stripe.

## Enable email

Configure a real sender for `hello@kennystudio.cfd` with your mailbox/transactional-mail provider, then set:

`SMTP_HOST`, `SMTP_PORT` (normally 587), `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM=hello@kennystudio.cfd`.

STARTTLS is required unless `SMTP_SSL=true` is deliberately selected (normally port 465). Verify the sender/domain in your provider. The persistent outbox sends queued confirmations when configured. Production delivery has not been verified without these credentials. It is at-least-once delivery; an interruption after SMTP acceptance can produce a repeated notification, never a repeated payment.

## Connect the existing main site

Only after the actual Render origin and order flow are verified, configure the static-site build's `ORDER_BACKEND_URL` with that HTTPS origin. The opt-in bridge sends selected catalogue IDs/quantities to the server; the server recalculates prices. It does not trust an amount from the browser. Before the origin is supplied, the existing static previews remain unchanged.

## Local run

```sh
cd backend
python3 -m pip install -r requirements.txt
python3 -m app.setup
# Put the printed APP_SECRET / ADMIN_PASSWORD_HASH into your private environment.
# Set PUBLIC_URL=http://127.0.0.1:8188 and DATA_DIR to a private writable directory.
python3 -m uvicorn app.server:app --host 127.0.0.1 --port 8188
```

`ADMIN_PASSWORD_HASH` is an alternative to the private Render `ADMIN_PASSWORD`. Local `.env` files are examples/configuration aids; the app reads real process environment, not an automatically loaded dotenv file.

## Validation and operations

```sh
python3 -m unittest discover -s backend/tests -p 'test_*.py' -v
python3 -m py_compile backend/app/*.py backend/entrypoint.py
node --check backend/static/app.js
```

API integration tests use an in-process ASGI adapter and inline worker execution because this execution sandbox blocks socket-based worker-thread wakeups. They exercise actual routes, DB transactions, authentication, PDFs and file access, without network or SMTP calls. Live Render deployment, Docker build and browser layout verification remain separate deployment checks, not claimed by the in-process test suite.

Data are in `/data/orders.sqlite3` (including its SQLite WAL files) and `/data/uploads/`. Take consistent SQLite backups with SQLite's backup API together with the uploaded files; do not copy only the database file while writes are active. Preserve `APP_SECRET` separately in the hosting secret manager. Do not run multiple service replicas against the same SQLite disk.

Quotes/invoices are immutable after approval in this first version. Correct a requested scope before issuing. Refunds, partial/underpayments, a revised issued invoice, multiple currencies and LHDN integration require an explicit workflow; they are not silently auto-approved.

## Isolated free testing service

`APP_TEST_MODE=true` is for a separate temporary test service only. A visible banner marks every screen, real receiving-account details are withheld, live Stripe checkout/webhooks and SMTP delivery are disabled, and generated PDFs are labelled TEST ONLY. The production blueprint does not enable this switch. Tests can upload dummy receipts and exercise owner approval and the 50/30/20 workflow without moving money. The free service uses ephemeral storage; do not put real customer data in it. Its credentials are kept in that service's Render environment, not in Git or public chat.


Testing owner login: https://kenny-studio-orders-test.onrender.com/admin . Email is `hello@kennystudio.cfd`. The generated password is stored only in the test service Render Environment as `ADMIN_PASSWORD`; inspect or replace it there. Never copy it into Git or public chat.

Local browser verification completed at 1440px and 390px: EN/ZH/MS request forms, real local order persistence, owner login/quotation, three dummy receipt uploads and approvals, sequential milestone releases, and six downloadable invoice/receipt PDFs. These tests use a separate temporary local database and never charge money. Render reports the isolated test deployment Live and its startup logs show HTTP GET / returning 200; direct external HTTP verification from this execution workspace is blocked by its proxy.

## Owner tools (prepared, deployment pending)

The owner dashboard now includes business overview, a cross-order receipt inbox, searchable clients, project planning (delivery state, priority and target date), private notes, versioned tasks, follow-up message copying and exports. Project planning is owner-only and never marks payments paid or releases stages. Notes are stored separately from customer-visible orders. Plans and tasks reject stale edits from another tab. Existing databases gain the additional tables/indexes using idempotent CREATE IF NOT EXISTS statements.

The overview uses all-time approved MYR project values, excluding Stripe fees. Settled values include only verified paid stages. Outstanding values include locked stages. USDT settlements use the agreed MYR book value of the project, not a fiat bank balance or an assumed current exchange rate. Pending transfers do not increase settled totals.

CSV exports include all orders, UTF-8 BOM and spreadsheet formula neutralization. The business ZIP contains records, uploaded receipts and invoice/receipt PDFs, excludes sessions/credentials/outbox/private-link tokens, and stops if a referenced upload is missing. It is a portable records archive, not an automated server restore. Exports require an authenticated owner session. Temporary files are removed after download.

Front/back order status and tool data are checked every five seconds while visible, retry with backoff on connection failures, and resync when the tab becomes visible. Background repaint retains dirty form values, selected files, focus and scroll. Receipt badges show which order needs review, even while a different order is open.

Additional checks:

```sh
node backend/tests/live_sync.cjs
node --check backend/static/admin-tools.js
```

The current revision passes 13 in-process backend integration tests and deterministic JavaScript sync/render tests (including untrusted client labels). A fresh Chromium end-to-end run was blocked by this environment's socket restrictions; the earlier browser verification above applies to the baseline flow before these additions. Deployment remains pending because the current free Render test instance has ephemeral customer records and files.

## Production promotion preparation

See `PRODUCTION-LAUNCH.md` for the exact existing-service upgrade and launch sequence. Live mode now requires an actual persistent mount; setting an environment variable alone cannot claim persistence. Stripe is hidden and rejected for new live orders/quotations until both server credentials exist. These promotion guards pass 15 backend integration tests. They are prepared in Git; infrastructure completion and live verification remain required before enabling real orders and publishing the main-site bridge.

## AI sales consultant and owner notifications

The user has authorised automatic closing of the five published standard website packages at their listed prices. Additional scope always requires an owner quotation. The model cannot set prices, call payment verification, change terms, release milestones, or charge a card. A qualified lead must explicitly confirm the displayed fixed scope, current policy and contact details before the server atomically creates the order and 50/30/20 invoices. The deposit alone is released. Exact USDT amounts remain an owner task; choosing USDT submits a quotation request rather than an automatic quotation. Client preferences do not silently add deliverables to the standard contract.

Configure these privately in Render (do not send secret values in chat):

```
OPENAI_API_KEY=<private new key, never one exposed in chat>
OPENAI_SALES_MODEL=gpt-4.1
AI_SALES_ENABLED=true
AI_STANDARD_SALES_ENABLED=true
AI_DAILY_REQUEST_LIMIT=50
```

The Responses API is called only server-side with `store:false`, bounded history/output and strict structured responses. Per-IP/session/global request caps, per-turn idempotency and a busy lease limit duplicate billing. A provider failure returns a real unavailable response, never a fake generated answer or a fake order. Thirty-day inactive chat expiry is disclosed and cleaned up on session creation. No reference URLs are fetched; the AI asks what the visitor likes about a reference rather than claiming to have browsed it.

The widget identifies itself as AI, obtains processing consent, supports multilingual text replies, browser speech synthesis and optional browser speech recognition. Browser voices and microphone support vary. Speech input is reviewed before sending. The API model can reply in other languages; the interface has EN/ZH/MS controls. Voice playback is user-controlled and no audio autoplay is promised.

Owner tools include AI brief/transcript review, automatic Chinese summaries retaining original reference URLs and names, and links to resulting orders. The order sound must be enabled by a user gesture in the open owner page; it cannot ring in a closed browser. Background tabs resynchronise on return.

The owner currently has only ordinary WhatsApp/Business App, not Cloud API. Therefore automatic WhatsApp is NOT active. The UI provides copy-to-WhatsApp summaries. A queued adapter is ready for a future owner-supplied Cloud API account, approved one-body-variable template and private configuration:

```
WHATSAPP_ACCESS_TOKEN
WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_NOTIFY_TO
WHATSAPP_TEMPLATE_NAME
WHATSAPP_TEMPLATE_LANGUAGE
WHATSAPP_API_VERSION
```

These values must be supplied only after the owner enables the relevant WhatsApp service and agrees its billing. No session cookie scraping or unofficial personal-account automation is used. Provider acceptance is labelled `accepted`, not delivered; delivery callbacks are not implemented. Retry after an ambiguous provider timeout can create a duplicate notification, so the UI does not claim exactly-once delivery. Automatic external notifications remain disabled in test mode.

The public price guide has been updated to include one ordinary first-year domain per website package, first-year basic static hosting for showcase sites, explicit renewal/server-hosting charges, and a versioned project policy with proportionate cancellation settlement and mandatory rights preserved. The 50% deposit clause does not claim absolute forfeiture in every circumstance.
