"""Quantitative calculations and local CI pipeline utilities."""

from __future__ import annotations

import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

Number = Union[int, float]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
GITHUB_REPOSITORY = "akshyagupta-tech/YuvaIntern_python-security-enhancements"
GITHUB_WORKFLOW = "ci.yml"


class ComputationError(ValueError):
    """Raised when input values violate a computation's domain."""


@dataclass(frozen=True)
class PipelineResult:
    """Capture the result of one fixed local CI command."""

    name: str
    command: Tuple[str, ...]
    return_code: int
    output: str


class QuantitativeEngine:
    """Provide validated arithmetic, finance, and sample statistics."""

    @staticmethod
    def _validate_number(value: object, name: str) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ComputationError(f"{name} must be an integer or float.")
        try:
            is_finite = math.isfinite(value)
        except OverflowError as error:
            raise ComputationError(
                f"{name} is outside the supported range."
            ) from error
        if not is_finite:
            raise ComputationError(f"{name} must be finite.")

    @classmethod
    def add(cls, a: Number, b: Number) -> Number:
        cls._validate_number(a, "First operand")
        cls._validate_number(b, "Second operand")
        return a + b

    @classmethod
    def subtract(cls, a: Number, b: Number) -> Number:
        cls._validate_number(a, "First operand")
        cls._validate_number(b, "Second operand")
        return a - b

    @classmethod
    def multiply(cls, a: Number, b: Number) -> Number:
        cls._validate_number(a, "First operand")
        cls._validate_number(b, "Second operand")
        return a * b

    @classmethod
    def divide(cls, a: Number, b: Number) -> float:
        cls._validate_number(a, "Numerator")
        cls._validate_number(b, "Denominator")
        if b == 0:
            raise ComputationError("Cannot divide by zero.")
        return a / b

    @classmethod
    def calculate_compound_interest(
        cls,
        principal: float,
        annual_rate_pct: float,
        years: int,
        compounds_per_year: int = 1,
    ) -> float:
        """Return compound interest earned, rounded to two decimal places."""
        cls._validate_number(principal, "Principal")
        cls._validate_number(annual_rate_pct, "Annual rate")
        if principal <= 0 or annual_rate_pct < 0:
            raise ComputationError(
                "Principal must be positive and annual rate non-negative."
            )
        if isinstance(years, bool) or not isinstance(years, int) or years < 0:
            raise ComputationError("Years must be a non-negative integer.")
        if (
            isinstance(compounds_per_year, bool)
            or not isinstance(compounds_per_year, int)
            or compounds_per_year < 1
        ):
            raise ComputationError(
                "Compounds per year must be a positive integer."
            )

        rate = annual_rate_pct / 100
        try:
            amount = principal * math.pow(
                1 + rate / compounds_per_year,
                compounds_per_year * years,
            )
        except OverflowError as error:
            raise ComputationError(
                "Compound interest exceeds the supported range."
            ) from error
        return round(amount - principal, 2)

    @classmethod
    def compute_dataset_variance(
        cls,
        series: List[Number],
    ) -> Dict[str, float]:
        """Return the mean, sample variance, and sample standard deviation."""
        if not isinstance(series, list) or len(series) < 2:
            raise ComputationError(
                "Variance requires a list with at least two numeric values."
            )
        for value in series:
            cls._validate_number(value, "Dataset value")

        try:
            mean = math.fsum(series) / len(series)
            squared_deviations = math.fsum(
                (value - mean) ** 2 for value in series
            )
            variance = squared_deviations / (len(series) - 1)
            std_dev = math.sqrt(variance)
        except (OverflowError, ValueError) as error:
            raise ComputationError(
                "Dataset exceeds the supported range."
            ) from error

        return {
            "mean": round(mean, 4),
            "variance": round(variance, 4),
            "std_dev": round(std_dev, 4),
        }


def _decode_output(output: Optional[Union[str, bytes]]) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output


def run_local_pipeline(
    progress_callback: Optional[Callable[[PipelineResult], None]] = None,
) -> List[PipelineResult]:
    """Run fixed CI checks locally without shell expansion or user commands."""
    commands = (
        (
            "Flake8",
            (
                sys.executable,
                "-m",
                "flake8",
                "core/week6_ci.py",
                "tests/test_week6.py",
            ),
        ),
        (
            "Bandit",
            (sys.executable, "-m", "bandit", "-r", "core/week6_ci.py", "-ll"),
        ),
        (
            "Unit tests and coverage",
            (
                sys.executable,
                "-m",
                "coverage",
                "run",
                "--source=core.week6_ci",
                "-m",
                "unittest",
                "discover",
                "-s",
                ".",
                "-p",
                "test_*.py",
            ),
        ),
        (
            "Coverage gate",
            (
                sys.executable,
                "-m",
                "coverage",
                "report",
                "--fail-under=90",
                "-m",
            ),
        ),
    )
    results: List[PipelineResult] = []
    for name, command in commands:
        try:
            completed = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=300,
            )
            output = "\n".join(
                text for text in (completed.stdout, completed.stderr) if text
            ).strip()
            result = PipelineResult(
                name=name,
                command=command,
                return_code=completed.returncode,
                output=output,
            )
        except subprocess.TimeoutExpired as error:
            output = "\n".join(
                text
                for text in (
                    _decode_output(error.stdout),
                    _decode_output(error.stderr),
                    "Command timed out.",
                )
                if text
            )
            result = PipelineResult(name, command, 124, output)
        except OSError as error:
            result = PipelineResult(name, command, 127, str(error))

        results.append(result)
        if progress_callback is not None:
            progress_callback(result)
        if result.return_code != 0:
            break
    return results


def _run_streamlit_dashboard() -> None:  # pragma: no cover
    """Render CI status, workflow source, and the local pipeline runner."""
    import streamlit as st

    st.title("Week 6 CI Dashboard")
    status_tab, config_tab, runner_tab = st.tabs(
        ("Actions status", "CI configuration", "Run locally")
    )

    with status_tab:
        badge_url = (
            f"https://github.com/{GITHUB_REPOSITORY}/actions/workflows/"
            f"{GITHUB_WORKFLOW}/badge.svg"
        )
        actions_url = (
            f"https://github.com/{GITHUB_REPOSITORY}/actions/workflows/"
            f"{GITHUB_WORKFLOW}"
        )
        st.markdown(f"[![GitHub Actions status]({badge_url})]({actions_url})")
        st.link_button("Open GitHub Actions", actions_url)
        st.caption(
            "If the badge is blocked, use the Actions link for the latest run."
        )

    with config_tab:
        try:
            configuration = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
        except OSError as error:
            st.error(f"Unable to read CI configuration: {error}")
        else:
            st.code(configuration, language="yaml")

    with runner_tab:
        log_area = st.empty()
        status_area = st.status("Pipeline ready", expanded=True)
        if st.button("Run local CI pipeline"):
            outputs: List[str] = []

            def show_progress(result: PipelineResult) -> None:
                state = "passed" if result.return_code == 0 else "failed"
                outputs.append(f"{result.name}: {state}\n{result.output}")
                log_area.code("\n\n".join(outputs))

            results = run_local_pipeline(show_progress)
            if results and all(result.return_code == 0 for result in results):
                status_area.update(label="Pipeline passed", state="complete")
            else:
                status_area.update(label="Pipeline failed", state="error")


if __name__ == "__main__":  # pragma: no cover
    _run_streamlit_dashboard()
