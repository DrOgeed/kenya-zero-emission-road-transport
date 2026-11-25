# 2. Scenario design

The scenarios answer three questions:

1. Can every road vehicle be zero-emission by 2050?
2. What does the grid need for that to work: how charging behaves, how fast supply is built, and what else comes alongside it (modal shift, freight fuels)?
3. How robust are the answers to costs, demand, drought, oil prices and the discount rate?

The full catalogue with exact definitions is `docs/generated/scenario_matrix.md`. Each scenario is a short function in `src/kezer/scenarios.py`, applied as a delta on its parent. This mirrors MUIO's layered scenarios.

## 2.1 Core scenarios

| ID | Purpose | Key settings |
|---|---|---|
| **S0_REF** | Counterfactual under current policies | Reference diffusion caps; EPRA time-of-use tariff behaviour; no bans |
| **S1_NDC** | Policy-aligned without bans | Fuel-economy standard; faster diffusion; 10 % of heavy-truck tonne-km to rail (NCCAP) |
| **S2_ZE** | Core research question | Phased bans on new ICE registrations, including used imports: 2/3W 2030, buses 2032, matatus and minibuses 2033, cars and LCVs 2035, medium trucks 2038, heavy trucks 2040. No fossil road vehicles in use from 2050. TOU charging. |
| S2A / S2B | Timing of the bans | Bans 3–5 years earlier (2027–35) / later (2035–45), with scrappage by 2050 |
| **S3 vs S4** | Does *when* vehicles charge matter? | S3: unmanaged, plug-in-on-arrival charging. S4: smart charging, shifted freely within the day and blocked 15:00–21:00. |
| S5 | Value of fleet flexibility | S4 + vehicle-to-grid from parked depot fleets |
| **S6 / S6B** | The "crippling the grid" stress test | Build limits applied in every year from 2024, so capacity cannot be pre-built before the limits bind: geothermal 70 MW/yr, wind + solar 250 MW/yr, batteries 100 MW/yr, other firm plant (gas, hydro, nuclear, pumped hydro, bioenergy) 150 MW/yr, distribution reinforcement 350 MW/yr, imports held at 400 MW. S6 uses unmanaged charging, S6B smart charging. |
| S7 | Enabling supply | S4 + EAPP imports up to 1.5 GW, geothermal potential +30 %, batteries −20 % |
| S8 | Avoid–Shift–Improve | 20 % of car passenger-km to bus/BRT, 15 % of heavy-truck tonne-km to rail, 10 % logistics efficiency |
| S9A / S9B / S9C | The hard-to-abate heavy-freight tail | Battery-only freight / hydrogen heavy trucks / renewable-diesel (HVO) heavy trucks |
| S10 | Carrots instead of bans | Carbon price US$30 → 150/t; green finance that lowers ZEV WACC (boda 25 → 15 %, matatu 18 → 12 %); faster diffusion |

## 2.2 Sensitivities (paired on S2_ZE and S0_REF)

Each sensitivity is applied twice: to S2_ZE (`SEN_*`) and to S0_REF (`REF_*`). The cost of the zero-emission pathway can then be compared with a reference that shares the same assumption.

| ID | Setting |
|---|---|
| SEN_BATT_LOW / HIGH | ZEV, swap-station and battery capex −20 % / +25 % from 2026 |
| SEN_DEMAND_HIGH / LOW | All transport and electricity demand growth ±1 percentage point per year |
| SEN_DROUGHT | Hydro capacity factors ×0.6 in 2030–33 and 2040–43 |
| SEN_OIL_HIGH / LOW | Oil product prices ×1.5 / ×0.7 from 2026 |
| SEN_DR06 / DR14 | Social discount rate 6 % / 14 % |

## 2.3 Why these scenarios

* **Ban sequencing follows the economics.** Two- and three-wheelers already have lower total cost of ownership electric than petrol (Manufacturing Africa, 2025), so they go first. Heavy trucks have no Kenyan evidence base yet, so they go last.
* **Grid impact is mostly about charging timing.** Kenya's binding power-system constraint is evening peak capacity, not annual energy. Night demand of about 1.4 GW is supplied by geothermal and leaves curtailed energy, while the peak already exceeds firm capacity (KPLC, 2025–26). S3 vs S4, and S6 vs S6B, isolate the charging effect.
* **Livelihood finance is explicit.** The cost of capital for bodas and matatus enters through `DiscountRateIdv`. S10 tests whether cheaper finance alone moves the fleet, a question about the boda and matatu economy as much as about technology.
* **Fiscal exposure is reported.** Fuel taxes and levies fund the Road Maintenance Levy and the Exchequer. Every run reports the revenue that electrification removes (Costa Rica's experience; IDB 2021).
