#!/usr/bin/env python3
"""Writes the INK Preset Packs pages from PACKS below: ink/packs/index.html lists the packs, and each released pack gets its
listening page at ink/packs/<slug>/index.html. Styles: ink/packs/packs.css.

A released pack: its .inksounds file in ink/packs/files/, one AAC preview per sound in ink/packs/audio/<pack>/<sound>.m4a
(a phrase rendered by INK's own engine: RM INK's `ink_render <library> <out> --pack <file> --scenes phrase --all`),
and the waveforms drawn here from those previews (ffmpeg decodes them). A pack with 'soon' is listed, not linked.
Usage: python3 tools/build_packs.py"""
from html import escape
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PACKS_DIR = ROOT / 'ink' / 'packs'
TESTFLIGHT = 'https://testflight.apple.com/join/mCCTYCpR'

PACKS = [
    {
        'slug': 'pluck-studies',
        'name': 'Pluck Studies',
        'file': 'pluck-studies.inksounds',
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
        'slug': 'dub',
        'name': 'Dub',
        'soon': True,
    },
]

BARS = 64


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
    return f'{path.stat().st_size / 1e6:.1f} MB'


def shell(*, title, description, canonical, up, body, script=''):
    """The page around `body`; `up` is the path back to the site root."""
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
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


def list_page():
    rows = []
    for n, p in enumerate(PACKS, 1):
        if p.get('soon'):
            rows.append(f'''
        <li class="entry entry--soon">
          <span class="entry__no">{n:02d}</span>
          <div class="entry__text"><h2>{escape(p['name'])}</h2><p class="entry__meta">Coming soon</p></div>
        </li>''')
            continue
        strip = wave(peaks(audio_of(p, p['sounds'][0][0])))
        rows.append(f'''
        <li class="entry">
          <a href="{p['slug']}/">
            <span class="entry__no">{n:02d}</span>
            <div class="entry__text"><h2>{escape(p['name'])}</h2><p class="entry__line">{escape(p['line'])}</p></div>
            <svg class="entry__wave" viewBox="0 0 256 40" preserveAspectRatio="none" aria-hidden="true"><path d="{strip}"/></svg>
            <span class="entry__go">Listen<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6"/></svg></span>
          </a>
        </li>''')
    body = f'''    <div class="packs__in">
      <a class="ink-mark" href="../../#ink"><img src="../../ink/assets/ink-wordmark.svg" alt="INK Synth" width="800" height="562"></a>
      <h1 class="packs__title">Preset Packs</h1>
      <p class="packs__lede">Sound packs for INK Synth. Listen to every sound, then download the pack.</p>
      <ol class="entries">{''.join(rows)}
      </ol>
    </div>'''
    return shell(title='Preset Packs — INK Synth | Random Machines',
                 description='Sound packs for INK Synth, the three-engine touch synthesizer for iPhone and iPad. '
                             'Listen to every sound, then download the .inksounds file.',
                 canonical='ink/packs/', up='../../', body=body)


def pack_page(p):
    file = PACKS_DIR / 'files' / p['file']
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
      <a class="ink-mark" href="../../../#ink"><img src="../../../ink/assets/ink-wordmark.svg" alt="INK Synth" width="800" height="562"></a>
      <a class="crumb" href="../"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H6M11 6l-6 6 6 6"/></svg>Preset Packs</a>
      <h1 class="packs__title">{escape(p['name'])}</h1>
      <p class="packs__lede">{escape(p['line'])}</p>
      <div class="pack__actions">
        <a class="btn btn--lg btn--primary" href="../files/{p['file']}" download="{escape(p['save_as'])}"><span>Download</span></a>
        <span class="pack__file">{size(file)} · Free</span>
      </div>
      <p class="pack__how">In INK Synth, tap Import in the Library and choose the file, or open it in INK from Files or AirDrop. <a href="../../manual/save-and-share-sounds.html">Save and share sounds</a></p>
      <ol class="sounds" aria-label="Sounds">{''.join(rows)}
      </ol>
      <p class="pack__credits">{escape(p['credits'])}</p>
    </div>'''
    return shell(title=f"{p['name']} — INK Synth Preset Packs | Random Machines",
                 description=f"{p['name']}: {p['line']}",
                 canonical=f"ink/packs/{p['slug']}/", up='../../../', body=body, script=PLAYER)


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


if __name__ == '__main__':
    pages = {PACKS_DIR / 'index.html': list_page()}
    for p in PACKS:
        if not p.get('soon'):
            pages[PACKS_DIR / p['slug'] / 'index.html'] = pack_page(p)
    for path, html in pages.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html)
        print(f'wrote {path.relative_to(ROOT)}')
