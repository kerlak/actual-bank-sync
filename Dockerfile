# USAMOS LA IMAGEN OFICIAL
FROM mcr.microsoft.com/playwright/python:v1.56.0-jammy

# 1. Instalamos Xvfb
RUN apt-get update && apt-get install -y \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# 2. INSTALAMOS LIBRERÍAS (FORZAMOS LA INSTALACIÓN AQUÍ)
# Añadimos playwright y stealth explícitamente para asegurar que Python las ve
RUN pip install --no-cache-dir \
    pywebio \
    playwright==1.56.0 \
    playwright-stealth==2.0.0

WORKDIR /app

# 3. Copiamos archivos
COPY app.py .
COPY run.sh .

# 4. Permisos de ejecución
RUN chmod +x run.sh

# Variables
ENV PYTHONUNBUFFERED=1
ENV TERM=xterm-256color

EXPOSE 2077

# 5. Arrancamos con tu script manual
CMD ["./run.sh"]
