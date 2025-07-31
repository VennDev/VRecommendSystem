package models

import "time"

type InteractionBody struct {
	UserID    string         `json:"user_id"`
	ItemID    string         `json:"item_id"`
	Timestamp time.Time      `json:"timestamp"`
	Context   map[string]any `json:"context"` // Device, location, etc.
	SessionID string         `json:"session_id"`
	Duration  int64          `json:"duration,omitempty"` // For VIEW events
}
