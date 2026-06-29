# Krugman / Flood-Garber Balance-of-Payments Crisis Tool

Interactive Streamlit app and notebook for the first-generation balance-of-payments crisis model. The project uses one shared Python core for the analytical solution, numerical time stepping, Plotly figures, Monte Carlo simulations, exports, tests, and the notebook.

## Economics in Brief

Under a fixed exchange rate, domestic credit grows while the central bank defends the peg by selling reserves. Reserves therefore fall over time:

$$
R(t) = R_0 - \mu t
$$

If markets were not forward-looking, reserves would mechanically reach zero at:

$$
t_0 = \frac{R_0}{\mu}
$$

The shadow floating exchange rate after collapse is:

$$
\tilde{s}(t) = D_0 + \mu t + \alpha(i^* + \mu)
$$

The rational speculative attack occurs when the shadow rate reaches the peg. With a fixed-regime-consistent peg, this gives the textbook result:

$$
\tilde{s}(t_c) = \bar{s}
\quad\Longrightarrow\quad
t_c = t_0 - \alpha
$$

So the crisis arrives before reserves mechanically hit zero, and reserves are still positive immediately before the attack.

## Project Structure

```text
app.py
krugman/
  model.py
  simulate.py
  plots.py
  scenarios.py
  export.py
notebooks/
  krugman_bop_crisis.ipynb
tests/
  test_model.py
assets/
  handout_template.html
SPEC.md
implementation_plan.md
requirements.txt
```

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Run Tests

```bash
pytest tests/ -q
```

The tests check analytical and numerical agreement, reserve and money-demand identities, the zero-noise Monte Carlo limit, and comparative statics.

## Notebook

Open `notebooks/krugman_bop_crisis.ipynb` in Jupyter. It imports the same `krugman/` package used by the app.

## Exports

The app can download:

- deterministic simulation CSV,
- Plotly figures as PNG/SVG when Kaleido image export is available,
- a one-page printable HTML handout.

## Streamlit Community Cloud Deployment

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app from the public repository.
4. Set the entry point to `app.py`.
5. Let Streamlit install `requirements.txt`.

Authentication and the final publish click must be done manually by the repository owner.
