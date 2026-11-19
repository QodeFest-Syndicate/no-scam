---
name: quarto-publishing
description: Render, preview, and publish scientific and technical documents using Quarto CLI installed via pip in the project virtual environment. Use when creating or rendering .qmd files, Jupyter notebooks to HTML/PDF/Word/slides, building Quarto websites/books/dashboards, managing Quarto extensions, or when the user mentions Quarto, document publishing, or technical report generation.
---

# Quarto Publishing

Render `.qmd` and `.ipynb` sources to HTML, PDF, Word, slides, dashboards, books, and websites with the Quarto CLI that lives inside the project `.venv`.

## Activation Contract

Load this skill when the task includes any of:

| Trigger | Typical request |
|---|---|
| `.qmd` file work | "Create a report document", "fix the YAML header" |
| Notebook publishing | "Turn this notebook into HTML", "render the analysis" |
| Technical or scientific docs | "Generate a PDF whitepaper", "render with citations" |
| Slides and presentations | "Make reveal.js slides from this analysis" |
| Dashboards | "Build an interactive dashboard" |
| Books and websites | "Set up a multi-chapter book", "build the docs site" |
| Extensions | "Add a journal template", "install a shortcode" |
| Publishing | "Publish to GitHub Pages", "deploy to Netlify" |

Do not load this skill for Markdown that never enters a Quarto project, or for DOCX/PDF editing that does not involve rendering.

## Environment Setup

Quarto is installed as a Python package inside `.venv`. Never rely on a global `quarto` on `PATH`.

| Step | Command |
|---|---|
| Install pinned CLI | `.venv/bin/python -m pip install "quarto-cli==1.11.9"` |
| Install compute dependencies | `.venv/bin/python -m pip install jupyter ipykernel` |
| Verify binary | `.venv/bin/quarto --version` (expect `1.11.9`) |
| Full diagnostic | `.venv/bin/quarto check` |
| Compute diagnostic | `.venv/bin/quarto check jupyter` |

Prefer running `scripts/setup-quarto.sh` for the whole sequence. It creates `.venv` when missing, installs the pinned CLI, registers the kernel, runs both diagnostics, and exits non-zero on failure.

```bash
bash .agents/skills/quarto-publishing/scripts/setup-quarto.sh
bash .agents/skills/quarto-publishing/scripts/setup-quarto.sh --help
```

Two ways to invoke the binary after setup:

1. Absolute path: `.venv/bin/quarto render report.qmd` — deterministic, works in any shell.
2. Activated venv: `source .venv/bin/activate && quarto render report.qmd`.

Set `QUARTO_PYTHON` so kernels bind to the project interpreter:

```bash
export QUARTO_PYTHON="$(pwd)/.venv/bin/python"
```

## Mandatory Invariants

1. Always use the project venv's quarto executable, never a system-wide one.
2. Pin quarto-cli version in requirements/constraints files.
3. Verify `quarto check jupyter` passes before rendering computational documents.
4. Prefer Typst over LaTeX for PDF output (bundled, no TeX install needed).
5. Run `quarto render` with an explicit `--to` format flag for deterministic output.
6. Inspect `_quarto.yml` before modifying any project-level configuration.
7. Never commit rendered output directories (`_site/`, `_book/`, `_output/`) — add to `.gitignore`.

## Work Loop

1. **Verify the environment.** Run `.venv/bin/quarto --version` and `.venv/bin/quarto check jupyter`. Stop and run the setup script if either fails.
2. **Inspect the source.** Read the document's YAML header and its `_quarto.yml`. Run `.venv/bin/quarto inspect <file>` to see the resolved format, output path, and execution settings.
3. **Resolve the format.** Pick the target from the Output Formats table. Default to `html` for review, `typst` for PDF, `docx` for human editing, `revealjs` for talks.
4. **Render with an explicit format.** `.venv/bin/quarto render <file> --to <format>`. Add `--execute` when the document contains code whose outputs must be regenerated.
5. **Inspect the artifact.** Open the emitted file (`open _site/<name>.html`, `open <name>.pdf`). Confirm figures, cross-references, and tables resolved.
6. **Report.** State source path, output path, format, and any warnings left in the render log.

For iterative drafting, run `.venv/bin/quarto preview <file>` instead of repeating renders. Preview rebuilds on save and prints the local URL.

## Core Commands

| Command | Purpose |
|---|---|
| `quarto render <file>` | Render a single document |
| `quarto render <file> --to html` | Render to specific format |
| `quarto render` | Render entire project |
| `quarto preview <file>` | Live preview with auto-rebuild |
| `quarto inspect <file>` | Show resolved configuration |
| `quarto convert <file>` | Convert between formats |
| `quarto check` | Full installation diagnostic |
| `quarto check jupyter` | Python/Jupyter diagnostic |
| `quarto add <extension>` | Install an extension |
| `quarto publish` | Publish to supported services |
| `quarto install tinytex` | Install TeX (only if LaTeX PDF needed) |

Add `--to <format>`, `--execute`, `--no-execute`, and `-P key:value` (parameters) as needed. `--output <path>` overrides the output filename.

## Output Formats

| Format | Flag | Use when |
|---|---|---|
| HTML | `--to html` | Default; richest features, interactivity, review loops |
| Typst PDF | `--to typst` then `--to pdf` | Print and PDF deliverables without a TeX install |
| LaTeX PDF | `--to pdf` | A journal or template requires LaTeX specifically |
| Word | `--to docx` | Reviewers edit in Word with tracked changes |
| Reveal.js | `--to revealjs` | HTML presentations, interactive, browser-driven |
| PowerPoint | `--to pptx` | Slides handed to corporate template owners |
| Dashboard | `--to dashboard` | Interactive KPI and data dashboards |
| Book | project type `book` | Multi-chapter documents with numbering |
| Website | project type `website` | Multi-page sites with navigation and search |

Set the format in YAML (`format: html`) or pass `--to`. YAML is the source of truth; `--to` selects among declared formats.

## Document Authoring

Minimal document header:

```yaml
---
title: "Quarterly Latency Report"
author: "Data Platform Team"
date: "2026-11-19"
format: html
toc: true
---
```

Computational cell with a cross-referenceable figure:

````markdown
```{python}
#| label: fig-latency
#| fig-cap: "p95 latency by region"
import pandas as pd
df = pd.read_csv("data/latency.csv")
df.plot.bar(x="region", y="p95")
```
````

Then reference it as `@fig-latency` and cite as `[@knuth1984]` with a `references.bib` file listed under `bibliography:`.

Callout block:

```markdown
::: {.callout-warning}
## Data freshness
Figures use a snapshot from 2026-11-18.
:::
```

Parameterized render:

```yaml
params:
  region: eu-west
```

```bash
.venv/bin/quarto render report.qmd --to html -P region:us-east
```

Reusable content and variables:

```markdown
{{< include _shared/methodology.md >}}
```

```yaml
# _variables.yml
version: "2.4.0"
```

```markdown
Release {{< var version >}} ships these figures.
```

Code chunk options use `#|` comments (`#| echo: false`, `#| warning: false`, `#| label:`). Legacy `{python, echo=FALSE}` syntax still works in Jupyter-sourced documents.

## Project Configuration

Create `_quarto.yml` at the project root; every document inherits it.

```yaml
project:
  type: default        # default | website | book | manuscript
  output-dir: _output

format:
  html:
    theme: cosmo
    toc: true
  typst:
    toc: true

execute:
  echo: false
  warning: false
```

Website and book types add `_quarto.yml` navigation instead of an output directory alone:

```yaml
project:
  type: website
  output-dir: _site

website:
  title: "Platform Docs"
  navbar:
    left:
      - href: index.qmd
        text: Home
      - href: guides/index.qmd
        text: Guides
```

```yaml
project:
  type: book
  output-dir: _book

book:
  title: "Data Platform Handbook"
  chapters:
    - index.qmd
    - part: "Ingestion"
      chapters:
        - pipelines/overview.qmd
```

Profiles swap configuration without editing the base file. Create `_quarto-prod.yml` and render with `QUARTO_PROFILE=prod .venv/bin/quarto render`.

## Validation Workflow

Before delivery:

- [ ] `quarto check jupyter` passes
- [ ] `quarto render` completes without errors
- [ ] Output opens correctly in browser/viewer
- [ ] All code cells execute successfully (no stale outputs)
- [ ] Cross-references and citations resolve
- [ ] Images and media render correctly

Run `quarto render` from a clean state when verification matters: `rm -rf _site _output` first, then confirm the directory rebuilds.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `No module named jupyter` | jupyter not in venv | `.venv/bin/python -m pip install jupyter` |
| `kernel not found` | wrong Python selected | `export QUARTO_PYTHON="$PWD/.venv/bin/python"` |
| `LaTeX not found` for PDF | no TeX distribution | set `format: typst`, or `.venv/bin/quarto install tinytex` |
| Stale notebook outputs | execution skipped | add `--execute`, or set `execute: true` in YAML |
| Extension not found | ran outside project root | run `quarto add` from the project root |
| `quarto: command not found` | venv not active | use `.venv/bin/quarto` |
| Render writes to unexpected folder | `output-dir` in `_quarto.yml` | check `quarto inspect <file>` for the resolved path |
| Figures missing in PDF | relative paths resolved from output dir | move assets next to the source or set `resources:` |

## References

- `reference.md` — full YAML option catalog, execution control (cache, freeze, daemon), extensions, publishing targets, multi-format strategies, custom templates, Observable JS, widget embedding, environment variables, CI/CD patterns.
- `scripts/setup-quarto.sh` — executes the install and diagnostics sequence. Run it, do not read it.
