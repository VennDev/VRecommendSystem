package event

// TypeStats EventTypeStats represents statistics for an event type
type TypeStats struct {
	EventType   string  `json:"event_type"`
	Weight      float64 `json:"weight"`
	RetentionMs int64   `json:"retention_ms"`
	Partitions  int     `json:"partitions"`
	Enabled     bool    `json:"enabled"`
	TopicName   string  `json:"topic_name"`
}

// Message EventMessage represents a message for an event
type Message struct {
	UserID    string                 `json:"user_id"`
	ItemID    string                 `json:"item_id,omitempty"`
	EventType string                 `json:"event_type"`
	Timestamp int64                  `json:"timestamp"`
	SessionID string                 `json:"session_id,omitempty"`
	DeviceID  string                 `json:"device_id,omitempty"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}
