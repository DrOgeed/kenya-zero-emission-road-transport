# 3. Using KEZERT in MUIO

KEZERT is distributed as a **native MUIO v5.7 case**: `muio/KEZERT_MUIO_v5.7_case.zip`. You can open, inspect, edit and run every scenario from the graphical interface without any Python.

## 3.1 Install MUIO

1. Download MUIO v5.7 for Windows from the [MUIO repository](https://github.com/OSeMOSYS/MUIO). The README links to the installer form.
2. Run `MUIO.exe` as administrator from a folder you have write access to.

## 3.2 Load the case

1. On the MUIO home page choose **Upload case** and select `KEZERT_MUIO_v5.7_case.zip`.
2. The case **KEZERT** appears in the case list. Open it.
3. Check the case contents.
   * **Model structure:**
     * 95 technologies in 17 technology groups, e.g. `vehicle-MOTO`, `charging`, `power`.
     * 37 commodities with balance levels: timeslice, seasonal or annual.
     * 48 timeslices mapped to 4 seasons, 2 day types and 6 daily brackets.
     * 3 storages, 28 user-defined constraints.
     * Years 2024–2060.
   * **Scenarios:** `SC_0` (the reference data, S0) plus one layer per scenario. Each layer stores only the values that differ from the scenario it builds on.
   * **Case runs:** one per scenario. Each case run activates the layers of that scenario's lineage in order. For example:

     | Case run | Active layers, in order |
     |---|---|
     | `S4_ZE_SMART` | `SC_0 → S2_ZE → S4_ZE_SMART` |
     | `SEN_DROUGHT` | `SC_0 → S2_ZE → SEN_DROUGHT` |

     `docs/generated/scenario_matrix.md` lists every lineage.

## 3.3 Run a scenario

1. Open **Run** (the data-file page) and select a case run.
2. Choose **CBC** or **GLPK**. A 2024–2060 run is a large LP, about 176,000 variables by 248,000 constraints:
   * CBC solves it on a modern laptop in roughly 10–40 minutes.
   * GLPK is much slower and is not recommended for the full horizon.
   * The HiGHS community build of MUIO (`Islam-Dj/MUIO-5.6-HiGHS`) is fastest.
3. Results appear in MUIO's result viewer under the case run. The indicator tables used in the report come from the Python post-processor (§3.5). MUIO's own result variables are identical because the LP is identical (§3.4).

**Objective value.** MUIO's raw solver objective omits the constant fixed cost of residual capacity. This is a property of the LP export, also documented by the MUIO HiGHS community edition. Use the total discounted cost in `results/scenarios/<ID>/summary.csv` when comparing scenarios.

## 3.4 Proof that the GUI and the Python pipeline are the same model

`scripts/export_muio.py --muio-src <MUIO v5.7 checkout> --verify S0_REF S4_ZE_SMART` does the following:

1. Writes the case in MUIO's on-disk format (`genData.json`, one JSON per parameter group, `view/resData.json`).
2. Imports MUIO's own `DataFileClass` from the MUIO source and calls `generateDatafile()` and `preprocessData()` for the case run, exactly as the GUI does when you press *Run*.
3. Solves that MUIO-generated data file and the Python-written data file with the same MUIO model file.
4. Compares objective values. The result is written to `muio/muio_verification.json`.

The two match to better than 1 in 10⁷, with identical numbers of rows and columns, including scenarios built from several layers. The test also runs in CI (`tests/test_pipeline.py::test_muio_generator_parity`).

## 3.5 Editing workflow

There are two supported ways to change data.

* **In MUIO.** Edit the parameters, or add a new scenario layer, in the GUI. This suits exploratory runs and training. To feed results back into this repository, export the case from MUIO (*Backup case*) and keep the zip alongside your results.
* **In the repository (recommended for publication).** Edit `data/assumptions/*.csv` or `src/kezer/scenarios.py`, then run:

  ```bash
  python scripts/run_scenarios.py          # solve and write indicators
  python scripts/export_muio.py            # regenerate the MUIO case
  python scripts/make_figures.py && python scripts/make_docs.py
  ```

  Every number then stays traceable to a CSV row with a source and confidence rating.

## 3.6 Notes on MUIO features used

* **Balance levels.** Set in the commodity editor; KEZERT already sets them. Charging commodities are *Seasonal*, so charging may move within the representative day.
* **OperationalProfile** (RYTTs, parameter *Operational Profile*) holds the unmanaged and TOU charging shapes on `CHGT_*`. The smart-charging layers set it to 0, which removes the constraint, and set `CapacityFactor = 0` in the 15:00–21:00 brackets.
* **User-defined constraints** (*Constraints* page):

  | Constraint | What it does |
  |---|---|
  | `RM_PEAK_A`, `RM_PEAK_B` | Reserve margin at the peak timeslices |
  | `ZEVCAP_*` | Diffusion limits on the zero-emission share of new vehicles |
  | `DemVs*`, `GasInfraPrereq` | PSM integration rules |
  | `BUILD_*` | Build-rate limits; loose (99 GW/yr) except in the grid-constrained scenarios |
  | `V2G_LIMIT` | V2G resource limit |

  Each constraint's description states its meaning, and the inequality is always "≤ constant".
* **Units** are written as free text in the technology and commodity metadata, e.g. `kveh`, `Gpkm`, `GW`, `PJ`.
