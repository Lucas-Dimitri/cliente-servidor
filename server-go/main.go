package main

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"sync"
	"time"
)

var (
	csvLock sync.Mutex
)

type RequestData struct {
	ClientID       interface{} `json:"client_id"`
	MessageID      interface{} `json:"message_id"`
	ClientSendTime interface{} `json:"client_send_time"`
}

func getCSVPath() string {
	timestampSuffix := os.Getenv("TIMESTAMP_SUFFIX")
	if timestampSuffix != "" {
		return "/data/requests" + timestampSuffix + ".csv"
	}
	return "/data/requests.csv"
}

func logRequest(clientID, messageID string, clientSendTime, serverProcessingTime float64) {
	csvLock.Lock()
	defer csvLock.Unlock()

	csvPath := getCSVPath()
	file, err := os.OpenFile(csvPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Printf("Failed to open CSV: %v", err)
		return
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Calculate approximate client_receive_time and response_time with proper precision
	clientReceiveTime := float64(time.Now().UnixNano()) / 1e9
	responseTime := clientReceiveTime - clientSendTime

	// Get scenario parameters from environment variables
	numServers := os.Getenv("NUM_SERVERS")
	if numServers == "" {
		numServers = "unknown"
	}
	
	numClients := os.Getenv("NUM_CLIENTES")
	if numClients == "" {
		numClients = "unknown"
	}
	
	numMessages := os.Getenv("NUM_MENSAGENS")
	if numMessages == "" {
		numMessages = "unknown"
	}
	
	// Write data row in the expected format with all required columns
	writer.Write([]string{
		clientID,
		messageID,
		hostname(),                               // server_id
		fmt.Sprintf("%.6f", clientSendTime),      // client_send_time
		fmt.Sprintf("%.6f", serverProcessingTime), // server_processing_time
		fmt.Sprintf("%.6f", clientReceiveTime),   // client_receive_time
		fmt.Sprintf("%.6f", responseTime),        // response_time
		numServers,                               // num_servers
		numClients,                               // num_clients
		numMessages,                              // num_messages
	})
}

// Initialize CSV with proper header
func initCSV() {
	csvLock.Lock()
	defer csvLock.Unlock()

	csvPath := getCSVPath()
	// Check if file exists
	if _, err := os.Stat(csvPath); os.IsNotExist(err) {
		file, err := os.Create(csvPath)
		if err != nil {
			log.Fatalf("Failed to create CSV: %v", err)
		}
		defer file.Close()

		writer := csv.NewWriter(file)
		defer writer.Flush()

		// Write header in the expected format (matching the Python server)
		writer.Write([]string{
			"client_id", "message_id", "server_id", "client_send_time",
			"server_processing_time", "client_receive_time", "response_time",
			"num_servers", "num_clients", "num_messages",
		})
	}
}

func hostname() string {
	name, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return name
}

func parseFloat(value interface{}) float64 {
	switch v := value.(type) {
	case float64:
		return v
	case string:
		if f, err := strconv.ParseFloat(v, 64); err == nil {
			return f
		}
	case int:
		return float64(v)
	}
	return 0.0
}

func parseString(value interface{}) string {
	switch v := value.(type) {
	case string:
		return v
	case int:
		return strconv.Itoa(v)
	case float64:
		return strconv.FormatFloat(v, 'f', -1, 64)
	}
	return "unknown"
}

func handler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()

	// Extract request data
	var clientID, messageID string
	var clientSendTime float64

	if r.Method == "POST" {
		body, err := io.ReadAll(r.Body)
		if err == nil {
			var data RequestData
			if json.Unmarshal(body, &data) == nil {
				clientID = parseString(data.ClientID)
				messageID = parseString(data.MessageID)
				clientSendTime = parseFloat(data.ClientSendTime)
			}
		}
	}

	// Fallback for GET requests or malformed POST
	if clientID == "" {
		clientID = r.URL.Query().Get("client_id")
		if clientID == "" {
			clientID = "unknown"
		}
	}
	if messageID == "" {
		messageID = r.URL.Query().Get("message_id")
		if messageID == "" {
			messageID = "unknown"
		}
	}
	if clientSendTime == 0 {
		if sendTimeStr := r.URL.Query().Get("client_send_time"); sendTimeStr != "" {
			clientSendTime = parseFloat(sendTimeStr)
		} else {
			clientSendTime = float64(time.Now().UnixNano()) / 1e9
		}
	}

	// Simulate work
	time.Sleep(1 * time.Millisecond)

	serverProcessingTime := time.Since(start).Seconds()

	// Write response
	fmt.Fprintf(w, "Resposta do servidor %s", hostname())

	// Log request
	logRequest(clientID, messageID, clientSendTime, serverProcessingTime)
}

func main() {
	// Initialize logging
	initCSV()

	// Start server
	http.HandleFunc("/", handler)
	log.Println("Starting server on :5000")
	log.Fatal(http.ListenAndServe(":5000", nil))
}