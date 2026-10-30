import json
import os

def create_python_notebook():
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 🐍 PYTHON SDET MASTERY NOTEBOOK (40 PROGRESSIVE EXERCISES)\n",
                    "**Target**: York Solutions / Optum SDET Interview Preparation\n",
                    "**Candidate**: Lokender Singh\n",
                    "**Kernel**: Python (ai-expense-venv)\n",
                    "\n",
                    "This notebook contains 40 hands-on Python exercises designed for senior SDET interviews, covering:\n",
                    "- Batch 1: OOP Fundamentals (Classes, Encapsulation, Inheritance, Polymorphism)\n",
                    "- Batch 2: Advanced OOP & Test Design Patterns (Dunder methods, ABCs, Context Managers)\n",
                    "- Batch 3: Core SDET Data Structures & Algorithms (Deduplication, Frequency Maps, Two Pointers)\n",
                    "- Batch 4: API Payload & Log Data Processing (Deep JSON Diff, Schema Validation, Regex Parsers)\n",
                    "- Batch 5: Pytest Mastery & Automation Utilities (Retry Decorators, Mocking, Fixture Yielding)\n",
                    "- Batch 6: Final Technical Challenges (LRU Cache, Interval Merging, Concurrency)\n",
                    "\n",
                    "---"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python (ai-expense-venv)",
                "language": "python",
                "name": "ai-expense-venv"
            },
            "language_info": {
                "name": "python",
                "version": "3.12"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }

    exercises = [
        # Batch 1: OOP Fundamentals
        ("Exercise 1: Class & Instance Variables (Account Tracker)",
         "Create a class `ExpenseAccount` that takes `account_name` and `initial_balance`. Track the balance for the instance, and maintain a class-level variable `total_accounts_created` that increments whenever a new instance is instantiated. Include a method `deposit(amount)` and `withdraw(amount)` with validation.",
         "class ExpenseAccount:\n    total_accounts_created = 0\n\n    def __init__(self, account_name: str, initial_balance: float = 0.0):\n        # TODO: Implement instance initialization\n        pass\n\n    def deposit(self, amount: float) -> float:\n        # TODO: Implement deposit\n        pass\n\n    def withdraw(self, amount: float) -> float:\n        # TODO: Implement withdraw\n        pass",
         "acc1 = ExpenseAccount('Healthcare Ops', 1000)\nacc2 = ExpenseAccount('Pharmacy Ledger', 500)\nacc1.deposit(250)\nassert acc1.balance == 1250\nacc1.withdraw(500)\nassert acc1.balance == 750\nassert ExpenseAccount.total_accounts_created >= 2\nprint('✅ Exercise 1 Passed!')"),

        ("Exercise 2: Encapsulation & Properties (Patient Claim Validation)",
         "Create a class `PatientClaim` with private attributes `__claim_id` and `__amount`. Use `@property` for `amount` with a setter that raises `ValueError` if the amount is less than or equal to 0. Add a read-only property for `claim_id`.",
         "class PatientClaim:\n    def __init__(self, claim_id: str, amount: float):\n        # TODO: Initialize private attributes\n        pass\n\n    @property\n    def claim_id(self) -> str:\n        # TODO: Return read-only claim_id\n        pass\n\n    @property\n    def amount(self) -> float:\n        # TODO: Return amount\n        pass\n\n    @amount.setter\n    def amount(self, value: float):\n        # TODO: Validate amount > 0 and set\n        pass",
         "claim = PatientClaim('CLM-9901', 450.0)\nassert claim.claim_id == 'CLM-9901'\nassert claim.amount == 450.0\ntry:\n    claim.amount = -50.0\n    assert False, 'Should raise ValueError'\nexcept ValueError:\n    pass\nprint('✅ Exercise 2 Passed!')"),

        ("Exercise 3: Inheritance & super() (SDET Test Case Hierarchy)",
         "Create a base class `BaseTestCase` taking `test_name` and `timeout_seconds=30`. Then create derived class `ApiTestCase` that adds `base_url` and calls `super().__init__()`. Add method `execute()` that returns an execution summary string.",
         "class BaseTestCase:\n    def __init__(self, test_name: str, timeout_seconds: int = 30):\n        # TODO: Implement base init\n        pass\n\nclass ApiTestCase(BaseTestCase):\n    def __init__(self, test_name: str, base_url: str, timeout_seconds: int = 30):\n        # TODO: Call super().__init__ and set base_url\n        pass\n\n    def execute(self) -> str:\n        # TODO: Return formatted execution string\n        pass",
         "api_test = ApiTestCase('Verify Auth Token', 'https://api.optum.com', timeout_seconds=15)\nassert api_test.test_name == 'Verify Auth Token'\nassert api_test.base_url == 'https://api.optum.com'\nassert api_test.timeout_seconds == 15\nassert 'Verify Auth' in api_test.execute()\nprint('✅ Exercise 3 Passed!')"),

        ("Exercise 4: Polymorphism & Method Overriding (Test Reporters)",
         "Create a base class `TestReporter` with a method `format_result(test_name: str, status: str) -> str`. Create `JsonReporter` (returns a JSON string `{'test': ..., 'status': ...}`) and `ConsoleReporter` (returns `[STATUS] test_name`). Demonstrate polymorphism via a helper function `publish_report(reporter, test_name, status)`.",
         "import json\n\nclass TestReporter:\n    def format_result(self, test_name: str, status: str) -> str:\n        return f'{test_name}: {status}'\n\nclass JsonReporter(TestReporter):\n    # TODO: Override format_result to return JSON string\n    pass\n\nclass ConsoleReporter(TestReporter):\n    # TODO: Override format_result to return '[STATUS] test_name'\n    pass",
         "json_rep = JsonReporter()\ncon_rep = ConsoleReporter()\nassert json.loads(json_rep.format_result('TC01', 'PASS')) == {'test': 'TC01', 'status': 'PASS'}\nassert con_rep.format_result('TC01', 'PASS') == '[PASS] TC01'\nprint('✅ Exercise 4 Passed!')"),

        ("Exercise 5: Alternate Constructor using @classmethod (Factory Pattern)",
         "Create a `TransactionDTO` class with attributes `id`, `vendor`, `amount`, `category`. Implement a `@classmethod` named `from_dict(data: dict)` and `from_csv_line(line: str)` that parses a comma-separated string `'TX101,Swiggy,450.0,Dining'` into a `TransactionDTO` instance.",
         "class TransactionDTO:\n    def __init__(self, id: str, vendor: str, amount: float, category: str):\n        self.id = id\n        self.vendor = vendor\n        self.amount = float(amount)\n        self.category = category\n\n    @classmethod\n    def from_csv_line(cls, line: str):\n        # TODO: Implement CSV parser constructor\n        pass",
         "dto = TransactionDTO.from_csv_line('TX101,Optum Health,1250.50,Healthcare')\nassert dto.id == 'TX101'\nassert dto.vendor == 'Optum Health'\nassert dto.amount == 1250.50\nassert dto.category == 'Healthcare'\nprint('✅ Exercise 5 Passed!')"),

        ("Exercise 6: Static Methods for Test Utilities",
         "Create a `TestUtils` class with static methods: `is_valid_email(email: str) -> bool` using regex, and `sanitize_currency(val: str) -> float` which converts `' ₹ 2,450.50 '` into float `2450.50`.",
         "import re\n\nclass TestUtils:\n    @staticmethod\n    def is_valid_email(email: str) -> bool:\n        # TODO: Implement email regex validation\n        pass\n\n    @staticmethod\n    def sanitize_currency(val: str) -> float:\n        # TODO: Strip symbols and commas, return float\n        pass",
         "assert TestUtils.is_valid_email('lokender.singh@optum.com') == True\nassert TestUtils.is_valid_email('invalid-email') == False\nassert TestUtils.sanitize_currency(' ₹ 12,450.75 ') == 12450.75\nprint('✅ Exercise 6 Passed!')"),

        ("Exercise 7: Type Checking & isinstance Polymorphic Asserter",
         "Create a function `assert_field_types(payload: dict, schema: dict) -> list[str]` that takes an API payload dictionary and a schema mapping `{field_name: expected_type}`. It should return a list of error strings for any missing fields or fields where `not isinstance(payload[k], expected_type)`.",
         "def assert_field_types(payload: dict, schema: dict) -> list[str]:\n    errors = []\n    # TODO: Iterate schema and validate payload presence and isinstance()\n    return errors",
         "schema = {'id': str, 'amount': (int, float), 'is_active': bool}\npayload = {'id': '123', 'amount': 'not_a_number'}\nerrs = assert_field_types(payload, schema)\nassert len(errs) == 2  # 'amount' type mismatch, 'is_active' missing\nprint('✅ Exercise 7 Passed!')"),

        # Batch 2: Advanced OOP & Test Design Patterns
        ("Exercise 8: Dunder Methods __str__ and __repr__ for Failure Logs",
         "Implement `__str__` (user-readable) and `__repr__` (unambiguous developer representation) on a `ClaimRecord` class so test assertions and pytest logs display informative failure diffs.",
         "class ClaimRecord:\n    def __init__(self, claim_id: str, member_id: str, amount: float):\n        self.claim_id = claim_id\n        self.member_id = member_id\n        self.amount = amount\n\n    # TODO: Implement __str__ and __repr__\n    pass",
         "c = ClaimRecord('C1', 'M1', 100.0)\nassert str(c) == 'Claim C1 for Member M1: ₹100.0'\nassert repr(c) == \"ClaimRecord(claim_id='C1', member_id='M1', amount=100.0)\"\nprint('✅ Exercise 8 Passed!')"),

        ("Exercise 9: Dunder Equality __eq__ and Ordering __lt__ for Assertions",
         "Implement `__eq__` (two claims are equal if claim_id and amount match) and `__lt__` (orders claims by amount ascending) on a `Claim` class. This allows direct `assert actual == expected` and `sorted(claims)`.",
         "class Claim:\n    def __init__(self, claim_id: str, amount: float):\n        self.claim_id = claim_id\n        self.amount = amount\n\n    # TODO: Implement __eq__ and __lt__\n    pass",
         "c1 = Claim('C1', 100)\nc2 = Claim('C1', 100)\nc3 = Claim('C2', 50)\nassert c1 == c2\nassert c3 < c1\nassert sorted([c1, c3]) == [c3, c1]\nprint('✅ Exercise 9 Passed!')"),

        ("Exercise 10: Abstract Base Classes (abc.ABC and @abstractmethod)",
         "Create an abstract class `AbstractDBClient` using `abc.ABC` with abstract methods `connect()`, `execute_query(query: str)`, and `disconnect()`. Implement concrete class `PostgresClient` that inherits from it.",
         "from abc import ABC, abstractmethod\n\nclass AbstractDBClient(ABC):\n    @abstractmethod\n    def connect(self) -> bool:\n        pass\n\n    @abstractmethod\n    def execute_query(self, query: str) -> list:\n        pass\n\nclass PostgresClient(AbstractDBClient):\n    # TODO: Implement all abstract methods\n    pass",
         "pg = PostgresClient()\nassert pg.connect() == True\nassert isinstance(pg, AbstractDBClient)\nprint('✅ Exercise 10 Passed!')"),

        ("Exercise 11: Composition over Inheritance (TestContext Architecture)",
         "Build a `TestContext` class that holds instances of `ApiClient`, `DatabaseHelper`, and `ConfigManager` via composition rather than multi-inheritance.",
         "class ApiClient:\n    def get(self, endpoint: str): return {'status': 200}\n\nclass DatabaseHelper:\n    def query(self, sql: str): return [{'id': 1}]\n\nclass TestContext:\n    def __init__(self):\n        # TODO: Initialize components via composition\n        pass",
         "ctx = TestContext()\nassert ctx.api.get('/health')['status'] == 200\nassert ctx.db.query('SELECT 1')[0]['id'] == 1\nprint('✅ Exercise 11 Passed!')"),

        ("Exercise 12: Custom Context Manager (__enter__, __exit__) for Test Timer",
         "Create a class `TestTimer` that works as a context manager (`with TestTimer() as timer:`). In `__enter__` it records start time; in `__exit__` it calculates `elapsed_time` and logs duration.",
         "import time\n\nclass TestTimer:\n    def __enter__(self):\n        # TODO: record start\n        return self\n\n    def __exit__(self, exc_type, exc_val, exc_tb):\n        # TODO: calculate elapsed\n        pass",
         "with TestTimer() as timer:\n    time.sleep(0.05)\nassert timer.elapsed_time >= 0.04\nprint('✅ Exercise 12 Passed!')"),

        ("Exercise 13: Custom Exception Hierarchy for Automation Framework",
         "Create a custom exception hierarchy: `AutomationFrameworkError` (base), `ElementNotFoundError` (inherits from base), and `ApiContractViolationError` (inherits from base, stores `status_code` and `payload`).",
         "class AutomationFrameworkError(Exception): pass\n\n# TODO: Implement ElementNotFoundError and ApiContractViolationError",
         "try:\n    raise ApiContractViolationError('Missing ID field', status_code=422, payload={'err': 'bad'})\nexcept AutomationFrameworkError as e:\n    assert e.status_code == 422\nprint('✅ Exercise 13 Passed!')"),

        ("Exercise 14: Thread-Safe Singleton Pattern for Framework Config",
         "Implement a Singleton class `FrameworkConfig` where repeated calls `FrameworkConfig()` return the exact same instance in memory (`assert FrameworkConfig() is FrameworkConfig()`).",
         "class FrameworkConfig:\n    _instance = None\n\n    def __new__(cls, *args, **kwargs):\n        # TODO: Implement Singleton pattern\n        pass",
         "c1 = FrameworkConfig()\nc2 = FrameworkConfig()\nassert c1 is c2\nprint('✅ Exercise 14 Passed!')"),

        # Batch 3: Core SDET Data Structures & Algorithms
        ("Exercise 15: Deduplication Preserving Order (O(N) Time and Space)",
         "Given a list of transaction IDs with duplicates `['TX1', 'TX2', 'TX1', 'TX3', 'TX2']`, return a deduplicated list that strictly preserves the original first-seen order without using O(N^2) list lookups.",
         "def deduplicate_preserve_order(items: list) -> list:\n    # TODO: Implement O(N) deduplication using seen set\n    pass",
         "assert deduplicate_preserve_order(['TX1', 'TX2', 'TX1', 'TX3', 'TX2']) == ['TX1', 'TX2', 'TX3']\nprint('✅ Exercise 15 Passed!')"),

        ("Exercise 16: Top K Most Frequent Error Codes",
         "Given a list of HTTP status codes returned by a stress test, write a function `top_k_frequent_codes(codes: list[int], k: int) -> list[tuple[int, int]]` that returns the top K most common codes and their frequencies sorted descending.",
         "def top_k_frequent_codes(codes: list[int], k: int) -> list[tuple[int, int]]:\n    # TODO: Count frequencies and return top k\n    pass",
         "codes = [200, 200, 500, 200, 404, 500, 500, 500, 429]\nres = top_k_frequent_codes(codes, 2)\nassert res == [(500, 4), (200, 3)]\nprint('✅ Exercise 16 Passed!')"),

        ("Exercise 17: First Non-Repeating Transaction ID",
         "Given a stream of transaction IDs `['A', 'B', 'C', 'B', 'A', 'D']`, find the first transaction ID that appears exactly once. Return `None` if all elements repeat.",
         "def first_non_repeating(stream: list[str]) -> str | None:\n    # TODO: Find first non-repeating\n    pass",
         "assert first_non_repeating(['A', 'B', 'C', 'B', 'A', 'D']) == 'C'\nassert first_non_repeating(['A', 'A', 'B', 'B']) == None\nprint('✅ Exercise 17 Passed!')"),

        ("Exercise 18: Two-Sum for Expense Budget Matching",
         "Given a list of expense amounts `[120.0, 450.0, 300.0, 550.0]` and a target `750.0`, return the indices of the two amounts that sum up to target in O(N) time.",
         "def two_sum_budget(amounts: list[float], target: float) -> tuple[int, int] | None:\n    # TODO: Implement two-sum using complement hash map\n    pass",
         "assert two_sum_budget([120.0, 450.0, 300.0, 550.0], 750.0) == (1, 2)\nprint('✅ Exercise 18 Passed!')"),

        ("Exercise 19: Grouping Transactions by Category",
         "Given a list of transaction dictionaries, group them into a dictionary mapping each category to a list of its transaction descriptions.",
         "def group_by_category(records: list[dict]) -> dict[str, list[str]]:\n    # TODO: Group records by category\n    pass",
         "txs = [{'desc': 'Swiggy', 'cat': 'Food'}, {'desc': 'Doctor', 'cat': 'Health'}, {'desc': 'Zomato', 'cat': 'Food'}]\nres = group_by_category(txs)\nassert res['Food'] == ['Swiggy', 'Zomato']\nassert res['Health'] == ['Doctor']\nprint('✅ Exercise 19 Passed!')"),

        ("Exercise 20: Safe Nested Key Extractor",
         "Write a function `safe_get(data: dict, path: str, default=None)` that takes a dot-separated path like `'user.profile.address.city'` and returns the nested value safely without throwing `KeyError` or `TypeError` if an intermediate key is missing or None.",
         "def safe_get(data: dict, path: str, default=None):\n    # TODO: Traverse dot path safely\n    pass",
         "sample = {'user': {'profile': {'address': {'city': 'Noida'}}}}\nassert safe_get(sample, 'user.profile.address.city') == 'Noida'\nassert safe_get(sample, 'user.profile.phone.number', 'N/A') == 'N/A'\nassert safe_get({}, 'user.profile') == None\nprint('✅ Exercise 20 Passed!')"),

        ("Exercise 21: Set Operations for RBAC Permission Assertions",
         "Given `actual_permissions: list[str]` and `required_permissions: list[str]`, determine: 1) `missing_permissions`, 2) `extra_permissions`, and 3) whether access should be granted (`is_compliant`).",
         "def check_rbac_compliance(actual: list[str], required: list[str]) -> dict:\n    # TODO: Use set operations\n    pass",
         "res = check_rbac_compliance(['READ', 'WRITE', 'EXECUTE'], ['READ', 'ADMIN'])\nassert res['missing'] == {'ADMIN'}\nassert res['extra'] == {'WRITE', 'EXECUTE'}\nassert res['is_compliant'] == False\nprint('✅ Exercise 21 Passed!')"),

        # Batch 4: API Payload & Log Data Processing
        ("Exercise 22: Deep JSON Comparison (Ignoring Ignored Keys)",
         "Write a recursive function `deep_diff(expected: dict, actual: dict, ignore_keys: set = {'timestamp', 'id'}) -> list[str]` that returns a list of difference descriptions (e.g. `'Key amount mismatch: expected 100, got 200'`).",
         "def deep_diff(expected: dict, actual: dict, ignore_keys: set = None) -> list[str]:\n    # TODO: Implement recursive dictionary comparison\n    pass",
         "exp = {'status': 'active', 'user': {'age': 30, 'id': 'u1'}}\nact = {'status': 'active', 'user': {'age': 35, 'id': 'u2'}}\ndiffs = deep_diff(exp, act, ignore_keys={'id'})\nassert len(diffs) == 1 and 'age' in diffs[0]\nprint('✅ Exercise 22 Passed!')"),

        ("Exercise 23: API Payload Schema & Mandatory Field Validator",
         "Write a function `validate_api_payload(payload: dict, required_fields: list[str], field_types: dict) -> tuple[bool, list[str]]` that validates both presence of required keys and correctness of data types.",
         "def validate_api_payload(payload: dict, required_fields: list[str], field_types: dict) -> tuple[bool, list[str]]:\n    # TODO: Validate fields\n    pass",
         "valid, errors = validate_api_payload({'id': '123', 'amount': 'abc'}, ['id', 'amount', 'date'], {'id': str, 'amount': (int, float), 'date': str})\nassert valid == False\nassert len(errors) == 2  # 'amount' type wrong, 'date' missing\nprint('✅ Exercise 23 Passed!')"),

        ("Exercise 24: Production Log File Regex Parser",
         "Given raw log lines like `'2026-10-30 14:22:10 [ERROR] 500 Internal Server Error in /api/claims/submit - Database connection pool exhausted'`, extract timestamps, log levels, status codes, endpoints, and error messages into dictionaries.",
         "import re\n\ndef parse_log_line(line: str) -> dict | None:\n    # TODO: Use regex to extract named groups\n    pass",
         "line = '2026-10-30 14:22:10 [ERROR] 500 /api/claims/submit - DB pool exhausted'\nd = parse_log_line(line)\nassert d['timestamp'] == '2026-10-30 14:22:10'\nassert d['level'] == 'ERROR'\nassert d['status_code'] == '500'\nprint('✅ Exercise 24 Passed!')"),

        ("Exercise 25: Sliding Window Rate Limiter Simulation",
         "Write a class `RateLimiter` that allows at most `max_requests` requests within a sliding window of `window_seconds`. Return `True` if request is allowed, `False` if throttled.",
         "import time\nfrom collections import deque\n\nclass RateLimiter:\n    def __init__(self, max_requests: int, window_seconds: float):\n        # TODO: Use deque to track timestamps\n        pass\n\n    def allow_request(self) -> bool:\n        # TODO: Evict old timestamps and check count\n        pass",
         "rl = RateLimiter(max_requests=2, window_seconds=0.1)\nassert rl.allow_request() == True\nassert rl.allow_request() == True\nassert rl.allow_request() == False  # throttled\ntime.sleep(0.12)\nassert rl.allow_request() == True  # allowed again\nprint('✅ Exercise 25 Passed!')"),

        ("Exercise 26: URL Query Parameter Builder",
         "Given a dictionary with primitives and lists `{'status': ['active', 'pending'], 'limit': 20, 'filter': 'healthcare'}`, serialize it into standard URL query parameters `'filter=healthcare&limit=20&status=active&status=pending'`.",
         "def build_query_string(params: dict) -> str:\n    # TODO: Serialize query string\n    pass",
         "qs = build_query_string({'status': ['active', 'pending'], 'limit': 20})\nassert 'limit=20' in qs and 'status=active' in qs\nprint('✅ Exercise 26 Passed!')"),

        ("Exercise 27: CSV to Typed Dataclasses",
         "Given a multi-line CSV string of medical claims, parse each row into an instance of a Python `@dataclass ClaimDTO` with types `claim_id: str, amount: float, is_approved: bool`.",
         "from dataclasses import dataclass\n\n@dataclass\nclass ClaimDTO:\n    claim_id: str\n    amount: float\n    is_approved: bool\n\ndef parse_claims_csv(csv_content: str) -> list[ClaimDTO]:\n    # TODO: Parse CSV rows into ClaimDTO instances\n    pass",
         "csv_text = 'id,amount,approved\\nCLM1,150.0,true\\nCLM2,200.5,false'\ndtols = parse_claims_csv(csv_text)\nassert len(dtols) == 2\nassert dtols[0].is_approved == True\nprint('✅ Exercise 27 Passed!')"),

        ("Exercise 28: Flattening Nested JSON Dictionaries",
         "Write a function `flatten_json(nested_dict: dict, parent_key: str = '', sep: str = '.') -> dict` that converts nested objects into single-level key paths (`{'a': {'b': 1}} -> {'a.b': 1}`).",
         "def flatten_json(d: dict, parent_key: str = '', sep: str = '.') -> dict:\n    # TODO: Recursively flatten dict\n    pass",
         "flat = flatten_json({'user': {'name': 'Lokender', 'meta': {'role': 'SDET'}}})\nassert flat == {'user.name': 'Lokender', 'user.meta.role': 'SDET'}\nprint('✅ Exercise 28 Passed!')"),

        # Batch 5: Pytest Mastery & Automation Utilities
        ("Exercise 29: Custom Pytest Parametrization Data Matrix Generator",
         "Create a utility function `generate_test_matrix(browsers: list[str], viewports: list[tuple[int, int]]) -> list[tuple[str, int, int]]` that produces all cartesian combinations with clean pytest ID strings.",
         "def generate_test_matrix(browsers: list[str], viewports: list[tuple[int, int]]):\n    # TODO: Generate combined test cases and custom IDs\n    pass",
         "cases, ids = generate_test_matrix(['chromium', 'firefox'], [(1280, 720), (375, 667)])\nassert len(cases) == 4\nassert 'chromium-1280x720' in ids\nprint('✅ Exercise 29 Passed!')"),

        ("Exercise 30: Retry Decorator with Exponential Backoff",
         "Write a decorator `@retry(max_attempts=3, backoff_factor=1.5)` that catches specified exceptions and retries the wrapped function with increasing sleep delays before finally re-raising.",
         "import time\nfrom functools import wraps\n\ndef retry(max_attempts: int = 3, backoff_factor: float = 1.0, exceptions=(Exception,)):\n    # TODO: Implement retry decorator\n    pass",
         "attempts = 0\n@retry(max_attempts=3, backoff_factor=0.01)\ndef flaky_call():\n    nonlocal attempts\n    attempts += 1\n    if attempts < 3: raise ValueError('Fail')\n    return 'OK'\nassert flaky_call() == 'OK'\nassert attempts == 3\nprint('✅ Exercise 30 Passed!')"),

        ("Exercise 31: Mocking External Service with unittest.mock",
         "Given a function `get_payment_status(tx_id: str)` that calls an external HTTP API, use `unittest.mock.patch` to mock `requests.get` returning a status 200 JSON `{'status': 'SUCCESS'}` without making a real network call.",
         "from unittest.mock import patch, MagicMock\n\ndef get_payment_status(tx_id: str):\n    import requests\n    resp = requests.get(f'https://payment.optum.com/status/{tx_id}')\n    return resp.json()['status']\n\n# TODO: Test get_payment_status using patch",
         "with patch('requests.get') as mock_get:\n    mock_get.return_value.json.return_value = {'status': 'SUCCESS'}\n    assert get_payment_status('TX99') == 'SUCCESS'\nprint('✅ Exercise 31 Passed!')"),

        ("Exercise 32: Data-Driven Generator Fixture (Yield Pattern)",
         "Write a generator function `db_user_fixture()` that simulates creating a temporary test user in setup, yields the user dictionary, and in teardown executes the cleanup deletion logic.",
         "def db_user_fixture():\n    # SETUP\n    user = {'id': 'usr_temp_123', 'name': 'Test User'}\n    print('User created in DB')\n    try:\n        yield user\n    finally:\n        # TEARDOWN\n        print('User deleted from DB')",
         "gen = db_user_fixture()\nu = next(gen)\nassert u['id'] == 'usr_temp_123'\ntry:\n    next(gen)\nexcept StopIteration:\n    pass\nprint('✅ Exercise 32 Passed!')"),

        ("Exercise 33: Pydantic Claim Schema Validation",
         "Define a Pydantic `BaseModel` named `HealthcareClaim` with fields `claim_id: str`, `amount: float`, `status: Literal['PENDING', 'APPROVED', 'REJECTED']`, and a validator ensuring `amount > 0`.",
         "from pydantic import BaseModel, Field, field_validator\nfrom typing import Literal\n\nclass HealthcareClaim(BaseModel):\n    # TODO: Implement Pydantic model\n    pass",
         "c = HealthcareClaim(claim_id='C1', amount=250.0, status='APPROVED')\nassert c.amount == 250.0\ntry:\n    HealthcareClaim(claim_id='C2', amount=-10.0, status='PENDING')\n    assert False\nexcept Exception:\n    pass\nprint('✅ Exercise 33 Passed!')"),

        ("Exercise 34: PII Data Sanitization / Masking",
         "Write a function `mask_pii(text: str) -> str` that automatically detects and masks credit card numbers (keep first 4 and last 4, e.g. `4111-XXXX-XXXX-1111`) and 10-digit phone numbers (`XXXXXX1234`).",
         "def mask_pii(text: str) -> str:\n    # TODO: Implement regex masking for sensitive data\n    pass",
         "res = mask_pii('My card is 4111-2222-3333-4444 and phone is 9876543210')\nassert '4111-XXXX-XXXX-4444' in res or '4111-XXXX' in res\nprint('✅ Exercise 34 Passed!')"),

        # Batch 6: Final Interview Challenges
        ("Exercise 35: LRU Cache Implementation",
         "Implement an `LRUCache(capacity: int)` with `get(key: str)` and `put(key: str, value: any)` operating in O(1) average time complexity using `collections.OrderedDict`.",
         "from collections import OrderedDict\n\nclass LRUCache:\n    def __init__(self, capacity: int):\n        # TODO: Initialize LRU cache\n        pass\n\n    def get(self, key: str):\n        # TODO: Get and move to end\n        pass\n\n    def put(self, key: str, value):\n        # TODO: Put and evict oldest if over capacity\n        pass",
         "lru = LRUCache(2)\nlru.put('a', 1)\nlru.put('b', 2)\nassert lru.get('a') == 1\nlru.put('c', 3)  # evicts 'b'\nassert lru.get('b') == None\nassert lru.get('c') == 3\nprint('✅ Exercise 35 Passed!')"),

        ("Exercise 36: Balanced JSON Brackets Validation",
         "Given a string containing only brackets `'{}[]()'`, write a function `is_valid_brackets(s: str) -> bool` using a stack to verify that all opening brackets are closed in the correct order.",
         "def is_valid_brackets(s: str) -> bool:\n    # TODO: Validate balanced brackets using stack\n    pass",
         "assert is_valid_brackets('{[()]}') == True\nassert is_valid_brackets('{[(])}') == False\nassert is_valid_brackets('{{[') == False\nprint('✅ Exercise 36 Passed!')"),

        ("Exercise 37: Merge Overlapping Appointment Time Intervals",
         "Given a list of appointment intervals `[[9, 11], [10, 12], [14, 16], [15, 17]]`, merge all overlapping intervals into `[[9, 12], [14, 17]]`.",
         "def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:\n    # TODO: Sort and merge overlapping intervals\n    pass",
         "assert merge_intervals([[9, 11], [10, 12], [14, 16], [15, 17]]) == [[9, 12], [14, 17]]\nprint('✅ Exercise 37 Passed!')"),

        ("Exercise 38: Matrix Transposition (Row to Column Assertions)",
         "Given a 2D matrix of tabular test data (rows and columns), return the transposed matrix where rows become columns and columns become rows.",
         "def transpose_matrix(matrix: list[list]) -> list[list]:\n    # TODO: Transpose matrix\n    pass",
         "m = [['Name', 'Age'], ['Lokender', 30], ['Amit', 28]]\nassert transpose_matrix(m) == [['Name', 'Lokender', 'Amit'], ['Age', 30, 28]]\nprint('✅ Exercise 38 Passed!')"),

        ("Exercise 39: Concurrent Health Check Worker (ThreadPoolExecutor)",
         "Write a function `check_endpoints_parallel(endpoints: list[str], max_workers: int = 5) -> dict[str, bool]` that runs health check validations concurrently using `concurrent.futures.ThreadPoolExecutor`.",
         "from concurrent.futures import ThreadPoolExecutor\n\ndef check_endpoint_mock(url: str) -> bool:\n    return True\n\ndef check_endpoints_parallel(endpoints: list[str], max_workers: int = 5) -> dict[str, bool]:\n    # TODO: Run checks in parallel\n    pass",
         "res = check_endpoints_parallel(['/auth', '/transactions', '/analytics'])\nassert len(res) == 3 and all(res.values())\nprint('✅ Exercise 39 Passed!')"),

        ("Exercise 40: Custom Test Discovery Engine",
         "Write a function `discover_test_functions(module_obj) -> list[str]` that inspects a Python module or class using `inspect` or `dir()` and returns all callable function names that start with `'test_'`.",
         "def discover_test_functions(obj) -> list[str]:\n    # TODO: Discover callables starting with 'test_'\n    pass",
         "class SampleSuite:\n    def test_login(self): pass\n    def test_logout(self): pass\n    def helper(self): pass\nassert discover_test_functions(SampleSuite) == ['test_login', 'test_logout']\nprint('✅ Exercise 40 Passed!')")
    ]

    for title, desc, code_stub, test_cell in exercises:
        nb["cells"].append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"### {title}\n", f"**Requirement**: {desc}\n"]
        })
        nb["cells"].append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [code_stub]
        })
        nb["cells"].append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [test_cell]
        })

    with open("notebooks/01_python_sdet_mastery.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print("Created notebooks/01_python_sdet_mastery.ipynb with 40 exercises!")

if __name__ == "__main__":
    create_python_notebook()
