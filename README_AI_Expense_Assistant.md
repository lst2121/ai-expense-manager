
# 🧾 AI Expense Assistant – README

An agentic AI app for analyzing household expenses using LangGraph (LLM orchestration), Pandas (for expense data), and Gradio (for ChatGPT-style UI).

---

## ✅ Current Status

- ✅ **Agentic reasoning flow** using LangGraph.
- ✅ **Tool suite implemented**: monthly summaries, category queries, comparisons, and memory summarization.
- ✅ **Chat-style UI** using Gradio with:
  - Query input + "Send" button
  - 3 autosuggest queries
  - Scrollable chat history
- ✅ **Clean architecture**: modular tools, stateful execution, memory tracking.
- ❌ **Charts removed** (for now, to keep UI clean).
- 🟢 Ready for **CSV upload**, **multi-step planning**, and **user profiles** next.

---

## 🏗️ Architecture Overview

```
📁 ai-expense-manager/
.
├── .env
├── .gitignore
├── .gradio
│   └── flagged
│       └── dataset1.csv
├── LICENSE
├── README.md
├── README_AI_Expense_Assistant.md
├── app
│   ├── gradio_ui.py
│   └── gradio_ui_rag.py
├── data
│   └── sample_expense.csv
├── expense_manager
│   ├── __init__.py
│   ├── chains
│   │   ├── __init__.py
│   │   └── expense_chain.py
│   ├── config.py
│   ├── utils
│   │   ├── __init__.py
│   │   └── csv_loader.py
│   └── vector_store
│       ├── __init__.py
│       ├── document_loader.py
│       ├── embedder.py
│       ├── retriever_chain.py
│       └── vector_db.py
├── folder_structure.txt
├── langgraph_app
│   ├── __init__.py
│   ├── graph.py
│   └── nodes
│       ├── retrieve_memory_node.py
│       ├── rewrite_agent_node.py
│       └── tool_executor_node.py
├── main.py
├── notebooks
│   ├── eda.ipynb
│   ├── expense_graph_viz.pdf
│   ├── expense_graph_viz.png
│   ├── graph_visualization.ipynb
│   └── vector_store.ipynb
├── requirements.txt
├── scripts
│   └── generate_sample_csv.py
├── test_langgraph_chart_runner.py
├── test_langgraph_runner.py
├── test_tool_runner.py
├── tools
│   ├── compare_months_tool.py
│   ├── date_range_expense_tool.py
│   ├── fallback_tool.py
│   ├── monthly_expenses_tool.py
│   ├── query_dataframe_tool.py
│   ├── sum_category_expenses_tool.py
│   ├── summarize_memory_tool.py
│   ├── top_expenses_tool.py
│   └── utils.py
└── vector_store
    └── faiss_index

15 directories, 46 files

---

## 🧠 LangGraph Agent

- **Agent State (`ExpenseAgentState`)** stores:
  - `query`: current user input
  - `tool_input`: parsed tool and args
  - `result`: last tool response
  - `memory`: previous tool executions

- **Graph Flow:**
  ```
  rewrite_query → retrieve_memory → execute_tool → END
  ```

- **Compiled Graph** is imported as `expense_analysis_app`.

---

## 🛠️ Tools (in `/tools`) – Working

| Tool Name                    | Function                                                |
|-----------------------------|---------------------------------------------------------|
| `monthly_expenses_tool`     | List total & individual expenses by month (opt. category) |
| `compare_months_tool`       | Compare expenses between two months                     |
| `sum_category_expenses_tool`| Total for a category across months                      |
| `summarize_memory_tool`     | Aggregate past tool runs (used for memory)              |
| `date_range_expense_tool`   | Filter expenses in a custom date range                  |
| `fallback_tool`             | Handles unknown queries gracefully                      |

> All tools are decorated with `@tool` from LangChain Core and registered in a central `TOOL_REGISTRY`.

---

## 💬 Gradio Chat UI

### Main Features:
- Styled like Groq/ChatGPT:
  - White background, rounded input, clean buttons
- Scrollable chat log (markdown-based)
- Input via:
  - Textbox with Enter
  - Send Button
- **Autosuggested Prompts**:
  - “How much did I spend last month?”
  - “Compare shopping vs groceries.”
  - “Show my top 3 expenses.”

### File: `app/gradio_ui.py`

- Loads state: `{"df", "memory"}`
- On `query.submit` or `send.click`, invokes LangGraph
- Appends response to chat log
- Handles initial UI reset via `demo.load(...)`

---

## 📦 Data

### Sample DF used (in-memory for now):

```csv
Date,Category,Amount,Notes
2025-06-20,Rent,2300.00,Monthly Rent
2025-06-15,Groceries,750.25,Big Bazaar
2025-06-10,Shopping,1450.00,Flipkart
2025-06-04,Subscriptions,485.52,Netflix
2025-05-22,Shopping,1200.00,Amazon
2025-05-10,Groceries,670.00,Local Store
```

---

## 🧪 How to Run

### 1. Local test runner
```bash
python test_langgraph_runner.py
```

### 2. Gradio app
```bash
python -m app.gradio_ui
```

Access: http://localhost:7860

---

## 🔜 Next Milestones

| Feature                    | Status   | Notes |
|---------------------------|----------|-------|
| 📂 CSV Upload             | ⏳ Pending | Upload real data via UI |
| 🔁 Multi-step Planning     | ⏳ Pending | Agent breaks down complex queries |
| 👥 Multi-user Memory       | ⏳ Pending | Store chat sessions per user |
| 📤 Export Data             | ⏳ Pending | Export filtered data as CSV/PDF |
| 🧠 Fuzzy Category Matching | ✅ Done    | Robust query parsing |

---

## ✨ Sample Queries to Try

- "Compare May and June spending"
- "How much did I spend on groceries?"
- "Summarize my past spending"
- "What about subscriptions?"
