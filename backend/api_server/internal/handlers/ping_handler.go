package handlers

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/global"
)

func PingHandler(c fiber.Ctx) error {
	global.Logger.Info("Received ping request from " + c.IP())
	return c.SendString("pong")
}
