# Use the official Python image as the base
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies and build Tailwind CSS
RUN npm install \
    && npx tailwindcss -i ./static/src/styles.css -o ./static/css/output.css --minify

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]