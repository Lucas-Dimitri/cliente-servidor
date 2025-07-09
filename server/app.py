from flask import Flask, request
import socket
import time
import csv
from datetime import datetime

app = Flask(__name__)

# CSV header setup
CSV_HEADER = ["timestamp", "client_ip", "response_time", "server_hostname"]
CSV_PATH = "/data/requests.csv"


def init_logging():
    """Initialize CSV file with header if it doesn't exist"""
    try:
        with open(CSV_PATH, "x", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
    except FileExistsError:
        pass


def log_request(client_ip, response_time):
    """Log request details to CSV"""
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                datetime.now().isoformat(),
                client_ip,
                f"{response_time:.6f}",  # Microsecond precision
                socket.gethostname(),
            ]
        )


@app.route("/")
def hello():
    """Handle root endpoint"""
    start_time = time.perf_counter()  # More precise timing

    # Optional processing simulation (adjust as needed)
    time.sleep(0.001)  # 1ms delay

    response_time = time.perf_counter() - start_time
    log_request(request.remote_addr, response_time)

    return f"Resposta do servidor {socket.gethostname()}"


# Initialize logging when app starts
init_logging()

if __name__ == "__main__":
    # This will only run when using Flask dev server (not with Gunicorn)
    app.run(host="0.0.0.0", port=5000)
