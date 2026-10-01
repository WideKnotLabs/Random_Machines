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
    [['srcWebm', 'video/webm'], ['srcMp4', 'video/mp4']].forEach(([key, type]) => {
      if (!v.dataset[key]) return;
      const s = document.createElement('source');
      s.src = v.dataset[key];
      s.type = type;
      v.append(s);
    });
    v.load();
  };
  const play = new IntersectionObserver(entries => {
    entries.forEach(({ target: v, isIntersecting }) => {
      if (isIntersecting) { loadVideo(v); if (!still) v.play().catch(() => {}); } else v.pause();
    });
  }, { rootMargin: '200px 0px' });
  $$('video[data-src-mp4]').forEach(v => play.observe(v));

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
  const progress = track => { const r = track.getBoundingClientRect(); return clamp(-r.top / Math.max(1, r.height - window.innerHeight)); };

  /* The story: hero → the pad → zoom into the rail → 8 slots → the nineteen */
  const story = $('[data-story]');
  if (story) {
    const track = $('.story__track', story);
    const pin = $('.story__pin', story);
    const phone = $('[data-phone]', story);
    const rail = $('[data-rail]', story);
    const beats = Object.fromEntries($$('[data-beat]', story).map(b => [b.dataset.beat, b]));
    const cats = $$('.cat', story);
    /* key captures replace the drawn tiles once they exist (data-keys on the section) */
    if (story.dataset.keys) $$('.cat li', story).forEach(li => {
      const img = new Image(); img.src = `assets/media/key-${li.dataset.id}.webp`; img.alt = '';
      img.onload = () => { li.classList.add('has-img'); li.prepend(img); };
    });
    const setBeat = (el, v, dy = 0) => {
      el.style.opacity = v.toFixed(3);
      el.classList.toggle('is-vis', v > 0.01);
      el.style.translate = `0 ${((1 - v) * dy).toFixed(1)}px`;
    };
    if (still) story.classList.add('story--static');
    else onScroll.push(() => {
      const p = progress(track);
      /* copy */
      setBeat(beats.hero, 1 - seg(p, 0.07, 0.13), -24);
      setBeat(beats.move, band(p, 0.12, 0.17, 0.27, 0.31), 24);
      setBeat(beats.slots, band(p, 0.43, 0.47, 0.55, 0.59), 20);
      setBeat(beats.fx, seg(p, 0.60, 0.65), 20);
      /* phone: zoom its rail to the middle of the stage, then hand over to the full rail */
      const z = ease(seg(p, 0.31, 0.44));
      const pr = pin.getBoundingClientRect();
      const fw = phone.offsetWidth, fh = phone.offsetHeight;
      const fx = phone.offsetLeft, fy = phone.offsetTop;
      const ox = fx + fw / 2, oy = fy + fh * 0.11;
      const tx = pr.width / 2 - ox, ty = pr.height * 0.5 - oy;
      const S = Math.min(1.8, (pr.width * 0.9) / fw);   /* never upscale the capture past sharp */
      phone.style.transform = `translate(${(tx * z).toFixed(1)}px, ${(ty * z).toFixed(1)}px) scale(${(1 + (S - 1) * z).toFixed(3)})`;
      phone.style.opacity = (1 - seg(p, 0.36, 0.43)).toFixed(3);
      /* the rail drops in, sits for "8 slots", then lifts away for the grid */
      const rin = ease(seg(p, 0.35, 0.44)), rout = ease(seg(p, 0.56, 0.62));
      rail.style.opacity = Math.min(rin, 1 - rout).toFixed(3);
      rail.style.transform = `translate(-50%, -50%) scale(${(0.55 + 0.45 * rin - rout * 0.08).toFixed(3)})`;
      /* the nineteen, a category at a time, then the lines under them */
      cats.forEach((c, i) => {
        const t = ease(seg(p, 0.60 + i * 0.025, 0.66 + i * 0.025));
        $$('li', c).forEach((li, k) => { const u = ease(seg(p, 0.60 + i * 0.025 + k * 0.01, 0.66 + i * 0.025 + k * 0.01)); li.style.opacity = u; li.style.transform = `translateY(${(1 - u) * 24}px)`; });
        $('h3', c).style.opacity = t;
        const l = ease(seg(p, 0.66 + i * 0.025, 0.72 + i * 0.025));
        $('p', c).style.opacity = l;
      });
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
          d = `M${X(lx)} ${Y(ly)} H${X(gutter)} V${Y(cy)} H${X(cx)}`;
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
    let cur = -2;
    onScroll.push(() => {
      if (!wide.matches) { items.forEach(li => li.style.left = ''); return; }
      layout();
      const p = progress(track);
      const i = p < 0.08 ? -1 : p > 0.9 ? items.length : Math.min(items.length - 1, Math.floor((p - 0.08) / 0.82 * items.length));
      if (i === cur) return;
      cur = i;
      aim(i);
      items.forEach((li, k) => { li.classList.toggle('is-in', k <= i); li.classList.toggle('is-on', k === i || i === items.length); });
      lines.forEach((l, k) => { l.classList.toggle('is-in', k <= i); l.classList.toggle('is-on', k === i); });
      dots.forEach((d, k) => d.classList.toggle('is-in', k <= i));
    });
  }

  /* Generators: cycle the three editors */
  const gen = $('[data-gen]');
  if (gen && !still) {
    const imgs = $$('.gen__shots img', gen);
    const names = $$('.gen__names li', gen);
    if (imgs.length > 1) {
      let i = 0, t = 0;
      const step = () => {
        i = (i + 1) % imgs.length;
        imgs.forEach((im, k) => im.classList.toggle('is-on', k === i));
        names.forEach((n, k) => n.classList.toggle('is-on', k === i));
      };
      new IntersectionObserver(([e]) => { clearInterval(t); if (e.isIntersecting) t = setInterval(step, 3200); }).observe(gen);
    }
  }

  queue();
})();
