package routes

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/app/handlers"
	"github.com/venndev/vrecommendation/pkg/utils"
)

type PublicRoutes struct {
	Logger *utils.Logger
}

func (l *PublicRoutes) Init(a *fiber.App) {
	// Initialize all handlers here
	pingHandler := &handlers.PingHandler{
		Logger: l.Logger,
	}

	route := a.Group("/api/v1")

	// This route is used to check if the server is running
	route.Get("/ping", pingHandler.GetPing)
}
