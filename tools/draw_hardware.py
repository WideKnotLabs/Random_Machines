#!/usr/bin/env python3
"""Line drawings of the MIDI hardware shown on the RMXY-1 landing page.

Drawn for this site from the makers' published top views (panel layout only: no photos, logos or printed
labels):
    Elektron Digitakt II  -> rmxy-1/assets/shots/hw-digitakt.svg
    Arturia MicroFreak    -> rmxy-1/assets/shots/hw-microfreak.svg

Style (round 3 tokens): drawn for a black (#000) page, strokes in #f5f5f7 at low opacity, hairline weights
that are the same fraction of the drawing width in both files (so both read identically at the same rendered
width), accent #ff6a00 only on a few tiny LEDs and key underlines. No fills besides black, no gradients.
Each viewBox is the body outline plus the same proportional padding, so nothing clips.

The only motion is a quiet running step light (Digitakt) and a soft key underline (MicroFreak); both stop
under prefers-reduced-motion. Usage: python3 tools/draw_hardware.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'rmxy-1' / 'assets' / 'shots'
INK = 'rgba(245,245,247,0.55)'
DIM = 'rgba(245,245,247,0.32)'
FAINT = 'rgba(245,245,247,0.16)'
ACCENT = '#ff6a00'
BLACK = '#000'

# Stroke weights as a fraction of the body width, so equal rendered widths give equal hairlines.
HAIR = 0.0019      # main outlines
FINE = 0.0013      # secondary detail
PAD = 0.012        # padding around the body, fraction of body width


def svg(body_box, body, style, label, weight):
    x0, y0, x1, y1 = body_box
    w = x1 - x0
    pad = PAD * w + weight  # padding plus stroke overhang
    vx, vy = round(x0 - pad, 2), round(y0 - pad, 2)
    vw, vh = round(w + 2 * pad, 2), round(y1 - y0 + 2 * pad, 2)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx} {vy} {vw} {vh}" width="{round(vw)}" height="{round(vh)}" role="img" aria-label="{label}">\n'
        f'<style>{style}\n@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}</style>\n'
        f'{body}\n</svg>\n'
    )


# ---------------------------------------------------------------- Digitakt II

def digitakt():
    W, H = 430, 355
    sw, fw = round(HAIR * (W - 3), 3), round(FINE * (W - 3), 3)
    o = []
    add = o.append
    add(f'<g fill="none" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round">')
    add('<rect x="1.5" y="1.5" width="427" height="352" rx="7"/>')
    # rear-edge ports (as small outlines, no printed labels) and screws
    for x, w in [(38, 10), (64, 26), (126, 26), (186, 14), (222, 14), (262, 14), (304, 10), (340, 10), (382, 12)]:
        add(f'<rect x="{x - w / 2}" y="7" width="{w}" height="4" rx="1" stroke="{FAINT}" stroke-width="{fw}"/>')
    for x, y in [(20, 9), (199, 9), (410, 9), (20, 346), (199, 346), (410, 346)]:
        add(f'<circle cx="{x}" cy="{y}" r="2.6" stroke="{DIM}" stroke-width="{fw}"/>')

    def knob(cx, cy, r):
        add(f'<circle cx="{cx}" cy="{cy}" r="{r}"/><circle cx="{cx}" cy="{cy}" r="{r - 3.2}" stroke="{FAINT}" stroke-width="{fw}"/>'
            f'<line x1="{cx}" y1="{cy - r + 2.4}" x2="{cx}" y2="{cy - r + 7}"/>')

    def btn(cx, cy, w=18, h=15):
        add(f'<rect x="{cx - w / 2}" y="{cy - h / 2}" width="{w}" height="{h}" rx="2.6"/>')

    knob(32, 67, 11)
    knob(32, 116, 11)
    # screen: bezel and a clean, empty display
    add('<rect x="63" y="44" width="134" height="104" rx="4"/>')
    add(f'<rect x="70" y="51" width="120" height="68" rx="1.5" stroke="{DIM}"/>')
    # data entry knobs A-H
    for cy in [66, 116]:
        for cx in [236, 289, 342, 395]:
            knob(cx, cy, 12)
    # page buttons
    for cx in [236, 267, 298, 330, 361, 393]:
        btn(cx, 160)
    btn(40, 182, 32, 18)
    for cx in [86, 118, 151, 184]:
        btn(cx, 182)
    # transport: record, play, stop (the glyphs are the controls' shapes, kept for recognition)
    for i, cx in enumerate([92, 135, 177]):
        btn(cx, 213, 28, 16)
        glyph = [f'<circle cx="{cx}" cy="213" r="3.2"/>', f'<path d="M{cx - 2.6} 209.6 l5.8 3.4 -5.8 3.4z"/>', f'<rect x="{cx - 3}" y="210" width="6" height="6"/>'][i]
        add(glyph.replace('/>', f' stroke="{DIM}" stroke-width="{fw}"/>'))
    for cy in [213, 249, 283, 316]:
        btn(40, cy, 28, 16)
    btn(236, 198)
    btn(236, 230)
    for cx, cy, d in [(297, 196, 'M-3 1.6 l3 -3.2 3 3.2'), (266, 229, 'M1.6 -3 l-3.2 3 3.2 3'), (297, 229, 'M-3 -1.6 l3 3.2 3 -3.2'), (329, 229, 'M-1.6 -3 l3.2 3 -3.2 3')]:
        btn(cx, cy)
        add(f'<path d="M{cx} {cy} m{d[1:]}" stroke="{DIM}" stroke-width="{fw}"/>')
    # pattern-page LEDs: outlined, one lit
    for row, cy in enumerate([193, 205]):
        for col, cx in enumerate([368, 380, 392, 404]):
            if row == 0 and col == 0:
                add(f'<circle cx="{cx}" cy="{cy}" r="1.8" fill="{ACCENT}" stroke="none"/>')
            else:
                add(f'<circle cx="{cx}" cy="{cy}" r="1.8" stroke="{DIM}" stroke-width="{fw}"/>')
    btn(388, 229, 26, 15)
    # 16 trig keys with a quiet running step light
    for i in range(16):
        cx = round(93 + (i % 8) * 42.14, 2)
        cy = 273 if i < 8 else 314
        add(f'<rect x="{cx - 16}" y="{cy - 16}" width="32" height="32" rx="4"/>')
        add(f'<rect class="dt-step" x="{cx - 6}" y="{cy + 9}" width="12" height="1.4" rx="0.7" fill="{ACCENT}" stroke="none" style="animation-delay:{i * 0.125:.3f}s"/>')
    add('</g>')
    style = (
        '.dt-step{opacity:0;animation:dtStep 2s steps(1,end) infinite}'
        '@keyframes dtStep{0%{opacity:.8}6.25%{opacity:0}100%{opacity:0}}'
    )
    return svg((1.5, 1.5, W - 1.5, H - 1.5), '\n'.join(o), style,
               'Line drawing of an Elektron Digitakt II: screen, eight data knobs and sixteen trig keys', sw)


# ---------------------------------------------------------------- MicroFreak

def microfreak():
    X0, Y0, X1, Y1 = 12, 4, 788, 582
    sw, fw = round(HAIR * (X1 - X0), 3), round(FINE * (X1 - X0), 3)
    o = []
    add = o.append
    add(f'<g fill="none" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round">')
    add(f'<rect x="{X0}" y="{Y0}" width="{X1 - X0}" height="{Y1 - Y0}" rx="12"/>')

    def knob(cx, cy, r, big=False):
        inner = f'<circle cx="{cx}" cy="{cy}" r="{r - 5}" stroke="{FAINT}" stroke-width="{fw}"/>' if big else ''
        add(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>{inner}'
            f'<line x1="{cx}" y1="{cy - r + 3}" x2="{cx}" y2="{cy - r * 0.35}"/>')

    def rule(x1, x2, y):
        add(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{FAINT}" stroke-width="{fw}"/>')

    def leds(x, y0, n, step=10):
        for i in range(n):
            add(f'<circle cx="{x}" cy="{y0 + i * step}" r="2" stroke="{DIM}" stroke-width="{fw}"/>')

    # modulation matrix
    cols = [70, 97, 122, 148, 175, 200, 227]
    for i in range(5):
        rule(54, 234, 62 + i * 12.5)
    for x in cols:
        add(f'<line x1="{x}" y1="48" x2="{x}" y2="118" stroke="{FAINT}" stroke-width="{fw}"/>')
    lit = {(0, 1), (2, 3), (3, 5)}
    for j, x in enumerate(cols):
        for i in range(5):
            y = 62 + i * 12.5
            if (i, j) in lit:
                add(f'<circle cx="{x}" cy="{y}" r="2.4" fill="{ACCENT}" stroke="none"/>')
            else:
                add(f'<circle cx="{x}" cy="{y}" r="2.4" stroke="{DIM}" stroke-width="{fw}"/>')
    for j in range(4, 7):
        add(f'<circle cx="{cols[j] + 4}" cy="26" r="8"/><circle cx="{cols[j] + 4}" cy="26" r="4" stroke="{DIM}" stroke-width="{fw}"/>')
    knob(285, 72, 20, big=True)
    knob(352, 72, 13)
    add(f'<rect x="324" y="94" width="56" height="14" rx="2" stroke="{DIM}" stroke-width="{fw}"/>')
    knob(412, 72, 12)
    # screen block: panel, clean display, preset / save / utility, master volume
    add('<rect x="450" y="33" width="256" height="78" rx="4"/>')
    add(f'<rect x="462" y="52" width="62" height="42" rx="2" stroke="{DIM}"/>')
    knob(556, 69, 19, big=True)
    knob(616, 69, 14)
    knob(673, 69, 14)
    knob(742, 72, 20, big=True)
    # oscillator / filter / cycling envelope
    for x1, x2 in [(110, 330), (340, 500), (505, 776)]:
        rule(x1, x2, 124)
    knob(58, 160, 19, big=True)
    for x in [143, 195, 248, 300]:
        knob(x, 160, 17, big=True)
    knob(352, 160, 12)
    leds(372, 150, 3)
    knob(420, 160, 20, big=True)
    knob(472, 160, 17, big=True)
    knob(520, 160, 12)
    leds(540, 150, 3)
    for x in [583, 638, 692, 745]:
        knob(x, 160, 17, big=True)
    # octave / arp-seq / lfo / envelope
    for x1, x2 in [(22, 120), (180, 330), (340, 500), (510, 776)]:
        rule(x1, x2, 212)
    add('<rect x="30" y="231" width="76" height="28" rx="14"/>')
    add('<circle cx="46" cy="245" r="10"/><circle cx="90" cy="245" r="10"/>')
    for x in [143, 195, 235]:
        knob(x, 245, 13)
    leds(258, 232, 4, 9)
    knob(300, 245, 19, big=True)
    knob(365, 245, 13)
    for i in range(3):
        add(f'<path d="M384 {236 + i * 10} q4 -6 8 0 t8 0" stroke="{DIM}" stroke-width="{fw}"/>')
    knob(470, 245, 19, big=True)
    knob(530, 245, 13)
    for x in [583, 638, 692, 745]:
        knob(x, 245, 17, big=True)
    # divider band above the keybed
    add(f'<line x1="{X0}" y1="292" x2="{X1}" y2="292"/>')
    add(f'<line x1="{X0}" y1="326" x2="{X1}" y2="326"/>')
    # arp / seq buttons, touch strip
    for x in [60, 115, 160, 205, 250, 300, 345, 390]:
        add(f'<rect x="{x - 18}" y="336" width="36" height="30" rx="3"/>')
    add('<rect x="420" y="336" width="340" height="32" rx="3"/>')
    # flat capacitive keyboard, 25 keys: clean outlines
    kx, ky, kh = 26, 378, 196
    kw = (774 - kx) / 15
    black = [0, 1, 3, 4, 5, 7, 8, 10, 11, 12]
    for i in range(15):
        x = round(kx + i * kw, 2)
        add(f'<rect x="{round(x + 1.5, 2)}" y="{ky}" width="{round(kw - 3, 2)}" height="{kh}" rx="3"/>')
    # soft key underlines (accent), two keys alternating
    for n, i in enumerate([4, 9]):
        x = kx + i * kw + kw / 2
        cls = 'mf-key mf-key2' if n else 'mf-key'
        add(f'<rect class="{cls}" x="{round(x - 10, 2)}" y="{ky + kh - 12}" width="20" height="1.6" rx="0.8" fill="{ACCENT}" stroke="none"/>')
    for i in black:
        x = round(kx + (i + 1) * kw - 15, 2)
        add(f'<rect x="{x}" y="{ky - 4}" width="30" height="112" rx="4" fill="{BLACK}" stroke="none"/>')
        add(f'<rect x="{round(x + 4, 2)}" y="{ky}" width="22" height="104" rx="3"/>')
    add('</g>')
    style = (
        '.mf-key{opacity:0;animation:mfKey 3.2s ease-out infinite}.mf-key2{animation-delay:1.6s}'
        '@keyframes mfKey{0%{opacity:.8}35%{opacity:0}100%{opacity:0}}'
    )
    return svg((X0, Y0, X1, Y1), '\n'.join(o), style,
               'Line drawing of an Arturia MicroFreak: modulation matrix, synth panel and flat touch keyboard', sw)


if __name__ == '__main__':
    (OUT / 'hw-digitakt.svg').write_text(digitakt())
    (OUT / 'hw-microfreak.svg').write_text(microfreak())
    print('wrote hw-digitakt.svg, hw-microfreak.svg')
