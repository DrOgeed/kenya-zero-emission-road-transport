"""Export the model and its scenarios as a native MUIO v5.7 case.

The case (genData.json + one JSON file per parameter group + view/resData.json
with the case runs) is written in exactly the layout MUIO's own CaseClass
creates, so it can be loaded with MUIO's *Upload case* button. Scenarios are
stored as MUIO scenario layers: SC_0 holds the reference data and every other
layer only the values that differ from its parent; each case run activates the
layers of one scenario's lineage in order.

`verify_with_muio` then runs MUIO's own data-file generator (generateDatafile
+ preprocessData, imported from a MUIO v5.7 source tree) on the exported case
and solves the result, which proves that the GUI reproduces the Python
pipeline.
"""
from __future__ import annotations

import json
import shutil
import sys
import zipfile
from datetime import date
from pathlib import Path

from .data import Model
from .gmpl_io import PARAM_INDEX, default_of

R = "RE1"

# MUIO parameter id -> (group, model parameter name)
MUIO_PARAMS = {
    "R": {"DR": "DiscountRate"},
    "RT": {"TMPAU": "TotalTechnologyModelPeriodActivityUpperLimit", "TMPAL": "TotalTechnologyModelPeriodActivityLowerLimit",
           "OL": "OperationalLife", "CAU": "CapacityToActivityUnit", "DRI": "DiscountRateIdv"},
    "RE": {"MPEL": "ModelPeriodEmissionLimit"},
    "RYCn": {"UCC": "UDCConstant"},
    "RYTCn": {"CAM": "UDCMultiplierActivity", "CNCM": "UDCMultiplierNewCapacity", "CCM": "UDCMultiplierTotalCapacity"},
    "RYTs": {"YS": "YearSplit"},
    "RYDtb": {"DS": "DaySplit"},
    "RYSeDt": {"DIDT": "DaysInDayType"},
    "RYT": {"COTU": "CapacityOfOneTechnologyUnit", "TAU": "TotalTechnologyAnnualActivityUpperLimit",
            "TAL": "TotalTechnologyAnnualActivityLowerLimit", "TAMinCI": "TotalAnnualMinCapacityInvestment",
            "TAMinC": "TotalAnnualMinCapacity", "TAMaxCI": "TotalAnnualMaxCapacityInvestment",
            "TAMaxC": "TotalAnnualMaxCapacity", "RC": "ResidualCapacity", "FC": "FixedCost", "CC": "CapitalCost",
            "AF": "AvailabilityFactor"},
    "RYTM": {"TAIML": "TechnologyActivityIncreaseByModeLimit", "TADML": "TechnologyActivityDecreaseByModeLimit",
             "TAMUL": "TechnologyActivityByModeUpperLimit", "TAMLL": "TechnologyActivityByModeLowerLimit",
             "VC": "VariableCost"},
    "RYTC": {"ITCR": "InputToTotalCapacityRatio", "INCR": "InputToNewCapacityRatio"},
    "RYTCM": {"OAR": "OutputActivityRatio", "IAR": "InputActivityRatio"},
    "RS": {"SLS": "StorageLevelStart", "OLS": "OperationalLifeStorage"},
    "RYS": {"MSC": "MinStorageCharge", "RSC": "ResidualStorageCapacity", "CCS": "CapitalCostStorage"},
    "RTSM": {"TFS": "TechnologyFromStorage", "TTS": "TechnologyToStorage"},
    "RYTTs": {"CF": "CapacityFactor", "OP": "OperationalProfile"},
    "RYC": {"SAD": "SpecifiedAnnualDemand", "AAD": "AccumulatedAnnualDemand"},
    "RYCTs": {"SDP": "SpecifiedDemandProfile"},
    "RYE": {"EP": "EmissionsPenalty", "AEL": "AnnualEmissionLimit"},
    "RYTEM": {"EACR": "EmissionToActivityChangeRatio", "EAR": "EmissionActivityRatio"},
}

# defaults as declared in MUIO's Parameters.json (used for SC_0 gaps)
MUIO_DEFAULT = {"DiscountRate": 0.05, "TotalTechnologyModelPeriodActivityUpperLimit": 999999,
                "ModelPeriodEmissionLimit": 999999, "OperationalLife": 1, "CapacityToActivityUnit": 1,
                "DiscountRateIdv": 0.05, "YearSplit": 1, "DaySplit": 1, "DaysInDayType": 1,
                "TotalTechnologyAnnualActivityUpperLimit": 999999, "TotalAnnualMaxCapacityInvestment": 999999,
                "TotalAnnualMaxCapacity": 999999, "AvailabilityFactor": 1, "TechnologyActivityByModeUpperLimit": 99999,
                "VariableCost": 0.0001, "StorageLevelStart": 1, "OperationalLifeStorage": 1, "CapacityFactor": 1,
                "AnnualEmissionLimit": 999999}


def _mdef(p):
    return MUIO_DEFAULT.get(p, 0)


class CaseWriter:
    def __init__(self, base: Model, casename: str = "KEZERT"):
        self.m = base
        self.casename = casename
        self.years = list(base.sets["YEAR"])
        self.modes = base.sets["MODE_OF_OPERATION"]
        self._ids()

    # -------------------------------------------------------------- ids
    def _ids(self):
        m = self.m
        self.tid = {t: f"TEC_{i}" for i, t in enumerate(m.sets["TECHNOLOGY"])}
        self.cid = {c: f"COM_{i}" for i, c in enumerate(m.sets["COMMODITY"])}
        self.eid = {e: f"EMI_{i}" for i, e in enumerate(m.sets["EMISSION"])}
        self.sid = {s: f"STG_{i}" for i, s in enumerate(m.sets["STORAGE"])}
        self.lid = {l: f"TS_{i}" for i, l in enumerate(m.sets["TIMESLICE"])}
        self.seid = {s: f"SE_{i}" for i, s in enumerate(m.sets["SEASON"])}
        self.dtid = {s: f"DT_{i}" for i, s in enumerate(m.sets["DAYTYPE"])}
        self.dtbid = {s: f"DTB_{i}" for i, s in enumerate(m.sets["DAILYTIMEBRACKET"])}
        self.uid = {u: f"CO_{i}" for i, u in enumerate(m.sets["UDC"])}

    # -------------------------------------------------------------- genData
    def gen_data(self, scenarios: list[tuple[str, str, str]]) -> dict:
        m = self.m
        from .build import BRACKET_LABEL, DAYTYPE_LABEL, SEASON_LABEL
        links = {"IAR": {}, "OAR": {}, "EAR": {}}
        for (r, t, c, mo, y), v in m.params.get("InputActivityRatio", {}).items():
            links["IAR"].setdefault(t, set()).add(self.cid[c])
        for (r, t, c, mo, y), v in m.params.get("OutputActivityRatio", {}).items():
            links["OAR"].setdefault(t, set()).add(self.cid[c])
        for (r, t, e, mo, y), v in m.params.get("EmissionActivityRatio", {}).items():
            links["EAR"].setdefault(t, set()).add(self.eid[e])
        groups = {}
        for t, me in m.techs.items():
            g = me.group if me.group != "vehicle" else f"vehicle-{me.vclass}"
            groups.setdefault(g, []).append(t)
        tg = [{"TechGroup": g, "TechGroupId": f"TG_{i}", "Desc": g} for i, g in enumerate(sorted(groups))]
        tgid = {d["TechGroup"]: d["TechGroupId"] for d in tg}
        techs = []
        for t in m.sets["TECHNOLOGY"]:
            me = m.techs[t]
            g = me.group if me.group != "vehicle" else f"vehicle-{me.vclass}"
            techs.append({"TechId": self.tid[t], "Tech": t, "Desc": me.description,
                          "CapUnitId": me.cap_unit, "ActUnitId": me.act_unit,
                          "IAR": sorted(links["IAR"].get(t, [])), "OAR": sorted(links["OAR"].get(t, [])),
                          "EAR": sorted(links["EAR"].get(t, [])), "INCR": [], "ITCR": [], "TG": [tgid[g]]})
        comms = [{"CommId": self.cid[c], "Comm": c, "Desc": m.comms[c].description,
                  "BalanceLevel": m.comms[c].balance, "UnitId": m.comms[c].unit} for c in m.sets["COMMODITY"]]
        conv = {}
        for p, key in [("Conversionls", "SE"), ("Conversionld", "DT"), ("Conversionlh", "DTB")]:
            for (l, s), v in m.params[p].items():
                if v:
                    conv.setdefault(l, {})[key] = s
        ts = [{"TsId": self.lid[l], "Ts": l,
               "Desc": f"{SEASON_LABEL[conv[l]['SE']]}, {DAYTYPE_LABEL[conv[l]['DT']]}, {BRACKET_LABEL[conv[l]['DTB']]}",
               "SE": self.seid[conv[l]["SE"]], "DT": self.dtid[conv[l]["DT"]], "DTB": self.dtbid[conv[l]["DTB"]]}
              for l in m.sets["TIMESLICE"]]
        se = [{"SeId": self.seid[s], "Se": s, "Desc": SEASON_LABEL[s]} for s in m.sets["SEASON"]]
        dt = [{"DtId": self.dtid[s], "Dt": s, "Desc": DAYTYPE_LABEL[s]} for s in m.sets["DAYTYPE"]]
        dtb = [{"DtbId": self.dtbid[s], "Dtb": s, "Desc": BRACKET_LABEL[s]} for s in m.sets["DAILYTIMEBRACKET"]]
        emis = [{"EmisId": self.eid[e], "Emis": e, "Desc": "Carbon dioxide", "UnitId": "Mt"} for e in m.sets["EMISSION"]]
        stg = []
        for s in m.sets["STORAGE"]:
            tts = next(k[1] for k, v in m.params["TechnologyToStorage"].items() if k[2] == s and v)
            tfs = next(k[1] for k, v in m.params["TechnologyFromStorage"].items() if k[2] == s and v)
            stg.append({"StgId": self.sid[s], "Stg": s, "Desc": {"BESS001": "Battery energy (intraday)",
                                                                 "PHS001": "Pumped hydro reservoir 1",
                                                                 "PHS002": "Pumped hydro reservoir 2"}.get(s, s),
                        "UnitId": "PJ", "TTS": self.tid[tts], "TFS": self.tid[tfs],
                        "Operation": "Daily" if s in m.sets["STORAGEINTRADAY"] else "Yearly"})
        cons = []
        cm = {}
        for p in ["UDCMultiplierActivity", "UDCMultiplierNewCapacity", "UDCMultiplierTotalCapacity"]:
            for (r, t, u, y), v in m.params.get(p, {}).items():
                cm.setdefault(u, set()).add(self.tid[t])
        for u in m.sets["UDC"]:
            cons.append({"ConId": self.uid[u], "Con": u, "Desc": m.udcs[u].description,
                         "Tag": m.udcs[u].tag, "CM": sorted(cm.get(u, []))})
        self.cm = cm
        return {
            "osy-version": "5.7", "osy-casename": self.casename,
            "osy-desc": "KEZERT: Kenya Zero-Emission Road Transport model (power + road transport + rail), "
                        "built on CCG OSeMOSYS Kenya PSM v3. Units: PJ, GW, M USD 2024, Mt CO2, Gpkm/Gtkm, kveh.",
            "osy-date": date.today().isoformat(), "osy-currency": "MUSD (2024)",
            "osy-mo": str(len(self.modes)), "osy-tech": techs, "osy-techGroups": tg, "osy-comm": comms,
            "osy-ts": ts, "osy-se": se, "osy-dt": dt, "osy-dtb": dtb, "osy-emis": emis, "osy-stg": stg,
            "osy-scenarios": [{"ScenarioId": sc, "Scenario": name, "Desc": desc, "Active": True}
                              for sc, name, desc in scenarios],
            "osy-constraints": cons, "osy-indicators": [], "osy-years": self.years,
        }

    # -------------------------------------------------------------- values
    def _val(self, model: Model, p: str, key: tuple):
        d = model.params.get(p, {})
        if key in d:
            return d[key]
        return _mdef(p)

    def chunks(self, group: str, pid: str, p: str, model: Model, parent: Model | None, gd: dict):
        """Dense chunk list for one parameter and scenario (None = inherit)."""
        Yr = self.years

        def clean(x):
            x = float(x)
            return int(x) if x.is_integer() else x

        def v(key):
            val = self._val(model, p, key)
            if parent is None:
                return clean(val)
            pv = self._val(parent, p, key)
            return None if abs(val - pv) <= 1e-12 * max(1, abs(pv)) else clean(val)

        tech_names = {d["TechId"]: d["Tech"] for d in gd["osy-tech"]}
        out = []
        if group == "R":
            return [{"value": v((R,))}]
        if group == "RT":
            return [{self.tid[t]: v((R, t)) for t in self.m.sets["TECHNOLOGY"]}]
        if group == "RE":
            return [{self.eid[e]: v((R, e)) for e in self.m.sets["EMISSION"]}]
        if group == "RS":
            return [{self.sid[s]: v((R, s)) for s in self.m.sets["STORAGE"]}]
        if group == "RYCn":
            for u in self.m.sets["UDC"]:
                out.append({"ConId": self.uid[u], **{y: v((R, u, y)) for y in Yr}})
            return out
        if group == "RYTCn":
            for u in self.m.sets["UDC"]:
                for tid in sorted(self.cm.get(u, [])):
                    t = tech_names[tid]
                    out.append({"TechId": tid, "ConId": self.uid[u], **{y: v((R, t, u, y)) for y in Yr}})
            return out
        if group == "RYTs":
            return [{"TsId": self.lid[l], **{y: v((l, y)) for y in Yr}} for l in self.m.sets["TIMESLICE"]]
        if group == "RYDtb":
            return [{"DtbId": self.dtbid[b], **{y: v((b, y)) for y in Yr}} for b in self.m.sets["DAILYTIMEBRACKET"]]
        if group == "RYSeDt":
            return [{"SeId": self.seid[s], "DtId": self.dtid[d], **{y: v((s, d, y)) for y in Yr}}
                    for s in self.m.sets["SEASON"] for d in self.m.sets["DAYTYPE"]]
        if group == "RYT":
            return [{"TechId": self.tid[t], **{y: v((R, t, y)) for y in Yr}} for t in self.m.sets["TECHNOLOGY"]]
        if group == "RYTM":
            return [{"TechId": self.tid[t], "MoId": int(mo), **{y: v((R, t, mo, y)) for y in Yr}}
                    for t in self.m.sets["TECHNOLOGY"] for mo in self.modes]
        if group == "RYTC":
            return []
        if group == "RYTCM":
            key = "IAR" if p == "InputActivityRatio" else "OAR"
            comm_names = {d["CommId"]: d["Comm"] for d in gd["osy-comm"]}
            for tech in gd["osy-tech"]:
                for cid in tech[key]:
                    for mo in self.modes:
                        out.append({"TechId": tech["TechId"], "CommId": cid, "MoId": int(mo),
                                    **{y: v((R, tech["Tech"], comm_names[cid], mo, y)) for y in Yr}})
            return out
        if group == "RYS":
            return [{"StgId": self.sid[s], **{y: v((R, s, y)) for y in Yr}} for s in self.m.sets["STORAGE"]]
        if group == "RTSM":
            key = "TTS" if p == "TechnologyToStorage" else "TFS"
            for stg in gd["osy-stg"]:
                t = tech_names[stg[key]]
                for mo in self.modes:
                    out.append({"StgId": stg["StgId"], "TechId": stg[key], "MoId": int(mo),
                                "Value": v((R, t, stg["Stg"], mo))})
            return out
        if group == "RYTTs":
            return [{"TechId": self.tid[t], "TsId": self.lid[l], **{y: v((R, t, l, y)) for y in Yr}}
                    for t in self.m.sets["TECHNOLOGY"] for l in self.m.sets["TIMESLICE"]]
        if group == "RYC":
            return [{"CommId": self.cid[c], **{y: v((R, c, y)) for y in Yr}} for c in self.m.sets["COMMODITY"]]
        if group == "RYCTs":
            return [{"CommId": self.cid[c], "TsId": self.lid[l], **{y: v((R, c, l, y)) for y in Yr}}
                    for c in self.m.sets["COMMODITY"] for l in self.m.sets["TIMESLICE"]]
        if group == "RYE":
            return [{"EmisId": self.eid[e], **{y: v((R, e, y)) for y in Yr}} for e in self.m.sets["EMISSION"]]
        if group == "RYTEM":
            emis_names = {d["EmisId"]: d["Emis"] for d in gd["osy-emis"]}
            for tech in gd["osy-tech"]:
                for eid in tech["EAR"]:
                    for mo in self.modes:
                        out.append({"TechId": tech["TechId"], "EmisId": eid, "MoId": int(mo),
                                    **{y: v((R, tech["Tech"], emis_names[eid], mo, y)) for y in Yr}})
            return out
        raise KeyError(group)

    # -------------------------------------------------------------- write
    def write(self, outdir: Path, layers: list[tuple[str, str, str, Model, str | None]],
              caseruns: list[tuple[str, str, list[str]]]) -> Path:
        """layers: (scenario_id, name, desc, model, parent_id); SC_0 first.
        caseruns: (name, desc, [active scenario ids in order])."""
        root = Path(outdir) / self.casename
        if root.exists():
            shutil.rmtree(root)
        (root / "res").mkdir(parents=True)
        (root / "view").mkdir()
        gd = self.gen_data([(sid, name, desc) for sid, name, desc, _, _ in layers])
        models = {sid: mm for sid, _, _, mm, _ in layers}
        parents = {sid: par for sid, _, _, _, par in layers}
        (root / "genData.json").write_text(json.dumps(gd, indent=1))
        for group, params in MUIO_PARAMS.items():
            data = {}
            for pid, p in params.items():
                data[pid] = {}
                for sid, _, _, mm, par in layers:
                    data[pid][sid] = self.chunks(group, pid, p, mm, models[par] if par else None, gd)
            (root / f"{group}.json").write_text(json.dumps(data, separators=(",", ":")))
        sc_meta = {d["ScenarioId"]: d for d in gd["osy-scenarios"]}
        cases = []
        for i, (name, desc, active) in enumerate(caseruns):
            scen = [{"ScenarioId": s, "Scenario": sc_meta[s]["Scenario"], "Desc": sc_meta[s]["Desc"],
                     "Active": s in active} for s in [l[0] for l in layers]]
            cases.append({"Case": name, "CaseId": f"CS_{i}", "Desc": desc, "Runtime": "", "Scenarios": scen})
            (root / "res" / name / "csv").mkdir(parents=True)
        (root / "view" / "resData.json").write_text(json.dumps({"osy-cases": cases}, indent=1))
        (root / "view" / "viewDefinitions.json").write_text(json.dumps({"osy-views": {}}))
        return root


def zip_case(case_dir: Path, zip_path: Path) -> Path:
    zip_path = Path(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(Path(case_dir).rglob("*")):
            z.write(f, f.relative_to(Path(case_dir).parent))
    return zip_path


def verify_with_muio(case_dir: Path, muio_src: Path, caserun: str, workdir: Path) -> Path:
    """Generate the GMPL data file for one case run with MUIO's own code."""
    import os
    workdir = Path(workdir)
    if workdir.exists():
        shutil.rmtree(workdir)
    ds = workdir / "WebAPP" / "DataStorage"
    ds.mkdir(parents=True)
    for f in ["Parameters.json", "Variables.json"]:
        shutil.copy(Path(muio_src) / "WebAPP" / "DataStorage" / f, ds / f)
    for f in ["Duals.json", "Indicators.json"]:
        (ds / f).write_text("{}")
    (workdir / "WebAPP" / "SOLVERs").mkdir(parents=True)
    shutil.copytree(case_dir, ds / Path(case_dir).name)
    cwd = os.getcwd()
    sys.path.insert(0, str(Path(muio_src) / "API"))
    try:
        os.chdir(workdir)
        from Classes.Case.DataFileClass import DataFile  # noqa: E402  (MUIO source)
        df = DataFile(Path(case_dir).name)
        df.generateDatafile(caserun)
        res = ds / Path(case_dir).name / "res" / caserun
        df.preprocessData(res / "data.txt", res / "data_processed.txt")
        return res / "data_processed.txt"
    finally:
        os.chdir(cwd)
