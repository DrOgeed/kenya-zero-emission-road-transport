# 6. Results

All numbers come from `results/scenarios/<ID>/*.csv`. The cross-scenario table is `docs/generated/results_tables.md` (also `results/headline_indicators.csv`). Costs are in US$ 2024. "Total cost" means total discounted system cost for 2024–2060 at 10 %, covering vehicles, fuels, charging, generation, storage and grids. Fuel taxes are excluded from cost because they are transfers.

## 6.1 Base-year calibration (2024)

| Indicator | Model | Observed | Source |
|---|---|---|---|
| Road petrol + diesel | 62.5 + 79.8 PJ (calibrated) | KNBS road shares of 1,492.6 kt petrol and 2,208.4 kt diesel | KNBS Economic Survey 2025 |
| Road transport CO2 | 10.25 Mt | 12.09 MtCO2e (2019, road, all GHG); 10.8 Mt (2023, all transport) | GoK via GIZ; EDGAR |
| Electricity generation | 15.5 TWh | 14.5 TWh (FY2024/25) | EPRA |
| System peak | 2.30 GW | 2.32 GW (FY2024/25) | EPRA |
| Firm capacity | 2.49 GW | ~2.50 GW (Dec 2025) | KPLC via Business Daily |

## 6.2 Key findings

**1. Zero-emission road transport by 2050 is feasible and lowers total system cost.**

| | Reference (S0) | Phased bans (S2) |
|---|---|---|
| Total system cost | US$158.6 bn | US$151.5 bn (−4.5 %) |
| Cumulative road CO2, 2024–2050 | 338 Mt | 189 Mt (−44 %) |
| Road fuel import bill, 2024–2050 (undiscounted) | US$120 bn | US$66 bn |

The saving arises because battery-electric vehicles have lower lifetime cost than fossil ones in most classes from the 2030s. Under S0, adoption is held back by the diffusion limits, which represent finance, supply and charging-access barriers. **The saving is only real if policy also removes those barriers.** A ban on its own does not create finance for a boda rider.

**2. Electrification adds a large new load.** EV charging reaches 31.5 TWh in 2050, equal to 57 % of all other electricity demand (55.5 TWh). Total final electricity demand is about 26 % above the reference, where EVs already use 13.6 TWh. Generation is 98 TWh in S2/S4 vs 79 TWh in S0.

**3. Whether the grid copes depends on *when* vehicles charge, more than on how many there are.**

| 2050 | Unmanaged (S3) | TOU (S2) | Smart (S4) | Reference (S0) |
|---|---|---|---|---|
| System peak (GW) | 17.6 | 12.3 | 11.5 | 10.4 |
| EV load at peak (GW) | 9.5 | 6.3 | 6.2 | 1.2 |
| Stationary batteries (GW) | 16.1 | 8.3 | 7.2 | 8.6 |
| T&D investment 2025–50 (bn US$) | 42.1 | 27.5 | 25.2 | 22.1 |
| Total cost (bn US$) | 157.4 | 151.5 | 150.2 | 158.6 |

* **Value of smart charging.** Smart charging is worth about US$7.2 bn against unmanaged charging. It avoids about 6 GW of peak demand and 17 bn US$ of grid investment.
* **Unmanaged charging also changes the freight technology choice.** Heavy freight shifts partly to hydrogen (9.4 TWh of electrolysis in 2050), because annually balanced electrolysers can avoid the evening peak.

**4. Smart charging moves the peak to the night, which turns today's tariff logic around.**

* **Peak timing.** In S2 and S4 the system peak moves from late afternoon (15–21 h) to 21–24 h by 2040–2050, when managed fleets plug in.
* **Marginal cost inverts.** From the 2040s the marginal cost of electricity at night (≈13–14 US¢/kWh) exceeds the evening cost (≈5–6 US¢/kWh).
* **Implication for EPRA.** The KES 8 off-peak e-mobility rate is right for today's geothermal-surplus nights. It will need dynamic or rotating windows once EVs dominate night load, otherwise it will create a "timer peak".
* **Reserve reporting.** The 25 % reserve criterion is enforced at the evening peak slices. Night-time margins are reported ex post: 1.17 in S4 in 2050.

**5. "Crippling the grid" is a build-rate risk, not an EV risk.** In S6, unmanaged charging on a grid limited to historical build rates:

* the reserve margin falls below 1.0 around 2040 (0.87) and reaches 0.40 by 2050;
* firm shortfall reaches 22 GW;
* 42 TWh of demand goes unserved over 2024–2050.

With the same build limits, smart charging (S6B) keeps the margin at or above 1.05 until 2040 and delays shortages by about a decade. By 2050, though, the margin is 0.65, with 32 TWh unserved. **Demand management buys time; it cannot replace building.**

The central smart pathway (S4) needs total capacity to grow from 3.2 GW (2024) to 25.8 GW (2050), about 0.9 GW a year, roughly 4–5 times Kenya's historical rate. By 2050 that is:

* geothermal 4.7 GW;
* wind 8.9 GW;
* solar 2.2 GW;
* batteries 7.2 GW.

**6. Ban timing.**

| Ban timing | Total cost (bn US$) | Cumulative road CO2 (Mt) | Idle fossil vehicles in 2050 |
|---|---|---|---|
| Early, 2027–35 (S2A) | 150.7 | 166 | — |
| Central (S2) | 151.5 | 189 | — |
| Late, 2035–45 (S2B) | 153.3 | 216 | 79,000 (stranded) |

Earlier bans are cheaper and cleaner. Late bans push stranded vehicles onto owners, many of them small operators. Under perfect foresight the optimiser delays car and truck electrification until shortly before each ban (see `results/figures/fig06_zev_fleet_share.png`). Real markets need a longer runway than that.

**7. Instruments without bans do not reach zero.** S10 combines a carbon price rising to US$150/t, green finance and faster diffusion. It reaches 84 % zero-emission vehicles in use and 5.4 Mt CO2 in 2050, with 223 Mt cumulative. NDC-aligned measures (S1) reach 7.3 Mt in 2050. Reaching zero needs registration bans or an equivalent mandate.

**8. Avoid–Shift–Improve is the cheapest pathway.** Moving car trips to buses/BRT and truck freight to rail, plus logistics efficiency (S8), costs US$143.1 bn. That is US$8.4 bn less than S2, and it lowers the 2050 EV load by 3 TWh.

**9. Heavy freight.**

* Battery-electric trucks are the least-cost zero-emission option at the assumed costs. When fuel-cell trucks are allowed (S2), the model does not choose them.
* Forcing hydrogen (S9B) adds US$1.4 bn and 22.6 TWh of electrolysis by 2050.
* Renewable diesel at US$36–45/GJ is not chosen (S9C).

Kenyan cost data for heavy freight barely exist, so treat these results as exploratory.

**10. Vehicle-to-grid** (S5) saves a further US$0.9 bn. Parked depot fleets provide 7.7 GW of discharge capacity and displace 5 GW of stationary batteries.

**11. Fiscal exposure.** Fuel taxes and levies of about US$2.3 bn a year in 2024 (≈KES 70–80/L) fall almost to zero by 2050 in every zero-emission scenario. In the reference they would be about US$2.7 bn a year. Kenya needs a replacement road-funding instrument, for example distance- or weight-based charges or an e-mobility levy, phased in from the 2030s.

## 6.3 Robustness (sensitivities on S2)

Zero emissions in 2050 are reached in every sensitivity.

| Sensitivity | Total cost (bn US$) | Cum. road CO2 2024–50 (Mt) | Note |
|---|---|---|---|
| Central S2 | 151.5 | 189 | |
| Battery/ZEV cost −20 % / +25 % | 142.1 / 161.1 | 158 / 220 | Faster or slower uptake before the bans |
| Demand growth ±1 pp/yr | 131.4 / 175.9 | 173 / 206 | 2050 peak 9.5 / 16.0 GW |
| Oil price ×0.7 / ×1.5 | 143.9 / 162.7 | 208 / 157 | |
| Multi-year drought | 151.8 | 189 | +US$0.3 bn; no unserved energy. The geothermal-heavy mix is drought-robust. |
| Discount rate 6 % / 14 % | 266.1 / 98.4 | 186 / 190 | Totals not comparable across rates |

The sensitivities were run on S2 only. Cost differences against a reference under the *same* sensitivity are a natural next step: `python scripts/run_scenarios.py` with sensitivity layers on S0.

## 6.4 Figures

| | |
|---|---|
| ![](../results/figures/fig01_road_co2.png) | ![](../results/figures/fig06_zev_fleet_share.png) |
| ![](../results/figures/fig02_electricity_demand.png) | ![](../results/figures/fig03_peak_demand.png) |
| ![](../results/figures/fig04_adequacy_stress.png) | ![](../results/figures/fig05_generation_mix.png) |
| ![](../results/figures/fig07_cost_vs_reference.png) | ![](../results/figures/fig08_fuel_bill_tax.png) |
