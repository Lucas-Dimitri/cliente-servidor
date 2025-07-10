FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Gunicorn (production WSGI server) and filelock for better file locking
RUN pip install gunicorn==20.1.0 filelock==3.12.0

# Create data directory for logs and ensure proper permissions
RUN mkdir -p /data && chmod 777 /data

COPY app.py .

# Add a helper script to ensure clean shutdown
COPY <<EOF /app/start.sh
#!/bin/bash
# Trap SIGTERM and other signals to ensure clean shutdown
trap 'echo "Caught signal, shutting down..."; pkill -f gunicorn; sleep 2; exit 0' TERM INT

# Start Gunicorn in the background
gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 app:app &

# Wait for signals
wait
EOF

RUN chmod +x /app/start.sh

# Run the startup script which manages clean shutdown
CMD ["/app/start.sh"]
