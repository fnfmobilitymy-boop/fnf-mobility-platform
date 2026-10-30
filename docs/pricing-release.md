# Approved pricing page — 30 October 2026

Owner requested publication of all prices from the revised bilingual V2 guide.
Earlier restrictions on publishing unapproved package prices are superseded for these exact fees.

- Route: https://kennystudio.cfd/pricing/
- Website starting fees: MYR 1,000 / 1,800 / 1,800 / 2,500 / 4,500.
- One language and two consolidated revision rounds. See individual plan scope.
- Care: MYR 150 / 300 / from 600 per month; 1 / 2 / 4 total hours, not additive.
- 17 add-ons and five search/advertising offers match the V2 PDF.
- PDF: media/kenny-studio-pricing-en-zh.pdf; no private Canva edit URL is published.
- Payment stages: 50% deposit, 30% development preview approval, 20% before launch.
- Domain, hosting, subscriptions, provider and payment fees remain separate.
- Scope, consent, Search Console/Ads access, no-results-guarantee and care limits are explicit.

Implementation follows the retained Python static generator. source/seo/pricing.py centralises
EN/ZH/MS copy and approved fee data. The new route has pre-rendered English content, canonical,
Open Graph/Twitter metadata, breadcrumbs and factual starting-price offers. All seven indexable
routes appear in the sitemap. Homepage, service-page navigation and service content link to prices.

Existing 23 project URLs/covers, original home animations, globe, soundtrack, ten original design
service types, two search service types and original form budgets are preserved. Pricing CTAs
prefill the existing project type; they do not collect payments or create orders.

QA: SEO build unit suite, internal link and asset checks, 360/390/768/1024/1440px pricing checks
in all three languages, PDF response, project-brief prefill, mobile menu, reduced-motion video,
language-switch video lifecycle, existing route smoke tests, globe and real WebGL gallery tests,
and local-only analytics-consent fixtures. Analytics IDs remain unset in production.

## Order requests and payment prerequisites

- /order/ is a noindex utility route outside the sitemap. Package selection comes from the pricing cards.
- Requests can be reviewed and then sent by the visitor through WhatsApp. This does not automatically submit an order to a server, accept an order or collect payment. Personal fields remain in page memory, not localStorage or a database.
- 50% deposit shown is an estimate from the selected package starting price; a final written quotation is required before paying.
- Online Transfer, Touch ’n Go eWallet and Stripe use actual payment icons from activemerchant/payment_icons. They are labelled setup pending. No bank account, QR/payment URL or Stripe live account was supplied. No fake success state or unconfigured payment action is enabled.
- To enable real payments: obtain verified bank details, TNG merchant QR/link and Stripe live account/payment links. Automated authoritative order/payment confirmation additionally requires a server-side order store and verified payment webhooks. GitHub Pages does not run such a backend. Never accept a URL success flag as proof of payment.
- Primary website email and downloadable guide now use hello@kennystudio.cfd, as supplied by the owner. Domain mailbox delivery has not been tested and DNS/mailbox provisioning is outside this source update. Existing private Canva documents are retained.
