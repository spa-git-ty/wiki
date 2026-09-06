<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# The Spagitty wiki

The documentation site for [Spagitty](https://github.com/spa-git-ty/spagitty) — a
local-first desktop Git client and the gateway to a Git-managed agent farm.

**Live:** <https://spa-git-ty.github.io/wiki/>

It is a static site with no runtime dependencies: plain HTML, one stylesheet, one
small script. Nothing is fetched from a CDN and nothing is tracked.

## How it is put together

Every page is a body fragment in `content/`. `build.py` wraps each one in the
shared shell — head, sidebar, header, table of contents, footer — and writes it to
the repository root, where GitHub Pages serves it.

```
content/<slug>.html   the page body — write here
build.py              the page registry, the shell, the sitemap, the search index
assets/wiki.css       the whole design system, as tokens on :root
assets/wiki.js        theme switch, navigation drawer, scroll-spy, search
assets/brand/         the mark, lockup and favicons, from the product repository
assets/screens/       screenshots, from the product repository
<slug>.html           generated — do not edit
sitemap.xml           generated
robots.txt            generated
assets/search-index.json   generated
```

The page registry in `build.py` is the single source of truth for navigation
order, titles, descriptions, keywords and the sitemap.

## Editing

1. Edit the fragment in `content/`, or add a new one.
2. If it is a new page, add a `Page(...)` row to `PAGES` in `build.py` — that is
   what puts it in the sidebar, the sitemap and the search index.
3. Rebuild, and commit both the fragment and the generated page:

```sh
python3 build.py
```

Check that the committed output is current without writing anything:

```sh
python3 build.py --check
```

Nothing beyond Python 3 is needed. To preview locally:

```sh
python3 -m http.server 8000
```

### Writing a fragment

Fragments are ordinary HTML — no front matter, no template language. Headings get
their `id`, their self-link and their table-of-contents entry at build time, so
write plain `<h2>` and `<h3>`. A few classes carry the design:

| Class | For |
| --- | --- |
| `.lede` | The opening paragraph. |
| `.eyebrow` | The small section label above an `<h1>`. |
| `.note` `.tip` `.rule` `.warn` | Callouts. Put a `<span class="note-label">` first. |
| `.cards` / `.card` | A grid of links. |
| `.modules` with `.m-path` / `.m-what` | A code-map row: path on the left, what it holds on the right. |
| `.layers` / `.layer` | The stacked architecture diagram. |
| `.swatches` / `.swatch` | Colour swatches. |
| `.screen-code` | The `1A`-style screen badge. |
| `.meta-row` | The small monospace line of file paths under a screen heading. |

Tables are wrapped in a horizontal scroller at runtime, so plain `<table>` is
fine.

## Publishing

The site is committed in its built form, so either Pages source works:

- **Deploy from a branch** — `main`, root. Nothing else to configure.
- **GitHub Actions** — `.github/workflows/pages.yml` runs `build.py --check`
  first and then publishes. Use this one if you want a stale page to fail the
  build rather than ship.

`.nojekyll` is present so the files are served exactly as committed.

## Keeping it true

The wiki describes the product repository, and the product repository is the
authority. When something changes there — a screen, a module, a gate, a brand
rule — the corresponding page here changes with it. A page describing something
that no longer exists is a defect, the same as it is over there.

The pages that track the source most closely, and so drift first:

| Page | Tracks |
| --- | --- |
| `screens.html` | `docs/screens.md` and `src/lib/nav.ts` |
| `architecture.html` | `docs/architecture.md` |
| `core-crate.html` · `farm-crate.html` · `tauri-layer.html` · `frontend.html` | The module headers themselves |
| `ipc.html` | The command registration in `src-tauri/src/lib.rs` |
| `ci.html` | `.github/workflows/` |
| `branding.html` | `docs/branding.md` |
| `releases.html` | `CHANGELOG.md` |

## Licence

GPL-3.0-or-later, the same as Spagitty. Brand assets are copied from the product
repository and carry the rules in [`branding.html`](branding.html): the mark is
never redrawn, and the Git logo and Git orange are never used.
