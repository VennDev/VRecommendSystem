package provider

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/venndev/vrecommendation/pkg/configs"
	"github.com/venndev/vrecommendation/pkg/utils/connection"
	"github.com/xo/dburl"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
)

type DatabaseManager struct {
	db      *sql.DB
	mongodb *mongo.Client
	url     *dburl.URL
}

func (dm *DatabaseManager) GetDB() *sql.DB {
	return dm.db
}

func (dm *DatabaseManager) GetMongoDB() *mongo.Client {
	return dm.mongodb
}

func (dm *DatabaseManager) GetURL() *dburl.URL {
	return dm.url
}

// Close properly closes both SQL and MongoDB connections
func (dm *DatabaseManager) Close() error {
	var errors []error

	if dm.db != nil {
		if err := dm.db.Close(); err != nil {
			errors = append(errors, fmt.Errorf("failed to close SQL database: %w", err))
		}
	}

	if dm.mongodb != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		if err := dm.mongodb.Disconnect(ctx); err != nil {
			errors = append(errors, fmt.Errorf("failed to close MongoDB: %w", err))
		}
	}

	if len(errors) > 0 {
		return fmt.Errorf("database close errors: %v", errors)
	}
	return nil
}

// connectSQL creates a SQL database connection
func connectSQL(connectionStr string) (*sql.DB, *dburl.URL, error) {
	u, err := dburl.Parse(connectionStr)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to parse database URL: %w", err)
	}

	db, err := sql.Open(u.Driver, connectionStr)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Set connection timeout
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return nil, nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return db, u, nil
}

// connectMongoDB creates a MongoDB connection
func connectMongoDB(connectionStr string, maxLifetime time.Duration) (*mongo.Client, error) {
	client, err := mongo.Connect(options.Client().ApplyURI(connectionStr))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to MongoDB: %w", err)
	}

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

func GetDB() (*DatabaseManager, error) {
	cfg := configs.DatabaseConfig()
	connectionStr, err := connection.ConnectionURLBuilder(cfg.Type)
	if err != nil {
		return nil, fmt.Errorf("failed to build connection URL: %w", err)
	}

	db, url, err := connectSQL(connectionStr)
	if err != nil {
		return nil, err
	}

	return &DatabaseManager{
		db:      db,
		mongodb: nil,
		url:     url,
	}, nil
}

func GetInteractionsDB() (*DatabaseManager, error) {
	cfg := configs.InteractionsDBConfig()
	connectionStr, err := connection.ConnectionURLBuilder(cfg.Type)
	if err != nil {
		return nil, fmt.Errorf("failed to build connection URL: %w", err)
	}

	if cfg.Type == "mongodb" {
		client, err := connectMongoDB(connectionStr, cfg.ConnMaxLifetime)
		if err != nil {
			return nil, err
		}

		return &DatabaseManager{
			db:      nil,
			mongodb: client,
			url:     nil,
		}, nil
	}

	// Handle SQL databases
	db, url, err := connectSQL(connectionStr)
	if err != nil {
		return nil, err
	}

	return &DatabaseManager{
		db:      db,
		mongodb: nil,
		url:     url,
	}, nil
}
