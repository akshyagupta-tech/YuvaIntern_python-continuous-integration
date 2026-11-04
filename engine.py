"""Zero-dependency command-line health and quantitative benchmark checks."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from typing import Sequence

from quant_engine import QuantitativeEngine
from telemetry import build_metadata, health_check


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "--check",
        action="store_true",
        help="run standard-library-only arithmetic and health checks",
    )
    actions.add_argument(
        "--metadata",
        action="store_true",
        help="print semantic version and build metadata as JSON",
    )
    actions.add_argument(
        "--benchmark",
        action="store_true",
        help="print a deterministic sample quantitative report as JSON",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one health, build-metadata, or sample-report action."""
    arguments = _parser().parse_args(argv)
    if arguments.check:
        result = health_check()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] == "healthy" else 1
    if arguments.metadata:
        print(json.dumps(build_metadata(), indent=2, sort_keys=True))
        return 0
    if arguments.benchmark:
        summary = QuantitativeEngine.analyze_series(
            [
                Decimal("0.012"),
                Decimal("-0.004"),
                Decimal("0.019"),
                Decimal("0.008"),
                Decimal("0.011"),
            ],
            window=3,
        )
        print(QuantitativeEngine.export_json(summary))
        return 0
    _parser().print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
