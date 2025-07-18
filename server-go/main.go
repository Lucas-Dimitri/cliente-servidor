package main

import (
	"encoding/binary"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"sync"
	"time"
)

var (
	csvLock sync.Mutex
)

// Helper function to convert interface{} to string
func interfaceToString(v interface{}) string {
	switch val := v.(type) {
	case string:
		return val
	case int:
		return fmt.Sprintf("%d", val)
	case int64:
		return fmt.Sprintf("%d", val)
	case float64:
		return fmt.Sprintf("%.0f", val)
	default:
		return fmt.Sprintf("%v", val)
	}
}

// Protocol constants
const (
	MAGIC_NUMBER         = 0x12345678
	MSG_CLIENT_REQUEST   = 1
	MSG_SERVER_RESPONSE  = 2
	MSG_CLOSE_CONNECTION = 4
)

// Message structure
type Message struct {
	MagicNumber uint32          `json:"magic_number"`
	MsgType     uint32          `json:"msg_type"`
	Payload     json.RawMessage `json:"payload"`
}

// Payload for MSG_CLIENT_REQUEST
type MessagePayload struct {
	ClientID  string      `json:"client_id"`
	MessageID interface{} `json:"message_id"` // Accept both string and number
	Timestamp float64     `json:"timestamp"`
	Data      string      `json:"data"`
}

// Response structure
type ResponsePayload struct {
	Status           string  `json:"status"`
	ServerID         string  `json:"server_id"`
	ProcessingTime   float64 `json:"processing_time"` // Match client expectation
	ResponseMessage  string  `json:"response_message"`
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

// Handle individual client connection
func handleClient(conn net.Conn) {
	defer conn.Close()
	clientAddr := conn.RemoteAddr().String()
	log.Printf("Cliente conectado: %s", clientAddr)

	// Session statistics
	var clientID string
	messagesProcessed := 0
	totalProcessingTime := 0.0
	var firstMessageTime float64

	for {
		// Read protocol header (12 bytes: magic + type + length)
		headerBuf := make([]byte, 12)
		log.Printf("🔍 Aguardando header do cliente %s...", clientAddr)
		_, err := io.ReadFull(conn, headerBuf)
		if err != nil {
			if err != io.EOF {
				log.Printf("❌ Erro lendo header do cliente %s: %v", clientAddr, err)
			} else {
				log.Printf("📤 Cliente %s fechou conexão (EOF)", clientAddr)
			}
			break
		}

		// Parse header: magic (4 bytes), type (4 bytes), length (4 bytes)
		magic := binary.BigEndian.Uint32(headerBuf[0:4])
		msgType := binary.BigEndian.Uint32(headerBuf[4:8])
		payloadLength := binary.BigEndian.Uint32(headerBuf[8:12])

		log.Printf("🔍 Header recebido - Magic: 0x%x, Type: %d, Length: %d", magic, msgType, payloadLength)

		// Validate magic number
		if magic != MAGIC_NUMBER {
			log.Printf("❌ Magic number inválido: 0x%x (esperado: 0x%x)", magic, MAGIC_NUMBER)
			break
		}

		if payloadLength == 0 || payloadLength > 1024*1024 { // Limite de 1MB
			log.Printf("❌ Tamanho de payload inválido: %d", payloadLength)
			break
		}

		// Read the payload
		payloadBuf := make([]byte, payloadLength)
		log.Printf("🔍 Lendo payload de %d bytes...", payloadLength)
		_, err = io.ReadFull(conn, payloadBuf)
		if err != nil {
			log.Printf("❌ Erro lendo payload: %v", err)
			break
		}

		log.Printf("✅ Payload recebido: %s", string(payloadBuf))

		start := time.Now()

		if msgType == MSG_CLIENT_REQUEST {
			// Parse message payload
			var payload MessagePayload
			if err := json.Unmarshal(payloadBuf, &payload); err != nil {
				log.Printf("Erro parsing payload: %v", err)
				continue
			}

			// Simulate work
			time.Sleep(1 * time.Millisecond)

			serverProcessingTime := time.Since(start).Seconds()

			// Update session statistics
			if clientID == "" {
				clientID = payload.ClientID
				firstMessageTime = payload.Timestamp
			}

			messagesProcessed++
			totalProcessingTime += serverProcessingTime

			// Create response
			response := ResponsePayload{
				Status:          "success",
				ServerID:        hostname(),
				ProcessingTime:  serverProcessingTime, // Fixed field name
				ResponseMessage: fmt.Sprintf("Resposta do servidor %s", hostname()),
			}

			responseBytes, err := json.Marshal(response)
			if err != nil {
				log.Printf("Erro criando resposta: %v", err)
				continue
			}

			// Send response with protocol header
			responseLength := uint32(len(responseBytes))
			responseHeader := make([]byte, 12)
			binary.BigEndian.PutUint32(responseHeader[0:4], MAGIC_NUMBER)
			binary.BigEndian.PutUint32(responseHeader[4:8], MSG_SERVER_RESPONSE) // Correct response type
			binary.BigEndian.PutUint32(responseHeader[8:12], responseLength)

			if _, err := conn.Write(responseHeader); err != nil {
				log.Printf("Erro enviando header da resposta: %v", err)
				break
			}

			if _, err := conn.Write(responseBytes); err != nil {
				log.Printf("Erro enviando resposta: %v", err)
				break
			}

		} else if msgType == MSG_CLOSE_CONNECTION {
			log.Printf("Cliente %s solicitou fechamento da conexão", clientAddr)
			break
		}
	}

	// Log consolidated session data only once
	if clientID != "" && messagesProcessed > 0 {
		avgProcessingTime := totalProcessingTime / float64(messagesProcessed)
		logRequest(clientID, fmt.Sprintf("%d", messagesProcessed), firstMessageTime, avgProcessingTime)
	}

	log.Printf("Cliente %s desconectado", clientAddr)
}

func main() {
	// Initialize logging
	initCSV()

	// Start TCP server
	listener, err := net.Listen("tcp", ":5000")
	if err != nil {
		log.Fatalf("Erro iniciando servidor TCP: %v", err)
	}
	defer listener.Close()

	log.Println("🚀 Servidor de protocolo customizado iniciado em :5000")
	log.Printf("📊 Logs serão salvos em: %s", getCSVPath())
	log.Printf("🔧 Server ID: %s", hostname())

	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("Erro aceitando conexão: %v", err)
			continue
		}

		go handleClient(conn)
	}
}