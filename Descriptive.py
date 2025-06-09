import streamlit as st
import numpy as np
import pickle
from transformers import pipeline

# Load inventory prediction model
with open('inventory_model.pkl', 'rb') as file:
    model = pickle.load(file)

# Load conversational model using Hugging Face
#chatbot_pipeline = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.1", tokenizer="mistralai/Mistral-7B-Instruct-v0.1")

# Load an open-access model like GPT-2
chatbot_pipeline = pipeline("text-generation", model="gpt2")

#print("GPT-2 model loaded successfully!")
st.title("Inventory Management Chatbot")

# Sidebar for navigation
option = st.sidebar.selectbox("Choose an action:", ["Predict Inventory", "Chat with AI"])

# Prediction Section
import matplotlib.pyplot as plt
import seaborn as sns

def plot_predictions(days, predicted_stock):
    # Plot the predicted stock
    plt.figure(figsize=(8, 5))
    sns.lineplot(x=days.flatten(), y=predicted_stock, marker='o', color='blue')
    plt.title('Stock Prediction for Future Days')
    plt.xlabel('Days')
    plt.ylabel('Predicted Stock')
    plt.grid(True)
    
    # Save the plot to a file
    plot_path = 'predicted_stock.png'
    plt.savefig(plot_path)
    plt.close()
    return plot_path

import base64

# Function to generate download link for the image
def get_image_download_link(image_path, filename="predicted_stock.png"):
    with open(image_path, "rb") as img_file:
        img_data = img_file.read()
        b64_data = base64.b64encode(img_data).decode()
        href = f'<a href="data:image/png;base64,{b64_data}" download="{filename}">Download Predicted Stock Chart</a>'
        return href
    
if option == "Predict Inventory":
    st.markdown(
    """
    <div style="display: flex; align-items: center;">
        <img src="https://h5p.org/sites/default/files/styles/medium-logo/public/logos/chart-icon-color.png?itok=kpLTYHHJ" width="75" style="margin-right: 10px;">
        <h2>Predict Future Inventory</h2>
    </div>
    """,
    unsafe_allow_html=True
)

    days_input = st.text_input("Enter days (comma-separated, e.g., 30,60,90):")
    
    if st.button("Predict"):
        try:
            # Convert input to array and predict stock
            days = np.array([int(day.strip()) for day in days_input.split(',')]).reshape(-1, 1)
            predicted_stock = model.predict(days)
            st.success(f"Predicted Stock for the next {days_input} days: {predicted_stock}")

            # Plot the prediction and display the image
            plot_path = plot_predictions(days, predicted_stock)
            st.image(plot_path, caption="Predicted Stock Levels", use_container_width=True)

            # Provide download link
            st.markdown(get_image_download_link(plot_path), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {e}")

# Chat Section
elif option == "Chat with AI":
    st.markdown(
    """
    <div style="display: flex; align-items: center;">
        <img src="https://thumbs.dreamstime.com/b/chat-icon-isolated-white-background-79426494.jpg" width="75" style="margin-right: 10px;">
        <h2>Chat with Inventory Chatbot</h2>
    </div>
    """,
    unsafe_allow_html=True
)

    user_input = st.text_area("Ask your question about inventory management:")
    
    if st.button("Send"):
        try:
            response = chatbot_pipeline(user_input, max_length=200, num_return_sequences=1, truncation=True)[0]['generated_text']
            st.write(response)
        except Exception as e:
            st.error(f"Error: {e}")

