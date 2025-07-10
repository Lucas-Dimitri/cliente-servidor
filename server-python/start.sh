#!/bin/bash
# Trap SIGTERM and other signals to ensure clean shutdown
trap 'echo "Caught signal, shutting down..."; pkill -f gunicorn; sleep 2; exit 0' TERM INT QUIT

# Start Gunicorn in the background
gunicorn --bind 0.0.0.0:5000 --workers 6 --threads 2 app:app &
GUNICORN_PID=$!

# Wait for Gunicorn to exit
wait $GUNICORN_PID
