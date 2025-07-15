package handlers

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/pkg/utils"
)

type PingHandler struct {
	Logger *utils.Logger
}

func (pc *PingHandler) GetPing(c fiber.Ctx) error {
	pc.Logger.Info("Received ping request from " + c.IP())
	return c.SendString("pong")
}
