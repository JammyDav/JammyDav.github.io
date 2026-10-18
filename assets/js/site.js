/* Portfolio shell: renders content/case-studies.json, hero index, top bar dots and progress, stat count-up, launch cards, reveals. */
(function () {
  'use strict';

  var reduced = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  // Escape, then turn {{PLACEHOLDER:...}} and {{CONFIRM:...}} into visible markers.
  function rich(s) {
    return esc(s)
      .replace(/\{\{PLACEHOLDER:([^}]*)\}\}/g, '<span class="ph"><b>PLACEHOLDER</b>$1</span>')
      .replace(/\{\{CONFIRM:([^}]*)\}\}/g, '<span class="confirm">$1<sup>CONFIRM</sup></span>');
  }
  function ph(label) { return '<span class="ph"><b>PLACEHOLDER</b>' + esc(label) + '</span>'; }

  /* ---------- sections ---------- */
  function renderHero(h) {
    var links = h.links.map(function (l, i) {
      if (l.placeholder) return '<a class="btn" href="' + esc(l.href) + '">' + esc(l.label) + '</a> ' + ph(l.placeholder);
      return '<a class="btn' + (i === 0 ? ' pri' : '') + '" href="' + esc(l.href) + '">' + esc(l.label) + '</a>';
    }).join('');
    document.getElementById('hero').innerHTML =
      '<img class="hero-mark" src="assets/img/mark.svg" alt="" width="96" height="96">' +
      '<div><h1 id="hero-name">' + esc(h.name) + '</h1>' +
      '<p class="lede">' + rich(h.pitch[0]) + '</p><p class="ai-note">' + rich(h.pitch[1]) + '</p>' +
      '<ul class="chips" aria-label="Roles I am looking at">' + h.chips.map(function (c) { return '<li>' + esc(c) + '</li>'; }).join('') + '</ul>' +
      '<div class="hero-links">' + links + '</div></div>';
  }

  // Five cards under the intro: what each build is and its standout number, linking to it.
  function renderIndex(cases) {
    document.getElementById('hero-index').innerHTML =
      '<h2 class="ix-head" id="ix-head">The ' + (['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'][cases.length] || cases.length) + ' builds</h2><ol class="index" aria-labelledby="ix-head">' + cases.map(function (cs, i) {
        return '<li><a class="ix" href="#' + esc(cs.id) + '">' +
          '<img src="' + esc(cs.panel.thumb) + '" alt="" width="480" height="' + Math.round(480 * cs.panel.previewSize[1] / cs.panel.previewSize[0]) + '" decoding="async">' +
          '<span class="ix-n" aria-hidden="true">0' + (i + 1) + '</span><span class="ix-t">' + esc(cs.short) + '</span>' +
          '<span class="ix-h">' + esc(cs.headline) + '</span></a></li>';
      }).join('') + '</ol>';
  }

  function statValue(s) {
    var pre = (s.approx ? '~' : '') + (s.prefix || '');
    var sup = s.confirm ? '<sup>CONFIRM</sup>' : '';
    if (s.text) return '<span class="v' + (s.confirm ? ' confirm' : '') + '">' + esc(s.text) + sup + '</span>';
    var final = pre + s.value.toLocaleString('en-GB') + (s.suffix || '');
    return '<span class="v' + (s.confirm ? ' confirm' : '') + '" data-count="' + s.value + '" data-pre="' + esc(pre) + '" data-suf="' + esc(s.suffix || '') + '">' +
      '<span class="sr">' + esc(final) + '</span><span aria-hidden="true" class="num">' + esc(final) + '</span>' + sup + '</span>';
  }

  function renderPanel(cs) {
    var p = cs.panel, badge = p.type === 'live' ? '<span class="badge live">Live demo</span>' : '<span class="badge visual">Visual</span>';
    var alt = '<details><summary>What this ' + (p.type === 'live' ? 'demo' : 'visual') + ' shows</summary><p>' + rich(p.alt) + '</p></details>';
    if (p.status !== 'ready') {
      return '<div class="panel"><div class="panel-head">' + badge + '<h3>' + esc(p.title) + '</h3></div>' +
        '<div class="ph-box" role="note"><b>PLACEHOLDER</b><span>' + esc(p.placeholder) + '</span></div>' + alt + '</div>';
    }
    // Launch card: a looping preview (a still under reduced motion) until the visitor launches the real demo.
    var size = p.aspect ? 'aspect-ratio:' + p.aspect : 'height:' + p.height + 'px';
    var img = reduced ? p.poster : p.preview, wh = reduced ? p.posterSize : p.previewSize;
    var launch = '<div class="launch" style="aspect-ratio:' + wh[0] + ' / ' + wh[1] + '">' +
      '<img src="' + esc(img) + '" data-fallback="' + esc(p.poster) + '" alt="' + (reduced ? 'Still' : 'Looping preview') + ' of the ' + esc(cs.short) + ' demo" width="' + wh[0] + '" height="' + wh[1] + '" loading="lazy" decoding="async">' +
      '<button type="button" class="launch-btn" data-src="' + esc(p.src) + '" data-size="' + esc(size) + '" data-title="' + esc(p.title) + '"' + (p.allow ? ' data-allow="' + esc(p.allow) + '"' : '') + '>' +
      '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M7 4.5v15l12-7.5z" fill="currentColor"/></svg>Launch live demo</button></div>';
    return '<div class="panel"><div class="panel-head">' + badge + '<h3>' + esc(p.title) + '</h3>' +
      '<a class="fs" href="' + esc(p.src) + '" target="_blank" rel="noopener">Open full screen<span class="sr"> (new tab)</span> &#8599;</a></div>' +
      launch + (p.note ? '<p class="note">' + rich(p.note) + '</p>' : '') + alt + '</div>';
  }

  function renderCase(cs, i, n) {
    return '<section class="cs" id="' + esc(cs.id) + '" aria-labelledby="' + esc(cs.id) + '-title"><div class="wrap">' +
      '<header class="cs-head rv"><div class="kicker">Case study ' + (i + 1) + ' of ' + n + '</div>' +
      '<h2 id="' + esc(cs.id) + '-title">' + rich(cs.title) + '</h2><p class="summary">' + rich(cs.summary) + '</p></header>' +
      '<ul class="stats rv" aria-label="Outcome in numbers">' + cs.stats.map(function (s) { return '<li>' + statValue(s) + '<span class="l">' + rich(s.label) + '</span></li>'; }).join('') + '</ul>' +
      '<div class="rv">' + renderPanel(cs) + '</div>' +
      '</div></section>';
  }

  function renderContact(c) {
    document.getElementById('contact-in').innerHTML =
      '<div class="kicker">Get in touch</div><h2 id="contact-title">' + esc(c.title) + '</h2><p class="intro">' + rich(c.intro) + '</p>' +
      '<ul class="contact-list">' +
      '<li><a class="btn pri" href="mailto:' + esc(c.email) + '">' + esc(c.email) + '</a></li>' +
      '<li><a class="btn" href="' + esc(c.cv) + '">Download CV (PDF)</a></li>' +
      '<li><a class="btn" href="' + esc(c.linkedin) + '" rel="me noopener">LinkedIn</a></li></ul>' +
      '<p class="contact-meta">' + rich(c.location) + '</p>';
  }

  /* ---------- behaviour ---------- */
  function topbar(cases) {
    var bar = document.getElementById('topbar'), hero = document.getElementById('top'), progress = document.getElementById('progress');
    document.getElementById('dots').innerHTML = cases.map(function (cs, i) {
      return '<li><a href="#' + esc(cs.id) + '" title="' + esc(cs.short) + '"><span class="lbl">Case study ' + (i + 1) + ': ' + esc(cs.short) + '</span></a></li>';
    }).join('');
    var links = [].slice.call(document.querySelectorAll('#dots a'));
    var secs = cases.map(function (cs) { return document.getElementById(cs.id); });
    var ticking = false;
    function update() {
      ticking = false;
      var heroGone = hero.getBoundingClientRect().bottom < 0;
      var room = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.transform = 'scaleX(' + (room > 0 ? Math.min(1, window.scrollY / room) : 0) + ')';
      bar.classList.toggle('on', heroGone);
      bar.inert = !heroGone;   // off-screen bar: out of the tab order and the accessibility tree
      var mid = window.innerHeight * 0.4, cur = -1;
      secs.forEach(function (s, i) { if (s.getBoundingClientRect().top < mid) cur = i; });
      var last = secs[secs.length - 1].getBoundingClientRect();
      if (last.bottom < mid) cur = secs.length; // past the case studies: all filled
      links.forEach(function (a, i) {
        a.classList.toggle('passed', i < cur);
        if (i === cur) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
      });
    }
    window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  function countUps() {
    var els = [].slice.call(document.querySelectorAll('.stats .v[data-count]'));
    if (reduced || !('IntersectionObserver' in window)) return; // final values are already in place
    function fmt(el, v) { return el.getAttribute('data-pre') + Math.round(v).toLocaleString('en-GB') + el.getAttribute('data-suf'); }
    els.forEach(function (el) { el.querySelector('.num').textContent = fmt(el, 0); });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        var el = e.target, to = +el.getAttribute('data-count'), t0 = performance.now(), dur = 900, num = el.querySelector('.num');
        (function step(now) {
          var p = Math.min(1, (now - t0) / dur), k = 1 - Math.pow(1 - p, 3);
          num.textContent = fmt(el, to * k);
          if (p < 1) requestAnimationFrame(step);
        })(t0);
      });
    }, { threshold: 0.6 });
    els.forEach(function (el) { io.observe(el); });
  }

  // Launch: swap the preview for the live demo. On small screens the demos open full screen instead.
  function launchers() {
    document.getElementById('case-studies').addEventListener('click', function (e) {
      var b = e.target.closest('.launch-btn');
      if (!b) return;
      var src = b.getAttribute('data-src');
      if (window.innerWidth < 700) { window.open(src, '_blank', 'noopener'); return; }
      var frame = document.createElement('div');
      frame.className = 'frame';
      frame.style.cssText = b.getAttribute('data-size');
      var allow = b.getAttribute('data-allow');
      frame.innerHTML = '<iframe src="' + esc(src) + '" title="' + esc(b.getAttribute('data-title')) + ' (live demo, synthetic data)"' + (allow ? ' allow="' + esc(allow) + '"' : '') + '></iframe>';
      b.closest('.launch').replaceWith(frame);
      var f = frame.querySelector('iframe');
      f.addEventListener('load', function () { f.focus(); }, { once: true });
    });
    // A preview that fails to load falls back to the still poster.
    [].slice.call(document.querySelectorAll('.launch img')).forEach(function (img) {
      img.addEventListener('error', function () { img.src = img.getAttribute('data-fallback'); }, { once: true });
    });
  }

  // Sections ease in as they arrive. Skipped entirely under reduced motion.
  function reveals() {
    if (reduced || !('IntersectionObserver' in window)) return;
    document.documentElement.classList.add('motion');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    var els = [].slice.call(document.querySelectorAll('.rv'));
    els.forEach(function (el) { io.observe(el); });
    // Safety net: anything already scrolled past (a jump link, a fast flick) is shown, never left hidden.
    var t = null;
    function sweep() { els.forEach(function (el) { if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add('in'); }); }
    window.addEventListener('scroll', function () { clearTimeout(t); t = setTimeout(sweep, 150); }, { passive: true });
    window.addEventListener('hashchange', function () { setTimeout(sweep, 50); });
    setTimeout(sweep, 1200);
  }

  function render(data) {
    renderHero(data.hero);
    renderIndex(data.caseStudies);
    var n = data.caseStudies.length;
    document.getElementById('case-studies').innerHTML = data.caseStudies.map(function (cs, i) { return renderCase(cs, i, n); }).join('');
    renderContact(data.contact);
    topbar(data.caseStudies);
    countUps();
    launchers();
    reveals();
    if (location.hash) { var t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView({ behavior: 'instant' }); }
  }

  function fallback() {
    document.getElementById('load-error').hidden = false;
    var ns = document.getElementById('static-copy');
    if (ns) document.getElementById('fallback').innerHTML = ns.textContent;
  }

  fetch('content/case-studies.json', { cache: 'no-cache' })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(render)
    .catch(function (e) { console.error('Could not load content/case-studies.json', e); fallback(); });
})();
