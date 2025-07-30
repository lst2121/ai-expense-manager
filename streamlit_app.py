#!/usr/bin/env python3
"""
AI Expense Manager - Streamlit App
DuckDB-powered expense analysis with interactive charts
"""

import streamlit as st
import pandas as pd
import base64
import io
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import DuckDB components
from duckdb_tools.core.duckdb_manager import DuckDBManager
from duckdb_tools.tools.sum_category_expenses_tool import sum_category_expenses_tool
from duckdb_tools.tools.top_expenses_tool import top_expenses_tool
from duckdb_tools.tools.category_summary_tool import category_summary_tool

# Import LangGraph
from langgraph_app.graph import expense_analysis_app

# Configure page
st.set_page_config(
    page_title="AI Expense Manager",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .chart-container {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_duckdb():
    """Initialize DuckDB with sample data"""
    db_manager = DuckDBManager("data/expenses.duckdb")
    
    # Load sample data if not already loaded
    csv_path = "data/sample_expense.csv"
    if os.path.exists(csv_path):
        db_manager.load_csv_to_table(csv_path, "expenses")
        db_manager.create_views()
    
    return db_manager

def display_chart(chart_base64: str, title: str = "Chart"):
    """Display base64 chart in Streamlit"""
    if chart_base64:
        try:
            # Decode base64 image
            chart_data = base64.b64decode(chart_base64)
            
            # Display image
            st.image(chart_data, caption=title, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to display chart: {e}")
    else:
        st.info("No chart available for this analysis")

def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown('<h1 class="main-header">💰 AI Expense Manager</h1>', unsafe_allow_html=True)
    st.markdown("### SQL-Powered Expense Analysis with Interactive Charts")
    
    # Initialize DuckDB
    try:
        db_manager = init_duckdb()
        table_info = db_manager.get_table_info("expenses")
        
        # Sidebar
        st.sidebar.title("📊 Quick Actions")
        
        # Display basic stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Expenses", f"₹{table_info.get('row_count', 0):,}")
        with col2:
            st.metric("Categories", len(table_info.get('categories', [])))
        with col3:
            st.metric("Date Range", f"{table_info.get('date_range', {}).get('min_date', 'N/A')} to {table_info.get('date_range', {}).get('max_date', 'N/A')}")
        with col4:
            st.metric("Database", "DuckDB ✅")
        
        # Main content area
        tab1, tab2, tab3, tab4 = st.tabs(["🤖 AI Chat", "📊 Quick Analysis", "📈 Charts", "⚙️ Settings"])
        
        with tab1:
            st.header("🤖 AI-Powered Expense Analysis")
            st.markdown("Ask questions about your expenses in natural language!")
            
            # Chat interface
            if "messages" not in st.session_state:
                st.session_state.messages = []
            
            # Display chat history
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if "chart" in message and message["chart"]:
                        display_chart(message["chart"], "Analysis Chart")
            
            # Chat input
            if prompt := st.chat_input("Ask about your expenses..."):
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Get AI response
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing your expenses..."):
                        try:
                            # Use LangGraph for AI analysis
                            result = expense_analysis_app.invoke({
                                "query": prompt,
                                "df": pd.DataFrame(),  # Empty for DuckDB tools
                                "memory": []
                            })
                            
                            response_text = result.get("result", "No response generated")
                            chart_data = result.get("chart")
                            
                            st.markdown(response_text)
                            
                            if chart_data:
                                display_chart(chart_data, "Analysis Chart")
                            
                            # Add assistant message
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": response_text,
                                "chart": chart_data
                            })
                            
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        with tab2:
            st.header("📊 Quick Analysis Tools")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Sum Category Expenses")
                category = st.selectbox("Select Category", table_info.get('categories', []))
                month = st.text_input("Month (optional)", placeholder="2025-01 or 'last month'")
                
                if st.button("Calculate Sum"):
                    with st.spinner("Calculating..."):
                        result = sum_category_expenses_tool.invoke({
                            "category": category,
                            "month": month if month else None
                        })
                        
                        st.success(result["text"])
            
            with col2:
                st.subheader("Top Expenses")
                n_expenses = st.slider("Number of expenses", 1, 20, 5)
                top_category = st.selectbox("Category filter", ["All"] + table_info.get('categories', []))
                top_month = st.text_input("Month filter", placeholder="2025-01")
                
                if st.button("Find Top Expenses"):
                    with st.spinner("Finding top expenses..."):
                        args: dict = {"n": n_expenses}
                        if top_category != "All":
                            args["category"] = top_category
                        if top_month:
                            args["month"] = top_month
                        
                        result = top_expenses_tool.invoke(args)
                        
                        st.success(result["text"])
                        if result["chart"]:
                            display_chart(result["chart"], "Top Expenses Chart")
        
        with tab3:
            st.header("📈 Interactive Charts")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Category Summary")
                summary_category = st.selectbox("Category for Summary", table_info.get('categories', []))
                summary_mode = st.selectbox("Analysis Mode", ["total", "average", "count"])
                summary_month = st.text_input("Month for Summary", placeholder="2025-01")
                
                if st.button("Generate Summary"):
                    with st.spinner("Generating summary..."):
                        args = {
                            "category": summary_category,
                            "mode": summary_mode
                        }
                        if summary_month:
                            args["month"] = summary_month
                        
                        result = category_summary_tool.invoke(args)
                        
                        st.success(result["text"])
                        if result["chart"]:
                            display_chart(result["chart"], f"{summary_mode.capitalize()} Summary")
            
            with col2:
                st.subheader("Database Info")
                st.json(table_info)
        
        with tab4:
            st.header("⚙️ Settings")
            
            st.subheader("Database Management")
            
            # File upload
            uploaded_file = st.file_uploader("Upload CSV File", type=['csv'])
            if uploaded_file is not None:
                if st.button("Load New Data"):
                    with st.spinner("Loading data..."):
                        # Save uploaded file temporarily
                        temp_path = f"temp_{uploaded_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Load to DuckDB
                        success = db_manager.load_csv_to_table(temp_path, "expenses")
                        
                        if success:
                            st.success("Data loaded successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to load data")
                        
                        # Clean up
                        os.remove(temp_path)
            
            # Clear chat
            if st.button("Clear Chat History"):
                st.session_state.messages = []
                st.success("Chat history cleared!")
                st.rerun()
    
    except Exception as e:
        st.error(f"Failed to initialize application: {e}")
        st.info("Please ensure the sample data file exists at 'data/sample_expense.csv'")

if __name__ == "__main__":
    main() 