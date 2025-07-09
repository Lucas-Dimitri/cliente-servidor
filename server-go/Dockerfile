# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY . .

# Download dependencies
RUN go mod download

# Build static binary (adjust 'main.go' if your entrypoint has a different name)
RUN CGO_ENABLED=0 GOOS=linux go build -o /server

# Runtime stage
FROM alpine:3.18

# Create data directory for logs (matches Python server structure)
RUN mkdir -p /data

# Install CA certificates (needed for HTTPS if you add it later)
RUN apk --no-cache add ca-certificates

# Copy binary from builder
COPY --from=builder /server /server

# Copy any static files if needed (e.g., templates, assets)
# COPY --from=builder /app/static /static

# Expose port (must match your Go server port)
EXPOSE 5000

# Run the binary
CMD ["/server"]