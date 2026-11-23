#!/usr/bin/env python3
"""Writes the INK Preset Packs pages from PACKS below: ink/packs/index.html lists the packs, and each released pack gets its
listening page at ink/packs/<slug>/index.html. Styles: ink/packs/packs.css.

A released pack: its .inksounds file in ink/packs/files/, one AAC preview per sound in ink/packs/audio/<pack>/<sound>.m4a
(a phrase rendered by INK's own engine: RM INK's `ink_render <library> <out> --pack <file> --scenes phrase --all`),
and the waveforms drawn here from those previews (ffmpeg decodes them). A pack with 'soon' is listed, not linked.

A pack with a 'roster' (Arp Magic) also downloads sound by sound. Its data (each sound's name, family and line, the credits) is in
tools/packs/<slug>.json, and `split` writes its files from the pack INK's tools made:
  files/<slug>.zip              the whole pack, its manifest naming the pack and its author (the folder and credit INK shows)
  files/<slug>/<sound>.zip      a pack of one: the sound, the kit it plays with all that kit's recordings, its wavetable if it has one.
                                A kit travels whole: its fingerprint is its eight slots, so a sound and the whole pack land on one kit
                                in INK, stored once, and the sound is skipped as already there (sound library plan 4.2)
  audio/<slug>/<sound>.m4a      the demo, AAC at 112 kb/s from the take each sound's row names in --clips (<sound>.wav, or <n>-<sound>-take.wav)
It refuses a pack whose sounds and the roster's differ, and one with a recording no credit in the roster covers.
Usage: python3 tools/build_packs.py                                                   the pages
       python3 tools/build_packs.py split <slug> <pack.inksounds> [--clips <folder>]  a roster pack's files, then the pages"""
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
        # Free while the beta opens, every sound with its demo, the whole pack or any one sound to download, each with its size
        # (owner, 23 November 2026). Line, families, sounds and credits: the roster. Files: `split` (see the top).
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


for _p in PACKS:
    if _p.get('roster'):
        load_roster(_p)


def missing_files(p):
    """What a released pack's page needs and does not have yet (a roster pack before `split`)."""
    need = [PACKS_DIR / 'files' / p['file']] + [audio_of(p, slug) for slug, _ in p['sounds']]
    if p.get('roster'):
        need += [sound_file(p, slug) for slug, _ in p['sounds']]
    return [f for f in need if not f.exists()]


def sound_file(p, slug):
    return PACKS_DIR / 'files' / p['slug'] / f'{slug}.zip'


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


GET_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 10.5l5 5 5-5M5 20h14"/></svg>'


def checked(file: Path, href, save_as):
    """What DOWNLOAD needs on a button: where the bytes are, the name to save them under, their size and SHA-256."""
    return (f'href="{href}" download="{escape(save_as)}" data-bytes="{file.stat().st_size}" '
            f'data-sha256="{hashlib.sha256(file.read_bytes()).hexdigest()}"')


def get_button(item, label, up='', price='Free'):
    """The Download button for a pack file (item: 'file', 'save_as') and the line beside it, which DOWNLOAD uses."""
    file = PACKS_DIR / 'files' / item['file']
    return (f'<a class="ink-btn ink-btn--fill pack__get" {checked(file, up + "files/" + item["file"], item["save_as"])}>{GET_ICON}'
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
            print(f"{p['slug']}: left off the list, its files are not here yet (build_packs.py split)")
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
    """A pack that downloads whole or sound by sound: each row plays its demo and has its own Download with its size."""
    count = {g['id']: sum(row['group'] == g['id'] for row in p['rows']) for g in p['groups']}
    fams = ''.join(f'<button type="button" aria-pressed="false" data-group="{g["id"]}">{escape(g["name"])} <span>{count[g["id"]]}</span></button>'
                   for g in p['groups'] if count[g['id']])
    rows = []
    for row in p['rows']:
        slug, name = row['slug'], row['name']
        path = wave(peaks(audio_of(p, slug)))
        file = sound_file(p, slug)
        rows.append(f'''
        <li class="snd snd--get" data-src="../audio/{p['slug']}/{slug}.m4a" data-group="{row['group']}">
          <button class="snd__play" type="button" aria-label="Play {escape(name)}"><svg viewBox="0 0 24 24" aria-hidden="true"><path class="i-play" d="M8 5.5v13l11-6.5z"/><path class="i-stop" d="M7 7h10v10H7z"/></svg></button>
          <div class="snd__text"><h3>{escape(name)}</h3><p>{escape(row['line'])}</p></div>
          <div class="snd__wave" aria-hidden="true">
            <svg viewBox="0 0 256 40" preserveAspectRatio="none"><path d="{path}"/></svg>
            <svg class="snd__on" viewBox="0 0 256 40" preserveAspectRatio="none"><path d="{path}"/></svg>
          </div>
          <div class="snd__get">
            <a class="ink-btn pack__get" {checked(file, f"../files/{p['slug']}/{slug}.zip", name + '.inksounds')} aria-label="Download {escape(name)}, {size(file)}">{GET_ICON}{size(file)}</a>
            <span class="pack__file" role="status"></span>
          </div>
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
        {get_button(p, 'Download all ' + str(len(p['rows'])), up='../', price=p.get('price', 'Free'))}
      </div>
      <p class="pack__how">Or download any one sound: it comes with the kit of recordings it plays, and INK keeps a kit once, however many of its sounds you add. In INK Synth, tap Import in the Library and choose the file, or open it in INK from Files or AirDrop. <a href="../../manual/save-and-share-sounds.html">Save and share sounds</a></p>
      <div class="fams" role="group" aria-label="Show" hidden><button type="button" aria-pressed="true" data-group="">All <span>{len(p['rows'])}</span></button>{fams}</div>
      <ol class="sounds" aria-label="Sounds">{''.join(rows)}
      </ol>{credits}
    </div>'''
    return shell(title=f"{p['name']} — INK Synth Preset Packs | Random Machines",
                 description=f"{p['name']}: {p['line']}",
                 canonical=f"ink/packs/{p['slug']}/", up='../../../', body=body, script=PLAYER + FAMILIES + DOWNLOAD,
                 draft=bool(p.get('draft')))


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
      audio.play().then(() => { r.classList.add('is-playing'); label(r, 'Stop'); cancelAnimationFrame(frame); draw(); }).catch(stop);
    };
    audio.addEventListener('ended', stop);
    document.querySelectorAll('.snd').forEach(r => {
      r.querySelector('.snd__play').addEventListener('click', () => {
        if (r === row && !audio.paused) { audio.pause(); stop(); } else play(r);
      });
      r.querySelector('.snd__wave').addEventListener('click', e => {
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

DOWNLOAD = '''  <script>
  // Download saves one .inksounds file, for every Download on the page (a pack's, a demo's on the list, each sound's on a roster pack).
  // The files are stored as .zip (see PACKS), and Safari would unzip a .zip it downloads into a folder INK cannot import, so the page
  // fetches the bytes, checks them against the file's size and SHA-256, and saves them under the .inksounds name. A download cut
  // short is not saved; the line by the button says so. A big file counts its progress there.
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


def split(slug, source: Path, clips: Path = None):
    """A roster pack's files from the pack INK's tools made (see the top). Every file is written the same way each time
    (fixed order, dates and compression), so a sound that did not change keeps its bytes, its SHA-256 and its place in git."""
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
    for row, snd in zip(p['rows'], order):
        write(sound_file(p, row['slug']), [snd])
    keep = {f"{row['slug']}.zip" for row in p['rows']}
    for old in (PACKS_DIR / 'files' / p['slug']).glob('*.zip'):
        if old.name not in keep:
            old.unlink()
    authors = {snd.get('by') for snd in order} - {p['author'], None}
    if authors:
        print(f"note: the sounds say they are by {', '.join(sorted(authors))}, the pack by {p['author']}")
    print(f"{p['file']}: {size(PACKS_DIR / 'files' / p['file'])}, {len(order)} sounds, {len(kits_doc['kits'])} kits, {len(recordings)} recordings")
    for row in p['rows']:
        print(f"  {row['name']}: {size(sound_file(p, row['slug']))}")

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
    if sys.argv[1:2] == ['split']:
        args = sys.argv[2:]
        clips = None
        if '--clips' in args:
            i = args.index('--clips')
            clips = Path(args[i + 1]).expanduser()
            del args[i:i + 2]
        if len(args) != 2:
            sys.exit(__doc__)
        split(args[0], Path(args[1]).expanduser(), clips)
    pages = {PACKS_DIR / 'index.html': list_page()}
    for p in PACKS:
        if p.get('soon'):
            continue
        if missing_files(p):
            print(f"{p['slug']}: no page yet, {len(missing_files(p))} files missing (build_packs.py split)")
            continue
        pages[PACKS_DIR / p['slug'] / 'index.html'] = pack_page(p)
    for path, html in pages.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html)
        print(f'wrote {path.relative_to(ROOT)}')
