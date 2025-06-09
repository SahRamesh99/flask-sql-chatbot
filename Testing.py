import streamlit as st
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain

# OpenRouter API Key (Replace with your actual key)
OPENROUTER_API_KEY = "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"

# Base URL for OpenRouter API
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Embedding model (Replacing OpenAI embeddings)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# Upload PDF Files
st.markdown("<h1 style='text-align: center;'>Chatbot</h1>", unsafe_allow_html=True)
with st.sidebar:
    st.title("Your Documents")
    file = st.file_uploader("Upload a PDF file and start asking questions", type="pdf")

text = ""
# Extract the text
if file is not None:
    pdf_reader = PdfReader(file)
    for page in pdf_reader.pages:
        text += page.extract_text()

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n"],
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len
    )
    chunks = text_splitter.split_text(text)

    # Create FAISS vector store
    vector_store = FAISS.from_texts(chunks, embeddings)

    # Get User question
    user_question = st.text_input("Type your question here")

    if user_question:
    # Perform similarity search (retrieve more chunks for better context)
        match = vector_store.similarity_search(user_question, k=5)

    # Ensure match is always a list (even if empty)
        if not match:
            match = []

        if len(match) > 0:  # If relevant content is found
            context = "\n".join([doc.page_content for doc in match])

            prompt = f"""
            You are an AI assistant trained to answer questions accurately based on the provided document.
            If the answer is not available in the document, respond with 'I don't know' instead of making up information.

            Context from the document:
            {context}

            Question: {user_question}

            Answer:
            """
        else:
        # If no relevant document is found, allow GPT-4 to answer freely
            prompt = f"""
            You are a helpful AI assistant. Answer the following question as accurately as possible.

            Question: {user_question}

            Answer:
            """

    # Use OpenRouter Chat API with GPT-4-Turbo
        llm = ChatOpenAI(
            openai_api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=0.7,
            max_tokens=512,
            model_name="mistralai/mistral-7b-instruct"
        )

    # Use "stuff" for document-based QA, otherwise just chat freely
        chain = load_qa_chain(llm, chain_type="stuff")

    # Fix: Ensure `match` is a list before passing it
        response = chain.run(input_documents=match if match else [], question=prompt)
        st.write(response)
