package handlers

import (
	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/internal/services"
	"strconv"

	"github.com/gofiber/fiber/v3"
	"github.com/samber/lo"
	"github.com/venndev/vrecommendation/app/models"
	"github.com/venndev/vrecommendation/pkg/event"
)

func NewInteraction(c fiber.Ctx) error {
	eventType := c.Get("Event-Type")
	if eventType == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Event-Type header is required",
		})
	}

	eventTypeConvert, err := strconv.Atoi(eventType)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid Event-Type header, must be an integer",
		})
	}

	listKeys := lo.Keys(event.EventNames)
	if !lo.Contains(listKeys, eventTypeConvert) {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid Event-Type header",
		})
	}

	var bodyData models.InteractionBody
	if err := c.Bind().Body(&bodyData); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Failed to parse request body",
		})
	}

	evType := eventTypeConvert
	sessionID := services.WithSessionID(bodyData.SessionID)
	producer, err := services.GetRecommendationProducer()
	if err != nil {
		global.Logger.Error("Failed to get recommendation producer", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get recommendation producer",
		})
	}

	err = producer.SendEventAsync(
		evType, bodyData.UserID, bodyData.ItemID, sessionID,
	)

	if err != nil {
		global.Logger.Error("Failed to send event. When sending interaction event", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to send event",
		})
	}

	return c.Status(fiber.StatusOK).JSON(fiber.Map{
		"message": "Event sent successfully!",
		"data": fiber.Map{
			"user_id":    bodyData.UserID,
			"item_id":    bodyData.ItemID,
			"event_type": eventTypeConvert,
		},
	})
}
