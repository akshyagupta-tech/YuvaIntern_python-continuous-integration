"""
Automated Test Suite for Quantitative Engine
Author: Akshya Gupta
Covers boundary assertions, exceptions, and coverage targets for CI integration.
"""

import unittest
from calculator_engine import QuantitativeEngine, ComputationError

class TestQuantitativeEngine(unittest.TestCase):

    def test_basic_arithmetic(self):
        self.assertEqual(QuantitativeEngine.add(10, 5), 15)
        self.assertEqual(QuantitativeEngine.subtract(10, 5), 5)
        self.assertEqual(QuantitativeEngine.multiply(4, 5), 20)
        self.assertEqual(QuantitativeEngine.divide(20, 4), 5.0)

    def test_divide_by_zero_exception(self):
        with self.assertRaises(ComputationError):
            QuantitativeEngine.divide(10, 0)

    def test_compound_interest_annual(self):
        interest = QuantitativeEngine.calculate_compound_interest(1000.0, 5.0, 2, 1)
        self.assertEqual(interest, 102.50)

    def test_compound_interest_quarterly(self):
        interest = QuantitativeEngine.calculate_compound_interest(1000.0, 5.0, 2, 4)
        self.assertEqual(interest, 104.49)

    def test_compound_interest_invalid_arguments(self):
        with self.assertRaises(ComputationError):
            QuantitativeEngine.calculate_compound_interest(-1000.0, 5.0, 2)
        with self.assertRaises(ComputationError):
            QuantitativeEngine.calculate_compound_interest(1000.0, 5.0, 2, compounds_per_year=0)

    def test_dataset_variance_nominal(self):
        dataset = [10.0, 12.0, 23.0, 23.0, 16.0, 23.0, 21.0, 16.0]
        stats = QuantitativeEngine.compute_dataset_variance(dataset)
        self.assertEqual(stats["mean"], 18.0)
        self.assertEqual(stats["variance"], 27.4286)
        self.assertEqual(stats["std_deviation"], 5.2372)

    def test_dataset_variance_edge_cases(self):
        with self.assertRaises(ComputationError):
            QuantitativeEngine.compute_dataset_variance([10.0])
        with self.assertRaises(ComputationError):
            QuantitativeEngine.compute_dataset_variance([10.0, "corrupted", 30.0])

if __name__ == "__main__":
    unittest.main()
