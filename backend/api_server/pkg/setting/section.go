package setting

import "time"

type Config struct {
	// From local.yml
	StatusDev string   `yaml:"status_dev" mapstructure:"status_dev"`
	Server    Server   `yaml:"server" mapstructure:"server"`
	Logger    Logger   `yaml:"logger" mapstructure:"logger"`
	JWT       JWT      `yaml:"jwt" mapstructure:"jwt"`
	Redis     Redis    `yaml:"redis" mapstructure:"redis"`
	Database  Database `yaml:"database" mapstructure:"database"`

	// From kafka.yml
	Kafka          Kafka          `yaml:"kafka" mapstructure:"kafka"`
	Topics         Topics         `yaml:"topics" mapstructure:"topics"`
	ConsumerGroups ConsumerGroups `yaml:"consumer_groups" mapstructure:"consumer_groups"`
	Producer       Producer       `yaml:"producer" mapstructure:"producer"`
	Consumer       Consumer       `yaml:"consumer" mapstructure:"consumer"`
	TopicDefaults  TopicDefaults  `yaml:"topic_defaults" mapstructure:"topic_defaults"`
	TopicRetention TopicRetention `yaml:"topic_retention" mapstructure:"topic_retention"`
	Partitioning   Partitioning   `yaml:"partitioning" mapstructure:"partitioning"`
	SchemaRegistry SchemaRegistry `yaml:"schema_registry" mapstructure:"schema_registry"`
	Monitoring     Monitoring     `yaml:"monitoring" mapstructure:"monitoring"`
	Security       Security       `yaml:"security" mapstructure:"security"`
	Environment    Environment    `yaml:"environment" mapstructure:"environment"`
	Recommendation Recommendation `yaml:"recommendation" mapstructure:"recommendation"`
}

type Server struct {
	Host        string `yaml:"host" mapstructure:"host"`
	Port        int    `yaml:"port" mapstructure:"port"`
	ReadTimeout int    `yaml:"read_timeout" mapstructure:"read_timeout"`
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
	Host string `yaml:"host" mapstructure:"host"`
	Port int    `yaml:"port" mapstructure:"port"`
}

type Database struct {
	Type            string        `yaml:"type" mapstructure:"type"`
	Host            string        `yaml:"host" mapstructure:"host"`
	Port            int           `yaml:"port" mapstructure:"port"`
	User            string        `yaml:"user" mapstructure:"user"`
	Password        string        `yaml:"password" mapstructure:"password"`
	Name            string        `yaml:"name" mapstructure:"name"`
	SSL             bool          `yaml:"ssl" mapstructure:"ssl"`
	MaxIdleConns    int           `yaml:"max_idle_conns" mapstructure:"max_idle_conns"`
	MaxOpenConns    int           `yaml:"max_open_conns" mapstructure:"max_open_conns"`
	ConnMaxLifetime time.Duration `yaml:"conn_max_lifetime" mapstructure:"conn_max_lifetime"`
	ConnMaxIdleTime time.Duration `yaml:"conn_max_idle_time" mapstructure:"conn_max_idle_time"`
}

type Kafka struct {
	Brokers         []string `yaml:"brokers" mapstructure:"brokers"`
	ClientID        string   `yaml:"client_id" mapstructure:"client_id"`
	AutoOffsetReset string   `yaml:"auto_offset_reset" mapstructure:"auto_offset_reset"`
}

type Topics struct {
	Prefix string `yaml:"prefix" mapstructure:"prefix"`
	Suffix string `yaml:"suffix" mapstructure:"suffix"`
}

type ConsumerGroups struct {
	Realtime  string `yaml:"realtime" mapstructure:"realtime"`
	Batch     string `yaml:"batch" mapstructure:"batch"`
	Analytics string `yaml:"analytics" mapstructure:"analytics"`
}

type Producer struct {
	Acks                             string `yaml:"acks" mapstructure:"acks"`
	Retries                          int    `yaml:"retries" mapstructure:"retries"`
	RetryBackoffMs                   int    `yaml:"retry_backoff_ms" mapstructure:"retry_backoff_ms"`
	EnableIdempotence                bool   `yaml:"enable_idempotence" mapstructure:"enable_idempotence"`
	MaxInFlightRequestsPerConnection int    `yaml:"max_in_flight_requests_per_connection" mapstructure:"max_in_flight_requests_per_connection"`
	BatchSize                        int    `yaml:"batch_size" mapstructure:"batch_size"`
	LingerMs                         int    `yaml:"linger_ms" mapstructure:"linger_ms"`
	BufferMemory                     int    `yaml:"buffer_memory" mapstructure:"buffer_memory"`
	CompressionType                  string `yaml:"compression_type" mapstructure:"compression_type"`
	MaxRequestSize                   int    `yaml:"max_request_size" mapstructure:"max_request_size"`
	RequestTimeoutMs                 int    `yaml:"request_timeout_ms" mapstructure:"request_timeout_ms"`
	DeliveryTimeoutMs                int    `yaml:"delivery_timeout_ms" mapstructure:"delivery_timeout_ms"`
}

type Consumer struct {
	MaxPollRecords         int  `yaml:"max_poll_records" mapstructure:"max_poll_records"`
	FetchMinBytes          int  `yaml:"fetch_min_bytes" mapstructure:"fetch_min_bytes"`
	FetchMaxBytes          int  `yaml:"fetch_max_bytes" mapstructure:"fetch_max_bytes"`
	FetchMaxWaitMs         int  `yaml:"fetch_max_wait_ms" mapstructure:"fetch_max_wait_ms"`
	MaxPartitionFetchBytes int  `yaml:"max_partition_fetch_bytes" mapstructure:"max_partition_fetch_bytes"`
	SessionTimeoutMs       int  `yaml:"session_timeout_ms" mapstructure:"session_timeout_ms"`
	HeartbeatIntervalMs    int  `yaml:"heartbeat_interval_ms" mapstructure:"heartbeat_interval_ms"`
	MaxPollIntervalMs      int  `yaml:"max_poll_interval_ms" mapstructure:"max_poll_interval_ms"`
	EnableAutoCommit       bool `yaml:"enable_auto_commit" mapstructure:"enable_auto_commit"`
	AutoCommitIntervalMs   int  `yaml:"auto_commit_interval_ms" mapstructure:"auto_commit_interval_ms"`
}

type TopicDefaults struct {
	ReplicationFactor int `yaml:"replication_factor" mapstructure:"replication_factor"`
	Partitions        int `yaml:"partitions" mapstructure:"partitions"`
	RetentionMs       int `yaml:"retention_ms" mapstructure:"retention_ms"`
}

type TopicRetention struct {
	ViewEvents int64 `yaml:"view_events" mapstructure:"view_events"`
	LikeEvents int64 `yaml:"like_events" mapstructure:"like_events"`
	BuyEvents  int64 `yaml:"buy_events" mapstructure:"buy_events"`
}

type Partitioning struct {
	PartitionerClass  string `yaml:"partitioner_class" mapstructure:"partitioner_class"`
	PartitionKeyField string `yaml:"partition_key_field" mapstructure:"partition_key_field"`
}

type SchemaRegistry struct {
	URL     string `yaml:"url" mapstructure:"url"`
	Enabled bool   `yaml:"enabled" mapstructure:"enabled"`
}

type Monitoring struct {
	JMX         JMX         `yaml:"jmx" mapstructure:"jmx"`
	ConsumerLag ConsumerLag `yaml:"consumer_lag" mapstructure:"consumer_lag"`
}

type JMX struct {
	Enabled bool `yaml:"enabled" mapstructure:"enabled"`
	Port    int  `yaml:"port" mapstructure:"port"`
}

type ConsumerLag struct {
	MaxLag         int `yaml:"max_lag" mapstructure:"max_lag"`
	AlertThreshold int `yaml:"alert_threshold" mapstructure:"alert_threshold"`
}

type Security struct {
	Protocol string `yaml:"protocol" mapstructure:"protocol"`
	SASL     SASL   `yaml:"sasl" mapstructure:"sasl"`
	SSL      SSL    `yaml:"ssl" mapstructure:"ssl"`
}

type SASL struct {
	Mechanism string `yaml:"mechanism" mapstructure:"mechanism"`
	Username  string `yaml:"username" mapstructure:"username"`
	Password  string `yaml:"password" mapstructure:"password"`
}

type SSL struct {
	Truststore SSLStore `yaml:"truststore" mapstructure:"truststore"`
	Keystore   SSLStore `yaml:"keystore" mapstructure:"keystore"`
}

type SSLStore struct {
	Location string `yaml:"location" mapstructure:"location"`
	Password string `yaml:"password" mapstructure:"password"`
}

type Environment struct {
	Env          string   `yaml:"env" mapstructure:"env"`
	DebugEnabled bool     `yaml:"debug_enabled" mapstructure:"debug_enabled"`
	LogLevel     string   `yaml:"log_level" mapstructure:"log_level"`
	Brokers      []string `yaml:"brokers" mapstructure:"brokers"`
}

type Recommendation struct {
	Realtime     RealtimeConfig `yaml:"realtime" mapstructure:"realtime"`
	Batch        BatchConfig    `yaml:"batch" mapstructure:"batch"`
	EventWeights EventWeights   `yaml:"event_weights" mapstructure:"event_weights"`
}

type RealtimeConfig struct {
	WindowSizeMs int `yaml:"window_size_ms" mapstructure:"window_size_ms"`
}

type BatchConfig struct {
	ProcessingIntervalMs int `yaml:"processing_interval_ms" mapstructure:"processing_interval_ms"`
}

type EventWeights struct {
	View           float64 `yaml:"view" mapstructure:"view"`
	Like           float64 `yaml:"like" mapstructure:"like"`
	Comment        float64 `yaml:"comment" mapstructure:"comment"`
	Share          float64 `yaml:"share" mapstructure:"share"`
	Bookmark       float64 `yaml:"bookmark" mapstructure:"bookmark"`
	AddToCart      float64 `yaml:"add_to_cart" mapstructure:"add_to_cart"`
	AddToFavorites float64 `yaml:"add_to_favorites" mapstructure:"add_to_favorites"`
	Buy            float64 `yaml:"buy" mapstructure:"buy"`
}
