package core

import "go.uber.org/zap"

type Logger interface {
	Init() error
	Info(msg string, fields ...zap.Field)
	Error(msg string, err error, fields ...zap.Field)
	Debug(msg string, fields ...zap.Field)
	Warn(msg string, fields ...zap.Field)
	Fatal(msg string, fields ...zap.Field)

	InfoSimple(msg string)
	ErrorSimple(msg string, err error)
	DebugSimple(msg string)
	WarnSimple(msg string)
	FatalSimple(msg string)

	Rotate() error
	GetLogStats() map[string]any
	Close()
}
