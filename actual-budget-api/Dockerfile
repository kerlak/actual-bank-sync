ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    && pip3 install --no-cache-dir --break-system-packages \
        fastapi \
        uvicorn \
        actualpy \
        pydantic

# Copy application files
COPY rest_api.py /app/
COPY run.sh /

# Make run script executable
RUN chmod a+x /run.sh

# Set working directory
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8080/')" || exit 1

CMD [ "/run.sh" ]
