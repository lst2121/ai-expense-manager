# 🐍 PYTHON SDET CONCEPTUAL GUIDE
**Target**: Understanding the Core Mechanics & Mental Models for SDET Technical Interviews  
*Note: This document contains conceptual explanations, syntax patterns, and underlying principles. No direct problem solutions are given so you can implement them yourself in `notebooks/01_python_sdet_mastery.ipynb`.*

---

## 1. Lists, Loops & Comprehensions

### List Comprehension Mental Model
A list comprehension is a concise, memory-optimized way to construct a new list by applying an expression to each element of an iterable, optionally filtering with an `if` condition.

- **Basic Pattern**:
  ```python
  [expression for item in iterable if condition]
  ```
- **How Python Executes It**:
  1. Iterates over `iterable`.
  2. Evaluates `condition`. If `False`, skips to the next item.
  3. If `True`, evaluates `expression` and appends the result into the newly constructed list.
- **Nested List Comprehension (Flattening a 2D Matrix)**:
  Think of the order as identical to standard nested `for` loops written in plain text:
  ```python
  # Plain loops:
  result = []
  for sublist in matrix:
      for item in sublist:
          result.append(item)

  # Equivalent List Comprehension:
  [item for sublist in matrix for item in sublist]
  ```
  *Key Rule*: Outer loop comes first, inner loop comes second.

### `enumerate(iterable, start=0)`
Never use manual index counter variables (`i = 0; i += 1`). `enumerate()` wraps an iterable in an iterator yielding `(index, item)` tuples.
- **SDET Use Case**: Finding failed step numbers in a sequential execution log, tracking row numbers in CSV tables.

### `zip(*iterables)`
`zip()` pairs elements from two or more iterables position-by-position, stopping when the shortest iterable is exhausted (or use `itertools.zip_longest` to pad).
- **SDET Use Case**: Pairing a list of input prompts with a list of expected HTTP status codes to generate test-data dictionaries.

### Memory-Preserving Deduplication in $O(N)$ Time
- Checking `if item not in result_list` inside a loop results in **$O(N^2)$** complexity because `in` on a list scans linearly.
- **The $O(N)$ Pattern**: Maintain a companion `seen = set()`. Set lookups are $O(1)$ on average (hash-based).
  1. For each item: check `if item not in seen:`.
  2. If not seen, add to `seen` and append to `result_list`. This preserves the exact first-seen order.

### Slicing and List Chunking
Python slicing `data[start:stop:step]` creates a shallow copy of a sub-range.
- Chunking into fixed-size batches of size $K$:
  ```python
  for i in range(0, len(data), K):
      chunk = data[i : i + K]
  ```
- **SDET Use Case**: Batching 5,000 transaction IDs into chunks of 100 to avoid overwhelming an API batch endpoint.

### Single-Pass Second Largest ($O(N)$ Time, $O(1)$ Space)
Sorting a list to find the second largest takes $O(N \log N)$ time. An interviewer will ask: *"Can you find it in a single pass without sorting?"*
- **Mechanism**:
  - Maintain `first = float('-inf')` and `second = float('-inf')`.
  - Iterate through numbers:
    - If `num > first`: `second` becomes `first`, and `first` becomes `num`.
    - Else if `first > num > second`: `second` becomes `num`.
  - If `second` remains `-inf`, fewer than 2 distinct numbers existed.

---

## 2. Dictionaries & Sets Mastery

### Dictionary Frequency Counter Pattern
Counting occurrences of elements (status codes, errors, words) without `collections.Counter`:
- **Pattern 1 (`dict.get`)**:
  ```python
  counts[item] = counts.get(item, 0) + 1
  ```
- **Pattern 2 (`dict.setdefault`)**:
  `counts.setdefault(key, default)` returns the existing value if `key` exists; if not, sets `key = default` and returns `default`.

### Grouping Records into a Dictionary of Lists
When grouping flat records (e.g., transactions by category, employees by department):
```python
groups = {}
for record in records:
    key = record['category']
    groups.setdefault(key, []).append(record['id'])
```

### Inverting a Dictionary (Handling One-to-Many Mappings)
If multiple keys share the same value (e.g. `{'Lokender': 'QA', 'Priya': 'QA'}`), the inverted dictionary cannot be a 1-to-1 mapping or values will overwrite each other. The inverted dictionary must map each unique value to a list of keys:
```python
inverted = {}
for k, v in original.items():
    inverted.setdefault(v, []).append(k)
```

### Merging Dictionaries with Collision Handling
- In Python 3.9+, `d1 | d2` merges two dictionaries, but if a key collides, `d2` silently overwrites `d1`.
- When business logic requires **summing** or **combining** colliding keys (e.g., total spending across consecutive months), you must iterate through keys or build a new dictionary:
  - Copy `d1`.
  - For `k, v` in `d2`: add `v` to `result[k]` if `k` exists, else set `result[k] = v`.

### Set Operations for RBAC & Assertion Diffing
Sets are unordered collections of unique, hashable elements.
- **Difference (`A - B`)**: Elements in $A$ but NOT in $B$. (e.g., unexpected/extra permissions granted).
- **Difference (`B - A`)**: Elements in $B$ but NOT in $A$. (e.g., missing required permissions).
- **Intersection (`A & B`)**: Elements common to both.
- **Symmetric Difference (`A ^ B`)**: Elements in either $A$ or $B$, but not in both.

---

## 3. Lambda Functions, Custom Sorting & Built-in Functions

### What is a Lambda Function?
A `lambda` is an anonymous, single-line function defined using `lambda args: expression`. It implicitly returns the result of the expression.

### Sorting with Custom `key=lambda`
`sorted(iterable, key=function, reverse=False)` sorts elements based on the proxy value returned by `function(item)`.
- **Multi-Key Sorting (Ascending & Descending Mix)**:
  When sorting by `status` alphabetically ascending, and for tied statuses, by `amount` descending:
  ```python
  sorted(items, key=lambda x: (x['status'], -x['amount']))
  ```
  *(Note: Negating a numeric value (`-x['amount']`) flips its sort order to descending while keeping strings ascending).*

### `min()` and `max()` with Custom Keys
Instead of sorting the entire list (which takes $O(N \log N)$), `min(data, key=lambda x: x['ms'])` and `max(data, key=lambda x: x['ms'])` find the extreme items in a single $O(N)$ pass.

### `all()` and `any()` for Assertion Checks
- `all(iterable)`: Returns `True` if **every** element in the iterable is truthy. Short-circuits (stops immediately) upon hitting the first `False`.
- `any(iterable)`: Returns `True` if **at least one** element in the iterable is truthy. Short-circuits upon hitting the first `True`.
- **SDET Pattern**:
  ```python
  all_passed = all(r['status'] == 'PASS' for r in test_results)
  has_p0_bug = any(r['priority'] == 'P0' and r['status'] == 'FAIL' for r in test_results)
  ```

---

## 4. DateTime & Timedelta Math

### Parsing Strings to Dates (`strptime`) vs Formatting Dates (`strftime`)
- **Mnemonic**:
  - `p` = **Parse** string into `datetime` object.
  - `f` = **Format** `datetime` object into string.
- Common Directives:
  - `%Y`: 4-digit year (`2026`)
  - `%m`: 2-digit month (`01`-`12`)
  - `%d`: 2-digit day (`01`-`31`)
  - `%b`: Abbreviated month (`Oct`, `Nov`)
  - `%H`: 24-hour hour (`00`-`23`)
  - `%M`: Minute (`00`-`59`)
  - `%S`: Second (`00`-`59`)

### `timedelta` Arithmetic
Subtracting two `datetime` objects returns a `timedelta` object:
```python
diff = end_date - start_date
days_int = diff.days
```
Adding or subtracting a `timedelta` creates a shifted `datetime`:
```python
cutoff_date = reference_date - timedelta(days=30)
```
- **SDET Use Case**: Calculating claim adjudication SLA turnaround, verifying session token expiry times, filtering records within the last $N$ days.

---

## 5. String Manipulation, Regex & Data Validation

### Regex Named Groups (`(?P<name>pattern)`)
When parsing raw server logs, instead of using index-based regex matches (`m.group(1)`), use named groups:
```python
pattern = r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>[A-Z]+)\] (?P<status>\d{3}) (?P<endpoint>\S+) - (?P<msg>.+)'
match = re.search(pattern, log_line)
if match:
    data = match.groupdict() # returns dict with keys: timestamp, level, status, endpoint, msg
```

### Recursive JSON Diffing (Deep Diff)
When comparing two JSON payloads (e.g., API response vs DB record), you must recursively traverse nested structures:
1. Base cases: If one is a `dict` and the other is not $\rightarrow$ mismatch.
2. If both are `dict`:
   - Identify missing keys in either dictionary.
   - For common keys: if the key is in `ignore_keys` (like `timestamp` or `auto_generated_id`), skip it.
   - If values are dictionaries, recurse: `diff_json(val1, val2, path + '.' + k)`.
   - If values are primitives, assert equality.

### Safe Nested Key Traversal
Accessing `data['user']['profile']['address']['city']` crashes with `KeyError` or `TypeError` if any key in the chain is missing or `None`.
- **The Safe Pattern**: Split the dot path `'user.profile.address.city'.split('.')`. Iterate through parts, updating `current = current.get(part)` while `current` is a dictionary; if `current is None` at any step, return `default`.

### Stack Pattern for Bracket Matching
Validating balanced brackets (`{}[]()`) in raw strings:
- Maintain an empty `stack = []`.
- When encountering an opening bracket (`{`, `[`, `(`), push it onto the stack.
- When encountering a closing bracket, check if the stack is non-empty and whether the top matches the corresponding opening bracket (`map[closing] == stack.pop()`).
- At the end, the string is valid only if `len(stack) == 0`.

