# DuckDB Tools Infrastructure

## 🎯 Overview

SQL-powered expense analysis tools using DuckDB for high-performance data processing. This infrastructure replaces Pandas-based tools with SQL queries for better scalability and performance.

## 📁 Structure

```
duckdb_tools/
├── core/
│   ├── duckdb_manager.py      # Core DuckDB operations
│   └── chart_generator.py     # Plotly chart generation
├── tools/
│   └── sum_category_expenses_tool.py  # First migrated tool
├── utils/
│   ├── sql_helpers.py         # SQL query builders
│   └── date_utils.py          # Date parsing utilities
└── tests/
    └── test_duckdb_manager.py # Unit tests
```

## 🚀 Core Components

### DuckDBManager
- **Database operations:** CSV loading, SQL queries, schema management
- **Persistent storage:** `data/expenses.duckdb`
- **Automatic indexing:** Date and Category columns
- **Views:** Pre-built aggregations for common queries

### PlotlyChartGenerator
- **Interactive charts:** Bar, line, pie, horizontal bar charts
- **Base64 encoding:** For Streamlit integration
- **Error handling:** Graceful fallbacks for empty data
- **Theming:** Consistent visual style

### SQLQueryBuilder
- **Fuzzy matching:** Category name matching
- **Date parsing:** Multiple format support
- **Query construction:** Dynamic SQL building
- **Filtering:** Category and date filters

## 🛠️ Tools

### sum_category_expenses_tool
- **Purpose:** Sum expenses by category
- **SQL-based:** Efficient aggregation queries
- **Fuzzy matching:** Handles category name variations
- **Date filtering:** Optional month filtering
- **Output:** Text summary only

## 📊 Data Flow

```
CSV → DuckDBManager.load_csv() → expenses.duckdb
Tool Request → SQL Query → fetchdf() → Plotly Chart → Base64
```

## 🧪 Testing

### Infrastructure Test
```bash
python test_duckdb_infrastructure.py
```

### Unit Tests
```bash
python -m unittest duckdb_tools/tests/test_duckdb_manager.py
```

## 📈 Performance Benefits

- **Large CSV support:** DuckDB handles GB+ files efficiently
- **SQL optimization:** Automatic query optimization
- **Memory efficient:** Columnar storage
- **Scalable:** Handles millions of rows

## 🔧 Usage Example

```python
from duckdb_tools.core.duckdb_manager import DuckDBManager
from duckdb_tools.tools.sum_category_expenses_tool import sum_category_expenses_tool

# Load data
db_manager = DuckDBManager()
db_manager.load_csv_to_table("data/sample_expense.csv", "expenses")

# Use tool
result = sum_category_expenses_tool.invoke({
    "category": "grocery",
    "month": "2025-01"
})
print(result["text"])
```

## 🎯 Next Steps

1. **Migrate remaining tools:** top_expenses_tool, category_summary_tool
2. **Add chart generation:** For tools that need visualizations
3. **Performance testing:** Large dataset benchmarks
4. **Integration:** Update LangGraph nodes and Streamlit components

## 📋 Dependencies

- `duckdb==0.9.2`
- `plotly==5.17.0`
- `pandas==2.3.0` (for DataFrame operations)
- `langchain-core` (for tool decorators) 