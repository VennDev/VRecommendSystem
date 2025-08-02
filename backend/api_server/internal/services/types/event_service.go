package types

import (
	"context"
	"github.com/venndev/vrecommendation/internal/event"
)

// EventService defines the methods for handling events
type EventService interface {
	SendEvent(ctx context.Context, event event.Message) error
	SendBatchEvents(ctx context.Context, events []event.Message) error
	ConsumeEvents(ctx context.Context, eventTypes []string, groupID string) (<-chan event.Message, <-chan error)
	GetEventStats() map[string]event.TypeStats
	ValidateEvent(event event.Message) error
	CreateEventTopics(ctx context.Context) error
	GetEnabledEventTypes() []string
	GetEventWeight(eventType string) float64
	GetHighValueEvents(threshold float64) []string
	IsEventEnabled(eventType string) bool
}
