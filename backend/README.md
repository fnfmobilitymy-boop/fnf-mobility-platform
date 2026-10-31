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

This project has **not** been deployed into your Render account by the assistant. Account access and real payment/mail credentials are still required. The GitHub Pages production site is not automatically redirected to an unverified server.

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
