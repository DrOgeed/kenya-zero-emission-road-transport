#!/usr/bin/env python3
"""Recompute indicator tables from saved solutions (results/runs/<SID>.solution.pkl)
without re-solving. Usage: python scripts/postprocess.py [SID ...]"""
import pickle
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kezer.build import build_base  # noqa: E402
from kezer.results import indicators  # noqa: E402
from kezer.scenarios import SCENARIOS, build_scenario  # noqa: E402

RUNS = ROOT / "results" / "runs"
OUT = ROOT / "results" / "scenarios"


def main():
    log = pd.read_csv(ROOT / "results" / "run_log.csv").set_index("name")
    sids = sys.argv[1:] or [s for s in SCENARIOS if (RUNS / f"{s}.solution.pkl").exists()]
    base = build_base()
    for sid in sids:
        m = build_scenario(base, sid)
        sol = pickle.load(open(RUNS / f"{sid}.solution.pkl", "rb"))
        res = {**sol, "status": "Optimal", "objective": float(log.loc[sid, "objective"]),
               "t_solve_s": float(log.loc[sid, "t_solve_s"])}
        ind = indicators(m, res, sid)
        d = OUT / sid
        d.mkdir(parents=True, exist_ok=True)
        for k, df in ind.items():
            df.to_csv(d / f"{k}.csv", index=False, float_format="%.6g")
        print("post-processed", sid)


if __name__ == "__main__":
    main()
