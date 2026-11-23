#!/usr/bin/env python3
"""Arp Magic's scores for the page's note view: what each demo plays, from RM INK's listening desk (read only).

  python3 tools/packs/scores_from_desk.py "<RM INK>/research/arp-demo-pack-2026-11-22" [desk/r6]   -> tools/packs/arp-magic-scores.json

For each sound in tools/packs/arp-magic.json (matched by name to the desk's cards):
  bpm, bar (beats), bars             the take's tempo and length (the demo is exactly its 8 bars)
  chords  [[name, [MIDI...]], ...]   the chord held in each bar, as voiced
  notes   [[t, MIDI, length, vel]]   every note the arp played, t and length in seconds from the demo's start (the render job's live
                                     notes, less the desk's lead-in: desk.py cuts the take T0 after Play)
  arp                                the sound's arp in a line (mode and direction, Notes, Division, Sustain, ...)
  moves   [{what, bars: [8 values]}] the settings the matrix moves bar by bar (the desk's arcs), only those that change
  kb      the chord keyboard as INK draws it in the sound's key: {key: "D minor", numerals, top (row 2), bottom (row 1, with Spice
          on when the sound uses it), spice, press: [[column, 0 top | 1 bottom] or null, a bar each]}, from the desk's own model
          of the keyboard (tools/keys.py there: ChordLogic.h's rows 1, 2 and Spice). A bar whose chord is no pad is null.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEAD_BEATS = 32                       # desk.py T0: eight bars after Play
NOTE = {n: i for i, n in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}
SPREAD = {'Wave', 'Sweep', 'Stairs', 'Picking', 'Fox cells', 'Pinky', 'Converge', 'Diverge', 'Walk'}


def midi(name):
    m = re.fullmatch(r'([A-G]#?)(-?\d)', name)
    return NOTE[m[1]] + 12 * (int(m[2]) + 1)


def arp_line(new):
    """'Sweep Down · Notes 8 · 16ths · Sustain All · Humanize': the arp as the page shows it."""
    mode = new['Mode'].replace("today's ", '')
    out = [f"{mode} {new['Transpose']}" if mode in SPREAD else mode]
    if mode not in SPREAD and new.get('Transpose') not in (None, 'Auto'):
        out.append(f"Transpose {new['Transpose']}")
    if new.get('Shift'):
        out.append(f"Shift {new['Shift']}")
    out.append(f"Notes {new['Notes']}" if new.get('Notes') not in (None, 'All') else 'All notes')
    out.append(new['Division'])
    if new.get('Sustain') not in (None, 'Off'):
        out.append(f"Sustain {new['Sustain']}")
    out += [x for x in ('Strum', 'Bass hand', 'Humanize') if new.get(x)]
    return ' · '.join(out)


SCALE_LABEL = {'Major': 'major', 'Minor': 'minor', 'Harmonic Min': 'harmonic minor', 'Penta Min': 'minor pentatonic',
               'Penta Maj': 'major pentatonic', 'Dorian': 'dorian', 'Lydian': 'lydian', 'Phrygian': 'phrygian', 'Mixolydian': 'mixolydian'}
ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']


def app_name(n):
    """keys.py's chord names as INK's pads spell them: Bbadd9, Aø7, A°, D°add11."""
    n = n.replace('(add9)', 'add9').replace('(add11)', 'add11').replace('m7b5', 'ø7')
    return re.sub(r'dim(?=$|7|add|/)', '°', n)


def keyboard(K, key, chords):
    """The pads of the sound's key, and which one each bar holds (its pitch classes; the voicing decides a tie)."""
    root_name, scale = key.split(' ', 1)
    root = K.NAMES.index(root_name) if root_name in K.NAMES else K.FLATS.index(root_name)
    flats = K.spelled_flat(scale, root)
    cols = range(len(K.SCALES[scale]))
    pads = {}
    for c in cols:
        for row in (2, 'S', 1):
            pads.setdefault(frozenset(x % 12 for x in K.voice(scale, root, c, row)), []).append((c, row))
    press, spice = [], False
    for _, notes in chords:
        found = pads.get(frozenset(x % 12 for x in notes), [])
        same = [cr for cr in found if any(sorted(x + 12 * k for x in K.voice(scale, root, cr[0], cr[1])) == sorted(notes) for k in (-2, -1, 0, 1, 2))]
        pick = (same or [cr for cr in found if cr[1] == 2] or found or [None])[0]
        spice |= bool(pick and pick[1] == 'S')
        press.append(None if pick is None else [pick[0], 0 if pick[1] == 2 else 1])
    numerals = []
    for c in cols:
        q = K.chord(scale, root, c, 1)[2]
        r = ROMAN[c] if q in ('maj', 'aug', 'sus4', 'sus2', '7sus4') else ROMAN[c].lower()
        numerals.append(r + ('°' if q == 'dim' else '+' if q == 'aug' else ''))
    return {'key': f"{(K.FLATS if flats else K.NAMES)[root]} {SCALE_LABEL.get(scale, scale.lower())}", 'numerals': numerals,
            'top': [app_name(K.name(scale, root, c, 2, flats)) for c in cols],
            'bottom': [app_name(K.name(scale, root, c, 'S' if spice else 1, flats)) for c in cols], 'spice': spice, 'press': press}


def moves(arcs):
    """The desk's arcs ('Division: 8ths 8ths ...', 'Gate: 87 87 42 ... %') as 8 values a bar; those that never change are left out."""
    out = []
    for a in arcs or []:
        what, _, rest = a.partition(': ')
        pct = rest.endswith(' %')
        rest = rest[:-2] if pct else rest
        vals = re.findall(r"\([^)]*\)|today's \S+(?: \S+)?(?= today's|$)|\S+", rest)
        vals = [v.replace("today's ", '') + ('%' if pct else '') for v in vals]
        if len(vals) == 8 and len(set(vals)) > 1 and not any(v.startswith('(') for v in vals):
            out.append({'what': what, 'bars': vals})
        elif len(vals) != 8:
            print(f'  left out (not 8 bars): {a}')
    return out


def main(root, rnd='desk/r6'):
    root = Path(root).expanduser()
    sys.path.insert(0, str(root / 'tools'))
    import keys as K
    desk = json.loads((root / rnd / 'data.json').read_text())
    cards = {c['name'].casefold(): c for c in desk['cards']}
    roster = json.loads((HERE / 'arp-magic.json').read_text())['sounds']
    bpm = float(desk.get('tempo', 84)); bar = 4; bar_s = 60 / bpm * bar; lead = LEAD_BEATS * 60 / bpm
    scores = {}
    for row in roster:
        c = cards.get(row['name'].casefold())
        if not c:
            sys.exit(f"{row['name']}: no card on the desk ({rnd})")
        job = root / 'renders/take' / f"{c['n']:02d}-{c['slug']}.json"
        live = json.loads(job.read_text())['live']['notes']
        notes = [[round(t - lead, 3), n, round(d, 3), v] for t, _, n, v, d in live if lead - 0.03 <= t < lead + 8 * bar_s - 0.03]
        chords = [[name, [midi(x) for x in voicing.split()]] for name, voicing in c['prog']]
        kb = keyboard(K, c['key'], chords)
        chords = [[app_name(name), notes] for name, notes in chords]
        off = [chords[b][0] for b, x in enumerate(kb['press']) if x is None]
        if off:
            print(f"  {row['name']}: not on the chord keyboard: {', '.join(off)}")
        scores[row['slug']] = {'bpm': bpm, 'bar': bar, 'bars': 8, 'chords': chords, 'notes': notes,
                               'arp': arp_line(c['new']), 'moves': moves(c.get('arcs')), 'kb': kb}
        print(f"{row['name']}: {len(notes)} notes, {scores[row['slug']]['arp']}" + ''.join(f" | {m['what']}" for m in scores[row['slug']]['moves']))
    out = HERE / 'arp-magic-scores.json'
    out.write_text(json.dumps({'about': f'Made by scores_from_desk.py from {rnd} (placeholder: round 6 takes).', 'scores': scores},
                              separators=(',', ':')) + '\n')
    print(f'wrote {out.relative_to(HERE.parents[1])}: {out.stat().st_size / 1e3:.0f} KB')


if __name__ == '__main__':
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    main(*sys.argv[1:])
