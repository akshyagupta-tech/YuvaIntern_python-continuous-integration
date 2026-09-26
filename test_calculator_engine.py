"""
Automated CI Regression Test Suite
Author: Akshya Gupta
Covers boundary assertions and error conditions for CalculatorEngine.
"""

import unittest
from calculator_engine import CalculatorEngine, ComputationError

class TestCalculatorEngine(unittest.TestCase):

    def test_basic_arithmetic(self):
        self.assertEqual(CalculatorEngine.add(10, 5), 15)
        self.assertEqual(CalculatorEngine.subtract(10, 5), 5)
        self.assertEqual(CalculatorEngine.multiply(4, 5), 20)
        self.assertEqual(CalculatorEngine.divide(20, 4), 5.0)

    def test_division_by_zero_exception(self):
        with self.assertRaises(ComputationError):
            CalculatorEngine.divide(100, 0)

    def test_compound_interest_calculation(self):
        interest = CalculatorEngine.calculate_compound_interest(1000.0, 5.0, 2)
        self.assertEqual(interest, 102.50)

    def test_compound_interest_invalid_arguments(self):
        with self.assertRaises(ComputationError):
            CalculatorEngine.calculate_compound_interest(-500.0, 5.0, 2)

    def test_batch_sum(self):
        self.assertEqual(CalculatorEngine.batch_sum([10, 20.5, 30]), 60.5)
        self.assertEqual(CalculatorEngine.batch_sum([]), 0)

    def test_batch_sum_invalid_type(self):
        with self.assertRaises(ComputationError):
            CalculatorEngine.batch_sum("not-a-list")

if __name__ == "__main__":
    unittest.main()
