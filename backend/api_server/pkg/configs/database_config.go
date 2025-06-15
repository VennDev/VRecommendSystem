package configs

import (
	"os"
	"strconv"
	"time"
)

type DatabaseConfigResult struct {
	Type            string
	URL             string
	MaxOpenConns    int
	MaxIdleConns    int
	ConnMaxLifetime time.Duration
	ConnMaxIdleTime time.Duration
}

func DatabaseConfig() *DatabaseConfigResult {
	dbType := os.Getenv("DATABASE_TYPE")
	if dbType == "" {
		dbType = "mysql"
	}

	url := os.Getenv("DATABASE_URL")
	if url == "" {
		url = "root:password@tcp(localhost:3306)/dbname"
	}

	maxOpenConns := 10
	if val := os.Getenv("DATABASE_MAX_OPEN_CONNS"); val != "" {
		if v, err := strconv.Atoi(val); err == nil {
			maxOpenConns = v
		}
	}

	maxIdleConns := 5
	if val := os.Getenv("DATABASE_MAX_IDLE_CONNS"); val != "" {
		if v, err := strconv.Atoi(val); err == nil {
			maxIdleConns = v
		}
	}

	connMaxLifetime := time.Hour
	if val := os.Getenv("DATABASE_CONN_MAX_LIFETIME"); val != "" {
		if d, err := time.ParseDuration(val); err == nil {
			connMaxLifetime = d
		}
	}

	connMaxIdleTime := time.Minute
	if val := os.Getenv("DATABASE_CONN_MAX_IDLE_TIME"); val != "" {
		if d, err := time.ParseDuration(val); err == nil {
			connMaxIdleTime = d
		}
	}

	return &DatabaseConfigResult{
		Type:            dbType,
		URL:             url,
		MaxOpenConns:    maxOpenConns,
		MaxIdleConns:    maxIdleConns,
		ConnMaxLifetime: connMaxLifetime,
		ConnMaxIdleTime: connMaxIdleTime,
	}
}
