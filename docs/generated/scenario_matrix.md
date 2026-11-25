# Scenario matrix
_Auto-generated from `src/kezer/scenarios.py`._

| ID | Name | Family | Builds on | MUIO case run layers | Definition |
|---|---|---|---|---|---|
| S0_REF | Reference (current policies) | core | - | SC_0 | LCPDP/PSM v3 electricity demand; EV uptake limited by reference diffusion caps; current taxes and EPRA time-of-use e-mobility tariff (charging profile 'tou'); no ICE bans. |
| S1_NDC | NDC 3.0 / LT-LEDS aligned | core | S0_REF | SC_0 -> S1_NDC | Reference + fuel-economy standard for cars and LCVs (1.5 %/yr), higher ZEV diffusion (+30 % of headroom by 2030), NCCAP rail target (10 % of heavy-truck tonne-km to rail by 2035). |
| S2_ZE | Zero-emission road transport 2050 - phased bans (central) | core | S0_REF | SC_0 -> S2_ZE | ICE new-registration bans: 2/3-wheelers 2030, large buses 2032, matatus & minibuses 2033, cars & LCVs 2035, medium trucks 2038, heavy trucks 2040; no fossil road vehicle in use from 2050. TOU charging. |
| S2A_ZE_EARLY | ZE 2050 - early bans | core | S0_REF | SC_0 -> S2A_ZE_EARLY | Bans 3-5 years earlier than S2 (2027-2035). |
| S2B_ZE_LATE | ZE 2050 - late bans + scrappage | core | S0_REF | SC_0 -> S2B_ZE_LATE | Bans 2035-2045; remaining fossil vehicles scrapped by 2050. |
| S3_ZE_UNMANAGED | ZE 2050 - unmanaged charging | core | S2_ZE | SC_0 -> S2_ZE -> S3_ZE_UNMANAGED | S2 with plug-in-on-arrival charging (evening-heavy home and depot profiles). |
| S4_ZE_SMART | ZE 2050 - smart charging and swapping | core | S2_ZE | SC_0 -> S2_ZE -> S4_ZE_SMART | S2 with managed charging: home, depot and swap charging may be shifted freely within the day but is blocked 15:00-21:00; fast charging stays need-driven. |
| S5_ZE_SMART_V2G | ZE 2050 - smart charging + vehicle-to-grid | core | S4_ZE_SMART | SC_0 -> S2_ZE -> S4_ZE_SMART -> S5_ZE_SMART_V2G | S4 + bidirectional depot charging (bounded by parked fleet battery power). |
| S6_ZE_UNMANAGED_GRIDCAP | ZE 2050 - unmanaged charging on a build-constrained grid | core | S3_ZE_UNMANAGED | SC_0 -> S2_ZE -> S3_ZE_UNMANAGED -> S6_ZE_UNMANAGED_GRIDCAP | S3 + build limits in every year (2024-2060): geothermal 70 MW/yr, wind+solar 250 MW/yr, batteries 100 MW/yr, other firm plant (gas, hydro, nuclear, pumped hydro, bio) 150 MW/yr, distribution reinforcement 350 MW/yr, imports held at 400 MW. Stress test for 'crippling the grid'. |
| S6B_ZE_SMART_GRIDCAP | ZE 2050 - smart charging on a build-constrained grid | core | S4_ZE_SMART | SC_0 -> S2_ZE -> S4_ZE_SMART -> S6B_ZE_SMART_GRIDCAP | S4 with the S6 build limits. |
| S7_ZE_SMART_ACCEL | ZE 2050 - smart charging + accelerated clean supply | core | S4_ZE_SMART | SC_0 -> S2_ZE -> S4_ZE_SMART -> S7_ZE_SMART_ACCEL | S4 + Ethiopia/EAPP imports to 1.0 GW (2030) and 1.5 GW (2035), geothermal resource limits +30 %, battery costs -20 %. |
| S8_ZE_ASI | ZE 2050 - Avoid-Shift-Improve | core | S2_ZE | SC_0 -> S2_ZE -> S8_ZE_ASI | S2 + 20 % of car passenger-km shifted to buses/BRT, 15 % of heavy-truck tonne-km to rail, and 10 % logistics efficiency (empty running) on heavy trucks, all phased in 2026-2040. |
| S9A_FREIGHT_BEV | ZE 2050 - battery-electric freight only | core | S2_ZE | SC_0 -> S2_ZE -> S9A_FREIGHT_BEV | S2 with fuel-cell buses and trucks disabled. |
| S9B_FREIGHT_H2 | ZE 2050 - hydrogen heavy freight | core | S2_ZE | SC_0 -> S2_ZE -> S9B_FREIGHT_H2 | S2 with battery-electric heavy trucks disabled. |
| S9C_FREIGHT_HVO | ZE 2050 - renewable-diesel heavy freight | core | S2_ZE | SC_0 -> S2_ZE -> S9C_FREIGHT_HVO | S2 + HVO trucks exempt from the ban; renewable diesel supply up to 25 PJ by 2050. |
| S10_MARKET | Market instruments without bans | core | S0_REF | SC_0 -> S10_MARKET | Reference + carbon price (US$30/t 2027 -> 100 by 2040 -> 150 by 2050) + green finance for ZEVs (boda/tuk-tuk WACC 25 -> 15 %, matatu/minibus 18 -> 12 %, others -2 pp) + faster diffusion. |
| SEN_BATT_LOW | Low battery / ZEV cost (-20 %) | sensitivity | S2_ZE | SC_0 -> S2_ZE -> SEN_BATT_LOW | Sensitivity on S2_ZE: Low battery / ZEV cost (-20 %). |
| SEN_BATT_HIGH | High battery / ZEV cost (+25 %) | sensitivity | S2_ZE | SC_0 -> S2_ZE -> SEN_BATT_HIGH | Sensitivity on S2_ZE: High battery / ZEV cost (+25 %). |
| SEN_DEMAND_HIGH | High demand growth (+1 pp/yr) | sensitivity | S2_ZE | SC_0 -> S2_ZE -> SEN_DEMAND_HIGH | Sensitivity on S2_ZE: High demand growth (+1 pp/yr). |
| SEN_DEMAND_LOW | Low demand growth (-1 pp/yr) | sensitivity | S2_ZE | SC_0 -> S2_ZE -> SEN_DEMAND_LOW | Sensitivity on S2_ZE: Low demand growth (-1 pp/yr). |
| SEN_DROUGHT | Multi-year drought (hydro -40 % 2030-33, 2040-43) | sensitivity | S2_ZE | SC_0 -> S2_ZE -> SEN_DROUGHT | Sensitivity on S2_ZE: Multi-year drought (hydro -40 % 2030-33, 2040-43). |
| SEN_OIL_HIGH | High oil price (x1.5) | sensitivity | S2_ZE | SC_0 -> S2_ZE -> SEN_OIL_HIGH | Sensitivity on S2_ZE: High oil price (x1.5). |
| SEN_OIL_LOW | Low oil price (x0.7) | sensitivity | S2_ZE | SC_0 -> S2_ZE -> SEN_OIL_LOW | Sensitivity on S2_ZE: Low oil price (x0.7). |
| SEN_DR06 | Social discount rate 6 % | sensitivity | S2_ZE | SC_0 -> S2_ZE -> SEN_DR06 | Sensitivity on S2_ZE: Social discount rate 6 %. |
| SEN_DR14 | Social discount rate 14 % | sensitivity | S2_ZE | SC_0 -> S2_ZE -> SEN_DR14 | Sensitivity on S2_ZE: Social discount rate 14 %. |
| REF_BATT_LOW | Reference - Low battery / ZEV cost (-20 %) | sensitivity_ref | S0_REF | SC_0 -> REF_BATT_LOW | Sensitivity on S0_REF: Low battery / ZEV cost (-20 %). |
| REF_BATT_HIGH | Reference - High battery / ZEV cost (+25 %) | sensitivity_ref | S0_REF | SC_0 -> REF_BATT_HIGH | Sensitivity on S0_REF: High battery / ZEV cost (+25 %). |
| REF_DEMAND_HIGH | Reference - High demand growth (+1 pp/yr) | sensitivity_ref | S0_REF | SC_0 -> REF_DEMAND_HIGH | Sensitivity on S0_REF: High demand growth (+1 pp/yr). |
| REF_DEMAND_LOW | Reference - Low demand growth (-1 pp/yr) | sensitivity_ref | S0_REF | SC_0 -> REF_DEMAND_LOW | Sensitivity on S0_REF: Low demand growth (-1 pp/yr). |
| REF_DROUGHT | Reference - Multi-year drought (hydro -40 % 2030-33, 2040-43) | sensitivity_ref | S0_REF | SC_0 -> REF_DROUGHT | Sensitivity on S0_REF: Multi-year drought (hydro -40 % 2030-33, 2040-43). |
| REF_OIL_HIGH | Reference - High oil price (x1.5) | sensitivity_ref | S0_REF | SC_0 -> REF_OIL_HIGH | Sensitivity on S0_REF: High oil price (x1.5). |
| REF_OIL_LOW | Reference - Low oil price (x0.7) | sensitivity_ref | S0_REF | SC_0 -> REF_OIL_LOW | Sensitivity on S0_REF: Low oil price (x0.7). |
| REF_DR06 | Reference - Social discount rate 6 % | sensitivity_ref | S0_REF | SC_0 -> REF_DR06 | Sensitivity on S0_REF: Social discount rate 6 %. |
| REF_DR14 | Reference - Social discount rate 14 % | sensitivity_ref | S0_REF | SC_0 -> REF_DR14 | Sensitivity on S0_REF: Social discount rate 14 %. |
