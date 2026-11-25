# Model sets
_Auto-generated from the model builder._

95 technologies, 37 commodities, 30 user-defined constraints, 48 timeslices, years 2024-2060.

## Technologies

| Technology | Group | Class | Drivetrain | ZEV | Capacity unit | Activity unit | Description |
|---|---|---|---|---|---|---|---|
| BACKSTOP | slack |  |  |  | GW | PJ | Unserved energy (value of lost load) |
| BESS_TECH | storage |  |  |  | GW | PJ | Battery energy storage (power block) |
| BUS_BEV | vehicle | BUS | BEV | yes | kveh | Gpkm | Large bus / BRT - battery electric |
| BUS_DSL | vehicle | BUS | ICE |  | kveh | Gpkm | Large bus / BRT / intercity coach - diesel |
| BUS_FCEV | vehicle | BUS | FCEV | yes | kveh | Gpkm | Large bus - hydrogen fuel cell |
| CAR_BEV | vehicle | CAR | BEV | yes | kveh | Gpkm | Passenger car - battery electric |
| CAR_DSL | vehicle | CAR | ICE |  | kveh | Gpkm | Passenger car / SUV - diesel |
| CAR_HEV | vehicle | CAR | HEV |  | kveh | Gpkm | Passenger car - petrol hybrid |
| CAR_PET | vehicle | CAR | ICE |  | kveh | Gpkm | Passenger car / SUV - petrol |
| CHGT_DEPOT | charging |  |  |  | GW | PJ | Fleet depot charging (buses / matatus / trucks / LCVs) |
| CHGT_FAST | charging |  |  |  | GW | PJ | Public DC fast / corridor megawatt charging |
| CHGT_HOME | charging |  |  |  | GW | PJ | Residential / workplace AC charging (incl. 2W sockets) |
| CHGT_SWAP | charging |  |  |  | GW | PJ | Battery-swap stations incl. swap-battery inventory (~1.6 packs per vehicle) |
| DEMCOMELC | demand |  |  |  | GW | PJ | Commercial electricity end use |
| DEMINDELC | demand |  |  |  | GW | PJ | Industrial electricity end use |
| DEMRESELC | demand |  |  |  | GW | PJ | Residential electricity end use |
| EXPELC | power |  |  |  | GW | PJ | Electricity export |
| H2_ELY | hydrogen |  |  |  | GW(H2) | PJ | Grid-connected PEM/alkaline electrolysis incl. compression storage and dispensing |
| HDT_BEV | vehicle | HDT | BEV | yes | kveh | Gtkm | Heavy truck - battery electric (depot + corridor megawatt charging) |
| HDT_DSL | vehicle | HDT | ICE |  | kveh | Gtkm | Heavy truck / prime mover (>16 t) - diesel |
| HDT_FCEV | vehicle | HDT | FCEV | yes | kveh | Gtkm | Heavy truck - hydrogen fuel cell |
| HDT_HVO | vehicle | HDT | BIO |  | kveh | Gtkm | Heavy truck - diesel engine on hydrotreated vegetable oil (drop-in biofuel) |
| IMPBIO | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: BIO |
| IMPCOA | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: COA |
| IMPELC001 | power |  |  |  | GW | PJ | Electricity import - Ethiopia |
| IMPELC002 | power |  |  |  | GW | PJ | Electricity import - Uganda |
| IMPHFOMOM | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: HFOMOM |
| IMPHFONAI | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: HFONAI |
| IMPLFOELD | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: LFOELD |
| IMPNGS | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: NGS |
| IMPURN | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: URN |
| IMP_DSL | fuel |  |  |  | PJ/yr | PJ | Imported automotive diesel (landed + distribution margin; ex-tax economic cost) |
| IMP_PET | fuel |  |  |  | PJ/yr | PJ | Imported motor gasoline (landed + distribution margin; ex-tax economic cost) |
| LCV_BEV | vehicle | LCV | BEV | yes | kveh | Gtkm | Light commercial vehicle - battery electric |
| LCV_DSL | vehicle | LCV | ICE |  | kveh | Gtkm | Light commercial vehicle (pick-up / van) - diesel |
| LCV_PET | vehicle | LCV | ICE |  | kveh | Gtkm | Light commercial vehicle - petrol |
| MAT_BEV | vehicle | MAT | BEV | yes | kveh | Gpkm | 14-seat matatu - battery electric |
| MAT_DSL | vehicle | MAT | ICE |  | kveh | Gpkm | 14-seat matatu - diesel |
| MDT_BEV | vehicle | MDT | BEV | yes | kveh | Gtkm | Medium truck - battery electric |
| MDT_DSL | vehicle | MDT | ICE |  | kveh | Gtkm | Medium truck (3.5-16 t) - diesel |
| MINBIO | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: BIO |
| MINCOA | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: COA |
| MINGEO | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: GEO |
| MINHYD | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: HYD |
| MINI_BEV | vehicle | MINI | BEV | yes | kveh | Gpkm | 25-33 seat minibus - battery electric (e.g. BasiGo) |
| MINI_DSL | vehicle | MINI | ICE |  | kveh | Gpkm | 25-33 seat minibus - diesel |
| MINSOL | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: SOL |
| MINWND | fuel |  |  |  | PJ/yr | PJ | Primary resource supply: WND |
| MOTO_BEV | vehicle | MOTO | BEV | yes | kveh | Gpkm | Electric motorcycle - plug-in (home/depot charged) |
| MOTO_ICE | vehicle | MOTO | ICE |  | kveh | Gpkm | Motorcycle (boda boda and private) - petrol |
| MOTO_SWP | vehicle | MOTO | BEV | yes | kveh | Gpkm | Electric motorcycle - battery-swap network (battery-as-a-service) |
| PWRBIO001 | power |  |  |  | GW | PJ | Biomass / bagasse |
| PWRCOA001 | power |  |  |  | GW | PJ | Coal plant |
| PWRDIST | grid |  |  |  | GW | PJ | Distribution network |
| PWRGEO001 | power |  |  |  | GW | PJ | Geothermal - resource block 001 |
| PWRGEO002 | power |  |  |  | GW | PJ | Geothermal - resource block 002 |
| PWRGEO003 | power |  |  |  | GW | PJ | Geothermal - resource block 003 |
| PWRGEO004 | power |  |  |  | GW | PJ | Geothermal - resource block 004 |
| PWRGEO005 | power |  |  |  | GW | PJ | Geothermal - resource block 005 |
| PWRGEO006 | power |  |  |  | GW | PJ | Geothermal - resource block 006 |
| PWRGEO007 | power |  |  |  | GW | PJ | Geothermal - resource block 007 |
| PWRHFO001 | power |  |  |  | GW | PJ | Heavy fuel oil plants |
| PWRHYD001 | power |  |  |  | GW | PJ | Hydropower - group 001 |
| PWRHYD002 | power |  |  |  | GW | PJ | Hydropower - group 002 |
| PWRHYD003 | power |  |  |  | GW | PJ | Hydropower - group 003 |
| PWRHYD004 | power |  |  |  | GW | PJ | Hydropower - group 004 |
| PWRHYD005 | power |  |  |  | GW | PJ | Hydropower - group 005 |
| PWRLFO001 | power |  |  |  | GW | PJ | Light fuel oil / diesel plants |
| PWRNGS001 | power |  |  |  | GW | PJ | Natural gas (LNG) CCGT |
| PWRPHS001 | storage |  |  |  | GW | PJ | Pumped hydro storage 1 |
| PWRPHS002 | storage |  |  |  | GW | PJ | Pumped hydro storage 2 |
| PWRSOL001 | power |  |  |  | GW | PJ | Solar PV - supply region 001 |
| PWRSOL002 | power |  |  |  | GW | PJ | Solar PV - supply region 002 |
| PWRTRN | grid |  |  |  | GW | PJ | Transmission network |
| PWRURN001 | power |  |  |  | GW | PJ | Nuclear |
| PWRWND001 | power |  |  |  | GW | PJ | Wind - supply region 001 |
| PWRWND002 | power |  |  |  | GW | PJ | Wind - supply region 002 |
| PWRWND003 | power |  |  |  | GW | PJ | Wind - supply region 003 |
| PWRWND004 | power |  |  |  | GW | PJ | Wind - supply region 004 |
| PWRWND005 | power |  |  |  | GW | PJ | Wind - supply region 005 |
| PWRWND006 | power |  |  |  | GW | PJ | Wind - supply region 006 |
| PWRWND007 | power |  |  |  | GW | PJ | Wind - supply region 007 |
| PWRWND008 | power |  |  |  | GW | PJ | Wind - supply region 008 |
| PWRWND009 | power |  |  |  | GW | PJ | Wind - supply region 009 |
| PWRWND010 | power |  |  |  | GW | PJ | Wind - supply region 010 |
| PWRWND011 | power |  |  |  | GW | PJ | Wind - supply region 011 |
| RAILF_DSL | rail | RAILF | ICE |  | Gtkm/yr | Gtkm | Freight rail (SGR + metre gauge) - diesel locomotives |
| RAILF_ELC | rail | RAILF | ELC | yes | Gtkm/yr | Gtkm | Freight rail - electrified (catenary on SGR) |
| RAILP_DSL | rail | RAILP | ICE |  | Gpkm/yr | Gpkm | Passenger rail (SGR Madaraka Express + Nairobi commuter) - diesel |
| RAILP_ELC | rail | RAILP | ELC | yes | Gpkm/yr | Gpkm | Passenger rail - electrified (SGR + commuter EMUs) |
| RSV_SHORTFALL | slack |  |  |  | GW | - | Firm-capacity shortfall against the reserve-margin requirement (penalised slack) |
| SUP_HVO | fuel |  |  |  | PJ/yr | PJ | Hydrotreated vegetable oil / renewable diesel (import or domestic) |
| TW3_BEV | vehicle | TW3 | BEV | yes | kveh | Gpkm | Three-wheeler - electric |
| TW3_ICE | vehicle | TW3 | ICE |  | kveh | Gpkm | Three-wheeler (tuk-tuk) - petrol |
| V2G_DEPOT | charging |  |  |  | GW | PJ | Vehicle-to-grid discharge from parked depot fleets (bidirectional chargers) |

## Commodities

| Commodity | Balance level | Unit | Description |
|---|---|---|---|
| BIO | annual | PJ | Primary energy / fuel for power: BIO |
| CHG_DEPOT | seasonal (intra-day) | PJ | EV energy delivered via fleet depot charging |
| CHG_FAST | seasonal (intra-day) | PJ | EV energy delivered via public DC fast / corridor charging |
| CHG_HOME | seasonal (intra-day) | PJ | EV energy delivered via home/workplace AC charging |
| CHG_SWAP | seasonal (intra-day) | PJ | EV energy delivered via battery-swap network |
| COA | annual | PJ | Primary energy / fuel for power: COA |
| COADOM | annual | PJ | Primary energy / fuel for power: COADOM |
| COMELC | timeslice | PJ | Commercial electricity demand |
| DSL | annual | PJ | Automotive diesel |
| ELC001 | timeslice | PJ | Electricity - generation busbar |
| ELC002 | timeslice | PJ | Electricity - transmission |
| ELC003 | timeslice | PJ | Electricity - distribution (end-use level) |
| F_HDT | annual | Gtkm | Transport service demand: HDT |
| F_LCV | annual | Gtkm | Transport service demand: LCV |
| F_MDT | annual | Gtkm | Transport service demand: MDT |
| F_RAIL | annual | Gtkm | Transport service demand: RAILF |
| GEO | annual | PJ | Primary energy / fuel for power: GEO |
| H2 | annual | PJ | Hydrogen (delivered, compressed) |
| HFOMOM | annual | PJ | Primary energy / fuel for power: HFOMOM |
| HFONAI | annual | PJ | Primary energy / fuel for power: HFONAI |
| HVO | annual | PJ | Hydrotreated vegetable oil (renewable diesel) |
| HYD | annual | PJ | Primary energy / fuel for power: HYD |
| INDELC | timeslice | PJ | Industrial electricity demand |
| LFOELD | annual | PJ | Primary energy / fuel for power: LFOELD |
| NGS | annual | PJ | Primary energy / fuel for power: NGS |
| PET | annual | PJ | Motor gasoline (petrol) |
| P_BUS | annual | Gpkm | Transport service demand: BUS |
| P_CAR | annual | Gpkm | Transport service demand: CAR |
| P_MAT | annual | Gpkm | Transport service demand: MAT |
| P_MINI | annual | Gpkm | Transport service demand: MINI |
| P_MOTO | annual | Gpkm | Transport service demand: MOTO |
| P_RAIL | annual | Gpkm | Transport service demand: RAILP |
| P_TW3 | annual | Gpkm | Transport service demand: TW3 |
| RESELC | timeslice | PJ | Residential electricity demand |
| SOL | annual | PJ | Primary energy / fuel for power: SOL |
| URN | annual | PJ | Primary energy / fuel for power: URN |
| WND | annual | PJ | Primary energy / fuel for power: WND |

## User-defined constraints

| UDC | Type | Description |
|---|---|---|
| BUILD_BESS | <= | Annual new battery power capacity limit (GW/yr) |
| BUILD_DIST | <= | Annual distribution network reinforcement limit (GW/yr) |
| BUILD_FIRM | <= | Annual new firm thermal / hydro / nuclear / pumped-hydro capacity limit (GW/yr) |
| BUILD_GEO | <= | Annual new geothermal capacity limit (GW/yr) |
| BUILD_VRE | <= | Annual new wind + solar capacity limit (GW/yr) |
| DemVsSol001 | <= | PSM v3 VRE integration limit DemVsSol001: zone capacity x k <= grid demand |
| DemVsWind001 | <= | PSM v3 VRE integration limit DemVsWind001: zone capacity x k <= grid demand |
| DemVsWind002 | <= | PSM v3 VRE integration limit DemVsWind002: zone capacity x k <= grid demand |
| DemVsWind003 | <= | PSM v3 VRE integration limit DemVsWind003: zone capacity x k <= grid demand |
| DemVsWind004 | <= | PSM v3 VRE integration limit DemVsWind004: zone capacity x k <= grid demand |
| DemVsWind005 | <= | PSM v3 VRE integration limit DemVsWind005: zone capacity x k <= grid demand |
| DemVsWind006 | <= | PSM v3 VRE integration limit DemVsWind006: zone capacity x k <= grid demand |
| DemVsWind007 | <= | PSM v3 VRE integration limit DemVsWind007: zone capacity x k <= grid demand |
| DemVsWind008 | <= | PSM v3 VRE integration limit DemVsWind008: zone capacity x k <= grid demand |
| DemVsWind009 | <= | PSM v3 VRE integration limit DemVsWind009: zone capacity x k <= grid demand |
| DemVsWind010 | <= | PSM v3 VRE integration limit DemVsWind010: zone capacity x k <= grid demand |
| GasInfraPrereq | <= | Gas infrastructure prerequisite (PSM v3) |
| HEVCAP_CAR | <= | Maximum hybrid share of new cars (used-import supply limit) |
| RM_PEAK_A | <= | Reserve margin at timeslice TS34: firm capacity >= RM(y) x peak incl. EV charging (RM 1.05 in 2024-26 -> 1.25 from 2030) |
| RM_PEAK_B | <= | Reserve margin at timeslice TS35: firm capacity >= RM(y) x peak incl. EV charging (RM 1.05 in 2024-26 -> 1.25 from 2030) |
| V2G_LIMIT | <= | V2G discharge capacity <= 20% availability x bidirectional kW of BEV depot fleets |
| ZEVCAP_BUS | <= | Maximum zero-emission share of new BUS vehicles (diffusion limit) |
| ZEVCAP_CAR | <= | Maximum zero-emission share of new CAR vehicles (diffusion limit) |
| ZEVCAP_HDT | <= | Maximum zero-emission share of new HDT vehicles (diffusion limit) |
| ZEVCAP_LCV | <= | Maximum zero-emission share of new LCV vehicles (diffusion limit) |
| ZEVCAP_MAT | <= | Maximum zero-emission share of new MAT vehicles (diffusion limit) |
| ZEVCAP_MDT | <= | Maximum zero-emission share of new MDT vehicles (diffusion limit) |
| ZEVCAP_MINI | <= | Maximum zero-emission share of new MINI vehicles (diffusion limit) |
| ZEVCAP_MOTO | <= | Maximum zero-emission share of new MOTO vehicles (diffusion limit) |
| ZEVCAP_TW3 | <= | Maximum zero-emission share of new TW3 vehicles (diffusion limit) |

## 2024 calibration

| target_petrol_PJ | target_diesel_PJ | prior_petrol_PJ | prior_diesel_PJ | vkt_scale_petrol_group | vkt_scale_diesel_group |
|---|---|---|---|---|---|
| 62.5459 | 79.7674 | 65.2671 | 90.4704 | 0.964 | 0.8764 |

## Power capacity carried into 2024 as residual (GW, from PSM v3 committed builds 2019-2023)

| Technology | GW |
|---|---|
| IMPELC001 | 0.2 |
| PWRBIO001 | 0.0014 |
| PWRGEO001 | 0.0833 |
| PWRGEO002 | 0.035 |
| PWRHYD005 | 0.0098 |
| PWRSOL001 | 0.1512 |
| PWRWND011 | 0.1 |

## PSM v3 MaxCapacity values lifted to hold committed builds (tech, year: PSM value -> used)

| Technology | Year | PSM | Used |
|---|---|---|---|
| PWRWND011 | 2041 | 0.08 | 0.152 |

## Transport service demand in 2024 (from calibrated stock x km x occupancy)

| Commodity | 2024 (Gpkm or Gtkm) |
|---|---|
| P_MOTO | 35.17 |
| P_TW3 | 3.24 |
| P_CAR | 20.54 |
| F_LCV | 3.18 |
| P_MAT | 17.55 |
| P_MINI | 23.44 |
| P_BUS | 17.99 |
| F_MDT | 6.14 |
| F_HDT | 27.61 |
| F_RAIL | 3.75 |
| P_RAIL | 1.2 |
