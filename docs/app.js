/* Renders the generated SITE_DATA into the static page. No framework. */
(function () {
  'use strict';
  var D = window.SITE_DATA;
  if (!D) return;

  function el(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function rel(href) {
    if (/^https?:\/\//.test(href)) return href;
    return 'https://github.com/adineo-cmd/open-research-lab/blob/main/' + href;
  }

  /* hero */
  el('hero-kicker').textContent = 'Consolidated record · ' + D.meta.updated;
  el('hero-intro').textContent = D.meta.intro;
  el('register-date').textContent = D.stats.dateSpan;

  var rows = [
    ['Findings recorded', D.stats.findings, ''],
    ['Machine-checkable certificates', D.stats.certificates, ''],
    ['Research tracks', D.stats.tracks, ''],
    ['Reasoning instruments', D.stats.apps, ''],
    ['Days of work', D.stats.daysOfWork, '']
  ];
  var dl = el('register-rows');
  rows.forEach(function (r) {
    var wrap = document.createElement('div');
    wrap.className = 'register-row';
    var dt = document.createElement('dt'); dt.textContent = r[0];
    var dd = document.createElement('dd');
    var num = document.createElement('span');
    num.textContent = typeof r[1] === 'number' ? '0' : r[1];
    if (typeof r[1] === 'number') { num.dataset.target = r[1]; }
    dd.appendChild(num);
    if (r[2]) { var s = document.createElement('small'); s.textContent = r[2]; dd.appendChild(s); }
    wrap.appendChild(dt); wrap.appendChild(dd); dl.appendChild(wrap);
  });

  /* the single orchestrated reveal: counts settle into place */
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('[data-target]').forEach(function (node) {
    var target = parseInt(node.dataset.target, 10);
    if (reduce) { node.textContent = target; return; }
    var start = null, dur = 900;
    function tick(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      node.textContent = Math.floor(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick); else node.textContent = target;
    }
    requestAnimationFrame(tick);
  });

  /* now */
  el('now-list').innerHTML = D.now.map(function (n) {
    return '<article class="now-item">' +
      '<span class="status">' + esc(n.status) + '</span>' +
      '<div><h3>' + esc(n.title) + '</h3><p>' + esc(n.detail) + '</p>' +
      '<a href="' + esc(rel(n.link)) + '">Read the record</a></div></article>';
  }).join('');

  /* findings ledger */
  el('findings-sub').textContent = D.stats.findings + ' dated entries from ' +
    D.stats.dateSpan + '. Select a row to expand it.';
  var tracked = ['All'].concat(Object.keys(D.trackCounts).sort());
  el('filters').innerHTML = tracked.map(function (t, i) {
    return '<button class="filter" type="button" data-track="' + esc(t) + '"' +
      ' aria-pressed="' + (i === 0) + '">' + esc(t) + '</button>';
  }).join('');

  function renderLedger(filter) {
    var items = D.findings.filter(function (f) {
      return filter === 'All' || f.track === filter;
    });
    el('ledger').innerHTML = items.map(function (f) {
      return '<details class="ledger-row"><summary class="ledger-summary">' +
        '<span class="ledger-id">' + esc(f.id) + '</span>' +
        '<span class="ledger-date">' + esc(f.date) + '</span>' +
        '<span class="ledger-track">' + esc(f.track) + '</span>' +
        '<span class="ledger-title">' + esc(f.title) + '</span>' +
        '<span class="ledger-caret" aria-hidden="true">+</span>' +
        '</summary><div class="ledger-detail">' + esc(f.detail) + '</div></details>';
    }).join('');
    document.querySelectorAll('.ledger-row').forEach(function (d) {
      d.addEventListener('toggle', function () {
        var c = d.querySelector('.ledger-caret');
        if (c) c.textContent = d.open ? '−' : '+';
      });
    });
  }
  renderLedger('All');
  el('filters').addEventListener('click', function (ev) {
    var b = ev.target.closest('.filter');
    if (!b) return;
    el('filters').querySelectorAll('.filter').forEach(function (x) {
      x.setAttribute('aria-pressed', String(x === b));
    });
    renderLedger(b.dataset.track);
  });

  /* tracks */
  el('track-list').innerHTML = D.tracks.map(function (t) {
    return '<article class="track-item"><span class="track-key">' + esc(t.id) + '</span>' +
      '<h3>' + esc(t.label) + '</h3><p>' + esc(t.desc) + '</p>' +
      '<div class="track-examples">' + esc(t.examples) + '</div></article>';
  }).join('');

  /* librephone */
  el('libre-summary').textContent = D.librephone.summary;
  el('libre-highlights').innerHTML = D.librephone.highlights.map(function (h) {
    return '<li>' + esc(h) + '</li>';
  }).join('');
  el('libre-workorders').textContent = D.librephone.workorders;
  el('libre-areas').innerHTML = D.librephone.areas.map(function (a) {
    return '<span class="chip">' + esc(a) + '</span>';
  }).join('');
  el('libre-link').href = D.librephone.repo;

  /* apps */
  el('apps-summary').textContent = D.apps.summary;
  el('app-index').innerHTML = D.apps.items.map(function (a) {
    return '<li><strong>' + esc(a.name) + '</strong><span>' + esc(a.desc) + '</span></li>';
  }).join('');

  /* method */
  el('method-steps').innerHTML = D.method.map(function (m) {
    return '<li><strong>' + esc(m.step) + '</strong><p>' + esc(m.detail) + '</p></li>';
  }).join('');

  /* repository + recent commits */
  el('repo-link').href = D.meta.repo;
  el('recent').innerHTML = D.commits.map(function (c) {
    return '<div class="recent-row"><span>' + esc(c.hash) + '</span>' +
      '<span>' + esc(c.date) + '</span><span>' + esc(c.subject) + '</span></div>';
  }).join('');

  el('footer-meta').textContent = D.stats.certificates + ' certificates · ' +
    D.stats.findings + ' findings · updated ' + D.stats.generated;
})();
