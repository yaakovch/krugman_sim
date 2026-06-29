"""Curated presets for the teaching app."""

from __future__ import annotations

from dataclasses import dataclass

from .model import CrisisParams


@dataclass(frozen=True)
class Scenario:
    label: str
    description: str
    params: CrisisParams


def _consistent(
    domestic_credit0: float,
    reserves0: float,
    credit_growth: float,
    alpha: float,
    foreign_rate: float = 0.0,
    horizon: float = 35.0,
    dt: float = 0.1,
) -> CrisisParams:
    params = CrisisParams(
        domestic_credit0=domestic_credit0,
        reserves0=reserves0,
        credit_growth=credit_growth,
        alpha=alpha,
        peg=domestic_credit0 + reserves0 + alpha * foreign_rate,
        foreign_rate=foreign_rate,
        horizon=horizon,
        dt=dt,
    )
    return params


SCENARIOS: dict[str, Scenario] = {
    "baseline": Scenario(
        label="Baseline",
        description="A clean benchmark where reserves last 25 periods mechanically but the rational attack occurs at 20.",
        params=_consistent(50.0, 50.0, 2.0, 5.0, horizon=35.0),
    ),
    "fast_credit": Scenario(
        label="Fast credit growth",
        description="Faster domestic-credit creation brings both mechanical exhaustion and the attack forward.",
        params=_consistent(50.0, 50.0, 4.0, 5.0, horizon=20.0),
    ),
    "high_alpha": Scenario(
        label="High interest sensitivity",
        description="More interest-sensitive money demand increases the jump in money demand at collapse, so the attack comes earlier.",
        params=_consistent(50.0, 50.0, 2.0, 8.0, horizon=35.0),
    ),
    "stylized_historical": Scenario(
        label="Stylized historical peg",
        description="Illustrative only, not an empirical calibration: larger initial credit, thinner reserves, and brisk credit growth.",
        params=_consistent(60.0, 40.0, 3.0, 4.5, horizon=22.0),
    ),
}
