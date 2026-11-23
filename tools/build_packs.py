#!/usr/bin/env python3
"""Writes the INK Preset Packs pages from PACKS below: ink/packs/index.html lists the packs, and each released pack gets its
listening page at ink/packs/<slug>/index.html. Styles: ink/packs/packs.css.

A released pack: its .inksounds file in ink/packs/files/, one AAC preview per sound in ink/packs/audio/<pack>/<sound>.m4a
(a phrase rendered by INK's own engine: RM INK's `ink_render <library> <out> --pack <file> --scenes phrase --all`),
and the waveforms drawn here from those previews (ffmpeg decodes them). A pack with 'soon' is listed, not linked.

A pack with a 'roster' (Arp Magic) takes its line, each sound's name, family and line, and the credits from tools/packs/<slug>.json,
and `prepare` writes its files from the pack INK's tools made and the demo takes:
  files/<slug>.zip              the pack in the roster's order, its manifest naming the pack and its author (the folder and credit INK shows)
  audio/<slug>/<sound>.m4a      the demo, AAC at 112 kb/s from the take each sound's row names in --clips (<sound>.wav, or <n>-<sound>-take.wav)
It refuses a pack whose sounds and the roster's differ, and one with a recording no credit in the roster covers. The pack downloads
whole only: one sound's own file would carry its whole kit, and the 34 of them came to 341 MB against the pack's 61 (owner, 23 November 2026).
Usage: python3 tools/build_packs.py                                                     the pages
       python3 tools/build_packs.py prepare <slug> <pack.inksounds> [--clips <folder>]  a roster pack's files, then the pages"""
from html import escape
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKS_DIR = ROOT / 'ink' / 'packs'
TESTFLIGHT = 'https://testflight.apple.com/join/mCCTYCpR'

PACKS = [
    {
        'slug': 'pluck-studies',
        'name': 'Pluck Studies',
        # The .inksounds stored as .zip: GitHub Pages gzips unknown types, and Safari saved that download cut short. The page's
        # Download (DOWNLOAD below) fetches it and saves it as save_as, since Safari unzips a .zip into a folder (27 Oct 2026).
        'file': 'pluck-studies.zip',
        'save_as': 'Pluck Studies.inksounds',
        'line': 'Eight granular plucks for the Strings keyboard, on recorded zither, mbira, balafon, psaltery and chime.',
        'credits': 'Recordings from the Versilian Community Sample Library (VCSL) by Versilian Studios, CC0 1.0. '
                   'Prism Drive and Elastic Circuit use original synthesized sources.',
        'sounds': [
            ('silk-bridge', 'Silk Bridge'),
            ('rattle-tines', 'Rattle Tines'),
            ('gourd-flick', 'Gourd Flick'),
            ('ghost-psaltery', 'Ghost Psaltery'),
            ('prism-drive', 'Prism Drive'),
            ('elastic-circuit', 'Elastic Circuit'),
            ('clay-knock', 'Clay Knock'),
            ('chime-stitch', 'Chime Stitch'),
        ],
    },
    {
        'slug': 'arp-magic',
        'name': 'Arp Magic',
        'author': 'Random Machines',
        'file': 'arp-magic.zip',
        'save_as': 'Arp Magic.inksounds',
        'price': 'Free while the INK Synth beta is open',
        # Free while the beta opens, every sound with its demo, the pack's size shown (owner, 23 November 2026). Line, families,
        # sounds and credits: the roster. Files: `prepare` (see the top).
        'roster': 'tools/packs/arp-magic.json',
    },
    {
        'slug': 'dub-echoes',
        'name': 'Dub Echoes',
        'soon': True,
        # A free demo before the pack: 14 of its sounds (6 keys, 3 pads, 2 basses, 2 leads, 1 FX; levelled by loudness.py), downloaded from the list
        # row with the same checked fetch-and-save as a released pack (12 November 2026).
        'demo': {'file': 'dub-echoes-demo.zip', 'save_as': 'Dub Echoes Demo.inksounds'},
    },
]

BARS = 64


def load_roster(p):
    """A roster pack takes its line, sounds and credits from its JSON (see the top)."""
    r = json.loads((ROOT / p['roster']).read_text())
    p.update(line=r['line'], more=r.get('more', ''), draft=r.get('draft'), groups=r['groups'], credits=r['credits'], rows=r['sounds'])
    p['sounds'] = [(row['slug'], row['name']) for row in r['sounds']]
    p['scores'] = json.loads((ROOT / r['scores']).read_text())['scores'] if r.get('scores') else {}


for _p in PACKS:
    if _p.get('roster'):
        load_roster(_p)


def missing_files(p):
    """What a released pack's page needs and does not have yet (a roster pack before `prepare`)."""
    need = [PACKS_DIR / 'files' / p['file']] + [audio_of(p, slug) for slug, _ in p['sounds']]
    return [f for f in need if not f.exists()]


def peaks(audio: Path):
    """BARS heights in 0..1: each slice's peak against the loudest, eased so the tails still show."""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(audio), '-ac', '1', '-ar', '8000', '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    x = [abs(v) for (v,) in struct.iter_unpack('<f', raw)]
    n = len(x)
    p = [max(x[n * i // BARS:n * (i + 1) // BARS] or [0]) for i in range(BARS)]
    top = max(p) or 1
    return [(v / top) ** 0.7 for v in p]


def wave(heights):
    """One path of rounded bars in a 256 x 40 box, centred on the middle line."""
    d = []
    for i, h in enumerate(heights):
        half = max(0.4, h * 19)
        d.append(f'M{i * 4 + 1.5:g} {20 - half:.1f}V{20 + half:.1f}')
    return ''.join(d)


def audio_of(pack, sound):
    return PACKS_DIR / 'audio' / pack['slug'] / f'{sound}.m4a'


def size(path: Path):
    n = path.stat().st_size
    return f'{n / 1e6:.1f} MB' if n >= 95_000 else f'{max(1, round(n / 1e3))} KB'


def shell(*, title, description, canonical, up, body, script='', draft=False):
    """The page around `body`; `up` is the path back to the site root. A draft page asks search engines to leave it out."""
    robots = '\n  <meta name="robots" content="noindex">' if draft else ''
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">{robots}
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <meta name="theme-color" content="#f1ede4">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Random Machines">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:url" content="https://randommachines.app/{canonical}">
  <link rel="canonical" href="https://randommachines.app/{canonical}">
  <link rel="icon" href="{up}rmxy-1/assets/favicon.ico">
  <link rel="apple-touch-icon" href="{up}rmxy-1/assets/apple-touch-icon.png">
  <link rel="preload" href="{up}rmxy-1/assets/fonts/space-grotesk.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{up}rmxy-1/assets/site.css">
  <link rel="stylesheet" href="{up}ink/manual/assets/fonts.css">
  <link rel="stylesheet" href="{up}ink/packs/packs.css">
</head>
<body class="ink-page">
  <a class="skip" href="#main">Skip to content</a>
  <header class="nav">
    <div class="nav__inner">
      <a class="nav__brand" href="{up}" aria-label="Random Machines home">
        <img class="nav__logo nav__logo--full" src="{up}ink/packs/assets/rm-lockup-stacked-on-light.svg" alt="" width="157" height="40">
        <img class="nav__logo nav__logo--symbol" src="{up}ink/packs/assets/rm-symbol-on-light.svg" alt="" width="40" height="40">
      </a>
      <nav class="nav__links" aria-label="Main"><a href="{up}#ink">INK Synth</a><a href="{up}ink/packs/" aria-current="page">Preset Packs</a><a href="{up}ink/manual/">Manual</a></nav>
    </div>
  </header>

  <main id="main" class="packs">
{body}
  </main>

  <footer class="footer">
    <div class="footer__inner">
      <a class="footer__brand" href="{up}" aria-label="Random Machines home">
        <img src="{up}ink/packs/assets/rm-lockup-stacked-on-light.svg" alt="" width="204" height="52" loading="lazy">
      </a>
      <ul class="footer__links">
        <li><a href="{TESTFLIGHT}" rel="noopener">INK Synth beta</a></li>
        <li><a href="{up}ink/manual/">INK Synth manual</a></li>
        <li><a href="{up}rmxy-1/">RMXY-1</a></li>
        <li><a href="mailto:wideknotlabs@gmail.com">Contact</a></li>
      </ul>
    </div>
    <div class="footer__legal">
      <p>© 2026 Random Machines. INK Synth is published by Borja Deudero Gracia.</p>
      <p>iPhone and iPad are trademarks of Apple Inc., registered in the U.S. and other countries.</p>
    </div>
  </footer>
{script}</body>
</html>
'''


def get_button(item, label, up='', price='Free'):
    """The Download button for a pack file (item: 'file', 'save_as') and the line beside it, which DOWNLOAD uses."""
    file = PACKS_DIR / 'files' / item['file']
    return (f'<a class="ink-btn ink-btn--fill pack__get" href="{up}files/{item["file"]}" download="{escape(item["save_as"])}" '
            f'data-bytes="{file.stat().st_size}" data-sha256="{hashlib.sha256(file.read_bytes()).hexdigest()}">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 10.5l5 5 5-5M5 20h14"/></svg>'
            f'{escape(label)}</a>\n        <span class="pack__file" role="status">{size(file)} · {escape(price)}</span>')


def list_page():
    rows = []
    for n, p in enumerate(PACKS, 1):
        if p.get('soon'):
            demo = ''
            if p.get('demo'):
                demo = '\n          <div class="entry__demo">' + get_button(p['demo'], 'Download demo') + '</div>'
            rows.append(f'''
        <li class="entry entry--soon{' entry--demo' if demo else ''}">
          <span class="entry__no">{n:02d}</span>
          <div class="entry__text"><h2>{escape(p['name'])}</h2><p class="entry__meta">Coming soon</p></div>{demo}
        </li>''')
            continue
        if missing_files(p):
            print(f"{p['slug']}: left off the list, its files are not here yet (build_packs.py prepare)")
            continue
        strip = wave(peaks(audio_of(p, p['sounds'][0][0])))
        rows.append(f'''
        <li class="entry">
          <a href="{p['slug']}/">
            <span class="entry__no">{n:02d}</span>
            <div class="entry__text"><h2>{escape(p['name'])}</h2>{'<p class="entry__meta">Draft</p>' if p.get('draft') else ''}<p class="entry__line">{escape(p['line'])}</p></div>
            <svg class="entry__wave" viewBox="0 0 256 40" preserveAspectRatio="none" aria-hidden="true"><path d="{strip}"/></svg>
            <span class="ink-btn">Listen<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6"/></svg></span>
          </a>
        </li>''')
    body = f'''    <div class="packs__in">
      <p class="kick">INK Synth</p>
      <h1 class="packs__title">Preset Packs</h1>
      <p class="packs__lede">Sound packs for INK Synth. Listen to every sound, then download the pack.</p>
      <ol class="entries">{''.join(rows)}
      </ol>
    </div>'''
    return shell(title='Preset Packs — INK Synth | Random Machines',
                 description='Sound packs for INK Synth, the three-engine touch synthesizer for iPhone and iPad. '
                             'Listen to every sound, then download the .inksounds file.',
                 canonical='ink/packs/', up='../../', body=body,
                 script=DOWNLOAD if any(p.get('demo') for p in PACKS) else '')


def pack_page(p):
    if p.get('roster'):
        return roster_page(p)
    rows = []
    for slug, name in p['sounds']:
        path = wave(peaks(audio_of(p, slug)))
        rows.append(f'''
        <li class="snd" data-src="../audio/{p['slug']}/{slug}.m4a">
          <button class="snd__play" type="button" aria-label="Play {escape(name)}"><svg viewBox="0 0 24 24" aria-hidden="true"><path class="i-play" d="M8 5.5v13l11-6.5z"/><path class="i-stop" d="M7 7h10v10H7z"/></svg></button>
          <div class="snd__text"><h3>{escape(name)}</h3></div>
          <div class="snd__wave" aria-hidden="true">
            <svg viewBox="0 0 256 40" preserveAspectRatio="none"><path d="{path}"/></svg>
            <svg class="snd__on" viewBox="0 0 256 40" preserveAspectRatio="none"><path d="{path}"/></svg>
          </div>
        </li>''')
    body = f'''    <div class="packs__in">
      <a class="crumb" href="../"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H6M11 6l-6 6 6 6"/></svg>Preset Packs</a>
      <h1 class="packs__title">{escape(p['name'])}</h1>
      <p class="packs__lede">{escape(p['line'])}</p>
      <div class="pack__actions">
        {get_button(p, 'Download', up='../')}
      </div>
      <p class="pack__how">In INK Synth, tap Import in the Library and choose the file, or open it in INK from Files or AirDrop. <a href="../../manual/save-and-share-sounds.html">Save and share sounds</a></p>
      <ol class="sounds" aria-label="Sounds">{''.join(rows)}
      </ol>
      <p class="pack__credits">{escape(p['credits'])}</p>
    </div>'''
    return shell(title=f"{p['name']} — INK Synth Preset Packs | Random Machines",
                 description=f"{p['name']}: {p['line']}",
                 canonical=f"ink/packs/{p['slug']}/", up='../../../', body=body, script=PLAYER + DOWNLOAD)


def roster_page(p):
    """A roster pack: each row plays its demo and says what the sound is; the family buttons show one family."""
    count = {g['id']: sum(row['group'] == g['id'] for row in p['rows']) for g in p['groups']}
    fams = ''.join(f'<button type="button" aria-pressed="false" data-group="{g["id"]}">{escape(g["name"])} <span>{count[g["id"]]}</span></button>'
                   for g in p['groups'] if count[g['id']])
    rows = []
    for row in p['rows']:
        slug, name = row['slug'], row['name']
        path = wave(peaks(audio_of(p, slug)))
        rows.append(f'''
        <li class="snd snd--line" data-src="../audio/{p['slug']}/{slug}.m4a" data-group="{row['group']}" data-slug="{slug}">
          <button class="snd__play" type="button" aria-label="Play {escape(name)}"><svg viewBox="0 0 24 24" aria-hidden="true"><path class="i-play" d="M8 5.5v13l11-6.5z"/><path class="i-stop" d="M7 7h10v10H7z"/></svg></button>
          <div class="snd__text"><h3>{escape(name)}</h3><p>{escape(row['line'])}</p></div>
          <div class="snd__wave" aria-hidden="true">
            <svg viewBox="0 0 256 40" preserveAspectRatio="none"><path d="{path}"/></svg>
            <svg class="snd__on" viewBox="0 0 256 40" preserveAspectRatio="none"><path d="{path}"/></svg>
          </div>{score_panel(p['scores'].get(slug))}
        </li>''')
    c = p['credits']
    credits = f'''
      <section class="pack__credits credits" aria-labelledby="credits">
        <h2 id="credits">Credits</h2>
        <p>{escape(p['name'])} by {escape(p['author'])}.</p>
        <h3>Recordings under Creative Commons Attribution</h3>
        <ul>{''.join(f"<li>{escape(x['line'])}</li>" for x in c['required'])}</ul>
        <p>{escape(c['changes'])}</p>
        <h3>Also from, with thanks (CC0 and public domain)</h3>
        <ul>{''.join(f"<li>{escape(x['line'])}</li>" for x in c['courtesy'])}</ul>
      </section>'''
    draft = f'\n      <p class="draft">{escape(p["draft"])}</p>' if p.get('draft') else ''
    lede = p['line'] + (' ' + p['more'] if p.get('more') else '')
    body = f'''    <div class="packs__in">{draft}
      <a class="crumb" href="../"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H6M11 6l-6 6 6 6"/></svg>Preset Packs</a>
      <h1 class="packs__title">{escape(p['name'])}</h1>
      <p class="packs__lede">{escape(lede)}</p>
      <div class="pack__actions">
        {get_button(p, 'Download', up='../', price=p.get('price', 'Free'))}
      </div>
      <p class="pack__how">In INK Synth, tap Import in the Library and choose the file, or open it in INK from Files or AirDrop. <a href="../../manual/save-and-share-sounds.html">Save and share sounds</a></p>
      <div class="fams" role="group" aria-label="Show" hidden><button type="button" aria-pressed="true" data-group="">All <span>{len(p['rows'])}</span></button>{fams}</div>
      {'<p class="pack__hint">Play a sound to see it on INK: the chord pad held in each bar, and every note the arp plays from it. Then tap a chord to keep the arp on it.</p>' if p['scores'] else ''}
      <ol class="sounds" aria-label="Sounds">{''.join(rows)}
      </ol>{credits}
    </div>'''
    scores = ''
    if p['scores']:
        blob = json.dumps({row['slug']: p['scores'][row['slug']] for row in p['rows'] if row['slug'] in p['scores']}, separators=(',', ':'))
        blob = blob.replace('</', '<\\/')
        scores = f'  <script type="application/json" id="scores">{blob}</script>\n' + KEYS
    return shell(title=f"{p['name']} — INK Synth Preset Packs | Random Machines",
                 description=f"{p['name']}: {p['line']}",
                 canonical=f"ink/packs/{p['slug']}/", up='../../../', body=body, script=PLAYER + FAMILIES + scores + DOWNLOAD,
                 draft=bool(p.get('draft')))


def score_panel(sc):
    """Under a row with a score, opened by Play: its 8 chords as INK's chord pads (one a bar, with the scale degree as the app
    numbers its columns), the arp's shape for the bar (KEYS draws it and plays the pads), and the arp in words."""
    if not sc:
        return ''
    kb = sc['kb']
    name = lambda n: escape(n).replace('add', '<wbr>add').replace('+maj', '+<wbr>maj').replace('/', '<wbr>/')   # a long name breaks only there
    pads = ''.join(f'<button class="ink__pad" type="button" aria-pressed="false" aria-label="Bar {b + 1}: {escape(c)}">'
                   f'<span class="ink__num">{escape(kb["numerals"][at[0]]) if at else "&nbsp;"}</span><span class="ink__name">{name(c)}</span></button>'
                   for b, ((c, _), at) in enumerate(zip(sc['chords'], kb['press'])))
    moves = ', '.join(m['what'] for m in sc['moves'])
    moving = f' <span class="ink__moves">Moving bar by bar: {escape(moves)}</span>' if moves else ''
    return f'''
          <div class="ink" hidden>
            <div class="ink__kb">
              <p class="ink__key"><span>{escape(kb['key'])}</span><span class="ink__tip">Tap a chord to hold it</span></p>
              <div class="ink__pads" role="group" aria-label="Chords">{pads}</div>
            </div>
            <div class="ink__arp"><canvas aria-hidden="true"></canvas><span class="ink__say"></span></div>
            <p class="ink__words"><span class="ink__mode">{escape(sc['arp'])}</span>{moving}</p>
          </div>'''


FAMILIES = '''  <script>
  // The family buttons show one family's sounds or all of them; the order stays the pack's. Without JavaScript every sound shows.
  (() => {
    const bar = document.querySelector('.fams');
    if (!bar) return;
    const rows = document.querySelectorAll('.snd[data-group]');
    bar.hidden = false;
    bar.addEventListener('click', e => {
      const b = e.target.closest('button');
      if (!b) return;
      bar.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
      rows.forEach(r => {
        r.hidden = !!b.dataset.group && r.dataset.group !== b.dataset.group;
        if (r.hidden && r.classList.contains('is-playing')) r.querySelector('.snd__play').click();
      });
    });
  })();
  </script>
'''


PLAYER = '''  <script>
  // One preview at a time: a row's button or waveform plays it, the lit part of the waveform follows the playhead.
  // A row KEYS plays (data-keys) is left to it; 'snd:solo' keeps one sound at a time between the two.
  (() => {
    const audio = new Audio();
    let row = null, frame = 0;
    const label = (r, verb) => r.querySelector('.snd__play').setAttribute('aria-label', verb + ' ' + r.querySelector('h3').textContent);
    const draw = () => {
      if (row && audio.duration) row.style.setProperty('--p', (100 * audio.currentTime / audio.duration).toFixed(2) + '%');
      frame = requestAnimationFrame(draw);
    };
    const stop = () => {
      cancelAnimationFrame(frame);
      if (row) { row.classList.remove('is-playing'); row.style.setProperty('--p', '0%'); label(row, 'Play'); }
      row = null;
    };
    const play = r => {
      if (r !== row) { audio.pause(); stop(); row = r; audio.src = r.dataset.src; }
      document.dispatchEvent(new CustomEvent('snd:solo', { detail: r }));
      audio.play().then(() => { r.classList.add('is-playing'); label(r, 'Stop'); cancelAnimationFrame(frame); draw(); }).catch(stop);
    };
    audio.addEventListener('ended', stop);
    document.addEventListener('snd:solo', e => { if (row && e.detail !== row) { audio.pause(); stop(); } });
    document.querySelectorAll('.snd').forEach(r => {
      r.querySelector('.snd__play').addEventListener('click', () => {
        if (r.dataset.keys) return;
        if (r === row && !audio.paused) { audio.pause(); stop(); } else play(r);
      });
      r.querySelector('.snd__wave').addEventListener('click', e => {
        if (r.dataset.keys) return;
        const box = e.currentTarget.getBoundingClientRect();
        const at = Math.min(Math.max((e.clientX - box.left) / box.width, 0), 1);
        if (r === row && audio.duration) { audio.currentTime = at * audio.duration; if (audio.paused) play(r); return; }
        play(r);
        audio.addEventListener('loadedmetadata', () => { audio.currentTime = at * audio.duration; }, { once: true });
      });
    });
  })();
  </script>
'''

KEYS = r'''  <script>
  // INK at work (a roster pack's page). Each take is 8 bars, one chord a bar, so its row plays it as INK's chord pads: 8 pads, a
  // bar's chord on each. Play runs the take round and round, the pad of each bar going down as its bar plays. Tap a pad and the
  // arp keeps playing that chord: the page loops that bar of the same recording (Web Audio, cut on the beat), so one file plays
  // every pad. Tap it again, or Stop, to stop. Beside the pads, the bar's arp as INK's Arp tab draws it, larger: a dot for each
  // note with its gate as a tail, an octave pass hollow and marked +1, the notes played in ink and the rest of the bar faint, a
  // line where the sound is. The panel opens with Play and stays open, so the pads can be played after the take stops.
  // Rows it plays carry data-keys, and PLAYER leaves them alone; 'snd:solo' keeps one sound at a time between the two.
  (() => {
    const el = document.getElementById('scores'), AC = window.AudioContext || window.webkitAudioContext;
    if (!el || !AC || !window.HTMLCanvasElement) return;
    const scores = JSON.parse(el.textContent);
    const css = getComputedStyle(document.body), tok = k => css.getPropertyValue(k).trim();
    const INK = tok('--ink') || '#161513', PENCIL = tok('--pencil') || '#6e6a62';
    const HAND = "'Gaegu', 'Comic Sans MS', 'Chalkboard SE', cursive";
    const still = matchMedia('(prefers-reduced-motion: reduce)');
    const AHEAD = 1.5;                         // seconds scheduled ahead (a hidden tab wakes its timers once a second)
    let ac = null, live = null, run = null, timer = 0, frame = 0;
    const bufs = new Map();

    const prepare = s => {
      if (s.barS) return s;
      const ps = s.notes.map(n => n[1]);
      s.lo = Math.min(...ps) - 1; s.hi = Math.max(...ps) + 1; s.barS = 60 / s.bpm * s.bar; s.L = s.barS * s.bars;
      const say = { Notes: v => v + ' notes', Range: v => 'Range ' + v, Gate: v => 'Gate ' + v };
      s.pages = Array.from({ length: s.bars }, (_, b) => {
        const a = b * s.barS, notes = s.notes.filter(n => n[0] >= a - 0.02 && n[0] < a + s.barS - 0.02);
        const base = {};                       // each pitch class's lowest place this bar: higher ones are octave passes
        for (const n of notes) base[n[1] % 12] = Math.min(base[n[1] % 12] ?? 1e9, n[1]);
        const gaps = notes.slice(1).map((n, i) => n[0] - notes[i][0]).filter(g => g > 0.02).sort((x, y) => x - y);
        const step = gaps.length ? gaps[Math.floor(gaps.length / 2)] : s.barS / 4;
        const label = s.moves.map(m => (say[m.what] || (v => v))(m.bars[b])).filter(Boolean).join(' · ');
        return { a, step, label, notes: notes.map(n => ({ t: n[0], p: n[1], d: n[2], up: Math.round((n[1] - base[n[1] % 12]) / 12) })) };
      });
      return s;
    };

    // The bar's arp; now is the time in the take (the notes before it are in ink), head draws the line at now.
    const draw = (v, b, now, head) => {
      const { canvas, ctx, s } = v, pg = s.pages[b];
      const dpr = window.devicePixelRatio || 1, W = canvas.clientWidth, H = canvas.clientHeight;
      if (!W || !H) return;
      if (canvas.width !== Math.round(W * dpr) || canvas.height !== Math.round(H * dpr)) { canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr); }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
      const left = 12, right = W - 14, top = pg.label ? 30 : 16, bottom = H - 12, r = W < 420 ? 3.2 : 3.8;
      const X = t => left + (t - pg.a) / s.barS * (right - left), Y = p => bottom - (p - s.lo) / (s.hi - s.lo) * (bottom - top);
      ctx.strokeStyle = PENCIL; ctx.globalAlpha = 0.35; ctx.lineWidth = 1;          // the beats, as ticks along the foot
      for (let k = 0; k <= s.bar; k++) { const x = Math.round(X(pg.a + k * s.barS / s.bar)) + 0.5; ctx.beginPath(); ctx.moveTo(x, H - 6); ctx.lineTo(x, H - (k % s.bar ? 9 : 13)); ctx.stroke(); }
      const rings = [];
      pg.notes.forEach(n => {
        const x = X(n.t), y = Y(n.p), x2 = Math.max(x + r + 4, X(n.t + Math.min(n.d, pg.step * 0.85)));
        ctx.globalAlpha = n.t <= now ? 1 : 0.2; ctx.strokeStyle = INK; ctx.fillStyle = INK; ctx.lineWidth = 1.7; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(x + r, y); ctx.lineTo(x2, y); ctx.stroke();
        ctx.beginPath(); ctx.arc(x, y, r, 0, 2 * Math.PI);
        if (n.up) {
          ctx.lineWidth = 1.5; ctx.stroke();
          ctx.font = `${W < 420 ? 12 : 13}px ${HAND}`; ctx.fillText((n.up > 0 ? '+' : '') + n.up, x + r, y - r - 2);
        } else ctx.fill();
        if (head && !still.matches && now - n.t >= 0 && now - n.t < 0.3) rings.push([x, y, (now - n.t) / 0.3]);
      });
      ctx.strokeStyle = INK; ctx.lineWidth = 1.4;
      for (const [x, y, k] of rings) { ctx.globalAlpha = 0.65 * (1 - k); ctx.beginPath(); ctx.arc(x, y, r + 2 + 10 * k, 0, 2 * Math.PI); ctx.stroke(); }
      ctx.globalAlpha = 1; ctx.lineWidth = 1.8;
      if (head) { const x = Math.round(X(now)) + 0.5; ctx.beginPath(); ctx.moveTo(x, 6); ctx.lineTo(x, H - 6); ctx.stroke(); }
      if (b !== v.bar) { v.bar = b; v.say.textContent = pg.label; }
    };
    const down = (v, b) => { if (v.down !== b) { v.down = b; v.pads.forEach((p, i) => p.classList.toggle('is-down', i === b)); } };
    const rest = () => { if (!live) return; down(live, -1); const b = live.bar < 0 ? 0 : live.bar; draw(live, b, live.s.pages[b].a + live.s.barS, false); };

    const open = row => {
      if (live && live.row === row) return live;
      if (live) live.panel.hidden = true;
      const panel = row.querySelector('.ink'), canvas = panel.querySelector('canvas');
      panel.hidden = false;
      live = { row, panel, canvas, ctx: canvas.getContext('2d'), s: prepare(scores[row.dataset.slug]), say: panel.querySelector('.ink__say'),
               pads: [...panel.querySelectorAll('.ink__pad')], bar: -1, down: -1 };
      rest();
      return live;
    };

    const wake = () => {                        // in the tap itself, or iOS keeps the sound off
      if (!ac) {
        try { if (navigator.audioSession) navigator.audioSession.type = 'playback'; } catch (e) {}   // play with the ring switch on silent
        ac = new AC();
      }
      if (ac.state !== 'running') ac.resume();
    };
    const load = row => {
      const slug = row.dataset.slug;
      if (!bufs.has(slug)) {
        bufs.set(slug, fetch(row.dataset.src).then(r => { if (!r.ok) throw new Error('audio'); return r.arrayBuffer(); })
          .then(b => new Promise((ok, no) => ac.decodeAudioData(b, ok, no))));
        bufs.get(slug).catch(() => bufs.delete(slug));
        while (bufs.size > 3) bufs.delete(bufs.keys().next().value);
      }
      return bufs.get(slug);
    };

    // One recording, cut on the bar: Play is the whole take from its start (each pass rings on into the next, as a held loop
    // would); a pad is its bar, start to end, again and again, with a few milliseconds of fade at each cut.
    const voice = (when, from, len) => {
      const src = ac.createBufferSource(), g = ac.createGain();
      src.buffer = run.buf; src.connect(g); g.connect(run.out);
      if (from > 0) { g.gain.setValueAtTime(0, when); g.gain.linearRampToValueAtTime(1, when + 0.003); }
      if (len) { g.gain.setValueAtTime(1, when + len - 0.008); g.gain.linearRampToValueAtTime(0, when + len); src.start(when, from, len); }
      else src.start(when, from);
      run.srcs.push({ src, end: when + (len || run.buf.duration - from) });
    };
    const pump = () => {
      if (!run || !run.buf) return;
      const s = run.s, until = ac.currentTime + AHEAD;
      for (;;) {
        const when = run.t0 + run.k * (run.pad < 0 ? s.L : s.barS);
        if (when >= until) break;
        if (run.pad < 0) voice(Math.max(when, run.start), Math.max(0, run.start - when), 0);
        else voice(when, run.pad * s.barS, s.barS);
        run.k++;
      }
      run.srcs = run.srcs.filter(x => x.end > ac.currentTime);
    };
    const hush = () => {                         // fade what sounds and let it go
      if (!run) return;
      const r = run; run = null; clearInterval(timer);
      if (r.out) {
        const t = ac.currentTime;
        r.out.gain.setValueAtTime(1, t); r.out.gain.linearRampToValueAtTime(0, t + 0.02);
        r.srcs.forEach(x => { try { x.src.stop(t + 0.03); } catch (e) {} });
      }
      return r;
    };
    const label = (row, verb) => row.querySelector('.snd__play').setAttribute('aria-label', verb + ' ' + row.querySelector('h3').textContent);
    const quiet = row => {
      row.classList.remove('is-playing', 'is-loading'); row.style.setProperty('--p', '0%'); label(row, 'Play');
      if (live && live.row === row) live.pads.forEach(p => p.setAttribute('aria-pressed', 'false'));
    };
    const halt = () => { const r = hush(); cancelAnimationFrame(frame); if (r) quiet(r.row); rest(); };

    // pad -1: the whole take from at seconds in; otherwise that pad's bar, looped.
    const begin = async (row, pad, at) => {
      wake();
      const r0 = hush();
      if (r0 && r0.row !== row) quiet(r0.row);
      document.dispatchEvent(new CustomEvent('snd:solo', { detail: row }));
      const v = open(row);
      const me = run = { row, s: v.s, pad, at, srcs: [], k: 0 };
      v.pads.forEach((p, i) => p.setAttribute('aria-pressed', String(i === pad)));
      row.classList.add('is-playing'); label(row, 'Stop');
      if (!bufs.has(row.dataset.slug)) row.classList.add('is-loading');
      let buf;
      try { buf = await load(row); } catch (e) { if (run === me) halt(); return; }
      if (run !== me) return;
      row.classList.remove('is-loading');
      me.buf = buf; me.out = ac.createGain(); me.out.connect(ac.destination);
      const t = ac.currentTime + 0.04;
      if (pad < 0) { me.t0 = t - at; me.start = t; } else me.t0 = t;
      pump(); clearInterval(timer); timer = setInterval(pump, 250);
      cancelAnimationFrame(frame); frame = requestAnimationFrame(tick);
    };
    const tick = () => {
      if (!run || !run.buf || !live) return;
      const s = run.s, t = ac.currentTime - (ac.outputLatency || ac.baseLatency || 0);
      let now, b;
      if (run.pad < 0) { now = ((t - run.t0) % s.L + s.L) % s.L; b = Math.min(s.bars - 1, Math.floor(now / s.barS)); }
      else { b = run.pad; now = b * s.barS + Math.max(0, t - run.t0) % s.barS; }
      draw(live, b, now, true); down(live, b);
      run.row.style.setProperty('--p', (100 * now / run.buf.duration).toFixed(2) + '%');
      frame = requestAnimationFrame(tick);
    };

    document.addEventListener('snd:solo', e => { if (run && run.row !== e.detail) halt(); });
    document.querySelectorAll('.snd[data-slug]').forEach(row => {
      if (!scores[row.dataset.slug] || !row.querySelector('.ink')) return;
      row.dataset.keys = '1';
      row.querySelector('.snd__play').addEventListener('click', () => { if (run && run.row === row) halt(); else begin(row, -1, 0); });
      row.querySelector('.snd__wave').addEventListener('click', e => {
        const box = e.currentTarget.getBoundingClientRect(), s = prepare(scores[row.dataset.slug]);
        begin(row, -1, Math.min(Math.max((e.clientX - box.left) / box.width, 0), 0.999) * s.L);
      });
      row.querySelectorAll('.ink__pad').forEach((p, i) => p.addEventListener('click', () => {
        if (run && run.row === row && run.pad === i) halt(); else begin(row, i, 0);
      }));
    });
    addEventListener('resize', () => { if (!run) rest(); });
  })();
  </script>
'''


DOWNLOAD = '''  <script>
  // Download saves one .inksounds file (a pack's page, or a demo on the list). The pack is stored as .zip (see PACKS), and Safari would
  // unzip a .zip it downloads into a folder INK cannot import, so the page fetches the bytes, checks them against the pack's size and
  // SHA-256, and saves them under the .inksounds name. A download cut short is not saved; the line beside the button says so. A big
  // pack counts its progress there.
  (() => {
    if (!window.fetch || !window.crypto || !crypto.subtle) return;
    document.querySelectorAll('.pack__get').forEach(get => {
      const note = get.parentElement.querySelector('.pack__file'), said = note.textContent, want = +get.dataset.bytes;
      let busy = false;
      const read = async reply => {
        if (!reply.body || !reply.body.getReader) return reply.arrayBuffer();
        const reader = reply.body.getReader(), parts = [];
        let got = 0;
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          parts.push(value); got += value.length;
          if (want > 4e6) note.textContent = 'Downloading… ' + Math.min(99, Math.floor(100 * got / want)) + '%';
        }
        const all = new Uint8Array(got);
        let at = 0;
        for (const part of parts) { all.set(part, at); at += part.length; }
        return all.buffer;
      };
      get.addEventListener('click', async e => {
        e.preventDefault();
        if (busy) return;
        busy = true; note.textContent = 'Downloading…';
        try {
          const reply = await fetch(get.href, { cache: 'no-store' });
          if (!reply.ok) throw new Error('reply');
          const bytes = await read(reply);
          const sum = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('');
          if (bytes.byteLength !== want || sum !== get.dataset.sha256) throw new Error('bytes');
          const url = URL.createObjectURL(new Blob([bytes], { type: 'application/octet-stream' }));
          const a = document.createElement('a');
          a.href = url; a.download = get.getAttribute('download'); a.style.display = 'none';
          document.body.append(a); a.click(); a.remove();
          setTimeout(() => URL.revokeObjectURL(url), 60000);
          note.textContent = said;
        } catch (err) {
          note.textContent = 'The download did not finish. Try again.';
        }
        busy = false;
      });
    });
  })();
  </script>
'''


def prepare(slug, source: Path, clips: Path = None):
    """A roster pack's files from the pack INK's tools made (see the top). The pack is written the same way each time (fixed
    order, dates and compression), so the same sounds give the same bytes and SHA-256."""
    p = next((x for x in PACKS if x['slug'] == slug and x.get('roster')), None)
    if not p:
        sys.exit(f'{slug}: no pack with a roster')
    z = zipfile.ZipFile(source)
    names = set(z.namelist())
    manifest = json.loads(z.read('manifest.json'))
    if manifest.get('format') != 'rm-ink-sounds' or manifest.get('kind') == 'project':
        sys.exit(f'{source}: not an INK sounds file')
    coll = json.loads(z.read('sounds.json'))
    kits_doc = json.loads(z.read('kits.json')) if 'kits.json' in names else {'format': 'rm-ink-sounds-kits', 'version': 1, 'kits': []}
    kits = {k['key']: k for k in kits_doc['kits']}
    by_name = {}
    for snd in coll['presets']:
        if snd['name'].casefold() in by_name:
            sys.exit(f"{source}: two sounds are called {snd['name']}")
        by_name[snd['name'].casefold()] = snd
    want = {row['name'].casefold() for row in p['rows']}
    missing = [row['name'] for row in p['rows'] if row['name'].casefold() not in by_name]
    extra = [snd['name'] for snd in coll['presets'] if snd['name'].casefold() not in want]
    if missing or extra:
        sys.exit(f"{source} and {p['roster']} differ.\n  Not in the pack: {', '.join(missing) or '-'}\n  Not in the roster: {', '.join(extra) or '-'}")

    def carries(snd):
        """The kits and entries a sound needs: its kit (when the file has it: a factory kit is every INK's) with all its
        recordings, and its own wavetable (a factory one is every INK's)."""
        kit = kits.get(snd.get('kit'))
        entries = []
        for slot in (kit or {}).get('slots', []):
            if slot.get('recording'):
                entries += [f"recordings/{slot['recording']}.flac", f"recordings/{slot['recording']}.json"]
        wt = snd.get('wavetable')
        if isinstance(wt, str) and f'wavetables/{wt}.s16' in names:
            entries += [f'wavetables/{wt}.s16', f'wavetables/{wt}.json']
        gone = [e for e in entries if e not in names]
        if gone:
            sys.exit(f"{source}: {snd['name']} needs {', '.join(gone)}, which the file does not have")
        return [kit] if kit else [], entries

    # Every recording the pack carries is credited (CC BY ones must be; the others are thanked).
    credited = {r for group in ('required', 'courtesy') for c in p['credits'][group] for r in c['recordings']}
    recordings = sorted({e for snd in coll['presets'] for e in carries(snd)[1] if e.startswith('recordings/') and e.endswith('.json')})
    uncredited = sorted({json.loads(z.read(e))['name'] for e in recordings} - credited)
    if uncredited:
        sys.exit(f"{source}: no credit in {p['roster']} for: {'; '.join(uncredited)}")

    m = re.match(r'(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)', manifest.get('created', ''))
    stamp = tuple(int(x) for x in m.groups()) if m else (2026, 1, 1, 0, 0, 0)
    head = dict(manifest, name=p['name'], author=p['author'])   # the folder INK files the sounds in, and the pack's credit

    def write(path: Path, sounds):
        used, entries = [], set()
        for snd in sounds:
            k, e = carries(snd)
            used += [x for x in k if x not in used]
            entries |= set(e)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix('.part')
        with zipfile.ZipFile(tmp, 'w') as out:
            def put(name, data):
                info = zipfile.ZipInfo(name, stamp)
                info.compress_type = zipfile.ZIP_STORED if name.endswith('.flac') else zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                out.writestr(info, data)
            put('manifest.json', json.dumps(head, indent=2, ensure_ascii=False))
            put('sounds.json', json.dumps(dict(coll, presets=sounds), indent=1, ensure_ascii=False))
            put('kits.json', json.dumps(dict(kits_doc, kits=used), indent=2, ensure_ascii=False))
            for e in sorted(entries):
                put(e, z.read(e))
        tmp.replace(path)

    order = [by_name[row['name'].casefold()] for row in p['rows']]
    write(PACKS_DIR / 'files' / p['file'], order)
    authors = {snd.get('by') for snd in order} - {p['author'], None}
    if authors:
        print(f"note: the sounds say they are by {', '.join(sorted(authors))}, the pack by {p['author']}")
    print(f"{p['file']}: {size(PACKS_DIR / 'files' / p['file'])}, {len(order)} sounds, {len(kits_doc['kits'])} kits, {len(recordings)} recordings")

    if clips:
        out_dir = PACKS_DIR / 'audio' / p['slug']
        out_dir.mkdir(parents=True, exist_ok=True)
        takes = [f for f in clips.iterdir() if f.suffix.lower() in ('.wav', '.aif', '.aiff', '.flac', '.caf', '.m4a')]
        for row in p['rows']:
            stem = row.get('clip', row['slug'])
            found = [f for f in takes if re.fullmatch(rf'(\d+-)?{re.escape(stem)}(-take)?', f.stem)]
            if len(found) != 1:
                sys.exit(f"{row['name']}: {len(found)} takes in {clips} for '{stem}'")
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(found[0]), '-map_metadata', '-1', '-vn', '-c:a', 'aac_at', '-b:a', '112k',
                            '-movflags', '+faststart', '-fflags', '+bitexact', str(out_dir / f"{row['slug']}.m4a")], check=True)
        for old in out_dir.glob('*.m4a'):
            if old.stem not in {row['slug'] for row in p['rows']}:
                old.unlink()
        print(f"audio/{p['slug']}: {len(p['rows'])} demos, {sum(f.stat().st_size for f in out_dir.glob('*.m4a')) / 1e6:.1f} MB")


if __name__ == '__main__':
    if sys.argv[1:2] == ['prepare']:
        args = sys.argv[2:]
        clips = None
        if '--clips' in args:
            i = args.index('--clips')
            clips = Path(args[i + 1]).expanduser()
            del args[i:i + 2]
        if len(args) != 2:
            sys.exit(__doc__)
        prepare(args[0], Path(args[1]).expanduser(), clips)
    pages = {PACKS_DIR / 'index.html': list_page()}
    for p in PACKS:
        if p.get('soon'):
            continue
        if missing_files(p):
            print(f"{p['slug']}: no page yet, {len(missing_files(p))} files missing (build_packs.py prepare)")
            continue
        pages[PACKS_DIR / p['slug'] / 'index.html'] = pack_page(p)
    for path, html in pages.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html)
        print(f'wrote {path.relative_to(ROOT)}')
