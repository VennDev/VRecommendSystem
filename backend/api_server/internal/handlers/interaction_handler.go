package handlers

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/internal/event"
	"github.com/venndev/vrecommendation/internal/services"
)

func NewInteraction(c fiber.Ctx) error {
	var bodyData event.Message
	if err := c.Bind().Body(&bodyData); err != nil {
		global.Logger.Error("Failed to bind request body", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid request body",
		})
	}

	service := services.GetEventService()
	err := service.SendEvent(c.Context(), event.Message{
		EventType: bodyData.EventType,
		UserID:    bodyData.UserID,
		ItemID:    bodyData.ItemID,
		Timestamp: bodyData.Timestamp,
		SessionID: bodyData.SessionID,
		DeviceID:  bodyData.DeviceID,
		Metadata:  bodyData.Metadata,
	})

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
			"event_type": bodyData.EventType,
		},
	})
}
