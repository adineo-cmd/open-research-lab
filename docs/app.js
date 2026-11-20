/* Shared behaviour for the Open Research Lab site. No framework. */
(function () {
  'use strict';
  var D = window.SITE_DATA;
  if (!D) return;

  var PAGES = [
    { id: 'home', label: 'Home', file: 'index.html' },
    { id: 'findings', label: 'Findings', file: 'findings.html' },
    { id: 'research', label: 'Research', file: 'research.html' },
    { id: 'librephone', label: 'LibrePhone', file: 'librephone.html' },
    { id: 'projects', label: 'Projects', file: 'projects.html' },
    { id: 'apps', label: 'Apps', file: 'apps.html' },
    { id: 'method', label: 'Method', file: 'method.html' }
  ];
  var current = document.body.dataset.page || 'home';
  var REPO = D.meta.repo;

  function el(id) { return document.getElementById(id); }
  function has(id) { return !!el(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function repoLink(path) {
    if (/^https?:\/\//.test(path)) return path;
    return REPO + '/blob/main/' + path;
  }
  function shortDate(d) { return esc((d || '').slice(0, 10)); }

  /* ---- navigation, shared by every page ---- */
  function buildNav() {
    var nav = el('site-nav');
    if (nav) {
      nav.innerHTML = PAGES.map(function (p) {
        return '<a href="' + p.file + '"' + (p.id === current ? ' aria-current="page"' : '') +
          '>' + esc(p.label) + '</a>';
      }).join('');
    }
    var btn = el('menu-toggle');
    if (btn && nav) {
      btn.setAttribute('aria-expanded', 'false');
      btn.addEventListener('click', function () {
        var open = nav.classList.toggle('open');
        btn.setAttribute('aria-expanded', String(open));
        btn.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
      });
      nav.addEventListener('click', function (e) {
        if (e.target.tagName === 'A') {
          nav.classList.remove('open');
          btn.setAttribute('aria-expanded', 'false');
        }
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && nav.classList.contains('open')) {
          nav.classList.remove('open');
          btn.setAttribute('aria-expanded', 'false');
          btn.focus();
        }
      });
    }
    var fm = el('footer-meta');
    if (fm) {
      fm.textContent = D.stats.certificates + ' certificates · ' + D.stats.findings +
        ' findings · ' + D.stats.repos + ' repositories · ' + D.stats.generated;
    }
    var rl = el('footer-repo');
    if (rl) rl.href = REPO;
  }

  /* ---- the single orchestrated reveal (home only) ---- */
  function countUp() {
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
  }

  function registerRows() {
    var rows = [
      ['Findings recorded', D.stats.findings],
      ['Machine-checkable certificates', D.stats.certificates],
      ['Public repositories', D.stats.repos],
      ['Days of work', D.stats.daysOfWork]
    ];
    var dl = el('register-rows');
    if (!dl) return;
    dl.innerHTML = rows.map(function (r) {
      return '<div class="register-row"><dt>' + esc(r[0]) + '</dt><dd>' +
        '<span data-target="' + r[1] + '">0</span></dd></div>';
    }).join('');
    countUp();
  }

  function renderNow() {
    var n = el('now-list');
    if (!n) return;
    n.innerHTML = D.now.map(function (x) {
      return '<article class="now-item"><span class="status">' + esc(x.status) + '</span>' +
        '<div><h3 class="entry-title">' + esc(x.title) + '</h3>' +
        '<p class="entry-detail">' + esc(x.detail) + '</p>' +
        '<a class="inline-link" href="' + esc(repoLink(x.link)) + '">Read the record</a></div></article>';
    }).join('');
  }

  function renderRecent() {
    var r = el('recent');
    if (!r) return;
    r.innerHTML = D.commits.map(function (c) {
      return '<div class="recent-row"><span>' + esc(c.hash) + '</span>' +
        '<span>' + esc(c.date) + '</span><span>' + esc(c.subject) + '</span></div>';
    }).join('');
  }

  /* ---- home ---- */
  function home() {
    if (has('hero-intro')) el('hero-intro').textContent = D.meta.intro;
    registerRows();
    renderNow();
    renderRecent();
    var featured = el('featured-findings');
    if (featured) {
      var last = D.findings.slice(-5).reverse();
      featured.innerHTML = last.map(function (f) {
        return '<div class="ruled"><article class="now-item"><span class="status">' +
          esc(f.date) + ' · ' + esc(f.track) + '</span><div>' +
          '<h3 class="entry-title">' + esc(f.id) + ' — ' + esc(f.title.slice(0, 120)) + '</h3>' +
          '</div></article></div>';
      }).join('');
    }
    var fp = el('featured-projects');
    if (fp) {
      fp.innerHTML = D.projects.repos.slice(0, 5).map(function (p) {
        return '<article class="project"><div class="project-head">' +
          '<a class="project-name" href="https://github.com/' + esc(D.projects.owner) + '/' +
          esc(p.name) + '">' + esc(p.name) + '</a>' +
          '<span class="project-meta"><span>' + esc(p.language || 'mixed') + '</span><span>updated ' +
          shortDate(p.updated) + '</span></span></div>' +
          '<p class="project-desc">' + esc(p.description || 'No description recorded.') + '</p></article>';
      }).join('');
    }
  }

  /* ---- findings ledger ---- */
  function findings() {
    var sub = el('findings-sub');
    if (sub) sub.textContent = D.stats.findings + ' dated entries from ' + D.stats.dateSpan +
      '. Filter by track or search the text.';
    var tracks = ['All'].concat(Object.keys(D.trackCounts).sort());
    var filters = el('filters');
    if (!filters) return;
    filters.innerHTML = tracks.map(function (t, i) {
      return '<button class="filter" type="button" data-track="' + esc(t) + '" aria-pressed="' +
        (i === 0) + '">' + esc(t) + '</button>';
    }).join('');

    var query = '';
    var active = 'All';
    function render() {
      var q = query.toLowerCase();
      var items = D.findings.filter(function (f) {
        if (active !== 'All' && f.track !== active) return false;
        if (!q) return true;
        return (f.id + ' ' + f.title + ' ' + f.detail + ' ' + f.date).toLowerCase().indexOf(q) !== -1;
      });
      var count = el('result-count');
      if (count) count.textContent = items.length + ' of ' + D.stats.findings + ' shown';
      el('ledger').innerHTML = items.length ? items.map(function (f) {
        return '<details class="ledger-row"><summary class="ledger-summary">' +
          '<span class="ledger-id">' + esc(f.id) + '</span>' +
          '<span class="ledger-date">' + esc(f.date) + '</span>' +
          '<span class="ledger-track">' + esc(f.track) + '</span>' +
          '<span class="ledger-title">' + esc(f.title) + '</span>' +
          '<span class="ledger-caret" aria-hidden="true">+</span></summary>' +
          '<div class="ledger-detail">' + esc(f.detail) + '</div></details>';
      }).join('') : '<p class="empty">No findings match that search.</p>';
      el('ledger').querySelectorAll('.ledger-row').forEach(function (d) {
        d.addEventListener('toggle', function () {
          var c = d.querySelector('.ledger-caret');
          if (c) c.textContent = d.open ? '−' : '+';
        });
      });
    }
    filters.addEventListener('click', function (e) {
      var b = e.target.closest('.filter');
      if (!b) return;
      active = b.dataset.track;
      filters.querySelectorAll('.filter').forEach(function (x) {
        x.setAttribute('aria-pressed', String(x === b));
      });
      render();
    });
    var search = el('finding-search');
    if (search) search.addEventListener('input', function () { query = search.value; render(); });
    render();
  }

  /* ---- research ---- */
  function research() {
    var s = el('stat-strip');
    if (s) {
      s.innerHTML = [
        [D.stats.findings, 'dated findings'],
        [D.stats.certificates, 'certificates'],
        [Object.keys(D.stats.certificatesByTrack).length, 'certificate tracks'],
        [D.stats.dateSpan, 'ledger span']
      ].map(function (x) {
        return '<div><strong>' + esc(x[0]) + '</strong><span>' + esc(x[1]) + '</span></div>';
      }).join('');
    }
    var t = el('track-list');
    if (t) {
      t.innerHTML = D.tracks.map(function (x) {
        return '<article class="track-item"><span class="track-key">' + esc(x.id) + '</span>' +
          '<h3>' + esc(x.label) + '</h3><p>' + esc(x.desc) + '</p>' +
          '<span class="track-examples">' + esc(x.examples) + '</span></article>';
      }).join('');
    }
    var r = el('result-list');
    if (r) {
      r.innerHTML = D.researchResults.map(function (x) {
        return '<article class="project"><div class="project-head">' +
          '<h3 class="entry-title">' + esc(x.title) + '</h3>' +
          '<span class="project-meta"><span>' + esc(x.status) + '</span></span></div>' +
          '<p class="project-desc">' + esc(x.detail) + '</p>' +
          '<a class="inline-link" href="' + esc(repoLink(x.link)) + '">Read the result</a></article>';
      }).join('');
    }
    if (has('prior-art-summary')) el('prior-art-summary').textContent = D.priorArt.summary;
    if (has('prior-art-link')) el('prior-art-link').href = repoLink(D.priorArt.link);
  }

  /* ---- librephone ---- */
  function librephone() {
    function set(id, text) { if (has(id)) el(id).textContent = text; }
    set('libre-summary', D.librephone.summary);
    set('libre-workorders', D.librephone.workorders);
    if (has('libre-highlights')) {
      el('libre-highlights').innerHTML = D.librephone.highlights.map(function (h) {
        return '<li>' + esc(h) + '</li>';
      }).join('');
    }
    if (has('libre-areas')) {
      el('libre-areas').innerHTML = D.librephone.areas.map(function (a) {
        return '<span class="chip">' + esc(a) + '</span>';
      }).join('');
    }
    if (has('libre-link')) el('libre-link').href = D.librephone.repo;
  }

  /* ---- projects catalog ---- */
  function projects() {
    var p = el('project-list');
    if (!p) return;
    var langs = ['All'].concat(Object.keys(D.projects.repos.reduce(function (a, r) {
      var k = r.language || 'Mixed'; a[k] = (a[k] || 0) + 1; return a;
    }, {}))).sort();
    el('lang-filters').innerHTML = langs.map(function (l, i) {
      return '<button class="filter" type="button" data-lang="' + esc(l) + '" aria-pressed="' +
        (i === 0) + '">' + esc(l) + '</button>';
    }).join('');
    var query = '', active = 'All';
    function render() {
      var q = query.toLowerCase();
      var items = D.projects.repos.filter(function (r) {
        if (active !== 'All' && (r.language || 'Mixed') !== active) return false;
        if (!q) return true;
        return (r.name + ' ' + r.description + ' ' + (r.topics || []).join(' ')).toLowerCase().indexOf(q) !== -1;
      });
      var c = el('project-count');
      if (c) c.textContent = items.length + ' of ' + D.stats.repos + ' repositories';
      p.innerHTML = items.length ? items.map(function (r) {
        var url = 'https://github.com/' + esc(D.projects.owner) + '/' + esc(r.name);
        var meta = '<span>' + esc(r.language || 'mixed') + '</span>' +
          '<span>' + esc(r.stars) + ' stars</span>' +
          '<span>updated ' + shortDate(r.updated) + '</span>';
        if (r.homepage && /^https?:\/\//.test(r.homepage)) {
          meta += '<a class="inline-link" href="' + esc(r.homepage) + '">site</a>';
        }
        return '<article class="project"><div class="project-head">' +
          '<a class="project-name" href="' + url + '">' + esc(r.name) + '</a>' +
          '<span class="project-meta">' + meta + '</span></div>' +
          '<p class="project-desc">' + esc(r.description || 'No description recorded.') + '</p></article>';
      }).join('') : '<p class="empty">No repositories match that search.</p>';
    }
    el('lang-filters').addEventListener('click', function (e) {
      var b = e.target.closest('.filter');
      if (!b) return;
      active = b.dataset.lang;
      el('lang-filters').querySelectorAll('.filter').forEach(function (x) {
        x.setAttribute('aria-pressed', String(x === b));
      });
      render();
    });
    var search = el('project-search');
    if (search) search.addEventListener('input', function () { query = search.value; render(); });
    render();
  }

  /* ---- apps ---- */
  function apps() {
    var a = el('app-index');
    if (!a) return;
    a.innerHTML = D.apps.items.map(function (x) {
      return '<li><strong>' + esc(x.name) + '</strong><p>' + esc(x.desc) + '</p></li>';
    }).join('');
    var s = el('apps-summary');
    if (s) s.textContent = D.apps.summary;
  }

  /* ---- method ---- */
  function method() {
    var m = el('method-steps');
    if (m) {
      m.innerHTML = D.method.map(function (x) {
        return '<li><strong>' + esc(x.step) + '</strong><p>' + esc(x.detail) + '</p></li>';
      }).join('');
    }
    var n = el('not-claimed');
    if (n) n.innerHTML = D.notClaimed.map(function (x) {
      return '<li>' + esc(x) + '</li>';
    }).join('');
  }

  buildNav();
  switch (current) {
    case 'home': home(); break;
    case 'findings': findings(); break;
    case 'research': research(); break;
    case 'librephone': librephone(); break;
    case 'projects': projects(); break;
    case 'apps': apps(); break;
    case 'method': method(); break;
  }
})();
