#!/usr/bin/env python3
"""Figures for the scenario report and README (PNG, 200 dpi) from
results/scenarios/<SID>/*.csv. Palette: validated categorical order
(blue, orange, aqua, yellow, magenta, green, violet, red)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "scenarios"
FIG = ROOT / "results" / "figures"
PAL = ["#257de0", "#f47230", "#00b894", "#f2a600", "#ee7fac", "#008a17", "#6a4ce2", "#ec4647"]
GREY = "#8a8a8a"
TEXT = "#191919"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": "#c8c8c8", "axes.labelcolor": TEXT,
    "xtick.color": "#666666", "ytick.color": "#666666", "axes.grid": True, "grid.color": "#ececec",
    "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
    "axes.titlesize": 11, "legend.frameon": False, "lines.linewidth": 2, "figure.dpi": 100,
})
LABEL = {
    "S0_REF": "S0 Reference", "S1_NDC": "S1 NDC-aligned", "S2_ZE": "S2 ZE-2050 (TOU)",
    "S2A_ZE_EARLY": "S2a early bans", "S2B_ZE_LATE": "S2b late bans", "S3_ZE_UNMANAGED": "S3 unmanaged charging",
    "S4_ZE_SMART": "S4 smart charging", "S5_ZE_SMART_V2G": "S5 smart + V2G",
    "S6_ZE_UNMANAGED_GRIDCAP": "S6 unmanaged + grid cap", "S6B_ZE_SMART_GRIDCAP": "S6b smart + grid cap",
    "S7_ZE_SMART_ACCEL": "S7 smart + accelerated supply", "S8_ZE_ASI": "S8 avoid-shift-improve",
    "S9A_FREIGHT_BEV": "S9a BEV freight", "S9B_FREIGHT_H2": "S9b H2 freight", "S9C_FREIGHT_HVO": "S9c HVO freight",
    "S10_MARKET": "S10 market instruments",
}


def load(name: str, sids=None) -> pd.DataFrame:
    frames = []
    for d in sorted(RES.iterdir()):
        f = d / f"{name}.csv"
        if f.exists() and (sids is None or d.name in sids):
            frames.append(pd.read_csv(f))
    return pd.concat(frames) if frames else pd.DataFrame()


def lines(ax, df, x, y, sids, title, ylabel, xmax=2050):
    for i, s in enumerate(sids):
        d = df[(df.scenario == s) & (df[x] <= xmax)].sort_values(x)
        if d.empty:
            continue
        ax.plot(d[x], d[y], color=PAL[i % 8], label=LABEL.get(s, s))
    ax.set_title(title, loc="left")
    ax.set_ylabel(ylabel)
    ax.set_xlim(2024, xmax)


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    core = ["S0_REF", "S1_NDC", "S2_ZE", "S3_ZE_UNMANAGED", "S4_ZE_SMART", "S6_ZE_UNMANAGED_GRIDCAP",
            "S8_ZE_ASI", "S10_MARKET"]

    # 1 road CO2
    em = load("emissions")
    road = em[em.sector == "Road transport"].groupby(["scenario", "YEAR"], as_index=False).MtCO2.sum()
    fig, ax = plt.subplots(figsize=(7.5, 4))
    lines(ax, road, "YEAR", "MtCO2", core, "Road transport CO2 emissions", "Mt CO2 per year")
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    save(fig, "fig01_road_co2")

    # 2 electricity demand (total) and EV share
    ed = load("electricity_demand")
    ed["total_TWh"] = ed.non_transport_TWh + ed.ev_charging_TWh + ed.hydrogen_TWh + ed.rail_TWh
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    sel = ["S0_REF", "S2_ZE", "S4_ZE_SMART", "S8_ZE_ASI", "S9B_FREIGHT_H2", "S10_MARKET"]
    lines(axs[0], ed, "YEAR", "total_TWh", sel, "Final electricity demand incl. transport", "TWh per year")
    lines(axs[1], ed, "YEAR", "ev_charging_TWh", sel, "EV charging electricity (grid side)", "TWh per year")
    axs[0].legend(loc="upper left", fontsize=8)
    save(fig, "fig02_electricity_demand")

    # 3 peak demand and reserve margin (two panels, no dual axis)
    ad = load("adequacy")
    sel = ["S0_REF", "S2_ZE", "S3_ZE_UNMANAGED", "S4_ZE_SMART", "S5_ZE_SMART_V2G", "S6_ZE_UNMANAGED_GRIDCAP",
           "S6B_ZE_SMART_GRIDCAP"]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    lines(axs[0], ad, "YEAR", "peak_GW", sel, "System peak demand (generation level)", "GW")
    lines(axs[1], ad, "YEAR", "ev_at_peak_GW", sel, "EV charging coincident with the system peak", "GW")
    axs[0].legend(loc="upper left", fontsize=8)
    save(fig, "fig03_peak_demand")

    # 4 adequacy failures: unserved energy and firm shortfall
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    lines(axs[0], ad, "YEAR", "unserved_energy_TWh", sel, "Unserved energy", "TWh per year")
    lines(axs[1], ad, "YEAR", "reserve_shortfall_GW", sel, "Firm-capacity shortfall vs reserve requirement", "GW")
    axs[0].legend(loc="upper left", fontsize=8)
    save(fig, "fig04_adequacy_stress")

    # 5 generation mix (stacked bars) for selected scenarios and years
    gen = load("generation")
    order = ["Geothermal", "Hydro", "Wind", "Solar PV", "Imports", "Battery storage", "Pumped hydro", "Other"]
    gen["type2"] = gen.type.where(gen.type.isin(order), "Other")
    sel = ["S0_REF", "S3_ZE_UNMANAGED", "S4_ZE_SMART", "S9B_FREIGHT_H2"]
    years = [2024, 2030, 2040, 2050]
    fig, ax = plt.subplots(figsize=(11, 4.5))
    xt, xl = [], []
    pos = 0
    for s in sel:
        for y in years:
            d = gen[(gen.scenario == s) & (gen.YEAR == y)].groupby("type2").TWh.sum()
            bottom = 0
            for i, t in enumerate(order):
                v = d.get(t, 0)
                ax.bar(pos, v, bottom=bottom, color=PAL[i], width=0.8, edgecolor="white", linewidth=1,
                       label=t if pos == 0 else None)
                bottom += v
            xt.append(pos)
            xl.append(f"{y}")
            pos += 1
        ax.text(pos - 2.5, ax.get_ylim()[1] * 0.98 if pos > 4 else 0, "", ha="center")
        pos += 0.8
    ax.set_xticks(xt, xl, fontsize=8)
    for k, s in enumerate(sel):
        ax.annotate(LABEL[s], xy=(k * 4.8 + 1.5, -0.13), xycoords=("data", "axes fraction"), ha="center", fontsize=8.5)
    ax.set_ylabel("TWh per year")
    ax.set_title("Electricity generation mix", loc="left")
    ax.legend(ncol=1, fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    save(fig, "fig05_generation_mix")

    # 6 ZEV share of fleet by class, S2
    fl = load("fleet", ["S2_ZE", "S0_REF"])
    fig, axs = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    classes = ["MOTO", "TW3", "CAR", "LCV", "MAT", "MINI", "BUS", "MDT"]
    for ax, s in zip(axs, ["S0_REF", "S2_ZE"]):
        d = fl[fl.scenario == s]
        for i, c in enumerate(classes):
            g = d[d.vclass == c].groupby(["YEAR", "zev"]).in_use.sum().unstack(fill_value=0)
            if g.empty:
                continue
            share = 100 * g.get(True, 0) / g.sum(axis=1)
            share = share[share.index <= 2050]
            ax.plot(share.index, share.values, color=PAL[i], label=c)
        d = fl[(fl.scenario == s) & (fl.vclass == "HDT")].groupby(["YEAR", "zev"]).in_use.sum().unstack(fill_value=0)
        sh = 100 * d.get(True, 0) / d.sum(axis=1)
        sh = sh[sh.index <= 2050]
        ax.plot(sh.index, sh.values, color=GREY, linestyle="--", label="HDT")
        ax.set_title(f"Zero-emission share of fleet - {LABEL[s]}", loc="left")
        ax.set_ylabel("% of vehicles in use")
        ax.set_xlim(2024, 2050)
    axs[0].legend(ncol=3, fontsize=8, loc="upper left")
    save(fig, "fig06_zev_fleet_share")

    # 7 cost difference vs reference
    sm = load("summary")
    base = sm.loc[sm.scenario == "S0_REF", "total_discounted_system_cost_MUSD"]
    if len(base):
        sm["delta_bn"] = (sm.total_discounted_system_cost_MUSD - base.iloc[0]) / 1000
        sm = sm[~sm.scenario.str.startswith(("SEN", "REF")) & (sm.scenario != "S0_REF")].sort_values("delta_bn")
        fig, ax = plt.subplots(figsize=(7.5, 5))
        ax.barh([LABEL.get(s, s) for s in sm.scenario], sm.delta_bn,
                color=[PAL[0] if v >= 0 else PAL[2] for v in sm.delta_bn], height=0.6)
        ax.axvline(0, color=GREY, linewidth=1)
        ax.set_xlabel("Change in total discounted system cost vs S0, 2024-2060 (billion US$ 2024, 10 % discount)")
        ax.set_title("Cost of the pathways relative to the reference", loc="left")
        ax.grid(axis="y", visible=False)
        save(fig, "fig07_cost_vs_reference")

    # 8 fuel import bill and fuel tax revenue
    fu = load("fuels")
    agg = fu.groupby(["scenario", "YEAR"], as_index=False)[["import_bill_MUSD", "fuel_tax_MUSD"]].sum()
    agg[["import_bill_MUSD", "fuel_tax_MUSD"]] /= 1000
    sel = ["S0_REF", "S1_NDC", "S2_ZE", "S2B_ZE_LATE", "S8_ZE_ASI", "S10_MARKET"]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    lines(axs[0], agg, "YEAR", "import_bill_MUSD", sel, "Road and rail fuel import bill", "billion US$ per year")
    lines(axs[1], agg, "YEAR", "fuel_tax_MUSD", sel, "Fuel tax and levy revenue at risk", "billion US$ per year")
    axs[0].legend(fontsize=8, loc="upper left")
    save(fig, "fig08_fuel_bill_tax")
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
