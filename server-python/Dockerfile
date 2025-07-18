FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Gunicorn (production WSGI server) and filelock for better file locking
RUN pip install gunicorn==20.1.0 filelock==3.12.0

# Create data directory for logs and ensure proper permissions
RUN mkdir -p /data && chmod 777 /data

COPY app.py .
COPY start.sh .

RUN chmod +x /app/start.sh

# Run the startup script which manages clean shutdown
CMD ["/app/start.sh"]
