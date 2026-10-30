import json

def generate_sdet_focused_python_nb():
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 🐍 PYTHON SDET MASTERY NOTEBOOK (CORE DATA STRUCTURES & SDET LOGIC)\n",
                    "**Target**: York Solutions / Optum SDET Technical Interview\n",
                    "**Candidate**: Lokender Singh\n",
                    "**Kernel**: Python (ai-expense-venv)\n",
                    "\n",
                    "This notebook is strictly focused on **high-frequency SDET coding questions**:\n",
                    "- **Batch 1 (1–7)**: Lists, Loops & Comprehensions (Filtering, flattening, `enumerate`, `zip`)\n",
                    "- **Batch 2 (8–14)**: Dictionaries & Sets (Frequency counting, grouping, merging, set diffs)\n",
                    "- **Batch 3 (15–21)**: Lambda Functions, Custom Sorting & Built-in Functions (`key=lambda`, `any`, `all`)\n",
                    "- **Batch 4 (22–28)**: DateTime & Timedelta Math, Date Parsing, String Manipulations\n",
                    "- **Batch 5 (29–34)**: Real-World SDET Data Validation (Deep JSON diff, Missing keys, Log parsing)\n",
                    "- **Batch 6 (35–40)**: Core OOP & Test Utilities (Classes, Inheritance, Retry loops, Masking)\n",
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
        # BATCH 1: Lists, Loops & Comprehensions
        ("Exercise 1: List Comprehension with Conditional Filtering",
         "Given a list of transaction dictionaries, write a function `filter_high_value_claims(claims: list[dict], min_amount: float) -> list[str]` using a list comprehension that returns a list of `claim_id`s for all claims where `amount >= min_amount` and `status == 'APPROVED'`.",
         "def filter_high_value_claims(claims: list[dict], min_amount: float) -> list[str]:\n    # TODO: Use list comprehension to extract claim_id\n    pass",
         "claims = [\n    {'claim_id': 'CLM1', 'amount': 1200.0, 'status': 'APPROVED'},\n    {'claim_id': 'CLM2', 'amount': 450.0, 'status': 'APPROVED'},\n    {'claim_id': 'CLM3', 'amount': 3000.0, 'status': 'DENIED'},\n    {'claim_id': 'CLM4', 'amount': 2500.0, 'status': 'APPROVED'}\n]\nassert filter_high_value_claims(claims, 1000.0) == ['CLM1', 'CLM4']\nprint('✅ Exercise 1 Passed!')"),

        ("Exercise 2: Flattening 2D Test Matrix using Nested List Comprehension",
         "Given a nested list of test environments `[['chrome-win', 'chrome-mac'], ['firefox-win', 'firefox-mac'], ['safari-mac']]`, write a function `flatten_environments(matrix: list[list[str]]) -> list[str]` using a single nested list comprehension to flatten it into a 1D list.",
         "def flatten_environments(matrix: list[list[str]]) -> list[str]:\n    # TODO: Single nested list comprehension [item for sublist in matrix for item in sublist]\n    pass",
         "matrix = [['chrome-win', 'chrome-mac'], ['firefox-win', 'firefox-mac'], ['safari-mac']]\nassert flatten_environments(matrix) == ['chrome-win', 'chrome-mac', 'firefox-win', 'firefox-mac', 'safari-mac']\nprint('✅ Exercise 2 Passed!')"),

        ("Exercise 3: Tracking Indexes with enumerate() in Test Step Validation",
         "Given a list of executed test step statuses `['PASS', 'PASS', 'FAIL', 'PASS', 'FAIL']`, write a function `find_failed_step_numbers(steps: list[str]) -> list[int]` using `enumerate()` that returns 1-based step numbers of all failed steps (e.g. `[3, 5]`).",
         "def find_failed_step_numbers(steps: list[str]) -> list[int]:\n    # TODO: Use enumerate(steps, start=1) and list comprehension\n    pass",
         "steps = ['PASS', 'PASS', 'FAIL', 'PASS', 'FAIL']\nassert find_failed_step_numbers(steps) == [3, 5]\nprint('✅ Exercise 3 Passed!')"),

        ("Exercise 4: Pairing Test Data with zip()",
         "Given a list of input prompts `['Login', 'Book', 'Cancel']` and a list of expected status codes `[200, 201, 204]`, write a function `pair_test_cases(prompts: list[str], statuses: list[int]) -> list[dict]` that uses `zip()` to produce a list of dictionaries `[{'prompt': ..., 'expected_status': ...}]`.",
         "def pair_test_cases(prompts: list[str], statuses: list[int]) -> list[dict]:\n    # TODO: Use zip() in list comprehension\n    pass",
         "prompts = ['Login', 'Book', 'Cancel']\nstatuses = [200, 201, 204]\nexpected = [\n    {'prompt': 'Login', 'expected_status': 200},\n    {'prompt': 'Book', 'expected_status': 201},\n    {'prompt': 'Cancel', 'expected_status': 204}\n]\nassert pair_test_cases(prompts, statuses) == expected\nprint('✅ Exercise 4 Passed!')"),

        ("Exercise 5: Deduplicating List while Strictly Preserving First-Seen Order",
         "Given a list with duplicate elements `['CLM10', 'CLM20', 'CLM10', 'CLM30', 'CLM20']`, write a function `dedup_preserve_order(items: list) -> list` that removes duplicates while preserving original order in O(N) time (hint: use a seen `set`).",
         "def dedup_preserve_order(items: list) -> list:\n    # TODO: Deduplicate preserving order\n    pass",
         "assert dedup_preserve_order(['CLM10', 'CLM20', 'CLM10', 'CLM30', 'CLM20']) == ['CLM10', 'CLM20', 'CLM30']\nassert dedup_preserve_order([1, 2, 1, 3, 2, 4]) == [1, 2, 3, 4]\nprint('✅ Exercise 5 Passed!')"),

        ("Exercise 6: Chunking a List into Fixed-Size Batches for API Stress Testing",
         "Write a function `chunk_list(data: list, chunk_size: int) -> list[list]` that splits a list of items into sub-batches of size `chunk_size` using loop slicing `range(0, len(data), chunk_size)`.",
         "def chunk_list(data: list, chunk_size: int) -> list[list]:\n    # TODO: Split list into chunks\n    pass",
         "records = [1, 2, 3, 4, 5, 6, 7, 8]\nassert chunk_list(records, 3) == [[1, 2, 3], [4, 5, 6], [7, 8]]\nprint('✅ Exercise 6 Passed!')"),

        ("Exercise 7: Finding the Second Largest Element without using sort()",
         "Given a list of numbers, find the second largest number in a single loop (O(N) time and O(1) space). If fewer than 2 distinct numbers exist, return `None`.",
         "def second_largest(nums: list[float]) -> float | None:\n    # TODO: Find 2nd largest in single pass\n    pass",
         "assert second_largest([10.5, 25.0, 4.0, 25.0, 18.0]) == 18.0\nassert second_largest([10, 10, 10]) == None\nassert second_largest([5]) == None\nprint('✅ Exercise 7 Passed!')"),

        # BATCH 2: Dictionaries & Sets Mastery
        ("Exercise 8: Frequency Counter using Standard Dictionary Loop",
         "Given a list of HTTP response codes `[200, 200, 500, 404, 200, 500, 429]`, count occurrences of each code using a standard loop and dictionary (without importing Counter).",
         "def count_frequencies(items: list) -> dict:\n    # TODO: Return {item: count}\n    pass",
         "codes = [200, 200, 500, 404, 200, 500, 429]\nexpected = {200: 3, 500: 2, 404: 1, 429: 1}\nassert count_frequencies(codes) == expected\nprint('✅ Exercise 8 Passed!')"),

        ("Exercise 9: Grouping Records by Category using Dictionary of Lists",
         "Given a list of claim dictionaries `[{'id': 'C1', 'specialty': 'Cardio'}, {'id': 'C2', 'specialty': 'Dental'}, {'id': 'C3', 'specialty': 'Cardio'}]`, group them into a dictionary mapping each `specialty` to a list of claim IDs.",
         "def group_claims_by_specialty(claims: list[dict]) -> dict[str, list[str]]:\n    # TODO: Group into dict of lists\n    pass",
         "claims = [\n    {'id': 'C1', 'specialty': 'Cardio'},\n    {'id': 'C2', 'specialty': 'Dental'},\n    {'id': 'C3', 'specialty': 'Cardio'},\n    {'id': 'C4', 'specialty': 'Dental'}\n]\nexpected = {'Cardio': ['C1', 'C3'], 'Dental': ['C2', 'C4']}\nassert group_claims_by_specialty(claims) == expected\nprint('✅ Exercise 9 Passed!')"),

        ("Exercise 10: Inverting a Dictionary (Handling One-to-Many)",
         "Given a dictionary mapping employee names to their department `{'Lokender': 'QA', 'Amit': 'Dev', 'Priya': 'QA'}`, write a function `invert_dict(d: dict) -> dict[str, list[str]]` that returns a dictionary mapping each department to a list of employees.",
         "def invert_dict(d: dict) -> dict[str, list[str]]:\n    # TODO: Invert dictionary\n    pass",
         "d = {'Lokender': 'QA', 'Amit': 'Dev', 'Priya': 'QA'}\nassert invert_dict(d) == {'QA': ['Lokender', 'Priya'], 'Dev': ['Amit']}\nprint('✅ Exercise 10 Passed!')"),

        ("Exercise 11: Merging Dictionaries with Summation on Key Collision",
         "Given two expense dictionaries for consecutive months `m1 = {'Dining': 400.0, 'Rent': 2000.0}` and `m2 = {'Dining': 350.0, 'Health': 150.0}`, write a function `merge_expenses(m1: dict, m2: dict) -> dict` that sums values when a key appears in both dictionaries.",
         "def merge_expenses(m1: dict, m2: dict) -> dict:\n    # TODO: Merge dictionaries and sum common keys\n    pass",
         "m1 = {'Dining': 400.0, 'Rent': 2000.0}\nm2 = {'Dining': 350.0, 'Health': 150.0}\nexpected = {'Dining': 750.0, 'Rent': 2000.0, 'Health': 150.0}\nassert merge_expenses(m1, m2) == expected\nprint('✅ Exercise 11 Passed!')"),

        ("Exercise 12: Dictionary Comprehension for Transforming API Data",
         "Given a dictionary of API user statuses `{'usr_1': 'ACTIVE', 'usr_2': 'INACTIVE', 'usr_3': 'ACTIVE'}`, use a dictionary comprehension to create a lookup `{user_id: True/False}` where value is `True` if status is `'ACTIVE'`.",
         "def transform_user_status(users: dict[str, str]) -> dict[str, bool]:\n    # TODO: Dictionary comprehension\n    pass",
         "users = {'usr_1': 'ACTIVE', 'usr_2': 'INACTIVE', 'usr_3': 'ACTIVE'}\nassert transform_user_status(users) == {'usr_1': True, 'usr_2': False, 'usr_3': True}\nprint('✅ Exercise 12 Passed!')"),

        ("Exercise 13: Set Operations for RBAC Permission Diffing",
         "Given `actual_permissions: list[str]` and `required_permissions: list[str]`, return a tuple of `(missing_permissions, unexpected_permissions)` using set operations (`set.difference`).",
         "def diff_permissions(actual: list[str], required: list[str]) -> tuple[set, set]:\n    # TODO: Use set difference\n    pass",
         "actual = ['READ', 'WRITE', 'EXECUTE']\nrequired = ['READ', 'WRITE', 'ADMIN']\nmissing, unexpected = diff_permissions(actual, required)\nassert missing == {'ADMIN'}\nassert unexpected == {'EXECUTE'}\nprint('✅ Exercise 13 Passed!')"),

        ("Exercise 14: Finding First Non-Repeating Character in a String",
         "Given a string `s = 'optumautomation'`, find the first character that does not repeat. If none exists, return `None`. (Use dict or set for frequency).",
         "def first_unique_char(s: str) -> str | None:\n    # TODO: Find first non-repeating char\n    pass",
         "assert first_unique_char('swiss') == 'w'\nassert first_unique_char('aabbcc') == None\nassert first_unique_char('optumautomation') == 'p'\nprint('✅ Exercise 14 Passed!')"),

        # BATCH 3: Lambda Functions, Custom Sorting & Built-in Functions
        ("Exercise 15: Sorting List of Dictionaries by Multiple Keys with Lambda",
         "Given a list of transactions, sort them first by `status` alphabetically ascending, and for identical statuses, by `amount` descending using `sorted(data, key=lambda x: (...))`.",
         "def sort_transactions(txs: list[dict]) -> list[dict]:\n    # TODO: Sort with lambda key\n    pass",
         "txs = [\n    {'id': 'T1', 'status': 'PAID', 'amount': 150},\n    {'id': 'T2', 'status': 'DENIED', 'amount': 400},\n    {'id': 'T3', 'status': 'PAID', 'amount': 900},\n    {'id': 'T4', 'status': 'DENIED', 'amount': 250}\n]\nres = sort_transactions(txs)\nassert [x['id'] for x in res] == ['T2', 'T4', 'T3', 'T1']\nprint('✅ Exercise 15 Passed!')"),

        ("Exercise 16: Finding Max and Min with Custom Lambda Keys",
         "Given a list of API latency logs `[{'endpoint': '/auth', 'ms': 120}, {'endpoint': '/claims', 'ms': 850}, {'endpoint': '/patients', 'ms': 45}]`, return the slowest endpoint and fastest endpoint as a tuple using `max()` and `min()` with a `key=lambda`.",
         "def find_slowest_and_fastest(logs: list[dict]) -> tuple[str, str]:\n    # TODO: Use max and min with key=lambda\n    pass",
         "logs = [{'endpoint': '/auth', 'ms': 120}, {'endpoint': '/claims', 'ms': 850}, {'endpoint': '/patients', 'ms': 45}]\nassert find_slowest_and_fastest(logs) == ('/claims', '/patients')\nprint('✅ Exercise 16 Passed!')"),

        ("Exercise 17: Validating Assertions using any() and all()",
         "Write a function `validate_test_suite_results(results: list[dict]) -> dict` that checks: 1) `all_passed` (True if all status == 'PASS'), 2) `has_critical_failure` (True if any failure has priority == 'P0'). Use `all()` and `any()`.",
         "def validate_test_suite_results(results: list[dict]) -> dict:\n    # TODO: Use all() and any()\n    pass",
         "suite1 = [{'status': 'PASS', 'priority': 'P0'}, {'status': 'PASS', 'priority': 'P1'}]\nassert validate_test_suite_results(suite1) == {'all_passed': True, 'has_critical_failure': False}\nsuite2 = [{'status': 'PASS', 'priority': 'P1'}, {'status': 'FAIL', 'priority': 'P0'}]\nassert validate_test_suite_results(suite2) == {'all_passed': False, 'has_critical_failure': True}\nprint('✅ Exercise 17 Passed!')"),

        ("Exercise 18: Filtering and Transforming with map() and filter() vs Comprehension",
         "Given a list of raw transaction amounts `['-50.0', '125.50', 'invalid', '800.00', '0.0']`, write a function `extract_positive_amounts(raw_values: list[str]) -> list[float]` that filters out invalid strings and values <= 0, returning clean floats.",
         "def extract_positive_amounts(raw_values: list[str]) -> list[float]:\n    # TODO: Clean and filter positive floats\n    pass",
         "raw = ['-50.0', '125.50', 'invalid', '800.00', '0.0']\nassert extract_positive_amounts(raw) == [125.50, 800.00]\nprint('✅ Exercise 18 Passed!')"),

        ("Exercise 19: Dynamic Filter Factory using Higher-Order Functions / Closures",
         "Write a function `create_amount_filter(min_val: float, max_val: float)` that returns a lambda/function `is_within_range(amount: float) -> bool` testing if an amount is between min_val and max_val inclusive.",
         "def create_amount_filter(min_val: float, max_val: float):\n    # TODO: Return a closure/lambda checking bounds\n    pass",
         "in_budget = create_amount_filter(100.0, 500.0)\nassert in_budget(250.0) == True\nassert in_budget(50.0) == False\nassert in_budget(600.0) == False\nprint('✅ Exercise 19 Passed!')"),

        ("Exercise 20: Sorting Dictionary Keys by Value using sorted() and lambda",
         "Given a category spend dictionary `{'Dining': 1200, 'Rent': 4500, 'Health': 800, 'Utilities': 1500}`, return a list of category names sorted from highest spend to lowest spend.",
         "def rank_categories_by_spend(spend_dict: dict[str, float]) -> list[str]:\n    # TODO: Return keys sorted by values descending\n    pass",
         "data = {'Dining': 1200, 'Rent': 4500, 'Health': 800, 'Utilities': 1500}\nassert rank_categories_by_spend(data) == ['Rent', 'Utilities', 'Dining', 'Health']\nprint('✅ Exercise 20 Passed!')"),

        ("Exercise 21: Aggregating Nested List of Dictionaries with lambda",
         "Given a list of department objects `[{'dept': 'QA', 'members': [{'name': 'A', 'salary': 50}, {'name': 'B', 'salary': 70}]}]`, calculate the total salary per department as `{dept: total_salary}`.",
         "def calculate_dept_salaries(depts: list[dict]) -> dict[str, float]:\n    # TODO: Aggregate salaries\n    pass",
         "depts = [\n    {'dept': 'QA', 'members': [{'name': 'A', 'salary': 50}, {'name': 'B', 'salary': 70}]},\n    {'dept': 'Dev', 'members': [{'name': 'C', 'salary': 100}]}\n]\nassert calculate_dept_salaries(depts) == {'QA': 120, 'Dev': 100}\nprint('✅ Exercise 21 Passed!')"),

        # BATCH 4: DateTime, Timedelta & String Manipulation
        ("Exercise 22: Calculating Turnaround Days with datetime and timedelta",
         "Given a claim submission date `'2026-10-15'` and adjudication date `'2026-10-28'`, write a function `calculate_turnaround_days(sub_date_str: str, adj_date_str: str) -> int` that returns the difference in calendar days.",
         "from datetime import datetime\n\ndef calculate_turnaround_days(sub_date_str: str, adj_date_str: str) -> int:\n    # TODO: Parse YYYY-MM-DD and return day difference\n    pass",
         "assert calculate_turnaround_days('2026-10-15', '2026-10-28') == 13\nprint('✅ Exercise 22 Passed!')"),

        ("Exercise 23: Filtering Records within Past N Days using timedelta",
         "Given a list of transactions with ISO timestamp strings, write a function `filter_recent_transactions(records: list[dict], reference_date: datetime, days: int) -> list[dict]` that returns only transactions that occurred within `days` before `reference_date`.",
         "from datetime import datetime, timedelta\n\ndef filter_recent_transactions(records: list[dict], reference_date: datetime, days: int) -> list[dict]:\n    # TODO: Filter using timedelta\n    pass",
         "ref = datetime(2026, 10, 30)\nrecords = [\n    {'id': 'T1', 'date': '2026-10-29'},\n    {'id': 'T2', 'date': '2026-10-15'},\n    {'id': 'T3', 'date': '2026-09-01'}\n]\nres = filter_recent_transactions(records, ref, days=20)\nassert [r['id'] for r in res] == ['T1', 'T2']\nprint('✅ Exercise 23 Passed!')"),

        ("Exercise 24: Parsing Multiple Variable Date Formats",
         "Incoming API payloads have inconsistent date strings: some are `'2026-10-30'`, some `'30/10/2026'`, and some `'Oct 30, 2026'`. Write a function `normalize_date_to_iso(date_str: str) -> str` that parses whichever format is passed and returns `'2026-10-30'`.",
         "from datetime import datetime\n\ndef normalize_date_to_iso(date_str: str) -> str:\n    formats = ['%Y-%m-%d', '%d/%m/%Y', '%b %d, %Y']\n    # TODO: Try parsing each format and return formatted ISO string\n    pass",
         "assert normalize_date_to_iso('2026-10-30') == '2026-10-30'\nassert normalize_date_to_iso('30/10/2026') == '2026-10-30'\nassert normalize_date_to_iso('Oct 30, 2026') == '2026-10-30'\nprint('✅ Exercise 24 Passed!')"),

        ("Exercise 25: String Masking for PII (Credit Cards & Phone Numbers)",
         "Write a function `mask_pii(text: str) -> str` that replaces 10-digit phone numbers with `'XXXXXX' + last4` and 16-digit card numbers with `'XXXX-XXXX-XXXX-' + last4`.",
         "import re\n\ndef mask_pii(text: str) -> str:\n    # TODO: Use regex sub to mask sensitive digits\n    pass",
         "assert mask_pii('Call 9876543210') == 'Call XXXXXX3210'\nprint('✅ Exercise 25 Passed!')"),

        ("Exercise 26: Longest Common Prefix for API Endpoint Routes",
         "Given a list of API routes `['/api/v1/claims/submit', '/api/v1/claims/status', '/api/v1/claims/history']`, find the longest common path prefix (should return `'/api/v1/claims/'`).",
         "def longest_common_prefix(routes: list[str]) -> str:\n    # TODO: Find longest common prefix string\n    pass",
         "routes = ['/api/v1/claims/submit', '/api/v1/claims/status', '/api/v1/claims/history']\nassert longest_common_prefix(routes) == '/api/v1/claims/'\nprint('✅ Exercise 26 Passed!')"),

        ("Exercise 27: Extracting Query Parameters from URL into Dictionary",
         "Given a URL string `'https://api.optum.com/claims?patient_id=PAT-001&status=PAID&limit=25'`, parse the query string into a dictionary `{'patient_id': 'PAT-001', 'status': 'PAID', 'limit': '25'}` without using urllib.",
         "def parse_query_params(url: str) -> dict[str, str]:\n    # TODO: Parse query parameters into dict\n    pass",
         "url = 'https://api.optum.com/claims?patient_id=PAT-001&status=PAID&limit=25'\nexpected = {'patient_id': 'PAT-001', 'status': 'PAID', 'limit': '25'}\nassert parse_query_params(url) == expected\nprint('✅ Exercise 27 Passed!')"),

        ("Exercise 28: Validating Balanced JSON Brackets with a Stack",
         "Given a string containing payload brackets `'({[]})'`, write a function `is_valid_brackets(s: str) -> bool` using a list as a stack to verify brackets are closed in proper order.",
         "def is_valid_brackets(s: str) -> bool:\n    # TODO: Stack-based bracket matcher\n    pass",
         "assert is_valid_brackets('({[]})') == True\nassert is_valid_brackets('([)]') == False\nassert is_valid_brackets('((') == False\nprint('✅ Exercise 28 Passed!')"),

        # BATCH 5: Real-World SDET Data Validation
        ("Exercise 29: Deep JSON Diffing (Ignoring Dynamic Timestamps)",
         "Write a recursive function `diff_json(expected: dict, actual: dict, ignore_keys: set = {'timestamp', 'id'}) -> list[str]` that reports any mismatched values or missing keys.",
         "def diff_json(expected: dict, actual: dict, ignore_keys: set = None) -> list[str]:\n    # TODO: Recursive dict comparison\n    pass",
         "exp = {'status': 200, 'data': {'user': 'Lokender', 'id': 'temp-1', 'role': 'SDET'}}\nact = {'status': 200, 'data': {'user': 'Lokender', 'id': 'temp-2', 'role': 'Admin'}}\ndiffs = diff_json(exp, act, ignore_keys={'id'})\nassert len(diffs) == 1 and 'role' in diffs[0]\nprint('✅ Exercise 29 Passed!')"),

        ("Exercise 30: Validating Required Fields & Data Types in API Responses",
         "Write a function `validate_schema(payload: dict, expected_schema: dict) -> list[str]` that checks: 1) all keys in `expected_schema` exist in `payload`, 2) `isinstance(payload[k], expected_schema[k])` holds true.",
         "def validate_schema(payload: dict, expected_schema: dict) -> list[str]:\n    # TODO: Return list of error messages\n    pass",
         "schema = {'claim_id': str, 'amount': (int, float), 'is_approved': bool}\npayload = {'claim_id': 'C100', 'amount': 'not_numeric'}\nerrors = validate_schema(payload, schema)\nassert len(errors) == 2  # wrong type for amount, missing is_approved\nprint('✅ Exercise 30 Passed!')"),

        ("Exercise 31: Regex Parsing of Production Server Log Files",
         "Given a production log line `'2026-10-30 14:05:22 [ERROR] 500 /api/claims - DB connection timed out'`, extract `timestamp`, `level`, `status_code`, `endpoint`, and `message` using regex named groups.",
         "import re\n\ndef parse_log_line(log_line: str) -> dict:\n    # TODO: Regex with named groups\n    pass",
         "log_line = '2026-10-30 14:05:22 [ERROR] 500 /api/claims - DB connection timed out'\nres = parse_log_line(log_line)\nassert res['status_code'] == '500'\nassert res['level'] == 'ERROR'\nassert res['endpoint'] == '/api/claims'\nprint('✅ Exercise 31 Passed!')"),

        ("Exercise 32: Flattening Nested JSON Dictionaries",
         "Write a function `flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict` that converts nested objects into single-level dot-notation keys (`{'a': {'b': 10}} -> {'a.b': 10}`).",
         "def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:\n    # TODO: Recursively flatten dict\n    pass",
         "sample = {'user': {'name': 'Lokender', 'auth': {'role': 'Senior SDET'}}}\nflat = flatten_dict(sample)\nassert flat == {'user.name': 'Lokender', 'user.auth.role': 'Senior SDET'}\nprint('✅ Exercise 32 Passed!')"),

        ("Exercise 33: Safely Extracting Deeply Nested Keys without KeyError",
         "Write a function `safe_get(data: dict, dot_path: str, default=None)` that retrieves `'data.claims.0.patient_id'` safely, returning `default` if any key or index is missing.",
         "def safe_get(data: dict, dot_path: str, default=None):\n    # TODO: Safe traversal\n    pass",
         "data = {'claims': [{'id': 'C1', 'patient': {'name': 'John'}}]}\nassert safe_get(data, 'claims.0.patient.name') == 'John'\nassert safe_get(data, 'claims.0.doctor.name', 'N/A') == 'N/A'\nassert safe_get(data, 'claims.5.id', None) == None\nprint('✅ Exercise 33 Passed!')"),

        ("Exercise 34: Data Cleansing & Deduplicating Transaction Stream",
         "Given a list of transactions where some are missing required keys (`id`, `amount`) and some have negative amounts, filter out invalid records and return clean deduplicated transactions kept by highest amount.",
         "def clean_and_dedup_transactions(records: list[dict]) -> list[dict]:\n    # TODO: Validate and dedup by highest amount\n    pass",
         "txs = [\n    {'id': 'T1', 'amount': 100.0},\n    {'id': 'T1', 'amount': 250.0}, # duplicate ID with higher amount\n    {'id': 'T2', 'amount': -50.0}, # invalid amount\n    {'amount': 80.0}              # missing ID\n]\ncleaned = clean_and_dedup_transactions(txs)\nassert len(cleaned) == 1 and cleaned[0] == {'id': 'T1', 'amount': 250.0}\nprint('✅ Exercise 34 Passed!')"),

        # BATCH 6: Core OOP & Test Utilities
        ("Exercise 35: Light OOP - Simple Claim Entity with Validation",
         "Create a class `PatientClaim` with attributes `claim_id: str`, `amount: float`, `status: str`. In `__init__`, raise `ValueError` if `amount <= 0`. Add method `approve()` which sets status to `'APPROVED'`.",
         "class PatientClaim:\n    def __init__(self, claim_id: str, amount: float, status: str = 'PENDING'):\n        # TODO: Initialize and validate\n        pass\n\n    def approve(self):\n        # TODO: Set status to APPROVED\n        pass",
         "c = PatientClaim('CLM1', 500.0)\nassert c.status == 'PENDING'\nc.approve()\nassert c.status == 'APPROVED'\ntry:\n    PatientClaim('CLM2', -100.0)\n    assert False\nexcept ValueError:\n    pass\nprint('✅ Exercise 35 Passed!')"),

        ("Exercise 36: OOP Inheritance - BaseTest to ApiTest",
         "Create a base class `BaseTestCase` taking `test_name: str` and `timeout: int = 30`. Create derived class `ApiTestCase` that adds `base_url: str`, calls `super().__init__()`, and has method `get_full_url(endpoint: str)`.",
         "class BaseTestCase:\n    def __init__(self, test_name: str, timeout: int = 30):\n        # TODO: Base init\n        pass\n\nclass ApiTestCase(BaseTestCase):\n    def __init__(self, test_name: str, base_url: str, timeout: int = 30):\n        # TODO: super().__init__ and base_url\n        pass\n\n    def get_full_url(self, endpoint: str) -> str:\n        # TODO: Combine base_url and endpoint\n        pass",
         "t = ApiTestCase('Auth Test', 'https://api.optum.com')\nassert t.test_name == 'Auth Test'\nassert t.get_full_url('/v1/token') == 'https://api.optum.com/v1/token'\nprint('✅ Exercise 36 Passed!')"),

        ("Exercise 37: Retry Function with While Loop and Delays",
         "Write a function `execute_with_retry(action_fn, max_retries: int = 3) -> any` that invokes `action_fn()`. If it raises an exception, catch it and retry up to `max_retries`. If it still fails, re-raise the exception.",
         "def execute_with_retry(action_fn, max_retries: int = 3):\n    # TODO: While loop retry\n    pass",
         "count = 0\ndef flaky():\n    nonlocal count\n    count += 1\n    if count < 3: raise RuntimeError('Temporary network blip')\n    return 'SUCCESS'\n\nassert execute_with_retry(flaky, 3) == 'SUCCESS'\nassert count == 3\nprint('✅ Exercise 37 Passed!')"),

        ("Exercise 38: Two-Sum Target Budget Matcher",
         "Given a list of numbers `[120.0, 450.0, 300.0, 550.0]` and a target budget `750.0`, return the indices of the two numbers that sum up to target in O(N) time using a dictionary.",
         "def two_sum_indices(amounts: list[float], target: float) -> tuple[int, int] | None:\n    # TODO: O(N) hash map solution\n    pass",
         "assert two_sum_indices([120.0, 450.0, 300.0, 550.0], 750.0) == (1, 2)\nprint('✅ Exercise 38 Passed!')"),

        ("Exercise 39: Generating Test Matrix Cartesians with itertools / loops",
         "Given `browsers = ['chromium', 'firefox']` and `resolutions = ['desktop', 'mobile']`, generate a list of all combination tuples `[('chromium', 'desktop'), ...]` using a list comprehension.",
         "def generate_matrix(browsers: list[str], resolutions: list[str]) -> list[tuple[str, str]]:\n    # TODO: List comprehension cartesian product\n    pass",
         "expected = [('chromium', 'desktop'), ('chromium', 'mobile'), ('firefox', 'desktop'), ('firefox', 'mobile')]\nassert generate_matrix(['chromium', 'firefox'], ['desktop', 'mobile']) == expected\nprint('✅ Exercise 39 Passed!')"),

        ("Exercise 40: Concurrent Endpoint Health Checks (ThreadPoolExecutor)",
         "Write a function `ping_endpoints(urls: list[str]) -> dict[str, bool]` that runs a dummy check concurrently using `concurrent.futures.ThreadPoolExecutor`.",
         "from concurrent.futures import ThreadPoolExecutor\n\ndef ping_mock(url: str) -> bool:\n    return True\n\ndef ping_endpoints(urls: list[str]) -> dict[str, bool]:\n    # TODO: Parallel execution with ThreadPoolExecutor\n    pass",
         "res = ping_endpoints(['/auth', '/claims', '/health'])\nassert len(res) == 3 and all(res.values())\nprint('✅ Exercise 40 Passed!')")
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
    print("Regenerated notebooks/01_python_sdet_mastery.ipynb with SDET-focused syllabus!")

if __name__ == "__main__":
    generate_sdet_focused_python_nb()

