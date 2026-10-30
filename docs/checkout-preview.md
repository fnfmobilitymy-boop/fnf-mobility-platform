# Service basket / payment preview

Preview URL: https://kennystudio.cfd/checkout-demo/cart/

This is a browser preview, not a production order/payment backend. The existing homepage, public pricing, sitemap and production checkout entry remain unchanged in this preview release.

- Catalogue uses approved pricing: 5 website packages, 3 care plans, 17 add-ons, 5 search services. Quantities, product-entry minimum, language setup plus per-page charge, and selected monthly periods are explicit. No automatic subscriptions.
- Basket localStorage contains catalogue IDs and quantities only. Requirements move to checkout through tab sessionStorage, expire after 30 minutes, and are removed from sessionStorage when read. Customer details and receipt files stay in page memory. No automatic server submission.
- Visitors can review/send requirements through WhatsApp. Opening a text link never attaches a file; native file sharing is offered only if supported. Bank/TNG/USDT require a local receipt selection, USDT also requires a transaction hash, before preparing a verification message. JPG/PNG/PDF, 10 MB maximum. Files are never represented as uploaded.
- Quote amount remains a customer-entered draft requiring written approval. Checkbox and client totals are not trusted proof of scope, price, invoice issuance or funds.
- Owner confirmed Stripe is customer-entered MYR. Website calculates 6% on the selected stage, but the Payment Link does not enforce or populate this amount. No automatic fee enforcement is claimed.
- Stage PDFs are local raster A4 pro forma payment notices, with Chinese supported by the browser font. 50% and 30% are rounded to cents; the 20% balance receives the remainder so the three base stages sum exactly to the quote. PDFs are not paid receipts, tax invoices or Malaysian e-Invoices. Long baskets paginate.
- No paid state can be set by URL parameters, local file selection, PDF download, Stripe opening or a WhatsApp action.
- All preview routes noindex and omitted from the production sitemap.

## Next: real order backend

Requires a connected backend deployment and private file storage. Implement authenticated owner order list, server-side catalogue/quote validation, per-order stage ledger, receipt upload validation/access control, payment review, and immutable invoice numbers/documents. Stripe Checkout Sessions must be created server-side with the agreed stage total plus disclosed fee; validate Stripe webhook signatures and settle the stage only after verified successful payment. Manual transfers require owner confirmation against actual funds. Generate paid receipts only after verification, notify hello@kennystudio.cfd using a configured transactional mail provider. Do not put API keys in the static repository or client.

Tests: `python3 -m unittest discover -s tests -p 'test_*.py' -q`, `python3 tests/check_links.py`, browser checkout/order/pricing checks at desktop/tablet/mobile sizes and EN/ZH/MS.
