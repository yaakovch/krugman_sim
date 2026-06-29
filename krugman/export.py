"""Export helpers for CSV, figure images, and a printable teaching handout."""

from __future__ import annotations

import base64
import html
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from .model import CrisisParams
from .simulate import DeterministicResult


ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
HANDOUT_TEMPLATE = ASSET_DIR / "handout_template.html"


def simulation_csv_bytes(result: DeterministicResult) -> bytes:
    return result.data.to_csv(index=False).encode("utf-8")


def monte_carlo_summary_csv_bytes(summary: pd.Series) -> bytes:
    return summary.to_frame("value").to_csv().encode("utf-8")


def figure_image_bytes(fig: go.Figure, fmt: str = "png", scale: int = 2) -> bytes:
    if fmt not in {"png", "svg"}:
        raise ValueError("fmt must be 'png' or 'svg'")
    return fig.to_image(format=fmt, scale=scale)


def render_handout_html(
    params: CrisisParams,
    result: DeterministicResult,
    figure: go.Figure | None = None,
) -> str:
    image_html = ""
    if figure is not None:
        try:
            image_bytes = figure_image_bytes(figure, fmt="png", scale=2)
            image_src = base64.b64encode(image_bytes).decode("ascii")
            image_html = f'<img class="chart" alt="Reserve crisis chart" src="data:image/png;base64,{image_src}" />'
        except Exception as exc:  # pragma: no cover - depends on local kaleido/browser setup
            image_html = (
                '<p class="note">Chart image export was unavailable in this environment: '
                f"{html.escape(str(exc))}</p>"
            )

    template = HANDOUT_TEMPLATE.read_text(encoding="utf-8")
    return template.format(
        domestic_credit0=params.domestic_credit0,
        reserves0=params.reserves0,
        credit_growth=params.credit_growth,
        alpha=params.alpha,
        peg=params.peg,
        foreign_rate=params.foreign_rate,
        attack_time=result.analytical_attack_time,
        mechanical_time=result.mechanical_exhaustion_time,
        reserves_attack=result.reserves_before_attack,
        lead_time=result.mechanical_exhaustion_time - result.analytical_attack_time,
        image_html=image_html,
    )
