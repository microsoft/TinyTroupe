# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -e .

# Set environment variables for LiteLLM
ENV LITELLM_URL=""
ENV LITELLM_KEY=""
ENV GROQ_API_KEY=""
ENV GEMINI_API_KEY=""
ENV OPENROUTER_API_KEY=""

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV NAME TinyTroupe

# Run app.py when the container launches
CMD ["python", "./examples/simple_chat.ipynb"]
