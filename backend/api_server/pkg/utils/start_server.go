package utils

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/global"
	"go.uber.org/zap"
)

func buildStringConnection() string {
	// Get host from environment variable or config
	host := os.Getenv("HOST_ADDRESS")
	if host == "" {
		host = global.Config.Server.Host
		if host == "" {
			host = "0.0.0.0"
		}
	}

	// Get port from environment variable or config
	var port int
	if envPort := os.Getenv("HOST_PORT"); envPort != "" {
		if p, err := strconv.Atoi(envPort); err == nil {
			port = p
		}
	}
	if port == 0 {
		port = global.Config.Server.Port
		if port == 0 {
			port = 3000
		}
	}

	return fmt.Sprintf("%s:%d", host, port)
}

func StartServer(app *fiber.App) {
	address := buildStringConnection()

	if err := app.Listen(address); err != nil {
		global.Logger.Error("Failed to start server", err, zap.String("address", address))
		os.Exit(1)
	}
}

func StartServerWithGracefulShutdown(app *fiber.App) {
	address := buildStringConnection()
	go func() {
		if err := app.Listen(address); err != nil {
			global.Logger.Fatal("Server exited with error", zap.String("error", err.Error()))
		}
	}()

	// Wait for interrupt signal to gracefully shut down the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	global.Logger.Info("Shutting down server...")

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := app.ShutdownWithContext(ctx); err != nil {
		global.Logger.Error("Error during server shutdown", err, zap.String("address", address))
	} else {
		global.Logger.Info("Server shut down gracefully")
	}
}
