"""Write, solve and read back a model run.

Pipeline: tidy model -> GMPL data file (MUIO v5.7 conventions, incl. the
CapitalRecoveryFactor / PvAnnuity tables that MUIO appends) -> glpsol
--check --wlp (matrix generation with the unmodified MUIO model file) ->
HiGHS (LP) -> tidy results by variable.
"""
from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

import highspy
import pandas as pd

from .data import Model
from .gmpl_io import write_datafile

ROOT = Path(__file__).resolve().parents[2]
MODEL_FILE = ROOT / "model" / "osemosys_muio_v5.7.txt"

VAR_INDEX = {
    "NewCapacity": ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalCapacityAnnual": ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalTechnologyAnnualActivity": ["REGION", "TECHNOLOGY", "YEAR"],
    "TotalAnnualTechnologyActivityByMode": ["REGION", "TECHNOLOGY", "MODE_OF_OPERATION", "YEAR"],
    "RateOfActivity": ["REGION", "TIMESLICE", "TECHNOLOGY", "MODE_OF_OPERATION", "YEAR"],
    "SeasonalRateOfActivity": ["REGION", "SEASON", "TECHNOLOGY", "MODE_OF_OPERATION", "YEAR"],
    "AnnualTechnologyEmission": ["REGION", "TECHNOLOGY", "EMISSION", "YEAR"],
    "NewStorageCapacity": ["REGION", "STORAGE", "YEAR"],
    "AccumulatedNewStorageCapacity": ["REGION", "STORAGE", "YEAR"],
    "CapitalInvestment": ["REGION", "TECHNOLOGY", "YEAR"],
    "CapitalInvestmentStorage": ["REGION", "STORAGE", "YEAR"],
    "DiscountedSalvageValue": ["REGION", "TECHNOLOGY", "YEAR"],
    "DiscountedSalvageValueStorage": ["REGION", "STORAGE", "YEAR"],
}


def crf_tables(m: Model) -> str:
    """CapitalRecoveryFactor and PvAnnuity exactly as MUIO computes them."""
    dr = m.get("DiscountRate", ("RE1",))
    techs = m.sets["TECHNOLOGY"]
    crf, pva = [], []
    for t in techs:
        dri = m.get("DiscountRateIdv", ("RE1", t))
        ol = int(m.get("OperationalLife", ("RE1", t)))
        crf.append(round((1 - (1 + dri) ** -1) / (1 - (1 + dri) ** -ol), 4) if dri else 0)
        pva.append(round((1 - (1 + dr) ** -ol) * (1 + dr) / dr, 4))
    s = "param CapitalRecoveryFactor default 0 :\n" + " ".join(techs) + " :=\nRE1 " + " ".join(map(str, crf)) + "\n;\n"
    s += "param PvAnnuity default 0 :\n" + " ".join(techs) + " :=\nRE1 " + " ".join(map(str, pva)) + "\n;\n"
    return s


def derived_sets(m: Model) -> str:
    """Mode/technology mapping sets that MUIO's preprocessData appends."""
    from collections import defaultdict
    out = defaultdict(set)
    inp = defaultdict(set)
    emi = defaultdict(set)
    tts = defaultdict(set)
    tfs = defaultdict(set)
    modes = defaultdict(set)
    for (r, t, f, mo, y), v in m.params.get("OutputActivityRatio", {}).items():
        if v:
            out[f].add((mo, t)); modes[t].add(mo)
    for (r, t, f, mo, y), v in m.params.get("InputActivityRatio", {}).items():
        if v:
            inp[f].add((mo, t)); modes[t].add(mo)
    for (r, t, e, mo, y), v in m.params.get("EmissionActivityRatio", {}).items():
        if v:
            emi[e].add((mo, t)); modes[t].add(mo)
    for (r, t, s, mo), v in m.params.get("TechnologyToStorage", {}).items():
        if v:
            tts[s].add((mo, t)); modes[t].add(mo)
    for (r, t, s, mo), v in m.params.get("TechnologyFromStorage", {}).items():
        if v:
            tfs[s].add((mo, t)); modes[t].add(mo)

    def block(name, keys, d):
        lines = []
        for k in keys:
            pairs = " ".join(f"({mo},{t})" for mo, t in sorted(d.get(k, ())))
            lines.append(f"set {name}[{k}] := {pairs};\n")
        return "".join(lines)

    s = block("MODExTECHNOLOGYperFUELout", m.sets["COMMODITY"], out)
    s += block("MODExTECHNOLOGYperFUELin", m.sets["COMMODITY"], inp)
    s += block("MODExTECHNOLOGYperEMISSION", m.sets["EMISSION"], emi)
    s += block("MODExTECHNOLOGYperEMISSIONChange", m.sets["EMISSION"], {})
    s += block("MODExTECHNOLOGYperSTORAGEto", m.sets["STORAGE"], tts)
    s += block("MODExTECHNOLOGYperSTORAGEfrom", m.sets["STORAGE"], tfs)
    for c in m.sets["COMMODITY"]:
        s += f"set INPUTxNEWxCAPACITYperFUEL[{c}] := ;\nset INPUTxTOTALxCAPACITYperFUEL[{c}] := ;\n"
    for t in m.sets["TECHNOLOGY"]:
        s += f"set MODEperTECHNOLOGY[{t}] := {' '.join(sorted(modes.get(t, ())))};\n"
    s += "set INPUTxFUEL := ;\n"
    return s


def write_model(m: Model, path: Path, header: str = "") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_datafile(path, m.sets, m.to_frames(), header=header)
    txt = path.read_text()
    txt = txt.replace("end;\n", crf_tables(m) + derived_sets(m) + "end;\n")
    path.write_text(txt)
    return path


_NAME = re.compile(r"^(\w+)\((.*)\)$")


def solve(m: Model, workdir: Path, name: str, **kw) -> dict:
    """Write the model as a MUIO-format data file and solve it."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    dat = write_model(m, workdir / f"{name}.txt", header=f"KEZERT model run: {name}")
    return solve_datafile(dat, workdir, name, **kw)


def solve_datafile(dat: Path | None, workdir: Path, name: str, model: Model | None = None,
                   keep_lp=False, time_limit=7200, log=print, solver: str = "ipm", threads: int = 1) -> dict:
    """Solve a GMPL data file (e.g. one generated by MUIO) with the MUIO v5.7
    model file. If ``dat`` is None the data file is written from ``model``."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    if dat is None:
        dat = write_model(model, workdir / f"{name}.txt", header=f"KEZERT model run: {name}")
    lp = workdir / f"{name}.lp"
    t0 = time.time()
    res = subprocess.run(["glpsol", "--check", "-m", str(MODEL_FILE), "-d", str(dat), "--wlp", str(lp)],
                         capture_output=True, text=True)
    if res.returncode != 0 or not lp.exists():
        raise RuntimeError(f"glpsol failed for {name}:\n{res.stdout[-4000:]}\n{res.stderr[-2000:]}")
    (workdir / f"{name}.glpsol.log").write_text(res.stdout)
    t_gen = time.time() - t0
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    h.setOptionValue("time_limit", float(time_limit))
    h.setOptionValue("presolve", "on")
    h.setOptionValue("solver", solver)
    h.setOptionValue("threads", threads)
    if solver == "ipm":
        h.setOptionValue("run_crossover", "on")
    h.readModel(str(lp))
    t1 = time.time()
    h.run()
    status = h.modelStatusToString(h.getModelStatus())
    t_solve = time.time() - t1
    info = h.getInfo()
    out = {"name": name, "status": status, "objective": info.objective_function_value,
           "t_generate_s": round(t_gen, 1), "t_solve_s": round(t_solve, 1),
           "n_cols": h.getNumCol(), "n_rows": h.getNumRow()}
    log(f"[{name}] {status} obj={out['objective']:.1f} M$  gen={t_gen:.0f}s solve={t_solve:.0f}s "
        f"({out['n_cols']} cols x {out['n_rows']} rows)")
    if status != "Optimal":
        return out
    sol = h.getSolution()
    lp_model = h.getLp()
    names = lp_model.col_names_
    vals = sol.col_value
    rows: dict[str, list] = {v: [] for v in VAR_INDEX}
    for nm, v in zip(names, vals):
        if abs(v) < 1e-9:
            continue
        mt = _NAME.match(nm)
        if not mt:
            continue
        var = mt.group(1)
        if var in rows:
            rows[var].append((*[s.strip("'") for s in mt.group(2).split(",")], v))
    out["vars"] = {v: pd.DataFrame(r, columns=VAR_INDEX[v] + ["VALUE"]) for v, r in rows.items()}
    # duals of the timeslice electricity balance (marginal cost of electricity)
    duals = []
    row_names = lp_model.row_names_
    for nm, d in zip(row_names, sol.row_dual):
        if nm.startswith("EB_TimesliceBalance") and "ELC003" in nm:
            mt = _NAME.match(nm)
            if mt:
                duals.append((*[s.strip("'") for s in mt.group(2).split(",")], d))
    out["duals_ELC003"] = pd.DataFrame(duals, columns=["REGION", "TIMESLICE", "COMMODITY", "YEAR", "VALUE"])
    if not keep_lp:
        lp.unlink(missing_ok=True)
    return out
