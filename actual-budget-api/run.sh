#!/usr/bin/with-contenv bashio

# Get configuration
API_PORT=$(bashio::config 'api_port')
LOG_LEVEL=$(bashio::config 'log_level')

bashio::log.info "Starting Actual Budget REST API..."
bashio::log.info "API Port: ${API_PORT}"
bashio::log.info "Log Level: ${LOG_LEVEL}"

# Start the REST API server
cd /app
exec python3 -m uvicorn rest_api:app \
    --host 0.0.0.0 \
    --port "${API_PORT}" \
    --log-level "${LOG_LEVEL}"
