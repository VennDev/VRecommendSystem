package services

import (
	"context"
	"encoding/json"
	"fmt"
	"go.uber.org/zap"
	"maps"
	"strconv"
	"time"

	"github.com/venndev/vrecommendation/global"
	ev "github.com/venndev/vrecommendation/pkg/event"
	"github.com/venndev/vrecommendation/pkg/messaging"
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

// RecommendationProducer handles sending events to Kafka using the new messaging interface
type RecommendationProducer struct {
	producer messaging.MessageProducer
	timeout  time.Duration
}

// NewRecommendationProducer creates a new producer instance using global MessageBroker
func NewRecommendationProducer() (*RecommendationProducer, error) {
	if global.MessageBroker == nil {
		return nil, fmt.Errorf("global MessageBroker is not initialized")
	}

	producer := global.MessageBroker.GetProducer()
	if producer == nil {
		return nil, fmt.Errorf("failed to get producer from global MessageBroker")
	}

	return &RecommendationProducer{
		producer: producer,
		timeout:  time.Duration(global.Config.Producer.DeliveryTimeoutMs) * time.Millisecond,
	}, nil
}

// getTopicName gets topic name based on event type
func getTopicName(eventType int) string {
	switch eventType {
	case ev.VIEW:
		return "view-events"
	case ev.LIKE:
		return "like-events"
	case ev.COMMENT:
		return "comment-events"
	case ev.SHARE:
		return "share-events"
	case ev.BOOKMARK:
		return "bookmark-events"
	case ev.ADD_TO_CART:
		return "cart-events"
	case ev.ADD_TO_FAVORITES:
		return "favorite-events"
	case ev.BUY:
		return "buy-events"
	default:
		return "user-events"
	}
}

// SendEvent sends an interaction event to the appropriate topic synchronously
func (rp *RecommendationProducer) SendEvent(eventType int, userID, itemID string, options ...EventOption) error {
	ctx, cancel := context.WithTimeout(context.Background(), rp.timeout)
	defer cancel()

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
		global.Logger.Error("Failed to marshal event", err)
		return fmt.Errorf("failed to marshal event: %w", err)
	}

	// Get topic name
	topicName := getTopicName(eventType)

	// Create headers
	headers := rp.buildHeaders(event)

	// Send message synchronously
	err = rp.producer.SendMessageWithHeaders(ctx, topicName, []byte(userID), eventData, headers)
	if err != nil {
		global.Logger.Error("Failed to produce message", err, zap.String("topic", topicName))
		return fmt.Errorf("failed to produce message: %w", err)
	}

	global.Logger.Debug(
		"Message sent successfully",
		zap.String("topic", topicName),
		zap.String("userID", userID),
		zap.String("itemID", itemID))
	return nil
}

// SendEventAsync sends an event asynchronously without waiting for confirmation
func (rp *RecommendationProducer) SendEventAsync(eventType int, userID, itemID string, options ...EventOption) error {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
	defer cancel()

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
		global.Logger.Error("Failed to marshal event", err)
		return fmt.Errorf("failed to marshal event: %w", err)
	}

	// Get topic name
	topicName := getTopicName(eventType)

	// Send message asynchronously
	err = rp.producer.SendMessageAsync(ctx, topicName, []byte(userID), eventData)
	if err != nil {
		global.Logger.Error("Failed to produce async message", err, zap.String("topic", topicName))
		return fmt.Errorf("failed to produce async message: %w", err)
	}

	global.Logger.Debug(
		"Async message sent",
		zap.String("topic", topicName),
		zap.String("userID", userID),
		zap.String("itemID", itemID))
	return nil
}

// buildHeaders creates headers for the message
func (rp *RecommendationProducer) buildHeaders(event *InteractionEvent) map[string][]byte {
	// Create weight header value using strconv.AppendFloat for better performance
	weightBuf := make([]byte, 0, 16)
	weightBuf = strconv.AppendFloat(weightBuf, event.Weight, 'f', 2, 64)

	headers := map[string][]byte{
		"event_type": []byte(ev.EventNames[event.EventType]),
		"weight":     weightBuf,
		"timestamp":  []byte(event.Timestamp.Format(time.RFC3339)),
		"user_id":    []byte(event.UserID),
		"item_id":    []byte(event.ItemID),
	}

	if event.SessionID != "" {
		headers["session_id"] = []byte(event.SessionID)
	}

	if event.Duration > 0 {
		headers["duration"] = []byte(strconv.FormatInt(event.Duration, 10))
	}

	return headers
}

// Flush waits for all pending messages to be delivered
func (rp *RecommendationProducer) Flush(timeoutMs int) int {
	remaining := rp.producer.Flush(timeoutMs)
	if remaining > 0 {
		global.Logger.Error("Failed to deliver messages", nil, zap.Int("remaining", remaining))
	}
	return remaining
}

// Close closes the producer
func (rp *RecommendationProducer) Close() {
	err := rp.producer.Close()
	if err != nil {
		global.Logger.Error("Failed to close producer", err)
	} else {
		global.Logger.Info("RecommendationProducer closed successfully")
	}
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

// WithTimestamp sets custom timestamp for the event
func WithTimestamp(timestamp time.Time) EventOption {
	return func(event *InteractionEvent) {
		event.Timestamp = timestamp
	}
}

// Convenience methods for common events

// TrackView tracks a view event (async by default for performance)
func (rp *RecommendationProducer) TrackView(userID, itemID string, options ...EventOption) error {
	return rp.SendEventAsync(ev.VIEW, userID, itemID, options...)
}

// TrackLike tracks a like event (sync for importance)
func (rp *RecommendationProducer) TrackLike(userID, itemID string, options ...EventOption) error {
	return rp.SendEvent(ev.LIKE, userID, itemID, options...)
}

// TrackComment tracks a comment event (sync for importance)
func (rp *RecommendationProducer) TrackComment(userID, itemID string, options ...EventOption) error {
	return rp.SendEvent(ev.COMMENT, userID, itemID, options...)
}

// TrackShare tracks a share event (sync for importance)
func (rp *RecommendationProducer) TrackShare(userID, itemID string, options ...EventOption) error {
	return rp.SendEvent(ev.SHARE, userID, itemID, options...)
}

// TrackBookmark tracks a bookmark event (sync for importance)
func (rp *RecommendationProducer) TrackBookmark(userID, itemID string, options ...EventOption) error {
	return rp.SendEvent(ev.BOOKMARK, userID, itemID, options...)
}

// TrackAddToFavorites tracks add to favorites event (sync for importance)
func (rp *RecommendationProducer) TrackAddToFavorites(userID, itemID string, options ...EventOption) error {
	return rp.SendEvent(ev.ADD_TO_FAVORITES, userID, itemID, options...)
}

// TrackPurchase tracks a purchase event (synchronous - critical)
func (rp *RecommendationProducer) TrackPurchase(userID, itemID string, options ...EventOption) error {
	return rp.SendEvent(ev.BUY, userID, itemID, options...)
}

// TrackAddToCart tracks add to cart event (sync for importance)
func (rp *RecommendationProducer) TrackAddToCart(userID, itemID string, options ...EventOption) error {
	return rp.SendEvent(ev.ADD_TO_CART, userID, itemID, options...)
}

// BatchSendEvents sends multiple events in batch
func (rp *RecommendationProducer) BatchSendEvents(events []BatchEvent) error {
	global.Logger.Info("Sending batch events", zap.Int("count", len(events)))

	for i, event := range events {
		var err error

		// Choose sync/async based on event type importance
		switch event.EventType {
		case ev.VIEW:
			err = rp.SendEventAsync(event.EventType, event.UserID, event.ItemID, event.Options...)
		case ev.BUY, ev.ADD_TO_CART:
			err = rp.SendEvent(event.EventType, event.UserID, event.ItemID, event.Options...)
		default:
			err = rp.SendEventAsync(event.EventType, event.UserID, event.ItemID, event.Options...)
		}

		if err != nil {
			global.Logger.Error("Failed to send batch event", err, zap.Int("index", i))
			return fmt.Errorf("failed to send batch event %d: %w", i, err)
		}
	}

	// Wait for all messages to be delivered
	remaining := rp.Flush(10000) // 10 second timeout
	if remaining > 0 {
		return fmt.Errorf("failed to deliver %d messages", remaining)
	}

	global.Logger.Info("Successfully sent batch events", zap.Int("count", len(events)))
	return nil
}

// BatchSendEventsAsync sends multiple events asynchronously for high throughput
func (rp *RecommendationProducer) BatchSendEventsAsync(events []BatchEvent) error {
	global.Logger.Info("Sending batch events async", zap.Int("count", len(events)))

	for i, event := range events {
		err := rp.SendEventAsync(event.EventType, event.UserID, event.ItemID, event.Options...)
		if err != nil {
			global.Logger.Error("Failed to send async batch event", err, zap.Int("index", i))
			return fmt.Errorf("failed to send async batch event %d: %w", i, err)
		}
	}

	global.Logger.Info("Successfully queued batch events", zap.Int("count", len(events)))
	return nil
}

// BatchEvent represents an event for batch processing
type BatchEvent struct {
	EventType int
	UserID    string
	ItemID    string
	Options   []EventOption
}

// RecommendationProducerPool manages multiple producer instances for high throughput
type RecommendationProducerPool struct {
	producers []*RecommendationProducer
	current   int
	size      int
}

// NewRecommendationProducerPool creates a pool of producers
func NewRecommendationProducerPool(size int) (*RecommendationProducerPool, error) {
	if size <= 0 {
		size = 1
	}

	producers := make([]*RecommendationProducer, size)
	for i := 0; i < size; i++ {
		producer, err := NewRecommendationProducer()
		if err != nil {
			// Close previously created producers
			for j := 0; j < i; j++ {
				producers[j].Close()
			}
			return nil, fmt.Errorf("failed to create producer %d: %w", i, err)
		}
		producers[i] = producer
	}

	return &RecommendationProducerPool{
		producers: producers,
		current:   0,
		size:      size,
	}, nil
}

// GetProducer returns the next producer in round-robin fashion
func (pool *RecommendationProducerPool) GetProducer() *RecommendationProducer {
	producer := pool.producers[pool.current]
	pool.current = (pool.current + 1) % pool.size
	return producer
}

// Close closes all producers in the pool
func (pool *RecommendationProducerPool) Close() {
	for _, producer := range pool.producers {
		producer.Close()
	}
}

// Global convenience functions

// GetRecommendationProducer returns a new producer instance using global MessageBroker
func GetRecommendationProducer() (*RecommendationProducer, error) {
	return NewRecommendationProducer()
}

// TrackUserEvent is a global convenience function to track any user event
func TrackUserEvent(eventType int, userID, itemID string, options ...EventOption) error {
	producer, err := GetRecommendationProducer()
	if err != nil {
		return err
	}
	defer producer.Close()

	// Use async for high-frequency events, sync for important events
	switch eventType {
	case ev.VIEW:
		return producer.SendEventAsync(eventType, userID, itemID, options...)
	case ev.BUY, ev.ADD_TO_CART, ev.LIKE, ev.COMMENT, ev.SHARE:
		return producer.SendEvent(eventType, userID, itemID, options...)
	default:
		return producer.SendEventAsync(eventType, userID, itemID, options...)
	}
}

// TrackUserView is a global convenience function for view events
func TrackUserView(userID, itemID string, duration time.Duration, sessionID string) error {
	options := []EventOption{
		WithDuration(duration),
	}
	if sessionID != "" {
		options = append(options, WithSessionID(sessionID))
	}

	return TrackUserEvent(ev.VIEW, userID, itemID, options...)
}

// TrackUserPurchase is a global convenience function for purchase events
func TrackUserPurchase(userID, itemID string, context map[string]any) error {
	options := []EventOption{}
	if context != nil {
		options = append(options, WithContext(context))
	}

	return TrackUserEvent(ev.BUY, userID, itemID, options...)
}

// TrackUserInteraction is a comprehensive function to track any interaction
func TrackUserInteraction(eventType int, userID, itemID, sessionID string, duration time.Duration, context map[string]any) error {
	options := []EventOption{}

	if sessionID != "" {
		options = append(options, WithSessionID(sessionID))
	}

	if duration > 0 {
		options = append(options, WithDuration(duration))
	}

	if context != nil {
		options = append(options, WithContext(context))
	}

	return TrackUserEvent(eventType, userID, itemID, options...)
}

// Singleton pattern for global producer (optional)
var (
	globalProducer     *RecommendationProducer
	globalProducerPool *RecommendationProducerPool
	poolSize           = 5 // Default pool size
)

// InitializeGlobalProducer initializes the global producer
func InitializeGlobalProducer() error {
	producer, err := NewRecommendationProducer()
	if err != nil {
		return err
	}
	globalProducer = producer
	return nil
}

// InitializeGlobalProducerPool initializes the global producer pool
func InitializeGlobalProducerPool(size int) error {
	pool, err := NewRecommendationProducerPool(size)
	if err != nil {
		return err
	}
	globalProducerPool = pool
	poolSize = size
	return nil
}

// GetGlobalProducer returns the global producer instance
func GetGlobalProducer() *RecommendationProducer {
	return globalProducer
}

// GetGlobalProducerPool returns the global producer pool
func GetGlobalProducerPool() *RecommendationProducerPool {
	return globalProducerPool
}

// CloseGlobalResources closes all global producer resources
func CloseGlobalResources() {
	if globalProducer != nil {
		globalProducer.Close()
		globalProducer = nil
	}

	if globalProducerPool != nil {
		globalProducerPool.Close()
		globalProducerPool = nil
	}
}
