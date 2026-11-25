#!/usr/bin/env python3
"""Export KEZERT as a MUIO v5.7 case (all scenarios as layers + one case run
per scenario) and verify it with MUIO's own data-file generator.

Usage:
    python scripts/export_muio.py [--muio-src PATH] [--verify S0_REF S4_ZE_SMART]

--muio-src points to a checkout of https://github.com/OSeMOSYS/MUIO at tag
v5.7 (only needed for --verify).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kezer.build import build_base  # noqa: E402
from kezer.muio_case import CaseWriter, verify_with_muio, zip_case  # noqa: E402
from kezer.scenarios import SCENARIOS, build_scenario, lineage  # noqa: E402
from kezer.solve import solve_datafile  # noqa: E402

OUT = ROOT / "muio"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--muio-src", default=None)
    ap.add_argument("--verify", nargs="*", default=[])
    ap.add_argument("--families", nargs="*", default=["core", "sensitivity"])
    a = ap.parse_args()

    base = build_base()
    sids = [s for s, sc in SCENARIOS.items() if sc.family in a.families]
    models = {s: build_scenario(base, s) for s in sids}
    layer_id = {s: ("SC_0" if s == "S0_REF" else s) for s in sids}
    layers = []
    for s in sids:
        sc = SCENARIOS[s]
        layers.append((layer_id[s], sc.name, sc.description, models[s],
                       layer_id[sc.parent] if sc.parent else None))
    caseruns = [(s, SCENARIOS[s].name, [layer_id[x] for x in lineage(s)]) for s in sids]
    w = CaseWriter(models["S0_REF"], "KEZERT")
    case_dir = w.write(OUT / "case", layers, caseruns)
    z = zip_case(case_dir, OUT / "KEZERT_MUIO_v5.7_case.zip")
    size = sum(f.stat().st_size for f in case_dir.rglob("*") if f.is_file()) / 1e6
    print(f"case written: {case_dir} ({size:.1f} MB unzipped, {z.stat().st_size/1e6:.1f} MB zipped)")

    checks = []
    for s in a.verify:
        if not a.muio_src:
            raise SystemExit("--verify needs --muio-src")
        dat = verify_with_muio(case_dir, Path(a.muio_src), s, ROOT / "results" / "muio_verify")
        r = solve_datafile(dat, ROOT / "results" / "muio_verify", f"muio_{s}")
        log = ROOT / "results" / "run_log.csv"
        import pandas as pd
        ref_obj = None
        if log.exists():
            lg = pd.read_csv(log).set_index("name")
            if s in lg.index:
                ref_obj = float(lg.loc[s, "objective"])
        if ref_obj is None:
            ref_obj = solve_datafile(None, ROOT / "results" / "muio_verify", f"py_{s}", model=models[s])["objective"]
        rel = abs(r["objective"] - ref_obj) / abs(ref_obj)
        checks.append({"scenario": s, "muio_generated_objective": r["objective"], "python_pipeline_objective": ref_obj,
                       "relative_difference": rel, "rows_cols_muio": [r["n_rows"], r["n_cols"]],
                       "pass": rel < 1e-5})
        print(checks[-1])
    if checks:
        (OUT / "muio_verification.json").write_text(json.dumps(checks, indent=1))


if __name__ == "__main__":
    main()
