from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.utils import secure_filename
import os
import io
from flask import send_file
import csv
import re
import docx
from PyPDF2 import PdfReader
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain

app = Flask(__name__,template_folder=r"C:\Users\Sahanar\Desktop\VScode")
app.secret_key = "your-secret-key"
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# LLM config
API_KEY = "328875e268ad9d5706701de2907d3022398629a7bd19bc70c63b3dbc650accfb"
BASE_URL = "https://api.together.xyz/v1"
EMBEDDING_MODEL = "microsoft/codebert-base"
#EMBEDDING_MODEL = "huggingface/CodeBERTa-small-v1"
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
        all_chunks = []
        chunk_file_map = []  # To keep track of which file each chunk came from
        for file in uploaded_files:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            text = extract_text(path)
            chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_text(text)
            all_chunks.extend(chunks)
            chunk_file_map.extend([filename] * len(chunks))

        # Store both chunks and their file names in the vector store as metadata
        vector_store = FAISS.from_texts(all_chunks, embeddings, metadatas=[{"file_name": fn} for fn in chunk_file_map])
        session["files_uploaded"] = [file.filename for file in uploaded_files]
        return redirect("/")

    return render_template("index 1.html", chat_history=chat_history, files_uploaded=session.get("files_uploaded", []))

@app.route("/ask", methods=["POST"])
def ask():
    global vector_store
    data = request.get_json()
    question = data.get("question", "")

    if not vector_store:
        return jsonify({"answer": "Please upload documents first."})

    # Get top k docs with metadata
    docs = vector_store.similarity_search(question, k=20)
    # Find the file name from the most relevant chunk (first doc)
    file_name = None
    if docs and hasattr(docs[0], 'metadata') and 'file_name' in docs[0].metadata:
        file_name = docs[0].metadata['file_name']
    else:
        # fallback to session or default
        files_uploaded = session.get("files_uploaded", [])
        file_name = files_uploaded[0] if files_uploaded else "uploaded_file"

    llm = ChatOpenAI(
        openai_api_key=API_KEY,
        base_url=BASE_URL,
        temperature=0.5,
        model_name="mistralai/Mixtral-8x7B-Instruct-v0.1",
        max_tokens=2000
    )

    chain = load_qa_chain(llm, chain_type="stuff")

    # Dynamically detect if the question is about tables/columns/schema/fields
    table_keywords = ["table", "tables", "columns", "schema", "structure", "fields"]
    if any(kw in question.lower() for kw in table_keywords):
        table_prompt = f"""
            You are an intelligent assistant analyzing uploaded documents.

            - If the answer contains structured or tabular information (like rows of data, comparisons, columns, key-value pairs, or records), format **only that part** as a Markdown table.
            - Keep the rest of the response in plain, readable Markdown text.
            - If you provide a table, add a Markdown heading at the top with the file name: **File: {file_name}**

            Example:
            Question: What are the employee details?
            Answer:

            **File: employees.csv**
            | Name   | Department | Salary |
            |--------|------------|--------|
            | Alice  | HR         | 50000  |
            | Bob    | IT         | 60000  |

            Now, answer this question:
            Question: {question}
            """
    else:
        table_prompt = f"""
            You are an intelligent assistant analyzing uploaded documents.

            - If the answer contains structured or tabular information (like rows of data, comparisons, columns, key-value pairs, or records), format **only that part** as a Markdown table.
            - Keep the rest of the response in plain, readable Markdown text.

            Example:
            Question: What are the employee details?
            Answer:

            | Name   | Department | Salary |
            |--------|------------|--------|
            | Alice  | HR         | 50000  |
            | Bob    | IT         | 60000  |

            Now, answer this question:
            Question: {question}
            """


    answer = chain.run(input_documents=docs, question=table_prompt)

    def ensure_file_heading(answer, file_name):
        # Look for the first Markdown table
        table_match = re.search(r'(\n\|.+\|\n\|[-| ]+\|\n(?:\|.*\|\n)+)', answer)
        heading = f'**File: {file_name}**\n'
        if table_match:
            # Check if heading is already above the table
            before_table = answer[:table_match.start()]
            if heading.strip() not in before_table:
                # Insert heading above the table
                answer = before_table.rstrip() + '\n' + heading + answer[table_match.start():]
        return answer

    # --- Ensure file name heading is above the first Markdown table if needed, and remove lists above table ---
    def clean_table_answer(answer, file_name):
        # Find the first Markdown table
        table_match = re.search(r'(\n\|.+\|\n\|[-| ]+\|\n(?:\|.*\|\n)+)', answer)
        heading = f'**File: {file_name}**\n'
        if table_match:
            # Only keep the heading and the table, remove everything before the table
            table_start = table_match.start()
            table_text = answer[table_start:]
            return heading + table_text
        return answer

    if any(kw in question.lower() for kw in table_keywords):
        answer = clean_table_answer(answer, file_name)
    else:
        answer = ensure_file_heading(answer, file_name)
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
    app.run(debug=True,host='0.0.0.0', port=5000)



