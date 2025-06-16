import gradio as gr
import pandas as pd
from langgraph_app.graph import expense_analysis_app
from expense_manager.utils.csv_loader import load_and_prepare_csv  # ✅ Custom loader

# ✅ Default state initialization
def init_state():
    data = {
        "Date": ["2025-06-20", "2025-06-15", "2025-06-10", "2025-06-04", "2025-05-22", "2025-05-10"],
        "Category": ["Rent", "Groceries", "Shopping", "Subscriptions", "Shopping", "Groceries"],
        "Amount": [2300, 750.25, 1450, 485.52, 1200, 670],
        "Notes": ["Monthly Rent", "Big Bazaar", "Flipkart", "Netflix", "Amazon", "Local Store"]
    }
    return {
        "df": pd.DataFrame(data),
        "memory": []
    }

# 🧠 Core handler
def run_expense_assistant(query, state):
    if not query.strip():
        return gr.update(), state
    state["query"] = query
    result = expense_analysis_app.invoke(state)
    return result["result"], result

# 📁 File upload logic
def handle_file_upload(file_path):
    df = load_and_prepare_csv(file_path)
    return {"df": df, "memory": []}, gr.update(value=df)

# 🔘 Suggestions
suggestions = [
    "Compare May and June spending",
    "How much did I spend on groceries in May?",
    "Show top 3 expense categories",
    "Summarize my past spending",
]

# 🧼 Gradio UI
with gr.Blocks(theme=gr.themes.Soft(), css="""
.suggestion-button button {
    background-color: #e3f2fd;
    color: #1e88e5;
    margin: 4px;
    border-radius: 10px;
    font-size: 0.8rem;
}
.markdown-box {
    min-height: 180px;
    padding: 1rem;
    border-radius: 12px;
    background-color: #f8f9fa;
    border: 1px solid #ddd;
}
""") as demo:

    gr.Markdown("<h1 style='text-align: center;'>💬 AI Expense Assistant</h1>")

    state = gr.State(init_state())

    # 📁 CSV Upload + Preview
    file_upload = gr.File(label="📁 Upload CSV", type="filepath")
    data_preview = gr.Dataframe(label="📊 Uploaded Data", interactive=False)

    file_upload.change(
        fn=handle_file_upload,
        inputs=file_upload,
        outputs=[state, data_preview]
    )

    # 💬 Input + Output
    query = gr.Textbox(placeholder="Ask a question...", show_label=False)
    output = gr.Markdown(elem_classes="markdown-box")
    submit = gr.Button("Submit")

    # 🔘 Suggested Questions
    with gr.Row():
        for q in suggestions:
            gr.Button(q, elem_classes="suggestion-button") \
                .click(fn=run_expense_assistant, inputs=[gr.State(q), state], outputs=[output, state])

    submit.click(fn=run_expense_assistant, inputs=[query, state], outputs=[output, state])
    query.submit(fn=run_expense_assistant, inputs=[query, state], outputs=[output, state])

    demo.load(lambda: ("", init_state(), init_state()["df"]), outputs=[output, state, data_preview])

if __name__ == "__main__":
    demo.launch()
