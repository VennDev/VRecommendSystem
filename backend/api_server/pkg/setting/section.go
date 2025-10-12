package setting

type Config struct {
	// From local.yml
	Logger Logger `yaml:"logger" mapstructure:"logger"`
	JWT    JWT    `yaml:"jwt" mapstructure:"jwt"`
	Redis  Redis  `yaml:"redis" mapstructure:"redis"`
}

type Logger struct {
	MaxSize     int  `yaml:"max_size" mapstructure:"max_size"`
	MaxBackups  int  `yaml:"max_backups" mapstructure:"max_backups"`
	MaxAge      int  `yaml:"max_age" mapstructure:"max_age"`
	Compression bool `yaml:"compression" mapstructure:"compression"`
	LocalTime   bool `yaml:"local_time" mapstructure:"local_time"`
}

type JWT struct {
	SecretKey               string `yaml:"secret_key" mapstructure:"secret_key"`
	ExpireMinsCount         int    `yaml:"expire_mins_count" mapstructure:"expire_mins_count"`
	RefreshKey              string `yaml:"refresh_key" mapstructure:"refresh_key"`
	RefreshExpireHoursCount int    `yaml:"refresh_expire_hours_count" mapstructure:"refresh_expire_hours_count"`
}

type Redis struct {
	Host            string `yaml:"host" mapstructure:"host"`
	Port            int    `yaml:"port" mapstructure:"port"`
	Password        string `yaml:"password" mapstructure:"password"`
	DB              int    `yaml:"db" mapstructure:"db"`
	SSL             bool   `yaml:"ssl" mapstructure:"ssl"`
	MaxRetries      int    `yaml:"max_retries" mapstructure:"max_retries"`
	PoolSize        int    `yaml:"pool_size" mapstructure:"pool_size"`
	MinIdleConns    int    `yaml:"min_idle_conns" mapstructure:"min_idle_conns"`
	MaxConnAge      int    `yaml:"max_conn_age" mapstructure:"max_conn_age"`
	PoolTimeout     int    `yaml:"pool_timeout" mapstructure:"pool_timeout"`
	IdleTimeout     int    `yaml:"idle_timeout" mapstructure:"idle_timeout"`
	ReadTimeout     int    `yaml:"read_timeout" mapstructure:"read_timeout"`
	WriteTimeout    int    `yaml:"write_timeout" mapstructure:"write_timeout"`
}
