# SEO preview, configuration and release

## What changed

The existing static React export is preserved in `source/seo/legacy-export.html`. The build extracts/cache-versions its real CSS, font files and application bundle, with asserted patches for copy, service links/cards, image attributes and enquiry types. `source/seo/home.html` is the actual English app’s prerendered HTML, not placeholder content. React progressively replaces it after loading; this is not described as server-side React hydration. The actual repository has no original TypeScript project or framework server to rebuild, so a framework migration was avoided.

New static directory routes follow GitHub Pages’ native `route/index.html` convention:

- `/services/`
- `/services/website-design/`
- `/services/google-ads-management/`
- `/services/seo/`
- `/privacy/`

All have initial HTML copy, a unique English title/description, one H1, heading hierarchy, breadcrumbs, internal links, responsive navigation and EN/ZH/MS content. The homepage retains all 15 original project URLs/images and adds KENNY KITCHEN and WUKONG as clearly labelled concept demos, plus TRAVTHRU and the GLOBAL MARS furniture-service demo and ALYSSA LIM property-agent personal website demo and KENNY STORE footwear e-commerce concept demo and SALOON hair salon landing page demo (22 projects total), alongside ten original service categories, animations, reduced motion, music, language preference, form and budget choices. Two service categories and form choices were added. No fixed package prices were present, and no prices were invented or changed.

Google Ads covers the eight requested deliverables, a separate management fee and advertising spend paid separately to Google. SEO covers the ten requested deliverables, distinguishes website work from eligible Google Business Profile work, and gives no guaranteed ranking or lead promises. Real contact methods remain unchanged. New service quote links select the appropriate service in the existing WhatsApp-summary form.

## Build and local preview

Python 3.11+ builds the generated site without npm dependencies:

```sh
python3 scripts/build_site.py
python3 scripts/package_preview.py
python3 -m http.server 8126 --directory dist
```

Open http://localhost:8126/ and `/services/`. `PACKAGE_DIR` can override the package destination. `OUTPUT_DIR` can override the build destination. Keep the existing media and globe files beside the generated pages. The clean ZIP includes the required local media; it excludes source, docs, tests, archived frame sequences and large source movies.

Regenerate the homepage snapshot after deliberate app/content changes, with Python Playwright and Chromium installed:

```sh
python3 scripts/build_site.py
python3 scripts/prerender_home.py
```

The snapshot intentionally contains a disabled/inert interactive form when JavaScript is absent, with working email and WhatsApp alternatives. This avoids a no-JavaScript browser submitting personal form values in a default GET request. The existing live React form replaces it and behaves normally.

## Production domain: kennystudio.cfd

The owner selected `https://kennystudio.cfd`, completed the Spaceship DNS records, reported a successful GitHub DNS check, and confirmed the website opens after HTTPS activation. The old Namecheap domain is no longer the production origin. `.env.example` documents configuration; the build reads environment variables. It does not load or commit secret account files.

Preview defaults:

- `SITE_URL` unset; no guessed canonical or production URL in JSON-LD.
- `BUILD_INDEXABLE=false`; meta `noindex, follow` and robots `Disallow: /`.
- No sitemap is emitted for an all-noindex preview. This avoids an empty or invented-URL sitemap.
- Optional analytics is disabled, even if a tracking ID is present in the build environment.

Only after confirming the official domain, DNS, HTTPS and release approval, set:

```sh
export SITE_URL='https://kennystudio.cfd'
export SITE_URL_VERIFIED=true
export BUILD_INDEXABLE=true
python3 scripts/build_site.py
python3 scripts/package_preview.py
```

The URL above is the approved production origin. The build also emits its CNAME, and clean packaging preserves the binding. The builder rejects missing/unverified origins for an indexable build, query/fragment-bearing origins and invalid tracking identifiers.

The production build generates absolute per-route canonicals, matching OG URLs/images and Twitter metadata, an XML sitemap containing only the six canonical indexable pages, and robots with the sitemap URL. Query-string links do not create extra sitemap entries. `404.html` is noindex and excluded. Internal source/preview/admin paths are disallowed. The clean release package does not contain internal source or duplicate source HTML at all. GitHub Pages provides directory redirects; canonical links consolidate explicit `index.html` variants. Search engines determine indexing, not sitemap submission alone.

The JSON-LD graph uses verified Organization, WebSite, WebPage, Service and BreadcrumbList facts. No office address, reviews, ratings, certificates, pricing or campaign results are fabricated. English is the initial crawlable language; remembered client-side language preferences do not create alternate language URLs, so unsupported hreflang URLs are not emitted.

## Search Console

1. Confirm the real production origin and restore its DNS/HTTPS if necessary.
2. In your own Google Search Console account create the appropriate property. Domain-property DNS verification uses a real verification TXT record in the current Spaceship DNS provider.
3. For HTML-tag URL-prefix verification, copy the real token to `GOOGLE_SITE_VERIFICATION`, rebuild, deploy the approved release, then verify in Search Console. The build adds the tag only when supplied. No token has been invented or configured.
4. Submit the production `/sitemap.xml`; inspect homepage and service URLs, their selected canonicals and indexing reports.

## Analytics / Tag Manager and consent

No Google account ID has been supplied, and no analytics is enabled. For an approved production build set either `GA4_MEASUREMENT_ID` or `GTM_CONTAINER_ID` to the real ID, not both. No script or request to Google’s tag host occurs before opt-in. Essential-only choices and withdrawal persist locally. Ad-related storage/personalisation consent remains denied; analytics storage is granted only after opt-in.

A GTM container must be reviewed so its tags respect consent; adding a container ID is not a substitute for configuring its tags correctly. No advertising-conversion ID or event results are fabricated. Test real account receipt and your privacy/consent requirements before enabling measurement. The privacy page documents the actual form/local-storage behaviour and third-party links. It is factual site copy, not a claim of legal certification.

## Validation performed

- Python build and compilation; Node syntax checks for generated JS. There were no existing npm build, lint or TypeScript/typecheck tasks. No such tasks are falsely reported as passing.
- Five automated SEO build tests: unique initial metadata/H1/content, preview/production URL safeguards, six-route production sitemap, canonical consistency, JSON-LD facts, real-token hooks, preservation of projects/contacts/budget strings and default tracking off.
- Internal link/asset/font checks, including fragments and project-subpath hosting.
- Browser tests at 1440, 1024, 768, 390 and 360px: all new routes, English/Chinese/Malay, mobile navigation, typed quote CTAs and original form, no horizontal overflow, no missing assets/runtime errors.
- JavaScript-disabled crawlability and safe form fallback; curved WebGL project gallery, globe wheel/selection and reduced motion.
- Local initial homepage CLS measured 0.0 in the tested Chromium run. This is not field Core Web Vitals, a Lighthouse score, or a promise of performance on every device. Animations and source media remain substantial; Search Console/CrUX should be reviewed after an approved release.
- Local-only synthetic test fixtures verify GA4/GTM consent gating without contacting Google. No fixture IDs/tokens are used by the preview or production configuration.

## Release approval

The owner explicitly approved publishing the SEO build to `kennystudio.cfd` on 2026-10-23. Deploy only the clean package contents to `gh-pages`; retain this source branch for future builds. Real Search Console and analytics IDs remain unconfigured. The release retains the latest neon HELLO intro, reference opening sound, background song and visitor-interaction playback fallback.
