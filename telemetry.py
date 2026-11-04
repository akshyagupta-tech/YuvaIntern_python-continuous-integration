"""Semantic-version build metadata and standard-library health probes."""

from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from quant_engine import QuantitativeEngine

__version__ = "1.0.0"
_SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


def build_metadata(commit_hash: str | None = None) -> dict[str, str]:
    """Return SemVer, UTC build time, revision, and runtime metadata."""
    if not _SEMVER_PATTERN.fullmatch(__version__):
        raise RuntimeError("Configured package version is not valid SemVer.")
    revision = commit_hash or os.environ.get("GITHUB_SHA") or _git_revision()
    return {
        "version": __version__,
        "commit_hash": revision or "unknown",
        "build_timestamp": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }


def _git_revision() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=1,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    revision = result.stdout.strip()
    return revision if result.returncode == 0 and revision else None


def health_check() -> dict[str, Any]:
    """Run zero-third-party-dependency arithmetic and transformation probes."""
    checks = {
        "decimal_arithmetic": QuantitativeEngine.add(
            Decimal("0.1"), Decimal("0.2")
        )
        == Decimal("0.3"),
        "matrix_transform": QuantitativeEngine.transpose_matrix(
            [[1, 2], [3, 4]]
        )
        == [
            [QuantitativeEngine._decimal(1), QuantitativeEngine._decimal(3)],
            [QuantitativeEngine._decimal(2), QuantitativeEngine._decimal(4)],
        ],
        "rolling_statistics": QuantitativeEngine.rolling_mean([1, 3], 2)
        == [QuantitativeEngine._decimal(2)],
    }
    return {
        "status": "healthy" if all(checks.values()) else "unhealthy",
        "checks": checks,
        "version": __version__,
        "python_version": sys.version.split()[0],
    }


__all__ = ["__version__", "build_metadata", "health_check"]
