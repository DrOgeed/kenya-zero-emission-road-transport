"""Post-processing: turn raw solution variables into the indicators reported
in the scenario report (all tables tidy: scenario, year, item, value, unit)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .build import CHARGERS, GW_TO_PJ, R, ts_frame
from .data import Model

PJ_TO_TWH = 1 / 3.6
POWER_TYPES = {
    "PWRGEO": "Geothermal", "PWRHYD": "Hydro", "PWRWND": "Wind", "PWRSOL": "Solar PV",
    "PWRHFO": "Oil (HFO)", "PWRLFO": "Oil (LFO/diesel)", "PWRNGS": "Natural gas", "PWRCOA": "Coal",
    "PWRURN": "Nuclear", "PWRBIO": "Bioenergy", "IMPELC": "Imports", "BESS_TECH": "Battery storage",
    "PWRPHS": "Pumped hydro", "BACKSTOP": "Unserved energy", "V2G_DEPOT": "Vehicle-to-grid",
}


def power_type(t: str) -> str | None:
    for k, v in POWER_TYPES.items():
        if t.startswith(k):
            return v
    return None


def _v(res, var):
    df = res["vars"].get(var)
    if df is None or df.empty:
        return pd.DataFrame(columns=["TECHNOLOGY", "YEAR", "VALUE"])
    return df


def indicators(m: Model, res: dict, scenario: str) -> dict[str, pd.DataFrame]:
    years = [int(y) for y in m.sets["YEAR"]]
    tsf = ts_frame(m)
    const = m.info["constants"]
    techs = m.techs
    out = {}

    cap = _v(res, "TotalCapacityAnnual").copy()
    cap["YEAR"] = cap.YEAR.astype(int)
    new = _v(res, "NewCapacity").copy()
    new["YEAR"] = new.YEAR.astype(int)
    act = _v(res, "TotalTechnologyAnnualActivity").copy()
    act["YEAR"] = act.YEAR.astype(int)
    actm = _v(res, "TotalAnnualTechnologyActivityByMode").copy()
    actm["YEAR"] = actm.YEAR.astype(int)
    roa = _v(res, "RateOfActivity").copy()
    roa["YEAR"] = roa.YEAR.astype(int)

    def meta(df):
        df = df.copy()
        df["group"] = df.TECHNOLOGY.map(lambda t: techs[t].group if t in techs else "")
        df["vclass"] = df.TECHNOLOGY.map(lambda t: techs[t].vclass if t in techs else "")
        df["drivetrain"] = df.TECHNOLOGY.map(lambda t: techs[t].drivetrain if t in techs else "")
        df["zev"] = df.TECHNOLOGY.map(lambda t: techs[t].zev if t in techs else False)
        return df

    # ---------------- fleet ----------------
    vcap = meta(cap[cap.TECHNOLOGY.map(lambda t: techs[t].group == "vehicle")])
    vcap = vcap.assign(item=vcap.vclass + "|" + vcap.drivetrain, value=vcap.VALUE * 1000, unit="vehicles")
    # vehicles actually in use = activity / service per vehicle (idle, i.e.
    # stranded or scrapped, vehicles excluded)
    va = act[act.TECHNOLOGY.isin(vcap.TECHNOLOGY.unique())].set_index(["TECHNOLOGY", "YEAR"]).VALUE
    vcap["in_use"] = [va.get((t, y), 0.0) / m.get("CapacityToActivityUnit", (R, t)) * 1000
                      for t, y in zip(vcap.TECHNOLOGY, vcap.YEAR)]
    out["fleet"] = vcap[["YEAR", "TECHNOLOGY", "vclass", "drivetrain", "zev", "value", "in_use", "unit"]]
    vnew = meta(new[new.TECHNOLOGY.map(lambda t: techs[t].group == "vehicle")])
    vnew = vnew.assign(value=vnew.VALUE * 1000, unit="vehicles/yr")
    out["sales"] = vnew[["YEAR", "TECHNOLOGY", "vclass", "drivetrain", "zev", "value", "unit"]]

    # ---------------- emissions ----------------
    em = _v(res, "AnnualTechnologyEmission").copy()
    em["YEAR"] = em.YEAR.astype(int)
    em = meta(em)
    em["sector"] = np.where(em.group == "vehicle", "Road transport",
                            np.where(em.group == "rail", "Rail", "Power"))
    out["emissions"] = em.groupby(["YEAR", "sector", "vclass"], as_index=False).VALUE.sum().rename(
        columns={"VALUE": "MtCO2"})

    # ---------------- fuels & fiscal ----------------
    fuel = act[act.TECHNOLOGY.isin(["IMP_PET", "IMP_DSL", "SUP_HVO"])].copy()
    mj = {"IMP_PET": const["petrol_MJ_per_L"], "IMP_DSL": const["diesel_MJ_per_L"], "SUP_HVO": 34.4}
    tax = {"IMP_PET": const["fuel_tax_petrol_usd_per_L"], "IMP_DSL": const["fuel_tax_diesel_usd_per_L"],
           "SUP_HVO": 0.0}
    fuel["PJ"] = fuel.VALUE
    fuel["billion_L"] = fuel.VALUE * 1e9 / fuel.TECHNOLOGY.map(mj) / 1e9
    fuel["import_bill_MUSD"] = fuel.apply(
        lambda r: r.VALUE * m.get("VariableCost", (R, r.TECHNOLOGY, "1", str(r.YEAR))), axis=1)
    fuel["fuel_tax_MUSD"] = fuel.billion_L * 1e9 * fuel.TECHNOLOGY.map(tax) / 1e6
    out["fuels"] = fuel[["YEAR", "TECHNOLOGY", "PJ", "billion_L", "import_bill_MUSD", "fuel_tax_MUSD"]]

    # ---------------- electricity supply ----------------
    gen = actm.copy()
    gen["type"] = gen.TECHNOLOGY.map(power_type)
    gen = gen[gen.type.notna()]
    # storage: only mode 2 (discharge) is generation
    is_sto = gen.TECHNOLOGY.isin(["BESS_TECH", "PWRPHS001", "PWRPHS002"])
    gen = gen[~is_sto | (gen.MODE_OF_OPERATION == "2")]
    gen["TWh"] = gen.VALUE.copy()
    sto2 = gen.TECHNOLOGY.isin(["BESS_TECH", "PWRPHS001", "PWRPHS002"])
    gen.loc[sto2, "TWh"] = gen.loc[sto2].apply(
        lambda r: r.VALUE * m.get("OutputActivityRatio", (R, r.TECHNOLOGY, "ELC001", "2", str(r.YEAR))), axis=1)
    gen["TWh"] = gen.TWh * PJ_TO_TWH
    out["generation"] = gen.groupby(["YEAR", "type"], as_index=False).TWh.sum()

    pc = cap.copy()
    pc["type"] = pc.TECHNOLOGY.map(power_type)
    pc = pc[pc.type.notna() & (pc.TECHNOLOGY != "BACKSTOP")]
    out["power_capacity"] = pc.groupby(["YEAR", "type"], as_index=False).VALUE.sum().rename(columns={"VALUE": "GW"})

    # ---------------- electricity demand incl. EVs ----------------
    rows = []
    for y in years:
        ys = str(y)
        nonev = sum(m.get("SpecifiedAnnualDemand", (R, c, ys), 0) for c in ["RESELC", "COMELC", "INDELC"])
        ev = {}
        for t in CHARGERS:
            a = act[(act.TECHNOLOGY == t) & (act.YEAR == y)].VALUE.sum()
            ev[t] = a * m.get("InputActivityRatio", (R, t, "ELC003", "1", ys))
        h2 = act[(act.TECHNOLOGY == "H2_ELY") & (act.YEAR == y)].VALUE.sum() * \
            m.get("InputActivityRatio", (R, "H2_ELY", "ELC002", "1", ys))
        rail = sum(act[(act.TECHNOLOGY == t) & (act.YEAR == y)].VALUE.sum() *
                   m.get("InputActivityRatio", (R, t, "ELC002", "1", ys)) for t in ["RAILF_ELC", "RAILP_ELC"])
        rows.append({"YEAR": y, "non_transport_TWh": nonev * PJ_TO_TWH,
                     "ev_charging_TWh": sum(ev.values()) * PJ_TO_TWH,
                     **{f"{k}_TWh": v * PJ_TO_TWH for k, v in ev.items()},
                     "hydrogen_TWh": h2 * PJ_TO_TWH, "rail_TWh": rail * PJ_TO_TWH})
    out["electricity_demand"] = pd.DataFrame(rows)

    # ---------------- peak, firm capacity, reserve margin ----------------
    dist_in = []
    rtot = roa.copy()
    rtot["iar"] = rtot.apply(lambda r: m.get("InputActivityRatio", (R, r.TECHNOLOGY, "ELC003", r.MODE_OF_OPERATION, str(r.YEAR))), axis=1)
    rtot["oar"] = rtot.apply(lambda r: m.get("OutputActivityRatio", (R, r.TECHNOLOGY, "ELC003", r.MODE_OF_OPERATION, str(r.YEAR))), axis=1)
    tags = dict(m.info["psm_reserve_tags"])
    tags.pop("BACKSTOP", None)
    tags.update({"V2G_DEPOT": 0.5})
    peak_rows = []
    for y in years:
        ys = str(y)
        eta = m.get("OutputActivityRatio", (R, "PWRDIST", "ELC003", "1", ys)) * \
            m.get("OutputActivityRatio", (R, "PWRTRN", "ELC002", "1", ys))
        sub = rtot[rtot.YEAR == y]
        best = (0, None, 0, 0)
        for l in tsf.index:
            nonev = sum(m.get("SpecifiedAnnualDemand", (R, c, ys), 0) * m.get("SpecifiedDemandProfile", (R, c, l, ys), 0)
                        for c in ["RESELC", "COMELC", "INDELC"]) / tsf.loc[l, "ys"]
            s = sub[sub.TIMESLICE == l]
            evd = (s[s.TECHNOLOGY.isin(CHARGERS)].VALUE * s[s.TECHNOLOGY.isin(CHARGERS)].iar).sum()
            v2g = (s[s.TECHNOLOGY == "V2G_DEPOT"].VALUE * s[s.TECHNOLOGY == "V2G_DEPOT"].oar).sum()
            tot = (nonev + evd - v2g) / eta / GW_TO_PJ
            if tot > best[0]:
                best = (tot, l, evd / eta / GW_TO_PJ, nonev / eta / GW_TO_PJ)
        c = cap[cap.YEAR == y]
        firm = sum(c[c.TECHNOLOGY == t].VALUE.sum() * v for t, v in tags.items())
        short = c[c.TECHNOLOGY == "RSV_SHORTFALL"].VALUE.sum()
        unserved = act[(act.TECHNOLOGY == "BACKSTOP") & (act.YEAR == y)].VALUE.sum() * PJ_TO_TWH
        peak_rows.append({"YEAR": y, "peak_GW": best[0], "peak_timeslice": best[1],
                          "ev_at_peak_GW": best[2], "non_ev_at_peak_GW": best[3],
                          "firm_capacity_GW": firm, "reserve_margin": firm / best[0] if best[0] else np.nan,
                          "reserve_shortfall_GW": short, "unserved_energy_TWh": unserved})
    out["adequacy"] = pd.DataFrame(peak_rows)

    # ---------------- infrastructure ----------------
    infra = cap[cap.TECHNOLOGY.isin(CHARGERS + ["PWRDIST", "PWRTRN", "H2_ELY", "V2G_DEPOT"])]
    out["infrastructure"] = infra.rename(columns={"VALUE": "GW"})[["YEAR", "TECHNOLOGY", "GW"]]
    sto = _v(res, "AccumulatedNewStorageCapacity").copy()
    if not sto.empty:
        sto["YEAR"] = sto.YEAR.astype(int)
        sto["GWh"] = sto.VALUE * 277.78
        out["storage_energy"] = sto[["YEAR", "STORAGE", "GWh"]]

    # ---------------- costs (undiscounted annual, M$) ----------------
    inv = _v(res, "CapitalInvestment").copy()
    inv["YEAR"] = inv.YEAR.astype(int)
    inv = meta(inv)
    inv["sector"] = inv.group.map(lambda g: {"vehicle": "Vehicles", "rail": "Rail", "charging": "EV charging",
                                             "hydrogen": "Hydrogen", "grid": "Grid (T&D)", "storage": "Storage",
                                             "power": "Generation"}.get(g, "Other"))
    sinv = _v(res, "CapitalInvestmentStorage").copy()
    rows = inv.groupby(["YEAR", "sector"], as_index=False).VALUE.sum()
    if not sinv.empty:
        sinv["YEAR"] = sinv.YEAR.astype(int)
        rows = pd.concat([rows, sinv.groupby("YEAR", as_index=False).VALUE.sum().assign(sector="Storage")])
    out["investment"] = rows.groupby(["YEAR", "sector"], as_index=False).VALUE.sum().rename(columns={"VALUE": "MUSD"})

    opex = []
    for r in actm.itertuples(index=False):
        vc = m.get("VariableCost", (R, r.TECHNOLOGY, r.MODE_OF_OPERATION, str(r.YEAR)))
        if vc > 0.001:
            opex.append((r.YEAR, r.TECHNOLOGY, vc * r.VALUE))
    for r in cap.itertuples(index=False):
        fc = m.get("FixedCost", (R, r.TECHNOLOGY, str(r.YEAR)), 0)
        if fc:
            opex.append((r.YEAR, r.TECHNOLOGY, fc * r.VALUE))
    op = pd.DataFrame(opex, columns=["YEAR", "TECHNOLOGY", "MUSD"])
    op = meta(op)
    op["sector"] = np.where(op.TECHNOLOGY.isin(["IMP_PET", "IMP_DSL", "SUP_HVO"]), "Transport fuels",
                            np.where(op.group == "vehicle", "Vehicle O&M",
                                     np.where(op.TECHNOLOGY.str.startswith(("MIN", "IMP")), "Power fuels",
                                              np.where(op.TECHNOLOGY == "RSV_SHORTFALL", "Reserve shortfall penalty",
                                                       np.where(op.TECHNOLOGY == "BACKSTOP", "Unserved energy",
                                                                "Other O&M")))))
    out["opex"] = op.groupby(["YEAR", "sector"], as_index=False).MUSD.sum()

    # ---------------- marginal cost of electricity (from duals) ----------------
    d = res.get("duals_ELC003")
    if d is not None and not d.empty:
        d = d.copy()
        d["YEAR"] = d.YEAR.astype(int)
        dr = m.get("DiscountRate", (R,))
        d["ys"] = d.TIMESLICE.map(tsf.ys)
        # the balance row is in PJ of energy delivered in the slice, so its dual
        # is discounted M$ per PJ; undiscount (mid-year) and convert to US$/kWh
        d["usd_per_kWh"] = d.VALUE * (1 + dr) ** (d.YEAR - years[0] + 0.5) / 277.78
        dem = []
        for y in years:
            w = {l: sum(m.get("SpecifiedAnnualDemand", (R, c, str(y)), 0) *
                        m.get("SpecifiedDemandProfile", (R, c, l, str(y)), 0) for c in ["RESELC", "COMELC", "INDELC"])
                 for l in tsf.index}
            s = d[d.YEAR == y]
            avg = (s.usd_per_kWh * s.TIMESLICE.map(w)).sum() / max(sum(w.values()), 1e-9)
            pk = s[s.TIMESLICE.map(tsf.bracket).isin(["4", "5"])].usd_per_kWh.mean()
            off = s[s.TIMESLICE.map(tsf.bracket).isin(["1", "6"])].usd_per_kWh.mean()
            dem.append({"YEAR": y, "avg_marginal_usd_per_kWh": avg, "peak_marginal_usd_per_kWh": pk,
                        "offpeak_marginal_usd_per_kWh": off})
        out["electricity_price"] = pd.DataFrame(dem)

    # ---------------- totals ----------------
    obj = res["objective"]
    # constant term not in LP: fixed O&M on residual capacity (discounted)
    const_term = 0.0
    dr = m.get("DiscountRate", (R,))
    for (r_, t, y), v in m.params.get("ResidualCapacity", {}).items():
        fc = m.get("FixedCost", (R, t, y), 0)
        if fc:
            const_term += v * fc / (1 + dr) ** (int(y) - years[0] + 0.5)
    out["summary"] = pd.DataFrame([{
        "total_discounted_system_cost_MUSD": obj + const_term,
        "objective_MUSD": obj, "residual_fixed_cost_constant_MUSD": const_term,
        "status": res["status"], "solve_s": res["t_solve_s"],
    }])
    for k, df in out.items():
        df.insert(0, "scenario", scenario)
    return out
