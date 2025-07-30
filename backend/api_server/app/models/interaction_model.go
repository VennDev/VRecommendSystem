package models

import "time"

type InteractionEvent struct {
	UserID    string         `json:"user_id"`
	ItemID    string         `json:"item_id"`
	EventType int            `json:"event_type"`
	Timestamp time.Time      `json:"timestamp"`
	Weight    float64        `json:"weight"`
	Context   map[string]any `json:"context"` // Device, location, etc.
	SessionID string         `json:"session_id"`
	Duration  int64          `json:"duration,omitempty"` // For VIEW events
}
