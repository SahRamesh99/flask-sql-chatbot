from flask import Flask, render_template, request, redirect, url_for, flash
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import plotly
import plotly.express as px
import plotly.graph_objs as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import pandas as pd
import time
import requests
from datetime import datetime
import pytz
from faker import Faker
import random

app = Flask(__name__,template_folder=r'C:/Users/Sahanar/Downloads/PMS 1/PMS/templates')
app.secret_key = 'your_secret_key'  # Replace with something secure

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\Users\Sahanar\Downloads\PMS 1\PMS\pms credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Doctor Information")  # <--- Using your file name here

def setup_forms_sheet():
    headers = [
        'Date (IST)',  # Make it clear this is in IST
        'Drug Name', 'Age', 'Gender', 'Reported Side Effects',
        'Efficacy Rating', 'Feedback', 'Prescription Frequency',
        'Doctor Feedback', 'Drug Description', 'Dosage Forms',
        'Adverse Event Report'
    ]

    try:
        form_sheet = sheet.worksheet('forms')
        existing_headers = form_sheet.row_values(1)
        if existing_headers != headers:
            form_sheet.delete_rows(1)  # Clear any wrong header
            form_sheet.insert_row(headers, 1)
    except gspread.exceptions.WorksheetNotFound:
        form_sheet = sheet.add_worksheet(title="forms", rows="100", cols="20")
        form_sheet.insert_row(headers, 1)

setup_forms_sheet()

fake = Faker()

def generate_synthetic_entry():
    return [
        datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y'),
        random.choice(['Paracetamol', 'Ibuprofen', 'Aspirin']),
        random.randint(18, 90),
        random.choice(['Male', 'Female']),
        random.choice(['Nausea', 'Dizziness', 'Headache', 'Fatigue']),
        random.choice(['Low', 'Moderate', 'High']),
        fake.sentence(),
        random.choice(['Once daily', 'Twice daily', 'Weekly']),
        fake.sentence(),
        fake.text(max_nb_chars=100),
        random.choice(['Tablet', 'Syrup', 'Injection']),
        fake.sentence()
    ]

@app.route('/generate_synthetic_data')
def generate_synthetic_data():
    try:
        form_sheet = sheet.worksheet('forms')
        for _ in range(10):  # Generate 10 synthetic entries
            entry = generate_synthetic_entry()
            form_sheet.append_row(entry)
        flash("Synthetic data generated and added to the sheet.")
    except Exception as e:
        flash(f"Error generating synthetic data: {str(e)}")
        print("Error details:", e)
    return redirect(url_for('doctor_dashboard', user='Doctor'))

@app.route('/check_auth')
def check_auth():
    try:
        sh = client.open("Doctor Information")
        worksheet_titles = [ws.title for ws in sh.worksheets()]
        return f"✅ Authenticated. Worksheets: {worksheet_titles}"
    except Exception as e:
        return f"❌ Auth failed: {str(e)}"

@app.route('/test_gsheet_write')
def test_gsheet_write():
    try:
        sheet_ref = client.open("Doctor Information")
        form_sheet = sheet_ref.worksheet("forms")
        test_row = ["✅ TEST", "SyntheticDrug", 42, "Female", "Headache", "High",
                    "Auto-generated feedback", "Once daily", "No issues noted",
                    "Generated for testing", "Tablet", "No adverse effect"]
        form_sheet.append_row(test_row)
        return "✅ Test row added to 'forms' worksheet."
    except Exception as e:
        return f"❌ Error writing to sheet: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
