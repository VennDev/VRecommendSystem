package main

import (
	"fmt"
	_ "github.com/lib/pq"
	"github.com/venndev/vrecommendation/internal/initialize"
)

func main() {
	fmt.Println("Starting VRecommendation Service...")

	//err := godotenv.Load()
	//if err != nil {
	//	log.Fatal("Error loading .env file")
	//}

	// Initialize the application
	initialize.Run()
}
