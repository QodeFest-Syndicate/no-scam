# Quarto Publishing Reference

Detailed configuration for the `quarto-publishing` skill. Every command assumes the project venv binary: `.venv/bin/quarto`.

## Contents

1. [YAML front matter by format](#yaml-front-matter-by-format)
2. [Execution control](#execution-control)
3. [Extensions](#extensions)
4. [Publishing targets](#publishing-targets)
5. [Multi-format rendering](#multi-format-rendering)
6. [Custom templates](#custom-templates)
7. [Observable JS](#observable-js)
8. [Embedded interactivity](#embedded-interactivity)
9. [Environment variables](#environment-variables)
10. [CI/CD integration](#cicd-integration)
11. [Freeze and execution recipes](#freeze-and-execution-recipes)

## YAML Front Matter by Format

Common keys apply everywhere; format-specific keys nest under the format name.

```yaml
---
title: "Document Title"
subtitle: "Optional subtitle"
author:
  - name: "Author One"
    affiliation: "Data Platform"
date: "2026-11-19"
date-modified: last-modified
abstract: "One-paragraph summary."
keywords: [latency, platform, slo]
lang: en
format: html
---
```

### HTML

```yaml
format:
  html:
    theme: cosmo              # or a .scss file, or {light: flatly, dark: darkly}
    toc: true
    toc-depth: 3
    toc-location: right
    number-sections: true
    code-fold: true
    code-tools: true
    code-copy: true
    code-overflow: wrap
    fig-cap-location: bottom
    tbl-cap-location: top
    embed-resources: true     # single self-contained file
    smooth-scroll: true
    link-external-icon: true
    df-print: paged
    max-width: 1100px
    css: styles/site.css
```

`embed-resources: true` inlines CSS, JS, and images. Use it for email-ready or archivally stable single files; leave it off for multi-page sites.

### PDF via Typst

Typst needs no TeX install. Set the format, then render with `--to pdf` (Quarto maps `typst` output to PDF).

```yaml
format:
  typst:
    toc: true
    toc-depth: 2
    number-sections: true
    papersize: a4
    margin:
      x: 2.2cm
      y: 2.4cm
    fontsize: 10pt
    section-numbering: "1.1"
    columns: 1
    include-in-header:
      - typst/header.typ
    template: typst/custom.typ   # optional custom template
```

### PDF via LaTeX

Only when a journal template or LaTeX-only package is required.

```yaml
format:
  pdf:
    documentclass: article
    papersize: letter
    geometry:
      - top=1in
      - bottom=1in
      - left=1in
      - right=1in
    fontsize: 11pt
    linestretch: 1.15
    number-sections: true
    colorlinks: true
    cite-method: natbib
    include-in-header:
      text: |
        \usepackage{microtype}
```

Install TeX only on demand: `.venv/bin/quarto install tinytex`.

### Word

```yaml
format:
  docx:
    toc: true
    number-sections: true
    reference-doc: templates/reference.docx
    highlight-style: github
    fig-width: 6
    fig-height: 4
```

Generate a style reference from an existing document: `.venv/bin/quarto pandoc -o templates/reference.docx --print-default-data-file reference.docx`.

### Reveal.js

```yaml
format:
  revealjs:
    theme: moon
    slide-number: true
    chalkboard: true
    preview-links: auto
    incremental: false
    transition: slide
    width: 1280
    height: 720
    footer: "Platform Review — 2026"
    controls: true
    progress: true
```

Slide breaks: `## Section` for horizontal, `### Subsection` for vertical. Add `::: {.notes}` blocks for speaker notes.

### PowerPoint

```yaml
format:
  pptx:
    reference-doc: templates/brand.pptx
    slide-level: 2
    incremental: false
```

### Dashboard

```yaml
format:
  dashboard:
    theme: cosmo
    scrolling: false
    orientation: rows
```

Dashboard pages use `## Page Title {.tabset}` style headings or level-1 headings per page, with value boxes and cards:

```markdown
::: {.valuebox}
99.95%
[SLO attainment]{.small}
:::
```

### Book

```yaml
project:
  type: book
  output-dir: _book

book:
  title: "Platform Handbook"
  author: "Data Platform Team"
  date: "2026-11-19"
  chapters:
    - index.qmd
    - part: "Foundations"
      chapters:
        - chapters/architecture.qmd
        - chapters/contracts.qmd
  appendices:
    - appendices/glossary.qmd
  downloads: [pdf, epub]
  search: true
  repo-url: https://github.com/org/repo
```

### Website

```yaml
project:
  type: website
  output-dir: _site

website:
  title: "Platform Docs"
  site-url: https://docs.example.com
  repo-url: https://github.com/org/docs
  navbar:
    background: "#1f2a37"
    left:
      - href: index.qmd
        text: Home
      - href: guides/index.qmd
        text: Guides
  sidebar:
    style: docked
    contents: guides
  page-footer:
    left: "© 2026 Data Platform"
    right: "Built with Quarto"
  search:
    location: navbar
    type: overlay
  google-analytics: "G-XXXXXXX"
```

## Execution Control

Execution settings live in document YAML, project `_quarto.yml`, or the CLI.

| Option | Scope | Effect |
|---|---|---|
| `execute: true` / `false` | Document or project | Force or forbid code execution |
| `execute: {enabled: false}` | Project | Render pre-computed outputs only |
| `execute: {echo: true}` | Document | Show source alongside output |
| `execute: {warning: false}` | Document | Suppress warnings in output |
| `execute: {error: false}` | Document | Fail fast instead of continuing |
| `execute: {cache: true}` | Document | Reuse results when inputs and code are unchanged |
| `execute: {freeze: true}` | Project | Recompute only changed documents |
| `execute: {daemon: true}` | Project | Keep a persistent kernel for fast rebuilds |
| `execute: {daemon: 300}` | Project | Daemon with 300-second idle timeout |
| `execute: {execute-dir: project}` | Project | Run code from project root instead of file directory |
| `execute: {working-dir: .}` | Document | Override working directory |
| `--execute` | CLI | Execute even if YAML disables it |
| `--no-execute` | CLI | Skip execution, keep stored outputs |

Cache is per document and keyed on code plus tracked inputs. `freeze` is project-wide and stores results under `_freeze/`. Commit `_freeze/` when CI must render without executing.

Chunk-level options in a Python cell:

````markdown
```{python}
#| label: tbl-regions
#| echo: false
#| output: asis
#| warning: false
#| message: false
#| cache: true
#| fig-cap: "Regions by throughput"
#| tbl-cap: "Throughput table"
#| fig-format: svg
#| fig-dpi: 300
#| out-width: "90%"
```
````

## Extensions

Extensions add shortcodes, filters, formats, journal templates, and reveal.js plugins.

```bash
# From the project root only
.venv/bin/quarto add quarto-ext/fontawesome
.venv/bin/quarto add quarto-journals/apa
.venv/bin/quarto add quarto-ext/lightbox

.venv/bin/quarto list extensions        # installed
.venv/bin/quarto update extension <id>  # upgrade
.venv/bin/quarto remove extension <id>  # uninstall
```

Commit the `_extensions/` directory so every machine and CI runner resolves the same versions.

### Shortcodes

Built-in:

| Shortcode | Purpose |
|---|---|
| `{{< var name >}}` | Insert a value from `_variables.yml` |
| `{{< include _file.md >}}` | Inline another Markdown file |
| `{{< video path.mp4 >}}` | Embed video with responsive wrapper |
| `{{< embed notebook.ipynb#fig-1 >}}` | Reuse a cell from another document |
| `{{< pagebreak >}}` | Force a page or slide break |
| `{{< kbd Ctrl+C >}}` | Keyboard key rendering |
| `{{< fa database >}}` | Font Awesome icon (after `quarto add`) |
| `{{< lipsum 2 >}}` | Placeholder paragraphs |

### Filters

Lua filters declared per document or project:

```yaml
filters:
  - _extensions/custom/word-count.lua
  - quarto
```

Filters run in order; `quarto` must stay last to apply built-in post-processing.

### Journal Templates

```bash
.venv/bin/quarto add quarto-journals/jasa
```

```yaml
format:
  jasa-pdf: default
```

Templates bring their own `format` names, required YAML keys, and submission structure. Read the extension `README.md` under `_extensions/` before overriding its defaults.

## Publishing Targets

```bash
.venv/bin/quarto publish gh-pages   # GitHub Pages
.venv/bin/quarto publish netlify    # Netlify
.venv/bin/quarto publish quarto-pub # Quarto Pub
.venv/bin/quarto publish connect    # Posit Connect
```

| Target | Requirements | Notes |
|---|---|---|
| GitHub Pages | Git remote, `gh-pages` branch or Actions | Renders, pushes `_site/` to `gh-pages` |
| Netlify | `netlify` CLI authenticated, site linked | Uses `_site/` as publish dir |
| Quarto Pub | Posit account authenticated | Fastest public sharing path |
| Posit Connect | Server URL plus API key | Enterprise content hosting |
| Cloudflare Pages / Vercel | Build command `quarto render` | Publish `_site/` as static output |

Non-interactive credentials for CI come from environment variables (`NETLIFY_AUTH_TOKEN`, `CONNECT_SERVER`, `CONNECT_API_KEY`, `QUARTO_PUB_TOKEN`). Never hard-code them in `_quarto.yml`.

## Multi-Format Rendering

Declare several formats and render them in one pass:

```yaml
format:
  html:
    toc: true
  typst:
    toc: true
  docx:
    toc: true
```

```bash
.venv/bin/quarto render report.qmd                    # all declared formats
.venv/bin/quarto render report.qmd --to html,typst    # subset
.venv/bin/quarto render report.qmd --to html --output report-draft.html
```

Conditional content by format:

```markdown
::: {.content-visible when-format="html"}
Interactive version with live filters.
:::

::: {.content-visible when-format="typst"}
Static table for print.
:::
```

Or in a code cell:

```python
#| eval: true
#| output: asis
import os
fmt = os.environ.get("QUARTO_FORMAT", "html")
print("HTML-only note" if fmt == "html" else "")
```

Keep format matrices small. Each extra format doubles render time and drift surface.

## Custom Templates

### Typst

1. Generate a starter: `.venv/bin/quarto create template mysite --type typst` (or copy an existing `.typ` template).
2. Place it at `templates/custom.typ` with a matching `template.typ` partial layout.
3. Reference it in YAML: `format: {typst: {template: templates/custom.typ}}`.

Template variables arrive as `$title$`, `$author$`, `$date$`, and `$body$`. Brand colors and fonts belong in the template, not in every document header.

### LaTeX

```yaml
format:
  pdf:
    template: templates/article.tex
    template-partials:
      - templates/before-body.tex
      - templates/title.tex
```

Pandoc template syntax uses `$if(...)$` conditionals and `$for(...)$` loops. Keep partials under version control beside the main template.

### Word Reference Document

Open `templates/reference.docx`, edit styles (`Title`, `Heading 1-3`, `Body Text`, `Source Code`), save, and set `reference-doc`. Quarto copies those styles onto generated content.

## Observable JS

OJS runs in the browser; no Python kernel required. Wrap code in `{ojs}` blocks.

````markdown
```{ojs}
data = FileAttachment("data/metrics.csv").csv()
```

```{ojs}
Inputs.table(data.filter(d => d.region === "eu-west"))
```
````

```{ojs}
viewof threshold = Inputs.range([0, 500], {value: 200, step: 10, label: "p95 threshold (ms)"})
```

```{ojs}
Plot.plot({
  marks: [
    Plot.barY(data, {x: "region", y: "p95", fill: d => d.p95 > threshold ? "#b42318" : "#1d4ed8"}),
    Plot.ruleY([threshold])
  ]
})
```

Enable syntax highlighting and library control:

```yaml
format:
  html:
    ojs: true
    code-fold: true
    lib-dir: libs
```

OJS cannot read the local filesystem beyond `FileAttachment` paths served with the page, and cannot import Python objects. Use it for dashboards and lightweight exploration; use Python for heavy computation.

## Embedded Interactivity

| Library | Enables | Requirement |
|---|---|---|
| Plotly | Interactive charts | `pip install plotly`, `fig.show()` with the plotly renderer |
| Bokeh | Linked brushing, serverless widgets | `pip install bokeh`, `output_notebook()` |
| Altair | Declarative Vega-Lite charts | `pip install altair` |
| ipywidgets | Sliders, dropdowns, tabs | `pip install ipywidgets`, `jupyter nbextension enable` not required in Quarto |
| htmlwidgets | R widget bridging | R plus `QUARTO_R` configured |
| Leaflet | Maps | `pip install folium` |
| Great Tables | Publication tables | `pip install great_tables`, `GT(...)` |

Static-first default:

```yaml
format:
  html:
    embed-resources: false
  docx:
    default: true
```

Widgets degrade to static images or nothing in PDF and Word. Guard with `when-format` blocks so print output stays readable.

## Environment Variables

| Variable | Purpose | Typical value |
|---|---|---|
| `QUARTO_PYTHON` | Python interpreter for jupyter kernels | `$PWD/.venv/bin/python` |
| `QUARTO_R` | R interpreter for knitr documents | `/usr/local/bin/R` |
| `QUARTO_DENO` | Deno binary used internally | bundled with the venv package |
| `QUARTO_PROFILE` | Activate a `_quarto-<profile>.yml` overlay | `prod` |
| `QUARTO_PROJECT_DIR` | Force the project root | `$PWD` |
| `QUARTO_LOG_LEVEL` | Diagnostic verbosity | `debug` |
| `QUARTO_CHROMIUM` | Browser used for PDF and screenshots | Chromium path |
| `QUARTO_PANDOC` | Override the bundled Pandoc | absolute path |
| `QUARTO_TINYTEX` | TeX installation location | `~/.TinyTeX` |

Set them per command rather than globally in shell profiles:

```bash
QUARTO_PYTHON="$PWD/.venv/bin/python" QUARTO_PROFILE=prod \
  .venv/bin/quarto render report.qmd --to typst
```

## CI/CD Integration

GitHub Actions job that pins the CLI, installs inside the repo venv, and publishes artifacts:

```yaml
name: render-docs
on:
  push:
    branches: [main]
  pull_request:

jobs:
  render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install Quarto and Jupyter
        run: |
          python -m venv .venv
          .venv/bin/python -m pip install --upgrade pip
          .venv/bin/python -m pip install "quarto-cli==1.11.9" jupyter ipykernel

      - name: Diagnostics
        run: |
          .venv/bin/quarto check
          .venv/bin/quarto check jupyter

      - name: Render
        env:
          QUARTO_PYTHON: ${{ github.workspace }}/.venv/bin/python
          QUARTO_PROFILE: prod
        run: .venv/bin/quarto render --to html

      - uses: actions/upload-artifact@v4
        with:
          name: site
          path: _site/
```

Practical rules for pipelines:

1. Pin `quarto-cli==1.11.9` in the install step, never `latest`.
2. Cache `.venv` and `_freeze/` keyed on the lock or requirements hash.
3. Run `quarto check jupyter` before `render`; a missing kernel fails ten minutes later otherwise.
4. Commit `_freeze/` when the runner lacks data access, then render with `--no-execute`.
5. Upload the output directory as an artifact and let a separate job deploy it.
6. Fail the job on warnings only after the suite is clean: `quarto render 2>&1 | tee render.log`.

Netlify build settings:

```toml
[build]
  command = "python -m venv .venv && .venv/bin/python -m pip install 'quarto-cli==1.11.9' jupyter ipykernel && .venv/bin/quarto render"
  publish = "_site"
```

## Freeze and Execution Recipes

| Goal | Configuration |
|---|---|
| Fast local iteration on prose | `execute: {enabled: false}` plus `--no-execute` |
| Recompute only changed chapters | `execute: {freeze: true}` in `_quarto.yml` |
| Persistent kernel for dashboards | `execute: {daemon: true}` |
| Reproducible CI without data access | commit `_freeze/`, render with `--no-execute` |
| Force a full recompute | delete `_freeze/` and `_site/`, rerun `quarto render` |
| Execute from project root so relative data paths resolve | `execute: {execute-dir: project}` |

Inspect what Quarto resolved before debugging output paths:

```bash
.venv/bin/quarto inspect report.qmd | head -40
.venv/bin/quarto inspect project
```

## Known Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| `_freeze` present but outputs stale | freeze skipped a changed dependency | delete the document's entry under `_freeze/` and rerender |
| Dashboard cards overflow | fixed `scrolling: false` with tall content | set `scrolling: true` or shorten card content |
| Typst PDF drops table borders | template overrides `table.stroke` | restore stroke in the custom template |
| Reveal.js slide content clipped | fixed `width`/`height` with dense slides | increase canvas size or split the slide |
| `embed-resources` inflates file to tens of MB | large images and libraries inlined | keep `embed-resources: false` for sites |
| Website 404s on subpages | relative links mixed with `site-url` | use root-relative hrefs inside `_quarto.yml` navigation |
| Extension changes ignored | stale `_extensions/` cache | `quarto update extension <id>`, then rerender |
| LaTeX build fails on missing package | TinyTeX minimal install | `tlmgr install <package>` inside TinyTeX |
