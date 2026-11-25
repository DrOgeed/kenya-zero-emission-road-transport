"""Fast regression tests (short horizon). Run with: pytest -q"""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kezer.build import build_base, load_constants  # noqa: E402
from kezer.scenarios import SCENARIOS, build_scenario, lineage  # noqa: E402
from kezer.solve import solve, solve_datafile  # noqa: E402


@pytest.fixture(scope="module")
def base():
    return build_base(2024, 2028)


def test_build_validates(base):
    assert base.validate() == []
    assert len(base.sets["TECHNOLOGY"]) > 90


def test_calibration_reproduces_knbs_fuel(base):
    """2024 bottom-up road fuel use equals KNBS road petrol and diesel."""
    const = load_constants()
    veh = base.info["vehicles"]
    pet = dsl = 0.0
    for r in veh.itertuples():
        e = r.stock_2024 * r.annual_km * r.energy_MJ_per_vkm / 1e9
        for part in r.inputs.split(";"):
            c, s = part.split(":")
            if c == "PET":
                pet += e * float(s)
            if c == "DSL":
                dsl += e * float(s)
    cal = base.info["calibration"]
    assert abs(pet - cal["target_petrol_PJ"]) / cal["target_petrol_PJ"] < 1e-6
    assert abs(dsl - cal["target_diesel_PJ"]) / cal["target_diesel_PJ"] < 1e-6
    assert 0.75 < cal["vkt_scale_petrol_group"] < 1.25
    assert 0.75 < cal["vkt_scale_diesel_group"] < 1.25


def test_all_scenarios_build(base):
    for sid in SCENARIOS:
        m = build_scenario(base, sid)
        assert m.validate() == [], sid


@pytest.mark.parametrize("sid", ["S0_REF", "S4_ZE_SMART"])
def test_short_horizon_solves(base, sid, tmp_path):
    r = solve(build_scenario(base, sid), tmp_path, sid, solver="simplex")
    assert r["status"] == "Optimal"


@pytest.mark.skipif(not os.environ.get("MUIO_SRC"), reason="set MUIO_SRC to a MUIO v5.7 checkout")
def test_muio_generator_parity(base, tmp_path):
    """MUIO's own generateDatafile/preprocessData on the exported case gives
    the same LP optimum as the Python writer (scenario layers included)."""
    from kezer.muio_case import CaseWriter, verify_with_muio
    sids = ["S0_REF", "S2_ZE", "S4_ZE_SMART"]
    models = {s: build_scenario(base, s) for s in sids}
    lid = {s: ("SC_0" if s == "S0_REF" else s) for s in sids}
    layers = [(lid[s], s, s, models[s], lid[SCENARIOS[s].parent] if SCENARIOS[s].parent else None) for s in sids]
    runs = [(s, s, [lid[x] for x in lineage(s)]) for s in sids]
    case = CaseWriter(models["S0_REF"]).write(tmp_path / "case", layers, runs)
    for s in ["S0_REF", "S4_ZE_SMART"]:
        dat = verify_with_muio(case, Path(os.environ["MUIO_SRC"]), s, tmp_path / f"v_{s}")
        a = solve_datafile(dat, tmp_path, f"muio_{s}", solver="simplex")
        b = solve_datafile(None, tmp_path, f"py_{s}", model=models[s], solver="simplex")
        assert abs(a["objective"] - b["objective"]) / abs(b["objective"]) < 1e-6
