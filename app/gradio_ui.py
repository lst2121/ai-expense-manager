import gradio as gr
import pandas as pd
from expense_manager.utils.csv_loader import load_and_prepare_csv
from langgraph_app.graph import expense_analysis_app

### 🔧 Utility: Generate Memory Markdown ###
def generate_memory_markdown(memory: list) -> str:
    if not memory:
        return "_No memory yet._"
    md = "<details><summary>🧠 Memory (click to expand)</summary>\n\n"
    for i, item in enumerate(memory[-5:]):  # Show last 5
        query = item.get("query", "N/A")
        answer = item.get("answer", "N/A")
        md += f"**Q{i+1}:** {query}\n\n"
        md += f"**A{i+1}:** {answer}\n\n---\n"
    md += "</details>"
    return md

### 🔄 File Upload Handler ###
def handle_file_upload(file_obj) -> tuple[dict, gr.Dataframe]:
    if file_obj is None:
        return {"df": pd.DataFrame(), "memory": []}, gr.Dataframe(value=pd.DataFrame())
    df = load_and_prepare_csv(file_obj.name)
    return {"df": df, "memory": []}, gr.Dataframe(value=df)

### 🤖 Main Assistant Logic ###
def run_expense_assistant(query, state: dict) -> tuple[str, str, dict]:
    df = state.get("df", pd.DataFrame())
    memory = state.get("memory", [])

    result = expense_analysis_app.invoke({"query": query, "df": df})

    answer = result.get("result", result.get("answer", "Sorry, I couldn’t understand."))

    memory.append({"query": query, "answer": answer})
    memory_md = generate_memory_markdown(memory)

    return answer, memory_md, {"df": df, "memory": memory}

### 🚀 UI Setup ###
with gr.Blocks(css=".suggestion-button {font-size: 0.85rem !important;}") as demo:
    state = gr.State({"df": pd.DataFrame(), "memory": []})

    gr.Markdown("## 💸 AI Expense Assistant")

    with gr.Row():
        query = gr.Textbox(label="Ask a question", placeholder="e.g. my spendings on groceries in May?")
        submit_btn = gr.Button("🔍 Analyze")

    output = gr.Textbox(label="📢 Assistant Response")
    output_memory = gr.Markdown()

    ### 📁 File Upload ###
    file_input = gr.File(label="📁 Upload Expense CSV", file_types=[".csv"])
    file_input.upload(fn=handle_file_upload, inputs=[file_input], outputs=[state, output])

    ### 🚀 Main Interaction ###
    submit_btn.click(
        fn=run_expense_assistant,
        inputs=[query, state],
        outputs=[output, output_memory, state]
    )

    # ✅ Also trigger on Enter key
    query.submit(
        fn=run_expense_assistant,
        inputs=[query, state],
        outputs=[output, output_memory, state]
    )

    ### 🧠 Auto-suggested Questions ###
    gr.Markdown("#### 💡 Try one of these:")
    suggestions = [
        "Compare May and June spending",
        # "Show average spending by category",
        # "Which month had highest grocery expense?"
        "How much did I spend in June?",
        "Summarize my past spending",
    ]

    for q in suggestions:
        gr.Button(q, elem_classes="suggestion-button").click(
            fn=lambda state, q=q: run_expense_assistant(q, state),
            inputs=[state],
            outputs=[output, output_memory, state]
        )

demo.launch()
