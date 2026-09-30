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

- `rmxy-1/assets/site.css` holds every token and component: near-black page, bone ink, hairlines, one accent (orange `#FF6A00`), one radius, Space Grotesk (the app's own typeface, self-hosted). All pages use it; do not add page-specific stylesheets.
- No cards, glows, pills, eyebrows or scroll effects. Two section patterns on the landing page: a text column beside one visual, and spec rows.
- `rmxy-1/assets/site.js` is progressive enhancement: the XY pad, effect-slot and scene-bank demonstrations, document contents, and the manual drawer and search. Nothing moves on its own. Every page reads fine without it.
- Header and footer live in `tools/site_chrome.py`. Pages mark them with `<!-- chrome:header -->` / `<!-- chrome:footer -->`; run `python3 tools/site_chrome.py` after changing navigation or footer links.
- Logo: the Random Machines grid symbol and machined wordmark, copied from `RMX1-Logo/random-machines/svg/` in the app repository into `rmxy-1/assets/logo/` (stacked lockup in the header, footer and root redirect; symbol alone in the header below 350 px). The favicon and touch icon are the symbol on ink. Read that folder's README before changing anything; change its `source/` and rebuild there, then recopy. Widths come from each file's own `viewBox`.

## Manual

The manual's single source is the app repository: `documentation/product/user-manual.md` plus its `manual/assets/*.svg` diagrams. Rebuild the site edition with:

```sh
python3 tools/build_manual.py ~/Desktop/RMXY
```

It copies the diagrams, renders the Markdown into the site layout, and verifies anchors, links and images. Requires `markdown2`. Never edit the manual text here.

## Screenshots

`rmxy-1/assets/shots/*.webp` are frameless captures from the app's Debug visual-QA runner, taken on a copy of the scene store at real device sizes (iPad Air 11″ 1180 × 820 pt; phone shots are frameless). `*-sm.webp` files are half-size variants for `srcset`. The local-only `docs/` folder (not published) has the full capture recipe, the crop values for the macOS-only test-transport row, and the list of capture steps. `hw-digitakt.svg` and `hw-microfreak.svg` are line drawings made for this site, not product photos.

## Checks

```sh
python3 tools/check_site.py    # every href, src and srcset resolves; alt text; no third-party requests
python3 tools/build_manual.py ~/Desktop/RMXY
```

## Rules

- Public pages only: no login, analytics, tracking pixels, newsletter forms, ads, or third-party requests (fonts are self-hosted).
- No "coming soon" or placeholder copy. Footer links to Support, Privacy and Terms on every page.
- Copy is plain and factual, in the owner's own words. No wordplay.
- Same identity everywhere: RMXY-1, Random Machines, Borja Deudero Gracia.
- Keep the privacy policy in step with App Store Connect's privacy answers.
- Third-party names (Apple, Elektron, Arturia) are trademarks of their owners; the footer says so.
