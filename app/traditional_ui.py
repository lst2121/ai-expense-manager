import sys
import os
# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
import pandas as pd
from datetime import datetime
from expense_manager.utils.csv_loader import load_and_prepare_csv
from expense_manager.memory_system import memory_system
from langgraph_app.graph import expense_analysis_app

### 🔄 File Upload Handler ###
def handle_file_upload(file_obj):
    """Handle CSV file upload and data preparation."""
    if file_obj is None:
        return {"df": pd.DataFrame()}, gr.Dataframe(value=pd.DataFrame()), "No file uploaded"
    
    try:
        df = load_and_prepare_csv(file_obj.name)
        message = f"✅ Loaded {len(df)} expense records"
        return {"df": df}, gr.Dataframe(value=df.head(10)), message
    except Exception as e:
        error_msg = f"❌ Error loading file: {e}"
        return {"df": pd.DataFrame()}, gr.Dataframe(value=pd.DataFrame()), error_msg

### 🤖 Enhanced Assistant Logic ###
def run_expense_assistant(query: str, state: dict):
    """Enhanced assistant with memory integration."""
    df = state.get("df", pd.DataFrame())
    
    if df.empty:
        return "⚠️ Please upload a CSV file first to analyze your expenses.", state
    
    if not query.strip():
        return "❓ Please enter a question about your expenses.", state
    
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
        
        return answer, state
        
    except Exception as e:
        error_msg = f"❌ Analysis failed: {e}"
        memory_system.add_conversation(
            query=query,
            result=error_msg,
            analysis_metadata={"error": True, "execution_time": 0}
        )
        return error_msg, state

### 📊 Memory Display Functions ###
def get_memory_stats():
    """Get formatted memory statistics."""
    stats = memory_system.get_memory_stats()
    total = stats['total_conversations']
    
    # Calculate percentages
    simple_count = stats['query_type_breakdown'].get('simple', 0)
    multi_step_count = stats['query_type_breakdown'].get('multi_step', 0)
    complex_count = stats['query_type_breakdown'].get('complex', 0)
    
    simple_pct = (simple_count / total * 100) if total > 0 else 0
    multi_step_pct = (multi_step_count / total * 100) if total > 0 else 0
    complex_pct = (complex_count / total * 100) if total > 0 else 0
    
    return f"""
### 📊 Memory Statistics

**📈 Overview:**
- **Total Conversations:** {total}
- **This Session:** {stats['session_conversations']}
- **Current Session ID:** `{stats['current_session']}`

**🎯 Query Complexity Breakdown:**
- 🔍 **Simple:** {simple_count} ({simple_pct:.1f}%)
- 🔄 **Multi-step:** {multi_step_count} ({multi_step_pct:.1f}%)  
- 🧠 **Complex:** {complex_count} ({complex_pct:.1f}%)

**💾 Storage:** {stats['memory_file']}
"""

def get_full_memory_display():
    """Get full conversation history display."""
    conversations = memory_system.get_conversations(limit=20)
    
    if not conversations:
        return "### 🧠 No conversations yet\n\nStart asking questions to build up your conversation history!\n\n💡 **Tip:** Try uploading a CSV file first, then ask questions like:\n- 'How much did I spend on groceries?'\n- 'Show grocery trends over 3 months'\n- 'Compare transportation vs dining'"
    
    display_text = "### 🧠 Conversation History\n\n"
    
    for i, conv in enumerate(conversations, 1):
        # Format timestamp
        try:
            dt = datetime.fromisoformat(conv['timestamp'])
            time_str = dt.strftime("%H:%M:%S on %Y-%m-%d")
        except:
            time_str = conv['timestamp']
        
        # Get query type info
        type_emoji = "🔍" if conv['query_type'] == "simple" else "🔄" if conv['query_type'] == "multi_step" else "🧠"
        type_name = conv['query_type'].replace('_', ' ').title()
        
        # Multi-step info
        multi_step_info = ""
        execution_time = ""
        if conv['metadata'].get('is_multi_step'):
            steps = conv['metadata'].get('step_results', [])
            multi_step_info = f" ({len(steps)} steps)"
        
        # Add execution time if available
        if conv['metadata'].get('execution_time'):
            exec_time = conv['metadata']['execution_time']
            execution_time = f" _⏱️ {exec_time:.1f}s_"
        
        display_text += f"**{type_emoji} {type_name} Query{multi_step_info}**{execution_time} _{time_str}_\n\n"
        display_text += f"❓ **Q:** {conv['query']}\n\n"
        display_text += f"💬 **A:** {conv['result'][:250]}{'...' if len(conv['result']) > 250 else ''}\n\n"
        display_text += "---\n\n"
    
    return display_text

def search_conversations(search_term: str):
    """Search conversations and return formatted results."""
    if not search_term.strip():
        return get_full_memory_display()
    
    results = memory_system.search_conversations(search_term)
    
    if not results:
        return f"### 🔍 No results found for '{search_term}'"
    
    display_text = f"### 🔍 Search Results for '{search_term}' ({len(results)} found)\n\n"
    
    for conv in results[:10]:  # Limit to 10 results
        try:
            dt = datetime.fromisoformat(conv['timestamp'])
            time_str = dt.strftime("%H:%M:%S on %Y-%m-%d")
        except:
            time_str = conv['timestamp']
        
        type_emoji = "🔍" if conv['query_type'] == "simple" else "🔄" if conv['query_type'] == "multi_step" else "🧠"
        
        display_text += f"""
**{type_emoji} Query** _{time_str}_

**Q:** {conv['query']}

**A:** {conv['result'][:200]}{'...' if len(conv['result']) > 200 else ''}

---
"""
    
    return display_text

def display_expense_data(df: pd.DataFrame) -> gr.DataFrame:
    """
    Displays expense data with inferred categories highlighted.
    Args:
        df: DataFrame with expense data, including inferred categories.
    Returns:
        Gradio DataFrame component with styled output.
    """
    if df.empty:
        empty_df = pd.DataFrame(columns=["Date", "Category", "Amount", "Notes"])
        return gr.DataFrame(value=empty_df)

    # Add a column to indicate inferred categories
    df["Source"] = df["Category"].apply(
        lambda x: "Inferred" if "/" in str(x) else "Manual"
    )

    # Style the DataFrame to highlight inferred categories
    def style_row(row):
        if row["Source"] == "Inferred":
            return ["background-color: #FFF2CC"] * len(row)
        return [""] * len(row)

    styled_df = df.style.apply(style_row, axis=1)
    return gr.DataFrame(
        value=df,  # Use original DataFrame instead of styled version
        interactive=False
    )

### 🎨 UI Setup ###
custom_css = """
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.chat-container {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
}
"""

# Create the traditional Gradio interface
with gr.Blocks(css=custom_css, title="AI Expense Assistant - Traditional") as demo:
    
    # Application state
    state = gr.State({"df": pd.DataFrame()})
    
    # Header
    gr.Markdown("""
    # 💸 AI Expense Assistant (Traditional Interface)
    ### Multi-step reasoning with intelligent conversation tracking
    """)
    
    # Main interface with tabs
    with gr.Tabs():
        
        # ==================== CHAT ASSISTANT TAB ====================
        with gr.TabItem("💬 Chat Assistant", id="chat"):
            
            with gr.Row():
                with gr.Column():
                    
                    # File upload section
                    with gr.Group():
                        gr.Markdown("### 📁 Data Upload")
                        file_input = gr.File(label="Upload Expense CSV", file_types=[".csv"])
                        upload_status = gr.Textbox(label="Status", value="No file uploaded yet", interactive=False)
                    
                    # Chat interface
                    with gr.Group(elem_classes="chat-container"):
                        gr.Markdown("### 💭 Ask Your Question")
                        query_input = gr.Textbox(
                            label="Query",
                            placeholder="e.g., Show grocery trends over the last 3 months...",
                            lines=2
                        )
                        
                        with gr.Row():
                            submit_btn = gr.Button("🚀 Analyze", variant="primary", scale=2)
                            clear_btn = gr.Button("🧹 Clear", scale=1)
                    
                    # Response
                    response_output = gr.Textbox(
                        label="🤖 Assistant Response",
                        lines=10,
                        max_lines=20,
                        interactive=False
                    )
                    
                    # Quick suggestions
                    gr.Markdown("### 💡 Try These Advanced Queries:")
                    with gr.Row():
                        suggest1 = gr.Button("Show grocery trends over 3 months", size="sm")
                        suggest2 = gr.Button("Compare transportation vs dining", size="sm")
                        suggest3 = gr.Button("Find top 5 expenses and analyze", size="sm")
        
        # ==================== MEMORY TAB ====================
        with gr.TabItem("🧠 Memory Center", id="memory"):
            
            with gr.Row():
                with gr.Column(scale=1):
                    # Memory controls
                    gr.Markdown("### 🔍 Search & Controls")
                    search_input = gr.Textbox(
                        label="Search conversations",
                        placeholder="Enter keywords...",
                        value=""
                    )
                    search_btn = gr.Button("🔍 Search", variant="secondary")
                    refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
                    
                    # Memory stats
                    stats_display = gr.Markdown(value=get_memory_stats())
                
                with gr.Column(scale=2):
                    # Full memory display
                    full_memory_display = gr.Markdown(
                        value=get_full_memory_display(),
                        label="Conversation History"
                    )
        
        # ==================== DATA TAB ====================
        with gr.TabItem("📊 Data Preview", id="data"):
            gr.Markdown("### 📊 Uploaded Data Preview")
            data_display = display_expense_data(pd.DataFrame())
    
    # ==================== EVENT HANDLERS ====================
    
    def handle_query_submit(query, current_state):
        """Handle query submission and update displays."""
        if not query.strip():
            return "", current_state, query
        
        result, updated_state = run_expense_assistant(query, current_state)
        
        # Update stats and full memory for memory tab
        new_stats = get_memory_stats()
        new_full_memory = get_full_memory_display()
        
        return result, updated_state, "", new_stats, new_full_memory
    
    def handle_clear():
        """Clear the input and response."""
        return "", ""
    
    def handle_suggestion(suggestion_text, current_state):
        """Handle suggestion button clicks."""
        result, updated_state = run_expense_assistant(suggestion_text, current_state)
        new_stats = get_memory_stats()
        new_full_memory = get_full_memory_display()
        return result, updated_state, suggestion_text, new_stats, new_full_memory
    
    # Main submission
    submit_btn.click(
        fn=handle_query_submit,
        inputs=[query_input, state],
        outputs=[response_output, state, query_input, stats_display, full_memory_display]
    )
    
    query_input.submit(
        fn=handle_query_submit,
        inputs=[query_input, state],
        outputs=[response_output, state, query_input, stats_display, full_memory_display]
    )
    
    # Clear button
    clear_btn.click(
        fn=handle_clear,
        outputs=[query_input, response_output]
    )
    
    # Suggestion buttons
    suggest1.click(
        fn=lambda state: handle_suggestion("Show grocery trends over 3 months", state),
        inputs=[state],
        outputs=[response_output, state, query_input, stats_display, full_memory_display]
    )
    
    suggest2.click(
        fn=lambda state: handle_suggestion("Compare transportation vs dining", state),
        inputs=[state],
        outputs=[response_output, state, query_input, stats_display, full_memory_display]
    )
    
    suggest3.click(
        fn=lambda state: handle_suggestion("Find top 5 expenses and analyze", state),
        inputs=[state],
        outputs=[response_output, state, query_input, stats_display, full_memory_display]
    )
    
    # File upload
    file_input.upload(
        fn=handle_file_upload,
        inputs=[file_input],
        outputs=[state, data_display, upload_status]
    )
    
    # Memory search
    search_btn.click(
        fn=search_conversations,
        inputs=[search_input],
        outputs=[full_memory_display]
    )
    
    # Refresh memory
    refresh_btn.click(
        fn=get_full_memory_display,
        outputs=[full_memory_display]
    )

# Launch configuration
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7863,  # Different port
        share=False,
        show_error=True
    ) 