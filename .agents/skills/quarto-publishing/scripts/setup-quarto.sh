#!/usr/bin/env bash
#
# setup-quarto.sh — install and verify the Quarto CLI inside a project .venv.
#
# Run this script; do not just read it. It creates the virtual environment when
# missing, installs quarto-cli at a pinned version, installs the Jupyter
# dependencies Quarto needs for computational documents, then runs both
# diagnostics and reports a clear pass/fail result.
#
# Usage:
#   bash .agents/skills/quarto-publishing/scripts/setup-quarto.sh
#   bash .agents/skills/quarto-publishing/scripts/setup-quarto.sh --help
#
set -euo pipefail

QUARTO_VERSION="1.11.9"
JUPYTER_PACKAGES=(jupyter ipykernel)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"

PROJECT_ROOT=""
SKIP_JUPYTER=0
CHECK_ONLY=0
QUIET_PIP=1

usage() {
  cat <<'EOF'
setup-quarto.sh — install and verify Quarto CLI in a project virtual environment.

USAGE
  bash setup-quarto.sh [options]

OPTIONS
  -h, --help              Show this help and exit.
  -r, --project-root DIR  Use DIR as the project root (default: auto-detect).
  -c, --check-only        Skip installs; only run the existing diagnostics.
      --skip-jupyter      Install Quarto only, not jupyter/ipykernel.
  -v, --verbose           Show full pip output.

WHAT IT DOES
  1. Locates the project root (directory containing .venv, .git, or AGENTS.md).
  2. Creates .venv with python3 when the directory does not exist.
  3. Installs "quarto-cli==1.11.9" into .venv.
  4. Installs jupyter and ipykernel into .venv.
  5. Runs ".venv/bin/quarto --version", "quarto check", and "quarto check jupyter".
  6. Prints the exact export line for QUARTO_PYTHON.

EXIT STATUS
  0  Everything installed and both diagnostics passed.
  1  A step failed; the failing command and reason are printed.
  2  Invalid arguments.

EXAMPLES
  bash setup-quarto.sh
  bash setup-quarto.sh --project-root ~/Downloads/QodeFest
  bash setup-quarto.sh --check-only
EOF
}

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[ok]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m[fail]\033[0m %s\n' "$*" >&2; exit 1; }

need_value() {
  [[ $# -ge 2 && -n "${2:-}" ]] || fail "Option $1 requires a value. Run --help."
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    -r|--project-root) need_value "$1" "${2:-}"; PROJECT_ROOT="$2"; shift 2 ;;
    -c|--check-only) CHECK_ONLY=1; shift ;;
    --skip-jupyter) SKIP_JUPYTER=1; shift ;;
    -v|--verbose) QUIET_PIP=0; shift ;;
    *) printf 'Unknown option: %s\n\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

detect_root() {
  local dir="$SKILL_DIR"
  while [[ "$dir" != "/" ]]; do
    if [[ -d "$dir/.venv" || -d "$dir/.git" || -f "$dir/AGENTS.md" ]]; then
      printf '%s\n' "$dir"
      return 0
    fi
    dir="$(dirname -- "$dir")"
  done
  printf '%s\n' "$PWD"
}

if [[ -z "$PROJECT_ROOT" ]]; then
  PROJECT_ROOT="$(detect_root)"
else
  [[ -d "$PROJECT_ROOT" ]] || fail "Project root does not exist: $PROJECT_ROOT"
  PROJECT_ROOT="$(cd -- "$PROJECT_ROOT" && pwd -P)"
fi

VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
QUARTO_BIN="$VENV_DIR/bin/quarto"

printf '\nQuarto setup — %s\n' "$PROJECT_ROOT"
printf 'Pinned version: quarto-cli==%s\n\n' "$QUARTO_VERSION"

# --- 1. Platform and interpreter preflight -----------------------------------
case "$(uname -s)" in
  Darwin|Linux) ;;
  *) warn "Untested platform: $(uname -s). Continuing." ;;
esac

# --- 2. Virtual environment ---------------------------------------------------
if [[ -x "$PYTHON_BIN" ]]; then
  ok "Virtual environment found: $VENV_DIR ($("$PYTHON_BIN" --version 2>&1))"
else
  if (( CHECK_ONLY )); then
    fail "No virtual environment at $VENV_DIR and --check-only was requested."
  fi
  command -v python3 >/dev/null 2>&1 || fail "python3 not found on PATH."
  log "Creating virtual environment at $VENV_DIR"
  python3 -m venv "$VENV_DIR" || fail "venv creation failed."
  ok "Created $VENV_DIR ($("$PYTHON_BIN" --version 2>&1))"
fi

# --- 3. Install pinned Quarto CLI --------------------------------------------
if (( CHECK_ONLY )); then
  log "Skipping installs (--check-only)"
  [[ -x "$QUARTO_BIN" ]] && ok "Quarto binary present: $QUARTO_BIN" \
    || warn "Quarto binary missing: $QUARTO_BIN"
else
  log "Upgrading pip"
  pip_args=(--disable-pip-version-check)
  if (( QUIET_PIP )); then
    pip_args+=(--quiet)
  fi
  "$PYTHON_BIN" -m pip install "${pip_args[@]}" --upgrade pip \
    || fail "pip upgrade failed."

  log "Installing quarto-cli==$QUARTO_VERSION"
  "$PYTHON_BIN" -m pip install "${pip_args[@]}" "quarto-cli==$QUARTO_VERSION" \
    || fail "Install of quarto-cli==$QUARTO_VERSION failed."
  ok "Installed quarto-cli==$QUARTO_VERSION"

  if (( SKIP_JUPYTER )); then
    warn "Skipping jupyter/ipykernel (--skip-jupyter); computational documents will not render."
  else
    log "Installing ${JUPYTER_PACKAGES[*]}"
    "$PYTHON_BIN" -m pip install "${pip_args[@]}" "${JUPYTER_PACKAGES[@]}" \
      || fail "Install of ${JUPYTER_PACKAGES[*]} failed."
    ok "Installed ${JUPYTER_PACKAGES[*]}"
  fi
fi

[[ -x "$QUARTO_BIN" ]] || fail "Quarto binary not executable: $QUARTO_BIN. Re-run without --check-only."

# --- 4. Version verification --------------------------------------------------
REPORTED_VERSION="$("$QUARTO_BIN" --version 2>/dev/null | head -n 1 | tr -d '[:space:]')"
if [[ "$REPORTED_VERSION" == "$QUARTO_VERSION" ]]; then
  ok "Quarto version matches pin: $REPORTED_VERSION"
elif [[ -z "$REPORTED_VERSION" ]]; then
  fail "'quarto --version' returned nothing. The install is broken; delete $VENV_DIR and re-run."
else
  warn "Quarto reports $REPORTED_VERSION but the pin is $QUARTO_VERSION. Reinstall the pinned package."
fi

export QUARTO_PYTHON="$PYTHON_BIN"

# --- 5. Diagnostics -----------------------------------------------------------
CHECK_LOG="$(mktemp -t quarto-check)"
trap 'rm -f "$CHECK_LOG"' EXIT

log "Running: quarto check"
if "$QUARTO_BIN" check >"$CHECK_LOG" 2>&1; then
  ok "quarto check passed"
else
  sed -n '1,40p' "$CHECK_LOG" >&2
  fail "quarto check failed. Full output above; see reference.md known failure modes."
fi

if (( SKIP_JUPYTER )); then
  warn "Skipping 'quarto check jupyter' (--skip-jupyter)"
elif "$QUARTO_BIN" check jupyter >"$CHECK_LOG" 2>&1; then
  ok "quarto check jupyter passed"
else
  sed -n '1,40p' "$CHECK_LOG" >&2
  fail "quarto check jupyter failed. Install jupyter and ipykernel, then set QUARTO_PYTHON=$QUARTO_PYTHON."
fi

# --- 6. Version pin reminder --------------------------------------------------
PINNED=0
for f in "$PROJECT_ROOT/constraints.txt" "$PROJECT_ROOT/requirements.txt" "$PROJECT_ROOT/requirements-dev.txt"; do
  if [[ -f "$f" ]] && grep -q 'quarto-cli' "$f" 2>/dev/null; then
    ok "Version pinned in $(basename "$f")"
    PINNED=1
    break
  fi
done
if (( PINNED == 0 )); then
  warn "quarto-cli is not pinned in requirements.txt or constraints.txt. Add this line:"
  printf '     quarto-cli==%s\n' "$QUARTO_VERSION"
fi

# --- 7. Summary ---------------------------------------------------------------
printf '\n'
ok "Quarto is ready in $VENV_DIR"
printf '   binary : %s\n' "$QUARTO_BIN"
printf '   version: %s\n' "$REPORTED_VERSION"
printf '   python : %s\n' "$PYTHON_BIN"
printf '\nNext steps:\n'
printf '   export QUARTO_PYTHON="%s"\n' "$PYTHON_BIN"
printf '   %s check jupyter\n' "$QUARTO_BIN"
printf '   %s preview index.qmd\n' "$QUARTO_BIN"
printf '   %s render index.qmd --to html\n' "$QUARTO_BIN"
printf '\nKeep _site/, _book/, and _output/ out of git.\n'
