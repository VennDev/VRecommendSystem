package initialize

import (
	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/pkg/logger"
	"log"
)

func InitLogger() *logger.Logger {
	lgr := logger.Logger{}
	global.Logger = &lgr

	err := global.Logger.Init()
	if err != nil {
		log.Fatal("Failed to initialize logger", err)
	}

	return global.Logger
}
