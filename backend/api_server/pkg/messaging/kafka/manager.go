package kafka

import (
	"context"
	"fmt"
	"strings"
	"sync"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"go.uber.org/zap"

	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/pkg/messaging"
	"github.com/venndev/vrecommendation/pkg/setting"
)

type Manager struct {
	config    *setting.Config
	producers map[string]*Producer
	consumers map[string]*Consumer
	mu        sync.RWMutex
	closed    bool
}

func NewManager() (*Manager, error) {
	if len(global.Config.Kafka.Brokers) == 0 {
		return nil, fmt.Errorf("kafka brokers not configured")
	}

	return &Manager{
		config:    &global.Config,
		producers: make(map[string]*Producer),
		consumers: make(map[string]*Consumer),
	}, nil
}

func (m *Manager) GetProducer() messaging.MessageProducer {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.closed {
		return nil
	}

	if producer, exists := m.producers["default"]; exists {
		return producer
	}

	producer, err := NewProducer(m.config)
	if err != nil {
		// Log error
		global.Logger.Error("Failed to create Kafka producer", err)
		return nil
	}

	m.producers["default"] = producer
	return producer
}

func (m *Manager) GetConsumer(groupID string) messaging.MessageConsumer {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.closed {
		return nil
	}

	if consumer, exists := m.consumers[groupID]; exists {
		return consumer
	}

	consumer, err := NewConsumer(m.config, groupID)
	if err != nil {
		global.Logger.Error("Failed to create Kafka consumer", err, zap.String("groupID", groupID))
		return nil
	}

	m.consumers[groupID] = consumer
	return consumer
}

func (m *Manager) CreateTopic(ctx context.Context, topic string, partitions int, replicationFactor int) error {
	adminConfig := m.buildAdminConfig()
	adminClient, err := kafka.NewAdminClient(&adminConfig)
	if err != nil {
		return fmt.Errorf("failed to create admin client: %w", err)
	}
	defer adminClient.Close()

	if partitions <= 0 {
		partitions = m.config.TopicDefaults.Partitions
	}
	if replicationFactor <= 0 {
		replicationFactor = m.config.TopicDefaults.ReplicationFactor
	}

	fullTopicName := m.buildTopicName(topic)

	// Get retention from event type configuration if applicable
	retentionMs := int64(m.config.TopicDefaults.RetentionMs)
	if eventType, err := m.extractEventTypeFromTopic(topic); err == nil {
		if eventRetention := m.config.EventTypes.GetEventRetention(eventType); eventRetention > 0 {
			retentionMs = eventRetention
		}
	}

	topicSpec := kafka.TopicSpecification{
		Topic:             fullTopicName,
		NumPartitions:     partitions,
		ReplicationFactor: replicationFactor,
		Config: map[string]string{
			"retention.ms": fmt.Sprintf("%d", retentionMs),
		},
	}

	results, err := adminClient.CreateTopics(ctx, []kafka.TopicSpecification{topicSpec})
	if err != nil {
		return fmt.Errorf("failed to create topic: %w", err)
	}

	for _, result := range results {
		if result.Error.Code() != kafka.ErrNoError && result.Error.Code() != kafka.ErrTopicAlreadyExists {
			return fmt.Errorf("failed to create topic %s: %v", result.Topic, result.Error)
		}
	}

	return nil
}

func (m *Manager) CreateEventTopic(ctx context.Context, eventType string) error {
	if !m.config.EventTypes.IsEventEnabled(eventType) {
		return fmt.Errorf("event type %s is not enabled", eventType)
	}

	topicName := m.buildEventTopicName(eventType)
	partitions := m.config.EventTypes.GetEventPartitions(eventType)

	return m.CreateTopic(ctx, topicName, partitions, m.config.TopicDefaults.ReplicationFactor)
}

func (m *Manager) DeleteTopic(ctx context.Context, topic string) error {
	adminConfig := m.buildAdminConfig()
	adminClient, err := kafka.NewAdminClient(&adminConfig)
	if err != nil {
		return fmt.Errorf("failed to create admin client: %w", err)
	}
	defer adminClient.Close()

	fullTopicName := m.buildTopicName(topic)
	results, err := adminClient.DeleteTopics(ctx, []string{fullTopicName})
	if err != nil {
		return fmt.Errorf("failed to delete topic: %w", err)
	}

	for _, result := range results {
		if result.Error.Code() != kafka.ErrNoError {
			return fmt.Errorf("failed to delete topic %s: %v", result.Topic, result.Error)
		}
	}

	return nil
}

func (m *Manager) ListTopics(ctx context.Context) ([]string, error) {
	adminConfig := m.buildAdminConfig()
	adminClient, err := kafka.NewAdminClient(&adminConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create admin client: %w", err)
	}
	defer adminClient.Close()

	metadata, err := adminClient.GetMetadata(nil, false, 5000)
	if err != nil {
		return nil, fmt.Errorf("failed to get metadata: %w", err)
	}

	var topics []string
	for topic := range metadata.Topics {
		topics = append(topics, topic)
	}

	return topics, nil
}

func (m *Manager) Close() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.closed {
		return nil
	}

	var errors []error

	// Close all producers
	for name, producer := range m.producers {
		if err := producer.Close(); err != nil {
			errors = append(errors, fmt.Errorf("failed to close producer %s: %w", name, err))
		}
	}

	// Close all consumers
	for groupID, consumer := range m.consumers {
		if err := consumer.Close(); err != nil {
			errors = append(errors, fmt.Errorf("failed to close consumer %s: %w", groupID, err))
		}
	}

	m.closed = true

	if len(errors) > 0 {
		return fmt.Errorf("kafka close errors: %v", errors)
	}
	return nil
}

func (m *Manager) HealthCheck(ctx context.Context) error {
	testConfig := m.buildProducerConfig()
	testConfig["client.id"] = fmt.Sprintf("%s-health-check", m.config.Kafka.ClientID)

	producer, err := kafka.NewProducer(&testConfig)
	if err != nil {
		return fmt.Errorf("kafka health check failed: %w", err)
	}
	defer producer.Close()

	// Check metadata
	metadata, err := producer.GetMetadata(nil, false, 5000)
	if err != nil {
		return fmt.Errorf("kafka metadata check failed: %w", err)
	}

	if len(metadata.Brokers) == 0 {
		return fmt.Errorf("no kafka brokers available")
	}

	return nil
}

// GetEnabledEventTypes Event-related helper methods
func (m *Manager) GetEnabledEventTypes() []string {
	return m.config.EventTypes.GetEnabledEvents()
}

func (m *Manager) GetEventWeight(eventType string) float64 {
	return m.config.EventTypes.GetEventWeight(eventType)
}

func (m *Manager) IsEventTypeEnabled(eventType string) bool {
	return m.config.EventTypes.IsEventEnabled(eventType)
}

func (m *Manager) GetEventTopicName(eventType string) string {
	return m.buildEventTopicName(eventType)
}

// Helper methods
func (m *Manager) buildTopicName(topic string) string {
	fullName := topic
	if m.config.Topics.Prefix != "" {
		fullName = m.config.Topics.Prefix + fullName
	}
	if m.config.Topics.Suffix != "" {
		fullName = fullName + m.config.Topics.Suffix
	}
	return fullName
}

func (m *Manager) buildEventTopicName(eventType string) string {
	return m.buildTopicName(eventType)
}

func (m *Manager) extractEventTypeFromTopic(topic string) (string, error) {
	// Remove prefix and suffix to get an event type
	eventType := topic
	if m.config.Topics.Prefix != "" {
		eventType = strings.TrimPrefix(eventType, m.config.Topics.Prefix)
	}
	if m.config.Topics.Suffix != "" {
		eventType = strings.TrimSuffix(eventType, m.config.Topics.Suffix)
	}

	// Validate if it's a known event type
	if !m.config.EventTypes.IsEventEnabled(eventType) {
		return "", fmt.Errorf("unknown or disabled event type: %s", eventType)
	}

	return eventType, nil
}

func (m *Manager) buildAdminConfig() kafka.ConfigMap {
	config := kafka.ConfigMap{
		"bootstrap.servers": strings.Join(m.config.Kafka.Brokers, ","),
		"client.id":         m.config.Kafka.ClientID + "-admin",
	}

	// Add security config if enabled
	if m.config.Security.Protocol != "" {
		config["security.protocol"] = m.config.Security.Protocol

		if m.config.Security.SASL.Mechanism != "" {
			config["sasl.mechanism"] = m.config.Security.SASL.Mechanism
			config["sasl.username"] = m.config.Security.SASL.Username
			config["sasl.password"] = m.config.Security.SASL.Password
		}

		if m.config.Security.SSL.Truststore.Location != "" {
			config["ssl.ca.location"] = m.config.Security.SSL.Truststore.Location
			config["ssl.ca.password"] = m.config.Security.SSL.Truststore.Password
		}

		if m.config.Security.SSL.Keystore.Location != "" {
			config["ssl.certificate.location"] = m.config.Security.SSL.Keystore.Location
			config["ssl.key.password"] = m.config.Security.SSL.Keystore.Password
		}
	}

	return config
}

func (m *Manager) buildProducerConfig() kafka.ConfigMap {
	config := kafka.ConfigMap{
		"bootstrap.servers":                     strings.Join(m.config.Kafka.Brokers, ","),
		"client.id":                             m.config.Kafka.ClientID,
		"acks":                                  m.config.Producer.Acks,
		"retries":                               m.config.Producer.Retries,
		"retry.backoff.ms":                      m.config.Producer.RetryBackoffMs,
		"enable.idempotence":                    m.config.Producer.EnableIdempotence,
		"max.in.flight.requests.per.connection": m.config.Producer.MaxInFlightRequestsPerConnection,
		"batch.size":                            m.config.Producer.BatchSize,
		"linger.ms":                             m.config.Producer.LingerMs,
		// "buffer.memory":                         m.config.Producer.BufferMemory,
		"compression.type":    m.config.Producer.CompressionType,
		"message.max.bytes":   m.config.Producer.MaxRequestSize,
		"request.timeout.ms":  m.config.Producer.RequestTimeoutMs,
		"delivery.timeout.ms": m.config.Producer.DeliveryTimeoutMs,
	}

	// Add security config
	m.addSecurityConfig(&config)
	return config
}

func (m *Manager) buildConsumerConfig(groupID string) kafka.ConfigMap {
	config := kafka.ConfigMap{
		"bootstrap.servers":         strings.Join(m.config.Kafka.Brokers, ","),
		"group.id":                  groupID,
		"client.id":                 fmt.Sprintf("%s-%s", m.config.Kafka.ClientID, groupID),
		"auto.offset.reset":         m.config.Kafka.AutoOffsetReset,
		"fetch.min.bytes":           m.config.Consumer.FetchMinBytes,
		"fetch.max.bytes":           m.config.Consumer.FetchMaxBytes,
		"fetch.max.wait.ms":         m.config.Consumer.FetchMaxWaitMs,
		"max.partition.fetch.bytes": m.config.Consumer.MaxPartitionFetchBytes,
		"session.timeout.ms":        m.config.Consumer.SessionTimeoutMs,
		"heartbeat.interval.ms":     m.config.Consumer.HeartbeatIntervalMs,
		"max.poll.interval.ms":      m.config.Consumer.MaxPollIntervalMs,
		"enable.auto.commit":        m.config.Consumer.EnableAutoCommit,
		"auto.commit.interval.ms":   m.config.Consumer.AutoCommitIntervalMs,
	}

	m.addSecurityConfig(&config)

	return config
}

func (m *Manager) addSecurityConfig(config *kafka.ConfigMap) {
	if m.config.Security.Protocol != "" {
		(*config)["security.protocol"] = m.config.Security.Protocol

		if m.config.Security.SASL.Mechanism != "" {
			(*config)["sasl.mechanism"] = m.config.Security.SASL.Mechanism
			(*config)["sasl.username"] = m.config.Security.SASL.Username
			(*config)["sasl.password"] = m.config.Security.SASL.Password
		}

		if m.config.Security.SSL.Truststore.Location != "" {
			(*config)["ssl.ca.location"] = m.config.Security.SSL.Truststore.Location
			(*config)["ssl.ca.password"] = m.config.Security.SSL.Truststore.Password
		}

		if m.config.Security.SSL.Keystore.Location != "" {
			(*config)["ssl.certificate.location"] = m.config.Security.SSL.Keystore.Location
			(*config)["ssl.key.password"] = m.config.Security.SSL.Keystore.Password
		}
	}
}
