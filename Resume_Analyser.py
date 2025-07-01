from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.utils import secure_filename
import os
import re
import docx
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
import markdown  # Add this import
from collections import defaultdict

app = Flask(__name__,template_folder=r"C:\Users\Sahanar\Desktop\VScode")
app.secret_key = "your-secret-key"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# OpenAI Config
API_KEY = "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"  # Replace with your actual key
BASE_URL = "https://api.openai.com/v1"
EMBEDDING_MODEL = "text-embedding-3-small"

embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    openai_api_key=API_KEY
)

vector_store = None
chat_history = []

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return "\n".join([p.extract_text() for p in PdfReader(file_path).pages if p.extract_text()])
    elif ext == ".docx":
        return "\n".join([p.text for p in docx.Document(file_path).paragraphs])
    return ""

@app.route("/", methods=["GET", "POST"])
def index():
    global vector_store
    if request.method == "POST":
        uploaded_files = request.files.getlist("documents")
        all_chunks, chunk_file_map = [], []
        for file in uploaded_files:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            text = extract_text(path)
            print(f"[DEBUG] Extracted text from {filename}:\n{text[:500]}")  # Print first 500 chars
            chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_text(text)
            all_chunks.extend(chunks)
            chunk_file_map.extend([filename] * len(chunks))

        vector_store = FAISS.from_texts(all_chunks, embeddings, metadatas=[{"file_name": fn} for fn in chunk_file_map])
        session["files_uploaded"] = [file.filename for file in uploaded_files]
        return redirect("/")
    # Convert assistant answers from Markdown to HTML
    chat_history_html = []
    for chat in chat_history:
        if chat["role"] == "assistant":
            content = chat["content"]
            # Remove code block markers and 'markdown' for tables
            content = re.sub(r"^```(?:markdown)?\s*", "", content)
            content = re.sub(r"```$", "", content)
            content = markdown.markdown(content, extensions=['tables'])
        else:
            content = chat["content"]
        chat_history_html.append({"role": chat["role"], "content": content})
    return render_template(
        "CV Analyser 1.html",
        chat_history=chat_history_html,
        files_uploaded=session.get("files_uploaded", [])
    )

@app.route("/ask", methods=["POST"])
def ask():
    global vector_store
    try:
        data = request.get_json()
        question = data.get("question", "")

        if not vector_store:
            return jsonify({"answer": "Please upload documents first."})

        docs = vector_store.similarity_search(question, k=2000)

        # Collect top N chunks per file
        N = 10  # or 5, depending on context window
        file_chunks = defaultdict(list)
        for doc in docs:
            file_name = doc.metadata.get("file_name")
            if len(file_chunks[file_name]) < N:
                file_chunks[file_name].append(doc)

        # Flatten to a list: each file gets up to N chunks
        input_docs = [chunk for chunks in file_chunks.values() for chunk in chunks]

        llm = ChatOpenAI(
            openai_api_key=API_KEY,
            base_url=BASE_URL,
            temperature=0.3,
            model_name="gpt-4o",
            max_tokens=2000
        )

        chain = load_qa_chain(llm, chain_type="stuff")

        prompt = f"""
        You are a smart assistant analyzing uploaded resumes.

        - Respond to this user question: **{question}**
        - If the question involves listing, comparing, or extracting structured data, use a **Markdown table**.
        - If the question is about extracting candidate details, extract **all candidates** and their details (such as Name, Education, Skills, Experience/Projects, etc.) from the uploaded resumes.
        - If the question is about a specific skill (e.g., Python), only list candidates who explicitly mention that skill in their skills section.
        - Avoid repeating file names or unnecessary headings.
        - Do not include candidates who do not mention the skill.
        - Be precise and concise.
        """

        # Auto-hint formatting if keywords detected
        if any(k in question.lower() for k in ["list", "compare", "table", "summary", "summarize", "details"]):
            prompt += "\n- Format your response as a **Markdown table**."

        answer = chain.run(input_documents=input_docs, question=prompt)

        # Only apply name-list formatting for very specific questions
        if re.search(r"\bwho\s+has\s+python\b", question.lower()):
            matches = re.findall(r"\| *([A-Z][^\|]+?) *\|", answer, flags=re.IGNORECASE)
            if matches:
                answer = "\n".join(f"- {name.strip()}" for name in matches[1:])

        chat_history.append({"role": "user", "content": question})
        chat_history.append({"role": "assistant", "content": answer})
        return jsonify({"answer": answer})

    except Exception as e:
        print(f"[ERROR] Exception in /ask: {str(e)}")
        return jsonify({"answer": "An error occurred while processing your question."})

@app.route("/clear_chat")
def clear_chat():
    global chat_history
    chat_history.clear()
    return redirect("/")

@app.route("/clear_files")
def clear_files():
    global vector_store
    vector_store = None
    session.pop("files_uploaded", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
