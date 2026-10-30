# 🧪 PYTEST & PYTHON OOP: COMPREHENSIVE SDET MASTERY GUIDE
**Target**: Complete Pytest Architecture, Fixtures, Scopes, Mocking & Automation OOP Design Patterns  
**Candidate**: Lokender Singh (8+ yrs Exp)  
*Note: This is an exhaustive, self-contained reference and conceptual guide. It explains everything from virtual environment creation and installation to advanced framework design patterns.*

---

## 1. Installation & Environment Setup from Scratch

### 1. Setting Up a Dedicated Virtual Environment
In professional automation, always isolate your Python dependencies from the global system:
```powershell
# Create a virtual environment named 'venv'
python -m venv venv

# Activate on Windows PowerShell:
.\venv\Scripts\Activate.ps1

# (If PowerShell blocks scripts, run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)
```

### 2. Installing Core SDET Libraries
```bash
pip install pytest pytest-asyncio pytest-rerunfailures pytest-xdist httpx pydantic
```
- **`pytest`**: The core testing framework.
- **`pytest-asyncio`**: Enables testing `async def` functions and coroutines (essential for modern FastAPI/httpx backends).
- **`pytest-rerunfailures`**: Adds `--reruns 2` to automatically retry flaky tests.
- **`pytest-xdist`**: Adds `-n auto` to execute tests in parallel across multiple CPU cores.
- **`httpx`**: Modern, fast async HTTP client (superior to `requests` for async API testing).
- **`pydantic`**: Data validation and type enforcement for API payload schemas.

### 3. Pytest Configuration File (`pytest.ini`)
Every enterprise project should have a `pytest.ini` at the root directory:
```ini
[pytest]
minversion = 8.0
testpaths = backend/tests tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = -v -s --strict-markers
markers =
    smoke: Critical sanity and smoke tests
    regression: Comprehensive regression suite
    evals: LLM and AI evaluation tests
```

---

## 2. Pytest Execution Engine & CLI Flags

### How Pytest Discovers Tests
When you invoke `pytest`, the runner scans files matching `test_*.py` or `*_test.py`. It inspects:
1. Functions starting with `test_` outside any class.
2. Classes starting with `Test` (which must **never** define an `__init__` constructor—doing so causes pytest to ignore the class).
3. Methods inside those classes starting with `test_`.

### Assertion Rewriting (The Secret Behind `assert a == b`)
- In other frameworks (like Java JUnit or Python `unittest`), you write `self.assertEqual(a, b)` or `self.assertTrue(x)`.
- **In Pytest**, you simply write standard Python `assert a == b`.
- **How it works under the hood**: Pytest uses Python's Abstract Syntax Tree (AST) rewriting to intercept standard `assert` statements before execution. If the assertion fails, Pytest introspects the intermediate variables, displaying rich failure diffs (showing exact missing dictionary keys, mismatched strings, or set differences) without requiring custom assertion libraries!

### Essential SDET CLI Flags
| Flag | What It Does |
| :--- | :--- |
| `pytest -v` | **Verbose mode**: Prints each test file and function name with pass/fail status. |
| `pytest -s` | **No capture**: Disables stdout capturing, printing all `print()` statements in real-time. |
| `pytest -k "auth and not slow"` | **Keyword filtering**: Runs tests matching an expression based on test names. |
| `pytest -m "smoke"` | **Marker filtering**: Runs only tests decorated with `@pytest.mark.smoke`. |
| `pytest --lf` | **Last Failed**: Runs *only* tests that failed during the previous test run. |
| `pytest --ff` | **Failed First**: Runs failed tests first, then executes the rest of the suite. |
| `pytest -x` or `--maxfail=1` | **Fail Fast**: Halts the test run immediately upon encountering the first failure. |
| `pytest -n auto` | **Parallel Execution** (via `pytest-xdist`): Spawns worker processes across all CPU cores. |
| `pytest --reruns 2` | Retries failed tests up to 2 times before marking as failed. |
| `pytest --durations=5` | Lists the 5 slowest tests and fixtures (identifies framework bottlenecks). |

---

## 3. Fixtures, Scopes & The Dependency Injection Lifecycle

### Anatomy of a Fixture with `yield`
A fixture manages setup and teardown via Python generators:
```python
import pytest

@pytest.fixture
def api_client():
    # 1. SETUP: Executes before the test function runs
    client = MyApiClient(base_url="http://localhost:8000")
    client.authenticate()
    
    # 2. YIELD: Hands off the resource to the test function
    yield client
    
    # 3. TEARDOWN: Executes after the test completes (even if test fails!)
    client.cleanup_sessions()
```

### The 5 Fixture Scopes (High-Frequency Interview Question)
The `scope` parameter in `@pytest.fixture(scope="...")` controls fixture lifetime:

```
[ Session Scope: Lifetime of entire test run (once per test suite) ]
   └── [ Package Scope: Lifetime of directory package ]
         └── [ Module Scope: Lifetime of single Python file (test_claims.py) ]
               └── [ Class Scope: Lifetime of single test class (TestAuthApi) ]
                     └── [ Function Scope (Default): Lifetime of individual test_func() ]
```

1. **`function`** *(Default)*:
   - Re-instantiated before every single test function, and torn down immediately after.
   - *Ideal Use*: Generating isolated, disposable test records; clean mock states.
2. **`class`**:
   - Executed once per test class. Shared across all `test_*` methods in that class.
   - *Ideal Use*: Initializing a shared page object or test harness for a group of related tests.
3. **`module`**:
   - Executed once per Python module file (`test_transactions.py`).
   - *Ideal Use*: Booting an in-memory test database, opening a persistent network socket.
4. **`package`**:
   - Executed once per directory package containing multiple test modules.
5. **`session`**:
   - Executed **once for the entire pytest run**.
   - *Ideal Use*: Database connection pool creation, starting Docker test containers, fetching an enterprise JWT token reused across 1,000 API tests.

### Cascading `conftest.py` Architecture
- A `conftest.py` file serves as a global or package-level fixture repository.
- Fixtures defined in `conftest.py` are **automatically available** to all test files in that directory and child directories without needing `import`.
- **Cascading Overrides**: If `root/conftest.py` defines `base_url = "http://localhost:8000"`, a subfolder `root/tests/staging/conftest.py` can define `base_url = "https://staging.optum.com"`. Tests in that subfolder will automatically use the staging URL!

### Parameterized Fixtures
Fixtures themselves can be parameterized to run dependent tests across multiple configurations:
```python
@pytest.fixture(params=["chromium", "firefox", "webkit"])
def browser_name(request):
    return request.param

def test_login(browser_name):
    print(f"Testing on {browser_name}")
```
*Result*: Any test requesting `browser_name` executes 3 times automatically!

---

## 4. Test Parameterization (`@pytest.mark.parametrize`)

Parameterization allows you to run a single test function against multiple data rows:

```python
import pytest

@pytest.mark.parametrize(
    "patient_id, billed_amount, expected_status",
    [
        ("PAT-001", 150.0, 201),
        ("PAT-002", -50.0, 422), # Negative amount validation
        ("", 500.0, 422),        # Missing patient ID
        ("PAT-003", 0.0, 422),   # Zero amount validation
    ],
    ids=["valid_claim", "negative_amount", "missing_patient", "zero_amount"]
)
def test_claim_submission_api(patient_id, billed_amount, expected_status, api_client):
    payload = {"patient_id": patient_id, "amount": billed_amount}
    response = api_client.post("/api/claims", json=payload)
    assert response.status_code == expected_status
```

---

## 5. Mocking in Python (`unittest.mock`)

Mocking replaces external, slow, or unreliable dependencies (like external payment gateways or third-party SMS providers) with controllable mock objects.

### The Golden Rule of Mocking
> *"Always patch where an object is **USED**, not where it is **DEFINED**."*

Suppose `backend/services/claims.py` has:
```python
from backend.clients.payment import charge_copay
def submit_claim(...):
    return charge_copay(...)
```
- ❌ **Wrong**: `patch('backend.clients.payment.charge_copay')`
- ✅ **Correct**: `patch('backend.services.claims.charge_copay')`

### Mocking Return Values and Side Effects
```python
from unittest.mock import patch, MagicMock

# 1. Mocking a return value
@patch("backend.services.claims.charge_copay")
def test_claim_success(mock_charge, api_client):
    mock_charge.return_value = {"transaction_id": "TX99", "status": "SUCCESS"}
    res = api_client.post("/api/claims", json={...})
    assert res.status_code == 201
    mock_charge.assert_called_once()

# 2. Mocking an exception (Side Effect)
@patch("backend.services.claims.charge_copay")
def test_claim_gateway_timeout(mock_charge, api_client):
    mock_charge.side_effect = TimeoutError("Gateway unreachable")
    res = api_client.post("/api/claims", json={...})
    assert res.status_code == 504 # Gateway Timeout error handling
```

---

## 6. Python OOP Patterns for Test Automation Frameworks

### 1. Class & Instance Attributes
- **Class Attributes**: Defined directly in the class body; shared by all instances.
  - *SDET Use Case*: Default timeouts, shared base URLs, class-level counters.
- **Instance Attributes**: Defined inside `__init__(self)`; unique to each instance.

### 2. Encapsulation & `@property` (Getters/Setters)
Encapsulation protects internal state from invalid mutation:
```python
class PatientClaim:
    def __init__(self, claim_id: str, amount: float):
        self._claim_id = claim_id
        self._amount = amount

    @property
    def amount(self) -> float:
        return self._amount

    @amount.setter
    def amount(self, value: float):
        if value <= 0:
            raise ValueError("Claim amount must be strictly greater than zero.")
        self._amount = value
```

### 3. Inheritance & `super()` for Test Hierarchies
```python
class BaseApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}

class ClaimsApiClient(BaseApiClient):
    def __init__(self, base_url: str, auth_token: str):
        super().__init__(base_url)
        self.headers["Authorization"] = f"Bearer {auth_token}"

    def get_claim(self, claim_id: str):
        return httpx.get(f"{self.base_url}/claims/{claim_id}", headers=self.headers)
```

### 4. Polymorphism & Abstract Base Classes (`abc.ABC`)
Enforces that every database client adheres to a common interface:
```python
from abc import ABC, abstractmethod

class BaseDatabase(ABC):
    @abstractmethod
    def query(self, sql: str) -> list[dict]:
        """Must be implemented by concrete classes."""
        pass

class PostgresDatabase(BaseDatabase):
    def query(self, sql: str) -> list[dict]:
        # Concrete implementation
        return [...]
```

### 5. Custom Context Managers (`__enter__`, `__exit__`)
```python
import time

class BenchmarkTimer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration_ms = (time.perf_counter() - self.start) * 1000

# In test:
with BenchmarkTimer() as timer:
    api.search_claims("Cardiology")
assert timer.duration_ms < 200.0, f"Search took too long: {timer.duration_ms}ms"
```
