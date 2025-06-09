import streamlit as st
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOpenAI
import os

api_key = os.getenv("OPENROUTER_API_KEY")  # Ensure key is loaded
if not api_key:
    st.error("Missing OpenRouter API key!")

# OpenRouter API Key (Replace with your actual key)
OPENROUTER_API_KEY = "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"

# Base URL for OpenRouter API
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Embedding model (Replacing OpenAI embeddings)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

st.markdown("<h1 style='text-align: center;'>Chatbot (OpenRouter)</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.title("Your Documents")
    file = st.file_uploader("Upload a PDF file and start asking questions", type="pdf")

text = ""

if file is not None:
    pdf_reader = PdfReader(file)
    for page in pdf_reader.pages:
        text += page.extract_text()

    st.write("Extracted Text Length:", len(text))

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        separators="\n",
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len
    )
    chunks = text_splitter.split_text(text)

    st.write("Number of Chunks:", len(chunks))

    # Create FAISS vector store
    vector_store = FAISS.from_texts(chunks, embeddings)
    st.write("Vector Store Created")

    user_question = st.text_input("Type your question here")

    if user_question:
        st.write("User Question Received:", user_question)

        # Perform similarity search
        match = vector_store.similarity_search(user_question)
        context = "\n".join([doc.page_content for doc in match])

        st.write("Similarity Search Completed, Matches Found:", len(match))

        # Use OpenRouter Chat API (Mistral-7B or GPT-4)
        llm = ChatOpenAI(
            openai_api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=0.7,
            max_tokens=512,
            model_name="mistralai/mistral-7b-instruct"  # You can also try "gpt-4-turbo" & mistralai/mistral-7b-instruct
        )

        st.write("LLM Object Created")

        # Generate response using retrieved context
        prompt = f"Use the following context to answer:\n\n{context}\n\nQuestion: {user_question}\n\nAnswer:"
        response = llm.invoke(prompt)
        st.write("### Raw API Response:", response)  # Debug output

        #st.write("### Answer:")
        #st.write(response)
    