import gradio as gr
import pandas as pd
from langgraph_app.graph import expense_analysis_app

# Sample DataFrame
data = {
    "Date": ["2025-06-20", "2025-06-15", "2025-06-10", "2025-06-04", "2025-05-22", "2025-05-10"],
    "Category": ["Rent", "Groceries", "Shopping", "Subscriptions", "Shopping", "Groceries"],
    "Amount": [2300, 750.25, 1450, 485.52, 1200, 670],
    "Notes": ["Monthly Rent", "Big Bazaar", "Flipkart", "Netflix", "Amazon", "Local Store"]
}
df = pd.DataFrame(data)

# --- Run Pipeline ---
def run_pipeline(query, memory):
    inputs = {
        "query": query,
        "df": df,
        "memory": memory
    }
    output = expense_analysis_app.invoke(inputs)

    updated_memory = output.get("memory", memory)
    result = output.get("result", {})
    text = result.get("text") if isinstance(result, dict) else str(result)

    # Format chat-like Markdown
    chat_md = ""
    for entry in updated_memory:
        user_q = entry.get("query", "")
        assistant_r = entry.get("result", "")
        assistant_r = assistant_r.get("text") if isinstance(assistant_r, dict) else assistant_r

        chat_md += f"**🟢 You:**\n{user_q.strip()}\n\n"
        chat_md += f"**🤖 Assistant:**\n> {assistant_r.strip()}\n\n---\n"

    return text, updated_memory, chat_md

# --- Gradio UI ---
with gr.Blocks() as demo:
    gr.Markdown("## 💬 AI Expense Assistant (Chat Style)")
    
    with gr.Row():
        query = gr.Textbox(label="Type your question", placeholder="e.g. Compare May and June spending", scale=5)
        submit = gr.Button("Submit", scale=1)

    output_box = gr.Textbox(label="Latest Assistant Reply", lines=4)
    chat_log = gr.Markdown(label="🕘 Chat History")

    memory_state = gr.State([])

    # Submit via Enter
    query.submit(fn=run_pipeline, inputs=[query, memory_state], outputs=[output_box, memory_state, chat_log])
    # Submit via Button
    submit.click(fn=run_pipeline, inputs=[query, memory_state], outputs=[output_box, memory_state, chat_log])

demo.launch()
