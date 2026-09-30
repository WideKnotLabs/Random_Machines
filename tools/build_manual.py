#!/usr/bin/env python3
"""Build rmxy-1/manual/ from the app repository's user manual.

Source of truth: <RMXY repo>/documentation/product/user-manual.md and its manual/assets/*.svg.
Usage:  python3 tools/build_manual.py [path/to/RMXY]   (default: ~/Desktop/RMXY or $RMXY_REPO)
Requires Python 3 and markdown2.
"""
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
import json
import os
import re
import shutil
import sys
import unicodedata
import xml.etree.ElementTree as ET

import markdown2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_chrome import header, footer  # noqa: E402

REPO = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get('RMXY_REPO', Path.home() / 'Desktop/RMXY')).expanduser()
SOURCE = REPO / 'documentation/product/user-manual.md'
SOURCE_ASSETS = REPO / 'documentation/product/manual/assets'
OUT = Path(__file__).resolve().parents[1] / 'rmxy-1/manual'
SITE_URL = 'https://wideknotlabs.github.io/Random_Machines/rmxy-1/'


def slug(title):
    value = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', value)).strip('-')


def md(value):
    rendered = str(markdown2.markdown(value, extras=['tables']))
    rendered = rendered.replace('src="manual/assets/', 'src="assets/')

    def figure(m):
        src, alt = m.group(1), m.group(2)
        _, _, width, height = ET.parse(OUT / src).getroot().attrib['viewBox'].split()
        return (f'<figure><div class="diagram"><a href="{src}" aria-label="Open full-size illustration">'
                f'<img src="{src}" alt="{alt}" width="{width}" height="{height}" loading="lazy"></a></div>'
                f'<figcaption>{alt}</figcaption></figure>')

    rendered = re.sub(r'<p><img src="([^"]+)" alt="([^"]*)"\s*/></p>', figure, rendered)
    return (rendered
            .replace('<table>', '<div class="table-scroll" tabindex="0" role="region" aria-label="Reference table"><table>')
            .replace('</table>', '</table></div>'))


def main():
    if not SOURCE.exists():
        sys.exit(f'Manual source not found: {SOURCE}')
    (OUT / 'assets').mkdir(parents=True, exist_ok=True)
    for svg in SOURCE_ASSETS.glob('*.svg'):
        shutil.copy2(svg, OUT / 'assets' / svg.name)

    raw = SOURCE.read_text()
    parts = re.split(r'^(#{1,3}) (.+)$', raw, flags=re.M)
    headings = [(len(parts[i]), parts[i + 1].strip(), parts[i + 2]) for i in range(1, len(parts), 3)]
    chapters, intro, title = [], '', 'RMXY-1 User Guide'
    for level, heading, body in headings:
        if level == 1:
            title, intro = heading, md(body)
        elif level == 2:
            chapters.append({'title': heading, 'id': slug(heading), 'intro': body, 'lessons': []})
        else:
            chapters[-1]['lessons'].append({'title': heading, 'id': slug(heading), 'body': body})
    ids = [c['id'] for c in chapters] + [l['id'] for c in chapters for l in c['lessons']]
    assert len(ids) == len(set(ids)), 'Duplicate heading IDs'

    nav, content, search = [], [], []
    for n, c in enumerate(chapters):
        num, _, name = c['title'].partition(' — ')
        name = name or c['title']
        num = num if name != c['title'] else f'{n + 1:02d}'
        c['name'] = name
        sub = ''.join(f'<li><a href="#{l["id"]}">{escape(l["title"])}</a></li>' for l in c['lessons'])
        nav.append(f'<li data-chapter="{c["id"]}"><a href="#{c["id"]}"><span>{escape(num)}</span>{escape(name)}</a><ul class="subnav">{sub}</ul></li>')
        content.append(f'<section class="m-chapter" id="{c["id"]}" aria-labelledby="h-{c["id"]}">'
                       f'<header class="m-chapter__head"><span class="m-chapter__num">{escape(num)}</span><h2 id="h-{c["id"]}">{escape(name)}</h2></header>')
        if len(c['lessons']) > 12:
            content.append('<nav class="effect-index" aria-label="In this chapter">'
                           + ''.join(f'<a href="#{l["id"]}">{escape(l["title"])}</a>' for l in c['lessons']) + '</nav>')
        content.append(md(c['intro']))
        for l in c['lessons']:
            rendered = md(l['body'])
            content.append(f'<section class="m-lesson" id="{l["id"]}" aria-labelledby="h-{l["id"]}"><h3 id="h-{l["id"]}">{escape(l["title"])}</h3>{rendered}</section>')
            plain = unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', rendered)).strip())
            search.append({'title': l['title'], 'id': l['id'], 'chapter': name, 'text': plain})
        if n + 1 < len(chapters):
            nxt = chapters[n + 1]
            nxt_name = nxt['title'].partition(' — ')[2] or nxt['title']
            content.append(f'<a class="next-chapter" href="#{nxt["id"]}"><span>Next</span>{escape(nxt_name)}<span aria-hidden="true">→</span></a>')
        content.append('</section>')

    search_json = json.dumps(search, ensure_ascii=False).replace('<', '\\u003c')
    html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Manual — RMXY-1 | Random Machines</title>
  <meta name="description" content="The RMXY-1 user guide: the main screen, Base/X/Y mapping, every effect, the audio looper, scenes and programs, MIDI, AUv3 and Settings.">
  <meta name="theme-color" content="#07090b">
  <link rel="canonical" href="{SITE_URL}manual/">
  <link rel="icon" href="../assets/favicon.ico">
  <link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
  <link rel="preload" href="../assets/fonts/space-grotesk.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="../assets/site.css">
</head>
<body>
  <a class="skip" href="#main">Skip to the guide</a>
  <!-- chrome:header -->
  {header('../', 'manual')}
  <!-- /chrome:header -->
  <button class="manual-toggle" type="button" aria-expanded="false" aria-controls="contents">Contents</button>
  <div class="manual">
    <aside class="manual__side" id="contents" aria-label="Guide contents">
      <div class="manual__side-inner">
        <div class="search">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
          <input type="search" id="manual-search" placeholder="Search the manual" aria-label="Search the manual" autocomplete="off">
        </div>
        <p class="search-status" id="search-status" role="status" aria-live="polite"></p>
        <ol class="results" id="search-results" hidden></ol>
        <nav aria-label="Chapters"><ol class="chapters">{''.join(nav)}</ol></nav>
      </div>
    </aside>
    <main class="manual__main" id="main">
      <article class="manual__article">
        <header class="manual-cover" id="top">
          <h1>{escape(title)}</h1>
          <div class="preface">{intro}</div>
          <div class="manual-tools">
            <a class="btn btn--primary" href="#{chapters[0]['id']}">Start reading</a>
            <button class="btn btn--ghost" id="print" type="button">Print or save as PDF</button>
          </div>
        </header>
        {''.join(content)}
      </article>
    </main>
  </div>
  <!-- chrome:footer -->
  {footer('../')}
  <!-- /chrome:footer -->
  <script id="search-data" type="application/json">{search_json}</script>
  <script src="../assets/site.js" defer></script>
</body>
</html>
'''
    (OUT / 'index.html').write_text(html)

    class Verify(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids, self.links, self.images = [], [], []

        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if 'id' in a:
                self.ids.append(a['id'])
            if tag == 'a':
                self.links.append(a.get('href', ''))
            if tag == 'img':
                self.images.append(a)

    v = Verify()
    v.feed(html)
    assert len(v.ids) == len(set(v.ids)), 'Duplicate HTML IDs'
    for href in v.links:
        if href.startswith('#'):
            assert href[1:] in v.ids, f'Broken anchor {href}'
        elif not re.match(r'(https?:|mailto:)', href):
            target = (OUT / href.split('#')[0])
            assert target.exists(), f'Broken file link {href}'
    for img in v.images:
        assert img.get('alt') is not None, 'Missing image alt text'
        assert (OUT / img['src']).exists(), f'Missing image {img["src"]}'
    lessons = sum(len(c['lessons']) for c in chapters)
    print(f'Built manual: {len(chapters)} chapters, {lessons} lessons, {len(v.images)} images, {len(v.links)} links OK.')


if __name__ == '__main__':
    main()
