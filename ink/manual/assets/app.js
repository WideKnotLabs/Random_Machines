/* INK guide: theme switch, drawer, search, scroll-spy. No dependencies. */
(function () {
  var root = document.documentElement;
  var KEY = 'ink-guide-theme';

  function setTheme(t, save) {
    root.setAttribute('data-theme', t);
    if (save) { try { localStorage.setItem(KEY, t); } catch (e) {} }
    var btns = document.querySelectorAll('.th');
    for (var i = 0; i < btns.length; i++) btns[i].setAttribute('aria-pressed', btns[i].dataset.th === t ? 'true' : 'false');
    var imgs = document.querySelectorAll('img[data-paper],img[data-dark],img[data-blue],img[data-loop]');
    for (var j = 0; j < imgs.length; j++) {
      var im = imgs[j], want = im.dataset[t] || im.dataset.base || im.getAttribute('src');
      if (!im.dataset.base) im.dataset.base = im.getAttribute('src');
      if (im.getAttribute('src') !== want) im.setAttribute('src', want);
      if (im.hasAttribute('data-loop')) syncLoop(im, t);
    }
  }

  /* loops (make_loops.py): an animated figure in a <picture> whose <source> gives the still poster to readers who asked
     for less motion. For them a Play button (or a tap on the picture) plays it here; the theme picks loop and poster. */
  var lessMotion = window.matchMedia ? matchMedia('(prefers-reduced-motion: reduce)') : null;
  function themeNow() { return root.getAttribute('data-theme') || 'paper'; }
  function posterOf(im, t) { return im.dataset['poster' + t.charAt(0).toUpperCase() + t.slice(1)] || im.dataset.posterPaper || ''; }
  function syncLoop(im, t) {
    var pic = im.parentNode, src = pic && pic.tagName === 'PICTURE' ? pic.querySelector('source') : null;
    if (!src) return;
    var want = pic.classList.contains('playing') ? (im.dataset[t] || im.dataset.base || im.getAttribute('src')) : posterOf(im, t);
    if (src.getAttribute('srcset') !== want) src.setAttribute('srcset', want);
  }
  function setPlaying(pic, on) {
    pic.classList.toggle('playing', on);
    var b = pic.parentNode && pic.parentNode.querySelector('.loop-play');
    if (b) { b.textContent = on ? 'Pause' : 'Play'; b.setAttribute('aria-pressed', on ? 'true' : 'false'); }
    var im = pic.querySelector('img'); if (im) syncLoop(im, themeNow());
  }
  function loopButtons() {
    var pics = document.querySelectorAll('picture.loop');
    for (var i = 0; i < pics.length; i++) {
      var pic = pics[i], box = pic.parentNode, b = box.querySelector('.loop-play');
      if (lessMotion && lessMotion.matches) {
        if (!b && !box.closest('#lb') && !box.closest('.qstrip')) {   /* strip tiles are links: their poster stays */
          b = document.createElement('button'); b.type = 'button'; b.className = 'loop-play';
          b.setAttribute('aria-label', 'Play the animation'); box.appendChild(b);
        }
        setPlaying(pic, pic.classList.contains('playing'));
      } else {
        if (b) b.remove();
        pic.classList.remove('playing');
      }
    }
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.loop-play');
    var shot = !b && e.target.closest && e.target.closest('.shot');
    var pic = b ? b.parentNode.querySelector('picture.loop') : shot ? shot.querySelector('picture.loop') : null;
    if (!pic || !(lessMotion && lessMotion.matches)) return;
    if (b || !pic.classList.contains('playing')) {   /* a paused loop plays on a tap; once playing, a tap enlarges it */
      e.preventDefault(); e.stopImmediatePropagation();
      setPlaying(pic, !pic.classList.contains('playing'));
    }
  }, true);
  if (lessMotion) { if (lessMotion.addEventListener) lessMotion.addEventListener('change', loopButtons); else if (lessMotion.addListener) lessMotion.addListener(loopButtons); }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.th');
    if (!b) return;
    var t = b.dataset.th;
    if (b.getAttribute('aria-pressed') === 'true' && window.matchMedia && matchMedia('(max-width:640px)').matches) {   /* one theme button on phones: tap = next */
      var order = ['paper', 'dark', 'blue']; t = order[(order.indexOf(t) + 1) % order.length];
    }
    setTheme(t, true);
  });
  setTheme(root.getAttribute('data-theme') || 'paper', false);
  loopButtons();

  /* print always uses Paper (colours and picture variants), then puts the reader's theme back */
  var beforePrint = null;
  window.addEventListener('beforeprint', function () {
    if (beforePrint === null) { beforePrint = root.getAttribute('data-theme') || 'paper'; setTheme('paper', false); }
  });
  window.addEventListener('afterprint', function () {
    if (beforePrint !== null) { setTheme(beforePrint, false); beforePrint = null; }
  });

  /* drawer on narrow screens */
  var burger = document.getElementById('burger');
  function nav(open) {
    document.body.classList.toggle('nav-open', open);
    if (burger) burger.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  if (burger) burger.addEventListener('click', function () { nav(!document.body.classList.contains('nav-open')); });
  var scrim = document.getElementById('scrim');
  if (scrim) scrim.addEventListener('click', function () { nav(false); });
  var mpill = document.getElementById('mpill');
  if (mpill) mpill.addEventListener('click', function () { nav(true); var on = document.querySelector('.part li.on'); if (on && on.scrollIntoView) on.scrollIntoView({ block: 'center' }); });
  var side = document.getElementById('side');
  if (side) side.addEventListener('click', function (e) { if (e.target.closest('.toc a')) nav(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { nav(false); hideRes(); if (q && document.activeElement === q) q.blur(); } });

  /* chapters read so far (kept in this browser only) */
  var seen = [];
  try { seen = JSON.parse(localStorage.getItem('ink-guide-seen') || '[]'); } catch (e) { seen = []; }
  var curLi = document.querySelector('.part li.on');
  if (curLi && curLi.dataset.slug && seen.indexOf(curLi.dataset.slug) < 0) {
    seen.push(curLi.dataset.slug);
    try { localStorage.setItem('ink-guide-seen', JSON.stringify(seen)); } catch (e) {}
  }
  var marked = document.querySelectorAll('li[data-slug]');
  for (var m = 0; m < marked.length; m++) if (seen.indexOf(marked[m].dataset.slug) >= 0) marked[m].classList.add('seen');

  /* reading progress and back to top */
  var prog = document.querySelector('#prog i'), totop = document.getElementById('totop'), tick = false;
  function onScroll() {
    tick = false;
    var h = document.documentElement, max = h.scrollHeight - h.clientHeight, y = window.pageYOffset || h.scrollTop;
    if (prog) prog.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, y / max) : 0) + ')';
    if (totop) totop.hidden = y < 700;
  }
  window.addEventListener('scroll', function () { if (!tick) { tick = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();
  if (totop) totop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });

  /* picture viewer: click or tap a figure; click the picture to switch between fit and full size */
  var lb = document.getElementById('lb'), lbBox = document.getElementById('lb-box'), lbCap = document.getElementById('lb-cap'),
      lbZoom = document.getElementById('lb-zoom'), lastFocus = null;
  function closeLb() {
    if (!lb || lb.hidden) return;
    lb.hidden = true; lb.classList.remove('full'); lbBox.innerHTML = ''; document.body.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function openLb(shot) {
    if (!lb) return;
    lastFocus = shot;
    var c = shot.cloneNode(true);
    c.removeAttribute('data-zoom'); c.removeAttribute('tabindex'); c.removeAttribute('role'); c.removeAttribute('aria-label');
    var im = c.querySelector('img'); if (im) im.removeAttribute('loading');
    var cp = c.querySelectorAll('.ck-pin,.loop-play'); for (var q = 0; q < cp.length; q++) cp[q].remove();
    lbBox.innerHTML = ''; lbBox.appendChild(c); lbBox.scrollTop = 0;
    var fig = shot.closest('figure'), cap = fig && fig.querySelector('.cap');
    lbCap.textContent = cap ? cap.textContent : '';
    lb.classList.remove('full'); lbZoom.textContent = 'Full size';
    lb.hidden = false; document.body.style.overflow = 'hidden'; sizeLb(); lbZoom.focus();
  }
  function sizeLb() { if (lb && !lb.hidden) lbBox.style.setProperty('--lbh', Math.max(200, lbBox.clientHeight - 18) + 'px'); }
  window.addEventListener('resize', sizeLb);
  function toggleFull() { var f = lb.classList.toggle('full'); lbZoom.textContent = f ? 'Fit screen' : 'Full size'; }
  document.addEventListener('click', function (e) {
    var sh = e.target.closest && e.target.closest('.shot[data-zoom]');
    if (sh && !sh.closest('#lb')) { openLb(sh); return; }
    if (e.target.closest && e.target.closest('#lb-x')) { closeLb(); return; }
    if (e.target.closest && e.target.closest('#lb-zoom')) { toggleFull(); return; }
    if (lb && !lb.hidden && e.target.closest && e.target.closest('#lb .shot')) { toggleFull(); return; }
    if (lb && !lb.hidden && e.target === lbBox) closeLb();
  });
  document.addEventListener('keydown', function (e) {
    if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('.shot[data-zoom]')) { e.preventDefault(); openLb(e.target); }
    else if (e.key === 'Escape') closeLb();
  });

  /* search */
  var q = document.getElementById('q'), res = document.getElementById('res');
  function hideRes() { if (res) res.hidden = true; }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function mark(s, words) {
    s = esc(s);
    words.forEach(function (w) { if (w) s = s.replace(new RegExp('(' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig'), '<mark>$1</mark>'); });
    return s;
  }
  function snippet(t, words) {
    var low = t.toLowerCase(), at = -1;
    for (var i = 0; i < words.length && at < 0; i++) at = low.indexOf(words[i]);
    var a = Math.max(0, at - 50), s = t.substr(a, 150);
    return (a > 0 ? '… ' : '') + s + (a + 150 < t.length ? ' …' : '');
  }
  function run() {
    var raw = q.value.trim().toLowerCase();
    if (raw.length < 2 || !window.INK_INDEX) { hideRes(); return; }
    var words = raw.split(/\s+/);
    var hits = [];
    window.INK_INDEX.forEach(function (e) {
      var h = (e.h || '').toLowerCase(), c = (e.c || '').toLowerCase(), t = (e.t || '').toLowerCase(), score = 0;
      for (var i = 0; i < words.length; i++) {
        var w = words[i], s = 0;
        if (h.indexOf(w) >= 0) s += 6;
        if (c.indexOf(w) >= 0) s += 2;
        var k = t.indexOf(w);
        if (k >= 0) { s += 1; var n = 0; while (k >= 0 && n < 5) { n++; k = t.indexOf(w, k + 1); } s += n * 0.2; }
        if (!s) { score = 0; break; }
        score += s;
      }
      if (score) hits.push([score, e]);
    });
    hits.sort(function (a, b) { return b[0] - a[0]; });
    hits = hits.slice(0, 10);
    res.innerHTML = hits.length ? hits.map(function (x) {
      var e = x[1];
      return '<a href="' + esc(e.u) + '"><b>' + mark(e.h || e.c, words) + '</b><small>' + esc(e.c) + ' · ' + mark(snippet(e.t, words), words) + '</small></a>';
    }).join('') : '<div class="none">Nothing found for "' + esc(raw) + '".</div>';
    res.hidden = false;
  }
  if (q) {
    q.addEventListener('input', run);
    q.addEventListener('focus', run);
    q.addEventListener('keydown', function (e) {
      var links = res.querySelectorAll('a'), cur = res.querySelector('a.sel'), i = Array.prototype.indexOf.call(links, cur);
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (!links.length) return;
        i = e.key === 'ArrowDown' ? Math.min(links.length - 1, i + 1) : Math.max(0, i - 1);
        if (cur) cur.classList.remove('sel');
        links[i].classList.add('sel');
        links[i].scrollIntoView({ block: 'nearest' });
      } else if (e.key === 'Enter') {
        var t = cur || links[0];
        if (t) window.location.href = t.getAttribute('href');
      }
    });
    document.addEventListener('click', function (e) { if (!e.target.closest('.search')) hideRes(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === '/' && document.activeElement !== q && !/input|textarea/i.test((document.activeElement || {}).tagName || '')) { e.preventDefault(); q.focus(); }
    });
  }

  /* scroll-spy for the page's own section list */
  var tocLinks = document.querySelectorAll('.toc a');
  if (tocLinks.length && 'IntersectionObserver' in window) {
    var map = {};
    for (var i = 0; i < tocLinks.length; i++) map[tocLinks[i].getAttribute('href').slice(1)] = tocLinks[i];
    var io = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) {
        if (en.isIntersecting) {
          for (var k in map) map[k].classList.remove('cur');
          var l = map[en.target.id];
          if (l) l.classList.add('cur');
        }
      });
    }, { rootMargin: '-60px 0px -70% 0px' });
    for (var id in map) { var h = document.getElementById(id); if (h) io.observe(h); }
  }
})();
