package configs

import (
	"context"
	"fmt"
	"strconv"
	"time"

	"github.com/confluentinc/confluent-kafka-go/kafka"
	"github.com/venndev/vrecommendation/pkg/event"
	"github.com/venndev/vrecommendation/pkg/logger"
	"github.com/venndev/vrecommendation/pkg/utils/env"
)

type KafkaConfigResult struct {
	Brokers           string
	TopicPrefix       string
	TopicSuffix       string
	DefaultPartitions int32
	ReplicationFactor int16
	RetentionMs       map[int]int64
	ProducerConfig    map[string]any
	ConsumerConfig    map[string]any
	Logger            *logger.Logger
}

func KafkaConfig() *KafkaConfigResult {
	config := &KafkaConfigResult{
		Brokers:           env.GetEnv("KAFKA_BROKERS", "localhost:9092"),
		TopicPrefix:       env.GetEnv("KAFKA_TOPIC_PREFIX", "user_interactions"),
		TopicSuffix:       env.GetEnv("KAFKA_TOPIC_SUFFIX", "_events"),
		DefaultPartitions: int32(env.GetEnvInt("KAFKA_DEFAULT_PARTITIONS", 12)),
		ReplicationFactor: int16(env.GetEnvInt("KAFKA_DEFAULT_REPLICATION_FACTOR", 1)),
		RetentionMs:       make(map[int]int64),
		ProducerConfig:    make(map[string]any),
		ConsumerConfig:    make(map[string]any),
	}

	config.RetentionMs[event.VIEW] = env.GetEnvInt64("KAFKA_RETENTION_VIEW_EVENTS", 86400000)         // 1 day
	config.RetentionMs[event.LIKE] = env.GetEnvInt64("KAFKA_RETENTION_LIKE_EVENTS", 2592000000)       // 30 days
	config.RetentionMs[event.BUY] = env.GetEnvInt64("KAFKA_RETENTION_BUY_EVENTS", 31536000000)        // 1 year
	config.RetentionMs[event.ADD_TO_CART] = env.GetEnvInt64("KAFKA_RETENTION_CART_EVENTS", 604800000) // 7 days

	defaultRetention := env.GetEnvInt64("KAFKA_DEFAULT_RETENTION_MS", 604800000) // 7 days
	for eventType := range event.EventNames {
		if _, exists := config.RetentionMs[eventType]; !exists {
			config.RetentionMs[eventType] = defaultRetention
		}
	}

	config.loadProducerConfig()
	config.loadConsumerConfig()

	return config
}

func (c *KafkaConfigResult) loadProducerConfig() {
	c.ProducerConfig = map[string]any{
		"bootstrap.servers":                     c.Brokers,
		"acks":                                  env.GetEnv("KAFKA_ACKS", "all"),
		"retries":                               env.GetEnv("KAFKA_RETRIES", "3"),
		"enable.idempotence":                    env.GetEnv("KAFKA_ENABLE_IDEMPOTENCE", "true"),
		"compression.type":                      env.GetEnv("KAFKA_COMPRESSION_TYPE", "snappy"),
		"batch.size":                            env.GetEnv("KAFKA_BATCH_SIZE", "16384"),
		"linger.ms":                             env.GetEnv("KAFKA_LINGER_MS", "5"),
		"buffer.memory":                         env.GetEnv("KAFKA_BUFFER_MEMORY", "33554432"),
		"max.request.size":                      env.GetEnv("KAFKA_MAX_REQUEST_SIZE", "1048576"),
		"request.timeout.ms":                    env.GetEnv("KAFKA_REQUEST_TIMEOUT_MS", "30000"),
		"delivery.timeout.ms":                   env.GetEnv("KAFKA_DELIVERY_TIMEOUT_MS", "120000"),
		"retry.backoff.ms":                      env.GetEnv("KAFKA_RETRY_BACKOFF_MS", "1000"),
		"max.in.flight.requests.per.connection": env.GetEnv("KAFKA_MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION", "5"),
	}
}

func (c *KafkaConfigResult) loadConsumerConfig() {
	c.ConsumerConfig = map[string]any{
		"bootstrap.servers":         c.Brokers,
		"group.id":                  env.GetEnv("KAFKA_CONSUMER_GROUP_REALTIME", "realtime_recommendation_group"),
		"auto.offset.reset":         env.GetEnv("KAFKA_AUTO_OFFSET_RESET", "earliest"),
		"enable.auto.commit":        env.GetEnv("KAFKA_ENABLE_AUTO_COMMIT", "false"),
		"auto.commit.interval.ms":   env.GetEnv("KAFKA_AUTO_COMMIT_INTERVAL_MS", "5000"),
		"session.timeout.ms":        env.GetEnv("KAFKA_SESSION_TIMEOUT_MS", "30000"),
		"heartbeat.interval.ms":     env.GetEnv("KAFKA_HEARTBEAT_INTERVAL_MS", "3000"),
		"max.poll.interval.ms":      env.GetEnv("KAFKA_MAX_POLL_INTERVAL_MS", "300000"),
		"max.poll.records":          env.GetEnv("KAFKA_MAX_POLL_RECORDS", "500"),
		"fetch.min.bytes":           env.GetEnv("KAFKA_FETCH_MIN_BYTES", "1"),
		"fetch.max.bytes":           env.GetEnv("KAFKA_FETCH_MAX_BYTES", "52428800"),
		"fetch.max.wait.ms":         env.GetEnv("KAFKA_FETCH_MAX_WAIT_MS", "500"),
		"max.partition.fetch.bytes": env.GetEnv("KAFKA_MAX_PARTITION_FETCH_BYTES", "1048576"),
	}
}

func (c *KafkaConfigResult) GetTopicName(eventType int) string {
	eventName := event.EventNames[eventType]
	return fmt.Sprintf("%s_%s%s", c.TopicPrefix, eventName, c.TopicSuffix)
}

func (c *KafkaConfigResult) GetProducerConfig() *kafka.ConfigMap {
	configMap := &kafka.ConfigMap{}
	for key, value := range c.ProducerConfig {
		configMap.SetKey(key, value)
	}
	return configMap
}

func (c *KafkaConfigResult) GetConsumerConfig(groupID string) *kafka.ConfigMap {
	configMap := &kafka.ConfigMap{}
	for key, value := range c.ConsumerConfig {
		configMap.SetKey(key, value)
	}
	if groupID != "" {
		configMap.SetKey("group.id", groupID)
	}
	return configMap
}

func (c *KafkaConfigResult) CreateAllTopics() error {
	adminClient, err := kafka.NewAdminClient(&kafka.ConfigMap{
		"bootstrap.servers": c.Brokers,
	})
	if err != nil {
		return fmt.Errorf("failed to create admin client: %v", err)
	}
	defer adminClient.Close()

	var topicSpecs []kafka.TopicSpecification

	for eventType := range event.EventNames {
		topicName := c.GetTopicName(eventType)
		retentionMs := c.RetentionMs[eventType]

		topicSpec := kafka.TopicSpecification{
			Topic:             topicName,
			NumPartitions:     int(c.DefaultPartitions),
			ReplicationFactor: int(c.ReplicationFactor),
			Config: map[string]string{
				"retention.ms":        strconv.FormatInt(retentionMs, 10),
				"cleanup.policy":      "delete",
				"compression.type":    "snappy",
				"min.insync.replicas": "1",
			},
		}

		topicSpecs = append(topicSpecs, topicSpec)
		fmt.Printf("Preparing topic: %s (retention: %d ms, weight: %.1f)\n",
			topicName, retentionMs, event.EventWeights[eventType])
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	results, err := adminClient.CreateTopics(
		ctx,
		topicSpecs,
		kafka.SetAdminOperationTimeout(time.Second*30),
	)
	if err != nil {
		return fmt.Errorf("failed to create topics: %v", err)
	}

	// Check results
	for _, result := range results {
		if result.Error.Code() != kafka.ErrNoError && result.Error.Code() != kafka.ErrTopicAlreadyExists {
			fmt.Printf("Failed to create topic %s: %v\n", result.Topic, result.Error)
		} else {
			fmt.Printf("Topic created/exists: %s\n", result.Topic)
		}
	}

	return nil
}

func (c *KafkaConfigResult) GetAllTopicNames() []string {
	var topics []string
	for eventType := range event.EventNames {
		topics = append(topics, c.GetTopicName(eventType))
	}
	return topics
}

func (c *KafkaConfigResult) ValidateConfig() error {
	if c.Brokers == "" {
		return fmt.Errorf("KAFKA_BROKERS cannot be empty")
	}

	if c.DefaultPartitions <= 0 {
		return fmt.Errorf("KAFKA_DEFAULT_PARTITIONS must be greater than 0")
	}

	if c.ReplicationFactor <= 0 {
		return fmt.Errorf("KAFKA_DEFAULT_REPLICATION_FACTOR must be greater than 0")
	}

	return nil
}

func (c *KafkaConfigResult) PrintTopicSummary() {
	fmt.Println("\nKafka Topics Configuration Summary:")
	fmt.Printf("Brokers: %s\n", c.Brokers)
	fmt.Printf("Default Partitions: %d\n", c.DefaultPartitions)
	fmt.Printf("Replication Factor: %d\n", c.ReplicationFactor)
	fmt.Println("\nTopics to be created:")

	for eventType, _ := range event.EventNames {
		topicName := c.GetTopicName(eventType)
		retention := c.RetentionMs[eventType]
		weight := event.EventWeights[eventType]
		retentionDays := retention / (24 * 60 * 60 * 1000) // Convert ms to days

		fmt.Printf("  %-35s | Weight: %5.1f | Retention: %2d days\n",
			topicName, weight, retentionDays)
	}
	fmt.Println()
}
