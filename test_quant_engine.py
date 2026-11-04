"""Boundary and regression tests for the quantitative DevSecOps engine."""

from __future__ import annotations

import csv
import io
import json
import math
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import engine
from quant_engine import ComputationError, QuantitativeEngine
import telemetry
from telemetry import __version__, build_metadata, health_check


class TestDecimalArithmetic(unittest.TestCase):
    def test_decimal_operations_are_deterministic(self) -> None:
        self.assertEqual(
            QuantitativeEngine.add(Decimal("0.1"), Decimal("0.2")),
            Decimal("0.3"),
        )
        self.assertEqual(
            QuantitativeEngine.divide(Decimal("1"), Decimal("4")),
            Decimal("0.25"),
        )
        self.assertTrue(QuantitativeEngine.approximately_equal(0.1 + 0.2, 0.3))

    def test_invalid_nonfinite_and_zero_boundaries_fail(self) -> None:
        for operation, arguments in (
            (QuantitativeEngine.add, (True, 1)),
            (QuantitativeEngine.multiply, (float("nan"), 2)),
            (QuantitativeEngine.divide, (1, 0)),
        ):
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(ComputationError):
                    operation(*arguments)
        with self.assertRaises(ComputationError):
            QuantitativeEngine.add("not numeric", 1)  # type: ignore[arg-type]
        with self.assertRaises(ComputationError):
            QuantitativeEngine.add(Decimal("NaN"), 1)
        with self.assertRaises(ComputationError):
            QuantitativeEngine.approximately_equal(1, 1, relative_tolerance=-1)
        self.assertFalse(
            QuantitativeEngine.approximately_equal(
                Decimal("1e10000"), Decimal("2e10000")
            )
        )

    def test_compound_interest_precision_and_domain_validation(self) -> None:
        self.assertEqual(
            QuantitativeEngine.calculate_compound_interest(1000, 5, 2, 4),
            Decimal("104.49"),
        )
        invalid_arguments = (
            (-1, 5, 2, 1),
            (1000, -1, 2, 1),
            (1000, 5, -1, 1),
            (1000, 5, True, 1),
            (1000, 5, 2, 0),
            (1000, 5, 2, True),
        )
        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ComputationError):
                    QuantitativeEngine.calculate_compound_interest(*arguments)


class TestQuantitativeSeries(unittest.TestCase):
    def test_rolling_mean_and_moving_average(self) -> None:
        expected = [Decimal("1.5"), Decimal("2.5"), Decimal("3.5")]
        values = [1, 2, 3, 4]
        self.assertEqual(QuantitativeEngine.rolling_mean(values, 2), expected)
        self.assertEqual(
            QuantitativeEngine.moving_average(values, 2), expected
        )

    def test_empty_singleton_and_window_boundaries(self) -> None:
        self.assertEqual(QuantitativeEngine.rolling_mean([], 1), [])
        self.assertEqual(
            QuantitativeEngine.mean([Decimal("4.2")]), Decimal("4.2")
        )
        for values, window in (([1], 0), ([1], 2), ([], 1)):
            with self.subTest(values=values, window=window):
                if values == [] and window == 1:
                    continue
                with self.assertRaises(ComputationError):
                    QuantitativeEngine.rolling_mean(values, window)

    def test_sample_statistics_and_risk_adjusted_return(self) -> None:
        stats = QuantitativeEngine.compute_dataset_variance([1, 2, 3])
        self.assertEqual(stats["mean"], Decimal("2"))
        self.assertEqual(stats["variance"], Decimal("1"))
        self.assertEqual(stats["std_dev"], Decimal("1"))
        ratio = QuantitativeEngine.risk_adjusted_return(
            [Decimal("0.1"), Decimal("0.2"), Decimal("0.15")]
        )
        self.assertGreater(ratio, Decimal("0"))
        self.assertTrue(math.isfinite(float(ratio)))

    def test_risk_metric_and_variance_reject_invalid_series(self) -> None:
        with self.assertRaises(ComputationError):
            QuantitativeEngine.risk_adjusted_return([])
        with self.assertRaises(ComputationError):
            QuantitativeEngine.risk_adjusted_return([0.1, 0.1])
        with self.assertRaises(ComputationError):
            QuantitativeEngine.compute_dataset_variance([1])
        with self.assertRaises(ComputationError):
            QuantitativeEngine.mean([1, "bad"])  # type: ignore[list-item]
        with self.assertRaises(ComputationError):
            QuantitativeEngine.risk_adjusted_return(
                [0.1, 0.2], periods_per_year=0
            )
        with self.assertRaises(ComputationError):
            QuantitativeEngine.risk_adjusted_return(
                [0.1, 0.2], risk_free_rate=float("nan")
            )

    def test_invalid_rolling_inputs_and_invalid_series_shape(self) -> None:
        with self.assertRaises(ComputationError):
            QuantitativeEngine.rolling_mean("abc", 1)  # type: ignore[arg-type]
        with self.assertRaises(ComputationError):
            QuantitativeEngine.rolling_mean([1, 2], True)
        with self.assertRaises(ComputationError):
            QuantitativeEngine.mean([])

    def test_outlier_detection_handles_singletons_and_constant_series(
        self,
    ) -> None:
        self.assertEqual(
            QuantitativeEngine.detect_outliers([1, 1, 1, 100]),
            [Decimal("100")],
        )
        self.assertEqual(QuantitativeEngine.detect_outliers([5]), [])
        self.assertEqual(QuantitativeEngine.detect_outliers([]), [])
        self.assertEqual(
            QuantitativeEngine.detect_outliers([1, 2, 2, 3, 100]),
            [Decimal("100")],
        )
        with self.assertRaises(ComputationError):
            QuantitativeEngine.detect_outliers([1, 2], threshold=0)


class TestMatrixAndExports(unittest.TestCase):
    def test_matrix_transpose_and_multiplication(self) -> None:
        self.assertEqual(
            QuantitativeEngine.transpose_matrix([[1, 2], [3, 4]]),
            [[Decimal("1"), Decimal("3")], [Decimal("2"), Decimal("4")]],
        )
        self.assertEqual(
            QuantitativeEngine.multiply_matrices([[1, 2]], [[3], [4]]),
            [[Decimal("11")]],
        )

    def test_ragged_or_incompatible_matrices_are_rejected(self) -> None:
        with self.assertRaises(ComputationError):
            QuantitativeEngine.transpose_matrix([[1, 2], [3]])
        with self.assertRaises(ComputationError):
            QuantitativeEngine.multiply_matrices([[1, 2]], [[1, 2]])
        for matrix in ([[]], [[True]], "invalid"):
            with self.subTest(matrix=matrix):
                with self.assertRaises(ComputationError):
                    QuantitativeEngine.transpose_matrix(
                        matrix  # type: ignore[arg-type]
                    )
        with self.assertRaises(ComputationError):
            QuantitativeEngine.multiply_matrices([], [[1]])

    def test_json_csv_and_text_table_exports(self) -> None:
        summary = QuantitativeEngine.analyze_series([1, 2, 3], window=2)
        json_result = json.loads(QuantitativeEngine.export_json(summary))
        self.assertEqual(json_result["count"], 3)
        csv_rows = list(
            csv.DictReader(io.StringIO(QuantitativeEngine.export_csv(summary)))
        )
        self.assertTrue(any(row["metric"] == "mean" for row in csv_rows))
        self.assertIn("mean", QuantitativeEngine.export_table(summary))
        self.assertIn("No metrics", QuantitativeEngine.export_table({}))
        self.assertTrue(
            QuantitativeEngine.export_csv({}).startswith("metric,value")
        )
        with self.assertRaises(TypeError):
            QuantitativeEngine.export_json({"unsupported": object()})

    def test_series_analysis_empty_singleton_and_invalid_window(self) -> None:
        self.assertEqual(QuantitativeEngine.analyze_series([])["count"], 0)
        singleton = QuantitativeEngine.analyze_series([Decimal("4.2")])
        self.assertEqual(singleton["mean"], Decimal("4.2"))
        with self.assertRaises(ComputationError):
            QuantitativeEngine.analyze_series([1], window=0)


class TestBuildTelemetry(unittest.TestCase):
    def test_metadata_has_semver_timestamp_and_commit_hash(self) -> None:
        metadata = build_metadata(commit_hash="0123456789abcdef")
        self.assertEqual(metadata["version"], __version__)
        self.assertRegex(metadata["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(metadata["commit_hash"], "0123456789abcdef")
        self.assertTrue(metadata["build_timestamp"].endswith("Z"))

    def test_health_check_is_zero_dependency_and_passes(self) -> None:
        result = health_check()
        self.assertEqual(result["status"], "healthy")
        self.assertTrue(result["checks"])
        self.assertTrue(all(result["checks"].values()))

    def test_semver_validation_and_ci_revision_precedence(self) -> None:
        with patch.object(telemetry, "__version__", "not-semver"):
            with self.assertRaises(RuntimeError):
                build_metadata(commit_hash="revision")
        with patch.dict("os.environ", {"GITHUB_SHA": "ci-revision"}):
            with patch(
                "telemetry._git_revision", return_value="local-revision"
            ):
                self.assertEqual(
                    build_metadata()["commit_hash"], "ci-revision"
                )

    def test_git_revision_failures_are_nonfatal(self) -> None:
        with patch.dict("os.environ", {"GITHUB_SHA": ""}):
            with patch(
                "telemetry.subprocess.run",
                side_effect=OSError("git unavailable"),
            ):
                self.assertEqual(build_metadata()["commit_hash"], "unknown")
            with patch("telemetry.subprocess.run") as run:
                run.return_value.returncode = 1
                run.return_value.stdout = ""
                self.assertEqual(build_metadata()["commit_hash"], "unknown")

    def test_cli_health_metadata_benchmark_and_help_paths(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(engine.main(["--check"]), 0)
            self.assertEqual(engine.main(["--metadata"]), 0)
            self.assertEqual(engine.main(["--benchmark"]), 0)
            self.assertEqual(engine.main([]), 0)
        self.assertIn('"healthy"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
