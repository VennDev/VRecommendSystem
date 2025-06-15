package configs

import (
	"os"
)

type ServerConfigResult struct {
	Host string
	Port string 
}

func ServerConfig() ServerConfigResult {
	host := os.Getenv("SERVER_HOST")
	port := os.Getenv("SERVER_PORT")

	if host == "" {
		host = "localhost" // Default host
	}

	if port == "" {
		port = "3000" // Default port
	}

	return ServerConfigResult{
		Host: host,
		Port: port,
	}
}