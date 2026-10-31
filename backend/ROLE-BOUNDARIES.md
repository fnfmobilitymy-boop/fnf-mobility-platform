# Customer and owner boundaries

Customer pages use `index.html`, `customer-app.js` and the customer account/chat modules. The owner workspace uses `owner.html`, `owner-app.js` and `admin-tools.js`. They have no navigation into the other role's pages. The owner brand links only to `/admin`; customer portal sharing controls and the owner link-generation endpoint have been removed.

`app.js` is development source. After changing it, run `node backend/build_clients.cjs` and commit both generated entrypoints. Customer output must not reference owner API endpoints; owner output must not reference customer account modules. The owner page does not load customer account or chat scripts.

Owner sessions use an HttpOnly, SameSite Strict cookie scoped to `/api/admin`. Login deletes the previous root-scoped owner cookie. Owner data and private files are requested through authenticated `/api/admin/orders/{id}`, `/api/admin/documents/{id}` and `/api/admin/receipts/{id}`. Customer sessions remain separate, and customer-owned order/file requests require the owning customer session. Legacy unlinked orders retain their existing private capability links. All operations still use the same business database, so orders and payment updates remain synchronized. These are role and navigation boundaries on one host, not a claim of separate network origins.

## Country information

New registrations select a country/region from ISO 3166-1 codes. The server snapshots it into the order. Stripe Checkout collects billing addresses; a valid, matching paid webhook updates the order's billing country. The owner list, project detail, customer list and CSV label the source. Existing records without either source show Not provided. This is declared/billing country data, not IP geolocation or verified physical location. Country codes/names are sourced from the system iso-codes dataset; browser Intl.DisplayNames localizes the names.

## Payment state

The server calculates Not invoiced / Unpaid / Partially paid / Paid in full from invoice stages and verified payments, with paid project value and the current released amount due. Stripe's signed, matched webhook settles its stage and issues the receipt automatically. Browser return URLs or uploaded screenshots never prove funds were received.

The owner requested bank/TNG/USDT automation too. Those provider integrations still require the owner's merchant/payment-gateway choice and credentials. Do not label them automatic or replace their existing verification with unverified claims. Keep current formal Stripe credentials unchanged; the owner explicitly cancelled sandbox/test-key work.
