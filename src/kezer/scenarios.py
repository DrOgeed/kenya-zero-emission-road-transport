"""Scenario definitions as deltas on the base model.

Every scenario is a list of (parent, modifier) steps so that it maps onto
MUIO's layered scenarios: a MUIO case run activates the base data (SC_0)
followed by the scenario layers in order.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .build import (R, VEHICLE_CLASSES, _interp, apply_charging_regime, set_zev_caps, update_reserve_udc)
from .data import Model

Y = lambda m: m.sets["YEAR"]


# ---------------------------------------------------------------- helpers
def _veh(m: Model, cls=None, zev=None):
    return [t for t, me in m.techs.items() if me.group == "vehicle"
            and (cls is None or me.vclass == cls) and (zev is None or me.zev == zev)]


def phased_bans(bans: dict[str, int], ze_year: int = 2050, exempt=("HDT_HVO",)):
    """ICE new-registration (incl. used-import) bans by class + zero-emission
    fleet from ze_year. ZEV sales-share caps ramp linearly from their 2026
    reference value to 100 % in the ban year."""
    def f(m: Model):
        caps = {k: dict(v) for k, v in m.info["zev_caps"].items()}
        for cls, ban in bans.items():
            for t in _veh(m, cls, zev=False):
                if t in exempt:
                    continue
                for y in Y(m):
                    if int(y) >= ban:
                        m.set("TotalAnnualMaxCapacityInvestment", (R, t, y), 0)
            s0 = caps[cls]["2026"]
            for y in Y(m):
                yi = int(y)
                if 2026 < yi < ban:
                    caps[cls][y] = max(caps[cls][y], s0 + (1 - s0) * (yi - 2026) / (ban - 2026))
                elif yi >= ban:
                    caps[cls][y] = 1.0
        set_zev_caps(m, caps)
        for t in _veh(m, zev=False):
            if t in exempt:
                continue
            for y in Y(m):
                if int(y) >= ze_year:
                    m.set("TotalTechnologyAnnualActivityUpperLimit", (R, t, y), 0)
        m.info["bans"] = bans
    return f


BANS_CENTRAL = {"MOTO": 2030, "TW3": 2030, "BUS": 2032, "MAT": 2033, "MINI": 2033,
                "CAR": 2035, "LCV": 2035, "MDT": 2038, "HDT": 2040}
BANS_EARLY = {"MOTO": 2027, "TW3": 2027, "BUS": 2030, "MAT": 2030, "MINI": 2030,
              "CAR": 2032, "LCV": 2032, "MDT": 2035, "HDT": 2035}
BANS_LATE = {"MOTO": 2035, "TW3": 2035, "BUS": 2038, "MAT": 2038, "MINI": 2038,
             "CAR": 2040, "LCV": 2040, "MDT": 2045, "HDT": 2045}


def charging(regime):
    def f(m):
        apply_charging_regime(m, regime)
    return f


def open_v2g(m: Model):
    for y in Y(m):
        m.set("TotalAnnualMaxCapacity", (R, "V2G_DEPOT", y), 999)
    update_reserve_udc(m)


def grid_constrained(m: Model):
    lim = {"BUILD_GEO": 0.07, "BUILD_VRE": 0.25, "BUILD_BESS": 0.10, "BUILD_DIST": 0.35, "BUILD_FIRM": 0.15}
    for u, v in lim.items():
        for y in Y(m):       # every year incl. 2024: no pre-building ahead of the limit
            m.set("UDCConstant", (R, u, y), v)
    for y in Y(m):          # no imports beyond the committed 400 MW
        m.set("TotalAnnualMaxCapacity", (R, "IMPELC001", y), 0.4)


def accelerated_supply(m: Model):
    for y in Y(m):
        yi = int(y)
        m.set("TotalAnnualMaxCapacity", (R, "IMPELC001", y), 0.4 if yi < 2030 else (1.0 if yi < 2035 else 1.5))
        m.set("TotalAnnualMinCapacity", (R, "IMPELC001", y), 0.4)
        for t in [t for t in m.techs if t.startswith("PWRGEO")]:
            k = (R, t, y)
            v = m.params.get("TotalAnnualMaxCapacity", {}).get(k)
            if v is not None and v > 0:
                m.set("TotalAnnualMaxCapacity", k, v * 1.3)
        for s, t in [("BESS001", None), (None, "BESS_TECH")]:
            if t:
                m.set("CapitalCost", (R, t, y), m.get("CapitalCost", (R, t, y)) * 0.8)
            else:
                m.set("CapitalCostStorage", (R, s, y), m.get("CapitalCostStorage", (R, s, y)) * 0.8)


def _ramp(y: str, start: int, full: int) -> float:
    yi = int(y)
    return 0.0 if yi <= start else 1.0 if yi >= full else (yi - start) / (full - start)


def shift_demand(src: str, dst: str, share: float, start: int, full: int, dst_factor: float = 1.0):
    def f(m: Model):
        for y in Y(m):
            k = _ramp(y, start, full) * share
            s = m.get("AccumulatedAnnualDemand", (R, src, y))
            d = m.get("AccumulatedAnnualDemand", (R, dst, y))
            m.set("AccumulatedAnnualDemand", (R, src, y), s * (1 - k))
            m.set("AccumulatedAnnualDemand", (R, dst, y), d + s * k * dst_factor)
    return f


def scale_demand(com: str, share: float, start: int, full: int):
    def f(m: Model):
        for y in Y(m):
            k = _ramp(y, start, full) * share
            m.set("AccumulatedAnnualDemand", (R, com, y), m.get("AccumulatedAnnualDemand", (R, com, y)) * (1 - k))
    return f


def fuel_economy_standard(m: Model):
    g_ref = m.info["constants"]["ice_efficiency_gain_reference"]
    g = m.info["constants"]["ice_efficiency_gain_standard"]
    y0 = int(Y(m)[0])
    for t in [t for t in m.techs if m.techs[t].vclass in ("CAR", "LCV") and m.techs[t].drivetrain in ("ICE", "HEV")]:
        for k in [k for k in m.params["InputActivityRatio"] if k[1] == t]:
            yi = int(k[4])
            if yi > 2026:
                m.params["InputActivityRatio"][k] *= ((1 - g) / (1 - g_ref)) ** (yi - 2026)
        for k in [k for k in m.params.get("EmissionActivityRatio", {}) if k[1] == t]:
            yi = int(k[4])
            if yi > 2026:
                m.params["EmissionActivityRatio"][k] *= ((1 - g) / (1 - g_ref)) ** (yi - 2026)


def raise_zev_caps(frac: float):
    def f(m: Model):
        caps = {c: {y: v + frac * (1 - v) * _ramp(y, 2025, 2030) for y, v in d.items()}
                for c, d in m.info["zev_caps"].items()}
        set_zev_caps(m, caps)
    return f


def disable(*techs):
    def f(m: Model):
        for t in techs:
            for y in Y(m):
                m.set("TotalAnnualMaxCapacityInvestment", (R, t, y), 0)
    return f


def hvo_route(m: Model):
    for y in Y(m):
        yi = int(y)
        cap = 0 if yi < 2030 else m.info["constants"]["hvo_supply_cap_2050_PJ"] * min(1, (yi - 2030) / 20)
        m.set("TotalTechnologyAnnualActivityUpperLimit", (R, "SUP_HVO", y), cap)
        m.params.get("TotalAnnualMaxCapacityInvestment", {}).pop((R, "HDT_HVO", y), None)


def carbon_price(points: dict[int, float]):
    def f(m: Model):
        p = _interp(points, Y(m))
        for y in Y(m):
            m.set("EmissionsPenalty", (R, "CO2", y), p[y] if int(y) >= min(points) else 0)
    return f


def green_finance(m: Model):
    new = {"MOTO": 0.15, "TW3": 0.13, "MAT": 0.12, "MINI": 0.12}
    for t in _veh(m, zev=True):
        cls = m.techs[t].vclass
        cur = m.get("DiscountRateIdv", (R, t))
        m.set("DiscountRateIdv", (R, t), new.get(cls, max(0.08, cur - 0.02)))


def scale_zev_capex(f_vehicle: float, f_storage: float):
    def f(m: Model):
        for t in _veh(m, zev=True) + ["CHGT_SWAP"]:
            for y in Y(m):
                if int(y) >= 2026:
                    m.set("CapitalCost", (R, t, y), m.get("CapitalCost", (R, t, y)) * f_vehicle)
        for y in Y(m):
            if int(y) >= 2026:
                m.set("CapitalCost", (R, "BESS_TECH", y), m.get("CapitalCost", (R, "BESS_TECH", y)) * f_storage)
                m.set("CapitalCostStorage", (R, "BESS001", y), m.get("CapitalCostStorage", (R, "BESS001", y)) * f_storage)
    return f


def demand_growth_shift(delta: float):
    """Add delta (e.g. +0.01) to the annual growth of every transport and
    electricity demand from 2025."""
    def f(m: Model):
        y0 = int(Y(m)[0])
        for p, coms in [("AccumulatedAnnualDemand", [c for c in m.comms if c.startswith(("P_", "F_"))]),
                        ("SpecifiedAnnualDemand", ["RESELC", "COMELC", "INDELC"])]:
            for c in coms:
                for y in Y(m):
                    k = (R, c, y)
                    if k in m.params.get(p, {}):
                        m.params[p][k] *= (1 + delta) ** (int(y) - y0)
        update_reserve_udc(m)
        # VRE integration RHS follows demand
        for k in [k for k in m.params.get("UDCConstant", {}) if k[1].startswith("DemVs")]:
            m.params["UDCConstant"][k] = sum(m.get("SpecifiedAnnualDemand", (R, c, k[2]), 0)
                                             for c in ["RESELC", "COMELC", "INDELC"])
    return f


def drought(m: Model):
    """Multi-year drought: hydro capacity factors x0.6 in 2030-2033 and 2040-2043."""
    for k in [k for k in m.params.get("CapacityFactor", {}) if k[1].startswith("PWRHYD")]:
        if 2030 <= int(k[3]) <= 2033 or 2040 <= int(k[3]) <= 2043:
            m.params["CapacityFactor"][k] *= 0.6


def oil_price(f_: float):
    def f(m: Model):
        for t in ["IMP_PET", "IMP_DSL", "IMPHFONAI", "IMPHFOMOM", "IMPLFOELD"]:
            for y in Y(m):
                k = (R, t, "1", y)
                if k in m.params.get("VariableCost", {}) and int(y) >= 2026:
                    m.params["VariableCost"][k] *= f_
    return f


def discount_rate(r: float):
    def f(m: Model):
        m.set("DiscountRate", (R,), r)
    return f


# ---------------------------------------------------------------- catalogue
@dataclass
class Scenario:
    sid: str
    name: str
    description: str
    parent: str | None
    steps: list[Callable] = field(default_factory=list)
    family: str = "core"


SCENARIOS: dict[str, Scenario] = {}


def _add(s: Scenario):
    SCENARIOS[s.sid] = s


_add(Scenario("S0_REF", "Reference (current policies)",
              "LCPDP/PSM v3 electricity demand; EV uptake limited by reference diffusion caps; current taxes and "
              "EPRA time-of-use e-mobility tariff (charging profile 'tou'); no ICE bans.", None, []))
_add(Scenario("S1_NDC", "NDC 3.0 / LT-LEDS aligned",
              "Reference + fuel-economy standard for cars and LCVs (1.5 %/yr), higher ZEV diffusion (+30 % of "
              "headroom by 2030), NCCAP rail target (10 % of heavy-truck tonne-km to rail by 2035).",
              "S0_REF", [fuel_economy_standard, raise_zev_caps(0.3), shift_demand("F_HDT", "F_RAIL", 0.10, 2026, 2035)]))
_add(Scenario("S2_ZE", "Zero-emission road transport 2050 - phased bans (central)",
              "ICE new-registration bans: 2/3-wheelers 2030, large buses 2032, matatus & minibuses 2033, cars & LCVs "
              "2035, medium trucks 2038, heavy trucks 2040; no fossil road vehicle in use from 2050. TOU charging.",
              "S0_REF", [phased_bans(BANS_CENTRAL)]))
_add(Scenario("S2A_ZE_EARLY", "ZE 2050 - early bans", "Bans 3-5 years earlier than S2 (2027-2035).",
              "S0_REF", [phased_bans(BANS_EARLY)]))
_add(Scenario("S2B_ZE_LATE", "ZE 2050 - late bans + scrappage",
              "Bans 2035-2045; remaining fossil vehicles scrapped by 2050.", "S0_REF", [phased_bans(BANS_LATE)]))
_add(Scenario("S3_ZE_UNMANAGED", "ZE 2050 - unmanaged charging",
              "S2 with plug-in-on-arrival charging (evening-heavy home and depot profiles).", "S2_ZE",
              [charging("unmanaged")]))
_add(Scenario("S4_ZE_SMART", "ZE 2050 - smart charging and swapping",
              "S2 with managed charging: home, depot and swap charging may be shifted freely within the day but "
              "is blocked 15:00-21:00; fast charging stays need-driven.", "S2_ZE", [charging("smart")]))
_add(Scenario("S5_ZE_SMART_V2G", "ZE 2050 - smart charging + vehicle-to-grid",
              "S4 + bidirectional depot charging (bounded by parked fleet battery power).", "S4_ZE_SMART", [open_v2g]))
_add(Scenario("S6_ZE_UNMANAGED_GRIDCAP", "ZE 2050 - unmanaged charging on a build-constrained grid",
              "S3 + build limits in every year (2024-2060): geothermal 70 MW/yr, wind+solar 250 MW/yr, batteries 100 MW/yr, "
              "other firm plant (gas, hydro, nuclear, pumped hydro, bio) 150 MW/yr, distribution reinforcement "
              "350 MW/yr, imports held at 400 MW. Stress test for 'crippling the grid'.",
              "S3_ZE_UNMANAGED", [grid_constrained]))
_add(Scenario("S6B_ZE_SMART_GRIDCAP", "ZE 2050 - smart charging on a build-constrained grid",
              "S4 with the S6 build limits.", "S4_ZE_SMART", [grid_constrained]))
_add(Scenario("S7_ZE_SMART_ACCEL", "ZE 2050 - smart charging + accelerated clean supply",
              "S4 + Ethiopia/EAPP imports to 1.0 GW (2030) and 1.5 GW (2035), geothermal resource limits +30 %, "
              "battery costs -20 %.", "S4_ZE_SMART", [accelerated_supply]))
_add(Scenario("S8_ZE_ASI", "ZE 2050 - Avoid-Shift-Improve",
              "S2 + 20 % of car passenger-km shifted to buses/BRT, 15 % of heavy-truck tonne-km to rail, and 10 % "
              "logistics efficiency (empty running) on heavy trucks, all phased in 2026-2040.",
              "S2_ZE", [shift_demand("P_CAR", "P_BUS", 0.20, 2026, 2040), shift_demand("F_HDT", "F_RAIL", 0.15, 2026, 2040),
                        scale_demand("F_HDT", 0.10, 2026, 2040)]))
_add(Scenario("S9A_FREIGHT_BEV", "ZE 2050 - battery-electric freight only", "S2 with fuel-cell buses and trucks disabled.",
              "S2_ZE", [disable("HDT_FCEV", "BUS_FCEV")]))
_add(Scenario("S9B_FREIGHT_H2", "ZE 2050 - hydrogen heavy freight", "S2 with battery-electric heavy trucks disabled.",
              "S2_ZE", [disable("HDT_BEV")]))
_add(Scenario("S9C_FREIGHT_HVO", "ZE 2050 - renewable-diesel heavy freight",
              "S2 + HVO trucks exempt from the ban; renewable diesel supply up to 25 PJ by 2050.", "S2_ZE", [hvo_route]))
_add(Scenario("S10_MARKET", "Market instruments without bans",
              "Reference + carbon price (US$30/t 2027 -> 100 by 2040 -> 150 by 2050) + green finance for ZEVs "
              "(boda/tuk-tuk WACC 25 -> 15 %, matatu/minibus 18 -> 12 %, others -2 pp) + faster diffusion.",
              "S0_REF", [carbon_price({2027: 30, 2040: 100, 2050: 150, 2060: 150}), green_finance, raise_zev_caps(0.5)]))

# sensitivities on the central ZE pathway
SENSITIVITIES = [
    ("SEN_BATT_LOW", "Low battery / ZEV cost (-20 %)", [scale_zev_capex(0.8, 0.8)]),
    ("SEN_BATT_HIGH", "High battery / ZEV cost (+25 %)", [scale_zev_capex(1.25, 1.25)]),
    ("SEN_DEMAND_HIGH", "High demand growth (+1 pp/yr)", [demand_growth_shift(0.01)]),
    ("SEN_DEMAND_LOW", "Low demand growth (-1 pp/yr)", [demand_growth_shift(-0.01)]),
    ("SEN_DROUGHT", "Multi-year drought (hydro -40 % 2030-33, 2040-43)", [drought]),
    ("SEN_OIL_HIGH", "High oil price (x1.5)", [oil_price(1.5)]),
    ("SEN_OIL_LOW", "Low oil price (x0.7)", [oil_price(0.7)]),
    ("SEN_DR06", "Social discount rate 6 %", [discount_rate(0.06)]),
    ("SEN_DR14", "Social discount rate 14 %", [discount_rate(0.14)]),
]
for sid, name, steps in SENSITIVITIES:
    _add(Scenario(sid, name, f"Sensitivity on S2_ZE: {name}.", "S2_ZE", steps, family="sensitivity"))
# the same sensitivities on the reference, so that ZE-vs-reference cost
# differences can be compared under identical assumptions
for sid, name, steps in SENSITIVITIES:
    _add(Scenario("REF" + sid[3:], f"Reference - {name}", f"Sensitivity on S0_REF: {name}.", "S0_REF", steps,
                  family="sensitivity_ref"))


def lineage(sid: str) -> list[str]:
    out = []
    while sid:
        out.insert(0, sid)
        sid = SCENARIOS[sid].parent
    return out


def build_scenario(base: Model, sid: str) -> Model:
    m = base.copy()
    for s in lineage(sid):
        for step in SCENARIOS[s].steps:
            step(m)
    m.finalise_sets()
    m.info["scenario"] = sid
    return m
