from __future__ import annotations

import streamlit as st

from krugman.export import figure_image_bytes, render_handout_html, simulation_csv_bytes
from krugman.model import CrisisParams, attack_time, mechanical_exhaustion_time
from krugman.plots import (
    actual_exchange_rate_figure,
    core_figures,
    crisis_timing_curve_figure,
    mechanical_vs_attack_figure,
    monte_carlo_histogram_figure,
    monte_carlo_paths_figure,
    sensitivity_sweep_figure,
)
from krugman.scenarios import SCENARIOS
from krugman.simulate import deterministic_simulation, monte_carlo_simulation


st.set_page_config(
    page_title="Krugman BOP Crisis Tool",
    page_icon=None,
    layout="wide",
)

PLOT_CONFIG = {
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "filename": "krugman_crisis_figure", "scale": 2},
}


def _format_number(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "Not reached"
    return f"{value:.{digits}f}"


def _scenario_label(key: str) -> str:
    return SCENARIOS[key].label


def _render_notation_legend(params: CrisisParams, result) -> None:
    st.markdown("**Notation legend**")
    left, right = st.columns(2)
    left.markdown(
        rf"""
- $D_0$ - initial domestic credit, currently {params.domestic_credit0:.2f}
- $R_0$ - initial reserves, currently {params.reserves0:.2f}
- $\mu$ - domestic-credit growth rate, currently {params.credit_growth:.2f}
- $\alpha$ - interest semi-elasticity of money demand, currently {params.alpha:.2f}
- $i^*$ - foreign interest rate, currently {params.foreign_rate:.3f}
        """
    )
    right.markdown(
        rf"""
- $\bar{{S}}$ - fixed peg, currently {params.peg:.2f}
- $\tilde{{S}}(t)$ - shadow floating exchange rate after collapse
- $t_0$ - mechanical reserve-exhaustion date, currently {result.mechanical_exhaustion_time:.2f}
- $t_c$ - rational speculative-attack date, currently {result.analytical_attack_time:.2f}
- $R(t_c^-)$ - reserves just before the attack, currently {result.reserves_before_attack:.2f}
        """
    )


def _render_model_equations() -> None:
    st.markdown(
        "The app uses the normalized linear Flood-Garber form. Foreign prices, the money-demand "
        "intercept, and the exchange-rate scale are normalized so the core system is:"
    )
    st.latex(
        r"""
\begin{aligned}
M_t &= D_t + R_t \\
D_t &= D_0 + \mu t \\
M_t &= S_t - \alpha i_t \\
i_t &= i^* + \dot{S}_t
\end{aligned}
        """
    )
    st.markdown("While the peg is defended, the exchange rate is fixed, so reserves absorb credit growth:")
    st.latex(
        r"""
\begin{aligned}
\dot{S}_t &= 0,\quad i_t = i^* \\
\bar{M} &= \bar{S} - \alpha i^* \\
R(t) &= R_0 - \mu t \\
t_0 &= \frac{R_0}{\mu}
\end{aligned}
        """
    )
    st.markdown("After a collapse, reserves are zero and the no-bubble shadow float is:")
    st.latex(
        r"""
\tilde{S}(t) = D_0 + \mu t + \alpha(i^* + \mu)
        """
    )
    st.markdown("The rational attack occurs at the first crossing of the shadow float and the peg:")
    st.latex(
        r"""
\begin{aligned}
\tilde{S}(t_c) &= \bar{S} \\
t_c &= \frac{\bar{S} - \alpha(i^*+\mu) - D_0}{\mu}
\end{aligned}
        """
    )
    st.markdown("With a fixed-regime-consistent peg, the textbook timing result follows:")
    st.latex(
        r"""
\bar{S} = D_0 + R_0 + \alpha i^*
\quad\Longrightarrow\quad
t_c = t_0 - \alpha
        """
    )


def _render_current_timing(params: CrisisParams, result) -> None:
    st.markdown("For the current slider values:")
    st.latex(
        rf"""
\begin{{aligned}}
t_0 &= \frac{{R_0}}{{\mu}}
     = \frac{{{params.reserves0:.2f}}}{{{params.credit_growth:.2f}}}
     = {result.mechanical_exhaustion_time:.2f} \\
t_c &= {result.analytical_attack_time:.2f} \\
t_0 - t_c &= {result.mechanical_exhaustion_time - result.analytical_attack_time:.2f} \\
R(t_c^-) &= {result.reserves_before_attack:.2f}
\end{{aligned}}
        """
    )


st.title("Krugman / Flood-Garber Balance-of-Payments Crisis")
st.caption(
    "An interactive teaching tool for the first-generation crisis result: the rational attack "
    "arrives before mechanical reserve exhaustion."
)

with st.sidebar:
    st.header("Parameters")
    scenario_key = st.selectbox(
        "Preset",
        options=list(SCENARIOS.keys()),
        format_func=_scenario_label,
    )
    scenario = SCENARIOS[scenario_key]
    st.caption(scenario.description)

    base = scenario.params
    domestic_credit0 = st.slider(
        "Initial domestic credit D0",
        min_value=0.0,
        max_value=120.0,
        value=float(base.domestic_credit0),
        step=1.0,
    )
    reserves0 = st.slider(
        "Initial reserves R0",
        min_value=1.0,
        max_value=120.0,
        value=float(base.reserves0),
        step=1.0,
    )
    credit_growth = st.slider(
        "Credit growth mu",
        min_value=0.1,
        max_value=10.0,
        value=float(base.credit_growth),
        step=0.1,
    )
    alpha = st.slider(
        "Money-demand semi-elasticity alpha",
        min_value=0.1,
        max_value=15.0,
        value=float(base.alpha),
        step=0.1,
    )
    foreign_rate = st.slider(
        "Foreign interest rate i*",
        min_value=0.0,
        max_value=0.20,
        value=float(base.foreign_rate),
        step=0.005,
        format="%.3f",
    )
    horizon = st.slider(
        "Simulation horizon",
        min_value=5.0,
        max_value=80.0,
        value=float(base.horizon),
        step=1.0,
    )
    dt = st.slider(
        "Time step",
        min_value=0.02,
        max_value=1.0,
        value=float(base.dt),
        step=0.02,
        format="%.2f",
    )

    keep_consistent_peg = st.checkbox("Keep peg consistent with initial money market", value=True)
    consistent_peg = domestic_credit0 + reserves0 + alpha * foreign_rate
    if keep_consistent_peg:
        peg = consistent_peg
        st.metric("Fixed peg Sbar", f"{peg:.2f}")
    else:
        peg = st.number_input(
            "Fixed peg Sbar",
            min_value=1.0,
            max_value=300.0,
            value=float(consistent_peg),
            step=1.0,
        )

params = CrisisParams(
    domestic_credit0=domestic_credit0,
    reserves0=reserves0,
    credit_growth=credit_growth,
    alpha=alpha,
    peg=peg,
    foreign_rate=foreign_rate,
    horizon=horizon,
    dt=dt,
)
result = deterministic_simulation(params)
figures = core_figures(result)

if not params.is_money_market_consistent:
    st.warning(
        "The selected peg is not consistent with initial money supply under fixed-rate money "
        "demand. The app still solves the shadow-rate crossing, but the textbook identity "
        "tc = t0 - alpha no longer applies."
    )

if result.numerical_attack_time is None:
    st.info(
        "The analytical attack time lies beyond the current simulation horizon. Increase the "
        "horizon to see the numerical crossing in the time-step simulation."
    )

metric_cols = st.columns(5)
metric_cols[0].metric("Attack time tc", _format_number(result.analytical_attack_time))
metric_cols[1].metric("Numerical tc", _format_number(result.numerical_attack_time))
metric_cols[2].metric("Mechanical t0", _format_number(result.mechanical_exhaustion_time))
metric_cols[3].metric(
    "Lead time",
    _format_number(result.mechanical_exhaustion_time - result.analytical_attack_time),
)
metric_cols[4].metric("Reserves at attack", _format_number(result.reserves_before_attack))

core_tab, analysis_tab, mc_tab, export_tab, math_tab = st.tabs(
    ["Core Dynamics", "Sensitivity", "Monte Carlo", "Exports", "Math"]
)

with core_tab:
    st.subheader("Deterministic Crisis Dynamics")
    st.plotly_chart(figures["domestic_credit"], width="stretch", config=PLOT_CONFIG)
    st.markdown(
        "Domestic credit grows at a constant absolute rate. Under the peg, reserve sales "
        "absorb that credit expansion."
    )
    st.plotly_chart(figures["reserves"], width="stretch", config=PLOT_CONFIG)
    st.markdown(
        "Actual reserves drop discretely at the attack. The dotted path marks the no-attack "
        "reserve-exhaustion date."
    )
    st.plotly_chart(figures["shadow_rate"], width="stretch", config=PLOT_CONFIG)
    st.markdown(
        "The attack occurs at the crossing. Once the shadow float reaches the peg, attacking "
        "the peg exhausts reserves without requiring an exchange-rate jump at collapse."
    )
    st.plotly_chart(figures["actual_exchange_rate"], width="stretch", config=PLOT_CONFIG)
    st.markdown(
        "The exchange rate is fixed before the crisis and follows the shadow float after "
        "the peg collapses."
    )

    with st.expander("Show the math"):
        _render_notation_legend(params, result)
        _render_model_equations()
        _render_current_timing(params, result)

with analysis_tab:
    st.subheader("Comparative Statics")
    st.plotly_chart(crisis_timing_curve_figure(params), width="stretch", config=PLOT_CONFIG)
    st.plotly_chart(mechanical_vs_attack_figure(result), width="stretch", config=PLOT_CONFIG)

    sweep_parameter = st.selectbox(
        "Sensitivity parameter",
        options=[
            "alpha",
            "credit_growth",
            "reserves0",
            "domestic_credit0",
            "foreign_rate",
            "peg",
        ],
        format_func={
            "alpha": "Money-demand semi-elasticity alpha",
            "credit_growth": "Credit growth mu",
            "reserves0": "Initial reserves R0",
            "domestic_credit0": "Initial domestic credit D0",
            "foreign_rate": "Foreign interest rate i*",
            "peg": "Fixed peg Sbar",
        }.get,
    )
    st.plotly_chart(
        sensitivity_sweep_figure(params, parameter=sweep_parameter),
        width="stretch",
        config=PLOT_CONFIG,
    )

with mc_tab:
    st.subheader("Stochastic Crisis Timing")
    mc_controls = st.columns(4)
    n_paths = mc_controls[0].slider("Paths", min_value=100, max_value=5000, value=800, step=100)
    sigma_credit = mc_controls[1].slider(
        "Credit shock sigma",
        min_value=0.0,
        max_value=2.0,
        value=0.35,
        step=0.05,
    )
    sigma_money = mc_controls[2].slider(
        "Money-demand shock sigma",
        min_value=0.0,
        max_value=2.0,
        value=0.0,
        step=0.05,
    )
    seed = mc_controls[3].number_input("Seed", min_value=0, max_value=999999, value=1234, step=1)

    mc_result = monte_carlo_simulation(
        params,
        n_paths=n_paths,
        sigma_credit=sigma_credit,
        sigma_money_demand=sigma_money,
        seed=int(seed),
    )
    summary_cols = st.columns(4)
    summary_cols[0].metric("Observed crises", f"{int(mc_result.summary['observed_crises'])}")
    summary_cols[1].metric("Mean", _format_number(float(mc_result.summary["mean"])))
    summary_cols[2].metric("Median", _format_number(float(mc_result.summary["median"])))
    summary_cols[3].metric("Missed by horizon", f"{int(mc_result.summary['missed_by_horizon'])}")

    mc_left, mc_right = st.columns(2)
    with mc_left:
        st.plotly_chart(monte_carlo_histogram_figure(mc_result), width="stretch", config=PLOT_CONFIG)
    with mc_right:
        st.plotly_chart(monte_carlo_paths_figure(mc_result), width="stretch", config=PLOT_CONFIG)

with export_tab:
    st.subheader("Downloads")
    st.download_button(
        "Download deterministic CSV",
        data=simulation_csv_bytes(result),
        file_name="krugman_deterministic_simulation.csv",
        mime="text/csv",
    )

    export_figures = {
        "Domestic credit": figures["domestic_credit"],
        "Reserves": figures["reserves"],
        "Shadow rate vs peg": figures["shadow_rate"],
        "Actual exchange rate": actual_exchange_rate_figure(result),
        "Crisis timing curve": crisis_timing_curve_figure(params),
        "Mechanical vs attack": mechanical_vs_attack_figure(result),
    }
    figure_name = st.selectbox("Figure", options=list(export_figures.keys()))
    image_format = st.radio("Format", options=["png", "svg"], horizontal=True)
    try:
        image_bytes = figure_image_bytes(export_figures[figure_name], fmt=image_format)
        st.download_button(
            f"Download {image_format.upper()}",
            data=image_bytes,
            file_name=f"krugman_{figure_name.lower().replace(' ', '_')}.{image_format}",
            mime="image/png" if image_format == "png" else "image/svg+xml",
        )
    except Exception as exc:
        st.info(f"Figure image export is unavailable in this environment: {exc}")

    handout_html = render_handout_html(params, result, figures["reserves"])
    st.download_button(
        "Download teaching handout HTML",
        data=handout_html.encode("utf-8"),
        file_name="krugman_crisis_handout.html",
        mime="text/html",
    )

with math_tab:
    st.subheader("Model Reference")
    st.markdown(
        """
The app implements the linear Flood-Garber version of the Krugman first-generation crisis model.
The shadow float is the no-bubble post-collapse exchange rate; the peg becomes vulnerable
when that shadow float reaches the fixed rate.
        """
    )
    _render_notation_legend(params, result)
    _render_model_equations()
    _render_current_timing(params, result)
    st.dataframe(
        {
            "Quantity": [
                "Consistent peg",
                "Money-market gap",
                "Closed-form attack time",
                "Mechanical exhaustion time",
                "Reserve purchase at attack",
            ],
            "Value": [
                params.implied_consistent_peg,
                params.money_market_gap,
                attack_time(params),
                mechanical_exhaustion_time(params),
                result.reserves_before_attack,
            ],
        },
        width="stretch",
    )
