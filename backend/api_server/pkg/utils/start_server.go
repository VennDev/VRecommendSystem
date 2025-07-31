package utils

import (
	"context"
	"github.com/venndev/vrecommendation/global"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v3"
	"go.uber.org/zap"
)

func StartServer(app *fiber.App) {
	cfg := &global.Config.Server
	host := cfg.Host
	port := strconv.Itoa(cfg.Port)
	address := host + ":" + port

	if err := app.Listen(address); err != nil {
		global.Logger.Error("Failed to start server", err, zap.String("address", address))
		os.Exit(1)
	}
}

func StartServerWithGracefulShutdown(app *fiber.App) {
	cf := &global.Config.Server
	host := cf.Host
	port := strconv.Itoa(cf.Port)
	address := host + ":" + port

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
