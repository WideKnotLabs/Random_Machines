# Random Machines

Static public site for Random Machines and its first app, RMXY-1. Plain HTML, one stylesheet, one script; no build step is needed to serve it.

## Pages

- Landing: `/rmxy-1/`
- Manual: `/rmxy-1/manual/` (generated, see below)
- Support: `/rmxy-1/support/`
- Privacy Policy: `/rmxy-1/privacy/`
- Terms of Use: `/rmxy-1/terms/`

App Store Connect URLs (GitHub Pages):

- Marketing URL: `https://wideknotlabs.github.io/Random_Machines/rmxy-1/`
- Support URL: `https://wideknotlabs.github.io/Random_Machines/rmxy-1/support/`
- Privacy Policy URL: `https://wideknotlabs.github.io/Random_Machines/rmxy-1/privacy/`

## Design system

- `rmxy-1/assets/site.css` holds every token and component. It follows the round-3 plan (`docs/round3-plan.md`): a black stage where the app is the only colour, `#0b0b0c` bands, `#f5f5f7` ink, 1 px graphite hairlines, 28 px media corners, pill buttons, no shadows or gradients on chrome. One typeface (Space Grotesk, the app's own, self-hosted) at 600 with tight tracking for headlines. One accent, the logo orange `#FF6A00`, used only as punctuation (live dots, the focus ring, the effects ring). The app's lime appears only inside captures. All pages use it; do not add page-specific stylesheets.
- `rmxy-1/assets/site.js` is progressive enhancement for every page: document contents and the manual drawer and search.
- `rmxy-1/assets/landing.js` runs only on the landing page. Everything it shows of the app is a real capture (`rmxy-1/assets/media/`); it only stages them:
  - reveals on scroll, and plays the videos only while they are on screen;
  - the hero iPad rises and settles as you scroll;
  - the effects section pins and walks slot 6 through all nineteen captures (`fx-<id>.webp`) as you scroll; the list and the one-line description follow. Update the list in `index.html` when the app's effects change;
  - "Built to perform" zooms a lens on the main-screen capture onto each control. The rectangles are in app points on the 1180 × 820 iPad screen (`data-rect` on each tab);
  - under `prefers-reduced-motion` nothing moves on its own and nothing pins.
- Devices are flat slim frames drawn in CSS (`.device--ipad`, `--phone-land`, `--phone`): no bevel, no island, no buttons, the screen fills the frame with the device's own corner radius.
- Without JavaScript every device falls back to a real screenshot.
- Header and footer live in `tools/site_chrome.py`. Pages mark them with `<!-- chrome:header -->` / `<!-- chrome:footer -->`; run `python3 tools/site_chrome.py` after changing navigation or footer links.
- Logo: the Random Machines grid symbol and machined wordmark, copied from `RMX1-Logo/random-machines/svg/` in the app repository into `rmxy-1/assets/logo/` (stacked lockup in the header, footer and root redirect; symbol alone in the header below 350 px). The favicon and touch icon are the symbol on ink. Read that folder's README before changing anything; change its `source/` and rebuild there, then recopy. Widths come from each file's own `viewBox`.
- The app icon in the hero (`rmxy-1/assets/rmxy-1-icon.svg`) is a copy of `RMX1-Logo/ios/AppIcon-master.svg`.

## Manual

The manual's single source is the app repository: `documentation/product/user-manual.md` plus its `manual/assets/*.svg` diagrams. Rebuild the site edition with:

```sh
python3 tools/build_manual.py ~/Desktop/RMXY
```

It copies the diagrams, renders the Markdown into the site layout, and verifies anchors, links and images. Requires `markdown2`. Never edit the manual text here.

## Screenshots

`rmxy-1/assets/media/` holds every capture the landing page shows, all from the app's Debug visual-QA runner on a copy of the scene store, with the same rack in every shot (Filter, Delay, Verb, EQ, Drive, Cloud, Erode, Fold). iPhone captures are 402 × 874 pt at 3x with the iOS status bar and home indicator; iPad captures are 1180 × 820 pt at 2x. The videos (`phone-main`, `hero-ipad`) loop seamlessly; `key-<id>.webp` are the slot keys for the effects grid. The local-only `docs/` folder (not published) has the capture recipe.

`hw-digitakt.svg` and `hw-microfreak.svg` are line drawings made for this site from the makers' published top views (panel layout only, no photos or logos). They carry their own small animations. Regenerate them with `python3 tools/draw_hardware.py`; do not hand-edit.

## Share image

`rmxy-1/assets/shots/og.png` (1200 × 630 at 2x, lossless PNG) is rendered from `tools/og.html`: the large XY-1 wordmark (`assets/logo/xy-1-wordmark.svg`, a tight crop of `RMX1-Logo/rmxy-1-logo.svg`, never the square app icon) with the headline in two lines beside it, above the app on a drawn iPad, cut off at the bottom. The screen comes from the lossless window screenshot in `tools/og-source/` (Dark theme, Fold editor open; see `build_og.py` for how it was prepared); `build_og.py` swaps its macOS-only test row for the iPad status-bar area so the app fills the 1180 × 820 pt screen exactly. After changing the headline or the capture, rebuild it with:

```sh
python3 tools/build_og.py    # needs Google Chrome and websocket-client
```

## Checks

```sh
python3 tools/check_site.py    # every href, src and srcset resolves; alt text; no third-party requests
python3 tools/build_manual.py ~/Desktop/RMXY
```

## Rules

- Public pages only: no login, analytics, tracking pixels, newsletter forms, ads, or third-party requests (fonts are self-hosted).
- No "coming soon" or placeholder copy, with one exception the owner asked for: the greyed-out App Store button in the hero says "Coming soon" until the app is live. Replace it with the App Store link at launch. Footer links to Support, Privacy and Terms on every page.
- Copy is short, direct and factual: headlines that land in a few words (Torso, Elektron), no wordplay, no filler, no minor housekeeping features (bypass, solo, reorder) in the story.
- Same identity everywhere: RMXY-1, Random Machines, Borja Deudero Gracia.
- Keep the privacy policy in step with App Store Connect's privacy answers.
- Third-party names (Apple, Elektron, Arturia) are trademarks of their owners; the footer says so.
