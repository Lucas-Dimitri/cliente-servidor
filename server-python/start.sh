#!/bin/bash
# Trap SIGTERM and other signals to ensure clean shutdown
trap 'echo "Caught signal, shutting down..."; pkill -f python; sleep 2; exit 0' TERM INT QUIT

# Start the custom protocol server directly
python app.py &
SERVER_PID=$!

# Wait for server to exit
wait $SERVER_PID
