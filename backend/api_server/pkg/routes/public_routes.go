package routes

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/app/handlers"
	"github.com/venndev/vrecommendation/pkg/logger"
)

type PublicRoutes struct {
	Logger *logger.Logger
}

func (l *PublicRoutes) Init(a *fiber.App) {
	route := a.Group("/api/v1")

	// Initialize all handlers here
	pingHandler := &handlers.PingHandler{
		Logger: l.Logger,
	}

	// This route is used to check if the server is running
	route.Get("/ping", pingHandler.GetPing)

	// // Initialize interaction handlers
	// interactionHandler := &handlers.InteractionHandler{
	// 	Logger: l.Logger,
	// }
	//
	// // This route is used to create a new interaction
	// route.Post("/new_interaction", interactionHandler.NewInteraction)
}
