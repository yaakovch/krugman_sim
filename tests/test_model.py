import math

import numpy as np

from krugman.model import (
    CrisisParams,
    actual_exchange_rate,
    attack_time,
    domestic_credit,
    mechanical_exhaustion_time,
    money_demand_fixed,
    money_demand_float,
    reserves,
    reserves_before_attack,
    shadow_rate,
)
from krugman.simulate import deterministic_simulation, monte_carlo_simulation


def baseline_params() -> CrisisParams:
    return CrisisParams(
        domestic_credit0=50.0,
        reserves0=50.0,
        credit_growth=2.0,
        alpha=5.0,
        peg=100.0,
        foreign_rate=0.0,
        horizon=35.0,
        dt=0.25,
    )


def test_consistent_closed_form_attack_time_equals_t0_minus_alpha():
    params = baseline_params()

    assert params.is_money_market_consistent
    assert attack_time(params) == mechanical_exhaustion_time(params) - params.alpha
    assert attack_time(params) == 20.0
    assert mechanical_exhaustion_time(params) == 25.0


def test_numerical_crossing_matches_analytical_attack_time():
    result = deterministic_simulation(baseline_params())

    assert result.numerical_attack_time is not None
    assert math.isclose(
        result.numerical_attack_time,
        result.analytical_attack_time,
        rel_tol=0.0,
        abs_tol=1e-8,
    )


def test_reserves_positive_before_attack_and_zero_after_attack():
    params = baseline_params()
    tc = attack_time(params)

    assert reserves_before_attack(params) > 0
    assert reserves(tc - 1e-6, params) > 0
    assert reserves(tc, params) == 0
    assert reserves(tc + 1e-6, params) == 0


def test_exchange_rate_is_continuous_at_attack_then_floats():
    params = baseline_params()
    tc = attack_time(params)

    assert math.isclose(shadow_rate(tc, params), params.peg)
    assert math.isclose(actual_exchange_rate(tc - 1e-6, params), params.peg)
    assert actual_exchange_rate(tc + 1.0, params) > params.peg


def test_money_market_identities_hold_on_consistent_path():
    params = baseline_params()

    assert math.isclose(money_demand_fixed(params), params.money_stock_fixed)

    times = np.array([attack_time(params), attack_time(params) + 1.0, params.horizon])
    np.testing.assert_allclose(money_demand_float(times, params), domestic_credit(times, params))


def test_zero_noise_monte_carlo_matches_deterministic_limit():
    params = baseline_params()
    mc = monte_carlo_simulation(params, n_paths=30, sigma_credit=0.0, sigma_money_demand=0.0)

    np.testing.assert_allclose(mc.crisis_times, np.full(30, attack_time(params)))
    assert mc.summary["observed_crises"] == 30


def test_higher_alpha_and_credit_growth_move_crisis_earlier():
    params = baseline_params()
    higher_alpha = params.with_updates(alpha=params.alpha + 1.0).with_consistent_peg()
    higher_growth = params.with_updates(credit_growth=params.credit_growth + 1.0)

    assert attack_time(higher_alpha) < attack_time(params)
    assert attack_time(higher_growth) < attack_time(params)


def test_randomized_consistent_params_match_normalized_flood_garber_identities():
    rng = np.random.default_rng(20260629)

    for _ in range(100):
        credit_growth = rng.uniform(0.25, 6.0)
        alpha = rng.uniform(0.5, 6.0)
        reserves0 = rng.uniform((alpha + 2.0) * credit_growth, 120.0)
        domestic_credit0 = rng.uniform(5.0, 120.0)
        foreign_rate = rng.uniform(0.0, 0.12)
        params = CrisisParams(
            domestic_credit0=float(domestic_credit0),
            reserves0=float(reserves0),
            credit_growth=float(credit_growth),
            alpha=float(alpha),
            peg=float(domestic_credit0 + reserves0 + alpha * foreign_rate),
            foreign_rate=float(foreign_rate),
            horizon=float(reserves0 / credit_growth + 5.0),
            dt=0.37,
        )

        t0 = mechanical_exhaustion_time(params)
        tc = attack_time(params)

        assert params.is_money_market_consistent
        assert math.isclose(money_demand_fixed(params), params.money_stock_fixed)
        assert math.isclose(t0, params.reserves0 / params.credit_growth)
        assert math.isclose(tc, t0 - params.alpha, abs_tol=1e-10)
        assert math.isclose(shadow_rate(tc, params), params.peg, abs_tol=1e-9)
        assert math.isclose(
            reserves_before_attack(params),
            params.alpha * params.credit_growth,
            rel_tol=1e-10,
            abs_tol=1e-9,
        )

        result = deterministic_simulation(params)
        assert result.numerical_attack_time is not None
        assert math.isclose(result.numerical_attack_time, tc, abs_tol=1e-8)
