package utils

import (
	"errors"
	"os"
	"path/filepath"

	"github.com/venndev/vrecommendation/pkg/configs"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"gopkg.in/natefinch/lumberjack.v2"
)

type Logger struct {
	logger     *zap.Logger
	lumberJack *lumberjack.Logger
}

func (l *Logger) Init() error {
	logsDir := "logs"
	err := os.MkdirAll(logsDir, 0755)
	if err != nil {
		return err
	}

	// Load log configuration
	log_config := configs.LogConfig()
	maxSize := log_config.MaxSize
	maxBackups := log_config.MaxBackups
	maxAge := log_config.MaxAge
	compress := log_config.Compress
	localTime := log_config.LocalTime

	logFileName := DateTimeString() + ".log"
	logFilePath := filepath.Join(logsDir, logFileName)

	l.lumberJack = &lumberjack.Logger{
		Filename:   logFilePath,
		MaxSize:    maxSize, // megabytes
		MaxBackups: maxBackups,
		MaxAge:     maxAge, // days
		Compress:   compress,
		LocalTime:  localTime,
	}

	writeSyncer := zapcore.NewMultiWriteSyncer(
		zapcore.AddSync(os.Stdout),
		zapcore.AddSync(l.lumberJack),
	)

	encoderConfig := zap.NewProductionEncoderConfig()
	encoderConfig.TimeKey = "time"
	encoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
	encoderConfig.CallerKey = "caller"
	encoderConfig.EncodeCaller = zapcore.ShortCallerEncoder

	encoder := zapcore.NewJSONEncoder(encoderConfig)

	core := zapcore.NewCore(encoder, writeSyncer, zapcore.DebugLevel)
	l.logger = zap.New(core, zap.AddCaller(), zap.AddStacktrace(zapcore.ErrorLevel))

	if l.logger == nil {
		return errors.New("failed to create logger")
	}

	l.logger.Info("Logger initialized successfully",
		zap.String("logFile", logFilePath),
		zap.Int("maxSize", l.lumberJack.MaxSize),
		zap.Int("maxBackups", l.lumberJack.MaxBackups),
		zap.Int("maxAge", l.lumberJack.MaxAge),
		zap.Bool("compress", l.lumberJack.Compress),
	)

	return nil
}

func (l *Logger) Info(msg string, fields ...zap.Field) {
	if l.logger != nil {
		l.logger.Info(msg, fields...)
	}
}

func (l *Logger) Error(msg string, err error, fields ...zap.Field) {
	if l.logger != nil {
		allFields := append(fields, zap.Error(err))
		l.logger.Error(msg, allFields...)
	}
}

func (l *Logger) Debug(msg string, fields ...zap.Field) {
	if l.logger != nil {
		l.logger.Debug(msg, fields...)
	}
}

func (l *Logger) Warn(msg string, fields ...zap.Field) {
	if l.logger != nil {
		l.logger.Warn(msg, fields...)
	}
}

func (l *Logger) Fatal(msg string, fields ...zap.Field) {
	if l.logger != nil {
		l.logger.Fatal(msg, fields...)
	}
}

func (l *Logger) InfoSimple(msg string) {
	l.Info(msg)
}

func (l *Logger) ErrorSimple(msg string, err error) {
	l.Error(msg, err)
}

func (l *Logger) DebugSimple(msg string) {
	l.Debug(msg)
}

func (l *Logger) WarnSimple(msg string) {
	l.Warn(msg)
}

func (l *Logger) FatalSimple(msg string) {
	l.Fatal(msg)
}

func (l *Logger) Rotate() error {
	if l.lumberJack != nil {
		return l.lumberJack.Rotate()
	}
	return nil
}

func (l *Logger) GetLogStats() map[string]interface{} {
	if l.lumberJack == nil {
		return nil
	}

	return map[string]interface{}{
		"filename":   l.lumberJack.Filename,
		"maxSize":    l.lumberJack.MaxSize,
		"maxBackups": l.lumberJack.MaxBackups,
		"maxAge":     l.lumberJack.MaxAge,
		"compress":   l.lumberJack.Compress,
	}
}

func (l *Logger) Close() {
	if l.logger != nil {
		_ = l.logger.Sync()
	}
	if l.lumberJack != nil {
		_ = l.lumberJack.Close()
	}
}
