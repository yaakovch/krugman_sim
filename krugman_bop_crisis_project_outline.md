# Numerical Tool for the Krugman Balance-of-Payments Crisis Model

## Short project outline

### Goal

Build a simple, user-friendly computational tool that solves and visualizes the classic first-generation balance-of-payments crisis model associated with Krugman (1979), using the cleaner linear version developed by Flood and Garber (1984) as the main implementation framework.

The final product should help users understand how persistent domestic credit creation under a fixed exchange-rate regime can gradually deplete foreign-exchange reserves and trigger a speculative attack before reserves are mechanically exhausted.

---

## Core economic idea

The model describes an economy with a fixed exchange rate. The government or central bank expands domestic credit over time, for example to finance fiscal deficits. To maintain the peg, the central bank must sell foreign reserves. As domestic credit rises, reserves fall.

The key insight is that the crisis does **not** necessarily occur when reserves reach zero. Under forward-looking behavior, speculators attack earlier: the attack occurs when the shadow exchange rate—the exchange rate that would prevail after the collapse of the peg—equals the fixed exchange rate.

---

## What we can build

### 1. Baseline Python notebook

Create a clear Jupyter notebook that:

- defines the model equations,
- sets baseline parameters,
- simulates the dynamics over time,
- calculates the crisis time,
- produces clean graphs.

This should be the first version because it is transparent, easy to debug, and easy to explain.

### 2. Interactive Streamlit app

Convert the notebook into a small Streamlit app with sliders for key parameters:

- initial domestic credit,
- domestic credit growth rate,
- initial reserves,
- fixed exchange rate,
- money-demand parameters,
- interest-rate or depreciation sensitivity.

The user will be able to change assumptions and immediately see how the timing of the crisis changes.

### 3. Main graphs

The tool should produce several simple, polished graphs:

1. Domestic credit over time.
2. Foreign-exchange reserves over time.
3. Shadow exchange rate versus the fixed peg.
4. Actual exchange rate before and after the crisis.
5. Crisis timing as a function of the domestic credit growth rate.
6. Optional comparison: mechanical reserve exhaustion versus rational speculative attack.

### 4. Educational explanations

Add short explanations next to each graph:

- what the graph shows,
- why the variable moves as it does,
- what triggers the crisis,
- how changing parameters affects the result.

The aim is not only to solve the model but also to make it teachable.

---

## Suggested implementation stages

### Stage 1: Minimal working model

Implement the simplest linear version:

- domestic credit grows at a constant rate,
- reserves fall one-for-one while the peg is maintained,
- the shadow exchange rate is calculated,
- the crisis occurs when the shadow exchange rate reaches the peg.

Output:

- basic time-series simulation,
- crisis time,
- reserves just before the attack,
- two or three graphs.

### Stage 2: Better visualization

Improve the graphs:

- add labels and annotations,
- mark the crisis point clearly,
- compare alternative parameter values,
- show what happens under faster or slower domestic credit growth.

Output:

- publication-quality or classroom-quality figures.

### Stage 3: Interactive app

Build a Streamlit interface:

- parameter sliders,
- automatic recalculation,
- downloadable results table,
- explanatory text.

Output:

- a small educational app that can be shared with students or colleagues.

### Stage 4: Optional Excel/VBA version

If accessibility through Excel is important, create a simplified version in Excel/VBA.

This version would be less elegant than Python/Streamlit, but it may be useful for users who prefer spreadsheets.

---

## Deliverables

The project can produce:

1. A Jupyter notebook with the full model and graphs.
2. A Streamlit app for interactive use.
3. A short written explanation of the economics.
4. A parameter table explaining each assumption.
5. Optional Excel/VBA version.
6. Optional teaching handout or README file.

---

## Why this is feasible

This is not a heavy numerical project. The baseline version has a simple analytical structure, and the numerical component is mainly used for simulation, visualization, sensitivity analysis, and interactivity.

For someone comfortable with Python, the first useful version can be built with standard tools:

- `numpy`
- `pandas`
- `matplotlib` or `plotly`
- `streamlit`

---

## Possible extensions

After the baseline version works, we can extend it by adding:

- stochastic shocks,
- alternative fiscal paths,
- uncertainty about the timing of the attack,
- comparison with second-generation crisis models,
- empirical calibration examples,
- teaching exercises for students.

---

## References

- Krugman, Paul (1979). *A Model of Balance-of-Payments Crises*. Journal of Money, Credit and Banking, 11(3), 311–325.  
  https://stonecenter.gc.cuny.edu/publications/a-model-of-balance-of-payment-crises/

- Flood, Robert P. and Garber, Peter M. (1984). *Collapsing Exchange-Rate Regimes: Some Linear Examples*. Journal of International Economics, 17(1–2), 1–13.  
  https://ideas.repec.org/a/eee/inecon/v17y1984i1-2p1-13.html

- Krugman, Paul. *Currency Crisis Model* notes and references.  
  https://web.mit.edu/krugman/www/crises.html
