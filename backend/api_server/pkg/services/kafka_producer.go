package services

import (
	"encoding/json"
	"fmt"
	"maps"
	"strconv"
	"time"

	"github.com/confluentinc/confluent-kafka-go/kafka"
	"github.com/venndev/vrecommendation/pkg/configs"
	ev "github.com/venndev/vrecommendation/pkg/event"
)

// InteractionEvent represents a user interaction event
type InteractionEvent struct {
	UserID    string         `json:"user_id"`
	ItemID    string         `json:"item_id"`
	EventType int            `json:"event_type"`
	Weight    float64        `json:"weight"`
	Timestamp time.Time      `json:"timestamp"`
	SessionID string         `json:"session_id,omitempty"`
	Duration  int64          `json:"duration,omitempty"`
	Context   map[string]any `json:"context,omitempty"`
}

// RecommendationProducer handles sending events to Kafka
type RecommendationProducer struct {
	producer *kafka.Producer
	config   *configs.KafkaConfigResult
}

// NewRecommendationProducer creates a new producer instance
func NewRecommendationProducer(config *configs.KafkaConfigResult) (*RecommendationProducer, error) {
	producer, err := kafka.NewProducer(config.GetProducerConfig())
	if err != nil {
		return nil, fmt.Errorf("failed to create producer: %v", err)
	}

	return &RecommendationProducer{
		producer: producer,
		config:   config,
	}, nil
}

// SendEvent sends an interaction event to the appropriate topic
func (rp *RecommendationProducer) SendEvent(eventType int, userID, itemID string, options ...EventOption) error {
	// Create base event
	event := &InteractionEvent{
		UserID:    userID,
		ItemID:    itemID,
		EventType: eventType,
		Weight:    ev.EventWeights[eventType],
		Timestamp: time.Now(),
		Context:   make(map[string]any),
	}

	// Apply options
	for _, option := range options {
		option(event)
	}

	// Serialize event to JSON
	eventData, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to marshal event: %v", err)
	}

	// Get topic name
	topicName := rp.config.GetTopicName(eventType)

	// Create weight header value using strconv.AppendFloat for better performance
	weightBuf := make([]byte, 0, 16)
	weightBuf = strconv.AppendFloat(weightBuf, event.Weight, 'f', 2, 64)

	// Create Kafka message
	message := &kafka.Message{
		TopicPartition: kafka.TopicPartition{
			Topic:     &topicName,
			Partition: kafka.PartitionAny,
		},
		Key:   []byte(userID), // Partition by user_id for ordering
		Value: eventData,
		Headers: []kafka.Header{
			{Key: "event_type", Value: []byte(ev.EventNames[eventType])},
			{Key: "weight", Value: weightBuf},
			{Key: "timestamp", Value: []byte(event.Timestamp.Format(time.RFC3339))},
		},
	}

	// Send message
	deliveryChan := make(chan kafka.Event)
	err = rp.producer.Produce(message, deliveryChan)
	if err != nil {
		return fmt.Errorf("failed to produce message: %v", err)
	}

	// Wait for delivery confirmation (optional, for critical events)
	select {
	case e := <-deliveryChan:
		if msg, ok := e.(*kafka.Message); ok {
			if msg.TopicPartition.Error != nil {
				return fmt.Errorf("delivery failed: %v", msg.TopicPartition.Error)
			}
		}
	case <-time.After(time.Second * 5):
		return fmt.Errorf("delivery timeout")
	}

	return nil
}

// SendEventAsync sends an event asynchronously without waiting for confirmation
func (rp *RecommendationProducer) SendEventAsync(eventType int, userID, itemID string, options ...EventOption) error {
	// Create base event
	event := &InteractionEvent{
		UserID:    userID,
		ItemID:    itemID,
		EventType: eventType,
		Weight:    ev.EventWeights[eventType],
		Timestamp: time.Now(),
		Context:   make(map[string]any),
	}

	// Apply options
	for _, option := range options {
		option(event)
	}

	// Serialize event to JSON
	eventData, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to marshal event: %v", err)
	}

	// Get topic name
	topicName := rp.config.GetTopicName(eventType)

	// Create weight header value using strconv.AppendFloat for better performance
	weightBuf := make([]byte, 0, 16)
	weightBuf = strconv.AppendFloat(weightBuf, event.Weight, 'f', 2, 64)

	// Create Kafka message
	message := &kafka.Message{
		TopicPartition: kafka.TopicPartition{
			Topic:     &topicName,
			Partition: kafka.PartitionAny,
		},
		Key:   []byte(userID),
		Value: eventData,
		Headers: []kafka.Header{
			{Key: "event_type", Value: []byte(ev.EventNames[eventType])},
			{Key: "weight", Value: weightBuf},
		},
	}

	// Send message asynchronously
	return rp.producer.Produce(message, nil)
}

// Flush waits for all pending messages to be delivered
func (rp *RecommendationProducer) Flush(timeoutMs int) int {
	return rp.producer.Flush(timeoutMs)
}

// Close closes the producer
func (rp *RecommendationProducer) Close() {
	rp.producer.Close()
}

// EventOption allows customizing event properties
type EventOption func(*InteractionEvent)

// WithSessionID sets the session ID for the event
func WithSessionID(sessionID string) EventOption {
	return func(event *InteractionEvent) {
		event.SessionID = sessionID
	}
}

// WithDuration sets the duration for the event (useful for VIEW events)
func WithDuration(duration time.Duration) EventOption {
	return func(event *InteractionEvent) {
		event.Duration = duration.Milliseconds()
	}
}

// WithContext adds context data to the event
func WithContext(context map[string]any) EventOption {
	return func(event *InteractionEvent) {
		// Use maps.Copy for better performance instead of manual loop
		maps.Copy(event.Context, context)
	}
}

// WithCustomWeight overrides the default event weight
func WithCustomWeight(weight float64) EventOption {
	return func(event *InteractionEvent) {
		event.Weight = weight
	}
}

// Convenience methods for common events

// TrackView tracks a view event
func (rp *RecommendationProducer) TrackView(userID, itemID string, options ...EventOption) error {
	return rp.SendEventAsync(ev.VIEW, userID, itemID, options...)
}

// TrackLike tracks a like event
func (rp *RecommendationProducer) TrackLike(userID, itemID string, options ...EventOption) error {
	return rp.SendEvent(ev.LIKE, userID, itemID, options...)
}

// TrackPurchase tracks a purchase event (synchronous - important)
func (rp *RecommendationProducer) TrackPurchase(userID, itemID string, options ...EventOption) error {
	return rp.SendEvent(ev.BUY, userID, itemID, options...)
}

// TrackAddToCart tracks add to cart event
func (rp *RecommendationProducer) TrackAddToCart(userID, itemID string, options ...EventOption) error {
	return rp.SendEvent(ev.ADD_TO_CART, userID, itemID, options...)
}

// BatchSendEvents sends multiple events in batch
func (rp *RecommendationProducer) BatchSendEvents(events []BatchEvent) error {
	for _, event := range events {
		err := rp.SendEventAsync(event.EventType, event.UserID, event.ItemID, event.Options...)
		if err != nil {
			return fmt.Errorf("failed to send batch event: %v", err)
		}
	}

	// Wait for all messages to be delivered
	remaining := rp.Flush(10000) // 10 second timeout
	if remaining > 0 {
		return fmt.Errorf("failed to deliver %d messages", remaining)
	}

	return nil
}

// BatchEvent represents an event for batch processing
type BatchEvent struct {
	EventType int
	UserID    string
	ItemID    string
	Options   []EventOption
}
