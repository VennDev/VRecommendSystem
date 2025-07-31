package database

import (
	"context"
	"fmt"
	"time"

	"github.com/venndev/vrecommendation/pkg/setting"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
)

type NoSQLManager interface {
	Manager
	GetClient() *mongo.Client
	GetDatabase(name string) *mongo.Database
	GetCollection(dbName, collectionName string) *mongo.Collection
}

type mongoManager struct {
	client    *mongo.Client
	config    setting.Database
	connected bool
}

func NewMongoManager(config setting.Database) (NoSQLManager, error) {
	connectionStr := buildMongoConnectionString(config)

	client, err := connectMongoDB(connectionStr, config.ConnMaxLifetime)
	if err != nil {
		return nil, err
	}

	return &mongoManager{
		client:    client,
		config:    config,
		connected: true,
	}, nil
}

func (mm *mongoManager) GetClient() *mongo.Client {
	return mm.client
}

func (mm *mongoManager) GetDatabase(name string) *mongo.Database {
	if name == "" {
		name = mm.config.Name
	}
	return mm.client.Database(name)
}

func (mm *mongoManager) GetCollection(dbName, collectionName string) *mongo.Collection {
	return mm.GetDatabase(dbName).Collection(collectionName)
}

func (mm *mongoManager) Close() error {
	if mm.client != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		mm.connected = false
		return mm.client.Disconnect(ctx)
	}
	return nil
}

func (mm *mongoManager) Ping(ctx context.Context) error {
	if mm.client == nil {
		return fmt.Errorf("MongoDB client is nil")
	}
	return mm.client.Ping(ctx, nil)
}

func (mm *mongoManager) IsConnected() bool {
	return mm.connected && mm.client != nil
}

func connectMongoDB(connectionStr string, maxLifetime time.Duration) (*mongo.Client, error) {
	clientOptions := options.Client().ApplyURI(connectionStr)

	if maxLifetime > 0 {
		clientOptions.SetMaxConnIdleTime(maxLifetime)
	}

	client, err := mongo.Connect(clientOptions)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to MongoDB: %w", err)
	}

	// Test connection
	timeout := 10 * time.Second
	if maxLifetime > 0 {
		timeout = maxLifetime
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	if err := client.Ping(ctx, nil); err != nil {
		client.Disconnect(ctx)
		return nil, fmt.Errorf("failed to ping MongoDB: %w", err)
	}

	return client, nil
}

func buildMongoConnectionString(config setting.Database) string {
	if config.User != "" && config.Password != "" {
		return fmt.Sprintf("mongodb://%s:%s@%s:%d/%s",
			config.User, config.Password, config.Host, config.Port, config.Name)
	}
	return fmt.Sprintf("mongodb://%s:%d/%s", config.Host, config.Port, config.Name)
}
