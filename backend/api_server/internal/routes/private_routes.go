package routes

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/internal/handlers"
)

func PrivateRouters(a *fiber.App) {
	// Email whitelist routes (localhost only - checked in handlers)
	routeLocal := a.Group("/api/v1/local")
	routeLocal.Get("/whitelist/list", handlers.GetWhitelistEmails)
	routeLocal.Post("/whitelist/check", handlers.CheckEmailWhitelisted)
	routeLocal.Delete("/whitelist/:id", handlers.RemoveEmailFromWhitelist)
	routeLocal.Put("/whitelist/:id", handlers.UpdateWhitelistEmail)
}
