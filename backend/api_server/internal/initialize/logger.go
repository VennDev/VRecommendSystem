package initialize

import (
	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/pkg/logger"
	"github.com/venndev/vrecommendation/pkg/logger/types"
	"log"
)

func InitLogger() types.Logger {
	lgr := logger.Logger{}
	global.Logger = &lgr

	err := global.Logger.Init()
	if err != nil {
		log.Fatal("Failed to initialize logger", err)
	}

	lgr.Info("Initialized logger")

	return global.Logger
}
