package main

import (
	_ "github.com/lib/pq"
	"github.com/venndev/vrecommendation/internal/initialize"
)

func main() {
	//err := godotenv.Load()
	//if err != nil {
	//	log.Fatal("Error loading .env file")
	//}

	// Initialize the application
	initialize.Run()
}
