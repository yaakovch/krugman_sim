# Krugman / Flood–Garber Balance-of-Payments Crisis Tool — Spec & Plan

## Context

Build a small, intuitive, low-dependency tool that solves and visualizes the first-generation
balance-of-payments crisis model (Krugman 1979) using the cleaner linear formulation of
Flood–Garber (1984). The teaching point: under a fixed peg with persistent domestic-credit
creation, reserves fall over time, but a rational speculative attack hits **before** reserves
mechanically reach zero — at the instant the *shadow floating exchange rate* rises to meet the peg.
Reserves are still strictly positive at the moment of attack; the attack discretely exhausts them.

Greenfield project at `/home/yaako/projects/krugman_sim`. A public GitHub repo already exists.

### Decisions locked in via spec interview
- **Audience:** mixed / layered — default to intuition, with expandable "show the math" sections.
- **Delivery:** Streamlit app, **sharing one Python core with a Jupyter notebook** (single source of truth).
- **Math:** **both** closed-form analytical collapse time **and** a numerical time-stepping simulation that cross-validate.
- **Plots:** Plotly (interactive; same figures reused in notebook + app).
- **Hosting:** deploy to a **free public URL** (Streamlit Community Cloud) using the existing GitHub repo; user assists with auth/manual steps.
- **v1 analyses (all in):** crisis-timing curve t*(μ); mechanical-exhaustion vs rational-attack comparison; general parameter sensitivity sweeps; **Monte Carlo** stochastic shocks.
- **Onboarding:** curated **presets + free sliders**, including a **stylized historical** preset (clearly flagged illustrative).
- **Validation:** pytest suite asserting analytical ≡ numerical + model invariants.
- **Exports:** CSV results table, figure export (PNG/SVG), one-page printable teaching handout.
- **Excel/VBA:** out of scope.

---

## The model (reference for implementation)

Continuous-time, perfect-foresight, log-linear (Cagan) money demand.

- Money demand:  `m − p = −α·i`  (α > 0 = interest semi-elasticity)
- PPP:  `p = s`  (foreign price normalized, p* = 0)
- UIP:  `i = i* + ṡ`  (perfect foresight)
- Money supply identity:  `M = D + R`  (domestic credit D + reserves R)
- Domestic credit grows at constant absolute rate:  `D(t) = D0 + μ·t`  (μ > 0)

**Fixed-rate regime (peg `s = s̄`):** ṡ = 0 ⇒ i = i* ⇒ real balances pinned ⇒ nominal money
`M̄` constant. Reserves fall one-for-one with credit: `R(t) = M̄ − D(t) = M̄ − D0 − μ·t`.
Mechanical exhaustion date: `t0 = (M̄ − D0)/μ`.

**Shadow floating rate** (post-collapse, R = 0 so M = D; forward-looking no-bubble solution):
`s̃(t) = d(t) + α·μ` — domestic credit plus a constant `α·μ` (anticipated post-collapse
depreciation μ scaled by α).

**Rational attack time:** first instant `s̃(t_c) = s̄`. Closed form (with the normalization above):
`t_c = t0 − α` — the attack precedes mechanical exhaustion by α. Reserves at attack
`R(t_c⁻) > 0`; the discrete attack buys the remainder, dropping R to 0 instantly (corresponding to
the jump in i from i* to i*+μ shrinking money demand).

**Stochastic extension (Monte Carlo):** discrete-time sim where domestic-credit growth carries
Gaussian noise around drift μ (optionally money-demand shocks); for each path find the first time
the shadow rate ≥ peg; report a **distribution** of crisis times (histogram + summary stats). The
deterministic case is the zero-variance limit and must match the closed form.

> The exact internally-consistent equation set and the analytical-vs-numerical agreement tolerance
> will be pinned and documented in `SPEC.md` at the start of execution.

---

## Architecture & repo structure

Keep dependencies minimal so Streamlit Community Cloud deploys cleanly and non-technical users can run locally.

```
krugman_sim/
  README.md                      # overview, run + deploy instructions, the economics in brief
  SPEC.md                        # full spec (written first in execution, per kickoff workflow)
  implementation_plan.md         # execution plan (written first in execution)
  requirements.txt               # streamlit, numpy, pandas, plotly, kaleido
  app.py                         # Streamlit entry point AT ROOT (required by Community Cloud)
  krugman/
    __init__.py
    model.py                     # params dataclass; analytical t_c, t0, shadow rate, reserves
    simulate.py                  # deterministic time-stepping + Monte Carlo drivers
    plots.py                     # Plotly figure builders (shared by app + notebook)
    scenarios.py                 # presets: baseline, fast credit, high-α, stylized historical
    export.py                    # CSV, PNG/SVG (via kaleido), HTML teaching handout
  notebooks/
    krugman_bop_crisis.ipynb     # transparent walkthrough using the same core
  tests/
    test_model.py                # analytical ≡ numerical, invariants
  assets/handout_template.html
  .streamlit/config.toml         # light theme
```

**Dependencies:** `streamlit, numpy, pandas, plotly, kaleido` (+ `pytest` dev). Avoid scipy — use a
closed form plus a small numpy bisection for the numerical root-find. The handout renders the key
Plotly figure to PNG (kaleido), embeds it in an HTML template; users print-to-PDF (no heavy PDF libs).

**DRY principle:** `model.py`/`simulate.py`/`plots.py` are the single source of truth; both the
Streamlit app and the notebook import them — no duplicated math.

---

## Implementation stages

### Stage 0 — Spec & scaffold
- Write `SPEC.md` and `implementation_plan.md` into the repo (honors the kickoff workflow's deliverables).
- Init git locally, wire the existing GitHub remote (confirm URL with user), `requirements.txt`, package skeleton, `.gitignore`.

### Stage 1 — Core model (`model.py`, `simulate.py`)
- `CrisisParams` dataclass (D0, μ, R0/M̄, s̄, α, i*, horizon, dt).
- Analytical: `mechanical_exhaustion_time`, `shadow_rate(t)`, `attack_time`, `reserves(t)`, attack size.
- Numerical: deterministic time-stepping that reproduces R(t), s̃(t), and detects the crisis by
  bisection where `s̃ = s̄`; assert agreement with closed form.

### Stage 2 — Visualization (`plots.py`)
Plotly builders for the 4 core series + the 4 chosen analyses:
1. Domestic credit over time
2. Reserves over time (with attack point + mechanical-exhaustion point marked)
3. Shadow rate vs peg (attack = crossing)
4. Actual exchange rate before/after collapse
5. Crisis-timing curve `t*(μ)`
6. Mechanical-exhaustion vs rational-attack overlay (the gap = α)
7. General sensitivity sweep (user picks any parameter)
8. Monte Carlo histogram of crisis times
All with clear annotations marking the crisis; layered explanatory text per figure.

### Stage 3 — Streamlit app (`app.py`)
- Sidebar sliders for all parameters; preset selector (baseline / fast credit / high-α / stylized historical).
- Live recompute; tabbed or scrolling layout pairing each figure with intuition + an expandable "show the math".
- Export controls: CSV download, figure PNG/SVG download, "generate teaching handout" (HTML).
- Monte Carlo panel (n paths, shock σ) with histogram + summary stats.

### Stage 4 — Notebook, tests, docs
- `krugman_bop_crisis.ipynb`: narrated walkthrough importing the same core, reproducing the figures.
- `tests/test_model.py`: analytical ≡ numerical within tolerance; invariants (reserves continuous &
  positive pre-attack, money-market identity, deterministic = zero-noise Monte Carlo limit, t_c = t0 − α).
- `README.md`: what it is, the economics in brief, run locally, deploy, reproduce.

### Stage 5 — Deploy
- Push to the existing public GitHub repo; connect Streamlit Community Cloud (`app.py` at root,
  `requirements.txt` resolved); user performs GitHub auth / clicks where needed; confirm the live URL.

---

## Deliverables
1. Streamlit app (`app.py` + `krugman/` core) — interactive, deployed to a public URL.
2. Jupyter notebook walkthrough using the same core.
3. `SPEC.md` + `implementation_plan.md` (parameter table + methodology inside SPEC).
4. `README.md` with the economics explanation and run/deploy/reproduce steps.
5. One-page printable teaching handout (HTML → print-to-PDF).
6. pytest validation suite.

## Out of scope (v1)
Excel/VBA version; shareable-parameter-URL permalinks; second-generation crisis models; empirical
econometric calibration (the "stylized historical" preset is illustrative only). Noted as possible future extensions.

---

## Verification
- **Tests:** `pytest tests/ -q` — analytical ≡ numerical within tolerance; all invariants pass;
  deterministic run equals the zero-variance Monte Carlo limit; `t_c = t0 − α`.
- **Notebook:** run top-to-bottom without errors; figures render; printed crisis time matches `attack_time`.
- **App locally:** `streamlit run app.py` — sliders recompute live; each preset loads sensible values;
  reserves/shadow/crisis markers move coherently (e.g., higher μ or α ⇒ earlier crisis); CSV, PNG/SVG,
  and handout exports download and open correctly; Monte Carlo histogram renders.
- **Deploy:** Community Cloud build succeeds; live URL loads and is interactive end-to-end.
- **Economic sanity:** attack always strictly precedes mechanical exhaustion; reserves strictly
  positive immediately before the attack; raising α or μ moves the crisis earlier.
