/* Site search: loads /search.json once and ranks results in the browser. */
(function () {
  var script = document.currentScript;
  var dialog = document.getElementById('search');
  var input = document.getElementById('searchInput');
  var box = document.getElementById('searchResults');
  var openBtn = document.getElementById('searchOpen');
  if (!dialog || !input) return;
  var docs = null, loading = null, active = -1;

  function norm(s) { return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); }
  function words(s) { return norm(s).split(/[^a-z0-9]+/).filter(Boolean); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function load() {
    if (!loading) loading = fetch(script.getAttribute('data-index')).then(function (r) { return r.json(); }).then(function (list) {
      docs = list.map(function (d) {
        return { d: d, t: words(d.t), k: words(d.k), s: words(d.d), c: words(d.c) };
      });
      return docs;
    });
    return loading;
  }

  // Prefix match on whole words: "over" matches "overtime"; every query word must match somewhere.
  function hit(list, q) { for (var i = 0; i < list.length; i++) if (list[i].indexOf(q) === 0) return true; return false; }
  function count(list, q) { var n = 0; for (var i = 0; i < list.length && n < 5; i++) if (list[i].indexOf(q) === 0) n++; return n; }

  function search(query) {
    var qs = words(query);
    if (!qs.length) return null;
    var out = [];
    docs.forEach(function (x) {
      var score = 0;
      for (var i = 0; i < qs.length; i++) {
        var q = qs[i], s = 0;
        if (hit(x.t, q)) s += 10;
        if (hit(x.k, q)) s += 6;
        if (hit(x.s, q)) s += 3;
        s += count(x.c, q);
        if (!s) return;
        score += s;
      }
      if (x.d.y === 'Tool') score += 2;
      out.push({ x: x, score: score });
    });
    return out.sort(function (a, b) { return b.score - a.score; }).slice(0, 8).map(function (r) { return r.x.d; });
  }

  function mark(text, qs) {
    var html = esc(text);
    qs.forEach(function (q) {
      if (q.length < 2) return;
      html = html.replace(new RegExp('\\b(' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '[a-z0-9]*)', 'gi'), '<mark>$1</mark>');
    });
    return html;
  }

  function snippet(d, qs) {
    if (!d.c) return d.d || '';
    var text = d.c, low = norm(text);
    for (var i = 0; i < qs.length; i++) {
      var at = low.search(new RegExp('\\b' + qs[i].replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
      if (at > -1 && !hit(words(d.t + ' ' + d.d), qs[i])) {
        var start = Math.max(0, text.lastIndexOf(' ', Math.max(0, at - 60)));
        return (start > 0 ? '…' : '') + text.slice(start, start + 170).trim() + '…';
      }
    }
    return d.d || '';
  }

  function item(d, qs) {
    return '<a class="search-item" role="option" href="' + esc(d.u) + '">' +
      '<span class="search-type t-' + esc(d.y.toLowerCase()) + '">' + esc(d.y) + '</span>' +
      '<strong>' + mark(d.t, qs) + '</strong>' +
      '<span class="search-snip">' + mark(snippet(d, qs), qs) + '</span></a>';
  }

  function render() {
    if (!docs) return;
    var qs = words(input.value), res = search(input.value);
    active = -1;
    if (res === null) {
      var tools = docs.filter(function (x) { return x.d.y === 'Tool'; }).map(function (x) { return x.d; });
      var guides = docs.filter(function (x) { return x.d.y === 'Guide'; }).map(function (x) { return x.d; }).slice(0, 4);
      box.innerHTML = '<p class="search-label">Free tools</p>' + tools.map(function (d) { return item(d, []); }).join('') +
        (guides.length ? '<p class="search-label">Guides</p>' + guides.map(function (d) { return item(d, []); }).join('') : '');
    } else if (!res.length) {
      box.innerHTML = '<p class="search-empty">No results for “' + esc(input.value) + '”. Try <em>overtime</em>, <em>Pitman</em> or <em>template</em> — or <a href="' + '/support' + '">ask us</a>.</p>';
    } else {
      box.innerHTML = res.map(function (d) { return item(d, qs); }).join('');
    }
  }

  function move(step) {
    var items = box.querySelectorAll('.search-item');
    if (!items.length) return;
    active = (active + step + items.length) % items.length;
    items.forEach(function (el, i) { el.classList.toggle('active', i === active); });
    items[active].scrollIntoView({ block: 'nearest' });
  }

  function open() {
    if (dialog.open) return;
    dialog.showModal();
    input.value = '';
    load().then(render);
    setTimeout(function () { input.focus(); }, 0);
  }

  openBtn && openBtn.addEventListener('click', open);
  input.addEventListener('input', render);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
    else if (e.key === 'Enter') {
      var items = box.querySelectorAll('.search-item');
      var target = items[active > -1 ? active : 0];
      if (target) { e.preventDefault(); location.href = target.href; }
    }
  });
  dialog.addEventListener('click', function (e) { if (e.target === dialog) dialog.close(); });
  document.addEventListener('keydown', function (e) {
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
    if ((e.key === 'k' && (e.metaKey || e.ctrlKey)) || (e.key === '/' && !typing)) { e.preventDefault(); open(); }
  });
})();
