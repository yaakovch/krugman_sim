"""Plotly figure builders shared by the app and notebook."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .model import (
    CrisisParams,
    attack_time,
    crisis_timing_for_credit_growth,
    mechanical_exhaustion_time,
)
from .simulate import DeterministicResult, MonteCarloResult, deterministic_simulation


PLOT_TEMPLATE = "plotly_white"
COLOR_CREDIT = "#1f6f8b"
COLOR_RESERVES = "#3a7d44"
COLOR_ATTACK = "#b42318"
COLOR_MECH = "#8a6f2a"
COLOR_SHADOW = "#7a3e9d"
COLOR_PEG = "#172026"


def _base_layout(fig: go.Figure, title: str, x_title: str = "Time") -> go.Figure:
    fig.update_layout(
        title=title,
        template=PLOT_TEMPLATE,
        hovermode="x unified",
        margin=dict(l=48, r=24, t=64, b=48),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title=x_title, zeroline=False)
    fig.update_yaxes(zeroline=False)
    return fig


def _add_event_lines(fig: go.Figure, result: DeterministicResult) -> None:
    attack = result.analytical_attack_time
    mechanical = result.mechanical_exhaustion_time
    if 0 <= attack <= result.params.horizon:
        fig.add_vline(
            attack,
            line_color=COLOR_ATTACK,
            line_dash="dash",
            annotation_text="attack",
            annotation_position="top left",
        )
    if 0 <= mechanical <= result.params.horizon:
        fig.add_vline(
            mechanical,
            line_color=COLOR_MECH,
            line_dash="dot",
            annotation_text="mechanical exhaustion",
            annotation_position="top right",
        )


def domestic_credit_figure(result: DeterministicResult) -> go.Figure:
    df = result.data
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["domestic_credit"],
            mode="lines",
            name="Domestic credit",
            line=dict(color=COLOR_CREDIT, width=3),
        )
    )
    _add_event_lines(fig, result)
    return _base_layout(fig, "Domestic Credit Path").update_yaxes(title="D(t)")


def reserves_figure(result: DeterministicResult) -> go.Figure:
    df = result.data
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["mechanical_reserves"],
            mode="lines",
            name="Mechanical reserves",
            line=dict(color=COLOR_MECH, dash="dot", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["actual_reserves"],
            mode="lines",
            name="Actual reserves",
            line=dict(color=COLOR_RESERVES, width=3),
        )
    )
    attack = result.analytical_attack_time
    if 0 <= attack <= result.params.horizon:
        fig.add_trace(
            go.Scatter(
                x=[attack],
                y=[result.reserves_before_attack],
                mode="markers",
                name="Reserves just before attack",
                marker=dict(color=COLOR_ATTACK, size=10, symbol="circle"),
            )
        )
    _add_event_lines(fig, result)
    return _base_layout(fig, "Foreign-Exchange Reserves").update_yaxes(title="R(t)")


def shadow_rate_figure(result: DeterministicResult) -> go.Figure:
    df = result.data
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["shadow_exchange_rate"],
            mode="lines",
            name="Shadow float",
            line=dict(color=COLOR_SHADOW, width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["fixed_peg"],
            mode="lines",
            name="Peg",
            line=dict(color=COLOR_PEG, width=2),
        )
    )
    _add_event_lines(fig, result)
    return _base_layout(fig, "Shadow Exchange Rate vs Peg").update_yaxes(title="Exchange rate")


def actual_exchange_rate_figure(result: DeterministicResult) -> go.Figure:
    df = result.data
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["actual_exchange_rate"],
            mode="lines",
            name="Actual exchange rate",
            line=dict(color=COLOR_ATTACK, width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["shadow_exchange_rate"],
            mode="lines",
            name="Shadow after collapse",
            line=dict(color=COLOR_SHADOW, dash="dash", width=2),
        )
    )
    _add_event_lines(fig, result)
    return _base_layout(fig, "Actual Exchange Rate Before and After Collapse").update_yaxes(
        title="Exchange rate"
    )


def core_figures(result: DeterministicResult) -> dict[str, go.Figure]:
    return {
        "domestic_credit": domestic_credit_figure(result),
        "reserves": reserves_figure(result),
        "shadow_rate": shadow_rate_figure(result),
        "actual_exchange_rate": actual_exchange_rate_figure(result),
    }


def crisis_timing_curve_figure(
    params: CrisisParams, min_growth: float = 0.5, max_growth: float = 8.0, points: int = 120
) -> go.Figure:
    growth_values = np.linspace(min_growth, max_growth, points)
    attack_values = crisis_timing_for_credit_growth(params, growth_values)
    mechanical_values = params.reserves0 / growth_values
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=growth_values,
            y=attack_values,
            mode="lines",
            name="Rational attack",
            line=dict(color=COLOR_ATTACK, width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=growth_values,
            y=mechanical_values,
            mode="lines",
            name="Mechanical exhaustion",
            line=dict(color=COLOR_MECH, width=2, dash="dot"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[params.credit_growth],
            y=[attack_time(params)],
            mode="markers",
            name="Current setting",
            marker=dict(color=COLOR_PEG, size=10),
        )
    )
    _base_layout(fig, "Crisis Timing as Domestic Credit Growth Changes", x_title="Credit growth mu")
    fig.update_yaxes(title="Time")
    return fig


def mechanical_vs_attack_figure(result: DeterministicResult) -> go.Figure:
    params = result.params
    attack = result.analytical_attack_time
    mechanical = result.mechanical_exhaustion_time
    gap = mechanical - attack
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=["Rational attack", "Mechanical exhaustion"],
            y=[attack, mechanical],
            marker_color=[COLOR_ATTACK, COLOR_MECH],
            text=[f"{attack:.2f}", f"{mechanical:.2f}"],
            textposition="outside",
            name="Timing",
        )
    )
    fig.add_annotation(
        x=0.5,
        y=max(attack, mechanical),
        text=f"Lead time: {gap:.2f} periods",
        showarrow=False,
        yshift=28,
    )
    fig.update_layout(template=PLOT_TEMPLATE, margin=dict(l=48, r=24, t=64, b=48), showlegend=False)
    fig.update_yaxes(title="Time", range=[0, max(mechanical * 1.2, 1)])
    fig.update_xaxes(title="")
    fig.update_layout(title="Rational Attack vs Mechanical Exhaustion")
    if params.is_money_market_consistent:
        fig.add_annotation(
            x=0.5,
            y=max(attack, mechanical) * 0.55,
            text=f"With a consistent peg, the gap equals alpha = {params.alpha:.2f}.",
            showarrow=False,
        )
    return fig


def sensitivity_sweep_figure(
    params: CrisisParams,
    parameter: str = "alpha",
    low: float | None = None,
    high: float | None = None,
    points: int = 100,
) -> go.Figure:
    labels = {
        "alpha": "Interest semi-elasticity alpha",
        "credit_growth": "Credit growth mu",
        "reserves0": "Initial reserves R0",
        "domestic_credit0": "Initial domestic credit D0",
        "foreign_rate": "Foreign interest rate i*",
        "peg": "Fixed peg sbar",
    }
    current = float(getattr(params, parameter))
    if low is None:
        low = max(0.01, current * 0.4) if current > 0 else -0.05
    if high is None:
        high = current * 1.8 + 0.01 if current > 0 else 0.15
    values = np.linspace(low, high, points)
    attack_values: list[float] = []
    mechanical_values: list[float] = []
    for value in values:
        updated = params.with_updates(**{parameter: float(value)})
        if parameter in {"domestic_credit0", "reserves0", "alpha", "foreign_rate"} and params.is_money_market_consistent:
            updated = updated.with_consistent_peg()
        attack_values.append(attack_time(updated))
        mechanical_values.append(mechanical_exhaustion_time(updated))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=values,
            y=attack_values,
            mode="lines",
            name="Rational attack",
            line=dict(color=COLOR_ATTACK, width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=values,
            y=mechanical_values,
            mode="lines",
            name="Mechanical exhaustion",
            line=dict(color=COLOR_MECH, width=2, dash="dot"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[current],
            y=[attack_time(params)],
            mode="markers",
            name="Current setting",
            marker=dict(color=COLOR_PEG, size=10),
        )
    )
    _base_layout(fig, f"Sensitivity Sweep: {labels.get(parameter, parameter)}", labels.get(parameter, parameter))
    fig.update_yaxes(title="Time")
    return fig


def monte_carlo_histogram_figure(result: MonteCarloResult) -> go.Figure:
    observed = result.crisis_times[~np.isnan(result.crisis_times)]
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=observed,
            nbinsx=40,
            marker_color=COLOR_CREDIT,
            opacity=0.85,
            name="Crisis times",
        )
    )
    deterministic = attack_time(result.params)
    fig.add_vline(
        deterministic,
        line_color=COLOR_ATTACK,
        line_dash="dash",
        annotation_text="deterministic",
        annotation_position="top",
    )
    _base_layout(fig, "Monte Carlo Distribution of Crisis Times", "Crisis time")
    fig.update_yaxes(title="Paths")
    return fig


def monte_carlo_paths_figure(result: MonteCarloResult) -> go.Figure:
    fig = go.Figure()
    for path_id, path_df in result.paths.groupby("path"):
        fig.add_trace(
            go.Scatter(
                x=path_df["time"],
                y=path_df["shadow_exchange_rate"],
                mode="lines",
                name=f"path {path_id}",
                line=dict(color="rgba(31,111,139,0.24)", width=1),
                showlegend=False,
            )
        )
    fig.add_hline(result.params.peg, line_color=COLOR_PEG, line_width=2, annotation_text="peg")
    _base_layout(fig, "Sample Stochastic Shadow-Rate Paths")
    fig.update_yaxes(title="Shadow exchange rate")
    return fig


def all_analysis_figures(result: DeterministicResult) -> dict[str, go.Figure]:
    figures = core_figures(result)
    figures["crisis_timing_curve"] = crisis_timing_curve_figure(result.params)
    figures["mechanical_vs_attack"] = mechanical_vs_attack_figure(result)
    figures["sensitivity_alpha"] = sensitivity_sweep_figure(result.params, parameter="alpha")
    return figures


def build_result_from_params(params: CrisisParams) -> DeterministicResult:
    return deterministic_simulation(params)
