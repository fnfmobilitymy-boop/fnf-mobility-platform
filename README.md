# Kenny Studio — native scroll portfolio

A static, framework-free HTML/CSS/JavaScript website for Kenny Studio, served from the root of `gh-pages` at https://kennystudio.space/.

## Run locally

Place `index.html` beside the complete `frames/` directory, then run:

```sh
python3 -m http.server 8123
```

Open http://localhost:8123/. No npm install or build step is required to run the supplied site.

## Scroll-controlled backgrounds

Five original character scenes run from pre-extracted WebP frame sequences on a fixed, fullscreen Canvas. The page does not use background video elements or `video.currentTime` seeking. Scroll down advances frames and scroll up reverses them. Frame movement has damping and a speed limit; the copy fades and moves in the scroll direction near each node’s end. Each node holds until two additional deliberate scroll gestures; mouse wheels and touch gestures are supported. Fixed navigation can jump directly to a node’s readable state. Home and contact CTA buttons have a repeating subtle animation.

The five-node order is Hero/game room → creative desk → exercise/process → everyday life/services → final greeting/contact. The Hero sequence includes the large, behind-character HI! / I’M KENNY captions.

`CONFIG` near the beginning of the application script in `index.html` centralizes the frame rate, scroll distance, damping, maximum frame speed, text fade range/duration, hold-gesture count, cache sizes and gallery timing. Defaults include 24 source frames per second, a maximum of 72 displayed sequence frames per second, and two end-hold gestures. Reduced motion shows static end frames and disables automatic animation.

The supplied sequences contain 241 frames each, in separate desktop (828px; preserved caption frames may be 960px) and mobile (480px) sizes. Frames are loaded around the current playhead with bounded decoded-image caches; the entire frame set is not preloaded. The scroll playhead advances independently of downloads; slow connections show the nearest decoded frame without locking page scrolling. Rendering is capped at 30 canvas paints per second and stops when the frame and text opacity settle, including at intermediate positions. Decoded images are cached within a fixed limit, and stale scene requests are dropped. Sequences are extracted from the original movies rather than upscaled from the smaller streaming encodes; the existing behind-character Hero caption frames remain. Desktop uses a single sharp character image without an enlarged, low-resolution duplicate. Canvas and globe work pause offscreen or when the page is hidden.

### Rebuild frame assets

The original high-resolution movies and optimized captioned movie remain in `media/`. `build-frames.sh` regenerates the supplied sequences with FFmpeg. For example:

```sh
mkdir -p frames/about/desktop
ffmpeg -y -i media/work.mp4 -an \
  -vf "fps=24,scale=828:-2" -c:v libwebp -q:v 72 -compression_level 2 \
  frames/about/desktop/frame_%04d.webp
```

For mobile, use `scale=480:-2` and `frames/about/mobile/`. If changing fps/duration or file counts, update the corresponding `CONFIG` values and frame manifest.

## Website features

- A global language menu switches English, Chinese and Bahasa Melayu across navigation, story copy, services, gallery controls, globe controls and the inquiry form. The selected language is remembered. English share metadata remains English even when the site language changes.
- Fifteen user-supplied website screenshots appear in a curved WebGL gallery, with a CSS card fallback, automatic advance, hover/focus pause, drag/touch, keyboard and previous/next controls. All original website URLs remain.
- Ten service categories cover landing pages, personal brands, business websites, e-commerce, bookings, CMS/admin dashboards, custom systems, backend integrations, redesign and SEO/maintenance.
- A reference-inspired starfield and dotted globe rotates automatically. The searchable/filterable directory contains 250 countries and regions, including small territories, with selection/centering, mouse/touch rotation, zoom, reset, keyboard controls and reduced-motion support. Collaboration is described as remote availability; no offices or client history are invented.
- The project brief requires name, project type and a description. Company, budget and six features are optional. It prepares a localized, reviewable summary and a WhatsApp link. No site server sends or stores form entries. Values survive a language switch in memory and clear on reload.
- A 96 kbps music asset reduces the background audio download from 7.6 MB to 2.3 MB. Daylight background music defaults on and loops, retries after a user gesture when autoplay is blocked, and remembers manual mute. Native browser autoplay rules still apply.
- Purple/cyan fluid follows mouse and touch movement without blocking ordinary page scrolling. Mobile uses a smaller simulation; reduced motion disables the effect.

## Contact and previews

- Email: kennystudio09@gmail.com
- WhatsApp: https://wa.me/message/DHXOYXRCJIKZK1
- WhatsApp project summary recipient: +6011-6773 5644
- Telegram: https://t.me/KennyStudio

Static English Open Graph/Twitter tags and an English homepage cover are included. Social applications may retain older preview caches; deployment alone does not force their cache refresh.

## Verification

Checked forward/reverse sequences, frame-speed limits, five-node navigation, two-gesture holds on wheel and real browser touch input, late text visibility, desktop/390px/360px layouts, mobile-only frame loading, three-language switching, preserved form data during language switches, correct WhatsApp recipient and encoding, no entries after reload, gallery controls/curved rendering, all 250 country/region selections, globe centering/drag/zoom/keyboard/offscreen behavior, music autoplay/gesture recovery/mute persistence, and reduced motion. No background video elements or runtime errors were found in these checks. Real-device performance depends on the device and connection.

Map geometry: Natural Earth (public domain), distributed via world-atlas. Country/region data: world-countries; adapted data in `frames/globe/countries.json` is available under ODbL. Attribution and dependency notices are included in `frames/globe/` and font notices in `frames/fonts/`.

Performance regression checks: intermediate-opacity idle has zero story redraws; stalled frame requests do not block the two-gesture exit. Mobile scroll checked with a 4× CPU throttle and 1.6 Mbps / 150 ms network conditions. These are browser simulations, not a guarantee for every physical device.
