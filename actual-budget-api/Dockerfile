# Same base as local build
FROM python:3.11-slim

WORKDIR /app

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY rest_api.py .
COPY run.sh .
COPY pwa/ ./pwa/

# Make run script executable
RUN chmod +x run.sh

# Environment variables
ENV PYTHONUNBUFFERED=1

EXPOSE 2078

# Start application
CMD ["./run.sh"]
