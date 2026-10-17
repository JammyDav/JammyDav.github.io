/* Portfolio shell: renders content/case-studies.json, top bar dots, stat count-up, demo panels. */
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
  function paras(list) { return (list || []).map(function (p) { return '<p>' + rich(p) + '</p>'; }).join(''); }
  function ph(label) { return '<span class="ph"><b>PLACEHOLDER</b>' + esc(label) + '</span>'; }

  var ICONS = {
    doc: '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',
    flow: '<rect x="3" y="4" width="6" height="5" rx="1"/><rect x="15" y="4" width="6" height="5" rx="1"/><rect x="9" y="15" width="6" height="5" rx="1"/><path d="M9 6.5h6M18 9v3H12v3"/>',
    leaf: '<path d="M5 19c0-8 5-14 15-14 0 10-6 15-14 15"/><path d="M5 19l7-7"/>',
    phone: '<rect x="7" y="2.5" width="10" height="19" rx="2"/><path d="M11 18.5h2M10 8l1.5 1.5L14 7"/>',
    stack: '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/><path d="M3 17.5l9 5 9-5"/>',
    play: '<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M10 8.5v5l4.5-2.5z"/><path d="M8 21h8"/>'
  };
  function icon(k) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICONS[k] || '') + '</svg>';
  }

  /* ---------- sections ---------- */
  function renderHero(h) {
    var links = h.links.map(function (l, i) {
      if (l.placeholder) return '<a class="btn" href="' + esc(l.href) + '">' + esc(l.label) + '</a> ' + ph(l.placeholder);
      return '<a class="btn' + (i === 0 ? ' pri' : '') + '" href="' + esc(l.href) + '">' + esc(l.label) + '</a>';
    }).join('');
    document.getElementById('hero').innerHTML =
      '<img class="hero-mark" src="assets/img/mark.svg" alt="" width="96" height="96">' +
      '<div><h1 id="hero-name">' + esc(h.name) + '</h1>' +
      '<p class="lede">' + rich(h.pitch[0]) + '</p><p class="sub">' + rich(h.pitch[1]) + '</p>' +
      (h.proof ? '<p class="proof">' + rich(h.proof) + '</p>' : '') +
      '<ul class="chips" aria-label="Roles I am looking at">' + h.chips.map(function (c) { return '<li>' + esc(c) + '</li>'; }).join('') + '</ul>' +
      '<div class="hero-links">' + links + '</div>' +
      '<a class="scroll-cue" href="#pattern"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M12 4v15M5 13l7 7 7-7"/></svg>Five case studies, each with a live demo</a></div>';
  }

  function renderPattern(p) {
    document.getElementById('pattern-in').innerHTML =
      '<div class="kicker">The through-line</div><h2 id="pattern-title">' + esc(p.title) + '</h2><p class="intro">' + rich(p.intro) + '</p>' +
      '<ol class="pattern-steps">' + p.steps.map(function (s) { return '<li><h3>' + esc(s.title) + '</h3><p>' + rich(s.text) + '</p></li>'; }).join('') + '</ol>';
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
      return '<div class="panel"><div class="panel-head">' + badge + '<h4>' + esc(p.title) + '</h4></div>' +
        '<div class="ph-box" role="note"><b>PLACEHOLDER</b><span>' + esc(p.placeholder) + '</span></div>' + alt + '</div>';
    }
    var size = p.aspect ? 'aspect-ratio:' + p.aspect : 'height:' + p.height + 'px';
    var strip = p.strip ? '<ol class="strip" aria-label="Three generations">' + p.strip.map(function (g) { return '<li><b>' + esc(g.title) + '</b>' + esc(g.text) + '</li>'; }).join('') + '</ol>' : '';
    var poster = '<a class="poster" href="' + esc(p.src) + '" target="_blank" rel="noopener">' +
      '<img src="' + esc(p.poster) + '" alt="Preview of the ' + esc(cs.short) + ' demo" width="' + p.posterSize[0] + '" height="' + p.posterSize[1] + '" loading="lazy" decoding="async">' +
      '<span>Open the demo full screen</span></a>';
    return '<div class="panel small-poster"><div class="panel-head">' + badge + '<h4>' + esc(p.title) + '</h4>' +
      '<a class="fs" href="' + esc(p.src) + '" target="_blank" rel="noopener">Open full screen<span class="sr"> (new tab)</span> &#8599;</a></div>' + strip +
      '<div class="frame" style="' + size + '"><iframe src="' + esc(p.src) + '" title="' + esc(p.title) + ' (live demo, synthetic data)" loading="lazy"></iframe></div>' +
      poster + (p.note ? '<p class="note">' + rich(p.note) + '</p>' : '') + alt + '</div>';
  }

  function renderCase(cs, i, n) {
    var prose =
      '<h3>Context</h3>' + paras(cs.context) +
      '<h3>What I built</h3>' + paras(cs.built) +
      '<h3>How</h3>' + paras(cs.how) +
      '<h3>Outcome</h3><ul>' + cs.outcome.map(function (o) { return '<li>' + rich(o) + '</li>'; }).join('') + '</ul>';
    return '<section class="cs" id="' + esc(cs.id) + '" aria-labelledby="' + esc(cs.id) + '-title"><div class="wrap">' +
      '<header class="cs-head"><div class="kicker">Case study ' + (i + 1) + ' of ' + n + '</div>' +
      '<h2 id="' + esc(cs.id) + '-title">' + rich(cs.title) + '</h2><p class="pitch">' + rich(cs.pitch) + '</p></header>' +
      '<ul class="stats" aria-label="Outcome in numbers">' + cs.stats.map(function (s) { return '<li>' + statValue(s) + '<span class="l">' + rich(s.label) + '</span></li>'; }).join('') + '</ul>' +
      '<div class="cs-grid"><div class="cs-prose">' + prose + '</div><div class="cs-side">' + renderPanel(cs) + '</div></div>' +
      '</div></section>';
  }

  function renderAlso(a) {
    document.getElementById('also-in').innerHTML =
      '<div class="kicker">Range</div><h2 id="also-title">' + esc(a.title) + '</h2><p class="intro">' + rich(a.intro) + '</p>' +
      '<ul class="tiles">' + a.tiles.map(function (t) { return '<li>' + icon(t.icon) + '<h3>' + esc(t.title) + '</h3><p>' + rich(t.text) + '</p></li>'; }).join('') + '</ul>';
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
    var bar = document.getElementById('topbar'), hero = document.getElementById('top');
    document.getElementById('dots').innerHTML = cases.map(function (cs, i) {
      return '<li><a href="#' + esc(cs.id) + '" title="' + esc(cs.short) + '"><span class="lbl">Case study ' + (i + 1) + ': ' + esc(cs.short) + '</span></a></li>';
    }).join('');
    var links = [].slice.call(document.querySelectorAll('#dots a'));
    var secs = cases.map(function (cs) { return document.getElementById(cs.id); });
    var ticking = false;
    function update() {
      ticking = false;
      var heroGone = hero.getBoundingClientRect().bottom < 0;
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

  // A poster that has not been made yet becomes a visible placeholder, not a broken image.
  function posterFallbacks() {
    [].slice.call(document.querySelectorAll('.poster img')).forEach(function (img) {
      img.addEventListener('error', function () {
        var a = img.parentNode;
        a.innerHTML = '<div class="ph-box" style="min-height:160px"><b>PLACEHOLDER</b><span>Small-screen preview image not made yet. Tap to open the demo full screen.</span></div>';
      });
    });
  }

  function render(data) {
    renderHero(data.hero);
    renderPattern(data.pattern);
    var n = data.caseStudies.length;
    document.getElementById('case-studies').innerHTML = data.caseStudies.map(function (cs, i) { return renderCase(cs, i, n); }).join('');
    renderAlso(data.alsoBuilt);
    renderContact(data.contact);
    topbar(data.caseStudies);
    countUps();
    posterFallbacks();
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
