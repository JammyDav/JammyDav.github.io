/* Skills matrix demo: heatmap, three filters, gap and trainer toggles, engineer detail. Synthetic data only. */
(function () {
  'use strict';

  var D, byId = {}, siteName = {}, clsById = {};
  var S = { site: 'all', cls: 'all', level: 0, gap: false, train: false };
  var $ = function (id) { return document.getElementById(id); };

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function lv(e, cid) { return e.skills[cid] || [0, 0]; }
  function levelLabel(n) { return D.meta.levels[n].label; }

  /* ---------- state <-> hash, so a filtered view can be linked ---------- */
  function readHash() {
    location.hash.replace(/^#/, '').split('&').forEach(function (kv) {
      var p = kv.split('='), k = p[0], v = decodeURIComponent(p[1] || '');
      if (k === 'site' || k === 'cls') S[k] = v || 'all';
      else if (k === 'level') S.level = +v || 0;
      else if (k === 'gap' || k === 'train') S[k] = v === '1';
    });
    if (S.site !== 'all' && !siteName[S.site]) S.site = 'all';
    if (S.cls !== 'all' && !clsById[S.cls]) S.cls = 'all';
  }
  function writeHash() {
    var parts = [];
    if (S.site !== 'all') parts.push('site=' + S.site);
    if (S.cls !== 'all') parts.push('cls=' + S.cls);
    if (S.level) parts.push('level=' + S.level);
    if (S.gap) parts.push('gap=1');
    if (S.train) parts.push('train=1');
    history.replaceState(null, '', parts.length ? '#' + parts.join('&') : location.pathname + location.search);
  }

  /* ---------- derived views ---------- */
  function team() { return D.engineers.filter(function (e) { return S.site === 'all' || e.site === S.site; }); }
  function visibleClasses() { return S.cls === 'all' ? D.classes : [clsById[S.cls]]; }
  function rows(t) {
    var list = t.filter(function (e) {
      if (!S.level) return true;
      if (S.cls !== 'all') return lv(e, S.cls)[0] >= S.level;
      return D.classes.some(function (c) { return lv(e, c.id)[0] >= S.level; });
    });
    if (S.cls !== 'all') list.sort(function (a, b) { return lv(b, S.cls)[0] - lv(a, S.cls)[0] || a.name.localeCompare(b.name); });
    return list;
  }
  // Competent = validated level at or above competent_min. Pending self-assessments do not count.
  function competentCount(t, cid) {
    return t.filter(function (e) { var x = lv(e, cid); return x[0] >= D.meta.competent_min && x[1]; }).length;
  }
  function trainers(t, cid) {
    return t.filter(function (e) { var x = lv(e, cid); return x[0] >= D.meta.trainer_level && x[1]; });
  }

  /* ---------- rendering ---------- */
  function render() {
    var t0 = performance.now();
    var t = team(), cls = visibleClasses(), list = rows(t);
    var counts = {}, gaps = {};
    cls.forEach(function (c) { counts[c.id] = competentCount(t, c.id); gaps[c.id] = counts[c.id] < D.meta.gap_threshold; });
    var nGaps = cls.filter(function (c) { return gaps[c.id]; }).length;
    var where = S.site === 'all' ? 'all sites' : siteName[S.site];

    $('summary').innerHTML =
      '<span><b>' + list.length + '</b> of ' + t.length + ' engineers at ' + esc(where) + '</span>' +
      '<span class="gapn"><b>' + nGaps + '</b> ' + (nGaps === 1 ? 'class has' : 'classes have') + ' fewer than ' + D.meta.gap_threshold + ' competent engineers' +
      (S.site === 'all' && !nGaps ? ' (pick a site: gaps are local)' : '') + '</span>' +
      '<span class="legend" aria-hidden="true">' + D.meta.levels.map(function (l) { return '<span><i class="c l' + l.n + '" style="background:var(--l' + l.n + ')"></i>' + l.n + ' ' + esc(l.label) + '</span>'; }).join('') +
      '<span><i style="background:repeating-linear-gradient(135deg,#9fd1cb 0 3px,#fff 3px 6px)"></i>Pending validation</span></span>';

    $('main').innerHTML = S.train ? trainerView(t, cls, gaps) : grid(list, cls, counts, gaps);
    if (!S.train) wireGrid();
    console.debug('skills-matrix render ' + (performance.now() - t0).toFixed(1) + ' ms');
  }

  function grid(list, cls, counts, gaps) {
    if (!list.length) return '<div class="scroller"><p class="empty">No engineers match these filters.</p></div>';
    var gapOn = S.gap;
    var head = '<tr><th class="corner" scope="col">Engineer</th>' + cls.map(function (c) {
      var g = gapOn && gaps[c.id];
      return '<th scope="col" class="' + (g ? 'gapcol' : '') + '" title="' + esc(c.name) + '">' + esc(c.short) +
        (g ? '<span class="gapflag">GAP</span>' : '') + '</th>';
    }).join('') + '</tr>';
    var body = list.map(function (e, r) {
      return '<tr><th scope="row" class="rowh"><button type="button" data-eng="' + e.id + '" data-r="' + r + '" data-c="-1" tabindex="-1">' +
        '<span class="nm">' + esc(e.name) + '</span><span class="sub">' + esc(siteName[e.site]) + ' · ' + esc(e.role) + '</span></button></th>' +
        cls.map(function (c, ci) {
          var x = lv(e, c.id), g = gapOn && gaps[c.id];
          var label = e.name + ', ' + c.name + ': ' + (x[0] ? x[0] + ' ' + levelLabel(x[0]) + (x[1] ? '' : ', pending validation') : 'not assessed');
          return '<td class="' + (g ? 'gapcol' : '') + '" tabindex="-1" data-eng="' + e.id + '" data-r="' + r + '" data-c="' + ci + '" aria-label="' + esc(label) + '">' +
            '<div class="c l' + x[0] + (x[0] && !x[1] ? ' pending' : '') + (gapOn && !g ? ' dim' : '') + '" aria-hidden="true">' + (x[0] || '·') + '</div></td>';
        }).join('') + '</tr>';
    }).join('');
    var foot = '<tr><th scope="row">Competent (validated)</th>' + cls.map(function (c) {
      return '<td class="' + (counts[c.id] < D.meta.gap_threshold ? 'low' : '') + '">' + counts[c.id] + '</td>';
    }).join('') + '</tr>';
    return '<div class="scroller" id="scroller"><table role="grid" aria-label="Skills matrix: engineers by equipment class" aria-rowcount="' + (list.length + 1) + '">' +
      '<thead>' + head + '</thead><tbody>' + body + '</tbody><tfoot>' + foot + '</tfoot></table></div>' +
      '<p class="sr">Use the arrow keys to move between cells. Press Enter to open an engineer.</p>';
  }

  function trainerView(t, cls, gaps) {
    return '<div class="trainers">' + cls.map(function (c) {
      var tr = trainers(t, c.id), g = S.gap && gaps[c.id];
      return '<section class="tcard' + (g ? ' gapcol' : '') + '" aria-label="' + esc(c.name) + '"><h2>' + esc(c.name) + '<span>' + tr.length + ' ' + (tr.length === 1 ? 'trainer' : 'trainers') + (g ? ' · GAP' : '') + '</span></h2>' +
        (tr.length ? '<ul>' + tr.map(function (e) { return '<li><button type="button" data-open="' + e.id + '">' + esc(e.name) + ' <span class="sub" style="display:inline">· ' + esc(siteName[e.site]) + '</span></button></li>'; }).join('') + '</ul>'
          : '<p class="none">No qualified trainer' + (S.site === 'all' ? '' : ' at ' + esc(siteName[S.site])) + '</p>') + '</section>';
    }).join('') + '</div>';
  }

  /* ---------- keyboard grid (roving tabindex) ---------- */
  var pos = { r: 0, c: -1 };
  function cellAt(r, c) {
    return document.querySelector(c < 0 ? 'th.rowh button[data-r="' + r + '"]' : 'td[data-r="' + r + '"][data-c="' + c + '"]');
  }
  function wireGrid() {
    var nR = document.querySelectorAll('th.rowh button').length, nC = visibleClasses().length;
    if (!nR) return;
    pos.r = Math.min(pos.r, nR - 1); pos.c = Math.min(pos.c, nC - 1);
    var first = cellAt(pos.r, pos.c); if (first) first.tabIndex = 0;
    var table = document.querySelector('table[role=grid]');
    table.addEventListener('keydown', function (e) {
      var el = e.target.closest('[data-r]'); if (!el) return;
      var r = +el.getAttribute('data-r'), c = +el.getAttribute('data-c'), nr = r, nc = c;
      if (e.key === 'ArrowDown') nr = Math.min(nR - 1, r + 1);
      else if (e.key === 'ArrowUp') nr = Math.max(0, r - 1);
      else if (e.key === 'ArrowRight') nc = Math.min(nC - 1, c + 1);
      else if (e.key === 'ArrowLeft') nc = Math.max(-1, c - 1);
      else if (e.key === 'Home') nc = -1;
      else if (e.key === 'End') nc = nC - 1;
      else if ((e.key === 'Enter' || e.key === ' ') && el.tagName === 'TD') { e.preventDefault(); openEngineer(el.getAttribute('data-eng')); return; }
      else return;
      e.preventDefault();
      var next = cellAt(nr, nc);
      if (next) { el.tabIndex = -1; next.tabIndex = 0; next.focus(); pos = { r: nr, c: nc }; }
    });
    table.addEventListener('click', function (e) {
      var el = e.target.closest('[data-eng]'); if (!el) return;
      openEngineer(el.getAttribute('data-eng'));
    });
  }

  /* ---------- engineer detail ---------- */
  var lastFocus = null;
  function openEngineer(id) {
    var e = byId[id], dlg = $('dlg');
    lastFocus = document.activeElement;
    var canTrain = D.classes.filter(function (c) { var x = lv(e, c.id); return x[0] >= D.meta.trainer_level && x[1]; });
    $('dlg-in').innerHTML = '<button type="button" class="close" id="dlg-close">Close</button>' +
      '<h2 id="dlg-title">' + esc(e.name) + '</h2><span class="sub">' + esc(e.role) + ' · ' + esc(siteName[e.site]) + ' · ' + e.id + '</span>' +
      '<table><thead><tr><th scope="col">Equipment class</th><th scope="col">Level</th><th scope="col">Status</th></tr></thead><tbody>' +
      D.classes.filter(function (c) { return lv(e, c.id)[0]; }).map(function (c) {
        var x = lv(e, c.id);
        return '<tr><td>' + esc(c.name) + '</td><td><span class="lv l' + x[0] + '">' + x[0] + '</span> ' + esc(levelLabel(x[0])) + '</td><td>' +
          (x[1] ? 'Validated' : 'Self-assessed, awaiting manager') + '</td></tr>';
      }).join('') + '</tbody></table>' +
      '<p style="margin:12px 0 0"><b>Not assessed:</b> ' + (D.classes.filter(function (c) { return !lv(e, c.id)[0]; }).map(function (c) { return esc(c.name); }).join(', ') || 'none') + '</p>' +
      '<p style="margin:6px 0 0"><b>Can train:</b> ' + (canTrain.length ? canTrain.map(function (c) { return esc(c.name); }).join(', ') : 'none yet') + '</p>';
    $('dlg-close').addEventListener('click', function () { dlg.close(); });
    dlg.showModal();
  }

  function init(data) {
    D = data;
    D.engineers.forEach(function (e) { byId[e.id] = e; });
    D.sites.forEach(function (s) { siteName[s.id] = s.name; });
    D.classes.forEach(function (c) { clsById[c.id] = c; });
    readHash();
    $('f-site').innerHTML = '<option value="all">All sites</option>' + D.sites.map(function (s) { return '<option value="' + s.id + '">' + esc(s.name) + '</option>'; }).join('');
    $('f-class').innerHTML = '<option value="all">All classes</option>' + D.classes.map(function (c) { return '<option value="' + c.id + '">' + esc(c.name) + '</option>'; }).join('');
    $('f-level').innerHTML = '<option value="0">Any level</option>' + D.meta.levels.slice(1).map(function (l) { return '<option value="' + l.n + '">' + l.n + ' ' + esc(l.label) + ' or above</option>'; }).join('');
    $('f-site').value = S.site; $('f-class').value = S.cls; $('f-level').value = String(S.level);
    $('t-gap').checked = S.gap; $('t-train').checked = S.train;
    [['f-site', 'site'], ['f-class', 'cls']].forEach(function (p) { $(p[0]).addEventListener('change', function () { S[p[1]] = this.value; writeHash(); render(); }); });
    $('f-level').addEventListener('change', function () { S.level = +this.value; writeHash(); render(); });
    $('t-gap').addEventListener('change', function () { S.gap = this.checked; writeHash(); render(); });
    $('t-train').addEventListener('change', function () { S.train = this.checked; writeHash(); render(); });
    $('main').addEventListener('click', function (e) { var b = e.target.closest('[data-open]'); if (b) openEngineer(b.getAttribute('data-open')); });
    $('dlg').addEventListener('close', function () { if (lastFocus) lastFocus.focus(); });
    $('dlg').addEventListener('click', function (e) { if (e.target === this) this.close(); });
    $('foot').textContent = D.meta.note + ' Seed ' + D.meta.seed + '. Gap rule: fewer than ' + D.meta.gap_threshold + ' engineers at level ' + D.meta.competent_min + ' or above, validated by a manager.';
    render();
  }

  fetch('data.json').then(function (r) { return r.json(); }).then(init).catch(function (e) {
    $('main').innerHTML = '<p class="empty">Could not load data.json. Serve this folder over http rather than opening the file directly.</p>';
    console.error(e);
  });
})();
