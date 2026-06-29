# Implementation Plan

## Stage 0: Scaffold

- Create project dependencies, `.gitignore`, Streamlit theme config, package skeleton, assets, tests, and notebook directory.
- Write `SPEC.md` and this implementation plan from the approved `PLAN.md`.

## Stage 1: Shared Model Core

- Implement `CrisisParams` with validation and money-market consistency helpers.
- Implement analytical functions for domestic credit, reserves, shadow exchange rate, mechanical exhaustion, attack time, and attack size.
- Implement deterministic time stepping plus bisection-based crisis detection.
- Implement stochastic Monte Carlo paths with exact zero-variance deterministic behavior.

## Stage 2: Visualizations

- Build Plotly figures for domestic credit, reserves, shadow rate versus peg, actual exchange rate, crisis-timing curve, mechanical versus rational timing, parameter sweeps, and Monte Carlo output.
- Reuse the same builders in the app and notebook.

## Stage 3: Streamlit App

- Add preset selection and parameter controls.
- Show core metrics and warnings for inconsistent peg choices.
- Present core figures, sensitivity analyses, Monte Carlo, exports, and math in tabs.
- Provide CSV, image, and printable handout downloads.

## Stage 4: Notebook, Tests, Docs

- Add notebook walkthrough importing the shared core.
- Add pytest coverage for analytical/numerical equality, model identities, invariants, Monte Carlo zero-noise limit, and comparative statics.
- Add README with economics, run, test, export, and deploy instructions.

## Stage 5: Local Verification and Deployment Prep

- Install dependencies in a local virtual environment if needed.
- Run `pytest tests/ -q`.
- Start `streamlit run app.py` locally and report the URL.
- Leave Streamlit Community Cloud deployment as a manual follow-up requiring GitHub/Streamlit authentication.
