# JAGUAR — Video Editor & Colorist

The original portfolio restored from `index-1.html`, now branded with the JAGUAR
mark from the repository's `Jaguar.avif`. The original layout, textures, film
grain, cursor, particle field, animations, showreel, and project media are preserved;
the theme and effect colors now match the logo's greens. The broken extensionless
`portfolio` duplicate and replacement `styles.css` have been removed.

The hero background video starts after the loading curtain lifts, plays once,
and smoothly dissolves into green ambient lighting before its final frame. Grain,
particles, and lighting continue so the page does not look frozen. The clip pauses
when offscreen or in a hidden tab and never restarts after ending. Playback is
disabled for reduced-motion preferences. Set `CONFIG.heroVideo` to change the
clip. Watch Reel and project videos are unchanged.

The hero also includes flowing green aurora ribbons, glowing drifting dust,
moving light trails, green light sweeps, hexagonal outlines, and a pointer-reactive
spotlight. Aurora uses a pre-rendered WebP texture; dust and trails use CSS, so they work
on mobile and without the external JavaScript libraries. Layers stay behind the text and
pause offscreen and while the tab is hidden. Reduced-motion preferences stop
animation, hide light trails, and disable pointer glow.

## Brand assets and colors

- `assets/jaguar.avif`: the original image from GitHub, preserved unchanged.
- `assets/jaguar-mark.png`: the J emblem cropped from that image, with its white
  background removed. The stock “COMPANY LOGO / TAGLINE HERE” text is not used.
- `assets/favicon.png`: the same emblem sized for the browser tab.
- Primary green: `#3ba543` (RGB 59, 165, 67).
- Secondary lime: `#8bbb33` (RGB 139, 187, 51), sampled from the emblem's tip.

The mark appears beside the JAGUAR name in the navigation and in the footer.
Edit `--c1`, `--c2`, `--c1-rgb`, and `--c2-rgb` together in the inline CSS to
adjust the palette. Glows, gradients, glitch effects, and other accents use those
tokens; the Three.js particles read the same CSS colors. The aurora texture uses those
sampled greens; regenerate it with `scripts/generate_aurora.py` if the palette changes. Form errors remain red
as a functional warning, not a decorative accent.

## Preview locally

```sh
python3 -m http.server 8000 --bind 0.0.0.0
```

Open `http://localhost:8000` on your own computer, or your environment's forwarded
preview URL. No build step is needed. You can also open `index.html` directly for
a quick visual check; use an HTTP server when testing a configured contact API.

Fonts, animation libraries, and placeholder images/videos load from external
hosts, so internet access is needed for the full experience. If the animation
libraries cannot load, some effects will be unavailable.

## Customize

Edit the `CONFIG` object inside `index.html` to set your name, email, media,
projects, client marquee, and social links. The original demo media and text are
intentionally unchanged. Verify the email, social URLs, testimonials, statistics,
and pricing before publishing.

Set `CONFIG.formEndpoint` to a real form service/API that accepts multipart POSTs
and returns a successful HTTP status after accepting the message. With no endpoint,
the form now explicitly says the message was **not sent**, rather than pretending
it was delivered. No backend is included in this repository.

## Ask Jaguar assistant

The floating **Ask Jaguar** button opens an accessible chat panel styled with the
brand palette. `assistant.js` answers common questions about the site's services,
packages, listed prices, process, tools, work, and contact details. It is a basic
built-in portfolio helper, not an external AI model. There are no demo labels in
the visitor interface. Messages stay in memory in the current tab; they are not
stored locally or sent to an AI service unless a backend is configured.

Recommended model for a future integration: **GPT-4.1 mini**. The backend should
choose the model; no provider credentials belong in `index.html`, `CONFIG`, or
`assistant.js`.

To enable real AI later:

1. Deploy a secure backend route on the same origin, such as `/api/assistant`.
   Store its provider API key in a server-side environment variable. Add request
   validation, body limits, rate limits, spending limits, and abuse protection.
2. Have the route accept JSON `{ "message": "...", "history": [...] }` and return
   `{ "reply": "..." }` on success, or a non-2xx status on failure. History contains
   at most the previous 12 messages with `role` and `content` fields. Treat all
   client-provided messages as untrusted; the backend must supply its own system
   instructions and trusted portfolio information. Do not let it invent bookings,
   completed projects, final quotes, or delivery confirmations.
3. Set `CONFIG.assistantEndpoint` to `/api/assistant`. The client rejects
   cross-origin endpoints, times out after 20 seconds, and displays errors safely.
   It renders all responses as plain text, not executable HTML.
4. Add an appropriate privacy disclosure before enabling a live provider.

No AI backend is included yet; the static preview cannot call a model on its own.
Deploy `index.html`, `assistant.js`, and `assets/` together. Test opening/closing,
Escape and focus restoration, suggested questions, portfolio replies, and API failures
when an endpoint is configured.

## Checks

```sh
python3 -m unittest discover -s tests -v
npx --yes --package html-validate html-validate index.html
```

Python tests check structure, navigation targets, design hooks, control semantics,
and JavaScript syntax (the syntax test requires Node.js). HTML validation requires
Node.js/npm. `.htmlvalidate.json` allows the original inline styles, muted background
autoplay video, and accessible label on the animated heading; these are deliberate
design choices, not syntax errors. GitHub Actions runs the Python/JS checks.

For manual testing, check desktop/mobile layouts, project filters, video modal
open/close and Escape, mobile menu, keyboard focus, before/after slider arrow and
Home/End keys, reduced motion, and contact validation. Automated structural checks
do not replace a visual/browser accessibility audit.

## Performance and publishing

The aurora blur is pre-rendered in `assets/aurora.webp` instead of recalculated
by an animated, full-screen SVG filter. The video fade runs on its own composited
layer; the decoded video is released after the transition. WebGL particles start
only afterward, during idle time, with a smaller 350-point field. The pointer glow
moves a bounded texture instead of repainting a full-screen gradient each frame.

To regenerate the aurora asset, install Pillow in a development environment and
run `python scripts/generate_aurora.py`. Pillow is not needed by visitors or Pages.

GitHub Pages serves the root of `main`:
https://corelink-sudo.github.io/portfolio/

Develop and push changes on `arena/05725cdf-portfolio`, then publish through a
pull request into `main`. GitHub builds and deploys Pages after the merge.
`.nojekyll` enables direct static serving; no Pages settings changes are needed.
