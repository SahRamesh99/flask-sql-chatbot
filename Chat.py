import streamlit as st
import pandas as pd
import sqlite3
import re
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
import docx
import sqlparse

# ========== Configuration ==========
OPENROUTER_API_KEY = "55214e4596a5fbf44bfa9bddb99c001cefd864172e09d3ff09a602a8292c9c92"
OPENROUTER_BASE_URL = "https://api.together.xyz/v1"
EMBEDDING_MODEL = "huggingface/CodeBERTa-small-v1"
#"intfloat/e5-base-v2"
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# ========== File Text Extraction ==========
def extract_pdf_text(file):
    reader = PdfReader(file)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

def extract_docx_text(file):
    return "\n".join([p.text for p in docx.Document(file).paragraphs])

def extract_csv_text(file, file_table_info):
    df = pd.read_csv(file)
    file_table_info[file.name] = {"CSV Table": {"columns": df.columns.tolist(), "data": df}}
    return df.to_string()

#def extract_excel_text(file, file_table_info):
    #df = pd.read_excel(file)
    #file_table_info[file.name] = {"Excel Table": {"columns": df.columns.tolist(), "data": df}}
    #return df.to_string()

def extract_excel_text(file, file_table_info):

    excel_data = pd.read_excel(file, sheet_name=None)  # Read all sheets
    file_table_info[file.name] = {}

    combined_text = ""
    for sheet_name, df in excel_data.items():
        # Save sheet as table with its data
        file_table_info[file.name][sheet_name] = {
            "columns": df.columns.tolist(),
            "data": df
        }

        combined_text += f"Sheet: {sheet_name}\n"
        combined_text += df.to_string(index=False)
        combined_text += "\n\n"

        # Try to detect and parse SQL queries in 'Query' column or similar
        sql_col_candidates = [col for col in df.columns if re.search(r'query|sql', col, re.IGNORECASE)]
        for sql_col in sql_col_candidates:
            for sql_text in df[sql_col].dropna():
                # Parse SQL using logic from extract_sql_text
                statements = sqlparse.split(sqlparse.format(str(sql_text), strip_comments=True))
                for stmt in statements:
                    stmt_clean = stmt.strip()
                    match = re.match(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([^\s(]+)", stmt_clean, re.IGNORECASE)
                    if not match:
                        continue

                    table_name = match.group(1).split('.')[-1]
                    column_names = []

                    if '(' in stmt_clean and 'AS' not in stmt_clean.upper():
                        col_block_match = re.search(r'\((.*?)\)', stmt_clean, re.DOTALL)
                        if col_block_match:
                            col_lines = col_block_match.group(1).splitlines()
                            for line in col_lines:
                                line = line.strip().rstrip(',')
                                col_match = re.match(r'[`"]?(\w+)[`"]?\s+\w+', line)
                                if col_match:
                                    column_names.append(col_match.group(1))

                    # Save SQL table metadata under file_table_info
                    file_table_info[file.name][table_name] = {
                        "columns": column_names,
                        "data": None
                    }

    return combined_text

#def extract_sql_text(file, file_table_info):
    #raw_sql = file.read().decode("utf-8", errors="ignore")
    #conn = sqlite3.connect(":memory:")
    #cursor = conn.cursor()
    #try:
        #cursor.executescript(raw_sql)
        #cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        #tables = [t[0] for t in cursor.fetchall()]
        #file_table_info[file.name] = {}
        #sql_output = ""
        #for table in tables:
            #df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            #file_table_info[file.name][table] = {"columns": df.columns.tolist(), "data": df}
            #sql_output += f"Table: {table}\nColumns: {', '.join(df.columns)}\n\n"
        #return sql_output
    #except Exception as e:
        #return f"Failed to process SQL file: {e}"
    
#def extract_sql_text(file, file_table_info):
    #raw_sql = file.read().decode("utf-8", errors="ignore")
    #file_table_info[file.name] = {}
    #sql_output = ""

    #Match CREATE TABLE statements
    #table_defs = re.findall(r'CREATE TABLE\s+`?(\w+)`?\s*\((.*?)\);', raw_sql, re.DOTALL | re.IGNORECASE)

    #for table_name, columns_block in table_defs:
        #column_lines = [line.strip() for line in columns_block.splitlines() if line.strip() and not line.strip().upper().startswith("PRIMARY KEY")]
        #column_names = []
        #for col_line in column_lines:
             #Try to capture column name; ignore constraints like PRIMARY KEY
            #col_match = re.match(r'`?(\w+)`?\s+\w+', col_line)
            #if col_match:
                #column_names.append(col_match.group(1))
        #file_table_info[file.name][table_name] = {
            #"columns": column_names,
            #"data": None  # No data loaded since we’re not executing SQL
        #}
        #sql_output += f"Table: {table_name}\nColumns: {', '.join(column_names)}\n\n"

    #if not file_table_info[file.name]:
        #return "No valid CREATE TABLE statements found."
    #return sql_output

#def extract_sql_text(file, file_table_info):

    #raw_sql = file.read().decode("utf-8", errors="ignore")
    #file_table_info[file.name] = {}
    #sql_output = ""

    # Improved CREATE TABLE regex (supports IF NOT EXISTS and various quote styles)
    #table_defs = re.findall(
        #r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?[`"]?(\w+)[`"]?\s*\((.*?)\)\s*;',
        #raw_sql,
        #re.DOTALL | re.IGNORECASE
    #)

    #for table_name, columns_block in table_defs:
        # Clean and filter out constraint lines
        #column_lines = [
            #line.strip()
            #for line in columns_block.splitlines()
            #if line.strip() and not re.match(r'(?i)PRIMARY KEY|CONSTRAINT|FOREIGN KEY|UNIQUE|CHECK', line.strip())
        #]

        #column_names = []
        #for col_line in column_lines:
            #col_match = re.match(r'[`"]?(\w+)[`"]?\s+\w+', col_line)
            #if col_match:
                #column_names.append(col_match.group(1))

        # Store metadata (no data available here)
        #file_table_info[file.name][table_name] = {
            #"columns": column_names,
            #"data": None
        #}

        #sql_output += f"Table: {table_name}\nColumns: {', '.join(column_names)}\n\n"

    #if not file_table_info[file.name]:
        #return "No valid CREATE TABLE statements found."
    #return sql_output

def extract_sql_text(file, file_table_info):
    import sqlparse
    raw_sql = file.read().decode("utf-8", errors="ignore")
    file_table_info[file.name] = {}
    sql_output = ""

    statements = sqlparse.split(sqlparse.format(raw_sql, strip_comments=True))

    for stmt in statements:
        stmt_clean = stmt.strip()
        match = re.match(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([^\s(]+)", stmt_clean, re.IGNORECASE)
        if not match:
            continue

        table_name = match.group(1).split('.')[-1]
        column_names = []

        if '(' in stmt_clean and 'AS' not in stmt_clean.upper():
            col_block_match = re.search(r'\((.*?)\)', stmt_clean, re.DOTALL)
            if col_block_match:
                col_lines = col_block_match.group(1).splitlines()
                for line in col_lines:
                    line = line.strip().rstrip(',')
                    col_match = re.match(r'[`"]?(\w+)[`"]?\s+\w+', line)
                    if col_match:
                        column_names.append(col_match.group(1))
        elif 'AS' in stmt_clean.upper():
            # Extract from SELECT portion
            select_match = re.search(r'AS\s+SELECT\s+(.*?)\s+FROM\s', stmt_clean, re.IGNORECASE | re.DOTALL)
            if select_match:
                col_part = select_match.group(1)
                col_part = re.sub(r'\s+AS\s+', ' as ', col_part, flags=re.IGNORECASE)
                col_tokens = re.split(r',\s*(?![^()]*\))', col_part)
                for token in col_tokens:
                    token = token.strip().replace('\n', ' ')
                    alias_match = re.search(r'\s+as\s+(\w+)$', token, re.IGNORECASE)
                    if alias_match:
                        column_names.append(alias_match.group(1))
                    else:
                        fallback = token.split('.')[-1].split()[-1]
                        if fallback.lower() not in ["from", "select", "case", "when", "else", "end"]:
                            column_names.append(fallback)

        file_table_info[file.name][table_name] = {
            "columns": column_names,
            "data": None
        }
        sql_output += f"Table: {table_name}\nColumns: {', '.join(column_names) if column_names else 'N/A'}\n\n"

    if not file_table_info[file.name]:
        return "No valid CREATE TABLE statements found."
    return sql_output

# ========== Streamlit UI ==========
st.markdown("<h1 style='text-align: center;'>📄 Document Q&A Chatbot</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.title("📁 Upload Files")
    files = st.file_uploader("Upload PDF, DOCX, CSV, Excel, or SQL files", type=["pdf", "docx", "csv", "xlsx", "sql"], accept_multiple_files=True)

all_text = ""
documents = []
file_table_info = {}

# ========== Process Uploaded Files ==========
if files:
    for file in files:
        try:
            if file.name.endswith(".pdf"):
                text = extract_pdf_text(file)
            elif file.name.endswith(".docx"):
                text = extract_docx_text(file)
            elif file.name.endswith(".csv"):
                text = extract_csv_text(file, file_table_info)
            elif file.name.endswith(".xlsx"):
                text = extract_excel_text(file, file_table_info)
            elif file.name.endswith(".sql"):
                file.seek(0)
                text = extract_sql_text(file, file_table_info)
            else:
                text = file.read().decode("utf-8", errors="ignore")
            all_text += text + "\n"
            documents.append(text)
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")

    # ========== Build Vector Store ==========
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_text(all_text)
    vector_store = FAISS.from_texts(chunks, embeddings)

    # ========== User Input ==========
    user_question = st.text_input("💬 Ask your question:")

    if user_question:
        question_lower = user_question.lower()

        # === Dimensions and Measures ===
        if "list of dimensions and measures" in question_lower:
            st.subheader(" Dimensions and Measures by File")

            for fname, tables in file_table_info.items():
                st.markdown(f"### File: `{fname}`")

                # Extract dimensions
                #dimensions = set()
                #for table_info in tables.values():
                    #df = table_info.get("data")
                    #if df is not None:
                        #dims = df.select_dtypes(exclude=["number"]).columns.tolist()
                    #dimensions.update(table_info.get("columns", []))
                        #dimensions.update(dims)
                
                # Extract dimensions
                dimensions = set()
                for table_info in tables.values():
                    df = table_info.get("data")
                    cols = table_info.get("columns", [])

                    if df is not None:
                        dims = df.select_dtypes(exclude=["number"]).columns.tolist()
                        dimensions.update(dims)
                    else:
        # Infer likely dimensions from column names if no data
                        for col in cols:
                            if re.search(r'name|type|code|status|date|email|address|city|state|country|description', col, re.IGNORECASE):
                                dimensions.add(col)

                # Extract measures (for SQL only)
                measures = set()
                if fname.endswith(".sql"):
                    try:
                        uploaded_file = next((f for f in files if f.name == fname), None)
                        if uploaded_file:
                            uploaded_file.seek(0)
                            #raw_sql = uploaded_file.read().decode("utf-8", errors="ignore").lower()
                            raw_sql = uploaded_file.read().decode("utf-8", errors="ignore")
                            pattern = r"(sum|avg|count|max|min)\s*\((.*?)\)\s*(?:as\s+(\w+))?"
                            #matches = re.findall(r"(sum|avg|count|max|min)\s*\(.*?\)\s+as\s+(\w+)", raw_sql)
                            matches = re.findall(pattern, raw_sql, flags=re.IGNORECASE)
                            for func, expr, alias in matches:
                                label = f"{alias} ({func.upper()}({expr}))" if alias else f"{func.upper()}({expr})"
                                measures.add(label)
                            #measures = {alias for _, alias in matches}
                    except Exception as e:
                        st.warning(f"Could not extract measures from {fname}: {e}")

                # Display in table format
                #df_result = pd.DataFrame({
                    #"Dimensions": pd.Series(list(dimensions)),
                    #"Measures": pd.Series(list(measures))
                #})
                #st.dataframe(df_result, use_container_width=True)

                st.markdown("Dimensions:")
                #st.write(sorted(dimensions) if dimensions else "None found.")
                for dim in sorted(dimensions):
                    st.markdown(f"- {dim}")

                st.markdown("Measures:")
                #st.write(sorted(measures) if measures else "None found.")
                for meas in sorted(measures):
                    st.markdown(f"- {meas}")


        # === List of Tables ===
        elif "list of tables" in question_lower or "list tables" in question_lower:
            st.subheader("📂 Tables by File")
            for fname, tables in file_table_info.items():
                if fname.endswith(".sql"):
                    st.markdown(f"**File: {fname}**")
                    table_list = []
                    for table_name, content in tables.items():
                        cols = content.get("columns", [])
                        table_list.append([table_name, ', '.join(cols)])
                    if table_list:
                        table_df = pd.DataFrame(table_list, columns=["Table Name", "Columns"])
                        st.dataframe(table_df, use_container_width=True)
                    else:
                        st.write("No tables found in this file.")

        # === General Q&A ===
        else:
            matches = vector_store.similarity_search(user_question, k=10)
            context = "\n".join([doc.page_content if hasattr(doc, "page_content") else doc for doc in matches])
            if len(context.split()) > 3000:
                context = " ".join(context.split()[:3000])

            llm = ChatOpenAI(
                openai_api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=0.7,
                max_tokens=2000,
                model_name="mistralai/Mixtral-8x7B-Instruct-v0.1"
            )
            chain = load_qa_chain(llm, chain_type="stuff")
            response = chain.run(input_documents=matches, question=user_question)
            st.write(response)
    