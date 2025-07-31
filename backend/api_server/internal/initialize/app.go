package initialize

import (
	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/global"
	"time"
)

func InitApp() *fiber.App {
	app := fiber.New(fiber.Config{
		ReadTimeout: time.Second * time.Duration(global.Config.Server.ReadTimeout),
	})

	return app
}
