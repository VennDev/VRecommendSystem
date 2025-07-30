package utils

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/pkg/configs"
	"github.com/venndev/vrecommendation/pkg/logger"
	"go.uber.org/zap"
)

func StartServer(app *fiber.App, cf configs.ServerConfigResult, logger *logger.Logger) {
	address := cf.Host + ":" + cf.Port
	if err := app.Listen(address); err != nil {
		logger.Error("Failed to start server", err, zap.String("address", address))
		os.Exit(1)
	}
}

func StartServerWithGracefulShutdown(app *fiber.App, cf configs.ServerConfigResult, logger *logger.Logger) {
	address := cf.Host + ":" + cf.Port

	go func() {
		if err := app.Listen(address); err != nil {
			logger.Fatal("Server exited with error", zap.String("error", err.Error()))
		}
	}()

	// Wait for interrupt signal to gracefully shutdown the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down server...")

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := app.ShutdownWithContext(ctx); err != nil {
		logger.Error("Error during server shutdown", err, zap.String("address", address))
	} else {
		logger.Info("Server shut down gracefully")
	}
}
