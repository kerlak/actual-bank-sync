# Base image: Official Playwright Python image
FROM mcr.microsoft.com/playwright/python:v1.56.0-jammy

# Install Xvfb for virtual display
RUN apt-get update && apt-get install -y \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (playwright and stealth explicitly for visibility)
RUN pip install --no-cache-dir \
    pywebio \
    playwright==1.56.0 \
    playwright-stealth==2.0.0

WORKDIR /app

# Copy application files
COPY webui.py .
COPY actual_sync.py .
COPY banks/ banks/
COPY run.sh .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Set execution permissions
RUN chmod +x run.sh

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV TERM=xterm-256color

EXPOSE 2077

# Start application via run script
CMD ["./run.sh"]
