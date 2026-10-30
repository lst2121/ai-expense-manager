# 🎓 SDET INTERVIEW MASTERY STUDY PACKAGE
**Candidate**: Lokender Singh | **Target Role**: Automation Test Engineer / SDET  
**Client**: Optum (via York Solutions) | **Date**: 3 November 2026

Welcome to your complete, self-contained offline study package. Every concept, theory, formula, CLI command, and architectural pattern is organized into standalone Markdown guides with **zero code spoilers**, allowing you to read the concept, understand the underlying mental model, and write the code yourself.

---

## 📚 Study Package Directory Index

| Guide | Core Focus Areas | Hands-On Practice Target |
| :--- | :--- | :--- |
| **[`01_PYTHON_SDET_CONCEPTS.md`](./01_PYTHON_SDET_CONCEPTS.md)** | List & Dict Comprehensions, Nested loops, Slicing, Grouping, Frequency maps, Lambdas, Multi-key sorting, DateTime/Timedelta math, Regex log parsing, Deep JSON diffing, Safe nested traversal. | [`notebooks/01_python_sdet_mastery.ipynb`](../notebooks/01_python_sdet_mastery.ipynb) |
| **[`02_SQL_SDET_CONCEPTS.md`](./02_SQL_SDET_CONCEPTS.md)** | Execution lifecycle, Aggregations, HAVING vs WHERE, INNER/LEFT Joins, Anti-joins / orphan checks, Window functions (`ROW_NUMBER`, `RANK`, `DENSE_RANK`), Running totals, `LEAD`/`LAG`, CTEs, Double-entry balance, Row locking. | [`notebooks/02_sql_sdet_mastery.ipynb`](../notebooks/02_sql_sdet_mastery.ipynb) |
| **[`03_PLAYWRIGHT_TS_PRACTICE_GUIDE.md`](./03_PLAYWRIGHT_TS_PRACTICE_GUIDE.md)** | Complete CLI installation from scratch, `playwright.config.ts` options deep dive, WebSocket vs WebDriver architecture, User-facing locators (`getByRole`), Strict mode, Iframes, Shadow DOM, Popups, 5 Actionability checks, Web-first assertions, Page Object Model, Custom fixtures (`test.extend`), API testing via `APIRequestContext`, Trace Viewer, and 4 Step-by-Step Challenges. | [`automation/ui/`](../automation/ui/) |
| **[`04_PYTEST_AND_PYTHON_OOPS.md`](./04_PYTEST_AND_PYTHON_OOPS.md)** | Virtual environment setup, Pytest CLI flags (`-v`, `-s`, `-k`, `-m`, `--lf`, `-n auto`), AST assertion rewriting, The 5 Fixture Scopes (`function`, `class`, `module`, `package`, `session`), Cascading `conftest.py`, Parameterization (`@pytest.mark.parametrize`), `unittest.mock.patch` golden rules, Base test classes, Abstract Base Classes (`abc.ABC`), Custom context managers. | [`backend/tests/`](../backend/tests/) |
| **[`05_AI_EVALUATION_DEEPEVAL_LANGFUSE.md`](./05_AI_EVALUATION_DEEPEVAL_LANGFUSE.md)** | AI testing paradigm shift, Data validation vs Metric evaluation, DeepEval `LLMTestCase`, Formulas for **Faithfulness**, **Answer Relevancy**, **Hallucination**, Contextual Precision/Recall, GEval rubrics, Zero-cost custom LLM judges (`DeepEvalBaseLLM`), Golden datasets, Langfuse Traces/Spans/Generations, Agent tool tracking, and score linking. | [`backend/tests/evals/`](../backend/tests/evals/) |
| **[`06_TYPESCRIPT_FOR_SDET_INTERVIEWS.md`](./06_TYPESCRIPT_FOR_SDET_INTERVIEWS.md)** | **Theory-Only Master Guide for Interviews**: Type Erasure, `interface` vs `type` in frameworks, `any` vs `unknown` vs `never` vs `void`, Type Narrowing & Custom Type Guards (`is`), Generics (`<T>`) in fixtures/API wrappers, Utility Types (`Partial`, `Required`, `Readonly`, `Pick`, `Omit`, `Record`), Unions vs Enums, Event Loop (Microtasks vs Macrotasks), and Top 10 TS SDET Interview Questions. | Verbal Interview Mastery |

---

## ⚡ How to Use This Package

1. **Keep These Files Open Side-by-Side in VS Code**:
   - You don't need to switch back to chat. Open the relevant `.md` guide in your left split, and your Jupyter Notebook or TypeScript file in your right split.
2. **Read the Concept $\rightarrow$ Write the Implementation**:
   - Check the syntax pattern, CLI commands, and mental model in the guide.
   - Switch to your code cell or test file and write the solution yourself from scratch.
3. **Verify Locally**:
   - For Python: Run the notebook assertion cell (`assert ... == expected`).
   - For SQL: Run `run_sql(query, 'health')` to see the live Pandas DataFrame.
   - For Playwright: Run `npx playwright test --project=chromium`.
