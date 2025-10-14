package routes

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/internal/handlers"
)

func PublicRouters(a *fiber.App) {
	route := a.Group("/api/v1")

	// This route is used to check if the server is running
	route.Get("/ping", handlers.PingHandler)

	// This route is used to get recommendations based on user interactions
	route.Get("/recommend", handlers.Recommend)

	// Authentication routes
	// IMPORTANT: Specific routes MUST come before wildcard routes
	route.Get("/auth/user", handlers.GetUserHandler)
	route.Post("/auth/logout", handlers.LogoutHandler)
	route.Get("/auth/:provider/callback", handlers.CallbackHandler)
	route.Get("/auth/:provider", handlers.BeginAuthHandler)

	// Email whitelist routes (localhost only)
	route.Post("/whitelist/add", handlers.AddEmailToWhitelist)
	route.Get("/whitelist/list", handlers.GetWhitelistEmails)
	route.Post("/whitelist/check", handlers.CheckEmailWhitelisted)
	route.Delete("/whitelist/:id", handlers.RemoveEmailFromWhitelist)
	route.Put("/whitelist/:id", handlers.UpdateWhitelistEmail)

	// Activity logging routes
	route.Post("/activity-logs", handlers.CreateActivityLog)
	route.Get("/activity-logs/user", handlers.GetUserActivityLogs)
	route.Get("/activity-logs/all", handlers.GetAllRecentActivityLogs)
	route.Get("/activity-logs/resource", handlers.GetActivityLogsByResource)
	route.Get("/activity-logs/export", handlers.ExportUserActivityLogs)

	// Server logs routes
	route.Get("/server-logs", handlers.GetServerLogs)
}
