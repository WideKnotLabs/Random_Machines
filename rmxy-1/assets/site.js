/* Random Machines site behaviour. Progressive enhancement: every page reads fine without it.
   Nothing here moves on its own: no scroll effects, no timers, no animation loops. */
(() => {
  'use strict';
  document.documentElement.classList.add('js');
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const clamp = (v, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));

  /* XY pad demonstration. A parameter starts at its Base value and moves toward its X and Y targets;
     both contributions add, then clamp, like the app's anchor model. Drag the square or tap the pad.
     On touch screens only the square captures the finger, so the page still scrolls. */
  $$('[data-xy]').forEach(module => {
    const pad = $('.xy-pad', module);
    const dot = $('.xy-pad__dot', pad);
    const inputs = { x: $('input[data-axis="x"]', pad), y: $('input[data-axis="y"]', pad) };
    const curve = (t, c) => (c === 'exp' ? t * t : c === 'log' ? Math.sqrt(t) : t);
    const format = (v, kind) => {
      if (kind === 'hz') {
        const hz = 20 * Math.pow(1000, v / 100);
        return hz >= 1000 ? `${(hz / 1000).toFixed(1)} kHz` : `${Math.round(hz)} Hz`;
      }
      return `${Math.round(v)}%`;
    };
    const rows = $$('.xy-param', module).map(el => ({
      base: +el.dataset.base,
      x: el.dataset.x === undefined ? null : +el.dataset.x,
      y: el.dataset.y === undefined ? null : +el.dataset.y,
      cx: el.dataset.cx, cy: el.dataset.cy, fmt: el.dataset.fmt,
      fill: $('.xy-param__fill', el), val: $('.xy-param__val', el),
    }));
    const set = (nx, ny) => {
      pad.style.setProperty('--px', `${(nx * 100).toFixed(2)}%`);
      pad.style.setProperty('--py', `${((1 - ny) * 100).toFixed(2)}%`);
      inputs.x.value = Math.round(nx * 100);
      inputs.y.value = Math.round(ny * 100);
      rows.forEach(r => {
        let v = r.base;
        if (r.x !== null) v += (r.x - r.base) * curve(nx, r.cx);
        if (r.y !== null) v += (r.y - r.base) * curve(ny, r.cy);
        v = clamp(v, 0, 100);
        r.fill.style.setProperty('--v', `${v}%`);
        r.val.textContent = format(v, r.fmt);
      });
    };
    const at = e => {
      const r = pad.getBoundingClientRect();
      return [clamp((e.clientX - r.left) / r.width), clamp(1 - (e.clientY - r.top) / r.height)];
    };
    let dragging = false, tap = null;
    pad.addEventListener('pointerdown', e => {
      if (e.pointerType === 'touch' && e.target !== dot) { tap = { id: e.pointerId, x: e.clientX, y: e.clientY }; return; }
      dragging = true;
      pad.setPointerCapture(e.pointerId);
      set(...at(e));
    });
    pad.addEventListener('pointermove', e => { if (dragging) set(...at(e)); });
    const end = e => {
      if (tap && tap.id === e.pointerId && e.type === 'pointerup' && Math.hypot(e.clientX - tap.x, e.clientY - tap.y) < 8) set(...at(e));
      tap = null; dragging = false;
    };
    pad.addEventListener('pointerup', end);
    pad.addEventListener('pointercancel', end);
    const fromInputs = () => set(inputs.x.value / 100, inputs.y.value / 100);
    inputs.x.addEventListener('input', fromInputs);
    inputs.y.addEventListener('input', fromInputs);
    set(0.3, 0.25);
  });

  /* Effect slots: tap to bypass. */
  $$('[data-slots] .slot').forEach(btn => {
    btn.addEventListener('click', () => btn.setAttribute('aria-pressed', String(btn.getAttribute('aria-pressed') !== 'true')));
  });

  /* Scene banks: pick one of 32. */
  $$('[data-banks]').forEach(module => {
    const cells = $$('.cell', module);
    const note = $('.bank-note', module);
    cells.forEach(cell => cell.addEventListener('click', () => {
      cells.forEach(c => c.setAttribute('aria-pressed', String(c === cell)));
      if (note) note.textContent = cell.getAttribute('aria-label');
    }));
  });

  /* Active section in document tables of contents */
  const tocLinks = $$('.toc a[href^="#"]');
  if (tocLinks.length) {
    const targets = tocLinks.map(a => document.getElementById(a.hash.slice(1))).filter(Boolean);
    let queued = false;
    const spy = () => {
      queued = false;
      const current = targets.filter(t => t.getBoundingClientRect().top < 160).pop() || targets[0];
      tocLinks.forEach(a => {
        if (a.hash === `#${current.id}`) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
      });
    };
    window.addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(spy); } }, { passive: true });
    spy();
  }

  /* Manual: contents drawer, search, scrollspy, print */
  const side = $('.manual__side');
  if (side) {
    const toggle = $('.manual-toggle');
    const search = $('#manual-search');
    const results = $('#search-results');
    const status = $('#search-status');
    const chapterList = $('.chapters', side);
    const dataEl = $('#search-data');
    const index = dataEl ? JSON.parse(dataEl.textContent) : [];
    const narrow = window.matchMedia('(max-width: 960px)');
    const setDrawer = open => {
      side.classList.toggle('is-open', open);
      document.body.classList.toggle('scroll-lock', open);
      if (toggle) toggle.setAttribute('aria-expanded', String(open));
    };
    toggle?.addEventListener('click', () => setDrawer(toggle.getAttribute('aria-expanded') !== 'true'));
    narrow.addEventListener('change', () => setDrawer(false));
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && side.classList.contains('is-open')) { setDrawer(false); toggle?.focus(); }
      if (e.key === '/' && document.activeElement !== search && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '') && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        if (narrow.matches) setDrawer(true);
        search?.focus();
      }
    });
    side.addEventListener('click', e => {
      const link = e.target.closest('a[href^="#"]');
      if (link && narrow.matches) setDrawer(false);
    });
    $('#print')?.addEventListener('click', () => window.print());

    search?.addEventListener('input', () => {
      const q = search.value.trim().toLocaleLowerCase();
      results.replaceChildren();
      results.hidden = !q;
      chapterList.hidden = !!q;
      if (!q) { status.textContent = ''; return; }
      const terms = q.split(/\s+/);
      const matches = index.filter(item => terms.every(t => `${item.title} ${item.text}`.toLocaleLowerCase().includes(t)));
      status.textContent = matches.length ? `${matches.length} matching topic${matches.length === 1 ? '' : 's'}` : 'Nothing found. Try a control or effect name.';
      matches.slice(0, 40).forEach(item => {
        const li = document.createElement('li');
        const small = document.createElement('small'); small.textContent = item.chapter;
        const a = document.createElement('a'); a.href = `#${item.id}`; a.textContent = item.title;
        const p = document.createElement('p');
        const at = item.text.toLocaleLowerCase().indexOf(terms[0]);
        const start = Math.max(0, at - 40);
        p.textContent = `${start ? '…' : ''}${item.text.slice(start, start + 140)}…`;
        li.append(small, a, p);
        results.append(li);
      });
    });

    const chapters = $$('.m-chapter');
    const lessons = $$('.m-lesson');
    let queued = false;
    const spy = () => {
      queued = false;
      const chapter = chapters.filter(el => el.getBoundingClientRect().top <= 180).pop() || chapters[0];
      if (!chapter) return;
      $$('.chapters > li').forEach(li => {
        if (li.dataset.chapter === chapter.id) li.setAttribute('data-active', ''); else li.removeAttribute('data-active');
      });
      const lesson = lessons.filter(el => el.closest('.m-chapter') === chapter && el.getBoundingClientRect().top <= 200).pop();
      $$('.subnav a').forEach(a => {
        if (lesson && a.hash === `#${lesson.id}`) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current');
      });
    };
    window.addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(spy); } }, { passive: true });
    spy();
  }
})();
