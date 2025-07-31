package initialize

import (
	vp "github.com/spf13/viper"
	"github.com/venndev/vrecommendation/global"
)

func LoadConfig() {
	viper := vp.New()

	viper.AddConfigPath("./config")
	viper.SetConfigName("local")
	viper.SetConfigType("yaml")

	if err := viper.ReadInConfig(); err != nil {
		global.Logger.Fatal("Failed to read config file: " + err.Error())
	}

	if err := viper.Unmarshal(&global.Config); err != nil {
		global.Logger.Fatal("Failed to unmarshal config: " + err.Error())
	}
}
