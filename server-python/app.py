from flask import Flask, request, jsonify
import os
import csv
import socket
import time
import fcntl  # Add file locking support
import tempfile
import shutil
from filelock import FileLock  # More robust file locking
import atexit
from datetime import datetime

app = Flask(__name__)

# CSV header setup - matching the expected format for analysis
CSV_HEADER = [
    "client_id",
    "message_id",
    "server_id",
    "client_send_time",
    "server_processing_time",
    "client_receive_time",
    "response_time",
    "num_servers",
    "num_clients",
    "num_messages",
]
CSV_PATH = "/data/requests.csv"

# Use timestamp suffix to avoid conflicts between test runs
timestamp_suffix = os.getenv("TIMESTAMP_SUFFIX", "")
if timestamp_suffix:
    CSV_PATH = f"/data/requests{timestamp_suffix}.csv"


def init_logging():
    """Initialize CSV file with header if it doesn't exist"""
    try:
        # Make sure the directory exists
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

        # Use FileLock for cross-process locking
        with file_lock:
            # Create file with header if it doesn't exist or is empty
            if not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) == 0:
                with open(CSV_PATH, "w", newline="") as f:
                    # Also get exclusive lock while creating file
                    fcntl.flock(f, fcntl.LOCK_EX)
                    try:
                        writer = csv.writer(f)
                        writer.writerow(CSV_HEADER)
                        f.flush()
                        os.fsync(f.fileno())
                    finally:
                        fcntl.flock(f, fcntl.LOCK_UN)
            else:
                # Validate header if file exists
                try:
                    with open(CSV_PATH, "r", newline="") as f:
                        reader = csv.reader(f)
                        header = next(reader, None)
                        if header != CSV_HEADER:
                            print(
                                f"Warning: CSV header mismatch in {CSV_PATH}. Expected: {CSV_HEADER}, Found: {header}"
                            )
                            # File exists but has incorrect header, backup and recreate
                            backup_path = f"{CSV_PATH}.bak"
                            shutil.copy2(CSV_PATH, backup_path)
                            print(f"Backed up existing file to {backup_path}")

                            # Recreate with proper header
                            with open(CSV_PATH, "w", newline="") as f:
                                fcntl.flock(f, fcntl.LOCK_EX)
                                try:
                                    writer = csv.writer(f)
                                    writer.writerow(CSV_HEADER)
                                    f.flush()
                                    os.fsync(f.fileno())
                                finally:
                                    fcntl.flock(f, fcntl.LOCK_UN)
                except Exception as e:
                    print(f"Error validating CSV header: {e}")
    except Exception as e:
        print(f"Error initializing log file: {e}")


# Setup lock file path
LOCK_FILE = "/data/requests.lock"

# Create a singleton lock object
file_lock = FileLock(LOCK_FILE)


# Register cleanup function
def cleanup():
    """Clean up resources when application exits"""
    if os.path.exists(LOCK_FILE):
        try:
            os.unlink(LOCK_FILE)
        except Exception:
            pass


atexit.register(cleanup)


def log_request(
    client_id,
    message_id,
    client_send_time,
    server_processing_time,
    num_servers,
    num_clients,
    num_messages,
):
    """Log request details to CSV in the expected format with robust file locking"""
    # Get values from environment if marked as unknown
    if num_servers == "unknown":
        num_servers = os.getenv("NUM_SERVERS", "unknown")
    if num_clients == "unknown":
        num_clients = os.getenv("NUM_CLIENTES", "unknown")
    if num_messages == "unknown":
        num_messages = os.getenv("NUM_MENSAGENS", "unknown")

    # Calculate response times
    client_receive_time = time.time()
    try:
        response_time = client_receive_time - float(client_send_time)
    except (ValueError, TypeError):
        print(
            f"Error calculating response time, invalid client_send_time: {client_send_time}"
        )
        response_time = 0.0
        client_send_time = time.time()  # Use current time as fallback

    # Prepare row data - ensure all fields are present and valid
    row_data = [
        str(client_id),
        str(message_id),
        socket.gethostname(),
        str(client_send_time),
        f"{server_processing_time:.6f}",
        str(client_receive_time),
        f"{response_time:.6f}",
        str(num_servers),
        str(num_clients),
        str(num_messages),
    ]

    # Validate row data has exactly 10 fields
    if len(row_data) != 10:
        print(f"ERROR: Invalid row data length: {len(row_data)}, expected 10")
        return

    # Use atomic write pattern with multi-level file locking
    try:
        # First write to a temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", newline="", dir="/data", delete=False
        ) as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow(row_data)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_path = temp_file.name

        # Use FileLock for process-safe locking
        with file_lock:
            # Then also use fcntl for system-level locking (double protection)
            with open(CSV_PATH, "a", newline="") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    # Verify file exists and is a valid CSV before appending
                    if os.path.getsize(CSV_PATH) > 0:
                        # Read the temp file contents
                        with open(temp_path, "r", newline="") as temp_read:
                            content = temp_read.read()

                        # Append to the main CSV file
                        f.write(content)
                        f.flush()
                        os.fsync(f.fileno())
                    else:
                        # If file is empty or corrupted, rewrite it completely
                        print(
                            f"Warning: CSV file {CSV_PATH} is empty or invalid, recreating"
                        )
                        f.seek(0)
                        f.truncate()
                        writer = csv.writer(f)
                        writer.writerow(CSV_HEADER)
                        writer.writerow(row_data)
                        f.flush()
                        os.fsync(f.fileno())
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)

        # Clean up the temp file
        try:
            os.unlink(temp_path)
        except Exception:
            pass
    except Exception as e:
        print(f"Error logging request: {e}")


@app.route("/", methods=["GET", "POST"])
def handle_request():
    """Handle both GET and POST requests"""
    start_time = time.perf_counter()

    # Extract request data
    if request.method == "POST" and request.is_json:
        data = request.get_json()
        client_id = data.get("client_id", "unknown")
        message_id = data.get("message_id", "unknown")
        client_send_time = data.get("client_send_time", time.time())
    else:
        client_id = request.args.get("client_id", "unknown")
        message_id = request.args.get("message_id", "unknown")
        client_send_time = request.args.get("client_send_time", time.time())

    # Obtenha os parâmetros do cenário das variáveis de ambiente
    num_servers = os.getenv("NUM_SERVERS", "unknown")
    num_clients = os.getenv("NUM_CLIENTES", "unknown")
    num_messages = os.getenv("NUM_MENSAGENS", "unknown")

    # Simulate processing work
    time.sleep(0.001)  # 1ms delay

    server_processing_time = time.perf_counter() - start_time

    # Log the request
    log_request(
        client_id,
        message_id,
        client_send_time,
        server_processing_time,
        num_servers,
        num_clients,
        num_messages,
    )

    return f"Resposta do servidor {socket.gethostname()}"


# Initialize logging when app starts
init_logging()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
