# Build
FROM golang:1.24.4 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=1 GOOS=linux go build -a -installsuffix cgo -o main .

# Final image
FROM golang:1.24.4
RUN apt-get update && apt-get install -y ca-certificates tzdata librdkafka-dev curl && rm -rf /var/lib/apt/lists/*
RUN addgroup --gid 1001 appgroup && adduser --uid 1001 --gid 1001 --disabled-password --gecos "" appuser
WORKDIR /app
COPY --from=builder /app/main .
COPY --from=builder /app/config ./config
USER appuser
CMD ["./main"]