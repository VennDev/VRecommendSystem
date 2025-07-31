package initialize

import (
	"github.com/gofiber/fiber/v3"
	"github.com/gofiber/fiber/v3/middleware/cors"
	"github.com/gofiber/fiber/v3/middleware/logger"
)

func InitMiddlewares(app *fiber.App) {
	app.Use(
		cors.New(),
		logger.New(),
	)
}
