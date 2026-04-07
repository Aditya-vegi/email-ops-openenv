# Use a highly cached, stable version to avoid registry timeouts
FROM python:3.10-slim

# Prevent Python from generating .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install basic system tools in case your app needs them for git/io
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies separately to utilize layer caching
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy your source code
COPY . .

# Set the command to run your agent
# Ensure 'app.py' is your actual entry point!
CMD ["python", "app.py"]