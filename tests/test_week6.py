"""Precision, boundary, and pipeline tests for Week 6."""

import subprocess
import unittest
from unittest.mock import patch

from core.week6_ci import (
    ComputationError,
    QuantitativeEngine,
    run_local_pipeline,
)


class TestQuantitativeEngine(unittest.TestCase):
    def test_basic_arithmetic_and_precision(self) -> None:
        self.assertEqual(QuantitativeEngine.add(0.1, 0.2), 0.30000000000000004)
        self.assertEqual(QuantitativeEngine.subtract(10, 4), 6)
        self.assertEqual(QuantitativeEngine.multiply(-3, 4), -12)
        self.assertEqual(QuantitativeEngine.divide(1, 3), 1 / 3)

    def test_arithmetic_rejects_bad_types_and_zero_division(self) -> None:
        with self.assertRaises(ComputationError):
            QuantitativeEngine.add(True, 1)
        with self.assertRaises(ComputationError):
            QuantitativeEngine.divide(1, 0)
        with self.assertRaises(ComputationError):
            QuantitativeEngine.divide(float("nan"), 2)

    def test_compound_interest_annual_and_quarterly(self) -> None:
        self.assertEqual(
            QuantitativeEngine.calculate_compound_interest(1000, 5, 2),
            102.5,
        )
        self.assertEqual(
            QuantitativeEngine.calculate_compound_interest(1000, 5, 2, 4),
            104.49,
        )
        self.assertEqual(
            QuantitativeEngine.calculate_compound_interest(1000, 0, 3),
            0.0,
        )

    def test_compound_interest_rejects_invalid_boundaries(self) -> None:
        invalid_arguments = (
            (-1, 5, 2, 1),
            (1000, -1, 2, 1),
            (1000, 5, -1, 1),
            (1000, 5, 2, 0),
            (1000, float("inf"), 2, 1),
            (1000, 5, True, 1),
        )
        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ComputationError):
                    QuantitativeEngine.calculate_compound_interest(*arguments)

    def test_dataset_sample_statistics_and_rounding(self) -> None:
        result = QuantitativeEngine.compute_dataset_variance(
            [10, 12, 23, 23, 16, 23, 21, 16]
        )

        self.assertEqual(
            result,
            {"mean": 18.0, "variance": 27.4286, "std_dev": 5.2372},
        )

    def test_dataset_variance_rejects_invalid_boundaries(self) -> None:
        invalid_series = ([], [1], (1, 2), [1, "two"], [1, float("nan")])
        for series in invalid_series:
            with self.subTest(series=series):
                with self.assertRaises(ComputationError):
                    QuantitativeEngine.compute_dataset_variance(series)

    def test_pipeline_runs_fixed_commands_and_reports_progress(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="passed",
            stderr="",
        )
        progress = []
        with patch(
            "core.week6_ci.subprocess.run",
            return_value=completed,
        ) as run:
            results = run_local_pipeline(progress.append)

        self.assertEqual(len(results), 4)
        self.assertEqual(progress, results)
        self.assertTrue(all(result.return_code == 0 for result in results))
        self.assertIn("core/week6_ci.py", results[0].command)
        self.assertIn("tests/test_week6.py", results[0].command)
        self.assertTrue(
            all(call.kwargs["shell"] is False for call in run.call_args_list)
        )
        self.assertIn("--fail-under=90", results[-1].command)

    def test_pipeline_stops_after_failed_step(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="lint error",
            stderr="",
        )
        with patch(
            "core.week6_ci.subprocess.run",
            return_value=completed,
        ) as run:
            results = run_local_pipeline()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].return_code, 1)
        self.assertIn("lint error", results[0].output)
        run.assert_called_once()

    def test_pipeline_captures_timeout_and_missing_executable(self) -> None:
        timeout = subprocess.TimeoutExpired("flake8", 1, output=b"partial")
        with patch("core.week6_ci.subprocess.run", side_effect=timeout):
            timeout_results = run_local_pipeline()
        self.assertEqual(timeout_results[0].return_code, 124)
        self.assertIn("partial", timeout_results[0].output)

        with patch(
            "core.week6_ci.subprocess.run",
            side_effect=FileNotFoundError("python missing"),
        ):
            missing_results = run_local_pipeline()
        self.assertEqual(missing_results[0].return_code, 127)
        self.assertIn("python missing", missing_results[0].output)


if __name__ == "__main__":
    unittest.main()
