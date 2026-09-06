# FLOOD-X — Testing Guide

> How to run, extend, and understand the test suite.

---

## Test Architecture

```
tests/
├── conftest.py              — pytest config, sys.path setup
├── unit/
│   ├── test_hydrology.py    — SCS-CN, Kirpich, Rational Method
│   ├── test_ml_predictor.py — XGBoost predictor load + inference
│   ├── test_risk_engine.py  — weighted risk scoring
│   └── test_routing.py      — NetworkX Dijkstra routing
├── api/
│   └── test_endpoints.py    — all 16 API routes (httpx AsyncClient)
├── integration/
│   └── test_simulation.py   — simulation lifecycle (start/pause/reset)
└── e2e/                     — (reserved for browser tests, Playwright)
```

**Current count:** 43 unit tests + 27 API/integration tests = **70 total**

---

## Running Tests

### All tests
```bash
# From project root, venv active:
pytest tests/ -v
```

### By category
```bash
# Unit tests only (fast, no IO)
pytest tests/unit/ -v

# API tests only
pytest tests/api/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Individual test file
```bash
pytest tests/unit/test_hydrology.py -v
pytest tests/api/test_endpoints.py::test_flood_nowcast -v
```

---

## Test Configuration

```ini
# pytest.ini (or pyproject.toml [tool.pytest.ini_options])
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

For async tests, `pytest-asyncio` is used. Fixtures with `@pytest_asyncio.fixture` are used for async client setup.

---

## Unit Test Coverage

### `test_hydrology.py` — 14 tests

Tests SCS-CN hydrology engine:
- `test_scs_cn_zero_rainfall` — zero input → zero runoff
- `test_scs_cn_low_rainfall` — below initial abstraction threshold
- `test_scs_cn_moderate` — AMC-II normal conditions
- `test_scs_cn_extreme` — extreme 100mm/hr input
- `test_amc_adjustment` — AMC-I, AMC-II, AMC-III CN values
- `test_kirpich_tc` — time of concentration formula
- `test_rational_method_peak_flow` — Q = CiA/360
- `test_catchments_defined` — 12 synthetic catchments present
- ... (6 more)

### `test_ml_predictor.py` — 11 tests

Tests XGBoost predictor:
- `test_models_loaded` — verifies models/scaler_v1.pkl present
- `test_classifier_output_range` — probability in [0.0, 1.0]
- `test_regressor_nonnegative` — depth ≥ 0
- `test_predict_zero_rainfall` — zero intensity → low probability
- `test_predict_extreme_rainfall` — 120 mm/hr → high probability
- `test_feature_importances` — 14 features, sum ≈ 1.0
- `test_explain_prediction` — contribution dict present
- ... (4 more)

### `test_risk_engine.py` — 8 tests

Tests 5-component risk scoring:
- `test_zero_risk_inputs` → LOW
- `test_moderate_inputs` → MODERATE
- `test_critical_inputs` → CRITICAL
- `test_weight_sum_is_one` — engineering requirement
- `test_thresholds_monotonic` — LOW < MODERATE < HIGH < CRITICAL
- ... (3 more)

### `test_routing.py` — 10 tests

Tests NetworkX Dijkstra routing:
- `test_graph_loaded` — 22 nodes, 58 edges
- `test_normal_route_exists` — path from origin to destination
- `test_flood_aware_route_different` — flood-aware ≠ normal when zones flooded
- `test_flood_penalty_applied` — edge weights increase for HIGH/CRITICAL zones
- `test_impassable_edges_excluded` — CRITICAL nodes removed from graph
- ... (5 more)

---

## API Test Coverage (`test_endpoints.py`)

All 16 routes tested:

| Route | Test | Checks |
|-------|------|--------|
| `GET /health` | ✅ | status=ok |
| `GET /rainfall/current` | ✅ | data_source field |
| `GET /rainfall/forecast` | ✅ | array, non-empty |
| `GET /flood/nowcast` | ✅ | 12 catchments, 9 horizons |
| `GET /flood/zones` | ✅ | GeoJSON FeatureCollection |
| `GET /flood/zones/polygons` | ✅ | Polygon geometry |
| `GET /flood/location/{id}` | ✅ | valid + 404 |
| `GET /flood/clock/{id}` | ✅ | status field |
| `GET /drainage/status` | ✅ | utilization float |
| `GET /drainage/nodes` | ✅ | 30 nodes |
| `GET /routes/safe` | ✅ | both route variants |
| `GET /routes/graph-info` | ✅ | node/edge counts |
| `GET /alerts` | ✅ | list response |
| `GET /decisions/current` | ✅ | disclaimer present |
| `GET /system/status` | ✅ | data_mode field |
| `GET /simulation/scenarios` | ✅ | ≥8 scenarios |
| `GET /explain/feature-importance` | ✅ | 14 features, sorted |
| `GET /explain/prediction` | ✅ | contributions dict |
| `GET /demo/phases` | ✅ | non-empty list |

---

## Writing New Tests

### Unit test template
```python
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.services.my_service import MyService

def test_my_service_basic():
    svc = MyService()
    result = svc.compute(input=10)
    assert result > 0
    assert isinstance(result, float)
```

### Async API test template
```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_my_endpoint(client):
    r = await client.get("/api/v1/my-endpoint")
    assert r.status_code == 200
    assert "expected_field" in r.json()
```

---

## CI/CD Integration

```yaml
# .github/workflows/test.yml (example)
- name: Run tests
  run: |
    python scripts/train_models.py  # models required for ML tests
    pytest tests/ -v --tb=short
```

**Note:** ML model files are required before running `test_ml_predictor.py`. Always run `python scripts/train_models.py` first.
