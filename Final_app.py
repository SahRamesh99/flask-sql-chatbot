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
        'Adverse Event Report', 'Formulation Version'
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

def generate_synthetic_entry(drug=None):
    drug = drug or random.choice(['Paracetamol', 'Ibuprofen', 'Aspirin', 'Azithromycin', 'Benadryl', 'Celexa'])
    side_effect = random.choice(['Nausea', 'Dizziness', 'Headache', 'Fatigue','Shortness of Breath',
                                 'Blurred Vision','Stomach Pain','Liver Damage','Allergic Reaction',
                                 'Increased Heart Rate'])

    feedback_templates = [
        f"{drug} provided relief, but mild {side_effect.lower()} occurred.",
        f"Patient showed improvement using {drug}, with minimal {side_effect}.",
        f"{side_effect} noted during the second dose of {drug}."
    ]
    doctor_feedback_templates = [
        f"Consider monitoring {side_effect.lower()} if prescribing {drug}.",
        f"{drug} is generally well-tolerated, but can lead to {side_effect.lower()}.",
        f"Recommend alternate if {side_effect.lower()} persists."
    ]
    description_templates = [
        f"{drug} is an effective medication for treating common symptoms.",
        f"{drug} helps with inflammation but may cause {side_effect.lower()}.",
        f"This formulation of {drug} is fast-acting and convenient."
    ]
    formulation_version = random.choice([
    "v1 - baseline",
    "v2 - reduced PEG",
    "v3 - no lactose",
    "v4 - added antiemetic"
    ])

    return [
        datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y'),
        drug,
        random.randint(18, 90),
        random.choice(['Male', 'Female', 'Other']),
        side_effect,
        random.choice(['Low', 'Moderate', 'High']),
        random.choice(feedback_templates),
        random.choice(['Once daily', 'Twice daily', 'Weekly', 'Thrice daily']),
        random.choice(doctor_feedback_templates),
        random.choice(description_templates),
        random.choice(['Tablet', 'Syrup', 'Injection']),
        random.choice(['Critical Issues','No Issues','Moderate Concern']),
        formulation_version
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

@app.route('/formulation_recommendations')
def formulation_recommendations():
    selected_drug = request.args.get('drug')
    try:
        form_sheet = sheet.worksheet('forms')
        records = form_sheet.get_all_records()
        df = pd.DataFrame(records)

        df['Drug Name'] = df['Drug Name'].str.strip()
        df['Dosage Forms'] = df['Dosage Forms'].str.lower().str.strip()
        df['Reported Side Effects'] = df['Reported Side Effects'].str.lower().str.strip()

        drug_names = sorted(df['Drug Name'].dropna().unique())

        if selected_drug:
            df = df[df['Drug Name'] == selected_drug]

        df = df[(df['Dosage Forms'].notna()) & (df['Reported Side Effects'].notna())]
    
        unique_combinations = df[['Drug Name', 'Reported Side Effects', 'Dosage Forms']].drop_duplicates()

        recommendations = []

        for _, row in unique_combinations.iterrows():
            drug = row['Drug Name'].title()
            side_effect = row['Reported Side Effects'].title()
            dosage_form = row['Dosage Forms'].title()
            efficacy = row.get('Efficacy Rating', 'Unknown')
            suggestion = get_mistral_suggestion(drug, side_effect, dosage_form,efficacy)
            recommendations.append({
                'drug': drug,
                'side_effect': side_effect,
                'dosage_form': dosage_form,
                'suggestion': suggestion if suggestion else "No suggestion available"
            })

        top_side_effects = df['Reported Side Effects'].value_counts().head(10)
        viz_data = {
            'side_effect_counts': {k: int(v) for k, v in top_side_effects.to_dict().items()},
            'dosage_form_counts': {k: int(v) for k, v in df['Dosage Forms'].value_counts().to_dict().items()}
        }

        return render_template('formulation_recommendations.html', recommendations=recommendations, viz_data=viz_data,
                               drug_names=drug_names,selected_drug=selected_drug)

    except Exception as e:
        app.logger.error(f"Error in formulation_recommendations: {str(e)}")
        flash("Error generating recommendations. Please try again later.", "error")
        return redirect(url_for('user_dashboard'))

recommendation_cache = {}

def get_cached_recommendation(key):
    cached = recommendation_cache.get(key)
    if cached and (time.time() - cached['timestamp']) < 86400:
        return cached
    return None

def cache_recommendation(key, recommendation):
    recommendation_cache[key] = recommendation

#def get_mistral_suggestion(side_effect, dosage_form):
def get_mistral_suggestion(drug, side_effect, dosage_form,efficacy='Unknown'):
    api_key = "55214e4596a5fbf44bfa9bddb99c001cefd864172e09d3ff09a602a8292c9c92"  # Replace with your actual API key
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Sample prompt logic (inactive)
    prompt = f"""As a pharmaceutical formulator, suggest 3 modifications for {drug} {dosage_form} 
    to address reported {side_effect}. Consider:
    1. Excipient substitutions
    2. Dosage form optimizations
    3. Additive ingredientss
    Provide scientifically valid options with brief rationale and as short and accurate as possible.
    """

    data = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500
    }

    try:
        response = requests.post("https://api.together.xyz/v1/chat/completions", 
                               headers=headers, 
                               json=data,
                               timeout=30)
        response.raise_for_status()
        response_json = response.json()
        if 'choices' not in response_json:
            print("Unexpected API response:", response_json)
            return "Could not generate suggestion: No 'choices' in response"
        
        return response_json["choices"][0]["message"]["content"]
        
    except requests.exceptions.RequestException as e:
        print("Request error:", e)
        return f"Could not generate suggestion: {str(e)}"
    
    except Exception as e:
        return f"Could not generate suggestion: {str(e)}"

def create_visualization_data(df, recommendations):
    return {
        'side_effect_counts': df['Reported Side Effects'].value_counts().to_dict(),
        'dosage_form_counts': df['Dosage Forms'].value_counts().to_dict(),
        'recommendation_counts': len(recommendations)
    }

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role'].lower()
        username = request.form['username']
        password = request.form['password']

        try:
            worksheet = sheet.worksheet(role)
            records = worksheet.get_all_records()
        except Exception as e:
            flash("Error accessing the sheet: " + str(e))
            return render_template('login.html')

        for record in records:
            if record['username'] == username and record['password'] == password:
                if role == 'doctor':
                    return redirect(url_for('doctor_dashboard', user=username))
                elif role == 'user':
                    return redirect(url_for('user_dashboard', user=username))

        flash("Invalid credentials. Please try again.")
        return render_template('login.html')

    return render_template('login.html')

@app.route('/user_dashboard')
def user_dashboard():
    user = request.args.get('user', 'User')
    selected_drug = request.args.get('drug')

    try:
        form_sheet = sheet.worksheet('forms')
        records = form_sheet.get_all_records()
        df = pd.DataFrame(records)

        drug_names = sorted(df['Drug Name'].dropna().unique())

        if selected_drug:
            df = df[df['Drug Name'] == selected_drug]

        df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
        efficacy_order = ['Low', 'Moderate', 'High']
        df['Efficacy Rating'] = pd.Categorical(df['Efficacy Rating'], categories=efficacy_order, ordered=True)

        charts = {}

        side_effects_gender = df.groupby(['Reported Side Effects', 'Gender']).size().reset_index(name='count')

        side_effects_gender_sorted = side_effects_gender.sort_values(by='count', ascending=False)   

        fig1 = px.histogram(side_effects_gender_sorted, 
                      x="Reported Side Effects", 
                      y="count", 
                      color="Gender", 
                      title="Most Common Side Effects Categorized by Gender",
                      labels={"Reported Side Effects": "Side Effect", "count": "Frequency"},
                      color_discrete_sequence=['#0457ac', '#308fac','#37bd79'])
        # Save chart as JSON for passing to the template
        fig1.update_layout(transition=dict(duration=700, easing='cubic-in-out'))
        charts['gender_side_effects'] = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)

        fig2 = px.box(df, x="Efficacy Rating", y="Age", title="Age vs. Efficacy Rating Distribution")
        fig2.update_layout(transition=dict(duration=700, easing='cubic-in-out'))
        charts['age_efficacy'] = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

        fig3 = px.histogram(df, x="Reported Side Effects", color="Efficacy Rating", title="Side Effects by Efficacy Rating")
        fig3.update_layout(transition=dict(duration=700, easing='cubic-in-out'))
        charts['efficacy_side_effects'] = json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)

        fig4 = px.bar(df, x="Dosage Forms", color="Prescription Frequency", title="Dosage Forms by Prescription Frequency")
        fig4.update_layout(transition=dict(duration=700, easing='cubic-in-out'))
        charts['dosage_frequency'] = json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder)

        fig5 = px.strip(df, x="Efficacy Rating", y="Age", color="Gender", title="Age Distribution by Efficacy Rating and Gender")
        fig5.update_layout(transition=dict(duration=700, easing='cubic-in-out'))
        charts['age_rating_scatter'] = json.dumps(fig5, cls=plotly.utils.PlotlyJSONEncoder)

        feedback_text = ' '.join(df['Feedback'].dropna().astype(str).tolist() + df['Adverse Event Report'].dropna().astype(str).tolist())
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(feedback_text)
        img = BytesIO()
        wordcloud.to_image().save(img, format='PNG')
        img.seek(0)
        wordcloud_base64 = base64.b64encode(img.read()).decode('utf-8')

        # Prepare Data
        df['Drug Name'] = df['Drug Name'].str.strip()
        df['Dosage Forms'] = df['Dosage Forms'].str.lower().str.strip()
        df['Reported Side Effects'] = df['Reported Side Effects'].str.lower().str.strip()

        if selected_drug:
            df = df[df['Drug Name'] == selected_drug]

        df = df[(df['Dosage Forms'].notna()) & (df['Reported Side Effects'].notna())]
        unique_combinations = df[['Drug Name', 'Reported Side Effects', 'Dosage Forms']].drop_duplicates()

        recommendations = []
        for _, row in unique_combinations.iterrows():
            drug = row['Drug Name'].title()
            side_effect = row['Reported Side Effects'].title()
            dosage_form = row['Dosage Forms'].title()
            efficacy = row.get('Efficacy Rating', 'Unknown')
            suggestion = get_mistral_suggestion(drug, side_effect, dosage_form, efficacy)
            recommendations.append({
                'drug': drug,
                'side_effect': side_effect,
                'dosage_form': dosage_form,
                'suggestion': suggestion if suggestion else "No suggestion available"
            })

        viz_recommendations = pd.DataFrame(recommendations)

        if not viz_recommendations.empty:
            viz_recommendations['count'] = 1
            grouped = viz_recommendations.groupby(['side_effect', 'dosage_form', 'suggestion'], as_index=False)['count'].sum()
            grouped = grouped.sort_values(by='count', ascending=False)

            fig_recommend = px.sunburst(
                grouped,
                path=['side_effect', 'dosage_form'],
                #x='side_effect',
                #y='count',
                values='count',
                color='dosage_form',
                hover_data=['suggestion'],
                title="Dosage-Related Complaints with Linked Recommendations",
                labels={"count": "Reported Cases", "side_effect": "Side Effect"},
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_recommend.update_layout(
                transition=dict(duration=700, easing='cubic-in-out'),
                xaxis_tickangle=-45,
                barmode='group',
                hoverlabel=dict(bgcolor="white", font_size=12)
            )
            #fig_recommend.update_traces(
                #customdata=grouped[['suggestion']],
                #hovertemplate="<b>%{label}</b><br>Parent: %{parent}<br>Count: %{value}<br>Suggestion: %{customdata[0]}"
            #)

            # Ensure customdata is a list of lists (each inner list contains 1 string)
            # Convert the suggestions to a list of lists for proper use with customdata
            customdata = [[s] for s in grouped['suggestion'].tolist()]

            fig_recommend.update_traces(
            customdata=customdata,
            hovertemplate="<b>%{label}</b><br>Parent: %{parent}<br>Count: %{value}<br>Suggestion: %{customdata[0]}",
            )


            dosage_chart_json = json.dumps(fig_recommend, cls=plotly.utils.PlotlyJSONEncoder)
        else:
            dosage_chart_json = None
        
        version_efficacy = df.groupby(['Formulation Version', 'Efficacy Rating']).size().reset_index(name='count')

        fig_ver = px.bar(
                  version_efficacy,
                  x='Formulation Version',
                  y='count',
                  color='Efficacy Rating',
                  title='Efficacy by Formulation Version',
                  barmode='group')

        charts['version_efficacy'] = json.dumps(fig_ver, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('user_dashboard.html', charts=charts, wordcloud=wordcloud_base64, user=user,
                               drug_names=drug_names,selected_drug=selected_drug,dosage_chart=dosage_chart_json)

    except Exception as e:
        return f"Error generating visualizations: {e}"

@app.route('/doctor_dashboard')
def doctor_dashboard():
    user = request.args.get('user', 'Doctor')

    try:
        form_sheet = sheet.worksheet('forms')
        records = form_sheet.get_all_records()
        df = pd.DataFrame(records)
        drug_names = sorted(df['Drug Name'].dropna().unique())
    except Exception as e:
        drug_names = []
        flash(f"Error loading drug names: {str(e)}")

    return render_template('doctor_dashboard.html', user=user,drug_names=drug_names)

@app.route('/submit_form', methods=['POST'])
def submit_form():
    try:
        ist = pytz.timezone('Asia/Kolkata')
        current_date_ist = datetime.now(ist).strftime('%d-%m-%Y')
        data = [current_date_ist] + [request.form.get(field) for field in [
            'Drug Name', 'Age', 'Gender', 'Reported Side Effects',
            'Efficacy Rating', 'Feedback', 'Prescription Frequency',
            'Doctor Feedback', 'Drug Description', 'Dosage Forms',
            'Adverse Event Report','Formulation Version']]

        form_sheet = sheet.worksheet('forms')
        form_sheet.append_row(data)

        flash("Form submitted successfully with timestamp!")
    except Exception as e:
        flash(f"Error submitting form: {str(e)}")

    return render_template('doctor_dashboard.html', user=request.args.get('user', 'Doctor'))

@app.route('/logout')
def logout():
    flash("You have been logged out.")
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
