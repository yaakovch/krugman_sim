# Krugman / Flood-Garber Balance-of-Payments Crisis Tool Spec

## Purpose

Build a small Streamlit teaching tool and matching notebook for the first-generation balance-of-payments crisis model associated with Krugman (1979), implemented in the linear Flood-Garber style. The tool emphasizes the central timing result: reserves fall gradually under a peg, but the rational attack arrives before mechanical reserve exhaustion, at the first instant the shadow floating exchange rate reaches the peg.

## Audience

The primary audience is mixed: students, instructors, and technically curious readers. The default experience should be intuitive, while the app and notebook also expose the equations and validation checks for users who want the math.

## Model

The implemented model is the normalized linear Flood-Garber teaching form. Foreign prices, the
money-demand intercept, and the exchange-rate scale are normalized so the app can focus on the
crisis-timing mechanism:

- Money supply: `M = D + R`
- Domestic credit: `D(t) = D0 + mu * t`
- Linear money demand in exchange-rate units: `M = S - alpha * i`
- Linear perfect-foresight interest parity: `i = i_star + dS/dt`

While the peg is defended, `S = Sbar`, `dS/dt = 0`, and reserves fall one-for-one with domestic credit:

`R(t) = R0 - mu * t`

Mechanical exhaustion is:

`t0 = R0 / mu`

After collapse, reserves are zero and the no-bubble shadow float is:

`S_tilde(t) = D0 + mu * t + alpha * (i_star + mu)`

The rational attack time is the first `t` such that `S_tilde(t) = Sbar`:

`tc = (Sbar - alpha * (i_star + mu) - D0) / mu`

For an internally consistent peg, `Sbar = D0 + R0 + alpha * i_star`, so:

`tc = t0 - alpha`

The deterministic app uses the general formula above and warns when the slider choices break the fixed-regime money-market consistency condition.

## Functional Requirements

- Provide curated presets: baseline, fast domestic-credit growth, high money-demand sensitivity, and a stylized historical peg flagged as illustrative only.
- Provide sliders for initial domestic credit, initial reserves, credit-growth rate, money-demand semi-elasticity, foreign interest rate, horizon, time step, and optionally the peg.
- Keep the peg consistent with initial money supply by default, with an explicit option to override it.
- Show analytical crisis timing, numerical bisection timing, mechanical reserve exhaustion, lead time, and reserves just before attack.
- Plot domestic credit, reserves, shadow exchange rate versus the peg, and actual exchange rate.
- Provide additional analyses: crisis timing as a function of `mu`, rational attack versus mechanical exhaustion, a general parameter sensitivity sweep, and a Monte Carlo crisis-time distribution.
- Export deterministic simulation results as CSV.
- Export Plotly figures as PNG/SVG when Kaleido is available.
- Generate a one-page printable HTML teaching handout.
- Provide a Jupyter notebook walkthrough that imports the same shared Python core.
- Provide tests that verify analytical/numerical agreement and model invariants.

## Non-Goals

- No Excel/VBA version in v1.
- No empirical econometric calibration.
- No second-generation crisis model.
- No shareable parameter URL permalinks in v1.

## Validation Criteria

- `pytest tests/ -q` passes.
- Analytical attack time and numerical bisection agree for internally consistent parameters.
- In the consistent deterministic case, `tc = t0 - alpha`.
- Reserves are positive immediately before the attack and zero after the attack.
- The floating-regime money-demand identity equals domestic credit on the shadow path.
- Zero-variance Monte Carlo returns the deterministic analytical crisis time.
- Raising `alpha` or `mu` moves the rational attack earlier for the baseline case.

## Reproducibility

Install dependencies with `pip install -r requirements.txt`, run tests with `pytest tests/ -q`, run the app with `streamlit run app.py`, and open the notebook at `notebooks/krugman_bop_crisis.ipynb`.
