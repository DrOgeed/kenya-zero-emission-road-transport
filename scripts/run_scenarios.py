#!/usr/bin/env python3
"""Build the KEZERT model, run scenarios and write indicator tables.

Usage:
    python scripts/run_scenarios.py                 # all scenarios
    python scripts/run_scenarios.py S0_REF S2_ZE    # selected scenarios
    python scripts/run_scenarios.py --jobs 2        # parallel runs

Outputs:
    results/scenarios/<SID>/<indicator>.csv   indicator tables (committed)
    results/runs/<SID>.txt                    GMPL data file (MUIO v5.7 format, not committed)
    results/run_log.csv                       status / timing of every run
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import pickle
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kezer.build import build_base  # noqa: E402
from kezer.results import indicators  # noqa: E402
from kezer.scenarios import SCENARIOS, build_scenario  # noqa: E402
from kezer.solve import solve  # noqa: E402

RUNS = ROOT / "results" / "runs"
OUT = ROOT / "results" / "scenarios"
CACHE = ROOT / "results" / "runs" / "base_model.pkl"


def run_one(sid: str) -> dict:
    t0 = time.time()
    try:
        base = pickle.load(open(CACHE, "rb"))
        m = build_scenario(base, sid)
        res = solve(m, RUNS, sid, solver="ipm")
        row = {k: res[k] for k in ["name", "status", "objective", "t_generate_s", "t_solve_s", "n_cols", "n_rows"]}
        if res["status"] == "Optimal":
            ind = indicators(m, res, sid)
            d = OUT / sid
            d.mkdir(parents=True, exist_ok=True)
            for k, df in ind.items():
                df.to_csv(d / f"{k}.csv", index=False, float_format="%.6g")
            row["total_cost_MUSD"] = float(ind["summary"].total_discounted_system_cost_MUSD.iloc[0])
            pickle.dump({k: v for k, v in res.items() if k in ("vars", "duals_ELC003")},
                        open(RUNS / f"{sid}.solution.pkl", "wb"))
        row["wall_s"] = round(time.time() - t0, 1)
        return row
    except Exception as e:  # keep the batch going
        traceback.print_exc()
        return {"name": sid, "status": f"error: {e}", "wall_s": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenarios", nargs="*")
    ap.add_argument("--jobs", type=int, default=1)
    a = ap.parse_args()
    sids = a.scenarios or list(SCENARIOS)
    RUNS.mkdir(parents=True, exist_ok=True)
    print("building base model ...", flush=True)
    base = build_base()
    pickle.dump(base, open(CACHE, "wb"))
    import pandas as pd
    if a.jobs > 1:
        with mp.get_context("fork").Pool(a.jobs) as pool:
            rows = pool.map(run_one, sids, chunksize=1)
    else:
        rows = [run_one(s) for s in sids]
    log = ROOT / "results" / "run_log.csv"
    new = pd.DataFrame(rows)
    if log.exists():
        old = pd.read_csv(log)
        new = pd.concat([old[~old.name.isin(new.name)], new])
    new.to_csv(log, index=False)
    print(new.to_string())


if __name__ == "__main__":
    main()
