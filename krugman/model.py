"""Analytical Krugman/Flood-Garber first-generation crisis model."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

import numpy as np


def _return_scalar_if_needed(original: float | np.ndarray, value: np.ndarray) -> float | np.ndarray:
    return float(np.asarray(value)) if np.ndim(original) == 0 else value


@dataclass(frozen=True)
class CrisisParams:
    """Parameters for the linear perfect-foresight balance-of-payments crisis model.

    The internally consistent fixed-rate normalization is
    ``peg = D0 + R0 + alpha * foreign_rate``. With that normalization,
    the rational attack time is ``mechanical_exhaustion_time - alpha``.
    """

    domestic_credit0: float = 50.0
    reserves0: float = 50.0
    credit_growth: float = 2.0
    alpha: float = 5.0
    peg: float = 100.0
    foreign_rate: float = 0.0
    horizon: float = 35.0
    dt: float = 0.1

    def __post_init__(self) -> None:
        checks = {
            "domestic_credit0": self.domestic_credit0,
            "reserves0": self.reserves0,
            "credit_growth": self.credit_growth,
            "alpha": self.alpha,
            "horizon": self.horizon,
            "dt": self.dt,
        }
        for name, value in checks.items():
            if not np.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.credit_growth <= 0:
            raise ValueError("credit_growth must be positive")
        if self.alpha <= 0:
            raise ValueError("alpha must be positive")
        if self.reserves0 <= 0:
            raise ValueError("reserves0 must be positive")
        if self.horizon <= 0:
            raise ValueError("horizon must be positive")
        if self.dt <= 0:
            raise ValueError("dt must be positive")

    @property
    def money_stock_fixed(self) -> float:
        """Nominal money stock while the peg is defended."""

        return self.domestic_credit0 + self.reserves0

    @property
    def money_demand_at_peg(self) -> float:
        """Money demand implied by PPP/UIP under the fixed peg."""

        return self.peg - self.alpha * self.foreign_rate

    @property
    def implied_consistent_peg(self) -> float:
        """Peg that makes initial reserves and money demand mutually consistent."""

        return self.money_stock_fixed + self.alpha * self.foreign_rate

    @property
    def money_market_gap(self) -> float:
        """Positive if the peg implies more money demand than supplied initially."""

        return self.money_demand_at_peg - self.money_stock_fixed

    @property
    def is_money_market_consistent(self) -> bool:
        return abs(self.money_market_gap) <= 1e-8

    def with_consistent_peg(self) -> "CrisisParams":
        return replace(self, peg=self.implied_consistent_peg)

    def with_updates(self, **updates: float) -> "CrisisParams":
        return replace(self, **updates)


def domestic_credit(t: float | np.ndarray, params: CrisisParams) -> float | np.ndarray:
    """Domestic credit path D(t) = D0 + mu t."""

    value = params.domestic_credit0 + params.credit_growth * np.asarray(t)
    return _return_scalar_if_needed(t, value)


def mechanical_reserves(t: float | np.ndarray, params: CrisisParams) -> float | np.ndarray:
    """Reserve path that would prevail if the peg were defended mechanically."""

    value = params.reserves0 - params.credit_growth * np.asarray(t)
    return _return_scalar_if_needed(t, value)


def reserves(t: float | np.ndarray, params: CrisisParams) -> float | np.ndarray:
    """Actual reserves, with a discrete attack that exhausts reserves at t_c."""

    times = np.asarray(t)
    attack = attack_time(params)
    pre_attack = mechanical_reserves(times, params)
    actual = np.where(times < attack, pre_attack, 0.0)
    return _return_scalar_if_needed(t, actual)


def mechanical_exhaustion_time(params: CrisisParams) -> float:
    """Date at which reserves would mechanically hit zero absent an attack."""

    return params.reserves0 / params.credit_growth


def shadow_rate(t: float | np.ndarray, params: CrisisParams) -> float | np.ndarray:
    """Post-collapse no-bubble shadow floating exchange rate.

    Under the linear Cagan money-demand setup, after reserves are gone M = D and
    the credit path depreciates at rate mu, so s_tilde(t) = D(t) + alpha(i* + mu).
    """

    value = domestic_credit(t, params) + params.alpha * (
        params.foreign_rate + params.credit_growth
    )
    return _return_scalar_if_needed(t, np.asarray(value))


def raw_attack_time(params: CrisisParams) -> float:
    """Unclipped closed-form crossing date for s_tilde(t) = peg."""

    numerator = (
        params.peg
        - params.alpha * (params.foreign_rate + params.credit_growth)
        - params.domestic_credit0
    )
    return numerator / params.credit_growth


def attack_time(params: CrisisParams) -> float:
    """Closed-form rational attack time, clipped at zero for already-breached pegs."""

    return max(0.0, raw_attack_time(params))


def reserves_before_attack(params: CrisisParams) -> float:
    """Reserves remaining just before the speculative attack."""

    return max(0.0, float(mechanical_reserves(attack_time(params), params)))


def attack_size(params: CrisisParams) -> float:
    """Reserve purchase needed to exhaust reserves at the attack."""

    return reserves_before_attack(params)


def actual_exchange_rate(t: float | np.ndarray, params: CrisisParams) -> float | np.ndarray:
    """Observed exchange rate: fixed before the crisis, shadow float afterward."""

    times = np.asarray(t)
    attack = attack_time(params)
    actual = np.where(times < attack, params.peg, shadow_rate(times, params))
    return _return_scalar_if_needed(t, actual)


def no_arbitrage_gap(t: float | np.ndarray, params: CrisisParams) -> float | np.ndarray:
    """Shadow rate minus peg; the crisis occurs when this reaches zero."""

    value = shadow_rate(t, params) - params.peg
    return _return_scalar_if_needed(t, np.asarray(value))


def money_demand_fixed(params: CrisisParams) -> float:
    """Money demand under the peg: m = p - alpha i = sbar - alpha i*."""

    return params.peg - params.alpha * params.foreign_rate


def money_demand_float(t: float | np.ndarray, params: CrisisParams) -> float | np.ndarray:
    """Money demand after collapse, equal to domestic credit on the no-bubble path."""

    value = shadow_rate(t, params) - params.alpha * (
        params.foreign_rate + params.credit_growth
    )
    return _return_scalar_if_needed(t, np.asarray(value))


def crisis_timing_for_credit_growth(
    params: CrisisParams, credit_growth_values: Iterable[float]
) -> np.ndarray:
    """Closed-form attack times across alternative credit-growth rates."""

    values = np.asarray(list(credit_growth_values), dtype=float)
    out = np.empty_like(values)
    for i, growth in enumerate(values):
        out[i] = attack_time(params.with_updates(credit_growth=float(growth)))
    return out
