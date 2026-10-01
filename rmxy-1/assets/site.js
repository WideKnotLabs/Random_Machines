/* Random Machines site behaviour: document contents and the manual. Progressive enhancement: every page reads fine without it.
   The landing page's live demonstrations are in landing.js. */
(() => {
  'use strict';
  document.documentElement.classList.add('js');
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];

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
