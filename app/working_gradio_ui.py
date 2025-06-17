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

### 💬 ChatGPT-like Interface Functions ###
def handle_chatbot_message(message, history, current_state):
    """Handle chatbot message submission."""
    if not message or not message.strip():
        return history, current_state, ""
    
    if current_state.get('df') is None or current_state['df'].empty:
        bot_response = "⚠️ Please upload a CSV file first to analyze your expenses."
        history.append((message, bot_response))
        return history, current_state, ""
    
    try:
        # Get AI response
        result, updated_state = run_expense_assistant(message, current_state)
        
        # Add to chat history
        history.append((message, result))
        
        return history, updated_state, ""
        
    except Exception as e:
        error_msg = f"❌ Analysis failed: {e}"
        history.append((message, error_msg))
        return history, current_state, ""

def handle_chatbot_suggestion(suggestion_text, history, current_state):
    """Handle suggestion button clicks in chatbot."""
    return handle_chatbot_message(suggestion_text, history, current_state)

def handle_chatbot_file_upload(file_obj, history, current_state):
    """Handle file upload for chatbot interface."""
    if file_obj is None:
        return current_state, "No file uploaded", history, gr.Dataframe(value=pd.DataFrame())
    
    try:
        df = load_and_prepare_csv(file_obj.name)
        message = f"✅ Loaded {len(df)} expense records. You can now ask questions about your expenses!"
        
        # Add system message to chat
        history.append(("📁 File uploaded", message))
        
        return {"df": df}, message, history, gr.Dataframe(value=df.head(10))
    except Exception as e:
        error_msg = f"❌ Error loading file: {e}"
        history.append(("📁 File upload", error_msg))
        return {"df": pd.DataFrame()}, error_msg, history, gr.Dataframe(value=pd.DataFrame())

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

/* ChatGPT-like interface styling */
.chatbot-container {
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid #e1e5e9;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.chat-input-container {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    margin-top: 10px;
    border: 1px solid #e1e5e9;
}

/* Target the memory sidebar container */
.memory-sidebar {
    background: #f8f9fa !important;
    border-radius: 8px;
    padding: 15px;
    border: 1px solid #dee2e6;
    max-height: 600px !important;
    overflow-y: auto !important;
}

/* Target Gradio's markdown content specifically */
.memory-sidebar .prose,
.memory-sidebar .markdown,
.memory-sidebar div[data-testid="markdown"],
.memory-sidebar .gr-markdown {
    max-height: 550px !important;
    overflow-y: auto !important;
    padding-right: 10px;
}

/* Target any div inside memory sidebar that contains the content */
.memory-sidebar > div,
.memory-sidebar > div > div {
    max-height: 550px !important;
    overflow-y: auto !important;
}

/* Sticky header */
.memory-sidebar h3 {
    position: sticky;
    top: 0;
    background: #f8f9fa;
    margin-top: 0 !important;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid #007bff;
    z-index: 10;
}

.memory-sidebar hr {
    margin: 10px 0;
    border: none;
    border-top: 1px solid #dee2e6;
}

/* Enhanced scrollbar styling */
.memory-sidebar::-webkit-scrollbar,
.memory-sidebar div::-webkit-scrollbar {
    width: 8px;
}

.memory-sidebar::-webkit-scrollbar-track,
.memory-sidebar div::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

.memory-sidebar::-webkit-scrollbar-thumb,
.memory-sidebar div::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
}

.memory-sidebar::-webkit-scrollbar-thumb:hover,
.memory-sidebar div::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}

/* Force height constraints on all possible containers */
.memory-sidebar * {
    max-height: inherit !important;
}

/* Special handling for deeply nested content */
.memory-sidebar div[class*="markdown"],
.memory-sidebar div[class*="prose"] {
    max-height: 520px !important;
    overflow-y: auto !important;
    padding-right: 8px;
}
"""

# Create the working Gradio interface
with gr.Blocks(css=custom_css, title="AI Expense Assistant - Enhanced") as demo:
    
    # Application state
    state = gr.State({"df": pd.DataFrame()})
    
    # Header
    gr.Markdown("""
    # 💸 AI Expense Assistant (Enhanced Memory)
    ### Multi-step reasoning with intelligent conversation tracking
    """)
    
    # Main interface with tabs
    with gr.Tabs():
        
        # ==================== CHAT TAB ====================
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

        # ==================== CHAT UI TAB (ChatGPT-like) ====================
        with gr.TabItem("💬 Chat UI", id="chat-ui"):
            
            with gr.Row():
                with gr.Column(scale=3):
                    # ChatGPT-like conversation interface
                    chatbot = gr.Chatbot(
                        label="💬 Conversation",
                        height=400,
                        elem_classes="chatbot-container",
                        show_label=True,
                        container=True,
                        bubble_full_width=False
                    )
                    
                    # Message input area
                    with gr.Group(elem_classes="chat-input-container"):
                        with gr.Row():
                            chat_input = gr.Textbox(
                                label="",
                                placeholder="💭 Ask me anything about your expenses...",
                                lines=2,
                                scale=4,
                                show_label=False,
                                container=False
                            )
                            chat_send_btn = gr.Button("🚀 Send", variant="primary", scale=1, size="lg")
                    
                    # Quick action buttons
                    with gr.Row():
                        chat_suggest1 = gr.Button("📊 Show top 5 expenses", size="sm", variant="secondary")
                        chat_suggest2 = gr.Button("🛒 Grocery spending trends", size="sm", variant="secondary")
                        chat_suggest3 = gr.Button("🚗 Transportation vs dining", size="sm", variant="secondary")
                        chat_clear_btn = gr.Button("🧹 Clear Chat", size="sm", variant="secondary")
                
                with gr.Column(scale=1):
                    # File upload for chat interface
                    with gr.Group():
                        gr.Markdown("### 📁 Data Upload")
                        chat_file_input = gr.File(label="Upload CSV", file_types=[".csv"])
                        chat_upload_status = gr.Textbox(label="Status", value="No file uploaded", interactive=False)
                    
                    # Data preview
                    with gr.Group():
                        gr.Markdown("### 📊 Data Preview")
                        chat_data_preview = gr.Dataframe(
                            value=pd.DataFrame(),
                            interactive=False,
                            wrap=True
                        )
        
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
            data_preview = gr.Dataframe(
                value=pd.DataFrame(),
                interactive=False,
                wrap=True
            )
    
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
        outputs=[state, data_preview, upload_status]
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
    
    # ==================== CHAT UI EVENT HANDLERS ====================
    
    # Chat message submission
    chat_send_btn.click(
        fn=handle_chatbot_message,
        inputs=[chat_input, chatbot, state],
        outputs=[chatbot, state, chat_input]
    )
    
    chat_input.submit(
        fn=handle_chatbot_message,
        inputs=[chat_input, chatbot, state],
        outputs=[chatbot, state, chat_input]
    )
    
    # Chat suggestion buttons
    chat_suggest1.click(
        fn=lambda history, state: handle_chatbot_suggestion("Show top 5 expenses", history, state),
        inputs=[chatbot, state],
        outputs=[chatbot, state, chat_input]
    )
    
    chat_suggest2.click(
        fn=lambda history, state: handle_chatbot_suggestion("Show grocery trends over 3 months", history, state),
        inputs=[chatbot, state],
        outputs=[chatbot, state, chat_input]
    )
    
    chat_suggest3.click(
        fn=lambda history, state: handle_chatbot_suggestion("Compare transportation vs dining", history, state),
        inputs=[chatbot, state],
        outputs=[chatbot, state, chat_input]
    )
    
    # Clear chat
    chat_clear_btn.click(
        fn=lambda: ([], ""),
        outputs=[chatbot, chat_input]
    )
    
    # Chat file upload
    chat_file_input.upload(
        fn=handle_chatbot_file_upload,
        inputs=[chat_file_input, chatbot, state],
        outputs=[state, chat_upload_status, chatbot, chat_data_preview]
    )

# Launch configuration
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7862,  # Different port
        share=False,
        show_error=True
    ) 