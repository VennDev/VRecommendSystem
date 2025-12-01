# Build stage
FROM golang:1.24.4-alpine AS builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev librdkafka-dev pkgconf

WORKDIR /app

# Copy go mod files first for better caching
COPY go.mod go.sum ./

# Download dependencies (cached if go.mod/go.sum unchanged)
RUN go mod download

# Copy source code
COPY . .

# Build with optimizations
RUN CGO_ENABLED=1 GOOS=linux go build \
    -ldflags="-w -s" \
    -a -installsuffix cgo \
    -o main .

# Final image - use alpine for smaller size
FROM alpine:3.19

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    tzdata \
    librdkafka \
    curl

# Create non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D -s /bin/sh appuser

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/main .
COPY --from=builder /app/config ./config

# Copy .env file if it exists (optional)
COPY --from=builder /app/.env* ./

# Create user_logs directory with proper permissions
RUN mkdir -p /app/user_logs && \
    chown -R appuser:appgroup /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${HOST_PORT:-2030}/api/v1/ping || exit 1

CMD ["./main"]
