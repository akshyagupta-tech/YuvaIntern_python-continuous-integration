"""Deterministic quantitative analytics using decimal arithmetic."""

from __future__ import annotations

import csv
import io
import json
import math
from decimal import Decimal, InvalidOperation, localcontext
from statistics import median
from typing import Any, Sequence, TypeAlias

Number: TypeAlias = int | float | Decimal


class ComputationError(ValueError):
    """Raised when input values violate a quantitative operation's domain."""


class QuantitativeEngine:
    """Provide validated Decimal arithmetic, risk statistics, and matrices."""

    @staticmethod
    def _decimal(value: object, name: str = "value") -> Decimal:
        if isinstance(value, bool) or not isinstance(
            value, (int, float, Decimal)
        ):
            raise ComputationError(f"{name} must be a finite numeric value.")
        if isinstance(value, float) and not math.isfinite(value):
            raise ComputationError(f"{name} must be finite.")
        try:
            result = (
                value if isinstance(value, Decimal) else Decimal(str(value))
            )
        except (InvalidOperation, ValueError, OverflowError) as error:
            raise ComputationError(
                f"{name} is outside the supported range."
            ) from error
        if not result.is_finite():
            raise ComputationError(f"{name} must be finite.")
        return result

    @classmethod
    def add(cls, left: Number, right: Number) -> Decimal:
        return cls._decimal(left, "left operand") + cls._decimal(
            right, "right operand"
        )

    @classmethod
    def subtract(cls, left: Number, right: Number) -> Decimal:
        return cls._decimal(left, "left operand") - cls._decimal(
            right, "right operand"
        )

    @classmethod
    def multiply(cls, left: Number, right: Number) -> Decimal:
        return cls._decimal(left, "left operand") * cls._decimal(
            right, "right operand"
        )

    @classmethod
    def divide(cls, numerator: Number, denominator: Number) -> Decimal:
        top = cls._decimal(numerator, "numerator")
        bottom = cls._decimal(denominator, "denominator")
        if bottom == 0:
            raise ComputationError("Cannot divide by zero.")
        return top / bottom

    @staticmethod
    def approximately_equal(
        left: Number,
        right: Number,
        *,
        relative_tolerance: float = 1e-12,
        absolute_tolerance: float = 1e-12,
    ) -> bool:
        """Compare values using explicit tolerances at a float boundary."""
        left_decimal = QuantitativeEngine._decimal(left, "left value")
        right_decimal = QuantitativeEngine._decimal(right, "right value")
        if relative_tolerance < 0 or absolute_tolerance < 0:
            raise ComputationError(
                "Comparison tolerances must be non-negative."
            )
        try:
            left_float = float(left_decimal)
            right_float = float(right_decimal)
            if not math.isfinite(left_float) or not math.isfinite(right_float):
                return left_decimal == right_decimal
            return math.isclose(
                left_float,
                right_float,
                rel_tol=relative_tolerance,
                abs_tol=absolute_tolerance,
            )
        except OverflowError:
            return left_decimal == right_decimal

    @classmethod
    def mean(cls, values: Sequence[Number]) -> Decimal:
        decimals = cls._series(values, minimum=1)
        return sum(decimals, Decimal(0)) / Decimal(len(decimals))

    @classmethod
    def compute_dataset_variance(
        cls,
        values: Sequence[Number],
    ) -> dict[str, Decimal]:
        """Return mean, sample variance, and sample standard deviation."""
        decimals = cls._series(values, minimum=2)
        average = sum(decimals, Decimal(0)) / Decimal(len(decimals))
        squared_differences = sum(
            ((value - average) ** 2 for value in decimals), Decimal(0)
        )
        variance = squared_differences / Decimal(len(decimals) - 1)
        return {
            "mean": average,
            "variance": variance,
            "std_dev": variance.sqrt(),
        }

    @classmethod
    def calculate_compound_interest(
        cls,
        principal: Number,
        annual_rate_percent: Number,
        years: int,
        compounds_per_year: int = 1,
    ) -> Decimal:
        """Calculate compound interest without binary floating-point drift."""
        amount = cls._decimal(principal, "principal")
        rate = cls._decimal(annual_rate_percent, "annual rate")
        if amount <= 0 or rate < 0:
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
        rate_per_period = rate / Decimal(100 * compounds_per_year)
        exponent = compounds_per_year * years
        try:
            with localcontext() as context:
                context.prec = 40
                total = amount * (Decimal(1) + rate_per_period) ** exponent
                return (total - amount).quantize(Decimal("0.01"))
        except (InvalidOperation, OverflowError) as error:
            raise ComputationError(
                "Compound interest exceeds the supported range."
            ) from error

    @classmethod
    def rolling_mean(
        cls,
        values: Sequence[Number],
        window: int,
    ) -> list[Decimal]:
        """Calculate simple rolling means using a Decimal sliding sum."""
        decimals = cls._series(values, minimum=0)
        if (
            isinstance(window, bool)
            or not isinstance(window, int)
            or window < 1
        ):
            raise ComputationError("Window must be a positive integer.")
        if not decimals:
            return []
        if window > len(decimals):
            raise ComputationError("Window cannot exceed the series length.")
        running_sum = sum(decimals[:window], Decimal(0))
        result = [running_sum / Decimal(window)]
        for index in range(window, len(decimals)):
            running_sum += decimals[index] - decimals[index - window]
            result.append(running_sum / Decimal(window))
        return result

    @classmethod
    def moving_average(
        cls,
        values: Sequence[Number],
        window: int,
    ) -> list[Decimal]:
        """Alias for the rolling simple moving average calculation."""
        return cls.rolling_mean(values, window)

    @classmethod
    def risk_adjusted_return(
        cls,
        returns: Sequence[Number],
        risk_free_rate: Number = Decimal(0),
        periods_per_year: int = 1,
    ) -> Decimal:
        """Return an annualized Sharpe ratio over periodic simple returns."""
        decimals = cls._series(returns, minimum=2)
        if (
            isinstance(periods_per_year, bool)
            or not isinstance(periods_per_year, int)
            or periods_per_year < 1
        ):
            raise ComputationError(
                "Periods per year must be a positive integer."
            )
        risk_free = cls._decimal(risk_free_rate, "risk-free rate")
        excess_returns = [value - risk_free for value in decimals]
        average_excess = sum(excess_returns, Decimal(0)) / Decimal(
            len(excess_returns)
        )
        squared_differences = sum(
            ((value - average_excess) ** 2 for value in excess_returns),
            Decimal(0),
        )
        volatility = (
            squared_differences / Decimal(len(excess_returns) - 1)
        ).sqrt()
        if volatility == 0:
            raise ComputationError(
                "Risk-adjusted return is undefined for zero volatility."
            )
        return (average_excess / volatility) * Decimal(periods_per_year).sqrt()

    @classmethod
    def detect_outliers(
        cls,
        values: Sequence[Number],
        threshold: Number = Decimal("3.5"),
    ) -> list[Decimal]:
        """Detect value outliers with a median absolute deviation score."""
        decimals = cls._series(values, minimum=0)
        if not decimals:
            return []
        cutoff = cls._decimal(threshold, "outlier threshold")
        if cutoff <= 0:
            raise ComputationError("Outlier threshold must be positive.")
        center = Decimal(str(median(decimals)))
        deviations = [abs(value - center) for value in decimals]
        median_deviation = Decimal(str(median(deviations)))
        if median_deviation == 0:
            return [value for value in decimals if value != center]
        scale = Decimal("0.6744897501960817")
        return [
            value
            for value, deviation in zip(decimals, deviations, strict=True)
            if scale * deviation / median_deviation > cutoff
        ]

    @classmethod
    def transpose_matrix(
        cls,
        matrix: Sequence[Sequence[Number]],
    ) -> list[list[Decimal]]:
        """Return a validated rectangular matrix transpose."""
        rows = cls._matrix(matrix, "matrix")
        if not rows:
            return []
        return [list(column) for column in zip(*rows, strict=True)]

    @classmethod
    def multiply_matrices(
        cls,
        left: Sequence[Sequence[Number]],
        right: Sequence[Sequence[Number]],
    ) -> list[list[Decimal]]:
        """Multiply compatible rectangular matrices using Decimal sums."""
        left_rows = cls._matrix(left, "left matrix")
        right_rows = cls._matrix(right, "right matrix")
        if not left_rows or not right_rows:
            raise ComputationError(
                "Matrix multiplication requires non-empty matrices."
            )
        if len(left_rows[0]) != len(right_rows):
            raise ComputationError("Matrix dimensions are not compatible.")
        columns = list(zip(*right_rows, strict=True))
        return [
            [
                sum(
                    (
                        left_value * right_value
                        for left_value, right_value in zip(
                            row, column, strict=True
                        )
                    ),
                    Decimal(0),
                )
                for column in columns
            ]
            for row in left_rows
        ]

    @classmethod
    def analyze_series(
        cls,
        values: Sequence[Number],
        window: int = 1,
    ) -> dict[str, Any]:
        """Build a JSON/CSV-ready summary with optional rolling means."""
        decimals = cls._series(values, minimum=0)
        summary: dict[str, Any] = {
            "count": len(decimals),
            "mean": cls.mean(decimals) if decimals else Decimal(0),
            "outliers": cls.detect_outliers(decimals),
            "moving_average": cls.rolling_mean(decimals, window),
        }
        if len(decimals) >= 2:
            summary.update(cls.compute_dataset_variance(decimals))
        else:
            summary.update({"variance": Decimal(0), "std_dev": Decimal(0)})
        return summary

    @classmethod
    def export_json(cls, data: Any) -> str:
        """Serialize telemetry with fixed-point decimal strings."""
        return json.dumps(
            data, default=cls._json_default, indent=2, sort_keys=True
        )

    @staticmethod
    def _json_default(value: Any) -> Any:
        if isinstance(value, Decimal):
            return format(value, "f")
        raise TypeError(f"Unsupported JSON value: {type(value).__name__}")

    @classmethod
    def export_csv(cls, summary: dict[str, Any]) -> str:
        """Export summary metrics as deterministic metric/value CSV rows."""
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(("metric", "value"))
        for metric in sorted(summary):
            value = summary[metric]
            if isinstance(value, list):
                rendered = ";".join(cls._format_value(item) for item in value)
            else:
                rendered = cls._format_value(value)
            writer.writerow((metric, rendered))
        return output.getvalue()

    @classmethod
    def export_table(cls, summary: dict[str, Any]) -> str:
        """Render summary data in an aligned plain-text table."""
        rows = [
            (metric, cls._format_value(value))
            for metric, value in sorted(summary.items())
        ]
        if not rows:
            return "No metrics available."
        key_width = max(len("metric"), *(len(key) for key, _ in rows))
        value_width = max(len("value"), *(len(value) for _, value in rows))
        border = f"+{'-' * (key_width + 2)}+{'-' * (value_width + 2)}+"
        lines = [
            border,
            f"| {'metric'.ljust(key_width)} | {'value'.ljust(value_width)} |",
            border,
        ]
        lines.extend(
            f"| {key.ljust(key_width)} | {value.ljust(value_width)} |"
            for key, value in rows
        )
        lines.append(border)
        return "\n".join(lines)

    @staticmethod
    def _format_value(value: Any) -> str:
        if isinstance(value, Decimal):
            return format(value, "f")
        if isinstance(value, list):
            return ";".join(
                QuantitativeEngine._format_value(item) for item in value
            )
        return str(value)

    @classmethod
    def _series(
        cls,
        values: Sequence[Number],
        *,
        minimum: int,
    ) -> list[Decimal]:
        if isinstance(values, (str, bytes)) or not isinstance(
            values, Sequence
        ):
            raise ComputationError(
                "Series must be a sequence of numeric values."
            )
        if len(values) < minimum:
            raise ComputationError(
                f"Series requires at least {minimum} numeric value(s)."
            )
        return [
            cls._decimal(value, f"series[{index}]")
            for index, value in enumerate(values)
        ]

    @classmethod
    def _matrix(
        cls,
        matrix: Sequence[Sequence[Number]],
        name: str,
    ) -> list[list[Decimal]]:
        if isinstance(matrix, (str, bytes)) or not isinstance(
            matrix, Sequence
        ):
            raise ComputationError(f"{name} must be a sequence of rows.")
        rows: list[list[Decimal]] = []
        width: int | None = None
        for row_index, row in enumerate(matrix):
            if isinstance(row, (str, bytes)) or not isinstance(row, Sequence):
                raise ComputationError(f"{name} row {row_index} is invalid.")
            if width is None:
                width = len(row)
                if width == 0:
                    raise ComputationError(f"{name} rows cannot be empty.")
            elif len(row) != width:
                raise ComputationError(f"{name} must be rectangular.")
            rows.append(
                [
                    cls._decimal(value, f"{name}[{row_index}][{column_index}]")
                    for column_index, value in enumerate(row)
                ]
            )
        return rows


__all__ = ["ComputationError", "Number", "QuantitativeEngine"]
