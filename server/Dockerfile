FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Gunicorn (production WSGI server)
RUN pip install gunicorn==20.1.0

# Create data directory for logs
RUN mkdir -p /data

COPY app.py .

# Run Gunicorn with 4 worker processes
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "app:app"]
