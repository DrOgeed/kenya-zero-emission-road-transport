"""Container for an OSeMOSYS (MUIO v5.7) model instance.

Parameters are held as dicts keyed by index tuples so that scenario deltas can
be applied cheaply; they are converted to tidy DataFrames only for writing.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

import pandas as pd

from .gmpl_io import PARAM_INDEX, default_of


@dataclass
class TechMeta:
    name: str
    description: str
    group: str            # power | grid | storage | fuel | vehicle | rail | charging | hydrogen | slack | demand
    cap_unit: str
    act_unit: str
    sector: str = ""
    vclass: str = ""      # vehicle / rail class
    drivetrain: str = ""
    zev: bool = False


@dataclass
class CommMeta:
    name: str
    description: str
    unit: str
    balance: str          # Ts | Se | An  (MUIO balance-level codes)


@dataclass
class UDCMeta:
    name: str
    description: str
    tag: int              # 0 = '<=', 1 = '='


@dataclass
class Model:
    sets: dict[str, list] = field(default_factory=dict)
    params: dict[str, dict[tuple, float]] = field(default_factory=dict)
    techs: dict[str, TechMeta] = field(default_factory=dict)
    comms: dict[str, CommMeta] = field(default_factory=dict)
    udcs: dict[str, UDCMeta] = field(default_factory=dict)
    storage_meta: dict[str, dict] = field(default_factory=dict)
    info: dict = field(default_factory=dict)

    # ------------------------------------------------------------------
    def set(self, param: str, key: tuple, value: float) -> None:
        assert param in PARAM_INDEX, param
        assert len(key) == len(PARAM_INDEX[param]), (param, key)
        self.params.setdefault(param, {})[tuple(str(k) for k in key)] = float(value)

    def get(self, param: str, key: tuple, default=None):
        d = self.params.get(param, {})
        k = tuple(str(x) for x in key)
        if k in d:
            return d[k]
        return default_of(param) if default is None else default

    def drop(self, param: str, pred) -> None:
        d = self.params.get(param, {})
        for k in [k for k in d if pred(k)]:
            del d[k]

    def add_tech(self, meta: TechMeta) -> None:
        self.techs[meta.name] = meta

    def add_comm(self, meta: CommMeta) -> None:
        self.comms[meta.name] = meta

    def copy(self) -> "Model":
        return copy.deepcopy(self)

    # ------------------------------------------------------------------
    def finalise_sets(self) -> None:
        self.sets["TECHNOLOGY"] = sorted(self.techs)
        self.sets["COMMODITY"] = sorted(self.comms)
        self.sets["UDC"] = sorted(self.udcs)
        self.sets["COMMODITY_TS"] = sorted(c for c, m in self.comms.items() if m.balance == "Ts")
        self.sets["COMMODITY_S"] = sorted(c for c, m in self.comms.items() if m.balance == "Se")
        self.sets["COMMODITY_AN"] = sorted(c for c, m in self.comms.items() if m.balance == "An")
        for u, meta in self.udcs.items():
            self.set("UDCTag", ("RE1", u), meta.tag)

    def to_frames(self) -> dict[str, pd.DataFrame]:
        out = {}
        for p, d in self.params.items():
            idx = PARAM_INDEX[p]
            if not d:
                continue
            df = pd.DataFrame([(*k, v) for k, v in d.items()], columns=idx + ["VALUE"])
            out[p] = df
        return out

    def validate(self) -> list[str]:
        """Basic referential checks; returns a list of problems."""
        problems = []
        techs, comms = set(self.sets["TECHNOLOGY"]), set(self.sets["COMMODITY"])
        years = set(str(y) for y in self.sets["YEAR"])
        for p, d in self.params.items():
            idx = PARAM_INDEX[p]
            for k in list(d)[:200000]:
                for name, val in zip(idx, k):
                    if name == "TECHNOLOGY" and val not in techs:
                        problems.append(f"{p}: unknown technology {val}")
                    elif name == "COMMODITY" and val not in comms:
                        problems.append(f"{p}: unknown commodity {val}")
                    elif name == "YEAR" and val not in years:
                        problems.append(f"{p}: year {val} outside horizon")
        # every technology needs an activity link or must be a declared slack
        linked = {k[1] for k in self.params.get("InputActivityRatio", {})} | \
                 {k[1] for k in self.params.get("OutputActivityRatio", {})}
        for t, m in self.techs.items():
            if t not in linked and m.group != "slack":
                problems.append(f"technology {t} has no input/output commodity")
        return sorted(set(problems))
