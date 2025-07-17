# Use an official Python runtime as a parent image
# python:3.9-slim is based on Debian, which is great.
FROM python:3.9-slim

# Set an environment variable to prevent interactive installation prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory in the container
WORKDIR /app

# --- Install System Dependencies ---
# 1. Update package lists and install only the required tesseract runtime.
# 2. Combine all apt commands into a single RUN layer for better caching and smaller image size.
# 3. Clean up apt cache to keep the final image slim.
RUN apt-get update -y && \
    apt-get install -y tesseract-ocr && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# --- Install Python Dependencies ---
# Copy the requirements file and install dependencies
COPY ./requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

# --- Copy Application Code ---
# Copy the rest of the application code
COPY ./app /app/app
COPY ./config /app/config

# Expose the port the app runs on
EXPOSE 8000

# --- Run the Application ---
# The host 0.0.0.0 makes it accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]