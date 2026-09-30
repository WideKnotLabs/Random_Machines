#!/usr/bin/env python3
"""Shared header and footer for every RMXY-1 page.

Pages carry marker comments; run this file to rewrite the chrome between them:
    <!-- chrome:header -->...<!-- /chrome:header -->
    <!-- chrome:footer -->...<!-- /chrome:footer -->
"""
from pathlib import Path
import re

SITE = Path(__file__).resolve().parents[1] / 'rmxy-1'
CONTACT = 'wideknotlabs@gmail.com'

NAV = [('manual', 'manual/', 'Manual'), ('support', 'support/', 'Support')]

# page path relative to rmxy-1/ -> (prefix back to rmxy-1/, current nav key)
PAGES = {
    'index.html': ('', None),
    'support/index.html': ('../', 'support'),
    'privacy/index.html': ('../', None),
    'terms/index.html': ('../', None),
    'manual/index.html': ('../', 'manual'),
}


def logo_width(name, height):
    """Width of a logo file at a given height, from its own viewBox so the aspect ratio is never guessed."""
    svg = (SITE / 'assets/logo' / name).read_text()
    _, _, w, h = re.search(r'viewBox="([^"]+)"', svg).group(1).split()
    return round(height * float(w) / float(h))


def header(prefix, current):
    here = ' aria-current="page"'
    links = ''.join(
        f'<a href="{prefix}{href}"{here if key == current else ""}>{label}</a>'
        for key, href, label in NAV
    )
    return f'''<header class="nav">
    <div class="nav__inner">
      <a class="nav__brand" href="{prefix or './'}" aria-label="Random Machines, RMXY-1 home">
        <img class="nav__logo nav__logo--full" src="{prefix}assets/logo/rm-lockup-stacked-on-dark.svg" alt="" width="{logo_width('rm-lockup-stacked-on-dark.svg', 40)}" height="40">
        <img class="nav__logo nav__logo--symbol" src="{prefix}assets/logo/rm-symbol-on-dark.svg" alt="" width="{logo_width('rm-symbol-on-dark.svg', 40)}" height="40">
      </a>
      <nav class="nav__links" aria-label="Main">{links}</nav>
    </div>
  </header>'''


def footer(prefix):
    return f'''<footer class="footer">
    <div class="footer__inner">
      <a class="footer__brand" href="{prefix or './'}" aria-label="Random Machines, RMXY-1 home">
        <img src="{prefix}assets/logo/rm-lockup-stacked-on-dark.svg" alt="" width="{logo_width('rm-lockup-stacked-on-dark.svg', 52)}" height="52" loading="lazy">
      </a>
      <ul class="footer__links">
        <li><a href="{prefix}manual/">Manual</a></li>
        <li><a href="{prefix}support/">Support</a></li>
        <li><a href="{prefix}privacy/">Privacy Policy</a></li>
        <li><a href="{prefix}terms/">Terms of Use</a></li>
        <li><a href="mailto:{CONTACT}">Contact</a></li>
      </ul>
    </div>
    <div class="footer__legal">
      <p>© 2026 Random Machines. RMXY-1 is published by Borja Deudero Gracia.</p>
      <p>iPhone, iPad and App Store are trademarks of Apple Inc., registered in the U.S. and other countries. Elektron, Digitakt, Arturia and MicroFreak are trademarks of their respective owners. Random Machines is not affiliated with them.</p>
    </div>
  </footer>'''


def stamp(html, prefix, current):
    html, n1 = re.subn(r'<!-- chrome:header -->.*?<!-- /chrome:header -->',
                       lambda _: f'<!-- chrome:header -->\n  {header(prefix, current)}\n  <!-- /chrome:header -->', html, flags=re.S)
    html, n2 = re.subn(r'<!-- chrome:footer -->.*?<!-- /chrome:footer -->',
                       lambda _: f'<!-- chrome:footer -->\n  {footer(prefix)}\n  <!-- /chrome:footer -->', html, flags=re.S)
    assert n1 == 1 and n2 == 1, 'page is missing chrome markers'
    return html


if __name__ == '__main__':
    for rel, (prefix, current) in PAGES.items():
        path = SITE / rel
        path.write_text(stamp(path.read_text(), prefix, current))
        print('stamped', rel)
