package initialize

import (
	"github.com/gofiber/fiber/v3"
	"github.com/gofiber/fiber/v3/middleware/cors"
	"github.com/venndev/vrecommendation/global"
	"os"
	"strconv"
	"time"
)

func InitApp() *fiber.App {
	readTimeout := os.Getenv("HOST_READ_TIMEOUT")
	if readTimeout == "" {
		readTimeout = "60"
	}

	rTO, err := strconv.Atoi(readTimeout)
	if err != nil {
		global.Logger.Error("Invalid HOST_READ_TIMEOUT value, using default 60 seconds", err)
		rTO = 60
	}

	app := fiber.New(fiber.Config{
		ReadTimeout: time.Second * time.Duration(rTO),
	})

	app.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:5173", "http://localhost:3000"}, // support both Vite dev server ports
		AllowMethods:     []string{"GET,POST,PUT,DELETE,OPTIONS"},
		AllowHeaders:     []string{"Origin, Content-Type, Accept, Authorization"},
		AllowCredentials: true, // bắt buộc khi dùng cookie/session
	}))

	return app
}
