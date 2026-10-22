# Python Setup — Trading Research (Mac M1 / Apple Silicon)

This project uses **uv project mode** to manage Python, dependencies, and the local virtual environment. The initial research workflow is **MetaTrader 5 CSV export → pandas → Parquet → backtesting**. Docker, Windows, and third-party MT5 bridges are not needed for this phase.

**Source of truth:** `pyproject.toml` defines the project's direct dependencies; `uv.lock` records the resolved dependency set; `.python-version` selects Python 3.12. **Do not manually maintain `requirements.txt`** for normal development. Export one only if another tool specifically requires it.

## 1. Project files

| File or directory | Purpose | Git? |
|---|---|---|
| `.python-version` | Preferred Python version (`3.12`) | Yes |
| `pyproject.toml` | Project metadata, Python compatibility, direct and development dependencies | Yes |
| `uv.lock` | Resolved dependency lockfile for reproducible installations | Yes |
| `.venv/` | Machine-local Python environment created by uv | **No** |
| `requirements.txt` | **Optional export** for tools that only accept pip requirements | Only if needed |
| `data/raw/`, `data/processed/` | Historical CSV and processed Parquet data | Usually no |

A lockfile pins the resolved packages, but does not guarantee identical binary behavior on every operating system or CPU architecture. Run validation/tests after changing environments.

## 2. First-time setup on a Mac M1

Install [Homebrew](https://brew.sh/) first if it is not already available. In Terminal:

```bash
brew install uv
cd /path/to/trading-research
```

### A. Starting a new repository

If the project **does not yet contain** `pyproject.toml`:

```bash
uv init --bare              # initialize project metadata without sample application code
uv python pin 3.12          # create/update .python-version
uv add pandas numpy pyarrow matplotlib backtesting pyyaml
uv add --dev pytest jupyterlab
uv sync                    # create/update .venv and uv.lock
```

`uv` may install the selected Python version automatically. To install it explicitly:

```bash
uv python install 3.12
```

**Existing repository warning:** if `pyproject.toml` and `uv.lock` already exist, **do not reinitialize** or replace them; follow the clone/reinstall instructions below.

### B. Cloning or setting up an existing uv repository

```bash
git clone <repository-url>
cd <repository-folder>
uv sync --locked            # restore environment without changing uv.lock
uv run python --version
uv run python -c "import pandas, pyarrow, backtesting; print('Environment OK')"
```

`uv sync --locked` checks that `uv.lock` is consistent with `pyproject.toml`, and errors if it would have to change the lockfile. For stricter CI-style reproducibility, use `uv sync --frozen` only when you intentionally want to trust the existing lock without checking its freshness.

## 3. Daily development (no activation required)

Run commands in the repository root:

```bash
uv run python src/main.py       # if this script exists
uv run pytest
uv run jupyter lab
uv run python --version
```

`uv run` uses the project's managed environment. You can optionally activate it for your shell or an IDE:

```bash
source .venv/bin/activate
python --version
deactivate
```

In VS Code, choose `.venv/bin/python` as the Python interpreter. You do not need to activate the environment when using `uv run`.

## 4. Managing dependencies

```bash
uv add plotly                 # add a runtime package
uv add --dev ruff            # add a development-only tool
uv remove plotly             # remove a dependency
uv sync                      # apply project and lockfile to .venv
uv tree                      # inspect resolved dependencies
```

`uv add` and `uv remove` update `pyproject.toml` and `uv.lock`. Commit **both** files with the change.

Upgrade deliberately, then test:

```bash
uv lock --upgrade-package pandas
uv sync
uv run pytest
```

To upgrade all resolved dependencies (potentially breaking changes):

```bash
uv lock --upgrade
uv sync
uv run pytest
```

A package version constraint in `pyproject.toml` may limit what the resolver can upgrade. Review dependency changes before committing `uv.lock`.

## 5. Reinstall from scratch

In the **correct repository root**, with your code and data safely retained:

```bash
rm -rf .venv                 # deletes only this repository's virtual environment
uv sync --locked             # recreates .venv using .python-version + uv.lock
uv run pytest
```

For a new Mac, install `uv`, clone the project, and run `uv sync --locked`. **Do not delete** `src/`, `data/`, notebooks, or `uv.lock`. If Python 3.12 is unavailable, `uv` can download it; `uv python install 3.12` is also available explicitly.

If you changed `pyproject.toml` on purpose but haven't updated the lock yet, run `uv lock` and then `uv sync` (not `--locked`).

## 6. Creating and understanding the configuration files

### `.python-version`

Generate:

```bash
uv python pin 3.12
```

Its contents should be:

```text
3.12
```

The minor-version pin allows current Python 3.12 patch releases. For even stricter interpreter reproducibility, pin an explicit patch version.

### `pyproject.toml`

The recommended approach is to **let `uv add` write dependencies**, rather than editing versions manually. Example starting file for an application-style research repository:

```toml
[project]
name = "trading-research"
version = "0.1.0"
description = "Historical market-data research and ADR strategy backtesting"
requires-python = ">=3.12,<3.13"
dependencies = [
    "backtesting",
    "matplotlib",
    "numpy",
    "pandas",
    "pyarrow",
    "pyyaml",
]

[dependency-groups]
dev = [
    "jupyterlab",
    "pytest",
]
```

For this research workflow, an installable Python package is not required. If `uv init --bare` generated other valid metadata, keep it instead of copying this example blindly. When you manually edit `pyproject.toml`, run `uv lock && uv sync` to update the environment and commit the changed lockfile.

### `uv.lock`

Generated and maintained by uv:

```bash
uv lock
```

**Commit this file.** Do not hand-edit it. It stores resolved versions and hashes so another developer can recreate a closely matched environment.

## 7. `requirements.txt` compatibility (optional)

Some deployment tools still expect `requirements.txt`. Export it **from uv**, rather than maintaining a separate dependency list:

```bash
uv export --format requirements-txt --output-file requirements.txt
```

To export runtime packages only, without the `dev` dependency group:

```bash
uv export --format requirements-txt --no-dev --output-file requirements.txt
```

Regenerate after dependency changes if another workflow depends on this file. For this repository's normal use, prefer `uv sync` and `uv run`; the exported file is not the primary source of truth.

## 8. Suggested `.gitignore`

```gitignore
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.ipynb_checkpoints/
.DS_Store
.env
.env.*
data/raw/
data/processed/
results/
```

**Commit:** `.python-version`, `pyproject.toml`, `uv.lock`, Python source code, tests, and documentation. **Never commit:** broker account credentials, access tokens, local `.venv/`, or private account exports.

## 9. Troubleshooting

| Symptom | Check / solution |
|---|---|
| `uv: command not found` | Install `uv` with `brew install uv`, then open a new Terminal session. |
| Wrong Python version | Check `.python-version`; run `uv run python --version` and `uv python install 3.12`. |
| Package import missing | Ensure package is declared via `uv add <package>`; run `uv sync`. |
| Environment seems corrupted | Run `rm -rf .venv && uv sync --locked` in the repository root. |
| `uv sync --locked` fails | Your `pyproject.toml` and `uv.lock` disagree; run `uv lock`, inspect the changes, then `uv sync`. |
| VS Code/Jupyter uses the wrong Python | Select `.venv/bin/python`; launch Jupyter with `uv run jupyter lab`. |
| Architecture/build problems | Ensure you're using Apple Silicon ARM64 rather than a Rosetta/x86 shell or interpreter. |
| `.python-version` hidden in Finder | Press Command + Shift + Period to show hidden files. |

## 10. Quick-reference commands

```bash
# New project (once)
brew install uv
uv init --bare
uv python pin 3.12
uv add pandas numpy pyarrow matplotlib backtesting pyyaml
uv add --dev pytest jupyterlab
uv sync

# Everyday work
uv run pytest
uv run jupyter lab

# Add or remove a library
uv add plotly
uv remove plotly

# Clone / reinstall using committed files
uv sync --locked

# Full reset of only the virtual environment
rm -rf .venv && uv sync --locked
```

**Current scope:** offline analysis and backtesting using exported MT5 historical candles. Real-time feeds, the Windows-only official `MetaTrader5` integration, and automated trade execution are separate later-stage decisions.

References: [uv project guide](https://docs.astral.sh/uv/guides/projects/), [uv CLI reference](https://docs.astral.sh/uv/reference/cli/), [uv pip compatibility and exports](https://docs.astral.sh/uv/concepts/projects/sync/).