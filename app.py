"""Streamlit dashboard for quantitative analytics and pipeline health."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
import streamlit as st

from quant_engine import ComputationError, QuantitativeEngine
from telemetry import build_metadata, health_check

REPOSITORY = "akshyagupta-tech/YuvaIntern_python-continuous-integration"
WORKFLOW_URL = f"https://github.com/{REPOSITORY}/actions/workflows/ci.yml"
BADGE_URL = f"{WORKFLOW_URL}/badge.svg"


def _parse_series(raw_values: str) -> list[Decimal]:
    """Parse comma-separated observations without a float conversion."""
    if not raw_values.strip():
        return []
    try:
        values = [Decimal(token.strip()) for token in raw_values.split(",")]
    except InvalidOperation as error:
        raise ComputationError(
            "Enter comma-separated decimal values."
        ) from error
    if any(not value.is_finite() for value in values):
        raise ComputationError("All observations must be finite decimals.")
    return values


st.set_page_config(
    page_title=("Automated Quantitative Engine & DevSecOps " "CI/CD Suite"),
    layout="wide",
)
st.title("Automated Quantitative Engine & DevSecOps CI/CD Suite")
st.markdown(f"[![CI status]({BADGE_URL})]({WORKFLOW_URL})")

calculator_tab, analytics_tab, pipeline_tab = st.tabs(
    ("Financial calculator", "Return-series analytics", "CI/CD telemetry")
)

with calculator_tab:
    control_column, chart_column = st.columns([1, 2], gap="large")
    with control_column:
        principal = st.number_input(
            "Principal amount",
            min_value=0.01,
            value=10_000.0,
            step=500.0,
        )
        annual_rate = st.number_input(
            "Annual rate (%)",
            min_value=0.0,
            value=7.5,
            step=0.25,
        )
        years = st.slider("Investment horizon (years)", 0, 40, 10)
        compounding = st.select_slider(
            "Compounds per year",
            options=(1, 2, 4, 12, 365),
            value=12,
        )
        try:
            interest = QuantitativeEngine.calculate_compound_interest(
                Decimal(str(principal)),
                Decimal(str(annual_rate)),
                years,
                compounding,
            )
        except ComputationError as error:
            st.error(str(error))
            interest = Decimal(0)
        st.metric("Accrued interest", f"{interest:,.2f}")
        balance = Decimal(str(principal)) + interest
        st.metric("Projected balance", f"{balance:,.2f}")

    with chart_column:
        projection_rows: list[dict[str, Any]] = []
        for year in range(years + 1):
            accrued = QuantitativeEngine.calculate_compound_interest(
                Decimal(str(principal)),
                Decimal(str(annual_rate)),
                year,
                compounding,
            )
            projection_rows.append(
                {
                    "Year": year,
                    "Balance": float(Decimal(str(principal)) + accrued),
                }
            )
        projection_frame = pd.DataFrame(projection_rows).set_index("Year")
        st.line_chart(projection_frame, y="Balance")
        st.download_button(
            "Export projection CSV",
            data=projection_frame.to_csv(),
            file_name="compound-interest-projection.csv",
            mime="text/csv",
        )

with analytics_tab:
    input_column, results_column = st.columns([1, 2], gap="large")
    with input_column:
        raw_returns = st.text_area(
            "Periodic returns",
            value="0.012, -0.004, 0.019, 0.008, 0.011, -0.006, 0.015",
            height=130,
        )
        window = st.number_input(
            "Moving-average window",
            min_value=1,
            max_value=100,
            value=3,
            step=1,
        )
        risk_free_rate = st.number_input(
            "Risk-free rate per period",
            value=0.0,
            step=0.001,
            format="%.4f",
        )

    try:
        returns = _parse_series(raw_returns)
        summary = QuantitativeEngine.analyze_series(returns, int(window))
    except ComputationError as error:
        st.error(str(error))
    else:
        with results_column:
            metrics_left, metrics_right = st.columns(2)
            metrics_left.metric("Observations", summary["count"])
            metrics_right.metric("Mean return", str(summary["mean"]))
            st.dataframe(
                {
                    "Period": list(range(1, len(returns) + 1)),
                    "Return": [float(value) for value in returns],
                },
                use_container_width=True,
                hide_index=True,
            )
            if returns:
                plot_rows = [
                    {
                        "Window end": index + int(window),
                        "Moving average": float(value),
                    }
                    for index, value in enumerate(summary["moving_average"])
                ]
                st.line_chart(pd.DataFrame(plot_rows).set_index("Window end"))
            try:
                sharpe = QuantitativeEngine.risk_adjusted_return(
                    returns,
                    Decimal(str(risk_free_rate)),
                    periods_per_year=252,
                )
            except ComputationError as error:
                st.warning(str(error))
            else:
                st.metric("Annualized risk-adjusted return", f"{sharpe:.4f}")
            st.write(
                "Detected outliers",
                [str(value) for value in summary["outliers"]],
            )
            export_column, json_column = st.columns(2)
            export_column.download_button(
                "Export metrics CSV",
                data=QuantitativeEngine.export_csv(summary),
                file_name="quantitative-summary.csv",
                mime="text/csv",
                use_container_width=True,
            )
            json_column.download_button(
                "Export metrics JSON",
                data=QuantitativeEngine.export_json(summary),
                file_name="quantitative-summary.json",
                mime="application/json",
                use_container_width=True,
            )

with pipeline_tab:
    health = health_check()
    status_column, metadata_column = st.columns([1, 2], gap="large")
    with status_column:
        st.metric("Engine health", health["status"].title())
        st.json(health["checks"])
    with metadata_column:
        st.subheader("Build metadata")
        st.json(build_metadata())
    st.subheader("Automated delivery path")
    st.graphviz_chart("""
        digraph pipeline {
            rankdir=LR;
            node [shape=box, style=rounded];
            source -> lint -> types -> sast -> tests -> coverage -> artifact;
            lint [label="Flake8\nPython 3.10-3.12"];
            types [label="Strict mypy"];
            sast [label="Bandit + pip-audit"];
            tests [label="unittest matrix"];
            coverage [label="Coverage >= 90%"];
            artifact [label="Reports + wheel"];
        }
        """)
    st.link_button("Open latest GitHub Actions run", WORKFLOW_URL)
