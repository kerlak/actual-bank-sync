# Use Python Alpine directly (no s6-overlay)
FROM python:3.12-alpine

# Install bash, jq and Python dependencies
RUN apk add --no-cache bash jq \
    && pip install --no-cache-dir \
        fastapi \
        uvicorn \
        actualpy \
        pydantic

WORKDIR /app

# Copy application files
COPY rest_api.py .
COPY run.sh .

# Make run script executable
RUN chmod +x run.sh

# Environment variables
ENV PYTHONUNBUFFERED=1

EXPOSE 2078

# Start application
CMD ["./run.sh"]
