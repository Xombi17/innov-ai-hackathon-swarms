# Use python 3.10 slim image for smaller size
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run_api.py

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a user to run the application (security best practice)
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Expose the port the app runs on (7860 is default for Hugging Face Spaces)
EXPOSE 7860

# Command to run the application
# We map 7860 to the PORT env var for the app
CMD ["python", "run_api.py"]
