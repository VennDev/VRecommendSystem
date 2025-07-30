package configs

import (
	"os"
	"strconv"
	"time"

	"github.com/venndev/vrecommendation/pkg/utils/connection"
)

type InteractionsDBConfigResult struct {
	Type            string
	URL             string
	MaxOpenConns    int
	MaxIdleConns    int
	ConnMaxLifetime time.Duration
	ConnMaxIdleTime time.Duration
}

func InteractionsDBConfig() *InteractionsDBConfigResult {
	dbType := os.Getenv("DATABASE_TYPE")
	if dbType == "" {
		dbType = "mysql"
	}

	url, err := connection.ConnectionURLBuilder(dbType)
	if err != nil || url == "" {
		panic("Failed to build database connection URL: " + err.Error())
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

	return &InteractionsDBConfigResult{
		Type:            dbType,
		URL:             url,
		MaxOpenConns:    maxOpenConns,
		MaxIdleConns:    maxIdleConns,
		ConnMaxLifetime: connMaxLifetime,
		ConnMaxIdleTime: connMaxIdleTime,
	}
}
