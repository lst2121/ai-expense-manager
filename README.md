# AI Expense Manager

A comprehensive expense management system powered by AI, featuring natural language querying, interactive visualizations, and SQL-powered data analysis.

## Overview

This project combines multiple AI and data technologies to create an intelligent expense management system. Users can upload expense data, ask natural language questions, and receive detailed analysis with interactive charts.

## Architecture

### Core Components

- **DuckDB**: High-performance analytical database for fast SQL queries
- **LangGraph**: AI orchestration framework for natural language processing
- **Streamlit**: Modern web interface for user interaction
- **Vector Store**: FAISS-based document retrieval for semantic search
- **Plotly**: Interactive chart generation and visualization

### Technology Stack

#### Data Layer
- **DuckDB**: Columnar database for analytical queries
- **Pandas**: Data manipulation and processing
- **FAISS**: Vector similarity search

#### AI/ML Layer
- **LangChain**: LLM integration and chain orchestration
- **LangGraph**: Multi-step AI reasoning and planning
- **DeepSeek**: Primary LLM for natural language understanding
- **OpenAI**: Alternative LLM provider
- **Sentence Transformers**: Text embedding generation

#### Web Interface
- **Streamlit**: Primary web application
- **Gradio**: Alternative UI framework

#### Visualization
- **Plotly**: Interactive charts and graphs
- **Matplotlib**: Static chart generation
- **Kaleido**: Chart export and base64 encoding

## Project Structure

```
ai-expense-manager/
├── duckdb_tools/           # SQL-based analysis tools
│   ├── core/
│   │   ├── duckdb_manager.py      # Database management
│   │   └── chart_generator.py     # Chart generation
│   ├── tools/
│   │   ├── sum_category_expenses_tool.py
│   │   ├── top_expenses_tool.py
│   │   └── category_summary_tool.py
│   └── utils/
│       ├── sql_helpers.py
│       └── date_utils.py
├── langgraph_app/          # AI orchestration
│   ├── nodes/
│   │   ├── planner_node.py
│   │   ├── tool_executor_node.py
│   │   └── duckdb_tool_executor_node.py
│   └── graph.py
├── expense_manager/        # Core expense management
│   ├── chains/
│   ├── memory_system.py
│   ├── vector_store/
│   └── utils/
├── app/                    # Alternative UI components
│   ├── streamlit_app.py
│   ├── gradio_ui.py
│   └── traditional_ui.py
├── tools/                  # Analysis tools
├── data/                   # Sample data and database
└── tests/                  # Test suite
```

## Features

### Natural Language Queries
- Ask questions like "What are my top 5 expenses?"
- "How much did I spend on groceries this month?"
- "Show me expenses over $100"

### Interactive Analysis
- Category-based expense summaries
- Top expense identification
- Monthly spending trends
- Custom date range analysis

### Data Visualization
- Interactive bar charts
- Horizontal bar charts for top expenses
- Pie charts for category distribution
- Line charts for time series analysis

### Data Management
- CSV file upload and processing
- Automatic data validation
- Persistent DuckDB storage
- Real-time data refresh

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-expense-manager
   ```

2. **Create and activate virtual environment**
   ```bash
   # On Windows
   python -m venv ai-expense-venv
   ai-expense-venv\Scripts\activate

   # On macOS/Linux
   python -m venv ai-expense-venv
   source ai-expense-venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   DEEPSEEK_API_KEY=your_deepseek_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

## Usage

### Primary Interface: Streamlit App

The easiest way to get started:

```bash
streamlit run streamlit_app.py
```

This opens your browser to `http://localhost:8501` where you can:
- Chat with AI about your expenses using natural language
- Use quick analysis tools for common queries
- Upload your own CSV files
- View interactive charts and visualizations

### Other Ways to Run

**Gradio interface (alternative UI):**
```bash
python app/working_gradio_ui.py
```

**Basic command line demo:**
```bash
python main.py
```

## Data Format

Your CSV files should have these columns:
- `date`: Transaction date (YYYY-MM-DD format)
- `amount`: Expense amount (numbers only)
- `category`: Expense category (like "groceries", "transport")
- `description`: Transaction description

The project comes with sample data in `data/sample_expense.csv` (200+ example records) to get you started.

## Programmatic Access

The system can be extended with API endpoints for programmatic access. The current implementation focuses on web interfaces (Streamlit/Gradio) and command-line tools.

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Key Test Files
- `test_duckdb_tools.py`: Database functionality tests
- `test_langgraph_duckdb_integration.py`: AI integration tests
- `test_tool_runner.py`: Tool execution tests

### Code Structure

**DuckDB Tools**: SQL-based analysis tools for performance
**LangGraph App**: Multi-step AI reasoning and planning
**Expense Manager**: Core business logic and data processing
**Vector Store**: Semantic search and document retrieval

## Performance

- **SQL Optimization**: Automatic query optimization via DuckDB
- **Large Dataset Support**: Handles GB+ CSV files efficiently
- **Memory Efficient**: Columnar storage reduces memory usage
- **Scalable**: Supports millions of expense records

## Configuration

Key configuration options in `expense_manager/config.py`:
- LLM model selection
- Temperature settings
- API endpoints
- Database paths
- Vector store settings

## Troubleshooting

### Common Issues

1. **API Key Errors**: Make sure your `.env` file has the correct API keys
2. **Database Errors**: Check that the `data/` folder has write permissions
3. **Chart Display Issues**: Try reinstalling Plotly: `pip install plotly kaleido`
4. **Memory Issues**: For large files, the system will handle it automatically

### Getting Help

If you run into issues:
- Check that your virtual environment is activated
- Verify all dependencies are installed: `pip list`
- Look at the console output for error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- DuckDB for high-performance analytical database
- LangChain for LLM integration framework
- Streamlit for rapid web application development
- Plotly for interactive visualizations