package initialize

import (
	"github.com/venndev/vrecommendation/global"
	"log"
)

func InitLogger() {
	err := global.Logger.Init()
	if err != nil {
		log.Fatal("Failed to initialize logger", err)
	}
	defer global.Logger.Close()
}
