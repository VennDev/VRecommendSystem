package handlers

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/internal/initialize"
)

func ReloadData(c fiber.Ctx) error {
	err := initialize.InitDataHandler()
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to reload data",
		})
	}

	return c.JSON(fiber.Map{
		"message": "Reload endpoint is under construction",
	})
}
