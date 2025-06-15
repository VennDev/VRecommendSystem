package utils

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/pkg/configs"
	"github.com/venndev/vrecommendation/pkg/database/manager"
	"go.uber.org/zap"
)

func StartServer(app *fiber.App, cf configs.ServerConfigResult, logger *Logger) {
	// Initialize database connection
	dbConfig := configs.DatabaseConfig()
	connectionManager := manager.GetConnectionManager()

	if err := connectionManager.Initialize(dbConfig); err != nil {
		logger.Fatal("Failed to initialize database", zap.String("error", err.Error()))
	}

	if err := connectionManager.Ping(); err != nil {
		logger.Fatal("Database connection failed", zap.String("error", err.Error()))
	}

	logger.Info("Successfully connected to database", zap.String("type", connectionManager.GetProvider().GetType()))

	address := cf.Host + ":" + cf.Port
	if err := app.Listen(address); err != nil {
		logger.Error("Failed to start server", err, zap.String("address", address))
		os.Exit(1)
	}
}

func StartServerWithGracefulShutdown(app *fiber.App, cf configs.ServerConfigResult, logger *Logger) {
	// Initialize database connection
	dbConfig := configs.DatabaseConfig()
	connectionManager := manager.GetConnectionManager()

	if err := connectionManager.Initialize(dbConfig); err != nil {
		logger.Fatal("Failed to initialize database", zap.String("error", err.Error()))
	}

	if err := connectionManager.Ping(); err != nil {
		logger.Fatal("Database connection failed", zap.String("error", err.Error()))
	}

	logger.Info("Successfully connected to database", zap.String("type", connectionManager.GetProvider().GetType()))

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
