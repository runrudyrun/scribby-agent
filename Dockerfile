# Use a Python base image compatible with Raspberry Pi (ARM64)
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy the dependency file first to leverage Docker layer caching
COPY requirements.txt .

# Install system dependencies that might be needed for some Python packages
# (e.g., for numpy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only what's needed for index building to leverage caching
COPY build_index.py .
COPY ./scribby_pi ./scribby_pi
COPY ./data/corpus ./data/corpus

# --- Pre-build the knowledge base index ---
# This step runs only if the corpus or build scripts change.
RUN echo "Pre-building knowledge base index..."
RUN python3 build_index.py
RUN echo "Index build complete."

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
