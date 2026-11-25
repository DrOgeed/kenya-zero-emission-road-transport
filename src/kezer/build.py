"""Assemble the KEZERT base model (power + road transport + rail) for MUIO v5.7.

Power sector: CCG OSeMOSYS Kenya Power System Model v3.0.0 (PSM v3), ingested
from its published data file and adapted to the MUIO v5.7 formulation.
Transport: new stock-based module built from data/assumptions/*.csv.

Units
-----
energy PJ; power capacity GW; money million USD (2024); emissions Mt CO2;
passenger demand Gpkm; freight demand Gtkm; vehicle capacity thousand vehicles
(kveh); rail capacity Gpkm/yr or Gtkm/yr.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .data import CommMeta, Model, TechMeta, UDCMeta
from .gmpl_io import PARAM_INDEX, read_datafile_via_glpsol

ROOT = Path(__file__).resolve().parents[2]
ASSUME = ROOT / "data" / "assumptions"
PSM_DIR = ROOT / "data" / "external" / "ccg_kenya_psm_v3"
R = "RE1"
CO2 = "CO2"
GW_TO_PJ = 31.536
BRACKET_HOURS = {"1": 6, "2": 3, "3": 6, "4": 4, "5": 2, "6": 3}
BRACKET_LABEL = {"1": "00-06", "2": "06-09", "3": "09-15", "4": "15-19", "5": "19-21", "6": "21-24"}
SEASON_LABEL = {"1": "Jan-Mar (hot, dry)", "2": "Apr-May (long rains)",
                "3": "Jun-Sep (cool, dry)", "4": "Oct-Dec (short rains)"}
DAYTYPE_LABEL = {"1": "weekday", "2": "weekend"}
PEAK_BRACKETS = ("4", "5")   # 15:00-21:00, blocked for managed ('smart') charging

VEHICLE_CLASSES = {
    "MOTO": ("P_MOTO", "Gpkm"), "TW3": ("P_TW3", "Gpkm"), "CAR": ("P_CAR", "Gpkm"),
    "MAT": ("P_MAT", "Gpkm"), "MINI": ("P_MINI", "Gpkm"), "BUS": ("P_BUS", "Gpkm"),
    "LCV": ("F_LCV", "Gtkm"), "MDT": ("F_MDT", "Gtkm"), "HDT": ("F_HDT", "Gtkm"),
}
RAIL_CLASSES = {"RAILP": ("P_RAIL", "Gpkm"), "RAILF": ("F_RAIL", "Gtkm")}
CHARGERS = ["CHGT_HOME", "CHGT_DEPOT", "CHGT_SWAP", "CHGT_FAST"]

PSM_PARAM_INDEX = dict(PARAM_INDEX)
PSM_PARAM_INDEX.update({
    "DiscountRateIdv": ["REGION", "TECHNOLOGY", "YEAR"],
    "ReserveMargin": ["REGION", "YEAR"],
    "ReserveMarginTagFuel": ["REGION", "COMMODITY", "YEAR"],
    "ReserveMarginTagTechnology": ["REGION", "TECHNOLOGY", "YEAR"],
    "UDCMultiplierDemand": ["REGION", "COMMODITY", "UDC", "YEAR"],
})
PSM_PARAM_INDEX.pop("OperationalProfile")

PSM_TECH_DESC = {
    "BACKSTOP": "Unserved energy (value of lost load)", "BESS_TECH": "Battery energy storage (power block)",
    "DEMCOMELC": "Commercial electricity end use", "DEMINDELC": "Industrial electricity end use",
    "DEMRESELC": "Residential electricity end use", "EXPELC": "Electricity export",
    "IMPELC001": "Electricity import - Ethiopia", "IMPELC002": "Electricity import - Uganda",
    "PWRDIST": "Distribution network", "PWRTRN": "Transmission network",
    "PWRPHS001": "Pumped hydro storage 1", "PWRPHS002": "Pumped hydro storage 2",
    "PWRHFO001": "Heavy fuel oil plants", "PWRLFO001": "Light fuel oil / diesel plants",
    "PWRNGS001": "Natural gas (LNG) CCGT", "PWRCOA001": "Coal plant", "PWRURN001": "Nuclear",
    "PWRBIO001": "Biomass / bagasse",
}


def _years(first=2024, last=2060):
    return [str(y) for y in range(first, last + 1)]


def _interp(points: dict[int, float], years: list[str]) -> dict[str, float]:
    xs = sorted(points)
    return {y: float(np.interp(int(y), xs, [points[x] for x in xs])) for y in years}


def load_constants() -> dict[str, float]:
    c = pd.read_csv(ASSUME / "constants.csv")
    return dict(zip(c.name, c.value.astype(float)))


# =========================================================================
# Power sector (PSM v3)
# =========================================================================
def load_psm():
    return read_datafile_via_glpsol(PSM_DIR / "data.txt", PSM_DIR / "model.txt",
                                    param_index=PSM_PARAM_INDEX)


def build_power(m: Model, years: list[str], const: dict) -> None:
    psm_sets, P = load_psm()
    psm_years = psm_sets["YEAR"]
    last_psm = psm_years[-1]
    m.sets.update({k: psm_sets[k] for k in ["SEASON", "DAYTYPE", "DAILYTIMEBRACKET", "TIMESLICE",
                                             "MODE_OF_OPERATION", "STORAGE", "STORAGEINTRADAY",
                                             "STORAGEINTRAYEAR", "EMISSION"]})
    m.sets["REGION"] = [R]
    m.sets["YEAR"] = years
    ts = psm_sets["TIMESLICE"]

    def ymap(y):  # model year -> PSM year (hold 2050 values after 2050)
        return y if y in psm_years else last_psm

    # --- technology / commodity metadata ------------------------------------
    resource_comms = {"BIO", "COA", "COADOM", "GEO", "HFOMOM", "HFONAI", "HYD", "LFOELD",
                      "NGS", "SOL", "URN", "WND"}
    for c in psm_sets["COMMODITY"]:
        if c in resource_comms:
            m.add_comm(CommMeta(c, f"Primary energy / fuel for power: {c}", "PJ", "An"))
        else:
            desc = {"ELC001": "Electricity - generation busbar", "ELC002": "Electricity - transmission",
                    "ELC003": "Electricity - distribution (end-use level)",
                    "RESELC": "Residential electricity demand", "COMELC": "Commercial electricity demand",
                    "INDELC": "Industrial electricity demand"}.get(c, c)
            m.add_comm(CommMeta(c, desc, "PJ", "Ts"))
    for t in psm_sets["TECHNOLOGY"]:
        if t.startswith("PWRGEO"):
            d, g = f"Geothermal - resource block {t[-3:]}", "power"
        elif t.startswith("PWRWND"):
            d, g = f"Wind - supply region {t[-3:]}", "power"
        elif t.startswith("PWRSOL"):
            d, g = f"Solar PV - supply region {t[-3:]}", "power"
        elif t.startswith("PWRHYD"):
            d, g = f"Hydropower - group {t[-3:]}", "power"
        elif t.startswith(("MIN", "IMP")) and t not in ("IMPELC001", "IMPELC002"):
            d, g = f"Primary resource supply: {t[3:]}", "fuel"
        else:
            d = PSM_TECH_DESC.get(t, t)
            g = {"PWRDIST": "grid", "PWRTRN": "grid", "BESS_TECH": "storage", "PWRPHS001": "storage",
                 "PWRPHS002": "storage", "BACKSTOP": "slack"}.get(t, "power")
            if t.startswith("DEM"):
                g = "demand"
        cap = "GW" if (t.startswith(("PWR", "BESS", "IMPELC", "DEM", "EXPELC")) or t == "BACKSTOP") else "PJ/yr"
        m.add_tech(TechMeta(t, d, g, cap, "PJ", sector="power"))

    # --- copy parameters ------------------------------------------------------
    yearly = [p for p, idx in PSM_PARAM_INDEX.items() if idx[-1] == "YEAR" and p in P]
    skip = {"ReserveMargin", "ReserveMarginTagFuel", "ReserveMarginTagTechnology",
            "UDCMultiplierDemand", "UDCMultiplierTotalCapacity", "UDCMultiplierNewCapacity",
            "UDCMultiplierActivity", "UDCConstant", "DiscountRateIdv", "DaySplit", "DaysInDayType",
            "AccumulatedAnnualDemand", "TotalTechnologyAnnualActivityUpperLimit",
            "TechnologyActivityByModeUpperLimit", "TotalAnnualMaxCapacityInvestment",
            "TotalAnnualMaxCapacity", "AnnualEmissionLimit"}
    for p in yearly:
        if p in skip:
            continue
        df = P[p]
        dflt = {"CapacityFactor": 1, "AvailabilityFactor": 1, "VariableCost": 0.0001,
                "YearSplit": 1}.get(p, 0)
        df = df[df.VALUE != dflt]
        if df.empty:
            continue
        idx = PSM_PARAM_INDEX[p]
        by_year = {y: g for y, g in df.groupby("YEAR")}
        for y in years:
            g = by_year.get(ymap(y))
            if g is None:
                continue
            for row in g.itertuples(index=False):
                key = list(row[:-1])
                key[-1] = y
                m.set(p, tuple(key), row[-1])
    # upper limits with PSM 'no limit' = 9999/99999/999999 -> keep only binding ones
    for p in ["TotalAnnualMaxCapacity", "TotalAnnualMaxCapacityInvestment",
              "TotalTechnologyAnnualActivityUpperLimit"]:
        df = P[p]
        df = df[df.VALUE < 9000]
        by_year = {y: g for y, g in df.groupby("YEAR")}
        for y in years:
            g = by_year.get(ymap(y))
            if g is None:
                continue
            for row in g.itertuples(index=False):
                m.set(p, (R, row.TECHNOLOGY, y), row.VALUE)
    for p in ["Conversionls", "Conversionld", "Conversionlh"]:
        for row in P[p].itertuples(index=False):
            if row.VALUE:
                m.set(p, tuple(row[:-1]), row.VALUE)
    for p in ["CapacityToActivityUnit", "OperationalLife"]:
        for row in P[p].itertuples(index=False):
            m.set(p, tuple(row[:-1]), row.VALUE)
    for p in ["TechnologyToStorage", "TechnologyFromStorage"]:
        for row in P[p].itertuples(index=False):
            if row.VALUE:
                m.set(p, tuple(row[:-1]), row.VALUE)
    for row in P["OperationalLifeStorage"].itertuples(index=False):
        m.set("OperationalLifeStorage", tuple(row[:-1]), row.VALUE)
    # PSM uses tech-specific WACC by year; MUIO v5.7 takes one value per technology
    dri = P["DiscountRateIdv"]
    for row in dri[dri.YEAR == "2030"].itertuples(index=False):
        v = row.VALUE if row.VALUE < 1 else 0.10
        m.set("DiscountRateIdv", (R, row.TECHNOLOGY), v)

    # --- timeslice structure for MUIO storage equations ----------------------
    for y in years:
        for b, h in BRACKET_HOURS.items():
            m.set("DaySplit", (b, y), h / 8760)
        for s in m.sets["SEASON"]:
            m.set("DaysInDayType", (s, "1", y), 5)
            m.set("DaysInDayType", (s, "2", y), 2)

    # --- demand: PSM to 2050, then 3.5 %/yr ------------------------------------
    for c in ["RESELC", "COMELC", "INDELC"]:
        base = m.get("SpecifiedAnnualDemand", (R, c, last_psm))
        for y in years:
            if int(y) > int(last_psm):
                m.set("SpecifiedAnnualDemand", (R, c, y), base * 1.035 ** (int(y) - int(last_psm)))

    # --- existing (pre-2024) capacity: PSM pins 2019-2023 builds through
    #     Min/MaxCapacity; convert them to residual capacity -----------------
    minc, maxc, res = P["TotalAnnualMinCapacity"], P["TotalAnnualMaxCapacity"], P["ResidualCapacity"]
    ol = dict(zip(P["OperationalLife"].TECHNOLOGY, P["OperationalLife"].VALUE))
    stock_2024 = {}
    for t in psm_sets["TECHNOLOGY"]:
        r24 = res[(res.TECHNOLOGY == t) & (res.YEAR == "2024")].VALUE.sum()
        mn = minc[(minc.TECHNOLOGY == t) & (minc.YEAR == "2024")].VALUE.sum()
        mx = maxc[(maxc.TECHNOLOGY == t) & (maxc.YEAR == "2024")].VALUE
        mx = mx.iloc[0] if len(mx) and mx.iloc[0] < 9000 else 0
        existing = max(r24, mn)
        if t.startswith("PWRGEO") and mx > existing:      # geothermal fleet at PSM 2024 cap
            existing = mx
        extra = existing - r24
        if extra > 1e-6:
            stock_2024[t] = extra
            retire = 2022 + int(ol.get(t, 25))
            for y in years:
                if int(y) < retire:
                    cur = m.get("ResidualCapacity", (R, t, y), 0.0)
                    m.set("ResidualCapacity", (R, t, y), cur + extra)
    m.info["power_pre2024_capacity_added_as_residual_GW"] = stock_2024
    # PSM retirement paths (via MaxCapacity) can be earlier than the nominal
    # lifetime used above; never let residual exceed PSM's own maximum.
    mx = m.params.get("TotalAnnualMaxCapacity", {})
    for k, v in list(m.params["ResidualCapacity"].items()):
        if k in mx and v > mx[k]:
            m.params["ResidualCapacity"][k] = mx[k]
    # PSM forces committed builds through MinCapacity and retires sites through
    # a declining MaxCapacity. With a 2024 start, committed builds made in
    # 2024-2030 outlive PSM's retirement path; lift MaxCapacity just enough to
    # hold them (otherwise the model is infeasible by construction).
    mn = m.params.get("TotalAnnualMinCapacity", {})
    lifted = {}
    for t in {k[1] for k in mn}:
        life = int(m.get("OperationalLife", (R, t)))
        forced = {}
        for y in years:
            active = sum(v for yy, v in forced.items() if int(y) - int(yy) < life)
            need = mn.get((R, t, y), 0) - m.get("ResidualCapacity", (R, t, y), 0.0) - active
            if need > 1e-9:
                forced[y] = need
                active += need
            cap_k = (R, t, y)
            floor = m.get("ResidualCapacity", cap_k, 0.0) + active
            if cap_k in mx and mx[cap_k] < floor - 1e-9:
                lifted[cap_k] = (mx[cap_k], floor)
                mx[cap_k] = round(floor + 1e-6, 6)
    m.info["psm_maxcap_lifted"] = lifted

    # --- networks: PSM's residual T&D (1.58 GW) predates its 2019-23 builds and
    #     is below the 2024 peak; set the 2024 network to carry the 2024 peak
    #     (+3 % headroom) so the base year does not 'buy' an existing grid.
    rates = {l: sum(m.get("SpecifiedAnnualDemand", (R, c, years[0]), 0) *
                    m.get("SpecifiedDemandProfile", (R, c, l, years[0]), 0) for c in ["RESELC", "COMELC", "INDELC"])
             / m.get("YearSplit", (l, years[0])) for l in ts}
    peak_end_use = max(rates.values()) / GW_TO_PJ
    eta_d = m.get("OutputActivityRatio", (R, "PWRDIST", "ELC003", "1", years[0]))
    dist0, trn0 = peak_end_use / eta_d * 1.03, peak_end_use / eta_d * 1.03   # capacity on input side
    for y in years:
        m.set("ResidualCapacity", (R, "PWRDIST", y), max(dist0, m.get("ResidualCapacity", (R, "PWRDIST", y), 0)))
        m.set("ResidualCapacity", (R, "PWRTRN", y), max(trn0 / m.get("OutputActivityRatio", (R, "PWRTRN", "ELC002", "1", y)),
                                                        m.get("ResidualCapacity", (R, "PWRTRN", y), 0)))
    m.info["network_2024_residual_GW"] = {"PWRDIST": dist0, "PWRTRN": trn0}
    # committed min-capacity paths only matter for years >= 2024 (already copied)

    # --- technology learning on VRE and batteries (PSM holds costs ~flat) -----
    learn = pd.read_csv(ASSUME / "power_cost_learning.csv")
    for row in learn.itertuples(index=False):
        mult = _interp({2024: row[1], 2030: row[2], 2040: row[3], 2050: row[4], 2060: row[5]}, years)
        for t in [t for t in m.techs if t.startswith(row.tech_prefix)]:
            base = m.get("CapitalCost", (R, t, "2024"), 0.0)
            for y in years:
                m.set("CapitalCost", (R, t, y), base * mult[y])

    # --- battery storage -------------------------------------------------------
    # PSM v3 prices BESS_TECH at US$800/kW with energy capacity free (custom
    # storage block). In MUIO's standard storage block a power-only price would
    # let the model buy 0.75 GW of firm (reserve) capacity per GW without any
    # energy behind it. We therefore price the power block as a 4-hour system
    # (US$300/kW power + 4 h x US$150/kWh = US$900/kW in 2024, close to PSM's 800)
    # and charge only a small cost (US$25/kWh) for energy beyond 4 hours.
    bess_mult = _interp({2024: 1.0, 2030: 0.75, 2040: 0.60, 2050: 0.55, 2060: 0.52}, years)
    for y in years:
        m.set("CapitalCost", (R, "BESS_TECH", y), (300 + 4 * 150) * bess_mult[y])    # US$/kW (4 h)
        m.set("CapitalCostStorage", (R, "BESS001", y), 25 * 277.78 * bess_mult[y])    # US$/kWh -> M$/PJ
        m.drop("TotalAnnualMaxCapacity", lambda k, y=y: k[1] == "BESS_TECH")
    m.set("OperationalLifeStorage", (R, "BESS001"), 15)
    m.set("OperationalLife", (R, "BESS_TECH"), 15)
    for s in m.sets["STORAGE"]:
        m.set("StorageLevelStart", (R, s), 0)

    # --- backstop = unserved energy at VOLL ------------------------------------
    m.drop("CapitalCost", lambda k: k[1] == "BACKSTOP")
    m.drop("FixedCost", lambda k: k[1] == "BACKSTOP")
    m.set("OperationalLife", (R, "BACKSTOP"), 1)
    m.set("DiscountRateIdv", (R, "BACKSTOP"), 0.10)
    voll = const["voll_usd_per_kWh"] * 277.78  # M$/PJ
    # unserved energy is booked at the end-use (distribution) level, so that it
    # also absorbs shortfalls caused by a capped distribution network
    m.drop("OutputActivityRatio", lambda k: k[1] == "BACKSTOP")
    for y in years:
        m.set("VariableCost", (R, "BACKSTOP", "1", y), voll)
        m.set("OutputActivityRatio", (R, "BACKSTOP", "ELC003", "1", y), 1)

    # --- emissions factor units: PSM EAR in Mt/PJ (kept) ------------------------
    m.info["psm_param_tables"] = sorted(P)
    m.info["psm_reserve_tags"] = (P["ReserveMarginTagTechnology"].query("YEAR=='2030' and VALUE>0")
                                  .set_index("TECHNOLOGY").VALUE.to_dict())
    m.info["psm_reserve_margin"] = float(P["ReserveMargin"].VALUE.iloc[0])
    m.info["psm_udc"] = {k: P[k] for k in ["UDCMultiplierTotalCapacity", "UDCMultiplierDemand", "UDCTag"]}
    m.info["timeslices"] = ts


# =========================================================================
# Transport
# =========================================================================
def load_vehicles() -> pd.DataFrame:
    return pd.read_csv(ASSUME / "vehicle_technologies.csv")


def parse_inputs(s: str) -> dict[str, float]:
    out = {}
    for part in s.split(";"):
        c, v = part.split(":")
        out[c.strip()] = float(v)
    return out


def calibrate_vkt(veh: pd.DataFrame, const: dict) -> tuple[pd.DataFrame, dict]:
    """Scale annual km so that 2024 bottom-up fuel use matches KNBS road fuel.

    Classes are split into a petrol-dominated group (MOTO, TW3, CAR) and a
    diesel-dominated group (LCV, MAT, MINI, BUS, MDT, HDT); one scaling factor
    per group is solved from the 2x2 linear system of petrol and diesel
    balances (cross-fuel vehicles such as diesel cars are included)."""
    target_pet = const["petrol_demand_2024_kt"] * const["petrol_road_share"] * const["petrol_GJ_per_t"] / 1e3
    target_dsl = const["diesel_demand_2024_kt"] * const["diesel_road_share"] * const["diesel_GJ_per_t"] / 1e3
    pg = {"MOTO", "TW3", "CAR"}
    A = np.zeros((2, 2))
    for r in veh.itertuples():
        ins = parse_inputs(r.inputs)
        e = r.stock_2024 * r.annual_km * r.energy_MJ_per_vkm / 1e9  # PJ
        col = 0 if r._2 in pg else 1
        if "PET" in ins:
            A[0, col] += e * ins["PET"]
        if "DSL" in ins:
            A[1, col] += e * ins["DSL"]
    a, b = np.linalg.solve(A, np.array([target_pet, target_dsl]))
    veh = veh.copy()
    veh["annual_km_prior"] = veh.annual_km
    veh["annual_km"] = np.where(veh["class"].isin(pg), veh.annual_km * a, veh.annual_km * b)
    info = {"target_petrol_PJ": target_pet, "target_diesel_PJ": target_dsl,
            "prior_petrol_PJ": A[0].sum(), "prior_diesel_PJ": A[1].sum(),
            "vkt_scale_petrol_group": a, "vkt_scale_diesel_group": b}
    return veh, info


def build_transport(m: Model, years: list[str], const: dict) -> None:
    veh, cal = calibrate_vkt(load_vehicles(), const)
    m.info["calibration"] = cal
    m.info["vehicles"] = veh
    y0 = years[0]
    ts = m.sets["TIMESLICE"]

    # ---------------- commodities ----------------
    for cls, (dem, unit) in {**VEHICLE_CLASSES, **RAIL_CLASSES}.items():
        m.add_comm(CommMeta(dem, f"Transport service demand: {cls}", unit, "An"))
    m.add_comm(CommMeta("PET", "Motor gasoline (petrol)", "PJ", "An"))
    m.add_comm(CommMeta("DSL", "Automotive diesel", "PJ", "An"))
    m.add_comm(CommMeta("HVO", "Hydrotreated vegetable oil (renewable diesel)", "PJ", "An"))
    m.add_comm(CommMeta("H2", "Hydrogen (delivered, compressed)", "PJ", "An"))
    for c, d in {"CHG_HOME": "home/workplace AC charging", "CHG_DEPOT": "fleet depot charging",
                 "CHG_SWAP": "battery-swap network", "CHG_FAST": "public DC fast / corridor charging"}.items():
        # Seasonal balance on a representative-day timeslice structure = energy
        # balanced over the day, i.e. charging may be shifted within the day.
        m.add_comm(CommMeta(c, f"EV energy delivered via {d}", "PJ", "Se"))

    # ---------------- fuels ----------------
    fuels = pd.read_csv(ASSUME / "fuels.csv")
    for r in fuels.itertuples():
        m.add_tech(TechMeta(r.tech, r.description, "fuel", "PJ/yr", "PJ", sector="transport"))
        m.set("CapacityToActivityUnit", (R, r.tech), 1)
        m.set("OperationalLife", (R, r.tech), 1)
        m.set("DiscountRateIdv", (R, r.tech), 0.10)
        cost = _interp({2024: r.cost_usd_per_GJ_2024, 2030: r.cost_usd_per_GJ_2030,
                        2040: r.cost_usd_per_GJ_2040, 2050: r.cost_usd_per_GJ_2050,
                        2060: r.cost_usd_per_GJ_2050 * 1.05}, years)
        for y in years:
            m.set("OutputActivityRatio", (R, r.tech, r.output, "1", y), 1)
            m.set("VariableCost", (R, r.tech, "1", y), cost[y])
    m.info["fuel_ef"] = dict(zip(fuels.output, fuels.co2_t_per_TJ / 1000))  # Mt/PJ
    for y in years:  # renewable diesel only where a scenario opens it
        m.set("TotalTechnologyAnnualActivityUpperLimit", (R, "SUP_HVO", y), 0)

    # ---------------- vehicles ----------------
    ice_gain = const["ice_efficiency_gain_reference"]
    demand0 = {}
    for r in veh.itertuples():
        cls = r._2
        dem, unit = VEHICLE_CLASSES[cls]
        m.add_tech(TechMeta(r.tech, r.description, "vehicle", "kveh", unit, sector="transport",
                            vclass=cls, drivetrain=r.drivetrain, zev=bool(r.zev)))
        cta = r.annual_km * r.occupancy / 1e6                 # Gpkm (Gtkm) per kveh-yr
        m.set("CapacityToActivityUnit", (R, r.tech), cta)
        m.set("OperationalLife", (R, r.tech), int(r.life_yr))
        m.set("DiscountRateIdv", (R, r.tech), r.wacc)
        ins = parse_inputs(r.inputs)
        capex = _interp({2024: r.capex_2024, 2030: r.capex_2030, 2040: r.capex_2040,
                         2050: r.capex_2050, 2060: r.capex_2050}, years)
        gain = ice_gain if r.drivetrain in ("ICE", "HEV", "BIO") else 0.003
        for y in years:
            k = int(y) - int(y0)
            e_pkm = r.energy_MJ_per_vkm / r.occupancy * (1 - gain) ** k   # PJ per Gpkm
            for c, share in ins.items():
                m.set("InputActivityRatio", (R, r.tech, c, "1", y), e_pkm * share)
            m.set("OutputActivityRatio", (R, r.tech, dem, "1", y), 1)
            m.set("CapitalCost", (R, r.tech, y), capex[y] / 1000)     # M$ per kveh
            m.set("FixedCost", (R, r.tech, y), r.fom_usd_per_yr / 1000)
            ef = sum(m.info["fuel_ef"].get(c, 0) * s for c, s in ins.items() if c in ("PET", "DSL"))
            if ef:
                m.set("EmissionActivityRatio", (R, r.tech, CO2, "1", y), e_pkm * ef)
            # residual stock, uniform age distribution
            frac = max(0.0, 1 - k / r.life_yr)
            if r.stock_2024 and frac > 0:
                m.set("ResidualCapacity", (R, r.tech, y), r.stock_2024 / 1000 * frac)
        demand0[dem] = demand0.get(dem, 0) + r.stock_2024 * r.annual_km * r.occupancy / 1e9
    # HVO trucks only exist in the biofuel scenario
    for y in years:
        m.set("TotalAnnualMaxCapacityInvestment", (R, "HDT_HVO", y), 0)

    # ---------------- rail ----------------
    rail = pd.read_csv(ASSUME / "rail_technologies.csv")
    for r in rail.itertuples():
        dem, unit = RAIL_CLASSES[r._2]
        m.add_tech(TechMeta(r.tech, r.description, "rail", r.cap_unit, unit, sector="transport",
                            vclass=r._2, drivetrain="ELC" if "ELC" in r.tech else "ICE",
                            zev="ELC" in r.tech))
        m.set("CapacityToActivityUnit", (R, r.tech), 1)
        m.set("OperationalLife", (R, r.tech), int(r.life_yr))
        m.set("DiscountRateIdv", (R, r.tech), r.wacc)
        ins = parse_inputs(r.inputs)
        capex = _interp({2024: r.capex_2024, 2050: r.capex_2050, 2060: r.capex_2050}, years)
        for y in years:
            for c, s in ins.items():
                m.set("InputActivityRatio", (R, r.tech, c, "1", y), r.energy_MJ_per_unit * s)
            m.set("OutputActivityRatio", (R, r.tech, dem, "1", y), 1)
            m.set("CapitalCost", (R, r.tech, y), capex[y])
            m.set("FixedCost", (R, r.tech, y), capex[y] * r.fom_frac)
            if "DSL" in ins:
                m.set("EmissionActivityRatio", (R, r.tech, CO2, "1", y),
                      r.energy_MJ_per_unit * m.info["fuel_ef"]["DSL"])
            if r.residual_2024 and int(y) < r.residual_retire_year:
                m.set("ResidualCapacity", (R, r.tech, y), r.residual_2024)
        if r.residual_2024:
            demand0[dem] = demand0.get(dem, 0) + r.residual_2024 * 0.75   # 2024 utilisation of rail capacity

    # ---------------- transport demand ----------------
    growth = pd.read_csv(ASSUME / "demand_growth.csv").set_index("commodity")
    m.info["transport_demand_2024"] = demand0
    for dem, d0 in demand0.items():
        g = growth.loc[dem]
        val = d0
        for y in years:
            yi = int(y)
            if yi > int(y0):
                rate = (g.g_2025_2030 if yi <= 2030 else g.g_2031_2040 if yi <= 2040
                        else g.g_2041_2050 if yi <= 2050 else g.g_2051_2060)
                val *= 1 + rate
            m.set("AccumulatedAnnualDemand", (R, dem, y), val)

    # ---------------- charging infrastructure ----------------
    chg = pd.read_csv(ASSUME / "charging_technologies.csv")
    for r in chg.itertuples():
        grp = "charging"
        m.add_tech(TechMeta(r.tech, r.description, grp, "GW", "PJ", sector="transport"))
        m.set("CapacityToActivityUnit", (R, r.tech), GW_TO_PJ)
        m.set("OperationalLife", (R, r.tech), int(r.life_yr))
        m.set("DiscountRateIdv", (R, r.tech), r.wacc)
        capex = _interp({2024: r.capex_2024, 2030: r.capex_2030, 2040: r.capex_2040,
                         2050: r.capex_2050, 2060: r.capex_2050}, years)
        for y in years:
            m.set("CapitalCost", (R, r.tech, y), capex[y])
            m.set("FixedCost", (R, r.tech, y), capex[y] * r.fom_frac)
            if r.tech == "V2G_DEPOT":
                m.set("InputActivityRatio", (R, r.tech, "CHG_DEPOT", "1", y), 1 / r.efficiency)
                m.set("OutputActivityRatio", (R, r.tech, "ELC003", "1", y), 1)
                m.set("VariableCost", (R, r.tech, "1", y), 4.2)        # battery wear ~US$15/MWh
                m.set("TotalAnnualMaxCapacity", (R, r.tech, y), 0)      # opened by V2G scenario
            else:
                m.set("InputActivityRatio", (R, r.tech, "ELC003", "1", y), 1 / r.efficiency)
                m.set("OutputActivityRatio", (R, r.tech, r.output, "1", y), 1)
    # existing chargers in 2024 (approx. from EV stock; avoids zero-capacity start)
    for t, gw in {"CHGT_SWAP": 0.004, "CHGT_HOME": 0.002, "CHGT_DEPOT": 0.003, "CHGT_FAST": 0.002}.items():
        for y in years[:8]:
            m.set("ResidualCapacity", (R, t, y), gw)

    # ---------------- hydrogen ----------------
    h2 = pd.read_csv(ASSUME / "hydrogen.csv").iloc[0]
    m.add_tech(TechMeta("H2_ELY", h2.description, "hydrogen", "GW(H2)", "PJ", sector="transport"))
    m.set("CapacityToActivityUnit", (R, "H2_ELY"), GW_TO_PJ)
    m.set("OperationalLife", (R, "H2_ELY"), int(h2.life_yr))
    m.set("DiscountRateIdv", (R, "H2_ELY"), h2.wacc)
    capex = _interp({2024: h2.capex_2024, 2030: h2.capex_2030, 2040: h2.capex_2040,
                     2050: h2.capex_2050, 2060: h2.capex_2050}, years)
    eff = _interp({2024: h2.efficiency_2024, 2050: h2.efficiency_2050, 2060: h2.efficiency_2050}, years)
    vc = _interp({2024: h2.vc_usd_per_GJ_2024, 2050: h2.vc_usd_per_GJ_2050, 2060: h2.vc_usd_per_GJ_2050}, years)
    for y in years:
        m.set("InputActivityRatio", (R, "H2_ELY", "ELC002", "1", y), 1 / eff[y])
        m.set("OutputActivityRatio", (R, "H2_ELY", "H2", "1", y), 1)
        m.set("CapitalCost", (R, "H2_ELY", y), capex[y] / eff[y])     # per kW of H2 output
        m.set("FixedCost", (R, "H2_ELY", y), capex[y] / eff[y] * h2.fom_frac)
        m.set("VariableCost", (R, "H2_ELY", "1", y), vc[y])

    # ---------------- slack for firm-capacity shortfall ----------------
    m.add_tech(TechMeta("RSV_SHORTFALL", "Firm-capacity shortfall against the reserve-margin requirement (penalised slack)",
                        "slack", "GW", "-", sector="power"))
    m.set("CapacityToActivityUnit", (R, "RSV_SHORTFALL"), GW_TO_PJ)
    m.set("OperationalLife", (R, "RSV_SHORTFALL"), 1)
    m.set("DiscountRateIdv", (R, "RSV_SHORTFALL"), 0.10)
    for y in years:
        m.set("FixedCost", (R, "RSV_SHORTFALL", y), const["reserve_shortfall_penalty_usd_per_kW_yr"])


# =========================================================================
# Charging regimes, reserve margin, integration and diffusion constraints
# =========================================================================
def ts_frame(m: Model) -> pd.DataFrame:
    rows = []
    y0 = m.sets["YEAR"][0]
    for l in m.sets["TIMESLICE"]:
        se = next(k[1] for k in m.params["Conversionls"] if k[0] == l)
        dt = next(k[1] for k in m.params["Conversionld"] if k[0] == l)
        dtb = next(k[1] for k in m.params["Conversionlh"] if k[0] == l)
        rows.append((l, se, dt, dtb, m.get("YearSplit", (l, y0))))
    return pd.DataFrame(rows, columns=["ts", "season", "daytype", "bracket", "ys"]).set_index("ts")


def charging_profile(m: Model, regime: str) -> dict[str, dict[str, float]]:
    """Normalised share of each charger's annual energy by timeslice."""
    tsf = ts_frame(m)
    prof = pd.read_csv(ASSUME / "charging_profiles.csv")
    prof = prof[prof.regime == regime]
    out = {}
    for r in prof.itertuples():
        shares = dict(zip("123456", [r.b1_00_06, r.b2_06_09, r.b3_09_15, r.b4_15_19, r.b5_19_21, r.b6_21_24]))
        # energy per day by bracket x number of days represented by the timeslice
        w = {l: shares[row.bracket] * row.ys / (BRACKET_HOURS[row.bracket] / 8760 * 365) for l, row in tsf.iterrows()}
        tot = sum(w.values())
        out[r.charger] = {l: v / tot for l, v in w.items()}
    return out


def apply_charging_regime(m: Model, regime: str) -> None:
    """regime: 'unmanaged' | 'tou' | 'smart'."""
    years = m.sets["YEAR"]
    tsf = ts_frame(m)
    m.drop("OperationalProfile", lambda k: k[1] in CHARGERS)
    m.drop("CapacityFactor", lambda k: k[1] in CHARGERS)
    if regime in ("unmanaged", "tou"):
        prof = charging_profile(m, regime)
        for c, shares in prof.items():
            for y in years:
                for l, v in shares.items():
                    m.set("OperationalProfile", (R, c, l, y), round(v, 6))
    elif regime == "smart":
        prof = charging_profile(m, "unmanaged")          # fast charging stays need-driven
        for y in years:
            for l, v in prof["CHGT_FAST"].items():
                m.set("OperationalProfile", (R, "CHGT_FAST", l, y), round(v, 6))
            for c in ["CHGT_HOME", "CHGT_DEPOT", "CHGT_SWAP"]:
                for l, row in tsf.iterrows():
                    if row.bracket in PEAK_BRACKETS:
                        m.set("CapacityFactor", (R, c, l, y), 0)
    else:
        raise ValueError(regime)
    m.info["charging_regime"] = regime
    update_reserve_udc(m)


def peak_slices(m: Model) -> dict[str, str]:
    tsf = ts_frame(m)
    y = m.sets["YEAR"][0]
    ratio = {}
    for l, row in tsf.iterrows():
        d = sum(m.get("SpecifiedDemandProfile", (R, c, l, y), 0) for c in ["RESELC", "COMELC", "INDELC"]) / 3
        ratio[l] = d / row.ys
    l1 = max(ratio, key=ratio.get)
    l2 = max((l for l in ratio if tsf.loc[l, "bracket"] == "5"), key=ratio.get)
    return {"RM_PEAK_A": l1, "RM_PEAK_B": l2}


def nonev_rate_gw(m: Model, l: str, y: str) -> float:
    d = sum(m.get("SpecifiedAnnualDemand", (R, c, y), 0) * m.get("SpecifiedDemandProfile", (R, c, l, y), 0)
            for c in ["RESELC", "COMELC", "INDELC"])
    eta = m.get("OutputActivityRatio", (R, "PWRDIST", "ELC003", "1", y)) * \
        m.get("OutputActivityRatio", (R, "PWRTRN", "ELC002", "1", y))
    return d / m.get("YearSplit", (l, y)) / eta / GW_TO_PJ


def update_reserve_udc(m: Model) -> None:
    """Firm capacity >= RM x (non-EV peak + EV charging at peak), two slices."""
    years = m.sets["YEAR"]
    rm_target = m.info["psm_reserve_margin"]
    # Kenya's actual 2024-25 margin is thin (firm ~2.5 GW vs 2.3-2.5 GW peak,
    # KPLC 2025); require 1.05 in 2024-26 rising linearly to the PSM/LCPDP
    # planning criterion (1.25) by 2030, instead of forcing an instant fix.
    rm_path = _interp({2024: 1.05, 2026: 1.05, 2030: rm_target, 2060: rm_target}, years)
    m.info["reserve_margin_path"] = rm_path
    tags = dict(m.info["psm_reserve_tags"])
    tags.pop("BACKSTOP", None)
    tags.update({"RSV_SHORTFALL": 1.0, "V2G_DEPOT": 0.5})
    slices = peak_slices(m)
    m.info["reserve_slices"] = slices
    for u, l in slices.items():
        m.udcs[u] = UDCMeta(u, f"Reserve margin at timeslice {l}: firm capacity >= RM(y) x peak incl. EV charging (RM 1.05 in 2024-26 -> {rm_target} from 2030)", 0)
        m.drop("UDCMultiplierTotalCapacity", lambda k, u=u: k[2] == u)
        m.drop("UDCMultiplierActivity", lambda k, u=u: k[2] == u)
        m.drop("UDCConstant", lambda k, u=u: k[1] == u)
        for y in years:
            rm = rm_path[y]
            for t, tag in tags.items():
                if t in m.techs:
                    m.set("UDCMultiplierTotalCapacity", (R, t, u, y), -tag)
            eta = m.get("OutputActivityRatio", (R, "PWRDIST", "ELC003", "1", y)) * \
                m.get("OutputActivityRatio", (R, "PWRTRN", "ELC002", "1", y))
            ys = m.get("YearSplit", (l, y))
            for c in CHARGERS:
                prof = {k[2]: v for k, v in m.params.get("OperationalProfile", {}).items()
                        if k[1] == c and k[3] == y}
                if prof:
                    share = prof.get(l, 0) / sum(prof.values())
                else:   # unprofiled ('smart'): blocked in peak brackets -> no peak draw
                    share = 0.0
                iar = m.get("InputActivityRatio", (R, c, "ELC003", "1", y))
                kappa = iar * share / ys / eta / GW_TO_PJ
                if kappa:
                    m.set("UDCMultiplierActivity", (R, c, u, y), rm * kappa)
            m.set("UDCConstant", (R, u, y), -rm * nonev_rate_gw(m, l, y))


def add_vre_integration_udc(m: Model) -> None:
    """PSM v3 'DemVsWind/DemVsSol' limits (zone capacity proportional to grid
    demand), generalised so that EV, rail and electrolyser load also count as
    demand. MUIO has no UDCMultiplierDemand, so exogenous demand moves to the
    right-hand side."""
    years = m.sets["YEAR"]
    U = m.info["psm_udc"]
    tags = U["UDCTag"]
    mult = U["UDCMultiplierTotalCapacity"]
    psm_years = sorted(mult.YEAR.unique())
    for u in tags.UDC:
        desc = ("Gas infrastructure prerequisite (PSM v3)" if u == "GasInfraPrereq"
                else f"PSM v3 VRE integration limit {u}: zone capacity x k <= grid demand")
        m.udcs[u] = UDCMeta(u, desc, 0)
        sub = mult[(mult.UDC == u) & (mult.VALUE != 0)]
        for y in years:
            py = y if y in psm_years else psm_years[-1]
            for row in sub[sub.YEAR == py].itertuples(index=False):
                m.set("UDCMultiplierTotalCapacity", (R, row.TECHNOLOGY, u, y), row.VALUE)
            if u != "GasInfraPrereq":
                dem = sum(m.get("SpecifiedAnnualDemand", (R, c, y), 0) for c in ["RESELC", "COMELC", "INDELC"])
                m.set("UDCConstant", (R, u, y), dem)
                for t in CHARGERS + ["H2_ELY", "RAILF_ELC", "RAILP_ELC"]:
                    c = "ELC003" if t in CHARGERS else "ELC002"
                    m.set("UDCMultiplierActivity", (R, t, u, y), -m.get("InputActivityRatio", (R, t, c, "1", y)))


def zev_cap_table(cap_df: pd.DataFrame, years: list[str]) -> dict[str, dict[str, float]]:
    out = {}
    for r in cap_df.itertuples(index=False):
        pts = {int(c): float(getattr(r, f"_{i+1}")) for i, c in enumerate(cap_df.columns[1:-1])}
        out[r[0]] = _interp(pts, years)
    return out


def set_zev_caps(m: Model, caps: dict[str, dict[str, float]]) -> None:
    """New ZEV capacity <= s(y) x all new capacity of the class (sales share)."""
    years = m.sets["YEAR"]
    for cls in VEHICLE_CLASSES:
        u = f"ZEVCAP_{cls}"
        m.udcs[u] = UDCMeta(u, f"Maximum zero-emission share of new {cls} vehicles (diffusion limit)", 0)
        m.drop("UDCMultiplierNewCapacity", lambda k, u=u: k[2] == u)
        techs = [t for t, me in m.techs.items() if me.group == "vehicle" and me.vclass == cls]
        for y in years:
            s = caps[cls][y]
            for t in techs:
                coef = (1 - s) if m.techs[t].zev else -s
                if coef:
                    m.set("UDCMultiplierNewCapacity", (R, t, u, y), coef)
            m.set("UDCConstant", (R, u, y), 0)
    m.info["zev_caps"] = caps


def add_hev_cap(m: Model) -> None:
    """New hybrid cars <= s(y) x all new cars (used-import supply limit)."""
    years = m.sets["YEAR"]
    cap = pd.read_csv(ASSUME / "hev_sales_cap.csv").iloc[0]
    pts = {int(c): float(cap[c]) for c in cap.index if c.isdigit()}
    s = _interp(pts, years)
    u = "HEVCAP_CAR"
    m.udcs[u] = UDCMeta(u, "Maximum hybrid share of new cars (used-import supply limit)", 0)
    techs = [t for t, me in m.techs.items() if me.group == "vehicle" and me.vclass == "CAR"]
    for y in years:
        for t in techs:
            coef = (1 - s[y]) if t == "CAR_HEV" else -s[y]
            m.set("UDCMultiplierNewCapacity", (R, t, u, y), coef)
        m.set("UDCConstant", (R, u, y), 0)


def add_build_rate_udcs(m: Model) -> None:
    """Group build-rate limits (GW/yr); loose by default, tightened in the
    grid-constrained scenario."""
    years = m.sets["YEAR"]
    groups = {
        "BUILD_GEO": ("Annual new geothermal capacity limit (GW/yr)", lambda t: t.startswith("PWRGEO")),
        "BUILD_VRE": ("Annual new wind + solar capacity limit (GW/yr)", lambda t: t.startswith(("PWRWND", "PWRSOL"))),
        "BUILD_BESS": ("Annual new battery power capacity limit (GW/yr)", lambda t: t == "BESS_TECH"),
        "BUILD_DIST": ("Annual distribution network reinforcement limit (GW/yr)", lambda t: t == "PWRDIST"),
        "BUILD_FIRM": ("Annual new firm thermal / hydro / nuclear / pumped-hydro capacity limit (GW/yr)",
                       lambda t: t.startswith(("PWRNGS", "PWRCOA", "PWRURN", "PWRHYD", "PWRBIO", "PWRPHS"))),
    }
    for u, (desc, f) in groups.items():
        m.udcs[u] = UDCMeta(u, desc, 0)
        for y in years:
            for t in m.techs:
                if f(t):
                    m.set("UDCMultiplierNewCapacity", (R, t, u, y), 1)
            m.set("UDCConstant", (R, u, y), 99)


def add_v2g_udc(m: Model) -> None:
    """V2G power <= available bidirectional power of parked BEV depot fleets."""
    years = m.sets["YEAR"]
    u = "V2G_LIMIT"
    m.udcs[u] = UDCMeta(u, "V2G discharge capacity <= 20% availability x bidirectional kW of BEV depot fleets", 0)
    kw = {"BUS_BEV": 100, "MINI_BEV": 60, "MAT_BEV": 30, "MDT_BEV": 60, "HDT_BEV": 150, "LCV_BEV": 11}
    for y in years:
        m.set("UDCMultiplierTotalCapacity", (R, "V2G_DEPOT", u, y), 1)
        for t, k in kw.items():
            m.set("UDCMultiplierTotalCapacity", (R, t, u, y), -0.2 * k / 1000)   # GW per kveh
        m.set("UDCConstant", (R, u, y), 0)


# =========================================================================
def build_base(first=2024, last=2060) -> Model:
    const = load_constants()
    years = _years(first, last)
    m = Model()
    build_power(m, years, const)
    build_transport(m, years, const)
    m.set("DiscountRate", (R,), const["social_discount_rate"])
    add_vre_integration_udc(m)
    add_build_rate_udcs(m)
    add_v2g_udc(m)
    add_hev_cap(m)
    caps = zev_cap_table(pd.read_csv(ASSUME / "zev_sales_cap_reference.csv"), years)
    set_zev_caps(m, caps)
    apply_charging_regime(m, "tou")           # current policy: EPRA e-mobility TOU tariff
    m.finalise_sets()
    m.info["constants"] = const
    return m
