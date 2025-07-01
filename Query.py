import pyodbc
from flask import Flask, render_template_string, request
import openai
import re

app = Flask(__name__)

HTML = """
<!doctype html>
<title>SQL Chatbot</title>
<h2>SQL Chatbot for AdventureWorks2022</h2>
<form method="post">
    <textarea name="query" rows="4" cols="80" placeholder="Enter your SQL query here">{{query}}</textarea><br>
    <input type="submit" value="Run Query">
</form>
{% if error %}
    <p style="color:red;">Error: {{error}}</p>
{% endif %}
{% if success %}
    <p style="color:green;">{{success}}</p>
{% endif %}
{% if columns %}
    <table border="1" cellpadding="5">
        <tr>{% for col in columns %}<th>{{col}}</th>{% endfor %}</tr>
        {% for row in rows %}
            <tr>{% for cell in row %}<td>{{cell}}</td>{% endfor %}</tr>
        {% endfor %}
    </table>
{% endif %}
{% if sql %}
    <p><b>Generated SQL:</b> {{sql}}</p>
{% endif %}
{% if explanation %}
    <p><b>Explanation:</b> {{explanation}}</p>
{% endif %}
"""

def get_supported_columns(table_schema, table_name):
    # Exclude columns with unsupported types (e.g., geometry, geography, hierarchyid)
    conn = pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=9M7LKJ2\SQLEXPRESS;'
        r'DATABASE=AdventureWorks2022;'
        r'UID=sa;'
        r'PWD=Sahana@123;'
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
    """, (table_schema, table_name))
    supported = [row[0] for row in cursor.fetchall() if row[1] not in ('geometry', 'geography', 'hierarchyid')]
    conn.close()
    return supported

def safe_select_star(sql):
    # Replace SELECT * with supported columns if needed
    match = re.match(r"SELECT\s+\*\s+FROM\s+([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)", sql.strip(), re.IGNORECASE)
    if match:
        schema, table = match.group(1), match.group(2)
        cols = get_supported_columns(schema, table)
        if cols:
            return f"SELECT {', '.join(cols)} FROM {schema}.{table};"
    return sql

def run_query(query):
    conn = pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=9M7LKJ2\SQLEXPRESS;'
        r'DATABASE=AdventureWorks2022;'
        r'UID=sa;'
        r'PWD=Sahana@123;'
    )
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return columns, rows, None
        else:
            conn.commit()
            return [], [], "Query executed successfully (no results to display)."
    except Exception as e:
        return [], [], str(e)
    finally:
        conn.close()

OPENAI_API_KEY = "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"  # Replace with your key

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_null_count_sql(table_schema, table_name):
    # Connect to DB and get column names
    conn = pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=9M7LKJ2\SQLEXPRESS;'
        r'DATABASE=AdventureWorks2022;'
        r'UID=sa;'
        r'PWD=Sahana@123;'
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
    """, (table_schema, table_name))
    columns = [row[0] for row in cursor.fetchall()]
    conn.close()
    null_checks = [
        f"SUM(CASE WHEN [{col}] IS NULL THEN 1 ELSE 0 END) AS [{col}_Nulls]"
        for col in columns
    ]
    sql = f"SELECT {', '.join(null_checks)} FROM [{table_schema}].[{table_name}];"
    return sql

def question_to_sql(question):
    # Detect if the question is about null values in a table
    match = re.search(r"null values.*in\s+([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)", question, re.IGNORECASE)
    if match:
        schema, table = match.group(1), match.group(2)
        return get_null_count_sql(schema, table)
    # Otherwise, use LLM as before
    schema_hint = """
Tables in AdventureWorks2022:
- Person.Address (columns: AddressID, AddressLine1, AddressLine2, City, StateProvinceID, PostalCode, rowguid, ModifiedDate)
- Person.Person (columns: BusinessEntityID, PersonType, NameStyle, Title, FirstName, MiddleName, LastName, Suffix, EmailPromotion, AdditionalContactInfo, Demographics, rowguid, ModifiedDate)
- Sales.Customer (columns: CustomerID, PersonID, StoreID, TerritoryID, AccountNumber, rowguid, ModifiedDate)
"""
    prompt = f"""{schema_hint}
You are an assistant that converts English questions to SQL for the AdventureWorks2022 SQL Server database.
Question: "{question}"
Write a complete SQL Server query that answers the question. Only output the SQL code, nothing else.
SQL:"""
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=400,
        temperature=0,
        stop=[";"]
    )
    sql = response.choices[0].text.strip()
    if not sql.endswith(";"):
        sql += ";"
    return sql

def explain_result(question, sql, result):
    prompt = f"""You are a helpful assistant. The user asked: "{question}"
The SQL generated was: {sql}
The result of the query was: {result}
Explain the result in simple English."""
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=150,
        temperature=0,
        stop=["\n"]
    )
    return response.choices[0].text.strip()

def extract_expected_columns(question):
    # Looks for patterns like: Show X, Y, Z from ...
    match = re.search(r"show\s+([a-zA-Z0-9_,\s]+)\s+from", question, re.IGNORECASE)
    if match:
        cols = [c.strip() for c in match.group(1).split(",")]
        return [c for c in cols if c]
    return []

def validate_format(expected_cols, actual_cols):
    # Returns error message if format doesn't match, else None
    if not expected_cols:
        return None
    missing = [col for col in expected_cols if col not in actual_cols]
    if missing:
        return f"Format error: Missing columns in result: {', '.join(missing)}"
    return None

def get_column_types(table_schema, table_name):
    conn = pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=9M7LKJ2\SQLEXPRESS;'
        r'DATABASE=AdventureWorks2022;'
        r'UID=sa;'
        r'PWD=Sahana@123;'
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
    """, (table_schema, table_name))
    types = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return types

def extract_date_column_check(question):
    # Looks for: any date column format ... of schema.table
    match = re.search(r"date\s*column.*of\s+([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)", question, re.IGNORECASE)
    if match:
        return match.group(1), match.group(2)
    return None, None

@app.route("/", methods=["GET", "POST"])
def index():
    columns, rows, error, sql, explanation, success = [], [], None, "", "", None
    query = ""
    format_error = None
    if request.method == "POST":
        query = request.form["query"]

        # Detect if input is a SQL query (starts with SELECT, UPDATE, INSERT, DELETE)
        sql_match = re.match(r"^\s*(select|update|insert|delete)\b", query.strip(), re.IGNORECASE)
        if sql_match:
            # User entered a SQL query, validate and run it
            sql = safe_select_star(query.strip())
            try:
                conn = pyodbc.connect(
                    r'DRIVER={ODBC Driver 17 for SQL Server};'
                    r'SERVER=9M7LKJ2\SQLEXPRESS;'
                    r'DATABASE=AdventureWorks2022;'
                    r'UID=sa;'
                    r'PWD=Sahana@123;'
                )
                conn.autocommit = False
                cursor = conn.cursor()
                cursor.execute("BEGIN TRANSACTION")
                cursor.execute(sql)
                cursor.execute("ROLLBACK TRANSACTION")
                success = "Yes, the query is correct."
                # Actually run and show results
                columns, rows, error = run_query(sql)
            except Exception as e:
                error = f"No, the query is not correct: {str(e)}"
            finally:
                conn.close()
        else:
            # Treat as natural language, generate SQL, then run it
            sql = question_to_sql(query)
            sql = safe_select_star(sql)
            if sql.strip().upper() == "SELECT" or len(sql.strip()) < 20:
                error = "The generated SQL was incomplete. Please rephrase your question or try again."
                columns, rows = [], []
            else:
                columns, rows, error = run_query(sql)
                expected_cols = extract_expected_columns(query)
                format_error = validate_format(expected_cols, columns)
                if format_error:
                    error = (error or "") + " " + format_error
                if error:
                    explanation = explain_result(query, sql, error)
                else:
                    if rows:
                        result_str = str(rows[:5])
                        explanation = explain_result(query, sql, result_str)
                    else:
                        explanation = explain_result(query, sql, error)
    return render_template_string(
        HTML,
        columns=columns, rows=rows, error=error, success=success, query=query, sql=sql, explanation=explanation
    )

if __name__ == "__main__":
    app.run(debug=True)




