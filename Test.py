

import streamlit as st
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
import os

# OpenRouter API Key (Replace with your actual key)
OPENROUTER_API_KEY="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"

# Base URL for OpenRouter API
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Embedding model (Replacing OpenAI embeddings)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# Upload PDF Files
#st.header("Chatbot")
st.markdown("<h1 style='text-align: center;'>Chatbot</h1>", unsafe_allow_html=True)
with st.sidebar:
     st.title("Your Documents")
     file=st.file_uploader("Upload a PDF file and start asking questions",type="pdf")
    # run to see the initial result, python -m streamlit run Test.py, it will ask you for email, just press enter

text=""
#Extract the text
if file is not None:
     pdf_reader=PdfReader(file)
     for page in pdf_reader.pages:
          text=text+page.extract_text()
          # st.write(text) 

    # Break it into chunks, why? for better understanding on each section 
     text_splitter=RecursiveCharacterTextSplitter(
          separators="\n",
          chunk_size=1000,
          chunk_overlap=150,
          length_function=len
     )
     chunks=text_splitter.split_text(text)
     #st.write(chunks)

     # Creating vector stores
     vector_store=FAISS.from_texts(chunks,embeddings)

     # Get User question
     user_question=st.text_input("Type your question here")

     # Do similarity search
     if user_question:
          #search
          match=vector_store.similarity_search(user_question)
          context = "\n".join([doc.page_content for doc in match])
          #st.write(match)

          llm=ChatOpenAI(
               openai_api_key=OPENROUTER_API_KEY,
               base_url=OPENROUTER_BASE_URL,
               temperature=0.7,
               max_tokens=512,
               model_name="mistralai/mistral-7b-instruct"
          )

          # Output result
          #chain=load_qa_chain(llm,chain_type="stuff")
          #response=chain.run(input_documents=match,question=user_question)
          #st.write(response)

          prompt = f"Use the following context to answer:\n\n{context}\n\nQuestion: {user_question}\n\nAnswer:"
          response = llm.invoke(prompt)

          st.write("### Answer:")
          st.write(response)