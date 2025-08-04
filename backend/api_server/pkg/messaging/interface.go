package messaging

import (
	"context"
	"time"
)

type MessageProducer interface {
	SendMessage(ctx context.Context, topic string, key, value []byte) error
	SendMessageAsync(ctx context.Context, topic string, key, value []byte) error
	SendMessageWithHeaders(ctx context.Context, topic string, key, value []byte, headers map[string][]byte) error
	Flush(timeoutMs int) int
	Close() error
}

type MessageConsumer interface {
	Subscribe(topics []string) error
	Consume(ctx context.Context) (<-chan Message, <-chan error)
	Commit(ctx context.Context, message Message) error
	CommitOffset(ctx context.Context, topic string, partition int, offset int64) error
	Close() error
}

type Message struct {
	Topic     string
	Key       []byte
	Value     []byte
	Partition int
	Offset    int64
	Headers   map[string][]byte
	Timestamp time.Time
}

type MessageBroker interface {
	GetProducer() MessageProducer
	GetConsumer(groupID string) MessageConsumer
	CreateTopic(ctx context.Context, topic string, partitions int, replicationFactor int) error
	DeleteTopic(ctx context.Context, topic string) error
	ListTopics(ctx context.Context) ([]string, error)
	HealthCheck(ctx context.Context) error
	Close() error
}
