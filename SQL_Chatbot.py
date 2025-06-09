from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.utils import secure_filename
import os
from PyPDF2 import PdfReader
import docx
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
from pyngrok import ngrok

app = Flask(__name__,template_folder=r"C:\Users\Sahanar\Desktop\VScode")
app.secret_key = "your-secret-key"
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
public_url = ngrok.connect(5000)
print(" * ngrok tunnel URL:", public_url)

# LLM config
API_KEY = "328875e268ad9d5706701de2907d3022398629a7bd19bc70c63b3dbc650accfb"
BASE_URL = "https://api.together.xyz/v1"
EMBEDDING_MODEL = "microsoft/codebert-base"
#"huggingface/CodeBERTa-small-v1"
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

vector_store = None
chat_history = []

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return "\n".join([p.extract_text() for p in PdfReader(file_path).pages if p.extract_text()])
    elif ext == ".docx":
        return "\n".join([p.text for p in docx.Document(file_path).paragraphs])
    elif ext == ".csv":
        df = pd.read_csv(file_path)
        return "\n".join([f"{c}:\n" + "\n".join(df[c].astype(str)) for c in df.columns])
    elif ext == ".xlsx":
        df = pd.read_excel(file_path)
        return "\n".join([f"{c}:\n" + "\n".join(df[c].astype(str)) for c in df.columns])
    elif ext in [".txt", ".sql"]:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    return ""

@app.route("/", methods=["GET", "POST"])
def index():
    global vector_store
    if request.method == "POST":
        uploaded_files = request.files.getlist("documents")
        all_text = ""
        for file in uploaded_files:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            all_text += extract_text(path) + "\n"

        chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_text(all_text)
        vector_store = FAISS.from_texts(chunks, embeddings)
        session["files_uploaded"] = [file.filename for file in uploaded_files]
        return redirect("/")

    return render_template("index.html", chat_history=chat_history, files_uploaded=session.get("files_uploaded", []))

@app.route("/ask", methods=["POST"])
def ask():
    global vector_store
    data = request.get_json()
    question = data.get("question", "")

    print(f"[DEBUG] Received question: {question}")

    if not vector_store:
        print("[DEBUG] No vector_store found. Returning upload prompt.")
        return jsonify({"answer": "Please upload documents first."})

    docs = vector_store.similarity_search(question, k=20)
    print(f"[DEBUG] Retrieved {len(docs)} relevant documents.")

    llm = ChatOpenAI(
        openai_api_key=API_KEY,
        base_url=BASE_URL,
        temperature=0.5,
        model_name="mistralai/Mixtral-8x7B-Instruct-v0.1",
        max_tokens=2000
    )

    chain = load_qa_chain(llm, chain_type="stuff")
    table_keywords = ["table", "tables", "columns", "schema", "structure", "fields"]
    files_uploaded = session.get("files_uploaded", [])
    file_heading = f"### File: {files_uploaded[0]}\n" if files_uploaded else ""
    if any(kw in question.lower() for kw in table_keywords):
        table_prompt = f"""Return ONLY a Markdown heading with the file name at the top, followed by a Markdown table with columns 'Table Name' and 'Columns'. Do NOT include any text, lists, or explanations before or after the heading and table. Example:\n### File: {files_uploaded[0] if files_uploaded else 'your_file.sql'}\n| Table Name | Columns |\n|---|---|\n| customers | customer_id, customer_name |\n| orders | order_id, customer_id, order_date, total_amount |\nQuestion: {question}"""
    else:
        table_prompt = f"""Answer the question with the uploaded documents. Format output as Markdown.\nQuestion: {question}"""

    print(f"[DEBUG] Prompt sent to LLM:\n{table_prompt}")

    answer = chain.run(input_documents=docs, question=table_prompt)
    print(f"[DEBUG] LLM response:\n{answer}")

    chat_history.append({"role": "user", "content": question})
    chat_history.append({"role": "assistant", "content": answer})
    return jsonify({"answer": answer})

@app.route("/clear")
def clear_chat():
    global chat_history, vector_store
    chat_history.clear()
    vector_store = None
    session.pop("files_uploaded", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
