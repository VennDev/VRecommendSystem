package handlers

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/pkg/logger"
)

type PingHandler struct {
	Logger *logger.Logger
}

func (ph *PingHandler) GetPing(c fiber.Ctx) error {
	ph.Logger.Info("Received ping request from " + c.IP())
	return c.SendString("pong")
}
