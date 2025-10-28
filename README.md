# BASIL (Bayesian Approach to Scientific Iteration and Learning)
A cross-platform GUI that helps research teams design, run, and iterate on laboratory campaigns using Bayesian optimization.

<img src="assets/logo.png" height=200>

## Table of contents
- [Overview](#overview)
- [Key features](#key-features)
- [Quick start](#quick-start)
- [Running the app](#running-the-app)
- [Workspaces & data](#workspaces--data)
- [optimization workflow](#optimization-workflow)
- [Project layout](#project-layout)
- [Development tasks](#development-tasks)
- [Packaging](#packaging)
- [Resources](#resources)

## Overview
BASIL provides a modern graphical interface for machine learning guided experimentation without writing code. Researchers can capture parameters, objectives, and legacy data, then let [BayBE](https://github.com/emdgroup/baybe/) generate the next experiments to run. The application currently targets Windows, macOS, and Linux via PySide6/Qt6 and ships in an **alpha** state while we continue to expand the user experience and model coverage.

## Key features
- **Workspace management** – create, open, and remember project workspaces with persistent recent history.
- **Rich parameter authoring** – continuous, discrete, categorical, fixed, and chemistry (SMILES) parameters with constraint validation and templated CSV export.
- **Data import & validation** – generate CSV templates, preview imported data, and highlight schema mismatches before optimization.
- **Bayesian experiment planning** – integrate with BayBE for single- or multi-objective optimization, including desirability blending and surrogate/acquisition tuning.
- **Campaign dashboard** –  Runs, Parameters, and Settings views with run history, logs.
- **Logging & provenance** – per-campaign log files and run outputs saved alongside workspace assets for auditability.

## Quick start

### Prerequisites
- Python 3.11 (3.11–3.13 supported by `pyproject.toml`)
- [Poetry](https://python-poetry.org/) 1.6+
- (Optional) [UPX](https://upx.github.io/) if you plan to create compressed executables

### Install dependencies (recommended Poetry workflow)
```powershell
git clone https://github.com/molecularmodelinglab/BASIL.git
cd BASIL
poetry install
```

### Launch the GUI
```powershell
poetry run python main.py
```

### Alternative: pure `pip` environment
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Running the app
1. **Select or create a workspace** – choose a folder that will store campaign metadata, run outputs, and logs. BASIL writes a `basil_workspace.json` file and a `campaigns/` directory inside the workspace.
2. **Create a campaign** – the wizard guides you through naming the campaign, defining optimization targets, specifying surrogate/acquisition settings, and authoring the parameter space.
3. **Seed data (optional)** – import historical results via CSV, validate against constraints, and preview the dataset before continuing.
4. **optimize** – use the campaign panel to request new experiment suggestions powered by BayBE. Logs and generated batches are written to the workspace for later review.


## Workspaces & data
- Each workspace contains:
  - `basil_workspace.json` – workspace metadata (name, version, timestamps).
  - `campaigns/<uuid>/` – campaign-specific folders storing `config.json`, run CSVs, and BayBE state snapshots.
  - `logs/` – generated automatically to capture optimization traces (e.g., `bayesian_generation.log`).
- The application remembers your most recently opened workspace via `app/core/settings.py`, so launching BASIL again jumps straight back into your work.

## optimization workflow
- **Targets & desirability** – define one or more objectives, assign bounds, choose maximise/minimise modes, and optionally weight multi-objective desirability functions.
- **Parameter space** – mix numeric, integer, categorical, and chemistry parameters with validation widgets. The parameter serializer persists definitions so campaigns can be resumed later.
- **BayBE integration** – BASIL converts campaign definitions into BayBE campaigns and persists optimization state between runs.
- **Experiment batches** – generated suggestions are saved as CSV files under `campaigns/<uuid>/runs/`. Subsequent optimization rounds incorporate previous results automatically.
- **Fallback handling** – if BayBE cannot produce recommendations, BASIL falls back to random sampling so you can keep moving while inspecting logs.

## Project layout
```
app/
├── app.py                # Qt entry point (sets icons, logging)
├── main_application.py   # Main window orchestrating navigation
├── bayesopt/             # BayBE integration, parameter/objective adapters
├── core/                 # Shared settings, base screen/widget classes
├── models/               # Campaign, parameter, and workspace dataclasses
├── screens/              # Workspace selection, campaign wizard, panels
└── shared/               # Reusable UI components, styles, dialogs
tests/
├── test_smoke.py         # High-level UI smoke tests with pytest-qt
└── ...                   # Screen, model, and service unit tests
```

Additional developer utilities live at the repository root (`build.py`, `example_*`, `poetry.lock`, etc.).

## Development tasks
- **Run the test suite**
  - `poetry run pytest`
- **Check coverage**
  - `poetry run pytest --cov=app tests/`
- **Static analysis & formatting**
  - `poetry run ruff check app tests`
  - `poetry run ruff format`
  - `poetry run mypy app`
- **Pre-commit hooks**
  - `poetry run pre-commit install`
  - `poetry run pre-commit run --all-files`

`pytest-qt` powers the GUI smoke tests. When running under WSL or headless CI, ensure an X server is available or use Qt's offscreen plugin.

## Packaging
Use `build.py` to create platform-specific bundles via PyInstaller:

```powershell
poetry run python build.py --version 0.1.0 --tag-output
```

**Performance Note**: Using the `--onefile` option may result in slower startup times on both Windows and macOS due to the need to extract dependencies on each launch. For better performance, we recommend using the default `--onedir` mode.

The script handles icons, Windows version info, macOS bundle metadata, and optional UPX compression. Generated artefacts land in `dist/`, with intermediate files in `build/`.

## macOS Installation

### Important: First-Time Setup (macOS only)

After installing BASIL to Applications, open Terminal and run:
```bash
xattr -cr /Applications/BASIL.app
```

Then you can open BASIL normally. You only need to do this once.

### Why is this needed?

BASIL is free and open-source. Apple requires a $99/year developer account to avoid this security warning. We provide this simple workaround instead.

### Important: First-Time Setup (Windows only)

1. Download the BASIL installer archive.
2. If your antivirus deletes it, temporarily disable protection and re-download.
3. Extract and install BASIL.
4. Launch BASIL in Administrator mode.

### Why is this needed?

BASIL is currently in beta and unsigned (no digital certificate). Some antivirus software may flag or delete unsigned applications. Running as Administrator ensures BASIL can correctly access required resources during its first launch.

## Resources
- License: [Apache 2.0](LICENSE)
- Issue tracker: [GitHub Issues](https://github.com/molecularmodelinglab/BASIL/issues)
- Primary maintainers: Kelvin P. Idanwekhai, Valeria Kaneva

We welcome bug reports, usability feedback, and feature proposals as we continue to harden the BASIL experience.
