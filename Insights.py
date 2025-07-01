from flask import Flask, render_template, request, send_file
import pandas as pd
import matplotlib.pyplot as plt
import openai
import os

app = Flask(__name__,template_folder=r"C:\Users\Sahanar\Desktop\VScode")
openai.api_key = "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"
BASE_URL = "https://api.openai.com/v1"
EMBEDDING_MODEL = "text-embedding-3-small"  # Replace this

# Load your data
#df = pd.read_excel(r"C:\Users\Sahanar\Downloads\Sales and Expense data.xlsx")

# Ensure 'static' directory exists
if not os.path.exists("static"):
    os.makedirs("static")

@app.route("/", methods=["GET", "POST"])
def index():
    code_output = ""
    error_msg = ""
    plot_generated = False
    df = None

    if request.method == "POST":
        # Handle file upload
        file = request.files.get("datafile")
        if file and file.filename:
            try:
                if file.filename.endswith(".csv"):
                    df = pd.read_csv(file)
                elif file.filename.endswith(".xlsx"):
                    df = pd.read_excel(file)
                else:
                    error_msg = "Unsupported file type. Please upload a CSV or Excel file."
            except Exception as e:
                error_msg = f"Error reading file: {str(e)}"
        else:
            # Fallback to default file if no upload
            df = pd.read_excel(r"C:\Users\Sahanar\Downloads\Sales and Expense data.xlsx")

        user_input = request.form.get("user_input", "")

        if df is not None and not error_msg:
            prompt = f"""
You are a Python assistant. The user gave this request: "{user_input}".
The DataFrame `df` has these columns: {list(df.columns)}.
Generate matplotlib code to visualize this DataFrame. Do NOT import libraries.
Assume `df` is already loaded. Only return Python code that plots the graph.
"""
            try:
                client = openai.OpenAI(api_key=openai.api_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )

                code = response.choices[0].message.content

                # Remove markdown code fences if present
                if code.startswith("```"):
                    code = code.split("```")[1]
                    if code.startswith("python"):
                        code = code[len("python"):].lstrip()
                    code = code.strip("`").strip()

                code_output = code

                # Remove plt.show() to avoid GUI errors in web apps
                code = code.replace("plt.show()", "")

                # Ensure 'static' directory exists
                if not os.path.exists("static"):
                    os.makedirs("static")

                # Save figure
                local_vars = {"df": df, "plt": plt}
                exec(code, {}, local_vars)
                plt.savefig("static/plot.png", bbox_inches='tight')
                plt.clf()
                plot_generated = True

            except Exception as e:
                error_msg = f"Error: {str(e)}"

    return render_template("Visual.html",
                           code_output=code_output,
                           plot_generated=plot_generated,
                           error_msg=error_msg)

if __name__ == "__main__":
    app.run(debug=True)
