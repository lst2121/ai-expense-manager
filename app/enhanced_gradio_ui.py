import sys
import os
# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
import pandas as pd
from datetime import datetime
from expense_manager.utils.csv_loader import load_and_prepare_csv
from expense_manager.memory_system import memory_system
from app.memory_ui_components import (
    generate_memory_display, 
    export_memory_handler, 
    clear_memory_handler,
    search_memory_handler
)
from langgraph_app.graph import expense_analysis_app

### 🔄 File Upload Handler ###
def handle_file_upload(file_obj):
    """Handle CSV file upload and data preparation."""
    if file_obj is None:
        return {"df": pd.DataFrame()}, gr.Dataframe(value=pd.DataFrame()), "No file uploaded"
    
    try:
        df = load_and_prepare_csv(file_obj.name)
        message = f"✅ Loaded {len(df)} expense records from {file_obj.name}"
        return {"df": df}, gr.Dataframe(value=df.head()), message
    except Exception as e:
        error_msg = f"❌ Error loading file: {e}"
        return {"df": pd.DataFrame()}, gr.Dataframe(value=pd.DataFrame()), error_msg

### 🤖 Enhanced Assistant Logic ###
def run_expense_assistant(query: str, state: dict):
    """Enhanced assistant with memory integration."""
    df = state.get("df", pd.DataFrame())
    
    if df.empty:
        return "⚠️ Please upload a CSV file first to analyze your expenses.", "", state
    
    if not query.strip():
        return "❓ Please enter a question about your expenses.", "", state
    
    try:
        # Record start time for performance tracking
        start_time = datetime.now()
        
        # Invoke the expense analysis
        result = expense_analysis_app.invoke({"query": query, "df": df})
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Extract result and metadata
        answer = result.get("result", "Sorry, I couldn't process your request.")
        
        # Prepare metadata for memory storage
        analysis_metadata = {
            "is_multi_step": result.get("is_multi_step", False),
            "step_results": result.get("step_results", []),
            "execution_time": execution_time,
            "invoked_tool": result.get("invoked_tool", "unknown"),
            "query_timestamp": datetime.now().isoformat()
        }
        
        # Add to enhanced memory system
        memory_system.add_conversation(
            query=query,
            result=answer,
            analysis_metadata=analysis_metadata
        )
        
        # Generate updated memory display
        memory_display = generate_memory_display(limit=5)
        
        return answer, memory_display, state
        
    except Exception as e:
        error_msg = f"❌ Analysis failed: {e}"
        memory_system.add_conversation(
            query=query,
            result=error_msg,
            analysis_metadata={"error": True, "execution_time": 0}
        )
        memory_display = generate_memory_display(limit=5)
        return error_msg, memory_display, state

### 📊 Memory Management Functions ###
def refresh_memory_display(limit: int, query_type_filter: str, search_term: str):
    """Refresh the memory display with current filters."""
    return search_memory_handler(search_term, query_type_filter, limit)

def export_memory(format_choice: str, session_only: bool):
    """Export memory and return as downloadable file."""
    content, filename = export_memory_handler(format_choice, session_only)
    return content

def clear_memory(session_only: bool):
    """Clear memory and refresh display."""
    message, updated_display = clear_memory_handler(session_only)
    return message, updated_display

### 🎨 Enhanced UI Setup ###
custom_css = """
.gradio-container {
    max-width: 1200px !important;
}

.chat-interface {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
}

.memory-display {
    max-height: 600px;
    overflow-y: auto;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    background: #fafafa;
}

.suggestion-button {
    font-size: 0.85rem !important;
    margin: 4px !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    color: white !important;
}
"""

# Create the enhanced Gradio interface
with gr.Blocks(css=custom_css, title="AI Expense Assistant") as demo:
    
    # Application state
    state = gr.State({"df": pd.DataFrame()})
    
    # Header
    gr.Markdown("""
    # 💸 AI Expense Assistant (Enhanced)
    ### Your intelligent financial analysis companion with advanced memory and multi-step reasoning
    """)
    
    # Main interface with tabs
    with gr.Tabs():
        
        # ==================== CHAT TAB ====================
        with gr.TabItem("💬 Chat Assistant"):
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Main chat interface
                    with gr.Group(elem_classes="chat-interface"):
                        query_input = gr.Textbox(
                            label="💭 Ask about your expenses",
                            placeholder="e.g., Show grocery trends over the last 3 months, or Compare my spending patterns...",
                            lines=2
                        )
                        
                        with gr.Row():
                            submit_btn = gr.Button("🚀 Analyze", variant="primary", scale=2)
                            clear_btn = gr.Button("🧹 Clear", scale=1)
                    
                    # Response area
                    response_output = gr.Textbox(
                        label="🤖 Assistant Response",
                        lines=8,
                        max_lines=15,
                        interactive=False
                    )
                    
                    # Quick suggestions
                    gr.Markdown("#### 💡 Try These Advanced Queries:")
                    suggestions = [
                        "Show grocery trends over 3 months",
                        "Compare transportation vs dining", 
                        "Find top 5 expenses and analyze categories",
                        "What category increased the most?",
                        "Analyze spending patterns by month"
                    ]
                    
                    with gr.Row():
                        for suggestion in suggestions[:3]:
                            gr.Button(suggestion, elem_classes="suggestion-button").click(
                                fn=lambda current_state, q=suggestion: run_expense_assistant(q, current_state),
                                inputs=[state],
                                outputs=[response_output, query_input]
                            )
                
                with gr.Column(scale=1):
                    # Recent memory sidebar
                    gr.Markdown("### 🧠 Recent Conversations")
                    recent_memory = gr.HTML(
                        value=generate_memory_display(limit=3),
                        elem_classes="memory-display"
                    )
        
        # ==================== MEMORY TAB ====================
        with gr.TabItem("🧠 Memory Center"):
            
            gr.Markdown("## 🗂️ Conversation Memory & Analytics")
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🔍 Search & Filter")
                    
                    search_input = gr.Textbox(
                        label="Search conversations",
                        placeholder="Search by keywords...",
                        value=""
                    )
                    
                    with gr.Row():
                        type_filter = gr.Dropdown(
                            choices=["All", "Simple", "Multi Step", "Complex"],
                            value="All",
                            label="Query Type Filter"
                        )
                        
                        result_limit = gr.Slider(
                            minimum=5,
                            maximum=50,
                            value=10,
                            step=5,
                            label="Results Limit"
                        )
                    
                    refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
                
                with gr.Column(scale=2):
                    full_memory_display = gr.HTML(
                        value=generate_memory_display(),
                        elem_classes="memory-display"
                    )
        
        # ==================== DATA TAB ====================
        with gr.TabItem("📊 Data Management"):
            
            gr.Markdown("## 📁 Data Upload & Preview")
            
            file_input = gr.File(
                label="📂 Upload Expense CSV",
                file_types=[".csv"]
            )
            
            upload_status = gr.Textbox(
                label="📋 Upload Status",
                value="No file uploaded yet",
                interactive=False
            )
            
            data_preview = gr.Dataframe(
                label="📊 Data Preview",
                value=pd.DataFrame(),
                interactive=False
            )
    
    # ==================== EVENT HANDLERS ====================
    
    # Main chat functionality
    def handle_submit(query, current_state):
        result, memory_html, updated_state = run_expense_assistant(query, current_state)
        return result, memory_html, updated_state, ""  # Clear input
    
    def handle_submit_and_update_memory(query, current_state):
        result, memory_html, updated_state = run_expense_assistant(query, current_state)
        # Also update the full memory display
        full_memory_html = generate_memory_display(limit=10)
        return result, memory_html, full_memory_html, updated_state, ""  # Clear input
    
    submit_btn.click(
        fn=handle_submit,
        inputs=[query_input, state],
        outputs=[response_output, recent_memory, state, query_input],
        show_progress="full"
    )
    
    query_input.submit(
        fn=handle_submit,
        inputs=[query_input, state],
        outputs=[response_output, recent_memory, state, query_input],
        show_progress="full"
    )
    
    # File upload
    file_input.upload(
        fn=handle_file_upload,
        inputs=[file_input],
        outputs=[state, data_preview, upload_status]
    )
    
    # Memory management
    refresh_btn.click(
        fn=refresh_memory_display,
        inputs=[result_limit, type_filter, search_input],
        outputs=[full_memory_display]
    )

# Launch configuration
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,  # Different port to avoid conflicts
        share=False,
        show_error=True
    ) 