# FROM python:3.11-slim

# WORKDIR /app

# # Install system dependencies for transformers & torch (minimal)
# RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt .

# RUN pip install --no-cache-dir -r requirements.txt

# COPY main.py .

# ENV PYTHONUNBUFFERED=1

# EXPOSE 8080

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y git

# Create app directory
WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
