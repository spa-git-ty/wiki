#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Assemble the Spagitty wiki.

Every page is a body fragment in `content/`. This script wraps each one in the
shared shell — head, sidebar, header, footer — and writes it to the repository
root, where GitHub Pages serves it. It also writes `sitemap.xml` and the
client-side search index.

The page registry below is the single source of truth for navigation order,
titles, descriptions and the sitemap. Adding a page means adding a row here and
a fragment in `content/`; nothing else has to be touched.

    python3 build.py           # build
    python3 build.py --check   # fail if the committed output is stale
"""

from __future__ import annotations

import html
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"

SITE = "https://spa-git-ty.github.io/wiki"
REPO = "https://github.com/spa-git-ty/spagitty"
WIKI_REPO = "https://github.com/spa-git-ty/wiki"
BUILT = date.today().isoformat()


@dataclass
class Page:
    slug: str
    title: str
    nav: str
    description: str
    section: str
    keywords: list[str] = field(default_factory=list)
    priority: str = "0.7"

    @property
    def filename(self) -> str:
        return "index.html" if self.slug == "index" else f"{self.slug}.html"

    @property
    def url(self) -> str:
        return f"{SITE}/" if self.slug == "index" else f"{SITE}/{self.slug}.html"


# Navigation order is reading order. The sections are the four questions a
# reader arrives with: what is this, how do I use it, how is it built, and how
# do we work on it.
PAGES = [
    Page("index", "Spagitty Wiki", "Home",
         "Spagitty is a local-first desktop Git client and the gateway to a Git-managed agent farm. "
         "The complete documentation: features, screens, architecture and the full code map.",
         "Start here",
         ["spagitty", "git client", "desktop git", "agent farm", "coding agents", "tauri", "rust", "svelte"],
         "1.0"),
    Page("overview", "What Spagitty Is", "What Spagitty is",
         "The problem Spagitty solves, the principles it is built on, what it deliberately is not, "
         "and where the name comes from.",
         "Start here",
         ["local-first git client", "spaghetti git", "git gui", "agents commit", "open source git client"],
         "0.9"),
    Page("install", "Install & First Run", "Install & first run",
         "Download a build for Linux, macOS or Windows, open your first repository, "
         "or build Spagitty from source with Rust and Bun.",
         "Start here",
         ["install spagitty", "download git client", "build from source", "rust", "bun", "webkitgtk"],
         "0.9"),
    Page("features", "Feature Reference", "Feature reference",
         "Every capability Spagitty ships, grouped by what you are trying to do: the graph, the "
         "working copy, diffs, branches, rebasing, pull requests, the farm and the chrome.",
         "Start here",
         ["git features", "commit graph", "interactive rebase", "pull requests", "worktrees", "submodules"],
         "0.9"),

    Page("farm", "The Agent Farm", "The agent farm",
         "A goal, the tasks it was cut into, and the coding agents on your machine working them in "
         "parallel — one branch and one worktree each, verified and peer-reviewed before anything merges.",
         "Using Spagitty",
         ["agent farm", "claude code", "codex", "cursor", "parallel agents", "git worktree", "autonomy levels"],
         "1.0"),
    Page("screens", "Screen Reference", "Screens 1A–1Q",
         "Every screen in Spagitty by its code — Graph, Diff, Working copy, Conflicts, Rebase, "
         "Branches, Stash, Pull requests, Log, Repositories, Settings, Clone, Reflog, Tags, History, Badges, Farm.",
         "Using Spagitty",
         ["git gui screens", "commit graph ui", "conflict resolution ui", "rebase ui", "blame view"],
         "0.9"),
    Page("themes", "Themes & Appearance", "Themes & appearance",
         "Eight palette families in light and dark, the contrast rules they are held to, "
         "the glass chrome, and the two independent scaling dials.",
         "Using Spagitty",
         ["catppuccin", "dracula", "tokyo night", "gruvbox", "nord", "rose pine", "solarized", "everforest"]),
    Page("privacy", "Privacy & Security", "Privacy & security",
         "No telemetry, no account, no server of ours. Where tokens live, what crosses the network, "
         "and the two boundaries that make those claims checkable.",
         "Using Spagitty",
         ["local-first", "no telemetry", "os keychain", "personal access token", "git privacy"]),

    Page("architecture", "Architecture", "Architecture",
         "Three layers that each know nothing about the one above: the SvelteKit app, the Tauri shell, "
         "and the Rust crates. The seams, the boundaries, and why they hold.",
         "How it is built",
         ["tauri architecture", "rust git library", "gitoxide", "gix", "sveltekit spa", "ipc"],
         "0.9"),
    Page("code-map", "Code Map", "Code map",
         "Every directory and module in the Spagitty workspace, what it holds, and where to start reading.",
         "How it is built",
         ["code map", "source tree", "module reference", "rust crates", "svelte stores"],
         "0.9"),
    Page("core-crate", "spagitty-core", "spagitty-core (git)",
         "The Rust crate that performs every git operation — module by module, including the gix/git "
         "binary boundary and the forge network boundary.",
         "How it is built",
         ["spagitty-core", "gix", "gitoxide", "git shell boundary", "blame", "graph lanes"]),
    Page("farm-crate", "spagitty-farm", "spagitty-farm (agents)",
         "The agent farm's control plane: the model, adapters, workspaces, execution, orchestration, "
         "verification, review and persistence.",
         "How it is built",
         ["spagitty-farm", "agent orchestration", "scheduler", "dependency dag", "peer review"]),
    Page("tauri-layer", "The Tauri Layer", "The Tauri layer",
         "The thin shell that owns the window, the background workers and the command surface "
         "between the webview and the Rust crates.",
         "How it is built",
         ["tauri", "commands", "workers", "filesystem watcher", "webkitgtk"]),
    Page("frontend", "The Frontend", "The frontend",
         "The SvelteKit app: one store per screen, the single API module, the shared UI kit, "
         "the metrics contract and the delight layer.",
         "How it is built",
         ["sveltekit", "svelte 5", "runes", "stores", "command palette", "virtualised list"]),
    Page("ipc", "IPC Reference", "IPC reference",
         "Every Tauri command and every event that crosses between the webview and the backend, "
         "grouped by what it is for.",
         "How it is built",
         ["tauri commands", "ipc", "invoke", "events", "api reference"]),

    Page("testing", "Testing", "Testing",
         "What is tested and how — headless suites, real repository fixtures, the one test that "
         "crosses the language boundary, and how the app is driven for a visual sweep.",
         "How we work",
         ["testing", "vitest", "cargo test", "coverage", "fixtures", "happy-dom"]),
    Page("ci", "CI/CD & Releases", "CI/CD & releases",
         "Six ordered gates, the coverage floor, the three release lanes, and when a merge publishes.",
         "How we work",
         ["ci", "github actions", "gates", "coverage floor", "release", "cargo deny", "gitleaks"]),
    Page("process", "How We Work", "How we work",
         "The working record: items, plans and test sweeps under `agile/`, the branching model, "
         "and the standing rules a change is written against.",
         "How we work",
         ["working record", "git flow", "work items", "amendments", "agile"]),
    Page("branding", "Brand & Identity", "Brand & identity",
         "The mark, the wordmark, the palette, the voice, and the rules that keep them consistent.",
         "How we work",
         ["brand guide", "logo", "colour palette", "wordmark", "inter"]),
    Page("contributing", "Contributing", "Contributing",
         "How to send a change: what to read first, how a branch is named, what a pull request needs, "
         "and the checks it has to clear.",
         "How we work",
         ["contributing", "pull request", "open source", "gpl-3.0"]),
    Page("releases", "Release History", "Release history",
         "Every version of Spagitty and what shipped in it, newest first.",
         "How we work",
         ["changelog", "release notes", "versions", "semver"]),
    Page("glossary", "Glossary", "Glossary",
         "The vocabulary this wiki uses — Spagitty's own terms and the git ones it leans on.",
         "How we work",
         ["glossary", "git terminology", "definitions"], "0.5"),
    Page("faq", "FAQ", "FAQ",
         "Common questions about Spagitty: what it costs, what it sends, which agents it runs, "
         "and how it compares to the clients you already know.",
         "How we work",
         ["faq", "questions", "git client comparison"], "0.6"),
]

BY_SLUG = {p.slug: p for p in PAGES}

SECTIONS: list[str] = []
for _p in PAGES:
    if _p.section not in SECTIONS:
        SECTIONS.append(_p.section)


def sidebar(current: str) -> str:
    """The navigation tree, with the current page marked."""
    out = ['<nav class="sidebar-nav" aria-label="Wiki sections">']
    for section in SECTIONS:
        out.append(f'<p class="nav-section">{html.escape(section)}</p>')
        out.append("<ul>")
        for page in PAGES:
            if page.section != section:
                continue
            here = ' aria-current="page"' if page.slug == current else ""
            cls = ' class="here"' if page.slug == current else ""
            out.append(
                f'<li{cls}><a href="{page.filename}"{here}>{html.escape(page.nav)}</a></li>'
            )
        out.append("</ul>")
    out.append("</nav>")
    return "\n".join(out)


def neighbours(slug: str) -> str:
    """Previous / next links, so the wiki can also be read straight through."""
    i = [p.slug for p in PAGES].index(slug)
    prev_p = PAGES[i - 1] if i > 0 else None
    next_p = PAGES[i + 1] if i < len(PAGES) - 1 else None
    if not prev_p and not next_p:
        return ""
    parts = ['<nav class="pager" aria-label="Page navigation">']
    if prev_p:
        parts.append(
            f'<a class="pager-link prev" href="{prev_p.filename}">'
            f'<span class="pager-dir">Previous</span>'
            f'<span class="pager-title">{html.escape(prev_p.nav)}</span></a>'
        )
    else:
        parts.append('<span class="pager-link empty"></span>')
    if next_p:
        parts.append(
            f'<a class="pager-link next" href="{next_p.filename}">'
            f'<span class="pager-dir">Next</span>'
            f'<span class="pager-title">{html.escape(next_p.nav)}</span></a>'
        )
    parts.append("</nav>")
    return "\n".join(parts)


def anchorise(body: str) -> tuple[str, list[tuple[str, str, str]]]:
    """Give every heading an id and a self link, and collect them for the TOC.

    Written here rather than in JavaScript so the anchors exist for a reader
    with no scripting and for whatever crawls the page.
    """
    headings: list[tuple[str, str, str]] = []
    used: set[str] = set()

    def slugify(text: str) -> str:
        s = re.sub(r"<[^>]+>", "", text)
        s = html.unescape(s).lower()
        s = re.sub(r"[^a-z0-9\s-]", "", s)
        s = re.sub(r"[\s-]+", "-", s).strip("-") or "section"
        base, n = s, 2
        while s in used:
            s, n = f"{base}-{n}", n + 1
        used.add(s)
        return s

    def repl(m: re.Match[str]) -> str:
        level, attrs, text = m.group(1), m.group(2) or "", m.group(3)
        if "id=" in attrs:
            return m.group(0)
        ident = slugify(text)
        plain = html.unescape(re.sub(r"<[^>]+>", "", text)).strip()
        headings.append((level, ident, plain))
        return (
            f'<h{level}{attrs} id="{ident}">{text}'
            f'<a class="anchor" href="#{ident}" aria-label="Link to this section">#</a>'
            f"</h{level}>"
        )

    body = re.sub(r"<h([23])([^>]*)>(.*?)</h\1>", repl, body, flags=re.S)
    return body, headings


def toc(headings: list[tuple[str, str, str]]) -> str:
    items = [h for h in headings if h[0] == "2"]
    if len(items) < 2:
        return ""
    rows = "\n".join(
        f'<li><a href="#{i}">{html.escape(t)}</a></li>' for _, i, t in items
    )
    return (
        '<aside class="toc" aria-label="On this page">'
        '<p class="toc-title">On this page</p>'
        f"<ul>{rows}</ul></aside>"
    )


SHELL = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="keywords" content="{keywords}">
<meta name="author" content="The Spagitty Authors">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{url}">
<link rel="icon" href="assets/brand/favicon.ico" sizes="any">
<link rel="icon" href="assets/brand/mark.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="assets/brand/favicon-64.png">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Spagitty Wiki">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{site}/assets/brand/hero.png">
<meta property="og:image:alt" content="Spagitty — untangle the work, yours and your agents'">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{site}/assets/brand/hero.png">
<meta name="theme-color" content="#1e1e2e" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#eff1f5" media="(prefers-color-scheme: light)">
<link rel="sitemap" type="application/xml" href="sitemap.xml">
<link rel="stylesheet" href="assets/wiki.css">
<script>
  // Applied before first paint so a chosen theme never flashes the other one.
  try {{
    var t = localStorage.getItem('spagitty-wiki-theme');
    if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t;
    else if (window.matchMedia('(prefers-color-scheme: light)').matches)
      document.documentElement.dataset.theme = 'light';
  }} catch (e) {{}}
</script>
<script type="application/ld+json">{jsonld}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<header class="topbar">
  <button class="menu-toggle" aria-label="Open navigation" aria-expanded="false"></button>
  <a class="brand" href="index.html">
    <img src="assets/brand/mark.svg" width="26" height="26" alt="">
    <span class="brand-word">spagitty</span>
    <span class="brand-tag">wiki</span>
  </a>
  <div class="search" role="search">
    <input id="search-input" type="search" placeholder="Search the wiki…" autocomplete="off"
           aria-label="Search the wiki" aria-controls="search-results" aria-expanded="false">
    <kbd class="search-key">/</kbd>
    <div id="search-results" class="search-results" role="listbox" hidden></div>
  </div>
  <div class="topbar-actions">
    <button class="theme-toggle" aria-label="Switch between light and dark"></button>
    <a class="ghlink" href="{repo}" rel="noopener">GitHub</a>
  </div>
</header>

<div class="shell">
  <aside class="sidebar" id="sidebar">
{sidebar}
    <div class="sidebar-foot">
      <a href="{repo}/releases/latest" rel="noopener">Download Spagitty</a>
      <a href="{repo}" rel="noopener">Source repository</a>
      <a href="{wiki_repo}" rel="noopener">Edit this wiki</a>
    </div>
  </aside>

  <main id="main" class="content">
{toc}
    <article class="prose">
{body}
    </article>
{pager}
    <footer class="page-foot">
      <p>Spagitty is free software under the
        <a href="{repo}/blob/main/LICENSE" rel="noopener">GNU General Public License v3.0 or later</a>.
        Spagitty is not affiliated with the Git project; Git and the Git logo are trademarks of
        Software Freedom Conservancy.</p>
      <p class="built">Wiki built {built} · <a href="{wiki_repo}" rel="noopener">spa-git-ty/wiki</a></p>
    </footer>
  </main>
</div>

<div class="scrim" hidden></div>
<script src="assets/wiki.js" defer></script>
</body>
</html>
"""


def jsonld(page: Page) -> str:
    """Structured data: the site once, then the page, then its trail."""
    graph: list[dict] = []
    if page.slug == "index":
        graph.append({
            "@type": "SoftwareApplication",
            "name": "Spagitty",
            "applicationCategory": "DeveloperApplication",
            "operatingSystem": "Linux, macOS, Windows",
            "description": "A local-first desktop Git client for repositories where people and "
                           "coding agents commit side by side, and the gateway to a Git-managed agent farm.",
            "url": SITE,
            "downloadUrl": f"{REPO}/releases/latest",
            "license": "https://www.gnu.org/licenses/gpl-3.0.html",
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        })
    graph.append({
        "@type": "TechArticle",
        "headline": page.title,
        "description": page.description,
        "url": page.url,
        "inLanguage": "en",
        "dateModified": BUILT,
        "isPartOf": {"@type": "WebSite", "name": "Spagitty Wiki", "url": SITE},
        "author": {"@type": "Organization", "name": "The Spagitty Authors"},
    })
    trail = [{"@type": "ListItem", "position": 1, "name": "Wiki", "item": SITE}]
    if page.slug != "index":
        trail.append({"@type": "ListItem", "position": 2, "name": page.nav, "item": page.url})
    graph.append({"@type": "BreadcrumbList", "itemListElement": trail})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=None)


def render(page: Page) -> str:
    raw = (CONTENT / f"{page.slug}.html").read_text(encoding="utf-8")
    body, headings = anchorise(raw)
    return SHELL.format(
        title=html.escape(page.title if page.slug == "index" else f"{page.title} · Spagitty Wiki"),
        description=html.escape(page.description),
        keywords=html.escape(", ".join(page.keywords)),
        url=page.url,
        site=SITE,
        repo=REPO,
        wiki_repo=WIKI_REPO,
        og_type="website" if page.slug == "index" else "article",
        jsonld=jsonld(page),
        sidebar=sidebar(page.slug),
        toc=toc(headings),
        body=body,
        pager=neighbours(page.slug),
        built=BUILT,
    )


def search_index() -> str:
    """A flat index the browser filters. Small enough to ship whole."""
    rows = []
    for page in PAGES:
        raw = (CONTENT / f"{page.slug}.html").read_text(encoding="utf-8")
        _, headings = anchorise(raw)
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S)
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
        text = re.sub(r"\s+", " ", text).strip()
        rows.append({
            "t": page.title,
            "n": page.nav,
            "u": page.filename,
            "s": page.section,
            "d": page.description,
            "h": [{"i": i, "t": t} for lvl, i, t in headings if lvl in ("2", "3")],
            "b": text[:6000],
        })
    return json.dumps(rows, separators=(",", ":"))


def sitemap() -> str:
    urls = "\n".join(
        "  <url>\n"
        f"    <loc>{p.url}</loc>\n"
        f"    <lastmod>{BUILT}</lastmod>\n"
        "    <changefreq>weekly</changefreq>\n"
        f"    <priority>{p.priority}</priority>\n"
        "  </url>"
        for p in PAGES
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9"\n'
        '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
        f"{urls}\n"
        "</urlset>\n"
    ).replace("www.sitemap.org", "www.sitemaps.org")


def robots() -> str:
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {SITE}/sitemap.xml\n"
    )


def main() -> int:
    check = "--check" in sys.argv
    written: dict[Path, str] = {}

    for page in PAGES:
        written[ROOT / page.filename] = render(page)
    written[ROOT / "sitemap.xml"] = sitemap()
    written[ROOT / "robots.txt"] = robots()
    written[ROOT / "assets" / "search-index.json"] = search_index()

    stale = []
    for path, text in written.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == text:
            continue
        stale.append(path.relative_to(ROOT))
        if not check:
            path.write_text(text, encoding="utf-8")

    if check:
        if stale:
            print("stale output, run `python3 build.py`:")
            for p in stale:
                print(f"  {p}")
            return 1
        print(f"{len(written)} files up to date")
        return 0

    print(f"built {len(PAGES)} pages, sitemap, robots.txt and the search index")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
