// SPDX-License-Identifier: GPL-3.0-or-later
//
// Everything the wiki needs at runtime, which is deliberately not much: a theme
// switch, a navigation drawer on narrow windows, a scroll-spy for the table of
// contents, and a search that filters an index shipped as one JSON file. There
// is no framework and no build step for this file — the pages are static, and a
// reader with scripting turned off still gets every word.

(function () {
	'use strict';

	var root = document.documentElement;

	/* ------------------------------------------------------------- theme -- */

	var toggle = document.querySelector('.theme-toggle');
	if (toggle) {
		toggle.addEventListener('click', function () {
			var next = root.dataset.theme === 'light' ? 'dark' : 'light';
			root.dataset.theme = next;
			try {
				localStorage.setItem('spagitty-wiki-theme', next);
			} catch (e) {
				/* A private window that refuses storage still switches for this page. */
			}
		});
	}

	/* --------------------------------------------------------- navigation -- */

	var menu = document.querySelector('.menu-toggle');
	var scrim = document.querySelector('.scrim');

	function setNav(open) {
		document.body.classList.toggle('nav-open', open);
		if (menu) menu.setAttribute('aria-expanded', String(open));
		if (scrim) scrim.hidden = !open;
	}

	if (menu) menu.addEventListener('click', function () {
		setNav(!document.body.classList.contains('nav-open'));
	});
	if (scrim) scrim.addEventListener('click', function () { setNav(false); });
	setNav(false);

	/* ------------------------------------------------------------ tables -- */

	// Wide tables scroll inside their own box rather than pushing the page
	// sideways. Done here so a content fragment stays plain markup.
	Array.prototype.forEach.call(document.querySelectorAll('.prose table'), function (table) {
		if (table.parentElement && table.parentElement.classList.contains('table-wrap')) return;
		var wrap = document.createElement('div');
		wrap.className = 'table-wrap';
		table.parentNode.insertBefore(wrap, table);
		wrap.appendChild(table);
	});

	/* --------------------------------------------------------- scroll spy -- */

	var tocLinks = Array.prototype.slice.call(document.querySelectorAll('.toc a'));
	if (tocLinks.length && 'IntersectionObserver' in window) {
		var byId = {};
		tocLinks.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });

		var seen = {};
		var observer = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) { seen[entry.target.id] = entry.isIntersecting; });
				var current = null;
				Object.keys(byId).forEach(function (id) { if (seen[id] && !current) current = id; });
				tocLinks.forEach(function (a) {
					a.classList.toggle('active', a.getAttribute('href') === '#' + current);
				});
			},
			{ rootMargin: '-80px 0px -70% 0px', threshold: 0 }
		);

		Object.keys(byId).forEach(function (id) {
			var el = document.getElementById(id);
			if (el) observer.observe(el);
		});
	}

	/* ------------------------------------------------------------ search -- */

	var input = document.getElementById('search-input');
	var results = document.getElementById('search-results');
	if (!input || !results) return;

	var index = null;
	var loading = false;
	var active = -1;

	function load() {
		if (index || loading) return Promise.resolve(index);
		loading = true;
		return fetch('assets/search-index.json')
			.then(function (r) { return r.json(); })
			.then(function (data) { index = data; loading = false; return data; })
			.catch(function () { loading = false; return null; });
	}

	function escapeHtml(s) {
		return s.replace(/[&<>"]/g, function (c) {
			return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
		});
	}

	// One snippet around the first hit, so a result says why it matched.
	function snippet(body, term) {
		var at = body.toLowerCase().indexOf(term);
		if (at < 0) return '';
		var from = Math.max(0, at - 60);
		var text = (from > 0 ? '…' : '') + body.slice(from, at + term.length + 110) + '…';
		var re = new RegExp('(' + term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig');
		return escapeHtml(text).replace(re, '<mark>$1</mark>');
	}

	function score(page, term) {
		var t = term.toLowerCase();
		var s = 0;
		if (page.t.toLowerCase().indexOf(t) >= 0) s += 60;
		if (page.n.toLowerCase().indexOf(t) >= 0) s += 40;
		if (page.d.toLowerCase().indexOf(t) >= 0) s += 20;
		for (var i = 0; i < page.h.length; i++) {
			if (page.h[i].t.toLowerCase().indexOf(t) >= 0) s += 14;
		}
		var body = page.b.toLowerCase();
		var at = body.indexOf(t);
		if (at >= 0) s += 8;
		return s;
	}

	function render(term) {
		if (!index || term.length < 2) {
			results.hidden = true;
			input.setAttribute('aria-expanded', 'false');
			return;
		}

		var hits = [];
		index.forEach(function (page) {
			var s = score(page, term);
			if (!s) return;

			// A matching heading is a better destination than the page top.
			var target = page.u;
			var where = page.s;
			for (var i = 0; i < page.h.length; i++) {
				if (page.h[i].t.toLowerCase().indexOf(term.toLowerCase()) >= 0) {
					target = page.u + '#' + page.h[i].i;
					where = page.n + ' · ' + page.h[i].t;
					break;
				}
			}
			hits.push({ s: s, u: target, title: page.t, where: where, snip: snippet(page.b, term) || escapeHtml(page.d) });
		});

		hits.sort(function (a, b) { return b.s - a.s; });
		hits = hits.slice(0, 8);
		active = -1;

		if (!hits.length) {
			results.innerHTML = '<p class="r-empty">Nothing here matches “' + escapeHtml(term) + '”.</p>';
		} else {
			results.innerHTML = hits
				.map(function (h) {
					return (
						'<a href="' + h.u + '" role="option">' +
						'<span class="r-where">' + escapeHtml(h.where) + '</span>' +
						'<span class="r-title">' + escapeHtml(h.title) + '</span>' +
						'<span class="r-snippet">' + h.snip + '</span>' +
						'</a>'
					);
				})
				.join('');
		}
		results.hidden = false;
		input.setAttribute('aria-expanded', 'true');
	}

	input.addEventListener('focus', load);
	input.addEventListener('input', function () {
		var term = input.value.trim();
		load().then(function () { render(term); });
	});

	input.addEventListener('keydown', function (event) {
		var links = results.querySelectorAll('a');
		if (event.key === 'Escape') {
			input.value = '';
			results.hidden = true;
			input.blur();
			return;
		}
		if (!links.length) return;
		if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
			event.preventDefault();
			active += event.key === 'ArrowDown' ? 1 : -1;
			if (active < 0) active = links.length - 1;
			if (active >= links.length) active = 0;
			Array.prototype.forEach.call(links, function (a, i) {
				a.classList.toggle('active', i === active);
			});
			links[active].scrollIntoView({ block: 'nearest' });
		}
		if (event.key === 'Enter' && active >= 0) {
			event.preventDefault();
			window.location.href = links[active].getAttribute('href');
		}
	});

	document.addEventListener('click', function (event) {
		if (!event.target.closest('.search')) results.hidden = true;
	});

	// `/` focuses the search from anywhere, the way the application's palette
	// answers a key rather than a click.
	document.addEventListener('keydown', function (event) {
		var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
		if (event.key === '/' && !typing) {
			event.preventDefault();
			input.focus();
			input.select();
		}
	});
})();
