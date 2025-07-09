package main

import (
	"encoding/csv"
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"
	"time"
)

var (
	csvLock sync.Mutex
)

func logRequest(clientIP string, responseTime float64) {
	csvLock.Lock()
	defer csvLock.Unlock()

	file, err := os.OpenFile("/data/requests.csv", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Printf("Failed to open CSV: %v", err)
		return
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Write data row (all values as strings)
	writer.Write([]string{
		time.Now().Format(time.RFC3339Nano),
		clientIP,
		fmt.Sprintf("%.6f", responseTime), // Convert float64 to string
		hostname(),
	})
}

// Initialize CSV with proper header
func initCSV() {
	csvLock.Lock()
	defer csvLock.Unlock()

	// Check if file exists
	if _, err := os.Stat("/data/requests.csv"); os.IsNotExist(err) {
		file, err := os.Create("/data/requests.csv")
		if err != nil {
			log.Fatalf("Failed to create CSV: %v", err)
		}
		defer file.Close()

		writer := csv.NewWriter(file)
		defer writer.Flush()

		// Write header
		writer.Write([]string{"timestamp", "client_ip", "response_time", "server_hostname"})
	}
}

func hostname() string {
	name, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return name
}

func handler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()

	// Simulate work
	time.Sleep(1 * time.Millisecond)

	// Write response
	fmt.Fprintf(w, "Resposta do servidor %s", hostname())

	// Log request
	logRequest(r.RemoteAddr, time.Since(start).Seconds())
}

func main() {
	// Initialize logging
	initCSV()

	// Start server
	http.HandleFunc("/", handler)
	log.Println("Starting server on :5000")
	log.Fatal(http.ListenAndServe(":5000", nil))
}