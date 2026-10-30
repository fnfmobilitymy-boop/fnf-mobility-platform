# Kenny chapter / typography preview

Preview: https://kennystudio.cfd/scroll-demo/

The reference is IMG_6121.MOV. Apply its page-to-page handoff direction to Kenny Studio, retaining the actual Kenny character, native autoplay videos, content, 23 projects, quote form, music and globe. Do not copy TRAVTHRU text or assets into Kenny.

React-owned chapter shells give visual sections one viewport of sticky travel. The globe and enquiry form use ordinary document flow to protect interactive content. The next section naturally covers the outgoing section, then releases it. A tall section scrolls all of its content before holding its final viewport. Geometry recalculates with fonts, section size and viewport changes. No wheel or touch events are intercepted. Anchor navigation targets each shell's normal-flow position, including when navigating backwards. No currentTime writes, video seeking, new frame sequence or rendering library.

Incoming corners flatten as the section arrives; copy enters more slowly and the outgoing copy remains readable. Reduced-motion mode uses ordinary document flow, clears sticky geometry and disables decorative camera motion.

Font: Manrope variable 200–800, licensed under SIL Open Font License. This is a similar geometric direction to the supplied Grift reference, not a claim to have licensed/installed Grift. English display headings use weight 800, upright and wider letterforms; Chinese uses the existing Noto Sans CJK SC fallback with separate sizing and wrapping. Self-hosted font and license included. Original brand colors and outlined middle title line remain.

Only `/scroll-demo/` and new uniquely named assets are deployed for this preview. Noindex, nofollow; excluded from sitemap. Production home, checkout preview and public service/pricing pages remain unchanged.

Validation: browser_chapter_stack at 1440, 1024, 768, 390 and 360 widths; EN/ZH/MS switching without reload; hold/cover/release and reverse navigation; full services content; reduced-motion cleanup. Reuse browser_integrations for globe controls, initial CLS, actual WebGL project navigation and existing consent behavior. Static SEO unit and internal-link checks also run.


## Refinement after user video / black-globe report

- Duplicate original `main > section` CSS selectors for `main > .chapter-shell > section`, preserving full specificity and the original enquiry form grid. This fixes the intro overlapping the form after chapter wrappers were introduced.
- Globe resize paints a first bitmap immediately, skips unnecessary bitmap resets, and recovers on context restoration. Geometry checks back up IntersectionObserver during transitions. This fixes the reproduced empty first canvas; tests inspect actual pixel values rather than only DOM presence.
- Globe and enquiry form do not pin, animate their copy or round their corners. The left form introduction is static. Visual chapters retain page-cover transitions.
- Fluid cursor simulation clears and sleeps over interactive sections and while scrolling; visible opacity elsewhere is reduced. Form values and all original project content remain intact.
- Globe data/attribution links resolve from the module URL, including the isolated preview path.
- Regression checks: 1440 / 1340 / 1024 / 768 / 390 / 360 widths with 1–2 DPR, EN/ZH/MS geometry, actual non-black canvas pixels on first load/re-entry/resize/restoration, wheel and two-finger zoom, country selection and enquiry-message preparation. No real customer messages are sent. No claim of guaranteed frame rates on all client devices.
