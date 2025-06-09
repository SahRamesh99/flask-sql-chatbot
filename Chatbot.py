import streamlit as st
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain

# OpenRouter API Key (Replace with your actual key)
OPENROUTER_API_KEY = "328875e268ad9d5706701de2907d3022398629a7bd19bc70c63b3dbc650accfb"

# Base URL for OpenRouter API
OPENROUTER_BASE_URL = "https://api.together.xyz/v1"

# Embedding model (Replacing OpenAI embeddings)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# Upload PDF Files
st.markdown("<h1 style='text-align: center;'>Chatbot</h1>", unsafe_allow_html=True)
with st.sidebar:
    st.title("Your Documents")
    file = st.file_uploader("Upload a PDF file and start asking questions", type="pdf")
     # run to see the initial result, python -m streamlit run filename.py, it will ask you for email, just press enter

text = ""
#Extract the text
if file is not None:
    pdf_reader = PdfReader(file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    #st.write("Extracted Text Length:", len(text))

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        separators="\n",
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    #st.write("Number of Chunks:", len(chunks))

    # Create FAISS vector store
    vector_store = FAISS.from_texts(chunks, embeddings)
    #st.write("Vector Store Created")

    # Get User question
    user_question = st.text_input("Type your question here")

    if user_question:
        #st.write("User Question Received:", user_question)
        # Perform similarity search
        match = vector_store.similarity_search(user_question)
        context = "\n".join([doc.page_content for doc in match])
        #st.write("Similarity Search Completed, Matches Found:", len(match))
            
        # Use OpenRouter Chat API (Mistral-7B or GPT-4)
        llm = ChatOpenAI(
                openai_api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=0.7,
                max_tokens=512,
                model_name="mistralai/Mixtral-8x7B-Instruct-v0.1" # mistralai/mistral-7b-instruct
            )

        #st.write("LLM Object Created")

         #Output result
        chain = load_qa_chain(llm, chain_type="stuff")
        response=chain.run(input_documents=match,question=user_question)
        st.write(response)
    