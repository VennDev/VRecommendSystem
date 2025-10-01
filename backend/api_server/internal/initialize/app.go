package initialize

import (
	"github.com/gofiber/fiber/v3"
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

	return app
}
