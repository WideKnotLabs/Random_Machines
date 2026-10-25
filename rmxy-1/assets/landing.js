/* RMXY-1 landing page. Everything the page shows of the app is a real capture; this script only stages it:
   reveals on scroll, plays the videos while they are on screen, lifts the hero device, walks the effects
   rail through all nineteen as you scroll, and points the performance lens at each control.
   Without JavaScript every device shows its poster or still. Under prefers-reduced-motion nothing moves on its own. */
(() => {
  'use strict';
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));

  /* Reveal on scroll */
  const reveal = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('is-in'); reveal.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -8% 0px' });
  $$('[data-reveal]').forEach(el => reveal.observe(el));

  /* Videos: load when near, play only while visible */
  const loadVideo = v => {
    if (v.dataset.loaded) return;
    v.dataset.loaded = '1';
    /* a phone screen is about 1200 device pixels across: it gets the 1180-wide encode, a quarter of the pixels to decode */
    const small = window.innerWidth * (window.devicePixelRatio || 1) <= 1300 ? 'Small' : '';
    [['srcWebm', 'video/webm'], ['srcMp4', 'video/mp4']].forEach(([key, type]) => {
      const src = v.dataset[key + small] || v.dataset[key];
      if (!src) return;
      const s = document.createElement('source');
      s.src = src;
      s.type = type;
      v.append(s);
    });
    v.load();
  };
  const play = new IntersectionObserver(entries => {
    entries.forEach(({ target: v, isIntersecting }) => {
      if (isIntersecting) { loadVideo(v); if (!still && !v.dataset.hold) v.play().catch(() => {}); } else v.pause();
    });
  }, { rootMargin: '200px 0px' });
  $$('video[data-src-mp4]').forEach(v => play.observe(v));

  /* The MIDI wires pulse only while they are on screen */
  const live = new IntersectionObserver(entries => entries.forEach(e => e.target.classList.toggle('is-live', e.isIntersecting)));
  $$('.io').forEach(el => live.observe(el));

  /* Scroll-driven pieces share one frame callback */
  const onScroll = [];
  let queued = false;
  const tick = () => { queued = false; onScroll.forEach(f => f()); };
  const queue = () => { if (!queued) { queued = true; requestAnimationFrame(tick); } };
  window.addEventListener('scroll', queue, { passive: true });
  window.addEventListener('resize', queue);

  const ease = t => 1 - Math.pow(1 - clamp(t), 3);
  const seg = (p, a, b) => clamp((p - a) / (b - a));            /* 0→1 across [a, b] */
  const band = (p, a, b, c, d) => Math.min(seg(p, a, b), 1 - seg(p, c, d)); /* in a→b, out c→d */
  const lerp = (a, b, t) => a + (b - a) * t;
  /* write a style only when it changed: most pieces sit still through most of the scroll, and every write costs a style pass */
  const put = (el, k, v) => {
    const c = el.__css || (el.__css = {});
    if (c[k] === v) return;
    c[k] = v;
    if (k.startsWith('--')) el.style.setProperty(k, v); else el.style[k] = v;
  };
  /* a pinned stage plus the bar above it is 100svh: unlike innerHeight it holds still while a phone's toolbars slide */
  const viewH = pin => pin.offsetHeight + (parseFloat(getComputedStyle(pin).top) || 0);
  const progress = (track, pin) => { const r = track.getBoundingClientRect(); return clamp(-r.top / Math.max(1, r.height - viewH(pin))); };

  /* The story: hero → the pad → zoom into the rail → 8 slots → the nineteen */
  const story = $('[data-story]');
  if (story) {
    const track = $('.story__track', story);
    const pin = $('.story__pin', story);
    const scrim = $('[data-scrim]', story);
    const side = $('.story__copy--side', story);
    const padShade = $('[data-pad-shade]', story);
    const narrow = window.matchMedia('(max-width: 900px)');
    const ipad = $('[data-ipad]', story);
    const rail = $('[data-rail]', story);
    const beats = Object.fromEntries($$('[data-beat]', story).map(b => [b.dataset.beat, b]));
    /* the rail sequence: 19 keys (icon and label lifted from the app's own key art), a tray, and 8 slots that roll */
    const keys = $$('.fxr__keys .fxk', story);
    const keyIndex = Object.fromEntries(keys.map((k, i) => [k.dataset.id, i]));
    const tray = $('[data-tray]', story), wells = $$('i', tray);
    const slots = $$('[data-slots] .fxk', story);
    const FIRST = ['filter', 'delay', 'verb', 'eq', 'dist', 'cloud', 'erode', 'fold'];   /* the rack in the captures */
    const CHAINS = [                                                                    /* dice rolls: OSC and Shepard sit out, as in the app */
      ['cloud', 'shift', 'verb', 'filter', 'grain', 'delay', 'bloom', 'wide'],
      ['dist', 'mod', 'time', 'reson', 'eq', 'verb', 'erode', 'ring'],
      ['noise', 'filter', 'fold', 'delay', 'cloud', 'shift', 'bloom', 'eq'],
      ['grain', 'ring', 'erode', 'wide', 'filter', 'time', 'reson', 'verb'],
      ['eq', 'bloom', 'dist', 'cloud', 'mod', 'fold', 'delay', 'noise'],
      ['reson', 'time', 'shift', 'verb', 'dist', 'grain', 'filter', 'wide'],
    ];
    const art = id => `assets/media/keyart-${id}.webp`;
    CHAINS.flat().forEach(id => { const im = new Image(); im.src = art(id); });   /* warm the cache so rolls never flash */
    let shown = -1;
    const roll = n => {
      if (n === shown) return;
      const first = shown < 0;
      shown = n;
      slots.forEach((el, i) => {
        const img = $('img', el), id = CHAINS[n][i];
        if (first) { img.src = art(id); return; }
        setTimeout(() => {
          el.classList.remove('is-flip'); void el.offsetWidth; el.classList.add('is-flip');
          setTimeout(() => { img.src = art(id); }, 240);
        }, i * 55);
      });
    };
    roll(0);
    const setBeat = (el, v, dy = 0) => {
      put(el, 'opacity', v.toFixed(3));
      el.classList.toggle('is-vis', v > 0.01);
      put(el, 'translate', `0 ${((1 - v) * dy).toFixed(1)}px`);
    };
    const copyTop = $('.story__copy--top', story);
    const below = (box, b) => box.offsetTop + b.offsetTop + b.offsetHeight;   /* bottom of a beat's copy in the stage, ignoring its slide */
    /* a phone on its side has too little height for the pinned story: it reads as the plain sequence instead */
    const short = window.matchMedia('(orientation: landscape) and (max-height: 500px)');
    const staged = [ipad, rail, scrim, padShade, side, tray, ...Object.values(beats), ...keys, ...slots, ...wells];
    let flat = false;
    const heroVideo = $('video', ipad);
    let heroOn = true, Ps = -1, lastT = 0;
    if (still) story.classList.add('story--static');
    else onScroll.push(() => {
      if (story.classList.toggle('story--static', short.matches)) {
        if (!flat) { flat = true; staged.forEach(el => { el.removeAttribute('style'); el.__css = null; }); }
        return;
      }
      flat = false;
      const U = viewH(pin);
      const phone = narrow.matches;
      const r0 = track.getBoundingClientRect();
      /* the story follows the scroll through a short glide (about 80 ms), so wheel notches and uneven touch updates
         play as one smooth move instead of steps; a jump (a link, a reload part-way down) lands at once */
      const Pt = clamp(-r0.top, 0, r0.height - U) / (5.2 * U), now = performance.now();
      if (Ps < 0 || Math.abs(Pt - Ps) > 0.5) Ps = Pt;
      else Ps += (Pt - Ps) * (1 - Math.exp(-Math.min(now - lastT, 50) / 80));
      lastT = now;
      if (Math.abs(Pt - Ps) > 0.0002) queue(); else Ps = Pt;
      if (Ps === Pt && r0.bottom < -200) return;   /* scrolled well past the story: it holds its last frame */
      const P = Ps, p = P;   /* one scroll scale for every beat */
      const Pend = (r0.height - U) / (5.2 * U);
      /* copy */
      setBeat(beats.hero, 1 - seg(p, 0.012, 0.042), -24);
      setBeat(beats.move, band(p, 0.15, 0.20, 0.29, 0.33), 20);
      setBeat(beats.slots, band(P, 0.44, 0.48, 0.55, 0.59), 20);
      setBeat(beats.fx, band(P, 0.78, 0.82, 0.96, 1.0), 20);
      setBeat(beats.endless, seg(P, 1.10, 1.14), 20);
      /* the hero is the app itself, edge to edge; scrolling sets it into the iPad */
      const h = ease(seg(p, 0.035, 0.15));
      put(scrim, 'opacity', (1 - h).toFixed(3));   /* the darkening lifts as the screen settles into the iPad */
      put(ipad, '--frame', seg(p, 0.06, 0.14).toFixed(3));
      const pr = pin.getBoundingClientRect();
      const W = ipad.offsetWidth, bz = W * 0.022, sw = W - 2 * bz, sh = sw * 820 / 1180;
      const ox = bz + (14.5 + 575) / 1180 * sw, oy = bz + (27.5 + 61.25) / 820 * sh;  /* rail centre in the iPad capture */
      const railW = rail.offsetWidth;
      const S = railW / (1150 / 1180 * sw);
      const z = ease(seg(p, 0.31, 0.43));
      const H = W * 0.7124, L = ipad.offsetLeft, T0 = ipad.offsetTop;
      /* where the iPad settles: on a phone, in the space under the tallest copy it shares the stage with */
      let Yf = 0;
      if (phone) {
        const lo = below(copyTop, beats.move) + 24, hi = pr.height - H - 20;
        Yf = (lo <= hi ? (lo + hi) / 2 : lo) - T0;
      }
      /* the rail strip lands on the middle of the stage; on a phone it stays where the iPad's rail already is */
      const midY = phone ? T0 + Yf + oy : pr.height / 2;
      let s, X, Y;
      if (z > 0) {            /* zoom: carry the rail centre to the middle of the stage */
        s = lerp(1, S, z);
        X = lerp(L + ox, pr.width / 2, z) - L - s * ox;
        Y = lerp(T0 + Yf + oy, midY, z) - T0 - s * oy;
      } else {                /* enter: from edge to edge to its place in the frame */
        const s0 = phone ? pr.width / sw : Math.max(pr.width / sw, pr.height / sh);
        s = lerp(s0, 1, h);
        /* start with the app's top edge (under the status band) at the top of the stage, rail fully in view;
           on a phone the screen spans the width just under the hero copy */
        const X0 = pr.width / 2 - L - s0 * W / 2;
        const Y0 = phone ? Math.max(pr.height * 0.62 - s0 * H / 2, below(side, beats.hero) + 24 - s0 * bz) - T0
          : -s0 * (bz + 28 / 820 * sh) - T0;
        X = lerp(X0, 0, h);
        Y = lerp(Y0, Yf, h);
      }
      /* hero copy sits inside the XY pad (28–778 × 160–743 pt of the capture), fitted to what is on screen */
      if (!phone && p < 0.06) {
        const px = v => L + X + s * (bz + v / 1180 * sw), py = v => T0 + Y + s * (bz + v / 820 * sh);
        const left = px(28), right = px(778), top = Math.max(py(160), 0), bottom = Math.min(py(743), pr.height);
        const padW = right - left;
        put(side, 'left', `${(left + padW * 0.06).toFixed(1)}px`);
        put(side, 'width', `${(padW * 0.88).toFixed(1)}px`);
        put(side, 'top', `${((top + bottom) / 2).toFixed(1)}px`);
        put(side, '--fit-h', `${(bottom - top).toFixed(0)}px`);
        put(padShade, 'left', `${left.toFixed(1)}px`); put(padShade, 'top', `${top.toFixed(1)}px`);
        put(padShade, 'width', `${padW.toFixed(1)}px`); put(padShade, 'height', `${(bottom - top).toFixed(1)}px`);
      } else if (phone && side.style.top) { side.removeAttribute('style'); side.__css = null; }   /* back to the stylesheet after a rotation */
      put(padShade, 'opacity', (1 - h).toFixed(3));
      put(ipad, 'transform', `translate(${X.toFixed(1)}px, ${Y.toFixed(1)}px) scale(${s.toFixed(4)})`);
      const seen = 1 - seg(p, 0.42, 0.46);
      put(ipad, 'opacity', seen.toFixed(3));
      /* the hero video only decodes while the iPad is in sight */
      if ((seen > 0) !== heroOn) {
        heroOn = seen > 0;
        if (!heroOn) { heroVideo.dataset.hold = '1'; heroVideo.pause(); }
        else { delete heroVideo.dataset.hold; if (heroVideo.dataset.loaded) heroVideo.play().catch(() => {}); }
      }
      /* rail strip from the capture: in for "8 slots.", then it hands over to clean keys in a tray */
      put(rail, 'opacity', Math.min(seg(P, 0.42, 0.45), 1 - seg(P, 0.49, 0.53)).toFixed(3));
      const pw = pr.width, ph = pr.height, kr = 299 / 288;
      const railH = railW * 122.67 / 1150, kw = 96 / 1150 * railW;
      /* the eight keys as they sit in the rail strip */
      const rowAt = (i, cy) => [pw / 2 - railW / 2 + (99 + 113.33 * i) / 1150 * railW, cy - railH / 2 + 11.67 / 122.67 * railH, kw];
      put(rail, 'transform', `translate(-50%, -50%) translateY(${(midY - ph / 2).toFixed(1)}px)`);
      /* grid: the rail's eight drop straight down as the first row (on a phone, the first two rows of four);
         the other eleven rise into the rows below */
      const ROWS = phone ? [4, 4, 4, 4, 3] : [8, 6, 5];
      const order = FIRST.concat(keys.map(k => k.dataset.id).filter(id => !FIRST.includes(id)));
      const gTop = phone ? Math.max(below(copyTop, beats.fx), below(copyTop, beats.slots)) + 24 : Math.max(230, ph * 0.31);
      const maxC = Math.max(...ROWS), R = ROWS.length;
      const G = Math.min(phone ? 112 : 124, (pw * (phone ? 0.9 : 0.88)) / (maxC + (maxC - 1) * 0.22), (ph - gTop - 28) / (R * kr + (R - 1) * 0.22));
      const gap = G * 0.22;
      const gridAt = id => {
        let i = order.indexOf(id), row = 0;
        while (i >= ROWS[row]) { i -= ROWS[row]; row++; }
        const rowW = ROWS[row] * G + (ROWS[row] - 1) * gap;
        return [pw / 2 - rowW / 2 + i * (G + gap), gTop + row * (G * kr + gap), G];
      };
      /* a phone holds the eight as a rack of two rows of four, the size of the grid's keys, so they stay readable */
      const rackH = 2 * G * kr + gap, rackY = gTop + rackH / 2;
      const rackAt = (i, cy) => [pw / 2 - (4 * G + 3 * gap) / 2 + (i % 4) * (G + gap), cy - rackH / 2 + Math.floor(i / 4) * (G * kr + gap), G];
      const slotAt = phone ? rackAt : rowAt;
      const upY = Math.max(ph * 0.11, 30) + railH / 2;
      const endY = phone ? Math.max((below(copyTop, beats.endless) + ph) / 2, below(copyTop, beats.endless) + 32 + rackH / 2) : ph * 0.58;
      const place = (el, [x, y, w], o) => {
        put(el, 'opacity', o.toFixed(3));
        put(el, 'transform', `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) scale(${(w / 120).toFixed(4)})`);
      };
      const mix = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
      /* the eight before the grid opens: the rail rises to the top, or on a phone unfolds into the rack */
      const railY = lerp(midY, upY, ease(seg(P, 0.56, 0.64)));
      const restAt = i => phone ? rackAt(i, rackY) : rowAt(i, upY);
      const firstAt = i => phone ? mix(rowAt(i, midY), rackAt(i, rackY), ease(seg(P, 0.53 + i * 0.004, 0.61 + i * 0.004))) : rowAt(i, railY);
      /* the first roll lands in the order the keys stand in the grid (left to right, or reading order on a phone), so paths barely cross */
      const back = CHAINS[0].slice().sort((a, b) => { const A = gridAt(a), B = gridAt(b); return phone ? A[1] - B[1] || A[0] - B[0] : A[0] - B[0] || A[1] - B[1]; });
      if (back.join() !== CHAINS[0].join()) { CHAINS[0] = back; if (shown === 0) { shown = -1; roll(0); } }
      keys.forEach(el => {
        const id = el.dataset.id, f = FIRST.indexOf(id), c = back.indexOf(id), g = gridAt(id), n = order.indexOf(id);
        let pos, o;
        if (P < 0.64) {                                   /* sitting in the rail */
          pos = f >= 0 ? firstAt(f) : g;
          o = f >= 0 ? seg(P, 0.49, 0.53) : 0;
        } else if (P < 0.98) {                            /* the rail opens into the nineteen */
          if (f >= 0) {
            const t = ease(seg(P, 0.64 + f * 0.005, 0.74 + f * 0.005));
            pos = mix(restAt(f), g, t); o = 1;
          } else {
            const t = ease(seg(P, 0.69 + (n - 8) * 0.006, 0.77 + (n - 8) * 0.006));
            pos = [g[0], g[1] + (1 - t) * G * 0.6, g[2] * (0.92 + 0.08 * t)]; o = t;
          }
        } else if (c >= 0) {                              /* one roll of the dice glides back into the rail */
          const t = ease(seg(P, 1.02, 1.11));
          pos = mix(g, slotAt(c, endY), t); o = P < 1.16 ? 1 : 0;
        } else {                                          /* the rest clear the way first */
          const t = ease(seg(P, 0.98, 1.03));
          pos = [g[0], g[1] + t * G * 0.3, g[2] * (1 - 0.06 * t)]; o = 1 - t;
        }
        place(el, pos, o);
      });
      /* the tray: with the rail in, gone while the keys are out, back for the dice */
      const trayO = P < 1.0 ? Math.min(seg(P, 0.49, 0.53), 1 - seg(P, 0.66, 0.72)) : seg(P, 1.04, 1.10);
      const wellAt = wells.map((_, i) => P < 0.64 ? firstAt(i) : P < 1.0 ? restAt(i) : slotAt(i, endY));
      const tx0 = Math.min(...wellAt.map(w => w[0])), ty0 = Math.min(...wellAt.map(w => w[1]));
      const tx1 = Math.max(...wellAt.map(w => w[0] + w[2])), ty1 = Math.max(...wellAt.map(w => w[1] + w[2] * kr)), pad = wellAt[0][2] * 0.08;
      put(tray, 'opacity', trayO.toFixed(3));
      if (trayO > 0) {   /* the tray and its wells are laid out, not transformed: only while it shows */
        put(tray, 'width', `${(tx1 - tx0 + 2 * pad).toFixed(1)}px`); put(tray, 'height', `${(ty1 - ty0 + 2 * pad).toFixed(1)}px`);
        put(tray, 'transform', `translate(${(tx0 - pad).toFixed(1)}px, ${(ty0 - pad).toFixed(1)}px)`);
        wells.forEach((w, i) => { const [x, y, k] = wellAt[i];
          put(w, 'left', `${(pad + x - tx0).toFixed(1)}px`); put(w, 'top', `${(pad + y - ty0).toFixed(1)}px`);
          put(w, 'width', `${k.toFixed(1)}px`); put(w, 'height', `${(k * kr).toFixed(1)}px`); });
      }
      /* the rolling rail: the rolls share out whatever track is left, so a shorter phone track still shows them all */
      const live = P >= 1.16, every = Math.min(0.085, (Pend - 1.18) / CHAINS.length);
      slots.forEach((el, i) => place(el, slotAt(i, endY), live ? 1 : 0));
      roll(live ? Math.min(CHAINS.length - 1, Math.floor((P - 1.16) / every)) : 0);
    });
  }

  /* Built to perform: one control lit per step; each callout stays once it has appeared */
  const perf = $('[data-perform]');
  if (perf) {
    const track = $('.perform__track', perf);
    const stage = $('[data-stage]', perf);
    const dev = $('.perform__device', perf);
    const spot = $('[data-spot]', perf);
    const svg = $('[data-lines]', perf);
    const items = $$('.callouts li', perf);
    const NS = 'http://www.w3.org/2000/svg';
    const lines = items.map(() => { const g = document.createElementNS(NS, 'path'); svg.append(g); return g; });
    const dots = items.map(() => { const c = document.createElementNS(NS, 'circle'); c.setAttribute('r', '0'); svg.append(c); return c; });
    const layout = () => {
      const sr = stage.getBoundingClientRect(), scr = $('.device__screen', dev).getBoundingClientRect();
      const k = scr.width / 1180;
      items.forEach((li, i) => {
        const [x, y, w, h] = li.dataset.rect.split(' ').map(Number);
        /* right-angle leader lines that end at the control's outer edge and stay off the screen's content */
        const X = v => (v / sr.width * 100).toFixed(2), Y = v => (v / sr.height * 100).toFixed(2);
        const sx = scr.left - sr.left, sy = scr.top - sr.top;
        const side = li.dataset.side;
        let d, cx, cy;
        if (side === 'below') {
          cx = sx + (x + w / 2) * k; cy = sy + (y + h + 6) * k;
          li.style.left = `${X(cx)}%`;
          const lr = li.getBoundingClientRect();
          d = `M${X(cx)} ${Y(lr.top - sr.top - 10)} V${Y(cy)}`;
        } else {
          const lr = li.getBoundingClientRect();
          const left = side === 'left';
          cx = sx + (left ? x - 6 : x + w + 6) * k; cy = sy + (y + h / 2) * k;
          const lx = left ? lr.right - sr.left + 12 : lr.left - sr.left - 12;
          const ly = lr.top - sr.top + 12;
          const gutter = left ? (lx + sx) / 2 : (lx + sx + scr.width) / 2;
          if (li.dataset.route === 'under') {   /* run under the screen so the line never crosses other controls */
            const ux = sx + (x + w / 2) * k, under = sy + scr.height + (dev.offsetWidth * 0.011);
            d = `M${X(lx)} ${Y(ly)} H${X(gutter)} V${Y(under)} H${X(ux)} V${Y(sy + (y + h + 6) * k)}`;
          } else d = `M${X(lx)} ${Y(ly)} H${X(gutter)} V${Y(cy)} H${X(cx)}`;
        }
        lines[i].setAttribute('d', d);
        dots[i].setAttribute('cx', X(cx)); dots[i].setAttribute('cy', Y(cy));
      });
    };
    const aim = i => {
      const scr = $('.device__screen', dev), k = scr.clientWidth / 1180;
      if (i < 0 || i >= items.length) { spot.style.opacity = 0; return; }
      const [x, y, w, h] = items[i].dataset.rect.split(' ').map(Number), pad = 5;
      Object.assign(spot.style, { opacity: 1, left: `${(x - pad) * k}px`, top: `${(y - pad) * k}px`, width: `${(w + 2 * pad) * k}px`, height: `${(h + 2 * pad) * k}px` });
    };
    const wide = window.matchMedia('(min-width: 901px)');
    let cur = -2, laid = '';
    document.fonts?.ready.then(() => { laid = ''; queue(); });   /* callout heights move once the font is in */
    onScroll.push(() => {
      if (!wide.matches) { if (laid) { laid = ''; items.forEach(li => li.style.left = ''); } return; }
      const r = track.getBoundingClientRect();
      if (r.bottom < -200 || r.top > window.innerHeight + 200) return;   /* nothing to do while it is out of sight */
      /* the leader lines depend on sizes, not on the scroll: lay them out only when the stage changes size */
      const size = `${stage.offsetWidth}x${stage.offsetHeight}`;
      if (size !== laid) { laid = size; layout(); cur = -2; }
      const p = progress(track, $('.perform__pin', perf));
      const i = p < 0.08 ? -1 : p > 0.9 ? items.length : Math.min(items.length - 1, Math.floor((p - 0.08) / 0.82 * items.length));
      if (i === cur) return;
      cur = i;
      aim(i);
      items.forEach((li, k) => { li.classList.toggle('is-in', k <= i); li.classList.toggle('is-on', k === i || i === items.length); });
      lines.forEach((l, k) => { l.classList.toggle('is-in', k <= i); l.classList.toggle('is-on', k === i); });
      dots.forEach((d, k) => d.classList.toggle('is-in', k <= i));
    });
  }

  queue();
})();
