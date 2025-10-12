package initialize

import (
	"github.com/venndev/vrecommendation/global"
	redisClient "github.com/venndev/vrecommendation/pkg/redis"
)

func InitRedis() error {
	config := global.Config

	_, err := redisClient.InitRedis(config.Redis.Host, config.Redis.Port)
	if err != nil {
		global.Logger.Error("Failed to initialize Redis", err)
		return err
	}

	global.Logger.Info("Redis initialized successfully")
	return nil
}
