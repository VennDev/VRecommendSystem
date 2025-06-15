package configs

import (
	"os"
	"strconv"
)

type LogConfigResult struct {
	MaxSize int
	MaxBackups int 
	MaxAge int 
	Compress bool
	LocalTime bool
}

func LogConfig() LogConfigResult {
	maxSize := os.Getenv("LOG_MAX_SIZE")
	maxBackups := os.Getenv("LOG_MAX_BACKUPS")
	maxAge := os.Getenv("LOG_MAX_AGE")
	compress := os.Getenv("LOG_COMPRESS") == "true"
	localTime := os.Getenv("LOG_LOCAL_TIME") == "true"

	maxSizeInt, err := strconv.ParseInt(maxSize, 10, 64)
	if err != nil {
		maxSizeInt = 10
	}

	maxBackupsInt, err := strconv.ParseInt(maxBackups, 10, 64)
	if err != nil {
		maxBackupsInt = 5
	}

	maxAgeInt, err := strconv.ParseInt(maxAge, 10, 64)
	if err != nil {
		maxAgeInt = 30
	}

	return LogConfigResult{
		MaxSize: int(maxSizeInt), 
		MaxBackups: int(maxBackupsInt),
		MaxAge: int(maxAgeInt),
		Compress: compress,
		LocalTime: localTime,
	}
}