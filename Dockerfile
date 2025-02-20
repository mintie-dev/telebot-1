# Use official Python runtime as a base image
FROM python:3.9-slim

# Set working directory in the container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a non-root user for security
RUN useradd -m botuser && \
    chown -R botuser:botuser /app
USER botuser

# Command to run the bot
CMD ["python", "bot.py"] 