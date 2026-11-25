# 5. Reproducing the results

## Requirements

* Python ≥ 3.10 with the packages in `requirements.txt`: pandas, numpy, highspy, matplotlib, openpyxl, pytest.
* GLPK's `glpsol`, used only to generate the LP matrix from the MUIO model file:
  * Ubuntu: `apt install glpk-utils`
  * macOS: `brew install glpk`
  * Windows: install winglpk, or use the `glpsol.exe` bundled with MUIO.
* About 3 GB of RAM per parallel run.

## One-command rebuild

```bash
pip install -r requirements.txt
python scripts/run_scenarios.py --jobs 2   # build model, solve all scenarios
python scripts/postprocess.py              # (optional) recompute indicators from saved solutions
python scripts/make_figures.py             # results/figures/*.png
python scripts/make_docs.py                # docs/generated/*.md + results/headline_indicators.csv
python scripts/export_muio.py              # muio/KEZERT_MUIO_v5.7_case.zip
```

Optional verification against MUIO's own data-file generator. MUIO's code checks that `glpsol` and `cbc` are installed (`apt install coinor-cbc`), even though only the data-file generator is used:

```bash
git clone --depth 1 --branch v5.7 https://github.com/OSeMOSYS/MUIO /tmp/muio
python scripts/export_muio.py --muio-src /tmp/muio --verify S4_ZE_SMART
MUIO_SRC=/tmp/muio pytest -q
```

## Runtime

Each 2024–2060 scenario has about 176,000 variables and 248,000 constraints. On one CPU core it takes about 35 s for matrix generation and 2.5–9 min to solve with HiGHS (interior point plus crossover). All 25 runs finish in about 1 hour on two cores. `results/run_log.csv` records status, objective, timing and matrix size for every run.

## Provenance chain

```
data/external/ccg_kenya_psm_v3/data.txt  (CCG PSM v3, CC BY 4.0)
data/assumptions/*.csv                   (every value + source_id + confidence)
        │  src/kezer/build.py            (ingest, adapt, calibrate)
        ▼
base model ──src/kezer/scenarios.py──► scenario models
        │  src/kezer/solve.py            (MUIO-format data file → glpsol --wlp → HiGHS)
        ▼
results/runs/<ID>.txt                    (exact GMPL data file used, MUIO v5.7 format)
results/scenarios/<ID>/*.csv             (indicators)
muio/KEZERT_MUIO_v5.7_case.zip           (same model as a MUIO case; parity-tested)
```

## Versioning and archiving

* Tag releases (`v1.0.0`, …) and enable the Zenodo–GitHub integration so each release gets a DOI.
* Update `CITATION.cff` with the DOI.
* Pin the solver versions in the release notes. The current results used glpsol 5.0 and HiGHS 1.16.0.
