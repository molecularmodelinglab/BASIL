<div align = "center">
<img src="assets/logo.png" height=200>
</div>

<div align = "center">
<span>
<h1> BASIL: Bayesian Application for Scientific Iteration and Learning  </h1>
</span>
</div>
<h4>
A cross-platform GUI that helps research teams design, run, and iterate on laboratory campaigns using Bayesian optimization.
</h4>


## Table of contents
- [Overview](#overview)
- [Key features](#key-features)
- [Installation and use](#installation-and-use)
- [Development](#development)
- [Packaging](#packaging)
- [Resources](#resources)
- [Citation](#citation)

## Overview
BASIL is user-friendly desktop application for process optimization, it provides a modern graphical interface for machine learning guided experimentation without writing code. Researchers can capture parameters, objectives, and legacy data, then let [BayBE](https://github.com/emdgroup/baybe/) generate the next experiments to run. The application currently targets Windows, macOS (Apple Silicon), and Linux via PySide6/Qt6 while we continue to expand the user experience and model coverage.

> **Note:** Intel-based Macs are not supported. Only Apple Silicon (M-series) Macs are supported.

## Key features
- **Workspace management** – create, open, and remember project workspaces with persistent recent history.
- **Rich parameter authoring** – continuous, discrete, categorical, fixed, and chemistry (SMILES) parameters with constraint validation and templated CSV export.
- **Data import & validation** – generate CSV templates, preview imported data, and highlight schema mismatches before optimization.
- **Bayesian experiment planning** – integrate with BayBE for single- or multi-objective optimization, including desirability blending and surrogate/acquisition tuning.
- **Campaign dashboard** –  Runs, Parameters, and Settings views with run history, logs.
- **Logging & provenance** – per-campaign log files and run outputs saved alongside workspace assets for auditability.


## Installation and use

You can download and install the bundled version of BASIL from the [releases section](https://github.com/molecularmodelinglab/BASIL/releases). Select the file extension that correponds with your operating system.

### Tutorial

It's very easy to get started with BASIL! Please follow our quick [demo](docs/demo.ipynb) on this page.

### Workspaces & data
- Each workspace contains:
  - `basil_workspace.json` – workspace metadata (name, version, timestamps).
  - `campaigns/<uuid>/` – campaign-specific folders storing `config.json`, run CSVs, and BayBE state snapshots.
  - `logs/` – generated automatically to capture optimization traces (e.g., `bayesian_generation.log`).
- The application remembers your most recently opened workspace via `app/core/settings.py`, so launching BASIL again jumps straight back into your work.

### optimization workflow
- **Targets & optimization type** – define one or more objectives, assign bounds, choose maximise/minimise modes, and optionally weight multi-objective desirability, or choose a Pareto-optimization scheme.
- **Parameter space** – mix numeric, integer, categorical, and chemistry parameters, and SMILES strings with validation widgets. The parameter serializer persists definitions so campaigns can be resumed later.
- **BayBE integration** – BASIL converts campaign definitions into BayBE campaigns and persists optimization state between runs.
- **Experiment batches** – generated suggestions are saved as CSV files under `campaigns/<uuid>/runs/`. Subsequent optimization rounds incorporate previous results automatically.
- **Fallback handling** – if BayBE cannot produce recommendations, BASIL falls back to random sampling so you can keep moving while inspecting logs.

## Development

```powershell
git clone https://github.com/molecularmodelinglab/BASIL.git
cd BASIL
poetry install
```

### Prerequisites
- Python 3.11 (3.11–3.13 supported by `pyproject.toml`)
- [Poetry](https://python-poetry.org/) 1.6+
- (Optional) [UPX](https://upx.github.io/) if you plan to create compressed executables

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

### Launch the GUI
```powershell
poetry run python main.py
```

## Packaging
Use `build.py` to create platform-specific bundles via PyInstaller:

```powershell
poetry run python build.py --version 0.1.0 --tag-output
```

**Performance Note**: Using the `--onefile` option may result in slower startup times on both Windows and macOS due to the need to extract dependencies on each launch. For better performance, we recommend using the default `--onedir` mode.

The script handles icons, Windows version info, macOS bundle metadata, and optional UPX compression. Generated artefacts land in `dist/`, with intermediate files in `build/`.

### CI builds
The [Build and Release workflow](.github/workflows/build-release.yml) builds installers for Windows, macOS (Apple Silicon), and Linux. It runs automatically when a GitHub Release is published (and uploads the installers to that release), or it can be triggered manually (`workflow_dispatch`, on any branch, e.g. `dev`) to produce test builds without publishing anything — those runs upload the installers as downloadable workflow artifacts instead, which are automatically deleted after 7 days.

## macOS Installation

> **Note:** BASIL only supports Apple Silicon (M-series) Macs. Intel-based Macs are not supported.

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
- License: [See Here](LICENSE)
- Issue tracker: [GitHub Issues](https://github.com/molecularmodelinglab/BASIL/issues)
- Primary maintainers: Kelvin P. Idanwekhai, Valeria Kaneva

### Citation
If you use BASIL in your work, please cite: [our paper](https://doi.org/10.48550/arXiv.2606.21092):

```bibtex
@article{basil2026,
 title={BASIL: Bayesian Application for Scientific Iteration and Learning}, 
      author={Kelvin P. Idanwekhai and Valeriia Kaneva and Stefano Menegatti and Alexander Tropsha},
      year={2026},
      eprint={2606.21092},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/2606.21092}, 
}
```

We welcome bug reports, usability feedback, and feature proposals as we continue to harden the BASIL experience.