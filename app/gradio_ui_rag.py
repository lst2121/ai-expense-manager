# app/gradio_ui.py

import gradio as gr
import os

from expense_manager.vector_store.vector_db import VectorDB
from expense_manager.chains.expense_chain import create_expense_chain
from expense_manager.vector_store.retriever_chain import create_retriever_chain
from expense_manager.utils.csv_loader import load_and_prepare_csv

# Global objects
retriever_chain = None

# Step 0: Try to load existing vector DB
persist_path = "vector_store/faiss_index"
def try_load_existing_vector_db():
    global retriever_chain
    try:
        vdb = VectorDB(persist_path=persist_path)
        if not os.path.exists(persist_path):
            return None, None, None

        vdb.load()
        llm = create_expense_chain().llm
        retriever = vdb.get_vectorstore()
        retriever_chain = create_retriever_chain(llm=llm, retriever=retriever)

        return None, None, "✅ Loaded default data from existing vector store."

    except Exception as e:
        print("Failed to auto-load vector store:", e)
        return None, None, "❌ Failed to auto-load vector store. Please upload CSV."

# Step 1: Define function to handle file upload
def handle_file_upload(file_obj):
    global retriever_chain

    if not file_obj:
        return "❌ Please upload a valid CSV file.", "", gr.update(visible=False)

    try:
        df = load_and_prepare_csv(file_obj.name)
        vdb = VectorDB(persist_path=persist_path)
        vdb.create_from_dataframe(df)
        vdb.load()

        llm = create_expense_chain().llm
        retriever = vdb.get_vectorstore()
        retriever_chain = create_retriever_chain(llm=llm, retriever=retriever)

        return "✅ File uploaded and processed. Ask your question below.", "", gr.update(visible=True)

    except Exception as e:
        return f"❌ Failed to process file: {str(e)}", "", gr.update(visible=False)

# Step 2: Answer user questions
def answer_question(query):
    if retriever_chain is None:
        return "❌ Please upload a CSV file first.", ""

    try:
        result = retriever_chain(query)
        answer = result.get('result', "No answer found.")
        sources = "\n\n".join([doc.page_content for doc in result.get("source_documents", [])])
        return answer, sources if sources else "No source documents found."

    except Exception as e:
        return f"❌ Error: {str(e)}", ""

# Step 3: Gradio UI layout
with gr.Blocks() as ui:
    gr.Markdown("## 💸 AI Expense Assistant\nUpload your expense CSV file and ask questions about it!")

    with gr.Row():
        file_input = gr.File(label="📄 Upload your CSV file", file_types=[".csv"])
        upload_btn = gr.Button("📤 Upload and Process")

    status = gr.Textbox(label="Status", interactive=False)

    question_input = gr.Textbox(label="Enter your question", placeholder="e.g., What were my top 3 expenses?", visible=False)
    question_btn = gr.Button("Ask")
    answer_output = gr.Textbox(label="Answer")
    sources_output = gr.Textbox(label="Source Documents", lines=6)

    upload_btn.click(fn=handle_file_upload, inputs=[file_input], 
                     outputs=[status, answer_output, question_input])

    # Trigger Q&A via both Enter and button click
    question_input.submit(fn=answer_question, inputs=question_input, 
                          outputs=[answer_output, sources_output])
    question_btn.click(fn=answer_question, inputs=question_input, 
                       outputs=[answer_output, sources_output])

    # Try to load default data from persisted vector DB
    _, _, default_status = try_load_existing_vector_db()
    if default_status:
        status.value = default_status
        question_input.visible = True

# Step 4: Run app
if __name__ == "__main__":
    ui.launch()
