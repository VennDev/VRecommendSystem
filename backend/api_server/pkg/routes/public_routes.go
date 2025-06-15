package routes

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/app/controllers"
	"github.com/venndev/vrecommendation/pkg/utils"
)

type PublicRoutes struct {
	Logger *utils.Logger
}

func (l *PublicRoutes) Init(a *fiber.App) {
	// Initialize all controllers here 
	pingController := &controllers.PingController{
		Logger: l.Logger,
	}

	route := a.Group("/api/v1")

	// This route is used to check if the server is running
	route.Get("/ping", pingController.GetPing)
}