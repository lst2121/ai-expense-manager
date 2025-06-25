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

.sidebar-container {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    border: 1px solid #e1e5e9;
}
"""

def display_expense_data(df: pd.DataFrame) -> gr.DataFrame:
    """
    Displays expense data with inferred categories highlighted.
    Args:
        df: DataFrame with expense data, including inferred categories.
    Returns:
        Gradio DataFrame component with styled output.
    """
    if df.empty:
        return gr.DataFrame(value=pd.DataFrame())

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
    return gr.DataFrame(value=styled_df, interactive=False)

# Create the ChatGPT-like Gradio interface
with gr.Blocks(css=custom_css, title="AI Expense Assistant - Chat UI") as demo:
    
    # Application state
    state = gr.State({"df": pd.DataFrame()})
    
    # Header
    gr.Markdown("""
    # 💬 AI Expense Chat Assistant
    ### ChatGPT-like conversation interface with intelligent expense analysis
    """)
    
    # Main chat interface
    with gr.Row():
        with gr.Column(scale=3):
            # ChatGPT-like conversation interface
            chatbot = gr.Chatbot(
                label="💬 Conversation",
                height=400,
                elem_classes="chatbot-container",
                show_label=True,
                container=True
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
            with gr.Group(elem_classes="sidebar-container"):
                gr.Markdown("### 📁 Data Upload")
                chat_file_input = gr.File(label="Upload CSV", file_types=[".csv"])
                chat_upload_status = gr.Textbox(label="Status", value="No file uploaded", interactive=False)
            
            # Data preview
            with gr.Group(elem_classes="sidebar-container"):
                gr.Markdown("### 📊 Data Preview")
                chat_data_preview = gr.Dataframe(
                    value=pd.DataFrame(),
                    interactive=False,
                    wrap=True
                )
            
            # Usage tips
            with gr.Group(elem_classes="sidebar-container"):
                gr.Markdown("""
                ### 💡 Usage Tips
                
                **Quick Start:**
                1. Upload your expense CSV file
                2. Start chatting with questions
                3. Use suggestion buttons for examples
                
                **Example Questions:**
                - "What are my top expenses?"
                - "Show grocery trends over 3 months"
                - "Compare dining vs transportation"
                - "How much did I spend on subscriptions?"
                
                **Features:**
                - Multi-step reasoning
                - Conversation memory
                - Real-time analysis
                """)
    
    # ==================== EVENT HANDLERS ====================
    
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
        server_port=7864,  # Different port
        share=False,
        show_error=True
    ) 

def summarize_memory_tool(memory, df):
    """
    Generates deep-dive questions based on expense data, avoiding string ops on numeric fields.
    Args:
        memory: List of past interactions (unused here).
        df: DataFrame with expense data.
    Returns:
        List of suggested questions or analysis prompts.
    """
    try:
        # Ensure df is a DataFrame and has required columns
        if not isinstance(df, pd.DataFrame) or df.empty:
            return ["No data available for analysis."]

        questions = []

        # 1. Top categories analysis
        top_categories = df.groupby('Category')['Amount'].sum().head(3)
        if not top_categories.empty:
            questions.append(
                f"Top spending categories: {', '.join(top_categories.index)}. "
                f"Why do these dominate your expenses?"
            )

        # 2. Monthly trends (numeric analysis)
        monthly_totals = df.groupby('Month')['Amount'].sum()
        if len(monthly_totals) > 1:
            max_month = monthly_totals.idxmax()
            questions.append(
                f"Highest spending month: {max_month} (₹{monthly_totals[max_month]:.2f}). "
                f"What drove this peak?"
            )

        # 3. Anomaly detection (numeric)
        mean_amount = df['Amount'].mean()
        outliers = df[df['Amount'] > 2 * mean_amount]
        if not outliers.empty:
            questions.append(
                f"Potential outliers: {len(outliers)} expenses exceed ₹{2 * mean_amount:.2f}. "
                f"Review these for errors or bulk purchases."
            )

        # 4. Behavioral prompts (text fields only)
        if 'Notes' in df.columns:
            frequent_notes = df['Notes'].value_counts().head(2)
            if not frequent_notes.empty:
                questions.append(
                    f"Frequent notes: {', '.join(frequent_notes.index)}. "
                    f"Are these recurring or one-time expenses?"
                )

        return questions if questions else ["No patterns detected. Try more specific queries."]

    except Exception as e:
        return [f"Analysis error: {str(e)}"] 