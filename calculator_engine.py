"""
High-Precision Financial & Computational Engine
Author: Akshya Gupta (YuvaIntern Junior Python Developer Track - Week 6)
Targeted for automated CI/CD pipeline integration and strict static analysis.
"""

from typing import List, Union

Number = Union[int, float]

class ComputationError(ValueError):
    """Domain exception raised upon invalid computational input."""

class CalculatorEngine:
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
            raise ComputationError("Division by zero is strictly prohibited.")
        return a / b

    @staticmethod
    def calculate_compound_interest(principal: float, rate: float, time_years: int) -> float:
        """Calculates compound interest: A = P(1 + r/n)^(nt) where n=1."""
        if principal <= 0 or rate < 0 or time_years < 0:
            raise ComputationError("Financial variables must be non-negative values.")
        amount = principal * ((1 + (rate / 100)) ** time_years)
        return round(amount - principal, 2)

    @staticmethod
    def batch_sum(values: List[Number]) -> Number:
        if not isinstance(values, list):
            raise ComputationError("Expected list container for batch summation.")
        return sum(values)
