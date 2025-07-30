package connection

import (
	"fmt"
	"os"
)

func ConnectionURLBuilder(n string) (string, error) {
	var url string

	switch n {
	case "postgres":
		url = fmt.Sprintf(
			"host=%s port=%s user=%s password=%s dbname=%s sslmode=%s",
			os.Getenv("DATABASE_HOST"),
			os.Getenv("DATABASE_PORT"),
			os.Getenv("DATABASE_USER"),
			os.Getenv("DATABASE_PASSWORD"),
			os.Getenv("DATABASE_NAME"),
			os.Getenv("DATABASE_SSL_MODE"),
		)
	case "mysql":
		url = fmt.Sprintf(
			"%s:%s@tcp(%s:%s)/%s",
			os.Getenv("DATABASE_USER"),
			os.Getenv("DATABASE_PASSWORD"),
			os.Getenv("DATABASE_HOST"),
			os.Getenv("DATABASE_PORT"),
			os.Getenv("DATABASE_NAME"),
		)
	case "redis":
		url = fmt.Sprintf(
			"%s:%s",
			os.Getenv("REDIS_HOST"),
			os.Getenv("REDIS_PORT"),
		)
	case "fiber":
		url = fmt.Sprintf(
			"%s:%s",
			os.Getenv("SERVER_HOST"),
			os.Getenv("SERVER_PORT"),
		)
	case "kafka":
		url = fmt.Sprintf(
			"%s:%s",
			os.Getenv("KAFKA_HOST"),
			os.Getenv("KAFKA_PORT"),
		)
	case "mongodb_interaction":
		url = fmt.Sprintf(
			"mongodb://%s:%s@%s:%s/%s",
			os.Getenv("INTERACTIONS_DB_USER"),
			os.Getenv("INTERACTIONS_DB_PASSWORD"),
			os.Getenv("INTERACTIONS_DB_HOST"),
			os.Getenv("INTERACTIONS_DB_PORT"),
			os.Getenv("INTERACTIONS_DB_NAME"),
		)
	default:
		return "", fmt.Errorf("connection name '%v' is not supported", n)
	}

	return url, nil
}
