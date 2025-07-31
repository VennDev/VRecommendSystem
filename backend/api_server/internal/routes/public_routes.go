package routes

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/internal/handlers"
)

func PublicRouters(a *fiber.App) {
	route := a.Group("/api/v1")

	// This route is used to check if the server is running
	route.Get("/ping", handlers.PingHandler)

	// This route is used to create a new interaction
	route.Post("/new_interaction", handlers.NewInteraction)
}
