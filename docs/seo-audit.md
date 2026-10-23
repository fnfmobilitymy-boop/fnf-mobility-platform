# Kenny Studio — baseline SEO/code audit

Baseline: `24584c8`, inspected before changes. Production has not been modified by the SEO work.

## Actual stack and deployment

- A static export whose single `index.html` embeds the compiled React 19.3.1/React DOM application, motion/scroll libraries and CSS. No editable TypeScript/React project, package manifest, framework server, router package configuration, lint/typecheck scripts or original build configuration is present in this repository.
- Section navigation is hash-based: home, directory, projects, profile, process, services, worldwide coverage, identity, contact and project brief. Dialogs use the same bundled client app. Fifteen real screenshot projects remain in `media/projects/`.
- Styling is plain embedded CSS with custom properties, embedded font data and responsive overrides, plus a local stylesheet for the lazily imported canvas globe. Animations include character videos, a WebGL project ribbon, scroll/reveal motion, an identity card and a pointer/touch fluid effect. Reduced-motion behaviour and EN/ZH/MS preferences already exist.
- GitHub Pages publishes the root of `gh-pages`; `.nojekyll` disables Jekyll processing. No checked-in Actions workflow exists. `CNAME` still records the previously used custom domain.

## Metadata and crawlability

- One homepage title and description, canonical, English Open Graph/Twitter tags and a real 1200×630 JPEG share image exist. The app also resets title/description in a client effect.
- `#root` is empty in the served HTML. The main headings, text, links and forms depend on JavaScript rendering. There are no separate service documents, sitemap, robots file, JSON-LD graph, Search Console integration or configured analytics ID in the baseline.
- There is one main client-rendered H1. It is a creative headline, without a descriptive Malaysia website-design positioning line. Some navigation/CTA elements are buttons that scroll rather than crawlable document links.
- Custom-domain DNS previously failed after the registrar account was frozen. The domain is not currently verified as reachable. SEO release configuration must therefore leave production origin unset until confirmed, block indexable builds without a verified origin, and use noindex previews without guessed canonical URLs.

## Existing content and commercial safeguards

- Preserve all fifteen project names, image mappings and original URLs; no unverified outcomes, delivery roles, testimonials, ratings or credentials should be added.
- Preserve all ten existing service categories. Add Google Ads Management and SEO Services without removing the existing SEO/launch/care offering.
- No fixed website package prices were found in the actual export. The RM figures are optional enquiry-budget choices, not published package prices; preserve them unchanged and do not turn them into fees.
- Contacts are verified in code: `kennystudio09@gmail.com`, displayed `+6011-6773 5644`, the existing WhatsApp conversation URL and Telegram account. The brief prepares a visitor-reviewed WhatsApp message. A separate legacy dialog optionally stores/downloads a local draft; no server submission endpoint exists.

## Recommended implementation

Keep the current app and visual identity. Introduce a reproducible static build for initial crawlable HTML and directory routes, instead of migrating frameworks. Keep the existing hash navigation, forms and animation code. Centralize production URL and verification/tracking IDs. Add service-specific metadata, links, structured data, sitemap/robots generation and validation. Do not publish production without approval.

## Scope update from owner

The owner confirmed the custom domain is still unavailable and requested restoring the default GitHub Pages URL for the existing demo, with SEO kept in preview. That separate hosting-only change was published as `e84b6db`; its GitHub deployment reports https://fnfmobilitymy-boop.github.io/fnf-mobility-platform/. SEO/new service work remains on `seo-services-preview-20261023`, outside the published branch. The production origin for an indexable SEO release remains unset.
