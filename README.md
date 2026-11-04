# Automated Quantitative Engine & DevSecOps CI/CD Suite

[![CI status](https://github.com/akshyagupta-tech/YuvaIntern_python-continuous-integration/actions/workflows/ci.yml/badge.svg)](https://github.com/akshyagupta-tech/YuvaIntern_python-continuous-integration/actions/workflows/ci.yml)

## Capabilities

- Decimal-based financial calculations, rolling statistics, sample variance,
  risk-adjusted returns, robust outlier detection, and matrix operations.
- JSON, CSV, and plain-text report exporters.
- SemVer/build metadata and a standard-library health sentinel.
- Python 3.10, 3.11, and 3.12 CI matrix with strict Flake8, mypy, Bandit,
  dependency audit, and a 90% branch-aware coverage gate.
- Archived unit test output, coverage reports, benchmark data, and wheel builds.

## Install and Run

```bash
python -m pip install -r requirements.txt
python -m engine --check
python -m engine --metadata
python -m engine --benchmark
streamlit run app.py
```

## Development Checks

```bash
python -m pip install -r requirements-dev.txt
flake8 . --count --max-line-length=79 --statistics
mypy --strict --ignore-missing-imports quant_engine.py telemetry.py engine.py calculator_engine.py calc.py core/week6_ci.py app.py
bandit -r . -x ./.git,./tests -ll
python -m coverage run --branch --source=quant_engine,telemetry,engine -m unittest discover
python -m coverage report --fail-under=90 -m
pip-audit -r requirements.txt
```