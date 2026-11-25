# 4. Limitations, data gaps and conflicts log

This page records what the model cannot tell you and where its inputs are weakest. Reviewers should read it before the results. Confidence ratings (A/B/C) for every input are in `docs/generated/assumption_tables.md`.

## 4.1 Structural limitations

| Limitation | Effect on results | Mitigation / next step |
|---|---|---|
| **Representative days.** 48 timeslices, i.e. 4 seasons × 2 day types × 6 brackets. Within-bracket peaks are averaged. | The 2-hour 19–21 h bracket understates the instantaneous peak by a few per cent. Multi-day low-wind or low-hydro events are not represented. | 25 % reserve margin on the bracket peak. Hourly dispatch check of chosen capacities (as Kihara et al. 2024 did with FlexTool) is the recommended follow-up. |
| **Seasonal balance of charging commodities.** This is how smart charging is represented. | Smart charging can move any amount of energy within the day, limited only by charger kW and the peak block. Real fleets have duty cycles. | Charger capacity is costed, so flexibility is not free. Fast charging is never flexible. The bounds are made explicit in the profiles file. |
| **No vintage tracking.** Fuel economy applies to the whole stock of a technology in a year. | Fleet-average efficiency responds faster than real turnover would allow. | Gains are small: 0.5–1.5 %/yr. |
| **Single node.** | Nairobi feeder and transformer constraints (Lukuyu et al. 2024) are represented only through the national distribution-reinforcement technology (PWRDIST) and the `BUILD_DIST` limit. | Local distribution studies are needed before siting decisions. |
| **Modal shift is exogenous.** | Shift scenarios (S1, S8) are what-ifs, not predictions. | |
| **Hydrogen balanced annually.** | Free seasonal H2 storage flatters fuel-cell pathways. | Treat S9b as an upper bound for hydrogen. |
| **Economic, not consumer, perspective.** Taxes are excluded from costs. | Adoption is driven by system cost within diffusion limits, not by pump prices. Real buyers face taxes and subsidies. | Fiscal effects are reported separately. The diffusion caps represent non-cost barriers. |
| **No macro feedback.** | Fuel-tax loss, jobs and GDP effects are not fed back into demand. | MUIOGO / OG-Core soft-link is a natural extension. |

## 4.2 Data gaps (proxies used)

* **Active fleet.** NTSA's register is cumulative and is never purged. Active stocks are modeller estimates calibrated to KNBS 2024 road fuel. The calibration fixes total fuel, not the split between classes. Matatu, minibus, bus and truck numbers are confidence C.
* **Kenyan costs for e-buses, e-trucks and e-cars.** Essentially absent. Costs combine IEA, ICCT and BNEF international trajectories with Kenyan duty-free or CKD assumptions. **Heavy-freight results are exploratory.**
* **Charging behaviour.** There is no published Kenyan telemetry. Profiles are modeller assumptions informed by Lukuyu et al. (2024), the WEVJ (2025) Nairobi boda study and operator descriptions. Request swap-station data from EMAK, Spiro and Roam, and depot data from BasiGo.
* **Hourly load.** The timeslice demand profile is inherited from CCG PSM v3. Request hourly KPLC load for 2019–2025.
* **Fuel taxes.** Approximate per-litre totals from press summaries of EPRA price build-ups (KES 70–80/L). They are used only for the fiscal indicator.

## 4.3 Conflicts log

| Item | Values found | Choice and reason |
|---|---|---|
| EV stock 2025 | 6,442 (EPRA, June 2025); 24,754 (The Star / Ministry); 35,661 (NTSA indicative); 39,324 (Ministry, cumulative); 43,324 (EMAK cumulative) | 2024 active base of ~22,000, about 90 % two-wheelers. Registered stock overstates active fleet. |
| New registrations 2024 | 166,514 (Economic Survey 2025) vs 267,193 (Economic Survey 2026, revised) | Not used directly; the stock is calibrated to fuel. Both figures recorded. |
| E-motorcycle share of new motorcycles 2025 | 15.3 % (EMAK: 25,277 / 168,286) vs ~10 % (KNBS denominator of 241,763) | Reference diffusion cap 15 % in 2025 (upper value), since a cap is a ceiling, not a forecast. |
| Fuel economy, cars and matatus | GIZ 2018 survey: 6.1 L/100 km (car), 10.3 (matatu). Mbandi 2019, Nairobi on-road: 22.8 L/100 km (car), 33.1 (matatu). | Mid values (8.5 and 13 L/100 km), then calibrated to fuel totals. |
| Diesel road share | No official split. EPRA PDP: road is 84 % of all petroleum demand. | 0.84 applied to diesel, 0.97 to petrol. |
| Firm capacity vs peak | KPLC Dec 2025: firm ~2,495 MW; peak 2,514 MW (June 2026) | The model starts from PSM v3 capacities and reports its own reserve margin. |
| PSM v3 timeslice bracket hours | Not documented in the repository | Inferred from YearSplit and solar CFs: 00–06, 06–09, 09–15, 15–19, 19–21, 21–24 h. To be confirmed with the CCG authors. |

## 4.4 Claims the model does not support

* It does not predict EV sales. Diffusion caps are scenario assumptions.
* It does not assess local air quality, health co-benefits or employment quantitatively.
* It does not price distribution upgrades at feeder level.
