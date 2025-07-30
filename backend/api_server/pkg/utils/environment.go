package utils

import (
	"fmt"
	"log"
	"os"

	"github.com/joho/godotenv"
)

func LoadEnvironment() error {
	if err := godotenv.Load(envFile); err != nil {
		if os.IsExist(err) {
			return fmt.Errorf("error loading %s file: %w", envFile, err)
		}
		log.Printf("Warning: %s file not found, using system environment variables", envFile)
	}
	return nil
}

