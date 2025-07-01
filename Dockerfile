# Use an official lightweight Python image
FROM python:3.11-slim

# Install system packages for build dependencies (Rust, ODBC, FAISS, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    build-essential \
    rustc \
    cargo \
    unixodbc-dev \
    curl \
    gnupg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy your files into the container
COPY . .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the default port
EXPOSE 5000

# Set environment variable so Flask runs on the correct host/port
ENV PORT=5000

# Run your app (adjust filename if not app.py)
CMD ["python", "SQL_Chatbot_Flask 1.py"]
