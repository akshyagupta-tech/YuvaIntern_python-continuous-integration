"""
Enterprise Computational & Quantitative Finance Engine
Author: Akshya Gupta (YuvaIntern Junior Python Developer Track - Week 6)
Engineered for static typing, coverage enforcement, and CI validation.
"""

from __future__ import annotations
import math
from typing import List, Union, Dict

Number = Union[int, float]


class ComputationError(ValueError):
    """Raised when arithmetic inputs are invalid."""


class QuantitativeEngine:
    @staticmethod
    def add(a: Number, b: Number) -> Number:
        return a + b

    @staticmethod
    def subtract(a: Number, b: Number) -> Number:
        return a - b

    @staticmethod
    def multiply(a: Number, b: Number) -> Number:
        return a * b

    @staticmethod
    def divide(a: Number, b: Number) -> float:
        if b == 0:
            raise ComputationError(
                "ZeroDivisionError: Denominator cannot be zero."
            )
        return a / b

    @staticmethod
    def calculate_compound_interest(
        principal: float,
        annual_rate_pct: float,
        years: int,
        compounds_per_year: int = 1,
    ) -> float:
        """Calculates compound interest: A = P(1 + r/n)^(nt) - P."""
        if (
            principal <= 0
            or annual_rate_pct < 0
            or years < 0
            or compounds_per_year <= 0
        ):
            raise ComputationError(
                "Financial values must be non-negative and frequency positive."
            )
        rate_decimal = annual_rate_pct / 100.0
        amount = principal * math.pow(
            (1 + (rate_decimal / compounds_per_year)),
            (compounds_per_year * years),
        )
        return round(amount - principal, 2)

    @staticmethod
    def compute_dataset_variance(series: List[Number]) -> Dict[str, float]:
        """Calculate mean, sample variance, and standard deviation."""
        if not isinstance(series, list) or len(series) < 2:
            raise ComputationError(
                "Variance requires a list containing at least two values."
            )

        for val in series:
            if not isinstance(val, (int, float)):
                raise ComputationError(
                    "Unsupported data type in numeric sequence: "
                    f"{type(val).__name__}"
                )

        n = len(series)
        mean_val = sum(series) / n
        squared_diff_sum = sum((x - mean_val) ** 2 for x in series)
        variance = squared_diff_sum / (n - 1)
        std_dev = math.sqrt(variance)

        return {
            "mean": round(mean_val, 4),
            "variance": round(variance, 4),
            "std_deviation": round(std_dev, 4),
        }
