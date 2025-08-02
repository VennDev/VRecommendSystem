package types

import (
	"context"
	"github.com/venndev/vrecommendation/pkg/messaging"
)

type KafkaManager interface {
	GetProducer() messaging.MessageProducer
	GetConsumer(groupID string) messaging.MessageConsumer

	CreateTopic(ctx context.Context, topic string, partitions int, replicationFactor int) error
	DeleteTopic(ctx context.Context, topic string) error
	ListTopics(ctx context.Context) ([]string, error)

	CreateEventTopic(ctx context.Context, eventType string) error

	GetEnabledEventTypes() []string
	GetEventWeight(eventType string) float64
	IsEventTypeEnabled(eventType string) bool
	GetEventTopicName(eventType string) string

	HealthCheck(ctx context.Context) error
	Close() error
}
