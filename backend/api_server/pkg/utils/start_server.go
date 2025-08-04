package utils

import (
	"context"
	"github.com/venndev/vrecommendation/global"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v3"
	"go.uber.org/zap"
)

func buildStringConnection() string {
	host := os.Getenv("HOST_ADDRESS")
	if host == "" {
		host = "localhost"
	}

	port := os.Getenv("HOST_PORT")
	if port == "" {
		port = "3000"
	}

	return host + ":" + port
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

	// Wait for interrupt signal to gracefully shutdown the server
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
