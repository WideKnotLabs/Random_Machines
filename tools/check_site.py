#!/usr/bin/env python3
"""Offline check: every href, src and srcset in every page resolves; every image has alt text; no third-party requests.
Usage: python3 tools/check_site.py"""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / 'index.html'] + sorted((ROOT / 'rmxy-1').rglob('index.html'))
problems = []


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids, self.imgs = [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'img':
            self.imgs.append(a)
        for key in ('href', 'src'):
            if key in a and tag in ('a', 'img', 'link', 'script'):
                self.refs.append((tag, a[key]))
        if 'srcset' in a:
            for part in a['srcset'].split(','):
                self.refs.append(('srcset', part.strip().split()[0]))


for page in PAGES:
    p = P()
    p.feed(page.read_text())
    if len(p.ids) != len(set(p.ids)):
        problems.append(f'{page.relative_to(ROOT)}: duplicate ids')
    for img in p.imgs:
        if img.get('alt') is None:
            problems.append(f'{page.relative_to(ROOT)}: image without alt {img.get("src")}')
    for tag, ref in p.refs:
        if re.match(r'(mailto:|https://wideknotlabs\.github\.io/Random_Machines/|https://www\.apple\.com/legal/|https://www\.instagram\.com/randommachines/$)', ref) or ref.startswith('#'):
            if ref.startswith('#') and ref[1:] not in p.ids:
                problems.append(f'{page.relative_to(ROOT)}: broken anchor {ref}')
            continue
        if re.match(r'https?:', ref):
            problems.append(f'{page.relative_to(ROOT)}: third-party URL {ref}')
            continue
        target = (page.parent / ref.split('#')[0].split('?')[0]).resolve()
        if not target.exists() and not (target / 'index.html').exists():
            problems.append(f'{page.relative_to(ROOT)}: missing {tag} {ref}')
print(f'Checked {len(PAGES)} pages.')
if problems:
    print('\n'.join(problems))
    sys.exit(1)
print('All references resolve; no third-party requests.')
