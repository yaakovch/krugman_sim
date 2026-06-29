"""Numerical simulations for the Krugman/Flood-Garber crisis model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .model import (
    CrisisParams,
    actual_exchange_rate,
    attack_time,
    domestic_credit,
    mechanical_exhaustion_time,
    mechanical_reserves,
    no_arbitrage_gap,
    reserves,
    reserves_before_attack,
    shadow_rate,
)


@dataclass(frozen=True)
class DeterministicResult:
    params: CrisisParams
    data: pd.DataFrame
    analytical_attack_time: float
    numerical_attack_time: float | None
    mechanical_exhaustion_time: float
    reserves_before_attack: float


@dataclass(frozen=True)
class MonteCarloResult:
    params: CrisisParams
    crisis_times: np.ndarray
    paths: pd.DataFrame
    summary: pd.Series


def _time_grid(params: CrisisParams) -> np.ndarray:
    steps = int(np.floor(params.horizon / params.dt))
    grid = np.linspace(0.0, steps * params.dt, steps + 1)
    if grid[-1] < params.horizon:
        grid = np.append(grid, params.horizon)
    return grid


def _bisect_crossing(params: CrisisParams, left: float, right: float, tol: float) -> float:
    f_left = no_arbitrage_gap(left, params)
    f_right = no_arbitrage_gap(right, params)
    if f_left >= 0:
        return left
    if f_right < 0:
        raise ValueError("No crossing in supplied bracket")

    lo, hi = left, right
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if no_arbitrage_gap(mid, params) >= 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def detect_attack_time(params: CrisisParams, tol: float = 1e-10) -> float | None:
    """Detect the crisis by time stepping plus bisection of the crossing interval."""

    times = _time_grid(params)
    gaps = no_arbitrage_gap(times, params)
    crossed = np.flatnonzero(gaps >= 0)
    if len(crossed) == 0:
        return None
    idx = int(crossed[0])
    if idx == 0:
        return 0.0
    return _bisect_crossing(params, float(times[idx - 1]), float(times[idx]), tol=tol)


def deterministic_simulation(params: CrisisParams) -> DeterministicResult:
    """Simulate deterministic paths and cross-validate the analytical crisis time."""

    times = _time_grid(params)
    analytical = attack_time(params)
    numerical = detect_attack_time(params)
    data = pd.DataFrame(
        {
            "time": times,
            "domestic_credit": domestic_credit(times, params),
            "mechanical_reserves": mechanical_reserves(times, params),
            "actual_reserves": reserves(times, params),
            "shadow_exchange_rate": shadow_rate(times, params),
            "fixed_peg": params.peg,
            "actual_exchange_rate": actual_exchange_rate(times, params),
            "shadow_minus_peg": no_arbitrage_gap(times, params),
        }
    )
    return DeterministicResult(
        params=params,
        data=data,
        analytical_attack_time=analytical,
        numerical_attack_time=numerical,
        mechanical_exhaustion_time=mechanical_exhaustion_time(params),
        reserves_before_attack=reserves_before_attack(params),
    )


def monte_carlo_simulation(
    params: CrisisParams,
    n_paths: int = 500,
    sigma_credit: float = 0.25,
    sigma_money_demand: float = 0.0,
    seed: int | None = 1234,
) -> MonteCarloResult:
    """Discrete stochastic extension with noisy domestic-credit increments.

    ``sigma_credit`` scales Brownian-style credit shocks. When both shock standard
    deviations are zero, the deterministic analytical crisis time is returned for
    every path so tests and teaching output match the closed-form limit exactly.
    """

    if n_paths <= 0:
        raise ValueError("n_paths must be positive")
    if sigma_credit < 0 or sigma_money_demand < 0:
        raise ValueError("shock standard deviations must be non-negative")

    times = _time_grid(params)
    if sigma_credit == 0 and sigma_money_demand == 0:
        crisis_times = np.full(n_paths, attack_time(params), dtype=float)
        path_rows = pd.DataFrame(
            {
                "path": np.repeat(np.arange(min(n_paths, 25)), len(times)),
                "time": np.tile(times, min(n_paths, 25)),
                "domestic_credit": np.tile(domestic_credit(times, params), min(n_paths, 25)),
                "shadow_exchange_rate": np.tile(shadow_rate(times, params), min(n_paths, 25)),
            }
        )
        return MonteCarloResult(
            params=params,
            crisis_times=crisis_times,
            paths=path_rows,
            summary=_summarize_crisis_times(crisis_times),
        )

    rng = np.random.default_rng(seed)
    dt = params.dt
    n_steps = len(times)
    credit = np.empty((n_paths, n_steps), dtype=float)
    credit[:, 0] = params.domestic_credit0

    for step in range(1, n_steps):
        elapsed = times[step] - times[step - 1]
        shocks = sigma_credit * np.sqrt(elapsed) * rng.standard_normal(n_paths)
        increment = params.credit_growth * elapsed + shocks
        credit[:, step] = credit[:, step - 1] + increment

    demand_shocks = sigma_money_demand * rng.standard_normal((n_paths, n_steps))
    shadow = credit + params.alpha * (params.foreign_rate + params.credit_growth) + demand_shocks
    crossed = shadow >= params.peg
    crisis_times = np.full(n_paths, np.nan, dtype=float)

    for path_idx in range(n_paths):
        hits = np.flatnonzero(crossed[path_idx])
        if len(hits) == 0:
            continue
        idx = int(hits[0])
        if idx == 0:
            crisis_times[path_idx] = 0.0
            continue
        previous_gap = shadow[path_idx, idx - 1] - params.peg
        current_gap = shadow[path_idx, idx] - params.peg
        if current_gap == previous_gap:
            crisis_times[path_idx] = times[idx]
        else:
            weight = -previous_gap / (current_gap - previous_gap)
            crisis_times[path_idx] = times[idx - 1] + weight * (times[idx] - times[idx - 1])

    sample_paths = min(n_paths, 25)
    path_rows = pd.DataFrame(
        {
            "path": np.repeat(np.arange(sample_paths), n_steps),
            "time": np.tile(times, sample_paths),
            "domestic_credit": credit[:sample_paths].reshape(-1),
            "shadow_exchange_rate": shadow[:sample_paths].reshape(-1),
        }
    )
    return MonteCarloResult(
        params=params,
        crisis_times=crisis_times,
        paths=path_rows,
        summary=_summarize_crisis_times(crisis_times),
    )


def _summarize_crisis_times(crisis_times: np.ndarray) -> pd.Series:
    observed = crisis_times[~np.isnan(crisis_times)]
    missed = int(np.isnan(crisis_times).sum())
    if len(observed) == 0:
        return pd.Series(
            {
                "paths": len(crisis_times),
                "observed_crises": 0,
                "missed_by_horizon": missed,
                "mean": np.nan,
                "median": np.nan,
                "p05": np.nan,
                "p95": np.nan,
            }
        )
    return pd.Series(
        {
            "paths": len(crisis_times),
            "observed_crises": len(observed),
            "missed_by_horizon": missed,
            "mean": float(np.mean(observed)),
            "median": float(np.median(observed)),
            "p05": float(np.percentile(observed, 5)),
            "p95": float(np.percentile(observed, 95)),
        }
    )
