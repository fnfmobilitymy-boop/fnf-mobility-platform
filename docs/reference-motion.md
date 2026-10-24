# Reference-inspired chapter motion

Approved scope: the owner has no rigged Kenny model or matching replacement action footage and chose to approximate the reference using the five existing Kenny MP4 clips. Character identity, footage, captions, content, forms, prices/budget options, projects, globe, navigation, music and SEO remain intact. This is not a claim of identical skeletal or facial animation.

`source/motion/chapter-flow.js` replaces only the legacy chapter-flow hook during the static build. `assets/reference-motion.css` supplies the native-video camera transform. `KENNY_REFERENCE_MOTION` centralizes timing, camera strength, scroll damping, text entry/exit distances and scrub duration.

The hero camera follows decoded video timestamps, moving from a wide view toward the existing greeting and returning to the wide view. Desktop zoom is capped at 1.26 and mobile at 1.10. It never assigns `video.currentTime`, changes video playback rate, extracts frames or replaces source footage. Callbacks stop when the video is paused/offscreen/hidden. Scrolling uses the existing Lenis/GSAP stack with text entry/exit, a cassette approach, subtle gallery arrival and alternating timeline entries. No pinned section changes page heights or navigation anchors.

Reduced motion reverts the chapter context, removes the camera transform and keeps all content accessible. Native touch scrolling, menus and globe gestures remain unchanged. The production packager includes the generated CSS/JS, not the reference recording or internal source files.

Validation: native camera closeup and return at 1440 and 390 px, every chapter forwards/backwards, dynamic reduced-motion cleanup, three global languages, all service routes and quote form at 1440/1024/768/390/360 px, real software-WebGL gallery, globe interactions and local-only consent fixtures. Browser tests check missing assets/runtime errors and layout overflow. Local initial CLS observed as 0.0; this is not a field performance guarantee.

Run with a clean packaged site served on port 8133:

```sh
PREVIEW_URL=http://127.0.0.1:8133/ python3 tests/browser_reference_motion.py
```
