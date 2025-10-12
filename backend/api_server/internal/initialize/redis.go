package initialize

import (
	"fmt"

	"github.com/venndev/vrecommendation/global"
	redisClient "github.com/venndev/vrecommendation/pkg/redis"
)

func InitRedis() error {
	config := global.Config

	_, err := redisClient.InitRedisWithConfig(config.Redis)
	if err != nil {
		global.Logger.Error("Failed to initialize Redis", err)
		return err
	}

	global.Logger.Info("Redis initialized successfully")
	global.Logger.Info("Redis configuration:")
	global.Logger.Info("  - Host: " + config.Redis.Host)
	global.Logger.Info("  - SSL: " + fmt.Sprint(config.Redis.SSL))
	global.Logger.Info("  - DB: " + fmt.Sprint(config.Redis.DB))
	global.Logger.Info("  - Pool Size: " + fmt.Sprint(config.Redis.PoolSize))
	return nil
}
