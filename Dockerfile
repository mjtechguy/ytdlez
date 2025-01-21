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

# Install Node.js (version 16.x) and npm
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs

# Copy application files
COPY . .

# Create package.json and install Node.js dependencies
RUN npm init -y \
    && npm install tailwindcss postcss autoprefixer \
    && npx tailwindcss init

# Build Tailwind CSS
RUN npx tailwindcss -i ./static/src/styles.css -o ./static/css/output.css --minify

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]