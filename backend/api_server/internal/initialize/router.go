package initialize

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/internal/routes"
)

func InitRouter(app *fiber.App) {
	routes.PublicRouters(app)
}
