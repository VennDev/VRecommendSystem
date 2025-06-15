package controllers

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/pkg/utils"
)

type PingController struct {
	Logger *utils.Logger
}

func (pc *PingController) GetPing(c fiber.Ctx) error {
	pc.Logger.Info("Received ping request from " + c.IP())
	return c.SendString("pong")
}