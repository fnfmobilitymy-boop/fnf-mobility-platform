# Kenny Studio: promote the existing service to real orders

Target: `kenny-studio-orders-test` (`srv-dbipjrlg1s2s73dtcq7g`), My Workspace. Keep the current URL and credentials. Do not change the unrelated `kenny-commerce` / hangover service.

The owner has authorized production launch. The available Render connector can deploy and merge environment variables but cannot change the instance plan or attach a disk. Those infrastructure steps must be completed in the Render Dashboard; inspect its current bill before applying a paid plan.

## Required infrastructure

1. Open https://dashboard.render.com/web/srv-dbipjrlg1s2s73dtcq7g .
2. Change Instance Type from Free to a paid web-service plan.
3. Open Disks and add a 1 GB persistent disk, mount path `/data`.
4. Wait for the disk-backed deployment to become Live.

The following non-secret variables will then be merged without replacing credentials:

```
APP_ENV=production
DATA_DIR=/data
PERSISTENT_DATA_ROOT=/data
MAIN_SITE_ORIGIN=https://kennystudio.cfd
APP_TEST_MODE=false
```

Do not disable test mode before the disk is present. The prepared backend checks the actual disk mount and refuses live startup on an ordinary ephemeral directory. `/api/config` reports actual persistence instead of guessing from the test-mode flag. It also offers Stripe only when its API and webhook credentials exist. Transfers remain available.

## Payments and notifications

The existing bank, TNG and TRC20 receiving details remain in the server catalogue. Before transferring, customers must confirm the recipient; owner checks actual funds before approving. USDT amounts are agreed per stage, with no assumed exchange rate.

For Stripe, set `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` privately in Render. Register the deployed URL plus `/api/stripe/webhook` in Stripe. The existing pay-what-you-want Payment Link cannot enforce the approved order total and automatic 6% fee. Use the server Checkout workflow, verify a signed live event for an exact amount, then enable it for customer use. No keys belong in Git or chat.

For automatic email, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` privately in Render. Without SMTP, use the customer private portal link and manually send follow-up text; queued messages are not delivered messages.

## Before linking the main website

1. Verify the promoted commit is Live and `/api/config` reports `testMode:false,persistent:true`.
2. Verify a fresh order, quote, dummy/test receipt flow and PDFs, then ensure test data are not presented as real payments. Do not approve fake transfers as real received funds in production.
3. For persistence, create a clearly labelled launch verification order, deploy the same version, and verify that the record and its attachment remain accessible. Keep payment unverified.
4. Configure `ORDER_BACKEND_URL=https://kenny-studio-orders-test.onrender.com` in the actual latest main-site publishing source/build, preserving existing site content and SEO. Publish the static bridge only after verification. The currently published static preview must not be represented as connected until this step is completed.
5. Download a business ZIP regularly, preserve APP_SECRET in Render's secret manager, and keep application-consistent SQLite backups separately from filesystem snapshots.

The current promotion changes pass 15 backend integration tests and the deterministic JavaScript sync/tool-render checks. External full-browser/live HTTP verification remains limited by this execution environment; do not claim such checks passed without evidence.
